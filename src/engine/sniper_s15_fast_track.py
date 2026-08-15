"""S15 fast-track scalping helpers and durable custody state."""

import hashlib
import json
import os
import re
import threading
import time
from datetime import datetime
from pathlib import Path

from src.engine import kiwoom_orders
from src.engine.sniper_entry_latency import evaluate_live_buy_entry
from src.engine.trade_profit import calculate_net_profit_rate
from src.engine.scalping.entry_ai_gate import evaluate_ai_score_prior
from src.engine.scalping.entry_candle_context import (
    build_entry_candle_context,
    entry_candle_context_enabled,
    fetch_entry_candles_with_meta,
    resolve_entry_candle_session,
    resolve_entry_candle_venue,
)
from src.database.models import RecommendationHistory
from src.utils.constants import TRADING_RULES
from src.utils.runtime_flags import is_trading_paused
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event

KIWOOM_TOKEN = None
WS_MANAGER = None
AI_ENGINE = None
DB = None


def bind_s15_dependencies(kiwoom_token=None, ws_manager=None, ai_engine=None, db=None):
    global KIWOOM_TOKEN, WS_MANAGER, AI_ENGINE, DB
    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if ws_manager is not None:
        WS_MANAGER = ws_manager
    if ai_engine is not None:
        AI_ENGINE = ai_engine
    if db is not None:
        DB = db


# ==========================================
# ⚡ [S15 v2] Fast-Track 상태 관리
# ==========================================
FAST_SCALP_POOL = {}
FAST_TRADE_STATE = {}
FAST_REENTRY_BLOCK = {}
FAST_LOCK = threading.RLock()
S15_FAST_TRACK_CONTRACT_VERSION = "s15_fast_track_v1"
S15_CUSTODY_SCHEMA = "s15_fast_track_custody_v2"
S15_CUSTODY_MAX_BYTES = 1_000_000
S15_CUSTODY_DIR = Path(
    os.getenv("KORSTOCKSCAN_S15_CUSTODY_DIR", "data/runtime/s15_fast_custody")
)
_S15_REQUIRED_EXCHANGES = frozenset({"KRX", "NXT"})
_S15_RECOVERY_THREADS = set()


def _canonical_json(payload):
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _serializable_fast_state(state):
    payload = {}
    for key, value in state.items():
        if key in {"lock", "_receipt_event", "_recovery_thread_active"}:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            payload[key] = value
        elif isinstance(value, dict):
            payload[key] = value
        elif isinstance(value, (list, tuple)):
            payload[key] = list(value)
    return payload


def _s15_custody_path(code):
    normalized = str(code or "").strip()[:6]
    if len(normalized) != 6 or not normalized.isdigit():
        raise ValueError("invalid_s15_custody_code")
    return S15_CUSTODY_DIR / f"{normalized}.json"


def _fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _persist_fast_state(code, state):
    """Atomically persist every unresolved S15 order/custody transition."""

    temporary = None
    try:
        state.pop("s15_custody_persist_failed", None)
        state.pop("s15_custody_persist_error", None)
        state_payload = _serializable_fast_state(state)
        body = {
            "schema": S15_CUSTODY_SCHEMA,
            "code": str(code).strip()[:6],
            "state": state_payload,
            "runtime_effect": False,
            "actual_order_submitted": False,
            "allowed_runtime_apply": False,
        }
        body["content_sha256"] = hashlib.sha256(_canonical_json(body)).hexdigest()
        target = _s15_custody_path(code)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.parent.is_symlink():
            raise RuntimeError("s15_custody_symlink_forbidden")
        temporary = target.with_name(
            f".{target.name}.{os.getpid()}.{time.time_ns()}.tmp"
        )
        raw = _canonical_json(body) + b"\n"
        if len(raw) > S15_CUSTODY_MAX_BYTES:
            raise RuntimeError("s15_custody_size_limit_exceeded")
        with temporary.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        _fsync_directory(target.parent)
        return True
    except Exception as exc:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        state["s15_custody_persist_failed"] = True
        state["s15_custody_persist_error"] = str(exc)
        broker_exposure_may_exist = bool(
            str(state.get("buy_ord_no") or "").strip()
            or str(state.get("sell_ord_no") or "").strip()
            or int(state.get("cum_buy_qty", 0) or 0) > 0
        )
        if broker_exposure_may_exist:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "custody_persistence_failed"
        log_error(f"[S15_CUSTODY_PERSIST_FAILED] {code}: {exc}")
        if broker_exposure_may_exist:
            with FAST_LOCK:
                runtime_state_matches = FAST_TRADE_STATE.get(code) is state
            if runtime_state_matches:
                try:
                    _start_s15_recovery_thread(code, state)
                except Exception as recovery_exc:
                    log_error(
                        f"[S15_CUSTODY_RECOVERY_START_FAILED] {code}: {recovery_exc}"
                    )
        return False


def _clear_fast_state_journal(code):
    try:
        target = _s15_custody_path(code)
        if target.parent.is_symlink() or target.is_symlink():
            raise RuntimeError("s15_custody_symlink_forbidden")
        if target.exists():
            target.unlink()
            _fsync_directory(target.parent)
        return True
    except Exception as exc:
        log_error(f"[S15_CUSTODY_CLEAR_FAILED] {code}: {exc}")
        return False


def _log_s15_event(stage, code, name="-", *, actual_order_submitted=False, **fields):
    try:
        emit_pipeline_event(
            "ENTRY_PIPELINE",
            name or "-",
            code,
            stage,
            record_id=fields.pop("record_id", None),
            fields={
                "metric_role": "source_quality_gate",
                "decision_authority": "real_s15_fast_track_runtime_only",
                "source_quality_gate": "s15_fast_track_contract",
                "window_policy": "intraday_operational_guard",
                "sample_floor": "not_applicable_runtime_guard",
                "primary_decision_metric": "funnel_count",
                "forbidden_uses": (
                    "score_threshold_change,provider_route_change,order_price_change,"
                    "quantity_or_cap_change,broker_guard_change,bot_restart_authority,"
                    "hard_safety_change,real_execution_quality_approval"
                ),
                "runtime_effect": True,
                "actual_order_submitted": bool(actual_order_submitted),
                "broker_order_forbidden": False,
                "s15_fast_track_contract_version": S15_FAST_TRACK_CONTRACT_VERSION,
                **fields,
            },
        )
    except Exception as exc:
        log_error(f"🚨 S15 provenance emit failed ({stage}:{code}): {exc}")


