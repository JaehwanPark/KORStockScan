"""Order execution receipt handlers for the sniper engine."""

import threading
import time
from datetime import datetime
from typing import Any

from src.database.models import RecommendationHistory
from src.engine.sniper_entry_state import (
    ENTRY_LOCK,
    get_terminal_entry_order,
    move_orders_to_terminal,
)
from src.engine.sniper_scale_in_utils import record_add_history_event
from src.engine.sniper_position_tags import (
    default_position_tag_for_strategy,
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
)
from src.engine.trade_profit import calculate_net_profit_rate
from src.utils.constants import TRADING_RULES
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine.sniper_time import TIME_15_30
from src.engine.sniper_post_sell_feedback import record_post_sell_candidate


KIWOOM_TOKEN = None
DB = None
event_bus = None
ACTIVE_TARGETS = None
highest_prices = None
_get_fast_state = None
_weighted_avg = None
_now_ts = None

# Receipt module의 임시/DB 작업은 독립 락으로 직렬화하고,
# ACTIVE_TARGETS 같은 shared runtime truth는 주입된 _STATE_LOCK(실운영에서는 ENTRY_LOCK)으로만 만집니다.
# 테스트/단독 사용 시에는 _STATE_LOCK이 없을 수 있으므로 RECEIPT_LOCK을 fallback으로 둡니다.
RECEIPT_LOCK = threading.RLock()
_STATE_LOCK = None


def _active_state_lock():
    """ACTIVE_TARGETS/ordno/pending state mutation에 사용할 소유 락을 반환한다."""
    return _STATE_LOCK or RECEIPT_LOCK


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return int(default)
        return int(float(value))
    except Exception:
        return int(default)

_BUY_RECEIPT_SNAPSHOT_KEYS = (
    "buy_execution_notified",
    "buy_price",
    "buy_qty",
    "code",
    "actual_order_submitted",
    "msg_audience",
    "name",
    "pending_buy_msg",
    "scalp_live_simulator",
    "simulation_book",
    "simulation_owner",
    "swing_live_order_dry_run",
)
_SELL_RECEIPT_SNAPSHOT_KEYS = (
    "actual_order_submitted",
    "buy_qty",
    "code",
    "last_exit_current_ai_score",
    "last_exit_decision_source",
    "last_exit_held_sec",
    "last_exit_peak_profit",
    "last_exit_rule",
    "last_exit_same_symbol_soft_stop_cooldown_would_block",
    "last_exit_soft_stop_threshold_pct",
    "msg_audience",
    "name",
    "no_scale_in_counterfactual_profit_pct",
    "pending_sell_msg",
    "post_add_avg_price",
    "post_add_qty",
    "pre_add_avg_price",
    "pre_add_qty",
    "scalp_live_simulator",
    "scale_in_incremental_realized_delta_pct",
    "simulation_book",
    "simulation_owner",
    "swing_live_order_dry_run",
)
_ADD_RECEIPT_SNAPSHOT_KEYS = (
    "actual_order_submitted",
    "add_count",
    "avg_down_count",
    "buy_price",
    "buy_qty",
    "code",
    "hard_stop_price",
    "msg_audience",
    "name",
    "post_add_avg_price",
    "post_add_qty",
    "pyramid_count",
    "pre_add_avg_price",
    "pre_add_qty",
    "scale_in_locked",
    "scalp_live_simulator",
    "simulation_book",
    "simulation_owner",
    "strategy",
    "swing_live_order_dry_run",
    "trailing_stop_price",
)
_PENDING_ADD_META_KEYS = (
    "pending_add_order",
    "pending_add_type",
    "pending_add_reason",
    "pending_add_qty",
    "pending_add_ord_no",
    "pending_add_requested_at",
    "pending_add_counted",
    "pending_add_filled_qty",
    "add_order_time",
    "add_odno",
)
_SELL_REVIVE_RESET_KEYS = (
    "odno",
    "order_time",
    "order_price",
    "buy_time",
    "target_buy_price",
    "pending_buy_msg",
    "pending_sell_msg",
    "sell_odno",
    "sell_order_time",
    "sell_target_price",
    "pending_entry_orders",
    "entry_mode",
    "entry_requested_qty",
    "entry_filled_qty",
    "entry_fill_amount",
    "entry_bundle_id",
    "requested_buy_qty",
    "_entry_receipt_filled_by_order_no",
    "_entry_receipt_requested_by_order_no",
    "buy_execution_notified",
    "trailing_stop_price",
    "hard_stop_price",
    "protect_profit_pct",
)
_SELL_COMPLETE_RESET_KEYS = (
    "pending_entry_orders",
    "entry_mode",
    "entry_requested_qty",
    "entry_filled_qty",
    "entry_fill_amount",
    "entry_bundle_id",
    "requested_buy_qty",
    "_entry_receipt_filled_by_order_no",
    "_entry_receipt_requested_by_order_no",
    "buy_execution_notified",
    "trailing_stop_price",
    "hard_stop_price",
    "protect_profit_pct",
)
_ENTRY_RECEIPT_FILLED_BY_ORDER_KEY = "_entry_receipt_filled_by_order_no"
_ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY = "_entry_receipt_requested_by_order_no"
_ENTRY_RECEIPT_NO_ORDER_KEY = "__entry_without_order_no__"


def bind_execution_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    event_bus_instance=None,
    active_targets=None,
    highest_prices_map=None,
    get_fast_state=None,
    weighted_avg=None,
    now_ts=None,
    state_lock=None,
    state_machine=None,
    **_unused_kwargs,
):
    """Receipt 모듈 의존성 주입.

    lock ownership:
    - `state_lock`: ACTIVE_TARGETS 및 target_stock runtime truth를 보호하는 상위 락
    - `RECEIPT_LOCK`: state_lock 미주입 테스트/단독 경로의 fallback 직렬화 락
    """
    global KIWOOM_TOKEN, DB, event_bus, ACTIVE_TARGETS, highest_prices
    global _get_fast_state, _weighted_avg, _now_ts, _STATE_LOCK

    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if event_bus_instance is not None:
        event_bus = event_bus_instance
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if highest_prices_map is not None:
        highest_prices = highest_prices_map
    if get_fast_state is not None:
        _get_fast_state = get_fast_state
    if weighted_avg is not None:
        _weighted_avg = weighted_avg
    if now_ts is not None:
        _now_ts = now_ts
    if state_lock is not None:
        _STATE_LOCK = state_lock


def _log_holding_pipeline(name, code, target_id, stage, **fields):
    emit_pipeline_event(
        "HOLDING_PIPELINE",
        name,
        code,
        stage,
        record_id=target_id,
        fields=fields,
    )


def _receipt_snapshot(target_stock: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: target_stock.get(key) for key in keys}


def _receipt_audience(snapshot: dict[str, Any] | None) -> str:
    snapshot = snapshot or {}
    simulated = (
        bool(snapshot.get("swing_live_order_dry_run"))
        or bool(snapshot.get("scalp_live_simulator"))
        or bool(snapshot.get("simulation_book"))
        or bool(snapshot.get("simulation_owner"))
        or snapshot.get("actual_order_submitted") is False
    )
    if simulated:
        return "ADMIN_ONLY"
    return str(snapshot.get("msg_audience") or "ADMIN_ONLY")


def _entry_receipt_order_key(order_no: str) -> str:
    normalized = str(order_no or "").strip()
    return normalized or _ENTRY_RECEIPT_NO_ORDER_KEY


def _entry_receipt_int_map(target_stock: dict[str, Any], key: str) -> dict[str, int]:
    raw_map = target_stock.get(key)
    if not isinstance(raw_map, dict):
        raw_map = {}
        target_stock[key] = raw_map
    normalized: dict[str, int] = {}
    for raw_key, raw_value in raw_map.items():
        normalized[str(raw_key)] = int(raw_value or 0)
    if normalized is not raw_map:
        target_stock[key] = normalized
    return normalized


