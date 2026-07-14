#!/usr/bin/env python3
"""DEPRECATED: use scripts/render_jams_reports.R (R engine). Kept for reference only."""

from __future__ import annotations

import base64
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_jams_report import OUT, PAPERS, STEM_TO_ROLLING, bar_html, chips_html, tex_para

DOWNLOADS = Path.home() / "Downloads"
ANALYSIS_PATH = OUT / "stylo_full_analysis.json"
ROOT = Path(__file__).resolve().parents[1]

CSS = """
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#f4f5f7;color:#1a1a1a}
 header{background:#22303f;color:#fff;padding:24px 32px}
 header h1{margin:0 0 8px;font-size:22px}
 header p{margin:0;opacity:.85;font-size:13.5px;max-width:980px;line-height:1.5}
 .wrap{max-width:1200px;margin:0 auto;padding:28px 22px 60px}
 h2.sec{margin:40px 0 14px;font-size:17px;color:#22303f;border-bottom:2px solid #c9d2db;padding-bottom:8px}
 h3.sub{margin:22px 0 10px;font-size:14px;color:#334}
 .grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:18px 0}
 .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin:18px 0}
 .stat{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
 .stat .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8794a1;font-weight:700}
 .stat .val{font-size:26px;font-weight:700;color:#22303f;margin-top:4px}
 .stat .note{font-size:12px;color:#667;margin-top:6px;line-height:1.45}
 .card{background:#fff;border:1px solid #dce1e6;border-radius:10px;margin:18px 0;box-shadow:0 1px 3px rgba(0,0,0,.05);overflow:hidden}
 .card-hdr{background:#eef1f4;padding:12px 18px;border-bottom:1px solid #dce1e6}
 .card-hdr h3{margin:0;font-size:15px;color:#22303f}
 .card-hdr p{margin:4px 0 0;font-size:12.5px;color:#556}
 .card-body{padding:16px 18px}
 .cols2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
 @media(max-width:860px){.cols2{grid-template-columns:1fr}}
 table.data{width:100%;border-collapse:collapse;font-size:12.5px}
 table.data th,table.data td{padding:6px 8px;border-bottom:1px solid #eceff2;text-align:left;vertical-align:top}
 table.data th{background:#f7f9fa;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#667}
 .tag{display:inline-block;font-size:10.5px;padding:2px 7px;border-radius:10px;font-weight:600}
 .tag.geo{background:#e7f0f8;color:#1c5580}
 .tag.alg{background:#faeae9;color:#8a3936}
 .tag.ok{background:#e8f5ec;color:#1a6631}
 .tag.no{background:#fdecea;color:#8a2a24}
 .tag.warn{background:#fff4e5;color:#8a5a00}
 .method,.prose{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:18px 20px;margin:0 0 22px;font-size:13px;line-height:1.65}
 .method dl{display:grid;grid-template-columns:180px 1fr;gap:6px 12px;margin:12px 0 0}
 .method dt{color:#667;font-weight:600}
 .method dd{margin:0}
 .spark{display:flex;height:32px;border-radius:4px;overflow:hidden;border:1px solid #dce1e6;margin:8px 0}
 .spark div{min-width:2px}
 .conf-spark{display:flex;height:18px;border-radius:4px;overflow:hidden;border:1px solid #e0e4e8;margin:6px 0 12px}
 .conf-spark div{min-width:2px;background:#94a3b8}
 .heatmap-wrap{overflow-x:auto;margin:10px 0}
 .heatmap{font-size:10px;border-collapse:collapse}
 .heatmap th,.heatmap td{padding:3px 5px;border:1px solid #e8ebee;text-align:center;white-space:nowrap}
 .heatmap th.sticky{position:sticky;left:0;background:#f7f9fa;z-index:1;text-align:left;max-width:220px;overflow:hidden;text-overflow:ellipsis}
 .imgroll{max-width:100%;height:auto;border:1px solid #dce1e6;border-radius:6px;margin-top:8px}
 .rlabel{font-size:11px;color:#667;margin:10px 0 3px}
 .excerpt{font-size:13.5px;line-height:1.55;background:#fbfcfd;border:1px solid #eceff2;border-radius:8px;padding:12px 14px;margin:10px 0}
 .dist-bar{height:14px;border-radius:3px;background:#eef1f4;position:relative;margin:4px 0 10px}
 .dist-bar .fill{height:100%;border-radius:3px}
 ul.compact{margin:8px 0;padding-left:18px;font-size:13px;line-height:1.55}
 .quadrant-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}
 .qcell{border:1px solid #dce1e6;border-radius:8px;padding:10px 12px;background:#fbfcfd;font-size:12.5px}
 .qcell b{display:block;margin-bottom:4px;color:#22303f}
 .health-ok{border-left:4px solid #2d8a4e}
 .health-warn{border-left:4px solid #c47f00}
 .health-crit{border-left:4px solid #b83232}
 .hist{display:flex;align-items:flex-end;height:72px;gap:2px;margin:8px 0 12px;border:1px solid #e8ebee;border-radius:6px;padding:8px 8px 4px;background:#fafbfc}
 .hist div{flex:1;background:#5b7a9d;min-width:3px;border-radius:2px 2px 0 0}
 .mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
 .ci{color:#556;font-size:11.5px}
 .badge-crit{background:#fdecea;color:#8a2a24;font-size:10.5px;padding:2px 8px;border-radius:10px;font-weight:700}
 .badge-warn{background:#fff4e5;color:#8a5a00;font-size:10.5px;padding:2px 8px;border-radius:10px;font-weight:700}
 .badge-ok{background:#e8f5ec;color:#1a6631;font-size:10.5px;padding:2px 8px;border-radius:10px;font-weight:700}
 pre.stats{background:#f7f9fa;border:1px solid #e8ebee;border-radius:8px;padding:12px 14px;font-size:12px;line-height:1.5;overflow-x:auto}
"""