def _now_ts():
    return time.time()


def _get_tick_size_for_price(price):
    if hasattr(kiwoom_utils, "get_tick_size"):
        return int(kiwoom_utils.get_tick_size(price))
    if price < 2000:
        return 1
    if price < 5000:
        return 5
    if price < 20000:
        return 10
    if price < 50000:
        return 50
    if price < 200000:
        return 100
    if price < 500000:
        return 500
    return 1000


def _price_ticks_up(curr_price, ticks=2):
    price = int(curr_price)
    for _ in range(ticks):
        price += _get_tick_size_for_price(price)
    return int(price)


def _target_price_pct_up(avg_buy_price, pct=1.8):
    ideal = avg_buy_price * (1 + (pct / 100.0))
    price = int(avg_buy_price)
    while price < ideal:
        price += _get_tick_size_for_price(price)
    return int(price)


def _weighted_avg(amount, qty):
    if qty <= 0:
        return 0
    return int(amount / qty)


def _arm_s15_candidate(code, name, cnd_name, ttl_sec=180):
    now = _now_ts()
    expires_at = now + ttl_sec
    with FAST_LOCK:
        FAST_SCALP_POOL[code] = {
            "name": name or code,
            "armed_at": now,
            "last_seen": now,
            "base_condition": cnd_name,
            "expires_at": expires_at,
        }
    try:
        _save_armed_candidate_to_db(code, name, cnd_name, now, expires_at)
    except Exception as exc:
        log_error(f"🚨 S15 armed candidate DB 저장 실패 ({code}): {exc}")
    _log_s15_event(
        "s15_candidate_armed",
        code,
        name or code,
        s15_condition_role="candidate_arm",
        base_condition=cnd_name,
        armed_at=now,
        expires_at=expires_at,
        ttl_sec=ttl_sec,
    )


def _unarm_s15_candidate(code):
    with FAST_LOCK:
        FAST_SCALP_POOL.pop(code, None)
    _delete_armed_candidate_from_database(code)


def _save_armed_candidate_to_db(code, name, cnd_name, armed_at, expires_at):
    today = datetime.now().date()
    if DB is None:
        return
    with DB.get_session() as session:
        record = (
            session.query(RecommendationHistory)
            .filter_by(rec_date=today, stock_code=code, strategy="S15_CANDID")
            .first()
        )
        if record:
            record.stock_name = name
            record.position_tag = "S15_CANDID:" + cnd_name
            record.entry_armed_at_epoch = armed_at
            # Legacy TTL persistence fields: nxt=armed_at, hard_stop_price=expires_at.
            record.nxt = armed_at
            record.hard_stop_price = expires_at
            record.profit_rate = 0.0
        else:
            record = RecommendationHistory(
                rec_date=today,
                stock_code=code,
                stock_name=name,
                trade_type="SCALP",
                strategy="S15_CANDID",
                status="WATCHING",
                position_tag="S15_CANDID:" + cnd_name,
                prob=0.0,
                entry_armed_at_epoch=armed_at,
                # Legacy TTL persistence fields: nxt=armed_at, hard_stop_price=expires_at.
                nxt=armed_at,
                hard_stop_price=expires_at,
                profit_rate=0.0,
                buy_price=0,
                buy_qty=0,
            )
            session.add(record)


def _delete_armed_candidate_from_database(code):
    today = datetime.now().date()
    if DB is None:
        return
    with DB.get_session() as session:
        session.query(RecommendationHistory).filter_by(
            rec_date=today, stock_code=code, strategy="S15_CANDID"
        ).delete()


def _restore_armed_candidates_from_database():
    """봇 재시작 시 DB에 저장된 S15_CANDID 후보들을 FAST_SCALP_POOL에 복원합니다."""
    today = datetime.now().date()
    now = _now_ts()
    if DB is None:
        return
    with DB.get_session() as session:
        records = (
            session.query(RecommendationHistory)
            .filter_by(rec_date=today, strategy="S15_CANDID", status="WATCHING")
            .all()
        )
        for rec in records:
            code = rec.stock_code
            name = rec.stock_name
            cnd_name = (
                rec.position_tag.replace("S15_CANDID:", "") if rec.position_tag else ""
            )
            armed_at = (
                rec.entry_armed_at_epoch
                if rec.entry_armed_at_epoch
                else (rec.nxt if rec.nxt else 0.0)
            )
            expires_at = (
                rec.hard_stop_price
                if rec.hard_stop_price
                else (rec.profit_rate if rec.profit_rate else 0.0)
            )
            if expires_at < now:
                session.query(RecommendationHistory).filter_by(
                    rec_date=today, stock_code=code, strategy="S15_CANDID"
                ).delete()
                continue
            with FAST_LOCK:
                FAST_SCALP_POOL[code] = {
                    "name": name or code,
                    "cnd_name": cnd_name,
                    "armed_at": armed_at,
                    "expires_at": expires_at,
                }
        session.commit()


def _is_s15_armed(code):
    now = _now_ts()
    need_unarm = False
    with FAST_LOCK:
        item = FAST_SCALP_POOL.get(code)
        if not item:
            return False
        if item.get("expires_at", 0) < now:
            FAST_SCALP_POOL.pop(code, None)
            need_unarm = True
        else:
            return True
    if need_unarm:
        _unarm_s15_candidate(code)
    return False


