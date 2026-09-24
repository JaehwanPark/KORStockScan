"""Summarize family-owned postclose evidence and direct runtime handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.automation.runtime_policy_bootstrap import (
    direct_policy_digest,
    validate_rising_missed_policy_receipt,
)
from src.utils.constants import DATA_DIR

REPORT_DIR = DATA_DIR / "report" / "runtime_approval_summary"
MAX_DIRECT_JSON_BYTES = 64 * 1024 * 1024

DIRECT_EVIDENCE_COMPLETE = "direct_evidence_complete"
DIRECT_EVIDENCE_INCOMPLETE = "direct_evidence_incomplete"

PRIMARY_DIRECT_OWNERS = (
    "source_quality",
    "entry_cancel_wait",
    "entry_split",
    "pre_submit_delay",
    "scale_in_split",
    "machine_entry",
    "low_price_two_leg",
    "low_price_expansion",
    "ws_freshness",
    "main_mechanistic_entry",
    "compact_auxiliary",
    "rising_missed",
)
REQUIRED_DIRECT_OWNERS = frozenset(PRIMARY_DIRECT_OWNERS)

PRODUCER_FLAG_BY_OWNER = {
    "source_quality": "observation_source_quality_audit",
    "entry_split": "entry_split_order_plan",
    "pre_submit_delay": "pre_submit_delay_tuning",
    "scale_in_split": "scale_in_split_order_plan",
    "machine_entry": "samsung_machine_entry_tuning",
    "low_price_two_leg": "low_price_two_leg_tuning",
    "low_price_expansion": "low_price_two_leg_candidate_recommendation",
    "ws_freshness": "intraday_ws_freshness_finalize",
    "main_mechanistic_entry": "ai_decision_action_outcome_calibration",
    "compact_auxiliary": "ai_decision_action_outcome_calibration",
    "rising_missed": "rising_missed_classifier_prior",
}

POLICY_OWNER_BY_SOURCE = {
    "entry_cancel_wait": "entry_cancel_wait_policy",
    "entry_split": "entry_split_policy",
    "pre_submit_delay": "pre_submit_delay_policy",
    "scale_in_split": "scale_in_split_policy",
    "machine_entry": "machine_entry_candidate",
    "low_price_two_leg": "low_price_candidate",
    "low_price_expansion": "low_price_expansion_policy",
    "rising_missed": "rising_missed_policy",
    "compact_auxiliary": "compact_policy",
    "main_mechanistic_entry": "main_mechanistic_policy",
}

DEFAULT_CLOSURE_OWNER = {
    "source_quality": "observation_source_quality_audit",
    "entry_cancel_wait": "entry_cancel_wait_tuning",
    "entry_split": "entry_split_order_plan",
    "pre_submit_delay": "pre_submit_delay_tuning",
    "scale_in_split": "scale_in_split_order_plan",
    "machine_entry": "samsung_machine_entry_tuning",
    "low_price_two_leg": "low_price_two_leg_tuning",
    "low_price_expansion": "low_price_two_leg_expanded_candidate_research",
    "ws_freshness": "intraday_ws_freshness_monitor",
    "main_mechanistic_entry": "ai_decision_action_outcome_calibration",
    "compact_auxiliary": "compact_auxiliary_paired_replay",
    "rising_missed": "rising_missed_classifier_prior",
}


def summary_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"runtime_approval_summary_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _paths(target_date: str) -> dict[str, Path]:
    requested_effective = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE")
    if requested_effective:
        date.fromisoformat(requested_effective)
    report = DATA_DIR / "report"
    threshold = DATA_DIR / "threshold_cycle"
    compact_policies = []
    machine_policies = []
    for candidate in sorted(
        (DATA_DIR / "runtime/mechanistic_entry_policy").glob("policy_????-??-??.json")
    ):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if requested_effective and payload.get("target_date") != requested_effective:
            continue
        if payload.get("compact_evaluation_source_date") == target_date:
            compact_policies.append(candidate)
        if (payload.get("machine_evaluation_source") or {}).get("source_date") == target_date:
            machine_policies.append(candidate)
    compact_policy = (
        compact_policies[-1]
        if compact_policies
        else DATA_DIR / "runtime/mechanistic_entry_policy" / "policy_missing.json"
    )
    machine_policy = (
        machine_policies[-1]
        if machine_policies
        else DATA_DIR / "runtime/mechanistic_entry_policy" / "policy_missing.json"
    )
    expansion_policies = []
    for candidate in sorted((DATA_DIR / "runtime/low_price_two_leg_auto_expansion").glob("low_price_two_leg_auto_expansion_????-??-??.json")):
        payload = _load_json(candidate)
        if payload.get("source_date") == target_date and (not requested_effective or payload.get("effective_date") == requested_effective):
            expansion_policies.append(candidate)
    return {
        "source_quality": report / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json",
        "entry_cancel_wait": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_tuning_{target_date}.json",
        "entry_cancel_wait_policy": report / "entry_cancel_wait_tuning" / f"entry_cancel_wait_policy_{target_date}.json",
        "entry_split": report / "entry_split_order_plan" / f"entry_split_order_plan_{target_date}.json",
        "entry_split_policy": threshold / "entry_split_order_policy" / f"entry_split_order_policy_{target_date}.json",
        "pre_submit_delay": report / "pre_submit_delay_tuning" / f"pre_submit_delay_tuning_{target_date}.json",
        "pre_submit_delay_policy": threshold / "pre_submit_delay_policy" / f"pre_submit_delay_policy_{target_date}.json",
        "scale_in_split": report / "scale_in_split_order_plan" / f"scale_in_split_order_plan_{target_date}.json",
        "scale_in_split_policy": threshold / "scale_in_split_order_policy" / f"scale_in_split_order_policy_{target_date}.json",
        "machine_entry": report / "samsung_machine_entry_tuning" / f"samsung_machine_entry_tuning_{target_date}.json",
        "machine_entry_candidate": threshold / "samsung_machine_entry_policy" / "candidates" / f"samsung_machine_entry_policy_candidate_{target_date}.json",
        "low_price_two_leg": report / "low_price_two_leg_tuning" / f"low_price_two_leg_tuning_{target_date}.json",
        "low_price_candidate": threshold / "low_price_two_leg" / "candidates" / f"low_price_two_leg_policy_candidate_{target_date}.json",
        "low_price_expansion": report / "low_price_two_leg_expanded_candidate_research" / f"low_price_two_leg_expanded_candidate_research_{target_date}.json",
        "low_price_expansion_policy": expansion_policies[-1] if expansion_policies else DATA_DIR / "runtime/low_price_two_leg_auto_expansion" / "policy_missing.json",
        "ws_freshness": report / "intraday_ws_freshness_monitor" / f"intraday_ws_freshness_monitor_{target_date}.json",
        "main_mechanistic_entry": report / "ai_decision_action_outcome_calibration" / f"ai_decision_action_outcome_calibration_{target_date}.json",
        "main_mechanistic_policy": machine_policy,
        "compact_auxiliary": report / "ai_entry_setup_paired_replay_batch" / f"compact_auxiliary_paired_economic_{target_date}.json",
        "compact_policy": compact_policy,
        "rising_missed": report / "rising_missed_classifier_prior" / f"rising_missed_classifier_prior_{target_date}.json",
        "rising_missed_policy": report / "rising_missed_classifier_prior" / f"rising_missed_tp1_policy_source_{target_date}.json",
        "runtime_bootstrap": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_{target_date}.json",
        "runtime_bootstrap_verify": DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_verify_{target_date}.json",
    }


def _postclose_status_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target_date}.status.json"


def _read(path: Path) -> tuple[dict[str, Any], str | None, str, int | None]:
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        return {}, "missing", "absent", None
    except OSError as exc:
        return {}, f"unreadable:{type(exc).__name__}", "stat_failed", None
    if size > MAX_DIRECT_JSON_BYTES:
        return {}, None, "stream_hash_only_large_json", size
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {}, f"unreadable:{type(exc).__name__}", "bounded_json", size
    if not isinstance(value, dict):
        return {}, "object_required", "bounded_json", size
    return value, None, "bounded_json", size


def _load_json(path: Path) -> dict[str, Any]:
    value, error, _, _ = _read(path)
    return value if error is None else {}


def _read_top_level_sections(path: Path, wanted: set[str]) -> dict[str, Any]:
    """Read selected pretty-printed top-level members without materializing JSON."""
    sections: dict[str, Any] = {}
    current: str | None = None
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.startswith('  "'):
                    if current in wanted:
                        sections[current] = json.loads(
                            "".join(sections[current]).rstrip().rstrip(",")
                        )
                    current = line.split('"', 2)[1]
                    if current in wanted:
                        sections[current] = [line.split(":", 1)[1]]
                elif current in wanted:
                    if line.strip() == "}" and line.startswith("}"):
                        sections[current] = json.loads(
                            "".join(sections[current]).rstrip().rstrip(",")
                        )
                        current = None
                    else:
                        sections[current].append(line)
    except (OSError, ValueError, TypeError):
        return {}
    return sections if wanted <= sections.keys() else {}


def _sha(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _date_matches(payload: dict[str, Any], target_date: str) -> bool:
    values = [payload.get(key) for key in ("target_date", "date", "source_date", "end_date") if payload.get(key)]
    return bool(values) and target_date in {str(value) for value in values}


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _flag_enabled(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _owner_requirements(target_date: str) -> tuple[dict[str, bool], dict[str, Any]]:
    status_path = _postclose_status_path(target_date)
    status = _load_json(status_path)
    flags = status.get("producer_flags") if isinstance(status.get("producer_flags"), dict) else {}
    required: dict[str, bool] = {}
    missing_flags: list[str] = []
    for owner in PRIMARY_DIRECT_OWNERS:
        flag = PRODUCER_FLAG_BY_OWNER.get(owner)
        if owner == "pre_submit_delay" and target_date < "2026-09-23":
            required[owner] = False
            continue
        if flag is not None and flag not in flags:
            missing_flags.append(flag)
        required[owner] = True if flag is None else _flag_enabled(flags.get(flag), True)
    return required, {
        "path": str(status_path),
        "exists": status_path.exists(),
        "sha256": _sha(status_path),
        "producer_flags": flags,
        "fallback_used": bool(missing_flags),
        "missing_producer_flags": sorted(missing_flags),
        "fallback_contract": "current_wrapper_default_active_direct_owners",
    }


def _expansion_economic_projection(path: Path) -> dict[str, Any]:
    from src.engine.monitoring.low_price_two_leg_expanded_candidate_research import read_report
    report = read_report(path)
    payload = {key: report.get(key) for key in (
        "schema", "report_type", "target_date", "status", "decision", "runtime_effect",
        "allowed_runtime_apply", "actual_order_submitted", "source_symbol_count",
        "eligible_source_symbol_count", "quarantined_source_symbol_count")}
    gate = report.get("joint_allocation_gate") or {}
    payload["economic_evaluation"] = {
        "status": "source_gap" if report.get("status") == "partial_source_quality" or gate.get("status") == "allocation_blocked" else "insufficient_sample",
        "blocker": gate.get("reason") or ("retained_source_quarantine" if report.get("source_quarantine") else "independent_economic_selection_pending"),
        "candidate_count": report.get("recommendation_count", 0),
        "allowed_runtime_apply": False,
        "closure_test": "retained_source_isolation_frozen_allocator_independent_holdout_and_dated_consumer",
    }
    return payload


def _large_companion(
    owner: str,
    path: Path,
    target_date: str,
    artifact_sha256: str | None,
    paths: dict[str, Path],
) -> tuple[dict[str, Any], dict[str, Any], str | None]:
    if owner == "low_price_two_leg":
        companion_path = paths["low_price_candidate"]
        payload, error, read_mode, _ = _read(companion_path)
        projection = _read_top_level_sections(
            path,
            {"schema", "target_date", "artifact_hash", "paired_economic_search"},
        )
        embedded_sha = projection.get("artifact_hash")
        source_path = Path(str(payload.get("source_report_path") or ""))
        source_name_matches = source_path.name == path.name
        semantic_sha_matches = bool(
            embedded_sha and payload.get("source_report_artifact_hash") == embedded_sha
        )
        projection_matches = bool(
            projection.get("target_date") == target_date
            and payload.get("source_report_schema") == projection.get("schema")
            and payload.get("paired_economic_search") == projection.get("paired_economic_search")
        )
        verified = (
            error is None and _date_matches(payload, target_date) and source_name_matches
            and semantic_sha_matches and projection_matches
        )
        return payload, {
            "path": str(companion_path),
            "sha256": _sha(companion_path),
            "read_mode": read_mode,
            "contract": "low_price_candidate_source_semantic_hash",
            "source_name_matches": source_name_matches,
            "source_semantic_sha256": embedded_sha,
            "semantic_sha_matches": semantic_sha_matches,
            "economic_projection_matches": projection_matches,
            "verified": verified,
        }, None if verified else "semantic_unverified_large_source"
    if owner == "low_price_expansion":
        companion_path = path.with_name(path.name + ".reuse-contract.json")
        payload, error, read_mode, _ = _read(companion_path)
        source_path = Path(str(payload.get("artifact_path") or ""))
        source_name_matches = source_path.name == path.name
        byte_sha_matches = bool(artifact_sha256 and payload.get("artifact_sha256") == artifact_sha256)
        verified = error is None and _date_matches(payload, target_date) and source_name_matches and byte_sha_matches
        if not verified:
            # The late machine publisher can legitimately replace the study
            # after main's reuse receipt. Accept only its current native proof.
            from src.engine.automation.machine_research_closed_loop_refresh import validate_current_receipt
            native_path = path.parent.parent / "machine_research_closed_loop" / f"machine_research_closed_loop_{target_date}.json"
            native, native_error, native_mode, _ = _read(native_path)
            if (native_error is None and (native.get("dependency_sources") or {}).get(str(path.resolve()))
                and validate_current_receipt(native, target_date)):
                return _expansion_economic_projection(path), {
                    "path": str(native_path), "sha256": _sha(native_path),
                    "read_mode": native_mode, "contract": "machine_research_closed_loop_current_dependency",
                    "source_artifact_sha256": artifact_sha256, "verified": True,
                }, None
        return (_expansion_economic_projection(path) if verified else payload), {
            "path": str(companion_path),
            "sha256": _sha(companion_path),
            "read_mode": read_mode,
            "contract": "postclose_artifact_reuse_contract_v1",
            "source_name_matches": source_name_matches,
            "artifact_sha_matches": byte_sha_matches,
            "verified": verified,
        }, None if verified else "semantic_unverified_large_source"
    if owner == "ws_freshness":
        companion_path = path.with_name(path.name + ".reuse-contract.json")
        payload, error, read_mode, _ = _read(companion_path)
        source_path = Path(str(payload.get("artifact_path") or ""))
        source_name_matches = source_path.name == path.name
        byte_sha_matches = bool(
            artifact_sha256 and payload.get("artifact_sha256") == artifact_sha256
        )
        # The freshness report is source-only evidence. Its postclose handoff
        # must be final and must never authorize runtime or order changes.
        report_projection = _read_top_level_sections(
            path,
            {
                "report_type",
                "target_date",
                "evaluation_phase",
                "postclose_quality_handoff",
                "metric_contract",
            },
        )
        handoff = report_projection.get("postclose_quality_handoff") or {}
        metric_contract = report_projection.get("metric_contract") or {}
        semantic_contract_matches = (
            report_projection.get("report_type") == "intraday_ws_freshness_monitor"
            and report_projection.get("target_date") == target_date
            and report_projection.get("evaluation_phase") == "postclose_final"
            and handoff.get("parent_quality_final_claimed") is True
            and handoff.get("source_only") is True
            and metric_contract.get("runtime_effect") is False
            and metric_contract.get("allowed_runtime_apply") is False
            and metric_contract.get("broker_order_forbidden") is True
        )
        verified = (
            error is None
            and _date_matches(payload, target_date)
            and source_name_matches
            and byte_sha_matches
            and semantic_contract_matches
        )
        return payload, {
            "path": str(companion_path),
            "sha256": _sha(companion_path),
            "read_mode": read_mode,
            "contract": "ws_freshness_source_reuse_contract_v1",
            "source_name_matches": source_name_matches,
            "artifact_sha_matches": byte_sha_matches,
            "semantic_contract_matches": semantic_contract_matches,
            "verified": verified,
        }, None if verified else "semantic_unverified_large_source"
    return {}, {"path": None, "sha256": None, "contract": None, "verified": False}, "semantic_unverified_large_source"


def _dict_value(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _economic_section(owner: str, payload: dict[str, Any]) -> dict[str, Any]:
    if owner == "entry_cancel_wait":
        return _dict_value(payload, "economic_evaluation")
    if owner == "entry_split":
        return _dict_value(payload, "economic_acceptance")
    if owner == "scale_in_split":
        return _dict_value(payload, "evaluation_state")
    if owner == "low_price_two_leg":
        return _dict_value(payload, "paired_economic_search")
    if owner == "ws_freshness":
        return _dict_value(payload, "postclose_quality_handoff")
    if owner == "main_mechanistic_entry":
        from src.engine.scalping.entry_strategy_policy import select_report_candidate, promotion_errors
        selected = select_report_candidate(payload)
        if selected and selected[1].get('promotion_pass') is True:
            scope, result = selected
            proposal = result['candidate']
            if not promotion_errors(proposal, proposal.get('parent_policy') or {}, tuple(scope.split('|'))):
                arm = proposal['evidence']['holdout']
                measured = arm['economics']
                if measured.get('status') == 'supported_machine_admission':
                    # Machine selection is independent of auxiliary/portfolio replay.
                    # Preserve its diagnostics without asserting realized/portfolio EV.
                    return dict(status='unsupported_portfolio_scope', candidate_count=1,
                        paired_sample_count=None, allowed_runtime_apply=False,
                        metric_role='sim_probe_ev', selected_scope=scope,
                        diagnostic_machine_selection=dict(
                            status=result.get('status'),
                            selection_basis=result.get('selection_basis'),
                            auxiliary_ai_required=False,
                            evaluated_candidate_count=result.get('evaluated_candidate_count'),
                            train=(proposal['evidence'].get('train') or {}).get('economics'),
                            holdout=measured),
                        blocker='machine_policy_selected_portfolio_economics_separate',
                        future_generation_contract_verified=False,
                        closure_test='natural_machine_policy_outcomes')
                old, new = measured['incumbent'], measured['candidate']
                return dict(status='validated_edge', candidate_count=1,
                    paired_sample_count=len(arm['opportunity_ids']),
                    incumbent_ev_pct=old.get('ev_pct'), candidate_ev_pct=new.get('ev_pct'),
                    robust_delta_ev_lower_bound_pct=measured['robust_paired_delta_ev_lower_bound_pct'],
                    net_profit_uplift_krw_per_observation_day=measured['daily_net_profit_delta_krw'],
                    allowed_runtime_apply=True, metric_role='sim_probe_ev', blocker=None,
                    source_date_count=len(arm['source_dates']), selected_scope=scope,
                    future_generation_contract_verified=False,
                    closure_test='current_generation_receipt_then_natural_completed_cost_outcomes')
        projection = _dict_value(payload, "machine_full_evaluation")
        # Report execution flags do not prove prospective owner-model support.
        future_contract_verified = False
        operating_complete = projection.get("downstream_operating_evidence_complete") is True
        economics = _dict_value(projection, "operating_economics")
        incumbent = _dict_value(economics, "incumbent").get("ev_pct")
        candidate = _dict_value(economics, "candidate").get("ev_pct")
        return {
            "status": ("source_gap" if projection.get("daily_net_profit_status") == "not_available_without_exact_changed_decision_owner_replay" else projection.get("state")),
            "candidate_count": projection.get("independent_candidate_count"),
            "paired_sample_count": projection.get("paired_comparable_count") if operating_complete else None,
            "diagnostic_terminal_proxy": {
                "population_count": projection.get("full_population_count"),
                "comparable_count": projection.get("paired_comparable_count"),
                "accepted_lane_counts": projection.get("accepted_lane_counts"),
                "incumbent_ev_pct": projection.get("holdout_incumbent_ev_pct"),
                "candidate_ev_pct": projection.get("holdout_cost_adjusted_ev_pct"),
                "delta_ev_pct": projection.get("holdout_paired_delta_ev_pct"),
                "economic_basis": projection.get("economic_basis"),
            },
            "incumbent_ev_pct": incumbent if operating_complete else None,
            "candidate_ev_pct": candidate if operating_complete else None,
            "delta_ev_pct": candidate - incumbent if operating_complete and candidate is not None and incumbent is not None else None,
            "robust_delta_ev_lower_bound_pct": economics.get("robust_paired_delta_ev_lower_bound_pct"),
            "net_profit_uplift_krw_per_observation_day": projection.get(
                "daily_net_profit_delta_krw"
            ),
            "allowed_runtime_apply": projection.get("promotion_pass") is True,
            "blocker": (
                None
                if projection.get("state") in {"validated_edge", "evaluated_no_edge"}
                else (projection.get("structural_blocker") or projection.get("daily_net_profit_status"))
            ),
            "metric_role": projection.get("metric_role", "sim_probe_ev"),
            "future_generation_contract_verified": future_contract_verified,
            "closure_test": (
                "future_exact_changed_decision_owner_replay_and_completed_profit_rate"
            ),
        }
    if owner == "compact_auxiliary":
        metrics = _dict_value(payload, "metrics")
        operating = _dict_value(metrics, "operating_economic_comparison")
        incumbent = _dict_value(operating, "incumbent")
        candidate = _dict_value(operating, "candidate")
        zero = _dict_value(payload, "candidate_zero_disposition")
        prospective = _dict_value(payload, "prospective_source_contract")
        blockers = zero.get("blockers") if isinstance(zero.get("blockers"), list) else []
        return {
            "status": (
                "validated_edge"
                if payload.get("promotion_pass") is True
                else zero.get("status") or payload.get("evaluation_state") or payload.get("status")
            ),
            "blocker": (
                (blockers[0] or {}).get("blocker")
                if blockers and isinstance(blockers[0], dict)
                else operating.get("blocker")
            ),
            "incumbent_ev_pct": incumbent.get("ev_pct"),
            "candidate_ev_pct": candidate.get("ev_pct"),
            "delta_ev_pct": metrics.get("delta_net_ev_pct"),
            "robust_paired_delta_ev_lower_bound_pct": operating.get(
                "robust_paired_delta_ev_lower_bound_pct"
            ),
            "net_profit_uplift_krw_per_observation_day": operating.get(
                "portfolio_daily_net_delta_krw"
            ),
            "paired_tail_delta_pct": (
                candidate.get("es10") - incumbent.get("es10")
                if isinstance(candidate.get("es10"), (int, float))
                and isinstance(incumbent.get("es10"), (int, float))
                else None
            ),
            "capital_exposure_delta": operating.get("portfolio_capital_delta_krw_minutes"),
            "fill_participation_delta_pct": (
                candidate.get("fill_participation")
                - incumbent.get("fill_participation")
                if isinstance(candidate.get("fill_participation"), (int, float))
                and isinstance(incumbent.get("fill_participation"), (int, float))
                else None
            ),
            "model_holdout_status": payload.get("owner_execution_model_status"),
            "candidate_holdout_status": (
                "consumed"
                if _dict_value(payload, "chronological_validation").get("holdout_consumed")
                else "preserved"
            ),
            "paired_sample_count": metrics.get("paired_comparable_count"),
            "source_date_count": len(
                {
                    row.get("source_date")
                    for row in _dict_value(payload, "chronological_validation").get(
                        "learning_pairs", []
                    )
                    if isinstance(row, dict) and row.get("source_date")
                }
            ),
            "candidate_count": (
                1
                if _dict_value(payload, "candidate_selection").get("status")
                == "candidate_selected"
                else 0
            ),
            "allowed_runtime_apply": payload.get("promotion_pass") is True,
            "metric_role": "primary_ev",
            "future_generation_contract_verified": (
                prospective.get("implementation_verified") is True
            ),
            "historical_evidence_state": payload.get(
                "historical_evidence_state"
            ),
            "closure_test": payload.get("closure_test"),
        }
    return _dict_value(payload, "economic_evaluation")


def _status_texts(owner: str, payload: dict[str, Any]) -> list[str]:
    economic = _economic_section(owner, payload)
    values = [
        economic.get("comparison_status"), economic.get("status"), economic.get("decision"), economic.get("disposition"),
        payload.get("comparison_status"), payload.get("selection_status"), payload.get("decision"), payload.get("status"), payload.get("conclusion"),
        payload.get("evaluation_state"),
    ]
    if owner == "low_price_two_leg":
        for row in (_dict_value(payload, "paired_economic_search").get("profiles") or {}).values():
            if isinstance(row, dict):
                values.extend([row.get("disposition"), row.get("promotion_disposition")])
    return [str(value).strip().lower() for value in values if value not in (None, "")]


def _comparison_status(owner: str, payload: dict[str, Any]) -> str:
    if owner == "source_quality":
        return "not_applicable"
    texts = _status_texts(owner, payload)
    joined = " ".join(texts)
    if any("validated_edge" in value for value in texts):
        return "validated_edge"
    if owner == "low_price_two_leg":
        profiles = _dict_value(payload, "paired_economic_search").get("profiles") or {}
        profile_states = {
            str(row.get("disposition") or row.get("promotion_disposition") or "").lower()
            for row in profiles.values() if isinstance(row, dict)
        }
        profile_states.discard("")
        if len(profile_states) > 1:
            return "mixed"
    if "source_gap" in joined or "contract_block" in joined or "missing_source" in joined:
        return "source_gap"
    if "unsupported" in joined:
        return "unsupported_scope"
    if "evaluated_no_edge" in joined or "no_edge" in joined or "negative_edge" in joined or "hold_no_edge" in joined:
        return "measured_no_edge"
    if "skipped_no_applicable_fill" in joined or "insufficient_sample" in joined or "insufficient_mature_sample" in joined:
        return "insufficient_sample"
    if any(token in joined for token in ("pending_maturity", "hold_actual_sample", "paired_search_incomplete")):
        return "pending_maturity"
    if any(token in joined for token in ("identical_policy", "incumbent_preserved")):
        return "identical_policy"
    return "not_applicable"


def _first_blocker(owner: str, payload: dict[str, Any]) -> str | None:
    economic = _economic_section(owner, payload)
    values = [economic.get("blocker"), economic.get("reason"), economic.get("blocked_reason"), payload.get("blocked_reason")]
    for key in ("blockers", "blocking_reasons", "promotion_blocking_reasons"):
        rows = economic.get(key)
        if isinstance(rows, list) and rows:
            values.append(rows[0])
    if owner == "low_price_two_leg":
        for row in (_dict_value(payload, "paired_economic_search").get("profiles") or {}).values():
            if not isinstance(row, dict):
                continue
            blockers = row.get("promotion_blocking_reasons")
            if isinstance(blockers, list) and blockers:
                values.append(blockers[0])
                break
            if row.get("disposition") == "source_gap":
                values.append("profile_source_gap")
                break
    value = _first_nonempty(*values)
    return str(value) if value is not None else None


def _economic_projection(owner: str, payload: dict[str, Any]) -> dict[str, Any]:
    economic = _economic_section(owner, payload)
    status = _comparison_status(owner, payload)
    recommended = _dict_value(payload, "recommended_policy")
    policy_allowed_values = (
        (
            recommended.get("runtime_apply_allowed"),
            recommended.get("ev_validated_runtime_apply_allowed"),
            economic.get("allowed_runtime_apply"),
            payload.get("allowed_runtime_apply"),
        )
        if owner == "rising_missed"
        else (
            recommended.get("runtime_apply_allowed"),
            recommended.get("ev_validated_runtime_apply_allowed"),
            payload.get("allowed_runtime_apply"),
            economic.get("allowed_runtime_apply"),
        )
    )
    policy_allowed = _first_nonempty(*policy_allowed_values)
    candidate_count = _first_nonempty(
        recommended.get("candidate_count"), recommended.get("runtime_candidate_count"),
        economic.get("candidate_count"),
        len(economic.get("candidates") or []) if isinstance(economic.get("candidates"), list) else None,
    )
    paired_sample_count = _first_nonempty(
        economic.get("paired_sample_count"), economic.get("paired_economic_sample_count"),
        economic.get("paired_comparison_count"), economic.get("comparison_sample_count"),
        economic.get("completed_candidate_count"), economic.get("applicable_receipt_count"),
        economic.get("eligible_sample_count"), economic.get("sample_count"),
    )
    source_day_count = _first_nonempty(
        economic.get("source_date_count"), economic.get("economic_source_date_count"),
        len(economic.get("source_counts") or {}) if isinstance(economic.get("source_counts"), dict) else None,
    )
    first_blocker = _first_blocker(owner, payload)
    historical_evidence_state = economic.get("historical_evidence_state")
    historical_changed_decision_replay_unrecoverable = bool(
        owner == "compact_auxiliary"
        and historical_evidence_state == "exact_source_unrecoverable_preserved_excluded"
    )
    if status == "measured_no_edge" and not paired_sample_count:
        status = "source_gap"
        first_blocker = first_blocker or "paired_comparison_denominator_missing"
    future_contract_verified = _first_nonempty(
        economic.get("future_generation_contract_verified"),
        economic.get("future_source_contract_verified"),
        economic.get("producer_consumer_contract_verified"),
    ) is True
    if status == "pending_maturity" and not future_contract_verified:
        status = "source_gap"
        first_blocker = first_blocker or "future_generation_contract_unverified"
    if status == "validated_edge" and (policy_allowed is not True or not candidate_count):
        status = "source_gap"
        first_blocker = first_blocker or "validated_candidate_contract_incomplete"
    prospective_resolution_mode = None
    historical_evidence_state = historical_evidence_state or None
    if historical_changed_decision_replay_unrecoverable:
        # The already-observed changed decisions cannot acquire an exact order,
        # fill, quantity, or capital-occupation receipt later.  Keep that
        # historical fact distinct from the verified prospective writer/reader
        # path, which can close only with new natural observations.
        resolution_mode = "historical_unrecoverable"
        historical_evidence_state = historical_evidence_state or (
            "exact_owner_replay_unrecoverable"
        )
        prospective_resolution_mode = (
            "natural_maturity" if future_contract_verified else "producer_repair"
        )
    elif status == "validated_edge":
        resolution_mode = "validated_economic_action"
    elif status == "measured_no_edge":
        resolution_mode = "measured_no_edge"
    elif status in {"pending_maturity", "insufficient_sample"}:
        resolution_mode = "natural_maturity" if future_contract_verified else "producer_contract_review"
    elif status in {"source_gap", "unsupported_scope", "mixed"}:
        resolution_mode = (
            "historical_unrecoverable"
            if any("irrecoverable" in value for value in _status_texts(owner, payload))
            else "producer_repair"
        )
    else:
        resolution_mode = "retired_or_not_applicable"
    if (
        historical_changed_decision_replay_unrecoverable
        and prospective_resolution_mode == "natural_maturity"
    ):
        handoff = "incumbent_preserved"
    elif status == "validated_edge":
        handoff = "candidate_published"
    elif status in {"measured_no_edge", "identical_policy", "pending_maturity", "insufficient_sample"}:
        handoff = "incumbent_preserved"
    elif status in {"source_gap", "unsupported_scope", "mixed"}:
        handoff = "blocked"
    else:
        handoff = "not_applicable"
    return {
        "comparison_status": status,
        "diagnostic_terminal_proxy": economic.get("diagnostic_terminal_proxy"),
        "diagnostic_machine_selection": economic.get("diagnostic_machine_selection"),
        "future_contract_state": "verified_supported_scope" if future_contract_verified else "unverified_requires_owner_evidence",
        "implementation_incomplete_inferred_from_historical_gap": False,
        "raw_statuses": _status_texts(owner, payload),
        "metric_role": _first_nonempty(economic.get("metric_role"), payload.get("metric_role")),
        "incumbent_cost_adjusted_ev_pct": _first_nonempty(economic.get("incumbent_ev_pct"), economic.get("primary_operating_ev_pct")),
        "candidate_cost_adjusted_ev_pct": economic.get("candidate_ev_pct"),
        "paired_delta_ev_pct": _first_nonempty(economic.get("delta_ev_pct"), economic.get("ev_uplift_pct_point")),
        "conservative_delta_ev_lower_bound_pct": _first_nonempty(economic.get("delta_ev_lower_bound_pct"), economic.get("robust_paired_delta_ev_lower_bound_pct")),
        "actual_net_profit_improvement": _first_nonempty(economic.get("actual_net_profit_improvement"), economic.get("net_profit_uplift_krw_per_observation_day")),
        "paired_tail_delta_pct": _first_nonempty(
            economic.get("paired_tail_delta_pct"), economic.get("tail_delta_pct"),
            economic.get("downside_tail_delta_pct"),
        ),
        "capital_exposure_delta": _first_nonempty(
            economic.get("capital_exposure_delta"), economic.get("reserve_delta_krw"),
            economic.get("capital_occupation_delta_krw"),
        ),
        "fill_participation_delta_pct": _first_nonempty(
            economic.get("fill_participation_delta_pct"), economic.get("fill_rate_delta_pct"),
        ),
        "model_holdout_status": _first_nonempty(
            economic.get("model_holdout_status"), economic.get("chronological_model_holdout_status"),
        ),
        "candidate_holdout_status": _first_nonempty(
            economic.get("candidate_holdout_status"), economic.get("selection_holdout_status"),
        ),
        "paired_sample_count": paired_sample_count,
        "source_day_count": source_day_count,
        "candidate_count": candidate_count or 0,
        "policy_apply_allowed": policy_allowed is True and status == "validated_edge",
        "policy_handoff_state": handoff,
        "resolution_mode": resolution_mode,
        "historical_evidence_state": historical_evidence_state,
        "prospective_resolution_mode": prospective_resolution_mode,
        "first_blocker": first_blocker,
        "closure_owner": DEFAULT_CLOSURE_OWNER.get(owner),
        "closure_test": economic.get("closure_test") or {
            "entry_cancel_wait": "native_execution_census_cancel_terminal_cost_and_independent_holdouts",
            "entry_split": "submitted_order_frozen_plan_model_holdout_paired_candidate_and_loader",
            "pre_submit_delay": "exact_attempt_submit_clock_quote_cost_terminal_and_independent_holdout",
            "scale_in_split": "eligible_add_fill_terminal_clock_cost_and_independent_paired_holdout",
            "low_price_two_leg": "profile_leg_durable_denominator_custody_cost_and_dated_consumer",
            "low_price_expansion": "retained_source_isolation_frozen_allocator_independent_holdout_and_dated_consumer",
        }.get(owner),
        "model_delta_ev_is_actual_profit": False,
    }


def _runtime_consumption_state(
    target_date: str, sources: dict[str, dict[str, Any]]
) -> tuple[str, str, dict[str, Any]]:
    effective_dates = sorted(
        {
            str(row.get("effective_date"))
            for row in sources.values()
            if row.get("exists") and row.get("target_date_matches")
            and not row.get("error") and row.get("effective_date")
        }
    )
    requested_effective = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE")
    if requested_effective:
        date.fromisoformat(requested_effective)
        if effective_dates and requested_effective not in effective_dates:
            raise ValueError("runtime_summary_prepared_effective_date_missing")
    apply_date = requested_effective or (effective_dates[-1] if effective_dates else target_date)
    runtime_dir = DATA_DIR / "runtime" / "policy_bootstrap"
    manifest_path = runtime_dir / f"runtime_policy_bootstrap_{apply_date}.json"
    verification_path = runtime_dir / f"runtime_policy_bootstrap_verify_{apply_date}.json"
    manifest = _load_json(manifest_path)
    verification = _load_json(verification_path)
    runtime_pid = verification.get("pid")
    receipt_runtime_pid = (
        runtime_pid
        if isinstance(runtime_pid, int)
        and not isinstance(runtime_pid, bool)
        and runtime_pid > 0
        else None
    )
    bootstrap_verified = bool(
        effective_dates
        and manifest.get("target_date") == apply_date
        and verification.get("target_date") == apply_date
        and verification.get("status") == "pass"
        and verification.get("passed") is True
    )
    actual_pid_consumed = bool(
        bootstrap_verified
        and receipt_runtime_pid is not None
        and verification.get("status") == "pass"
        and verification.get("passed") is True
        and verification.get("pid_passed") is True
        and verification.get("pid_env_available") is True
    )
    receipt = {
        "source_date": target_date,
        "effective_dates": effective_dates,
        "apply_date": apply_date if effective_dates else None,
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha(manifest_path),
        "verification_path": str(verification_path),
        "verification_sha256": _sha(verification_path),
        "runtime_pid": receipt_runtime_pid,
        "pid_passed": verification.get("pid_passed"),
        "pid_env_available": verification.get("pid_env_available"),
        "actual_pid_consumed": actual_pid_consumed,
    }
    if not effective_dates:
        return "not_due", "not_applicable", receipt
    if bootstrap_verified:
        return "verified", ("pending" if actual_pid_consumed else "not_due"), receipt
    if verification_path.exists():
        return "rejected", "not_due", receipt
    if manifest_path.exists():
        return "pending", "not_due", receipt
    return "pending", "not_due", receipt


def build_runtime_approval_summary(
    target_date: str, *, include_swing: bool = True, include_producer_gap: bool = True
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    paths = _paths(target_date)
    required_by_owner, owner_contract = _owner_requirements(target_date)
    sources: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []

    for owner, path in paths.items():
        payload, error, read_mode, size_bytes = _read(path)
        artifact_sha256 = _sha(path)
        companion: dict[str, Any] | None = None
        if read_mode == "stream_hash_only_large_json":
            payload, companion, semantic_error = _large_companion(owner, path, target_date, artifact_sha256, paths)
            if semantic_error:
                error = semantic_error
            else:
                read_mode = "bounded_terminal_companion"
        exact_name_date = path.stem.endswith(target_date)
        target_date_matches = _date_matches(payload, target_date) if payload else exact_name_date
        if owner == "compact_policy" and payload:
            target_date_matches = (
                payload.get("compact_evaluation_source_date") == target_date
            )
        if owner == "main_mechanistic_policy" and payload:
            target_date_matches = (
                (payload.get("machine_evaluation_source") or {}).get("source_date")
                == target_date
            )
        required = required_by_owner.get(owner, False)
        applicability = "active_required" if required else ("not_applicable_disabled_by_wrapper" if owner in PRIMARY_DIRECT_OWNERS else "optional_handoff")
        row = {
            "owner": owner, "path": str(path), "exists": path.exists(), "size_bytes": size_bytes,
            "sha256": artifact_sha256, "report_type": payload.get("report_type") or payload.get("schema"),
            "status": payload.get("status") or payload.get("decision") or payload.get("conclusion") or ("artifact_complete" if payload else None),
            "target_date_matches": target_date_matches, "runtime_effect": payload.get("runtime_effect"),
            "source_date": payload.get("source_date"), "publication_date": payload.get("publication_date"),
            "effective_date": payload.get("effective_date"),
            "allowed_runtime_apply": payload.get("allowed_runtime_apply"), "actual_order_submitted": payload.get("actual_order_submitted"),
            "error": error, "read_mode": read_mode, "required": required, "applicability": applicability,
            "producer_flag": PRODUCER_FLAG_BY_OWNER.get(owner), "semantic_companion": companion,
            "artifact_semantic_sha256": payload.get("artifact_sha256"),
            "policy_sha256": payload.get("policy_sha256"),
            "source_report_sha256": payload.get("source_report_sha256"),
            "consumer_schema": payload.get("consumer_schema"),
        }
        if owner in PRIMARY_DIRECT_OWNERS:
            projection = _economic_projection(owner, payload)
            row["economic_evidence"] = projection
            row["policy_owner"] = POLICY_OWNER_BY_SOURCE.get(owner)
        sources[owner] = row
        if required and error:
            blockers.append(f"{owner}:{error}")
        elif required and not target_date_matches:
            blockers.append(f"{owner}:target_date_mismatch")
        elif required and not artifact_sha256:
            blockers.append(f"{owner}:artifact_hash_missing")

    # A validated family result is actionable only when its direct dated policy
    # receipt is also present and hash-bound.  Diagnostic and incumbent outcomes
    # remain valid without inventing a policy handoff.
    for owner in PRIMARY_DIRECT_OWNERS:
        row = sources[owner]
        policy_owner = row.get("policy_owner")
        if not policy_owner:
            continue
        policy = sources.get(str(policy_owner)) or {}
        policy_receipt_valid = bool(
            policy.get("exists") and policy.get("target_date_matches")
            and policy.get("sha256") and not policy.get("error")
        )
        if owner == "rising_missed" and policy_receipt_valid:
            policy_payload = _load_json(Path(str(policy.get("path") or "")))
            source_payload = _load_json(Path(str(row.get("path") or "")))
            policy_receipt_valid = bool(
                policy.get("source_report_sha256")
                == row.get("artifact_semantic_sha256")
                and policy.get("consumer_schema")
                == "rising_missed_tp1_selector_bounded_env_v1"
                and policy.get("policy_sha256")
                == direct_policy_digest(policy_payload)
                and validate_rising_missed_policy_receipt(
                    policy_payload,
                    source_payload,
                    str(policy_payload.get("effective_date") or ""),
                )
                is None
            )
        if owner == "compact_auxiliary" and policy_receipt_valid:
            from src.engine.scalping import compact_auxiliary_paired_replay as compact
            from src.engine.scalping import mechanistic_entry_runtime_policy as compact_policy

            policy_payload = _load_json(Path(str(policy.get("path") or "")))
            source_payload = _load_json(Path(str(row.get("path") or "")))
            policy_receipt_valid = bool(
                compact.valid(source_payload)
                and policy_payload.get("bundle_sha256")
                == compact_policy.digest(
                    {
                        key: value
                        for key, value in policy_payload.items()
                        if key != "bundle_sha256"
                    }
                )
                and policy_payload.get("compact_evaluation_source_date")
                == target_date
                and policy_payload.get("compact_paired_artifact_sha256")
                == source_payload.get("artifact_content_sha256")
                and policy_payload.get("compact_evaluation_fingerprint")
                == source_payload.get("evaluation_fingerprint")
            )
        if owner == "pre_submit_delay" and policy_receipt_valid:
            from src.engine.scalping.pre_submit_delay_tuning import _digest
            policy_payload = _load_json(Path(str(policy.get("path") or "")))
            source_payload = _load_json(Path(str(row.get("path") or "")))
            policy_receipt_valid = bool(
                policy_payload.get("schema") == "pre_submit_delay_policy_v1"
                and source_payload.get("schema") == "pre_submit_delay_tuning_v1"
                and policy_payload.get("policy_sha256")
                == _digest({k: v for k, v in policy_payload.items() if k != "policy_sha256"})
                and policy_payload.get("report_sha256")
                == _digest({k: v for k, v in source_payload.items() if k != "policy_sha256"})
                and source_payload.get("policy_sha256") == policy_payload.get("policy_sha256")
                and policy_payload.get("source_date") == target_date
            )
        if owner == "main_mechanistic_entry" and policy_receipt_valid:
            from src.engine.scalping import mechanistic_entry_runtime_policy as machine_policy

            policy_payload = _load_json(Path(str(policy.get("path") or "")))
            source_payload = _load_json(Path(str(row.get("path") or "")))
            machine_source = policy_payload.get("machine_evaluation_source") or {}
            try:
                row['current_strategy_generation'] = machine_policy.current_strategy_receipt(data_root=DATA_DIR)
            except (OSError, ValueError, TypeError, KeyError) as exc:
                row['current_strategy_generation'] = dict(status='active_generation_invalid', reason=str(exc), actual_pid_consumed=False)
                policy_receipt_valid = False
            try:
                loaded_policy = machine_policy.load(
                    data_root=DATA_DIR,
                    target_date=str(policy_payload.get("target_date") or ""),
                )
                policy_contract_valid = bool(
                    loaded_policy
                    and loaded_policy.get("bundle_sha256")
                    == policy_payload.get("bundle_sha256")
                )
            except (OSError, ValueError):
                policy_contract_valid = False
            from src.engine.scalping.entry_strategy_policy import select_report_candidate
            typed_selection = select_report_candidate(source_payload)
            if not policy_payload.get('winrate_selection') and typed_selection and typed_selection[1].get('promotion_pass') is True:
                policy_contract_valid = bool(policy_contract_valid and
                    (row.get('current_strategy_generation', {}).get('activation') or {}).get('candidate_sha256')
                    == machine_policy.digest(typed_selection[1]['candidate']))
            winrate = policy_payload.get('winrate_selection') or {}
            if winrate:
                winrate_source = _load_json(DATA_DIR / 'report' / 'ai_decision_action_outcome_calibration' /
                    f'winrate_policy_{target_date}.json')
                row['winrate_policy'] = dict(selection_basis=winrate_source.get('selection_basis'),
                    disposition=winrate.get('disposition'),
                    report_sha256=winrate.get('report_sha256'),
                    machine_policy_sha256=winrate.get('machine_policy_sha256'),
                    source_date=winrate_source.get('target_date'),
                    actual_pid_consumed=False)
                policy_receipt_valid = bool(policy_receipt_valid and policy_contract_valid
                    and winrate_source.get('schema') == 'main_entry_winrate_policy_report_v1'
                    and winrate_source.get('selection_basis') == 'win_rate_only'
                    and winrate.get('report_sha256') == winrate_source.get('artifact_content_sha256')
                    and winrate.get('machine_policy_sha256') == machine_policy.digest(policy_payload['machine_policy'])
                    and winrate.get('disposition') == policy_payload.get('machine_disposition')
                    and machine_source.get('artifact_content_sha256') == winrate_source.get('artifact_content_sha256')
                    and winrate_source.get('target_date') == target_date)
            else:
                policy_receipt_valid = bool(
                    policy_receipt_valid and policy_contract_valid
                    and source_payload.get("report_scope") == "main_mechanistic_entry"
                    and source_payload.get("noncompact_sections_refreshed") is True
                    and machine_source.get("source_date") == target_date
                    and machine_source.get("artifact_content_sha256")
                    == source_payload.get("artifact_content_sha256")
                    and machine_source.get("terminal_state")
                    == (source_payload.get("machine_full_evaluation") or {}).get("state")
                )
        row["policy_receipt"] = {
            "owner": policy_owner,
            "path": policy.get("path"),
            "sha256": policy.get("sha256"),
            "target_date_matches": policy.get("target_date_matches"),
            "valid": policy_receipt_valid,
        }
        evidence = row["economic_evidence"]
        if policy.get("exists") and not policy_receipt_valid:
            evidence["policy_handoff_state"] = "blocked"
            evidence["first_blocker"] = (
                evidence["first_blocker"] or "dated_policy_receipt_invalid"
            )
        if evidence["comparison_status"] == "validated_edge" and not policy_receipt_valid:
            evidence.update({
                "comparison_status": "source_gap",
                "policy_handoff_state": "blocked",
                "resolution_mode": "producer_repair",
                "first_blocker": "validated_candidate_policy_receipt_missing",
                "policy_apply_allowed": False,
            })

    active_states = {
        owner: sources[owner]["economic_evidence"]["comparison_status"]
        for owner in PRIMARY_DIRECT_OWNERS if required_by_owner.get(owner)
    }
    comparable_states = {state for state in active_states.values() if state != "not_applicable"}
    economic_counts: Counter[str] = Counter(active_states.values())
    overall_economic_state = "not_applicable" if not comparable_states else next(iter(comparable_states)) if len(comparable_states) == 1 else "mixed"
    preopen_state, natural_state, preopen_receipt = _runtime_consumption_state(target_date, sources)
    direct_state = "complete" if not blockers else "incomplete"
    status = DIRECT_EVIDENCE_COMPLETE if direct_state == "complete" else DIRECT_EVIDENCE_INCOMPLETE
    handoff_states = Counter(
        sources[owner]["economic_evidence"]["policy_handoff_state"]
        for owner in PRIMARY_DIRECT_OWNERS if required_by_owner.get(owner)
    )
    trailing_path = (
        DATA_DIR / "report" / "holding_exit_observation"
        / f"holding_exit_observation_{target_date}.json"
    )
    trailing_payload, trailing_error, trailing_read_mode, _ = _read(trailing_path)
    trailing_readiness = trailing_payload.get("trailing_threshold_readiness") or {}
    trailing_status = (
        "source_gap_report_missing_or_unreadable" if trailing_error
        else "source_gap_report_exceeds_read_limit"
        if trailing_read_mode == "stream_hash_only_large_json"
        else "source_gap_report_date_mismatch"
        if trailing_payload.get("date") != target_date
        else str(trailing_readiness.get("status") or "source_gap_readiness_missing")
    )
    trailing_lineage = {
        "path": str(trailing_path),
        "source_sha256": _sha(trailing_path),
        "source_date": trailing_payload.get("date"),
        "status": trailing_status,
        "read_mode": trailing_read_mode,
        "error": trailing_error,
        "policy_manifest_bound_count": len(
            (trailing_readiness.get("funnel_ids") or {}).get("policy_manifest_bound_ids") or []
        ),
        "grid_source_linked_count": len(
            (trailing_readiness.get("funnel_ids") or {}).get("grid_source_linked_ids") or []
        ),
        "decision_authority": "optional_source_only_no_candidate_or_runtime_apply",
    }
    report = {
        "schema_version": 3, "report_type": "runtime_approval_summary", "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"), "status": status,
        "direct_evidence_state": direct_state, "economic_state": overall_economic_state,
        "economic_state_counts": dict(sorted(economic_counts.items())),
        "validated_edge_count": economic_counts.get("validated_edge", 0),
        "policy_candidate_count": sum(1 for owner in PRIMARY_DIRECT_OWNERS if sources[owner]["economic_evidence"]["policy_handoff_state"] == "candidate_published"),
        "preopen_consumption_state": preopen_state, "natural_acceptance_state": natural_state,
        "preopen_consumption_receipt": preopen_receipt,
        "holding_exit_threshold_lineage": trailing_lineage,
        "policy_handoff_state": (
            "candidate_published" if handoff_states.get("candidate_published")
            else "blocked" if handoff_states.get("blocked")
            else "incumbent_preserved" if handoff_states.get("incumbent_preserved")
            else "not_applicable"
        ),
        "policy_handoff_state_counts": dict(sorted(handoff_states.items())),
        "decision_authority": "family_owned_direct_evidence_summary_only", "common_tuning_candidate_created": False,
        "daily_threshold_cycle_retired": True, "threshold_cycle_ev_retired": True, "owner_contract": owner_contract,
        "sources": sources, "required_source_count": sum(required_by_owner.values()),
        "available_required_source_count": sum(
            1 for owner, required in required_by_owner.items()
            if required and sources[owner]["exists"] and sources[owner]["target_date_matches"] and sources[owner]["sha256"] and not sources[owner]["error"]
        ),
        "blocking_reasons": blockers,
        "economic_blockers": [
            {
                "owner": owner, "comparison_status": sources[owner]["economic_evidence"]["comparison_status"],
                "first_blocker": sources[owner]["economic_evidence"]["first_blocker"],
                "closure_owner": sources[owner]["economic_evidence"]["closure_owner"],
                "closure_test": sources[owner]["economic_evidence"]["closure_test"],
            }
            for owner in PRIMARY_DIRECT_OWNERS
            if required_by_owner.get(owner) and sources[owner]["economic_evidence"]["comparison_status"] in {"source_gap", "unsupported_scope", "mixed"}
        ],
        "runtime_effect": False, "allowed_runtime_apply": False, "actual_order_submitted": False,
        "include_swing": include_swing, "include_producer_gap": include_producer_gap,
    }
    from src.engine.automation.postclose_summary_handoff import stage_overview, stage_path, STAGE_REGISTRY
    if any(stage_path(DATA_DIR / 'report', target_date, stage).exists() for stage in STAGE_REGISTRY):
        report['postclose_stage_status'] = stage_overview(DATA_DIR / 'report', target_date)
    json_path, md_path = summary_paths(target_date)
    _atomic_write(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"# Runtime approval summary - {target_date}", "", f"- status: `{report['status']}`",
        f"- direct evidence: `{report['direct_evidence_state']}`", f"- economic state: `{report['economic_state']}`",
        f"- PREOPEN consumption: `{report['preopen_consumption_state']}`", "- authority: family-owned direct evidence summary only",
        "- common Daily/EV candidate generation: `retired`",
        f"- holding exit threshold lineage: `{trailing_status}`; source hash: `{trailing_lineage['source_sha256'] or '-'}`",
        f"- required sources: `{report['available_required_source_count']}/{report['required_source_count']}`", "", "## Direct owners", "",
        "| Owner | Required | Evidence | Economic | Policy handoff | First blocker |", "|---|---:|---|---|---|---|",
    ]
    for name, row in sources.items():
        economic = row.get("economic_evidence") or {}
        lines.append(
            f"| `{name}` | `{row['required']}` | `{row.get('status') or row.get('error') or '-'}` | "
            f"`{economic.get('comparison_status') or '-'}` | `{economic.get('policy_handoff_state') or '-'}` | "
            f"`{economic.get('first_blocker') or '-'}` |"
        )
    if blockers:
        lines.extend(["", "## Blocking reasons", *[f"- `{value}`" for value in blockers]])
    _atomic_write(md_path, "\n".join(lines) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--exclude-swing", action="store_true")
    parser.add_argument("--producer-gap-disabled", action="store_true")
    args = parser.parse_args(argv)
    report = build_runtime_approval_summary(
        args.target_date,
        include_swing=not args.exclude_swing,
        include_producer_gap=not args.producer_gap_disabled,
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
