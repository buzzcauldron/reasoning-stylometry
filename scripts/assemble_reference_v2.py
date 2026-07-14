#!/usr/bin/env python3
"""Assemble validated training corpora from research chunks + optional elementary pairs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "corpus_classify" / "reference_research" / "chunks"
ELEMENTARY = ROOT / "corpus_classify" / "reference_elementary"
OUT = ROOT / "corpus_classify" / "reference_v2"


def assemble(include_elementary: bool = False, min_words: int = 400) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.txt"):
        old.unlink()

    counts = {"research": 0, "elementary": 0, "skipped_short": 0}

    def word_count(p: Path) -> int:
        return len(p.read_text(encoding="utf-8", errors="ignore").split())

    for src in sorted(RESEARCH.glob("*.txt")):
        if word_count(src) >= min_words:
            shutil.copy2(src, OUT / src.name)
            counts["research"] += 1
        else:
            counts["skipped_short"] += 1

    if include_elementary:
        for src in sorted(ELEMENTARY.glob("*.txt")):
            if word_count(src) >= 150:
                shutil.copy2(src, OUT / src.name)
                counts["elementary"] += 1

    manifest = {
        "path": str(OUT),
        "total": counts["research"] + counts["elementary"],
        **counts,
    }
    (OUT / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    assemble()
