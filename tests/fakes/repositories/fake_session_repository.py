from src.application.ports.repositories import SessionRepository
from src.domain.entities import Session
from src.domain.value_objects import RefreshTokenHash, SessionId


class FakeSessionRepository(SessionRepository):

    def __init__(self):
        self._by_public_id: dict[SessionId, Session] = {}
        self._by_refresh_token_hash: dict[str, Session] = {}
        self._next_id = 1

    async def add(self, session: Session) -> None:
        if session.id is None:
            session.id = self._next_id
            self._next_id += 1
        self._by_public_id[session.public_id] = session
        self._by_refresh_token_hash[session.refresh_token_hash.value] = session

    async def get_by_public_id(self, public_id: SessionId) -> Session | None:
        return self._by_public_id.get(public_id)

    async def get_by_refresh_token_hash(
            self,
            token_hash: RefreshTokenHash,
    ) -> Session | None:
        return self._by_refresh_token_hash.get(token_hash.value)

    async def list_by_account_id(self, account_id: int) -> list[Session]:
        return [
            session
            for session in self._by_public_id.values()
            if session.account_id == account_id
        ]

    async def save(self, session: Session) -> None:
        stale_hashes = [
            token_hash
            for token_hash, stored in self._by_refresh_token_hash.items()
            if stored.public_id == session.public_id
               and token_hash != session.refresh_token_hash.value
        ]
        for token_hash in stale_hashes:
            del self._by_refresh_token_hash[token_hash]
        self._by_public_id[session.public_id] = session
        self._by_refresh_token_hash[session.refresh_token_hash.value] = session
