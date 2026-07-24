import requests
import json
import re
import threading
import time
from datetime import datetime, time as datetime_time
from zoneinfo import ZoneInfo

# 💡 Level 1 & 2 공통 모듈
from src.engine import sniper_config
from src.utils.logger import log_error, log_info
from src.utils.constants import TRADING_RULES
from src.core.event_bus import EventBus
from src.utils import kiwoom_utils
from src.engine.trade_pause_control import is_buy_side_paused, get_pause_state_label

# ==========================================
# 1. 계좌 및 자산 조회 API
# ==========================================
_LAST_INVENTORY_ERRORS = []
_LAST_DEPOSIT_OVERRIDE = None
_LAST_SUCCESSFUL_DEPOSIT = 0
_LAST_SUCCESSFUL_DEPOSIT_AT = 0.0
_LAST_DEPOSIT_ERRORS = []
_LAST_DEPOSIT_META = {}
_LAST_DEPOSIT_FLOOR_LOG_MARKER = None
_DEPOSIT_API_COOLDOWN_UNTIL = 0.0
_DEPOSIT_API_COOLDOWN_REASON = ""
_ORDERABLE_AMOUNT_CACHE_LOCK = threading.RLock()
_DEPOSIT_API_FETCH_LOCKS = {}
_LAST_SUCCESSFUL_DEPOSIT_BY_KEY = {}
_ORDERABLE_AMOUNT_CACHE = {}
KST = ZoneInfo("Asia/Seoul")
KRX_REGULAR_OPEN = datetime_time(hour=9, minute=0)
KRX_REGULAR_CLOSE = datetime_time(hour=15, minute=30)
_DEFENSIVE_BUY_TIME_BLOCK_OVERRIDE_REASONS = frozenset(
    {
        "stop_line_touch_mandatory_avg_down",
        "deep_recovery_avg_down",
        "late_loss_avg_down_retry",
    }
)


def get_last_inventory_errors():
    """최근 잔고 조회 실패 원인을 반환합니다."""
    return list(_LAST_INVENTORY_ERRORS)


def get_last_deposit_errors():
    """최근 주문가능금액 조회 실패 원인을 반환합니다."""
    return list(_LAST_DEPOSIT_ERRORS)


def get_last_deposit_meta():
    """최근 주문가능금액 조회 출처와 cache 상태를 반환합니다."""
    return dict(_LAST_DEPOSIT_META)


def reset_orderable_amount_cache():
    """테스트/운영 진단용 주문가능금액 loop cache 초기화."""
    global _LAST_DEPOSIT_META
    with _ORDERABLE_AMOUNT_CACHE_LOCK:
        _ORDERABLE_AMOUNT_CACHE.clear()
        _DEPOSIT_API_FETCH_LOCKS.clear()
    _LAST_DEPOSIT_META = {}


def reset_deposit_diagnostics():
    """테스트/운영 진단용 최근 주문가능금액 에러/메타 초기화."""
    global _LAST_DEPOSIT_META, _LAST_DEPOSIT_FLOOR_LOG_MARKER
    _LAST_DEPOSIT_META = {}
    _LAST_DEPOSIT_FLOOR_LOG_MARKER = None
    _LAST_DEPOSIT_ERRORS.clear()


def _set_last_deposit_meta(
    source,
    *,
    amount=0,
    age_sec=None,
    cache_hit=False,
    fallback_used=False,
    extra=None,
):
    global _LAST_DEPOSIT_META
    meta = {
        "source": str(source or ""),
        "amount": int(amount or 0),
        "cache_hit": bool(cache_hit),
        "fallback_used": bool(fallback_used),
    }
    if age_sec is not None:
        meta["age_sec"] = round(float(age_sec), 3)
    if isinstance(extra, dict):
        meta.update(extra)
    _LAST_DEPOSIT_META = meta
    return meta


def _apply_kt00001_orderable_amount_floor(
    amount,
    *,
    source,
    age_sec=None,
    cache_hit=False,
    fallback_used=False,
):
    """Apply the operator-approved live budget floor only to valid kt00001 values."""
    global _LAST_DEPOSIT_FLOOR_LOG_MARKER
    try:
        raw_amount = max(0, int(float(amount or 0)))
    except (TypeError, ValueError):
        raw_amount = 0
    floor_amount = max(
        0,
        int(
            getattr(
                TRADING_RULES,
                "KT00001_ORDERABLE_AMOUNT_MIN_FLOOR_KRW",
                0,
            )
            or 0
        ),
    )
    floor_applied = floor_amount > 0 and raw_amount < floor_amount
    effective_amount = floor_amount if floor_applied else raw_amount
    _set_last_deposit_meta(
        source,
        amount=effective_amount,
        age_sec=age_sec,
        cache_hit=cache_hit,
        fallback_used=fallback_used,
        extra={
            "raw_amount": raw_amount,
            "effective_amount": effective_amount,
            "minimum_floor_krw": floor_amount,
            "minimum_floor_applied": floor_applied,
            "minimum_floor_authority": "operator_approved_2026_07_22",
            "minimum_floor_rollback_krw": 0,
        },
    )
    marker = (raw_amount, floor_amount)
    if floor_applied and _LAST_DEPOSIT_FLOOR_LOG_MARKER != marker:
        log_info(
            f"💰 [주문가능금액 보정] kt00001 원본 {raw_amount:,}원 -> "
            f"적용 {effective_amount:,}원 (operator floor, rollback=0원)"
        )
        _LAST_DEPOSIT_FLOOR_LOG_MARKER = marker
    return effective_amount


def is_auth_failure_error(error) -> bool:
    """키움 인증/토큰 무효화 계열 실패인지 판정합니다."""
    if not isinstance(error, dict):
        return False
    msg = str(error.get("return_msg") or error.get("err_msg") or "")
    code = str(error.get("return_code") or error.get("rt_cd") or "")
    lowered = msg.lower()
    return "8005" in code or "token" in lowered or "토큰" in msg or "인증" in msg


def is_request_limit_error(error) -> bool:
    """키움 API 요청 제한 초과 계열 실패인지 판정합니다."""
    if not isinstance(error, dict):
        return False
    msg = str(error.get("return_msg") or error.get("err_msg") or "")
    code = str(error.get("return_code") or error.get("rt_cd") or "")
    return (
        "1700" in code
        or "1700" in msg
        or "허용된 요청 개수" in msg
        or "요청 개수" in msg
        or "request count" in msg.lower()
    )


def is_deposit_transport_error(error) -> bool:
    """키움 계좌 API transport/sendReceive 계열 실패인지 판정합니다."""
    if not isinstance(error, dict):
        return False
    msg = str(error.get("return_msg") or error.get("err_msg") or "")
    code = str(error.get("return_code") or error.get("rt_cd") or "")
    lowered = msg.lower()
    code_or_msg_marks_transport = code == "2000" or "[2000]" in msg or "(2000" in msg
    return code_or_msg_marks_transport and (
        "sendreceive" in lowered or "wingsj" in lowered or "-994" in msg
    )


def _parse_kiwoom_amount(value, *, field_name):
    """Parse Kiwoom numeric string fields and reject schema drift clearly."""
    raw = "" if value is None else str(value).strip()
    normalized = raw.replace(",", "")
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", normalized):
        raise ValueError(f"{field_name} schema invalid: {raw!r}")
    return int(float(normalized))


def _post_kiwoom_with_auth_retry(url, headers, payload, api_id, *, timeout=5):
    """POST once, then refresh token and retry once only for Kiwoom auth/token failures."""
    active_headers = dict(headers or {})
    response = requests.post(url, headers=active_headers, json=payload, timeout=timeout)
    try:
        data = response.json()
    except Exception:
        return response, {}

    is_success = str(data.get("rt_cd", data.get("return_code", ""))) == "0"
    if response.status_code == 200 and is_success:
        return response, data
    if not is_auth_failure_error(data):
        return response, data

    api_label = str(api_id or active_headers.get("api-id") or "unknown")
    try:
        failed_token = (
            str(active_headers.get("authorization") or "")
            .replace("Bearer ", "")
            .strip()
        )
        refreshed_token = kiwoom_utils.get_kiwoom_token_after_auth_failure(
            api_id=api_label,
            failed_token=failed_token,
            reason_prefix="order_api_8005_retry",
        )
    except Exception as exc:
        log_error(
            f"❌ [{api_label}] 8005 감지 후 Kiwoom token force refresh 예외: {exc}"
        )
        return response, data
    if not refreshed_token:
        log_error(f"❌ [{api_label}] 8005 감지 후 Kiwoom token force refresh 실패")
        return response, data

    retry_headers = dict(active_headers)
    retry_headers["authorization"] = f"Bearer {refreshed_token}"
    log_info(
        f"🔐 [{api_label}] 8005 감지 후 Kiwoom token force refresh 성공 (주문/계좌 API 1회 retry)"
    )
    retry_response = requests.post(
        url, headers=retry_headers, json=payload, timeout=timeout
    )
    try:
        retry_data = retry_response.json()
    except Exception:
        return retry_response, {}
    return retry_response, retry_data


