"""Reusable UI widgets: gradient background, glass cards, pills, drop zone."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
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
    LAVENDER,
    OFF_WHITE,
    PEACH,
    SKY_BLUE,
    status_dot_color,
    status_pill_qss,
)


class GradientBackground(QWidget):
    """Layered atmospheric pastel background.

    Composition (back to front):
      1. Off-white wash with a faint top-to-bottom warm tilt.
      2. Three large soft radial glows (lavender top-left, sky-blue
         top-right, peach + blush low-center) — these create the
         "blurred glow behind the content" effect without using
         QGraphicsEffect (which causes child rendering issues).
      3. A subtle vignette of the same off-white at the corners to keep
         the cards readable.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        rectf = QRectF(rect)

        # 1. Off-white wash with a slight diagonal tilt.
        wash = QLinearGradient(rectf.topLeft(), rectf.bottomRight())
        wash.setColorAt(0.0, QColor("#F4F0FB"))
        wash.setColorAt(0.5, QColor(OFF_WHITE))
        wash.setColorAt(1.0, QColor("#FFF8F0"))
        painter.fillRect(rectf, QBrush(wash))

        # 2. Three large radial glows. Each uses several stops with
        #    decreasing alpha to simulate a blurred edge — no real
        #    Gaussian blur is needed.
        def _glow(cx: float, cy: float, r: float, hex_color: str, peak_alpha: int) -> None:
            color = QColor(hex_color)
            radial = QRadialGradient(QPointF(cx, cy), r)
            inner = QColor(color)
            inner.setAlpha(peak_alpha)
            mid = QColor(color)
            mid.setAlpha(int(peak_alpha * 0.45))
            soft = QColor(color)
            soft.setAlpha(int(peak_alpha * 0.18))
            edge = QColor(color)
            edge.setAlpha(0)
            radial.setColorAt(0.0, inner)
            radial.setColorAt(0.45, mid)
            radial.setColorAt(0.75, soft)
            radial.setColorAt(1.0, edge)
            painter.fillRect(rectf, QBrush(radial))

        w = rectf.width()
        h = rectf.height()
        max_r = max(w, h)

        _glow(w * 0.18, h * 0.18, max_r * 0.55, LAVENDER, peak_alpha=200)
        _glow(w * 0.85, h * 0.10, max_r * 0.45, SKY_BLUE, peak_alpha=170)
        _glow(w * 0.68, h * 0.78, max_r * 0.55, PEACH, peak_alpha=180)
        _glow(w * 0.30, h * 0.85, max_r * 0.40, BLUSH, peak_alpha=140)

        # 3. Inner soft white that lifts the content area's contrast.
        center_glow = QRadialGradient(
            QPointF(w * 0.5, h * 0.45),
            max_r * 0.55,
        )
        center_glow.setColorAt(0.0, QColor(255, 255, 255, 170))
        center_glow.setColorAt(0.6, QColor(255, 255, 255, 60))
        center_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.fillRect(rectf, QBrush(center_glow))


