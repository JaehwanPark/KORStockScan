#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
exec "$PROJECT_DIR/.venv/bin/python" - "$PROJECT_DIR" "${1:---print-plan}" <<'PY'
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path(sys.argv[1])
mode = sys.argv[2]
if mode not in {'--install', '--remove', '--print-plan'}:
    raise SystemExit('expected --install, --remove or --print-plan')
marker = '# KORSTOCKSCAN_MONITORING_INSTRUCTION_REFRESH_'
wrapper = root / 'deploy/run_monitoring_instruction_refresh.sh'
# Cron command fields do not support arbitrary shell/path syntax.
if any(c not in '/_-.' and not c.isalnum() for c in str(root)):
    raise SystemExit('unsupported cron project path')
entries = [
    f'30-59 19 * * * /bin/bash {wrapper} --mode postclose >> {root}/logs/monitoring_instruction_refresh.log 2>&1 {marker}1930',
    f'* * * * * /bin/bash {wrapper} --mode intraday >> {root}/logs/monitoring_instruction_refresh.log 2>&1 {marker}AFTER_COMPLETION',
]
if mode == '--print-plan':
    print('\n'.join(entries))
    raise SystemExit(0)
timezone = subprocess.check_output(['timedatectl', 'show', '--property=Timezone', '--value'], text=True).strip()
if mode == '--install' and timezone != 'Asia/Seoul':
    raise SystemExit('cron requires system timezone Asia/Seoul; no timezone mutation performed')
state = root / 'data/report/monitoring_instruction_refresh'
state.mkdir(parents=True, exist_ok=True)
with (state / 'writer.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    def read_cron():
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode and 'no crontab' not in result.stderr:
            raise RuntimeError('cannot read existing crontab')
        return result.stdout
    def atomic_json(path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, 'w') as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    old = read_cron()
    kept = [line for line in old.splitlines() if marker not in line]
    new = '\n'.join(kept + (entries if mode == '--install' else [])) + '\n'
    config_path = root / 'data/config/monitoring_instruction_refresh.json'
    prior_config = json.loads(config_path.read_text()) if config_path.exists() else None
    config = dict(prior_config) if prior_config is not None else {
        'schema': 'monitoring_instruction_refresh_v1', 'model': 'gpt-5.6-sol',
        'effort': 'medium', 'effective_from_date': datetime.now(ZoneInfo('Asia/Seoul')).date().isoformat(),
    }
    config['enabled'] = mode == '--install'
    stamp = datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%dT%H%M%S%f')
    backup = state / f'crontab_before_{stamp}.txt'
    with os.fdopen(os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as handle:
        handle.write(old)
    # Compare again instead of overwriting an unrelated concurrent installation.
    if read_cron() != old:
        raise RuntimeError('crontab changed during installation')
    (root / 'logs').mkdir(exist_ok=True)
    atomic_json(config_path, config)
    try:
        subprocess.run(['crontab', '-'], input=new, text=True, check=True)
    except subprocess.CalledProcessError:
        if prior_config is not None:
            atomic_json(config_path, prior_config)
        else:
            config_path.unlink(missing_ok=True)
        raise
    installed = read_cron()
    if installed != new:
        raise RuntimeError('crontab verification failed; inspect backup and current table before recovery')
    receipt = {'schema': 'monitoring_instruction_refresh_install_v1', 'installed_at': stamp,
        'mode': mode, 'timezone': timezone, 'enabled': config['enabled'],
        'model': config['model'], 'effort': config['effort'],
        'effective_from_date': config['effective_from_date'], 'entries': entries if config['enabled'] else [],
        'crontab_backup': str(backup), 'crontab_sha256': hashlib.sha256(installed.encode()).hexdigest(),
        'module_sha256': hashlib.sha256((root / 'src/engine/automation/monitoring_instruction_refresh.py').read_bytes()).hexdigest(),
        'module_path': str(root / 'src/engine/automation/monitoring_instruction_refresh.py'),
        'wrapper_sha256': hashlib.sha256(wrapper.read_bytes()).hexdigest(),
        'runtime_effect': False, 'allowed_runtime_apply': False}
    atomic_json(state / 'installed_trigger.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))
PY
