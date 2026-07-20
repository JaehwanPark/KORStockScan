from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.model.common_v2 import DATA_DIR, engine, resolve_bull_specialist_mode

REPORT_DIR = Path(DATA_DIR) / "report" / "swing_model_retrain"
MIN_CALENDAR_DAYS = 180
MIN_BULL_TRADING_DAYS = 60
MIN_BULL_ROWS = 3000
LABEL_SAFETY_DAYS = 5


def _parse_date(value: Any) -> date | None:
    try:
        if value in (None, ""):
            return None
        return pd.to_datetime(value).date()
    except Exception:
        return None


def _target_date(value: str | None) -> date:
    return _parse_date(value) or date.today()


def _load_ai_json_payload() -> dict[str, Any]:
    raw = os.getenv("KORSTOCKSCAN_SWING_BULL_AI_RESPONSE_JSON")
    if not raw:
        path = os.getenv("KORSTOCKSCAN_SWING_BULL_AI_RESPONSE_PATH")
        if path:
            try:
                raw = Path(path).read_text(encoding="utf-8")
            except Exception:
                raw = ""
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def deterministic_bull_period_proposal(
    target_date: str | None = None,
) -> dict[str, Any]:
    dt = _target_date(target_date)
    end = dt - timedelta(days=LABEL_SAFETY_DAYS)
    start = end - timedelta(days=730)
    mode = resolve_bull_specialist_mode(
        os.getenv("KORSTOCKSCAN_SWING_BULL_SPECIALIST_MODE")
    )
    return {
        "source": "deterministic_fallback",
        "bull_specialist_mode": mode,
        "bull_base_start": start.isoformat(),
        "bull_base_end": end.isoformat(),
        "reason": "recent_24m_with_label_safety_gap",
        "expected_regime_fit": "balanced_recent_bull_regime_window",
        "risk_flags": [],
    }


def load_ai_or_fallback_proposal(target_date: str | None = None) -> dict[str, Any]:
    payload = _load_ai_json_payload()
    if payload:
        proposal = {
            "source": "ai_response_json",
            "bull_specialist_mode": resolve_bull_specialist_mode(
                payload.get("bull_specialist_mode")
            ),
            "bull_base_start": payload.get("bull_base_start"),
            "bull_base_end": payload.get("bull_base_end"),
            "reason": payload.get("reason") or "",
            "expected_regime_fit": payload.get("expected_regime_fit") or "",
            "risk_flags": (
                payload.get("risk_flags")
                if isinstance(payload.get("risk_flags"), list)
                else []
            ),
        }
        return proposal
    return deterministic_bull_period_proposal(target_date)


def estimate_bull_period_stats(
    start: str, end: str, *, codes_limit: int = 300
) -> dict[str, Any]:
    """Lightweight DB-based proxy stats used by deterministic guard.

    The full bull_regime feature is calculated in dataset_builder_v2. For the
    guard, we require enough quote rows and trading days, then classify the final
    model by ablation in the retrain pipeline.
    """
    query = text("""
        SELECT COUNT(*) AS rows_count,
               COUNT(DISTINCT quote_date) AS trading_days,
               MIN(quote_date) AS min_date,
               MAX(quote_date) AS max_date
        FROM daily_stock_quotes
        WHERE quote_date >= :start
          AND quote_date <= :end
          AND stock_code IN (
              SELECT stock_code
              FROM daily_stock_quotes
              WHERE quote_date = (SELECT MAX(quote_date) FROM daily_stock_quotes)
              GROUP BY stock_code
              ORDER BY MAX(volume) DESC
              LIMIT :codes_limit
          )
        """)
    try:
        with engine.connect() as conn:
            row = pd.read_sql(
                query,
                conn,
                params={"start": start, "end": end, "codes_limit": codes_limit},
            ).iloc[0]
    except Exception as exc:
        return {
            "available": False,
            "error": str(exc),
            "bull_rows": 0,
            "bull_trading_days": 0,
            "min_date": None,
            "max_date": None,
        }
    return {
        "available": True,
        "bull_rows": int(row.get("rows_count") or 0),
        "bull_trading_days": int(row.get("trading_days") or 0),
        "min_date": (
            str(row.get("min_date")) if row.get("min_date") is not None else None
        ),
        "max_date": (
            str(row.get("max_date")) if row.get("max_date") is not None else None
        ),
    }


