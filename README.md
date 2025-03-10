# pgargs

A tiny library for creating [asyncpg](https://github.com/MagicStack/asyncpg)
queries with f-strings and named arguments.

asyncpg only supports positional arguments, not named arguments.
pgargs makes it easy to prepare queries and positional arguments
for asyncpg using f-strings and named arguments.

## Install

```sh
pip install pgargs
```

## What it looks like

Lower level arguments usage:

```py
from pgargs import Args

args = Args(name="bilbo", age=111)
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"
await conn.fetch(query, *args)
```

Higher level columns usage:

```py
from pgargs import Args, Cols

cols = Cols(name="bilbo", age=111)
query = f"INSERT INTO table {cols.names} VALUES {cols.values}"
await conn.execute(query, *cols.args)

args = Args()
search = Cols(args, name="bilbo", age=111)
changes = Cols(args, adventurous=False, hungry=True)
query = f"UPDATE table SET {changes.assignments} WHERE {search.conditions}"
await conn.execute(query, *args)
```

## Args usage

Use `Args` instances in f-strings to build up queries and positional arguments.

```py
from pgargs import Args

# Create an Args instance.
# It supports various methods of adding values,
# both at initialization time and afterwards.
args = Args(name="bilbo", age=111)
args = Args({"name": "bilbo", "age": 111})
args = Args()
args.name = "bilbo"
args["age"] = 111

# Use args in an f-string to create a query and build up positional arguments.
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"

# Unpack args into an asyncpg method to get the positional values.
await conn.fetch(query, *args)

# query = "SELECT * FROM table WHERE name = $1 AND age = $2"
# *args = ("bilbo", 111)
```

## Args usage with `executemany` and `fetchmany`

```py
args = Args()
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"

# Use args as a callable, passing in an iterable of dicts,
# to get an iterable of positional values.
items = [
    {"name": "bilbo", "age": 111},
    {"name": "frodo", "age": 33},
]
await conn.fetchmany(query, args(items))

# query = "SELECT * FROM table WHERE name = $1 AND age = $2"
# list(args(items)) = [("bilbo", 111), ("frodo", 33)]
```

## Piecemeal queries

```py
args = Args()

query = f"SELECT * FROM table WHERE name = {args.name}"
args.name = "bilbo"

if age:
    query += f" AND age = {args.age}"
    args.age = 111

await conn.fetch(query, *args)

# query = "SELECT * FROM table WHERE a = $1 AND b = $2"
# *args = ("bilbo", 111)
```

## Cols usage

Use `Cols` instances to render groups of columns together in queries.

```py
from pgargs import Cols

# Create a Cols instance.
# It supports various methods of adding column names and values,
# at initialization time or afterwards.
cols = Cols("hungry", {"adventurous": False}, covetous=False)
cols["hungry"] = True

# Use cols in an f-string to render all columns together.
query = f"INSERT INTO users {cols.names} VALUES {cols.values}"
await conn.execute(query, *cols.args)

# query = "INSERT INTO users hungry, adventurous, covetous VALUES ($1, $2, $3)"
# *args = (true, false, false)
```

## Cols usage with `executemany` and `fetchmany`

```py
# Create a Cols instance with column names but no values.
cols = Cols("name", "age")
query = f"DELETE FROM users WHERE {cols.conditions}"

# Use cols.args as a callable, passing in an iterable of dicts,
# to get an iterable of positional values.
items = [
    {"name": "bilbo", "age": 111},
    {"name": "frodo", "age": 33},
]
await conn.executemany(query, cols.args(items))

# query = "DELETE FROM users WHERE name = $1 AND age = $2"
# list(cols.args(items)) = [("bilbo", 111), ("frodo", 33)]
```

## Composing cols and args

```py
# Create a shared Args instance to use with multiple Cols instances.
args = Args(rating="s-tier")
search = Cols(args, name="bilbo", age=111)
changes = Cols(args, adventurous=False, hungry=True)

# Build a complex query using an f-string, cols, and args.
query = f"UPDATE users SET {changes.assignments} WHERE {search.conditions} AND rating = {args.rating}"
await conn.execute(query, *args)

# query = "UPDATE users SET adventurous = $1, hungry = $2 WHERE name = $3 AND age = $4 AND rating = $5"
# *args = (true, false, "bilbo", 111, "s-tier")
```