def _resolve_entry_effective_fill_qty(
    *,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_qty: int,
) -> tuple[int, int, int]:
    """Return the entry fill delta that may be applied to runtime truth.

    Kiwoom execution notices can repeat a final fill or report cumulative
    quantities for the same order number. Entry orders with a known requested
    quantity must therefore be capped by remaining leg quantity before mutating
    buy_qty/avg price. The per-order ledger intentionally survives terminal
    entry-order grace so delayed duplicate receipts do not inflate position size.
    """

    order_key = _entry_receipt_order_key(order_no)
    requested_by_order = _entry_receipt_int_map(target_stock, _ENTRY_RECEIPT_REQUESTED_BY_ORDER_KEY)
    filled_by_order = _entry_receipt_int_map(target_stock, _ENTRY_RECEIPT_FILLED_BY_ORDER_KEY)

    pending_order = None
    for order in target_stock.get("pending_entry_orders") or []:
        if str(order.get("ord_no", "") or "").strip() == str(order_no or "").strip():
            pending_order = order
            break

    requested_qty = int(requested_by_order.get(order_key, 0) or 0)
    if pending_order is not None:
        requested_qty = max(requested_qty, int(pending_order.get("qty", 0) or 0))
    if requested_qty <= 0:
        requested_qty = int(
            target_stock.get("entry_requested_qty", target_stock.get("requested_buy_qty", 0)) or 0
        )

    already_filled = int(filled_by_order.get(order_key, 0) or 0)
    if pending_order is not None:
        already_filled = max(already_filled, int(pending_order.get("filled_qty", 0) or 0))

    if requested_qty > 0:
        requested_by_order[order_key] = requested_qty
        remaining_qty = max(0, requested_qty - already_filled)
        if remaining_qty <= 0:
            log_info(
                f"[ENTRY_FILL_IGNORED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={exec_qty} "
                f"already_filled={already_filled}/{requested_qty} reason=duplicate_or_cumulative_receipt"
            )
            if pending_order is not None:
                pending_order["filled_qty"] = already_filled
                pending_order["status"] = "FILLED"
            return 0, requested_qty, already_filled

        effective_qty = min(int(exec_qty or 0), remaining_qty)
        if effective_qty < int(exec_qty or 0):
            log_info(
                f"[ENTRY_FILL_CAPPED] {target_stock.get('name')}({code}) "
                f"ord_no={order_no or '-'} raw_fill_qty={exec_qty} "
                f"effective_fill_qty={effective_qty} already_filled={already_filled}/{requested_qty} "
                "reason=cumulative_or_over_requested_receipt"
            )
    else:
        effective_qty = int(exec_qty or 0)

    new_filled = already_filled + effective_qty
    filled_by_order[order_key] = new_filled
    if pending_order is not None:
        pending_order["filled_qty"] = new_filled
        pending_order["status"] = "FILLED" if requested_qty > 0 and new_filled >= requested_qty else "PARTIAL"
        pending_order["last_effective_fill_qty"] = effective_qty
    return effective_qty, requested_qty, new_filled


def _clear_runtime_keys(target_stock: dict[str, Any], keys: tuple[str, ...]) -> None:
    for key in keys:
        target_stock.pop(key, None)


def _publish_sell_execution_message(*, name: str, pending_msg: str, audience: str, exec_price: int, profit_rate: float) -> None:
    if pending_msg:
        final_msg = (
            pending_msg.replace("매도 전송", "매도 체결 완료")
            .replace("[익절 주문]", "[익절 완료]")
            .replace("[손절 주문]", "[손절 완료]")
        )
        final_msg += f"\n✅ **실제 체결가:** `{exec_price:,}원` (확정 수익률: `{profit_rate:+.2f}%`)"
        event_bus.publish(
            'TELEGRAM_BROADCAST',
            {'message': final_msg, 'audience': audience, 'parse_mode': 'HTML'},
        )
        return

    sign = "🎊 [익절 완료]" if profit_rate > 0 else "📉 [손절 완료]"
    event_bus.publish(
        'TELEGRAM_BROADCAST',
        {
            'message': f"{sign} **[{name}]** 매도 체결!\n체결가: `{exec_price:,}원`\n수익률: `{profit_rate:+.2f}%`",
            'audience': audience,
            'parse_mode': 'HTML',
        },
    )


def _resolve_sell_execution_context(target_id: int, target_stock: dict[str, Any], exec_price: int, now_t):
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return None
            safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
            if safe_buy_price > 0:
                profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
            else:
                profit_rate = 0.0
                log_error(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")
            strategy = normalize_strategy(record.strategy or target_stock.get('strategy') or 'KOSPI_ML')
            is_scalp_revive = (strategy == 'SCALPING') and (now_t < TIME_15_30)
            return record, safe_buy_price, profit_rate, strategy, is_scalp_revive
    except Exception as e:
        log_error(f"🚨 [DB 조회 에러] ID {target_id} SELL 처리 중 에러: {e}")
        return None


def _finalize_standard_sell_execution(
    *,
    target_id: int,
    exec_price: int,
    now: datetime,
    target_stock: dict[str, Any],
    strategy: str,
    is_scalp_revive: bool,
    code: str,
) -> None:
    highest_prices.pop(code, None)
    target_stock['status'] = 'COMPLETED'
    target_stock['sell_time'] = now.strftime('%H:%M:%S')
    move_orders_to_terminal(target_stock, reason='sell_completed_cleanup')
    sell_receipt_snapshot = _receipt_snapshot(target_stock, _SELL_RECEIPT_SNAPSHOT_KEYS)
    _clear_runtime_keys(target_stock, _SELL_COMPLETE_RESET_KEYS)
    target_stock.pop('pending_sell_msg', None)
    threading.Thread(
        target=_update_db_for_sell,
        args=(target_id, exec_price, now, sell_receipt_snapshot, strategy, is_scalp_revive),
        daemon=True,
    ).start()


def _handle_scalp_revive_sell_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    exec_price: int,
    now: datetime,
    profit_rate: float,
    safe_buy_price: float,
    strategy: str,
) -> bool:
    revived_position_tag = normalize_position_tag(
        'SCALPING',
        target_stock.get('position_tag') or default_position_tag_for_strategy('SCALPING'),
    )
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return False
            record.status = 'COMPLETED'
            record.sell_price = exec_price
            record.sell_time = now
            record.profit_rate = profit_rate
            log_info(f"🎉 [매매 완료: ID {target_id}] {code} 실매도가: {exec_price:,}원 / 수익률: {profit_rate}%")

            new_record = RecommendationHistory(
                rec_date=now.date(),
                stock_code=code,
                stock_name=record.stock_name,
                buy_price=0,
                status='WATCHING',
                strategy='SCALPING',
                trade_type='SCALP',
                position_tag=revived_position_tag,
                prob=record.prob
            )
            session.add(new_record)
            session.flush()
            new_watch_id = new_record.id

            _publish_sell_execution_message(
                name=target_stock.get('name') or '-',
                pending_msg=target_stock.get('pending_sell_msg') or '',
                audience=_receipt_audience(target_stock),
                exec_price=exec_price,
                profit_rate=profit_rate,
            )
            _log_holding_pipeline(
                target_stock.get('name'),
                code,
                target_id,
                'sell_completed',
                sell_price=int(exec_price or 0),
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=target_stock.get('last_exit_rule') or '-',
                exit_decision_source=target_stock.get('last_exit_decision_source') or 'MANUAL',
                revive=True,
                new_watch_id=int(new_watch_id or 0),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=target_stock,
                    code=code,
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=exec_price,
                    profit_rate=profit_rate,
                    buy_qty=int(float(getattr(record, 'buy_qty', 0) or target_stock.get('buy_qty', 0) or 0)),
                    exit_rule=target_stock.get('last_exit_rule') or '-',
                    strategy=strategy,
                    revive=True,
                    peak_profit=target_stock.get('last_exit_peak_profit'),
                    held_sec=target_stock.get('last_exit_held_sec'),
                    current_ai_score=target_stock.get('last_exit_current_ai_score'),
                    soft_stop_threshold_pct=target_stock.get('last_exit_soft_stop_threshold_pct'),
                    same_symbol_soft_stop_cooldown_would_block=target_stock.get(
                        'last_exit_same_symbol_soft_stop_cooldown_would_block'
                    ),
                )
            except Exception as exc:
                log_error(f"[POST_SELL] candidate record failed (id={target_id}): {exc}")
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")
        return False

    _apply_scalp_revive_memory_state(
        target_stock=target_stock,
        code=code,
        new_watch_id=new_watch_id,
        revived_position_tag=revived_position_tag,
    )
    return True


