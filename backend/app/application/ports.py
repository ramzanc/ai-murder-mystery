from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID

from app.domain.case import CaseManifest
from app.domain.investigation import InvestigationSession


@dataclass(frozen=True, slots=True)
class SessionRecord:
    id: UUID
    session: InvestigationSession


class CaseFinder(Protocol):
    def __call__(
        self,
        case_id: str,
    ) -> CaseManifest | None:
        ...


class SessionRepository(Protocol):
    async def add(
        self,
        record: SessionRecord,
    ) -> None:
        ...

    async def get(
        self,
        session_id: UUID,
        *,
        for_update: bool = False,
    ) -> SessionRecord | None:
        ...

    async def replace(
        self,
        record: SessionRecord,
    ) -> None:
        ...


class UnitOfWork(Protocol):
    @property
    def sessions(self) -> SessionRepository:
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...
