"""Build trigger decisions for postclose automation-chain slimming."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_TYPE = "automation_chain_trigger_decision"
REPORT_DIR = PROJECT_ROOT / "data" / "report" / REPORT_TYPE
SCOPES = {"lifecycle_windows", "deep_audits", "workorder_branch", "all"}
FORBIDDEN_USES = [
    "broker_submit",
    "runtime_threshold_apply",
    "provider_route_change",
    "bot_restart_trigger",
    "position_cap_release",
    "hard_safety_bypass",
]
DRIFT_TOKENS = (
    "promotion",
    "candidate",
    "conflict",
    "source_quality",
    "handoff",
    "gap",
    "fail",
    "warning",
    "stale",
    "new_bucket",
    "runtime_apply_gap",
    "code_improvement",
)


@dataclass(frozen=True)
class StepSpec:
    step_id: str
    scope: str
    output_paths: tuple[str, ...]
    source_paths: tuple[str, ...]
    force_env: str
    description: str


def _report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _artifact(report_type: str, file_name: str) -> str:
    return f"data/report/{report_type}/{file_name}"


def _pair(report_type: str, stem: str, target_date: str) -> tuple[str, str]:
    return (
        _artifact(report_type, f"{stem}_{target_date}.json"),
        _artifact(report_type, f"{stem}_{target_date}.md"),
    )


def _dated_pair(report_type: str, stem_with_date: str) -> tuple[str, str]:
    return (
        _artifact(report_type, f"{stem_with_date}.json"),
        _artifact(report_type, f"{stem_with_date}.md"),
    )


def _step_specs(target_date: str) -> list[StepSpec]:
    specs: list[StepSpec] = []
    lifecycle_sources = (
        *_pair("lifecycle_decision_matrix", "lifecycle_decision_matrix", target_date),
        *_pair("lifecycle_bucket_discovery", "lifecycle_bucket_discovery", target_date),
    )
    for window in ("rolling5d", "rolling10d", "mtd"):
        specs.append(
            StepSpec(
                step_id=f"lifecycle_window_{window}",
                scope="lifecycle_windows",
                output_paths=(
                    *_dated_pair(
                        "lifecycle_decision_matrix",
                        f"lifecycle_decision_matrix_{target_date}_{window}",
                    ),
                    *_dated_pair(
                        "lifecycle_bucket_discovery",
                        f"lifecycle_bucket_discovery_{target_date}_{window}",
                    ),
                ),
                source_paths=lifecycle_sources,
                force_env="THRESHOLD_CYCLE_FORCE_LIFECYCLE_BUCKET_WINDOWS",
                description=f"rolling/MTD lifecycle bucket window refresh: {window}",
            )
        )

    deep_steps = {
        "scalp_sim_ai_deferred_review": (
            _pair("scalp_sim_ai_deferred_review", "scalp_sim_ai_deferred_review", target_date),
            (
                "data/threshold_cycle/snapshots",
                *_pair("openai_ws", "openai_ws_stability", target_date),
            ),
        ),
        "pattern_lab_currentness_audit": (
            _pair("pattern_lab_currentness_audit", "pattern_lab_currentness_audit", target_date),
            (
                "analysis/gemini_scalping_pattern_lab/outputs/tuning_observability_summary.json",
                "analysis/claude_scalping_pattern_lab/outputs/tuning_observability_summary.json",
            ),
        ),
        "pattern_lab_ai_review": (
            _pair("pattern_lab_ai_review", "pattern_lab_ai_review", target_date),
            _pair("pattern_lab_currentness_audit", "pattern_lab_currentness_audit", target_date),
        ),
        "observation_source_quality_audit": (
            _pair("observation_source_quality_audit", "observation_source_quality_audit", target_date),
            (
                "data/pipeline_events",
                *_pair("lifecycle_decision_matrix", "lifecycle_decision_matrix", target_date),
            ),
        ),
        "codebase_performance_workorder": (
            _pair("codebase_performance_workorder", "codebase_performance_workorder", target_date),
            ("src", "deploy"),
        ),
        "producer_gap_discovery": (
            _pair("producer_gap_discovery", "producer_gap_discovery", target_date),
            (
                *_pair("producer_gap_source_bundle", "producer_gap_source_bundle", target_date),
                *_pair("lifecycle_bucket_discovery", "lifecycle_bucket_discovery", target_date),
            ),
        ),
        "stage_hook_workorder_discovery": (
            _pair("stage_hook_workorder_discovery", "stage_hook_workorder_discovery", target_date),
            _pair("producer_gap_discovery", "producer_gap_discovery", target_date),
        ),
        "stage_hook_runtime_scaffold": (
            _pair("stage_hook_runtime_scaffold", "stage_hook_runtime_scaffold", target_date),
            _pair("stage_hook_workorder_discovery", "stage_hook_workorder_discovery", target_date),
        ),
        "pattern_lab_propagation_audit": (
            _pair("pattern_lab_propagation_audit", "pattern_lab_propagation_audit", target_date),
            (
                *_pair("pattern_lab_currentness_audit", "pattern_lab_currentness_audit", target_date),
                *_pair("pattern_lab_ai_review", "pattern_lab_ai_review", target_date),
            ),
        ),
        "runtime_apply_gap_audit": (
            _pair("runtime_apply_gap_audit", "runtime_apply_gap_audit", target_date),
            (
                *_pair("runtime_approval_summary", "runtime_approval_summary", target_date),
                _artifact("code_improvement_workorder", f"code_improvement_workorder_{target_date}.json"),
                f"docs/code-improvement-workorders/code_improvement_workorder_{target_date}.md",
                *_pair("runtime_apply_bridge", "runtime_apply_bridge", target_date),
            ),
        ),
    }
    for step_id, (outputs, sources) in deep_steps.items():
        specs.append(
            StepSpec(
                step_id=step_id,
                scope="deep_audits",
                output_paths=tuple(outputs),
                source_paths=tuple(sources),
                force_env="THRESHOLD_CYCLE_FORCE_DEEP_AUDITS",
                description=f"triggered deep/report-heavy audit: {step_id}",
            )
        )

    specs.append(
        StepSpec(
            step_id="workorder_branch",
            scope="workorder_branch",
            output_paths=(
                _artifact("code_improvement_workorder", f"code_improvement_workorder_{target_date}.json"),
                f"docs/code-improvement-workorders/code_improvement_workorder_{target_date}.md",
            ),
            source_paths=(
                *_pair("threshold_cycle_ev", "threshold_cycle_ev", target_date),
                *_pair("producer_gap_discovery", "producer_gap_discovery", target_date),
                *_pair("stage_hook_workorder_discovery", "stage_hook_workorder_discovery", target_date),
                *_pair("pattern_lab_currentness_audit", "pattern_lab_currentness_audit", target_date),
                *_pair("pattern_lab_ai_review", "pattern_lab_ai_review", target_date),
            ),
            force_env="THRESHOLD_CYCLE_FORCE_WORKORDER_BRANCH",
            description="code-improvement workorder side branch",
        )
    )
    return specs


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _read_json(path: Path) -> tuple[bool, Any]:
    try:
        return True, json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, str(exc)


def _path_status(path_text: str, require_json_parse: bool = True) -> dict[str, Any]:
    path = _resolve(path_text)
    if not path.exists():
        return {"path": path_text, "status": "missing", "mtime": None}
    if path.is_dir():
        return {"path": path_text, "status": "available_dir", "mtime": path.stat().st_mtime}
    if path.stat().st_size <= 0:
        return {"path": path_text, "status": "empty", "mtime": path.stat().st_mtime}
    if path.suffix == ".json" and require_json_parse:
        ok, detail = _read_json(path)
        if not ok:
            return {
                "path": path_text,
                "status": "unreadable_json",
                "mtime": path.stat().st_mtime,
                "error": detail,
            }
    return {"path": path_text, "status": "available", "mtime": path.stat().st_mtime}


def _max_mtime(statuses: list[dict[str, Any]]) -> float | None:
    mtimes = [item.get("mtime") for item in statuses if isinstance(item.get("mtime"), (int, float))]
    return max(mtimes) if mtimes else None


def _min_mtime(statuses: list[dict[str, Any]]) -> float | None:
    mtimes = [item.get("mtime") for item in statuses if isinstance(item.get("mtime"), (int, float))]
    return min(mtimes) if mtimes else None


def _contains_drift_signal(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(token in key_text for token in DRIFT_TOKENS):
                if item not in (None, False, 0, "", [], {}):
                    return True
            if _contains_drift_signal(item):
                return True
    elif isinstance(value, list):
        return any(_contains_drift_signal(item) for item in value)
    elif isinstance(value, str):
        text = value.lower()
        return any(token in text for token in DRIFT_TOKENS)
    return False


def _source_has_drift_signal(source_paths: tuple[str, ...]) -> bool:
    for path_text in source_paths:
        path = _resolve(path_text)
        if not path.exists() or path.is_dir() or path.suffix != ".json":
            continue
        ok, payload = _read_json(path)
        if ok and _contains_drift_signal(payload):
            return True
    return False


def evaluate_step(spec: StepSpec, env: dict[str, str] | None = None) -> dict[str, Any]:
    env = env or os.environ
    force = str(env.get(spec.force_env, "false")).lower() in {"1", "true", "yes", "on"}
    output_statuses = [_path_status(path) for path in spec.output_paths]
    source_statuses = [_path_status(path) for path in spec.source_paths]
    output_missing = any(item["status"] not in {"available", "available_dir"} for item in output_statuses)
    source_missing = any(item["status"] not in {"available", "available_dir"} for item in source_statuses)
    source_mtime = _max_mtime(source_statuses)
    output_mtime = _min_mtime(output_statuses)
    upstream_newer = source_mtime is not None and output_mtime is not None and source_mtime > output_mtime
    drift_signal = False if source_missing else _source_has_drift_signal(spec.source_paths)

    reasons: list[str] = []
    if force:
        reasons.append("force_override")
    if output_missing:
        reasons.append("output_missing_or_unreadable")
    if source_missing:
        reasons.append("source_missing_or_unreadable")
    if upstream_newer:
        reasons.append("upstream_artifact_newer")
    if drift_signal:
        reasons.append("upstream_drift_signal")
    decision = "run" if reasons else "skip"
    if not reasons:
        reasons.append("fresh_outputs_no_trigger")

    return {
        "step_id": spec.step_id,
        "scope": spec.scope,
        "decision": decision,
        "trigger_reasons": reasons,
        "source_missing": source_missing,
        "force_override": force,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": list(FORBIDDEN_USES),
        "description": spec.description,
        "outputs": output_statuses,
        "sources": source_statuses,
    }


def build_report(target_date: str, scope: str = "all", env: dict[str, str] | None = None) -> dict[str, Any]:
    if scope not in SCOPES:
        raise ValueError(f"unsupported scope: {scope}")
    decisions = [
        evaluate_step(spec, env=env)
        for spec in _step_specs(target_date)
        if scope == "all" or spec.scope == scope
    ]
    return {
        "report_type": REPORT_TYPE,
        "schema_version": 1,
        "target_date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": scope,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": list(FORBIDDEN_USES),
        "summary": {
            "total_steps": len(decisions),
            "run_count": sum(1 for item in decisions if item["decision"] == "run"),
            "skip_count": sum(1 for item in decisions if item["decision"] == "skip"),
            "source_missing_count": sum(1 for item in decisions if item["source_missing"]),
            "force_override_count": sum(1 for item in decisions if item["force_override"]),
        },
        "decisions": decisions,
    }


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report["target_date"])
    json_path, md_path = _report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary", {})
    lines = [
        f"# Automation Chain Trigger Decision {report.get('target_date')}",
        "",
        f"- scope: `{report.get('scope')}`",
        f"- run_count: `{summary.get('run_count')}`",
        f"- skip_count: `{summary.get('skip_count')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        "",
        "## Decisions",
        "",
        "| step | decision | reasons |",
        "| --- | --- | --- |",
    ]
    for item in report.get("decisions", []):
        reasons = ", ".join(str(reason) for reason in item.get("trigger_reasons", []))
        lines.append(f"| `{item.get('step_id')}` | `{item.get('decision')}` | {reasons} |")
    lines.append("")
    lines.append("Forbidden uses: " + ", ".join(f"`{item}`" for item in FORBIDDEN_USES))
    lines.append("")
    return "\n".join(lines)


def _decision_for_step(report: dict[str, Any], step_id: str) -> str:
    for item in report.get("decisions", []):
        if item.get("step_id") == step_id:
            return str(item.get("decision") or "run")
    return "run"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--scope", choices=sorted(SCOPES), default="all")
    parser.add_argument("--step")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.date, scope=args.scope)
    if args.write:
        write_report(report)
    if args.step:
        print(_decision_for_step(report, args.step))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
