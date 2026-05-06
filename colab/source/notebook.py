# noqa: INP001
# This file is the source-of-truth for the Colab worker notebook.
#
# Each `# %% [markdown]` block becomes a markdown cell; each `# %%` block
# becomes a code cell. Run `python scripts/build_notebook.py` from the
# repo root to (re)generate `colab/sn_video_upscaler_colab_worker.ipynb`.
#
# IMPORTANT: This file is intentionally written for review readability —
# it does NOT need to be runnable on the local box. The actual execution
# context is Google Colab. We import inside cells (instead of at the top
# of the file) so each cell is self-contained and runnable on its own.
#
# ruff: noqa

# %% [markdown]
# # SN Video Upscaler — Colab Worker
#
# This notebook turns a free Google Colab GPU runtime into a temporary
# worker that the **SN Video Upscaler** desktop app can talk to.
#
# **PR #3B scope**: single-video pipeline. This notebook installs FFmpeg,
# Real-ESRGAN, and the Python deps, checks the GPU, creates the working
# folders, and starts a worker that exposes:
#
# - `GET /health` — readiness + GPU info
# - `POST /upscale` — accept one video file + quality preset
# - `GET /status/{job_id}` — phase + progress for a running job
# - `GET /download/{job_id}` — the upscaled MP4 once it finishes
#
# A single video flows: upload → extract frames (FFmpeg) → upscale frames
# (Real-ESRGAN, picked by preset) → rebuild MP4 (FFmpeg) → mux original
# audio (FFmpeg). Batch queueing lands in PR #6; desktop integration
# lands in PR #4–#5.
#
# ---
#
# ## How to run this notebook
#
# 1. Open this notebook in **Google Colab** (File → Open notebook → GitHub
#    URL, or click the *Open in Colab* badge in the repo).
# 2. **Runtime → Change runtime type → Hardware accelerator → GPU**, then click *Save*.
# 3. Click **Connect** (top-right of the notebook).
# 4. Run the **Setup** cells (in order). They install FFmpeg + Real-ESRGAN
#    + the worker deps. The first run can take 1–3 minutes because of the
#    Real-ESRGAN install + initial model weight download.
# 5. Run **Start Worker**. The cell will print something like:
#    ```
#    Worker URL: https://xxxxx-xxxxx-xxxxx.trycloudflare.com
#    ```
# 6. Keep this Colab tab **open** while SN Video Upscaler is processing
#    videos. If the runtime disconnects, just re-run **Start Worker**.
#
# ## Smoke-test single-video pipeline (curl)
#
# ```bash
# # 1. Upload a short clip and pick a preset.
# curl -F "video=@my_clip.mp4" -F "preset=fast_2x" \
#      https://<worker>.trycloudflare.com/upscale
# # -> {"job_id":"...","status":"uploaded","file_name":"my_clip.mp4"}
#
# # 2. Poll status (the worker reports current phase + progress).
# curl https://<worker>.trycloudflare.com/status/<job_id>
#
# # 3. Once status.output_ready is true, download the MP4.
# curl -O -J https://<worker>.trycloudflare.com/download/<job_id>
# ```
#
# ## Common Colab issues
#
# - **"No GPU detected"** — go back to step 2 and pick **GPU**.
# - **"Cannot connect to runtime"** — click *Reconnect*; Colab idles
#   sessions out after ~90 minutes.
# - **"Worker URL changed"** — Colab gives you a new tunnel URL every
#   time you re-run the start cell. The desktop app rediscovers it
#   automatically (PR #4) using your pairing code.
# - **First `/upscale` is slow** — Real-ESRGAN downloads a ~64MB model
#   on first use; subsequent jobs reuse the cached weights.

# %% [markdown]
# ## 1. Pairing code
#
# Paste the pairing code shown in the SN Video Upscaler desktop app
# (it looks like `SNVU-XXXXXXXX`). The notebook will publish its
# temporary worker URL to a private discovery channel keyed by this
# code so the desktop app can find it without you copy-pasting URLs.
#
# Leave it empty for now if you're just smoke-testing PR #3A.

# %%
PAIRING_CODE = ""  # e.g. "SNVU-AB12CD34"

# Notebook config — beginners shouldn't need to touch these.
APP_NAME = "SN Video Upscaler"
WORKER_PORT = 8000
DISCOVERY_BASE = "https://ntfy.sh"  # used by PR #4 to publish the URL