def _apply_scalp_revive_memory_state(
    *,
    target_stock: dict[str, Any],
    code: str,
    new_watch_id: int,
    revived_position_tag: str,
) -> None:
    highest_prices.pop(code, None)
    target_stock['id'] = new_watch_id
    target_stock['status'] = 'WATCHING'
    target_stock['buy_price'] = 0
    target_stock['buy_qty'] = 0
    target_stock['added_time'] = time.time()
    target_stock['position_tag'] = revived_position_tag
    move_orders_to_terminal(target_stock, reason='sell_revive_cleanup')
    _clear_runtime_keys(target_stock, _SELL_REVIVE_RESET_KEYS)


def _clear_split_entry_shadow_state(target_stock: dict[str, Any]) -> None:
    for key in [
        "_split_entry_rebase_shadow_count",
        "_split_entry_rebase_shadow_last_second",
        "_split_entry_rebase_shadow_same_second_count",
        "_split_entry_first_partial_qty",
        "_split_entry_last_immediate_recheck_rebase_count",
    ]:
        target_stock.pop(key, None)


def _emit_split_entry_followup_shadows(
    *,
    target_stock: dict[str, Any],
    code: str,
    target_id: int,
    now: datetime,
    entry_mode: str,
    fill_quality: str,
    requested_entry_qty: int,
    cum_filled_qty: int,
    remaining_qty: int,
    new_qty: int,
) -> None:
    if not bool(getattr(TRADING_RULES, "SPLIT_ENTRY_REBASE_INTEGRITY_SHADOW_ENABLED", False)):
        return

    rebase_count = int(target_stock.get("_split_entry_rebase_shadow_count", 0) or 0) + 1
    target_stock["_split_entry_rebase_shadow_count"] = rebase_count

    emitted_second = now.strftime("%Y-%m-%dT%H:%M:%S")
    last_second = str(target_stock.get("_split_entry_rebase_shadow_last_second") or "")
    if emitted_second == last_second:
        same_second_count = int(target_stock.get("_split_entry_rebase_shadow_same_second_count", 0) or 0) + 1
    else:
        same_second_count = 1
    target_stock["_split_entry_rebase_shadow_last_second"] = emitted_second
    target_stock["_split_entry_rebase_shadow_same_second_count"] = same_second_count

    fill_quality_upper = str(fill_quality or "").upper()
    first_partial_qty = int(target_stock.get("_split_entry_first_partial_qty", 0) or 0)
    if fill_quality_upper == "PARTIAL_FILL" and first_partial_qty <= 0:
        first_partial_qty = max(0, int(cum_filled_qty or 0))
        target_stock["_split_entry_first_partial_qty"] = first_partial_qty

    split_entry_candidate = rebase_count >= 2 or fill_quality_upper == "PARTIAL_FILL" or first_partial_qty > 0
    if not split_entry_candidate:
        return

    integrity_flags: list[str] = []
    if requested_entry_qty > 0 and cum_filled_qty > requested_entry_qty:
        integrity_flags.append("cum_gt_requested")
    if requested_entry_qty == 0 and fill_quality_upper == "UNKNOWN":
        integrity_flags.append("requested0_unknown")
    if same_second_count >= 2:
        integrity_flags.append("same_ts_multi_rebase")

    integrity_flag_text = ",".join(integrity_flags) if integrity_flags else "-"
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "split_entry_rebase_integrity_shadow",
        requested_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        fill_quality=fill_quality_upper or "-",
        entry_mode=entry_mode or "-",
        buy_qty_after_rebase=int(new_qty or 0),
        rebase_count=int(rebase_count),
        same_ts_multi_rebase_count=int(same_second_count),
        integrity_flags=integrity_flag_text,
    )

    if not bool(getattr(TRADING_RULES, "SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_ENABLED", False)):
        return

    expanded_after_partial = first_partial_qty > 0 and int(new_qty or 0) > first_partial_qty
    if not (expanded_after_partial or rebase_count >= 2):
        return

    last_logged_count = int(target_stock.get("_split_entry_last_immediate_recheck_rebase_count", 0) or 0)
    if rebase_count <= last_logged_count:
        return
    target_stock["_split_entry_last_immediate_recheck_rebase_count"] = rebase_count

    trigger_reason = "partial_then_expand" if expanded_after_partial else "multi_rebase"
    shadow_window_sec = int(getattr(TRADING_RULES, "SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_WINDOW_SEC", 90) or 90)
    _log_holding_pipeline(
        target_stock.get("name"),
        code,
        target_id,
        "split_entry_immediate_recheck_shadow",
        trigger_reason=trigger_reason,
        shadow_window_sec=int(shadow_window_sec),
        requested_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        buy_qty_after_rebase=int(new_qty or 0),
        first_partial_qty=int(first_partial_qty or 0),
        rebase_count=int(rebase_count),
        fill_quality=fill_quality_upper or "-",
        entry_mode=entry_mode or "-",
        integrity_flags=integrity_flag_text,
    )


def _find_buy_bundle_match(code: str, normalized_order_no: str):
    return next(
        (
            stock for stock in ACTIVE_TARGETS
            if str(stock.get('code', '')).strip()[:6] == code
            and any(
                str(order.get('ord_no', '') or '').strip() == normalized_order_no
                for order in (stock.get('pending_entry_orders') or [])
            )
        ),
        None,
    )


def _find_terminal_entry_target(normalized_order_no: str):
    terminal_match = get_terminal_entry_order(normalized_order_no)
    if not terminal_match:
        return None
    stock_code = str(terminal_match.get('stock_code', '') or '').strip()[:6]
    return next(
        (
            stock for stock in ACTIVE_TARGETS
            if str(stock.get('code', '')).strip()[:6] == stock_code
        ),
        None,
    )


def _find_add_order_match(code: str, normalized_order_no: str):
    return next(
        (
            stock for stock in ACTIVE_TARGETS
            if str(stock.get('code', '')).strip()[:6] == code
            and bool(stock.get('pending_add_order'))
            and str(stock.get('pending_add_ord_no', '')).strip() == normalized_order_no
        ),
        None
    )


def _find_execution_target(code, exec_type, order_no):
    """실제체결 대상 runtime truth 매칭.

    BUY 우선순위:
    1) split-entry bundle ord_no exact
    2) terminal entry order exact
    3) BUY_ORDERED status + odno exact
    4) HOLDING pending_add_order + pending_add_ord_no exact
    5) 단일 HOLDING pending_add candidate (order_no 없음)
    6) 단일 BUY_ORDERED candidate

    SELL 우선순위:
    1) SELL_ORDERED status + sell_odno exact
    2) 단일 SELL_ORDERED candidate
    """
    normalized_order_no = str(order_no or '').strip()

    if exec_type == 'BUY':
        if normalized_order_no:
            bundle_match = _find_buy_bundle_match(code, normalized_order_no)
            if bundle_match:
                return bundle_match

            target = _find_terminal_entry_target(normalized_order_no)
            if target:
                return target

        status_key = 'BUY_ORDERED'
        order_key = 'odno'
    else:
        status_key = 'SELL_ORDERED'
        order_key = 'sell_odno'

    status_candidates = [
        stock for stock in ACTIVE_TARGETS
        if str(stock.get('code', '')).strip()[:6] == code and stock.get('status') == status_key
    ]

    if normalized_order_no:
        exact_match = next(
            (
                stock for stock in status_candidates
                if str(stock.get(order_key, '')).strip() == normalized_order_no
            ),
            None
        )
        if exact_match:
            return exact_match

        if exec_type == 'BUY':
            add_match = _find_add_order_match(code, normalized_order_no)
            if add_match:
                return add_match

    if exec_type == 'BUY':
        pending_add_candidates = [
            stock for stock in ACTIVE_TARGETS
            if str(stock.get('code', '')).strip()[:6] == code
            and bool(stock.get('pending_add_order'))
            and stock.get('status') == 'HOLDING'
        ]
        if len(pending_add_candidates) == 1:
            return pending_add_candidates[0]

    if len(status_candidates) == 1:
        return status_candidates[0]

    return None


