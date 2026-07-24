#!/usr/bin/env python3
"""Build a POS-filtered function-word list for the style axis.

Rationale (2026-07-17): the sweep-winning style config (MFW-500 raw word
unigrams) was found to include real content vocabulary in its lower-ranked
words (morphisms, embedding, surjective, differential, complexes, ...) --
i.e. it was partly re-learning TOPIC, which is exactly what splitting
content/style scoring was meant to avoid. This script re-derives a function
word list from the same balanced_style/ training corpus, but keeps only
words whose most-common part of speech (per spaCy, tagged IN CONTEXT --
not via a fixed dictionary) is a closed-class function-word category:
DET, PRON, ADP, CCONJ, SCONJ, AUX, PART. NOUN/PROPN/VERB/ADJ/ADV are
excluded on principle (ADV is technically open-class and can carry content
modifiers, so it's excluded too despite some high-frequency adverbs being
discourse connectives -- a stricter cut, deliberately).

Math notation (single-character tokens, Greek letters) is ALSO excluded
for now, per explicit instruction -- these are plausible style markers
(variable-naming convention) but are being set aside as a separate
question rather than folded into this list silently.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import spacy

CORPUS_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("corpus_classify/reference_research/balanced_style")
OUT_FILE = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output/style_pos_filtered_words.txt")
TOP_N = int(sys.argv[3]) if len(sys.argv) > 3 else 500

FUNCTION_POS = {"DET", "PRON", "ADP", "CCONJ", "SCONJ", "AUX", "PART"}
GREEK = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")


def is_math_notation(token_text: str) -> bool:
    if len(token_text) == 1:
        return True
    if any(ch in GREEK for ch in token_text):
        return True
    return False


def break_long_lines(text: str, max_run: int = 300) -> str:
    """Force a sentence break at the nearest whitespace every max_run chars.

    Some chunks contain single lines of 7-8k+ characters (dense
    equation/symbol runs with no normal sentence-ending punctuation for
    spaCy's tagger to key on). Treating that as one giant "sentence" caused
    a real stall (confirmed: two independent runs both stuck at the exact
    same file, position ~4500/10000, one with the parser enabled and one
    without -- so it wasn't the parser, it was sentence length). This is a
    blunt fix -- it doesn't need to produce linguistically correct
    sentences, just bound the worst case for spaCy's per-sentence cost.
    """
    out_lines = []
    for line in text.split("\n"):
        if len(line) <= max_run:
            out_lines.append(line)
            continue
        start = 0
        pieces = []
        while start < len(line):
            end = start + max_run
            if end < len(line):
                space = line.rfind(" ", start, end)
                if space > start:
                    end = space
            pieces.append(line[start:end])
            start = end
        out_lines.append(". ".join(pieces))
    return "\n".join(out_lines)


def main() -> None:
    # "parser" is disabled too -- pos_ comes from tagger + attribute_ruler, not
    # from dependency parsing, and the parser is the single most expensive
    # component. It was left on in a first attempt and the job stalled for
    # 20+ minutes with zero throughput, almost certainly the parser choking on
    # a math-heavy chunk with no normal sentence-ending punctuation (a run of
    # symbols/equations reads as one pathologically long "sentence").
    nlp = spacy.load("en_core_web_lg", disable=["ner", "lemmatizer", "parser"])
    # Default max_length (1M chars) exists to bound parser/NER memory use;
    # both are disabled here, so it's safe to raise for the handful of
    # unusually large chunks in this corpus (confirmed: one file is
    # 1,069,588 chars).
    nlp.max_length = 3_000_000
    files = sorted(CORPUS_DIR.glob("*.txt"))
    print(f"Processing {len(files)} files from {CORPUS_DIR}", flush=True)

    word_freq: Counter[str] = Counter()
    word_pos: dict[str, Counter[str]] = {}

    # n_process: two earlier attempts on akdeniz (n_process=16) stalled dead
    # at the same position across independent runs -- eventually traced to
    # another user's unrelated Lean4/mathlib compile job pegging that
    # machine (load average 542 on a 32-core box), not a spaCy bug or a
    # pathological document. This machine's load is clean, so multiprocessing
    # is restored, sized to leave a couple cores free.
    import os
    n_process = max(1, int(os.environ.get("POS_FILTER_N_PROCESS", "1")))
    texts = (break_long_lines(f.read_text(encoding="utf-8", errors="ignore")) for f in files)
    for i, doc in enumerate(nlp.pipe(texts, batch_size=64, n_process=n_process), 1):
        for tok in doc:
            if not tok.is_alpha:
                continue
            w = tok.text.lower()
            word_freq[w] += 1
            word_pos.setdefault(w, Counter())[tok.pos_] += 1
        if i % 500 == 0:
            print(f"  {i}/{len(files)} files tagged", flush=True)

    print(f"Done tagging. {len(word_freq)} distinct alpha tokens.", flush=True)

    # Persist raw counts so the filter below can be re-tuned later without
    # repeating the ~15-20 min tagging pass.
    raw_out = OUT_FILE.parent / "style_pos_word_stats.json"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    with raw_out.open("w", encoding="utf-8") as f:
        json.dump(
            {w: {"freq": freq, "pos": dict(word_pos[w])} for w, freq in word_freq.items()},
            f,
        )
    print(f"Saved raw word/POS stats to {raw_out}", flush=True)

    qualifying = []
    for w, freq in word_freq.most_common():
        if is_math_notation(w):
            continue
        # PDF-extraction artifact filter: this corpus has known cases of two
        # words losing their whitespace around an inline math variable (e.g.
        # "ifA", "constantC" -- documented earlier this session). Those
        # garbled merges are out-of-vocabulary for spaCy's word vectors,
        # unlike genuine (even rare) English function words, so require a
        # real vector as a cheap, principled "is this an actual word" check.
        lex = nlp.vocab[w]
        if lex.is_oov or not lex.has_vector:
            continue
        pos_counts = word_pos[w]
        majority_pos = pos_counts.most_common(1)[0][0]
        if majority_pos in FUNCTION_POS:
            qualifying.append((w, freq, majority_pos))

    top = qualifying[:TOP_N]
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for w, freq, pos in top:
            f.write(w + "\n")

    print(f"Wrote {len(top)} POS-filtered function words to {OUT_FILE}")
    print("Sample (first 40):", [w for w, _, _ in top[:40]])
    print("Sample (last 20):", [w for w, _, _ in top[-20:]])


if __name__ == "__main__":
    main()
