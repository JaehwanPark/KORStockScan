"""Account/DB sync helpers for the sniper engine."""

import time
from datetime import date, datetime
from math import isclose
from pathlib import Path
import re

from src.database.models import HoldingAddHistory, RecommendationHistory
from src.engine.scalping.opening_rotation import (
    POSITION_TAG as OPENING_ROTATION_POSITION_TAG,
)
from src.engine.scalping.entry_split_order_plan import (
    recover_probe_runtime_bundle_for_stock,
)
from src.engine.sniper_position_tags import (
    normalize_position_tag,
    normalize_strategy,
    target_identity,
)
from src.engine.sniper_scale_in_utils import (
    record_add_history_event,
    find_latest_open_add_order_no,
)
from src.engine.trade_profit import (
    calculate_net_profit_rate,
    calculate_net_realized_pnl,
)
from src.engine.risk.manual_control_exclusion import (
    remove_manual_control_exclusion_code,
)
from src.utils import kiwoom_utils
from src.utils.constants import (
    RESTART_FLAG_PATH,
    SCALPING_RUNTIME_ARCHIVE_CUTOFF_DATE,
    TRADING_RULES,
)
from src.utils.logger import log_error, log_info
from src.utils.pipeline_event_logger import emit_pipeline_event
from src.engine import kiwoom_orders

KIWOOM_TOKEN = None
DB = None
ACTIVE_TARGETS = None
EVENT_BUS = None
HIGHEST_PRICES = None
STATE_LOCK = None
CONF = None
_LAST_AUTH_RESTART_TS = 0.0
_WS_FILL_ORD_RE = re.compile(
    r"WS 실제체결\]\s*(?P<code>\d{6})\s+(?P<side>BUY|SELL)\b.*?\(주문번호:\s*(?P<ord_no>\d+)\)"
)
_ENTRY_TP_RE = re.compile(
    r"ENTRY_TP_REFRESH\]\s*.*?\((?P<code>\d{6})\).*?\bord_no=(?P<ord_no>\S+)"
)
_ENTRY_FILL_RE = re.compile(
    r"ENTRY_FILL\]\s*.*?\((?P<code>\d{6})\).*?\bord_no=(?P<ord_no>\S+)"
)
_PIPELINE_LEG_RE = re.compile(
    r"\((?P<code>\d{6})\).*?\border_leg_sent\b.*?\bord_no=(?P<ord_no>\S+)"
)
_PIPELINE_TP_RE = re.compile(
    r"\((?P<code>\d{6})\).*?\bpreset_exit_setup\b.*?\bord_no=(?P<ord_no>\S+)"
)
_SCALPING_RUNTIME_ARCHIVE_CUTOFF_DATE = date.fromisoformat(
    SCALPING_RUNTIME_ARCHIVE_CUTOFF_DATE
)


def bind_sync_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    active_targets=None,
    event_bus=None,
    highest_prices=None,
    state_lock=None,
    conf=None,
):
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS, HIGHEST_PRICES, STATE_LOCK, CONF
    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if event_bus is not None:
        EVENT_BUS = event_bus
    if highest_prices is not None:
        HIGHEST_PRICES = highest_prices
    if state_lock is not None:
        STATE_LOCK = state_lock
    if conf is not None:
        CONF = conf


def _quarantine_prebaseline_scalping_ghost(
    record,
    *,
    real_codes: set[str] | dict[str, object],
    broker_absence_verified: bool,
    source: str,
) -> bool:
    """Expire archive-only SCALPING rows unless broker inventory proves a holding."""
    code = str(getattr(record, "stock_code", "") or "").strip()[:6]
    strategy = normalize_strategy(getattr(record, "strategy", None))
    rec_date = getattr(record, "rec_date", None)
    if isinstance(rec_date, datetime):
        rec_date = rec_date.date()
    buy_time = getattr(record, "buy_time", None)
    if isinstance(buy_time, datetime):
        lifecycle_date = buy_time.date()
    elif isinstance(buy_time, date):
        lifecycle_date = buy_time
    else:
        lifecycle_date = rec_date
    if (
        not code
        or code in real_codes
        or not broker_absence_verified
        or strategy != "SCALPING"
        or not isinstance(rec_date, date)
        or not isinstance(lifecycle_date, date)
        or lifecycle_date >= _SCALPING_RUNTIME_ARCHIVE_CUTOFF_DATE
    ):
        return False

    prior_status = str(getattr(record, "status", "") or "").upper()
    if prior_status not in {"HOLDING", "SELL_ORDERED"}:
        return False

    record.status = "EXPIRED"
    with _with_state_lock():
        target = next(
            (
                item
                for item in (ACTIVE_TARGETS or [])
                if _to_int(item.get("id")) == _to_int(getattr(record, "id", 0))
            ),
            None,
        )
        if target is not None:
            target["status"] = "EXPIRED"
            target["prebaseline_scalping_ghost_quarantined"] = True
        if HIGHEST_PRICES is not None:
            HIGHEST_PRICES.pop(code, None)

    log_info(
        "[PREBASELINE_SCALPING_GHOST_QUARANTINED] "
        f"{getattr(record, 'stock_name', code)}({code}) id={getattr(record, 'id', '-')} "
        f"rec_date={rec_date} lifecycle_date={lifecycle_date} "
        f"prior_status={prior_status} source={source} "
        f"broker_holding_present=False cutoff={_SCALPING_RUNTIME_ARCHIVE_CUTOFF_DATE}"
    )
    return True


def _emit_probe_recovery_event(target: dict, recovery: dict) -> None:
    if not (recovery.get("recovered") or recovery.get("circuit_open")):
        return
    code = str(target.get("code") or target.get("stock_code") or "").strip()[:6]
    stage = (
        "probe_restart_recovery_blocked"
        if recovery.get("circuit_open")
        else "probe_restart_recovered"
    )
    try:
        confirmation_count = max(0, int(target.get("probe_confirmation_count") or 0))
    except (TypeError, ValueError):
        confirmation_count = 0
    try:
        emit_pipeline_event(
            "HOLDING_PIPELINE",
            target.get("name") or code,
            code,
            stage,
            record_id=target.get("id"),
            fields={
                "reason": recovery.get("reason") or "-",
                "entry_split_probe_phase": (
                    target.get("entry_split_probe_phase")
                    or recovery.get("phase")
                    or "unknown"
                ),
                "entry_split_probe_bundle_id": (
                    target.get("entry_split_probe_bundle_id") or "-"
                ),
                "entry_split_probe_abort_reason": (
                    target.get("entry_split_probe_abort_reason") or "-"
                ),
                "probe_confirmation_count": confirmation_count,
                "probe_confirmation_required_count": 2,
                "probe_confirmation_last_state": (
                    target.get("probe_confirmation_last_state") or "UNKNOWN"
                ),
                "probe_expand_forbidden": bool(
                    target.get("probe_expand_forbidden", False)
                ),
                "entry_split_probe_scale_in_forbidden": bool(
                    target.get("entry_split_probe_scale_in_forbidden", False)
                ),
                "metric_role": "source_quality_gate",
                "decision_authority": "probe_restart_state_reconciliation",
                "window_policy": "same_day_position_cycle_restart_recovery",
                "sample_floor": "one_persisted_probe_bundle_and_live_holding",
                "primary_decision_metric": ("probe_terminal_expansion_guard_restored"),
                "source_quality_gate": ("code_target_id_and_broker_quantity_match"),
                "forbidden_uses": (
                    "new_order_authority|threshold_mutation|provider_route_change|"
                    "quantity_cap_release|broker_guard_bypass"
                ),
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": True,
            },
        )
    except Exception as exc:
        log_error(f"[ENTRY_SPLIT_PROBE_RECOVERY_EVENT] {code} failed={exc}")


