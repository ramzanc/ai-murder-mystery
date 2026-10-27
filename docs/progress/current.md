# Daily Detective — Current Progress

## Current checkpoint

Day 14 complete: investigation changes can be represented as immutable,
append-only PostgreSQL events with monotonic sequence numbers, idempotent
retries, optimistic concurrency checks, and deterministic replay into an
investigation-session snapshot.

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
- Added immutable theory and final-submission value objects.
- Added immutable canonical solution and reusable accusation-option models.
- Validated that the canonical killer and key evidence reference case data.
- Preserved the Day 2 unique suspect/evidence ID invariants.
- Added deterministic scoring for killer, motive, method, and 2–3 evidence
  items.
- Added a one-way finalization transition that permits exactly one officially
  scored accusation.
- Kept the score and submitted theory together in the final submission state.
- Added an application-level reveal lock until an accusation is finalized.
- Built the reveal only from the immutable canonical case definition.
- Extended the terminal game with theory selection, confirmation, scoring, and
  reveal rendering.
- Moved motive and method choices into validated case data so the terminal is
  not coupled to one mystery.
- Strengthened the sample evidence so the deterministic case is solvable from
  player-visible clues.
- Added unit and integration coverage for correct/wrong theories, copy-on-write
  finalization, scoring lockout, reveal lockout, and the full CLI flow.
- Added immutable epistemic-state models for suspect knowledge.
- Separated canonical timeline truth from subjective observations and beliefs.
- Added confidence values constrained between 0.0 and 1.0.
- Required every observation to reference a canonical source event.
- Required an observing suspect to be present in the source event.
- Prevented suspects from knowing private events without a causal source.
- Prevented beliefs from using another suspect's private observations.
- Allowed contradictory and incorrect beliefs without modifying canonical truth.
- Integrated knowledge consistency validation into case loading.
- Added Day 7 unit coverage for causal sources, private knowledge boundaries,
  divergent perception, incorrect beliefs, and cross-suspect leakage.
- Added canonical source-event provenance to evidence.
- Added discriminated unlock-rule models for:
  - evidence available at investigation start
  - questioning a specific suspect about a supported intent
  - discovering prerequisite evidence
- Reused deterministic question topics as validated unlock intents.
- Added evidence-rule reference validation for suspects and evidence.
- Added a fixed-point reachability algorithm for clue graphs.
- Rejected circular or otherwise unreachable critical-evidence paths.
- Added multiple legal discovery paths to the sample case.
- Integrated evidence consistency validation into case loading.
- Added Day 8 unit coverage for discriminated unions, provenance, invalid
  references, circular dependencies, evidence chains, and multiple unlock
  paths.
- Added immutable structured validation findings containing:
  - severity
  - stable machine-readable code
  - case-data path
  - human-readable message
- Added HARD_ERROR and WARNING severity levels.
- Added immutable validation reports with separated hard errors and warnings.
- Made hard errors block case approval while warnings remain non-blocking.
- Added a composable validator runner that collects all findings.
- Added an ordered validator registry for reusable rule composition.
- Adapted timeline, knowledge, and evidence consistency checks into structured
  case validators.
- Added a warning for unreachable non-critical evidence.
- Added Day 9 unit coverage for clean, warning-only, and blocked validation
  reports.
- Separated structural manifest loading from semantic case validation.
- Kept application case loading strict while allowing the linter to inspect
  structurally valid but semantically inconsistent cases.
- Added `scripts/validate_case.py` as the case-linter entrypoint.
- Added human-readable reports grouped into hard errors and warnings.
- Added machine-readable JSON reports for automated and AI-assisted repair
  loops.
- Added process exit-code behavior where approved cases exit 0 and blocked or
  unloadable cases exit 1.
- Converted case-loading failures into structured `case.load_failed` findings.
- Added valid and broken-timeline case fixtures.
- Added Day 10 integration coverage for approved cases, blocked cases, JSON
  output, clean standard error, and missing files.
- Added separate FastAPI routers for cases and investigation sessions.
- Added explicit request and response DTOs for the public HTTP boundary.
- Added domain-to-API mapping for cases, evidence, sessions, question events,
  theories, and scores.
- Prevented canonical truth from leaking through public case responses,
  including:
  - canonical timeline and solution
  - suspect knowledge
  - evidence provenance and unlock rules
- Added `GET /cases/{case_id}` for player-visible case browsing.
- Added `POST /sessions` with UUID identifiers and in-memory runtime storage.
- Added `GET /sessions/{session_id}` for retrieving the current immutable
  session snapshot.
- Added `GET /sessions/{session_id}/evidence` for retrieving discovered
  player-visible evidence.
- Added `POST /sessions/{session_id}/questions` for deterministic suspect
  questioning and copy-on-write session updates.
- Added `POST /sessions/{session_id}/theory` for one-time final theory
  submission and deterministic scoring.
