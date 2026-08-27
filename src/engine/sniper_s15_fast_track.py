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
_S15_SELL_TERMINAL_MARKER_KEYS = (
    "s15_sell_terminal_outcome_kind",
    "s15_sell_terminal_outcome_generation",
    "s15_sell_terminal_outcome_context_sha256",
    "s15_sell_terminal_outcome_target_id",
    "s15_sell_terminal_outcome_code",
    "s15_sell_terminal_outcome_owner_position_qty",
    "s15_sell_terminal_outcome_requested_qty",
    "s15_sell_terminal_outcome_intended_route",
    "s15_sell_terminal_outcome_intended_effective_venue",
    "s15_sell_terminal_outcome_intended_session_bucket",
)


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
            from src.engine import sniper_execution_receipts as _receipt_handlers

            shadow_id = int(state.get("shadow_id") or state.get("id") or 0)
            position_qty = max(
                int(state.get("buy_qty") or 0),
                int(state.get("cum_buy_qty") or 0),
            )
            db_owner_exact = False
            db_status = ""
            if DB is not None and shadow_id > 0 and position_qty > 0:
                try:
                    with DB.get_session() as session:
                        record = (
                            session.query(RecommendationHistory)
                            .filter_by(
                                id=shadow_id,
                                stock_code=code,
                                buy_qty=position_qty,
                            )
                            .first()
                        )
                    db_status = str(getattr(record, "status", "") or "").upper()
                    db_owner_exact = bool(
                        record is not None
                        and str(getattr(record, "strategy", "") or "").upper()
                        == "S15_FAST"
                    )
                except Exception as exc:
                    state["s15_pending_submit_restore_error"] = str(exc)[:240]
            restored_pending, pending_reason = (
                _receipt_handlers.load_pending_sell_submit_custody(
                    target_id=shadow_id,
                    code=code,
                    position_qty=position_qty,
                )
                if shadow_id > 0 and position_qty > 0
                else (None, "pending_submit_owner_invalid")
            )
            fast_pending = state.get("sell_submit_pending") is True
            validated_fast_context, _fast_context_reason = (
                _receipt_handlers._validated_sell_pending_submit_context(state)
            )
            fast_terminal_marker_exact = bool(
                validated_fast_context is not None
                and state.get("s15_sell_terminal_outcome_kind")
                == "definitive_reject_no_broker_order"
                and str(state.get("s15_sell_terminal_outcome_generation") or "").strip()
                == str(validated_fast_context.get("generation") or "").strip()
                and str(
                    state.get("s15_sell_terminal_outcome_context_sha256") or ""
                ).strip()
                == str(state.get("sell_submit_context_sha256") or "").strip()
                and int(state.get("s15_sell_terminal_outcome_target_id") or 0)
                == int(validated_fast_context.get("target_id") or 0)
                and str(state.get("s15_sell_terminal_outcome_code") or "").strip()
                == str(validated_fast_context.get("code") or "").strip()
                and int(state.get("s15_sell_terminal_outcome_owner_position_qty") or 0)
                == int(validated_fast_context.get("owner_position_qty") or 0)
                and int(state.get("s15_sell_terminal_outcome_requested_qty") or 0)
                == int(validated_fast_context.get("requested_qty") or 0)
                and str(
                    state.get("s15_sell_terminal_outcome_intended_route") or ""
                ).strip()
                == str(validated_fast_context.get("intended_route") or "").strip()
                and str(
                    state.get("s15_sell_terminal_outcome_intended_effective_venue")
                    or ""
                ).strip()
                == str(
                    validated_fast_context.get("intended_effective_venue") or ""
                ).strip()
                and str(
                    state.get("s15_sell_terminal_outcome_intended_session_bucket") or ""
                ).strip()
                == str(
                    validated_fast_context.get("intended_session_bucket") or ""
                ).strip()
            )
            if (
                isinstance(restored_pending, dict)
                and restored_pending.get("sell_submit_terminal_outcome_kind")
                == "definitive_reject_no_broker_order"
            ):
                state.update(restored_pending)
                state.update(
                    {
                        "id": shadow_id,
                        "code": code,
                        "status": "SELL_ORDERED",
                    }
                )
                try:
                    from src.engine import sniper_state_handlers as _state_handlers

                    terminal_recovered = bool(
                        _state_handlers._finish_definitive_sell_reject_boundary(
                            state,
                            code,
                            target_id=shadow_id,
                            generation=str(
                                restored_pending.get("sell_submit_generation") or ""
                            ),
                            db=DB,
                        )
                    )
                except Exception as exc:
                    terminal_recovered = False
                    state["s15_pending_submit_restore_error"] = str(exc)[:240]
                if terminal_recovered:
                    state["status"] = "HOLDING"
                    state["s15_recovery_reason"] = (
                        "definitive_reject_terminal_restart_recovered"
                    )
                    if not _persist_fast_state(code, state):
                        terminal_recovered = False
                if not terminal_recovered:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "definitive_reject_terminal_restart_recovery_deferred"
                    )
            elif restored_pending is not None:
                exact_fast_context = all(
                    state.get(key) == value
                    for key, value in restored_pending.items()
                    if key != "sell_submit_pending"
                )
                if not db_owner_exact or db_status != "SELL_ORDERED":
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "pending_submit_db_owner_mismatch"
                elif fast_pending and not exact_fast_context:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "pending_submit_dual_journal_context_mismatch"
                    )
                else:
                    state.update(restored_pending)
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "pending_submit_exact_restart_reconciliation"
                    )
            elif (
                fast_pending
                and fast_terminal_marker_exact
                and db_owner_exact
                and db_status == "HOLDING"
                and pending_reason == "pending_submit_journal_missing"
            ):
                for field_name in _receipt_handlers._SELL_PENDING_SUBMIT_RUNTIME_KEYS:
                    state.pop(field_name, None)
                for field_name in _S15_SELL_TERMINAL_MARKER_KEYS:
                    state.pop(field_name, None)
                state["status"] = "HOLDING"
                state["s15_recovery_reason"] = (
                    "definitive_reject_terminal_fast_journal_recovered"
                )
                if not _persist_fast_state(code, state):
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "definitive_reject_terminal_fast_journal_persist_deferred"
                    )
            elif fast_pending:
                state["status"] = "RECOVERY_REQUIRED"
                state["s15_recovery_reason"] = (
                    f"pending_submit_common_journal_invalid:{pending_reason}"
                )
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
    # Establish the order state first.  The inventory used for residual SELL
    # authority must be fetched after this snapshot so a fill that removes the
    # order cannot be hidden behind an older pre-fill balance.
    rows, meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
        KIWOOM_TOKEN,
        all_stk_tp="0",
        trde_tp="0",
        stex_tp="0",
    )
    if not bool((meta or {}).get("request_succeeded", False)):
        return None, (), "unfilled_order_snapshot_failed"
    if not bool((meta or {}).get("normalization_contract_complete", False)):
        return None, (), "open_order_snapshot_contract_incomplete"
    for row in rows or ():
        if not isinstance(row, dict):
            return None, (), "open_order_identity_or_side_invalid"
        row_code = str(row.get("code") or "").strip()[:6]
        row_remaining = _strict_nonnegative_int(row.get("remaining_qty"))
        if (
            row_remaining is not None
            and row_remaining > 0
            and re.fullmatch(r"[0-9]{6}", row_code) is None
        ):
            return None, (), "open_order_identity_or_side_invalid"
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
    for row in orders:
        order_no = _s15_order_no(row)
        if (
            re.fullmatch(r"[0-9]{7}", order_no) is None
            or int(order_no) <= 0
            or _s15_order_side(row) not in {"BUY", "SELL"}
        ):
            return None, (), "open_order_identity_or_side_invalid"
    inventory, successful_exchanges, inventory_meta = (
        kiwoom_utils.get_account_balance_kt00005_with_meta(KIWOOM_TOKEN)
    )
    if not bool((inventory_meta or {}).get("normalization_contract_complete", False)):
        return None, (), "inventory_snapshot_contract_incomplete"
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