# %% [markdown]
# ## 2. Install dependencies
#
# - **FFmpeg** is pre-installed on Colab — we just verify it.
# - **Web stack**: `fastapi`, plain `uvicorn` (no `[standard]` — uvloop
#   conflicts with our threaded startup), `python-multipart` (so FastAPI
#   can accept the video file upload), and `requests` (used by PR #4 to
#   publish the worker URL).
# - **Real-ESRGAN** + its deps (`basicsr`, `facexlib`, `gfpgan`) — the
#   actual upscaling engine. Torch is whatever the Colab runtime ships
#   with; we don't pin it.
# - **cloudflared** gives us a public HTTPS URL into the Colab runtime.

# %%
import shutil
import subprocess
import sys


def _run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


# Verify FFmpeg is present.
if shutil.which("ffmpeg") is None:
    _run(["apt-get", "update", "-qq"])
    _run(["apt-get", "install", "-y", "-qq", "ffmpeg"])
print("FFmpeg:", shutil.which("ffmpeg"))

# Worker / web stack. Plain `uvicorn` (not `uvicorn[standard]`) — uvloop
# can't be patched by nest_asyncio and we don't need its perf for a
# low-traffic worker. We also explicitly remove uvloop in case a previous
# run of this cell (or the runtime image) already installed it; otherwise
# uvicorn would auto-detect and use it.
_run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "uvloop"], check=False)
_run([
    sys.executable, "-m", "pip", "install", "-q",
    "fastapi==0.115.5",
    "uvicorn==0.32.0",
    "python-multipart==0.0.12",
    "requests==2.32.3",
])

# Real-ESRGAN. We don't pin torch — Colab's GPU runtime already has a
# CUDA-enabled torch and forcing a specific torch version often breaks
# the runtime. We DO patch `basicsr` after install because newer
# torchvision releases moved `rgb_to_grayscale` out of
# `torchvision.transforms.functional_tensor` and basicsr's
# `degradations.py` still imports the old path.
_run([
    sys.executable, "-m", "pip", "install", "-q",
    "basicsr==1.4.2",
    "facexlib==0.3.0",
    "gfpgan==1.3.8",
    "realesrgan==0.3.0",
])

from pathlib import Path as _Path  # local alias — Path is re-imported in cell 5

import basicsr as _basicsr  # noqa: E402

_deg_py = _Path(_basicsr.__file__).parent / "data" / "degradations.py"
if _deg_py.exists():
    _src = _deg_py.read_text()
    _patched = _src.replace(
        "from torchvision.transforms.functional_tensor import rgb_to_grayscale",
        "from torchvision.transforms.functional import rgb_to_grayscale",
    )
    if _patched != _src:
        _deg_py.write_text(_patched)
        print("Patched basicsr/data/degradations.py for newer torchvision.")

# Cloudflared — provides a free https://*.trycloudflare.com tunnel.
if shutil.which("cloudflared") is None:
    _run([
        "wget", "-q",
        "https://github.com/cloudflare/cloudflared/releases/latest/"
        "download/cloudflared-linux-amd64",
        "-O", "/usr/local/bin/cloudflared",
    ])
    _run(["chmod", "+x", "/usr/local/bin/cloudflared"])
print("cloudflared:", shutil.which("cloudflared"))

print("Dependencies ready.")

# %% [markdown]
# ## 3. GPU check
#
# Confirms a CUDA GPU is attached to the runtime. If you see
# *"No GPU detected"* below, redo **Runtime → Change runtime type → GPU**.

# %%
GPU_AVAILABLE = False
GPU_NAME = ""

try:
    import torch  # type: ignore[import-not-found]

    GPU_AVAILABLE = bool(torch.cuda.is_available())
    if GPU_AVAILABLE:
        GPU_NAME = torch.cuda.get_device_name(0)
except ModuleNotFoundError:
    # Torch is not installed yet (PR #3B will pin a CUDA build of torch).
    # Fall back to nvidia-smi so this notebook still reports GPU presence.
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            check=True, capture_output=True, text=True, timeout=10,
        )
        GPU_NAME = (result.stdout.strip().splitlines() or [""])[0]
        GPU_AVAILABLE = bool(GPU_NAME)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        GPU_AVAILABLE = False
        GPU_NAME = ""

