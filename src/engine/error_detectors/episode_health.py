"""Exact-date general Episode apply/preflight/PID/source census, read-only.

Ownership: process/source health. Historical failed units and future profile
windows are not current startup failures. This module never starts a service.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

PREFLIGHT_PUBLICATION_GRACE_SEC = 60


def _unit_started_at(unit):
    raw = str(unit.get('ExecMainStartTimestamp') or '')
    match = re.fullmatch(r'\w+ (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (KST|UTC)', raw)
    if not match:
        return None
    return datetime.fromisoformat(match[1]).replace(
        tzinfo=ZoneInfo('Asia/Seoul' if match[2] == 'KST' else 'UTC'))


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


def check(root, now, *, target_date, reader, states=None, timer_dir=Path('/etc/systemd/system'), read_clock=None):
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
        units = [name for pid in profiles for name in (
            f'korstockscan-low-price-two-leg@{pid}.service',
            f'korstockscan-low-price-two-leg-preflight@{pid}.service')]
        if states is None:
            states = unit_census(units)
        prior_applied = None
        for pid, profile in sorted(profiles.items()):
            unit = states.get(f'korstockscan-low-price-two-leg@{pid}.service') or {}
            preflight_unit = states.get(f'korstockscan-low-price-two-leg-preflight@{pid}.service') or {}
            row = dict(profile_id=pid, symbol=profile.symbol, session=profile.session,
                policy_hash=applied['policy_hash'], unit=unit, preflight_unit=preflight_unit,
                status='future_due', findings=[])
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
                if str(exc) == 'semantic_generation_changed_during_read':
                    raise
                row.update(status='source_invalid', error=str(exc), findings=['episode_profile_state_invalid'])
                continue
            # The native capture can be published after this census started.
            # Measure freshness at the completed read, without permitting a
            # future timestamp or extending the existing freshness bound.
            source_as_of = read_clock() if read_clock is not None else now
            if not isinstance(source_as_of, datetime) or source_as_of.tzinfo is None or source_as_of < now:
                raise ValueError('episode_source_read_clock_invalid')
            row['source_freshness_as_of'] = source_as_of.isoformat()
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
                age = (source_as_of-stamp).total_seconds() if stamp.tzinfo is not None else None
            except (TypeError, ValueError):
                age = None
            row['source_age_sec'] = age
            active_pid = int(unit.get('MainPID') or 0)
            if active_pid and unit.get('ActiveState') == 'active':
                cwd_unobservable = False
                try:
                    cwd = os.readlink(f'/proc/{active_pid}/cwd')
                except (PermissionError, FileNotFoundError, ProcessLookupError) as exc:
                    # An inaccessible or changing process is not missing raw
                    # capture. Retain unknown PID consumption; never substitute
                    # the configured WorkingDirectory as an observed cwd.
                    cwd_unobservable = True
                    row['process_observability'] = dict(status='unobservable',
                        reason='cwd_permission_denied' if isinstance(exc, PermissionError)
                        else 'process_exited_during_census', errno=exc.errno)
                    cwd = None
                except OSError:
                    row['findings'].append('episode_pid_cwd_unobservable')
                    cwd = None
                row['pid_cwd'] = cwd
                if cwd and cwd != unit.get('WorkingDirectory'):
                    row['findings'].append('episode_unit_process_release_mismatch')
                if not authority_valid:
                    row['findings'].append('episode_current_authority_invalid')
                source_identity_valid = not (not current_state
                    or capture.get('source_date') != target_date or capture.get('runtime_pid') != active_pid
                    or capture.get('profile_id') != pid
                    or not isinstance(capture.get('runtime_cwd'), str)
                    or not Path(capture.get('runtime_cwd') or '').is_absolute()
                    or capture.get('runtime_cwd') != unit.get('WorkingDirectory')
                    or (cwd is not None and capture.get('runtime_cwd') != cwd)
                    or capture.get('execution_mode') != 'real' or capture.get('status') != 'persisted'
                    or not chain_valid or age is None or not 0 <= age <= 120)
                source_valid = source_identity_valid and capture.get('policy_hash') == applied['policy_hash']
                row['capture_contract_valid'] = source_valid
                # Date rollover records the prior custody policy before the
                # first completed eligible minute binds today's entry policy.
                # This is a bounded initialization phase, never PID consumption
                # or an exemption for an evaluated bar or non-flat ledger.
                started = _unit_started_at(unit)
                first_bar_close = datetime.combine(day, profile.policy.scan_start, tzinfo=now.tzinfo) + timedelta(minutes=1)
                initial_binding = (source_identity_valid and not source_valid and authority_valid
                    and not row['findings']
                    and unit.get('Result') in (None, '', 'success')
                    and sequence == {'daily_state_initialized': 1,
                        'daily_state_initialized_from_prior_terminal_policy': 2}.get(capture.get('action'))
                    and state.get('status') == 'READY' and state.get('attempt_consumed') is False
                    and type(state.get('position_qty')) is int and state['position_qty'] == 0
                    and state.get('legs') == [] and state.get('owned_order_nos') == []
                    and not state.get('last_evaluated_bar') and not state.get('pending_entry_confirmation')
                    and started is not None and started.astimezone(now.tzinfo).date() == day
                    and started <= stamp <= source_as_of < first_bar_close)
                if initial_binding:
                    if prior_applied is None:
                        prior_applied = {}
                        try:
                            prior_day = date.fromisoformat(applied.get('source_date') or '')
                            if prior_day < day:
                                prior_path = applied_path.with_name(f'low_price_two_leg_policy_{prior_day.isoformat()}.json')
                                prior, prior_sha = reader(prior_path)
                                if policy.validate_applied(prior, target_date=prior_day)[0]:
                                    prior_applied = dict(payload=prior, artifact=str(prior_path), report_sha256=prior_sha)
                        except (OSError, ValueError, TypeError, KeyError) as exc:
                            if str(exc) == 'semantic_generation_changed_during_read':
                                raise
                    prior_payload = prior_applied.get('payload') or {}
                    initial_binding = (pid in (prior_payload.get('profiles') or {})
                        and prior_payload.get('policy_hash') == capture.get('policy_hash'))
                    if initial_binding:
                        row['initial_policy_binding'] = dict(status='waiting_first_completed_bar',
                            deadline=first_bar_close.isoformat(), prior_artifact=prior_applied['artifact'],
                            prior_report_sha256=prior_applied['report_sha256'], prior_policy_hash=capture['policy_hash'])
                if not source_valid and not initial_binding:
                    row['findings'].append('episode_current_pid_source_not_observed')
                row['status'] = ('source_unverified' if row['findings'] else
                                 'waiting_runtime_policy_binding' if initial_binding else
                                 'process_unobservable' if cwd_unobservable else 'running_observed')
            elif now.time() < profile.policy.scan_start:
                row['status'] = 'preflight_ready_waiting_start' if authority_valid else 'preflight_not_observed'
                if not authority_valid:
                    started = _unit_started_at(preflight_unit)
                    due_at = datetime.combine(day, due, tzinfo=now.tzinfo) if due else None
                    current_start = (started is not None and due_at is not None
                        and due_at <= started <= now and started.astimezone(now.tzinfo).date() == day)
                    current_failed = (current_start and (preflight_unit.get('ActiveState') == 'failed'
                        or preflight_unit.get('Result') not in (None, '', 'success')))
                    waiting = (current_start and not current_failed
                        and preflight_unit.get('ActiveState') in {'activating', 'active'}
                        and 0 <= (now-due_at).total_seconds() <= PREFLIGHT_PUBLICATION_GRACE_SEC)
                    if waiting:
                        row['status'] = 'waiting_preflight_producer'
                        row['preflight_grace_sec'] = PREFLIGHT_PUBLICATION_GRACE_SEC
                    else:
                        row['findings'].append('episode_current_preflight_failed' if current_failed
                                               else 'episode_current_preflight_not_observed')
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
        result['unobservable_profile_count'] = result['counts'].get('process_unobservable', 0)
        result['status'] = ('warning' if result['findings'] else
                           'unobservable' if result['unobservable_profile_count'] else
                           'waiting_producer' if (result['counts'].get('waiting_preflight_producer')
                                                  or result['counts'].get('waiting_runtime_policy_binding')) else 'pass')
        result['actual_pid_consumed'] = any(r['status'] == 'running_observed' for r in result['rows'])
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        moving = str(exc) in {'semantic_generation_changed_during_read', 'episode_unit_census_unobservable'} or isinstance(exc, subprocess.SubprocessError)
        result.update(status='unobservable' if moving else 'source_invalid',
                      findings=[] if moving else ['episode_startup_contract_invalid'], error=str(exc))
    return result
