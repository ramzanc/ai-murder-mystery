# Daily Detective

Daily Detective is a multiplayer AI detective game built as a hands-on Python and AI engineering project.

The backend will remain authoritative for canonical case truth, game rules, permissions, evidence causality, scoring, and state transitions. AI components will later operate within explicit knowledge and strategy boundaries rather than inventing game canon.

## Current status

Day 5 complete: the first deterministic terminal mystery is playable from
dossier review through one official accusation and the canonical reveal.

Available endpoint:

```text
GET /health
```

## Run the backend checks

From `backend/`:

```bash
uv run pytest
```

## Play the case

From `backend/`:

```bash
uv run python -m scripts.play_case
```

The terminal game lets you inspect the dossier, question four suspects, review
the starting evidence, submit one killer/motive/method/evidence theory, receive
a deterministic score, and view the immutable canonical solution.