if GPU_AVAILABLE:
    print(f"Google Colab GPU is ready. ({GPU_NAME})")
else:
    print(
        "No GPU detected. Please change Runtime > Change runtime type > GPU, "
        "then click Connect and re-run the setup cells."
    )

# %% [markdown]
# ## 4. Working folders
#
# Create the per-job folder structure under `/content/sn_video_upscaler/`.
# Each job gets its own subdirectory under `temp/` for frames; the final
# upscaled MP4 lands in `output/`.

# %%
import os

WORK_ROOT = "/content/sn_video_upscaler"
SUBDIRS = ("input", "frames", "upscaled_frames", "output", "temp", "logs")

os.makedirs(WORK_ROOT, exist_ok=True)
for sub in SUBDIRS:
    os.makedirs(os.path.join(WORK_ROOT, sub), exist_ok=True)

print(f"Working root: {WORK_ROOT}")
for sub in SUBDIRS:
    full = os.path.join(WORK_ROOT, sub)
    print(f"  - {sub}/  ->  {full}")

# %% [markdown]
# ## 5. Pipeline helpers
#
# Building blocks for the single-video pipeline: preset → Real-ESRGAN
# model mapping, FFmpeg helpers (frame extract, MP4 rebuild, audio mux),
# the Real-ESRGAN upscaler (lazy-loaded on first use), and the job state
# machine + background runner.
#
# These are pure definitions — running this cell does not start the
# worker. Cell 6 wires them into FastAPI endpoints.

# %%
import shutil as _shutil
import subprocess as _subprocess
import threading as _threading_p  # cell 6 binds its own `threading`
import traceback as _traceback_p
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional


# Preset → (Real-ESRGAN model name, native scale factor).
PRESETS: dict[str, tuple[str, int]] = {
    "fast_2x": ("RealESRGAN_x2plus", 2),
    "high_quality_4x": ("RealESRGAN_x4plus", 4),
    "anime_illustration": ("RealESRGAN_x4plus_anime_6B", 4),
}
SUPPORTED_INPUT_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

# Phases — kept in sync with /status response and the README table.
PHASE_UPLOADED = "uploaded"
PHASE_EXTRACTING = "extracting_frames"
PHASE_UPSCALING = "upscaling_frames"
PHASE_REBUILDING = "rebuilding_video"
PHASE_AUDIO = "preserving_audio"
PHASE_COMPLETED = "completed"
PHASE_FAILED = "failed"

WEIGHTS_DIR = Path(WORK_ROOT) / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class JobInfo:
    job_id: str
    file_name: str
    preset: str
    status: str = PHASE_UPLOADED
    progress: float = 0.0
    output_ready: bool = False
    error: Optional[str] = None
    output_path: Optional[str] = None
    started_at: str = ""
    updated_at: str = ""
    frame_count: int = 0

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "file_name": self.file_name,
            "preset": self.preset,
            "status": self.status,
            "current_phase": self.status,
            "progress": round(self.progress, 4),
            "output_ready": self.output_ready,
            "error": self.error,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "frame_count": self.frame_count,
        }


JOBS: dict[str, JobInfo] = {}
JOBS_LOCK = _threading_p.Lock()
JOB_EXECUTOR = ThreadPoolExecutor(max_workers=1)  # one video at a time


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _set_phase(
    job_id: str, phase: str, *, progress: Optional[float] = None
) -> None:
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.status = phase
        if progress is not None:
            job.progress = progress
        job.updated_at = _now_iso()


def _job_dir(job_id: str) -> Path:
    return Path(WORK_ROOT) / "temp" / job_id


# ---------- FFmpeg helpers ----------

def _ffprobe_fps(path: Path) -> float:
    """Return source video's framerate. Falls back to 30.0 if unknown."""
    try:
        out = _subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=r_frame_rate",
                "-of", "default=nokey=1:noprint_wrappers=1", str(path),
            ],
            text=True, timeout=15,
        ).strip()
        if "/" in out:
            num, den = out.split("/", 1)
            n, d = float(num), float(den) or 1.0
            if d > 0:
                return n / d
        return float(out) if out else 30.0
    except (
        _subprocess.CalledProcessError,
        _subprocess.TimeoutExpired,
        ValueError,
        FileNotFoundError,
    ):
        return 30.0


