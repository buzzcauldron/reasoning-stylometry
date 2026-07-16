# Benchmark JAMS classification against v1 vs v2 reference corpora.
# Legacy/exploratory script predating the content/style split (see
# corpus_classify/CORPUS.md); benchmarks the CONTENT axis specifically since
# test.corpus.dir below (jams_quadrant) is content-leading.
# Run from project root: Rscript scripts/benchmark_corpora.R
library(stylo)
library(jsonlite)
source("R/jams_metadata.R")

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
  content_labels <- EXPERT_CONTENT_LABELS
  pred <- as.character(result$predicted)
  names(pred) <- stems
  hits <- sum(pred[names(content_labels)] == content_labels)
  cat("Content accuracy:", hits, "/ 4\n")
  for (s in names(content_labels)) {
    cat(" ", s, "\n    expert:", content_labels[s], " predicted:", pred[s],
        if (pred[s] == content_labels[s]) "OK" else "MISS", "\n")
  }
  list(
    label = label,
    train_dir = train_dir,
    n_train = nrow(result$frequencies.training.set),
    predicted = as.list(pred),
    expected_prefix = as.list(as.character(result$expected)),
    test_files = rownames(result$frequencies.test.set),
    content_accuracy = hits,
    success_rate_filename = as.numeric(result$success.rate)
  )
}

results <- list(
  v1_cutknot = benchmark("corpus_classify/reference_set", "v1 elementary CutKnot"),
  v2_mixed = benchmark("corpus_classify/reference_v2", "v2 research + elementary"),
  v3_research_all = benchmark("corpus_classify/reference_research/chunks", "v3 research all chunks"),
  v5_research_balanced_content = benchmark("corpus_classify/reference_research/balanced_content", "v5 research balanced (content axis)")
)

write_json(results, file.path(out_dir, "benchmark.json"), pretty = TRUE, auto_unbox = TRUE)
cat("\nWrote", file.path(out_dir, "benchmark.json"), "\n")
