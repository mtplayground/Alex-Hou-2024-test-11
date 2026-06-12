# PRODUCT

## What this is

A small Flask guestbook app with a server-rendered HTML UI. Visitors can submit
short messages and, when PostgreSQL is reachable, see messages listed
newest-first on the homepage.

## Current capabilities

- `GET /` renders a styled single-page guestbook from `templates/index.html`.
- `POST /messages` accepts `name` and `text`, inserts a message, then redirects
  back to `/`.
- Empty or whitespace-only submissions are ignored.
- The `messages` table is created lazily on first successful database access.
- If PostgreSQL is unavailable, the app keeps serving the form and empty state,
  disables further DB attempts in that worker, and avoids fatal startup errors.
- Static styling is served from `static/styles.css`.

## Architecture and decisions

- **Single-file backend**: routes, database bootstrap, and degraded-mode
  handling live in `app.py`.
- **Server-rendered frontend**: Jinja templates plus one CSS file; no JavaScript
  bundle or client framework.
- **PostgreSQL via psycopg 3**: synchronous raw SQL, parameterized writes, and
  `dict_row` reads for template-friendly records.
- **Lazy DB initialization**: startup does not depend on DB availability;
  schema bootstrap runs on demand.
- **Bounded DB connection attempts**: connections use a short timeout so a bad
  database endpoint does not hang gunicorn workers.
- **Production process**: gunicorn binds to `0.0.0.0:${PORT:-8080}`.

## Layout

```text
app.py               Flask app, routes, DB bootstrap, degraded-mode handling
templates/index.html Guestbook page and form
static/styles.css    Guestbook styling
requirements.txt     Flask, psycopg[binary], gunicorn
Dockerfile           Python container runtime
fly.toml             Fly config retained in the repo
```

## Conventions

- Configuration is environment-variable driven: `DATABASE_URL` controls
  persistence and `PORT` controls the bind port.
- DB reads and writes go through `get_conn()` and close connections explicitly.
- Schema setup is limited to `CREATE TABLE IF NOT EXISTS`; there is no migration
  framework yet.
- User-submitted values render through Jinja autoescaping.
- Form length limits are client-side `maxlength` attributes.

## Not implemented

- Tests.
- Authentication or user accounts.
- Pagination, editing, deletion, or moderation.
- Server-side rate limits or length validation.
- Connection pooling, retries, metrics, or structured logging.
