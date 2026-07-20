"""Audit pattern lab currentness and emit report-only workorders."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.daily_threshold_cycle_report import REPORT_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_TYPE = "pattern_lab_currentness_audit"
REPORT_SCHEMA_VERSION = 1
REPORT_DIRNAME = REPORT_TYPE
CLEAN_TUNING_BASELINE_DATE = "2026-06-04"
FORBIDDEN_USES = [
    "threshold mutation",
    "order guard mutation",
    "provider change",
    "bot restart",
    "broker order submit",
]
REQUIRED_METRIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "forbidden_uses",
    "runtime_effect",
)
FORBIDDEN_TERMS = ("shadow-only", "canary-ready")
ACTIVE_SOURCE_SUFFIXES = {".py", ".md", ".sh", ".txt", ".json"}
RETIRED_PATTERN_LABS = {
    "gemini_scalping": {
        "reason": "retired_from_automatic_execution",
        "manual_only": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
}

SCALPING_REENTRY_TERMS = (
    "threshold_cycle_ev",
    "lifecycle_decision_matrix",
    "lifecycle_bucket_discovery",
)
SWING_REENTRY_TERMS = (
    "threshold_cycle_ev",
    "swing_lifecycle_decision_matrix",
    "swing_lifecycle_bucket_discovery",
    "swing_strategy_discovery_ev",
)

FEEDBACK_SOURCE_CONTRACTS = {
    "scalping": {
        "terms": SCALPING_REENTRY_TERMS,
        "artifact_dirs": {
            "threshold_cycle_ev": ("threshold_cycle_ev", "threshold_cycle_ev"),
            "lifecycle_decision_matrix": (
                "lifecycle_decision_matrix",
                "lifecycle_decision_matrix",
            ),
            "lifecycle_bucket_discovery": (
                "lifecycle_bucket_discovery",
                "lifecycle_bucket_discovery",
            ),
            "runtime_approval_summary": (
                "runtime_approval_summary",
                "runtime_approval_summary",
            ),
        },
    },
    "swing": {
        "terms": SWING_REENTRY_TERMS,
        "artifact_dirs": {
            "threshold_cycle_ev": ("threshold_cycle_ev", "threshold_cycle_ev"),
            "swing_lifecycle_decision_matrix": (
                "swing_lifecycle_decision_matrix",
                "swing_lifecycle_decision_matrix",
            ),
            "swing_lifecycle_bucket_discovery": (
                "swing_lifecycle_bucket_discovery",
                "swing_lifecycle_bucket_discovery",
            ),
            "swing_strategy_discovery_ev": (
                "swing_strategy_discovery_ev",
                "swing_strategy_discovery_ev",
            ),
        },
    },
}


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / REPORT_DIRNAME / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _source_rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _lab_paths() -> dict[str, dict[str, Any]]:
    return {
        "claude_scalping": {
            "lab_dir": PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab",
            "analysis_result": PROJECT_ROOT
            / "analysis"
            / "claude_scalping_pattern_lab"
            / "outputs"
            / "ev_analysis_result.json",
            "observability": PROJECT_ROOT
            / "analysis"
            / "claude_scalping_pattern_lab"
            / "outputs"
            / "tuning_observability_summary.json",
            "manifest": PROJECT_ROOT
            / "analysis"
            / "claude_scalping_pattern_lab"
            / "outputs"
            / "run_manifest.json",
        },
        "deepseek_swing": {
            "lab_dir": PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab",
            "analysis_result": PROJECT_ROOT
            / "analysis"
            / "deepseek_swing_pattern_lab"
            / "outputs"
            / "swing_pattern_analysis_result.json",
            "data_quality": PROJECT_ROOT
            / "analysis"
            / "deepseek_swing_pattern_lab"
            / "outputs"
            / "data_quality_report.json",
            "manifest": PROJECT_ROOT
            / "analysis"
            / "deepseek_swing_pattern_lab"
            / "outputs"
            / "run_manifest.json",
        },
    }


def _order(
    *,
    check_id: str,
    title: str,
    finding: str,
    source_paths: list[Path],
    files_likely_touched: list[str],
    acceptance_tests: list[str],
    severity: str,
) -> dict[str, Any]:
    return {
        "order_id": f"order_{REPORT_TYPE}_{check_id}",
        "title": title,
        "source_report_type": REPORT_TYPE,
        "lifecycle_stage": "pattern_lab_currentness",
        "target_subsystem": "pattern_lab",
        "priority": 10,
        "route": "implement_now",
        "confidence": "consensus",
        "intent": finding,
        "expected_ev_effect": "Improve report/source-quality attribution without runtime mutation.",
        "evidence": [_source_rel(path) for path in source_paths],
        "files_likely_touched": files_likely_touched,
        "acceptance_tests": acceptance_tests,
        "improvement_type": severity,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "strategy_effect": False,
        "data_quality_effect": True,
        "tuning_axis_effect": False,
        "next_postclose_metric": f"{REPORT_TYPE}.{check_id}",
        "forbidden_uses": FORBIDDEN_USES,
    }


def _check(
    *,
    check_id: str,
    ok: bool,
    finding: str,
    source_paths: list[Path],
    severity: str = "instrumentation_gap",
    order_title: str,
    files_likely_touched: list[str],
    acceptance_tests: list[str],
) -> dict[str, Any]:
    recommended_order = None
    if not ok:
        recommended_order = _order(
            check_id=check_id,
            title=order_title,
            finding=finding,
            source_paths=source_paths,
            files_likely_touched=files_likely_touched,
            acceptance_tests=acceptance_tests,
            severity=severity,
        )
    return {
        "check_id": check_id,
        "status": "pass" if ok else "fail",
        "severity": "info" if ok else severity,
        "finding": finding,
        "source_paths": [_source_rel(path) for path in source_paths],
        "recommended_order": recommended_order,
    }


def _metric_contract_ok(payload: dict[str, Any]) -> bool:
    contract = (
        payload.get("metric_contract")
        if isinstance(payload.get("metric_contract"), dict)
        else {}
    )
    if int(payload.get("schema_version") or 0) < 2:
        return False
    for field in REQUIRED_METRIC_CONTRACT_FIELDS:
        if field not in contract:
            return False
    return contract.get("runtime_effect") is False


def _observability_contract_ok(path: Path) -> bool:
    payload = _load_json(path)
    if not payload:
        return False
    return _metric_contract_ok(payload)


def _observability_source_contract_ok(path: Path) -> bool:
    payload = _load_json(path)
    if not payload:
        return False
    if int(payload.get("schema_version") or 0) < 3:
        return False
    source_quality = payload.get("source_quality")
    if not isinstance(source_quality, dict):
        return False
    return str(payload.get("source_contract_status") or "") == "pass"


def _observability_embedded_orders(path: Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    orders = (
        payload.get("code_improvement_orders")
        if isinstance(payload.get("code_improvement_orders"), list)
        else []
    )
    return [
        {
            **item,
            "source_report_type": "tuning_observability_summary",
            "handoff_source_report_type": REPORT_TYPE,
            "route": "source_contract_gap",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "strategy_effect": False,
            "data_quality_effect": True,
            "tuning_axis_effect": False,
        }
        for item in orders
        if isinstance(item, dict)
    ]


def _scan_forbidden_terms(lab_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for path in sorted(lab_dir.rglob("*")):
        if not path.is_file() or path.suffix not in ACTIVE_SOURCE_SUFFIXES:
            continue
        parts = set(path.relative_to(lab_dir).parts)
        if "outputs" in parts or "__pycache__" in parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for term in FORBIDDEN_TERMS:
            for match in re.finditer(re.escape(term), text):
                line_no = text.count("\n", 0, match.start()) + 1
                hits.append({"path": path, "line": line_no, "term": term})
    return hits


def _active_source_text(paths: list[Path]) -> str:
    chunks: list[str] = []
    for base in paths:
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(base.rglob("*"))
        for path in files:
            if not path.is_file() or path.suffix not in ACTIVE_SOURCE_SUFFIXES:
                continue
            try:
                rel_parts = (
                    set(path.relative_to(base).parts) if base.is_dir() else set()
                )
            except ValueError:
                rel_parts = set(path.parts)
            if "outputs" in rel_parts or "__pycache__" in rel_parts:
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    return "\n".join(chunks).lower()


def _source_mentions_all(paths: list[Path], terms: tuple[str, ...]) -> bool:
    text = _active_source_text(paths)
    return bool(text) and all(term.lower() in text for term in terms)


def _feedback_artifact_path(report_name: str, stem: str, target_date: str) -> Path:
    return REPORT_DIR / report_name / f"{stem}_{target_date}.json"


def _latest_feedback_artifact_path(
    report_name: str, stem: str, target_date: str
) -> tuple[Path | None, str | None]:
    target = str(target_date).strip()[:10]
    report_dir = REPORT_DIR / report_name
    exact = _feedback_artifact_path(report_name, stem, target)
    if exact.exists():
        return exact, target
    latest_path: Path | None = None
    latest_date: str | None = None
    for path in sorted(report_dir.glob(f"{stem}_*.json")):
        suffix = path.name.removeprefix(f"{stem}_").removesuffix(".json")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", suffix):
            continue
        source_date = suffix
        if (
            target >= CLEAN_TUNING_BASELINE_DATE
            and source_date < CLEAN_TUNING_BASELINE_DATE
        ):
            continue
        if source_date <= target and (latest_date is None or source_date > latest_date):
            latest_path = path
            latest_date = source_date
    return latest_path, latest_date


def _feedback_source_status(
    *,
    target_date: str,
    domain: str,
    source_paths: list[Path],
) -> dict[str, Any]:
    contract = FEEDBACK_SOURCE_CONTRACTS[domain]
    active_text = _active_source_text(source_paths)
    consumed: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    for source_id, (report_name, stem) in contract["artifact_dirs"].items():
        artifact_path, source_date = _latest_feedback_artifact_path(
            report_name, stem, target_date
        )
        mentioned = source_id.lower() in active_text
        exists = artifact_path is not None and artifact_path.exists()
        item = {
            "source_id": source_id,
            "artifact_path": str(artifact_path) if exists else None,
            "source_date": source_date,
            "target_date": target_date,
            "freshness": (
                "same_day"
                if source_date == str(target_date).strip()[:10]
                else "latest_available_lte_target" if source_date else "missing"
            ),
            "active_source_mentions": mentioned,
            "artifact_exists": exists,
            "decision_authority": "source_quality_only",
            "runtime_effect": False,
        }
        if mentioned and exists:
            consumed.append(item)
        else:
            reason = []
            if not mentioned:
                reason.append("active_source_missing_reference")
            if not exists:
                reason.append("same_day_artifact_missing")
            missing.append({**item, "gap_type": "source_quality_gap", "reason": reason})
    return {
        "domain": domain,
        "consumed_feedback_sources": consumed,
        "missing_feedback_sources": missing,
        "decision_authority": "source_quality_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _pattern_lab_ai_review_contract_ok() -> bool:
    candidates = [
        PROJECT_ROOT / "src" / "engine" / "pattern_lab_ai_review.py",
        PROJECT_ROOT / "src" / "engine" / "pattern_lab_ai_reviewer.py",
    ]
    required_terms = (
        "ai_two_pass_review",
        "interpretation",
        "audit",
        "final_conclusions",
        "auditor_pass",
        "explicit_gap_type",
        "source_paths",
        "runtime_effect",
        "allowed_runtime_apply",
        "FORBIDDEN_USES",
    )
    for path in candidates:
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if all(term in text for term in required_terms):
            return True
    return False


def _manifest_covers_target(path: Path, target_date: str) -> bool:
    manifest = _load_json(path)
    if not manifest:
        return False
    candidates = []
    analysis_window = (
        manifest.get("analysis_window")
        if isinstance(manifest.get("analysis_window"), dict)
        else {}
    )
    candidates.extend([analysis_window.get("start"), analysis_window.get("end")])
    candidates.extend(
        [
            manifest.get("history_coverage_start"),
            manifest.get("history_coverage_end"),
            manifest.get("analysis_start"),
            manifest.get("analysis_end"),
        ]
    )
    return any(str(value or "").strip()[:10] == target_date for value in candidates)


def build_pattern_lab_currentness_audit(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    paths = _lab_paths()
    checks: list[dict[str, Any]] = []

    for lab_name, lab in paths.items():
        analysis_path = lab["analysis_result"]
        analysis_payload = _load_json(analysis_path)
        checks.append(
            _check(
                check_id=f"{lab_name}_metric_contract",
                ok=_metric_contract_ok(analysis_payload),
                finding=f"{lab_name} output must expose schema_version>=2 and required metric_contract fields.",
                source_paths=[analysis_path],
                severity="instrumentation_gap",
                order_title=f"{lab_name} metric contract currentness",
                files_likely_touched=[_source_rel(lab["lab_dir"])],
                acceptance_tests=[
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"
                ],
            )
        )
        if lab.get("observability"):
            observability_path = lab["observability"]
            checks.append(
                _check(
                    check_id=f"{lab_name}_observability_metric_contract",
                    ok=_observability_contract_ok(observability_path),
                    finding=f"{lab_name} tuning observability output must expose the common metric contract.",
                    source_paths=[observability_path],
                    severity="instrumentation_gap",
                    order_title=f"{lab_name} observability metric contract currentness",
                    files_likely_touched=["analysis/tuning_observability_summary.py"],
                    acceptance_tests=[
                        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"
                    ],
                )
            )
            checks.append(
                _check(
                    check_id=f"{lab_name}_observability_source_contract",
                    ok=_observability_source_contract_ok(observability_path),
                    finding=(
                        f"{lab_name} tuning observability output must expose schema_version>=3, source_quality, "
                        "source_contract_status=pass, and source contract workorders when producer/consumer inputs drift."
                    ),
                    source_paths=[observability_path],
                    severity="automation_handoff_gap",
                    order_title=f"{lab_name} observability source contract handoff",
                    files_likely_touched=[
                        "analysis/tuning_observability_summary.py",
                        "src/engine/pattern_lab_currentness_audit.py",
                    ],
                    acceptance_tests=[
                        "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_tuning_observability_summary.py src/tests/test_pattern_lab_currentness_audit.py"
                    ],
                )
            )
        manifest_path = lab["manifest"]
        checks.append(
            _check(
                check_id=f"{lab_name}_manifest_freshness",
                ok=_manifest_covers_target(manifest_path, target_date),
                finding=f"{lab_name} manifest must cover target_date={target_date}; stale outputs cannot be reused as fresh source.",
                source_paths=[manifest_path],
                severity="source_quality_blocker",
                order_title=f"{lab_name} stale output freshness guard",
                files_likely_touched=[_source_rel(lab["lab_dir"])],
                acceptance_tests=[
                    "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"
                ],
            )
        )

    forbidden_hits: list[dict[str, Any]] = []
    for lab in paths.values():
        forbidden_hits.extend(_scan_forbidden_terms(lab["lab_dir"]))
    checks.append(
        _check(
            check_id="active_source_forbidden_terms",
            ok=not forbidden_hits,
            finding="Active pattern lab code/docs/prompts must not use legacy shadow-only or canary-ready wording.",
            source_paths=[hit["path"] for hit in forbidden_hits[:20]]
            or [PROJECT_ROOT / "analysis"],
            severity="instrumentation_gap",
            order_title="Replace legacy pattern lab stage wording",
            files_likely_touched=sorted(
                {_source_rel(hit["path"]) for hit in forbidden_hits[:20]}
            ),
            acceptance_tests=[
                "rg -n \"shadow-only|canary-ready\" analysis/gemini_scalping_pattern_lab analysis/claude_scalping_pattern_lab analysis/deepseek_swing_pattern_lab -g '!**/outputs/**'"
            ],
        )
    )

    claude_prepare = paths["claude_scalping"]["lab_dir"] / "prepare_dataset.py"
    claude_prepare_text = (
        claude_prepare.read_text(encoding="utf-8") if claude_prepare.exists() else ""
    )
    checks.append(
        _check(
            check_id="claude_empty_trade_fact_overwrite_guard",
            ok="TRADE_FACT_COLUMNS" in claude_prepare_text
            and "DataFrame(columns=TRADE_FACT_COLUMNS)" in claude_prepare_text,
            finding="Claude empty input must overwrite trade_fact.csv with header-only CSV to prevent stale reuse.",
            source_paths=[claude_prepare],
            severity="source_quality_blocker",
            order_title="Guard Claude stale trade_fact reuse",
            files_likely_touched=[
                "analysis/claude_scalping_pattern_lab/prepare_dataset.py"
            ],
            acceptance_tests=[
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_claude_scalping_pattern_lab_prepare_dataset.py"
            ],
        )
    )

    deepseek_quality_path = paths["deepseek_swing"]["data_quality"]
    deepseek_quality = _load_json(deepseek_quality_path)
    deepseek_provenance = (
        deepseek_quality.get("sim_probe_provenance")
        if isinstance(deepseek_quality.get("sim_probe_provenance"), dict)
        else {}
    )
    checks.append(
        _check(
            check_id="deepseek_sim_probe_provenance",
            ok=bool(deepseek_provenance),
            finding="DeepSeek swing sim/probe/dry-run outputs must include actual_order_submitted/broker_order_forbidden/decision_authority provenance.",
            source_paths=[deepseek_quality_path],
            severity="source_quality_blocker",
            order_title="Add DeepSeek swing sim/probe provenance",
            files_likely_touched=[
                "analysis/deepseek_swing_pattern_lab/prepare_dataset.py"
            ],
            acceptance_tests=[
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py"
            ],
        )
    )

    scalping_lab_dirs = [paths["claude_scalping"]["lab_dir"]]
    feedback_sources = {
        "scalping": _feedback_source_status(
            target_date=target_date,
            domain="scalping",
            source_paths=scalping_lab_dirs,
        ),
        "swing": _feedback_source_status(
            target_date=target_date,
            domain="swing",
            source_paths=[paths["deepseek_swing"]["lab_dir"]],
        ),
    }
    checks.append(
        _check(
            check_id="scalping_ldm_threshold_reentry_sources",
            ok=_source_mentions_all(scalping_lab_dirs, SCALPING_REENTRY_TERMS)
            and not feedback_sources["scalping"]["missing_feedback_sources"],
            finding=(
                "Scalping pattern labs must consume threshold_cycle_ev, lifecycle_decision_matrix, "
                "and lifecycle_bucket_discovery as re-entry sources so LDM/threshold outcomes improve the next lab run."
            ),
            source_paths=scalping_lab_dirs,
            severity="automation_handoff_gap",
            order_title="Feed LDM/threshold feedback into scalping pattern labs",
            files_likely_touched=[
                "analysis/claude_scalping_pattern_lab/prepare_dataset.py",
                "analysis/claude_scalping_pattern_lab/build_claude_payload.py",
                "src/engine/pattern_lab_currentness_audit.py",
            ],
            acceptance_tests=[
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py",
                "pattern lab payloads include LDM bucket/discovery and threshold EV feedback context with runtime_effect=false",
            ],
        )
    )

    checks.append(
        _check(
            check_id="swing_ldm_threshold_reentry_sources",
            ok=_source_mentions_all(
                [paths["deepseek_swing"]["lab_dir"]], SWING_REENTRY_TERMS
            )
            and not feedback_sources["swing"]["missing_feedback_sources"],
            finding=(
                "DeepSeek swing pattern lab must consume threshold_cycle_ev, swing_lifecycle_decision_matrix, "
                "swing_lifecycle_bucket_discovery, and swing_strategy_discovery_ev as re-entry sources."
            ),
            source_paths=[paths["deepseek_swing"]["lab_dir"]],
            severity="automation_handoff_gap",
            order_title="Feed Swing LDM/discovery feedback into DeepSeek swing pattern lab",
            files_likely_touched=[
                "analysis/deepseek_swing_pattern_lab/prepare_dataset.py",
                "analysis/deepseek_swing_pattern_lab/build_deepseek_payload.py",
                "analysis/deepseek_swing_pattern_lab/prompts/prompt_swing_lifecycle_patterns.md",
                "src/engine/pattern_lab_currentness_audit.py",
            ],
            acceptance_tests=[
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py src/tests/test_pattern_lab_currentness_audit.py",
                "DeepSeek payload summary/cases expose Swing LDM bucket/discovery and threshold EV feedback context with runtime_effect=false",
            ],
        )
    )

    checks.append(
        _check(
            check_id="pattern_lab_ai_review_contract",
            ok=_pattern_lab_ai_review_contract_ok(),
            finding=(
                "Pattern lab must have a source-only two-pass AI reviewer contract: first interpretation, second-pass audit, "
                "and final conclusions that re-rank findings against LDM/threshold/workorder feedback and emit explicit "
                "source-quality gaps."
            ),
            source_paths=[
                PROJECT_ROOT / "src" / "engine",
                PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab",
                PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab",
            ],
            severity="ai_review_gap",
            order_title="Add source-only Pattern Lab AI reviewer",
            files_likely_touched=[
                "src/engine/pattern_lab_ai_review.py",
                "deploy/run_threshold_cycle_postclose.sh",
                "src/engine/threshold_cycle_ev_report.py",
                "src/engine/runtime_approval_summary.py",
                "src/engine/build_code_improvement_workorder.py",
                "src/engine/pattern_lab_currentness_audit.py",
            ],
            acceptance_tests=[
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py src/tests/test_threshold_cycle_wrappers.py src/tests/test_build_code_improvement_workorder.py",
                "AI reviewer output must be runtime_effect=false, allowed_runtime_apply=false, and forbidden from order/provider/bot/threshold mutation",
            ],
        )
    )

    embedded_observability_orders: list[dict[str, Any]] = []
    for lab in paths.values():
        if lab.get("observability"):
            embedded_observability_orders.extend(
                _observability_embedded_orders(lab["observability"])
            )

    orders = [
        check["recommended_order"]
        for check in checks
        if isinstance(check.get("recommended_order"), dict)
    ]
    orders.extend(embedded_observability_orders)
    fail_count = sum(1 for check in checks if check["status"] == "fail")
    status = "pass" if fail_count == 0 else "warning"
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "report_type": REPORT_TYPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        "runtime_effect": False,
        "decision_authority": "source_quality_only",
        "forbidden_uses": FORBIDDEN_USES,
        "summary": {
            "check_count": len(checks),
            "fail_count": fail_count,
            "order_count": len(orders),
            "observability_embedded_order_count": len(embedded_observability_orders),
            "consumed_feedback_source_count": sum(
                len(item.get("consumed_feedback_sources") or [])
                for item in feedback_sources.values()
            ),
            "missing_feedback_source_count": sum(
                len(item.get("missing_feedback_sources") or [])
                for item in feedback_sources.values()
            ),
        },
        "retired_labs": RETIRED_PATTERN_LABS,
        "feedback_sources": feedback_sources,
        "checks": checks,
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Pattern Lab Currentness Audit - {report.get('date')}",
        "",
        "## Summary",
        "",
        f"- status: `{report.get('status')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- check_count: `{(report.get('summary') or {}).get('check_count')}`",
        f"- fail_count: `{(report.get('summary') or {}).get('fail_count')}`",
        f"- code_improvement_orders: `{len(report.get('code_improvement_orders') or [])}`",
        "",
        "## Checks",
        "",
    ]
    for check in report.get("checks") or []:
        if not isinstance(check, dict):
            continue
        lines.extend(
            [
                f"### `{check.get('check_id')}`",
                "",
                f"- status: `{check.get('status')}`",
                f"- severity: `{check.get('severity')}`",
                f"- finding: {check.get('finding')}",
                f"- sources: `{check.get('source_paths')}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    args = parser.parse_args(argv)
    report = build_pattern_lab_currentness_audit(args.date)
    json_path, md_path = report_paths(args.date)
    print(
        f"pattern_lab_currentness_audit status={report['status']} json={json_path} md={md_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
