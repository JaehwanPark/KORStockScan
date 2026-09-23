#!/usr/bin/env bash
# Shared nonblocking deployment lock. Source from systemd installers and keep
# descriptor 9 open for the complete mutation window.
runtime_release_set_lock_acquire() {
  local project_root="${1:-${PROJECT_DIR:-}}"
  if [[ -z "$project_root" ]]; then
    echo "runtime_release_set_lock: project root required" >&2
    return 2
  fi
  local lock_path="$project_root/data/runtime/runtime_release_set.lock"
  if [[ ! -d "$(dirname "$lock_path")" ]]; then
    echo "runtime_release_set_lock: runtime directory missing" >&2
    return 2
  fi
  /usr/bin/touch "$lock_path"
  /usr/bin/chmod 0666 "$lock_path"
  exec 9>"$lock_path"
  if ! /usr/bin/flock -n 9; then
    echo "runtime_release_set_lock: another deployment transition is active" >&2
    return 2
  fi
}
