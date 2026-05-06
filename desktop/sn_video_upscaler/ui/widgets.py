"""Reusable UI widgets: gradient background, glass cards, pills, drop zone."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QLinearGradient,
    QPainter,
    QPaintEvent,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..theme import (
    BLUSH,
    CREAM,
    LAVENDER,
    PEACH,
    SKY_BLUE,
    status_pill_qss,
)


class GradientBackground(QWidget):
    """Soft pastel gradient + a large blurred radial glow behind the content."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        # base linear gradient: sky blue -> lavender -> blush -> peach -> cream
        grad = QLinearGradient(QPointF(rect.topLeft()), QPointF(rect.bottomRight()))
        grad.setColorAt(0.0, QColor(SKY_BLUE))
        grad.setColorAt(0.35, QColor(LAVENDER))
        grad.setColorAt(0.65, QColor(BLUSH))
        grad.setColorAt(0.85, QColor(PEACH))
        grad.setColorAt(1.0, QColor(CREAM))
        painter.fillRect(rect, QBrush(grad))

        # large blurred radial glow behind content (the "soft hero glow")
        glow_center = QPointF(rect.width() * 0.5, rect.height() * 0.42)
        glow_radius = max(rect.width(), rect.height()) * 0.7
        radial = QRadialGradient(glow_center, glow_radius, glow_center)
        radial.setColorAt(0.0, QColor(255, 255, 255, 230))
        radial.setColorAt(0.55, QColor(255, 255, 255, 90))
        radial.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(rect, QBrush(radial))


class GlassCard(QFrame):
    """White-translucent rounded card.

    Note: we deliberately avoid setting QGraphicsDropShadowEffect on the card
    itself. When a QGraphicsEffect is on a widget, Qt renders its children
    through an offscreen pixmap and child widgets with semi-transparent QSS
    backgrounds (like our PrimaryButton) lose their styling. To keep a soft
    elevation feel, the card's QSS already includes a subtle border, and the
    overall app has a strong radial glow behind it.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        strong: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("GlassCardStrong" if strong else "GlassCard")
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(22, 20, 22, 20)
        self._main_layout.setSpacing(14)

    def layout_v(self) -> QVBoxLayout:
        return self._main_layout


class StatusPill(QLabel):
    """Compact colored pill that reflects a state name."""

    def __init__(self, text: str = "", state: str = "queued", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("StatusPill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_state(state, text)

    def set_state(self, state: str, text: str | None = None) -> None:
        self.setStyleSheet(status_pill_qss(state))
        if text is not None:
            self.setText(text)


class CardHeader(QWidget):
    """Title + optional helper text + optional right-side widgets row."""

    def __init__(
        self,
        title: str,
        helper: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("H2")
        top.addWidget(self.title_label)
        top.addStretch(1)
        self._top_layout = top
        layout.addLayout(top)

        self.helper_label = QLabel(helper)
        self.helper_label.setObjectName("Helper")
        self.helper_label.setWordWrap(True)
        if not helper:
            self.helper_label.hide()
        layout.addWidget(self.helper_label)

    def add_right_widget(self, widget: QWidget) -> None:
        self._top_layout.addWidget(widget)

    def set_helper(self, text: str) -> None:
        self.helper_label.setText(text)
        self.helper_label.setVisible(bool(text))


class DropZone(QFrame):
    """Drag-and-drop target that emits dropped file paths."""

    files_dropped = Signal(list)
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Drop video files here")
        title.setObjectName("H3")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        sub = QLabel("MP4, MOV, MKV, WebM, AVI — or click to browse")
        sub.setObjectName("Subtle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self.setObjectName("DropZoneActive")
            self.style().unpolish(self)
            self.style().polish(self)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.toLocalFile()]
        if files:
            self.files_dropped.emit(files)
        self.setObjectName("DropZone")
        self.style().unpolish(self)
        self.style().polish(self)
        event.acceptProposedAction()


class IconButton(QPushButton):
    """Small round button that fits unicode glyphs (no icon font dep)."""

    def __init__(self, glyph: str, tooltip: str = "", parent: QWidget | None = None) -> None:
        super().__init__(glyph, parent)
        self.setObjectName("IconButton")
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(QSize(36, 36))


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("PrimaryButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class GhostButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("GhostButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


class PresetButton(QPushButton):
    """Selectable preset card (radio-style)."""

    def __init__(
        self,
        title: str,
        description: str,
        emoji: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PresetCard")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(8)
        emoji_label = QLabel(emoji)
        emoji_label.setStyleSheet("font-size: 18px;")
        head.addWidget(emoji_label)
        title_label = QLabel(title)
        title_label.setObjectName("H3")
        head.addWidget(title_label, stretch=1)
        layout.addLayout(head)

        desc = QLabel(description)
        desc.setObjectName("Subtle")
        desc.setWordWrap(True)
        layout.addWidget(desc)