class GlassCard(QFrame):
    """Translucent rounded card with a soft drop shadow and inner highlight.

    The card is custom-painted instead of relying on QSS + QGraphicsEffect
    to avoid the well-known issue where a graphics effect on a parent
    widget breaks the QSS background of children with semi-transparent
    fills (e.g. the PrimaryButton).
    """

    HERO = "hero"
    NORMAL = "normal"
    STRONG = "strong"

    def __init__(
        self,
        parent: QWidget | None = None,
        variant: str = NORMAL,
    ) -> None:
        super().__init__(parent)
        self._variant = variant
        self.setObjectName(
            {
                self.HERO: "HeroCard",
                self.STRONG: "GlassCardStrong",
                self.NORMAL: "GlassCard",
            }.get(variant, "GlassCard")
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._shadow_padding = 14  # space the card leaves around itself for the drop shadow
        self._main_layout = QVBoxLayout(self)
        if variant == self.HERO:
            self._main_layout.setContentsMargins(28, 26, 28, 26)
        else:
            self._main_layout.setContentsMargins(26, 22, 26, 22)
        self._main_layout.setSpacing(14)

    def layout_v(self) -> QVBoxLayout:
        return self._main_layout

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect())
        radius = 22 if self._variant != self.HERO else 26
        body_rect = rect.adjusted(2, 2, -2, -3)

        # 1. Soft outer shadow — three stacked rounded rects with rising
        #    alpha simulate a blurred drop shadow without QGraphicsEffect.
        for i, alpha in enumerate((10, 16, 22)):
            offset = (3 - i) * 1.2
            shadow_rect = body_rect.adjusted(-2 - i, 2 + i + offset, 2 + i, 6 + i + offset)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(40, 30, 80, alpha))
            painter.drawRoundedRect(shadow_rect, radius + i, radius + i)

        # 2. Card body — vertical translucent gradient (slightly brighter
        #    at the top to suggest a glassy highlight).
        body_path = QPainterPath()
        body_path.addRoundedRect(body_rect, radius, radius)
        body_grad = QLinearGradient(body_rect.topLeft(), body_rect.bottomLeft())
        if self._variant == self.HERO:
            body_grad.setColorAt(0.0, QColor(255, 255, 255, 235))
            body_grad.setColorAt(0.6, QColor(255, 255, 255, 215))
            body_grad.setColorAt(1.0, QColor(255, 255, 255, 195))
        elif self._variant == self.STRONG:
            body_grad.setColorAt(0.0, QColor(255, 255, 255, 240))
            body_grad.setColorAt(1.0, QColor(255, 255, 255, 220))
        else:
            body_grad.setColorAt(0.0, QColor(255, 255, 255, 200))
            body_grad.setColorAt(0.5, QColor(255, 255, 255, 175))
            body_grad.setColorAt(1.0, QColor(255, 255, 255, 150))
        painter.fillPath(body_path, QBrush(body_grad))

        # 3. 1px soft border — slightly stronger on the bottom edge to
        #    feel "lifted".
        painter.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor(120, 110, 180, 50))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.drawRoundedRect(body_rect.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)

        # 4. Soft inner highlight on the top edge to sell the glass.
        highlight_rect = QRectF(
            body_rect.left() + 6,
            body_rect.top() + 1,
            body_rect.width() - 12,
            1,
        )
        painter.fillRect(highlight_rect, QColor(255, 255, 255, 140))

        super().paintEvent(event)


class StatusPill(QWidget):
    """Compact colored pill: leading colored dot + label."""

    def __init__(
        self,
        text: str = "",
        state: str = "queued",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusPillContainer")
        self._state = state
        self._plain_text = text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._label = QLabel()
        self._label.setObjectName("StatusPill")
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._label)
        self.set_state(state, text)

    def set_state(self, state: str, text: str | None = None) -> None:
        self._state = state
        if text is not None:
            self._plain_text = text
        dot = status_dot_color(state)
        pill_styles = status_pill_qss(state)
        # Build rich text so the leading dot can have its own color
        # while the label text uses the pill's foreground.
        rich = (
            f'<span style="color:{dot};">●</span>'
            f'<span style="color:transparent;">&nbsp;&nbsp;</span>'
            f"<span>{self._plain_text}</span>"
        )
        self._label.setStyleSheet(pill_styles)
        self._label.setText(rich)

    def text(self) -> str:
        return self._plain_text


