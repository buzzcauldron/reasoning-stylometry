#!/usr/bin/env python3
"""Build research-register reference corpus from arXiv PDFs (manifest-driven)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus_classify" / "reference_research" / "manifest.json"
OUT_DIR = ROOT / "corpus_classify" / "reference_research" / "chunks"
CACHE = ROOT / "output" / "pdf_cache"


def arxiv_id_to_pdf_url(arxiv_id: str) -> str:
    aid = arxiv_id.strip()
    if aid.startswith("http"):
        return aid
    return f"https://arxiv.org/pdf/{aid}.pdf"


def download_pdf(arxiv_id: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", arxiv_id)
    dest = CACHE / f"{safe}.pdf"
    if dest.exists() and dest.stat().st_size > 10_000:
        return dest
    url = arxiv_id_to_pdf_url(arxiv_id)
    subprocess.run(
        ["curl", "-fsSL", "-o", str(dest), url],
        check=True,
        capture_output=True,
    )
    return dest


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    text = "\n".join(parts)
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s+\n\s+", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return [w for w in text.split() if w]


def chunk_text(text: str, min_words: int, target_words: int) -> list[str]:
    words = tokenize(text)
    if len(words) < min_words:
        return []

    chunks: list[str] = []
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    buf: list[str] = []
    buf_words = 0

    def flush_buf() -> None:
        nonlocal buf, buf_words
        if buf_words >= min_words:
            chunks.append("\n\n".join(buf))
        buf = []
        buf_words = 0

    for para in paras:
        low = para.lower()
        if (
            any(
                x in low
                for x in (
                    "arxiv:",
                    "submitted to",
                    "preprint",
                    "acknowledgment",
                    "acknowledgement",
                )
            )
            and len(tokenize(para)) < 80
        ):
            continue
        nw = len(tokenize(para))
        if buf_words + nw > target_words * 1.3 and buf_words >= min_words:
            flush_buf()
        buf.append(para)
        buf_words += nw
        if buf_words >= target_words:
            flush_buf()
    flush_buf()

    step = target_words // 2
    raw = text.split()
    for i in range(0, max(len(raw) - min_words, 1), step):
        seg_words = raw[i : i + target_words]
        if len(tokenize(" ".join(seg_words))) < min_words:
            break
        chunk = " ".join(seg_words)
        if not any(tokenize(chunk)[:50] == tokenize(c)[:50] for c in chunks):
            chunks.append(chunk)

    return chunks


def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s.lower()).strip("_")
    return s[:48]


def existing_chunks_for(arxiv: str, style: str) -> list[Path]:
    pat = f"{style}__*__{slug(arxiv)}__chunk*.txt"
    return sorted(OUT_DIR.glob(pat))


def build(clean: bool = True, resume: bool = False) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    min_words = manifest.get("min_words_per_chunk", 400)
    target = manifest.get("chunk_target_words", 1200)
    exclude = set(manifest.get("exclude_test_papers", []))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if clean and not resume:
        for old in OUT_DIR.glob("*.txt"):
            old.unlink()

    stats = {"sources": [], "chunks_written": 0, "errors": [], "skipped_resume": 0}
    total = len(manifest["sources"])

    for idx, src in enumerate(manifest["sources"], 1):
        arxiv = src["arxiv"]
        if any(ex in arxiv for ex in exclude):
            stats["errors"].append(f"skipped excluded {arxiv}")
            continue
        style = src["style"]
        topic = src.get("content_topic", style)

        if resume:
            existing = existing_chunks_for(arxiv, style)
            if existing:
                stats["skipped_resume"] += 1
                stats["chunks_written"] += len(existing)
                continue

        print(f"\n[{idx}/{total}] [{style}] {arxiv}", flush=True)
        try:
            pdf = download_pdf(arxiv)
            text = extract_text(pdf)
            chunks = chunk_text(text, min_words, target)
            print(f"  {len(tokenize(text)):,} words -> {len(chunks)} chunks", flush=True)
            for i, chunk in enumerate(chunks, 1):
                name = f"{style}__{topic}__{slug(arxiv)}__chunk{i:03d}.txt"
                (OUT_DIR / name).write_text(chunk, encoding="utf-8")
                stats["chunks_written"] += 1
            stats["sources"].append(
                {
                    "arxiv": arxiv,
                    "style": style,
                    "chunks": len(chunks),
                    "words": len(tokenize(text)),
                }
            )
        except subprocess.CalledProcessError as e:
            stats["errors"].append(f"{arxiv}: download failed")
            print(f"  ERROR download: {e}", flush=True)
        except Exception as e:
            stats["errors"].append(f"{arxiv}: {e}")
            print(f"  ERROR: {e}", flush=True)

    summary_path = OUT_DIR.parent / "build_stats.json"
    summary_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    geo = len(list(OUT_DIR.glob("geometric__*.txt")))
    alg = len(list(OUT_DIR.glob("algebraic__*.txt")))
    print(f"\nDone: {stats['chunks_written']} chunks ({geo} geometric, {alg} algebraic)")
    print(f"Errors: {len(stats['errors'])} | Resume skipped: {stats['skipped_resume']}")
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true", help="Skip arxiv ids with existing chunks")
    ap.add_argument("--clean", action="store_true", help="Delete existing chunks before build")
    args = ap.parse_args()
    build(clean=args.clean or not args.resume, resume=args.resume)


if __name__ == "__main__":
    main()
