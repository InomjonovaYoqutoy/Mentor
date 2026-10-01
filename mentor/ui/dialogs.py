from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, QTime, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QSpinBox, QTableWidget,
    QTableWidgetItem, QTextEdit, QTimeEdit, QVBoxLayout, QWidget
)

from ..services.data_service import DataService
from ..theme import tokens
from ..i18n import tr, enum_display, enum_canonical, format_date, format_time
from .icons import icon


def add_enum_items(combo: QComboBox, values: list[str]) -> None:
    for value in values:
        combo.addItem(enum_display(value), value)


def set_enum_value(combo: QComboBox, value: str) -> None:
    index = combo.findData(value)
    combo.setCurrentIndex(index if index >= 0 else 0)


class BaseDialog(QDialog):
    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setStyleSheet(f"QDialog{{background:{tokens.BG2};}}")

    @staticmethod
    def add_header(layout: QVBoxLayout, title: str, subtitle: str = "") -> None:
        label = QLabel(title); label.setObjectName("dialogTitle")
        layout.addWidget(label)
        if subtitle:
            sub = QLabel(subtitle); sub.setObjectName("dialogSubtitle"); sub.setWordWrap(True)
            layout.addWidget(sub)

    def buttons(self, save_text: str = "Save") -> QDialogButtonBox:
        box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        box.rejected.connect(self.reject)
        box.accepted.connect(self.accept)
        save = box.button(QDialogButtonBox.Save)
        save.setObjectName("primary")
        save.setText(tr(save_text))
        return box


