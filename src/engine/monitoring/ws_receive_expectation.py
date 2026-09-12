"""Verified market-state receive diagnostics; never an execution-health waiver."""

from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Any, Mapping

KST = timezone(timedelta(hours=9))
CONTRACT_VERSION = "ws_market_state_receive_expectation_v2"
MARKET_SESSION_STATE_CONTRACT_VERSION = "kiwoom_0s_market_operation_v1"
VERIFIED_0S_QUIET_STATES = {
    ("KRX", "2"): "CALL_AUCTION",
    ("KRX", "c"): "CALL_AUCTION",
    ("NXT", "T"): "CALL_AUCTION",
}
ROUTES = {
    "KRX": "KRX",
    "krx_regular": "KRX",
    "krx_only": "KRX",
    "NXT": "NXT",
    "nxt_only": "NXT",
    "SOR": "SOR",
    "krx_nxt_integrated": "SOR",
}
ABSENCE_REASONS = {
    "",
    "none",
    "subscription_no_tick",
    "subscription_stale",
    "subscription_required_realtime_missing",
    "dashboard_snapshot_subscription_state_unavailable",
}


def _aware_kst(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _remaining_seconds(value: Any) -> int | None:
    token = str(value or "").strip()
    if len(token) != 6 or not token.isdigit():
        return None
    hours, minutes, seconds = int(token[:2]), int(token[2:4]), int(token[4:])
    if minutes >= 60 or seconds >= 60:
        return None
    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def _exchange_time(receipt: Mapping[str, Any], received_at: datetime) -> datetime | None:
    token = str(receipt.get("exchange_time_raw") or "").strip()
    if len(token) != 6 or not token.isdigit():
        return None
    hours, minutes, seconds = int(token[:2]), int(token[2:4]), int(token[4:])
    if hours >= 24 or minutes >= 60 or seconds >= 60:
        return None
    exchange_at = received_at.replace(
        hour=hours, minute=minutes, second=seconds, microsecond=0
    )
    return exchange_at if exchange_at <= received_at else None


def _verified_quiet_receipt(
    receipt: Any, *, scope: str, at: datetime
) -> tuple[bool, datetime | None, datetime | None]:
    if not isinstance(receipt, Mapping):
        return False, None, None
    received_at = _aware_kst(receipt.get("receive_timestamp"))
    raw_state = str(receipt.get("market_session_state_raw") or "")
    normalized_state = str(receipt.get("market_session_state_normalized") or "")
    if (
        receipt.get("market_session_state_contract_version")
        != MARKET_SESSION_STATE_CONTRACT_VERSION
        or receipt.get("runtime_effect") is not False
        or receipt.get("allowed_runtime_apply") is not False
        or receipt.get("market_session_state_known") is not True
        or str(receipt.get("market_session_state_market_scope") or "") != scope
        or VERIFIED_0S_QUIET_STATES.get((scope, raw_state)) != normalized_state
        or received_at is None
        or received_at > at
    ):
        return False, received_at, None
    remaining = _remaining_seconds(receipt.get("market_session_remaining_raw"))
    exchange_at = _exchange_time(receipt, received_at)
    if remaining is None or exchange_at is None:
        return False, received_at, None
    valid_until = exchange_at + timedelta(seconds=remaining)
    return at < valid_until, exchange_at, valid_until


def receive_expectation(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Use exact event/as-of time, route, and bounded verified state receipts."""
    result = {
        "contract_version": CONTRACT_VERSION,
        "scheduled_quiet": False,
        "reason": "missing_or_unverified_market_state_quiet_receipt",
        "resume_at": None,
        "required_market_scopes": [],
        "verified_quiet_scopes": [],
        "quiet_started_at": None,
    }
    if at is None or at.tzinfo is None:
        return result
    at = at.astimezone(KST)
    routes = row.get("registered_market_routes")
    if routes is None:
        routes = [
            row[key]
            for key in (
                "observed_market_route",
                "market_data_market_route",
                "market_route",
                "venue",
            )
            if row.get(key)
        ]
    if not isinstance(routes, (list, tuple)) or not routes:
        return result
    normalized = {ROUTES.get(str(route)) for route in routes}
    if None in normalized:
        return result
    required_scopes = set()
    for route in normalized:
        required_scopes.update({"KRX", "NXT"} if route == "SOR" else {route})
    result["required_market_scopes"] = sorted(required_scopes)
    states = row.get("market_session_states_by_scope")
    if not isinstance(states, Mapping):
        return result
    quiet_starts = []
    quiet_ends = []
    verified_scopes = []
    for scope in sorted(required_scopes):
        verified, started_at, valid_until = _verified_quiet_receipt(
            states.get(scope), scope=scope, at=at
        )
        if not verified:
            return result
        verified_scopes.append(scope)
        quiet_starts.append(started_at)
        quiet_ends.append(valid_until)
    quiet_started_at = max(quiet_starts)
    resume_at = min(quiet_ends)
    result.update(
        scheduled_quiet=True,
        reason="verified_market_session_call_auction_or_vi",
        resume_at=resume_at.isoformat(),
        verified_quiet_scopes=verified_scopes,
        quiet_started_at=quiet_started_at.isoformat(),
    )
    return result


def classify_receive_gap(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Preserve raw ages/observations while removing absence-only repair advice."""
    result = dict(row)
    # A persisted diagnostic is not a waiver after the opening boundary.
    prior_expectation = row.get("receive_expectation")
    if (
        isinstance(prior_expectation, dict)
        and prior_expectation.get("contract_version")
        in {CONTRACT_VERSION, "ws_opening_receive_expectation_v1"}
    ):
        prior_reason = str(row.get("repair_reason") or "")
        if (
            "observed_repair_reason" in row
            and prior_reason
            in {
                "verified_market_session_call_auction_or_vi",
                "scheduled_opening_auction_or_nxt_pause",
            }
            and row.get("repair_recommended") is False
            and row.get("recommended_repair") == "none"
        ):
            result["repair_reason"] = row["observed_repair_reason"]
            result["repair_recommended"] = row.get("observed_repair_recommended", False)
            result["recommended_repair"] = row.get(
                "observed_recommended_repair", "none"
            )
        if row.get("freshness_state") == "expected_market_quiet":
            result["freshness_state"] = row.get("observed_freshness_state", "unknown")
            result["trade_tick_quiet"] = row.get("observed_trade_tick_quiet", False)
    row = result
    expectation = receive_expectation(row, at)
    result["receive_expectation"] = expectation
    result["expected_market_quiet"] = False
    age = row.get("last_receive_age_sec")
    if age is not None:
        if (
            isinstance(age, bool)
            or not isinstance(age, (int, float))
            or not isfinite(age)
            or age < 0
        ):
            return result
        # A receive gap already stale before the pause is not explained by it.
        stale_after = row.get("stale_after_sec", 30.0)
        if (
            isinstance(stale_after, bool)
            or not isinstance(stale_after, (int, float))
            or not isfinite(stale_after)
            or stale_after <= 0
        ):
            return result
        if expectation["scheduled_quiet"]:
            quiet_started_at = _aware_kst(expectation.get("quiet_started_at"))
            if quiet_started_at is None:
                return result
            if at.astimezone(KST).timestamp() - age < (
                quiet_started_at.timestamp() - stale_after
            ):
                return result
    missing = row.get("required_realtime_missing_types", [])
    if (
        not expectation["scheduled_quiet"]
        or row.get("subscribed") is False
        or str(row.get("repair_reason") or "") not in ABSENCE_REASONS
        or not isinstance(missing, (list, tuple))
        or not all(isinstance(item, str) for item in missing)
        or set(missing) - {"0B", "0D"}
        or any(
            row.get(key)
            for key in (
                "connection_error",
                "subscription_error",
                "storage_error",
                "parse_error",
                "receive_age_contract_invalid",
            )
        )
        or any(
            row.get(key) is False
            for key in (
                "connected",
                "login_ok",
                "subscription_ack_ok",
                "storage_healthy",
            )
        )
    ):
        return result
    raw_state = str(row.get("freshness_state") or "")
    if raw_state not in {"no_tick", "stale", "fresh"}:
        return result
    if raw_state == "fresh" and not row.get("trade_tick_quiet") and not missing:
        return result
    result.update(
        observed_freshness_state=raw_state,
        observed_trade_tick_quiet=bool(row.get("trade_tick_quiet")),
        observed_repair_reason=row.get("repair_reason"),
        observed_repair_recommended=row.get("repair_recommended", False),
        observed_recommended_repair=row.get("recommended_repair", "none"),
        freshness_state="expected_market_quiet",
        expected_market_quiet=True,
        trade_tick_quiet=False,
        repair_recommended=False,
        repair_reason=expectation["reason"],
        recommended_repair="none",
    )
    return result
