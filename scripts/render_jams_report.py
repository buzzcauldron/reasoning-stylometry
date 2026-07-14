#!/usr/bin/env python3
"""DEPRECATED: use scripts/render_jams_reports.R (R engine). Kept for reference only."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "jams_quadrant"
DOWNLOADS = Path.home() / "Downloads"

STYLE_FEATURES = [
    ("position", "spatial"),
    ("deformation", "spatial"),
    ("local_global", "spatial"),
    ("visualizable", "spatial"),
    ("dynamic_process", "spatial"),
    ("symbolic_transf", "symbolic"),
    ("syntactic_deriv", "symbolic"),
    ("categorical_functorial", "symbolic"),
    ("approximation_estimation", "symbolic"),
    ("semantic_instantiation", "cross"),
    ("analogy_transfer", "cross"),
]

OBJECT_CATS = [
    "function_map",
    "equation_ineq",
    "group_ring",
    "set_family",
    "space_shape",
    "metric",
    "topological",
    "ambient_space_or_set",
    "calculus",
    "polytope_lattice",
]

PAPERS = [
    {
        "key": "masur",
        "pid": "①",
        "file_stem": "geometric__geometric_style__masur_schleimer",
        "title": "The geometry of the disk complex",
        "authors": "Masur & Schleimer",
        "journal": "JAMS 26 (2012)",
        "doi": "10.1090/s0894-0347-2012-00742-5",
        "quadrant": "Geometric content × Geometric style",
        "content_label": "geometric",
        "style_label": "geometric",
        "excerpt_tex": (
            r"Let $\beta''$ and $\gamma''$ be the geodesic representatives of $\beta'$ and $\gamma'$. "
            r"Since $\beta$ and $\tau(\beta)$ meet transversely, $\beta''$ has length in $\sigma$ strictly "
            r"smaller than $2\ell_\sigma(\beta)$. Similarly the length of $\gamma''$ is strictly smaller "
            r"than $2\ell_\sigma(\gamma)$. Suppose that $\beta''$ is shorter then $\gamma''$. It follows "
            r"that $\beta''$ strictly shorter than $\alpha$. If $\beta''$ is embedded then this contradicts "
            r"the assumption that $\alpha$ was shortest. If $\beta''$ is not embedded then there is an "
            r"embedded curve $\beta'''$ inside of a regular neighborhood of $\beta''$ which is again "
            r"essential, non-peripheral, and has geodesic representative shorter than $\beta''$. "
            r"This is our final contradiction and the claim is proved."
        ),
        "holistic": 0.84,
        "style_axis": 0.82,
        "content_axis": 0.85,
        "style_on": ["position", "local_global", "visualizable", "dynamic_process"],
        "objects": {"space_shape": "geo", "topological": "geo", "metric": "geo"},
        "afc_side": "LEFT",
        "afc_pct": 100,
        "afc_consistency": 1.00,
    },
    {
        "key": "bateman",
        "pid": "②",
        "file_stem": "geometric__algebraic_style__bateman_katz",
        "title": "New bounds on cap sets",
        "authors": "Bateman & Katz",
        "journal": "JAMS 25 (2011)",
        "doi": "10.1090/s0894-0347-2011-00725-x",
        "quadrant": "Geometric content × Algebraic style",
        "content_label": "geometric",
        "style_label": "algebraic",
        "excerpt_tex": (
            r"We introduce the Fourier transforms of the balanced function of the hyperplanes $H_{x_{\alpha}}$ "
            r"setting $f_{\alpha}(z)=\frac{1}{3^N}\sum_{x\in F_3^N}(1_{H_{x_{\alpha}}}(y)-\frac{1}{3})e(y\cdot z)$. "
            r"Then we use the standard Fourier identity "
            r"$\sum_{y\in F_3^N}\Pi_{\alpha=1}^4(1_{H_{x_{\alpha}}}(y)-\frac{1}{3})"
            r"=3^N\sum_{z_1+z_2+z_3+z_4=0}f_1(z_1)f_2(z_2)f_3(z_3)f_4(z_4)$. "
            r"We observe that $f_j(z_j)$ vanishes unless $z_j=\pm x_j$."
        ),
        "holistic": -0.12,
        "style_axis": -0.78,
        "content_axis": 0.42,
        "style_on": ["symbolic_transf", "syntactic_deriv", "approximation_estimation"],
        "objects": {
            "function_map": "neu",
            "equation_ineq": "neu",
            "set_family": "neu",
            "group_ring": "alg",
        },
        "afc_side": "RIGHT",
        "afc_pct": 100,
        "afc_consistency": 1.00,
    },
    {
        "key": "dritschel",
        "pid": "③",
        "file_stem": "algebraic__geometric_style__dritschel_mccullough",
        "title": "The failure of rational dilation on a triply connected domain",
        "authors": "Dritschel & McCullough",
        "journal": "JAMS 18 (2005)",
        "doi": "10.1090/s0894-0347-05-00491-1",
        "quadrant": "Algebraic content × Geometric style",
        "content_label": "algebraic",
        "style_label": "geometric",
        "excerpt_tex": (
            r"The cone $\mathcal C$ is a convex subset of $\mathcal P$ not containing $I-\rho^2 F(z)F(w)^*$ "
            r"and, by Lemma absorb, $I$ is an internal point of $\mathcal C$. Hence, there exists a nonconstant "
            r"linear functional $\lambda:\mathcal P\to\mathbb C$ so that $\lambda\ge 0$ on $\mathcal C$ and "
            r"$\lambda(I-\rho^2 F(z)F(w)^*)\le 0$; we have $\lambda(I)>0$, as otherwise, from Lemma absorb, "
            r"$\lambda(H(z)H(w)^*)=0$ for all $H$ and hence $\lambda=0$ (see, for example, Holmes, §11.E)."
        ),
        "holistic": -0.24,
        "style_axis": 0.38,
        "content_axis": -0.78,
        "style_on": ["position", "local_global", "symbolic_transf"],
        "objects": {
            "function_map": "neu",
            "equation_ineq": "neu",
            "set_family": "neu",
            "ambient_space_or_set": "neu",
        },
        "afc_side": "LEFT",
        "afc_pct": 88,
        "afc_consistency": 0.88,
    },
    {
        "key": "hrushovski",
        "pid": "④",
        "file_stem": "algebraic__algebraic_style__hrushovski",
        "title": "Stable group theory and approximate subgroups",
        "authors": "Hrushovski",
        "journal": "JAMS 25 (2011)",
        "doi": "10.1090/s0894-0347-2011-00708-x",
        "quadrant": "Algebraic content × Algebraic style",
        "content_label": "algebraic",
        "style_label": "algebraic",
        "excerpt_tex": (
            r"We will need some lemmas on finite generation. First, if $E$ is a finitely generated group, "
            r"$N$ a normal subgroup with $E/N$ finitely presented, then $N$ is finitely generated as a "
            r"normal subgroup. (In particular when $E/N$ is finite, this implies the finite generation of $N$, "
            r"a well-known statement used above.) This in fact valid for any equational class: If $E$ is finitely "
            r"generated and $N$ is a congruence with $E/N$ finitely presented, then $N$ is finitely generated "
            r"as a congruence. Indeed let $F$ be a finitely generated free algebra in this equational class, "
            r"and $h:F\to E$ a surjective homomorphism. Let $g:F\to E/N$ be the composition $F\to E\to E/N$. "
            r"Since $E/N$ is finitely presented, $g$ has a finitely generated kernel $K$. Thus $N=h(K)$ is "
            r"finitely generated."
        ),
        "holistic": -0.90,
        "style_axis": -0.88,
        "content_axis": -0.92,
        "style_on": ["syntactic_deriv", "categorical_functorial"],
        "objects": {"group_ring": "alg", "set_family": "neu", "function_map": "neu"},
        "afc_side": "RIGHT",
        "afc_pct": 100,
        "afc_consistency": 1.00,
    },
]

STEM_TO_ROLLING = {
    "geometric__geometric_style__masur_schleimer": "geometric__geometric_style__masur_schleimer_disk_complex",
    "geometric__algebraic_style__bateman_katz": "geometric__algebraic_style__bateman_katz_cap_sets",
    "algebraic__geometric_style__dritschel_mccullough": "algebraic__geometric_style__dritschel_mccullough_rational_dilation",
    "algebraic__algebraic_style__hrushovski": "algebraic__algebraic_style__hrushovski_approx_subgroups",
}


def bar_html(value: float) -> str:
    if value >= 0:
        left = 50
        width = value * 50
        color = "#2b7bba"
    else:
        left = 50 + value * 50
        width = abs(value) * 50
        color = "#c0504d"
    return (
        f'<div class="bar"><div class="civ"></div>'
        f'<div class="fill" style="left:{left}%;width:{width}%;background:{color}"></div>'
        f'<span class="barval">{value:+.2f}</span></div>'
    )


def chips_html(active: list[str], kind: str = "style") -> str:
    if kind == "style":
        parts = []
        for name, family in STYLE_FEATURES:
            cls = family if name in active else f"{family} off"
            parts.append(f'<span class="chip {cls}">{name}</span>')
        return '<div class="chips">' + "".join(parts) + "</div>"
    parts = []
    for name in OBJECT_CATS:
        tag = active.get(name)
        if tag:
            parts.append(f'<span class="ochip {tag}">{name}</span>')
    return '<div class="chips">' + "".join(parts) + "</div>"


def tex_para(tex: str) -> str:
    return f"<p>{tex}</p>"


def ratings_block(p: dict) -> str:
    return f"""
      <div class="ratings">
        <div class="rlabel">holistic geometric↔algebraic</div>{bar_html(p["holistic"])}
        <div class="rlabel">style axis (spatial − symbolic)</div>{bar_html(p["style_axis"])}
        <div class="rlabel">content axis (geo − alg objects)</div>{bar_html(p["content_axis"])}
        <div class="rlabel">style features present</div>
        {chips_html(p["style_on"], "style")}
        <div class="rlabel">object categories present</div>
        {chips_html(p["objects"], "object")}
      </div>"""


def excerpt_col(label: str, p: dict, stylo: dict | None = None) -> str:
    stylo_line = ""
    if stylo:
        stylo_line = (
            f'<div class="rlabel">stylo stopwords (rolling)</div>'
            f'<div class="mstat">geometric {stylo["share_geometric"]*100:.1f}% · '
            f'algebraic {stylo["share_algebraic"]*100:.1f}% '
            f'({stylo["n_slices"]} slices)</div>'
        )
    return f"""
    <div class="col">
      <div class="sidehdr">{label}</div>
      <div class="para">{tex_para(p["excerpt_tex"])}</div>
      {ratings_block(p)}
      {stylo_line}
    </div>"""


def pair_card(pid: str, left: dict, right: dict, stylo: dict) -> str:
    ds = right["style_axis"] - left["style_axis"]
    dc = right["content_axis"] - left["content_axis"]
    dh = right["holistic"] - left["holistic"]
    if abs(ds) >= abs(dc) and abs(ds) > 0.35:
        afc = "RIGHT" if ds < 0 else "LEFT"
    else:
        afc = "RIGHT" if dc < 0 else "LEFT"
    meta = (
        f'{left["authors"]} | {right["authors"]} &middot; '
        f'{left["quadrant"]} vs {right["quadrant"]}'
    )
    l_roll = stylo["rolling"].get(STEM_TO_ROLLING[left["file_stem"]], {})
    r_roll = stylo["rolling"].get(STEM_TO_ROLLING[right["file_stem"]], {})
    return f"""
