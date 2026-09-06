"""Lifecycle AI context source and attribution reports.

This module is intentionally context-only. It may build prompt text and
postclose attribution summaries, but it must not gate real orders or mutate
runtime actions.
"""

from __future__ import annotations

from src.engine.lifecycle.retirement import RETIREMENT_ID, retired_status

import gzip
import hashlib
import json
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
    return retired_status("lifecycle_ai_context")


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
    return retired_status("lifecycle_ai_context")


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
    stage_name = _stage_for_prompt(prompt_profile, stage)
    return {
        "applied": False,
        "status": "retired",
        "cache_token": RETIREMENT_ID,
        "prompt_context": "",
        "fields": {
            "lifecycle_ai_context_enabled": False,
            "lifecycle_ai_context_applied": False,
            "lifecycle_ai_context_status": "retired",
            "lifecycle_ai_context_version": "-",
            "lifecycle_ai_context_source_date": "-",
            "lifecycle_ai_context_stage": stage_name,
            "lifecycle_ai_context_policy_key": "-",
            "lifecycle_ai_context_hash": "-",
            "lifecycle_ai_context_alignment_hint": "NO_CHANGE",
            "lifecycle_ai_context_decision_authority": "archive_only",
            "lifecycle_ai_context_runtime_effect": "none",
            "lifecycle_ai_context_actual_order_submitted": False,
            "lifecycle_ai_context_broker_order_forbidden": True,
        },
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
    print(json.dumps(retired_status("lifecycle_ai_context")))
    return 0


if __name__ == "__main__":
    main()
