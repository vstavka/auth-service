from collections.abc import Iterable
from uuid6 import UUID, uuid7

from src.application.ports.system.id_generator import IdGenerator


class FakeIdGenerator(IdGenerator):
    def __init__(
        self,
        ids: Iterable[UUID] | None = None,
    ) -> None:
        self._ids = iter(ids or [])
        self.generated_ids: list[UUID] = []

    def new(self) -> UUID:
        try:
            value = next(self._ids)
        except StopIteration:
            value = uuid7()

        self.generated_ids.append(value)

        return value