"""Convert colab/source/notebook.py into a Jupyter (.ipynb) notebook.

The notebook source is authored as a single Python file with cell
markers (`# %%` for code cells, `# %% [markdown]` for markdown cells).
This script parses the markers and emits a valid nbformat-4 notebook.

Run from the repo root:

    python scripts/build_notebook.py

It rewrites colab/sn_video_upscaler_colab_worker.ipynb in place.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "colab" / "source" / "notebook.py"
OUTPUT = REPO_ROOT / "colab" / "sn_video_upscaler_colab_worker.ipynb"


def _strip_md_prefix(line: str) -> str:
    """Remove the leading '# ' / '#' that markdown cells use."""
    if line.startswith("# "):
        return line[2:]
    if line == "#":
        return ""
    return line


def parse_cells(source: str) -> list[tuple[str, list[str]]]:
    """Parse Python source with `# %%` markers into (cell_type, lines) pairs."""
    cells: list[tuple[str, list[str]]] = []
    cell_type = "code"
    buf: list[str] = []
    in_header = True

    for raw_line in source.splitlines():
        stripped = raw_line.rstrip()
        if stripped.startswith("# %% [markdown]"):
            if not in_header and buf:
                cells.append((cell_type, buf))
            cell_type = "markdown"
            buf = []
            in_header = False
            continue
        if stripped.startswith("# %%"):
            if not in_header and buf:
                cells.append((cell_type, buf))
            cell_type = "code"
            buf = []
            in_header = False
            continue
        if in_header:
            # Skip the file-level header (license / generator hint).
            continue
        if cell_type == "markdown":
            buf.append(_strip_md_prefix(raw_line))
        else:
            buf.append(raw_line)

    if buf:
        cells.append((cell_type, buf))

    # Trim leading/trailing blank lines per cell.
    cleaned: list[tuple[str, list[str]]] = []
    for ctype, lines in cells:
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if lines:
            cleaned.append((ctype, lines))
    return cleaned


def _to_source(lines: list[str]) -> list[str]:
    """nbformat expects each line ending with \n except optionally the last."""
    out = [line + "\n" for line in lines]
    if out:
        out[-1] = out[-1].rstrip("\n")
    return out


def build_notebook(cells: list[tuple[str, list[str]]]) -> dict:
    nb_cells: list[dict] = []
    for cell_type, lines in cells:
        if cell_type == "markdown":
            nb_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": _to_source(lines),
            })
        else:
            nb_cells.append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": _to_source(lines),
            })

    return {
        "cells": nb_cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {
                "name": "sn_video_upscaler_colab_worker.ipynb",
                "provenance": [],
                "toc_visible": True,
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main() -> int:
    if not SOURCE.exists():
        print(f"Notebook source not found: {SOURCE}", file=sys.stderr)
        return 1
    cells = parse_cells(SOURCE.read_text())
    nb = build_notebook(cells)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT.relative_to(REPO_ROOT)}  ({len(cells)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
