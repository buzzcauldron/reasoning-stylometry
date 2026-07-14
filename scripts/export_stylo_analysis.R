# Export detailed stylometric analysis JSON for HTML report generation.
# Run after classify/rolling: Rscript scripts/export_stylo_analysis.R
library(jsonlite)

out_dir <- "output/jams_quadrant"
full <- readRDS(file.path(out_dir, "classify_full_papers.rds"))
excerpt <- readRDS(file.path(out_dir, "classify_excerpts.rds"))

paper_files <- list.files("corpus_classify/jams_quadrant", pattern = "\\.txt$")
paper_stems <- sub("\\.txt$", "", paper_files)

short_name <- function(stem) {
  parts <- strsplit(stem, "__")[[1]]
  if (length(parts) >= 3) paste(parts[1], parts[3], sep = " / ") else stem
}

wilson_ci <- function(k, n, z = 1.96) {
  if (n <= 0) return(c(NA_real_, NA_real_))
  p <- k / n
  denom <- 1 + z^2 / n
  centre <- (p + z^2 / (2 * n)) / denom
  margin <- z * sqrt((p * (1 - p) + z^2 / (4 * n)) / n) / denom
  c(max(0, centre - margin), min(1, centre + margin))
}

cohens_h <- function(p1, p2) {
  2 * (asin(sqrt(p1)) - asin(sqrt(p2)))
}

delta_to_centroid <- function(row_vec, centroid_vec) {
  mean(abs(as.numeric(row_vec) - as.numeric(centroid_vec)))
}

delta_to_refs <- function(test_row, train_mat) {
  d <- sapply(seq_len(nrow(train_mat)), function(j) {
    mean(abs(as.numeric(test_row) - train_mat[j, ]))
  })
  names(d) <- rownames(train_mat)
  d
}

ref_labels <- rownames(full$frequencies.training.set)
ref_class <- ifelse(grepl("^geometric", ref_labels), "geometric", "algebraic")

train_freq <- as.matrix(full$frequencies.training.set)
geo_idx <- which(ref_class == "geometric")
alg_idx <- which(ref_class == "algebraic")
geo_centroid <- colMeans(train_freq[geo_idx, , drop = FALSE])
alg_centroid <- colMeans(train_freq[alg_idx, , drop = FALSE])

feats_used <- full$features.actually.used
train_sub_all <- train_freq[, feats_used, drop = FALSE]
geo_c_feat <- colMeans(train_sub_all[geo_idx, , drop = FALSE])
alg_c_feat <- colMeans(train_sub_all[alg_idx, , drop = FALSE])

class_sep_l1 <- mean(abs(geo_c_feat - alg_c_feat))
top_disc_idx <- order(abs(geo_c_feat - alg_c_feat), decreasing = TRUE)[seq_len(min(15, length(feats_used)))]
top_discriminators <- lapply(top_disc_idx, function(j) {
  list(
    word = feats_used[j],
    geo_centroid = round(geo_c_feat[j], 5),
    alg_centroid = round(alg_c_feat[j], 5),
    geo_minus_alg = round(geo_c_feat[j] - alg_c_feat[j], 5)
  )
})

sample_loo <- function(freq_mat, labels, n_sample = 2000, seed = 42) {
  set.seed(seed)
  n <- nrow(freq_mat)
  idx <- sample(seq_len(n), min(n_sample, n))
  correct <- 0L
  for (i in idx) {
    g_idx <- which(labels == "geometric" & seq_len(n) != i)
    a_idx <- which(labels == "algebraic" & seq_len(n) != i)
    cg <- colMeans(freq_mat[g_idx, , drop = FALSE])
    ca <- colMeans(freq_mat[a_idx, , drop = FALSE])
    v <- freq_mat[i, ]
    pred <- if (delta_to_centroid(v, cg) < delta_to_centroid(v, ca)) "geometric" else "algebraic"
    if (pred == labels[i]) correct <- correct + 1L
  }
  total <- length(idx)
  ci <- wilson_ci(correct, total)
  list(
    n_sampled = total,
    correct = correct,
    accuracy = round(correct / total, 4),
    accuracy_pct = round(100 * correct / total, 2),
    wilson_ci_low = round(ci[1], 4),
    wilson_ci_high = round(ci[2], 4),
    note = "Sampled leave-one-out Burrows-Delta on training feature matrix (stylo stopwords)"
  )
}

loo_train <- sample_loo(train_sub_all, ref_class)

geo_intra <- mean(sapply(geo_idx, function(i) delta_to_centroid(train_sub_all[i, ], geo_c_feat)))
alg_intra <- mean(sapply(alg_idx, function(i) delta_to_centroid(train_sub_all[i, ], alg_c_feat)))
geo_to_alg <- mean(sapply(geo_idx, function(i) delta_to_centroid(train_sub_all[i, ], alg_c_feat)))
alg_to_geo <- mean(sapply(alg_idx, function(i) delta_to_centroid(train_sub_all[i, ], geo_c_feat)))

