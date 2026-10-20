from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.cases import find_case
from app.application.investigation_service import (
    InvestigationUseCases,
)
from app.application.ports import UnitOfWork
from app.infrastructure.database import get_db_session
from app.infrastructure.persistence.repositories import (
    SqlAlchemyUnitOfWork,
)


DatabaseSessionDependency = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


def get_unit_of_work(
    database: DatabaseSessionDependency,
) -> UnitOfWork:
    return SqlAlchemyUnitOfWork(database)


UnitOfWorkDependency = Annotated[
    UnitOfWork,
    Depends(get_unit_of_work),
]


def get_investigation_use_cases(
    unit_of_work: UnitOfWorkDependency,
) -> InvestigationUseCases:
    return InvestigationUseCases(
        unit_of_work=unit_of_work,
        find_case=find_case,
    )


InvestigationUseCasesDependency = Annotated[
    InvestigationUseCases,
    Depends(get_investigation_use_cases),
]
