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
        "gemini_scalping": {
            "lab_dir": PROJECT_ROOT / "analysis" / "gemini_scalping_pattern_lab",
            "analysis_result": PROJECT_ROOT / "analysis" / "gemini_scalping_pattern_lab" / "outputs" / "ev_analysis_result.json",
            "observability": PROJECT_ROOT / "analysis" / "gemini_scalping_pattern_lab" / "outputs" / "tuning_observability_summary.json",
            "manifest": PROJECT_ROOT / "analysis" / "gemini_scalping_pattern_lab" / "outputs" / "run_manifest.json",
        },
        "claude_scalping": {
            "lab_dir": PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab",
            "analysis_result": PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab" / "outputs" / "ev_analysis_result.json",
            "observability": PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab" / "outputs" / "tuning_observability_summary.json",
            "manifest": PROJECT_ROOT / "analysis" / "claude_scalping_pattern_lab" / "outputs" / "run_manifest.json",
        },
        "deepseek_swing": {
            "lab_dir": PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab",
            "analysis_result": PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab" / "outputs" / "swing_pattern_analysis_result.json",
            "data_quality": PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab" / "outputs" / "data_quality_report.json",
            "manifest": PROJECT_ROOT / "analysis" / "deepseek_swing_pattern_lab" / "outputs" / "run_manifest.json",
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
    contract = payload.get("metric_contract") if isinstance(payload.get("metric_contract"), dict) else {}
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


def _scan_forbidden_terms(lab_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    allowed_suffixes = {".py", ".md", ".sh", ".txt", ".json"}
    for path in sorted(lab_dir.rglob("*")):
        if not path.is_file() or path.suffix not in allowed_suffixes:
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


def _manifest_covers_target(path: Path, target_date: str) -> bool:
    manifest = _load_json(path)
    if not manifest:
        return False
    candidates = []
    analysis_window = manifest.get("analysis_window") if isinstance(manifest.get("analysis_window"), dict) else {}
    candidates.extend([analysis_window.get("start"), analysis_window.get("end")])
    candidates.extend([
        manifest.get("history_coverage_start"),
        manifest.get("history_coverage_end"),
        manifest.get("analysis_start"),
        manifest.get("analysis_end"),
    ])
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
                acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"],
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
                    acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"],
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
                acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"],
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
            source_paths=[hit["path"] for hit in forbidden_hits[:20]] or [PROJECT_ROOT / "analysis"],
            severity="instrumentation_gap",
            order_title="Replace legacy pattern lab stage wording",
            files_likely_touched=sorted({_source_rel(hit["path"]) for hit in forbidden_hits[:20]}),
            acceptance_tests=["rg -n \"shadow-only|canary-ready\" analysis/gemini_scalping_pattern_lab analysis/claude_scalping_pattern_lab analysis/deepseek_swing_pattern_lab -g '!**/outputs/**'"],
        )
    )

    gemini_config = paths["gemini_scalping"]["lab_dir"] / "config.py"
    gemini_config_text = gemini_config.read_text(encoding="utf-8") if gemini_config.exists() else ""
    checks.append(
        _check(
            check_id="gemini_remote_default_excluded",
            ok="PATTERN_LAB_INCLUDE_REMOTE" in gemini_config_text and "\"false\"" in gemini_config_text.lower(),
            finding="Gemini remote logs must be excluded by default and enabled only by PATTERN_LAB_INCLUDE_REMOTE=true.",
            source_paths=[gemini_config],
            severity="source_quality_blocker",
            order_title="Guard Gemini remote log source mode",
            files_likely_touched=["analysis/gemini_scalping_pattern_lab/config.py", "analysis/gemini_scalping_pattern_lab/build_dataset.py"],
            acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_currentness_audit.py"],
        )
    )

    claude_prepare = paths["claude_scalping"]["lab_dir"] / "prepare_dataset.py"
    claude_prepare_text = claude_prepare.read_text(encoding="utf-8") if claude_prepare.exists() else ""
    checks.append(
        _check(
            check_id="claude_empty_trade_fact_overwrite_guard",
            ok="TRADE_FACT_COLUMNS" in claude_prepare_text and "DataFrame(columns=TRADE_FACT_COLUMNS)" in claude_prepare_text,
            finding="Claude empty input must overwrite trade_fact.csv with header-only CSV to prevent stale reuse.",
            source_paths=[claude_prepare],
            severity="source_quality_blocker",
            order_title="Guard Claude stale trade_fact reuse",
            files_likely_touched=["analysis/claude_scalping_pattern_lab/prepare_dataset.py"],
            acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_claude_scalping_pattern_lab_prepare_dataset.py"],
        )
    )

    deepseek_quality_path = paths["deepseek_swing"]["data_quality"]
    deepseek_quality = _load_json(deepseek_quality_path)
    deepseek_provenance = deepseek_quality.get("sim_probe_provenance") if isinstance(deepseek_quality.get("sim_probe_provenance"), dict) else {}
    checks.append(
        _check(
            check_id="deepseek_sim_probe_provenance",
            ok=bool(deepseek_provenance),
            finding="DeepSeek swing sim/probe/dry-run outputs must include actual_order_submitted/broker_order_forbidden/decision_authority provenance.",
            source_paths=[deepseek_quality_path],
            severity="source_quality_blocker",
            order_title="Add DeepSeek swing sim/probe provenance",
            files_likely_touched=["analysis/deepseek_swing_pattern_lab/prepare_dataset.py"],
            acceptance_tests=["PYTHONPATH=. .venv/bin/pytest -q src/tests/test_deepseek_swing_pattern_lab.py"],
        )
    )

    orders = [
        check["recommended_order"]
        for check in checks
        if isinstance(check.get("recommended_order"), dict)
    ]
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
        },
        "checks": checks,
        "code_improvement_orders": orders,
    }
    json_path, md_path = report_paths(target_date)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
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
    print(f"pattern_lab_currentness_audit status={report['status']} json={json_path} md={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
