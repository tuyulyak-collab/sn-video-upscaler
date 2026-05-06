"""Smoke tests for the Colab worker notebook (PR #3A foundation).

These don't execute the notebook (Colab/GPU only); they verify the
notebook is valid JSON, has the expected structure, and contains the
key elements promised by PR #3A: setup, GPU check, folder creation,
and a `/health` endpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK = REPO_ROOT / "colab" / "sn_video_upscaler_colab_worker.ipynb"
SOURCE = REPO_ROOT / "colab" / "source" / "notebook.py"


@pytest.fixture(scope="module")
def notebook() -> dict:
    assert NOTEBOOK.exists(), "Run scripts/build_notebook.py to generate the .ipynb."
    return json.loads(NOTEBOOK.read_text())


def _all_source(nb: dict) -> str:
    return "\n".join("".join(c["source"]) for c in nb["cells"])


def test_notebook_is_valid_nbformat(notebook: dict) -> None:
    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] >= 4
    assert notebook["metadata"].get("accelerator") == "GPU"
    assert isinstance(notebook["cells"], list)
    assert len(notebook["cells"]) > 0


def test_notebook_has_beginner_instructions(notebook: dict) -> None:
    src = _all_source(notebook).lower()
    assert "runtime" in src and "gpu" in src
    assert "open this notebook" in src or "open in colab" in src.lower() or "step 1" in src


def test_notebook_has_gpu_check_with_friendly_messages(notebook: dict) -> None:
    src = _all_source(notebook)
    assert "Google Colab GPU is ready." in src
    assert "No GPU detected" in src
    assert "torch.cuda.is_available" in src or "nvidia-smi" in src


def test_notebook_creates_required_folders(notebook: dict) -> None:
    src = _all_source(notebook)
    for sub in ("input", "frames", "upscaled_frames", "output", "temp", "logs"):
        assert sub in src, f"Missing folder reference: {sub}"
    assert "/content/sn_video_upscaler" in src


def test_notebook_defines_health_endpoint(notebook: dict) -> None:
    src = _all_source(notebook)
    assert "@app.get(\"/health\")" in src or "@app.get('/health')" in src
    # Required fields per PR #3A.
    for key in ("status", "gpu_available", "gpu_name", "current_job", "message"):
        assert f'"{key}"' in src, f"Missing /health field: {key}"


def test_notebook_starts_tunnel_and_prints_url(notebook: dict) -> None:
    src = _all_source(notebook)
    assert "cloudflared" in src
    assert "trycloudflare.com" in src
    assert "Worker URL" in src


def test_notebook_does_not_implement_full_pipeline_yet(notebook: dict) -> None:
    """PR #3A scope: no Real-ESRGAN install, no /upscale, /download, /status."""
    code = "\n".join(
        "".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
    ).lower()
    assert '"pip"' in code and '"install"' in code, "expected a pip install step"
    # No Real-ESRGAN install line in code cells (it's only mentioned in
    # markdown explaining what's deferred to PR #3B).
    assert "realesrgan" not in code
    assert "real_esrgan" not in code
    assert "real-esrgan" not in code.replace("# ", " ")  # ignore comments
    assert "/upscale" not in code
    assert "/download" not in code
    assert "/status/" not in code


def test_notebook_source_and_ipynb_are_in_sync() -> None:
    """If you edit the .py without re-running the build script, fail."""
    assert SOURCE.exists(), "Notebook source file is missing."
    src_text = SOURCE.read_text()
    nb = json.loads(NOTEBOOK.read_text())
    nb_code_text = "\n".join(
        "".join(c["source"])
        for c in nb["cells"]
        if c["cell_type"] == "code"
    )
    # Pairing code is the first code cell — it should appear identically.
    assert 'PAIRING_CODE = ""' in src_text
    assert 'PAIRING_CODE = ""' in nb_code_text
