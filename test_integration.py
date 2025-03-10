from typing import Optional, Sequence
from pgargs import Cols, Args
import pytest
from unittest.mock import AsyncMock
from pydantic import BaseModel


class AddUserPayload(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class AddUserResult(BaseModel):
    id: int


class GetUserResult(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


class UpdateUserPayload(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


class UserFood(BaseModel, frozen=True):
    user_id: int
    food_name: str


class UserRepository:
    def __init__(self) -> None:
        self.conn = AsyncMock()

    async def add_user(self, payload: AddUserPayload) -> AddUserResult:
        cols = Cols(payload.model_dump(exclude_unset=True))
        query = f"INSERT INTO users {cols.names} VALUES {cols.values} RETURNING id"
        record = await self.conn.fetchrow(query, *cols.args)
        return AddUserResult.model_validate(record)

    async def eat_food(self, user_id: int, foods: Sequence[str]) -> None:
        args = Args(user_id=user_id)
        query = f"SELECT * FROM foods WHERE user_id = {args.user_id}"
        records = await self.conn.fetch(query, *args)
        previous_foods = {UserFood.model_validate(record) for record in records}

        desired_foods = {UserFood(user_id=user_id, food_name=food) for food in foods}

        to_create = desired_foods - previous_foods
        to_delete = previous_foods - desired_foods

        if to_create:
            cols = Cols(*UserFood.model_fields)
            query = f"INSERT INTO foods {cols.names} VALUES {cols.values}"
            iargs = cols.args(food.model_dump() for food in to_create)
            await self.conn.executemany(query, iargs)

        if to_delete:
            cols = Cols(*UserFood.model_fields)
            query = f"DELETE FROM foods WHERE {cols.conditions}"
            iargs = cols.args(food.model_dump() for food in to_delete)
            await self.conn.executemany(query, iargs)

    async def get_user(self, id: int) -> Optional[GetUserResult]:
        args = Args(id=id)
        query = f"SELECT * FROM users WHERE id = {args.id}"
        record = await self.conn.fetchrow(query, *args)
        return GetUserResult.model_validate(record) if record else None

    async def update_user(self, user_id: int, payload: UpdateUserPayload) -> None:
        cols = Cols(payload.model_dump(exclude_unset=True))
        if cols:
            query = f"UPDATE users SET {cols.assignments} WHERE id = {cols.args.id}"
            cols.args.id = user_id
            await self.conn.execute(query, *cols.args)


@pytest.fixture()
def repo() -> UserRepository:
    return UserRepository()


@pytest.mark.asyncio
async def test_add_user(repo: UserRepository) -> None:
    repo.conn.fetchrow.return_value = {"id": 1}
    result = await repo.add_user(AddUserPayload(name="bilbo", email="bilbo@shire.net"))
    assert result == AddUserResult(id=1)
    repo.conn.fetchrow.assert_called_once_with(
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
        "bilbo",
        "bilbo@shire.net",
    )


@pytest.mark.asyncio
async def test_eat_food(repo: UserRepository) -> None:
    repo.conn.fetch.return_value = [
        {"user_id": 1, "food_name": "turnip"},
        {"user_id": 1, "food_name": "potato"},
    ]
    await repo.eat_food(user_id=1, foods=["potato", "fish"])

    repo.conn.fetch.assert_called_once_with("SELECT * FROM foods WHERE user_id = $1", 1)
    assert len(repo.conn.executemany.mock_calls) == 2
    insert_call, delete_call = repo.conn.executemany.mock_calls

    insert_query, insert_args = insert_call.args
    assert insert_query == "INSERT INTO foods (user_id, food_name) VALUES ($1, $2)"
    assert list(insert_args) == [(1, "fish")]

    delete_query, delete_args = delete_call.args
    assert delete_query == "DELETE FROM foods WHERE user_id = $1 AND food_name = $2"
    assert list(delete_args) == [(1, "turnip")]


@pytest.mark.asyncio
async def test_get_user(repo: UserRepository) -> None:
    repo.conn.fetchrow.return_value = {
        "id": 123,
        "name": "bilbo",
        "email": "bilbo@shire.net",
    }
    result = await repo.get_user(id=123)
    assert result == GetUserResult(
        id=123,
        name="bilbo",
        email="bilbo@shire.net",
    )
    repo.conn.fetchrow.assert_called_once_with(
        "SELECT * FROM users WHERE id = $1",
        123,
    )


@pytest.mark.asyncio
async def test_update_user_with_email(repo: UserRepository) -> None:
    await repo.update_user(
        user_id=1,
        payload=UpdateUserPayload(email="bilbo@shire.net", age=111),
    )
    repo.conn.execute.assert_called_once_with(
        "UPDATE users SET email = $1, age = $2 WHERE id = $3",
        "bilbo@shire.net",
        111,
        1,
    )


@pytest.mark.asyncio
async def test_update_user_with_name(repo: UserRepository) -> None:
    await repo.update_user(
        user_id=2,
        payload=UpdateUserPayload(name="frodo", age=33),
    )
    repo.conn.execute.assert_called_once_with(
        "UPDATE users SET name = $1, age = $2 WHERE id = $3",
        "frodo",
        33,
        2,
    )


@pytest.mark.asyncio
async def test_update_user_with_empty_payload(repo: UserRepository) -> None:
    await repo.update_user(user_id=1, payload=UpdateUserPayload())
    assert not repo.conn.execute.called
