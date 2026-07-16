#!/usr/bin/env Rscript
# Master stylo analysis pipeline — all measurement and reporting in R.
root <- Sys.getenv("REASONING_STYLOMETRY_ROOT", getwd())
if (!file.exists(file.path(root, "scripts/run_jams_quadrant.R"))) {
  root <- normalizePath(file.path(dirname(sys.frame(1)$ofile %||% "."), ".."))
}
setwd(root)
Sys.setenv(REASONING_STYLOMETRY_ROOT = root)

steps <- c(
  "extract_jams_pdfs.R",
  "make_style_leading_targets.R",
  "run_jams_quadrant.R",
  "diagnose_corpus.R",
  "export_stylo_analysis.R",
  "render_jams_reports.R"
)

for (step in steps) {
  script <- file.path("scripts", step)
  message("\n========== ", step, " ==========")
  status <- system2("Rscript", script, stdout = "", stderr = "")
  if (!is.na(status) && status != 0) {
    stop("Pipeline failed at ", step, " (exit ", status, ")")
  }
}

message("\nDone. Reports:")
message("  ~/Downloads/jams_quadrant_full_report.html")
message("  ~/Downloads/jams_quadrant_cross_view.html")
message("  ~/Downloads/jams_quadrant_within_view.html")
message("  output/jams_quadrant/")
