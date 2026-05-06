# Colab worker — `sn_video_upscaler_colab_worker.ipynb`

This is the Google Colab notebook that the **SN Video Upscaler** desktop
app talks to. **PR #3A** is the foundation only — it boots the worker
and exposes a `/health` endpoint. Real video upscaling lands in PR #3B.

## How to open and run

1. Open the notebook in Colab. Easiest path: from this repo, click
   `colab/sn_video_upscaler_colab_worker.ipynb` and then click the
   **Open in Colab** button GitHub renders for `.ipynb` files.
2. **Runtime → Change runtime type → Hardware accelerator: GPU**, then
   click **Save**.
3. Click **Connect** (top-right of the notebook).
4. Run the **Setup** cells in order:
   - *1. Pairing code* — paste the `SNVU-XXXXXXXX` from the desktop app
     if you have one (optional in PR #3A; required from PR #4 onward).
   - *2. Install dependencies*
   - *3. GPU check*
   - *4. Working folders*
5. Run *5. Start Worker*. After ~10–30s it will print:
   ```
   ============================================================
   Worker URL: https://xxxxx-xxxxx-xxxxx.trycloudflare.com
   ============================================================
   ```
6. Keep this Colab tab open while the desktop app is processing videos.

## Verify `/health`

From any terminal:

```bash
curl https://xxxxx-xxxxx-xxxxx.trycloudflare.com/health
```

Expected response:

```json
{
  "status": "ready",
  "app": "SN Video Upscaler",
  "version": "0.3.0a",
  "gpu_available": true,
  "gpu_name": "Tesla T4",
  "current_job": null,
  "started_at": "2026-05-06T10:00:00.000000+00:00",
  "message": "Google Colab GPU is ready."
}
```

If `gpu_available` is `false`, redo step 2 (Runtime → GPU) and re-run
the setup cells.

## Common Colab issues

| Symptom | Fix |
|---|---|
| `No GPU detected.` printed by GPU check cell | Runtime → Change runtime type → **GPU** → Save → Connect → re-run setup cells. |
| `Cannot connect to runtime` | Click *Reconnect* (top-right). Colab idles sessions out after ~90 minutes. |
| Worker URL changed | Re-running *Start Worker* always issues a fresh `trycloudflare.com` URL. The desktop app rediscovers it via your pairing code (PR #4 onward). |
| `Cloudflared tunnel did not produce a public URL within 60s` | Re-run *Start Worker*. If it persists, *Restart runtime* and re-run setup. |

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

## Out of scope for PR #3A

- Real-ESRGAN install + frame upscaling
- `POST /upscale`, `GET /status/{job_id}`, `GET /download/{job_id}` endpoints
- Auto-publish of the worker URL via the pairing-code discovery channel

These arrive in **PR #3B** (single-video pipeline) and **PR #4** (desktop ↔ worker).
