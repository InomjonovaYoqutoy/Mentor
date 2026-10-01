from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from . import __version__
from .core.logging_config import configure_logging
from .core.paths import database_path
from .database.database import Database
from .services.data_service import DataService
from .theme.preferences import apply_preferences
from .i18n import tr
from .ui.main_window import MainWindow

log = logging.getLogger(__name__)


class MentorApplication:
    def __init__(self):
        configure_logging()
        self.qt = QApplication(sys.argv)
        self.qt.setApplicationName("Mentor")
        self.qt.setApplicationVersion(__version__)
        self.qt.setOrganizationName("Mentor")
        self.qt.setStyle("Fusion")
        self.db = Database(database_path())
        self.service = DataService(self.db)
        apply_preferences(self.service)
        self.window = MainWindow(self.service)
        self._install_exception_hook()

    def _install_exception_hook(self):
        old_hook = sys.excepthook
        def hook(exc_type, exc, tb):
            log.exception("Unhandled application exception", exc_info=(exc_type, exc, tb))
            try:
                QMessageBox.critical(self.window, "Mentor", tr("Something went wrong. The technical details were written to the Mentor log."))
            except Exception:
                old_hook(exc_type, exc, tb)
        sys.excepthook = hook

    def run(self) -> int:
        log.info("Mentor starting")
        self.window.show()
        code = self.qt.exec()
        self.db.close()
        log.info("Mentor stopped")
        return code