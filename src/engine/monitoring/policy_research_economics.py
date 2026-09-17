"""Source-only machine/widget economics, separate from broker accounting.

Owned by monitoring: these adapters consume frozen observations, never issue
orders, create owner signals, or assign live capital/quantity authority.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.utils.market_day import is_krx_trading_day
from src.trading.market.micro_confirmation import modeled_dynamic_target_price

AUTHORITY = {
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}
DECISION_ROLES = {"actual_widget_entry_signal", "episode_signal_decision_leg"}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def numeric(value):
    return value if type(value) in (int, float) and math.isfinite(value) else None


def aware(value):
    try:
        clock = datetime.fromisoformat(str(value))
        return clock if clock.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def trading_window(target_date, days):
    result, clock = [], target_date
    while len(result) < days:
        if is_krx_trading_day(clock):
            result.append(clock)
        clock -= timedelta(days=1)
    return sorted(result)


def modeled_summary(episodes, qualified_dates, quantity=10):
    """Valid zero-signal days stay in the denominator; unknown PnL stays null."""
    dates = set(qualified_dates)
    valid = type(quantity) is int and quantity > 0
    valid &= all(
        numeric(row.get("entry_price")) is not None
        and row["entry_price"] > 0
        and numeric(row.get("net_return_pct")) is not None
        and aware(row.get("entry_at")) is not None
        and aware(row.get("exit_at")) is not None
        and aware(row["entry_at"]).date() in dates
        and aware(row["exit_at"]) >= aware(row["entry_at"])
        for row in episodes
    )
    pnl = (
        sum(
            row["entry_price"] * quantity * row["net_return_pct"] / 100
            for row in episodes
        )
        if valid
        else None
    )
    capital_seconds = (
        sum(
            row["entry_price"]
            * quantity
            * (aware(row["exit_at"]) - aware(row["entry_at"])).total_seconds()
            for row in episodes
        )
        if valid
        else None
    )
    return {
        "qualified_source_day_count": len(dates),
        "modeled_quantity_each": quantity,
        "modeled_net_profit_krw": pnl,
        "modeled_net_pnl_per_qualified_day": (
            pnl / len(dates) if pnl is not None and dates else None
        ),
        "modeled_capital_krw_seconds": capital_seconds,
        "completed_episodes_per_qualified_day": (
            len(episodes) / len(dates) if valid and dates else None
        ),
        "economic_basis": "source_only_registered_quantity_not_broker_profit",
    }


def joint_capital_demand(symbol_episodes, *, capital_limit_krw=None, quantity=10):
    """Measure simultaneous demand; do not invent a shared allocation limit."""
    events, invalid, pnl = [], 0, 0.0
    identities = set()
    for symbol, episodes in sorted(symbol_episodes.items()):
        for row in episodes:
            entry, exit_ = aware(row.get("entry_at")), aware(row.get("exit_at"))
            price, net = numeric(row.get("entry_price")), numeric(
                row.get("net_return_pct")
            )
            identity = (symbol, row.get("entry_at"), row.get("exit_at"))
            if (
                entry is None
                or exit_ is None
                or exit_ <= entry
                or price is None
                or price <= 0
                or net is None
                or identity in identities
                or type(quantity) is not int
                or quantity <= 0
            ):
                invalid += 1
                continue
            identities.add(identity)
            notional = price * quantity
            events.extend([(entry, 1, notional), (exit_, 0, -notional)])
            pnl += notional * net / 100
    occupied = peak = 0.0
    for _clock, _order, delta in sorted(events):
        occupied += delta
        peak = max(peak, occupied)
    limit = numeric(capital_limit_krw)
    valid_limit = limit is not None and limit > 0
    return {
        "schema": "policy_research_joint_capital_demand_v1",
        "status": (
            "source_gap"
            if invalid
            else "observed" if valid_limit else "allocation_contract_missing"
        ),
        "modeled_peak_concurrent_notional_krw": peak if not invalid else None,
        "independent_modeled_net_profit_krw": pnl if not invalid else None,
        "feasible_combined_net_profit_krw": (
            pnl if not invalid and valid_limit and peak <= limit else None
        ),
        "capital_limit_krw": limit if valid_limit else None,
        "capital_feasible": bool(not invalid and valid_limit and peak <= limit),
        "invalid_or_duplicate_episode_count": invalid,
        "allocation_role": "demand_validation_only_no_hindsight_trade_pruning",
        **AUTHORITY,
    }


def source_only_timing_observation(*, source_date, row, replay):
    """Compare an immediate CF control with a causal confirmation decision.

    Both arms use one exact depth-backed evaluation deadline. The diagnostic
    adverse label is never a stop, and a 300s terminal is never a live exit.
    Held/missing/control gaps cannot become zero-profit baseline observations.
    The caller must reconstruct the decision from its original causal features.
    """
    anchor = aware(row.get("anchor_at"))
    try:
        cost = comparison_cost_contract(source_date)
    except ValueError:
        return None
    qty = numeric(row.get("owner_requested_quantity"))
    report = row.get("dynamic_confirmation_first_hit_outcomes")
    if (
        row.get("anchor_role") not in DECISION_ROLES
        or (
            row.get("actual_order_submitted") is not None
            and type(row.get("actual_order_submitted")) is not bool
        )
        or row.get("owner_lifecycle_contract_valid") is not True
        or row.get("classification") == "source_quality_blocked"
        or row.get("source_gap_reasons")
        or not row.get("source_entry_event_id")
        or not row.get("anchor_id")
        or not row.get("lifecycle_id")
        or anchor is None
        or anchor.date() != source_date
        or qty is None
        or qty <= 0
        or not float(qty).is_integer()
        or not isinstance(report, dict)
        or report.get("schema") != "machine_dynamic_confirmation_first_hit_outcomes_v1"
        or report.get("label_horizon_sec") != 300
        or any(report.get(key) is not value for key, value in AUTHORITY.items())
        or report.get("counterfactual_only") is not True
        or report.get("trading_runtime_effect") is not False
        or report.get("trading_decision_effect") is not False
        or numeric(row.get("owner_round_trip_cost_pct")) != cost["round_trip_cost_pct"]
    ):
        return None
    deadline = anchor + timedelta(seconds=300)

    def completed(checkpoint):
        label = (report.get("checkpoint_outcomes") or {}).get(str(checkpoint))
        bbo = (
            row.get("entry_confirmation_bbo_anchor")
            if checkpoint == 0
            else (row.get("entry_confirmation_bbo_horizons") or {}).get(str(checkpoint))
        )
        if not isinstance(label, dict) or not isinstance(bbo, dict):
            return None
        entry, hit = (
            label.get("entry") or {},
            label.get("target_adverse_first_hit") or {},
        )
        terminal = label.get("common_horizon_terminal") or {}
        terminal_at = aware(terminal.get("observed_at"))
        terminal_bid = numeric(terminal.get("executable_bid"))
        terminal_qty = numeric(terminal.get("available_bid_quantity"))
        terminal_age = numeric(terminal.get("quote_age_ms"))
        ask, bid = numeric(entry.get("ask_price")), numeric(
            hit.get("target_executable_bid")
        )
        target, available = numeric(hit.get("target_price")), numeric(
            hit.get("target_available_bid_quantity")
        )
        entry_at, exit_at = aware(entry.get("entry_at")), aware(hit.get("target_at"))
        limit = numeric(row.get("owner_entry_limit_price"))
        epoch = bbo.get("sequence_epoch")
        expected_target = modeled_dynamic_target_price(
            owner=str(row.get("owner") or ""),
            baseline_fill_price=row.get("anchor_price"),
            owner_target_price=row.get("owner_target_price"),
            checkpoint_ask=ask,
            widget_take_profit=(row.get("owner_outcome") or {}).get("exit_reason")
            == "take_profit_fill",
        )
        if (
            terminal.get("schema") != "machine_common_horizon_terminal_v1"
            or terminal.get("evaluation_only") is not True
            or terminal.get("runtime_effect") is not False
            or terminal.get("allowed_runtime_apply") is not False
            or terminal.get("source_quality_status") != "eligible"
            or terminal.get("source_gap_reasons")
            or aware(terminal.get("deadline_at")) != deadline
            or terminal_at is None
            or not anchor <= terminal_at <= deadline
            or terminal_bid is None
            or terminal_bid <= 0
            or terminal_qty is None
            or terminal_qty < qty
            or terminal_age is None
            or not 0 <= terminal_age <= 5000
            or not math.isclose(
                terminal_age,
                (deadline - terminal_at).total_seconds() * 1000,
                abs_tol=1e-6,
            )
            or label.get("checkpoint_sec") != checkpoint
            or type(epoch) is not int
            or epoch <= 0
            or label.get("sequence_epoch") != epoch
            or epoch
            != (row.get("entry_confirmation_bbo_anchor") or {}).get("sequence_epoch")
            or label.get("future_label_only") is not True
            or label.get("future_outcome_input_used_by_confirmation_action")
            is not False
            or bbo.get("observed") is not True
            or bbo.get("depth_backed") is not True
            or entry.get("depth_backed") is not True
            or entry.get("required_quantity") != qty
            or limit is None
            or entry.get("owner_entry_limit_price") != limit
            or ask is None
            or ask <= 0
            or ask > limit
            or ask != numeric(bbo.get("best_ask"))
            or entry_at != anchor + timedelta(seconds=checkpoint)
            or target is None
            or target <= ask
            or target != expected_target
            or numeric(hit.get("baseline_owner_target_price"))
            != numeric(row.get("owner_target_price"))
            or numeric(label.get("round_trip_cost_pct")) != cost["round_trip_cost_pct"]
        ):
            return None
        if exit_at is not None:
            if (
                not entry_at <= exit_at <= anchor + timedelta(seconds=checkpoint + 300)
                or bid is None
                or bid < target
                or available is None
                or available < qty
            ):
                return None
        target_completed = exit_at is not None and exit_at <= deadline
        exit_price = target if target_completed else terminal_bid
        exit_at = exit_at if target_completed else deadline
        net = (exit_price / ask - 1) * 100 - cost["round_trip_cost_pct"]
        notional = ask * qty
        return (
            net,
            notional * net / 100,
            notional * (exit_at - entry_at).total_seconds() / 60,
        )

    baseline = completed(0)
    decisions = replay.get("checkpoint_decisions") or []
    action, delay = replay.get("terminal_action"), replay.get("selected_delay_sec")
    if (
        baseline is None
        or replay.get("source_quality_status") != "eligible"
        or not decisions
    ):
        return None
    if action == "REJECT":
        candidate = (0.0, 0.0, 0.0)
    elif action == "ENTER" and type(delay) is int and delay >= 0:
        candidate = completed(delay)
    else:
        return None
    if candidate is None:
        return None
    return {
        "source_date": source_date,
        "lifecycle_id": row["lifecycle_id"],
        "anchor_id": row["anchor_id"],
        "terminal_action": action,
        "selected_delay_sec": delay,
        "baseline_net_pct": baseline[0],
        "candidate_net_pct": candidate[0],
        "comparison_weight_notional_krw": numeric(
            (report["checkpoint_outcomes"]["0"]["entry"]).get("ask_price")
        )
        * qty,
        "baseline_modeled_net_profit_krw": baseline[1],
        "candidate_modeled_net_profit_krw": candidate[1],
        "baseline_capital_krw_minutes": baseline[2],
        "candidate_capital_krw_minutes": candidate[2],
        "realized_quantity": None,
        "modeled_quantity": int(qty),
        "baseline_realized_loss": False,
        "reported_cost_aware_net_pct": None,
        "outcome_basis": "paired_source_only_common_300s_evaluation_not_owner_exit_or_broker_fill",
        "comparison_cost_contract_sha256": cost["contract_sha256"],
        "round_trip_cost_pct": cost["round_trip_cost_pct"],
        "counterfactual_first_hit_state": (
            (report.get("checkpoint_outcomes") or {}).get(
                str(delay if type(delay) is int else 0)
            )
            or {}
        )
        .get("target_adverse_first_hit", {})
        .get("state"),
        "counterfactual_timeout_net_return_pct": None,
    }


def population_dispositions(rows, admitted_ids):
    counts = Counter()
    for day, row in rows:
        key = (day, row.get("anchor_id"))
        if row.get("anchor_role") not in DECISION_ROLES:
            counts["diagnostic_or_other_guard"] += 1
        elif key in admitted_ids:
            counts["economic_pair"] += 1
        elif row.get("classification") == "source_quality_blocked":
            counts["source_quality_blocked"] += 1
        else:
            counts["economic_or_control_gap"] += 1
    return {
        "input_count": len(rows),
        "disposition_counts": dict(counts),
        "unaccounted_count": len(rows) - sum(counts.values()),
        **AUTHORITY,
    }


def signal_execution_feasibility(
    result, *, symbol, source_date, signal_policy, observation_dir
):
    """Recheck a selected proxy against its exact prospective seed and raw BBO.

    Missing historical quotes leave the proxy available for research, but do
    not authorize a newly selected execution policy. No API is called here.
    """
    expected_seed = digest(signal_policy)
    windows = {
        window: (result.get(window) or {}).get(
            "episodes", (result.get("selected_episodes") or {}).get(window, [])
        )
        for window in ("calibration", "holdout")
    }
    episodes = [row for rows in windows.values() for row in rows]
    receipt = {
        "schema": "widget_signal_execution_feasibility_v1",
        "symbol": symbol,
        "source_date": source_date.isoformat(),
        "parameters_sha256": digest(result.get("selected_policy")),
        "signal_seed_parameters_sha256": expected_seed,
        "episode_count": len(episodes),
        "matched_episode_count": 0,
        "status": "source_gap",
        "source_hashes": {},
        "evidence_role": "modeled_full_quantity_BBO_not_actual_fill",
        **AUTHORITY,
    }
    if any(
        len(windows[window])
        != (result.get(window) or {}).get("episode_count", len(windows[window]))
        for window in windows
    ):
        receipt["reason"] = "selected_episode_count_mismatch"
        return receipt
    identities = [(row.get("entry_at"), row.get("exit_at")) for row in episodes]
    if len(set(identities)) != len(identities):
        receipt["reason"] = "duplicate_selected_episode"
        return receipt
    if not episodes:
        receipt["reason"] = "selected_episode_lineage_missing"
        return receipt
    clocks = [aware(row.get(k)) for row in episodes for k in ("entry_at", "exit_at")]
    if any(clock is None or clock.date() > source_date for clock in clocks):
        receipt["reason"] = "selected_episode_clock_invalid"
        return receipt
    days = {clock.date() for clock in clocks}
    observations = {}
    quote_identities = {}
    for day in sorted(days):
        path = (
            Path(observation_dir)
            / f"widget_symbol_advisory_{symbol}_{day:%Y%m%d}.jsonl"
        )
        try:
            before = path.lstat()
            if path.is_symlink() or before.st_size > 64 * 1024 * 1024:
                continue
            now = datetime.now().astimezone(clocks[0].tzinfo)
            if day > now.date() or (
                day == now.date() and (now.hour, now.minute) < (20, 5)
            ):
                continue
            source_hash = hashlib.sha256()
            with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as handle:
                for line in handle:
                    source_hash.update(line)
                    payload = json.loads(line)
                    if not isinstance(payload, dict):
                        raise ValueError("observation_not_object")
                    seed = payload.get("observation_seed") or {}
                    advisory, bbo = (
                        payload.get("advisory") or {},
                        payload.get("bbo") or {},
                    )
                    at = aware(payload.get("observed_at_kst"))
                    received = aware(bbo.get("received_at"))
                    if (
                        payload.get("symbol") != symbol
                        or at is None
                        or at.date() != day
                        or payload.get("observation_role") == "raw_only"
                        or payload.get("advisory_generated") is False
                        or seed.get("parameters_sha256") != expected_seed
                        or advisory.get("session") != "KRX_REGULAR"
                        or payload.get("market_venue") != "KRX"
                        or (advisory.get("source_quality") or {}).get("status")
                        != "PASS"
                        or received is None
                        or not 0 <= (at - received).total_seconds() <= 5
                        or not all(
                            numeric(bbo.get(k)) is not None and bbo[k] > 0
                            for k in (
                                "best_bid",
                                "best_ask",
                                "best_bid_qty",
                                "best_ask_qty",
                            )
                        )
                        or bbo["best_bid"] > bbo["best_ask"]
                    ):
                        continue
                    quote_key = (day, received)
                    fingerprint = tuple(
                        bbo[key]
                        for key in (
                            "best_bid",
                            "best_ask",
                            "best_bid_qty",
                            "best_ask_qty",
                        )
                    )
                    if (
                        quote_key in quote_identities
                        and quote_identities[quote_key] != fingerprint
                    ):
                        raise ValueError("conflicting_quote_identity")
                    quote_identities[quote_key] = fingerprint
                    effective = aware(seed.get("effective_at_kst"))
                    if effective is None or at < effective:
                        continue
                    observations.setdefault(day, []).append(
                        (at, bbo, advisory.get("state"))
                    )
            after = path.lstat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
            ):
                observations.pop(day, None)
                continue
            receipt["source_hashes"][str(path.resolve())] = source_hash.hexdigest()
        except (OSError, ValueError, TypeError, AttributeError, UnicodeError):
            observations.pop(day, None)
    for row in episodes:
        entry, exit_ = aware(row["entry_at"]), aware(row["exit_at"])
        price, exit_price = numeric(row.get("entry_price")), numeric(
            row.get("exit_price")
        )
        if price is None or exit_price is None:
            continue
        opening = next(
            (
                bbo
                for at, bbo, state in observations.get(entry.date(), [])
                if 0 <= (at - entry).total_seconds() <= 5
                and state in {"ENTRY_READY", "ENTRY_CAUTION"}
                and bbo["best_ask"] <= price
                and bbo["best_ask_qty"] >= 40
            ),
            None,
        )
        closing = next(
            (
                bbo
                for at, bbo, _state in observations.get(exit_.date(), [])
                if 0 <= (at - exit_).total_seconds() <= 5
                and bbo["best_bid"] >= exit_price
                and bbo["best_bid_qty"] >= 40
            ),
            None,
        )
        if opening is not None and closing is not None:
            receipt["matched_episode_count"] += 1
    receipt["status"] = (
        "pass" if receipt["matched_episode_count"] == len(episodes) else "source_gap"
    )
    receipt["reason"] = (
        "exact_seed_full_quantity_base_and_stress"
        if receipt["status"] == "pass"
        else "exact_seed_entry_exit_depth_missing"
    )
    return receipt


def research_universe_handoff(census, *, source_date, universe, results):
    """Conserve upstream census IDs without enrolling or reviving symbols."""
    rows = census.get("opportunity_details") if isinstance(census, dict) else None
    if isinstance(rows, dict):
        # Use the canonical panel once; other panels overlap the same census.
        rows = ((rows.get("liquid_common") or {}).get("top_20") or {}).get(
            "forward_exact"
        )
    if (
        not isinstance(rows, list)
        or census.get("target_date") != source_date.isoformat()
    ):
        return {
            "status": "source_gap",
            "reason": "exact_date_census_missing",
            **AUTHORITY,
        }
    try:
        census_hash = digest(census)
    except (TypeError, ValueError):
        return {"status": "source_gap", "reason": "census_content_invalid", **AUTHORITY}
    dispositions = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            dispositions.append(
                {"source_index": index, "disposition": "invalid_census_row"}
            )
            continue
        symbol = str(row.get("symbol") or row.get("stock_code") or "")
        disposition = (
            "not_enrolled_research_universe"
            if symbol not in universe
            else (
                "policy_selected"
                if (results.get(symbol) or {}).get("decision")
                == "holdout_pass_widget_signal_policy_candidate"
                else "research_not_selected_or_source_gap"
            )
        )
        dispositions.append(
            {
                "source_index": index,
                "symbol": symbol,
                "opportunity_id": row.get("opportunity_id")
                or row.get("opportunity_episode_id")
                or row.get("episode_id"),
                "disposition": disposition,
            }
        )
    return {
        "schema": "widget_research_universe_handoff_v1",
        "status": "observed",
        "source_date": source_date.isoformat(),
        "census_content_sha256": census_hash,
        "input_count": len(rows),
        "dispositions": dispositions,
        "disposition_counts": dict(Counter(row["disposition"] for row in dispositions)),
        "unaccounted_count": len(rows) - len(dispositions),
        "recall_role": "observed_census_to_research_not_whole_market_recall",
        **AUTHORITY,
    }
