"""Progress card (placeholder for PR #1).

Renders the three progress bars (Uploading / Processing on GPU /
Downloading result), per-job stats, and an activity line. The skeleton
keeps these inert — actual progress is fed in by the queue worker that
arrives in PR #5/#6.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .widgets import CardHeader, GlassCard, StatusPill


class _Stat(QWidget):
    def __init__(self, title: str, value: str = "0") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.title = QLabel(title)
        self.title.setObjectName("Muted")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value = QLabel(value)
        self.value.setObjectName("H2")
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value)
        layout.addWidget(self.title)


class ProgressCard(GlassCard):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = self.layout_v()
        self.header = CardHeader(
            "Progress",
            "Current file status, plus how many are completed, failed, and remaining.",
        )
        self.activity_pill = StatusPill("Idle", state="queued")
        self.header.add_right_widget(self.activity_pill)
        layout.addWidget(self.header)

        self.current_file = QLabel("No video processing yet.")
        self.current_file.setObjectName("H3")
        self.current_file.setWordWrap(True)
        layout.addWidget(self.current_file)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)

        self.upload_bar, self.upload_label = self._make_bar("Uploading")
        self.process_bar, self.process_label = self._make_bar("Processing on GPU")
        self.download_bar, self.download_label = self._make_bar("Downloading result")

        grid.addWidget(self.upload_label, 0, 0)
        grid.addWidget(self.upload_bar, 0, 1)
        grid.addWidget(self.process_label, 1, 0)
        grid.addWidget(self.process_bar, 1, 1)
        grid.addWidget(self.download_label, 2, 0)
        grid.addWidget(self.download_bar, 2, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        stats = QHBoxLayout()
        stats.setContentsMargins(0, 4, 0, 0)
        stats.setSpacing(20)
        self.stat_completed = _Stat("Completed")
        self.stat_failed = _Stat("Failed")
        self.stat_remaining = _Stat("Remaining")
        for w in (self.stat_completed, self.stat_failed, self.stat_remaining):
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            stats.addWidget(w)
        layout.addLayout(stats)

        self.activity_label = QLabel("Ready when you are.")
        self.activity_label.setObjectName("Subtle")
        self.activity_label.setWordWrap(True)
        layout.addWidget(self.activity_label)

    def _make_bar(self, title: str) -> tuple[QProgressBar, QLabel]:
        label = QLabel(title)
        label.setObjectName("Subtle")
        label.setMinimumWidth(160)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(True)
        bar.setFormat("%p%")
        return bar, label

    def set_activity(self, text: str, state: str = "queued") -> None:
        self.activity_label.setText(text or "")
        labels = {
            "queued": "Idle",
            "uploading": "Uploading",
            "processing": "Processing",
            "downloading": "Downloading",
            "completed": "Completed",
            "failed": "Failed",
            "reconnect": "Reconnect required",
            "starting": "Starting",
            "connected": "Connected",
            "waiting": "Waiting for Colab",
        }
        self.activity_pill.set_state(state, labels.get(state, state.title()))

    def update_summary(self, completed: int, failed: int, remaining: int) -> None:
        self.stat_completed.value.setText(str(completed))
        self.stat_failed.value.setText(str(failed))
        self.stat_remaining.value.setText(str(remaining))