def _has_audio_stream(path: Path) -> bool:
    try:
        out = _subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "default=nokey=1:noprint_wrappers=1", str(path),
            ],
            text=True, timeout=15,
        ).strip()
        return bool(out)
    except (
        _subprocess.CalledProcessError,
        _subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return False


def _extract_frames(input_path: Path, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path), "-q:v", "1",
        str(out_dir / "%06d.png"),
    ]
    proc = _subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg frame extraction failed: {proc.stderr.strip()[-2000:]}"
        )
    return sum(1 for _ in out_dir.glob("*.png"))


def _rebuild_video(frames_dir: Path, fps: float, out_video_only: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-framerate", f"{fps:.6f}",
        "-i", str(frames_dir / "%06d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "18", "-movflags", "+faststart",
        str(out_video_only),
    ]
    proc = _subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"FFmpeg rebuild failed: {proc.stderr.strip()[-2000:]}"
        )


def _mux_audio(video_only: Path, source: Path, final: Path) -> None:
    if not _has_audio_stream(source):
        _shutil.copyfile(video_only, final)
        return
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_only), "-i", str(source),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        str(final),
    ]
    proc = _subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        # Audio mux failed — keep the silent video so the user still has
        # a usable result; surface the error to the caller as a warning.
        _shutil.copyfile(video_only, final)
        raise RuntimeError(
            f"Audio mux failed (kept silent video): {proc.stderr.strip()[-2000:]}"
        )


# ---------- Real-ESRGAN upscaler ----------

UPSCALERS: dict[str, Any] = {}  # cached per-preset


def _build_upscaler(preset: str):
    """Lazy-load and cache the Real-ESRGAN upscaler for `preset`."""
    if preset in UPSCALERS:
        return UPSCALERS[preset]
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset: {preset!r}")
    model_name, scale = PRESETS[preset]

    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet

    if model_name == "RealESRGAN_x4plus":
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                      num_block=23, num_grow_ch=32, scale=4)
        url = ("https://github.com/xinntao/Real-ESRGAN/releases/download/"
               "v0.1.0/RealESRGAN_x4plus.pth")
    elif model_name == "RealESRGAN_x2plus":
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                      num_block=23, num_grow_ch=32, scale=2)
        url = ("https://github.com/xinntao/Real-ESRGAN/releases/download/"
               "v0.2.1/RealESRGAN_x2plus.pth")
    elif model_name == "RealESRGAN_x4plus_anime_6B":
        net = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                      num_block=6, num_grow_ch=32, scale=4)
        url = ("https://github.com/xinntao/Real-ESRGAN/releases/download/"
               "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth")
    else:
        raise ValueError(f"Unsupported model: {model_name!r}")

    weight_path = WEIGHTS_DIR / f"{model_name}.pth"
    if not weight_path.exists():
        print(f"Downloading Real-ESRGAN weights: {model_name} (~64MB)…")
        _subprocess.run(
            ["wget", "-q", url, "-O", str(weight_path)], check=True
        )

    upsampler = RealESRGANer(
        scale=scale,
        model_path=str(weight_path),
        model=net,
        tile=400,            # tile to keep VRAM bounded on T4
        tile_pad=10,
        pre_pad=0,
        half=GPU_AVAILABLE,  # FP16 if GPU is available
    )
    UPSCALERS[preset] = upsampler
    return upsampler


