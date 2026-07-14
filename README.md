# Reasoning stylometry

Stylometric analysis of four JAMS papers on a **content × style** quadrant. **R/stylo is the engine**; Python is only a thin launcher shell.

## Run analysis

```bash
python3 scripts/run.py
# or
Rscript scripts/run_stylo_analysis.R
# or
bash scripts/run_jams_report.sh
```

Pipeline (all R except the launcher):

1. `extract_jams_pdfs.R` — PDF → text (pdftools or pdftotext)
2. `run_jams_quadrant.R` — `stylo::classify`, `rolling.classify`
3. `diagnose_corpus.R` — `stylo::crossv` LOO on training matrix
4. `export_stylo_analysis.R` — JSON export via stylo distance.table / dist.delta
5. `render_jams_reports.R` — HTML reports (cross, within, full statistical)

Reports: `~/Downloads/jams_quadrant_*.html` and `output/jams_quadrant/`.

## Requirements

- R packages: `stylo`, `stopwords`, `jsonlite`
- Optional: `pdftools` for PDF extraction
- Python 3 (launcher only for `scripts/run.py`)

## Corpus build (offline, legacy Python)

Reference corpus construction still uses Python scripts (`build_research_reference.py`, etc.). See `corpus_classify/CORPUS.md`. After building chunks, point stylo at `corpus_classify/reference_research/balanced`.

## Layout

- `R/` — paper metadata, HTML helpers, report rendering
- `scripts/*.R` — stylo pipeline
- `scripts/run.py` — invokes R only (no stylometry logic)
- `scripts/*.py` (except `run.py`) — corpus/data prep only, not the analysis engine
