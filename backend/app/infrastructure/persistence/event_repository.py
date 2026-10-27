from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import (
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PostgreSQLUUID,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.application.event_store import (
    OptimisticConcurrencyError,
)
from app.domain.events import (
    SessionEventPayload,
    StoredSessionEvent,
)
from app.infrastructure.persistence.models import Base

_event_payload_adapter = TypeAdapter(SessionEventPayload)

class SessionEventRow(Base):
    __tablename__ = "session_events"
    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "idempotency_key",
            name=(
                "uq_session_events_session_id_"
                "idempotency_key"
            ),
        ),
    )

    session_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )

    sequence: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    @classmethod
    def from_domain(
        cls,
        event: StoredSessionEvent,
    ) -> "SessionEventRow":
        return cls(
            session_id=event.session_id,
            sequence=event.sequence,
            idempotency_key=event.idempotency_key,
            event_type=event.payload.type,
            payload=event.payload.model_dump(
                mode="json"
            ),
        )

    def to_domain(self) -> StoredSessionEvent:
        payload = _event_payload_adapter.validate_python(
            self.payload
        )

        if payload.type != self.event_type:
            raise ValueError(
                "Stored event type does not match its "
                "payload discriminator."
            )

        return StoredSessionEvent(
            session_id=self.session_id,
            sequence=self.sequence,
            idempotency_key=self.idempotency_key,
            payload=payload,
        )

class SqlAlchemySessionEventRepository:
    def __init__(
        self,
        database: AsyncSession,
    ) -> None:
        self._database = database

    async def append(
        self,
        *,
        session_id: UUID,
        expected_version: int,
        idempotency_key: str,
        payload: SessionEventPayload,
    ) -> StoredSessionEvent:
        duplicate_statement = select(
            SessionEventRow
        ).where(
            SessionEventRow.session_id == session_id,
            SessionEventRow.idempotency_key
            == idempotency_key,
        )

        duplicate_result = await self._database.execute(
            duplicate_statement
        )
        duplicate = duplicate_result.scalar_one_or_none()

        if duplicate is not None:
            return duplicate.to_domain()

        version_statement = select(
            func.coalesce(
                func.max(SessionEventRow.sequence),
                0,
            )
        ).where(
            SessionEventRow.session_id == session_id
        )

        version_result = await self._database.execute(
            version_statement
        )
        current_version = int(version_result.scalar_one())

        if current_version != expected_version:
            raise OptimisticConcurrencyError(
                f"Session {session_id} is at version "
                f"{current_version}; expected "
                f"{expected_version}."
            )

        stored_event = StoredSessionEvent(
            session_id=session_id,
            sequence=current_version + 1,
            idempotency_key=idempotency_key,
            payload=payload,
        )

        self._database.add(
            SessionEventRow.from_domain(stored_event)
        )

        await self._database.flush()

        return stored_event

    async def list_for_session(
        self,
        session_id: UUID,
    ) -> tuple[StoredSessionEvent, ...]:
        statement = (
            select(SessionEventRow)
            .where(
                SessionEventRow.session_id == session_id
            )
            .order_by(SessionEventRow.sequence)
        )

        result = await self._database.execute(statement)

        return tuple(
            row.to_domain()
            for row in result.scalars().all()
        )

