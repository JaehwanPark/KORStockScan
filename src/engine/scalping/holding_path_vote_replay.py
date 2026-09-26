"""Postclose path-vote lineage and replay over broker-complete positions.

The caller owns the strict BUY/SELL/COMPLETED/cost cohort. This module never
turns a vote classification into a causal fill or an automatic policy.
"""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Callable

from src.engine.ai.holding_exit_vote import (
    MARKETS, PATH_IDS, PATH_POLICY_BY_MARKET, input_snapshot_id,
    buy_fill_identity_from_legs, path_signal_snapshot, validate_path_policy,
)


def _trade_id(row: dict[str, Any]) -> str:
    return str(row.get("id") or row.get("record_id") or "").strip()


def _buy_identity_at_signal(trade: dict[str, Any], signal_at: float) -> str | None:
    legs = trade.get("buy_fill_legs") or []
    prior = []
    for leg in legs:
        if not isinstance(leg, dict):
            return None
        try:
            at = datetime.fromisoformat(str(leg["at"]))
            epoch = at.timestamp() if at.tzinfo else None
        except (KeyError, TypeError, ValueError, OverflowError):
            return None
        if epoch is None or not math.isfinite(epoch):
            return None
        if epoch <= signal_at:
            prior.append(leg)
    return buy_fill_identity_from_legs(prior)


