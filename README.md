# Reasoning stylometry

Stylometric analysis of four JAMS papers on a **content × style** quadrant. **R/stylo is the engine**; Python is only a thin launcher shell / corpus-prep step.

Content (subject topic: geometric vs algebraic) and style (reasoning presentation:
spatial/visual vs symbolic/derivational) are trained and predicted as **two
independent classifiers**. They used to be the same label by construction — see
`corpus_classify/CORPUS.md` for that history and `output/corpus_diagnosis_stylo.json`
for the independence check this fix introduced.

## Run analysis

```bash
python3 scripts/retag_content_style.py       # (re)tag reference chunks: content + style, independently
python3 scripts/balance_research_corpus.py   # build balanced_content/ and balanced_style/
Rscript scripts/make_style_leading_targets.R # style-first copies of the 4 JAMS test papers
Rscript scripts/run_jams_quadrant.R          # stylo::classify / rolling.classify, both axes
Rscript scripts/diagnose_corpus.R            # stylo::crossv LOO + content/style independence check
Rscript scripts/export_stylo_analysis.R      # JSON export via stylo distance.table / dist.delta
Rscript scripts/render_jams_reports.R        # HTML reports (cross, within, full statistical)
```

The first three steps only need re-running after a corpus/keyword-vocabulary
change; day-to-day iteration is usually just the last four (`run_jams_quadrant.R`
onward).

Reports: `~/Downloads/jams_quadrant_*.html` and `output/jams_quadrant/`.

## Current results

Content and style are now genuinely decoupled in training data (43.1%
off-diagonal in the content×style contingency table, Cramer's V = 0.06 — see
`output/corpus_diagnosis_stylo.json`). Stopword-Delta classification itself
remains weak against the 4-paper JAMS holdout on both axes (content
whole-paper 1/4, style whole-paper 3/4; both axes' rolling majority and
in-domain LOO hover near chance). See `corpus_classify/CORPUS.md`'s "v5"
section for the full breakdown and what that does and doesn't mean.

## Requirements

- R packages: `stylo`, `stopwords`, `jsonlite`
- Optional: `pdftools` for PDF extraction
- Python 3 (corpus prep + tagging; no stylometry logic)

## Corpus build (offline, Python)

Reference corpus construction and content/style tagging use Python scripts
(`build_research_reference.py`, `retag_content_style.py`, `balance_research_corpus.py`).
See `corpus_classify/CORPUS.md`. After building and retagging chunks, point stylo
at `corpus_classify/reference_research/balanced_content` (content classifier) and
`corpus_classify/reference_research/balanced_style` (style classifier).

## Layout

- `R/` — paper metadata, HTML helpers, report rendering
- `scripts/*.R` — stylo pipeline (dual content/style classifiers)
- `scripts/run.py` — invokes R only (no stylometry logic)
- `scripts/style_keyword_tagger.py` — independent content (topic) and style (rhetorical marker) scorers
- `scripts/retag_content_style.py` — re-tags reference chunks from their own text using the two scorers above
- `scripts/*.py` (except `run.py`) — corpus/data prep and tagging, not the analysis engine
