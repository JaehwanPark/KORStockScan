"""Shadow candidate recording and post-close evaluation for dynamic strength momentum."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.constants import DATA_DIR
from src.utils.logger import log_error, log_info


_WRITE_LOCK = threading.RLock()
_RECORDED_KEYS: dict[tuple[str, str, str], float] = {}


def _shadow_dir() -> Path:
    path = DATA_DIR / "shadow"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _candidate_path(target_date: str) -> Path:
    return _shadow_dir() / f"strength_shadow_candidates_{target_date}.jsonl"


def _evaluation_path(target_date: str) -> Path:
    return _shadow_dir() / f"strength_shadow_evaluations_{target_date}.jsonl"


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


def _minute_bucket(ts: datetime, bucket_min: int = 5) -> str:
    floored_min = (ts.minute // bucket_min) * bucket_min
    return ts.replace(minute=floored_min, second=0, microsecond=0).strftime("%H:%M")


def record_shadow_candidate(stock: dict, code: str, ws_data: dict, momentum_gate: dict) -> dict | None:
    stock = stock or {}
    ws_data = ws_data or {}
    momentum_gate = momentum_gate or {}

    if not momentum_gate.get("allowed"):
        return None

    now = datetime.now()
    target_date = now.strftime("%Y-%m-%d")
    bucket = _minute_bucket(now, bucket_min=5)
    dedupe_key = (target_date, str(code).strip()[:6], bucket)

    with _WRITE_LOCK:
        if dedupe_key in _RECORDED_KEYS:
            return None

        orderbook = ws_data.get("orderbook") or {}
        asks = orderbook.get("asks") or []
        bids = orderbook.get("bids") or []
        best_ask = int((asks[-1] or {}).get("price", 0) or 0) if asks else 0
        best_bid = int((bids[0] or {}).get("price", 0) or 0) if bids else 0
        current_price = int(float(ws_data.get("curr", 0) or 0))

        payload = {
            "shadow_id": uuid.uuid4().hex[:16],
            "recorded_at": now.isoformat(),
            "signal_date": target_date,
            "signal_time": now.strftime("%H:%M:%S"),
            "signal_bucket": bucket,
            "stock_code": str(code).strip()[:6],
            "stock_name": str(stock.get("name", "") or ""),
            "strategy": str(stock.get("strategy", "") or ""),
            "position_tag": str(stock.get("position_tag", "") or ""),
            "signal_price": current_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
            "ask_tot": int(float(ws_data.get("ask_tot", 0) or 0)),
            "bid_tot": int(float(ws_data.get("bid_tot", 0) or 0)),
            "current_vpw": float(ws_data.get("v_pw", 0) or 0.0),
            "dynamic_reason": str(momentum_gate.get("reason", "") or ""),
            "dynamic_base_vpw": float(momentum_gate.get("base_vpw", 0.0) or 0.0),
            "dynamic_delta": float(momentum_gate.get("vpw_delta", 0.0) or 0.0),
            "dynamic_slope_per_sec": float(momentum_gate.get("slope_per_sec", 0.0) or 0.0),
            "dynamic_window_sec": int(momentum_gate.get("window_sec", 0) or 0),
            "dynamic_window_total_value": int(momentum_gate.get("window_total_value", 0) or 0),
            "dynamic_window_buy_value": int(momentum_gate.get("window_buy_value", 0) or 0),
            "dynamic_window_sell_value": int(momentum_gate.get("window_sell_value", 0) or 0),
            "dynamic_window_buy_ratio": float(momentum_gate.get("window_buy_ratio", 0.0) or 0.0),
            "dynamic_window_exec_buy_ratio": float(momentum_gate.get("window_exec_buy_ratio", 0.0) or 0.0),
            "dynamic_window_net_buy_qty": int(momentum_gate.get("window_net_buy_qty", 0) or 0),
            "evaluation_mode": "next_minute_forward",
        }

        _append_jsonl(_candidate_path(target_date), payload)
        _RECORDED_KEYS[dedupe_key] = now.timestamp()
        log_info(
            f"[SHADOW_CANDIDATE] {payload['stock_name']}({payload['stock_code']}) "
            f"price={payload['signal_price']} vpw={payload['current_vpw']:.1f} "
            f"delta={payload['dynamic_delta']:.1f} buy_value={payload['dynamic_window_buy_value']} "
            f"buy_ratio={payload['dynamic_window_buy_ratio']:.2f} "
            f"exec_buy_ratio={payload['dynamic_window_exec_buy_ratio']:.2f} "
            f"net_buy_qty={payload['dynamic_window_net_buy_qty']}"
        )
        return payload


def _parse_minute_time(value: str, signal_date: str) -> datetime | None:
    try:
        return datetime.strptime(f"{signal_date} {value}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def _compute_window_metrics(candidate: dict, candles: list[dict], window_minutes: int) -> dict:
    signal_dt = datetime.strptime(
        f"{candidate['signal_date']} {candidate['signal_time']}",
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

    signal_price = float(candidate.get("signal_price", 0) or 0)
    if signal_price <= 0 or not relevant:
        return {
            "close_ret_pct": 0.0,
            "mfe_pct": 0.0,
            "mae_pct": 0.0,
            "hit_tp_05": False,
            "hit_tp_10": False,
            "hit_sl_05": False,
            "tp05_before_sl05": False,
            "bars": len(relevant),
        }

    highs = []
    lows = []
    close_ret = 0.0
    first_tp_dt = None
    first_sl_dt = None

    for candle_dt, candle in relevant:
        high_p = float(candle.get("고가", 0) or 0)
        low_p = float(candle.get("저가", 0) or 0)
        close_p = float(candle.get("현재가", 0) or 0)

        if high_p > 0:
            high_ret = ((high_p / signal_price) - 1.0) * 100.0
            highs.append(high_ret)
            if first_tp_dt is None and high_ret >= 0.5:
                first_tp_dt = candle_dt
        if low_p > 0:
            low_ret = ((low_p / signal_price) - 1.0) * 100.0
            lows.append(low_ret)
            if first_sl_dt is None and low_ret <= -0.5:
                first_sl_dt = candle_dt
        if close_p > 0:
            close_ret = ((close_p / signal_price) - 1.0) * 100.0

    mfe_pct = max(highs) if highs else 0.0
    mae_pct = min(lows) if lows else 0.0

    return {
        "close_ret_pct": round(close_ret, 3),
        "mfe_pct": round(mfe_pct, 3),
        "mae_pct": round(mae_pct, 3),
        "hit_tp_05": mfe_pct >= 0.5,
        "hit_tp_10": mfe_pct >= 1.0,
        "hit_sl_05": mae_pct <= -0.5,
        "tp05_before_sl05": bool(first_tp_dt is not None and (first_sl_dt is None or first_tp_dt <= first_sl_dt)),
        "bars": len(relevant),
    }


def _classify_candidate(metrics_5m: dict) -> str:
    if metrics_5m.get("tp05_before_sl05"):
        return "GOOD"
    if bool(metrics_5m.get("hit_sl_05")) and not bool(metrics_5m.get("hit_tp_05")):
        return "BAD"
    if float(metrics_5m.get("close_ret_pct", 0.0) or 0.0) >= 0.3:
        return "GOOD"
    if float(metrics_5m.get("close_ret_pct", 0.0) or 0.0) <= -0.5:
        return "BAD"
    return "NEUTRAL"


@dataclass
class ShadowFeedbackSummary:
    date: str
    total_candidates: int = 0
    evaluated_candidates: int = 0
    outcome_counts: dict[str, int] = field(default_factory=dict)
    best_cases: list[dict] = field(default_factory=list)
    missed_winners: list[dict] = field(default_factory=list)


def evaluate_shadow_candidates(target_date: str, token: str | None = None) -> ShadowFeedbackSummary:
    try:
        from src.utils import kiwoom_utils
    except Exception as exc:
        log_error(f"[SHADOW_EVAL] kiwoom_utils import failed: {exc}")
        kiwoom_utils = None

    candidates = _load_jsonl(_candidate_path(target_date))
    existing_evaluations = _load_jsonl(_evaluation_path(target_date))
    evaluated_ids = {str(item.get("shadow_id", "")) for item in existing_evaluations}

    if token is None and candidates and kiwoom_utils is not None:
        try:
            token = kiwoom_utils.get_kiwoom_token()
        except Exception as exc:
            log_error(f"[SHADOW_EVAL] token fetch failed: {exc}")
            token = None

    candle_cache: dict[str, list[dict]] = {}
    new_evaluations: list[dict] = []

    for candidate in candidates:
        shadow_id = str(candidate.get("shadow_id", "") or "")
        code = str(candidate.get("stock_code", "") or "")
        if not shadow_id or not code or shadow_id in evaluated_ids or token is None or kiwoom_utils is None:
            continue

        if code not in candle_cache:
            try:
                candle_cache[code] = kiwoom_utils.get_minute_candles_ka10080(token, code, limit=600) or []
            except Exception as exc:
                log_error(f"[SHADOW_EVAL] {code} minute candles fetch failed: {exc}")
                candle_cache[code] = []

        candles = candle_cache.get(code, [])
        metrics_1m = _compute_window_metrics(candidate, candles, 1)
        metrics_3m = _compute_window_metrics(candidate, candles, 3)
        metrics_5m = _compute_window_metrics(candidate, candles, 5)
        metrics_10m = _compute_window_metrics(candidate, candles, 10)
        outcome = _classify_candidate(metrics_5m)

        evaluation = {
            "shadow_id": shadow_id,
            "evaluated_at": datetime.now().isoformat(),
            "signal_date": target_date,
            "stock_code": code,
            "stock_name": candidate.get("stock_name", ""),
            "signal_price": candidate.get("signal_price", 0),
            "outcome": outcome,
            "metrics_1m": metrics_1m,
            "metrics_3m": metrics_3m,
            "metrics_5m": metrics_5m,
            "metrics_10m": metrics_10m,
        }
        new_evaluations.append(evaluation)

    if new_evaluations:
        with _WRITE_LOCK:
            path = _evaluation_path(target_date)
            for item in new_evaluations:
                _append_jsonl(path, item)

    all_evaluations = existing_evaluations + new_evaluations
    summary = ShadowFeedbackSummary(date=target_date)
    summary.total_candidates = len(candidates)
    summary.evaluated_candidates = len(all_evaluations)

    outcome_counts: dict[str, int] = {"GOOD": 0, "NEUTRAL": 0, "BAD": 0}
    for item in all_evaluations:
        outcome = str(item.get("outcome", "NEUTRAL") or "NEUTRAL").upper()
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
    summary.outcome_counts = outcome_counts

    def _score(item: dict) -> tuple[float, float]:
        metrics_5m = item.get("metrics_5m", {}) or {}
        return (
            float(metrics_5m.get("mfe_pct", 0.0) or 0.0),
            float(metrics_5m.get("close_ret_pct", 0.0) or 0.0),
        )

    summary.best_cases = sorted(all_evaluations, key=_score, reverse=True)[:5]
    summary.missed_winners = [item for item in summary.best_cases if str(item.get("outcome", "")).upper() == "GOOD"]
    return summary


def format_shadow_feedback_summary(summary: ShadowFeedbackSummary) -> str:
    if summary.total_candidates <= 0:
        return f"📈 동적 체결강도 shadow 피드백 ({summary.date})\n- 후보 기록 없음"

    lines = [
        f"📈 동적 체결강도 shadow 피드백 ({summary.date})",
        f"- 후보 기록: {summary.total_candidates}건",
        f"- 평가 완료: {summary.evaluated_candidates}건",
        f"- 결과 분포: GOOD {summary.outcome_counts.get('GOOD', 0)} / "
        f"NEUTRAL {summary.outcome_counts.get('NEUTRAL', 0)} / "
        f"BAD {summary.outcome_counts.get('BAD', 0)}",
    ]

    if summary.missed_winners:
        lines.append("- 놓쳤지만 좋았던 후보:")
        for item in summary.missed_winners[:3]:
            metrics = item.get("metrics_5m", {}) or {}
            lines.append(
                f"  {item.get('stock_name')}({item.get('stock_code')}) "
                f"MFE5m {float(metrics.get('mfe_pct', 0.0) or 0.0):+.2f}% / "
                f"Close5m {float(metrics.get('close_ret_pct', 0.0) or 0.0):+.2f}%"
            )
    return "\n".join(lines)
