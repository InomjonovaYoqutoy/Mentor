from __future__ import annotations

from datetime import date, datetime

from PySide6.QtCore import (
    QEasingCurve, QEvent, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer, Signal
)
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QToolButton, QVBoxLayout, QWidget
)

from ..theme import tokens
from ..i18n import tr, enum_display, format_time, format_duration
from .icons import icon


class AtmosphereWidget(QWidget):
    """Near-black app background with barely visible warm depth."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Root")

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(tokens.BG))
        if tokens.AMBIENT_GLOW:
            # Use the selected accent as atmosphere, but keep it quiet.
            accent = QColor(tokens.ACCENT)
            g1 = QRadialGradient(self.width() * 0.82, self.height() * 0.10, max(260.0, self.width() * 0.40))
            c1 = QColor(accent); c1.setAlpha(15)
            c2 = QColor(accent); c2.setAlpha(6)
            g1.setColorAt(0.0, c1); g1.setColorAt(0.45, c2); g1.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(self.rect(), QBrush(g1))
            g2 = QRadialGradient(self.width() * 0.10, self.height() * 0.88, max(220.0, self.width() * 0.32))
            c3 = QColor(accent); c3.setAlpha(7)
            g2.setColorAt(0.0, c3); g2.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(self.rect(), QBrush(g2))
        p.end()

class Card(QFrame):
    """Reusable dark surface with a restrained hover response."""

    def __init__(self, parent: QWidget | None = None, interactive: bool = False):
        super().__init__(parent)
        self.setObjectName("card")
        self._interactive = interactive
        if interactive:
            self.setCursor(Qt.PointingHandCursor)
        self._apply_hover(False)

    def _apply_hover(self, hovered: bool) -> None:
        border = "rgba(255,255,255,28)" if hovered and self._interactive else tokens.BORDER_SUBTLE
        bg = "#141416" if hovered and self._interactive else tokens.SURFACE
        self.setStyleSheet(
            f"QFrame#card{{background:{bg};border:1px solid {border};border-radius:{tokens.RADIUS_CARD}px;}}"
        )

    def enterEvent(self, event: QEvent) -> None:
        self._apply_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._apply_hover(False)
        super().leaveEvent(event)


class StatCard(Card):
    clicked = Signal()

    def __init__(self, icon_name: str, title: str, parent: QWidget | None = None, interactive: bool = True):
        super().__init__(parent, interactive=interactive)
        self._clickable = interactive
        self.setMinimumHeight(144)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 15)
        layout.setSpacing(5)
        top = QHBoxLayout()
        self.icon_label = QLabel()
        self.icon_label.setPixmap(icon(icon_name, tokens.ACCENT, 23).pixmap(23, 23))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet(f"background:{tokens.ACCENT_SOFT};border:1px solid {tokens.ACCENT_DARK};border-radius:20px;")
        top.addWidget(self.icon_label)
        top.addStretch()
        if interactive:
            arrow = QLabel()
            arrow.setPixmap(icon("arrow_right", tokens.MUTED, 17).pixmap(17, 17))
            top.addWidget(arrow)
        layout.addLayout(top)
        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")
        layout.addWidget(self.title)
        self.value = QLabel("0")
        self.value.setObjectName("bigNumber")
        layout.addWidget(self.value)
        self.meta = QLabel("")
        self.meta.setObjectName("secondary")
        layout.addWidget(self.meta)

    def set_data(self, value: str, meta: str = "", meta_accent: bool = False) -> None:
        self.value.setText(value)
        self.meta.setText(meta)
        self.meta.setStyleSheet(f"color:{tokens.ACCENT if meta_accent else tokens.TEXT2};")

    def mouseReleaseEvent(self, event) -> None:
        if self._clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class SessionRow(QWidget):
    clicked = Signal(int)
    context_requested = Signal(int, object)

    def __init__(self, session: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.session_id = int(session["id"])
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(64)
        self.setStyleSheet("QWidget:hover{background:rgba(255,255,255,5);border-radius:12px;}")
        l = QHBoxLayout(self)
        l.setContentsMargins(7, 4, 7, 4)
        l.setSpacing(12)
        time = QLabel(format_time(session.get("start_time", "")))
        time.setFixedWidth(52)
        time.setStyleSheet(f"color:{tokens.TEXT2};font-size:14px;")
        l.addWidget(time)
        dot = QLabel("●")
        dot.setFixedWidth(12)
        dot.setStyleSheet(f"color:{tokens.ACCENT};font-size:11px;")
        l.addWidget(dot)
        texts = QVBoxLayout(); texts.setSpacing(2)
        title = QLabel(session.get("subject", tr("Lesson"))); title.setStyleSheet("font-size:14px;font-weight:600;")
        subtitle_parts = [session.get("student_name") or tr("Unassigned"), self._duration(session)]
        if session.get("session_type") and session.get("session_type") != "Lesson":
            subtitle_parts.append(enum_display(session["session_type"]))
        attendance = session.get("attendance") or "Not marked"
        if attendance != "Not marked":
            subtitle_parts.append(enum_display(attendance))
        subtitle = QLabel(" · ".join(x for x in subtitle_parts if x))
        subtitle.setObjectName("muted")
        texts.addWidget(title); texts.addWidget(subtitle)
        l.addLayout(texts, 1)
        status = session.get("status", "Upcoming")
        needs_review = bool(session.get("needs_review"))
        badge = QLabel(tr("Needs review") if needs_review else enum_display(status))
        badge.setAlignment(Qt.AlignCenter)
        badge.setContentsMargins(10, 5, 10, 5)
        color, bg = ((tokens.WARNING, "#2A2111") if needs_review else self._status_colors(status))
        badge.setStyleSheet(f"color:{color};background:{bg};border:1px solid rgba(255,255,255,8);border-radius:11px;")
        l.addWidget(badge)

    @staticmethod
    def _duration(session: dict) -> str:
        try:
            a = datetime.strptime(session["start_time"], "%H:%M")
            b = datetime.strptime(session["end_time"], "%H:%M")
            mins = int((b-a).total_seconds()/60)
            if mins <= 0:
                return ""
            return format_duration(mins)
        except Exception:
            return ""

    @staticmethod
    def _status_colors(status: str) -> tuple[str, str]:
        return {
            "Completed": (tokens.SUCCESS, "#10231A"),
            "In Progress": (tokens.ACCENT, "#2A1A0F"),
            "Cancelled": (tokens.ERROR, "#281313"),
            "Upcoming": (tokens.TEXT2, "#1B1B1E"),
        }.get(status, (tokens.TEXT2, "#1B1B1E"))

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.session_id)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        self.context_requested.emit(self.session_id, event.globalPos())
        event.accept()


class LessonChip(QFrame):
    """Compact schedule event used inside week columns."""

    clicked = Signal(int)
    context_requested = Signal(int, object)

    def __init__(self, session: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self.session_id = int(session["id"])
        self.setCursor(Qt.PointingHandCursor)
        status = session.get("status", "Upcoming")
        needs_review = bool(session.get("needs_review"))
        edge = tokens.WARNING if needs_review else {
            "Completed": tokens.SUCCESS,
            "In Progress": tokens.ACCENT,
            "Cancelled": tokens.ERROR,
        }.get(status, tokens.ACCENT)
        self.setStyleSheet(
            f"QFrame{{background:#171719;border:1px solid rgba(255,255,255,12);"
            f"border-left:2px solid {edge};border-radius:12px;}}"
            "QFrame:hover{background:#1D1D20;border-color:rgba(255,255,255,26);}"
        )
        l = QVBoxLayout(self); l.setContentsMargins(10,8,9,8); l.setSpacing(2)
        top = QHBoxLayout(); top.setSpacing(5)
        tm = QLabel(format_time(session.get("start_time", ""))); tm.setStyleSheet(f"color:{tokens.ACCENT};font-size:11px;font-weight:600;")
        top.addWidget(tm); top.addStretch()
        if needs_review:
            review = QLabel(tr("REVIEW")); review.setStyleSheet(f"color:{tokens.WARNING};font-size:9px;font-weight:700;")
            top.addWidget(review)
        elif status == "In Progress":
            live = QLabel(tr("LIVE")); live.setStyleSheet(f"color:{tokens.ACCENT};font-size:9px;font-weight:700;")
            top.addWidget(live)
        l.addLayout(top)
        subject = QLabel(session.get("subject", tr("Lesson"))); subject.setWordWrap(True); subject.setStyleSheet("font-size:12px;font-weight:600;")
        l.addWidget(subject)
        student_text = session.get("student_name") or tr("Unassigned")
        attendance = session.get("attendance") or "Not marked"
        if attendance != "Not marked":
            student_text += f" · {enum_display(attendance)}"
        student = QLabel(student_text); student.setObjectName("muted"); student.setWordWrap(True)
        l.addWidget(student)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.session_id)
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        self.context_requested.emit(self.session_id, event.globalPos())
        event.accept()


class InsightCard(Card):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setMinimumHeight(290)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 28, 30, 28)
        top = QHBoxLayout()
        spark = QLabel(); spark.setPixmap(icon("sparkles", tokens.ACCENT, 18).pixmap(18,18))
        tag = QLabel(tr("MENTOR INSIGHT")); tag.setObjectName("eyebrow")
        top.addWidget(spark); top.addWidget(tag); top.addStretch(); layout.addLayout(top)
        layout.addStretch()
        self.text = QLabel(tr("A good teacher\ncan change the world\none student at a time."))
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setWordWrap(True)
        self.text.setStyleSheet(f"font-size:18px;color:{tokens.TEXT2};line-height:1.4;")
        layout.addWidget(self.text)
        line = QFrame(); line.setFixedSize(44, 2); line.setStyleSheet(f"background:{tokens.ACCENT};border:none;")
        row = QHBoxLayout(); row.addStretch(); row.addWidget(line); row.addStretch(); layout.addLayout(row)
        layout.addStretch()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c = QColor(tokens.ACCENT); c.setAlpha(66); pen = QPen(c, 42)
        p.setPen(pen)
        r = self.rect().adjusted(self.width()-170, -130, 105, -self.height()+145)
        p.drawEllipse(r)
        c2 = QColor(tokens.ACCENT); c2.setAlpha(22); pen.setColor(c2); pen.setWidth(55); p.setPen(pen)
        p.drawArc(self.rect().adjusted(-160, self.height()-170, -self.width()+160, 150), 0, 180*16)
        p.end()


class QuickActionButton(QPushButton):
    def __init__(self, icon_name: str, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setIcon(icon(icon_name, tokens.ACCENT, 20))
        self.setIconSize(QSize(20, 20))
        self.setMinimumHeight(62)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton{{background:#171719;border:1px solid rgba(255,255,255,10);border-radius:14px;"
            f"color:{tokens.TEXT2};padding:10px 12px;}}"
            f"QPushButton:hover{{background:#1E1E21;border-color:{tokens.ACCENT};color:{tokens.TEXT};}}"
            "QPushButton:pressed{background:#242428;}"
        )


class SegmentedControl(QFrame):
    changed = Signal(str)

    def __init__(self, items: list[tuple[str, str]], selected: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFixedHeight(38)
        self.setStyleSheet("QFrame{background:#121214;border:1px solid rgba(255,255,255,14);border-radius:19px;}")
        self._selected = selected
        self._buttons: dict[str, QPushButton] = {}
        self._indicator = QFrame(self)
        self._indicator.setStyleSheet("background:#29292D;border:1px solid rgba(255,255,255,20);border-radius:16px;")
        self._indicator.lower()
        self._anim = QPropertyAnimation(self._indicator, b"geometry", self)
        self._anim.setDuration(tokens.ANIM_NORMAL)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        l = QHBoxLayout(self); l.setContentsMargins(3,3,3,3); l.setSpacing(1)
        for key, label in items:
            b = QPushButton(label)
            b.setFixedHeight(32)
            b.setMinimumWidth(68)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton{background:transparent;border:none;border-radius:16px;padding:5px 11px;}QPushButton:hover{background:rgba(255,255,255,5);}")
            b.clicked.connect(lambda _=False, k=key: self.select(k))
            l.addWidget(b); self._buttons[key] = b
        QTimer.singleShot(0, lambda: self.select(selected, animate=False, emit=False))

    @property
    def selected(self) -> str:
        return self._selected

    def select(self, key: str, animate: bool = True, emit: bool = True) -> None:
        if key not in self._buttons:
            return
        changed = key != self._selected
        self._selected = key
        for k, b in self._buttons.items():
            b.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;border-radius:16px;padding:5px 11px;"
                f"color:{tokens.TEXT if k == key else tokens.TEXT2};font-weight:{'600' if k == key else '400'};}}"
                "QPushButton:hover{background:rgba(255,255,255,5);}"
            )
            b.raise_()
        target = self._buttons[key].geometry()
        if target.width() <= 0:
            return
        if animate:
            self._anim.stop(); self._anim.setStartValue(self._indicator.geometry()); self._anim.setEndValue(target); self._anim.start()
        else:
            self._indicator.setGeometry(target)
        self._indicator.show(); self._indicator.lower()
        if emit and changed:
            self.changed.emit(key)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._selected in self._buttons:
            self._indicator.setGeometry(self._buttons[self._selected].geometry())
            self._indicator.lower()
            for b in self._buttons.values(): b.raise_()


class DockButton(QToolButton):
    def __init__(self, key: str, icon_name: str, label: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.key = key
        self.icon_name = icon_name
        self.setText(label)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(96, 58)
        self.setIconSize(QSize(21,21))
        self.update_state(False)

    def update_state(self, checked: bool) -> None:
        self.setIcon(icon(self.icon_name, tokens.ACCENT if checked else tokens.TEXT2, 21))
        self.setStyleSheet(
            f"QToolButton{{background:transparent;border:none;border-radius:24px;color:{tokens.ACCENT if checked else tokens.TEXT2};"
            f"font-size:11px;font-weight:{'600' if checked else '400'};padding:5px 8px;}}"
            f"QToolButton:hover{{background:rgba(255,255,255,6);color:{tokens.TEXT if not checked else tokens.ACCENT_BRIGHT};}}"
        )


class FloatingDock(QFrame):
    navigate = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("floatingDock")
        self.setFixedHeight(78)
        self.setMinimumWidth(550)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 135))
        self.setGraphicsEffect(shadow)

        self.indicator = QFrame(self)
        self.indicator.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.indicator.setStyleSheet(
            f"background:{tokens.ACCENT_SOFT};"
            f"border:1px solid {tokens.ACCENT_DARK};"
            "border-radius:25px;"
        )
        self.indicator.setGeometry(10, 10, 100, 58)
        self.indicator.lower()

        self._indicator_anim = QPropertyAnimation(self.indicator, b"geometry", self)
        self._indicator_anim.setDuration(tokens.ANIM_NORMAL)
        self._indicator_anim.setEasingCurve(QEasingCurve.OutCubic)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(2)
        definitions = [
            ("home", "home", tr("Home")),
            ("schedule", "calendar", tr("Schedule")),
            ("notes", "note", tr("Notes")),
            ("materials", "folder", tr("Materials")),
            ("statistics", "stats", tr("Stats")),
        ]
        self.buttons: dict[str, DockButton] = {}
        for key, icon_name, label in definitions:
            button = DockButton(key, icon_name, label)
            button.setFocusPolicy(Qt.NoFocus)
            button.clicked.connect(lambda _=False, k=key: self.navigate.emit(k))
            layout.addWidget(button)
            self.buttons[key] = button

        self._selected = "home"
        QTimer.singleShot(0, lambda: self.select("home", animate=False))

    def paintEvent(self, event) -> None:
        # Keep the dock deliberately clean. The previous decorative arc looked
        # like a rendering defect on some Windows scaling configurations.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        alpha = tokens.glass_alpha()
        gradient.setColorAt(0.0, QColor(25, 25, 28, alpha))
        gradient.setColorAt(0.55, QColor(15, 15, 17, alpha))
        gradient.setColorAt(1.0, QColor(18, 16, 15, alpha))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor(255, 255, 255, 22), 1))
        painter.drawRoundedRect(rect, 37, 37)
        painter.end()

    def select(self, key: str, animate: bool = True) -> None:
        if key not in self.buttons:
            return
        self._selected = key
        for button_key, button in self.buttons.items():
            button.update_state(button_key == key)
            button.raise_()

        target = self.buttons[key].geometry()
        if target.width() <= 0:
            return
        target = QRect(target.x(), target.y(), target.width(), target.height())
        if animate and self.indicator.isVisible():
            self._indicator_anim.stop()
            self._indicator_anim.setStartValue(self.indicator.geometry())
            self._indicator_anim.setEndValue(target)
            self._indicator_anim.start()
        else:
            self.indicator.setGeometry(target)
        self.indicator.show()
        self.indicator.lower()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._selected in self.buttons:
            self.indicator.setGeometry(self.buttons[self._selected].geometry())
            self.indicator.lower()
            for button in self.buttons.values():
                button.raise_()


class QuickCreatePopover(QDialog):
    """Frameless quick-create popup with one clean rounded surface.

    A custom popup avoids the inconsistent native QMenu outlines seen on
    different Windows scaling/theme combinations.
    """

    action_triggered = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(False)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        surface = QFrame()
        surface.setObjectName("quickCreateSurface")
        surface.setStyleSheet(
            "QFrame#quickCreateSurface{"
            "background:#171719;"
            "border:1px solid rgba(255,255,255,24);"
            "border-radius:18px;"
            "}"
        )
        shadow = QGraphicsDropShadowEffect(surface)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 9)
        shadow.setColor(QColor(0, 0, 0, 155))
        surface.setGraphicsEffect(shadow)
        outer.addWidget(surface)

        layout = QVBoxLayout(surface)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(3)

        heading = QLabel(tr("QUICK CREATE"))
        heading.setObjectName("eyebrow")
        heading.setContentsMargins(10, 6, 10, 5)
        layout.addWidget(heading)

        actions = [
            ("calendar_add", tr("New Lesson"), "add_session", True),
            ("people", tr("New Student"), "add_student", False),
            ("note", tr("New Note"), "add_note", False),
            ("task", tr("Assign Homework"), "add_assignment", True),
            ("task", tr("New Task"), "new_task", False),
            ("star", tr("New Goal"), "new_goal", False),
            ("folder", tr("Add Material"), "add_material", False),
        ]
        for icon_name, label, action, accented in actions:
            button = QPushButton(label)
            button.setIcon(icon(icon_name, tokens.ACCENT if accented else tokens.TEXT2, 18))
            button.setIconSize(QSize(18, 18))
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
            button.setMinimumSize(224, 42)
            button.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;border-radius:11px;"
                f"padding:8px 10px;text-align:left;color:{tokens.TEXT};}}"
                "QPushButton:hover{background:rgba(255,255,255,8);}"
                f"QPushButton:pressed{{background:{tokens.ACCENT_SOFT};}}"
            )
            button.clicked.connect(lambda _=False, a=action: self._trigger(a))
            layout.addWidget(button)

        separator = QFrame()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background:rgba(255,255,255,12);border:none;margin:5px 8px;")
        layout.addWidget(separator)

        focus = QPushButton(tr("Focus Timer"))
        focus.setIcon(icon("timer", tokens.TEXT2, 18))
        focus.setIconSize(QSize(18, 18))
        focus.setCursor(Qt.PointingHandCursor)
        focus.setFocusPolicy(Qt.NoFocus)
        focus.setMinimumSize(224, 42)
        focus.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;border-radius:11px;"
            f"padding:8px 10px;text-align:left;color:{tokens.TEXT};}}"
            "QPushButton:hover{background:rgba(255,255,255,8);}"
            "QPushButton:pressed{background:rgba(255,255,255,12);}"
        )
        focus.clicked.connect(lambda: self._trigger("focus"))
        layout.addWidget(focus)

        self.adjustSize()

    def _trigger(self, action: str) -> None:
        self.close()
        self.action_triggered.emit(action)

    def open_for(self, anchor: QWidget) -> None:
        self.adjustSize()
        bottom_right = anchor.mapToGlobal(QPoint(anchor.width(), anchor.height() + 7))
        self.move(bottom_right.x() - self.width(), bottom_right.y())
        self.show()
        self.raise_()


class LessonContextPopover(QDialog):
    """Small frameless lesson action menu used for right-click interactions."""

    action_triggered = Signal(str, int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._session_id = 0
        outer = QVBoxLayout(self); outer.setContentsMargins(10,10,10,10)
        surface = QFrame(); surface.setObjectName("lessonContextSurface")
        surface.setStyleSheet(
            "QFrame#lessonContextSurface{background:#171719;border:1px solid rgba(255,255,255,24);border-radius:17px;}"
        )
        shadow = QGraphicsDropShadowEffect(surface); shadow.setBlurRadius(26); shadow.setOffset(0,8); shadow.setColor(QColor(0,0,0,150)); surface.setGraphicsEffect(shadow)
        outer.addWidget(surface)
        self.layout_box = QVBoxLayout(surface); self.layout_box.setContentsMargins(8,8,8,8); self.layout_box.setSpacing(2)
        self.buttons: dict[str, QPushButton] = {}
        definitions = [
            ("open", "arrow_right", tr("Open Lesson"), False),
            ("wrap_up", "check", tr("Complete / Wrap Up"), True),
            ("duplicate", "plus", tr("Duplicate"), False),
            ("cancel", "close", tr("Cancel Lesson"), False),
            ("delete", "trash", tr("Delete"), False),
        ]
        for action, icon_name, label, accented in definitions:
            button = QPushButton(label); button.setIcon(icon(icon_name, tokens.ACCENT if accented else tokens.TEXT2, 16)); button.setIconSize(QSize(16,16)); button.setMinimumSize(205,39); button.setCursor(Qt.PointingHandCursor); button.setFocusPolicy(Qt.NoFocus)
            button.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;border-radius:10px;padding:7px 10px;text-align:left;color:{tokens.ERROR if action=='delete' else tokens.TEXT};}}"
                "QPushButton:hover{background:rgba(255,255,255,8);}"
            )
            button.clicked.connect(lambda _=False, a=action:self._trigger(a))
            self.layout_box.addWidget(button); self.buttons[action]=button
        self.adjustSize()

    def open_for(self, global_pos: QPoint, session_id: int, status: str) -> None:
        self._session_id = int(session_id)
        self.buttons["wrap_up"].setEnabled(status != "Cancelled")
        self.buttons["cancel"].setEnabled(status not in {"Cancelled", "Completed"})
        self.adjustSize(); self.move(global_pos); self.show(); self.raise_()

    def _trigger(self, action: str) -> None:
        session_id = self._session_id
        self.close(); self.action_triggered.emit(action, session_id)


class Toast(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setStyleSheet(
            f"background:#19191C;border:1px solid rgba(255,255,255,26);border-radius:15px;"
            f"padding:11px 16px;color:{tokens.TEXT};font-weight:500;"
        )
        self.setAlignment(Qt.AlignCenter)
        self._effect = QGraphicsOpacityEffect(self); self.setGraphicsEffect(self._effect)
        self._fade = QPropertyAnimation(self._effect, b"opacity", self)
        self._fade.setDuration(170); self._fade.setEasingCurve(QEasingCurve.OutCubic)
        self.hide()

    def show_message(self, text: str, duration_ms: int = 2200) -> None:
        self.setText(text); self.adjustSize()
        parent = self.parentWidget()
        if parent:
            x = parent.width() - self.width() - 28
            y = parent.height() - self.height() - 116
            self.move(max(20, x), max(20, y))
        self._fade.stop(); self._effect.setOpacity(0.0); self.show(); self.raise_()
        self._fade.setStartValue(0.0); self._fade.setEndValue(1.0); self._fade.start()
        QTimer.singleShot(duration_ms, self._fade_out)

    def _fade_out(self) -> None:
        if not self.isVisible():
            return
        self._fade.stop(); self._fade.setStartValue(self._effect.opacity()); self._fade.setEndValue(0.0)
        try:
            self._fade.finished.disconnect(self.hide)
        except (TypeError, RuntimeError):
            pass
        self._fade.finished.connect(self.hide)
        self._fade.start()