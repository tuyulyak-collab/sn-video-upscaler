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
# **PR #3A scope**: foundation only. This notebook installs base
# dependencies, checks the GPU, creates the working folders, and starts
# a tiny worker that exposes a single `GET /health` endpoint plus a
# public URL. Real video upscaling (upload → process → download) lands
# in PR #3B.
#
# ---
#
# ## How to run this notebook
#
# 1. Open this notebook in **Google Colab** (File → Open notebook → GitHub
#    URL, or click the *Open in Colab* badge in the repo).
# 2. **Runtime → Change runtime type → Hardware accelerator → GPU**, then click *Save*.
# 3. Click **Connect** (top-right of the notebook).
# 4. Run the **Setup** cells (in order). They install FFmpeg + Python deps.
# 5. Run **Start Worker**. The cell will print something like:
#    ```
#    Worker URL: https://xxxxx-xxxxx-xxxxx.trycloudflare.com
#    ```
# 6. Keep this Colab tab **open** while SN Video Upscaler is processing
#    videos. If the runtime disconnects, just re-run **Start Worker**.
#
# ## Common Colab issues
#
# - **"No GPU detected"** — go back to step 2 and pick **GPU**.
# - **"Cannot connect to runtime"** — click *Reconnect*; Colab idles
#   sessions out after ~90 minutes.
# - **"Worker URL changed"** — Colab gives you a new tunnel URL every
#   time you re-run the start cell. The desktop app rediscovers it
#   automatically (PR #4) using your pairing code.

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
# - **Python packages** for the temporary worker: `fastapi`, plain
#   `uvicorn` (no `[standard]` — uvloop conflicts with our threaded
#   startup), and `requests` (for publishing the worker URL in PR #4).
# - **cloudflared** gives us a public HTTPS URL into the Colab runtime.
#
# Real-ESRGAN / Torch installation is intentionally **deferred to PR #3B**
# so this PR stays small and reviewable.

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

# Worker dependencies. Plain `uvicorn` (not `uvicorn[standard]`) — uvloop
# can't be patched by nest_asyncio and we don't need its perf for a
# low-traffic worker. We also explicitly remove uvloop in case a previous
# run of this cell (or the runtime image) already installed it; otherwise
# uvicorn would auto-detect and use it.
_run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "uvloop"], check=False)
_run([
    sys.executable, "-m", "pip", "install", "-q",
    "fastapi==0.115.5",
    "uvicorn==0.32.0",
    "requests==2.32.3",
])

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
# These directories are reused by every job so we don't re-create them
# on each video — PR #3B will write `input/`, `frames/`, etc. inside.

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
# ## 5. Start Worker
#
# This cell does four things:
#
# 1. Defines a tiny **FastAPI app** with a single `GET /health` endpoint
#    that reports GPU availability + worker readiness.
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
from datetime import datetime, timezone
from pathlib import Path

import requests as _requests
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse


WORKER_VERSION = "0.3.0a"  # PR #3A: foundation only.
STARTED_AT = datetime.now(timezone.utc).isoformat()


app = FastAPI(title=f"{APP_NAME} Colab Worker", version=WORKER_VERSION)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({
        "status": "ready",
        "app": APP_NAME,
        "version": WORKER_VERSION,
        "gpu_available": GPU_AVAILABLE,
        "gpu_name": GPU_NAME,
        "current_job": None,
        "started_at": STARTED_AT,
        "message": (
            "Google Colab GPU is ready."
            if GPU_AVAILABLE
            else "No GPU detected. Change Runtime > GPU and re-run setup."
        ),
    })


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
# ## 6. Stop Worker (optional)
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
