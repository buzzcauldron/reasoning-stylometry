#!/usr/bin/env python3
"""Extract plain text from downloaded JAMS PDFs for stylo corpus."""

from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus_classify" / "jams_quadrant"

PDFS = {
    "geometric__geometric_style__masur_schleimer_disk_complex": "/tmp/masur_disk.pdf",
    "geometric__algebraic_style__bateman_katz_cap_sets": "/tmp/bateman_cap.pdf",
    "algebraic__geometric_style__dritschel_mccullough_rational_dilation": "/tmp/dritschel.pdf",
    "algebraic__algebraic_style__hrushovski_approx_subgroups": "/tmp/hrushovski.pdf",
}


def clean(text: str) -> str:
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
