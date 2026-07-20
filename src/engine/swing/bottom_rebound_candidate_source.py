"""Build a source-only swing candidate packet from bottom rebound research.

This module consumes the research-only bottom rebound report and emits a
loosely coupled postclose candidate artifact. It does not write to the
database, recommendation_history, runtime env, broker, provider, or bot state.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.swing.sim_auto_approval_control_tower import (
    bottom_rebound_is_approved_by_control_tower,
    swing_sim_auto_approval_path,
)
from src.engine.swing.bottom_rebound_pattern_research import (
    FORBIDDEN_USES as RESEARCH_FORBIDDEN_USES,
)
from src.engine.swing.bottom_rebound_pattern_research import (
    REPORT_DIR as BOTTOM_REBOUND_REPORT_DIR,
)
from src.utils.constants import DATA_DIR

REPORT_TYPE = "swing_bottom_rebound_candidate_source"
SCHEMA_VERSION = "swing_bottom_rebound_candidate_source_v1"
DECISION_AUTHORITY = "swing_sim_candidate_source_only"
POLICY_VERSION = "bottom_rebound_swing_source_v1"
REPORT_DIR = Path(DATA_DIR) / "report" / REPORT_TYPE
POLICY_AUTO_LOOP_DIR = (
    Path(DATA_DIR) / "report" / "swing_bottom_rebound_policy_auto_loop"
)
FORBIDDEN_USES = sorted(
    set(
        RESEARCH_FORBIDDEN_USES
        + [
            "recommendation_history_replacement",
            "swing_real_order_conversion",
            "phase0_real_canary_reopen",
            "telegram_buy_alert",
            "direct_swing_runtime_hook",
        ]
    )
)


@dataclass(frozen=True)
class CandidateSourceConfig:
    target_date: str | None = None
    max_candidates: int = 30
    min_backtest_rank_score: float = 3.0
    min_primary_adjusted_ev_pct: float = 0.0
    require_research_contract: bool = True
    source_family: str = "bottom_rebound_pattern_research"
    policy_version: str = POLICY_VERSION


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _bottom_report_path(target_date: str) -> Path:
    return (
        BOTTOM_REBOUND_REPORT_DIR
        / f"bottom_rebound_pattern_research_{target_date}.json"
    )


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _policy_auto_loop_path(target_date: str) -> Path:
    return (
        POLICY_AUTO_LOOP_DIR
        / f"swing_bottom_rebound_policy_auto_loop_{target_date}.json"
    )


def config_from_policy_auto_loop(
    policy_report: dict[str, Any],
    *,
    target_date: str | None = None,
    require_sim_auto_approved: bool = True,
    control_tower_approval: dict[str, Any] | None = None,
) -> tuple[CandidateSourceConfig, dict[str, Any]]:
    conclusion = (
        policy_report.get("final_conclusion")
        if isinstance(policy_report.get("final_conclusion"), dict)
        else {}
    )
    approved_policy = (
        policy_report.get("sim_auto_approved_policy")
        if isinstance(policy_report.get("sim_auto_approved_policy"), dict)
        else {}
    )
    policy_approved = (
        conclusion.get("classification_state") == "sim_auto_approved"
        and conclusion.get("promote_policy") is True
        and bool(approved_policy)
    )
    control_tower_approved = (
        bottom_rebound_is_approved_by_control_tower(control_tower_approval)
        if isinstance(control_tower_approval, dict)
        else False
    )
    approved = policy_approved and (
        control_tower_approved if require_sim_auto_approved else True
    )
    diagnostics = {
        "policy_report_type": policy_report.get("report_type"),
        "policy_date": policy_report.get("date"),
        "approved": approved,
        "policy_approved": policy_approved,
        "control_tower_approved": control_tower_approved,
        "classification_state": conclusion.get("classification_state"),
        "promote_policy": conclusion.get("promote_policy"),
        "require_sim_auto_approved": require_sim_auto_approved,
    }
    if require_sim_auto_approved and not approved:
        block_reason = (
            "control_tower_sim_auto_approval_missing"
            if policy_approved and not control_tower_approved
            else "policy_not_sim_auto_approved"
        )
        return (
            CandidateSourceConfig(
                target_date=target_date or _date_text(policy_report.get("date")),
                max_candidates=0,
                min_backtest_rank_score=1_000_000_000.0,
            ),
            {**diagnostics, "block_reason": block_reason},
        )
    return (
        CandidateSourceConfig(
            target_date=target_date or _date_text(policy_report.get("date")),
            max_candidates=int(
                approved_policy.get("max_candidates")
                or CandidateSourceConfig.max_candidates
            ),
            min_backtest_rank_score=_safe_float(
                approved_policy.get("min_backtest_rank_score"),
                CandidateSourceConfig.min_backtest_rank_score,
            ),
            min_primary_adjusted_ev_pct=_safe_float(
                approved_policy.get("min_primary_adjusted_ev_pct"),
                CandidateSourceConfig.min_primary_adjusted_ev_pct,
            ),
            policy_version=str(approved_policy.get("policy_version") or POLICY_VERSION),
        ),
        diagnostics,
    )


def _source_contract_pass(
    report: dict[str, Any], config: CandidateSourceConfig
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not config.require_research_contract:
        return True, reasons
    if report.get("decision_authority") != "research_only":
        reasons.append("source_decision_authority_not_research_only")
    if report.get("runtime_effect") is not False:
        reasons.append("source_runtime_effect_not_false")
    if report.get("broker_order_forbidden") is not True:
        reasons.append("source_broker_order_forbidden_not_true")
    if report.get("allowed_runtime_apply") is not False:
        reasons.append("source_allowed_runtime_apply_not_false")
    if not isinstance(report.get("latest_as_of_research_only_candidates"), list):
        reasons.append("source_latest_candidates_missing")
    return not reasons, reasons


def _primary_adjusted_ev(report: dict[str, Any]) -> float:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return _safe_float(summary.get("top_primary_source_quality_adjusted_ev_pct"))


def _entry_policy(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return str(summary.get("top_primary_entry_policy") or "atr_pullback_entry")


def _candidate_row(
    row: dict[str, Any],
    *,
    report: dict[str, Any],
    rank: int,
    config: CandidateSourceConfig,
) -> dict[str, Any]:
    code = str(row.get("stock_code") or "").zfill(6)
    primary_policy = _entry_policy(report)
    return {
        "candidate_id": f"{config.policy_version}:{_date_text(report.get('date'))}:{code}",
        "source_date": _date_text(report.get("date")),
        "stock_code": code,
        "stock_name": str(row.get("stock_name") or ""),
        "source_family": config.source_family,
        "policy_version": config.policy_version,
        "candidate_rank": rank,
        "candidate_stage": "selection",
        "candidate_intent": "bottom_rebound_swing_sim_entry",
        "recommended_sim_entry_policy": primary_policy,
        "suggested_discovery_arms": [
            "arm03_pullback_equal_fixed10d",
            "arm04_pullback_risk_mae_time",
            "arm07_pullback_vol_scale_recovery",
        ],
        "lifecycle_exploration_score": _safe_float(row.get("backtest_rank_score")),
        "source_quality_adjusted_ev_pct": _primary_adjusted_ev(report),
        "diagnostic_features": {
            "close_price": row.get("close_price"),
            "drawdown_high60_pct": row.get("drawdown_high60_pct"),
            "dist_low60_pct": row.get("dist_low60_pct"),
            "low_retest_count20": row.get("low_retest_count20"),
            "vwap_distance_pct": row.get("vwap_distance_pct"),
            "volume_ratio20": row.get("volume_ratio20"),
            "foreign_roll20_ratio": row.get("foreign_roll20_ratio"),
            "inst_roll20_ratio": row.get("inst_roll20_ratio"),
            "market_regime_bucket": row.get("market_regime_bucket"),
            "flow_combo_bucket": row.get("flow_combo_bucket"),
            "kiwoom_sector": row.get("kiwoom_sector"),
            "kiwoom_theme_tags": row.get("kiwoom_theme_tags") or [],
            "kiwoom_sector_source_quality": row.get("kiwoom_sector_source_quality"),
            "kiwoom_theme_source_quality": row.get("kiwoom_theme_source_quality"),
        },
        "source_features": {
            "bottom_rebound_signal": row,
            "source_report_type": report.get("report_type"),
            "source_schema_version": report.get("schema_version"),
            "source_report_date": report.get("date"),
            "source_primary_entry_policy": primary_policy,
            "source_primary_adjusted_ev_pct": _primary_adjusted_ev(report),
        },
        "decision_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }


def build_candidate_source_report(
    *,
    bottom_report: dict[str, Any],
    source_path: str | Path | None = None,
    config: CandidateSourceConfig | None = None,
    policy_auto_loop: dict[str, Any] | None = None,
    policy_auto_loop_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or CandidateSourceConfig()
    target_date = _date_text(config.target_date or bottom_report.get("date"))
    contract_pass, contract_reasons = _source_contract_pass(bottom_report, config)
    primary_ev = _primary_adjusted_ev(bottom_report)
    source_candidates = (
        bottom_report.get("latest_as_of_research_only_candidates")
        if isinstance(bottom_report.get("latest_as_of_research_only_candidates"), list)
        else []
    )
    warnings: list[str] = []
    if not bottom_report:
        warnings.append("bottom_rebound_report_missing_or_invalid")
    if not contract_pass:
        warnings.extend(contract_reasons)
    if primary_ev < float(config.min_primary_adjusted_ev_pct):
        warnings.append("primary_adjusted_ev_below_candidate_source_floor")
    if policy_auto_loop_diagnostics and policy_auto_loop_diagnostics.get(
        "block_reason"
    ):
        warnings.append(str(policy_auto_loop_diagnostics["block_reason"]))

    rows: list[dict[str, Any]] = []
    if contract_pass and primary_ev >= float(config.min_primary_adjusted_ev_pct):
        ranked = sorted(
            source_candidates,
            key=lambda item: (
                _safe_float(item.get("backtest_rank_score")),
                -abs(_safe_float(item.get("vwap_distance_pct"))),
                -_safe_float(item.get("dist_low60_pct")),
            ),
            reverse=True,
        )
        for row in ranked:
            if _safe_float(row.get("backtest_rank_score")) < float(
                config.min_backtest_rank_score
            ):
                continue
            rows.append(
                _candidate_row(
                    row, report=bottom_report, rank=len(rows) + 1, config=config
                )
            )
            if len(rows) >= max(1, int(config.max_candidates)):
                break
    if not rows:
        warnings.append("no_bottom_rebound_candidates_selected")

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "family": "swing_bottom_rebound_candidate_source",
        "policy_version": config.policy_version,
        "mode": "postclose_source_only_candidate_packet",
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "candidate_source_feature",
            "decision_authority": DECISION_AUTHORITY,
            "window_policy": "postclose_asof_research_report_to_next_day_sim_candidate_source",
            "sample_floor": (
                bottom_report.get("metric_contract", {}).get("sample_floor")
                if isinstance(bottom_report.get("metric_contract"), dict)
                else None
            ),
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "bottom_rebound_research_contract_pass_and_candidate_rank_floor",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "config": asdict(config),
        "source_report": {
            "path": str(source_path) if source_path else None,
            "report_type": bottom_report.get("report_type"),
            "schema_version": bottom_report.get("schema_version"),
            "date": bottom_report.get("date"),
            "decision_authority": bottom_report.get("decision_authority"),
            "runtime_effect": bottom_report.get("runtime_effect"),
            "broker_order_forbidden": bottom_report.get("broker_order_forbidden"),
            "allowed_runtime_apply": bottom_report.get("allowed_runtime_apply"),
            "primary_adjusted_ev_pct": primary_ev,
            "top_primary_entry_policy": _entry_policy(bottom_report),
        },
        "source_quality": {
            "contract_pass": contract_pass,
            "contract_block_reasons": contract_reasons,
            "source_candidate_count": len(source_candidates),
            "selected_candidate_count": len(rows),
            "primary_adjusted_ev_floor": config.min_primary_adjusted_ev_pct,
            "backtest_rank_score_floor": config.min_backtest_rank_score,
            "warnings": warnings,
        },
        "policy_auto_loop": {
            "report_type": (
                (policy_auto_loop or {}).get("report_type")
                if isinstance(policy_auto_loop, dict)
                else None
            ),
            "date": (
                (policy_auto_loop or {}).get("date")
                if isinstance(policy_auto_loop, dict)
                else None
            ),
            "diagnostics": policy_auto_loop_diagnostics or {"status": "not_supplied"},
        },
        "candidate_rows": rows,
        "scannerization_feedback_loop": {
            "state": "source_only_design_ready",
            "allowed_next_mutation": "versioned_candidate_source_config_proposal_only",
            "feedback_sources": [
                "bottom_rebound_pattern_research.backtest",
                "swing_strategy_discovery_labels",
                "swing_strategy_discovery_ev",
                "swing_lifecycle_decision_matrix",
                "approved_real_canary_results_only_after_separate_approval",
            ],
            "mutation_loop": [
                "collect labels and sim outcomes",
                "aggregate by feature bucket and entry arm",
                "propose a new candidate source policy version",
                "run source-only backtest and sim validation",
                "promote only through separate swing discovery or approval contract",
            ],
            "forbidden_automatic_mutations": [
                "same-day live threshold change",
                "broker order enablement",
                "recommendation_history replacement",
                "phase0 real canary approval or broker order enablement",
                "bot restart",
            ],
        },
        "downstream_contract": {
            "recommended_consumer": "swing_strategy_discovery_sim",
            "handoff_mode": "postclose_json_artifact",
            "db_write_performed": False,
            "runtime_hook_performed": False,
            "next_integration_step": "add optional consumer flag that imports candidate_rows as sim-only discovery source",
        },
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    source_quality = (
        report.get("source_quality")
        if isinstance(report.get("source_quality"), dict)
        else {}
    )
    source_report = (
        report.get("source_report")
        if isinstance(report.get("source_report"), dict)
        else {}
    )
    lines = [
        f"# Swing Bottom Rebound Candidate Source - {report.get('date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- broker_order_forbidden: `{report.get('broker_order_forbidden')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- source_report_date: `{source_report.get('date')}`",
        f"- top_primary_entry_policy: `{source_report.get('top_primary_entry_policy')}`",
        f"- primary_adjusted_ev_pct: `{source_report.get('primary_adjusted_ev_pct')}`",
        f"- source_candidate_count: `{source_quality.get('source_candidate_count')}`",
        f"- selected_candidate_count: `{source_quality.get('selected_candidate_count')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Candidates",
        "",
        "| rank | code | name | score | policy | ev | sector | themes |",
        "| ---: | --- | --- | ---: | --- | ---: | --- | --- |",
    ]
    for row in (report.get("candidate_rows") or [])[:30]:
        features = (
            row.get("diagnostic_features")
            if isinstance(row.get("diagnostic_features"), dict)
            else {}
        )
        themes = (
            features.get("kiwoom_theme_tags")
            if isinstance(features.get("kiwoom_theme_tags"), list)
            else []
        )
        lines.append(
            f"| `{row.get('candidate_rank')}` | `{row.get('stock_code')}` | {row.get('stock_name') or ''} | "
            f"`{row.get('lifecycle_exploration_score')}` | `{row.get('recommended_sim_entry_policy')}` | "
            f"`{row.get('source_quality_adjusted_ev_pct')}` | {features.get('kiwoom_sector') or ''} | "
            f"{', '.join(str(item) for item in themes[:3])} |"
        )
    if not report.get("candidate_rows"):
        lines.append("| - | - | - | - | - | - | - | - |")
    lines.extend(
        [
            "",
            "## Feedback Loop",
            "",
            "- Candidate logic may evolve only through versioned source-only policy proposals.",
            "- Backtest, sim, and approved real-canary outcomes can be evidence, but this artifact cannot approve live use.",
            "- Runtime, broker order, provider, threshold, bot, and recommendation_history mutation are forbidden here.",
            "",
        ]
    )
    return "\n".join(lines)


def report_paths(target_date: str, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    base = output_dir / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def build_from_path(
    path: Path,
    *,
    config: CandidateSourceConfig | None = None,
    policy_report_path: Path | None = None,
    require_sim_auto_policy: bool = False,
    control_tower_approval_path: Path | None = None,
) -> dict[str, Any]:
    policy_report = _load_json(policy_report_path) if policy_report_path else {}
    control_tower_approval: dict[str, Any] = {}
    if require_sim_auto_policy:
        approval_date = _date_text(
            (config.target_date if config else None)
            or policy_report.get("date")
            or path.stem.rsplit("_", 1)[-1]
        )
        resolved_control_tower_path = (
            control_tower_approval_path or swing_sim_auto_approval_path(approval_date)
        )
        control_tower_approval = _load_json(resolved_control_tower_path)
    else:
        resolved_control_tower_path = control_tower_approval_path
    policy_diag: dict[str, Any] | None = None
    if policy_report_path:
        config, policy_diag = config_from_policy_auto_loop(
            policy_report,
            target_date=(config.target_date if config else None),
            require_sim_auto_approved=require_sim_auto_policy,
            control_tower_approval=control_tower_approval,
        )
        policy_diag["path"] = str(policy_report_path)
        if require_sim_auto_policy:
            policy_diag["control_tower_path"] = str(resolved_control_tower_path)
    return build_candidate_source_report(
        bottom_report=_load_json(path),
        source_path=path,
        config=config,
        policy_auto_loop=policy_report,
        policy_auto_loop_diagnostics=policy_diag,
    )


def write_report(
    report: dict[str, Any], *, output_dir: Path = REPORT_DIR
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(_date_text(report.get("date")), output_dir)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=None)
    parser.add_argument("--bottom-report", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument(
        "--max-candidates", type=int, default=CandidateSourceConfig.max_candidates
    )
    parser.add_argument(
        "--min-backtest-rank-score",
        type=float,
        default=CandidateSourceConfig.min_backtest_rank_score,
    )
    parser.add_argument(
        "--min-primary-adjusted-ev-pct",
        type=float,
        default=CandidateSourceConfig.min_primary_adjusted_ev_pct,
    )
    parser.add_argument("--policy-report", type=Path, default=None)
    parser.add_argument("--control-tower-approval", type=Path, default=None)
    parser.add_argument("--require-sim-auto-policy", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    target_date = _date_text(args.date) if args.date else None
    source_path = args.bottom_report or _bottom_report_path(
        target_date or date.today().isoformat()
    )
    config = CandidateSourceConfig(
        target_date=target_date,
        max_candidates=args.max_candidates,
        min_backtest_rank_score=args.min_backtest_rank_score,
        min_primary_adjusted_ev_pct=args.min_primary_adjusted_ev_pct,
    )
    policy_report_path = args.policy_report
    if policy_report_path is None and args.require_sim_auto_policy:
        policy_report_path = _policy_auto_loop_path(
            target_date or date.today().isoformat()
        )
    report = build_from_path(
        source_path,
        config=config,
        policy_report_path=policy_report_path,
        require_sim_auto_policy=args.require_sim_auto_policy,
        control_tower_approval_path=args.control_tower_approval,
    )
    if args.no_write:
        print(
            json.dumps(
                {
                    "date": report.get("date"),
                    "source_quality": report.get("source_quality"),
                    "candidate_count": len(report.get("candidate_rows") or []),
                    "warnings": report.get("warnings"),
                },
                ensure_ascii=False,
                default=str,
            )
        )
        return
    paths = write_report(report, output_dir=args.output_dir)
    print(
        f"[DONE] swing_bottom_rebound_candidate_source json={paths['json']} md={paths['md']}"
    )


if __name__ == "__main__":
    main()