def _s15_open_sell_matches_pending_context(row, state, *, order_no):
    """Validate one open SELL row against one already-bound S15 generation."""

    from src.engine import sniper_trade_utils as _trade_utils

    submitted_qty = _strict_nonnegative_int(row.get("qty"))
    remaining_qty = _strict_nonnegative_int(row.get("remaining_qty"))
    requested_qty = _strict_nonnegative_int(state.get("sell_submit_requested_qty"))
    intended_route = str(state.get("sell_submit_intended_route") or "").strip().upper()
    return bool(
        _s15_order_side(row) == "SELL"
        and _s15_order_no(row) == str(order_no or "").strip()
        and row.get("submitted_quantity_source_valid") is True
        and submitted_qty is not None
        and requested_qty is not None
        and submitted_qty == requested_qty
        and remaining_qty is not None
        and 0 < remaining_qty <= submitted_qty
        and _trade_utils._pending_sell_order_route(row) == intended_route
    )


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


def _reconcile_s15_positive_inventory_owner(code, state, snapshot):
    """Commit a terminal partial BUY to its exact shadow before any SELL."""

    shadow_id = int(state.get("shadow_id") or state.get("id") or 0)
    inventory_qty = int((snapshot or {}).get("qty") or 0)
    sold_qty = int(state.get("cum_sell_qty", 0) or 0)
    owner_buy_qty = int(state.get("cum_buy_qty", 0) or 0)
    receipt_buy_amount = int(state.get("cum_buy_amount", 0) or 0)
    avg_price = int(state.get("avg_buy_price", 0) or 0)
    inventory_avg_price = int((snapshot or {}).get("avg_price") or 0)
    buy_order_no = str(state.get("buy_ord_no") or "").strip()
    if (
        DB is None
        or shadow_id <= 0
        or inventory_qty <= 0
        or owner_buy_qty <= 0
        or avg_price <= 0
    ):
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "partial_buy_owner_identity_or_price_invalid"
        _persist_fast_state(code, state)
        return False
    receipt_avg_from_amount = (
        int(receipt_buy_amount / owner_buy_qty)
        if owner_buy_qty > 0 and receipt_buy_amount > 0
        else 0
    )
    if not all(
        (
            owner_buy_qty == inventory_qty + sold_qty,
            receipt_buy_amount > 0,
            avg_price > 0,
            inventory_avg_price > 0,
            avg_price == inventory_avg_price,
            receipt_avg_from_amount == avg_price,
        )
    ):
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "partial_buy_db_reconciliation_failed"
            state["s15_partial_buy_db_error"] = (
                "s15_partial_buy_receipt_inventory_economics_mismatch"
            )
        _persist_fast_state(code, state)
        return False
    if re.fullmatch(r"[0-9]{7}", buy_order_no) is None or int(buy_order_no) <= 0:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "partial_buy_db_reconciliation_failed"
            state["s15_partial_buy_db_error"] = "s15_partial_buy_order_identity_invalid"
        _persist_fast_state(code, state)
        return False
    committed = False
    try:
        with DB.get_session() as session:
            record = (
                session.query(RecommendationHistory)
                .filter_by(
                    id=shadow_id,
                    stock_code=str(code or "").strip()[:6],
                )
                .first()
            )
            record_status = str(getattr(record, "status", "") or "").upper()
            record_qty = int(getattr(record, "buy_qty", 0) or 0)
            record_buy_price = int(getattr(record, "buy_price", 0) or 0)
            strategy = str(getattr(record, "strategy", "") or "").upper()
            if record is None or strategy != "S15_FAST":
                raise RuntimeError("s15_partial_buy_db_owner_missing")
            if (
                record_status == "HOLDING"
                and record_qty == owner_buy_qty
                and record_buy_price == avg_price
            ):
                committed = True
            elif (
                record_status == "SELL_ORDERED"
                and record_qty == owner_buy_qty
                and record_buy_price == avg_price
            ):
                committed = True
            elif record_status == "BUY_ORDERED" and record_qty in {
                0,
                owner_buy_qty,
            }:
                updated_rows = (
                    session.query(RecommendationHistory)
                    .filter_by(
                        id=shadow_id,
                        stock_code=str(code or "").strip()[:6],
                        status="BUY_ORDERED",
                        buy_qty=record_qty,
                    )
                    .update(
                        {
                            "status": "HOLDING",
                            "buy_qty": owner_buy_qty,
                            "buy_price": avg_price,
                            "scale_in_locked": True,
                        }
                    )
                )
                if updated_rows != 1:
                    raise RuntimeError(
                        f"s15_partial_buy_db_owner_rowcount:{updated_rows}"
                    )
                committed = True
            else:
                raise RuntimeError(
                    "s15_partial_buy_db_owner_state_mismatch:"
                    f"{record_status}:{record_qty}"
                )
    except Exception as exc:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "partial_buy_db_reconciliation_failed"
            state["s15_partial_buy_db_error"] = str(exc)[:240]
        _persist_fast_state(code, state)
        return False
    if not committed:
        return False
    with state["lock"]:
        state["buy_qty"] = owner_buy_qty
        state["cum_buy_qty"] = owner_buy_qty
        state["avg_buy_price"] = avg_price
        state["status"] = "HOLDING"
        state["s15_partial_buy_owner_reconciled"] = True
        state.pop("s15_partial_buy_db_error", None)
    if not _persist_fast_state(code, state):
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                "partial_buy_fast_state_reconciliation_failed"
            )
        return False
    return True


