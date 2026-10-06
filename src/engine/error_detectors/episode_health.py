"""Exact-date general Episode apply/preflight/PID/source census, read-only.

Ownership: process/source health. Historical failed units and future profile
windows are not current startup failures. This module never starts a service.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections import Counter
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo


def unit_census(units):
    result = subprocess.run(['/bin/systemctl', 'show', *units,
        '--property=Id,LoadState,ActiveState,Result,MainPID,WorkingDirectory,ExecMainStartTimestamp',
        '--no-pager'], capture_output=True, text=True, timeout=5, check=False)
    if result.returncode or len(result.stdout) > 256 * 1024:
        raise ValueError('episode_unit_census_unobservable')
    rows = {}
    for block in result.stdout.strip().split('\n\n'):
        values = dict(line.split('=', 1) for line in block.splitlines() if '=' in line)
        if values.get('Id'):
            rows[values['Id']] = values
    return rows


def check(root, now, *, target_date, reader, states=None, timer_dir=Path('/etc/systemd/system')):
    from src.trading.low_price_two_leg import policy_runtime as policy
    from src.trading.low_price_two_leg.preflight import validate_authority
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    now = now.replace(tzinfo=ZoneInfo('Asia/Seoul')) if now.tzinfo is None else now.astimezone(ZoneInfo('Asia/Seoul'))
    day = date.fromisoformat(target_date)
    profiles = profiles_for_target_date(day)
    folder = root / 'data/runtime/low_price_two_leg'
    applied_path = root / 'data/threshold_cycle/low_price_two_leg/applied' / f'low_price_two_leg_policy_{target_date}.json'
    result = dict(status='future_due', findings=[], source_date=target_date, target_date=target_date,
        artifact=str(applied_path), actual_pid_consumed=False, rows=[], decision_authority='report_only')
    if target_date < '2026-10-06':
        result['status'] = 'not_required_before_introduction'
        return result
    # Applied episode policy is produced by Main PREOPEN at 07:35, not the
    # independent symbol-owner job at 07:32. Keep a bounded publication grace.
    future = now.date() < day or (now.date() == day and now.time() < time(7, 36))
    if not applied_path.exists() and not applied_path.is_symlink():
        preopen = root / 'data/report/threshold_cycle_preopen_status' / f'threshold_cycle_preopen_{target_date}.status.json'
        if now.date() == day and now.time() >= time(7, 35) and preopen.exists():
            try:
                producer, _ = reader(preopen)
                if producer.get('target_date') == target_date and producer.get('status') == 'failed':
                    result.update(status='source_invalid', findings=['episode_apply_preopen_producer_failed'])
                    return result
                if future and producer.get('target_date') == target_date and producer.get('status') in {'running', 'started'}:
                    result['status'] = 'waiting_producer'
            except (OSError, ValueError, TypeError) as exc:
                result.update(status='source_invalid', findings=['episode_apply_preopen_receipt_invalid'], error=str(exc)[:160])
                return result
        result['rows'] = [dict(profile_id=pid, status='future_due' if future else 'applied_missing') for pid in profiles]
        if not future:
            result.update(status='source_invalid', findings=['episode_applied_missing_after_due'])
        return result
    try:
        applied, sha = reader(applied_path)
        valid, reason = policy.validate_applied(applied, target_date=day)
        if not valid:
            raise ValueError(reason)
        result['report_sha256'] = sha
        excluded = {r['profile_id'] for r in applied.get('runtime_profile_exclusions') or []}
        timer_clocks = {}
        for path in timer_dir.glob('korstockscan-low-price-two-leg-*-preflight.timer'):
            text = path.read_text()
            unit = re.search(r'^Unit=korstockscan-low-price-two-leg-preflight@([^\s]+)\.service$', text, re.M)
            clock = re.search(r'^OnCalendar=Mon\.\.Fri \*-\*-\* (\d{2}:\d{2}:\d{2}) Asia/Seoul$', text, re.M)
            if unit and clock:
                if unit[1] in timer_clocks:
                    raise ValueError('episode_duplicate_preflight_timer_owner')
                timer_clocks[unit[1]] = time.fromisoformat(clock[1])
        units = [f'korstockscan-low-price-two-leg@{pid}.service' for pid in profiles]
        if states is None:
            states = unit_census(units)
        for pid, profile in sorted(profiles.items()):
            unit = states.get(f'korstockscan-low-price-two-leg@{pid}.service') or {}
            row = dict(profile_id=pid, symbol=profile.symbol, session=profile.session,
                policy_hash=applied['policy_hash'], unit=unit, status='future_due', findings=[])
            result['rows'].append(row)
            if pid in excluded:
                row['status'] = 'quarantined'
                continue
            due = timer_clocks.get(pid)
            row['preflight_due'] = due.isoformat() if due else None
            if future or (due and now.time() < due):
                continue
            if due is None:
                row['findings'].append('episode_preflight_schedule_unobservable')
            authority_path = folder / f'{pid}_authority.json'
            authority_valid, authority_reason = validate_authority(profile=profile, now=now, path=authority_path)
            row['authority'] = dict(valid=authority_valid, reason=authority_reason)
            state_path = folder / f'{pid}_state.json'
            try:
                state = reader(state_path)[0] if state_path.exists() or state_path.is_symlink() else {}
            except (OSError, ValueError, TypeError, KeyError) as exc:
                row.update(status='source_invalid', error=str(exc), findings=['episode_profile_state_invalid'])
                continue
            current_state = state.get('trade_date') == target_date
            capture = state.get('economic_capture') or {}
            capture = capture if isinstance(capture, dict) else {}
            row.update(state_date=state.get('trade_date'), state_status=state.get('status'), capture=capture)
            chain = capture.get('capture_sequence') or {}
            chain = chain if isinstance(chain, dict) else {}
            sequence = chain.get('sequence')
            chain_valid = (chain.get('schema') == 'low_price_capture_sequence_v1'
                and re.fullmatch(r'[0-9a-f]{32}', str(chain.get('generation_id'))) is not None
                and type(sequence) is int and sequence >= 1
                and (chain.get('previous_observation_sha256') is None if sequence == 1
                     else re.fullmatch(r'[0-9a-f]{64}', str(chain.get('previous_observation_sha256'))) is not None)
                and re.fullmatch(r'[0-9a-f]{64}', str(capture.get('observation_sha256'))) is not None)
            try:
                stamp = datetime.fromisoformat(capture.get('observed_at_kst') or '')
                age = (now-stamp).total_seconds() if stamp.tzinfo is not None else None
            except (TypeError, ValueError):
                age = None
            row['source_age_sec'] = age
            active_pid = int(unit.get('MainPID') or 0)
            if active_pid and unit.get('ActiveState') == 'active':
                try:
                    cwd = os.readlink(f'/proc/{active_pid}/cwd')
                except OSError:
                    row['findings'].append('episode_pid_cwd_unobservable')
                    cwd = None
                row['pid_cwd'] = cwd
                if cwd and cwd != unit.get('WorkingDirectory'):
                    row['findings'].append('episode_unit_process_release_mismatch')
                if not authority_valid:
                    row['findings'].append('episode_current_authority_invalid')
                if (capture.get('source_date') != target_date or capture.get('runtime_pid') != active_pid
                    or capture.get('profile_id') != pid or capture.get('runtime_cwd') != cwd
                    or capture.get('policy_hash') != applied['policy_hash']
                    or capture.get('execution_mode') != 'real' or capture.get('status') != 'persisted'
                    or not chain_valid or age is None or not 0 <= age <= 120):
                    row['findings'].append('episode_current_pid_source_not_observed')
                row['status'] = 'running_observed' if not row['findings'] else 'source_unverified'
            elif now.time() < profile.policy.scan_start:
                row['status'] = 'preflight_ready_waiting_start' if authority_valid else 'preflight_not_observed'
                if not authority_valid:
                    row['findings'].append('episode_current_preflight_not_observed')
            elif (current_state and state.get('status') in {'COMPLETE', 'NO_TRADE'}
                  and capture.get('source_date') == target_date and capture.get('profile_id') == pid
                  and capture.get('policy_hash') == applied['policy_hash'] and capture.get('execution_mode') == 'real'
                  and capture.get('status') == 'persisted' and chain_valid and age is not None and age >= 0):
                row['status'] = 'terminal_observed'
            else:
                row['status'] = 'startup_not_observed'
                row['findings'].append('episode_current_startup_not_observed')
        result['counts'] = dict(Counter(r['status'] for r in result['rows']))
        result['findings'] = sorted({f for row in result['rows'] for f in row['findings']})
        result['status'] = 'warning' if result['findings'] else 'pass'
        result['actual_pid_consumed'] = any(r['status'] == 'running_observed' for r in result['rows'])
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        moving = str(exc) in {'semantic_generation_changed_during_read', 'episode_unit_census_unobservable'} or isinstance(exc, subprocess.SubprocessError)
        result.update(status='unobservable' if moving else 'source_invalid',
                      findings=[] if moving else ['episode_startup_contract_invalid'], error=str(exc))
    return result
