from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from .. import __version__
from ..core.paths import app_data_dir
from ..database.schema import SCHEMA_VERSION
from ..i18n import LANGUAGES, tr
from ..services.data_service import DataService
from ..theme import tokens
from ..theme.stylesheet import app_stylesheet


ACCENT_LABELS = {
    "orange": "Mentor Orange",
    "amber": "Warm Amber",
    "graphite": "Graphite",
    "blue": "Deep Blue",
    "violet": "Violet",
}


class SettingsDialog(QDialog):
    """One coherent settings surface with non-destructive live appearance preview."""

    preview_changed = Signal()

    def __init__(self, service: DataService, parent=None, initial_section: str = "general"):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle(tr("Settings"))
        self.setModal(True)
        self.setMinimumSize(820, 610)
        self.resize(900, 650)
        self.setStyleSheet(f"QDialog{{background:{tokens.BG2};}}")
        self._original = self._read_settings()

        root = QVBoxLayout(self); root.setContentsMargins(22,20,22,20); root.setSpacing(14)
        title = QLabel(tr("Settings")); title.setObjectName("dialogTitle")
        subtitle = QLabel(tr("Personalize Mentor and keep your local data safe.")); subtitle.setObjectName("dialogSubtitle")
        root.addWidget(title); root.addWidget(subtitle)

        content = QHBoxLayout(); content.setSpacing(14)
        self.categories = QListWidget(); self.categories.setFixedWidth(190); self.categories.setSpacing(2)
        self.categories.setStyleSheet(self._category_stylesheet())
        self.stack = QStackedWidget()
        sections = [
            ("general", tr("General"), self._general_page()),
            ("appearance", tr("Appearance"), self._appearance_page()),
            ("language", tr("Language & Region"), self._language_page()),
            ("data", tr("Data & Backup"), self._data_page()),
            ("about", tr("About"), self._about_page()),
        ]
        section_rows: dict[str, int] = {}
        for index, (key, label, page) in enumerate(sections):
            section_rows[key] = index
            self.categories.addItem(QListWidgetItem(label)); self.stack.addWidget(page)
        self.categories.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.categories.setCurrentRow(section_rows.get(initial_section, 0))
        content.addWidget(self.categories); content.addWidget(self.stack,1); root.addLayout(content,1)

        footer = QHBoxLayout(); footer.addStretch()
        cancel = QPushButton(tr("Cancel")); cancel.clicked.connect(self.reject)
        save = QPushButton(tr("Save Settings")); save.setObjectName("primary"); save.clicked.connect(self.accept)
        footer.addWidget(cancel); footer.addWidget(save); root.addLayout(footer)

    @staticmethod
    def _category_stylesheet() -> str:
        return (
            "QListWidget{background:#101012;border:1px solid rgba(255,255,255,12);border-radius:18px;padding:7px;}"
            "QListWidget::item{padding:10px 12px;border-radius:11px;}"
            f"QListWidget::item:selected{{background:{tokens.ACCENT_SOFT};color:{tokens.ACCENT};font-weight:600;}}"
        )

    @staticmethod
    def _card() -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(); frame.setObjectName("section")
        layout = QVBoxLayout(frame); layout.setContentsMargins(18,17,18,17); layout.setSpacing(12)
        return frame, layout

    def _section_heading(self, title: str, detail: str = "") -> tuple[QLabel, QLabel | None]:
        heading = QLabel(title); heading.setObjectName("sectionTitle")
        sub = None
        if detail:
            sub = QLabel(detail); sub.setObjectName("secondary"); sub.setWordWrap(True)
        return heading, sub

    def _general_page(self) -> QWidget:
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(3,3,3,3); l.setSpacing(12)
        card, box = self._card(); heading, sub = self._section_heading(tr("General"), tr("Personalize Mentor and keep your local data safe.")); box.addWidget(heading)
        if sub: box.addWidget(sub)
        form = QFormLayout(); form.setSpacing(12)
        self.name = QLineEdit(self.service.get_setting("profile_name","Shohjahon"))
        self.notifications = QCheckBox(tr("Enable in-app reminders")); self.notifications.setChecked(self.service.get_setting("notifications","1") != "0")
        form.addRow(tr("Display name"), self.name); form.addRow(tr("Notifications"), self.notifications); box.addLayout(form)
        l.addWidget(card); l.addStretch(); return page

    def _appearance_page(self) -> QWidget:
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(3,3,3,3); l.setSpacing(12)
        card, box = self._card(); heading, sub = self._section_heading(tr("Appearance"), tr("Changes preview immediately. Cancel restores your previous appearance.")); box.addWidget(heading)
        if sub: box.addWidget(sub)
        form = QFormLayout(); form.setSpacing(12)
        self.accent = QComboBox()
        current_accent = self.service.get_setting("accent","orange")
        for key, label in ACCENT_LABELS.items(): self.accent.addItem(tr(label), key)
        idx = self.accent.findData(current_accent); self.accent.setCurrentIndex(idx if idx >= 0 else 0)
        self.glass = QComboBox(); [(self.glass.addItem(tr(label), key)) for key,label in [("subtle","Subtle"),("standard","Standard"),("strong","Strong")]]
        self.glass.setCurrentIndex(max(0,self.glass.findData(self.service.get_setting("glass","standard"))))
        self.motion = QComboBox(); [(self.motion.addItem(tr(label), key)) for key,label in [("full","Full"),("reduced","Reduced"),("off","Off")]]
        self.motion.setCurrentIndex(max(0,self.motion.findData(self.service.get_setting("motion","full"))))
        self.density = QComboBox(); [(self.density.addItem(tr(label), key)) for key,label in [("comfortable","Comfortable"),("compact","Compact")]]
        self.density.setCurrentIndex(max(0,self.density.findData(self.service.get_setting("density","comfortable"))))
        self.glow = QCheckBox(tr("Atmospheric glow")); self.glow.setChecked(self.service.get_setting("ambient_glow","1") != "0")
        form.addRow(tr("Accent"), self.accent); form.addRow(tr("Glass intensity"), self.glass); form.addRow(tr("Motion"), self.motion); form.addRow(tr("Interface density"), self.density); form.addRow("", self.glow); box.addLayout(form)
        preview = QFrame(); preview.setFixedHeight(74); preview.setObjectName("settingsPreview")
        preview_layout = QHBoxLayout(preview); preview_layout.setContentsMargins(16,12,16,12)
        self.preview_dot = QLabel("●"); self.preview_dot.setStyleSheet(f"font-size:24px;color:{tokens.ACCENT};")
        self.preview_text = QLabel(tr("Mentor · Live Preview")); self.preview_text.setStyleSheet("font-size:15px;font-weight:600;")
        sample = QPushButton(tr("Save")); sample.setObjectName("primary"); sample.setEnabled(False)
        preview_layout.addWidget(self.preview_dot); preview_layout.addWidget(self.preview_text); preview_layout.addStretch(); preview_layout.addWidget(sample)
        box.addWidget(preview)
        for control in (self.accent,self.glass,self.motion,self.density): control.currentIndexChanged.connect(self._preview_appearance)
        self.glow.toggled.connect(self._preview_appearance)
        l.addWidget(card); l.addStretch(); return page

    def _language_page(self) -> QWidget:
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(3,3,3,3); l.setSpacing(12)
        card, box = self._card(); heading, sub = self._section_heading(tr("Language & Region"), tr("Language changes apply to the whole interface as soon as you save — no restart required.")); box.addWidget(heading)
        if sub: box.addWidget(sub)
        form = QFormLayout(); form.setSpacing(12)
        self.language = QComboBox()
        for code, name in LANGUAGES.items(): self.language.addItem(name, code)
        self.language.setCurrentIndex(max(0,self.language.findData(self.service.get_setting("language","en"))))
        self.time_format = QComboBox(); self.time_format.addItem("24-hour · 14:30", "24"); self.time_format.addItem("12-hour · 2:30 PM", "12")
        self.time_format.setCurrentIndex(0 if self.service.get_setting("time_24h","1") != "0" else 1)
        self.week_start = QComboBox(); self.week_start.addItem(tr("Monday"),"monday"); self.week_start.addItem(tr("Sunday"),"sunday")
        self.week_start.setCurrentIndex(max(0,self.week_start.findData(self.service.get_setting("week_start","monday"))))
        self.schedule_view = QComboBox(); self.schedule_view.addItem(tr("Week"),"week"); self.schedule_view.addItem(tr("Day"),"day")
        self.schedule_view.setCurrentIndex(max(0,self.schedule_view.findData(self.service.get_setting("default_schedule_view","week"))))
        form.addRow(tr("Language"), self.language); form.addRow(tr("Time format"), self.time_format); form.addRow(tr("Week starts on"), self.week_start); form.addRow(tr("Default schedule view"), self.schedule_view); box.addLayout(form)
        l.addWidget(card); l.addStretch(); return page

    def _data_page(self) -> QWidget:
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(3,3,3,3); l.setSpacing(12)
        card, box = self._card(); heading, sub = self._section_heading(tr("Data & Backup"), tr("Your workspace remains local. Backups are standard SQLite database files.")); box.addWidget(heading)
        if sub: box.addWidget(sub)
        row = QHBoxLayout();
        for text, callback in [(tr("Backup"),self.backup),(tr("Restore"),self.restore),(tr("Export JSON"),self.export_json),(tr("Students CSV"),self.export_csv)]:
            b=QPushButton(text); b.clicked.connect(callback); row.addWidget(b)
        row.addStretch(); box.addLayout(row)
        path = QLabel(str(app_data_dir())); path.setObjectName("muted"); path.setTextInteractionFlags(Qt.TextSelectableByMouse); box.addWidget(path)
        l.addWidget(card); l.addStretch(); return page

    def _about_page(self) -> QWidget:
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(3,3,3,3); l.setSpacing(12)
        card, box = self._card()
        brand = QLabel("MENTOR"); brand.setStyleSheet(f"font-size:25px;font-weight:700;color:{tokens.ACCENT};letter-spacing:2px;")
        box.addWidget(brand)
        desc = QLabel(tr("Local-first teaching productivity for Windows.")); desc.setObjectName("secondary"); box.addWidget(desc)
        form=QFormLayout(); form.setSpacing(11)
        version=QLabel(__version__); schema=QLabel(str(SCHEMA_VERSION)); path=QLabel(str(app_data_dir())); path.setTextInteractionFlags(Qt.TextSelectableByMouse); path.setWordWrap(True)
        form.addRow(tr("App version"),version); form.addRow(tr("Database schema"),schema); form.addRow(tr("App data"),path); box.addLayout(form)
        l.addWidget(card); l.addStretch(); return page

    def _read_settings(self) -> dict[str,str]:
        keys = ["profile_name","notifications","language","accent","glass","motion","density","ambient_glow","time_24h","week_start","default_schedule_view"]
        defaults = {"profile_name":"Shohjahon","notifications":"1","language":"en","accent":"orange","glass":"standard","motion":"full","density":"comfortable","ambient_glow":"1","time_24h":"1","week_start":"monday","default_schedule_view":"week"}
        return {k:self.service.get_setting(k,defaults[k]) for k in keys}

    def _preview_appearance(self, *_args) -> None:
        tokens.apply_preferences(
            accent=self.accent.currentData() or "orange", density=self.density.currentData() or "comfortable",
            glass=self.glass.currentData() or "standard", motion=self.motion.currentData() or "full",
            ambient_glow=self.glow.isChecked(),
        )
        app=QApplication.instance()
        if app: app.setStyleSheet(app_stylesheet())
        self.preview_text.setStyleSheet(f"font-size:15px;font-weight:600;color:{tokens.ACCENT};")
        self.preview_dot.setStyleSheet(f"font-size:24px;color:{tokens.ACCENT};")
        self.categories.setStyleSheet(self._category_stylesheet())
        parent=self.parentWidget()
        if parent is not None and hasattr(parent,"root"): parent.root.update()
        self.preview_changed.emit()

    def accept(self) -> None:
        values = {
            "profile_name": self.name.text().strip() or "Teacher", "notifications": "1" if self.notifications.isChecked() else "0",
            "language": self.language.currentData() or "en", "accent": self.accent.currentData() or "orange",
            "glass": self.glass.currentData() or "standard", "motion": self.motion.currentData() or "full",
            "density": self.density.currentData() or "comfortable", "ambient_glow": "1" if self.glow.isChecked() else "0",
            "time_24h": "1" if self.time_format.currentData()=="24" else "0", "week_start": self.week_start.currentData() or "monday",
            "default_schedule_view": self.schedule_view.currentData() or "week",
        }
        for key,value in values.items(): self.service.set_setting(key,str(value))
        super().accept()

    def reject(self) -> None:
        tokens.apply_preferences(
            accent=self._original["accent"], density=self._original["density"], glass=self._original["glass"], motion=self._original["motion"], ambient_glow=self._original["ambient_glow"] != "0"
        )
        app=QApplication.instance()
        if app: app.setStyleSheet(app_stylesheet())
        parent=self.parentWidget()
        if parent is not None and hasattr(parent,"root"): parent.root.update()
        super().reject()

    def backup(self) -> None:
        path,_=QFileDialog.getSaveFileName(self,tr("Backup Mentor database"),str(Path.home()/"mentor-backup.db"),"Database (*.db)")
        if path: self.service.backup_database(Path(path)); QMessageBox.information(self,tr("Backup created"),f"{tr('Backup saved to:')}\n{path}")

    def restore(self) -> None:
        path,_=QFileDialog.getOpenFileName(self,tr("Restore Mentor database"),str(Path.home()),"Database (*.db)")
        if not path:return
        if QMessageBox.question(self,tr("Restore database"),tr("This replaces the current Mentor database contents. Continue?"))==QMessageBox.Yes:
            self.service.restore_database(Path(path)); QMessageBox.information(self,tr("Restore complete"),tr("Database restored. Close settings to refresh the workspace."))

    def export_json(self) -> None:
        path,_=QFileDialog.getSaveFileName(self,tr("Export Mentor data"),str(Path.home()/"mentor-export.json"),"JSON (*.json)")
        if path:self.service.export_json(Path(path));QMessageBox.information(self,tr("Export complete"),f"{tr('Data exported to:')}\n{path}")

    def export_csv(self) -> None:
        path,_=QFileDialog.getSaveFileName(self,tr("Export students"),str(Path.home()/"mentor-students.csv"),"CSV (*.csv)")
        if path:self.service.export_students_csv(Path(path));QMessageBox.information(self,tr("Export complete"),f"{tr('Students exported to:')}\n{path}")