from contextlib import asynccontextmanager

import decouple
from aiomysql import DatabaseError
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from .database import DatabaseClient
from .routers import root_router
from .utils import ConfigLoader

__all__ = ("app",)


class AppFactory:
    def build(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(ins: FastAPI):
            db_conf = ConfigLoader("config/database.toml")
            ins.state.database = DatabaseClient(**db_conf["dsn"])
            try:
                await ins.state.database.initialize()
            except DatabaseError as e:
                raise RuntimeError("Failed to initialize database client.") from e
            try:
                yield
            finally:
                await ins.state.database.close()

        res = FastAPI(title="TeachCraft", docs_url=None, redoc_url=None, lifespan=lifespan)

        res.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        res.add_middleware(
            SessionMiddleware,
            secret_key=decouple.config("session_secret"),
            session_cookie="session",
            same_site="lax",
            https_only=True,
        )

        @res.exception_handler(HTTPException)
        async def redirect_404_handler(request: Request, exc: HTTPException):
            if exc.status_code == 404:
                return RedirectResponse(url="/")
            return await http_exception_handler(request, exc)

        res.include_router(root_router)
        return res


app = AppFactory().build()
