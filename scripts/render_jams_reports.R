#!/usr/bin/env Rscript
# Render cross_view, within_view, and full_report HTML from stylo JSON (R engine).
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
root <- if (length(file_arg)) {
  normalizePath(file.path(dirname(sub("^--file=", "", file_arg)), ".."))
} else {
  getwd()
}
setwd(root)
`%||%` <- function(a, b) if (is.null(a) || length(a) == 0 || (length(a) == 1 && is.na(a))) b else a
source("R/jams_metadata.R")
source("R/html_helpers.R")
source("R/render_full_report.R")
library(jsonlite)

out_dir <- "output/jams_quadrant"
downloads_dir <- path.expand("~/Downloads")

classify_pair <- function(left, right) {
  ds <- right$style_axis - left$style_axis
  dc <- right$content_axis - left$content_axis
  if (abs(dc) < 0.35 && abs(ds) >= 0.55) return("Style-only")
  if (abs(ds) < 0.35 && abs(dc) >= 0.55) return("Content-only")
  if (ds * dc < 0) return("Conflict")
  "Aligned"
}

ratings_block <- function(p) {
  paste0(
    '<div class="rlabel">holistic geometric↔algebraic</div>', bar_html(p$holistic),
    '<div class="rlabel">style axis</div>', bar_html(p$style_axis),
    '<div class="rlabel">content axis</div>', bar_html(p$content_axis),
    '<div class="rlabel">style features</div>', chips_html(p$style_on, "style"),
    '<div class="rlabel">object categories</div>', chips_html(p$objects, "object")
  )
}

excerpt_col <- function(label, p, roll = NULL) {
  stylo_line <- if (!is.null(roll) && length(roll) > 0) {
    sprintf(
      '<div class="rlabel">stylo rolling (Burrows Delta)</div><div class="mstat">geometric %.1f%% · algebraic %.1f%% (%d slices)</div>',
      100 * roll$share_geometric, 100 * roll$share_algebraic, roll$n_slices
    )
  } else ""
  paste0(
    '<div class="col"><div class="sidehdr">', html_escape(label), '</div>',
    '<div class="para">', tex_para(p$excerpt_tex), '</div>', ratings_block(p), stylo_line, '</div>'
  )
}

pair_card <- function(pid, left, right, stylo) {
  ds <- right$style_axis - left$style_axis
  dc <- right$content_axis - left$content_axis
  dh <- right$holistic - left$holistic
  afc <- if (abs(ds) >= abs(dc) && abs(ds) > 0.35) {
    if (ds < 0) "RIGHT" else "LEFT"
  } else {
    if (dc < 0) "RIGHT" else "LEFT"
  }
  l_roll <- stylo$rolling[[STEM_TO_ROLLING[[left$file_stem]]]] %||% list()
  r_roll <- stylo$rolling[[STEM_TO_ROLLING[[right$file_stem]]]] %||% list()
  paste0(
    '<div class="card"><div class="phdr"><span class="pid">', pid, '</span> ',
    html_escape(paste(left$authors, "|", right$authors)), ' · ',
    html_escape(paste(left$quadrant, "vs", right$quadrant)),
    sprintf('<span class="mstat">Δstyle %+.2f · Δcontent %+.2f · 2AFC: %s more geometric</span></div>',
            ds, dc, afc),
    '<div class="cols">', excerpt_col("excerpt 1", left, l_roll),
    excerpt_col("excerpt 2", right, r_roll), '</div></div>'
  )
}

