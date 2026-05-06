"""Connect Google Colab card — hero treatment for PR #2.

The real connection logic (auto-discovery via ntfy.sh, /health probing,
status transitions) lands in PR #4. This card emits signals for clicks
and exposes a minimal `set_state(...)` so the rest of the app can drive
it once the connection layer arrives.
"""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

from .widgets import (
    CardHeader,
    GhostButton,
    GlassCard,
    PrimaryButton,
    StatusPill,
)


class ColabConnectionCard(GlassCard):
    open_colab_clicked = Signal()
    check_connection_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, variant=GlassCard.HERO)

        layout = self.layout_v()
        layout.setSpacing(18)

        self.header = CardHeader(
            "Connect Google Colab",
            "SN Video Upscaler uses Google Colab GPU to process your videos faster. "
            "Open Colab, start the worker, then return here.",
            title_object_name="HeroTitle",
        )
        self.status_pill = StatusPill("Waiting for Colab", state="waiting")
        self.header.add_right_widget(self.status_pill)
        layout.addWidget(self.header)

        # Pairing code chip — pretty card-within-card so it feels intentional.
        chip_row = QHBoxLayout()
        chip_row.setContentsMargins(0, 4, 0, 4)
        chip_row.setSpacing(12)

        chip_box = QVBoxLayout()
        chip_box.setSpacing(4)
        chip_box.setContentsMargins(0, 0, 0, 0)
        pair_label = QLabel("Your pairing code")
        pair_label.setObjectName("PairingLabel")
        chip_box.addWidget(pair_label)
        self.pairing_code_label = QLabel("—")
        self.pairing_code_label.setObjectName("PairingCode")
        self.pairing_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pairing_code_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        chip_box.addWidget(self.pairing_code_label)
        chip_row.addLayout(chip_box)

        chip_help = QLabel(
            "Paste this code into the Colab notebook so it can publish "
            "its temporary worker URL back to you. The pairing code is "
            "rotated every session — never share it."
        )
        chip_help.setObjectName("Subtle")
        chip_help.setWordWrap(True)
        chip_help.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        chip_row.addWidget(chip_help, stretch=1)
        layout.addLayout(chip_row)

        self.message_label = QLabel("")
        self.message_label.setObjectName("Helper")
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)

        # Buttons — primary leads, ghost follows; right side stays empty so
        # the hero card feels balanced.
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(12)
        self.open_button = PrimaryButton("Open Colab Notebook")
        self.check_button = GhostButton("Check Connection")
        button_row.addWidget(self.open_button)
        button_row.addWidget(self.check_button)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.open_button.clicked.connect(self._open_clicked)
        self.check_button.clicked.connect(self.check_connection_clicked.emit)

        self._notebook_url = ""
        self.set_state("waiting", "Waiting for Colab")

    # ---- public ----
    def set_pairing_code(self, code: str) -> None:
        self.pairing_code_label.setText(code or "—")

    def set_notebook_url(self, url: str) -> None:
        self._notebook_url = url

    def set_state(self, state: str, message: str) -> None:
        labels = {
            "waiting": "Waiting for Colab",
            "starting": "Starting Colab worker",
            "connected": "Connected",
            "failed": "Connection failed",
            "reconnect": "Reconnect required",
        }
        self.status_pill.set_state(state, labels.get(state, state.title()))
        self.message_label.setText(message or "")

    # ---- handlers ----
    def _open_clicked(self) -> None:
        if self._notebook_url:
            webbrowser.open(self._notebook_url, new=2)
        self.open_colab_clicked.emit()
