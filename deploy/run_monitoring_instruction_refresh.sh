#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
# Separate document writer. Never invokes a trading/postclose producer or sync.
exec timeout --kill-after=10s 900s env PYTHONPATH="$PROJECT_DIR" \
  "$PROJECT_DIR/.venv/bin/python" -m src.engine.automation.monitoring_instruction_refresh "$@"
