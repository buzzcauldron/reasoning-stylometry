#!/usr/bin/env python3
"""Thin shell: invoke the R/stylo analysis engine. No stylometry logic here."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    script = ROOT / "scripts" / "run_stylo_analysis.R"
    return subprocess.call(["Rscript", str(script)], cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
