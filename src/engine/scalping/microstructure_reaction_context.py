from __future__ import annotations

import ast
import hashlib
import json
import math
from uuid import uuid4
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.trading.market.quote_consistency import build_market_data_health
from src.utils.constants import DATA_DIR

CONTEXT_VERSION = "microstructure_reaction_context_v2"
REPORT_DIR = DATA_DIR / "report" / "microstructure_reaction_context"
TRUSTED_TICK_VOLUME_SOURCES = {"15_abs", "13_delta"}
DEFAULT_QUOTE_STALE_MS = 3000
KST = timezone(timedelta(hours=9))

DELIVERY_KEYS = tuple(
    "microstructure_reaction_" + name
    for name in (
        "context_id",
        "parent_context_id",
        "evaluation_id",
        "reference_time",
        "reference_price",
        "venue",
        "context_computed",
        "context_reused",
        "delivery_telemetry_version",
        "context_payload_included",
        "provider_delivery_status",
        "context_sent",
        "context_consumed",
        "context_consumer",
        "context_delivery_state",
        "quote_stale_threshold_ms",
        "quote_threshold_setting_status",
    )
)


def normalize_quote_stale_threshold(value: Any) -> tuple[int, str]:
    """Canonical setting normalization, without granting freshness to invalid input."""
    if value is None or value == "":
        return DEFAULT_QUOTE_STALE_MS, "default"
    if isinstance(value, bool):
        return DEFAULT_QUOTE_STALE_MS, "invalid"
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_QUOTE_STALE_MS, "invalid"
    if not math.isfinite(number):
        return DEFAULT_QUOTE_STALE_MS, "invalid"
    if number == 0:
        return DEFAULT_QUOTE_STALE_MS, "default"
    return max(1, int(number)), "invalid_clamped" if number < 0 else "explicit"


def microstructure_delivery_fields(payload: dict) -> dict:
    """Lossless receipt projection, including unknown (null) delivery."""
    return {key: payload[key] for key in DELIVERY_KEYS if key in payload}



MACHINE_EVALUATION_SCHEMA = "microstructure_machine_auxiliary_evaluation_v1"


def bind_machine_microstructure_source(capture: dict) -> dict:
    """Project the already verified exact capture; never reconstruct live inputs."""
    source = capture.get("source") or {}
    payload = source.get("exact_payload") or {}
    evidence = source.get("setup_evidence") or {}
    context = capture.get("label_context") or {}
    snapshot = payload.get("ai_market_snapshot_v1") or {}
    mechanistic = evidence.get("mechanistic_context") or {}
    flow = mechanistic.get("flow") or {}
    window = mechanistic.get("micro_window") or payload.get("mechanistic_micro_window") or {}
    from src.trading.market.micro_confirmation import _live_route_item

    expected_item = _live_route_item(str(context.get("stock_code") or ""), {"krx_only": "KRX", "nxt_only": "NXT", "krx_nxt_integrated": "SOR"}.get(str(context.get("market_data_route") or ""), ""))
    features = payload.get("features") or {}
    reaction = {k: v for k, v in features.items() if k.startswith("microstructure_reaction_")}
    try:
        captured = datetime.fromisoformat(capture["captured_at"])
        cutoff = float(window["cutoff_ms"]) / 1000
        cutoff_valid = captured.tzinfo is not None and 0 <= captured.timestamp() - cutoff <= 5
    except (KeyError, TypeError, ValueError, OverflowError):
        cutoff_valid = False
    return {
        "capture_sha256": capture.get("machine_observation_sha256"),
        "setup_evidence_sha256": evidence.get("evidence_sha256"),
        "flow_observation_sha256": flow.get("flow_observation_sha256"),
        "decision_snapshot_id": context.get("snapshot_id"),
        "snapshot_identity_matches": bool(context.get("snapshot_id") and context.get("snapshot_id") == snapshot.get("snapshot_id")),
        "venue_session_matches": all(str(context.get(k) or "").upper() == str(snapshot.get(k) or "").upper() and bool(context.get(k)) for k in ("effective_venue", "session_bucket")),
        "bundle_sha256": capture.get("bundle_sha256"),
        "effective_venue": context.get("effective_venue"),
        "session_bucket": context.get("session_bucket"),
        "flow_source_quality_status": (flow.get("source_quality") or {}).get("status"),
        "micro_recovery": evidence.get("micro_recovery_observation") or {},
        "reaction_context": reaction,
        "micro_window": window,
        "micro_window_cutoff_valid": cutoff_valid,
        "micro_window_item_matches": bool(expected_item and window.get("item") == expected_item),
        "source_authority": "hash_verified_exact_machine_capture_not_legacy_score_join",
    }



def summarize_machine_capture_population(captures: list[dict]) -> dict:
    """Preserve verified capture coverage before any cost/outcome exclusion."""
    partitions = {}
    seen = set()
    duplicates = 0
    for capture in captures:
        digest = capture.get("machine_observation_sha256")
        if digest in seen:
            duplicates += 1
            continue
        seen.add(digest)
        binding = bind_machine_microstructure_source(capture)
        action = ((capture.get("source") or {}).get("assessment") or {}).get("action") or "UNKNOWN"
        key = (str(capture.get("captured_at") or "")[:10], binding.get("bundle_sha256"), binding.get("effective_venue"), str(binding.get("session_bucket") or "").upper(), action)
        partition = partitions.setdefault(key, {"source_date": key[0], "bundle_sha256": key[1], "effective_venue": key[2], "session_bucket": key[3], "machine_action": action, "capture_count": 0, "source_binding_counts": Counter()})
        partition["capture_count"] += 1
        bound = binding.get("snapshot_identity_matches") is True and binding.get("venue_session_matches") is True
        partition["source_binding_counts"]["exact_bound" if bound else "exact_source_gap"] += 1
        window = binding.get("micro_window") or {}
        partition["source_binding_counts"]["micro_window_source_gap" if window.get("action") == "SOURCE_UNAVAILABLE" or not window or not binding.get("micro_window_cutoff_valid") else "micro_window_observed"] += 1
    result = []
    for key in sorted(partitions, key=lambda key: tuple(str(x or "") for x in key)):
        partition = partitions[key]
        partition["source_binding_counts"] = dict(sorted(partition["source_binding_counts"].items()))
        result.append(partition)
    return {"verified_capture_count": len(captures), "unique_verified_capture_count": len(seen), "duplicate_capture_collapsed_count": duplicates, "partitions": result, "economic_exclusions_do_not_erase_capture_population": True}