class StudentDialog(BaseDialog):
    def __init__(self, service: DataService, student: dict[str, Any] | None = None, parent=None):
        super().__init__(tr("Edit Student") if student else tr("Add Student"), parent)
        self.service, self.student = service, student
        root = QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        self.add_header(root, tr("Edit student") if student else tr("New student"), tr("Keep only the details that are actually useful to you."))
        form = QFormLayout(); form.setSpacing(11)
        self.name = QLineEdit(); self.name.setPlaceholderText(tr("Student name"))
        self.age = QSpinBox(); self.age.setRange(0,120); self.age.setSpecialValueText(tr("Optional"))
        self.grade = QLineEdit(); self.grade.setPlaceholderText(tr("e.g. Grade 10"))
        self.subject = QLineEdit(); self.subject.setPlaceholderText(tr("Primary subject"))
        self.contact = QLineEdit(); self.contact.setPlaceholderText(tr("Phone, Telegram, email…"))
        self.status = QComboBox(); add_enum_items(self.status,["Active","Inactive","Archived"])
        self.notes = QTextEdit(); self.notes.setFixedHeight(90); self.notes.setPlaceholderText(tr("Optional student notes"))
        for label, widget in [("Full name",self.name),("Age",self.age),("Class / grade",self.grade),("Subject",self.subject),("Contact",self.contact),("Status",self.status),("Notes",self.notes)]:
            form.addRow(tr(label), widget)
        root.addLayout(form); root.addWidget(self.buttons("Save Student" if student else "Add Student"))
        if student:
            self.name.setText(student.get("name") or ""); self.age.setValue(student.get("age") or 0)
            self.grade.setText(student.get("grade") or ""); self.subject.setText(student.get("subject") or "")
            self.contact.setText(student.get("contact") or ""); self.notes.setPlainText(student.get("notes") or "")
            set_enum_value(self.status, student.get("status") or "Active")

    def data(self) -> dict[str, Any]:
        return {"name":self.name.text(),"age":self.age.value() or None,"grade":self.grade.text(),"subject":self.subject.text(),"contact":self.contact.text(),"notes":self.notes.toPlainText(),"status":str(self.status.currentData() or "Active")}

    def accept(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(self,tr("Missing name"),tr("Student name is required.")); return
        super().accept()


class SessionDialog(BaseDialog):
    """Lesson editor with quick duration presets and reliable validation."""

    def __init__(
        self,
        service: DataService,
        session: dict[str, Any] | None = None,
        default_date: date | None = None,
        default_time: str | None = None,
        default_student_id: int | None = None,
        parent=None,
    ):
        super().__init__(tr("Edit Lesson") if session else tr("Schedule Lesson"), parent)
        self.service, self.session = service, session
        self.setMinimumSize(780, 600)
        self.resize(820, 640)
        self._updating_time = False
        self._preferred_duration = 60
        root = QVBoxLayout(self); root.setContentsMargins(28,25,28,25); root.setSpacing(16)
        self.add_header(
            root,
            tr("Edit lesson") if session else tr("Schedule a lesson"),
            tr("Choose who, when, and where. Mentor will warn you about overlaps before saving."),
        )

        template_bar = QFrame(); template_bar.setObjectName("section")
        template_row = QHBoxLayout(template_bar); template_row.setContentsMargins(14,10,14,10); template_row.setSpacing(9)
        template_icon = QLabel(); template_icon.setPixmap(icon("sparkles", tokens.ACCENT, 17).pixmap(17,17))
        template_label = QLabel(tr("Lesson template")); template_label.setObjectName("secondary")
        self.template_combo = QComboBox(); self.template_combo.setMinimumWidth(210)
        self.template_combo.addItem(tr("Start fresh"), None)
        for template in service.lesson_templates():
            self.template_combo.addItem(template["name"], template["id"])
        self.template_combo.currentIndexChanged.connect(self._template_selected)
        save_template = QPushButton(tr("Save current as template"))
        save_template.setObjectName("ghost")
        save_template.clicked.connect(self._save_template)
        template_row.addWidget(template_icon); template_row.addWidget(template_label); template_row.addWidget(self.template_combo,1); template_row.addWidget(save_template)
        root.addWidget(template_bar)

        content = QHBoxLayout(); content.setSpacing(12)
        left = QVBoxLayout(); left.setSpacing(12)
        right = QVBoxLayout(); right.setSpacing(12)
        content.addLayout(left, 1); content.addLayout(right, 1)
        root.addLayout(content)

        basics = QFrame(); basics.setObjectName("section")
        form = QFormLayout(basics); form.setContentsMargins(16,16,16,16); form.setSpacing(11)
        self.subject = QComboBox(); self.subject.setEditable(True); self.subject.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.subject.lineEdit().setPlaceholderText("Math, Physics, IELTS…")
        for subject in service.recent_subjects():
            self.subject.addItem(subject)
        # Suggestions should not silently become the lesson subject. Start empty
        # so validation and student-subject autofill behave predictably.
        self.subject.setCurrentIndex(-1)
        self.subject.setEditText("")
        self.student = QComboBox(); self.student.addItem(tr("Unassigned"), None)
        for student in service.students(active_only=True):
            self.student.addItem(student["name"], student["id"])
        self.student.currentIndexChanged.connect(self._student_changed)
        if default_student_id is not None and not session:
            default_index = self.student.findData(default_student_id)
            if default_index >= 0:
                self.student.setCurrentIndex(default_index)
        self.session_type = QComboBox(); add_enum_items(self.session_type,["Lesson","Review","Consultation","Exam Prep","Assessment"])
        form.addRow(tr("Subject"), self.subject); form.addRow(tr("Student"), self.student); form.addRow(tr("Type"), self.session_type)
        left.addWidget(basics)

        timing = QFrame(); timing.setObjectName("section")
        tf = QFormLayout(timing); tf.setContentsMargins(16,16,16,16); tf.setSpacing(11)
        self.date = QDateEdit(); self.date.setCalendarPopup(True); self.date.setDisplayFormat("ddd, MMM d, yyyy")
        d = default_date or date.today(); self.date.setDate(QDate(d.year,d.month,d.day))
        start_qtime = QTime.fromString(default_time or "09:00", "HH:mm")
        if not start_qtime.isValid(): start_qtime = QTime(9,0)
        self.start = QTimeEdit(start_qtime); self.end = QTimeEdit(start_qtime.addSecs(3600))
        time_display = "HH:mm" if service.get_setting("time_24h","1") != "0" else "h:mm AP"
        self.start.setDisplayFormat(time_display); self.end.setDisplayFormat(time_display)
        self.start.timeChanged.connect(self._start_changed); self.end.timeChanged.connect(self._end_changed)

        duration_wrap = QWidget(); dl = QHBoxLayout(duration_wrap); dl.setContentsMargins(0,0,0,0); dl.setSpacing(6)
        self.duration_buttons: dict[int, QPushButton] = {}
        for minutes in (30,45,60,90):
            b = QPushButton(f"{minutes}m"); b.setObjectName("pill"); b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, m=minutes: self._set_duration(m)); dl.addWidget(b); self.duration_buttons[minutes] = b
        self.duration_label = QLabel("1h"); self.duration_label.setObjectName("secondary"); dl.addStretch(); dl.addWidget(self.duration_label)

        tf.addRow(tr("Date"), self.date); tf.addRow(tr("Start"), self.start); tf.addRow(tr("End"), self.end); tf.addRow(tr("Length"), duration_wrap)
        left.addWidget(timing); left.addStretch()

        details = QFrame(); details.setObjectName("section")
        df = QFormLayout(details); df.setContentsMargins(16,16,16,16); df.setSpacing(11)
        self.status = QComboBox(); add_enum_items(self.status,["Upcoming","In Progress","Completed","Cancelled"])
        self.attendance = QComboBox(); add_enum_items(self.attendance,["Not marked","Present","Late","Absent","Excused"])
        self.attendance.setToolTip(tr("Attendance is only used when a student is assigned to this lesson."))
        self.location = QLineEdit(); self.location.setPlaceholderText(tr("Classroom, address, or Online"))
        self.meeting_link = QLineEdit(); self.meeting_link.setPlaceholderText(tr("Optional meeting link"))
        self.recurrence = QComboBox(); add_enum_items(self.recurrence,["None","Every day","Every week","Every 2 weeks"])
        self.repeat_count = QSpinBox(); self.repeat_count.setRange(2,52); self.repeat_count.setValue(8); self.repeat_count.setSuffix(" "+tr("occurrences"))
        self.recurrence.currentIndexChanged.connect(lambda _i: self.repeat_count.setEnabled(self.recurrence.currentData() != "None"))
        self.repeat_count.setEnabled(False)
        self.reminder = QComboBox()
        for label, minutes in [("Off",0),("5 minutes before",5),("10 minutes before",10),("15 minutes before",15),("30 minutes before",30),("1 hour before",60)]:
            self.reminder.addItem(tr(label), minutes)
        self.reminder.setCurrentIndex(self.reminder.findData(15))
        self.notes = QTextEdit(); self.notes.setFixedHeight(82); self.notes.setPlaceholderText(tr("Preparation notes, homework, lesson focus…"))
        for label, widget in [("Status",self.status),("Attendance",self.attendance),("Location",self.location),("Meeting link",self.meeting_link),("Repeat",self.recurrence),("Series",self.repeat_count),("Reminder",self.reminder),("Notes",self.notes)]:
            df.addRow(tr(label), widget)
        right.addWidget(details); right.addStretch()

        footer = QHBoxLayout(); footer.setSpacing(8)
        if session:
            duplicate = QPushButton(tr("Duplicate")); duplicate.clicked.connect(lambda:self.done(2))
            delete = QPushButton(tr("Delete")); delete.setObjectName("danger"); delete.clicked.connect(lambda:self.done(3))
            footer.addWidget(duplicate); footer.addWidget(delete)
        footer.addStretch()
        cancel = QPushButton(tr("Cancel")); cancel.clicked.connect(self.reject)
        save = QPushButton(tr("Save Changes") if session else tr("Schedule Lesson")); save.setObjectName("primary"); save.clicked.connect(self.accept)
        footer.addWidget(cancel); footer.addWidget(save); root.addLayout(footer)

        if session:
            self._load_session(session)
        else:
            self._set_duration(60)
        self._sync_attendance_enabled()
        self.subject.setFocus()

    def _template_selected(self, *_args) -> None:
        template_id = self.template_combo.currentData()
        if template_id is None:
            return
        template = self.service.lesson_template(int(template_id))
        if not template:
            return
        self.subject.setCurrentText(template.get("subject") or "")
        student_index = self.student.findData(template.get("student_id"))
        self.student.setCurrentIndex(student_index if student_index >= 0 else 0)
        set_enum_value(self.session_type, template.get("session_type") or "Lesson")
        self.location.setText(template.get("location") or "")
        self.meeting_link.setText(template.get("meeting_link") or "")
        reminder_index = self.reminder.findData(int(template.get("reminder_minutes") or 0))
        self.reminder.setCurrentIndex(reminder_index if reminder_index >= 0 else 0)
        set_enum_value(self.recurrence, template.get("recurrence") or "None")
        self.repeat_count.setValue(int(template.get("repeat_count") or 8))
        self._set_duration(int(template.get("duration_minutes") or 60))

    def _save_template(self) -> None:
        if not self.subject.currentText().strip():
            QMessageBox.warning(self, tr("Template needs a subject"), tr("Add a subject before saving this lesson as a template."))
            return
        dialog = TemplateNameDialog(self.subject.currentText().strip(), self)
        if dialog.exec() != QDialog.Accepted:
            return
        try:
            self.service.save_lesson_template({
                "name": dialog.name.text(),
                "student_id": self.student.currentData(),
                "subject": self.subject.currentText(),
                "duration_minutes": max(15, self._duration_minutes()),
                "session_type": str(self.session_type.currentData() or "Lesson"),
                "location": self.location.text(),
                "meeting_link": self.meeting_link.text(),
                "reminder_minutes": self.reminder.currentData() or 0,
                "recurrence": str(self.recurrence.currentData() or "None"),
                "repeat_count": self.repeat_count.value(),
            })
            self.template_combo.blockSignals(True)
            self.template_combo.clear(); self.template_combo.addItem(tr("Start fresh"), None)
            for template in self.service.lesson_templates():
                self.template_combo.addItem(template["name"], template["id"])
            self.template_combo.setCurrentIndex(0)
            self.template_combo.blockSignals(False)
        except Exception as exc:
            QMessageBox.warning(self, tr("Template not saved"), str(exc))

    def _load_session(self, session: dict[str, Any]) -> None:
        self.subject.setCurrentText(session.get("subject") or "")
        idx = self.student.findData(session.get("student_id")); self.student.setCurrentIndex(max(0,idx))
        qd = QDate.fromString(session.get("session_date") or "", "yyyy-MM-dd")
        if qd.isValid(): self.date.setDate(qd)
        st = QTime.fromString(session.get("start_time") or "09:00","HH:mm")
        en = QTime.fromString(session.get("end_time") or "10:00","HH:mm")
        if st.isValid(): self.start.setTime(st)
        if en.isValid(): self.end.setTime(en)
        set_enum_value(self.status, session.get("status") or "Upcoming")
        set_enum_value(self.attendance, session.get("attendance") or "Not marked")
        self.location.setText(session.get("location") or "")
        self.meeting_link.setText(session.get("meeting_link") or "")
        set_enum_value(self.recurrence, session.get("recurrence") or "None")
        set_enum_value(self.session_type, session.get("session_type") or "Lesson")
        idx = self.reminder.findData(int(session.get("reminder_minutes") or 0)); self.reminder.setCurrentIndex(idx if idx >= 0 else 0)
        self.notes.setPlainText(session.get("notes") or "")
        current_minutes = self._duration_minutes()
        if current_minutes > 0: self._preferred_duration = current_minutes
        self._refresh_duration_ui()

    def _student_changed(self, *_args) -> None:
        student_id = self.student.currentData()
        self._sync_attendance_enabled()
        if student_id is None or self.subject.currentText().strip():
            return
        student = self.service.student(int(student_id))
        if student and student.get("subject"):
            self.subject.setCurrentText(student["subject"])

    def _sync_attendance_enabled(self) -> None:
        has_student = self.student.currentData() is not None
        self.attendance.setEnabled(has_student)
        if not has_student:
            set_enum_value(self.attendance, "Not marked")

    def _set_duration(self, minutes: int) -> None:
        self._preferred_duration = minutes
        self._updating_time = True
        self.end.setTime(self.start.time().addSecs(minutes * 60))
        self._updating_time = False
        self._refresh_duration_ui()

    def _start_changed(self) -> None:
        if self._updating_time: return
        duration = self._preferred_duration if self._preferred_duration > 0 else 60
        self._updating_time = True; self.end.setTime(self.start.time().addSecs(duration*60)); self._updating_time = False
        self._refresh_duration_ui()

    def _end_changed(self) -> None:
        if not self._updating_time:
            minutes = self._duration_minutes()
            if minutes > 0: self._preferred_duration = minutes
            self._refresh_duration_ui()

    def _duration_minutes(self) -> int:
        return self.start.time().secsTo(self.end.time()) // 60

    def _refresh_duration_ui(self) -> None:
        minutes = self._duration_minutes()
        if minutes <= 0:
            self.duration_label.setText("Invalid")
        elif minutes < 60:
            self.duration_label.setText(f"{minutes} min")
        else:
            h, m = divmod(minutes,60); self.duration_label.setText(f"{h}h" + (f" {m}m" if m else ""))
        for value, button in self.duration_buttons.items():
            button.setObjectName("pillChecked" if value == minutes else "pill")
            button.style().unpolish(button); button.style().polish(button)

    def data(self) -> dict[str, Any]:
        return {
            "student_id": self.student.currentData(),
            "subject": self.subject.currentText(),
            "session_date": self.date.date().toString("yyyy-MM-dd"),
            "start_time": self.start.time().toString("HH:mm"),
            "end_time": self.end.time().toString("HH:mm"),
            "status": str(self.status.currentData() or "Upcoming"),
            "attendance": str(self.attendance.currentData() or "Not marked"),
            "location": self.location.text(),
            "meeting_link": self.meeting_link.text(),
            "notes": self.notes.toPlainText(),
            "recurrence": str(self.recurrence.currentData() or "None"),
            "repeat_count": self.repeat_count.value(),
            "session_type": str(self.session_type.currentData() or "Lesson"),
            "reminder_minutes": self.reminder.currentData() or 0,
            "color_tag": "orange",
            "series_id": self.session.get("series_id") if self.session else None,
        }

    def accept(self) -> None:
        data = self.data()
        if not data["subject"].strip():
            QMessageBox.warning(self,tr("Missing subject"),tr("Add a subject before scheduling the lesson.")); self.subject.setFocus(); return
        if data["end_time"] <= data["start_time"]:
            QMessageBox.warning(self,tr("Invalid time"),tr("End time must be later than start time.")); return
        conflicts = self.service.session_conflicts(
            data["session_date"], data["start_time"], data["end_time"],
            self.session.get("id") if self.session else None,
        )
        if conflicts:
            names = "\n".join(f"• {c['start_time']}–{c['end_time']}  {c['subject']}" for c in conflicts[:4])
            choice = QMessageBox.warning(
                self, tr("Schedule overlap"),
                f"This lesson overlaps with:\n\n{names}\n\nSchedule it anyway?",
                QMessageBox.Save | QMessageBox.Cancel, QMessageBox.Cancel,
            )
            if choice != QMessageBox.Save: return
        super().accept()


class FocusTimerDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(tr("Focus"), parent)
        self.setMinimumSize(410, 390)
        self._seconds = 25 * 60
        self._initial_seconds = self._seconds
        self._running = False
        self.timer = QTimer(self); self.timer.setInterval(1000); self.timer.timeout.connect(self._tick)
        root = QVBoxLayout(self); root.setContentsMargins(28,26,28,26); root.setSpacing(18)
        self.add_header(root, tr("Focus"), tr("A quiet timer for lesson prep, marking, or planning."))
        root.addStretch()
        self.time_label = QLabel("25:00"); self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("font-size:58px;font-weight:300;letter-spacing:-1px;")
        root.addWidget(self.time_label)
        self.state_label = QLabel(tr("Ready when you are")); self.state_label.setAlignment(Qt.AlignCenter); self.state_label.setObjectName("secondary")
        root.addWidget(self.state_label)
        presets = QHBoxLayout(); presets.setSpacing(7); presets.addStretch()
        for mins in (15,25,45,60):
            b=QPushButton(f"{mins}m"); b.setObjectName("pill"); b.clicked.connect(lambda _=False,m=mins:self.set_minutes(m)); presets.addWidget(b)
        presets.addStretch(); root.addLayout(presets)
        root.addStretch()
        controls=QHBoxLayout(); controls.addStretch()
        reset=QPushButton(tr("Reset")); reset.clicked.connect(self.reset)
        self.start_btn=QPushButton(tr("Start")); self.start_btn.setIcon(icon("play", "#111111", 17)); self.start_btn.setObjectName("primary"); self.start_btn.clicked.connect(self.toggle)
        close=QPushButton(tr("Close")); close.clicked.connect(self.accept)
        controls.addWidget(reset); controls.addWidget(self.start_btn); controls.addWidget(close); controls.addStretch(); root.addLayout(controls)

    def set_minutes(self, minutes: int) -> None:
        self.timer.stop(); self._running=False; self._seconds=minutes*60; self._initial_seconds=self._seconds
        self.start_btn.setText(tr("Start")); self.start_btn.setIcon(icon("play", "#111111",17)); self.state_label.setText(tr("Ready when you are")); self._render()

    def toggle(self) -> None:
        if self._seconds <= 0: self.reset()
        self._running = not self._running
        if self._running:
            self.timer.start(); self.start_btn.setText(tr("Pause")); self.start_btn.setIcon(icon("pause", "#111111",17)); self.state_label.setText(tr("Focus mode"))
        else:
            self.timer.stop(); self.start_btn.setText(tr("Resume")); self.start_btn.setIcon(icon("play", "#111111",17)); self.state_label.setText(tr("Paused"))

    def reset(self) -> None:
        self.timer.stop(); self._running=False; self._seconds=self._initial_seconds
        self.start_btn.setText(tr("Start")); self.start_btn.setIcon(icon("play", "#111111",17)); self.state_label.setText(tr("Ready when you are")); self._render()

    def _tick(self) -> None:
        self._seconds=max(0,self._seconds-1); self._render()
        if self._seconds == 0:
            self.timer.stop(); self._running=False; self.start_btn.setText(tr("Restart")); self.state_label.setText(tr("Focus complete"))

    def _render(self) -> None:
        mins, secs = divmod(self._seconds,60); self.time_label.setText(f"{mins:02d}:{secs:02d}")