def _execution_ignore_context(code: str, exec_type: str, order_no: str) -> str:
    normalized_order_no = str(order_no or '').strip()
    matching_code_targets = [
        stock for stock in ACTIVE_TARGETS
        if str((stock or {}).get('code', '')).strip()[:6] == code
    ]
    target_summaries = []
    for stock in matching_code_targets[:5]:
        pending_orders = stock.get('pending_entry_orders') or []
        pending_ord_nos = [
            str(order.get('ord_no', '') or '').strip() or '-'
            for order in pending_orders[:3]
        ]
        target_summaries.append(
            "{status}:odno={odno}:sell_odno={sell_odno}:pending={pending}".format(
                status=str(stock.get('status', '') or '-'),
                odno=str(stock.get('odno', '') or '-'),
                sell_odno=str(stock.get('sell_odno', '') or '-'),
                pending="|".join(pending_ord_nos) if pending_ord_nos else '-',
            )
        )
    terminal_present = False
    if exec_type == 'BUY' and normalized_order_no:
        terminal_present = get_terminal_entry_order(normalized_order_no) is not None
    return (
        f"active_code_targets={len(matching_code_targets)} "
        f"target_context={';'.join(target_summaries) if target_summaries else '-'} "
        f"terminal_entry_bridge={terminal_present}"
    )


def _find_order_notice_target(code, exec_type, order_no):
    target = _find_execution_target(code, exec_type, order_no)
    if target:
        return target

    status_key = 'BUY_ORDERED' if exec_type == 'BUY' else 'SELL_ORDERED'
    status_candidates = [
        stock for stock in ACTIVE_TARGETS
        if str(stock.get('code', '')).strip()[:6] == code and stock.get('status') == status_key
    ]
    if len(status_candidates) == 1:
        return status_candidates[0]
    return None


def _apply_order_notice_to_target(target_stock, *, code, exec_type, order_no, status):
    changed = False

    if exec_type == 'BUY':
        pending_orders = target_stock.get('pending_entry_orders') or []
        exact_match = None
        blank_match = None

        for order in pending_orders:
            existing_ord_no = str(order.get('ord_no', '') or '').strip()
            if existing_ord_no == order_no:
                exact_match = order
                break
            if not existing_ord_no and blank_match is None:
                blank_match = order

        target_order = exact_match or blank_match
        if target_order:
            if not str(target_order.get('ord_no', '') or '').strip():
                target_order['ord_no'] = order_no
                changed = True
            target_order['notice_status'] = status
            target_order['notice_at'] = time.time()
            changed = True

        if order_no and not str(target_stock.get('odno', '') or '').strip():
            target_stock['odno'] = order_no
            changed = True

    elif exec_type == 'SELL':
        if order_no and not str(target_stock.get('sell_odno', '') or '').strip():
            target_stock['sell_odno'] = order_no
            changed = True

    if changed:
        log_info(
            f"[ORDER_NOTICE_BOUND] {target_stock.get('name')}({code}) "
            f"type={exec_type} status={status} order_no={order_no}"
        )


def _avg_from_totals(total_amount: float, total_qty: int) -> float:
    if total_qty <= 0:
        return 0.0
    return round(float(total_amount) / float(total_qty), 4)


def weighted_avg_price(old_price, old_qty, exec_price, exec_qty):
    if old_qty <= 0:
        return exec_price
    return _avg_from_totals((old_price * old_qty) + (exec_price * exec_qty), old_qty + exec_qty)


def handle_order_notice(notice_data):
    code = str(notice_data.get('code', '') or '').strip()[:6]
    exec_type = str(notice_data.get('type', '') or '').upper()
    order_no = str(notice_data.get('order_no', '') or '').strip()
    status = str(notice_data.get('status', '') or '').strip()

    if not code or exec_type not in {'BUY', 'SELL'} or not order_no:
        return

    with _active_state_lock():
        target_stock = _find_order_notice_target(code, exec_type, order_no)
        if not target_stock:
            return
        _apply_order_notice_to_target(
            target_stock,
            code=code,
            exec_type=exec_type,
            order_no=order_no,
            status=status,
        )


def _clear_pending_add_meta(target_stock):
    _clear_runtime_keys(target_stock, _PENDING_ADD_META_KEYS)


def _apply_scale_in_protection(target_stock, add_type):
    """추가매수 체결 후 보호선 보정(1차 단순 버전)."""
    try:
        raw_strategy = (target_stock.get('strategy') or 'KOSPI_ML').upper()
        strategy = 'SCALPING' if raw_strategy in ['SCALPING', 'SCALP'] else raw_strategy
        avg_price = float(target_stock.get('buy_price') or 0)
        if avg_price <= 0:
            return False

        if add_type == 'PYRAMID':
            if strategy == 'SCALPING':
                protect_price = avg_price * 1.003
            else:
                protect_price = avg_price * 1.01

            existing = float(target_stock.get('trailing_stop_price') or 0)
            target_stock['trailing_stop_price'] = max(existing, protect_price)
        elif add_type == 'AVG_DOWN':
            target_stock.pop('soft_stop_micro_grace_started_at', None)
            target_stock.pop('soft_stop_micro_grace_extension_used', None)
            target_stock['soft_stop_reset_after_avg_down'] = True
        return True
    except Exception as e:
        log_error(f"⚠️ [ADD_PROTECT] 보호선 보정 실패: {e}")
        return False


def _is_ok_response(res):
    if not isinstance(res, dict):
        return bool(res)
    return str(res.get('return_code', res.get('rt_cd', ''))) == '0'


