"""Permanent retirement of the scalping ADM/LDM policy chain.

Raw candidate/order/receipt/terminal lineage, exact AI investor/program context,
and dedicated strategy replay are still owned by their existing producers.
Archived matrix and dedicated institutional aggregate artifacts are never current
policy, prompt input, or a reason to regenerate the retired chain.
"""

from pathlib import Path
from typing import Any

RETIREMENT_ID = "scalping_adm_ldm_retirement_20260906"
SCALP_OVERNIGHT_RETIREMENT_ID = "scalping_overnight_retirement_20260906"
LATENCY_RECOMMENDATION_RETIREMENT_ID = "latency_recommendation_retirement_20260906"
LATENCY_RECOMMENDATION_RETIRED_REPORTS = frozenset(
    {"latency_classifier_recommendation"}
)
RETIRED_CALIBRATION_FAMILIES = frozenset({"latency_classifier_runtime_profile"})
SCALP_OVERNIGHT_RETIRED_REPORTS = frozenset({"scalp_sim_overnight"})
SCALP_OVERNIGHT_RETIRED_STAGES = frozenset(
    {
        "scalp_sim_overnight_decision",
        "scalp_sim_overnight_sell_today",
        "scalp_sim_overnight_hold",
        "scalp_sim_overnight_carry_restored",
    }
)
SCALP_OVERNIGHT_RETIRED_FAMILIES = (
    frozenset(
        {
            "scalp_sim_overnight",
            "scalp_sim_overnight_ai_carry",
            "scalping_overnight_gatekeeper",
        }
    )
    | SCALP_OVERNIGHT_RETIRED_STAGES
)
RETIRED_REPORTS = (
    frozenset(
        {
            "scalp_entry_action_decision_matrix",
            "holding_exit_decision_matrix",
            "statistical_action_weight",
            "lifecycle_decision_matrix",
            "lifecycle_ai_context",
            "lifecycle_ai_context_attribution",
            "lifecycle_bucket_discovery",
            "ldm_hypothesis_parent_refinement",
            "runtime_apply_bridge",
            "ldm_hypothesis_discovery",
            "institutional_flow_context",
            "scale_in_incremental_counterfactual",
        }
    )
    | SCALP_OVERNIGHT_RETIRED_REPORTS
    | LATENCY_RECOMMENDATION_RETIRED_REPORTS
)
RETIRED_FAMILIES = (
    RETIRED_REPORTS
    | frozenset(
        {
            "scalp_entry_action_decision_matrix_advisory",
            "scalp_entry_adm_runtime_bias_p1",
            "holding_exit_decision_matrix_advisory",
            "holding_exit_matrix_runtime_bias_p1",
            "holding_exit_matrix_avg_down_bias",
            "holding_exit_matrix_pyramid_bias",
            "lifecycle_decision_matrix_runtime",
            "ldm_scale_in_runtime_bridge",
            "greenfield_real_environment_authority",
            "lifecycle_bucket_sim_policy",
            "lifecycle_sim_auto_approval",
            "lifecycle_bucket_sim_auto_approval",
            "ldm_hypothesis_observation_plan",
            "lifecycle_bucket_catalog",
            "scalp_sim_scale_in_window_expansion",
            "scalp_sim_scale_in_window_approval",
        }
    )
    | SCALP_OVERNIGHT_RETIRED_FAMILIES
)
RETIRED_ENV_PREFIXES = (
    "KORSTOCKSCAN_SCALP_ENTRY_ADM_",
    "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_",
    "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_",
    "KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_",
    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_",
    "KORSTOCKSCAN_LDM_SCALE_IN_",
    "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_",
    "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_",
    "KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_",
    "KORSTOCKSCAN_OVERNIGHT_CONTEXT_",
)
RETIRED_OWNER_PREFIXES = tuple(
    owner + separator for owner in RETIRED_FAMILIES for separator in (":", "_", ".")
)
RETIRED_STAGE_FLAGS = frozenset(
    {
        "scalp_entry_adm",
        "lifecycle_decision_matrix",
        "lifecycle_ai_context",
        "lifecycle_bucket_discovery",
        "lifecycle_bucket_windows",
        "ldm_hypothesis_parent_refinement",
        "runtime_apply_bridge",
        "institutional_flow_context",
    }
)


