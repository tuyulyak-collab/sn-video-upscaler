# SN Video Upscaler

Windows desktop app that upscales videos with **Google Colab GPU** —
a friendly EXE on your PC, the heavy GPU work in Colab.

This repo is being built up in small, reviewable PRs. **You are looking
at the result of PR #1 — the desktop app skeleton only.** The cards and
buttons are placeholders; actual Colab connection, upload/download, and
EXE packaging arrive in later PRs.

![PR #1 skeleton — main window](docs/screenshot.png)

## What's in PR #1

- **Project setup**: `pyproject.toml`, `.gitignore`, ruff + pytest config.
- **Base desktop window** (PySide6) with the soft-pastel gradient and
  the radial glow behind the content.
- **Five glass cards in placeholder mode**:
  1. *Connect Google Colab* — header, status pill (`Waiting for Colab`),
     pairing code display, *Open Colab Notebook* + *Check Connection*
     buttons (clicks log to the activity line).
  2. *Videos* — drag-and-drop zone, file list, *Add Videos* /
     *Remove Selected* / *Clear Queue* (disabled until PR #4 lands the
     real Colab connection — for review, the queue can still be exercised
     because the disabled gating is just a flag).
  3. *Quality preset* — Fast 2× / High Quality 4× / Anime / Illustration
     radio cards.
  4. *Run* — Start, Pause, Stop, Retry Failed, Open Output Folder
     buttons.
  5. *Progress* — current-file label, three progress bars (Uploading,
     Processing on GPU, Downloading result), Completed / Failed /
     Remaining counts, and an activity line.
- **Header**: app title, subtitle "Upscale videos with Google Colab GPU",
  *Output Folder* shortcut, and a settings cog (placeholder).
- **In-memory `AppSettings`** with default output folder and a generated
  pairing code (`SNVU-XXXXXXXX`).
- **Smoke tests** (`tests/test_skeleton.py`).
- **`docs/screenshot.png`** of the running skeleton.

## Roadmap (next PRs)

- **PR #2** — Final UI/UX polish to match the Gemini/Canvas reference.
- **PR #3** — Google Colab worker notebook (`colab/sn_video_upscaler_colab_worker.ipynb`).
- **PR #4** — Desktop ↔ Colab connection (auto-discovery via ntfy.sh).
- **PR #5** — Single video upload → process → download.
- **PR #6** — Batch queue, one-by-one.
- **PR #7** — Polish, error handling, Windows EXE packaging, README, QA.

## Run from source

Requires Python 3.10+.

```bash
# Clone
git clone https://github.com/tuyulyak-collab/sn-video-upscaler.git
cd sn-video-upscaler

# Virtualenv + install
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -e ".[dev]"

# Run the app
sn-video-upscaler
# or:
python -m sn_video_upscaler.main
```

### Lint and tests

```bash
ruff check desktop tests
pytest tests
```

## What's still placeholder

- **Connect Google Colab card.** Status is hard-coded to "Waiting for Colab".
  Buttons emit signals but do not open a notebook or probe a worker. (PR #3, #4)
- **Videos card.** Disabled by default with the helper text
  "Connect Google Colab first to add videos". The Add / Remove / Clear
  flow itself works on a `list[str]` of file paths but does not upload
  anything yet. (PR #5/#6)
- **Run card.** Buttons log to the activity line and update the progress
  bars are not wired to a real worker. (PR #5, #6)
- **Progress card.** Bars and counts are inert in the skeleton. (PR #5, #6)
- **Settings cog.** Pops a "coming in a later PR" message. (PR #7)
- **Output folder shortcut** does open the configured folder with the
  platform's file manager.
- **`AppSettings`** is in-memory only. JSON persistence under
  `platformdirs.user_config_dir(...)` lands in PR #7.

## Project structure

```
desktop/sn_video_upscaler/
├── __init__.py
├── main.py
├── theme.py
├── settings.py
└── ui/
    ├── widgets.py        # GradientBackground, GlassCard, StatusPill, DropZone, ...
    ├── main_window.py    # Composes the cards (placeholder wiring)
    ├── colab_card.py     # Connect Google Colab (placeholder state machine)
    ├── queue_card.py     # Videos (drag-drop, list, add/remove/clear)
    ├── preset_card.py    # Quality preset (Fast 2×, High Quality 4×, Anime)
    ├── start_card.py     # Run controls
    └── progress_card.py  # Bars + counts + activity line
docs/
└── screenshot.png        # PR #1 main window
tests/
└── test_skeleton.py      # smoke tests
pyproject.toml
README.md
```

## License

MIT.