- Added HTTP error behavior for:
  - missing cases and sessions with 404 responses
  - invalid investigation operations with 400 responses
  - repeated final submissions with 409 responses
  - invalid request DTOs with 422 responses
- Added Day 11 API coverage for public case fields, hidden-truth protection,
  session creation and retrieval, evidence responses, questioning, request
  validation, final scoring, and finalization conflicts.
- Added environment-based database configuration using Pydantic Settings.
- Added an async SQLAlchemy engine and reusable `async_sessionmaker`.
- Added request-scoped `AsyncSession` dependencies with rollback on errors.
- Added a PostgreSQL `investigation_sessions` table containing:
  - UUID primary keys
  - indexed case IDs
  - JSONB domain snapshots
  - creation and update timestamps
- Added explicit mapping between mutable SQLAlchemy persistence rows and
  immutable `InvestigationSession` domain snapshots.
- Replaced the in-memory API session dictionary with PostgreSQL persistence.
- Made all session API handlers asynchronous.
- Added explicit transaction boundaries for session creation, questioning, and
  final-theory submission.
- Added row-level `SELECT ... FOR UPDATE` locking for session state transitions
  to prevent concurrent updates from overwriting one another.
- Added application-lifespan disposal of the async database engine.
- Added `GET /health/database` to verify PostgreSQL connectivity separately
  from the process-level `GET /health` check.
- Added an async Alembic environment connected to application configuration.
- Added the initial Alembic migration for the `investigation_sessions` table
  and its case-ID index.
- Updated API tests to use explicit FastAPI startup and shutdown lifecycles.
- Added Day 12 integration coverage for database health and persistence across
  application restarts.
- Added application-layer `Protocol` ports for:
  - case lookup
  - investigation-session repositories
  - units of work
- Added an immutable `SessionRecord` that pairs a session UUID with its domain
  snapshot without exposing persistence rows to application code.
- Added `InvestigationUseCases` to coordinate session creation, retrieval,
  evidence retrieval, questioning, and final-theory submission.
- Moved SQLAlchemy queries and row locking out of FastAPI routes and into a
  concrete `SqlAlchemySessionRepository` adapter.
- Added `SqlAlchemyUnitOfWork` so every application use case owns one explicit
  commit-or-rollback transaction boundary.
- Added FastAPI dependency wiring that injects the SQLAlchemy unit of work into
  application use cases at the API composition boundary.
- Kept HTTP status translation in the API layer through application-level case
  and session-not-found errors.
- Added an in-memory fake session repository and rollback-capable fake unit of
  work for database-free application tests.
- Added reusable repository contract tests and verified that both the fake and
  PostgreSQL repositories satisfy the same behavior.
- Added Day 13 unit coverage for successful commits, failed-operation
  rollbacks, session updates, finalization, and one transaction boundary per
  use case.
- Added integration coverage for the SQL repository with explicit engine
  disposal to keep async event-loop ownership isolated between tests.
- Added immutable session-domain events for:
  - session creation
  - suspect questions
  - final-theory submission
- Added stored event envelopes containing:
  - session UUID
  - monotonic stream sequence
  - idempotency key
  - discriminated event payload
- Added deterministic replay from an ordered event stream into an immutable
  `InvestigationSession`.
- Added replay validation for empty streams, sequence gaps, mixed session IDs,
  invalid event order, question sequence gaps, post-finalization questions,
  and repeated finalization.
- Added an application-layer event-store port independent of SQLAlchemy.
- Added a PostgreSQL append-only event repository with no update or delete
  operations.
- Added a composite event-stream primary key on session ID and sequence.
- Added per-session idempotency-key uniqueness and made duplicate keys return
  the originally stored event.
- Added expected-version checks for optimistic concurrency.
- Added an Alembic migration for the `session_events` table.
- Added Day 14 unit coverage for deterministic replay and invalid streams.
- Added Day 14 PostgreSQL integration coverage for monotonic sequences,
  idempotent retries, optimistic concurrency, ordered loading, and snapshot
  reconstruction.

## Verification

Run from `backend/`:

```bash
uv run pytest
uv run alembic upgrade head
uv run alembic current
uv run python -m scripts.play_case
uv run python -m scripts.validate_case cases/sample_case.json
uv run python -m scripts.validate_case \
  tests/fixtures/cases/broken_timeline.json
uv run python -m scripts.validate_case \
  tests/fixtures/cases/broken_timeline.json \
  --format json
uv run pytest tests/api -v
uv run pytest tests/unit/test_session_use_cases.py -v
uv run pytest tests/unit/test_session_repository.py -v
uv run pytest tests/integration/test_session_repository.py -v
uv run pytest tests/unit/test_replay.py -v
uv run pytest tests/integration/test_event_store.py -v
uv run alembic check
uv run uvicorn app.main:app --reload
```

