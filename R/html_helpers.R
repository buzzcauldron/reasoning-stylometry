# HTML helpers for JAMS quadrant reports (pure R, no Python).

html_escape <- function(s) {
  s <- gsub("&", "&amp;", s, fixed = TRUE)
  s <- gsub("<", "&lt;", s, fixed = TRUE)
  s <- gsub(">", "&gt;", s, fixed = TRUE)
  s <- gsub("\"", "&quot;", s, fixed = TRUE)
  s
}

bar_html <- function(value) {
  if (value >= 0) {
    left <- 50
    width <- value * 50
    color <- "#2b7bba"
  } else {
    left <- 50 + value * 50
    width <- abs(value) * 50
    color <- "#c0504d"
  }
  sprintf(
    '<div class="bar"><div class="civ"></div><div class="fill" style="left:%.1f%%;width:%.1f%%;background:%s"></div><span class="barval">%+.2f</span></div>',
    left, width, color, value
  )
}

chips_html <- function(active, kind = "style") {
  if (kind == "style") {
    parts <- vapply(seq_len(nrow(STYLE_FEATURES)), function(i) {
      name <- STYLE_FEATURES$name[i]
      fam <- STYLE_FEATURES$family[i]
      cls <- if (name %in% active) fam else paste0(fam, " off")
      sprintf('<span class="chip %s">%s</span>', cls, html_escape(name))
    }, character(1))
    paste0('<div class="chips">', paste(parts, collapse = ""), "</div>")
  } else {
    parts <- vapply(OBJECT_CATS, function(name) {
      if (!name %in% names(active)) return("")
      tag <- unname(active[name])
      if (length(tag) == 0 || is.na(tag) || !nzchar(tag)) return("")
      sprintf('<span class="ochip %s">%s</span>', tag, html_escape(name))
    }, character(1))
    paste0('<div class="chips">', paste(parts[parts != ""], collapse = ""), "</div>")
  }
}

tex_para <- function(tex) paste0("<p>", tex, "</p>")

tag_html <- function(label, ok = NULL) {
  cls <- substr(label, 1, 3)
  extra <- if (!is.null(ok)) {
    sprintf(' <span class="tag %s">%s</span>', if (ok) "ok" else "no", if (ok) "\u2713" else "\u2717")
  } else ""
  sprintf('<span class="tag %s">%s</span>%s', cls, html_escape(label), extra)
}

write_html <- function(path, html) {
  dir.create(dirname(path), showWarnings = FALSE, recursive = TRUE)
  writeLines(html, path, useBytes = TRUE)
  message("Wrote ", path)
}

img_data_uri <- function(path) {
  if (!file.exists(path)) return("")
  raw <- readBin(path, "raw", file.info(path)$size)
  b64 <- jsonlite::base64_enc(raw)
  paste0("data:image/png;base64,", b64)
}

