"""Independent content-topic and reasoning-style tagging for math paper text.

The two axes are deliberately built from disjoint vocabularies so they can move
independently, matching the JAMS "quadrant" premise (content and style are meant
to be orthogonal — see corpus_classify/CORPUS.md and R/jams_metadata.R):

- score_content(): WHAT the paper is about. Subject-matter nouns (geodesic,
  manifold, functor, cap set...) plus arXiv subfield category. This is a topic
  classifier.
- score_style(): HOW the reasoning is presented. Rhetorical/discourse markers
  (visualize, locally/globally, by definition, substituting...) that describe
  the *mode* of argument rather than the subject. These phrases are chosen to
  be generic across subfields so a paper about algebra can still score
  geometric-style (heavy in spatial/visual presentation) and vice versa.

Do not add subject nouns (ring, manifold, functor, knot...) to the style
markers, and do not add presentation-mode phrases to the content keywords —
that recreates the content/style conflation this module exists to avoid.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# CONTENT axis: subject-matter vocabulary (topic), independent of style.
# ---------------------------------------------------------------------------

CONTENT_GEOMETRIC_KEYWORDS: dict[str, float] = {
    "geodesic": 2.0,
    "curvature": 1.8,
    "riemannian": 1.8,
    "hyperbolic": 1.8,
    "manifold": 1.5,
    "embedding": 1.2,
    "isotopy": 1.6,
    "homotopy": 1.2,
    "knot": 1.5,
    "link": 1.0,
    "surface": 1.2,
    "triangulation": 1.5,
    "simplex": 1.2,
    "cell complex": 1.8,
    "mapping class": 2.0,
    "teichmuller": 2.0,
    "teichmüller": 2.0,
    "moduli space": 1.5,
    "foliation": 1.6,
    "orbifold": 1.5,
    "metric space": 1.4,
    "convex hull": 1.3,
    "polyhedron": 1.2,
    "handlebody": 1.8,
    "heegaard": 1.8,
    "train track": 1.8,
    "lamination": 1.5,
    "billiard": 1.3,
    "symplectic": 1.0,
    "contact structure": 1.5,
    "floer": 1.5,
    "gauge theory": 1.2,
    "fiber bundle": 1.2,
    "fibration": 1.0,
    "covering space": 1.5,
    "fundamental group": 1.0,
    "topological": 0.8,
    "homology sphere": 1.5,
    "surgery": 1.2,
    "boundary": 0.6,
    "dimension": 0.5,
    "configuration space": 1.2,
    "geometric group": 1.5,
    "cube complex": 1.6,
    "cat(0)": 2.0,
    "nonpositive curvature": 2.0,
}

CONTENT_ALGEBRAIC_KEYWORDS: dict[str, float] = {
    "homomorphism": 1.8,
    "functor": 1.8,
    "category": 1.2,
    "morphism": 1.5,
    "module": 1.2,
    "ring": 0.8,
    "ideal": 1.0,
    "polynomial": 1.0,
    "galois": 1.5,
    "representation": 1.0,
    "character": 0.6,
    "scheme": 1.2,
    "sheaf": 1.0,
    "tensor": 1.0,
    "operator algebra": 1.8,
    "c*-algebra": 1.8,
    "von neumann": 1.8,
    "model theory": 2.0,
    "definable": 1.5,
    "o-minimal": 2.0,
    "stable group": 2.0,
    "finite field": 1.5,
    "additive combinatorics": 1.8,
    "fourier": 1.5,
    "cap set": 2.0,
    "recurrence": 1.0,
    "generating function": 1.5,
    "combinatorial": 1.0,
    "lattice": 0.8,
    "poset": 1.2,
    "young tableau": 1.5,
    "schubert": 1.2,
    "hopf": 1.2,
    "lie algebra": 1.0,
    "cohomology ring": 1.2,
    "derived category": 1.5,
    "spectral sequence": 1.0,
    "formal power series": 1.5,
    "algebraic geometry": 0.8,
    "number theory": 0.6,
    "approximate subgroup": 2.0,
    "logic": 0.8,
    "axiom": 1.0,
    "proof system": 1.5,
}

# arXiv primary category lean (subfield -> content axis, applied before keyword tie-break)
CONTENT_CATEGORY_LEAN: dict[str, tuple[float, float]] = {
    "math.gt": (1.5, 0.0),
    "math.dg": (1.5, 0.0),
    "math.at": (1.2, 0.0),
    "math.mg": (1.2, 0.0),
    "math.ra": (0.0, 1.5),
    "math.ct": (0.0, 1.8),
    "math.lo": (0.0, 1.8),
    "math.ac": (0.0, 1.2),
    "math.co": (0.0, 0.8),
    "math.nt": (0.0, 1.0),
    "math.ag": (0.5, 1.0),
    "math.rt": (0.0, 1.2),
    "math.oa": (0.0, 1.5),
}

# ---------------------------------------------------------------------------
# STYLE axis: rhetorical/discourse markers of HOW the argument is presented.
# Deliberately subject-agnostic — no subfield nouns here.
# ---------------------------------------------------------------------------

STYLE_SPATIAL_MARKERS: dict[str, float] = {
    "visualize": 1.5,
    "visualise": 1.5,
    "pictorially": 1.8,
    "as illustrated": 1.5,
    "as depicted": 1.5,
    "as shown in the figure": 1.8,
    "as shown in figure": 1.8,
    "diagrammatically": 1.8,
    "geometric picture": 1.8,
    "geometric intuition": 1.6,
    "intuitively, one can think of": 1.8,
    "can be thought of as living in": 1.6,
    "think of it as sitting inside": 1.6,
    "moving along": 1.4,
    "sliding along": 1.6,
    "continuously deform": 1.8,
    "deform continuously": 1.8,
    "perturb slightly": 1.2,
    "shrinks to a point": 1.6,
    "expands outward": 1.2,
    "converges to a point": 1.2,
    "sweeps out": 1.4,
    "traces out a path": 1.6,
    "flows toward": 1.2,
    "local-to-global": 1.8,
    "in a neighborhood of": 1.2,
    "nearby points": 1.0,
    "patch these together": 1.6,
    "glue together": 1.2,
    "sits inside": 1.0,
    "lies inside": 0.8,
    "positioned at": 1.0,
    "located near": 1.0,
    "at a distance of": 1.0,
}

STYLE_SYMBOLIC_MARKERS: dict[str, float] = {
    "substituting": 1.6,
    "substitute this into": 1.8,
    "rearranging": 1.6,
    "rearrange terms": 1.8,
    "collecting terms": 1.8,
    "expanding the expression": 1.8,
    "simplify the expression": 1.6,
    "algebraic manipulation": 1.8,
    "symbolically": 1.4,
    "syntactically": 1.4,
    "we compute directly": 1.4,
    "explicitly compute": 1.4,
    "plugging in": 1.6,
    "plug in": 1.4,
    "solving for": 1.4,
    "derive the identity": 1.6,
    "the above equation implies": 1.6,
    "combining these identities": 1.6,
}


def _normalize(text: str) -> str:
    # NFKD decomposes PDF-extracted ligatures (U+FB01 "fi", U+FB02 "fl", ...)
    # to plain ASCII letters. Without this, "finitely" survives PDF text
    # extraction as "ﬁnitely" and downstream alpha-only regexes silently
    # drop the ligature, corrupting the word to "nitely".
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = text.replace("−", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text)


def _score(text: str, geo_kw: dict[str, float], alg_kw: dict[str, float]) -> tuple[float, float, list[str], list[str]]:
    geo = 0.0
    alg = 0.0
    hits_geo: list[str] = []
    hits_alg: list[str] = []
    for kw, w in geo_kw.items():
        if kw in text:
            geo += w
            hits_geo.append(kw)
    for kw, w in alg_kw.items():
        if kw in text:
            alg += w
            hits_alg.append(kw)
    return geo, alg, hits_geo, hits_alg


FIGURE_PATTERN = re.compile(r"\bfig(?:ure)?s?\.?\b|\bdiagrams?\b|\bpictures?\b", re.IGNORECASE)
EQUATION_REF_PATTERN = re.compile(r"\(\s*\d{1,3}(\.\d{1,2})?\s*\)")


def _structural_density(text: str) -> tuple[float, float, list[str], list[str]]:
    """Presentation-mode density: figure/diagram references (visual) vs. numbered
    equation references (derivation-chain-heavy), per 1000 words. Independent of
    subject vocabulary — a paper on any topic can be figure-heavy or equation-heavy."""
    text = unicodedata.normalize("NFKD", text)
    n_words = max(len(text.split()), 1)
    n_fig = len(FIGURE_PATTERN.findall(text))
    n_eqref = len(EQUATION_REF_PATTERN.findall(text))
    fig_per_1k = 1000 * n_fig / n_words
    eqref_per_1k = 1000 * n_eqref / n_words
    geo = 3.0 * fig_per_1k
    alg = 0.5 * eqref_per_1k
    hits_geo = [f"figure/diagram refs: {n_fig} ({fig_per_1k:.2f}/1k words)"] if n_fig else []
    hits_alg = [f"numbered equation refs: {n_eqref} ({eqref_per_1k:.2f}/1k words)"] if n_eqref else []
    return geo, alg, hits_geo, hits_alg


@dataclass
class ContentScore:
    geometric: float
    algebraic: float
    label: str
    margin: float
    hits_geo: list[str] = field(default_factory=list)
    hits_alg: list[str] = field(default_factory=list)


@dataclass
class StyleScore:
    geometric: float
    algebraic: float
    label: str
    margin: float
    hits_geo: list[str] = field(default_factory=list)
    hits_alg: list[str] = field(default_factory=list)


def score_content(text: str, categories: list[str] | None = None) -> ContentScore:
    """Topic/subject-matter score: what the paper is about."""
    norm = _normalize(text)
    geo, alg, hits_geo, hits_alg = _score(norm, CONTENT_GEOMETRIC_KEYWORDS, CONTENT_ALGEBRAIC_KEYWORDS)
    if categories:
        for cat in categories:
            lean = CONTENT_CATEGORY_LEAN.get(cat.lower())
            if lean:
                geo += lean[0]
                alg += lean[1]
    margin = geo - alg
    label = "geometric" if margin >= 0.5 else "algebraic" if margin <= -0.5 else ("algebraic" if alg >= geo else "geometric")
    return ContentScore(geo, alg, label, margin, hits_geo, hits_alg)


def score_style(text: str) -> StyleScore:
    """Reasoning-style score: how the argument is presented, independent of topic."""
    norm = _normalize(text)
    geo, alg, hits_geo, hits_alg = _score(norm, STYLE_SPATIAL_MARKERS, STYLE_SYMBOLIC_MARKERS)
    d_geo, d_alg, d_hits_geo, d_hits_alg = _structural_density(text)
    geo += d_geo
    alg += d_alg
    hits_geo = hits_geo + d_hits_geo
    hits_alg = hits_alg + d_hits_alg
    margin = geo - alg
    label = "geometric" if margin >= 0.5 else "algebraic" if margin <= -0.5 else ("algebraic" if alg >= geo else "geometric")
    return StyleScore(geo, alg, label, margin, hits_geo, hits_alg)


@dataclass
class PaperScore:
    content: ContentScore
    style: StyleScore


def score_paper(text: str, categories: list[str] | None = None) -> PaperScore:
    return PaperScore(content=score_content(text, categories), style=score_style(text))


# Backward-compatible alias: old callers used `score_text` for what was actually
# a content/topic score mislabeled as style. New callers should use
# score_content()/score_style() explicitly.
score_text = score_content