def _refresh_kiwoom_token(reason, error_detail=None):
    """초기 부팅/토큰 미보유 시에만 키움 토큰을 발급합니다."""
    global KIWOOM_TOKEN, CONF
    detail_str = f" | detail={error_detail}" if error_detail else ""
    log_info(f"🔄 [TOKEN 재발급] 사유={reason}{detail_str}")
    if not CONF:
        log_error("❌ [TOKEN 재발급] CONF가 없어 재발급 불가")
        return None
    new_token = kiwoom_utils.get_kiwoom_token(CONF)
    if new_token:
        KIWOOM_TOKEN = new_token
        log_info("✅ [TOKEN 재발급] 성공")
    else:
        log_error("❌ [TOKEN 재발급] 실패")
    return new_token


def _request_auth_restart(reason, error_detail=None):
    """런타임 8005 인증 장애는 hot-refresh 대신 restart.flag 복구로 고정합니다."""
    global _LAST_AUTH_RESTART_TS
    cooldown_sec = int(
        getattr(TRADING_RULES, "KIWOOM_AUTH_RESTART_COOLDOWN_SEC", 120) or 120
    )
    now_ts = time.time()
    detail_str = f" | detail={error_detail}" if error_detail else ""
    try:
        cache_invalidated = kiwoom_utils.invalidate_kiwoom_token_cache(
            reason=f"auth_restart:{reason}"
        )
    except Exception as exc:
        cache_invalidated = False
        log_error(
            f"❌ [AUTH TOKEN CACHE INVALIDATE FAILED] reason={reason} error={exc}{detail_str}"
        )
    if cooldown_sec > 0 and (now_ts - _LAST_AUTH_RESTART_TS) < cooldown_sec:
        wait_left = max(0.0, float(cooldown_sec) - (now_ts - _LAST_AUTH_RESTART_TS))
        log_info(
            f"⏸️ [AUTH RESTART SKIP] cooldown={cooldown_sec}s wait_left={wait_left:.1f}s "
            f"token_cache_invalidated={cache_invalidated} reason={reason}{detail_str}"
        )
        return False

    try:
        RESTART_FLAG_PATH.touch()
        _LAST_AUTH_RESTART_TS = now_ts
        log_error(
            f"🚨 [AUTH RESTART REQUESTED] restart.flag set | "
            f"token_cache_invalidated={cache_invalidated} reason={reason}{detail_str}"
        )
        return True
    except Exception as exc:
        log_error(
            f"❌ [AUTH RESTART REQUEST FAILED] reason={reason} error={exc}{detail_str}"
        )
        return False


def _detect_auth_failure():
    """최근 잔고 조회 오류에서 인증 실패 여부를 판단."""
    errors = kiwoom_orders.get_last_inventory_errors()
    for err in errors:
        msg = str(err.get("return_msg", ""))
        code = str(err.get("return_code", ""))
        if "8005" in code or "Token" in msg or "토큰" in msg or "인증" in msg:
            return True, err
    return False, errors[0] if errors else None


def _to_int(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def _to_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _trade_type_for_strategy(strategy):
    normalized = normalize_strategy(strategy)
    if normalized == "SCALPING":
        return "SCALP"
    if normalized == "KOSDAQ_ML":
        return "RUNNER"
    return "MAIN"


def _inventory_name(real_data):
    return (
        real_data.get("name")
        or real_data.get("stock_name")
        or real_data.get("hts_kor_isnm")
        or real_data.get("item_name")
        or ""
    )


def _iter_recovery_log_paths():
    logs_dir = Path(__file__).resolve().parents[2] / "logs"
    patterns = (
        "bot_history.log*",
        "sniper_execution_receipts_info.log*",
        "pipeline_event_logger_info.log*",
    )
    seen = set()
    for pattern in patterns:
        for path in sorted(
            logs_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
        ):
            if path.is_file() and path not in seen:
                seen.add(path)
                yield path


def _tail_text(path: Path, max_bytes: int = 512_000) -> str:
    try:
        with path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(size - max_bytes, 0))
            return fh.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _recover_order_refs_from_logs(code: str) -> dict:
    normalized = str(code or "").strip()[:6]
    refs = {}
    if not normalized:
        return refs

    for path in _iter_recovery_log_paths():
        text = _tail_text(path)
        if not text:
            continue
        for line in reversed(text.splitlines()):
            if normalized not in line:
                continue
            if (
                "WS 실제체결" in line
                and "주문번호:" in line
                and "buy_ord_no" not in refs
            ):
                match = _WS_FILL_ORD_RE.search(line)
                if (
                    match
                    and match.group("code") == normalized
                    and match.group("side") == "BUY"
                ):
                    refs["buy_ord_no"] = match.group("ord_no")
            if "ENTRY_FILL" in line and "buy_ord_no" not in refs:
                match = _ENTRY_FILL_RE.search(line)
                if match and match.group("code") == normalized:
                    refs["buy_ord_no"] = match.group("ord_no")
            if "order_leg_sent" in line and "buy_ord_no" not in refs:
                match = _PIPELINE_LEG_RE.search(line)
                if match and match.group("code") == normalized:
                    refs["buy_ord_no"] = match.group("ord_no")
            if "ENTRY_TP_REFRESH" in line and "preset_tp_ord_no" not in refs:
                match = _ENTRY_TP_RE.search(line)
                if match and match.group("code") == normalized:
                    refs["preset_tp_ord_no"] = match.group("ord_no")
            if "preset_exit_setup" in line and "preset_tp_ord_no" not in refs:
                match = _PIPELINE_TP_RE.search(line)
                if match and match.group("code") == normalized:
                    refs["preset_tp_ord_no"] = match.group("ord_no")
            if "buy_ord_no" in refs and "preset_tp_ord_no" in refs:
                return refs
    return refs


