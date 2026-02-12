from fastapi import APIRouter

from .session import session_router

__all__ = ("root_router",)

root_router = APIRouter(include_in_schema=False)
root_router.include_router(session_router)
