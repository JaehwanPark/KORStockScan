"""Build disabled source-only runtime hook scaffold provenance."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR

REPORT_TYPE = "stage_hook_runtime_scaffold"
SCHEMA_VERSION = 1
SUPPORTED_HOOKS = {
    "holding_flow_runner_debounce_guard": {
        "stage": "holding",
        "hook_class": "runtime_arbitration_hook",
        "action_namespace": ["EXIT_CONFIRM", "HOLD_REVIEW", "TRIM"],
        "required_source_artifacts": ["runner_regime_counterfactual_producer"],
        "implementation_files": [
            "src/engine/automation/stage_hook_runtime_scaffold.py"
        ],
    },
    "plateau_breakdown_exit_arbitration_probe": {
        "stage": "exit",
        "hook_class": "runtime_arbitration_hook",
        "action_namespace": ["EXIT_CONFIRM", "TAKE_PROFIT_ON_PLATEAU", "HOLD_REVIEW"],
        "required_source_artifacts": ["plateau_breakdown_exit_counterfactual_producer"],
        "implementation_files": [
            "src/engine/automation/stage_hook_runtime_scaffold.py"
        ],
    },
}
FORBIDDEN_USES = [
    "real order enablement",
    "threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "hard stop override",
    "protect stop override",
    "emergency stop override",
    "broker guard bypass",
    "account guard bypass",
    "order guard bypass",
    "quantity guard bypass",
    "cooldown guard bypass",
    "entry decision override",
    "exit decision override",
    "broker order submit",
]


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_TYPE / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def stage_hook_discovery_path(target_date: str) -> Path:
    return (
        REPORT_DIR
        / "stage_hook_workorder_discovery"
        / f"stage_hook_workorder_discovery_{target_date}.json"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _candidate_contracts(discovery: dict[str, Any]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for item in discovery.get("stage_hook_candidates") or []:
        if not isinstance(item, dict):
            continue
        contract = item.get("stage_hook_candidate_contract")
        if isinstance(contract, dict):
            contracts.append(contract)
    return contracts


def build_stage_hook_runtime_scaffold_report(target_date: str) -> dict[str, Any]:
    discovery_path = stage_hook_discovery_path(target_date)
    discovery = _load_json(discovery_path)
    discovery_status = str(discovery.get("status") or "").strip()
    discovery_summary = (
        discovery.get("summary") if isinstance(discovery.get("summary"), dict) else {}
    )
    discovery_ai_status = str(
        discovery_summary.get("ai_two_pass_review_status") or ""
    ).strip()
    discovery_audit_status = str(discovery_summary.get("audit_status") or "").strip()
    source_contract_pass = bool(
        discovery
        and discovery_path.exists()
        and discovery_status != "fail"
        and discovery_ai_status == "parsed"
        and discovery_audit_status == "pass"
    )
    contracts = _candidate_contracts(discovery)
    implemented_hooks = []
    observed_hook_names = {str(item.get("hook_name") or "") for item in contracts}
    if source_contract_pass:
        for hook_name, scaffold in SUPPORTED_HOOKS.items():
            if hook_name not in observed_hook_names:
                continue
            source_contract = next(
                (item for item in contracts if item.get("hook_name") == hook_name), {}
            )
            implemented_hooks.append(
                {
                    "hook_name": hook_name,
                    "status": "implemented",
                    "implementation_status": "implemented",
                    "initial_runtime_state": "disabled",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "requires_separate_runtime_apply_candidate": True,
                    "decision_authority": "stage_hook_disabled_source_only_scaffold",
                    "action_namespace_scope": "review_only_labels_not_runtime_actions",
                    "stage": scaffold["stage"],
                    "hook_class": scaffold["hook_class"],
                    "action_namespace": scaffold["action_namespace"],
                    "required_source_artifacts": scaffold["required_source_artifacts"],
                    "implementation_files": scaffold["implementation_files"],
                    "source_candidate_ids": source_contract.get("source_candidate_ids")
                    or [],
                    "acceptance_tests": [
                        "scaffold artifact preserves runtime_effect=false",
                        "hook remains disabled until separate runtime apply candidate",
                        "forbidden uses remain blocked",
                    ],
                    "forbidden_uses": FORBIDDEN_USES,
                }
            )
    missing_supported_hooks = sorted(
        observed_hook_names.intersection(SUPPORTED_HOOKS)
        - {item["hook_name"] for item in implemented_hooks}
    )
    status = (
        "pass"
        if implemented_hooks
        else ("fail" if not source_contract_pass else "warning")
    )
    report = {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "status": status,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "runtime_mutation_allowed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "stage_hook_disabled_source_only_scaffold",
        "metric_role": "source_quality_gate",
        "window_policy": "postclose_stage_hook_scaffold_provenance",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "stage hook discovery artifact exists and hook is implemented as disabled source-only scaffold",
        "forbidden_uses": FORBIDDEN_USES,
        "sources": {
            "stage_hook_workorder_discovery": (
                str(discovery_path) if discovery_path.exists() else None
            )
        },
        "summary": {
            "status": status,
            "implemented_hook_count": len(implemented_hooks),
            "candidate_hook_count": len(contracts),
            "missing_supported_hooks": missing_supported_hooks,
            "implemented_hook_names": [item["hook_name"] for item in implemented_hooks],
            "source_contract_pass": source_contract_pass,
            "source_discovery_status": discovery_status or "missing",
            "source_ai_two_pass_review_status": discovery_ai_status or "missing",
            "source_audit_status": discovery_audit_status or "missing",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "implemented_hooks": implemented_hooks,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Stage Hook Runtime Scaffold - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- implemented_hook_count: `{summary.get('implemented_hook_count')}`",
        f"- implemented_hook_names: `{summary.get('implemented_hook_names') or []}`",
        "",
        "## Hooks",
        "",
    ]
    for item in report.get("implemented_hooks") or []:
        lines.extend(
            [
                f"### `{item.get('hook_name')}`",
                f"- stage: `{item.get('stage')}`",
                f"- hook_class: `{item.get('hook_class')}`",
                f"- initial_runtime_state: `{item.get('initial_runtime_state')}`",
                f"- requires_separate_runtime_apply_candidate: `{item.get('requires_separate_runtime_apply_candidate')}`",
                f"- action_namespace_scope: `{item.get('action_namespace_scope')}`",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build disabled source-only stage hook scaffold provenance."
    )
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    report = build_stage_hook_runtime_scaffold_report(args.date)
    print(
        json.dumps(
            {
                "status": report.get("status"),
                "json": str(report_paths(args.date)[0]),
                "md": str(report_paths(args.date)[1]),
            },
            ensure_ascii=False,
        )
    )
    if report.get("status") == "fail":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
