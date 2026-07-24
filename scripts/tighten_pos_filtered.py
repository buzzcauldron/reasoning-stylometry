#!/usr/bin/env python3
"""Tighten the POS-filtered style word list: require membership in a curated
reference stopword lexicon (spaCy's own Defaults.stop_words, 326 entries) in
addition to the existing corpus-derived POS/vector filters. This is what
actually eliminates the residual noise found on inspection (typos like
"betwen"/"untill", fragments like "thel"/"fo"/"und", abbreviations like "tcp")
-- none of those are in any curated function-word lexicon, so this is a much
harder filter than frequency or vector-existence alone. Ranking (which of the
qualifying words to prefer) still comes from actual corpus frequency, not
from the lexicon itself, so ordering/inclusion still reflects this corpus.
"""
import json
import sys

import spacy

GREEK = set("αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")


def is_math_notation(w):
    if len(w) == 1:
        return True
    if any(ch in GREEK for ch in w):
        return True
    return False


def main():
    stats_path = sys.argv[1] if len(sys.argv) > 1 else "style_pos_word_stats.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "style_pos_filtered_words_tight.txt"

    nlp = spacy.load("en_core_web_lg", disable=["ner", "lemmatizer", "parser"])
    stopword_lexicon = nlp.Defaults.stop_words
    print(f"Reference lexicon: {len(stopword_lexicon)} words")

    with open(stats_path, encoding="utf-8") as f:
        stats = json.load(f)

    FUNCTION_POS = {"DET", "PRON", "ADP", "CCONJ", "SCONJ", "AUX", "PART"}

    candidates = []
    for w, d in stats.items():
        if is_math_notation(w):
            continue
        if w not in stopword_lexicon:
            continue
        pos_counts = d["pos"]
        majority_pos = max(pos_counts, key=pos_counts.get)
        if majority_pos not in FUNCTION_POS:
            continue
        candidates.append((w, d["freq"], majority_pos))

    candidates.sort(key=lambda t: -t[1])
    print(f"Qualifying (POS-filtered AND in reference lexicon): {len(candidates)}")

    with open(out_path, "w", encoding="utf-8") as f:
        for w, freq, pos in candidates:
            f.write(w + "\n")

    print("Full list, ranked by corpus frequency:")
    for w, freq, pos in candidates:
        print(f"  {w:20s} freq={freq:6d}  pos={pos}")


if __name__ == "__main__":
    main()
