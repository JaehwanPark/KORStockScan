"""Shared trading utilities for the sniper engine."""

import re
import time
from datetime import datetime, time as datetime_time, timedelta, timezone

from src.engine import kiwoom_orders
from src.utils import kiwoom_utils
from src.engine.sniper_time import (
    TIME_15_30,
    TIME_20_00,
    TIME_SCALPING_NEW_BUY_CUTOFF,
)

_KST = timezone(timedelta(hours=9))
_PENDING_SELL_ORDER_BIND_MAX_DELAY_SEC = 300.0


class BrokerRemainingQty(int):
    """Integer-compatible broker quantity with tri-state confirmation provenance."""

    def __new__(
        cls,
        value,
        *,
        confirmation_state: str,
        source: str,
        successful_exchanges=(),
    ):
        instance = int.__new__(cls, max(0, int(value or 0)))
        instance.confirmation_state = str(confirmation_state)
        instance.source = str(source)
        instance.successful_exchanges = tuple(
            sorted(
                {
                    str(exchange or "").strip().upper()
                    for exchange in (successful_exchanges or ())
                    if str(exchange or "").strip()
                }
            )
        )
        return instance


def _remaining_qty_result(
    value: int,
    *,
    confirmation_state: str,
    source: str,
    successful_exchanges=(),
) -> BrokerRemainingQty:
    return BrokerRemainingQty(
        value,
        confirmation_state=confirmation_state,
        source=source,
        successful_exchanges=successful_exchanges,
    )


def _strict_nonnegative_int(value):
    """Parse broker quantities without accepting float/scientific coercion."""

    if isinstance(value, bool):
        return None
    normalized = str(value if value is not None else "").strip()
    if not re.fullmatch(r"[+]?(?:\d{1,3}(?:,\d{3})+|\d+)", normalized):
        return None
    try:
        parsed = int(normalized.replace(",", ""))
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _pending_sell_order_route(row):
    row = row if isinstance(row, dict) else {}
    raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
    sor_yn = str(row.get("sor_yn") or raw.get("sor_yn") or "").strip().upper()
    if sor_yn == "Y":
        return "SOR"
    route = (
        str(row.get("stex_tp") or raw.get("dmst_stex_tp") or raw.get("stex_tp") or "")
        .strip()
        .upper()
    )
    if route in {"1", "KRX"}:
        return "KRX"
    if route in {"2", "NXT"}:
        return "NXT"
    if route in {"0", "SOR", "통합"}:
        return "SOR"
    return ""


def _pending_sell_order_side(row):
    normalized = str((row or {}).get("side") or "").strip().upper()
    if normalized in {"SELL", "S", "1", "매도"} or "매도" in normalized:
        return "SELL"
    if normalized in {"BUY", "B", "2", "매수"} or "매수" in normalized:
        return "BUY"
    return "UNKNOWN"


def _pending_sell_order_time_epoch(row, *, requested_date):
    row = row if isinstance(row, dict) else {}
    raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
    date_text = str(
        row.get("trade_date") or raw.get("ord_dt") or requested_date or ""
    ).strip()
    raw_time = str(raw.get("ord_tm") or "").strip().replace(":", "")
    if re.fullmatch(r"[0-9]{8}", date_text) is None:
        return None
    if re.fullmatch(r"[0-9]{6}(?:[0-9]{3})?", raw_time) is None:
        return None
    try:
        parsed = datetime.strptime(
            f"{date_text}{raw_time[:6]}", "%Y%m%d%H%M%S"
        ).replace(tzinfo=_KST)
    except ValueError:
        return None
    return parsed.timestamp()


