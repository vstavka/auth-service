from hashlib import sha256

from src.application.ports.security import PasswordHasher
from src.domain.value_objects import PasswordHash


class FakePasswordHasher(PasswordHasher):
    PREFIX = "fake-hash:"

    def hash(self, raw_password: str) -> PasswordHash:
        digest = sha256(raw_password.encode("utf-8")).hexdigest()
        return PasswordHash(f"{self.PREFIX}{digest}")

    def verify(
        self,
        raw_password: str,
        password_hash: PasswordHash,
    ) -> bool:
        return self.hash(raw_password) == password_hash
