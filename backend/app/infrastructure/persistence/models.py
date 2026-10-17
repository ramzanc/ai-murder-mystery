from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from app.domain.investigation import InvestigationSession


class Base(DeclarativeBase):
    pass

class InvestigationSessionRow(Base):
    __tablename__ = "investigation_sessions"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        primary_key=True,
    )

    case_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @classmethod
    def from_domain(
        cls,
        *,
        session_id: UUID,
        session: InvestigationSession,
    ) -> "InvestigationSessionRow":
        return cls(
            id=session_id,
            case_id=session.case_id,
            snapshot=session.model_dump(mode="json"),
        )

    def to_domain(self) -> InvestigationSession:
        return InvestigationSession.model_validate(
            self.snapshot
        )

    def replace_snapshot(
        self,
        session: InvestigationSession,
    ) -> None:
        self.case_id = session.case_id
        self.snapshot = session.model_dump(mode="json")