def _pending_sell_order_session(order_epoch):
    observed_t = datetime.fromtimestamp(order_epoch, _KST).time().replace(tzinfo=None)
    if datetime_time(hour=8) <= observed_t < datetime_time(hour=8, minute=50):
        return "krx_like_premarket"
    if datetime_time(hour=9) <= observed_t < TIME_15_30:
        return "krx_regular"
    if datetime_time(hour=15, minute=45) <= observed_t < datetime_time(hour=16):
        return "nxt_aftermarket_early_sell"
    if datetime_time(hour=16) <= observed_t < datetime_time(hour=16, minute=10):
        return "nxt_open_observe"
    if datetime_time(hour=16, minute=10) <= observed_t < TIME_SCALPING_NEW_BUY_CUTOFF:
        return "nxt_entry_window"
    if TIME_SCALPING_NEW_BUY_CUTOFF <= observed_t < TIME_20_00:
        return "nxt_close_only"
    return "outside_krx_nxt_window"


def resolve_pending_sell_order_no(target_stock, token, *, now_epoch=None):
    """Bind a blank pending generation to one exact, still-open broker order.

    This is reconciliation-only.  Absence, ambiguity, or an invalid official
    identity never grants a new submit or clears the pending generation.
    """

    if not isinstance(target_stock, dict):
        return None, "pending_sell_order_runtime_target_invalid"
    try:
        from src.engine import sniper_execution_receipts as _receipt_handlers
    except Exception as exc:
        return None, f"pending_sell_order_custody_import_failed:{type(exc).__name__}"
    per_target_lock = target_stock.get("lock")
    custody_lock = (
        per_target_lock
        if hasattr(per_target_lock, "__enter__")
        and hasattr(per_target_lock, "__exit__")
        else (_receipt_handlers._STATE_LOCK or _receipt_handlers.RECEIPT_LOCK)
    )
    context_keys = _receipt_handlers._SELL_PENDING_SUBMIT_CONTEXT_KEYS
    with custody_lock:
        validated_context, validation_reason = (
            _receipt_handlers._validated_sell_pending_submit_context(target_stock)
        )
        owner_position_qty = _strict_nonnegative_int(
            target_stock.get("sell_submit_owner_position_qty")
        )
        if validated_context is None or owner_position_qty is None:
            return None, f"pending_sell_order_context_invalid:{validation_reason}"
        durable_fields, durable_reason = (
            _receipt_handlers.load_pending_sell_submit_custody(
                target_id=target_stock.get("id"),
                code=str(target_stock.get("code") or "").strip()[:6],
                position_qty=owner_position_qty,
            )
        )
        if not isinstance(durable_fields, dict) or any(
            durable_fields.get(key) != target_stock.get(key) for key in context_keys
        ):
            return None, f"pending_sell_order_durable_context_invalid:{durable_reason}"
        immutable_context = {key: target_stock.get(key) for key in context_keys}
    code = str(
        target_stock.get("sell_submit_code") or target_stock.get("code") or ""
    ).strip()[:6]
    generation = str(target_stock.get("sell_submit_generation") or "").strip()
    context_sha256 = str(target_stock.get("sell_submit_context_sha256") or "").strip()
    requested_qty = _strict_nonnegative_int(
        target_stock.get("sell_submit_requested_qty")
    )
    started_at = target_stock.get("sell_submit_started_at")
    try:
        started_at = float(started_at)
    except (TypeError, ValueError):
        started_at = 0.0
    intended_route = (
        str(target_stock.get("sell_submit_intended_route") or "").strip().upper()
    )
    intended_session = str(
        target_stock.get("sell_submit_intended_session_bucket") or ""
    ).strip()
    if (
        re.fullmatch(r"[0-9]{6}", code) is None
        or re.fullmatch(r"[0-9a-f]{32}", generation) is None
        or re.fullmatch(r"[0-9a-f]{64}", context_sha256) is None
        or requested_qty is None
        or requested_qty <= 0
        or started_at <= 0
        or intended_route not in {"KRX", "NXT", "SOR"}
        or not intended_session
        or not token
    ):
        return None, "pending_sell_order_context_invalid"
    observed_now = time.time() if now_epoch is None else float(now_epoch)
    requested_date = datetime.fromtimestamp(started_at, _KST).strftime("%Y%m%d")
    try:
        history_rows, history_meta = (
            kiwoom_utils.get_order_reference_snapshot_kt00007_with_meta(
                token,
                ord_dt=requested_date,
                qry_tp="1",
                sell_tp="1",
                stk_cd=code,
                dmst_stex_tp="%",
            )
        )
        open_rows, open_meta = (
            kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
                token,
                stk_cd=code,
                all_stk_tp="1",
                trde_tp="1",
                stex_tp="0",
            )
        )
    except Exception as exc:
        return None, f"pending_sell_order_snapshot_failed:{type(exc).__name__}"
    if not bool((history_meta or {}).get("request_succeeded", False)):
        return None, "pending_sell_order_history_snapshot_unconfirmed"
    if not bool((history_meta or {}).get("normalization_contract_complete", False)):
        return None, "pending_sell_order_history_snapshot_contract_incomplete"
    if not bool((open_meta or {}).get("request_succeeded", False)):
        return None, "pending_sell_order_open_snapshot_unconfirmed"
    if not bool((open_meta or {}).get("normalization_contract_complete", False)):
        return None, "pending_sell_order_open_snapshot_contract_incomplete"

    def exact_identity(row, *, require_time, expected_source):
        if not isinstance(row, dict):
            return None
        if str(row.get("source_api") or "").strip() != expected_source:
            return None
        row_code = str(row.get("code") or "").strip()[:6]
        side = _pending_sell_order_side(row)
        qty = _strict_nonnegative_int(row.get("qty"))
        remaining_qty = _strict_nonnegative_int(row.get("remaining_qty"))
        order_no = str(row.get("ord_no") or "").strip()
        route = _pending_sell_order_route(row)
        route_matches = route == intended_route
        if (
            row_code != code
            or side != "SELL"
            or row.get("submitted_quantity_source_valid") is not True
            or qty != requested_qty
            or remaining_qty is None
            or remaining_qty <= 0
            or re.fullmatch(r"[0-9]{7}", order_no) is None
            or int(order_no) <= 0
            or not route_matches
        ):
            return None
        if require_time:
            order_epoch = _pending_sell_order_time_epoch(
                row, requested_date=requested_date
            )
            if (
                order_epoch is None
                or order_epoch < int(started_at)
                or order_epoch > started_at + _PENDING_SELL_ORDER_BIND_MAX_DELAY_SEC
                or order_epoch > observed_now + 5.0
                or _pending_sell_order_session(order_epoch) != intended_session
            ):
                return None
        return order_no, route

    open_identities = {
        identity
        for row in open_rows or ()
        if (
            identity := exact_identity(
                row,
                require_time=False,
                expected_source="ka10075",
            )
        )
        is not None
    }
    history_identities = {
        identity
        for row in history_rows or ()
        if (
            identity := exact_identity(
                row,
                require_time=True,
                expected_source="kt00007",
            )
        )
        is not None
    }
    candidate_order_numbers = {
        identity[0] for identity in open_identities | history_identities
    }
    matched = sorted(
        order_no
        for order_no in candidate_order_numbers
        if (
            (open_routes := {r for number, r in open_identities if number == order_no})
            == (
                history_routes := {
                    r for number, r in history_identities if number == order_no
                }
            )
            and len(open_routes) == 1
            and len(history_routes) == 1
        )
    )
    if len(matched) != 1:
        return None, (
            "pending_sell_order_unique_match_missing"
            if not matched
            else "pending_sell_order_unique_match_ambiguous"
        )
    with custody_lock:
        revalidated_context, revalidation_reason = (
            _receipt_handlers._validated_sell_pending_submit_context(target_stock)
        )
        reloaded_fields, reload_reason = (
            _receipt_handlers.load_pending_sell_submit_custody(
                target_id=target_stock.get("id"),
                code=code,
                position_qty=owner_position_qty,
            )
        )
        if (
            revalidated_context is None
            or not isinstance(reloaded_fields, dict)
            or any(
                target_stock.get(key) != immutable_context.get(key)
                for key in context_keys
            )
            or any(
                reloaded_fields.get(key) != immutable_context.get(key)
                for key in context_keys
            )
            or str(
                target_stock.get("sell_odno") or target_stock.get("sell_ord_no") or ""
            ).strip()
        ):
            return None, (
                "pending_sell_order_generation_intervened:"
                f"{revalidation_reason}:{reload_reason}"
            )
        target_stock.update(
            {
                "sell_odno": matched[0],
                "sell_pending_order_bound_generation": generation,
                "sell_pending_order_bound_context_sha256": context_sha256,
                "sell_pending_order_bound_source": (
                    "kt00007_plus_ka10075_exact_unique"
                ),
                "sell_pending_order_bound_at": observed_now,
                "sell_cancel_reconciliation_required": True,
                "sell_cancel_reconciliation_source": (
                    "pending_sell_order_number_exactly_bound"
                ),
            }
        )
    return matched[0], "kt00007_plus_ka10075_exact_unique"