Expected:

- All tests pass.
- The sample case loads successfully.
- The player can browse the dossier.
- The player can inspect all four suspects.
- The player can inspect discovered evidence.
- The player can ask suspects about alibis and secrets.
- Each question is appended to investigation history.
- Invalid suspect IDs and topics are rejected.
- The player can submit exactly one official accusation containing a killer,
  motive, method, and 2–3 discovered evidence items.
- Correct and wrong submissions receive deterministic scores.
- A wrong accusation still locks further official scoring.
- The canonical reveal remains unavailable until final submission.
- Canonical case data remains unchanged.
- Every evidence item has a canonical timeline source.
- Unlock rules reference valid suspects, evidence, and supported intents.
- Every murder-critical clue has at least one reachable discovery path.
- Circular evidence dependencies cannot make critical clues unreachable.
- The sample case produces a clean, approved validation report.
- Warning-only findings do not block case approval.
- Hard-error findings block case approval.
- Every validation finding contains a severity, code, path, and message.
- The validation runner continues collecting findings after a hard error.
- The valid sample case receives an approved human-readable lint report and
  exits 0.
- The broken-timeline fixture receives a blocked report containing
  `timeline.inconsistent` and exits 1.
- Human-readable lint output groups hard errors and warnings separately.
- JSON lint output is valid machine-readable JSON with summary counts and
  structured findings.
- Missing case files produce a structured `case.load_failed` finding and exit
  1.
- `GET /cases/case_ashcroft_study` returns only player-visible case data.
- Public case responses never include the canonical timeline, solution,
  suspect knowledge, evidence provenance, or evidence unlock rules.
- `POST /sessions` persists a new PostgreSQL-backed investigation session and
  returns 201 with a UUID session identifier.
- `GET /sessions/{session_id}` returns the latest immutable session snapshot.
- `GET /sessions/{session_id}/evidence` returns only public evidence fields.
- `POST /sessions/{session_id}/questions` appends a deterministic question
  event and stores the resulting copy-on-write session snapshot.
- `POST /sessions/{session_id}/theory` scores and finalizes the official
  theory exactly once.
- Repeating a final theory submission returns 409 Conflict.
- Unknown cases and sessions return 404, while invalid request DTOs return
  422.
- `GET /health/database` confirms that PostgreSQL is reachable.
- A session created before application shutdown remains available after the
  application and connection pool restart.
- Session updates execute within transactions and lock the target row until
  the transaction completes.
- FastAPI session routes contain no SQLAlchemy queries or persistence-row
  mapping logic.
- Application session workflows run against the in-memory fake without a
  database connection.
- Each use case enters exactly one unit-of-work transaction boundary.
- Successful fake-unit-of-work operations commit, while failed operations
  restore the previous repository state and record a rollback.
- The fake and SQLAlchemy repositories pass the same repository contract.
- SQL-backed state transitions continue to acquire row-level locks through the
  repository abstraction.
- Session event streams receive contiguous, monotonically increasing sequence
  numbers.
- Retrying an append with the same idempotency key returns its original event.
- Appending against a stale expected stream version raises an optimistic
  concurrency error.
- Replaying stored session-start, question, and theory events reconstructs the
  same immutable session snapshot, including evidence and final submission.
- Invalid event streams are rejected rather than silently reordered or
  repaired.
- `uv run alembic upgrade head` creates the schema from an empty database.
- `uv run alembic current` reports `b7a9c4e21d14 (head)`.
- `uv run alembic check` reports no new upgrade operations.
- Swagger UI exposes the complete persisted API flow at `/docs` while the
  server is running.

## Current playable result

Run `uv run python -m scripts.play_case` from `backend/` for the complete
terminal investigation, or run `uv run uvicorn app.main:app --reload` and open
`http://127.0.0.1:8000/docs` for the HTTP version. The API supports public case
browsing, PostgreSQL-backed session creation, evidence retrieval, suspect
questioning, and final theory scoring without exposing canonical case truth.
Investigation progress now survives backend process restarts, while the same
application workflows can run against an in-memory fake for fast unit tests.
The Day 14 event store can append and reload an investigation history and
deterministically rebuild the equivalent session snapshot.

## Current limitation

Persisted sessions do not yet have expiration, archival, or deletion rules.
Application memory remains bounded because requests load only the requested
row, but PostgreSQL storage will grow until a later retention policy and cleanup
job are introduced. The append-only event store is implemented and verified,
but the existing HTTP session mutations still write only the Day 13 JSONB
snapshot. A later integration must append the event and update the snapshot in
the same unit-of-work transaction before the event log becomes authoritative
for live API requests.

## Next checkpoint

Day 15: add a deliberately simple browser UI for the dossier, suspects,
evidence, theory submission, and reveal while keeping Python authoritative for
game state.
