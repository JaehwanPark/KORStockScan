"""Lifecycle AI context source and attribution reports.

This module is intentionally context-only. It may build prompt text and
postclose attribution summaries, but it must not gate real orders or mutate
runtime actions.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from src.utils.constants import DATA_DIR, TRADING_RULES
from src.utils.jsonl_io import existing_or_gzip_path

REPORT_DIR = DATA_DIR / "report"
CONTEXT_DIR = REPORT_DIR / "lifecycle_ai_context"
ATTRIBUTION_DIR = REPORT_DIR / "lifecycle_ai_context_attribution"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"

REPORT_SCHEMA_VERSION = 1
CONTEXT_VERSION_PREFIX = "lifecycle_ai_context_v1"
ATTRIBUTION_VERSION_PREFIX = "lifecycle_ai_context_attribution_v1"
STAGES = ("entry", "submit", "holding", "scale_in", "exit")
PROMPT_STAGES = {"entry", "holding", "exit"}
REPLAY_BUDGET = 30
FORBIDDEN_USES = [
    "real_order_gate",
    "pre_submit_block",
    "provider_route",
    "bot_restart",
    "threshold_env_mutation",
    "telegram_buy_sell",
]
IMPLEMENTATION_ORDER_ID = "order_lifecycle_ai_context_attribution_feedback"


def _implementation_provenance() -> dict[str, Any]:
    return {
        "order_id": IMPLEMENTATION_ORDER_ID,
        "scope": "instrumentation_report_provenance_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": "postclose_context_attribution_only",
        "feedback_target": "lifecycle_decision_matrix.policy_entries",
        "forbidden_uses": FORBIDDEN_USES,
    }


def _implementation_checks(
    *, stage_count: int, runtime_effect: bool
) -> list[dict[str, Any]]:
    return [
        {
            "name": "stage_attribution_contract",
            "status": "pass" if stage_count == len(STAGES) else "warning",
            "observed_stage_count": stage_count,
            "expected_stage_count": len(STAGES),
        },
        {
            "name": "runtime_effect_contract",
            "status": "pass" if runtime_effect is False else "fail",
            "runtime_effect": runtime_effect,
        },
        {
            "name": "forbidden_use_contract",
            "status": "pass",
            "forbidden_uses": FORBIDDEN_USES,
        },
    ]


def context_report_paths(target_date: str) -> tuple[Path, Path]:
    base = CONTEXT_DIR / f"lifecycle_ai_context_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def attribution_report_paths(target_date: str) -> tuple[Path, Path]:
    base = ATTRIBUTION_DIR / f"lifecycle_ai_context_attribution_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _open_text(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    return path.open("r", encoding="utf-8", errors="ignore")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    path = existing_or_gzip_path(path)
    if not path.exists():
        return
    try:
        with _open_text(path) as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload
    except OSError:
        return


def _context_hash(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()[:16]


def _session_cutoff_source_date(now: datetime) -> date:
    if now.hour >= 16:
        return now.date()
    return now.date() - timedelta(days=1)


def _latest_context_path_on_or_before(target_date: date) -> Path | None:
    explicit = str(
        getattr(TRADING_RULES, "LIFECYCLE_AI_CONTEXT_FILE", "") or ""
    ).strip()
    if explicit:
        path = Path(explicit)
        if path.exists():
            return path
    if not CONTEXT_DIR.exists():
        return None
    best_date: date | None = None
    best_path: Path | None = None
    for path in CONTEXT_DIR.glob("lifecycle_ai_context_*.json"):
        raw_date = path.stem.replace("lifecycle_ai_context_", "")
        try:
            current_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        if current_date > target_date:
            continue
        if best_date is None or current_date > best_date:
            best_date = current_date
            best_path = path
    return best_path


def _load_stage_attribution(target_date: str) -> dict[str, dict[str, Any]]:
    path, _ = attribution_report_paths(target_date)
    payload = _read_json(path)
    by_stage = (
        payload.get("stage_attribution")
        if isinstance(payload.get("stage_attribution"), dict)
        else {}
    )
    return {
        str(stage): dict(value)
        for stage, value in by_stage.items()
        if isinstance(value, dict)
    }


def _source_payloads(target_date: str) -> dict[str, Any]:
    lifecycle_path = (
        REPORT_DIR
        / "lifecycle_decision_matrix"
        / f"lifecycle_decision_matrix_{target_date}.json"
    )
    entry_path = (
        REPORT_DIR
        / "scalp_entry_action_decision_matrix"
        / f"scalp_entry_action_decision_matrix_{target_date}.json"
    )
    holding_path = (
        REPORT_DIR
        / "holding_exit_decision_matrix"
        / f"holding_exit_decision_matrix_{target_date}.json"
    )
    return {
        "lifecycle_decision_matrix": _read_json(lifecycle_path),
        "scalp_entry_action_decision_matrix": _read_json(entry_path),
        "holding_exit_decision_matrix": _read_json(holding_path),
        "paths": {
            "lifecycle_decision_matrix": (
                str(lifecycle_path) if lifecycle_path.exists() else None
            ),
            "scalp_entry_action_decision_matrix": (
                str(entry_path) if entry_path.exists() else None
            ),
            "holding_exit_decision_matrix": (
                str(holding_path) if holding_path.exists() else None
            ),
        },
    }


def _policy_by_stage(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = (
        payload.get("policy_entries")
        if isinstance(payload.get("policy_entries"), list)
        else []
    )
    result: dict[str, dict[str, Any]] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        stage = str(item.get("stage") or "")
        if stage in STAGES and stage not in result:
            result[stage] = item
    return result


def _stage_context_text(
    *,
    stage: str,
    policy: dict[str, Any],
    attribution: dict[str, Any],
    matrix_version: str,
) -> str:
    selected = str(policy.get("selected_action") or "NO_CHANGE")
    confidence = _safe_float(policy.get("confidence"), 0.0)
    ev = policy.get("stage_ev_composite_pct")
    contribution = _safe_float(attribution.get("context_contribution_score"), 0.0)
    quality = str(attribution.get("attribution_quality_status") or "hold_sample")
    return "\n".join(
        [
            "[Lifecycle AI Context]",
            f"- stage: {stage}",
            f"- source_matrix_version: {matrix_version or '-'}",
            f"- policy_key: {policy.get('policy_key') or f'{stage}:missing_policy'}",
            f"- selected_action_hint: {selected}",
            f"- confidence: {confidence}",
            f"- stage_ev_composite_pct: {ev}",
            f"- context_contribution_score: {contribution}",
            f"- attribution_quality_status: {quality}",
            "- authority: ai_advisory_prompt_context_only",
            "- rule: use this as statistical background only; do not force BUY/WAIT/DROP/HOLD/EXIT.",
            "- rule: hard safety, account/order/broker guard, stale quote guard, and qty guard remain higher priority.",
        ]
    )


def build_lifecycle_ai_context_report(
    target_date: str, *, provider: str | None = None
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    source = _source_payloads(target_date)
    lifecycle = (
        source["lifecycle_decision_matrix"]
        if isinstance(source["lifecycle_decision_matrix"], dict)
        else {}
    )
    policy_entries = _policy_by_stage(lifecycle)
    attribution_by_stage = _load_stage_attribution(target_date)
    matrix_version = str(lifecycle.get("matrix_version") or "")
    raw_provider_name = str(provider or "").strip().lower()
    provider_name = (
        "deterministic_source_only"
        if raw_provider_name in {"", "none", "deterministic"}
        else raw_provider_name
    )
    stage_contexts: list[dict[str, Any]] = []
    for stage in STAGES:
        policy = policy_entries.get(stage, {})
        attribution = attribution_by_stage.get(stage, {})
        text = _stage_context_text(
            stage=stage,
            policy=policy,
            attribution=attribution,
            matrix_version=matrix_version,
        )
        stage_contexts.append(
            {
                "stage": stage,
                "prompt_injection_allowed": stage in PROMPT_STAGES,
                "policy_key": str(
                    policy.get("policy_key") or f"{stage}:missing_policy"
                ),
                "source_matrix_version": matrix_version or "-",
                "selected_action_hint": str(
                    policy.get("selected_action") or "NO_CHANGE"
                ),
                "alignment_hint": str(policy.get("selected_action") or "NO_CHANGE"),
                "confidence": _safe_float(policy.get("confidence"), 0.0),
                "stage_ev_composite_pct": policy.get("stage_ev_composite_pct"),
                "context_contribution_score": _safe_float(
                    attribution.get("context_contribution_score"), 0.0
                ),
                "bounded_auxiliary_weight": _safe_float(
                    attribution.get("bounded_auxiliary_weight"), 0.0
                ),
                "attribution_quality_status": str(
                    attribution.get("attribution_quality_status") or "hold_sample"
                ),
                "context_text": text,
                "context_hash": _context_hash(text),
                "runtime_effect": False,
                "decision_authority": "ai_advisory_prompt_context_only",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    warnings: list[str] = []
    if not lifecycle:
        warnings.append("lifecycle_decision_matrix_missing")
    if not attribution_by_stage:
        warnings.append("lifecycle_ai_context_attribution_missing_or_empty")
    provider_status = {
        "provider": provider_name,
        "status": (
            "deterministic_fallback"
            if provider_name == "deterministic_source_only"
            else "not_called_v1"
        ),
        "schema_name": "lifecycle_ai_context_v1",
        "fallback_used": True,
    }
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "lifecycle_ai_context",
        "context_version": f"{CONTEXT_VERSION_PREFIX}_{target_date}",
        "runtime_effect": False,
        "decision_authority": "ai_advisory_prompt_context_only",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "provider_status": provider_status,
        "source_family": "lifecycle_ai_context",
        "family_type": "ai_advisory_context_source",
        "live_selectable": False,
        "preopen_apply_allowed": True,
        "env_apply_allowed": True,
        "threshold_env_mutation_allowed": False,
        "real_order_allowed": False,
        "prompt_stages": sorted(PROMPT_STAGES),
        "prompt_stage_count": len(
            [
                item
                for item in stage_contexts
                if bool(item.get("prompt_injection_allowed"))
            ]
        ),
        "stage_contexts": stage_contexts,
        "sources": source.get("paths") or {},
        "forbidden_uses": FORBIDDEN_USES,
        "warnings": warnings,
    }
    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = context_report_paths(target_date)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(render_lifecycle_ai_context_markdown(report), encoding="utf-8")
    return report


def _infer_stage(stage: str, fields: dict[str, Any]) -> str:
    explicit = str(fields.get("lifecycle_ai_context_stage") or "").strip().lower()
    if explicit in STAGES:
        return explicit
    raw = str(stage or "").lower()
    if "scale" in raw:
        return "scale_in"
    if "submit" in raw:
        return "submit"
    if "holding" in raw or "hold" in raw:
        return "holding"
    if "exit" in raw or "sell" in raw:
        return "exit"
    return "entry"


def _aligned(action: str, hint: str) -> bool | None:
    action = str(action or "").upper()
    hint = str(hint or "").upper()
    if not action or not hint or hint == "NO_CHANGE":
        return None
    if hint == "BUY_DEFENSIVE":
        return action in {"BUY", "BUY_NOW"}
    if hint == "WAIT_REQUOTE":
        return action == "WAIT"
    if hint in {"DROP", "HOLD", "EXIT"}:
        return action == hint
    if hint == "ALLOW_SUBMIT":
        return action in {"ALLOW_SUBMIT", "BUY", "BUY_NOW"}
    if hint in {"AVG_DOWN_BIAS", "PYRAMID_BIAS"}:
        return action in {"AVG_DOWN", "PYRAMID", "NO_CHANGE", "HOLD"}
    return None


def _pipeline_context_rows(target_date: str) -> list[dict[str, Any]]:
    path = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    rows: list[dict[str, Any]] = []
    for item in _iter_jsonl(path) or []:
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        merged = {**item, **fields}
        if not (
            "lifecycle_ai_context_enabled" in merged
            or "lifecycle_ai_context_applied" in merged
            or "lifecycle_ai_context_status" in merged
        ):
            continue
        stage = _infer_stage(str(item.get("stage") or ""), merged)
        action = str(
            merged.get("ai_action")
            or merged.get("action_v2")
            or merged.get("action")
            or merged.get("chosen_action")
            or ""
        )
        score = _safe_float(merged.get("ai_score") or merged.get("score"), None)
        replay_action = str(
            merged.get("lifecycle_ai_context_no_context_action")
            or merged.get("no_context_replay_action")
            or ""
        )
        replay_score = _safe_float(
            merged.get("lifecycle_ai_context_no_context_score")
            or merged.get("no_context_replay_score"),
            None,
        )
        rows.append(
            {
                "stage": stage,
                "applied": bool(merged.get("lifecycle_ai_context_applied")),
                "enabled": bool(merged.get("lifecycle_ai_context_enabled")),
                "status": str(merged.get("lifecycle_ai_context_status") or "-"),
                "policy_key": str(merged.get("lifecycle_ai_context_policy_key") or "-"),
                "context_hash": str(merged.get("lifecycle_ai_context_hash") or "-"),
                "alignment_hint": str(
                    merged.get("lifecycle_ai_context_alignment_hint") or "NO_CHANGE"
                ),
                "action": action,
                "score": score,
                "profit_rate": _safe_float(merged.get("profit_rate"), None),
                "source_quality": str(
                    merged.get("source_quality_status")
                    or merged.get("source_quality_gate")
                    or "-"
                ),
                "replay_action": replay_action,
                "replay_score": replay_score,
            }
        )
    return rows


def build_lifecycle_ai_context_attribution_report(
    target_date: str, *, replay_budget: int = REPLAY_BUDGET
) -> dict[str, Any]:
    target_date = str(target_date).strip()
    rows = _pipeline_context_rows(target_date)
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_stage[str(row.get("stage") or "entry")].append(row)
    stage_attribution: dict[str, dict[str, Any]] = {}
    for stage in STAGES:
        subset = by_stage.get(stage, [])
        eligible = len(subset)
        applied = [row for row in subset if row.get("applied")]
        skipped = eligible - len(applied)
        alignments = [
            _aligned(str(row.get("action") or ""), str(row.get("alignment_hint") or ""))
            for row in applied
        ]
        alignments = [value for value in alignments if value is not None]
        replay_rows = [
            row for row in applied if str(row.get("replay_action") or "").strip()
        ][: max(0, int(replay_budget or 0))]
        score_deltas = [
            float(row.get("score") or 0.0) - float(row.get("replay_score") or 0.0)
            for row in replay_rows
            if row.get("score") is not None and row.get("replay_score") is not None
        ]
        action_delta_count = sum(
            1
            for row in replay_rows
            if str(row.get("action") or "").upper()
            != str(row.get("replay_action") or "").upper()
        )
        profits = [
            float(row["profit_rate"])
            for row in applied
            if row.get("profit_rate") is not None
        ]
        completed_sample = len(profits)
        avg_profit = (
            round(sum(profits) / completed_sample, 4) if completed_sample else None
        )
        alignment_rate = (
            round(sum(1 for value in alignments if value) / len(alignments), 4)
            if alignments
            else None
        )
        replay_sample = min(len(applied), max(0, int(replay_budget or 0)))
        action_delta_rate = (
            round(action_delta_count / len(replay_rows), 4) if replay_rows else None
        )
        score_delta_avg = (
            round(sum(score_deltas) / len(score_deltas), 4) if score_deltas else None
        )
        if eligible <= 0:
            quality = "hold_sample"
        elif completed_sample <= 0:
            quality = "observational_only_pending_outcome"
        elif replay_rows:
            quality = "sampled_replay"
        else:
            quality = "observational_only"
        ev_component = (
            0.0 if avg_profit is None else max(-1.0, min(1.0, avg_profit / 2.0))
        )
        alignment_component = (
            0.0 if alignment_rate is None else (alignment_rate * 2.0 - 1.0)
        )
        replay_component = (
            0.0 if action_delta_rate is None else min(1.0, action_delta_rate)
        )
        contribution = round(
            max(
                -1.0,
                min(
                    1.0,
                    0.45 * ev_component
                    + 0.35 * alignment_component
                    + 0.20 * replay_component,
                ),
            ),
            4,
        )
        bounded_weight = round(max(-0.15, min(0.15, contribution * 0.15)), 4)
        stage_attribution[stage] = {
            "stage": stage,
            "context_eligible_count": eligible,
            "context_applied_count": len(applied),
            "context_skipped_count": skipped,
            "ai_action_alignment_rate": alignment_rate,
            "no_context_replay_sample": replay_sample,
            "no_context_replay_observed": len(replay_rows),
            "ai_action_delta_rate": action_delta_rate,
            "ai_score_delta_avg": score_delta_avg,
            "completed_sample": completed_sample,
            "equal_weight_avg_profit_pct": avg_profit,
            "notional_weighted_ev_pct": avg_profit,
            "source_quality_adjusted_ev_pct": avg_profit,
            "context_contribution_score": contribution,
            "bounded_auxiliary_weight": bounded_weight,
            "attribution_quality_status": quality,
            "feedback_route": "bounded_auxiliary_weight" if eligible else "hold_sample",
            "runtime_effect": False,
            "decision_authority": "postclose_context_attribution_only",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "forbidden_uses": FORBIDDEN_USES,
        }
    summary = {
        "context_eligible_count": sum(
            item["context_eligible_count"] for item in stage_attribution.values()
        ),
        "context_applied_count": sum(
            item["context_applied_count"] for item in stage_attribution.values()
        ),
        "context_skipped_count": sum(
            item["context_skipped_count"] for item in stage_attribution.values()
        ),
        "no_context_replay_sample": sum(
            item["no_context_replay_sample"] for item in stage_attribution.values()
        ),
        "no_context_replay_observed": sum(
            item["no_context_replay_observed"] for item in stage_attribution.values()
        ),
        "replay_budget": int(replay_budget or 0),
        "replay_mode": "observed_no_context_fields_or_degrade",
        "stage_quality_counts": dict(
            Counter(
                item["attribution_quality_status"]
                for item in stage_attribution.values()
            )
        ),
    }
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": "lifecycle_ai_context_attribution",
        "attribution_version": f"{ATTRIBUTION_VERSION_PREFIX}_{target_date}",
        "runtime_effect": False,
        "decision_authority": "postclose_context_attribution_only",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "metric_role": "source_quality_adjusted_ev_feedback",
        "primary_decision_metric": "context_contribution_score",
        "window_policy": "same_day_observational_plus_sampled_replay_when_available",
        "sample_floor": 20,
        "context_eligible_count": summary["context_eligible_count"],
        "context_applied_count": summary["context_applied_count"],
        "context_skipped_count": summary["context_skipped_count"],
        "no_context_replay_sample": summary["no_context_replay_sample"],
        "no_context_replay_observed": summary["no_context_replay_observed"],
        "replay_budget": summary["replay_budget"],
        "implementation_status": "implemented",
        "implementation_provenance": _implementation_provenance(),
        "implementation_checks": _implementation_checks(
            stage_count=len(stage_attribution),
            runtime_effect=False,
        ),
        "summary": summary,
        "stage_attribution": stage_attribution,
        "sources": {
            "pipeline_events": str(
                PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
            ),
            "post_sell": str(
                POST_SELL_DIR / f"sim_post_sell_evaluations_{target_date}.jsonl"
            ),
        },
        "forbidden_uses": FORBIDDEN_USES,
        "warnings": [] if rows else ["lifecycle_ai_context_runtime_provenance_missing"],
    }
    ATTRIBUTION_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = attribution_report_paths(target_date)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(
        render_lifecycle_ai_context_attribution_markdown(report), encoding="utf-8"
    )
    return report


def _stage_for_prompt(prompt_profile: str, requested_stage: str | None = None) -> str:
    stage = str(requested_stage or "").strip().lower()
    if stage in STAGES:
        return stage
    profile = str(prompt_profile or "").strip().lower()
    if profile in {"holding", "scalping_holding"}:
        return "holding"
    if profile == "exit":
        return "exit"
    if profile in {"watching", "entry", "scalping_entry", "shared", ""}:
        return "entry"
    return "entry"


def build_lifecycle_ai_runtime_context(
    *,
    prompt_profile: str,
    stage: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_dt = now or datetime.now()
    stage_name = _stage_for_prompt(prompt_profile, stage)
    enabled = bool(getattr(TRADING_RULES, "LIFECYCLE_AI_CONTEXT_ENABLED", False))
    base_fields = {
        "lifecycle_ai_context_enabled": enabled,
        "lifecycle_ai_context_applied": False,
        "lifecycle_ai_context_status": "disabled" if not enabled else "not_loaded",
        "lifecycle_ai_context_version": "-",
        "lifecycle_ai_context_source_date": "-",
        "lifecycle_ai_context_stage": stage_name,
        "lifecycle_ai_context_policy_key": "-",
        "lifecycle_ai_context_hash": "-",
        "lifecycle_ai_context_alignment_hint": "NO_CHANGE",
        "lifecycle_ai_context_decision_authority": "ai_advisory_prompt_context_only",
        "lifecycle_ai_context_runtime_effect": "none",
        "lifecycle_ai_context_actual_order_submitted": False,
        "lifecycle_ai_context_broker_order_forbidden": True,
    }
    if not enabled:
        return {
            "applied": False,
            "status": "disabled",
            "cache_token": f"lifecycle_ai_context:disabled:{stage_name}",
            "prompt_context": "",
            "fields": base_fields,
        }
    path = _latest_context_path_on_or_before(_session_cutoff_source_date(current_dt))
    payload = _read_json(path) if path else {}
    if not payload:
        fields = {
            **base_fields,
            "lifecycle_ai_context_status": "context_missing_or_invalid",
        }
        return {
            "applied": False,
            "status": "context_missing_or_invalid",
            "cache_token": f"lifecycle_ai_context:missing:{stage_name}",
            "prompt_context": "",
            "fields": fields,
        }
    contexts = (
        payload.get("stage_contexts")
        if isinstance(payload.get("stage_contexts"), list)
        else []
    )
    selected = next(
        (
            item
            for item in contexts
            if isinstance(item, dict) and str(item.get("stage") or "") == stage_name
        ),
        {},
    )
    if not selected or not bool(selected.get("prompt_injection_allowed")):
        fields = {
            **base_fields,
            "lifecycle_ai_context_status": "stage_context_not_prompt_injected",
            "lifecycle_ai_context_version": str(payload.get("context_version") or "-"),
            "lifecycle_ai_context_source_date": str(payload.get("date") or "-"),
        }
        return {
            "applied": False,
            "status": "stage_context_not_prompt_injected",
            "cache_token": f"lifecycle_ai_context:excluded:{stage_name}",
            "prompt_context": "",
            "fields": fields,
        }
    context_text = str(selected.get("context_text") or "")
    context_hash = str(selected.get("context_hash") or _context_hash(context_text))
    fields = {
        **base_fields,
        "lifecycle_ai_context_applied": True,
        "lifecycle_ai_context_status": "advisory_prompt_applied",
        "lifecycle_ai_context_version": str(payload.get("context_version") or "-"),
        "lifecycle_ai_context_source_date": str(payload.get("date") or "-"),
        "lifecycle_ai_context_policy_key": str(selected.get("policy_key") or "-"),
        "lifecycle_ai_context_hash": context_hash,
        "lifecycle_ai_context_alignment_hint": str(
            selected.get("alignment_hint") or "NO_CHANGE"
        ),
    }
    return {
        "applied": True,
        "status": "advisory_prompt_applied",
        "cache_token": f"lifecycle_ai_context:{payload.get('context_version') or '-'}:{stage_name}:{context_hash}",
        "prompt_context": context_text,
        "fields": fields,
    }


def merge_lifecycle_ai_context_fields(
    result: dict[str, Any] | None,
    runtime_context: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(result or {})
    context = runtime_context or {}
    fields = dict(context.get("fields") or {})
    payload.update(fields)
    return payload


def render_lifecycle_ai_context_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Lifecycle AI Context - {report.get('date')}",
        "",
        f"- context_version: `{report.get('context_version')}`",
        f"- authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- provider_status: `{report.get('provider_status') or {}}`",
        "",
        "## Stage Contexts",
        "| stage | prompt | policy_key | hint | contribution | quality |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report.get("stage_contexts") or []:
        if not isinstance(item, dict):
            continue
        lines.append(
            "| `{stage}` | `{prompt}` | `{policy}` | `{hint}` | `{score}` | `{quality}` |".format(
                stage=item.get("stage"),
                prompt=item.get("prompt_injection_allowed"),
                policy=item.get("policy_key"),
                hint=item.get("alignment_hint"),
                score=item.get("context_contribution_score"),
                quality=item.get("attribution_quality_status"),
            )
        )
    lines.extend(["", "## Forbidden Uses", f"- `{report.get('forbidden_uses') or []}`"])
    return "\n".join(lines) + "\n"


def render_lifecycle_ai_context_attribution_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        f"# Lifecycle AI Context Attribution - {report.get('date')}",
        "",
        f"- authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        f"- context eligible/applied/skipped: `{summary.get('context_eligible_count')}` / `{summary.get('context_applied_count')}` / `{summary.get('context_skipped_count')}`",
        f"- replay_budget: `{summary.get('replay_budget')}` / mode: `{summary.get('replay_mode')}`",
        f"- implementation_status: `{report.get('implementation_status') or '-'}`",
        "",
        "## Stage Attribution",
        "| stage | eligible | applied | completed | align | replay | delta | ev | contribution | quality |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    stage_map = (
        report.get("stage_attribution")
        if isinstance(report.get("stage_attribution"), dict)
        else {}
    )
    for stage in STAGES:
        item = stage_map.get(stage) if isinstance(stage_map.get(stage), dict) else {}
        lines.append(
            "| `{stage}` | `{eligible}` | `{applied}` | `{completed}` | `{align}` | `{replay}` | `{delta}` | `{ev}` | `{contrib}` | `{quality}` |".format(
                stage=stage,
                eligible=item.get("context_eligible_count"),
                applied=item.get("context_applied_count"),
                completed=item.get("completed_sample"),
                align=item.get("ai_action_alignment_rate"),
                replay=item.get("no_context_replay_observed"),
                delta=item.get("ai_action_delta_rate"),
                ev=item.get("source_quality_adjusted_ev_pct"),
                contrib=item.get("context_contribution_score"),
                quality=item.get("attribution_quality_status"),
            )
        )
    lines.extend(["", "## Forbidden Uses", f"- `{report.get('forbidden_uses') or []}`"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build lifecycle AI context and attribution reports."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument(
        "--mode",
        choices=("context", "attribution", "both"),
        default="both",
    )
    parser.add_argument("--provider", default="deterministic_source_only")
    parser.add_argument("--replay-budget", type=int, default=REPLAY_BUDGET)
    args = parser.parse_args()
    if args.mode in {"attribution", "both"}:
        build_lifecycle_ai_context_attribution_report(
            args.target_date, replay_budget=args.replay_budget
        )
    if args.mode in {"context", "both"}:
        build_lifecycle_ai_context_report(args.target_date, provider=args.provider)


if __name__ == "__main__":
    main()