def _ensure_runtime_target(record, *, buy_qty=None, buy_price=None):
    code = str(getattr(record, "stock_code", "") or "").strip()[:6]
    strategy = normalize_strategy(getattr(record, "strategy", None) or "KOSPI_ML")
    identity = target_identity(code, strategy)
    target = next(
        (
            t
            for t in (ACTIVE_TARGETS or [])
            if target_identity(t.get("code", ""), t.get("strategy", "")) == identity
            and str((t or {}).get("simulation_book") or "") != "scalp_ai_buy_all"
        ),
        None,
    )
    resolved_qty = _to_int(
        buy_qty if buy_qty is not None else getattr(record, "buy_qty", 0)
    )
    resolved_price = _to_float(
        buy_price if buy_price is not None else getattr(record, "buy_price", 0)
    )
    initial_buy_qty = _to_int(getattr(record, "initial_buy_qty", 0))
    scale_in_filled_qty = _to_int(getattr(record, "scale_in_filled_qty", 0))
    prior_bundle_count = max(
        _to_int(getattr(record, "add_count", 0)),
        _to_int(getattr(record, "avg_down_count", 0)),
        _to_int(getattr(record, "pyramid_count", 0)),
        int(bool(str(getattr(record, "last_add_type", "") or "").strip())),
    )
    if (
        prior_bundle_count > 0
        and (initial_buy_qty <= 0 or scale_in_filled_qty <= 0)
        and DB is not None
        and getattr(record, "id", None)
    ):
        try:
            with DB.get_session() as history_session:
                add_rows = (
                    history_session.query(HoldingAddHistory)
                    .filter(
                        HoldingAddHistory.recommendation_id == int(record.id),
                        HoldingAddHistory.event_type == "EXECUTED",
                    )
                    .order_by(
                        HoldingAddHistory.event_time.asc(), HoldingAddHistory.id.asc()
                    )
                    .all()
                )
            if add_rows:
                if initial_buy_qty <= 0:
                    initial_buy_qty = _to_int(getattr(add_rows[0], "prev_buy_qty", 0))
                if scale_in_filled_qty <= 0:
                    scale_in_filled_qty = sum(
                        max(0, _to_int(getattr(row, "executed_qty", 0)))
                        for row in add_rows
                    )
        except Exception as exc:
            log_info(
                f"[SCALE_IN_BASELINE] history hydration skipped "
                f"({code}, record_id={getattr(record, 'id', None)}): {exc}"
            )
    if initial_buy_qty <= 0 and prior_bundle_count <= 0:
        initial_buy_qty = max(0, resolved_qty)
    buy_time = getattr(record, "buy_time", None)
    position_tag = normalize_position_tag(
        strategy, getattr(record, "position_tag", None)
    )
    order_refs = _recover_order_refs_from_logs(code)
    recovered_buy_ord_no = str(
        getattr(record, "_broker_recovered_buy_ord_no", "") or ""
    ).strip()
    recovered_orig_ord_no = str(
        getattr(record, "_broker_recovered_orig_ord_no", "") or ""
    ).strip()
    if recovered_buy_ord_no and "buy_ord_no" not in order_refs:
        order_refs["buy_ord_no"] = recovered_buy_ord_no
    broker_recovered = bool(getattr(record, "_broker_recovered", False))
    broker_recovered_legacy = bool(getattr(record, "_broker_recovered_legacy", False))
    broker_recovered_at = getattr(record, "_broker_recovered_at", None) or time.time()
    broker_recovered_execution_verified = bool(
        getattr(record, "_broker_recovered_execution_verified", False)
    )

    if target is None:
        marcap = int(DB.get_latest_marcap(code) or 0) if DB is not None and code else 0
        target = {
            "id": getattr(record, "id", None),
            "code": code,
            "name": getattr(record, "stock_name", "") or code,
            "strategy": strategy,
            "trade_type": getattr(record, "trade_type", None)
            or _trade_type_for_strategy(strategy),
            "status": "HOLDING",
            "position_tag": position_tag,
            "buy_qty": resolved_qty,
            "buy_price": resolved_price,
            "initial_buy_qty": initial_buy_qty,
            "scale_in_filled_qty": max(0, scale_in_filled_qty),
            "buy_time": buy_time,
            "holding_started_at": buy_time or datetime.now(),
            "added_time": time.time(),
            "marcap": marcap,
            "scale_in_locked": bool(getattr(record, "scale_in_locked", False)),
            "broker_recovered": broker_recovered,
            "broker_recovered_legacy": broker_recovered_legacy,
            "broker_recovered_at": broker_recovered_at,
            "broker_recovered_execution_verified": broker_recovered_execution_verified,
        }
        if order_refs.get("buy_ord_no"):
            target["odno"] = order_refs["buy_ord_no"]
        if order_refs.get("preset_tp_ord_no"):
            target["preset_tp_ord_no"] = order_refs["preset_tp_ord_no"]
        if recovered_orig_ord_no:
            target["broker_recovered_orig_ord_no"] = recovered_orig_ord_no
        if strategy == "SCALPING" and position_tag != OPENING_ROTATION_POSITION_TAG:
            target.setdefault("exit_mode", "SCALP_PRESET_TP")
        probe_recovery = recover_probe_runtime_bundle_for_stock(target)
        if probe_recovery.get("recovered") or probe_recovery.get("circuit_open"):
            log_info(
                f"[ENTRY_SPLIT_PROBE_RECOVERY] {code} "
                f"result={probe_recovery.get('reason')} "
                f"phase={probe_recovery.get('phase', '-')}"
            )
            _emit_probe_recovery_event(target, probe_recovery)
        ACTIVE_TARGETS.append(target)
        if EVENT_BUS is not None and code:
            EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code]})
        return target

    target["id"] = getattr(record, "id", target.get("id"))
    target["name"] = getattr(record, "stock_name", "") or target.get("name") or code
    target["strategy"] = strategy
    target["status"] = "HOLDING"
    target["position_tag"] = position_tag
    target["buy_qty"] = resolved_qty
    target["buy_price"] = resolved_price
    target["initial_buy_qty"] = initial_buy_qty
    target["scale_in_filled_qty"] = max(0, scale_in_filled_qty)
    target["buy_time"] = buy_time or target.get("buy_time")
    if buy_time and not target.get("holding_started_at"):
        target["holding_started_at"] = buy_time
    if order_refs.get("buy_ord_no") and not str(target.get("odno", "") or "").strip():
        target["odno"] = order_refs["buy_ord_no"]
    if (
        order_refs.get("preset_tp_ord_no")
        and not str(target.get("preset_tp_ord_no", "") or "").strip()
    ):
        target["preset_tp_ord_no"] = order_refs["preset_tp_ord_no"]
    if recovered_orig_ord_no:
        target["broker_recovered_orig_ord_no"] = recovered_orig_ord_no
    target["scale_in_locked"] = bool(
        getattr(record, "scale_in_locked", target.get("scale_in_locked", False))
    )
    target["broker_recovered"] = broker_recovered or bool(
        target.get("broker_recovered")
    )
    target["broker_recovered_legacy"] = broker_recovered_legacy or bool(
        target.get("broker_recovered_legacy")
    )
    target["broker_recovered_execution_verified"] = (
        broker_recovered_execution_verified
        or bool(target.get("broker_recovered_execution_verified"))
    )
    if broker_recovered:
        target["broker_recovered_at"] = broker_recovered_at
    if strategy == "SCALPING" and position_tag != OPENING_ROTATION_POSITION_TAG:
        target.setdefault("exit_mode", "SCALP_PRESET_TP")
    elif strategy == "SCALPING" and position_tag == OPENING_ROTATION_POSITION_TAG:
        target.pop("exit_mode", None)
    probe_recovery = recover_probe_runtime_bundle_for_stock(target)
    if probe_recovery.get("recovered") or probe_recovery.get("circuit_open"):
        log_info(
            f"[ENTRY_SPLIT_PROBE_RECOVERY] {code} "
            f"result={probe_recovery.get('reason')} "
            f"phase={probe_recovery.get('phase', '-')}"
        )
        _emit_probe_recovery_event(target, probe_recovery)
    return target


def _broker_recovery_audience(target):
    target = target or {}
    simulated = (
        bool(target.get("swing_live_order_dry_run"))
        or bool(target.get("scalp_live_simulator"))
        or bool(target.get("simulation_book"))
        or bool(target.get("simulation_owner"))
        or target.get("actual_order_submitted") is False
    )
    if simulated:
        return "ADMIN_ONLY"
    return str(target.get("msg_audience") or "ADMIN_ONLY")


