# PRODUCT

## What this is

A minimal Flask "guestbook"-style web service backed by PostgreSQL, packaged for deployment on Fly.io. End-to-end functional: visitors can view all posted messages and submit new ones via a single HTML page.

## Current capabilities

- `GET /` renders `templates/index.html` with all messages ordered newest-first (`created_at DESC`).
- `POST /messages` accepts a form-encoded `name` + `text`, inserts a row via parameterized SQL, then 302-redirects to `/` (Post/Redirect/Get).
- Empty/whitespace-only `name` or `text` submissions are silently dropped (redirect without insert) — no error surface.
- Database bootstrap on import: opens a psycopg2 connection from `DATABASE_URL` and creates the `messages` table if missing. Idempotent — safe to run on every worker start.
- `messages` schema: `id SERIAL PK`, `name TEXT NOT NULL`, `text TEXT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT NOW()`.
- Container image (`python:3.11-slim`) running gunicorn on port 8080.
- Direct `python app.py` entrypoint for local dev (binds `0.0.0.0:$PORT`, default 8080).

## Architecture & key decisions

- **Single-file app** (`app.py`) — no blueprints or package layout yet; expand only when routes/modules require it.
- **Bootstrap at import time, not lazily.** `init_db()` runs on module load so misconfiguration (missing `DATABASE_URL`, unreachable DB) fails the process immediately rather than on first request. `psycopg2.OperationalError` is logged and re-raised.
- **`DATABASE_URL` is required.** `get_conn()` raises `RuntimeError` if unset — no silent fallback.
- **psycopg2 (sync), not asyncpg or SQLAlchemy.** Raw SQL via cursor; transactions managed by `with conn:` context manager. Read path uses `RealDictCursor` so templates can address columns by name.
- **Parameterized SQL only.** Inserts pass values as cursor params (`%s`), never via string formatting.
- **Server-side rendering with Jinja2 autoescape.** No JS, no client framework; `m.name`/`m.text` are rendered through Jinja's default autoescape so user-submitted content is HTML-safe.
- **Post/Redirect/Get pattern** for `POST /messages` to prevent duplicate submits on refresh.
- **gunicorn in container, `flask run`/`python app.py` for local.** Both paths re-trigger the same import-time bootstrap.

## Layout

```
app.py             Flask app, routes, DB bootstrap
templates/
  index.html       Message list + post form (single page)
requirements.txt   Flask 3.0.3, psycopg2-binary 2.9.9, gunicorn 22.0.0
Dockerfile         python:3.11-slim, gunicorn on :8080
.env.example       DATABASE_URL template
```

## Conventions

- Configuration via environment variables only (`DATABASE_URL`, `PORT`).
- Schema changes are expressed as `CREATE TABLE IF NOT EXISTS` in `init_db()` — no migration tool yet.
- Fail loudly on startup misconfiguration; do not degrade silently.
- All DB access goes through `get_conn()` with `try/finally` close — no connection pooling yet.
- Form input length capped client-side (`maxlength` on `name`/`text`); no server-side length enforcement beyond the `TEXT` column.

## Not yet implemented

- Tests.
- Migrations / schema versioning.
- Observability (structured logging, metrics).
- Pagination, message deletion/editing, auth.
- Server-side input length/rate limits.
