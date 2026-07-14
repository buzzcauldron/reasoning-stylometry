#!/usr/bin/env python3
"""Relabel mis-tagged chunks and build balanced research training set."""

from __future__ import annotations

import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "corpus_classify" / "reference_research" / "chunks"
BALANCED = ROOT / "corpus_classify" / "reference_research" / "balanced"

# Force-correct arXiv ids mislabeled by HTML aggregation (topology → geometric)
FORCE_GEOMETRIC = {
    "math_0306277",
    "math_0701334",
    "math_0607446",
    "math_9807012",
    "math_0608426",
    "math_0505035",
    "math_0306388",
    "math_0412357",
    "math_0503113",
    "math_0701247",
    "math_0607442",
}

FORCE_ALGEBRAIC = {
    "math_0407161",
    "math_0109048",
    "math_0211391",
    "1103_5619",
}


def relabel_chunks() -> int:
    fixed = 0
    for path in list(CHUNKS.glob("*.txt")):
        name = path.name
        if not name.startswith(("geometric__", "algebraic__")):
            continue
        parts = name.split("__", 2)
        if len(parts) < 3:
            continue
        current_style, topic, rest = parts[0], parts[1], parts[2]
        slug = rest.split("__chunk")[0]
        want = None
        if slug in FORCE_GEOMETRIC:
            want = "geometric"
        elif slug in FORCE_ALGEBRAIC:
            want = "algebraic"
        if want and want != current_style:
            new_name = f"{want}__{topic}__{rest}"
            path.rename(CHUNKS / new_name)
            fixed += 1
    return fixed


def build_balanced(seed: int = 42) -> dict:
    BALANCED.mkdir(parents=True, exist_ok=True)
    for old in BALANCED.glob("*.txt"):
        old.unlink()

    geo = sorted(CHUNKS.glob("geometric__*.txt"))
    alg = sorted(CHUNKS.glob("algebraic__*.txt"))
    rng = random.Random(seed)
    if len(alg) > len(geo):
        alg = rng.sample(alg, len(geo))
    elif len(geo) > len(alg):
        geo = rng.sample(geo, len(alg))

    for src in geo + alg:
        shutil.copy2(src, BALANCED / src.name)

    stats = {"geometric": len(geo), "algebraic": len(alg), "total": len(geo) + len(alg)}
    return stats


def main() -> None:
    fixed = relabel_chunks()
    stats = build_balanced()
    print(f"Relabeled {fixed} chunk files")
    print(f"Balanced corpus: {stats['total']} chunks ({stats['geometric']} geo / {stats['algebraic']} alg)")
    print(f"Output: {BALANCED}")


if __name__ == "__main__":
    main()
