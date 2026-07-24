#!/usr/bin/env python3
"""Extract plain text from downloaded JAMS PDFs for stylo corpus."""

import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_research_reference import _ARROWEXT_RE, fix_paren_encoding  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus_classify" / "jams_quadrant"

PDFS = {
    "geometric__geometric_style__masur_schleimer_disk_complex": "/tmp/masur_disk.pdf",
    "geometric__algebraic_style__bateman_katz_cap_sets": "/tmp/bateman_cap.pdf",
    "algebraic__geometric_style__dritschel_mccullough_rational_dilation": "/tmp/dritschel.pdf",
    "algebraic__algebraic_style__hrushovski_approx_subgroups": "/tmp/hrushovski.pdf",
}


def clean(text: str) -> str:
    # Same fixes as build_research_reference.py's extract_text(): NFKD for
    # PDF ligatures, strip control chars (NUL truncates R's readLines()),
    # strip commutative-diagram-arrow glyph names, fix mis-encoded parens,
    # and split prose merged with an inline italic math variable ("ifA" ->
    # "if A") -- see that function's comments for the full rationale.
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or ord(ch) >= 32)
    text = _ARROWEXT_RE.sub(" ", text)
    text = fix_paren_encoding(text)
    text = re.sub(r"([a-z]{2,})([A-Z])\b", r"\1 \2", text)
    text = re.sub(r"([a-z]{2,})([Ͱ-Ͽἀ-῿])", r"\1 \2", text)

    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isdigit() and len(line) <= 4:
            continue
        lines.append(line)
    return "\n\n".join(lines)


def extract(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    chunks = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            chunks.append(t)
    return clean("\n".join(chunks))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, pdf in PDFS.items():
        text = extract(pdf)
        out = OUT / f"{stem}.txt"
        out.write_text(text, encoding="utf-8")
        print(f"{stem}: {len(text.split()):,} words -> {out}")


if __name__ == "__main__":
    main()
