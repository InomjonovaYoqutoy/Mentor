from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from uuid import uuid4

from PySide6.QtCore import QPoint, QSize, QTimer, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QMenu, QMessageBox, QPushButton,
    QStackedWidget, QToolButton, QVBoxLayout, QWidget
)

from .. import __version__
from ..services.data_service import DataService
from ..theme import tokens
from ..theme.preferences import apply_preferences
from ..i18n import tr, format_date, format_time
from .dialogs import (
    AssignmentDialog, AssignmentManager, FocusTimerDialog, GoalDialog, GoalManager,
    LessonWrapUpDialog, SearchDialog, SeriesScopeDialog, SessionDialog,
    StudentDialog, StudentManager, TaskDialog, TaskManager,
)
from .icons import icon
from .pages.home import HomePage
from .pages.materials import MaterialsPage
from .pages.notes import NotesPage
from .pages.schedule import SchedulePage
from .pages.statistics import StatisticsPage
from .student_profile import StudentProfileDialog
from .lesson_detail import LessonDetailDialog
from .settings import SettingsDialog
from .widgets import AtmosphereWidget, FloatingDock, LessonContextPopover, QuickCreatePopover, Toast

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, service: DataService):
        super().__init__()
        self.service = service
        self._reminded_sessions: set[int] = set()
        self.setWindowTitle("Mentor")
        self.resize(1450, 900)
        self.setMinimumSize(1100, 700)

        self.root = AtmosphereWidget(); self.setCentralWidget(self.root)
        layout = QVBoxLayout(self.root); layout.setContentsMargins(28,18,28,0); layout.setSpacing(10)
        layout.addLayout(self._build_topbar())

        self.stack = QStackedWidget(); layout.addWidget(self.stack,1)
        self.pages: dict[str, QWidget] = {}
        self._create_pages()

        self.dock = FloatingDock(self.root); self.dock.navigate.connect(self.navigate)
        self.quick_create = QuickCreatePopover(self)
        self.quick_create.action_triggered.connect(self._quick_create_action)
        self.lesson_context = LessonContextPopover(self)
        self.lesson_context.action_triggered.connect(self._lesson_context_action)
        self.toast = Toast(self.root)
        self._setup_shortcuts(); self._restore_window_state()
        initial = self.service.get_setting("last_page","home"); self.navigate(initial if initial in self.pages else "home")

        self.clock = QTimer(self); self.clock.timeout.connect(self._tick); self.clock.start(60_000); self._tick()
        QTimer.singleShot(250,self._first_run)

    def _create_pages(self) -> None:
        self.home = HomePage(self.service)
        self.schedule = SchedulePage(self.service)
        self.notes = NotesPage(self.service)
        self.materials = MaterialsPage(self.service)
        self.statistics = StatisticsPage(self.service)
        self.pages = {"home":self.home,"schedule":self.schedule,"notes":self.notes,"materials":self.materials,"statistics":self.statistics}
        for page in self.pages.values():
            self.stack.addWidget(page)
        self.home.request_action.connect(self.handle_action)
        self.schedule.request_action.connect(self.handle_action)
        self.notes.changed.connect(self.refresh_all)
        self.materials.changed.connect(self.refresh_all)

    def _rebuild_localized_ui(self, preserved_state: dict | None = None) -> None:
        current = self.service.get_setting("last_page", "home")
        for page in list(self.pages.values()):
            self.stack.removeWidget(page)
            page.deleteLater()
        self._create_pages()
        old_dock = self.dock
        old_dock.hide(); old_dock.deleteLater()
        self.dock = FloatingDock(self.root); self.dock.navigate.connect(self.navigate)
        self.quick_create.close(); self.quick_create.deleteLater()
        self.quick_create = QuickCreatePopover(self); self.quick_create.action_triggered.connect(self._quick_create_action)
        self.lesson_context.close(); self.lesson_context.deleteLater()
        self.lesson_context = LessonContextPopover(self); self.lesson_context.action_triggered.connect(self._lesson_context_action)
        if preserved_state:
            schedule_state = preserved_state.get("schedule") or {}
            anchor = schedule_state.get("anchor")
            mode = schedule_state.get("mode")
            if anchor is not None:
                self.schedule.set_anchor(anchor, mode)
            self.notes.restore_draft_snapshot(preserved_state.get("notes"))
        self._retranslate_topbar()
        self.root.update()
        self.navigate(current if current in self.pages else "home")
        QTimer.singleShot(0, self._position_floating_ui)

    def _build_topbar(self):
        row=QHBoxLayout();row.setContentsMargins(2,0,2,0);row.setSpacing(6)
        self.brand_mark=QLabel();self.brand_mark.setPixmap(icon("sparkles",tokens.ACCENT,23).pixmap(23,23))
        brand=QLabel("Mentor");brand.setStyleSheet("font-size:20px;font-weight:600;")
        version=QLabel(".".join(__version__.split(".")[:2]));version.setObjectName("muted");version.setStyleSheet(f"color:{tokens.MUTED};font-size:10px;")
        row.addWidget(self.brand_mark);row.addWidget(brand);row.addWidget(version);row.addStretch()

        self.new_button=QToolButton()
        self.new_button.setIcon(icon("plus",tokens.ACCENT,18))
        self.new_button.setIconSize(QSize(18,18))
        self.new_button.setFixedSize(36,36)
        self.new_button.setFocusPolicy(Qt.NoFocus)
        self.new_button.setCursor(Qt.PointingHandCursor)
        self.new_button.setToolTip(tr("Quick create (Ctrl+N)"))
        self.new_button.setStyleSheet(
            f"QToolButton{{background:{tokens.ACCENT_SOFT};border:1px solid {tokens.ACCENT_DARK};"
            "border-radius:18px;padding:0;}"
            f"QToolButton:hover{{background:{tokens.SURFACE3};border-color:{tokens.ACCENT};}}"
            f"QToolButton:pressed{{background:{tokens.ACCENT_SOFT};border-color:{tokens.ACCENT_BRIGHT};}}"
        )
        self.new_button.clicked.connect(lambda:self._new_menu(self.new_button));row.addWidget(self.new_button)

        self.date_button=QPushButton();self.date_button.setIcon(icon("calendar",tokens.TEXT2,17));self.date_button.setObjectName("pill");self.date_button.setCursor(Qt.PointingHandCursor);self.date_button.clicked.connect(lambda:self.navigate("schedule"));row.addWidget(self.date_button)
        self.search_button=QToolButton();self.search_button.setIcon(icon("search",tokens.TEXT2,21));self.search_button.clicked.connect(self.open_search);row.addWidget(self.search_button)
        self.bell=QToolButton();self.bell.setIcon(icon("bell",tokens.TEXT2,21));self.bell.clicked.connect(self.show_reminder_summary);row.addWidget(self.bell)
        self.profile_button=QToolButton();self.profile_button.setIcon(icon("user",tokens.TEXT2,21));self.profile_button.clicked.connect(lambda:self._profile_menu(self.profile_button));row.addWidget(self.profile_button)
        self._retranslate_topbar()
        return row

    def _retranslate_topbar(self) -> None:
        self.brand_mark.setPixmap(icon("sparkles",tokens.ACCENT,23).pixmap(23,23))
        self.new_button.setIcon(icon("plus",tokens.ACCENT,18))
        self.new_button.setStyleSheet(
            f"QToolButton{{background:{tokens.ACCENT_SOFT};border:1px solid {tokens.ACCENT_DARK};"
            "border-radius:18px;padding:0;}"
            f"QToolButton:hover{{background:{tokens.SURFACE3};border-color:{tokens.ACCENT};}}"
            f"QToolButton:pressed{{background:{tokens.ACCENT_SOFT};border-color:{tokens.ACCENT_BRIGHT};}}"
        )
        self.new_button.setToolTip(tr("Quick create (Ctrl+N)"))
        self.search_button.setToolTip(tr("Search Mentor (Ctrl+K)"))
        self.bell.setToolTip(tr("Upcoming reminders"))
        self.profile_button.setToolTip(tr("Profile and settings"))
        self._update_date_label()

    def _update_date_label(self) -> None:
        self.date_button.setText(format_date(date.today(), compact=True, relative=False))

    def _new_menu(self, button: QToolButton) -> None:
        self.quick_create.open_for(button)

    def _quick_create_action(self, action: str) -> None:
        if action == "add_session":
            self.add_session()
        elif action == "add_student":
            self.add_student()
        elif action == "add_note":
            self.navigate("notes")
            self.notes.new_note()
        elif action == "add_assignment":
            self.add_assignment()
        elif action == "new_task":
            self.add_task()
        elif action == "new_goal":
            self.add_goal()
        elif action == "add_material":
            self.navigate("materials")
            self.materials.add_material()
        elif action == "focus":
            self.open_focus()

    def _profile_menu(self, button: QToolButton) -> None:
        menu=QMenu(self);name=self.service.get_setting("profile_name","Teacher")
        title=QAction(name,menu);title.setEnabled(False);menu.addAction(title);menu.addSeparator()
        settings=menu.addAction(tr("Settings"));backup=menu.addAction(tr("Backup & Data"));about=menu.addAction(tr("About Mentor"));menu.addSeparator();quit_action=menu.addAction(tr("Quit"))
        chosen=menu.exec(button.mapToGlobal(QPoint(0,button.height())))
        if chosen==settings:self.open_settings()
        elif chosen==backup:self.open_settings("data")
        elif chosen==about:QMessageBox.information(self,tr("About Mentor"),f"Mentor {__version__} · {tr('Global & Personal')}\n{tr('Local-first teaching productivity for Windows.')}\n\nPython · PySide6 · SQLite")
        elif chosen==quit_action:self.close()

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+K"),self,activated=self.open_search)
        QShortcut(QKeySequence("Ctrl+N"),self,activated=self.context_new)
        QShortcut(QKeySequence("Ctrl+S"),self,activated=self.context_save)
        QShortcut(QKeySequence("1"),self,activated=lambda:self.navigate("home"));QShortcut(QKeySequence("2"),self,activated=lambda:self.navigate("schedule"));QShortcut(QKeySequence("3"),self,activated=lambda:self.navigate("notes"));QShortcut(QKeySequence("4"),self,activated=lambda:self.navigate("materials"));QShortcut(QKeySequence("5"),self,activated=lambda:self.navigate("statistics"))

    def context_new(self) -> None:
        key=self.service.get_setting("last_page","home")
        if key=="schedule":self.add_session(self.schedule.anchor)
        elif key=="notes":self.notes.new_note()
        elif key=="materials":self.materials.add_material()
        else:self._new_menu(self.new_button)

    def context_save(self) -> None:
        if self.service.get_setting("last_page","home")=="notes":self.notes.save();self.toast.show_message(tr("Note saved"))

    def _restore_window_state(self) -> None:
        try:
            w=int(self.service.get_setting("window_w","1450"));h=int(self.service.get_setting("window_h","900"));self.resize(max(1100,w),max(700,h))
        except ValueError:pass

    def _save_window_state(self) -> None:
        self.service.set_setting("window_w",str(self.width()));self.service.set_setting("window_h",str(self.height()))

    def _first_run(self) -> None:
        if self.service.get_setting("onboarding_complete","0")=="1":return
        box=QMessageBox(self);box.setWindowTitle(tr("Welcome to Mentor"));box.setText(tr("Welcome to Mentor"));box.setInformativeText(tr("Your teaching, organized.")+"\n\n"+tr("Start empty or load a small sample workspace to explore the app."))
        box.addButton(tr("Start Empty"),QMessageBox.AcceptRole);sample=box.addButton(tr("Load Sample Workspace"),QMessageBox.ActionRole);box.exec()
        if box.clickedButton()==sample:self.service.seed_sample_data();self.toast.show_message(tr("Sample workspace loaded"))
        self.service.set_setting("onboarding_complete","1");self.refresh_all()

    def navigate(self,key:str) -> None:
        if key not in self.pages:return
        self.stack.setCurrentWidget(self.pages[key]);self.dock.select(key);self.service.set_setting("last_page",key);self._refresh_page(key)

    def _refresh_page(self,key:str) -> None:
        page=self.pages[key]
        if hasattr(page,"refresh"):page.refresh()

    def refresh_all(self) -> None:
        for key in self.pages:
            try:self._refresh_page(key)
            except Exception:log.exception("Failed refreshing %s",key)

    def handle_action(self, action: str, payload) -> None:
        if action in self.pages:
            self.navigate(action); return
        if action == "students":
            self.open_students()
        elif action == "student_profile":
            self.open_student_profile(int(payload))
        elif action == "tasks":
            self.open_tasks()
        elif action == "assignments":
            self.open_assignments(int(payload) if isinstance(payload, int) else None)
        elif action == "assignment":
            self.edit_assignment(int(payload))
        elif action == "goals":
            self.open_goals()
        elif action == "add_student":
            self.add_student()
        elif action == "new_task":
            self.add_task()
        elif action == "add_assignment":
            default_student_id = None; default_session_id = None
            if isinstance(payload, int):
                default_student_id = payload
            elif isinstance(payload, dict):
                default_student_id = payload.get("student_id")
                default_session_id = payload.get("session_id")
            self.add_assignment(default_student_id, default_session_id)
        elif action == "new_goal":
            self.add_goal()
        elif action == "focus":
            self.open_focus()
        elif action == "schedule_lesson":
            self.add_session(default_student_id=int(payload))
        elif action == "add_session":
            default_date=None; default_time=None; default_student_id=None
            if isinstance(payload,date): default_date=payload
            elif isinstance(payload,dict):
                default_date=payload.get("date");default_time=payload.get("time");default_student_id=payload.get("student_id")
            self.add_session(default_date,default_time,default_student_id)
        elif action == "add_note":
            self.navigate("notes")
            self.notes.new_note(student_id=int(payload) if isinstance(payload,int) else None)
        elif action == "add_material":
            self.navigate("materials"); self.materials.add_material()
        elif action == "session":
            self.open_lesson_detail(int(payload))
        elif action == "edit_session":
            self.edit_session(int(payload))
        elif action == "wrap_up":
            self.wrap_up_lesson(int(payload))
        elif action == "duplicate_session":
            self.duplicate_session(int(payload))
        elif action == "cancel_session":
            self.cancel_session(int(payload))
        elif action == "delete_session":
            self.delete_session_action(int(payload))
        elif action == "session_context" and isinstance(payload, dict):
            self.show_session_context(int(payload["id"]), payload.get("pos"))

    def add_student(self) -> None:
        dialog=StudentDialog(self.service,parent=self)
        if dialog.exec()==QDialogAccepted:
            try:self.service.save_student(dialog.data());self.refresh_all();self.toast.show_message(tr("Student added"))
            except Exception as exc:log.exception("Could not save student");QMessageBox.critical(self,tr("Could not save student"),str(exc))

    def open_students(self) -> None:
        d=StudentManager(self.service,self)
        d.changed.connect(self.refresh_all)
        d.action_requested.connect(self.handle_action)
        d.exec()
        self.refresh_all()

    def open_student_profile(self, student_id: int) -> None:
        d=StudentProfileDialog(self.service,student_id,self)
        d.changed.connect(self.refresh_all)
        d.action_requested.connect(self.handle_action)
        d.exec()
        self.refresh_all()

    def add_task(self) -> None:
        d=TaskDialog(self.service,parent=self)
        if d.exec()==QDialogAccepted:
            try:self.service.save_task(d.data());self.refresh_all();self.toast.show_message(tr("Task created"))
            except Exception as exc:log.exception("Could not save task");QMessageBox.critical(self,tr("Could not save task"),str(exc))

    def open_tasks(self) -> None:
        d=TaskManager(self.service,self);d.changed.connect(self.refresh_all);d.exec();self.refresh_all()

    def add_assignment(self, default_student_id: int | None = None, default_session_id: int | None = None) -> None:
        dialog = AssignmentDialog(
            self.service, default_student_id=default_student_id,
            default_session_id=default_session_id, parent=self,
        )
        if dialog.exec() == QDialogAccepted:
            try:
                self.service.save_assignment(dialog.data()); self.refresh_all(); self.toast.show_message(tr("Homework assigned"))
            except Exception as exc:
                log.exception("Could not save homework"); QMessageBox.critical(self,tr("Homework not saved"),str(exc))

    def edit_assignment(self, assignment_id: int) -> None:
        assignment = self.service.assignment(assignment_id)
        if not assignment:
            return
        dialog = AssignmentDialog(self.service, assignment=assignment, parent=self)
        if dialog.exec() == QDialogAccepted:
            try:
                self.service.save_assignment(dialog.data(), assignment_id); self.refresh_all(); self.toast.show_message(tr("Homework saved"))
            except Exception as exc:
                log.exception("Could not update homework"); QMessageBox.critical(self,tr("Homework not saved"),str(exc))

    def open_assignments(self, student_id: int | None = None) -> None:
        dialog = AssignmentManager(self.service, self, student_id=student_id); dialog.changed.connect(self.refresh_all); dialog.exec(); self.refresh_all()

    def add_goal(self) -> None:
        d=GoalDialog(parent=self)
        if d.exec()==QDialogAccepted:
            try:self.service.save_goal(d.data());self.refresh_all();self.toast.show_message(tr("Goal created"))
            except Exception as exc:log.exception("Could not save goal");QMessageBox.critical(self,tr("Could not save goal"),str(exc))

    def open_goals(self) -> None:
        d=GoalManager(self.service,self);d.changed.connect(self.refresh_all);d.exec();self.refresh_all()

    def open_focus(self) -> None:
        FocusTimerDialog(self).exec()

    def open_lesson_detail(self, session_id: int) -> None:
        dialog = LessonDetailDialog(self.service, session_id, self)
        dialog.changed.connect(self.refresh_all)
        dialog.action_requested.connect(self.handle_action)
        dialog.exec()
        self.refresh_all()

    def wrap_up_lesson(self, session_id: int) -> None:
        session = self.service.session(session_id)
        if not session:
            return
        dialog = LessonWrapUpDialog(self.service, session, self)
        if dialog.exec() != QDialogAccepted:
            return
        data = dialog.data()
        try:
            self.service.complete_session(session_id, data["attendance"], data["notes"])
            if data.get("homework"):
                self.service.save_assignment(data["homework"])
            self.refresh_all(); self.toast.show_message(tr("Lesson completed"))
        except Exception as exc:
            log.exception("Could not complete lesson"); QMessageBox.critical(self,tr("Lesson not completed"),str(exc))

    def duplicate_session(self, session_id: int) -> None:
        try:
            duplicate_id = self.service.duplicate_session(session_id)
            self.refresh_all(); self.toast.show_message(tr("Lesson duplicated"))
            duplicate = self.service.session(duplicate_id)
            if duplicate:
                self.schedule.set_anchor(date.fromisoformat(duplicate["session_date"]), "week")
        except Exception as exc:
            log.exception("Could not duplicate lesson"); QMessageBox.critical(self,tr("Could not duplicate lesson"),str(exc))

    def cancel_session(self, session_id: int) -> None:
        session = self.service.session(session_id)
        if not session:
            return
        scope = self._series_scope(session, "Cancel")
        if scope is None:
            return
        prompt = tr("Cancel one lesson", subject=session["subject"], date=format_date(session["session_date"])) if scope == "this" else tr("Cancel lesson series part", subject=session["subject"])
        if QMessageBox.question(self,tr("Cancel lesson"),prompt) != QMessageBox.Yes:
            return
        try:
            count = self.service.update_session_status_scope(session_id,"Cancelled",scope)
            self.refresh_all(); self.toast.show_message(tr("Lessons cancelled", count=count))
        except Exception as exc:
            QMessageBox.critical(self,tr("Could not cancel lesson"),str(exc))

    def _series_scope(self, session: dict, action_name: str) -> str | None:
        if not session.get("series_id"):
            return "this"
        dialog = SeriesScopeDialog(action_name, self)
        return dialog.scope if dialog.exec() == QDialogAccepted else None

    def delete_session_action(self, session_id: int) -> None:
        session = self.service.session(session_id)
        if not session:
            return
        scope = self._series_scope(session, "Delete")
        if scope is None:
            return
        prompt = tr("Delete one lesson", subject=session["subject"]) if scope == "this" else tr("Delete lesson series part", subject=session["subject"])
        if QMessageBox.question(self,tr("Delete lesson"),prompt + " " + tr("This cannot be undone.")) != QMessageBox.Yes:
            return
        try:
            count = self.service.delete_session_scope(session_id, scope); self.refresh_all(); self.toast.show_message(tr("Lessons deleted", count=count))
        except Exception as exc:
            log.exception("Could not delete lesson"); QMessageBox.critical(self,tr("Could not delete lesson"),str(exc))

    def show_session_context(self, session_id: int, global_pos) -> None:
        session = self.service.session(session_id)
        if not session or global_pos is None:
            return
        self.lesson_context.open_for(global_pos, session_id, session.get("status") or "Upcoming")

    def _lesson_context_action(self, action: str, session_id: int) -> None:
        mapping = {
            "open": "session", "wrap_up": "wrap_up", "duplicate": "duplicate_session",
            "cancel": "cancel_session", "delete": "delete_session",
        }
        if action in mapping:
            QTimer.singleShot(0, lambda: self.handle_action(mapping[action], session_id))

    def add_session(self,default_date:date|None=None,default_time:str|None=None,default_student_id:int|None=None) -> None:
        d=SessionDialog(
            self.service,
            default_date=default_date,
            default_time=default_time,
            default_student_id=default_student_id,
            parent=self,
        )
        if d.exec()!=QDialogAccepted:return
        data=d.data();repeat_count=int(data.pop("repeat_count",8))
        if data.get("recurrence") != "None":
            data["series_id"] = uuid4().hex
        try:
            sid=self.service.save_session(data);self._create_recurrence_copies(data,sid,repeat_count)
            lesson_date=date.fromisoformat(data["session_date"]);self.schedule.set_anchor(lesson_date,"week");self.navigate("schedule")
            self.refresh_all();self.toast.show_message(f"{data['subject']} · {tr('Lesson scheduled')} · {format_time(data['start_time'])}")
        except Exception as exc:
            log.exception("Could not schedule lesson");QMessageBox.critical(self,tr("Could not schedule lesson"),f"{tr("Mentor couldn't save this lesson.")}\n\n{exc}")

    def _create_recurrence_copies(self,data:dict,original_id:int,occurrence_count:int=8) -> None:
        recurrence=data.get("recurrence","None")
        if recurrence=="None":return
        step={"Every day":1,"Every week":7,"Every 2 weeks":14}.get(recurrence)
        if not step:return
        start=date.fromisoformat(data["session_date"]);count=max(2,min(52,occurrence_count))
        for i in range(1,count):
            copy=dict(data)
            copy["session_date"]=(start+timedelta(days=step*i)).isoformat()
            copy["recurrence"]=recurrence
            copy["status"]="Upcoming"
            copy["attendance"]="Not marked"
            self.service.save_session(copy)

    def edit_session(self,session_id:int) -> None:
        session=self.service.session(session_id)
        if not session:return
        d=SessionDialog(self.service,session=session,parent=self);result=d.exec()
        try:
            if result==QDialogAccepted:
                data=d.data();data.pop("repeat_count",None)
                scope = self._series_scope(session, "Edit")
                if scope is None:
                    return
                count = self.service.update_session_scope(session_id, data, scope)
                self.refresh_all();self.toast.show_message(tr("Lesson saved") if count == 1 else tr("Lessons updated", count=count))
            elif result==2:
                self.duplicate_session(session_id)
            elif result==3:
                self.delete_session_action(session_id)
        except Exception as exc:
            log.exception("Could not update lesson");QMessageBox.critical(self,tr("Lesson update failed"),str(exc))

    def open_search(self) -> None:
        d=SearchDialog(self.service,self);d.navigate.connect(self.search_navigate);d.exec()

    def search_navigate(self,key:str,entity_id:int) -> None:
        if key=="students":self.open_student_profile(entity_id)
        elif key=="tasks":self.open_tasks()
        elif key=="schedule":
            session=self.service.session(entity_id)
            if session:
                self.schedule.set_anchor(date.fromisoformat(session["session_date"]),"week")
            self.navigate("schedule");self.open_lesson_detail(entity_id)
        elif key=="assignments":
            self.edit_assignment(entity_id)
        elif key=="notes":self.navigate("notes");self.notes.select_note(entity_id)
        elif key=="materials":self.navigate("materials");self.materials.select_material(entity_id)

    def open_settings(self, initial_section: str = "general") -> None:
        preserved_state = {
            "schedule": {"anchor": self.schedule.anchor, "mode": self.schedule.mode},
            "notes": self.notes.draft_snapshot(),
        }
        d=SettingsDialog(self.service,self,initial_section=initial_section)
        if d.exec()==QDialogAccepted:
            apply_preferences(self.service)
            self._rebuild_localized_ui(preserved_state)
            self.refresh_all()
            self.toast.show_message(tr("Settings saved"))
        else:
            apply_preferences(self.service)
            self.root.update()
            self.refresh_all()

    def show_reminder_summary(self) -> None:
        today=date.today();now=datetime.now();rows=self.service.sessions_between(today,today);upcoming=[]
        for session in rows:
            try:
                dt=datetime.combine(today,datetime.strptime(session["start_time"],"%H:%M").time())
                if now<=dt<=now+timedelta(hours=3) and session["status"] not in ("Cancelled","Completed"):
                    upcoming.append(f"{format_time(session['start_time'])}  {session['subject']}  ·  {session.get('student_name') or tr('Unassigned')}")
            except Exception:continue
        QMessageBox.information(self,tr("Upcoming lessons"),tr("No lessons in the next 3 hours.") if not upcoming else tr("Coming up:")+"\n\n"+"\n".join(upcoming))

    def _tick(self) -> None:
        self._update_date_label()
        if self.stack.currentWidget() is self.home:
            try:self.home.refresh()
            except Exception:log.exception("Failed to refresh live home data")
        if self.service.get_setting("notifications","1")=="0":return
        today=date.today();now=datetime.now()
        for session in self.service.sessions_between(today,today):
            if session["id"] in self._reminded_sessions or session["status"] in ("Cancelled","Completed"):continue
            try:
                reminder=int(session.get("reminder_minutes") or 0)
                if reminder<=0:continue
                dt=datetime.combine(today,datetime.strptime(session["start_time"],"%H:%M").time());minutes=(dt-now).total_seconds()/60
                if 0<=minutes<=reminder:
                    self.toast.show_message(f"{session['subject']} {tr('starts in')} {max(1,round(minutes))} min");self._reminded_sessions.add(session["id"])
            except Exception:continue

    def _position_floating_ui(self) -> None:
        if not hasattr(self, "dock"):
            return
        dock_w=min(610,max(550,self.root.width()-450));self.dock.setFixedWidth(dock_w)
        x=(self.root.width()-dock_w)//2;y=self.root.height()-self.dock.height()-18;self.dock.move(x,y);self.dock.raise_()
        if self.toast.isVisible():self.toast.move(self.root.width()-self.toast.width()-28,self.root.height()-self.toast.height()-118)

    def resizeEvent(self,event) -> None:
        super().resizeEvent(event)
        self._position_floating_ui()

    def closeEvent(self,event:QCloseEvent) -> None:
        self._save_window_state();event.accept()


# QDialog.Accepted is an enum value. Keeping it in one module-level name makes the
# comparisons explicit without importing QDialog just for every branch.
from PySide6.QtWidgets import QDialog
QDialogAccepted = QDialog.Accepted