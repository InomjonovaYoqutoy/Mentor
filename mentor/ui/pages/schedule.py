from __future__ import annotations

from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget
)

from ...services.data_service import DataService
from ...theme import tokens
from ...i18n import tr, format_date, format_weekday, week_starts_monday, format_duration, lesson_count
from ..icons import icon
from ..widgets import Card, LessonChip, SegmentedControl, SessionRow


class SchedulePage(QWidget):
    request_action = Signal(str, object)

    def __init__(self, service: DataService, parent=None):
        super().__init__(parent)
        self.service = service
        self.anchor = date.today()
        self.mode = service.get_setting("default_schedule_view", "week")
        if self.mode not in ("day", "week"): self.mode = "week"
        root = QVBoxLayout(self); root.setContentsMargins(26,14,26,115); root.setSpacing(16)

        top = QHBoxLayout(); top.setSpacing(10)
        titles = QVBoxLayout(); titles.setSpacing(2)
        title = QLabel(tr("Schedule")); title.setObjectName("pageTitle")
        subtitle = QLabel(tr("Plan lessons without losing sight of the week.")); subtitle.setObjectName("secondary")
        titles.addWidget(title); titles.addWidget(subtitle); top.addLayout(titles); top.addStretch()
        self.segment = SegmentedControl([("day",tr("Day")),("week",tr("Week"))], self.mode)
        self.segment.changed.connect(self.set_mode); top.addWidget(self.segment)
        add = QPushButton(tr("New Lesson")); add.setIcon(icon("calendar_add", "#111111", 18)); add.setObjectName("primary")
        add.clicked.connect(lambda: self.request_action.emit("add_session", {"date": self.anchor}))
        top.addWidget(add); root.addLayout(top)

        nav = QHBoxLayout(); nav.setSpacing(7)
        prev = QPushButton(); prev.setIcon(icon("chevron_left",tokens.TEXT2,18)); prev.setFixedWidth(38); prev.clicked.connect(lambda:self.shift(-1))
        today = QPushButton(tr("Today")); today.setObjectName("pill"); today.clicked.connect(self.go_today)
        nxt = QPushButton(); nxt.setIcon(icon("chevron_right",tokens.TEXT2,18)); nxt.setFixedWidth(38); nxt.clicked.connect(lambda:self.shift(1))
        self.period = QLabel(); self.period.setObjectName("sectionTitle")
        nav.addWidget(prev); nav.addWidget(today); nav.addWidget(nxt); nav.addSpacing(7); nav.addWidget(self.period); nav.addStretch()
        self.summary = QLabel(); self.summary.setObjectName("secondary"); nav.addWidget(self.summary)
        root.addLayout(nav)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True); root.addWidget(self.scroll,1)
        self.refresh()

    def set_anchor(self, value: date, mode: str | None = None) -> None:
        self.anchor = value
        if mode in ("day","week"):
            self.mode = mode; self.segment.select(mode, animate=False, emit=False)
        self.refresh()

    def set_mode(self, mode: str) -> None:
        if mode not in ("day","week"): return
        self.mode = mode; self.refresh()

    def shift(self, n: int) -> None:
        self.anchor += timedelta(days=n if self.mode == "day" else 7*n)
        self.refresh()

    def go_today(self) -> None:
        self.anchor = date.today(); self.refresh()

    def refresh(self) -> None:
        if self.mode == "day": self._day()
        else: self._week()

    def _day(self) -> None:
        self.period.setText(format_date(self.anchor))
        rows = self.service.sessions_between(self.anchor,self.anchor)
        total_minutes = sum(self._minutes(x) for x in rows if x.get("status") != "Cancelled")
        self.summary.setText(f"{lesson_count(len(rows))} · {format_duration(total_minutes)}")
        body = QWidget(); l = QVBoxLayout(body); l.setContentsMargins(0,0,0,0); l.setSpacing(12)

        hero = Card(); hl=QHBoxLayout(hero);hl.setContentsMargins(18,14,18,14)
        date_box=QVBoxLayout(); day=QLabel(format_weekday(self.anchor, short=False).upper());day.setObjectName("eyebrow")
        number=QLabel(self.anchor.strftime("%d"));number.setStyleSheet("font-size:28px;font-weight:600;")
        date_box.addWidget(day);date_box.addWidget(number);hl.addLayout(date_box);hl.addSpacing(12)
        desc=QVBoxLayout(); label=QLabel(tr("Today's teaching plan") if self.anchor==date.today() else tr("Teaching plan"));label.setObjectName("sectionTitle")
        small=QLabel(tr("Click a lesson to edit it, or add another one at any time."));small.setObjectName("secondary");desc.addWidget(label);desc.addWidget(small);hl.addLayout(desc,1)
        add=QPushButton(tr("Add Lesson"));add.setIcon(icon("plus",tokens.ACCENT,16));add.clicked.connect(lambda:self.request_action.emit("add_session",{"date":self.anchor}));hl.addWidget(add)
        l.addWidget(hero)

        if not rows:
            c=Card();cl=QVBoxLayout(c);cl.setContentsMargins(28,34,28,34);cl.setSpacing(9)
            ico=QLabel();ico.setPixmap(icon("calendar_add",tokens.ACCENT,30).pixmap(30,30));ico.setAlignment(Qt.AlignCenter);cl.addWidget(ico)
            msg=QLabel(tr("No lessons scheduled"));msg.setAlignment(Qt.AlignCenter);msg.setStyleSheet("font-size:17px;font-weight:600;");cl.addWidget(msg)
            sub=QLabel(tr("Your day is clear. Add a lesson when you're ready."));sub.setAlignment(Qt.AlignCenter);sub.setObjectName("secondary");cl.addWidget(sub)
            row=QHBoxLayout();row.addStretch();b=QPushButton(tr("Schedule Lesson"));b.setObjectName("primary");b.clicked.connect(lambda:self.request_action.emit("add_session",{"date":self.anchor}));row.addWidget(b);row.addStretch();cl.addLayout(row);l.addWidget(c)
        else:
            c=Card();cl=QVBoxLayout(c);cl.setContentsMargins(16,10,16,12);cl.setSpacing(0)
            for session in rows:
                r=SessionRow(session);r.clicked.connect(lambda sid:self.request_action.emit("session",sid));r.context_requested.connect(lambda sid,pos:self.request_action.emit("session_context",{"id":sid,"pos":pos}));cl.addWidget(r)
                if session is not rows[-1]:
                    line=QFrame();line.setObjectName("hairline");cl.addWidget(line)
            l.addWidget(c)
        l.addStretch(); self.scroll.setWidget(body)

    def _week(self) -> None:
        offset = self.anchor.weekday() if week_starts_monday() else (self.anchor.weekday() + 1) % 7
        start = self.anchor - timedelta(days=offset); end = start + timedelta(days=6)
        self.period.setText(f"{format_date(start, compact=True, relative=False)} — {format_date(end, compact=True, relative=False)}")
        sessions = self.service.sessions_between(start,end)
        self.summary.setText(f"{lesson_count(len(sessions))} · {tr('this week')}")
        grouped = {start+timedelta(days=i):[] for i in range(7)}
        for session in sessions:
            d = date.fromisoformat(session["session_date"]); grouped.setdefault(d,[]).append(session)

        body=QWidget();grid=QGridLayout(body);grid.setContentsMargins(0,0,0,0);grid.setHorizontalSpacing(9);grid.setVerticalSpacing(9)
        for i,d in enumerate(grouped):
            col=Card();cl=QVBoxLayout(col);cl.setContentsMargins(9,11,9,10);cl.setSpacing(7)
            is_today=d==date.today()
            head_btn=QPushButton();head_btn.setObjectName("ghost");head_btn.setCursor(Qt.PointingHandCursor)
            head_btn.setText(f"{format_weekday(d).upper()}\n{d.day}")
            head_btn.setStyleSheet(
                f"QPushButton{{background:{tokens.ACCENT_SOFT if is_today else 'transparent'};border:{('1px solid '+tokens.ACCENT) if is_today else 'none'};"
                f"border-radius:14px;color:{tokens.ACCENT if is_today else tokens.TEXT2};font-size:12px;font-weight:600;padding:8px 4px;}}"
                "QPushButton:hover{background:#1B1B1E;}"
            )
            head_btn.clicked.connect(lambda _=False, day=d:self.set_anchor(day,"day"));cl.addWidget(head_btn)
            if grouped[d]:
                for session in grouped[d]:
                    chip=LessonChip(session);chip.clicked.connect(lambda sid:self.request_action.emit("session",sid));chip.context_requested.connect(lambda sid,pos:self.request_action.emit("session_context",{"id":sid,"pos":pos}));cl.addWidget(chip)
            else:
                empty=QLabel(tr("No lessons"));empty.setObjectName("muted");empty.setAlignment(Qt.AlignCenter);empty.setMinimumHeight(54);cl.addWidget(empty)
            cl.addStretch()
            plus=QPushButton(tr("Add"));plus.setIcon(icon("plus",tokens.MUTED,14));plus.setObjectName("ghost")
            plus.clicked.connect(lambda _=False, day=d:self.request_action.emit("add_session",{"date":day}));cl.addWidget(plus)
            grid.addWidget(col,0,i)
            grid.setColumnStretch(i,1)
        self.scroll.setWidget(body)

    @staticmethod
    def _minutes(session: dict) -> int:
        try:
            st=datetime.strptime(session["start_time"],"%H:%M");en=datetime.strptime(session["end_time"],"%H:%M")
            return max(0,int((en-st).total_seconds()/60))
        except Exception:return 0

    @staticmethod
    def _pretty_minutes(minutes: int) -> str:
        return format_duration(minutes)