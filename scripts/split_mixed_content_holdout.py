#!/usr/bin/env python3
"""Set aside chunks tagged with BOTH geometric and algebraic content keywords
(plus anything tagged via the "algebraic geometry" keyword specifically) as a
held-out test set, instead of letting them join the training pool.

Most research-length chunks mention vocabulary from both CONTENT_GEOMETRIC_
KEYWORDS and CONTENT_ALGEBRAIC_KEYWORDS somewhere -- that's expected, not a
bug. This script trains the content classifier only on the chunks that read
as unambiguously single-topic by keyword tagging, and holds out the (larger)
set that reads as topically mixed to see how well that classifier generalizes
to realistic, non-clean-cut papers.

Run after retag_content_style.py (chunks must already be tagged) and before
balance_research_corpus.py (so the holdout set never enters
balanced_content/balanced_style).

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

CHUNKS = ROOT / "corpus_classify" / "reference_research" / "chunks"
HOLDOUT = ROOT / "corpus_classify" / "reference_research" / "mixed_content_holdout"
HOLDOUT_CONTENT = ROOT / "corpus_classify" / "reference_research" / "mixed_content_holdout_content_leading"
HOLDOUT_STYLE = ROOT / "corpus_classify" / "reference_research" / "mixed_content_holdout_style_leading"
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

    for path in sorted(CHUNKS.glob("*.txt")):
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

    print(f"{'Would move' if args.dry_run else 'Moving'} {moved} mixed-content chunks "
          f"({kept} unambiguous chunks remain in the training pool)")

    if not args.dry_run:
        HOLDOUT.mkdir(parents=True, exist_ok=True)
        for path in to_move:
            shutil.move(str(path), str(HOLDOUT / path.name))

        # Build content-leading and style-leading copies for direct use as a
        # stylo test.corpus.dir against each axis's classifier.
        HOLDOUT_CONTENT.mkdir(parents=True, exist_ok=True)
        HOLDOUT_STYLE.mkdir(parents=True, exist_ok=True)
        for old in HOLDOUT_CONTENT.glob("*.txt"):
            old.unlink()
        for old in HOLDOUT_STYLE.glob("*.txt"):
            old.unlink()
        for path in HOLDOUT.glob("*.txt"):
            parsed = parse(path.name)
            content, style, arxiv_slug, chunk_suffix = parsed
            shutil.copy2(path, HOLDOUT_CONTENT / f"{content}__{style}__{arxiv_slug}__{chunk_suffix}")
            shutil.copy2(path, HOLDOUT_STYLE / f"{style}__{content}__{arxiv_slug}__{chunk_suffix}")

    report = {
        "n_moved_to_holdout": moved,
        "n_kept_in_training_pool": kept,
        "holdout_dir": str(HOLDOUT),
        "examples": examples,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