def calc_buy_qty(
    current_price,
    total_deposit,
    ratio=0.1,
    max_budget=None,
    allow_min_one_share_over_budget=False,
):
    """
    [v12.1] 예수금 대비 비중을 계산하여 정수 수량 산출
    """
    _, _, qty, _ = describe_buy_capacity(
        current_price,
        total_deposit,
        ratio,
        max_budget=max_budget,
        allow_min_one_share_over_budget=allow_min_one_share_over_budget,
    )
    return qty


def describe_buy_capacity(
    current_price,
    total_deposit,
    ratio=0.1,
    safety_ratio=None,
    max_budget=None,
    allow_min_one_share_over_budget=False,
):
    """
    주문가능금액과 전략 비중을 바탕으로 실제 주문 가능 예산/수량을 설명합니다.
    """
    if current_price <= 0 or total_deposit <= 0:
        return 0, 0, 0, 0.0

    if safety_ratio is None:
        safety_ratio = getattr(TRADING_RULES, "BUY_BUDGET_SAFETY_RATIO", 0.95)
    safe_ratio = max(0.0, min(float(safety_ratio), 1.0))
    target_budget = max(float(total_deposit) * float(ratio), 0.0)
    if max_budget is not None:
        try:
            budget_cap = max(float(max_budget), 0.0)
        except (TypeError, ValueError):
            budget_cap = 0.0
        if budget_cap > 0:
            target_budget = min(target_budget, budget_cap)
    safe_budget = target_budget * safe_ratio  # 슬리피지 대비 95% 사용

    qty = int(safe_budget // current_price)
    used_ratio = safe_ratio

    if qty <= 0 and target_budget >= float(current_price):
        relaxed_ratio = max(
            safe_ratio,
            min(
                float(
                    getattr(TRADING_RULES, "BUY_BUDGET_RELAXED_SAFETY_RATIO", 1.0)
                    or 1.0
                ),
                1.0,
            ),
        )
        relaxed_budget = target_budget * relaxed_ratio
        relaxed_qty = int(relaxed_budget // current_price)
        if relaxed_qty > 0:
            safe_budget = relaxed_budget
            qty = relaxed_qty
            used_ratio = relaxed_ratio

    if (
        qty <= 0
        and allow_min_one_share_over_budget
        and float(total_deposit) >= float(current_price)
    ):
        qty = 1

    return int(target_budget), int(safe_budget), qty, float(used_ratio)


def _get_virtual_orderable_amount():
    """설정된 가상 주문가능금액이 있으면 반환합니다."""
    conf = getattr(sniper_config, "CONF", {}) or {}
    for key in ("VIRTUAL_ORDERABLE_AMOUNT", "FIXED_ORDERABLE_AMOUNT"):
        raw_value = conf.get(key, 0)
        try:
            amount = int(float(raw_value or 0))
        except (TypeError, ValueError):
            amount = 0
        if amount > 0:
            return amount, key
    return 0, None


def _log_virtual_orderable_amount_once(amount, key):
    global _LAST_DEPOSIT_OVERRIDE
    marker = (key, int(amount))
    if _LAST_DEPOSIT_OVERRIDE == marker:
        return
    log_info(f"💰 [주문가능금액] 가상 주문가능금액 사용 " f"({key}={int(amount):,}원)")
    _LAST_DEPOSIT_OVERRIDE = marker


def _loop_cache_enabled():
    raw_value = getattr(TRADING_RULES, "DEPOSIT_LOOP_CACHE_ENABLED", True)
    if isinstance(raw_value, str):
        return raw_value.strip().lower() not in {"0", "false", "no", "off", ""}
    return bool(raw_value)


def _loop_cache_ttl_sec():
    return max(
        float(getattr(TRADING_RULES, "DEPOSIT_LOOP_CACHE_TTL_SEC", 1.0) or 0.0), 0.0
    )


def _deposit_cache_key(token):
    raw_token = str(token or "").strip()
    if raw_token:
        return f"token:{raw_token}"
    return "orderable_amount"


def _get_deposit_fetch_lock(cache_key):
    with _ORDERABLE_AMOUNT_CACHE_LOCK:
        lock = _DEPOSIT_API_FETCH_LOCKS.get(cache_key)
        if lock is None:
            lock = threading.RLock()
            _DEPOSIT_API_FETCH_LOCKS[cache_key] = lock
        return lock


def _get_loop_cached_deposit(cache_key, now_ts=None):
    if not _loop_cache_enabled():
        return 0, 0.0
    ttl_sec = _loop_cache_ttl_sec()
    if ttl_sec <= 0:
        return 0, 0.0
    if now_ts is None:
        now_ts = time.time()
    with _ORDERABLE_AMOUNT_CACHE_LOCK:
        record = dict(_ORDERABLE_AMOUNT_CACHE.get(cache_key) or {})
        amount = int(record.get("amount") or 0)
        updated_at = float(record.get("updated_at") or 0.0)
    if amount <= 0 or updated_at <= 0:
        return 0, 0.0
    age = float(now_ts) - updated_at
    if age < 0 or age > ttl_sec:
        return 0, age
    return amount, age


def _store_loop_cached_deposit(amount, *, cache_key, source="api_fresh", now_ts=None):
    if not _loop_cache_enabled():
        return
    try:
        normalized = int(float(amount or 0))
    except (TypeError, ValueError):
        normalized = 0
    if normalized <= 0:
        return
    if now_ts is None:
        now_ts = time.time()
    with _ORDERABLE_AMOUNT_CACHE_LOCK:
        _ORDERABLE_AMOUNT_CACHE[cache_key] = {
            "amount": normalized,
            "updated_at": float(now_ts),
            "source": str(source or "api_fresh"),
        }


def _remember_successful_deposit(amount, *, cache_key=None, loop_cache_source=None):
    global _LAST_SUCCESSFUL_DEPOSIT, _LAST_SUCCESSFUL_DEPOSIT_AT
    global _DEPOSIT_API_COOLDOWN_UNTIL, _DEPOSIT_API_COOLDOWN_REASON
    try:
        normalized = int(float(amount or 0))
    except (TypeError, ValueError):
        normalized = 0
    if normalized <= 0:
        return
    _LAST_SUCCESSFUL_DEPOSIT = normalized
    _LAST_SUCCESSFUL_DEPOSIT_AT = time.time()
    if cache_key:
        _LAST_SUCCESSFUL_DEPOSIT_BY_KEY[cache_key] = {
            "amount": normalized,
            "updated_at": _LAST_SUCCESSFUL_DEPOSIT_AT,
        }
    _DEPOSIT_API_COOLDOWN_UNTIL = 0.0
    _DEPOSIT_API_COOLDOWN_REASON = ""
    if loop_cache_source:
        _store_loop_cached_deposit(
            normalized,
            cache_key=cache_key or "orderable_amount",
            source=loop_cache_source,
            now_ts=_LAST_SUCCESSFUL_DEPOSIT_AT,
        )


def get_cached_deposit(max_age_sec=None, cache_key=None):
    """최근 정상 주문가능금액이 충분히 최신이면 fallback 값으로 반환합니다."""
    if max_age_sec is None:
        max_age_sec = int(
            getattr(TRADING_RULES, "DEPOSIT_CACHE_FALLBACK_TTL_SEC", 30) or 30
        )
    if cache_key:
        record = dict(_LAST_SUCCESSFUL_DEPOSIT_BY_KEY.get(cache_key) or {})
        amount = int(record.get("amount") or 0)
        updated_at = float(record.get("updated_at") or 0.0)
        if amount <= 0 or max_age_sec <= 0:
            return 0
        age = time.time() - updated_at
        if age > float(max_age_sec):
            return 0
        return amount
    if _LAST_SUCCESSFUL_DEPOSIT <= 0 or max_age_sec <= 0:
        return 0
    age = time.time() - float(_LAST_SUCCESSFUL_DEPOSIT_AT or 0.0)
    if age > float(max_age_sec):
        return 0
    return int(_LAST_SUCCESSFUL_DEPOSIT)


def _cached_deposit_age_sec(cache_key=None):
    if cache_key:
        record = dict(_LAST_SUCCESSFUL_DEPOSIT_BY_KEY.get(cache_key) or {})
        updated_at = float(record.get("updated_at") or 0.0)
        if updated_at > 0:
            return time.time() - updated_at
    return time.time() - float(_LAST_SUCCESSFUL_DEPOSIT_AT or 0.0)


def get_deposit(token):
    """
    [kt00001] 예수금 조회 - return_code 대응 수정
    """
    _LAST_DEPOSIT_ERRORS.clear()
    virtual_amount, config_key = _get_virtual_orderable_amount()
    if virtual_amount > 0:
        _log_virtual_orderable_amount_once(virtual_amount, config_key)
        _remember_successful_deposit(virtual_amount)
        _set_last_deposit_meta("virtual_override", amount=virtual_amount)
        return virtual_amount

    cache_key = _deposit_cache_key(token)
    with _get_deposit_fetch_lock(cache_key):
        return _get_deposit_real(token, cache_key)


def _get_deposit_real(token, cache_key):
    global _DEPOSIT_API_COOLDOWN_UNTIL, _DEPOSIT_API_COOLDOWN_REASON
    _LAST_DEPOSIT_ERRORS.clear()

    now_ts = time.time()
    loop_cached_amount, loop_cached_age = _get_loop_cached_deposit(
        cache_key, now_ts=now_ts
    )
    if loop_cached_amount > 0:
        return _apply_kt00001_orderable_amount_floor(
            loop_cached_amount,
            source="loop_cache",
            age_sec=loop_cached_age,
            cache_hit=True,
        )

    if _DEPOSIT_API_COOLDOWN_UNTIL > now_ts:
        cooldown_remaining = _DEPOSIT_API_COOLDOWN_UNTIL - now_ts
        cached_amount = get_cached_deposit(cache_key=cache_key)
        cooldown_classification = (
            "deposit_transport_cooldown"
            if str(_DEPOSIT_API_COOLDOWN_REASON or "").startswith("kt00001 transport")
            else "request_count_exceeded_cooldown"
        )
        cooldown_code = (
            "2000"
            if cooldown_classification == "deposit_transport_cooldown"
            else "1700"
        )
        _LAST_DEPOSIT_ERRORS.append(
            {
                "http_status": None,
                "return_code": cooldown_code,
                "return_msg": _DEPOSIT_API_COOLDOWN_REASON
                or "kt00001 request-limit cooldown active",
                "attempt": 0,
                "classification": cooldown_classification,
                "cooldown_remaining_sec": round(cooldown_remaining, 1),
                "cache_fallback_used": bool(cached_amount > 0),
            }
        )
        if cached_amount > 0:
            cached_age = _cached_deposit_age_sec(cache_key)
            _store_loop_cached_deposit(
                cached_amount,
                cache_key=cache_key,
                source="cooldown_fallback",
                now_ts=now_ts,
            )
            log_info(
                f"⚠️ [예수금조회 cooldown fallback] 최근 정상 주문가능금액 사용 "
                f"({cached_amount:,}원, cooldown_remaining={cooldown_remaining:.1f}s)"
            )
            return _apply_kt00001_orderable_amount_floor(
                cached_amount,
                source="cooldown_fallback",
                age_sec=cached_age,
                fallback_used=True,
            )
        _set_last_deposit_meta("fail_closed_zero", amount=0)
        log_error(
            f"❌ [예수금조회 cooldown] {_DEPOSIT_API_COOLDOWN_REASON or 'kt00001 cooldown active'} "
            f"(remaining={cooldown_remaining:.1f}s) - 주문가능금액 0 fail-closed"
        )
        return 0

    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "cont-yn": "N",
        "next-key": "",
        "api-id": "kt00001",
    }
    payload = {"qry_tp": "3"}
    retries = max(int(getattr(TRADING_RULES, "DEPOSIT_API_RETRY_COUNT", 2) or 2), 1)
    retry_delay = max(
        float(getattr(TRADING_RULES, "DEPOSIT_API_RETRY_DELAY_SEC", 0.15) or 0.15), 0.0
    )

    for attempt in range(1, retries + 1):
        try:
            res, data = _post_kiwoom_with_auth_retry(
                url, headers, payload, "kt00001", timeout=5
            )
            is_success = str(data.get("rt_cd", data.get("return_code", ""))) == "0"
            if res.status_code == 200 and is_success:
                try:
                    amount = _parse_kiwoom_amount(
                        data.get("ord_alow_amt", 0), field_name="ord_alow_amt"
                    )
                except ValueError as exc:
                    _LAST_DEPOSIT_ERRORS.append(
                        {
                            "http_status": res.status_code,
                            "return_code": data.get(
                                "return_code", data.get("rt_cd", "")
                            ),
                            "return_msg": str(exc),
                            "attempt": attempt,
                            "classification": "deposit_response_schema_invalid",
                            "field_name": "ord_alow_amt",
                        }
                    )
                    log_error(
                        f"❌ [예수금조회 응답스키마] attempt={attempt}/{retries} 사유: {exc}"
                    )
                    break
                if amount > 0:
                    _remember_successful_deposit(
                        amount, cache_key=cache_key, loop_cache_source="api_fresh"
                    )
                return _apply_kt00001_orderable_amount_floor(
                    amount,
                    source="api_fresh",
                )

            err_msg = data.get("return_msg") or data.get("err_msg") or "상세 사유 없음"
            _LAST_DEPOSIT_ERRORS.append(
                {
                    "http_status": res.status_code,
                    "return_code": data.get("return_code", data.get("rt_cd", "")),
                    "return_msg": err_msg,
                    "attempt": attempt,
                }
            )
            if is_request_limit_error(_LAST_DEPOSIT_ERRORS[-1]):
                cooldown_sec = max(
                    float(
                        getattr(
                            TRADING_RULES,
                            "DEPOSIT_API_REQUEST_LIMIT_COOLDOWN_SEC",
                            10.0,
                        )
                        or 10.0
                    ),
                    0.0,
                )
                if cooldown_sec > 0:
                    _DEPOSIT_API_COOLDOWN_UNTIL = max(
                        _DEPOSIT_API_COOLDOWN_UNTIL, time.time() + cooldown_sec
                    )
                    _DEPOSIT_API_COOLDOWN_REASON = str(
                        err_msg or "kt00001 request count exceeded"
                    )
                _LAST_DEPOSIT_ERRORS[-1]["classification"] = "request_count_exceeded"
                _LAST_DEPOSIT_ERRORS[-1]["cooldown_sec"] = cooldown_sec
                log_error(
                    f"❌ [예수금조회 요청제한] attempt={attempt}/{retries} 사유: {err_msg}"
                )
                break
            if is_deposit_transport_error(_LAST_DEPOSIT_ERRORS[-1]):
                cooldown_sec = max(
                    float(
                        getattr(
                            TRADING_RULES, "DEPOSIT_API_TRANSPORT_COOLDOWN_SEC", 5.0
                        )
                        or 5.0
                    ),
                    0.0,
                )
                cached_amount = get_cached_deposit(cache_key=cache_key)
                if cooldown_sec > 0:
                    _DEPOSIT_API_COOLDOWN_UNTIL = max(
                        _DEPOSIT_API_COOLDOWN_UNTIL, time.time() + cooldown_sec
                    )
                    _DEPOSIT_API_COOLDOWN_REASON = (
                        "kt00001 transport sendReceive failure"
                    )
                _LAST_DEPOSIT_ERRORS[-1]["classification"] = "deposit_transport_failure"
                _LAST_DEPOSIT_ERRORS[-1]["cooldown_sec"] = cooldown_sec
                _LAST_DEPOSIT_ERRORS[-1]["cache_fallback_available"] = bool(
                    cached_amount > 0
                )
                if cached_amount > 0:
                    log_info(
                        f"⚠️ [예수금조회 transport fallback] attempt={attempt}/{retries} "
                        f"최근 정상 주문가능금액 사용 예정 ({cached_amount:,}원) 사유: {err_msg}"
                    )
                else:
                    log_error(
                        f"❌ [예수금조회 transport] attempt={attempt}/{retries} 사유: {err_msg}"
                    )
                break
            log_error(
                f"❌ [예수금조회 실패] attempt={attempt}/{retries} 사유: {err_msg}"
            )
        except Exception as exc:
            _LAST_DEPOSIT_ERRORS.append(
                {
                    "http_status": None,
                    "return_code": None,
                    "return_msg": str(exc),
                    "attempt": attempt,
                }
            )
            log_error(f"❌ [예수금조회 예외] attempt={attempt}/{retries} 사유: {exc}")

        if attempt < retries and retry_delay > 0:
            time.sleep(retry_delay)

    cached_amount = get_cached_deposit(cache_key=cache_key)
    if cached_amount > 0:
        cached_age = _cached_deposit_age_sec(cache_key)
        log_info(
            f"⚠️ [예수금조회 fallback] 최근 정상 주문가능금액 사용 "
            f"({cached_amount:,}원, age={cached_age:.1f}s)"
        )
        return _apply_kt00001_orderable_amount_floor(
            cached_amount,
            source="stale_cache_fallback",
            age_sec=cached_age,
            fallback_used=True,
        )
    _set_last_deposit_meta("fail_closed_zero", amount=0)
    return 0


def get_my_inventory(token):
    """
    [kt00018] 계좌평가잔고내역을 조회합니다.
    SOR 주문을 고려하여 KRX(한국거래소) 잔고를 우선 반영하고,
    NXT(넥스트트레이드) 잔고 중복 종목은 무시하여 리스트를 구성합니다.
    """
    url = kiwoom_utils.get_api_url("/api/dostk/acnt")
    token_preview = f"{str(token)[:6]}...{str(token)[-6:]}" if token else "None"
    log_info(f"🔎 [잔고조회] url={url}, token={token_preview}")
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "cont-yn": "N",
        "next-key": "",
        "api-id": "kt00018",
    }

    # 💡 [핵심] 종목 코드를 키(Key)로 사용하여 중복을 제거할 딕셔너리
    aggregated_inventory = {}
    successful_exchanges = set()
    exchanges = ["KRX", "NXT"]
    _LAST_INVENTORY_ERRORS.clear()

    for exchange in exchanges:
        params = {"qry_tp": "2", "dmst_stex_tp": exchange}

        try:
            response, data = _post_kiwoom_with_auth_retry(
                url, headers, params, "kt00018", timeout=5
            )

            if str(data.get("return_code", data.get("rt_cd", ""))) == "0":
                successful_exchanges.add(exchange)
                stock_list = data.get("acnt_evlt_remn_indv_tot", [])

                for item in stock_list:
                    raw_code = item.get("stk_cd", "")
                    code = raw_code[1:] if raw_code.startswith("A") else raw_code
                    qty = int(item.get("rmnd_qty", 0))
                    name = item.get("stk_nm", "")

                    if qty > 0:
                        # 💡 [수정됨] KRX 데이터가 먼저 들어가고, NXT 조회 시 이미 딕셔너리에 있는 종목이면 무시(방어)합니다.
                        if code not in aggregated_inventory:
                            aggregated_inventory[code] = {
                                "code": code,
                                "name": name,
                                "qty": qty,
                            }
            else:
                err_code = data.get("return_code", data.get("rt_cd", ""))
                err_msg = (
                    data.get("return_msg") or data.get("err_msg") or "알 수 없는 오류"
                )
                log_info(f"⚠️ [API 경고] {exchange} 잔고 조회 실패: {err_msg}")
                _LAST_INVENTORY_ERRORS.append(
                    {
                        "exchange": exchange,
                        "http_status": response.status_code,
                        "return_code": err_code,
                        "return_msg": err_msg,
                    }
                )

        except Exception as e:
            log_error(f"❌ [API 에러] {exchange} 잔고 통신 실패: {e}")
            _LAST_INVENTORY_ERRORS.append(
                {
                    "exchange": exchange,
                    "http_status": None,
                    "return_code": None,
                    "return_msg": str(e),
                }
            )

    return list(aggregated_inventory.values()), successful_exchanges