def _candidate_policies(
    path_id: str, base: dict[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    """Bounded single-axis and interacting quorum/freshness alternatives."""
    choices = {
        "window_sec": (120.0, 240.0),
        "min_votes": (3,),
        "pass_votes": (3,),
        "veto_votes": (3,),
        "firm_pass_votes": (0, 1, 2),
        "firm_veto_votes": (0, 2),
        "max_latest_age_sec": (20.0, 60.0),
        "max_gap_sec": (60.0, 120.0),
        "min_duration_sec": (4.0, 16.0),
        "max_defer_sec": (max(1.0, float(base["max_defer_sec"]) / 2.0),),
    }
    candidates = []
    for axis, values in choices.items():
        for value in values:
            if value == base[axis]:
                continue
            candidate = {**base, axis: value}
            if validate_path_policy(candidate, path_id=path_id):
                candidates.append((axis, candidate))
    for label, changes in (
        ("quorum_compound", {"min_votes": 3, "pass_votes": 3,
                             "veto_votes": 3}),
        ("freshness_compound", {"max_latest_age_sec": 20.0,
                                "max_gap_sec": 60.0,
                                "min_duration_sec": 4.0}),
    ):
        candidate = {**base, **changes}
        if candidate != base and validate_path_policy(candidate, path_id=path_id):
            candidates.append((label, candidate))
    return candidates


def summarize_holding_path_votes(
    strict_trades: list[dict[str, Any]],
    *,
    load_events: Callable[[str], list[dict[str, Any]]],
    model: str,
) -> dict[str, Any]:
    """Replay first signals without inventing missing votes or paired economics."""
    cells: dict[str, dict[str, Any]] = {}
    for path in sorted(PATH_IDS):
        for market in sorted(MARKETS):
            base = PATH_POLICY_BY_MARKET[(path, market)]
            cells[f"{path}|{market}"] = {
                "path_id": path, "market": market,
                "runtime_policy_sha256": input_snapshot_id(base),
                "strict_completed_position_count": len(strict_trades),
                "signal_count": 0, "eligible_signal_count": 0,
                "vote_count": 0, "invalid_vote_count": 0,
                "zero_vote_signals": 0, "one_vote_signals": 0,
                "runtime_decisions": {"PASS": 0, "VETO": 0, "INSUFFICIENT": 0},
                "candidate_grid": [
                    {"axis": axis, "policy_sha256": input_snapshot_id(candidate),
                     "policy": candidate,
                     "decision_counts": {"PASS": 0, "VETO": 0,
                                         "INSUFFICIENT": 0},
                     "cost_after_paired_ev_krw": None,
                     "censoring_status": "counterfactual_execution_unobserved"}
                    for axis, candidate in _candidate_policies(path, base)
                ],
                "cost_after_paired_ev_krw": None,
                "prompt_comparison_status": "source_gap_no_counterfactual_model_votes",
                "holdout_status": "source_gap_no_independent_economic_comparison",
                "allowed_runtime_apply": False,
            }
    exclusions: dict[str, list[str]] = {}
    for trade in strict_trades:
        trade_id = _trade_id(trade)
        if not trade_id:
            exclusions["missing_id"] = ["strict_trade_id_missing"]
            continue
        position_key = f"record:{trade_id}"
        try:
            events = load_events(position_key)
        except (OSError, ValueError) as exc:
            events = []
            exclusions.setdefault(trade_id, []).append(
                f"vote_ledger_unreadable:{type(exc).__name__}"
            )
        if not events:
            exclusions.setdefault(trade_id, []).append("vote_ledger_missing")
        timeline = [item for item in trade.get("timeline") or []
                    if isinstance(item, dict)
                    and item.get("stage") == "holding_path_signal_snapshot"]
        if not timeline:
            exclusions.setdefault(trade_id, []).append("path_signal_receipt_missing")
        seen_signals: set[tuple[str, str, str]] = set()
        for signal in timeline:
            fields = signal.get("fields") or {}
            path = str(fields.get("path_id") or "")
            market = str(fields.get("market") or "")
            signal_id = str(fields.get("signal_id") or "")
            if (path not in PATH_IDS or market not in MARKETS or not signal_id
                    or (path, market, signal_id) in seen_signals):
                exclusions.setdefault(trade_id, []).append(
                    "invalid_or_duplicate_path_signal_receipt"
                )
                continue
            seen_signals.add((path, market, signal_id))
            cell = cells[f"{path}|{market}"]
            cell["signal_count"] += 1
            try:
                signal_at = float(fields["signal_at"])
            except (KeyError, ValueError, TypeError):
                exclusions.setdefault(trade_id, []).append("signal_time_invalid")
                continue
            if not math.isfinite(signal_at):
                exclusions.setdefault(trade_id, []).append("signal_time_invalid")
                continue
            buy_fill_identity = _buy_identity_at_signal(trade, signal_at)
            if (buy_fill_identity is None
                    or fields.get("buy_fill_identity") != buy_fill_identity):
                exclusions.setdefault(trade_id, []).append("buy_fill_identity_mismatch")
                continue
            exact_sell = trade.get("exact_sell_fill_time")
            if not exact_sell:
                exclusions.setdefault(trade_id, []).append("exact_sell_time_missing")
                continue
            try:
                sell_dt = datetime.fromisoformat(str(exact_sell))
                sell_at = sell_dt.timestamp() if sell_dt.tzinfo else None
            except (TypeError, ValueError, OverflowError):
                sell_at = None
            if sell_at is None or not math.isfinite(sell_at):
                exclusions.setdefault(trade_id, []).append("exact_sell_time_invalid")
                continue
            if signal_at > sell_at:
                exclusions.setdefault(trade_id, []).append("signal_after_final_sell")
                continue
            path_events = [item for item in events
                           if item.get("path_id") == path
                           and item.get("market") == market
                           and item.get("buy_fill_identity") == buy_fill_identity
                           and isinstance(item.get("received_at"), (int, float))
                           and item["received_at"] < signal_at]
            cell["vote_count"] += sum(item.get("status") == "VALID"
                                      for item in path_events)
            cell["invalid_vote_count"] += sum(item.get("status") != "VALID"
                                              for item in path_events)
            policy = PATH_POLICY_BY_MARKET[(path, market)]
            if fields.get("policy_sha256") != input_snapshot_id(policy):
                exclusions.setdefault(trade_id, []).append("policy_hash_mismatch")
                continue
            session_key = str(fields.get("session_key") or "")
            if not session_key or str(fields.get("position_key")) != position_key:
                exclusions.setdefault(trade_id, []).append("position_or_session_mismatch")
                continue
            replayed = path_signal_snapshot(
                events, position_key=position_key, market=market,
                session_key=session_key, path_id=path, model=model,
                signal_at=signal_at, policy=policy,
                buy_fill_identity=buy_fill_identity,
            )
            try:
                recorded_vote_count = int(fields["vote_count"])
            except (KeyError, ValueError, TypeError, OverflowError):
                exclusions.setdefault(trade_id, []).append("signal_vote_count_invalid")
                continue
            if (str(fields.get("decision")) != replayed["decision"]
                    or recorded_vote_count != replayed["vote_count"]):
                exclusions.setdefault(trade_id, []).append("signal_replay_mismatch")
                continue
            cell["eligible_signal_count"] += 1
            cell["runtime_decisions"][replayed["decision"]] += 1
            if replayed["vote_count"] == 0:
                cell["zero_vote_signals"] += 1
            elif replayed["vote_count"] == 1:
                cell["one_vote_signals"] += 1
            for candidate in cell["candidate_grid"]:
                candidate_result = path_signal_snapshot(
                    events, position_key=position_key, market=market,
                    session_key=session_key, path_id=path, model=model,
                    signal_at=signal_at, policy=candidate["policy"],
                    source_policy_sha256=input_snapshot_id(policy),
                    buy_fill_identity=buy_fill_identity,
                )
                candidate["decision_counts"][candidate_result["decision"]] += 1
    for cell in cells.values():
        cell["status"] = (
            "replay_ready_economics_missing" if cell["eligible_signal_count"]
            else "source_gap_no_replayable_signal"
        )
    return {
        "schema": "holding_path_vote_postclose_replay_v1",
        "decision_authority": "research_only_no_runtime_apply",
        "strict_completed_position_ids": [_trade_id(row) for row in strict_trades],
        "strict_population_count": len(strict_trades),
        "path_market": cells,
        "excluded_by_position_id": exclusions,
        "selected_policy": None,
        "allowed_runtime_apply": False,
        "cost_after_paired_ev_krw": None,
        "economic_source_gap": "signal_time_counterfactual_fill_and_no_add_outcome_missing",
    }