CROSS_WITHIN_CSS <- "
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#f4f5f7;color:#1a1a1a}
 header{background:#22303f;color:#fff;padding:20px 28px}
 header h1{margin:0 0 6px;font-size:20px}
 header p{margin:0;opacity:.85;font-size:13px}
 .wrap{max-width:1100px;margin:0 auto;padding:24px 20px 48px}
 h2.bg{font-size:15px;color:#22303f;margin:28px 0 12px;padding:8px 12px;background:#eef1f4;border-radius:6px}
 .card{background:#fff;border:1px solid #dce1e6;border-radius:10px;margin:16px 0;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.05)}
 .phdr{background:#eef1f4;padding:10px 16px;border-bottom:1px solid #dce1e6;font-size:12.5px;color:#556}
 .pid{font-weight:700;color:#22303f;margin-right:8px}
 .cols{display:grid;grid-template-columns:1fr 1fr;gap:0}
 @media(max-width:800px){.cols{grid-template-columns:1fr}}
 .col{padding:14px 16px;border-right:1px solid #eceff2}
 .col:last-child{border-right:none}
 .sidehdr{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8794a1;font-weight:700;margin-bottom:8px}
 .para{font-size:13.5px;line-height:1.55}
 .rlabel{font-size:11px;color:#667;margin:10px 0 3px}
 .bar{position:relative;height:18px;background:#eef1f4;border-radius:3px;margin:4px 0 8px}
 .bar .civ{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#ccc}
 .bar .fill{position:absolute;top:0;bottom:0;border-radius:3px}
 .barval{position:absolute;right:6px;top:1px;font-size:10px;color:#556}
 .chips{display:flex;flex-wrap:wrap;gap:4px;margin:4px 0}
 .chip,.ochip{font-size:10px;padding:2px 6px;border-radius:8px;background:#eef1f4;color:#667}
 .chip.spatial,.ochip.geo{background:#e7f0f8;color:#1c5580}
 .chip.symbolic,.ochip.alg{background:#faeae9;color:#8a3936}
 .chip.off{opacity:.35}
 .summarybox{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:16px 18px;margin:0 0 20px}
 .tag{display:inline-block;font-size:10.5px;padding:2px 7px;border-radius:10px;font-weight:600}
 .tag.geo{background:#e7f0f8;color:#1c5580}.tag.alg{background:#faeae9;color:#8a3936}
 .tag.ok{background:#e8f5ec;color:#1a6631}.tag.no{background:#fdecea;color:#8a2a24}
 .mstat{display:block;margin-top:6px;font-size:12px;color:#667}
"

FULL_REPORT_CSS <- "
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:0;background:#f4f5f7;color:#1a1a1a}
 header{background:#22303f;color:#fff;padding:24px 32px}
 header h1{margin:0 0 8px;font-size:22px}
 header p{margin:0;opacity:.85;font-size:13.5px;max-width:980px;line-height:1.5}
 .wrap{max-width:1200px;margin:0 auto;padding:28px 22px 60px}
 h2.sec{margin:40px 0 14px;font-size:17px;color:#22303f;border-bottom:2px solid #c9d2db;padding-bottom:8px}
 h3.sub{margin:22px 0 10px;font-size:14px;color:#334}
 .grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:18px 0}
 .stat{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:16px 18px}
 .stat .lbl{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:#8794a1;font-weight:700}
 .stat .val{font-size:26px;font-weight:700;color:#22303f;margin-top:4px}
 .stat .note{font-size:12px;color:#667;margin-top:6px;line-height:1.45}
 .card{background:#fff;border:1px solid #dce1e6;border-radius:10px;margin:18px 0;overflow:hidden}
 .card-hdr{background:#eef1f4;padding:12px 18px;border-bottom:1px solid #dce1e6}
 .card-hdr h3{margin:0;font-size:15px;color:#22303f}
 .card-body{padding:16px 18px}
 .cols2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
 @media(max-width:860px){.cols2{grid-template-columns:1fr}}
 table.data{width:100%;border-collapse:collapse;font-size:12.5px}
 table.data th,table.data td{padding:6px 8px;border-bottom:1px solid #eceff2;text-align:left;vertical-align:top}
 table.data th{background:#f7f9fa;font-size:11px;text-transform:uppercase;color:#667}
 .tag{display:inline-block;font-size:10.5px;padding:2px 7px;border-radius:10px;font-weight:600}
 .tag.geo{background:#e7f0f8;color:#1c5580}.tag.alg{background:#faeae9;color:#8a3936}
 .tag.ok{background:#e8f5ec;color:#1a6631}.tag.no{background:#fdecea;color:#8a2a24}
 .method,.prose{background:#fff;border:1px solid #dce1e6;border-radius:10px;padding:18px 20px;margin:0 0 22px;font-size:13px;line-height:1.65}
 .prose ul.compact{margin:8px 0;padding-left:18px;font-size:13px}
 .health-crit{border-left:4px solid #b83232}.health-warn{border-left:4px solid #c47f00}.health-ok{border-left:4px solid #2d8a4e}
 .badge-crit{background:#fdecea;color:#8a2a24;font-size:10.5px;padding:2px 8px;border-radius:10px;font-weight:700}
 .badge-warn{background:#fff4e5;color:#8a5a00;font-size:10.5px;padding:2px 8px;border-radius:10px;font-weight:700}
 .ci{color:#556;font-size:11.5px}.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}
 .bar{position:relative;height:18px;background:#eef1f4;border-radius:3px;margin:4px 0 8px}
 .bar .civ{position:absolute;left:50%;top:0;bottom:0;width:1px;background:#ccc}
 .bar .fill{position:absolute;top:0;bottom:0;border-radius:3px}
 .barval{position:absolute;right:6px;top:1px;font-size:10px;color:#556}
 .chips{display:flex;flex-wrap:wrap;gap:4px}.chip{font-size:10px;padding:2px 6px;border-radius:8px}
 .chip.spatial{background:#e7f0f8;color:#1c5580}.chip.symbolic{background:#faeae9;color:#8a3936}.chip.off{opacity:.35}
 .excerpt{font-size:13.5px;line-height:1.55;background:#fbfcfd;border:1px solid #eceff2;border-radius:8px;padding:12px 14px}
 .rlabel{font-size:11px;color:#667;margin:10px 0 3px}
 .imgroll{max-width:100%;border:1px solid #dce1e6;border-radius:6px}
 .hist{display:flex;align-items:flex-end;height:72px;gap:2px;margin:8px 0;border:1px solid #e8ebee;padding:8px;background:#fafbfc}
 .hist div{flex:1;background:#5b7a9d;min-width:3px;border-radius:2px 2px 0 0}
"

page_shell <- function(title, subtitle, body, css = CROSS_WITHIN_CSS) {
  paste0(
    "<!doctype html><html><head><meta charset=\"utf-8\">",
    "<script>MathJax={tex:{inlineMath:[[\"\\\\(\",\"\\\\)\"]],displayMath:[[\"\\\\[\",\"\\\\]\"]]}};</script>",
    "<script src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\" async></script>",
    "<style>", css, "</style></head><body>",
    "<header><h1>", html_escape(title), "</h1><p>", html_escape(subtitle), "</p></header>",
    "<div class=\"wrap\">", body, "</div></body></html>"
  )
}

roll_pred <- function(roll, weighted = FALSE) {
  if (weighted && !is.null(roll$confidence_weighted_geo_share)) {
    return(if (roll$confidence_weighted_geo_share > 0.5) "geometric" else "algebraic")
  }
  if (roll$share_geometric > roll$share_algebraic) "geometric" else "algebraic"
}

paper_stem_for <- function(p) STEM_TO_ROLLING[[p$file_stem]]
