#!/usr/bin/env python3
"""Rank ALL corpus words by keyness (log-likelihood, Dunning 1993) between
the geometric- and algebraic-labeled halves of a balanced pool, after
excluding the N most frequent words overall (generic function words /
math-genre scaffolding like "theorem", "proof", "the", "is" that appear
about equally often in both classes and drown out real discriminators by
raw frequency alone). Unlike keyness_content_words.py (recovered from
akdeniz), this has no spaCy/POS candidate-pool restriction -- it's a direct
scan of every word in the corpus, usable for either axis.

Usage: python3 scripts/keyness_scan.py <balanced_dir> <exclude_top_n> [top_n_out]
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path

CORPUS_DIR = Path(sys.argv[1])
EXCLUDE_TOP_N = int(sys.argv[2])
TOP_N_OUT = int(sys.argv[3]) if len(sys.argv) > 3 else 25
MIN_TOTAL_FREQ = 20


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def log_likelihood(a: int, b: int, total_a: int, total_b: int) -> float:
    e1 = total_a * (a + b) / (total_a + total_b)
    e2 = total_b * (a + b) / (total_a + total_b)
    ll = 0.0
    if a > 0 and e1 > 0:
        ll += 2 * a * math.log(a / e1)
    if b > 0 and e2 > 0:
        ll += 2 * b * math.log(b / e2)
    return ll


def main() -> None:
    files = sorted(CORPUS_DIR.glob("*.txt"))
    geo_counts: Counter[str] = Counter()
    alg_counts: Counter[str] = Counter()
    geo_total = 0
    alg_total = 0
    for f in files:
        cls = "geometric" if f.name.startswith("geometric") else "algebraic"
        toks = tokenize(f.read_text(encoding="utf-8", errors="ignore"))
        if cls == "geometric":
            geo_counts.update(toks)
            geo_total += len(toks)
        else:
            alg_counts.update(toks)
            alg_total += len(toks)

    overall = geo_counts + alg_counts
    ranked_by_freq = [w for w, _ in overall.most_common()]
    excluded = set(ranked_by_freq[:EXCLUDE_TOP_N])

    print(f"{CORPUS_DIR}: {len(files)} files, geo_total={geo_total} alg_total={alg_total}, "
          f"{len(overall)} distinct words, excluding top {EXCLUDE_TOP_N} by raw frequency")
    print(f"  (excluded set, rank {EXCLUDE_TOP_N-9}-{EXCLUDE_TOP_N}): "
          f"{ranked_by_freq[max(0,EXCLUDE_TOP_N-10):EXCLUDE_TOP_N]}")

    scored = []
    for w, total in overall.items():
        if w in excluded or total < MIN_TOTAL_FREQ:
            continue
        a = geo_counts.get(w, 0)
        b = alg_counts.get(w, 0)
        ll = log_likelihood(a, b, geo_total, alg_total)
        rate_a = a / geo_total
        rate_b = b / alg_total
        direction = "geometric" if rate_a > rate_b else "algebraic"
        ratio = (rate_a / rate_b) if direction == "geometric" and rate_b > 0 else (rate_b / rate_a if rate_a > 0 else float("inf"))
        scored.append((w, ll, direction, a, b, ratio))

    scored.sort(key=lambda t: -t[1])
    geo_top = [t for t in scored if t[2] == "geometric"][:TOP_N_OUT]
    alg_top = [t for t in scored if t[2] == "algebraic"][:TOP_N_OUT]

    print(f"\n-- Top {TOP_N_OUT} GEOMETRIC-leaning (by log-likelihood keyness, rank > {EXCLUDE_TOP_N}) --")
    for w, ll, d, a, b, ratio in geo_top:
        print(f"  {w:20s} LL={ll:8.1f}  geo_count={a:6d}  alg_count={b:6d}  rate_ratio={ratio:.2f}x")

    print(f"\n-- Top {TOP_N_OUT} ALGEBRAIC-leaning (by log-likelihood keyness, rank > {EXCLUDE_TOP_N}) --")
    for w, ll, d, a, b, ratio in alg_top:
        print(f"  {w:20s} LL={ll:8.1f}  geo_count={a:6d}  alg_count={b:6d}  rate_ratio={ratio:.2f}x")


if __name__ == "__main__":
    main()