def load_analysis() -> dict:
    return json.loads(ANALYSIS_PATH.read_text(encoding="utf-8"))


def paper_stem_for(p: dict) -> str:
    return STEM_TO_ROLLING[p["file_stem"]]


def img_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    b64 = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def heat_color(value: float, vmin: float, vmax: float) -> str:
    t = 0.5 if vmax <= vmin else (value - vmin) / (vmax - vmin)
    r = int(230 - t * 120)
    g = int(240 - t * 80)
    b = int(250 - t * 40)
    return f"background:rgb({r},{g},{b})"


def roll_pred(roll: dict, weighted: bool = False) -> str:
    if weighted and roll.get("confidence_weighted_geo_share") is not None:
        return "geometric" if roll["confidence_weighted_geo_share"] > 0.5 else "algebraic"
    return "geometric" if roll.get("share_geometric", 0) > roll.get("share_algebraic", 0) else "algebraic"


def timeline_html(bins: list[dict], show_confidence: bool = False) -> str:
    parts = []
    for b in bins:
        if b.get("geo_share") is None:
            continue
        geo = b["geo_share"]
        pct_geo = geo * 100
        style = f"flex:1;background:linear-gradient(to top,#c0504d {100-pct_geo:.1f}%,#2b7bba {100-pct_geo:.1f}%)"
        title = f"slices {b.get('start_slice','?')}-{b.get('end_slice','?')}: {pct_geo:.0f}% geo"
        if show_confidence and b.get("mean_margin") is not None:
            title += f", margin {b['mean_margin']:.3f}"
        parts.append(f'<div style="{style}" title="{html.escape(title)}"></div>')
    return f'<div class="spark">{"".join(parts)}</div>'


def confidence_timeline_html(bins: list[dict]) -> str:
    parts = []
    max_m = max((b.get("mean_margin") or 0) for b in bins) or 0.001
    for b in bins:
        m = b.get("mean_margin") or 0
        h = max(15, int(100 * m / max_m))
        op = min(1.0, 0.25 + m / max_m * 0.75)
        title = f"slices {b.get('start_slice','?')}-{b.get('end_slice','?')}: mean margin {m:.4f}"
        parts.append(
            f'<div style="flex:1;height:{h}%;align-self:flex-end;background:rgba(34,48,63,{op:.2f})" title="{html.escape(title)}"></div>'
        )
    return f'<div class="conf-spark" style="align-items:flex-end;height:48px">{"".join(parts)}</div>'


def nn_table(neighbors: list[dict]) -> str:
    rows = []
    for n in neighbors:
        cls = n["class"]
        sid = n.get("short_id") or n["id"]
        rows.append(
            f'<tr><td><span class="tag {cls[:3]}">{cls}</span></td>'
            f'<td>{html.escape(str(sid))}</td>'
            f'<td>{n["distance"]:.4f}</td></tr>'
        )
    return (
        '<table class="data"><tr><th>Class</th><th>Reference</th><th>Δ distance</th></tr>'
        + "".join(rows)
        + "</table>"
    )


def feature_table(features: list[dict]) -> str:
    rows = []
    for f in features:
        score = f["style_score"]
        direction = "→ algebraic" if score > 0 else "→ geometric"
        rows.append(
            f"<tr><td>{html.escape(f['word'])}</td>"
            f"<td>{f['test_freq']:.3f}</td>"
            f"<td>{f['geo_centroid']:.3f}</td>"
            f"<td>{f['alg_centroid']:.3f}</td>"
            f"<td>{score:+.3f} <span style='color:#667;font-size:11px'>{direction}</span></td></tr>"
        )
    return (
        '<table class="data"><tr><th>Stopword</th><th>Paper freq</th>'
        "<th>Geo centroid</th><th>Alg centroid</th><th>Style pull</th></tr>"
        + "".join(rows)
        + "</table>"
    )


def short_paper_name(stem: str) -> str:
    return stem.split("__")[2] if "__" in stem else stem[:36]


def margin_histogram_html(hist: list[dict]) -> str:
    if not hist:
        return ""
    mx = max(h.get("count", 0) for h in hist) or 1
    bars = []
    for h in hist:
        ht = max(4, int(60 * h.get("count", 0) / mx))
        title = f"[{h.get('bin_low',0):.3f}, {h.get('bin_high',0):.3f}): n={h.get('count',0)}"
        bars.append(
            f'<div style="height:{ht}px" title="{html.escape(title)}"></div>'
        )
    return f'<div class="hist">{"".join(bars)}</div>'


