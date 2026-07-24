# Sweep of classic stylometric feature families for the STYLE axis, against
# the same train/test harness as run_jams_quadrant.R (balanced_style train,
# 4 JAMS papers style-first test, whole-paper Delta classify only -- no
# rolling/LOO here, this is a fast first-pass comparison). Real mfw.min/
# culling.min parameter names throughout (see run_jams_quadrant.R's history
# for why the fake mfw=/culling= names are a landmine).
#
# Run from project root: Rscript scripts/style_feature_sweep.R [train_dir] [out_json]
suppressMessages(library(stylo))
source("R/jams_metadata.R")

args <- commandArgs(trailingOnly = TRUE)
STYLE_TRAIN_DIR <- if (length(args) >= 1) args[1] else "corpus_classify/reference_research/balanced_style"
OUT_JSON <- if (length(args) >= 2) args[2] else "output/style_feature_sweep.json"
ONLY_CONFIGS <- if (length(args) >= 3) strsplit(args[3], ",")[[1]] else NULL
STYLE_TEST_DIR <- "corpus_classify/jams_quadrant_style_first"
strip_style_first_prefix <- function(x) sub("^[^_]+__[^_]+_content__", "", x)

PUNCT_CHARS <- c(".", ",", ";", ":", "!", "?", "-", "(", ")", "[", "]",
                  "'", "\"", "/", "\\", "=", "+", "<", ">", "%")

configs <- list(
  letters = list(
    mfw.min = 100, mfw.max = 100, mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "c", ngram.size = 1, classification.method = "delta"
  ),
  char_bigrams = list(
    mfw.min = 500, mfw.max = 500, mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "c", ngram.size = 2, classification.method = "delta"
  ),
  char_trigrams = list(
    mfw.min = 500, mfw.max = 500, mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "c", ngram.size = 3, classification.method = "delta"
  ),
  word_bigrams = list(
    mfw.min = 300, mfw.max = 300, mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "w", ngram.size = 2, classification.method = "delta"
  ),
  word_trigrams = list(
    mfw.min = 300, mfw.max = 300, mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "w", ngram.size = 3, classification.method = "delta"
  ),
  punctuation = list(
    mfw.min = length(PUNCT_CHARS), mfw.max = length(PUNCT_CHARS), mfw.incr = 100,
    culling.min = 0, culling.max = 0, culling.incr = 20,
    analyzed.features = "c", ngram.size = 1, classification.method = "delta",
    features = PUNCT_CHARS
  )
)

results <- list()
config_names <- if (is.null(ONLY_CONFIGS)) names(configs) else intersect(names(configs), ONLY_CONFIGS)
for (name in config_names) {
  cat("\n=== config:", name, "===\n")
  cfg <- configs[[name]]
  r <- tryCatch(
    do.call(classify, c(
      list(gui = FALSE, training.corpus.dir = STYLE_TRAIN_DIR, test.corpus.dir = STYLE_TEST_DIR,
           write.png.file = FALSE),
      cfg
    )),
    error = function(e) { cat("ERROR:", conditionMessage(e), "\n"); NULL }
  )
  if (is.null(r)) { results[[name]] <- list(error = TRUE); next }
  rn <- strip_style_first_prefix(rownames(r$frequencies.test.set))
  pred <- setNames(as.character(r$predicted), rn)
  match <- sum(pred[names(EXPERT_STYLE_LABELS)] == EXPERT_STYLE_LABELS)
  cat("predicted:", paste(names(pred), "=", pred, collapse = ", "), "\n")
  cat("match:", match, "/4\n")
  results[[name]] <- list(predicted = as.list(pred), match = match,
                           n_features = length(r$features.actually.used))
}

cat("\n\n########## SWEEP SUMMARY (whole-paper style accuracy) ##########\n")
for (name in names(results)) {
  res <- results[[name]]
  if (isTRUE(res$error)) {
    cat(sprintf("%-15s ERROR\n", name))
  } else {
    cat(sprintf("%-15s %d/4  (%d features actually used)\n", name, res$match, res$n_features))
  }
}
cat(sprintf("%-15s %s (current production config, from last run_jams_quadrant.R run)\n",
            "function_words", "see output/jams_quadrant/stylo_results.json"))

library(jsonlite)
write_json(results, OUT_JSON, auto_unbox = TRUE, pretty = TRUE)
cat("\nWrote", OUT_JSON, "(train_dir:", STYLE_TRAIN_DIR, ")\n")
