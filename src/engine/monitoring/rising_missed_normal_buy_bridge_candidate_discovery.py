"""Discover source-only candidates for the rising-missed normal BUY bridge."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_DIR = PROJECT_ROOT / "data" / "report"
OUTPUT_DIR = REPORT_DIR / "rising_missed_normal_buy_bridge_candidate_discovery"
INTRADAY_ENTRY_BLOCKER_DIR = REPORT_DIR / "intraday_entry_blocker_diagnostics"
RISING_MISSED_SCOUT_WORKORDER_DIR = REPORT_DIR / "rising_missed_scout_workorder"
RISING_MISSED_CLASSIFIER_PRIOR_DIR = REPORT_DIR / "rising_missed_classifier_prior"
KST = timezone(timedelta(hours=9))

BRIDGE_ENV_KEY = "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED"
BRIDGE_FAMILY = "rising_missed_normal_buy_bridge"
ELIGIBLE_CLASSES = {"rising_missed_raw", "actionable_major_missed"}
SAFETY_BLOCK_REASONS = {
    "upper_limit_proximity_entry_block",
    "open_pending_entry_order",
    "already_holding",
    "price_above_one_share_entry_cap",
}
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "buy_score_threshold_change",
    "broker_guard_bypass",
    "stale_submit_bypass",
    "order_guard_relaxation",
    "quantity_or_cap_change",
    "forced_one_share_qty_or_tag_reuse",
    "provider_route_change",
    "bot_restart",
    "real_execution_quality_approval",
]


def _now_kst_iso() -> str:
    return datetime.now(tz=KST).isoformat(timespec="seconds")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "null", "none"):
            return default
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except Exception:
        return default


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _walk_values(value: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(value, dict):
        if key in value:
            found.append(value.get(key))
        for child in value.values():
            found.extend(_walk_values(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(_walk_values(child, key))
    return found


def _first_nested(
    row: dict[str, Any], keys: tuple[str, ...], default: Any = None
) -> Any:
    for key in keys:
        for value in _walk_values(row, key):
            if value not in (None, ""):
                return value
    return default


def _default_source_paths(target_date: str) -> dict[str, Path]:
    diagnostic_path = (
        INTRADAY_ENTRY_BLOCKER_DIR
        / f"intraday_entry_blocker_diagnostics_{target_date}.json"
    )
    if not diagnostic_path.exists():
        candidates = sorted(
            INTRADAY_ENTRY_BLOCKER_DIR.glob(
                f"intraday_entry_blocker_diagnostics_{target_date}*.json"
            )
        )
        if candidates:
            diagnostic_path = max(candidates, key=lambda path: path.stat().st_mtime_ns)
    return {
        "intraday_entry_blocker_diagnostics": diagnostic_path,
        "rising_missed_scout_workorder": RISING_MISSED_SCOUT_WORKORDER_DIR
        / f"rising_missed_scout_workorder_{target_date}.json",
        "rising_missed_classifier_prior": RISING_MISSED_CLASSIFIER_PRIOR_DIR
        / f"rising_missed_classifier_prior_{target_date}.json",
    }


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = (
        OUTPUT_DIR
        / f"rising_missed_normal_buy_bridge_candidate_discovery_{target_date}"
    )
    return base.with_suffix(".json"), base.with_suffix(".md")


def _source_refs(source_paths: dict[str, Path]) -> dict[str, Any]:
    return {
        label: {
            "path": str(path),
            "exists": path.exists(),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
        for label, path in source_paths.items()
    }


def _row_block_reason(
    row: dict[str, Any], *, action: str, score: float | None, threshold: float
) -> str:
    klass = str(row.get("rising_missed_class") or "").strip()
    if klass and klass not in ELIGIBLE_CLASSES:
        return (
            klass
            if klass == "source_quality_excluded"
            else "rising_missed_class_not_bridge_eligible"
        )
    if not _truthy(row.get("rising_missed_one_share_eligible")):
        return "rising_missed_one_share_not_eligible"
    source_quality = str(
        _first_nested(row, ("source_quality_gate", "source_quality_status"), "") or ""
    ).lower()
    if "blocked" in source_quality or "fail" in source_quality:
        return "source_quality_blocked"
    safety_reason = str(
        _first_nested(
            row,
            (
                "rising_missed_normal_buy_bridge_reason",
                "rising_missed_class_reason",
                "block_reason",
                "reason",
                "latest_reason",
            ),
            "",
        )
        or ""
    )
    if safety_reason in SAFETY_BLOCK_REASONS:
        return safety_reason
    if action != "BUY":
        return "entry_ai_action_not_buy"
    if score is None:
        return "entry_ai_score_missing"
    if score >= threshold:
        return "score_prior_not_blocking"
    return ""


def _candidate_from_row(row: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    action = (
        str(
            _first_nested(
                row,
                (
                    "rising_missed_entry_ai_action",
                    "entry_ai_action",
                    "ai_action",
                    "last_watching_ai_action",
                    "current_ai_action",
                ),
                "",
            )
            or ""
        )
        .strip()
        .upper()
    )
    score = _safe_float(
        _first_nested(
            row,
            (
                "rising_missed_entry_ai_score",
                "entry_score_value",
                "ai_score",
                "current_ai_score",
                "last_watching_ai_score",
            ),
        )
    )
    threshold = (
        _safe_float(
            _first_nested(row, ("entry_score_threshold", "threshold"), None), 75.0
        )
        or 75.0
    )
    block_reason = _row_block_reason(
        row, action=action, score=score, threshold=threshold
    )
    if block_reason:
        return None, block_reason
    candidate = {
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "rising_missed_class": row.get("rising_missed_class"),
        "rising_missed_one_share_eligible": bool(
            row.get("rising_missed_one_share_eligible")
        ),
        "ai_action": action,
        "ai_score": score,
        "entry_score_threshold": threshold,
        "score_prior_band": _first_nested(row, ("score_prior_band",), "-"),
        "latest_stage": (
            (row.get("latest_blocker") or {}).get("stage")
            if isinstance(row.get("latest_blocker"), dict)
            else row.get("latest_stage")
        ),
        "latest_reason": (
            (row.get("latest_blocker") or {}).get("reason")
            if isinstance(row.get("latest_blocker"), dict)
            else row.get("latest_reason")
        ),
        "source_signature": _first_nested(row, ("source_signature",), "-"),
        "scanner_promotion_reason": _first_nested(
            row, ("scanner_promotion_reason",), "-"
        ),
        "rising_missed_selection_prior_key": _first_nested(
            row,
            ("rising_missed_selection_prior_key",),
            "-",
        ),
        "rising_missed_selection_recommendation": _first_nested(
            row,
            ("rising_missed_selection_recommendation",),
            "unavailable",
        ),
        "max_price_delta_since_first_seen_pct": _safe_float(
            row.get("max_price_delta_since_first_seen_pct")
            or _first_nested(row, ("price_delta_since_first_seen_pct",), None)
        ),
    }
    return candidate, ""


def _bridge_candidate_rows(
    diagnostic: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for row in diagnostic.get("rising_missed_buy") or []:
        if not isinstance(row, dict):
            continue
        candidate, block_reason = _candidate_from_row(row)
        if candidate:
            candidates.append(candidate)
        else:
            blocked.append(
                {
                    "stock_code": row.get("stock_code"),
                    "stock_name": row.get("stock_name"),
                    "rising_missed_class": row.get("rising_missed_class"),
                    "rising_missed_one_share_eligible": bool(
                        row.get("rising_missed_one_share_eligible")
                    ),
                    "blocker": block_reason,
                }
            )
    return candidates, blocked


def _code_improvement_orders(
    candidates: list[dict[str, Any]], source_paths: dict[str, Path]
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    return [
        {
            "order_id": "order_rising_missed_normal_buy_bridge_preopen_env_review",
            "title": "rising missed normal BUY bridge PREOPEN env review",
            "source_report_type": "rising_missed_normal_buy_bridge_candidate_discovery",
            "lifecycle_stage": "entry",
            "target_subsystem": "normal_buy_score_prior_bridge",
            "route": "preopen_env_candidate_review",
            "mapped_family": BRIDGE_FAMILY,
            "threshold_family": BRIDGE_FAMILY,
            "improvement_type": "implemented_runtime_bridge_preopen_candidate",
            "confidence": "same_day_source_only",
            "priority": 1,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "implementation_status": "implemented_but_waiting_sample",
            "implementation_provenance": {
                "implementation_type": "rising_missed_normal_buy_runtime_bridge_hook",
                "runtime_hook_present": True,
                "runtime_env_key": BRIDGE_ENV_KEY,
                "uses_existing_rising_missed_one_share_eligibility": True,
                "uses_normal_buy_sizing": True,
                "forced_one_share_qty_or_tag_used": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "requires_preopen_env_selection": True,
                "root_cause_closure_status_hint": "implementation_done",
            },
            "expected_ev_effect": (
                "Review same-day AI BUY + below-threshold rising-missed eligible rows for next PREOPEN "
                "runtime env selection. The bridge must keep normal BUY sizing and all broker/stale/order guards."
            ),
            "evidence": [
                f"bridge_candidate_count={len(candidates)}",
                f"runtime_env_key={BRIDGE_ENV_KEY}",
                "runtime_effect=false",
                "allowed_runtime_apply=false",
                "forced_one_share_qty_or_tag_used=false",
            ],
            "source_paths": [str(path) for path in source_paths.values()],
            "files_likely_touched": [
                "src/engine/sniper_state_handlers.py",
                "src/engine/scalping/rising_missed_one_share_entry.py",
                "src/utils/constants.py",
            ],
            "acceptance_tests": [
                'PYTHONPATH=. .venv/bin/pytest src/tests/test_sniper_scale_in.py -k "rising_missed or blocked_ai_score"',
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_constants.py",
                "bridge ON must not bypass stale quote, broker/account/order/quantity/cooldown/pre-submit guards",
            ],
            "forbidden_uses": FORBIDDEN_USES,
            "next_preopen_candidate": {
                "env": {BRIDGE_ENV_KEY: "true"},
                "rollback_env": {BRIDGE_ENV_KEY: "false"},
                "apply_timing": "PREOPEN_ONLY",
                "operator_review_required": True,
            },
        }
    ]


def build_report(
    target_date: str,
    *,
    source_paths: dict[str, Path] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    source_paths = source_paths or _default_source_paths(target_date)
    generated_at = generated_at or _now_kst_iso()
    missing_sources = [
        label
        for label, path in source_paths.items()
        if label == "intraday_entry_blocker_diagnostics" and not path.exists()
    ]
    diagnostic = _load_json(source_paths["intraday_entry_blocker_diagnostics"])
    scout = _load_json(source_paths["rising_missed_scout_workorder"])
    prior = _load_json(source_paths["rising_missed_classifier_prior"])
    candidates, blocked = _bridge_candidate_rows(diagnostic)
    blocker_counts = Counter(str(row.get("blocker") or "unknown") for row in blocked)
    prior_summary = (
        prior.get("summary") if isinstance(prior.get("summary"), dict) else {}
    )
    scout_summary = (
        scout.get("summary") if isinstance(scout.get("summary"), dict) else {}
    )
    orders = _code_improvement_orders(candidates, source_paths)
    return {
        "schema_version": 1,
        "report_type": "rising_missed_normal_buy_bridge_candidate_discovery",
        "target_date": target_date,
        "generated_at": generated_at,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "source_only_preopen_env_candidate_discovery",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contracts": {
            "bridge_candidate_count": {
                "metric_role": "source_quality_gate",
                "decision_authority": "source_only_preopen_env_candidate_discovery",
                "window_policy": "same_day_postclose_intraday_entry_blocker_rows",
                "sample_floor": "1_ai_buy_below_threshold_rising_missed_eligible_row",
                "primary_decision_metric": "bridge_candidate_count",
                "source_quality_gate": "rising_missed_one_share_eligible_and_entry_score_usable",
                "forbidden_uses": FORBIDDEN_USES,
            }
        },
        "source": _source_refs(source_paths),
        "summary": {
            "bridge_candidate_count": len(candidates),
            "blocked_row_count": len(blocked),
            "blocked_reason_counts": dict(blocker_counts),
            "status": (
                "source_missing"
                if missing_sources
                else "preopen_env_candidate" if candidates else "hold_no_candidate"
            ),
            "missing_required_sources": missing_sources,
            "runtime_env_key": BRIDGE_ENV_KEY,
            "scout_profitable_forced_scout_count": scout_summary.get(
                "profitable_forced_scout_count"
            ),
            "classifier_prior_count": prior_summary.get("prior_count"),
            "code_improvement_order_count": len(orders),
        },
        "bridge_candidates": candidates[:50],
        "blocked_rows": blocked[:50],
        "code_improvement_orders": orders,
    }


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Rising Missed Normal BUY Bridge Candidate Discovery - {report.get('target_date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        "- decision_authority: `source_only_preopen_env_candidate_discovery`",
        "- runtime_effect: `false`",
        "- allowed_runtime_apply: `false`",
        f"- runtime_env_key: `{summary.get('runtime_env_key')}`",
        "",
        "## Summary",
        "",
        f"- status: `{summary.get('status')}`",
        f"- bridge_candidate_count: `{summary.get('bridge_candidate_count')}`",
        f"- blocked_row_count: `{summary.get('blocked_row_count')}`",
        f"- code_improvement_order_count: `{summary.get('code_improvement_order_count')}`",
        "",
        "## Candidates",
        "",
    ]
    for item in report.get("bridge_candidates") or []:
        lines.append(
            f"- `{item.get('stock_code')}` {item.get('stock_name')}: "
            f"score={item.get('ai_score')} threshold={item.get('entry_score_threshold')} "
            f"source_signature={item.get('source_signature')}"
        )
    if not report.get("bridge_candidates"):
        lines.append("- none")
    lines.extend(["", "## Workorders", ""])
    for order in report.get("code_improvement_orders") or []:
        lines.append(
            f"- `{order.get('order_id')}` route=`{order.get('route')}` env=`{BRIDGE_ENV_KEY}`"
        )
    if not report.get("code_improvement_orders"):
        lines.append("- none")
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build rising missed normal BUY bridge candidate discovery."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--intraday-entry-blocker-path", type=Path)
    parser.add_argument("--rising-missed-scout-workorder-path", type=Path)
    parser.add_argument("--rising-missed-classifier-prior-path", type=Path)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    source_paths = _default_source_paths(args.target_date)
    if args.intraday_entry_blocker_path:
        source_paths["intraday_entry_blocker_diagnostics"] = (
            args.intraday_entry_blocker_path
        )
    if args.rising_missed_scout_workorder_path:
        source_paths["rising_missed_scout_workorder"] = (
            args.rising_missed_scout_workorder_path
        )
    if args.rising_missed_classifier_prior_path:
        source_paths["rising_missed_classifier_prior"] = (
            args.rising_missed_classifier_prior_path
        )
    report = build_report(
        args.target_date, source_paths=source_paths, generated_at=args.generated_at
    )
    default_json, default_md = _default_output_paths(args.target_date)
    output_json = args.output_json or default_json
    output_md = args.output_md or default_md
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        print(
            json.dumps(
                {
                    "output_json": str(output_json),
                    "output_md": str(output_md),
                    **report["summary"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
