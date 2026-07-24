# Reasoning stylometry

Stylometric analysis of four JAMS papers on a **content × style** quadrant. **R/stylo is the engine**; Python is only a thin launcher shell / corpus-prep step.

Content (subject topic: geometric vs algebraic) and style (reasoning presentation:
spatial/visual vs symbolic/derivational) are trained and predicted as **two
independent classifiers**. They used to be the same label by construction — see
`corpus_classify/CORPUS.md` for that history and `output/corpus_diagnosis_stylo.json`
for the independence check this fix introduced.

## Run analysis

```bash
python3 scripts/retag_content_style.py         # tag chunks/ into INDEPENDENT chunks_content/ + chunks_style/ pools
python3 scripts/split_mixed_content_holdout.py # hold out content-ambiguous chunks from chunks_content/ ONLY
python3 scripts/balance_research_corpus.py     # build balanced_content/ and balanced_style/
Rscript scripts/make_style_leading_targets.R   # style-first copies of the 4 JAMS test papers
Rscript scripts/run_jams_quadrant.R            # stylo::classify / rolling.classify, both axes
Rscript scripts/diagnose_corpus.R              # stylo::crossv LOO + content/style independence check
Rscript scripts/export_stylo_analysis.R        # JSON export via stylo distance.table / dist.delta
Rscript scripts/render_jams_reports.R          # HTML reports (cross, within, full statistical)
```

The first three steps only need re-running after a corpus/keyword-vocabulary
change; day-to-day iteration is usually just the last four (`run_jams_quadrant.R`
onward).

Reports: `~/Downloads/jams_quadrant_*.html` and `output/jams_quadrant/`.

## Current results

(2026-07-23, after fully re-extracting the reference corpus with consistent
PDF-cleaning, fixing a content/style tagger bug that silently defaulted
zero-signal chunks to "algebraic," and splitting `chunks_content/`/
`chunks_style/` into independent pools -- see git history for the full
investigation.) Content and style remain independent by construction (45.3%
off-diagonal in the content×style contingency table among chunks confidently
labeled on both axes — see `output/corpus_diagnosis_content_style_retag.json`).
Stopword-Delta classification against the 4-paper JAMS holdout: content
whole-paper 3/4, style whole-paper 2/4 (joint quadrant, both axes correct:
1/4); rolling majority and in-domain LOO still hover near chance on both
axes. The style training pool is now 94.9% keyword-verified (previously as
low as 22% when content and style shared one ambiguity-gated pool). See
`corpus_classify/CORPUS.md`'s "v5" section for the pre-2026-07-23 baseline
this improves on and what these numbers do and don't mean.

## Requirements

- R packages: `stylo`, `stopwords`, `jsonlite`
- Optional: `pdftools` for PDF extraction
- Python 3 (corpus prep + tagging; no stylometry logic)

## Corpus build (offline, Python)

Reference corpus construction and content/style tagging use Python scripts
(`build_research_reference.py`, `retag_content_style.py`, `split_mixed_content_holdout.py`,
`balance_research_corpus.py`). See `corpus_classify/CORPUS.md`. After building, point
stylo at `corpus_classify/reference_research/balanced_content` (content classifier) and
`corpus_classify/reference_research/balanced_style` (style classifier).

`chunks/` (raw output of `build_research_reference.py`) is an immutable source —
`retag_content_style.py` only reads it, writing into two INDEPENDENT pools:
`chunks_content/` and `chunks_style/`. A chunk confident on both axes is
duplicated into both; a chunk ambiguous (tied/no signal) on one axis is simply
absent from that axis's pool without affecting the other. This matters because
`split_mixed_content_holdout.py`'s "hits both keyword dictionaries" filter is
inherently content-specific — it only ever removes chunks from `chunks_content/`,
never `chunks_style/`. Before this split (pre-2026-07-23), the two axes shared one
pool gated by a single ambiguous-on-EITHER-axis check, which meant content-only
ambiguity silently starved the style classifier's training pool too.

## Layout

- `R/` — paper metadata, HTML helpers, report rendering
- `scripts/*.R` — stylo pipeline (dual content/style classifiers)
- `scripts/run.py` — invokes R only (no stylometry logic)
- `scripts/style_keyword_tagger.py` — independent content (topic) and style (rhetorical marker) scorers
- `scripts/retag_content_style.py` — tags `chunks/` into independent `chunks_content/`/`chunks_style/` pools
- `scripts/split_mixed_content_holdout.py` — holds out content-ambiguous chunks from `chunks_content/` only
- `scripts/classify_mixed_content.R` + `scripts/merge_pseudo_labels.py` — pseudo-label the keyword-ambiguous
  holdout with the current best classifier and fold predictions into `chunks_pseudo_labeled/`; empirically
  regressed accuracy in this session's one trial (uniform-collapse bias), so not part of the default pipeline
- `scripts/build_pos_filtered_style_words.py` + `scripts/tighten_pos_filtered.py` — derive
  `corpus_classify/style_function_words.txt` (the style classifier's feature list) via spaCy POS-tagging
- `scripts/*.py` (except `run.py`) — corpus/data prep and tagging, not the analysis engine