def send_market_exit_now(code, qty, token):
    """정규장 중 즉시 시장가 청산용 공통 래퍼"""
    return kiwoom_orders.send_sell_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type="3",
    )


def send_exit_best_ioc(
    code,
    qty,
    token,
    *,
    dmst_stex_tp=None,
    reason_type=None,
    strategy=None,
    bypass_open_time_block=False,
):
    """[공통 긴급 청산 래퍼] 최유리(IOC, 16) 조건으로 즉각 청산 시도"""
    kwargs = {
        "code": code,
        "qty": qty,
        "token": token,
        "order_type": "16",
        "dmst_stex_tp": dmst_stex_tp,
        "reason_type": reason_type,
        "strategy": strategy,
    }
    if bypass_open_time_block:
        kwargs["bypass_open_time_block"] = True
    return kiwoom_orders.send_sell_order_market(**kwargs)


def _cancel_response_success(response) -> bool:
    if not isinstance(response, dict):
        return False
    raw_code = response.get("return_code", response.get("rt_cd"))
    if raw_code is None or isinstance(raw_code, bool):
        return False
    return str(raw_code).strip() == "0"


def cancel_response_ack_exact(
    response,
    *,
    intended_route="SOR",
    expected_orig_order_no="",
    expected_code="",
    expected_max_qty=None,
) -> bool:
    """Validate the documented kt10003 acceptance identity."""

    if not _cancel_response_success(response):
        return False
    cancel_order_no = str(response.get("ord_no") or "").strip()
    base_original_order_no = str(response.get("base_orig_ord_no") or "").strip()
    cancelled_qty = _strict_nonnegative_int(response.get("cncl_qty"))
    broker_route = (
        str(
            response.get("effective_dmst_stex_tp") or response.get("broker_route") or ""
        )
        .strip()
        .upper()
    )
    intended = str(intended_route or "SOR").strip().upper()
    expected_original = str(expected_orig_order_no or "").strip()
    expected_stock_code = str(expected_code or "").strip()[:6]
    max_cancel_qty = _strict_nonnegative_int(expected_max_qty)
    route_matches = broker_route == intended or (
        intended == "SOR" and broker_route in {"SOR", "KRX", "NXT"}
    )
    return bool(
        re.fullmatch(r"[0-9]{7}", cancel_order_no)
        and int(cancel_order_no) > 0
        and re.fullmatch(r"[0-9]{7}", base_original_order_no)
        and int(base_original_order_no) > 0
        and cancelled_qty is not None
        and cancelled_qty > 0
        and (max_cancel_qty is None or cancelled_qty <= max_cancel_qty)
        and response.get("broker_route_attempted") is True
        and response.get("cancel_request_bound") is True
        and response.get("cancel_request_api_id") == "kt10003"
        and re.fullmatch(
            r"[0-9]{7}",
            str(response.get("cancel_request_orig_ord_no") or "").strip(),
        )
        and (
            not expected_original
            or str(response.get("cancel_request_orig_ord_no") or "").strip()
            == expected_original
        )
        and re.fullmatch(
            r"[0-9]{6}",
            str(response.get("cancel_request_code") or "").strip()[:6],
        )
        and (
            not expected_stock_code
            or str(response.get("cancel_request_code") or "").strip()[:6]
            == expected_stock_code
        )
        and str(response.get("cancel_request_qty") or "").strip() == "0"
        and str(response.get("cancel_request_route") or "").strip().upper()
        == broker_route
        and route_matches
    )


