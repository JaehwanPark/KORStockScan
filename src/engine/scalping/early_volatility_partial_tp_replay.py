"""Clean-baseline replay and policy selection for early scalp partial TP."""

from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable

import duckdb
from sqlalchemy import text

from src.database.db_manager import DBManager
from src.engine.scalping.early_volatility_partial_tp import POLICY_VERSION
from src.engine.trade_profit import calculate_net_realized_pnl, get_trade_cost_rate
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

KST = timezone(timedelta(hours=9))
CLEAN_BASELINE = datetime.fromisoformat("2026-06-04T14:29:09+09:00")
PARTIAL_RATIOS = (0.25, 0.30, 0.35)
TARGET_NET_PCTS = (0.45, 0.55, 0.65, 0.75)
TTL_SECS = (90, 150, 210)
MIN_RANGE_PCT = 0.60
MIN_TICK_SAMPLES = 3
MIN_SPAN_SEC = 2.0
OBSERVATION_WINDOW_SEC = 20.0
BOOTSTRAP_OBSERVATION_WINDOW_SEC = 120.0
OPERATOR_BOOTSTRAP_CODES = ("117730", "459510")
VENUE_PROVENANCE_STAGES = {
    "scalping_sizing_final_price_revalidated",
    "entry_order_sent",
    "probe_submitted",
    "residual_submitted",
    "order_bundle_submitted",
    "holding_started",
    "sell_order_sent",
    "sell_completed",
}
RELEVANT_HOLDING_STAGES = {
    "holding_started",
    "bundle_completed",
    "scale_in_executed",
    "sell_completed",
    "sell_order_sent",
    "stat_action_decision_snapshot",
    "exit_signal",
    "ai_holding_review",
    "bad_entry_refined_candidate",
    "scale_in_feature_context_refresh",
    "scalp_trailing_continuation_recheck",
    "scalp_trailing_loss_conversion_recheck",
    "holding_flow_override_force_exit",
}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").replace("%", "").replace("+", ""))
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "")))
    except Exception:
        return default


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _timestamp(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except Exception:
        return None
    return (
        parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    )


def _ceil_tick(price: float) -> int:
    raw = max(0, int(math.ceil(price)))
    tick = max(1, int(kiwoom_utils.get_tick_size(raw) or 1)) if raw else 1
    return int(math.ceil(raw / tick) * tick) if raw else 0


def _target_price(avg_price: float, target_net_pct: float) -> int:
    return _ceil_tick(
        avg_price
        * (1.0 + target_net_pct / 100.0)
        / max(1e-9, 1.0 - get_trade_cost_rate())
    )


@dataclass
class Trade:
    record_id: str
    code: str = ""
    name: str = ""
    venue: str = ""
    entry_terminal_at: datetime | None = None
    exit_at: datetime | None = None
    exit_price: int = 0
    avg_price: float = 0.0
    qty: int = 0
    actual_submit_seen: bool = False
    completed_seen: bool = False
    events: list[dict[str, Any]] = field(default_factory=list)


def _event_price(fields: dict[str, Any]) -> int:
    for key in (
        "curr_price",
        "canonical_mark_price",
        "executable_sell_price",
        "sell_price",
    ):
        value = _int(fields.get(key), 0)
        if value > 0:
            return value
    return 0


def _consume_event(trades: dict[str, Trade], row: dict[str, Any]) -> None:
    emitted = _timestamp(row.get("emitted_at"))
    record_id = str(row.get("record_id") or "").strip()
    if emitted is None or not record_id:
        return
    if record_id.endswith(".0"):
        record_id = record_id[:-2]
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    pipeline = str(row.get("pipeline") or "")
    stage = str(row.get("stage") or "")
    trade = trades.setdefault(record_id, Trade(record_id=record_id))
    trade.code = str(row.get("stock_code") or trade.code)
    trade.name = str(row.get("stock_name") or trade.name)
    if stage in VENUE_PROVENANCE_STAGES or pipeline == "VENUE_PROVENANCE":
        for key in ("effective_venue", "rising_missed_effective_venue", "venue"):
            venue = str(fields.get(key) or "").strip().upper()
            if venue in {"KRX", "NXT", "PREMARKET_KRX_LIKE", "OFF_SESSION"}:
                if not trade.venue:
                    trade.venue = venue
                elif trade.venue != venue:
                    trade.venue = "CONFLICT"
                break
    if _truthy(fields.get("actual_order_submitted")):
        trade.actual_submit_seen = True
    if pipeline != "HOLDING_PIPELINE":
        return
    if stage == "bundle_completed":
        trade.entry_terminal_at = emitted
    if stage == "holding_started":
        trade.avg_price = _float(fields.get("buy_price"), trade.avg_price)
        trade.qty = _int(fields.get("buy_qty"), trade.qty)
    if stage == "scale_in_executed":
        trade.avg_price = _float(fields.get("new_avg_price"), trade.avg_price)
        trade.qty = _int(fields.get("new_buy_qty"), trade.qty)
    price = _event_price(fields)
    if price > 0:
        trade.events.append(
            {
                "at": emitted,
                "stage": stage,
                "price": price,
                "avg_price": trade.avg_price,
                "qty": trade.qty,
                "add_type": str(fields.get("add_type") or "").upper(),
            }
        )
    if stage == "sell_completed":
        trade.completed_seen = True
        trade.exit_at = emitted
        trade.exit_price = _int(
            fields.get("position_weighted_sell_price"),
            _int(fields.get("sell_price"), price),
        )


def load_trades_duckdb(
    duckdb_path: Path, snapshot_at: datetime, events_dir: Path | None = None
) -> tuple[list[Trade], dict[str, int]]:
    trades: dict[str, Trade] = {}
    excluded = defaultdict(int)
    try:
        with DBManager().engine.connect() as sql_connection:
            completed_ids = {int(row[0]) for row in sql_connection.execute(text("""
                        SELECT id
                        FROM recommendation_history
                        WHERE UPPER(strategy) IN ('SCALPING', 'SCALP')
                          AND status = 'COMPLETED'
                          AND profit_rate IS NOT NULL
                          AND rec_date >= DATE '2026-06-04'
                        """)).fetchall()}
    except Exception:
        completed_ids = set()
    if not completed_ids:
        excluded["completed_real_id_source_missing"] += 1
        return [], dict(excluded)
    connection = duckdb.connect(str(duckdb_path), read_only=True)
    id_list = ",".join(str(item) for item in sorted(completed_ids))
    venue_query = f"""
        SELECT record_id,
               json_extract_string(fields_json, '$.effective_venue') AS effective_venue,
               json_extract_string(fields_json, '$.rising_missed_effective_venue') AS rising_venue,
               json_extract_string(fields_json, '$.venue') AS venue
        FROM v_pipeline_events
        WHERE emitted_at >= ? AND emitted_at <= ?
          AND CAST(record_id AS BIGINT) IN ({id_list})
          AND stage IN ('scalping_sizing_final_price_revalidated', 'entry_order_sent',
                        'holding_started', 'sell_order_sent', 'sell_completed')
          AND (fields_json LIKE '%effective_venue%' OR fields_json LIKE '%\"venue\"%')
    """
    stage_sql = ",".join(f"'{stage}'" for stage in sorted(RELEVANT_HOLDING_STAGES))
    query = f"""
        SELECT pipeline, stage, stock_name, stock_code, record_id, emitted_at, fields_json
        FROM v_pipeline_events
        WHERE emitted_at >= ? AND emitted_at <= ?
          AND CAST(record_id AS BIGINT) IN ({id_list})
          AND pipeline = 'HOLDING_PIPELINE'
          AND stage IN ({stage_sql})
        ORDER BY emitted_at
    """
    try:
        params = [
            CLEAN_BASELINE.replace(tzinfo=None).isoformat(),
            snapshot_at.replace(tzinfo=None).isoformat(),
        ]
        for record_id, effective_venue, rising_venue, venue in connection.execute(
            venue_query, params
        ).fetchall():
            if record_id is None:
                continue
            _consume_event(
                trades,
                {
                    "pipeline": "VENUE_PROVENANCE",
                    "stage": "venue_provenance",
                    "record_id": str(int(record_id)),
                    "emitted_at": CLEAN_BASELINE.isoformat(),
                    "fields": {
                        "effective_venue": effective_venue,
                        "rising_missed_effective_venue": rising_venue,
                        "venue": venue,
                    },
                },
            )
        cursor = connection.execute(
            query,
            params,
        )
        while True:
            batch = cursor.fetchmany(10_000)
            if not batch:
                break
            for (
                pipeline,
                stage,
                name,
                code,
                record_id,
                emitted_at,
                fields_json,
            ) in batch:
                if record_id is None:
                    continue
                try:
                    fields = json.loads(fields_json or "{}")
                except json.JSONDecodeError:
                    continue
                _consume_event(
                    trades,
                    {
                        "pipeline": pipeline,
                        "stage": stage,
                        "stock_name": name,
                        "stock_code": code,
                        "record_id": str(int(record_id)),
                        "emitted_at": emitted_at,
                        "fields": fields,
                    },
                )
    finally:
        connection.close()
    if events_dir is not None:
        current_raw = (
            events_dir / f"pipeline_events_{snapshot_at.date().isoformat()}.jsonl"
        )
        if current_raw.exists():
            _merge_current_raw_events(
                trades,
                current_raw,
                snapshot_at=snapshot_at,
                completed_ids=completed_ids,
            )
    return _filter_accepted_trades(trades, excluded)


def _merge_current_raw_events(
    trades: dict[str, Trade],
    path: Path,
    *,
    snapshot_at: datetime,
    completed_ids: set[int],
) -> None:
    """Merge deployment-day rows not yet present in the analytics snapshot."""
    with path.open("rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            if '"record_id":' not in raw_line:
                continue
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            record_id = _int(row.get("record_id"), 0)
            if record_id not in completed_ids:
                continue
            emitted = _timestamp(row.get("emitted_at"))
            if emitted is None or emitted < CLEAN_BASELINE or emitted > snapshot_at:
                continue
            pipeline = str(row.get("pipeline") or "")
            stage = str(row.get("stage") or "")
            fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
            relevant = (
                (pipeline == "HOLDING_PIPELINE" and stage in RELEVANT_HOLDING_STAGES)
                or stage in VENUE_PROVENANCE_STAGES
                or _truthy(fields.get("actual_order_submitted"))
            )
            if relevant:
                _consume_event(trades, row)


def _filter_accepted_trades(
    trades: dict[str, Trade], excluded: defaultdict[str, int]
) -> tuple[list[Trade], dict[str, int]]:
    accepted = []
    for trade in trades.values():
        if trade.venue != "KRX":
            excluded[f"venue_{trade.venue or 'missing'}"] += 1
            continue
        if not trade.entry_terminal_at or not (
            time(9, 0)
            <= trade.entry_terminal_at.timetz().replace(tzinfo=None)
            < time(15, 30)
        ):
            excluded["entry_not_krx_regular"] += 1
            continue
        if not trade.completed_seen or trade.exit_price <= 0:
            excluded["not_completed_valid_sell"] += 1
            continue
        if not trade.actual_submit_seen:
            excluded["real_submit_missing"] += 1
            continue
        if trade.avg_price <= 0 or trade.qty <= 0:
            excluded["position_terms_missing"] += 1
            continue
        accepted.append(trade)
    return accepted, dict(excluded)


def load_trades(
    events_dir: Path, snapshot_at: datetime
) -> tuple[list[Trade], dict[str, int]]:
    trades: dict[str, Trade] = {}
    excluded = defaultdict(int)
    for path in sorted(events_dir.glob("pipeline_events_*.jsonl*")):
        date_token = path.name.replace("pipeline_events_", "").split(".jsonl", 1)[0]
        try:
            file_date = datetime.fromisoformat(date_token).date()
        except ValueError:
            continue
        if file_date < CLEAN_BASELINE.date() or file_date > snapshot_at.date():
            continue
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
            for raw_line in handle:
                if (
                    '"pipeline":"HOLDING_PIPELINE"' not in raw_line
                    and "effective_venue" not in raw_line
                    and "rising_missed_effective_venue" not in raw_line
                ):
                    continue
                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                emitted = _timestamp(row.get("emitted_at"))
                if emitted is None or emitted < CLEAN_BASELINE or emitted > snapshot_at:
                    continue
                _consume_event(trades, row)
    return _filter_accepted_trades(trades, excluded)


def replay_candidate(
    trade: Trade,
    ratio: float,
    target_net: float,
    ttl_sec: int,
    *,
    observation_window_sec: float = OBSERVATION_WINDOW_SEC,
) -> dict[str, Any] | None:
    terminal = trade.entry_terminal_at
    if terminal is None:
        return None
    samples: list[tuple[datetime, int]] = []
    arm = None
    target = 0
    arm_avg = 0.0
    arm_qty = 0
    hit_at = None
    first_adverse_at = None
    observed_after_arm: list[tuple[datetime, int]] = []
    for event in sorted(trade.events, key=lambda item: item["at"]):
        at = event["at"]
        if at < terminal or at > trade.exit_at:
            continue
        if event["stage"] == "scale_in_executed":
            if hit_at is not None:
                return None
            samples.clear()
            arm = None
            target = 0
            observed_after_arm.clear()
            first_adverse_at = None
            continue
        price = int(event["price"])
        samples.append((at, price))
        samples = [
            item
            for item in samples
            if (at - item[0]).total_seconds() <= observation_window_sec
        ]
        if arm is None and len(samples) >= MIN_TICK_SAMPLES:
            span = (samples[-1][0] - samples[0][0]).total_seconds()
            low = min(value for _, value in samples)
            range_pct = ((max(value for _, value in samples) - low) / low) * 100.0
            avg_price = _float(event.get("avg_price"), trade.avg_price)
            qty = _int(event.get("qty"), trade.qty)
            if (
                span >= MIN_SPAN_SEC
                and range_pct >= MIN_RANGE_PCT
                and avg_price > 0
                and qty >= 2
            ):
                arm = at
                arm_avg = avg_price
                arm_qty = qty
                target = _target_price(avg_price, target_net)
        if arm is not None:
            observed_after_arm.append((at, price))
            if first_adverse_at is None and price < arm_avg:
                first_adverse_at = at
            if hit_at is None:
                if (at - arm).total_seconds() > ttl_sec:
                    break
                if price >= target:
                    hit_at = at
    if arm is None or hit_at is None:
        return None
    partial_qty = min(arm_qty - 1, max(1, int(math.floor(arm_qty * ratio))))
    runner_qty = arm_qty - partial_qty
    baseline_pnl = calculate_net_realized_pnl(arm_avg, trade.exit_price, arm_qty)
    candidate_pnl = calculate_net_realized_pnl(
        arm_avg, target, partial_qty
    ) + calculate_net_realized_pnl(arm_avg, trade.exit_price, runner_qty)
    post_hit_prices = [price for at, price in observed_after_arm if at >= hit_at]
    post_hit_mfe_price = max(post_hit_prices or [target])
    post_hit_mae_price = min(post_hit_prices or [target])
    target_first = first_adverse_at is None or hit_at <= first_adverse_at
    return {
        "record_id": trade.record_id,
        "code": trade.code,
        "name": trade.name,
        "arm_at": arm.isoformat(),
        "hit_at": hit_at.isoformat(),
        "first_adverse_at": (
            first_adverse_at.isoformat() if first_adverse_at is not None else None
        ),
        "first_hit_sequence": "target_first" if target_first else "adverse_then_target",
        "avg_price": round(arm_avg, 4),
        "qty": arm_qty,
        "partial_qty": partial_qty,
        "runner_qty": runner_qty,
        "target_price": target,
        "exit_price": trade.exit_price,
        "baseline_pnl_krw": baseline_pnl,
        "candidate_pnl_krw": candidate_pnl,
        "delta_net_profit_krw": candidate_pnl - baseline_pnl,
        "post_hit_mfe_price": post_hit_mfe_price,
        "post_hit_mae_price": post_hit_mae_price,
        "foregone_additional_mfe_krw": max(
            0, (post_hit_mfe_price - target) * partial_qty
        ),
        "avoided_post_hit_mae_krw": max(0, (target - post_hit_mae_price) * partial_qty),
        "notional_krw": int(round(arm_avg * arm_qty)),
    }


def load_operator_bootstrap_trades(
    events_dir: Path, snapshot_at: datetime
) -> tuple[list[Trade], dict[str, int]]:
    """Load only the two explicitly authorized 2026-07-23 bootstrap trades."""
    excluded = defaultdict(int)
    try:
        with DBManager().engine.connect() as connection:
            rows = connection.execute(text("""
                    SELECT id, stock_code
                    FROM recommendation_history
                    WHERE rec_date = DATE '2026-07-23'
                      AND stock_code IN ('117730', '459510')
                      AND UPPER(strategy) IN ('SCALPING', 'SCALP')
                      AND status = 'COMPLETED'
                      AND profit_rate IS NOT NULL
                    """)).fetchall()
    except Exception:
        rows = []
    id_to_code = {int(row[0]): str(row[1]) for row in rows}
    if set(id_to_code.values()) != set(OPERATOR_BOOTSTRAP_CODES):
        excluded["operator_bootstrap_completed_real_pair_missing"] += 1
        return [], dict(excluded)
    path = events_dir / "pipeline_events_2026-07-23.jsonl"
    if not path.exists():
        excluded["operator_bootstrap_raw_file_missing"] += 1
        return [], dict(excluded)
    trades: dict[str, Trade] = {}
    with path.open("rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            if '"record_id":' not in raw_line:
                continue
            try:
                row = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            record_id = _int(row.get("record_id"), 0)
            if record_id not in id_to_code:
                continue
            emitted = _timestamp(row.get("emitted_at"))
            if emitted is None or emitted > snapshot_at:
                continue
            pipeline = str(row.get("pipeline") or "")
            stage = str(row.get("stage") or "")
            fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
            if (
                (pipeline == "HOLDING_PIPELINE" and stage in RELEVANT_HOLDING_STAGES)
                or stage in VENUE_PROVENANCE_STAGES
                or _truthy(fields.get("actual_order_submitted"))
            ):
                _consume_event(trades, row)
    accepted = []
    for record_id, expected_code in id_to_code.items():
        trade = trades.get(str(record_id))
        if trade is None or trade.code != expected_code:
            excluded[f"operator_bootstrap_{expected_code}_events_missing"] += 1
            continue
        if trade.venue != "PREMARKET_KRX_LIKE":
            excluded[f"operator_bootstrap_{expected_code}_venue_invalid"] += 1
            continue
        if (
            not trade.entry_terminal_at
            or not trade.completed_seen
            or trade.exit_price <= 0
            or not trade.actual_submit_seen
            or trade.avg_price <= 0
            or trade.qty <= 0
        ):
            excluded[f"operator_bootstrap_{expected_code}_contract_incomplete"] += 1
            continue
        accepted.append(trade)
    return accepted, dict(excluded)


def _evaluate_grid(
    trades: list[Trade], *, observation_window_sec: float
) -> list[dict[str, Any]]:
    candidates = []
    for ratio in PARTIAL_RATIOS:
        for target_net in TARGET_NET_PCTS:
            for ttl in TTL_SECS:
                hits = [
                    result
                    for trade in trades
                    if (
                        result := replay_candidate(
                            trade,
                            ratio,
                            target_net,
                            ttl,
                            observation_window_sec=observation_window_sec,
                        )
                    )
                ]
                delta = sum(item["delta_net_profit_krw"] for item in hits)
                baseline_net_profit = sum(item["baseline_pnl_krw"] for item in hits)
                candidate_net_profit = sum(item["candidate_pnl_krw"] for item in hits)
                notional = sum(item["notional_krw"] for item in hits)
                ev_delta = (delta / notional * 100.0) if notional > 0 else 0.0
                candidate_ev = (
                    candidate_net_profit / notional * 100.0 if notional > 0 else 0.0
                )
                candidates.append(
                    {
                        "partial_ratio": ratio,
                        "target_net_profit_pct": target_net,
                        "ttl_sec": ttl,
                        "observation_window_sec": observation_window_sec,
                        "valid_first_hit_count": len(hits),
                        "target_first_count": sum(
                            item["first_hit_sequence"] == "target_first"
                            for item in hits
                        ),
                        "adverse_then_target_count": sum(
                            item["first_hit_sequence"] == "adverse_then_target"
                            for item in hits
                        ),
                        "baseline_net_profit_krw": baseline_net_profit,
                        "candidate_net_profit_krw": candidate_net_profit,
                        "delta_net_profit_krw": delta,
                        "notional_weighted_ev_pct": round(candidate_ev, 8),
                        "notional_weighted_ev_delta_pct": round(ev_delta, 8),
                        "foregone_additional_mfe_krw": sum(
                            item["foregone_additional_mfe_krw"] for item in hits
                        ),
                        "avoided_post_hit_mae_krw": sum(
                            item["avoided_post_hit_mae_krw"] for item in hits
                        ),
                        "hits": hits,
                    }
                )
    return sorted(
        candidates,
        key=lambda item: (
            item["delta_net_profit_krw"],
            -item["partial_ratio"],
            item["target_net_profit_pct"],
            item["ttl_sec"],
        ),
        reverse=True,
    )


def build_report(
    events_dir: Path, snapshot_at: datetime, *, duckdb_path: Path | None = None
) -> dict[str, Any]:
    if duckdb_path is not None and duckdb_path.exists():
        trades, excluded = load_trades_duckdb(
            duckdb_path, snapshot_at, events_dir=events_dir
        )
        source_kind = "analytics_duckdb_plus_current_raw_pipeline_events"
    else:
        trades, excluded = load_trades(events_dir, snapshot_at)
        source_kind = "raw_pipeline_jsonl"
    ranked = _evaluate_grid(trades, observation_window_sec=OBSERVATION_WINDOW_SEC)
    regular_selected = ranked[0] if ranked else None
    bootstrap_trades: list[Trade] = []
    bootstrap_excluded: dict[str, int] = {}
    bootstrap_ranked: list[dict[str, Any]] = []
    selection_basis = "clean_baseline_explicit_krx_regular"
    selected = regular_selected
    if not regular_selected or regular_selected["valid_first_hit_count"] <= 0:
        bootstrap_trades, bootstrap_excluded = load_operator_bootstrap_trades(
            events_dir, snapshot_at
        )
        bootstrap_ranked = _evaluate_grid(
            bootstrap_trades,
            observation_window_sec=BOOTSTRAP_OBSERVATION_WINDOW_SEC,
        )
        bootstrap_selected = bootstrap_ranked[0] if bootstrap_ranked else None
        if bootstrap_selected and bootstrap_selected["valid_first_hit_count"] > 0:
            selected = bootstrap_selected
            selection_basis = "operator_directed_named_trade_bootstrap"
    qualified = bool(
        selected
        and selected["valid_first_hit_count"] > 0
        and selected["delta_net_profit_krw"] > 0
        and selected["notional_weighted_ev_delta_pct"] >= 0
    )
    return {
        "schema_version": 1,
        "policy_version": POLICY_VERSION,
        "generated_at": datetime.now(KST).isoformat(),
        "snapshot_at": snapshot_at.isoformat(),
        "source_kind": source_kind,
        "clean_baseline_ts_kst": CLEAN_BASELINE.isoformat(),
        "effective_venue": "KRX",
        "market_session": "KRX_REGULAR",
        "selection_basis": selection_basis,
        "operator_bootstrap": {
            "enabled_only_when_regular_first_hit_zero": True,
            "source_venue": "PREMARKET_KRX_LIKE",
            "target_runtime_venue": "KRX",
            "explicit_user_authority": True,
            "stock_codes": list(OPERATOR_BOOTSTRAP_CODES),
            "eligible_trade_count": len(bootstrap_trades),
            "excluded_counts": bootstrap_excluded,
            "observation_window_sec": BOOTSTRAP_OBSERVATION_WINDOW_SEC,
            "forbidden_uses": "nxt_apply|general_krx_ev_pool_merge|hard_safety_relaxation",
        },
        "decision": (
            "implemented_historical_real_validation_pass"
            if qualified
            else (
                "implemented_insufficient_history_keep_guarded"
                if not selected or selected["valid_first_hit_count"] <= 0
                else "implemented_needs_supplement"
            )
        ),
        "qualified_for_runtime": qualified,
        "eligible_trade_count": len(trades),
        "excluded_counts": excluded,
        "grid": {
            "partial_ratios": list(PARTIAL_RATIOS),
            "target_net_profit_pcts": list(TARGET_NET_PCTS),
            "ttl_secs": list(TTL_SECS),
            "min_range_pct": MIN_RANGE_PCT,
            "min_tick_samples": MIN_TICK_SAMPLES,
            "min_observation_span_sec": MIN_SPAN_SEC,
            "regular_observation_window_sec": OBSERVATION_WINDOW_SEC,
            "operator_bootstrap_observation_window_sec": BOOTSTRAP_OBSERVATION_WINDOW_SEC,
        },
        "selected": selected,
        "candidates": (
            bootstrap_ranked
            if selection_basis == "operator_directed_named_trade_bootstrap"
            else ranked
        ),
        "regular_candidates": ranked,
        "operator_bootstrap_candidates": bootstrap_ranked,
    }


def write_artifacts(report: dict[str, Any], target_date: str) -> tuple[Path, Path]:
    report_dir = Path(DATA_DIR) / "report" / "early_volatility_partial_tp_replay"
    policy_dir = Path(DATA_DIR) / "threshold_cycle" / "runtime_policy"
    report_dir.mkdir(parents=True, exist_ok=True)
    policy_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"early_volatility_partial_tp_replay_{target_date}.json"
    policy_path = policy_dir / f"early_volatility_partial_tp_policy_{target_date}.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    selected = report.get("selected") or {}
    policy = {
        "schema_version": 1,
        "policy_version": POLICY_VERSION,
        "decision": report.get("decision"),
        "qualified_for_runtime": bool(report.get("qualified_for_runtime")),
        "effective_venue": "KRX",
        "market_session": "KRX_REGULAR",
        "selection_basis": report.get("selection_basis"),
        "operator_bootstrap": report.get("operator_bootstrap"),
        "source_report": str(report_path),
        "snapshot_at": report.get("snapshot_at"),
        "partial_ratio": selected.get("partial_ratio"),
        "target_net_profit_pct": selected.get("target_net_profit_pct"),
        "ttl_sec": selected.get("ttl_sec"),
        "min_range_pct": MIN_RANGE_PCT,
        "min_tick_samples": MIN_TICK_SAMPLES,
        "min_observation_span_sec": MIN_SPAN_SEC,
        "observation_window_sec": selected.get(
            "observation_window_sec", OBSERVATION_WINDOW_SEC
        ),
        "valid_first_hit_count": selected.get("valid_first_hit_count", 0),
        "delta_net_profit_krw": selected.get("delta_net_profit_krw", 0),
        "notional_weighted_ev_delta_pct": selected.get(
            "notional_weighted_ev_delta_pct", 0.0
        ),
    }
    policy_path.write_text(
        json.dumps(policy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report_path, policy_path


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--snapshot-at")
    parser.add_argument("--events-dir", default=str(Path(DATA_DIR) / "pipeline_events"))
    parser.add_argument(
        "--duckdb-path",
        default=str(
            Path(DATA_DIR) / "analytics" / "duckdb" / "korstockscan_analytics.duckdb"
        ),
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    snapshot_at = (
        _timestamp(args.snapshot_at) if args.snapshot_at else datetime.now(KST)
    )
    if snapshot_at is None:
        raise SystemExit("invalid --snapshot-at")
    report = build_report(
        Path(args.events_dir), snapshot_at, duckdb_path=Path(args.duckdb_path)
    )
    output = {"report": report}
    if args.write:
        report_path, policy_path = write_artifacts(report, args.target_date)
        output.update(
            {"report_path": str(report_path), "policy_path": str(policy_path)}
        )
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if report.get("qualified_for_runtime") else 2


if __name__ == "__main__":
    raise SystemExit(main())
