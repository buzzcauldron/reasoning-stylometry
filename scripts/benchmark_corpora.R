# Benchmark JAMS classification against v1 vs v2 reference corpora.
# Run from project root: Rscript scripts/benchmark_corpora.R
library(stylo)
library(jsonlite)

stopword_list <- stopwords::stopwords("en", source = "snowball")
out_dir <- "output/corpus_benchmark"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

stylo_args <- list(
  mfw = length(stopword_list),
  culling = 0,
  features = stopword_list,
  classification.method = "delta"
)

benchmark <- function(train_dir, label) {
  cat("\n==========", label, "==========\n")
  result <- do.call(
    classify,
    c(
      list(
        gui = FALSE,
        training.corpus.dir = train_dir,
        test.corpus.dir = "corpus_classify/jams_quadrant",
        write.png.file = FALSE
      ),
      stylo_args
    )
  )
  stems <- rownames(result$frequencies.test.set)
  style_labels <- c(
    "geometric__geometric_style__masur_schleimer_disk_complex" = "geometric",
    "geometric__algebraic_style__bateman_katz_cap_sets" = "algebraic",
    "algebraic__geometric_style__dritschel_mccullough_rational_dilation" = "geometric",
    "algebraic__algebraic_style__hrushovski_approx_subgroups" = "algebraic"
  )
  pred <- as.character(result$predicted)
  names(pred) <- stems
  hits <- sum(pred[names(style_labels)] == style_labels)
  cat("Style accuracy:", hits, "/ 4\n")
  for (s in names(style_labels)) {
    cat(" ", s, "\n    expert:", style_labels[s], " predicted:", pred[s],
        if (pred[s] == style_labels[s]) "OK" else "MISS", "\n")
  }
  list(
    label = label,
    train_dir = train_dir,
    n_train = nrow(result$frequencies.training.set),
    predicted = as.list(pred),
    expected_prefix = as.list(as.character(result$expected)),
    test_files = rownames(result$frequencies.test.set),
    style_accuracy = hits,
    success_rate_filename = as.numeric(result$success.rate)
  )
}

results <- list(
  v1_cutknot = benchmark("corpus_classify/reference_set", "v1 elementary CutKnot"),
  v2_mixed = benchmark("corpus_classify/reference_v2", "v2 research + elementary"),
  v3_research_all = benchmark("corpus_classify/reference_research/chunks", "v3 research all chunks"),
  v3_research_balanced = benchmark("corpus_classify/reference_research/balanced", "v3 research balanced")
)

write_json(results, file.path(out_dir, "benchmark.json"), pretty = TRUE, auto_unbox = TRUE)
cat("\nWrote", file.path(out_dir, "benchmark.json"), "\n")
