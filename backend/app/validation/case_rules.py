from app.domain.case import CaseManifest
from app.validation.base import (
    CaseValidator,
    Severity,
    ValidationFinding,
    ValidationReport,
)
from app.validation.evidence import (
    EvidenceConsistencyError,
    reachable_evidence_ids,
    validate_evidence,
)
from app.validation.knowledge import (
    KnowledgeConsistencyError,
    validate_knowledge,
)
from app.validation.runner import run_validators
from app.validation.timeline import (
    TimelineConsistencyError,
    validate_timeline,
)

def validate_case_timeline(
    case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    """Convert timeline consistency failures into findings."""

    valid_actor_ids = {
        case.victim.id,
        *(suspect.id for suspect in case.suspects),
    }

    required_murder_actor_ids = {
        case.victim.id,
        case.solution.killer_id,
    }

    try:
        validate_timeline(
            case.timeline,
            valid_actor_ids=valid_actor_ids,
            required_murder_actor_ids=required_murder_actor_ids,
        )
    except TimelineConsistencyError as exc:
        return (
            ValidationFinding(
                severity=Severity.HARD_ERROR,
                code="timeline.inconsistent",
                path="timeline",
                message=str(exc),
            ),
        )

    return ()


def validate_case_knowledge(
    case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    """Convert suspect-knowledge failures into findings."""

    try:
        validate_knowledge(
            suspects=case.suspects,
            timeline=case.timeline,
        )
    except KnowledgeConsistencyError as exc:
        return (
            ValidationFinding(
                severity=Severity.HARD_ERROR,
                code="knowledge.inconsistent",
                path="suspects[*].knowledge",
                message=str(exc),
            ),
        )

    return ()


def validate_case_evidence(
    case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    """Convert evidence consistency failures into findings."""

    try:
        validate_evidence(
            evidence_items=case.initial_evidence,
            suspects=case.suspects,
            timeline=case.timeline,
            critical_evidence_ids=case.solution.key_evidence_ids,
        )
    except EvidenceConsistencyError as exc:
        return (
            ValidationFinding(
                severity=Severity.HARD_ERROR,
                code="evidence.inconsistent",
                path="initial_evidence",
                message=str(exc),
            ),
        )

    return ()


def warn_about_unreachable_optional_evidence(
    case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    """
    Warn when non-critical evidence has no discovery path.

    Critical unreachable evidence is already a hard error in
    validate_case_evidence.
    """

    reachable_ids = reachable_evidence_ids(
        case.initial_evidence,
    )
    critical_ids = set(case.solution.key_evidence_ids)

    findings: list[ValidationFinding] = []

    for index, evidence in enumerate(case.initial_evidence):
        if evidence.id in critical_ids:
            continue

        if evidence.id in reachable_ids:
            continue

        findings.append(
            ValidationFinding(
                severity=Severity.WARNING,
                code="evidence.optional_unreachable",
                path=(
                    f"initial_evidence[{index}].unlock_rules"
                ),
                message=(
                    f"Optional evidence '{evidence.id}' cannot be "
                    "discovered through any reachable unlock rule."
                ),
            )
        )

    return tuple(findings)


CASE_VALIDATORS: tuple[CaseValidator, ...] = (
    validate_case_timeline,
    validate_case_knowledge,
    validate_case_evidence,
    warn_about_unreachable_optional_evidence,
)


def validate_case(
    case: CaseManifest,
) -> ValidationReport:
    """Run the complete case-validation pipeline."""

    return run_validators(
        case=case,
        validators=CASE_VALIDATORS,
    )