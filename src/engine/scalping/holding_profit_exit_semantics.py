"""Read-only semantic checks for the real main trailing-profit exit chain."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
from typing import Any, Callable
from zoneinfo import ZoneInfo

from src.engine.ai.holding_exit_vote import (
    PATH_POLICY_BY_MARKET, input_snapshot_id, path_signal_snapshot,
)
from src.engine.scalping.trailing_threshold_policy import market_type_at
from src.engine.scalping.trailing_exit_decision import EXIT_WAIT_STAGES
from src.engine.scalping.trailing_mechanical_policy import (
    classifier_hash, market_values_hash, CLASSIFIER_VERSION,
)

KST = ZoneInfo("Asia/Seoul")
LIFECYCLE_STATES = {"signal_observed", "deferred", "guard_wait", "pending_submit",
                    "pending_terminal", "completed"}
ECONOMICS_STATES = {"pending", "verified", "unavailable"}


def _epoch(value: Any) -> float | None:
    if isinstance(value, datetime):
        return (value if value.tzinfo else value.replace(tzinfo=KST)).timestamp()
    try:
        return _epoch(datetime.fromisoformat(str(value)))
    except (ValueError, TypeError):
        return None


def event_generation(events: list[Any]) -> str:
    digest = hashlib.sha256()
    for event in events:
        material = {"at": _epoch(event.emitted_at), "stage": event.stage,
                    "record_id": str(event.record_id), "fields": _fields(event)}
        digest.update(json.dumps(material, sort_keys=True, separators=(",", ":"),
                                 default=str, allow_nan=False).encode())
        digest.update(b"\n")
    return digest.hexdigest()


def _mechanical_check(transition: dict, snapshot: dict, receipt: dict | None,
                      market: str, target_date: str) -> str | None:
    if not receipt:
        return "tp_mechanical_policy_receipt_missing"
    try:
        vector, classifier = receipt["market_values"], receipt["classifier_parameters"]
        observed_vector = transition.get("scalp_trailing_market_values")
        if isinstance(observed_vector, str):
            observed_vector = json.loads(observed_vector)
        vector_sha = market_values_hash(vector, classifier)
        effective = vector[market]
        typed_sha = transition.get('effective_trailing_policy_sha256')
        if typed_sha:
            from src.engine.scalping.trailing_situation_policy import PreparedTrailingPolicy, PreparedPin
            policy = receipt.get('situation_policy')
            if not isinstance(policy, dict) or policy.get('policy_sha256') != typed_sha:
                return 'tp_situation_policy_receipt_missing'
            prepared = PreparedTrailingPolicy.prepare(policy, target_date=target_date, parent_sha256=vector_sha)
            raw_pin = transition.get('trailing_situation_pin')
            raw_pin = json.loads(raw_pin) if isinstance(raw_pin, str) else raw_pin
            position_key = transition.get('position_key')
            pin = PreparedPin.prepare(raw_pin, position_key)
            snapshot_pin = snapshot.get('trailing_situation_pin')
            snapshot_pin = json.loads(snapshot_pin) if isinstance(snapshot_pin, str) else snapshot_pin
            if (transition.get('classification_origin_hash') != pin.classification_origin_hash
                    or snapshot.get('position_key') != position_key
                    or snapshot_pin != raw_pin
                    or snapshot.get('effective_trailing_policy_sha256') != typed_sha):
                return 'tp_situation_origin_or_snapshot_unbound'
            effective = prepared.effective(market, pin, position_key=pin.position_key, target_date=target_date)
        if (receipt["market_values_sha256"] != vector_sha
                or receipt["classifier_version"] != CLASSIFIER_VERSION
                or receipt["classifier_sha256"] != classifier_hash(classifier)
                or transition.get("scalp_trailing_market_values_sha256") != vector_sha
                or observed_vector != vector
                or transition.get("scalp_trailing_policy_date") != target_date
                or transition.get("classifier_version") != CLASSIFIER_VERSION
                or transition.get("classifier_sha256") != receipt["classifier_sha256"]
                or _float(transition.get("trailing_start_pct")) != effective["SCALP_TRAILING_START_PCT"]):
            return "tp_mechanical_policy_generation_mismatch"
        crossing = _first_crossing_fields(transition)
        if (_float(transition.get("raw_limit_pct", transition.get("trailing_limit_pct")))
                != effective[crossing["threshold_key"]]):
            return "tp_mechanical_policy_width_mismatch"
        pinned = snapshot.get("mechanical_policy_receipt")
        if isinstance(pinned, str):
            pinned = json.loads(pinned)
        if (not isinstance(pinned, dict)
                or pinned.get("scalp_trailing_market_values_sha256") != vector_sha
                or pinned.get("scalp_trailing_policy_date") != target_date):
            return "tp_snapshot_mechanical_policy_unbound"
    except (KeyError, TypeError, ValueError):
        return "tp_mechanical_policy_contract_invalid"
    return None


def _first_crossing_fields(fields: dict) -> dict:
    raw = fields.get("first_crossing")
    return json.loads(raw) if isinstance(raw, str) else (raw or {})


def _float(value: Any) -> float | None:
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _fields(event: Any) -> dict[str, Any]:
    return event.fields if isinstance(getattr(event, "fields", None), dict) else {}


def _first_crossing(event: Any) -> dict[str, Any] | None:
    raw = _fields(event).get("first_crossing")
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _latency_distribution(rows: list[Any], field: str) -> dict[str, Any]:
    values = sorted(value for row in rows
                    if (value := _float(_fields(row).get(field))) is not None
                    and value >= 0)
    if not values:
        return {"count": 0, "p50_ms": None, "p95_ms": None, "p99_ms": None}
    return {
        "count": len(values),
        "p50_ms": values[math.ceil(len(values) * 0.50) - 1],
        "p95_ms": values[math.ceil(len(values) * 0.95) - 1],
        "p99_ms": values[math.ceil(len(values) * 0.99) - 1],
    }


def audit_profit_exit_flow(
    events: list[Any], *, target_date: str,
    load_votes: Callable[[str], list[dict[str, Any]]],
    observation: dict[str, Any] | None = None,
    policies: dict[tuple[str, str], dict[str, Any]] | None = None,
    policy_bundle_sha256: str | None = None,
    as_of: datetime | None = None, source_generation: str | None = None,
    mechanical_policy_receipt: dict | None = None, consumed_pid: int | None = None,
    consumed_pids: list[int] | None = None,
    mechanical_receipts_by_pid: dict[int, dict] | None = None,
    model: str = "gpt-5.4-nano",
) -> dict[str, Any]:
    """Audit evidence order; absent natural positions remain valid empty."""
    selected = policies or PATH_POLICY_BY_MARKET
    cutoff = _epoch(as_of) if as_of is not None else max(
        (_epoch(event.emitted_at) or 0 for event in events), default=0)
    events = [event for event in events if (at := _epoch(event.emitted_at)) is not None
              and datetime.fromtimestamp(at, KST).date().isoformat() == target_date
              and at <= cutoff]
    generation = event_generation(events)
    if source_generation is not None and source_generation != generation:
        raise ValueError("holding_semantic_source_generation_mismatch")
    stages = Counter()
    scoped: dict[str, list[Any]] = defaultdict(list)
    for event in events:
        fields = _fields(event)
        if fields.get("pipeline_lifecycle_population_scope") != "real_record_bound":
            continue
        record_id = str(getattr(event, "record_id", "") or "").strip()
        if not record_id:
            continue
        stage = str(getattr(event, "stage", "") or "")
        stages[stage] += 1
        scoped[record_id].append(event)

    findings: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    policy_gaps: list[dict[str, str]] = []
    runtime_gaps: list[dict[str, str]] = []
    counts = Counter()
    lifecycles: list[dict] = []
    market_trigger = Counter()
    market_trigger_kind = Counter()
    timing_rows: dict[str, list[Any]] = defaultdict(list)
    observation_at = _epoch(((observation or {}).get("meta") or {}).get("knowledge_cutoff"))
    observation_available = observation_at is not None and observation_at <= cutoff
    if not observation_available:
        observation = {}
    strict_ids = set(str(value) for value in (
        (observation or {}).get("completed_population_quality") or {}
    ).get("strict_completed_position_ids") or [])
    outcomes = {
        str(row.get("record_id")): row
        for row in (observation or {}).get("position_outcomes") or []
        if isinstance(row, dict) and row.get("record_id") is not None
    }

    def add(bucket: list[dict[str, str]], record_id: str, reason: str) -> None:
        bucket.append({"position_id": record_id, "reason": reason})

    for record_id, rows in scoped.items():
        rows = sorted(rows, key=lambda row: _epoch(row.emitted_at))
        row_order = {id(row): index for index, row in enumerate(rows)}
        counts["holding_started"] += int(any(
            getattr(row, "stage", "") == "holding_started" for row in rows))
        reviews = [row for row in rows if getattr(row, "stage", "") == "holding_path_review"]
        counts["review_due"] += len(reviews)
        counts["review_unchanged_input"] += sum(
            _fields(row).get("status") == "unchanged_input_skip" for row in reviews)
        counts["vote_source_gap"] += sum(
            getattr(row, "stage", "") == "holding_path_vote_source_gap" for row in rows)
        collected = [row for row in rows if getattr(row, "stage", "") == "holding_path_votes_collected"]
        timing_rows["vote_claim_ms"].extend(collected)
        timing_rows["engine_call_ms"].extend(collected)
        timing_rows["vote_store_ms"].extend(collected)
        counts["vote_bundle_persisted"] += len(collected)
        counts["provider_called"] += sum(
            max(0, int(_float(_fields(row).get("provider_calls")) or 0))
            for row in collected)
        snapshots = [event for event in rows
                     if getattr(event, "stage", "") == "holding_path_signal_snapshot"
                     and _fields(event).get("path_id") == "EXIT_TRAILING_TP"]
        timing_rows["signal_snapshot_ms"].extend(snapshots)
        timing_rows["signal_provider_wait_ms"].extend(snapshots)
        transitions = [event for event in rows
                       if getattr(event, "stage", "") == "scalp_trailing_input_transition"]
        exits = [event for event in rows if getattr(event, "stage", "") == "exit_signal"
                 and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"]
        sent = [event for event in rows if getattr(event, "stage", "") == "sell_order_sent"
                and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"]
        partial = [event for event in rows
                   if getattr(event, "stage", "") == "sell_partial_fill_progress"
                   and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"]
        completed = [event for event in rows if getattr(event, "stage", "") == "sell_completed"
                     and _fields(event).get("exit_rule") == "scalp_trailing_take_profit"]
        if not (snapshots or exits or sent or partial or completed):
            continue
        counts["tp_signal_snapshots"] += len(snapshots)
        counts["tp_exit_signals"] += len(exits)
        counts["tp_sell_submitted"] += len(sent)
        counts["tp_sell_partial_fill"] += len(partial)
        counts["tp_sell_completed"] += len(completed)
        counts["tp_arm_observed"] += sum(
            str(_fields(row).get("armed")).lower() == "true"
            for row in transitions)
        counts["tp_source_ready"] += sum(
            str(_fields(row).get("tuning_grid_source_complete")).lower() == "true"
            for row in transitions)
        counts["tp_veto_defer"] += sum(
            getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
            for row in rows)
        snapshot_ids = [str(_fields(row).get("signal_id") or "") for row in snapshots]
        snapshot_keys = [(_fields(row).get("position_key"), _fields(row).get("buy_fill_identity"),
                          _fields(row).get("signal_id")) for row in snapshots]
        if len(snapshot_keys) != len(set(snapshot_keys)):
            add(findings, record_id, "tp_duplicate_signal_snapshot_id")
        for row in exits:
            if str(_fields(row).get("holding_path_signal_id") or "") not in snapshot_ids:
                add(gaps, record_id, "tp_exit_without_vote_snapshot")
        for row in sent:
            if not any(
                _fields(exit_row).get("holding_path_signal_id")
                == _fields(row).get("holding_path_signal_id")
                for exit_row in exits
            ):
                add(findings, record_id, "tp_sell_without_exit_signal")
        for row in (*partial, *completed):
            fields = _fields(row)
            signal_id = str(fields.get("holding_path_signal_id") or "")
            if signal_id and signal_id not in snapshot_ids:
                add(gaps, record_id, "tp_terminal_signal_generation_unmatched")
            if (fields.get("holding_path_terminal_signal_binding")
                    != "same_position_buy_generation"):
                add(gaps, record_id, "tp_terminal_buy_generation_unbound")
            order_no = str(fields.get("order_no") or "")
            submitted_orders = {
                str(_fields(item).get("ord_no") or "") for item in sent
            }
            if order_no not in {"", "-"} and submitted_orders and order_no not in submitted_orders:
                add(gaps, record_id, "tp_terminal_order_number_unmatched")
        for row in completed:
            fields = _fields(row)
            if _float(fields.get("remaining_sell_qty")) is None:
                add(gaps, record_id, "tp_terminal_remaining_quantity_missing")
            elif _float(fields.get("remaining_sell_qty")) != 0.0:
                add(findings, record_id, "tp_terminal_remaining_quantity_nonzero")
        counted_vote_keys: set[tuple[str, str, str]] = set()
        for event in snapshots:
            fields = _fields(event)
            signal_at = _float(fields.get("signal_at"))
            market = str(fields.get("market") or "")
            signal_id = str(fields.get("signal_id") or "")
            position_key = str(fields.get("position_key") or "")
            buy_identity = str(fields.get("buy_fill_identity") or "")
            policy = selected.get(("EXIT_TRAILING_TP", market))
            if (signal_at is None or not signal_id or not policy
                    or market_type_at(signal_at) != market
                    or position_key != f"record:{record_id}"
                    or len(buy_identity) != 64):
                add(findings, record_id, "tp_signal_identity_or_market_invalid")
                continue
            if fields.get("policy_sha256") != input_snapshot_id(policy):
                add(findings, record_id, "tp_signal_policy_hash_mismatch")
                continue
            if (policy_bundle_sha256 is not None
                    and fields.get("policy_bundle_sha256") != policy_bundle_sha256):
                add(policy_gaps, record_id, "tp_signal_bundle_hash_mismatch")
            elif (policy_bundle_sha256 is not None
                  and fields.get("policy_load_status") != "estimated_provisional_loaded"):
                add(runtime_gaps, record_id, "tp_runtime_policy_load_unproven")
            elif (policy_bundle_sha256 is None
                  and fields.get("policy_load_status") == "estimated_provisional_loaded"):
                add(policy_gaps, record_id, "tp_loaded_policy_bundle_missing")
            crossing_rows = [row for row in transitions
                             if _epoch(row.emitted_at) <= _epoch(event.emitted_at)
                             and _fields(row).get("position_key") == position_key
                             and (_first_crossing(row) or {}).get("at_epoch") == signal_at]
            if not crossing_rows:
                add(gaps, record_id, "tp_first_crossing_transition_missing")
            else:
                crossing = _first_crossing(crossing_rows[-1]) or {}
                transition = _fields(crossing_rows[-1])
                if (crossing.get("market") != market
                        or crossing.get("threshold_key") not in {
                            "SCALP_TRAILING_LIMIT_WEAK", "SCALP_TRAILING_LIMIT_STRONG"
                        }
                        or transition.get("tuning_exit_allowed_by_clock") not in {"True", "true", True}):
                    add(findings, record_id, "tp_crossing_arm_or_clock_invalid")
                pid_receipt = (mechanical_receipts_by_pid or {}).get(_float(fields.get("runtime_pid")), mechanical_policy_receipt)
                mechanical_error = _mechanical_check(transition, fields, pid_receipt, market, target_date)
                if mechanical_error:
                    add(policy_gaps, record_id, mechanical_error)
                valid_pids = set(consumed_pids or ([consumed_pid] if consumed_pid is not None else []))
                if _float(fields.get("runtime_pid")) not in valid_pids:
                    add(runtime_gaps, record_id, "tp_mechanical_pid_consumption_unproven")
                evaluator = str(transition.get("evaluator") or "normal")
                kind = "fast" if evaluator.startswith("fast") else "normal"
                market_trigger[f"{market}|{kind}"] += 1
                trigger_kind = str(transition.get("trigger_kind") or "")
                if trigger_kind == "trailing_peak_worsen_floor":
                    market_trigger_kind[f"{market}|{kind}|{trigger_kind}"] += 1
                else:
                    add(gaps, record_id, "tp_first_crossing_trigger_kind_missing_or_invalid")
            try:
                votes = load_votes(position_key)
            except (OSError, ValueError):
                add(gaps, record_id, "tp_vote_ledger_unreadable")
                votes = []
            for vote in votes:
                if (vote.get("path_id") != "EXIT_TRAILING_TP"
                        or vote.get("market") != market
                        or any((at := _float(vote.get(key))) is None or at > min(cutoff, signal_at)
                               for key in ("requested_at", "received_at", "persisted_at"))):
                    continue
                identity = (str(vote.get("path_id")), str(vote.get("market")),
                            str(vote.get("input_snapshot_id")))
                if identity in counted_vote_keys:
                    continue
                counted_vote_keys.add(identity)
                counts["tp_vote_claimed"] += bool(vote.get("path_decision_input_sha256"))
                counts["tp_vote_provider_called"] += vote.get("provider_called") is True
                counts["tp_vote_valid_persisted"] += (
                    vote.get("status") == "VALID" and _float(vote.get("persisted_at")) is not None)
            if not votes and _float(fields.get("vote_count")):
                add(gaps, record_id, "tp_vote_ledger_missing")
            expected = path_signal_snapshot(
                votes, position_key=position_key, market=market,
                session_key=str(fields.get("session_key") or ""),
                path_id="EXIT_TRAILING_TP", model=model,
                signal_at=signal_at, policy=policy,
                buy_fill_identity=buy_identity,
            )
            count = _float(fields.get("vote_count"))
            if (count is None or count != expected["vote_count"]
                    or fields.get("decision") != expected["decision"]):
                add(findings if votes else gaps, record_id,
                    "tp_vote_snapshot_replay_mismatch")
            counts[f"tp_decision_{fields.get('decision') or 'UNKNOWN'}"] += 1
            matching_exit = [row for row in exits if
                             _fields(row).get("holding_path_signal_id") == signal_id]
            matching_sent = [row for row in sent if
                             _fields(row).get("holding_path_signal_id") == signal_id]
            matching_completed = [row for row in completed if
                                  _fields(row).get("holding_path_signal_id") == signal_id]
            matching_partial = [row for row in partial if
                                _fields(row).get("holding_path_signal_id") == signal_id]
            for row in (*matching_exit, *matching_sent, *matching_partial, *matching_completed):
                bound = _fields(row)
                if (bound.get("holding_path_position_key") != position_key
                        or bound.get("holding_path_buy_fill_identity") != buy_identity):
                    add(gaps, record_id, "tp_lifecycle_buy_generation_unbound")
            def same_generation(row: Any) -> bool:
                return (_fields(row).get("holding_path_position_key") == position_key
                        and _fields(row).get("holding_path_buy_fill_identity") == buy_identity)
            matching_exit = [row for row in matching_exit if same_generation(row)]
            matching_sent = [row for row in matching_sent if same_generation(row)]
            matching_partial = [row for row in matching_partial if same_generation(row)]
            matching_completed = [row for row in matching_completed if same_generation(row)]
            if any(not str(_fields(row).get("ord_no") or "") for row in matching_sent):
                add(gaps, record_id, "tp_submit_order_identity_missing")
            matching_sent = [row for row in matching_sent
                             if str(_fields(row).get("ord_no") or "")]
            submitted_orders = {str(_fields(row)["ord_no"]) for row in matching_sent}
            for row in (*matching_partial, *matching_completed):
                if (str(_fields(row).get("order_no") or "") not in submitted_orders
                        or not any(
                            str(_fields(attempt).get("ord_no")) == str(_fields(row).get("order_no"))
                            and _epoch(attempt.emitted_at) <= _epoch(row.emitted_at)
                            for attempt in matching_sent)):
                    add(gaps, record_id, "tp_terminal_attempt_unmatched")
            def matches_submitted_attempt(row: Any) -> bool:
                return any(str(_fields(attempt).get("ord_no")) == str(_fields(row).get("order_no"))
                           and _epoch(attempt.emitted_at) <= _epoch(row.emitted_at)
                           for attempt in matching_sent)
            matching_partial = [row for row in matching_partial if matches_submitted_attempt(row)
                and _fields(row).get("holding_path_terminal_signal_binding") == "same_position_buy_generation"]
            matching_completed = [row for row in matching_completed if matches_submitted_attempt(row)
                and _fields(row).get("holding_path_terminal_signal_binding") == "same_position_buy_generation"
                and _float(_fields(row).get("remaining_sell_qty")) == 0.0]
            if any(_epoch(row.emitted_at) < _epoch(event.emitted_at) for row in matching_exit):
                add(findings, record_id, "tp_exit_before_vote_snapshot")
            if (matching_exit and any(_epoch(row.emitted_at) < _epoch(matching_exit[0].emitted_at)
                                      for row in matching_sent)):
                add(findings, record_id, "tp_submit_before_exit_signal")
            if fields.get("decision") == "VETO" and matching_exit:
                elapsed = _epoch(matching_exit[0].emitted_at) - signal_at
                if elapsed < 0:
                    add(findings, record_id, "tp_veto_exit_before_first_crossing")
                elif elapsed < policy["max_defer_sec"] and not any(
                    _fields(row).get("signal_id") == signal_id
                    for row in rows if getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
                ):
                    add(gaps, record_id, "tp_veto_defer_or_safety_reason_missing")
            deferrals = [row for row in rows
                         if getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
                         and _fields(row).get("signal_id") == signal_id
                         and _fields(row).get("position_key") == position_key
                         and _fields(row).get("buy_fill_identity") == buy_identity]
            last_exit_index = max((row_order[id(row)] for row in matching_exit), default=-1)
            guards = [row for row in rows if getattr(row, "stage", "") in EXIT_WAIT_STAGES
                      and row_order[id(row)] > last_exit_index
                      and _fields(row).get("holding_path_signal_id") == signal_id
                      and _fields(row).get("holding_path_position_key") == position_key
                      and _fields(row).get("holding_path_buy_fill_identity") == buy_identity]
            state = ("completed" if matching_completed else
                     "pending_terminal" if matching_sent else
                     "guard_wait" if guards else
                     "pending_submit" if matching_exit else
                     "deferred" if deferrals and _fields(deferrals[-1]).get("phase") != "released"
                     else "signal_observed")
            economics = "pending"
            outcome = outcomes.get(record_id)
            if matching_completed:
                economics = "unavailable"
                cost = (outcome or {}).get("actual_cost_reconciliation") or {}
                known_at = max(_epoch(cost.get("cost_available_at")) or float("inf"),
                               _epoch(cost.get("reconciled_at")) or float("inf"))
                if (record_id in strict_ids and outcome
                        and outcome.get("sell_quantity_conserved") is True
                        and _float(outcome.get("profit_rate")) is not None
                        and _float(outcome.get("realized_pnl_krw")) is not None
                        and cost.get("status") == "actual_cost_reconciled" and known_at <= cutoff
                        and outcome.get("holding_path_buy_fill_identity") == buy_identity):
                    economics = "verified"
                elif known_at > cutoff and cost.get("status") == "actual_cost_reconciled":
                    economics = "pending"
            if state in {"pending_submit", "pending_terminal"}:
                counts[f"tp_{state}"] += 1
            counts[f"tp_economics_{economics}"] += 1
            lifecycles.append({
                "position_key": position_key, "buy_fill_identity": buy_identity,
                "signal_id": signal_id, "lifecycle_state": state,
                "economics_status": economics, "signal_at": signal_at,
                "elapsed_sec": max(0, cutoff - signal_at),
                "blocking_reason": (_fields(guards[-1]).get("reason") or guards[-1].stage) if guards else None,
                "orders": sorted(submitted_orders),
                "attempts": [{"order_no": _fields(row).get("ord_no"),
                              "attempt_id": _fields(row).get("attempt_id"),
                              "submitted_at": row.emitted_at.isoformat(),
                              "terminal_events": [getattr(item, "stage", "") for item in rows
                                  if _fields(item).get("order_no") == _fields(row).get("ord_no")
                                  and _fields(item).get("holding_path_signal_id") == signal_id
                                  and _fields(item).get("holding_path_buy_fill_identity") == buy_identity
                                  and getattr(item, "stage", "") in {
                                      "sell_partial_fill_progress", "sell_completed",
                                      "sell_order_cancelled", "sell_order_rejected"}]}
                             for row in matching_sent],
            })
        if completed and not sent:
            add(gaps, record_id, "tp_completed_without_submit_receipt")
        outcome = outcomes.get(record_id)
        if completed and outcome is not None:
            if outcome.get("sell_quantity_conserved") is not True:
                add(findings, record_id, "tp_sell_quantity_not_conserved")
            if (_float(outcome.get("profit_rate")) is None
                    or _float(outcome.get("realized_pnl_krw")) is None):
                counts["tp_economics_null"] += 1
            if not outcome.get("exact_sell_fill_time"):
                counts["tp_forward_censored_no_sell_time"] += 1
            elif (outcome.get("post_sell_status") == "pass"
                  and (_epoch(outcome.get("post_sell_observed_at")) or float("inf")) <= cutoff):
                counts["tp_forward_observed"] += 1
            else:
                counts["tp_forward_censored_source_or_horizon_gap"] += 1
        buy_qty = max((_float(_fields(row).get("buy_qty")) or 0.0
                       for row in exits), default=0.0)
        if buy_qty and any((_float(_fields(row).get("qty")) or 0.0) > buy_qty
                           for row in sent):
            add(findings, record_id, "tp_submitted_quantity_exceeds_buy")
    semantic_status = ("semantic_contract_invalid" if findings else
              "policy_binding_gap" if policy_gaps else
              "runtime_not_consumed" if runtime_gaps else
              "source_gap" if gaps else
              "valid_empty" if not counts["tp_signal_snapshots"] else "pass")
    status = semantic_status
    if semantic_status == "pass":
        status = ("pending_submit" if counts["tp_pending_submit"] else
                  "pending_terminal" if counts["tp_pending_terminal"] else "pass")
    return {
        "schema": "holding_profit_exit_semantics_v2",
        "target_date": target_date,
        "status": status,
        "semantic_status": semantic_status,
        "lifecycle": lifecycles,
        "economics_status": ("unavailable" if counts["tp_economics_unavailable"] else
                             "pending" if counts["tp_economics_pending"] or not lifecycles else "verified"),
        "as_of": datetime.fromtimestamp(cutoff, KST).isoformat() if cutoff else
                 f"{target_date}T00:00:00+09:00",
        "source_generation": generation,
        "mechanical_policy_sha256": (mechanical_policy_receipt or {}).get("market_values_sha256"),
        "mechanical_policy_sha256_by_pid": {str(pid): receipt.get("market_values_sha256")
                                            for pid, receipt in (mechanical_receipts_by_pid or {}).items()},
        "consumed_pid": consumed_pid,
        "consumed_pids": sorted(set(consumed_pids or ([consumed_pid] if consumed_pid is not None else []))),
        "observation_as_of_status": "available" if observation_available else "unassessed_source_as_of",
        "decision_authority": "report_only_no_order_or_policy_mutation",
        "funnel": dict(sorted(counts.items())),
        "by_market_trigger": dict(sorted(market_trigger.items())),
        "by_market_trigger_kind": dict(sorted(market_trigger_kind.items())),
        "latency_ms": {
            field: _latency_distribution(rows, field)
            for field, rows in sorted(timing_rows.items())
        },
        "findings": findings,
        "source_gaps": gaps,
        "policy_binding_gaps": policy_gaps,
        "runtime_consumption_gaps": runtime_gaps,
        "strict_completed_position_count": len(strict_ids),
    }
