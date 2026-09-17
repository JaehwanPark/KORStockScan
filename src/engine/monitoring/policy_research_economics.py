"""Source-only machine/widget economics, separate from broker accounting.

Owned by monitoring: these adapters consume frozen observations, never issue
orders, create owner signals, or assign live capital/quantity authority.
"""

from __future__ import annotations

from collections import Counter
from bisect import bisect_left
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
import stat
from pathlib import Path
from zoneinfo import ZoneInfo

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
    pnl = capital_seconds = 0
    for row in episodes:
        price = numeric(row.get("entry_price"))
        net = numeric(row.get("net_return_pct"))
        entry, exit_ = aware(row.get("entry_at")), aware(row.get("exit_at"))
        if (
            price is None
            or price <= 0
            or net is None
            or entry is None
            or exit_ is None
            or entry.date() not in dates
            or exit_ < entry
        ):
            valid = False
            break
        pnl += price * quantity * net / 100
        capital_seconds += price * quantity * (exit_ - entry).total_seconds()
    if not valid:
        pnl = capital_seconds = None
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


def joint_capital_demand(
    symbol_episodes, *, capital_limit_krw=None, quantity=10, buy_fee_bps=0
):
    """Measure simultaneous demand; do not invent a shared allocation limit."""
    events, invalid, pnl = [], 0, 0.0
    identities = set()
    for symbol, episodes in sorted(symbol_episodes.items()):
        for row in episodes:
            entry, exit_ = aware(row.get("entry_at")), aware(row.get("exit_at"))
            price, net = (
                numeric(row.get("entry_price")),
                numeric(row.get("net_return_pct")),
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
            notional = price * quantity * (1 + buy_fee_bps / 10000)
            events.extend([(entry, 1, notional), (exit_, 0, -notional)])
            pnl += price * quantity * net / 100
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
            else "observed"
            if valid_limit
            else "allocation_contract_missing"
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
        ask, bid = (
            numeric(entry.get("ask_price")),
            numeric(hit.get("target_executable_bid")),
        )
        target, available = (
            numeric(hit.get("target_price")),
            numeric(hit.get("target_available_bid_quantity")),
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
    revision = result.get("candidate_revision")
    if revision is not None:
        from src.engine.monitoring.research_closed_loop import validate_revision

        try:
            validate_revision(revision, symbol=symbol, owner="widget")
            if revision["parameters"] != result.get("selected_policy"):
                raise ValueError("prospective_parameters_changed")
            from src.engine.monitoring.research_closed_loop import (
                widget_prospective_summary_valid,
            )

            if not widget_prospective_summary_valid(result, revision):
                raise ValueError("prospective_native_economic_summary_mismatch")
        except (TypeError, ValueError, KeyError):
            return {
                "status": "source_gap",
                "reason": "prospective_revision_invalid",
                **AUTHORITY,
            }
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
        "source_generations": {},
        "depth_demands": [],
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
    if revision is not None:
        for row in episodes:
            entry = aware(row.get("entry_at"))
            signal = aware(row.get("signal_at"))
            cost = comparison_cost_contract(entry.date())
            price, exit_price, net = (
                numeric(row.get("entry_price")),
                numeric(row.get("exit_price")),
                numeric(row.get("net_return_pct")),
            )
            if (
                signal is None
                or signal >= entry
                or entry.date().isoformat()
                not in revision["calibration_dates"] + revision["holdout_dates"]
                or price is None
                or price <= 0
                or exit_price is None
                or net is None
                or row.get("cost_contract_sha256") != cost["contract_sha256"]
                or abs(
                    net - ((exit_price / price - 1) * 100 - cost["round_trip_cost_pct"])
                )
                > 0.0000011
            ):
                receipt["reason"] = "prospective_episode_causal_cost_contract_invalid"
                return receipt
    days = {clock.date() for clock in clocks}
    observations = {}
    quote_identities = {}
    for day in sorted(days):
        path = (
            Path(observation_dir)
            / f"widget_symbol_advisory_{symbol}_{day:%Y%m%d}.jsonl"
        )
        from src.engine.monitoring.research_closed_loop import DIRECTORY, _directory

        paths = [path]
        if revision is not None:
            from src.engine.monitoring.research_fact_archive import fact_path

            paths.append(fact_path(_directory(DIRECTORY), symbol, day))
        for path in paths:
            path_observations = []
            try:
                before = path.lstat()
                if path.is_symlink() or before.st_size > 64 * 1024 * 1024:
                    continue
                now = datetime.now().astimezone(clocks[0].tzinfo)
                if day > now.date() or (
                    day == now.date() and (now.hour, now.minute) < (20, 5)
                ):
                    continue
                from src.engine.monitoring.research_source_facts import (
                    indexed_day_facts,
                )

                source_sha256, facts = indexed_day_facts(
                    path,
                    windows=[
                        (clock - timedelta(seconds=5), clock + timedelta(seconds=5))
                        for clock in clocks
                        if clock.date() == day
                    ],
                )
                for payload in facts:
                    if (
                        revision is not None
                        and payload.get("schema")
                        == "prospective_registered_seed_market_facts_v1"
                    ):
                        memberships = payload.get("seed_memberships") or ()
                        member = next(
                            (
                                value
                                for value in memberships
                                if value.get("revision_sha256")
                                == revision["revision_sha256"]
                                and value.get("parameters_sha256")
                                == revision["parameters_sha256"]
                                and value.get("frozen_at") == revision["frozen_at"]
                            ),
                            None,
                        )
                        at = aware(payload.get("observed_at_kst"))
                        if (
                            member is None
                            or at is None
                            or at <= aware(revision["frozen_at"])
                            or any(
                                payload.get(key) is not value
                                for key, value in AUTHORITY.items()
                            )
                        ):
                            continue
                        payload = dict(payload)
                        payload["observation_seed"] = {
                            "parameters_sha256": expected_seed,
                            "effective_at_kst": revision["calibration_dates"][0]
                            + "T09:03:00+09:00",
                        }
                        payload["advisory"] = {
                            "session": "KRX_REGULAR",
                            "state": "CF_ENTRY",
                            "source_quality": {
                                "status": payload.get("source_quality_status")
                            },
                        }
                        payload["advisory_generated"] = None
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
                    anchors = [clock for clock in clocks if clock.date() == day]
                    if any(0 <= (at - clock).total_seconds() <= 5 for clock in anchors):
                        path_observations.append((at, bbo, advisory.get("state")))
                after = path.lstat()
                if (before.st_ino, before.st_size, before.st_mtime_ns) != (
                    after.st_ino,
                    after.st_size,
                    after.st_mtime_ns,
                ):
                    continue
                observations.setdefault(day, []).extend(path_observations)
                receipt["source_hashes"][str(path.resolve())] = source_sha256
                from src.engine.monitoring.research_source_facts import generation

                receipt["source_generations"][str(path.resolve())] = generation(
                    path.lstat()
                )
            except ValueError as exc:
                if str(exc) == "conflicting_quote_identity":
                    receipt["reason"] = "conflicting_quote_identity"
                    return receipt
            except (OSError, TypeError, AttributeError, UnicodeError):
                continue
    for day, facts in observations.items():
        facts.sort(key=lambda row: row[0])
    quote_clocks = {
        day: [row[0] for row in facts] for day, facts in observations.items()
    }

    def nearby(clock):
        facts = observations.get(clock.date(), [])
        at = quote_clocks.get(clock.date(), [])
        return facts[
            bisect_left(at, clock) : bisect_left(
                at, clock + timedelta(seconds=5, microseconds=1)
            )
        ]

    for row in episodes:
        entry, exit_ = aware(row["entry_at"]), aware(row["exit_at"])
        price, exit_price = (
            numeric(row.get("entry_price")),
            numeric(row.get("exit_price")),
        )
        if price is None or exit_price is None:
            continue
        opening = next(
            (
                bbo
                for at, bbo, state in nearby(entry)
                if 0 <= (at - entry).total_seconds() <= 5
                and state in {"ENTRY_READY", "ENTRY_CAUTION", "CF_ENTRY"}
                and bbo["best_ask"] <= price
                and bbo["best_ask_qty"] >= 40
            ),
            None,
        )
        closing = next(
            (
                bbo
                for at, bbo, _state in nearby(exit_)
                if 0 <= (at - exit_).total_seconds() <= 5
                and (
                    revision is None
                    or (
                        opening is not None
                        and type(opening.get("source_epoch")) is int
                        and opening["source_epoch"] > 0
                        and bbo.get("source_epoch") == opening["source_epoch"]
                    )
                )
                and bbo["best_bid"] >= exit_price
                and bbo["best_bid_qty"] >= 40
            ),
            None,
        )
        if opening is not None and closing is not None:
            receipt["matched_episode_count"] += 1
            for side, book in (("best_ask_qty", opening), ("best_bid_qty", closing)):
                receipt["depth_demands"].append(
                    dict(
                        quote_id=digest(
                            [
                                symbol,
                                book.get("source_epoch"),
                                book.get("received_at"),
                                book.get("source_sequence"),
                                side,
                            ]
                        ),
                        stress_quantity=40,
                        available_quantity=book[side],
                    )
                )
    receipt["status"] = (
        "pass" if receipt["matched_episode_count"] == len(episodes) else "source_gap"
    )
    receipt["reason"] = (
        "exact_seed_full_quantity_base_and_stress"
        if receipt["status"] == "pass"
        else "exact_seed_entry_exit_depth_missing"
    )
    from src.engine.monitoring.research_closed_loop import seal_execution_receipt

    return seal_execution_receipt(receipt)


def research_universe_handoff(census, *, source_date, universe, results):
    """Conserve upstream census IDs without enrolling or reviving symbols."""
    admission = research_admission_ledger(
        census, source_date=source_date, universe=universe, owner="widget"
    )
    rows = census.get("opportunity_details") if isinstance(census, dict) else None
    if isinstance(rows, dict):
        # Use the canonical panel once; other panels overlap the same census.
        panel = rows.get("liquid_common")
        window = panel.get("top_20") if isinstance(panel, dict) else None
        rows = window.get("forward_exact") if isinstance(window, dict) else None
    if (
        not isinstance(rows, list)
        or census.get("target_date") != source_date.isoformat()
    ):
        return {
            "status": "source_gap",
            "reason": "exact_date_census_missing",
            "admission_ledger": admission,
            **AUTHORITY,
        }
    census_hash = admission.get("census_content_sha256")
    if census_hash is None:
        return {
            "status": "source_gap",
            "reason": "census_content_invalid",
            "admission_ledger": admission,
            **AUTHORITY,
        }
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
        "admission_ledger": admission,
        **AUTHORITY,
    }


def _load_bounded_research_summary(path, *, maximum_bytes):
    """Read a bounded, stable regular summary; never scan growing raw data."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum_bytes:
                return None
            raw = handle.read(maximum_bytes + 1)
            after = os.fstat(handle.fileno())
            current = os.stat(path, follow_symlinks=False)

        def identity(value):
            return (
                value.st_dev,
                value.st_ino,
                value.st_size,
                value.st_mtime_ns,
                value.st_ctime_ns,
            )

        if (
            len(raw) > maximum_bytes
            or identity(before) != identity(after)
            or identity(after) != identity(current)
        ):
            return None
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return None
        digest(payload)  # Reject non-finite facts, even in optional fields.
        return payload
    except (OSError, ValueError, TypeError, UnicodeError, RecursionError):
        return None


def research_census_file_generation(path):
    value = os.stat(path, follow_symlinks=False)
    if not stat.S_ISREG(value.st_mode):
        raise ValueError("census_parent_not_regular")
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
        "ctime_ns": value.st_ctime_ns,
    }


def load_research_census(path, *, maximum_bytes=4 * 1024 * 1024):
    """Prefer the writer-issued compact projection bound to the current parent."""
    path = Path(path)
    sidecar = path.with_suffix(".admission.json")
    try:
        if sidecar.exists() or sidecar.is_symlink():
            before = research_census_file_generation(path)
            payload = _load_bounded_research_summary(
                sidecar, maximum_bytes=maximum_bytes
            )
            if (
                not payload
                or payload.get("schema") != "market_opportunity_research_projection_v1"
            ):
                return None
            parent = payload.get("canonical_parent") or {}
            parent_hash = parent.get("sha256") if isinstance(parent, dict) else None
            if (
                not isinstance(parent, dict)
                or parent.get("filename") != path.name
                or parent.get("generation") != before
                or not isinstance(parent_hash, str)
                or len(parent_hash) != 64
                or any(character not in "0123456789abcdef" for character in parent_hash)
            ):
                return None
            checksum = payload.get("projection_content_sha256")
            if checksum != digest(
                {
                    key: value
                    for key, value in payload.items()
                    if key != "projection_content_sha256"
                }
            ):
                return None
            if any(
                payload.get(key) is not expected for key, expected in AUTHORITY.items()
            ):
                return None
            if before != research_census_file_generation(path):
                return None
            return payload
        return _load_bounded_research_summary(path, maximum_bytes=maximum_bytes)
    except (OSError, ValueError, TypeError, RecursionError):
        return None


def research_census_projection(report, *, parent_filename, parent_sha256, generation):
    """Project admission facts during the existing producer's publication."""
    keys = (
        "opportunity_episode_id",
        "opportunity_id",
        "episode_id",
        "stock_code",
        "symbol",
        "stock_name",
        "venue",
        "session",
        "first_census_at",
        "symbol_master_status",
        "instrument_type",
        "listing_market",
    )
    details = report.get("opportunity_details")

    def slim(row):
        if not isinstance(row, dict):
            return row
        stages, clocks = row.get("stage_reached"), row.get("first_stage_at")
        return {
            **{key: row[key] for key in keys if key in row},
            "stage_reached": (
                {"candidate_evaluated": stages.get("candidate_evaluated")}
                if isinstance(stages, dict)
                else None
            ),
            "first_stage_at": (
                {"candidate_evaluated": clocks.get("candidate_evaluated")}
                if isinstance(clocks, dict)
                else None
            ),
            "canonical_source_row_sha256": digest(row),
        }

    if isinstance(details, list):
        projected = [slim(row) for row in details]
    elif isinstance(details, dict):
        projected = {}
        for panel, windows in details.items():
            if not isinstance(windows, dict):
                projected[panel] = None
                continue
            projected[panel] = {}
            for window, evidence in windows.items():
                rows = (
                    evidence.get("forward_exact")
                    if isinstance(evidence, dict)
                    else None
                )
                projected[panel][window] = {
                    "forward_exact": (
                        [slim(row) for row in rows] if isinstance(rows, list) else None
                    )
                }
    else:
        projected = None
    payload = {
        "schema": "market_opportunity_research_projection_v1",
        "target_date": report.get("target_date"),
        "generated_at": report.get("generated_at"),
        "canonical_parent": {
            "filename": parent_filename,
            "sha256": parent_sha256,
            "generation": generation,
        },
        "opportunity_details": projected,
        **AUTHORITY,
    }
    payload["projection_content_sha256"] = digest(payload)
    return payload


def research_admission_ledger(census, *, source_date, universe, owner):
    """Audit causal admission readiness, not signals or live enrollment.

    All forward panels are projections. Preserve every input location while
    deduplicating native IDs; retrospective outcomes never choose admission.
    A new symbol waits for the existing catalog/capacity contract, not a fill.
    """
    base = {
        "schema": "machine_research_admission_ledger_v1",
        "owner": owner,
        "source_date": source_date.isoformat(),
        "metric_role": "funnel_count",
        "decision_authority": "research_admission_readiness_only",
        "catalog_mutated": False,
        "primary_recall_denominator_changed": False,
        "window_policy": "exact_source_date_forward_candidate_join",
        "sample_floor": "one_native_causal_candidate_with_official_master",
        "primary_decision_metric": "input_count_and_disposition_conservation",
        "source_quality_gate": "bounded_summary_native_clock_scope_master_binding",
        "valid_zero_day_proven": False,
        "forbidden_uses": [
            "runtime_policy_selection",
            "actual_order_permission",
            "ex_post_profit_admission_priority",
            "whole_market_recall_acceptance",
        ],
        **AUTHORITY,
    }
    lane_scopes = {
        "widget": {("KRX", "KRX_REGULAR")},
        "low_price_two_leg": {("KRX", "KRX_REGULAR"), ("NXT", "NXT_REGULAR_OVERLAP")},
    }.get(owner, set())
    try:
        if source_date.isoformat() < "2026-06-05" or not lane_scopes:
            raise ValueError("research_date_or_owner_contract_invalid")
        if (
            not isinstance(census, dict)
            or census.get("target_date") != source_date.isoformat()
        ):
            raise ValueError("exact_date_census_missing")
        census_hash = digest(census)
        details = census.get("opportunity_details")
        inputs, malformed = [], []
        if isinstance(details, list):
            inputs = [
                (f"opportunity_details/{i}", row) for i, row in enumerate(details)
            ]
        elif isinstance(details, dict):
            for panel, windows in sorted(details.items()):
                if not isinstance(windows, dict):
                    malformed.append(f"opportunity_details/{panel}")
                    continue
                for window, evidence in sorted(windows.items()):
                    location = f"opportunity_details/{panel}/{window}/forward_exact"
                    rows = (
                        evidence.get("forward_exact")
                        if isinstance(evidence, dict)
                        else None
                    )
                    if not isinstance(rows, list):
                        malformed.append(location)
                        continue
                    inputs.extend(
                        (f"{location}/{i}", row) for i, row in enumerate(rows)
                    )
        else:
            raise ValueError("census_details_invalid")
    except (TypeError, ValueError, RecursionError) as error:
        return {
            **base,
            "status": "source_gap",
            "reason": str(error),
            "input_count": None,
            "unaccounted_count": None,
        }

    # Detect conflicting bindings before deduplication; no first-row winner.
    bindings = {}
    generation_clock = aware(census.get("generated_at"))
    for _, row in inputs:
        if not isinstance(row, dict):
            continue
        native = (
            row.get("opportunity_episode_id")
            or row.get("opportunity_id")
            or row.get("episode_id")
        )
        if isinstance(native, str) and native.strip():
            binding = digest(
                {
                    **{
                        key: row.get(key)
                        for key in (
                            "venue",
                            "session",
                            "first_census_at",
                            "symbol_master_status",
                            "instrument_type",
                            "listing_market",
                        )
                    },
                    "symbol": row.get("stock_code") or row.get("symbol"),
                    "candidate_reached": (
                        (row.get("stage_reached") or {}).get("candidate_evaluated")
                        if isinstance(row.get("stage_reached"), dict)
                        else None
                    ),
                    "candidate_at": (
                        (row.get("first_stage_at") or {}).get("candidate_evaluated")
                        if isinstance(row.get("first_stage_at"), dict)
                        else None
                    ),
                }
            )
            bindings.setdefault(native, set()).add(binding)
    ledger, seen = [], set()
    for location, row in inputs:
        item = {
            "source_location": location,
            "disposition": "source_gap",
            "reason": "native_identity_missing",
        }
        if not isinstance(row, dict):
            item["reason"] = "invalid_census_row"
            ledger.append(item)
            continue
        native = (
            row.get("opportunity_episode_id")
            or row.get("opportunity_id")
            or row.get("episode_id")
        )
        symbol = row.get("stock_code") or row.get("symbol")
        venue, session = row.get("venue"), row.get("session")
        item.update(
            native_id=native,
            symbol=symbol,
            venue=venue,
            session=session,
            source_row_sha256=digest(row),
            canonical_source_row_sha256=row.get("canonical_source_row_sha256"),
        )
        if (
            not isinstance(native, str)
            or not native.strip()
            or not isinstance(symbol, str)
            or len(symbol) != 6
            or not symbol.isascii()
            or not symbol.isdigit()
            or not isinstance(venue, str)
            or not isinstance(session, str)
            or not session
        ):
            ledger.append(item)
            continue
        if len(bindings[native]) != 1:
            item["reason"] = "conflicting_native_scope"
            ledger.append(item)
            continue
        if native in seen:
            item.update(
                disposition="duplicate_projection",
                reason="native_opportunity_already_accounted",
            )
            ledger.append(item)
            continue
        seen.add(native)
        if (venue, session) not in lane_scopes:
            item.update(
                disposition="excluded_by_contract",
                reason="registered_research_lane_scope_mismatch",
            )
        elif (
            row.get("symbol_master_status") != "verified"
            or row.get("instrument_type") != "EQUITY"
            or not isinstance(row.get("listing_market"), str)
            or row.get("listing_market") not in {"KOSPI", "KOSDAQ"}
        ):
            item["reason"] = "official_common_stock_binding_missing"
        else:
            first = aware(row.get("first_census_at"))
            stages, clocks = row.get("stage_reached"), row.get("first_stage_at")
            candidate_at = (
                aware(clocks.get("candidate_evaluated"))
                if isinstance(clocks, dict)
                else None
            )
            try:
                clock_dates_valid = (
                    first is not None
                    and candidate_at is not None
                    and (
                        first.astimezone(ZoneInfo("Asia/Seoul")).date() == source_date
                        and candidate_at.astimezone(ZoneInfo("Asia/Seoul")).date()
                        == source_date
                    )
                )
            except (OverflowError, ValueError):
                clock_dates_valid = False
            if (
                not isinstance(stages, dict)
                or stages.get("candidate_evaluated") is not True
                or first is None
                or candidate_at is None
                or candidate_at < first
                or not clock_dates_valid
                or ("generated_at" in census and generation_clock is None)
                or (generation_clock is not None and candidate_at > generation_clock)
            ):
                item["reason"] = "causal_scanner_candidate_join_unproven"
            elif symbol in universe:
                item.update(
                    disposition="admitted",
                    reason="existing_research_catalog_causal_candidate",
                    research_state="pending_consumer_source_validation",
                )
            else:
                item.update(
                    disposition="deferred_capacity",
                    reason="research_catalog_capacity_contract_pending",
                    research_state="pending_catalog_admission",
                )
        ledger.append(item)
    counts = dict(Counter(row["disposition"] for row in ledger))
    return {
        **base,
        "status": "source_gap" if malformed or counts.get("source_gap") else "observed",
        "census_content_sha256": census_hash,
        "canonical_parent": census.get("canonical_parent"),
        "input_count": len(inputs),
        "native_id_count": len(bindings),
        "dispositions": ledger,
        "disposition_counts": counts,
        "unaccounted_count": len(inputs) - sum(counts.values()),
        "malformed_scopes": malformed,
        "admission_rule": "causal_candidate_and_official_master_not_ex_post_profit",
        "catalog_capacity_closure_pending": True,
        "source_generation_clock_proven": generation_clock is not None,
        "registered_research_scopes": sorted([list(scope) for scope in lane_scopes]),
        "scope_disposition_counts": {
            scope: dict(
                Counter(
                    row["disposition"]
                    for row in ledger
                    if f"{row.get('venue', 'UNKNOWN')}:{row.get('session', 'UNKNOWN')}"
                    == scope
                )
            )
            for scope in sorted(
                {
                    f"{row.get('venue', 'UNKNOWN')}:{row.get('session', 'UNKNOWN')}"
                    for row in ledger
                }
            )
        },
    }