def _publish_broker_recovered_buy_message(
    target,
    *,
    qty,
    buy_price,
    order_no,
    execution_verified,
):
    if EVENT_BUS is None or target is None:
        return False
    if target.get("broker_recover_buy_notified"):
        return False

    name = str(target.get("name") or target.get("code") or "UNKNOWN")
    order_line = f"\n주문번호: `{order_no}`" if order_no else ""
    verify_line = "체결/주문조회 확인" if execution_verified else "잔고조회 확인"
    msg = (
        f"🛒 **[{name}]** 매수 체결 확인 (브로커 복구)\n"
        f"평균 체결가: `{float(buy_price):,.0f}원`\n"
        f"체결수량: `{int(qty)}주`"
        f"{order_line}\n확인 경로: `{verify_line}`"
    )
    EVENT_BUS.publish(
        "TELEGRAM_BROADCAST",
        {
            "message": msg,
            "audience": _broker_recovery_audience(target),
            "parse_mode": "Markdown",
        },
    )
    target["broker_recover_buy_notified"] = True
    return True


def _recover_missing_broker_holdings(session, real_codes):
    recovered = 0
    today = datetime.now().date()
    execution_snapshot = []
    order_ref_snapshot = []
    if KIWOOM_TOKEN:
        try:
            execution_snapshot = kiwoom_utils.get_account_execution_snapshot_kt00008(
                KIWOOM_TOKEN
            )
        except Exception:
            execution_snapshot = []
        use_order_ref_2nd_pass = False
        if isinstance(CONF, dict) and "ENABLE_ORDER_REF_2ND_PASS" in CONF:
            use_order_ref_2nd_pass = bool(CONF.get("ENABLE_ORDER_REF_2ND_PASS"))
        elif len(str(KIWOOM_TOKEN or "")) >= 40:
            # 테스트 토큰("token")에서는 호출을 건너뛰고, 실토큰에서만 기본 활성
            use_order_ref_2nd_pass = True
        if use_order_ref_2nd_pass:
            try:
                qry_tp = (
                    str((CONF or {}).get("BROKER_ORDER_REF_QRY_TP", "0"))
                    if isinstance(CONF, dict)
                    else "0"
                )
                stk_bond_tp = (
                    str((CONF or {}).get("BROKER_ORDER_REF_STK_BOND_TP", "0"))
                    if isinstance(CONF, dict)
                    else "0"
                )
                order_ref_snapshot = kiwoom_utils.get_order_reference_snapshot_2nd_pass(
                    KIWOOM_TOKEN,
                    qry_tp=qry_tp,
                    stk_bond_tp=stk_bond_tp,
                )
            except Exception:
                order_ref_snapshot = []
    active_statuses = {"HOLDING", "SELL_ORDERED", "BUY_ORDERED"}
    tracked_codes = {
        str(getattr(record, "stock_code", "") or "").strip()[:6]
        for record in session.query(RecommendationHistory)
        .filter(RecommendationHistory.status.in_(tuple(active_statuses)))
        .all()
    }
    tracked_codes.update(
        str(t.get("code", "")).strip()[:6]
        for t in (ACTIVE_TARGETS or [])
        if str(t.get("status", "")).upper() in active_statuses
    )

    for code, real_data in real_codes.items():
        if code in tracked_codes:
            continue

        real_qty = _to_int(real_data.get("qty", 0))
        if real_qty <= 0:
            continue

        raw_price = (
            real_data.get("buy_price")
            or real_data.get("purchase_price")
            or real_data.get("pchs_avg_pric")
            or 0
        )
        real_buy_uv = _to_int(raw_price)
        stock_name = _inventory_name(real_data) or code
        execution_match = next(
            (
                row
                for row in execution_snapshot
                if row.get("code") == code
                and row.get("side") == "매수"
                and _to_int(row.get("qty")) == real_qty
                and (
                    _to_int(row.get("unit_price")) <= 0
                    or abs(_to_int(row.get("unit_price")) - real_buy_uv) <= 1
                )
            ),
            None,
        )
        order_ref_match = kiwoom_utils.find_order_reference_match(
            order_ref_snapshot,
            code=code,
            side="매수",
            qty=real_qty,
            unit_price=real_buy_uv,
            max_price_diff=1,
        )
        history_records = (
            session.query(RecommendationHistory).filter_by(stock_code=code).all()
        )
        latest = max(
            history_records, key=lambda r: int(getattr(r, "id", 0) or 0), default=None
        )
        reusable = next(
            (
                r
                for r in sorted(
                    history_records,
                    key=lambda r: int(getattr(r, "id", 0) or 0),
                    reverse=True,
                )
                if str(getattr(r, "status", "") or "").upper()
                in {"WATCHING", "EXPIRED"}
            ),
            None,
        )

        if reusable is not None:
            record = reusable
            strategy = normalize_strategy(
                getattr(record, "strategy", None) or "SCALPING"
            )
            record.stock_name = stock_name
            record.status = "HOLDING"
            record.strategy = strategy
            record.trade_type = getattr(
                record, "trade_type", None
            ) or _trade_type_for_strategy(strategy)
            record.position_tag = normalize_position_tag(
                strategy, getattr(record, "position_tag", None)
            )
            record.buy_qty = real_qty
            record.buy_price = real_buy_uv
            record.buy_time = getattr(record, "buy_time", None) or datetime.now()
        else:
            strategy = normalize_strategy(
                getattr(latest, "strategy", None) or "KOSPI_ML"
            )
            record = RecommendationHistory(
                rec_date=datetime.now().date(),
                stock_code=code,
                stock_name=stock_name,
                trade_type=getattr(latest, "trade_type", None)
                or _trade_type_for_strategy(strategy),
                strategy=strategy,
                status="HOLDING",
                position_tag=normalize_position_tag(
                    strategy, getattr(latest, "position_tag", None)
                ),
                prob=float(getattr(latest, "prob", 0.7) or 0.7),
                buy_price=real_buy_uv,
                buy_qty=real_qty,
                buy_time=datetime.now(),
            )
            session.add(record)
            if hasattr(session, "flush"):
                session.flush()

        rec_date = getattr(record, "rec_date", None)
        legacy_recovered = bool(rec_date and rec_date < today)
        if execution_match and execution_match.get("trade_date"):
            try:
                exec_trade_date = datetime.strptime(
                    execution_match["trade_date"], "%Y%m%d"
                ).date()
                legacy_recovered = legacy_recovered or exec_trade_date < today
            except Exception:
                pass
        record._broker_recovered = True
        record._broker_recovered_legacy = legacy_recovered
        record._broker_recovered_at = time.time()
        record._broker_recovered_execution_verified = bool(
            execution_match or order_ref_match
        )
        record._broker_recovered_buy_ord_no = str(
            (order_ref_match or {}).get("ord_no", "") or ""
        ).strip()
        record._broker_recovered_orig_ord_no = str(
            (order_ref_match or {}).get("orig_ord_no", "") or ""
        ).strip()

        log_info(
            f"🔄 [BROKER_RECOVER] {stock_name}({code}) -> HOLDING "
            f"(qty={real_qty}, buy_price={real_buy_uv}, strategy={getattr(record, 'strategy', '')}, "
            f"legacy={legacy_recovered}, exec_verified={bool(execution_match or order_ref_match)}, "
            f"order_ref_verified={bool(order_ref_match)})"
        )
        target = _ensure_runtime_target(record, buy_qty=real_qty, buy_price=real_buy_uv)
        if not legacy_recovered:
            _publish_broker_recovered_buy_message(
                target,
                qty=real_qty,
                buy_price=real_buy_uv,
                order_no=str((order_ref_match or {}).get("ord_no", "") or "").strip(),
                execution_verified=bool(execution_match or order_ref_match),
            )
        if HIGHEST_PRICES is not None and real_buy_uv > 0:
            HIGHEST_PRICES.setdefault(code, real_buy_uv)
        tracked_codes.add(code)
        recovered += 1

    return recovered