def _reconcile_s15_pending_sell_cancel(code, state):
    """Let the common exact cancel boundary own one S15 SELL generation."""

    with state["lock"]:
        generation = str(state.get("sell_submit_generation") or "").strip()
        order_no = str(
            state.get("pending_cancel_ord_no")
            or state.get("sell_odno")
            or state.get("sell_ord_no")
            or ""
        ).strip()
    if not generation or not order_no:
        return None
    from src.engine import sniper_execution_receipts as _receipt_handlers
    from src.engine import sniper_state_handlers as _state_handlers

    owns_cancel = bool(
        _receipt_handlers.pending_sell_cancel_ack_exact(
            state,
            code=code,
            order_no=order_no,
        )
        or _receipt_handlers.pending_sell_cancel_intent_exact(
            state,
            code=code,
            order_no=order_no,
        )
    )
    if not owns_cancel:
        return None
    with state["lock"]:
        state["status"] = "SELL_ORDERED"
        state["sell_odno"] = order_no
        state["sell_ord_no"] = order_no
        state["sell_cancel_reconciliation_required"] = True
    released = bool(
        _state_handlers.process_sell_cancellation(
            state,
            code,
            order_no,
            DB,
        )
    )
    if released:
        with state["lock"]:
            state.pop("pending_cancel_ord_no", None)
            state["s15_recovery_reason"] = "stop_exit_cancel_terminal_released"
    else:
        with state["lock"]:
            state["status"] = "SELL_ORDERED"
            state["s15_recovery_reason"] = "stop_exit_cancel_terminal_pending"
    _persist_fast_state(code, state)
    return released


def _submit_s15_stop_cancel(
    state,
    code,
    order_no,
    *,
    allow_existing_intent_open_order_retry=False,
):
    """Fsync one S15 cancel intent before the only permitted kt10003 call."""

    from src.engine import sniper_execution_receipts as _receipt_handlers
    from src.engine import sniper_trade_utils as _trade_utils

    normalized_code = str(code or "").strip()[:6]
    normalized_order_no = str(order_no or "").strip()
    cancel_route = str(state.get("sell_submit_intended_route") or "SOR").strip().upper()
    with state["lock"]:
        generation = str(state.get("sell_submit_generation") or "").strip()
        context_sha256 = str(state.get("sell_submit_context_sha256") or "").strip()
        current_order_no = str(
            state.get("sell_odno") or state.get("sell_ord_no") or ""
        ).strip()
        if (
            not generation
            or not context_sha256
            or not normalized_code
            or not re.fullmatch(r"[0-9]{7}", normalized_order_no)
            or int(normalized_order_no) <= 0
            or (current_order_no and current_order_no != normalized_order_no)
        ):
            return False
        state["status"] = "SELL_ORDERED"
        state["sell_odno"] = normalized_order_no
        state["sell_ord_no"] = normalized_order_no
        # This marker is part of the pre-call crash boundary.  It is bound to
        # the exact SELL generation so a later generation can never inherit a
        # stale stop-cancel retry.
        state["s15_stop_cancel_retry_required"] = True
        state["s15_stop_cancel_retry_generation"] = generation
        state["s15_stop_cancel_retry_context_sha256"] = context_sha256
        state["s15_stop_cancel_retry_order_no"] = normalized_order_no
    if not _persist_fast_state(code, state):
        return False
    cancel_ack_exact = _receipt_handlers.pending_sell_cancel_ack_exact(
        state,
        code=code,
        order_no=normalized_order_no,
    )
    cancel_intent_exact = _receipt_handlers.pending_sell_cancel_intent_exact(
        state,
        code=code,
        order_no=normalized_order_no,
    )
    if cancel_ack_exact or (
        cancel_intent_exact and not allow_existing_intent_open_order_retry
    ):
        with state["lock"]:
            state.pop("s15_stop_cancel_retry_required", None)
            state.pop("s15_stop_cancel_retry_generation", None)
            state.pop("s15_stop_cancel_retry_context_sha256", None)
            state.pop("s15_stop_cancel_retry_order_no", None)
        return True
    if (
        not cancel_intent_exact
        and not _receipt_handlers.persist_pending_sell_cancel_intent_custody(
            state,
            order_no=normalized_order_no,
            broker_route=cancel_route,
        )
    ):
        return False
    cancel_res = kiwoom_orders.send_cancel_order(
        code=code,
        orig_ord_no=normalized_order_no,
        token=KIWOOM_TOKEN,
        qty=0,
        dmst_stex_tp=cancel_route,
    )
    if _trade_utils.cancel_response_ack_exact(
        cancel_res,
        intended_route=cancel_route,
        expected_orig_order_no=normalized_order_no,
        expected_code=code,
        expected_max_qty=int(state.get("sell_submit_requested_qty") or 0),
    ):
        _receipt_handlers.persist_pending_sell_cancel_ack_custody(
            state,
            order_no=normalized_order_no,
            cancel_response=cancel_res,
        )
    with state["lock"]:
        state["pending_cancel_ord_no"] = normalized_order_no
        state.pop("s15_stop_cancel_retry_required", None)
        state.pop("s15_stop_cancel_retry_generation", None)
        state.pop("s15_stop_cancel_retry_context_sha256", None)
        state.pop("s15_stop_cancel_retry_order_no", None)
    return True


