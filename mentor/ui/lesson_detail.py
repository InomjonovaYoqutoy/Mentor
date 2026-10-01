from __future__ import annotations

from datetime import date
from typing import Any

from PySide6.QtCore import QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
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
    QVBoxLayout,
    QWidget,
)

from ..services.data_service import DataService
from ..theme import tokens
from ..i18n import tr, enum_display, format_date, format_time
from .icons import icon
from .widgets import Card


class LessonDetailDialog(QDialog):
    """A single lesson workspace used instead of immediately opening an editor.

    The sheet intentionally separates viewing from editing. The teacher can scan
    the lesson, mark attendance, open the learner, create homework, or start the
    completion flow without being dropped into a large form first.
    """

    action_requested = Signal(str, object)
    changed = Signal()

    def __init__(self, service: DataService, session_id: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.service = service
        self.session_id = int(session_id)
        self.setWindowTitle(tr("Lesson Details"))
        self.setModal(True)
        self.setMinimumSize(780, 650)
        self.resize(900, 720)
        self.setStyleSheet(f"QDialog{{background:{tokens.BG2};}}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        root.addWidget(self.scroll)
        self.refresh()

    @staticmethod
    def _clear(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                LessonDetailDialog._clear(item.layout())

    @staticmethod
    def _pretty_date(value: str) -> str:
        try:
            parsed = date.fromisoformat(value)
            return format_date(parsed)
        except ValueError:
            return value

    @staticmethod
    def _status_style(status: str, needs_review: bool = False) -> tuple[str, str]:
        if needs_review:
            return tokens.WARNING, "#281F12"
        return {
            "Completed": (tokens.SUCCESS, "#10231A"),
            "In Progress": (tokens.ACCENT, "#2A1A0F"),
            "Cancelled": (tokens.ERROR, "#281313"),
        }.get(status, (tokens.TEXT2, "#1B1B1E"))

    def refresh(self) -> None:
        session = self.service.session(self.session_id)
        if not session:
            QMessageBox.warning(self, tr("Lesson unavailable"), tr("This lesson no longer exists."))
            self.reject()
            return
        self.session = session

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 25, 28, 26)
        layout.setSpacing(15)
        self.scroll.setWidget(body)

        self._build_header(layout, session)
        self._build_summary(layout, session)
        self._build_work(layout, session)
        layout.addStretch()
        self._build_footer(layout, session)

    def _build_header(self, layout: QVBoxLayout, session: dict[str, Any]) -> None:
        row = QHBoxLayout(); row.setSpacing(12)
        leading = QLabel(); leading.setPixmap(icon("calendar", tokens.ACCENT, 23).pixmap(23, 23))
        leading.setFixedSize(44,44); leading.setAlignment(Qt.AlignCenter)
        leading.setStyleSheet(f"background:{tokens.ACCENT_SOFT};border:1px solid {tokens.ACCENT_DARK};border-radius:22px;")
        row.addWidget(leading)

        text = QVBoxLayout(); text.setSpacing(2)
        title = QLabel(session.get("subject") or tr("Lesson")); title.setStyleSheet("font-size:25px;font-weight:650;")
        student = session.get("student_name") or tr("Unassigned")
        subtitle = QLabel(f"{student}  ·  {self._pretty_date(session.get('session_date') or '')}  ·  {format_time(session.get('start_time'))}–{format_time(session.get('end_time'))}")
        subtitle.setObjectName("secondary")
        text.addWidget(title); text.addWidget(subtitle); row.addLayout(text,1)

        status_text = tr("Needs review") if session.get("needs_review") else enum_display(session.get("status") or "Upcoming")
        fg,bg = self._status_style(session.get("status") or "Upcoming", bool(session.get("needs_review")))
        status = QLabel(status_text); status.setContentsMargins(11,6,11,6); status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet(f"color:{fg};background:{bg};border:1px solid rgba(255,255,255,10);border-radius:12px;font-weight:600;")
        row.addWidget(status)

        edit = QPushButton(tr("Edit")); edit.setIcon(icon("edit",tokens.TEXT2,15)); edit.clicked.connect(lambda: self._defer("edit_session", self.session_id))
        row.addWidget(edit)
        layout.addLayout(row)

    def _build_summary(self, layout: QVBoxLayout, session: dict[str, Any]) -> None:
        grid = QGridLayout(); grid.setHorizontalSpacing(12); grid.setVerticalSpacing(12)

        overview = Card(); ol=QVBoxLayout(overview); ol.setContentsMargins(18,16,18,16); ol.setSpacing(10)
        heading=QLabel(tr("Lesson")); heading.setObjectName("sectionTitle"); ol.addWidget(heading)
        details = [
            (tr("Type"), enum_display(session.get("session_type") or "Lesson")),
            (tr("Location"), session.get("location") or "—"),
            (tr("Repeat"), enum_display(session.get("recurrence") or "None")),
            (tr("Reminder"), tr("Off") if not session.get("reminder_minutes") else f"{session.get('reminder_minutes')} min"),
        ]
        for label,value in details:
            row=QHBoxLayout(); a=QLabel(label);a.setObjectName("muted");b=QLabel(str(value));b.setObjectName("secondary");row.addWidget(a);row.addStretch();row.addWidget(b);ol.addLayout(row)
        if session.get("meeting_link"):
            open_link=QPushButton(tr("Open meeting link"));open_link.setIcon(icon("link",tokens.ACCENT,15));open_link.clicked.connect(self._open_meeting);ol.addWidget(open_link,0,Qt.AlignLeft)
        grid.addWidget(overview,0,0)

        attendance = Card(); al=QVBoxLayout(attendance);al.setContentsMargins(18,16,18,16);al.setSpacing(10)
        ah=QHBoxLayout(); at=QLabel(tr("Attendance"));at.setObjectName("sectionTitle");ah.addWidget(at);ah.addStretch();al.addLayout(ah)
        combo=QComboBox();
        for value in ["Not marked","Present","Late","Absent","Excused"]: combo.addItem(enum_display(value), value)
        combo.setCurrentIndex(max(0, combo.findData(session.get("attendance") or "Not marked")))
        combo.setEnabled(session.get("student_id") is not None and session.get("status") != "Cancelled")
        combo.currentIndexChanged.connect(lambda _index: self._attendance_changed(str(combo.currentData())));al.addWidget(combo)
        hint=QLabel(tr("Saved immediately") if combo.isEnabled() else tr("Assign a student to track attendance"));hint.setObjectName("muted");al.addWidget(hint)
        if session.get("student_id") is not None:
            profile=QPushButton(tr("Open student profile"));profile.setIcon(icon("user",tokens.TEXT2,15));profile.clicked.connect(lambda: self._defer("student_profile", int(session["student_id"])));al.addWidget(profile,0,Qt.AlignLeft)
        al.addStretch();grid.addWidget(attendance,0,1)
        grid.setColumnStretch(0,3);grid.setColumnStretch(1,2)
        layout.addLayout(grid)

    def _build_work(self, layout: QVBoxLayout, session: dict[str, Any]) -> None:
        notes = Card(); nl=QVBoxLayout(notes);nl.setContentsMargins(18,16,18,16);nl.setSpacing(8)
        h=QHBoxLayout();title=QLabel(tr("Lesson notes"));title.setObjectName("sectionTitle");h.addWidget(title);h.addStretch();nl.addLayout(h)
        note_text=(session.get("notes") or "").strip()
        text=QLabel(note_text if note_text else tr("No lesson notes yet."));text.setWordWrap(True);text.setObjectName("secondary" if note_text else "muted");text.setMinimumHeight(54);nl.addWidget(text)
        layout.addWidget(notes)

        homework = Card(); hl=QVBoxLayout(homework);hl.setContentsMargins(18,16,18,16);hl.setSpacing(8)
        top=QHBoxLayout();ico=QLabel();ico.setPixmap(icon("task",tokens.ACCENT,18).pixmap(18,18));title=QLabel(tr("Homework from this lesson"));title.setObjectName("sectionTitle")
        add=QPushButton(tr("Assign Homework"));add.setIcon(icon("plus",tokens.ACCENT,14));add.clicked.connect(lambda: self._defer("add_assignment", {"session_id":self.session_id,"student_id":session.get("student_id")}))
        top.addWidget(ico);top.addWidget(title);top.addStretch();top.addWidget(add);hl.addLayout(top)

        assignments=self.service.assignments(session_id=self.session_id)
        if not assignments:
            empty=QLabel(tr("Nothing assigned from this lesson yet."));empty.setObjectName("muted");empty.setContentsMargins(2,10,2,10);hl.addWidget(empty)
        else:
            for index, assignment in enumerate(assignments[:6]):
                row=QHBoxLayout();row.setSpacing(9)
                state=QLabel("●"); state.setStyleSheet(f"color:{tokens.ERROR if assignment.get('overdue') else tokens.SUCCESS if assignment.get('status')=='Completed' else tokens.ACCENT};")
                texts=QVBoxLayout();texts.setSpacing(1);name=QLabel(assignment["title"]);name.setStyleSheet("font-weight:600;")
                due=format_date(assignment.get("due_date"), compact=True) if assignment.get("due_date") else "—";meta=QLabel(f"{due} · {enum_display(assignment.get('status') or 'Assigned')}");meta.setObjectName("muted");texts.addWidget(name);texts.addWidget(meta)
                open_button=QPushButton();open_button.setIcon(icon("arrow_right",tokens.TEXT2,14));open_button.setFixedSize(32,32);open_button.clicked.connect(lambda _=False, aid=int(assignment["id"]):self._defer("assignment",aid))
                row.addWidget(state);row.addLayout(texts,1);row.addWidget(open_button);hl.addLayout(row)
                if index < min(6,len(assignments))-1:
                    line=QFrame();line.setObjectName("hairline");hl.addWidget(line)
        layout.addWidget(homework)

    def _build_footer(self, layout: QVBoxLayout, session: dict[str, Any]) -> None:
        row=QHBoxLayout();row.setSpacing(8)
        duplicate=QPushButton(tr("Duplicate"));duplicate.clicked.connect(lambda:self._defer("duplicate_session",self.session_id));row.addWidget(duplicate)
        cancel=QPushButton(tr("Cancel Lesson"));cancel.clicked.connect(lambda:self._defer("cancel_session",self.session_id));row.addWidget(cancel)
        delete=QPushButton(tr("Delete"));delete.setObjectName("danger");delete.clicked.connect(lambda:self._defer("delete_session",self.session_id));row.addWidget(delete)
        row.addStretch()
        close=QPushButton(tr("Close"));close.clicked.connect(self.accept);row.addWidget(close)
        if session.get("status") != "Cancelled":
            if session.get("status") == "Completed":
                wrap=QPushButton(tr("Review Completion"));wrap.setObjectName("primary")
            else:
                wrap=QPushButton(tr("Complete Lesson"));wrap.setObjectName("primary");wrap.setIcon(icon("check","#111111",15))
            wrap.clicked.connect(lambda:self._defer("wrap_up",self.session_id));row.addWidget(wrap)
        layout.addLayout(row)

    def _attendance_changed(self, value: str) -> None:
        try:
            self.service.update_attendance(self.session_id, value)
            self.changed.emit()
        except Exception as exc:
            QMessageBox.warning(self,tr("Attendance not saved"),str(exc))

    def _open_meeting(self) -> None:
        link=(self.session.get("meeting_link") or "").strip()
        if link:
            QDesktopServices.openUrl(QUrl.fromUserInput(link))

    def _defer(self, action: str, payload: object) -> None:
        self.accept()
        QTimer.singleShot(0, lambda: self.action_requested.emit(action,payload))