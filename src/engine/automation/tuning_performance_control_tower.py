"""Build a compact control view from family-owned direct evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

REPORT_TYPE = "tuning_performance_control_tower"
REPORT_ROOT_DIR = DATA_DIR / "report"
REPORT_DIR = REPORT_ROOT_DIR / REPORT_TYPE


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _sha(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _selected_runtime(
    apply_plan: dict[str, Any] | None = None,
    threshold_ev: dict[str, Any] | None = None,
    runtime_manifest: dict[str, Any] | None = None,
    *,
    pid_receipt: dict[str, Any] | None = None,
    target_date: str,
) -> dict[str, Any]:
    path = DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_{target_date}.json"
    manifest = _load_json(path) or (runtime_manifest or {})
    verify_path = DATA_DIR / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_verify_{target_date}.json"
    verification = _load_json(verify_path) or (pid_receipt or {})
    return {
        "owner": "runtime_policy_bootstrap",
        "manifest_path": str(path),
        "manifest_sha256": _sha(path),
        "target_date": manifest.get("target_date"),
        "selected_families": manifest.get("selected_families") or [],
        "selection_changes": manifest.get("selection_changes") or [],
        "verification_status": verification.get("status") or "not_generated",
        "pid": verification.get("pid"),
        "pid_passed": verification.get("pid_passed"),
        "common_candidate_selection_retired": True,
    }


def build_tuning_performance_control_tower(target_date: str) -> dict[str, Any]:
    from src.engine.automation.postclose_summary_handoff import (
        assert_sources_unchanged,
        source_paths,
        source_receipt,
    )

    summary_path = REPORT_ROOT_DIR / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json"
    verifier_path = REPORT_ROOT_DIR / "threshold_cycle_postclose_verification" / f"threshold_cycle_postclose_verification_{target_date}.json"
    summary = _load_json(summary_path)
    verifier = _load_json(verifier_path)
    preopen_receipt = (
        summary.get("preopen_consumption_receipt")
        if isinstance(summary.get("preopen_consumption_receipt"), dict)
        else {}
    )
    runtime_apply_date = str(preopen_receipt.get("apply_date") or target_date)
    sources = {
        "runtime_approval_summary": {"path": str(summary_path), "sha256": _sha(summary_path)},
        "postclose_verifier": {"path": str(verifier_path), "sha256": _sha(verifier_path)},
    }
    handoff_paths = source_paths(REPORT_ROOT_DIR, target_date, "tower")
    runtime_root = DATA_DIR / "runtime" / "policy_bootstrap"
    observed_runtime_paths = {
        "runtime_policy_bootstrap": runtime_root
        / f"runtime_policy_bootstrap_{runtime_apply_date}.json",
        "runtime_policy_bootstrap_verify": runtime_root
        / f"runtime_policy_bootstrap_verify_{runtime_apply_date}.json",
    }
    handoff_paths.update(
        {
            label: path
            for label, path in observed_runtime_paths.items()
            if path.exists()
        }
    )
    handoff_receipt = source_receipt(handoff_paths, target_date)
    report = {
        "schema_version": 2,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if summary.get("direct_evidence_state") == "complete" and verifier.get("status") == "pass" else "direct_evidence_pending",
        "summary": {
            "direct_source_status": summary.get("direct_evidence_state") or "missing",
            "postclose_verifier_status": verifier.get("status") or "missing",
            "economic_state": summary.get("economic_state") or "not_available",
            "economic_state_counts": summary.get("economic_state_counts") or {},
            "validated_improvement_count": summary.get("validated_edge_count") or 0,
            "policy_candidate_count": summary.get("policy_candidate_count") or 0,
            "preopen_consumption_state": summary.get("preopen_consumption_state") or "not_available",
            "natural_acceptance_state": summary.get("natural_acceptance_state") or "not_available",
            "common_tuning_search_retired": True,
        },
        "selected_runtime": _selected_runtime(target_date=runtime_apply_date),
        "runtime_approval": summary,
        "postclose_verifier_summary": {
            "status": verifier.get("status"),
            "issues": verifier.get("issues") or [],
        },
        "sources": sources,
        "source_generation_contract": handoff_receipt,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "warnings": (
            list(summary.get("blocking_reasons") or [])
            + [
                f"{row.get('owner')}:{row.get('comparison_status')}:{row.get('first_blocker')}"
                for row in summary.get("economic_blockers") or []
                if isinstance(row, dict)
            ]
            + list(verifier.get("issues") or [])
        ),
    }
    json_path, md_path = report_paths(target_date)
    assert_sources_unchanged(handoff_receipt, handoff_paths)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(
        "\n".join([
            f"# Tuning control tower - {target_date}", "",
            f"- status: `{report['status']}`",
            "- common tuning search: `retired`",
            f"- direct source status: `{report['summary']['direct_source_status']}`",
            f"- verifier status: `{report['summary']['postclose_verifier_status']}`",
            f"- runtime bootstrap verification: `{report['selected_runtime']['verification_status']}`", "",
        ]), encoding="utf-8"
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args(argv)
    report = build_tuning_performance_control_tower(args.date)
    print(json.dumps({"date": args.date, "path": str(report_paths(args.date)[0]), "summary": report["summary"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
