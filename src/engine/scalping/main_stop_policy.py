"""Typed Main stop confirmation policy and causal, I/O-free decisions.

Hard/emergency/manual authority is pinned evidence, never a search dimension.
The loaded bundle is immutable for this process; open positions retain their pin.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import date
import hashlib
import json
import math
import os
from pathlib import Path
from types import MappingProxyType

SCHEMA = "main_stop_confirmation_policy_v1"
PIN_SCHEMA = "main_stop_confirmation_pin_v1"
ENV_FILE = "KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_FILE"
ENV_SHA = "KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_SHA256"
ENV_DATE = "KORSTOCKSCAN_MAIN_STOP_CONFIRMATION_POLICY_ACTIVE_DATE"
MARKETS = ("PREMARKET", "REGULAR", "INTEGRATED_AFTERMARKET")
ROLES = ("SCALP_PRESET_TP", "SCANNER", "SCALPING")
TUNABLE = frozenset({"soft_stop_pct", "grace_sec", "window_sec", "min_span_sec",
                     "min_samples", "below_ratio", "buffer_pct"})
KEYS = {
    "soft_stop_pct": "SCALP_STOP", "grace_sec": "SCALP_SOFT_STOP_MICRO_GRACE_SEC",
    "window_sec": "SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC",
    "min_span_sec": "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC",
    "min_samples": "SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES",
    "below_ratio": "SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO",
    "buffer_pct": "SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT",
    "hard_stop_pct": "SCALP_HARD_STOP",
    "soft_emergency_pct": "SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT",
    "protect_emergency_pct": "SCALP_PROTECT_TRAILING_EMERGENCY_PCT",
    "protect_exit_floor_pct": "SCALP_PROTECT_TRAILING_MIN_EXIT_PROFIT_PCT",
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def implementation_paths():
    return ('automation/main_stop_postclose.py','automation/main_stop_source_index.py',
        'scalping/main_stop_policy.py','scalping/main_stop_replay.py',
        'scalping/trailing_exit_decision.py','scalping/holding_path_vote_policy.py',
        'ai/holding_vote_replay_source.py','ai/holding_exit_vote.py','sniper_state_handlers.py',
        'ai_prompt_contracts.py','ai_response_contracts.py')


def implementation_sha():
    engine=Path(__file__).parents[1]
    return digest({name:hashlib.sha256((engine/name).read_bytes()).hexdigest() for name in implementation_paths()})


def verify_runtime_code_contract(bundle, target):
    """Preserve only the already-approved incumbent across a reviewed handoff.

    Research/publication and selected numeric successors retain current code
    requirements. Exact original-to-runtime source pairs, original policy,
    native consumption and same-day authority are independently verified.
    """
    validate_bundle(bundle, target)
    if any(cell['status'] == 'selected' for cell in bundle['cells'].values()):
        raise ValueError('stop_bundle_code_generation_changed')
    from src.engine.automation.intraday_release_handoff import verify_entry_consumer_code
    try:
        current = implementation_sha()
        proof = verify_entry_consumer_code(target, family='main_stop', policy_sha=bundle['policy_sha256'],
            expected=bundle['code_sha256'], actual=current,
            paths={name:'src/engine/'+name for name in implementation_paths()})
        if (proof.get('status') != 'verified_intraday_consumer_repair'
                or proof.get('policy_effect') != 'unchanged'
                or proof.get('policy_sha256') != bundle['policy_sha256']
                or proof.get('code_contract_sha256') != bundle['code_sha256']
                or proof.get('runtime_code_contract_sha256') != current):
            raise ValueError('stop_intraday_consumer_proof_invalid')
        return proof
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError('stop_bundle_code_generation_changed:' + str(exc)) from exc


def bounded_object(path, limit=1024*1024):
    """Hash the same bounded, stable bytes that were decoded."""
    path=Path(path)
    if path.is_symlink():raise ValueError('stop_source_size_or_path_invalid')
    def identity(st):
        return st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns
    with path.open('rb') as handle:
        before=os.fstat(handle.fileno())
        if before.st_size>limit:raise ValueError('stop_source_size_or_path_invalid')
        raw=handle.read(limit+1)
        after=os.fstat(handle.fileno())
    if (len(raw)>limit or path.is_symlink() or identity(before)!=identity(after)
            or identity(after)!=identity(path.stat())):
        raise ValueError('stop_source_changed_during_read')
    value=json.loads(raw)
    if not isinstance(value,dict):raise ValueError('stop_source_object_invalid')
    return value,hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class StopValues:
    soft_stop_pct: float
    grace_sec: int
    window_sec: int
    min_span_sec: int
    min_samples: int
    below_ratio: float
    buffer_pct: float
    hard_stop_pct: float
    soft_emergency_pct: float
    protect_emergency_pct: float
    protect_exit_floor_pct: float

    @classmethod
    def parse(cls, values):
        if not isinstance(values, dict) or set(values) != set(KEYS):
            raise ValueError("stop_policy_fields_invalid")
        if not all(finite(v) for v in values.values()):
            raise ValueError("stop_policy_nonfinite")
        v = cls(**values)
        if (not -100 < v.hard_stop_pct < v.soft_stop_pct < 0
                or not -100 < v.soft_emergency_pct <= v.soft_stop_pct
                or not -100 < v.protect_emergency_pct < 0
                or not -1000 <= v.protect_exit_floor_pct < 100
                or any(type(values[k]) is not int for k in ("grace_sec", "window_sec", "min_span_sec", "min_samples"))
                or not 0 <= v.grace_sec <= 60 or not 1 <= v.window_sec <= 30
                or not 0 <= v.min_span_sec <= v.window_sec
                or not 1 <= v.min_samples <= 120
                or not 0 <= v.below_ratio <= 1 or not 0 <= v.buffer_pct <= 1):
            raise ValueError("stop_policy_bounds_or_safety_order_invalid")
        return v

    @classmethod
    def from_rules(cls, rule):
        # The actual effective rule source is mandatory; no guessed baseline.
        from src.utils.constants import TradingConfig
        defaults = TradingConfig()
        raw = {field: rule(key) for field, key in KEYS.items()}
        raw = {k: getattr(defaults, KEYS[k]) if v is None else v for k, v in raw.items()}
        return cls.parse(raw)


@dataclass(frozen=True)
class StopDecision:
    disposition: str
    rule: str
    touch_at: float | None = None
    due_at: float | None = None


def soft_decision(values, *, profit_pct, now, touch_at=None, enabled=True, after_add=False):
    if not finite(profit_pct) or not finite(now) or now <= 0:
        return StopDecision("source_unusable", "invalid_clock_or_profit", touch_at)
    if profit_pct <= values.hard_stop_pct:
        return StopDecision("exit_candidate", "scalp_hard_stop_pct", touch_at)
    if profit_pct > values.soft_stop_pct:
        return StopDecision("hold", "soft_recovered")
    # A malformed/backwards touch cannot grant a fresh grace period.
    if touch_at is not None and (not finite(touch_at) or touch_at <= 0 or touch_at > now):
        return StopDecision("exit_candidate", "scalp_soft_stop_pct", touch_at)
    start = now if touch_at is None else touch_at
    due = start + (values.grace_sec if enabled and not after_add else 0)
    if now < due and profit_pct > values.soft_emergency_pct:
        return StopDecision("defer_until", "soft_stop_micro_grace", start, due)
    return StopDecision("exit_candidate", "scalp_soft_stop_pct", start, due)


def safety_decision(*, profit_pct, hard_pct, emergency_pct=None, protect_pct=None,
                    held_sec=0, preset_grace_sec=0, manual=False, pending=False,
                    handoff_enabled=False):
    if manual:
        return StopDecision("hold", "manual_custody")
    if pending:
        return StopDecision("hold", "pending_exit")
    if not finite(profit_pct) or not finite(hard_pct):
        return StopDecision("source_unusable", "stop_role_source_missing")
    if finite(emergency_pct) and profit_pct <= emergency_pct:
        return StopDecision("exit_candidate", "scalp_hard_stop_emergency")
    if finite(protect_pct) and profit_pct <= protect_pct:
        return StopDecision("exit_candidate", "scalp_protect_profit_stop")
    if profit_pct <= hard_pct and held_sec >= preset_grace_sec:
        return StopDecision("manual_handoff" if handoff_enabled else "exit_candidate", "scalp_hard_stop_pct")
    return StopDecision("hold", "safety_not_breached")


def append_sample(samples, *, at, price, horizon=30, cap=512):
    """Keep receipt order, preserve duplicates as no-ops, expose lost span."""
    if not finite(at) or not finite(price) or at <= 0 or price <= 0:
        return samples, "source_invalid"
    if not isinstance(samples, list) or any(not isinstance(x, dict)
            or not finite(x.get("ts")) or not finite(x.get("price"))
            or x["price"] <= 0 for x in samples):
        return [], "source_invalid"
    if samples and at <= samples[-1]["ts"]:
        return samples, "duplicate" if at == samples[-1]["ts"] else "out_of_order"
    result = [row for row in samples if at - horizon <= row["ts"] <= at]
    result.append(dict(ts=at, price=price))
    return result[-cap:], "capacity_censored" if len(result) > cap else "complete"


def protect_confirmed(values, samples, *, now, price_line, profit_pct, enabled=True, observation=None):
    if not all(finite(x) for x in (now, price_line, profit_pct)) or price_line <= 0:
        return False, "source_unusable"
    if not enabled or profit_pct <= values.protect_emergency_pct:
        return True, "emergency_or_unsmoothed"
    if values.protect_exit_floor_pct > -100 and profit_pct > values.protect_exit_floor_pct:
        return False, "profit_floor_hold"
    rows = [x for x in samples if isinstance(x,dict) and finite(x.get('ts'))
            and finite(x.get('price')) and x['price']>0 and now - values.window_sec <= x['ts'] <= now]
    if observation is not None:
        observation.update(prices=[x['price'] for x in rows],count=len(rows),
                           span=rows[-1]['ts']-rows[0]['ts'] if rows else 0)
    if (len(rows) < values.min_samples or not rows
            or rows[-1]["ts"] - rows[0]["ts"] < values.min_span_sec):
        return False, "sample_source_gap"
    prices = sorted(x["price"] for x in rows)
    mid = len(prices) // 2
    median = prices[mid] if len(prices) % 2 else (prices[mid - 1] + prices[mid]) / 2
    line = price_line * (1 - values.buffer_pct / 100)
    ratio = sum(p <= line for p in prices) / len(prices)
    if observation is not None:
        observation.update(median=median, ratio=ratio, count=len(prices),
                           span=rows[-1]['ts']-rows[0]['ts'])
    return (median <= line and ratio >= values.below_ratio), "observed"


def policy_path(data_root, target):
    date.fromisoformat(target)
    return Path(data_root) / "threshold_cycle/main_stop_confirmation" / f"main_stop_confirmation_policy_{target}.json"


def validate_bundle(bundle, target):
    if (not isinstance(bundle, dict) or bundle.get("schema") != SCHEMA or bundle.get("target_date") != target
            or bundle.get("valid_until") != target
            or not "2026-09-29" <= bundle.get("source_date", "") < target
            or bundle.get("policy_sha256") != digest({k: v for k, v in bundle.items() if k != "policy_sha256"})
            or set(bundle.get("cells") or {}) != {f"{r}|{m}" for r in ROLES for m in MARKETS}):
        raise ValueError("stop_bundle_binding_invalid")
    date.fromisoformat(target)
    date.fromisoformat(bundle["source_date"])
    for key, cell in bundle["cells"].items():
        StopValues.parse(cell["values"])
        before = StopValues.parse(cell["parent_values"])
        if cell.get("status") not in {"baseline_carry", "selected", "hold_sample", "source_gap", "hold_no_edge"}:
            raise ValueError("stop_cell_status_invalid")
        if cell["status"] == "selected":
            changed = {k for k, v in cell["values"].items() if v != asdict(before)[k]}
            if (len(changed) != 1 or not changed <= TUNABLE or cell.get("authority", {}).get("allowed_keys") != sorted(changed)
                    or not cell.get("selection_evidence", {}).get("holdout_verified")):
                raise ValueError("stop_selection_authority_invalid")
            from .main_stop_replay import candidates, choose, validate_experiment
            auth, evidence = cell['authority'], cell['selection_evidence']
            if (auth.get('target_date') != target
                    or auth.get('parent_values_sha256') != digest(asdict(before))):
                raise ValueError('stop_exact_key_succession_invalid')
            contract = validate_experiment(evidence.get('experiment'), parent_sha=digest(asdict(before)),
                source_sha=auth.get('source_sha256'), code_sha=auth.get('code_sha256'))
            name, status = choose(evidence.get('aggregates') or {}, contract)
            if (status != 'selected' or name != evidence.get('selected_candidate')
                    or asdict(candidates(before)[name]) != cell['values']
                    or any(abs(cell['values'][k]-getattr(before,k))>contract['max_daily_change'][k] for k in changed)
                    or auth.get('experiment_sha256') != contract['experiment_sha256']
                    or auth.get('operator_lock_sha256') != contract['operator_lock_sha256']):
                raise ValueError('stop_selection_evidence_invalid')
        elif cell['values'] != asdict(before):
            raise ValueError('stop_parent_carry_changed')
    if sum(c['status'] == 'selected' for c in bundle['cells'].values()) > 1:
        raise ValueError('stop_multiple_scope_change_not_authorized')
    return bundle


def load_bundle(path, sha, target, *, require_current_code=True):
    value,actual_sha = bounded_object(path)
    if actual_sha != sha:
        raise ValueError("stop_bundle_byte_hash_invalid")
    if require_current_code and value.get('code_sha256')!=implementation_sha():
        verify_runtime_code_contract(value, target)
    return validate_bundle(value, target)


def validate_runtime_environment(bundle, env):
    """An operator safety change cannot be hidden by a previously frozen pin."""
    integer_fields = {'grace_sec', 'window_sec', 'min_span_sec', 'min_samples'}
    def read(key):
        raw = env.get('KORSTOCKSCAN_' + key)
        if raw is None:
            return None
        return int(raw) if key in {KEYS[k] for k in integer_fields} else float(raw)
    effective = asdict(StopValues.from_rules(read))
    inherited = (bundle.get('parent_receipt') or {}).get('effective_values')
    if inherited is not None and asdict(StopValues.parse(inherited)) != effective:
        raise ValueError('stop_parent_effective_environment_changed')
    if any(any(cell['parent_values'][key] != effective[key] for key in set(KEYS) - TUNABLE)
           for cell in bundle['cells'].values()):
        raise ValueError('stop_parent_effective_environment_changed')


_LOADED = None
_LOADED_ENV = None
_RECEIPT_KEY = None


def preload(env=None):
    global _LOADED, _LOADED_ENV
    env = os.environ if env is None else env
    keys = (ENV_FILE, ENV_SHA, ENV_DATE)
    if not any(env.get(k) for k in keys):
        _LOADED = None
        _LOADED_ENV = None
        return None
    identity = tuple(env.get(k) for k in keys)
    if identity == _LOADED_ENV and _LOADED is not None:
        return _LOADED[0]
    bundle = load_bundle(env[ENV_FILE], env[ENV_SHA], env[ENV_DATE])
    cells = MappingProxyType({k: StopValues.parse(c["values"]) for k, c in bundle["cells"].items()})
    _LOADED = (bundle["policy_sha256"], bundle["target_date"], cells)
    _LOADED_ENV = identity
    return bundle["policy_sha256"]


def record_loaded_policy(data_root):
    """One startup receipt proves lookup loading, not an exit or a fill."""
    global _RECEIPT_KEY
    if not _LOADED or not _LOADED_ENV:return None
    from src.engine.lifecycle.research_admission import start_ticks
    from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
    pid=os.getpid();ticks=start_ticks(pid)
    key=(pid,ticks,*_LOADED_ENV)
    if key==_RECEIPT_KEY:return None
    body=dict(schema='main_stop_loaded_policy_v1',pid=pid,start_ticks=ticks,
        process_cwd=str(Path.cwd().resolve()),target_date=_LOADED[1],policy_sha256=_LOADED[0],
        policy_file=_LOADED_ENV[0],policy_byte_sha256=_LOADED_ENV[1],
        loaded_cells_sha256=digest({k:asdict(v) for k,v in _LOADED[2].items()}))
    body['receipt_sha256']=digest(body)
    path=Path(data_root)/'runtime/main_stop_confirmation'/body['target_date']/f'pid_{pid}_{ticks}.json'
    _atomic(path,body);_RECEIPT_KEY=key
    return path


def pin(*, position_key, role, market, target, baseline):
    values, identity, origin = baseline, digest(asdict(baseline)), "effective_legacy_rules"
    if _LOADED and _LOADED[1] == target and role in ROLES and market in MARKETS:
        values, identity, origin = _LOADED[2][role + "|" + market], _LOADED[0], "preopen_policy"
    body = dict(schema=PIN_SCHEMA, position_key=position_key, role=role, market=market,
                target_date=target, policy_sha256=identity, values=asdict(values), origin=origin)
    return dict(body, pin_sha256=digest(body))


def pin_values(value, position_key):
    if (not isinstance(value, dict) or value.get("schema") != PIN_SCHEMA
            or value.get("position_key") != position_key
            or value.get("role") not in ROLES or value.get("market") not in (*MARKETS, "UNKNOWN")
            or (value.get("market") == "UNKNOWN" and value.get("origin") != "effective_legacy_rules")
            or value.get("pin_sha256") != digest({k: v for k, v in value.items() if k != "pin_sha256"})):
        raise ValueError("stop_pin_invalid")
    return StopValues.parse(value.get("values"))


def protect_line_origin(stock):
    line=stock.get('trailing_stop_price')
    if not finite(line) or line<=0:return 'not_applicable_no_active_line'
    if stock.get('manual_control_exclusion_blocked'):return 'manual_existing'
    if stock.get('pyramid_count') or stock.get('last_add_type')=='PYRAMID':return 'legacy_retired'
    return 'unverified_existing'


def preset_stop_receipt(stock, *, at, evaluator, hard_pct, grace_sec, emergency_pct,
                        held_sec, enabled, protect_pct=None):
    """Observation of the evaluated preset; never replaces the common pin."""
    from .position_peak_ledger import position_cycle_id
    pin = stock.get('main_stop_policy_pin') or {}
    if not isinstance(pin, dict):
        raise ValueError('stop_pin_invalid')
    key = position_cycle_id(stock)
    pin_values(pin, key)
    body = dict(schema='main_preset_stop_receipt_v1', position_key=key,
        pin_sha256=pin['pin_sha256'], at=at, evaluator=evaluator,
        hard_stop_pct=hard_pct, grace_sec=grace_sec, emergency_pct=emergency_pct,
        held_sec=held_sec, enabled=enabled, protect_pct=protect_pct)
    return dict(body, sha256=digest(body))


def handoff_source(stock, *, at, registered, exit_rule, profit_pct, source_stage,
                   preset_stop=None):
    """Seal the already completed registration result, not a SELL receipt."""
    from .position_peak_ledger import position_cycle_id
    key = position_cycle_id(stock)
    pin = stock.get('main_stop_policy_pin') or {}
    if not isinstance(pin, dict):
        raise ValueError('stop_pin_invalid')
    values = pin_values(pin, key)
    if type(registered) is not bool or not finite(at) or not finite(profit_pct):
        raise ValueError('stop_handoff_result_invalid')
    body = dict(schema='main_stop_handoff_source_v1', position_key=key,
        record_id=stock.get('id'), role=pin['role'], market=pin['market'], at=at,
        pin_sha256=pin['pin_sha256'], source_stop_values=asdict(values),
        owner='main', registered=registered, exit_rule=exit_rule,
        decision_profit_pct=profit_pct, source_stage=source_stage,
        preset_stop=preset_stop, handoff_enabled=True, actual_order_submitted=False,
        actual_realized_net_krw=None, allowed_runtime_apply=False)
    return dict(body, source_sha256=digest(body))


def source_row(stock, *, at, bid, bid_qty, quote, coverage_complete, cost_model, vote_source,
               automatic_management_allowed=False, runtime_flags=None, decision_profit_pct=None, seal=True,
               post_add_vote_source=None, post_add_inputs=None, preset_stop=None):
    """Project the already supplied holding snapshot; no I/O or new collection."""
    value = stock.get('main_stop_policy_pin') or {}
    from .position_peak_ledger import position_cycle_id
    values = stock.get('_main_stop_typed_values')
    if not isinstance(values,StopValues) or stock.get('_main_stop_position_key')!=position_cycle_id(stock):
        values = pin_values(value, position_cycle_id(stock))
    # A pin is immutable for the position; avoid recursive dataclass projection
    # and hashing on each capture. The observation queue freezes the envelope.
    cached=stock.get('_main_stop_source_values')
    if cached is None or cached[0]!=value['pin_sha256']:
        projected=asdict(values)
        cached=(value['pin_sha256'],projected,digest(projected))
        stock['_main_stop_source_values']=cached
    qty = stock.get('buy_qty')
    average = stock.get('buy_price')
    body = dict(schema='main_stop_source_v1',position_key=position_cycle_id(stock),
        record_id=stock.get('id'),role=value['role'],market=value['market'],at=at,
        bid=bid,bid_qty=bid_qty,route=quote.get('market_route'),item=quote.get('item'),
        transport_epoch=quote.get('transport_epoch'),quote_at=quote.get('observed_epoch'),
        pin_sha256=value['pin_sha256'],parent_values_sha256=cached[2],
        source_stop_values=cached[1],
        preset_stop=preset_stop,
        owner='main',automatic_management_allowed=automatic_management_allowed is True,quantity=qty,
        buy_basis_krw=qty*average if finite(qty) and finite(average) else None,
        decision_profit_pct=decision_profit_pct,
        cost_model=cost_model,holding_ai_required=vote_source is not None,
        holding_vote_source=vote_source,manual=bool(stock.get('manual_control_exclusion_blocked')),
        pending_exit=bool(stock.get('exit_requested')),add_count=stock.get('add_count',0),
        pending_add=bool(stock.get('pending_add_qty') or stock.get('pending_add_ord_no') or stock.get('pending_add_ord_nos')),
        protect_line=stock.get('trailing_stop_price'),protect_line_origin=protect_line_origin(stock),
        post_add_generation=stock.get('post_add_economic_generation'),
        post_add_vote_source=post_add_vote_source,post_add_failure_inputs=post_add_inputs,
        coverage_complete=bool(coverage_complete),
        capture_rejected_count=stock.get('main_stop_source_rejected_count',0),
        partial_fill=bool(stock.get('entry_partial_fill_deferred_notice')))
    flags = runtime_flags or {}
    body.update({key: flags.get(key) for key in (
        'grace_enabled', 'protect_enabled', 'handoff_enabled', 'vote_max_worsen_pct')})
    return dict(body,source_sha256=digest(body)) if seal else body


_SOURCE_SINK = None

# The fast evaluator freezes research inputs before claiming an exit, but
# admits them to the shared writer only after the critical disposition. This
# avoids writer/GIL work competing with an already observed safety crossing.
from contextlib import contextmanager
from contextvars import ContextVar
_DEFERRED_SOURCES = ContextVar('main_stop_deferred_sources', default=None)


@contextmanager
def defer_source_capture():
    if _DEFERRED_SOURCES.get() is not None:
        yield
        return
    pending = []
    token = _DEFERRED_SOURCES.set(pending)
    try:
        yield
    finally:
        _DEFERRED_SOURCES.reset(token)
        for stock, code, name, record_id, raw in pending:
            try:
                accepted = _submit_source(code, name, record_id, raw)
            except Exception:
                accepted = False
            if not accepted:
                stock['main_stop_source_gap'] = 'observation_queue_rejected'
                stock['main_stop_source_rejected_count'] = stock.get('main_stop_source_rejected_count', 0) + 1


def configure_source_sink(sink):
    global _SOURCE_SINK
    _SOURCE_SINK=sink
    from .main_custody_checkpoint import configure_sink
    configure_sink(sink)


def _append_source(code,name,record_id,row):
    from src.utils.pipeline_event_logger import emit_pipeline_event
    if isinstance(row, str):
        raw = row
        row = json.loads(row)
    else:
        raw = json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False)
    source_sha256 = hashlib.sha256(raw.encode()).hexdigest()
    # The producer already froze canonical bytes. Seal without decoding and
    # recursively serializing the same nested policy/cost snapshot again.
    sealed = raw[:-1] + ',"source_sha256":"' + source_sha256 + '"}'
    result = emit_pipeline_event('HOLDING_PIPELINE',name,code,'main_stop_source',record_id=record_id,
        observed_at_epoch=row['at'],fields=dict(main_stop_source=sealed,
            stop_source_sha256=source_sha256,position_key=row['position_key'],
            threshold_family='main_stop_confirmation',allowed_runtime_apply=False,actual_order_submitted=False,
            broker_order_forbidden=True,decision_authority='source_only_stop_research',
            pipeline_lifecycle_population_scope='real_record_bound' if record_id else 'unclassified_missing_record'))
    # A queued research writer must not keep the GIL for a whole drain batch
    # while a burst of safety evaluations is ready. Yield only this worker;
    # never sleep, block, or retry on the trading thread.
    import time
    time.sleep(0)
    return result


def _submit_source(code,name,record_id,row):
    if _SOURCE_SINK is None:return False
    try:
        result=_SOURCE_SINK(_append_source,code,name,record_id,row,
                            observation_category='main_stop')
        return isinstance(result,dict) and result.get('status')=='queued'
    except (ValueError,TypeError,RuntimeError):return False


def enqueue_source(stock,code,row):
    """Freeze before disposition; retain the existing shared queue budgets."""
    pending = _DEFERRED_SOURCES.get()
    if pending is not None:
        if len(pending) >= 2:return False
        raw = json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False)
        if len(raw.encode()) > 64 * 1024:return False
        pending.append((stock, code, stock.get('name') or code, stock.get('id'), raw))
        return True
    return _submit_source(code, stock.get('name') or code, stock.get('id'), row)