def _retry_s15_stop_cancel_if_required(code, state):
    """Retry one exact open stop cancel across the bounded crash window."""

    from src.engine import sniper_execution_receipts as _receipt_handlers

    with state["lock"]:
        retry_required = state.get("s15_stop_cancel_retry_required") is True
        order_no = str(state.get("s15_stop_cancel_retry_order_no") or "").strip()
        retry_generation = str(
            state.get("s15_stop_cancel_retry_generation") or ""
        ).strip()
        retry_context_sha256 = str(
            state.get("s15_stop_cancel_retry_context_sha256") or ""
        ).strip()
        current_generation = str(state.get("sell_submit_generation") or "").strip()
        current_context_sha256 = str(
            state.get("sell_submit_context_sha256") or ""
        ).strip()
        current_order_no = str(
            state.get("sell_odno") or state.get("sell_ord_no") or ""
        ).strip()
    if not retry_required:
        return None
    if (
        not retry_generation
        or retry_generation != current_generation
        or not retry_context_sha256
        or retry_context_sha256 != current_context_sha256
        or not order_no
        or order_no != current_order_no
    ):
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "stop_exit_cancel_retry_context_mismatch"
        _persist_fast_state(code, state)
        return False
    snapshot, open_orders, snapshot_reason = _s15_inventory_and_orders(code)
    if snapshot is None:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                f"stop_exit_cancel_retry_snapshot_blocked:{snapshot_reason}"
            )
        _persist_fast_state(code, state)
        return False
    open_buys = [row for row in open_orders if _s15_order_side(row) == "BUY"]
    open_sells = [row for row in open_orders if _s15_order_side(row) == "SELL"]
    cancel_intent_exact = _receipt_handlers.pending_sell_cancel_intent_exact(
        state,
        code=code,
        order_no=order_no,
    )
    cancel_ack_exact = _receipt_handlers.pending_sell_cancel_ack_exact(
        state,
        code=code,
        order_no=order_no,
    )
    if (
        open_buys
        or len(open_sells) != 1
        or not _s15_open_sell_matches_pending_context(
            open_sells[0],
            state,
            order_no=order_no,
        )
    ):
        if cancel_intent_exact or cancel_ack_exact:
            with state["lock"]:
                state["status"] = "SELL_ORDERED"
                state["pending_cancel_ord_no"] = order_no
                state["s15_recovery_reason"] = "stop_exit_terminal_pending"
                state.pop("s15_stop_cancel_retry_required", None)
                state.pop("s15_stop_cancel_retry_generation", None)
                state.pop("s15_stop_cancel_retry_context_sha256", None)
                state.pop("s15_stop_cancel_retry_order_no", None)
            _persist_fast_state(code, state)
            return True
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                "stop_exit_cancel_retry_exact_open_order_required"
            )
        _persist_fast_state(code, state)
        return False
    if not order_no or not _submit_s15_stop_cancel(
        state,
        code,
        order_no,
        allow_existing_intent_open_order_retry=True,
    ):
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "stop_exit_cancel_intent_durability_failed"
        _persist_fast_state(code, state)
        return False
    with state["lock"]:
        state["status"] = "SELL_ORDERED"
        state["s15_recovery_reason"] = "stop_exit_terminal_pending"
        state.pop("s15_stop_cancel_retry_required", None)
        state.pop("s15_stop_cancel_retry_generation", None)
        state.pop("s15_stop_cancel_retry_context_sha256", None)
        state.pop("s15_stop_cancel_retry_order_no", None)
    _persist_fast_state(code, state)
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
            stop_cancel_retry = _retry_s15_stop_cancel_if_required(code, state)
            if stop_cancel_retry is not None:
                time.sleep(
                    0.1 if stop_cancel_retry else (1.0 if poll_attempt <= 120 else 30.0)
                )
                continue
            cancel_release = _reconcile_s15_pending_sell_cancel(code, state)
            if cancel_release is not None:
                time.sleep(
                    0.1 if cancel_release else (1.0 if poll_attempt <= 120 else 30.0)
                )
                continue
            snapshot, open_orders, reason = _s15_inventory_and_orders(code)
            if snapshot is None:
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = reason
                _persist_fast_state(code, state)
                if reason == "open_order_identity_or_side_invalid":
                    return
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            open_buys = [row for row in open_orders if _s15_order_side(row) == "BUY"]
            open_sells = [row for row in open_orders if _s15_order_side(row) == "SELL"]
            if any(
                re.fullmatch(r"[0-9]{7}", _s15_order_no(row)) is None
                or int(_s15_order_no(row)) <= 0
                for row in open_buys + open_sells
            ):
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

            if qty > 0 and not _reconcile_s15_positive_inventory_owner(
                code,
                state,
                snapshot,
            ):
                return

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

            with state["lock"]:
                pending_generation = bool(
                    state.get("sell_submit_pending") is True
                    and str(state.get("sell_submit_generation") or "").strip()
                )
                pending_order_no = str(
                    state.get("sell_odno") or state.get("sell_ord_no") or ""
                ).strip()
            if pending_generation:
                if not pending_order_no:
                    from src.engine import sniper_trade_utils as _trade_utils

                    pending_order_no, bind_reason = (
                        _trade_utils.resolve_pending_sell_order_no(
                            state,
                            KIWOOM_TOKEN,
                        )
                    )
                else:
                    if len(
                        open_sells
                    ) != 1 or not _s15_open_sell_matches_pending_context(
                        open_sells[0],
                        state,
                        order_no=pending_order_no,
                    ):
                        with state["lock"]:
                            state["status"] = "RECOVERY_REQUIRED"
                            state["s15_recovery_reason"] = (
                                "pending_sell_order_open_identity_conflict"
                            )
                        _persist_fast_state(code, state)
                        time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                        continue
                    bind_reason = "pending_sell_order_already_bound_exact_open_row"
                with state["lock"]:
                    if pending_order_no:
                        state["sell_odno"] = pending_order_no
                        state["sell_ord_no"] = pending_order_no
                        state["status"] = "EXIT_SENT"
                        state["s15_recovery_reason"] = bind_reason
                    else:
                        state["status"] = "RECOVERY_REQUIRED"
                        state["s15_recovery_reason"] = (
                            f"pending_sell_order_number_unresolved:{bind_reason}"
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
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "open_sell_without_pending_generation"
                    )
                _persist_fast_state(code, state)
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue

            residual_route = (
                str(kiwoom_orders.resolve_order_dmst_stex_tp() or "SOR").strip().upper()
            )
            residual_submit = _arm_s15_pending_sell_submit(
                state,
                code,
                qty,
                route=residual_route,
                kind="recovery_residual_ioc",
            )
            if residual_submit is None:
                return
            try:
                exit_response = _send_exit_best_ioc(code, qty, KIWOOM_TOKEN)
            except Exception as exc:
                exit_response = {"return_code": "exception", "return_msg": str(exc)}
            residual_state, exit_order_no, residual_error = _classify_s15_sell_response(
                exit_response
            )
            if _s15_receipt_first_response_handled(
                state,
                code,
                submit=residual_submit,
                response_state=residual_state,
                response_order_no=exit_order_no,
                qty=qty,
            ):
                time.sleep(1.0 if poll_attempt <= 120 else 30.0)
                continue
            if residual_state == "ambiguous":
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "residual_exit_response_ambiguous"
                    state["s15_sell_submit_response_error"] = residual_error[:240]
                _persist_fast_state(code, state)
                return
            if residual_state in {"definitive_reject", "local_no_call"}:
                if not _clear_s15_pending_sell_submit(
                    state,
                    generation=residual_submit["generation"],
                ):
                    with state["lock"]:
                        state["status"] = "RECOVERY_REQUIRED"
                        state["s15_recovery_reason"] = (
                            "residual_exit_reject_boundary_incomplete"
                        )
                    _persist_fast_state(code, state)
                    return
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = "residual_exit_rejected"
                    state["s15_sell_submit_response_error"] = residual_error[:240]
                _persist_fast_state(code, state)
                return
            with state["lock"]:
                state["sell_ord_no"] = exit_order_no
                state["status"] = "EXIT_RETRY"
                state["s15_recovery_reason"] = "exact_residual_exit_submitted"
            if not _persist_fast_state(code, state):
                return
            _log_s15_sell_order_sent(
                state,
                code,
                order_no=exit_order_no,
                qty=qty,
            )
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


