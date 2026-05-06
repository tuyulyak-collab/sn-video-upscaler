"""Global theme: soft pastel + glassmorphism palette and QSS for the desktop app."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# ---- Palette (pastel SaaS) -------------------------------------------------
SKY_BLUE = "#BFD7FF"
LAVENDER = "#D9CCFF"
BLUSH = "#FFD0E0"
PEACH = "#FFD9C2"
CREAM = "#FFF6E5"
OFF_WHITE = "#FBF9FF"

INK = "#2C2A4A"          # primary text
INK_SOFT = "#5A567A"      # secondary text
INK_MUTED = "#8E8AA8"     # tertiary text
SURFACE = "rgba(255, 255, 255, 0.72)"
SURFACE_STRONG = "rgba(255, 255, 255, 0.92)"
BORDER = "rgba(120, 110, 180, 0.18)"

ACCENT = "#7B6CF6"        # soft violet accent
ACCENT_HOVER = "#6B5BEA"
ACCENT_PRESSED = "#5A4DD6"
ACCENT_SOFT = "rgba(123, 108, 246, 0.12)"

SUCCESS = "#3DB48F"
WARNING = "#E8A33E"
DANGER = "#E26A78"
INFO = "#5AA9E6"

# Status pill colors (background, foreground) for various states
STATUS_COLORS: dict[str, tuple[str, str]] = {
    "waiting": ("#FFE9C2", "#A1641A"),
    "starting": ("#D9CCFF", "#4A3CB7"),
    "connected": ("#CFEFE0", "#1F7A57"),
    "failed": ("#FFD0D0", "#A52B3A"),
    "reconnect": ("#FFE0C2", "#A85A1A"),
    "uploading": ("#BFD7FF", "#1E4FA8"),
    "processing": ("#D9CCFF", "#4A3CB7"),
    "downloading": ("#CFEFE0", "#1F7A57"),
    "completed": ("#CFEFE0", "#1F7A57"),
    "queued": ("#F0E9FF", "#5A567A"),
}


def _build_qss() -> str:
    return f"""
    /* ------- Base ------- */
    QWidget {{
        color: {INK};
        font-family: "Segoe UI", "Inter", "SF Pro Display", "Helvetica Neue", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{
        background-color: transparent;
    }}

    /* ------- Glass cards ------- */
    QFrame#GlassCard {{
        background-color: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 22px;
    }}
    QFrame#GlassCardStrong {{
        background-color: {SURFACE_STRONG};
        border: 1px solid {BORDER};
        border-radius: 22px;
    }}
    QFrame#HeaderBar {{
        background-color: transparent;
    }}

    /* ------- Typography helpers ------- */
    QLabel#H1 {{
        font-size: 26px;
        font-weight: 700;
        color: {INK};
        letter-spacing: -0.3px;
    }}
    QLabel#H2 {{
        font-size: 18px;
        font-weight: 700;
        color: {INK};
    }}
    QLabel#H3 {{
        font-size: 15px;
        font-weight: 600;
        color: {INK};
    }}
    QLabel#Subtle {{
        font-size: 12px;
        color: {INK_SOFT};
    }}
    QLabel#Helper {{
        font-size: 13px;
        color: {INK_SOFT};
    }}
    QLabel#Muted {{
        font-size: 12px;
        color: {INK_MUTED};
    }}

    /* ------- Buttons ------- */
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.85);
        color: {INK};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 9px 18px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 1.0);
        border: 1px solid rgba(123, 108, 246, 0.35);
    }}
    QPushButton:pressed {{
        background-color: rgba(245, 242, 255, 1.0);
    }}
    QPushButton:disabled {{
        color: {INK_MUTED};
        background-color: rgba(255, 255, 255, 0.55);
    }}

    QPushButton#PrimaryButton {{
        background-color: {ACCENT};
        color: white;
        border: none;
        padding: 11px 22px;
        border-radius: 14px;
        font-weight: 700;
    }}
    QPushButton#PrimaryButton:hover {{ background-color: {ACCENT_HOVER}; }}
    QPushButton#PrimaryButton:pressed {{ background-color: {ACCENT_PRESSED}; }}
    QPushButton#PrimaryButton:disabled {{
        background-color: rgba(123, 108, 246, 0.35);
        color: rgba(255, 255, 255, 0.85);
    }}

    QPushButton#GhostButton {{
        background-color: transparent;
        border: 1px solid {BORDER};
    }}
    QPushButton#IconButton {{
        background-color: rgba(255, 255, 255, 0.7);
        border: 1px solid {BORDER};
        border-radius: 18px;
        min-width: 36px;
        min-height: 36px;
        max-width: 36px;
        max-height: 36px;
        padding: 0;
        font-size: 16px;
    }}
    QPushButton#IconButton:hover {{
        background-color: rgba(255, 255, 255, 1.0);
    }}
    QPushButton#DangerGhost {{
        background-color: transparent;
        color: {DANGER};
        border: 1px solid rgba(226, 106, 120, 0.35);
    }}
    QPushButton#DangerGhost:hover {{
        background-color: rgba(226, 106, 120, 0.08);
    }}

    /* ------- Inputs ------- */
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTextEdit {{
        background-color: rgba(255, 255, 255, 0.9);
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 8px 12px;
        selection-background-color: {ACCENT_SOFT};
        selection-color: {INK};
    }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
    QPlainTextEdit:focus, QTextEdit:focus {{
        border: 1px solid rgba(123, 108, 246, 0.55);
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: white;
        border: 1px solid {BORDER};
        border-radius: 10px;
        selection-background-color: {ACCENT_SOFT};
        selection-color: {INK};
        padding: 4px;
    }}

    /* ------- List widgets / tables ------- */
    QListWidget, QTreeWidget, QTableWidget {{
        background-color: rgba(255, 255, 255, 0.7);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 6px;
    }}
    QListWidget::item, QTreeWidget::item {{
        padding: 8px 10px;
        border-radius: 10px;
        margin: 2px 0;
        color: {INK};
    }}
    QListWidget::item:selected, QTreeWidget::item:selected {{
        background-color: {ACCENT_SOFT};
        color: {INK};
    }}

    /* ------- Progress bar ------- */
    QProgressBar {{
        background-color: rgba(180, 175, 220, 0.18);
        border: none;
        border-radius: 8px;
        height: 10px;
        text-align: center;
        color: {INK_SOFT};
    }}
    QProgressBar::chunk {{
        background-color: {ACCENT};
        border-radius: 8px;
    }}

    /* ------- Scroll bars ------- */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: rgba(120, 110, 180, 0.25);
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: rgba(120, 110, 180, 0.5);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: rgba(120, 110, 180, 0.25);
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ------- Tabs ------- */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {INK_SOFT};
        padding: 8px 14px;
        margin-right: 6px;
        border-radius: 10px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background-color: rgba(255, 255, 255, 0.85);
        color: {INK};
    }}

    /* ------- Tooltips ------- */
    QToolTip {{
        background-color: white;
        color: {INK};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 10px;
    }}

    /* ------- Status pill ------- */
    QLabel#StatusPill {{
        border-radius: 14px;
        padding: 4px 12px;
        font-weight: 600;
        font-size: 12px;
    }}

    /* ------- Drag-drop area ------- */
    QFrame#DropZone {{
        background-color: rgba(255, 255, 255, 0.55);
        border: 2px dashed rgba(123, 108, 246, 0.35);
        border-radius: 16px;
    }}
    QFrame#DropZoneActive {{
        background-color: rgba(207, 198, 255, 0.45);
        border: 2px dashed {ACCENT};
        border-radius: 16px;
    }}

    /* Quality preset radio cards */
    QPushButton#PresetCard {{
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 14px 16px;
        text-align: left;
        font-weight: 600;
    }}
    QPushButton#PresetCard:hover {{
        border: 1px solid rgba(123, 108, 246, 0.35);
        background-color: rgba(255, 255, 255, 1.0);
    }}
    QPushButton#PresetCard:checked {{
        background-color: rgba(207, 198, 255, 0.5);
        border: 1.5px solid {ACCENT};
    }}
    """


def apply_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(OFF_WHITE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(INK))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F5F1FF"))
    palette.setColor(QPalette.ColorRole.Text, QColor(INK))
    palette.setColor(QPalette.ColorRole.Button, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(INK))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(INK_MUTED))
    app.setPalette(palette)
    app.setStyleSheet(_build_qss())
    app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)


def status_pill_qss(state: str) -> str:
    """Return QSS to be set on a single StatusPill via QWidget.setStyleSheet().

    Note: when applied to one widget directly, no selector prefix is required
    — the rules apply to that widget. Using a #ID selector here causes Qt to
    log "Could not parse stylesheet" warnings.
    """
    bg, fg = STATUS_COLORS.get(state, STATUS_COLORS["queued"])
    return (
        f"background-color: {bg}; color: {fg}; "
        "border-radius: 14px; padding: 4px 12px; font-weight: 600; font-size: 12px;"
    )
