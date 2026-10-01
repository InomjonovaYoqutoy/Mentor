from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ...services.data_service import DataService
from ...theme import tokens
from ...i18n import tr
from ..icons import icon
from ..widgets import Card


class NotesPage(QWidget):
    changed = Signal()

    def __init__(self, service: DataService, parent=None):
        super().__init__(parent)
        self.service = service
        self.current_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 14, 26, 115)
        root.setSpacing(16)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        title = QLabel(tr("Notes"))
        title.setObjectName("pageTitle")
        subtitle = QLabel(tr("A quiet workspace for teaching notes and ideas."))
        subtitle.setObjectName("secondary")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()

        new_button = QPushButton(tr("New Note"))
        new_button.setIcon(icon("plus", "#111111", 17))
        new_button.setObjectName("primary")
        new_button.clicked.connect(self.new_note)
        header.addWidget(new_button)
        root.addLayout(header)

        # One cohesive workspace surface. The previous version put two rounded
        # cards directly next to each other inside a splitter, which visually
        # read as two windows colliding. This keeps the split interaction while
        # presenting a single, calm workspace.
        workspace = Card()
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(
            "QSplitter{background:transparent;border:none;}"
            "QSplitter::handle{background:rgba(255,255,255,12);margin:18px 0;}"
        )

        left = QWidget()
        left.setMinimumWidth(255)
        left.setMaximumWidth(430)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 14, 16)
        left_layout.setSpacing(10)

        search_row = QHBoxLayout()
        search_row.setSpacing(8)
        search_icon = QLabel()
        search_icon.setPixmap(icon("search", tokens.MUTED, 17).pixmap(17, 17))
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("Search notes…"))
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(search_icon)
        search_row.addWidget(self.search, 1)
        left_layout.addLayout(search_row)

        self.list = QListWidget()
        self.list.setSpacing(1)
        self.list.currentItemChanged.connect(self.load_selected)
        self.list.setStyleSheet(
            "QListWidget{background:transparent;border:none;padding:0;}"
            "QListWidget::item{border-radius:10px;padding:10px 9px;margin:1px 0;}"
            "QListWidget::item:hover{background:rgba(255,255,255,6);}"
            f"QListWidget::item:selected{{background:{tokens.ACCENT_SOFT};color:{tokens.TEXT};}}"
        )
        left_layout.addWidget(self.list, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(22, 18, 20, 18)
        right_layout.setSpacing(12)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr("Untitled note"))
        self.title_edit.setStyleSheet(
            f"QLineEdit{{font-size:20px;font-weight:600;background:transparent;border:none;"
            f"border-bottom:1px solid {tokens.BORDER_SUBTLE};border-radius:0;padding:8px 2px;}}"
            f"QLineEdit:focus{{border:none;border-bottom:1px solid {tokens.ACCENT};}}"
        )
        self.pin = QCheckBox(tr("Pinned"))
        self.archive = QCheckBox(tr("Archived"))
        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(self.pin)
        title_row.addWidget(self.archive)
        right_layout.addLayout(title_row)

        meta = QHBoxLayout()
        meta.setSpacing(8)
        self.subject = QLineEdit()
        self.subject.setPlaceholderText(tr("Subject"))
        self.tags = QLineEdit()
        self.tags.setPlaceholderText(tr("Tags · comma separated"))
        self.student = QComboBox()
        self.student.addItem(tr("No student"), None)
        meta.addWidget(self.subject, 1)
        meta.addWidget(self.tags, 1)
        meta.addWidget(self.student, 1)
        right_layout.addLayout(meta)

        self.body = QTextEdit()
        self.body.setPlaceholderText(tr("Write your teaching note…"))
        self.body.setAcceptRichText(False)
        self.body.setStyleSheet(
            f"QTextEdit{{background:transparent;border:none;padding:10px 4px;"
            f"font-size:14px;color:{tokens.TEXT};}}"
            f"QTextEdit:focus{{border:none;background:rgba(255,255,255,2);}}"
        )
        right_layout.addWidget(self.body, 1)

        footer_line = QFrame()
        footer_line.setFixedHeight(1)
        footer_line.setStyleSheet("background:rgba(255,255,255,10);border:none;")
        right_layout.addWidget(footer_line)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.delete = QPushButton(tr("Delete"))
        self.delete.setObjectName("danger")
        self.delete.clicked.connect(self.delete_note)
        self.status = QLabel(tr("Ctrl+S to save"))
        self.status.setObjectName("muted")
        save = QPushButton(tr("Save Note"))
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        actions.addWidget(self.delete)
        actions.addWidget(self.status)
        actions.addStretch()
        actions.addWidget(save)
        right_layout.addLayout(actions)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 900])
        workspace_layout.addWidget(splitter)
        root.addWidget(workspace, 1)

        self.refresh_students()
        self.refresh()
        self.new_note()


    def draft_snapshot(self) -> dict:
        """Capture the editor state so a live language/theme rebuild cannot lose unsaved text."""
        return {
            "current_id": self.current_id,
            "title": self.title_edit.text(),
            "subject": self.subject.text(),
            "tags": self.tags.text(),
            "content": self.body.toPlainText(),
            "pinned": self.pin.isChecked(),
            "archived": self.archive.isChecked(),
            "student_id": self.student.currentData(),
        }

    def restore_draft_snapshot(self, state: dict | None) -> None:
        if not state:
            return
        self.current_id = state.get("current_id")
        self.title_edit.setText(state.get("title") or "")
        self.subject.setText(state.get("subject") or "")
        self.tags.setText(state.get("tags") or "")
        self.body.setPlainText(state.get("content") or "")
        self.pin.setChecked(bool(state.get("pinned")))
        self.archive.setChecked(bool(state.get("archived")))
        index = self.student.findData(state.get("student_id"))
        self.student.setCurrentIndex(index if index >= 0 else 0)
        if self.current_id is not None:
            for row in range(self.list.count()):
                item = self.list.item(row)
                if item.data(Qt.UserRole) == self.current_id:
                    self.list.blockSignals(True)
                    self.list.setCurrentItem(item)
                    self.list.blockSignals(False)
                    break
        self._sync_actions()

    def refresh_students(self) -> None:
        current = self.student.currentData()
        self.student.blockSignals(True)
        self.student.clear()
        self.student.addItem(tr("No student"), None)
        for student in self.service.students(active_only=True):
            self.student.addItem(student["name"], student["id"])
        index = self.student.findData(current)
        self.student.setCurrentIndex(max(0, index))
        self.student.blockSignals(False)

    def refresh(self) -> None:
        current = self.current_id
        self.list.blockSignals(True)
        self.list.clear()
        selected_item: QListWidgetItem | None = None

        for note in self.service.notes(self.search.text()):
            marker = "★  " if note["pinned"] else ""
            subtitle = note.get("subject") or note.get("student_name") or tr("Note")
            item = QListWidgetItem(f"{marker}{note['title']}\n{subtitle}")
            item.setData(Qt.UserRole, note["id"])
            item.setSizeHint(QSize(0, 58))
            self.list.addItem(item)
            if note["id"] == current:
                selected_item = item

        self.list.blockSignals(False)
        if selected_item:
            self.list.setCurrentItem(selected_item)
        self._sync_actions()

    def _sync_actions(self) -> None:
        self.delete.setEnabled(self.current_id is not None)
        if self.current_id is None:
            self.status.setText(tr("New note · Ctrl+S to save"))
        else:
            self.status.setText(tr("Saved note · Ctrl+S to save changes"))

    def new_note(self, checked: bool = False, student_id: int | None = None) -> None:
        self.current_id = None
        self.list.blockSignals(True)
        self.list.clearSelection()
        self.list.setCurrentItem(None)
        self.list.blockSignals(False)
        self.title_edit.clear()
        self.subject.clear()
        self.tags.clear()
        self.body.clear()
        self.pin.setChecked(False)
        self.archive.setChecked(False)
        self.student.setCurrentIndex(0)
        if student_id is not None:
            index = self.student.findData(student_id)
            if index >= 0:
                self.student.setCurrentIndex(index)
                student = self.service.student(student_id)
                if student and student.get("subject"):
                    self.subject.setText(student["subject"])
        self._sync_actions()
        self.title_edit.setFocus()

    def load_selected(self, current, previous) -> None:
        if not current:
            return
        note = self.service.note(current.data(Qt.UserRole))
        if not note:
            return

        self.current_id = note["id"]
        self.title_edit.setText(note.get("title") or "")
        self.subject.setText(note.get("subject") or "")
        self.tags.setText(note.get("tags") or "")
        self.body.setPlainText(note.get("content") or "")
        self.pin.setChecked(bool(note.get("pinned")))
        self.archive.setChecked(bool(note.get("archived")))
        index = self.student.findData(note.get("student_id"))
        self.student.setCurrentIndex(max(0, index))
        self._sync_actions()

    def save(self) -> None:
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, tr("Missing title"), tr("Give this note a title before saving."))
            self.title_edit.setFocus()
            return

        data = {
            "student_id": self.student.currentData(),
            "session_id": None,
            "subject": self.subject.text(),
            "title": self.title_edit.text(),
            "content": self.body.toPlainText(),
            "tags": self.tags.text(),
            "pinned": self.pin.isChecked(),
            "archived": self.archive.isChecked(),
        }
        self.current_id = self.service.save_note(data, self.current_id)
        self.refresh()
        self.select_note(self.current_id)
        self.status.setText(tr("Saved"))
        self.changed.emit()

    def select_note(self, note_id: int) -> None:
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.UserRole) == note_id:
                self.list.setCurrentItem(item)
                self.list.scrollToItem(item)
                return

    def delete_note(self) -> None:
        if not self.current_id:
            return
        if QMessageBox.question(
            self,
            tr("Delete note"),
            tr("Delete this note? This cannot be undone."),
        ) != QMessageBox.Yes:
            return

        self.service.delete_note(self.current_id)
        self.new_note()
        self.refresh()
        self.changed.emit()