analyze_paper <- function(i, classify_result) {
  stem <- rownames(classify_result$frequencies.test.set)[i]
  test_row <- classify_result$frequencies.test.set[i, classify_result$features.actually.used, drop = FALSE]
  train_sub <- classify_result$frequencies.training.set[, classify_result$features.actually.used, drop = FALSE]
  dists <- delta_to_refs(test_row, train_sub)
  geo_mean <- mean(dists[ref_class == "geometric"])
  alg_mean <- mean(dists[ref_class == "algebraic"])
  nn <- sort(dists)[1:10]
  nn_out <- lapply(names(nn), function(nm) {
    list(
      id = nm,
      short_id = sub("^[^_]+__([^_]+(?:_[^_]+)*)__.*", "\\1", nm),
      class = ref_class[match(nm, ref_labels)],
      distance = round(unname(nn[nm]), 4)
    )
  })
  nn_classes <- vapply(nn_out, function(x) x$class, character(1))
  nn_geo <- sum(nn_classes == "geometric")

  test_freq <- as.numeric(classify_result$frequencies.test.set[i, ])
  names(test_freq) <- colnames(classify_result$frequencies.test.set)
  feats <- classify_result$features.actually.used
  test_freq <- test_freq[feats]
  geo_c <- geo_centroid[feats]
  alg_c <- alg_centroid[feats]
  geo_pull <- test_freq - geo_c
  alg_pull <- test_freq - alg_c
  style_score <- alg_pull - geo_pull

  ord <- order(abs(style_score), decreasing = TRUE)[1:15]
  top_features <- lapply(ord, function(j) {
    list(
      word = feats[j],
      test_freq = round(test_freq[j], 4),
      geo_centroid = round(geo_c[j], 4),
      alg_centroid = round(alg_c[j], 4),
      style_score = round(style_score[j], 4)
    )
  })

  list(
    stem = stem,
    short_name = short_name(stem),
    expected_prefix = as.character(classify_result$expected[i]),
    predicted = as.character(classify_result$predicted[i]),
    geo_mean_distance = round(geo_mean, 4),
    alg_mean_distance = round(alg_mean, 4),
    delta_alg_minus_geo = round(alg_mean - geo_mean, 4),
    nearest_neighbors = nn_out,
    nn_geo_count = nn_geo,
    nn_alg_count = 10L - nn_geo,
    top_style_features = top_features
  )
}

papers_full <- lapply(seq_len(nrow(full$frequencies.test.set)), function(i) analyze_paper(i, full))
names(papers_full) <- rownames(full$frequencies.test.set)

papers_excerpt <- lapply(seq_len(nrow(excerpt$frequencies.test.set)), function(i) analyze_paper(i, excerpt))
names(papers_excerpt) <- rownames(excerpt$frequencies.test.set)

rolling_export <- list()
CONF_THRESHOLDS <- c(0.02, 0.03, 0.05, 0.10)
SLICE_SIZE <- 250L
SLICE_OVERLAP <- 150L
SLICE_STEP <- SLICE_SIZE - SLICE_OVERLAP

margin_histogram <- function(margins, n_bins = 20) {
  if (!length(margins)) return(list())
  brks <- seq(0, max(margins) * 1.001, length.out = n_bins + 1)
  counts <- as.integer(hist(margins, breaks = brks, plot = FALSE)$counts)
  lapply(seq_len(n_bins), function(i) {
    list(
      bin_low = round(brks[i], 4),
      bin_high = round(brks[i + 1], 4),
      count = counts[i]
    )
  })
}

