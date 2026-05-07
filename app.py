"""Flask messages app with PostgreSQL backend."""
from __future__ import annotations

import os
from typing import Optional

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor
from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)


def get_conn() -> PgConnection:
    """Open a new psycopg2 connection using DATABASE_URL.

    Raises RuntimeError if DATABASE_URL is not set so misconfiguration
    fails loudly at first use rather than silently connecting to nowhere.
    """
    dsn: Optional[str] = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg2.connect(dsn)


def init_db() -> None:
    """Create the messages table if it does not already exist.

    Idempotent: safe to call on every process startup. Uses a context
    manager so the transaction is committed on success and rolled back
    on error, and the connection is always closed.
    """
    ddl = """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(ddl)
    finally:
        conn.close()


@app.route("/")
def index():
    """Render the message list ordered by newest first."""
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, name, text, created_at FROM messages "
                "ORDER BY created_at DESC"
            )
            messages = cur.fetchall()
    finally:
        conn.close()
    return render_template("index.html", messages=messages)


@app.route("/messages", methods=["POST"])
def post_message():
    """Insert a new message via parameterized SQL and redirect to /."""
    name = (request.form.get("name") or "").strip()
    text = (request.form.get("text") or "").strip()
    if not name or not text:
        return redirect(url_for("index"))
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (name, text) VALUES (%s, %s)",
                    (name, text),
                )
    finally:
        conn.close()
    return redirect(url_for("index"))


# Run the bootstrap once at import time so it executes under both
# `flask run` and gunicorn worker startup.
try:
    init_db()
except psycopg2.OperationalError as exc:
    app.logger.error("Database bootstrap failed: %s", exc)
    raise


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