# ==========================================
# 2. 주문 실행 API
# ==========================================
def _is_nxt_market_order_type(order_type) -> bool:
    return str(order_type or "").strip().upper() in {"3", "MARKET"}


def _nxt_market_order_remap_required(
    order_type, dmst_stex_tp=None, *, now=None
) -> bool:
    if not _is_nxt_market_order_type(order_type):
        return False
    return str(dmst_stex_tp or "").strip().upper() == "NXT"


def _resolve_buy_order_type(
    order_type,
    price=0,
    tif=None,
    dmst_stex_tp=None,
    *,
    now=None,
    emit_log=True,
):
    """
    Normalize legacy buy order request into Kiwoom order code + price.

    Project convention:
    - DAY limit: `00`
    - Best/marketable IOC: `16`
    - Market: `3`
    - Best: `6`

    NOTE:
    - Kiwoom IOC BUY requests are normalized to best-IOC (`16`).
    - The incoming limit price is advisory only and is discarded in payload.
    """
    tif_value = str(tif or "DAY").upper()
    requested_type = str(order_type or "6").upper()
    requested_price = int(price or 0)
    if _nxt_market_order_remap_required(requested_type, dmst_stex_tp, now=now):
        if emit_log:
            log_info(
                "[NXT_MARKET_BUY_REMAP] NXT plain market buy is unsupported; "
                "using best-limit style buy order type 6"
            )
        return "6", 0
    if requested_type in {"3", "MARKET"} and _pre0830_sor_market_order_remap_required(
        requested_type, now=now
    ):
        if emit_log:
            log_info(
                "[PRE0830_BUY_MARKET_REMAP] SOR market buy is unavailable before 08:30; "
                "using best-limit style buy order type 6"
            )
        return "6", 0

    if tif_value == "IOC":
        if requested_type in {"00", "LIMIT", "6", "BEST", "16"}:
            if requested_price > 0 and emit_log:
                log_info(
                    f"[ENTRY_TIF_MAP] IOC buy request promoted to best-IOC(16); "
                    f"requested_limit_price={requested_price} is advisory only"
                )
            return "16", 0
        if requested_type in {"3", "MARKET"}:
            return "3", 0

    if requested_type in {"00", "LIMIT"}:
        return "00", requested_price
    if requested_type in {"3", "MARKET"}:
        return "3", 0
    if requested_type in {"16", "BEST_IOC"}:
        return "16", 0
    return str(order_type), requested_price


