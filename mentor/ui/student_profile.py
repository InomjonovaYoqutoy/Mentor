from __future__ import annotations

from datetime import date, datetime
from typing import Any

from PySide6.QtCore import QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..services.data_service import DataService
from ..theme import tokens
from ..i18n import tr, enum_display, format_date, format_time
from .icons import icon
from .widgets import Card


ATTENDANCE_VALUES = ["Not marked", "Present", "Late", "Absent", "Excused"]


class StudentProfileDialog(QDialog):
    """A focused student workspace without adding another permanent app page."""

    action_requested = Signal(str, object)
    changed = Signal()

    def __init__(self, service: DataService, student_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.service = service
        self.student_id = int(student_id)
        self.setWindowTitle(tr("Student Profile"))
        self.setModal(True)
        self.setMinimumSize(900, 650)
        self.resize(1040, 720)
        self.setStyleSheet(f"QDialog{{background:{tokens.BG2};}}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.layout = QVBoxLayout(self.body)
        self.layout.setContentsMargins(28, 26, 28, 26)
        self.layout.setSpacing(16)
        scroll.setWidget(self.body)
        root.addWidget(scroll)

        self.refresh()

    @staticmethod
    def _clear(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child = item.layout()
            if widget:
                widget.deleteLater()
            elif child:
                StudentProfileDialog._clear(child)  # type: ignore[arg-type]

    @staticmethod
    def _initials(name: str) -> str:
        pieces = [part for part in name.strip().split() if part]
        if not pieces:
            return "?"
        if len(pieces) == 1:
            return pieces[0][:2].upper()
        return (pieces[0][0] + pieces[-1][0]).upper()

    @staticmethod
    def _hours(minutes: int) -> str:
        if minutes <= 0:
            return "0h"
        hours, remainder = divmod(minutes, 60)
        if hours and remainder:
            return f"{hours}h {remainder}m"
        if hours:
            return f"{hours}h"
        return f"{remainder}m"

    def refresh(self) -> None:
        self._clear(self.layout)
        try:
            data = self.service.student_profile(self.student_id)
        except Exception as exc:
            QMessageBox.critical(self, tr("Student unavailable"), str(exc))
            self.reject()
            return

        student = data["student"]
        self._build_header(student)
        self._build_metrics(data)
        self._build_content(data)
        self.layout.addStretch()
        self._build_footer()

    def _build_header(self, student: dict[str, Any]) -> None:
        row = QHBoxLayout()
        row.setSpacing(15)

        avatar = QLabel(self._initials(student.get("name") or ""))
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(64, 64)
        avatar.setStyleSheet(
            f"background:{tokens.ACCENT_SOFT};color:{tokens.ACCENT};border:1px solid {tokens.ACCENT_DARK};"
            "border-radius:32px;font-size:19px;font-weight:700;"
        )
        row.addWidget(avatar)

        identity = QVBoxLayout()
        identity.setSpacing(3)
        name = QLabel(student.get("name") or tr("Student"))
        name.setStyleSheet("font-size:25px;font-weight:650;")
        identity.addWidget(name)

        metadata = [student.get("grade"), student.get("subject"), student.get("contact")]
        sub = QLabel("  ·  ".join(str(value) for value in metadata if value))
        sub.setObjectName("secondary")
        sub.setWordWrap(True)
        identity.addWidget(sub)
        row.addLayout(identity, 1)

        status = QLabel(enum_display(student.get("status") or "Active"))
        status.setAlignment(Qt.AlignCenter)
        status.setContentsMargins(11, 6, 11, 6)
        status_color = tokens.SUCCESS if student.get("status") == "Active" else tokens.TEXT2
        status.setStyleSheet(
            f"color:{status_color};background:#151A17;border:1px solid rgba(255,255,255,10);border-radius:12px;"
        )
        row.addWidget(status)

        edit = QPushButton(tr("Edit"))
        edit.setIcon(icon("edit", tokens.TEXT2, 16))
        edit.clicked.connect(self._edit_student)
        row.addWidget(edit)

        lesson = QPushButton(tr("Schedule Lesson"))
        lesson.setObjectName("primary")
        lesson.setIcon(icon("calendar_add", "#111111", 17))
        lesson.clicked.connect(lambda: self._emit_and_close("schedule_lesson", self.student_id))
        row.addWidget(lesson)
        self.layout.addLayout(row)

    def _metric(self, icon_name: str, title: str, value: str, detail: str) -> Card:
        card = Card()
        card.setMinimumHeight(112)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        head = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(icon(icon_name, tokens.ACCENT, 18).pixmap(18, 18))
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        head.addWidget(icon_label)
        head.addWidget(title_label)
        head.addStretch()
        layout.addLayout(head)
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size:24px;font-weight:650;")
        layout.addWidget(value_label)
        detail_label = QLabel(detail)
        detail_label.setObjectName("muted")
        layout.addWidget(detail_label)
        return card

    def _build_metrics(self, data: dict[str, Any]) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        rate = data["attendance_rate"]
        attendance_value = f"{rate}%" if rate is not None else "—"
        attendance_detail = (
            f"{data['attendance']['Present']} {tr('present')} · {data['attendance']['Late']} {tr('late')}"
            if rate is not None
            else tr("No marked attendance yet")
        )
        cards = [
            self._metric("calendar", tr("Lessons"), str(data["lessons_total"]), f"{data['completed_lessons']} {tr('completed')}"),
            self._metric("clock", tr("Teaching time"), self._hours(data["teaching_minutes"]), tr("Completed lessons")),
            self._metric("circle_check", tr("Attendance"), attendance_value, attendance_detail),
            self._metric("arrow_right", tr("Upcoming"), str(data["upcoming_count"]), tr("Scheduled ahead")),
        ]
        for column, card in enumerate(cards):
            grid.addWidget(card, 0, column)
            grid.setColumnStretch(column, 1)
        self.layout.addLayout(grid)

    def _build_content(self, data: dict[str, Any]) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        history = Card()
        history_layout = QVBoxLayout(history)
        history_layout.setContentsMargins(18, 16, 18, 16)
        history_layout.setSpacing(7)
        h = QHBoxLayout()
        title = QLabel(tr("Lesson history"))
        title.setObjectName("sectionTitle")
        h.addWidget(title)
        h.addStretch()
        hint = QLabel(tr("Mark attendance directly here"))
        hint.setObjectName("muted")
        h.addWidget(hint)
        history_layout.addLayout(h)

        sessions = data["recent_sessions"]
        if not sessions:
            empty = QLabel(tr("No lessons with this student yet."))
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignCenter)
            empty.setMinimumHeight(180)
            history_layout.addWidget(empty)
        else:
            for index, session in enumerate(sessions):
                history_layout.addWidget(self._session_row(session))
                if index < len(sessions) - 1:
                    separator = QFrame()
                    separator.setObjectName("hairline")
                    history_layout.addWidget(separator)
        history_layout.addStretch()
        grid.addWidget(history, 0, 0, 2, 1)

        next_card = Card()
        next_layout = QVBoxLayout(next_card)
        next_layout.setContentsMargins(18, 16, 18, 16)
        next_layout.setSpacing(8)
        next_title = QLabel(tr("Next lesson"))
        next_title.setObjectName("sectionTitle")
        next_layout.addWidget(next_title)
        upcoming = data.get("next_session")
        if upcoming:
            subject = QLabel(upcoming.get("subject") or tr("Lesson"))
            subject.setStyleSheet("font-size:18px;font-weight:650;")
            next_layout.addWidget(subject)
            when = QLabel(self._format_next(upcoming))
            when.setObjectName("secondary")
            next_layout.addWidget(when)
            if upcoming.get("location"):
                loc = QLabel(upcoming["location"])
                loc.setObjectName("muted")
                next_layout.addWidget(loc)
            open_button = QPushButton(tr("Open lesson"))
            open_button.setIcon(icon("arrow_right", tokens.ACCENT, 15))
            open_button.clicked.connect(
                lambda _=False, sid=int(upcoming["id"]): self._emit_and_close("session", sid)
            )
            next_layout.addWidget(open_button, 0, Qt.AlignLeft)
        else:
            empty = QLabel(tr("Nothing scheduled yet."))
            empty.setObjectName("muted")
            next_layout.addWidget(empty)
            add = QPushButton(tr("Schedule a lesson"))
            add.clicked.connect(lambda: self._emit_and_close("schedule_lesson", self.student_id))
            next_layout.addWidget(add, 0, Qt.AlignLeft)
        next_layout.addStretch()
        grid.addWidget(next_card, 0, 1)

        linked = Card()
        linked_layout = QVBoxLayout(linked)
        linked_layout.setContentsMargins(18, 16, 18, 16)
        linked_layout.setSpacing(10)
        linked_title = QLabel(tr("Linked work"))
        linked_title.setObjectName("sectionTitle")
        linked_layout.addWidget(linked_title)
        self._linked_row(linked_layout, "note", tr("Notes"), data["notes_count"])
        self._linked_row(linked_layout, "folder", tr("Materials"), data["materials_count"])
        self._linked_row(linked_layout, "task", tr("Open tasks"), data["open_tasks"])
        self._linked_row(linked_layout, "check", tr("Open homework"), data.get("open_assignments", 0))
        add_note = QPushButton(tr("New note for this student"))
        add_note.clicked.connect(lambda: self._emit_and_close("add_note", self.student_id))
        add_homework = QPushButton(tr("Assign Homework"))
        add_homework.setIcon(icon("task", tokens.ACCENT, 15))
        add_homework.clicked.connect(lambda: self._emit_and_close("add_assignment", {"student_id": self.student_id}))
        linked_layout.addWidget(add_note)
        linked_layout.addWidget(add_homework)
        linked_layout.addStretch()
        grid.addWidget(linked, 1, 1)

        assignments = data.get("recent_assignments") or []
        homework_card = Card()
        homework_layout = QVBoxLayout(homework_card)
        homework_layout.setContentsMargins(18,16,18,16); homework_layout.setSpacing(8)
        hh = QHBoxLayout(); ht = QLabel(tr("Homework")); ht.setObjectName("sectionTitle"); hh.addWidget(ht); hh.addStretch()
        open_all = QPushButton(tr("View all")); open_all.setObjectName("ghost"); open_all.clicked.connect(lambda: self._emit_and_close("assignments", self.student_id)); hh.addWidget(open_all); homework_layout.addLayout(hh)
        if not assignments:
            empty = QLabel(tr("No homework assigned yet.")); empty.setObjectName("muted"); homework_layout.addWidget(empty)
        else:
            for index, assignment in enumerate(assignments):
                row = QHBoxLayout(); row.setSpacing(9)
                state = QLabel("●")
                state_color = tokens.SUCCESS if assignment.get("status") == "Completed" else tokens.ACCENT
                state.setStyleSheet(f"color:{state_color};font-size:9px;")
                text = QVBoxLayout(); text.setSpacing(1)
                title = QLabel(assignment.get("title") or tr("Homework")); title.setStyleSheet("font-weight:600;")
                meta = QLabel(f"{format_date(assignment.get('due_date'), compact=True) if assignment.get('due_date') else '—'} · {enum_display(assignment.get('status') or 'Assigned')}")
                meta.setObjectName("muted"); text.addWidget(title); text.addWidget(meta)
                open_button = QPushButton(); open_button.setIcon(icon("arrow_right", tokens.TEXT2, 14)); open_button.setFixedSize(32,32)
                open_button.clicked.connect(lambda _=False, aid=int(assignment["id"]): self._emit_and_close("assignment", aid))
                row.addWidget(state); row.addLayout(text,1); row.addWidget(open_button); homework_layout.addLayout(row)
                if index < len(assignments)-1:
                    sep=QFrame();sep.setObjectName("hairline");homework_layout.addWidget(sep)
        grid.addWidget(homework_card, 2, 0, 1, 2)

        student_notes = (data["student"].get("notes") or "").strip()
        if student_notes:
            note_card = Card()
            nl = QVBoxLayout(note_card)
            nl.setContentsMargins(18, 16, 18, 16)
            nl.setSpacing(7)
            t = QLabel(tr("Student notes"))
            t.setObjectName("sectionTitle")
            nl.addWidget(t)
            text = QLabel(student_notes)
            text.setWordWrap(True)
            text.setObjectName("secondary")
            nl.addWidget(text)
            grid.addWidget(note_card, 3, 0, 1, 2)

        grid.setColumnStretch(0, 7)
        grid.setColumnStretch(1, 4)
        self.layout.addLayout(grid)

    def _session_row(self, session: dict[str, Any]) -> QWidget:
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(2, 5, 2, 5)
        row.setSpacing(10)

        date_label = QLabel(self._short_date(session.get("session_date") or ""))
        date_label.setFixedWidth(76)
        date_label.setObjectName("muted")
        row.addWidget(date_label)

        text = QVBoxLayout()
        text.setSpacing(2)
        subject = QLabel(session.get("subject") or tr("Lesson"))
        subject.setStyleSheet("font-weight:600;")
        meta = QLabel(
            f"{format_time(session.get('start_time'))}–{format_time(session.get('end_time'))}  ·  {enum_display(session.get('status') or 'Upcoming')}"
        )
        meta.setObjectName("muted")
        text.addWidget(subject)
        text.addWidget(meta)
        row.addLayout(text, 1)

        attendance = QComboBox()
        attendance.setMinimumWidth(132)
        for value in ATTENDANCE_VALUES: attendance.addItem(enum_display(value), value)
        attendance.setCurrentIndex(max(0, attendance.findData(session.get("attendance") or "Not marked")))
        attendance.setProperty("session_id", int(session["id"]))
        attendance.currentIndexChanged.connect(
            lambda _index, combo=attendance: self._attendance_changed(int(combo.property("session_id")), str(combo.currentData()))
        )
        row.addWidget(attendance)

        open_button = QPushButton()
        open_button.setIcon(icon("arrow_right", tokens.TEXT2, 15))
        open_button.setIconSize(QSize(15, 15))
        open_button.setFixedSize(34, 34)
        open_button.setToolTip(tr("Open lesson"))
        open_button.clicked.connect(
            lambda _=False, sid=int(session["id"]): self._emit_and_close("session", sid)
        )
        row.addWidget(open_button)
        return wrap

    def _attendance_changed(self, session_id: int, value: str) -> None:
        try:
            self.service.update_attendance(session_id, value)
            self.changed.emit()
        except Exception as exc:
            QMessageBox.warning(self, tr("Attendance not saved"), str(exc))
            self.refresh()

    @staticmethod
    def _linked_row(layout: QVBoxLayout, icon_name: str, title: str, value: int) -> None:
        row = QHBoxLayout()
        img = QLabel()
        img.setPixmap(icon(icon_name, tokens.TEXT2, 17).pixmap(17, 17))
        label = QLabel(title)
        label.setObjectName("secondary")
        count = QLabel(str(value))
        count.setStyleSheet("font-weight:650;")
        row.addWidget(img)
        row.addWidget(label)
        row.addStretch()
        row.addWidget(count)
        layout.addLayout(row)

    @staticmethod
    def _short_date(value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
            return format_date(parsed, compact=True)
        except ValueError:
            return value

    @staticmethod
    def _format_next(session: dict[str, Any]) -> str:
        try:
            parsed = date.fromisoformat(session["session_date"])
            day = format_date(parsed, compact=True)
            return f"{day} · {format_time(session.get('start_time'))}–{format_time(session.get('end_time'))}"
        except (KeyError, ValueError):
            return f"{session.get('session_date') or ''} · {format_time(session.get('start_time'))}"

    def _edit_student(self) -> None:
        from .dialogs import StudentDialog

        student = self.service.student(self.student_id)
        if not student:
            return
        dialog = StudentDialog(self.service, student, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.service.save_student(dialog.data(), self.student_id)
                self.changed.emit()
                self.refresh()
            except Exception as exc:
                QMessageBox.critical(self, tr("Student not saved"), str(exc))

    def _emit_and_close(self, action: str, payload: object) -> None:
        self.accept()
        QTimer.singleShot(0, lambda: self.action_requested.emit(action, payload))

    def _build_footer(self) -> None:
        row = QHBoxLayout()
        row.addStretch()
        close = QPushButton(tr("Close"))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        self.layout.addLayout(row)