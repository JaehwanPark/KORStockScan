"""Observe market-wide gainers independently from the live scanner universe.

The census is source-only instrumentation. It never contributes candidates to
the live scanner and has no order, threshold, provider-route, or restart
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    iter_jsonl,
    iter_jsonl_objects_strict,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - non-Unix fallback
    fcntl = None

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "market_opportunity_census"
SCHEMA_VERSION = "market_opportunity_census_v1"
SNAPSHOT_DIR = DATA_DIR / "market_opportunity_census"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_DIR = DATA_DIR / "pipeline_events"
AI_TRACE_DIR = DATA_DIR / "ai_decision_trace"
TOP_N_WINDOWS = (10, 20, 50)

FORBIDDEN_USES = [
    "standalone_buy",
    "live_candidate_injection",
    "score_or_threshold_mutation",
    "provider_or_model_change",
    "order_price_or_quantity_change",
    "broker_or_account_guard_bypass",
    "stale_or_source_conflict_bypass",
    "upper_limit_chase_authority",
    "bot_restart",
    "real_execution_quality_approval",
]
METRIC_CONTRACT = {
    "metric_role": "scanner_market_opportunity_coverage",
    "decision_authority": "source_only_scanner_coverage_audit",
    "window_policy": "exact_capture_timestamp_venue_panel_then_forward_pipeline",
    "sample_floor": "one_valid_ka10027_row_per_venue_panel",
    "primary_decision_metric": "top_n_entry_ai_provider_reach_rate_pct",
    "secondary_diagnostic_metrics": {
        "scanner_to_entry_ai_decision_latency_sec": (
            "first same-promotion-lineage provider-backed decision timestamp "
            "minus scanner promotion"
        ),
        "terminal_coverage_reason_counts": (
            "first missing funnel owner or post-AI/submit terminal state"
        ),
    },
    "source_quality_gate": (
        "kiwoom_ka10027_success_same_venue_timestamp_and_scanner_lineage"
    ),
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

VENUE_REQUEST_CODES = {"KRX": "1", "NXT": "2"}
PANEL_CONTRACTS = {
    "all": {
        "trde_qty_cnd": "0000",
        "stk_cnd": "0",
        "pric_cnd": "0",
        "trde_prica_cnd": "0",
    },
    "liquid_common": {
        "trde_qty_cnd": "0010",
        "stk_cnd": "4",
        "pric_cnd": "8",
        "trde_prica_cnd": "10",
    },
}

PIPELINE_STAGE_MAP = {
    # candidate_observed is emitted on the real-source guard block path. It is
    # not the native scanner-universe denominator and must not be presented as
    # successful discovery.
    "scanner_guard_observed": {
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    },
    "scanner_promoted": {"scalping_scanner_candidate_promoted"},
    "fast_precheck": {"scalping_scanner_fast_precheck"},
    "heavy_eval": {
        "scanner_async_eval_dispatched",
        "scanner_async_result_commit",
        "scalping_scanner_heavy_eval_completion",
    },
    "submitted": {"order_bundle_submitted", "order_leg_sent"},
}
STAGE_ORDER = (
    "scanner_guard_observed",
    "scanner_promoted",
    "fast_precheck",
    "heavy_eval",
    "entry_ai_trace",
    "entry_ai_provider_called",
    "submitted",
)
ENTRY_AI_ENDPOINTS = {"analyze_target", "scalping_entry"}


def _safe_code(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith("A") and len(text) >= 7:
        text = text[1:]
    return text[:6]


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _lineage_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower().startswith("not_applicable"):
        return ""
    return text


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _normalize_event_venue(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return "UNKNOWN"
    if (
        "INTEGRATED" in text
        or "COMBINED" in text
        or text in {"SOR", "KRX+NXT", "KRX_NXT"}
    ):
        return "UNKNOWN"
    if "NXT" in text and "KRX" not in text:
        return "NXT"
    if text in {"NXT", "NXT_REGULAR_OVERLAP", "NXT_AFTERMARKET"}:
        return "NXT"
    if "PREMARKET" in text or text.startswith("KRX") or text == "KRX":
        return "KRX"
    return "UNKNOWN"


def _event_venue(row: dict[str, Any]) -> str:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    for value in (
        row.get("effective_venue"),
        row.get("venue"),
        fields.get("effective_venue"),
        fields.get("venue"),
        fields.get("market_data_effective_venue"),
    ):
        normalized = _normalize_event_venue(value)
        if normalized != "UNKNOWN":
            return normalized
    return "UNKNOWN"


def _capture_id(*, target_date: str, captured_at: str, venue: str, panel: str) -> str:
    raw = f"{target_date}|{captured_at}|{venue}|{panel}|ka10027"
    return "moc-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def capture_market_snapshots(
    token: str,
    *,
    target_date: str,
    captured_at: datetime | None = None,
    venues: Iterable[str] = ("KRX", "NXT"),
    panels: Iterable[str] = ("all", "liquid_common"),
    limit: int = 200,
    fetcher: Callable[..., list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Fetch sanitized ka10027 snapshots without exposing credentials."""
    fetch = fetcher or kiwoom_utils.get_top_fluctuation_ka10027
    observed_at = captured_at or datetime.now(KST)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=KST)
    else:
        observed_at = observed_at.astimezone(KST)
    if observed_at.date().isoformat() != target_date:
        raise ValueError(
            "ka10027 snapshots can only be labeled with their actual capture date"
        )
    captured_at_text = observed_at.isoformat()
    records: list[dict[str, Any]] = []

    for raw_venue in venues:
        venue = str(raw_venue).strip().upper()
        if venue not in VENUE_REQUEST_CODES:
            raise ValueError(f"unsupported venue: {raw_venue}")
        for raw_panel in panels:
            panel = str(raw_panel).strip()
            if panel not in PANEL_CONTRACTS:
                raise ValueError(f"unsupported panel: {raw_panel}")
            request_contract = {
                "mrkt_tp": "000",
                "sort_tp": "1",
                "stex_tp": VENUE_REQUEST_CODES[venue],
                "updown_incls": "1",
                "crd_cnd": "0",
                **PANEL_CONTRACTS[panel],
            }
            source_error = ""
            try:
                fetched = fetch(
                    token,
                    mrkt_tp=request_contract["mrkt_tp"],
                    trde_qty_cnd=request_contract["trde_qty_cnd"],
                    limit=limit,
                    stex_tp=request_contract["stex_tp"],
                    sort_tp=request_contract["sort_tp"],
                    stk_cnd=request_contract["stk_cnd"],
                    crd_cnd=request_contract["crd_cnd"],
                    updown_incls=request_contract["updown_incls"],
                    pric_cnd=request_contract["pric_cnd"],
                    trde_prica_cnd=request_contract["trde_prica_cnd"],
                )
            except Exception as exc:  # preserve sanitized source-unavailable evidence
                fetched = []
                source_error = type(exc).__name__

            rows = []
            for rank, item in enumerate(fetched[:limit], start=1):
                code = _safe_code(item.get("Code"))
                if not code:
                    continue
                rows.append(
                    {
                        "rank": rank,
                        "stock_code": code,
                        "stock_name": str(item.get("Name") or "").strip(),
                        "current_price": _safe_float(item.get("Price")),
                        "change_rate_pct": _safe_float(item.get("ChangeRate")),
                        "volume": _safe_float(item.get("Volume")),
                        "execution_strength": _safe_float(item.get("CntrStr")),
                        "previous_close_signal": str(item.get("PreSig") or "").strip(),
                    }
                )

            status = "ok" if rows else "source_unavailable"
            records.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "capture_id": _capture_id(
                        target_date=target_date,
                        captured_at=captured_at_text,
                        venue=venue,
                        panel=panel,
                    ),
                    "target_date": target_date,
                    "captured_at": captured_at_text,
                    "venue": venue,
                    "panel": panel,
                    "source": {
                        "provider": "kiwoom",
                        "api_id": "ka10027",
                        "path": "/api/dostk/rkinfo",
                        "request_contract": request_contract,
                        "credential_fields_stored": [],
                    },
                    "source_quality_status": status,
                    "source_error": source_error,
                    "row_count": len(rows),
                    "metric_contract": METRIC_CONTRACT,
                    "rows": rows,
                }
            )
    return records


