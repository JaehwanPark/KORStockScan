"""Auto-review bottom rebound candidate-source policy for swing sim.

The report produced here can auto-approve only the next source-only swing sim
candidate policy. It cannot mutate runtime env, broker order state, provider
routes, recommendation_history, thresholds, or bot state.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.engine.swing.sim_auto_approval_control_tower import refresh_swing_sim_auto_approval
from src.engine.swing.bottom_rebound_candidate_source import (
    CandidateSourceConfig,
    POLICY_VERSION as CURRENT_SOURCE_POLICY_VERSION,
    REPORT_DIR as CANDIDATE_SOURCE_DIR,
    build_candidate_source_report,
    write_report as write_candidate_source_report,
)
from src.engine.swing.bottom_rebound_pattern_research import REPORT_DIR as RESEARCH_REPORT_DIR
from src.utils.constants import DATA_DIR, TRADING_RULES


REPORT_TYPE = "swing_bottom_rebound_policy_auto_loop"
SCHEMA_VERSION = "swing_bottom_rebound_policy_auto_loop_v1"
DECISION_AUTHORITY = "swing_bottom_rebound_sim_policy_auto_approval"
AI_REVIEW_SCHEMA_NAME = "swing_bottom_rebound_policy_ai_review_v1"
AI_REVIEW_MODEL = str(getattr(TRADING_RULES, "GPT_REPORT_MODEL", "gpt-5.4-mini") or "gpt-5.4-mini")
REPORT_DIR = Path(DATA_DIR) / "report" / REPORT_TYPE
EV_REPORT_DIR = Path(DATA_DIR) / "report" / "swing_strategy_discovery_ev"
FORBIDDEN_USES = [
    "broker_order_submit",
    "real_order_enable",
    "swing_real_canary_approval",
    "provider_route_change",
    "bot_restart",
    "runtime_threshold_mutation",
    "recommendation_history_replacement",
    "same_day_live_entry_relaxation",
]


@dataclass(frozen=True)
class PolicyAutoLoopConfig:
    target_date: str | None = None
    current_policy_version: str = CURRENT_SOURCE_POLICY_VERSION
    proposed_policy_version: str = "bottom_rebound_swing_source_v2"
    min_relative_improvement: float = 0.01
    min_absolute_improvement_pct: float = 0.01
    min_sample_count: int = 5
    max_candidates: int = 40
    min_backtest_rank_score: float = 2.5
    min_primary_adjusted_ev_pct: float = 0.0


def _date_text(value: str | date | datetime | None) -> str:
    if value is None:
        return date.today().isoformat()
    return str(value)[:10]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        numeric = float(value)
        return numeric if math.isfinite(numeric) else default
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _text_hash(payload: Any) -> str:
    import hashlib

    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def default_source_paths(target_date: str) -> dict[str, Path]:
    return {
        "bottom_rebound_research": RESEARCH_REPORT_DIR / f"bottom_rebound_pattern_research_{target_date}.json",
        "candidate_source": CANDIDATE_SOURCE_DIR / f"swing_bottom_rebound_candidate_source_{target_date}.json",
        "swing_strategy_discovery_ev": EV_REPORT_DIR / f"swing_strategy_discovery_ev_{target_date}.json",
    }


def _contract_ok(payload: dict[str, Any], expected_authority: str) -> bool:
    return (
        payload.get("decision_authority") == expected_authority
        and payload.get("runtime_effect") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
    )


def _candidate_source_selected_count(payload: dict[str, Any]) -> int:
    source_quality = payload.get("source_quality") if isinstance(payload.get("source_quality"), dict) else {}
    return _safe_int(source_quality.get("selected_candidate_count"))


def _candidate_source_config(config: PolicyAutoLoopConfig) -> CandidateSourceConfig:
    return CandidateSourceConfig(
        target_date=config.target_date,
        max_candidates=config.max_candidates,
        min_backtest_rank_score=config.min_backtest_rank_score,
        min_primary_adjusted_ev_pct=config.min_primary_adjusted_ev_pct,
        policy_version=config.proposed_policy_version,
    )


def _ensure_candidate_source_packet(
    *,
    config: PolicyAutoLoopConfig,
    research: dict[str, Any],
    candidate_source: dict[str, Any],
    candidate_source_path: Path,
    research_path: Path,
    materialize: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if _contract_ok(candidate_source, "swing_sim_candidate_source_only") and _candidate_source_selected_count(candidate_source) > 0:
        return candidate_source, {
            "status": "existing_candidate_source_used",
            "candidate_source_selected_count": _candidate_source_selected_count(candidate_source),
            "path": str(candidate_source_path) if candidate_source_path.exists() else None,
        }
    generated = build_candidate_source_report(
        bottom_report=research,
        source_path=research_path,
        config=_candidate_source_config(config),
        policy_auto_loop_diagnostics={
            "status": "deterministic_pre_policy_auto_loop_source_only_packet",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
        },
    )
    selected_count = _candidate_source_selected_count(generated)
    diagnostics = {
        "status": "generated_candidate_source_packet" if selected_count > 0 else "candidate_source_generation_empty",
        "previous_candidate_source_selected_count": _candidate_source_selected_count(candidate_source),
        "candidate_source_selected_count": selected_count,
        "path": str(candidate_source_path),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
    }
    if selected_count > 0 and materialize:
        write_candidate_source_report(generated, output_dir=candidate_source_path.parent)
        diagnostics["materialized"] = True
    else:
        diagnostics["materialized"] = False
    return generated, diagnostics


def _research_ev(research: dict[str, Any]) -> float:
    summary = research.get("summary") if isinstance(research.get("summary"), dict) else {}
    return _safe_float(summary.get("top_primary_source_quality_adjusted_ev_pct"))


def _bottom_bucket_ev(ev_report: dict[str, Any]) -> dict[str, Any]:
    aggregates = ev_report.get("aggregates") if isinstance(ev_report.get("aggregates"), dict) else {}
    candidates: list[dict[str, Any]] = []
    for axis, key in (
        ("volatility_bucket", "bottom_rebound"),
        ("selection_arm", "BOTTOM_REBOUND_SOURCE_ONLY"),
    ):
        for item in aggregates.get(axis) or []:
            if isinstance(item, dict) and str(item.get(axis) or "") == key:
                candidates.append({"axis": axis, **item})
    if not candidates:
        return {}
    return max(candidates, key=lambda item: (_safe_float(item.get("source_quality_adjusted_ev_pct")), _safe_int(item.get("sample_count"))))


def _candidate_source_ev(candidate_source: dict[str, Any]) -> float | None:
    if _candidate_source_selected_count(candidate_source) <= 0:
        return None
    rows = candidate_source.get("candidate_rows") if isinstance(candidate_source.get("candidate_rows"), list) else []
    values = [_safe_float(row.get("source_quality_adjusted_ev_pct")) for row in rows if isinstance(row, dict)]
    if values:
        return max(values)
    source_report = candidate_source.get("source_report") if isinstance(candidate_source.get("source_report"), dict) else {}
    if source_report.get("primary_adjusted_ev_pct") is not None:
        return _safe_float(source_report.get("primary_adjusted_ev_pct"))
    return None


def _research_sample_count(research: dict[str, Any]) -> int:
    summary = research.get("summary") if isinstance(research.get("summary"), dict) else {}
    portfolio = research.get("portfolio_backtest") if isinstance(research.get("portfolio_backtest"), dict) else {}
    portfolio_summary = portfolio.get("summary") if isinstance(portfolio.get("summary"), dict) else {}
    return max(
        _safe_int(summary.get("backtest_trade_count")),
        _safe_int(portfolio_summary.get("trade_count")),
        _safe_int(summary.get("signal_rows")),
    )


def _build_context(
    *,
    config: PolicyAutoLoopConfig,
    research: dict[str, Any],
    candidate_source: dict[str, Any],
    ev_report: dict[str, Any],
    source_paths: dict[str, Path],
) -> dict[str, Any]:
    bucket = _bottom_bucket_ev(ev_report)
    research_ev = _research_ev(research)
    bucket_ev = _safe_float(bucket.get("source_quality_adjusted_ev_pct"))
    candidate_source_ev = _candidate_source_ev(candidate_source)
    has_sim_bucket = bool(bucket)
    baseline_ev = research_ev if has_sim_bucket else 0.0
    candidate_ev = bucket_ev if has_sim_bucket else candidate_source_ev if candidate_source_ev is not None else research_ev
    absolute_improvement = candidate_ev - baseline_ev
    relative_improvement = (
        absolute_improvement / abs(baseline_ev)
        if abs(baseline_ev) >= 1e-9
        else (1.0 if absolute_improvement > 0 else 0.0)
    )
    return {
        "date": _date_text(config.target_date),
        "review_authority": DECISION_AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "broker_order_forbidden": True,
        "forbidden_uses": FORBIDDEN_USES,
        "policy_contract": {
            "promotion_scope": "next_update_kospi_after_close_swing_sim_candidate_source_only",
            "promotion_rule": "approve if source-quality contracts pass and candidate EV is at least 1 percent better",
            "real_trading_authority": False,
        },
        "source_contracts": {
            "bottom_rebound_research": _contract_ok(research, "research_only"),
            "swing_strategy_discovery_ev": _contract_ok(ev_report, "swing_sim_exploration_only"),
        },
        "downstream_contracts": {
            "candidate_source": _contract_ok(candidate_source, "swing_sim_candidate_source_only"),
            "candidate_source_selected_count": _safe_int(
                (candidate_source.get("source_quality") or {}).get("selected_candidate_count")
                if isinstance(candidate_source.get("source_quality"), dict)
                else 0
            ),
        },
        "source_paths": {label: str(path) if path.exists() else None for label, path in source_paths.items()},
        "metrics": {
            "baseline_research_ev_pct": round(research_ev, 6),
            "baseline_policy_ev_pct": round(baseline_ev, 6),
            "candidate_sim_bucket_ev_pct": round(candidate_ev, 6),
            "source_quality_adjusted_ev_pct": round(candidate_ev, 6),
            "candidate_ev_evidence_source": (
                "swing_strategy_discovery_ev_bucket"
                if has_sim_bucket
                else "bottom_rebound_candidate_source_packet"
                if candidate_source_ev is not None
                else "bottom_rebound_research_backtest_bootstrap"
            ),
            "absolute_improvement_pct": round(absolute_improvement, 6),
            "relative_improvement": round(relative_improvement, 6),
            "sample_count": _safe_int(bucket.get("sample_count")) if has_sim_bucket else _research_sample_count(research),
            "ev_bucket": bucket,
        },
        "proposed_policy": {
            "policy_version": config.proposed_policy_version,
            "max_candidates": config.max_candidates,
            "min_backtest_rank_score": config.min_backtest_rank_score,
            "min_primary_adjusted_ev_pct": config.min_primary_adjusted_ev_pct,
            "include_bottom_rebound_source": True,
            "sim_auto_approved": True,
            "allowed_runtime_apply": False,
        },
    }


def _deterministic_ai_payload(context: dict[str, Any], config: PolicyAutoLoopConfig) -> dict[str, Any]:
    contracts = context.get("source_contracts") if isinstance(context.get("source_contracts"), dict) else {}
    metrics = context.get("metrics") if isinstance(context.get("metrics"), dict) else {}
    explicit_gaps = [name for name, ok in contracts.items() if ok is not True]
    sample_count = _safe_int(metrics.get("sample_count"))
    abs_imp = _safe_float(metrics.get("absolute_improvement_pct"))
    rel_imp = _safe_float(metrics.get("relative_improvement"))
    if sample_count < config.min_sample_count:
        explicit_gaps.append("sample_floor_not_met")
    promoted = not explicit_gaps and (
        rel_imp >= config.min_relative_improvement or abs_imp >= config.min_absolute_improvement_pct
    )
    return {
        "schema_version": 1,
        "interpretation": {
            "policy_edge_state": "candidate_policy_better" if promoted else "keep_current_policy",
            "evidence": [
                f"relative_improvement={rel_imp}",
                f"absolute_improvement_pct={abs_imp}",
                f"sample_count={sample_count}",
            ],
        },
        "audit": {
            "status": "pass" if not explicit_gaps else "correction_required",
            "explicit_gaps": explicit_gaps,
            "forbidden_use_violations": [],
            "runtime_authority_preserved": True,
        },
        "final_conclusion": {
            "classification_state": "sim_auto_approved" if promoted else "source_only_keep_collecting",
            "promote_policy": promoted,
            "reason": "Candidate policy is at least 1 percent better and remains sim-only."
            if promoted
            else "Candidate policy did not pass improvement, sample, or source-quality gates.",
        },
    }


def _ai_instructions() -> str:
    return (
        "You are a Tier-2 swing simulation policy reviewer.\n"
        "Use first interpretation, second audit, and final conclusion.\n"
        "Auto-approve only source-only swing sim candidate-source policy updates when the candidate policy is at "
        "least 1 percent better by source_quality_adjusted_ev_pct and source-quality contracts pass.\n"
        "Never approve broker orders, real canaries, runtime env, threshold mutation, provider changes, bot restart, "
        "recommendation_history replacement, or live entry relaxation.\n"
        "If there is no explicit source-quality or forbidden-use gap, small/ambiguous concerns must not block "
        "sim-only auto approval when the numeric 1 percent improvement rule passes.\n"
        "Return strict JSON for swing_bottom_rebound_policy_ai_review_v1 with these exact top-level keys: "
        "schema_version, interpretation, audit, final_conclusion.\n"
        "Use audit.status in pass, correction_required, insufficient_context. "
        "Use final_conclusion.classification_state in sim_auto_approved, source_only_keep_collecting, code_patch_required."
    )


def _call_openai_review(context: dict[str, Any], *, model: str) -> tuple[Any | None, dict[str, Any]]:
    try:
        from openai import OpenAI, RateLimitError
        from src.engine.ai_response_contracts import build_openai_response_text_format
        from src.engine.daily_threshold_cycle_report import _extract_openai_response_text, _load_threshold_ai_openai_keys
    except Exception as exc:
        return None, {"provider": "openai", "status": "unavailable", "reason": f"openai import failed: {exc}"}
    keys = _load_threshold_ai_openai_keys()
    if not keys:
        return None, {"provider": "openai", "status": "unavailable", "reason": "OPENAI_API_KEY not configured", "model": model}
    prompt = json.dumps(context, ensure_ascii=True, indent=2, default=str)
    errors: list[dict[str, str]] = []
    for attempt_index, (key_name, api_key) in enumerate(keys, start=1):
        try:
            response = OpenAI(api_key=api_key).responses.create(
                model=model,
                instructions=_ai_instructions(),
                input=prompt,
                text={"format": build_openai_response_text_format(AI_REVIEW_SCHEMA_NAME), "verbosity": "low"},
                reasoning={"effort": "medium"},
                store=False,
                timeout=120,
                metadata={
                    "endpoint_name": REPORT_TYPE,
                    "schema_name": AI_REVIEW_SCHEMA_NAME,
                    "report_type": REPORT_TYPE,
                },
            )
            raw_text = _extract_openai_response_text(response)
            usage = getattr(response, "usage", None)
            return raw_text, {
                "provider": "openai",
                "status": "success",
                "model": model,
                "model_tier": "tier2",
                "key_name": key_name,
                "attempt_index": attempt_index,
                "input_context_hash": _text_hash(context),
                "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
                "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
            }
        except RateLimitError as exc:
            errors.append({"key_name": key_name, "error": f"rate_limit:{exc}"})
        except Exception as exc:
            errors.append({"key_name": key_name, "error": str(exc)})
    return None, {"provider": "openai", "status": "unavailable", "reason": "all OpenAI attempts failed", "model": model, "errors": errors[-3:]}


def _normalize_ai_payload_shape(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    normalized = dict(payload)
    notes: list[str] = []
    if normalized.get("schema_version") == "1":
        normalized["schema_version"] = 1
        notes.append("normalized_schema_version_string")
    if not isinstance(normalized.get("final_conclusion"), dict):
        conclusions = normalized.get("final_conclusions")
        if isinstance(conclusions, list) and conclusions and isinstance(conclusions[0], dict):
            first = conclusions[0]
            state = first.get("classification_state") or first.get("final_classification_state") or first.get("final_state")
            decision = str(first.get("final_decision") or first.get("decision") or "").lower()
            normalized["final_conclusion"] = {
                "classification_state": state,
                "promote_policy": bool(first.get("promote_policy"))
                or state == "sim_auto_approved"
                or decision in {"approve", "promote"},
                "reason": first.get("reason") or first.get("correction_reason") or "",
            }
            notes.append("normalized_final_conclusions_array")
    audit = normalized.get("audit") if isinstance(normalized.get("audit"), dict) else {}
    if audit and str(audit.get("status") or "") == "passed":
        audit = {**audit, "status": "pass"}
        normalized["audit"] = audit
        notes.append("normalized_audit_status_passed")
    return normalized, notes


def _parse_ai_payload(raw: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw in (None, ""):
        return "missing", {}, ["ai_review_response_missing"]
    if isinstance(raw, dict):
        payload = raw
    else:
        try:
            payload = json.loads(str(raw))
        except Exception as exc:
            return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    payload, normalization_notes = _normalize_ai_payload_shape(payload)
    warnings: list[str] = []
    if payload.get("schema_version") != 1:
        warnings.append("ai_review_schema_version_invalid")
    if not isinstance(payload.get("interpretation"), dict):
        warnings.append("ai_review_interpretation_missing")
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    if str(audit.get("status") or "") not in {"pass", "correction_required", "insufficient_context"}:
        warnings.append("ai_review_audit_status_invalid")
    conclusion = payload.get("final_conclusion") if isinstance(payload.get("final_conclusion"), dict) else {}
    if str(conclusion.get("classification_state") or "") not in {"sim_auto_approved", "source_only_keep_collecting", "code_patch_required"}:
        warnings.append("ai_review_final_classification_invalid")
    return ("parse_rejected", payload, warnings + normalization_notes) if warnings else ("parsed", payload, normalization_notes)


def _normalize_conclusion(payload: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    deterministic = _deterministic_ai_payload(context, PolicyAutoLoopConfig(target_date=context.get("date")))
    conclusion = payload.get("final_conclusion") if isinstance(payload.get("final_conclusion"), dict) else {}
    audit = payload.get("audit") if isinstance(payload.get("audit"), dict) else {}
    forbidden = audit.get("forbidden_use_violations") if isinstance(audit.get("forbidden_use_violations"), list) else []
    gaps = audit.get("explicit_gaps") if isinstance(audit.get("explicit_gaps"), list) else []
    promote = bool(conclusion.get("promote_policy"))
    if forbidden or gaps:
        promote = False
    state = "sim_auto_approved" if promote else str(conclusion.get("classification_state") or "source_only_keep_collecting")
    if state not in {"sim_auto_approved", "source_only_keep_collecting", "code_patch_required"}:
        state = deterministic["final_conclusion"]["classification_state"]
    return {
        "classification_state": state,
        "promote_policy": state == "sim_auto_approved",
        "reason": str(conclusion.get("reason") or deterministic["final_conclusion"]["reason"]),
        "explicit_gaps": [str(item) for item in gaps],
        "forbidden_use_violations": [str(item) for item in forbidden],
    }


def _deterministic_gate_gaps(context: dict[str, Any], config: PolicyAutoLoopConfig) -> list[str]:
    contracts = context.get("source_contracts") if isinstance(context.get("source_contracts"), dict) else {}
    metrics = context.get("metrics") if isinstance(context.get("metrics"), dict) else {}
    gaps = [f"{name}_contract_failed" for name, ok in contracts.items() if ok is not True]
    sample_count = _safe_int(metrics.get("sample_count"))
    abs_imp = _safe_float(metrics.get("absolute_improvement_pct"))
    rel_imp = _safe_float(metrics.get("relative_improvement"))
    if sample_count < config.min_sample_count:
        gaps.append("sample_floor_not_met")
    if rel_imp < config.min_relative_improvement and abs_imp < config.min_absolute_improvement_pct:
        gaps.append("one_percent_improvement_not_met")
    return gaps


def build_policy_auto_loop_report(
    target_date: str,
    *,
    config: PolicyAutoLoopConfig | None = None,
    provider: str | None = None,
    ai_raw_response: Any | None = None,
    source_paths: dict[str, Path] | None = None,
    materialize_generated_candidate_source: bool = False,
) -> dict[str, Any]:
    config = config or PolicyAutoLoopConfig(target_date=target_date)
    date_key = _date_text(target_date)
    paths = source_paths or default_source_paths(date_key)
    research = _load_json(paths["bottom_rebound_research"])
    candidate_source = _load_json(paths["candidate_source"])
    ev_report = _load_json(paths["swing_strategy_discovery_ev"])
    candidate_source, candidate_source_generation = _ensure_candidate_source_packet(
        config=config,
        research=research,
        candidate_source=candidate_source,
        candidate_source_path=paths["candidate_source"],
        research_path=paths["bottom_rebound_research"],
        materialize=materialize_generated_candidate_source,
    )
    context = _build_context(
        config=config,
        research=research,
        candidate_source=candidate_source,
        ev_report=ev_report,
        source_paths=paths,
    )
    resolved_provider = str(provider if provider is not None else os.getenv("KORSTOCKSCAN_BOTTOM_REBOUND_POLICY_AI_REVIEW_PROVIDER", "openai")).lower()
    provider_status = {
        "provider": resolved_provider,
        "status": "disabled" if resolved_provider in {"none", "off", "false", "0"} else "not_called",
        "model": AI_REVIEW_MODEL if resolved_provider not in {"none", "off", "false", "0"} else None,
        "model_tier": "tier2" if resolved_provider not in {"none", "off", "false", "0"} else "deterministic_fallback",
    }
    raw_response = ai_raw_response
    if raw_response is None and resolved_provider == "openai":
        raw_response, provider_status = _call_openai_review(context, model=AI_REVIEW_MODEL)
    ai_status, ai_payload, ai_warnings = _parse_ai_payload(raw_response)
    fallback_used = False
    if ai_status != "parsed":
        fallback_used = True
        ai_payload = _deterministic_ai_payload(context, config)
        ai_status = "disabled_deterministic_review" if resolved_provider in {"none", "off", "false", "0"} else "unavailable_deterministic_review"
    conclusion = _normalize_conclusion(ai_payload, context)
    deterministic_gaps = _deterministic_gate_gaps(context, config)
    if deterministic_gaps:
        conclusion["classification_state"] = "source_only_keep_collecting"
        conclusion["promote_policy"] = False
        conclusion["explicit_gaps"] = sorted(set(conclusion.get("explicit_gaps") or []) | set(deterministic_gaps))
    if ai_status in {"unavailable_deterministic_review", "disabled_deterministic_review"}:
        conclusion["classification_state"] = "source_only_keep_collecting"
        conclusion["promote_policy"] = False
        gap = "tier2_ai_review_disabled" if ai_status == "disabled_deterministic_review" else "tier2_ai_review_unavailable"
        conclusion["explicit_gaps"] = sorted(set(conclusion.get("explicit_gaps") or []) | {gap})
    approved_policy = context["proposed_policy"] if conclusion["promote_policy"] else None
    warnings = list(ai_warnings)
    if conclusion.get("explicit_gaps"):
        warnings.extend(f"explicit_gap:{item}" for item in conclusion["explicit_gaps"])
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "date": date_key,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "runtime_effect": False,
        "source_only": True,
        "decision_authority": DECISION_AUTHORITY,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "sim_policy_auto_approval_source",
            "decision_authority": DECISION_AUTHORITY,
            "window_policy": "after_update_kospi_db_refresh_backtest_and_swing_sim_feedback",
            "sample_floor": config.min_sample_count,
            "primary_decision_metric": "source_quality_adjusted_ev_pct",
            "source_quality_gate": "research_candidate_source_ev_contracts_and_tier2_ai_audit",
            "forbidden_uses": FORBIDDEN_USES,
        },
        "config": asdict(config),
        "source_context_hash": _text_hash(context),
        "source_context": context,
        "candidate_source_generation": candidate_source_generation,
        "ai_tier2_review": {
            "provider": resolved_provider,
            "status": ai_status,
            "model": provider_status.get("model"),
            "model_tier": provider_status.get("model_tier", "tier2"),
            "provider_status": provider_status,
            "fallback_used": fallback_used,
            "payload": ai_payload,
            "warnings": ai_warnings,
        },
        "final_conclusion": conclusion,
        "sim_auto_approved_policy": approved_policy,
        "downstream_contract": {
            "auto_consumer": "swing_bottom_rebound_candidate_source",
            "next_runner": "swing_strategy_discovery_sim --include-bottom-rebound-source",
            "db_write_allowed": "swing_strategy_discovery_sim_virtual_candidate_arm_rows_only",
            "runtime_hook_performed": False,
            "allowed_runtime_apply": False,
            "broker_order_forbidden": True,
        },
        "warnings": warnings,
    }


def render_markdown(report: dict[str, Any]) -> str:
    metrics = ((report.get("source_context") or {}).get("metrics") or {}) if isinstance(report.get("source_context"), dict) else {}
    conclusion = report.get("final_conclusion") if isinstance(report.get("final_conclusion"), dict) else {}
    lines = [
        f"# Swing Bottom Rebound Policy Auto Loop - {report.get('date')}",
        "",
        f"- generated_at: `{report.get('generated_at')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- broker_order_forbidden: `{report.get('broker_order_forbidden')}`",
        f"- allowed_runtime_apply: `{report.get('allowed_runtime_apply')}`",
        f"- ai_tier2_status: `{(report.get('ai_tier2_review') or {}).get('status')}`",
        f"- classification_state: `{conclusion.get('classification_state')}`",
        f"- promote_policy: `{conclusion.get('promote_policy')}`",
        f"- baseline_research_ev_pct: `{metrics.get('baseline_research_ev_pct')}`",
        f"- candidate_sim_bucket_ev_pct: `{metrics.get('candidate_sim_bucket_ev_pct')}`",
        f"- relative_improvement: `{metrics.get('relative_improvement')}`",
        f"- sample_count: `{metrics.get('sample_count')}`",
        f"- warnings: `{report.get('warnings') or []}`",
        "",
        "## Contract",
        "",
        "- A 1 percent improvement can auto-approve only the next sim candidate-source policy.",
        "- This does not approve live orders, real canaries, runtime env, thresholds, providers, or bot actions.",
        "- If Tier-2 AI is unavailable, the report keeps collecting instead of promoting.",
        "",
    ]
    return "\n".join(lines)


def report_paths(target_date: str, output_dir: Path = REPORT_DIR) -> tuple[Path, Path]:
    base = output_dir / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def write_policy_auto_loop_report(report: dict[str, Any], *, output_dir: Path = REPORT_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(_date_text(report.get("date")), output_dir)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    if output_dir == REPORT_DIR:
        refresh_swing_sim_auto_approval(_date_text(report.get("date")), bottom_rebound_policy_report=report)
    return {"json": json_path, "md": md_path}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--provider", default=None)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    report = build_policy_auto_loop_report(
        args.date,
        provider=args.provider,
        materialize_generated_candidate_source=not args.no_write,
    )
    if args.no_write:
        print(json.dumps({"date": report["date"], "final_conclusion": report["final_conclusion"], "warnings": report["warnings"]}, ensure_ascii=False))
        return
    paths = write_policy_auto_loop_report(report, output_dir=args.output_dir)
    print(f"[DONE] swing_bottom_rebound_policy_auto_loop json={paths['json']} md={paths['md']}")


if __name__ == "__main__":
    main()