def guard_bull_period_proposal(
    proposal: dict[str, Any],
    *,
    target_date: str | None = None,
    stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = _target_date(target_date)
    start = _parse_date(proposal.get("bull_base_start"))
    end = _parse_date(proposal.get("bull_base_end"))
    mode = resolve_bull_specialist_mode(proposal.get("bull_specialist_mode"))
    reasons: list[str] = []

    if start is None:
        reasons.append("invalid_bull_base_start")
    if end is None:
        reasons.append("invalid_bull_base_end")
    if start and end and end < start:
        reasons.append("end_before_start")
    if end and end > target - timedelta(days=LABEL_SAFETY_DAYS):
        reasons.append("label_safety_gap_violation")
    calendar_days = (end - start).days + 1 if start and end and end >= start else 0
    if calendar_days < MIN_CALENDAR_DAYS:
        reasons.append("calendar_days_below_floor")

    stats_payload = stats
    if stats_payload is None and start and end:
        stats_payload = estimate_bull_period_stats(start.isoformat(), end.isoformat())
    stats_payload = stats_payload or {}
    bull_rows = int(stats_payload.get("bull_rows") or 0)
    bull_days = int(stats_payload.get("bull_trading_days") or 0)
    if bull_rows < MIN_BULL_ROWS:
        reasons.append("bull_rows_below_floor")
    if bull_days < MIN_BULL_TRADING_DAYS:
        reasons.append("bull_trading_days_below_floor")

    guard_passed = not reasons
    fallback = deterministic_bull_period_proposal(target.isoformat())
    final_start = (
        proposal.get("bull_base_start") if guard_passed else fallback["bull_base_start"]
    )
    final_end = (
        proposal.get("bull_base_end") if guard_passed else fallback["bull_base_end"]
    )
    final_mode = mode if guard_passed else "hold_current"
    return {
        "schema_version": 1,
        "report_type": "swing_bull_period_ai_review",
        "target_date": target.isoformat(),
        "proposal": proposal,
        "stats": stats_payload,
        "guard": {
            "passed": guard_passed,
            "reasons": reasons,
            "min_calendar_days": MIN_CALENDAR_DAYS,
            "min_bull_trading_days": MIN_BULL_TRADING_DAYS,
            "min_bull_rows": MIN_BULL_ROWS,
            "label_safety_days": LABEL_SAFETY_DAYS,
        },
        "decision": {
            "bull_specialist_mode": final_mode,
            "bull_base_start": final_start,
            "bull_base_end": final_end,
            "source": "ai_guarded" if guard_passed else "fallback_hold_current",
        },
        "runtime_change": False,
    }


def review_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"bull_period_ai_review_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def render_markdown(report: dict[str, Any]) -> str:
    decision = report.get("decision") or {}
    guard = report.get("guard") or {}
    return "\n".join(
        [
            f"# Swing Bull Period AI Review {report.get('target_date')}",
            "",
            f"- mode: `{decision.get('bull_specialist_mode')}`",
            f"- bull_base_start: `{decision.get('bull_base_start')}`",
            f"- bull_base_end: `{decision.get('bull_base_end')}`",
            f"- guard_passed: `{guard.get('passed')}`",
            f"- guard_reasons: `{', '.join(guard.get('reasons') or []) or '-'}`",
            "- runtime_change: `false`",
            "",
        ]
    )


def write_review(target_date: str | None = None) -> dict[str, Any]:
    target = _target_date(target_date).isoformat()
    proposal = load_ai_or_fallback_proposal(target)
    report = guard_bull_period_proposal(proposal, target_date=target)
    json_path, md_path = review_paths(target)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review swing bull specialist period proposal."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    write_review(args.target_date)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
