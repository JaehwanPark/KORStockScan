#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="${KORSTOCKSCAN_PROJECT_DIR:-/home/ubuntu/KORStockScan}"
ACTION="${1:-install}"
if (( EUID != 0 )); then
  printf 'run as root: sudo %s\n' "$0" >&2
  exit 1
fi

source "$PROJECT_DIR/deploy/runtime_release_set_lock.sh"
runtime_release_set_lock_acquire "$PROJECT_DIR"

legacy_dropin_name="$(printf '%0180d' 0 | tr '0' 'z')-postclose-eod-gate-20260929.conf"
# Existing reviewed retirement/source pins begin with '~zzz'. A plain 'z'
# filename is lower priority and cannot update their effective ExecStart.
dropin_name="~zzzz-postclose-eod-gate-20260929.conf"
if [[ "$ACTION" == "--rollback" ]]; then
  for unit in korstockscan-machine-microstructure-final-refresh.service; do
    rm -f "/etc/systemd/system/${unit}.d/$dropin_name"
    rm -f "/etc/systemd/system/${unit}.d/$legacy_dropin_name"
  done
  systemctl daemon-reload
  printf '[POSTCLOSE_EOD_SYSTEMD] rollback=removed_schedule_pins services_not_restarted=true\n'
  exit 0
elif [[ "$ACTION" != "install" || $# -gt 0 ]]; then
  echo "usage: $0 [--rollback]" >&2
  exit 2
fi

selection="$($PROJECT_DIR/.venv/bin/python - "$PROJECT_DIR" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1]).resolve(strict=True)
payload = json.loads((workspace / "data/runtime/runtime_release_selection.json").read_text())
root = Path(payload["release_root"]).resolve(strict=True)
commit = str(payload["git_commit"])
if root.parent != workspace.parent / f"{workspace.name}-runtime-releases":
    raise SystemExit("selected_release_outside_managed_directory")
if subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() != commit:
    raise SystemExit("selected_release_commit_mismatch")
dirty = subprocess.check_output(
    ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all", "--", "deploy", "src"],
    text=True,
)
if dirty:
    raise SystemExit("selected_release_source_dirty")
for relative in (
    "deploy/run_machine_microstructure_final_refresh.sh",
    "deploy/eod_terminal_gate.sh",
):
    if not (root / relative).is_file():
        raise SystemExit(f"selected_release_schedule_file_missing:{relative}")
print(f"{root}\n{commit}")
PY
)"
mapfile -t release_values <<< "$selection"
RELEASE_ROOT="${release_values[0]}"
RELEASE_COMMIT="${release_values[1]}"
if [[ -z "$RELEASE_ROOT" || ! "$RELEASE_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "postclose_eod_systemd_release_identity_invalid" >&2
  exit 2
fi

units=(
  "korstockscan-machine-microstructure-final-refresh:run_machine_microstructure_final_refresh.sh"
)
for entry in "${units[@]}"; do
  unit="${entry%%:*}.service"
  wrapper="${entry#*:}"
  timer="${unit%.service}.timer"
  main_pid="$(systemctl show "$unit" --property=MainPID --value)"
  [[ "$main_pid" == "0" ]] || { echo "${unit}_active_pid_blocks_schedule_pin:${main_pid}" >&2; exit 1; }
  [[ "$(systemctl show "$timer" --property=LoadState --value)" == "loaded" ]] || { echo "${timer}_not_loaded" >&2; exit 1; }
  dropin_dir="/etc/systemd/system/${unit}.d"
  install -d -m 0755 "$dropin_dir"
  dropin="$dropin_dir/$dropin_name"
  temporary="$(mktemp "$dropin_dir/.postclose-eod-gate.XXXXXX")"
  cat > "$temporary" <<EOF
# Exact-date EOD completion gates are required before postclose compute.
# Reviewed selected-release router; installation preserves timer hold state.
[Service]
WorkingDirectory=$PROJECT_DIR
Environment="PYTHONPATH=$PROJECT_DIR"
Environment="PROJECT_DIR=$PROJECT_DIR"
UnsetEnvironment=KORSTOCKSCAN_PROJECT_DIR KORSTOCKSCAN_PYTHON_BIN KORSTOCKSCAN_RUNTIME_GIT_COMMIT
ExecStart=
ExecStart=/bin/bash $PROJECT_DIR/deploy/run_runtime_release.sh machine-final-refresh
EOF
  chmod 0644 "$temporary"
  mv -f "$temporary" "$dropin"
done

systemctl daemon-reload
for entry in "${units[@]}"; do
  unit="${entry%%:*}.service"
  wrapper="${entry#*:}"
  timer="${unit%.service}.timer"
  properties="$(systemctl show "$unit" --property=WorkingDirectory,ExecStart,Environment --no-pager)"
  grep -Fq "WorkingDirectory=$PROJECT_DIR" <<< "$properties"
  grep -Fq "$PROJECT_DIR/deploy/run_runtime_release.sh machine-final-refresh" <<< "$properties"
  [[ "$(systemctl show "$unit" --property=MainPID --value)" == "0" ]]
done

printf '[POSTCLOSE_EOD_SYSTEMD] release_root=%s commit=%s units=1 timers=preserved services_not_restarted=true\n' \
  "$RELEASE_ROOT" "$RELEASE_COMMIT"
