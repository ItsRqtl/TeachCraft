from typing import Any, Dict, Optional, TypeVar, overload

import tomli

__all__ = ("ConfigLoader",)

T = TypeVar("T")


class ConfigLoader:
    def __init__(self, path: str) -> None:
        self._path = path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        with open(self._path, "rb") as f:
            return tomli.load(f)

    @overload
    def get(self, key: str) -> Any: ...

    @overload
    def get(self, key: str, default: T) -> T: ...

    def get(self, key: str, default: Optional[T] = None) -> Any:
        data = self._config
        for k in key.split("."):
            if k in data:
                data = data[k]
            else:
                return default
        return data

    def reload(self) -> None:
        self._config = self._load_config()

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    def __getitem__(self, key: str) -> Any:
        return self.get(key)