def threshold_table(roll: dict, expert_style: str) -> str:
    rows = []
    for t in roll.get("threshold_stats", []):
        if not t.get("n"):
            continue
        geo = t.get("geo_share")
        pred = "geometric" if geo and geo > 0.5 else "algebraic"
        ok = pred == expert_style
        ci_lo = t.get("wilson_ci_low")
        ci_hi = t.get("wilson_ci_high")
        ci_txt = (
            f'<span class="ci">[{ci_lo*100:.1f}%, {ci_hi*100:.1f}%]</span>'
            if ci_lo is not None and ci_hi is not None
            else ""
        )
        rows.append(
            f"<tr><td>≥ {t['threshold']:.2f}</td><td>{t['n']}</td><td>{t.get('pct',0):.1f}%</td>"
            f"<td>{(geo or 0)*100:.1f}% {ci_txt}</td><td>{pred}</td>"
            f"<td><span class='tag {'ok' if ok else 'no'}'>{'match' if ok else 'miss'}</span></td></tr>"
        )
    if not rows:
        return "<p style='font-size:12.5px;color:#667'>No slices above confidence thresholds.</p>"
    return (
        "<table class='data'><tr><th>Margin ≥</th><th>Slices (n)</th><th>% paper</th>"
        "<th>Geo share [Wilson 95% CI]</th><th>Pred style</th><th>vs expert</th></tr>"
        + "".join(rows)
        + "</table>"
    )


def margin_quantile_table(roll: dict) -> str:
    qrows = [
        ("p05", roll.get("margin_p05")),
        ("p10", roll.get("margin_p10")),
        ("p25", roll.get("margin_p25")),
        ("p50 (median)", roll.get("margin_median")),
        ("p75", roll.get("margin_p75")),
        ("p90", roll.get("margin_p90")),
        ("p95", roll.get("margin_p95")),
        ("max", roll.get("margin_max")),
        ("mean ± sd", f"{roll.get('margin_mean', 0):.4f} ± {roll.get('margin_sd', 0):.4f}"),
    ]
    rows = "".join(
        f"<tr><td>{lbl}</td><td class='mono'>{val if isinstance(val, str) else f'{val:.4f}'}</td></tr>"
        for lbl, val in qrows
        if val is not None
    )
    return (
        "<table class='data'><tr><th>Margin quantile</th><th>Value</th></tr>"
        + rows
        + "</table>"
    )


def corpus_health_section(analysis: dict) -> str:
    ch = analysis.get("corpus_health", {})
    if not ch:
        return ""
    loo = ch.get("loo_sample", {})
    intra = ch.get("intra_class_delta", {})
    inter = ch.get("inter_class_delta", {})
    verdicts = ch.get("verdict", [])
    badges = []
    for v in verdicts:
        if "CRITICAL" in v:
            badges.append(f'<span class="badge-crit">{html.escape(v[:80])}…</span>' if len(v) > 80 else f'<span class="badge-crit">{html.escape(v)}</span>')
        elif "WEAK" in v:
            badges.append(f'<span class="badge-warn">{html.escape(v)}</span>')
        else:
            badges.append(f'<span class="badge-ok">{html.escape(v)}</span>')

    disc_rows = ""
    for d in ch.get("top_discriminators", [])[:10]:
        disc_rows += (
            f"<tr><td>{html.escape(d['word'])}</td>"
            f"<td>{d['geo_centroid']:.4f}</td><td>{d['alg_centroid']:.4f}</td>"
            f"<td>{d['geo_minus_alg']:+.5f}</td></tr>"
        )

    return f"""
<h2 class="sec">Corpus health &amp; separability</h2>
<div class="prose health-{'crit' if ch.get('class_separability_l1', 1) < 0.005 else 'warn' if loo.get('accuracy', 1) < 0.85 else 'ok'}">
<p>Diagnostics on the <b>actual stylo training matrix</b> ({analysis['meta']['reference_n']:,} balanced chunks,
{analysis['meta'].get('n_features_used', '?')} stopword features). These quantify whether the reference corpus
can support reliable geometric vs algebraic attribution before interpreting JAMS holdout results.</p>
<div style="margin:10px 0">{''.join(f'<div style="margin:4px 0">{b}</div>' for b in badges)}</div>
</div>
<div class="grid4">
  <div class="stat"><div class="lbl">Centroid L1 separation</div>
    <div class="val">{ch.get('class_separability_l1', 0):.4f}</div>
    <div class="note">Mean |geo−alg| over stylo features; &lt;0.005 ≈ indistinguishable</div></div>
  <div class="stat"><div class="lbl">Sampled LOO accuracy</div>
    <div class="val">{loo.get('accuracy_pct', '—')}%</div>
    <div class="note">n={loo.get('n_sampled', '?')}; Wilson 95% CI [{loo.get('wilson_ci_low', 0)*100:.1f}%, {loo.get('wilson_ci_high', 0)*100:.1f}%]</div></div>
  <div class="stat"><div class="lbl">Inter / intra Δ ratio</div>
    <div class="val">{ch.get('separation_ratio', 0):.3f}</div>
    <div class="note">(cross-centroid Δ mean) / (own-centroid Δ mean); higher = more separated</div></div>
  <div class="stat"><div class="lbl">Training balance</div>
    <div class="val">50/50</div>
    <div class="note">{analysis['meta']['reference_geometric']:,} geo / {analysis['meta']['reference_algebraic']:,} alg chunks</div></div>
</div>
<div class="cols2">
  <div class="card"><div class="card-hdr"><h3>Intra-class Burrows Δ (mean to own centroid)</h3></div>
    <div class="card-body"><table class="data">
      <tr><th>Class</th><th>Mean Δ</th></tr>
      <tr><td>geometric</td><td>{intra.get('geometric_mean', 0):.4f}</td></tr>
      <tr><td>algebraic</td><td>{intra.get('algebraic_mean', 0):.4f}</td></tr>
    </table></div></div>
  <div class="card"><div class="card-hdr"><h3>Cross-class Burrows Δ (mean to other centroid)</h3></div>
    <div class="card-body"><table class="data">
      <tr><th>Source class</th><th>Δ to other centroid</th></tr>
      <tr><td>geo chunks → alg centroid</td><td>{inter.get('geo_chunks_to_alg_centroid', 0):.4f}</td></tr>
      <tr><td>alg chunks → geo centroid</td><td>{inter.get('alg_chunks_to_geo_centroid', 0):.4f}</td></tr>
    </table></div></div>
</div>
<h3 class="sub">Top training discriminators (geo − alg centroid)</h3>
<table class="data"><tr><th>Stopword</th><th>Geo μ</th><th>Alg μ</th><th>Δ</th></tr>{disc_rows}</table>
"""


