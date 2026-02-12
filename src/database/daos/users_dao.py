import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid7

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .base import BaseDAO


class UsersDAO(BaseDAO):
    ph = PasswordHasher()

    async def initialize(self) -> None:
        async with self.db.acquire(is_initializing=True) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id UUID,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        verified BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (id)
                    );
                    """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_tokens (
                        id UUID,
                        user_id UUID,
                        purpose ENUM('email', 'password') NOT NULL,
                        token_hash BINARY(32) NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        PRIMARY KEY (id),
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                    """)

    async def get_user(self, user_id: str) -> dict | None:
        async with self.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
                return await cur.fetchone()

    async def get_user_by_email(self, email: str) -> dict | None:
        async with self.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
                return await cur.fetchone()

    async def verify_user_credentials(self, email: str, password: str) -> str | None:
        user = await self.get_user_by_email(email)
        if not user:
            return
        try:
            self.ph.verify(user["password_hash"], password)
            return str(user["id"])
        except (VerificationError, VerifyMismatchError, InvalidHashError):
            return

    async def create_user(self, email: str, password: str) -> str:
        user_id = uuid7()
        password_hash = self.ph.hash(password)
        async with self.db.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (id, email, password_hash)
                    VALUES (%s, %s, %s);
                    """,
                    (user_id, email, password_hash),
                )
                await conn.commit()
        return str(user_id)

    async def create_token(self, user_id: str, purpose: str, validity_seconds: int = 3600) -> str:
        if purpose not in ("email", "password"):
            raise ValueError("Invalid token purpose.")
        async with self.db.acquire() as conn:
            async with conn.cursor() as cur:
                token_id = uuid7()
                raw = secrets.token_urlsafe(32)
                hashed = self.db.keyring.hash_token(purpose, raw)
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=validity_seconds)

                await cur.execute(
                    "DELETE FROM user_tokens WHERE user_id = %s AND purpose = %s;",
                    (user_id, purpose),
                )
                await cur.execute(
                    """
                    INSERT INTO user_tokens (id, user_id, purpose, token_hash, expires_at)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    (token_id, user_id, purpose, hashed, expires_at),
                )
                await conn.commit()
        return raw