def append_snapshot_records(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            for record in records:
                handle.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        default=str,
                    )
                    + "\n"
                )
                count += 1
            handle.flush()
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return count


def _load_stage_index(
    pipeline_path: Path, ai_trace_path: Path, *, target_date: str
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    index: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    reverse_stage = {
        raw_stage: logical_stage
        for logical_stage, raw_stages in PIPELINE_STAGE_MAP.items()
        for raw_stage in raw_stages
    }
    for row in iter_jsonl(existing_or_gzip_path(pipeline_path)):
        logical_stage = reverse_stage.get(str(row.get("stage") or ""))
        code = _safe_code(row.get("stock_code"))
        ts = _parse_ts(row.get("emitted_at"))
        if (
            not logical_stage
            or not code
            or ts is None
            or ts.date().isoformat() != target_date
        ):
            continue
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        index[code][logical_stage].append(
            {
                "ts": ts,
                "venue": _event_venue(row),
                "record_id": _lineage_value(
                    row.get("record_id") or fields.get("runtime_record_id")
                ),
                "scanner_promotion_id": _lineage_value(
                    fields.get("scanner_promotion_id")
                ),
                "source_signature": str(fields.get("source_signature") or ""),
                "reason": str(
                    fields.get("reason")
                    or fields.get("block_reason")
                    or fields.get("scanner_promotion_reason")
                    or ""
                ),
            }
        )

    try:
        for row in iter_jsonl_objects_strict(ai_trace_path):
            if str(row.get("endpoint") or "") not in ENTRY_AI_ENDPOINTS:
                continue
            code = _safe_code(row.get("stock_code") or row.get("symbol"))
            ts = _parse_ts(row.get("decision_ts") or row.get("created_at"))
            if not code or ts is None or ts.date().isoformat() != target_date:
                continue
            ai_row = {
                "ts": ts,
                "venue": _normalize_event_venue(row.get("effective_venue")),
                "action": str(row.get("action") or ""),
                "provider_called": _boolish(row.get("provider_called")),
                "provider_actual": str(row.get("provider_actual") or ""),
                "result_source": str(row.get("result_source") or ""),
                "record_id": _lineage_value(row.get("record_id")),
                "request_id": str(row.get("request_id") or ""),
            }
            index[code]["entry_ai_trace"].append(ai_row)
            provider_actual = ai_row["provider_actual"].strip().lower()
            if (
                ai_row["provider_called"]
                and provider_actual
                and provider_actual != "none"
            ):
                index[code]["entry_ai_provider_called"].append(ai_row)
    except FileNotFoundError:
        pass
    return index


def _matching_stage_rows(
    stage_index: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    code: str,
    stage: str,
    venue: str,
    after: datetime | None,
    before: datetime | None = None,
    require_venue: bool,
) -> list[dict[str, Any]]:
    matched = []
    for row in stage_index.get(code, {}).get(stage, []):
        if after is not None and row["ts"] < after:
            continue
        if before is not None and row["ts"] >= before:
            continue
        if require_venue and row.get("venue") != venue:
            continue
        matched.append(row)
    return matched


def _build_episodes(
    snapshots: Iterable[dict[str, Any]], *, panel: str, top_n: int
) -> list[dict[str, Any]]:
    episodes: dict[tuple[str, str], dict[str, Any]] = {}
    for snapshot in snapshots:
        if (
            snapshot.get("source_quality_status") != "ok"
            or snapshot.get("panel") != panel
        ):
            continue
        captured_at = _parse_ts(snapshot.get("captured_at"))
        venue = str(snapshot.get("venue") or "")
        if captured_at is None or venue not in VENUE_REQUEST_CODES:
            continue
        for row in snapshot.get("rows") or []:
            rank = int(row.get("rank") or 0)
            code = _safe_code(row.get("stock_code"))
            if not code or rank <= 0 or rank > top_n:
                continue
            key = (venue, code)
            episode = episodes.setdefault(
                key,
                {
                    "venue": venue,
                    "stock_code": code,
                    "stock_name": row.get("stock_name"),
                    "first_census_at": captured_at,
                    "last_census_at": captured_at,
                    "best_rank": rank,
                    "latest_rank": rank,
                    "latest_price": row.get("current_price"),
                    "latest_change_rate_pct": row.get("change_rate_pct"),
                    "snapshot_count": 0,
                },
            )
            episode["first_census_at"] = min(episode["first_census_at"], captured_at)
            episode["last_census_at"] = max(episode["last_census_at"], captured_at)
            episode["best_rank"] = min(int(episode["best_rank"]), rank)
            if captured_at >= episode["last_census_at"]:
                episode["latest_rank"] = rank
                episode["latest_price"] = row.get("current_price")
                episode["latest_change_rate_pct"] = row.get("change_rate_pct")
            episode["snapshot_count"] += 1
    return sorted(
        episodes.values(),
        key=lambda item: (
            item["venue"],
            int(item["best_rank"]),
            item["stock_code"],
        ),
    )


def _coverage_row(
    episode: dict[str, Any],
    stage_index: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    after: datetime | None,
    require_venue: bool,
    require_lineage: bool = False,
) -> dict[str, Any]:
    code = episode["stock_code"]
    venue = episode["venue"]
    candidate_rows = {
        stage: _matching_stage_rows(
            stage_index,
            code=code,
            stage=stage,
            venue=venue,
            after=after,
            require_venue=require_venue,
        )
        for stage in STAGE_ORDER
    }
    lineage_status = "not_requested_noncausal"
    lineage_promotion_id = ""
    lineage_source_signature = ""
    lineage_record_ids: set[str] = set()
    promotions = sorted(candidate_rows["scanner_promoted"], key=lambda row: row["ts"])
    if not require_lineage and promotions:
        lineage_promotion_id = _lineage_value(promotions[0].get("scanner_promotion_id"))
        lineage_source_signature = str(promotions[0].get("source_signature") or "")
    if require_lineage:
        selected_promotion = promotions[0] if promotions else None
        if selected_promotion is None:
            lineage_status = "not_applicable_no_scanner_promotion"
            candidate_rows = {
                stage: (rows if stage == "scanner_guard_observed" else [])
                for stage, rows in candidate_rows.items()
            }
        else:
            lineage_promotion_id = _lineage_value(
                selected_promotion.get("scanner_promotion_id")
            )
            lineage_source_signature = str(
                selected_promotion.get("source_signature") or ""
            )
            next_promotion_at = min(
                (
                    row["ts"]
                    for row in promotions[1:]
                    if row["ts"] > selected_promotion["ts"]
                ),
                default=None,
            )
            if not lineage_promotion_id:
                lineage_status = "scanner_promotion_id_missing"
                candidate_rows = {
                    stage: (
                        [selected_promotion]
                        if stage == "scanner_promoted"
                        else (rows if stage == "scanner_guard_observed" else [])
                    )
                    for stage, rows in candidate_rows.items()
                }
            else:
                lineage_status = "scanner_promotion_lineage_proven"
                lineaged_pipeline_rows: dict[str, list[dict[str, Any]]] = {}
                for stage, rows in candidate_rows.items():
                    if stage == "scanner_guard_observed":
                        lineaged_pipeline_rows[stage] = rows
                    elif stage == "scanner_promoted":
                        lineaged_pipeline_rows[stage] = [selected_promotion]
                    elif stage in {"entry_ai_trace", "entry_ai_provider_called"}:
                        lineaged_pipeline_rows[stage] = []
                    else:
                        lineaged_pipeline_rows[stage] = [
                            row
                            for row in rows
                            if (
                                selected_promotion["ts"] <= row["ts"]
                                and (
                                    next_promotion_at is None
                                    or row["ts"] < next_promotion_at
                                )
                                and _lineage_value(row.get("scanner_promotion_id"))
                                == lineage_promotion_id
                            )
                        ]
                        lineage_record_ids.update(
                            _lineage_value(row.get("record_id"))
                            for row in lineaged_pipeline_rows[stage]
                            if _lineage_value(row.get("record_id"))
                        )
                for stage in ("entry_ai_trace", "entry_ai_provider_called"):
                    lineaged_pipeline_rows[stage] = [
                        row
                        for row in candidate_rows[stage]
                        if (
                            selected_promotion["ts"] <= row["ts"]
                            and (
                                next_promotion_at is None
                                or row["ts"] < next_promotion_at
                            )
                            and _lineage_value(row.get("record_id"))
                            in lineage_record_ids
                        )
                    ]
                if not lineage_record_ids:
                    lineage_status = "scanner_promotion_record_lineage_pending"
                candidate_rows = lineaged_pipeline_rows

    flags: dict[str, bool] = {}
    first_times: dict[str, datetime | None] = {}
    actions: list[str] = []
    for stage in STAGE_ORDER:
        rows = candidate_rows[stage]
        flags[stage] = bool(rows)
        first_times[stage] = min((row["ts"] for row in rows), default=None)
        if stage == "entry_ai_trace":
            actions = sorted(
                {str(row.get("action") or "") for row in rows if row.get("action")}
            )

    promoted_at = first_times.get("scanner_promoted")
    stage_latency_from_promotion_sec = (
        {
            stage: (
                round((stage_at - promoted_at).total_seconds(), 6)
                if promoted_at is not None
                and stage_at is not None
                and stage_at >= promoted_at
                else None
            )
            for stage, stage_at in first_times.items()
            if stage != "scanner_promoted"
        }
        if require_lineage and lineage_promotion_id
        else {}
    )

    if not flags["scanner_promoted"]:
        no_ai_reason = (
            "scanner_source_guard_blocked_before_promotion"
            if flags["scanner_guard_observed"]
            else "scanner_discovery_gap_or_unobserved"
        )
    else:
        if require_lineage and not lineage_promotion_id:
            no_ai_reason = "scanner_promotion_lineage_unproven"
        else:
            no_ai_reason = "entry_ai_provider_reached"
            for stage, reason in (
                ("fast_precheck", "scanner_fast_precheck_gap"),
                ("heavy_eval", "scanner_heavy_eval_gap"),
                ("entry_ai_trace", "entry_ai_trace_gap"),
                ("entry_ai_provider_called", "entry_ai_preflight_or_transport_block"),
            ):
                if not flags[stage]:
                    no_ai_reason = reason
                    break

    return {
        **{
            key: (value.isoformat() if isinstance(value, datetime) else value)
            for key, value in episode.items()
        },
        "stage_reached": flags,
        "first_stage_at": {
            key: value.isoformat() if value is not None else None
            for key, value in first_times.items()
        },
        "stage_latency_from_scanner_promoted_sec": (stage_latency_from_promotion_sec),
        "scanner_lineage": {
            "required": require_lineage,
            "status": lineage_status,
            "scanner_promotion_id": lineage_promotion_id or None,
            "record_ids": sorted(lineage_record_ids),
            "source_signature": lineage_source_signature,
            "prev_close_gainer_source": (
                "PREV_CLOSE_GAINER"
                in {
                    token.strip().upper()
                    for token in lineage_source_signature.split(",")
                    if token.strip()
                }
            ),
        },
        "entry_ai_actions": actions,
        "terminal_coverage_reason": (
            "submitted"
            if flags["submitted"]
            else (
                "post_ai_or_submit_gap"
                if flags["entry_ai_provider_called"]
                else no_ai_reason
            )
        ),
    }


def _latency_summary(values: list[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values if value >= 0)
    if not ordered:
        return {
            "sample_count": 0,
            "p50_sec": None,
            "p95_sec": None,
            "max_sec": None,
        }

    def percentile(fraction: float) -> float:
        rank = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1))
        return round(ordered[rank], 6)

    return {
        "sample_count": len(ordered),
        "p50_sec": percentile(0.50),
        "p95_sec": percentile(0.95),
        "max_sec": round(ordered[-1], 6),
    }


