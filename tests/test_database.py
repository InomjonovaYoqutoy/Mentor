from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

from mentor.database.database import Database
from mentor.services.data_service import DataService


class DataServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "mentor.db")
        self.service = DataService(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _student(self, name: str = "Test Student") -> int:
        return self.service.save_student(
            {"name": name, "grade": "10", "subject": "Math", "status": "Active"}
        )

    def test_crud_dashboard_search_and_next_lesson(self):
        student_id = self._student()
        now = datetime.now()
        start_dt = now.replace(second=0, microsecond=0) + timedelta(minutes=10)
        if start_dt.date() != now.date():
            start_dt = now.replace(hour=23, minute=20, second=0, microsecond=0)
        end_dt = start_dt + timedelta(minutes=30)
        if end_dt.date() != start_dt.date():
            end_dt = start_dt.replace(hour=23, minute=59)

        session_id = self.service.save_session(
            {
                "student_id": student_id,
                "subject": "Math",
                "session_date": start_dt.date().isoformat(),
                "start_time": start_dt.strftime("%H:%M"),
                "end_time": end_dt.strftime("%H:%M"),
                "status": "Upcoming",
                "location": "Room 4",
                "meeting_link": "",
                "notes": "Quadratics",
                "recurrence": "None",
                "session_type": "Lesson",
                "reminder_minutes": 10,
                "color_tag": "orange",
                "attendance": "Not marked",
            }
        )
        self.service.save_task(
            {
                "student_id": student_id,
                "session_id": session_id,
                "subject": "Math",
                "title": "Worksheet",
                "description": "",
                "due_date": date.today().isoformat(),
                "priority": "High",
                "completed": False,
            }
        )
        lesson = self.service.session(session_id)
        self.assertEqual(lesson["reminder_minutes"], 10)
        self.assertEqual(lesson["session_type"], "Lesson")
        self.assertEqual(lesson["attendance"], "Not marked")
        dash = self.service.dashboard()
        self.assertEqual(dash["students"], 1)
        self.assertGreaterEqual(dash["tasks_due"], 1)
        self.assertTrue(self.service.search("Math")["Sessions"])

    def test_duplicate_does_not_repeat_series_or_attendance(self):
        sid = self.service.save_session(
            {
                "student_id": None,
                "subject": "Physics",
                "session_date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
                "status": "Completed",
                "location": "",
                "notes": "",
                "recurrence": "Every week",
                "attendance": "Present",
            }
        )
        duplicate = self.service.duplicate_session(sid)
        row = self.service.session(duplicate)
        self.assertEqual(row["recurrence"], "None")
        self.assertEqual(row["status"], "Upcoming")
        self.assertEqual(row["attendance"], "Not marked")

    def test_lesson_conflicts_and_notes_persist(self):
        day = date.today().isoformat()
        first = self.service.save_session(
            {
                "student_id": None,
                "subject": "English",
                "session_date": day,
                "start_time": "14:00",
                "end_time": "15:00",
                "status": "Upcoming",
                "location": "",
                "notes": "",
                "recurrence": "None",
                "session_type": "Lesson",
                "meeting_link": "",
                "reminder_minutes": 15,
                "color_tag": "orange",
                "attendance": "Not marked",
            }
        )
        conflicts = self.service.session_conflicts(day, "14:30", "15:30")
        self.assertEqual([row["id"] for row in conflicts], [first])

        note_id = self.service.save_note(
            {
                "student_id": None,
                "session_id": first,
                "subject": "English",
                "title": "Lesson notes",
                "content": "Vocabulary review",
                "tags": "vocab",
                "pinned": True,
                "archived": False,
            }
        )
        note = self.service.note(note_id)
        self.assertEqual(note["title"], "Lesson notes")
        self.assertEqual(note["content"], "Vocabulary review")
        self.assertEqual(note["session_id"], first)

    def test_student_profile_and_attendance_rate(self):
        student_id = self._student("Aziz")
        statuses = ["Present", "Late", "Absent", "Excused", "Not marked"]
        for index, attendance in enumerate(statuses):
            sid = self.service.save_session(
                {
                    "student_id": student_id,
                    "subject": "Math",
                    "session_date": (date.today() - timedelta(days=index + 1)).isoformat(),
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "status": "Completed",
                    "location": "",
                    "notes": "",
                    "recurrence": "None",
                    "attendance": attendance,
                }
            )
            if attendance == "Not marked":
                self.service.update_attendance(sid, "Present")

        self.service.save_note(
            {
                "student_id": student_id,
                "session_id": None,
                "subject": "Math",
                "title": "Progress note",
                "content": "Good work",
                "tags": "",
                "pinned": False,
                "archived": False,
            }
        )
        self.service.save_task(
            {
                "student_id": student_id,
                "session_id": None,
                "subject": "Math",
                "title": "Practice",
                "description": "",
                "due_date": None,
                "priority": "Medium",
                "completed": False,
            }
        )

        profile = self.service.student_profile(student_id)
        self.assertEqual(profile["lessons_total"], 5)
        self.assertEqual(profile["completed_lessons"], 5)
        self.assertEqual(profile["teaching_minutes"], 300)
        # Present + Late + Present = 3 attended; Absent = 1 denominator miss.
        self.assertEqual(profile["attendance_rate"], 75)
        self.assertEqual(profile["notes_count"], 1)
        self.assertEqual(profile["open_tasks"], 1)

    def test_homework_workflow_dashboard_profile_and_search(self):
        student_id = self._student("Homework Student")
        session_id = self.service.save_session(
            {
                "student_id": student_id,
                "subject": "Math",
                "session_date": date.today().isoformat(),
                "start_time": "10:00",
                "end_time": "11:00",
                "status": "Completed",
                "attendance": "Present",
            }
        )
        assignment_id = self.service.save_assignment(
            {
                "student_id": student_id,
                "session_id": session_id,
                "material_id": None,
                "subject": "Math",
                "title": "Quadratics practice",
                "instructions": "Complete questions 1-8",
                "due_date": date.today().isoformat(),
                "status": "Assigned",
                "score": "",
            }
        )
        assignment = self.service.assignment(assignment_id)
        self.assertEqual(assignment["student_name"], "Homework Student")
        self.assertEqual(assignment["session_id"], session_id)
        self.assertTrue(self.service.search("Quadratics")["Assignments"])
        dashboard = self.service.dashboard()
        self.assertEqual(dashboard["assignments_due"], 1)
        self.assertEqual(dashboard["assignment_rows"][0]["id"], assignment_id)
        profile = self.service.student_profile(student_id)
        self.assertEqual(profile["open_assignments"], 1)
        self.assertEqual(profile["recent_assignments"][0]["title"], "Quadratics practice")
        self.service.set_assignment_status(assignment_id, "Completed")
        self.assertEqual(self.service.assignment(assignment_id)["status"], "Completed")
        self.assertEqual(self.service.student_profile(student_id)["open_assignments"], 0)

    def test_lesson_wrap_up_completion_persists_attendance_and_notes(self):
        student_id = self._student("Wrap Student")
        session_id = self.service.save_session(
            {
                "student_id": student_id,
                "subject": "English",
                "session_date": date.today().isoformat(),
                "start_time": "09:00",
                "end_time": "10:00",
                "status": "Upcoming",
                "attendance": "Not marked",
            }
        )
        self.service.complete_session(session_id, "Late", "Reviewed speaking part 2")
        row = self.service.session(session_id)
        self.assertEqual(row["status"], "Completed")
        self.assertEqual(row["attendance"], "Late")
        self.assertEqual(row["notes"], "Reviewed speaking part 2")

    def test_past_upcoming_lesson_is_flagged_for_review(self):
        yesterday = date.today() - timedelta(days=1)
        session_id = self.service.save_session(
            {
                "student_id": None,
                "subject": "Review me",
                "session_date": yesterday.isoformat(),
                "start_time": "08:00",
                "end_time": "09:00",
                "status": "Upcoming",
                "attendance": "Not marked",
            }
        )
        row = self.service.session(session_id)
        self.assertTrue(row["needs_review"])
        self.assertIn(session_id, [item["id"] for item in self.service.sessions_needing_review()])
        self.assertGreaterEqual(self.service.dashboard()["lesson_review_count"], 1)

    def test_lesson_templates_round_trip(self):
        student_id = self._student("Template Student")
        template_id = self.service.save_lesson_template(
            {
                "name": "Weekly IELTS",
                "student_id": student_id,
                "subject": "IELTS",
                "duration_minutes": 90,
                "session_type": "Exam Prep",
                "location": "Online",
                "meeting_link": "https://example.com",
                "reminder_minutes": 30,
                "recurrence": "Every week",
                "repeat_count": 10,
            }
        )
        template = self.service.lesson_template(template_id)
        self.assertEqual(template["duration_minutes"], 90)
        self.assertEqual(template["recurrence"], "Every week")
        self.assertEqual(self.service.lesson_templates()[0]["student_name"], "Template Student")

    def test_recurring_series_scope_cancel_delete_and_duplicate_detaches(self):
        series_id = "series-test"
        ids = []
        start = date.today() + timedelta(days=1)
        for i in range(3):
            ids.append(self.service.save_session(
                {
                    "student_id": None,
                    "subject": "Series",
                    "session_date": (start + timedelta(days=7*i)).isoformat(),
                    "start_time": "12:00",
                    "end_time": "13:00",
                    "status": "Upcoming",
                    "recurrence": "Every week",
                    "series_id": series_id,
                    "attendance": "Not marked",
                }
            ))
        changed = self.service.update_session_status_scope(ids[1], "Cancelled", "future")
        self.assertEqual(changed, 2)
        self.assertEqual(self.service.session(ids[0])["status"], "Upcoming")
        self.assertEqual(self.service.session(ids[1])["status"], "Cancelled")
        self.assertEqual(self.service.session(ids[2])["status"], "Cancelled")
        duplicate = self.service.duplicate_session(ids[0])
        self.assertIsNone(self.service.session(duplicate)["series_id"])
        deleted = self.service.delete_session_scope(ids[0], "series")
        self.assertEqual(deleted, 3)
        self.assertIsNotNone(self.service.session(duplicate))

    def test_recurring_series_edit_can_apply_to_future_without_overwriting_attendance(self):
        student_id = self._student("Series Edit Student")
        series_id = "series-edit"
        start = date.today() + timedelta(days=2)
        ids = []
        for i in range(3):
            ids.append(self.service.save_session(
                {
                    "student_id": student_id,
                    "subject": "Math",
                    "session_date": (start + timedelta(days=7*i)).isoformat(),
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "status": "Completed" if i == 0 else "Upcoming",
                    "attendance": "Present" if i == 0 else "Not marked",
                    "recurrence": "Every week",
                    "series_id": series_id,
                }
            ))
        selected = self.service.session(ids[1])
        edited = dict(selected)
        edited.update({
            "subject": "Advanced Math",
            "session_date": (date.fromisoformat(selected["session_date"]) + timedelta(days=1)).isoformat(),
            "start_time": "11:30",
            "end_time": "12:30",
            "location": "Room 9",
        })
        changed = self.service.update_session_scope(ids[1], edited, "future")
        self.assertEqual(changed, 2)
        first = self.service.session(ids[0])
        second = self.service.session(ids[1])
        third = self.service.session(ids[2])
        self.assertEqual(first["subject"], "Math")
        self.assertEqual(first["attendance"], "Present")
        self.assertEqual(second["subject"], "Advanced Math")
        self.assertEqual(second["start_time"], "11:30")
        self.assertEqual(second["attendance"], "Not marked")
        self.assertEqual(second["session_date"], (start + timedelta(days=8)).isoformat())
        self.assertEqual(third["session_date"], (start + timedelta(days=15)).isoformat())

    def test_invalid_attendance_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.save_session(
                {
                    "student_id": None,
                    "subject": "Math",
                    "session_date": date.today().isoformat(),
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "attendance": "Definitely",
                }
            )

    def test_backup(self):
        destination = Path(self.tmp.name) / "backup.db"
        result = self.service.backup_database(destination)
        self.assertTrue(result.exists())


class MigrationTests(unittest.TestCase):
    def test_version_one_database_is_upgraded_to_four_without_data_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.db"
            conn = sqlite3.connect(path)
            conn.executescript(
                """
                CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT INTO app_metadata(key,value) VALUES('schema_version','1');
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    subject TEXT NOT NULL,
                    session_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Upcoming',
                    location TEXT,
                    notes TEXT,
                    recurrence TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO sessions(subject,session_date,start_time,end_time,status)
                VALUES('Legacy Math','2026-10-01','09:00','10:00','Upcoming');
                """
            )
            conn.commit()
            conn.close()
            db = Database(path)
            columns = {r["name"] for r in db.query_all("PRAGMA table_info(sessions)")}
            self.assertIn("meeting_link", columns)
            self.assertIn("reminder_minutes", columns)
            self.assertIn("attendance", columns)
            self.assertIn("series_id", columns)
            self.assertEqual(db.query_one("SELECT subject FROM sessions WHERE id=1")["subject"], "Legacy Math")
            self.assertEqual(db.query_one("SELECT attendance FROM sessions WHERE id=1")["attendance"], "Not marked")
            self.assertEqual(db.query_one("SELECT value FROM app_metadata WHERE key='schema_version'")["value"], "4")
            db.close()

    def test_version_two_database_gets_v3_and_v4_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v2.db"
            conn = sqlite3.connect(path)
            conn.executescript(
                """
                CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT INTO app_metadata(key,value) VALUES('schema_version','2');
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    subject TEXT NOT NULL,
                    session_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Upcoming',
                    location TEXT,
                    notes TEXT,
                    recurrence TEXT,
                    session_type TEXT NOT NULL DEFAULT 'Lesson',
                    meeting_link TEXT,
                    reminder_minutes INTEGER NOT NULL DEFAULT 15,
                    color_tag TEXT NOT NULL DEFAULT 'orange',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO sessions(subject,session_date,start_time,end_time,status)
                VALUES('Physics','2026-10-01','12:00','13:00','Completed');
                """
            )
            conn.commit()
            conn.close()
            db = Database(path)
            self.assertEqual(db.query_one("SELECT attendance FROM sessions WHERE id=1")["attendance"], "Not marked")
            columns = {r["name"] for r in db.query_all("PRAGMA table_info(sessions)")}
            self.assertIn("series_id", columns)
            tables = {r["name"] for r in db.query_all("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("assignments", tables)
            self.assertIn("lesson_templates", tables)
            self.assertEqual(db.query_one("SELECT value FROM app_metadata WHERE key='schema_version'")["value"], "4")
            db.close()

    def test_version_three_database_is_upgraded_to_four(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v3.db"
            conn = sqlite3.connect(path)
            conn.executescript(
                """
                CREATE TABLE app_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT INTO app_metadata(key,value) VALUES('schema_version','3');
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, age INTEGER, grade TEXT, subject TEXT,
                    contact TEXT, notes TEXT, status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, name TEXT NOT NULL, path TEXT NOT NULL,
                    category TEXT, description TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, subject TEXT NOT NULL, session_date TEXT NOT NULL,
                    start_time TEXT NOT NULL, end_time TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Upcoming', location TEXT,
                    notes TEXT, recurrence TEXT, session_type TEXT NOT NULL DEFAULT 'Lesson', meeting_link TEXT,
                    reminder_minutes INTEGER NOT NULL DEFAULT 15, color_tag TEXT NOT NULL DEFAULT 'orange',
                    attendance TEXT NOT NULL DEFAULT 'Not marked', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                INSERT INTO sessions(subject,session_date,start_time,end_time,status,attendance)
                VALUES('V3 lesson','2026-10-01','15:00','16:00','Upcoming','Not marked');
                """
            )
            conn.commit(); conn.close()
            db = Database(path)
            columns = {r["name"] for r in db.query_all("PRAGMA table_info(sessions)")}
            self.assertIn("series_id", columns)
            self.assertEqual(db.query_one("SELECT subject FROM sessions WHERE id=1")["subject"], "V3 lesson")
            self.assertEqual(db.query_one("SELECT value FROM app_metadata WHERE key='schema_version'")["value"], "4")
            tables = {r["name"] for r in db.query_all("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("assignments", tables)
            self.assertIn("lesson_templates", tables)
            db.close()


if __name__ == "__main__":
    unittest.main()