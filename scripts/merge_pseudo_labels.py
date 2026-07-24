#!/usr/bin/env python3
"""Merge classifier-predicted labels for the keyword-ambiguous holdout into
chunks_pseudo_labeled/, so the (much larger) set of chunks that keyword
tagging couldn't confidently call isn't simply wasted.

This is a from-scratch reconstruction, not a recovered original: this
project's docstrings/commit messages have referenced a "merge_pseudo_labels.py"
since before this session, but no version of it was ever committed, and an
exhaustive search of every machine this pipeline has run on (hal, akdeniz,
bridges2) plus both hosts' shell histories turned up the classifier
(scripts/classify_mixed_content.R, recovered from akdeniz as
classify_mixed_akdeniz.R) but never a script that actually writes these
files -- likely done via an unsaved interactive command originally.

Input: output/mixed_content_pseudo_labels.json (written by
classify_mixed_content.R), keyed by `{arxiv_slug}__{chunk_suffix}` with
predicted_content/predicted_style fields.
Source text: corpus_classify/reference_research/mixed_content_holdout/,
named `{old_content}__{old_style}__{arxiv_slug}__{chunk_suffix}.txt` (the
old_content/old_style prefix is whatever ambiguous/ tied score it had before
being set aside -- ignored here in favor of the classifier's prediction).
Output: corpus_classify/reference_research/chunks_pseudo_labeled/, named
`{predicted_content}__{predicted_style}__{arxiv_slug}__{chunk_suffix}.txt`
to match balance_research_corpus.py's expected 4-part naming.

Clears chunks_pseudo_labeled/ first -- this is meant to fully replace a
prior pseudo-labeling pass, not accumulate alongside it (the holdout it's
predicting over is a fresh split of the current, consistently-extracted
chunks/, not the same chunk identities an older pass may have covered).

Usage: python3 scripts/merge_pseudo_labels.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS = ROOT / "output" / "mixed_content_pseudo_labels.json"
HOLDOUT = ROOT / "corpus_classify" / "reference_research" / "mixed_content_holdout"
OUT_DIR = ROOT / "corpus_classify" / "reference_research" / "chunks_pseudo_labeled"


def parse(name: str) -> tuple[str, str, str, str] | None:
    # stylo::classify() rownames are the basename with .txt stripped (this is
    # where classify_mixed_content.R's canonical_key() keys come from) --
    # strip it here too so `{arxiv_slug}__{chunk_suffix}` matches those keys.
    stem = name[:-4] if name.endswith(".txt") else name
    parts = stem.split("__")
    if len(parts) != 4:
        return None
    old_content, old_style, arxiv_slug, chunk_suffix = parts
    return old_content, old_style, arxiv_slug, chunk_suffix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Report counts without writing files")
    args = ap.parse_args()

    predictions = json.loads(PREDICTIONS.read_text(encoding="utf-8"))

    # Map `{arxiv_slug}__{chunk_suffix}` -> source path, same key scheme
    # classify_mixed_content.R's canonical_key() uses.
    by_key: dict[str, Path] = {}
    for path in sorted(HOLDOUT.glob("*.txt")):
        parsed = parse(path.name)
        if parsed is None:
            continue
        _old_content, _old_style, arxiv_slug, chunk_suffix = parsed
        by_key[f"{arxiv_slug}__{chunk_suffix}"] = path

    written = 0
    missing_source = []
    missing_prediction = []

    if not args.dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        for old in OUT_DIR.iterdir():
            if old.is_file():
                old.unlink()

    for key, pred in predictions.items():
        content = pred.get("predicted_content")
        style = pred.get("predicted_style")
        if not content or not style:
            missing_prediction.append(key)
            continue
        src = by_key.get(key)
        if src is None:
            missing_source.append(key)
            continue
        arxiv_slug, chunk_suffix = key.split("__", 1)
        dest_name = f"{content}__{style}__{arxiv_slug}__{chunk_suffix}.txt"
        if not args.dry_run:
            (OUT_DIR / dest_name).write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        written += 1

    print(f"{'Would write' if args.dry_run else 'Wrote'} {written} pseudo-labeled chunks to {OUT_DIR}")
    print(f"Missing prediction for {len(missing_prediction)} keys, missing source text for {len(missing_source)} keys")
    if missing_source[:10]:
        print("Sample missing-source keys:", missing_source[:10])


if __name__ == "__main__":
    main()
