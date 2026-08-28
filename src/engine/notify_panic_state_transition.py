"""Send Telegram notices for panic and market-weakness transitions."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib import parse, request

from src.database.db_manager import DBManager
from src.utils.constants import CONFIG_PATH, DEV_PATH, PROJECT_ROOT

DEFAULT_STATE_FILE = PROJECT_ROOT / "tmp" / "panic_state_telegram_notify_state.json"
DEFAULT_MARKET_WEAKNESS_STATE_FILE = (
    PROJECT_ROOT / "tmp" / "market_weakness_observer_state.json"
)

SELL_ACTIVE_STATES = {"PANIC_SELL"}
SELL_RELEASE_STATES = {"NORMAL", "RECOVERY_WATCH", "RECOVERY_CONFIRMED"}
SELL_RESTART_SUPPRESS_AFTER_RELEASE_SEC = 10 * 60
MARKET_WEAKNESS_ACTIVE_STATES = {"BROAD_WEAKNESS", "SINGLE_MARKET_WEAKNESS"}
MARKET_WEAKNESS_RELEASE_STATE = "RECOVERY_EVIDENCE"
MARKET_WEAKNESS_BOUNDARY_STATE = "NEAR_WEAKNESS_BOUNDARY"
MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS = 2
MARKET_WEAKNESS_RELEASE_OBSERVATIONS = 3
MARKET_WEAKNESS_MAX_REPORT_LAG_SEC = 180
MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC = 60
MARKET_WEAKNESS_SEVERITY = {
    "SINGLE_MARKET_WEAKNESS": 1,
    "BROAD_WEAKNESS": 2,
}


def _report_session_key(report_file: Path, report: dict) -> str:
    for key in ("target_date", "date", "trade_date"):
        value = str(report.get(key) or "").strip()
        if value:
            return value[:10]
    stem = report_file.stem
    for prefix in (
        "panic_sell_defense_",
        "market_panic_breadth_",
    ):
        if stem.startswith(prefix):
            return stem.replace(prefix, "", 1)[:10]
    return ""


def _previous_session_key(previous: dict) -> str:
    value = str(
        previous.get("session_key") or previous.get("target_date") or ""
    ).strip()
    if value:
        return value[:10]
    report_file = str(previous.get("report_file") or "")
    stem = Path(report_file).stem
    for prefix in ("panic_sell_defense_",):
        if stem.startswith(prefix):
            return stem.replace(prefix, "", 1)[:10]
    return ""


def _load_telegram_config() -> tuple[str, str]:
    config_path = CONFIG_PATH if CONFIG_PATH.exists() else DEV_PATH
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except OSError:
        return "", ""
    token = str(config.get("TELEGRAM_TOKEN") or "").strip()
    admin_id = str(config.get("ADMIN_ID") or "").strip()
    return token, admin_id


def _load_report(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_state(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _send_telegram(token: str, chat_id: str, message: str) -> None:
    data = parse.urlencode({"chat_id": chat_id, "text": message}).encode("utf-8")
    req = request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        response.read()


def _load_all_chat_ids() -> list[str]:
    try:
        ids = DBManager().get_telegram_chat_ids()
    except Exception:
        return []
    result: list[str] = []
    for chat_id in ids:
        text = str(chat_id or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _target_chat_ids(audience: str, admin_id: str) -> list[str]:
    if audience == "admin":
        return [admin_id] if admin_id else []
    ids = _load_all_chat_ids()
    if admin_id and admin_id not in ids:
        ids.insert(0, admin_id)
    return ids


def _state_value(kind: str, report: dict) -> str:
    if kind == "panic_sell":
        return str(report.get("panic_state") or "UNKNOWN")
    raise ValueError(f"unsupported kind: {kind}")


def _state_phase(kind: str, value: str) -> str:
    if kind == "panic_sell":
        if value in SELL_ACTIVE_STATES:
            return "active"
        if value in SELL_RELEASE_STATES:
            return "released"
        return "unknown"
    return "unknown"


def _transition(
    previous_phase: str | None,
    current_phase: str,
    *,
    force: bool,
    current_value: str = "",
) -> str:
    if force:
        return "start" if current_phase == "active" else "release"
    previous_effective_phase = (
        "active" if previous_phase == "release_pending" else previous_phase
    )
    if previous_effective_phase != "active" and current_phase == "active":
        return "start"
    if previous_effective_phase == "active" and current_phase == "released":
        if previous_phase != "release_pending":
            return "release_pending"
        return "release"
    return "none"


SELL_CONTEXT_PRIORITY = {
    "panic_sell_watch": 0,
    "market_breadth_watch": 1,
    "microstructure_panic": 2,
    "stop_loss_cluster": 3,
    "market_and_stop_loss": 4,
    "market_and_micro_panic": 4,
}


def _safe_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: object, default: int = 0) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else default


def _parse_iso_timestamp(value: object) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        from datetime import datetime

        return datetime.fromisoformat(text).timestamp()
    except (TypeError, ValueError):
        return None


def _market_weakness_observation(report: dict) -> dict:
    direct = report.get("market_weakness_observation")
    if isinstance(direct, dict):
        return dict(direct)
    micro = report.get("microstructure_market_context")
    if isinstance(micro, dict) and isinstance(
        micro.get("market_weakness_observation"), dict
    ):
        return dict(micro["market_weakness_observation"])
    return {}


def _effective_market_weakness_observation(
    report_file: Path, report: dict
) -> dict:
    observation = _market_weakness_observation(report)
    if not observation:
        return {}
    session_key = _report_session_key(report_file, report)
    observation_session = str(observation.get("target_date") or "")[:10]
    report_as_of = _parse_iso_timestamp(report.get("as_of"))
    observation_as_of = _parse_iso_timestamp(observation.get("as_of"))
    lag_sec = (
        report_as_of - observation_as_of
        if report_as_of is not None and observation_as_of is not None
        else None
    )
    source_ready = bool(observation.get("source_quality_ready"))
    identity_valid = bool(str(observation.get("observation_id") or "").strip())
    raw_state = str(observation.get("raw_state") or "UNKNOWN")
    release_margin = (
        observation.get("release_margin")
        if isinstance(observation.get("release_margin"), dict)
        else {}
    )
    authority_valid = bool(
        observation.get("decision_authority")
        == "source_quality_observation_only"
        and observation.get("runtime_effect") is False
        and observation.get("allowed_runtime_apply") is False
    )
    state_contract_valid = bool(
        raw_state
        in MARKET_WEAKNESS_ACTIVE_STATES
        | {MARKET_WEAKNESS_RELEASE_STATE, MARKET_WEAKNESS_BOUNDARY_STATE, "UNKNOWN"}
        and (
            raw_state != MARKET_WEAKNESS_RELEASE_STATE
            or release_margin.get("passed") is True
        )
    )
    same_session = bool(
        session_key and observation_session and session_key == observation_session
    )
    fresh = bool(
        lag_sec is not None
        and 0.0 <= lag_sec <= MARKET_WEAKNESS_MAX_REPORT_LAG_SEC
    )
    observation["notifier_source_gate"] = {
        "same_session": same_session,
        "lag_sec": round(lag_sec, 3) if lag_sec is not None else None,
        "max_lag_sec": MARKET_WEAKNESS_MAX_REPORT_LAG_SEC,
        "fresh": fresh,
        "source_quality_ready": source_ready,
        "identity_valid": identity_valid,
        "authority_valid": authority_valid,
        "state_contract_valid": state_contract_valid,
        "passed": bool(
            source_ready
            and identity_valid
            and same_session
            and fresh
            and authority_valid
            and state_contract_valid
        ),
    }
    if not observation["notifier_source_gate"]["passed"]:
        original_id = str(observation.get("observation_id") or "missing")
        observation["observation_id"] = f"{original_id}:source_blocked"
        observation["raw_state"] = "UNKNOWN"
    return observation


def _fmt_pct(value: object) -> str:
    numeric = _safe_float(value)
    return f"{numeric:+.2f}%" if numeric is not None else "확인중"


def _market_weakness_message(
    observation: dict, transition: str, state: dict
) -> str:
    raw_state = str(observation.get("raw_state") or "UNKNOWN")
    evidence = (
        observation.get("evidence")
        if isinstance(observation.get("evidence"), dict)
        else {}
    )
    indices = (
        evidence.get("market_index_change_pct")
        if isinstance(evidence.get("market_index_change_pct"), dict)
        else {}
    )
    if transition == "release":
        title = "✅ 시장 약세 관찰 해제"
        body = "약세 임계치에서 충분히 벗어난 회복 근거가 3회 연속 확인되었습니다."
    elif transition == "update":
        title = "🔄 시장 전반 약세로 확산"
        body = "한쪽 시장 약세가 지수·업종 전반의 약세로 확산되었습니다."
    elif transition == "status":
        title = "ℹ️ 시장 약세 관찰 상태"
        body = "현재 source-only 시장 약세 관찰 상태입니다."
    elif raw_state == "BROAD_WEAKNESS":
        title = "🟠 시장 전반 약세 지속"
        body = "지수와 시장 breadth의 약세가 2회 연속 확인되었습니다."
    else:
        title = "⚠️ 한쪽 시장 약세 지속 관찰"
        body = "한쪽 시장 약세와 이를 뒷받침하는 하락 breadth가 2회 연속 확인되었습니다."
    return "\n".join(
        [
            title,
            body,
            f"- 지수: KOSPI {_fmt_pct(indices.get('KOSPI'))} / KOSDAQ {_fmt_pct(indices.get('KOSDAQ'))}",
            (
                "- breadth: 업종 하락 "
                f"{_fmt_pct(evidence.get('industry_down_ratio_pct'))} / "
                "시장별 최대 하락종목 비율 "
                f"{_fmt_pct(evidence.get('max_stock_fall_ratio_pct'))}"
            ),
            (
                "- 확인 누적: 약세 "
                f"{_safe_int(state.get('weak_streak'))}/{MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS}회 · "
                "회복 "
                f"{_safe_int(state.get('recovery_streak'))}/{MARKET_WEAKNESS_RELEASE_OBSERVATIONS}회"
            ),
            "- 대응: 현재는 관찰·반사실 수집만 수행",
            "- 자동매매 변경: 없음",
        ]
    )


def _deliver_market_weakness_pending(
    state: dict,
    *,
    state_file: Path,
    audience: str,
    now: float,
) -> str | None:
    current = state.get("market_weakness")
    if not isinstance(current, dict):
        return None
    pending = current.get("pending_notification")
    if not isinstance(pending, dict):
        return None
    token, admin_id = _load_telegram_config()
    if not token:
        return "missing_config"
    chat_ids = _target_chat_ids(audience, admin_id)
    if not chat_ids:
        return "missing_recipients"
    message = str(pending.get("message") or "")
    sent = 0
    for chat_id in chat_ids:
        try:
            _send_telegram(token, chat_id, message)
            sent += 1
        except Exception:
            continue
    if sent <= 0:
        return "send_failed"
    current["last_notification"] = {
        "transition": pending.get("transition"),
        "audience": audience,
        "sent_count": sent,
        "sent_at_ts": now,
        "state": pending.get("state"),
    }
    current.pop("pending_notification", None)
    state["market_weakness"] = current
    _write_state(state_file, state)
    return "sent"


def _notify_market_weakness_from_report(
    report_file: Path,
    report: dict,
    *,
    audience: str,
    state_file: Path,
    force: bool,
    now_ts: float | None,
    notification_enabled: bool,
) -> str:
    observation = _effective_market_weakness_observation(report_file, report)
    if not observation:
        return "missing_observation"
    raw_state = str(observation.get("raw_state") or "UNKNOWN")
    observation_id = str(observation.get("observation_id") or "")
    current_session_key = _report_session_key(report_file, report)
    state = _load_state(state_file)
    previous = (
        state.get("market_weakness")
        if isinstance(state.get("market_weakness"), dict)
        else {}
    )
    if _previous_session_key(previous) != current_session_key:
        previous = {}
    now = time.time() if now_ts is None else now_ts
    if (
        not force
        and observation_id
        and observation_id == str(previous.get("last_observation_id") or "")
    ):
        pending_status = (
            _deliver_market_weakness_pending(
                state, state_file=state_file, audience=audience, now=now
            )
            if notification_enabled
            else None
        )
        if not notification_enabled:
            previous.pop("pending_notification", None)
            state["market_weakness"] = previous
            _write_state(state_file, state)
            return "state_updated_notify_disabled"
        return pending_status or "duplicate_observation"

    previous_as_of = _parse_iso_timestamp(previous.get("last_observation_as_of"))
    current_as_of = _parse_iso_timestamp(observation.get("as_of"))
    observation_spacing_sec = (
        current_as_of - previous_as_of
        if current_as_of is not None and previous_as_of is not None
        else None
    )
    if (
        not force
        and previous
        and observation_spacing_sec is not None
        and observation_spacing_sec < MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC
    ):
        pending_status = (
            _deliver_market_weakness_pending(
                state, state_file=state_file, audience=audience, now=now
            )
            if notification_enabled
            else None
        )
        return pending_status or "observation_too_close"

    previous_phase = str(previous.get("phase") or "released")
    was_active = previous_phase in {"active", "release_pending"}
    previous_raw_state = str(previous.get("raw_state") or "")
    weak_streak = _safe_int(previous.get("weak_streak"), 0)
    recovery_streak = _safe_int(previous.get("recovery_streak"), 0)
    active_scope = str(previous.get("active_scope") or "")
    transition = "none"

    if raw_state in MARKET_WEAKNESS_ACTIVE_STATES:
        weak_streak = (
            weak_streak + 1
            if previous_raw_state in MARKET_WEAKNESS_ACTIVE_STATES
            else 1
        )
        recovery_streak = 0
        if was_active:
            phase = "active"
            if MARKET_WEAKNESS_SEVERITY.get(raw_state, 0) > MARKET_WEAKNESS_SEVERITY.get(
                active_scope, 0
            ):
                transition = "update"
                active_scope = raw_state
        elif weak_streak >= MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS:
            phase = "active"
            transition = "start"
            active_scope = raw_state
        else:
            phase = "activation_pending"
            active_scope = ""
    elif raw_state == MARKET_WEAKNESS_RELEASE_STATE:
        weak_streak = 0
        if was_active:
            recovery_streak += 1
            if recovery_streak >= MARKET_WEAKNESS_RELEASE_OBSERVATIONS:
                phase = "released"
                transition = "release"
                active_scope = ""
            else:
                phase = "release_pending"
        else:
            phase = "released"
            recovery_streak = 0
            active_scope = ""
    elif raw_state == MARKET_WEAKNESS_BOUNDARY_STATE:
        weak_streak = 0
        recovery_streak = 0
        phase = "active" if was_active else "released"
    else:
        weak_streak = weak_streak if was_active else 0
        recovery_streak = 0
        phase = "active" if was_active else "unknown"

    next_state = {
        "phase": phase,
        "raw_state": raw_state,
        "state": active_scope or raw_state,
        "active_scope": active_scope,
        "weak_streak": weak_streak,
        "recovery_streak": recovery_streak,
        "last_observation_id": observation_id,
        "last_observation_as_of": observation.get("as_of"),
        "last_source_gate": observation.get("notifier_source_gate") or {},
        "session_key": current_session_key,
        "updated_at_ts": now,
        "report_file": str(report_file),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    if isinstance(previous.get("last_notification"), dict):
        next_state["last_notification"] = previous["last_notification"]
    if isinstance(previous.get("pending_notification"), dict):
        next_state["pending_notification"] = previous["pending_notification"]
    if force:
        transition = "status"
    if notification_enabled and transition in {"start", "update", "release", "status"}:
        next_state["pending_notification"] = {
            "transition": transition,
            "state": raw_state,
            "message": _market_weakness_message(observation, transition, next_state),
            "created_at_ts": now,
        }
    elif not notification_enabled:
        next_state.pop("pending_notification", None)
    state["market_weakness"] = next_state
    _write_state(state_file, state)
    if not notification_enabled:
        return "state_updated_notify_disabled"
    pending_status = _deliver_market_weakness_pending(
        state, state_file=state_file, audience=audience, now=now
    )
    if pending_status is not None:
        return pending_status
    if raw_state == "UNKNOWN":
        return "source_quality_blocked"
    if phase == "activation_pending":
        return "activation_pending"
    if phase == "release_pending":
        return "release_pending"
    if was_active and raw_state == MARKET_WEAKNESS_BOUNDARY_STATE:
        return "weakness_latched"
    return "no_transition"


def _score_bar(value: object) -> str:
    numeric = _safe_float(value)
    if numeric is None:
        return "░░░░░░░░░░░░ 확인중"
    score = max(0.0, min(1.0, numeric))
    total = 12
    filled = int(round(score * total))
    empty = total - filled
    if score >= 0.75:
        label = "위험 높음"
        icon = "🔴"
    elif score >= 0.45:
        label = "주의"
        icon = "🟠"
    else:
        label = "낮음"
        icon = "🟢"
    pct = int(round(score * 100))
    return f"{icon} {'▰' * filled}{'▱' * empty} {pct}% · {label}"


def _sell_context_label(report: dict) -> str:
    reasons = [str(item or "") for item in (report.get("panic_state_reasons") or [])]
    micro_context = (
        report.get("microstructure_market_context")
        if isinstance(report.get("microstructure_market_context"), dict)
        else {}
    )
    market_breadth_only = any(
        "market breadth risk-off watch without panic confirmation" in item
        for item in reasons
    )
    market_breadth_risk_off = bool(
        micro_context.get("market_panic_breadth_risk_off_advisory")
    )
    single_market_risk_off = bool(
        micro_context.get("market_panic_breadth_single_market_risk_off_advisory")
    )
    micro_panic = (
        int(
            (report.get("microstructure_detector") or {}).get("panic_signal_count", 0)
            or 0
        )
        > 0
    )
    panic_metrics = (
        report.get("panic_metrics")
        if isinstance(report.get("panic_metrics"), dict)
        else {}
    )
    stop_cluster = bool(panic_metrics.get("panic_detected"))
    market_weak = (
        market_breadth_risk_off or single_market_risk_off or market_breadth_only
    )
    if market_weak and stop_cluster:
        return "market_and_stop_loss"
    if market_weak and micro_panic:
        return "market_and_micro_panic"
    if market_weak:
        return "market_breadth_watch"
    if stop_cluster:
        return "stop_loss_cluster"
    if micro_panic:
        return "microstructure_panic"
    return "panic_sell_watch"


def _sell_context_escalated(previous_context: str | None, current_context: str) -> bool:
    previous_score = SELL_CONTEXT_PRIORITY.get(str(previous_context or ""), -1)
    current_score = SELL_CONTEXT_PRIORITY.get(current_context, 0)
    return current_score > previous_score


def _sell_notice_copy(context: str) -> tuple[str, str, str]:
    if context == "market_breadth_watch":
        return (
            "⚠️ 시장 전반 약세 주의",
            "지수와 업종 전반이 약해졌습니다. 아직 개별 종목의 급한 매도 흐름이나 반복 청산은 뚜렷하지 않습니다.",
            "시장 전반 약세 관찰",
        )
    if context == "stop_loss_cluster":
        return (
            "⚠️ 손실 방어 구간 진입",
            "최근 보유/감시 종목에서 손실 확정성 청산이 평소보다 많이 발생했습니다. 새 진입은 보수적으로 보고 기존 안전장치는 유지합니다.",
            "손실 방어 구간",
        )
    if context == "microstructure_panic":
        return (
            "⚠️ 개별 종목 급매도 주의",
            "일부 종목에서 짧은 시간에 매도 압력이 강해졌습니다. 무리한 신규 진입보다 가격 안정 여부를 먼저 확인할 구간입니다.",
            "개별 종목 급매도 감지",
        )
    if context == "market_and_stop_loss":
        return (
            "⚠️ 시장 약세 + 손실 방어 구간",
            "시장 전반이 약한 가운데 손실 확정성 청산도 늘었습니다. 신규 진입은 더 보수적으로 보고, 자동매매 설정은 바꾸지 않습니다.",
            "시장 약세와 손실 방어 동시 감지",
        )
    if context == "market_and_micro_panic":
        return (
            "⚠️ 시장 약세 + 급매도 확산 주의",
            "시장 전반이 약한 가운데 일부 종목의 매도 압력도 강해졌습니다. 가격 안정 신호가 확인되기 전까지 추격 진입은 피해야 합니다.",
            "시장 약세와 개별 급매도 동시 감지",
        )
    return (
        "⚠️ 패닉셀 주의",
        "시장에 급한 매도세가 감지되었습니다. 신규 진입은 평소보다 더 보수적으로 볼 구간입니다.",
        "패닉셀 관찰",
    )


def _message_for_sell(report: dict, transition: str) -> str:
    micro = (
        report.get("microstructure_detector")
        if isinstance(report.get("microstructure_detector"), dict)
        else {}
    )
    micro_metrics = (
        micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    )
    if transition == "release":
        title = "✅ 패닉셀 경보 해제"
        body = "급한 매도세가 진정되어 패닉셀 관찰을 종료합니다."
        intensity_line = "- 해제 상태\n  🟢 회복 확인 · 신규 자동매매 변경 없음"
    elif transition == "status":
        title = "ℹ️ 패닉셀 알림 테스트"
        body = "현재 패닉셀 알림 상태를 관리자 테스트로 확인합니다."
        intensity_line = (
            f"- 체감 강도\n  {_score_bar(micro_metrics.get('max_panic_score'))}"
        )
    else:
        context = _sell_context_label(report)
        title, body, stage_label = _sell_notice_copy(context)
        if transition == "update":
            title = title.replace("⚠️", "🔄", 1)
        intensity_line = (
            f"- 체감 강도\n  {_score_bar(micro_metrics.get('max_panic_score'))}"
        )
    return "\n".join(
        [
            title,
            body,
            (
                f"- 현재 단계\n  {stage_label}"
                if transition not in {"release", "status"}
                else ""
            ),
            intensity_line,
            "- 자동매매 변경: 없음",
        ]
    ).replace("\n\n", "\n")


def _build_message(kind: str, report: dict, transition: str) -> str:
    if kind != "panic_sell":
        raise ValueError(f"unsupported kind: {kind}")
    return _message_for_sell(report, transition)


def notify_from_report(
    report_file: Path,
    *,
    kind: str,
    audience: str = "all",
    state_file: Path | None = None,
    force: bool = False,
    now_ts: float | None = None,
    send_enabled: bool = True,
) -> str:
    if state_file is None:
        state_file = (
            DEFAULT_MARKET_WEAKNESS_STATE_FILE
            if kind == "market_weakness"
            else DEFAULT_STATE_FILE
        )
    notification_enabled = send_enabled and str(
        os.getenv("KORSTOCKSCAN_PANIC_STATE_TELEGRAM_NOTIFY_ENABLED", "true")
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    report = _load_report(report_file)
    if not report:
        return "missing_report"
    if kind == "market_weakness":
        return _notify_market_weakness_from_report(
            report_file,
            report,
            audience=audience,
            state_file=state_file,
            force=force,
            now_ts=now_ts,
            notification_enabled=notification_enabled,
        )
    if not notification_enabled:
        return "disabled"
    current_value = _state_value(kind, report)
    current_phase = _state_phase(kind, current_value)
    if current_phase == "unknown":
        return "unknown_state"

    state = _load_state(state_file)
    previous = state.get(kind) if isinstance(state.get(kind), dict) else {}
    previous_phase = str(previous.get("phase") or "") or None
    current_session_key = _report_session_key(report_file, report)
    previous_session_key = (
        _previous_session_key(previous) if isinstance(previous, dict) else ""
    )
    stale_previous_session = (
        not force
        and previous_phase in {"active", "release_pending"}
        and bool(current_session_key)
        and previous_session_key != current_session_key
    )
    if stale_previous_session:
        previous_phase = None
    previous_value = (
        str(previous.get("state") or "") if isinstance(previous, dict) else ""
    )
    transition = _transition(
        previous_phase, current_phase, force=force, current_value=current_value
    )
    current_context = _sell_context_label(report) if kind == "panic_sell" else ""
    previous_context = (
        str(previous.get("context_label") or "") if isinstance(previous, dict) else ""
    )
    if (
        kind == "panic_sell"
        and transition == "none"
        and previous_phase == "active"
        and current_phase == "active"
        and (bool(previous_context) or previous_value == current_value)
        and _sell_context_escalated(previous_context, current_context)
    ):
        transition = "update"

    now = time.time() if now_ts is None else now_ts
    previous_last_notification = (
        previous.get("last_notification")
        if isinstance(previous.get("last_notification"), dict)
        else {}
    )
    suppress_sell_restart_after_release = False
    if (
        not force
        and kind == "panic_sell"
        and transition == "start"
        and previous_phase == "released"
    ):
        previous_release_ts = _safe_float(previous_last_notification.get("sent_at_ts"))
        suppress_sell_restart_after_release = (
            previous_last_notification.get("transition") == "release"
            and bool(current_session_key)
            and previous_session_key == current_session_key
            and previous_release_ts is not None
            and now - previous_release_ts <= SELL_RESTART_SUPPRESS_AFTER_RELEASE_SEC
        )
        if suppress_sell_restart_after_release:
            transition = "restart_suppressed_after_release"

    if transition == "restart_suppressed_after_release":
        next_phase = previous_phase or "released"
        next_value = previous_value or current_value
    else:
        next_phase = (
            "release_pending" if transition == "release_pending" else current_phase
        )
        next_value = current_value
    next_state = {
        "phase": next_phase,
        "state": next_value,
        "session_key": current_session_key,
        "updated_at_ts": now,
        "report_file": str(report_file),
    }
    if kind == "panic_sell":
        next_state["context_label"] = current_context
    if isinstance(previous, dict) and isinstance(
        previous.get("last_notification"), dict
    ):
        next_state["last_notification"] = previous["last_notification"]

    if transition in {"none", "release_pending", "restart_suppressed_after_release"}:
        state[kind] = next_state
        _write_state(state_file, state)
        if transition == "restart_suppressed_after_release":
            return "restart_suppressed_after_release"
        if stale_previous_session and current_phase == "released":
            return "stale_previous_active_reset"
        return "release_pending" if transition == "release_pending" else "no_transition"

    token, admin_id = _load_telegram_config()
    if not token:
        return "missing_config"
    chat_ids = _target_chat_ids(audience, admin_id)
    if not chat_ids:
        return "missing_recipients"

    message = _build_message(kind, report, transition)
    sent = 0
    for chat_id in chat_ids:
        try:
            _send_telegram(token, chat_id, message)
            sent += 1
        except Exception:
            continue
    if sent <= 0:
        return "send_failed"
    next_state["last_notification"] = {
        "transition": transition,
        "audience": audience,
        "sent_count": sent,
        "sent_at_ts": now,
        "state": current_value,
    }
    state[kind] = next_state
    _write_state(state_file, state)
    return "sent"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Notify Telegram users for panic or market-weakness transitions."
    )
    parser.add_argument("--report-file", required=True)
    parser.add_argument(
        "--kind", choices=["panic_sell", "market_weakness"], required=True
    )
    parser.add_argument("--audience", choices=["all", "admin"], default="all")
    parser.add_argument("--state-file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send a status notice even without a transition.",
    )
    parser.add_argument(
        "--observe-only",
        action="store_true",
        help="Update the market-weakness state without sending Telegram.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    status = notify_from_report(
        Path(args.report_file),
        kind=args.kind,
        audience=args.audience,
        state_file=Path(args.state_file) if args.state_file else None,
        force=bool(args.force),
        send_enabled=not bool(args.observe_only),
    )
    print(
        f"[INFO] panic state Telegram notify status={status} kind={args.kind} audience={args.audience}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
