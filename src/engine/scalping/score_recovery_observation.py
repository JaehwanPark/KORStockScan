"""Pure pre-decision observation contract; no entry/order or policy authority."""

from __future__ import annotations

import hashlib
import json
import math

SCHEMA = "score_recovery_observation_v1"


def finite(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def observation_fields(
    *,
    action,
    score,
    decision,
    probe,
    latency_state,
    policy,
    source_blocked,
    scope,
    reference_price,
):
    """Record a conservative rise/rebound cohort even when the owner is OFF.

    Membership is not a runtime eligibility decision. All normal entry/submit
    checks still run independently, including any explicit owner veto.
    """
    values = {
        key: finite(policy.get(key))
        for key in (
            "min_score",
            "max_score",
            "min_buy_pressure",
            "min_tick_accel",
            "min_micro_vwap_bp",
        )
    }
    observed = {
        key: finite(probe.get(key))
        for key in ("buy_pressure", "tick_accel", "micro_vwap_bp")
    }
    score = finite(score)
    reference_price = finite(reference_price)
    complete = all(
        value is not None for value in [*values.values(), *observed.values(), score]
    )
    evidence = decision.get("evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    venue = str(scope.get("effective_venue") or "")
    session = str(scope.get("market_session_bucket") or "")
    scope_valid = {
        "KRX": "krx_regular",
        "NXT": "nxt",
        "PREMARKET_KRX_LIKE": "krx_like_premarket",
    }.get(venue) == session
    quality = bool(
        decision.get("ai_parse_ok") is True
        and not decision.get("ai_fallback_score_50")
        and not source_blocked
        and scope_valid
        and reference_price is not None
        and reference_price > 0
        and probe.get("minute_candle_window_fresh") is True
        and probe.get("micro_vwap_available") is True
        and latency_state in {"SAFE", "CAUTION"}
        and str(decision.get("decision_quality_contract_status") or "")
        not in {"semantic_rejected", "invalid"}
        and str(evidence.get("adverse_risk") or "") != "blocking"
    )
    historical_match = bool(
        complete
        and quality
        and str(action).upper() in {"WAIT", "WAIT_REQUOTE"}
        and 60 <= score <= 74
        and values["min_score"] <= score <= values["max_score"]
        and observed["buy_pressure"] >= max(50.0, values["min_buy_pressure"])
        and observed["tick_accel"] >= max(0.0, values["min_tick_accel"])
        and observed["micro_vwap_bp"] > max(0.0, values["min_micro_vwap_bp"])
    )
    # The score-selected cohort is retained as historical provenance only.
    # Its membership must not feed a new tuning candidate.
    eligible = False
    encoded = json.dumps(
        {**values, "venue": venue, "session": session},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return {
        "score_recovery_observation_schema": SCHEMA,
        "score_recovery_observation_eligible": eligible,
        "score_recovery_observation_policy_hash": hashlib.sha256(
            encoded.encode("ascii")
        ).hexdigest(),
        "score_recovery_observation_policy": encoded,
        "score_recovery_observation_reason": "ai_score_tuning_retired",
        "score_recovery_observation_decision_authority": "diagnostic_only",
        "score_recovery_observation_historical_match": historical_match,
        "score_recovery_observation_score_source_state": (
            "missing_or_invalid" if score is None else "observed_diagnostic_only"
        ),
        "score_recovery_observation_runtime_effect": False,
        "score_recovery_observation_reference_price": reference_price,
    }


def eligible_observation(row: dict) -> bool:
    """Require producer-owned membership, not an inferred historical BUY."""
    encoded = row.get("score_recovery_observation_policy")
    if not isinstance(encoded, str):
        return False
    try:
        policy = json.loads(encoded)
        if not isinstance(policy, dict) or any(
            finite(policy.get(key)) is None
            for key in (
                "min_score",
                "max_score",
                "min_buy_pressure",
                "min_tick_accel",
                "min_micro_vwap_bp",
            )
        ):
            return False
    except (ValueError, TypeError):
        return False
    return bool(
        row.get("score_recovery_observation_schema") == SCHEMA
        and row.get("score_recovery_observation_eligible") in (True, "True", "true")
        and row.get("score_recovery_observation_runtime_effect")
        in (False, "False", "false")
        and bool(row.get("candidate_id"))
        and bool(row.get("record_id"))
        and policy.get("venue") in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
        and {
            "KRX": "krx_regular",
            "NXT": "nxt",
            "PREMARKET_KRX_LIKE": "krx_like_premarket",
        }.get(policy.get("venue"))
        == policy.get("session")
        and (finite(row.get("score_recovery_observation_reference_price")) or 0) > 0
        and hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        == row.get("score_recovery_observation_policy_hash")
    )


def score_recovery_cohort_member(row: dict) -> bool:
    if "score_recovery_observation_schema" in row:
        # A known invalid new observation cannot fall back to an applied marker.
        return eligible_observation(row)
    return row.get("has_score65_74_probe") is True


def observation_cohort_valid(metrics: dict) -> bool:
    hashes = metrics.get("score60_74_observation_policy_hashes", [])
    if not isinstance(hashes, list):
        return False
    if any(
        not isinstance(value, str)
        or len(value) != 64
        or any(c not in "0123456789abcdef" for c in value)
        for value in hashes
    ):
        return False
    return len(set(hashes)) <= 1


def condition_feasibility(metrics: dict, sample_floor: int) -> dict:
    """Preserve historical score-cohort evidence without a tuning decision."""
    count = finite(metrics.get("score60_74_cost_adjusted_sample_count")) or 0
    net = finite(metrics.get("score60_74_avg_cost_adjusted_expected_ev_pct"))
    return {
        "schema": "score_recovery_condition_feasibility_v1",
        "state": "retired_uncalibrated_ai_score_tuning",
        "sample_count": int(count),
        "sample_floor": sample_floor,
        "primary_metric": "cost_adjusted_counterfactual_ev_pct",
        "baseline": "no_entry_zero_exposure_counterfactual_not_realized_pnl",
        "net_ev_pct": net,
        "legacy_absolute_ev_floor_pct": 2.0,
        "success_probability": None,
        "indefinite_wait_appropriate": False,
        "next_action": "archive_diagnostic_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
