"""Flask app skeleton with PostgreSQL bootstrap.

Issue #3: defines the module-level Flask `app`, a psycopg2 connection
helper that reads DATABASE_URL from the environment, and an `init_db()`
function that creates the `messages` table if it does not exist.
Routes are added in issue #4.
"""
from __future__ import annotations

import os
from typing import Optional

import psycopg2
from psycopg2.extensions import connection as PgConnection
from flask import Flask


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


# Run the bootstrap once at import time so it executes under both
# `flask run` and gunicorn worker startup. Failures are surfaced
# immediately so the process does not start in a broken state.
try:
    init_db()
except psycopg2.OperationalError as exc:
    app.logger.error("Database bootstrap failed: %s", exc)
    raise


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