def describe_buy_order_resolution(
    order_type,
    price=0,
    tif=None,
    dmst_stex_tp=None,
    *,
    now=None,
    emit_log=False,
):
    """Return requested/effective order metadata without submitting an order."""
    route_resolution = describe_order_route_resolution(dmst_stex_tp, now=now)
    resolved_exchange = route_resolution["effective_dmst_stex_tp"]
    effective_type, effective_price = _resolve_buy_order_type(
        order_type,
        price=price,
        tif=tif,
        dmst_stex_tp=resolved_exchange,
        now=now,
        emit_log=emit_log,
    )
    requested_type = str(order_type or "6").strip().upper()
    requested_price = int(price or 0)
    remapped = bool(
        str(effective_type) != requested_type
        or int(effective_price or 0) != requested_price
    )
    remap_reason = "none"
    if _nxt_market_order_remap_required(requested_type, resolved_exchange, now=now):
        remap_reason = "nxt_market_to_best_limit"
    elif requested_type in {"3", "MARKET"} and _pre0830_sor_market_order_remap_required(
        requested_type, now=now
    ):
        remap_reason = "pre0830_market_to_best_limit"
    elif str(tif or "DAY").upper() == "IOC" and str(effective_type) == "16":
        remap_reason = "ioc_to_best_ioc"
    return {
        **route_resolution,
        "requested_order_type": requested_type,
        "requested_order_price": requested_price,
        "effective_order_type": str(effective_type),
        "effective_order_price": int(effective_price or 0),
        "order_type_remapped": remapped,
        "order_type_remap_reason": remap_reason,
    }


