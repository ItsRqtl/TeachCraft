import asyncio
from email.mime.text import MIMEText

import aiosmtplib

__all__ = ("Mailer",)


class Mailer:
    _ready = asyncio.Event()

    def __init__(self, host: str, port: int, username: str, password: str, use_tls: bool = True, sender: str = None):
        self.sender = sender or username
        self.server = aiosmtplib.SMTP(
            hostname=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_tls,
        )

    async def initialize(self):
        await self.server.connect()
        self._ready.set()

    async def wait_until_ready(self):
        await self._ready.wait()

    async def close(self):
        if not self._ready.is_set():
            raise RuntimeError("Mailer is not initialized.")
        self._ready.clear()
        await self.server.quit()

    async def send_email_verification(self, recipient: str, token: str):
        message = MIMEText(
            "Please verify your email by clicking the following link:\n\nhttps://example.com/verify-email?token="
            + token
        )
        message["Subject"] = "TeachCraft: Email Verification"
        message["From"] = f"TeachCraft <{self.sender}>"
        message["To"] = recipient
        await self.server.send_message(message)
