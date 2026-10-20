from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
)

from app.application.ports import SessionRecord
from app.infrastructure.persistence.models import (
    InvestigationSessionRow,
)


class SqlAlchemySessionRepository:
    def __init__(
        self,
        database: AsyncSession,
    ) -> None:
        self._database = database

    async def add(
        self,
        record: SessionRecord,
    ) -> None:
        row = InvestigationSessionRow.from_domain(
            session_id=record.id,
            session=record.session,
        )

        self._database.add(row)

    async def get(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> SessionRecord | None:
        statement = select(
            InvestigationSessionRow
        ).where(
            InvestigationSessionRow.id == session_id
        )

        if for_update:
            statement = statement.with_for_update()

        result = await self._database.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            return None

        return SessionRecord(
            id=row.id,
            session=row.to_domain(),
        )

    async def replace(
        self,
        record: SessionRecord,
    ) -> None:
        statement = select(
            InvestigationSessionRow
        ).where(
            InvestigationSessionRow.id == record.id
        )

        result = await self._database.execute(statement)
        row = result.scalar_one_or_none()

        if row is None:
            raise LookupError(
                f"Session {str(record.id)!r} was not found."
            )

        row.replace_snapshot(record.session)


class SqlAlchemyUnitOfWork:
    def __init__(
        self,
        database: AsyncSession,
    ) -> None:
        self._database = database
        self._transaction: (
            AsyncSessionTransaction | None
        ) = None

        self.sessions = SqlAlchemySessionRepository(
            database
        )

    async def __aenter__(self) -> Self:
        self._transaction = self._database.begin()
        await self._transaction.__aenter__()

        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is None:
            raise RuntimeError(
                "Unit of work was not entered."
            )

        transaction = self._transaction
        self._transaction = None

        await transaction.__aexit__(
            exception_type,
            exception,
            traceback,
        )
