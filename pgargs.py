from typing import Any, Iterator, Optional, Union, Generator, Iterable, overload


class Args:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._refs: dict[str, str] = {}
        self._vals: dict[str, Any] = {}
        for key, value in dict(*args, **kwargs).items():
            self[key] = value

    # Unpacking values

    def __iter__(self) -> Iterator[Any]:
        return iter(self._vals[key] for key in self._refs)

    # Call to get values or many values

    @overload
    def __call__(
        self,
        /,
        **kwargs: Any,
    ) -> tuple[Any, ...]: ...

    @overload
    def __call__(
        self,
        items: Iterable[dict[str, Any]],
        /,
        **kwargs: Any,
    ) -> Generator[tuple[Any, ...], None, None]: ...

    def __call__(
        self,
        items: Optional[Iterable[dict[str, Any]]] = None,
        /,
        **kwargs: Any,
    ) -> Union[tuple[Any, ...], Iterable[tuple[Any, ...]]]:
        if items is None:
            vals = self._vals | kwargs
            return tuple(vals[key] for key in self._refs)
        else:
            return self._values_many(items, kwargs)

    def _values_many(
        self,
        items: Iterable[dict[str, Any]],
        kwargs: dict[str, Any],
    ) -> Generator[tuple[Any, ...], None, None]:
        for item in items:
            vals = self._vals | kwargs | item
            yield tuple(vals[key] for key in self._refs)

    # Dictionary access

    def __getitem__(self, key: str) -> str:
        if key not in self._refs:
            self._refs[key] = f"${len(self._refs) + 1}"
        return self._refs[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._vals[key] = value

    # Attributes access

    def __getattr__(self, name: str) -> str:
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value


class Cols:
    def __init__(
        self,
        *args_or_names_or_data: Union[Args, str, dict[str, Any]],
        **kwargs: Any,
    ) -> None:
        args: Optional[Args] = None
        names: list[str] = []
        data: dict[str, Any] = {}

        for item in args_or_names_or_data:
            if isinstance(item, Args):
                if args is not None:
                    raise ValueError("multiple args values provided")
                args = item
            elif isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                data.update(item)
            else:
                raise TypeError(item)

        self.args = args if args is not None else Args()

        self._keys: dict[str, None] = {}  # use as an ordered set
        self.add(*names)
        self.update(data | kwargs)

    def __len__(self) -> int:
        return len(self._keys)

    def __getitem__(self, key: str) -> Any:
        return self.args._vals[key]

    def __setitem__(self, key, value) -> None:
        self.args[key] = value
        self._keys[key] = None

    def add(self, *keys: str) -> None:
        for key in keys:
            self.args[key]
            self._keys[key] = None

    def update(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            self[key] = value

    @property
    def assignments(self) -> str:
        if not self._keys:
            raise ValueError
        return ", ".join(f"{key} = {self.args[key]}" for key in self._keys.keys())

    @property
    def conditions(self) -> str:
        if not self._keys:
            raise ValueError
        return " AND ".join(f"{key} = {self.args[key]}" for key in self._keys.keys())

    @property
    def names(self) -> str:
        if not self._keys:
            raise ValueError
        return "(" + ", ".join(self._keys.keys()) + ")"

    @property
    def values(self) -> str:
        if not self._keys:
            raise ValueError
        return "(" + ", ".join(self.args[key] for key in self._keys.keys()) + ")"
