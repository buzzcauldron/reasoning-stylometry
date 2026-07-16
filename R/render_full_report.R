# Full statistical HTML report from stylo_full_analysis.json (R engine).
# Reports BOTH independent axes (content = topic, style = reasoning
# presentation) plus their joint quadrant match against expert v4 labels.

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || (length(a) == 1 && is.na(a))) b else a

bar_html_label <- function(label, value) {
  paste0('<div class="rlabel">', html_escape(label), "</div>", bar_html(value))
}

discriminators_table <- function(top_discriminators) {
  if (is.null(top_discriminators) || length(top_discriminators) == 0) return("")
  rows <- paste(vapply(top_discriminators, function(w) {
    sprintf(
      "<tr><td class=\"mono\">%s</td><td>%.4f</td><td>%.4f</td><td>%+.4f</td></tr>",
      html_escape(w$word), w$geo_centroid, w$alg_centroid, w$geo_minus_alg
    )
  }, character(1)), collapse = "")
  paste0(
    '<table class="data" style="margin-top:10px"><tr><th>Word</th><th>Geo freq</th><th>Alg freq</th><th>Geo &minus; Alg</th></tr>',
    rows, "</table>"
  )
}

axis_health_block <- function(axis_title, ch, m_n_features) {
  loo <- ch$loo_sample
  badges <- paste(vapply(ch$verdict, function(v) {
    cls <- if (grepl("CRITICAL", v)) "badge-crit" else if (grepl("WEAK", v)) "badge-warn" else "badge-warn"
    sprintf('<div style="margin:4px 0"><span class="%s">%s</span></div>', cls, html_escape(v))
  }, character(1)), collapse = "")
  sprintf('
<h3 class="sub">%s</h3>
<div class="prose health-warn">%s</div>
<div class="grid4">
  <div class="stat"><div class="lbl">Centroid L1</div><div class="val">%.4f</div></div>
  <div class="stat"><div class="lbl">stylo crossv LOO</div><div class="val">%.1f%%</div>
    <div class="note">n=%s; Wilson [%.1f%%, %.1f%%]</div></div>
  <div class="stat"><div class="lbl">Inter/intra ratio</div><div class="val">%.3f</div></div>
  <div class="stat"><div class="lbl">Features (MFW)</div><div class="val">%d</div></div>
</div>
<h4 style="margin:14px 0 6px;font-size:12.5px;color:#556">Top discriminating stopwords (training centroid frequency)</h4>
%s',
    html_escape(axis_title), badges, ch$class_separability_l1, loo$accuracy_pct, loo$n_sampled,
    100 * loo$wilson_ci_low, 100 * loo$wilson_ci_high, ch$separation_ratio, m_n_features,
    discriminators_table(ch$top_discriminators))
}

