"""Headless Qt smoke tests.

These tests are skipped when PySide6 is not installed. On a development Windows
machine they exercise real widget construction using Qt's offscreen platform.
They are intentionally small: they catch broken imports, impossible geometry,
and nested-page construction regressions before a build is handed to users.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
except ModuleNotFoundError:  # build environment without Qt
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 is not installed")
class QtRuntimeSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from mentor.database.database import Database
        from mentor.services.data_service import DataService

        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "mentor.db")
        self.service = DataService(self.db)
        self.service.set_setting("onboarding_complete", "1")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_main_window_and_dock_geometry(self):
        from mentor.ui.main_window import MainWindow

        window = MainWindow(self.service)
        window.resize(1200, 760)
        window.show()
        self.app.processEvents()
        dock = window.dock.geometry()
        root = window.root.rect()
        self.assertGreater(dock.width(), 0)
        self.assertGreaterEqual(dock.left(), root.left())
        self.assertLessEqual(dock.right(), root.right())
        self.assertGreaterEqual(dock.top(), root.top())
        self.assertLessEqual(dock.bottom(), root.bottom())
        window.close()

    def test_notes_page_constructs_and_new_student_note_prefills(self):
        from mentor.ui.pages.notes import NotesPage

        student_id = self.service.save_student(
            {"name": "Qt Test", "subject": "English", "status": "Active"}
        )
        page = NotesPage(self.service)
        page.resize(1000, 650)
        page.show()
        page.new_note(student_id=student_id)
        self.app.processEvents()
        self.assertEqual(page.student.currentData(), student_id)
        self.assertEqual(page.subject.text(), "English")
        page.close()

    def test_lesson_detail_and_homework_dialogs_construct(self):
        from mentor.ui.dialogs import AssignmentDialog
        from mentor.ui.lesson_detail import LessonDetailDialog

        student_id = self.service.save_student(
            {"name": "Homework Qt", "subject": "Physics", "status": "Active"}
        )
        session_id = self.service.save_session(
            {
                "student_id": student_id, "subject": "Physics",
                "session_date": "2026-10-01", "start_time": "10:00", "end_time": "11:00",
                "status": "Upcoming", "attendance": "Not marked",
            }
        )
        detail = LessonDetailDialog(self.service, session_id)
        detail.show(); self.app.processEvents()
        self.assertGreater(detail.width(), 0)
        detail.close()

        homework = AssignmentDialog(self.service, default_session_id=session_id)
        homework.show(); self.app.processEvents()
        self.assertEqual(homework.student.currentData(), student_id)
        self.assertEqual(homework.subject.text(), "Physics")
        homework.close()

    def test_session_dialog_loads_persisted_template(self):
        from mentor.ui.dialogs import SessionDialog

        student_id = self.service.save_student(
            {"name": "Template Qt", "subject": "IELTS", "status": "Active"}
        )
        template_id = self.service.save_lesson_template(
            {
                "name": "IELTS 90", "student_id": student_id, "subject": "IELTS",
                "duration_minutes": 90, "session_type": "Exam Prep", "location": "Online",
                "meeting_link": "", "reminder_minutes": 15, "recurrence": "Every week",
                "repeat_count": 8,
            }
        )
        dialog = SessionDialog(self.service)
        index = dialog.template_combo.findData(template_id)
        self.assertGreaterEqual(index, 0)
        dialog.template_combo.setCurrentIndex(index); self.app.processEvents()
        self.assertEqual(dialog.subject.currentText(), "IELTS")
        self.assertEqual(dialog.student.currentData(), student_id)
        self.assertEqual(dialog._duration_minutes(), 90)
        dialog.close()

    def test_student_profile_constructs_with_attendance(self):
        from mentor.ui.student_profile import StudentProfileDialog

        student_id = self.service.save_student(
            {"name": "Profile Test", "subject": "Math", "status": "Active"}
        )
        self.service.save_session(
            {
                "student_id": student_id,
                "subject": "Math",
                "session_date": "2026-09-30",
                "start_time": "10:00",
                "end_time": "11:00",
                "status": "Completed",
                "attendance": "Present",
            }
        )
        dialog = StudentProfileDialog(self.service, student_id)
        dialog.show()
        self.app.processEvents()
        self.assertGreater(dialog.width(), 0)
        self.assertGreater(dialog.height(), 0)
        dialog.close()

    def test_russian_ui_builds_and_session_enums_stay_canonical(self):
        from mentor.theme.preferences import apply_preferences
        self.service.set_setting("language", "ru")
        self.service.set_setting("accent", "blue")
        apply_preferences(self.service)

        from mentor.ui.main_window import MainWindow
        from mentor.ui.dialogs import SessionDialog

        window = MainWindow(self.service)
        window.show(); self.app.processEvents()
        self.assertEqual(window.dock.buttons["home"].text(), "Главная")
        dialog = SessionDialog(self.service)
        dialog.subject.setEditText("Physics")
        dialog.status.setCurrentIndex(dialog.status.findData("Completed"))
        self.assertEqual(dialog.data()["status"], "Completed")
        dialog.close(); window.close()

    def test_settings_cancel_restores_live_preview_tokens(self):
        from mentor.theme import tokens
        from mentor.theme.preferences import apply_preferences
        from mentor.ui.settings import SettingsDialog
        self.service.set_setting("accent", "orange")
        apply_preferences(self.service)
        dialog = SettingsDialog(self.service)
        blue = dialog.accent.findData("blue")
        dialog.accent.setCurrentIndex(blue); self.app.processEvents()
        self.assertEqual(tokens.ACCENT_KEY, "blue")
        dialog.reject(); self.app.processEvents()
        self.assertEqual(tokens.ACCENT_KEY, "orange")


if __name__ == "__main__":
    unittest.main()