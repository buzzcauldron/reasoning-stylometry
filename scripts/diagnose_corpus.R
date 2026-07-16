#!/usr/bin/env Rscript
# Corpus health via stylo::crossv on the training matrices from classify(), for
# BOTH the content and style axes, plus an independence check between them —
# are content and style labels actually decoupled in the training data, or
# still confounded the way they were before scripts/retag_content_style.py?
# Run after run_jams_quadrant.R (reuses classify_{content,style}_full_papers.rds).
# Usage: Rscript scripts/diagnose_corpus.R [sample_size] [out_json]
library(stylo)
library(jsonlite)

args <- commandArgs(trailingOnly = TRUE)
n_sample <- if (length(args) >= 1) as.integer(args[[1]]) else as.integer(Sys.getenv("STYLO_LOO_SAMPLE", "500"))
out_json <- if (length(args) >= 2) args[[2]] else "output/corpus_diagnosis_stylo.json"

diagnose_axis <- function(rds_name, n_sample) {
  rds_path <- file.path("output/jams_quadrant", rds_name)
  if (!file.exists(rds_path)) {
    stop("Run Rscript scripts/run_jams_quadrant.R first (missing ", rds_path, ")")
  }
  cl <- readRDS(rds_path)
  freq <- as.matrix(cl$frequencies.training.set[, cl$features.actually.used, drop = FALSE])
  labels <- ifelse(grepl("^geometric", rownames(freq)), "geometric", "algebraic")
  corpus_dir <- cl$call$training.corpus.dir

  geo_idx <- which(labels == "geometric")
  alg_idx <- which(labels == "algebraic")
  geo_c <- colMeans(freq[geo_idx, , drop = FALSE])
  alg_c <- colMeans(freq[alg_idx, , drop = FALSE])
  sep_l1 <- mean(abs(geo_c - alg_c))

  set.seed(42)
  idx <- sample(seq_len(nrow(freq)), min(n_sample, nrow(freq)))
  sub <- freq[idx, , drop = FALSE]
  sub_lab <- labels[idx]

  cv <- crossv(
    training.set = sub,
    cv.mode = "leaveoneout",
    classes.training.set = sub_lab,
    classification.method = "delta"
  )
  correct <- sum(cv$predicted == cv$expected, na.rm = TRUE)
  total <- length(cv$expected)

  list(
    corpus_dir = corpus_dir,
    n_texts = nrow(freq),
    n_geometric = sum(labels == "geometric"),
    n_algebraic = sum(labels == "algebraic"),
    n_features_used = ncol(freq),
    class_separability_l1 = round(sep_l1, 6),
    stylo_loo = list(
      n_sampled = total,
      correct = as.integer(correct),
      accuracy_pct = round(100 * correct / total, 2),
      confusion_matrix = as.list(as.matrix(cv$confusion_matrix)),
      method = "stylo::crossv leave-one-out on classify() training matrix"
    )
  )
}

verdict_for <- function(axis_name, d) {
  sep_l1 <- d$class_separability_l1
  acc <- d$stylo_loo$correct / d$stylo_loo$n_sampled
  c(
    if (sep_l1 < 0.005) sprintf("CRITICAL [%s]: stylo feature centroids nearly identical (L1=%.4f)", axis_name, sep_l1),
    if (acc < 0.85) sprintf("WEAK [%s]: stylo crossv LOO accuracy only %.0f%% on sample", axis_name, 100 * acc),
    if (sep_l1 >= 0.005 && acc >= 0.85) sprintf("[%s] passes stylo separability checks", axis_name)
  )
}

content <- diagnose_axis("classify_content_full_papers.rds", n_sample = n_sample)
style <- diagnose_axis("classify_style_full_papers.rds", n_sample = n_sample)

# Independence check: are content and style genuinely decoupled in the training
# corpus, or still confounded (content_topic == style, as before the fix)?
retag_report_path <- "output/corpus_diagnosis_content_style_retag.json"
independence <- if (file.exists(retag_report_path)) {
  retag <- fromJSON(retag_report_path)
  ct <- retag$contingency_content__style
  tbl <- matrix(
    c(ct$geometric__geometric, ct$geometric__algebraic, ct$algebraic__geometric, ct$algebraic__algebraic),
    nrow = 2, byrow = TRUE
  )
  chisq <- suppressWarnings(chisq.test(tbl))
  stat <- unname(chisq$statistic)
  cramers_v <- round(sqrt(stat / sum(tbl)), 4)
  off_diag <- retag$off_diagonal_fraction
  interpretation <- if (off_diag < 0.02) {
    sprintf("CRITICAL: content and style are still ~fully confounded (%.1f%% off-diagonal) -- retagging did not decouple them.", 100 * off_diag)
  } else if (chisq$p.value < 0.001 && cramers_v > 0.5) {
    sprintf("Content and style are decoupled (%.1f%% off-diagonal) but still statistically associated (Cramer's V=%.2f) -- expected for topic-correlated heuristic tags, not evidence of a bug.", 100 * off_diag, cramers_v)
  } else {
    sprintf("Content and style are decoupled (%.1f%% off-diagonal); low residual association (Cramer's V=%.2f).", 100 * off_diag, cramers_v)
  }
  list(
    n_geometric_geometric = ct$geometric__geometric,
    n_geometric_algebraic = ct$geometric__algebraic,
    n_algebraic_geometric = ct$algebraic__geometric,
    n_algebraic_algebraic = ct$algebraic__algebraic,
    off_diagonal_fraction = off_diag,
    chi_squared = round(stat, 4),
    p_value = signif(chisq$p.value, 4),
    cramers_v = cramers_v,
    interpretation = interpretation
  )
} else {
  list(note = "Run scripts/retag_content_style.py to generate the independence check", interpretation = NA)
}

report <- list(
  content = content,
  style = style,
  independence = independence,
  verdict = c(verdict_for("content", content), verdict_for("style", style), independence$interpretation)
)
report$verdict <- report$verdict[!vapply(report$verdict, function(x) is.na(x) || !nzchar(x), logical(1))]

dir.create(dirname(out_json), showWarnings = FALSE, recursive = TRUE)
write_json(report, out_json, pretty = TRUE, auto_unbox = TRUE)
cat("\n=== STYLO VERDICT ===\n")
for (v in report$verdict) cat(" •", v, "\n")
cat("\nWrote", out_json, "\n")
