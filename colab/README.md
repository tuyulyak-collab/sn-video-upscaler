# Colab worker — `sn_video_upscaler_colab_worker.ipynb`

This is the Google Colab notebook that the **SN Video Upscaler** desktop
app talks to. **PR #3B** adds the single-video upscaling pipeline on top
of the PR #3A foundation.

## What this notebook exposes

| Endpoint | Purpose |
|---|---|
| `GET  /health` | readiness + GPU info + active job |
| `POST /upscale` | accept one video file + quality preset, kick off the pipeline |
| `GET  /status/{job_id}` | current phase + progress for a running job |
| `GET  /download/{job_id}` | the upscaled MP4 once it finishes |

## How to open and run

1. Open the notebook in Colab. Easiest path: from this repo, click
   `colab/sn_video_upscaler_colab_worker.ipynb` and then click the
   **Open in Colab** button GitHub renders for `.ipynb` files.
2. **Runtime → Change runtime type → Hardware accelerator: GPU**, then
   click **Save**.
3. Click **Connect** (top-right of the notebook).
4. Run the **Setup** cells in order:
   - *1. Pairing code* — paste the `SNVU-XXXXXXXX` from the desktop app
     if you have one (optional in PR #3A/#3B; required from PR #4 onward).
   - *2. Install dependencies* — installs FFmpeg, the web stack
     (`fastapi`, `uvicorn`, `python-multipart`), and Real-ESRGAN
     (`basicsr`, `facexlib`, `gfpgan`, `realesrgan`). First run takes
     1–3 minutes.
   - *3. GPU check*
   - *4. Working folders*
   - *5. Pipeline helpers* — defines the upscaling pipeline. No visible
     output other than `Pipeline helpers loaded: fast_2x, high_quality_4x, anime_illustration`.
5. Run *6. Start Worker*. After ~10–30s it will print:
   ```
   ============================================================
   Worker URL: https://xxxxx-xxxxx-xxxxx.trycloudflare.com
   ============================================================
   ```
6. Keep this Colab tab open while the desktop app is processing videos.

## Quality presets

| Preset | Real-ESRGAN model | Native scale | Best for |
|---|---|---|---|
| `fast_2x` | `RealESRGAN_x2plus` | 2× | quick passes, mild detail recovery |
| `high_quality_4x` | `RealESRGAN_x4plus` | 4× | photoreal, general video |
| `anime_illustration` | `RealESRGAN_x4plus_anime_6B` | 4× | anime, line art, stylized |

## Smoke-test with one short clip (curl)

> Use a 3–5 second clip first. Real-ESRGAN at 4× is GPU-bound and a
> long input can chew through a Colab session.

```bash
WORKER="https://xxxxx-xxxxx-xxxxx.trycloudflare.com"

# 1. Health check.
curl -s "$WORKER/health" | jq
# {"status":"ready","gpu_available":true,"gpu_name":"Tesla T4",...,
#  "presets":["fast_2x","high_quality_4x","anime_illustration"]}

# 2. Upload a clip + pick a preset.
curl -s -F "video=@my_clip.mp4" -F "preset=fast_2x" \
  "$WORKER/upscale" | jq
# {"job_id":"a1b2c3d4e5f6","file_name":"my_clip.mp4","preset":"fast_2x",
#  "status":"uploaded","current_phase":"uploaded","progress":0.0,
#  "output_ready":false,"error":null,...}

# 3. Poll status until output_ready=true.
curl -s "$WORKER/status/a1b2c3d4e5f6" | jq
# Phases you'll see, in order:
#   uploaded -> extracting_frames -> upscaling_frames
#   -> rebuilding_video -> preserving_audio -> completed

# 4. Download the upscaled MP4.
curl -O -J "$WORKER/download/a1b2c3d4e5f6"
```

### Sample `/status/{job_id}` while upscaling

```json
{
  "job_id": "a1b2c3d4e5f6",
  "file_name": "my_clip.mp4",
  "preset": "fast_2x",
  "status": "upscaling_frames",
  "current_phase": "upscaling_frames",
  "progress": 0.42,
  "output_ready": false,
  "error": null,
  "started_at": "2026-05-06T10:00:00.000000+00:00",
  "updated_at": "2026-05-06T10:00:23.456789+00:00",
  "frame_count": 150
}
```

### Sample `/status/{job_id}` after completion

```json
{
  "job_id": "a1b2c3d4e5f6",
  "file_name": "my_clip.mp4",
  "preset": "fast_2x",
  "status": "completed",
  "current_phase": "completed",
  "progress": 1.0,
  "output_ready": true,
  "error": null,
  "started_at": "2026-05-06T10:00:00.000000+00:00",
  "updated_at": "2026-05-06T10:01:12.345678+00:00",
  "frame_count": 150
}
```

## Supported input formats

`.mp4`, `.mov`, `.mkv`, `.webm`, `.avi`. Output is always MP4 (`libx264`,
`yuv420p`, `+faststart`). Original audio is preserved when the input has
an audio stream.

## Error responses

`POST /upscale`:
- `400` — unknown preset, unsupported file extension, or empty upload.
- `409` — worker is already busy with another job (PR #3B is single-video
  by design; batch queueing arrives in PR #6).
- `413` — upload exceeded the 2 GiB hard cap.
- `503` — no GPU detected on the runtime.

`GET /status/{job_id}`:
- `404` — unknown `job_id`.
- `200` with `status: "failed"` and a populated `error` field — the
  pipeline raised. The error message indicates which phase blew up
  (extraction, upscaling, rebuild, audio mux).

`GET /download/{job_id}`:
- `404` — unknown `job_id`.
- `409` — output isn't ready yet (poll `/status` until `output_ready`).
- `410` — output file is missing (Colab runtime was recycled).

## Common Colab issues

| Symptom | Fix |
|---|---|
| `No GPU detected.` printed by GPU check cell | Runtime → Change runtime type → **GPU** → Save → Connect → re-run setup cells. |
| `Cannot connect to runtime` | Click *Reconnect* (top-right). Colab idles sessions out after ~90 minutes. |
| Worker URL changed | Re-running *Start Worker* always issues a fresh `trycloudflare.com` URL. The desktop app rediscovers it via your pairing code (PR #4 onward). |
| `Cloudflared tunnel did not produce a public URL within 60s` | Re-run *Start Worker*. If it persists, *Restart runtime* and re-run setup. |
| `basicsr` import fails with `functional_tensor` | The install cell auto-patches `basicsr/data/degradations.py` for newer torchvision. If the patch was skipped, *Restart runtime* and re-run *Install dependencies*. |
| `/upscale` first request is slow | Real-ESRGAN downloads its ~64 MB weight file on first use, per preset. Subsequent jobs reuse the cached weights in `/content/sn_video_upscaler/weights/`. |

## Editing the notebook

The `.ipynb` is **generated from `colab/source/notebook.py`** so each cell
is reviewable as plain Python. To change the notebook:

```bash
# 1. Edit colab/source/notebook.py
# 2. Regenerate the .ipynb:
python scripts/build_notebook.py
# 3. Verify
pytest tests/test_notebook.py -q
```

Cell markers in the source: `# %%` for code cells, `# %% [markdown]`
for markdown cells. Anything before the first marker is treated as the
file header and dropped.

## Out of scope for PR #3B

- Auto-publish of the worker URL via the pairing-code discovery channel — **PR #4**.
- Desktop app upload/download wiring — **PR #5**.
- Batch queue (one video at a time across many) — **PR #6**.
- EXE packaging and final QA — **PR #7**.
