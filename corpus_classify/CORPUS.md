# Reasoning stylometry — reference corpus guide

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
python3 scripts/balance_research_corpus.py            # relabel + 50/50 subsample
```

### Contemporary scrape (`scrape_contemporary_arxiv.py`)

Queries arXiv API (2020+) across geometry/topology and algebra/logic categories, then
tags each paper with **keyword-based style scores** from the v4 rubric
(`scripts/style_keyword_tagger.py`: geodesic, mapping class, functor, model theory, etc.).

Outputs `manifest_contemporary.json`; `--merge` appends to `manifest.json` without
duplicating existing arXiv IDs.

### Label curation

Raw HTML aggregation mis-tags some topology papers as algebraic. After manual overrides
and relabeling (`scripts/balance_research_corpus.py`), use the **balanced** directory:

| Directory | Chunks | Geo / Alg | Use |
|-----------|--------|-----------|-----|
| `reference_research/chunks` | 3583 | 1440 / 2302 | Full pool; class imbalance hurts holdout |
| **`reference_research/balanced`** | **2834** | **1417 / 1417** | **Default training set** |

### Benchmark on JAMS style labels (stopwords + Delta)

**Primary metric:** rolling majority vote (250-word slices, 150 overlap). Whole-paper classify is a secondary summary on 13k–36k-word texts where register varies by section.

| Training corpus | Rolling | Whole-paper | Notes |
|-----------------|---------|-------------|-------|
| v1 CutKnot (54) | — | 3/4 | Wrong register |
| v2 mixed (297) | — | **1/4** | Elementary chunks hurt |
| v2 research 8-paper (262) | — | **3/4** | Small curated set |
| v3 all chunks (3583) | — | **2/4** | Label noise + imbalance |
| **v3 balanced (2834)** | **2/4** | **3/4** | Current default; Dritschel/Masur swap by metric |

Current rolling shares (balanced corpus): Masur 38.9% geo, Bateman 47.3%, Dritschel 35.4%, Hrushovski 41.6%. Bateman and Hrushovski hit majority; Masur and Dritschel lean algebraic despite expert geometric style.

Use **`corpus_classify/reference_research/balanced`** as the default training set for
research-paper targets.

## Tooling

```bash
# Diagnose any corpus (separability, length, LOO accuracy)
python3 scripts/diagnose_corpus.py --corpus corpus_classify/reference_research/balanced

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

Even v3 research corpus has geo/alg stopword centroids with L1 ≈ **0.001–0.002** — classes
are still barely separated in function-word space. Stylo stopwords alone cannot
reliably encode the content×style decomposition from the v4 rubric (spatial features,
object categories, etc.). For that axis, use the expert/LLM rating pipeline
(`cross_view.html` / `within_view.html`).

**Dritschel & McCullough** (algebraic content × geometric style) is consistently misclassified
as algebraic — the hardest quadrant cell for stopword-only stylo.

To improve stylo further:

1. Curate style labels from v4 rubric (not filename/topic alone)
2. Add structural features (equation density, figure refs, spatial n-grams)
3. Train on excerpt-length windows (~250 words) matched to classification unit
4. Retry failed arXiv downloads or substitute equivalent papers