def _pre0830_sor_market_order_remap_required(order_type, now=None) -> bool:
    if str(order_type) != "3":
        return False
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current_kst = current.astimezone(KST)
    return current_kst.time() < datetime_time(hour=8, minute=30)


def _pre0830_sor_market_sell_remap_required(order_type, now=None) -> bool:
    return _pre0830_sor_market_order_remap_required(order_type, now=now)


def _resolve_sell_order_type(order_type, price=0, dmst_stex_tp=None, *, now=None):
    normalized_type = str(order_type)
    normalized_price = int(price or 0)
    resolved_exchange = resolve_order_dmst_stex_tp(dmst_stex_tp, now=now)
    if _nxt_market_order_remap_required(normalized_type, resolved_exchange, now=now):
        log_info(
            "[NXT_MARKET_SELL_REMAP] NXT plain market sell is unsupported; "
            "using best-limit style sell order type 6"
        )
        return "6", 0
    if _pre0830_sor_market_sell_remap_required(normalized_type, now=now):
        log_info(
            "[PRE0830_SELL_MARKET_REMAP] SOR market sell is unavailable before 08:30; "
            "using best-limit style sell order type 6"
        )
        return "6", 0
    return normalized_type, normalized_price


def _is_sor_market_time_reject(data) -> bool:
    msg = str(data.get("return_msg") or data.get("err_msg") or "")
    code = str(data.get("return_code") or data.get("rt_cd") or "")
    return (
        "571034" in code
        or "571034" in msg
        or "SOR 시장가 주문은 08:30 이후" in msg
        or "407022" in msg
        or "주문이 불가능한 주문종류" in msg
    )


def _is_sor_market_sell_time_reject(data) -> bool:
    return _is_sor_market_time_reject(data)


def _buy_time_block_cutoff():
    raw_cutoff = str(
        getattr(TRADING_RULES, "BUY_SIDE_TIME_BLOCK_UNTIL_HHMM", "09:10") or ""
    ).strip()
    try:
        hour_text, minute_text = raw_cutoff.split(":", 1)
        return datetime_time(hour=int(hour_text), minute=int(minute_text))
    except Exception:
        return datetime_time(hour=9, minute=10)


def _parse_hhmmss_time(raw_value):
    raw_text = str(raw_value or "").strip()
    parts = raw_text.split(":")
    try:
        if len(parts) == 2:
            hour_text, minute_text = parts
            second_text = "0"
        elif len(parts) == 3:
            hour_text, minute_text, second_text = parts
        else:
            return None
        return datetime_time(
            hour=int(hour_text),
            minute=int(minute_text),
            second=int(second_text),
        )
    except Exception:
        return None


def _scalping_buy_windows():
    raw_windows = str(getattr(TRADING_RULES, "SCALPING_BUY_WINDOWS", "") or "").strip()
    return _parse_time_windows(raw_windows)


def _sell_windows():
    raw_windows = str(
        getattr(TRADING_RULES, "SELL_WINDOWS", "")
        or getattr(TRADING_RULES, "SCALPING_SELL_WINDOWS", "")
        or ""
    ).strip()
    return _parse_time_windows(raw_windows)


def _parse_time_windows(raw_windows):
    windows = []
    for token in raw_windows.split(","):
        token = token.strip()
        if not token or "-" not in token:
            continue
        start_raw, end_raw = token.split("-", 1)
        start = _parse_hhmmss_time(start_raw)
        end = _parse_hhmmss_time(end_raw)
        if start is None or end is None:
            continue
        windows.append((start, end))
    return tuple(windows)


def _time_in_window(now_t, start, end) -> bool:
    if start <= end:
        return start <= now_t <= end
    return now_t >= start or now_t <= end


def _coerce_kst_time(now=None):
    current = now or datetime.now(KST)
    if isinstance(current, datetime_time):
        return current
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    return current.astimezone(KST).time()


def is_krx_regular_order_session(now=None) -> bool:
    current_time = _coerce_kst_time(now)
    return KRX_REGULAR_OPEN <= current_time < KRX_REGULAR_CLOSE


def resolve_order_dmst_stex_tp(dmst_stex_tp=None, *, now=None) -> str:
    explicit = str(dmst_stex_tp or "").strip().upper()
    if explicit in {"KRX", "NXT", "SOR"}:
        return explicit
    return "SOR" if is_krx_regular_order_session(now) else "NXT"


def describe_order_route_resolution(dmst_stex_tp=None, *, now=None) -> dict:
    """Describe the broker route independently from the venue cohort.

    ``dmst_stex_tp`` is the Kiwoom execution route.  It must never be reused as
    an effective venue/cohort label: KRX regular-session orders use SOR, while
    premarket and NXT-session orders default to NXT.
    """

    explicit = str(dmst_stex_tp or "").strip().upper()
    effective = (
        resolve_order_dmst_stex_tp(dmst_stex_tp)
        if now is None
        else resolve_order_dmst_stex_tp(dmst_stex_tp, now=now)
    )
    if explicit in {"KRX", "NXT", "SOR"}:
        resolution = "explicit_request"
        requested = explicit
    elif effective == "SOR":
        resolution = "krx_regular_session_default_sor"
        requested = "AUTO"
    else:
        resolution = "outside_krx_regular_session_default_nxt"
        requested = "AUTO"
    return {
        "requested_dmst_stex_tp": requested,
        "effective_dmst_stex_tp": effective,
        "broker_route": effective,
        "broker_route_resolution": resolution,
    }


def _with_order_route_provenance(
    data,
    *,
    route_resolution: dict,
    broker_route_attempted: bool,
):
    if not isinstance(data, dict):
        return data
    enriched = dict(data)
    enriched.update(route_resolution)
    enriched["broker_route_attempted"] = bool(broker_route_attempted)
    return enriched


def _inside_scalping_buy_window(now_t) -> bool:
    return any(
        _time_in_window(now_t, start, end) for start, end in _scalping_buy_windows()
    )


def _inside_sell_window(now_t) -> bool:
    return any(_time_in_window(now_t, start, end) for start, end in _sell_windows())


def is_scalping_buy_window_blocked(now=None) -> bool:
    if not bool(getattr(TRADING_RULES, "BUY_SIDE_TIME_BLOCK_ENABLED", True)):
        return False
    if not _scalping_buy_windows():
        return False
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current_kst = current.astimezone(KST)
    return not _inside_scalping_buy_window(current_kst.time())


def is_buy_side_time_blocked(now=None) -> bool:
    if not bool(getattr(TRADING_RULES, "BUY_SIDE_TIME_BLOCK_ENABLED", True)):
        return False
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current_kst = current.astimezone(KST)
    current_time = current_kst.time()
    if is_scalping_buy_window_blocked(current_kst):
        return True
    if current_time < _buy_time_block_cutoff() and _inside_scalping_buy_window(
        current_time
    ):
        return False
    return current_time < _buy_time_block_cutoff()


def get_buy_side_time_block_label() -> str:
    cutoff = _buy_time_block_cutoff()
    buy_windows = _scalping_buy_windows()
    if buy_windows:
        windows_text = ",".join(
            f"{start.strftime('%H:%M:%S')}-{end.strftime('%H:%M:%S')}"
            for start, end in buy_windows
        )
        return (
            "real BUY 허용 시간창 밖 차단 또는 신규 매수 및 추가매수 시간 차단 "
            f"(KST {cutoff.strftime('%H:%M')} 전, BUY windows {windows_text})"
        )
    return "신규 매수 및 추가매수 시간 차단 " f"(KST {cutoff.strftime('%H:%M')} 전)"


def _sell_side_open_time_block_cutoff():
    raw_cutoff = str(
        getattr(TRADING_RULES, "SELL_SIDE_OPEN_TIME_BLOCK_UNTIL_HHMM", "") or ""
    ).strip()
    try:
        hour_text, minute_text = raw_cutoff.split(":", 1)
        return datetime_time(hour=int(hour_text), minute=int(minute_text))
    except Exception:
        return None


def _sell_side_open_time_scope() -> str:
    return str(
        getattr(TRADING_RULES, "SELL_SIDE_OPEN_TIME_BLOCK_SCOPE", "") or ""
    ).strip()


