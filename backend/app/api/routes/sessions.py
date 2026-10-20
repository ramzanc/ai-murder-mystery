from typing import Never
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies import (
    InvestigationUseCasesDependency,
)
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
    CaseNotFoundError,
    InvestigationAlreadyFinalizedError,
    InvestigationError,
    SessionNotFoundError,
)


router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)


def _raise_not_found(
    error: CaseNotFoundError | SessionNotFoundError,
) -> Never:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    request: CreateSessionRequest,
    use_cases: InvestigationUseCasesDependency,
) -> SessionResponse:
    try:
        record = await use_cases.create_session(
            request.case_id
        )
    except CaseNotFoundError as exc:
        _raise_not_found(exc)

    return SessionResponse.from_domain(
        session_id=record.id,
        session=record.session,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_session(
    session_id: UUID,
    use_cases: InvestigationUseCasesDependency,
) -> SessionResponse:
    try:
        record = await use_cases.get_session(session_id)
    except SessionNotFoundError as exc:
        _raise_not_found(exc)

    return SessionResponse.from_domain(
        session_id=record.id,
        session=record.session,
    )


@router.get(
    "/{session_id}/evidence",
    response_model=tuple[PublicEvidenceResponse, ...],
    status_code=status.HTTP_200_OK,
)
async def get_discovered_evidence(
    session_id: UUID,
    use_cases: InvestigationUseCasesDependency,
) -> tuple[PublicEvidenceResponse, ...]:
    try:
        evidence_items = (
            await use_cases.get_discovered_evidence(
                session_id
            )
        )
    except (
        CaseNotFoundError,
        SessionNotFoundError,
    ) as exc:
        _raise_not_found(exc)

    return tuple(
        PublicEvidenceResponse.from_domain(evidence)
        for evidence in evidence_items
    )


@router.post(
    "/{session_id}/questions",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def question_suspect(
    session_id: UUID,
    request: AskQuestionRequest,
    use_cases: InvestigationUseCasesDependency,
) -> SessionResponse:
    try:
        record = await use_cases.question_suspect(
            session_id=session_id,
            suspect_id=request.suspect_id,
            topic=request.to_domain_topic(),
        )
    except (
        CaseNotFoundError,
        SessionNotFoundError,
    ) as exc:
        _raise_not_found(exc)
    except InvestigationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SessionResponse.from_domain(
        session_id=record.id,
        session=record.session,
    )


@router.post(
    "/{session_id}/theory",
    response_model=TheorySubmissionResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_theory(
    session_id: UUID,
    request: SubmitTheoryRequest,
    use_cases: InvestigationUseCasesDependency,
) -> TheorySubmissionResponse:
    try:
        record, score = await use_cases.submit_theory(
            session_id=session_id,
            theory=request.to_domain(),
        )
    except (
        CaseNotFoundError,
        SessionNotFoundError,
    ) as exc:
        _raise_not_found(exc)
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

    return TheorySubmissionResponse(
        session=SessionResponse.from_domain(
            session_id=record.id,
            session=record.session,
        ),
        score=TheoryScoreResponse.from_domain(score),
    )
