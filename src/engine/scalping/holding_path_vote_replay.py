"""Postclose path-vote lineage and replay over broker-complete positions.

The caller owns the strict BUY/SELL/COMPLETED/cost cohort. This module never
turns a vote classification into a causal fill or an automatic policy.
"""

from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Callable, Iterable

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
    if path_id == "ADD_REBOUND":
        # ADD timing belongs to the selected Main machine. Its incumbent
        # confirmation can be replayed, but this exit owner cannot tune it.
        return []
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


def compact_signal(event):
    """Original decision fields needed for replay; no reconstructed votes."""
    fields=event.get('fields') if isinstance(event.get('fields'),dict) else {}
    return dict(stage='holding_path_signal_snapshot',fields={key:fields.get(key) for key in (
        'path_id','market','session_key','position_key','buy_fill_identity','signal_id',
        'signal_at','policy_sha256','decision','vote_count')})


def freeze_replay_trade(trade, root, output, sources):
    """Seal the original per-position vote inputs alongside the bounded cohort."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.lifecycle.research_json_stream import TRADE_FIELDS
    from src.engine.ai.holding_vote_replay_source import assemble_votes, SCHEMA
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    position_key='record:'+_trade_id(trade)
    source=dict(schema=SCHEMA,position_key=position_key,
                store_name=path_vote_store_path(root,position_key).name,path_id=None)
    return dict(schema='holding_path_frozen_trade_v1',
        trade={key:trade.get(key) for key in TRADE_FIELDS},
        source_gap=trade.get('holding_path_projection_gap') or trade.get('projection_source_gap'),
        signals_ref=trade.get('holding_path_signal_snapshots_ref') or storage.write_tree(output,
            (compact_signal(event) for event in trade.get('timeline') or []
             if isinstance(event,dict) and event.get('stage')=='holding_path_signal_snapshot')),
        buys_ref=trade.get('buy_fill_legs_ref') or storage.write_tree(output,trade.get('buy_fill_legs') or []),
        votes=assemble_votes(root,output,source,sources))


def summarize_frozen_holding_path_votes(assembly, partitions, *, model, clean_start):
    """Use the same strict admission and replay on sealed partition inputs."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.automation.main_trailing_all_scope_research import _sealed
    from src.engine.ai.holding_vote_replay_source import _verify_projection
    from src.engine.holding_exit_observation_report import _strict_completed_reasons,_is_valid_completed_trade
    gaps={};frozen_count=0
    current_votes={}
    def bounded_rows(reference):
        rows=[];size=0
        for row in storage.iter_tree(assembly,reference):
            size+=len(storage.encoded(row))
            if size>16*1024*1024:
                raise ValueError('frozen_vote_position_partition_required')
            rows.append(row)
        return rows
    def trades():
        nonlocal frozen_count
        for part in storage.iter_tree(assembly,partitions):
            payload=_sealed(assembly/part['path'],expected=part.get('artifact_sha256'))
            for position in payload['positions']:
                if position['evidence_kind']!='actual_completed':continue
                ref=position.get('holding_path_diagnostic_ref')
                if not ref:
                    gaps[position['position_key']]=['frozen_vote_trade_missing'];continue
                rows=list(storage.iter_tree(assembly,ref))
                if len(rows)!=1 or rows[0].get('schema')!='holding_path_frozen_trade_v1':
                    raise ValueError('holding_path_frozen_trade_invalid')
                frozen_count+=1;frozen=rows[0];trade=frozen['trade']
                reasons=_strict_completed_reasons(trade,clean_start=clean_start)
                if position['position_key']!='main:'+_trade_id(trade):
                    reasons.append('frozen_vote_position_identity_mismatch')
                if not _is_valid_completed_trade(trade):reasons.append('completed_trade_invalid')
                if frozen.get('source_gap'):reasons.append(frozen['source_gap'])
                if reasons:
                    gaps[_trade_id(trade)]=sorted(set(reasons));continue
                vote_ref=frozen['votes']
                try:
                    trade=dict(trade,buy_fill_legs=bounded_rows(frozen['buys_ref']),
                        timeline=bounded_rows(frozen['signals_ref']))
                    rows=bounded_rows(vote_ref['events_ref']) if vote_ref.get('status')=='source_bound' else []
                except ValueError as exc:
                    if str(exc)!='frozen_vote_position_partition_required':raise
                    gaps[_trade_id(trade)]=[str(exc)];continue
                current_votes.clear()
                # A retained VALID verdict without its exact original input
                # is evidence loss, not an eligible model observation.
                for row in rows:
                    if row.get('status')=='VALID' and row.get('actual_input_verified') is True:
                        try:
                            _verify_projection(row['actual_input_ref'],row)
                        except (ValueError,OSError,KeyError,TypeError):
                            row['actual_input_verified']=False
                current_votes['record:'+_trade_id(trade)]=[
                    dict(row,status='INSUFFICIENT',excluded_reason='original_vote_input_unverified')
                    if row.get('status')=='VALID' and row.get('actual_input_verified') is not True else row
                    for row in rows]
                yield trade
    result=summarize_holding_path_votes(trades(),load_events=lambda key:current_votes[key],model=model)
    result.update(source_status='sealed_partition_vote_inputs' if frozen_count else
        'source_gap_partitioned_vote_inputs_unavailable',frozen_position_count=frozen_count,
        partition_excluded_by_position_id=gaps,economic_replay_observed=False)
    return result


def summarize_holding_path_votes(
    strict_trades: Iterable[dict[str, Any]],
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
                "strict_completed_position_count": 0,
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
    strict_ids=[]
    for trade in strict_trades:
        trade_id = _trade_id(trade)
        strict_ids.append(trade_id)
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
        cell['strict_completed_position_count']=len(strict_ids)
        cell["status"] = (
            "replay_ready_economics_missing" if cell["eligible_signal_count"]
            else "source_gap_no_replayable_signal"
        )
    return {
        "schema": "holding_path_vote_postclose_replay_v1",
        "decision_authority": "research_only_no_runtime_apply",
        "strict_completed_position_ids": strict_ids,
        "strict_population_count": len(strict_ids),
        "path_market": cells,
        "excluded_by_position_id": exclusions,
        "selected_policy": None,
        "allowed_runtime_apply": False,
        "cost_after_paired_ev_krw": None,
        "economic_source_gap": "signal_time_counterfactual_fill_and_no_add_outcome_missing",
    }
