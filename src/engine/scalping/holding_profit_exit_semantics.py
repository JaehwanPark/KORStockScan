"""Read-only semantic checks for the real main trailing-profit exit chain."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import math
from typing import Any, Callable

from src.engine.ai.holding_exit_vote import (
    PATH_POLICY_BY_MARKET, input_snapshot_id, path_signal_snapshot,
)
from src.engine.scalping.trailing_threshold_policy import market_type_at


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
) -> dict[str, Any]:
    """Audit evidence order; absent natural positions remain valid empty."""
    selected = policies or PATH_POLICY_BY_MARKET
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
    market_trigger = Counter()
    market_trigger_kind = Counter()
    timing_rows: dict[str, list[Any]] = defaultdict(list)
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
        if len(snapshot_ids) != len(set(snapshot_ids)):
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
            if _float(fields.get("remaining_sell_qty")) not in {0.0, None}:
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
                             if row.emitted_at <= event.emitted_at
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
                        or _float(transition.get("trailing_start_pct")) != 0.4
                        or transition.get("tuning_exit_allowed_by_clock") not in {"True", "true", True}):
                    add(findings, record_id, "tp_crossing_arm_or_clock_invalid")
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
                        or vote.get("market") != market):
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
                path_id="EXIT_TRAILING_TP", model="gpt-5.4-nano",
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
            if any(row.emitted_at < event.emitted_at for row in matching_exit):
                add(findings, record_id, "tp_exit_before_vote_snapshot")
            if (matching_exit and any(row.emitted_at < matching_exit[0].emitted_at
                                      for row in matching_sent)):
                add(findings, record_id, "tp_submit_before_exit_signal")
            if fields.get("decision") == "VETO" and matching_exit:
                elapsed = matching_exit[0].emitted_at.timestamp() - signal_at
                if elapsed < 0:
                    add(findings, record_id, "tp_veto_exit_before_first_crossing")
                elif elapsed < policy["max_defer_sec"] and not any(
                    _fields(row).get("signal_id") == signal_id
                    for row in rows if getattr(row, "stage", "") == "holding_path_exit_veto_deferred"
                ):
                    add(gaps, record_id, "tp_veto_defer_or_safety_reason_missing")
        if completed and not sent:
            add(gaps, record_id, "tp_completed_without_submit_receipt")
        if completed and record_id not in strict_ids:
            add(gaps, record_id, "tp_completed_cost_or_quantity_evidence_missing")
        outcome = outcomes.get(record_id)
        if completed and outcome is None:
            add(gaps, record_id, "tp_completed_outcome_projection_missing")
        if completed and outcome is not None:
            if outcome.get("sell_quantity_conserved") is not True:
                add(findings, record_id, "tp_sell_quantity_not_conserved")
            if (_float(outcome.get("profit_rate")) is None
                    or _float(outcome.get("realized_pnl_krw")) is None):
                counts["tp_economics_null"] += 1
            if not outcome.get("exact_sell_fill_time"):
                counts["tp_forward_censored_no_sell_time"] += 1
            elif outcome.get("post_sell_status") == "pass":
                counts["tp_forward_observed"] += 1
            else:
                counts["tp_forward_censored_source_or_horizon_gap"] += 1
        buy_qty = max((_float(_fields(row).get("buy_qty")) or 0.0
                       for row in exits), default=0.0)
        if buy_qty and any((_float(_fields(row).get("qty")) or 0.0) > buy_qty
                           for row in sent):
            add(findings, record_id, "tp_submitted_quantity_exceeds_buy")
        if exits and not sent:
            counts["tp_pending_submit"] += 1
        if sent and not completed:
            counts["tp_pending_terminal"] += 1

    status = ("semantic_contract_invalid" if findings else
              "policy_binding_gap" if policy_gaps else
              "runtime_not_consumed" if runtime_gaps else
              "source_gap" if gaps else
              "economics_null" if counts["tp_economics_null"] else
              "pending_terminal" if counts["tp_pending_terminal"] else
              "valid_empty" if not counts["tp_signal_snapshots"] else "pass")
    return {
        "schema": "holding_profit_exit_semantics_v1",
        "target_date": target_date,
        "status": status,
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