def retired_status(report_type: str = "adm_ldm") -> dict[str, Any]:
    """Explicit terminal state; never a source-quality failure or retry request."""
    retirement_id = (
        LATENCY_RECOMMENDATION_RETIREMENT_ID
        if report_type in LATENCY_RECOMMENDATION_RETIRED_REPORTS
        else (
            SCALP_OVERNIGHT_RETIREMENT_ID
            if report_type in SCALP_OVERNIGHT_RETIRED_FAMILIES
            else RETIREMENT_ID
        )
    )
    return {
        "status": "retired",
        "report_type": report_type,
        "retirement_id": retirement_id,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "archive_only",
        "operator_action_required": False,
        "warnings": [],
        "issues": [],
    }


def retired_artifact(path: Any) -> bool:
    if path is None:
        return False
    parts = Path(str(path)).parts
    return any(part in RETIRED_FAMILIES for part in parts[:-1]) or retired_owner(
        Path(str(path)).stem
    )


def retirement_env() -> dict[str, str]:
    """Explicit OFF defeats inherited supervisors and old operator overrides."""
    return {
        prefix + suffix: value
        for prefix, suffix, value in (
            ("KORSTOCKSCAN_SCALP_ENTRY_ADM_", "ADVISORY_ENABLED", "false"),
            ("KORSTOCKSCAN_SCALP_ENTRY_ADM_", "RUNTIME_BIAS_ENABLED", "false"),
            ("KORSTOCKSCAN_HOLDING_EXIT_MATRIX_", "ADVISORY_ENABLED", "false"),
            ("KORSTOCKSCAN_HOLDING_EXIT_MATRIX_", "RUNTIME_BIAS_ENABLED", "false"),
            ("KORSTOCKSCAN_HOLDING_EXIT_MATRIX_", "SCALE_IN_BIAS_ENABLED", "false"),
            ("KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_", "ENABLED", "false"),
            (
                "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_",
                "RUNTIME_EFFECT_ENABLED",
                "false",
            ),
            ("KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_", "PROMOTE_ENABLED", "false"),
            ("KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_", "ENABLED", "false"),
            ("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_", "ENABLED", "false"),
            (
                "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_",
                "LIVE_AUTO_APPLY_ENABLED",
                "false",
            ),
            ("KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_", "ENABLED", "false"),
            ("KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_", "ENABLED", "false"),
            ("KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_", "ENABLED", "false"),
            ("KORSTOCKSCAN_OVERNIGHT_CONTEXT_", "ENABLED", "false"),
        )
    }


def without_retired_env(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if not k.startswith(RETIRED_ENV_PREFIXES)}


def retired_owner(value: Any) -> bool:
    return isinstance(value, str) and (
        value in RETIRED_FAMILIES or value.startswith(RETIRED_OWNER_PREFIXES)
    )


def _dict_rows(value: Any) -> list[dict[str, Any]]:
    return (
        [item for item in value if isinstance(item, dict)]
        if isinstance(value, list)
        else []
    )


def current_report_view(payload: Any) -> Any:
    """Exclude archived policy sources from current mixed automation bundles."""
    if isinstance(payload, list):
        return [
            current_report_view(item)
            for item in payload
            if not (isinstance(item, str) and retired_owner(item))
            if not (
                isinstance(item, dict)
                and any(
                    retired_owner(item.get(key))
                    for key in (
                        "family",
                        "mapped_family",
                        "target_subsystem",
                        "source_report_type",
                        "source_id",
                        "policy_kind",
                        "policy_id",
                    )
                )
            )
        ]
    if isinstance(payload, dict):
        if retired_owner(payload.get("schema_version")) or (
            retired_owner(payload.get("report_type"))
            and payload.get("status") != "retired"
        ):
            return {}
        result = {
            key: current_report_view(value)
            for key, value in payload.items()
            if not retired_owner(key)
        }
        if payload.get("schema_version") == "scalp_sim_policy_catalog_v1":
            allowed_seeds = {
                str(seed.get("active_seed_id"))
                for item in _dict_rows(result.get("policies"))
                for seed in _dict_rows(item.get("active_sim_priority_seeds"))
            }
            result["active_sim_priority_seeds"] = [
                seed
                for seed in _dict_rows(result.get("active_sim_priority_seeds"))
                if str(seed.get("active_seed_id")) in allowed_seeds
            ]
            result.pop("hypothesis_observation_plan", None)
        return result
    return payload
