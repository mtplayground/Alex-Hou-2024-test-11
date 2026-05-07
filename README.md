# Alex-Hou-2024-test-11

A minimal Flask app that lets visitors post short text messages and lists them
newest-first on the homepage. All state is stored in PostgreSQL.

- `GET /` renders the message list (newest first) and a post form.
- `POST /messages` inserts a row and redirects back to `/`.

The `messages` table is created on startup if it does not exist, so no manual
migration step is required.

## Requirements

- Python 3.11+
- A reachable PostgreSQL database (the `DATABASE_URL` connection string)
- Docker (only for the containerized run)

## Configuration

The app reads a single environment variable:

| Variable       | Required | Description                                                |
| -------------- | -------- | ---------------------------------------------------------- |
| `DATABASE_URL` | yes      | PostgreSQL DSN, e.g. `postgresql://user:pass@host:5432/db` |
| `PORT`         | no       | Port for `python app.py` direct run (default `8080`)       |

A template lives in `.env.example`.

## Run locally

```bash
# 1. install dependencies
pip install -r requirements.txt

# 2. point at your database
export DATABASE_URL='postgresql://user:password@localhost:5432/app'

# 3. start the dev server
flask --app app run --host 0.0.0.0 --port 8080
```

Open http://localhost:8080/ and submit a message — it should appear at the top
of the list after the redirect.

For a production-style local run, use gunicorn (already in `requirements.txt`):

```bash
gunicorn -b 0.0.0.0:8080 app:app
```

## Run with Docker

```bash
# 1. build the image
docker build -t alex-hou-messages .

# 2. run, passing the database URL through
docker run --rm -p 8080:8080 \
  -e DATABASE_URL='postgresql://user:password@host:5432/app' \
  alex-hou-messages
```

The container listens on `0.0.0.0:8080` via gunicorn (see `Dockerfile`).

If you are connecting to a Postgres instance running on the host machine from
the container, replace `localhost` in the DSN with `host.docker.internal` (or
the host's LAN IP on Linux).

## End-to-end smoke test

With the server running and `DATABASE_URL` reachable:

1. Open `http://localhost:8080/` — the form renders, list may be empty.
2. Enter a name and a message, click **Post**.
3. The browser is redirected back to `/` and the new message appears as the
   first `<li>` in the list (newest-first ordering).
4. Restart the server (Ctrl-C, then start again, or `docker run` a fresh
   container against the same `DATABASE_URL`) and reload `/` — the message is
   still there, confirming it persisted in PostgreSQL.

## Project layout

```
app.py             # Flask app + DB bootstrap
templates/         # Jinja templates (index.html)
requirements.txt   # Python dependencies
Dockerfile         # Container image (gunicorn on :8080)
.env.example       # Sample DATABASE_URL
```