def _sell_side_scope_applies_to_all() -> bool:
    return _sell_side_open_time_scope().lower() in {
        "all",
        "all_exit",
        "all_sells",
        "all_sell",
    }


def _sell_side_open_time_strategy_allowed(strategy=None) -> bool:
    if _sell_side_scope_applies_to_all():
        return True
    strategy_key = str(strategy or "").strip().upper()
    return strategy_key in {"SCALPING", "SCALP"}


def sell_side_open_time_passthrough_reason(reason_type=None) -> str:
    if _sell_side_scope_applies_to_all():
        return ""
    reason_key = str(reason_type or "").strip().upper()
    if not reason_key:
        return "scope_unknown_passthrough"
    safety_markers = (
        "LOSS",
        "CLOSE",
        "HARD",
        "STOP",
        "EMERGENCY",
        "PROTECT",
        "PANIC",
        "LIQUIDITY",
        "BROKEN",
        "OVERNIGHT",
        "SAFETY",
    )
    if any(marker in reason_key for marker in safety_markers):
        return f"safety_reason_{reason_key.lower()}"
    return ""


def is_sell_side_open_time_blocked(now=None, reason_type=None, strategy=None) -> bool:
    if not bool(getattr(TRADING_RULES, "SELL_SIDE_OPEN_TIME_BLOCK_ENABLED", False)):
        return False
    if not _sell_side_open_time_strategy_allowed(strategy):
        return False
    if sell_side_open_time_passthrough_reason(reason_type):
        return False
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current_kst = current.astimezone(KST)
    current_time = current_kst.time()
    if _sell_windows():
        return not _inside_sell_window(current_time)
    cutoff = _sell_side_open_time_block_cutoff()
    if cutoff is None:
        return False
    return current_kst.time() < cutoff


def get_sell_side_open_time_block_label() -> str:
    cutoff = _sell_side_open_time_block_cutoff()
    sell_windows = _sell_windows()
    if sell_windows:
        windows_text = ",".join(
            f"{start.strftime('%H:%M:%S')}-{end.strftime('%H:%M:%S')}"
            for start, end in sell_windows
        )
        return f"real SELL 허용 시간창 밖 차단 (KST {windows_text})"
    if cutoff is None:
        return "real SELL 시간 차단 설정 없음"
    return (
        "real SCALPING 장초반 discretionary 매도 시간 차단 "
        f"(KST {cutoff.strftime('%H:%M')} 전)"
    )


def get_sell_side_open_time_block_fields(
    now=None, reason_type=None, strategy=None
) -> dict:
    cutoff = _sell_side_open_time_block_cutoff()
    passthrough_reason = sell_side_open_time_passthrough_reason(reason_type)
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    current_kst = current.astimezone(KST)
    enabled = bool(getattr(TRADING_RULES, "SELL_SIDE_OPEN_TIME_BLOCK_ENABLED", False))
    strategy_allowed = _sell_side_open_time_strategy_allowed(strategy)
    current_time = current_kst.time()
    sell_windows = _sell_windows()
    inside_sell_window = _inside_sell_window(current_time) if sell_windows else True
    before_cutoff = current_time < cutoff if cutoff is not None else False
    blocked_by_time = not inside_sell_window if sell_windows else before_cutoff
    applied = bool(
        enabled and strategy_allowed and not passthrough_reason and blocked_by_time
    )
    return {
        "runtime_family": "sell_side_open_time_block_runtime",
        "policy_version": "sell_side_open_time_block_v1",
        "sell_time_block_enabled": enabled,
        "sell_time_block_until_hhmm": (
            cutoff.strftime("%H:%M") if cutoff is not None else ""
        ),
        "sell_time_block_scope": _sell_side_open_time_scope(),
        "sell_windows": ",".join(
            f"{start.strftime('%H:%M:%S')}-{end.strftime('%H:%M:%S')}"
            for start, end in sell_windows
        ),
        "sell_time_block_inside_sell_window": inside_sell_window,
        "sell_reason_type": str(reason_type or ""),
        "sell_time_block_checked": True,
        "sell_time_block_strategy": str(strategy or ""),
        "sell_time_block_strategy_allowed": strategy_allowed,
        "sell_time_block_before_cutoff": before_cutoff,
        "sell_time_block_applied": applied,
        "sell_time_block_passthrough_reason": passthrough_reason or "-",
    }


def send_buy_order_market(
    code,
    qty,
    token,
    order_type="6",
    price=0,
    tif=None,
    allow_time_block_override=False,
    time_block_override_reason=None,
    dmst_stex_tp=None,
):
    """
    [kt10000] 매수 주문 - return_code 대응 수정 및 지정가(00) 기능 추가
    - order_type: "00" (지정가 - 스캘핑 눌림목 그물망용)
                  "6"  (최유리지정가 - 기본값, 우량주 스윙용)
                  "3"  (시장가 - 강력한 추격 매수용)
    - price: 지정가 주문 시 입력할 1주당 단가 (시장가/최유리 지정가일 경우 0 또는 생략)
    """
    if qty <= 0:
        return None
    time_block_override_reason = str(time_block_override_reason or "").strip()
    allow_time_block_override = (
        bool(allow_time_block_override)
        and time_block_override_reason in _DEFENSIVE_BUY_TIME_BLOCK_OVERRIDE_REASONS
    )

    if is_buy_side_paused():
        clean_code = str(code)[:6]
        msg = f"[TRADING_PAUSED_BLOCK] buy order blocked 종목:{clean_code}, 상태:{get_pause_state_label()}"
        log_info(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return {
            "rt_cd": "PAUSED",
            "return_code": "PAUSED",
            "return_msg": get_pause_state_label(),
            "ord_no": "",
        }

    buy_window_blocked = is_scalping_buy_window_blocked()
    if buy_window_blocked:
        allow_time_block_override = False
    buy_time_blocked = is_buy_side_time_blocked()
    if buy_time_blocked and not allow_time_block_override:
        clean_code = str(code)[:6]
        label = get_buy_side_time_block_label()
        msg = f"[BUY_TIME_BLOCK] buy order blocked 종목:{clean_code}, 상태:{label}"
        log_info(msg)
        return {
            "rt_cd": "BUY_TIME_BLOCKED",
            "return_code": "BUY_TIME_BLOCKED",
            "return_msg": label,
            "ord_no": "",
        }
    if buy_time_blocked and allow_time_block_override:
        clean_code = str(code)[:6]
        log_info(
            f"[BUY_TIME_BLOCK_OVERRIDE] buy order time block bypassed 종목:{clean_code}, "
            f"reason={time_block_override_reason}"
        )

    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "cont-yn": "N",
        "next-key": "",
        "api-id": "kt10000",
    }

    order_resolution = describe_buy_order_resolution(
        order_type,
        price=price,
        tif=tif,
        dmst_stex_tp=dmst_stex_tp,
        emit_log=True,
    )
    resolved_dmst_stex_tp = order_resolution["effective_dmst_stex_tp"]
    normalized_type = order_resolution["effective_order_type"]
    normalized_price = order_resolution["effective_order_price"]
    ord_price_str = (
        str(int(normalized_price))
        if str(normalized_type) == "00" and normalized_price > 0
        else ""
    )

    payload = {
        "dmst_stex_tp": resolved_dmst_stex_tp,
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(normalized_type),
        "cond_uv": "",
    }

    try:
        res, data = _post_kiwoom_with_auth_retry(
            url, headers, payload, "kt10000", timeout=5
        )

        is_success = (
            str(data.get("rt_cd", "")) == "0" or str(data.get("return_code", "")) == "0"
        )

        if res.status_code == 200 and is_success:
            return _with_order_route_provenance(
                data,
                route_resolution={
                    key: order_resolution[key]
                    for key in (
                        "requested_dmst_stex_tp",
                        "effective_dmst_stex_tp",
                        "broker_route",
                        "broker_route_resolution",
                    )
                },
                broker_route_attempted=True,
            )
        else:
            if str(payload.get("trde_tp")) == "3" and _is_sor_market_time_reject(data):
                retry_payload = dict(payload)
                retry_payload["trde_tp"] = "6"
                retry_payload["ord_uv"] = ""
                log_info(
                    f"[BUY_MARKET_RETRY_AS_BEST] {clean_code} SOR market buy rejected; "
                    "retrying with order type 6"
                )
                retry_res, retry_data = _post_kiwoom_with_auth_retry(
                    url, headers, retry_payload, "kt10000", timeout=5
                )
                retry_success = (
                    str(retry_data.get("rt_cd", "")) == "0"
                    or str(retry_data.get("return_code", "")) == "0"
                )
                if retry_res.status_code == 200 and retry_success:
                    return _with_order_route_provenance(
                        retry_data,
                        route_resolution={
                            key: order_resolution[key]
                            for key in (
                                "requested_dmst_stex_tp",
                                "effective_dmst_stex_tp",
                                "broker_route",
                                "broker_route_resolution",
                            )
                        },
                        broker_route_attempted=True,
                    )
                data = retry_data
            err_msg = data.get("return_msg") or data.get("err_msg") or "상세 사유 없음"
            err_code = data.get("return_code", data.get("rt_cd", ""))

            # 💡 [핵심] 에러 로깅 후 EventBus로 텔레그램 발송 (Decoupling)
            msg = f"❌ [매수거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return _with_order_route_provenance(
                data,
                route_resolution={
                    key: order_resolution[key]
                    for key in (
                        "requested_dmst_stex_tp",
                        "effective_dmst_stex_tp",
                        "broker_route",
                        "broker_route_resolution",
                    )
                },
                broker_route_attempted=True,
            )

    except Exception as e:
        msg = f"🔥 [매수주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None


