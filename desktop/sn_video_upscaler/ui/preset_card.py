"""Quality preset card with three radio-style preset cards."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QWidget

from .widgets import CardHeader, GlassCard, PresetButton

# Preset metadata is inlined here for the PR #1 skeleton. When the queue
# state machine arrives in PR #5/#6 the canonical source will live next
# to it (services/queue_manager.PRESETS) and this dict will become a thin
# pull from there.
PRESETS: dict[str, dict[str, str]] = {
    "fast_2x": {
        "emoji": "⚡",
        "label": "Fast 2×",
        "description": "Quick general-purpose upscale, keeps natural look.",
    },
    "high_4x": {
        "emoji": "✨",
        "label": "High Quality 4×",
        "description": "Slower, sharper detail. Best for photos and live action.",
    },
    "anime": {
        "emoji": "🎨",
        "label": "Anime / Illustration",
        "description": "Tuned for anime, cartoons, and illustrations.",
    },
}


class PresetCard(GlassCard):
    preset_changed = Signal(str)  # preset key

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = self.layout_v()
        layout.addWidget(
            CardHeader(
                "Quality preset",
                "Pick how much detail you want. "
                "You can change advanced model settings in Settings.",
            )
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        self._buttons: dict[str, PresetButton] = {}
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        for key, info in PRESETS.items():
            btn = PresetButton(
                title=info["label"],
                description=info["description"],
                emoji=info["emoji"],
            )
            btn.toggled.connect(lambda checked, k=key: self._on_toggled(k, checked))
            self._buttons[key] = btn
            self._group.addButton(btn)
            row.addWidget(btn, stretch=1)

        layout.addLayout(row)

        self.set_preset("fast_2x")

    def set_preset(self, key: str) -> None:
        if key not in self._buttons:
            key = "fast_2x"
        for k, btn in self._buttons.items():
            btn.setChecked(k == key)

    def selected_preset(self) -> str:
        for k, btn in self._buttons.items():
            if btn.isChecked():
                return k
        return "fast_2x"

    def _on_toggled(self, key: str, checked: bool) -> None:
        if checked:
            self.preset_changed.emit(key)
