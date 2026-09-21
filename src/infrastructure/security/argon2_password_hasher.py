from pwdlib.hashers.argon2 import Argon2Hasher

from src.application.ports.security import PasswordHasher
from src.domain.value_objects import PasswordHash


class Argon2PasswordHasher(PasswordHasher):

    def __init__(self):
        self._password_hash = Argon2Hasher()

    def hash(self, raw_password: str) -> PasswordHash:
        return PasswordHash(self._password_hash.hash(raw_password))

    def verify(
            self,
            raw_password: str,
            password_hash: PasswordHash,
    ) -> bool:
        return self._password_hash.verify(raw_password, password_hash.value)