for (stem in paper_stems) {
  rds_path <- file.path(out_dir, paste0("rolling_", stem, ".rds"))
  if (!file.exists(rds_path)) next
  r <- readRDS(rds_path)
  slices <- as.character(r$classification.results)
  counts <- as.list(sort(table(slices), decreasing = TRUE))
  total <- length(slices)
  n_geo <- sum(slices == "geometric")

  margins <- as.numeric(r$classification.scores[, 2] - r$classification.scores[, 1])
  weights <- pmax(margins, 0)
  geo_mask <- slices == "geometric"
  conf_weighted_geo <- if (sum(weights) > 0) sum(weights[geo_mask]) / sum(weights) else NA

  geo_ci <- wilson_ci(n_geo, total)
  bt <- binom.test(n_geo, total, p = 0.5, alternative = "two.sided")
  set.seed(42)
  boot_shares <- replicate(2000, {
    idx <- sample(total, total, replace = TRUE)
    mean(slices[idx] == "geometric")
  })
  boot_ci <- quantile(boot_shares, c(0.025, 0.975))

  lag1_same <- if (total > 1) mean(slices[-total] == slices[-1]) else NA

  threshold_stats <- lapply(CONF_THRESHOLDS, function(th) {
    keep <- margins >= th
    n <- sum(keep)
    if (n == 0) {
      return(list(threshold = th, n = 0L, geo_share = NA, alg_share = NA, wilson_ci_low = NA, wilson_ci_high = NA))
    }
    seg <- slices[keep]
    n_g <- sum(seg == "geometric")
    ci <- wilson_ci(n_g, n)
    list(
      threshold = th,
      n = as.integer(n),
      pct = round(100 * n / total, 2),
      geo_share = round(n_g / n, 4),
      alg_share = round(1 - n_g / n, 4),
      wilson_ci_low = round(ci[1], 4),
      wilson_ci_high = round(ci[2], 4)
    )
  })

  n_bins <- min(40, total)
  bin_size <- ceiling(total / n_bins)
  bins <- lapply(seq_len(n_bins), function(b) {
    lo <- (b - 1) * bin_size + 1
    hi <- min(b * bin_size, total)
    if (lo > total) return(list(index = b, geo_share = NA))
    seg <- slices[lo:hi]
    seg_m <- margins[lo:hi]
    list(
      index = b,
      start_slice = lo,
      end_slice = hi,
      geo_share = round(mean(seg == "geometric"), 4),
      alg_share = round(mean(seg == "algebraic"), 4),
      mean_margin = round(mean(seg_m), 4),
      strong_share = round(mean(seg_m >= 0.05), 4)
    )
  })

  top_conf <- order(margins, decreasing = TRUE)[seq_len(min(12, total))]
  top_slices <- lapply(top_conf, function(i) {
    list(
      slice_index = as.integer(i),
      predicted = slices[i],
      margin = round(margins[i], 4),
      word_offset = as.integer(names(r$classification.results)[i])
    )
  })

  text_len <- if (!is.null(r$text.length)) as.integer(r$text.length) else NA
  eff_n <- if (!is.na(text_len)) as.integer(ceiling(text_len / SLICE_STEP)) else NA

  rolling_export[[stem]] <- list(
    n_slices = total,
    text_length = text_len,
    effective_independent_slices = eff_n,
    slice_step_words = SLICE_STEP,
    overlap_fraction = round(SLICE_OVERLAP / SLICE_SIZE, 3),
    counts = counts,
    share_geometric = if ("geometric" %in% names(counts)) round(counts[["geometric"]] / total, 4) else 0,
    share_algebraic = if ("algebraic" %in% names(counts)) round(counts[["algebraic"]] / total, 4) else 0,
    geo_wilson_ci_low = round(geo_ci[1], 4),
    geo_wilson_ci_high = round(geo_ci[2], 4),
    geo_bootstrap_ci_low = round(boot_ci[1], 4),
    geo_bootstrap_ci_high = round(boot_ci[2], 4),
    binomial_p_vs_half = signif(bt$p.value, 4),
    cohens_h_vs_half = round(cohens_h(n_geo / total, 0.5), 4),
    margin_mean = round(mean(margins), 4),
    margin_sd = round(sd(margins), 4),
    margin_median = round(median(margins), 4),
    margin_p05 = round(as.numeric(quantile(margins, 0.05)), 4),
    margin_p10 = round(as.numeric(quantile(margins, 0.10)), 4),
    margin_p25 = round(as.numeric(quantile(margins, 0.25)), 4),
    margin_p75 = round(as.numeric(quantile(margins, 0.75)), 4),
    margin_p90 = round(as.numeric(quantile(margins, 0.90)), 4),
    margin_p95 = round(as.numeric(quantile(margins, 0.95)), 4),
    margin_max = round(max(margins), 4),
    margin_histogram = margin_histogram(margins),
    lag1_label_agreement = round(lag1_same, 4),
    confidence_weighted_geo_share = round(conf_weighted_geo, 4),
    threshold_stats = threshold_stats,
    timeline_bins = bins,
    top_confident_slices = top_slices
  )
}

distance_matrix <- lapply(rownames(full$frequencies.test.set), function(row) {
  idx <- match(row, rownames(full$frequencies.test.set))
  test_row <- full$frequencies.test.set[idx, full$features.actually.used, drop = FALSE]
  train_sub <- full$frequencies.training.set[, full$features.actually.used, drop = FALSE]
  vals <- delta_to_refs(test_row, train_sub)
  as.list(round(vals, 4))
})
names(distance_matrix) <- rownames(full$frequencies.test.set)

