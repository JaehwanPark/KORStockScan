#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${PROJECT_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
VENV_PY="$PROJECT_DIR/.venv/bin/python"
RETENTION_DAYS="${1:-1}"

mkdir -p "$PROJECT_DIR/logs"
cd "$PROJECT_DIR"
PYTHONPATH=. "$VENV_PY" -m src.engine.compress_db_backfilled_files --days "$RETENTION_DAYS" >> "$PROJECT_DIR/logs/dashboard_db_archive.log" 2>&1
