import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.domain.case import CaseManifest
from app.validation.case_rules import validate_case

class CaseLoadError(RuntimeError):
    """Base exception for failures while loading a case."""


class CaseFileNotFoundError(CaseLoadError):
    """Raised when the requested case file does not exist."""


class CaseReadError(CaseLoadError):
    """Raised when an existing case file cannot be read."""


class CaseJsonError(CaseLoadError):
    """Raised when a case file does not contain valid JSON."""


class CaseSchemaError(CaseLoadError):
    """Raised when a case definition is structurally or semantically invalid."""


def load_case_manifest(path: str | Path) -> CaseManifest:
    """
    Load a structurally valid case manifest.

    This function handles filesystem, JSON, and Pydantic schema validation.
    It intentionally does not run the semantic case-validator suite.
    """

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
        return CaseManifest.model_validate(payload)
    except ValidationError as exc:
        raise CaseSchemaError(
            _format_schema_error(case_path, exc)
        ) from exc


def load_case(path: str | Path) -> CaseManifest:
    """
    Load a case that is safe for the application to use.

    Unlike load_case_manifest(), this function also rejects semantic
    consistency errors discovered by the complete validator suite.
    """

    case_path = Path(path).expanduser()
    case = load_case_manifest(case_path)
    report = validate_case(case)

    if report.hard_errors:
        details = "\n".join(
            (
                f"  - [{finding.code}] "
                f"{finding.path}: {finding.message}"
            )
            for finding in report.hard_errors
        )

        raise CaseSchemaError(
            f"Case file '{case_path}' failed consistency validation:\n"
            f"{details}"
        )

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