from pgargs import Cols
import pytest


def test_init() -> None:
    # Create cols with a defined column.
    cols = Cols("a")
    assert cols

    # Add another column without a value.
    cols.add("b")

    # Add a column with a value.
    cols["c"] = "c"

    # Check rendering of strings.
    query = f"INSERT INTO table {cols.names} VALUES {cols.values}"
    assert query == "INSERT INTO table (a, b, c) VALUES ($1, $2, $3)"

    query = f"UPDATE table SET {cols.assignments} WHERE id = {cols.args.id}"
    assert query == "UPDATE table SET a = $1, b = $2, c = $3 WHERE id = $4"


def test_empty() -> None:
    # Create cols with no defined column names.
    cols = Cols()
    assert not cols

    with pytest.raises(ValueError):
        f"INSERT INTO table {cols.names} VALUES {cols.values}"

    with pytest.raises(ValueError):
        f"UPDATE table SET {cols.assignments} WHERE id = {cols.args.id}"
