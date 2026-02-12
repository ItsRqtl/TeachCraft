from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import DatabaseClient

__all__ = ("BaseDAO",)


class BaseDAO(ABC):
    def __init__(self, db: "DatabaseClient") -> None:
        self.db = db

    async def wait_until_ready(self) -> None:
        await self.db.wait_until_ready()

    @abstractmethod
    async def initialize(self) -> None: ...