def confusion_section(analysis: dict) -> str:
    conf = analysis.get("confusion", {})
    def rows_for(kind: str) -> str:
        rows = ""
        for stem, row in conf.get(kind, {}).items():
            ok = row.get("match")
            rows += (
                f"<tr><td>{html.escape(short_paper_name(stem))}</td>"
                f"<td><span class='tag {row['expert'][:3]}'>{row['expert']}</span></td>"
                f"<td><span class='tag {row['predicted'][:3]}'>{row['predicted']}</span></td>"
                f"<td><span class='tag {'ok' if ok else 'no'}'>{'✓' if ok else '✗'}</span></td></tr>"
            )
        return rows
    return f"""
<h2 class="sec">Confusion vs expert style labels</h2>
<p style="font-size:13px;color:#556">Gold standard = expert v4 style axis on holdout excerpts (not filename prefix).
n=4 holdout papers — accuracy is descriptive only; no binomial calibration at this sample size.</p>
<div class="cols2">
  <div><h3 class="sub">Rolling majority</h3>
    <table class="data"><tr><th>Paper</th><th>Expert</th><th>Predicted</th><th></th></tr>
    {rows_for('rolling')}</table></div>
  <div><h3 class="sub">Whole-paper classify</h3>
    <table class="data"><tr><th>Paper</th><th>Expert</th><th>Predicted</th><th></th></tr>
    {rows_for('whole_paper')}</table></div>
</div>
"""


def benchmark_section(analysis: dict) -> str:
    bench = analysis.get("benchmarks", {})
    corp = bench.get("corpora")
    feat = bench.get("features")
    corp_rows = ""
    if corp:
        items = corp if isinstance(corp, list) else [
            {"label": v.get("label", k), **v} for k, v in corp.items()
        ] if isinstance(corp, dict) else []
        if isinstance(corp, dict):
            for k, v in corp.items():
                corp_rows += (
                    f"<tr><td>{html.escape(v.get('label', k))}</td>"
                    f"<td>{v.get('n_train', '—')}</td>"
                    f"<td>{v.get('style_accuracy', '—')}/4</td></tr>"
                )
    feat_rows = ""
    if feat and isinstance(feat, list):
        for row in sorted(feat, key=lambda x: -x.get("accuracy", 0)):
            feat_rows += (
                f"<tr><td>{html.escape(row.get('label', ''))}</td>"
                f"<td>{row.get('accuracy', '—')}/4</td>"
                f"<td>{row.get('separation', 0):.4f}</td>"
                f"<td>{row.get('n_features', '—')}</td></tr>"
            )
    return f"""
<h2 class="sec">Corpus &amp; feature ablations</h2>
<div class="cols2">
  <div>
    <h3 class="sub">Training corpus variants (whole-paper accuracy)</h3>
    <table class="data"><tr><th>Corpus</th><th>n_train</th><th>Style acc</th></tr>{corp_rows}</table>
  </div>
  <div>
    <h3 class="sub">Feature sets (whole-paper accuracy)</h3>
    <table class="data"><tr><th>Config</th><th>Acc</th><th>Separation</th><th>MFW</th></tr>{feat_rows}</table>
  </div>
</div>
"""


def inference_note_block(analysis: dict) -> str:
    m = analysis["meta"]
    med_margin = 0.01
    if analysis.get("rolling"):
        first = next(iter(analysis["rolling"].values()))
        med_margin = first.get("margin_median", 0.01)
    return f"""
<div class="method">
<h2 style="margin:0 0 8px;font-size:16px;color:#22303f">Statistical inference notes</h2>
<ul class="compact">
  <li><b>Rolling slices are not independent.</b> Window = {m['slice_size']} words, overlap = {m['slice_overlap']} → step = {m.get('slice_step', 100)} words.
  Reported Wilson and bootstrap CIs on slice labels treat slices as i.i.d. (optimistic / anti-conservative for overlap).
  Effective independent windows ≈ <code>ceil(words / {m.get('slice_step', 100)})</code> per paper.</li>
  <li><b>Margin</b> = Burrows Δ to 2nd-nearest class minus Δ to nearest class. Typical median ≈ {med_margin:.4f}; small margins indicate near-tie decisions.</li>
  <li><b>H₀ for geo share:</b> two-sided exact binomial test vs p=0.5 per paper. Cohen's h effect size vs 0.5 reported.</li>
  <li><b>Holdout n=4:</b> quadrant accuracy is illustrative; primary evidence is per-paper shares, CIs, and high-margin subsets.</li>
  <li><b>Expert labels</b> are independent of stylo training; stylo uses stopwords only.</li>
</ul>
</div>
"""

