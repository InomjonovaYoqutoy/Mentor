from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ...services.data_service import DataService
from ...theme import tokens
from ...i18n import tr, localized_insight, localize_activity_title, enum_display, format_date
from ..icons import icon
from ..widgets import Card, InsightCard, QuickActionButton, SessionRow, StatCard


class HomePage(QWidget):
    request_action = Signal(str, object)

    def __init__(self, service: DataService, parent=None):
        super().__init__(parent)
        self.service = service

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        body = QWidget()
        self.body_layout = QVBoxLayout(body)
        self.body_layout.setContentsMargins(26, 12, 26, 118)
        self.body_layout.setSpacing(22)

        self._build_header()
        self._build_stats()
        self._build_main()
        self._build_assignments()
        self.body_layout.addStretch()

        scroll.setWidget(body)
        outer.addWidget(scroll)

    def _build_header(self) -> None:
        """Keep the top area close to the original visual reference.

        Version 1.1 added a large 'Up Next' island here. It consumed too much
        horizontal space and looked broken when there was no upcoming lesson.
        Upcoming information already has a dedicated stat card and schedule,
        so the header is intentionally calm again.
        """
        row = QHBoxLayout()
        row.setSpacing(22)

        left = QVBoxLayout()
        left.setSpacing(5)
        self.greeting = QLabel()
        self.greeting.setObjectName("pageTitle")
        self.subtitle = QLabel(tr("Better planning. Better teaching. Better results."))
        self.subtitle.setObjectName("secondary")
        left.addWidget(self.greeting)
        left.addWidget(self.subtitle)
        row.addLayout(left, 1)

        self.quote = QLabel(tr("“Progress isn’t about being perfect,\nit’s about being consistent.”"))
        self.quote.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.quote.setStyleSheet(
            f"color:{tokens.TEXT2};"
            f"border-left:2px solid {tokens.ACCENT};"
            "padding-left:12px;"
            "font-size:12px;"
        )
        row.addWidget(self.quote, 0, Qt.AlignVCenter)
        self.body_layout.addLayout(row)

    def _build_stats(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self.cards = {
            "students": StatCard("people", tr("Total Students")),
            "upcoming": StatCard("calendar", tr("Upcoming Lessons")),
            "tasks": StatCard("check", tr("Tasks Due")),
            "goals": StatCard("star", tr("Goals Progress")),
        }
        for index, card in enumerate(self.cards.values()):
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            grid.addWidget(card, 0, index)
            grid.setColumnStretch(index, 1)

        self.cards["students"].clicked.connect(lambda: self.request_action.emit("students", None))
        self.cards["upcoming"].clicked.connect(lambda: self.request_action.emit("schedule", None))
        self.cards["tasks"].clicked.connect(lambda: self.request_action.emit("tasks", None))
        self.cards["goals"].clicked.connect(lambda: self.request_action.emit("goals", None))
        self.body_layout.addLayout(grid)

    def _build_main(self) -> None:
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        schedule = Card()
        schedule.setMinimumHeight(354)
        schedule_layout = QVBoxLayout(schedule)
        schedule_layout.setContentsMargins(18, 16, 18, 16)
        schedule_layout.setSpacing(5)

        head = QHBoxLayout()
        calendar_icon = QLabel()
        calendar_icon.setPixmap(icon("calendar", tokens.ACCENT, 19).pixmap(19, 19))
        title = QLabel(tr("Today's Schedule"))
        title.setObjectName("sectionTitle")
        view = QPushButton(tr("View all"))
        view.setObjectName("ghost")
        view.clicked.connect(lambda: self.request_action.emit("schedule", None))
        head.addWidget(calendar_icon)
        head.addWidget(title)
        head.addStretch()
        head.addWidget(view)
        schedule_layout.addLayout(head)

        self.schedule_box = QVBoxLayout()
        self.schedule_box.setSpacing(0)
        schedule_layout.addLayout(self.schedule_box)
        schedule_layout.addStretch()
        grid.addWidget(schedule, 0, 0, 2, 1)

        self.insight = InsightCard()
        grid.addWidget(self.insight, 0, 1, 2, 1)

        quick = Card()
        quick_layout = QVBoxLayout(quick)
        quick_layout.setContentsMargins(18, 15, 18, 15)
        quick_layout.setSpacing(10)

        quick_head = QHBoxLayout()
        quick_icon = QLabel()
        quick_icon.setPixmap(icon("bolt", tokens.ACCENT, 19).pixmap(19, 19))
        quick_title = QLabel(tr("Quick Actions"))
        quick_title.setObjectName("sectionTitle")
        quick_head.addWidget(quick_icon)
        quick_head.addWidget(quick_title)
        quick_head.addStretch()
        quick_layout.addLayout(quick_head)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)
        definitions = [
            ("calendar_add", tr("Add Lesson"), "add_session"),
            ("note", tr("Add Note"), "add_note"),
            ("task", tr("Homework"), "add_assignment"),
            ("folder", tr("Add Material"), "add_material"),
            ("people", tr("Add Student"), "add_student"),
            ("check", tr("New Task"), "new_task"),
        ]
        for index, (icon_name, text, action) in enumerate(definitions):
            button = QuickActionButton(icon_name, text)
            button.clicked.connect(lambda _=False, a=action: self.request_action.emit(a, None))
            quick_grid.addWidget(button, index // 2, index % 2)
        quick_layout.addLayout(quick_grid)
        grid.addWidget(quick, 0, 2)

        activity = Card()
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(18, 15, 18, 15)
        activity_layout.setSpacing(8)

        activity_head = QHBoxLayout()
        activity_icon = QLabel()
        activity_icon.setPixmap(icon("clock", tokens.ACCENT, 19).pixmap(19, 19))
        activity_title = QLabel(tr("Recent Activity"))
        activity_title.setObjectName("sectionTitle")
        activity_head.addWidget(activity_icon)
        activity_head.addWidget(activity_title)
        activity_head.addStretch()
        activity_layout.addLayout(activity_head)

        self.activity_box = QVBoxLayout()
        self.activity_box.setSpacing(7)
        activity_layout.addLayout(self.activity_box)
        activity_layout.addStretch()
        grid.addWidget(activity, 1, 2)

        grid.setColumnStretch(0, 5)
        grid.setColumnStretch(1, 4)
        grid.setColumnStretch(2, 4)
        self.body_layout.addLayout(grid)

    def _build_assignments(self) -> None:
        self.assignments_card = Card()
        layout = QVBoxLayout(self.assignments_card)
        layout.setContentsMargins(18,15,18,15); layout.setSpacing(8)
        head = QHBoxLayout(); ico = QLabel(); ico.setPixmap(icon("task", tokens.ACCENT, 18).pixmap(18,18))
        title = QLabel(tr("Homework & Assignments")); title.setObjectName("sectionTitle")
        self.assignments_summary = QLabel(); self.assignments_summary.setObjectName("secondary")
        view_all = QPushButton(tr("View all")); view_all.setObjectName("ghost"); view_all.clicked.connect(lambda: self.request_action.emit("assignments", None))
        head.addWidget(ico); head.addWidget(title); head.addStretch(); head.addWidget(self.assignments_summary); head.addWidget(view_all); layout.addLayout(head)
        self.assignments_box = QVBoxLayout(); self.assignments_box.setSpacing(5); layout.addLayout(self.assignments_box)
        self.body_layout.addWidget(self.assignments_card)

    @staticmethod
    def _clear(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.deleteLater()
            elif child_layout:
                HomePage._clear(child_layout)

    def refresh(self) -> None:
        now = datetime.now()
        hour = now.hour
        greeting = tr("Good morning") if hour < 12 else tr("Good afternoon") if hour < 18 else tr("Good evening")
        name = self.service.get_setting("profile_name", "Shohjahon")
        self.greeting.setText(f"{greeting}, <span style='color:{tokens.ACCENT}'>{name}</span>")
        self.greeting.setTextFormat(Qt.RichText)

        data = self.service.dashboard()
        self.cards["students"].set_data(str(data["students"]), tr("Active learners"))
        self.cards["upcoming"].set_data(
            str(data["upcoming"]),
            f"{data['week_count']} {tr('this week')}" if data["week_count"] else tr("Nothing scheduled"),
        )
        self.cards["tasks"].set_data(
            str(data["tasks_due"]),
            tr("Need attention") if data["tasks_due"] else tr("You're clear"),
            bool(data["tasks_due"]),
        )
        self.cards["goals"].set_data(f"{data['goal_progress']}%", tr("Across active goals"))
        self.insight.text.setText(localized_insight(data))

        self._clear(self.schedule_box)
        if not data["today_sessions"]:
            wrap = QWidget()
            layout = QVBoxLayout(wrap)
            layout.setContentsMargins(0, 32, 0, 22)
            layout.setSpacing(8)

            empty = QLabel(tr("No lessons today"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("font-size:16px;font-weight:600;")
            layout.addWidget(empty)

            sub = QLabel(tr("Your schedule is clear."))
            sub.setObjectName("muted")
            sub.setAlignment(Qt.AlignCenter)
            layout.addWidget(sub)

            action_row = QHBoxLayout()
            action_row.addStretch()
            add = QPushButton(tr("Schedule Lesson"))
            add.setObjectName("primary")
            add.clicked.connect(lambda: self.request_action.emit("add_session", None))
            action_row.addWidget(add)
            action_row.addStretch()
            layout.addLayout(action_row)
            self.schedule_box.addWidget(wrap)
        else:
            sessions = data["today_sessions"]
            for index, session in enumerate(sessions):
                row = SessionRow(session)
                row.clicked.connect(lambda session_id: self.request_action.emit("session", session_id))
                row.context_requested.connect(lambda session_id, pos: self.request_action.emit("session_context", {"id": session_id, "pos": pos}))
                self.schedule_box.addWidget(row)
                if index < len(sessions) - 1:
                    separator = QFrame()
                    separator.setObjectName("hairline")
                    self.schedule_box.addWidget(separator)

        self._clear(self.activity_box)
        if not data["activity"]:
            label = QLabel(tr("No recent activity yet."))
            label.setObjectName("muted")
            self.activity_box.addWidget(label)
        else:
            for activity in data["activity"][:4]:
                wrap = QWidget()
                row = QHBoxLayout(wrap)
                row.setContentsMargins(0, 0, 0, 0)
                row.setSpacing(9)

                dot = QLabel("●")
                dot.setStyleSheet(f"color:{tokens.ACCENT};font-size:9px;")

                text = QVBoxLayout()
                text.setSpacing(1)
                title = QLabel(localize_activity_title(activity["title"]))
                subtitle = QLabel(activity.get("description") or "")
                subtitle.setObjectName("muted")
                subtitle.setWordWrap(True)
                text.addWidget(title)
                text.addWidget(subtitle)

                row.addWidget(dot)
                row.addLayout(text, 1)
                self.activity_box.addWidget(wrap)

        self._clear(self.assignments_box)
        due = int(data.get("assignments_due") or 0)
        overdue = int(data.get("assignments_overdue") or 0)
        if overdue:
            self.assignments_summary.setText(tr("Homework overdue and due", overdue=overdue, due=due))
            self.assignments_summary.setStyleSheet(f"color:{tokens.ERROR};")
        elif due:
            self.assignments_summary.setText(tr("Homework due today", count=due))
            self.assignments_summary.setStyleSheet(f"color:{tokens.ACCENT};")
        else:
            self.assignments_summary.setText(tr("You're clear"))
            self.assignments_summary.setStyleSheet(f"color:{tokens.TEXT2};")

        assignment_rows = data.get("assignment_rows") or []
        if not assignment_rows:
            empty = QLabel(tr("No homework due soon."))
            empty.setObjectName("muted"); self.assignments_box.addWidget(empty)
        else:
            for assignment in assignment_rows[:4]:
                wrap = QWidget(); row = QHBoxLayout(wrap); row.setContentsMargins(2,4,2,4); row.setSpacing(10)
                dot = QLabel("●"); dot.setStyleSheet(f"color:{tokens.ERROR if assignment.get('overdue') else tokens.ACCENT};font-size:9px;")
                text = QVBoxLayout(); text.setSpacing(1)
                title = QLabel(assignment.get("title") or tr("Homework")); title.setStyleSheet("font-weight:600;")
                who = assignment.get("student_name") or tr("Unassigned"); due_text = format_date(assignment.get("due_date"), compact=True) if assignment.get("due_date") else "—"
                meta = QLabel(f"{who} · {due_text} · {enum_display(assignment.get('status') or 'Assigned')}"); meta.setObjectName("muted")
                text.addWidget(title); text.addWidget(meta)
                open_button = QPushButton(); open_button.setIcon(icon("arrow_right",tokens.TEXT2,14)); open_button.setFixedSize(32,32)
                open_button.clicked.connect(lambda _=False, aid=int(assignment["id"]): self.request_action.emit("assignment", aid))
                row.addWidget(dot); row.addLayout(text,1); row.addWidget(open_button); self.assignments_box.addWidget(wrap)