import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

__all__ = ("Keyring",)


class Keyring:
    def __init__(self, master: str, context: str):
        """
        Initialize the keyring system.
        """
        ctx = context.encode("utf-8")
        ikm = bytes.fromhex(master)
        salt = b"hkdf_salt:" + ctx

        def hkdf(label: str) -> bytes:
            info = ctx + b":" + label.encode("utf-8")
            return HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=info,
            ).derive(ikm)

        self.enc_key = hkdf("encryption")
        self.token_mac_key = hkdf("token_mac")
        self.password_mac_key = hkdf("password_mac")
        self.session_secret_key = hkdf("session_secret")

    def get_session_secret(self) -> str:
        return self.session_secret_key.hex()

    def encrypt(self, secret: bytes) -> bytes:
        aesgcm = AESGCM(self.enc_key)
        nonce = self.generate_secret(12)
        ciphertext = aesgcm.encrypt(nonce, secret, None)
        return nonce + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        aesgcm = AESGCM(self.enc_key)
        nonce = data[:12]
        ciphertext = data[12:]
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def generate_secret(length: int = 32) -> bytes:
        return os.urandom(length)
