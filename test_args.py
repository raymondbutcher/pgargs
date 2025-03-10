from pgargs import Args
import pytest


def test_init() -> None:
    # Initialize args and add values values using all available methods.
    args = Args({"a": "init.dict.a"}, b="init.kwargs.b")
    args.c = "set.attr.c"
    args["d"] = "set.dict.d"

    # Access all arguments, one of them has no value yet.
    assert f"{args.a}, {args.b}, {args.c}, {args.d}, {args.e}" == "$1, $2, $3, $4, $5"

    # Call the args, including the final value as a keyword argument,
    # and check all values get returned.
    assert args(e="call.kwargs.e") == (
        "init.dict.a",
        "init.kwargs.b",
        "set.attr.c",
        "set.dict.d",
        "call.kwargs.e",
    )


def test_call_error() -> None:
    # Access two arguments.
    args = Args()
    assert f"{args.a}, {args.b}" == "$1, $2"

    # Call the args without providing values for all accessed arguments.
    with pytest.raises(KeyError):
        assert args(a=1)


def test_call_success() -> None:
    # Args can be called to include more values.
    # The returned values will be merged from 2 places.
    args = Args({"a": "args.a", "b": "args.b"})  # lowest priority
    kwargs = {"b": "kwargs.b"}  # highest priority

    # Access both arguments.
    assert f"{args.a}, {args.b}" == "$1, $2"

    # Call the args and check where values came from.
    assert args(**kwargs) == ("args.a", "kwargs.b")


def test_call_iterable_error() -> None:
    # Access two arguments.
    args = Args()
    assert f"{args.a}, {args.b}" == "$1, $2"

    # Call the args without providing values for all accessed arguments.
    items = ({"a": f"items.{i}.a"} for i in range(3))
    with pytest.raises(KeyError):
        assert list(args(items))


def test_call_iterable_success() -> None:
    # Args can be called with an iterable,
    # for use with executemany and fetchmany.
    # The final values will be merged from 3 places.
    args = Args({"a": "args.a", "b": "args.b", "c": "args.c"})  # lowest priority
    kwargs = {"a": "kwargs.a", "b": "kwargs.b"}  # middle priority
    items = ({"a": f"items.{i}.a"} for i in range(3))  # highest priority

    # Access all 3 arguments.
    assert f"{args.a}, {args.b}, {args.c}" == "$1, $2, $3"

    # Call the args and check where values came from.
    assert list(args(items, **kwargs)) == [
        ("items.0.a", "kwargs.b", "args.c"),
        ("items.1.a", "kwargs.b", "args.c"),
        ("items.2.a", "kwargs.b", "args.c"),
    ]


def test_unpack_error() -> None:
    args = Args()
    assert f"{args.a}" == "$1"

    # Trying to unpack these args will raise an error because
    # not all accessed arguments have values.
    with pytest.raises(KeyError):
        assert [*args]


def test_unpack_success() -> None:
    args = Args({"a": 1}, b=2, c=3)

    # Unpacking returns nothing when nothing has been accessed.
    assert [*args] == []

    # Access some arguments.
    assert f"{args.a}, {args.b}" == "$1, $2"

    # Unpacking returns the values of the arguments that were accessed.
    assert [*args] == [1, 2]