def _is_s15_reentry_blocked(code):
    return FAST_REENTRY_BLOCK.get(code, 0) > _now_ts()


def _block_s15_reentry(code, seconds=60 * 60 * 6):
    FAST_REENTRY_BLOCK[code] = _now_ts() + seconds


def _get_fast_state(code):
    with FAST_LOCK:
        return FAST_TRADE_STATE.get(code)


def _set_fast_state(code, state):
    with FAST_LOCK:
        FAST_TRADE_STATE[code] = state
    _persist_fast_state(code, state)


def _pop_fast_state(code):
    with FAST_LOCK:
        state = FAST_TRADE_STATE.pop(code, None)
    if state is not None and str(state.get("status") or "").upper() in {
        "DONE",
        "CANCELLED",
        "FAILED",
        "BLOCKED",
    }:
        _clear_fast_state_journal(code)
    return state


def _load_fast_state_journal(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("s15_custody_not_regular_file")
    if path.stat().st_size > S15_CUSTODY_MAX_BYTES:
        raise ValueError("s15_custody_size_limit_exceeded")
    payload = json.loads(path.read_text(encoding="utf-8"))
    declared_hash = str(payload.pop("content_sha256", "") or "")
    if declared_hash != hashlib.sha256(_canonical_json(payload)).hexdigest():
        raise ValueError("s15_custody_hash_mismatch")
    if payload.get("schema") != S15_CUSTODY_SCHEMA:
        raise ValueError("s15_custody_schema_mismatch")
    if any(
        payload.get(key) is not expected
        for key, expected in (
            ("runtime_effect", False),
            ("actual_order_submitted", False),
            ("allowed_runtime_apply", False),
        )
    ):
        raise ValueError("s15_custody_authority_mismatch")
    code = str(payload.get("code") or "").strip()[:6]
    if path != _s15_custody_path(code):
        raise ValueError("s15_custody_path_mismatch")
    state = payload.get("state")
    if not isinstance(state, dict):
        raise ValueError("s15_custody_state_missing")
    state["lock"] = threading.RLock()
    state["s15_custody_restored"] = True
    return code, state


def _restore_fast_trade_states_from_journal():
    """Restore unresolved S15 custody before accepting any new S15 trigger."""

    if not S15_CUSTODY_DIR.exists():
        return 0
    if S15_CUSTODY_DIR.is_symlink() or not S15_CUSTODY_DIR.is_dir():
        log_error(
            f"[S15_CUSTODY_RESTORE_BLOCKED] {S15_CUSTODY_DIR}: "
            "custody_directory_not_regular"
        )
        return 0
    for temporary in S15_CUSTODY_DIR.glob(".*.tmp"):
        try:
            if temporary.is_file() and not temporary.is_symlink():
                temporary.unlink()
        except OSError as exc:
            log_error(f"[S15_CUSTODY_TEMP_PRUNE_FAILED] {temporary}: {exc}")
    restored = 0
    for path in sorted(S15_CUSTODY_DIR.glob("*.json")):
        try:
            code, state = _load_fast_state_journal(path)
            status = str(state.get("status") or "").upper()
            if status in {"DONE", "CANCELLED", "FAILED", "BLOCKED"}:
                if not _clear_fast_state_journal(code):
                    raise ValueError("s15_terminal_journal_clear_failed")
                continue
            with FAST_LOCK:
                if code in FAST_TRADE_STATE:
                    raise ValueError("s15_custody_duplicate_runtime_state")
                FAST_TRADE_STATE[code] = state
            restored += 1
            _start_s15_recovery_thread(code, state)
        except Exception as exc:
            log_error(f"[S15_CUSTODY_RESTORE_BLOCKED] {path}: {exc}")
    return restored


def _s15_inventory_and_orders(code):
    if not _s15_symbol_allocation_unambiguous(code):
        return None, (), "same_symbol_custody_allocation_ambiguous"
    inventory, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(
        KIWOOM_TOKEN
    )
    normalized_exchanges = {
        str(exchange or "").strip().upper() for exchange in successful_exchanges or ()
    }
    if not _S15_REQUIRED_EXCHANGES.issubset(normalized_exchanges):
        return None, (), "partial_venue_inventory_snapshot"
    quantity = 0
    weighted_amount = 0
    for row in inventory or ():
        if str(row.get("code") or "").strip()[:6] != code:
            continue
        row_qty = _strict_nonnegative_int(row.get("qty"))
        row_price = _strict_nonnegative_int(
            row.get("buy_price")
            or row.get("purchase_price")
            or row.get("pchs_avg_pric")
        )
        if row_qty is None or row_price is None:
            return None, (), "inventory_numeric_contract_invalid"
        quantity += row_qty
        weighted_amount += row_qty * row_price
    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
        KIWOOM_TOKEN,
        all_stk_tp="0",
        trde_tp="0",
        stex_tp="0",
    )
    if not bool((meta or {}).get("request_succeeded", False)):
        return None, (), "unfilled_order_snapshot_failed"
    matching_orders = [
        row for row in rows or () if str(row.get("code") or "").strip()[:6] == code
    ]
    parsed_remaining = [
        _strict_nonnegative_int(row.get("remaining_qty")) for row in matching_orders
    ]
    if any(remaining is None for remaining in parsed_remaining):
        return None, (), "open_order_numeric_contract_invalid"
    orders = tuple(
        row
        for row, remaining in zip(matching_orders, parsed_remaining, strict=True)
        if remaining > 0
    )
    avg_price = int(weighted_amount / quantity) if quantity else 0
    return {"qty": quantity, "avg_price": avg_price}, orders, "exact"


def _strict_nonnegative_int(value):
    if value is None or isinstance(value, bool):
        return None
    normalized = str(value).strip()
    if not re.fullmatch(r"[+]?(?:\d{1,3}(?:,\d{3})+|\d+)", normalized):
        return None
    return int(normalized.replace(",", ""))


