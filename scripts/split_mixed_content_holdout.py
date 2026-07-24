#!/usr/bin/env python3
"""Set aside chunks tagged with BOTH geometric and algebraic content keywords
(plus anything tagged via the "algebraic geometry" keyword specifically) as a
held-out test set, instead of letting them join the CONTENT training pool.

Most research-length chunks mention vocabulary from both CONTENT_GEOMETRIC_
KEYWORDS and CONTENT_ALGEBRAIC_KEYWORDS somewhere -- that's expected, not a
bug. This script trains the content classifier only on the chunks that read
as unambiguously single-topic by keyword tagging, and holds out the (larger)
set that reads as topically mixed to see how well that classifier generalizes
to realistic, non-clean-cut papers.

Operates ONLY on chunks_content/ -- this check is inherently content-specific
(it scores CONTENT_GEOMETRIC_KEYWORDS/CONTENT_ALGEBRAIC_KEYWORDS), so it must
never touch chunks_style/. It used to operate on a single chunks/ pool shared
by both axes, which meant a chunk removed here for having mixed CONTENT
vocabulary was also silently unavailable for STYLE training even when its
style score was perfectly confident -- confirmed to measurably hurt style
accuracy in practice (2026-07-23 investigation). See retag_content_style.py's
header for the full chunks_content/chunks_style split this fixed.

A chunk moved to content_mixed_holdout/ by this script keeps whatever
chunks_style/ membership it already has (untouched, unaffected) -- this
holdout is purely a content-axis concern.

Run after retag_content_style.py (chunks_content/ must already exist) and
before balance_research_corpus.py (so the holdout set never enters
balanced_content/).

Usage: python3 scripts/split_mixed_content_holdout.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from style_keyword_tagger import score_content  # noqa: E402

CHUNKS_CONTENT = ROOT / "corpus_classify" / "reference_research" / "chunks_content"
HOLDOUT = ROOT / "corpus_classify" / "reference_research" / "content_mixed_holdout"
REPORT = ROOT / "output" / "mixed_content_holdout_report.json"


def parse(name: str) -> tuple[str, str, str, str] | None:
    parts = name.split("__")
    if len(parts) != 4:
        return None
    content, style, arxiv_slug, chunk_suffix = parts
    return content, style, arxiv_slug, chunk_suffix


def is_mixed(score) -> bool:
    if score.hits_geo and score.hits_alg:
        return True
    if "algebraic geometry" in score.hits_alg:
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Report counts without moving files")
    args = ap.parse_args()

    moved = 0
    kept = 0
    examples = []
    to_move: list[Path] = []

    for path in sorted(CHUNKS_CONTENT.glob("*.txt")):
        parsed = parse(path.name)
        if parsed is None:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        score = score_content(text)
        if is_mixed(score):
            moved += 1
            to_move.append(path)
            if len(examples) < 20:
                examples.append(
                    {
                        "file": path.name,
                        "hits_geo": score.hits_geo,
                        "hits_alg": score.hits_alg,
                        "margin": round(score.margin, 2),
                    }
                )
        else:
            kept += 1

    print(f"{'Would move' if args.dry_run else 'Moving'} {moved} mixed-content chunks out of chunks_content/ "
          f"({kept} unambiguous chunks remain in the content training pool; chunks_style/ is untouched)")

    if not args.dry_run:
        HOLDOUT.mkdir(parents=True, exist_ok=True)
        for old in HOLDOUT.glob("*.txt"):
            old.unlink()
        for path in to_move:
            shutil.move(str(path), str(HOLDOUT / path.name))

    report = {
        "n_moved_to_holdout": moved,
        "n_kept_in_content_pool": kept,
        "holdout_dir": str(HOLDOUT),
        "examples": examples,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
