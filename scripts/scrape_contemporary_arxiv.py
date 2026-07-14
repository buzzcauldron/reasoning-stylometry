#!/usr/bin/env python3
"""Scrape contemporary arXiv papers and tag geometric vs algebraic style via keywords."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from style_keyword_tagger import score_text  # noqa: E402

MANIFEST = ROOT / "corpus_classify" / "reference_research" / "manifest.json"
CONTEMP = ROOT / "corpus_classify" / "reference_research" / "manifest_contemporary.json"
SCRAPE_LOG = ROOT / "output" / "contemporary_scrape.json"

ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"

EXCLUDE = {
    "1010.3174",
    "0909.2190",
    "math/0310398",
    "1107.3666",
    "1809.03427",
}

# Queries tuned for contemporary research register + style-leaning subfields
SEARCH_QUERIES: list[tuple[str, str]] = [
    # geometric-style contemporary
    ("geometric", "cat:math.GT AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "cat:math.DG AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "cat:math.AT AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "cat:math.MG AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "cat:math.SG AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", 'all:"mapping class" AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", "all:hyperbolic AND all:manifold AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", 'all:"cube complex" AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", "all:foliation AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", 'all:"geometric group" AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", 'all:"3-manifold" AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", "all:knot AND cat:math.GT AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "all:symplectic AND all:manifold AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", 'all:"gauge theory" AND all:manifold AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", 'all:"coarse geometry" AND submittedDate:[{date_from} TO {date_to}]'),
    ("geometric", "all:teichmuller AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "all:curvature AND all:manifold AND submittedDate:[{date_from} TO {date_to}]"),
    ("geometric", "all:floer AND submittedDate:[{date_from} TO {date_to}]"),
    # algebraic-style contemporary
    ("algebraic", "cat:math.RA AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.CT AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.LO AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.RT AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.AC AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.OA AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "cat:math.CO AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "all:homomorphism AND all:category AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", 'all:"model theory" AND submittedDate:[{date_from} TO {date_to}]'),
    ("algebraic", 'all:"additive combinatorics" AND submittedDate:[{date_from} TO {date_to}]'),
    ("algebraic", 'all:"finite field" AND submittedDate:[{date_from} TO {date_to}]'),
    ("algebraic", 'all:"hopf algebra" AND submittedDate:[{date_from} TO {date_to}]'),
    ("algebraic", "all:representation AND all:finite AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", 'all:"derived category" AND submittedDate:[{date_from} TO {date_to}]'),
    ("algebraic", "all:combinatorics AND all:proof AND submittedDate:[{date_from} TO {date_to}]"),
    ("algebraic", "all:galois AND submittedDate:[{date_from} TO {date_to}]"),
]


def canonical_arxiv_id(aid: str) -> str:
    return re.sub(r"v\d+$", "", aid)


def manifest_style_counts() -> tuple[int, int]:
    if not MANIFEST.exists():
        return 0, 0
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    geo = sum(1 for s in data.get("sources", []) if s["style"] == "geometric")
    alg = sum(1 for s in data.get("sources", []) if s["style"] == "algebraic")
    return geo, alg


def style_at_target(style: str, base_geo: int, base_alg: int, collected: dict, target: int | None) -> bool:
    if target is None:
        return False
    geo = base_geo + sum(1 for p in collected.values() if p["style"] == "geometric")
    alg = base_alg + sum(1 for p in collected.values() if p["style"] == "algebraic")
    return geo >= target if style == "geometric" else alg >= target


def arxiv_api_query(query: str, start: int = 0, max_results: int = 50) -> str:
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query={quote(query)}&start={start}&max_results={max_results}"
        "&sortBy=submittedDate&sortOrder=descending"
    )
    proc = subprocess.run(
        ["curl", "-fsSL", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall(f"{ATOM}entry"):
        raw_id = entry.findtext(f"{ATOM}id", default="")
        aid = raw_id.rstrip("/").split("/abs/")[-1]
        title = re.sub(r"\s+", " ", entry.findtext(f"{ATOM}title", default="")).strip()
        summary = re.sub(r"\s+", " ", entry.findtext(f"{ATOM}summary", default="")).strip()
        published = entry.findtext(f"{ATOM}published", default="")[:10]
        cats = [c.attrib.get("term", "") for c in entry.findall(f"{ATOM}category")]
        primary = entry.find(f"{ARXIV}primary_category")
        if primary is not None and primary.attrib.get("term"):
            cats.insert(0, primary.attrib["term"])
        papers.append(
            {
                "arxiv": aid,
                "title": title,
                "abstract": summary,
                "published": published,
                "categories": cats,
            }
        )
    return papers


def load_existing_ids() -> set[str]:
    ids: set[str] = set(EXCLUDE)
    for path in (MANIFEST, CONTEMP):
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            for src in data.get("sources", []):
                ids.add(canonical_arxiv_id(src["arxiv"]))
    return ids


def scrape(
    year_from: int = 2020,
    year_to: int = 2026,
    per_query: int = 40,
    min_margin: float = 0.0,
    sleep_s: float = 3.0,
    target_per_style: int | None = None,
) -> list[dict]:
    date_from = f"{year_from}0101"
    date_to = f"{year_to}1231"
    seen = load_existing_ids()
    collected: dict[str, dict] = {}
    base_geo, base_alg = manifest_style_counts()
    print(f"Manifest baseline: {base_geo} geometric, {base_alg} algebraic", flush=True)
    if target_per_style:
        print(f"Target per style: {target_per_style}", flush=True)

    queries = list(SEARCH_QUERIES)
    if target_per_style:
        # run queries for the lagging style first
        geo_now, alg_now = base_geo, base_alg
        if geo_now < alg_now:
            queries.sort(key=lambda q: 0 if q[0] == "geometric" else 1)
        elif alg_now < geo_now:
            queries.sort(key=lambda q: 0 if q[0] == "algebraic" else 1)

    for query_style, template in queries:
        if style_at_target("geometric", base_geo, base_alg, collected, target_per_style) and style_at_target(
            "algebraic", base_geo, base_alg, collected, target_per_style
        ):
            print("Both style targets reached.", flush=True)
            break
        if style_at_target(query_style, base_geo, base_alg, collected, target_per_style):
            print(f"Skipping {query_style} queries (target reached)", flush=True)
            continue
        q = template.format(date_from=date_from, date_to=date_to)
        print(f"Query [{query_style}]: {q}", flush=True)
        try:
            xml_text = arxiv_api_query(q, max_results=per_query)
        except subprocess.CalledProcessError as e:
            print(f"  API error: {e.stderr}", flush=True)
            continue
        papers = parse_feed(xml_text)
        print(f"  got {len(papers)} entries", flush=True)
        for p in papers:
            aid = canonical_arxiv_id(p["arxiv"])
            if aid in seen or aid in collected:
                continue
            blob = f"{p['title']} {p['abstract']}"
            score = score_text(blob, p["categories"])
            if score.label != query_style and abs(score.margin) < min_margin:
                continue
            # prefer query-aligned papers; allow cross-label if margin is strong
            if query_style == "geometric" and score.label == "algebraic" and score.margin < -1.0:
                continue
            if query_style == "algebraic" and score.label == "geometric" and score.margin > 1.0:
                continue
            # when balancing, accept query-bucket label if keyword margin is weak
            label = score.label
            if target_per_style and abs(score.margin) < 1.0:
                label = query_style
            if target_per_style and style_at_target(label, base_geo, base_alg, collected, target_per_style):
                continue
            collected[aid] = {
                "style": label,
                "arxiv": aid,
                "title": p["title"][:200],
                "content_topic": score.label,
                "published": p["published"],
                "query_bucket": query_style,
                "keyword_score_geo": round(score.geometric, 2),
                "keyword_score_alg": round(score.algebraic, 2),
                "keyword_margin": round(score.margin, 2),
                "keyword_hits_geo": score.hits_geo[:8],
                "keyword_hits_alg": score.hits_alg[:8],
                "categories": p["categories"][:5],
            }
            seen.add(aid)
        time.sleep(sleep_s)

    return sorted(collected.values(), key=lambda x: (x["style"], x["published"], x["arxiv"]), reverse=True)


def merge_manifest(contemporary: list[dict]) -> dict:
    base = {"sources": [], "exclude_test_papers": sorted(EXCLUDE)}
    if MANIFEST.exists():
        base = json.loads(MANIFEST.read_text(encoding="utf-8"))
    existing = {s["arxiv"] for s in base.get("sources", [])}
    added = [s for s in contemporary if s["arxiv"] not in existing]
    merged_sources = list(base.get("sources", [])) + [
        {k: v for k, v in s.items() if k in ("style", "arxiv", "title", "content_topic")}
        for s in added
    ]
    manifest = {
        "version": "4.0",
        "description": (
            "Research-register corpus: cross_view/within_view labels plus contemporary "
            "arXiv scrape (keyword-tagged geometric/algebraic style)."
        ),
        "min_words_per_chunk": base.get("min_words_per_chunk", 400),
        "chunk_target_words": base.get("chunk_target_words", 1200),
        "exclude_test_papers": base.get("exclude_test_papers", sorted(EXCLUDE)),
        "sources": merged_sources,
        "contemporary_meta": {
            "n_added": len(added),
            "year_from": contemporary[0].get("published", "")[:4] if contemporary else None,
        },
        "stats": {
            "n_geometric": sum(1 for s in merged_sources if s["style"] == "geometric"),
            "n_algebraic": sum(1 for s in merged_sources if s["style"] == "algebraic"),
            "n_total": len(merged_sources),
        },
    }
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape contemporary arXiv for style-tagged corpus")
    ap.add_argument("--year-from", type=int, default=2020)
    ap.add_argument("--year-to", type=int, default=2026)
    ap.add_argument("--per-query", type=int, default=40, help="Max results per search query")
    ap.add_argument("--min-margin", type=float, default=0.0, help="Min |geo-alg| keyword margin")
    ap.add_argument("--target-per-style", type=int, default=None, help="Stop after this many per style in manifest")
    ap.add_argument("--merge", action="store_true", help="Merge into manifest.json")
    ap.add_argument("--sleep", type=float, default=3.0, help="Seconds between API calls")
    args = ap.parse_args()

    papers = scrape(
        year_from=args.year_from,
        year_to=args.year_to,
        per_query=args.per_query,
        min_margin=args.min_margin,
        sleep_s=args.sleep,
        target_per_style=args.target_per_style,
    )
    geo = sum(1 for p in papers if p["style"] == "geometric")
    alg = sum(1 for p in papers if p["style"] == "algebraic")
    print(f"\nCollected {len(papers)} contemporary papers ({geo} geometric, {alg} algebraic)")

    contemporary_manifest = {
        "version": "1.0",
        "description": "Contemporary arXiv papers keyword-tagged for geometric/algebraic style.",
        "year_from": args.year_from,
        "year_to": args.year_to,
        "sources": papers,
        "stats": {"n_geometric": geo, "n_algebraic": alg, "n_total": len(papers)},
    }
    CONTEMP.parent.mkdir(parents=True, exist_ok=True)
    CONTEMP.write_text(json.dumps(contemporary_manifest, indent=2), encoding="utf-8")
    SCRAPE_LOG.parent.mkdir(parents=True, exist_ok=True)
    SCRAPE_LOG.write_text(json.dumps(papers, indent=2), encoding="utf-8")
    print(f"Wrote {CONTEMP}")
    print(f"Wrote {SCRAPE_LOG}")

    if args.merge:
        merged = merge_manifest(papers)
        MANIFEST.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        print(f"Merged into {MANIFEST}: +{merged['contemporary_meta']['n_added']} sources")
        print(json.dumps(merged["stats"], indent=2))


if __name__ == "__main__":
    main()
