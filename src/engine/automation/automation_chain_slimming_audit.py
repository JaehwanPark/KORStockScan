"""Build a report-only slimming audit for the automation chain."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "automation_chain_slimming_audit"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / REPORT_TYPE
POSTCLOSE_SCRIPT = PROJECT_ROOT / "deploy" / "run_threshold_cycle_postclose.sh"
PREOPEN_SCRIPT = PROJECT_ROOT / "deploy" / "run_threshold_cycle_preopen.sh"
TRACEABILITY_DOC = PROJECT_ROOT / "docs" / "report-based-automation-traceability.md"

VALID_PROFILES = {"standard", "aggressive"}
FALSE_DEFAULTS = {"false", "0", "off", "none", "no"}
TRUE_DEFAULTS = {"true", "1", "on", "yes"}
FORBIDDEN_USES = [
    "broker_submit",
    "runtime_threshold_apply",
    "provider_route_change",
    "bot_restart_trigger",
    "position_cap_release",
    "hard_safety_bypass",
]

CORE_MODULES = {
    "src.engine.backfill_threshold_cycle_events",
    "src.engine.daily_threshold_cycle_report",
    "src.engine.threshold_cycle_preopen_apply",
    "src.engine.threshold_cycle_ev_report",
    "src.engine.lifecycle_decision_matrix",
    "src.engine.lifecycle_bucket_discovery",
    "src.engine.runtime_apply_bridge",
    "src.engine.scalping.scalp_sim_auto_approval_control_tower",
    "src.engine.runtime_approval_summary",
    "src.engine.verify_threshold_cycle_postclose_chain",
}

DEEP_AUDIT_MODULE_TOKENS = (
    "runtime_apply_gap_audit",
    "producer_gap_discovery",
    "stage_hook_workorder_discovery",
    "stage_hook_runtime_scaffold",
    "pattern_lab_currentness_audit",
    "pattern_lab_propagation_audit",
    "observation_source_quality_audit",
    "codebase_performance_workorder_report",
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"path": str(path), "status": "missing_or_unreadable"}
    if isinstance(payload, dict):
        return {"path": str(path), "status": "available", "payload": payload}
    return {"path": str(path), "status": "invalid_non_object"}


def _report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _extract_run_defaults(script_text: str) -> list[dict[str, Any]]:
    defaults: list[dict[str, Any]] = []
    pattern = re.compile(
        r'^\s*((?:[A-Z0-9_]*RUN[A-Z0-9_]*|BUILD_CODE_IMPROVEMENT_WORKORDER))="\$\{([A-Z0-9_]+):-([^}]*)\}"',
        re.MULTILINE,
    )
    for match in pattern.finditer(script_text):
        value = match.group(3).strip()
        defaults.append(
            {
                "name": match.group(1),
                "env_var": match.group(2),
                "default": value,
                "default_enabled": _literal_default_enabled(value),
                "default_is_dependency": value.startswith("$"),
            }
        )
    return defaults


def _literal_default_enabled(value: str) -> bool | None:
    normalized = str(value or "").strip().lower()
    if normalized in TRUE_DEFAULTS:
        return True
    if normalized in FALSE_DEFAULTS:
        return False
    return None


def _resolve_run_defaults(defaults: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {str(item.get("name") or ""): item for item in defaults}

    def resolve(name: str, seen: set[str] | None = None) -> bool | None:
        seen = set(seen or set())
        if not name or name in seen:
            return None
        seen.add(name)
        item = by_name.get(name)
        if not item:
            return None
        value = str(item.get("default") or "").strip()
        literal = _literal_default_enabled(value)
        if literal is not None:
            return literal
        if value.startswith("$"):
            return resolve(value[1:], seen)
        return None

    resolved: list[dict[str, Any]] = []
    for item in defaults:
        name = str(item.get("name") or "")
        enabled = resolve(name)
        resolved.append(
            {
                **item,
                "resolved_default_enabled": enabled,
                "default_enabled_resolution": "resolved" if enabled is not None else "unknown",
            }
        )
    return resolved


def _extract_ai_provider_defaults(script_text: str) -> list[dict[str, Any]]:
    defaults: list[dict[str, Any]] = []
    pattern = re.compile(r'^\s*([A-Z0-9_]*AI[A-Z0-9_]*PROVIDER[A-Z0-9_]*)="\$\{([A-Z0-9_]+):-([^}]*)\}"', re.MULTILINE)
    for match in pattern.finditer(script_text):
        defaults.append({"name": match.group(1), "env_var": match.group(2), "default": match.group(3).strip()})
    return defaults


def _clean_artifact_path(raw: str, target_date: str) -> str:
    cleaned = raw.replace("$PROJECT_DIR/", "")
    cleaned = cleaned.replace("${TARGET_DATE}", "{date}").replace("$TARGET_DATE", "{date}")
    cleaned = cleaned.replace(target_date, "{date}")
    return cleaned


def _nearby_artifacts(lines: list[str], start_index: int, target_date: str) -> list[str]:
    artifacts: list[str] = []
    for line in lines[start_index + 1 : min(len(lines), start_index + 15)]:
        if " -m src." in line or "run_postclose_cmd env PYTHONPATH" in line and artifacts:
            break
        for match in re.finditer(r'"\$PROJECT_DIR/([^"]+)"', line):
            artifacts.append(_clean_artifact_path(match.group(1), target_date))
    return sorted(dict.fromkeys(artifacts))


def _extract_guard_flags(line: str) -> list[str]:
    flags = re.findall(r'"\$([A-Z0-9_]*(?:RUN|BUILD_CODE_IMPROVEMENT_WORKORDER)[A-Z0-9_]*)"\s*=\s*"(?:true|1)"', line)
    return sorted(dict.fromkeys(flags))


def _guard_condition_type(line: str, flags: list[str]) -> str:
    if not flags:
        return "none"
    if "||" in line and "&&" in line:
        return "compound"
    if "||" in line:
        return "any"
    return "all"


def _is_shell_if_start(stripped: str) -> bool:
    return bool(re.match(r"^if\b", stripped)) and not stripped.endswith(":")


def _guard_context_by_line(lines: list[str]) -> dict[int, dict[str, Any]]:
    contexts: dict[int, dict[str, Any]] = {}
    stack: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        flags: list[str] = []
        for item in stack:
            flags.extend(item["flags"])
        contexts[index] = {
            "flags": sorted(dict.fromkeys(flags)),
            "conditions": [dict(item) for item in stack if item["condition_type"] != "none"],
            "condition_type": "nested_all"
            if len([item for item in stack if item["condition_type"] != "none"]) > 1
            else next((item["condition_type"] for item in stack if item["condition_type"] != "none"), "none"),
        }

        stripped = line.strip()
        if _is_shell_if_start(stripped):
            guard_flags = _extract_guard_flags(line)
            stack.append(
                {
                    "flags": guard_flags,
                    "condition_type": _guard_condition_type(line, guard_flags),
                }
            )
        if re.match(r"^fi\b", stripped) and stack:
            stack.pop()
    return contexts


def _function_ranges(lines: list[str], function_name: str) -> list[range]:
    ranges: list[range] = []
    start: int | None = None
    for index, line in enumerate(lines):
        if re.match(rf"^{re.escape(function_name)}\(\)\s*\{{", line):
            start = index
            continue
        if start is not None and line == "}":
            ranges.append(range(start, index + 1))
            start = None
    return ranges


def _line_in_ranges(index: int, ranges: list[range]) -> bool:
    return any(index in item for item in ranges)


def _extract_module_calls(script_text: str, wrapper: str, target_date: str) -> list[dict[str, Any]]:
    lines = script_text.splitlines()
    calls: list[dict[str, Any]] = []
    module_counts: Counter[str] = Counter()
    ev_function_ranges = _function_ranges(lines, "run_threshold_cycle_ev_and_wait")
    guard_contexts = _guard_context_by_line(lines)
    for index, line in enumerate(lines):
        match = re.search(r"-m\s+(src\.[A-Za-z0-9_.]+)", line)
        if not match:
            continue
        module = match.group(1)
        if module == "src.engine.threshold_cycle_ev_report" and _line_in_ranges(index, ev_function_ranges):
            continue
        module_counts[module] += 1
        occurrence = module_counts[module]
        nearby = "\n".join(lines[max(0, index - 5) : min(len(lines), index + 12)])
        guard_context = guard_contexts.get(index, {"flags": [], "condition_type": "none"})
        default_flags = list(guard_context.get("flags") or [])
        is_lifecycle_window = (
            module
            in {
                "src.engine.lifecycle_decision_matrix",
                "src.engine.lifecycle_bucket_discovery",
            }
            and ("--window-policy" in nearby or "lifecycle_bucket_window" in nearby)
        )
        calls.append(
            {
                "step_id": f"{wrapper}:{module.rsplit('.', 1)[-1]}:{occurrence}",
                "wrapper": wrapper,
                "line_no": index + 1,
                "producer": module,
                "module": module,
                "occurrence": occurrence,
                "default_flag": default_flags[0] if default_flags else None,
                "default_flags": sorted(dict.fromkeys(default_flags)),
                "default_condition_type": guard_context.get("condition_type") or "none",
                "default_guard_conditions": guard_context.get("conditions") or [],
                "required_artifacts": _nearby_artifacts(lines, index, target_date),
                "ai_dependency": bool(
                    "AI_PROVIDER" in nearby
                    or "openai" in nearby.lower()
                    or "ai_review" in module
                    or "deepseek" in module.lower()
                ),
                "window_policy": "rolling_or_mtd" if is_lifecycle_window else "daily",
                "allow_pending_done_marker": "--allow-pending-done-marker" in nearby,
                "runtime_authority": "preopen_runtime_env_apply_only"
                if module == "src.engine.threshold_cycle_preopen_apply"
                else "report_only",
            }
        )
    for index, line in enumerate(lines):
        match = re.search(r'^\s*run_threshold_cycle_ev_and_wait\s+"([^"]+)"', line)
        if not match:
            continue
        module = "src.engine.threshold_cycle_ev_report"
        module_counts[module] += 1
        occurrence = module_counts[module]
        pass_label = match.group(1)
        calls.append(
            {
                "step_id": f"{wrapper}:threshold_cycle_ev_report:{occurrence}",
                "wrapper": wrapper,
                "line_no": index + 1,
                "producer": module,
                "module": module,
                "occurrence": occurrence,
                "default_flag": None,
                "required_artifacts": [
                    "data/report/threshold_cycle_ev/threshold_cycle_ev_{date}.json",
                    "data/report/threshold_cycle_ev/threshold_cycle_ev_{date}.md",
                ],
                "ai_dependency": False,
                "window_policy": "daily",
                "allow_pending_done_marker": False,
                "runtime_authority": "report_only",
                "function_pass_label": pass_label,
            }
        )
    return calls


def _classify_call(
    call: dict[str, Any],
    module_total_counts: Counter[str],
    profile: str,
    default_enabled: bool | None,
) -> tuple[str, str, str]:
    module = str(call.get("module") or "")
    occurrence = int(call.get("occurrence") or 0)
    base = module.rsplit(".", 1)[-1]
    if default_enabled is False and module not in CORE_MODULES:
        return "deprecated_candidate", "deprecated_candidate", "disabled_by_default_non_core_step"
    if call.get("window_policy") == "rolling_or_mtd":
        return "change_triggered_candidate", "change_triggered", "rolling_or_mtd_full_recompute"
    if module == "src.engine.verify_threshold_cycle_postclose_chain":
        if call.get("allow_pending_done_marker"):
            return "duplicate_refresh_candidate", "change_triggered", "interim_verifier_duplicates_final_verifier"
        return "core_daily", "core_daily", "final_fail_closed_postclose_verifier"
    if module_total_counts[module] > 1 and occurrence > 1:
        return "duplicate_refresh_candidate", "change_triggered", "same_module_reexecuted_in_wrapper"
    if base == "build_code_improvement_workorder":
        return "side_branch_candidate", "change_triggered", "workorder_generation_can_run_outside_strategy_ev_refresh"
    if _is_triggered_deep_review(base):
        mode = "manual_or_weekly" if profile == "aggressive" else "change_triggered"
        return "triggered_deep_review_candidate", mode, "deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap"
    if module in CORE_MODULES:
        return "core_daily", "core_daily", "direct_apply_or_core_handoff_boundary"
    return "manual_or_weekly_candidate", "manual_or_weekly", "support_report_not_direct_apply_boundary"


def _is_triggered_deep_review(base: str) -> bool:
    return any(token in base for token in DEEP_AUDIT_MODULE_TOKENS) or base.endswith("_ai_review") or "ai_deferred_review" in base


def _classification_group(classification: str, recommended_mode: str) -> str:
    if classification == "core_daily":
        return "core_daily"
    if classification == "deprecated_candidate" or recommended_mode == "deprecated_candidate":
        return "deprecated_candidate"
    if recommended_mode == "manual_or_weekly":
        return "manual_or_weekly"
    return "change_triggered"


def _stable_group_counts(counter: Counter[str]) -> dict[str, int]:
    groups = ("core_daily", "change_triggered", "manual_or_weekly", "deprecated_candidate")
    return {group: int(counter.get(group, 0)) for group in groups}


def _step_consumer(module: str) -> str:
    if module == "src.engine.threshold_cycle_preopen_apply":
        return "src/run_bot.sh"
    if module == "src.engine.verify_threshold_cycle_postclose_chain":
        return "postclose health gate"
    if module == "src.engine.build_code_improvement_workorder":
        return "Codex implementation intake"
    if "lifecycle" in module or "runtime_apply" in module:
        return "threshold_cycle_ev/runtime_approval_summary/preopen_apply"
    return "postclose summary consumers"


def _build_inventory(
    calls: list[dict[str, Any]],
    run_defaults: list[dict[str, Any]],
    profile: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    default_by_name = {item["name"]: item for item in run_defaults}
    module_total_counts = Counter(str(call.get("module") or "") for call in calls)
    inventory: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for call in calls:
        default_flags = [str(item) for item in call.get("default_flags") or []]
        if not default_flags and call.get("default_flag"):
            default_flags = [str(call["default_flag"])]
        default_enabled, default_enabled_resolution = _resolve_call_default_enabled(
            default_flags,
            str(call.get("default_condition_type") or "none"),
            default_by_name,
            call.get("default_guard_conditions") if isinstance(call.get("default_guard_conditions"), list) else None,
        )
        classification, recommended_mode, reason = _classify_call(
            call,
            module_total_counts,
            profile,
            default_enabled if isinstance(default_enabled, bool) else None,
        )
        classification_group = _classification_group(classification, recommended_mode)
        step = {
            "step_id": call["step_id"],
            "wrapper": call["wrapper"],
            "line_no": call["line_no"],
            "producer": call["producer"],
            "consumer": _step_consumer(str(call["module"])),
            "required_artifact": call["required_artifacts"],
            "runtime_authority": call["runtime_authority"],
            "ai_dependency": call["ai_dependency"],
            "default_flag": default_flags[0] if default_flags else None,
            "default_flags": default_flags,
            "default_guard_conditions": call.get("default_guard_conditions") or [],
            "default_enabled": default_enabled,
            "default_enabled_resolution": default_enabled_resolution,
            "classification": classification,
            "classification_group": classification_group,
            "recommended_mode": recommended_mode,
            "classification_reason": reason,
            "runtime_effect": call["runtime_authority"] == "preopen_runtime_env_apply_only",
            "allowed_runtime_apply": call["runtime_authority"] == "preopen_runtime_env_apply_only",
        }
        inventory.append(step)
        if classification != "core_daily":
            candidates.append(
                {
                    "candidate_id": f"slim_{len(candidates) + 1:03d}",
                    "source_step_id": step["step_id"],
                    "producer": step["producer"],
                    "classification": classification,
                    "classification_group": classification_group,
                    "recommended_mode": recommended_mode,
                    "reason": reason,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "forbidden_uses": list(FORBIDDEN_USES),
                }
            )
    return inventory, candidates


def _resolve_call_default_enabled(
    default_flags: list[str],
    condition_type: str,
    default_by_name: dict[str, dict[str, Any]],
    guard_conditions: list[dict[str, Any]] | None = None,
) -> tuple[bool | None, str]:
    if not default_flags:
        return True, "unconditional"
    conditions = guard_conditions or [{"flags": default_flags, "condition_type": condition_type}]
    condition_values: list[bool | None] = []
    for condition in conditions:
        flags = [str(item) for item in condition.get("flags") or []]
        values = [default_by_name.get(flag, {}).get("resolved_default_enabled") for flag in flags]
        if not flags or any(value is None for value in values):
            condition_values.append(None)
            continue
        bool_values = [bool(value) for value in values]
        item_type = str(condition.get("condition_type") or "all")
        if item_type == "any":
            condition_values.append(any(bool_values))
        elif item_type == "compound":
            condition_values.append(True if all(bool_values) else None)
        else:
            condition_values.append(all(bool_values))

    if any(value is False for value in condition_values):
        return False, "resolved_guard_nested_all"
    if any(value is None for value in condition_values):
        return None, "unknown_guard_default"
    if len(condition_values) > 1:
        return True, "resolved_guard_nested_all"
    if condition_type == "any":
        return True, "resolved_guard_any"
    if condition_type == "compound":
        return True, "resolved_guard_compound_all_true"
    return True, "resolved_guard_all"


def _must_keep_daily(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keep: list[dict[str, Any]] = []
    for step in inventory:
        producer = str(step.get("producer") or "")
        if step.get("classification") == "core_daily" and (
            "preopen_apply" in producer
            or "verify_threshold_cycle_postclose_chain" in producer
            or "threshold_cycle_ev_report" in producer
            or "runtime_approval_summary" in producer
            or "lifecycle" in producer
            or "runtime_apply_bridge" in producer
        ):
            keep.append(
                {
                    "step_id": step["step_id"],
                    "producer": producer,
                    "reason": step["classification_reason"],
                    "runtime_authority": step["runtime_authority"],
                }
            )
    return keep


def _blocked_reductions() -> list[dict[str, Any]]:
    return [
        {
            "area": "preopen_apply_runtime_env",
            "reason": "direct PREOPEN runtime env apply boundary and bot startup source",
            "forbidden_reduction": "do_not_skip_or_trigger_only_without_replacement_guard",
        },
        {
            "area": "final_postclose_verifier",
            "reason": "fail-closed handoff and wrapper completion quality gate",
            "forbidden_reduction": "do_not_remove_final_verification",
        },
        {
            "area": "hard_safety_and_source_quality_contracts",
            "reason": "broker/order/stale/quantity/provider/cap safety boundaries remain outside slimming scope",
            "forbidden_reduction": "do_not_convert_safety_gate_to_optional",
        },
    ]


def _implementation_workorders(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class = Counter(str(item.get("classification") or "") for item in candidates)
    by_group = Counter(str(item.get("classification_group") or "") for item in candidates)
    workorders: list[dict[str, Any]] = []
    if by_class.get("duplicate_refresh_candidate"):
        workorders.append(
            {
                "workorder_id": "automation_chain_reduce_duplicate_refresh_v1",
                "reason": "multiple same-day refresh/verifier calls detected",
                "candidate_count": by_class["duplicate_refresh_candidate"],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    if by_class.get("change_triggered_candidate"):
        workorders.append(
            {
                "workorder_id": "automation_chain_trigger_lifecycle_windows_v1",
                "reason": "rolling/MTD lifecycle recompute can be gated by input drift or promotion day",
                "candidate_count": by_class["change_triggered_candidate"],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    if by_class.get("triggered_deep_review_candidate"):
        workorders.append(
            {
                "workorder_id": "automation_chain_trigger_deep_audits_v1",
                "reason": "AI/deep audit reports can run on upstream drift, new candidate, or handoff miss",
                "candidate_count": by_class["triggered_deep_review_candidate"],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    if by_class.get("side_branch_candidate"):
        workorders.append(
            {
                "workorder_id": "automation_chain_decouple_workorder_branch_v1",
                "reason": "code-improvement intake can be separated from strategy EV refresh loop",
                "candidate_count": by_class["side_branch_candidate"],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    if by_group.get("deprecated_candidate"):
        workorders.append(
            {
                "workorder_id": "automation_chain_review_disabled_non_core_steps_v1",
                "reason": "disabled-by-default non-core steps can be removed or kept manual after owner review",
                "candidate_count": by_group["deprecated_candidate"],
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        )
    for item in workorders:
        item["forbidden_uses"] = list(FORBIDDEN_USES)
    return workorders


def _estimate_risk(
    class_counts: Counter[str],
    traceability_available: bool,
    status_inputs: dict[str, dict[str, Any]],
) -> str:
    if not traceability_available or class_counts.get("core_daily", 0) < 5:
        return "medium"
    for item in status_inputs.values():
        if item.get("status") != "available":
            return "medium"
    return "low"


def build_report(target_date: str, profile: str = "standard") -> dict[str, Any]:
    if profile not in VALID_PROFILES:
        raise ValueError(f"unsupported_profile:{profile}")
    postclose_text = _read_text(POSTCLOSE_SCRIPT)
    preopen_text = _read_text(PREOPEN_SCRIPT)
    run_defaults = _resolve_run_defaults(_extract_run_defaults(postclose_text))
    ai_provider_defaults = _extract_ai_provider_defaults(postclose_text)
    calls = _extract_module_calls(postclose_text, "postclose", target_date)
    calls.extend(_extract_module_calls(preopen_text, "preopen", target_date))
    inventory, candidates = _build_inventory(calls, run_defaults, profile)
    class_counts = Counter(str(item.get("classification") or "") for item in inventory)
    group_counts = Counter(str(item.get("classification_group") or "") for item in inventory)
    candidate_counts = Counter(str(item.get("classification") or "") for item in candidates)
    candidate_group_counts = Counter(str(item.get("classification_group") or "") for item in candidates)
    status_inputs = {
        "postclose_status": _read_json(
            PROJECT_ROOT
            / "data"
            / "report"
            / "threshold_cycle_postclose_status"
            / f"threshold_cycle_postclose_{target_date}.status.json"
        ),
        "preopen_status": _read_json(
            PROJECT_ROOT
            / "data"
            / "report"
            / "threshold_cycle_preopen_status"
            / f"threshold_cycle_preopen_{target_date}.status.json"
        ),
    }
    traceability_available = bool(_read_text(TRACEABILITY_DOC))
    estimated_risk = _estimate_risk(class_counts, traceability_available, status_inputs)
    report = {
        "schema_version": "automation_chain_slimming_audit_v1",
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "profile": profile,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "report_only_slimming_audit",
        "forbidden_uses": list(FORBIDDEN_USES),
        "input_sources": {
            "postclose_script": str(POSTCLOSE_SCRIPT),
            "preopen_script": str(PREOPEN_SCRIPT),
            "traceability_doc": str(TRACEABILITY_DOC),
            "status_inputs": status_inputs,
        },
        "summary": {
            "total_steps": len(inventory),
            "core_count": class_counts.get("core_daily", 0),
            "change_triggered_candidates": sum(
                count
                for key, count in candidate_counts.items()
                if key in {"change_triggered_candidate", "triggered_deep_review_candidate"}
            ),
            "duplicate_refresh_candidates": candidate_counts.get("duplicate_refresh_candidate", 0),
            "deprecated_candidates": candidate_group_counts.get("deprecated_candidate", 0),
            "side_branch_candidates": candidate_counts.get("side_branch_candidate", 0),
            "manual_or_weekly_candidates": candidate_counts.get("manual_or_weekly_candidate", 0),
            "run_default_count": len(run_defaults),
            "ai_provider_default_count": len(ai_provider_defaults),
            "classification_counts": dict(sorted(class_counts.items())),
            "classification_group_counts": _stable_group_counts(group_counts),
            "estimated_risk": estimated_risk,
        },
        "run_defaults": run_defaults,
        "ai_provider_defaults": ai_provider_defaults,
        "step_inventory": inventory,
        "slimming_candidates": candidates,
        "must_keep_daily": _must_keep_daily(inventory),
        "blocked_reductions": _blocked_reductions(),
        "implementation_workorders": _implementation_workorders(candidates),
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Automation Chain Slimming Audit ({report.get('target_date')})",
        "",
        "## Summary",
        "",
        f"- profile: `{report.get('profile')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- total_steps: `{summary.get('total_steps')}`",
        f"- core_count: `{summary.get('core_count')}`",
        f"- change_triggered_candidates: `{summary.get('change_triggered_candidates')}`",
        f"- duplicate_refresh_candidates: `{summary.get('duplicate_refresh_candidates')}`",
        f"- manual_or_weekly_candidates: `{summary.get('manual_or_weekly_candidates')}`",
        f"- deprecated_candidates: `{summary.get('deprecated_candidates')}`",
        f"- estimated_risk: `{summary.get('estimated_risk')}`",
        f"- classification_group_counts: `{summary.get('classification_group_counts')}`",
        "",
        "## Slimming Candidates",
        "",
        "| candidate_id | producer | classification/group | recommended_mode | reason |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report.get("slimming_candidates") or []:
        lines.append(
            "| `{candidate_id}` | `{producer}` | `{classification}`/{group} | `{recommended_mode}` | {reason} |".format(
                candidate_id=item.get("candidate_id"),
                producer=item.get("producer"),
                classification=item.get("classification"),
                group=item.get("classification_group"),
                recommended_mode=item.get("recommended_mode"),
                reason=item.get("reason"),
            )
        )
    lines.extend(["", "## Must Keep Daily", "", "| step_id | producer | reason |", "| --- | --- | --- |"])
    for item in report.get("must_keep_daily") or []:
        lines.append(f"| `{item.get('step_id')}` | `{item.get('producer')}` | {item.get('reason')} |")
    lines.extend(["", "## Implementation Workorders", "", "| workorder_id | reason | runtime_effect |", "| --- | --- | --- |"])
    for item in report.get("implementation_workorders") or []:
        lines.append(f"| `{item.get('workorder_id')}` | {item.get('reason')} | `{item.get('runtime_effect')}` |")
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report.get("target_date") or "")
    json_path, md_path = _report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")
    parser.add_argument("--profile", choices=sorted(VALID_PROFILES), default="standard")
    parser.add_argument("--write", action="store_true", help="Write JSON/Markdown artifacts.")
    args = parser.parse_args(argv)
    report = build_report(args.date, profile=args.profile)
    if args.write:
        json_path, md_path = write_report(report)
        print(f"wrote {json_path}")
        print(f"wrote {md_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
