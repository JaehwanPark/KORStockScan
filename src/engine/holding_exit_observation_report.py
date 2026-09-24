"""Holding/exit observation report for Plan Rebase tuning decisions."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy
from src.engine.monitor_snapshot_runtime import guard_stdin_heavy_build
from src.engine.scalping.trailing_threshold_policy import (
    GRID_VERSION as SCALP_TRAILING_GRID_VERSION,
    bootstrap_receipt as scalp_trailing_bootstrap_receipt,
    start_values_hash as scalp_trailing_start_values_hash,
    value_hash as scalp_trailing_value_hash,
)
from src.engine.scalping.trailing_start_replay import (
    replay_start_grid,
    summarize_start_grid,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

SCHEMA_VERSION = 2
POST_FALLBACK_CUTOFF = datetime(2026, 4, 21, 9, 45)
TARGET_EXIT_RULES = (
    "scalp_trailing_take_profit",
    "scalp_soft_stop_pct",
    "scalp_preset_hard_stop_pct",
    "scalp_hard_stop_pct",
    "EOD/NXT",
)


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in (None, "", "-", "None"):
        return default
    try:
        result = float(value)
    except Exception:
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int = 0) -> int:
    if value in (None, "", "-", "None"):
        return default
    try:
        return int(float(value))
    except Exception:
        return default


def _ratio(numerator: int, denominator: int) -> float:
    return (
        round((float(numerator) / float(denominator)) * 100.0, 1)
        if denominator > 0
        else 0.0
    )


def _avg(values: list[float]) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    return round(sum(clean) / len(clean), 3) if clean else 0.0


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if value in (None, "", "None"):
        return None
    raw = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            continue
    return None


def _parse_aware_dt(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo is not None else None


def _post_sell_binding_gap(trade: dict, candidate: dict) -> str | None:
    terminal_fill_at = _parse_aware_dt(trade.get("exact_sell_fill_time"))
    candidate_fill_at = _parse_aware_dt(candidate.get("exact_sell_fill_time"))
    if terminal_fill_at is None or candidate_fill_at is None:
        return "source_gap_exact_fill_binding_missing"
    if terminal_fill_at != candidate_fill_at:
        return "source_gap_exact_fill_binding_mismatch"
    if (not trade.get("sell_order_no") or not trade.get("sell_execution_no")
            or str(candidate.get("sell_order_no") or "")
               != str(trade.get("sell_order_no"))
            or str(candidate.get("sell_execution_no") or "")
               != str(trade.get("sell_execution_no"))):
        return "source_gap_post_sell_execution_identity"
    terminal_venue = str(trade.get("effective_venue") or "").upper()
    candidate_venue = str(candidate.get("actual_execution_venue") or "").upper()
    terminal_route = str(trade.get("exit_execution_broker_route") or "").upper()
    candidate_route = str(candidate.get("broker_route_requested") or "").upper()
    if (candidate.get("market_axes_source_quality_status") != "route_contract_ready"
            or terminal_venue not in {"KRX", "NXT"}
            or candidate_venue != terminal_venue
            or terminal_route not in {"KRX", "NXT", "SOR"}
            or candidate_route != terminal_route):
        return "source_gap_post_sell_venue_route"
    return None


def _date_range(month_start: str, target_date: str) -> list[str]:
    start = datetime.strptime(month_start, "%Y-%m-%d").date()
    end = datetime.strptime(target_date, "%Y-%m-%d").date()
    if end < start:
        return []
    values: list[str] = []
    current = start
    while current <= end:
        values.append(current.isoformat())
        current += timedelta(days=1)
    return values


def _analysis_window_start(
    *, target_date: str, month_start: str | None
) -> tuple[str, dict[str, Any]]:
    """Resolve the report window without silently reverting to a month-only view.

    ``month_start`` remains an explicit, audit-oriented override for existing
    callers. The normal producer instead starts at the active clean-tuning
    baseline, so a quiet new month cannot hide mature post-sell evidence.
    """

    policy = clean_baseline_policy()
    baseline_date = str(
        policy.get("clean_tuning_baseline_date") or "2026-06-05"
    ).strip()
    explicit_start = str(month_start or "").strip()
    clean_baseline_enabled = bool(policy.get("enabled", True))
    default_start = baseline_date if clean_baseline_enabled else f"{target_date[:7]}-01"
    start_date = explicit_start or default_start
    return start_date, {
        "start_date": start_date,
        "end_date": target_date,
        "selection": (
            "explicit_month_start_audit_override"
            if explicit_start
            else (
                "clean_tuning_baseline_default"
                if clean_baseline_enabled
                else "calendar_month_policy_disabled"
            )
        ),
        "clean_tuning_baseline_date": baseline_date,
        "clean_tuning_baseline_enabled": clean_baseline_enabled,
        "pre_baseline_decision": policy.get("pre_baseline_decision"),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _read_json(path: Path) -> dict:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict]:
    path = existing_or_gzip_path(path)
    if not path.exists():
        return []
    opener = gzip.open if path.suffix == ".gz" else open
    rows: list[dict] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
    return rows


def _monitor_snapshot_path(snapshot_kind: str, target_date: str) -> Path | None:
    snapshot_dir = DATA_DIR / "report" / "monitor_snapshots"
    safe_kind = str(snapshot_kind or "").strip().lower().replace("-", "_")
    for suffix in (".json", ".json.gz"):
        candidate = snapshot_dir / f"{safe_kind}_{target_date}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _load_saved_snapshot(snapshot_kind: str, target_date: str) -> dict | None:
    path = _monitor_snapshot_path(snapshot_kind, target_date)
    if path is None:
        return None
    try:
        return _read_json(path)
    except Exception:
        return None


def _load_saved_snapshots(
    snapshot_kind: str, dates: list[str]
) -> tuple[list[dict], list[str]]:
    snapshots: list[dict] = []
    paths: list[str] = []
    for target_date in dates:
        path = _monitor_snapshot_path(snapshot_kind, target_date)
        if path is None:
            continue
        try:
            snapshots.append(_read_json(path))
            paths.append(str(path))
        except Exception:
            continue
    return snapshots, paths


def _collect_completed_trade_rows(
    snapshots: list[dict],
) -> tuple[list[dict], list[dict]]:
    rows: list[dict] = []
    gaps: list[dict] = []
    seen: dict[str, dict] = {}
    for snapshot in snapshots:
        if snapshot.get("code") or snapshot.get("since"):
            gaps.append(
                {
                    "date": snapshot.get("date"),
                    "reason": "filtered_trade_review_snapshot",
                }
            )
            continue
        if (snapshot.get("meta") or {}).get("warnings"):
            gaps.append(
                {"date": snapshot.get("date"), "reason": "trade_review_source_warning"}
            )
            continue
        sections = snapshot.get("sections") or {}
        projection = sections.get("completed_trade_projection")
        recent = sections.get("recent_trades") or []
        candidates = projection if isinstance(projection, list) else recent
        completed = [
            row
            for row in candidates
            if isinstance(row, dict)
            and str(row.get("status") or "").upper() == "COMPLETED"
        ]
        metrics = snapshot.get("metrics") or {}
        count_key = (
            "canonical_completed_trades"
            if isinstance(projection, list)
            else "completed_trades"
        )
        declared = _safe_int(metrics.get(count_key), -1)
        ids = [_trade_id(row) for row in completed]
        if isinstance(projection, list):
            raw_event_ids = (snapshot.get("meta") or {}).get("sell_completed_event_ids")
            if not isinstance(raw_event_ids, list) or {
                str(item) for item in raw_event_ids
            } != set(ids):
                gaps.append(
                    {
                        "date": snapshot.get("date"),
                        "reason": "sell_completed_id_census_mismatch",
                    }
                )
                continue
        if (
            declared < 0
            or len(completed) != declared
            or not all(ids)
            or len(set(ids)) != len(ids)
        ):
            gaps.append(
                {
                    "date": snapshot.get("date"),
                    "reason": (
                        "completed_population_truncated"
                        if not isinstance(projection, list)
                        and declared > len(completed)
                        else "completed_population_contract_gap"
                    ),
                    "declared": declared,
                    "observed": len(completed),
                }
            )
            continue
        if not isinstance(projection, list):
            gaps.append(
                {
                    "date": snapshot.get("date"),
                    "reason": "legacy_completion_census_unsealed",
                    "declared": declared,
                    "observed": len(completed),
                }
            )
            # Historical display rows carry modeled PnL and possibly synthetic
            # exit signals. They may be used diagnostically, never as exact-cost
            # economic evidence.
            completed = [
                {
                    **row,
                    "modeled_realized_pnl_krw": row.get("realized_pnl_krw"),
                    "realized_pnl_krw": None,
                    "realized_pnl_krw_source": "legacy_display_unsealed",
                    "exact_sell_fill_time": None,
                }
                for row in completed
            ]
        elif any(
            row.get("completion_day_basis") != "terminal_event" for row in completed
        ):
            gaps.append(
                {
                    "date": snapshot.get("date"),
                    "reason": "completion_day_terminal_receipt_missing",
                }
            )
        for row in completed:
            trade_id = _trade_id(row)
            previous = seen.get(trade_id)
            if previous is not None:
                if previous != row:
                    gaps.append(
                        {
                            "date": snapshot.get("date"),
                            "reason": "duplicate_completed_trade_conflict",
                            "id": trade_id,
                        }
                    )
                continue
            seen[trade_id] = row
            rows.append(row)
    return rows, gaps


def _collect_open_scalp_positions(
    snapshots: list[dict], target_date: str
) -> tuple[list[dict], str]:
    latest = next(
        (row for row in snapshots if str(row.get("date") or "") == target_date),
        None,
    )
    if not isinstance(latest, dict) or (latest.get("meta") or {}).get("warnings"):
        return [], "source_gap_trade_review_missing_or_warning"
    rows = (latest.get("sections") or {}).get("open_scalp_position_projection")
    if not isinstance(rows, list):
        return [], "source_gap_open_projection_missing"
    ids = [str(row.get("id") or "") for row in rows if isinstance(row, dict)]
    declared = _safe_int(
        (latest.get("metrics") or {}).get("open_scalp_position_projection_count"), -1
    )
    census_status = (latest.get("metrics") or {}).get(
        "open_scalp_position_projection_status"
    )
    if census_status != "current_db_census":
        return [], str(census_status or "source_gap_open_census_status_missing")
    if (
        len(ids) != len(rows)
        or declared != len(rows)
        or not all(ids)
        or len(set(ids)) != len(ids)
    ):
        return [], "source_gap_open_projection_census_mismatch"
    return rows, "observed_open_census_not_economic"


def _is_valid_completed_trade(row: dict) -> bool:
    if str(row.get("status") or "").upper() != "COMPLETED":
        return False
    if str(row.get("strategy") or "").upper() not in {"SCALPING", "SCALP"}:
        return False
    return _safe_float(row.get("profit_rate"), None) is not None


def _strict_completed_reasons(row: dict, *, clean_start: str) -> list[str]:
    """Keep the DB completion census separate from broker-proven economics."""
    raw_reasons = row.get("strict_completion_reasons")
    reasons = list(raw_reasons) if isinstance(raw_reasons, list) else []
    if raw_reasons is not None and not isinstance(raw_reasons, list):
        reasons.append("source_gap_strict_completion_reasons_invalid")
    if row.get("strict_completion_status") != "eligible":
        if not reasons:
            reasons.append("source_gap_strict_completion_receipt_missing")
    if str(row.get("rec_date") or "")[:10] < clean_start:
        reasons.append("outside_clean_entry_window")
    if str(row.get("completion_observed_date") or "")[:10] < clean_start:
        reasons.append("outside_clean_completion_window")
    if _entry_mode(row) != "normal":
        reasons.append("non_normal_or_unproven_entry_mode")
    if row.get("terminal_population_scope") != "real_record_bound":
        reasons.append("source_gap_real_custody_unproven")
    entry_day = str(row.get("rec_date") or "")[:10]
    completion_day = str(row.get("completion_observed_date") or "")[:10]
    if entry_day < completion_day:
        if (row.get("prior_entry_snapshot_receipt") or {}).get("status") != "sealed_entry_snapshot":
            reasons.append("source_gap_prior_entry_snapshot_unsealed")
        fill_receipts = row.get("prior_fill_snapshot_receipts")
        try:
            day = datetime.strptime(entry_day, "%Y-%m-%d").date()
            final_day = datetime.strptime(completion_day, "%Y-%m-%d").date()
            while day < final_day:
                if (not isinstance(fill_receipts, dict)
                        or not isinstance(fill_receipts.get(day.isoformat()), dict)
                        or fill_receipts[day.isoformat()].get("status")
                        != "sealed_entry_snapshot"):
                    reasons.append("source_gap_prior_fill_snapshot_unsealed")
                    break
                day += timedelta(days=1)
        except ValueError:
            reasons.append("source_gap_prior_fill_snapshot_unsealed")
    if row.get("sell_quantity_conserved") is not True:
        reasons.append("source_gap_sell_quantity_not_conserved")
    if row.get("terminal_profit_rate_reconciled") is not True:
        reasons.append("source_gap_profit_rate_unreconciled")
    if (row.get("realized_pnl_krw_source") != "broker_fill_prices_fee_aware"
            or _safe_float(row.get("realized_pnl_krw"), None) is None):
        reasons.append("source_gap_exact_cost_missing")
    return sorted(set(reasons))


def _entry_mode(row: dict) -> str:
    return str(row.get("entry_mode") or "").strip().lower()


def _trade_id(row: dict) -> str:
    return str(row.get("id") or row.get("recommendation_id") or "").strip()


def _is_post_fallback(row: dict) -> bool:
    buy_dt = _parse_dt(row.get("buy_time"))
    return bool(buy_dt and buy_dt >= POST_FALLBACK_CUTOFF)


def _exit_rule_from_trade(row: dict) -> str:
    exit_signal = row.get("exit_signal")
    if isinstance(exit_signal, dict):
        for key in ("exit_rule", "rule", "reason"):
            value = str(exit_signal.get(key) or "").strip()
            if value:
                return value
    for event in row.get("timeline") or []:
        if not isinstance(event, dict) or event.get("stage") != "exit_signal":
            continue
        fields = event.get("fields") or {}
        for key in ("exit_rule", "rule", "reason", "exit_reason"):
            value = str(fields.get(key) or "").strip()
            if value:
                return value
    return "-"


def _exit_group(exit_rule: str) -> str:
    normalized = str(exit_rule or "-").strip()
    lowered = normalized.lower()
    if any(token in lowered for token in ("eod", "nxt", "overnight", "preclose")):
        return "EOD/NXT"
    return normalized or "-"


def _fill_quality(row: dict) -> str:
    qualities: list[str] = []
    for event in row.get("timeline") or []:
        if not isinstance(event, dict):
            continue
        fields = event.get("fields") or {}
        value = str(fields.get("fill_quality") or "").strip().upper()
        if value:
            qualities.append(value)
    if any("PARTIAL" in quality for quality in qualities):
        return "partial_fill"
    if any("FULL" in quality for quality in qualities):
        return "full_fill"
    return "unknown_fill"


def _is_pyramid_activated(row: dict) -> bool:
    base_qty = _safe_int(row.get("buy_qty"), 0)
    for event in row.get("timeline") or []:
        if not isinstance(event, dict):
            continue
        if str(event.get("stage") or "") == "scale_in_executed":
            return True
        fields = event.get("fields") or {}
        if _safe_int(fields.get("add_count"), 0) > 0:
            return True
        if base_qty > 0 and _safe_int(fields.get("new_buy_qty"), 0) > base_qty:
            return True
    return False


def _summarize_completed_trades(rows: list[dict]) -> dict:
    valid_rows = [row for row in rows if _is_valid_completed_trade(row)]
    profits = [
        float(_safe_float(row.get("profit_rate"), 0.0) or 0.0) for row in valid_rows
    ]
    exit_rules = Counter(_exit_group(_exit_rule_from_trade(row)) for row in valid_rows)
    pnl_values = [_safe_float(row.get("realized_pnl_krw"), None) for row in valid_rows]
    pnl_complete = [value for value in pnl_values if value is not None]
    return {
        "trade_count": len(valid_rows),
        "win_trades": sum(1 for value in profits if value > 0),
        "loss_trades": sum(1 for value in profits if value <= 0),
        "avg_profit_rate": _avg(profits),
        "realized_pnl_krw": (
            int(round(sum(pnl_complete)))
            if len(pnl_complete) == len(valid_rows) and valid_rows
            else None
        ),
        "realized_pnl_complete_count": len(pnl_complete),
        "realized_pnl_missing_count": len(valid_rows) - len(pnl_complete),
        "exit_rules": [
            {"label": key, "count": value} for key, value in exit_rules.most_common()
        ],
    }


def _build_cohorts(valid_trades: list[dict]) -> dict:
    return {
        "normal_only": _summarize_completed_trades(
            [row for row in valid_trades if _entry_mode(row) == "normal"]
        ),
        "post_fallback_deprecation": _summarize_completed_trades(
            [row for row in valid_trades if _is_post_fallback(row)]
        ),
        "post_fallback_normal_only": _summarize_completed_trades(
            [
                row
                for row in valid_trades
                if _is_post_fallback(row) and _entry_mode(row) == "normal"
            ]
        ),
        "full_fill": _summarize_completed_trades(
            [row for row in valid_trades if _fill_quality(row) == "full_fill"]
        ),
        "partial_fill": _summarize_completed_trades(
            [row for row in valid_trades if _fill_quality(row) == "partial_fill"]
        ),
        "initial-only": _summarize_completed_trades(
            [row for row in valid_trades if not _is_pyramid_activated(row)]
        ),
        "pyramid-activated": _summarize_completed_trades(
            [row for row in valid_trades if _is_pyramid_activated(row)]
        ),
    }


def _post_sell_candidate_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_candidates_{target_date}.jsonl"


def _post_sell_evaluation_path(target_date: str) -> Path:
    return DATA_DIR / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl"


def _load_post_sell_rows(dates: list[str]) -> tuple[list[dict], list[str]]:
    candidates_by_id: dict[str, dict] = {}
    evaluations: list[dict] = []
    paths: list[str] = []
    for target_date in dates:
        candidate_path = _post_sell_candidate_path(target_date)
        evaluation_path = _post_sell_evaluation_path(target_date)
        candidate_actual_path = existing_or_gzip_path(candidate_path)
        evaluation_actual_path = existing_or_gzip_path(evaluation_path)
        if candidate_actual_path.exists():
            paths.append(str(candidate_actual_path))
        if evaluation_actual_path.exists():
            paths.append(str(evaluation_actual_path))
        for candidate in _read_jsonl(candidate_path):
            post_sell_id = str(candidate.get("post_sell_id") or "")
            if post_sell_id:
                candidates_by_id[post_sell_id] = candidate
        evaluations.extend(_read_jsonl(evaluation_path))

    rows: list[dict] = []
    evaluated_ids: set[str] = set()
    for evaluation in evaluations:
        post_sell_id = str(evaluation.get("post_sell_id") or "")
        candidate = candidates_by_id.get(post_sell_id, {})
        rows.append(
            {
                **_enrich_post_sell_row(candidate=candidate, evaluation=evaluation),
                "evaluation_status": (
                    "evaluated" if candidate else "source_gap_candidate_missing"
                ),
            }
        )
        evaluated_ids.add(post_sell_id)
    rows.extend(
        {**candidate, "evaluation_status": "candidate_only"}
        for post_sell_id, candidate in candidates_by_id.items()
        if post_sell_id not in evaluated_ids
    )
    return rows, paths


_FLOW_INTERVENTION_STAGES = {
    "holding_flow_override_defer_exit": "deferred",
    "holding_flow_max_defer_bullish_extension": "deferred_extension",
    "holding_flow_override_force_exit": "force_exit_review",
    "holding_flow_override_confirm_exit": "confirmed_exit_review",
}


def _trailing_policy_manifest_binding(
    policy_date: str, observed_sha: str, observed_market_sha: str = ""
) -> dict:
    """Bind an effective value hash to its dated producer, not to a live PID."""

    try:
        datetime.strptime(policy_date, "%Y-%m-%d")
    except (TypeError, ValueError):
        return {"status": "source_gap_policy_date_missing"}
    path = (
        DATA_DIR
        / "runtime"
        / "policy_bootstrap"
        / f"runtime_policy_bootstrap_{policy_date}.json"
    )
    env_path = path.with_suffix(".env")
    try:
        manifest = _read_json(path)
        env_bytes = env_path.read_bytes()
    except (OSError, ValueError):
        return {"status": "source_gap_bootstrap_missing", "path": str(path)}
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    try:
        manifest_sha = hashlib.sha256(
            json.dumps(
                unsigned, ensure_ascii=True, allow_nan=False, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError):
        return {"status": "source_gap_bootstrap_invalid", "path": str(path)}
    receipt = manifest.get("scalp_trailing_threshold_receipt") or {}
    try:
        receipt_sha = scalp_trailing_value_hash(receipt["values"])
        expected_receipt = scalp_trailing_bootstrap_receipt(
            manifest["env_overrides"], manifest["env_key_owners"]
        )
    except (KeyError, TypeError, ValueError):
        receipt_sha = ""
        expected_receipt = None
    valid = bool(
        manifest.get("target_date") == policy_date
        and manifest.get("manifest_sha256") == manifest_sha
        and manifest.get("env_sha256") == hashlib.sha256(env_bytes).hexdigest()
        and receipt.get("schema") == "scalp_trailing_threshold_receipt_v2"
        and receipt.get("value_sha256") == receipt_sha
        and receipt == expected_receipt
        and manifest["env_overrides"].get(
            "KORSTOCKSCAN_SCALP_TRAILING_VALUE_SHA256"
        ) == receipt_sha
        and observed_sha == receipt_sha
        and receipt.get("start_by_market_sha256") == observed_market_sha
        and manifest["env_overrides"].get(
            "KORSTOCKSCAN_SCALP_TRAILING_START_BY_MARKET_SHA256"
        ) == observed_market_sha
    )
    return {
        "status": (
            "manifest_value_hash_matched_no_pid_proof"
            if valid else "source_gap_bootstrap_binding_mismatch"
        ),
        "path": str(path),
        "manifest_sha256": manifest_sha if valid else None,
        "value_sha256": receipt_sha or None,
        "sources": receipt.get("sources") if valid else None,
    }


def _operational_manifest_binding(
    policy_date: str, values: dict | None, sources: dict | None
) -> dict:
    """Check environment sourced inputs against the dated bootstrap artifact."""

    if not isinstance(values, dict) or not isinstance(sources, dict):
        return {"status": "source_gap_operational_values_or_sources"}
    path = (
        DATA_DIR / "runtime" / "policy_bootstrap"
        / f"runtime_policy_bootstrap_{policy_date}.json"
    )
    try:
        manifest = _read_json(path)
    except (OSError, ValueError):
        return {"status": "source_gap_operational_manifest_missing"}
    env = manifest.get("env_overrides")
    owners = manifest.get("env_key_owners")
    if not isinstance(env, dict) or not isinstance(owners, dict):
        return {"status": "source_gap_operational_manifest_invalid"}
    matched = {}
    mismatched = []
    code_owned = []
    for key, observed in values.items():
        source = sources.get(key)
        if source in {"code_default", "code_constant"}:
            code_owned.append(key)
            continue
        if source != "runtime_env":
            mismatched.append(key)
            continue
        env_key = key if key.startswith("KORSTOCKSCAN_") else f"KORSTOCKSCAN_{key}"
        try:
            matches = math.isclose(float(env[env_key]), float(observed), abs_tol=1e-9)
        except (KeyError, TypeError, ValueError):
            matches = False
        if matches and owners.get(env_key):
            matched[key] = owners[env_key]
        else:
            mismatched.append(key)
    return {
        "status": (
            "source_gap_operational_env_mismatch" if mismatched
            else "env_values_matched_code_defaults_unproven_no_pid_proof"
        ),
        "manifest_path": str(path),
        "env_matched_owners": matched,
        "code_owned_keys": sorted(code_owned),
        "mismatched_keys": sorted(mismatched),
    }


def _build_position_outcomes(
    trades: list[dict], post_sell_rows: list[dict]
) -> tuple[list[dict], dict]:
    """Join existing owner receipts without turning labels into causal evidence."""
    post_sell_by_trade: dict[str, list[dict]] = defaultdict(list)
    for post_sell in post_sell_rows:
        trade_id = str(post_sell.get("recommendation_id") or "").strip()
        if trade_id and post_sell.get("post_sell_id"):
            post_sell_by_trade[trade_id].append(post_sell)

    outcomes: list[dict] = []
    bootstrap_bindings: dict[tuple[str, str], dict] = {}
    for trade in trades:
        trade_id = _trade_id(trade)
        timeline = [
            event for event in trade.get("timeline") or [] if isinstance(event, dict)
        ]
        exit_signal = trade.get("exit_signal") or {}
        exit_rule = _exit_group(_exit_rule_from_trade(trade))
        inferred = bool(exit_signal.get("inferred")) or not any(
            event.get("stage") == "exit_signal" and not event.get("is_inferred")
            for event in timeline
        )
        role_event = next(
            (
                event
                for event in reversed(timeline)
                if event.get("stage") in {"exit_signal", "sell_order_sent"}
                and (event.get("fields") or {}).get("holding_score_role_gate")
            ),
            {},
        )
        role_fields = role_event.get("fields") or {}
        role_gate = str(role_fields.get("holding_score_role_gate") or "missing")
        threshold_fields = exit_signal.get("fields") or {} if not inferred else {}
        threshold_status = str(
            threshold_fields.get("exit_threshold_status")
            or "source_gap_missing_receipt"
        )
        alternative_observations = sorted(
            {
                str((event.get("fields") or {}).get("exit_rule") or "")
                for event in timeline
                if event.get("stage") == "scalp_tp_alternative_observed"
                and (event.get("fields") or {}).get("would_exit") is True
                and (event.get("fields") or {}).get("exit_rule")
            }
        )
        trailing_transitions = [
            event.get("fields") or {}
            for event in timeline
            if event.get("stage") == "scalp_trailing_input_transition"
        ]
        holding_start_events = [
            event for event in timeline
            if event.get("stage") == "holding_started"
            and (event.get("fields") or {}).get(
                "pipeline_lifecycle_population_scope"
            ) == "real_record_bound"
        ]
        first_arm = next(
            (
                fields
                for fields in trailing_transitions
                if str(fields.get("armed")).strip().lower() in {"true", "1"}
            ),
            {},
        )
        first_trigger = next(
            (
                fields
                for fields in trailing_transitions
                if str(fields.get("triggered")).strip().lower() in {"true", "1"}
            ),
            {},
        )
        trailing_source_gap_count = sum(
            str(fields.get("source_gap")).strip().lower() in {"true", "1"}
            for fields in trailing_transitions
        )
        transition_sequences = [
            _safe_int(fields.get("event_sequence"), -1)
            for fields in trailing_transitions
        ]
        transition_position_keys = {
            str(fields.get("position_key") or "") for fields in trailing_transitions
        }
        transition_grid_versions = {
            str(fields.get("observation_grid_version") or "")
            for fields in trailing_transitions
        }
        coverage_exhausted = any(
            str(fields.get("observation_coverage_exhausted")).lower()
            in {"true", "1"}
            for fields in trailing_transitions
        )
        telemetry_gap = any(
            str(fields.get("observation_telemetry_gap")).lower() in {"true", "1"}
            for fields in trailing_transitions
        ) or str(threshold_fields.get(
            "scalp_trailing_observation_source_gap"
        )).lower() in {"true", "1"}
        policy_sha = str(
            threshold_fields.get("scalp_trailing_policy_value_sha256")
            or (trailing_transitions[-1].get("scalp_trailing_policy_value_sha256")
                if trailing_transitions else "")
            or ""
        )
        policy_date = str(
            threshold_fields.get("scalp_trailing_policy_date")
            or (trailing_transitions[-1].get("scalp_trailing_policy_date")
                if trailing_transitions else "")
            or ""
        )
        policy_values = threshold_fields.get("scalp_trailing_policy_values")
        if not isinstance(policy_values, dict):
            policy_values = next(
                (
                    row.get("scalp_trailing_policy_values")
                    for row in trailing_transitions
                    if isinstance(row.get("scalp_trailing_policy_values"), dict)
                ),
                None,
            )
        try:
            policy_values_valid = (
                isinstance(policy_values, dict)
                and scalp_trailing_value_hash(policy_values) == policy_sha
            )
        except (KeyError, TypeError, ValueError):
            policy_values_valid = False
        observed_policy_shas = {
            str(fields.get("scalp_trailing_policy_value_sha256") or "")
            for fields in trailing_transitions
        }
        observed_policy_provenance = {
            str(fields.get("scalp_trailing_policy_provenance") or "")
            for fields in trailing_transitions
        }
        observed_expected_shas = {
            str(fields.get("scalp_trailing_policy_expected_sha256") or "")
            for fields in trailing_transitions
        }
        observed_operational_shas = {
            str(fields.get("operational_threshold_value_sha256") or "")
            for fields in trailing_transitions
        }
        first_operational_values = next(
            (
                row.get("operational_threshold_values")
                for row in trailing_transitions
                if isinstance(row.get("operational_threshold_values"), dict)
            ),
            None,
        )
        first_operational_sources = next(
            (
                row.get("operational_threshold_sources")
                for row in trailing_transitions
                if isinstance(row.get("operational_threshold_sources"), dict)
            ),
            None,
        )
        operational_sha = next(iter(observed_operational_shas), "")
        try:
            operational_values_hash = hashlib.sha256(
                json.dumps(
                    first_operational_values, allow_nan=False, sort_keys=True,
                    separators=(",", ":")
                ).encode()
            ).hexdigest()
        except (TypeError, ValueError):
            operational_values_hash = ""
        operational_values_valid = bool(
            first_operational_values
            and len(observed_operational_shas) == 1
            and operational_sha == operational_values_hash
        )
        is_trailing_observed = bool(
            exit_rule == "scalp_trailing_take_profit" or trailing_transitions
        )
        market_values = next(
            (
                row.get("scalp_trailing_start_by_market")
                for row in trailing_transitions
                if isinstance(row.get("scalp_trailing_start_by_market"), dict)
            ),
            None,
        )
        start_replay = replay_start_grid(
            trade,
            trailing_transitions,
            actual_exit_rule=exit_rule,
            actual_exit_signal=exit_signal,
            incumbent_start_pct=_safe_float(
                (policy_values or {}).get("SCALP_TRAILING_START_PCT"), 0.6
            ) or 0.6,
            incumbent_by_market=market_values,
        )
        operational_binding = (
            _operational_manifest_binding(
                policy_date,
                first_operational_values if operational_values_valid else None,
                first_operational_sources if operational_values_valid else None,
            )
            if is_trailing_observed else {"status": "not_applicable_non_trailing"}
        )
        market_shas = {
            str(fields.get("scalp_trailing_start_by_market_sha256") or "")
            for fields in trailing_transitions
        }
        market_provenance = {
            str(fields.get("scalp_trailing_start_by_market_provenance") or "")
            for fields in trailing_transitions
        }
        market_sha = next(iter(market_shas), "")
        market_value_hashes = set()
        for row in trailing_transitions:
            try:
                market_value_hashes.add(scalp_trailing_start_values_hash(
                    row.get("scalp_trailing_start_by_market")
                ))
            except (TypeError, ValueError):
                market_value_hashes.add("")
        binding_key = (policy_date, policy_sha, market_sha)
        if is_trailing_observed and binding_key not in bootstrap_bindings:
            bootstrap_bindings[binding_key] = _trailing_policy_manifest_binding(
                policy_date, policy_sha, market_sha
            )
        policy_binding = (
            bootstrap_bindings[binding_key] if is_trailing_observed
            else {"status": "not_applicable_non_trailing"}
        )
        if not is_trailing_observed:
            trailing_replay_status = "not_applicable_non_trailing"
        elif not trailing_transitions:
            trailing_replay_status = "source_gap_no_input_samples"
        elif trade.get("trailing_event_source_status") != "structured_partition_read":
            trailing_replay_status = "source_gap_structured_event_partition"
        elif not trade.get("trailing_event_source_sha256"):
            trailing_replay_status = "source_gap_structured_event_hash_missing"
        elif not holding_start_events:
            trailing_replay_status = "source_gap_holding_start_missing"
        elif coverage_exhausted:
            trailing_replay_status = "source_gap_sample_cap_exhausted"
        elif telemetry_gap:
            trailing_replay_status = "source_gap_observation_telemetry_failure"
        elif (
            transition_sequences != list(range(1, len(transition_sequences) + 1))
            or len(transition_position_keys) != 1
            or "" in transition_position_keys
        ):
            trailing_replay_status = "source_gap_position_or_sequence"
        elif transition_grid_versions != {SCALP_TRAILING_GRID_VERSION}:
            trailing_replay_status = "source_gap_grid_version"
        elif observed_policy_shas != {policy_sha} or policy_sha in {"", "-"}:
            trailing_replay_status = "source_gap_policy_changed_or_missing"
        elif len(market_shas) != 1 or market_sha in {"", "-"}:
            trailing_replay_status = "source_gap_market_policy_changed_or_missing"
        elif market_value_hashes != {market_sha}:
            trailing_replay_status = "source_gap_market_policy_values_hash"
        elif market_provenance != {"bootstrap_value_hash_matched"}:
            trailing_replay_status = "source_gap_market_policy_runtime_hash"
        elif (
            observed_policy_provenance != {"bootstrap_value_hash_matched"}
            or observed_expected_shas != {policy_sha}
        ):
            trailing_replay_status = "source_gap_runtime_bootstrap_hash"
        elif not policy_values_valid:
            trailing_replay_status = "source_gap_policy_values"
        elif not operational_values_valid:
            trailing_replay_status = "source_gap_operational_values"
        elif operational_binding["status"].startswith("source_gap"):
            trailing_replay_status = "source_gap_operational_manifest_binding"
        elif policy_binding["status"] != "manifest_value_hash_matched_no_pid_proof":
            trailing_replay_status = "source_gap_policy_binding"
        else:
            # Grid crossings are captured, but unobserved intra-poll prices and
            # future order fills still prohibit an economic counterfactual.
            trailing_replay_status = "grid_source_linked_paired_replay_pending"
        if trailing_replay_status != "grid_source_linked_paired_replay_pending":
            start_replay = {
                **start_replay,
                "source_gap": trailing_replay_status,
                "markets": {},
            }
        operational_inputs = {
            "quote_age": any(
                _safe_float(row.get("bid_source_age_ms"), None) is not None
                and (
                    str(row.get("bid_source") or "") == "fresh_rest_executable_bid"
                    or str(row.get("adopted_quote_source_type") or "") in {"0B", "0D"}
                )
                for row in trailing_transitions
            ),
            "quote_gap": any(
                _safe_float(row.get("ws_rest_gap_bps"), None) is not None
                for row in trailing_transitions
            ),
            "spread": any(
                _safe_float(row.get("executable_spread_bps"), None) is not None
                for row in trailing_transitions
            ),
            "ai_age": any(
                _safe_float(row.get("ai_score_age_sec"), None) is not None
                for row in trailing_transitions
            ),
            "ai_provider": any(
                str(row.get("ai_score_source") or "-") not in {"", "-", "missing"}
                and str(row.get("ai_score_data_quality") or "-")
                in {"fresh", "partial"}
                for row in trailing_transitions
            ),
            "nxt_0b_0d": any(
                row.get("nxt_trailing_bid_guard_applied") is not None
                for row in trailing_transitions
            ),
            "rest_bid": any(
                str(row.get("bid_source") or "") == "fresh_rest_executable_bid"
                for row in trailing_transitions
            ),
        }
        if role_gate == "unusable_neutral_only":
            ai_intervention = "unusable"
        elif role_gate == "missing":
            ai_intervention = "unobserved"
        else:
            ai_intervention = "eligible_causal_effect_unproven"

        flow_stages = [
            str(event.get("stage") or "")
            for event in timeline
            if str(event.get("stage") or "") in _FLOW_INTERVENTION_STAGES
        ]
        if "holding_flow_override_defer_exit" in flow_stages:
            flow_intervention = "deferred"
        elif "holding_flow_max_defer_bullish_extension" in flow_stages:
            flow_intervention = "deferred_extension"
        elif flow_stages:
            flow_intervention = "reviewed_exit_not_proven_changed"
        elif exit_signal.get("exit_decision_source") == "HOLDING_FLOW_OVERRIDE":
            flow_intervention = "unproven_source_label_only"
        else:
            flow_intervention = "not_observed"

        exact_fill_time = str(trade.get("exact_sell_fill_time") or "").strip()
        horizon_forbidden = bool(trade.get("sell_time_forbidden_for_intraday_horizon"))
        matching = post_sell_by_trade.get(trade_id, [])
        if not exact_fill_time or horizon_forbidden:
            post_sell_status = "not_observable_no_exact_fill_time"
        elif len(matching) > 1:
            post_sell_status = "source_gap_multiple_post_sell_candidates"
        elif not matching:
            post_sell_status = "not_recorded_or_unmatured"
        elif matching[0].get("evaluation_status") == "candidate_only":
            post_sell_status = "candidate_unmatured"
        elif matching[0].get("evaluation_status") == "source_gap_candidate_missing":
            post_sell_status = "source_gap_candidate_missing"
        else:
            post_sell_status = str(
                matching[0].get("minute_candle_source_quality") or "source_gap"
            )
            candidate_date = str(matching[0].get("signal_date") or "")
            candidate_time = str(matching[0].get("sell_time") or "")
            exact_bucket = f"{exact_fill_time[:10]} {exact_fill_time[11:16]}"
            candidate_bucket = f"{candidate_date} {candidate_time[:5]}"
            if not candidate_date or not candidate_time:
                post_sell_status = "source_gap_anchor_missing"
            elif exact_bucket != candidate_bucket:
                post_sell_status = "source_gap_anchor_bucket_mismatch"
            if (
                matching[0].get("strategy")
                and str(matching[0].get("strategy")).upper()
                != str(trade.get("strategy") or "").upper()
            ):
                post_sell_status = "source_gap_custody_mismatch"
            if not post_sell_status.startswith("source_gap"):
                post_sell_status = _post_sell_binding_gap(trade, matching[0]) or post_sell_status
            if post_sell_status == "pass" and not isinstance(
                matching[0].get("metrics_10m"), dict
            ):
                post_sell_status = "source_gap_missing_10m_metrics"
            if post_sell_status == "pass":
                sell_dt = _parse_dt(f"{candidate_date} {candidate_time}")
                evaluated_dt = _parse_dt(matching[0].get("evaluated_at"))
                horizon_metrics = [
                    matching[0].get(f"metrics_{minute}m") for minute in (1, 3, 5, 10)
                ]
                if (
                    sell_dt is None
                    or evaluated_dt is None
                    or evaluated_dt < sell_dt + timedelta(minutes=10)
                    or any(
                        not isinstance(metric, dict)
                        or _safe_int(metric.get("bars")) <= 0
                        for metric in horizon_metrics
                    )
                ):
                    post_sell_status = "source_gap_horizon_maturity_unproven"

        pnl = _safe_float(trade.get("realized_pnl_krw"), None)
        outcomes.append(
            {
                "record_id": trade_id,
                "rec_date": trade.get("rec_date"),
                "code": trade.get("code"),
                "strategy": trade.get("strategy"),
                "position_tag": trade.get("position_tag"),
                "buy_time": trade.get("buy_time"),
                "sell_time": trade.get("sell_time"),
                "completion_observed_date": trade.get("completion_observed_date"),
                "completion_day_basis": trade.get("completion_day_basis"),
                "terminal_population_scope": trade.get("terminal_population_scope"),
                "attempt_id": trade.get("attempt_id"),
                "sell_order_no": trade.get("sell_order_no"),
                "sell_execution_no": trade.get("sell_execution_no"),
                "sell_quantity_conserved": trade.get("sell_quantity_conserved"),
                "exact_sell_fill_time": exact_fill_time or None,
                "exit_rule": exit_rule,
                "exit_rule_provenance": "inferred" if inferred else "observed",
                "exit_class": (
                    "exit_rule_missing" if exit_rule in {"", "-", "unknown"} else
                    "exit_rule_inferred" if inferred else
                    "trailing_observed" if exit_rule == "scalp_trailing_take_profit" else
                    "other_exit_observed"
                ),
                "holding_score_role_gate": role_gate,
                "ai_intervention": ai_intervention,
                "flow_intervention": flow_intervention,
                "exit_threshold_status": threshold_status,
                "exit_threshold_key": threshold_fields.get("exit_threshold_key"),
                "exit_threshold_effective_pct": _safe_float(
                    threshold_fields.get("exit_threshold_effective_pct"), None
                ),
                "exit_threshold_observed_pct": _safe_float(
                    threshold_fields.get("exit_threshold_observed_pct"), None
                ),
                "exit_threshold_provenance_status": threshold_fields.get(
                    "exit_threshold_provenance_status"
                ),
                "exit_threshold_trailing_start_pct": _safe_float(
                    threshold_fields.get("exit_threshold_trailing_start_pct"), None
                ),
                "exit_threshold_trailing_arm_observed_pct": _safe_float(
                    threshold_fields.get("exit_threshold_trailing_arm_observed_pct"),
                    None,
                ),
                "exit_threshold_strong_score_effective": _safe_float(
                    threshold_fields.get("exit_threshold_strong_score_effective"),
                    None,
                ),
                "exit_threshold_ai_score_observed": _safe_float(
                    threshold_fields.get("exit_threshold_ai_score_observed"), None
                ),
                "exit_threshold_ai_score_usable": threshold_fields.get(
                    "exit_threshold_ai_score_usable"
                ),
                "exit_threshold_peak_price": _safe_int(
                    threshold_fields.get("exit_threshold_peak_price"), 0
                ),
                "exit_threshold_executable_bid": _safe_int(
                    threshold_fields.get("exit_threshold_executable_bid"), 0
                ),
                "exit_threshold_bid_source": threshold_fields.get(
                    "exit_threshold_bid_source"
                ),
                "exit_threshold_trigger_kind": threshold_fields.get(
                    "exit_threshold_trigger_kind"
                ),
                "trailing_policy_value_sha256": policy_sha or None,
                "trailing_start_by_market_sha256": market_sha or None,
                "trailing_start_by_market_values": market_values,
                "trailing_policy_values": policy_values if policy_values_valid else None,
                "trailing_policy_date": policy_date or None,
                "trailing_policy_binding": policy_binding,
                "trailing_operational_value_sha256": (
                    operational_sha if operational_values_valid else None
                ),
                "trailing_operational_values": (
                    first_operational_values if operational_values_valid else None
                ),
                "trailing_operational_sources": (
                    first_operational_sources if operational_values_valid else None
                ),
                "trailing_operational_binding": operational_binding,
                "trailing_replay_source_status": trailing_replay_status,
                "trailing_start_market_replay": start_replay,
                "trailing_observation_grid_version": (
                    next(iter(transition_grid_versions))
                    if len(transition_grid_versions) == 1 else None
                ),
                "trailing_observation_coverage_exhausted": coverage_exhausted,
                "trailing_observation_telemetry_gap": telemetry_gap,
                "trailing_holding_start_observed": bool(holding_start_events),
                "trailing_observation_first_sequence": (
                    transition_sequences[0] if transition_sequences else None
                ),
                "trailing_observation_last_sequence": (
                    transition_sequences[-1] if transition_sequences else None
                ),
                "trailing_operational_inputs": operational_inputs,
                "trailing_replay_source_reference": {
                    "snapshot_kind": "trade_review",
                    "record_id": trade_id,
                    "source_date": trade.get("completion_observed_date"),
                    "pipeline_event_source_sha256": trade.get(
                        "trailing_event_source_sha256"
                    ),
                },
                "tp_alternative_observed_rules": alternative_observations,
                "trailing_input_transition_count": len(trailing_transitions),
                "trailing_first_arm_at_epoch": _safe_float(
                    first_arm.get("evaluation_at_epoch"), None
                ),
                "trailing_first_arm_ws_trade_at_epoch": _safe_float(
                    first_arm.get("ws_trade_received_at_epoch"), None
                ),
                "trailing_first_arm_ws_trade_clock_provenance": first_arm.get(
                    "ws_trade_clock_provenance"
                ),
                "trailing_first_trigger_at_epoch": _safe_float(
                    first_trigger.get("evaluation_at_epoch"), None
                ),
                "trailing_first_trigger_bid_at_epoch": _safe_float(
                    first_trigger.get("bid_source_received_at_epoch"), None
                ),
                "trailing_first_trigger_bid_clock_provenance": first_trigger.get(
                    "bid_source_clock_provenance"
                ),
                "trailing_source_gap_transition_count": trailing_source_gap_count,
                "terminal_decision_authority": trade.get("terminal_decision_authority"),
                "profit_rate": _safe_float(trade.get("profit_rate"), None),
                "buy_fill_amount": _safe_float(trade.get("buy_fill_amount"), None),
                "realized_pnl_krw": int(round(pnl)) if pnl is not None else None,
                "realized_pnl_krw_source": trade.get("realized_pnl_krw_source"),
                "modeled_realized_pnl_krw": trade.get("modeled_realized_pnl_krw"),
                "sell_time_precision": trade.get("sell_time_precision"),
                "post_sell_ids": [row["post_sell_id"] for row in matching],
                "post_sell_status": post_sell_status,
                "post_sell_layer": (
                    "pass" if post_sell_status == "pass" else
                    "partial_window" if post_sell_status == "partial_window" else
                    "unmatured" if post_sell_status in {
                        "not_recorded_or_unmatured", "candidate_unmatured"
                    } else
                    "not_observable_no_exact_fill_time" if post_sell_status ==
                    "not_observable_no_exact_fill_time" else "source_gap"
                ),
                "post_sell_outcome_diagnostic": (
                    matching[0].get("outcome") if len(matching) == 1 else None
                ),
            }
        )

    exact = [row for row in outcomes if row["realized_pnl_krw"] is not None]
    by_rule: dict[str, dict] = {}
    for rule in sorted({row["exit_rule"] for row in outcomes}):
        rule_rows = [row for row in outcomes if row["exit_rule"] == rule]
        exact_rows = [row for row in rule_rows if row["realized_pnl_krw"] is not None]
        by_rule[rule] = {
            "completed_valid_trades": len(rule_rows),
            "exact_cost_trades": len(exact_rows),
            "missing_exact_cost_trades": len(rule_rows) - len(exact_rows),
            "exact_cost_subset_pnl_krw": (
                sum(row["realized_pnl_krw"] for row in exact_rows)
                if exact_rows
                else None
            ),
            "whole_rule_pnl_krw": (
                sum(row["realized_pnl_krw"] for row in exact_rows)
                if len(exact_rows) == len(rule_rows)
                else None
            ),
            "observed_exit_signal_trades": sum(
                row["exit_rule_provenance"] == "observed" for row in rule_rows
            ),
        }
    coverage = {
        "metric_role": "source_quality_gate",
        "decision_authority": "holding_exit_observation_only",
        "window_policy": "completed_position_exact_terminal",
        "sample_floor": "all_completed_positions_with_exact_cost",
        "primary_decision_metric": "cost_adjusted_realized_pnl_when_complete",
        "source_quality_gate": "full_census_exact_cost_and_source_provenance",
        "forbidden_uses": "threshold_apply|order_change|gross_ev_substitution",
        "completed_valid_trades": len(outcomes),
        "exit_class_ids": {
            label: [row["record_id"] for row in outcomes if row["exit_class"] == label]
            for label in ("trailing_observed", "other_exit_observed",
                          "exit_rule_inferred", "exit_rule_missing")
        },
        "post_sell_layer_ids": {
            label: [row["record_id"] for row in outcomes if row["post_sell_layer"] == label]
            for label in ("pass", "partial_window", "unmatured",
                          "not_observable_no_exact_fill_time", "source_gap")
        },
        "exact_cost_trades": len(exact),
        "missing_exact_cost_trades": len(outcomes) - len(exact),
        "exact_cost_subset_pnl_krw": (
            sum(row["realized_pnl_krw"] for row in exact) if exact else None
        ),
        "whole_cohort_pnl_krw": (
            sum(row["realized_pnl_krw"] for row in exact)
            if len(exact) == len(outcomes) and outcomes
            else None
        ),
        "observed_exit_signal_trades": sum(
            row["exit_rule_provenance"] == "observed" for row in outcomes
        ),
        "effective_threshold_receipt_trades": sum(
            row["exit_threshold_status"] == "effective_value_observed"
            for row in outcomes
        ),
        "trailing_direct_input_receipt_trades": sum(
            row["exit_rule"] == "scalp_trailing_take_profit"
            and row["exit_rule_provenance"] == "observed"
            and row["exit_threshold_trailing_start_pct"] is not None
            and row["exit_threshold_strong_score_effective"] is not None
            and row["exit_threshold_peak_price"] > 0
            and row["exit_threshold_executable_bid"] > 0
            and row["exit_threshold_trigger_kind"]
            == "trailing_peak_worsen_floor"
            for row in outcomes
        ),
        "trailing_input_transition_trades": sum(
            row["trailing_input_transition_count"] > 0 for row in outcomes
        ),
        "trailing_first_arm_receipt_trades": sum(
            row["trailing_first_arm_at_epoch"] is not None for row in outcomes
        ),
        "trailing_first_arm_trade_clock_trades": sum(
            row["trailing_first_arm_ws_trade_at_epoch"] is not None
            and row["trailing_first_arm_ws_trade_clock_provenance"]
            == "type_specific_0B"
            for row in outcomes
        ),
        "trailing_first_trigger_bid_clock_trades": sum(
            row["trailing_first_trigger_bid_at_epoch"] is not None
            and row["trailing_first_trigger_bid_clock_provenance"]
            in {"type_specific_0D", "rest_receive"}
            for row in outcomes
        ),
        "flow_deferred_trades": sum(
            row["flow_intervention"] in {"deferred", "deferred_extension"}
            for row in outcomes
        ),
        "full_post_sell_observation_trades": sum(
            row["post_sell_status"] == "pass" for row in outcomes
        ),
        "by_exit_rule": by_rule,
    }
    return outcomes, coverage


def _metric_window(row: dict, window: str) -> dict:
    metrics = row.get(window) or {}
    return metrics if isinstance(metrics, dict) else {}


def _metric_float(row: dict, window: str, key: str) -> float:
    return float(_safe_float(_metric_window(row, window).get(key), 0.0) or 0.0)


def _recovery_to_buy_threshold_pct(row: dict) -> float:
    buy_price = float(_safe_float(row.get("buy_price"), 0.0) or 0.0)
    sell_price = float(_safe_float(row.get("sell_price"), 0.0) or 0.0)
    if buy_price <= 0 or sell_price <= 0:
        return 0.0
    return round(((buy_price / sell_price) - 1.0) * 100.0, 3)


def _rebound_above_sell(row: dict, window: str) -> bool:
    metrics = _metric_window(row, window)
    if "rebound_above_sell" in metrics:
        return bool(metrics.get("rebound_above_sell"))
    return _metric_float(row, window, "mfe_pct") > 0.0


def _rebound_above_buy(row: dict, window: str) -> bool:
    metrics = _metric_window(row, window)
    if "rebound_above_buy" in metrics:
        return bool(metrics.get("rebound_above_buy"))
    return _metric_float(row, window, "mfe_pct") >= _recovery_to_buy_threshold_pct(row)


def _enrich_post_sell_row(*, candidate: dict, evaluation: dict) -> dict:
    merged = {**(candidate or {}), **(evaluation or {})}
    metrics_10m = _metric_window(merged, "metrics_10m")
    metrics_1m = _metric_window(merged, "metrics_1m")
    metrics_3m = _metric_window(merged, "metrics_3m")
    metrics_5m = _metric_window(merged, "metrics_5m")
    metrics_20m = _metric_window(merged, "metrics_20m")
    profit_rate = float(_safe_float(merged.get("profit_rate"), 0.0) or 0.0)
    sell_price = float(_safe_float(merged.get("sell_price"), 0.0) or 0.0)
    buy_qty = _safe_int(merged.get("buy_qty"), 0)
    extra_upside_pct = max(
        0.0, float(_safe_float(metrics_10m.get("mfe_pct"), 0.0) or 0.0)
    )
    potential_peak_profit_rate = round(profit_rate + extra_upside_pct, 3)
    capture_efficiency_pct = (
        round(
            max(0.0, min(100.0, (profit_rate / potential_peak_profit_rate) * 100.0)), 1
        )
        if potential_peak_profit_rate > 0
        else 0.0
    )
    return {
        **merged,
        "post_sell_id": str(merged.get("post_sell_id") or ""),
        "recommendation_id": _safe_int(merged.get("recommendation_id"), 0),
        "signal_date": str(merged.get("signal_date") or ""),
        "stock_code": str(merged.get("stock_code") or ""),
        "stock_name": str(merged.get("stock_name") or ""),
        "strategy": str(merged.get("strategy") or ""),
        "position_tag": str(merged.get("position_tag") or ""),
        "exit_rule": str(merged.get("exit_rule") or "-"),
        "outcome": str(merged.get("outcome") or "NEUTRAL").upper(),
        "profit_rate": round(profit_rate, 3),
        "buy_price": _safe_int(merged.get("buy_price"), 0),
        "sell_price": _safe_int(merged.get("sell_price"), 0),
        "buy_qty": buy_qty,
        "peak_profit": round(
            float(_safe_float(merged.get("peak_profit"), 0.0) or 0.0), 3
        ),
        "held_sec": _safe_int(merged.get("held_sec"), 0),
        "extra_upside_10m_pct": round(extra_upside_pct, 3),
        "extra_upside_10m_krw_est": (
            int(round(sell_price * buy_qty * (extra_upside_pct / 100.0)))
            if sell_price > 0 and buy_qty > 0
            else 0
        ),
        "potential_peak_profit_rate_10m": float(potential_peak_profit_rate),
        "capture_efficiency_pct": float(capture_efficiency_pct),
        "recovery_to_buy_threshold_pct": _recovery_to_buy_threshold_pct(merged),
        "rebound_above_sell_1m": _rebound_above_sell(merged, "metrics_1m"),
        "rebound_above_sell_3m": _rebound_above_sell(merged, "metrics_3m"),
        "rebound_above_sell_5m": _rebound_above_sell(merged, "metrics_5m"),
        "rebound_above_sell_10m": _rebound_above_sell(merged, "metrics_10m"),
        "rebound_above_sell_20m": _rebound_above_sell(merged, "metrics_20m"),
        "rebound_above_buy_1m": _rebound_above_buy(merged, "metrics_1m"),
        "rebound_above_buy_3m": _rebound_above_buy(merged, "metrics_3m"),
        "rebound_above_buy_5m": _rebound_above_buy(merged, "metrics_5m"),
        "rebound_above_buy_10m": _rebound_above_buy(merged, "metrics_10m"),
        "rebound_above_buy_20m": _rebound_above_buy(merged, "metrics_20m"),
        "mfe_1m_pct": round(
            float(_safe_float(metrics_1m.get("mfe_pct"), 0.0) or 0.0), 3
        ),
        "mfe_3m_pct": round(
            float(_safe_float(metrics_3m.get("mfe_pct"), 0.0) or 0.0), 3
        ),
        "mfe_5m_pct": round(
            float(_safe_float(metrics_5m.get("mfe_pct"), 0.0) or 0.0), 3
        ),
        "mfe_10m_pct": round(
            float(_safe_float(metrics_10m.get("mfe_pct"), 0.0) or 0.0), 3
        ),
        "mfe_20m_pct": round(
            float(_safe_float(metrics_20m.get("mfe_pct"), 0.0) or 0.0), 3
        ),
        "close_ret_1m_pct": round(
            float(_safe_float(metrics_1m.get("close_ret_pct"), 0.0) or 0.0), 3
        ),
        "close_ret_3m_pct": round(
            float(_safe_float(metrics_3m.get("close_ret_pct"), 0.0) or 0.0), 3
        ),
        "close_ret_5m_pct": round(
            float(_safe_float(metrics_5m.get("close_ret_pct"), 0.0) or 0.0), 3
        ),
        "close_ret_10m_pct": round(
            float(_safe_float(metrics_10m.get("close_ret_pct"), 0.0) or 0.0), 3
        ),
        "close_ret_20m_pct": round(
            float(_safe_float(metrics_20m.get("close_ret_pct"), 0.0) or 0.0), 3
        ),
        "hit_up_05_1m": bool(metrics_1m.get("hit_up_05", False)),
        "hit_up_05_3m": bool(metrics_3m.get("hit_up_05", False)),
        "hit_up_05_5m": bool(metrics_5m.get("hit_up_05", False)),
        "hit_up_05_10m": bool(metrics_10m.get("hit_up_05", False)),
        "hit_up_05_20m": bool(metrics_20m.get("hit_up_05", False)),
        "hit_up_10_1m": bool(metrics_1m.get("hit_up_10", False)),
        "hit_up_10_3m": bool(metrics_3m.get("hit_up_10", False)),
        "hit_up_10_5m": bool(metrics_5m.get("hit_up_10", False)),
        "hit_up_10_10m": bool(metrics_10m.get("hit_up_10", False)),
        "hit_up_10_20m": bool(metrics_20m.get("hit_up_10", False)),
        "same_symbol_soft_stop_cooldown_would_block": bool(
            merged.get("same_symbol_soft_stop_cooldown_would_block", False)
        ),
    }


def _summarize_exit_rule_quality(
    post_sell_rows: list[dict], valid_trades: list[dict]
) -> list[dict]:
    post_sell_by_rule: dict[str, list[dict]] = defaultdict(list)
    for row in post_sell_rows:
        post_sell_by_rule[_exit_group(str(row.get("exit_rule") or "-"))].append(row)

    trades_by_rule: dict[str, list[dict]] = defaultdict(list)
    for row in valid_trades:
        trades_by_rule[_exit_group(_exit_rule_from_trade(row))].append(row)

    rows: list[dict] = []
    for exit_rule in TARGET_EXIT_RULES:
        quality_rows = post_sell_by_rule.get(exit_rule, [])
        completed_rows = trades_by_rule.get(exit_rule, [])
        outcomes = Counter(
            str(row.get("outcome") or "NEUTRAL").upper() for row in quality_rows
        )
        evaluated = len(quality_rows)
        completed_profits = [
            float(_safe_float(row.get("profit_rate"), 0.0) or 0.0)
            for row in completed_rows
            if _is_valid_completed_trade(row)
        ]
        capture_values = [
            float(_safe_float(row.get("capture_efficiency_pct"), 0.0) or 0.0)
            for row in quality_rows
            if float(_safe_float(row.get("potential_peak_profit_rate_10m"), 0.0) or 0.0)
            > 0
        ]
        rows.append(
            {
                "exit_rule": exit_rule,
                "evaluated_post_sell": evaluated,
                "outcome_counts": {
                    "MISSED_UPSIDE": int(outcomes.get("MISSED_UPSIDE", 0)),
                    "GOOD_EXIT": int(outcomes.get("GOOD_EXIT", 0)),
                    "NEUTRAL": int(outcomes.get("NEUTRAL", 0)),
                },
                "missed_upside_rate": _ratio(
                    outcomes.get("MISSED_UPSIDE", 0), evaluated
                ),
                "good_exit_rate": _ratio(outcomes.get("GOOD_EXIT", 0), evaluated),
                "capture_efficiency_avg_pct": _avg(capture_values),
                "avg_extra_upside_10m_pct": _avg(
                    [
                        float(_safe_float(row.get("extra_upside_10m_pct"), 0.0) or 0.0)
                        for row in quality_rows
                    ]
                ),
                "completed_valid_trades": len(completed_profits),
                "completed_valid_avg_profit_rate": _avg(completed_profits),
                "completed_valid_realized_pnl_krw": _summarize_completed_trades(
                    completed_rows
                )["realized_pnl_krw"],
            }
        )
    return rows






def _build_trailing_threshold_readiness(
    outcomes: list[dict], open_positions: list[dict] | None = None,
    *, completed_valid_ids: list[str] | None = None,
) -> dict:
    """Expose source-qualified denominators; never infer a tuning proposal."""

    trailing = [
        row for row in outcomes if row["exit_class"] == "trailing_observed"
    ]
    direct = [
        row for row in trailing
        if row["exit_rule_provenance"] == "observed"
        and row.get("terminal_population_scope") == "real_record_bound"
    ]
    inputs = [
        row
        for row in direct
        if row["exit_threshold_status"] == "effective_value_observed"
        and row["exit_threshold_peak_price"] > 0
        and row["exit_threshold_executable_bid"] > 0
        and row["exit_threshold_trailing_start_pct"] is not None
        and row["exit_threshold_strong_score_effective"] is not None
    ]
    exact = [row for row in inputs if row["realized_pnl_krw"] is not None]
    forward = [row for row in exact if row["post_sell_status"] == "pass"]
    source_linked = [
        row for row in outcomes
        if row.get("trailing_replay_source_status")
        == "grid_source_linked_paired_replay_pending"
    ]
    fully_paired = [
        row for row in source_linked
        if not (row.get("trailing_start_market_replay") or {}).get("source_gap")
        and all(
            candidate.get("paired_delta_pnl_krw") is not None
            for market in (row.get("trailing_start_market_replay") or {})
                .get("markets", {}).values()
            for candidate in market.values()
        )
        and (row.get("trailing_start_market_replay") or {}).get("markets")
    ]
    arm = [
        row for row in source_linked
        if row["trailing_first_arm_at_epoch"] is not None
    ]
    score = [
        row
        for row in source_linked
        if str(row["exit_threshold_ai_score_usable"]).strip().lower()
        in {"true", "1"}
        and row["exit_threshold_ai_score_observed"] is not None
        and (row.get("trailing_operational_inputs") or {}).get("ai_provider")
    ]
    funnel = {
        "completed_valid_ids": (
            completed_valid_ids if completed_valid_ids is not None
            else [row["record_id"] for row in outcomes]
        ),
        "strict_completed_position_ids": [row["record_id"] for row in outcomes],
        "competing_exit_ids": [row["record_id"] for row in outcomes
                               if row["exit_class"] == "other_exit_observed"],
        "trailing_exit_ids": [row["record_id"] for row in trailing],
        "real_completed_ids": [
            row["record_id"] for row in outcomes
            if row.get("terminal_population_scope") == "real_record_bound"
        ],
        "terminal_custody_unproven_ids": [
            row["record_id"] for row in outcomes
            if row.get("terminal_population_scope") != "real_record_bound"
        ],
        "direct_signal_ids": [row["record_id"] for row in direct],
        "effective_input_ids": [row["record_id"] for row in inputs],
        "exact_cost_ids": [row["record_id"] for row in exact],
        "mature_forward_ids": [row["record_id"] for row in forward],
        "paired_replay_eligible_ids": [row["record_id"] for row in fully_paired],
        "censored_open_position_ids": [
            str(row["id"]) for row in (open_positions or [])
            if row.get("real_position_observed")
        ],
        "open_position_custody_unproven_ids": [
            str(row["id"]) for row in (open_positions or [])
            if not row.get("real_position_observed")
        ],
        "grid_source_linked_ids": [
            row["record_id"] for row in outcomes
            if row.get("trailing_replay_source_status")
            == "grid_source_linked_paired_replay_pending"
        ],
        "policy_manifest_bound_ids": [
            row["record_id"] for row in outcomes
            if (row.get("trailing_policy_binding") or {}).get("status")
            == "manifest_value_hash_matched_no_pid_proof"
        ],
    }
    axis_inputs = {
        "SCALP_TRAILING_START_PCT": (arm, "pre_arm_quote_path_and_paired_replay_missing"),
        "SCALP_TRAILING_STRONG_AI_SCORE": (
            score,
            "score_ttl_provider_lineage_and_paired_replay_missing",
        ),
        "SCALP_TRAILING_LIMIT_WEAK": (
            [row for row in forward if row in source_linked and row["exit_threshold_key"] == "SCALP_TRAILING_LIMIT_WEAK"],
            "first_crossing_fill_cost_and_holdout_replay_missing",
        ),
        "SCALP_TRAILING_LIMIT_STRONG": (
            [row for row in forward if row in source_linked and row["exit_threshold_key"] == "SCALP_TRAILING_LIMIT_STRONG"],
            "first_crossing_fill_cost_and_holdout_replay_missing",
        ),
    }
    operational_requirements = {
        "KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS": None,
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS": "quote_age",
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_REST_AGE_MS": "rest_bid",
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS": "spread",
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS": "rest_bid",
        "HOLDING_EXIT_REST_QUOTE_FALLBACK_MIN_INTERVAL_SEC": "rest_bid",
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MAX_0D_AGE_MS": "nxt_0b_0d",
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MIN_0B_STALE_MS": "nxt_0b_0d",
        "AI_HOLDING_CRITICAL_COOLDOWN": "ai_age",
        "AI_HOLDING_CRITICAL_MIN_COOLDOWN": "ai_age",
        "AI_HOLDING_MIN_COOLDOWN": "ai_age",
        "AI_HOLDING_MAX_COOLDOWN": "ai_age",
        "SCALP_SAFE_PROFIT": "ai_age",
        "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC": "ai_age",
        "AI_HOLDING_NEAR_SAFE_PROFIT_BAND_PCT": "ai_age",
        "AI_HOLDING_CRITICAL_PRICE_TRIGGER_PCT": "ai_age",
        "AI_HOLDING_NORMAL_PRICE_TRIGGER_PCT": "ai_age",
    }
    operational_contracts = {
        "KORSTOCKSCAN_SCALP_FAST_EXIT_POLL_MS": ("ms", "poll_interval=max(50,value)"),
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_WS_AGE_MS": ("ms", "ws_age<=value"),
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_MAX_REST_AGE_MS": ("ms", "rest_age<=value"),
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_WARN_GAP_BPS": ("bps", "gap_or_spread>value_requires_recheck"),
        "KORSTOCKSCAN_QUOTE_CONSISTENCY_EMERGENCY_REST_TIMEOUT_MS": ("ms", "rest_request_timeout=value"),
        "HOLDING_EXIT_REST_QUOTE_FALLBACK_MIN_INTERVAL_SEC": ("sec", "rest_retry_elapsed>=max(3,value)"),
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MAX_0D_AGE_MS": ("ms", "nxt_0d_age<=value"),
        "KORSTOCKSCAN_SCALP_NXT_TRAILING_BID_GUARD_MIN_0B_STALE_MS": ("ms", "nxt_0b_age>=value"),
        "AI_HOLDING_CRITICAL_COOLDOWN": ("sec", "critical_score_age<=value"),
        "AI_HOLDING_CRITICAL_MIN_COOLDOWN": ("sec", "critical_recheck_elapsed>value"),
        "AI_HOLDING_MIN_COOLDOWN": ("sec", "normal_recheck_elapsed>value"),
        "AI_HOLDING_MAX_COOLDOWN": ("sec", "normal_recheck_elapsed>value_forced"),
        "SCALP_SAFE_PROFIT": ("pct", "profit_near_or_above_value_changes_ai_zone"),
        "AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC": ("sec", "ws_snapshot_age<=value"),
        "AI_HOLDING_NEAR_SAFE_PROFIT_BAND_PCT": ("pct_point", "abs(profit-safe_profit)<=value"),
        "AI_HOLDING_CRITICAL_PRICE_TRIGGER_PCT": ("pct", "critical_price_change>=value"),
        "AI_HOLDING_NORMAL_PRICE_TRIGGER_PCT": ("pct", "normal_price_change>=value"),
    }
    operational_axes = {}
    for key, required_input in operational_requirements.items():
        observed_rows = [
            row for row in outcomes
            if key in (row.get("trailing_operational_values") or {})
        ]
        connected_rows = [
            row for row in observed_rows
            if row.get("trailing_replay_source_status")
            == "grid_source_linked_paired_replay_pending"
            and (
                required_input is None
                or (row.get("trailing_operational_inputs") or {}).get(required_input)
            )
        ]
        operational_axes[key] = {
            "unit": operational_contracts[key][0],
            "consumer_comparison": operational_contracts[key][1],
            "owner": (
                "shared_quote_safety" if "QUOTE_CONSISTENCY" in key
                or "REST_QUOTE" in key else
                "holding_ai_shared" if key.startswith("AI_HOLDING")
                or key == "SCALP_SAFE_PROFIT" else
                "scalp_exit_input_quality"
            ),
            "observed_value_ids": [row["record_id"] for row in observed_rows],
            "source_connected_ids": [row["record_id"] for row in connected_rows],
            "effective_values": sorted({
                row["trailing_operational_values"][key] for row in observed_rows
            }),
            "effective_value_sha256": sorted({
                row["trailing_operational_value_sha256"] for row in observed_rows
                if row.get("trailing_operational_value_sha256")
            }),
            "effective_sources": sorted({
                (row.get("trailing_operational_sources") or {}).get(key, "source_gap")
                for row in observed_rows
            }),
            "candidate_value": None,
            "eligible_for_live_review": False,
            "blocker": (
                "poll_source_tick_and_stop_latency_counterfactual_missing"
                if required_input is None
                else "shared_owner_safety_and_paired_replay_missing"
            ),
            "decision_authority": "report_only_shared_owner_review_required",
        }
    return {
        "status": "source_gap_paired_replay_unavailable",
        "decision_authority": "report_only_no_threshold_apply",
        "funnel_ids": funnel,
        "operational_axes": operational_axes,
        "axes": {
            key: {
                "unit": "score" if key == "SCALP_TRAILING_STRONG_AI_SCORE" else "pct",
                "consumer_comparison": (
                    "usable_score>=value_selects_strong"
                    if key == "SCALP_TRAILING_STRONG_AI_SCORE" else
                    "peak_profit>=value_arms"
                    if key == "SCALP_TRAILING_START_PCT" else
                    "armed_and_peak_to_bid_drawdown>=value_triggers"
                ),
                "owner": "scalp_trailing_take_profit",
                "qualified_input_ids": [row["record_id"] for row in rows],
                "qualified_input_count": len(rows),
                "policy_manifest_bound_ids": [
                    row["record_id"] for row in rows
                    if (row.get("trailing_policy_binding") or {}).get("status")
                    == "manifest_value_hash_matched_no_pid_proof"
                ],
                "effective_values": sorted({
                    row["trailing_policy_values"][key]
                    for row in rows
                    if isinstance(row.get("trailing_policy_values"), dict)
                    and key in row["trailing_policy_values"]
                }),
                "effective_value_sha256": sorted({
                    row["trailing_policy_value_sha256"]
                    for row in rows if row.get("trailing_policy_value_sha256")
                }),
                "effective_sources": sorted({
                    (row.get("trailing_policy_binding") or {}).get("sources", {}).get(
                        key, "source_gap"
                    )
                    for row in rows
                    if isinstance(
                        (row.get("trailing_policy_binding") or {}).get("sources"), dict
                    )
                }),
                "candidate_value": None,
                "eligible_for_live_review": False,
                "blocker": blocker,
            }
            for key, (rows, blocker) in axis_inputs.items()
        },
    }


def _build_rebound_windows(rows: list[dict]) -> list[dict]:
    windows: list[dict] = []
    for label in ("1m", "3m", "5m", "10m", "20m"):
        window_total = sum(1 for row in rows if f"mfe_{label}_pct" in row)
        if window_total <= 0:
            continue
        mfe_values = [
            float(_safe_float(row.get(f"mfe_{label}_pct"), 0.0) or 0.0) for row in rows
        ]
        close_values = [
            float(_safe_float(row.get(f"close_ret_{label}_pct"), 0.0) or 0.0)
            for row in rows
        ]
        above_sell = sum(
            1 for row in rows if bool(row.get(f"rebound_above_sell_{label}"))
        )
        above_buy = sum(
            1 for row in rows if bool(row.get(f"rebound_above_buy_{label}"))
        )
        hit_up_05 = sum(1 for row in rows if bool(row.get(f"hit_up_05_{label}")))
        hit_up_10 = sum(1 for row in rows if bool(row.get(f"hit_up_10_{label}")))
        windows.append(
            {
                "window": label,
                "total": int(window_total),
                "rebound_above_sell_count": int(above_sell),
                "rebound_above_sell_rate": _ratio(above_sell, window_total),
                "rebound_above_buy_count": int(above_buy),
                "rebound_above_buy_rate": _ratio(above_buy, window_total),
                "hit_up_05_count": int(hit_up_05),
                "hit_up_05_rate": _ratio(hit_up_05, window_total),
                "hit_up_10_count": int(hit_up_10),
                "hit_up_10_rate": _ratio(hit_up_10, window_total),
                "mfe_ge_0_5_count": sum(1 for value in mfe_values if value >= 0.5),
                "mfe_ge_0_5_rate": _ratio(
                    sum(1 for value in mfe_values if value >= 0.5), window_total
                ),
                "mfe_ge_1_0_count": sum(1 for value in mfe_values if value >= 1.0),
                "mfe_ge_1_0_rate": _ratio(
                    sum(1 for value in mfe_values if value >= 1.0), window_total
                ),
                "avg_mfe_pct": _avg(mfe_values),
                "avg_close_ret_pct": _avg(close_values),
            }
        )
    return windows


def _build_hard_stop_auxiliary(
    post_sell_rows: list[dict], valid_trades: list[dict]
) -> dict:
    hard_rules = {"scalp_preset_hard_stop_pct", "scalp_hard_stop_pct"}
    rows = [
        row
        for row in post_sell_rows
        if _exit_group(str(row.get("exit_rule") or "-")) in hard_rules
    ]
    completed_rows = [
        row
        for row in valid_trades
        if _exit_group(_exit_rule_from_trade(row)) in hard_rules
        and _is_valid_completed_trade(row)
    ]
    outcomes = Counter(str(row.get("outcome") or "NEUTRAL").upper() for row in rows)
    by_rule = Counter(_exit_group(str(row.get("exit_rule") or "-")) for row in rows)
    completed_profits = [
        float(_safe_float(row.get("profit_rate"), 0.0) or 0.0) for row in completed_rows
    ]
    return {
        "candidate_id": "hard_stop_whipsaw_aux",
        "priority": "parking_auxiliary",
        "basis": "하드스탑은 극단 손실 방어선이므로 표본이 작거나 반등이 보여도 soft_stop보다 먼저 완화하지 않는다.",
        "evaluated_post_sell": len(rows),
        "exit_rule_counts": [
            {"label": key, "count": value} for key, value in by_rule.most_common()
        ],
        "outcome_counts": {
            "MISSED_UPSIDE": int(outcomes.get("MISSED_UPSIDE", 0)),
            "GOOD_EXIT": int(outcomes.get("GOOD_EXIT", 0)),
            "NEUTRAL": int(outcomes.get("NEUTRAL", 0)),
        },
        "rebound_windows": _build_rebound_windows(rows),
        "completed_valid_trades": len(completed_rows),
        "completed_valid_avg_profit_rate": _avg(completed_profits),
        "completed_valid_realized_pnl_krw": _summarize_completed_trades(completed_rows)[
            "realized_pnl_krw"
        ],
        "live_priority": "soft_stop 이후 보조 관찰. hard stop 완화 canary는 severe-loss guard 훼손 리스크 때문에 금지.",
    }


def _build_soft_stop_rebound(
    post_sell_rows: list[dict],
    same_symbol_reentry: dict,
    valid_trades: list[dict],
) -> dict:
    rows = [
        row
        for row in post_sell_rows
        if _exit_group(str(row.get("exit_rule") or "-")) == "scalp_soft_stop_pct"
    ]
    total = len(rows)
    rebound_sell_rate = _ratio(
        sum(1 for row in rows if bool(row.get("rebound_above_sell_10m"))), total
    )
    rebound_buy_rate = _ratio(
        sum(1 for row in rows if bool(row.get("rebound_above_buy_10m"))), total
    )
    cooldown_rate = _ratio(
        sum(
            1
            for row in rows
            if bool(row.get("same_symbol_soft_stop_cooldown_would_block"))
        ),
        total,
    )
    soft_reentry_losses = int(
        same_symbol_reentry.get("after_soft_stop_next_loss_count", 0) or 0
    )
    whipsaw_windows = _build_rebound_windows(rows)
    whipsaw_10m = next((row for row in whipsaw_windows if row["window"] == "10m"), {})
    whipsaw_signal = bool(
        whipsaw_10m
        and (
            float(whipsaw_10m.get("rebound_above_sell_rate", 0.0)) >= 50.0
            or float(whipsaw_10m.get("mfe_ge_0_5_rate", 0.0)) >= 30.0
        )
    )
    if rebound_buy_rate >= 50.0:
        recommendation = "cooldown live 금지, threshold/AI 재판정 후보"
    elif whipsaw_signal:
        recommendation = "soft_stop whipsaw confirmation canary 후보"
    elif (
        rebound_sell_rate >= 50.0
        and rebound_buy_rate < 50.0
        and soft_reentry_losses > 0
    ):
        recommendation = "same-symbol cooldown canary 후보"
    else:
        recommendation = "관찰 지속"
    return {
        "candidate_id": "soft_stop_rebound_split",
        "priority": 1,
        "priority_basis": "soft_stop completed_valid 손익 훼손이 가장 크므로 보유/청산 pain point 1순위다. 단, live 조작점은 rebound/reentry 조건으로 분리한다.",
        "total_soft_stop": total,
        "rebound_above_sell_10m_rate": rebound_sell_rate,
        "rebound_above_buy_10m_rate": rebound_buy_rate,
        "cooldown_would_block_rate": cooldown_rate,
        "same_symbol_reentry_loss_count": soft_reentry_losses,
        "whipsaw_signal": whipsaw_signal,
        "whipsaw_windows": whipsaw_windows,
        "hard_stop_auxiliary": _build_hard_stop_auxiliary(post_sell_rows, valid_trades),
        "recommendation": recommendation,
        "cooldown_live_allowed": bool(
            rebound_sell_rate >= 50.0
            and rebound_buy_rate < 50.0
            and soft_reentry_losses > 0
        ),
    }


def _build_same_symbol_reentry(valid_trades: list[dict]) -> dict:
    by_code: dict[str, list[dict]] = defaultdict(list)
    for row in valid_trades:
        code = str(row.get("code") or "").strip()
        if code:
            by_code[code].append(row)

    reentries: list[dict] = []
    for code, rows in by_code.items():
        ordered = sorted(
            rows, key=lambda item: _parse_dt(item.get("buy_time")) or datetime.min
        )
        for prev, next_trade in zip(ordered, ordered[1:]):
            prev_sell_dt = _parse_dt(prev.get("sell_time"))
            next_buy_dt = _parse_dt(next_trade.get("buy_time"))
            if not prev_sell_dt or not next_buy_dt or next_buy_dt < prev_sell_dt:
                continue
            gap_min = (next_buy_dt - prev_sell_dt).total_seconds() / 60.0
            if gap_min > 60.0:
                continue
            prev_rule = _exit_group(_exit_rule_from_trade(prev))
            next_profit = float(_safe_float(next_trade.get("profit_rate"), 0.0) or 0.0)
            reentries.append(
                {
                    "code": code,
                    "name": str(prev.get("name") or next_trade.get("name") or ""),
                    "prev_id": _trade_id(prev),
                    "next_id": _trade_id(next_trade),
                    "gap_min": round(gap_min, 1),
                    "prev_exit_rule": prev_rule,
                    "prev_profit_rate": round(
                        float(_safe_float(prev.get("profit_rate"), 0.0) or 0.0), 3
                    ),
                    "next_profit_rate": round(next_profit, 3),
                    "higher_reentry": (
                        float(_safe_float(next_trade.get("buy_price"), 0.0) or 0.0)
                        > float(_safe_float(prev.get("sell_price"), 0.0) or 0.0)
                    ),
                    "post_fallback_reentry": _is_post_fallback(next_trade),
                    "next_loss": next_profit <= 0,
                }
            )
    by_prev_rule = Counter(row["prev_exit_rule"] for row in reentries)
    return {
        "window_min": 60,
        "total_reentries": len(reentries),
        "higher_reentry_count": sum(1 for row in reentries if row["higher_reentry"]),
        "post_fallback_reentry_count": sum(
            1 for row in reentries if row["post_fallback_reentry"]
        ),
        "after_trailing_count": int(by_prev_rule.get("scalp_trailing_take_profit", 0)),
        "after_soft_stop_count": int(by_prev_rule.get("scalp_soft_stop_pct", 0)),
        "after_soft_stop_next_loss_count": sum(
            1
            for row in reentries
            if row["prev_exit_rule"] == "scalp_soft_stop_pct" and row["next_loss"]
        ),
        "prev_exit_rule_counts": [
            {"label": key, "count": value} for key, value in by_prev_rule.most_common()
        ],
        "examples": sorted(
            reentries,
            key=lambda row: (row["post_fallback_reentry"], -row["gap_min"]),
            reverse=True,
        )[:10],
    }


def _pipeline_event_paths(dates: list[str]) -> list[Path]:
    paths: list[Path] = []
    base = DATA_DIR / "pipeline_events"
    for target_date in dates:
        for suffix in (".jsonl", ".jsonl.gz"):
            path = base / f"pipeline_events_{target_date}{suffix}"
            if path.exists():
                paths.append(path)
    return paths


def _summarize_target_pipeline_events(target_date: str) -> tuple[dict, list[str], int]:
    paths = _pipeline_event_paths([target_date])
    counts = Counter()
    fallback_regression = 0
    row_count = 0
    for path in paths:
        # The live pipeline can be multiple gigabytes.  This aggregation only
        # needs counters, so never materialize the daily source as a list.
        for payload in iter_jsonl(path):
            row_count += 1
            stage = str(payload.get("stage") or "").strip()
            if stage:
                counts[stage] += 1
            fields = (
                payload.get("fields") if isinstance(payload.get("fields"), dict) else {}
            )
            if stage == "position_rebased_after_fill":
                fill_quality = str(fields.get("fill_quality") or "").upper()
                if "PARTIAL" in fill_quality:
                    counts["partial_fill_events"] += 1
                else:
                    counts["full_fill_events"] += 1
            fallback_tokens = ("fallback_scout", "fallback_main", "fallback_single")
            fallback_seen = any(token in stage for token in fallback_tokens) or any(
                any(token in str(value) for token in fallback_tokens)
                for value in fields.values()
            )
            if fallback_seen:
                fallback_regression += 1
    return (
        {
            "order_bundle_submitted_events": int(
                counts.get("order_bundle_submitted", 0)
            ),
            "full_fill_events": int(counts.get("full_fill_events", 0)),
            "partial_fill_events": int(counts.get("partial_fill_events", 0)),
            "fallback_regression_count": int(fallback_regression),
        },
        [str(path) for path in paths],
        row_count,
    )


def _build_opportunity_cost(dates: list[str]) -> tuple[dict, list[str]]:
    snapshots, paths = _load_saved_snapshots("missed_entry_counterfactual", dates)
    outcome_counts = Counter()
    terminal_counts = Counter()
    total_estimated_pnl = 0
    evaluated = 0
    for snapshot in snapshots:
        summary = snapshot.get("summary") or {}
        metrics = snapshot.get("metrics") or {}
        outcome_counts.update(summary.get("outcome_counts") or {})
        evaluated += _safe_int(
            metrics.get("evaluated_candidates", summary.get("evaluated_candidates")), 0
        )
        total_estimated_pnl += _safe_int(
            metrics.get("estimated_counterfactual_pnl_10m_krw_sum"), 0
        )
        for row in snapshot.get("rows") or []:
            terminal_counts[str(row.get("terminal_stage") or "-")] += 1
    return (
        {
            "evaluated_candidates": int(evaluated),
            "outcome_counts": {
                "MISSED_WINNER": int(outcome_counts.get("MISSED_WINNER", 0)),
                "AVOIDED_LOSER": int(outcome_counts.get("AVOIDED_LOSER", 0)),
                "NEUTRAL": int(outcome_counts.get("NEUTRAL", 0)),
            },
            "terminal_stage_top": [
                {"label": key, "count": value}
                for key, value in terminal_counts.most_common(10)
            ],
            "estimated_counterfactual_pnl_10m_krw_sum": int(total_estimated_pnl),
            "interpretation": "기회비용 방향성 참고용이며 COMPLETED 실현손익과 합산하지 않는다.",
        },
        paths,
    )


def _build_readiness(
    *,
    target_date: str,
    target_valid_trades: list[dict],
    performance_snapshot: dict | None,
    target_pipeline_summary: dict,
) -> dict:
    metrics = (performance_snapshot or {}).get("metrics") or {}
    submitted = _safe_int(metrics.get("order_bundle_submitted_events"), 0)
    full_fill = _safe_int(metrics.get("full_fill_events"), 0)
    partial_fill = _safe_int(metrics.get("partial_fill_events"), 0)
    if submitted <= 0:
        submitted = _safe_int(
            target_pipeline_summary.get("order_bundle_submitted_events"), 0
        )
    if full_fill + partial_fill <= 0:
        full_fill = _safe_int(target_pipeline_summary.get("full_fill_events"), 0)
        partial_fill = _safe_int(target_pipeline_summary.get("partial_fill_events"), 0)
    completed_valid = len(target_valid_trades)
    observation_ready = submitted >= 20 or (full_fill + partial_fill) >= 5
    directional_only = completed_valid < 10 or (completed_valid < 50 and submitted < 20)
    return {
        "target_date": target_date,
        "submitted_orders": int(submitted),
        "full_fill_events": int(full_fill),
        "partial_fill_events": int(partial_fill),
        "completed_valid_trades": int(completed_valid),
        "observation_ready": bool(observation_ready),
        "hard_pass_fail_allowed": not directional_only,
        "directional_only": bool(directional_only),
        "reason": (
            "submitted>=20 또는 full+partial>=5 조건 충족"
            if observation_ready
            else "submitted/full/partial 표본 부족"
        ),
    }


def _build_load_distribution_evidence(
    *,
    target_date: str,
    snapshot_paths: dict[str, list[str]],
    post_sell_paths: list[str],
    pipeline_paths: list[str],
    post_sell_rows: int,
    pipeline_rows: int,
) -> dict:
    manifest_dir = DATA_DIR / "report" / "monitor_snapshots" / "manifests"
    manifest_paths = [
        str(path)
        for path in (
            manifest_dir
            / f"monitor_snapshot_manifest_{target_date}_intraday_light.json",
            manifest_dir / f"monitor_snapshot_manifest_{target_date}_full.json",
        )
        if path.exists()
    ]
    return {
        "policy": "saved snapshot 우선 -> safe wrapper async dispatch -> completion artifact/Telegram",
        "direct_foreground_build_allowed": False,
        "intraday_refresh_command": f"deploy/run_monitor_snapshot_incremental_cron.sh {target_date}",
        "full_refresh_command": f"deploy/run_monitor_snapshot_cron.sh {target_date}",
        "full_snapshot_window": "12:00~12:20 KST 1회",
        "snapshot_paths": snapshot_paths,
        "manifest_paths": manifest_paths,
        "post_sell_files_read": post_sell_paths,
        "post_sell_rows_read": int(post_sell_rows),
        "pipeline_event_files_read": pipeline_paths,
        "pipeline_event_rows_read": int(pipeline_rows),
        "pipeline_event_load_mode": "streaming_counter_projection",
        "pipeline_event_full_source_materialized": False,
    }


def build_holding_exit_observation_report(
    *,
    target_date: str,
    month_start: str | None = None,
) -> dict:
    safe_date = str(target_date or datetime.now().strftime("%Y-%m-%d")).strip()
    safe_month_start, analysis_window = _analysis_window_start(
        target_date=safe_date,
        month_start=month_start,
    )
    guarded = guard_stdin_heavy_build(
        snapshot_kind="holding_exit_observation",
        target_date=safe_date,
        fallback_snapshot=_load_saved_snapshot("holding_exit_observation", safe_date),
        request_details={"analysis_window": analysis_window},
    )
    if guarded is not None:
        return guarded

    dates = _date_range(safe_month_start, safe_date)
    trade_snapshots, trade_snapshot_paths = _load_saved_snapshots("trade_review", dates)
    performance_snapshot = _load_saved_snapshot("performance_tuning", safe_date)
    performance_paths = []
    perf_path = _monitor_snapshot_path("performance_tuning", safe_date)
    if perf_path is not None:
        performance_paths.append(str(perf_path))

    completed_rows, completed_gaps = _collect_completed_trade_rows(trade_snapshots)
    loaded_trade_dates = {str(item.get("date") or "") for item in trade_snapshots}
    for missing_date in dates:
        if missing_date in loaded_trade_dates:
            continue
        completed_gaps.append(
            {
                "date": missing_date,
                "reason": (
                    "target_trade_review_snapshot_missing"
                    if missing_date == safe_date
                    else "analysis_window_trade_review_snapshot_missing"
                ),
            }
        )
    main_completed_rows = [
        row
        for row in completed_rows
        if str(row.get("strategy") or "").upper() in {"SCALPING", "SCALP"}
    ]
    valid_trades = [
        row for row in main_completed_rows if _is_valid_completed_trade(row)
    ]
    strict_exclusions = {
        _trade_id(row): _strict_completed_reasons(
            row, clean_start=analysis_window["clean_tuning_baseline_date"][:10]
        )
        for row in valid_trades
    }
    strict_trades = [
        row for row in valid_trades
        if not strict_exclusions[_trade_id(row)]
    ]
    main_ids = [_trade_id(row) for row in main_completed_rows]
    valid_ids = [_trade_id(row) for row in valid_trades]
    invalid_ids = [
        _trade_id(row) for row in main_completed_rows
        if not _is_valid_completed_trade(row)
    ]
    strict_ids = [_trade_id(row) for row in strict_trades]
    excluded_ids = [trade_id for trade_id, reasons in strict_exclusions.items() if reasons]
    source_gap_ids = [
        trade_id for trade_id, reasons in strict_exclusions.items()
        if any(reason.startswith("source_gap_") for reason in reasons)
    ]
    census_id_contract_ok = bool(
        len(main_ids) == len(set(main_ids))
        and set(main_ids) == set(valid_ids).union(invalid_ids)
        and not set(valid_ids).intersection(invalid_ids)
        and set(valid_ids) == set(strict_ids).union(excluded_ids)
        and not set(strict_ids).intersection(excluded_ids)
        and set(source_gap_ids).issubset(excluded_ids)
    )
    if not census_id_contract_ok:
        completed_gaps.append({
            "date": safe_date, "reason": "completed_position_id_partition_mismatch"
        })
    target_valid_trades = [
        row
        for row in strict_trades
        if str(
            row.get("completion_observed_date") or row.get("sell_time") or ""
        ).startswith(safe_date)
    ]
    post_sell_lineage_rows, post_sell_paths = _load_post_sell_rows(dates)
    post_sell_rows = [
        row
        for row in post_sell_lineage_rows
        if row.get("evaluation_status") == "evaluated"
    ]
    position_outcomes, position_coverage = _build_position_outcomes(
        strict_trades, post_sell_lineage_rows
    )
    open_positions, open_position_status = _collect_open_scalp_positions(
        trade_snapshots, safe_date
    )
    target_pipeline_summary, pipeline_paths, pipeline_rows = (
        _summarize_target_pipeline_events(safe_date)
    )
    opportunity_cost, missed_entry_paths = _build_opportunity_cost(dates)

    same_symbol_reentry = _build_same_symbol_reentry(strict_trades)
    report = {
        "date": safe_date,
        # Kept for compatibility with existing readers. New readers should
        # consume analysis_window, whose default is the clean baseline rather
        # than the first day of the current calendar month.
        "month_start": safe_month_start,
        "analysis_window": analysis_window,
        "completed_population_quality": {
            "metric_role": "source_quality_gate",
            "decision_authority": "completed_position_research_only",
            "window_policy": "clean_entry_to_exact_final_sell_day",
            "sample_floor": "all_db_completed_main_ids_accounted",
            "primary_decision_metric": "strict_completed_position_ids",
            "source_quality_gate": "sealed_census_and_broker_buy_sell_cost_reconciliation",
            "forbidden_uses": "threshold_apply|order_change|gross_ev_substitution",
            "complete": not completed_gaps,
            "source_gap_dates": completed_gaps,
            "canonical_completed_rows": len(completed_rows),
            "main_completed_rows": len(main_completed_rows),
            "other_owner_excluded_rows": len(completed_rows) - len(main_completed_rows),
            "valid_profit_rows": len(valid_trades),
            "invalid_profit_rows": len(main_completed_rows) - len(valid_trades),
            "id_partition_reconciled": census_id_contract_ok,
            "db_completed_main_ids": main_ids,
            "db_completed_valid_profit_ids": valid_ids,
            "db_completed_invalid_profit_ids": invalid_ids,
            "strict_completed_position_ids": strict_ids,
            "excluded_ids_by_reason": {
                reason: [trade_id for trade_id, reasons in strict_exclusions.items()
                         if reasons and reasons[0] == reason]
                for reason in sorted({reasons[0] for reasons in strict_exclusions.values()
                                      if reasons})
            },
            "excluded_all_reasons": {
                trade_id: reasons for trade_id, reasons in strict_exclusions.items()
                if reasons
            },
            "source_gap_ids": source_gap_ids,
            "strict_cohort_research_ready": bool(strict_trades and not completed_gaps),
            "whole_census_economics_complete": bool(
                strict_trades and len(strict_trades) == len(valid_trades)
                and len(valid_trades) == len(main_completed_rows)
                and not completed_gaps
            ),
            "target_sell_date_valid_rows": len(target_valid_trades),
        },
        "position_outcomes": position_outcomes,
        "position_outcome_coverage": position_coverage,
        "open_position_censoring": {
            "status": open_position_status,
            "position_ids": [str(row["id"]) for row in open_positions],
            "real_observed_ids": [
                str(row["id"]) for row in open_positions
                if row.get("real_position_observed")
            ],
            "decision_authority": "source_only_no_pnl_or_threshold_apply",
        },
        "readiness": _build_readiness(
            target_date=safe_date,
            target_valid_trades=target_valid_trades,
            performance_snapshot=performance_snapshot,
            target_pipeline_summary=target_pipeline_summary,
        ),
        "cohorts": _build_cohorts(strict_trades),
        "exit_rule_quality": _summarize_exit_rule_quality(post_sell_rows, strict_trades),
        "trailing_threshold_readiness": _build_trailing_threshold_readiness(
            position_outcomes, open_positions,
            completed_valid_ids=[_trade_id(row) for row in valid_trades],
        ),
        "trailing_start_market_tuning": summarize_start_grid(
            position_outcomes, population_complete=not completed_gaps
        ),
        "soft_stop_rebound": _build_soft_stop_rebound(
            post_sell_rows,
            same_symbol_reentry,
            strict_trades,
        ),
        "same_symbol_reentry": same_symbol_reentry,
        "opportunity_cost": opportunity_cost,
        "load_distribution_evidence": _build_load_distribution_evidence(
            target_date=safe_date,
            snapshot_paths={
                "trade_review": trade_snapshot_paths,
                "performance_tuning": performance_paths,
                "missed_entry_counterfactual": missed_entry_paths,
            },
            post_sell_paths=post_sell_paths,
            pipeline_paths=pipeline_paths,
            post_sell_rows=len(post_sell_rows),
            pipeline_rows=pipeline_rows,
        ),
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": datetime.now().isoformat(),
            "basis": "main-only, normal_only, post_fallback_deprecation",
            "profit_basis": "strict broker BUY and SELL filled completed positions with fee aware PnL",
            "post_fallback_cutoff": POST_FALLBACK_CUTOFF.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }
    economic_input_complete = bool(
        not completed_gaps
        and strict_trades
        and len(strict_trades) == len(valid_trades)
        and len(valid_trades) == len(main_completed_rows)
        and position_coverage["exact_cost_trades"] == len(strict_trades)
    )
    report["economic_input_complete"] = economic_input_complete
    tuning_input_complete = bool(
        economic_input_complete
        and position_coverage["observed_exit_signal_trades"] == len(strict_trades)
        and position_coverage["effective_threshold_receipt_trades"] == len(strict_trades)
        and position_coverage["full_post_sell_observation_trades"] == len(strict_trades)
    )
    report["tuning_input_complete"] = tuning_input_complete
    if (completed_gaps or len(strict_trades) != len(valid_trades)
            or len(valid_trades) != len(main_completed_rows)):
        position_coverage["whole_cohort_pnl_krw"] = None
        for rule in position_coverage["by_exit_rule"].values():
            rule["whole_rule_pnl_krw"] = None
    if not tuning_input_complete:
        report["soft_stop_rebound"]["cooldown_live_allowed"] = False
    return report
