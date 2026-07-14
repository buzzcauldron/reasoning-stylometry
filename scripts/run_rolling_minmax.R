# Rolling-window classification of an out-of-subject academic paper
# (MinMax real-time scheduling) against a geometric-vs-algebraic reference
# set built from subject-matched proof pairs (Pythagorean theorem, law of
# cosines, Heron's formula, AM-GM inequality, sum of first n integers,
# quadratic formula). Stopword-only features so the signal is style
# (function words), not topic vocabulary -- the reference set never saw
# scheduling-theory content, so this is a genuine content-generalization
# test of geometric vs. algebraic reasoning style.
#
# Run from project root: Rscript scripts/run_rolling_minmax.R
library(stylo)

stopword_list <- stopwords::stopwords("en", source = "snowball")

out_dir <- "output"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

result <- rolling.classify(
  gui = FALSE,
  training.corpus.dir = "corpus_classify/reference_set",
  test.corpus.dir = "corpus_classify/rolling_target",
  slice.size = 250,
  slice.overlap = 150,
  mfw = length(stopword_list),
  culling = 0,
  features = stopword_list,
  classification.method = "delta",
  write.png.file = TRUE,
  custom.graph.title = "Rolling classification: MinMax scheduling paper vs geometric/algebraic reference (stopwords)"
)

cat("\n=== Slice-by-slice classification ===\n")
print(result$classification.results)

counts <- sort(table(as.character(result$classification.results)), decreasing = TRUE)
cat("\n=== Slice attribution counts ===\n")
print(counts)
cat("\nShare algebraic:", round(counts["algebraic"] / sum(counts), 3), "\n")

for (path in list.files(".", pattern = "^rolling-delta-.*\\.png$", full.names = TRUE)) {
  file.rename(path, file.path(out_dir, "rolling_minmax_stopwords.png"))
}

saveRDS(result, file.path(out_dir, "rolling_minmax_result.rds"))
