"""Load and apply Mentor appearance preferences."""
from __future__ import annotations

from PySide6.QtWidgets import QApplication

from ..i18n import configure_region, set_language
from ..services.data_service import DataService
from . import tokens
from .stylesheet import app_stylesheet


def apply_preferences(service: DataService, *, refresh_stylesheet: bool = True) -> None:
    set_language(service.get_setting("language", "en"))
    configure_region(
        use_24h=service.get_setting("time_24h", "1") != "0",
        week_start=service.get_setting("week_start", "monday"),
    )
    tokens.apply_preferences(
        accent=service.get_setting("accent", "orange"),
        density=service.get_setting("density", "comfortable"),
        glass=service.get_setting("glass", "standard"),
        motion=service.get_setting("motion", "full"),
        ambient_glow=service.get_setting("ambient_glow", "1") != "0",
    )
    if refresh_stylesheet:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(app_stylesheet())