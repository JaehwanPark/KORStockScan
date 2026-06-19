"""Gatekeeper snapshot recording and replay helpers."""

from __future__ import annotations

import atexit
import json
import threading
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from src.engine.ai_response_contracts import normalize_gatekeeper_action_key
from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import read_jsonl
from src.utils.logger import log_error, log_info


_WRITE_LOCK = threading.RLock()
_RECENT_SNAPSHOT_SIGNATURES: dict[str, float] = {}

# ── 비동기 JSONL writer (single-thread, best-effort, process-exit flush) ─────
_JSONL_WRITER: ThreadPoolExecutor | None = None
_JSONL_WRITER_LOCK = threading.Lock()


def _get_jsonl_writer() -> ThreadPoolExecutor:
    global _JSONL_WRITER
    if _JSONL_WRITER is None:
        with _JSONL_WRITER_LOCK:
            if _JSONL_WRITER is None:
                _JSONL_WRITER = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="jsonl_writer",
                )
    return _JSONL_WRITER


def _flush_jsonl_writer() -> None:
    """process exit 시 flush. best-effort."""
    global _JSONL_WRITER
    writer = _JSONL_WRITER
    if writer is not None:
        writer.shutdown(wait=True)
        _JSONL_WRITER = None


# process-exit flush 등록 (best-effort)
atexit.register(_flush_jsonl_writer)


# ── TTL prune helpers ────────────────────────────────────────────────────────
_SNAPSHOT_PRUNE_INTERVAL_SEC = 300  # 5분마다 prune
_LAST_SNAPSHOT_PRUNE_TS: float = 0.0


def _prune_stale_signatures(now_ts: float) -> None:
    """GATEKEEPER_SNAPSHOT_DEDUP_TTL_SEC보다 충분히 긴 보존 구간으로 prune.

    반드시 _WRITE_LOCK을 획득한 상태에서 호출해야 한다.
    """
    global _LAST_SNAPSHOT_PRUNE_TS
    if now_ts - _LAST_SNAPSHOT_PRUNE_TS < _SNAPSHOT_PRUNE_INTERVAL_SEC:
        return
    dedup_ttl = float(getattr(TRADING_RULES, "GATEKEEPER_SNAPSHOT_DEDUP_TTL_SEC", 20.0))
    # dedup TTL의 10배 이상 경과한 시그니처는 제거 (최소 200초, 기본 200초)
    keep_ttl = max(dedup_ttl * 10, 200.0)
    stale_keys = [k for k, ts in list(_RECENT_SNAPSHOT_SIGNATURES.items()) if now_ts - ts > keep_ttl]
    for k in stale_keys:
        _RECENT_SNAPSHOT_SIGNATURES.pop(k, None)
    _LAST_SNAPSHOT_PRUNE_TS = now_ts


def _replay_dir() -> Path:
    path = DATA_DIR / "gatekeeper"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        # mkdir 실패 시에도 Path 객체 반환 (실제 write 실패는 _append_jsonl/_append_jsonl_async에서 처리)
        pass
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
    """동기 JSONL append. 비동기 writer의 fallback으로 유지."""
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _append_jsonl_async(
    path: Path,
    payload: dict,
    *,
    _rollback_signature: str = "",
) -> bool:
    """비동기 JSONL append (single-thread, best-effort, same-process ordering 보장).

    Returns:
        True  — enqueue 성공 (worker write는 비동기, 실패 시 callback에서 log_error + dedup 롤백)
        True  — enqueue 실패 후 동기 fallback write 성공
        False — enqueue 실패 + 동기 fallback write도 실패 (dedup 롤백 완료)

    규약:
    1. single-thread writer (ThreadPoolExecutor max_workers=1)
    2. best-effort enqueue (실패 시 동기 fallback)
    3. process exit 시 flush (atexit 등록)
    4. write 실패는 예외 전파 대신 log_error + False 반환
    5. same-process ordering 보장 (single worker thread)

    _rollback_signature가 전달되면, worker write 실패 시 _WRITE_LOCK 아래에서
    해당 시그니처를 _RECENT_SNAPSHOT_SIGNATURES에서 제거한다 (dedup 롤백).
    dedup 시그니처 자체는 호출자가 이미 _WRITE_LOCK 아래에서 즉시 기록했음을
    전제로 한다.
    """
    def _on_write_done(future):
        exc = future.exception()
        if exc is not None:
            log_error(f"[GATEKEEPER_SNAPSHOT] async write 실패 (dedup 롤백): {exc}")
            if _rollback_signature:
                with _WRITE_LOCK:
                    _RECENT_SNAPSHOT_SIGNATURES.pop(_rollback_signature, None)

    try:
        writer = _get_jsonl_writer()
        future = writer.submit(_append_jsonl, path, payload)
        future.add_done_callback(_on_write_done)
        return True
    except Exception as exc:
        log_error(f"[GATEKEEPER_SNAPSHOT] async enqueue 실패, 동기 fallback: {exc}")
        try:
            _append_jsonl(path, payload)
            # 동기 fallback 성공 → 롤백 불필요 (이미 기록된 dedup 유지)
            return True
        except Exception as fallback_exc:
            log_error(f"[GATEKEEPER_SNAPSHOT] 동기 fallback write도 실패 (dedup 롤백): {fallback_exc}")
            if _rollback_signature:
                with _WRITE_LOCK:
                    _RECENT_SNAPSHOT_SIGNATURES.pop(_rollback_signature, None)
            return False


