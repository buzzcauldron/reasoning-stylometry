#!/usr/bin/env Rscript
# Extract plain text from JAMS PDFs for stylo corpus (R; optional pdftools).
out_dir <- "corpus_classify/jams_quadrant"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

pdfs <- c(
  "geometric__geometric_style__masur_schleimer_disk_complex" = "/tmp/masur_disk.pdf",
  "geometric__algebraic_style__bateman_katz_cap_sets" = "/tmp/bateman_cap.pdf",
  "algebraic__geometric_style__dritschel_mccullough_rational_dilation" = "/tmp/dritschel.pdf",
  "algebraic__algebraic_style__hrushovski_approx_subgroups" = "/tmp/hrushovski.pdf"
)

clean_text <- function(text) {
  lines <- strsplit(text, "\n", fixed = TRUE)[[1]]
  lines <- trimws(lines)
  lines <- lines[nzchar(lines)]
  lines <- lines[!(grepl("^[0-9]{1,4}$", lines))]
  paste(lines, collapse = "\n\n")
}

extract_one <- function(pdf_path) {
  if (requireNamespace("pdftools", quietly = TRUE)) {
    pages <- pdftools::pdf_text(pdf_path)
    return(clean_text(paste(pages, collapse = "\n")))
  }
  # Fallback: pdftotext if available
  if (nzchar(Sys.which("pdftotext"))) {
    tmp <- tempfile(fileext = ".txt")
    status <- system2("pdftotext", c("-layout", pdf_path, tmp), stdout = FALSE, stderr = FALSE)
    if (status == 0 && file.exists(tmp)) {
      txt <- paste(readLines(tmp, warn = FALSE), collapse = "\n")
      unlink(tmp)
      return(clean_text(txt))
    }
  }
  NULL
}

for (stem in names(pdfs)) {
  out <- file.path(out_dir, paste0(stem, ".txt"))
  if (file.exists(out) && file.info(out)$size > 1000) {
    message(stem, ": using existing ", out)
    next
  }
  pdf <- pdfs[[stem]]
  if (!file.exists(pdf)) {
    warning("PDF missing: ", pdf, " — keep existing ", out)
    next
  }
  text <- extract_one(pdf)
  if (is.null(text) || !nzchar(text)) {
    stop("Cannot extract ", pdf, ". Install pdftools (install.packages('pdftools')) or pdftotext.")
  }
  writeLines(text, out, useBytes = TRUE)
  message(stem, ": ", length(strsplit(text, "\\s+")[[1]]), " words -> ", out)
}