def top_slices_table(slices: list[dict]) -> str:
    if not slices:
        return ""
    rows = []
    for s in slices:
        rows.append(
            f"<tr><td>{s['slice_index']}</td><td>{s.get('word_offset','—')}</td>"
            f"<td><span class='tag {s['predicted'][:3]}'>{s['predicted']}</span></td>"
            f"<td>{s['margin']:.4f}</td></tr>"
        )
    return (
        "<table class='data'><tr><th>Slice #</th><th>Word offset</th><th>Label</th><th>Margin</th></tr>"
        + "".join(rows)
        + "</table>"
    )


def class_distance_bars(geo_mean: float, alg_mean: float, predicted: str) -> str:
    mx = max(geo_mean, alg_mean, 0.001)
    gw = geo_mean / mx * 100
    aw = alg_mean / mx * 100
    winner = "geometric" if geo_mean < alg_mean else "algebraic"
    return f"""
<p style="font-size:12.5px;color:#556">Mean Burrows Δ to reference class centroids (lower = closer). Stylo assigns <b>{predicted}</b>.</p>
<div style="margin:8px 0"><span class="tag geo">geometric refs</span> {geo_mean:.4f}
  <div class="dist-bar"><div class="fill" style="width:{gw:.1f}%;background:#2b7bba"></div></div></div>
<div style="margin:8px 0"><span class="tag alg">algebraic refs</span> {alg_mean:.4f}
  <div class="dist-bar"><div class="fill" style="width:{aw:.1f}%;background:#c0504d"></div></div></div>
<p style="font-size:12px;color:#667">Closer class by mean Δ: <b>{winner}</b> (Δalg−Δgeo = {alg_mean - geo_mean:+.4f})</p>"""


def executive_summary(analysis: dict) -> str:
    m = analysis["meta"]
    sa = analysis.get("style_accuracy", {})
    manifest = m.get("manifest", {})
    ch = analysis.get("corpus_health", {})
    loo = ch.get("loo_sample", {})
    return f"""
<div class="prose">
<h2 style="margin-top:0;font-size:16px;color:#22303f">Executive summary (statistical)</h2>
<p>Four JAMS papers on a <b>content×style quadrant</b>: expert v4 style labels (gold) vs stylo Burrows-Δ stopword
classification on full PDF text. Training corpus: {m['reference_n']:,} balanced chunks ({manifest.get('n_sources', '?')} arXiv sources, manifest v{manifest.get('version', '—')}).</p>
<p><b>Corpus health:</b> centroid L1 separation = <b>{ch.get('class_separability_l1', 0):.4f}</b>;
sampled LOO accuracy = <b>{loo.get('accuracy_pct', '—')}%</b> (Wilson 95% CI {loo.get('wilson_ci_low', 0)*100:.1f}–{loo.get('wilson_ci_high', 0)*100:.1f}% on n={loo.get('n_sampled', '?')}).
Inter/intra Δ ratio = <b>{ch.get('separation_ratio', 0):.3f}</b>.</p>
<p><b>Holdout style accuracy:</b> rolling majority <b>{sa.get('rolling_majority', '—')}/4</b>;
whole-paper <b>{sa.get('whole_paper', '—')}/4</b>. Primary inference unit = rolling geo share with Wilson/bootstrap CIs and margin-filtered subsets.</p>
</div>"""


def method_block(analysis: dict) -> str:
    m = analysis["meta"]
    manifest = m.get("manifest", {})
    return f"""
<div class="method">
<h2 style="margin:0 0 8px;font-size:16px;color:#22303f">Stylometric protocol</h2>
<p>Separates <b>content</b> (objects under discussion) from <b>style</b> (spatial vs symbolic reasoning register).
Stylo uses function words only; expert ratings use the v4 rubric (style features, object categories, holistic/content/style axes).</p>
<dl>
<dt>Classifier</dt><dd>{m['method']} ({m['classification_method']})</dd>
<dt>Features</dt><dd>{m['features']}</dd>
<dt>Training dir</dt><dd>{m.get('train_dir', 'balanced')}</dd>
<dt>Reference chunks</dt><dd>{m['reference_n']:,} ({m['reference_geometric']:,} geo / {m['reference_algebraic']:,} alg)</dd>
<dt>Manifest sources</dt><dd>{manifest.get('n_sources', '—')} papers ({manifest.get('n_sources_geometric', '—')} geo / {manifest.get('n_sources_algebraic', '—')} alg), v{manifest.get('version', '—')}</dd>
<dt>Rolling windows</dt><dd>{m['slice_size']} words, overlap {m['slice_overlap']}</dd>
<dt>Slice confidence</dt><dd>{m.get('confidence_note', '')}</dd>
<dt>Test papers</dt><dd>Masur–Schleimer, Bateman–Katz, Dritschel–McCullough, Hrushovski (full PDF text)</dd>
</dl>
</div>"""


def quadrant_overview() -> str:
    cells = []
    for p in PAPERS:
        cells.append(
            f'<div class="qcell"><b>{p["pid"]} {html.escape(p["authors"])}</b>'
            f'{html.escape(p["quadrant"])}<br>'
            f'Expert style: <span class="tag {p["style_label"][:3]}">{p["style_label"]}</span> '
            f'· content: <span class="tag {p["content_label"][:3]}">{p["content_label"]}</span></div>'
        )
    return f"""
<h2 class="sec">Content×style quadrant</h2>
<div class="quadrant-grid">{''.join(cells)}</div>
<p style="font-size:12.5px;color:#556">Filename prefixes encode <em>content</em> quadrant; stylo targets <em>style</em> via stopwords.
Crossed cells (Bateman, Dritschel) deliberately decouple content from reasoning register.</p>"""


