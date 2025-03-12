from collections.abc import AsyncGenerator
import asyncpg  # type: ignore[import-untyped]
from typing import Optional, Sequence
from pgargs import Cols, Args
import pytest
from pydantic import BaseModel
import os
import pytest_asyncio


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
    def __init__(self, conn: asyncpg.Connection) -> None:
        self.conn = conn

    async def add_user(self, payload: AddUserPayload) -> AddUserResult:
        cols = Cols(payload.model_dump(exclude_unset=True))
        query = f"INSERT INTO users {cols.names} VALUES {cols.values} RETURNING id"
        record = await self.conn.fetchrow(query, *cols.args)
        return AddUserResult.model_validate(dict(record))

    async def eat_foods(self, user_id: int, foods: Sequence[str]) -> None:
        previous_foods = await self.get_foods(user_id)
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

    async def get_foods(self, user_id: int) -> set[UserFood]:
        args = Args(user_id=user_id)
        query = f"SELECT * FROM foods WHERE user_id = {args.user_id}"
        records = await self.conn.fetch(query, *args)
        return {UserFood.model_validate(dict(record)) for record in records}

    async def get_user(self, id: int) -> Optional[GetUserResult]:
        args = Args(id=id)
        query = f"SELECT * FROM users WHERE id = {args.id}"
        record = await self.conn.fetchrow(query, *args)
        return GetUserResult.model_validate(dict(record)) if record else None

    async def update_user(self, user_id: int, payload: UpdateUserPayload) -> None:
        cols = Cols(payload.model_dump(exclude_unset=True))
        if cols:
            query = f"UPDATE users SET {cols.assignments} WHERE id = {cols.args.id}"
            cols.args.id = user_id
            await self.conn.execute(query, *cols.args)


@pytest_asyncio.fixture()
async def conn() -> AsyncGenerator[asyncpg.Connection, None]:
    conn = await asyncpg.connect(
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
        host=os.environ["POSTGRES_HOST"],
    )
    try:
        await conn.execute("DROP TABLE IF EXISTS users, foods")
        await conn.execute("""
            CREATE TABLE users(
                id serial PRIMARY KEY,
                name text,
                email text,
                age smallint
            )
        """)
        await conn.execute("""
            CREATE TABLE foods(
                user_id integer,
                food_name text
            )
        """)
        yield conn
        await conn.execute("DROP TABLE users, foods")
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_all(conn: asyncpg.Connection) -> None:
    users = UserRepository(conn)

    # Add new user.
    added = await users.add_user(
        payload=AddUserPayload(name="bilbo", email="bilbo@shire.net"),
    )
    assert added == AddUserResult(id=1)

    # Get user.
    got = await users.get_user(id=1)
    assert got == GetUserResult(
        id=1,
        name="bilbo",
        email="bilbo@shire.net",
    )

    # Update user with email field.
    await users.update_user(
        user_id=1,
        payload=UpdateUserPayload(email="bilbo@shire.nz"),
    )
    got = await users.get_user(id=1)
    assert got == GetUserResult(
        id=1,
        name="bilbo",
        email="bilbo@shire.nz",
    )

    # Update user with email and age fields.
    await users.update_user(
        user_id=1,
        payload=UpdateUserPayload(email="bilbo@shire.net", age=111),
    )
    got = await users.get_user(id=1)
    assert got == GetUserResult(
        id=1,
        name="bilbo",
        email="bilbo@shire.net",
        age=111,
    )

    # Update user with empty payload.
    await users.update_user(user_id=1, payload=UpdateUserPayload())
    got = await users.get_user(id=1)
    assert got == GetUserResult(
        id=1,
        name="bilbo",
        email="bilbo@shire.net",
        age=111,
    )

    # Update user with age removal.
    await users.update_user(user_id=1, payload=UpdateUserPayload(age=None))
    got = await users.get_user(id=1)
    assert got == GetUserResult(
        id=1,
        name="bilbo",
        email="bilbo@shire.net",
    )

    # Eat some food.
    await users.eat_foods(user_id=1, foods=["potato", "fish"])
    foods = await users.get_foods(user_id=1)
    assert foods == {
        UserFood(user_id=1, food_name="potato"),
        UserFood(user_id=1, food_name="fish"),
    }

    # Eat different food.
    await users.eat_foods(user_id=1, foods=["potato", "turnip"])
    foods = await users.get_foods(user_id=1)
    assert foods == {
        UserFood(user_id=1, food_name="potato"),
        UserFood(user_id=1, food_name="turnip"),
    }
