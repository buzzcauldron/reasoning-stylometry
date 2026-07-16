# Classify four JAMS quadrant papers on TWO independent axes — content (topic)
# and style (reasoning presentation) — against independently-labeled reference
# corpora using stopword-only stylo features.
#
# Content and style used to be the same label by construction (see
# corpus_classify/CORPUS.md and scripts/retag_content_style.py for the history).
# Training now uses two separately-balanced corpora, and stylo::classify()
# requires the ground-truth label to be the leading filename segment, so each
# axis needs its own directory naming order:
#   - content: corpus_classify/reference_research/balanced_content/ (content-leading)
#     against corpus_classify/jams_quadrant/ + jams_excerpts/ (content-leading)
#   - style:   corpus_classify/reference_research/balanced_style/ (style-leading)
#     against corpus_classify/jams_quadrant_style_first/ + jams_excerpts_style_first/
#     (built by scripts/make_style_leading_targets.R)
#
# Run from project root: Rscript scripts/run_jams_quadrant.R
library(stylo)
library(jsonlite)
source("R/jams_metadata.R")

CONTENT_TRAIN_DIR <- Sys.getenv("STYLO_CONTENT_TRAIN_DIR", "corpus_classify/reference_research/balanced_content")
STYLE_TRAIN_DIR <- Sys.getenv("STYLO_STYLE_TRAIN_DIR", "corpus_classify/reference_research/balanced_style")

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

# corpus_classify/jams_quadrant_style_first/ and jams_excerpts_style_first/
# (built by make_style_leading_targets.R) name files
# `{style}__{content}_content__{original_stem}.txt` so stylo's leading-segment
# class parsing sees style. That leaves stylo's own rowname (the whole
# basename) not equal to the canonical stem used everywhere else (EXPERT_*
# labels, rolling output keys, etc.) -- strip the prefix back off so every
# axis keys its results by the same canonical stem.
strip_style_first_prefix <- function(x) sub("^[^_]+__[^_]+_content__", "", x)

run_classify <- function(train_dir, test_dir, label, rowname_fn = identity) {
  cat("\n=== classify:", label, "===\n")
  result <- do.call(
    classify,
    c(
      list(
        gui = FALSE,
        training.corpus.dir = train_dir,
        test.corpus.dir = test_dir,
        write.png.file = FALSE
      ),
      stylo_args
    )
  )
  rownames(result$frequencies.test.set) <- rowname_fn(rownames(result$frequencies.test.set))
  if (!is.null(rownames(result$distance.table))) {
    rownames(result$distance.table) <- rowname_fn(rownames(result$distance.table))
  }
  cat("expected:", paste(result$expected, collapse = ", "), "\n")
  cat("predicted:", paste(result$predicted, collapse = ", "), "\n")
  cat("success rate:", result$success.rate, "%\n")
  saveRDS(result, file.path(out_dir, paste0("classify_", label, ".rds")))
  result
}

