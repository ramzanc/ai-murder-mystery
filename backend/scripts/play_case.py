from pathlib import Path

from app.application.case_loader import CaseLoadError, load_case
from app.presentation.terminal import run_case_browser


def sample_case_path() -> Path:
    """Return the bundled sample-case path."""

    backend_root = Path(__file__).resolve().parents[1]

    return backend_root / "cases" / "sample_case.json"


def main() -> None:
    """Load and browse the sample Daily Detective case."""

    case_path = sample_case_path()

    try:
        case = load_case(case_path)
    except CaseLoadError as exc:
        print()
        print("Could not start Daily Detective.")
        print(exc)
        raise SystemExit(1) from exc

    run_case_browser(case)


if __name__ == "__main__":
    main()