def _refresh_scalp_preset_exit_order(target_stock, code, total_qty):
    """
    스캘핑 보유 수량이 바뀌면 preset TP 주문을 새 수량 기준으로 다시 맞춥니다.
    """
    from src.engine import kiwoom_orders

    preset_ord_no = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
    preset_tp_price = int(target_stock.get('preset_tp_price') or 0)

    if preset_ord_no:
        cancel_res = kiwoom_orders.send_cancel_order(code=code, orig_ord_no=preset_ord_no, token=KIWOOM_TOKEN, qty=0)
        if not _is_ok_response(cancel_res):
            log_error(
                f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) 기존 preset TP 취소 실패. "
                "added shares may remain partially unprotected."
            )
            return False

    if preset_tp_price > 0:
        tick = int(kiwoom_utils.get_tick_size(preset_tp_price))
        if tick > 0:
            normalized_price = int((preset_tp_price // tick) * tick)
            if normalized_price != preset_tp_price:
                log_info(
                    f"[ENTRY_TP_REFRESH] {target_stock.get('name')}({code}) "
                    f"preset_tp_price 정규화 {preset_tp_price} -> {normalized_price} (tick={tick})"
                )
            preset_tp_price = max(normalized_price, tick)
            target_stock['preset_tp_price'] = preset_tp_price

    if preset_tp_price <= 0 or total_qty <= 0:
        if total_qty <= 0:
            target_stock['preset_tp_qty'] = 0
        return True

    sell_res = kiwoom_orders.send_sell_order_market(
        code=code,
        qty=total_qty,
        token=KIWOOM_TOKEN,
        order_type="00",
        price=preset_tp_price,
    )
    new_ord_no = sell_res.get('ord_no') if isinstance(sell_res, dict) else ''
    if isinstance(sell_res, dict):
        err_msg = str(sell_res.get('return_msg') or sell_res.get('err_msg') or '')
        if ('매도가능수량' in err_msg) or ('잔고' in err_msg and '부족' in err_msg):
            target_stock['preset_tp_ord_no'] = ''
            target_stock['preset_tp_qty'] = 0
            log_info(
                f"[ENTRY_TP_REFRESH] {target_stock.get('name')}({code}) "
                "보유수량 부족 응답 수신으로 preset TP를 비활성화합니다."
            )
            return True
    target_stock['preset_tp_ord_no'] = new_ord_no
    target_stock['preset_tp_qty'] = int(total_qty or 0)
    if not new_ord_no:
        log_error(
            f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) refreshed preset TP order number missing."
        )
        return False
    log_info(
        f"[ENTRY_TP_REFRESH] {target_stock.get('name')}({code}) qty={total_qty} "
        f"tp_price={preset_tp_price} ord_no={new_ord_no}"
    )
    return True


def _update_db_for_buy(target_id, exec_price, now, receipt_snapshot):
    """비동기로 실행되는 BUY 체결 DB 업데이트 및 알림"""
    try:
        buy_qty = int(receipt_snapshot.get('buy_qty') or 0)
        avg_buy_price = float(receipt_snapshot.get('buy_price') or exec_price or 0)
        with DB.get_session() as session:
            session.query(RecommendationHistory).filter_by(id=target_id).update({
                "buy_price": avg_buy_price,
                "buy_qty": buy_qty,
                "status": "HOLDING",
                "buy_time": now
            })

        log_info(
            f"✅ [영수증: ID {target_id}] {receipt_snapshot.get('code')} "
            f"실제 매수 체결 반영 완료! avg={avg_buy_price:,} qty={buy_qty}"
        )

        if not receipt_snapshot.get('buy_execution_notified'):
            pending_msg = receipt_snapshot.get('pending_buy_msg')
            audience = _receipt_audience(receipt_snapshot)
            if pending_msg:
                final_msg = pending_msg.replace("그물망 투척!", "그물망 매수 체결!").replace("스나이퍼 포착!", "스나이퍼 매수 체결!")
                final_msg += f"\n✅ **평균 체결가:** `{avg_buy_price:,.0f}원` / **체결수량:** `{buy_qty}주`"
                event_bus.publish('TELEGRAM_BROADCAST', {'message': final_msg, 'audience': audience, 'parse_mode': 'Markdown'})
            else:
                event_bus.publish(
                    'TELEGRAM_BROADCAST',
                    {
                        'message': (
                            f"🛒 **[{receipt_snapshot.get('name')}]** 매수 체결 완료!\n"
                            f"평균 체결가: `{avg_buy_price:,.0f}원`\n체결수량: `{buy_qty}주`"
                        ),
                        'audience': audience,
                        'parse_mode': 'Markdown',
                    }
                )
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} BUY 처리 중 에러: {e}")


def _update_db_for_add(target_id, exec_price, exec_qty, now, receipt_snapshot, add_type, count_increment):
    """비동기로 실행되는 추가매수 체결 DB 업데이트"""
    try:
        add_count_after = int(receipt_snapshot.get('add_count') or 0)
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            old_price = float(record.buy_price) if record.buy_price is not None else 0.0
            old_qty = int(record.buy_qty or 0)
            new_avg = float(receipt_snapshot.get('buy_price') or exec_price or 0)
            new_qty = int(receipt_snapshot.get('buy_qty') or 0)

            record.buy_price = new_avg
            record.buy_qty = new_qty
            record.add_count = int(receipt_snapshot.get('add_count', record.add_count or 0) or 0)
            record.avg_down_count = int(receipt_snapshot.get('avg_down_count', record.avg_down_count or 0) or 0)
            record.pyramid_count = int(receipt_snapshot.get('pyramid_count', record.pyramid_count or 0) or 0)
            record.last_add_type = add_type
            record.last_add_at = now
            record.scale_in_locked = bool(receipt_snapshot.get('scale_in_locked', False))
            add_count_after = int(record.add_count or 0)

            # 보호선 보정값을 DB에도 반영 (있을 때만)
            if receipt_snapshot.get('trailing_stop_price') is not None:
                record.trailing_stop_price = float(receipt_snapshot.get('trailing_stop_price') or 0)
            if receipt_snapshot.get('hard_stop_price') is not None:
                record.hard_stop_price = float(receipt_snapshot.get('hard_stop_price') or 0)

        log_info(
            f"✅ [영수증: ID {target_id}] {receipt_snapshot.get('code')} 추가매수 체결 반영 "
            f"(avg={new_avg}, qty={new_qty}, type={add_type})"
        )

        if event_bus and count_increment:
            _type_kr = {'AVG_DOWN': '물타기', 'PYRAMID': '불타기'}.get(add_type, add_type)
            _strategy_kr = {'SCALPING': '스캘핑', 'SWING': '스윙'}.get(
                receipt_snapshot.get('strategy', ''), receipt_snapshot.get('strategy', ''))
            msg = (
                f"➕ 추가매수 체결\n"
                f"종목: {receipt_snapshot.get('name')} ({receipt_snapshot.get('code')})\n"
                f"전략: {_strategy_kr} | 유형: {_type_kr}\n"
                f"기존 평단가: {int(old_price):,}원 → 체결가: {int(exec_price):,}원\n"
                f"새 평단가: {int(new_avg):,}원 | 총 수량: {new_qty}주\n"
                f"누적 추가매수: {add_count_after}회"
            )
            event_bus.publish('TELEGRAM_BROADCAST', {
                'message': msg,
                'audience': _receipt_audience(receipt_snapshot),
                'parse_mode': None
            })
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} ADD 처리 중 에러: {e}")


