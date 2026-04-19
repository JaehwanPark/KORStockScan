#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
"$PROJECT_DIR/analysis/gemini_scalping_pattern_lab/run.sh"
