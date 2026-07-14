#!/usr/bin/env Rscript
# Corpus health via stylo::crossv on the training matrix from stylo::classify.
# Run after run_jams_quadrant.R (reuses classify_full_papers.rds).
# Usage: Rscript scripts/diagnose_corpus.R [sample_size] [out_json]
library(stylo)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
n_sample <- if (length(args) >= 1) as.integer(args[[1]]) else as.integer(Sys.getenv("STYLO_LOO_SAMPLE", "500"))
out_json <- if (length(args) >= 2) args[[2]] else "output/corpus_diagnosis_stylo.json"

rds_path <- "output/jams_quadrant/classify_full_papers.rds"
if (!file.exists(rds_path)) {
  stop("Run Rscript scripts/run_jams_quadrant.R first (missing ", rds_path, ")")
}

cl <- readRDS(rds_path)
freq <- as.matrix(cl$frequencies.training.set[, cl$features.actually.used, drop = FALSE])
train_labels <- ifelse(grepl("^geometric", rownames(freq)), "geometric", "algebraic")
corpus_dir <- cl$call$training.corpus.dir
if (is.null(corpus_dir)) corpus_dir <- Sys.getenv("STYLO_TRAIN_DIR", "corpus_classify/reference_research/balanced")

geo_idx <- which(train_labels == "geometric")
alg_idx <- which(train_labels == "algebraic")
geo_c <- colMeans(freq[geo_idx, , drop = FALSE])
alg_c <- colMeans(freq[alg_idx, , drop = FALSE])
sep_l1 <- mean(abs(geo_c - alg_c))

set.seed(42)
idx <- sample(seq_len(nrow(freq)), min(n_sample, nrow(freq)))
sub <- freq[idx, , drop = FALSE]
sub_lab <- train_labels[idx]

cat("Running stylo::crossv LOO on", nrow(sub), "of", nrow(freq), "training samples...\n")
cv <- crossv(
  training.set = sub,
  cv.mode = "leaveoneout",
  classes.training.set = sub_lab,
  classification.method = "delta"
)

correct <- sum(cv$predicted == cv$expected, na.rm = TRUE)
total <- length(cv$expected)

report <- list(
  corpus_dir = corpus_dir,
  n_texts = nrow(freq),
  n_geometric = sum(train_labels == "geometric"),
  n_algebraic = sum(train_labels == "algebraic"),
  n_features_used = ncol(freq),
  class_separability_l1 = round(sep_l1, 6),
  stylo_loo = list(
    n_sampled = total,
    correct = as.integer(correct),
    accuracy_pct = round(100 * correct / total, 2),
    confusion_matrix = as.list(as.matrix(cv$confusion_matrix)),
    method = "stylo::crossv leave-one-out on classify() training matrix"
  ),
  verdict = c(
    if (sep_l1 < 0.005) sprintf("CRITICAL: stylo feature centroids nearly identical (L1=%.4f)", sep_l1),
    if (correct / total < 0.85) sprintf(
      "WEAK: stylo crossv LOO accuracy only %.0f%% on sample", 100 * correct / total
    ),
    if (sep_l1 >= 0.005 && correct / total >= 0.85) "Corpus passes stylo separability checks"
  )
)
report$verdict <- report$verdict[!vapply(report$verdict, function(x) is.na(x) || !nzchar(x), logical(1))]

dir.create(dirname(out_json), showWarnings = FALSE, recursive = TRUE)
write_json(report, out_json, pretty = TRUE, auto_unbox = TRUE)
cat("\n=== STYLO VERDICT ===\n")
for (v in report$verdict) cat(" •", v, "\n")
cat("\nWrote", out_json, "\n")
