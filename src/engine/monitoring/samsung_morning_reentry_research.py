"""Source-only research for one additional Samsung morning SOR episode.

The producer consumes the existing clean-baseline Kiwoom minute backfill.  It
reconstructs the current NXT-first/SOR-fallback episode before looking for one
post-completion SOR episode.  It cannot call a broker, mutate policy, or grant
runtime authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.engine.monitoring.pure_market_reversal_replay import (
    Bar,
    KST,
    assess_date_coverage,
    load_market_bars,
)
from src.trading.order.tick_utils import clamp_price_to_tick, move_price_by_ticks
from src.utils.constants import DATA_DIR

REPORT_SCHEMA = "samsung_morning_reentry_research_v1"
INPUT_PATH = (
    DATA_DIR
    / "market_data"
    / "pure_market_reversal"
    / "samsung_1m_krx-nxt_2026-06-05_2026-08-10.jsonl"
)
MANIFEST_PATH = INPUT_PATH.with_suffix(".manifest.json")
OUTPUT_DIR = DATA_DIR / "report" / "samsung_morning_reentry_research"
CLEAN_START = date(2026, 6, 5)
END_DATE = date(2026, 8, 10)
HOLDOUT_DAYS = 16
COST_PCT = 0.20
LOOKBACK_GRID = (3, 5, 10, 15)
DRAWDOWN_GRID = (0.10, 0.20, 0.30, 0.50, 0.75, 1.00, 1.25)
NEAR_LOW_GRID = (0.05, 0.10, 0.20, 0.35, 0.50)
SCAN_END_GRID = (555, 570, 585, 600)  # 09:15 through 10:00
ENTRY_VALID_GRID = (3, 5, 10)
ENTRY_OFFSET_GRID = (0, -1, -2)

METRIC_CONTRACT = {
    "metric_role": "samsung_morning_second_episode_offline_research",
    "decision_authority": "source_only_no_runtime_or_order_authority",
    "window_policy": (
        "first_28_common_dates_per_family_calibration_then_last_16_holdout;"
        "sequential_family_iteration_disclosed"
    ),
    "sample_floor": {
        "calibration_signal_episodes": 6,
        "calibration_completed_legs": 8,
        "each_calibration_half_completed_legs": 3,
        "holdout_signal_episodes": 3,
        "holdout_completed_legs": 4,
        "calibration_and_holdout_held_legs": 0,
    },
    "primary_decision_metric": "notional_weighted_ev_pct",
    "source_quality_gate": [
        "clean_baseline_manifest_pass_and_sha256_match",
        "valid_unique_completed_krx_and_nxt_ohlcv",
        "44_common_dates_with_nxt_0800_and_krx_0900_anchors",
        "current_first_episode_completed_before_reentry",
        "same_bar_fill_then_target_forbidden",
        "calibration_and_holdout_held_legs_zero",
    ],
    "forbidden_uses": [
        "holdout_outcome_used_for_candidate_selection",
        "price_touch_as_real_fill_evidence",
        "same_bar_fill_then_target_assumption",
        "real_order_submission",
        "account_token_or_broker_api",
        "runtime_policy_or_quantity_mutation",
        "provider_bot_cap_or_broker_guard_change",
        "stop_loss_forced_exit_or_target_timeout_creation",
    ],
}


class ResearchError(RuntimeError):
    """Raised when a source or research contract fails closed."""


@dataclass(frozen=True)
class Candidate:
    family: str
    lookback_bars: int
    drawdown_pct: float
    near_low_pct: float
    scan_end_minute: int
    entry_valid_completed_bars: int
    entry_offset_ticks: int
    confirmation_bars: int = 0
    reclaim_ticks: int = 0
    entry_anchor: str = "signal_close"

    def public(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "lookback_bars": self.lookback_bars,
            "rolling_high_drawdown_pct": self.drawdown_pct,
            "rolling_low_proximity_pct": self.near_low_pct,
            "scan_end": _minute_text(self.scan_end_minute),
            "entry_valid_completed_bars": self.entry_valid_completed_bars,
            "entry_offset_ticks": self.entry_offset_ticks,
            "confirmation_bars": self.confirmation_bars,
            "reclaim_ticks": self.reclaim_ticks,
            "confirmation_low_hold_required": self.confirmation_bars > 0,
            "entry_anchor": self.entry_anchor,
        }


@dataclass(frozen=True)
class SignalFeature:
    index: int
    timestamp: datetime
    close_price: int
    drawdown_pct: float
    near_low_pct: float


@dataclass(frozen=True)
class ResolvedSignal:
    setup: SignalFeature
    entry_index: int
    entry_timestamp: datetime
    entry_anchor_price: int


@dataclass
class DayContext:
    trade_date: date
    krx_bars: tuple[Bar, ...]
    first_episode: dict[str, Any]
    features: dict[int, tuple[SignalFeature, ...]]
    outcome_cache: dict[tuple[int, int, int, int], dict[str, Any]] = field(
        default_factory=dict
    )


def _minute_value(timestamp: datetime) -> int:
    return timestamp.hour * 60 + timestamp.minute


def _minute_text(value: int) -> str:
    return f"{value // 60:02d}:{value % 60:02d}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(
    input_path: Path = INPUT_PATH, manifest_path: Path = MANIFEST_PATH
) -> dict[str, Any]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchError(f"manifest_unreadable:{type(exc).__name__}") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != "pure_market_minute_backfill_manifest_v1"
        or manifest.get("source_quality_status") != "PASS"
        or manifest.get("start_date") != CLEAN_START.isoformat()
        or manifest.get("end_date") != END_DATE.isoformat()
        or manifest.get("symbol") != "005930"
    ):
        raise ResearchError("manifest_contract_invalid")
    try:
        digest = _sha256(input_path)
    except OSError as exc:
        raise ResearchError(f"market_data_unreadable:{type(exc).__name__}") from exc
    if digest != manifest.get("data_sha256"):
        raise ResearchError("market_data_sha256_mismatch")
    bars, quality = load_market_bars(
        market_paths=(input_path,),
        widget_observation_dir=None,
        start_date=CLEAN_START,
        end_date=END_DATE,
    )
    if quality.get("status") != "PASS":
        raise ResearchError("market_data_source_quality_not_pass")
    coverage = assess_date_coverage(bars)
    qualified = coverage.get("qualified_dates_by_venue", {})
    if any(len(qualified.get(venue, [])) != 46 for venue in ("KRX", "NXT")):
        raise ResearchError("market_data_session_coverage_not_pass")
    return {
        "manifest": manifest,
        "quality": quality,
        "coverage": coverage,
        "bars": bars,
    }


def _bars_between(
    bars: Sequence[Bar], start_minute: int, end_minute: int
) -> tuple[Bar, ...]:
    return tuple(
        bar for bar in bars if start_minute <= _minute_value(bar.timestamp) < end_minute
    )


def _leg_outcome(
    *,
    entry_price: int,
    fill_bars: Sequence[Bar],
    target_bars: Sequence[Bar],
) -> dict[str, Any]:
    fill = next((bar for bar in fill_bars if bar.low <= entry_price), None)
    if fill is None:
        return {"status": "NO_FILL", "entry_price": entry_price}
    target_price = move_price_by_ticks(entry_price, 2)
    target = next(
        (
            bar
            for bar in target_bars
            if bar.timestamp > fill.timestamp and bar.high >= target_price
        ),
        None,
    )
    result = {
        "status": "COMPLETE" if target is not None else "HELD",
        "entry_price": entry_price,
        "target_price": target_price,
        "fill_at": fill.timestamp.isoformat(),
        "target_at": target.timestamp.isoformat() if target else None,
    }
    if target is not None:
        result["net_profit_pct"] = round(
            (target_price / entry_price - 1.0) * 100.0 - COST_PCT, 6
        )
    return result


def _opening_entries(open_price: int, drawdown_pct: float) -> tuple[int, int]:
    base = clamp_price_to_tick(open_price * (1.0 - drawdown_pct / 100.0))
    return move_price_by_ticks(base, 1), base


def reconstruct_first_episode(
    nxt_bars: Sequence[Bar], krx_bars: Sequence[Bar]
) -> dict[str, Any]:
    nxt_entry = _bars_between(nxt_bars, 480, 490)
    nxt_target = _bars_between(nxt_bars, 480, 530)
    krx_entry = _bars_between(krx_bars, 540, 570)
    krx_target = _bars_between(krx_bars, 540, 931)
    if not nxt_entry or _minute_value(nxt_entry[0].timestamp) != 480:
        return {"status": "SOURCE_GAP", "reason": "nxt_0800_anchor_missing"}
    if not krx_entry or _minute_value(krx_entry[0].timestamp) != 540:
        return {"status": "SOURCE_GAP", "reason": "krx_0900_anchor_missing"}
    nxt_entries = _opening_entries(nxt_entry[0].open, 3.0)
    sor_entries = _opening_entries(krx_entry[0].open, 0.75)
    legs: list[dict[str, Any]] = []
    for leg_id, nxt_price, sor_price in zip(
        ("base_plus_1tick", "base"), nxt_entries, sor_entries
    ):
        nxt = _leg_outcome(
            entry_price=nxt_price,
            fill_bars=nxt_entry,
            target_bars=nxt_target,
        )
        if nxt["status"] == "NO_FILL":
            sor = _leg_outcome(
                entry_price=sor_price,
                fill_bars=krx_entry,
                target_bars=krx_target,
            )
            legs.append({"leg_id": leg_id, "route": "SOR", **sor})
        else:
            legs.append({"leg_id": leg_id, "route": "NXT", **nxt})
    completed = all(leg["status"] == "COMPLETE" for leg in legs)
    completed_at = (
        max(datetime.fromisoformat(str(leg["target_at"])) for leg in legs)
        if completed
        else None
    )
    return {
        "status": "COMPLETE" if completed else "INCOMPLETE",
        "completed_at": completed_at.isoformat() if completed_at else None,
        "nxt_open": nxt_entry[0].open,
        "sor_open": krx_entry[0].open,
        "legs": legs,
    }


def build_contexts(bars: Iterable[Bar]) -> dict[date, DayContext]:
    grouped: dict[tuple[date, str, str], list[Bar]] = {}
    for bar in bars:
        grouped.setdefault((bar.trade_date, bar.venue, bar.session), []).append(bar)
    contexts: dict[date, DayContext] = {}
    all_dates = sorted({key[0] for key in grouped})
    for trade_date in all_dates:
        nxt = tuple(
            sorted(
                grouped.get((trade_date, "NXT", "NXT_PREMARKET"), []),
                key=lambda item: item.timestamp,
            )
        )
        krx = tuple(
            sorted(
                grouped.get((trade_date, "KRX", "KRX_REGULAR"), []),
                key=lambda item: item.timestamp,
            )
        )
        first = reconstruct_first_episode(nxt, krx)
        if first.get("status") == "SOURCE_GAP":
            continue
        if first.get("status") != "COMPLETE":
            post = ()
        else:
            completed_at = datetime.fromisoformat(str(first["completed_at"]))
            post = tuple(bar for bar in krx if bar.timestamp > completed_at)
        features: dict[int, tuple[SignalFeature, ...]] = {}
        for lookback in LOOKBACK_GRID:
            rows: list[SignalFeature] = []
            for index in range(lookback - 1, len(post)):
                window = post[index - lookback + 1 : index + 1]
                if any(
                    current.timestamp - previous.timestamp != timedelta(minutes=1)
                    for previous, current in zip(window, window[1:])
                ):
                    continue
                rolling_high = max(bar.high for bar in window)
                rolling_low = min(bar.low for bar in window)
                close = post[index].close
                if min(rolling_high, rolling_low, close) <= 0:
                    continue
                rows.append(
                    SignalFeature(
                        index=krx.index(post[index]),
                        timestamp=post[index].timestamp,
                        close_price=close,
                        drawdown_pct=(rolling_high - close) / rolling_high * 100.0,
                        near_low_pct=(close - rolling_low) / rolling_low * 100.0,
                    )
                )
            features[lookback] = tuple(rows)
        contexts[trade_date] = DayContext(trade_date, krx, first, features)
    return contexts


def candidate_grid() -> tuple[Candidate, ...]:
    direct = tuple(
        Candidate(
            "direct_low_proximity",
            lookback,
            drawdown,
            near_low,
            scan_end,
            valid,
            offset,
        )
        for lookback in LOOKBACK_GRID
        for drawdown in DRAWDOWN_GRID
        for near_low in NEAR_LOW_GRID
        for scan_end in SCAN_END_GRID
        for valid in ENTRY_VALID_GRID
        for offset in ENTRY_OFFSET_GRID
    )
    confirmed = tuple(
        Candidate(
            (
                "low_hold_reclaim_close_split"
                if offset == 0
                else "low_hold_reclaim_passive_split"
            ),
            lookback,
            drawdown,
            near_low,
            scan_end,
            valid,
            offset,
            confirmation_bars,
            reclaim_ticks,
            entry_anchor,
        )
        for lookback in LOOKBACK_GRID
        for drawdown in DRAWDOWN_GRID
        for near_low in NEAR_LOW_GRID
        for scan_end in SCAN_END_GRID
        for valid in ENTRY_VALID_GRID
        for offset in (0, -1)
        for confirmation_bars in (1, 2)
        for reclaim_ticks in (1, 2)
        for entry_anchor in ("confirmation_close", "trough_close")
    )
    return direct + confirmed


def _resolve_signal(context: DayContext, candidate: Candidate) -> ResolvedSignal | None:
    for setup in context.features[candidate.lookback_bars]:
        if _minute_value(setup.timestamp) > candidate.scan_end_minute:
            break
        if (
            setup.drawdown_pct + 1e-12 < candidate.drawdown_pct
            or setup.near_low_pct - 1e-12 > candidate.near_low_pct
        ):
            continue
        if candidate.family == "direct_low_proximity":
            return ResolvedSignal(
                setup,
                setup.index,
                setup.timestamp,
                setup.close_price,
            )
        if candidate.family not in {
            "low_hold_reclaim_close_split",
            "low_hold_reclaim_passive_split",
        }:
            raise ValueError("unknown_candidate_family")
        confirmation_index = setup.index + candidate.confirmation_bars
        if confirmation_index >= len(context.krx_bars):
            continue
        confirmation = context.krx_bars[confirmation_index]
        if _minute_value(confirmation.timestamp) > candidate.scan_end_minute:
            continue
        sequence = context.krx_bars[setup.index : confirmation_index + 1]
        if any(
            current.timestamp - previous.timestamp != timedelta(minutes=1)
            for previous, current in zip(sequence, sequence[1:])
        ):
            continue
        setup_bar = context.krx_bars[setup.index]
        if min(bar.low for bar in sequence) < setup_bar.low:
            continue
        if confirmation.close < move_price_by_ticks(
            setup.close_price, candidate.reclaim_ticks
        ):
            continue
        anchor = (
            confirmation.close
            if candidate.entry_anchor == "confirmation_close"
            else setup.close_price
        )
        return ResolvedSignal(
            setup,
            confirmation_index,
            confirmation.timestamp,
            anchor,
        )
    return None


def _episode(
    context: DayContext, signal: ResolvedSignal, candidate: Candidate
) -> dict[str, Any]:
    key = (
        signal.entry_index,
        candidate.entry_valid_completed_bars,
        candidate.entry_offset_ticks,
        int(signal.entry_anchor_price),
    )
    cached = context.outcome_cache.get(key)
    if cached is not None:
        return cached
    anchor = move_price_by_ticks(
        clamp_price_to_tick(signal.entry_anchor_price), candidate.entry_offset_ticks
    )
    entries = (anchor, move_price_by_ticks(anchor, -1))
    fill_bars = context.krx_bars[
        signal.entry_index
        + 1 : signal.entry_index
        + 1
        + candidate.entry_valid_completed_bars
    ]
    target_bars = context.krx_bars[signal.entry_index + 1 :]
    result = {
        "date": context.trade_date.isoformat(),
        "setup_at": signal.setup.timestamp.isoformat(),
        "signal_at": signal.entry_timestamp.isoformat(),
        "setup_close": signal.setup.close_price,
        "entry_anchor_price": signal.entry_anchor_price,
        "observed_drawdown_pct": round(signal.setup.drawdown_pct, 6),
        "observed_near_low_pct": round(signal.setup.near_low_pct, 6),
        "first_episode_completed_at": context.first_episode["completed_at"],
        "legs": [
            _leg_outcome(
                entry_price=entry_price,
                fill_bars=fill_bars,
                target_bars=target_bars,
            )
            for entry_price in entries
        ],
    }
    context.outcome_cache[key] = result
    return result


def evaluate_candidate(
    candidate: Candidate,
    contexts: dict[date, DayContext],
    dates: Sequence[date],
    *,
    include_episodes: bool = False,
) -> dict[str, Any]:
    episodes: list[dict[str, Any]] = []
    for trade_date in dates:
        context = contexts[trade_date]
        signal = _resolve_signal(context, candidate)
        if signal is not None:
            episodes.append(_episode(context, signal, candidate))
    legs = [leg for episode in episodes for leg in episode["legs"]]
    completed = [leg for leg in legs if leg["status"] == "COMPLETE"]
    attempted_notional = sum(int(leg["entry_price"]) for leg in legs)
    realized_profit = sum(
        int(leg["entry_price"]) * float(leg["net_profit_pct"]) / 100.0
        for leg in completed
    )
    ev = realized_profit / attempted_notional * 100.0 if attempted_notional else None
    result = {
        "signal_episodes": len(episodes),
        "attempted_legs": len(legs),
        "completed_legs": len(completed),
        "no_fill_legs": sum(leg["status"] == "NO_FILL" for leg in legs),
        "held_legs": sum(leg["status"] == "HELD" for leg in legs),
        "notional_weighted_ev_pct": round(ev, 6) if ev is not None else None,
    }
    if include_episodes:
        result["episodes"] = episodes
    return result


def _positive_ev(summary: dict[str, Any]) -> bool:
    value = summary.get("notional_weighted_ev_pct")
    return value is not None and float(value) > 0.0


def _calibration_ready(
    full: dict[str, Any], first: dict[str, Any], second: dict[str, Any]
) -> bool:
    return bool(
        full["signal_episodes"] >= 6
        and full["completed_legs"] >= 8
        and first["completed_legs"] >= 3
        and second["completed_legs"] >= 3
        and full["held_legs"] == first["held_legs"] == second["held_legs"] == 0
        and _positive_ev(first)
        and _positive_ev(second)
    )


def _robust_score(first: dict[str, Any], second: dict[str, Any]) -> float:
    values = []
    for summary in (first, second):
        completed = int(summary["completed_legs"])
        ev = float(summary["notional_weighted_ev_pct"])
        values.append(ev * completed / (completed + 6.0))
    return min(values)


def select_candidate(contexts: dict[date, DayContext]) -> dict[str, Any]:
    dates = sorted(contexts)
    if len(dates) != 44:
        raise ResearchError(f"expected_44_common_dates_found_{len(dates)}")
    calibration = dates[:-HOLDOUT_DAYS]
    holdout = dates[-HOLDOUT_DAYS:]
    first_half = calibration[: len(calibration) // 2]
    second_half = calibration[len(calibration) // 2 :]
    family_order = (
        "direct_low_proximity",
        "low_hold_reclaim_close_split",
        "low_hold_reclaim_passive_split",
    )
    ranked_by_family: dict[
        str, list[tuple[float, float, int, Candidate, dict[str, Any]]]
    ] = {family: [] for family in family_order}
    gate_counts = {
        family: {"sample_ready": 0, "inventory_clear": 0} for family in family_order
    }
    for candidate in candidate_grid():
        first = evaluate_candidate(candidate, contexts, first_half)
        second = evaluate_candidate(candidate, contexts, second_half)
        full = evaluate_candidate(candidate, contexts, calibration)
        if full["signal_episodes"] >= 6 and full["completed_legs"] >= 8:
            gate_counts[candidate.family]["sample_ready"] += 1
            if full["held_legs"] == 0:
                gate_counts[candidate.family]["inventory_clear"] += 1
        if not _calibration_ready(full, first, second):
            continue
        ranked_by_family[candidate.family].append(
            (
                _robust_score(first, second),
                float(full["notional_weighted_ev_pct"]),
                int(full["completed_legs"]),
                candidate,
                {"first_half": first, "second_half": second, "full": full},
            )
        )
    for ranked in ranked_by_family.values():
        ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    split = {
        "calibration_start": calibration[0].isoformat(),
        "calibration_end": calibration[-1].isoformat(),
        "holdout_start": holdout[0].isoformat(),
        "holdout_end": holdout[-1].isoformat(),
        "calibration_trading_day_count": len(calibration),
        "holdout_trading_day_count": len(holdout),
    }
    if not any(ranked_by_family.values()):
        return {
            "date_split": split,
            "grid_candidate_count": len(candidate_grid()),
            "calibration_ready_candidate_count": 0,
            "calibration_gate_counts": gate_counts,
            "family_results": {},
            "candidate": None,
            "decision": "no_robust_calibration_candidate",
            "recommended_action": "do_not_change_live_machine",
        }
    family_results: dict[str, dict[str, Any]] = {}
    selected: dict[str, Any] | None = None
    for family in family_order:
        ranked = ranked_by_family[family]
        if not ranked:
            family_results[family] = {
                "candidate": None,
                "decision": "no_robust_calibration_candidate",
            }
            continue
        score, _, _, winner, evidence = ranked[0]
        holdout_result = evaluate_candidate(winner, contexts, holdout)
        full_result = evaluate_candidate(winner, contexts, dates, include_episodes=True)
        holdout_ready = bool(
            holdout_result["signal_episodes"] >= 3
            and holdout_result["completed_legs"] >= 4
            and holdout_result["held_legs"] == 0
            and full_result["held_legs"] == 0
            and _positive_ev(holdout_result)
        )
        result = {
            "calibration_ready_candidate_count": len(ranked),
            "candidate": {
                "parameters": winner.public(),
                "robust_calibration_score": round(score, 6),
                "calibration_first_half": evidence["first_half"],
                "calibration_second_half": evidence["second_half"],
                "calibration": evidence["full"],
                "holdout": holdout_result,
                "full": full_result,
            },
            "decision": (
                "holdout_pass_source_only_reentry_candidate"
                if holdout_ready
                else "holdout_failed_do_not_change_live_machine"
            ),
        }
        family_results[family] = result
        if selected is None and holdout_ready:
            selected = result["candidate"]
    return {
        "date_split": split,
        "grid_candidate_count": len(candidate_grid()),
        "calibration_ready_candidate_count": sum(
            len(items) for items in ranked_by_family.values()
        ),
        "calibration_gate_counts": gate_counts,
        "family_results": family_results,
        "family_iteration_count": len(family_order),
        "holdout_reuse_warning": (
            "holdout_is_not_single-family-untouched_after_sequential_family_iteration"
        ),
        "candidate": selected,
        "decision": (
            "holdout_pass_source_only_reentry_candidate"
            if selected is not None
            else "holdout_failed_do_not_change_live_machine"
        ),
        "recommended_action": (
            "separate_user_review_required_before_live_implementation"
            if selected is not None
            else "retain_single_episode_live_machine"
        ),
    }


def build_report(
    *, input_path: Path = INPUT_PATH, manifest_path: Path = MANIFEST_PATH
) -> dict[str, Any]:
    source = validate_source(input_path, manifest_path)
    contexts = build_contexts(source.pop("bars"))
    selection = select_candidate(contexts)
    first_complete_count = sum(
        context.first_episode["status"] == "COMPLETE" for context in contexts.values()
    )
    return {
        "schema": REPORT_SCHEMA,
        "generated_at_kst": datetime.now(tz=KST).isoformat(timespec="seconds"),
        "start_date": CLEAN_START.isoformat(),
        "end_date": END_DATE.isoformat(),
        "cost_pct": COST_PCT,
        "execution_contract": {
            "maximum_additional_episodes_per_day": 1,
            "quantity": 2,
            "allocation": (
                "one_share_entry_anchor_plus_offset_and_one_share_one_tick_lower"
            ),
            "target_ticks": 2,
            "stop_loss": "none",
            "unfilled_target": "hold_without_forced_exit",
        },
        "metric_contract": METRIC_CONTRACT,
        "source": source,
        "first_episode_reconstruction": {
            "common_date_count": len(contexts),
            "complete_date_count": first_complete_count,
            "route_policy": "NXT_0800_0810_then_unfilled_leg_SOR_0900_0930",
        },
        "selection": selection,
        "decision": selection["decision"],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def render_markdown(report: dict[str, Any]) -> str:
    selection = report["selection"]
    candidate = selection.get("candidate")
    lines = [
        f"# Samsung morning re-entry research — {report['end_date']}",
        "",
        f"- decision: `{report['decision']}`",
        "- authority: source-only; no runtime or order mutation",
        f"- reconstructed first-episode complete dates: `{report['first_episode_reconstruction']['complete_date_count']}` / `{report['first_episode_reconstruction']['common_date_count']}`",
        f"- grid candidates: `{selection['grid_candidate_count']}`",
        "",
    ]
    if candidate is None:
        lines.append("No calibration-ready re-entry candidate was found.")
    else:
        lines.extend(
            [
                f"- parameters: `{candidate['parameters']}`",
                f"- calibration: `{candidate['calibration']}`",
                f"- holdout: `{candidate['holdout']}`",
                "",
                "Each family used calibration-only selection before holdout evaluation; the same holdout was reused across the disclosed family iteration. Minute-bar touches are not real fill evidence.",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    stem = f"samsung_morning_reentry_research_{report['end_date']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(md_path, render_markdown(report))
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(input_path=args.input, manifest_path=args.manifest)
    paths = write_report(report, args.output_dir) if args.write else (None, None)
    if args.print_summary:
        candidate = report["selection"].get("candidate")
        print(
            json.dumps(
                {
                    "decision": report["decision"],
                    "candidate": candidate["parameters"] if candidate else None,
                    "calibration": candidate["calibration"] if candidate else None,
                    "holdout": candidate["holdout"] if candidate else None,
                    "json_path": str(paths[0]) if paths[0] else None,
                    "markdown_path": str(paths[1]) if paths[1] else None,
                    "runtime_effect": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
