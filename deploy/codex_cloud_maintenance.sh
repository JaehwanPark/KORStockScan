#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "[CODEX_CLOUD_MAINTENANCE] .venv not found, running setup first"
  bash deploy/codex_cloud_setup.sh
  exit 0
fi

.venv/bin/pip install -r requirements.txt

echo "[CODEX_CLOUD_MAINTENANCE] completed"