def _upscale_frames(
    in_dir: Path,
    out_dir: Path,
    preset: str,
    on_progress: Callable[[int, int], None],
) -> int:
    import cv2  # bundled with realesrgan deps

    out_dir.mkdir(parents=True, exist_ok=True)
    frames = sorted(in_dir.glob("*.png"))
    if not frames:
        raise RuntimeError("Frame extraction produced 0 frames.")
    upsampler = _build_upscaler(preset)
    _, scale = PRESETS[preset]

    for i, src in enumerate(frames):
        img = cv2.imread(str(src), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise RuntimeError(f"Could not read frame {src.name}")
        try:
            output, _ = upsampler.enhance(img, outscale=scale)
        except Exception as exc:
            raise RuntimeError(
                f"Real-ESRGAN failed on frame {src.name}: {exc}"
            ) from exc
        cv2.imwrite(str(out_dir / src.name), output)
        on_progress(i + 1, len(frames))
    return len(frames)


# ---------- Job runner ----------

def _run_job(job_id: str) -> None:
    """Run the full single-video pipeline for one job."""
    with JOBS_LOCK:
        job = JOBS[job_id]
    job_dir = _job_dir(job_id)
    frames_dir = job_dir / "frames"
    upscaled_dir = job_dir / "upscaled_frames"
    input_path = job_dir / job.file_name
    final_path = (
        Path(WORK_ROOT) / "output"
        / f"{job_id}_{Path(job.file_name).stem}_upscaled.mp4"
    )
    intermediate = job_dir / "no_audio.mp4"

    try:
        # 1. Extract frames
        _set_phase(job_id, PHASE_EXTRACTING, progress=0.0)
        n_frames = _extract_frames(input_path, frames_dir)
        if n_frames == 0:
            raise RuntimeError("FFmpeg produced 0 frames from this video.")
        with JOBS_LOCK:
            job.frame_count = n_frames
        fps = _ffprobe_fps(input_path)

        # 2. Upscale frames
        _set_phase(job_id, PHASE_UPSCALING, progress=0.0)

        def _progress(done: int, total: int) -> None:
            _set_phase(job_id, PHASE_UPSCALING, progress=done / max(total, 1))

        _upscale_frames(frames_dir, upscaled_dir, job.preset, _progress)

        # 3. Rebuild MP4
        _set_phase(job_id, PHASE_REBUILDING, progress=0.0)
        _rebuild_video(upscaled_dir, fps, intermediate)

        # 4. Mux original audio (non-fatal: failure leaves silent video)
        _set_phase(job_id, PHASE_AUDIO, progress=0.0)
        try:
            _mux_audio(intermediate, input_path, final_path)
        except RuntimeError as exc:
            print(f"[job {job_id}] audio mux warning: {exc}")

        # 5. Done — mark complete and clean up heavy temp dirs
        with JOBS_LOCK:
            job.status = PHASE_COMPLETED
            job.progress = 1.0
            job.output_ready = True
            job.output_path = str(final_path)
            job.updated_at = _now_iso()

        for d in (frames_dir, upscaled_dir):
            _shutil.rmtree(d, ignore_errors=True)
        if intermediate.exists():
            intermediate.unlink(missing_ok=True)

    except BaseException as exc:  # noqa: BLE001 — surface every failure
        _traceback_p.print_exc()
        with JOBS_LOCK:
            job.status = PHASE_FAILED
            job.error = f"{type(exc).__name__}: {exc}"
            job.updated_at = _now_iso()


print("Pipeline helpers loaded:", ", ".join(PRESETS))

# %% [markdown]
# ## 6. Start Worker
#
# This cell does four things:
#
# 1. Defines the **FastAPI app** with `GET /health`, `POST /upscale`,
#    `GET /status/{job_id}`, and `GET /download/{job_id}` endpoints.
# 2. Starts `uvicorn` in a background thread on a free port (starts at
#    `WORKER_PORT` and walks up if it's already taken).
# 3. Boots a **cloudflared** tunnel pointing at the local worker, and
#    waits for the public `https://*.trycloudflare.com` URL to appear
#    in the tunnel logs.
# 4. Prints the public URL clearly so you can verify it manually with
#    `curl <url>/health`.
#
# Re-run this cell any time the runtime restarts. The URL changes each
# time — that's expected.

# %%
import asyncio
import json
import re
import socket
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests as _requests
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse


WORKER_VERSION = "0.3.0b"  # PR #3B: single-video pipeline.
STARTED_AT = datetime.now(timezone.utc).isoformat()
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB hard cap on uploaded video

app = FastAPI(title=f"{APP_NAME} Colab Worker", version=WORKER_VERSION)


def _current_running_job_id() -> Optional[str]:
    with JOBS_LOCK:
        for j in JOBS.values():
            if j.status not in (PHASE_COMPLETED, PHASE_FAILED):
                return j.job_id
    return None


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({
        "status": "ready",
        "app": APP_NAME,
        "version": WORKER_VERSION,
        "gpu_available": GPU_AVAILABLE,
        "gpu_name": GPU_NAME,
        "current_job": _current_running_job_id(),
        "started_at": STARTED_AT,
        "presets": list(PRESETS),
        "message": (
            "Google Colab GPU is ready."
            if GPU_AVAILABLE
            else "No GPU detected. Change Runtime > GPU and re-run setup."
        ),
    })


@app.post("/upscale")
async def upscale(
    video: UploadFile = File(...),
    preset: str = Form(...),
) -> JSONResponse:
    """Accept one video file + preset, kick off the pipeline."""
    if preset not in PRESETS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown preset {preset!r}. "
                f"Choose one of: {sorted(PRESETS)}."
            ),
        )
    if not GPU_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail=(
                "No GPU available. Change Runtime > GPU on the Colab tab "
                "and re-run the setup cells, then retry."
            ),
        )
    file_name = Path(video.filename or "input").name
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_INPUT_EXTS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type {suffix!r}. "
                f"Supported: {sorted(SUPPORTED_INPUT_EXTS)}."
            ),
        )
    if _current_running_job_id() is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Worker is busy with another job. PR #3B handles one video "
                "at a time; batch queueing arrives in PR #6."
            ),
        )

    job_id = uuid.uuid4().hex[:12]
    job_dir = _job_dir(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    dest = job_dir / file_name

    written = 0
    try:
        with dest.open("wb") as fh:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD_BYTES:
                    fh.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"Upload exceeded {MAX_UPLOAD_BYTES} bytes. "
                            "Trim the video or upgrade the cap in the worker."
                        ),
                    )
                fh.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        dest.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500, detail=f"Upload failed: {exc}"
        ) from exc

    if written == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty upload.")

    info = JobInfo(
        job_id=job_id,
        file_name=file_name,
        preset=preset,
        status=PHASE_UPLOADED,
        started_at=_now_iso(),
        updated_at=_now_iso(),
    )
    with JOBS_LOCK:
        JOBS[job_id] = info
    JOB_EXECUTOR.submit(_run_job, job_id)
    return JSONResponse(info.to_dict(), status_code=202)


