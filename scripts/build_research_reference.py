#!/usr/bin/env python3
"""Build research-register reference corpus from arXiv PDFs (manifest-driven)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
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


# A commutative-diagram arrow (xy-pic/tikz-cd) renders as a font glyph named
# "arrowext" in some source PDFs, and pypdf extracts the literal glyph name
# instead of an arrow symbol -- e.g. "C2 /arrowext /arrowext /arrowext -> C1"
# for one drawn arrow. Confirmed via grep context (2026-07-23): 145/1368
# textbook chunks (Hatcher's Algebraic Topology, heavy on diagram chases),
# 0/22390 arXiv-sourced chunks. Repeated many times per diagram, so it
# dominates raw word-frequency/keyness rankings for whatever class happens to
# use more commutative diagrams -- purely a rendering artifact, not content.
_ARROWEXT_RE = re.compile(r"/?arrowext\b", re.IGNORECASE)

# Some source PDFs mis-encode "(" as literal "p" and ")" as literal "q"
# (a font-encoding issue distinct from the ligature/merge fixes above) --
# confirmed via context (2026-07-23): "Φ2pxq" = "Φ2(x)", "EndpDq" = "End(D)",
# "LppRdq" = "Lp(Rd)", "slnpFqq" = "sln(Fq)" i.e. sl_n(F_q) (note: only the
# OUTER q is the mis-encoded paren; the inner "Fq" is a genuine F_q subscript,
# which is why only the trailing q gets touched, not every q in the word).
# A word ending in a bare lowercase "q" is otherwise essentially unseen in
# English math prose, making this a fairly safe signal -- but not perfectly
# safe (a genuine word could coincidentally end in "q"), hence the safelist.
_PAREN_SAFELIST = {"coq", "iraq", "qatar", "cinq", "burqa"}
_WORD_ENDING_IN_Q_RE = re.compile(r"\b[A-Za-z]{2,}q\b")


def _fix_paren_encoding_word(word: str) -> str:
    if word.lower() in _PAREN_SAFELIST:
        return word
    body = word[:-1]
    # Skip position 0: a leading "p" is plausibly a real initial letter
    # (e.g. a genuine "p-adic" prefix), not a mis-rendered opening paren --
    # under-fixing here is the safer failure mode than over-fixing.
    p_pos = body.find("p", 1)
    if p_pos == -1:
        return body + ")"
    return body[:p_pos] + "(" + body[p_pos + 1:] + ")"


def fix_paren_encoding(text: str) -> str:
    return _WORD_ENDING_IN_Q_RE.sub(lambda m: _fix_paren_encoding_word(m.group(0)), text)


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    text = "\n".join(parts)
    # NFKD decomposes PDF ligatures (U+FB01 "fi", U+FB02 "fl", ...) to plain
    # ASCII letters -- without this, "finitely" survives extraction as
    # "ﬁnitely" and the alpha-only regex in tokenize() silently drops the
    # ligature, corrupting the word to "nitely".
    text = unicodedata.normalize("NFKD", text)
    # pypdf occasionally emits embedded NUL bytes (valid UTF-8, but R's
    # readLines() treats NUL as a C-string terminator and silently truncates
    # the read to nothing) -- confirmed empirically: 20/10000 balanced_content
    # chunks tokenized to 0-1 words in stylo because of this, which crashed
    # any n-gram feature config (ngram.size>1) despite looking like perfectly
    # normal text via `cat`. Strip NUL and other non-printable control chars.
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = _ARROWEXT_RE.sub(" ", text)
    text = fix_paren_encoding(text)
    # pypdf frequently drops the space between prose and an inline italic
    # math variable ("if A" -> "ifA", "constant C" -> "constantC") -- found
    # to affect 90%+ of chunks and to corrupt frequency-based word-list
    # construction (POS-filtered/keyness word lists both picked up merge
    # garbage like "seta", "tpm" at meaningful rank). A lowercase run
    # immediately followed by exactly one capital or Greek letter at a word
    # boundary is essentially never legitimate prose (verified against
    # McDonald/arXiv-style exceptions, which have more letters after the
    # capital and so aren't at a boundary there).
    text = re.sub(r"([a-z]{2,})([A-Z])\b", r"\1 \2", text)
    text = re.sub(r"([a-z]{2,})([Ͱ-Ͽἀ-῿])", r"\1 \2", text)
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s+\n\s+", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text)
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
            # A single sparse window (title page, table of contents, a
            # reference list) shouldn't stop the whole scan -- skip it and
            # keep looking at later windows.
            continue
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
        # content_topic is a placeholder here (often just `style`, or absent for
        # newer manifests); scripts/retag_content_style.py overwrites both fields
        # from the actual chunk text after this build step, so it's not load-bearing.
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
