# Classify four JAMS quadrant papers (content x style exemplars) against the
# geometric-vs-algebraic reference set using stopword-only stylo features.
#
# Default training corpus: reference_research/balanced (relabel-corrected, 50/50
# subsample of research-register arXiv proof chunks). See corpus_classify/CORPUS.md.
#
# Run from project root: Rscript scripts/run_jams_quadrant.R
library(stylo)
library(jsonlite)

TRAIN_DIR <- Sys.getenv("STYLO_TRAIN_DIR", "corpus_classify/reference_research/balanced")

stopword_list <- stopwords::stopwords("en", source = "snowball")
out_dir <- "output/jams_quadrant"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

stylo_args <- list(
  mfw = length(stopword_list),
  culling = 0,
  features = stopword_list,
  classification.method = "delta",
  analyzed.features = "w",
  ngram.size = 1
)

run_classify <- function(test_dir, label) {
  cat("\n=== classify:", label, "===\n")
  result <- do.call(
    classify,
    c(
      list(
        gui = FALSE,
        training.corpus.dir = TRAIN_DIR,
        test.corpus.dir = test_dir,
        write.png.file = FALSE
      ),
      stylo_args
    )
  )
  cat("expected:", paste(result$expected, collapse = ", "), "\n")
  cat("predicted:", paste(result$predicted, collapse = ", "), "\n")
  cat("success rate:", result$success.rate, "%\n")
  saveRDS(result, file.path(out_dir, paste0("classify_", label, ".rds")))
  result
}

run_rolling_one <- function(test_file, label) {
  test_dir <- file.path(out_dir, paste0("rolling_input_", label))
  dir.create(test_dir, showWarnings = FALSE, recursive = TRUE)
  dest <- file.path(test_dir, basename(test_file))
  if (!file.exists(dest)) {
    file.copy(test_file, dest)
  }
  cat("\n=== rolling:", label, "===\n")
  result <- do.call(
    rolling.classify,
    c(
      list(
        gui = FALSE,
        training.corpus.dir = TRAIN_DIR,
        test.corpus.dir = test_dir,
        slice.size = 250,
        slice.overlap = 150,
        write.png.file = TRUE,
        custom.graph.title = paste("Rolling:", label, "(stopwords)")
      ),
      stylo_args
    )
  )
  counts <- sort(table(as.character(result$classification.results)), decreasing = TRUE)
  print(counts)
  for (path in list.files(".", pattern = "^rolling-delta-.*\\.png$", full.names = TRUE)) {
    file.rename(path, file.path(out_dir, paste0("rolling_", label, ".png")))
  }
  saveRDS(result, file.path(out_dir, paste0("rolling_", label, ".rds")))
  result
}

full <- run_classify("corpus_classify/jams_quadrant", "full_papers")
excerpt <- run_classify("corpus_classify/jams_excerpts", "excerpts")

paper_files <- list.files("corpus_classify/jams_quadrant", pattern = "\\.txt$", full.names = TRUE)
rolling_results <- list()
for (path in paper_files) {
  label <- sub("\\.txt$", "", basename(path))
  rolling_results[[label]] <- run_rolling_one(path, label)
}

paper_meta <- data.frame(
  file = basename(paper_files),
  stem = sub("\\.txt$", "", basename(paper_files)),
  stringsAsFactors = FALSE
)

export <- list(
  full_papers = list(
    files = basename(paper_files),
    expected_filename_prefix = as.character(full$expected),
    predicted_style = as.character(full$predicted),
    success_rate = as.numeric(full$success.rate)
  ),
  excerpts = list(
    expected_filename_prefix = as.character(excerpt$expected),
    predicted_style = as.character(excerpt$predicted),
    success_rate = as.numeric(excerpt$success.rate)
  ),
  rolling = lapply(names(rolling_results), function(name) {
    r <- rolling_results[[name]]
    counts <- as.list(sort(table(as.character(r$classification.results)), decreasing = TRUE))
    total <- sum(unlist(counts))
    list(
      counts = counts,
      share_geometric = if ("geometric" %in% names(counts)) round(counts[["geometric"]] / total, 4) else 0,
      share_algebraic = if ("algebraic" %in% names(counts)) round(counts[["algebraic"]] / total, 4) else 0,
      n_slices = as.integer(total)
    )
  })
)
names(export$rolling) <- names(rolling_results)

style_labels <- c(
  "geometric__geometric_style__masur_schleimer_disk_complex" = "geometric",
  "geometric__algebraic_style__bateman_katz_cap_sets" = "algebraic",
  "algebraic__geometric_style__dritschel_mccullough_rational_dilation" = "geometric",
  "algebraic__algebraic_style__hrushovski_approx_subgroups" = "algebraic"
)
whole_pred <- setNames(as.character(full$predicted), rownames(full$frequencies.test.set))
export$style_accuracy <- list(
  whole_paper = sum(whole_pred[names(style_labels)] == style_labels),
  rolling_majority = sum(vapply(names(export$rolling), function(stem) {
    r <- export$rolling[[stem]]
    pred <- if (r$share_geometric > r$share_algebraic) "geometric" else "algebraic"
    pred == style_labels[stem]
  }, logical(1))),
  expert_labels = as.list(style_labels)
)

write_json(export, file.path(out_dir, "stylo_results.json"), pretty = TRUE, auto_unbox = TRUE)

summary <- list(full = full, excerpts = excerpt, rolling = rolling_results)
saveRDS(summary, file.path(out_dir, "jams_quadrant_summary.rds"))
cat("\nDone. Outputs in", out_dir, "\n")
