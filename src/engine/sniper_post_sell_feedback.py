"""Post-sell candidate recording and post-close evaluation."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info


_WRITE_LOCK = threading.RLock()
_RECORDED_KEYS: dict[tuple[str, str, str, str], float] = {}
_WS_RETAIN_UNTIL: dict[str, float] = {}
POST_SELL_REPORT_SCHEMA_VERSION = 1


def _post_sell_dir() -> Path:
    path = DATA_DIR / "post_sell"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _candidate_path(target_date: str) -> Path:
    return _post_sell_dir() / f"post_sell_candidates_{target_date}.jsonl"


def _evaluation_path(target_date: str) -> Path:
    return _post_sell_dir() / f"post_sell_evaluations_{target_date}.jsonl"


def _append_jsonl(path: Path, payload: dict) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _parse_datetime(value, default: datetime | None = None) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "None"):
        return default
    candidate = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(candidate, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(candidate)
    except Exception:
        return default


def _minute_bucket(ts: datetime, bucket_min: int = 1) -> str:
    floored_min = (ts.minute // bucket_min) * bucket_min
    return ts.replace(minute=floored_min, second=0, microsecond=0).strftime("%H:%M")


def _safe_int(value, default: int = 0) -> int:
    try:
        if value in (None, "", "None"):
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 1)


def _avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 3)


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(item) for item in values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return round(ordered[mid], 3)
    return round((ordered[mid - 1] + ordered[mid]) / 2.0, 3)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def should_retain_ws_subscription(code: str, now_ts: float | None = None) -> bool:
    normalized = str(code or "").strip()[:6]
    if not normalized:
        return False

    current_ts = float(now_ts if now_ts is not None else time.time())
    with _WRITE_LOCK:
        until_ts = float(_WS_RETAIN_UNTIL.get(normalized, 0.0) or 0.0)
        if until_ts <= current_ts:
            _WS_RETAIN_UNTIL.pop(normalized, None)
            return False
        return True


def record_post_sell_candidate(
    *,
    recommendation_id=None,
    stock: dict | None = None,
    code: str | None = None,
    sell_time=None,
    buy_price=0,
    sell_price=0,
    profit_rate=0,
    buy_qty=0,
    exit_rule: str | None = None,
    strategy: str | None = None,
    revive: bool = False,
) -> dict | None:
    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_ENABLED", True)):
        return None

    stock = stock or {}
    norm_code = str(code or stock.get("code") or "").strip()[:6]
    if not norm_code:
        return None

    safe_sell_price = _safe_int(sell_price, 0)
    if safe_sell_price <= 0:
        return None

    now = datetime.now()
    sell_dt = _parse_datetime(sell_time, default=now) or now
    target_date = sell_dt.strftime("%Y-%m-%d")
    sell_bucket = _minute_bucket(sell_dt, bucket_min=1)
    rec_id_text = str(_safe_int(recommendation_id, 0))
    dedupe_marker = rec_id_text if rec_id_text != "0" else f"{sell_bucket}:{safe_sell_price}"
    dedupe_key = (
        target_date,
        norm_code,
        rec_id_text,
        dedupe_marker,
    )

    with _WRITE_LOCK:
        if dedupe_key in _RECORDED_KEYS:
            return None

        payload = {
            "post_sell_id": uuid.uuid4().hex[:16],
            "recorded_at": now.isoformat(),
            "signal_date": target_date,
            "recommendation_id": _safe_int(recommendation_id, 0),
            "sell_time": sell_dt.strftime("%H:%M:%S"),
            "sell_bucket": sell_bucket,
            "stock_code": norm_code,
            "stock_name": str(stock.get("name", "") or ""),
            "strategy": str(strategy or stock.get("strategy", "") or ""),
            "position_tag": str(stock.get("position_tag", "") or ""),
            "buy_price": _safe_int(buy_price, 0),
            "sell_price": safe_sell_price,
            "profit_rate": round(_safe_float(profit_rate, 0.0), 3),
            "buy_qty": _safe_int(buy_qty, 0),
            "exit_rule": str(exit_rule or stock.get("last_exit_rule") or "-"),
            "revive": bool(revive),
            "evaluation_mode": "post_sell_minute_forward",
        }

        _append_jsonl(_candidate_path(target_date), payload)
        _RECORDED_KEYS[dedupe_key] = now.timestamp()
        retain_minutes = int(getattr(TRADING_RULES, "POST_SELL_WS_RETAIN_MINUTES", 0) or 0)
        if retain_minutes > 0:
            retain_until = sell_dt.timestamp() + (retain_minutes * 60.0)
            current_until = float(_WS_RETAIN_UNTIL.get(norm_code, 0.0) or 0.0)
            if retain_until > current_until:
                _WS_RETAIN_UNTIL[norm_code] = retain_until
        log_info(
            f"[POST_SELL_CANDIDATE] {payload['stock_name']}({payload['stock_code']}) "
            f"sell={payload['sell_price']} ret={payload['profit_rate']:+.2f}% "
            f"exit_rule={payload['exit_rule']} revive={payload['revive']}"
        )
        return payload


def _parse_minute_time(value: str, signal_date: str) -> datetime | None:
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _compute_window_metrics(candidate: dict, candles: list[dict], window_minutes: int) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['sell_time']}",
        "%Y-%m-%d %H:%M:%S",
    )
    start_dt = signal_dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
    end_dt = start_dt + timedelta(minutes=window_minutes)

    relevant = []
    for candle in candles:
        candle_dt = _parse_minute_time(str(candle.get("체결시간", "") or ""), candidate["signal_date"])
        if candle_dt is None:
            continue
        if candle_dt < start_dt or candle_dt >= end_dt:
            continue
        relevant.append((candle_dt, candle))

    sell_price = float(candidate.get("sell_price", 0) or 0)
    if sell_price <= 0 or not relevant:
        return {
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "hit_up_05": False,
            "hit_up_10": False,
            "hit_down_05": False,
            "bars": len(relevant),
        }

    highs = []
    lows = []
    close_ret = 0.0

    for _, candle in relevant:
        high_p = float(candle.get("고가", 0) or 0)
        low_p = float(candle.get("저가", 0) or 0)
        close_p = float(candle.get("현재가", 0) or 0)

        if high_p > 0:
            highs.append(((high_p / sell_price) - 1.0) * 100.0)
        if low_p > 0:
            lows.append(((low_p / sell_price) - 1.0) * 100.0)
        if close_p > 0:
            close_ret = ((close_p / sell_price) - 1.0) * 100.0

    mfe_pct = max(highs) if highs else 0.0
    mae_pct = min(lows) if lows else 0.0
    return {
        "close_ret_pct": round(close_ret, 3),
        "mfe_pct": round(mfe_pct, 3),
        "mae_pct": round(mae_pct, 3),
        "hit_up_05": mfe_pct >= 0.5,
        "hit_up_10": mfe_pct >= 1.0,
        "hit_down_05": mae_pct <= -0.5,
        "bars": len(relevant),
    }


def _classify_candidate(metrics_10m: dict) -> str:
    missed_mfe = float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT", 0.8) or 0.8)
    missed_close = float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT", 0.3) or 0.3)
    good_mae = float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6) or -0.6)
    good_close = float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT", -0.2) or -0.2)

    mfe = float(metrics_10m.get("mfe_pct", 0.0) or 0.0)
    mae = float(metrics_10m.get("mae_pct", 0.0) or 0.0)
    close_ret = float(metrics_10m.get("close_ret_pct", 0.0) or 0.0)

    if mfe >= missed_mfe and close_ret >= missed_close:
        return "MISSED_UPSIDE"
    if mae <= good_mae and close_ret <= good_close:
        return "GOOD_EXIT"
    return "NEUTRAL"


@dataclass
class PostSellFeedbackSummary:
    date: str
    total_candidates: int = 0
    evaluated_candidates: int = 0
    outcome_counts: dict[str, int] = field(default_factory=dict)
    missed_upside_cases: list[dict] = field(default_factory=list)
    good_exit_cases: list[dict] = field(default_factory=list)


def evaluate_post_sell_candidates(target_date: str, token: str | None = None) -> PostSellFeedbackSummary:
    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[POST_SELL_EVAL] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    candidates = _load_jsonl(_candidate_path(target_date))
    existing_evaluations = _load_jsonl(_evaluation_path(target_date))
    evaluated_ids = {str(item.get("post_sell_id", "")) for item in existing_evaluations}
    summary = PostSellFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)

    if not bool(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_EVAL_ENABLED", True)):
        summary.evaluated_candidates = len(existing_evaluations)
        return summary

    candle_cache: dict[str, list[dict]] = {}
    new_evaluations: list[dict] = []
    token_fetch_attempted = token is not None

    for candidate in candidates:
        post_sell_id = str(candidate.get("post_sell_id", "") or "")
        code = str(candidate.get("stock_code", "") or "")
        if not post_sell_id or not code or post_sell_id in evaluated_ids or kiwoom_utils is None:
            continue

        if token is None and not token_fetch_attempted:
            token_fetch_attempted = True
            try:
                token = kiwoom_utils.get_kiwoom_token()
            except Exception as exc:
                log_error(f"[POST_SELL_EVAL] token fetch failed: {exc}")
                token = None

        if token is None:
            continue

        if code not in candle_cache:
            try:
                candle_cache[code] = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=700) or []
            except Exception as exc:
                log_error(f"[POST_SELL_EVAL] {code} minute candles fetch failed: {exc}")
                candle_cache[code] = []

        candles = candle_cache.get(code, [])
        metrics_1m = _compute_window_metrics(candidate, candles, 1)
        metrics_3m = _compute_window_metrics(candidate, candles, 3)
        metrics_5m = _compute_window_metrics(candidate, candles, 5)
        metrics_10m = _compute_window_metrics(candidate, candles, 10)
        metrics_20m = _compute_window_metrics(candidate, candles, 20)
        outcome = _classify_candidate(metrics_10m)

        evaluation = {
            "post_sell_id": post_sell_id,
            "evaluated_at": datetime.now().isoformat(),
            "signal_date": target_date,
            "stock_code": code,
            "stock_name": candidate.get("stock_name", ""),
            "recommendation_id": candidate.get("recommendation_id", 0),
            "strategy": candidate.get("strategy", ""),
            "position_tag": candidate.get("position_tag", ""),
            "sell_time": candidate.get("sell_time", ""),
            "sell_bucket": candidate.get("sell_bucket", ""),
            "buy_price": candidate.get("buy_price", 0),
            "sell_price": candidate.get("sell_price", 0),
            "profit_rate": candidate.get("profit_rate", 0.0),
            "buy_qty": candidate.get("buy_qty", 0),
            "exit_rule": candidate.get("exit_rule", "-"),
            "revive": bool(candidate.get("revive", False)),
            "outcome": outcome,
            "metrics_1m": metrics_1m,
            "metrics_3m": metrics_3m,
            "metrics_5m": metrics_5m,
            "metrics_10m": metrics_10m,
            "metrics_20m": metrics_20m,
        }
        new_evaluations.append(evaluation)

    if new_evaluations:
        with _WRITE_LOCK:
            path = _evaluation_path(target_date)
            for item in new_evaluations:
                _append_jsonl(path, item)

    all_evaluations = existing_evaluations + new_evaluations
    summary.evaluated_candidates = len(all_evaluations)

    outcome_counts: dict[str, int] = {"MISSED_UPSIDE": 0, "GOOD_EXIT": 0, "NEUTRAL": 0}
    for item in all_evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts

    summary.missed_upside_cases = sorted(
        [item for item in all_evaluations if str(item.get("outcome", "")).upper() == "MISSED_UPSIDE"],
        key=lambda item: float((item.get("metrics_10m", {}) or {}).get("mfe_pct", 0.0) or 0.0),
        reverse=True,
    )[:5]
    summary.good_exit_cases = sorted(
        [item for item in all_evaluations if str(item.get("outcome", "")).upper() == "GOOD_EXIT"],
        key=lambda item: float((item.get("metrics_10m", {}) or {}).get("mae_pct", 0.0) or 0.0),
    )[:5]
    return summary


def post_sell_feedback_summary_to_dict(summary: PostSellFeedbackSummary) -> dict:
    return {
        "date": summary.date,
        "total_candidates": int(summary.total_candidates),
        "evaluated_candidates": int(summary.evaluated_candidates),
        "outcome_counts": dict(summary.outcome_counts or {}),
        "missed_upside_cases": list(summary.missed_upside_cases or []),
        "good_exit_cases": list(summary.good_exit_cases or []),
    }


def format_post_sell_feedback_summary(summary: PostSellFeedbackSummary) -> str:
    if summary.total_candidates <= 0:
        return f"📉 post-sell 피드백 ({summary.date})\n- 후보 기록 없음"

    lines = [
        f"📉 post-sell 피드백 ({summary.date})",
        f"- 매도 후보 기록: {summary.total_candidates}건",
        f"- 평가 완료: {summary.evaluated_candidates}건",
        f"- 결과 분포: MISSED_UPSIDE {summary.outcome_counts.get('MISSED_UPSIDE', 0)} / "
        f"GOOD_EXIT {summary.outcome_counts.get('GOOD_EXIT', 0)} / "
        f"NEUTRAL {summary.outcome_counts.get('NEUTRAL', 0)}",
    ]

    if summary.missed_upside_cases:
        lines.append("- 상위 missed upside:")
        for item in summary.missed_upside_cases[:3]:
            metrics = item.get("metrics_10m", {}) or {}
            lines.append(
                f"  {item.get('stock_name')}({item.get('stock_code')}) "
                f"MFE10m {float(metrics.get('mfe_pct', 0.0) or 0.0):+.2f}% / "
                f"Close10m {float(metrics.get('close_ret_pct', 0.0) or 0.0):+.2f}% "
                f"(exit_rule={item.get('exit_rule', '-')})"
            )
    return "\n".join(lines)


def _build_summary_from_raw_rows(
    *,
    target_date: str,
    candidates: list[dict],
    evaluations: list[dict],
) -> PostSellFeedbackSummary:
    summary = PostSellFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)
    summary.evaluated_candidates = len(evaluations)

    outcome_counts: dict[str, int] = {"MISSED_UPSIDE": 0, "GOOD_EXIT": 0, "NEUTRAL": 0}
    for item in evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts

    summary.missed_upside_cases = sorted(
        [item for item in evaluations if str(item.get("outcome", "")).upper() == "MISSED_UPSIDE"],
        key=lambda item: float((item.get("metrics_10m", {}) or {}).get("mfe_pct", 0.0) or 0.0),
        reverse=True,
    )[:5]
    summary.good_exit_cases = sorted(
        [item for item in evaluations if str(item.get("outcome", "")).upper() == "GOOD_EXIT"],
        key=lambda item: float((item.get("metrics_10m", {}) or {}).get("mae_pct", 0.0) or 0.0),
    )[:5]
    return summary


def _enrich_post_sell_rows(
    *,
    candidates: list[dict],
    evaluations: list[dict],
) -> list[dict]:
    candidate_by_id = {
        str(item.get("post_sell_id", "") or ""): dict(item)
        for item in (candidates or [])
        if item.get("post_sell_id")
    }
    rows: list[dict] = []
    for item in evaluations:
        post_sell_id = str(item.get("post_sell_id", "") or "")
        candidate = candidate_by_id.get(post_sell_id, {})
        metrics_10m = dict(item.get("metrics_10m") or {})
        mfe_10m = _safe_float(metrics_10m.get("mfe_pct"), 0.0)
        mae_10m = _safe_float(metrics_10m.get("mae_pct"), 0.0)
        close_10m = _safe_float(metrics_10m.get("close_ret_pct"), 0.0)
        profit_rate = _safe_float(item.get("profit_rate", candidate.get("profit_rate")), 0.0)
        sell_price = _safe_float(item.get("sell_price", candidate.get("sell_price")), 0.0)
        buy_price = _safe_float(item.get("buy_price", candidate.get("buy_price")), 0.0)
        buy_qty = _safe_int(item.get("buy_qty", candidate.get("buy_qty")), 0)
        extra_upside_pct = max(0.0, mfe_10m)
        extra_upside_krw_est = int(round(sell_price * buy_qty * (extra_upside_pct / 100.0))) if sell_price > 0 and buy_qty > 0 else 0
        potential_peak_profit_rate = round(profit_rate + extra_upside_pct, 3)
        capture_efficiency_pct = (
            round(_clamp((profit_rate / potential_peak_profit_rate) * 100.0, 0.0, 100.0), 1)
            if potential_peak_profit_rate > 0
            else 0.0
        )
        rows.append(
            {
                "post_sell_id": post_sell_id,
                "signal_date": str(item.get("signal_date") or candidate.get("signal_date") or ""),
                "stock_code": str(item.get("stock_code") or candidate.get("stock_code") or ""),
                "stock_name": str(item.get("stock_name") or candidate.get("stock_name") or ""),
                "recommendation_id": _safe_int(item.get("recommendation_id", candidate.get("recommendation_id")), 0),
                "strategy": str(item.get("strategy") or candidate.get("strategy") or ""),
                "position_tag": str(item.get("position_tag") or candidate.get("position_tag") or ""),
                "sell_time": str(item.get("sell_time") or candidate.get("sell_time") or ""),
                "sell_bucket": str(item.get("sell_bucket") or candidate.get("sell_bucket") or ""),
                "buy_price": int(round(buy_price)),
                "sell_price": int(round(sell_price)),
                "buy_qty": int(buy_qty),
                "profit_rate": round(profit_rate, 3),
                "exit_rule": str(item.get("exit_rule") or candidate.get("exit_rule") or "-"),
                "revive": bool(item.get("revive", candidate.get("revive", False))),
                "outcome": str(item.get("outcome") or "NEUTRAL").upper(),
                "mfe_10m_pct": round(mfe_10m, 3),
                "mae_10m_pct": round(mae_10m, 3),
                "close_10m_pct": round(close_10m, 3),
                "extra_upside_10m_pct": round(extra_upside_pct, 3),
                "extra_upside_10m_krw_est": int(extra_upside_krw_est),
                "potential_peak_profit_rate_10m": float(potential_peak_profit_rate),
                "capture_efficiency_pct": float(capture_efficiency_pct),
                "metrics_10m": metrics_10m,
            }
        )
    return rows


def _build_exit_rule_tuning_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get("exit_rule") or "-")].append(row)

    result: list[dict] = []
    for exit_rule, items in grouped.items():
        trades = len(items)
        missed_count = sum(1 for item in items if str(item.get("outcome") or "") == "MISSED_UPSIDE")
        good_count = sum(1 for item in items if str(item.get("outcome") or "") == "GOOD_EXIT")
        avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in items])
        avg_mfe = _avg([_safe_float(item.get("mfe_10m_pct"), 0.0) for item in items])
        avg_mae = _avg([_safe_float(item.get("mae_10m_pct"), 0.0) for item in items])
        avg_close = _avg([_safe_float(item.get("close_10m_pct"), 0.0) for item in items])
        avg_capture = _avg([
            _safe_float(item.get("capture_efficiency_pct"), 0.0)
            for item in items
            if _safe_float(item.get("potential_peak_profit_rate_10m"), 0.0) > 0.0
        ])
        est_extra_krw = int(sum(_safe_int(item.get("extra_upside_10m_krw_est"), 0) for item in items))
        missed_rate = _ratio(missed_count, trades)
        good_rate = _ratio(good_count, trades)
        follow_up_rate = _ratio(sum(1 for item in items if _safe_float(item.get("close_10m_pct"), 0.0) >= 0.2), trades)
        tuning_score = _clamp(
            (missed_rate * 0.60)
            + _clamp(max(avg_close, 0.0) * 40.0, 0.0, 25.0)
            + _clamp(max(avg_mfe, 0.0) * 12.0, 0.0, 15.0)
            - _clamp(good_rate * 0.20, 0.0, 15.0),
            0.0,
            100.0,
        )
        if trades < 2:
            tuning_hint = "표본 부족: 2건 이상 누적 후 미세조정 권장"
        elif tuning_score >= 65.0:
            tuning_hint = "우선 점검: 익절 지연/분할청산 shadow 테스트 후보"
        elif good_rate >= 45.0 and avg_mae <= -0.5:
            tuning_hint = "손실 회피 기여가 확인됨: 과도 완화 주의"
        elif avg_mfe >= 1.0 and avg_close < 0.1:
            tuning_hint = "고점 회수보다 트레일링/재진입 규칙 보정이 유리"
        else:
            tuning_hint = "현행 유지 + 표본 추가 관찰"

        result.append(
            {
                "exit_rule": exit_rule,
                "trades": trades,
                "missed_upside_count": missed_count,
                "good_exit_count": good_count,
                "missed_upside_rate": missed_rate,
                "good_exit_rate": good_rate,
                "follow_up_10m_rate": follow_up_rate,
                "avg_profit_rate": avg_profit,
                "avg_mfe_10m_pct": avg_mfe,
                "avg_mae_10m_pct": avg_mae,
                "avg_close_10m_pct": avg_close,
                "avg_capture_efficiency_pct": avg_capture,
                "estimated_extra_upside_10m_krw": est_extra_krw,
                "tuning_pressure_score": round(tuning_score, 1),
                "tuning_hint": tuning_hint,
            }
        )

    return sorted(
        result,
        key=lambda item: (
            float(item.get("tuning_pressure_score", 0.0) or 0.0),
            int(item.get("trades", 0) or 0),
            int(item.get("estimated_extra_upside_10m_krw", 0) or 0),
        ),
        reverse=True,
    )


def _build_tag_tuning_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        strategy = str(row.get("strategy") or "-")
        position_tag = str(row.get("position_tag") or "-")
        grouped[(strategy, position_tag)].append(row)

    result: list[dict] = []
    for (strategy, position_tag), items in grouped.items():
        trades = len(items)
        missed_count = sum(1 for item in items if str(item.get("outcome") or "") == "MISSED_UPSIDE")
        good_count = sum(1 for item in items if str(item.get("outcome") or "") == "GOOD_EXIT")
        avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in items])
        avg_close = _avg([_safe_float(item.get("close_10m_pct"), 0.0) for item in items])
        avg_mfe = _avg([_safe_float(item.get("mfe_10m_pct"), 0.0) for item in items])
        result.append(
            {
                "strategy": strategy,
                "position_tag": position_tag,
                "trades": trades,
                "missed_upside_rate": _ratio(missed_count, trades),
                "good_exit_rate": _ratio(good_count, trades),
                "avg_profit_rate": avg_profit,
                "avg_close_10m_pct": avg_close,
                "avg_mfe_10m_pct": avg_mfe,
                "estimated_extra_upside_10m_krw": int(sum(_safe_int(item.get("extra_upside_10m_krw_est"), 0) for item in items)),
            }
        )
    return sorted(
        result,
        key=lambda item: (
            float(item.get("missed_upside_rate", 0.0) or 0.0),
            float(item.get("avg_close_10m_pct", 0.0) or 0.0),
            int(item.get("trades", 0) or 0),
        ),
        reverse=True,
    )


def _build_priority_actions(exit_rule_rows: list[dict], limit: int = 3) -> list[dict]:
    actions: list[dict] = []
    for row in exit_rule_rows:
        trades = int(row.get("trades", 0) or 0)
        tuning_score = float(row.get("tuning_pressure_score", 0.0) or 0.0)
        if trades < 2 or tuning_score < 55.0:
            continue
        actions.append(
            {
                "exit_rule": str(row.get("exit_rule") or "-"),
                "tuning_pressure_score": round(tuning_score, 1),
                "reason": (
                    f"missed {float(row.get('missed_upside_rate', 0.0) or 0.0):.1f}% / "
                    f"close10m {float(row.get('avg_close_10m_pct', 0.0) or 0.0):+.2f}% / "
                    f"예상추가수익 {int(row.get('estimated_extra_upside_10m_krw', 0) or 0):,}원"
                ),
                "suggested_test": str(row.get("tuning_hint") or ""),
            }
        )
        if len(actions) >= max(1, int(limit or 3)):
            break

    if actions:
        return actions

    return [
        {
            "exit_rule": "-",
            "tuning_pressure_score": 0.0,
            "reason": "당일 데이터에서 즉시 미세조정이 필요한 강한 신호가 없습니다.",
            "suggested_test": "표본 추가 후 재평가",
        }
    ]


def _case_view(row: dict) -> dict:
    return {
        "post_sell_id": str(row.get("post_sell_id") or ""),
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "strategy": str(row.get("strategy") or ""),
        "position_tag": str(row.get("position_tag") or ""),
        "exit_rule": str(row.get("exit_rule") or "-"),
        "profit_rate": round(_safe_float(row.get("profit_rate"), 0.0), 3),
        "mfe_10m_pct": round(_safe_float(row.get("mfe_10m_pct"), 0.0), 3),
        "mae_10m_pct": round(_safe_float(row.get("mae_10m_pct"), 0.0), 3),
        "close_10m_pct": round(_safe_float(row.get("close_10m_pct"), 0.0), 3),
        "extra_upside_10m_pct": round(_safe_float(row.get("extra_upside_10m_pct"), 0.0), 3),
        "extra_upside_10m_krw_est": int(_safe_int(row.get("extra_upside_10m_krw_est"), 0)),
        "capture_efficiency_pct": round(_safe_float(row.get("capture_efficiency_pct"), 0.0), 1),
    }


def build_post_sell_feedback_report(
    target_date: str,
    *,
    top_n: int = 10,
    evaluate_now: bool = True,
    token: str | None = None,
) -> dict:
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    if evaluate_now:
        summary = evaluate_post_sell_candidates(safe_date, token=token)
    else:
        existing_candidates = _load_jsonl(_candidate_path(safe_date))
        existing_evaluations = _load_jsonl(_evaluation_path(safe_date))
        summary = _build_summary_from_raw_rows(
            target_date=safe_date,
            candidates=existing_candidates,
            evaluations=existing_evaluations,
        )

    candidates = _load_jsonl(_candidate_path(safe_date))
    evaluations = _load_jsonl(_evaluation_path(safe_date))
    rows = _enrich_post_sell_rows(candidates=candidates, evaluations=evaluations)
    evaluated_count = len(rows)
    top_limit = max(1, int(top_n or 10))

    if not rows:
        return {
            "date": safe_date,
            "summary": post_sell_feedback_summary_to_dict(summary),
            "metrics": {
                "total_candidates": int(summary.total_candidates),
                "evaluated_candidates": int(summary.evaluated_candidates),
                "missed_upside_rate": 0.0,
                "good_exit_rate": 0.0,
                "avg_realized_profit_rate": 0.0,
                "avg_extra_upside_10m_pct": 0.0,
                "median_extra_upside_10m_pct": 0.0,
                "avg_close_after_sell_10m_pct": 0.0,
                "capture_efficiency_avg_pct": 0.0,
                "estimated_extra_upside_10m_krw_sum": 0,
                "estimated_extra_upside_10m_krw_avg": 0,
                "timing_tuning_pressure_score": 0.0,
            },
            "insight": {
                "headline": "post-sell 평가 데이터가 없습니다.",
                "comment": "후보 기록/장후 평가가 누적되면 수익 극대화 여지와 매도시점 튜닝 후보가 표시됩니다.",
            },
            "exit_rule_tuning": [],
            "tag_tuning": [],
            "priority_actions": _build_priority_actions([], limit=3),
            "top_missed_upside": [],
            "top_good_exit": [],
            "meta": {
                "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
                "generated_at": datetime.now().isoformat(),
                "evaluation_mode": "post_sell_minute_forward",
                "thresholds": {
                    "missed_upside_mfe_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT", 0.8) or 0.8),
                    "missed_upside_close_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT", 0.3) or 0.3),
                    "good_exit_mae_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6) or -0.6),
                    "good_exit_close_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT", -0.2) or -0.2),
                },
            },
        }

    outcome_counter = Counter(str(item.get("outcome") or "NEUTRAL").upper() for item in rows)
    missed_rate = _ratio(outcome_counter.get("MISSED_UPSIDE", 0), evaluated_count)
    good_rate = _ratio(outcome_counter.get("GOOD_EXIT", 0), evaluated_count)
    avg_profit = _avg([_safe_float(item.get("profit_rate"), 0.0) for item in rows])
    avg_extra_upside = _avg([_safe_float(item.get("extra_upside_10m_pct"), 0.0) for item in rows])
    median_extra_upside = _median([_safe_float(item.get("extra_upside_10m_pct"), 0.0) for item in rows])
    avg_close_10m = _avg([_safe_float(item.get("close_10m_pct"), 0.0) for item in rows])
    capture_avg = _avg([
        _safe_float(item.get("capture_efficiency_pct"), 0.0)
        for item in rows
        if _safe_float(item.get("potential_peak_profit_rate_10m"), 0.0) > 0.0
    ])
    est_extra_krw_sum = int(sum(_safe_int(item.get("extra_upside_10m_krw_est"), 0) for item in rows))
    est_extra_krw_avg = int(round(est_extra_krw_sum / evaluated_count)) if evaluated_count > 0 else 0
    timing_pressure = _clamp(
        (missed_rate * 0.65)
        + _clamp(max(avg_close_10m, 0.0) * 35.0, 0.0, 25.0)
        + _clamp(max(avg_extra_upside, 0.0) * 8.0, 0.0, 10.0)
        - _clamp(good_rate * 0.15, 0.0, 15.0),
        0.0,
        100.0,
    )

    if missed_rate >= 45.0 and avg_close_10m >= 0.2:
        headline = "매도 후 추가 상승이 잦아 수익 극대화 여지가 큽니다."
    elif good_rate >= 40.0 and avg_close_10m <= 0.0:
        headline = "손실 회피형 매도는 유효했고 과도 완화는 주의가 필요합니다."
    elif timing_pressure >= 55.0:
        headline = "매도시점 미세조정 실험을 시작할 만한 신호가 관측됩니다."
    else:
        headline = "현재 매도 규칙은 크게 무너지지 않았고 표본 축적이 우선입니다."

    exit_rule_rows = _build_exit_rule_tuning_rows(rows)
    tag_rows = _build_tag_tuning_rows(rows)
    priority_actions = _build_priority_actions(exit_rule_rows, limit=3)

    top_missed = [
        _case_view(item)
        for item in sorted(
            [row for row in rows if str(row.get("outcome") or "") == "MISSED_UPSIDE"],
            key=lambda row: (
                _safe_int(row.get("extra_upside_10m_krw_est"), 0),
                _safe_float(row.get("extra_upside_10m_pct"), 0.0),
            ),
            reverse=True,
        )[:top_limit]
    ]
    top_good = [
        _case_view(item)
        for item in sorted(
            [row for row in rows if str(row.get("outcome") or "") == "GOOD_EXIT"],
            key=lambda row: _safe_float(row.get("mae_10m_pct"), 0.0),
        )[:top_limit]
    ]

    return {
        "date": safe_date,
        "summary": post_sell_feedback_summary_to_dict(summary),
        "metrics": {
            "total_candidates": int(summary.total_candidates),
            "evaluated_candidates": int(summary.evaluated_candidates),
            "missed_upside_rate": float(missed_rate),
            "good_exit_rate": float(good_rate),
            "avg_realized_profit_rate": float(avg_profit),
            "avg_extra_upside_10m_pct": float(avg_extra_upside),
            "median_extra_upside_10m_pct": float(median_extra_upside),
            "avg_close_after_sell_10m_pct": float(avg_close_10m),
            "capture_efficiency_avg_pct": float(capture_avg),
            "estimated_extra_upside_10m_krw_sum": int(est_extra_krw_sum),
            "estimated_extra_upside_10m_krw_avg": int(est_extra_krw_avg),
            "timing_tuning_pressure_score": round(float(timing_pressure), 1),
        },
        "insight": {
            "headline": headline,
            "comment": (
                f"평가 {evaluated_count}건 기준으로 missed_upside {missed_rate:.1f}%, "
                f"good_exit {good_rate:.1f}%, 매도 후 10분 평균 종가 수익률 {avg_close_10m:+.2f}%입니다."
            ),
        },
        "exit_rule_tuning": exit_rule_rows,
        "tag_tuning": tag_rows,
        "priority_actions": priority_actions,
        "top_missed_upside": top_missed,
        "top_good_exit": top_good,
        "meta": {
            "schema_version": POST_SELL_REPORT_SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "evaluation_mode": "post_sell_minute_forward",
            "thresholds": {
                "missed_upside_mfe_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT", 0.8) or 0.8),
                "missed_upside_close_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT", 0.3) or 0.3),
                "good_exit_mae_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT", -0.6) or -0.6),
                "good_exit_close_pct": float(getattr(TRADING_RULES, "POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT", -0.2) or -0.2),
            },
        },
    }