def _cancel_response_message(response) -> str:
    if isinstance(response, dict):
        return str(response.get("return_msg", "") or "")
    return str(response or "")


def _cancel_reject_indicates_sor_exchange_mismatch(message: str) -> bool:
    text = str(message or "")
    return "571412" in text or "원주문이 SOR주문" in text


def _cancel_exchange_from_unfilled_row(row: dict | None) -> str:
    row = row if isinstance(row, dict) else {}
    raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
    sor_yn = str(row.get("sor_yn") or raw.get("sor_yn") or "").strip().upper()
    if sor_yn == "Y":
        return "SOR"
    stex_tp = str(row.get("stex_tp") or raw.get("stex_tp") or "").strip().upper()
    if stex_tp == "1":
        return "KRX"
    if stex_tp == "2":
        return "NXT"
    stex_text = (
        str(row.get("stex_tp_txt") or raw.get("stex_tp_txt") or "").strip().upper()
    )
    if "NXT" in stex_text:
        return "NXT"
    if "KRX" in stex_text:
        return "KRX"
    return ""


def _resolve_cancel_exchange_from_unfilled_snapshot(
    code: str, orig_ord_no: str, token: str
) -> str:
    try:
        rows = kiwoom_utils.get_unfilled_order_snapshot_ka10075(
            token,
            stk_cd=code,
            stex_tp="0",
        )
    except Exception:
        return ""
    normalized_ord_no = str(orig_ord_no or "").strip()
    for row in rows or []:
        row_ord_no = str((row or {}).get("ord_no") or "").strip()
        if row_ord_no != normalized_ord_no:
            continue
        return _cancel_exchange_from_unfilled_row(row)
    return ""


