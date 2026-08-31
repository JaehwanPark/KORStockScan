"""Exact-date market-weakness hysteresis policy.

The policy changes only the number of consecutive, uniquely spaced weakness or
recovery observations required by the existing notifier latch.  It has no
authority over breadth thresholds, owner selection, prices, quantities,
orders, holdings, exits, or the main bot.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Mapping

from src.utils.constants import DATA_DIR, PROJECT_ROOT
from src.utils.market_day import is_krx_trading_day

SCHEMA = "market_weakness_hysteresis_policy_applied_v1"
SOURCE_REPORT_SCHEMA = "machine_market_weakness_response_v2"
AUTHORITY = "explicit_user_approved_auto_bounded_market_weakness_hysteresis_v1"
CLEAN_BASELINE_DATE = date(2026, 6, 5)

BASELINE_ACTIVATION_OBSERVATIONS = 2
BASELINE_RELEASE_OBSERVATIONS = 3
MIN_OBSERVATION_SPACING_SEC = 60
ALLOWED_ACTIVATION_OBSERVATIONS = frozenset({2, 3, 4})
ALLOWED_RELEASE_OBSERVATIONS = frozenset({2, 3, 4, 5})

DEFAULT_POLICY_DIR = DATA_DIR / "runtime" / "market_weakness_hysteresis_policy"
DEFAULT_SOURCE_REPORT_DIR = DATA_DIR / "report" / "machine_microstructure_attribution"
POLICY_PREFIX = "market_weakness_hysteresis_policy"
SOURCE_REPORT_PREFIX = "machine_microstructure_attribution"
THRESHOLD_REVIEW_METHOD = (
    "deterministic_current_policy_neighbor_calibration_plus_latest_date_holdout_v2"
)
REQUIRED_SAMPLE_FLOOR_KEYS = frozenset(
    {
        "trading_dates_met",
        "counterfactual_entry_signals_met",
        "holdout_trading_dates_met",
        "current_policy_observed_trading_dates_met",
        "per_listing_market_signals_met",
        "per_owner_signals_met",
    }
)
THRESHOLD_REVIEW_FIELDS = (
    "window_start",
    "window_end",
    "calibration_dates",
    "holdout_dates",
    "current_policy_observed_dates",
    "sample_floor",
    "current_policy",
    "selected_policy",
    "review_method",
    "counterfactual_entry_signal_count",
    "owner_signal_counts",
    "listing_market_signal_counts",
    "candidates",
    "policy_candidate_ready",
)


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def threshold_hash(*, activation: int, release: int) -> str:
    return canonical_sha256(
        {
            "activation_unique_observations": int(activation),
            "release_unique_observations": int(release),
            "minimum_observation_spacing_sec": MIN_OBSERVATION_SPACING_SEC,
        }
    )


def threshold_recommendation_review_hash(
    recommendation: Mapping[str, Any],
) -> str:
    """Recalculate the deterministic review hash owned by the source report."""

    return canonical_sha256(
        {field: recommendation.get(field) for field in THRESHOLD_REVIEW_FIELDS}
    )


def validate_threshold_recommendation(
    recommendation: Any,
) -> tuple[bool, str]:
    if not isinstance(recommendation, Mapping):
        return False, "market_weakness_policy_recommendation_missing"
    current = recommendation.get("current_policy")
    selected = recommendation.get("selected_policy")
    candidate_ready = recommendation.get("policy_candidate_ready")
    if not isinstance(current, Mapping):
        return False, "market_weakness_policy_current_policy_missing"
    current_activation = current.get("activation_unique_observations")
    current_release = current.get("release_unique_observations")
    if (
        isinstance(current_activation, bool)
        or not isinstance(current_activation, int)
        or current_activation not in ALLOWED_ACTIVATION_OBSERVATIONS
        or isinstance(current_release, bool)
        or not isinstance(current_release, int)
        or current_release not in ALLOWED_RELEASE_OBSERVATIONS
        or not isinstance(candidate_ready, bool)
    ):
        return False, "market_weakness_policy_current_policy_invalid"
    if candidate_ready != isinstance(selected, Mapping):
        return False, "market_weakness_policy_candidate_state_invalid"
    if isinstance(selected, Mapping):
        selected_activation = selected.get("activation_unique_observations")
        selected_release = selected.get("release_unique_observations")
        if (
            isinstance(selected_activation, bool)
            or not isinstance(selected_activation, int)
            or selected_activation not in ALLOWED_ACTIVATION_OBSERVATIONS
            or isinstance(selected_release, bool)
            or not isinstance(selected_release, int)
            or selected_release not in ALLOWED_RELEASE_OBSERVATIONS
            or selected.get("review_status") != "passed_out_of_sample_review"
            or int(selected_activation != current_activation)
            + int(selected_release != current_release)
            != 1
            or abs(selected_activation - current_activation) > 1
            or abs(selected_release - current_release) > 1
        ):
            return False, "market_weakness_policy_selected_policy_invalid"
        calibration_dates = recommendation.get("calibration_dates")
        holdout_dates = recommendation.get("holdout_dates")
        current_policy_observed_dates = recommendation.get(
            "current_policy_observed_dates"
        )
        sample_floor = recommendation.get("sample_floor")
        owner_counts = recommendation.get("owner_signal_counts")
        market_counts = recommendation.get("listing_market_signal_counts")
        try:
            parsed_calibration_dates = {
                date.fromisoformat(value) for value in calibration_dates
            }
            parsed_holdout_dates = {
                date.fromisoformat(value) for value in holdout_dates
            }
            parsed_current_policy_dates = {
                date.fromisoformat(value) for value in current_policy_observed_dates
            }
            window_end = date.fromisoformat(str(recommendation.get("window_end")))
        except (TypeError, ValueError):
            return False, "market_weakness_policy_review_dates_invalid"
        if (
            recommendation.get("window_start") != CLEAN_BASELINE_DATE.isoformat()
            or not isinstance(calibration_dates, list)
            or not isinstance(holdout_dates, list)
            or not isinstance(current_policy_observed_dates, list)
            or parsed_calibration_dates & parsed_holdout_dates
            or len(parsed_calibration_dates | parsed_holdout_dates) < 10
            or len(parsed_holdout_dates) < 3
            or len(parsed_current_policy_dates) < 3
            or not parsed_current_policy_dates.issubset(
                parsed_calibration_dates | parsed_holdout_dates
            )
            or min(parsed_calibration_dates | parsed_holdout_dates)
            < CLEAN_BASELINE_DATE
            or max(parsed_calibration_dates | parsed_holdout_dates) > window_end
            or any(
                not is_krx_trading_day(review_date)
                for review_date in parsed_calibration_dates | parsed_holdout_dates
            )
            or any(
                not is_krx_trading_day(review_date)
                for review_date in parsed_current_policy_dates
            )
            or not isinstance(sample_floor, Mapping)
            or set(sample_floor) != REQUIRED_SAMPLE_FLOOR_KEYS
            or any(
                sample_floor.get(key) is not True for key in REQUIRED_SAMPLE_FLOOR_KEYS
            )
            or not isinstance(market_counts, Mapping)
            or any(
                isinstance(market_counts.get(market), bool)
                or not isinstance(market_counts.get(market), int)
                or int(market_counts[market]) < 10
                for market in ("KOSPI", "KOSDAQ")
            )
            or not isinstance(owner_counts, Mapping)
            or any(
                isinstance(owner_counts.get(owner), bool)
                or not isinstance(owner_counts.get(owner), int)
                or int(owner_counts[owner]) < 10
                for owner in ("widget", "episode")
            )
            or isinstance(recommendation.get("counterfactual_entry_signal_count"), bool)
            or not isinstance(
                recommendation.get("counterfactual_entry_signal_count"), int
            )
            or int(recommendation["counterfactual_entry_signal_count"]) < 50
        ):
            return False, "market_weakness_policy_sample_floor_invalid"
        expected_axis = (
            "activation_unique_observations"
            if selected_activation != current_activation
            else "release_unique_observations"
        )

        def finite_number(field: str) -> float | None:
            value = selected.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return None
            parsed = float(value)
            return parsed if math.isfinite(parsed) else None

        calibration_ev = finite_number(
            "calibration_incremental_vs_current_policy_avg_pct"
        )
        holdout_ev = finite_number("holdout_incremental_vs_current_policy_avg_pct")
        full_ev = finite_number("full_incremental_vs_current_policy_avg_pct")
        p10 = finite_number("full_incremental_vs_current_policy_p10_pct")
        sample_count = selected.get("sample_count")
        current_misclassification = current.get("misclassification_count")
        selected_misclassification = selected.get("misclassification_count")
        stratum_guards = selected.get("stratum_guards")
        required_strata = {
            "owner:widget",
            "owner:episode",
            "market:KOSPI",
            "market:KOSDAQ",
        }
        stratum_guards_valid = (
            isinstance(stratum_guards, Mapping)
            and set(stratum_guards) == required_strata
        )
        if stratum_guards_valid:
            for stratum in required_strata:
                guard = stratum_guards.get(stratum)
                if not isinstance(guard, Mapping):
                    stratum_guards_valid = False
                    break
                numeric_fields = {
                    field: guard.get(field)
                    for field in (
                        "holdout_incremental_vs_current_policy_avg_pct",
                        "full_incremental_vs_current_policy_avg_pct",
                    )
                }
                if (
                    isinstance(guard.get("sample_count"), bool)
                    or not isinstance(guard.get("sample_count"), int)
                    or int(guard["sample_count"]) < 10
                    or isinstance(guard.get("holdout_sample_count"), bool)
                    or not isinstance(guard.get("holdout_sample_count"), int)
                    or int(guard["holdout_sample_count"]) <= 0
                    or any(
                        isinstance(value, bool)
                        or not isinstance(value, (int, float))
                        or not math.isfinite(float(value))
                        or float(value) < 0.0
                        for value in numeric_fields.values()
                    )
                    or isinstance(guard.get("candidate_misclassification_count"), bool)
                    or not isinstance(
                        guard.get("candidate_misclassification_count"), int
                    )
                    or isinstance(
                        guard.get("current_policy_misclassification_count"), bool
                    )
                    or not isinstance(
                        guard.get("current_policy_misclassification_count"), int
                    )
                    or int(guard["candidate_misclassification_count"])
                    > int(guard["current_policy_misclassification_count"])
                ):
                    stratum_guards_valid = False
                    break
        if (
            selected.get("changed_axis") != expected_axis
            or selected.get("candidate_key")
            != f"a{selected_activation}_r{selected_release}"
            or isinstance(sample_count, bool)
            or not isinstance(sample_count, int)
            or sample_count < 50
            or calibration_ev is None
            or calibration_ev < 0.005
            or holdout_ev is None
            or holdout_ev < 0.0
            or full_ev is None
            or full_ev < 0.003
            or p10 is None
            or p10 < -0.05
            or isinstance(current_misclassification, bool)
            or not isinstance(current_misclassification, int)
            or isinstance(selected_misclassification, bool)
            or not isinstance(selected_misclassification, int)
            or selected_misclassification > current_misclassification
            or not stratum_guards_valid
        ):
            return False, "market_weakness_policy_economic_review_invalid"
    review_hash = recommendation.get("review_hash")
    if (
        not isinstance(review_hash, str)
        or len(review_hash) != 64
        or any(char not in "0123456789abcdef" for char in review_hash)
        or review_hash != threshold_recommendation_review_hash(recommendation)
    ):
        return False, "market_weakness_policy_review_hash_invalid"
    if recommendation.get("review_method") != THRESHOLD_REVIEW_METHOD:
        return False, "market_weakness_policy_review_method_invalid"
    return True, "ready"


def policy_path(target_date: date, *, policy_dir: Path = DEFAULT_POLICY_DIR) -> Path:
    return policy_dir / f"{POLICY_PREFIX}_{target_date.isoformat()}.json"


def source_report_path(
    source_date: date, *, source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR
) -> Path:
    return source_report_dir / f"{SOURCE_REPORT_PREFIX}_{source_date.isoformat()}.json"


def next_krx_trading_day(source_date: date) -> date:
    candidate = source_date + timedelta(days=1)
    while not is_krx_trading_day(candidate):
        candidate += timedelta(days=1)
    return candidate


@dataclass(frozen=True, slots=True)
class EffectiveMarketWeaknessThresholds:
    activation_unique_observations: int
    release_unique_observations: int
    source: str
    status: str
    target_date: str
    source_date: str | None
    policy_path: str
    policy_hash: str
    review_status: str

    def observation_contract(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "target_date": self.target_date,
            "source_date": self.source_date,
            "source": self.source,
            "status": self.status,
            "policy_path": self.policy_path,
            "policy_hash": self.policy_hash,
            "review_status": self.review_status,
            "activation_unique_observations": (self.activation_unique_observations),
            "release_unique_observations": self.release_unique_observations,
            "minimum_observation_spacing_sec": MIN_OBSERVATION_SPACING_SEC,
            "runtime_effect": self.source == "exact_date_applied_policy",
            "axis": "market_weakness_hysteresis_consecutive_observation_counts",
        }


def _baseline(
    *, target_date: date, status: str, policy_dir: Path
) -> EffectiveMarketWeaknessThresholds:
    return EffectiveMarketWeaknessThresholds(
        activation_unique_observations=BASELINE_ACTIVATION_OBSERVATIONS,
        release_unique_observations=BASELINE_RELEASE_OBSERVATIONS,
        source="bounded_baseline_fallback",
        status=status,
        target_date=target_date.isoformat(),
        source_date=None,
        policy_path=str(policy_path(target_date, policy_dir=policy_dir)),
        policy_hash=threshold_hash(
            activation=BASELINE_ACTIVATION_OBSERVATIONS,
            release=BASELINE_RELEASE_OBSERVATIONS,
        ),
        review_status="not_applicable_baseline",
    )


def validate_applied_policy(payload: Any, *, target_date: date) -> tuple[bool, str]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return False, "market_weakness_policy_schema_invalid"
    if payload.get("target_date") != target_date.isoformat():
        return False, "market_weakness_policy_target_date_mismatch"
    if not is_krx_trading_day(target_date):
        return False, "market_weakness_policy_target_date_not_trading_day"
    try:
        source_date = date.fromisoformat(str(payload.get("source_date") or ""))
    except ValueError:
        return False, "market_weakness_policy_source_date_invalid"
    if (
        source_date < CLEAN_BASELINE_DATE
        or source_date >= target_date
        or not is_krx_trading_day(source_date)
        or next_krx_trading_day(source_date) != target_date
    ):
        return False, "market_weakness_policy_source_date_contract_invalid"
    activation = payload.get("activation_unique_observations")
    release = payload.get("release_unique_observations")
    prior_activation = payload.get("prior_activation_unique_observations")
    prior_release = payload.get("prior_release_unique_observations")
    if (
        isinstance(activation, bool)
        or not isinstance(activation, int)
        or activation not in ALLOWED_ACTIVATION_OBSERVATIONS
        or isinstance(release, bool)
        or not isinstance(release, int)
        or release not in ALLOWED_RELEASE_OBSERVATIONS
        or isinstance(prior_activation, bool)
        or not isinstance(prior_activation, int)
        or prior_activation not in ALLOWED_ACTIVATION_OBSERVATIONS
        or isinstance(prior_release, bool)
        or not isinstance(prior_release, int)
        or prior_release not in ALLOWED_RELEASE_OBSERVATIONS
        or payload.get("minimum_observation_spacing_sec") != MIN_OBSERVATION_SPACING_SEC
    ):
        return False, "market_weakness_policy_threshold_bounds_invalid"
    changed_axes = int(activation != prior_activation) + int(release != prior_release)
    if changed_axes > 1:
        return False, "market_weakness_policy_multiple_axis_change_forbidden"
    if abs(activation - prior_activation) > 1 or abs(release - prior_release) > 1:
        return False, "market_weakness_policy_step_change_out_of_bounds"
    expected_hash = threshold_hash(activation=activation, release=release)
    review = payload.get("review")
    source_report = payload.get("source_report")
    source_hash = payload.get("source_report_canonical_sha256")
    source_review_hash = (
        review.get("source_review_hash") if isinstance(review, dict) else None
    )
    if (
        payload.get("clean_tuning_baseline_date") != CLEAN_BASELINE_DATE.isoformat()
        or payload.get("decision_authority") != AUTHORITY
        or payload.get("policy_hash") != expected_hash
        or not isinstance(source_report, str)
        or not source_report.strip()
        or not isinstance(source_hash, str)
        or len(source_hash) != 64
        or any(char not in "0123456789abcdef" for char in source_hash)
        or not isinstance(review, dict)
        or not isinstance(source_review_hash, str)
        or len(source_review_hash) != 64
        or any(char not in "0123456789abcdef" for char in source_review_hash)
        or review.get("status")
        not in {
            "passed_out_of_sample_review",
            "current_policy_carry_forward_no_approved_candidate",
        }
        or payload.get("runtime_effect") is not True
        or payload.get("allowed_runtime_apply") is not True
        or payload.get("actual_order_submitted") is not False
        or payload.get("broker_order_forbidden") is not False
    ):
        return False, "market_weakness_policy_authority_invalid"
    if review.get("status") == "passed_out_of_sample_review" and changed_axes != 1:
        return False, "market_weakness_policy_reviewed_change_missing"
    if (
        review.get("status") == "current_policy_carry_forward_no_approved_candidate"
        and changed_axes != 0
    ):
        return False, "market_weakness_policy_unreviewed_change_forbidden"
    forbidden = payload.get("forbidden_uses")
    required_forbidden = {
        "same_day_hot_threshold_mutation",
        "breadth_definition_or_release_margin_change",
        "main_bot_entry_or_exit_change",
        "price_quantity_target_holding_or_exit_change",
        "broker_guard_or_order_owner_change",
    }
    if not isinstance(forbidden, list) or not required_forbidden.issubset(
        {str(value) for value in forbidden}
    ):
        return False, "market_weakness_policy_forbidden_use_contract_invalid"
    return True, "ready"


def load_applied_policy(
    *,
    target_date: date,
    policy_dir: Path = DEFAULT_POLICY_DIR,
    source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR,
) -> tuple[dict[str, Any] | None, str]:
    path = policy_path(target_date, policy_dir=policy_dir)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"market_weakness_policy_unreadable:{type(exc).__name__}"
    valid, reason = validate_applied_policy(payload, target_date=target_date)
    if not valid:
        return None, reason
    source_date = date.fromisoformat(str(payload["source_date"]))
    declared_source = Path(str(payload["source_report"]))
    if not declared_source.is_absolute():
        declared_source = PROJECT_ROOT / declared_source
    expected_source = source_report_path(
        source_date, source_report_dir=source_report_dir
    )
    if declared_source.resolve() != expected_source.resolve():
        return None, "market_weakness_policy_source_report_path_invalid"
    try:
        source_payload = json.loads(declared_source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"market_weakness_source_report_unreadable:{type(exc).__name__}"
    response = (
        source_payload.get("market_weakness_entry_response")
        if isinstance(source_payload, dict)
        else None
    )
    if (
        not isinstance(response, dict)
        or response.get("schema") != SOURCE_REPORT_SCHEMA
        or response.get("target_date") != source_date.isoformat()
        or payload.get("source_report_canonical_sha256")
        != canonical_sha256(source_payload)
    ):
        return None, "market_weakness_policy_source_report_contract_invalid"
    recommendation = response.get("threshold_recommendation")
    recommendation_valid, recommendation_reason = validate_threshold_recommendation(
        recommendation
    )
    if not recommendation_valid:
        return None, recommendation_reason
    assert isinstance(recommendation, Mapping)
    selected = recommendation.get("selected_policy")
    current = recommendation.get("current_policy")
    assert isinstance(current, Mapping)
    prior_activation = int(current["activation_unique_observations"])
    prior_release = int(current["release_unique_observations"])
    expected_activation = prior_activation
    expected_release = prior_release
    expected_review = "current_policy_carry_forward_no_approved_candidate"
    if isinstance(selected, Mapping):
        expected_activation = int(selected["activation_unique_observations"])
        expected_release = int(selected["release_unique_observations"])
        expected_review = "passed_out_of_sample_review"
    review = payload.get("review") or {}
    if (
        payload.get("activation_unique_observations") != expected_activation
        or payload.get("release_unique_observations") != expected_release
        or payload.get("prior_activation_unique_observations") != prior_activation
        or payload.get("prior_release_unique_observations") != prior_release
        or review.get("status") != expected_review
        or review.get("source_review_hash") != recommendation.get("review_hash")
    ):
        return None, "market_weakness_policy_source_selection_mismatch"
    return payload, reason


def resolve_effective_thresholds(
    *,
    target_date: date,
    policy_dir: Path = DEFAULT_POLICY_DIR,
    source_report_dir: Path = DEFAULT_SOURCE_REPORT_DIR,
) -> EffectiveMarketWeaknessThresholds:
    payload, reason = load_applied_policy(
        target_date=target_date,
        policy_dir=policy_dir,
        source_report_dir=source_report_dir,
    )
    if payload is None:
        return _baseline(target_date=target_date, status=reason, policy_dir=policy_dir)
    return EffectiveMarketWeaknessThresholds(
        activation_unique_observations=int(payload["activation_unique_observations"]),
        release_unique_observations=int(payload["release_unique_observations"]),
        source="exact_date_applied_policy",
        status="applied",
        target_date=target_date.isoformat(),
        source_date=str(payload["source_date"]),
        policy_path=str(policy_path(target_date, policy_dir=policy_dir)),
        policy_hash=str(payload["policy_hash"]),
        review_status=str((payload.get("review") or {}).get("status") or ""),
    )


def observation_thresholds(observation: Mapping[str, Any]) -> tuple[int, int, int]:
    """Return thresholds bound to an immutable observation.

    Legacy schema-v2 observations created before this exact-date policy existed
    remain readable only as the documented 2/3 baseline.
    """

    policy = observation.get("hysteresis_policy")
    sample_floor = observation.get("sample_floor")
    if not isinstance(sample_floor, Mapping):
        raise ValueError("market_weakness_observation_sample_floor_invalid")
    activation = sample_floor.get("activation_unique_observations")
    release = sample_floor.get("release_unique_observations")
    if not isinstance(policy, Mapping):
        if (
            activation == BASELINE_ACTIVATION_OBSERVATIONS
            and release == BASELINE_RELEASE_OBSERVATIONS
        ):
            return (
                BASELINE_ACTIVATION_OBSERVATIONS,
                BASELINE_RELEASE_OBSERVATIONS,
                MIN_OBSERVATION_SPACING_SEC,
            )
        raise ValueError("market_weakness_observation_policy_missing")
    spacing = policy.get("minimum_observation_spacing_sec")
    if (
        isinstance(activation, bool)
        or not isinstance(activation, int)
        or activation not in ALLOWED_ACTIVATION_OBSERVATIONS
        or isinstance(release, bool)
        or not isinstance(release, int)
        or release not in ALLOWED_RELEASE_OBSERVATIONS
        or policy.get("activation_unique_observations") != activation
        or policy.get("release_unique_observations") != release
        or spacing != MIN_OBSERVATION_SPACING_SEC
        or policy.get("policy_hash")
        != threshold_hash(activation=activation, release=release)
    ):
        raise ValueError("market_weakness_observation_policy_invalid")
    policy_source = policy.get("source")
    target_date = str(observation.get("target_date") or "")
    if (
        policy.get("schema") != SCHEMA
        or policy.get("target_date") != target_date
        or not str(policy.get("policy_path") or "").strip()
    ):
        raise ValueError("market_weakness_observation_policy_provenance_invalid")
    if policy_source == "exact_date_applied_policy":
        if (
            policy.get("status") != "applied"
            or policy.get("runtime_effect") is not True
            or policy.get("review_status")
            not in {
                "passed_out_of_sample_review",
                "current_policy_carry_forward_no_approved_candidate",
            }
            or not str(policy.get("source_date") or "").strip()
        ):
            raise ValueError("market_weakness_observation_exact_policy_invalid")
    elif policy_source == "bounded_baseline_fallback":
        if (
            activation != BASELINE_ACTIVATION_OBSERVATIONS
            or release != BASELINE_RELEASE_OBSERVATIONS
            or policy.get("runtime_effect") is not False
            or policy.get("source_date") is not None
            or policy.get("review_status") != "not_applicable_baseline"
        ):
            raise ValueError("market_weakness_observation_baseline_policy_invalid")
    else:
        raise ValueError("market_weakness_observation_policy_source_invalid")
    return activation, release, int(spacing)
