from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

from .schema import SCHEMA_SQL, SCHEMA_VERSION

log = logging.getLogger(__name__)


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self.initialize()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def initialize(self) -> None:
        with self.transaction():
            self._conn.executescript(SCHEMA_SQL)
            row = self._conn.execute(
                "SELECT value FROM app_metadata WHERE key='schema_version'"
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO app_metadata(key, value) VALUES('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif int(row["value"]) < SCHEMA_VERSION:
                self._run_migrations(int(row["value"]))
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_attendance ON sessions(attendance)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_series ON sessions(series_id)"
            )

    def _column_exists(self, table: str, column: str) -> bool:
        rows = self._conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(row["name"] == column for row in rows)

    def _run_migrations(self, current_version: int) -> None:
        """Run small, idempotent migrations without discarding user data."""
        if current_version < 1:
            current_version = 1

        if current_version < 2:
            additions = (
                ("session_type", "TEXT NOT NULL DEFAULT 'Lesson'"),
                ("meeting_link", "TEXT"),
                ("reminder_minutes", "INTEGER NOT NULL DEFAULT 15"),
                ("color_tag", "TEXT NOT NULL DEFAULT 'orange'"),
            )
            for column, declaration in additions:
                if not self._column_exists("sessions", column):
                    self._conn.execute(
                        f"ALTER TABLE sessions ADD COLUMN {column} {declaration}"
                    )
            current_version = 2

        if current_version < 3:
            if not self._column_exists("sessions", "attendance"):
                self._conn.execute(
                    "ALTER TABLE sessions ADD COLUMN attendance TEXT NOT NULL DEFAULT 'Not marked'"
                )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_attendance ON sessions(attendance)"
            )
            current_version = 3

        if current_version < 4:
            if not self._column_exists("sessions", "series_id"):
                self._conn.execute("ALTER TABLE sessions ADD COLUMN series_id TEXT")
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    session_id INTEGER,
                    material_id INTEGER,
                    subject TEXT,
                    title TEXT NOT NULL,
                    instructions TEXT NOT NULL DEFAULT '',
                    due_date TEXT,
                    status TEXT NOT NULL DEFAULT 'Assigned',
                    score TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                    FOREIGN KEY(material_id) REFERENCES materials(id) ON DELETE SET NULL
                );
                CREATE TABLE IF NOT EXISTS lesson_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    student_id INTEGER,
                    subject TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL DEFAULT 60,
                    session_type TEXT NOT NULL DEFAULT 'Lesson',
                    location TEXT,
                    meeting_link TEXT,
                    reminder_minutes INTEGER NOT NULL DEFAULT 15,
                    recurrence TEXT NOT NULL DEFAULT 'None',
                    repeat_count INTEGER NOT NULL DEFAULT 8,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
                );
                CREATE INDEX IF NOT EXISTS idx_sessions_series ON sessions(series_id);
                CREATE INDEX IF NOT EXISTS idx_assignments_due ON assignments(due_date);
                CREATE INDEX IF NOT EXISTS idx_assignments_student ON assignments(student_id);
                CREATE INDEX IF NOT EXISTS idx_assignments_session ON assignments(session_id);
                """
            )
            current_version = 4

        self._conn.execute(
            "UPDATE app_metadata SET value=? WHERE key='schema_version'",
            (str(SCHEMA_VERSION),),
        )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            log.exception("Database transaction failed")
            raise

    def execute(self, sql: str, params: Sequence[object] = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def query_all(self, sql: str, params: Sequence[object] = ()) -> list[sqlite3.Row]:
        return list(self._conn.execute(sql, params).fetchall())

    def query_one(self, sql: str, params: Sequence[object] = ()) -> sqlite3.Row | None:
        return self._conn.execute(sql, params).fetchone()

    def close(self) -> None:
        self._conn.close()