def send_cancel_order_with_exchange_retry(
    code, orig_ord_no, token, qty=0, dmst_stex_tp="SOR"
):
    cancel_exchange = str(dmst_stex_tp or "SOR").strip().upper()
    if cancel_exchange not in {"KRX", "NXT", "SOR"}:
        cancel_exchange = "SOR"
    res = kiwoom_orders.send_cancel_order(
        code=code,
        orig_ord_no=orig_ord_no,
        token=token,
        qty=qty,
        dmst_stex_tp=cancel_exchange,
    )
    if _cancel_response_success(res) or cancel_exchange != "SOR":
        return res
    if not _cancel_reject_indicates_sor_exchange_mismatch(
        _cancel_response_message(res)
    ):
        return res

    resolved_exchange = _resolve_cancel_exchange_from_unfilled_snapshot(
        code, orig_ord_no, token
    )
    if resolved_exchange not in {"KRX", "NXT"}:
        return res
    return kiwoom_orders.send_cancel_order(
        code=code,
        orig_ord_no=orig_ord_no,
        token=token,
        qty=qty,
        dmst_stex_tp=resolved_exchange,
    )


def _cancelled_sell_order_absence_confirmed(code, orig_ord_no, token):
    """Require a successful ka10075 snapshot proving one order is terminal."""

    normalized_code = str(code or "").strip()[:6]
    normalized_order_no = str(orig_ord_no or "").strip()
    if not normalized_order_no:
        return False, "sell_order_number_missing"
    try:
        rows, source_meta = kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
            token,
            all_stk_tp="0",
            trde_tp="0",
            stex_tp="0",
        )
    except Exception as exc:
        return False, f"unfilled_snapshot_failed:{type(exc).__name__}"
    if not bool((source_meta or {}).get("request_succeeded", False)):
        return False, "unfilled_snapshot_unconfirmed"
    if not bool((source_meta or {}).get("normalization_contract_complete", False)):
        return False, "unfilled_snapshot_contract_incomplete"
    for row in rows or ():
        if not isinstance(row, dict):
            continue
        raw = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        row_code = str(
            row.get("code") or row.get("stk_cd") or raw.get("stk_cd") or ""
        ).strip()[:6]
        row_order_no = str(
            row.get("ord_no")
            or row.get("odno")
            or raw.get("ord_no")
            or raw.get("odno")
            or ""
        ).strip()
        if row_order_no == normalized_order_no and (
            not row_code or row_code == normalized_code
        ):
            return False, "sell_order_still_open"
    return True, "ka10075_terminal_absence_confirmed"


