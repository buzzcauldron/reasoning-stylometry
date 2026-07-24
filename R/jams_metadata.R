# Expert v4 metadata for four JAMS quadrant papers (independent of stylo).

# Wilson score interval for a binomial proportion -- used across rolling-
# classification scripts to decide whether a rolling majority is a real lean
# or a coin toss, rather than just picking whichever side has more slices
# (a 51/49 split on 20 slices is not a meaningful "majority", it's noise).
wilson_ci <- function(k, n, z = 1.96) {
  if (n <= 0) return(c(NA_real_, NA_real_))
  p <- k / n
  denom <- 1 + z^2 / n
  centre <- (p + z^2 / (2 * n)) / denom
  margin <- z * sqrt((p * (1 - p) + z^2 / (4 * n)) / n) / denom
  c(max(0, centre - margin), min(1, centre + margin))
}

# "coin_toss" whenever the 95% Wilson CI for the geometric share straddles
# 0.5 -- i.e. the rolling result can't distinguish this paper from a fair
# coin at that slice count. Otherwise, whichever side has the majority.
rolling_label <- function(n_geo, n_total) {
  if (n_total == 0) return("coin_toss")
  ci <- wilson_ci(n_geo, n_total)
  if (ci[1] <= 0.5 && ci[2] >= 0.5) return("coin_toss")
  if (n_geo / n_total > 0.5) "geometric" else "algebraic"
}

STEM_TO_ROLLING <- c(
  "geometric__geometric_style__masur_schleimer" = "geometric__geometric_style__masur_schleimer_disk_complex",
  "geometric__algebraic_style__bateman_katz" = "geometric__algebraic_style__bateman_katz_cap_sets",
  "algebraic__geometric_style__dritschel_mccullough" = "algebraic__geometric_style__dritschel_mccullough_rational_dilation",
  "algebraic__algebraic_style__hrushovski" = "algebraic__algebraic_style__hrushovski_approx_subgroups"
)

STYLE_FEATURES <- data.frame(
  name = c(
    "position", "deformation", "local_global", "visualizable", "dynamic_process",
    "symbolic_transf", "syntactic_deriv", "categorical_functorial", "approximation_estimation",
    "semantic_instantiation", "analogy_transfer"
  ),
  family = c(
    "spatial", "spatial", "spatial", "spatial", "spatial",
    "symbolic", "symbolic", "symbolic", "symbolic",
    "cross", "cross"
  ),
  stringsAsFactors = FALSE
)

OBJECT_CATS <- c(
  "function_map", "equation_ineq", "group_ring", "set_family", "space_shape",
  "metric", "topological", "ambient_space_or_set", "calculus", "polytope_lattice"
)

