#!/usr/bin/env bash
# JAMS stylometry: Python is only a launcher; R/stylo is the engine.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/run.py"
