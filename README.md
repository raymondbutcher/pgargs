# pgargs

A tiny library for creating asyncpg queries with f-strings
and named arguments.

asyncpg only supports positional arguments, not named arguments.
This helps with rendering queries and positional arguments for asyncpg
using f-strings and named arguments.

## What it looks like

Lower level arguments usage:

```py
args = Args(name="bilbo", age=111)
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"
await conn.fetch(query, *args)
```

Higher level columns usage:

```py
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

Use the `Args` class in f-strings to build up queries and positional arguments.

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

# Use the args instance in an f-string to create a query
# and build up positional arguments.
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"

# Unpack args into asyncpg method to get the positional values.
await conn.fetch(query, *args)

# query = "SELECT * FROM table WHERE name = $1 AND age = $2"
# *args = ("bilbo", 111)
```

## Args usage with `executemany` and `fetchmany`

```py
items = [
    {"name": "bilbo", "age": 111},
    {"name": "frodo", "age": 33},
]

# Use an empty args instance in an f-string to create a query
# and build up positional arguments.
args = Args()
query = f"SELECT * FROM table WHERE name = {args.name} AND age = {args.age}"

# Use the args instance as a callable, passing in an iterable of dicts,
# to generate an iterable of positional values.
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

```py
from pgargs import Cols

# Create a cols instance.
# It supports various methods of adding column names and values,
# at initialization time or afterwards.
cols = Cols({"adventurous": True}, hungry=False)
cols["covetous"] = True

query = f"INSERT INTO users {cols.names} VALUES {cols.values}"
await conn.execute(query, *cols.args)

# query = "INSERT INTO users adventurous, hungry, covetous VALUES ($1, $2, $3)"
# *args = (true, false, true)
```

## Cols usage with `executemany` and `fetchmany`

```py
# Start with a list of items to delete.
items = [
    {"name": "bilbo", "age": 111},
    {"name": "frodo", "age": 33},
]

# Create cols with the relevant column names but no values.
cols = Cols("name", "age")
query = f"DELETE FROM users WHERE {cols.conditions}"

# Use cols.args(items) to generate an iterable of value tuples.
await conn.executemany(query, cols.args(items))

# query = "DELETE FROM users WHERE name = $1 AND age = $2"
# list(cols.args(items)) = [("bilbo", 111), ("frodo", 33)]
```

## Composing cols and args

```py
args = Args(rating="s-tier")
search = Cols(args, name="bilbo", age=111)
changes = Cols(args, adventurous=False, hungry=True)

query = f"UPDATE users SET {changes.assignments} WHERE {search.conditions} AND rating = {args.rating}"
await conn.execute(query, *args)

# query = "UPDATE users SET adventurous = $1, hungry = $2 WHERE name = $3 AND age = $4 AND rating = $5"
# *args = (true, false, "bilbo", 111, "s-tier")
```
