import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.application.case_loader import (
    CaseLoadError,
    load_case_manifest,
)
from app.validation.base import (
    Severity,
    ValidationFinding,
    ValidationReport,
)
from app.validation.case_rules import validate_case

def parse_args(
    argv: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse command-line arguments for the case linter."""

    parser = argparse.ArgumentParser(
        description=(
            "Validate a Daily Detective case definition."
        ),
    )

    parser.add_argument(
        "case_path",
        type=Path,
        help="Path to the case JSON file.",
    )

    parser.add_argument(
        "--format",
        choices=("human", "json"),
        default="human",
        dest="output_format",
        help=(
            "Output format. Use 'json' for automated repair loops. "
            "Defaults to 'human'."
        ),
    )

    return parser.parse_args(argv)

def lint_case(case_path: Path) -> ValidationReport:
    """Load a case manifest and run the complete validator suite."""

    try:
        case = load_case_manifest(case_path)
    except CaseLoadError as exc:
        return ValidationReport(
            findings=(
                ValidationFinding(
                    severity=Severity.HARD_ERROR,
                    code="case.load_failed",
                    path="$",
                    message=str(exc),
                ),
            ),
        )

    return validate_case(case)


def render_human_report(
    *,
    case_path: Path,
    report: ValidationReport,
) -> str:
    """Render a validation report for a person reading a terminal."""

    lines = [
        f"CASE LINT: {case_path}",
        "",
        f"HARD ERRORS ({len(report.hard_errors)})",
    ]

    lines.extend(
        _render_human_findings(report.hard_errors)
    )

    lines.extend(
        [
            "",
            f"WARNINGS ({len(report.warnings)})",
        ]
    )

    lines.extend(
        _render_human_findings(report.warnings)
    )

    status = (
        "APPROVED"
        if report.is_approved
        else "BLOCKED"
    )

    lines.extend(
        [
            "",
            f"STATUS: {status}",
        ]
    )

    return "\n".join(lines)


def _render_human_findings(
    findings: tuple[ValidationFinding, ...],
) -> list[str]:
    """Render one human-readable report section."""

    if not findings:
        return ["  None"]

    lines: list[str] = []

    for finding in findings:
        lines.append(
            f"  - [{finding.code}] {finding.path}"
        )
        lines.append(
            f"    {finding.message}"
        )

    return lines


def render_json_report(
    *,
    case_path: Path,
    report: ValidationReport,
) -> str:
    """Render a stable machine-readable validation report."""

    payload: dict[str, Any] = {
        "case_path": str(case_path),
        "approved": report.is_approved,
        "summary": {
            "hard_errors": len(report.hard_errors),
            "warnings": len(report.warnings),
        },
        "findings": [
            {
                "severity": finding.severity.value,
                "code": finding.code,
                "path": finding.path,
                "message": finding.message,
            }
            for finding in report.findings
        ],
    }

    return json.dumps(
        payload,
        indent=2,
    )


def main(
    argv: Sequence[str] | None = None,
) -> int:
    """Run the case linter and return its process exit code."""

    args = parse_args(argv)
    report = lint_case(args.case_path)

    if args.output_format == "json":
        output = render_json_report(
            case_path=args.case_path,
            report=report,
        )
    else:
        output = render_human_report(
            case_path=args.case_path,
            report=report,
        )

    print(output)

    return 0 if report.is_approved else 1

if __name__ == "__main__":
    raise SystemExit(main())