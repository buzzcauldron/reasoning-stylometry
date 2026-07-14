#!/usr/bin/env bash
# End-to-end JAMS quadrant stylometry report pipeline.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
python3 scripts/extract_jams_pdfs.py
Rscript scripts/run_jams_quadrant.R
Rscript scripts/export_stylo_analysis.R
python3 scripts/render_jams_report.py
python3 scripts/render_jams_full_report.py
echo "Reports:"
echo "  $HOME/Downloads/jams_quadrant_full_report.html"
echo "  $HOME/Downloads/jams_quadrant_cross_view.html"
echo "  $HOME/Downloads/jams_quadrant_within_view.html"
echo "  $ROOT/output/jams_quadrant/"
