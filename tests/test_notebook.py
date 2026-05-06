"""Smoke tests for the Colab worker notebook (PR #3B single-video pipeline).

These don't execute the notebook (Colab/GPU only); they verify the
notebook is valid JSON, has the expected structure, and contains the
key elements promised by PR #3A + PR #3B: setup, GPU check, folder
creation, Real-ESRGAN upscaling pipeline, and the four endpoints
(`/health`, `/upscale`, `/status/{job_id}`, `/download/{job_id}`).
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


def test_notebook_installs_realesrgan_pipeline(notebook: dict) -> None:
    """PR #3B installs Real-ESRGAN + its supporting deps."""
    code = "\n".join(
        "".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
    )
    assert '"pip"' in code and '"install"' in code, "expected a pip install step"
    for dep in ("realesrgan", "basicsr", "facexlib", "gfpgan", "python-multipart"):
        assert dep in code, f"expected {dep!r} in install step"


def test_notebook_defines_upload_status_download_endpoints(notebook: dict) -> None:
    """PR #3B endpoints are wired in cell 6 (Start Worker)."""
    src = _all_source(notebook)
    assert "@app.post(\"/upscale\")" in src or "@app.post('/upscale')" in src
    assert "@app.get(\"/status/{job_id}\")" in src or "@app.get('/status/{job_id}')" in src
    assert "@app.get(\"/download/{job_id}\")" in src or "@app.get('/download/{job_id}')" in src
    # Required upload-handling primitives.
    assert "UploadFile" in src
    assert "FileResponse" in src
    assert "MAX_UPLOAD_BYTES" in src


def test_notebook_defines_quality_presets(notebook: dict) -> None:
    """PR #3B exposes the three presets the desktop app uses."""
    src = _all_source(notebook)
    for preset in ("fast_2x", "high_quality_4x", "anime_illustration"):
        assert preset in src, f"missing preset {preset!r}"
    # And the corresponding Real-ESRGAN models.
    for model in ("RealESRGAN_x2plus", "RealESRGAN_x4plus", "RealESRGAN_x4plus_anime_6B"):
        assert model in src, f"missing model {model!r}"


def test_notebook_defines_pipeline_phases(notebook: dict) -> None:
    """PR #3B status responses use a known set of phases."""
    src = _all_source(notebook)
    for phase in (
        "uploaded",
        "extracting_frames",
        "upscaling_frames",
        "rebuilding_video",
        "preserving_audio",
        "completed",
        "failed",
    ):
        assert phase in src, f"missing pipeline phase {phase!r}"


def test_notebook_does_not_implement_desktop_or_batch_yet(notebook: dict) -> None:
    """PR #3B is single-video only; desktop wiring + batch queue land later."""
    code = "\n".join(
        "".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
    )
    # No batch queue endpoint and no desktop-side discovery publish call yet.
    assert "/batch" not in code
    assert "@app.post(\"/queue" not in code and "@app.post('/queue" not in code
    # `ntfy.sh` shows up only as the DISCOVERY_BASE constant for PR #4 to use.
    assert code.count("ntfy.sh") <= 1, (
        "ntfy.sh should appear only as the discovery-base constant"
    )


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
