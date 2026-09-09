"""Opening-gap receive diagnostics; never an executable-price or health waiver."""

from datetime import datetime, time, timedelta, timezone
from math import isfinite
from typing import Any, Mapping

KST = timezone(timedelta(hours=9))
CONTRACT_VERSION = "ws_opening_receive_expectation_v1"
ROUTES = {
    "KRX": "KRX",
    "krx_regular": "KRX",
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


def receive_expectation(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Use event/as-of time and explicit routes, never today's wall clock for history.

    No guaranteed continuous 0B/0D cadence is assumed in this opening gap.
    Other channels and explicit failures retain their independent contracts.
    """
    result = {
        "contract_version": CONTRACT_VERSION,
        "scheduled_quiet": False,
        "reason": "outside_opening_gap_or_unverified_route_time",
        "resume_at": None,
    }
    if at is None or at.tzinfo is None:
        return result
    at = at.astimezone(KST)
    if at.weekday() >= 5:
        return result
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
    end = time(9, 0, 30) if normalized == {"NXT"} else time(9, 0)
    if not time(8, 50) <= at.time() < end:
        return result
    result.update(
        scheduled_quiet=True,
        reason="scheduled_opening_auction_or_nxt_pause",
        resume_at=at.replace(
            hour=end.hour, minute=end.minute, second=end.second, microsecond=0
        ).isoformat(),
    )
    return result


def classify_receive_gap(row: Mapping[str, Any], at: datetime | None) -> dict[str, Any]:
    """Preserve raw ages/observations while removing absence-only repair advice."""
    result = dict(row)
    # A persisted diagnostic is not a waiver after the opening boundary.
    prior_expectation = row.get("receive_expectation")
    if (
        isinstance(prior_expectation, dict)
        and prior_expectation.get("contract_version") == CONTRACT_VERSION
    ):
        if (
            "observed_repair_reason" in row
            and row.get("repair_reason") == "scheduled_opening_auction_or_nxt_pause"
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
            local = at.astimezone(KST)
            pre_pause_cutoff = (
                local.replace(hour=8, minute=50, second=0, microsecond=0).timestamp()
                - stale_after
            )
            if local.timestamp() - age < pre_pause_cutoff:
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
