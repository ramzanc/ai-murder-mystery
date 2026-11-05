from typing import Never
from uuid import UUID

from fastapi import (
    APIRouter,
    HTTPException,
    status,
)

from app.api.dependencies import (
    InterrogationServiceDependency,
)
from app.api.schemas import (
    InterrogationLatencyResponse,
    InterrogationRequest,
    InterrogationResponse,
    InterrogationTraceResponse,
)
from app.application.interrogation_service import (
    InterrogationResult,
)
from app.application.investigation_service import (
    CaseNotFoundError,
    SessionNotFoundError,
)
from app.application.suspect_context import (
    SuspectContextError,
)
from app.application.suspect_planner import (
    SuspectPlanningError,
)

router = APIRouter(
    prefix="/sessions",
    tags=["interrogation"],
)

def _raise_not_found(
    error: CaseNotFoundError | SessionNotFoundError,
) -> Never:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error

def _to_response(
    result: InterrogationResult,
) -> InterrogationResponse:
    return InterrogationResponse(
        session_id=result.session_id,
        suspect_id=result.suspect_id,
        question=result.question,
        dialogue=result.dialogue,
        trace=InterrogationTraceResponse(
            intent=result.trace.intent,
            strategy_id=result.trace.strategy_id,
            tactic=result.trace.tactic,
            selected_fact_ids=(
                result.trace.selected_fact_ids
            ),
        provider=result.trace.provider,
            model=result.trace.model,
            intent_prompt_version=(
                result.trace.intent_prompt_version
            ),
            strategy_prompt_version=(
                result.trace.strategy_prompt_version
            ),
            dialogue_prompt_version=(
                result.trace.dialogue_prompt_version
            ),
            intent_used_fallback=(
                result.trace.intent_used_fallback
            ),
            strategy_used_fallback=(
                result.trace.strategy_used_fallback
            ),
            dialogue_used_fallback=(
                result.trace.dialogue_used_fallback
            ),
            latency=InterrogationLatencyResponse(
                intent_ms=(
                    result.trace.latency.intent_ms
                ),
                planning_ms=(
                    result.trace.latency.planning_ms
                ),
                dialogue_ms=(
                    result.trace.latency.dialogue_ms
                ),
                total_ms=(
                    result.trace.latency.total_ms
                ),
            ),
        ),
    )

@router.post(
    "/{session_id}/interrogations",
    response_model=InterrogationResponse,
    status_code=status.HTTP_200_OK,
)
async def interrogate_suspect(
    session_id: UUID,
    request: InterrogationRequest,
    service: InterrogationServiceDependency,
) -> InterrogationResponse:
    try:
        result = await service.interrogate(
            session_id=session_id,
            suspect_id=request.suspect_id,
            question=request.question,
            presented_evidence_ids=(
                request.presented_evidence_ids
            ),
        )
    except (
        CaseNotFoundError,
        SessionNotFoundError,
    ) as exc:
        _raise_not_found(exc)
    except SuspectContextError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SuspectPlanningError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "The AI selected an invalid response plan."
            ),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _to_response(result)