def _classify_s15_sell_response(response):
    if kiwoom_orders.is_verified_local_sell_no_call_response(response):
        return (
            "local_no_call",
            "",
            str(response.get("return_msg") or "sell_time_blocked"),
        )
    if not isinstance(response, dict):
        return "ambiguous", "", "non_dict_or_missing_response"
    has_code = "return_code" in response or "rt_cd" in response
    raw_return_code = response.get("return_code", response.get("rt_cd", ""))
    return_code = (
        ""
        if raw_return_code is None or isinstance(raw_return_code, bool)
        else str(raw_return_code).strip()
    )
    order_no = _extract_ord_no(response).strip()
    message = str(
        response.get("return_msg")
        or response.get("msg1")
        or response.get("err_msg")
        or ""
    ).strip()
    available_qty_ambiguous = bool(response.get("non_fatal_no_qty") is True) or (
        "매도가능수량" in message
    )
    if not has_code or not return_code:
        return "ambiguous", order_no, message or "return_code_missing"
    if return_code != "0":
        if re.fullmatch(r"-?[1-9][0-9]*", return_code) and not available_qty_ambiguous:
            return "definitive_reject", order_no, message or "broker_rejected"
        return "ambiguous", order_no, message or "broker_response_ambiguous"
    if re.fullmatch(r"[0-9]{7}", order_no) is None or int(order_no) == 0:
        return "ambiguous", order_no, "accepted_order_identity_missing"
    return "success", order_no, message


def _s15_sell_context_keys():
    from src.engine import sniper_execution_receipts as _receipt_handlers

    return _receipt_handlers._SELL_PENDING_SUBMIT_CONTEXT_KEYS


