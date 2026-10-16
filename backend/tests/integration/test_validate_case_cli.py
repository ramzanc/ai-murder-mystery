import json
import subprocess
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]

FIXTURE_ROOT = (
    BACKEND_ROOT
    / "tests"
    / "fixtures"
    / "cases"
)

VALID_CASE_PATH = (
    FIXTURE_ROOT
    / "valid_case.json"
)

BROKEN_TIMELINE_PATH = (
    FIXTURE_ROOT
    / "broken_timeline.json"
)


def run_linter(
    case_path: Path,
    *extra_args: str,
) -> subprocess.CompletedProcess[str]:
    """Run the linter as a real command-line process."""

    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.validate_case",
            str(case_path),
            *extra_args,
        ],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_case_exits_zero() -> None:
    result = run_linter(VALID_CASE_PATH)

    assert result.returncode == 0
    assert "HARD ERRORS (0)" in result.stdout
    assert "WARNINGS (0)" in result.stdout
    assert "STATUS: APPROVED" in result.stdout
    assert result.stderr == ""


def test_hard_error_case_exits_nonzero() -> None:
    result = run_linter(BROKEN_TIMELINE_PATH)

    assert result.returncode == 1
    assert "HARD ERRORS (1)" in result.stdout
    assert "[timeline.inconsistent] timeline" in result.stdout
    assert "WARNINGS (0)" in result.stdout
    assert "STATUS: BLOCKED" in result.stdout
    assert result.stderr == ""


def test_json_report_is_machine_readable() -> None:
    result = run_linter(
        BROKEN_TIMELINE_PATH,
        "--format",
        "json",
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["approved"] is False
    assert payload["summary"] == {
        "hard_errors": 1,
        "warnings": 0,
    }
    assert payload["findings"][0]["severity"] == "hard_error"
    assert payload["findings"][0]["code"] == (
        "timeline.inconsistent"
    )
    assert payload["findings"][0]["path"] == "timeline"
    assert payload["findings"][0]["message"]
    assert result.stderr == ""


def test_missing_case_returns_structured_load_error(
    tmp_path: Path,
) -> None:
    missing_path = tmp_path / "missing_case.json"

    result = run_linter(
        missing_path,
        "--format",
        "json",
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["approved"] is False
    assert payload["findings"][0]["code"] == (
        "case.load_failed"
    )
    assert payload["findings"][0]["path"] == "$"