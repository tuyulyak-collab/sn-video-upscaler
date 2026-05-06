"""Connect Google Colab card (placeholder for PR #1).

The real connection logic (auto-discovery via ntfy.sh, /health probing,
status transitions) lands in PR #4. This skeleton just renders the card,
emits signals for clicks, and exposes a minimal `set_state(...)` so the
rest of the app can drive it once the connection layer arrives.
"""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .widgets import CardHeader, GhostButton, GlassCard, PrimaryButton, StatusPill


class ColabConnectionCard(GlassCard):
    open_colab_clicked = Signal()
    check_connection_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = self.layout_v()

        self.header = CardHeader(
            "Connect Google Colab",
            "SN Video Upscaler uses Google Colab GPU to process your videos faster. "
            "Open Colab, start the worker, then return here.",
        )
        self.status_pill = StatusPill("Waiting for Colab", state="waiting")
        self.header.add_right_widget(self.status_pill)
        layout.addWidget(self.header)

        # Pairing code row
        pairing_row = QHBoxLayout()
        pairing_row.setContentsMargins(0, 0, 0, 0)
        pairing_row.setSpacing(8)
        pair_label = QLabel("Pairing code")
        pair_label.setObjectName("Subtle")
        pairing_row.addWidget(pair_label)
        self.pairing_code_label = QLabel("—")
        self.pairing_code_label.setObjectName("H3")
        self.pairing_code_label.setStyleSheet(
            "QLabel { background-color: rgba(255, 255, 255, 0.85); "
            "border: 1px solid rgba(120, 110, 180, 0.18); border-radius: 10px; "
            "padding: 4px 10px; letter-spacing: 1.5px; "
            "font-family: 'Cascadia Code', 'Consolas', monospace; }"
        )
        pairing_row.addWidget(self.pairing_code_label)
        pairing_row.addStretch(1)
        self.message_label = QLabel("")
        self.message_label.setObjectName("Helper")
        self.message_label.setWordWrap(True)
        layout.addLayout(pairing_row)

        layout.addWidget(self.message_label)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(10)
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
