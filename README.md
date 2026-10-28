# Daily Detective

Daily Detective is a multiplayer AI detective game built as a hands-on Python and AI engineering project.

The backend will remain authoritative for canonical case truth, game rules, permissions, evidence causality, scoring, and state transitions. AI components will later operate within explicit knowledge and strategy boundaries rather than inventing game canon.

## Current status

Day 15 complete: the deterministic mystery is browser-playable from dossier
review through persisted suspect interviews, one authoritative official score,
and the post-finalization canonical reveal.

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

## Play in the browser

Start PostgreSQL and run the migrations, then use two terminals:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The Next.js app proxies API requests to
`http://127.0.0.1:8000` by default; set `BACKEND_URL` to use another backend.
