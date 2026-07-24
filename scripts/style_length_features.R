# Word-length / sentence-length / paragraph-length feature classifiers for
# the STYLE axis. These aren't stylo MFW/n-gram feature types, so this is a
# hand-rolled histogram-feature + Delta-style classifier rather than a
# stylo::classify() call: for each document, compute a small fixed-length
# histogram (e.g. share of 1-letter, 2-letter, ... words), z-score each
# feature using the TRAINING corpus's own mean/sd (Burrows-Delta-style
# standardization), then classify each of the 4 JAMS test papers by both
# nearest training-document (1-NN, matching stylo's actual k=1 behavior
# elsewhere in this pipeline) and nearest class-centroid (mean of z-scored
# training vectors per class -- more robust for a feature space this low-
# dimensional, reported alongside 1-NN rather than instead of it).
#
# Sentence splitting is a simple regex heuristic ([.!?] followed by
# whitespace + capital letter) -- it will misfire on abbreviations
# ("e.g.", "resp.") and numbered theorem/lemma references ("Theorem 3.2."),
# which are common in this corpus. Treat these results as a rough first
# pass, not a precise measurement.
#
# Run from project root: Rscript scripts/style_length_features.R
source("R/jams_metadata.R")

STYLE_TRAIN_DIR <- "corpus_classify/reference_research/balanced_style"
STYLE_TEST_DIR <- "corpus_classify/jams_quadrant_style_first"

read_words <- function(path) {
  text <- paste(readLines(path, warn = FALSE), collapse = " ")
  words <- unlist(strsplit(text, "[^A-Za-z]+"))
  words[nchar(words) > 0]
}

word_length_hist <- function(words) {
  lens <- pmin(nchar(words), 12)  # cap at 12+ bucket
  counts <- tabulate(lens, nbins = 12)
  counts / sum(counts)
}

sentence_lengths <- function(text) {
  # crude sentence split: [.!?] followed by whitespace + capital letter
  parts <- strsplit(text, "(?<=[.!?])\\s+(?=[A-Z])", perl = TRUE)[[1]]
  vapply(parts, function(s) length(unlist(strsplit(s, "\\s+"))), integer(1))
}

sentence_length_features <- function(text) {
  lens <- sentence_lengths(text)
  lens <- lens[lens > 0]
  # sd() of a single value is NA in R (undefined), not 0 -- a document with
  # only one detected "sentence" (short chunk, or crude regex missed all
  # boundaries) would otherwise poison every downstream distance calculation.
  if (length(lens) == 0) return(c(mean = 0, sd = 0, median = 0))
  if (length(lens) == 1) return(c(mean = lens[1], sd = 0, median = lens[1]))
  c(mean = mean(lens), sd = sd(lens), median = median(as.numeric(lens)))
}

paragraph_lengths <- function(text) {
  parts <- strsplit(text, "\\n\\s*\\n")[[1]]
  vapply(parts, function(p) length(unlist(strsplit(trimws(p), "\\s+"))), integer(1))
}

paragraph_length_features <- function(text) {
  lens <- paragraph_lengths(text)
  lens <- lens[lens > 0]
  if (length(lens) == 0) return(c(mean = 0, sd = 0, median = 0))
  if (length(lens) == 1) return(c(mean = lens[1], sd = 0, median = lens[1]))
  c(mean = mean(lens), sd = sd(lens), median = median(as.numeric(lens)))
}

read_text <- function(path) paste(readLines(path, warn = FALSE), collapse = "\n")

compute_features <- function(path, feature_type) {
  if (feature_type == "word_length") {
    return(word_length_hist(read_words(path)))
  }
  text <- read_text(path)
  if (feature_type == "sentence_length") return(sentence_length_features(text))
  if (feature_type == "paragraph_length") return(paragraph_length_features(text))
  stop("unknown feature_type")
}

classify_by_features <- function(feature_type) {
  train_files <- list.files(STYLE_TRAIN_DIR, pattern = "\\.txt$", full.names = TRUE)
  train_labels <- ifelse(grepl("^geometric", basename(train_files)), "geometric", "algebraic")

  cat(sprintf("\n=== %s: computing features for %d training docs ===\n", feature_type, length(train_files)))
  train_mat <- t(vapply(train_files, function(f) compute_features(f, feature_type), numeric(length(compute_features(train_files[1], feature_type)))))

  mu <- colMeans(train_mat)
  sdv <- apply(train_mat, 2, sd)
  sdv[sdv == 0] <- 1
  train_z <- scale(train_mat, center = mu, scale = sdv)

  geo_idx <- which(train_labels == "geometric")
  alg_idx <- which(train_labels == "algebraic")
  geo_centroid <- colMeans(train_z[geo_idx, , drop = FALSE])
  alg_centroid <- colMeans(train_z[alg_idx, , drop = FALSE])

  test_files <- list.files(STYLE_TEST_DIR, pattern = "\\.txt$", full.names = TRUE)
  canonical <- function(x) sub("^[^_]+__[^_]+_content__", "", sub("\\.txt$", "", basename(x)))

  match <- 0
  for (f in test_files) {
    feat <- compute_features(f, feature_type)
    z <- (feat - mu) / sdv
    d_geo_centroid <- sqrt(sum((z - geo_centroid)^2))
    d_alg_centroid <- sqrt(sum((z - alg_centroid)^2))
    pred_centroid <- if (d_geo_centroid < d_alg_centroid) "geometric" else "algebraic"

    dists_1nn <- sqrt(rowSums((train_z - matrix(z, nrow = nrow(train_z), ncol = length(z), byrow = TRUE))^2))
    nn_idx <- which.min(dists_1nn)
    pred_1nn <- train_labels[nn_idx]

    stem <- canonical(f)
    expert <- EXPERT_STYLE_LABELS[stem]
    if (pred_centroid == expert) match <- match + 1
    cat(sprintf("  %-70s expert=%-10s pred_centroid=%-10s (d_geo=%.3f d_alg=%.3f)  pred_1nn=%-10s\n",
                stem, expert, pred_centroid, d_geo_centroid, d_alg_centroid, pred_1nn))
  }
  cat(sprintf("%s: whole-paper match (centroid rule) = %d/4\n", feature_type, match))
  match
}

results <- list()
for (ft in c("word_length", "sentence_length", "paragraph_length")) {
  results[[ft]] <- classify_by_features(ft)
}

cat("\n\n########## LENGTH-FEATURE SUMMARY ##########\n")
for (ft in names(results)) cat(sprintf("%-20s %d/4\n", ft, results[[ft]]))