def _with_state_lock():
    class _DummyLock:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    return STATE_LOCK if STATE_LOCK is not None else _DummyLock()


def _reconcile_scale_in_lock(record, real_qty, real_buy_uv):
    """
    계좌 truth 기준으로 scale_in_locked 자동 해제 여부를 판단합니다.
    - DB/메모리/계좌 수량과 평단이 정합하면 자동 해제
    - 불일치가 남아 있으면 lock 유지
    """
    target_stock = next(
        (
            t
            for t in (ACTIVE_TARGETS or [])
            if str(t.get("code", "")).strip()[:6] == str(record.stock_code).strip()[:6]
        ),
        None,
    )
    mem_pending = bool(target_stock.get("pending_add_order")) if target_stock else False
    if mem_pending:
        return False

    db_qty = _to_int(record.buy_qty)
    db_avg = _to_float(record.buy_price)
    qty_match = db_qty == real_qty
    avg_match = (real_buy_uv <= 0) or isclose(
        db_avg, float(real_buy_uv), rel_tol=0.0, abs_tol=1.0
    )

    if qty_match and avg_match:
        reconcile_order_no = find_latest_open_add_order_no(
            DB, getattr(record, "id", None)
        )
        record.scale_in_locked = False
        if target_stock:
            target_stock["scale_in_locked"] = False
        record_add_history_event(
            DB,
            recommendation_id=getattr(record, "id", None),
            stock_code=record.stock_code,
            stock_name=record.stock_name,
            strategy=getattr(record, "strategy", None),
            add_type=getattr(record, "last_add_type", None),
            event_type="RECONCILED",
            order_no=reconcile_order_no,
            executed_qty=real_qty,
            executed_price=real_buy_uv,
            new_buy_price=record.buy_price,
            new_buy_qty=record.buy_qty,
            add_count_after=getattr(record, "add_count", 0),
            reason="scale_in_lock_auto_release",
        )
        log_info(
            f"✅ [ADD_RECONCILED] {record.stock_name}({record.stock_code}) scale_in_locked 자동 해제"
        )
        return True

    log_info(
        f"⚠️ [ADD_RECONCILE_PENDING] {record.stock_name}({record.stock_code}) "
        f"lock 유지 (db_qty={db_qty}, real_qty={real_qty}, db_avg={db_avg}, real_avg={real_buy_uv})"
    )
    return False


def _remove_manual_control_exclusion_for_completed_holding(
    code, *, reason: str
) -> None:
    removal = remove_manual_control_exclusion_code(code, reason=reason)
    if removal.removed:
        log_info(
            f"🧹 [수동관리 제외 해제] {removal.code} removed from {removal.source} "
            f"reason={removal.reason}"
        )


def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS

    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")
    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(초기 동기화)")
        if not KIWOOM_TOKEN:
            log_error("❌ [동기화 중단] 토큰 재발급 실패")
            return

    real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
    if not successful_exchanges:
        last_errors = kiwoom_orders.get_last_inventory_errors()
        if last_errors:
            log_info(f"⚠️ [동기화 원인] 잔고 조회 실패 상세: {last_errors}")
        auth_failed, auth_err = _detect_auth_failure()
        if auth_failed:
            _request_auth_restart("인증 실패(8005)", auth_err)
            print("⚠️ [동기화 보류] 인증 장애 감지. restart.flag 복구를 기다립니다.")
            return
        print("⚠️ [동기화 보류] 모든 거래소 잔고 조회 실패, 1회 재시도합니다.")
        time.sleep(1.5)
        real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(
            KIWOOM_TOKEN
        )
        if not successful_exchanges:
            print("⚠️ [동기화 보류] 모든 거래소 잔고 조회 실패, 동기화를 건너뜁니다.")
            return

    real_codes = {
        str(item.get("code", "")).strip()[:6]: item
        for item in real_inventory
        if item.get("code")
    }

    def get_exchange(code):
        is_nxt = DB.get_latest_is_nxt(code)
        return "NXT" if is_nxt else "KRX"

    pending_manual_control_removals = []
    try:
        with DB.get_session() as session:
            archive_active_records = (
                session.query(RecommendationHistory)
                .filter(RecommendationHistory.status.in_(("HOLDING", "SELL_ORDERED")))
                .all()
            )
            for record in archive_active_records:
                code = str(record.stock_code).strip()[:6]
                exchange = get_exchange(code)
                if _quarantine_prebaseline_scalping_ghost(
                    record,
                    real_codes=real_codes,
                    broker_absence_verified=exchange in successful_exchanges,
                    source="startup_balance_sync",
                ):
                    pending_manual_control_removals.append(
                        (
                            code,
                            "startup_sync_prebaseline_scalping_ghost_quarantined",
                        )
                    )

            db_holdings = (
                session.query(RecommendationHistory).filter_by(status="HOLDING").all()
            )
            db_holdings = [
                record
                for record in db_holdings
                if str(getattr(record, "status", "") or "").upper() == "HOLDING"
            ]

            for record in db_holdings:
                code = str(record.stock_code).strip()[:6]
                name = record.stock_name
                safe_db_qty = _to_int(record.buy_qty)

                if code not in real_codes:
                    exchange = get_exchange(code)
                    if exchange in successful_exchanges:
                        print(
                            f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경."
                        )
                        record.status = "COMPLETED"
                        if not record.sell_time:
                            record.sell_time = datetime.now()
                        pending_manual_control_removals.append(
                            (code, "startup_sync_completed_no_broker_holding")
                        )

                        target = next(
                            (
                                t
                                for t in ACTIVE_TARGETS
                                if str(t.get("code", "")).strip()[:6] == code
                            ),
                            None,
                        )
                        if target:
                            target["status"] = "COMPLETED"
                    else:
                        print(
                            f"⚠️ [동기화] {name}({code}): {exchange} 거래소 잔고 조회 실패로 상태 변경 생략."
                        )
                else:
                    real_qty = _to_int(real_codes[code].get("qty", 0))
                    raw_price = (
                        real_codes[code].get("buy_price")
                        or real_codes[code].get("purchase_price")
                        or real_codes[code].get("pchs_avg_pric")
                        or 0
                    )
                    real_buy_uv = _to_int(raw_price)
                    if safe_db_qty != real_qty:
                        print(
                            f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)"
                        )
                        record.buy_qty = real_qty

                    for t in ACTIVE_TARGETS:
                        if str(t.get("code", "")).strip()[:6] == code and real_qty > 0:
                            t["buy_qty"] = real_qty

                    if real_buy_uv > 0 and not isclose(
                        _to_float(record.buy_price),
                        float(real_buy_uv),
                        rel_tol=0.0,
                        abs_tol=1.0,
                    ):
                        record.buy_price = real_buy_uv
                        for t in ACTIVE_TARGETS:
                            if (
                                str(t.get("code", "")).strip()[:6] == code
                                and real_qty > 0
                            ):
                                t["buy_price"] = real_buy_uv

                    if bool(record.scale_in_locked):
                        _reconcile_scale_in_lock(record, real_qty, real_buy_uv)

            recovered_count = _recover_missing_broker_holdings(session, real_codes)
            if recovered_count:
                log_info(
                    f"🔄 [데이터 동기화] broker-only holding {recovered_count}건을 복구"
                )

    except Exception as exc:
        log_error(f"🚨 DB 동기화 중 에러 발생: {exc}")
    else:
        for code, reason in pending_manual_control_removals:
            _remove_manual_control_exclusion_for_completed_holding(code, reason=reason)

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")


