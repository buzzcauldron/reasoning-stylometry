#!/usr/bin/env Rscript
# Benchmark word/character n-grams vs stopword baseline on JAMS style holdout.
library(stylo)
library(jsonlite)

train <- "corpus_classify/reference_research/balanced"
test <- "corpus_classify/jams_quadrant"
out_dir <- "output/corpus_benchmark"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

sw <- stopwords::stopwords("en", source = "snowball")
style_labels <- c(
  "geometric__geometric_style__masur_schleimer_disk_complex" = "geometric",
  "geometric__algebraic_style__bateman_katz_cap_sets" = "algebraic",
  "algebraic__geometric_style__dritschel_mccullough_rational_dilation" = "geometric",
  "algebraic__algebraic_style__hrushovski_approx_subgroups" = "algebraic"
)

score <- function(r) {
  pred <- setNames(as.character(r$predicted), rownames(r$frequencies.test.set))
  hits <- pred[names(style_labels)] == style_labels
  list(
    accuracy = sum(hits),
    per_paper = as.list(setNames(as.character(pred[names(style_labels)]), names(style_labels))),
    matches = as.list(setNames(hits, names(style_labels)))
  )
}

sep <- function(r) {
  X <- r$frequencies.training.set[, r$features.actually.used, drop = FALSE]
  labs <- ifelse(grepl("^geometric", rownames(X)), "geometric", "algebraic")
  cg <- colMeans(X[labs == "geometric", , drop = FALSE])
  ca <- colMeans(X[labs == "algebraic", , drop = FALSE])
  mean(abs(cg - ca))
}

top_feats <- function(r, n = 8) {
  X <- r$frequencies.training.set[, r$features.actually.used, drop = FALSE]
  labs <- ifelse(grepl("^geometric", rownames(X)), "geometric", "algebraic")
  cg <- colMeans(X[labs == "geometric", , drop = FALSE])
  ca <- colMeans(X[labs == "algebraic", , drop = FALSE])
  diff <- abs(cg - ca)
  ord <- order(diff, decreasing = TRUE)[seq_len(min(n, length(diff)))]
  as.list(setNames(round(diff[ord], 5), colnames(X)[ord]))
}

run_one <- function(label, ...) {
  cat(sprintf("\n=== %s ===\n", label))
  r <- classify(
    gui = FALSE,
    training.corpus.dir = train,
    test.corpus.dir = test,
    write.png.file = FALSE,
    classification.method = "delta",
    ...
  )
  s <- score(r)
  cat("Style accuracy:", s$accuracy, "/4\n")
  for (nm in names(style_labels)) {
    cat(" ", nm, "->", s$per_paper[[nm]], if (s$matches[[nm]]) "OK" else "MISS", "\n")
  }
  cat("Centroid L1 sep:", round(sep(r), 6), "\n")
  cat("Top features:", paste(names(top_feats(r)), collapse = ", "), "\n")
  list(
    label = label,
    accuracy = s$accuracy,
    per_paper = s$per_paper,
    separation = sep(r),
    n_features = length(r$features.actually.used),
    top_features = top_feats(r)
  )
}

configs <- list(
  list(label = "baseline stopwords175", mfw = length(sw), culling = 0, features = sw,
       analyzed.features = "w", ngram.size = 1),
  list(label = "word ngram2 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "w", ngram.size = 2),
  list(label = "word ngram3 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "w", ngram.size = 3),
  list(label = "word ngram4 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "w", ngram.size = 4),
  list(label = "word ngram2 mfw500 c20", mfw = 500, culling = 20, analyzed.features = "w", ngram.size = 2),
  list(label = "char ngram3 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "c", ngram.size = 3),
  list(label = "char ngram4 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "c", ngram.size = 4),
  list(label = "char ngram5 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "c", ngram.size = 5),
  list(label = "char ngram6 mfw300 c20", mfw = 300, culling = 20, analyzed.features = "c", ngram.size = 6)
)

results <- lapply(configs, function(cfg) {
  label <- cfg$label
  cfg$label <- NULL
  tryCatch(
    do.call(run_one, c(list(label = label), cfg)),
    error = function(e) {
      cat("ERROR:", conditionMessage(e), "\n")
      list(label = label, error = conditionMessage(e))
    }
  )
})

write_json(results, file.path(out_dir, "ngram_benchmark.json"), pretty = TRUE, auto_unbox = TRUE)
cat("\nWrote", file.path(out_dir, "ngram_benchmark.json"), "\n")
