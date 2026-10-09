#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTION_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# Resolve from the shared selector on every entry, including a release wrapper.
# A data symlink alone is not proof that the code is the selected reviewed copy.
REVIEWED_ROOT="$("$EXECUTION_ROOT/.venv/bin/python" -I - "$EXECUTION_ROOT" <<'PY'
import json
import runpy
import sys
from pathlib import Path
execution = Path(sys.argv[1])
selection = json.loads((execution / 'data/runtime/runtime_release_selection.json').read_text())
workspace = Path(selection['workspace'])
router = runpy.run_path(str(execution / 'src/engine/infrastructure/runtime_release_router.py'))
root, _ = router['selected_release'](workspace)
print(root)
PY
)"
if [[ "$REVIEWED_ROOT" != "$EXECUTION_ROOT" ]]; then
  exec bash "$REVIEWED_ROOT/deploy/run_main_market_weakness_research_postclose.sh"
fi
cd "$REVIEWED_ROOT"
export PYTHONPATH="$REVIEWED_ROOT"
exec "$REVIEWED_ROOT/.venv/bin/python" -m src.engine.automation.main_market_weakness_research \
  --data-root "$REVIEWED_ROOT/data" --scheduled
