"""Global theme: layered pastel + glassmorphism palette and QSS."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

# ---- Palette (soft pastel SaaS) -------------------------------------------
SKY_BLUE = "#C9DCFF"
LAVENDER = "#DCD0FF"
BLUSH = "#FFD7E5"
PEACH = "#FFDFC8"
CREAM = "#FFF5E2"
OFF_WHITE = "#FBF8FF"
PAPER = "#F4F0FB"

INK = "#1F1D3D"          # primary text
INK_SOFT = "#52507A"      # secondary text
INK_MUTED = "#9088B0"     # tertiary text
SURFACE = "rgba(255, 255, 255, 0.62)"
SURFACE_STRONG = "rgba(255, 255, 255, 0.88)"
SURFACE_HOVER = "rgba(255, 255, 255, 0.78)"
BORDER = "rgba(120, 110, 180, 0.16)"
BORDER_STRONG = "rgba(120, 110, 180, 0.32)"

ACCENT = "#7B6CF6"
ACCENT_HOVER = "#6A5BEA"
ACCENT_PRESSED = "#5847D2"
ACCENT_LIGHT = "#A697FF"
ACCENT_SOFT = "rgba(123, 108, 246, 0.10)"
ACCENT_SOFT_HOVER = "rgba(123, 108, 246, 0.16)"
ACCENT_GLOW = "rgba(123, 108, 246, 0.28)"

SUCCESS = "#27AE82"
WARNING = "#E29A2D"
DANGER = "#E26A78"
INFO = "#5AA9E6"

# Status pill colors (background, text, dot)
STATUS_COLORS: dict[str, tuple[str, str, str]] = {
    "waiting":     ("rgba(255, 226, 184, 0.85)", "#8A4F12", "#E29A2D"),
    "starting":    ("rgba(220, 208, 255, 0.85)", "#3F2FA8", "#7B6CF6"),
    "connected":   ("rgba(204, 240, 224, 0.92)", "#15724F", "#27AE82"),
    "failed":      ("rgba(255, 210, 210, 0.85)", "#8E1F2D", "#E26A78"),
    "reconnect":   ("rgba(255, 218, 188, 0.85)", "#8E4914", "#E29A2D"),
    "uploading":   ("rgba(196, 220, 255, 0.85)", "#1A4596", "#5AA9E6"),
    "processing":  ("rgba(220, 208, 255, 0.85)", "#3F2FA8", "#7B6CF6"),
    "downloading": ("rgba(204, 240, 224, 0.92)", "#15724F", "#27AE82"),
    "completed":   ("rgba(204, 240, 224, 0.92)", "#15724F", "#27AE82"),
    "queued":      ("rgba(232, 226, 250, 0.85)", "#52507A", "#9088B0"),
    "idle":        ("rgba(232, 226, 250, 0.85)", "#52507A", "#9088B0"),
}


def _build_qss() -> str:
    return f"""
    QWidget {{
        color: {INK};
        font-family: "Segoe UI", "Inter", "SF Pro Display", "Helvetica Neue", sans-serif;
        font-size: 13px;
    }}
    QMainWindow, QDialog {{ background-color: transparent; }}

    /* ------- Glass cards (painted by GlassCard, but children inherit base) ------- */
    QFrame#GlassCard, QFrame#GlassCardStrong, QFrame#HeroCard {{
        background-color: transparent;
        border: none;
    }}

    /* ------- Typography helpers ------- */
    QLabel#H1 {{
        font-size: 28px;
        font-weight: 700;
        color: {INK};
        letter-spacing: -0.4px;
    }}
    QLabel#H2 {{
        font-size: 19px;
        font-weight: 700;
        color: {INK};
        letter-spacing: -0.2px;
    }}
    QLabel#HeroTitle {{
        font-size: 22px;
        font-weight: 700;
        color: {INK};
        letter-spacing: -0.3px;
    }}
    QLabel#H3 {{
        font-size: 15px;
        font-weight: 600;
        color: {INK};
    }}
    QLabel#Subtle {{
        font-size: 12.5px;
        color: {INK_SOFT};
    }}
    QLabel#Helper {{
        font-size: 13.5px;
        color: {INK_SOFT};
    }}
    QLabel#Muted {{
        font-size: 12px;
        color: {INK_MUTED};
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    QLabel#StatNumber {{
        font-size: 26px;
        font-weight: 700;
        color: {INK};
        letter-spacing: -0.4px;
    }}
    QLabel#PairingCode {{
        background-color: rgba(255, 255, 255, 0.92);
        border: 1px solid {BORDER_STRONG};
        border-radius: 11px;
        padding: 6px 14px;
        letter-spacing: 2.5px;
        font-family: "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
        font-weight: 700;
        font-size: 14px;
        color: {INK};
    }}
    QLabel#PairingLabel {{
        font-size: 11.5px;
        color: {INK_MUTED};
        letter-spacing: 0.7px;
        text-transform: uppercase;
        font-weight: 600;
    }}

    /* ------- Buttons ------- */
    QPushButton {{
        background-color: rgba(255, 255, 255, 0.85);
        color: {INK};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 10px 20px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: rgba(255, 255, 255, 1.0);
        border: 1px solid {BORDER_STRONG};
    }}
    QPushButton:pressed {{
        background-color: rgba(244, 240, 252, 1.0);
    }}
    QPushButton:disabled {{
        color: {INK_MUTED};
        background-color: rgba(255, 255, 255, 0.45);
        border-color: rgba(120, 110, 180, 0.12);
    }}

    QPushButton#PrimaryButton {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 {ACCENT_LIGHT},
            stop: 1 {ACCENT}
        );
        color: white;
        border: 1px solid {ACCENT};
        padding: 12px 24px;
        border-radius: 14px;
        font-weight: 700;
        font-size: 13.5px;
    }}
    QPushButton#PrimaryButton:hover {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #B5A8FF,
            stop: 1 {ACCENT_HOVER}
        );
        border: 1px solid {ACCENT_HOVER};
    }}
    QPushButton#PrimaryButton:pressed {{ background-color: {ACCENT_PRESSED}; }}
    QPushButton#PrimaryButton:disabled {{
        background: rgba(123, 108, 246, 0.32);
        border: 1px solid rgba(123, 108, 246, 0.32);
        color: rgba(255, 255, 255, 0.85);
    }}

    QPushButton#GhostButton {{
        background-color: rgba(255, 255, 255, 0.55);
        border: 1px solid {BORDER};
    }}
    QPushButton#GhostButton:hover {{
        background-color: rgba(255, 255, 255, 0.95);
        border: 1px solid {BORDER_STRONG};
    }}
    QPushButton#HeaderPill {{
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 8px 16px;
        font-weight: 600;
        color: {INK_SOFT};
    }}
    QPushButton#HeaderPill:hover {{
        background-color: rgba(255, 255, 255, 1.0);
        color: {INK};
        border: 1px solid {BORDER_STRONG};
    }}
    QPushButton#IconButton {{
        background-color: rgba(255, 255, 255, 0.75);
        border: 1px solid {BORDER};
        border-radius: 18px;
        min-width: 36px;
        min-height: 36px;
        max-width: 36px;
        max-height: 36px;
        padding: 0;
        font-size: 16px;
        color: {INK_SOFT};
    }}
    QPushButton#IconButton:hover {{
        background-color: rgba(255, 255, 255, 1.0);
        color: {INK};
        border: 1px solid {BORDER_STRONG};
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
        background-color: rgba(255, 255, 255, 0.92);
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
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background-color: white;
        border: 1px solid {BORDER};
        border-radius: 10px;
        selection-background-color: {ACCENT_SOFT};
        selection-color: {INK};
        padding: 4px;
    }}

    /* ------- List widgets ------- */
    QListWidget {{
        background-color: rgba(255, 255, 255, 0.55);
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 6px;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 10px;
        margin: 2px 0;
        color: {INK};
    }}
    QListWidget::item:selected {{
        background-color: {ACCENT_SOFT};
        color: {INK};
    }}
    QListWidget::item:hover {{
        background-color: rgba(255, 255, 255, 0.55);
    }}

    /* ------- Progress bar ------- */
    QProgressBar {{
        background-color: rgba(180, 175, 220, 0.18);
        border: none;
        border-radius: 6px;
        max-height: 10px;
        min-height: 10px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 {ACCENT_LIGHT},
            stop: 1 {ACCENT}
        );
        border-radius: 6px;
    }}

    /* ------- Scroll bars ------- */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background-color: rgba(120, 110, 180, 0.22);
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: rgba(120, 110, 180, 0.45);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: rgba(120, 110, 180, 0.22);
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ------- Tabs ------- */
    QTabWidget::pane {{ border: none; background-color: transparent; }}
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

    /* ------- Drop zone ------- */
    QFrame#DropZone {{
        background-color: rgba(255, 255, 255, 0.5);
        border: 1.5px dashed rgba(123, 108, 246, 0.32);
        border-radius: 16px;
    }}
    QFrame#DropZoneActive {{
        background-color: rgba(207, 198, 255, 0.45);
        border: 2px dashed {ACCENT};
        border-radius: 16px;
    }}

    /* ------- Quality preset cards ------- */
    QPushButton#PresetCard {{
        background-color: rgba(255, 255, 255, 0.7);
        border: 1px solid {BORDER};
        border-radius: 16px;
        padding: 16px 18px;
        text-align: left;
        font-weight: 600;
    }}
    QPushButton#PresetCard:hover {{
        border: 1px solid rgba(123, 108, 246, 0.35);
        background-color: rgba(255, 255, 255, 0.95);
    }}
    QPushButton#PresetCard:checked {{
        background-color: rgba(220, 208, 255, 0.5);
        border: 1.5px solid {ACCENT};
    }}

    /* ------- Activity dot indicator next to log line ------- */
    QLabel#ActivityDot {{
        min-width: 8px; min-height: 8px;
        max-width: 8px; max-height: 8px;
        border-radius: 4px;
        background-color: {ACCENT};
    }}
    """


def apply_theme(app: QApplication) -> None:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(OFF_WHITE))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(INK))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(PAPER))
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
    """QSS for a single StatusPill widget (set via setStyleSheet)."""
    bg, fg, _dot = STATUS_COLORS.get(state, STATUS_COLORS["queued"])
    return (
        "QLabel {"
        f"background-color: {bg};"
        f"color: {fg};"
        "border-radius: 13px;"
        "padding: 5px 12px 5px 12px;"
        "font-weight: 700;"
        "font-size: 11.5px;"
        "letter-spacing: 0.3px;"
        "}"
    )


def status_dot_color(state: str) -> str:
    _bg, _fg, dot = STATUS_COLORS.get(state, STATUS_COLORS["queued"])
    return dot