def _arm_s15_pending_sell_submit(state, code, qty, *, route, kind):
    """Persist exact S15 sell intent before the first broker-call instruction."""

    from src.engine import sniper_execution_receipts as _receipt_handlers

    with state["lock"]:
        if state.get("sell_submit_pending") is True:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                "existing_sell_submit_generation_reconciliation_only"
            )
            _persist_fast_state(code, state)
            return None
    normalized_route = str(route or "").strip().upper()
    if normalized_route not in {"KRX", "NXT", "SOR"}:
        normalized_route = "SOR"
    started_at = _now_ts()
    session_bucket = _receipt_handlers._sell_execution_session_bucket(
        datetime.fromtimestamp(started_at, tz=_receipt_handlers._KST)
    )
    if normalized_route in {"KRX", "NXT"}:
        effective_venue = normalized_route
    elif session_bucket == "krx_regular":
        effective_venue = "KRX"
    elif session_bucket.startswith("nxt_"):
        effective_venue = "NXT"
    else:
        effective_venue = "UNKNOWN"
    with state["lock"]:
        position_qty = max(
            int(qty or 0),
            int(state.get("cum_buy_qty", 0) or 0),
        )
        state.update(
            {
                "id": int(state.get("shadow_id") or 0),
                "code": str(code or "").strip()[:6],
                "strategy": "S15_FAST",
                "buy_qty": position_qty,
                "status": "EXIT_SUBMITTING",
                "s15_sell_submit_kind": str(kind or "sell"),
            }
        )
        fields = _receipt_handlers.build_pending_sell_submit_context_fields(
            state,
            code=code,
            requested_qty=int(qty),
            started_at=started_at,
            intended_route=normalized_route,
            intended_effective_venue=effective_venue,
            intended_session_bucket=session_bucket,
        )
        state.update(fields)
    db_boundary_committed = False
    if DB is not None and int(state.get("shadow_id") or 0) > 0:
        try:
            with DB.get_session() as session:
                updated_rows = (
                    session.query(RecommendationHistory)
                    .filter_by(
                        id=state.get("shadow_id"),
                        stock_code=str(code or "").strip()[:6],
                        buy_qty=position_qty,
                        status="HOLDING",
                    )
                    .update({"status": "SELL_ORDERED", "scale_in_locked": True})
                )
                if updated_rows != 1:
                    raise RuntimeError(f"s15_sell_db_owner_rowcount:{updated_rows}")
            db_boundary_committed = True
        except Exception as exc:
            state["s15_sell_submit_db_error"] = str(exc)[:240]
    if not db_boundary_committed:
        with state["lock"]:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = "sell_submit_db_boundary_failed"
        _persist_fast_state(code, state)
        return None
    if not _receipt_handlers.persist_pending_sell_submit_custody(state):
        rollback_committed = False
        try:
            with DB.get_session() as session:
                updated_rows = (
                    session.query(RecommendationHistory)
                    .filter_by(
                        id=state.get("shadow_id"),
                        stock_code=str(code or "").strip()[:6],
                        buy_qty=position_qty,
                        status="SELL_ORDERED",
                    )
                    .update({"status": "HOLDING"})
                )
                rollback_committed = updated_rows == 1
        except Exception:
            rollback_committed = False
        with state["lock"]:
            state["status"] = "HOLDING" if rollback_committed else "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                "sell_submit_common_custody_failed_no_call"
                if rollback_committed
                else "sell_submit_common_custody_failed_db_rollback_failed"
            )
            if rollback_committed:
                for field_name in _s15_sell_context_keys():
                    state.pop(field_name, None)
        _persist_fast_state(code, state)
        return None
    if not _persist_fast_state(code, state):
        rollback_committed = False
        try:
            with DB.get_session() as session:
                updated_rows = (
                    session.query(RecommendationHistory)
                    .filter_by(
                        id=state.get("shadow_id"),
                        stock_code=str(code or "").strip()[:6],
                        buy_qty=position_qty,
                        status="SELL_ORDERED",
                    )
                    .update({"status": "HOLDING"})
                )
                rollback_committed = updated_rows == 1
        except Exception:
            rollback_committed = False
        custody_cleared = False
        if rollback_committed:
            custody_cleared = _receipt_handlers.clear_pending_sell_submit_custody(
                state.get("shadow_id"),
                generation=str(fields.get("sell_submit_generation") or ""),
            )
            if not custody_cleared:
                try:
                    with DB.get_session() as session:
                        restored_rows = (
                            session.query(RecommendationHistory)
                            .filter_by(
                                id=state.get("shadow_id"),
                                stock_code=str(code or "").strip()[:6],
                                buy_qty=position_qty,
                                status="HOLDING",
                            )
                            .update({"status": "SELL_ORDERED", "scale_in_locked": True})
                        )
                        if restored_rows != 1:
                            raise RuntimeError(
                                "s15_fast_state_failure_interlock_restore_rowcount:"
                                f"{restored_rows}"
                            )
                except Exception as exc:
                    state["s15_sell_submit_db_error"] = str(exc)[:240]
        if not rollback_committed or not custody_cleared:
            state["status"] = "RECOVERY_REQUIRED"
            state["s15_recovery_reason"] = (
                "fast_state_persist_failed_db_rollback_failed"
                if not rollback_committed
                else "fast_state_persist_failed_custody_clear_failed"
            )
        else:
            state["status"] = "HOLDING"
            for field_name in _s15_sell_context_keys():
                state.pop(field_name, None)
        return None
    return {
        "generation": str(fields["sell_submit_generation"]),
        "context_sha256": str(fields["sell_submit_context_sha256"]),
    }


