from typing import Protocol
from uuid import UUID

from app.domain.events import (
    SessionEventPayload,
    StoredSessionEvent,
    replay_session,
)
from app.domain.investigation import InvestigationSession

class OptimisticConcurrencyError(RuntimeError):
    """Raised when a stream changed after it was read."""


class SessionEventRepository(Protocol):
    async def append(
        self,
        *,
        session_id: UUID,
        expected_version: int,
        idempotency_key: str,
        payload: SessionEventPayload,
    ) -> StoredSessionEvent:
        ...

    async def list_for_session(
        self,
        session_id: UUID,
    ) -> tuple[StoredSessionEvent, ...]:
        ...


class EventStore:
    def __init__(
        self,
        repository: SessionEventRepository,
    ) -> None:
        self._repository = repository

    async def append(
        self,
        *,
        session_id: UUID,
        expected_version: int,
        idempotency_key: str,
        payload: SessionEventPayload,
    ) -> StoredSessionEvent:
        if expected_version < 0:
            raise ValueError(
                "Expected version cannot be negative."
            )

        if not idempotency_key.strip():
            raise ValueError(
                "Idempotency key cannot be blank."
            )

        return await self._repository.append(
            session_id=session_id,
            expected_version=expected_version,
            idempotency_key=idempotency_key,
            payload=payload,
        )

    async def load(
        self,
        session_id: UUID,
    ) -> tuple[StoredSessionEvent, ...]:
        return await self._repository.list_for_session(
            session_id
        )

    async def rebuild_session(
        self,
        session_id: UUID,
    ) -> InvestigationSession:
        events = await self.load(session_id)
        return replay_session(events)