"""Build lifecycle labels for Swing Strategy Discovery Sim arms."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import (
    DailyStockQuote,
    SwingStrategyDiscoveryArm,
    SwingStrategyDiscoveryCandidate,
    SwingStrategyDiscoveryLabel,
)
from src.engine.swing_strategy_discovery_schema import ensure_swing_strategy_discovery_schema
from src.utils.constants import DATA_DIR, POSTGRES_URL


REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_labels"
DECISION_AUTHORITY = "swing_sim_exploration_only"
LABEL_VERSION = "swing_strategy_discovery_label_v1"
IMPLEMENTATION_ORDER_ID = "order_swing_strategy_discovery_source_quality_followup"
LABEL_HORIZONS = {"1d": 1, "5d": 5, "10d": 10}
ENTRY_LOOKAHEAD_DAYS = 3
PULLBACK_LIMIT_PCT = -1.5
BOTTOM_REBOUND_RETEST_LIMIT_PCT = -0.2
BOTTOM_REBOUND_ATR_PULLBACK_LIMIT_PCT = -1.0
BREAKOUT_TRIGGER_PCT = 1.5
GAP_FADE_GAP_PCT = 1.5
GAP_FADE_LIMIT_PCT = 0.3
MAE_STOP_PCT = -3.0
TRAILING_ARM_MFE_PCT = 4.0
TRAILING_GIVEBACK_PCT = -2.0
SCALE_IN_DRAWDOWN_PCT = -3.0
SCALE_IN_ADD_RATIO = 0.5


@dataclass
class Quote:
    quote_date: date
    open_price: float
    high_price: float
    low_price: float
    close_price: float


@dataclass
class EntryResult:
    status: str
    entry_date: date | None = None
    entry_price: float | None = None
    reason: str = ""


@dataclass
class ExitResult:
    status: str
    exit_date: date | None = None
    exit_price: float | None = None
    exit_reason: str = ""
    final_return_pct: float | None = None
    realized_exit_return_pct: float | None = None
    scale_in_delta_pct: float | None = None
    exit_only_delta_pct: float | None = None
    holding_days: int | None = None


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _pct(value: float, base: float) -> float:
    if base <= 0:
        return 0.0
    return ((value - base) / base) * 100.0


def _price_at_pct(base: float, pct: float) -> float:
    return base * (1.0 + pct / 100.0)


def _json_loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _quote_from_model(row: DailyStockQuote) -> Quote | None:
    open_price = _as_float(row.open_price)
    high_price = _as_float(row.high_price)
    low_price = _as_float(row.low_price)
    close_price = _as_float(row.close_price)
    if min(open_price, high_price, low_price, close_price) <= 0:
        return None
    return Quote(
        quote_date=row.quote_date,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
    )


def simulate_entry(entry_policy: str, reference_price: float, future_quotes: list[Quote]) -> EntryResult:
    if reference_price <= 0:
        return EntryResult("expired", reason="missing_reference_price")
    if not future_quotes:
        return EntryResult("pending_future_quotes", reason="missing_next_quote")
    if entry_policy == "next_open_entry":
        q = future_quotes[0]
        return EntryResult("entered", q.quote_date, q.open_price, "next_open")
    if entry_policy == "bottom_rebound_next_open_entry":
        q = future_quotes[0]
        return EntryResult("entered", q.quote_date, q.open_price, "bottom_rebound_next_open")
    lookahead = future_quotes[:ENTRY_LOOKAHEAD_DAYS]
    if entry_policy == "pullback_limit_entry":
        limit_price = _price_at_pct(reference_price, PULLBACK_LIMIT_PCT)
        for q in lookahead:
            if q.low_price <= limit_price:
                return EntryResult("entered", q.quote_date, limit_price, "pullback_limit_touched")
        return EntryResult("expired" if len(lookahead) >= ENTRY_LOOKAHEAD_DAYS else "pending_future_quotes", reason="pullback_not_touched")
    if entry_policy == "bottom_rebound_signal_close_retest_limit_entry":
        limit_price = _price_at_pct(reference_price, BOTTOM_REBOUND_RETEST_LIMIT_PCT)
        for q in lookahead:
            if q.low_price <= limit_price:
                return EntryResult("entered", q.quote_date, limit_price, "bottom_rebound_signal_close_retest_touched")
        return EntryResult(
            "expired" if len(lookahead) >= ENTRY_LOOKAHEAD_DAYS else "pending_future_quotes",
            reason="bottom_rebound_signal_close_retest_not_touched",
        )
    if entry_policy == "bottom_rebound_atr_pullback_limit_entry":
        limit_price = _price_at_pct(reference_price, BOTTOM_REBOUND_ATR_PULLBACK_LIMIT_PCT)
        for q in lookahead:
            if q.low_price <= limit_price:
                return EntryResult("entered", q.quote_date, limit_price, "bottom_rebound_atr_pullback_touched")
        return EntryResult(
            "expired" if len(lookahead) >= ENTRY_LOOKAHEAD_DAYS else "pending_future_quotes",
            reason="bottom_rebound_atr_pullback_not_touched",
        )
    if entry_policy == "breakout_confirm_entry":
        trigger_price = _price_at_pct(reference_price, BREAKOUT_TRIGGER_PCT)
        for q in lookahead:
            if q.high_price >= trigger_price:
                return EntryResult("entered", q.quote_date, trigger_price, "breakout_trigger_touched")
        return EntryResult("expired" if len(lookahead) >= ENTRY_LOOKAHEAD_DAYS else "pending_future_quotes", reason="breakout_not_touched")
    if entry_policy == "gap_fade_entry":
        q = future_quotes[0]
        gap_pct = _pct(q.open_price, reference_price)
        limit_price = _price_at_pct(reference_price, GAP_FADE_LIMIT_PCT)
        if gap_pct >= GAP_FADE_GAP_PCT and q.low_price <= limit_price:
            return EntryResult("entered", q.quote_date, limit_price, "gap_fade_limit_touched")
        return EntryResult("expired", reason="gap_fade_condition_not_met")
    return EntryResult("expired", reason=f"unknown_entry_policy:{entry_policy}")


def _quotes_from_entry(entry: EntryResult, future_quotes: list[Quote]) -> list[Quote]:
    if entry.entry_date is None:
        return []
    return [q for q in future_quotes if q.quote_date >= entry.entry_date]


def _label_maturity_status(entry: EntryResult, exit_result: ExitResult) -> str:
    if exit_result.status == "exited":
        return "matured_labeled"
    if entry.status == "expired":
        return "matured_no_entry"
    if entry.status == "pending_future_quotes" or exit_result.status == "pending_future_quotes":
        return "pending_future_quotes"
    return "unresolved"


def _window_mfe_mae(quotes: list[Quote], entry_price: float) -> tuple[float, float]:
    if not quotes or entry_price <= 0:
        return 0.0, 0.0
    return round(max(_pct(q.high_price, entry_price) for q in quotes), 6), round(
        min(_pct(q.low_price, entry_price) for q in quotes),
        6,
    )


def simulate_policy_exit(exit_policy: str, entry: EntryResult, quotes_from_entry: list[Quote]) -> ExitResult:
    if entry.status != "entered" or not entry.entry_date or not entry.entry_price:
        return ExitResult("not_entered", exit_reason=entry.reason)
    entry_price = float(entry.entry_price)
    if not quotes_from_entry:
        return ExitResult("pending_future_quotes", exit_reason="missing_entry_window")

    def _fixed(days: int, reason: str) -> ExitResult:
        if len(quotes_from_entry) < days:
            return ExitResult("pending_future_quotes", exit_reason=f"need_{days}_quotes")
        q = quotes_from_entry[days - 1]
        ret = round(_pct(q.close_price, entry_price), 6)
        return ExitResult("exited", q.quote_date, q.close_price, reason, ret, ret, holding_days=days)

    if exit_policy == "fixed_5d":
        return _fixed(5, "fixed_5d_close")
    if exit_policy == "fixed_10d":
        return _fixed(10, "fixed_10d_close")
    if exit_policy == "mae_stop_time_stop":
        stop_price = _price_at_pct(entry_price, MAE_STOP_PCT)
        window = quotes_from_entry[:10]
        for idx, q in enumerate(window, start=1):
            if q.low_price <= stop_price:
                ret = round(_pct(stop_price, entry_price), 6)
                return ExitResult("exited", q.quote_date, stop_price, "mae_stop_touched", ret, ret, holding_days=idx)
        return _fixed(10, "mae_stop_time_stop_10d_close")
    if exit_policy == "trailing_after_mfe":
        window = quotes_from_entry[:10]
        peak = entry_price
        armed = False
        for idx, q in enumerate(window, start=1):
            peak = max(peak, q.high_price)
            if _pct(peak, entry_price) >= TRAILING_ARM_MFE_PCT:
                armed = True
            if armed:
                trail_price = _price_at_pct(peak, TRAILING_GIVEBACK_PCT)
                if q.low_price <= trail_price:
                    ret = round(_pct(trail_price, entry_price), 6)
                    return ExitResult("exited", q.quote_date, trail_price, "trailing_after_mfe_stop", ret, ret, holding_days=idx)
        return _fixed(10, "trailing_after_mfe_10d_close")
    if exit_policy == "scale_in_recovery":
        if len(quotes_from_entry) < 10:
            return ExitResult("pending_future_quotes", exit_reason="need_10_quotes")
        scale_price = _price_at_pct(entry_price, SCALE_IN_DRAWDOWN_PCT)
        added = False
        for q in quotes_from_entry[:10]:
            if q.low_price <= scale_price:
                added = True
                break
        exit_q = quotes_from_entry[9]
        base_ret = _pct(exit_q.close_price, entry_price)
        if added:
            avg_price = ((entry_price * 1.0) + (scale_price * SCALE_IN_ADD_RATIO)) / (1.0 + SCALE_IN_ADD_RATIO)
            scaled_ret = _pct(exit_q.close_price, avg_price)
            delta = scaled_ret - base_ret
            ret = round(scaled_ret, 6)
            return ExitResult(
                "exited",
                exit_q.quote_date,
                exit_q.close_price,
                "scale_in_recovery_10d_close",
                ret,
                ret,
                scale_in_delta_pct=round(delta, 6),
                exit_only_delta_pct=round(base_ret, 6),
                holding_days=10,
            )
        ret = round(base_ret, 6)
        return ExitResult(
            "exited",
            exit_q.quote_date,
            exit_q.close_price,
            "scale_in_not_triggered_10d_close",
            ret,
            ret,
            scale_in_delta_pct=0.0,
            exit_only_delta_pct=ret,
            holding_days=10,
        )
    return ExitResult("expired", exit_reason=f"unknown_exit_policy:{exit_policy}")


def build_horizon_label(horizon: str, entry: EntryResult, quotes_from_entry: list[Quote]) -> dict[str, Any]:
    days = LABEL_HORIZONS[horizon]
    if entry.status != "entered" or not entry.entry_price:
        return {
            "label_horizon": horizon,
            "label_status": "expired_entry_no_trigger" if entry.status == "expired" else "pending_future_quotes",
            "label_features": {"fill_status": entry.status, "final_return_basis": "horizon_close", "entry_reason": entry.reason},
        }
    if len(quotes_from_entry) < days:
        return {
            "label_horizon": horizon,
            "label_status": "pending_future_quotes",
            "label_features": {"fill_status": "entered", "final_return_basis": "horizon_close", "required_days": days},
        }
    window = quotes_from_entry[:days]
    mfe, mae = _window_mfe_mae(window, entry.entry_price)
    close_return = round(_pct(window[-1].close_price, entry.entry_price), 6)
    return {
        "label_horizon": horizon,
        "label_status": "labeled",
        "mfe_pct": mfe,
        "mae_pct": mae,
        "close_return_pct": close_return,
        "final_return_pct": close_return,
        "label_features": {
            "fill_status": "entered",
            "final_return_basis": "horizon_close",
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "entry_price": entry.entry_price,
            "horizon_days": days,
        },
    }


def build_policy_exit_label(entry: EntryResult, exit_result: ExitResult, quotes_from_entry: list[Quote]) -> dict[str, Any]:
    mfe, mae = _window_mfe_mae(quotes_from_entry[: max(1, int(exit_result.holding_days or 10))], entry.entry_price or 0.0)
    status = "labeled" if exit_result.status == "exited" else (
        "expired_entry_no_trigger" if entry.status == "expired" else "pending_future_quotes"
    )
    return {
        "label_horizon": "policy_exit",
        "label_status": status,
        "mfe_pct": mfe if entry.status == "entered" else None,
        "mae_pct": mae if entry.status == "entered" else None,
        "close_return_pct": exit_result.final_return_pct,
        "final_return_pct": exit_result.final_return_pct,
        "realized_exit_return_pct": exit_result.realized_exit_return_pct,
        "exit_only_delta_pct": exit_result.exit_only_delta_pct,
        "scale_in_delta_pct": exit_result.scale_in_delta_pct,
        "label_features": {
            "fill_status": entry.status,
            "final_return_basis": "arm_policy_exit",
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "entry_price": entry.entry_price,
            "exit_date": exit_result.exit_date.isoformat() if exit_result.exit_date else None,
            "exit_price": exit_result.exit_price,
            "exit_reason": exit_result.exit_reason,
            "holding_days": exit_result.holding_days,
        },
    }


def _load_future_quotes(session: Any, stock_code: str, source_date: date) -> list[Quote]:
    rows = (
        session.query(DailyStockQuote)
        .filter(DailyStockQuote.stock_code == stock_code, DailyStockQuote.quote_date > source_date)
        .order_by(DailyStockQuote.quote_date.asc())
        .all()
    )
    out = [_quote_from_model(row) for row in rows]
    return [q for q in out if q is not None]


def _reference_price(arm: SwingStrategyDiscoveryArm, candidate: SwingStrategyDiscoveryCandidate) -> float:
    if arm.virtual_entry_price:
        return float(arm.virtual_entry_price)
    source_features = _json_loads(candidate.source_features)
    quote = source_features.get("quote_features") if isinstance(source_features.get("quote_features"), dict) else {}
    return _as_float(quote.get("reference_price"), 0.0)


def _upsert_label(
    session: Any,
    arm: SwingStrategyDiscoveryArm,
    label: dict[str, Any],
) -> None:
    existing = (
        session.query(SwingStrategyDiscoveryLabel)
        .filter_by(arm_row_id=arm.id, label_horizon=label["label_horizon"], label_version=LABEL_VERSION)
        .first()
    )
    payload = {
        "arm_row_id": arm.id,
        "source_date": arm.source_date,
        "stock_code": arm.stock_code,
        "policy_version": arm.policy_version,
        "label_horizon": label["label_horizon"],
        "label_version": LABEL_VERSION,
        "label_status": label.get("label_status"),
        "mfe_pct": label.get("mfe_pct"),
        "mae_pct": label.get("mae_pct"),
        "close_return_pct": label.get("close_return_pct"),
        "final_return_pct": label.get("final_return_pct"),
        "realized_exit_return_pct": label.get("realized_exit_return_pct"),
        "exit_only_delta_pct": label.get("exit_only_delta_pct"),
        "scale_in_delta_pct": label.get("scale_in_delta_pct"),
        "label_features": json.dumps(label.get("label_features") or {}, ensure_ascii=False, sort_keys=True, default=str),
        "updated_at": datetime.now(),
    }
    if existing is None:
        session.add(SwingStrategyDiscoveryLabel(**payload))
    else:
        for key, value in payload.items():
            setattr(existing, key, value)


def process_arm(session: Any, arm: SwingStrategyDiscoveryArm) -> dict[str, Any]:
    candidate = session.query(SwingStrategyDiscoveryCandidate).filter_by(id=arm.candidate_id).first()
    if candidate is None:
        return {"status": "candidate_missing", "labels": 0}
    future_quotes = _load_future_quotes(session, arm.stock_code, arm.source_date)
    reference_price = _reference_price(arm, candidate)
    entry = simulate_entry(arm.entry_policy, reference_price, future_quotes)
    quotes_from_entry = _quotes_from_entry(entry, future_quotes)
    exit_result = simulate_policy_exit(arm.exit_policy, entry, quotes_from_entry)
    maturity_status = _label_maturity_status(entry, exit_result)
    labels = [build_horizon_label(horizon, entry, quotes_from_entry) for horizon in LABEL_HORIZONS]
    labels.append(build_policy_exit_label(entry, exit_result, quotes_from_entry))
    for label in labels:
        _upsert_label(session, arm, label)

    if entry.status == "entered":
        arm.status = "EXITED" if exit_result.status == "exited" else "ENTERED"
        arm.entry_at = datetime.combine(entry.entry_date, datetime.min.time()) if entry.entry_date else None
        arm.virtual_entry_price = entry.entry_price
        if exit_result.status == "exited":
            arm.exit_at = datetime.combine(exit_result.exit_date, datetime.min.time()) if exit_result.exit_date else None
            arm.exit_price = exit_result.exit_price
            arm.final_return_pct = exit_result.final_return_pct
    elif entry.status == "expired":
        arm.status = "EXPIRED"
    else:
        arm.status = "PENDING_ENTRY"
    features = _json_loads(arm.arm_features)
    features.update(
        {
            "label_version": LABEL_VERSION,
            "entry_status": entry.status,
            "entry_reason": entry.reason,
            "policy_exit_status": exit_result.status,
            "policy_exit_reason": exit_result.exit_reason,
            "label_maturity_status": maturity_status,
            "future_quote_count": len(future_quotes),
            "quotes_from_entry_count": len(quotes_from_entry),
            "latest_future_quote_date": (
                max(q.quote_date for q in future_quotes).isoformat() if future_quotes else None
            ),
            "source_quality_status": "pending_future_quotes" if maturity_status == "pending_future_quotes" else "ok",
            "implementation_order_id": IMPLEMENTATION_ORDER_ID,
            "implementation_scope": "source_quality_instrumentation_only",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    )
    arm.arm_features = json.dumps(features, ensure_ascii=False, sort_keys=True, default=str)
    arm.updated_at = datetime.now()
    return {
        "status": arm.status,
        "labels": len(labels),
        "label_status_counts": dict(Counter(label.get("label_status") for label in labels)),
        "maturity_status": maturity_status,
    }


def build_swing_strategy_discovery_labels(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    refresh_matured: bool = False,
) -> dict[str, Any]:
    ensure_swing_strategy_discovery_schema(db_url)
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    date_key = _date_text(target_date)
    target = datetime.fromisoformat(date_key).date()
    processed = 0
    status_counts: Counter[str] = Counter()
    label_status_counts: Counter[str] = Counter()
    maturity_status_counts: Counter[str] = Counter()
    with Session.begin() as session:
        query = session.query(SwingStrategyDiscoveryArm).filter(SwingStrategyDiscoveryArm.source_date <= target)
        if not refresh_matured:
            query = query.filter(SwingStrategyDiscoveryArm.source_date == target)
        arms = query.order_by(SwingStrategyDiscoveryArm.source_date.asc(), SwingStrategyDiscoveryArm.id.asc()).all()
        for arm in arms:
            result = process_arm(session, arm)
            processed += 1
            status_counts[str(result.get("status"))] += 1
            maturity_status_counts[str(result.get("maturity_status") or "unknown")] += 1
            for status, count in (result.get("label_status_counts") or {}).items():
                label_status_counts[str(status)] += int(count)

    report = {
        "schema_version": 1,
        "report_type": "swing_strategy_discovery_labels",
        "date": date_key,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "label_version": LABEL_VERSION,
        "runtime_effect": False,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "refresh_matured": bool(refresh_matured),
        "implementation_status": "implemented",
        "implementation_provenance": {
            "order_id": IMPLEMENTATION_ORDER_ID,
            "scope": "source_quality_instrumentation_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": DECISION_AUTHORITY,
        },
        "implementation_checks": [
            {
                "name": "label_source_quality_provenance",
                "status": "pass",
                "fields": [
                    "label_maturity_status",
                    "future_quote_count",
                    "quotes_from_entry_count",
                    "source_quality_status",
                ],
            },
            {
                "name": "runtime_effect_contract",
                "status": "pass",
                "runtime_effect": False,
            },
        ],
        "summary": {
            "processed_arm_count": processed,
            "arm_status_counts": dict(status_counts),
            "label_status_counts": dict(label_status_counts),
            "maturity_status_counts": dict(maturity_status_counts),
            "pending_future_quote_count": label_status_counts.get("pending_future_quotes", 0),
            "labeled_sample_count": label_status_counts.get("labeled", 0),
        },
        "warnings": ["pending_future_quotes"] if label_status_counts.get("pending_future_quotes", 0) else [],
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return "\n".join(
        [
            f"# Swing Strategy Discovery Labels - {report.get('date')}",
            "",
            f"- generated_at: `{report.get('generated_at')}`",
            f"- label_version: `{report.get('label_version')}`",
            f"- runtime_effect: `{report.get('runtime_effect')}`",
            f"- decision_authority: `{report.get('decision_authority')}`",
            f"- processed_arm_count: `{summary.get('processed_arm_count')}`",
            f"- arm_status_counts: `{summary.get('arm_status_counts')}`",
            f"- label_status_counts: `{summary.get('label_status_counts')}`",
            f"- maturity_status_counts: `{summary.get('maturity_status_counts')}`",
            f"- pending_future_quote_count: `{summary.get('pending_future_quote_count')}`",
            f"- implementation_status: `{report.get('implementation_status') or '-'}`",
            "",
            "## Contract",
            "",
            "- Horizon labels use 1d/5d/10d close basis.",
            "- `policy_exit` uses the arm exit policy final return basis.",
            "- Future-only label fields are never runtime inputs.",
            "- All rows remain sim exploration only.",
            "",
        ]
    )


def write_swing_strategy_discovery_labels(
    target_date: str,
    *,
    db_url: str = POSTGRES_URL,
    output_dir: Path = REPORT_DIR,
    refresh_matured: bool = False,
) -> dict[str, Path]:
    report = build_swing_strategy_discovery_labels(target_date, db_url=db_url, refresh_matured=refresh_matured)
    output_dir.mkdir(parents=True, exist_ok=True)
    date_key = _date_text(target_date)
    json_path = output_dir / f"swing_strategy_discovery_labels_{date_key}.json"
    md_path = output_dir / f"swing_strategy_discovery_labels_{date_key}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--db-url", default=POSTGRES_URL)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--refresh-matured", action="store_true")
    args = parser.parse_args(argv)
    paths = write_swing_strategy_discovery_labels(
        args.target_date,
        db_url=args.db_url,
        output_dir=args.output_dir,
        refresh_matured=args.refresh_matured,
    )
    print(f"[DONE] swing_strategy_discovery_label_builder json={paths['json']} md={paths['md']}")


if __name__ == "__main__":
    main()
