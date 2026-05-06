"""Smoke tests for the PR #1 skeleton.

These verify the app composes without errors and surfaces the expected
placeholder state. The full Colab connection / queue worker tests land
in later PRs.
"""

from __future__ import annotations

import os
import sys

import pytest

# Force a headless Qt platform before importing PySide6.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402
from sn_video_upscaler.settings import AppSettings  # noqa: E402
from sn_video_upscaler.theme import apply_theme  # noqa: E402
from sn_video_upscaler.ui.main_window import MainWindow  # noqa: E402
from sn_video_upscaler.ui.preset_card import PRESETS  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    apply_theme(app)
    yield app


def test_pairing_code_format():
    s = AppSettings()
    assert s.pairing_code.startswith("SNVU-")
    assert len(s.pairing_code) == 13


def test_default_output_folder_contains_app_name():
    s = AppSettings()
    assert "SN Video Upscaler Output" in s.output_folder


def test_three_presets_present():
    assert set(PRESETS) == {"fast_2x", "high_4x", "anime"}
    for info in PRESETS.values():
        assert info["label"]
        assert info["description"]


def test_main_window_starts_in_waiting_state(qapp):
    w = MainWindow()
    try:
        # Connect-Colab card starts in "Waiting for Colab" state.
        assert w.colab_card.status_pill.text().lower() == "waiting for colab"
        # Queue card is disabled until PR #4 lands the real connection.
        assert w.queue_card.add_button.isEnabled() is False
        # Default preset is fast_2x.
        assert w.preset_card.selected_preset() == "fast_2x"
    finally:
        w.close()