def summary_stats(analysis: dict) -> str:
    m = analysis["meta"]
    papers = analysis["full_papers"]["papers"]
    style_hits = sum(1 for p in PAPERS if papers[paper_stem_for(p)]["predicted"] == p["style_label"])
    roll_hits = sum(1 for p in PAPERS if roll_pred(analysis["rolling"][paper_stem_for(p)]) == p["style_label"])
    conf_hits = sum(
        1
        for p in PAPERS
        if roll_pred(analysis["rolling"][paper_stem_for(p)], weighted=True) == p["style_label"]
    )
    return f"""
<div class="grid4">
  <div class="stat"><div class="lbl">Rolling majority</div><div class="val">{roll_hits}/4</div>
    <div class="note">Unweighted slice vote (primary aggregate metric)</div></div>
  <div class="stat"><div class="lbl">Confidence-weighted</div><div class="val">{conf_hits}/4</div>
    <div class="note">Slices weighted by Δ margin (2nd−1st class)</div></div>
  <div class="stat"><div class="lbl">Whole-paper</div><div class="val">{style_hits}/4</div>
    <div class="note">Single classify on full ~13k–36k word texts</div></div>
  <div class="stat"><div class="lbl">Training corpus</div><div class="val">{m['reference_n']:,}</div>
    <div class="note">Balanced chunks · {m.get('manifest', {}).get('n_sources', '?')} arXiv sources</div></div>
</div>"""


def master_table(analysis: dict) -> str:
    rows = []
    papers = analysis["full_papers"]["papers"]
    excerpts = analysis.get("excerpts", {}).get("papers", {})
    for p in PAPERS:
        stem = paper_stem_for(p)
        pa = papers[stem]
        ro = analysis["rolling"][stem]
        ex = excerpts.get(stem, {})
        rp = roll_pred(ro)
        rw = roll_pred(ro, weighted=True)
        rows.append(
            f"<tr><td>{html.escape(p['authors'])}</td>"
            f"<td><span class='tag {p['style_label'][:3]}'>{p['style_label']}</span></td>"
            f"<td>{rp} <span class='tag {'ok' if rp==p['style_label'] else 'no'}'>{'✓' if rp==p['style_label'] else '✗'}</span></td>"
            f"<td>{rw} <span class='tag {'ok' if rw==p['style_label'] else 'no'}'>{'✓' if rw==p['style_label'] else '✗'}</span></td>"
            f"<td>{pa['predicted']}</td>"
            f"<td>{ex.get('predicted','—')}</td>"
            f"<td>{ro['share_geometric']*100:.1f}%</td>"
            f"<td class='ci'>[{ro.get('geo_wilson_ci_low',0)*100:.1f}, {ro.get('geo_wilson_ci_high',0)*100:.1f}]</td>"
            f"<td class='mono'>{ro.get('binomial_p_vs_half', '—')}</td>"
            f"<td class='mono'>{ro.get('cohens_h_vs_half', 0):+.3f}</td>"
            f"<td>{ro.get('margin_median', 0):.4f}</td>"
            f"<td>{ro['n_slices']}</td>"
            f"<td>{ro.get('effective_independent_slices','—')}</td></tr>"
        )
    return """
<table class="data">
<tr><th>Paper</th><th>Expert</th><th>Rolling</th><th>Conf-wtd</th>
<th>Whole</th><th>Excerpt</th><th>Geo%</th><th>Wilson 95%</th><th>p vs ½</th><th>Cohen h</th>
<th>Med margin</th><th>Slices</th><th>Eff. n†</th></tr>
""" + "".join(rows) + "</table><p class='ci'>† Effective independent slices ≈ ceil(words/100); overlap makes raw slice count anti-conservative for variance.</p>"


def corpus_section() -> str:
    chunks_dir = ROOT / "corpus_classify" / "reference_research" / "chunks"
    n_geo = len(list(chunks_dir.glob("geometric__*.txt"))) if chunks_dir.exists() else 0
    n_alg = len(list(chunks_dir.glob("algebraic__*.txt"))) if chunks_dir.exists() else 0
    return f"""
<h2 class="sec">Reference corpus</h2>
<div class="prose">
<p>Built from cross_view/within_view expert-labeled arXiv IDs plus a contemporary scrape (2020–2026) with
keyword-based geometric/algebraic style tagging. PDFs chunked at ~1200 words (400 word minimum).</p>
<ul class="compact">
  <li>Raw chunks on disk: <b>{n_geo + n_alg:,}</b> ({n_geo:,} geometric, {n_alg:,} algebraic)</li>
  <li>Training uses <b>balanced</b> 50/50 subsample after label curation</li>
  <li>Contemporary geometric boost: math.GT/DG/AT, mapping class, foliation, cube complexes, etc.</li>
  <li>Contemporary algebraic boost: math.RA/CT/LO/RT, model theory, additive combinatorics, etc.</li>
</ul>
</div>"""


