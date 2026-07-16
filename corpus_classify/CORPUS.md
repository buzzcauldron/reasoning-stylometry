# Reasoning stylometry — reference corpus guide

## v5: content and style were the same label (fixed)

Every version of this corpus through v4 had a structural bug: **content_topic was
set equal to style by construction.**

- `scripts/generate_manifest_from_views.py` (the cross_view/within_view-derived
  batch, 131 sources) literally wrote `"content_topic": style` — not measured,
  copied.
- `scripts/scrape_contemporary_arxiv.py` (the 729-source contemporary arXiv
  scrape) tagged both fields from the same keyword score (`score_text()`, now
  `score_content()`), so `content_topic == style` for 849/860 manifest sources.
- The old `scripts/style_keyword_tagger.py` "style" keywords (`geodesic`,
  `mapping class`, `functor`, `model theory`, `cap set`...) are subject-matter
  nouns — a **topic** signal, not a measurement of *how* an argument is
  presented. Calling that score "style" was the root of the conflation.

The practical effect: the reference corpus only ever populated the
geometric-content/geometric-style and algebraic-content/algebraic-style
diagonal. Training a classifier on it and calling the result "style" actually
trained (and validated) a **topic classifier**, which is exactly why it agreed
with expert style ratings on the two JAMS papers where content and style
happen to match (Masur, Hrushovski) and disagreed on the two papers where
they're deliberately decoupled (Bateman: geometric content/algebraic style;
Dritschel: algebraic content/geometric style) — see "What still does not work"
below, written before this fix, describing exactly that failure mode.

**The fix:**

1. `scripts/style_keyword_tagger.py` now has two disjoint scorers:
   `score_content()` (unchanged subject-noun vocabulary + arXiv category lean —
   a legitimate topic signal) and a new `score_style()` (rhetorical/discourse
   markers — "visualize", "in a neighborhood of", "substituting", "plugging
   in" — plus a figure/diagram-reference vs. numbered-equation-reference
   density signal). Both are deliberately subject-agnostic on the style side:
   no subfield nouns appear in the style marker lists.
2. `scripts/retag_content_style.py` re-scores every chunk's *own full text*
   (not the abstract, not the arXiv category) with both scorers independently
   and renames it `{content}__{style}__{arxiv_slug}__chunkNNN.txt`. Where a
   chunk's source paper was one of the 131 with a real expert/LLM style_axis
   rating (from cross_view.html/within_view.html aggregation, not a keyword
   guess), that expert rating is preserved for `style` instead of being
   overwritten by the keyword score.
3. `scripts/balance_research_corpus.py` builds two independently-balanced
   training sets — `reference_research/balanced_content/` and
   `reference_research/balanced_style/` — because `stylo::classify()` always
   takes the ground-truth class from the filename segment before the first
   underscore, so each axis needs its own leading-field naming order.
4. `scripts/run_jams_quadrant.R` trains and reports two independent
   classifiers (content, style) plus a joint quadrant confusion matrix, instead
   of one classifier whose output was mislabeled.
