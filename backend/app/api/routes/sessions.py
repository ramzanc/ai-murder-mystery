from typing import Annotated
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.cases import find_case
from app.api.schemas import (
    AskQuestionRequest,
    CreateSessionRequest,
    PublicEvidenceResponse,
    SessionResponse,
    SubmitTheoryRequest,
    TheoryScoreResponse,
    TheorySubmissionResponse,
)
from app.application.investigation_service import (
    InvestigationAlreadyFinalizedError,
    InvestigationError,
    ask_question,
    start_session,
    submit_final_theory,
)
from app.infrastructure.database import get_db_session
from app.infrastructure.persistence.models import (
    InvestigationSessionRow,
)


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


async def _find_session_row(
    session_id: UUID,
    database: AsyncSession,
    *,
    for_update: bool = False,
) -> InvestigationSessionRow:
    statement = select(
        InvestigationSessionRow
    ).where(
        InvestigationSessionRow.id == session_id
    )

    if for_update:
        statement = statement.with_for_update()

    result = await database.execute(statement)
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Session {str(session_id)!r} "
                "was not found."
            ),
        )

    return row


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: CreateSessionRequest,
    database: DatabaseSession,
) -> SessionResponse:
    case = find_case(request.case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Case {request.case_id!r} "
                "was not found."
            ),
        )

    session_id = uuid4()
    domain_session = start_session(case)

    row = InvestigationSessionRow.from_domain(
        session_id=session_id,
        session=domain_session,
    )

    async with database.begin():
        database.add(row)

    return SessionResponse.from_domain(
        session_id=session_id,
        session=domain_session,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_session(
    session_id: UUID,
    database: DatabaseSession,
) -> SessionResponse:
    row = await _find_session_row(
        session_id,
        database,
    )

    domain_session = row.to_domain()

    return SessionResponse.from_domain(
        session_id=row.id,
        session=domain_session,
    )


@router.get(
    "/{session_id}/evidence",
    response_model=tuple[PublicEvidenceResponse, ...],
    status_code=status.HTTP_200_OK,
)
async def get_discovered_evidence(
    session_id: UUID,
    database: DatabaseSession,
) -> tuple[PublicEvidenceResponse, ...]:
    row = await _find_session_row(
        session_id,
        database,
    )

    domain_session = row.to_domain()
    case = find_case(domain_session.case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Case {domain_session.case_id!r} "
                "was not found."
            ),
        )

    discovered_ids = set(
        domain_session.discovered_evidence_ids
    )

    return tuple(
        PublicEvidenceResponse.from_domain(evidence)
        for evidence in case.initial_evidence
        if str(evidence.id) in discovered_ids
    )


@router.post(
    "/{session_id}/questions",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def question_suspect(
    session_id: UUID,
    request: AskQuestionRequest,
    database: DatabaseSession,
) -> SessionResponse:
    async with database.begin():
        row = await _find_session_row(
            session_id,
            database,
            for_update=True,
        )

        domain_session = row.to_domain()
        case = find_case(domain_session.case_id)

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Case {domain_session.case_id!r} "
                    "was not found."
                ),
            )

        try:
            updated_session = ask_question(
                case=case,
                session=domain_session,
                suspect_id=request.suspect_id,
                topic=request.to_domain_topic(),
            )
        except InvestigationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        row.replace_snapshot(updated_session)

    return SessionResponse.from_domain(
        session_id=row.id,
        session=updated_session,
    )


@router.post(
    "/{session_id}/theory",
    response_model=TheorySubmissionResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_theory(
    session_id: UUID,
    request: SubmitTheoryRequest,
    database: DatabaseSession,
) -> TheorySubmissionResponse:
    async with database.begin():
        row = await _find_session_row(
            session_id,
            database,
            for_update=True,
        )

        domain_session = row.to_domain()
        case = find_case(domain_session.case_id)

        if case is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Case {domain_session.case_id!r} "
                    "was not found."
                ),
            )

        try:
            updated_session, score = (
                submit_final_theory(
                    case=case,
                    session=domain_session,
                    theory=request.to_domain(),
                )
            )
        except InvestigationAlreadyFinalizedError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc
        except InvestigationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        row.replace_snapshot(updated_session)

    return TheorySubmissionResponse(
        session=SessionResponse.from_domain(
            session_id=row.id,
            session=updated_session,
        ),
        score=TheoryScoreResponse.from_domain(score),
    )