def _update_db_for_sell(target_id, exec_price, now, receipt_snapshot, strategy, is_scalp_revive):
    """비동기로 실행되는 SELL 체결 DB 업데이트 및 알림 (스캘핑 부활 제외)"""
    try:
        with DB.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(id=target_id).first()
            if not record:
                return

            safe_buy_price = float(record.buy_price) if record.buy_price is not None else 0.0
            if safe_buy_price > 0:
                profit_rate = calculate_net_profit_rate(safe_buy_price, exec_price)
            else:
                profit_rate = 0.0
                log_error(f"⚠️ [수익률 계산 불가] ID {target_id}의 매수가(buy_price)가 누락되어 수익률을 0%로 처리합니다.")
            pre_add_avg_price = _safe_float(receipt_snapshot.get("pre_add_avg_price"), 0.0)
            pre_add_qty = _safe_int(receipt_snapshot.get("pre_add_qty"), 0)
            if pre_add_avg_price > 0 and pre_add_qty > 0:
                no_scale_in_counterfactual_profit_pct = calculate_net_profit_rate(pre_add_avg_price, exec_price)
                receipt_snapshot["no_scale_in_counterfactual_profit_pct"] = round(
                    float(no_scale_in_counterfactual_profit_pct),
                    4,
                )
                receipt_snapshot["scale_in_incremental_realized_delta_pct"] = round(
                    float(profit_rate) - float(no_scale_in_counterfactual_profit_pct),
                    4,
                )

            record.status = 'COMPLETED'
            record.sell_price = exec_price
            record.sell_time = now
            record.profit_rate = profit_rate

            log_info(
                f"🎉 [매매 완료: ID {target_id}] {receipt_snapshot.get('code')} "
                f"실매도가: {exec_price:,}원 / 수익률: {profit_rate}%"
            )

            _publish_sell_execution_message(
                name=receipt_snapshot.get('name') or '-',
                pending_msg=receipt_snapshot.get('pending_sell_msg') or '',
                audience=_receipt_audience(receipt_snapshot),
                exec_price=exec_price,
                profit_rate=profit_rate,
            )
            _log_holding_pipeline(
                receipt_snapshot.get('name'),
                str(receipt_snapshot.get('code', '')).strip()[:6],
                target_id,
                'sell_completed',
                sell_price=int(exec_price or 0),
                profit_rate=f"{profit_rate:+.2f}",
                exit_rule=receipt_snapshot.get('last_exit_rule') or '-',
                exit_decision_source=receipt_snapshot.get('last_exit_decision_source') or 'MANUAL',
                revive=bool(is_scalp_revive),
                strategy=strategy,
                no_scale_in_counterfactual_profit_pct=receipt_snapshot.get("no_scale_in_counterfactual_profit_pct", "-"),
                scale_in_incremental_realized_delta_pct=receipt_snapshot.get("scale_in_incremental_realized_delta_pct", "-"),
                pre_add_avg_price=receipt_snapshot.get("pre_add_avg_price", "-"),
                post_add_avg_price=receipt_snapshot.get("post_add_avg_price", "-"),
                pre_add_qty=receipt_snapshot.get("pre_add_qty", "-"),
                post_add_qty=receipt_snapshot.get("post_add_qty", "-"),
                allowed_runtime_apply=False,
                forbidden_uses=(
                    "EV|rolling|MTD|live_auto_promotion|runtime_apply_bridge|threshold_mutation|"
                    "provider_change|order_price_change|quantity_cap_change|broker_guard_bypass"
                ),
            )
            try:
                record_post_sell_candidate(
                    recommendation_id=target_id,
                    stock=receipt_snapshot,
                    code=str(receipt_snapshot.get('code', '')).strip()[:6],
                    sell_time=now,
                    buy_price=safe_buy_price,
                    sell_price=exec_price,
                    profit_rate=profit_rate,
                    buy_qty=int(float(getattr(record, 'buy_qty', 0) or receipt_snapshot.get('buy_qty', 0) or 0)),
                    exit_rule=receipt_snapshot.get('last_exit_rule') or '-',
                    strategy=strategy,
                    revive=bool(is_scalp_revive),
                    peak_profit=receipt_snapshot.get('last_exit_peak_profit'),
                    held_sec=receipt_snapshot.get('last_exit_held_sec'),
                    current_ai_score=receipt_snapshot.get('last_exit_current_ai_score'),
                    soft_stop_threshold_pct=receipt_snapshot.get('last_exit_soft_stop_threshold_pct'),
                    same_symbol_soft_stop_cooldown_would_block=receipt_snapshot.get(
                        'last_exit_same_symbol_soft_stop_cooldown_would_block'
                    ),
                )
            except Exception as exc:
                log_error(f"[POST_SELL] candidate record failed (id={target_id}): {exc}")
    except Exception as e:
        log_error(f"🚨 [DB 에러] ID {target_id} SELL 처리 중 에러: {e}")


def _handle_add_buy_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
) -> None:
    add_type = (target_stock.get('pending_add_type') or '').upper()
    old_price = float(target_stock.get('buy_price') or 0)
    old_qty = int(target_stock.get('buy_qty') or 0)
    request_qty = int(target_stock.get('pending_add_qty', 0) or 0)
    pending_ord_no = str(target_stock.get('pending_add_ord_no', '') or '').strip()
    history_order_no = pending_ord_no or order_no
    new_qty = old_qty + exec_qty
    if old_qty > 0:
        total_qty = old_qty + exec_qty
        new_avg = _avg_from_totals((old_price * old_qty) + (exec_price * exec_qty), total_qty)
    else:
        new_avg = exec_price

    target_stock['status'] = 'HOLDING'
    target_stock['buy_price'] = new_avg
    target_stock['buy_qty'] = new_qty
    target_stock['pre_add_avg_price'] = round(float(old_price or 0.0), 4)
    target_stock['post_add_avg_price'] = round(float(new_avg or 0.0), 4)
    target_stock['pre_add_qty'] = int(old_qty or 0)
    target_stock['post_add_qty'] = int(new_qty or 0)
    target_stock['last_add_type'] = add_type
    target_stock['last_add_at'] = now
    target_stock['last_add_time'] = time.time()
    if (
        add_type == 'AVG_DOWN'
        and str(target_stock.get('pending_add_reason') or '').strip() == 'reversal_add_ok'
    ):
        target_stock['reversal_add_state'] = 'POST_ADD_EVAL'
        target_stock['reversal_add_executed_at'] = now.timestamp()
    if not target_stock.get('holding_started_at'):
        target_stock['holding_started_at'] = now
    if isinstance(highest_prices, dict):
        # 추가매수 후 포지션 평단/수량이 바뀌면 기존 고점 기준 trailing은 새 포지션에 과민하다.
        highest_prices[code] = max(float(exec_price or 0), float(new_avg or 0))

    count_increment = False
    if not target_stock.get('pending_add_counted'):
        target_stock['add_count'] = int(target_stock.get('add_count', 0) or 0) + 1
        if add_type == 'AVG_DOWN':
            target_stock['avg_down_count'] = int(target_stock.get('avg_down_count', 0) or 0) + 1
        elif add_type == 'PYRAMID':
            target_stock['pyramid_count'] = int(target_stock.get('pyramid_count', 0) or 0) + 1
        target_stock['pending_add_counted'] = True
        count_increment = True

    filled = int(target_stock.get('pending_add_filled_qty', 0) or 0) + exec_qty
    target_stock['pending_add_filled_qty'] = filled
    pending_qty = int(target_stock.get('pending_add_qty', 0) or 0)

    protection_ok = _apply_scale_in_protection(target_stock, add_type)
    strategy = normalize_strategy(target_stock.get('strategy'))
    pos_tag = normalize_position_tag(strategy, target_stock.get('position_tag'))
    if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
        base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
        target_stock['preset_tp_price'] = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
        protection_ok = _refresh_scalp_preset_exit_order(target_stock, code, new_qty) and protection_ok

    if not protection_ok:
        target_stock['scale_in_locked'] = True
        log_error(
            f"⚠️ [ADD_PROTECT] {target_stock.get('name')}({code}) 보호선 재설정 실패로 "
            "scale_in_locked=True"
        )

    add_receipt_snapshot = _receipt_snapshot(target_stock, _ADD_RECEIPT_SNAPSHOT_KEYS)
    _update_db_for_add(
        target_id,
        exec_price,
        exec_qty,
        now,
        add_receipt_snapshot,
        add_type,
        count_increment,
    )
    record_add_history_event(
        DB,
        recommendation_id=target_id,
        stock_code=code,
        stock_name=target_stock.get('name'),
        strategy=target_stock.get('strategy'),
        add_type=add_type,
        event_type='EXECUTED',
        order_no=history_order_no,
        request_qty=request_qty or pending_qty or exec_qty,
        executed_qty=exec_qty,
        executed_price=exec_price,
        prev_buy_price=old_price,
        new_buy_price=new_avg,
        prev_buy_qty=old_qty,
        new_buy_qty=new_qty,
        add_count_after=target_stock.get('add_count', 0),
        reason='receipt_confirmed',
    )
    if pending_qty > 0 and filled >= pending_qty:
        _clear_pending_add_meta(target_stock)
    log_info(
        "[ADD_EXECUTED] "
        f"{target_stock.get('name')}({code}) "
        f"type={add_type} exec={exec_price:,} "
        f"new_avg={new_avg} new_qty={new_qty} add_count={target_stock.get('add_count')}"
    )
    _log_holding_pipeline(
        target_stock.get('name'),
        code,
        target_id,
        'scale_in_executed',
        metric_role='execution_quality_real_only',
        decision_authority='broker_receipt_observation_only',
        runtime_effect=False,
        forbidden_uses='runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim',
        actual_order_submitted=True,
        broker_order_forbidden=False,
        add_type=add_type,
        fill_price=int(exec_price or 0),
        fill_qty=int(exec_qty or 0),
        new_avg_price=f"{float(new_avg or 0):.2f}",
        new_buy_qty=int(new_qty or 0),
        add_count=int(target_stock.get('add_count', 0) or 0),
        reversal_add_state=target_stock.get('reversal_add_state', '-'),
        reversal_add_executed_at=target_stock.get('reversal_add_executed_at', '-'),
    )