def _clear_s15_pending_sell_submit(state, *, generation):
    from src.engine import sniper_state_handlers as _state_handlers
    from src.engine import sniper_execution_receipts as _receipt_handlers

    state["id"] = int(state.get("shadow_id") or 0)
    state["code"] = str(state.get("code") or "").strip()[:6]
    state["status"] = "SELL_ORDERED"
    if not _receipt_handlers.persist_pending_sell_definitive_reject_outcome(
        state,
        generation=str(generation or ""),
    ):
        return False
    with state["lock"]:
        state.update(
            {
                "s15_sell_terminal_outcome_kind": ("definitive_reject_no_broker_order"),
                "s15_sell_terminal_outcome_generation": str(generation or ""),
                "s15_sell_terminal_outcome_context_sha256": str(
                    state.get("sell_submit_context_sha256") or ""
                ),
                "s15_sell_terminal_outcome_target_id": int(
                    state.get("sell_submit_target_id") or 0
                ),
                "s15_sell_terminal_outcome_code": str(
                    state.get("sell_submit_code") or ""
                ).strip(),
                "s15_sell_terminal_outcome_owner_position_qty": int(
                    state.get("sell_submit_owner_position_qty") or 0
                ),
                "s15_sell_terminal_outcome_requested_qty": int(
                    state.get("sell_submit_requested_qty") or 0
                ),
                "s15_sell_terminal_outcome_intended_route": str(
                    state.get("sell_submit_intended_route") or ""
                ).strip(),
                "s15_sell_terminal_outcome_intended_effective_venue": str(
                    state.get("sell_submit_intended_effective_venue") or ""
                ).strip(),
                "s15_sell_terminal_outcome_intended_session_bucket": str(
                    state.get("sell_submit_intended_session_bucket") or ""
                ).strip(),
            }
        )
    if not _persist_fast_state(str(state.get("code") or "")[:6], state):
        state["status"] = "RECOVERY_REQUIRED"
        state["s15_recovery_reason"] = "terminal_fast_marker_persist_failed"
        return False
    if not _state_handlers._finish_definitive_sell_reject_boundary(
        state,
        state["code"],
        target_id=state["id"],
        generation=str(generation or ""),
        db=DB,
    ):
        return False
    with state["lock"]:
        for field_name in _s15_sell_context_keys():
            state.pop(field_name, None)
        for field_name in _S15_SELL_TERMINAL_MARKER_KEYS:
            state.pop(field_name, None)
        state.pop("s15_sell_submit_kind", None)
        state["status"] = "HOLDING"
    return _persist_fast_state(str(state.get("code") or "")[:6], state)


def _log_s15_sell_order_sent(
    state,
    code,
    *,
    order_no,
    qty,
    corroboration_only=False,
    custody_committed=False,
):
    from src.engine import sniper_execution_receipts as _receipt_handlers

    route = str(state.get("sell_submit_intended_route") or "UNKNOWN").upper()
    effective_venue = str(
        state.get("sell_submit_intended_effective_venue") or "UNKNOWN"
    ).upper()
    session_bucket = str(
        state.get("sell_submit_intended_session_bucket") or "outside_krx_nxt_window"
    )
    _receipt_handlers._log_holding_pipeline(
        state.get("name"),
        code,
        state.get("shadow_id"),
        "sell_order_sent",
        candidate_stock=state,
        requested_qty=int(qty),
        submitted_qty=int(qty),
        qty=int(qty),
        broker_order_no=str(order_no),
        broker_order_no_list=str(order_no),
        broker_order_qty_list=f"{order_no}:{int(qty)}",
        lifecycle_submission_leg_contract="exact_broker_single_order_leg_v1",
        lifecycle_submission_time_source=(
            "pipeline_emit_after_broker_success_response"
        ),
        sell_submit_response_corroboration_only=bool(corroboration_only),
        exit_receipt_submission_custody_committed=bool(custody_committed),
        actual_order_submitted=True,
        broker_order_forbidden=False,
        runtime_effect=not bool(corroboration_only),
        broker_route=route,
        effective_venue=effective_venue,
        exit_effective_venue=effective_venue,
        market_session_bucket=session_bucket,
        exit_market_session_bucket=session_bucket,
        metric_role="execution_quality_real_only",
        decision_authority="broker_sell_submission_observation_only",
        window_policy="same_position_cycle_broker_submission",
        sample_floor="1_successful_broker_sell_submission",
        primary_decision_metric="broker_sell_order_sent_qty",
        source_quality_gate=(
            "successful_broker_response_and_execution_route_provenance"
        ),
        forbidden_uses=(
            "threshold_mutation|provider_route_change|quantity_cap_release|"
            "broker_guard_bypass|bot_restart"
        ),
    )