def summarize_machine_microstructure_evaluation(cases: list[dict], *, source_receipt: dict, capture_census: dict | None = None) -> dict:
    """Use all deduplicated cases before the case table's 200-row export limit.

    Endpoint returns are descriptive counterfactuals, not realized strategy PnL
    or causal feature uplift. AI denominators contain only machine ENTER_NOW.
    """
    def finite(value):
        if isinstance(value, bool):
            return None
        try:
            number = float(value)
            return number if math.isfinite(number) else None
        except (TypeError, ValueError, OverflowError):
            return None

    from src.engine.scalping.ai_decision_quality import HORIZON_END_MAX_LAG_SEC

    groups = {}
    exclusions = Counter()
    bindings = Counter()
    ai_routes = Counter()
    economic_count = 0
    auxiliary_economic_count = 0
    for case in cases:
        binding = case.get("microstructure_evaluation_binding") or {}
        bound = bool(binding.get("capture_sha256") and binding.get("snapshot_identity_matches") is True and binding.get("venue_session_matches") is True and binding.get("bundle_sha256") == case.get("bundle_sha256"))
        recovery = binding.get("micro_recovery") or {}
        reaction = binding.get("reaction_context") or {}
        window = binding.get("micro_window") or {}
        bindings["exact_source_bound" if bound else "exact_source_gap"] += 1
        flow_usable = bound and binding.get("flow_source_quality_status") == "fresh_consistent" and recovery.get("source_usable") is True
        reaction_usable = bound and reaction.get("microstructure_reaction_context_status") == "ok"
        window_usable = bound and binding.get("micro_window_cutoff_valid") is True and binding.get("micro_window_item_matches") is True and window.get("source_quality_status") == "eligible" and window.get("action") != "SOURCE_UNAVAILABLE"
        bindings["flow_recovery_usable" if flow_usable else "flow_recovery_source_gap"] += 1
        bindings["reaction_context_usable" if reaction_usable else "reaction_context_source_gap"] += 1
        bindings["micro_window_usable" if window_usable else "micro_window_source_gap"] += 1
        action = case.get("machine_action") or "UNKNOWN"
        ai = case.get("ai_and_final_guard") or {}
        verdict = "NOT_APPLICABLE_MACHINE_NONENTER"
        prompt = "NOT_APPLICABLE"
        if action == "ENTER_NOW":
            prompt = ai.get("prompt_version") or "UNKNOWN"
            if ai.get("join_status") != "exact_snapshot_machine_action_join":
                verdict = "EXACT_AI_JOIN_GAP"
            elif ai.get("provider_called") is not True:
                verdict = "PROVIDER_NOT_CALLED"
            elif ai.get("decision_quality_contract_status") != "pass" or ai.get("semantic_validation_status") not in {None, "pass"}:
                verdict = "SEMANTIC_INVALID"
            else:
                from src.engine.ai_prompt_contracts import MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS
                observed = str(ai.get("ai_risk_verdict") or "").upper()
                verdict = observed if prompt in MACHINE_AUXILIARY_COMPACT_ENTRY_PROMPT_VERSIONS and observed in {"PASS", "VETO", "CAUTION", "INSUFFICIENT"} else "UNREGISTERED_OR_INVALID_VERDICT"
            ai_routes[verdict] += 1
        key = (case.get("source_date"), case.get("bundle_sha256"), case.get("effective_venue"), case.get("session_bucket"), action, prompt, verdict)
        group = groups.setdefault(key, {"source_date": key[0], "bundle_sha256": key[1], "effective_venue": key[2], "session_bucket": key[3], "machine_action": action, "prompt_version": prompt, "ai_verdict": verdict, "case_count": 0, "classification_counts": Counter(), "net": [], "adverse": [], "flow_recovery_net": [], "reaction_context_net": [], "micro_window_net": []})
        group["case_count"] += 1
        group["classification_counts"][case.get("case_classification") or "UNKNOWN"] += 1
        cost = case.get("cost_evidence") or {}
        selected_cost = finite(cost.get("selected_economic_cost_pct"))
        metric = (case.get("outcome_horizon_metrics") or {}).get("3m") or {}
        end = finite(metric.get("end_return_pct"))
        path = case.get("entry_quality_path") or {}
        reason = None
        if case.get("policy_learning_excluded") is True:
            reason = case.get("policy_learning_exclusion_reason") or "lineage_excluded"
        elif case.get("exact_attempt_identity_complete") is not True or not bound:
            reason = "exact_identity_or_source_gap"
        elif selected_cost is None or selected_cost < 0 or cost.get("selected_cost_basis") not in {"executable_estimated_cost_pct", "broker_reconciled_cost_pct"} or not cost.get("cost_source_sha256") or cost.get("missing_cost_imputed") is not False:
            reason = "full_cost_contract_gap"
        elif path.get("status") != "evaluable" or path.get("cadence_complete") is not True or metric.get("status") != "observed" or end is None:
            reason = "mature_cadence_outcome_gap"
        if reason:
            exclusions[reason] += 1
            continue
        economic_count += 1
        if action == "ENTER_NOW" and verdict in {"PASS", "VETO", "CAUTION"} and case.get("compact_partition_eligible") is True:
            auxiliary_economic_count += 1
        net = end - selected_cost
        group["net"].append(net)
        adverse = finite(metric.get("mae_pct"))
        if adverse is not None:
            group["adverse"].append(adverse - selected_cost)
        for usable, name in [(flow_usable, "flow_recovery_net"), (reaction_usable, "reaction_context_net"), (window_usable, "micro_window_net")]:
            if usable:
                group[name].append(net)

    def stats(values):
        values = sorted(values)
        return {"count": len(values), "mean_net_pct": mean(values) if values else None, "sum_equal_weight_net_pct": sum(values) if values else None, "p05_net_pct": values[int((len(values)-1)*0.05)] if values else None}

    partitions = []
    for key in sorted(groups, key=lambda k: tuple(str(x or "") for x in k)):
        group = groups[key]
        net = group.pop("net")
        adverse = group.pop("adverse")
        group["classification_counts"] = dict(sorted(group["classification_counts"].items()))
        group["cost_adjusted_3m_endpoint_cf"] = stats(net)
        group["worst_3m_cost_adjusted_path_mae_pct"] = min(adverse) if adverse else None
        for name in ("flow_recovery", "reaction_context", "micro_window"):
            group[name + "_usable_endpoint_cf"] = stats(group.pop(name + "_net"))
        partitions.append(group)
    return {
        "schema": MACHINE_EVALUATION_SCHEMA,
        "status": "evaluable_descriptive_counterfactual" if economic_count else "source_gap_no_cost_adjusted_outcomes",
        "capture_population": (capture_census or {}).get("microstructure_capture_population"),
        "capture_exclusion_counts": {key: value for key, value in (capture_census or {}).items() if key in {"invalid_capture", "unsupported_cohort", "machine_action_mismatch_excluded", "full_round_trip_cost_missing", "executable_reference_missing", "path_or_cost_missing", "machine_action_invalid"}},
        "case_count": len(cases), "cost_adjusted_outcome_count": economic_count,
        "exclusion_counts": dict(sorted(exclusions.items())),
        "denominator_preserved": len(cases) == economic_count + sum(exclusions.values()),
        "source_binding_counts": dict(sorted(bindings.items())),
        "machine_action_counts": dict(sorted(Counter(case.get("machine_action") or "UNKNOWN" for case in cases).items())),
        "machine_enter_ai_routing_counts": dict(sorted(ai_routes.items())),
        "ai_denominator_role": "exact_joined_provider_called_machine_ENTER_NOW_only; nonentry_AI_absence_is_not_a_gap",
        "partitions": partitions,
        "measurement_role": "equal_weight_3m_endpoint_counterfactual_minus_existing_full_cost; not_strategy_EV_or_causal_delta_EV",
        "outcome_window_contract": {"owner": "ai_decision_quality.mature_outcome_labels", "horizon_end_max_lag_sec": HORIZON_END_MAX_LAG_SEC, "endpoint_role": "last_observation_within_existing_3m_window_not_exact_close_or_fill"},
        "source_receipt_machine_tuning_input_allowed": source_receipt.get("machine_threshold_tuning_input_allowed") is True,
        "source_receipt_auxiliary_tuning_input_allowed": source_receipt.get("tuning_input_allowed") is True,
        "machine_tuning_input_allowed": source_receipt.get("machine_threshold_tuning_input_allowed") is True and economic_count > 0,
        "auxiliary_tuning_input_allowed": source_receipt.get("tuning_input_allowed") is True and auxiliary_economic_count > 0,
        "auxiliary_cost_adjusted_outcome_count": auxiliary_economic_count,
        "tuning_authority": "existing_machine_case_table_source_partition_terminal_holdout_and_promotion_gates_only; no_independent_feature_tuner",
        "actual_completed_ev_pct": None, "actual_net_profit": None, "causal_model_delta_ev_pct": None,
        "runtime_effect": False, "allowed_runtime_apply": False,
    }


