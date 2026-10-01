# Daily Detective — Current Progress

## Current checkpoint

Day 4 complete: investigation session state and deterministic suspect questioning.

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
- Added `scripts/play_case.py` as the playable entrypoint.
- Added unit tests for valid loading and failure cases.
- Added immutable investigation-session snapshots on top of the immutable case definition.
- Added predefined deterministic interrogation topics:
  - alibi
  - secret
- Added ordered question events with monotonic sequence numbers.
- Added copy-on-write session transitions.
- Added session-owned discovered evidence IDs.
- Added validation for:
  - invalid suspect IDs
  - invalid question topics
  - session/case mismatches
- Extended the terminal game to question suspects.
- Added investigation-history rendering.
- Added Day 4 unit tests for investigation state transitions and invariants.

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
- The player can inspect discovered evidence.
- The player can ask suspects about alibis and secrets.
- Each question is appended to investigation history.
- Invalid suspect IDs and topics are rejected.
- Canonical case data remains unchanged.
Current playable result
Run:
uv run python -m scripts.play_case
The terminal now supports a stateful deterministic investigation. The player can browse the case, question different suspects about predefined topics, and inspect the ordered history of the current investigation.