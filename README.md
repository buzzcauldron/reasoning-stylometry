# Reasoning stylometry

Stylometric analysis of four JAMS papers on a **content × style** quadrant (geometric vs algebraic reasoning register). Expert v4 rubric ratings are compared against [stylo](https://github.com/computationalstylistics/stylo) Burrows-Delta stopword classification on full PDF text.

## Test papers

| Paper | Content | Expert style |
|-------|---------|--------------|
| Masur & Schleimer | geometric | geometric |
| Bateman & Katz | geometric | algebraic |
| Dritschel & McCullough | algebraic | geometric |
| Hrushovski | algebraic | algebraic |

## Quick start

Requires R with **stylo**, Python 3, and `curl`.

```bash
# Build reference corpus (see corpus_classify/CORPUS.md)
python3 scripts/scrape_contemporary_arxiv.py --target-per-style 430 --merge
python3 scripts/build_research_reference.py --resume
python3 scripts/balance_research_corpus.py

# End-to-end JAMS classification + HTML reports
./scripts/run_jams_report.sh
Rscript scripts/export_stylo_analysis.R
python3 scripts/render_jams_full_report.py
```

Reports land in `output/jams_quadrant/` and `~/Downloads/jams_quadrant_full_report.html`.

## Layout

- `scripts/` — pipeline, corpus build, benchmarks, HTML renderers
- `corpus_classify/jams_quadrant/` — full extracted JAMS test texts
- `corpus_classify/reference_research/manifest.json` — arXiv source list (860 papers, balanced geo/alg)
- `corpus_classify/CORPUS.md` — corpus design and failure-mode notes
- `output/jams_quadrant/` — stylo results, rolling plots, HTML reports

Training chunks (`reference_research/chunks/`, `balanced/`) are not in git — regenerate with the build scripts above (~18k chunks).

## Key findings

Stopword centroids on the research corpus are nearly indistinguishable (L1 ≈ 0.005; sampled LOO ≈ 53%). Rolling-window attribution on JAMS papers yields weak margins and 2/4 agreement with expert style labels at majority vote; high-confidence slice subsets are sparse. See the full statistical report for Wilson CIs, binomial tests, and corpus health diagnostics.