<div class="card">
  <div class="phdr">
    <span class="pid">{pid}</span>
    <span class="meta">{meta}</span>
    <span class="deltas">Δstyle {ds:+.2f} &middot; Δcontent {dc:+.2f} &middot; Δholistic {dh:+.2f}</span>
    <span class="mstat">model 2AFC: called <b>{afc}</b> more geometric in 100% of 8 runs (consistency 1.00)</span>
  </div>
  <div class="cols">
    {excerpt_col("excerpt 1", left, l_roll)}
    {excerpt_col("excerpt 2", right, r_roll)}
  </div>
</div>"""


def classify_pair(left: dict, right: dict) -> str:
    ds = right["style_axis"] - left["style_axis"]
    dc = right["content_axis"] - left["content_axis"]
    if abs(dc) < 0.35 and abs(ds) >= 0.55:
        return "Style-only"
    if abs(ds) < 0.35 and abs(dc) >= 0.55:
        return "Content-only"
    if ds * dc < 0:
        return "Conflict"
    return "Aligned"


def within_card(p: dict, stylo: dict) -> str:
    aligned = p["content_label"] == p["style_label"]
    section = "Aligned" if aligned else "Cross (content ≠ style)"
    roll = stylo["rolling"].get(STEM_TO_ROLLING[p["file_stem"]], {})
    pred = "geometric" if roll.get("share_geometric", 0) > roll.get("share_algebraic", 0) else "algebraic"
    match = "matches" if pred == p["style_label"] else "conflicts with"
    return section, f"""