class CardHeader(QWidget):
    """Title + optional helper text + optional right-side widgets row."""

    def __init__(
        self,
        title: str,
        helper: str = "",
        parent: QWidget | None = None,
        title_object_name: str = "H2",
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(10)
        self.title_label = QLabel(title)
        self.title_label.setObjectName(title_object_name)
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


class CloudUploadIcon(QWidget):
    """Custom painted cloud-with-up-arrow icon, used in the empty state."""

    def __init__(self, parent: QWidget | None = None, size: int = 56) -> None:
        super().__init__(parent)
        self.setFixedSize(QSize(size, size))

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        s = self.width()
        # cloud body
        path = QPainterPath()
        path.moveTo(s * 0.22, s * 0.62)
        path.cubicTo(s * 0.05, s * 0.62, s * 0.05, s * 0.40, s * 0.25, s * 0.40)
        path.cubicTo(s * 0.27, s * 0.22, s * 0.55, s * 0.18, s * 0.62, s * 0.34)
        path.cubicTo(s * 0.85, s * 0.30, s * 0.95, s * 0.55, s * 0.82, s * 0.62)
        path.lineTo(s * 0.22, s * 0.62)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(123, 108, 246, 30))
        painter.drawPath(path)

        pen = QPen(QColor(123, 108, 246, 200))
        pen.setWidthF(1.6)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # up arrow inside cloud
        center_x = s * 0.50
        arrow_top = s * 0.50
        arrow_bot = s * 0.86
        pen.setWidthF(2.0)
        painter.setPen(pen)
        painter.drawLine(QPointF(center_x, arrow_bot), QPointF(center_x, arrow_top))
        painter.drawLine(
            QPointF(center_x, arrow_top),
            QPointF(center_x - s * 0.10, arrow_top + s * 0.10),
        )
        painter.drawLine(
            QPointF(center_x, arrow_top),
            QPointF(center_x + s * 0.10, arrow_top + s * 0.10),
        )


class DropZone(QFrame):
    """Drag-and-drop target with an iconified empty state."""

    files_dropped = Signal(list)
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(132)
        self.setMaximumHeight(168)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_row = QHBoxLayout()
        icon_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon = CloudUploadIcon(size=44)
        icon_row.addWidget(self.icon)
        layout.addLayout(icon_row)

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


class HeaderPillButton(QPushButton):
    """Header-bar action presented as a soft pill (folder/settings shortcuts)."""

    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("HeaderPill")
        self.setCursor(Qt.CursorShape.PointingHandCursor)


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
    """Selectable preset card with a labelled emoji chip."""

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
        self.setMinimumHeight(108)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Emoji chip — rounded mini-pill that holds the emoji.
        chip_row = QHBoxLayout()
        chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.setSpacing(8)
        chip = QLabel(emoji)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setFixedSize(QSize(34, 34))
        chip.setStyleSheet(
            "QLabel {"
            "background: rgba(255, 255, 255, 0.85);"
            "border: 1px solid rgba(120, 110, 180, 0.18);"
            "border-radius: 17px;"
            "font-size: 18px;"
            "}"
        )
        chip_row.addWidget(chip)
        chip_row.addStretch(1)
        layout.addLayout(chip_row)

        title_label = QLabel(title)
        title_label.setObjectName("H3")
        layout.addWidget(title_label)

        desc = QLabel(description)
        desc.setObjectName("Subtle")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addStretch(1)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        # When the preset is checked, paint a soft accent glow before the
        # default QSS-styled body so the selected card feels lifted.
        if self.isChecked():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            rect = QRectF(self.rect()).adjusted(2, 4, -2, -4)
            for i in range(3):
                offset = i * 1.5
                glow_rect = rect.adjusted(-offset, -offset, offset, offset)
                color = QColor(123, 108, 246, 40 - i * 12)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(color)
                painter.drawRoundedRect(glow_rect, 18 + i, 18 + i)
        super().paintEvent(event)


class StatBlock(QWidget):
    """Stacked stat: big number on top, label underneath."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatNumber")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Muted")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value: int | str) -> None:
        self.value_label.setText(str(value))


class SectionDivider(QWidget):
    """Hairline horizontal divider, slightly soft."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = QRectF(self.rect())
        grad = QLinearGradient(rect.topLeft(), rect.topRight())
        grad.setColorAt(0.0, QColor(120, 110, 180, 0))
        grad.setColorAt(0.5, QColor(120, 110, 180, 60))
        grad.setColorAt(1.0, QColor(120, 110, 180, 0))
        painter.fillRect(rect, QBrush(grad))


__all__ = [
    "GradientBackground",
    "GlassCard",
    "StatusPill",
    "CardHeader",
    "DropZone",
    "IconButton",
    "HeaderPillButton",
    "PrimaryButton",
    "GhostButton",
    "PresetButton",
    "StatBlock",
    "SectionDivider",
    "CloudUploadIcon",
]
