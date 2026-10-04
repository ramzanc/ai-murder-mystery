from collections.abc import Iterable

from app.domain.case import CaseManifest
from app.validation.base import (
    CaseValidator,
    ValidationFinding,
    ValidationReport,
)

def run_validators(
    *,
    case: CaseManifest,
    validators: Iterable[CaseValidator],
) -> ValidationReport:
    """Run every validator and collect all findings in order."""

    findings: list[ValidationFinding] = []

    for validator in validators:
        findings.extend(validator(case))

    return ValidationReport(
        findings=tuple(findings),
    )


class ValidatorRegistry:
    """An ordered collection of reusable case validators."""

    def __init__(
        self,
        validators: Iterable[CaseValidator] = (),
    ) -> None:
        self._validators: list[CaseValidator] = list(validators)

    @property
    def validators(self) -> tuple[CaseValidator, ...]:
        return tuple(self._validators)

    def register(
        self,
        validator: CaseValidator,
    ) -> CaseValidator:
        """
        Register a validator.

        Returning the validator also allows register to be used as a
        decorator.
        """
        self._validators.append(validator)
        return validator

    def run(
        self,
        case: CaseManifest,
    ) -> ValidationReport:
        return run_validators(
            case=case,
            validators=self._validators,
        )