@app.get("/status/{job_id}")
def status(job_id: str) -> JSONResponse:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        snapshot = job.to_dict() if job else None
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Unknown job_id {job_id!r}.")
    return JSONResponse(snapshot)


@app.get("/download/{job_id}")
def download(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        path = job.output_path if job else None
        ready = bool(job and job.output_ready)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown job_id {job_id!r}.")
    if not ready or not path:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Output not ready. Current status: {job.status!r}. "
                "Poll /status/{job_id} until output_ready=true."
            ),
        )
    file_path = Path(path)
    if not file_path.exists():
        raise HTTPException(
            status_code=410,
            detail=(
                "Output file is missing. The Colab runtime may have been "
                "recycled — re-run the job."
            ),
        )
    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_path.name,
    )


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


# Pick the first free port in the WORKER_PORT..+10 range so the cell can
# be re-run without "address already in use" from a previous attempt.
WORKER_PORT_ACTIVE = WORKER_PORT
for _candidate in range(WORKER_PORT, WORKER_PORT + 10):
    if _port_is_free(_candidate):
        WORKER_PORT_ACTIVE = _candidate
        break
if WORKER_PORT_ACTIVE != WORKER_PORT:
    print(f"Port {WORKER_PORT} busy, using {WORKER_PORT_ACTIVE} instead.")

# Capture any exception raised inside the uvicorn thread so the user
# actually sees what went wrong instead of a generic timeout.
_serve_error: list[BaseException] = []


