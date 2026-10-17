from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

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
from app.domain.investigation import InvestigationSession

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
)

_SESSIONS: dict[UUID, InvestigationSession] = {}

def _find_session(
    session_id: UUID,
) -> InvestigationSession:
    session = _SESSIONS.get(session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Session {str(session_id)!r} "
                "was not found."
            ),
        )

    return session


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    request: CreateSessionRequest,
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
    session = start_session(case)

    _SESSIONS[session_id] = session

    return SessionResponse.from_domain(
        session_id=session_id,
        session=session,
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
def get_session(
    session_id: UUID,
) -> SessionResponse:
    session = _find_session(session_id)

    return SessionResponse.from_domain(
        session_id=session_id,
        session=session,
    )


@router.get(
    "/{session_id}/evidence",
    response_model=tuple[PublicEvidenceResponse, ...],
    status_code=status.HTTP_200_OK,
)
def get_discovered_evidence(
    session_id: UUID,
) -> tuple[PublicEvidenceResponse, ...]:
    session = _find_session(session_id)
    case = find_case(session.case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Case {session.case_id!r} "
                "was not found."
            ),
        )

    discovered_ids = set(
        session.discovered_evidence_ids
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
def question_suspect(
    session_id: UUID,
    request: AskQuestionRequest,
) -> SessionResponse:
    session = _find_session(session_id)
    case = find_case(session.case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Case {session.case_id!r} "
                "was not found."
            ),
        )

    try:
        updated_session = ask_question(
            case=case,
            session=session,
            suspect_id=request.suspect_id,
            topic=request.to_domain_topic(),
        )
    except InvestigationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    _SESSIONS[session_id] = updated_session

    return SessionResponse.from_domain(
        session_id=session_id,
        session=updated_session,
    )


@router.post(
    "/{session_id}/theory",
    response_model=TheorySubmissionResponse,
    status_code=status.HTTP_200_OK,
)
def submit_theory(
    session_id: UUID,
    request: SubmitTheoryRequest,
) -> TheorySubmissionResponse:
    session = _find_session(session_id)
    case = find_case(session.case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Case {session.case_id!r} "
                "was not found."
            ),
        )

    try:
        updated_session, score = submit_final_theory(
            case=case,
            session=session,
            theory=request.to_domain(),
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

    _SESSIONS[session_id] = updated_session

    return TheorySubmissionResponse(
        session=SessionResponse.from_domain(
            session_id=session_id,
            session=updated_session,
        ),
        score=TheoryScoreResponse.from_domain(score),
    )