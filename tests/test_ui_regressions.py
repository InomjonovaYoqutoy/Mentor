from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class SourceRegressionTests(unittest.TestCase):
    def test_home_header_does_not_render_up_next_island(self) -> None:
        home = source("mentor/ui/pages/home.py")
        self.assertNotIn("NextLessonIsland", home)
        self.assertNotIn("self.next_island", home)

    def test_dock_has_no_decorative_arc_line(self) -> None:
        widgets = source("mentor/ui/widgets.py")
        dock_start = widgets.index("class FloatingDock")
        dock_end = widgets.index("class QuickCreatePopover", dock_start)
        dock_source = widgets[dock_start:dock_end]
        self.assertNotIn("drawArc", dock_source)

    def test_quick_create_uses_custom_popup_not_qmenu(self) -> None:
        main = source("mentor/ui/main_window.py")
        self.assertIn("QuickCreatePopover", main)
        method_start = main.index("def _new_menu")
        method_end = main.index("def _quick_create_action", method_start)
        self.assertNotIn("QMenu", main[method_start:method_end])

    def test_notes_are_presented_as_one_workspace_surface(self) -> None:
        notes = source("mentor/ui/pages/notes.py")
        self.assertIn("workspace = Card()", notes)
        self.assertNotIn("left = Card()", notes)
        self.assertNotIn("right = Card()", notes)
        self.assertIn("splitter.addWidget(left)", notes)
        self.assertIn("splitter.addWidget(right)", notes)

    def test_student_profiles_are_real_and_manager_opens_them(self) -> None:
        profile = source("mentor/ui/student_profile.py")
        dialogs = source("mentor/ui/dialogs.py")
        main = source("mentor/ui/main_window.py")
        self.assertIn("class StudentProfileDialog", profile)
        self.assertIn("self.service.student_profile", profile)
        self.assertIn("self.service.update_attendance", profile)
        self.assertIn("self.table.doubleClicked.connect(self.profile)", dialogs)
        self.assertIn("open_student_profile", main)

    def test_lesson_editor_exposes_attendance_without_fake_state(self) -> None:
        dialogs = source("mentor/ui/dialogs.py")
        service = source("mentor/services/data_service.py")
        self.assertIn('add_enum_items(self.attendance,["Not marked","Present","Late","Absent","Excused"])', dialogs)
        self.assertIn('self.attendance.currentData()', dialogs)
        self.assertIn("allowed_attendance", service)
        self.assertIn("UPDATE sessions SET attendance=?", service)

    def test_lesson_click_opens_detail_sheet_before_editor(self) -> None:
        main = source("mentor/ui/main_window.py")
        detail = source("mentor/ui/lesson_detail.py")
        self.assertIn("class LessonDetailDialog", detail)
        self.assertIn("def open_lesson_detail", main)
        handle_start = main.index("def handle_action")
        handle_end = main.index("def add_student", handle_start)
        handle = main[handle_start:handle_end]
        self.assertIn('action == "session"', handle)
        self.assertIn("self.open_lesson_detail", handle)

    def test_schedule_right_click_uses_custom_lesson_popover(self) -> None:
        widgets = source("mentor/ui/widgets.py")
        schedule = source("mentor/ui/pages/schedule.py")
        main = source("mentor/ui/main_window.py")
        self.assertIn("class LessonContextPopover", widgets)
        self.assertIn("context_requested", schedule)
        self.assertIn("LessonContextPopover", main)
        pop_start = widgets.index("class LessonContextPopover")
        pop_end = widgets.index("class Toast", pop_start)
        self.assertNotIn("QMenu", widgets[pop_start:pop_end])

    def test_homework_has_real_ui_and_database_workflow(self) -> None:
        schema = source("mentor/database/schema.py")
        service = source("mentor/services/data_service.py")
        home = source("mentor/ui/pages/home.py")
        dialogs = source("mentor/ui/dialogs.py")
        self.assertIn("CREATE TABLE IF NOT EXISTS assignments", schema)
        self.assertIn("def save_assignment", service)
        self.assertIn("Homework & Assignments", home)
        self.assertIn("class AssignmentDialog", dialogs)
        self.assertIn("class AssignmentManager", dialogs)
        self.assertNotIn("fake homework", service.lower())

    def test_wrap_up_flow_combines_completion_attendance_notes_and_homework(self) -> None:
        dialogs = source("mentor/ui/dialogs.py")
        service = source("mentor/services/data_service.py")
        main = source("mentor/ui/main_window.py")
        self.assertIn("class LessonWrapUpDialog", dialogs)
        self.assertIn("def complete_session", service)
        self.assertIn("self.service.complete_session", main)
        self.assertIn("self.service.save_assignment", main)

    def test_recurring_series_have_real_group_id_and_scoped_actions(self) -> None:
        schema = source("mentor/database/schema.py")
        service = source("mentor/services/data_service.py")
        main = source("mentor/ui/main_window.py")
        self.assertIn("series_id TEXT", schema)
        self.assertIn("update_session_status_scope", service)
        self.assertIn("delete_session_scope", service)
        self.assertIn("uuid4().hex", main)
        self.assertIn("SeriesScopeDialog", main)

    def test_lesson_templates_are_persisted_not_hardcoded_presets(self) -> None:
        schema = source("mentor/database/schema.py")
        service = source("mentor/services/data_service.py")
        dialogs = source("mentor/ui/dialogs.py")
        self.assertIn("CREATE TABLE IF NOT EXISTS lesson_templates", schema)
        self.assertIn("def save_lesson_template", service)
        self.assertIn("self.service.save_lesson_template", dialogs)
        self.assertIn("self.service.lesson_template", dialogs)


    def test_recurring_edits_offer_this_future_or_series_scope(self) -> None:
        service = source("mentor/services/data_service.py")
        main = source("mentor/ui/main_window.py")
        dialogs = source("mentor/ui/dialogs.py")
        self.assertIn("def update_session_scope", service)
        self.assertIn('self._series_scope(session, "Edit")', main)
        self.assertIn('("future", "This and future lessons"', dialogs)
        self.assertIn('("series", "Entire series"', dialogs)

    def test_profile_actions_defer_nested_modal_opening(self) -> None:
        dialogs = source("mentor/ui/dialogs.py")
        start = dialogs.index("def _profile_action")
        end = dialogs.index("def edit", start)
        method = dialogs[start:end]
        self.assertIn("self.accept()", method)
        self.assertIn("QTimer.singleShot", method)

    def test_global_personal_has_real_localization_and_runtime_preferences(self) -> None:
        i18n = source("mentor/i18n.py")
        settings = source("mentor/ui/settings.py")
        tokens = source("mentor/theme/tokens.py")
        main = source("mentor/ui/main_window.py")
        self.assertIn('"uz": "O‘zbekcha"', i18n)
        self.assertIn('"ru": "Русский"', i18n)
        self.assertIn("def enum_canonical", i18n)
        self.assertIn("ACCENT_PRESETS", tokens)
        self.assertIn("Glass intensity", settings)
        self.assertIn("Interface density", settings)
        self.assertIn("Default schedule view", settings)
        self.assertIn("_rebuild_localized_ui", main)

    def test_translation_catalogs_cover_every_literal_ui_key(self) -> None:
        import ast
        import importlib.util
        keys: set[str] = set()
        for path in (ROOT / "mentor" / "ui").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "tr"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    keys.add(node.args[0].value)
        spec = importlib.util.spec_from_file_location("mentor_i18n_test", ROOT / "mentor" / "i18n.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        self.assertEqual([], sorted(keys - set(module.UZ)))
        self.assertEqual([], sorted(keys - set(module.RU)))

    def test_localized_enums_keep_database_values_canonical(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mentor_i18n_enum_test", ROOT / "mentor" / "i18n.py")
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        for lang in ("uz", "ru"):
            module.set_language(lang)
            shown = module.enum_display("Completed")
            self.assertNotEqual("Completed", shown)
            self.assertEqual("Completed", module.enum_canonical(shown))
        module.set_language("en")

    def test_settings_rebuild_preserves_notes_draft_and_schedule_context(self) -> None:
        main = source("mentor/ui/main_window.py")
        notes = source("mentor/ui/pages/notes.py")
        self.assertIn("draft_snapshot", notes)
        self.assertIn("restore_draft_snapshot", notes)
        self.assertIn('"schedule": {"anchor": self.schedule.anchor, "mode": self.schedule.mode}', main)
        self.assertIn("self._rebuild_localized_ui(preserved_state)", main)


if __name__ == "__main__":
    unittest.main()