def refresh_machine_evaluation_link(source_path: Path, *, report_root: Path) -> dict:
    """Late producer refresh: no raw pipeline replay, policy/env or provider calls."""
    before = source_path.stat()
    source_bytes = source_path.read_bytes()
    after = source_path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("machine_evaluation_parent_changed_during_read")
    source = json.loads(source_bytes)
    target_date = source.get("target_date")
    evaluation = ((source.get("hierarchical_entry_quality") or {}).get("machine_decision_case_table") or {}).get("microstructure_evaluation")
    if source.get("schema") != "ai_decision_action_outcome_calibration_v2" or source.get("runtime_effect") is not False or source.get("allowed_runtime_apply") is not False or not isinstance(target_date, str) or not isinstance(evaluation, dict) or evaluation.get("schema") != MACHINE_EVALUATION_SCHEMA:
        raise ValueError("exact_date_machine_evaluation_contract_missing")
    if datetime.strptime(target_date, "%Y-%m-%d").date().isoformat() != target_date or target_date < _DEFAULT_CLEAN_BASELINE_DATE:
        raise ValueError("machine_evaluation_target_date_invalid")
    if source_path.name != f"ai_decision_action_outcome_calibration_{target_date}.json":
        raise ValueError("machine_evaluation_source_filename_date_mismatch")
    if any(part.get("source_date") and part["source_date"] > target_date for part in evaluation.get("partitions") or []):
        raise ValueError("future_machine_evaluation_partition")
    if evaluation.get("runtime_effect") is not False or evaluation.get("allowed_runtime_apply") is not False:
        raise ValueError("machine_evaluation_diagnostic_authority_invalid")
    path = report_root / "microstructure_reaction_context" / f"microstructure_reaction_context_{target_date}.json"
    if path.exists():
        report = json.loads(path.read_text())
        if report.get("date") != target_date:
            raise ValueError("microstructure_report_target_date_mismatch")
    else:
        report = {"schema_version": 6, "date": target_date, "report_type": "microstructure_reaction_context", "summary": {}, "warnings": [], "runtime_effect": False, "allowed_runtime_apply": False}
    # Keep an old report's statistics as explicitly historical, never as current inputs.
    if report.get("evaluation_mode") != "machine_primary_auxiliary_only":
        if path.exists():
            legacy_bytes = path.read_bytes()
            legacy_digest = hashlib.sha256(legacy_bytes).hexdigest()
            legacy_path = path.with_name(path.stem + ".legacy." + legacy_digest + ".json")
            if not legacy_path.exists():
                legacy_path.write_bytes(legacy_bytes)
        report = {
            "schema_version": 6, "date": target_date,
            "report_type": "microstructure_reaction_context",
            "legacy_generated_at": report.get("generated_at"),
            "legacy_source_sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            "summary": {}, "warnings": [], "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    if report.get("runtime_effect") is not False or report.get("allowed_runtime_apply") is not False:
        raise ValueError("existing_microstructure_diagnostic_authority_invalid")
    report["metric_role"] = "machine_auxiliary_source_outcome_diagnostic"
    report["window_policy"] = "existing_case_labeler_clean_baseline_through_exact_target_date"
    report["sample_floor"] = {"diagnostic": "source_valid_existing_cases", "promotion": "existing_owner_gates_only"}
    report["source_quality_gate"] = ["verified_capture_identity", "exact_date_parent_payload_and_hash", "full_cost_and_existing_path_cadence"]
    report["evaluation_mode"] = "machine_primary_auxiliary_only"
    report["decision_authority"] = "postclose_diagnostic_only"
    report["forbidden_uses"] = FORBIDDEN_USES
    report["legacy_study_status"] = "retired"
    report.setdefault("summary", {})["machine_primary_auxiliary_evaluation"] = {
        **evaluation, "source_report_path": str(source_path),
        "source_report_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_target_date": target_date,
    }
    report["primary_decision_metric"] = "machine_primary_auxiliary_full_cost_outcome_diagnostic"
    report["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    path.with_suffix(".md").write_text(render_microstructure_reaction_context_markdown(report))
    return report


def microstructure_summary_contract(summary: dict) -> dict:
    modern = dict(summary.get("machine_primary_auxiliary_evaluation") or {})
    if not modern:
        modern = {"schema": MACHINE_EVALUATION_SCHEMA, "status": "source_gap_exact_date_machine_evaluation_not_generated", "actual_completed_ev_pct": None, "runtime_effect": False, "allowed_runtime_apply": False}
    elif modern.get("source_report_path") and modern.get("source_report_sha256"):
        try:
            path = Path(modern["source_report_path"])
            before = path.stat()
            source_bytes = path.read_bytes()
            digest = hashlib.sha256(source_bytes).hexdigest()
            parent = json.loads(source_bytes)
            after = path.stat()
            valid = digest == modern.get("source_report_sha256") and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            expected = ((parent.get("hierarchical_entry_quality") or {}).get("machine_decision_case_table") or {}).get("microstructure_evaluation")
            observed = {k: v for k, v in modern.items() if k not in {"source_report_path", "source_report_sha256", "source_target_date"}}
            valid = valid and parent.get("target_date") == modern.get("source_target_date") and path.name == f"ai_decision_action_outcome_calibration_{modern.get('source_target_date')}.json" and expected == observed and parent.get("schema") == "ai_decision_action_outcome_calibration_v2" and parent.get("runtime_effect") is False and parent.get("allowed_runtime_apply") is False
        except (OSError, ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            modern.update(status="source_gap_machine_evaluation_parent_hash_mismatch", machine_tuning_input_allowed=False, auxiliary_tuning_input_allowed=False)
    else:
        modern.update(status="source_gap_machine_evaluation_parent_hash_mismatch", machine_tuning_input_allowed=False, auxiliary_tuning_input_allowed=False)
    cumulative = {"status": "retired"}
    cumulative.update(
        {
            "runtime_application": "not_applicable_diagnostic",
            "runtime_reflection_status": "not_applicable_diagnostic",
            "candidate_review_required": False,
            "required_runtime_reflection_actions": [],
        }
    )
    return {
        **{
            key: summary.get(key)
            for key in (
                "machine_primary_auxiliary_evaluation",
                "v_pw_runtime_support_unknown_count",
                "delivery_telemetry_v3_unique_count",
                "delivery_applicability_unknown_row_count",
                "context_applicable_count",
                "context_reused_count",
                "context_payload_included_count",
                "provider_delivery_required_count",
                "context_delivery_unconfirmed_count",
                "computed_coverage_pct",
                "provider_delivery_coverage_pct",
                "internal_consumption_required_count",
                "internal_consumption_coverage_pct",
                "diagnostic_contract_violation_counts",
                "code_improvement_order_ids",
            )
        },
        "legacy_study_status": "retired",
        "row_count": None,
        "ok_count": None,
        "missing_or_unusable_count": None,
        "computed_coverage_pct": None,
        "provider_delivery_coverage_pct": None,
        "internal_consumption_coverage_pct": None,
        "code_improvement_order_ids": [],
        "machine_primary_auxiliary_evaluation": modern,
        "clean_baseline_cumulative_opportunity_exploration": cumulative,
        "runtime_application": "not_applicable_diagnostic",
        "applied_effect": "not_evaluated",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


_ENTRY_OPPORTUNITY_STAGES = {
    "ai_confirmed",
    "ai_confirmed_terminal_no_budget",
    "blocked_ai_score",
    "pre_submit_entry_ai_authority_guard_block",
    "pre_submit_entry_ai_authority_retry",
    "rising_missed_tick_speed_entry_block",
    "scalp_entry_action_decision_snapshot",
    "watching_analyze_target",
}
_DEFAULT_CLEAN_BASELINE_DATE = "2026-06-05"

CONTEXT_KEYS = (
    "microstructure_reaction_context_version",
    "microstructure_reaction_context_status",
    "microstructure_reaction_tick_aggressor_pressure_usable",
    "microstructure_reaction_tick_aggressor_trusted_count",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
    "microstructure_reaction_entry_reaction_quality",
    "microstructure_reaction_source_quality",
    "microstructure_reaction_quote_stale_threshold_ms",
    "microstructure_reaction_context_computed",
    "microstructure_reaction_delivery_telemetry_version",
    "microstructure_reaction_context_sent",
    "microstructure_reaction_context_consumed",
    "microstructure_reaction_context_consumer",
    "microstructure_reaction_context_delivery_state",
    "microstructure_reaction_context_hash",
    "tick_trade_value_source_counts",
    "tick_trade_value_1313_count",
    "tick_trade_value_1313_missing_count",
    "tick_trade_value_1313_missing_rate_pct",
    "trade_volume_source_counts",
    "trade_volume_1030_1031_vs_15_evaluable_count",
    "trade_volume_1030_1031_vs_15_mismatch_count",
    "trade_volume_1030_1031_vs_15_mismatch_rate_pct",
    "trade_volume_1030_1031_vs_15_comparison_contract",
    "trade_volume_1030_1031_vs_15_decision_usable",
    "tick_aggressor_source_counts",
    "kiwoom_0b_aux_observed_count",
    "kiwoom_0b_1313_present_count",
    "kiwoom_0b_1313_missing_count",
    "kiwoom_0b_1313_missing_rate_pct",
    "kiwoom_0b_trade_value_source_counts",
    "kiwoom_0b_trade_volume_source_counts",
    "kiwoom_0b_1030_1031_vs_15_evaluable_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_count",
    "kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct",
    "ka10003_buy_dominance_observation",
    "ka10003_buy_dominance_observation_source_counts",
    "ka10003_buy_dominance_observation_trade_value_source_counts",
    "ka10003_buy_dominance_observation_inside_spread_count",
    "ka10003_buy_dominance_observation_split_vs_15_evaluable_count",
    "ka10003_buy_dominance_observation_split_vs_15_mismatch_count",
    "v_pw_now",
    "v_pw_source",
    "v_pw_runtime_support_usable",
    "v_pw_ws_value",
    "v_pw_rest_value",
    "ka10046_strength_source",
    "ka10046_strength_decision_authority",
    "ka10046_strength_runtime_effect",
    "ka10046_strength_rest_received_ts_ms",
    "market_data_signed_tape_state",
    "market_data_signed_tape_sample_count",
    "market_data_signed_tape_buy_count",
    "market_data_signed_tape_sell_count",
    "market_data_signed_tape_buy_volume",
    "market_data_signed_tape_sell_volume",
    "market_data_signed_tape_buy_ratio_pct",
    "market_data_rest_signed_tape_pressure_usable",
    "rest_signed_trade_ticks",
    "latency_true_ofi_direct_canary_signed_tape_window",
    "latency_true_ofi_direct_canary_signed_tape_min_samples",
    "latency_true_ofi_direct_canary_signed_tape_max_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_sample_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_count",
    "latency_true_ofi_direct_canary_signed_tape_sell_count",
    "latency_true_ofi_direct_canary_signed_tape_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_sell_volume",
    "latency_true_ofi_direct_canary_signed_tape_net_buy_volume",
    "latency_true_ofi_direct_canary_signed_tape_buy_ratio",
    "latency_true_ofi_direct_canary_signed_tape_latest_side",
    "latency_true_ofi_direct_canary_signed_tape_sell_dominated",
    "latency_true_ofi_direct_canary_signed_tape_latest_buy_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_sell_single",
    "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated",
    "latency_true_ofi_direct_canary_tape_block_reason",
    "latency_true_ofi_direct_canary_tape_support_ok",
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
) + DELIVERY_KEYS

GENERIC_FRESHNESS_CONTEXT_KEYS = {
    "quote_stale",
    "quote_age_ms",
    "quote_age_at_submit_ms",
    "ws_age_ms",
    "market_data_freshness_state",
}

FORBIDDEN_USES = [
    "standalone_buy",
    "broker_guard_bypass",
    "threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "cap_release",
]

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        if isinstance(value, bool):
            return default
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _rate_pct(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 3) if denominator > 0 else 0.0


def _dict_counter(value: Any) -> Counter:
    if isinstance(value, dict):
        return Counter(
            {str(key): int(_safe_float(count, 0.0)) for key, count in value.items()}
        )
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, dict):
                return Counter(
                    {
                        str(key): int(_safe_float(count, 0.0))
                        for key, count in parsed.items()
                    }
                )
    return Counter()


def _list_value(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, list):
                return parsed
    return []


def _safe_hhmmss_to_seconds(value: Any) -> int | None:
    try:
        text = str(value or "").replace(":", "").strip()
        if not text:
            return None
        if not text.isdigit():
            return None
        text = text.zfill(6)
        hour = int(text[0:2])
        minute = int(text[2:4])
        second = int(text[4:6])
        if hour > 23 or minute > 59 or second > 59:
            return None
        return (hour * 3600) + (minute * 60) + second
    except Exception:
        return None


def _normalize_tick_side(value: Any) -> str:
    raw = str(value or "").strip().upper()
    compact = raw.replace("+", "").replace("-", "").replace(" ", "")
    if raw in {"BUY", "B", "2"} or "매수" in compact:
        return "BUY"
    if raw in {"SELL", "S", "1"} or "매도" in compact:
        return "SELL"
    return raw


def _tick_price(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("price")
        or tick.get("trade_price")
        or tick.get("cur_prc")
        or tick.get("현재가")
        or tick.get("체결가"),
        0.0,
    )


def _tick_best_ask(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_ask")
        or tick.get("ask_price")
        or tick.get("ask")
        or tick.get("27"),
        0.0,
    )


def _tick_best_bid(tick: dict[str, Any]) -> float:
    return _safe_float(
        tick.get("best_bid")
        or tick.get("bid_price")
        or tick.get("bid")
        or tick.get("28"),
        0.0,
    )


TRUSTED_AGGRESSOR_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
    "kiwoom_0b_signed_trade_volume",
    "provider_declared_side",
    "exchange_declared_side",
    "trusted_declared_side",
    "declared_aggressor_side",
}

ORDERBOOK_TOUCH_SOURCES = {
    "orderbook_touch",
    "cached_orderbook_touch",
}

ORDERBOOK_TOUCH_QUOTE_SOURCES = {
    "0B_inline_best_quote",
    "cached_top_of_book_ttl",
}


def infer_tick_aggressor_side(tick: dict[str, Any] | None) -> dict[str, Any]:
    tick = tick if isinstance(tick, dict) else {}
    declared_source = str(
        tick.get("aggressor_source") or tick.get("dir_source") or ""
    ).strip()
    declared_quality = str(tick.get("aggressor_quality") or "").strip()
    quote_source = str(tick.get("aggressor_quote_source") or "").strip()
    touch_source = (
        "cached_orderbook_touch"
        if declared_source == "cached_orderbook_touch"
        or quote_source == "cached_top_of_book_ttl"
        else "orderbook_touch"
    )

    def _touch_quality(default: str) -> str:
        if declared_quality and (
            declared_source in {"orderbook_touch", "cached_orderbook_touch"}
            or quote_source
        ):
            return declared_quality
        return default

    explicit = _normalize_tick_side(
        tick.get("aggressor_side")
        or tick.get("trade_aggressor_side")
        or tick.get("dir")
        or tick.get("side")
    )
    trade_price = _tick_price(tick)
    best_ask = _tick_best_ask(tick)
    best_bid = _tick_best_bid(tick)
    if (
        explicit in {"BUY", "SELL"}
        and declared_source == "kiwoom_0b_signed_trade_volume"
    ):
        return {
            "side": explicit,
            "source": declared_source,
            "quality": declared_quality or "signed_trade_volume",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
            "touch_side": str(tick.get("aggressor_touch_side") or "UNKNOWN"),
            "touch_source": str(tick.get("aggressor_touch_source") or ""),
            "touch_quality": str(tick.get("aggressor_touch_quality") or ""),
            "touch_confirms_signed": tick.get("aggressor_touch_confirms_signed"),
        }
    if trade_price > 0 and (best_ask > 0 or best_bid > 0):
        raw_inline_quote = (
            not declared_source and not quote_source and ("27" in tick or "28" in tick)
        )
        trusted_touch_source = (
            declared_source in ORDERBOOK_TOUCH_SOURCES
            or quote_source in ORDERBOOK_TOUCH_QUOTE_SOURCES
            or raw_inline_quote
        )
        if not trusted_touch_source:
            return {
                "side": "UNKNOWN",
                "source": declared_source or "untrusted_orderbook_touch_source",
                "quality": "quote_with_untrusted_aggressor_source",
                "declared_side": explicit if explicit in {"BUY", "SELL"} else "UNKNOWN",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask <= 0 or best_bid <= 0:
            return {
                "side": "UNKNOWN",
                "source": "missing_best_quote",
                "quality": "partial_orderbook_touch_quote",
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_ask > 0 and trade_price >= best_ask:
            return {
                "side": "BUY",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_ask"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        if best_bid > 0 and trade_price <= best_bid:
            return {
                "side": "SELL",
                "source": touch_source,
                "quality": _touch_quality("touch_or_crossed_bid"),
                "trade_price": trade_price,
                "best_ask": best_ask,
                "best_bid": best_bid,
            }
        return {
            "side": "UNKNOWN",
            "source": touch_source,
            "quality": _touch_quality("inside_spread_or_uncertain"),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"} and declared_source in TRUSTED_AGGRESSOR_SOURCES:
        return {
            "side": explicit,
            "source": declared_source,
            "quality": str(
                tick.get("aggressor_quality") or "side_without_orderbook_touch"
            ),
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    if explicit in {"BUY", "SELL"}:
        return {
            "side": "UNKNOWN",
            "source": declared_source or "declared_tick_side_untrusted",
            "quality": "side_without_trusted_source",
            "declared_side": explicit,
            "trade_price": trade_price,
            "best_ask": best_ask,
            "best_bid": best_bid,
        }
    return {
        "side": "UNKNOWN",
        "source": "missing_aggressor_side",
        "quality": "missing_orderbook_touch_and_side",
        "trade_price": trade_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
    }


def _aggressor_pressure_usable(inferred: dict[str, Any] | None) -> bool:
    inferred = inferred if isinstance(inferred, dict) else {}
    if inferred.get("side") not in {"BUY", "SELL"}:
        return False
    return str(inferred.get("source") or "").strip() in TRUSTED_AGGRESSOR_SOURCES


def _tick_volume_pressure_usable(tick: dict[str, Any] | None) -> bool:
    tick = tick if isinstance(tick, dict) else {}
    source = str(
        tick.get("volume_source") or tick.get("trade_volume_source") or ""
    ).strip()
    # Legacy/test rows without explicit provenance remain usable. Once the WS
    # producer declares a source, cumulative 1030/1031 totals must not acquire
    # per-tick pressure authority.
    return not source or source in TRUSTED_TICK_VOLUME_SOURCES


def _age_ms_from_hhmmss(value: Any, *, now: datetime | None = None) -> int | None:
    tick_sec = _safe_hhmmss_to_seconds(value)
    if tick_sec is None:
        return None
    # HHMMSS is a Korean market wall clock, not the caller's timezone.
    # Preserve legacy naive KST inputs; aware inputs keep their exact instant.
    now_dt = now or datetime.now(KST)
    if now_dt.tzinfo is not None:
        now_dt = now_dt.astimezone(KST)
    now_sec = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    age_sec = now_sec - tick_sec
    if age_sec < -43200:
        age_sec += 86400
    elif age_sec > 43200:
        age_sec -= 86400
    return int(age_sec * 1000)


def _safe_epoch_ms(value: Any) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        numeric = float(value)
        if not math.isfinite(numeric) or numeric <= 0:
            return None
        if numeric > 1_000_000_000_000:
            return int(numeric)
        if numeric > 1_000_000_000:
            return int(numeric * 1000)
    except (TypeError, ValueError):
        pass
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        return int(datetime.fromisoformat(text).timestamp() * 1000)
    except Exception:
        return None


def _quote_age_ms(
    ws_data: dict[str, Any], *, now: datetime | None = None
) -> tuple[int | None, str]:
    if "last_realtime_type_ts" in ws_data or "last_ws_update_ts" in ws_data:
        from src.trading.market.quote_consistency import ws_quote_receive_age_ms

        age = ws_quote_receive_age_ms(ws_data, now_ts=(now or datetime.now()).timestamp())
        basis = "last_realtime_type_ts:0D" if "last_realtime_type_ts" in ws_data else "last_ws_update_ts"
        return age, basis if age is not None else "invalid_quote_receive_timestamp"
    quote_ts_keys = (
        "quote_age_ms",
        "ws_age_ms",
        "ws_received_at_ms",
        "quote_received_at_ms",
        "received_at_ms",
        "last_ws_update_ts",
        "last_update_ms",
        "updated_at_ms",
        "captured_at_ms",
        "timestamp_ms",
        "ts_ms",
        "updated_at",
        "timestamp",
    )
    now_ms = int((now or datetime.now()).timestamp() * 1000)
    for key in quote_ts_keys:
        raw = ws_data.get(key)
        if raw in (None, "", "-"):
            continue
        if key in {"quote_age_ms", "ws_age_ms"}:
            age_value = _safe_float(raw, float("nan"))
            if isinstance(raw, bool) or not math.isfinite(age_value):
                return None, "invalid_" + key
            return age_value, key
        epoch_ms = _safe_epoch_ms(raw)
        if epoch_ms is None:
            continue
        return now_ms - epoch_ms, key
    return None, "missing"


def precompute_microstructure_reaction_inputs(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | float | int | None = None,
) -> dict[str, Any]:
    if isinstance(now, (int, float)):
        now = datetime.fromtimestamp(float(now), tz=KST)
    elif now is not None and not isinstance(now, datetime):
        now = None
    ws_data = ws_data if isinstance(ws_data, dict) else {}
    recent_ticks = recent_ticks if isinstance(recent_ticks, list) else []
    recent_candles = recent_candles if isinstance(recent_candles, list) else []
    orderbook = (
        ws_data.get("orderbook") if isinstance(ws_data.get("orderbook"), dict) else {}
    )
    asks = [
        level
        for level in (
            orderbook.get("asks") if isinstance(orderbook.get("asks"), list) else []
        )
        if isinstance(level, dict)
    ]
    bids = [
        level
        for level in (
            orderbook.get("bids") if isinstance(orderbook.get("bids"), list) else []
        )
        if isinstance(level, dict)
    ]
    curr_price = _safe_float(ws_data.get("curr") or ws_data.get("curr_price"), 0.0)
    best_ask = _safe_float(asks[0].get("price") if asks else 0, curr_price)
    best_bid = _safe_float(bids[0].get("price") if bids else 0, curr_price)
    best_ask_vol = _safe_float(asks[0].get("volume") if asks else 0, 0.0)
    best_bid_vol = _safe_float(bids[0].get("volume") if bids else 0, 0.0)
    top3_ask_vol = sum(_safe_float(level.get("volume"), 0.0) for level in asks[:3])
    top3_bid_vol = sum(_safe_float(level.get("volume"), 0.0) for level in bids[:3])
    ticks = [tick for tick in recent_ticks[:10] if isinstance(tick, dict)]
    tick_latest_time = str(ticks[0].get("time") or "") if ticks else ""
    tick_age_ms = (
        _age_ms_from_hhmmss(tick_latest_time, now=now) if tick_latest_time else None
    )
    tick_secs = [_safe_hhmmss_to_seconds(tick.get("time")) for tick in ticks]
    aggressor_rows = [infer_tick_aggressor_side(tick) for tick in ticks]
    tick_trade_value_source_counts = Counter(
        str(tick.get("tick_trade_value_source") or "unknown")
        for tick in ticks
        if "tick_trade_value_source" in tick
    )
    tick_trade_value_observed_count = sum(tick_trade_value_source_counts.values())
    tick_trade_value_1313_count = tick_trade_value_source_counts.get("1313", 0)
    tick_trade_value_1313_missing_count = max(
        0,
        tick_trade_value_observed_count - tick_trade_value_1313_count,
    )
    trade_volume_source_counts = Counter(
        str(tick.get("volume_source") or tick.get("trade_volume_source") or "unknown")
        for tick in ticks
        if "volume_source" in tick or "trade_volume_source" in tick
    )
    trade_volume_mismatch_rows = [
        tick for tick in ticks if "trade_volume_1030_1031_vs_15_mismatch" in tick
    ]
    trade_volume_mismatch_count = sum(
        1
        for tick in trade_volume_mismatch_rows
        if _safe_bool(tick.get("trade_volume_1030_1031_vs_15_mismatch"), False)
    )
    candidate_pressure_rows = [
        (tick, inferred)
        for tick, inferred in zip(ticks, aggressor_rows)
        if _aggressor_pressure_usable(inferred) and _tick_volume_pressure_usable(tick)
    ]
    explicit_untrusted_volume_present = any(
        not _tick_volume_pressure_usable(tick)
        for tick in ticks
        if tick.get("volume_source") or tick.get("trade_volume_source")
    )
    pressure_rows = [] if explicit_untrusted_volume_present else candidate_pressure_rows
    trusted_tick_prices = [
        int(_safe_float(tick.get("price"), 0.0))
        for tick, _inferred in pressure_rows
        if _safe_float(tick.get("price"), 0.0) > 0
    ]
    buy_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY"
    )
    sell_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "SELL"
    )
    total_vol = buy_vol + sell_vol
    buy_pressure_pct = (buy_vol / total_vol * 100.0) if total_vol > 0 else 50.0
    prices: list[float] = []
    volumes: list[float] = []
    pressure_volumes: list[float] = []
    for tick in ticks:
        price_value = _safe_float(tick.get("price"), 0.0)
        if price_value > 0:
            prices.append(price_value)
        volume_value = (
            _safe_float(tick.get("volume"), 0.0)
            if _tick_volume_pressure_usable(tick)
            else 0.0
        )
        if volume_value > 0:
            volumes.append(volume_value)
    for tick, _inferred in pressure_rows:
        volume_value = _safe_float(tick.get("volume"), 0.0)
        if volume_value > 0:
            pressure_volumes.append(volume_value)
    latest_price = prices[0] if prices else curr_price
    oldest_price = prices[-1] if prices else curr_price
    price_change_pct = (
        ((latest_price - oldest_price) / oldest_price * 100.0)
        if oldest_price > 0
        else 0.0
    )
    avg_tick_volume = mean(volumes) if volumes else 0.0
    avg_pressure_tick_volume = mean(pressure_volumes) if pressure_volumes else 0.0
    buy_at_or_above_ask_vol = sum(
        _safe_float(tick.get("volume"), 0.0)
        for tick, inferred in pressure_rows
        if inferred.get("side") == "BUY"
        and _safe_float(tick.get("price"), 0.0) >= best_ask
    )
    large_buy_print_detected = (
        any(
            _aggressor_pressure_usable(inferred)
            and inferred.get("side") == "BUY"
            and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
            for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
        )
        if avg_pressure_tick_volume > 0
        else False
    )
    large_sell_print_detected = (
        any(
            _aggressor_pressure_usable(inferred)
            and inferred.get("side") == "SELL"
            and _safe_float(tick.get("volume"), 0.0) >= avg_pressure_tick_volume * 2.2
            for tick, inferred in zip(ticks[:5], aggressor_rows[:5])
        )
        if avg_pressure_tick_volume > 0
        else False
    )
    price_buy_count: dict[float, int] = {}
    for tick, inferred in zip(ticks[:6], aggressor_rows[:6]):
        if not _aggressor_pressure_usable(inferred):
            continue
        if inferred.get("side") != "BUY":
            continue
        price_key = _safe_float(tick.get("price"), 0.0)
        price_buy_count[price_key] = price_buy_count.get(price_key, 0) + 1
    same_price_buy_absorption = max(price_buy_count.values()) if price_buy_count else 0
    candle_highs: list[float] = []
    candle_lows: list[float] = []
    for candle in recent_candles:
        if not isinstance(candle, dict):
            continue
        high_value = _safe_float(candle.get("고가"), 0.0)
        if high_value > 0:
            candle_highs.append(high_value)
        low_value = _safe_float(candle.get("저가"), 0.0)
        if low_value > 0:
            candle_lows.append(low_value)
    quote_age_ms, quote_age_source = _quote_age_ms(ws_data, now=now)
    return {
        "ws_data": ws_data,
        "recent_ticks": recent_ticks,
        "recent_candles": recent_candles,
        "asks": asks,
        "bids": bids,
        "curr_price": curr_price,
        "best_ask": best_ask,
        "best_bid": best_bid,
        "best_ask_vol": best_ask_vol,
        "best_bid_vol": best_bid_vol,
        "top3_ask_vol": top3_ask_vol,
        "top3_bid_vol": top3_bid_vol,
        "ticks": ticks,
        "tick_aggressor_rows": aggressor_rows,
        "tick_aggressor_source_counts": dict(
            Counter(str(row.get("source") or "unknown") for row in aggressor_rows)
        ),
        "tick_aggressor_quality_counts": dict(
            Counter(str(row.get("quality") or "unknown") for row in aggressor_rows)
        ),
        "tick_trade_value_source_counts": dict(
            sorted(tick_trade_value_source_counts.items())
        ),
        "tick_trade_value_1313_count": int(tick_trade_value_1313_count),
        "tick_trade_value_1313_missing_count": int(tick_trade_value_1313_missing_count),
        "tick_trade_value_1313_missing_rate_pct": _rate_pct(
            tick_trade_value_1313_missing_count,
            tick_trade_value_observed_count,
        ),
        "trade_volume_source_counts": dict(sorted(trade_volume_source_counts.items())),
        "trade_volume_1030_1031_vs_15_evaluable_count": len(trade_volume_mismatch_rows),
        "trade_volume_1030_1031_vs_15_mismatch_count": int(trade_volume_mismatch_count),
        "trade_volume_1030_1031_vs_15_mismatch_rate_pct": _rate_pct(
            trade_volume_mismatch_count,
            len(trade_volume_mismatch_rows),
        ),
        "tick_aggressor_unknown_count": sum(
            1 for row in aggressor_rows if row.get("side") not in {"BUY", "SELL"}
        ),
        "tick_aggressor_orderbook_touch_count": sum(
            1 for row in aggressor_rows if row.get("source") == "orderbook_touch"
        ),
        "tick_aggressor_cached_orderbook_touch_count": sum(
            1 for row in aggressor_rows if row.get("source") == "cached_orderbook_touch"
        ),
        "tick_aggressor_price_heuristic_count": sum(
            1 for row in aggressor_rows if row.get("source") == "price_change_heuristic"
        ),
        # This count is consumed as an authority signal in entry/holding
        # guards.  Keep it aligned with pressure_rows rather than exposing
        # otherwise trusted rows from a mixed window that was failed closed.
        "tick_aggressor_trusted_count": len(pressure_rows),
        "tick_aggressor_pressure_usable": bool(pressure_rows),
        # Newest-first prices from the same rows that own trusted pressure.
        # Consumers must not substitute heuristic/untrusted tick prices.
        "trusted_tick_prices": trusted_tick_prices,
        "tick_sample_count": len(ticks),
        "tick_latest_time": tick_latest_time,
        "tick_age_ms": tick_age_ms,
        "tick_secs": tick_secs,
        "buy_vol": buy_vol,
        "sell_vol": sell_vol,
        "total_vol": total_vol,
        "buy_pressure_pct": buy_pressure_pct,
        "latest_price": latest_price,
        "oldest_price": oldest_price,
        "price_change_pct": price_change_pct,
        "avg_tick_volume": avg_tick_volume,
        "buy_at_or_above_ask_vol": buy_at_or_above_ask_vol,
        "large_buy_print_detected": large_buy_print_detected,
        "large_sell_print_detected": large_sell_print_detected,
        "same_price_buy_absorption": same_price_buy_absorption,
        "quote_age_ms": quote_age_ms,
        "quote_age_source": quote_age_source,
        "market_data_health": build_market_data_health(
            ws_data, now_ts=(now or datetime.now()).timestamp(),
            quote_max_age_ms=normalize_quote_stale_threshold(ws_data.get("ai_quote_stale_max_ms"))[0],
        ),
        "candle_highs": candle_highs,
        "candle_lows": candle_lows,
        "session_high": max(candle_highs or [curr_price]),
        "session_low": min(candle_lows or [curr_price]),
    }


def _context_hash(payload: dict[str, Any]) -> str:
    compact = {
        key: payload.get(key)
        for key in CONTEXT_KEYS
        if key != "microstructure_reaction_context_hash"
        and (key not in DELIVERY_KEYS or key.endswith("quote_stale_threshold_ms"))
    }
    raw = json.dumps(compact, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def neutral_microstructure_reaction_context(
    status: str,
    reason: str,
    *,
    quote_stale_threshold_ms: int = DEFAULT_QUOTE_STALE_MS,
) -> dict[str, Any]:
    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": status,
        "microstructure_reaction_tick_aggressor_pressure_usable": False,
        "microstructure_reaction_tick_aggressor_trusted_count": 0,
        "microstructure_reaction_ask_sweep_score": 50,
        "microstructure_reaction_post_sweep_hold_score": 50,
        "microstructure_reaction_bid_replenishment_score": 50,
        "microstructure_reaction_wall_replenishment_risk_score": 50,
        "microstructure_reaction_vi_proximity_risk": 0,
        "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
        "microstructure_reaction_source_quality": reason,
        "microstructure_reaction_quote_stale_threshold_ms": max(
            1, int(quote_stale_threshold_ms)
        ),
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    payload["microstructure_reaction_context_id"] = uuid4().hex
    return payload


def _calculate_microstructure_reaction_context(
    ws_data: dict[str, Any] | None,
    recent_ticks: list[dict[str, Any]] | None,
    recent_candles: list[dict[str, Any]] | None = None,
    *,
    now: datetime | None = None,
    precomputed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = (
        precomputed
        if isinstance(precomputed, dict)
        else precompute_microstructure_reaction_inputs(
            ws_data,
            recent_ticks,
            recent_candles,
            now=now,
        )
    )
    ws_data = (
        snapshot.get("ws_data") if isinstance(snapshot.get("ws_data"), dict) else {}
    )
    recent_candles = (
        snapshot.get("recent_candles")
        if isinstance(snapshot.get("recent_candles"), list)
        else []
    )
    asks = snapshot.get("asks") if isinstance(snapshot.get("asks"), list) else []
    bids = snapshot.get("bids") if isinstance(snapshot.get("bids"), list) else []
    quote_stale_threshold_ms, setting_status = normalize_quote_stale_threshold(
        snapshot.get("ai_quote_stale_max_ms", ws_data.get("ai_quote_stale_max_ms"))
    )
    if setting_status == "invalid":
        payload = neutral_microstructure_reaction_context(
            "source_quality_partial",
            "invalid_quote_threshold_setting",
            quote_stale_threshold_ms=quote_stale_threshold_ms,
        )
        payload["microstructure_reaction_quote_threshold_setting_status"] = (
            setting_status
        )
        return payload
    if not asks or not bids:
        return neutral_microstructure_reaction_context(
            "source_quality_missing",
            "missing_orderbook",
            quote_stale_threshold_ms=quote_stale_threshold_ms,
        )
    if int(snapshot.get("tick_sample_count") or 0) < 5:
        return neutral_microstructure_reaction_context(
            "insufficient_window",
            "tick_sample_lt5",
            quote_stale_threshold_ms=quote_stale_threshold_ms,
        )

    tick_age_ms = snapshot.get("tick_age_ms")
    quote_age_ms = snapshot.get("quote_age_ms")
    for name, age in (("tick", tick_age_ms), ("quote", quote_age_ms)):
        if (
            age is None
            or isinstance(age, bool)
            or not isinstance(age, (float, int))
            or not math.isfinite(age)
            or age < 0
        ):
            return neutral_microstructure_reaction_context(
                "source_quality_missing" if age is None else "source_quality_partial",
                f"missing_{name}_time" if age is None else f"invalid_{name}_age",
                quote_stale_threshold_ms=quote_stale_threshold_ms,
            )
    if (tick_age_ms is not None and tick_age_ms > 5000) or (
        quote_age_ms is not None and quote_age_ms > quote_stale_threshold_ms
    ):
        return neutral_microstructure_reaction_context(
            "stale",
            "stale_tick_or_quote",
            quote_stale_threshold_ms=quote_stale_threshold_ms,
        )
    curr_price = _safe_float(snapshot.get("curr_price"), 0.0)
    best_ask = _safe_float(snapshot.get("best_ask"), curr_price)
    best_bid = _safe_float(snapshot.get("best_bid"), curr_price)
    top3_ask_vol = _safe_float(snapshot.get("top3_ask_vol"), 0.0)
    top3_bid_vol = _safe_float(snapshot.get("top3_bid_vol"), 0.0)
    top3_depth_ratio = top3_ask_vol / top3_bid_vol if top3_bid_vol > 0 else 9.99

    sell_vol = _safe_float(snapshot.get("sell_vol"), 0.0)
    total_vol = _safe_float(snapshot.get("total_vol"), 0.0)
    pressure_usable = (
        _safe_bool(snapshot.get("tick_aggressor_pressure_usable"), False)
        and total_vol > 0
    )
    pressure_trusted_count = _safe_int(snapshot.get("tick_aggressor_trusted_count"), 0)
    if not pressure_usable:
        payload = neutral_microstructure_reaction_context(
            "source_quality_partial",
            "tick_aggressor_pressure_unusable",
            quote_stale_threshold_ms=quote_stale_threshold_ms,
        )
        payload["microstructure_reaction_tick_aggressor_trusted_count"] = (
            pressure_trusted_count
        )
        payload["microstructure_reaction_context_hash"] = _context_hash(payload)
        return payload
    buy_pressure = _safe_float(snapshot.get("buy_pressure_pct"), 50.0)
    latest_price = _safe_float(snapshot.get("latest_price"), curr_price)
    price_change_pct = _safe_float(snapshot.get("price_change_pct"), 0.0)
    buy_at_or_above_ask = _safe_float(snapshot.get("buy_at_or_above_ask_vol"), 0.0)
    ask_sweep_share = buy_at_or_above_ask / total_vol if total_vol > 0 else 0.0
    avg_vol = _safe_float(snapshot.get("avg_tick_volume"), 0.0)
    large_buy = bool(snapshot.get("large_buy_print_detected")) if avg_vol > 0 else False
    large_sell = (
        bool(snapshot.get("large_sell_print_detected")) if avg_vol > 0 else False
    )

    ask_sweep_score = _clamp_score(
        35
        + (buy_pressure - 50) * 0.7
        + ask_sweep_share * 35
        + (12 if price_change_pct > 0 else 0)
        + (8 if large_buy else 0)
    )
    post_sweep_hold_score = _clamp_score(
        50
        + min(25, max(-25, price_change_pct * 45))
        + (12 if latest_price >= best_ask else 0)
        - (15 if latest_price < best_bid else 0)
    )
    bid_ratio = top3_bid_vol / top3_ask_vol if top3_ask_vol > 0 else 2.0
    bid_replenishment_score = _clamp_score(
        45
        + min(30, bid_ratio * 14)
        + (10 if sell_vol > 0 and price_change_pct >= -0.05 else 0)
        - (10 if latest_price < best_bid else 0)
    )
    wall_replenishment_risk_score = _clamp_score(
        25
        + max(0, top3_depth_ratio - 1.0) * 28
        + (16 if large_sell else 0)
        + (10 if buy_pressure < 55 else 0)
    )

    fluctuation = _safe_float(ws_data.get("fluctuation"), 0.0)
    high = _safe_float(snapshot.get("session_high"), curr_price)
    low = _safe_float(snapshot.get("session_low"), curr_price)
    distance_from_high = (
        ((curr_price - high) / high * 100.0) if high > 0 and curr_price > 0 else -99.0
    )
    intraday_range = ((high - low) / low * 100.0) if high >= low and low > 0 else 0.0
    vi_proximity_risk = _clamp_score(
        max(0, fluctuation - 20) * 6
        + (20 if distance_from_high >= -0.25 and intraday_range >= 12 else 0)
    )

    if wall_replenishment_risk_score >= 70 or vi_proximity_risk >= 70:
        quality = "risk_context_only"
    elif (
        ask_sweep_score >= 65
        and post_sweep_hold_score >= 60
        and bid_replenishment_score >= 55
    ):
        quality = "favorable_reaction"
    elif ask_sweep_score <= 40 or post_sweep_hold_score <= 40:
        quality = "weak_reaction"
    else:
        quality = "mixed_reaction"

    payload = {
        "microstructure_reaction_context_version": CONTEXT_VERSION,
        "microstructure_reaction_context_status": "ok",
        "microstructure_reaction_tick_aggressor_pressure_usable": bool(pressure_usable),
        "microstructure_reaction_tick_aggressor_trusted_count": pressure_trusted_count,
        "microstructure_reaction_ask_sweep_score": ask_sweep_score,
        "microstructure_reaction_post_sweep_hold_score": post_sweep_hold_score,
        "microstructure_reaction_bid_replenishment_score": bid_replenishment_score,
        "microstructure_reaction_wall_replenishment_risk_score": wall_replenishment_risk_score,
        "microstructure_reaction_vi_proximity_risk": vi_proximity_risk,
        "microstructure_reaction_entry_reaction_quality": quality,
        "microstructure_reaction_source_quality": "fresh_short_window",
        "microstructure_reaction_quote_stale_threshold_ms": (quote_stale_threshold_ms),
    }
    payload["microstructure_reaction_context_hash"] = _context_hash(payload)
    payload["microstructure_reaction_context_id"] = uuid4().hex
    payload["microstructure_reaction_quote_threshold_setting_status"] = setting_status
    return payload


def build_microstructure_reaction_context(
    ws_data, recent_ticks, recent_candles=None, *, now=None, precomputed=None
):
    if isinstance(now, (float, int)):
        now = datetime.fromtimestamp(now, tz=KST)
    elif not isinstance(now, datetime):
        now = datetime.now(KST)
    payload = _calculate_microstructure_reaction_context(
        ws_data, recent_ticks, recent_candles, now=now, precomputed=precomputed
    )
    source = ws_data if isinstance(ws_data, dict) else {}
    explicit_venues = {
        str(source.get(key) or "").upper()
        for key in (
            "effective_venue",
            "market_data_venue",
            "venue",
            "quote_source_market",
        )
    } & {"KRX", "NXT"}
    if isinstance(source.get("last_realtime_type_effective_venue"), dict):
        from src.engine.scalping.ai_market_snapshot import realtime_type_provenance

        explicit_venues.update(
            str(row.get("effective_venue"))
            for row in realtime_type_provenance(
                source, now_ts=(now or datetime.now()).timestamp()
            ).values()
            if row.get("quality") == "fresh"
            and row.get("effective_venue") in {"KRX", "NXT"}
        )
    quote_threshold, setting = normalize_quote_stale_threshold(
        (precomputed or {}).get(
            "ai_quote_stale_max_ms", source.get("ai_quote_stale_max_ms")
        )
    )
    payload["market_data_health"] = build_market_data_health(
        source, now_ts=now.timestamp(), quote_max_age_ms=quote_threshold,
    )
    payload.update(
        {
            "microstructure_reaction_reference_time": (
                now or datetime.now()
            ).isoformat(),
            "microstructure_reaction_reference_price": source.get("curr")
            or source.get("curr_price"),
            "microstructure_reaction_venue": (
                next(iter(explicit_venues)) if len(explicit_venues) == 1 else None
            ),
            "microstructure_reaction_quote_threshold_setting_status": setting,
        }
    )
    return payload


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"microstructure_reaction_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _has_context(fields: dict[str, Any]) -> bool:
    return any(
        key in fields
        for key in CONTEXT_KEYS
        if key not in GENERIC_FRESHNESS_CONTEXT_KEYS
    )


def _row_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    if not _has_context(fields):
        return None
    row = {
        "stock_code": str(
            event.get("stock_code") or fields.get("stock_code") or ""
        ).lstrip("A"),
        "stock_name": event.get("stock_name"),
        "event_time": event.get("emitted_at")
        or fields.get("event_time")
        or fields.get("event_ts"),
        "event_ts": fields.get("event_ts") or event.get("emitted_at"),
        "record_id": event.get("record_id") or fields.get("record_id"),
        "sim_record_id": fields.get("sim_record_id"),
        "sim_parent_record_id": fields.get("sim_parent_record_id"),
        "holding_context_broker_route_authority": fields.get(
            "holding_context_broker_route_authority"
        ),
        "source_event_stage": fields.get("source_event_stage") or event.get("stage"),
        "stage": event.get("stage"),
        "ai_prompt_type": fields.get("ai_prompt_type"),
        "ai_trace_endpoint_name": fields.get("ai_trace_endpoint_name"),
        "effective_venue": fields.get("effective_venue")
        or fields.get("ai_trace_effective_venue"),
        "venue": fields.get("venue"),
        "actual_order_submitted": _safe_bool(
            fields.get("actual_order_submitted"), False
        ),
        "order_submission_declaration_valid": (
            "actual_order_submitted" not in fields
            or _safe_bool(fields.get("actual_order_submitted"), None) is not None
        ),
        "broker_order_forbidden": (
            _safe_bool(fields.get("broker_order_forbidden"), False)
            if "broker_order_forbidden" in fields
            else None
        ),
    }
    row.update({key: fields.get(key) for key in CONTEXT_KEYS})
    v_pw_expected = any(
        key in fields
        for key in ("v_pw_now", "v_pw_source", "latest_strength", "current_vpw")
    )
    row["v_pw_expected"] = v_pw_expected
    current_v_pw_source = str(row.get("v_pw_source") or "").strip().lower()
    if current_v_pw_source in {"", "missing", "unknown", "not_available"}:
        legacy_v_pw = _safe_float(
            (
                fields.get("latest_strength")
                if fields.get("latest_strength") not in (None, "", "-")
                else fields.get("current_vpw")
            ),
            0.0,
        )
        if legacy_v_pw > 0:
            row["v_pw_now"] = legacy_v_pw
            row["v_pw_ws_value"] = legacy_v_pw
            row["v_pw_source"] = "ws_0b_latest_strength"
            row["v_pw_report_provenance_backfilled"] = True
        elif not v_pw_expected:
            row["v_pw_source"] = "not_applicable"

    comparison_contract = str(
        row.get("trade_volume_1030_1031_vs_15_comparison_contract") or ""
    ).strip()
    comparison_evaluable_count = _safe_int(
        row.get("trade_volume_1030_1031_vs_15_evaluable_count"),
        0,
    )
    if not comparison_contract and comparison_evaluable_count > 0:
        volume_sources = _dict_counter(row.get("trade_volume_source_counts"))
        if volume_sources.get("1030_1031_sum", 0) > 0:
            comparison_contract = "cumulative_split_vs_tick_not_comparable"
        else:
            comparison_contract = "comparison_scope_unknown"
        row["trade_volume_1030_1031_vs_15_comparison_contract"] = comparison_contract
        row["trade_volume_1030_1031_vs_15_contract_inferred_for_report"] = True
    if comparison_contract:
        row["trade_volume_1030_1031_vs_15_decision_usable"] = (
            comparison_contract == "same_tick_comparable"
        )
    observation = fields.get("ka10003_buy_dominance_observation")
    if isinstance(observation, dict):
        row["ka10003_buy_dominance_observation_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_source_counts")
            or observation.get("source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_trade_value_source_counts"] = (
            row.get("ka10003_buy_dominance_observation_trade_value_source_counts")
            or observation.get("trade_value_source_counts")
            or {}
        )
        row["ka10003_buy_dominance_observation_inside_spread_count"] = (
            row.get("ka10003_buy_dominance_observation_inside_spread_count")
            if row.get("ka10003_buy_dominance_observation_inside_spread_count")
            not in (None, "")
            else observation.get("inside_spread_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_evaluable_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_evaluable_count")
            not in (None, "")
            else observation.get("split_vs_15_evaluable_count")
        )
        row["ka10003_buy_dominance_observation_split_vs_15_mismatch_count"] = (
            row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count")
            if row.get("ka10003_buy_dominance_observation_split_vs_15_mismatch_count")
            not in (None, "")
            else observation.get("split_vs_15_mismatch_count")
        )
    for suffix in (
        "context_computed",
        "context_sent",
        "context_consumed",
        "context_reused",
        "context_payload_included",
    ):
        key = "microstructure_reaction_" + suffix
        if key in row:
            row[key] = _safe_bool(row[key], None)
    for suffix in ("context_id", "evaluation_id", "parent_context_id", "venue"):
        key = "microstructure_reaction_" + suffix
        if str(row.get(key) or "").lower() in {"", "none", "null", "-", "unknown"}:
            row[key] = None
    return row






















_DIAGNOSTIC_ROW_KEYS = (
    (
        "stock_code",
        "stock_name",
        "event_time",
        "record_id",
        "sim_record_id",
        "sim_parent_record_id",
        "source_event_stage",
        "stage",
        "actual_order_submitted",
        "broker_order_forbidden",
        "microstructure_reaction_context_status",
        "microstructure_reaction_quote_stale_threshold_ms",
        "microstructure_reaction_delivery_telemetry_version",
        "microstructure_reaction_context_computed",
        "microstructure_reaction_context_sent",
        "microstructure_reaction_context_consumed",
        "microstructure_reaction_context_consumer",
        "microstructure_reaction_context_delivery_state",
        "microstructure_reaction_entry_reaction_quality",
        "microstructure_reaction_source_quality",
        "microstructure_reaction_ask_sweep_score",
        "microstructure_reaction_post_sweep_hold_score",
        "microstructure_reaction_bid_replenishment_score",
        "microstructure_reaction_wall_replenishment_risk_score",
        "microstructure_reaction_vi_proximity_risk",
        "microstructure_reaction_tick_aggressor_pressure_usable",
        "microstructure_reaction_tick_aggressor_trusted_count",
        "market_data_freshness_state",
        "quote_age_ms",
        "ws_age_ms",
        "v_pw_source",
        "v_pw_runtime_support_usable",
    )
    + DELIVERY_KEYS
    + (
        "microstructure_reaction_context_version",
        "microstructure_reaction_context_hash",
    )
)


























































def render_microstructure_reaction_context_markdown(report: dict[str, Any]) -> str:
    modern = (report.get("summary") or {}).get("machine_primary_auxiliary_evaluation") or {}
    lines = [
        f"# Microstructure Machine Evaluation - {report.get('date')}",
        "",
        "- legacy raw postclose study: retired",
        "- decision_authority: diagnostic_only; runtime/apply: False",
        f"- status: `{modern.get('status')}`",
        f"- cases / full-cost outcomes: `{modern.get('case_count')}` / `{modern.get('cost_adjusted_outcome_count')}`",
        f"- source: `{modern.get('source_report_path')}`",
        f"- source SHA256: `{modern.get('source_report_sha256')}`",
        f"- actual completed EV: `{modern.get('actual_completed_ev_pct')}`",
        "- Price-window CF is descriptive; it is not realized profit or causal feature Delta EV.",
        "",
        "## Partitions",
        "```json",
        json.dumps(modern.get("partitions") or [], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit("Legacy raw microstructure study is retired; use the existing machine calibration producer.")