def _summarize_rows_base(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    counts = {
        stage: sum(bool(row["stage_reached"].get(stage)) for row in rows)
        for stage in STAGE_ORDER
    }
    latency_by_stage = {
        stage: _latency_summary(
            [
                float(latency)
                for row in rows
                if (
                    latency := (
                        row.get("stage_latency_from_scanner_promoted_sec") or {}
                    ).get(stage)
                )
                is not None
            ]
        )
        for stage in (
            "fast_precheck",
            "heavy_eval",
            "entry_ai_provider_called",
            "submitted",
        )
    }
    return {
        "episode_count": total,
        "stage_counts": counts,
        "stage_rates_pct": {
            stage: round((count / total * 100.0), 2) if total else 0.0
            for stage, count in counts.items()
        },
        "terminal_coverage_reason_counts": dict(
            sorted(Counter(row["terminal_coverage_reason"] for row in rows).items())
        ),
        "scanner_lineage_status_counts": dict(
            sorted(
                Counter(
                    str((row.get("scanner_lineage") or {}).get("status") or "missing")
                    for row in rows
                ).items()
            )
        ),
        "prev_close_gainer_source_promotion_count": sum(
            bool((row.get("scanner_lineage") or {}).get("prev_close_gainer_source"))
            for row in rows
        ),
        "stage_latency_from_scanner_promoted_sec": latency_by_stage,
    }


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize_rows_base(rows)
    summary["by_venue"] = {
        venue: _summarize_rows_base([row for row in rows if row.get("venue") == venue])
        for venue in VENUE_REQUEST_CODES
    }
    return summary


def _snapshot_contract_error(row: dict[str, Any], *, target_date: str) -> str:
    if row.get("schema_version") != SCHEMA_VERSION:
        return "schema_version_mismatch"
    if str(row.get("target_date") or "") != target_date:
        return "target_date_mismatch"
    captured_at = _parse_ts(row.get("captured_at"))
    if captured_at is None or captured_at.date().isoformat() != target_date:
        return "capture_timestamp_mismatch"
    if row.get("venue") not in VENUE_REQUEST_CODES:
        return "venue_invalid"
    if row.get("panel") not in PANEL_CONTRACTS:
        return "panel_invalid"
    rows = row.get("rows")
    if not isinstance(rows, list):
        return "rows_not_list"
    if row.get("source_quality_status") == "ok" and not rows:
        return "ok_status_without_rows"
    return ""


def build_report(
    target_date: str,
    *,
    snapshot_path: Path | None = None,
    pipeline_path: Path | None = None,
    ai_trace_path: Path | None = None,
) -> dict[str, Any]:
    snapshots_path = snapshot_path or (
        SNAPSHOT_DIR / f"{REPORT_TYPE}_{target_date}.jsonl"
    )
    events_path = pipeline_path or (
        PIPELINE_DIR / f"pipeline_events_{target_date}.jsonl"
    )
    trace_path = ai_trace_path or (
        AI_TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl"
    )
    all_snapshots = list(iter_jsonl(existing_or_gzip_path(snapshots_path)))
    target_date_snapshots = [
        row for row in all_snapshots if str(row.get("target_date") or "") == target_date
    ]
    contract_errors = [
        _snapshot_contract_error(row, target_date=target_date)
        for row in target_date_snapshots
    ]
    snapshots = [
        row for row, error in zip(target_date_snapshots, contract_errors) if not error
    ]
    stage_index = _load_stage_index(events_path, trace_path, target_date=target_date)
    valid_snapshots = [
        row for row in snapshots if row.get("source_quality_status") == "ok"
    ]

    coverage: dict[str, Any] = {}
    details: dict[str, Any] = {}
    for panel in PANEL_CONTRACTS:
        coverage[panel] = {}
        details[panel] = {}
        for top_n in TOP_N_WINDOWS:
            episodes = _build_episodes(snapshots, panel=panel, top_n=top_n)
            forward_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=episode["first_census_at"],
                    require_venue=True,
                    require_lineage=True,
                )
                for episode in episodes
            ]
            venue_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=None,
                    require_venue=True,
                )
                for episode in episodes
            ]
            any_venue_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=None,
                    require_venue=False,
                )
                for episode in episodes
            ]
            key = f"top_{top_n}"
            coverage[panel][key] = {
                "forward_exact": _summarize_rows(forward_rows),
                "same_day_venue_consistent_retrospective": _summarize_rows(venue_rows),
                "same_day_any_venue_retrospective_noncausal": _summarize_rows(
                    any_venue_rows
                ),
            }
            details[panel][key] = {
                "forward_exact": forward_rows,
                "same_day_venue_consistent_retrospective": venue_rows,
            }

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": "ok" if valid_snapshots else "source_unavailable",
        "metric_contract": METRIC_CONTRACT,
        "source_quality": {
            "snapshot_count": len(snapshots),
            "foreign_target_date_snapshot_count": (
                len(all_snapshots) - len(target_date_snapshots)
            ),
            "invalid_contract_snapshot_count": sum(
                bool(error) for error in contract_errors
            ),
            "invalid_contract_reasons": sorted(
                {error for error in contract_errors if error}
            ),
            "valid_snapshot_count": len(valid_snapshots),
            "unavailable_snapshot_count": len(snapshots) - len(valid_snapshots),
            "snapshot_path": str(snapshots_path),
            "pipeline_path": str(existing_or_gzip_path(events_path)),
            "ai_trace_path": str(existing_or_gzip_path(trace_path)),
            "postclose_snapshot_forward_warning": (
                "forward_exact requires intraday captures; same-day retrospective "
                "is noncausal diagnostic evidence only"
            ),
        },
        "coverage": coverage,
        "opportunity_details": details,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Market Opportunity Census - {report.get('target_date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- decision_authority: `{METRIC_CONTRACT['decision_authority']}`",
        "- runtime_effect: `false`",
        "- actual_order_submitted: `false`",
        (
            "- warning: forward_exact requires intraday captures; retrospective "
            "coverage is noncausal and cannot authorize BUY."
        ),
        "",
        "## Coverage",
        "",
        "| Panel | Window | Venue | View | Episodes | Scanner promoted | PREV_CLOSE_GAINER source | Heavy eval | AI trace | Provider call | Promote→AI decision p50 sec | Submitted |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for panel, panel_rows in report.get("coverage", {}).items():
        for window, views in panel_rows.items():
            for view, summary in views.items():
                summaries = [("ALL", summary), *summary.get("by_venue", {}).items()]
                for venue, venue_summary in summaries:
                    counts = venue_summary.get("stage_counts") or {}
                    latency = (
                        venue_summary.get("stage_latency_from_scanner_promoted_sec")
                        or {}
                    ).get("entry_ai_provider_called") or {}
                    lines.append(
                        "| "
                        f"{panel} | {window.replace('top_', '')} | {venue} | "
                        f"{view} | {venue_summary.get('episode_count', 0)} | "
                        f"{counts.get('scanner_promoted', 0)} | "
                        f"{venue_summary.get('prev_close_gainer_source_promotion_count', 0)} | "
                        f"{counts.get('heavy_eval', 0)} | "
                        f"{counts.get('entry_ai_trace', 0)} | "
                        f"{counts.get('entry_ai_provider_called', 0)} | "
                        f"{latency.get('p50_sec')} | "
                        f"{counts.get('submitted', 0)} |"
                    )
    lines.extend(
        [
            "",
            "## Forbidden Uses",
            "",
            *[f"- `{item}`" for item in FORBIDDEN_USES],
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report.get("target_date") or date.today().isoformat())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json"
    md_path = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--venues", default="KRX,NXT")
    parser.add_argument("--panels", default="all,liquid_common")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--snapshot-path")
    parser.add_argument("--pipeline-path")
    parser.add_argument("--ai-trace-path")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    snapshot_path = (
        Path(args.snapshot_path)
        if args.snapshot_path
        else SNAPSHOT_DIR / f"{REPORT_TYPE}_{args.target_date}.jsonl"
    )
    captured_count = 0
    if args.capture:
        token = kiwoom_utils.get_kiwoom_token()
        if not token:
            raise SystemExit("Kiwoom token unavailable")
        records = capture_market_snapshots(
            token,
            target_date=args.target_date,
            venues=_parse_csv(args.venues),
            panels=_parse_csv(args.panels),
            limit=max(1, args.limit),
        )
        captured_count = append_snapshot_records(snapshot_path, records)

    report = build_report(
        args.target_date,
        snapshot_path=snapshot_path,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path else None,
        ai_trace_path=Path(args.ai_trace_path) if args.ai_trace_path else None,
    )
    output_paths: tuple[Path, Path] | None = None
    if args.write:
        output_paths = write_report(report)
    if args.print_summary or args.capture or args.write:
        liquid_top_20 = (
            report.get("coverage", {})
            .get("liquid_common", {})
            .get("top_20", {})
            .get("same_day_venue_consistent_retrospective", {})
        )
        print(
            json.dumps(
                {
                    "status": report.get("status"),
                    "captured_records": captured_count,
                    "snapshot_path": str(snapshot_path),
                    "report_paths": (
                        [str(path) for path in output_paths] if output_paths else []
                    ),
                    "liquid_top_20_retrospective": liquid_top_20,
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
