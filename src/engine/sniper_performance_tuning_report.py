"""Performance tuning report for AI-heavy holding and gatekeeper paths."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from src.engine.log_archive_service import iter_target_log_lines
from src.engine.sniper_trade_review_report import build_trade_review_report
from src.utils.constants import LOGS_DIR, POSTGRES_URL, TRADING_RULES


_ENTRY_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[ENTRY_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_HOLDING_RE = re.compile(
    r"^\[(?P<timestamp>[^\]]+)\].*?\[HOLDING_PIPELINE\] "
    r"(?P<name>.+?)\((?P<code>[^)]+)\) "
    r"stage=(?P<stage>[^\s]+)(?P<rest>.*)$"
)
_FIELD_RE = re.compile(r"(?P<key>[A-Za-z_]+)=(?P<value>[^\s]+)")

_GATEKEEPER_DECISION_STAGES = {
    "blocked_gatekeeper_reject",
    "market_regime_pass",
    "blocked_gatekeeper_error",
}
_CONFIRMED_ENTRY_STAGES = {"order_bundle_submitted"}
_ENTRY_ARMED_STAGES = {"entry_armed", "entry_armed_resume"}
_GATEKEEPER_ACTION_RE = re.compile(
    r"\saction=(?P<action>.+?)(?:\s+cooldown_sec=|\s+cooldown_policy=|\s+gatekeeper_eval_ms=|$)"
)
_STRATEGY_LABELS = {
    "scalping": "스캘핑",
    "swing": "스윙",
    "other": "기타",
}
_STRATEGY_ORDER = ("scalping", "swing")
_BLOCKER_LABELS = {
    "blocked_strength_momentum": "동적 체결강도",
    "blocked_liquidity": "유동성",
    "blocked_ai_score": "AI 점수",
    "latency_block": "지연 리스크",
    "blocked_zero_qty": "주문 가능 수량",
    "blocked_gap_from_scan": "포착가 대비 갭",
    "blocked_overbought": "과열",
    "blocked_big_bite_hard_gate": "Big-Bite 하드게이트",
    "blocked_vpw": "정적 체결강도",
    "blocked_gatekeeper_reject": "게이트키퍼 보류",
    "blocked_swing_gap": "스윙 갭상승",
    "first_ai_wait": "첫 AI 대기",
}
_REUSE_REASON_LABELS = {
    "sig_changed": "시그니처 변경",
    "age_expired": "재사용 창 만료",
    "ws_stale": "WS stale",
    "price_move": "가격 변화 확대",
    "near_ai_exit": "AI 손절 경계",
    "near_safe_profit": "안전수익 경계",
    "near_low_score": "저점수 경계",
    "score_boundary": "점수 경계",
    "missing_action": "이전 액션 없음",
    "missing_allow_flag": "이전 허용값 없음",
}


@dataclass
class PerfEvent:
    timestamp: str
    name: str
    code: str
    stage: str
    fields: dict[str, str]
    raw_line: str


def _parse_since_datetime(target_date: str, since_time: str | None) -> datetime | None:
    if not since_time:
        return None
    candidate = str(since_time).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            if fmt.startswith("%Y"):
                return datetime.strptime(candidate, fmt)
            return datetime.strptime(f"{target_date} {candidate}", f"%Y-%m-%d {fmt}")
        except Exception:
            continue
    return None


def _iter_target_lines(log_path: Path, *, target_date: str, marker: str) -> list[str]:
    return iter_target_log_lines([log_path], target_date=target_date, marker=marker)


def _parse_event(line: str, pattern: re.Pattern[str]) -> PerfEvent | None:
    match = pattern.match(line.strip())
    if not match:
        return None
    fields = {
        m.group("key"): str(m.group("value") or "").replace("|", " ")
        for m in _FIELD_RE.finditer(match.group("rest") or "")
    }
    return PerfEvent(
        timestamp=match.group("timestamp"),
        name=match.group("name"),
        code=match.group("code"),
        stage=match.group("stage"),
        fields=fields,
        raw_line=line.strip(),
    )


def _safe_float(value, default: float | None = None) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int | None = None) -> int | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_date_string(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    rank = max(0, min(len(ordered) - 1, math.ceil((pct / 100.0) * len(ordered)) - 1))
    return float(ordered[rank])


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator > 0 else 0.0


def _metric_card(label: str, value: str, hint: str = "") -> dict:
    return {"label": label, "value": value, "hint": hint}


def _strategy_group(strategy: str | None) -> str:
    raw = str(strategy or "").strip().upper()
    if raw == "SCALPING":
        return "scalping"
    if raw in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "SWING_ML"}:
        return "swing"
    return "other"


def _strategy_label(group: str) -> str:
    return _STRATEGY_LABELS.get(group, group)


def _classify_entry_stage(stage: str) -> str:
    if stage in _CONFIRMED_ENTRY_STAGES:
        return "submitted"
    if stage.startswith("blocked_") or stage.endswith("_block") or stage.endswith("_failed"):
        return "blocked"
    if stage == "first_ai_wait":
        return "waiting"
    return "progress"


def _parse_trade_dt(value) -> datetime | None:
    if value in (None, "", "None"):
        return None
    candidate = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return None


def _is_entered_trade(row: dict) -> bool:
    status = str(row.get("status") or "").upper()
    if row.get("buy_time"):
        return True
    if (_safe_int(row.get("buy_qty"), 0) or 0) > 0:
        return True
    return status in {"BUY_ORDERED", "HOLDING", "SELL_ORDERED", "COMPLETED"}


def _extract_gatekeeper_action(event: PerfEvent) -> str:
    action = str(event.fields.get("action") or "").replace("|", " ").strip()
    if action and action not in {"눌림", "전량", "둘", "스윙"}:
        return action
    match = _GATEKEEPER_ACTION_RE.search(event.raw_line or "")
    if match:
        return str(match.group("action") or "").replace("|", " ").strip()
    return action


def _friendly_blocker_name(event: PerfEvent) -> str:
    if event.stage == "blocked_gatekeeper_reject":
        action = _extract_gatekeeper_action(event)
        if action:
            return f"게이트키퍼: {action}"
    return _BLOCKER_LABELS.get(event.stage, event.stage)


def _split_reason_codes(value) -> list[str]:
    raw = str(value or "").strip()
    if not raw:
        return []
    return [token for token in re.split(r"[,\s]+", raw) if token]


def _friendly_reason_name(code: str) -> str:
    normalized = str(code or "").strip()
    return _REUSE_REASON_LABELS.get(normalized, normalized)


def _build_current_trade_rows(target_date: str) -> tuple[list[dict], list[str]]:
    report = build_trade_review_report(
        target_date=target_date,
        since_time=None,
        top_n=10_000,
        scope="all",
    )
    rows = list((report.get("sections", {}) or {}).get("recent_trades", []) or [])
    warnings = list((report.get("meta", {}) or {}).get("warnings", []) or [])
    return rows, warnings


def _infer_strategy_from_event(event: PerfEvent, strategy_by_code: dict[str, str]) -> str:
    raw = str(event.fields.get("strategy") or "").strip()
    if raw:
        return raw
    raw = str(strategy_by_code.get(str(event.code or "").strip()[:6]) or "").strip()
    if raw:
        return raw
    if event.stage in {
        "blocked_gatekeeper_reject",
        "blocked_swing_gap",
        "market_regime_pass",
        "blocked_gatekeeper_error",
    }:
        return "KOSPI_ML"
    return "SCALPING"


def _summarize_top_counts(counter: Counter[str], limit: int = 3) -> list[dict]:
    total = sum(counter.values())
    rows = []
    for label, count in counter.most_common(limit):
        rows.append({
            "label": label,
            "count": count,
            "ratio": _ratio(count, total),
        })
    return rows


def _build_strategy_outcomes(
    *,
    entry_events: list[PerfEvent],
    holding_events: list[PerfEvent],
    trade_rows: list[dict],
    trend_by_group: dict[str, dict] | None = None,
) -> list[dict]:
    strategy_by_code = {}
    for row in trade_rows:
        code = str(row.get("code") or "").strip()[:6]
        if not code:
            continue
        if code not in strategy_by_code:
            strategy_by_code[code] = str(row.get("strategy") or "")

    stock_events: dict[tuple[str, str], list[PerfEvent]] = {}
    for event in entry_events:
        stock_events.setdefault((event.name, event.code), []).append(event)

    pipeline_by_group: dict[str, dict] = {}
    for group in _STRATEGY_ORDER:
        pipeline_by_group[group] = {
            "candidates": 0,
            "ai_confirmed": 0,
            "entry_armed": 0,
            "submitted": 0,
            "blocked_latest": 0,
            "waiting_latest": 0,
            "progress_latest": 0,
            "latest_blockers": Counter(),
        }

    for _, item_events in stock_events.items():
        latest = item_events[-1]
        raw_strategy = _infer_strategy_from_event(latest, strategy_by_code)
        group = _strategy_group(raw_strategy)
        if group not in pipeline_by_group:
            continue
        bucket = pipeline_by_group[group]
        bucket["candidates"] += 1
        seen_stages = {event.stage for event in item_events}
        if "ai_confirmed" in seen_stages:
            bucket["ai_confirmed"] += 1
        if seen_stages & _ENTRY_ARMED_STAGES:
            bucket["entry_armed"] += 1
        if seen_stages & _CONFIRMED_ENTRY_STAGES:
            bucket["submitted"] += 1
        stage_class = _classify_entry_stage(latest.stage)
        if stage_class == "blocked":
            bucket["blocked_latest"] += 1
            bucket["latest_blockers"][_friendly_blocker_name(latest)] += 1
        elif stage_class == "waiting":
            bucket["waiting_latest"] += 1
        else:
            bucket["progress_latest"] += 1

    outcome_by_group: dict[str, dict] = {}
    for group in _STRATEGY_ORDER:
        group_rows = [row for row in trade_rows if _strategy_group(row.get("strategy")) == group]
        entered_rows = [row for row in group_rows if _is_entered_trade(row)]
        completed_rows = [row for row in entered_rows if str(row.get("status") or "").upper() == "COMPLETED"]
        open_rows = [row for row in entered_rows if str(row.get("status") or "").upper() != "COMPLETED"]
        win_count = sum(1 for row in completed_rows if _safe_float(row.get("profit_rate")) > 0)
        loss_count = sum(1 for row in completed_rows if _safe_float(row.get("profit_rate")) < 0)
        outcome_by_group[group] = {
            "rows": group_rows,
            "entered_rows": entered_rows,
            "completed_rows": completed_rows,
            "open_rows": open_rows,
            "watching_rows": [
                row for row in group_rows
                if str(row.get("status") or "").upper() == "WATCHING"
            ],
            "expired_rows": [
                row for row in group_rows
                if str(row.get("status") or "").upper() == "EXPIRED"
            ],
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": _ratio(win_count, len(completed_rows)),
            "avg_profit_rate": round(
                sum(_safe_float(row.get("profit_rate")) for row in completed_rows) / len(completed_rows),
                2,
            ) if completed_rows else 0.0,
            "realized_pnl_krw": int(sum((_safe_int(row.get("realized_pnl_krw"), 0) or 0) for row in completed_rows)),
        }

    trade_group_by_code = {}
    for group, payload in outcome_by_group.items():
        for row in payload["entered_rows"]:
            code = str(row.get("code") or "").strip()[:6]
            if code and code not in trade_group_by_code:
                trade_group_by_code[code] = group

    exit_rules_by_group = {group: Counter() for group in _STRATEGY_ORDER}
    early_exit_by_group = Counter()
    for event in holding_events:
        if event.stage != "exit_signal":
            continue
        group = trade_group_by_code.get(str(event.code or "").strip()[:6])
        if group not in exit_rules_by_group:
            continue
        exit_rule = str(event.fields.get("exit_rule") or "-")
        exit_rules_by_group[group][exit_rule] += 1
        if "ai_early" in exit_rule:
            early_exit_by_group[group] += 1

    strategy_rows = []
    for group in _STRATEGY_ORDER:
        pipe = pipeline_by_group[group]
        out = outcome_by_group[group]
        blocker_total = sum(pipe["latest_blockers"].values())
        strategy_rows.append({
            "key": group,
            "label": _strategy_label(group),
            "pipeline": {
                "candidates": pipe["candidates"],
                "ai_confirmed": pipe["ai_confirmed"],
                "entry_armed": pipe["entry_armed"],
                "submitted": pipe["submitted"],
                "blocked_latest": pipe["blocked_latest"],
                "waiting_latest": pipe["waiting_latest"],
                "progress_latest": pipe["progress_latest"],
                "ai_confirm_rate": _ratio(pipe["ai_confirmed"], pipe["candidates"]),
                "entry_arm_rate": _ratio(pipe["entry_armed"], pipe["ai_confirmed"]),
                "submitted_rate": _ratio(pipe["submitted"], pipe["entry_armed"]),
                "latest_blockers": _summarize_top_counts(pipe["latest_blockers"]),
                "top_blocker": pipe["latest_blockers"].most_common(1)[0][0] if pipe["latest_blockers"] else "",
                "top_blocker_ratio": _ratio(pipe["latest_blockers"].most_common(1)[0][1], blocker_total) if pipe["latest_blockers"] else 0.0,
            },
            "outcomes": {
                "total_rows": len(out["rows"]),
                "entered_rows": len(out["entered_rows"]),
                "completed_rows": len(out["completed_rows"]),
                "open_rows": len(out["open_rows"]),
                "watching_rows": len(out["watching_rows"]),
                "expired_rows": len(out["expired_rows"]),
                "entry_rate": _ratio(len(out["entered_rows"]), pipe["candidates"]),
                "completion_rate": _ratio(len(out["completed_rows"]), len(out["entered_rows"])),
                "win_count": out["win_count"],
                "loss_count": out["loss_count"],
                "win_rate": out["win_rate"],
                "avg_profit_rate": out["avg_profit_rate"],
                "realized_pnl_krw": out["realized_pnl_krw"],
                "early_exit_count": early_exit_by_group[group],
                "early_exit_ratio": _ratio(early_exit_by_group[group], len(out["completed_rows"])),
                "top_exit_rules": _summarize_top_counts(exit_rules_by_group[group]),
            },
            "trends": (trend_by_group or {}).get(group, {}),
        })
    return strategy_rows


def _fetch_trade_history_rows(target_date: str, max_dates: int = 20) -> tuple[list[dict], list[str], list[str]]:
    warnings: list[str] = []
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    except Exception as exc:
        return [], [f"성과 추세용 DB 연결 준비 실패: {exc}"], []

    try:
        target_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
    except Exception:
        return [], [f"성과 추세 기준일 형식이 잘못되었습니다: {target_date}"], []

    recent_dates: list[str] = []
    try:
        with engine.connect() as conn:
            date_rows = conn.execute(
                text(
                    """
                    SELECT rec_date
                    FROM recommendation_history
                    WHERE rec_date <= :target_date
                    GROUP BY rec_date
                    ORDER BY rec_date DESC
                    LIMIT :limit
                    """
                ),
                {"target_date": target_date_obj, "limit": max_dates},
            ).fetchall()
            recent_dates = [_safe_date_string(row[0]) for row in date_rows if _safe_date_string(row[0])]
            if not recent_dates:
                return [], warnings, []

            oldest = min(recent_dates)
            result = conn.execute(
                text(
                    """
                    SELECT
                        rec_date, stock_code, stock_name, status, strategy,
                        buy_price, buy_qty, buy_time, sell_price, sell_time, profit_rate
                    FROM recommendation_history
                    WHERE rec_date >= :oldest_date AND rec_date <= :target_date
                    ORDER BY rec_date DESC, COALESCE(sell_time, buy_time) DESC NULLS LAST, stock_code
                    """
                ),
                {"oldest_date": oldest, "target_date": target_date_obj},
            ).mappings().all()
    except Exception as exc:
        warnings.append(f"성과 추세 이력 조회 실패: {exc}")
        return [], warnings, []

    rows: list[dict] = []
    for row in result:
        buy_price = _safe_float(row.get("buy_price"))
        sell_price = _safe_float(row.get("sell_price"))
        buy_qty = _safe_int(row.get("buy_qty"), 0) or 0
        pnl_krw = int(round((sell_price - buy_price) * buy_qty)) if sell_price and buy_price and buy_qty else 0
        rows.append({
            "rec_date": _safe_date_string(row.get("rec_date")),
            "code": str(row.get("stock_code") or "").strip()[:6],
            "name": str(row.get("stock_name") or ""),
            "status": str(row.get("status") or ""),
            "strategy": str(row.get("strategy") or ""),
            "buy_price": buy_price,
            "buy_qty": buy_qty,
            "buy_time": str(row.get("buy_time") or ""),
            "sell_price": _safe_int(sell_price, 0) or 0,
            "sell_time": str(row.get("sell_time") or ""),
            "profit_rate": round(_safe_float(row.get("profit_rate")), 2),
            "realized_pnl_krw": pnl_krw,
        })
    return rows, warnings, recent_dates


def _summarize_trade_rows(rows: list[dict], date_count: int) -> dict:
    entered_rows = [row for row in rows if _is_entered_trade(row)]
    completed_rows = [row for row in entered_rows if str(row.get("status") or "").upper() == "COMPLETED"]
    win_count = sum(1 for row in completed_rows if _safe_float(row.get("profit_rate")) > 0)
    loss_count = sum(1 for row in completed_rows if _safe_float(row.get("profit_rate")) < 0)
    return {
        "date_count": date_count,
        "entered_rows": len(entered_rows),
        "completed_rows": len(completed_rows),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": _ratio(win_count, len(completed_rows)),
        "avg_profit_rate": round(
            sum(_safe_float(row.get("profit_rate")) for row in completed_rows) / len(completed_rows),
            2,
        ) if completed_rows else 0.0,
        "realized_pnl_krw": int(sum(_safe_int(row.get("realized_pnl_krw"), 0) or 0 for row in completed_rows)),
    }


def _trend_signal(last_5: dict, last_20: dict) -> dict:
    diff = round(float(last_5.get("avg_profit_rate", 0.0)) - float(last_20.get("avg_profit_rate", 0.0)), 2)
    win_diff = round(float(last_5.get("win_rate", 0.0)) - float(last_20.get("win_rate", 0.0)), 1)
    if last_5.get("completed_rows", 0) < 2 and last_20.get("completed_rows", 0) < 4:
        return {
            "label": "표본 부족",
            "tone": "warn",
            "comment": "종료 거래가 적어 최근 추세 해석은 가볍게 보는 편이 좋습니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    if diff >= 0.25 and win_diff >= 0.0:
        return {
            "label": "개선 추세",
            "tone": "good",
            "comment": "최근 5거래일 평균 손익이 20거래일 평균보다 개선된 상태입니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    if diff <= -0.25 and win_diff <= 0.0:
        return {
            "label": "약화 추세",
            "tone": "bad",
            "comment": "최근 5거래일 평균 손익이 20거래일 평균보다 약해져 보수적 점검이 필요합니다.",
            "avg_profit_diff": diff,
            "win_rate_diff": win_diff,
        }
    return {
        "label": "혼합 추세",
        "tone": "warn",
        "comment": "최근 성과와 장기 성과가 엇갈려, 한 항목만 보고 튜닝하기엔 애매한 상태입니다.",
        "avg_profit_diff": diff,
        "win_rate_diff": win_diff,
    }


def _build_strategy_trends(history_rows: list[dict], recent_dates: list[str]) -> dict[str, dict]:
    rows_by_group_date: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for row in history_rows:
        group = _strategy_group(row.get("strategy"))
        if group not in _STRATEGY_ORDER:
            continue
        rows_by_group_date[group][str(row.get("rec_date") or "")].append(row)

    trend_by_group: dict[str, dict] = {}
    ordered_dates = list(reversed(recent_dates))
    for group in _STRATEGY_ORDER:
        date_map = rows_by_group_date.get(group, {})
        daily_points = []
        for rec_date in ordered_dates:
            rows = date_map.get(rec_date, [])
            summary = _summarize_trade_rows(rows, 1)
            daily_points.append({
                "date": rec_date,
                "entered_rows": summary["entered_rows"],
                "completed_rows": summary["completed_rows"],
                "win_rate": summary["win_rate"],
                "avg_profit_rate": summary["avg_profit_rate"],
                "realized_pnl_krw": summary["realized_pnl_krw"],
            })

        last_5_dates = ordered_dates[-5:]
        last_20_dates = ordered_dates[-20:]
        last_5_rows = [row for rec_date in last_5_dates for row in date_map.get(rec_date, [])]
        last_20_rows = [row for rec_date in last_20_dates for row in date_map.get(rec_date, [])]
        summary_5 = _summarize_trade_rows(last_5_rows, len(last_5_dates))
        summary_20 = _summarize_trade_rows(last_20_rows, len(last_20_dates))
        trend_by_group[group] = {
            "summary_5d": summary_5,
            "summary_20d": summary_20,
            "signal": _trend_signal(summary_5, summary_20),
            "recent_points": daily_points[-5:],
        }
    return trend_by_group


def _build_auto_comments(metrics: dict, strategy_rows: list[dict]) -> list[dict]:
    comments: list[dict] = []
    by_key = {row["key"]: row for row in strategy_rows}
    scalping = by_key.get("scalping")
    swing = by_key.get("swing")

    total_completed = sum(int((row.get("outcomes") or {}).get("completed_rows", 0)) for row in strategy_rows)
    if total_completed < 3:
        comments.append({
            "tone": "warn",
            "strategy": "전체",
            "title": "성과 표본이 아직 작습니다",
            "comment": (
                f"종료 거래가 {total_completed}건이라 성과 해석이 쉽게 흔들릴 수 있습니다. "
                "오늘 값은 방향성 점검용으로 보고, 3~5거래 이상 누적되면 튜닝 결정을 더 강하게 걸어보는 편이 안전합니다."
            ),
        })

    if scalping:
        pipe = scalping["pipeline"]
        out = scalping["outcomes"]
        trends = scalping.get("trends") or {}
        trend_signal = (trends.get("signal") or {})
        top_blocker = str(pipe.get("top_blocker") or "")
        top_blocker_ratio = float(pipe.get("top_blocker_ratio") or 0.0)
        if top_blocker == "동적 체결강도" and top_blocker_ratio >= 50.0 and out.get("entered_rows", 0) <= 2:
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "스캘핑 진입 병목이 동적 체결강도에 쏠려 있습니다",
                "comment": (
                    f"최신 차단의 {top_blocker_ratio:.1f}%가 동적 체결강도이며 실제 진입은 {out.get('entered_rows', 0)}건입니다. "
                    "특히 `window_buy_value`, `buy_ratio` 문턱이 과도한지 shadow 후보와 함께 점검할 시점입니다."
                ),
            })
        if float(out.get("early_exit_ratio", 0.0) or 0.0) >= 40.0 and float(out.get("avg_profit_rate", 0.0) or 0.0) <= 0.2:
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "조기청산 비중이 높습니다",
                "comment": (
                    f"종료 거래 중 AI 조기청산 비중이 {out.get('early_exit_ratio', 0.0):.1f}%입니다. "
                    "최소 보유시간, 하방카운트 조건, AI 저점수 컷아웃 민감도를 함께 점검해볼 만합니다."
                ),
            })
        if float(metrics.get("holding_skip_ratio", 0.0) or 0.0) > 65.0 and float(out.get("avg_profit_rate", 0.0) or 0.0) <= 0.0 and out.get("completed_rows", 0) >= 2:
            comments.append({
                "tone": "bad",
                "strategy": scalping["label"],
                "title": "보유 AI skip이 높고 성과가 약합니다",
                "comment": (
                    f"보유 AI skip 비율이 {metrics.get('holding_skip_ratio', 0.0):.1f}%인데 평균 손익률이 {out.get('avg_profit_rate', 0.0):+.2f}%입니다. "
                    "skip 재사용 창이나 WS age 기준이 공격적인지 확인할 필요가 있습니다."
                ),
            })
        elif out.get("completed_rows", 0) >= 2 and float(out.get("avg_profit_rate", 0.0) or 0.0) > 0.0:
            comments.append({
                "tone": "good",
                "strategy": scalping["label"],
                "title": "현재 스캘핑 밸런스는 크게 무너지지 않았습니다",
                "comment": (
                    f"종료 {out.get('completed_rows', 0)}건 기준 평균 손익률 {out.get('avg_profit_rate', 0.0):+.2f}%입니다. "
                    "성능 최적화 수치를 더 공격적으로 움직이기보다 현재 병목이 실제 기회손실로 이어지는지 우선 관찰하는 편이 좋습니다."
                ),
            })
        if trend_signal.get("label") == "약화 추세":
            comments.append({
                "tone": "warn",
                "strategy": scalping["label"],
                "title": "스캘핑 최근 추세가 장기 평균보다 약합니다",
                "comment": (
                    f"최근 5거래일 평균 손익은 {(trends.get('summary_5d') or {}).get('avg_profit_rate', 0.0):+.2f}%로, "
                    f"20거래일 평균 {(trends.get('summary_20d') or {}).get('avg_profit_rate', 0.0):+.2f}%보다 낮습니다. "
                    "지금 완화하려는 게이트가 최근 손익 약세를 더 키우는 방향은 아닌지 같이 봐야 합니다."
                ),
            })

    if swing:
        pipe = swing["pipeline"]
        out = swing["outcomes"]
        trends = swing.get("trends") or {}
        trend_signal = (trends.get("signal") or {})
        latest_blockers = {item["label"]: item["ratio"] for item in pipe.get("latest_blockers", [])}
        gatekeeper_ratio = sum(
            item["ratio"] for item in pipe.get("latest_blockers", [])
            if str(item.get("label") or "").startswith("게이트키퍼:")
        )
        gap_ratio = float(latest_blockers.get("스윙 갭상승", 0.0) or 0.0)
        if pipe.get("candidates", 0) >= 3 and out.get("entered_rows", 0) == 0 and (gatekeeper_ratio + gap_ratio) >= 60.0:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "스윙은 정책 게이트에서 대부분 멈추고 있습니다",
                "comment": (
                    f"스윙 감시 {pipe.get('candidates', 0)}종목 중 실제 진입은 0건이며, 최신 차단의 "
                    f"{gatekeeper_ratio:.1f}%는 Gatekeeper, {gap_ratio:.1f}%는 갭상승 차단입니다. "
                    "눌림 대기 cooldown, KOSPI gap 기준, Gatekeeper 프롬프트의 보수성을 함께 재확인하는 편이 좋습니다."
                ),
            })
        if float(metrics.get("gatekeeper_fast_reuse_ratio", 0.0) or 0.0) > 60.0 and pipe.get("ai_confirmed", 0) <= 1:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "Gatekeeper fast reuse가 높은 편입니다",
                "comment": (
                    f"Gatekeeper fast reuse 비율이 {metrics.get('gatekeeper_fast_reuse_ratio', 0.0):.1f}%인데 "
                    f"스윙 AI 확답은 {pipe.get('ai_confirmed', 0)}건입니다. TTL을 낮추거나 경계 구간 재평가를 더 자주 허용할 여지가 있습니다."
                ),
            })
        if gatekeeper_ratio > 0:
            comments.append({
                "tone": "good" if gatekeeper_ratio < 50.0 else "warn",
                "strategy": swing["label"],
                "title": "Gatekeeper 액션 분포를 함께 봐야 합니다",
                "comment": (
                    "스윙은 실제 체결보다 Gatekeeper 판단 품질이 선행합니다. "
                    "특히 `눌림 대기`가 많다면 재평가 간격과 재진입 조건을, `전량 회피`가 많다면 프롬프트의 공급 우위 해석이 과한지 확인하세요."
                ),
            })
        if trend_signal.get("label") == "개선 추세" and out.get("entered_rows", 0) == 0:
            comments.append({
                "tone": "warn",
                "strategy": swing["label"],
                "title": "스윙 장기 성과는 나쁘지 않은데 오늘 진입이 막혔습니다",
                "comment": (
                    f"최근 5거래일 평균 손익이 {(trends.get('summary_5d') or {}).get('avg_profit_rate', 0.0):+.2f}%로 개선 추세인데, "
                    f"오늘 실제 스윙 진입은 {out.get('entered_rows', 0)}건입니다. "
                    "Gatekeeper 보수성이나 gap 기준이 최근 장세 대비 과한지 다시 점검해볼 만합니다."
                ),
            })

    if float(metrics.get("gatekeeper_eval_ms_p95", 0.0) or 0.0) > 1200.0:
        comments.append({
            "tone": "warn",
            "strategy": "전체",
            "title": "Gatekeeper 평가 시간이 길어지고 있습니다",
            "comment": (
                f"Gatekeeper 평가 p95가 {metrics.get('gatekeeper_eval_ms_p95', 0.0):.0f}ms입니다. "
                "프롬프트 입력값이 너무 많아졌는지, fast reuse가 충분히 작동하는지 함께 점검해볼 만합니다."
            ),
        })

    return comments


def _build_watch_items(metrics: dict) -> list[dict]:
    hold_skip_ratio = float(metrics.get("holding_skip_ratio", 0.0) or 0.0)
    hold_ws_p95 = float(metrics.get("holding_skip_ws_age_p95", 0.0) or 0.0)
    gate_eval_p95 = float(metrics.get("gatekeeper_eval_ms_p95", 0.0) or 0.0)
    gate_fast_ratio = float(metrics.get("gatekeeper_fast_reuse_ratio", 0.0) or 0.0)
    gate_ws_p95 = float(metrics.get("gatekeeper_fast_reuse_ws_age_p95", 0.0) or 0.0)
    ai_hit_ratio = float(metrics.get("holding_ai_cache_hit_ratio", 0.0) or 0.0)

    hold_ws_warn = float(getattr(TRADING_RULES, "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC", 1.5) or 1.5)
    gate_ws_warn = float(getattr(TRADING_RULES, "AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC", 2.0) or 2.0)

    items: list[dict] = []

    items.append({
        "label": "보유 AI skip 비율",
        "value": f"{hold_skip_ratio:.1f}%",
        "target": "20% ~ 60%",
        "tone": "warn" if hold_skip_ratio < 15.0 or hold_skip_ratio > 70.0 else "good",
        "comment": "너무 낮으면 비용 절감이 약하고, 너무 높으면 stale 리스크를 점검해야 합니다.",
    })
    items.append({
        "label": "보유 AI skip WS age p95",
        "value": f"{hold_ws_p95:.2f}s",
        "target": f"<= {hold_ws_warn:.2f}s",
        "tone": "bad" if hold_ws_p95 > hold_ws_warn else "good",
        "comment": "skip 시점의 웹소켓 나이가 길면 최신성이 부족할 수 있습니다.",
    })
    items.append({
        "label": "Gatekeeper 평가 p95",
        "value": f"{gate_eval_p95:.0f}ms",
        "target": "< 1200ms",
        "tone": "warn" if gate_eval_p95 > 1200 else "good",
        "comment": "높을수록 컨텍스트 생성 또는 AI 응답이 무거운 상태입니다.",
    })
    items.append({
        "label": "Gatekeeper fast reuse 비율",
        "value": f"{gate_fast_ratio:.1f}%",
        "target": "15% ~ 55%",
        "tone": "warn" if gate_fast_ratio < 10.0 or gate_fast_ratio > 65.0 else "good",
        "comment": "너무 낮으면 최적화 효과가 적고, 너무 높으면 같은 판단을 오래 재사용할 수 있습니다.",
    })
    items.append({
        "label": "Gatekeeper fast reuse WS age p95",
        "value": f"{gate_ws_p95:.2f}s",
        "target": f"<= {gate_ws_warn:.2f}s",
        "tone": "bad" if gate_ws_p95 > gate_ws_warn else "good",
        "comment": "fast reuse가 stale WS 위에서 일어나지 않는지 확인합니다.",
    })
    items.append({
        "label": "보유 AI 결과 cache hit",
        "value": f"{ai_hit_ratio:.1f}%",
        "target": "10% ~ 50%",
        "tone": "warn" if ai_hit_ratio < 5.0 or ai_hit_ratio > 70.0 else "good",
        "comment": "높다고 무조건 좋은 건 아닙니다. 너무 높으면 같은 판단 반복일 수 있습니다.",
    })
    return items


def build_performance_tuning_report(*, target_date: str, since_time: str | None = None) -> dict:
    log_path = LOGS_DIR / "sniper_state_handlers_info.log"
    entry_lines = _iter_target_lines(log_path, target_date=target_date, marker="[ENTRY_PIPELINE]")
    holding_lines = _iter_target_lines(log_path, target_date=target_date, marker="[HOLDING_PIPELINE]")

    entry_events = [event for line in entry_lines if (event := _parse_event(line, _ENTRY_RE))]
    holding_events = [event for line in holding_lines if (event := _parse_event(line, _HOLDING_RE))]

    since_dt = _parse_since_datetime(target_date, since_time)
    if since_dt is not None:
        entry_events = [e for e in entry_events if datetime.strptime(e.timestamp, "%Y-%m-%d %H:%M:%S") >= since_dt]
        holding_events = [e for e in holding_events if datetime.strptime(e.timestamp, "%Y-%m-%d %H:%M:%S") >= since_dt]

    holding_reviews = [e for e in holding_events if e.stage == "ai_holding_review"]
    holding_skips = [e for e in holding_events if e.stage == "ai_holding_skip_unchanged"]
    exit_signals = [e for e in holding_events if e.stage == "exit_signal"]
    gatekeeper_decisions = [e for e in entry_events if e.stage in _GATEKEEPER_DECISION_STAGES]
    gatekeeper_fast_reuse = [e for e in entry_events if e.stage == "gatekeeper_fast_reuse"]

    holding_review_ms = [float(v) for e in holding_reviews if (v := _safe_float(e.fields.get("review_ms"))) is not None]
    holding_skip_ws_ages = [float(v) for e in holding_skips if (v := _safe_float(e.fields.get("ws_age_sec"))) is not None]
    gatekeeper_eval_ms = [float(v) for e in gatekeeper_decisions if (v := _safe_float(e.fields.get("gatekeeper_eval_ms"))) is not None]
    gatekeeper_fast_ws_ages = [float(v) for e in gatekeeper_fast_reuse if (v := _safe_float(e.fields.get("ws_age_sec"))) is not None]

    holding_ai_cache_modes = Counter(str(e.fields.get("ai_cache", "miss") or "miss") for e in holding_reviews)
    gatekeeper_cache_modes = Counter(str(e.fields.get("gatekeeper_cache", "miss") or "miss") for e in gatekeeper_decisions)
    gatekeeper_actions = Counter(str(e.fields.get("action", "UNKNOWN") or "UNKNOWN") for e in gatekeeper_decisions if e.stage == "blocked_gatekeeper_reject")
    exit_rule_counts = Counter(str(e.fields.get("exit_rule", "-") or "-") for e in exit_signals)
    trade_rows, trade_warnings = _build_current_trade_rows(target_date)
    history_rows, history_warnings, recent_history_dates = _fetch_trade_history_rows(target_date)
    trend_by_group = _build_strategy_trends(history_rows, recent_history_dates)

    holding_reuse_blockers = Counter()
    for event in holding_events:
        if event.stage != "ai_holding_reuse_bypass":
            continue
        for reason_code in _split_reason_codes(event.fields.get("reason_codes")):
            holding_reuse_blockers[_friendly_reason_name(reason_code)] += 1

    gatekeeper_reuse_blockers = Counter()
    for event in entry_events:
        if event.stage != "gatekeeper_fast_reuse_bypass":
            continue
        for reason_code in _split_reason_codes(event.fields.get("reason_codes")):
            gatekeeper_reuse_blockers[_friendly_reason_name(reason_code)] += 1

    total_holding_samples = len(holding_reviews) + len(holding_skips)
    total_gatekeeper_samples = len(gatekeeper_decisions)
    holding_ai_cache_hit_count = holding_ai_cache_modes.get("hit", 0)
    gatekeeper_fast_reuse_count = gatekeeper_cache_modes.get("fast_reuse", 0)
    gatekeeper_ai_cache_hit_count = gatekeeper_cache_modes.get("hit", 0)

    metrics = {
        "holding_reviews": len(holding_reviews),
        "holding_skips": len(holding_skips),
        "holding_skip_ratio": _ratio(len(holding_skips), total_holding_samples),
        "holding_ai_cache_hit_ratio": _ratio(holding_ai_cache_hit_count, len(holding_reviews)),
        "holding_review_ms_avg": _avg(holding_review_ms),
        "holding_review_ms_p95": round(_percentile(holding_review_ms, 95), 2),
        "holding_skip_ws_age_p95": round(_percentile(holding_skip_ws_ages, 95), 2),
        "gatekeeper_decisions": total_gatekeeper_samples,
        "gatekeeper_fast_reuse_ratio": _ratio(gatekeeper_fast_reuse_count, total_gatekeeper_samples),
        "gatekeeper_ai_cache_hit_ratio": _ratio(gatekeeper_ai_cache_hit_count, total_gatekeeper_samples),
        "gatekeeper_eval_ms_avg": _avg(gatekeeper_eval_ms),
        "gatekeeper_eval_ms_p95": round(_percentile(gatekeeper_eval_ms, 95), 2),
        "gatekeeper_fast_reuse_ws_age_p95": round(_percentile(gatekeeper_fast_ws_ages, 95), 2),
        "exit_signals": len(exit_signals),
    }

    cards = [
        _metric_card("보유 AI 리뷰", f"{metrics['holding_reviews']}건", "실제 AI 재평가"),
        _metric_card("보유 AI skip", f"{metrics['holding_skips']}건", "시장상태 동일로 생략"),
        _metric_card("보유 AI p95", f"{metrics['holding_review_ms_p95']:.0f}ms", "리뷰 지연 상위 5%"),
        _metric_card("Gatekeeper 결정", f"{metrics['gatekeeper_decisions']}건", "실제 허용/보류 판단"),
        _metric_card("Gatekeeper fast reuse", f"{metrics['gatekeeper_fast_reuse_ratio']:.1f}%", "같은 장면 재사용 비율"),
        _metric_card("Gatekeeper p95", f"{metrics['gatekeeper_eval_ms_p95']:.0f}ms", "평가 지연 상위 5%"),
    ]

    strategy_rows = _build_strategy_outcomes(
        entry_events=entry_events,
        holding_events=holding_events,
        trade_rows=trade_rows,
        trend_by_group=trend_by_group,
    )
    auto_comments = _build_auto_comments(metrics, strategy_rows)

    top_holding_slow = sorted(
        [
            {
                "timestamp": e.timestamp,
                "name": e.name,
                "code": e.code,
                "review_ms": _safe_int(e.fields.get("review_ms"), 0) or 0,
                "profit_rate": e.fields.get("profit_rate", ""),
                "ai_cache": e.fields.get("ai_cache", "miss"),
            }
            for e in holding_reviews
        ],
        key=lambda item: item["review_ms"],
        reverse=True,
    )[:8]

    top_gatekeeper_slow = sorted(
        [
            {
                "timestamp": e.timestamp,
                "name": e.name,
                "code": e.code,
                "gatekeeper_eval_ms": _safe_int(e.fields.get("gatekeeper_eval_ms"), 0) or 0,
                "cache": e.fields.get("gatekeeper_cache", "miss"),
                "action": e.fields.get("action", e.fields.get("gatekeeper", "")),
            }
            for e in gatekeeper_decisions
        ],
        key=lambda item: item["gatekeeper_eval_ms"],
        reverse=True,
    )[:8]

    return {
        "date": target_date,
        "since": since_time,
        "metrics": metrics,
        "cards": cards,
        "watch_items": _build_watch_items(metrics),
        "strategy_rows": strategy_rows,
        "auto_comments": auto_comments,
        "meta": {
            "warnings": trade_warnings + history_warnings,
            "outcome_basis": "기준일 누적 성과 (trade review 정규화)",
            "engine_basis": "조회 구간 엔진 지표",
            "trend_basis": f"최근 {len(recent_history_dates)}개 거래일 rolling 성과" if recent_history_dates else "최근 거래일 rolling 성과",
        },
        "breakdowns": {
            "holding_ai_cache_modes": [{"label": key, "count": value} for key, value in holding_ai_cache_modes.most_common()],
            "holding_reuse_blockers": [{"label": key, "count": value} for key, value in holding_reuse_blockers.most_common()],
            "gatekeeper_cache_modes": [{"label": key, "count": value} for key, value in gatekeeper_cache_modes.most_common()],
            "gatekeeper_reuse_blockers": [{"label": key, "count": value} for key, value in gatekeeper_reuse_blockers.most_common()],
            "gatekeeper_actions": [{"label": key, "count": value} for key, value in gatekeeper_actions.most_common()],
            "exit_rules": [{"label": key, "count": value} for key, value in exit_rule_counts.most_common()],
        },
        "sections": {
            "top_holding_slow": top_holding_slow,
            "top_gatekeeper_slow": top_gatekeeper_slow,
        },
    }
