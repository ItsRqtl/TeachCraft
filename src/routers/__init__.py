from fastapi import APIRouter

__all__ = ("root_router",)

root_router = APIRouter(include_in_schema=False)
