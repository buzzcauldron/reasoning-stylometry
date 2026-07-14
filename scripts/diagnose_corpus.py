#!/usr/bin/env python3
"""Diagnose why a stylometry reference corpus succeeds or fails."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "corpus_classify" / "reference_set"
JAMS = ROOT / "corpus_classify" / "jams_quadrant"

SNOWBALL = """
a about above after again against all am an and any are as at be because been
before being below between both but by could did do does doing done down during
each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself me more most my myself no nor not
of off on once only or other our ours ourselves out over own same she should so
some such than that the their theirs them themselves then there these they this
those through to too under until up very was we were what when where which while
who whom why with would you your yours yourself yourselves
""".split()


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return [w for w in text.split() if w]


def load_corpus(path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"geometric": [], "algebraic": []}
    for f in sorted(path.glob("*.txt")):
        label = "geometric" if f.name.startswith("geometric") else "algebraic"
        out[label].append(f.read_text(encoding="utf-8", errors="ignore"))
    return out


def rel_stopword_freq(text: str) -> dict[str, float]:
    words = [w for w in tokenize(text) if w in SNOWBALL]
    c = Counter(words)
    total = sum(c.values()) or 1
    return {w: c[w] / total for w in SNOWBALL}


def centroid(texts: list[str]) -> dict[str, float]:
    if not texts:
        return {w: 0.0 for w in SNOWBALL}
    vecs = [rel_stopword_freq(t) for t in texts]
    return {w: sum(v[w] for v in vecs) / len(vecs) for w in SNOWBALL}


def l1_mean(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(abs(a[w] - b[w]) for w in SNOWBALL) / len(SNOWBALL)


def leave_one_out_accuracy(texts: list[str], labels: list[str]) -> tuple[int, int]:
    correct = 0
    for i, text in enumerate(texts):
        train_geo = [t for j, t in enumerate(texts) if labels[j] == "geometric" and j != i]
        train_alg = [t for j, t in enumerate(texts) if labels[j] == "algebraic" and j != i]
        if not train_geo or not train_alg:
            continue
        cg, ca = centroid(train_geo), centroid(train_alg)
        v = rel_stopword_freq(text)
        pred = "geometric" if l1_mean(v, cg) < l1_mean(v, ca) else "algebraic"
        if pred == labels[i]:
            correct += 1
    return correct, len(texts)


def word_stats(texts: list[str]) -> dict:
    counts = [len(tokenize(t)) for t in texts]
    if not counts:
        return {"n": 0, "median": 0, "min": 0, "max": 0}
    counts.sort()
    return {
        "n": len(counts),
        "median": counts[len(counts) // 2],
        "min": counts[0],
        "max": counts[-1],
        "under_200": sum(1 for c in counts if c < 200),
        "under_400": sum(1 for c in counts if c < 400),
    }


def diagnose(corpus_dir: Path, test_dir: Path | None = None) -> dict:
    files = sorted(corpus_dir.glob("*.txt"))
    texts = [f.read_text(encoding="utf-8", errors="ignore") for f in files]
    labels = ["geometric" if f.name.startswith("geometric") else "algebraic" for f in files]
    geo_texts = [t for t, l in zip(texts, labels) if l == "geometric"]
    alg_texts = [t for t, l in zip(texts, labels) if l == "algebraic"]

    cg, ca = centroid(geo_texts), centroid(alg_texts)
    class_sep = l1_mean(cg, ca)
    loo_correct, loo_total = leave_one_out_accuracy(texts, labels)

    top_diff = sorted(
        ((w, cg[w] - ca[w]) for w in SNOWBALL),
        key=lambda x: abs(x[1]),
        reverse=True,
    )[:10]

    test_preds = []
    if test_dir and test_dir.exists():
        for f in sorted(test_dir.glob("*.txt")):
            v = rel_stopword_freq(f.read_text(encoding="utf-8", errors="ignore"))
            pred = "geometric" if l1_mean(v, cg) < l1_mean(v, ca) else "algebraic"
            test_preds.append({"file": f.name, "predicted": pred})

    return {
        "corpus_dir": str(corpus_dir),
        "n_texts": len(texts),
        "n_geometric": len(geo_texts),
        "n_algebraic": len(alg_texts),
        "geo_word_stats": word_stats(geo_texts),
        "alg_word_stats": word_stats(alg_texts),
        "class_separability_l1": round(class_sep, 6),
        "leave_one_out_accuracy": f"{loo_correct}/{loo_total}",
        "leave_one_out_pct": round(100 * loo_correct / max(loo_total, 1), 1),
        "top_discriminators": [
            {"word": w, "geo_minus_alg": round(d, 5)} for w, d in top_diff
        ],
        "test_predictions_vs_centroid": test_preds,
        "verdict": _verdict(class_sep, loo_correct, loo_total, word_stats(texts)),
    }


def _verdict(sep: float, loo_c: int, loo_t: int, stats: dict) -> list[str]:
    issues = []
    if sep < 0.005:
        issues.append(
            "CRITICAL: geometric/algebraic stopword centroids nearly identical "
            f"(L1={sep:.4f}). Function words do not separate classes in this corpus."
        )
    if loo_t and loo_c / loo_t < 0.85:
        issues.append(
            f"WEAK: leave-one-out accuracy only {100*loo_c/loo_t:.0f}% on the reference set itself."
        )
    if stats.get("under_400", 0) > stats.get("n", 1) * 0.4:
        issues.append(
            f"LENGTH: {stats['under_400']}/{stats['n']} texts under 400 words — too short for stable Delta."
        )
    if stats.get("median", 0) < 500:
        issues.append(
            f"REGISTER: median length {stats['median']} words suggests expository vignettes, "
            "not research theorem-proof prose (JAMS targets ~15k+ words)."
        )
    if not issues:
        issues.append("Corpus passes basic separability and length checks.")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description="Diagnose stylometry reference corpus")
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--test", type=Path, default=JAMS)
    ap.add_argument("--json", type=Path, help="Write JSON report")
    args = ap.parse_args()

    report = diagnose(args.corpus, args.test)
    print(json.dumps(report, indent=2))

    print("\n=== VERDICT ===")
    for line in report["verdict"]:
        print(f"  • {line}")

    if args.json:
        args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nWrote {args.json}")

    if report["class_separability_l1"] < 0.005:
        sys.exit(1)


if __name__ == "__main__":
    main()
