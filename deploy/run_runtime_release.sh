#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec "$WORKSPACE/.venv/bin/python" -I "$WORKSPACE/src/engine/infrastructure/runtime_release_router.py" "$@"
