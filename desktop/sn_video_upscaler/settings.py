"""Minimal in-memory settings for the PR #1 skeleton.

Real persistence (JSON in user config dir) and the Settings dialog land
in a later PR.
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_videos_dir


def _default_output_folder() -> str:
    return str(Path(user_videos_dir()) / "SN Video Upscaler Output")


def _generate_pairing_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "SNVU-" + "".join(secrets.choice(alphabet) for _ in range(8))


@dataclass
class AppSettings:
    """In-memory settings used by the PR #1 skeleton."""

    output_folder: str = field(default_factory=_default_output_folder)
    pairing_code: str = field(default_factory=_generate_pairing_code)
    quality_preset: str = "fast_2x"
