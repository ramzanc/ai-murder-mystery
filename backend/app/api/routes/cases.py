from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import PublicCaseResponse
from app.application.case_loader import load_case
from app.domain.case import CaseManifest


router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)

BACKEND_ROOT = Path(__file__).resolve().parents[3]

SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)

_SAMPLE_CASE = load_case(SAMPLE_CASE_PATH)

_CASES_BY_ID: dict[str, CaseManifest] = {
    str(_SAMPLE_CASE.id): _SAMPLE_CASE,
}

def find_case(
    case_id: str,
) -> CaseManifest | None:
    return _CASES_BY_ID.get(case_id)


@router.get(
    "/{case_id}",
    response_model=PublicCaseResponse,
    status_code=status.HTTP_200_OK,
)
def get_case(
    case_id: str,
) -> PublicCaseResponse:
    case = find_case(case_id)

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id!r} was not found.",
        )

    return PublicCaseResponse.from_domain(case)