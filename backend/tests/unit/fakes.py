from types import TracebackType
from typing import Self
from uuid import UUID

from app.application.ports import SessionRecord


class FakeSessionRepository:
    def __init__(
        self,
        records: dict[UUID, SessionRecord] | None = None,
    ) -> None:
        self.records = (
            records
            if records is not None
            else {}
        )

    async def add(
        self,
        record: SessionRecord,
    ) -> None:
        if record.id in self.records:
            raise ValueError(
                f"Duplicate session: {record.id}"
            )

        self.records[record.id] = record

    async def get(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> SessionRecord | None:
        del for_update
        return self.records.get(session_id)

    async def replace(
        self,
        record: SessionRecord,
    ) -> None:
        if record.id not in self.records:
            raise LookupError(
                f"Session {str(record.id)!r} was not found."
            )

        self.records[record.id] = record


class FakeUnitOfWork:
    def __init__(
        self,
        sessions: FakeSessionRepository | None = None,
    ) -> None:
        self.sessions = (
            sessions
            if sessions is not None
            else FakeSessionRepository()
        )

        self.enter_count = 0
        self.commit_count = 0
        self.rollback_count = 0

        self._snapshot: (
            dict[UUID, SessionRecord] | None
        ) = None

    async def __aenter__(self) -> Self:
        if self._snapshot is not None:
            raise RuntimeError(
                "Unit of work is already active."
            )

        self.enter_count += 1
        self._snapshot = self.sessions.records.copy()

        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exception, traceback

        if self._snapshot is None:
            raise RuntimeError(
                "Unit of work was not entered."
            )

        if exception_type is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1
            self.sessions.records.clear()
            self.sessions.records.update(
                self._snapshot
            )

        self._snapshot = None