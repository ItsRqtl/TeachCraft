from .base import BaseDAO
from .users_dao import UsersDAO

__all__ = ("DAO_CLASSES", "BaseDAO")

DAO_CLASSES = {
    "users": UsersDAO,
}