def _s15_symbol_allocation_unambiguous(code):
    """Require the S15 shadow to be the only active owner of this symbol."""

    if DB is None:
        return False
    try:
        with DB.get_session() as session:
            rows = (
                session.query(RecommendationHistory)
                .filter(
                    RecommendationHistory.stock_code == code,
                    RecommendationHistory.status.in_(
                        ("BUY_ORDERED", "HOLDING", "SELL_ORDERED")
                    ),
                )
                .all()
            )
        active = [
            row for row in rows if str(row.strategy or "").upper() != "S15_CANDID"
        ]
        return (
            bool(active)
            and all(str(row.strategy or "").upper() == "S15_FAST" for row in active)
            and len(active) == 1
        )
    except Exception as exc:
        log_error(f"[S15_CUSTODY_ALLOCATION_CHECK_FAILED] {code}: {exc}")
        return False


def _s15_order_side(row):
    side = str(row.get("side") or "").strip().upper()
    if side in {"BUY", "B", "2", "매수"}:
        return "BUY"
    if side in {"SELL", "S", "1", "매도"}:
        return "SELL"
    return "UNKNOWN"


def _s15_order_no(row):
    return str(
        row.get("order_no") or row.get("ord_no") or row.get("odno") or ""
    ).strip()


def _start_s15_recovery_thread(code, state):
    with state["lock"]:
        if state.get("_recovery_thread_active"):
            return False
        state["_recovery_thread_active"] = True
    thread = threading.Thread(
        target=_recover_s15_custody,
        args=(code, state),
        name=f"s15-custody-{code}",
        daemon=True,
    )
    _S15_RECOVERY_THREADS.add(thread)
    try:
        thread.start()
    except Exception:
        with state["lock"]:
            state["_recovery_thread_active"] = False
        _S15_RECOVERY_THREADS.discard(thread)
        raise
    return True


def _recover_s15_custody(code, state):
    """Reconcile open BUY/SELL orders before placing one exact residual exit."""

    try:
        poll_attempt = 0
        while True:
            poll_attempt += 1
            with state["lock"]:
                receipt_complete = bool(
                    int(state.get("cum_buy_qty", 0) or 0) > 0
                    and int(state.get("cum_sell_qty", 0) or 0)
                    == int(state.get("cum_buy_qty", 0) or 0)
                    and state.get("sell_receipt_position_complete") is True
                    and state.get("sell_receipt_economics_complete") is True
                )
            if receipt_complete:
                _finalize_s15_completed_state(code, state)
                return
            snapshot, open_orders, reason = _s15_inventory_and_orders(code)
            if snapshot is None:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = reason
                _persist_fast_state(code, state)
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            open_buys = [row for row in open_orders if _s15_order_side(row) == "BUY"]
            open_sells = [row for row in open_orders if _s15_order_side(row) == "SELL"]
            if any(not _s15_order_no(row) for row in open_buys + open_sells):
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "open_order_identity_missing"
                _persist_fast_state(code, state)
                return

            if open_buys:
                for row in open_buys:
                    kiwoom_orders.send_cancel_order(
                        code=code,
                        orig_ord_no=_s15_order_no(row),
                        token=KIWOOM_TOKEN,
                        qty=0,
                    )
                with state["lock"]:
                    state["status"] = "BUY_CANCEL_RECONCILING"
                    state["s15_recovery_reason"] = "open_buy_terminal_pending"
                _persist_fast_state(code, state)
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            qty = int(snapshot["qty"])
            with state["lock"]:
                state["cum_buy_qty"] = max(int(state.get("cum_buy_qty", 0) or 0), qty)
                if int(state.get("avg_buy_price", 0) or 0) <= 0:
                    state["avg_buy_price"] = int(snapshot["avg_price"])
                sold_qty = int(state.get("cum_sell_qty", 0) or 0)
                known_position_qty = max(
                    0, int(state.get("cum_buy_qty", 0) or 0) - sold_qty
                )

            if qty == 0:
                if known_position_qty == 0 and not open_sells:
                    with state["lock"]:
                        if int(state.get("cum_buy_qty", 0) or 0) == 0:
                            state["status"] = "CANCELLED"
                            update_s15_shadow_record(
                                state.get("shadow_id"), status="EXPIRED"
                            )
                            _persist_fast_state(code, state)
                            _pop_fast_state(code)
                            return
                        state["status"] = "EXIT_RECEIPT_PENDING"
                        state["s15_recovery_reason"] = (
                            "zero_inventory_exact_sell_receipt_pending"
                        )
                    _persist_fast_state(code, state)
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            if len(open_sells) > 1:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "multiple_open_sell_orders"
                _persist_fast_state(code, state)
                return
            if open_sells:
                with state["lock"]:
                    state["sell_ord_no"] = _s15_order_no(open_sells[0])
                    state["status"] = "EXIT_SENT"
                _persist_fast_state(code, state)
                update_s15_shadow_record(
                    state.get("shadow_id"),
                    status="SELL_ORDERED",
                    scale_in_locked=True,
                )
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            exit_response = _send_exit_best_ioc(code, qty, KIWOOM_TOKEN)
            exit_order_no = _extract_ord_no(exit_response)
            if not _is_ok_response(exit_response) or not exit_order_no:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "residual_exit_not_exactly_accepted"
                _persist_fast_state(code, state)
                return
            with state["lock"]:
                state["sell_ord_no"] = exit_order_no
                state["status"] = "EXIT_RETRY"
                state["s15_recovery_reason"] = "exact_residual_exit_submitted"
            _persist_fast_state(code, state)
            update_s15_shadow_record(
                state.get("shadow_id"),
                status="SELL_ORDERED",
                scale_in_locked=True,
            )
            time.sleep(1.0 if poll_attempt <= 120 else 30.0)
    except Exception as exc:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = f"recovery_exception:{exc}"
        _persist_fast_state(code, state)
        log_error(f"[S15_CUSTODY_RECOVERY_FAILED] {code}: {exc}")
    finally:
        with state["lock"]:
            state["_recovery_thread_active"] = False
        _S15_RECOVERY_THREADS.discard(threading.current_thread())


