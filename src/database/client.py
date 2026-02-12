import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Optional

import aiomysql

from ..utils import Keyring
from .daos import DAO_CLASSES, BaseDAO

__all__ = ("DatabaseClient",)


class DatabaseClient:
    _ready = asyncio.Event()

    def __init__(self, host: str, port: int, user: str, password: str, db: str, keyring: Keyring) -> None:
        self._dsn = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "db": db,
        }
        self.keyring = keyring
        self._pool: Optional[aiomysql.Pool] = None
        self._daos: Dict[str, BaseDAO] = {}
        for n, c in DAO_CLASSES.items():
            if hasattr(self, n):
                raise RuntimeError(f"DAO name {n} conflicts with existing attribute.")
            if not isinstance(c, type) or not issubclass(c, BaseDAO):
                raise TypeError(f"DAO class {c!r} is not a subclass of BaseDAO.")
            dao = c(self)
            setattr(self, n, dao)
            self._daos[n] = dao

    # ---------- lifecycle ----------
    async def initialize(self) -> None:
        if self._pool or self._ready.is_set():
            raise RuntimeError("Database client is already initialized.")
        self._pool = await aiomysql.create_pool(**self._dsn, autocommit=True, cursorclass=aiomysql.DictCursor)
        for dao in self._daos.values():
            await dao.initialize()
        self._ready.set()

    async def wait_until_ready(self) -> None:
        await self._ready.wait()

    async def close(self) -> None:
        if not self._pool or not self._ready.is_set():
            raise RuntimeError("Database client is not initialized.")
        self._ready.clear()
        self._pool.close()
        await self._pool.wait_closed()
        self._pool = None

    # ---------- low-level helpers ----------
    @asynccontextmanager
    async def acquire(self, is_initializing: bool = False) -> AsyncGenerator[aiomysql.Connection, None]:
        if not self._pool or (not self._ready.is_set() and not is_initializing):
            raise RuntimeError("Database client is not initialized.")
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self):
        async with self.acquire() as conn:
            try:
                await conn.begin()
                async with conn.cursor() as cur:
                    yield cur
                await conn.commit()
            except Exception:
                await conn.rollback()
                raise
