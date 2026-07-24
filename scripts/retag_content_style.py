#!/usr/bin/env python3
"""Tag reference chunks with independent content + style labels, writing two
independent pools instead of one shared one.

Previously chunk filenames encoded a single axis twice: `{style}__{topic}__...`
where topic was hardcoded equal to style (see corpus_classify/CORPUS.md and the
git history of generate_manifest_from_views.py / scrape_contemporary_arxiv.py).
That meant the "content x style quadrant" this project is named for did not
exist in training data — there was only ever a diagonal (geometric-content-and-
geometric-style, algebraic-content-and-algebraic-style).

This script re-scores every chunk's own text with the two disjoint scorers in
style_keyword_tagger.py (score_content: subject vocabulary; score_style:
rhetorical/discourse markers) and writes each chunk into chunks_content/
and/or chunks_style/ based on ITS OWN axis's confidence -- a chunk with a
confident content label but an ambiguous (tied/no-signal) style score still
gets duplicated into chunks_content/ (with a placeholder "ambiguous" in the
unused style slot of its filename); it's simply absent from chunks_style/.
This used to be one shared chunks/ pool gated by a single ambiguous-on-
EITHER-axis check, which meant a chunk useless for content dragged a
perfectly good style label down with it (and vice versa) -- confirmed to
measurably hurt style accuracy in practice (2026-07-23 investigation) once
split_mixed_content_holdout.py's content-only "hits both dictionaries" filter
started removing chunks from the single shared pool that had nothing to do
with style.

chunks/ (raw output of build_research_reference.py) is treated as an
immutable source here -- this script only reads it and writes into
chunks_content/ / chunks_style/ / chunks_fully_ambiguous/, so re-running it
is always a full, deterministic re-derivation, never an incremental rename.
chunks_fully_ambiguous/ holds chunks with no confident label on EITHER axis
(no signal to salvage for anything); split_mixed_content_holdout.py handles
the (content-specific) "hits both dictionaries" case separately, downstream
of chunks_content/.

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
CHUNKS_CONTENT = ROOT / "corpus_classify" / "reference_research" / "chunks_content"
CHUNKS_STYLE = ROOT / "corpus_classify" / "reference_research" / "chunks_style"
FULLY_AMBIGUOUS = ROOT / "corpus_classify" / "reference_research" / "chunks_fully_ambiguous"
MANIFEST = ROOT / "corpus_classify" / "reference_research" / "manifest.json"
REPORT = ROOT / "output" / "corpus_diagnosis_content_style_retag.json"


def parse_old_name(name: str) -> tuple[str, str] | None:
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


def _clear(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("*.txt"):
        old.unlink()


def retag(dry_run: bool = False) -> dict:
    files = sorted(CHUNKS.glob("*.txt"))
    expert_style = load_expert_style_by_slug()
    contingency = {
        "geometric__geometric": 0,
        "geometric__algebraic": 0,
        "algebraic__geometric": 0,
        "algebraic__algebraic": 0,
    }
    n_content_pool = 0
    n_style_pool = 0
    n_fully_ambiguous = 0
    skipped = []
    n_expert_style_preserved = 0
    n_ambiguous_content = 0
    n_ambiguous_style = 0

    if not dry_run:
        _clear(CHUNKS_CONTENT)
        _clear(CHUNKS_STYLE)
        _clear(FULLY_AMBIGUOUS)

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

        if content == "ambiguous":
            n_ambiguous_content += 1
        if style == "ambiguous":
            n_ambiguous_style += 1

        if content == "ambiguous" and style == "ambiguous":
            n_fully_ambiguous += 1
            if not dry_run:
                (FULLY_AMBIGUOUS / path.name).write_text(text, encoding="utf-8")
            continue

        # Contingency table only makes sense when both axes have a real
        # label -- an "ambiguous" slot isn't a third class to cross-tabulate,
        # it's the absence of a label for that axis on this chunk.
        if content != "ambiguous" and style != "ambiguous":
            contingency[f"{content}__{style}"] += 1

        # Both slots are always filled in the filename (content__style__...)
        # even when one side is "ambiguous" -- that slot is simply never read
        # by whichever axis's pool doesn't want this chunk.
        name = f"{content}__{style}__{arxiv_slug}__{chunk_suffix}"
        if content != "ambiguous":
            n_content_pool += 1
            if not dry_run:
                (CHUNKS_CONTENT / name).write_text(text, encoding="utf-8")
        if style != "ambiguous":
            n_style_pool += 1
            if not dry_run:
                (CHUNKS_STYLE / name).write_text(text, encoding="utf-8")

    total = sum(contingency.values())
    off_diagonal = contingency["geometric__algebraic"] + contingency["algebraic__geometric"]
    report = {
        "n_source_chunks": len(files),
        "n_content_pool": n_content_pool,
        "n_style_pool": n_style_pool,
        "n_fully_ambiguous": n_fully_ambiguous,
        "n_ambiguous_content": n_ambiguous_content,
        "n_ambiguous_style": n_ambiguous_style,
        "n_skipped": len(skipped),
        "skipped": skipped[:20],
        "n_expert_style_preserved": n_expert_style_preserved,
        "n_keyword_style_derived": total - n_expert_style_preserved,
        "contingency_content__style": contingency,
        "off_diagonal_fraction": round(off_diagonal / total, 4) if total else 0.0,
        "note": (
            "off_diagonal_fraction is the share of confidently-labeled-on-both-axes "
            "chunks where content and style labels disagree (e.g. algebraic content "
            "written in geometric style). 0.0 would indicate the scorers are not "
            "actually decoupled. n_content_pool/n_style_pool count chunks written to "
            "chunks_content/ and chunks_style/ respectively -- these overlap (a chunk "
            "confident on both axes is duplicated into both) but are independent: "
            "ambiguity on one axis never removes a chunk from the other axis's pool. "
            "n_fully_ambiguous chunks (no signal on either axis) go to "
            "chunks_fully_ambiguous/ instead, unusable for either."
        ),
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Score and report without writing files")
    args = ap.parse_args()

    report = retag(dry_run=args.dry_run)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nWrote {REPORT}")


if __name__ == "__main__":
    main()