class TaskDialog(BaseDialog):
    def __init__(self, service: DataService, task: dict | None = None, parent=None):
        super().__init__(tr("Edit Task") if task else tr("Create Task"), parent); self.service=service; self.task=task
        root=QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        self.add_header(root, tr("Edit task") if task else tr("New task"), tr("Keep the next action clear and lightweight."))
        form=QFormLayout(); form.setSpacing(11)
        self.title=QLineEdit(); self.title.setPlaceholderText(tr("What needs to be done?"))
        self.student=QComboBox(); self.student.addItem(tr("Unassigned"),None)
        for s in service.students(active_only=True): self.student.addItem(s["name"],s["id"])
        self.subject=QLineEdit(); self.due=QDateEdit(); self.due.setCalendarPopup(True); self.due.setDate(QDate.currentDate())
        self.priority=QComboBox(); add_enum_items(self.priority,["Low","Medium","High"]); self.completed=QCheckBox(tr("Completed"))
        self.description=QTextEdit(); self.description.setFixedHeight(90); self.description.setPlaceholderText(tr("Optional details"))
        for label,w in [("Title",self.title),("Student",self.student),("Subject",self.subject),("Due",self.due),("Priority",self.priority),("",self.completed),("Description",self.description)]: form.addRow(tr(label) if label else "",w)
        root.addLayout(form); root.addWidget(self.buttons("Save Task" if task else "Create Task"))
        if task:
            self.title.setText(task.get("title") or ""); self.subject.setText(task.get("subject") or "")
            idx=self.student.findData(task.get("student_id")); self.student.setCurrentIndex(max(0,idx))
            qd=QDate.fromString(task.get("due_date") or "","yyyy-MM-dd"); self.due.setDate(qd if qd.isValid() else QDate.currentDate())
            set_enum_value(self.priority, task.get("priority") or "Medium"); self.completed.setChecked(bool(task.get("completed"))); self.description.setPlainText(task.get("description") or "")

    def data(self):
        return {"title":self.title.text(),"student_id":self.student.currentData(),"session_id":None,"subject":self.subject.text(),"due_date":self.due.date().toString("yyyy-MM-dd"),"priority":str(self.priority.currentData() or "Medium"),"completed":self.completed.isChecked(),"description":self.description.toPlainText()}

    def accept(self):
        if not self.title.text().strip(): QMessageBox.warning(self,tr("Missing title"),tr("Task title is required.")); return
        super().accept()


class GoalDialog(BaseDialog):
    def __init__(self, goal: dict | None=None, parent=None):
        super().__init__(tr("Edit Goal") if goal else tr("Create Goal"),parent); self.goal=goal
        root=QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        self.add_header(root, tr("Edit goal") if goal else tr("New goal"), tr("Track a teaching target without turning Mentor into a project manager."))
        form=QFormLayout(); form.setSpacing(11)
        self.title=QLineEdit(); self.desc=QTextEdit(); self.desc.setFixedHeight(80)
        self.target=QDoubleSpinBox(); self.target.setRange(.01,1_000_000); self.target.setValue(20)
        self.progress=QDoubleSpinBox(); self.progress.setRange(0,1_000_000)
        self.deadline=QDateEdit(); self.deadline.setCalendarPopup(True); self.deadline.setDate(QDate.currentDate().addDays(30))
        self.status=QComboBox(); add_enum_items(self.status,["Active","Completed","Paused"])
        for label,w in [("Title",self.title),("Description",self.desc),("Target",self.target),("Progress",self.progress),("Deadline",self.deadline),("Status",self.status)]: form.addRow(tr(label),w)
        root.addLayout(form); root.addWidget(self.buttons("Save Goal" if goal else "Create Goal"))
        if goal:
            self.title.setText(goal.get("title") or ""); self.desc.setPlainText(goal.get("description") or "")
            self.target.setValue(float(goal.get("target") or 1)); self.progress.setValue(float(goal.get("progress") or 0))
            qd=QDate.fromString(goal.get("deadline") or "","yyyy-MM-dd"); self.deadline.setDate(qd if qd.isValid() else self.deadline.date())
            set_enum_value(self.status, goal.get("status") or "Active")

    def data(self):
        return {"title":self.title.text(),"description":self.desc.toPlainText(),"target":self.target.value(),"progress":self.progress.value(),"deadline":self.deadline.date().toString("yyyy-MM-dd"),"status":str(self.status.currentData() or "Active")}


