"""Main application window — composes all cards (PR #1 skeleton).

Wiring to a real Colab connection manager and queue worker happens in
later PRs. For now the buttons emit signals into a small in-window list
and a `_log()` activity buffer so we can validate the layout end-to-end.
"""

from __future__ import annotations

import os
import sys
from collections import deque
from datetime import datetime

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __app_subtitle__
from ..settings import AppSettings
from .colab_card import ColabConnectionCard
from .preset_card import PresetCard
from .progress_card import ProgressCard
from .queue_card import QueueCard
from .start_card import StartCard
from .widgets import GhostButton, GradientBackground, IconButton


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(__app_name__)
        self.resize(1180, 1080)

        self.settings = AppSettings()

        self._files: list[str] = []
        self._activity_log: deque[str] = deque(maxlen=200)

        # Background widget hosts the gradient + glow.
        self.background = GradientBackground()
        self.setCentralWidget(self.background)

        outer = QVBoxLayout(self.background)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)
        outer.addLayout(self._build_header())

        # Scrollable cards area. The transparent stylesheet must be scoped
        # to the host widgets only — a global `background: transparent` would
        # cascade into child QPushButtons and override their styled fills.
        scroll = QScrollArea()
        scroll.setObjectName("CardsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea#CardsScroll { background: transparent; border: none; }"
        )
        scroll.viewport().setObjectName("CardsScrollVP")
        scroll.viewport().setAutoFillBackground(False)
        scroll.viewport().setStyleSheet(
            "QWidget#CardsScrollVP { background: transparent; }"
        )

        cards_host = QWidget()
        cards_host.setObjectName("CardsHost")
        cards_host.setAutoFillBackground(False)
        cards_host.setStyleSheet("QWidget#CardsHost { background: transparent; }")
        cards_layout = QVBoxLayout(cards_host)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(18)

        self.colab_card = ColabConnectionCard()
        self.colab_card.set_pairing_code(self.settings.pairing_code)
        self.colab_card.set_state(
            "waiting",
            "Open Colab and start the worker. The connection layer arrives in PR #4.",
        )

        self.queue_card = QueueCard()
        self.queue_card.set_enabled(
            False,
            "Connect Google Colab first to add videos. (PR #1: cards are placeholder.)",
        )

        self.preset_card = PresetCard()
        self.preset_card.set_preset(self.settings.quality_preset)

        self.start_card = StartCard()
        self.progress_card = ProgressCard()

        for card in (
            self.colab_card,
            self.queue_card,
            self.preset_card,
            self.start_card,
            self.progress_card,
        ):
            cards_layout.addWidget(card)
        cards_layout.addStretch(1)

        scroll.setWidget(cards_host)
        outer.addWidget(scroll, stretch=1)

        # Footer
        footer = QLabel("PR #1 skeleton — controllers and Colab worker arrive in later PRs.")
        footer.setObjectName("Muted")
        outer.addWidget(footer)

        self._wire_signals()

    # ---- header ----
    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(2, 4, 2, 4)
        row.setSpacing(10)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel(__app_name__)
        title.setObjectName("H1")
        subtitle = QLabel(__app_subtitle__)
        subtitle.setObjectName("Subtle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        row.addLayout(title_box)
        row.addStretch(1)

        self.output_button = GhostButton("Output Folder")
        self.output_button.clicked.connect(self._open_output_folder)
        row.addWidget(self.output_button)

        self.settings_button = IconButton("⚙")
        self.settings_button.clicked.connect(self._open_settings_placeholder)
        row.addWidget(self.settings_button)

        return row

    # ---- wiring ----
    def _wire_signals(self) -> None:
        self.colab_card.open_colab_clicked.connect(
            lambda: self._log("Open Colab Notebook (PR #3 will open the real notebook).")
        )
        self.colab_card.check_connection_clicked.connect(
            lambda: self._log("Check Connection (PR #4 will probe the worker).")
        )

        self.queue_card.files_added.connect(self._on_files_added)
        self.queue_card.remove_selected_clicked.connect(self._remove_selected)
        self.queue_card.clear_clicked.connect(self._clear_queue)

        self.preset_card.preset_changed.connect(self._on_preset_changed)

        self.start_card.start_clicked.connect(
            lambda: self._log("Start Upscale (PR #5/#6 will run the queue).")
        )
        self.start_card.pause_clicked.connect(
            lambda paused: self._log(f"Pause toggled — {'paused' if paused else 'resumed'}.")
        )
        self.start_card.stop_clicked.connect(lambda: self._log("Stop pressed."))
        self.start_card.retry_failed_clicked.connect(
            lambda: self._log("Retry Failed (no failures yet in skeleton).")
        )
        self.start_card.open_output_clicked.connect(self._open_output_folder)

    # ---- handlers ----
    def _on_files_added(self, paths: list[str]) -> None:
        seen = set(self._files)
        added = [p for p in paths if p not in seen]
        self._files.extend(added)
        self.queue_card.render_paths(self._files)
        self.progress_card.update_summary(0, 0, len(self._files))
        self._log(f"Added {len(added)} video(s) to the queue.")

    def _remove_selected(self) -> None:
        for idx in self.queue_card.selected_indexes():
            if 0 <= idx < len(self._files):
                self._files.pop(idx)
        self.queue_card.render_paths(self._files)
        self.progress_card.update_summary(0, 0, len(self._files))
        self._log("Removed selected video(s).")

    def _clear_queue(self) -> None:
        self._files.clear()
        self.queue_card.render_paths(self._files)
        self.progress_card.update_summary(0, 0, 0)
        self._log("Cleared the queue.")

    def _on_preset_changed(self, key: str) -> None:
        self.settings.quality_preset = key
        self._log(f"Quality preset → {key}")

    def _open_output_folder(self) -> None:
        path = self.settings.output_folder
        os.makedirs(path, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')
            self._log(f"Opened output folder: {path}")
        except Exception as exc:  # pragma: no cover - best effort
            self._log(f"Could not open output folder: {exc}")

    def _open_settings_placeholder(self) -> None:
        QMessageBox.information(
            self,
            "Settings",
            "The full Settings dialog (general + Advanced/Troubleshooting) "
            "ships in a later PR. PR #1 is a placeholder skeleton.",
        )

    # ---- helpers ----
    def _log(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {text}"
        self._activity_log.append(line)
        self.progress_card.activity_label.setText(line)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        super().closeEvent(event)
