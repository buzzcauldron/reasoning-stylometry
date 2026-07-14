# Full statistical HTML report from stylo_full_analysis.json (R engine).

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || (length(a) == 1 && is.na(a))) b else a

bar_html_label <- function(label, value) {
  paste0('<div class="rlabel">', html_escape(label), "</div>", bar_html(value))
}

render_full_report <- function(analysis, out_dir, downloads_dir) {
  m <- analysis$meta
  ch <- analysis$corpus_health
  loo <- ch$loo_sample
  sa <- analysis$style_accuracy
  manifest <- m$manifest

  exec <- sprintf('
<div class="prose">
<h2 style="margin-top:0;font-size:16px;color:#22303f">Executive summary (statistical)</h2>
<p>Four JAMS papers: expert v4 style labels vs <b>stylo %s</b> on full PDF text.
Training: %s balanced chunks (%s arXiv sources).</p>
<p><b>Corpus health (stylo::crossv):</b> L1=%.4f; LOO=%.1f%% [Wilson %.1f–%.1f%%]; inter/intra ratio=%.3f.</p>
<p><b>Holdout:</b> rolling %s/4 · whole-paper %s/4.</p>
</div>',
    html_escape(m$method), format(m$reference_n, big.mark = ","),
    manifest$n_sources %||% "?",
    ch$class_separability_l1, loo$accuracy_pct,
    100 * loo$wilson_ci_low, 100 * loo$wilson_ci_high, ch$separation_ratio,
    sa$rolling_majority %||% "?", sa$whole_paper %||% "?")

  health_badges <- paste(vapply(ch$verdict, function(v) {
    cls <- if (grepl("CRITICAL", v)) "badge-crit" else if (grepl("WEAK", v)) "badge-warn" else "badge-warn"
    sprintf('<div style="margin:4px 0"><span class="%s">%s</span></div>', cls, html_escape(v))
  }, character(1)), collapse = "")

  health <- sprintf('
<h2 class="sec">Corpus health &amp; separability (stylo)</h2>
<div class="prose health-warn">%s</div>
<div class="grid4">
  <div class="stat"><div class="lbl">Centroid L1</div><div class="val">%.4f</div></div>
  <div class="stat"><div class="lbl">stylo crossv LOO</div><div class="val">%.1f%%</div>
    <div class="note">n=%s; Wilson [%.1f%%, %.1f%%]</div></div>
  <div class="stat"><div class="lbl">Inter/intra ratio</div><div class="val">%.3f</div></div>
  <div class="stat"><div class="lbl">Engine</div><div class="val">stylo</div>
    <div class="note">v%s · %d MFW</div></div>
</div>',
    health_badges, ch$class_separability_l1, loo$accuracy_pct, loo$n_sampled,
    100 * loo$wilson_ci_low, 100 * loo$wilson_ci_high, ch$separation_ratio,
    m$stylo_version, m$n_features_used)

  master_rows <- paste(vapply(JAMS_PAPERS, function(p) {
    stem <- paper_stem_for(p)
    pa <- analysis$full_papers$papers[[stem]]
    ro <- analysis$rolling[[stem]]
    rp <- roll_pred(ro)
    rw <- roll_pred(ro, weighted = TRUE)
    sprintf(
      "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%.1f%%</td><td class=\"ci\">[%.1f%%, %.1f%%]</td><td class=\"mono\">%s</td><td>%d</td></tr>",
      html_escape(p$authors), tag_html(p$style_label), tag_html(rp, rp == p$style_label),
      tag_html(rw, rw == p$style_label), tag_html(pa$predicted, pa$predicted == p$style_label),
      100 * ro$share_geometric, 100 * ro$geo_wilson_ci_low, 100 * ro$geo_wilson_ci_high,
      ro$binomial_p_vs_half, ro$n_slices
    )
  }, character(1)), collapse = "")

  master <- paste0('
<h2 class="sec">Master comparison</h2>
<table class="data"><tr><th>Paper</th><th>Expert</th><th>Rolling</th><th>Conf-wtd</th><th>Whole</th>
<th>Geo%</th><th>Wilson 95%</th><th>p vs &frac12;</th><th>Slices</th></tr>', master_rows, "</table>")

  paper_cards <- paste(vapply(JAMS_PAPERS, function(p) {
    stem <- paper_stem_for(p)
    pa <- analysis$full_papers$papers[[stem]]
    ro <- analysis$rolling[[stem]]
    png <- file.path(out_dir, paste0("rolling_", stem, ".png"))
    img <- if (file.exists(png)) sprintf('<img class="imgroll" src="%s">', img_data_uri(png)) else ""
    rp <- roll_pred(ro)
    sprintf('
<div class="card"><div class="card-hdr"><h3>%s %s</h3><p>%s</p></div>
<div class="card-body"><div class="cols2">
<div><div class="excerpt">%s</div>%s%s%s</div>
<div><p>Expert: %s · Rolling: %s · Geo %.1f%% <span class="ci">Wilson [%.1f%%, %.1f%%]</span></p>
<p class="mono">p(H0)= %s · Cohen h=%+.3f · eff. n≈%s</p>%s</div>
</div></div></div>',
      p$pid, html_escape(p$authors), html_escape(p$quadrant),
      tex_para(p$excerpt_tex), bar_html_label("style axis", p$style_axis),
      bar_html_label("content axis", p$content_axis), chips_html(p$style_on, "style"),
      tag_html(p$style_label), tag_html(rp, rp == p$style_label),
      100 * ro$share_geometric, 100 * ro$geo_wilson_ci_low, 100 * ro$geo_wilson_ci_high,
      ro$binomial_p_vs_half, ro$cohens_h_vs_half, ro$effective_independent_slices %||% "?",
      img)
  }, character(1)), collapse = "")

  body <- paste0(exec, health, master, '<h2 class="sec">Per-paper profiles</h2>', paper_cards)

  html <- paste0(
    "<!doctype html><html><head><meta charset=\"utf-8\">",
    "<script>MathJax={tex:{inlineMath:[[\"\\\\(\",\"\\\\)\"]],displayMath:[[\"\\\\[\",\"\\\\]\"]]}};</script>",
    "<script src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\" async></script>",
    "<style>", FULL_REPORT_CSS, "</style></head><body>",
    "<header><h1>JAMS quadrant — statistical stylometric report (R/stylo)</h1>",
    "<p>Generated by stylo ", html_escape(m$stylo_version %||% ""), " in R. ",
    "All classification, rolling, crossv, and distances from stylo::classify / rolling.classify / crossv.</p></header>",
    "<div class=\"wrap\">", body, "</div></body></html>"
  )

  write_html(file.path(downloads_dir, "jams_quadrant_full_report.html"), html)
  write_html(file.path(out_dir, "jams_quadrant_full_report.html"), html)
}
