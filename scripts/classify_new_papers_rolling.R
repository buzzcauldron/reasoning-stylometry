# Rolling (sliding-window) classification of the two non-JAMS math PDFs
# (Stokes overdetermination, aeroelastic/UAV review) on both axes, mirroring
# run_jams_quadrant.R's run_rolling_one() -- same slice size/overlap and
# real mfw.min/culling.min parameter names (see that script's history for why
# the fake mfw=/culling= names are a landmine).
#
# Run from project root: Rscript scripts/classify_new_papers_rolling.R
suppressMessages(library(stylo))
source("R/jams_metadata.R")  # wilson_ci(), rolling_label()

out_dir <- "output/new_paper_rolling"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

stopword_list <- stopwords::stopwords("en", source = "snowball")
content_args <- list(
  mfw.min = length(stopword_list), mfw.max = length(stopword_list), mfw.incr = 100,
  culling.min = 0, culling.max = 0, culling.incr = 20,
  features = stopword_list, classification.method = "delta",
  analyzed.features = "w", ngram.size = 1
)

style_words <- readLines("corpus_classify/style_function_words.txt")
style_args <- list(
  mfw.min = length(style_words), mfw.max = length(style_words), mfw.incr = 100,
  culling.min = 0, culling.max = 0, culling.incr = 20,
  features = style_words, classification.method = "delta",
  analyzed.features = "w", ngram.size = 1
)

papers <- list(
  stokes = "stokes_overdetermination.txt",
  aeroelastic = "aeroelastic_uav_review.txt"
)

run_rolling_one <- function(train_dir, test_file, label, stylo_args) {
  test_dir <- file.path(out_dir, paste0("rolling_input_", label))
  dir.create(test_dir, showWarnings = FALSE, recursive = TRUE)
  dest <- file.path(test_dir, basename(test_file))
  file.copy(test_file, dest, overwrite = TRUE)
  cat("\n=== rolling:", label, "===\n")
  result <- do.call(
    rolling.classify,
    c(
      list(gui = FALSE, training.corpus.dir = train_dir, test.corpus.dir = test_dir,
           slice.size = 250, slice.overlap = 150, write.png.file = TRUE,
           custom.graph.title = label),
      stylo_args
    )
  )
  counts <- sort(table(as.character(result$classification.results)), decreasing = TRUE)
  print(counts)
  for (path in list.files(".", pattern = "^rolling-delta-.*\\.png$", full.names = TRUE)) {
    file.rename(path, file.path(out_dir, paste0("rolling_", label, ".png")))
  }
  result
}

`%||%` <- function(a, b) if (length(a) == 0 || is.na(a)) b else a

summary_rows <- list()
for (name in names(papers)) {
  file <- papers[[name]]
  content_r <- run_rolling_one("corpus_classify/reference_research/balanced_content", file, paste0("content_", name), content_args)
  style_r <- run_rolling_one("corpus_classify/reference_research/balanced_style", file, paste0("style_", name), style_args)

  content_counts <- table(as.character(content_r$classification.results))
  style_counts <- table(as.character(style_r$classification.results))
  content_total <- sum(content_counts)
  style_total <- sum(style_counts)

  content_n_geo <- unname(content_counts["geometric"] %||% 0)
  style_n_geo <- unname(style_counts["geometric"] %||% 0)

  summary_rows[[length(summary_rows) + 1]] <- data.frame(
    paper = name,
    axis = "content",
    n_slices = content_total,
    share_geometric = round(content_n_geo / content_total, 3),
    share_algebraic = round(unname(content_counts["algebraic"] %||% 0) / content_total, 3),
    label = rolling_label(content_n_geo, content_total)
  )
  summary_rows[[length(summary_rows) + 1]] <- data.frame(
    paper = name,
    axis = "style",
    n_slices = style_total,
    share_geometric = round(style_n_geo / style_total, 3),
    share_algebraic = round(unname(style_counts["algebraic"] %||% 0) / style_total, 3),
    label = rolling_label(style_n_geo, style_total)
  )
}

summary_df <- do.call(rbind, summary_rows)
cat("\n=== ROLLING SUMMARY ===\n")
print(summary_df)
write.csv(summary_df, file.path(out_dir, "rolling_summary.csv"), row.names = FALSE)
