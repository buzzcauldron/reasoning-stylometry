# Predict content + style labels for corpus_classify/reference_research/
# mixed_content_holdout/ -- chunks split_mixed_content_holdout.py and
# retag_content_style.py's ambiguous-tie routing set aside because keyword
# tagging couldn't confidently call them (hits both content dictionaries, or
# scored a true tie/no signal on either axis). Recovered from a machine
# (akdeniz) this pipeline was developed on -- original was
# classify_mixed_akdeniz.R, hardcoded to that machine's home directory and
# using the same "fake" mfw=/culling= parameter names run_jams_quadrant.R
# used to have (see that script's history: those names are silently ignored
# by stylo::classify(), and culling actually applied falls back to whatever
# happens to be cached in classify_config.txt). Ported here with real
# parameter names and project-root-relative paths.
#
# Output (output/mixed_content_pseudo_labels.json) is consumed by
# merge_pseudo_labels.py to actually populate chunks_pseudo_labeled/ --
# that merge step itself was never found as a saved script anywhere this
# session looked (hal, akdeniz, bridges2, both bash histories), so
# merge_pseudo_labels.py is a from-scratch reconstruction, not a recovered
# original.
#
# Run from project root: Rscript scripts/classify_mixed_content.R
library(stylo)
library(jsonlite)

dir.create("output", showWarnings = FALSE, recursive = TRUE)

stopword_list <- stopwords::stopwords("en", source = "snowball")
stylo_args <- list(
  mfw.min = length(stopword_list), mfw.max = length(stopword_list), mfw.incr = 100,
  culling.min = 0, culling.max = 0, culling.incr = 20,
  features = stopword_list,
  classification.method = "delta",
  analyzed.features = "w",
  ngram.size = 1
)

# mixed_content_holdout_{content,style}_leading files are named
# `{content}__{style}__{arxiv_slug}__chunkNNN.txt` / `{style}__{content}__...`
# (split_mixed_content_holdout.py) -- canonical_key strips the leading
# content/style pair (about to be replaced by this script's own prediction)
# down to the arxiv_slug__chunk_suffix identifier shared by both views.
canonical_key <- function(rowname) {
  parts <- strsplit(rowname, "__")[[1]]
  n <- length(parts)
  paste(parts[(n - 1):n], collapse = "__")
}

cat("=== classifying mixed content (content axis) ===\n")
content_result <- do.call(classify, c(list(
  gui = FALSE,
  training.corpus.dir = "corpus_classify/reference_research/balanced_content",
  test.corpus.dir = "corpus_classify/reference_research/mixed_content_holdout_content_leading",
  write.png.file = FALSE
), stylo_args))

content_pred <- setNames(as.character(content_result$predicted), rownames(content_result$frequencies.test.set))
names(content_pred) <- vapply(names(content_pred), canonical_key, character(1))
saveRDS(content_result, "output/mixed_content_classify_content.rds")
cat("content predictions:\n"); print(table(content_pred))

cat("\n=== classifying mixed content (style axis) ===\n")
style_result <- do.call(classify, c(list(
  gui = FALSE,
  training.corpus.dir = "corpus_classify/reference_research/balanced_style",
  test.corpus.dir = "corpus_classify/reference_research/mixed_content_holdout_style_leading",
  write.png.file = FALSE
), stylo_args))

style_pred <- setNames(as.character(style_result$predicted), rownames(style_result$frequencies.test.set))
names(style_pred) <- vapply(names(style_pred), canonical_key, character(1))
saveRDS(style_result, "output/mixed_content_classify_style.rds")
cat("style predictions:\n"); print(table(style_pred))

keys <- union(names(content_pred), names(style_pred))
merged <- lapply(keys, function(k) list(
  key = k,
  predicted_content = unname(content_pred[k]),
  predicted_style = unname(style_pred[k])
))
names(merged) <- keys

write_json(merged, "output/mixed_content_pseudo_labels.json", auto_unbox = TRUE, pretty = TRUE)
cat("\nWrote output/mixed_content_pseudo_labels.json with", length(merged), "entries\n")
