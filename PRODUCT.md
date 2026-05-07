# PRODUCT

## What this is

A minimal Flask web service backed by PostgreSQL, packaged for deployment on Fly.io. Currently a skeleton: the HTTP layer (routes, request handling) has not yet been added — that lands in issue #4.

## Current capabilities

- Module-level Flask `app` exposed from `app.py` (importable by gunicorn as `app:app`).
- Database bootstrap on import: opens a psycopg2 connection from `DATABASE_URL` and creates the `messages` table if missing. Idempotent — safe to run on every worker start.
- `messages` schema: `id SERIAL PK`, `name TEXT NOT NULL`, `text TEXT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- Container image (`python:3.11-slim`) running gunicorn on port 8080.
- Direct `python app.py` entrypoint for local dev (binds `0.0.0.0:$PORT`, default 8080).

## Architecture & key decisions

- **Single-file app** (`app.py`) — no blueprints or package layout yet; expand only when routes/modules require it.
- **Bootstrap at import time, not lazily.** `init_db()` runs on module load so misconfiguration (missing `DATABASE_URL`, unreachable DB) fails the process immediately rather than on first request. `psycopg2.OperationalError` is logged and re-raised.
- **`DATABASE_URL` is required.** `get_conn()` raises `RuntimeError` if unset — no silent fallback.
- **psycopg2 (sync), not asyncpg or SQLAlchemy.** Raw SQL via cursor; transactions managed by `with conn:` context manager.
- **gunicorn in container, `flask run`/`python app.py` for local.** Both paths re-trigger the same import-time bootstrap.

## Layout

```
app.py            Flask app + DB bootstrap (issue #3)
requirements.txt  Flask 3.0.3, psycopg2-binary 2.9.9, gunicorn 22.0.0
Dockerfile        python:3.11-slim, gunicorn on :8080 (issue #2)
.env.example      DATABASE_URL template (issue #1)
```

## Conventions

- Configuration via environment variables only (`DATABASE_URL`, `PORT`).
- Schema changes are expressed as `CREATE TABLE IF NOT EXISTS` in `init_db()` — no migration tool yet.
- Fail loudly on startup misconfiguration; do not degrade silently.

## Not yet implemented

- HTTP routes (issue #4).
- Tests.
- Migrations / schema versioning.
- Observability (structured logging, metrics).
