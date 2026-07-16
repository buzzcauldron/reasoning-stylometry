# stylo::classify() always takes the class label from the filename segment
# before the FIRST underscore (see stylo:::run_classify, `gsub("_.*", "", ...)`).
# corpus_classify/jams_quadrant/ and jams_excerpts/ are named content-first
# (`{content}__{style}_style__...`), which is what the CONTENT classifier needs.
# The STYLE classifier needs the same 4 target papers with style as the leading
# segment. This script builds those style-first copies (text is untouched, only
# the filename field order changes) from the same source of truth used
# everywhere else: R/jams_metadata.R's JAMS_PAPERS list.
#
# Run from project root: Rscript scripts/make_style_leading_targets.R
# STYLO_LEMMATIZED=1 builds from the lemmatized sibling JAMS dirs (see
# lemmatize_corpus.py) into the matching _lemmatized style-first dirs.
source("R/jams_metadata.R")
suffix <- if (identical(Sys.getenv("STYLO_LEMMATIZED"), "1")) "_lemmatized" else ""

build_style_first <- function(src_dir, dest_dir, stem_fn) {
  dir.create(dest_dir, showWarnings = FALSE, recursive = TRUE)
  for (old in list.files(dest_dir, pattern = "\\.txt$", full.names = TRUE)) file.remove(old)
  for (p in JAMS_PAPERS) {
    stem <- stem_fn(p)
    src <- file.path(src_dir, paste0(stem, ".txt"))
    if (!file.exists(src)) stop("Missing expected source file: ", src)
    dest_name <- paste0(p$style_label, "__", p$content_label, "_content__", stem, ".txt")
    file.copy(src, file.path(dest_dir, dest_name), overwrite = TRUE)
  }
}

build_style_first(
  paste0("corpus_classify/jams_quadrant", suffix), paste0("corpus_classify/jams_quadrant_style_first", suffix),
  function(p) STEM_TO_ROLLING[[p$file_stem]]
)
build_style_first(
  paste0("corpus_classify/jams_excerpts", suffix), paste0("corpus_classify/jams_excerpts_style_first", suffix),
  function(p) p$file_stem
)

cat("Wrote corpus_classify/jams_quadrant_style_first", suffix, "/ and corpus_classify/jams_excerpts_style_first", suffix, "/\n", sep = "")
