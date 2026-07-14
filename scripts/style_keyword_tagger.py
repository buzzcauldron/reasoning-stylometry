"""Keyword-based geometric vs algebraic style tagging for math paper metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass

# v4 rubric: spatial / geometric reasoning register
GEOMETRIC_KEYWORDS: dict[str, float] = {
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
    "visualization": 1.0,
    "configuration space": 1.2,
    "geometric group": 1.5,
    "cube complex": 1.6,
    "cat(0)": 2.0,
    "nonpositive curvature": 2.0,
}

# v4 rubric: symbolic / algebraic reasoning register
ALGEBRAIC_KEYWORDS: dict[str, float] = {
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
    "asymptotic": 0.8,
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

# arXiv primary category lean (applied before keyword tie-break)
CATEGORY_LEAN: dict[str, tuple[float, float]] = {
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


@dataclass
class StyleScore:
    geometric: float
    algebraic: float
    label: str
    margin: float
    hits_geo: list[str]
    hits_alg: list[str]


def _normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("−", "-").replace("–", "-")
    return re.sub(r"\s+", " ", text)


def score_text(text: str, categories: list[str] | None = None) -> StyleScore:
    text = _normalize(text)
    geo = 0.0
    alg = 0.0
    hits_geo: list[str] = []
    hits_alg: list[str] = []

    for kw, w in GEOMETRIC_KEYWORDS.items():
        if kw in text:
            geo += w
            hits_geo.append(kw)
    for kw, w in ALGEBRAIC_KEYWORDS.items():
        if kw in text:
            alg += w
            hits_alg.append(kw)

    if categories:
        for cat in categories:
            lean = CATEGORY_LEAN.get(cat.lower())
            if lean:
                geo += lean[0]
                alg += lean[1]

    margin = geo - alg
    if margin >= 0.5:
        label = "geometric"
    elif margin <= -0.5:
        label = "algebraic"
    else:
        label = "algebraic" if alg >= geo else "geometric"

    return StyleScore(geo, alg, label, margin, hits_geo, hits_alg)