def _handle_entry_buy_execution(
    *,
    target_id: int,
    target_stock: dict[str, Any],
    code: str,
    order_no: str,
    exec_price: int,
    exec_qty: int,
    now: datetime,
) -> None:
    effective_exec_qty, order_requested_qty, order_filled_qty = _resolve_entry_effective_fill_qty(
        target_stock=target_stock,
        code=code,
        order_no=order_no,
        exec_qty=exec_qty,
    )
    if effective_exec_qty <= 0:
        return

    old_qty = int(target_stock.get('buy_qty') or 0)
    old_price = float(target_stock.get('buy_price') or 0)
    if old_qty <= 0:
        _clear_split_entry_shadow_state(target_stock)
    new_qty = old_qty + effective_exec_qty
    if old_qty > 0:
        new_avg = _avg_from_totals(
            (old_price * old_qty) + (exec_price * effective_exec_qty),
            old_qty + effective_exec_qty,
        )
    else:
        new_avg = exec_price
    entry_mode = str(target_stock.get('entry_mode', 'normal') or 'normal')

    pending_entry_orders = target_stock.get('pending_entry_orders') or []
    if pending_entry_orders and order_no:
        for pending_order in pending_entry_orders:
            if str(pending_order.get('ord_no', '') or '').strip() != order_no:
                continue
            requested_qty = int(pending_order.get('qty', 0) or 0)
            pending_order['last_fill_price'] = exec_price
            pending_order['last_fill_at'] = time.time()
            log_info(
                f"[ENTRY_FILL] {target_stock.get('name')}({code}) "
                f"tag={pending_order.get('tag')} ord_no={order_no} "
                f"fill_qty={effective_exec_qty} raw_fill_qty={exec_qty} "
                f"filled={pending_order.get('filled_qty')}/{requested_qty} "
                f"fill_price={exec_price}"
            )
            break

    target_stock['status'] = 'HOLDING'
    target_stock['buy_price'] = new_avg
    target_stock['buy_qty'] = new_qty
    target_stock['entry_filled_qty'] = int(target_stock.get('entry_filled_qty', 0) or 0) + effective_exec_qty
    target_stock['entry_fill_amount'] = int(target_stock.get('entry_fill_amount', 0) or 0) + (exec_price * effective_exec_qty)
    target_stock['buy_time'] = now
    if not target_stock.get('holding_started_at'):
        target_stock['holding_started_at'] = now
    highest_prices[code] = max(highest_prices.get(code, 0), exec_price)

    requested_entry_qty = int(target_stock.get('entry_requested_qty', target_stock.get('requested_buy_qty', 0)) or 0)
    cum_filled_qty = int(target_stock.get('entry_filled_qty', 0) or 0)
    remaining_qty = max(0, requested_entry_qty - cum_filled_qty) if requested_entry_qty > 0 else 0
    fill_quality = (
        "FULL_FILL"
        if requested_entry_qty > 0 and cum_filled_qty >= requested_entry_qty
        else ("PARTIAL_FILL" if requested_entry_qty > 0 else "UNKNOWN")
    )
    target_stock['entry_fill_quality'] = fill_quality

    preset_tp_price = int(target_stock.get('preset_tp_price') or 0)
    preset_tp_ord_no_before = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
    preset_tp_ord_no_after = preset_tp_ord_no_before
    preset_sync_status = "NOT_APPLICABLE"
    preset_sync_reason = "non_scalping_or_non_default_tag"
    if requested_entry_qty > 0 and new_qty >= requested_entry_qty:
        log_info(
            f"[ENTRY_BUNDLE_FILLED] {target_stock.get('name')}({code}) "
            f"mode={target_stock.get('entry_mode', 'normal')} "
            f"filled_qty={new_qty}/{requested_entry_qty} avg_buy={new_avg}"
        )
        move_orders_to_terminal(target_stock, reason='entry_bundle_filled')
        target_stock.pop('pending_entry_orders', None)
        target_stock.pop('entry_requested_qty', None)
        target_stock.pop('requested_buy_qty', None)
        target_stock.pop('entry_filled_qty', None)
        target_stock.pop('entry_fill_amount', None)
        target_stock.pop('entry_bundle_id', None)

    strategy = normalize_strategy(target_stock.get('strategy'))
    pos_tag = normalize_position_tag(strategy, target_stock.get('position_tag'))
    target_stock['position_tag'] = pos_tag

    if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
        target_stock['exit_mode'] = 'SCALP_PRESET_TP'

        base_buy_price = int(target_stock.get('buy_price') or exec_price or 0)
        if base_buy_price <= 0:
            base_buy_price = exec_price

        preset_tp_price = kiwoom_utils.get_target_price_up(base_buy_price, 1.5)
        target_stock['preset_tp_price'] = preset_tp_price
        preset_tp_ord_no_before = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
        preset_hard_stop_pct = float(getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_PCT', -0.7) or -0.7)
        preset_hard_stop_grace_sec = int(getattr(TRADING_RULES, 'SCALP_PRESET_HARD_STOP_GRACE_SEC', 0) or 0)
        preset_hard_stop_emergency_pct = float(
            getattr(
                TRADING_RULES,
                'SCALP_PRESET_HARD_STOP_EMERGENCY_PCT',
                min(preset_hard_stop_pct - 0.5, -1.2),
            )
            or min(preset_hard_stop_pct - 0.5, -1.2)
        )
        if str(target_stock.get('entry_mode', '')).strip().lower() == 'fallback':
            preset_hard_stop_pct = float(
                getattr(
                    TRADING_RULES,
                    'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT',
                    preset_hard_stop_pct,
                )
                or preset_hard_stop_pct
            )
            preset_hard_stop_grace_sec = int(
                getattr(
                    TRADING_RULES,
                    'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC',
                    preset_hard_stop_grace_sec,
                )
                or preset_hard_stop_grace_sec
            )
            preset_hard_stop_emergency_pct = float(
                getattr(
                    TRADING_RULES,
                    'SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT',
                    preset_hard_stop_emergency_pct,
                )
                or preset_hard_stop_emergency_pct
            )
        target_stock['hard_stop_pct'] = preset_hard_stop_pct
        target_stock['hard_stop_grace_sec'] = preset_hard_stop_grace_sec
        target_stock['hard_stop_emergency_pct'] = preset_hard_stop_emergency_pct
        target_stock['protect_profit_pct'] = None
        target_stock['ai_review_done'] = False
        target_stock['ai_review_score'] = None
        target_stock['ai_review_action'] = None
        target_stock['last_ai_reviewed_at'] = None
        target_stock['exit_requested'] = False
        target_stock['exit_order_type'] = None
        target_stock['exit_order_time'] = None

        sell_qty = int(target_stock.get('buy_qty') or exec_qty or 0)
        refreshed = _refresh_scalp_preset_exit_order(target_stock, code, sell_qty)
        preset_tp_ord_no_after = str(target_stock.get('preset_tp_ord_no', '') or '').strip()
        preset_tp_qty = int(target_stock.get('preset_tp_qty', 0) or 0)

        if not refreshed:
            preset_sync_status = "REFRESH_FAILED"
            preset_sync_reason = "refresh_failed"
        elif not preset_tp_ord_no_after:
            preset_sync_status = "MISSING_ORD_NO"
            preset_sync_reason = "missing_ord_no"
        elif preset_tp_qty != sell_qty:
            preset_sync_status = "QTY_MISMATCH"
            preset_sync_reason = f"preset_tp_qty={preset_tp_qty},sell_qty={sell_qty}"
        else:
            preset_sync_status = "OK"
            preset_sync_reason = "-"

        if not refreshed or not target_stock.get('preset_tp_ord_no'):
            log_error(f"⚠️ [SCALP 출구엔진] {target_stock.get('name')} 지정가 매도 주문번호 미수신. 보유 감시로 보강 필요.")
        else:
            log_info(
                f"🎯 [SCALP 출구엔진 셋업] {target_stock.get('name')} "
                f"+1.5% 지정가({preset_tp_price:,}원) {sell_qty}주 매도망 전개 완료."
            )
            _log_holding_pipeline(
                target_stock.get('name'),
                code,
                target_id,
                'preset_exit_setup',
                preset_tp_price=int(preset_tp_price or 0),
                qty=int(sell_qty or 0),
                ord_no=str(target_stock.get('preset_tp_ord_no', '') or '-'),
            )

    _log_holding_pipeline(
        target_stock.get('name'),
        code,
        target_id,
        'position_rebased_after_fill',
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        requested_qty=int(requested_entry_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        avg_buy_price=f"{float(new_avg or 0):.2f}",
        entry_mode=entry_mode,
        fill_quality=fill_quality,
        preset_tp_price=int(preset_tp_price or 0),
        preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
        preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
        sync_status=preset_sync_status,
    )
    _emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code=code,
        target_id=target_id,
        now=now,
        entry_mode=entry_mode,
        fill_quality=fill_quality,
        requested_entry_qty=int(requested_entry_qty or 0),
        cum_filled_qty=int(cum_filled_qty or 0),
        remaining_qty=int(remaining_qty or 0),
        new_qty=int(new_qty or 0),
    )
    if strategy == 'SCALPING' and is_default_position_tag(strategy, pos_tag):
        sync_stage = 'preset_exit_sync_ok' if preset_sync_status == "OK" else 'preset_exit_sync_mismatch'
        _log_holding_pipeline(
            target_stock.get('name'),
            code,
            target_id,
            sync_stage,
            entry_mode=entry_mode,
            fill_quality=fill_quality,
            requested_qty=int(requested_entry_qty or 0),
            buy_qty=int(new_qty or 0),
            preset_tp_qty=int(target_stock.get('preset_tp_qty', 0) or 0),
            preset_tp_price=int(preset_tp_price or 0),
            preset_tp_ord_no_before=preset_tp_ord_no_before or "-",
            preset_tp_ord_no_after=preset_tp_ord_no_after or "-",
            sync_status=preset_sync_status,
            sync_reason=preset_sync_reason,
        )

    _log_holding_pipeline(
        target_stock.get('name'),
        code,
        target_id,
        'holding_started',
        metric_role='execution_quality_real_only',
        decision_authority='broker_receipt_observation_only',
        runtime_effect=False,
        forbidden_uses='runtime_threshold_apply/provider_route_change/bot_restart/sim_execution_quality_claim',
        actual_order_submitted=True,
        broker_order_forbidden=False,
        strategy=target_stock.get('strategy'),
        position_tag=target_stock.get('position_tag'),
        buy_price=f"{float(new_avg or 0):.2f}",
        buy_qty=int(new_qty or 0),
        fill_price=int(exec_price or 0),
        fill_qty=int(effective_exec_qty or 0),
        raw_fill_qty=int(exec_qty or 0),
        order_requested_qty=int(order_requested_qty or 0),
        order_filled_qty=int(order_filled_qty or 0),
        entry_mode=entry_mode,
    )

    buy_receipt_snapshot = _receipt_snapshot(target_stock, _BUY_RECEIPT_SNAPSHOT_KEYS)
    buy_receipt_snapshot['buy_execution_notified'] = bool(
        buy_receipt_snapshot.get('buy_execution_notified', False)
    )
    if not buy_receipt_snapshot.get('buy_execution_notified'):
        target_stock['buy_execution_notified'] = True
        target_stock.pop('pending_buy_msg', None)

    threading.Thread(
        target=_update_db_for_buy,
        args=(target_id, exec_price, now, buy_receipt_snapshot),
        daemon=True
    ).start()


def handle_real_execution(exec_data):
    """
    웹소켓에서 주문 체결(00) 통보가 오면 이 함수가 즉시 실행됩니다.
    고유 ID(id)를 추적하여 해당 매매 건의 실제 체결가를 정확히 기록합니다.
    """
    code = str(exec_data.get('code', '')).strip()[:6]
    exec_type = str(exec_data.get('type', '')).upper()
    order_no = str(exec_data.get('order_no', '') or '').strip()

    try:
        exec_price = int(float(exec_data.get('price', 0) or 0))
    except Exception:
        exec_price = 0

    try:
        exec_qty = int(float(exec_data.get('qty', 0) or 0))
    except Exception:
        exec_qty = 0

    if not code or exec_price <= 0:
        return

    state = _get_fast_state(code)
    if state and exec_qty > 0:
        with state['lock']:
            matched = False

            if exec_type == 'BUY':
                if order_no and order_no == str(state.get('buy_ord_no', '')):
                    state['cum_buy_qty'] += exec_qty
                    state['cum_buy_amount'] += exec_price * exec_qty
                    state['avg_buy_price'] = _avg_from_totals(state['cum_buy_amount'], state['cum_buy_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

            elif exec_type == 'SELL':
                valid_sell_ord_nos = {
                    str(state.get('sell_ord_no', '') or ''),
                    str(state.get('pending_cancel_ord_no', '') or ''),
                }
                if order_no and order_no in valid_sell_ord_nos:
                    state['cum_sell_qty'] += exec_qty
                    state['cum_sell_amount'] += exec_price * exec_qty
                    state['avg_sell_price'] = _avg_from_totals(state['cum_sell_amount'], state['cum_sell_qty'])
                    state['updated_at'] = _now_ts()
                    matched = True

        if matched:
            return

    now = datetime.now()
    now_t = now.time()

    with _active_state_lock():
        target_stock = _find_execution_target(code, exec_type, order_no)
        if not target_stock:
            ignore_context = _execution_ignore_context(code, exec_type, order_no)
            log_info(
                f"[EXEC_IGNORED] no matching active order. code={code}, "
                f"type={exec_type}, order_no={order_no} {ignore_context}"
            )
            return

        target_id = target_stock.get('id')
        if not target_id:
            log_error(f"🚨 [영수증] 종목 {code}의 고유 ID가 메모리에 없습니다. DB 업데이트가 불가능합니다.")
            return
        is_scalp_revive = False

        # ==========================================
        # 1️⃣ DB 상태 업데이트 (ID 기반 정밀 타격)
        # ==========================================
        if exec_type == 'BUY':
            pending_add = bool(target_stock.get('pending_add_order'))
            pending_ord_no = str(target_stock.get('pending_add_ord_no', '') or '').strip()
            is_add_fill = pending_add and (not order_no or order_no == pending_ord_no)

            if is_add_fill:
                _handle_add_buy_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                )
            else:
                _handle_entry_buy_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    order_no=order_no,
                    exec_price=exec_price,
                    exec_qty=exec_qty,
                    now=now,
                )
            
        elif exec_type == 'SELL':
            sell_context = _resolve_sell_execution_context(target_id, target_stock, exec_price, now_t)
            if not sell_context:
                return
            _, safe_buy_price, profit_rate, strategy, is_scalp_revive = sell_context

            if is_scalp_revive:
                if not _handle_scalp_revive_sell_execution(
                    target_id=target_id,
                    target_stock=target_stock,
                    code=code,
                    exec_price=exec_price,
                    now=now,
                    profit_rate=profit_rate,
                    safe_buy_price=safe_buy_price,
                    strategy=strategy,
                ):
                    return
            else:
                _finalize_standard_sell_execution(
                    target_id=target_id,
                    exec_price=exec_price,
                    now=now,
                    target_stock=target_stock,
                    strategy=strategy,
                    is_scalp_revive=is_scalp_revive,
                    code=code,
                )

    # 메모리 업데이트는 각 조건문 내에서 이미 수행됨
