"""Flask messages app with PostgreSQL backend."""
from __future__ import annotations

import os
from typing import Optional

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row
from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)
db_initialized = False
db_available = True


def get_conn() -> Connection:
    """Open a new psycopg connection using DATABASE_URL.

    Raises RuntimeError if DATABASE_URL is not set so misconfiguration
    fails loudly at first use rather than silently connecting to nowhere.
    """
    dsn: Optional[str] = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    return psycopg.connect(dsn)


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


def ensure_db() -> None:
    """Initialize the database once per process, lazily on demand."""
    global db_initialized, db_available
    if not db_available:
        raise RuntimeError("database unavailable")
    if db_initialized:
        return
    try:
        init_db()
        db_initialized = True
    except psycopg.OperationalError:
        db_available = False
        raise


@app.route("/")
def index():
    """Render the message list ordered by newest first."""
    global db_available
    if not db_available:
        return render_template("index.html", messages=[])
    try:
        ensure_db()
        conn = get_conn()
        try:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    "SELECT id, name, text, created_at FROM messages "
                    "ORDER BY created_at DESC"
                )
                messages = cur.fetchall()
        finally:
            conn.close()
        return render_template("index.html", messages=messages)
    except psycopg.OperationalError:
        db_available = False
        app.logger.warning("Database access disabled for this worker.")
        return render_template("index.html", messages=[])


@app.route("/messages", methods=["POST"])
def post_message():
    """Insert a new message via parameterized SQL and redirect to /."""
    global db_available
    name = (request.form.get("name") or "").strip()
    text = (request.form.get("text") or "").strip()
    if not name or not text:
        return redirect(url_for("index"))
    if not db_available:
        return redirect(url_for("index"))
    try:
        ensure_db()
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
    except psycopg.OperationalError:
        db_available = False
        app.logger.warning("Database writes disabled for this worker.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