def _s15_receipt_first_response_handled(
    state,
    code,
    *,
    submit,
    response_state,
    response_order_no,
    qty,
):
    """Keep exact receipt truth monotonic when HTTP completes afterwards."""

    from src.engine import sniper_state_handlers as _state_handlers

    race_state = _state_handlers._sell_submit_response_race_state(
        state,
        generation=submit["generation"],
        context_sha256=submit["context_sha256"],
        requested_qty=int(qty),
        response_order_no=str(response_order_no or ""),
    )
    proof = state.get("_sell_submit_receipt_proof")
    proof = dict(proof) if isinstance(proof, dict) else {}
    if race_state in {"receipt_proved", "receipt_proved_custody_gap"}:
        receipt_order_no = str(proof.get("order_no") or "").strip()
        if response_state == "success" and receipt_order_no:
            _log_s15_sell_order_sent(
                state,
                code,
                order_no=receipt_order_no,
                qty=qty,
                corroboration_only=True,
                custody_committed=race_state == "receipt_proved",
            )
        if race_state == "receipt_proved_custody_gap":
            state["sell_cancel_reconciliation_required"] = True
            state["s15_recovery_reason"] = "receipt_submission_custody_retry_required"
        _persist_fast_state(code, state)
        return True
    if race_state in {
        "receipt_proof_response_order_conflict",
        "stale_or_intervened",
    }:
        state["sell_cancel_reconciliation_required"] = True
        state["s15_recovery_reason"] = (
            "sell_submit_response_order_conflict"
            if race_state == "receipt_proof_response_order_conflict"
            else "sell_submit_response_stale_or_intervened"
        )
        _persist_fast_state(code, state)
        return True
    return False


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
            metadata_extra={"position_tag": "S15_FAST"},
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

        initial_sell_route = (
            str(kiwoom_orders.resolve_order_dmst_stex_tp() or "SOR").strip().upper()
        )
        initial_submit = _arm_s15_pending_sell_submit(
            state,
            code,
            real_buy_qty,
            route=initial_sell_route,
            kind="initial_profit_limit",
        )
        if initial_submit is None:
            _start_s15_recovery_thread(code, state)
            return
        try:
            sell_res = _send_s15_limit_sell(code, real_buy_qty, target_price)
        except Exception as exc:
            sell_res = {"return_code": "exception", "return_msg": str(exc)}
        initial_response_state, initial_order_no, initial_error = (
            _classify_s15_sell_response(sell_res)
        )
        if _s15_receipt_first_response_handled(
            state,
            code,
            submit=initial_submit,
            response_state=initial_response_state,
            response_order_no=initial_order_no,
            qty=real_buy_qty,
        ):
            _start_s15_recovery_thread(code, state)
            return
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

        if initial_response_state == "ambiguous":
            with state["lock"]:
                state["status"] = "RECOVERY_REQUIRED"
                state["s15_recovery_reason"] = "initial_sell_response_ambiguous"
                state["s15_sell_submit_response_error"] = initial_error[:240]
            _persist_fast_state(code, state)
            _start_s15_recovery_thread(code, state)
            return

        if initial_response_state in {"definitive_reject", "local_no_call"}:
            if not _clear_s15_pending_sell_submit(
                state,
                generation=initial_submit["generation"],
            ):
                with state["lock"]:
                    state["status"] = "RECOVERY_REQUIRED"
                    state["s15_recovery_reason"] = (
                        "initial_sell_reject_custody_clear_failed"
                    )
                _persist_fast_state(code, state)
                _start_s15_recovery_thread(code, state)
                return
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
                emergency_route = (
                    str(kiwoom_orders.resolve_order_dmst_stex_tp() or "SOR")
                    .strip()
                    .upper()
                )
                emergency_submit = _arm_s15_pending_sell_submit(
                    state,
                    code,
                    rem_qty,
                    route=emergency_route,
                    kind="emergency_ioc",
                )
                if emergency_submit is None:
                    _start_s15_recovery_thread(code, state)
                    return
                try:
                    emergency_res = _send_exit_best_ioc(code, rem_qty, KIWOOM_TOKEN)
                except Exception as exc:
                    emergency_res = {
                        "return_code": "exception",
                        "return_msg": str(exc),
                    }
                emergency_state, emergency_order_no, emergency_error = (
                    _classify_s15_sell_response(emergency_res)
                )
                if _s15_receipt_first_response_handled(
                    state,
                    code,
                    submit=emergency_submit,
                    response_state=emergency_state,
                    response_order_no=emergency_order_no,
                    qty=rem_qty,
                ):
                    _start_s15_recovery_thread(code, state)
                    return
                if emergency_state == "success":
                    with state["lock"]:
                        state["sell_ord_no"] = emergency_order_no
                        state["status"] = "EXIT_RETRY"
                        state["updated_at"] = _now_ts()
                    if not _persist_fast_state(code, state):
                        return
                    _log_s15_sell_order_sent(
                        state,
                        code,
                        order_no=emergency_order_no,
                        qty=rem_qty,
                    )
                    update_s15_shadow_record(
                        state.get("shadow_id"),
                        status="SELL_ORDERED",
                        scale_in_locked=True,
                    )
                elif emergency_state in {"definitive_reject", "local_no_call"}:
                    if not _clear_s15_pending_sell_submit(
                        state,
                        generation=emergency_submit["generation"],
                    ):
                        with state["lock"]:
                            state["status"] = "RECOVERY_REQUIRED"
                            state["s15_recovery_reason"] = (
                                "emergency_sell_reject_boundary_incomplete"
                            )
                        _persist_fast_state(code, state)
                        _start_s15_recovery_thread(code, state)
                        return
                    with state["lock"]:
                        state["status"] = "HOLDING_NEEDS_EXIT"
                        state["s15_recovery_reason"] = "emergency_sell_rejected"
                        state["s15_sell_submit_response_error"] = emergency_error[:240]
                    _persist_fast_state(code, state)
                else:
                    with state["lock"]:
                        state["status"] = "RECOVERY_REQUIRED"
                        state["s15_recovery_reason"] = (
                            "emergency_sell_response_ambiguous"
                        )
                        state["s15_sell_submit_response_error"] = emergency_error[:240]
                    _persist_fast_state(code, state)
            else:
                print(
                    f"ℹ️ [S15 Fail-safe] {name} 재조회 결과 잔량 없음. 자연 종료 가능."
                )

            _start_s15_recovery_thread(code, state)
            return

        sell_order_no = initial_order_no
        with state["lock"]:
            state["sell_ord_no"] = sell_order_no
            state["status"] = "EXIT_SENT"
            state["updated_at"] = _now_ts()
        if not _persist_fast_state(code, state):
            return
        _log_s15_sell_order_sent(
            state,
            code,
            order_no=sell_order_no,
            qty=real_buy_qty,
        )
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
                    cancel_ready = _submit_s15_stop_cancel(
                        state,
                        code,
                        sell_ord_no,
                    )
                    if not cancel_ready:
                        with state["lock"]:
                            state["status"] = "RECOVERY_REQUIRED"
                            state["s15_recovery_reason"] = (
                                "stop_exit_cancel_intent_durability_failed"
                                if state.get("s15_stop_cancel_retry_required") is True
                                else "stop_exit_cancel_context_invalid"
                            )
                    else:
                        with state["lock"]:
                            state["status"] = "SELL_ORDERED"
                            state.pop("s15_stop_cancel_retry_required", None)
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
