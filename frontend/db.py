"""SQLite users for the Flask front-end."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

# username -> password is username + "01"
SEED_USERS = (
    ("juanjo", "juanjo01"),
    ("tom", "tom01"),
)


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
            """
        )
        for username, password in SEED_USERS:
            existing = conn.execute(
                "SELECT 1 FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                continue
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
        conn.commit()


def verify_user(db_path: str | Path, username: str, password: str) -> bool:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
    if row is None:
        return False
    return check_password_hash(row["password_hash"], password)
