# Daily Detective — Current Progress

## Current checkpoint

Day 3 complete: case JSON loading and playable terminal dossier browser.

## Implemented

- Created the backend Python project using uv.
- Established Python 3.13+ as the project baseline.
- Created the FastAPI application.
- Added `GET /health`.
- Added a pytest specification for the health endpoint.
- Added project documentation and Git ignore rules.
- Added immutable Pydantic v2 domain models for:
  - case manifest
  - public dossier
  - victim
  - suspects
  - initial evidence
- Added constrained namespaced IDs for cases, victims, suspects, and evidence.
- Added difficulty and evidence-kind enums.
- Enforced exactly four suspects per case.
- Rejected unknown fields.
- Enforced unique suspect and evidence IDs.
- Made canonical case definitions immutable.
- Added Day 2 unit tests for domain invariants.
- Added an application-layer case loader using pathlib.
- Added explicit case-loading errors for:
  - missing files
  - unreadable files
  - malformed JSON
  - invalid case schemas
- Added JSON deserialization into the Day 2 CaseManifest model.
- Added the first real case JSON at `cases/sample_case.json`.
- Added terminal presentation functions for:
  - case dossier
  - victim
  - suspects
  - starting evidence
- Added an interactive terminal case browser.
- Added `scripts/play_case.py` as the Day 3 playable entrypoint.
- Added unit tests for valid loading and failure cases.

## Verification

Run from `backend/`:

```bash
uv run pytest
uv run python -m scripts.play_case
Expected:
- All tests pass.
- The sample case loads successfully.
- The player can browse the dossier.
- The player can inspect all four suspects.
- The player can inspect starting evidence.
Current playable result
Run:
uv run python -m scripts.play_case
The terminal presents the first Daily Detective case and lets the player browse its public dossier, suspects, and starting evidence.