"""Start processing card: Start, Pause, Stop, Retry Failed, Open Output Folder."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QWidget

from .widgets import CardHeader, GhostButton, GlassCard, PrimaryButton


class StartCard(GlassCard):
    start_clicked = Signal()
    pause_clicked = Signal(bool)  # True = paused
    stop_clicked = Signal()
    retry_failed_clicked = Signal()
    open_output_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = self.layout_v()
        layout.addWidget(
            CardHeader(
                "Run",
                "Start sending videos to Colab. Videos are processed one by one.",
            )
        )

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self.start_btn = PrimaryButton("Start Upscale")
        self.pause_btn = GhostButton("Pause")
        self.pause_btn.setCheckable(True)
        self.stop_btn = GhostButton("Stop")
        self.retry_btn = GhostButton("Retry Failed")
        self.open_btn = GhostButton("Open Output Folder")

        for w in (self.start_btn, self.pause_btn, self.stop_btn, self.retry_btn):
            row.addWidget(w)
        row.addStretch(1)
        row.addWidget(self.open_btn)
        layout.addLayout(row)

        self.start_btn.clicked.connect(self.start_clicked)
        self.pause_btn.toggled.connect(self._on_pause_toggled)
        self.stop_btn.clicked.connect(self.stop_clicked)
        self.retry_btn.clicked.connect(self.retry_failed_clicked)
        self.open_btn.clicked.connect(self.open_output_clicked)

        self.set_running(False)

    def set_running(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running)
        self.stop_btn.setEnabled(running)

    def set_can_start(self, ok: bool) -> None:
        if not self.pause_btn.isEnabled() and not self.stop_btn.isEnabled():
            self.start_btn.setEnabled(ok)

    def _on_pause_toggled(self, checked: bool) -> None:
        self.pause_btn.setText("Resume" if checked else "Pause")
        self.pause_clicked.emit(checked)

    def reset_pause(self) -> None:
        self.pause_btn.blockSignals(True)
        self.pause_btn.setChecked(False)
        self.pause_btn.setText("Pause")
        self.pause_btn.blockSignals(False)