run_rolling_one <- function(train_dir, test_file, label) {
  test_dir <- file.path(out_dir, paste0("rolling_input_", label))
  dir.create(test_dir, showWarnings = FALSE, recursive = TRUE)
  dest <- file.path(test_dir, basename(test_file))
  if (!file.exists(dest)) {
    file.copy(test_file, dest)
  }
  cat("\n=== rolling:", label, "===\n")
  # stylo::rolling.classify() does not support reusing a precomputed
  # training.frequencies matrix together with a different test.corpus.dir
  # (verified: it silently falls back to a broken from-scratch corpus-loading
  # path). The corpus is capped at 1500 chunks/class in
  # balance_research_corpus.py specifically so re-loading it from disk 8 times
  # (4 papers x 2 axes) stays fast and memory-safe -- see that script's
  # docstring for the OOM this replaced.
  result <- do.call(
    rolling.classify,
    c(
      list(
        gui = FALSE,
        training.corpus.dir = train_dir,
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

# --- whole-paper + excerpt classification, both axes ---
content_full <- run_classify(CONTENT_TRAIN_DIR, "corpus_classify/jams_quadrant", "content_full_papers")
content_excerpt <- run_classify(CONTENT_TRAIN_DIR, "corpus_classify/jams_excerpts", "content_excerpts")
style_full <- run_classify(STYLE_TRAIN_DIR, "corpus_classify/jams_quadrant_style_first", "style_full_papers", strip_style_first_prefix)
style_excerpt <- run_classify(STYLE_TRAIN_DIR, "corpus_classify/jams_excerpts_style_first", "style_excerpts", strip_style_first_prefix)

# --- rolling classification, both axes (test file naming doesn't matter for
# rolling.classify — only the training corpus determines what the labels mean —
# so both axes reuse the same raw paper files as input) ---
paper_files <- list.files("corpus_classify/jams_quadrant", pattern = "\\.txt$", full.names = TRUE)
content_rolling <- list()
style_rolling <- list()
for (path in paper_files) {
  stem <- sub("\\.txt$", "", basename(path))
  content_rolling[[stem]] <- run_rolling_one(CONTENT_TRAIN_DIR, path, paste0("content_", stem))
  style_rolling[[stem]] <- run_rolling_one(STYLE_TRAIN_DIR, path, paste0("style_", stem))
}

rolling_summary <- function(rolling_results) {
  lapply(names(rolling_results), function(name) {
    r <- rolling_results[[name]]
    counts <- as.list(sort(table(as.character(r$classification.results)), decreasing = TRUE))
    total <- sum(unlist(counts))
    list(
      counts = counts,
      share_geometric = if ("geometric" %in% names(counts)) round(counts[["geometric"]] / total, 4) else 0,
      share_algebraic = if ("algebraic" %in% names(counts)) round(counts[["algebraic"]] / total, 4) else 0,
      n_slices = as.integer(total)
    )
  }) |> setNames(names(rolling_results))
}

axis_accuracy <- function(full_result, excerpt_result, rolling_results, expert_labels) {
  whole_pred <- setNames(as.character(full_result$predicted), rownames(full_result$frequencies.test.set))
  rolling_share <- rolling_summary(rolling_results)
  whole_match <- whole_pred[names(expert_labels)] == expert_labels
  rolling_match <- vapply(names(rolling_share), function(stem) {
    r <- rolling_share[[stem]]
    pred <- if (r$share_geometric > r$share_algebraic) "geometric" else "algebraic"
    pred == expert_labels[stem]
  }, logical(1))
  weights <- EXPERT_LABEL_CONFIDENCE[names(expert_labels)]
  list(
    whole_paper = sum(whole_match),
    rolling_majority = sum(rolling_match),
    # Confidence-weighted: a correct/incorrect call on a paper with weaker
    # rater agreement (afc_consistency < 1) counts for less than a unanimous
    # one, out of a max possible score of sum(weights) rather than n=4.
    whole_paper_weighted = round(sum(whole_match * weights), 3),
    rolling_majority_weighted = round(sum(rolling_match * weights), 3),
    max_possible_weighted = round(sum(weights), 3),
    expert_labels = as.list(expert_labels),
    expert_label_confidence = as.list(weights)
  )
}

export <- list(
  content = list(
    full_papers = list(
      files = basename(paper_files),
      expected_filename_prefix = as.character(content_full$expected),
      predicted = as.character(content_full$predicted),
      success_rate = as.numeric(content_full$success.rate)
    ),
    excerpts = list(
      expected_filename_prefix = as.character(content_excerpt$expected),
      predicted = as.character(content_excerpt$predicted),
      success_rate = as.numeric(content_excerpt$success.rate)
    ),
    rolling = rolling_summary(content_rolling),
    accuracy = axis_accuracy(content_full, content_excerpt, content_rolling, EXPERT_CONTENT_LABELS)
  ),
  style = list(
    full_papers = list(
      files = basename(paper_files),
      expected_filename_prefix = as.character(style_full$expected),
      predicted = as.character(style_full$predicted),
      success_rate = as.numeric(style_full$success.rate)
    ),
    excerpts = list(
      expected_filename_prefix = as.character(style_excerpt$expected),
      predicted = as.character(style_excerpt$predicted),
      success_rate = as.numeric(style_excerpt$success.rate)
    ),
    rolling = rolling_summary(style_rolling),
    accuracy = axis_accuracy(style_full, style_excerpt, style_rolling, EXPERT_STYLE_LABELS)
  )
)

# Joint quadrant confusion: does the pair (predicted content, predicted style)
# match the pair (expert content, expert style) for each paper?
content_whole_pred <- setNames(as.character(content_full$predicted), rownames(content_full$frequencies.test.set))
style_whole_pred <- setNames(as.character(style_full$predicted), rownames(style_full$frequencies.test.set))
quadrant <- lapply(names(EXPERT_STYLE_LABELS), function(stem) {
  list(
    stem = stem,
    expert_content = unname(EXPERT_CONTENT_LABELS[stem]),
    expert_style = unname(EXPERT_STYLE_LABELS[stem]),
    predicted_content = unname(content_whole_pred[stem]),
    predicted_style = unname(style_whole_pred[stem]),
    content_match = unname(content_whole_pred[stem] == EXPERT_CONTENT_LABELS[stem]),
    style_match = unname(style_whole_pred[stem] == EXPERT_STYLE_LABELS[stem]),
    quadrant_match = unname(
      content_whole_pred[stem] == EXPERT_CONTENT_LABELS[stem] &
        style_whole_pred[stem] == EXPERT_STYLE_LABELS[stem]
    )
  )
})
names(quadrant) <- names(EXPERT_STYLE_LABELS)
export$quadrant <- quadrant
export$quadrant_accuracy <- sum(vapply(quadrant, function(q) q$quadrant_match, logical(1)))

write_json(export, file.path(out_dir, "stylo_results.json"), pretty = TRUE, auto_unbox = TRUE)

summary <- list(
  content = list(full = content_full, excerpts = content_excerpt, rolling = content_rolling),
  style = list(full = style_full, excerpts = style_excerpt, rolling = style_rolling)
)
saveRDS(summary, file.path(out_dir, "jams_quadrant_summary.rds"))
cat("\nDone. Outputs in", out_dir, "\n")
cat("Content accuracy: whole-paper", export$content$accuracy$whole_paper, "/4, rolling", export$content$accuracy$rolling_majority, "/4",
    "(weighted", export$content$accuracy$whole_paper_weighted, "/", export$content$accuracy$max_possible_weighted, ")\n")
cat("Style accuracy:   whole-paper", export$style$accuracy$whole_paper, "/4, rolling", export$style$accuracy$rolling_majority, "/4",
    "(weighted", export$style$accuracy$whole_paper_weighted, "/", export$style$accuracy$max_possible_weighted, ")\n")
cat("Joint quadrant (both axes correct):", export$quadrant_accuracy, "/4\n")
cat("Note: expert labels are contested judgments, not ground truth -- see afc_consistency per paper (R/jams_metadata.R)\n")
