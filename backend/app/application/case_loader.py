import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.domain.case import CaseManifest

from app.validation.timeline import (
    TimelineConsistencyError,
    validate_timeline,
)

class CaseLoadError(RuntimeError):
    """Base exception for failures while loading a case."""


class CaseFileNotFoundError(CaseLoadError):
    """Raised when the requested case file does not exist."""


class CaseReadError(CaseLoadError):
    """Raised when an existing case file cannot be read."""


class CaseJsonError(CaseLoadError):
    """Raised when a case file does not contain valid JSON."""


class CaseSchemaError(CaseLoadError):
    """Raised when JSON does not satisfy the CaseManifest schema."""


def load_case(path: str | Path) -> CaseManifest:
    """Load and validate a case definition from a JSON file."""

    case_path = Path(path).expanduser()

    if not case_path.exists():
        raise CaseFileNotFoundError(
            f"Case file does not exist: {case_path}"
        )

    if not case_path.is_file():
        raise CaseReadError(
            f"Case path is not a file: {case_path}"
        )

    try:
        raw_text = case_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CaseReadError(
            f"Could not read case file '{case_path}': {exc}"
        ) from exc

    try:
        payload: Any = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CaseJsonError(
            f"Invalid JSON in '{case_path}' "
            f"at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    try:
        case = CaseManifest.model_validate(payload)
    except ValidationError as exc:
        raise CaseSchemaError(
            _format_schema_error(case_path, exc)
        ) from exc

    valid_actor_ids = {
        case.victim.id,
        *(
            suspect.id
            for suspect in case.suspects
        ),
    }

    required_murder_actor_ids = {
        case.victim.id,
        case.solution.killer_id,
    }

    try:
        validate_timeline(
            case.timeline,
            valid_actor_ids=valid_actor_ids,
            required_murder_actor_ids=(
                required_murder_actor_ids
            ),
        )
    except TimelineConsistencyError as exc:
        raise CaseSchemaError(
            f"Case file '{case_path}' has an "
            f"inconsistent timeline:\n"
            f"  - {exc}"
        ) from exc

    return case

def _format_schema_error(
    case_path: Path,
    error: ValidationError,
) -> str:
    """Convert Pydantic validation failures into a readable message."""

    details: list[str] = []

    for issue in error.errors():
        location = ".".join(str(part) for part in issue["loc"])
        message = issue["msg"]

        if not location:
            location = "<root>"

        details.append(f"  - {location}: {message}")

    formatted_details = "\n".join(details)

    return (
        f"Case file '{case_path}' does not match the case schema:\n"
        f"{formatted_details}"
    )