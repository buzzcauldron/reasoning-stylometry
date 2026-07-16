#!/usr/bin/env python3
"""Build balanced training sets for the content and style classifiers.

Chunks in reference_research/chunks/ are named
`{content}__{style}__{arxiv_slug}__chunkNNN.txt` with content and style labels
assigned independently by retag_content_style.py (see that script and
corpus_classify/CORPUS.md for why this matters — content and style used to be
the same value by construction).

stylo::classify() always uses the filename segment before the first
underscore as the ground-truth class. That means training a CONTENT
classifier and a STYLE classifier requires two differently-ordered filename
views of the same chunks:

- balanced_content/: `{content}__{style}__...` (content leading) — matches the
  existing corpus_classify/jams_quadrant test file convention.
- balanced_style/: `{style}__{content}__...` (style leading) — needs a
  matching style-leading copy of the test files (see
  scripts/make_style_leading_targets.py).

Each set is independently subsampled 50/50 on its own leading label, then
capped at MAX_PER_CLASS per class (env var STYLO_MAX_PER_CLASS, default 5000).
stylo::classify()/rolling.classify() re-load and re-tokenize the whole
training corpus from scratch on every call; with 4 JAMS papers x 2 axes
that's 8+ reloads per pipeline run, which OOM-killed a run against the
uncapped pool (~15k/~11k chunks) on a memory-constrained machine. Run the
bigger, higher-cap version on a machine with enough RAM (see akdeniz setup in
project notes) rather than lowering this back down.

Also pulls in corpus_classify/reference_research/chunks_pseudo_labeled/ if
present -- chunks originally held out by split_mixed_content_holdout.py
(ambiguous by keyword tagging) whose content/style labels were instead
assigned by the trained classifier itself (see
scripts/merge_pseudo_labels.py). These are pseudo-labels, not
keyword-verified ground truth; provenance (verified vs pseudo-labeled) is
reported in the balance report so this can be audited or excluded later.
"""

from __future__ import annotations

import json
import os
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# STYLO_LEMMATIZED=1 builds from the lemmatized sibling pools (see
# lemmatize_corpus.py) into balanced_content_lemmatized/balanced_style_lemmatized,
# for A/B comparison against the raw-text balanced sets.
SUFFIX = "_lemmatized" if os.environ.get("STYLO_LEMMATIZED") == "1" else ""
RR = ROOT / "corpus_classify" / "reference_research"
CHUNKS = RR / f"chunks{SUFFIX}"
PSEUDO_LABELED = RR / f"chunks_pseudo_labeled{SUFFIX}"
TEXTBOOK_CHUNKS = RR / f"textbook_chunks{SUFFIX}"
BALANCED_CONTENT = RR / f"balanced_content{SUFFIX}"
BALANCED_STYLE = RR / f"balanced_style{SUFFIX}"
REPORT = ROOT / "output" / f"corpus_balance_report{SUFFIX}.json"
MAX_PER_CLASS = int(os.environ.get("STYLO_MAX_PER_CLASS", "5000"))


def parse(name: str) -> tuple[str, str, str, str] | None:
    parts = name.split("__")
    if len(parts) != 4:
        return None
    content, style, arxiv_slug, chunk_suffix = parts
    return content, style, arxiv_slug, chunk_suffix


def build_balanced(out_dir: Path, axis: str, seed: int = 42) -> dict:
    """axis: 'content' or 'style'. Names the leading segment of out_dir files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.txt"):
        old.unlink()

    by_label: dict[str, list[Path]] = {"geometric": [], "algebraic": []}
    provenance: dict[Path, str] = {}
    pools = [("verified", CHUNKS)]
    if PSEUDO_LABELED.exists():
        pools.append(("pseudo_labeled", PSEUDO_LABELED))
    if TEXTBOOK_CHUNKS.exists():
        pools.append(("textbook", TEXTBOOK_CHUNKS))
    for source_name, pool_dir in pools:
        for path in pool_dir.glob("*.txt"):
            parsed = parse(path.name)
            if parsed is None:
                continue
            content, style, _, _ = parsed
            label = content if axis == "content" else style
            if label not in by_label:
                continue
            by_label[label].append(path)
            provenance[path] = source_name

    rng = random.Random(seed)
    geo, alg = by_label["geometric"], by_label["algebraic"]
    if len(alg) > len(geo):
        alg = rng.sample(alg, len(geo))
    elif len(geo) > len(alg):
        geo = rng.sample(geo, len(alg))

    if len(geo) > MAX_PER_CLASS:
        geo = rng.sample(geo, MAX_PER_CLASS)
    if len(alg) > MAX_PER_CLASS:
        alg = rng.sample(alg, MAX_PER_CLASS)

    source_counts = {"verified": 0, "pseudo_labeled": 0, "textbook": 0}
    for src in geo + alg:
        content, style, arxiv_slug, chunk_suffix = parse(src.name)
        if axis == "content":
            new_name = f"{content}__{style}__{arxiv_slug}__{chunk_suffix}"
        else:
            new_name = f"{style}__{content}__{arxiv_slug}__{chunk_suffix}"
        shutil.copy2(src, out_dir / new_name)
        source_counts[provenance[src]] += 1

    return {
        "axis": axis, "geometric": len(geo), "algebraic": len(alg), "total": len(geo) + len(alg),
        "n_verified": source_counts["verified"],
        "n_pseudo_labeled": source_counts["pseudo_labeled"],
        "n_textbook": source_counts["textbook"],
    }


def main() -> None:
    stats_content = build_balanced(BALANCED_CONTENT, "content")
    stats_style = build_balanced(BALANCED_STYLE, "style")

    report = {"balanced_content": stats_content, "balanced_style": stats_style}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"balanced_content: {stats_content['total']} chunks "
          f"({stats_content['geometric']} geo / {stats_content['algebraic']} alg) "
          f"[{stats_content['n_verified']} verified / {stats_content['n_pseudo_labeled']} pseudo-labeled / "
          f"{stats_content['n_textbook']} textbook] -> {BALANCED_CONTENT}")
    print(f"balanced_style:   {stats_style['total']} chunks "
          f"({stats_style['geometric']} geo / {stats_style['algebraic']} alg) "
          f"[{stats_style['n_verified']} verified / {stats_style['n_pseudo_labeled']} pseudo-labeled / "
          f"{stats_style['n_textbook']} textbook] -> {BALANCED_STYLE}")
    print(f"Wrote {REPORT}")


if __name__ == "__main__":
    main()
