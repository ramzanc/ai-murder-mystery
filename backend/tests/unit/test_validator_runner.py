from pathlib import Path

from app.application.case_loader import load_case
from app.domain.case import CaseManifest
from app.domain.timeline import TimelineEventKind
from app.validation.base import (
    Severity,
    ValidationFinding,
)
from app.validation.case_rules import validate_case
from app.validation.runner import (
    ValidatorRegistry,
    run_validators,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CASE_PATH = (
    BACKEND_ROOT
    / "cases"
    / "sample_case.json"
)


def sample_case() -> CaseManifest:
    return load_case(SAMPLE_CASE_PATH)


def warning_validator(
    _case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    return (
        ValidationFinding(
            severity=Severity.WARNING,
            code="case.example_warning",
            path="title",
            message="This is a non-blocking example warning.",
        ),
    )


def hard_error_validator(
    _case: CaseManifest,
) -> tuple[ValidationFinding, ...]:
    return (
        ValidationFinding(
            severity=Severity.HARD_ERROR,
            code="case.example_error",
            path="timeline",
            message="This is a blocking example error.",
        ),
    )


def test_clean_report_is_approved() -> None:
    report = run_validators(
        case=sample_case(),
        validators=(),
    )

    assert report.findings == ()
    assert report.hard_errors == ()
    assert report.warnings == ()
    assert report.is_approved is True


def test_warning_does_not_block_approval() -> None:
    report = run_validators(
        case=sample_case(),
        validators=(warning_validator,),
    )

    assert report.is_approved is True
    assert report.hard_errors == ()
    assert len(report.warnings) == 1

    finding = report.warnings[0]

    assert finding.severity == Severity.WARNING
    assert finding.code == "case.example_warning"
    assert finding.path == "title"
    assert finding.message == (
        "This is a non-blocking example warning."
    )


def test_hard_error_blocks_approval_without_hiding_warnings() -> None:
    report = run_validators(
        case=sample_case(),
        validators=(
            hard_error_validator,
            warning_validator,
        ),
    )

    assert report.is_approved is False
    assert len(report.hard_errors) == 1
    assert len(report.warnings) == 1
    assert len(report.findings) == 2


def test_registry_registers_and_runs_validators_in_order() -> None:
    registry = ValidatorRegistry()

    returned_validator = registry.register(
        warning_validator,
    )
    registry.register(hard_error_validator)

    report = registry.run(sample_case())

    assert returned_validator is warning_validator
    assert registry.validators == (
        warning_validator,
        hard_error_validator,
    )
    assert [
        finding.code
        for finding in report.findings
    ] == [
        "case.example_warning",
        "case.example_error",
    ]


def test_default_case_rules_accept_sample_case() -> None:
    report = validate_case(sample_case())

    assert report.is_approved is True
    assert report.findings == ()


def test_case_rules_distinguish_warning_from_hard_error() -> None:
    case = sample_case()

    optional_evidence = next(
        evidence
        for evidence in case.initial_evidence
        if evidence.id not in case.solution.key_evidence_ids
    )

    unreachable_optional_evidence = optional_evidence.model_copy(
        update={
            "unlock_rules": (),
        },
    )

    warning_case = case.model_copy(
        update={
            "initial_evidence": tuple(
                (
                    unreachable_optional_evidence
                    if evidence.id == optional_evidence.id
                    else evidence
                )
                for evidence in case.initial_evidence
            ),
        },
    )

    warning_report = validate_case(warning_case)

    assert warning_report.is_approved is True
    assert warning_report.hard_errors == ()
    assert len(warning_report.warnings) == 1
    assert (
        warning_report.warnings[0].code
        == "evidence.optional_unreachable"
    )
    assert warning_report.warnings[0].path.endswith(
        ".unlock_rules"
    )

    murder_event = next(
        event
        for event in case.timeline.events
        if event.kind == TimelineEventKind.MURDER
    )

    murder_without_killer = murder_event.model_copy(
        update={
            "actor_ids": (case.victim.id,),
        },
    )

    broken_timeline = case.timeline.model_copy(
        update={
            "events": tuple(
                (
                    murder_without_killer
                    if event.id == murder_event.id
                    else event
                )
                for event in case.timeline.events
            ),
        },
    )

    blocked_case = case.model_copy(
        update={
            "timeline": broken_timeline,
        },
    )

    blocked_report = validate_case(blocked_case)

    assert blocked_report.is_approved is False
    assert any(
        finding.code == "timeline.inconsistent"
        for finding in blocked_report.hard_errors
    )
    assert all(
        finding.code
        and finding.path
        and finding.message
        for finding in blocked_report.findings
    )