# -------------------------------------------------------------------
# Compatibility wrapper (legacy callers)
# -------------------------------------------------------------------
def send_buy_order(
    code,
    qty,
    price,
    order_type_code,
    token,
    order_type_desc=None,
    tif=None,
    allow_time_block_override=False,
    time_block_override_reason=None,
    dmst_stex_tp=None,
):
    """
    Legacy wrapper for send_buy_order_market.
    - order_type_code: "00" 지정가, "6" 최유리지정가, "3" 시장가
    - price: 지정가일 때만 사용
    """
    return send_buy_order_market(
        code=code,
        qty=qty,
        token=token,
        order_type=str(order_type_code),
        price=price or 0,
        tif=tif,
        allow_time_block_override=allow_time_block_override,
        time_block_override_reason=time_block_override_reason,
        dmst_stex_tp=dmst_stex_tp,
    )


def send_sell_order_market(
    code,
    qty,
    token,
    order_type="3",
    price=0,
    *,
    reason_type=None,
    strategy=None,
    bypass_open_time_block=False,
    dmst_stex_tp=None,
):
    """
    [kt10001] 주식 매도 주문 (시장가/지정가/최유리지정가 통합 지원)
    """
    if qty <= 0:
        return None

    clean_code = str(code)[:6]
    if not bypass_open_time_block and is_sell_side_open_time_blocked(
        reason_type=reason_type,
        strategy=strategy,
    ):
        label = get_sell_side_open_time_block_label()
        fields = get_sell_side_open_time_block_fields(
            reason_type=reason_type,
            strategy=strategy,
        )
        log_info(
            f"[SELL_TIME_BLOCK] sell order blocked 종목:{clean_code}, 상태:{label}"
        )
        return {
            "rt_cd": "SELL_TIME_BLOCKED",
            "return_code": "SELL_TIME_BLOCKED",
            "return_msg": label,
            "ord_no": "",
            "sell_time_block_fields": fields,
        }

    url = kiwoom_utils.get_api_url("/api/dostk/ordr")
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "cont-yn": "N",
        "next-key": "",
        "api-id": "kt10001",
    }

    route_resolution = describe_order_route_resolution(dmst_stex_tp)
    resolved_dmst_stex_tp = route_resolution["effective_dmst_stex_tp"]
    normalized_type, normalized_price = _resolve_sell_order_type(
        order_type,
        price=price,
        dmst_stex_tp=resolved_dmst_stex_tp,
    )

    # 💡 [핵심] 지정가("00") 매도일 경우 단가를 호가단위로 정규화합니다.
    ord_price_str = ""
    if str(normalized_type) == "00" and normalized_price > 0:
        try:
            raw_price = int(normalized_price)
            tick = int(kiwoom_utils.get_tick_size(raw_price))
            normalized_price = (
                int((raw_price // tick) * tick) if tick > 0 else raw_price
            )
            if normalized_price <= 0:
                normalized_price = raw_price
            if normalized_price != raw_price:
                log_info(
                    f"[주문단가정규화] {clean_code} 지정가 매도 {raw_price} -> {normalized_price} (tick={tick})"
                )
            ord_price_str = str(normalized_price)
        except Exception:
            ord_price_str = str(int(price))

    payload = {
        "dmst_stex_tp": resolved_dmst_stex_tp,
        "stk_cd": clean_code,
        "ord_qty": str(qty),
        "ord_uv": ord_price_str,
        "trde_tp": str(normalized_type),
        "cond_uv": "",
    }

    try:
        res, data = _post_kiwoom_with_auth_retry(
            url, headers, payload, "kt10001", timeout=5
        )

        is_success = (
            str(data.get("rt_cd", "")) == "0" or str(data.get("return_code", "")) == "0"
        )

        if res.status_code == 200 and is_success:
            return _with_order_route_provenance(
                data,
                route_resolution=route_resolution,
                broker_route_attempted=True,
            )
        else:
            if str(payload.get("trde_tp")) == "3" and _is_sor_market_sell_time_reject(
                data
            ):
                retry_payload = dict(payload)
                retry_payload["trde_tp"] = "6"
                retry_payload["ord_uv"] = ""
                log_info(
                    f"[SELL_MARKET_RETRY_AS_BEST] {clean_code} SOR market sell rejected; "
                    "retrying with order type 6"
                )
                retry_res, retry_data = _post_kiwoom_with_auth_retry(
                    url, headers, retry_payload, "kt10001", timeout=5
                )
                retry_success = (
                    str(retry_data.get("rt_cd", "")) == "0"
                    or str(retry_data.get("return_code", "")) == "0"
                )
                if retry_res.status_code == 200 and retry_success:
                    return _with_order_route_provenance(
                        retry_data,
                        route_resolution=route_resolution,
                        broker_route_attempted=True,
                    )
                data = retry_data
            err_msg = data.get("return_msg") or data.get("err_msg") or "상세 사유 없음"
            err_code = data.get("return_code", data.get("rt_cd", ""))

            # 📢 EventBus를 통한 에러 브로드캐스트
            msg = f"❌ [매도거절] 종목:{clean_code}, 사유:{err_msg} (코드:{err_code})"
            if ("매도가능수량" in str(err_msg)) or (
                "잔고" in str(err_msg) and "부족" in str(err_msg)
            ):
                log_info(msg + " [비치명]")
                data["non_fatal_no_qty"] = True
            else:
                log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return _with_order_route_provenance(
                data,
                route_resolution=route_resolution,
                broker_route_attempted=True,
            )

    except Exception as e:
        msg = f"🔥 [매도주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None


def _normalize_dmst_stex_tp(value, *, default="SOR"):
    normalized = str(value or default or "SOR").strip().upper()
    if normalized in {"KRX", "NXT", "SOR"}:
        return normalized
    return str(default or "SOR").strip().upper() or "SOR"


def send_cancel_order(code, orig_ord_no, token, qty=0, dmst_stex_tp=None):
    """
    [kt10003] 주식 취소 주문 - 미체결 물량 취소
    :param qty: 취소 수량. 기본값 0 (0 입력 시 미체결 잔량 전부 취소)
    """
    clean_code = str(code)[:6]
    url = kiwoom_utils.get_api_url("/api/dostk/ordr")

    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "cont-yn": "N",
        "next-key": "",
        "api-id": "kt10003",  # 주식 취소 전용 TR 명시
    }

    explicit_cancel_route = str(dmst_stex_tp or "").strip().upper()
    if explicit_cancel_route in {"KRX", "NXT", "SOR"}:
        route_resolution = describe_order_route_resolution(explicit_cancel_route)
    else:
        # Preserve the legacy cancel fallback.  A cancellation must inherit the
        # original order route; missing provenance is surfaced rather than
        # silently changing the live cancel destination by current wall clock.
        route_resolution = {
            "requested_dmst_stex_tp": "AUTO",
            "effective_dmst_stex_tp": "SOR",
            "broker_route": "SOR",
            "broker_route_resolution": "legacy_cancel_default_sor_original_route_missing",
        }
    payload = {
        "dmst_stex_tp": route_resolution["effective_dmst_stex_tp"],  # 국내거래소구분
        "orig_ord_no": str(orig_ord_no),  # 원주문번호
        "stk_cd": clean_code,  # 종목코드
        "cncl_qty": str(qty),  # 🚀 '0'이면 남은 물량 싹 다 취소!
    }

    try:
        res, data = _post_kiwoom_with_auth_retry(
            url, headers, payload, "kt10003", timeout=5
        )

        if res.status_code == 200 and str(data.get("return_code", "")) == "0":
            cncl_qty_result = data.get("cncl_qty", "전량")
            new_ord_no = data.get("ord_no", "")
            print(
                f"✅ [취소접수] {clean_code} {cncl_qty_result}주 취소 성공 (새주문번호:{new_ord_no})"
            )
            return _with_order_route_provenance(
                data,
                route_resolution=route_resolution,
                broker_route_attempted=True,
            )
        else:
            err_msg = data.get("return_msg", "상세 사유 없음")
            msg = f"❌ [취소거절] {clean_code}: {err_msg}"
            log_error(msg)
            # EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
            return _with_order_route_provenance(
                data,
                route_resolution=route_resolution,
                broker_route_attempted=True,
            )

    except Exception as e:
        msg = f"🔥 [취소주문] 시스템 예외: {str(e)}"
        log_error(msg)
        EventBus().publish("TELEGRAM_ADMIN_NOTIFY", {"text": msg})
        return None


# ==========================================
# 3. 🚀 스마트 하이브리드 주문 (Sniper 엔진에서 호출)
# ==========================================
def send_smart_sell_order(
    code,
    qty,
    token,
    ws_data,
    reason_type,
    strategy=None,
    bypass_open_time_block=False,
    dmst_stex_tp=None,
):
    """
     [v14.0] 슬리피지 방어를 위한 스마트 매도 로직 (사유 기반 동적 시장가 전환)
    - LOSS, CLOSE: 긴급 탈출 -> 시장가(3)
    - MOMENTUM_DECAY, TRAILING, LIMIT_UP: 빠른 익절 보장 -> 최유리지정가(6)
    - 기타(PROFIT, TIMEOUT): 1호가 잔량 확인 후 지정가(00) 우선 시도
    """
    if qty <= 0:
        return None

    # 1. 매수 1호가 데이터 추출 (kiwoom_websocket '0D' 구조 반영)
    try:
        orderbook = ws_data.get("orderbook", {})
        bids = orderbook.get("bids", [])

        if not bids:
            print(f"⚠️ [{code}] 호가 데이터가 없어 시장가(3)로 전환합니다.")
            return send_sell_order_market(
                code,
                qty,
                token,
                order_type="3",
                reason_type=reason_type,
                strategy=strategy,
                bypass_open_time_block=bypass_open_time_block,
                dmst_stex_tp=dmst_stex_tp,
            )

        # 매수 1호가 정보 (bids[0] 이 가장 높은 매수 호가)
        bid_1_p = bids[0].get("price", 0)
        bid_1_q = bids[0].get("volume", 0)

    except (IndexError, KeyError, TypeError) as e:
        log_error(f"❌ [{code}] 호가 데이터 파싱 실패: {e}")
        return send_sell_order_market(
            code,
            qty,
            token,
            order_type="3",
            reason_type=reason_type,
            strategy=strategy,
            bypass_open_time_block=bypass_open_time_block,
            dmst_stex_tp=dmst_stex_tp,
        )

    # 2. 매매 성격(reason_type)에 따른 주문 분기
    # 🚨 긴급 탈출(LOSS, CLOSE) : 절대 지정가 쓰지 않음. 시장가(3) 즉시 던짐.
    if reason_type in ["LOSS", "CLOSE"]:
        print(
            f"🚨 [긴급매도] {code}: 시장가(3) 매도 (사유: {reason_type}, 수량: {qty})"
        )
        return send_sell_order_market(
            code,
            qty,
            token,
            order_type="3",
            reason_type=reason_type,
            strategy=strategy,
            bypass_open_time_block=bypass_open_time_block,
            dmst_stex_tp=dmst_stex_tp,
        )

    # 💰 익절(PROFIT): 슬리피지 방어 가동
    # ⚠️ 모멘텀 급감, 트레일링 스탑 (MOMENTUM_DECAY, TRAILING) : 최유리지정가(6)로 시장가에 가깝게 즉시 체결 유도
    elif reason_type in ["MOMENTUM_DECAY", "TRAILING", "LIMIT_UP"]:
        print(
            f"⚠️ [시장가성 매도] {code}: 최유리지정가(6) 매도 (사유: {reason_type}, 수량: {qty})"
        )
        return send_sell_order_market(
            code,
            qty,
            token,
            order_type="6",
            reason_type=reason_type,
            strategy=strategy,
            bypass_open_time_block=bypass_open_time_block,
            dmst_stex_tp=dmst_stex_tp,
        )

    # 💰 일반 익절, 타임아웃 (PROFIT, TIMEOUT) : 지정가(00) 우선 시도, 안 되면 최유리지정가(6) (8:2 비율 중 2의 영역)

    else:
        # 매수 1호가 잔량이 내 물량보다 넉넉한지 확인 (2배 여유)
        if bid_1_p > 0 and bid_1_q >= qty * 2.0:
            print(
                f"💰 [스마트익절] {code}: 1호가({bid_1_p:,}원) 지정가 매도 (사유: {reason_type}, 호가잔량: {bid_1_q}주)"
            )
            return send_sell_order_market(
                code,
                qty,
                token,
                order_type="00",
                price=bid_1_p,
                reason_type=reason_type,
                strategy=strategy,
                bypass_open_time_block=bypass_open_time_block,
                dmst_stex_tp=dmst_stex_tp,
            )

        else:
            # 1호가 잔량이 부족하면 '최유리지정가(6)'로 던져서 슬리피지 최소화
            print(f"⚠️ [슬리피지방어] {code}: 1호가 잔량 부족. 최유리지정가(6) 매도")
            return send_sell_order_market(
                code,
                qty,
                token,
                order_type="6",
                reason_type=reason_type,
                strategy=strategy,
                bypass_open_time_block=bypass_open_time_block,
                dmst_stex_tp=dmst_stex_tp,
            )


def reserve_buy_order_ai(code, ai_target_price, deposit, token, ratio=0.05):
    """
    [v12.9] AI 권장 타점을 바탕으로 지정가 매수 예약 주문을 전송합니다.
    """
    try:
        # 💡 [보완] 입력값이 비어있거나 'None'인 경우 즉시 탈출
        if not ai_target_price or str(ai_target_price).strip() == "":
            print(f"⚠️ [{code}] AI 예약가 데이터가 비어있습니다.")
            return None

        clean_price_str = re.sub(r"[^0-9]", "", str(ai_target_price))
        if not clean_price_str:  # 숫자가 하나도 없는 경우 방어
            return None

        clean_price = int(clean_price_str)

        # 2. 유틸리티를 사용하여 호가 규격에 맞게 내림 정규화
        # AI가 준 가격이 19,950원인데 호가 단위가 100원이면 19,900원으로 맞춥니다.
        final_target_price = kiwoom_utils.get_target_price_by_percent(
            clean_price, drop_percent=0
        )

        if final_target_price <= 0:
            print(f"⚠️ [{code}] 유효하지 않은 예약가입니다.")
            return None

        # 3. 매수 수량 계산
        buy_qty = calc_buy_qty(final_target_price, deposit, ratio)

        if buy_qty <= 0:
            print(f"⚠️ [{code}] 예수금 부족으로 예약 주문을 생성할 수 없습니다.")
            return None

        # 4. 지정가(00) 주문 전송
        print(
            f"🎯 [AI 예약] {code}: {final_target_price:,}원에 {buy_qty}주 낚싯바늘 투척"
        )
        return send_buy_order_market(
            code=code,
            qty=buy_qty,
            token=token,
            order_type="00",  # 지정가
            price=final_target_price,
        )

    except Exception as e:
        print(f"❌ [예약주문 실패] {code}: {str(e)}")
        return None
