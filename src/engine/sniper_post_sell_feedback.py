"""Post-sell candidate recording and post-close evaluation."""

from __future__ import annotations

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

    if token is None and candidates and kiwoom_utils is not None:
        try:
            token = kiwoom_utils.get_kiwoom_token()
        except Exception as exc:
            log_error(f"[POST_SELL_EVAL] token fetch failed: {exc}")
            token = None

    candle_cache: dict[str, list[dict]] = {}
    new_evaluations: list[dict] = []

    for candidate in candidates:
        post_sell_id = str(candidate.get("post_sell_id", "") or "")
        code = str(candidate.get("stock_code", "") or "")
        if not post_sell_id or not code or post_sell_id in evaluated_ids or token is None or kiwoom_utils is None:
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
            "sell_price": candidate.get("sell_price", 0),
            "profit_rate": candidate.get("profit_rate", 0.0),
            "exit_rule": candidate.get("exit_rule", "-"),
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
