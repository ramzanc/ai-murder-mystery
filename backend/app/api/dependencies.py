from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.cases import find_case
from app.application.ai_ports import StructuredLLMClient
from app.application.intent_service import IntentClassifier
from app.application.interrogation_service import (
    InterrogationService,
)
from app.application.investigation_service import (
    InvestigationUseCases,
)
from app.application.ports import UnitOfWork
from app.application.suspect_dialogue import (
    SuspectDialogueGenerator,
)
from app.application.suspect_planner import SuspectPlanner
from app.config import Settings, get_settings
from app.infrastructure.ai.llm_client import (
    OpenAIStructuredLLMClient,
)
from app.infrastructure.ai.ollama_client import (
    OllamaStructuredLLMClient,
)
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


SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]


async def get_structured_llm_client(
    settings: SettingsDependency,
) -> AsyncIterator[StructuredLLMClient]:
    if settings.llm_provider == "openai":
        client = OpenAIStructuredLLMClient(
            model=settings.openai_model,
            timeout_seconds=(
                settings.openai_timeout_seconds
            ),
            max_retries=settings.openai_max_retries,
        )
    else:
        client = OllamaStructuredLLMClient(
            model=settings.ollama_model,
            host=settings.ollama_host,
            timeout_seconds=(
                settings.ollama_timeout_seconds
            ),
            num_ctx=settings.ollama_num_ctx,
        )

    try:
        yield client
    finally:
        await client.close()


StructuredLLMClientDependency = Annotated[
    StructuredLLMClient,
    Depends(get_structured_llm_client),
]


def get_interrogation_service(
    investigation_use_cases: (
        InvestigationUseCasesDependency
    ),
    llm_client: StructuredLLMClientDependency,
    settings: SettingsDependency,
) -> InterrogationService:
    model = (
        settings.openai_model
        if settings.llm_provider == "openai"
        else settings.ollama_model
    )

    return InterrogationService(
        investigation_use_cases=(
            investigation_use_cases
        ),
        find_case=find_case,
        intent_classifier=IntentClassifier(
            llm_client=llm_client,
        ),
        planner=SuspectPlanner(
            llm_client=llm_client,
        ),
        dialogue_generator=(
            SuspectDialogueGenerator(
                llm_client=llm_client,
            )
        ),
        provider=settings.llm_provider,
        model=model,
    )


InterrogationServiceDependency = Annotated[
    InterrogationService,
    Depends(get_interrogation_service),
]