def _pending_cancel_ack_exact(target_stock, *, code, order_no):
    if not isinstance(target_stock, dict):
        return False
    try:
        from src.engine import sniper_execution_receipts as _receipt_handlers

        return bool(
            _receipt_handlers.pending_sell_cancel_ack_exact(
                target_stock,
                code=code,
                order_no=order_no,
            )
        )
    except Exception:
        return False


def _pending_cancel_intent_exact(target_stock, *, code, order_no):
    if not isinstance(target_stock, dict):
        return False
    try:
        from src.engine import sniper_execution_receipts as _receipt_handlers

        return bool(
            _receipt_handlers.pending_sell_cancel_intent_exact(
                target_stock,
                code=code,
                order_no=order_no,
            )
        )
    except Exception:
        return False


def _persist_pending_cancel_intent(target_stock, *, order_no, broker_route):
    if not isinstance(target_stock, dict):
        return False
    try:
        from src.engine import sniper_execution_receipts as _receipt_handlers

        return bool(
            _receipt_handlers.persist_pending_sell_cancel_intent_custody(
                target_stock,
                order_no=order_no,
                broker_route=broker_route,
            )
        )
    except Exception:
        return False


def _persist_pending_cancel_ack(target_stock, *, order_no, cancel_response):
    if not isinstance(target_stock, dict):
        return False
    try:
        from src.engine import sniper_execution_receipts as _receipt_handlers

        return bool(
            _receipt_handlers.persist_pending_sell_cancel_ack_custody(
                target_stock,
                order_no=order_no,
                cancel_response=cancel_response,
            )
        )
    except Exception:
        return False


