# Classify non-JAMS test papers (unseen by the training corpus, no expert
# content/style labels) using the current best-validated configs: content =
# stopwords175+Delta, style = tightened 147-word POS-filtered function-word
# list. Adapted from classify_new_papers_v2.R (recovered from akdeniz,
# 2026-07-17) -- ported to project-root-relative paths and real
# mfw.min/culling.min parameter names (see run_jams_quadrant.R's history for
# why the fake mfw=/culling= names are a landmine: classify_config.txt,
# a git-tracked settings cache, silently supplies whatever was last set
# there instead).
#
# Run from project root: Rscript scripts/classify_new_papers.R
suppressMessages(library(stylo))

test_dir <- "output/new_paper_test"
dir.create(test_dir, showWarnings = FALSE, recursive = TRUE)
for (old in list.files(test_dir, pattern = "\\.txt$", full.names = TRUE)) file.remove(old)
file.copy("stokes_overdetermination.txt", file.path(test_dir, "unknown__stokes_nonlinear_overdetermination.txt"), overwrite = TRUE)
file.copy("aeroelastic_uav_review.txt", file.path(test_dir, "unknown__aeroelastic_uav_control_review.txt"), overwrite = TRUE)

run_axis <- function(axis, train_dir, cfg_args) {
  work_dir <- file.path("output/new_paper_workdirs", sprintf("%s_%d", axis, Sys.getpid()))
  dir.create(work_dir, showWarnings = FALSE, recursive = TRUE)
  old_wd <- getwd()
  setwd(work_dir)
  r <- do.call(classify, c(
    list(gui = FALSE, training.corpus.dir = file.path(old_wd, train_dir),
         test.corpus.dir = file.path(old_wd, test_dir), write.png.file = FALSE),
    cfg_args
  ))
  setwd(old_wd)
  unlink(work_dir, recursive = TRUE)
  saveRDS(r, sprintf("output/new_paper_classify_%s.rds", axis))
  data.frame(paper = rownames(r$frequencies.test.set), predicted = as.character(r$predicted),
             axis = axis, stringsAsFactors = FALSE)
}

stopword_list <- stopwords::stopwords("en", source = "snowball")
content_args <- list(
  mfw.min = length(stopword_list), mfw.max = length(stopword_list), mfw.incr = 100,
  culling.min = 0, culling.max = 0, culling.incr = 20,
  features = stopword_list, classification.method = "delta"
)

style_words <- readLines("corpus_classify/style_function_words.txt")
style_args <- list(
  mfw.min = length(style_words), mfw.max = length(style_words), mfw.incr = 100,
  culling.min = 0, culling.max = 0, culling.incr = 20,
  features = style_words, classification.method = "delta"
)

res_content <- run_axis("content", "corpus_classify/reference_research/balanced_content", content_args)
res_style <- run_axis("style", "corpus_classify/reference_research/balanced_style", style_args)

result <- rbind(res_content, res_style)
cat("\n=== RESULT (content=stopwords175, style=tightened POS-filtered 147, current corpus) ===\n")
print(result)
write.csv(result, "output/new_paper_classification.csv", row.names = FALSE)