stylo_summary <- function(stylo) {
  expert <- EXPERT_STYLE_LABELS
  rows <- paste(vapply(JAMS_PAPERS, function(p) {
    stem <- STEM_TO_ROLLING[[p$file_stem]]
    roll <- stylo$rolling[[stem]]
    rp <- roll_pred(roll)
    idx <- which(stylo$full_papers$files == paste0(stem, ".txt"))
    wp <- if (length(idx)) stylo$full_papers$predicted_style[[idx[1]]] else "?"
    sprintf(
      "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%.1f%% / %.1f%%</td><td>%s</td><td>%s</td></tr>",
      html_escape(p$authors), p$style_label, rp, wp,
      100 * roll$share_geometric, 100 * roll$share_algebraic,
      if (rp == p$style_label) "\u2713" else "\u2717",
      if (wp == p$style_label) "\u2713" else "\u2717"
    )
  }, character(1)), collapse = "")
  sa <- stylo$style_accuracy
  paste0(
    '<div class="summarybox"><h2 style="margin-top:0">Stylo classification (R engine)</h2>',
    sprintf("<p>Style accuracy: rolling <b>%s/4</b> · whole-paper <b>%s/4</b></p>",
            sa$rolling_majority, sa$whole_paper),
    '<table class="data"><tr><th>Paper</th><th>Expert</th><th>Rolling</th><th>Whole</th><th>Geo/Alg</th><th>Roll</th><th>Whole</th></tr>',
    rows, "</table></div>"
  )
}

within_card <- function(p, stylo) {
  stem <- STEM_TO_ROLLING[[p$file_stem]]
  roll <- stylo$rolling[[stem]]
  pred <- roll_pred(roll)
  match_txt <- if (pred == p$style_label) "matches" else "conflicts with"
  paste0(
    '<div class="card"><div class="phdr">', p$pid, " ", html_escape(p$authors),
    sprintf(' · stylo rolling <b>%s</b> (%s expert style)</div>', pred, match_txt),
    '<div class="cols">', excerpt_col("holdout excerpt", p, roll), '</div></div>'
  )
}

render_cross_within <- function() {
  stylo <- fromJSON(file.path(out_dir, "stylo_results.json"), simplifyVector = FALSE)
  pairs <- list()
  n <- length(JAMS_PAPERS)
  for (i in seq_len(n - 1)) {
    for (j in (i + 1):n) {
      pairs[[length(pairs) + 1]] <- list(JAMS_PAPERS[[i]], JAMS_PAPERS[[j]])
    }
  }
  sections <- list(Aligned = character(), Conflict = character(), `Content-only` = character(), `Style-only` = character())
  for (idx in seq_along(pairs)) {
    left <- pairs[[idx]][[1]]
    right <- pairs[[idx]][[2]]
    cat <- classify_pair(left, right)
    sections[[cat]] <- c(sections[[cat]], pair_card(sprintf("X%02d", idx), left, right, stylo))
  }
  body <- stylo_summary(stylo)
  for (nm in names(sections)) {
    if (length(sections[[nm]])) body <- paste0(body, '<h2 class="bg">', nm, "</h2>", paste(sections[[nm]], collapse = ""))
  }
  cross <- page_shell(
    "JAMS quadrant — cross-paper view (R/stylo)",
    "Expert v4 ratings + stylo rolling stopword classification.",
    body
  )
  within_body <- stylo_summary(stylo)
  for (p in JAMS_PAPERS) within_body <- paste0(within_body, within_card(p, stylo))
  within <- page_shell(
    "JAMS quadrant — within-paper view (R/stylo)",
    "Single-excerpt expert coding with stylo rolling on full PDF text.",
    within_body
  )
  write_html(file.path(downloads_dir, "jams_quadrant_cross_view.html"), cross)
  write_html(file.path(out_dir, "jams_quadrant_cross_view.html"), cross)
  write_html(file.path(downloads_dir, "jams_quadrant_within_view.html"), within)
  write_html(file.path(out_dir, "jams_quadrant_within_view.html"), within)
}

render_cross_within()

analysis_path <- file.path(out_dir, "stylo_full_analysis.json")
if (!file.exists(analysis_path)) stop("Missing ", analysis_path, " — run export_stylo_analysis.R first")
analysis <- fromJSON(analysis_path, simplifyVector = FALSE)
render_full_report(analysis, out_dir, downloads_dir)

message("All HTML reports rendered by R.")
