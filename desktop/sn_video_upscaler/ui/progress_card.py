"""Progress card.

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

from .widgets import (
    CardHeader,
    GlassCard,
    SectionDivider,
    StatBlock,
    StatusPill,
)


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

        # Current file display
        current_box = QVBoxLayout()
        current_box.setContentsMargins(0, 0, 0, 0)
        current_box.setSpacing(2)
        current_label = QLabel("Current file")
        current_label.setObjectName("Muted")
        current_box.addWidget(current_label)
        self.current_file = QLabel("No video processing yet.")
        self.current_file.setObjectName("H3")
        self.current_file.setWordWrap(True)
        current_box.addWidget(self.current_file)
        layout.addLayout(current_box)

        # Three progress bars in a grid, each with a percentage on the right.
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        self.upload_bar, self.upload_label, self.upload_pct = self._make_bar("Uploading")
        self.process_bar, self.process_label, self.process_pct = self._make_bar(
            "Processing on GPU"
        )
        self.download_bar, self.download_label, self.download_pct = self._make_bar(
            "Downloading result"
        )

        for row, (label, bar, pct) in enumerate(
            (
                (self.upload_label, self.upload_bar, self.upload_pct),
                (self.process_label, self.process_bar, self.process_pct),
                (self.download_label, self.download_bar, self.download_pct),
            )
        ):
            grid.addWidget(label, row, 0)
            grid.addWidget(bar, row, 1)
            grid.addWidget(pct, row, 2)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        layout.addWidget(SectionDivider())

        # Stats row
        stats = QHBoxLayout()
        stats.setContentsMargins(0, 4, 0, 0)
        stats.setSpacing(20)
        self.stat_completed = StatBlock("Completed", "0")
        self.stat_failed = StatBlock("Failed", "0")
        self.stat_remaining = StatBlock("Remaining", "0")
        for w in (self.stat_completed, self.stat_failed, self.stat_remaining):
            w.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            stats.addWidget(w)
        layout.addLayout(stats)

        layout.addWidget(SectionDivider())

        # Activity line — small leading dot + label, like a status feed.
        activity_row = QHBoxLayout()
        activity_row.setContentsMargins(0, 4, 0, 0)
        activity_row.setSpacing(10)
        self.activity_dot = QLabel("")
        self.activity_dot.setObjectName("ActivityDot")
        activity_row.addWidget(self.activity_dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.activity_label = QLabel("Ready when you are.")
        self.activity_label.setObjectName("Subtle")
        self.activity_label.setWordWrap(True)
        activity_row.addWidget(self.activity_label, stretch=1)
        layout.addLayout(activity_row)

    def _make_bar(self, title: str) -> tuple[QProgressBar, QLabel, QLabel]:
        label = QLabel(title)
        label.setObjectName("Subtle")
        label.setMinimumWidth(150)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        pct = QLabel("0%")
        pct.setObjectName("Subtle")
        pct.setMinimumWidth(38)
        pct.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return bar, label, pct

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
        # Tint the leading dot to match the active state for a tight feedback loop.
        from ..theme import status_dot_color
        color = status_dot_color(state)
        self.activity_dot.setStyleSheet(
            f"QLabel#ActivityDot {{ background-color: {color}; "
            "min-width: 8px; min-height: 8px; max-width: 8px; max-height: 8px; "
            "border-radius: 4px; }}"
        )

    def update_summary(self, completed: int, failed: int, remaining: int) -> None:
        self.stat_completed.set_value(completed)
        self.stat_failed.set_value(failed)
        self.stat_remaining.set_value(remaining)

    def set_progress(
        self,
        upload: int | None = None,
        process: int | None = None,
        download: int | None = None,
    ) -> None:
        for bar, pct, value in (
            (self.upload_bar, self.upload_pct, upload),
            (self.process_bar, self.process_pct, process),
            (self.download_bar, self.download_pct, download),
        ):
            if value is None:
                continue
            v = max(0, min(100, int(value)))
            bar.setValue(v)
            pct.setText(f"{v}%")
