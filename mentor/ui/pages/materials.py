from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QComboBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from ...services.data_service import DataService
from ...theme import tokens
from ...i18n import tr
from ..dialogs import MaterialDialog
from ..icons import icon
from ..widgets import Card


class MaterialsPage(QWidget):
    changed = Signal()

    def __init__(self, service: DataService, parent=None):
        super().__init__(parent)
        self.service=service;self.setAcceptDrops(True)
        root=QVBoxLayout(self);root.setContentsMargins(26,14,26,115);root.setSpacing(16)
        top=QHBoxLayout();titles=QVBoxLayout();titles.setSpacing(2)
        title=QLabel(tr("Materials"));title.setObjectName("pageTitle");sub=QLabel(tr("Keep teaching files findable without duplicating them."));sub.setObjectName("secondary")
        titles.addWidget(title);titles.addWidget(sub);top.addLayout(titles);top.addStretch()
        add=QPushButton(tr("Add Material"));add.setIcon(icon("plus","#111111",17));add.setObjectName("primary");add.clicked.connect(self.add_material);top.addWidget(add);root.addLayout(top)

        drop=Card();dl=QHBoxLayout(drop);dl.setContentsMargins(16,12,16,12);ico=QLabel();ico.setPixmap(icon("folder",tokens.ACCENT,21).pixmap(21,21));dl.addWidget(ico)
        text=QVBoxLayout();t=QLabel(tr("Drop a file anywhere on this page"));t.setStyleSheet("font-weight:600;");s=QLabel(tr("Mentor stores its path locally — your original file stays where it is."));s.setObjectName("secondary");text.addWidget(t);text.addWidget(s);dl.addLayout(text,1);root.addWidget(drop)

        panel=Card();pl=QVBoxLayout(panel);pl.setContentsMargins(15,15,15,15);pl.setSpacing(12)
        filters=QHBoxLayout();si=QLabel();si.setPixmap(icon("search",tokens.MUTED,17).pixmap(17,17));self.search=QLineEdit();self.search.setPlaceholderText(tr("Search materials…"));self.search.textChanged.connect(self.refresh)
        self.category=QComboBox();
        for value in ["All","General","Math","Physics","English","Computer Science","Other"]: self.category.addItem(tr(value), value)
        self.category.currentIndexChanged.connect(self.refresh)
        filters.addWidget(si);filters.addWidget(self.search,1);filters.addWidget(self.category);pl.addLayout(filters)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels([tr("Name"),tr("Category"),tr("Student"),tr("Location"),tr("Status")]);self.table.horizontalHeader().setStretchLastSection(True);self.table.setSelectionBehavior(QTableWidget.SelectRows);self.table.setEditTriggers(QTableWidget.NoEditTriggers);self.table.doubleClicked.connect(self.open_selected);pl.addWidget(self.table,1)
        actions=QHBoxLayout();edit=QPushButton(tr("Edit"));openb=QPushButton(tr("Open"));reveal=QPushButton(tr("Reveal in Explorer"));delete=QPushButton(tr("Remove"));delete.setObjectName("danger");edit.clicked.connect(self.edit_selected);openb.clicked.connect(self.open_selected);reveal.clicked.connect(self.reveal_selected);delete.clicked.connect(self.delete_selected);actions.addStretch();[actions.addWidget(x) for x in(edit,openb,reveal,delete)];pl.addLayout(actions);root.addWidget(panel,1);self.refresh()

    def refresh(self):
        rows=self.service.materials(self.search.text(),self.category.currentData() or "All");self.table.setProperty("rows",rows);self.table.setRowCount(len(rows))
        for r,m in enumerate(rows):
            exists=self._exists(m["path"]);vals=[m["name"],m.get("category") or "",m.get("student_name") or "—",m["path"],tr("Available") if exists else tr("Missing")]
            for c,v in enumerate(vals):
                item=QTableWidgetItem(str(v))
                if c==4:item.setForeground(QColor(tokens.TEXT2 if exists else tokens.ERROR))
                self.table.setItem(r,c,item)
        self.table.resizeColumnsToContents();self.table.horizontalHeader().setStretchLastSection(True)

    def selected(self):
        r=self.table.currentRow();rows=self.table.property("rows") or [];return rows[r] if 0<=r<len(rows) else None

    @staticmethod
    def _exists(path):return path.startswith("http://") or path.startswith("https://") or Path(path).exists()

    def add_material(self,path=""):
        d=MaterialDialog(self.service,str(path) if path else "",parent=self)
        if d.exec()==d.Accepted:self.service.save_material(d.data());self.refresh();self.changed.emit()

    def edit_selected(self):
        m=self.selected()
        if not m:return
        d=MaterialDialog(self.service,material=m,parent=self)
        if d.exec()==d.Accepted:self.service.save_material(d.data(),m["id"]);self.refresh();self.changed.emit()

    def open_selected(self,*_):
        m=self.selected()
        if not m:return
        p=m["path"]
        if p.startswith("http://") or p.startswith("https://"):QDesktopServices.openUrl(QUrl(p));return
        if not Path(p).exists():QMessageBox.warning(self,tr("Missing file"),tr("This file was moved or deleted outside Mentor."));return
        QDesktopServices.openUrl(QUrl.fromLocalFile(p))

    def reveal_selected(self):
        m=self.selected()
        if not m:return
        if m["path"].startswith(("http://","https://")):QDesktopServices.openUrl(QUrl(m["path"]));return
        p=Path(m["path"])
        if not p.exists():QMessageBox.warning(self,tr("Missing file"),tr("This file no longer exists at the saved location."));return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))

    def delete_selected(self):
        m=self.selected()
        if m and QMessageBox.question(self,tr("Remove material"),tr("Remove this material from Mentor? The original file will not be deleted."))==QMessageBox.Yes:self.service.delete_material(m["id"]);self.refresh();self.changed.emit()

    def select_material(self,material_id:int):
        rows=self.table.property("rows") or []
        for i,row in enumerate(rows):
            if row.get("id")==material_id:self.table.selectRow(i);self.table.scrollToItem(self.table.item(i,0));return

    def dragEnterEvent(self,event):
        if event.mimeData().hasUrls():event.acceptProposedAction()

    def dropEvent(self,event):
        urls=[u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if urls:self.add_material(urls[0]);event.acceptProposedAction()