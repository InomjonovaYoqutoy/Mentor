from __future__ import annotations

import csv
import json
import os
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.paths import backups_dir
from ..database.database import Database


class DataService:
    def __init__(self, db: Database):
        self.db = db

    # ---------- helpers ----------
    def _activity(self, type_: str, title: str, description: str = "", entity_type: str | None = None, entity_id: int | None = None) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO activity(entity_type, entity_id, type, title, description) VALUES(?,?,?,?,?)",
                (entity_type, entity_id, type_, title, description),
            )

    @staticmethod
    def _row(row: Any) -> dict[str, Any] | None:
        return dict(row) if row else None

    @staticmethod
    def _session_minutes(row: dict[str, Any] | Any) -> int:
        try:
            start = datetime.strptime(str(row["start_time"]), "%H:%M")
            end = datetime.strptime(str(row["end_time"]), "%H:%M")
            return max(0, int((end - start).total_seconds() // 60))
        except (KeyError, TypeError, ValueError):
            return 0

    @staticmethod
    def _needs_review(row: dict[str, Any], now: datetime | None = None) -> bool:
        """Return True when a lesson has ended but still looks unfinished."""
        if row.get("status") not in {"Upcoming", "In Progress"}:
            return False
        try:
            current = now or datetime.now()
            end_dt = datetime.combine(
                date.fromisoformat(str(row["session_date"])),
                datetime.strptime(str(row["end_time"]), "%H:%M").time(),
            )
            return end_dt < current
        except (KeyError, TypeError, ValueError):
            return False

    def _decorate_session(self, row: dict[str, Any]) -> dict[str, Any]:
        row["needs_review"] = self._needs_review(row)
        return row

    # ---------- settings ----------
    def get_setting(self, key: str, default: str = "") -> str:
        row = self.db.query_one("SELECT value FROM settings WHERE key=?", (key,))
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    # ---------- students ----------
    def students(self, search: str = "", active_only: bool = False) -> list[dict[str, Any]]:
        where, params = [], []
        if search:
            where.append("(name LIKE ? OR subject LIKE ? OR grade LIKE ? OR contact LIKE ?)")
            like = f"%{search}%"
            params += [like, like, like, like]
        if active_only:
            where.append("status='Active'")
        sql = "SELECT * FROM students"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY name COLLATE NOCASE"
        return [dict(r) for r in self.db.query_all(sql, params)]

    def student(self, student_id: int) -> dict[str, Any] | None:
        return self._row(self.db.query_one("SELECT * FROM students WHERE id=?", (student_id,)))

    def save_student(self, data: dict[str, Any], student_id: int | None = None) -> int:
        if not data.get("name", "").strip():
            raise ValueError("Student name is required.")
        values = (
            data["name"].strip(), data.get("age"), data.get("grade", "").strip(),
            data.get("subject", "").strip(), data.get("contact", "").strip(),
            data.get("notes", "").strip(), data.get("status", "Active"),
        )
        with self.db.transaction() as conn:
            if student_id:
                conn.execute(
                    "UPDATE students SET name=?,age=?,grade=?,subject=?,contact=?,notes=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    values + (student_id,),
                )
                sid = student_id
                title = "Student updated"
            else:
                cur = conn.execute(
                    "INSERT INTO students(name,age,grade,subject,contact,notes,status) VALUES(?,?,?,?,?,?,?)",
                    values,
                )
                sid = int(cur.lastrowid)
                title = "Student added"
        self._activity("student", title, data["name"], "student", sid)
        return sid

    def delete_student(self, student_id: int) -> None:
        student = self.student(student_id)
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM students WHERE id=?", (student_id,))
        if student:
            self._activity("student", "Student deleted", student["name"])

    def student_profile(self, student_id: int) -> dict[str, Any]:
        """Return the dashboard data needed by the student profile sheet.

        Attendance rate counts Present + Late as attended and excludes Excused
        and Not marked from the denominator. This keeps the metric useful while
        avoiding a penalty for lessons that have not been reviewed yet.
        """
        student = self.student(student_id)
        if not student:
            raise ValueError("Student not found.")

        raw_sessions = [dict(r) for r in self.db.query_all(
            """SELECT * FROM sessions WHERE student_id=?
               ORDER BY session_date DESC, start_time DESC""",
            (student_id,),
        )]
        active_sessions = [row for row in raw_sessions if row.get("status") != "Cancelled"]
        completed = [row for row in active_sessions if row.get("status") == "Completed"]
        total_minutes = sum(self._session_minutes(row) for row in completed)

        counts = {name: 0 for name in ("Present", "Late", "Absent", "Excused", "Not marked")}
        for row in active_sessions:
            value = str(row.get("attendance") or "Not marked")
            counts[value if value in counts else "Not marked"] += 1
        counted = counts["Present"] + counts["Late"] + counts["Absent"]
        attendance_rate = (
            round((counts["Present"] + counts["Late"]) / counted * 100)
            if counted else None
        )

        now = datetime.now()
        today = now.date().isoformat()
        current_time = now.strftime("%H:%M")
        upcoming_rows = [dict(r) for r in self.db.query_all(
            """SELECT * FROM sessions
               WHERE student_id=? AND status IN ('Upcoming','In Progress')
                 AND (session_date>? OR (session_date=? AND end_time>=?))
               ORDER BY session_date,start_time""",
            (student_id, today, today, current_time),
        )]

        notes_count = int(self.db.query_one(
            "SELECT COUNT(*) c FROM notes WHERE student_id=? AND archived=0",
            (student_id,),
        )["c"] or 0)
        materials_count = int(self.db.query_one(
            "SELECT COUNT(*) c FROM materials WHERE student_id=?",
            (student_id,),
        )["c"] or 0)
        open_tasks = int(self.db.query_one(
            "SELECT COUNT(*) c FROM tasks WHERE student_id=? AND completed=0",
            (student_id,),
        )["c"] or 0)
        open_assignments = int(self.db.query_one(
            "SELECT COUNT(*) c FROM assignments WHERE student_id=? AND status NOT IN ('Completed','Skipped')",
            (student_id,),
        )["c"] or 0)

        recent_notes = [dict(r) for r in self.db.query_all(
            """SELECT id,title,subject,updated_at FROM notes
               WHERE student_id=? AND archived=0
               ORDER BY pinned DESC,updated_at DESC LIMIT 4""",
            (student_id,),
        )]
        recent_tasks = [dict(r) for r in self.db.query_all(
            """SELECT id,title,due_date,priority,completed FROM tasks
               WHERE student_id=?
               ORDER BY completed, due_date IS NULL, due_date, created_at DESC LIMIT 4""",
            (student_id,),
        )]
        recent_assignments = [dict(r) for r in self.db.query_all(
            """SELECT id,title,subject,due_date,status,score FROM assignments
               WHERE student_id=?
               ORDER BY CASE WHEN status IN ('Completed','Skipped') THEN 1 ELSE 0 END,
                        due_date IS NULL, due_date, created_at DESC LIMIT 5""",
            (student_id,),
        )]

        return {
            "student": student,
            "lessons_total": len(active_sessions),
            "completed_lessons": len(completed),
            "teaching_minutes": total_minutes,
            "upcoming_count": len(upcoming_rows),
            "next_session": upcoming_rows[0] if upcoming_rows else None,
            "recent_sessions": raw_sessions[:7],
            "attendance": counts,
            "attendance_rate": attendance_rate,
            "notes_count": notes_count,
            "materials_count": materials_count,
            "open_tasks": open_tasks,
            "open_assignments": open_assignments,
            "recent_notes": recent_notes,
            "recent_tasks": recent_tasks,
            "recent_assignments": recent_assignments,
        }

    # ---------- sessions ----------
    def sessions_between(self, start: date, end: date) -> list[dict[str, Any]]:
        rows = [dict(r) for r in self.db.query_all(
            """SELECT s.*, st.name student_name FROM sessions s
               LEFT JOIN students st ON st.id=s.student_id
               WHERE s.session_date BETWEEN ? AND ?
               ORDER BY s.session_date, s.start_time""",
            (start.isoformat(), end.isoformat()),
        )]
        return [self._decorate_session(row) for row in rows]

    def session(self, session_id: int) -> dict[str, Any] | None:
        row = self._row(self.db.query_one(
            "SELECT s.*, st.name student_name FROM sessions s LEFT JOIN students st ON st.id=s.student_id WHERE s.id=?",
            (session_id,),
        ))
        return self._decorate_session(row) if row else None

    def save_session(self, data: dict[str, Any], session_id: int | None = None) -> int:
        subject = data.get("subject", "").strip()
        if not subject:
            raise ValueError("Subject is required.")
        if not data.get("session_date"):
            raise ValueError("Lesson date is required.")
        if data["end_time"] <= data["start_time"]:
            raise ValueError("End time must be later than start time.")

        reminder = data.get("reminder_minutes", 15)
        try:
            reminder = max(0, min(1440, int(reminder)))
        except (TypeError, ValueError):
            reminder = 15

        attendance = str(data.get("attendance") or "Not marked")
        allowed_attendance = {"Not marked", "Present", "Late", "Absent", "Excused"}
        if attendance not in allowed_attendance:
            raise ValueError("Invalid attendance status.")

        values = (
            data.get("student_id"),
            subject,
            data["session_date"],
            data["start_time"],
            data["end_time"],
            data.get("status", "Upcoming"),
            data.get("location", "").strip(),
            data.get("notes", "").strip(),
            data.get("recurrence", "None"),
            data.get("session_type", "Lesson"),
            data.get("meeting_link", "").strip(),
            reminder,
            data.get("color_tag", "orange"),
            attendance,
            data.get("series_id"),
        )
        with self.db.transaction() as conn:
            if session_id:
                conn.execute(
                    """UPDATE sessions SET student_id=?,subject=?,session_date=?,start_time=?,end_time=?,status=?,
                       location=?,notes=?,recurrence=?,session_type=?,meeting_link=?,reminder_minutes=?,color_tag=?,attendance=?,series_id=?,
                       updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    values + (session_id,),
                )
                sid = session_id
                title = "Lesson updated"
            else:
                cur = conn.execute(
                    """INSERT INTO sessions(
                           student_id,subject,session_date,start_time,end_time,status,location,notes,recurrence,
                           session_type,meeting_link,reminder_minutes,color_tag,attendance,series_id
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    values,
                )
                sid = int(cur.lastrowid)
                title = "Lesson scheduled"
        self._activity("session", title, f"{subject} · {data['session_date']} {data['start_time']}", "session", sid)
        return sid

    def delete_session(self, session_id: int) -> None:
        row = self.session(session_id)
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        if row:
            self._activity("session", "Lesson deleted", row["subject"])

    def duplicate_session(self, session_id: int) -> int:
        row = self.session(session_id)
        if not row:
            raise ValueError("Lesson not found.")
        keys = (
            "student_id", "subject", "session_date", "start_time", "end_time",
            "status", "location", "notes", "recurrence", "session_type",
            "meeting_link", "reminder_minutes", "color_tag", "attendance", "series_id",
        )
        data = {key: row.get(key) for key in keys}
        data["status"] = "Upcoming"
        data["recurrence"] = "None"
        data["attendance"] = "Not marked"
        data["series_id"] = None
        return self.save_session(data)

    def update_attendance(self, session_id: int, attendance: str) -> None:
        allowed = {"Not marked", "Present", "Late", "Absent", "Excused"}
        if attendance not in allowed:
            raise ValueError("Invalid attendance status.")
        row = self.session(session_id)
        if not row:
            raise ValueError("Lesson not found.")
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE sessions SET attendance=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (attendance, session_id),
            )
        if attendance != "Not marked":
            self._activity(
                "attendance",
                f"Attendance: {attendance}",
                f"{row['subject']} · {row.get('student_name') or 'Unassigned'}",
                "session",
                session_id,
            )

    def update_session_status(self, session_id: int, status: str) -> None:
        if status not in {"Upcoming", "In Progress", "Completed", "Cancelled"}:
            raise ValueError("Invalid lesson status.")
        row = self.session(session_id)
        if not row:
            raise ValueError("Lesson not found.")
        with self.db.transaction() as conn:
            conn.execute("UPDATE sessions SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status, session_id))
        self._activity("session", f"Lesson {status.lower()}", row["subject"], "session", session_id)

    def complete_session(self, session_id: int, attendance: str, notes: str) -> None:
        allowed = {"Not marked", "Present", "Late", "Absent", "Excused"}
        if attendance not in allowed:
            raise ValueError("Invalid attendance status.")
        row = self.session(session_id)
        if not row:
            raise ValueError("Lesson not found.")
        if row.get("student_id") is None:
            attendance = "Not marked"
        with self.db.transaction() as conn:
            conn.execute(
                """UPDATE sessions SET status='Completed',attendance=?,notes=?,updated_at=CURRENT_TIMESTAMP
                   WHERE id=?""",
                (attendance, notes.strip(), session_id),
            )
        self._activity(
            "session", "Lesson completed",
            f"{row['subject']} · {row.get('student_name') or 'Unassigned'}",
            "session", session_id,
        )

    def sessions_needing_review(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.db.query_all(
            """SELECT s.*, st.name student_name FROM sessions s
               LEFT JOIN students st ON st.id=s.student_id
               WHERE s.status IN ('Upcoming','In Progress')
               ORDER BY s.session_date, s.end_time"""
        )
        result = [self._decorate_session(dict(row)) for row in rows]
        return [row for row in result if row.get("needs_review")][:limit]

    def series_sessions(self, series_id: str) -> list[dict[str, Any]]:
        if not series_id:
            return []
        return [dict(r) for r in self.db.query_all(
            "SELECT * FROM sessions WHERE series_id=? ORDER BY session_date,start_time",
            (series_id,),
        )]

    def update_session_status_scope(self, session_id: int, status: str, scope: str = "this") -> int:
        if status not in {"Upcoming", "In Progress", "Completed", "Cancelled"}:
            raise ValueError("Invalid lesson status.")
        row = self.session(session_id)
        if not row:
            return 0
        series_id = row.get("series_id")
        if scope == "this" or not series_id:
            self.update_session_status(session_id, status)
            return 1
        if scope == "future":
            targets = self.db.query_all(
                """SELECT id FROM sessions WHERE series_id=?
                   AND (session_date>? OR (session_date=? AND start_time>=?))""",
                (series_id, row["session_date"], row["session_date"], row["start_time"]),
            )
        elif scope == "series":
            targets = self.db.query_all("SELECT id FROM sessions WHERE series_id=?", (series_id,))
        else:
            raise ValueError("Invalid series scope.")
        ids = [int(item["id"]) for item in targets]
        if ids:
            marks = ",".join("?" for _ in ids)
            with self.db.transaction() as conn:
                conn.execute(
                    f"UPDATE sessions SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id IN ({marks})",
                    [status, *ids],
                )
            self._activity("session", f"Lesson series {status.lower()}", f"Updated {len(ids)} lessons")
        return len(ids)

    def update_session_scope(self, session_id: int, data: dict[str, Any], scope: str = "this") -> int:
        """Update one occurrence or the structural fields of a recurring series.

        For series edits, each occurrence keeps its own attendance/status and its
        relative date position. If the edited occurrence is moved to another day,
        the same date delta is applied to the selected future/series occurrences.
        """
        original = self.session(session_id)
        if not original:
            return 0
        series_id = original.get("series_id")
        if scope == "this" or not series_id:
            clean = dict(data)
            clean["series_id"] = series_id
            self.save_session(clean, session_id)
            return 1
        if scope not in {"future", "series"}:
            raise ValueError("Invalid series scope.")

        if scope == "future":
            rows = self.db.query_all(
                """SELECT * FROM sessions WHERE series_id=?
                   AND (session_date>? OR (session_date=? AND start_time>=?))
                   ORDER BY session_date,start_time""",
                (series_id, original["session_date"], original["session_date"], original["start_time"]),
            )
        else:
            rows = self.db.query_all(
                "SELECT * FROM sessions WHERE series_id=? ORDER BY session_date,start_time",
                (series_id,),
            )
        targets = [dict(row) for row in rows]
        if not targets:
            return 0

        try:
            old_base = date.fromisoformat(original["session_date"])
            new_base = date.fromisoformat(str(data.get("session_date") or original["session_date"]))
            date_delta = new_base - old_base
        except ValueError:
            date_delta = timedelta(0)

        structural = {
            "student_id", "subject", "start_time", "end_time", "location",
            "recurrence", "session_type", "meeting_link", "reminder_minutes", "color_tag",
        }
        with self.db.transaction() as conn:
            for target in targets:
                try:
                    shifted_date = (date.fromisoformat(target["session_date"]) + date_delta).isoformat()
                except ValueError:
                    shifted_date = target["session_date"]
                merged = dict(target)
                for key in structural:
                    if key in data:
                        merged[key] = data.get(key)
                merged["session_date"] = shifted_date
                conn.execute(
                    """UPDATE sessions SET student_id=?,subject=?,session_date=?,start_time=?,end_time=?,
                       location=?,notes=?,recurrence=?,session_type=?,meeting_link=?,reminder_minutes=?,
                       color_tag=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (
                        merged.get("student_id"), str(merged.get("subject") or "").strip(),
                        merged["session_date"], merged["start_time"], merged["end_time"],
                        str(merged.get("location") or "").strip(), str(merged.get("notes") or "").strip(),
                        merged.get("recurrence") or "None", merged.get("session_type") or "Lesson",
                        str(merged.get("meeting_link") or "").strip(), int(merged.get("reminder_minutes") or 0),
                        merged.get("color_tag") or "orange", int(target["id"]),
                    ),
                )
        self._activity("session", "Lesson series edited", f"Updated {len(targets)} lessons")
        return len(targets)

    def delete_session_scope(self, session_id: int, scope: str = "this") -> int:
        row = self.session(session_id)
        if not row:
            return 0
        series_id = row.get("series_id")
        if scope == "this" or not series_id:
            self.delete_session(session_id)
            return 1
        if scope == "future":
            targets = self.db.query_all(
                """SELECT id FROM sessions WHERE series_id=?
                   AND (session_date>? OR (session_date=? AND start_time>=?))""",
                (series_id, row["session_date"], row["session_date"], row["start_time"]),
            )
        elif scope == "series":
            targets = self.db.query_all("SELECT id FROM sessions WHERE series_id=?", (series_id,))
        else:
            raise ValueError("Invalid series scope.")
        ids = [int(item["id"]) for item in targets]
        if ids:
            marks = ",".join("?" for _ in ids)
            with self.db.transaction() as conn:
                conn.execute(f"DELETE FROM sessions WHERE id IN ({marks})", ids)
            self._activity("session", "Lesson series updated", f"Removed {len(ids)} lessons")
        return len(ids)

    def session_conflicts(self, session_date: str, start_time: str, end_time: str, exclude_id: int | None = None) -> list[dict[str, Any]]:
        sql = """SELECT s.*, st.name student_name FROM sessions s LEFT JOIN students st ON st.id=s.student_id
                 WHERE s.session_date=? AND s.status!='Cancelled' AND s.start_time < ? AND s.end_time > ?"""
        params: list[Any] = [session_date, end_time, start_time]
        if exclude_id:
            sql += " AND s.id != ?"
            params.append(exclude_id)
        sql += " ORDER BY s.start_time"
        return [dict(r) for r in self.db.query_all(sql, params)]

    def next_session(self, from_dt: datetime | None = None) -> dict[str, Any] | None:
        now = from_dt or datetime.now()
        row = self.db.query_one(
            """SELECT s.*, st.name student_name FROM sessions s
               LEFT JOIN students st ON st.id=s.student_id
               WHERE s.status IN ('Upcoming','In Progress')
                 AND (s.session_date > ? OR (s.session_date = ? AND s.end_time >= ?))
               ORDER BY s.session_date, s.start_time LIMIT 1""",
            (now.date().isoformat(), now.date().isoformat(), now.strftime("%H:%M")),
        )
        return self._row(row)

    def recent_subjects(self, limit: int = 8) -> list[str]:
        rows = self.db.query_all(
            """SELECT subject, MAX(updated_at) touched FROM sessions
               WHERE TRIM(subject) != '' GROUP BY subject ORDER BY touched DESC LIMIT ?""",
            (limit,),
        )
        return [str(r["subject"]) for r in rows]

    # ---------- notes ----------
    def notes(self, search: str = "", include_archived: bool = False) -> list[dict[str, Any]]:
        where = [] if include_archived else ["n.archived=0"]
        params: list[Any] = []
        if search:
            where.append("(n.title LIKE ? OR n.content LIKE ? OR n.tags LIKE ? OR n.subject LIKE ?)")
            like = f"%{search}%"
            params += [like, like, like, like]
        sql = "SELECT n.*, s.name student_name FROM notes n LEFT JOIN students s ON s.id=n.student_id"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY n.pinned DESC, n.updated_at DESC"
        return [dict(r) for r in self.db.query_all(sql, params)]

    def note(self, note_id: int) -> dict[str, Any] | None:
        return self._row(self.db.query_one("SELECT * FROM notes WHERE id=?", (note_id,)))

    def save_note(self, data: dict[str, Any], note_id: int | None = None) -> int:
        title = data.get("title", "").strip() or "Untitled note"
        values = (
            data.get("student_id"), data.get("session_id"), data.get("subject", "").strip(), title,
            data.get("content", ""), data.get("tags", "").strip(), int(bool(data.get("pinned"))), int(bool(data.get("archived"))),
        )
        with self.db.transaction() as conn:
            if note_id:
                conn.execute(
                    "UPDATE notes SET student_id=?,session_id=?,subject=?,title=?,content=?,tags=?,pinned=?,archived=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                    values + (note_id,),
                )
                nid = note_id
                act = "Note saved"
            else:
                cur = conn.execute(
                    "INSERT INTO notes(student_id,session_id,subject,title,content,tags,pinned,archived) VALUES(?,?,?,?,?,?,?,?)",
                    values,
                )
                nid = int(cur.lastrowid)
                act = "New note added"
        self._activity("note", act, title, "note", nid)
        return nid

    def delete_note(self, note_id: int) -> None:
        note = self.note(note_id)
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        if note:
            self._activity("note", "Note deleted", note["title"])

    # ---------- materials ----------
    def materials(self, search: str = "", category: str = "") -> list[dict[str, Any]]:
        where, params = [], []
        if search:
            where.append("(m.name LIKE ? OR m.description LIKE ? OR m.path LIKE ?)")
            like = f"%{search}%"
            params += [like, like, like]
        if category and category != "All":
            where.append("m.category=?")
            params.append(category)
        sql = "SELECT m.*, s.name student_name FROM materials m LEFT JOIN students s ON s.id=m.student_id"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY m.created_at DESC"
        return [dict(r) for r in self.db.query_all(sql, params)]

    def save_material(self, data: dict[str, Any], material_id: int | None = None) -> int:
        if not data.get("name", "").strip() or not data.get("path", "").strip():
            raise ValueError("Name and path are required.")
        values = (data.get("student_id"), data["name"].strip(), data["path"].strip(), data.get("category", "General"), data.get("description", "").strip())
        with self.db.transaction() as conn:
            if material_id:
                conn.execute("UPDATE materials SET student_id=?,name=?,path=?,category=?,description=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", values + (material_id,))
                mid = material_id
            else:
                cur = conn.execute("INSERT INTO materials(student_id,name,path,category,description) VALUES(?,?,?,?,?)", values)
                mid = int(cur.lastrowid)
        self._activity("material", "Material added" if not material_id else "Material updated", data["name"], "material", mid)
        return mid

    def delete_material(self, material_id: int) -> None:
        row = self.db.query_one("SELECT name FROM materials WHERE id=?", (material_id,))
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM materials WHERE id=?", (material_id,))
        if row:
            self._activity("material", "Material removed", row["name"])

    # ---------- tasks ----------
    def tasks(self, include_completed: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT t.*, s.name student_name FROM tasks t LEFT JOIN students s ON s.id=t.student_id"
        if not include_completed:
            sql += " WHERE t.completed=0"
        sql += " ORDER BY t.completed, CASE t.priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END, t.due_date"
        return [dict(r) for r in self.db.query_all(sql)]

    def save_task(self, data: dict[str, Any], task_id: int | None = None) -> int:
        if not data.get("title", "").strip():
            raise ValueError("Task title is required.")
        values = (data.get("student_id"), data.get("session_id"), data.get("subject", "").strip(), data["title"].strip(), data.get("description", "").strip(), data.get("due_date"), data.get("priority", "Medium"), int(bool(data.get("completed"))))
        with self.db.transaction() as conn:
            if task_id:
                conn.execute("UPDATE tasks SET student_id=?,session_id=?,subject=?,title=?,description=?,due_date=?,priority=?,completed=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", values + (task_id,))
                tid = task_id
                title = "Task updated"
            else:
                cur = conn.execute("INSERT INTO tasks(student_id,session_id,subject,title,description,due_date,priority,completed) VALUES(?,?,?,?,?,?,?,?)", values)
                tid = int(cur.lastrowid)
                title = "Task created"
        self._activity("task", title, data["title"], "task", tid)
        return tid

    def toggle_task(self, task_id: int, completed: bool) -> None:
        with self.db.transaction() as conn:
            row = conn.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
            conn.execute("UPDATE tasks SET completed=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (int(completed), task_id))
        if row:
            self._activity("task", "Task completed" if completed else "Task reopened", row["title"], "task", task_id)

    def delete_task(self, task_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    # ---------- assignments / homework ----------
    def assignments(
        self,
        student_id: int | None = None,
        session_id: int | None = None,
        include_completed: bool = True,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if student_id is not None:
            where.append("a.student_id=?"); params.append(student_id)
        if session_id is not None:
            where.append("a.session_id=?"); params.append(session_id)
        if not include_completed:
            where.append("a.status NOT IN ('Completed','Skipped')")
        sql = """SELECT a.*, st.name student_name, m.name material_name
                 FROM assignments a
                 LEFT JOIN students st ON st.id=a.student_id
                 LEFT JOIN materials m ON m.id=a.material_id"""
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY CASE WHEN a.status IN ('Completed','Skipped') THEN 1 ELSE 0 END, a.due_date IS NULL, a.due_date, a.created_at DESC"
        rows = [dict(r) for r in self.db.query_all(sql, params)]
        today = date.today().isoformat()
        for row in rows:
            row["overdue"] = bool(
                row.get("due_date") and row["due_date"] < today
                and row.get("status") not in {"Completed", "Skipped"}
            )
        return rows

    def assignment(self, assignment_id: int) -> dict[str, Any] | None:
        row = self._row(self.db.query_one(
            """SELECT a.*, st.name student_name, m.name material_name
               FROM assignments a
               LEFT JOIN students st ON st.id=a.student_id
               LEFT JOIN materials m ON m.id=a.material_id
               WHERE a.id=?""",
            (assignment_id,),
        ))
        if row:
            row["overdue"] = bool(
                row.get("due_date") and row["due_date"] < date.today().isoformat()
                and row.get("status") not in {"Completed", "Skipped"}
            )
        return row

    def save_assignment(self, data: dict[str, Any], assignment_id: int | None = None) -> int:
        title = str(data.get("title") or "").strip()
        if not title:
            raise ValueError("Homework title is required.")
        status = str(data.get("status") or "Assigned")
        if status not in {"Assigned", "Submitted", "Completed", "Skipped"}:
            raise ValueError("Invalid homework status.")
        values = (
            data.get("student_id"), data.get("session_id"), data.get("material_id"),
            str(data.get("subject") or "").strip(), title,
            str(data.get("instructions") or "").strip(), data.get("due_date"),
            status, str(data.get("score") or "").strip(),
        )
        with self.db.transaction() as conn:
            if assignment_id:
                conn.execute(
                    """UPDATE assignments SET student_id=?,session_id=?,material_id=?,subject=?,title=?,
                       instructions=?,due_date=?,status=?,score=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    values + (assignment_id,),
                )
                aid = assignment_id
                activity_title = "Homework updated"
            else:
                cur = conn.execute(
                    """INSERT INTO assignments(student_id,session_id,material_id,subject,title,instructions,due_date,status,score)
                       VALUES(?,?,?,?,?,?,?,?,?)""",
                    values,
                )
                aid = int(cur.lastrowid)
                activity_title = "Homework assigned"
        self._activity("assignment", activity_title, title, "assignment", aid)
        return aid

    def set_assignment_status(self, assignment_id: int, status: str) -> None:
        if status not in {"Assigned", "Submitted", "Completed", "Skipped"}:
            raise ValueError("Invalid homework status.")
        row = self.assignment(assignment_id)
        if not row:
            raise ValueError("Homework not found.")
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE assignments SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (status, assignment_id),
            )
        self._activity("assignment", f"Homework {status.lower()}", row["title"], "assignment", assignment_id)

    def delete_assignment(self, assignment_id: int) -> None:
        row = self.assignment(assignment_id)
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM assignments WHERE id=?", (assignment_id,))
        if row:
            self._activity("assignment", "Homework deleted", row["title"])

    # ---------- lesson templates ----------
    def lesson_templates(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all(
            """SELECT t.*, s.name student_name FROM lesson_templates t
               LEFT JOIN students s ON s.id=t.student_id ORDER BY t.name COLLATE NOCASE"""
        )]

    def lesson_template(self, template_id: int) -> dict[str, Any] | None:
        return self._row(self.db.query_one("SELECT * FROM lesson_templates WHERE id=?", (template_id,)))

    def save_lesson_template(self, data: dict[str, Any], template_id: int | None = None) -> int:
        name = str(data.get("name") or "").strip()
        subject = str(data.get("subject") or "").strip()
        if not name or not subject:
            raise ValueError("Template name and subject are required.")
        duration = max(15, min(480, int(data.get("duration_minutes") or 60)))
        repeat_count = max(2, min(52, int(data.get("repeat_count") or 8)))
        values = (
            name, data.get("student_id"), subject, duration,
            data.get("session_type", "Lesson"), str(data.get("location") or "").strip(),
            str(data.get("meeting_link") or "").strip(), int(data.get("reminder_minutes") or 0),
            data.get("recurrence", "None"), repeat_count,
        )
        with self.db.transaction() as conn:
            if template_id:
                conn.execute(
                    """UPDATE lesson_templates SET name=?,student_id=?,subject=?,duration_minutes=?,session_type=?,
                       location=?,meeting_link=?,reminder_minutes=?,recurrence=?,repeat_count=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                    values + (template_id,),
                )
                return template_id
            cur = conn.execute(
                """INSERT INTO lesson_templates(name,student_id,subject,duration_minutes,session_type,location,meeting_link,
                   reminder_minutes,recurrence,repeat_count) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                values,
            )
            return int(cur.lastrowid)

    def delete_lesson_template(self, template_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM lesson_templates WHERE id=?", (template_id,))

    # ---------- goals ----------
    def goals(self) -> list[dict[str, Any]]:
        return [dict(r) for r in self.db.query_all("SELECT * FROM goals ORDER BY status='Active' DESC, deadline")]

    def save_goal(self, data: dict[str, Any], goal_id: int | None = None) -> int:
        if not data.get("title", "").strip():
            raise ValueError("Goal title is required.")
        target = max(float(data.get("target") or 1), 0.0001)
        progress = max(float(data.get("progress") or 0), 0)
        values = (data["title"].strip(), data.get("description", "").strip(), target, progress, data.get("deadline"), data.get("status", "Active"))
        with self.db.transaction() as conn:
            if goal_id:
                conn.execute("UPDATE goals SET title=?,description=?,target=?,progress=?,deadline=?,status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", values + (goal_id,))
                gid = goal_id
            else:
                cur = conn.execute("INSERT INTO goals(title,description,target,progress,deadline,status) VALUES(?,?,?,?,?,?)", values)
                gid = int(cur.lastrowid)
        self._activity("goal", "Goal updated" if goal_id else "Goal created", data["title"], "goal", gid)
        return gid

    def delete_goal(self, goal_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))

    # ---------- dashboard / statistics ----------
    def dashboard(self) -> dict[str, Any]:
        today = date.today().isoformat()
        now_time = datetime.now().strftime("%H:%M")
        students = self.db.query_one("SELECT COUNT(*) c FROM students WHERE status='Active'")["c"]
        upcoming = self.db.query_one(
            "SELECT COUNT(*) c FROM sessions WHERE session_date=? AND end_time>=? AND status IN ('Upcoming','In Progress')",
            (today, now_time),
        )["c"]
        tasks_due = self.db.query_one(
            "SELECT COUNT(*) c FROM tasks WHERE completed=0 AND due_date IS NOT NULL AND due_date<=?",
            (today,),
        )["c"]
        assignments_due = self.db.query_one(
            """SELECT COUNT(*) c FROM assignments
               WHERE status NOT IN ('Completed','Skipped') AND due_date IS NOT NULL AND due_date<=?""",
            (today,),
        )["c"]
        assignments_overdue = self.db.query_one(
            """SELECT COUNT(*) c FROM assignments
               WHERE status NOT IN ('Completed','Skipped') AND due_date IS NOT NULL AND due_date<?""",
            (today,),
        )["c"]
        attendance_pending = self.db.query_one(
            """SELECT COUNT(*) c FROM sessions
               WHERE student_id IS NOT NULL AND status='Completed' AND attendance='Not marked'"""
        )["c"]
        goals = self.goals()
        ratios = [
            min(1.0, (g["progress"] or 0) / max(g["target"] or 1, 0.0001))
            for g in goals if g["status"] == "Active"
        ]
        goal_progress = round(sum(ratios) / len(ratios) * 100) if ratios else 0
        today_sessions = self.sessions_between(date.today(), date.today())
        activity = [dict(r) for r in self.db.query_all("SELECT * FROM activity ORDER BY timestamp DESC LIMIT 6")]
        next_lesson = self.next_session()
        lesson_review_count = len(self.sessions_needing_review(limit=200))
        assignment_rows = self.assignments(include_completed=False)[:4]
        week_start = date.today() - timedelta(days=date.today().weekday())
        week_end = week_start + timedelta(days=6)
        week_count = self.db.query_one(
            "SELECT COUNT(*) c FROM sessions WHERE session_date BETWEEN ? AND ? AND status!='Cancelled'",
            (week_start.isoformat(), week_end.isoformat()),
        )["c"]
        return {
            "students": students,
            "upcoming": upcoming,
            "tasks_due": tasks_due,
            "assignments_due": assignments_due,
            "assignments_overdue": assignments_overdue,
            "assignment_rows": assignment_rows,
            "lesson_review_count": lesson_review_count,
            "attendance_pending": attendance_pending,
            "goal_progress": goal_progress,
            "today_sessions": today_sessions,
            "activity": activity,
            "next_session": next_lesson,
            "week_count": week_count,
        }

    def contextual_insight(self) -> str:
        data = self.dashboard()
        if data["assignments_overdue"]:
            n = data["assignments_overdue"]
            return f"{n} homework item{'s' if n != 1 else ''} overdue — worth a quick follow-up."
        if data["lesson_review_count"]:
            n = data["lesson_review_count"]
            return f"{n} past lesson{'s' if n != 1 else ''} still need review or completion."
        if data["tasks_due"]:
            n = data["tasks_due"]
            return f"{n} task{'s' if n != 1 else ''} need your attention today."
        if data["attendance_pending"]:
            n = data["attendance_pending"]
            return f"Attendance still needs marking for {n} completed lesson{'s' if n != 1 else ''}."
        if data["upcoming"] >= 4:
            return f"Busy day ahead — {data['upcoming']} lessons still on your schedule."
        if data["next_session"]:
            nxt = data["next_session"]
            return f"Next up: {nxt['subject']} at {nxt['start_time']}. Keep the next step simple."
        if data["today_sessions"]:
            return "Your teaching day is wrapped up. Capture anything worth remembering."
        return "Your schedule is clear. A little preparation now can make tomorrow lighter."

    def teaching_hours_by_day(self, days: int = 7) -> list[tuple[str, float]]:
        start = date.today() - timedelta(days=days - 1)
        rows = self.db.query_all(
            """SELECT session_date, start_time, end_time FROM sessions
               WHERE session_date BETWEEN ? AND ? AND status!='Cancelled'""",
            (start.isoformat(), date.today().isoformat()),
        )
        totals: dict[str, float] = {(start + timedelta(days=i)).isoformat(): 0.0 for i in range(days)}
        for r in rows:
            st = datetime.strptime(r["start_time"], "%H:%M")
            en = datetime.strptime(r["end_time"], "%H:%M")
            totals[r["session_date"]] += max(0.0, (en - st).total_seconds() / 3600)
        return list(totals.items())

    def attendance_statistics(self) -> dict[str, Any]:
        rows = self.db.query_all(
            """SELECT attendance, COUNT(*) c FROM sessions
               WHERE status!='Cancelled' GROUP BY attendance"""
        )
        counts = {name: 0 for name in ("Present", "Late", "Absent", "Excused", "Not marked")}
        for row in rows:
            key = str(row["attendance"] or "Not marked")
            counts[key if key in counts else "Not marked"] = int(row["c"] or 0)
        counted = counts["Present"] + counts["Late"] + counts["Absent"]
        rate = round((counts["Present"] + counts["Late"]) / counted * 100) if counted else None
        return {"counts": counts, "rate": rate, "marked": counted + counts["Excused"]}

    def statistics(self) -> dict[str, Any]:
        completed = self.db.query_one("SELECT COUNT(*) c FROM sessions WHERE status='Completed'")["c"]
        students_taught = self.db.query_one("SELECT COUNT(DISTINCT student_id) c FROM sessions WHERE status='Completed' AND student_id IS NOT NULL")["c"]
        tasks_completed = self.db.query_one("SELECT COUNT(*) c FROM tasks WHERE completed=1")["c"]
        assignments_completed = self.db.query_one("SELECT COUNT(*) c FROM assignments WHERE status='Completed'")["c"]
        total_hours = 0.0
        rows = self.db.query_all("SELECT start_time,end_time FROM sessions WHERE status='Completed'")
        for r in rows:
            st = datetime.strptime(r["start_time"], "%H:%M")
            en = datetime.strptime(r["end_time"], "%H:%M")
            total_hours += max(0.0, (en - st).total_seconds() / 3600)
        attendance = self.attendance_statistics()
        return {
            "completed_sessions": completed,
            "students_taught": students_taught,
            "tasks_completed": tasks_completed,
            "assignments_completed": assignments_completed,
            "teaching_hours": round(total_hours, 1),
            "weekly_hours": self.teaching_hours_by_day(7),
            "attendance_rate": attendance["rate"],
            "attendance_counts": attendance["counts"],
            "attendance_marked": attendance["marked"],
        }

    # ---------- search ----------
    def search(self, query: str) -> dict[str, list[dict[str, Any]]]:
        q = query.strip()
        if not q:
            return {"Students": [], "Sessions": [], "Notes": [], "Materials": [], "Assignments": [], "Tasks": []}
        like = f"%{q}%"
        return {
            "Students": [dict(r) for r in self.db.query_all("SELECT id,name,subject,grade FROM students WHERE name LIKE ? OR subject LIKE ? OR grade LIKE ? LIMIT 8", (like, like, like))],
            "Sessions": [dict(r) for r in self.db.query_all("SELECT id,subject,session_date,start_time FROM sessions WHERE subject LIKE ? OR notes LIKE ? LIMIT 8", (like, like))],
            "Notes": [dict(r) for r in self.db.query_all("SELECT id,title,subject,updated_at FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? LIMIT 8", (like, like, like))],
            "Materials": [dict(r) for r in self.db.query_all("SELECT id,name,category,path FROM materials WHERE name LIKE ? OR category LIKE ? OR description LIKE ? LIMIT 8", (like, like, like))],
            "Assignments": [dict(r) for r in self.db.query_all("SELECT id,title,due_date,status,subject FROM assignments WHERE title LIKE ? OR instructions LIKE ? OR subject LIKE ? LIMIT 8", (like, like, like))],
            "Tasks": [dict(r) for r in self.db.query_all("SELECT id,title,due_date,priority FROM tasks WHERE title LIKE ? OR description LIKE ? LIMIT 8", (like, like))],
        }

    # ---------- backup / export ----------
    def backup_database(self, destination: Path | None = None) -> Path:
        if destination is None:
            destination = backups_dir() / f"mentor-backup-{datetime.now():%Y%m%d-%H%M%S}.db"
        self.db.connection.commit()
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        backup_conn = __import__("sqlite3").connect(target)
        try:
            self.db.connection.backup(backup_conn)
        finally:
            backup_conn.close()
        return target

    def restore_database(self, source: Path) -> None:
        import sqlite3        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        src = sqlite3.connect(source)
        try:
            # A SQLite backup into the live connection is atomic from the app's point of view.
            src.backup(self.db.connection)
            self.db.connection.commit()
            self.db.connection.execute("PRAGMA foreign_keys = ON")
            self.db.initialize()
        finally:
            src.close()

    def export_json(self, destination: Path) -> Path:
        payload: dict[str, Any] = {}
        for table in ("students", "sessions", "notes", "materials", "tasks", "assignments", "lesson_templates", "goals", "activity"):
            payload[table] = [dict(r) for r in self.db.query_all(f"SELECT * FROM {table}")]
        destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return destination

    def export_students_csv(self, destination: Path) -> Path:
        rows = self.students()
        fields = ["id", "name", "age", "grade", "subject", "contact", "status", "created_at"]
        with destination.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k) for k in fields})
        return destination

    # ---------- sample ----------
    def seed_sample_data(self) -> None:
        if self.db.query_one("SELECT COUNT(*) c FROM students")["c"]:
            return
        ids = []
        for name, grade, subject in [
            ("Aziza Karimova", "Grade 10", "Math"),
            ("Bekzod Rakhimov", "Grade 11", "Physics"),
            ("Madinabonu Aliyeva", "Grade 9", "English"),
            ("Timur Akhmedov", "Private", "CS Basics"),
        ]:
            ids.append(self.save_student({"name": name, "grade": grade, "subject": subject, "status": "Active"}))
        today = date.today()
        for idx, (time_, subject, status) in enumerate([
            ("09:00", "Math", "Completed"), ("11:00", "Physics", "In Progress"),
            ("14:00", "English", "Upcoming"), ("16:00", "CS Basics", "Upcoming")
        ]):
            start = datetime.strptime(time_, "%H:%M")
            end = (start + timedelta(hours=1)).strftime("%H:%M")
            self.save_session({
                "student_id": ids[idx], "subject": subject, "session_date": today.isoformat(),
                "start_time": time_, "end_time": end, "status": status, "location": "",
                "notes": "", "recurrence": "None",
                "attendance": "Present" if status == "Completed" else "Not marked",
            })
        self.save_note({"student_id": ids[1], "subject": "Physics", "title": "Key formulas", "content": "Review Newton's laws and momentum.", "tags": "physics, review", "pinned": True, "archived": False})
        self.save_task({"student_id": ids[0], "title": "Prepare algebra worksheet", "description": "", "due_date": today.isoformat(), "priority": "High", "completed": False})
        self.save_task({"student_id": ids[2], "title": "Check essay drafts", "description": "", "due_date": today.isoformat(), "priority": "Medium", "completed": False})
        self.save_assignment({
            "student_id": ids[0], "session_id": None, "subject": "Math",
            "title": "Quadratics practice", "instructions": "Complete exercises 1–8.",
            "due_date": (today + timedelta(days=2)).isoformat(), "status": "Assigned", "score": "",
        })
        self.save_goal({"title": "Complete 20 sessions this month", "description": "", "target": 20, "progress": 13, "deadline": (today + timedelta(days=20)).isoformat(), "status": "Active"})