def sync_state_with_broker():
    """
    [Fallback 로직] 웹소켓 재접속 시 증권사 실제 잔고를 불러와
    누락된 체결 건(BUY_ORDERED -> HOLDING)을 강제로 동기화합니다.
    """
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS

    print("🔄 [상태 동기화] 웹소켓 재접속 감지! 증권사 잔고와 봇 상태를 대조합니다...")
    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(상태 동기화)")

    real_balances, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(
        KIWOOM_TOKEN
    )
    if not successful_exchanges:
        log_info("⚠️ [상태 동기화] 잔고 조회 실패 -> 토큰 재발급 후 재시도")
        _refresh_kiwoom_token("잔고 조회 실패(상태 동기화)")
        if KIWOOM_TOKEN:
            real_balances, successful_exchanges = (
                kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
            )
        print("⚠️ [상태 동기화] 모든 거래소 잔고 조회 실패. 다음 턴에 재시도합니다.")
        return

    balance_dict = {
        str(item.get("code", "")).strip()[:6]: item
        for item in real_balances
        if item.get("code")
    }

    synced_count = 0

    try:
        with DB.get_session() as session:
            pending_records = (
                session.query(RecommendationHistory)
                .filter_by(status="BUY_ORDERED")
                .all()
            )

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in balance_dict:
                    real_data = balance_dict[code]
                    cur_qty = _to_int(real_data.get("qty", 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get("buy_price")
                            or real_data.get("purchase_price")
                            or real_data.get("pchs_avg_pric")
                            or 0
                        )
                        buy_uv = _to_int(raw_price)

                        print(
                            f"✅ [동기화 완료] 누락 체결 확인! {record.stock_name}({code}) | 수량: {cur_qty} | 평단가: {buy_uv:,}원"
                        )

                        record.status = "HOLDING"
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        if not record.buy_time:
                            record.buy_time = datetime.now()

                        for t in ACTIVE_TARGETS:
                            if str(t.get("code", "")).strip()[:6] == code:
                                t["status"] = "HOLDING"
                                t["buy_price"] = buy_uv
                                t["buy_qty"] = cur_qty

                        synced_count += 1

    except Exception as exc:
        log_error(f"🚨 [상태 동기화] DB 처리 중 에러 발생: {exc}")

    if synced_count > 0:
        msg = f"🔄 <b>[시스템 복구 알림]</b>\n웹소켓 단절 시간 동안 체결된 <b>{synced_count}건</b>의 종목을 성공적으로 동기화하여 감시망에 편입했습니다."
        EVENT_BUS.publish(
            "TELEGRAM_BROADCAST",
            {"message": msg, "audience": "ADMIN_ONLY", "parse_mode": "HTML"},
        )
    else:
        print("✅ [상태 동기화] 누락된 체결 건이 없습니다.")


# =====================================================================
# 🔄 3분 주기 강제 계좌 동기화 (웹소켓 영수증 누락 방어)
# =====================================================================


def _unique_sell_execution_reconciliation(
    rows,
    *,
    code,
    qty,
    trade_date,
):
    """Return one exact same-day broker sell row or a fail-closed reason."""

    normalized_code = str(code or "").strip()[:6]
    expected_qty = max(0, _to_int(qty))
    expected_date = str(trade_date or "").replace("-", "").strip()
    matches = []
    for row in rows or []:
        row_code = str((row or {}).get("code") or "").strip()[:6]
        row_side = str((row or {}).get("side") or "").strip().upper()
        row_date = str((row or {}).get("trade_date") or "").replace("-", "").strip()
        row_qty = max(0, _to_int((row or {}).get("qty")))
        row_price = max(0, _to_int((row or {}).get("unit_price")))
        if (
            row_code == normalized_code
            and row_side in {"매도", "SELL", "S", "1"}
            and row_date == expected_date
            and expected_qty > 0
            and row_qty == expected_qty
            and row_price > 0
        ):
            matches.append(dict(row))
    if len(matches) == 1:
        return matches[0], "unique_same_day_code_side_qty_execution"
    if not matches:
        return None, "exact_sell_execution_not_found"
    return None, "ambiguous_multiple_sell_executions"


def periodic_account_sync():
    """
    주기적으로 실제 증권사 잔고를 조회하여, 웹소켓 체결 누락으로 인해
    DB와 메모리가 꼬이는 현상을 강제로 바로잡습니다.
    """
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, HIGHEST_PRICES, STATE_LOCK

    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(정기 동기화)")
    real_inventory, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(
        KIWOOM_TOKEN
    )
    if not successful_exchanges:
        log_info("⚠️ [정기 동기화] 잔고 조회 실패 -> 토큰 재발급 후 재시도")
        _refresh_kiwoom_token("잔고 조회 실패(정기 동기화)")
        if KIWOOM_TOKEN:
            real_inventory, successful_exchanges = (
                kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
            )
        print("⚠️ [정기 동기화] 모든 거래소 잔고 조회 실패, 동기화를 건너뜁니다.")
        return

    real_codes = {
        str(item.get("code", "")).strip()[:6]: item
        for item in real_inventory
        if item.get("code")
    }
    broker_snapshot_at = datetime.now().timestamp()
    unfilled_snapshot_ok = False
    open_qty_by_code = {}
    sell_execution_snapshot = None

    def _sell_execution_rows():
        nonlocal sell_execution_snapshot
        if sell_execution_snapshot is None:
            try:
                sell_execution_snapshot = (
                    kiwoom_utils.get_account_execution_snapshot_kt00008(KIWOOM_TOKEN)
                    or []
                )
            except Exception as exc:
                log_error(
                    "🚨 [정기 동기화] 매도 체결 reconciliation snapshot 조회 실패: "
                    f"{exc}"
                )
                sell_execution_snapshot = []
        return sell_execution_snapshot

    def get_exchange(code):
        is_nxt = DB.get_latest_is_nxt(code)
        return "NXT" if is_nxt else "KRX"

    synced_count = 0
    pending_manual_control_removals = []
    pending_sell_reconciliation_events = []
    pending_runtime_target_removals = []

    def _queue_sell_reconciliation_event(*args, **kwargs):
        pending_sell_reconciliation_events.append((args, kwargs))

    try:
        with DB.get_session() as session:
            # 1️⃣ [매도 누락 방어] DB엔 HOLDING/SELL_ORDERED 인데, 실제 계좌엔 없는 경우 -> 팔렸음 (COMPLETED)
            active_records = (
                session.query(RecommendationHistory)
                .filter(RecommendationHistory.status.in_(["HOLDING", "SELL_ORDERED"]))
                .all()
            )
            active_real_codes = {
                str(record.stock_code).strip()[:6]
                for record in active_records
                if str(record.stock_code).strip()[:6] in real_codes
            }
            if active_real_codes:
                try:
                    unfilled_rows, unfilled_source_meta = (
                        kiwoom_utils.get_unfilled_order_snapshot_ka10075_with_meta(
                            KIWOOM_TOKEN,
                            all_stk_tp="1",
                            trde_tp="0",
                            stex_tp="0",
                        )
                    )
                    unfilled_snapshot_ok = bool(
                        (unfilled_source_meta or {}).get("request_succeeded", False)
                    )
                    if not unfilled_snapshot_ok:
                        log_error(
                            "🚨 [정기 동기화] 미체결 스냅샷 응답 상태 불명확: "
                            f"{unfilled_source_meta}"
                        )
                except Exception as exc:
                    unfilled_rows = []
                    log_error(f"🚨 [정기 동기화] 미체결 스냅샷 조회 실패: {exc}")
                for row in unfilled_rows or []:
                    code = str(row.get("code") or "").strip()[:6]
                    if code not in active_real_codes:
                        continue
                    side = str(row.get("side") or "").strip().upper()
                    remaining_qty = max(0, _to_int(row.get("remaining_qty", 0)))
                    summary = open_qty_by_code.setdefault(
                        code, {"open_buy_qty": 0, "open_sell_qty": 0}
                    )
                    if side in {"매수", "BUY", "B", "2"}:
                        summary["open_buy_qty"] += remaining_qty
                    elif side in {"매도", "SELL", "S", "1"}:
                        summary["open_sell_qty"] += remaining_qty

            for record in active_records:
                code = str(record.stock_code).strip()[:6]
                exchange = get_exchange(code)

                if _quarantine_prebaseline_scalping_ghost(
                    record,
                    real_codes=real_codes,
                    broker_absence_verified=exchange in successful_exchanges,
                    source="periodic_account_sync",
                ):
                    pending_manual_control_removals.append(
                        (
                            code,
                            "periodic_sync_prebaseline_scalping_ghost_quarantined",
                        )
                    )
                    continue

                if code not in real_codes:
                    if exchange in successful_exchanges:
                        prior_record_status = str(record.status or "").upper()
                        print(
                            f"⚠️ [정기 동기화] {record.stock_name}({code}) 잔고 없음. 매도 영수증 누락으로 판단하여 COMPLETED 강제 전환."
                        )
                        record.status = "COMPLETED"
                        record.sell_time = None
                        pending_manual_control_removals.append(
                            (code, "periodic_sync_completed_no_broker_holding")
                        )

                        with STATE_LOCK:
                            target_stock = next(
                                (
                                    t
                                    for t in ACTIVE_TARGETS
                                    if str(t.get("code", "")).strip()[:6] == code
                                ),
                                None,
                            )
                            target_snapshot = dict(target_stock or {})

                        estimated_sell_price = target_snapshot.get(
                            "sell_target_price", 0
                        )
                        prior_status = str(
                            target_snapshot.get("status") or prior_record_status or ""
                        ).upper()
                        sell_order_no = str(
                            target_snapshot.get("sell_odno") or ""
                        ).strip()
                        prior_partial_qty = max(
                            _to_int(
                                target_snapshot.get("early_volatility_tp_filled_qty")
                            ),
                            _to_int(
                                target_snapshot.get(
                                    "nxt_rising_missed_tp1_partial_filled_qty"
                                )
                            ),
                        )
                        exact_execution = None
                        exact_execution_reason = "prior_status_not_sell_ordered"
                        if prior_partial_qty > 0:
                            exact_execution_reason = (
                                "partial_realized_context_requires_fill_receipt"
                            )
                        elif prior_status == "SELL_ORDERED":
                            exact_execution, exact_execution_reason = (
                                _unique_sell_execution_reconciliation(
                                    _sell_execution_rows(),
                                    code=code,
                                    qty=getattr(record, "buy_qty", 0),
                                    trade_date=datetime.now().strftime("%Y%m%d"),
                                )
                            )

                        # Balance absence proves that the position is no
                        # longer held.  Only a unique same-day broker
                        # execution row proves fill price and realized PnL;
                        # an intended target price never does.
                        if exact_execution:
                            record.sell_price = _to_int(
                                exact_execution.get("unit_price")
                            )
                            record.profit_rate = calculate_net_profit_rate(
                                record.buy_price,
                                record.sell_price,
                            )
                            realized_pnl_krw = calculate_net_realized_pnl(
                                record.buy_price,
                                record.sell_price,
                                getattr(record, "buy_qty", 0),
                            )
                            reconciliation_state = "broker_execution_snapshot_recovered"
                        else:
                            record.sell_price = None
                            record.profit_rate = None
                            realized_pnl_krw = None
                            reconciliation_state = (
                                "broker_holding_absent_fill_receipt_missing"
                            )

                        with STATE_LOCK:
                            if target_stock:
                                target_stock.update(
                                    {
                                        "status": "COMPLETED",
                                        "sell_completion_reconciliation_state": (
                                            reconciliation_state
                                        ),
                                        "sell_completion_reconciliation_at": (
                                            broker_snapshot_at
                                        ),
                                        "sell_completion_reconciliation_exchange": (
                                            exchange
                                        ),
                                    }
                                )
                                if exact_execution:
                                    target_stock.update(
                                        {
                                            "sell_price": record.sell_price,
                                            "profit_rate": record.profit_rate,
                                        }
                                    )

                            if HIGHEST_PRICES is not None:
                                HIGHEST_PRICES.pop(code, None)
                        try:
                            _queue_sell_reconciliation_event(
                                "HOLDING_PIPELINE",
                                record.stock_name,
                                code,
                                (
                                    "sell_completed"
                                    if exact_execution
                                    else "sell_completion_reconciliation_gap"
                                ),
                                record_id=getattr(record, "id", None),
                                fields={
                                    "metric_role": (
                                        "execution_quality_real_only"
                                        if exact_execution
                                        else "source_quality_gap"
                                    ),
                                    "decision_authority": (
                                        "broker_balance_reconciliation_only"
                                    ),
                                    "window_policy": (
                                        "same_position_cycle_periodic_account_sync"
                                    ),
                                    "sample_floor": (
                                        (
                                            "one_unique_same_day_broker_sell_execution"
                                            if exact_execution
                                            else (
                                                "one_missing_holding_with_no_fill_receipt"
                                            )
                                        )
                                    ),
                                    "primary_decision_metric": (
                                        "confirmed_broker_sell_fill_price"
                                    ),
                                    "source_quality_gate": (
                                        "unique_same_day_code_side_qty_broker_execution"
                                    ),
                                    "runtime_effect": True,
                                    "actual_order_submitted": bool(exact_execution),
                                    "broker_order_forbidden": not bool(exact_execution),
                                    "forbidden_uses": (
                                        (
                                            "threshold_mutation|provider_change|"
                                            "order_price_change|quantity_cap_change"
                                            if exact_execution
                                            else (
                                                "realized_pnl|EV|rolling|MTD|"
                                                "cumulative_tuning|"
                                                "live_auto_promotion|"
                                                "runtime_apply_bridge|"
                                                "threshold_mutation|"
                                                "provider_change|"
                                                "order_price_change|"
                                                "quantity_cap_change"
                                            )
                                        )
                                    ),
                                    "reconciliation_result": (reconciliation_state),
                                    "execution_match_reason": (exact_execution_reason),
                                    "execution_match_count": (
                                        1 if exact_execution else 0
                                    ),
                                    "sell_price": (
                                        record.sell_price if exact_execution else "-"
                                    ),
                                    "profit_rate": (
                                        record.profit_rate if exact_execution else "-"
                                    ),
                                    "realized_pnl_krw": (
                                        realized_pnl_krw if exact_execution else "-"
                                    ),
                                    "trade_status": "COMPLETED",
                                    "buy_price": getattr(record, "buy_price", "-"),
                                    "buy_qty": getattr(record, "buy_qty", "-"),
                                    "sell_qty": (
                                        exact_execution.get("qty")
                                        if exact_execution
                                        else "-"
                                    ),
                                    "strategy": (
                                        target_snapshot.get("strategy")
                                        or getattr(record, "strategy", "-")
                                        or "-"
                                    ),
                                    "position_tag": (
                                        target_snapshot.get("position_tag")
                                        or getattr(record, "position_tag", "-")
                                        or "-"
                                    ),
                                    "sell_completion_receipt_source": (
                                        "kt00008_unique_execution_reconciliation"
                                        if exact_execution
                                        else "missing"
                                    ),
                                    "sell_time_precision": (
                                        "date_only" if exact_execution else "missing"
                                    ),
                                    "sell_time_forbidden_for_intraday_horizon": True,
                                    "prior_status": prior_status or "-",
                                    "prior_sell_submission_observed": (
                                        prior_status == "SELL_ORDERED"
                                    ),
                                    "sell_order_no": sell_order_no or "-",
                                    "sell_target_price_observed": (
                                        estimated_sell_price or "-"
                                    ),
                                    "sell_target_price_forbidden_for_pnl": True,
                                    "prior_partial_realized_qty": prior_partial_qty,
                                    "broker_holding_present": False,
                                    "successful_exchange": exchange,
                                    "broker_snapshot_at": broker_snapshot_at,
                                },
                            )
                        except Exception as exc:
                            log_error(
                                "🚨 [정기 동기화] 매도 영수증 누락 "
                                f"source-quality 이벤트 기록 실패: {exc}"
                            )
                        if target_stock is not None:
                            pending_runtime_target_removals.append(target_stock)
                        synced_count += 1
                    else:
                        print(
                            f"⚠️ [정기 동기화] {record.stock_name}({code}): {exchange} 거래소 잔고 조회 실패로 상태 변경 생략."
                        )

                else:
                    real_data = real_codes[code]
                    real_qty = _to_int(real_data.get("qty", 0))
                    if unfilled_snapshot_ok:
                        open_orders = open_qty_by_code.get(
                            code, {"open_buy_qty": 0, "open_sell_qty": 0}
                        )
                        with _with_state_lock():
                            for target in ACTIVE_TARGETS:
                                if str(target.get("code", "")).strip()[:6] == code:
                                    target.update(
                                        {
                                            "broker_holding_qty": real_qty,
                                            "broker_snapshot_at": broker_snapshot_at,
                                            "open_buy_qty": open_orders["open_buy_qty"],
                                            "open_sell_qty": open_orders[
                                                "open_sell_qty"
                                            ],
                                            "broker_reconciliation_source": (
                                                "kt00005_plus_ka10075"
                                            ),
                                        }
                                    )

                    raw_price = (
                        real_data.get("buy_price")
                        or real_data.get("purchase_price")
                        or real_data.get("pchs_avg_pric")
                        or 0
                    )
                    real_buy_uv = _to_int(raw_price)

                    if real_qty > 0 and _to_int(record.buy_qty) != real_qty:
                        print(
                            f"🔄 [정기 동기화] {record.stock_name} 수량 오차 교정 (기존: {_to_int(record.buy_qty)}주 ➡️ 실제: {real_qty}주)"
                        )
                        record.buy_qty = real_qty
                        with STATE_LOCK:
                            for t in ACTIVE_TARGETS:
                                if str(t.get("code", "")).strip()[:6] == code:
                                    t["buy_qty"] = real_qty

                    if real_buy_uv > 0 and record.buy_price != real_buy_uv:
                        print(
                            f"🔄 [정기 동기화] {record.stock_name} 매입단가 오차 교정 (기존: {record.buy_price}원 ➡️ 실제: {real_buy_uv}원)"
                        )
                        record.buy_price = real_buy_uv
                        with _with_state_lock():
                            for t in ACTIVE_TARGETS:
                                if str(t.get("code", "")).strip()[:6] == code:
                                    t["buy_price"] = real_buy_uv

                    if bool(record.scale_in_locked):
                        _reconcile_scale_in_lock(record, real_qty, real_buy_uv)

            # 2️⃣ [매수 누락 방어] DB엔 BUY_ORDERED 인데, 실제 잔고에 들어와 있는 경우 -> 샀음 (HOLDING)
            pending_records = (
                session.query(RecommendationHistory)
                .filter_by(status="BUY_ORDERED")
                .all()
            )

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in real_codes:
                    real_data = real_codes[code]
                    cur_qty = _to_int(real_data.get("qty", 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get("buy_price")
                            or real_data.get("purchase_price")
                            or real_data.get("pchs_avg_pric")
                            or 0
                        )
                        buy_uv = _to_int(raw_price)

                        print(
                            f"⚠️ [정기 동기화] {record.stock_name}({code}) 매수 체결 확인! HOLDING 강제 전환 (평단가 {buy_uv:,}원)"
                        )

                        record.status = "HOLDING"
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        if not record.buy_time:
                            record.buy_time = datetime.now()

                        with _with_state_lock():
                            for t in ACTIVE_TARGETS:
                                if str(t.get("code", "")).strip()[:6] == code:
                                    t["status"] = "HOLDING"
                                    t["buy_price"] = buy_uv
                                    t["buy_qty"] = cur_qty
                                    if not t.get("buy_time"):
                                        t["buy_time"] = record.buy_time
                                    if not t.get("holding_started_at"):
                                        t["holding_started_at"] = (
                                            t.get("buy_time") or record.buy_time
                                        )

                        synced_count += 1

            synced_count += _recover_missing_broker_holdings(session, real_codes)

    except Exception as exc:
        log_error(f"🚨 정기 계좌 동기화 DB 에러: {exc}")
    else:
        if pending_runtime_target_removals:
            removed_target_ids = {
                id(target) for target in pending_runtime_target_removals
            }
            with _with_state_lock():
                ACTIVE_TARGETS[:] = [
                    target
                    for target in ACTIVE_TARGETS
                    if id(target) not in removed_target_ids
                ]
        for event_args, event_kwargs in pending_sell_reconciliation_events:
            try:
                emit_pipeline_event(*event_args, **event_kwargs)
            except Exception as exc:
                log_error(
                    "🚨 [정기 동기화] 매도 영수증 누락 "
                    f"source-quality 이벤트 기록 실패: {exc}"
                )
        for code, reason in pending_manual_control_removals:
            _remove_manual_control_exclusion_for_completed_holding(code, reason=reason)

    if synced_count > 0:
        print(
            f"🔄 [정기 동기화 완료] 총 {synced_count}건의 웹소켓 누락 체결 상태를 바로잡았습니다."
        )
    else:
        pass  # 조용히 넘어갑니다. (로그 기록 안 함)
