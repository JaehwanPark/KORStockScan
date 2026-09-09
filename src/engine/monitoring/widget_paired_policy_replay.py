"""Existing widget-axis comparisons on exact recorded BBO, never broker proof.

The common 20-minute research horizon is shared with adaptive-exit research.
Its final bid liquidation is evaluation-only, not a new live forced exit. A valid
prefix can resolve both arms early; missing depth or unresolved inventory never
becomes zero PnL, and a conflicting quote cannot support either arm.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import fmean
from zoneinfo import ZoneInfo

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.trading.order.tick_utils import move_price_up_by_bps
from src.utils.market_day import is_krx_trading_day

SCHEMA = "widget_paired_policy_economics_v1"
KST = ZoneInfo("Asia/Seoul")
BASELINE = date(2026, 6, 5)
HORIZON_SEC = 1200
SELECTION_START_DATE = date(2026, 9, 9)
ACTIONABLE = {"ENTRY_READY", "ENTRY_CAUTION"}
CONTRACT = {
    "metric_role": "paired_existing_axis_counterfactual_ev",
    "decision_authority": "existing_widget_policy_candidate_only",
    "window_policy": "same_source_same_policy_rolling_20_trading_dates_chronological_holdout",
    "sample_floor": "two_completed_calibration_pairs_and_one_independent_holdout_pair",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "exact_dated_BBO_and_quantity_contiguous_prefix_paired_resolution",
    "forbidden_uses": [
        "actual_broker_profit",
        "broker_enablement",
        "live_horizon_exit",
        "new_tuning_axis",
    ],
    "denominator": "common_initial_ask_times_fixed_leg_quantity_per_opportunity",
    "horizon": "1200s_common_evaluation_only_not_actual_terminal_or_live_exit",
    "exposure": "nonoverlapping_common_horizon_with_frozen_cap_and_cooldown",
    "profit_frequency_guard": "positive_net_close_within_180s_without_profit_upper_cap",
    "path_maturity": "paired_early_resolution_or_common_horizon_no_missing_outcome_imputation",
    "supported_recipe": "no_scale_in_without_exact_runtime_trigger_inputs",
}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _stamp(value):
    try:
        value = datetime.fromisoformat(str(value))
        return value.astimezone(KST) if value.tzinfo is not None else None
    except ValueError:
        return None


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def capture_input(advisory, *, symbol, venue, bbo):
    """Copy already-normalized internal fields; no API/parser or guard changes."""
    return {
        "schema": "widget_paired_replay_input_v1",
        "symbol": symbol,
        "venue": venue,
        "observed_at": advisory.get("observed_at"),
        "session": advisory.get("session"),
        "raw_state": advisory.get("raw_state") or advisory.get("state"),
        "source_quality_status": (advisory.get("source_quality") or {}).get("status"),
        "signal_contract": advisory.get("strategy_profile") or "widget_raw_signal_v1",
        "non_confirmation_entry_blocked": None,
        "entry_price_low": advisory.get("entry_price_low"),
        "entry_price_high": advisory.get("entry_price_high"),
        "bbo": {
            key: (bbo or {}).get(key)
            for key in (
                "best_bid",
                "best_ask",
                "best_bid_qty",
                "best_ask_qty",
                "received_at",
                "source",
            )
        },
    }


def load_inputs(
    paths: list[Path], *, symbol: str, target_date: date
) -> tuple[list[dict], dict]:
    inputs, hashes = {}, {}
    conflicts = set()
    gaps = 0
    target_records = {}
    for path in sorted(paths):
        try:
            day = datetime.strptime(path.stem.rsplit("_", 1)[-1], "%Y%m%d").date()
        except ValueError:
            continue
        if not BASELINE <= day <= target_date:
            continue
        try:
            raw = path.read_bytes()
            lines = raw.decode().splitlines()
        except (OSError, UnicodeError):
            gaps += 1
            continue
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        for line in lines:
            try:
                payload = json.loads(line)
                advisory = payload.get("advisory", {})
                trace = advisory.get("confirmation_input_trace", {}).get("rows", [])
                candidates = [
                    item.get("execution_replay_input")
                    for item in trace
                    if isinstance(item, dict)
                ]
                if payload.get("execution_replay_input"):
                    candidates.append(payload["execution_replay_input"])
                # The recorder's canonical current input is nested in advisory.
                # Keep it even when the promotion trace was reset or omitted.
                if advisory.get("execution_replay_input"):
                    candidates.append(advisory["execution_replay_input"])
                observed = _stamp(
                    payload.get("observed_at_kst") or advisory.get("observed_at")
                )
                session = advisory.get("session")
                if (
                    observed
                    and observed.date() == day == target_date
                    and isinstance(session, str)
                ):
                    target_records.setdefault(session, set()).add(observed.isoformat())
            except (ValueError, AttributeError, TypeError):
                gaps += 1
                continue
            for item in candidates:
                if not isinstance(item, dict) or item.get("symbol") != symbol:
                    continue
                stamp = _stamp(item.get("observed_at"))
                if (
                    not stamp
                    or stamp.date() != day
                    or not isinstance(item.get("session"), str)
                ):
                    gaps += 1
                    continue
                key = (stamp.isoformat(), item.get("session"))
                if key in inputs and inputs[key] != item:
                    conflicts.add(key)
                inputs[key] = item
    rows = [
        dict(item, source_conflict=key in conflicts)
        for key, item in sorted(inputs.items())
    ]
    return rows, {
        "source_hashes": hashes,
        "invalid_source_rows": gaps,
        "conflicting_observations": len(conflicts),
        "exact_input_count": len(rows),
        "target_date": target_date.isoformat(),
        "target_date_sessions": {
            session: {
                "observation_count": len(observations),
                "replay_input_count": sum(
                    r.get("session") == session
                    and _stamp(r["observed_at"]).date() == target_date
                    for r in rows
                ),
            }
            for session, observations in sorted(target_records.items())
        },
    }


def _quote(row):
    stamp = _stamp(row.get("observed_at"))
    bbo = row.get("bbo")
    received = _stamp(bbo.get("received_at")) if isinstance(bbo, dict) else None
    if (
        row.get("schema") != "widget_paired_replay_input_v1"
        or row.get("source_conflict")
        or row.get("source_quality_status") != "PASS"
        or not isinstance(row.get("raw_state"), str)
        or row["raw_state"]
        not in ACTIONABLE | {"DATA_WAIT", "WATCH", "NO_CHASE", "AVOID"}
        or type(row.get("non_confirmation_entry_blocked")) is not bool
        or not stamp
        or not received
        or not 0 <= (stamp - received).total_seconds() <= 20
        or not all(
            _positive(bbo.get(k))
            for k in ("best_bid", "best_ask", "best_bid_qty", "best_ask_qty")
        )
        or bbo["best_bid"] > bbo["best_ask"]
    ):
        return None
    return stamp, received, bbo


def _arm(path, *, confirmations, parameters, participation):
    qty = parameters["leg_quantity_each"]
    target = parameters["target_bps"]
    first = _stamp(path[0]["observed_at"])
    end = first + timedelta(seconds=HORIZON_SEC)
    streak, last_state, decision_at = 0, None, None
    entry_at = None
    positions = []
    capital_seconds = 0.0
    last_at = first
    used_quote = None
    target_streak = 0
    outcome = {
        "status": "source_gap",
        "net_pnl_krw": None,
        "net_return_pct": None,
        "entry_notional_krw": None,
        "capital_seconds": None,
        "quick_small_profit": False,
        "profitable_close_within_180s": False,
    }
    common_notional = path[0]["bbo"]["best_ask"] * qty
    cutoff = datetime.strptime(parameters["new_entry_cutoff_time"], "%H:%M:%S").time()
    for row in path:
        at, received, bbo = _quote(row)
        capital_seconds += (
            sum(price * qty for price in positions) * (at - last_at).total_seconds()
        )
        last_at = at
        raw = "WATCH" if row["non_confirmation_entry_blocked"] else row.get("raw_state")
        streak = streak + 1 if raw == last_state else 1
        last_state = raw
        if entry_at is None and (at.time() >= cutoff or raw not in ACTIONABLE):
            return dict(
                outcome,
                status="no_entry",
                net_pnl_krw=0.0,
                net_return_pct=0.0,
                entry_notional_krw=0.0,
                capital_seconds=0.0,
            )
        if entry_at is None and raw in ACTIONABLE and streak >= confirmations:
            if decision_at is None:
                decision_at = at
        if decision_at is None:
            continue
        if received == used_quote:
            continue
        used_quote = received
        if entry_at is None:
            if at <= decision_at or received <= decision_at:
                continue
            if math.floor(bbo["best_ask_qty"] * participation) < qty:
                return dict(outcome, status="partial_or_insufficient_entry_depth")
            positions.append(float(bbo["best_ask"]))
            entry_at = at
            continue
        average = fmean(positions)
        target_price = move_price_up_by_bps(int(math.ceil(average)), target)
        target_streak = target_streak + 1 if bbo["best_bid"] >= target_price else 0
        horizon_close = at >= end
        force_exit = parameters.get("force_exit_time")
        forced = bool(
            force_exit and at.time() >= datetime.strptime(force_exit, "%H:%M:%S").time()
        )
        if target_streak >= 2 or horizon_close or forced:
            total = qty * len(positions)
            if math.floor(bbo["best_bid_qty"] * participation) < total:
                if horizon_close or forced:
                    return dict(outcome, status="partial_or_insufficient_exit_depth")
                continue
            # A resting target gets its limit, never the better observed bid.
            exit_price = (
                min(bbo["best_bid"], target_price)
                if target_streak >= 2
                else bbo["best_bid"]
            )
            notional = sum(positions) * qty
            cost = comparison_cost_contract(first.date())
            pnl = exit_price * total - notional * (
                1 + cost["round_trip_cost_pct"] / 100
            )
            net = pnl / notional * 100
            return dict(
                outcome,
                status="completed_cf",
                net_pnl_krw=round(pnl, 6),
                net_return_pct=round(net, 8),
                opportunity_return_pct=round(pnl / common_notional * 100, 8),
                entry_notional_krw=notional,
                capital_seconds=capital_seconds,
                closed_at=at.isoformat(),
                entry_at=entry_at.isoformat(),
                quick_small_profit=0 < net <= 0.5
                and (at - entry_at).total_seconds() <= 180,
                profitable_close_within_180s=net > 0
                and (at - entry_at).total_seconds() <= 180,
                close_reason="target"
                if target_streak >= 2
                else "existing_force_exit"
                if forced
                else "common_horizon_evaluation_only",
                cost_contract_hash=cost["contract_sha256"],
            )
    if decision_at is None and _stamp(path[-1]["observed_at"]) >= end:
        return dict(
            outcome,
            status="no_entry",
            net_pnl_krw=0.0,
            net_return_pct=0.0,
            entry_notional_krw=0.0,
            capital_seconds=0.0,
        )
    return dict(outcome, status="right_censored")


def build_study(
    rows,
    *,
    symbol,
    session,
    parameters,
    baseline_confirmations,
    axis,
    values,
    target_date,
    source_audit,
):
    """One existing axis only. Freeze quantities/adds/exit and all other values."""
    result = {
        "schema": SCHEMA,
        "symbol": symbol,
        "session": session,
        "axis": axis,
        "target_date": target_date.isoformat(),
        "baseline_parameters": parameters,
        "baseline_confirmations": baseline_confirmations,
        "source_audit": source_audit,
        "metric_contract": CONTRACT,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_broker_execution_quality": False,
        "horizon_sec": HORIZON_SEC,
        "horizon_close_is_evaluation_only": True,
        "candidates": [],
        "status": "source_gap",
    }
    if (
        not isinstance(parameters, dict)
        or type(parameters.get("leg_quantity_each")) is not int
        or parameters.get("leg_quantity_each") != 10
        or axis not in {"confirmations", "target_bps"}
        or baseline_confirmations not in {2, 3}
        or not _positive(parameters.get("target_bps"))
        or not isinstance(
            parameters.get("add_trigger_bps_from_initial_fill"), (list, tuple)
        )
        or any(
            type(value) is not int or value >= 0
            for value in parameters["add_trigger_bps_from_initial_fill"]
        )
        or type(parameters.get("max_completed_entries_per_day")) is not int
        or not 1 <= parameters["max_completed_entries_per_day"] <= 5
        or type(parameters.get("reentry_cooldown_minutes")) is not int
        or not 1 <= parameters["reentry_cooldown_minutes"] <= 120
        or parameters.get("source_final_exit_action") != "observe_only_no_forced_sell"
    ):
        result["status"] = "baseline_contract_missing"
        result["content_hash"] = digest(result)
        return result
    try:
        cutoff = datetime.strptime(
            parameters["new_entry_cutoff_time"], "%H:%M:%S"
        ).time()
        if parameters.get("force_exit_time"):
            datetime.strptime(parameters["force_exit_time"], "%H:%M:%S")
    except (KeyError, ValueError, TypeError):
        result["status"] = "baseline_contract_missing"
        result["content_hash"] = digest(result)
        return result
    # Event-based source exits need their own replay. Never silently omit them.
    expected_venue = (
        "KRX"
        if session == "KRX_REGULAR"
        else "NXT"
        if session in {"NXT_PREMARKET", "NXT_AFTERMARKET"}
        else None
    )
    if expected_venue is None:
        result["status"] = "unsupported_session"
        result["content_hash"] = digest(result)
        return result
    # Runtime scale-in uses last trade price, tick-clamped triggers and its own
    # gates, not this BBO-only path. Never approve a new value from that proxy.
    # The incumbent still carries through the existing verified policy loader.
    if parameters["add_trigger_bps_from_initial_fill"]:
        result["status"] = "scale_in_runtime_trigger_source_missing"
        result["content_hash"] = digest(result)
        return result
    scoped = [
        r
        for r in rows
        if r.get("symbol") == symbol
        and r.get("session") == session
        and _stamp(r.get("observed_at"))
        and BASELINE <= _stamp(r["observed_at"]).date() <= target_date
        and is_krx_trading_day(_stamp(r["observed_at"]).date())
    ]
    scoped.sort(key=lambda r: _stamp(r["observed_at"]))
    paths, exclusions, source_gaps = [], [], []
    last_raw, last_at, reserved_until = None, None, None
    daily_opportunities = {}
    for index, row in enumerate(scoped):
        at = _stamp(row["observed_at"])
        raw = (
            "WATCH"
            if row.get("non_confirmation_entry_blocked") is True
            else row.get("raw_state")
        )
        start = (
            isinstance(raw, str)
            and raw in ACTIONABLE
            and (
                last_raw not in ACTIONABLE
                or last_at is None
                or (at - last_at).total_seconds() > 25
            )
        )
        last_raw, last_at = raw if isinstance(raw, str) else None, at
        if (
            not start
            or reserved_until
            and at < reserved_until
            or at.time() >= cutoff
            or daily_opportunities.get(at.date(), 0)
            >= parameters["max_completed_entries_per_day"]
        ):
            continue
        end = at + timedelta(seconds=HORIZON_SEC)
        reserved_until = end + timedelta(minutes=parameters["reentry_cooldown_minutes"])
        daily_opportunities[at.date()] = daily_opportunities.get(at.date(), 0) + 1
        path = []
        for item in scoped[index:]:
            clock = _stamp(item["observed_at"])
            if clock.date() != at.date():
                break
            path.append(item)
            if clock >= end:
                break
        quote_data = {}
        reason = None
        previous = None
        previous_received = None
        valid_prefix = []
        for item in path:
            quote = _quote(item)
            if not quote:
                reason = "quote_source_gap"
                break
            clock, received, bbo = quote
            if item.get("venue") != expected_venue or item.get(
                "signal_contract"
            ) != row.get("signal_contract"):
                reason = "venue_or_signal_contract_conflict"
                break
            fingerprint = (
                bbo["best_bid"],
                bbo["best_ask"],
                bbo["best_bid_qty"],
                bbo["best_ask_qty"],
            )
            if received in quote_data and quote_data[received] != fingerprint:
                reason = "same_quote_identity_conflict"
                break
            if previous_received and received < previous_received:
                reason = "quote_time_regression"
                break
            if previous and not 0 < (clock - previous).total_seconds() <= 25:
                reason = "observation_gap_or_duplicate"
                break
            quote_data[received], previous = fingerprint, clock
            previous_received = received
            valid_prefix.append(item)
        if not path or _stamp(path[-1]["observed_at"]) < end:
            reason = reason or "common_horizon_not_covered"
        if reason:
            gap = {"raw_first_at": at.isoformat(), "reason": reason}
            source_gaps.append(gap)
            # A conflicting reused quote can invalidate an earlier price, not
            # merely censor the future. It cannot support prefix acceptance.
            if reason == "same_quote_identity_conflict":
                valid_prefix = []
            if not valid_prefix:
                exclusions.append(gap)
        if valid_prefix:
            paths.append((valid_prefix, reason))
    result["path_count"], result["path_exclusions"] = len(paths), exclusions
    result["path_source_gaps"] = source_gaps
    baseline_value = (
        baseline_confirmations if axis == "confirmations" else parameters["target_bps"]
    )
    for value in sorted(set(values) | {baseline_value}):
        if (
            type(value) is not int
            or axis == "confirmations"
            and value not in {2, 3}
            or axis == "target_bps"
            and not 20 <= value <= 300
        ):
            continue
        changed = {
            **parameters,
            **({"target_bps": value} if axis == "target_bps" else {}),
        }
        pairs = []
        for path, gap_reason in paths:
            pair = {
                "source_date": _stamp(path[0]["observed_at"]).date().isoformat(),
                "raw_first_at": path[0]["observed_at"],
                "path_hash": digest(path),
                "path_source_gap": gap_reason,
                "models": {},
            }
            for name, participation in (("base", 0.5), ("stress", 0.25)):
                pair["models"][name] = {
                    "baseline": _arm(
                        path,
                        confirmations=baseline_confirmations,
                        parameters=parameters,
                        participation=participation,
                    ),
                    "candidate": _arm(
                        path,
                        confirmations=value
                        if axis == "confirmations"
                        else baseline_confirmations,
                        parameters=changed,
                        participation=participation,
                    ),
                }
            pairs.append(pair)
        result["candidates"].append(
            {"value": value, "parameters": changed, "pairs": pairs}
        )
    result["status"] = "observed" if paths else "source_gap"
    result["content_hash"] = digest(result)
    return result


def select_candidate(study, *, previous_value):
    """Recompute acceptance from matched rows, not a claimed PASS boolean."""
    carry = {
        "selected_value": previous_value,
        "decision": "carry_forward_paired_evidence_missing",
        "candidate_ready": False,
        "evidence_state": "paired_contract_invalid",
    }
    if (
        not isinstance(study, dict)
        or study.get("schema") != SCHEMA
        or study.get("content_hash")
        != digest({k: v for k, v in study.items() if k != "content_hash"})
        or study.get("metric_contract") != CONTRACT
    ):
        return carry
    source = study.get("source_audit")
    source = source if isinstance(source, dict) else {}
    sessions = (
        source.get("target_date_sessions")
        if source.get("target_date") == study.get("target_date")
        else {}
    )
    sessions = sessions if isinstance(sessions, dict) else {}
    current = sessions.get(study.get("session"))
    current = current if isinstance(current, dict) else {}
    carry["source_diagnostic"] = (
        "replay_input_observed_not_pid_or_economic_acceptance"
        if _positive(current.get("replay_input_count"))
        else "observation_present_replay_input_missing_check_collector_generation"
        if _positive(current.get("observation_count"))
        else "target_session_source_not_observed_check_schedule_and_owner"
    )
    if study.get("status") != "observed":
        carry["evidence_state"] = study.get("status") or "paired_contract_invalid"
        carry["path_exclusion_reasons"] = sorted(
            {r["reason"] for r in study.get("path_exclusions", [])}
        )
        return carry
    if not _valid_pairs(study, previous_value):
        carry["decision"] = "carry_forward_paired_contract_invalid"
        return carry
    accepted, diagnostics = [], []
    recent_pair_count = 0
    sample_floor_met = False
    incomplete_outcomes = False
    window_floor = date.fromisoformat(study["target_date"])
    trading_dates = 1 if is_krx_trading_day(window_floor) else 0
    while trading_dates < 20:
        window_floor -= timedelta(days=1)
        trading_dates += int(is_krx_trading_day(window_floor))
    for candidate in study["candidates"]:
        pairs = candidate["pairs"]
        dates = sorted(
            {
                row["source_date"]
                for row in pairs
                if row["source_date"] >= window_floor.isoformat()
            }
        )
        holdout_count = max(1, len(dates) // 5)
        windows = {
            "calibration": dates[:-holdout_count],
            "holdout": dates[-holdout_count:],
        }
        metrics = {}
        ready = len(dates) >= 2
        recent_pair_count = max(
            recent_pair_count, sum(p["source_date"] in dates for p in pairs)
        )
        candidate_sample_ready = len(dates) >= 2
        for model in ("base", "stress"):
            metrics[model] = {}
            for name, days in windows.items():
                all_rows = [p for p in pairs if p["source_date"] in days]
                rows = [
                    p["models"][model]
                    for p in all_rows
                    if all(
                        p["models"][model][a]["status"] in {"completed_cf", "no_entry"}
                        for a in ("baseline", "candidate")
                    )
                ]
                # An illiquid/censored pair never vanishes from approval's denominator.
                window_ready = len(rows) == len(all_rows) and len(rows) >= (
                    2 if name == "calibration" else 1
                )
                candidate_sample_ready &= window_ready
                incomplete_outcomes |= len(rows) < len(all_rows)
                sides = {}
                for arm in ("baseline", "candidate"):
                    outcomes = [r[arm] for r in rows]
                    sides[arm] = {
                        "source_quality_adjusted_ev_pct": fmean(
                            r.get("opportunity_return_pct", 0.0)
                            if r["status"] == "no_entry"
                            else r["opportunity_return_pct"]
                            for r in outcomes
                        )
                        if outcomes
                        else None,
                        "net_profit_krw_per_source_day": sum(
                            r["net_pnl_krw"] for r in outcomes
                        )
                        / len(days)
                        if days and outcomes
                        else None,
                        "worst_net_return_pct": min(
                            (r["net_return_pct"] for r in outcomes), default=None
                        ),
                        "capital_seconds": sum(r["capital_seconds"] for r in outcomes),
                        "quick_small_profit_count": sum(
                            r["quick_small_profit"] for r in outcomes
                        ),
                        "profitable_close_within_180s_count": sum(
                            _profitable_close_within_180s(r) for r in outcomes
                        ),
                    }
                base, new = sides["baseline"], sides["candidate"]
                window_ready &= bool(
                    new["source_quality_adjusted_ev_pct"] is not None
                    and new["source_quality_adjusted_ev_pct"] > 0
                    and new["source_quality_adjusted_ev_pct"]
                    > base["source_quality_adjusted_ev_pct"]
                    and new["net_profit_krw_per_source_day"]
                    >= base["net_profit_krw_per_source_day"]
                    and new["worst_net_return_pct"] >= base["worst_net_return_pct"]
                    and new["capital_seconds"] <= base["capital_seconds"]
                    and new["profitable_close_within_180s_count"]
                    >= base["profitable_close_within_180s_count"]
                )
                metrics[model][name] = {
                    "sample_count": len(rows),
                    "excluded_pair_count": len(all_rows) - len(rows),
                    "ready": window_ready,
                    **sides,
                }
                ready &= window_ready
        diagnostics.append(
            {"value": candidate["value"], "ready": ready, "windows": metrics}
        )
        sample_floor_met |= candidate_sample_ready
        if len(dates) >= 2 and all(
            metrics[model]["calibration"]["ready"] for model in ("base", "stress")
        ):
            accepted.append(
                (
                    metrics["base"]["calibration"]["candidate"][
                        "source_quality_adjusted_ev_pct"
                    ],
                    candidate["value"],
                    ready,
                )
            )
    if accepted:
        _, value, ready = max(accepted, key=lambda item: (item[0], -item[1]))
        carry["calibration_selected_value"] = value
        if ready:
            carry.update(
                selected_value=value,
                decision="paired_cost_ev_candidate_ready",
                candidate_ready=True,
                evidence_state="paired_research_candidate_ready",
            )
        else:
            carry["decision"] = "carry_forward_frozen_calibration_winner_holdout_failed"
            carry["evidence_state"] = "frozen_calibration_winner_holdout_not_passed"
    else:
        carry["decision"] = "carry_forward_paired_sample_or_economic_guard"
        carry["evidence_state"] = (
            "rolling_evidence_expired"
            if not recent_pair_count
            else "economic_guard_not_met"
            if sample_floor_met
            else "paired_outcome_incomplete"
            if incomplete_outcomes
            else "paired_sample_floor_not_met"
        )
    carry.update(
        diagnostics=diagnostics,
        source_study_hash=study["content_hash"],
        metric_contract=CONTRACT,
    )
    return carry


def _profitable_close_within_180s(outcome):
    """Recompute frequency from resolved economics; 0.5% is diagnostic only."""
    entry, closed = _stamp(outcome.get("entry_at")), _stamp(outcome.get("closed_at"))
    return bool(
        outcome.get("status") == "completed_cf"
        and _positive(outcome.get("net_return_pct"))
        and entry
        and closed
        and 0 <= (closed - entry).total_seconds() <= 180
    )


def policy_parameters(policy):
    """Freeze an already-validated incumbent; this helper never enables one."""
    if (
        not isinstance(policy, dict)
        or policy.get("new_entry_runtime_eligible") is not True
    ):
        return None
    keys = (
        "leg_quantity_each",
        "add_trigger_bps_from_initial_fill",
        "max_completed_entries_per_day",
        "reentry_cooldown_minutes",
        "new_entry_cutoff_time",
        "force_exit_time",
        "source_final_exit_action",
    )
    parameters = {
        **{key: policy.get(key) for key in keys},
        "target_bps": policy.get("take_profit_bps_from_equal_share_average"),
    }
    if isinstance(parameters["add_trigger_bps_from_initial_fill"], (tuple, list)):
        parameters["add_trigger_bps_from_initial_fill"] = list(
            parameters["add_trigger_bps_from_initial_fill"]
        )
    return parameters


def bind_incumbent(study, policy):
    """Freeze the verified recipe's file identity separately from market paths."""
    receipt = {"status": "missing"}
    try:
        path = Path(policy["policy_path"])
        raw = path.read_bytes()
        receipt = {
            "status": "bound",
            "path": str(path),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "policy_id": policy["policy_id"],
        }
    except (OSError, KeyError, TypeError):
        pass
    study["incumbent_receipt"] = receipt
    if "content_hash" in study:
        study["content_hash"] = digest(
            {k: v for k, v in study.items() if k != "content_hash"}
        )


