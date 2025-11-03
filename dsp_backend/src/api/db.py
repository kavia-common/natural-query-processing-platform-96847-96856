import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator, Optional

from .config import settings


def _ensure_parent_dir(path: str) -> None:
    """Ensure the parent directory for the DB file exists."""
    parent = os.path.dirname(path)
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def init_db() -> None:
    """Initialize database schema if it doesn't exist."""
    _ensure_parent_dir(settings.DB_FILE)
    with get_db() as conn:
        cur = conn.cursor()
        # Create a basic users table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite3 connection with check_same_thread=False for FastAPI use."""
    conn = sqlite3.connect(settings.DB_FILE, check_same_thread=False)
    try:
        # Ensure foreign key constraints enabled
        conn.execute("PRAGMA foreign_keys = ON;")
        yield conn
    finally:
        conn.close()


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[sqlite3.Row]:
    """Fetch user record by email. Returns a row-like tuple or None."""
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cur.fetchone()


def create_user(conn: sqlite3.Connection, email: str, password_hash: str) -> int:
    """Create a new user and return the inserted ID."""
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, password_hash),
    )
    conn.commit()
    return cur.lastrowid