def create_s15_shadow_record(code, name):
    if DB is None:
        return None
    try:
        with DB.get_session() as session:
            record = RecommendationHistory(
                rec_date=datetime.now().date(),
                stock_code=code,
                stock_name=name,
                buy_price=0,
                trade_type="SCALP",
                strategy="S15_FAST",
                status="WATCHING",
                position_tag="S15_FAST",
            )
            session.add(record)
            session.flush()
            return record.id
    except Exception as exc:
        log_error(f"🚨 S15 shadow record 생성 실패 ({code}): {exc}")
        return None


def update_s15_shadow_record(shadow_id, **kwargs):
    if DB is None:
        return False
    if not shadow_id:
        return False
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory).filter_by(id=shadow_id).first()
            )
            if not record:
                return False
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
        return True
    except Exception as exc:
        log_error(f"🚨 S15 shadow record 갱신 실패 ({shadow_id}): {exc}")
        return False


def _finalize_s15_completed_state(code, state):
    with state["lock"]:
        if state.get("s15_completion_committed") is True:
            if not _clear_fast_state_journal(code):
                return False
            with FAST_LOCK:
                FAST_TRADE_STATE.pop(code, None)
            return True
        buy_qty = int(state.get("cum_buy_qty", 0) or 0)
        sell_qty = int(state.get("cum_sell_qty", 0) or 0)
        exact = bool(
            buy_qty > 0
            and sell_qty == buy_qty
            and state.get("sell_receipt_position_complete") is True
            and state.get("sell_receipt_economics_complete") is True
        )
        if not exact:
            return False
        final_buy = int(state.get("avg_buy_price", 0) or 0)
        final_sell = int(state.get("avg_sell_price", 0) or 0)
        final_profit_rate = (
            calculate_net_profit_rate(final_buy, final_sell)
            if final_buy > 0 and final_sell > 0
            else 0.0
        )
        shadow_id = state.get("shadow_id")
        name = str(state.get("name") or code)
        state["s15_final_pending_db_commit"] = True
    if not _persist_fast_state(code, state):
        return False
    committed = update_s15_shadow_record(
        shadow_id,
        status="COMPLETED",
        sell_price=final_sell,
        sell_time=datetime.now(),
        profit_rate=final_profit_rate,
        buy_price=final_buy,
        buy_qty=buy_qty,
        scale_in_locked=False,
    )
    if not committed:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "completion_db_commit_failed"
        _persist_fast_state(code, state)
        return False
    with state["lock"]:
        state["status"] = "DONE"
        state["s15_completion_committed"] = True
        state.pop("s15_final_pending_db_commit", None)
        state.pop("s15_recovery_reason", None)
    # Replace the pending marker with an idempotent committed marker before
    # unlinking it.  If unlink fails, the next boot can clear the committed
    # marker without replaying the DB completion or any order transition.
    if not _persist_fast_state(code, state):
        return False
    _log_s15_event(
        "s15_fast_track_completed",
        code,
        name,
        s15_condition_role="fast_track_exit",
        shadow_id=shadow_id,
        buy_price=final_buy,
        sell_price=final_sell,
        buy_qty=buy_qty,
        profit_rate=final_profit_rate,
    )
    if not _clear_fast_state_journal(code):
        return False
    with FAST_LOCK:
        FAST_TRADE_STATE.pop(code, None)
    return True


def _send_s15_limit_buy(code, qty, price):
    return kiwoom_orders.send_buy_order_market(
        code=code, qty=qty, token=KIWOOM_TOKEN, order_type="00", price=int(price)
    )


def _send_s15_limit_sell(code, qty, price):
    return kiwoom_orders.send_sell_order_market(
        code=code, qty=qty, token=KIWOOM_TOKEN, order_type="00", price=int(price)
    )


def _send_s15_market_sell(code, qty):
    return kiwoom_orders.send_sell_order_market(
        code=code, qty=qty, token=KIWOOM_TOKEN, order_type="3"
    )


def _send_exit_best_ioc(code, qty, token):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    return kiwoom_orders.send_sell_order_market(
        code=code, qty=qty, token=token, order_type="16"
    )


def _extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get("ord_no", "") or res.get("odno", "") or "")
    return ""


def _is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get("return_code", res.get("rt_cd", ""))) == "0"
    return bool(res)


def _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.5):
    until = _now_ts() + wait_sec
    while _now_ts() < until:
        with state["lock"]:
            rem_qty = max(0, state["cum_buy_qty"] - state["cum_sell_qty"])
        if rem_qty == 0:
            return 0
        time.sleep(0.05)
    try:
        snapshot, _open_orders, reason = _s15_inventory_and_orders(code)
        if snapshot is not None:
            return int(snapshot["qty"])
        log_info(f"⚠️ S15 잔량 exact 재조회 실패 ({code}): {reason}")
    except Exception as exc:
        log_info(f"⚠️ S15 잔량 exact 재조회 실패 ({code}): {exc}")
    return None


