"""Permanent retirement of the scalping ADM/LDM policy chain.

Raw candidate/order/receipt/terminal lineage, exact AI investor/program context,
and dedicated strategy replay are still owned by their existing producers.
Archived matrix and dedicated institutional aggregate artifacts are never current
policy, prompt input, or a reason to regenerate the retired chain.
"""

import argparse
import os
import shlex
from pathlib import Path
from typing import Any, Mapping

RETIREMENT_ID = "scalping_adm_ldm_retirement_20260906"
SCALP_OVERNIGHT_RETIREMENT_ID = "scalping_overnight_retirement_20260906"
LATENCY_RECOMMENDATION_RETIREMENT_ID = "latency_recommendation_retirement_20260906"
LATENCY_RECOMMENDATION_RETIRED_REPORTS = frozenset(
    {"latency_classifier_recommendation"}
)
RISING_MISSED_SCOUT_RETIREMENT_ID = "rising_missed_scout_retirement_20260918"
RISING_MISSED_SCOUT_RETIRED_REPORTS = frozenset({"one_share_threshold_opportunity", "rising_missed_scout_workorder"})
SCALE_IN_RETIREMENT_ID = "pyramid_retirement_avg_down_shared_rebound_20260918"
SCALE_IN_RETIRED_REPORTS = frozenset({
    "scalping_pyramid_intraday_feedback", "scalping_pyramid_quality_calibration",
    "scalping_avg_down_recovery_calibration",
})
SCALE_IN_RETIRED_CALIBRATION_FAMILIES = frozenset({
    "scalping_pyramid_quality_gate", "scalping_avg_down_recovery_quality_gate",
    "post_probe_winner_recovery", "reversal_add", "shallow_avg_down_source_gap_recheck",
})
ENTRY_RECHECK_RETIREMENT_ID = "entry_recheck_drought_retirement_20260918"
ENTRY_RECHECK_RETIRED_REPORTS = frozenset({"entry_recheck_drought_controller"})
ENTRY_RECHECK_RETIRED_FAMILIES = frozenset({"entry_opportunity_recheck_runtime"})
RETIRED_CALIBRATION_FAMILIES = (
    ENTRY_RECHECK_RETIRED_FAMILIES
    | frozenset({"latency_classifier_runtime_profile"})
    | SCALE_IN_RETIRED_CALIBRATION_FAMILIES
)
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
CLAUDE_LAB_RETIREMENT_ID = "claude_scalping_pattern_lab_retirement_20260918"
CLAUDE_LAB_RETIRED_REPORTS = frozenset({"claude_scalping_pattern_lab", "scalping_pattern_lab_automation", "pattern_lab_automation"})
LIMIT_DOWN_RETIREMENT_ID = "limit_down_watch_retirement_20260919"
LIMIT_DOWN_RETIRED_REPORTS = frozenset({
    "limit_down_watch", "limit_down_watch_report", "limit_down_watch_candidate_source",
    "limit_down_watch_counterfactual", "limit_down_watch_sim_policy_catalog",
    "limit_down_watch_post_sim_attribution", "limit_down_watch_real_post_apply_attribution",
    "limit_down_watch_bounded_live_candidate",
})
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
    | SCALE_IN_RETIRED_REPORTS
    | RISING_MISSED_SCOUT_RETIRED_REPORTS
    | ENTRY_RECHECK_RETIRED_REPORTS
    | CLAUDE_LAB_RETIRED_REPORTS
    | LIMIT_DOWN_RETIRED_REPORTS
)
RETIRED_FAMILIES = (
    RETIRED_REPORTS
    | ENTRY_RECHECK_RETIRED_FAMILIES
    | SCALE_IN_RETIRED_CALIBRATION_FAMILIES
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
            "scalp_sim_auto_approval",
            "scalp_sim_auto_approval_control_tower",
        }
    )
    | SCALP_OVERNIGHT_RETIRED_FAMILIES
)
RETIRED_ENV_PREFIXES = (
    "KORSTOCKSCAN_NXT_RISING_MISSED_TP1_PARTIAL_",
    "KORSTOCKSCAN_SCALP_MFE_PROTECT_",
    "KORSTOCKSCAN_LIMIT_DOWN_",
    "THRESHOLD_CYCLE_RUN_LIMIT_DOWN_WATCH_REPORT",
    "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_",
    "THRESHOLD_CYCLE_RUN_ENTRY_RECHECK_DROUGHT_CONTROLLER",
    "KORSTOCKSCAN_RISING_MISSED_ONE_SHARE_ENTRY_",
    "KORSTOCKSCAN_RISING_MISSED_SCOUT_",
    "KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_",
    "THRESHOLD_CYCLE_RUN_ONE_SHARE_THRESHOLD_OPPORTUNITY",
    "THRESHOLD_CYCLE_RUN_RISING_MISSED_SCOUT_WORKORDER",
    "KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_",
    "KORSTOCKSCAN_SCALP_TRAILING_LOSS_CONVERSION_RECHECK_",
    "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ENABLED",
    "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_ACTIVE_DATE",
    "KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID",
    "KORSTOCKSCAN_SWING_ENABLE_PYRAMID",
    "KORSTOCKSCAN_SCALP_POST_PROBE_WINNER_RECOVERY_",
    "KORSTOCKSCAN_SHALLOW_SOURCE_GAP_RECHECK_",
    "KORSTOCKSCAN_SCALPING_PYRAMID_RUNTIME_",
    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_PROFIT_PCT",
    "KORSTOCKSCAN_SCALPING_PYRAMID_STRONG_CONTINUATION_",
    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_AI_SCORE",
    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_BUY_PRESSURE",
    "KORSTOCKSCAN_SCALPING_PYRAMID_MIN_TICK_ACCEL",
    "KORSTOCKSCAN_SWING_PYRAMID_",
    "KORSTOCKSCAN_RISING_MISSED_SCOUT_PYRAMID_",
    "KORSTOCKSCAN_POST_PROBE_WINNER_RECOVERY_",
    "KORSTOCKSCAN_AVG_DOWN_RUNTIME_",
    "KORSTOCKSCAN_SHALLOW_VOLATILITY_AVG_DOWN_",
    "KORSTOCKSCAN_DEEP_RECOVERY_AVG_DOWN_",
    "KORSTOCKSCAN_SCALP_LATE_LOSS_AVG_DOWN_",
    "KORSTOCKSCAN_SCALP_STOP_LINE_TOUCH_AVG_DOWN_",

    "KORSTOCKSCAN_SCALP_ENTRY_ADM_",
    "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_",
    "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_",
    "KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_",
    "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_",
    "KORSTOCKSCAN_LDM_SCALE_IN_",
    "KORSTOCKSCAN_GREENFIELD_REAL_ENV_AUTHORITY_",
    "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_",
    "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_",
    "KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_",
    "KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_",
    "KORSTOCKSCAN_OVERNIGHT_CONTEXT_",
)
RETIRED_OWNER_PREFIXES = tuple(
    owner + separator for owner in RETIRED_FAMILIES for separator in (":", "_", ".")
) + ("order_entry_recheck_",)
RETIRED_STAGE_FLAGS = frozenset(
    {
        "limit_down_watch_report",
        "pattern_labs",
        "scalping_pattern_lab_automation",
        "entry_recheck_drought_controller",
        "one_share_threshold_opportunity",
        "rising_missed_scout_workorder",
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
        LIMIT_DOWN_RETIREMENT_ID
        if report_type in LIMIT_DOWN_RETIRED_REPORTS
        else CLAUDE_LAB_RETIREMENT_ID
        if report_type in CLAUDE_LAB_RETIRED_REPORTS
        else ENTRY_RECHECK_RETIREMENT_ID
        if report_type in ENTRY_RECHECK_RETIRED_REPORTS | ENTRY_RECHECK_RETIRED_FAMILIES
        else RISING_MISSED_SCOUT_RETIREMENT_ID
        if report_type in RISING_MISSED_SCOUT_RETIRED_REPORTS
        else SCALE_IN_RETIREMENT_ID
        if report_type in SCALE_IN_RETIRED_REPORTS | SCALE_IN_RETIRED_CALIBRATION_FAMILIES
        else LATENCY_RECOMMENDATION_RETIREMENT_ID
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
    result = {
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
            ("KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_", "ENABLED", "false"),
            ("KORSTOCKSCAN_OVERNIGHT_CONTEXT_", "ENABLED", "false"),
        )
    }
    result.update({
        "KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED": "false",
        "KORSTOCKSCAN_LIMIT_DOWN_SIM_POLICY_ENABLED": "false",
        "KORSTOCKSCAN_LIMIT_DOWN_LIVE_POLICY_ENABLED": "false",
        "KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED": "false",
        "KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID": "false",
        "KORSTOCKSCAN_SWING_ENABLE_PYRAMID": "false",
    })
    return result


def retirement_shell_commands(environ: Mapping[str, str] | None = None) -> str:
    """Render shell commands that remove retired namespaces and assert OFF flags."""

    source = os.environ if environ is None else environ
    retired_keys = sorted(
        key for key in source if str(key).startswith(RETIRED_ENV_PREFIXES)
    )
    commands = [f"unset -- {shlex.quote(key)}" for key in retired_keys]
    commands.extend(
        f"export {key}={shlex.quote(value)}"
        for key, value in sorted(retirement_env().items())
    )
    return "\n".join(commands)


def without_retired_env(values: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in values.items() if not k.startswith(RETIRED_ENV_PREFIXES)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-commands", action="store_true")
    args = parser.parse_args(argv)
    if not args.shell_commands:
        parser.error("--shell-commands is required")
    print(retirement_shell_commands())
    return 0


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


def current_calibration_rows(value: Any) -> list[dict[str, Any]]:
    """Filter calibration authority only; keep the same family's raw telemetry."""
    return [
        item
        for item in _dict_rows(value)
        if not any(
            str(item.get(key) or "").strip() in RETIRED_CALIBRATION_FAMILIES
            for key in ("family", "source_family", "mapped_family")
        )
    ]


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
                        "order_id",
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
            key: current_report_view(
                current_calibration_rows(value)
                if key
                in {
                    "calibration_candidates",
                    "calibration_decisions",
                    "approval_requests",
                }
                and isinstance(value, list)
                else value
            )
            for key, value in payload.items()
            if not retired_owner(key)
        }
        outcome = result.get("calibration_outcome")
        if isinstance(outcome, dict) and isinstance(outcome.get("decisions"), list):
            outcome["decisions"] = current_calibration_rows(outcome["decisions"])
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


if __name__ == "__main__":
    raise SystemExit(main())
