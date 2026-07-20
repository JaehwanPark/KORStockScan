"""Source-only rising-missed selection prior adapter.

This module consumes the PREOPEN-verified scalp sim policy catalog and returns
ranking hints for scanner candidate ordering. It never changes order authority,
thresholds, one-share scout allow/block decisions, or broker guards.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

POLICY_ENV_KEYS = (
    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_FILE",
    "SCALP_SIM_AUTO_POLICY_FILE",
)

VALID_RECOMMENDATIONS = {
    "positive_prior",
    "recheck_prior",
    "hold_sample",
    "quality_risk",
    "loss_filter",
    "source_quality_blocked",
}

RECOMMENDATION_SCORE_DELTA = {
    "positive_prior": 20.0,
    "recheck_prior": 8.0,
    "hold_sample": 0.0,
    "quality_risk": -8.0,
    "loss_filter": -20.0,
    "source_quality_blocked": -30.0,
}

_CATALOG_CACHE: dict[str, Any] = {}


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "rising_missed_selection_prior_key": "-",
        "rising_missed_selection_recommendation": "unavailable",
        "rising_missed_selection_confidence": "none",
        "rising_missed_selection_score_delta": 0.0,
        "rising_missed_selection_rank_reason": reason,
        "rising_missed_selection_match_type": "none",
        "rising_missed_selection_runtime_effect": False,
        "rising_missed_selection_allowed_runtime_apply": False,
    }


def _policy_path(policy_file: str | os.PathLike[str] | None = None) -> str:
    explicit = str(policy_file or "").strip()
    if explicit:
        return explicit
    for key in POLICY_ENV_KEYS:
        value = str(os.getenv(key) or "").strip()
        if value:
            return value
    return ""


def clear_selection_prior_cache() -> None:
    """Clear the module cache. Intended for tests."""
    _CATALOG_CACHE.clear()


def _safe_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def _score_bucket(value: Any) -> str:
    score = _safe_float(value)
    if score is None:
        return ""
    if 0.0 < score <= 1.0:
        score *= 100.0
    if score < 55.0:
        return "score_low_observation"
    if score < 65.0:
        return "score_watch_recovery"
    if score < 75.0:
        return "score_mid_recovery"
    if score < 85.0:
        return "score_high_confirmation"
    return "score_extreme_confirmation"


def _first_text(mapping: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = str(mapping.get(key) or "").strip()
        if value and value != "-":
            return value
    return ""


def _derive_entry_source_parent(stock: dict[str, Any]) -> str:
    explicit = _first_text(
        stock,
        (
            "entry_source_parent",
            "rising_missed_entry_source_parent",
            "ldm_entry_source_parent",
        ),
    )
    if explicit:
        return explicit
    text = " ".join(
        str(stock.get(key) or "")
        for key in (
            "scanner_promotion_reason",
            "source_signature",
            "reason",
            "entry_reason",
            "stage",
            "action",
        )
    ).lower()
    if any(
        token in text
        for token in (
            "wait6579",
            "first_ai_wait",
            "score65_74",
            "rising_full_eval_relief",
        )
    ):
        return "entry_source_wait6579"
    return ""


def _candidate_observable_prefix(stock: dict[str, Any]) -> dict[str, str]:
    stock = stock if isinstance(stock, dict) else {}
    score_parent = _first_text(
        stock,
        (
            "entry_score_parent",
            "rising_missed_entry_score_parent",
            "ldm_entry_score_parent",
        ),
    )
    if not score_parent:
        score_parent = _score_bucket(
            stock.get("current_ai_score")
            if stock.get("current_ai_score") is not None
            else stock.get("ai_score", stock.get("rt_ai_prob", stock.get("prob")))
        )
    prefix = {
        "entry_score_parent": score_parent,
        "entry_source_parent": _derive_entry_source_parent(stock),
        "source_signature": _first_text(stock, ("source_signature",)),
        "scanner_promotion_reason": _first_text(stock, ("scanner_promotion_reason",)),
        "liquidity_bucket": _first_text(stock, ("liquidity_bucket",)),
        "strength_bucket": _first_text(stock, ("strength_bucket",)),
        "overbought_bucket": _first_text(stock, ("overbought_bucket",)),
        "chosen_action": _first_text(stock, ("chosen_action", "action")),
    }
    submit_quality = _first_text(
        stock, ("submit_quality_parent", "rising_missed_submit_quality_parent")
    )
    if submit_quality:
        prefix["submit_quality_parent"] = submit_quality
    return {key: value for key, value in prefix.items() if value}


def _catalog_contract_ok(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == "scalp_sim_policy_catalog_v1"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") in {None, False}
        and payload.get("allowed_runtime_apply") is False
        and payload.get("broker_order_forbidden") is True
    )


def load_selection_prior_catalog(
    policy_file: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    path_text = _policy_path(policy_file)
    if not path_text:
        return {"status": "policy_missing", "payload": {}}
    path = Path(path_text)
    try:
        stat = path.stat()
    except OSError:
        return {"status": "policy_missing", "path": str(path), "payload": {}}
    cache_key = str(path.resolve())
    cached = _CATALOG_CACHE.get(cache_key)
    if cached and cached.get("mtime_ns") == stat.st_mtime_ns:
        return cached
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        loaded = {
            "status": "policy_invalid_json",
            "path": str(path),
            "mtime_ns": stat.st_mtime_ns,
            "payload": {},
        }
        _CATALOG_CACHE[cache_key] = loaded
        return loaded
    if not _catalog_contract_ok(payload):
        loaded = {
            "status": "policy_invalid_contract",
            "path": str(path),
            "mtime_ns": stat.st_mtime_ns,
            "payload": {},
        }
        _CATALOG_CACHE[cache_key] = loaded
        return loaded
    loaded = {
        "status": "loaded",
        "path": str(path),
        "mtime_ns": stat.st_mtime_ns,
        "payload": payload,
    }
    _CATALOG_CACHE[cache_key] = loaded
    return loaded


def _prefix_matches(candidate: dict[str, str], prefix: Any) -> bool:
    if not isinstance(prefix, dict):
        return False
    required = {
        str(key): str(value).strip()
        for key, value in prefix.items()
        if str(value or "").strip() and value != "-"
    }
    if not required:
        return False
    exact_keys = [
        key
        for key in required
        if key not in {"source_signature", "scanner_promotion_reason"}
    ]
    if not exact_keys:
        return False
    for key, expected in required.items():
        actual = str(candidate.get(key) or "").strip()
        if not actual or actual != expected:
            return False
    return True


def _source_signature_matches(candidate: dict[str, str], row: dict[str, Any]) -> bool:
    signature = str(candidate.get("source_signature") or "").strip()
    if not signature:
        return False
    prefix = (
        row.get("observable_prefix")
        if isinstance(row.get("observable_prefix"), dict)
        else {}
    )
    return (
        signature
        == str(
            row.get("source_signature") or prefix.get("source_signature") or ""
        ).strip()
    )


def _promotion_reason_matches(candidate: dict[str, str], row: dict[str, Any]) -> bool:
    reason = str(candidate.get("scanner_promotion_reason") or "").strip()
    if not reason:
        return False
    prefix = (
        row.get("observable_prefix")
        if isinstance(row.get("observable_prefix"), dict)
        else {}
    )
    return (
        reason
        == str(
            row.get("scanner_promotion_reason") or prefix.get("source_signature") or ""
        ).strip()
    )


def _recommendation_from_row(row: dict[str, Any], fallback: str = "hold_sample") -> str:
    value = str(
        row.get("recommendation")
        or row.get("rising_missed_prior_recommendation")
        or row.get("priority_recommendation")
        or ""
    ).strip()
    if not value:
        reason = str(row.get("reason") or "").strip()
        for recommendation in VALID_RECOMMENDATIONS:
            if reason.endswith(recommendation) or recommendation in reason:
                value = recommendation
                break
    if not value:
        value = fallback
    return value if value in VALID_RECOMMENDATIONS else "hold_sample"


def _row_result(
    row: dict[str, Any], *, recommendation: str, match_type: str
) -> dict[str, Any]:
    delta = RECOMMENDATION_SCORE_DELTA.get(recommendation, 0.0)
    prior_key = str(
        row.get("prior_key")
        or row.get("source_parent_bucket_id")
        or row.get("active_seed_id")
        or "-"
    )
    reason = str(
        row.get("reason")
        or row.get("rising_missed_prior_reason")
        or row.get("active_collection_reason")
        or f"{recommendation}_{match_type}"
    )
    return {
        "rising_missed_selection_prior_key": prior_key,
        "rising_missed_selection_recommendation": recommendation,
        "rising_missed_selection_confidence": str(
            row.get("confidence")
            or row.get("rising_missed_prior_confidence")
            or "unknown"
        ),
        "rising_missed_selection_score_delta": delta,
        "rising_missed_selection_rank_reason": reason,
        "rising_missed_selection_match_type": match_type,
        "rising_missed_selection_runtime_effect": False,
        "rising_missed_selection_allowed_runtime_apply": False,
    }


def rising_missed_selection_prior_fields(
    stock: dict[str, Any] | None,
    *,
    policy_file: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    loaded = load_selection_prior_catalog(policy_file)
    if loaded.get("status") != "loaded":
        return _empty_result(str(loaded.get("status") or "policy_unavailable"))
    payload = loaded.get("payload") if isinstance(loaded.get("payload"), dict) else {}
    candidate = _candidate_observable_prefix(stock or {})
    if not candidate:
        return _empty_result("candidate_observable_prefix_missing")

    for row in payload.get("rising_missed_prior_active_seed_status_overrides") or []:
        if isinstance(row, dict) and _prefix_matches(
            candidate, row.get("observable_prefix")
        ):
            recommendation = _recommendation_from_row(
                row, fallback="source_quality_blocked"
            )
            if recommendation == "hold_sample":
                recommendation = "source_quality_blocked"
            return _row_result(
                row, recommendation=recommendation, match_type="observable_prefix_exact"
            )

    for seed in payload.get("active_sim_priority_seeds") or []:
        if not isinstance(seed, dict) or str(seed.get("status") or "") != "active":
            continue
        if _prefix_matches(candidate, seed.get("observable_prefix")):
            recommendation = _recommendation_from_row(seed, fallback="positive_prior")
            return _row_result(
                seed,
                recommendation=recommendation,
                match_type="observable_prefix_exact",
            )

    lanes = [
        row
        for row in payload.get("rising_missed_prior_observation_lanes") or []
        if isinstance(row, dict)
    ]
    for row in lanes:
        if _prefix_matches(candidate, row.get("observable_prefix")):
            return _row_result(
                row,
                recommendation=_recommendation_from_row(row),
                match_type="observable_prefix_exact",
            )
    for row in lanes:
        if _source_signature_matches(candidate, row):
            return _row_result(
                row,
                recommendation=_recommendation_from_row(row),
                match_type="source_signature",
            )
    for row in lanes:
        if _promotion_reason_matches(candidate, row):
            return _row_result(
                row,
                recommendation=_recommendation_from_row(row),
                match_type="scanner_promotion_reason",
            )
    return _empty_result("prior_match_not_found")


def rising_missed_selection_rank_delta(
    stock: dict[str, Any] | None,
    *,
    policy_file: str | os.PathLike[str] | None = None,
) -> float:
    fields = rising_missed_selection_prior_fields(stock, policy_file=policy_file)
    return float(fields.get("rising_missed_selection_score_delta") or 0.0)