manifest_path <- "corpus_classify/reference_research/manifest.json"
manifest_meta <- if (file.exists(manifest_path)) {
  m <- jsonlite::fromJSON(manifest_path)
  src <- m$sources
  n_src <- if (is.data.frame(src)) nrow(src) else length(src)
  list(
    version = if (!is.null(m$version)) m$version else NA,
    n_sources = n_src,
    n_sources_geometric = sum(src$style == "geometric"),
    n_sources_algebraic = sum(src$style == "algebraic")
  )
} else list()

stylo_results_path <- file.path(out_dir, "stylo_results.json")
style_accuracy <- if (file.exists(stylo_results_path)) {
  jsonlite::fromJSON(stylo_results_path)$style_accuracy
} else list()

expert_labels <- style_accuracy$expert_labels
if (is.null(expert_labels)) expert_labels <- list()

confusion_rolling <- list()
confusion_whole <- list()
for (nm in names(expert_labels)) {
  expert <- expert_labels[[nm]]
  roll <- rolling_export[[nm]]
  if (!is.null(roll)) {
    pred <- if (roll$share_geometric > 0.5) "geometric" else "algebraic"
    confusion_rolling[[nm]] <- list(expert = expert, predicted = pred, match = pred == expert)
  }
  if (nm %in% names(papers_full)) {
    pred <- papers_full[[nm]]$predicted
    confusion_whole[[nm]] <- list(expert = expert, predicted = pred, match = pred == expert)
  }
}

load_benchmark <- function(path) {
  if (!file.exists(path)) return(NULL)
  jsonlite::fromJSON(path)
}

corpus_health <- list(
  class_separability_l1 = round(class_sep_l1, 6),
  loo_sample = loo_train,
  intra_class_delta = list(
    geometric_mean = round(geo_intra, 4),
    algebraic_mean = round(alg_intra, 4)
  ),
  inter_class_delta = list(
    geo_chunks_to_alg_centroid = round(geo_to_alg, 4),
    alg_chunks_to_geo_centroid = round(alg_to_geo, 4)
  ),
  separation_ratio = round((geo_to_alg + alg_to_geo) / (geo_intra + alg_intra), 4),
  top_discriminators = top_discriminators,
  verdict = c(
    if (class_sep_l1 < 0.005) sprintf(
      "CRITICAL: stopword centroids nearly identical on stylo features (L1=%.4f)", class_sep_l1
    ),
    if (loo_train$accuracy < 0.85) sprintf(
      "WEAK: sampled LOO accuracy %.1f%% (95%% Wilson %.1f–%.1f%%) on training matrix",
      loo_train$accuracy_pct, 100 * loo_train$wilson_ci_low, 100 * loo_train$wilson_ci_high
    ),
    if (class_sep_l1 >= 0.005 && loo_train$accuracy >= 0.85) "Training matrix passes separability checks"
  )
)
corpus_health$verdict <- corpus_health$verdict[!vapply(corpus_health$verdict, function(x) is.na(x) || !nzchar(x), logical(1))]

export <- list(
  meta = list(
    method = "Burrows Delta",
    features = "175 English stopwords (Snowball)",
    n_features_used = length(feats_used),
    train_dir = "corpus_classify/reference_research/balanced",
    reference_n = length(ref_labels),
    reference_geometric = sum(ref_class == "geometric"),
    reference_algebraic = sum(ref_class == "algebraic"),
    manifest = manifest_meta,
    slice_size = SLICE_SIZE,
    slice_overlap = SLICE_OVERLAP,
    slice_step = SLICE_STEP,
    culling = 0,
    classification_method = "delta",
    confidence_note = "Slice margin = Delta(2nd best) - Delta(best); larger = more confident assignment",
    inference_note = "Rolling slices overlap (150/250); Wilson/bootstrap CIs treat slices as i.i.d. — conservative; effective independent slices ≈ ceil(words/100)"
  ),
  corpus_health = corpus_health,
  full_papers = list(
    success_rate = as.numeric(full$success.rate),
    papers = papers_full,
    distance_matrix = distance_matrix
  ),
  excerpts = list(
    success_rate = as.numeric(excerpt$success.rate),
    papers = papers_excerpt
  ),
  rolling = rolling_export,
  style_accuracy = style_accuracy,
  confusion = list(rolling = confusion_rolling, whole_paper = confusion_whole),
  benchmarks = list(
    corpora = load_benchmark("output/corpus_benchmark/benchmark.json"),
    features = load_benchmark("output/corpus_benchmark/ngram_benchmark.json")
  ),
  reference_labels = ref_labels,
  reference_classes = as.list(setNames(as.character(ref_class), ref_labels))
)

write_json(export, file.path(out_dir, "stylo_full_analysis.json"), pretty = TRUE, auto_unbox = TRUE, null = "null")
cat("Wrote", file.path(out_dir, "stylo_full_analysis.json"), "\n")
