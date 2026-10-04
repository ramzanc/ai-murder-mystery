from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from app.domain.case import CaseManifest


class Severity(str, Enum):
    """The publication impact of a validation finding."""

    HARD_ERROR = "hard_error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """One structured problem discovered while validating a case."""

    severity: Severity
    code: str
    path: str
    message: str

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("finding code must not be blank")

        if not self.path.strip():
            raise ValueError("finding path must not be blank")

        if not self.message.strip():
            raise ValueError("finding message must not be blank")


class CaseValidator(Protocol):
    """Callable contract implemented by every case validator."""

    def __call__(
        self,
        case: CaseManifest,
        /,
    ) -> Iterable[ValidationFinding]:
        ...


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Immutable aggregate returned after all validators run."""

    findings: tuple[ValidationFinding, ...]

    @property
    def hard_errors(self) -> tuple[ValidationFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.severity == Severity.HARD_ERROR
        )

    @property
    def warnings(self) -> tuple[ValidationFinding, ...]:
        return tuple(
            finding
            for finding in self.findings
            if finding.severity == Severity.WARNING
        )

    @property
    def is_approved(self) -> bool:
        return not self.hard_errors