def execute_fast_track_scalp_v2(code, name, trigger_price, ratio=0.10):
    state = _get_fast_state(code)
    if not state:
        return
    try:
        cleanup_allowed = False
        actual_entry_happened = False
        if is_trading_paused():
            with state["lock"]:
                state["status"] = "BLOCKED"
                state["updated_at"] = _now_ts()
            cleanup_allowed = True
            log_info(
                f"[TRADING_PAUSED_BLOCK] S15 fast-track buy skipped "
                f"{name}({code}) state=신규 매수 및 추가매수 중단 상태"
            )
            update_s15_shadow_record(
                state.get("shadow_id"),
                status="WATCHING",
                position_tag="S15_FAST_PAUSED",
            )
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="trading_paused",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
            )
            return

        rt_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
        curr_price = int(float((rt_data or {}).get("curr", 0) or 0))
        if curr_price <= 0:
            curr_price = int(trigger_price or 0)
        if curr_price <= 0:
            state["status"] = "FAILED"
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="missing_price",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
            )
            return

        if AI_ENGINE is None:
            state["status"] = "FAILED"
            log_error(f"🚨 S15 AI_ENGINE 미초기화 ({code})")
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
            _log_s15_event(
                "s15_fast_track_failed",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="ai_engine_missing",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                curr_price=curr_price,
            )
            return

        ticks = kiwoom_utils.get_tick_history_ka10003(KIWOOM_TOKEN, code, limit=10)
        candle_session = resolve_entry_candle_session()
        candle_venue = resolve_entry_candle_venue(
            rt_data or {},
            session=candle_session,
        )
        candle_axis_active = entry_candle_context_enabled(
            venue=candle_venue,
            session=candle_session,
        )
        recent_candles = []
        candle_context = None
        if candle_axis_active:
            recent_candles, candle_source_meta = fetch_entry_candles_with_meta(
                KIWOOM_TOKEN,
                code,
                rt_data or {},
                venue=candle_venue,
                session=candle_session,
                limit=40,
            )
            candle_context = build_entry_candle_context(
                KIWOOM_TOKEN,
                code,
                rt_data or {},
                venue=candle_venue,
                session=candle_session,
                limit=40,
                model_bar_limit=20,
                recent_candles=recent_candles,
                source_meta=candle_source_meta,
                include_investor_source=True,
            )
        ai_res = AI_ENGINE.analyze_target(
            name,
            rt_data or {"curr": curr_price, "orderbook": {"asks": [], "bids": []}},
            ticks,
            recent_candles=recent_candles,
            strategy="SCALPING",
            candle_context=candle_context,
        )

        s15_buy_score_threshold = int(
            getattr(TRADING_RULES, "BUY_SCORE_THRESHOLD", 75) or 75
        )
        s15_score_prior = evaluate_ai_score_prior(
            ai_res.get("action"),
            ai_res.get("score", 0),
            {"BUY_SCORE_THRESHOLD": s15_buy_score_threshold},
            usable=True,
        )
        if ai_res.get("action") != "BUY":
            block_reason = "ai_not_buy"
            state["status"] = "FAILED"
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason=block_reason,
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                curr_price=curr_price,
                ai_action=ai_res.get("action"),
                ai_score=ai_res.get("score", 0),
                ai_score_threshold=s15_buy_score_threshold,
                s15_score_gate_converted_to_prior=True,
                s15_score_prior_band=s15_score_prior.get("score_prior_band"),
                s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
                s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
                s15_hard_gate_veto=False,
            )
            return

        deposit = kiwoom_orders.get_deposit(KIWOOM_TOKEN)
        req_qty = kiwoom_orders.calc_buy_qty(curr_price, deposit, ratio=ratio)
        if req_qty <= 0:
            state["status"] = "FAILED"
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="qty_zero",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                curr_price=curr_price,
                deposit=deposit,
                requested_qty=req_qty,
                ai_action=ai_res.get("action"),
                ai_score=ai_res.get("score", 0),
                ai_score_threshold=s15_buy_score_threshold,
                s15_score_gate_converted_to_prior=True,
                s15_score_prior_band=s15_score_prior.get("score_prior_band"),
                s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
                s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
                s15_hard_gate_veto=False,
            )
            return

        latency_gate = evaluate_live_buy_entry(
            stock=state,
            code=code,
            ws_data=rt_data,
            strategy_id="S15_FAST",
            planned_qty=req_qty,
            signal_price=int(trigger_price or curr_price),
            signal_strength=float(ai_res.get("score", 0) or 0) / 100.0,
            target_buy_price=0,
        )
        if not latency_gate.get("allowed"):
            state["status"] = "BLOCKED"
            state["updated_at"] = _now_ts()
            log_info(
                f"[LATENCY_ENTRY_BLOCK] S15 {name}({code}) "
                f"decision={latency_gate.get('decision')} "
                f"latency={latency_gate.get('latency_state')} "
                f"reason={latency_gate.get('reason')} "
                f"signal={latency_gate.get('signal_price')} latest={latency_gate.get('latest_price')}"
            )
            update_s15_shadow_record(
                state.get("shadow_id"),
                status="WATCHING",
                position_tag="S15_FAST_LATENCY_BLOCKED",
            )
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="latency_block",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                curr_price=curr_price,
                requested_qty=req_qty,
                latency_decision=latency_gate.get("decision"),
                latency_state=latency_gate.get("latency_state"),
                latency_reason=latency_gate.get("reason"),
                ai_score=ai_res.get("score", 0),
                ai_score_threshold=s15_buy_score_threshold,
                s15_score_gate_converted_to_prior=True,
                s15_score_prior_band=s15_score_prior.get("score_prior_band"),
                s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
                s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
                s15_hard_gate_veto=False,
            )
            return

        buy_price = int(
            float(latency_gate.get("order_price", curr_price) or curr_price)
        )

        buy_res = _send_s15_limit_buy(code, req_qty, buy_price)
        if not _is_ok_response(buy_res):
            state["status"] = "FAILED"
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
            _log_s15_event(
                "s15_trigger_blocked",
                code,
                name,
                s15_condition_role="fast_track_submit",
                s15_block_reason="order_rejected",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                curr_price=curr_price,
                requested_qty=req_qty,
                order_price=buy_price,
                ai_score=ai_res.get("score", 0),
                ai_score_threshold=s15_buy_score_threshold,
                s15_score_gate_converted_to_prior=True,
                s15_score_prior_band=s15_score_prior.get("score_prior_band"),
                s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
                s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
                s15_hard_gate_veto=False,
                broker_return_code=(
                    (buy_res or {}).get("return_code")
                    if isinstance(buy_res, dict)
                    else ""
                ),
                broker_reason=(
                    (buy_res or {}).get("msg") if isinstance(buy_res, dict) else ""
                ),
            )
            return

        buy_route_fields = buy_res if isinstance(buy_res, dict) else {}
        accepted_buy_order_no = _extract_ord_no(buy_res)
        with state["lock"]:
            state["status"] = (
                "BUY_SENT" if accepted_buy_order_no else "RECOVERY_REQUIRED"
            )
            state["buy_ord_no"] = accepted_buy_order_no
            state["req_buy_qty"] = req_qty
            state["entry_execution_broker_route"] = str(
                buy_route_fields.get("broker_route")
                or buy_route_fields.get("effective_dmst_stex_tp")
                or "UNKNOWN"
            ).upper()
            state["entry_execution_broker_route_resolution"] = str(
                buy_route_fields.get("broker_route_resolution")
                or "response_route_missing"
            )
            state["updated_at"] = _now_ts()
        if not _persist_fast_state(code, state):
            return
        update_s15_shadow_record(state.get("shadow_id"), status="BUY_ORDERED")
        _log_s15_event(
            "s15_fast_track_submitted",
            code,
            name,
            actual_order_submitted=True,
            s15_condition_role="fast_track_submit",
            shadow_id=state.get("shadow_id"),
            trigger_price=trigger_price,
            curr_price=curr_price,
            requested_qty=req_qty,
            order_price=buy_price,
            broker_order_no=state.get("buy_ord_no", ""),
            broker_route=state.get("entry_execution_broker_route", "UNKNOWN"),
            broker_route_resolution=state.get(
                "entry_execution_broker_route_resolution",
                "response_route_missing",
            ),
            ai_action=ai_res.get("action"),
            ai_score=ai_res.get("score", 0),
            ai_score_threshold=s15_buy_score_threshold,
            s15_score_gate_converted_to_prior=True,
            s15_score_prior_band=s15_score_prior.get("score_prior_band"),
            s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
            s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
            s15_hard_gate_veto=False,
        )
        if not accepted_buy_order_no:
            with state["lock"]:
                state["s15_recovery_reason"] = "accepted_buy_order_number_missing"
            _persist_fast_state(code, state)
            _start_s15_recovery_thread(code, state)
            return

        expire_at = _now_ts() + 20.0
        while _now_ts() < expire_at:
            with state["lock"]:
                if state["cum_buy_qty"] >= req_qty:
                    break
            time.sleep(0.1)

        with state["lock"]:
            real_buy_qty = state["cum_buy_qty"]
            avg_buy_price = state["avg_buy_price"]
            buy_ord_no = state.get("buy_ord_no", "")
        if real_buy_qty > 0:
            actual_entry_happened = True

        if real_buy_qty <= 0:
            if buy_ord_no:
                kiwoom_orders.send_cancel_order(
                    code=code,
                    orig_ord_no=buy_ord_no,
                    token=KIWOOM_TOKEN,
                    qty=0,
                    dmst_stex_tp=state.get("entry_execution_broker_route"),
                )
            with state["lock"]:
                state["status"] = "BUY_CANCEL_RECONCILING"
                state["s15_recovery_reason"] = "no_fill_timeout_terminal_pending"
            _persist_fast_state(code, state)
            _log_s15_event(
                "s15_fast_track_cancelled",
                code,
                name,
                s15_condition_role="fast_track_submit",
                shadow_id=state.get("shadow_id"),
                trigger_price=trigger_price,
                requested_qty=req_qty,
                filled_qty=real_buy_qty,
                broker_order_no=buy_ord_no,
                s15_cancel_reason="no_fill_after_20s",
                ai_action=ai_res.get("action"),
                ai_score=ai_res.get("score", 0),
                ai_score_threshold=s15_buy_score_threshold,
                s15_score_gate_converted_to_prior=True,
                s15_score_prior_band=s15_score_prior.get("score_prior_band"),
                s15_ai_score_prior_weight=s15_score_prior.get("ai_score_prior_weight"),
                s15_score_prior_reason=s15_score_prior.get("score_prior_reason"),
                s15_hard_gate_veto=False,
            )
            _start_s15_recovery_thread(code, state)
            return

        if real_buy_qty < req_qty and buy_ord_no:
            kiwoom_orders.send_cancel_order(
                code=code,
                orig_ord_no=buy_ord_no,
                token=KIWOOM_TOKEN,
                qty=0,
                dmst_stex_tp=state.get("entry_execution_broker_route"),
            )
            with state["lock"]:
                state["status"] = "BUY_CANCEL_RECONCILING"
                state["s15_recovery_reason"] = "partial_buy_terminal_pending"
            _persist_fast_state(code, state)
            _start_s15_recovery_thread(code, state)
            return

        if avg_buy_price <= 0:
            avg_buy_price = buy_price

        target_price = _target_price_pct_up(avg_buy_price, 1.8)
        stop_price = int(avg_buy_price * (1 - 0.007))

        with state["lock"]:
            state["status"] = "HOLDING"
            state["target_price"] = target_price
            state["stop_price"] = stop_price
            state["updated_at"] = _now_ts()
        if not _persist_fast_state(code, state):
            return
        update_s15_shadow_record(
            state.get("shadow_id"),
            status="HOLDING",
            buy_price=avg_buy_price,
            buy_qty=real_buy_qty,
            scale_in_locked=True,
        )
        _log_s15_event(
            "s15_fast_track_holding",
            code,
            name,
            s15_condition_role="fast_track_holding",
            shadow_id=state.get("shadow_id"),
            trigger_price=trigger_price,
            avg_buy_price=avg_buy_price,
            buy_qty=real_buy_qty,
            target_price=target_price,
            stop_price=stop_price,
        )

        sell_res = _send_s15_limit_sell(code, real_buy_qty, target_price)
        sell_route_fields = sell_res if isinstance(sell_res, dict) else {}
        with state["lock"]:
            state["sell_execution_broker_route"] = str(
                sell_route_fields.get("broker_route")
                or sell_route_fields.get("effective_dmst_stex_tp")
                or state.get("entry_execution_broker_route")
                or "UNKNOWN"
            ).upper()
            state["sell_execution_broker_route_resolution"] = str(
                sell_route_fields.get("broker_route_resolution")
                or "response_route_missing"
            )

        if not _is_ok_response(sell_res):
            print(
                f"🚨 [S15 Fail-safe] {name} 익절 지정가 매도 세팅 실패. 보호 상태 유지 후 최유리(IOC) 청산 시도."
            )
            with state["lock"]:
                state["status"] = "HOLDING_NEEDS_EXIT"
                state["updated_at"] = _now_ts()

            update_s15_shadow_record(state.get("shadow_id"), status="HOLDING")

            rem_qty = _confirm_s15_cancel_or_reload_remaining(code, state, wait_sec=0.3)
            if rem_qty is None:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "residual_inventory_unknown"
            elif rem_qty > 0:
                emergency_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                emergency_order_no = _extract_ord_no(emergency_res)
                if _is_ok_response(emergency_res) and emergency_order_no:
                    with state["lock"]:
                        state["sell_ord_no"] = emergency_order_no
                        state["status"] = "EXIT_RETRY"
                        state["updated_at"] = _now_ts()
                    _persist_fast_state(code, state)
                    update_s15_shadow_record(
                        state.get("shadow_id"),
                        status="SELL_ORDERED",
                        scale_in_locked=True,
                    )
                else:
                    print(
                        f"🚨 [S15 Fail-safe] {name} 긴급 청산 주문도 실패. 상태 유지 및 관리자 알림 필요."
                    )
            else:
                print(
                    f"ℹ️ [S15 Fail-safe] {name} 재조회 결과 잔량 없음. 자연 종료 가능."
                )

            _start_s15_recovery_thread(code, state)
            return

        sell_order_no = _extract_ord_no(sell_res)
        if not sell_order_no:
            with state["lock"]:
                state["status"] = "RECOVERY_REQUIRED"
                state["s15_recovery_reason"] = "accepted_sell_order_number_missing"
            _persist_fast_state(code, state)
            _start_s15_recovery_thread(code, state)
            return
        with state["lock"]:
            state["sell_ord_no"] = sell_order_no
            state["status"] = "EXIT_SENT"
            state["updated_at"] = _now_ts()
        if not _persist_fast_state(code, state):
            return
        update_s15_shadow_record(
            state.get("shadow_id"),
            status="SELL_ORDERED",
            scale_in_locked=True,
        )

        while True:
            time.sleep(0.1)

            with state["lock"]:
                if (
                    state["cum_sell_qty"] == state["cum_buy_qty"] > 0
                    and state.get("sell_receipt_position_complete") is True
                    and state.get("sell_receipt_economics_complete") is True
                ):
                    state["status"] = "DONE"
                    cleanup_allowed = True
                    break

            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
            curr_p = int(float((rt or {}).get("curr", 0) or 0))
            if curr_p <= 0 or avg_buy_price <= 0:
                continue

            profit_rate = calculate_net_profit_rate(avg_buy_price, curr_p)
            if profit_rate <= -0.7:
                with state["lock"]:
                    sell_ord_no = state.get("sell_ord_no", "")

                if sell_ord_no:
                    cancel_res = kiwoom_orders.send_cancel_order(
                        code=code,
                        orig_ord_no=sell_ord_no,
                        token=KIWOOM_TOKEN,
                        qty=0,
                        dmst_stex_tp=state.get("sell_execution_broker_route"),
                    )
                    if _is_ok_response(cancel_res):
                        with state["lock"]:
                            state["pending_cancel_ord_no"] = sell_ord_no
                with state["lock"]:
                    state["status"] = "SELL_CANCEL_RECONCILING"
                    state["s15_recovery_reason"] = "stop_exit_terminal_pending"
                _persist_fast_state(code, state)
                _start_s15_recovery_thread(code, state)
                break

        with state["lock"]:
            exact_done = state.get("status") == "DONE"
        if not exact_done:
            return

        if not _finalize_s15_completed_state(code, state):
            cleanup_allowed = False
    except Exception as exc:
        log_error(f"🚨 S15 Fast-Track 에러 ({code}): {exc}")
        with state["lock"]:
            broker_order_may_exist = bool(
                state.get("buy_ord_no")
                or state.get("sell_ord_no")
                or int(state.get("cum_buy_qty", 0) or 0) > 0
            )
            if broker_order_may_exist:
                state["status"] = "RECOVERY_REQUIRED"
                state["s15_recovery_reason"] = f"runtime_exception:{exc}"
            else:
                state["status"] = "FAILED"
                cleanup_allowed = True
        if broker_order_may_exist:
            _persist_fast_state(code, state)
            _start_s15_recovery_thread(code, state)
        else:
            update_s15_shadow_record(state.get("shadow_id"), status="EXPIRED")
        _log_s15_event(
            "s15_fast_track_failed",
            code,
            name,
            s15_condition_role="fast_track_submit",
            s15_block_reason="exception",
            shadow_id=(
                (state or {}).get("shadow_id") if isinstance(state, dict) else None
            ),
            error=str(exc),
        )
    finally:
        if actual_entry_happened:
            _block_s15_reentry(code)
        _unarm_s15_candidate(code)
        with state["lock"]:
            safe_no_order_terminal = bool(
                str(state.get("status") or "").upper()
                in {"BLOCKED", "CANCELLED", "FAILED"}
                and not str(state.get("buy_ord_no") or "").strip()
                and not str(state.get("sell_ord_no") or "").strip()
                and int(state.get("cum_buy_qty", 0) or 0) == 0
                and int(state.get("cum_sell_qty", 0) or 0) == 0
            )
        if cleanup_allowed or safe_no_order_terminal:
            _pop_fast_state(code)