render_full_report <- function(analysis, out_dir, downloads_dir) {
  m <- analysis$meta
  ca <- analysis$content
  sa <- analysis$style
  manifest <- m$manifest
  quadrant <- analysis$quadrant

  exec <- sprintf('
<div class="prose">
<h2 style="margin-top:0;font-size:16px;color:#22303f">Executive summary (statistical)</h2>
<p>Four JAMS papers: expert v4 content/style labels vs <b>stylo %s</b> on full PDF text,
scored on two independently-labeled axes (content = subject topic, style = reasoning
presentation). Content and style are labeled independently per training chunk
(<span class="mono">scripts/retag_content_style.py</span>); see
<span class="mono">corpus_classify/CORPUS.md</span> and
<span class="mono">output/corpus_diagnosis_stylo.json</span> for the independence check.</p>
<p><b>Content holdout:</b> rolling %s/4 &middot; whole-paper %s/4.
<b>Style holdout:</b> rolling %s/4 &middot; whole-paper %s/4.
<b>Joint quadrant (both axes correct):</b> %s/4.</p>
<p style="font-size:12.5px;color:#667">The expert v4 labels below are contested holistic judgments, not
ground truth &mdash; each carries a 2AFC agreement rate (<span class="mono">afc_consistency</span>) and an
axis magnitude (how far from 0, i.e. how confidently rated). Dritschel is the only paper below 100%%
agreement (88%%) and has the weakest style-axis magnitude (+0.38) of the four &mdash; a "miss" there
carries less weight than a miss on a unanimous, high-magnitude paper like Hrushovski (-0.88).</p>
</div>',
    html_escape(m$method),
    analysis$content_accuracy$rolling_majority %||% "?", analysis$content_accuracy$whole_paper %||% "?",
    analysis$style_accuracy$rolling_majority %||% "?", analysis$style_accuracy$whole_paper %||% "?",
    analysis$quadrant_accuracy %||% "?")

  health <- paste0(
    '<h2 class="sec">Corpus health &amp; separability (stylo)</h2>',
    axis_health_block("Content axis (topic)", ca$corpus_health, ca$n_features_used),
    axis_health_block("Style axis (reasoning presentation)", sa$corpus_health, sa$n_features_used)
  )

  master_rows <- paste(vapply(JAMS_PAPERS, function(p) {
    stem <- paper_stem_for(p)
    pa_c <- ca$full_papers$papers[[stem]]
    pa_s <- sa$full_papers$papers[[stem]]
    ro_c <- ca$rolling[[stem]]
    ro_s <- sa$rolling[[stem]]
    rp_c <- roll_pred(ro_c)
    rp_s <- roll_pred(ro_s)
    q <- quadrant[[stem]]
    sprintf(
      paste0(
        "<tr><td>%s</td>",
        "<td>%s</td><td>%s</td><td>%s</td>",
        "<td>%s</td><td>%s</td><td>%s</td>",
        "<td>%s</td><td class=\"ci\">%.0f%% agree &middot; axis %+.2f/%+.2f</td></tr>"
      ),
      html_escape(p$authors),
      tag_html(p$content_label), tag_html(rp_c, rp_c == p$content_label), tag_html(pa_c$predicted, pa_c$predicted == p$content_label),
      tag_html(p$style_label), tag_html(rp_s, rp_s == p$style_label), tag_html(pa_s$predicted, pa_s$predicted == p$style_label),
      if (isTRUE(q$quadrant_match)) '<span class="tag ok">✓</span>' else '<span class="tag no">✗</span>',
      100 * p$afc_consistency, p$content_axis, p$style_axis
    )
  }, character(1)), collapse = "")

  master <- paste0('
<h2 class="sec">Master comparison</h2>
<table class="data"><tr><th>Paper</th>
<th>Expert content</th><th>Rolling content</th><th>Whole content</th>
<th>Expert style</th><th>Rolling style</th><th>Whole style</th>
<th>Quadrant</th><th>Label confidence</th></tr>', master_rows, "</table>")

  paper_cards <- paste(vapply(JAMS_PAPERS, function(p) {
    stem <- paper_stem_for(p)
    ro_c <- ca$rolling[[stem]]
    ro_s <- sa$rolling[[stem]]
    png_c <- file.path(out_dir, paste0("rolling_content_", stem, ".png"))
    png_s <- file.path(out_dir, paste0("rolling_style_", stem, ".png"))
    img_c <- if (file.exists(png_c)) sprintf('<img class="imgroll" src="%s">', img_data_uri(png_c)) else ""
    img_s <- if (file.exists(png_s)) sprintf('<img class="imgroll" src="%s">', img_data_uri(png_s)) else ""
    rp_c <- roll_pred(ro_c)
    rp_s <- roll_pred(ro_s)
    sprintf('
<div class="card"><div class="card-hdr"><h3>%s %s</h3><p>%s</p></div>
<div class="card-body"><div class="cols2">
<div><div class="excerpt">%s</div>%s%s%s</div>
<div>
<p><b>Content</b> — Expert: %s &middot; Rolling: %s &middot; Geo %.1f%% <span class="ci">Wilson [%.1f%%, %.1f%%]</span></p>
<p class="mono">p(H0)= %s &middot; Cohen h=%+.3f</p>%s
<p style="margin-top:12px"><b>Style</b> — Expert: %s &middot; Rolling: %s &middot; Geo %.1f%% <span class="ci">Wilson [%.1f%%, %.1f%%]</span></p>
<p class="mono">p(H0)= %s &middot; Cohen h=%+.3f</p>%s
</div>
</div></div></div>',
      p$pid, html_escape(p$authors), html_escape(p$quadrant),
      tex_para(p$excerpt_tex), bar_html_label("style axis (expert)", p$style_axis),
      bar_html_label("content axis (expert)", p$content_axis), chips_html(p$style_on, "style"),
      tag_html(p$content_label), tag_html(rp_c, rp_c == p$content_label),
      100 * ro_c$share_geometric, 100 * ro_c$geo_wilson_ci_low, 100 * ro_c$geo_wilson_ci_high,
      ro_c$binomial_p_vs_half, ro_c$cohens_h_vs_half, img_c,
      tag_html(p$style_label), tag_html(rp_s, rp_s == p$style_label),
      100 * ro_s$share_geometric, 100 * ro_s$geo_wilson_ci_low, 100 * ro_s$geo_wilson_ci_high,
      ro_s$binomial_p_vs_half, ro_s$cohens_h_vs_half, img_s)
  }, character(1)), collapse = "")

  body <- paste0(exec, health, master, '<h2 class="sec">Per-paper profiles</h2>', paper_cards)

  html <- paste0(
    "<!doctype html><html><head><meta charset=\"utf-8\">",
    "<script>MathJax={tex:{inlineMath:[[\"\\\\(\",\"\\\\)\"]],displayMath:[[\"\\\\[\",\"\\\\]\"]]}};</script>",
    "<script src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\" async></script>",
    "<style>", FULL_REPORT_CSS, "</style></head><body>",
    "<header><h1>JAMS quadrant — statistical stylometric report (R/stylo)</h1>",
    "<p>Generated by stylo ", html_escape(m$stylo_version %||% ""), " in R. ",
    "Content and style are trained and predicted as two independent classifiers ",
    "(see corpus_classify/CORPUS.md); all classification, rolling, crossv, and ",
    "distances from stylo::classify / rolling.classify / crossv.</p></header>",
    "<div class=\"wrap\">", body, "</div></body></html>"
  )

  write_html(file.path(downloads_dir, "jams_quadrant_full_report.html"), html)
  write_html(file.path(out_dir, "jams_quadrant_full_report.html"), html)
}
