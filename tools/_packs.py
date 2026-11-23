"""Shared helpers for the repository tools."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKS = ROOT / "packs"
REQUIRED = ("id", "name", "summary", "status", "version", "tags")
STATUSES = ("available", "beta", "idea")


def pack_dirs():
    """Real packs: folders under packs/ that contain a pack.json (the template does not count)."""
    return sorted(p for p in PACKS.iterdir() if p.is_dir() and not p.name.startswith("_") and (p / "pack.json").exists())


def load_pack(path):
    return json.loads((path / "pack.json").read_text(encoding="utf-8"))