def limitations_block() -> str:
    return """
<h2 class="sec">Interpretation &amp; limitations</h2>
<div class="prose">
<ul class="compact">
  <li><b>Stopwords encode register, not rubric style.</b> Function-word frequencies capture formality and exposition patterns; they weakly separate spatial vs symbolic reasoning even on 18k chunks (typical slice margins ~0.007–0.02).</li>
  <li><b>Near-50/50 rolling is not failure</b> if high-confidence slices align with expert labels — but on this corpus only 2–9% of slices exceed margin 0.05, and expert agreement on those subsets is mixed except Hrushovski.</li>
  <li><b>Content×style crossed papers</b> (Bateman, Dritschel) are the hardest cells: shared research register pulls all papers toward algebraic stopword centroids.</li>
  <li><b>Expert excerpt ratings</b> are independent of stylo; quadrant labels come from v4 rubric, not from the reference corpus.</li>
  <li><b>Keyword-tagged contemporary sources</b> may mislabel borderline papers; manual overrides and balanced subsampling mitigate but do not eliminate noise.</li>
</ul>
</div>"""


def paper_section(p: dict, analysis: dict) -> str:
    stem = paper_stem_for(p)
    pa = analysis["full_papers"]["papers"][stem]
    ex = analysis.get("excerpts", {}).get("papers", {}).get(stem, {})
    roll = analysis["rolling"].get(stem, {})
    png = OUT / f"rolling_{stem}.png"
    img = f'<img class="imgroll" src="{img_data_uri(png)}" alt="rolling classification">' if png.exists() else ""

    rp = roll_pred(roll)
    rw = roll_pred(roll, weighted=True)
    style_ok = pa["predicted"] == p["style_label"]
    roll_ok = rp == p["style_label"]
    conf_ok = rw == p["style_label"]

    return f"""
<div class="card" id="{p['key']}">
  <div class="card-hdr">
    <h3>{p['pid']} {html.escape(p['authors'])} — {html.escape(p['title'])}</h3>
    <p>{html.escape(p['quadrant'])} · {html.escape(p['journal'])} · doi:{html.escape(p['doi'])}</p>
  </div>
  <div class="card-body">
    <div class="cols2">
      <div>
        <h3 class="sub">Expert axis ratings (holdout excerpt)</h3>
        <div class="excerpt">{tex_para(p['excerpt_tex'])}</div>
        <div class="rlabel">holistic geometric↔algebraic</div>{bar_html(p['holistic'])}
        <div class="rlabel">style axis (spatial − symbolic)</div>{bar_html(p['style_axis'])}
        <div class="rlabel">content axis (geo − alg objects)</div>{bar_html(p['content_axis'])}
        <div class="rlabel">style features (v4 rubric)</div>{chips_html(p['style_on'], 'style')}
        <p style="font-size:12px;color:#667">2AFC: {p['afc_side']} more geometric in {p['afc_pct']}% of runs (consistency {p['afc_consistency']:.2f})</p>
      </div>
      <div>
        <h3 class="sub">Stylo rolling ({roll.get('n_slices', 0)} slices)</h3>
        <p>Expert style: <span class="tag {p['style_label'][:3]}">{p['style_label']}</span></p>
        <p>Rolling majority: <span class="tag {rp[:3]}">{rp}</span> <span class="tag {'ok' if roll_ok else 'no'}">{'match' if roll_ok else 'miss'}</span>
           · Conf-weighted: <span class="tag {rw[:3]}">{rw}</span> <span class="tag {'ok' if conf_ok else 'no'}">{'match' if conf_ok else 'miss'}</span></p>
        <p>Geo {roll.get('share_geometric', 0)*100:.1f}% <span class="ci">Wilson [{roll.get('geo_wilson_ci_low',0)*100:.1f}%, {roll.get('geo_wilson_ci_high',0)*100:.1f}%]</span>
           · Bootstrap [{roll.get('geo_bootstrap_ci_low',0)*100:.1f}%, {roll.get('geo_bootstrap_ci_high',0)*100:.1f}%]
           · p(H₀: p=½) = <span class="mono">{roll.get('binomial_p_vs_half', '—')}</span>
           · Cohen h = <span class="mono">{roll.get('cohens_h_vs_half', 0):+.3f}</span></p>
        <p>Conf-weighted geo {(roll.get('confidence_weighted_geo_share') or 0)*100:.1f}%
           · lag-1 label agreement {roll.get('lag1_label_agreement', 0)*100:.1f}%
           · ~{roll.get('text_length', '?')} words · eff. n≈{roll.get('effective_independent_slices', '?')}</p>
        <div class="rlabel">Style label timeline</div>
        {timeline_html(roll.get('timeline_bins', []))}
        <div class="rlabel">Mean slice confidence (margin) timeline</div>
        {confidence_timeline_html(roll.get('timeline_bins', []))}
        <p style="font-size:11px;color:#667">Blue/red = geo/alg share per segment; bar height/opacity = mean Delta margin</p>
        {img}
      </div>
    </div>
    <div class="cols2" style="margin-top:16px">
      <div>
        <h3 class="sub">Confidence thresholds</h3>
        <p style="font-size:12px;color:#556">Margin = Δ(2nd class) − Δ(1st class). Higher = more confident slice assignment.</p>
        <p style="font-size:12px">Median margin: <b>{roll.get('margin_median', 0):.4f}</b>
           · Mean±sd: <b>{roll.get('margin_mean', 0):.4f} ± {roll.get('margin_sd', 0):.4f}</b></p>
        {margin_quantile_table(roll)}
        <div class="rlabel">Margin histogram (slice-level)</div>
        {margin_histogram_html(roll.get('margin_histogram', []))}
        {threshold_table(roll, p['style_label'])}
      </div>
      <div>
        <h3 class="sub">Whole-paper &amp; excerpt classify</h3>
        <p>Whole-paper: <span class="tag {pa['predicted'][:3]}">{pa['predicted']}</span>
           <span class="tag {'ok' if style_ok else 'no'}">{'match' if style_ok else 'miss'}</span></p>
        <p>Excerpt-only: <span class="tag {(ex.get('predicted') or 'alg')[:3]}">{ex.get('predicted', '—')}</span></p>
        {class_distance_bars(pa['geo_mean_distance'], pa['alg_mean_distance'], pa['predicted'])}
        <p style="font-size:12px;color:#556">10-NN class mix: {pa.get('nn_geo_count', '?')} geometric / {pa.get('nn_alg_count', '?')} algebraic</p>
        <h3 class="sub" style="margin-top:14px">Top confident slices</h3>
        {top_slices_table(roll.get('top_confident_slices', []))}
      </div>
    </div>
    <div class="cols2" style="margin-top:16px">
      <div><h3 class="sub">10 nearest reference chunks</h3>{nn_table(pa['nearest_neighbors'])}</div>
      <div><h3 class="sub">Top discriminating stopwords</h3>{feature_table(pa['top_style_features'])}</div>
    </div>
  </div>
</div>"""


