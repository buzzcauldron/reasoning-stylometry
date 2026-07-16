#!/usr/bin/env python3
"""Re-tag reference chunks with independent content + style labels.

Previously chunk filenames encoded a single axis twice: `{style}__{topic}__...`
where topic was hardcoded equal to style (see corpus_classify/CORPUS.md and the
git history of generate_manifest_from_views.py / scrape_contemporary_arxiv.py).
That meant the "content x style quadrant" this project is named for did not
exist in training data — there was only ever a diagonal (geometric-content-and-
geometric-style, algebraic-content-and-algebraic-style).

This script re-scores every chunk's own text with the two disjoint scorers in
style_keyword_tagger.py (score_content: subject vocabulary; score_style:
rhetorical/discourse markers) and renames files to the canonical
`{content}__{style}__{arxiv_slug}__chunkNNN.txt` scheme, populating the
off-diagonal cells. Keyword output is treated as ground truth directly (no
separate "ambiguous" bucket for weak/no signal, for now).

Sources from BOTH chunks/ (currently keyword-unambiguous) and
mixed_content_holdout/ (previously set aside for hitting both keyword lists)
are re-scored and consolidated back into chunks/ -- run this whenever the
scorer or its underlying text extraction changes (e.g. the ligature-
normalization fix), then re-run split_mixed_content_holdout.py to regenerate
an up-to-date holdout from the fresh scores.

Usage: python3 scripts/retag_content_style.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from style_keyword_tagger import score_content, score_style  # noqa: E402

CHUNKS = ROOT / "corpus_classify" / "reference_research" / "chunks"
MIXED_HOLDOUT = ROOT / "corpus_classify" / "reference_research" / "mixed_content_holdout"
MANIFEST = ROOT / "corpus_classify" / "reference_research" / "manifest.json"
REPORT = ROOT / "output" / "corpus_diagnosis_content_style_retag.json"


def parse_old_name(name: str) -> tuple[str, str, str] | None:
    """Split `{old_a}__{old_b}__{arxiv_slug}__chunkNNN.txt` -> (arxiv_slug, chunk_suffix)."""
    parts = name.split("__")
    if len(parts) != 4:
        return None
    _old_a, _old_b, arxiv_slug, chunk_suffix = parts
    return arxiv_slug, chunk_suffix


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s.lower()).strip("_")[:48]


def load_expert_style_by_slug() -> dict[str, str]:
    """arXiv sources whose manifest title starts with 'cross_view style mean' carry
    a real expert/LLM style_axis rating (see generate_manifest_from_views.py) rather
    than a keyword guess — preserve that signal instead of overwriting it with the
    keyword-based score_style() used for everything else."""
    if not MANIFEST.exists():
        return {}
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    out = {}
    for src in manifest.get("sources", []):
        title = str(src.get("title", ""))
        if title.startswith("cross_view style mean"):
            out[_slug(src["arxiv"])] = src["style"]
    return out


def retag(dry_run: bool = False) -> dict:
    files = sorted(CHUNKS.glob("*.txt")) + sorted(MIXED_HOLDOUT.glob("*.txt"))
    expert_style = load_expert_style_by_slug()
    contingency = {
        "geometric__geometric": 0,
        "geometric__algebraic": 0,
        "algebraic__geometric": 0,
        "algebraic__algebraic": 0,
    }
    renamed = 0
    moved_from_holdout = 0
    skipped = []
    n_expert_style_preserved = 0

    for path in files:
        parsed = parse_old_name(path.name)
        if parsed is None:
            skipped.append(path.name)
            continue
        arxiv_slug, chunk_suffix = parsed
        text = path.read_text(encoding="utf-8", errors="ignore")
        content = score_content(text).label
        if arxiv_slug in expert_style:
            style = expert_style[arxiv_slug]
            n_expert_style_preserved += 1
        else:
            style = score_style(text).label
        contingency[f"{content}__{style}"] += 1

        new_name = f"{content}__{style}__{arxiv_slug}__{chunk_suffix}"
        dest = CHUNKS / new_name
        from_holdout = path.parent == MIXED_HOLDOUT
        if new_name != path.name or from_holdout:
            renamed += 1
            if from_holdout:
                moved_from_holdout += 1
            if not dry_run:
                if dest.exists() and dest != path:
                    # Extremely unlikely (arxiv_slug+chunk_suffix is unique per source);
                    # keep the existing file rather than clobber it.
                    skipped.append(f"{path.name} -> collision at {new_name}")
                    continue
                path.rename(dest)

    total = sum(contingency.values())
    off_diagonal = contingency["geometric__algebraic"] + contingency["algebraic__geometric"]
    report = {
        "n_chunks": total,
        "n_renamed": renamed,
        "n_moved_from_prior_holdout": moved_from_holdout,
        "n_skipped": len(skipped),
        "skipped": skipped[:20],
        "n_expert_style_preserved": n_expert_style_preserved,
        "n_keyword_style_derived": total - n_expert_style_preserved,
        "contingency_content__style": contingency,
        "off_diagonal_fraction": round(off_diagonal / total, 4) if total else 0.0,
        "note": (
            "off_diagonal_fraction is the share of chunks where content and style "
            "labels disagree (e.g. algebraic content written in geometric style). "
            "0.0 means content and style are still fully confounded; the two axes "
            "being independent heuristics does not guarantee a specific fraction, "
            "but 0.0 would indicate the scorers are not actually decoupled."
        ),
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Score and report without renaming files")
    args = ap.parse_args()

    report = retag(dry_run=args.dry_run)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {REPORT}")


if __name__ == "__main__":
    main()
