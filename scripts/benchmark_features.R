# Quick benchmark: MFW vs stopwords vs PCA on JAMS holdout
library(stylo)

train <- "corpus_classify/reference_research/balanced"
test <- "corpus_classify/jams_quadrant"
sw <- stopwords::stopwords("en", source = "snowball")
style_labels <- c(
  "geometric__geometric_style__masur_schleimer_disk_complex" = "geometric",
  "geometric__algebraic_style__bateman_katz_cap_sets" = "algebraic",
  "algebraic__geometric_style__dritschel_mccullough_rational_dilation" = "geometric",
  "algebraic__algebraic_style__hrushovski_approx_subgroups" = "algebraic"
)

score <- function(r) {
  pred <- setNames(as.character(r$predicted), rownames(r$frequencies.test.set))
  sum(pred[names(style_labels)] == style_labels)
}

run <- function(label, ...) {
  cat(sprintf("%-30s", label))
  r <- classify(
    gui = FALSE,
    training.corpus.dir = train,
    test.corpus.dir = test,
    write.png.file = FALSE,
    ...
  )
  cat(score(r), "/4\n")
  r
}

cat("JAMS style-axis holdout:\n")
results <- list()
results[["stopwords175 + Delta"]] <- run("stopwords175 + Delta", mfw = length(sw), culling = 0, features = sw, classification.method = "delta")
results[["mfw100 cull20 + Delta"]] <- run("mfw100 cull20 + Delta", mfw = 100, culling = 20, classification.method = "delta")
results[["mfw100 cull40 + Delta"]] <- run("mfw100 cull40 + Delta", mfw = 100, culling = 40, classification.method = "delta")
results[["mfw200 cull20 + Delta"]] <- run("mfw200 cull20 + Delta", mfw = 200, culling = 20, classification.method = "delta")
results[["mfw500 cull20 + Delta"]] <- run("mfw500 cull20 + Delta", mfw = 500, culling = 20, classification.method = "delta")

cat("\nPer-paper predictions (style axis):\n")
for (nm in names(results)) {
  r <- results[[nm]]
  pred <- setNames(as.character(r$predicted), rownames(r$frequencies.test.set))
  cat(nm, ":", paste(names(style_labels), pred[names(style_labels)], sep = "=", collapse = ", "), "\n")
}

pca_holdout <- function(mfw, cull, npc, features = NULL) {
  args <- list(
    gui = FALSE,
    training.corpus.dir = train,
    test.corpus.dir = test,
    write.png.file = FALSE,
    mfw = mfw,
    culling = cull,
    classification.method = "delta"
  )
  if (!is.null(features)) args$features <- features
  r <- do.call(classify, args)
  feats <- r$features.actually.used
  Xtr <- r$frequencies.training.set[, feats, drop = FALSE]
  Xte <- r$frequencies.test.set[, feats, drop = FALSE]
  sdv <- apply(Xtr, 2, sd)
  keep <- sdv > 1e-8
  Xtr <- Xtr[, keep, drop = FALSE]
  Xte <- Xte[, keep, drop = FALSE]
  labs <- ifelse(grepl("^geometric", rownames(Xtr)), "geometric", "algebraic")
  pca <- prcomp(rbind(Xtr, Xte), center = TRUE, scale. = TRUE)
  ntr <- nrow(Xtr)
  k <- min(npc, ncol(pca$x))
  scores_tr <- pca$x[1:ntr, 1:k, drop = FALSE]
  scores_te <- pca$x[(ntr + 1):nrow(pca$x), 1:k, drop = FALSE]
  cent <- aggregate(scores_tr, by = list(labs), FUN = mean)
  rownames(cent) <- cent$Group.1
  cent <- as.matrix(cent[, -1])
  preds <- vapply(seq_len(nrow(scores_te)), function(i) {
    d <- apply(cent, 1, function(c) sqrt(sum((scores_te[i, ] - c)^2)))
    names(which.min(d))
  }, character(1))
  names(preds) <- rownames(Xte)
  sum(preds[names(style_labels)] == style_labels)
}

cat("\nPCA nearest-centroid:\n")
for (npc in c(2, 5, 10, 20)) {
  acc <- pca_holdout(100, 20, npc)
  cat(sprintf("mfw100 cull20 + PCA-%d centroid %d/4\n", npc, acc))
}

sep <- function(mfw, cull, features = NULL) {
  args <- list(
    gui = FALSE,
    training.corpus.dir = train,
    test.corpus.dir = test,
    write.png.file = FALSE,
    mfw = mfw,
    culling = cull,
    classification.method = "delta"
  )
  if (!is.null(features)) args$features <- features
  r <- do.call(classify, args)
  X <- r$frequencies.training.set[, r$features.actually.used, drop = FALSE]
  labs <- ifelse(grepl("^geometric", rownames(X)), "geometric", "algebraic")
  cg <- colMeans(X[labs == "geometric", , drop = FALSE])
  ca <- colMeans(X[labs == "algebraic", , drop = FALSE])
  mean(abs(cg - ca))
}

cat("\nTraining centroid L1 separation:\n")
cat("  stopwords175:", round(sep(length(sw), 0, sw), 6), "\n")
cat("  mfw100 cull20:", round(sep(100, 20), 6), "\n")
cat("  mfw500 cull20:", round(sep(500, 20), 6), "\n")