class MaterialDialog(BaseDialog):
    def __init__(self, service: DataService, path: str = "", material: dict | None=None, parent=None):
        super().__init__(tr("Edit Material") if material else tr("Add Material"),parent); self.service=service; self.material=material
        root=QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        self.add_header(root, tr("Edit material") if material else tr("Add teaching material"), tr("Mentor stores the reference to your file, not another heavy copy."))
        form=QFormLayout(); form.setSpacing(11)
        self.name=QLineEdit(); self.path=QLineEdit(path); browse=QPushButton(tr("Browse…")); browse.clicked.connect(self.browse)
        pwrap=QWidget(); pl=QHBoxLayout(pwrap); pl.setContentsMargins(0,0,0,0); pl.addWidget(self.path,1); pl.addWidget(browse)
        self.category=QComboBox();
        for value in ["General","Math","Physics","English","Computer Science","Other"]: self.category.addItem(tr(value), value)
        self.student=QComboBox(); self.student.addItem(tr("Unassigned"),None)
        for s in service.students(active_only=True): self.student.addItem(s["name"],s["id"])
        self.desc=QTextEdit(); self.desc.setFixedHeight(80)
        for label,w in [("Name",self.name),("File / URL",pwrap),("Category",self.category),("Student",self.student),("Description",self.desc)]: form.addRow(tr(label),w)
        root.addLayout(form); root.addWidget(self.buttons("Save Material" if material else "Add Material"))
        if path: self.name.setText(Path(path).stem)
        if material:
            self.name.setText(material.get("name") or ""); self.path.setText(material.get("path") or "")
            self.category.setCurrentIndex(max(0,self.category.findData(material.get("category") or "General")))
            idx=self.student.findData(material.get("student_id")); self.student.setCurrentIndex(max(0,idx)); self.desc.setPlainText(material.get("description") or "")

    def browse(self):
        p,_=QFileDialog.getOpenFileName(self,tr("Choose teaching material"))
        if p: self.path.setText(p); self.name.setText(self.name.text().strip() or Path(p).stem)

    def data(self):
        return {"student_id":self.student.currentData(),"name":self.name.text(),"path":self.path.text(),"category":str(self.category.currentData() or "General"),"description":self.desc.toPlainText()}