def confirm_cancel_or_reload_remaining(
    code,
    orig_ord_no,
    token,
    expected_qty,
    *,
    target_stock=None,
):
    """
    Return a broker-confirmed remaining position after an acknowledged cancel.

    ``expected_qty`` is intentionally not a fallback.  Reusing the pre-cancel
    quantity after an unknown cancel/inventory result can duplicate a partially
    filled SELL, so every ambiguous path fails closed with zero.
    """
    normalized_order_no = str(orig_ord_no or "").strip()
    if normalized_order_no:
        pending_generation_owned = bool(
            isinstance(target_stock, dict)
            and str(target_stock.get("sell_submit_generation") or "").strip()
        )
        if not pending_generation_owned:
            return _remaining_qty_result(
                0,
                confirmation_state="unknown",
                source="sell_cancel_pending_generation_required",
            )
        intended_route = (
            str((target_stock or {}).get("sell_submit_intended_route") or "SOR")
            .strip()
            .upper()
        )
        cancel_intent_reused = _pending_cancel_intent_exact(
            target_stock,
            code=code,
            order_no=normalized_order_no,
        )
        cancel_ack_reused = _pending_cancel_ack_exact(
            target_stock,
            code=code,
            order_no=normalized_order_no,
        )
        if not cancel_ack_reused:
            if (
                pending_generation_owned
                and not cancel_intent_reused
                and not _persist_pending_cancel_intent(
                    target_stock,
                    order_no=normalized_order_no,
                    broker_route=intended_route,
                )
            ):
                return _remaining_qty_result(
                    0,
                    confirmation_state="unknown",
                    source="cancel_intent_durability_failed",
                )
            if not pending_generation_owned or not cancel_intent_reused:
                cancel_sender = (
                    kiwoom_orders.send_cancel_order
                    if pending_generation_owned
                    else send_cancel_order_with_exchange_retry
                )
                cancel_result = cancel_sender(
                    code=code,
                    orig_ord_no=normalized_order_no,
                    token=token,
                    qty=0,
                    dmst_stex_tp=intended_route,
                )
                if cancel_response_ack_exact(
                    cancel_result,
                    intended_route=intended_route,
                    expected_orig_order_no=normalized_order_no,
                    expected_code=code,
                    expected_max_qty=expected_qty,
                ):
                    if (
                        isinstance(target_stock, dict)
                        and str(
                            target_stock.get("sell_submit_generation") or ""
                        ).strip()
                        and not _persist_pending_cancel_ack(
                            target_stock,
                            order_no=normalized_order_no,
                            cancel_response=cancel_result,
                        )
                    ):
                        # The intent remains durable.  Do not invent an ACK;
                        # terminal proof below may still close the generation.
                        pass
                elif not pending_generation_owned or not _pending_cancel_intent_exact(
                    target_stock, code=code, order_no=normalized_order_no
                ):
                    return _remaining_qty_result(
                        0,
                        confirmation_state="unknown",
                        source="cancel_unconfirmed",
                    )
                time.sleep(0.5)
        terminal_absent, terminal_source = _cancelled_sell_order_absence_confirmed(
            code,
            normalized_order_no,
            token,
        )
        if not terminal_absent:
            return _remaining_qty_result(
                0,
                confirmation_state="unknown",
                source=terminal_source,
            )
        if (
            isinstance(target_stock, dict)
            and str(target_stock.get("sell_submit_generation") or "").strip()
        ):
            # The ACK and terminal order absence are necessary but not enough
            # to grant a replacement order.  The stateful owner must first
            # reconcile the receipt ledger, commit DB HOLDING, and unlink the
            # exact old generation.  Returning a quantity here would let the
            # caller overwrite that still-durable generation.
            return _remaining_qty_result(
                0,
                confirmation_state="unknown",
                source="cancel_terminal_release_required",
            )

    try:
        real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(token)
        successful = {
            str(exchange or "").strip().upper()
            for exchange in (successful_exchanges or ())
        }
        matching_rows = [
            item
            for item in (real_inventory or [])
            if str(item.get("code", "")).strip()[:6] == code
        ]
        if matching_rows:
            if not {"KRX", "NXT"}.issubset(successful):
                return _remaining_qty_result(
                    0,
                    confirmation_state="unknown",
                    source="kt00018_partial_venue_confirmation",
                    successful_exchanges=successful,
                )
            parsed_quantities = [
                _strict_nonnegative_int(item.get("qty")) for item in matching_rows
            ]
            if any(quantity is None for quantity in parsed_quantities):
                return _remaining_qty_result(
                    0,
                    confirmation_state="unknown",
                    source="kt00018_inventory_quantity_malformed",
                    successful_exchanges=successful,
                )
            quantity = sum(parsed_quantities)
            if quantity > 0:
                return _remaining_qty_result(
                    quantity,
                    confirmation_state="confirmed_positive",
                    source="kt00018_position_found",
                    successful_exchanges=successful,
                )
            if {"KRX", "NXT"}.issubset(successful):
                return _remaining_qty_result(
                    0,
                    confirmation_state="verified_zero",
                    source="kt00018_all_venues_zero_row",
                    successful_exchanges=successful,
                )
    except Exception:
        return _remaining_qty_result(
            0,
            confirmation_state="unknown",
            source="inventory_lookup_failed",
        )
    if {"KRX", "NXT"}.issubset(successful):
        return _remaining_qty_result(
            0,
            confirmation_state="verified_zero",
            source="kt00018_all_venues_position_absent",
            successful_exchanges=successful,
        )
    return _remaining_qty_result(
        0,
        confirmation_state="unknown",
        source="kt00018_partial_venue_confirmation",
        successful_exchanges=successful,
    )


def extract_ord_no(res):
    if isinstance(res, dict):
        return str(res.get("ord_no", "") or res.get("odno", "") or "")
    return ""


def is_ok_response(res):
    if isinstance(res, dict):
        return str(res.get("return_code", res.get("rt_cd", ""))) == "0"
    return bool(res)
