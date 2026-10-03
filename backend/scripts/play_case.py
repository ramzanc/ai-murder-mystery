from pathlib import Path

from app.application.case_loader import (
    CaseLoadError,
    load_case,
)
from app.presentation.terminal import run_case_browser


def main() -> None:
    backend_root = Path(__file__).resolve().parents[1]

    case_path = (
        backend_root
        / "cases"
        / "sample_case.json"
    )

    try:
        case = load_case(case_path)
    except CaseLoadError as exc:
        print(f"Unable to load case: {exc}")
        raise SystemExit(1) from exc

    run_case_browser(case)


if __name__ == "__main__":
    main()