5. `scripts/diagnose_corpus.R` adds a content/style **independence check**
   (contingency table + chi-squared/Cramer's V on the retagged corpus) so a
   future regression back to "content == style" would be caught, not silently
   re-introduced.

Run `python3 scripts/retag_content_style.py` to see the current contingency
table between content and style labels in `output/corpus_diagnosis_content_style_retag.json`,
and `Rscript scripts/diagnose_corpus.R` for the statistical independence check
in `output/corpus_diagnosis_stylo.json`.

**Results after the fix** (`output/jams_quadrant/stylo_results.json` and
`output/corpus_diagnosis_stylo.json`, 1500 chunks/class per axis,
stopwords175 + Delta):

| Check | Result |
|-------|--------|
| Content x style independence | 43.1% off-diagonal (was ~0% pre-fix); Cramer's V = 0.06 — decoupled, low residual association |
| Content: whole-paper accuracy | 1/4 |
| Content: rolling majority | 2/4 (all 4 papers land 58-60% algebraic-share — no real per-paper discrimination, just a uniform bias) |
| Content: crossv LOO (in-domain) | 53% — near chance |
| Style: whole-paper accuracy | 3/4 (genuinely varies per paper — a real signal, not a constant guess) |
| Style: rolling majority | 2/4 (all 4 papers land algebraic-leaning, same uniform-bias pattern as content) |
| Style: crossv LOO (in-domain) | 57% — weak |
| Joint quadrant (both axes correct, whole-paper) | 0/4 |

Read this alongside "What still does not work" below, which predates the fix
but remains largely accurate: stopword-Delta classification on JAMS-length
research text is a weak signal overall for both axes, not just style. The
fix's job was to make the two axes genuinely independent (done — see the
43.1%/Cramer's V row) and to stop mislabeling a topic classifier as a style
classifier; it does not by itself make stopword-Delta classification strong.
The rolling metric's uniform algebraic bias across all 4 papers on both axes
is the same "JAMS papers collapse to 'algebraic' in stopword space" pattern
documented below, now visible on two axes instead of hidden behind one
mislabeled one. The one clearly encouraging result is **style whole-paper
accuracy (3/4) genuinely varying by paper** rather than defaulting to a
constant guess — some real signal survives at the whole-document level even
though it disappears under the rolling/LOO metrics.

This keyword-based style signal is still a heuristic, not ground truth —
style is inherently harder to measure from text alone than content, and short
marker-phrase lists are sparse (see "What still does not work" below).

## Why v1 (`reference_set`) fails

The original 54-text Cut-the-Knot / Wikipedia corpus was designed as subject-matched
**elementary proof pairs** (same theorem, geometric vs algebraic presentation). That is
the right *labeling* idea, but four structural problems make stylo classification on
JAMS papers unreliable:

| Problem | v1 evidence |
|---------|-------------|
| **Register mismatch** | Median ~193 words, chatty expository prose vs JAMS ~15k-word formal research |
| **Too short** | 49/54 texts under 400 words — unstable Burrows Delta estimates |
| **No stopword signal** | Geo/alg centroid L1 separation ≈ **0.002**; max single-word diff ≈ 0.01 on "the" |
| **In-domain weak** | Leave-one-out on v1 itself only ~65% |

Function words encode **genre and formality** (expository vs research), not the
spatial-vs-symbolic **reasoning style** axis you care about. All four JAMS papers share
research-math register, so they collapse to "algebraic" in stopword space regardless
of expert style ratings.

## v3 research corpus (`reference_research/`)

Built by `scripts/build_research_reference.py` from arXiv PDFs listed in
`corpus_classify/reference_research/manifest.json` (generated via
`scripts/generate_manifest_from_views.py` from cross_view/within_view ratings,
plus a geometric topology boost list):

- **400+ word chunks**, ~1200-word target, sliding windows
- **131 arXiv sources** → **3583 chunks** (v3 base, before contemporary scrape)
- **+491 contemporary sources (2020–2026)** via keyword tagging → **622 total** in manifest v4.0
- Excludes the four JAMS test papers
- **5 PDFs failed to download** (network): `math/0305583`, `math/0507693`, `math/0508888`, `math/0711.0803`, `math/0804.3021`

Regenerate:

```bash
python3 scripts/generate_manifest_from_views.py
python3 scripts/scrape_contemporary_arxiv.py --year-from 2020 --per-query 35 --merge
python3 scripts/build_research_reference.py --clean   # full rebuild
python3 scripts/build_research_reference.py --resume  # add new manifest entries only
python3 scripts/retag_content_style.py                # independent content + style labels from chunk text
python3 scripts/balance_research_corpus.py            # 50/50 subsample, per axis
```

### Contemporary scrape (`scrape_contemporary_arxiv.py`)

Queries arXiv API (2020+) across geometry/topology and algebra/logic categories, then
tags each paper with **keyword-based style scores** from the v4 rubric
(`scripts/style_keyword_tagger.py`: geodesic, mapping class, functor, model theory, etc.).

Outputs `manifest_contemporary.json`; `--merge` appends to `manifest.json` without
duplicating existing arXiv IDs.

### Label curation

Content and style are now tagged independently per chunk by
`scripts/retag_content_style.py` (see the v5 section above). Use the two
axis-specific balanced directories:

| Directory | Chunks | Geo / Alg | Use |
|-----------|--------|-----------|-----|
| `reference_research/chunks` | 19058 | see `output/corpus_diagnosis_content_style_retag.json` for the full content×style contingency table | Full pool; class imbalance hurts holdout |
| **`reference_research/balanced_content`** | **3000** | **1500 / 1500** | **Default training set for the content classifier** |
| **`reference_research/balanced_style`** | **3000** | **1500 / 1500** | **Default training set for the style classifier** |

Both are capped at 1500/class (`MAX_PER_CLASS` in `balance_research_corpus.py`)
even though far more chunks are available (up to 7594/class for content,
5684/class for style) — `stylo::classify()`/`rolling.classify()` re-tokenize
the whole training directory from scratch on every call, and with 4 JAMS
papers x 2 axes that's 8+ reloads per pipeline run. Running that against the
uncapped pool OOM-killed the machine; 1500/class (a similar scale to the
proven pre-v5 ~2834-chunk corpus) keeps each `run_jams_quadrant.R` run to
under 2 minutes.

### Benchmark on JAMS style labels (stopwords + Delta)

**Primary metric:** rolling majority vote (250-word slices, 150 overlap). Whole-paper classify is a secondary summary on 13k–36k-word texts where register varies by section.

| Training corpus | Rolling | Whole-paper | Notes |
|-----------------|---------|-------------|-------|
| v1 CutKnot (54) | — | 3/4 | Wrong register |
| v2 mixed (297) | — | **1/4** | Elementary chunks hurt |
| v2 research 8-paper (262) | — | **3/4** | Small curated set |
| v3 all chunks (3583) | — | **2/4** | Label noise + imbalance |
| **v3 balanced (2834)** | **2/4** | **3/4** | Current default; Dritschel/Masur swap by metric |

Current rolling shares (v3 balanced corpus, pre-v5): Masur 38.9% geo, Bateman 47.3%, Dritschel 35.4%, Hrushovski 41.6%. Bateman and Hrushovski hit majority; Masur and Dritschel lean algebraic despite expert geometric style.

The table above predates the v5 content/style fix, where "style" was actually a
mislabeled topic signal (see the v5 section at the top of this file). Post-fix
content and style accuracy against expert v4 labels are in
`output/jams_quadrant/stylo_results.json` (`content_accuracy`, `style_accuracy`,
`quadrant_accuracy`) and reproduced in the master comparison table of
`jams_quadrant_full_report.html`.

Use **`corpus_classify/reference_research/balanced_content`** and
**`corpus_classify/reference_research/balanced_style`** as the default training
sets for research-paper targets (content and style classifiers respectively).

## Tooling

```bash
# scripts/diagnose_corpus.py is DEPRECATED (Python stopword-only prototype,
# single-axis, predates the content/style split) -- use `Rscript
# scripts/diagnose_corpus.R` after run_jams_quadrant.R instead; it reports
# both axes plus the content/style independence check.

# Build research chunks from manifest (curl + PDF extract)
python3 scripts/build_research_reference.py

# Relabel mis-tagged chunks and build balanced 50/50 set
python3 scripts/balance_research_corpus.py

# Assemble research-only v2 (default: no elementary)
python3 scripts/assemble_reference_v2.py

# Compare v1 vs v3 on JAMS holdout
Rscript scripts/benchmark_corpora.R
```

## What still does not work

Stopword-Delta classification is weak on both axes against this 4-paper JAMS
holdout (see the results table in the v5 section: content whole-paper 1/4,
style whole-paper 3/4; both axes' rolling majority and in-domain crossv LOO
hover near chance, 53-57%). Going in, the expectation was that content
(topic vocabulary correlating with function-word usage) would separate more
reliably than the subtler, sparser style signal — the opposite happened on
whole-paper accuracy, though rolling and LOO are weak for both. Read the
per-axis numbers before assuming either one is reliable; current figures are
in `output/jams_quadrant/stylo_results.json` and `output/corpus_diagnosis_stylo.json`.

**Dritschel & McCullough** (algebraic content × geometric style) remains the
hardest quadrant cell: its argument is symbol- and equation-dense (no figures,
high numbered-equation-reference density) even though expert raters coded its
*style* as geometric based on structural/conceptual moves (convex cones,
separating hyperplanes) that a text-frequency signal doesn't capture. This was
true before the v5 fix and remains true after — it isn't evidence the fix
didn't work, it's evidence that this specific paper's style is not recoverable
from surface text statistics alone.

Completed since the last version of this section:

1. ~~Curate style labels from v4 rubric (not filename/topic alone)~~ — done for
   the 131 chunks with real cross_view/within_view expert ratings; the rest use
   the new topic-independent rhetorical-marker scorer (`score_style()`).
2. ~~Add structural features (equation density, figure refs, spatial n-grams)~~
   — done (`_structural_density` in `style_keyword_tagger.py`: figure/diagram
   references vs. numbered-equation references per 1000 words).

Still open:

3. Train on excerpt-length windows (~250 words) matched to classification unit
4. Retry failed arXiv downloads or substitute equivalent papers
5. The rhetorical-marker phrase lists in `style_keyword_tagger.py` are a
   first-pass heuristic, hand-checked only against the 4 JAMS papers (to avoid
   overfitting them to that held-out set). A larger held-out validation set
   with independent human style ratings would be needed to properly tune or
   trust these markers beyond a sanity check.