def incumbent_valid(study):
    try:
        receipt = study["incumbent_receipt"]
        raw = Path(receipt["path"]).read_bytes()
        payload = json.loads(raw)
        source = date.fromisoformat(payload["source_target_date"])
        effective = date.fromisoformat(payload["effective_date"])
        row = payload["symbols"][study["symbol"]]["sessions"][study["session"]]
        return bool(
            receipt["status"] == "bound"
            and hashlib.sha256(raw).hexdigest() == receipt["sha256"]
            and payload["policy_version"] == receipt["policy_id"]
            and payload["schema"] == "widget_auto_trade_policy_v1"
            and payload["status"] == "verified"
            and payload["authority"] == "postclose_widget_auto_trade_calibration_v1"
            and payload["runtime_effect"] is True
            and row["enabled"] is True
            and BASELINE
            <= source
            < effective
            <= date.fromisoformat(study["target_date"])
            and policy_parameters(dict(row, new_entry_runtime_eligible=True))
            == study["baseline_parameters"]
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def _valid_pairs(study, previous_value):
    try:
        if (
            study.get("runtime_effect") is not False
            or study.get("allowed_runtime_apply") is not False
            or study.get("actual_broker_execution_quality") is not False
            or study.get("horizon_sec") != HORIZON_SEC
            or study.get("horizon_close_is_evaluation_only") is not True
            or study["baseline_parameters"].get("add_trigger_bps_from_initial_fill")
        ):
            return False
        axis = study["axis"]
        previous = (
            study["baseline_confirmations"]
            if axis == "confirmations"
            else study["baseline_parameters"]["target_bps"]
        )
        if previous != previous_value or axis not in {"confirmations", "target_bps"}:
            return False
        target_date = date.fromisoformat(study["target_date"])
        fingerprints, values, baselines = None, set(), None
        for candidate in study["candidates"]:
            value = candidate["value"]
            if (
                type(value) is not int
                or value in values
                or (axis == "confirmations" and value not in {2, 3})
                or (axis == "target_bps" and not 20 <= value <= 300)
            ):
                return False
            values.add(value)
            expected = {
                **study["baseline_parameters"],
                **({"target_bps": value} if axis == "target_bps" else {}),
            }
            if candidate["parameters"] != expected:
                return False
            identities = []
            candidate_baselines = []
            for pair in candidate["pairs"]:
                stamp = _stamp(pair["raw_first_at"])
                source_date = date.fromisoformat(pair["source_date"])
                if (
                    not stamp
                    or stamp.date() != source_date
                    or not BASELINE <= source_date <= target_date
                    or not is_krx_trading_day(source_date)
                ):
                    return False
                identities.append((pair["raw_first_at"], pair["path_hash"]))
                candidate_baselines.append(
                    [pair["models"][model]["baseline"] for model in ("base", "stress")]
                )
                for model in ("base", "stress"):
                    for arm in ("baseline", "candidate"):
                        outcome = pair["models"][model][arm]
                        if (
                            value == previous
                            and pair["models"][model]["baseline"]
                            != pair["models"][model]["candidate"]
                        ):
                            return False
                        if outcome["status"] == "completed_cf":
                            entry = _stamp(outcome.get("entry_at"))
                            closed = _stamp(outcome.get("closed_at"))
                            if (
                                not entry
                                or not closed
                                or not stamp <= entry <= closed
                                or closed.date() != source_date
                                or (closed - stamp).total_seconds() > HORIZON_SEC + 25
                                or outcome.get("cost_contract_hash")
                                != comparison_cost_contract(source_date)[
                                    "contract_sha256"
                                ]
                                or any(
                                    type(outcome.get(k)) not in (int, float)
                                    or not math.isfinite(outcome[k])
                                    for k in (
                                        "net_return_pct",
                                        "opportunity_return_pct",
                                        "net_pnl_krw",
                                        "entry_notional_krw",
                                        "capital_seconds",
                                    )
                                )
                                or outcome["entry_notional_krw"] <= 0
                                or outcome["capital_seconds"] < 0
                            ):
                                return False
                        elif outcome["status"] == "no_entry" and any(
                            outcome.get(k) != 0
                            for k in (
                                "net_return_pct",
                                "net_pnl_krw",
                                "entry_notional_krw",
                                "capital_seconds",
                            )
                        ):
                            return False
            if (
                len(set(identities)) != len(identities)
                or fingerprints is not None
                and fingerprints != identities
            ):
                return False
            fingerprints = identities
            if baselines is not None and baselines != candidate_baselines:
                return False
            baselines = candidate_baselines
        return bool(values and previous in values)
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
        return False


def selection_valid(
    study, selection, *, symbol, session, target_date, axis, selected_value
):
    """Bind scope/axis/date and recompute paired acceptance in the consumer."""
    try:
        baseline_value = (
            study["baseline_confirmations"]
            if axis == "confirmations"
            else study["baseline_parameters"]["target_bps"]
        )
        return bool(
            study.get("symbol") == symbol
            and study.get("session") == session
            and study.get("target_date") == target_date.isoformat()
            and study.get("axis") == axis
            and selection == select_candidate(study, previous_value=baseline_value)
            and selection.get("selected_value") == selected_value
        )
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        return False
