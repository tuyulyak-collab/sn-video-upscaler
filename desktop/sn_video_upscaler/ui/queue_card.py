"""Video queue card (placeholder for PR #1).

Currently shows a drop zone, file list, and Add/Remove/Clear buttons.
The list is a plain `list[str]` of file paths since the upload/process
state machine — and the real `Job` dataclass — land in PR #5/#6.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from .widgets import (
    CardHeader,
    DropZone,
    GhostButton,
    GlassCard,
    PrimaryButton,
    StatusPill,
)

VIDEO_FILTER = "Video files (*.mp4 *.mov *.mkv *.webm *.avi *.m4v);;All files (*)"
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


class QueueCard(GlassCard):
    files_added = Signal(list)
    remove_selected_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = self.layout_v()
        self.header = CardHeader(
            "Videos",
            "Add the videos you want to upscale. They will be sent to Colab one by one.",
        )
        self.queue_pill = StatusPill("0 in queue", state="queued")
        self.header.add_right_widget(self.queue_pill)
        layout.addWidget(self.header)

        # Top row: action buttons
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(10)
        self.add_button = PrimaryButton("Add Videos")
        self.add_button.clicked.connect(self._on_add_clicked)
        self.remove_button = GhostButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_clicked.emit)
        self.clear_button = GhostButton("Clear Queue")
        self.clear_button.clicked.connect(self.clear_clicked.emit)
        top_row.addWidget(self.add_button)
        top_row.addWidget(self.remove_button)
        top_row.addWidget(self.clear_button)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        # Drop zone
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self._on_files_dropped)
        self.drop_zone.clicked.connect(self._on_add_clicked)
        layout.addWidget(self.drop_zone)

        # File list
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setMinimumHeight(140)
        layout.addWidget(self.list_widget)

        self._enabled = False
        self.set_enabled(False, "Connect Google Colab first to add videos.")

    # ---- public ----
    def set_enabled(self, enabled: bool, helper_text: str | None = None) -> None:
        self._enabled = enabled
        self.add_button.setEnabled(enabled)
        self.drop_zone.setEnabled(enabled)
        self.list_widget.setEnabled(enabled)
        if helper_text is not None:
            self.header.set_helper(helper_text)
        self.setProperty("disabledLook", not enabled)

    def render_paths(self, paths: list[str]) -> None:
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for path in paths:
            self.list_widget.addItem(QListWidgetItem(self._format_path_label(path)))
        self.list_widget.blockSignals(False)
        self.queue_pill.set_state("queued", f"{len(paths)} in queue")

    def selected_indexes(self) -> list[int]:
        return sorted(
            {self.list_widget.row(it) for it in self.list_widget.selectedItems()},
            reverse=True,
        )

    @staticmethod
    def _format_path_label(path: str) -> str:
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            size_str = f"{size_mb:.1f} MB"
        except OSError:
            size_str = "—"
        return f"{os.path.basename(path)}    •    {size_str}    •    Queued"

    # ---- handlers ----
    def _on_add_clicked(self) -> None:
        if not self._enabled:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "Add videos", "", VIDEO_FILTER)
        if files:
            self.files_added.emit(files)

    def _on_files_dropped(self, files: list[str]) -> None:
        if not self._enabled:
            return
        accepted = [f for f in files if self._looks_like_video(f)]
        if accepted:
            self.files_added.emit(accepted)

    @staticmethod
    def _looks_like_video(path: str) -> bool:
        return os.path.splitext(path)[1].lower() in VIDEO_EXTENSIONS