def _serve() -> None:
    try:
        # A fresh thread needs its own event loop.
        asyncio.set_event_loop(asyncio.new_event_loop())
        config = uvicorn.Config(
            app,
            host="127.0.0.1",
            port=WORKER_PORT_ACTIVE,
            log_level="warning",
            access_log=False,
            # Force the stdlib asyncio loop. If `uvloop` is present in the
            # runtime image, uvicorn would auto-detect and use it, which
            # makes the loop unpatchable by nest_asyncio (used elsewhere
            # in Colab) and breaks `Server.run()` from this background
            # thread.
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        # Signal handlers can only be installed from the main thread; this
        # background thread isn't, so disable them. Otherwise uvicorn raises
        # ValueError("signal only works in main thread...").
        server.install_signal_handlers = lambda: None  # type: ignore[assignment]
        server.run()
    except BaseException as exc:  # noqa: BLE001 — surface any failure
        _serve_error.append(exc)


_server_thread = threading.Thread(target=_serve, daemon=True)
_server_thread.start()

# Wait until the local worker answers /health before bringing up the tunnel.
_local_ok = False
for _ in range(60):  # up to 15 seconds
    if _serve_error:
        break
    try:
        r = _requests.get(
            f"http://127.0.0.1:{WORKER_PORT_ACTIVE}/health", timeout=1.0
        )
        if r.status_code == 200:
            _local_ok = True
            break
    except _requests.RequestException:
        pass
    time.sleep(0.25)

if _serve_error:
    print("Uvicorn failed to start:")
    traceback.print_exception(_serve_error[0])
    raise _serve_error[0]
if not _local_ok:
    raise RuntimeError(
        f"Local worker did not come up on port {WORKER_PORT_ACTIVE}. "
        "Try Runtime > Restart runtime, then re-run all cells."
    )

print(f"Local worker is up on http://127.0.0.1:{WORKER_PORT_ACTIVE}")


# Bring up the cloudflared tunnel and capture the public URL.
# If a previous run of this cell already spawned a tunnel, terminate it
# first so we don't leave orphaned cloudflared processes behind.
_existing_tunnel = globals().get("_tunnel")
if _existing_tunnel is not None and _existing_tunnel.poll() is None:
    try:
        _existing_tunnel.terminate()
        _existing_tunnel.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        _existing_tunnel.kill()

_tunnel_log = Path("/tmp/cloudflared.log")
if _tunnel_log.exists():
    _tunnel_log.unlink()

_tunnel = subprocess.Popen(
    [
        "cloudflared", "tunnel",
        "--no-autoupdate",
        "--url", f"http://127.0.0.1:{WORKER_PORT_ACTIVE}",
        "--logfile", str(_tunnel_log),
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

WORKER_URL = ""
_url_pat = re.compile(r"https://[A-Za-z0-9-]+\.trycloudflare\.com")
for _ in range(120):
    if _tunnel_log.exists():
        try:
            text = _tunnel_log.read_text(errors="ignore")
        except OSError:
            text = ""
        m = _url_pat.search(text)
        if m:
            WORKER_URL = m.group(0)
            break
    time.sleep(0.5)

if not WORKER_URL:
    raise RuntimeError(
        "Cloudflared tunnel did not produce a public URL within 60s. "
        "Re-run this cell, or check /tmp/cloudflared.log."
    )

print()
print("=" * 60)
print(f"Worker URL: {WORKER_URL}")
print("=" * 60)
print()
print("Verify it with:")
print(f"  curl {WORKER_URL}/health")
print()
print(
    "Keep this Colab tab open while SN Video Upscaler is processing "
    "videos. The URL is temporary and will change if the runtime restarts."
)

# Smoke-call our own /health through the tunnel so the user sees a real
# response without leaving Colab.
try:
    resp = _requests.get(f"{WORKER_URL}/health", timeout=15.0)
    print()
    print(f"GET {WORKER_URL}/health -> {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))
except _requests.RequestException as exc:
    print(f"(Could not self-test the tunnel yet: {exc})")

# PR #4 will publish WORKER_URL to a discovery topic keyed by PAIRING_CODE
# so the desktop app finds it automatically. For now we only print it.
if PAIRING_CODE:
    print()
    print(
        f"PAIRING_CODE is set ({PAIRING_CODE}); auto-publish lands in PR #4."
    )

# %% [markdown]
# ## 7. Stop Worker (optional)
#
# Run this cell to terminate the cloudflared tunnel cleanly. The local
# worker thread is a daemon — it goes away when the runtime shuts down.

# %%
_tunnel_to_stop = globals().get("_tunnel")
if _tunnel_to_stop is None:
    print("No tunnel to stop — run *Start Worker* first.")
elif _tunnel_to_stop.poll() is not None:
    print("Tunnel already stopped.")
else:
    try:
        _tunnel_to_stop.terminate()
        _tunnel_to_stop.wait(timeout=5)
        print("Cloudflared tunnel stopped.")
    except subprocess.TimeoutExpired:
        _tunnel_to_stop.kill()
        print("Cloudflared tunnel did not exit cleanly — killed.")