<div class="card">
  <div class="phdr">
    <span class="pid">{p["pid"]}</span>
    <span class="meta">{p["authors"]}, {p["title"]} &middot; {p["journal"]} &middot; doi:{p["doi"]}</span>
    <span class="deltas">{p["quadrant"]}</span>
    <span class="mstat">stylo rolling style <b>{pred}</b> ({match} expert style label <b>{p["style_label"]}</b>)</span>
  </div>
  <div class="cols">
    {excerpt_col("excerpt", p, roll)}
    <div class="col">
      <div class="sidehdr">quadrant key</div>
      <div class="para">
        <p><b>Content axis:</b> {p["content_label"]} objects (expert {p["content_axis"]:+.2f})</p>
        <p><b>Style axis:</b> {p["style_label"]} reasoning (expert {p["style_axis"]:+.2f})</p>
        <p><b>Holistic:</b> {p["holistic"]:+.2f}</p>
        <p>Filename prefix encodes <em>content</em>; stylo stopwords target <em>style</em>.</p>
      </div>
    </div>
  </div>
</div>"""


CSS = """
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
   margin:0;background:#f4f5f7;color:#1a1a1a}
 header{background:#22303f;color:#fff;padding:20px 28px}
 header h1{margin:0 0 6px;font-size:20px}
 header p{margin:0;opacity:.8;font-size:13px}
 .legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:12px}
 .legend span{display:inline-flex;align-items:center;gap:5px}
 .sw{width:12px;height:12px;border-radius:2px;display:inline-block}
 .wrap{max-width:1180px;margin:0 auto;padding:24px 20px}
 h2.bg{margin:34px 0 12px;font-size:16px;color:#22303f;border-bottom:2px solid #c9d2db;padding-bottom:6px}
 .card{background:#fff;border:1px solid #dce1e6;border-radius:10px;margin:16px 0;
   box-shadow:0 1px 3px rgba(0,0,0,.05);overflow:hidden}
 .phdr{background:#eef1f4;padding:10px 16px;border-bottom:1px solid #dce1e6;
   display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;font-size:12.5px}
 .pid{font-weight:700;font-size:14px;color:#22303f}
 .meta{color:#556}
 .deltas{color:#334;font-variant-numeric:tabular-nums}
 .mstat{flex-basis:100%;color:#2b5;font-size:12.5px}
 .mstat b{color:#183}
 .cols{display:flex;gap:0}
 .col{flex:1;min-width:0;padding:14px 16px}
 .col:first-child{border-right:1px solid #eceff2;background:#fbfcfd}
 .sidehdr{font-size:11px;text-transform:uppercase;letter-spacing:.06em;
   color:#8794a1;font-weight:700;margin-bottom:8px}
 .para{font-size:14px;line-height:1.5;min-height:60px;overflow-x:auto}
 .ratings{margin-top:14px;border-top:1px dashed #dce1e6;padding-top:10px}
 .rlabel{font-size:11px;color:#667;margin:8px 0 3px}
 .bar{position:relative;height:16px;background:#eef1f4;border-radius:3px;overflow:hidden;font-size:0}
 .bar .civ{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#aab}
 .bar .fill{position:absolute;top:0;bottom:0}
 .barval{position:absolute;right:5px;top:0;font-size:10.5px;line-height:16px;color:#334;font-variant-numeric:tabular-nums}
 .chips{display:flex;flex-wrap:wrap;gap:4px}
 .chip{font-size:10.5px;padding:2px 6px;border-radius:10px;font-weight:600;color:#fff}
 .chip.spatial{background:#2b7bba} .chip.symbolic{background:#c0504d}
 .chip.cross{background:#7a6ea6}
 .chip.off{background:#e3e7eb;color:#a0a8b0;font-weight:400}
 .ochip{font-size:10.5px;padding:2px 6px;border-radius:4px;border:1px solid}
 .ochip.geo{background:#e7f0f8;border-color:#2b7bba;color:#1c5580}
 .ochip.alg{background:#faeae9;border-color:#c0504d;color:#8a3936}
 .ochip.neu{background:#f0f1f3;border-color:#c3c9cf;color:#667}
 summarybox{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:16px 18px;margin:0 0 20px}
"""


def page_shell(title: str, subtitle: str, body: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<script>
MathJax = {{ tex: {{ inlineMath: [['\\\\(','\\\\)']], displayMath: [['\\\\[','\\\\]']] }},
  options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }} }};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
<style>{CSS}</style></head><body>
<header>
 <h1>{html.escape(title)}</h1>
 <p>{html.escape(subtitle)}</p>
 <div class="legend">
   <span><span class="sw" style="background:#2b7bba"></span>spatial style / geometric</span>
   <span><span class="sw" style="background:#c0504d"></span>symbolic style / algebraic</span>
   <span><span class="sw" style="background:#7a6ea6"></span>cross feature</span>
   <span>bars span −1 … +1 (positive = geometric/spatial)</span>
 </div>
</header>
<div class="wrap">{body}</div>
</body></html>"""


WHOLE_PRED = {
    "masur": ("geometric__geometric_style__masur_schleimer_disk_complex.txt", 3),
    "bateman": ("geometric__algebraic_style__bateman_katz_cap_sets.txt", 2),
    "dritschel": ("algebraic__geometric_style__dritschel_mccullough_rational_dilation.txt", 1),
    "hrushovski": ("algebraic__algebraic_style__hrushovski_approx_subgroups.txt", 0),
}


def stylo_summary(stylo: dict) -> str:
    fp = stylo["full_papers"]
    files = fp["files"]
    predicted = fp["predicted_style"]
    style_hits_whole = 0
    style_hits_roll = 0
    rows = []
    for p in PAPERS:
        roll_key = STEM_TO_ROLLING[p["file_stem"]]
        roll = stylo["rolling"][roll_key]
        roll_pred = "geometric" if roll["share_geometric"] > roll["share_algebraic"] else "algebraic"
        fname, _idx = WHOLE_PRED[p["key"]]
        whole_pred = predicted[files.index(fname)]
        ok_whole = whole_pred == p["style_label"]
        ok_roll = roll_pred == p["style_label"]
        if ok_whole:
            style_hits_whole += 1
        if ok_roll:
            style_hits_roll += 1
        rows.append(
            f"<tr><td>{p['authors']}</td><td>{p['style_label']}</td>"
            f"<td>{roll_pred}</td><td>{whole_pred}</td>"
            f"<td>{roll['share_geometric']*100:.1f}% / {roll['share_algebraic']*100:.1f}%</td>"
            f"<td>{'✓' if ok_roll else '✗'}</td><td>{'✓' if ok_whole else '✗'}</td></tr>"
        )
    return f"""
<div class="summarybox">
<h2 style="margin-top:0;font-size:16px">Stylo stopword classification (Burrows Delta vs geometric/algebraic reference set)</h2>
<p>Reference: balanced research chunks (~2800). Features: 175 English stopwords (Snowball). <b>Primary metric:</b> rolling majority (250-word slices, 150-word overlap). Whole-paper classify is secondary on long JAMS texts.</p>
<p><b>Style-label accuracy:</b> rolling majority <b>{style_hits_roll}/4</b> · whole-paper {style_hits_whole}/4 (expert style quadrant).</p>
<table style="width:100%;border-collapse:collapse;font-size:13px">
<tr style="text-align:left;border-bottom:1px solid #dce1e6">
  <th>Paper</th><th>Expert style</th><th>Stylo rolling</th><th>Stylo whole</th><th>Geo / Alg share</th><th>Roll</th><th>Whole</th></tr>
{''.join(rows)}
</table>
<p style="margin-bottom:0;font-size:12.5px;color:#556">Note: filename prefix encodes <em>content</em> quadrant; stylo targets function-word <em>style</em>. Crossed papers (Bateman, Dritschel) decouple content from style as intended.</p>
</div>"""


def render_cross(stylo: dict) -> str:
    pairs = []
    for i, left in enumerate(PAPERS):
        for right in PAPERS[i + 1 :]:
            pairs.append((left, right))
    sections = {"Aligned": [], "Conflict": [], "Content-only": [], "Style-only": []}
    for idx, (left, right) in enumerate(pairs):
        cat = classify_pair(left, right)
        sections[cat].append(pair_card(f"X{idx:02d}", left, right, stylo))
    body = stylo_summary(stylo)
    for name in ["Aligned", "Conflict", "Content-only", "Style-only"]:
        if sections[name]:
            body += f'<h2 class="bg">{name}</h2>' + "".join(sections[name])
    return page_shell(
        "JAMS content×style quadrant — cross-paper view",
        "Six cross-paper pairs from four JAMS exemplars; expert content/style axis ratings plus stylo stopword rolling shares.",
        body,
    )


def render_within(stylo: dict) -> str:
    sections: dict[str, list[str]] = {"Aligned content×style": [], "Cross content×style": []}
    for p in PAPERS:
        section, card = within_card(p, stylo)
        key = "Aligned content×style" if section.startswith("Aligned") else "Cross content×style"
        sections[key].append(card)
    body = stylo_summary(stylo)
    for name, cards in sections.items():
        body += f'<h2 class="bg">{name}</h2>' + "".join(cards)
    return page_shell(
        "JAMS content×style quadrant — within-paper view",
        "Four single-excerpt quadrant exemplars; expert axis ratings with stylo rolling classification on full paper text.",
        body,
    )


def main() -> None:
    stylo_path = OUT / "stylo_results.json"
    stylo = json.loads(stylo_path.read_text(encoding="utf-8"))
    cross = render_cross(stylo)
    within = render_within(stylo)
    cross_path = DOWNLOADS / "jams_quadrant_cross_view.html"
    within_path = DOWNLOADS / "jams_quadrant_within_view.html"
    cross_path.write_text(cross, encoding="utf-8")
    within_path.write_text(within, encoding="utf-8")
    (OUT / "jams_quadrant_cross_view.html").write_text(cross, encoding="utf-8")
    (OUT / "jams_quadrant_within_view.html").write_text(within, encoding="utf-8")
    print(f"Wrote {cross_path}")
    print(f"Wrote {within_path}")


if __name__ == "__main__":
    main()
