"""Gatekeeper snapshot recording and replay helpers."""

from __future__ import annotations

import json
import threading
import time
import hashlib
from datetime import datetime
from pathlib import Path

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.logger import log_error, log_info


_WRITE_LOCK = threading.RLock()
_RECENT_SNAPSHOT_SIGNATURES: dict[str, float] = {}


def _replay_dir() -> Path:
    path = DATA_DIR / "gatekeeper"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _snapshot_path(target_date: str) -> Path:
    return _replay_dir() / f"gatekeeper_snapshots_{target_date}.jsonl"


def _json_safe(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _append_jsonl(path: Path, payload: dict) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _snapshot_signature(payload: dict) -> str:
    signature_payload = {
        "stock_code": payload.get("stock_code", ""),
        "strategy": payload.get("strategy", ""),
        "action_label": payload.get("action_label", ""),
        "allow_entry": payload.get("allow_entry", False),
        "ctx_summary": payload.get("ctx_summary", {}),
    }
    raw = json.dumps(signature_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def load_gatekeeper_snapshots(target_date: str) -> list[dict]:
    path = _snapshot_path(target_date)
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


def record_gatekeeper_snapshot(
    *,
    stock: dict,
    code: str,
    strategy: str,
    realtime_ctx: dict,
    gatekeeper: dict,
) -> dict | None:
    stock = stock or {}
    realtime_ctx = realtime_ctx or {}
    gatekeeper = gatekeeper or {}
    now = datetime.now()
    code = str(code or "").strip()[:6]
    if not code:
        return None

    payload = {
        "recorded_at": now.isoformat(timespec="seconds"),
        "signal_date": now.strftime("%Y-%m-%d"),
        "signal_time": now.strftime("%H:%M:%S"),
        "stock_code": code,
        "stock_name": str(stock.get("name", "") or ""),
        "strategy": str(strategy or stock.get("strategy", "") or ""),
        "position_tag": str(stock.get("position_tag", "") or ""),
        "action_label": str(gatekeeper.get("action_label", "") or "UNKNOWN"),
        "allow_entry": bool(gatekeeper.get("allow_entry", False)),
        "report": str(gatekeeper.get("report", "") or ""),
        "report_preview": str(gatekeeper.get("report", "") or "")[:240],
        "ctx_summary": {
            "curr_price": _json_safe(realtime_ctx.get("curr_price", 0)),
            "fluctuation": _json_safe(realtime_ctx.get("fluctuation", 0.0)),
            "vwap_status": _json_safe(realtime_ctx.get("vwap_status", "")),
            "buy_ratio_ws": _json_safe(realtime_ctx.get("buy_ratio_ws", 0.0)),
            "exec_buy_ratio": _json_safe(realtime_ctx.get("exec_buy_ratio", 0.0)),
            "tick_trade_value": _json_safe(realtime_ctx.get("tick_trade_value", 0)),
            "net_buy_exec_volume": _json_safe(realtime_ctx.get("net_buy_exec_volume", 0)),
            "program_flow_desc": _json_safe(realtime_ctx.get("program_flow_desc", "")),
            "micro_flow_desc": _json_safe(realtime_ctx.get("micro_flow_desc", "")),
            "depth_flow_desc": _json_safe(realtime_ctx.get("depth_flow_desc", "")),
            "market_cap": _json_safe(realtime_ctx.get("market_cap", 0)),
            "radar_score": _json_safe(realtime_ctx.get("radar_score", 0.0)),
            "radar_conclusion": _json_safe(realtime_ctx.get("radar_conclusion", "")),
        },
        "realtime_ctx": _json_safe(realtime_ctx),
    }

    try:
        with _WRITE_LOCK:
            now_ts = time.time()
            dedup_ttl = float(getattr(TRADING_RULES, "GATEKEEPER_SNAPSHOT_DEDUP_TTL_SEC", 20.0))
            signature = _snapshot_signature(payload)
            last_saved_at = _RECENT_SNAPSHOT_SIGNATURES.get(signature, 0.0)
            if dedup_ttl > 0 and (now_ts - last_saved_at) < dedup_ttl:
                return payload

            _append_jsonl(_snapshot_path(payload["signal_date"]), payload)
            _RECENT_SNAPSHOT_SIGNATURES[signature] = now_ts
        log_info(
            f"[GATEKEEPER_SNAPSHOT] {payload['stock_name']}({payload['stock_code']}) "
            f"action={payload['action_label']} allow={payload['allow_entry']}"
        )
        return payload
    except Exception as exc:
        log_error(f"[GATEKEEPER_SNAPSHOT] save failed: {exc}")
        return None


def find_gatekeeper_snapshot(target_date: str, code: str, target_time: str | None = None) -> dict | None:
    code = str(code or "").strip()[:6]
    rows = [row for row in load_gatekeeper_snapshots(target_date) if str(row.get("stock_code", "")) == code]
    if not rows:
        return None
    if not target_time:
        return rows[-1]
    try:
        target_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            target_dt = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M")
        except Exception:
            return rows[-1]

    def _distance_seconds(row: dict) -> float:
        try:
            row_dt = datetime.strptime(row.get("recorded_at", ""), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            try:
                row_dt = datetime.strptime(
                    f"{row.get('signal_date', target_date)} {row.get('signal_time', '00:00:00')}",
                    "%Y-%m-%d %H:%M:%S",
                )
            except Exception:
                return float("inf")
        return abs((row_dt - target_dt).total_seconds())

    rows.sort(key=_distance_seconds)
    return rows[0] if rows else None


def find_gatekeeper_snapshot_for_trade(
    target_date: str,
    code: str,
    anchor_dt: datetime | None,
    *,
    max_diff_sec: int = 60 * 90,
) -> dict | None:
    code = str(code or "").strip()[:6]
    if not code:
        return None
    rows = [row for row in load_gatekeeper_snapshots(target_date) if str(row.get("stock_code", "")) == code]
    if not rows:
        return None
    if anchor_dt is None:
        return rows[-1]

    best_row = None
    best_diff = float("inf")
    for row in rows:
        try:
            row_dt = datetime.strptime(row.get("recorded_at", ""), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            try:
                row_dt = datetime.strptime(
                    f"{row.get('signal_date', target_date)} {row.get('signal_time', '00:00:00')}",
                    "%Y-%m-%d %H:%M:%S",
                )
            except Exception:
                continue
        diff = (anchor_dt - row_dt).total_seconds()
        if diff < 0:
            continue
        if diff <= max_diff_sec and diff < best_diff:
            best_diff = diff
            best_row = row
    return best_row


def rerun_gatekeeper_snapshot(snapshot: dict, conf: dict | None = None) -> dict:
    snapshot = snapshot or {}
    conf = conf or {}
    try:
        from src.engine.ai_engine import GeminiSniperEngine
    except Exception as exc:
        return {
            "ok": False,
            "error": f"AI 엔진 import 실패: {exc}",
        }

    api_keys = [v for k, v in conf.items() if str(k).startswith("GEMINI_API_KEY") and v]
    if not api_keys:
        return {
            "ok": False,
            "error": "GEMINI_API_KEY 설정이 없어 재실행할 수 없습니다.",
        }

    try:
        engine = GeminiSniperEngine(api_keys=api_keys)
        realtime_ctx = snapshot.get("realtime_ctx") or {}
        result = engine.evaluate_realtime_gatekeeper(
            stock_name=str(snapshot.get("stock_name", "") or ""),
            stock_code=str(snapshot.get("stock_code", "") or ""),
            realtime_ctx=realtime_ctx,
            analysis_mode=str(snapshot.get("strategy", "") or "AUTO"),
        )
        return {
            "ok": True,
            "action_label": result.get("action_label"),
            "allow_entry": bool(result.get("allow_entry", False)),
            "report": str(result.get("report", "") or ""),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Gatekeeper 재실행 실패: {exc}",
        }
