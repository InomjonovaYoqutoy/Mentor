from . import tokens


def app_stylesheet() -> str:
    control_v = tokens.control_vpad()
    button_v = tokens.button_vpad()
    return f"""
    * {{
        font-family: 'Segoe UI Variable', 'Segoe UI';
        font-size: 13px;
        color: {tokens.TEXT};
    }}
    QWidget {{ background: transparent; }}
    QMainWindow, QWidget#Root {{ background: {tokens.BG}; }}

    QLabel#muted {{ color: {tokens.MUTED}; }}
    QLabel#secondary {{ color: {tokens.TEXT2}; }}
    QLabel#eyebrow {{ color: {tokens.MUTED}; font-size: 11px; font-weight: 600; }}
    QLabel#pageTitle {{ font-size: 30px; font-weight: 600; letter-spacing: -0.2px; }}
    QLabel#sectionTitle {{ font-size: 16px; font-weight: 600; }}
    QLabel#cardTitle {{ font-size: 13px; color: {tokens.TEXT2}; }}
    QLabel#bigNumber {{ font-size: 29px; font-weight: 600; }}
    QLabel#dialogTitle {{ font-size: 21px; font-weight: 600; }}
    QLabel#dialogSubtitle {{ color: {tokens.TEXT2}; font-size: 12px; }}

    QFrame#card, QFrame#panel, QFrame#section {{
        background: {tokens.SURFACE};
        border: 1px solid {tokens.BORDER_SUBTLE};
        border-radius: {tokens.RADIUS_CARD}px;
    }}
    QFrame#section {{ background: {tokens.SURFACE2}; border-radius: 16px; }}
    QFrame#hairline {{ background: rgba(255,255,255,12); border: none; max-height: 1px; }}

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QDateEdit, QTimeEdit,
    QSpinBox, QDoubleSpinBox {{
        background: {tokens.SURFACE2};
        border: 1px solid {tokens.BORDER};
        border-radius: 11px;
        padding: {control_v}px 11px;
        min-height: 20px;
        selection-background-color: {tokens.ACCENT_DARK};
    }}
    QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QComboBox:hover,
    QDateEdit:hover, QTimeEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
        border-color: {tokens.BORDER_HOVER};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
    QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {tokens.ACCENT};
        background: #181719;
    }}
    QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {{ color: {tokens.MUTED}; background: #101012; }}
    QComboBox::drop-down {{ border: none; width: 28px; }}
    QComboBox QAbstractItemView {{
        background: {tokens.SURFACE3}; border: 1px solid {tokens.BORDER}; border-radius: 10px;
        selection-background-color: {tokens.ACCENT_SOFT}; padding: 5px; outline: 0;
    }}

    QPushButton {{
        background: {tokens.SURFACE2};
        border: 1px solid {tokens.BORDER};
        border-radius: 11px;
        padding: {button_v}px 13px;
        min-height: 20px;
    }}
    QPushButton:hover {{ background: {tokens.HOVER}; border-color: {tokens.BORDER_HOVER}; }}
    QPushButton:pressed {{ background: {tokens.PRESSED}; }}
    QPushButton:disabled {{ color: #5F5F65; background: #101012; border-color: rgba(255,255,255,8); }}
    QPushButton#primary {{ background: {tokens.ACCENT}; color: #12100E; border: none; font-weight: 650; }}
    QPushButton#primary:hover {{ background: {tokens.ACCENT_BRIGHT}; }}
    QPushButton#primary:pressed {{ background: {tokens.ACCENT_DARK}; }}
    QPushButton#danger {{ color: {tokens.ERROR}; }}
    QPushButton#danger:hover {{ background: #271516; border-color: rgba(226,109,109,55); }}
    QPushButton#ghost {{ background: transparent; border: none; color: {tokens.TEXT2}; }}
    QPushButton#ghost:hover {{ background: {tokens.HOVER}; color: {tokens.TEXT}; }}
    QPushButton#pill {{ border-radius: 17px; padding: 6px 12px; min-height: 20px; }}
    QPushButton#pillChecked {{
        background: {tokens.ACCENT_SOFT}; color: {tokens.ACCENT}; border: 1px solid {tokens.ACCENT};
        border-radius: 17px; padding: 6px 12px; min-height: 20px; font-weight: 600;
    }}

    QToolButton {{ background: transparent; border: none; border-radius: 11px; padding: 7px; }}
    QToolButton:hover {{ background: {tokens.HOVER}; }}
    QToolButton:pressed {{ background: {tokens.PRESSED}; }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 7px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: #35353A; border-radius: 3px; min-height: 28px; }}
    QScrollBar::handle:vertical:hover {{ background: #4A4A50; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ background: transparent; height: 7px; }}
    QScrollBar::handle:horizontal {{ background: #35353A; border-radius: 3px; min-width: 28px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QListWidget, QTableWidget {{ background: transparent; border: none; outline: none; }}
    QListWidget::item {{ border-radius: 11px; padding: 9px; margin: 2px 0; }}
    QListWidget::item:selected {{ background: {tokens.ACCENT_SOFT}; color: {tokens.TEXT}; }}
    QListWidget::item:hover {{ background: {tokens.HOVER}; }}
    QHeaderView::section {{
        background: {tokens.SURFACE2}; color: {tokens.TEXT2}; border: none;
        border-bottom: 1px solid {tokens.BORDER_SUBTLE}; padding: 9px;
    }}
    QTableWidget::item {{ padding: 7px; border-bottom: 1px solid {tokens.BORDER_SUBTLE}; }}
    QTableWidget::item:selected {{ background: {tokens.ACCENT_SOFT}; }}

    QMenu {{ background: {tokens.SURFACE3}; border: 1px solid {tokens.BORDER}; border-radius: 12px; padding: 7px; }}
    QMenu::item {{ padding: 9px 28px 9px 12px; border-radius: 8px; }}
    QMenu::item:selected {{ background: {tokens.HOVER}; }}
    QMenu::separator {{ background: rgba(255,255,255,12); height: 1px; margin: 6px 8px; }}
    QToolTip {{ background: {tokens.SURFACE3}; color: {tokens.TEXT}; border: 1px solid {tokens.BORDER}; border-radius: 7px; padding: 6px; }}

    QProgressBar {{
        background: #0B0B0D; border: 1px solid {tokens.BORDER}; border-radius: 6px;
        height: 10px; text-align: center; color: transparent;
    }}
    QProgressBar::chunk {{ background: {tokens.ACCENT}; border-radius: 5px; }}

    QCheckBox {{ spacing: 9px; color: {tokens.TEXT2}; }}
    QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 1px solid #45454B; background: {tokens.SURFACE2}; }}
    QCheckBox::indicator:hover {{ border-color: #63636B; }}
    QCheckBox::indicator:checked {{ background: {tokens.ACCENT}; border-color: {tokens.ACCENT}; }}

    QCalendarWidget QWidget {{ alternate-background-color: {tokens.SURFACE2}; }}
    QCalendarWidget QAbstractItemView:enabled {{
        background: {tokens.SURFACE}; selection-background-color: {tokens.ACCENT}; selection-color: #111;
        border: none; outline: none;
    }}
    QCalendarWidget QToolButton {{ color: {tokens.TEXT}; font-weight: 600; }}
    QCalendarWidget QMenu {{ background: {tokens.SURFACE3}; }}

    QSplitter::handle {{ background: transparent; width: 1px; height: 1px; }}
    """