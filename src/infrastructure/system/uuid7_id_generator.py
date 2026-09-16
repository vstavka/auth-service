from uuid import UUID

from uuid6 import uuid7

from src.application.ports.system import IdGenerator


class UUID7IdGenerator(IdGenerator):
    def new(self) -> UUID:
        return uuid7()