def _snapshot_signature(payload: dict) -> str:
    signature_payload = {
        "stock_code": payload.get("stock_code", ""),
        "strategy": payload.get("strategy", ""),
        "action_label": payload.get("action_label", ""),
        "action_key": payload.get("action_key", ""),
        "allow_entry": payload.get("allow_entry", False),
        "ctx_summary": payload.get("ctx_summary", {}),
    }
    raw = json.dumps(signature_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def load_gatekeeper_snapshots(target_date: str) -> list[dict]:
    path = _snapshot_path(target_date)
    return read_jsonl(path)


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
        "action_key": normalize_gatekeeper_action_key(gatekeeper.get("action_key") or gatekeeper.get("action_label")),
        "allow_entry": bool(gatekeeper.get("allow_entry", False)),
        "cache_mode": str(gatekeeper.get("cache_mode", "") or ""),
        "eval_ms": int(gatekeeper.get("eval_ms", 0) or 0),
        "lock_wait_ms": int(gatekeeper.get("lock_wait_ms", 0) or 0),
        "packet_build_ms": int(gatekeeper.get("packet_build_ms", 0) or 0),
        "model_call_ms": int(gatekeeper.get("model_call_ms", 0) or 0),
        "total_internal_ms": int(gatekeeper.get("total_internal_ms", 0) or 0),
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

            # TTL prune (5분 주기, dedup TTL의 10배 이상 경과 시그니처 제거)
            _prune_stale_signatures(now_ts)

            # dedup 시그니처를 main thread에서 즉시 기록 (중복 enqueue 방지)
            _RECENT_SNAPSHOT_SIGNATURES[signature] = now_ts

            # 비동기 write (single-thread, best-effort, same-process ordering)
            # write 실패 시 _rollback_signature로 dedup 롤백
            ok = _append_jsonl_async(
                _snapshot_path(payload["signal_date"]), payload,
                _rollback_signature=signature,
            )
            if not ok:
                # enqueue 실패 + 동기 fallback write도 실패 → persist 실패
                log_error(
                    f"[GATEKEEPER_SNAPSHOT] {payload['stock_name']}({payload['stock_code']}) "
                    f"action={payload['action_label']} allow={payload['allow_entry']} "
                    f"— persist 실패 (enqueue+fallback 모두 실패)"
                )
                return None
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
        from src.engine.ai_engine_openai import GPTSniperEngine
    except Exception as exc:
        return {
            "ok": False,
            "error": f"AI 엔진 import 실패: {exc}",
        }

    api_keys = [v for k, v in conf.items() if str(k).startswith("OPENAI_API_KEY") and v]
    if not api_keys:
        return {
            "ok": False,
            "error": "OPENAI_API_KEY 설정이 없어 재실행할 수 없습니다.",
        }

    try:
        engine = GPTSniperEngine(api_keys=api_keys, announce_startup=False)
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