class StudentManager(BaseDialog):
    changed = Signal()
    action_requested = Signal(str, object)

    def __init__(self, service: DataService, parent=None):
        super().__init__(tr("Students"), parent)
        self.service = service
        self.setMinimumSize(860, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)
        self.add_header(root, tr("Students"), tr("Open a learner profile for lesson history, attendance, and linked work."))

        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Search students…"))
        self.search.textChanged.connect(self.refresh)
        self.summary = QLabel()
        self.summary.setObjectName("muted")
        add = QPushButton(tr("Add Student"))
        add.setObjectName("primary")
        add.clicked.connect(self.add)
        top.addWidget(self.search, 1)
        top.addWidget(self.summary)
        top.addWidget(add)
        root.addLayout(top)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr("Name"), tr("Grade"), tr("Subject"), tr("Contact"), tr("Status")])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.profile)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        profile = QPushButton(tr("Open Profile"))
        profile.setIcon(icon("user", tokens.ACCENT, 16))
        edit = QPushButton(tr("Edit"))
        delete = QPushButton(tr("Delete"))
        delete.setObjectName("danger")
        close = QPushButton(tr("Close"))
        profile.clicked.connect(self.profile)
        edit.clicked.connect(self.edit)
        delete.clicked.connect(self.delete)
        close.clicked.connect(self.accept)
        actions.addStretch()
        actions.addWidget(profile)
        actions.addWidget(edit)
        actions.addWidget(delete)
        actions.addWidget(close)
        root.addLayout(actions)
        self.refresh()

    def refresh(self):
        rows = self.service.students(self.search.text())
        self.table.setRowCount(len(rows))
        self.table.setProperty("rows", rows)
        self.summary.setText(tr("Learners count", count=len(rows)))
        for r, row in enumerate(rows):
            for c, key in enumerate(["name", "grade", "subject", "contact", "status"]):
                value = row.get(key) or ""
                if key == "status": value = enum_display(str(value))
                item = QTableWidgetItem(str(value))
                self.table.setItem(r, c, item)
            self.table.setRowHeight(r, 42)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def selected(self):
        r = self.table.currentRow()
        rows = self.table.property("rows") or []
        return rows[r] if 0 <= r < len(rows) else None

    def add(self):
        dialog = StudentDialog(self.service, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.service.save_student(dialog.data())
            self.refresh()
            self.changed.emit()

    def profile(self, *_):
        row = self.selected()
        if not row:
            return
        from .student_profile import StudentProfileDialog

        dialog = StudentProfileDialog(self.service, int(row["id"]), self)
        dialog.changed.connect(self._profile_changed)
        dialog.action_requested.connect(self._profile_action)
        dialog.exec()

    def _profile_changed(self) -> None:
        self.refresh()
        self.changed.emit()

    def _profile_action(self, action: str, payload: object) -> None:
        # Close the nested student windows before opening another editor.
        # Deferring the signal prevents stacked modal dialogs on Windows.
        self.accept()
        QTimer.singleShot(0, lambda: self.action_requested.emit(action, payload))

    def edit(self, *_):
        row = self.selected()
        if not row:
            return
        dialog = StudentDialog(self.service, row, self)
        if dialog.exec() == QDialog.Accepted:
            self.service.save_student(dialog.data(), row["id"])
            self.refresh()
            self.changed.emit()

    def delete(self):
        row = self.selected()
        if row and QMessageBox.question(
            self,
            tr("Delete student"),
            tr("Delete student confirmation", name=row["name"]),
        ) == QMessageBox.Yes:
            self.service.delete_student(row["id"])
            self.refresh()
            self.changed.emit()


class TaskManager(BaseDialog):
    changed=Signal()
    def __init__(self,service:DataService,parent=None):
        super().__init__(tr("Tasks"),parent); self.service=service; self.setMinimumSize(740,520)
        root=QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(14)
        self.add_header(root,tr("Tasks"),tr("Small actions that keep teaching work moving."))
        top=QHBoxLayout(); add=QPushButton(tr("Create Task")); add.setObjectName("primary"); add.clicked.connect(self.add); top.addStretch(); top.addWidget(add); root.addLayout(top)
        self.list=QListWidget(); self.list.itemDoubleClicked.connect(lambda _:self.edit()); root.addWidget(self.list,1)
        row=QHBoxLayout(); done=QPushButton(tr("Toggle complete")); edit=QPushButton(tr("Edit")); delete=QPushButton(tr("Delete")); delete.setObjectName("danger"); close=QPushButton(tr("Close"))
        done.clicked.connect(self.toggle); edit.clicked.connect(self.edit); delete.clicked.connect(self.delete); close.clicked.connect(self.accept); row.addStretch(); [row.addWidget(b) for b in (done,edit,delete,close)]; root.addLayout(row); self.refresh()

    def refresh(self):
        self.list.clear()
        for t in self.service.tasks():
            mark="✓ " if t["completed"] else "○ "; due=f" · {format_date(t['due_date'])}" if t.get("due_date") else ""
            item=QListWidgetItem(f"{mark}{t['title']}  —  {enum_display(t['priority'])}{due}"); item.setData(Qt.UserRole,t); self.list.addItem(item)

    def current(self): return self.list.currentItem().data(Qt.UserRole) if self.list.currentItem() else None
    def add(self):
        d=TaskDialog(self.service,parent=self)
        if d.exec()==QDialog.Accepted: self.service.save_task(d.data()); self.refresh(); self.changed.emit()
    def edit(self):
        t=self.current()
        if not t:return
        d=TaskDialog(self.service,t,self)
        if d.exec()==QDialog.Accepted: self.service.save_task(d.data(),t["id"]); self.refresh(); self.changed.emit()
    def toggle(self):
        t=self.current()
        if t:self.service.toggle_task(t["id"],not bool(t["completed"])); self.refresh(); self.changed.emit()
    def delete(self):
        t=self.current()
        if t and QMessageBox.question(self,tr("Delete task"),tr("Delete named item", name=t["title"]))==QMessageBox.Yes:self.service.delete_task(t["id"]);self.refresh();self.changed.emit()


class GoalManager(BaseDialog):
    changed=Signal()
    def __init__(self,service:DataService,parent=None):
        super().__init__(tr("Goals"),parent); self.service=service; self.setMinimumSize(720,500)
        root=QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(14)
        self.add_header(root,tr("Goals"),tr("Simple targets, visible progress."))
        top=QHBoxLayout(); add=QPushButton(tr("Create Goal")); add.setObjectName("primary"); add.clicked.connect(self.add); top.addStretch();top.addWidget(add);root.addLayout(top)
        self.list=QListWidget();self.list.itemDoubleClicked.connect(lambda _:self.edit());root.addWidget(self.list,1)
        row=QHBoxLayout();edit=QPushButton(tr("Edit"));delete=QPushButton(tr("Delete"));delete.setObjectName("danger");close=QPushButton(tr("Close"))
        edit.clicked.connect(self.edit);delete.clicked.connect(self.delete);close.clicked.connect(self.accept);row.addStretch();[row.addWidget(x) for x in(edit,delete,close)];root.addLayout(row);self.refresh()

    def refresh(self):
        self.list.clear()
        for g in self.service.goals():
            pct=min(100,round((g["progress"] or 0)/max(g["target"] or 1,.0001)*100));item=QListWidgetItem(f"{g['title']}  —  {pct}%  ·  {enum_display(g['status'])}  ·  {tr('Due')} {format_date(g.get('deadline')) if g.get('deadline') else '—'}");item.setData(Qt.UserRole,g);self.list.addItem(item)
    def current(self):return self.list.currentItem().data(Qt.UserRole) if self.list.currentItem() else None
    def add(self):
        d=GoalDialog(parent=self)
        if d.exec()==QDialog.Accepted:self.service.save_goal(d.data());self.refresh();self.changed.emit()
    def edit(self):
        g=self.current()
        if not g:return
        d=GoalDialog(g,self)
        if d.exec()==QDialog.Accepted:self.service.save_goal(d.data(),g["id"]);self.refresh();self.changed.emit()
    def delete(self):
        g=self.current()
        if g and QMessageBox.question(self,tr("Delete goal"),tr("Delete named item", name=g["title"]))==QMessageBox.Yes:self.service.delete_goal(g["id"]);self.refresh();self.changed.emit()


class SearchDialog(QDialog):
    navigate = Signal(str, int)
    def __init__(self, service:DataService,parent=None):
        super().__init__(parent); self.service=service; self.setModal(True); self.setWindowTitle(tr("Search Mentor")); self.setMinimumSize(680,540)
        self.setStyleSheet(f"QDialog{{background:{tokens.BG2};}}")
        root=QVBoxLayout(self);root.setContentsMargins(24,24,24,24);root.setSpacing(12)
        top=QHBoxLayout(); search_icon=QLabel();search_icon.setPixmap(icon("search",tokens.MUTED,20).pixmap(20,20));top.addWidget(search_icon)
        self.query=QLineEdit();self.query.setPlaceholderText(tr("Search students, lessons, notes, materials, tasks…"));self.query.setStyleSheet("font-size:16px;padding:12px;");self.query.textChanged.connect(self.refresh);top.addWidget(self.query,1);root.addLayout(top)
        hint=QLabel(tr("Press Enter to open a result · Esc to close")); hint.setObjectName("muted");root.addWidget(hint)
        self.results=QListWidget();self.results.itemActivated.connect(self.open_item);root.addWidget(self.results,1);self.query.setFocus()
    def refresh(self):
        self.results.clear();data=self.service.search(self.query.text())
        for group,rows in data.items():
            if not rows: continue
            label = tr("Lessons").upper() if group == "Sessions" else tr(group).upper()
            head=QListWidgetItem(label);head.setFlags(Qt.NoItemFlags);head.setForeground(QColor(tokens.MUTED));self.results.addItem(head)
            for r in rows:
                if group=="Students":text=f"{r['name']}  ·  {r.get('subject') or r.get('grade') or ''}";key="students"
                elif group=="Sessions":text=f"{r['subject']}  ·  {format_date(r['session_date'], compact=True)} {format_time(r['start_time'])}";key="schedule"
                elif group=="Notes":text=f"{r['title']}  ·  {r.get('subject') or tr('Note')}";key="notes"
                elif group=="Materials":text=f"{r['name']}  ·  {r.get('category') or tr('Material')}";key="materials"
                elif group=="Assignments":text=f"{r['title']}  ·  {enum_display(r.get('status') or 'Assigned')}";key="assignments"
                else:text=f"{r['title']}  ·  {enum_display(r.get('priority') or 'Task')}";key="tasks"
                item=QListWidgetItem(text);item.setData(Qt.UserRole,(key,int(r['id'])));self.results.addItem(item)
    def open_item(self,item):
        data=item.data(Qt.UserRole)
        if data:
            key, entity_id = data[0], int(data[1])
            self.accept()
            QTimer.singleShot(0, lambda: self.navigate.emit(key, entity_id))


class TemplateNameDialog(BaseDialog):
    """Small, predictable template-name prompt that keeps styling inside Mentor."""

    def __init__(self, suggested_subject: str = "Lesson", parent=None):
        super().__init__(tr("Save Lesson Template"), parent)
        self.setMinimumWidth(430)
        root = QVBoxLayout(self); root.setContentsMargins(24,22,24,22); root.setSpacing(13)
        self.add_header(root, tr("Save as template"), tr("Reuse the student, subject, duration, location, reminder, and repeat settings."))
        self.name = QLineEdit(f"{suggested_subject} {tr('Lesson').lower()}")
        self.name.selectAll()
        root.addWidget(self.name)
        root.addWidget(self.buttons("Save Template"))
        self.name.setFocus()

    def accept(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(self, tr("Missing name"), tr("Give this template a short name."))
            return
        super().accept()


class AssignmentDialog(BaseDialog):
    """Create or edit homework while keeping lesson/student relationships intact."""

    def __init__(
        self,
        service: DataService,
        assignment: dict[str, Any] | None = None,
        default_student_id: int | None = None,
        default_session_id: int | None = None,
        parent=None,
    ):
        super().__init__(tr("Edit Homework") if assignment else tr("Assign Homework"), parent)
        self.service = service
        self.assignment = assignment
        self.setMinimumSize(650, 560)
        root = QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        self.add_header(
            root,
            tr("Edit homework") if assignment else tr("Assign homework"),
            tr("Keep the task clear, connect it to the right learner, and optionally link a lesson or material."),
        )

        form = QFormLayout(); form.setSpacing(11)
        self.title = QLineEdit(); self.title.setPlaceholderText(tr("e.g. Complete questions 1–10"))
        self.student = QComboBox(); self.student.addItem(tr("Unassigned"), None)
        for student in service.students(active_only=True):
            self.student.addItem(student["name"], student["id"])
        self.student.currentIndexChanged.connect(self._student_changed)

        self.subject = QLineEdit(); self.subject.setPlaceholderText(tr("Subject"))
        self.lesson = QComboBox(); self.lesson.addItem(tr("No linked lesson"), None)
        lesson_rows = service.sessions_between(date.today() - timedelta(days=120), date.today() + timedelta(days=365))
        for lesson in reversed(lesson_rows):
            label = f"{lesson['session_date']} · {lesson['start_time']} · {lesson['subject']}"
            if lesson.get("student_name"):
                label += f" · {lesson['student_name']}"
            self.lesson.addItem(label, lesson["id"])
        self.lesson.currentIndexChanged.connect(self._lesson_changed)

        self.material = QComboBox(); self.material.addItem(tr("No linked material"), None)
        for material in service.materials():
            self.material.addItem(material["name"], material["id"])

        self.due = QDateEdit(); self.due.setCalendarPopup(True); self.due.setDisplayFormat("ddd, MMM d, yyyy")
        self.due.setDate(QDate.currentDate().addDays(7))
        self.status = QComboBox(); add_enum_items(self.status,["Assigned", "Submitted", "Completed", "Skipped"])
        self.score = QLineEdit(); self.score.setPlaceholderText(tr("Optional · e.g. 18/20 or A"))
        self.instructions = QTextEdit(); self.instructions.setMinimumHeight(130); self.instructions.setPlaceholderText(tr("Instructions, questions, links, expectations…"))

        for label, widget in [
            ("Homework", self.title), ("Student", self.student), ("Subject", self.subject),
            ("Lesson", self.lesson), ("Material", self.material), ("Due", self.due),
            ("Status", self.status), ("Score / result", self.score), ("Instructions", self.instructions),
        ]:
            form.addRow(tr(label), widget)
        root.addLayout(form)
        root.addWidget(self.buttons("Save Homework" if assignment else "Assign Homework"))

        if assignment:
            self.title.setText(assignment.get("title") or "")
            idx = self.student.findData(assignment.get("student_id")); self.student.setCurrentIndex(idx if idx >= 0 else 0)
            self.subject.setText(assignment.get("subject") or "")
            idx = self.lesson.findData(assignment.get("session_id")); self.lesson.setCurrentIndex(idx if idx >= 0 else 0)
            idx = self.material.findData(assignment.get("material_id")); self.material.setCurrentIndex(idx if idx >= 0 else 0)
            qd = QDate.fromString(assignment.get("due_date") or "", "yyyy-MM-dd")
            if qd.isValid(): self.due.setDate(qd)
            set_enum_value(self.status, assignment.get("status") or "Assigned")
            self.score.setText(assignment.get("score") or "")
            self.instructions.setPlainText(assignment.get("instructions") or "")
        else:
            if default_session_id is not None:
                idx = self.lesson.findData(default_session_id)
                if idx >= 0: self.lesson.setCurrentIndex(idx)
            elif default_student_id is not None:
                idx = self.student.findData(default_student_id)
                if idx >= 0: self.student.setCurrentIndex(idx)
        self.title.setFocus()

    def _student_changed(self, *_args) -> None:
        student_id = self.student.currentData()
        if student_id is None or self.subject.text().strip():
            return
        student = self.service.student(int(student_id))
        if student and student.get("subject"):
            self.subject.setText(student["subject"])

    def _lesson_changed(self, *_args) -> None:
        lesson_id = self.lesson.currentData()
        if lesson_id is None:
            return
        lesson = self.service.session(int(lesson_id))
        if not lesson:
            return
        if lesson.get("student_id") is not None:
            idx = self.student.findData(lesson["student_id"])
            if idx >= 0: self.student.setCurrentIndex(idx)
        self.subject.setText(lesson.get("subject") or self.subject.text())

    def data(self) -> dict[str, Any]:
        return {
            "student_id": self.student.currentData(),
            "session_id": self.lesson.currentData(),
            "material_id": self.material.currentData(),
            "subject": self.subject.text(),
            "title": self.title.text(),
            "instructions": self.instructions.toPlainText(),
            "due_date": self.due.date().toString("yyyy-MM-dd"),
            "status": str(self.status.currentData() or "Assigned"),
            "score": self.score.text(),
        }

    def accept(self) -> None:
        if not self.title.text().strip():
            QMessageBox.warning(self, tr("Missing homework"), tr("Homework needs a title."))
            self.title.setFocus(); return
        super().accept()


class AssignmentManager(BaseDialog):
    changed = Signal()

    def __init__(self, service: DataService, parent=None, student_id: int | None = None):
        super().__init__(tr("Homework & Assignments"), parent)
        self.service = service
        self.student_id = student_id
        self.setMinimumSize(860, 590)
        root = QVBoxLayout(self); root.setContentsMargins(24,24,24,24); root.setSpacing(13)
        student = self.service.student(student_id) if student_id is not None else None
        subtitle = (
            f"{tr('Homework')} · {student['name']}" if student else
            tr("See what is assigned, overdue, submitted, or completed without mixing it into ordinary tasks.")
        )
        self.add_header(root, tr("Homework & Assignments"), subtitle)

        controls = QHBoxLayout()
        self.show_done = QCheckBox(tr("Show completed"))
        self.show_done.setChecked(True)
        self.show_done.toggled.connect(lambda _checked: self.refresh())
        add = QPushButton(tr("Assign Homework")); add.setObjectName("primary"); add.setIcon(icon("plus", "#111111", 15)); add.clicked.connect(self.add)
        controls.addWidget(self.show_done); controls.addStretch(); controls.addWidget(add); root.addLayout(controls)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([tr("Homework"), tr("Student"), tr("Due"), tr("Status"), tr("Score")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setColumnWidth(0, 290); self.table.setColumnWidth(1, 180); self.table.setColumnWidth(2, 120); self.table.setColumnWidth(3, 120); self.table.setColumnWidth(4, 90)
        self.table.itemDoubleClicked.connect(lambda _item: self.edit())
        root.addWidget(self.table, 1)

        row = QHBoxLayout(); row.addStretch()
        edit = QPushButton(tr("Edit")); complete = QPushButton(tr("Mark Complete")); delete = QPushButton(tr("Delete")); delete.setObjectName("danger"); close = QPushButton(tr("Close"))
        edit.clicked.connect(self.edit); complete.clicked.connect(self.complete); delete.clicked.connect(self.delete); close.clicked.connect(self.accept)
        for button in (edit, complete, delete, close): row.addWidget(button)
        root.addLayout(row)
        self.refresh()

    def refresh(self) -> None:
        rows = self.service.assignments(student_id=self.student_id, include_completed=self.show_done.isChecked())
        self.table.setRowCount(len(rows))
        for r, assignment in enumerate(rows):
            title = assignment["title"]
            if assignment.get("overdue"):
                title = f"{title}  ·  {tr('OVERDUE')}"
            values = [
                title,
                assignment.get("student_name") or tr("Unassigned"),
                format_date(assignment.get("due_date")) if assignment.get("due_date") else "—",
                enum_display(assignment.get("status") or "Assigned"),
                assignment.get("score") or "—",
            ]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value)); item.setData(Qt.UserRole, assignment["id"])
                if c == 0 and assignment.get("overdue"):
                    item.setForeground(QColor(tokens.ERROR))
                self.table.setItem(r, c, item)
        if rows:
            self.table.selectRow(0)

    def current_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0 or not self.table.item(row,0): return None
        return int(self.table.item(row,0).data(Qt.UserRole))

    def add(self) -> None:
        dialog = AssignmentDialog(self.service, default_student_id=self.student_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.service.save_assignment(dialog.data()); self.refresh(); self.changed.emit()

    def edit(self) -> None:
        assignment_id = self.current_id()
        if assignment_id is None: return
        assignment = self.service.assignment(assignment_id)
        if not assignment: return
        dialog = AssignmentDialog(self.service, assignment=assignment, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.service.save_assignment(dialog.data(), assignment_id); self.refresh(); self.changed.emit()

    def complete(self) -> None:
        assignment_id = self.current_id()
        if assignment_id is None: return
        self.service.set_assignment_status(assignment_id, "Completed")
        self.refresh(); self.changed.emit()

    def delete(self) -> None:
        assignment_id = self.current_id()
        if assignment_id is None: return
        assignment = self.service.assignment(assignment_id)
        if assignment and QMessageBox.question(self, tr("Delete homework"), f"{tr('Delete')} '{assignment['title']}'?") == QMessageBox.Yes:
            self.service.delete_assignment(assignment_id); self.refresh(); self.changed.emit()


class LessonWrapUpDialog(BaseDialog):
    """One short post-lesson flow for completion, attendance, notes, and homework."""

    def __init__(self, service: DataService, session: dict[str, Any], parent=None):
        super().__init__(tr("Complete Lesson"), parent)
        self.service = service
        self.session = session
        self.setMinimumSize(700, 620)
        root = QVBoxLayout(self); root.setContentsMargins(26,24,26,24); root.setSpacing(14)
        student = session.get("student_name") or tr("Unassigned")
        self.add_header(root, tr("Wrap up lesson"), f"{session.get('subject') or tr('Lesson')} · {student} · {format_time(session.get('start_time'))}–{format_time(session.get('end_time'))}")

        review = QFrame(); review.setObjectName("section")
        form = QFormLayout(review); form.setContentsMargins(16,16,16,16); form.setSpacing(11)
        self.attendance = QComboBox(); add_enum_items(self.attendance,["Not marked","Present","Late","Absent","Excused"])
        set_enum_value(self.attendance, session.get("attendance") or "Not marked")
        self.attendance.setEnabled(session.get("student_id") is not None)
        self.notes = QTextEdit(); self.notes.setMinimumHeight(120); self.notes.setPlaceholderText(tr("What was covered? What should you remember next time?"))
        self.notes.setPlainText(session.get("notes") or "")
        form.addRow(tr("Attendance"), self.attendance); form.addRow(tr("Lesson notes"), self.notes)
        root.addWidget(review)

        homework = QFrame(); homework.setObjectName("section")
        hw = QVBoxLayout(homework); hw.setContentsMargins(16,14,16,16); hw.setSpacing(10)
        self.create_homework = QCheckBox(tr("Assign homework before finishing"))
        self.create_homework.setEnabled(session.get("student_id") is not None)
        self.create_homework.toggled.connect(self._toggle_homework)
        hw.addWidget(self.create_homework)
        homework_form = QFormLayout(); homework_form.setSpacing(9)
        self.homework_title = QLineEdit(); self.homework_title.setPlaceholderText(tr("Homework title"))
        self.homework_due = QDateEdit(); self.homework_due.setCalendarPopup(True); self.homework_due.setDate(QDate.currentDate().addDays(7))
        self.homework_instructions = QTextEdit(); self.homework_instructions.setFixedHeight(86); self.homework_instructions.setPlaceholderText(tr("Optional instructions"))
        homework_form.addRow(tr("Homework"), self.homework_title); homework_form.addRow(tr("Due"), self.homework_due); homework_form.addRow(tr("Instructions"), self.homework_instructions)
        hw.addLayout(homework_form)
        root.addWidget(homework)
        self._homework_widgets = [self.homework_title, self.homework_due, self.homework_instructions]
        self._toggle_homework(False)