JAMS_PAPERS <- list(
  list(
    key = "masur", pid = "\u2460",
    file_stem = "geometric__geometric_style__masur_schleimer",
    title = "The geometry of the disk complex",
    authors = "Masur & Schleimer",
    journal = "JAMS 26 (2012)",
    doi = "10.1090/s0894-0347-2012-00742-5",
    quadrant = "Geometric content \u00d7 Geometric style",
    content_label = "geometric", style_label = "geometric",
    excerpt_tex = paste(
      "Let $\\beta''$ and $\\gamma''$ be the geodesic representatives of $\\beta'$ and $\\gamma'$.",
      "Since $\\beta$ and $\\tau(\\beta)$ meet transversely, $\\beta''$ has length in $\\sigma$ strictly",
      "smaller than $2\\ell_\\sigma(\\beta)$. Similarly the length of $\\gamma''$ is strictly smaller",
      "than $2\\ell_\\sigma(\\gamma)$. Suppose that $\\beta''$ is shorter then $\\gamma''$. It follows",
      "that $\\beta''$ strictly shorter than $\\alpha$. If $\\beta''$ is embedded then this contradicts",
      "the assumption that $\\alpha$ was shortest. If $\\beta''$ is not embedded then there is an",
      "embedded curve $\\beta'''$ inside of a regular neighborhood of $\\beta''$ which is again",
      "essential, non-peripheral, and has geodesic representative shorter than $\\beta''$.",
      "This is our final contradiction and the claim is proved."
    ),
    holistic = 0.84, style_axis = 0.82, content_axis = 0.85,
    style_on = c("position", "local_global", "visualizable", "dynamic_process"),
    objects = c(space_shape = "geo", topological = "geo", metric = "geo"),
    afc_side = "LEFT", afc_pct = 100, afc_consistency = 1.00
  ),
  list(
    key = "bateman", pid = "\u2461",
    file_stem = "geometric__algebraic_style__bateman_katz",
    title = "New bounds on cap sets",
    authors = "Bateman & Katz",
    journal = "JAMS 25 (2011)",
    doi = "10.1090/s0894-0347-2011-00725-x",
    quadrant = "Geometric content \u00d7 Algebraic style",
    content_label = "geometric", style_label = "algebraic",
    excerpt_tex = paste(
      "We introduce the Fourier transforms of the balanced function of the hyperplanes $H_{x_{\\alpha}}$",
      "setting $f_{\\alpha}(z)=\\frac{1}{3^N}\\sum_{x\\in F_3^N}(1_{H_{x_{\\alpha}}}(y)-\\frac{1}{3})e(y\\cdot z)$.",
      "Then we use the standard Fourier identity",
      "$\\sum_{y\\in F_3^N}\\Pi_{\\alpha=1}^4(1_{H_{x_{\\alpha}}}(y)-\\frac{1}{3})",
      "=3^N\\sum_{z_1+z_2+z_3+z_4=0}f_1(z_1)f_2(z_2)f_3(z_3)f_4(z_4)$.",
      "We observe that $f_j(z_j)$ vanishes unless $z_j=\\pm x_j$."
    ),
    holistic = -0.12, style_axis = -0.78, content_axis = 0.42,
    style_on = c("symbolic_transf", "syntactic_deriv", "approximation_estimation"),
    objects = c(function_map = "neu", equation_ineq = "neu", set_family = "neu", group_ring = "alg"),
    afc_side = "RIGHT", afc_pct = 100, afc_consistency = 1.00
  ),
  list(
    key = "dritschel", pid = "\u2462",
    file_stem = "algebraic__geometric_style__dritschel_mccullough",
    title = "The failure of rational dilation on a triply connected domain",
    authors = "Dritschel & McCullough",
    journal = "JAMS 18 (2005)",
    doi = "10.1090/s0894-0347-05-00491-1",
    quadrant = "Algebraic content \u00d7 Geometric style",
    content_label = "algebraic", style_label = "geometric",
    excerpt_tex = paste(
      "The cone $\\mathcal C$ is a convex subset of $\\mathcal P$ not containing $I-\\rho^2 F(z)F(w)^*$",
      "and, by Lemma absorb, $I$ is an internal point of $\\mathcal C$. Hence, there exists a nonconstant",
      "linear functional $\\lambda:\\mathcal P\\to\\mathbb C$ so that $\\lambda\\ge 0$ on $\\mathcal C$ and",
      "$\\lambda(I-\\rho^2 F(z)F(w)^*)\\le 0$; we have $\\lambda(I)>0$, as otherwise, from Lemma absorb,",
      "$\\lambda(H(z)H(w)^*)=0$ for all $H$ and hence $\\lambda=0$ (see, for example, Holmes, \\S11.E)."
    ),
    holistic = -0.24, style_axis = 0.38, content_axis = -0.78,
    style_on = c("position", "local_global", "symbolic_transf"),
    objects = c(function_map = "neu", equation_ineq = "neu", set_family = "neu", ambient_space_or_set = "neu"),
    afc_side = "LEFT", afc_pct = 88, afc_consistency = 0.88
  ),
  list(
    key = "hrushovski", pid = "\u2463",
    file_stem = "algebraic__algebraic_style__hrushovski",
    title = "Stable group theory and approximate subgroups",
    authors = "Hrushovski",
    journal = "JAMS 25 (2011)",
    doi = "10.1090/s0894-0347-2011-00708-x",
    quadrant = "Algebraic content \u00d7 Algebraic style",
    content_label = "algebraic", style_label = "algebraic",
    excerpt_tex = paste(
      "We will need some lemmas on finite generation. First, if $E$ is a finitely generated group,",
      "$N$ a normal subgroup with $E/N$ finitely presented, then $N$ is finitely generated as a",
      "normal subgroup. (In particular when $E/N$ is finite, this implies the finite generation of $N$,",
      "a well-known statement used above.) This in fact valid for any equational class: If $E$ is finitely",
      "generated and $N$ is a congruence with $E/N$ finitely presented, then $N$ is finitely generated",
      "as a congruence. Indeed let $F$ be a finitely generated free algebra in this equational class,",
      "and $h:F\\to E$ a surjective homomorphism. Let $g:F\\to E/N$ be the composition $F\\to E\\to E/N$.",
      "Since $E/N$ is finitely presented, $g$ has a finitely generated kernel $K$. Thus $N=h(K)$ is",
      "finitely generated."
    ),
    holistic = -0.90, style_axis = -0.88, content_axis = -0.92,
    style_on = c("syntactic_deriv", "categorical_functorial"),
    objects = c(group_ring = "alg", set_family = "neu", function_map = "neu"),
    afc_side = "RIGHT", afc_pct = 100, afc_consistency = 1.00
  )
)

EXPERT_STYLE_LABELS <- setNames(
  vapply(JAMS_PAPERS, function(p) p$style_label, character(1)),
  vapply(JAMS_PAPERS, function(p) STEM_TO_ROLLING[[p$file_stem]], character(1))
)

EXPERT_CONTENT_LABELS <- setNames(
  vapply(JAMS_PAPERS, function(p) p$content_label, character(1)),
  vapply(JAMS_PAPERS, function(p) STEM_TO_ROLLING[[p$file_stem]], character(1))
)

# Expert v4 labels are contested holistic judgments, not ground truth --
# afc_consistency is the 2AFC rater-agreement rate for that paper (1.00 =
# unanimous). Use as a weight so a miss on a low-consistency paper (currently
# only Dritschel, at 0.88) doesn't count the same as a miss on a unanimous one.
EXPERT_LABEL_CONFIDENCE <- setNames(
  vapply(JAMS_PAPERS, function(p) p$afc_consistency, numeric(1)),
  vapply(JAMS_PAPERS, function(p) STEM_TO_ROLLING[[p$file_stem]], character(1))
)