def heatmap_section(analysis: dict) -> str:
    fp = analysis["full_papers"]
    all_d = fp.get("distance_matrix_top18") or fp.get("distance_matrix", {})
    if isinstance(all_d, list):
        papers = analysis.get("full_papers", {}).get("papers", {})
        all_d = {k: v for k, v in zip(papers.keys(), all_d)} if papers else {}
    ref_scores: dict[str, float] = {}
    for dists in all_d.values():
        for ref, val in dists.items():
            ref_scores[ref] = min(ref_scores.get(ref, 999.0), val)
    top_refs = sorted(ref_scores, key=ref_scores.get)[:18]
    all_vals = []
    row_data = []
    for paper_stem, dists in all_d.items():
        short = paper_stem.split("__")[2] if "__" in paper_stem else paper_stem
        row_vals = [dists.get(ref) for ref in top_refs]
        all_vals.extend(v for v in row_vals if v is not None)
        row_data.append((short, row_vals))
    vmin, vmax = min(all_vals), max(all_vals)
    rows_html = []
    for short, row_vals in row_data:
        cells = [f'<th class="sticky">{html.escape(short[:40])}</th>']
        for ref, v in zip(top_refs, row_vals):
            if v is None:
                cells.append(f'<td style="background:#f0f0f0">—</td>')
            else:
                cells.append(
                    f'<td style="{heat_color(v, vmin, vmax)}" title="{html.escape(ref)}">{v:.2f}</td>'
                )
        rows_html.append("<tr>" + "".join(cells) + "</tr>")
    ref_classes = analysis["reference_classes"]
    header = '<tr><th class="sticky">Paper ↓ / Ref →</th>' + "".join(
        f'<th title="{html.escape(r)}"><span class="tag {ref_classes.get(r,"")[:3]}">{ref_classes.get(r,"")[:3]}</span> '
        f'{html.escape(r.split("__")[1][:14])}</th>'
        for r in top_refs
    ) + "</tr>"
    return f"""
<p style="font-size:13px;color:#556">Burrows Δ to the 18 nearest reference chunks (any test paper). Lower = nearer in stopword space.</p>
<div class="heatmap-wrap"><table class="heatmap">{header}{''.join(rows_html)}</table></div>"""


def render_full_report() -> str:
    analysis = load_analysis()
    body = (
        executive_summary(analysis)
        + method_block(analysis)
        + inference_note_block(analysis)
        + corpus_health_section(analysis)
        + quadrant_overview()
        + summary_stats(analysis)
        + '<h2 class="sec">Master comparison (with inference)</h2>'
        + master_table(analysis)
        + confusion_section(analysis)
        + benchmark_section(analysis)
        + corpus_section()
        + '<h2 class="sec">Distance heatmap</h2>'
        + heatmap_section(analysis)
        + '<h2 class="sec">Per-paper profiles</h2>'
        + "".join(paper_section(p, analysis) for p in PAPERS)
        + limitations_block()
    )
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JAMS quadrant — statistical stylometric report</title>
<script>
MathJax = {{ tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }} }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
<style>{CSS}</style></head><body>
<header>
<h1>JAMS content×style quadrant — statistical stylometric report</h1>
<p>Expert v4 style labels vs stylo Burrows-Δ stopword classification. Balanced 17,948-chunk training corpus (860 arXiv sources).
Includes corpus health diagnostics, Wilson/bootstrap CIs, binomial tests, margin distributions, confusion tables, and ablation benchmarks.</p>
</header>
<div class="wrap">{body}</div>
</body></html>"""


def main() -> None:
    if not ANALYSIS_PATH.exists():
        raise SystemExit(f"Missing {ANALYSIS_PATH}; run Rscript scripts/export_stylo_analysis.R first")
    report = render_full_report()
    out_downloads = DOWNLOADS / "jams_quadrant_full_report.html"
    out_local = OUT / "jams_quadrant_full_report.html"
    out_downloads.write_text(report, encoding="utf-8")
    out_local.write_text(report, encoding="utf-8")
    print(f"Wrote {out_downloads}")
    print(f"Wrote {out_local}")
    import subprocess
    subprocess.run(["open", str(out_downloads)], check=False)


if __name__ == "__main__":
    main()
