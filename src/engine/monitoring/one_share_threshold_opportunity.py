from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import time
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.engine.ai.postclose_review_config import resolve_postclose_ai_review_config
from src.engine.ai_response_contracts import AI_RESPONSE_SCHEMA_REGISTRY

PROJECT_ROOT = Path(__file__).resolve().parents[3]
KST = timezone(timedelta(hours=9))
CLEAN_BASELINE_DATE = "2026-06-05"
CLEAN_BASELINE_TS_KST = "2026-06-05T00:00:00+09:00"
REPORT_TYPE = "one_share_threshold_opportunity"
REPORT_SCHEMA_VERSION = 4
PIPELINE_INDEX_CACHE_SCHEMA_VERSION = 4
THRESHOLD_GROUP_CONTRACT_VERSION = "one_share_threshold_groups_v3"
AI_REVIEW_SCHEMA_NAME = "one_share_threshold_opportunity_ai_review_v1"
AI_REVIEWER_NAME = "one_share_threshold_opportunity_ai_review"
FORCED_REASON = "rising_missed_one_share_entry"
FORBIDDEN_USES = [
    "runtime_threshold_mutation",
    "buy_score_threshold_relaxation_without_preopen_apply",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "provider_route_change",
    "bot_restart",
    "forced_one_share_success_counting",
    "real_execution_quality_approval",
]
THRESHOLD_GROUPS = {
    "ai_score_near_buy": {
        "stages": {"blocked_ai_score", "ai_confirmed_terminal_no_budget"},
        "tokens": {"blocked_ai_score", "below_buy_score_threshold"},
        "hook_family": "entry_opportunity_recheck_runtime",
        "target_subsystem": "scalping_entry_ai_score_recheck",
    },
    "latency_or_freshness": {
        "stages": {"latency_block", "entry_submit_revalidation_block"},
        "tokens": {"latency", "stale", "quote_freshness", "stale_context_or_quote"},
        "hook_family": "latency_classifier_runtime_profile",
        "target_subsystem": "entry_latency_freshness_recheck",
    },
    "strength_momentum_vpw": {
        "stages": {
            "blocked_strength_momentum",
            "strength_momentum_stability_recheck_pending",
            "scanner_fast_precheck_stability_pending",
        },
        "tokens": {
            "insufficient_history",
            "below_strength",
            "below_buy_ratio",
            "below_window_buy_value",
            "vpw",
        },
        "hook_family": "entry_strength_momentum_recheck",
        "target_subsystem": "entry_strength_momentum_history_recheck",
    },
    "overbought_or_liquidity": {
        "stages": {
            "pre_submit_liquidity_guard_block",
            "pre_submit_overbought_pullback_guard_block",
            "scalp_sim_pre_submit_overbought_guard_would_block",
        },
        "tokens": {"overbought", "liquidity", "pullback"},
        "hook_family": "pre_submit_guard_attribution",
        "target_subsystem": "entry_pre_submit_guard_split",
    },
    "cooldown_or_hard_safety": {
        "stages": {
            "entry_cooldown_active",
            "scalp_same_symbol_loss_reentry_blocked",
            "blocked_zero_qty",
            "auth_zero_qty",
            "blocked_pause",
        },
        "tokens": {
            "cooldown",
            "broker",
            "account",
            "quantity",
            "zero_qty",
            "paused",
            "loss_reentry",
        },
        "hook_family": "hard_safety_observation_only",
        "target_subsystem": "entry_hard_safety_preserve",
    },
}
TERMINAL_SELL_STAGES = {"sell_completed"}
_PROVENANCE_STAGES = {
    "order_bundle_submitted",
    "buy_order_filled",
    "buy_order_partial_filled",
    "residual_submitted",
    "residual_blocked",
    *TERMINAL_SELL_STAGES,
}
_PROVENANCE_FIELD_NAMES = {
    "actual_order_submitted",
    "entry_split_order_probe_first_applied",
    "entry_split_probe_first_applied",
    "entry_split_probe_bundle_id",
    "prior_probe_residual_bundle_id",
    "entry_split_order_variant_id",
    "entry_split_probe_phase",
    "entry_split_probe_abort_reason",
    "entry_split_probe_terminal_abort_reason",
    "prior_probe_residual_abort_reason",
    "entry_split_probe_terminal_outcome",
    "prior_probe_residual_outcome",
    "entry_split_probe_terminal_abort_detail_reason",
    "residual_revalidation_timeout_cause",
    "entry_split_probe_terminal_failure_signature",
    "prior_probe_residual_failure_signature",
}


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        return float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except ValueError:
        return None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
    for line in _iter_jsonl_lines(path):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _iter_jsonl_lines(path: Path) -> Iterator[str]:
    if not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            yield line


def _record_id_candidates_from_json_line(line: str) -> set[str]:
    """Return cheap record-id candidates; callers must verify the parsed top-level id."""

    return {
        match.group(1)
        for match in re.finditer(r'"record_id"\s*:\s*"?([^",}\s]+)', line)
    }


def _date_from_path(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return match.group(1) if match else ""


def _date_in_range(value: str, *, since_date: str, until_date: str) -> bool:
    return bool(value and since_date <= value <= until_date)


def _jsonl_paths(
    base: Path, prefix: str, *, since_date: str, until_date: str
) -> list[Path]:
    candidates = list(base.glob(f"{prefix}_*.jsonl")) + list(
        base.glob(f"{prefix}_*.jsonl.gz")
    )
    return sorted(
        path
        for path in candidates
        if _date_in_range(
            _date_from_path(path), since_date=since_date, until_date=until_date
        )
    )


def _pipeline_paths(*, since_date: str, until_date: str) -> list[Path]:
    base = PROJECT_ROOT / "data" / "pipeline_events"
    return _jsonl_paths(
        base, "pipeline_events", since_date=since_date, until_date=until_date
    )


def _post_sell_paths(*, since_date: str, until_date: str) -> list[Path]:
    base = PROJECT_ROOT / "data" / "post_sell"
    return _jsonl_paths(
        base, "post_sell_candidates", since_date=since_date, until_date=until_date
    )


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = PROJECT_ROOT / "data" / "report" / REPORT_TYPE
    return (
        base / f"{REPORT_TYPE}_{target_date}.json",
        base / f"{REPORT_TYPE}_{target_date}.md",
    )


def _is_forced_one_share(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return row.get("stage") == "rising_missed_one_share_entry" or _boolish(
        fields.get("rising_missed_one_share_entry_forced")
    )


def _clean_baseline_allowed(row: dict[str, Any], *, clean_baseline_ts_kst: str) -> bool:
    emitted_at = str(row.get("emitted_at") or "")
    if not emitted_at:
        return True
    row_date = emitted_at[:10]
    baseline_date = clean_baseline_ts_kst[:10]
    if row_date < baseline_date:
        return False
    if row_date > baseline_date:
        return True
    return emitted_at >= clean_baseline_ts_kst


def _event_record_id(row: dict[str, Any]) -> str:
    return str(row.get("record_id") or "").strip()


def _record_feature(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return {
        "record_id": _event_record_id(row),
        "stock_code": row.get("stock_code"),
        "stock_name": row.get("stock_name"),
        "entry_time": row.get("emitted_at"),
        "entry_date": str(row.get("emitted_at") or "")[:10],
        "source_stage": row.get("stage"),
        "source_signature": fields.get("source_signature"),
        "scanner_promotion_reason": fields.get("scanner_promotion_reason"),
        "ai_score": _safe_float(
            fields.get("ai_score")
            or fields.get("current_ai_score")
            or fields.get("entry_opportunity_recheck_ai_score")
        ),
        "entry_price": _safe_float(
            fields.get("rising_missed_one_share_entry_price")
            or fields.get("current_price")
            or fields.get("curr_price")
            or fields.get("curr")
        ),
        "actual_order_submitted_observed": _boolish(
            fields.get("actual_order_submitted")
        ),
        "entry_split_probe_first_applied_observed": _boolish(
            fields.get("entry_split_order_probe_first_applied")
            or fields.get("entry_split_probe_first_applied")
        ),
        "entry_split_probe_bundle_id": fields.get("entry_split_probe_bundle_id"),
        "entry_split_order_variant_id": fields.get("entry_split_order_variant_id"),
        "entry_split_probe_phase": fields.get("entry_split_probe_phase"),
        "entry_split_probe_abort_reason": fields.get("entry_split_probe_abort_reason"),
        "entry_split_probe_terminal_outcome": (
            fields.get("entry_split_probe_terminal_outcome")
            or fields.get("prior_probe_residual_outcome")
        ),
        "terminal_sell_observed": row.get("stage") in TERMINAL_SELL_STAGES,
        "terminal_sell_time": (
            row.get("emitted_at") if row.get("stage") in TERMINAL_SELL_STAGES else None
        ),
    }


def _merge_probe_split_provenance(item: dict[str, Any], row: dict[str, Any]) -> None:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    if _boolish(fields.get("actual_order_submitted")) or stage in {
        "order_bundle_submitted",
        "buy_order_filled",
        "buy_order_partial_filled",
    }:
        item["actual_order_submitted_observed"] = True
    if _boolish(
        fields.get("entry_split_order_probe_first_applied")
        or fields.get("entry_split_probe_first_applied")
    ):
        item["entry_split_probe_first_applied_observed"] = True
    for key, aliases in (
        (
            "entry_split_probe_bundle_id",
            ("entry_split_probe_bundle_id", "prior_probe_residual_bundle_id"),
        ),
        ("entry_split_order_variant_id", ("entry_split_order_variant_id",)),
        ("entry_split_probe_phase", ("entry_split_probe_phase",)),
        (
            "entry_split_probe_abort_reason",
            (
                "entry_split_probe_abort_reason",
                "entry_split_probe_terminal_abort_reason",
                "prior_probe_residual_abort_reason",
            ),
        ),
        (
            "entry_split_probe_terminal_outcome",
            (
                "entry_split_probe_terminal_outcome",
                "prior_probe_residual_outcome",
            ),
        ),
        (
            "entry_split_probe_terminal_abort_detail_reason",
            (
                "entry_split_probe_terminal_abort_detail_reason",
                "residual_revalidation_timeout_cause",
            ),
        ),
        (
            "entry_split_probe_terminal_failure_signature",
            (
                "entry_split_probe_terminal_failure_signature",
                "prior_probe_residual_failure_signature",
            ),
        ),
    ):
        value = next(
            (
                fields.get(alias)
                for alias in aliases
                if fields.get(alias) not in (None, "", "-")
            ),
            None,
        )
        if value not in (None, "", "-"):
            item[key] = value
    if stage == "residual_submitted":
        item["entry_split_residual_submitted_observed"] = True
    elif stage == "residual_blocked":
        item["entry_split_residual_blocked_observed"] = True
    if stage in TERMINAL_SELL_STAGES:
        terminal_time = row.get("emitted_at")
        terminal_stock_code = str(row.get("stock_code") or "").strip()[:6]
        if (
            item.get("terminal_sell_time") not in (None, "", "-")
            and item.get("terminal_sell_time") != terminal_time
        ):
            item["terminal_sell_identity_conflict"] = True
        if (
            item.get("terminal_sell_stock_code") not in (None, "", "-")
            and item.get("terminal_sell_stock_code") != terminal_stock_code
        ):
            item["terminal_sell_identity_conflict"] = True
        item["terminal_sell_observed"] = True
        item.setdefault("terminal_sell_time", terminal_time)
        item.setdefault("terminal_sell_stock_code", terminal_stock_code)


def _has_record_provenance(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return str(row.get("stage") or "") in _PROVENANCE_STAGES or any(
        fields.get(name) not in (None, "", "-") for name in _PROVENANCE_FIELD_NAMES
    )


def _merge_cached_provenance(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key, value in source.items():
        if value in (None, "", "-"):
            continue
        if key in {"terminal_sell_time", "terminal_sell_stock_code"}:
            prior = target.get(key)
            if prior not in (None, "", "-") and prior != value:
                target["terminal_sell_identity_conflict"] = True
                continue
        if isinstance(value, bool):
            target[key] = bool(target.get(key)) or value
        else:
            target[key] = value


def _event_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _event_order_key(event: dict[str, Any]) -> tuple[Any, ...]:
    parsed = _event_time(event.get("emitted_at"))
    return (
        0 if parsed is not None else 1,
        parsed or datetime.max.replace(tzinfo=timezone.utc),
        str(event.get("source_path") or ""),
        int(event.get("source_line_number") or 0),
    )


def _merge_primary_blocker(
    target: dict[str, dict[str, Any]],
    record_id: str,
    event: dict[str, Any],
) -> None:
    current = target.get(record_id)
    if current is None or _event_order_key(event) < _event_order_key(current):
        target[record_id] = dict(event)


def _merge_forced_feature(
    target: dict[str, dict[str, Any]],
    record_id: str,
    source: dict[str, Any],
) -> None:
    if record_id not in target:
        target[record_id] = dict(source)
        return
    current = target[record_id]
    current_is_primary = bool(current.get("forced_source_is_primary_stage"))
    source_is_primary = bool(source.get("forced_source_is_primary_stage"))
    current_stock_code = str(current.get("stock_code") or "").strip()[:6]
    source_stock_code = str(source.get("stock_code") or "").strip()[:6]
    current_emitted_at = str(current.get("emitted_at") or "")
    source_emitted_at = str(source.get("emitted_at") or "")
    identity_conflict = bool(
        (
            current_stock_code
            and source_stock_code
            and current_stock_code != source_stock_code
        )
        or (
            current_is_primary
            and source_is_primary
            and current_emitted_at != source_emitted_at
        )
    )
    prior_identity_conflict = bool(current.get("forced_identity_conflict")) or bool(
        source.get("forced_identity_conflict")
    )
    forced_count = int(current.get("forced_event_count") or 0) + int(
        source.get("forced_event_count") or 0
    )
    identity_keys = {
        "record_id",
        "stock_code",
        "stock_name",
        "entry_time",
        "entry_date",
        "source_stage",
        "source_signature",
        "scanner_promotion_reason",
        "ai_score",
        "entry_price",
        "forced_source_is_primary_stage",
        "emitted_at",
        "source_path",
        "source_line_number",
    }
    source_owns_identity = bool(
        (source_is_primary and not current_is_primary)
        or (
            source_is_primary == current_is_primary
            and _event_order_key(source) < _event_order_key(current)
        )
    )
    if source_owns_identity:
        preserved = {
            key: value
            for key, value in current.items()
            if key not in identity_keys and key != "forced_event_count"
        }
        current.clear()
        current.update(source)
        _merge_cached_provenance(current, preserved)
    else:
        _merge_cached_provenance(
            current,
            {
                key: value
                for key, value in source.items()
                if key not in identity_keys and key != "forced_event_count"
            },
        )
    current["forced_event_count"] = forced_count
    current["forced_identity_conflict"] = bool(
        prior_identity_conflict or identity_conflict
    )


def _primary_blocker_precedes_force(
    blocker: dict[str, Any], forced_entry: dict[str, Any]
) -> bool:
    blocker_time = _event_time(blocker.get("emitted_at"))
    forced_time = _event_time(forced_entry.get("emitted_at"))
    if blocker_time is not None and forced_time is not None:
        if blocker_time != forced_time:
            return blocker_time < forced_time
        return _event_order_key(blocker) <= _event_order_key(forced_entry)
    if (
        str(blocker.get("source_path") or "")
        == str(forced_entry.get("source_path") or "")
        and blocker.get("source_line_number")
        and forced_entry.get("source_line_number")
    ):
        return int(blocker["source_line_number"]) <= int(
            forced_entry["source_line_number"]
        )
    return False


def _residual_not_submitted_source(row: dict[str, Any]) -> str:
    if (
        str(row.get("entry_split_probe_terminal_outcome") or "").strip()
        == "residual_not_submitted"
    ):
        return "explicit_terminal_outcome"
    if (
        row.get("entry_split_residual_blocked_observed") is True
        and row.get("entry_split_residual_submitted_observed") is not True
        and str(row.get("entry_split_probe_phase") or "").strip() == "aborted"
    ):
        return "legacy_aborted_phase_fallback"
    return ""


def _classify_threshold(row: dict[str, Any]) -> set[str]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    haystack = " ".join(
        str(value or "")
        for value in [
            stage,
            fields.get("reason"),
            fields.get("terminal_reason"),
            fields.get("block_reason"),
            fields.get("skip_reason"),
        ]
    ).lower()
    groups: set[str] = set()
    for group, spec in THRESHOLD_GROUPS.items():
        if stage in spec["stages"] or any(
            token in haystack for token in spec["tokens"]
        ):
            groups.add(group)
    return groups


def _classify_primary_blocker(row: dict[str, Any]) -> set[str]:
    """Return explicit blocker groups only, excluding incidental token mentions."""

    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    stage = str(row.get("stage") or "")
    blocker_haystack = " ".join(
        str(fields.get(key) or "") for key in ("terminal_reason", "block_reason")
    ).lower()
    groups: set[str] = set()
    for group, spec in THRESHOLD_GROUPS.items():
        if stage in spec["stages"] or any(
            token in blocker_haystack for token in spec["tokens"]
        ):
            groups.add(group)
    return groups


def _pipeline_index_contract_digest(clean_baseline_ts_kst: str) -> str:
    contract = {
        "cache_schema_version": PIPELINE_INDEX_CACHE_SCHEMA_VERSION,
        "threshold_group_contract_version": THRESHOLD_GROUP_CONTRACT_VERSION,
        "forced_reason": FORCED_REASON,
        "threshold_groups": {
            group: {
                "stages": sorted(spec["stages"]),
                "tokens": sorted(spec["tokens"]),
            }
            for group, spec in sorted(THRESHOLD_GROUPS.items())
        },
        "terminal_sell_stages": sorted(TERMINAL_SELL_STAGES),
        "provenance_stages": sorted(_PROVENANCE_STAGES),
        "provenance_field_names": sorted(_PROVENANCE_FIELD_NAMES),
        "clean_baseline_ts_kst": clean_baseline_ts_kst,
    }
    encoded = json.dumps(
        contract, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _source_stat_contract(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.resolve()),
        "device": int(stat.st_dev),
        "inode": int(stat.st_ino),
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
        "ctime_ns": int(stat.st_ctime_ns),
    }


def _pipeline_index_cache_path(cache_dir: Path, path: Path) -> Path:
    identity = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    source_date = _date_from_path(path) or "undated"
    return cache_dir / f"pipeline_index_{source_date}_{identity}.json"


def _scan_pipeline_partition(
    path: Path,
    *,
    clean_baseline_ts_kst: str,
    source_stat: dict[str, Any],
    contract_digest: str,
) -> dict[str, Any]:
    forced: dict[str, dict[str, Any]] = {}
    cross_partition_provenance: dict[str, dict[str, Any]] = {}
    discovery_line_count = 0
    discovery_parsed_row_count = 0
    invalid_json_line_numbers: set[int] = set()

    # The discovery pass parses only forced-entry or terminal-sell lines.  In
    # particular, it must not retain per-record maps for the full multi-GiB
    # pipeline population in memory or in the persistent cache.
    for line_number, line in enumerate(_iter_jsonl_lines(path), start=1):
        discovery_line_count += 1
        if not line.strip():
            continue
        if FORCED_REASON not in line and '"sell_completed"' not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            invalid_json_line_numbers.add(line_number)
            continue
        if not isinstance(row, dict):
            continue
        if not _clean_baseline_allowed(
            row, clean_baseline_ts_kst=clean_baseline_ts_kst
        ):
            continue
        discovery_parsed_row_count += 1
        record_id = _event_record_id(row)
        if not record_id:
            continue

        if _is_forced_one_share(row):
            feature = {
                **_record_feature(row),
                "forced_event_count": 1,
                "forced_source_is_primary_stage": (
                    row.get("stage") == "rising_missed_one_share_entry"
                ),
                "emitted_at": row.get("emitted_at"),
                "source_path": str(path),
                "source_line_number": line_number,
            }
            _merge_forced_feature(forced, record_id, feature)

        if str(row.get("stage") or "") in TERMINAL_SELL_STAGES:
            item = cross_partition_provenance.setdefault(record_id, {})
            _merge_probe_split_provenance(item, row)

    threshold_counts: dict[str, Counter[str]] = defaultdict(Counter)
    primary_blockers: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    targeted_record_row_count = 0
    forced_ids = set(forced)
    if forced_ids:
        for line_number, line in enumerate(_iter_jsonl_lines(path), start=1):
            if not (_record_id_candidates_from_json_line(line) & forced_ids):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_line_numbers.add(line_number)
                continue
            if not isinstance(row, dict) or not _clean_baseline_allowed(
                row, clean_baseline_ts_kst=clean_baseline_ts_kst
            ):
                continue
            record_id = _event_record_id(row)
            if record_id not in forced_ids:
                continue
            targeted_record_row_count += 1
            for group in _classify_threshold(row):
                threshold_counts[record_id][group] += 1

            blocker_groups = sorted(_classify_primary_blocker(row))
            if blocker_groups:
                _merge_primary_blocker(
                    primary_blockers,
                    record_id,
                    {
                        "groups": blocker_groups,
                        "stage": row.get("stage"),
                        "emitted_at": row.get("emitted_at"),
                        "source_path": str(path),
                        "source_line_number": line_number,
                    },
                )

            if _has_record_provenance(row):
                item = provenance.setdefault(record_id, {})
                _merge_probe_split_provenance(item, row)

    current_source_stat = _source_stat_contract(path)
    if current_source_stat != source_stat:
        raise RuntimeError(
            "pipeline_source_changed_during_scan:"
            f"{path}:before={source_stat}:after={current_source_stat}"
        )
    return {
        "cache_schema_version": PIPELINE_INDEX_CACHE_SCHEMA_VERSION,
        "contract_digest": contract_digest,
        "source": source_stat,
        "scan_pass_count": 2 if forced_ids else 1,
        "discovery_line_count": discovery_line_count,
        "discovery_parsed_row_count": discovery_parsed_row_count,
        "targeted_record_row_count": targeted_record_row_count,
        "invalid_json_row_count": len(invalid_json_line_numbers),
        "forced": forced,
        "threshold_counts": {
            record_id: dict(counts) for record_id, counts in threshold_counts.items()
        },
        "primary_blockers": primary_blockers,
        "provenance": provenance,
        "cross_partition_provenance": cross_partition_provenance,
    }


def _load_or_build_pipeline_index(
    path: Path,
    *,
    clean_baseline_ts_kst: str,
    cache_dir: Path | None,
) -> tuple[dict[str, Any], bool, str | None]:
    source_stat = _source_stat_contract(path)
    contract_digest = _pipeline_index_contract_digest(clean_baseline_ts_kst)
    cache_path = (
        _pipeline_index_cache_path(cache_dir, path) if cache_dir is not None else None
    )
    if cache_path is not None and cache_path.is_file():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            cached = None
        if (
            isinstance(cached, dict)
            and cached.get("cache_schema_version")
            == PIPELINE_INDEX_CACHE_SCHEMA_VERSION
            and cached.get("contract_digest") == contract_digest
            and cached.get("source") == source_stat
            and all(
                isinstance(cached.get(key), dict)
                for key in (
                    "forced",
                    "threshold_counts",
                    "primary_blockers",
                    "provenance",
                    "cross_partition_provenance",
                )
            )
            and cached.get("scan_pass_count") in {1, 2}
        ):
            return cached, True, str(cache_path)

    index = _scan_pipeline_partition(
        path,
        clean_baseline_ts_kst=clean_baseline_ts_kst,
        source_stat=source_stat,
        contract_digest=contract_digest,
    )
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = cache_path.with_name(f".{cache_path.name}.{os.getpid()}.tmp")
        temporary_path.write_text(
            json.dumps(index, ensure_ascii=False, sort_keys=True), encoding="utf-8"
        )
        os.replace(temporary_path, cache_path)
        final_source_stat = _source_stat_contract(path)
        if final_source_stat != source_stat:
            cache_path.unlink(missing_ok=True)
            raise RuntimeError(
                "pipeline_source_changed_during_cache_publish:"
                f"{path}:before={source_stat}:after={final_source_stat}"
            )
    return index, False, str(cache_path) if cache_path is not None else None


def _build_forced_index(
    paths: Iterable[Path],
    *,
    clean_baseline_ts_kst: str = CLEAN_BASELINE_TS_KST,
    cache_dir: Path | None = None,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, Counter[str]],
    dict[str, dict[str, Any]],
    list[str],
    dict[str, Any],
]:
    forced: dict[str, dict[str, Any]] = {}
    threshold_counts: dict[str, Counter[str]] = defaultdict(Counter)
    primary_blockers: dict[str, dict[str, Any]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    path_list = list(paths)
    source_paths: list[str] = [str(path) for path in path_list]
    cache_hits = 0
    cache_misses = 0
    source_bytes_scanned = 0
    source_bytes_reused = 0
    cache_paths: list[str] = []
    cache_miss_source_pass_count = 0
    source_io_bytes_estimated = 0
    discovery_line_count = 0
    discovery_parsed_row_count = 0
    targeted_record_row_count = 0
    invalid_json_row_count = 0

    for path in path_list:
        index, cache_hit, cache_path = _load_or_build_pipeline_index(
            path,
            clean_baseline_ts_kst=clean_baseline_ts_kst,
            cache_dir=cache_dir,
        )
        source_size = int((index.get("source") or {}).get("size_bytes") or 0)
        if cache_hit:
            cache_hits += 1
            source_bytes_reused += source_size
        else:
            cache_misses += 1
            source_bytes_scanned += source_size
            scan_pass_count = int(index.get("scan_pass_count") or 1)
            cache_miss_source_pass_count += scan_pass_count
            source_io_bytes_estimated += source_size * scan_pass_count
        if cache_path:
            cache_paths.append(cache_path)
        discovery_line_count += int(index.get("discovery_line_count") or 0)
        discovery_parsed_row_count += int(index.get("discovery_parsed_row_count") or 0)
        targeted_record_row_count += int(index.get("targeted_record_row_count") or 0)
        invalid_json_row_count += int(index.get("invalid_json_row_count") or 0)

        for record_id, source in (index.get("forced") or {}).items():
            if not isinstance(source, dict):
                continue
            _merge_forced_feature(forced, record_id, source)

        for record_id, counts in (index.get("threshold_counts") or {}).items():
            if isinstance(counts, dict):
                threshold_counts[record_id].update(
                    {str(group): int(count or 0) for group, count in counts.items()}
                )

        for record_id, event in (index.get("primary_blockers") or {}).items():
            if isinstance(event, dict):
                _merge_primary_blocker(primary_blockers, record_id, event)

        for provenance_key in ("provenance", "cross_partition_provenance"):
            for record_id, source in (index.get(provenance_key) or {}).items():
                if isinstance(source, dict):
                    _merge_cached_provenance(
                        provenance.setdefault(record_id, {}), source
                    )

    for record_id, item in forced.items():
        _merge_cached_provenance(item, provenance.get(record_id) or {})

    source_bytes_total = source_bytes_scanned + source_bytes_reused
    processing = {
        "mode": (
            "partition_index_cache"
            if cache_dir is not None
            else "bounded_partition_scan_no_cache"
        ),
        "cache_schema_version": PIPELINE_INDEX_CACHE_SCHEMA_VERSION,
        "threshold_group_contract_version": THRESHOLD_GROUP_CONTRACT_VERSION,
        "cache_enabled": cache_dir is not None,
        "cache_dir": str(cache_dir) if cache_dir is not None else None,
        "source_file_count": len(path_list),
        "cache_hit_count": cache_hits,
        "cache_miss_count": cache_misses,
        "source_bytes_total": source_bytes_total,
        "source_bytes_scanned": source_bytes_scanned,
        "source_bytes_reused": source_bytes_reused,
        "source_reuse_pct": (
            round(source_bytes_reused / source_bytes_total * 100.0, 4)
            if source_bytes_total
            else None
        ),
        "cache_miss_source_pass_count": cache_miss_source_pass_count,
        "source_io_bytes_estimated": source_io_bytes_estimated,
        "cold_partition_pass_contract": (
            "one_discovery_pass_plus_one_targeted_pass_when_forced_ids_exist"
        ),
        "legacy_full_source_passes_per_run": 2,
        "cache_payload_scope": (
            "local_forced_records_plus_cross_partition_terminal_sell_provenance"
        ),
        "discovery_line_count": discovery_line_count,
        "discovery_parsed_row_count": discovery_parsed_row_count,
        "targeted_record_row_count": targeted_record_row_count,
        "invalid_json_row_count": invalid_json_row_count,
        "cache_paths": cache_paths,
    }
    return forced, threshold_counts, primary_blockers, source_paths, processing


def _source_coverage_manifest(
    *,
    pipeline_paths: list[Path],
    post_sell_paths: list[Path],
    since_date: str,
    until_date: str,
    terminal_sell_record_ids: Iterable[str] | None = None,
    post_sell_record_ids: Iterable[str] | None = None,
    submitted_unjoined_record_ids: Iterable[str] | None = None,
    identity_conflict_record_ids: Iterable[str] | None = None,
    invalid_source_json_row_count: int = 0,
) -> dict[str, Any]:
    pipeline_dates = sorted(
        {_date_from_path(path) for path in pipeline_paths if _date_from_path(path)}
    )
    post_sell_dates = sorted(
        {_date_from_path(path) for path in post_sell_paths if _date_from_path(path)}
    )
    observed_dates = sorted(set(pipeline_dates) | set(post_sell_dates))
    # A post-sell partition date is the terminal sell/evaluation date, not the
    # originating entry date. Coverage therefore uses exact record lineage:
    # only a pipeline terminal sell receipt requires a matching post-sell row.
    # A submitted entry without a terminal sell is pending/right-censored and
    # must not be converted into an entry-date partition gap.
    post_sell_only_dates = sorted(set(post_sell_dates) - set(pipeline_dates))
    missing_pipeline_dates: list[str] = []
    terminal_record_ids = sorted(
        {str(value) for value in (terminal_sell_record_ids or []) if str(value)}
    )
    observed_post_sell_record_ids = {
        str(value) for value in (post_sell_record_ids or []) if str(value)
    }
    identity_conflict_ids = sorted(
        {str(value) for value in (identity_conflict_record_ids or []) if str(value)}
    )
    missing_terminal_record_ids = sorted(
        set(terminal_record_ids)
        - observed_post_sell_record_ids
        - set(identity_conflict_ids)
    )
    blocking_record_id_set = set(missing_terminal_record_ids) | set(
        identity_conflict_ids
    )
    pending_or_right_censored_record_ids = sorted(
        {
            str(value)
            for value in (submitted_unjoined_record_ids or [])
            if str(value) and str(value) not in blocking_record_id_set
        }
    )
    gap_count = (
        len(missing_pipeline_dates)
        + len(missing_terminal_record_ids)
        + len(identity_conflict_ids)
        + max(0, int(invalid_source_json_row_count))
    )

    def _id_digest(values: list[str]) -> str:
        encoded = json.dumps(values, ensure_ascii=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    return {
        "status": "pass" if gap_count == 0 else "source_coverage_gap",
        "since_date": since_date,
        "until_date": until_date,
        "clean_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
        "observed_dates": observed_dates,
        "pipeline_event_dates": pipeline_dates,
        "post_sell_dates": post_sell_dates,
        "post_sell_only_dates": post_sell_only_dates,
        "post_sell_only_dates_are_informational": True,
        "coverage_key": (
            "unambiguous_record_id_and_stock_code_terminal_sell_to_"
            "post_sell_recommendation_id"
        ),
        "entry_date_partition_match_required": False,
        "terminal_sell_record_count": len(terminal_record_ids),
        "terminal_sell_record_ids_sha256": _id_digest(terminal_record_ids),
        "missing_terminal_post_sell_record_count": len(missing_terminal_record_ids),
        "missing_terminal_post_sell_record_ids": missing_terminal_record_ids[:50],
        "identity_conflict_record_count": len(identity_conflict_ids),
        "identity_conflict_record_ids_sha256": _id_digest(identity_conflict_ids),
        "identity_conflict_record_examples": identity_conflict_ids[:50],
        "invalid_source_json_row_count": max(0, int(invalid_source_json_row_count)),
        "pending_or_right_censored_submit_count": len(
            pending_or_right_censored_record_ids
        ),
        "pending_or_right_censored_submit_ids_sha256": _id_digest(
            pending_or_right_censored_record_ids
        ),
        "pending_or_right_censored_submit_examples": (
            pending_or_right_censored_record_ids[:50]
        ),
        # Deprecated v2 date fields remain empty for compatible readers. Date
        # presence is informational and no longer owns source coverage.
        "expected_post_sell_dates": [],
        "post_sell_not_expected_pipeline_dates": pipeline_dates,
        "missing_pipeline_event_dates": missing_pipeline_dates,
        "missing_post_sell_dates": [],
        "gap_count": gap_count,
        "pipeline_path_count": len(pipeline_paths),
        "pipeline_gzip_path_count": sum(
            1 for path in pipeline_paths if path.suffix == ".gz"
        ),
        "post_sell_path_count": len(post_sell_paths),
        "post_sell_gzip_path_count": sum(
            1 for path in post_sell_paths if path.suffix == ".gz"
        ),
        "fail_closed_on_gap": True,
    }


def _load_post_sell(
    paths: Iterable[Path],
) -> tuple[dict[str, dict[str, Any]], list[str], dict[str, Any]]:
    by_record: dict[str, dict[str, Any]] = {}
    ambiguous_record_ids: set[str] = set()
    source_paths: list[str] = []
    duplicate_row_count = 0
    compatible_duplicate_row_count = 0
    invalid_json_row_count = 0

    def _merge_if_compatible(
        prior: dict[str, Any], incoming: dict[str, Any]
    ) -> dict[str, Any] | None:
        merged = dict(prior)
        for key in (
            "signal_date",
            "sell_time",
            "profit_rate",
            "peak_profit",
            "held_sec",
            "exit_rule",
            "stock_code",
            "buy_price",
            "sell_price",
            "buy_qty",
        ):
            before = merged.get(key)
            after = incoming.get(key)
            before_missing = before in (None, "", "-")
            after_missing = after in (None, "", "-")
            if before_missing and not after_missing:
                merged[key] = after
            elif not before_missing and not after_missing and before != after:
                return None
        if merged.get("stock_name") in (None, "", "-") and incoming.get(
            "stock_name"
        ) not in (None, "", "-"):
            merged["stock_name"] = incoming["stock_name"]
        return merged

    for path in paths:
        source_paths.append(str(path))
        for line in _iter_jsonl_lines(path):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid_json_row_count += 1
                continue
            if not isinstance(row, dict):
                invalid_json_row_count += 1
                continue
            record_id = str(
                row.get("recommendation_id") or row.get("record_id") or ""
            ).strip()
            if not record_id:
                continue
            profit = _safe_float(row.get("profit_rate"))
            outcome = {
                "signal_date": row.get("signal_date") or _date_from_path(path),
                "sell_time": row.get("sell_time"),
                "profit_rate": profit,
                "peak_profit": _safe_float(row.get("peak_profit")),
                "held_sec": _safe_float(row.get("held_sec")),
                "exit_rule": row.get("exit_rule"),
                "stock_code": row.get("stock_code"),
                "stock_name": row.get("stock_name"),
                "buy_price": _safe_float(row.get("buy_price")),
                "sell_price": _safe_float(row.get("sell_price")),
                "buy_qty": _safe_float(row.get("buy_qty")),
            }
            if record_id in ambiguous_record_ids:
                duplicate_row_count += 1
                continue
            prior = by_record.get(record_id)
            if prior is None:
                by_record[record_id] = outcome
                continue
            duplicate_row_count += 1
            merged = _merge_if_compatible(prior, outcome)
            if merged is None:
                ambiguous_record_ids.add(record_id)
                by_record.pop(record_id, None)
            else:
                compatible_duplicate_row_count += 1
                by_record[record_id] = merged
    diagnostics = {
        "join_key": "recommendation_id_with_stock_code_validation",
        "duplicate_row_count": duplicate_row_count,
        "compatible_duplicate_row_count": compatible_duplicate_row_count,
        "ambiguous_record_id_count": len(ambiguous_record_ids),
        "ambiguous_record_ids": sorted(ambiguous_record_ids),
        "invalid_json_row_count": invalid_json_row_count,
        "last_row_wins_allowed": False,
    }
    return by_record, source_paths, diagnostics


def _joined_rows(
    forced: dict[str, dict[str, Any]],
    threshold_counts: dict[str, Counter[str]],
    primary_blockers: dict[str, dict[str, Any]],
    post_sell_by_record: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record_id, entry in forced.items():
        outcome = post_sell_by_record.get(record_id) or {}
        forced_stock_code = str(entry.get("stock_code") or "").strip()[:6]
        outcome_stock_code = str(outcome.get("stock_code") or "").strip()[:6]
        entry_date = str(entry.get("entry_date") or "")
        outcome_date = str(outcome.get("signal_date") or "")
        forced_stock_code_missing = not forced_stock_code
        post_sell_stock_code_missing = bool(outcome) and not outcome_stock_code
        post_sell_stock_code_conflict = bool(
            outcome
            and forced_stock_code
            and outcome_stock_code
            and forced_stock_code != outcome_stock_code
        )
        post_sell_date_conflict = bool(
            outcome and entry_date and outcome_date and outcome_date < entry_date
        )
        forced_identity_conflict = bool(entry.get("forced_identity_conflict"))
        terminal_sell_time = _event_time(entry.get("terminal_sell_time"))
        forced_entry_time = _event_time(entry.get("entry_time"))
        terminal_sell_stock_code = str(
            entry.get("terminal_sell_stock_code") or ""
        ).strip()[:6]
        terminal_identity_conflict = bool(
            entry.get("terminal_sell_identity_conflict")
            or (
                entry.get("terminal_sell_observed")
                and (
                    terminal_sell_time is None
                    or forced_entry_time is None
                    or terminal_sell_time < forced_entry_time
                    or not terminal_sell_stock_code
                    or (
                        forced_stock_code
                        and terminal_sell_stock_code != forced_stock_code
                    )
                )
            )
        )
        if (
            post_sell_stock_code_conflict
            or forced_stock_code_missing
            or post_sell_stock_code_missing
            or post_sell_date_conflict
            or forced_identity_conflict
            or terminal_identity_conflict
        ):
            outcome = {}
        groups = sorted(threshold_counts.get(record_id, Counter()))
        primary_event = primary_blockers.get(record_id) or {}
        causal_primary_event = bool(
            primary_event and _primary_blocker_precedes_force(primary_event, entry)
        )
        primary_groups = (
            list(primary_event.get("groups") or []) if causal_primary_event else []
        )
        primary_group = primary_groups[0] if len(primary_groups) == 1 else None
        primary_status = (
            "exact_single_group_first_blocker"
            if primary_group
            else (
                "ambiguous_multi_group_first_blocker"
                if primary_groups
                else (
                    "post_force_or_unordered_blocker_only"
                    if primary_event
                    else "missing_explicit_blocker"
                )
            )
        )
        profit = outcome.get("profit_rate")
        rows.append(
            {
                **entry,
                "record_id": record_id,
                "threshold_groups": groups,
                "threshold_group_counts": dict(
                    threshold_counts.get(record_id, Counter())
                ),
                "primary_threshold_group": primary_group,
                "primary_blocker_attribution_status": primary_status,
                "primary_blocker_event": primary_event,
                "post_sell_joined": bool(outcome),
                "source_identity_status": (
                    "forced_record_id_reused"
                    if forced_identity_conflict
                    else (
                        "forced_stock_code_missing"
                        if forced_stock_code_missing
                        else (
                            "terminal_sell_identity_conflict"
                            if terminal_identity_conflict
                            else (
                                "post_sell_stock_code_missing"
                                if post_sell_stock_code_missing
                                else (
                                    "post_sell_stock_code_conflict"
                                    if post_sell_stock_code_conflict
                                    else (
                                        "post_sell_before_forced_entry"
                                        if post_sell_date_conflict
                                        else "valid"
                                    )
                                )
                            )
                        )
                    )
                ),
                "profit_rate": profit,
                "peak_profit": outcome.get("peak_profit"),
                "held_sec": outcome.get("held_sec"),
                "exit_rule": outcome.get("exit_rule"),
                "profitable": bool(profit is not None and profit > 0),
            }
        )
    return rows


def _profit_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profits = [row["profit_rate"] for row in rows if row.get("profit_rate") is not None]
    winners = [value for value in profits if value > 0]
    losses = [value for value in profits if value <= 0]
    return {
        "sample": len(rows),
        "valid_profit_sample": len(profits),
        "profitable_count": len(winners),
        "loss_or_flat_count": len(losses),
        "equal_weight_avg_profit_pct": (
            round(sum(profits) / len(profits), 6) if profits else None
        ),
        "min_profit_pct": min(profits) if profits else None,
        "max_profit_pct": max(profits) if profits else None,
    }


def _threshold_group_evaluations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build overlapping fixed-taxonomy diagnostics, never actionable candidates."""

    evaluations: list[dict[str, Any]] = []
    joined = [row for row in rows if row.get("post_sell_joined")]
    for group, spec in THRESHOLD_GROUPS.items():
        group_rows = [
            row for row in joined if group in set(row.get("threshold_groups") or [])
        ]
        if not group_rows:
            continue
        summary = _profit_summary(group_rows)
        evaluations.append(
            {
                "evaluation_id": f"one_share_threshold_group_{group}",
                "threshold_group": group,
                "mapped_family": spec["hook_family"],
                "target_subsystem": spec["target_subsystem"],
                "sample": summary["sample"],
                "valid_profit_sample": summary["valid_profit_sample"],
                "profitable_count": summary["profitable_count"],
                "loss_or_flat_count": summary["loss_or_flat_count"],
                "equal_weight_avg_profit_pct": summary["equal_weight_avg_profit_pct"],
                "primary_decision_metric": "equal_weight_avg_profit_pct",
                "classification_role": "overlapping_fixed_taxonomy_diagnostic",
                "is_actionable_candidate": False,
                "groups_are_mutually_exclusive": False,
                "causal_threshold_attribution_allowed": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
                "example_records": [
                    {
                        "record_id": row.get("record_id"),
                        "stock_code": row.get("stock_code"),
                        "stock_name": row.get("stock_name"),
                        "profit_rate": row.get("profit_rate"),
                        "threshold_groups": row.get("threshold_groups"),
                    }
                    for row in group_rows[:8]
                ],
            }
        )
    return sorted(
        evaluations,
        key=lambda item: (
            item.get("equal_weight_avg_profit_pct") is not None,
            item.get("equal_weight_avg_profit_pct") or -999,
            item.get("sample") or 0,
        ),
        reverse=True,
    )


def _primary_blocker_evaluations(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build mutually exclusive first-blocker evaluations before candidate gates."""

    opportunities: list[dict[str, Any]] = []
    joined = [row for row in rows if row.get("post_sell_joined")]
    for group, spec in THRESHOLD_GROUPS.items():
        group_rows = [
            row for row in joined if row.get("primary_threshold_group") == group
        ]
        if not group_rows:
            continue
        summary = _profit_summary(group_rows)
        avg = summary["equal_weight_avg_profit_pct"]
        eligible = bool(
            summary["valid_profit_sample"] >= 3
            and avg is not None
            and avg > 0
            and group != "cooldown_or_hard_safety"
        )
        opportunities.append(
            {
                "candidate_id": f"one_share_threshold_{group}",
                "threshold_group": group,
                "mapped_family": spec["hook_family"],
                "target_subsystem": spec["target_subsystem"],
                "sample": summary["sample"],
                "valid_profit_sample": summary["valid_profit_sample"],
                "profitable_count": summary["profitable_count"],
                "loss_or_flat_count": summary["loss_or_flat_count"],
                "equal_weight_avg_profit_pct": avg,
                "primary_decision_metric": "equal_weight_avg_profit_pct",
                "classification_role": "exclusive_first_observed_blocker_evaluation",
                "primary_blocker_attribution_status": "pass",
                "is_actionable_candidate": eligible,
                "candidate_status": (
                    "eligible_for_existing_family_evidence"
                    if eligible
                    else "diagnostic_not_actionable"
                ),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "forbidden_uses": FORBIDDEN_USES,
                "example_records": [
                    {
                        "record_id": row.get("record_id"),
                        "stock_code": row.get("stock_code"),
                        "stock_name": row.get("stock_name"),
                        "profit_rate": row.get("profit_rate"),
                        "primary_blocker_event": row.get("primary_blocker_event"),
                    }
                    for row in group_rows[:8]
                ],
            }
        )
    return sorted(
        opportunities,
        key=lambda item: (
            item.get("candidate_status") == "eligible_for_existing_family_evidence",
            item.get("equal_weight_avg_profit_pct") is not None,
            item.get("equal_weight_avg_profit_pct") or -999,
            item.get("sample") or 0,
        ),
        reverse=True,
    )


def _threshold_opportunities(
    primary_blocker_evaluations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return only floor-qualified positive-EV existing-family candidates."""

    return [
        {
            **item,
            "classification_role": "eligible_existing_family_evidence_candidate",
            "is_actionable_candidate": True,
        }
        for item in primary_blocker_evaluations
        if item.get("candidate_status") == "eligible_for_existing_family_evidence"
    ]


def _build_code_orders(
    opportunities: list[dict[str, Any]], source_paths: dict[str, Any]
) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    for item in opportunities:
        sample = int(item.get("sample") or 0)
        valid_profit_sample = int(item.get("valid_profit_sample") or 0)
        avg = item.get("equal_weight_avg_profit_pct")
        if (
            item.get("candidate_status") != "eligible_for_existing_family_evidence"
            or item.get("primary_blocker_attribution_status") != "pass"
            or valid_profit_sample < 3
            or avg is None
            or avg <= 0
        ):
            continue
        group = str(item.get("threshold_group") or "")
        if group == "cooldown_or_hard_safety":
            continue
        priority = 1 if sample >= 10 and avg >= 0.2 else 2
        orders.append(
            {
                "order_id": f"order_{item['candidate_id']}_entry_hook_review",
                "candidate_id": item["candidate_id"],
                "title": (
                    f"one-share threshold opportunity existing-family evidence: {group}"
                ),
                "source_report_type": REPORT_TYPE,
                "lifecycle_stage": "entry",
                "target_subsystem": item.get("target_subsystem"),
                "route": "existing_family",
                "mapped_family": item.get("mapped_family"),
                "threshold_family": item.get("mapped_family"),
                "improvement_type": "source_only_existing_family_evidence",
                "confidence": (
                    "rolling_source_only" if sample >= 10 else "thin_source_only"
                ),
                "priority": priority,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "implementation_status": "source_evidence_candidate",
                "implementation_provenance": {
                    "implementation_type": "one_share_threshold_opportunity_audit",
                    "source_audit_implementation_status": "implemented",
                    "implemented_scope": (
                        "source-only threshold group audit and existing-family evidence "
                        "provenance only"
                    ),
                    "target_hook_implementation_status": (
                        "requires_independent_verification"
                    ),
                    "workorder_intake_role": "attach_existing_family_evidence",
                    "decision_authority": "source_only_threshold_opportunity_audit",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "requires_separate_runtime_apply_candidate": True,
                    "runtime_mutation_allowed": False,
                    "sample": sample,
                    "valid_profit_sample": valid_profit_sample,
                    "equal_weight_avg_profit_pct": avg,
                    "threshold_group": group,
                    "primary_blocker_attribution_status": item.get(
                        "primary_blocker_attribution_status"
                    ),
                    "mapped_family": item.get("mapped_family"),
                    "primary_decision_metric": "equal_weight_avg_profit_pct",
                    "source_quality_gate": (
                        "unambiguous_record_id_and_stock_code_joined_forced_"
                        "one_share_event_to_post_sell_outcome"
                    ),
                    "forbidden_uses": FORBIDDEN_USES,
                },
                "expected_ev_effect": (
                    "Attach one-share forced-entry post-sell evidence to the existing family without "
                    "treating positive EV as a code defect or standalone real-order approval evidence."
                ),
                "evidence": [
                    f"threshold_group={group}",
                    f"sample={sample}",
                    f"valid_profit_sample={valid_profit_sample}",
                    f"profitable_count={item.get('profitable_count')}",
                    f"loss_or_flat_count={item.get('loss_or_flat_count')}",
                    f"equal_weight_avg_profit_pct={avg}",
                    "runtime_effect=false",
                    "allowed_runtime_apply=false",
                ],
                "source_paths": [
                    path
                    for values in source_paths.values()
                    for path in (values if isinstance(values, list) else [values])
                ],
                "files_likely_touched": [],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_build_code_improvement_workorder.py",
                    "A separate source-gap/root-cause order is required before any implementation decision",
                    "source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps",
                ],
                "forbidden_uses": FORBIDDEN_USES,
            }
        )
    return orders


def _actionable_semantic_digest(report: dict[str, Any]) -> str:
    payload = [
        {
            key: value
            for key, value in item.items()
            if not str(key).startswith("ai_") and key != "source_paths"
        }
        for item in report.get("code_improvement_orders") or []
        if isinstance(item, dict)
    ]
    encoded = json.dumps(
        sorted(payload, key=lambda item: str(item.get("order_id") or "")),
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _load_previous_report(target_date: str) -> tuple[dict[str, Any] | None, str | None]:
    report_dir = PROJECT_ROOT / "data" / "report" / REPORT_TYPE
    candidates = sorted(
        (
            path
            for path in report_dir.glob(f"{REPORT_TYPE}_*.json")
            if _date_from_path(path) and _date_from_path(path) < target_date
        ),
        reverse=True,
    )
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            isinstance(payload, dict)
            and payload.get("report_type") == REPORT_TYPE
            and str(payload.get("target_date") or "") < target_date
        ):
            return payload, str(path)
    return None, None


def _annotate_candidate_change(
    report: dict[str, Any],
    *,
    previous_report: dict[str, Any] | None,
    previous_report_path: str | None,
    ai_provider: str,
) -> None:
    current_digest = _actionable_semantic_digest(report)
    previous_digest = (
        _actionable_semantic_digest(previous_report) if previous_report else None
    )
    current_ids = sorted(
        str(item.get("order_id") or "")
        for item in report.get("code_improvement_orders") or []
        if isinstance(item, dict) and item.get("order_id")
    )
    previous_ids = sorted(
        str(item.get("order_id") or "")
        for item in (previous_report or {}).get("code_improvement_orders") or []
        if isinstance(item, dict) and item.get("order_id")
    )
    if previous_report is None:
        status = "first_observation"
    elif current_digest == previous_digest:
        status = "unchanged"
    else:
        status = "changed"
    current_ai_contract = _ai_review_contract(ai_provider)
    previous_ai_contract = (
        previous_report.get("ai_review_contract")
        if isinstance((previous_report or {}).get("ai_review_contract"), dict)
        else {}
    )
    if previous_report is None:
        ai_contract_change_status = "first_observation"
    elif previous_ai_contract.get("semantic_digest") == current_ai_contract.get(
        "semantic_digest"
    ):
        ai_contract_change_status = "unchanged"
    else:
        ai_contract_change_status = "changed"
    report["ai_review_contract"] = current_ai_contract
    report["candidate_change"] = {
        "status": status,
        "semantic_digest": current_digest,
        "previous_semantic_digest": previous_digest,
        "previous_report_path": previous_report_path,
        "new_order_ids": sorted(set(current_ids) - set(previous_ids)),
        "removed_order_ids": sorted(set(previous_ids) - set(current_ids)),
        "unchanged_order_ids": sorted(set(current_ids) & set(previous_ids)),
        "ai_review_contract_change_status": ai_contract_change_status,
        "semantic_change_requires_new_ai_review": (
            bool(current_ids)
            and (status != "unchanged" or ai_contract_change_status != "unchanged")
        ),
    }
    report["summary"]["candidate_change_status"] = status
    report["summary"]["actionable_semantic_digest"] = current_digest


def _parse_ai_review(raw_response: Any | None) -> tuple[str, dict[str, Any], list[str]]:
    if raw_response in (None, ""):
        return "unavailable", {}, ["ai_review_response_missing"]
    try:
        payload = json.loads(str(raw_response))
    except json.JSONDecodeError as exc:
        return "parse_rejected", {}, [f"ai_review_json_parse_failed:{exc}"]
    if not isinstance(payload, dict):
        return "parse_rejected", {}, ["ai_review_non_dict"]
    warnings: list[str] = []
    try:
        schema_version = int(payload.get("schema_version") or 0)
    except (TypeError, ValueError):
        schema_version = 0
    if schema_version != 1:
        warnings.append("ai_review_schema_version_invalid")
    if str(payload.get("reviewer") or "") != AI_REVIEWER_NAME:
        warnings.append("ai_review_reviewer_invalid")
    if not isinstance(payload.get("candidate_reviews"), list):
        warnings.append("ai_review_candidate_reviews_missing")
    if not isinstance(payload.get("audit"), dict):
        warnings.append("ai_review_audit_missing")
    return ("parsed" if not warnings else "parse_rejected"), payload, warnings


def _ai_review_instructions() -> str:
    return (
        "You are one_share_threshold_opportunity_ai_review. Use English only. "
        "Return strict JSON matching one_share_threshold_opportunity_ai_review_v1. "
        "Review only source-only entry hook workorders. You cannot approve real orders, "
        "runtime threshold mutation, broker guard bypass, stale submit bypass, provider route changes, "
        "bot restarts, quantity/cap changes, or real execution quality approval. "
        "If evidence is thin or mixed, recommend keep_collecting or code_patch_required with concrete tests."
    )


def _resolved_ai_review_config(provider: str):
    config = resolve_postclose_ai_review_config(
        REPORT_TYPE,
        default_model="gpt-5.4-mini",
        default_reasoning_effort="medium",
        default_timeout_sec=180,
        env_prefix="KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI",
    )
    if provider:
        config = config.__class__(**{**config.__dict__, "primary_provider": provider})
    return config


def _ai_review_contract(provider: str) -> dict[str, Any]:
    config = _resolved_ai_review_config(provider)
    details = {
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "schema": AI_RESPONSE_SCHEMA_REGISTRY.get(AI_REVIEW_SCHEMA_NAME),
        "reviewer": AI_REVIEWER_NAME,
        "instructions": _ai_review_instructions(),
        "requested_provider": provider or "none",
        "provider_config": config.provider_status_fields(),
    }
    encoded = json.dumps(
        details, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    )
    return {
        "semantic_digest": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        **details,
    }


def _ai_review_context(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "target_date": report.get("target_date"),
        "window": report.get("window"),
        "summary": report.get("summary"),
        "metric_contract": report.get("metric_contract"),
        "opportunities": report.get("threshold_opportunities"),
        "code_improvement_orders": report.get("code_improvement_orders"),
    }


def _call_ai_review(
    report: dict[str, Any], *, provider: str
) -> tuple[str, dict[str, Any]]:
    if provider in {"", "none", "off", "false", "0"}:
        return "", {
            "provider": provider or "none",
            "status": "disabled",
            "reason": "ai_provider_disabled",
        }
    from src.engine.ai.postclose_structured_review_provider import (
        call_postclose_structured_review,
    )

    config = _resolved_ai_review_config(provider)
    return call_postclose_structured_review(
        _ai_review_context(report),
        schema_name=AI_REVIEW_SCHEMA_NAME,
        instructions=_ai_review_instructions(),
        config=config,
        metadata={"endpoint_name": AI_REVIEWER_NAME, "report_type": REPORT_TYPE},
        ensure_ascii=True,
    )


def _apply_ai_review(
    report: dict[str, Any],
    *,
    provider: str,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    coverage = (
        report.get("source_coverage_manifest")
        if isinstance(report.get("source_coverage_manifest"), dict)
        else {}
    )
    candidate_change = (
        report.get("candidate_change")
        if isinstance(report.get("candidate_change"), dict)
        else {}
    )
    orders = [
        item
        for item in report.get("code_improvement_orders") or []
        if isinstance(item, dict)
    ]
    prior_review = (
        previous_report.get("ai_review")
        if isinstance((previous_report or {}).get("ai_review"), dict)
        else {}
    )
    prior_order_rows = [
        item
        for item in (previous_report or {}).get("code_improvement_orders") or []
        if isinstance(item, dict) and item.get("candidate_id")
    ]
    prior_orders = {
        str(item.get("candidate_id") or ""): item for item in prior_order_rows
    }
    current_candidate_ids = {
        str(item.get("candidate_id") or "")
        for item in orders
        if item.get("candidate_id")
    }
    prior_review_complete = bool(
        current_candidate_ids
        and len(prior_orders) == len(prior_order_rows) == len(current_candidate_ids)
        and set(prior_orders) == current_candidate_ids
        and int(prior_review.get("reviewed_candidate_count") or 0)
        == len(current_candidate_ids)
        and all(
            str(item.get("ai_review_status") or "") == "parsed"
            and bool(str(item.get("ai_recommended_disposition") or "").strip())
            and bool(str(item.get("ai_review_confidence") or "").strip())
            and bool(str(item.get("ai_review_reason") or "").strip())
            and isinstance(item.get("ai_required_followup"), list)
            for item in prior_orders.values()
        )
    )
    can_reuse_prior_review = bool(
        candidate_change.get("status") == "unchanged"
        and candidate_change.get("ai_review_contract_change_status") == "unchanged"
        and prior_review.get("status") == "parsed"
        and prior_review.get("provider") == provider
        and prior_review_complete
    )
    if str(coverage.get("status") or "") != "pass":
        status = "blocked_source_coverage"
        payload: dict[str, Any] = {}
        warnings = ["ai_review_skipped_source_coverage_gap"]
        provider_status = {
            "provider": provider or "none",
            "status": "blocked_source_coverage",
            "reason": "source_coverage_gate_not_passed",
            "new_provider_call": False,
        }
    elif not orders:
        status = "not_required_no_actionable_candidate"
        payload = {}
        warnings = []
        provider_status = {
            "provider": provider or "none",
            "status": "not_required",
            "reason": "no_actionable_source_only_candidate",
            "new_provider_call": False,
        }
    elif can_reuse_prior_review:
        status = "parsed"
        payload = {
            "candidate_reviews": [
                {
                    "candidate_id": candidate_id,
                    "recommended_disposition": item.get("ai_recommended_disposition"),
                    "confidence": item.get("ai_review_confidence"),
                    "reason": item.get("ai_review_reason"),
                    "required_followup": item.get("ai_required_followup") or [],
                }
                for candidate_id, item in sorted(prior_orders.items())
            ],
            "audit": prior_review.get("audit") or {},
            "codex_directives": prior_review.get("codex_directives") or [],
        }
        warnings = []
        provider_status = {
            "provider": provider,
            "status": "reused",
            "reason": "unchanged_actionable_and_ai_contract_semantic_digests",
            "new_provider_call": False,
            "reused_target_date": (previous_report or {}).get("target_date"),
            "reused_semantic_digest": candidate_change.get("semantic_digest"),
            "reused_candidate_count": len(current_candidate_ids),
        }
    else:
        raw, provider_status = _call_ai_review(report, provider=provider)
        provider_status = dict(provider_status)
        provider_status.setdefault(
            "new_provider_call",
            provider not in {"", "none", "off", "false", "0"},
        )
        status, payload, warnings = _parse_ai_review(raw)
    if status == "parsed":
        review_rows = [
            item
            for item in (payload.get("candidate_reviews") or [])
            if isinstance(item, dict)
        ]
        review_ids = [str(item.get("candidate_id") or "") for item in review_rows]
        allowed_dispositions = {
            "keep_collecting",
            "code_patch_required",
            "attach_existing_entry_hook",
            "source_quality_blocker",
            "safety_veto",
            "reject",
        }
        review_rows_complete = all(
            str(item.get("recommended_disposition") or "") in allowed_dispositions
            and str(item.get("confidence") or "") in {"low", "medium", "high"}
            and bool(str(item.get("reason") or "").strip())
            and isinstance(item.get("required_followup"), list)
            for item in review_rows
        )
        if (
            any(not candidate_id for candidate_id in review_ids)
            or len(set(review_ids)) != len(review_ids)
            or set(review_ids) != current_candidate_ids
            or not review_rows_complete
        ):
            status = "parse_rejected"
            warnings = [
                *warnings,
                "ai_review_candidate_census_mismatch:"
                f"expected={sorted(current_candidate_ids)}:observed={sorted(review_ids)}",
            ]
    review_by_candidate = {
        str(item.get("candidate_id")): item
        for item in (payload.get("candidate_reviews") or [])
        if isinstance(item, dict)
    }
    for order in report.get("code_improvement_orders") or []:
        review = review_by_candidate.get(str(order.get("candidate_id")))
        if review:
            order["ai_review_status"] = status
            order["ai_recommended_disposition"] = review.get("recommended_disposition")
            order["ai_review_confidence"] = review.get("confidence")
            order["ai_review_reason"] = review.get("reason")
            order["ai_required_followup"] = review.get("required_followup") or []
        elif status == "parsed":
            order["ai_review_status"] = "unreviewed"
        else:
            order["ai_review_status"] = status
    report["ai_review"] = {
        "schema_name": AI_REVIEW_SCHEMA_NAME,
        "reviewer": AI_REVIEWER_NAME,
        "provider": provider,
        "status": status,
        "provider_status": provider_status,
        "warnings": warnings,
        "audit": payload.get("audit") if isinstance(payload.get("audit"), dict) else {},
        "codex_directives": (
            payload.get("codex_directives")
            if isinstance(payload.get("codex_directives"), list)
            else []
        ),
        "reviewed_candidate_count": len(review_by_candidate),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }
    report["summary"]["ai_review_status"] = status
    report["summary"]["ai_reviewed_candidate_count"] = len(review_by_candidate)
    return report


def build_report(
    target_date: str,
    *,
    since_date: str | None = None,
    pipeline_paths: list[Path] | None = None,
    post_sell_paths: list[Path] | None = None,
    generated_at: str | None = None,
    ai_provider: str = "none",
    partition_cache_dir: Path | None = None,
    use_partition_cache: bool | None = None,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    started_monotonic = time.monotonic()
    since_date = (
        since_date
        or os.getenv("KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_SINCE_DATE")
        or CLEAN_BASELINE_DATE
    )
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    using_default_pipeline_paths = pipeline_paths is None
    using_default_post_sell_paths = post_sell_paths is None
    if pipeline_paths is None:
        pipeline_paths = _pipeline_paths(since_date=since_date, until_date=target_date)
    if post_sell_paths is None:
        post_sell_paths = _post_sell_paths(
            since_date=since_date, until_date=target_date
        )
    if use_partition_cache is None:
        use_partition_cache = using_default_pipeline_paths
    if use_partition_cache and partition_cache_dir is None:
        partition_cache_dir = (
            PROJECT_ROOT / "data" / "report" / REPORT_TYPE / "partition_index_cache"
        )
    if not use_partition_cache:
        partition_cache_dir = None
    (
        forced,
        threshold_counts,
        primary_blockers,
        pipeline_sources,
        source_processing,
    ) = _build_forced_index(pipeline_paths, cache_dir=partition_cache_dir)
    (
        post_sell_by_record,
        post_sell_sources,
        post_sell_identity_diagnostics,
    ) = _load_post_sell(post_sell_paths)
    rows = _joined_rows(forced, threshold_counts, primary_blockers, post_sell_by_record)
    joined = [row for row in rows if row.get("post_sell_joined")]
    forced_record_ids = {str(record_id) for record_id in forced}
    post_sell_ambiguous_record_ids = (
        set(post_sell_identity_diagnostics.get("ambiguous_record_ids") or [])
        & forced_record_ids
    )
    source_identity_conflict_record_ids = {
        str(row.get("record_id") or "")
        for row in rows
        if row.get("source_identity_status") != "valid"
    } | post_sell_ambiguous_record_ids
    submitted_unjoined_record_ids = {
        str(row.get("record_id") or "")
        for row in rows
        if row.get("actual_order_submitted_observed")
        and not row.get("post_sell_joined")
    }
    coverage_manifest = _source_coverage_manifest(
        pipeline_paths=pipeline_paths,
        post_sell_paths=post_sell_paths,
        since_date=since_date,
        until_date=target_date,
        terminal_sell_record_ids={
            str(item.get("record_id") or "")
            for item in forced.values()
            if item.get("terminal_sell_observed")
        },
        post_sell_record_ids=post_sell_by_record,
        submitted_unjoined_record_ids=submitted_unjoined_record_ids,
        identity_conflict_record_ids=source_identity_conflict_record_ids,
        invalid_source_json_row_count=(
            int(source_processing.get("invalid_json_row_count") or 0)
            + int(post_sell_identity_diagnostics.get("invalid_json_row_count") or 0)
        ),
    )
    group_evaluations = _threshold_group_evaluations(rows)
    primary_blocker_evaluations = _primary_blocker_evaluations(rows)
    opportunities = _threshold_opportunities(primary_blocker_evaluations)
    source_paths = {
        "pipeline_events": pipeline_sources,
        "post_sell_candidates": post_sell_sources,
    }
    orders = (
        _build_code_orders(opportunities, source_paths)
        if coverage_manifest.get("status") == "pass"
        else []
    )
    threshold_group_counts = Counter(
        group for row in rows for group in row.get("threshold_groups") or []
    )
    submitted_rows = [row for row in rows if row.get("actual_order_submitted_observed")]
    probe_first_rows = [
        row for row in rows if row.get("entry_split_probe_first_applied_observed")
    ]
    variant_rows = [
        row
        for row in rows
        if str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    submitted_split_provenance_rows = [
        row
        for row in submitted_rows
        if str(row.get("entry_split_probe_bundle_id") or "").strip()
        or str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    probe_first_submitted_rows = [
        row
        for row in submitted_rows
        if row.get("entry_split_probe_first_applied_observed")
    ]
    probe_first_submit_with_provenance_rows = [
        row
        for row in probe_first_submitted_rows
        if str(row.get("entry_split_probe_bundle_id") or "").strip()
        or str(row.get("entry_split_order_variant_id") or "").strip()
    ]
    probe_first_provenance_gap_count = len(probe_first_submitted_rows) - len(
        probe_first_submit_with_provenance_rows
    )
    residual_submitted_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if row.get("entry_split_residual_submitted_observed") is True
    ]
    residual_blocked_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if row.get("entry_split_residual_blocked_observed") is True
    ]
    residual_not_submitted_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if _residual_not_submitted_source(row)
    ]
    residual_not_submitted_source_counts = Counter(
        _residual_not_submitted_source(row) for row in residual_not_submitted_rows
    )
    residual_terminal_abort_reason_counts = Counter(
        str(row.get("entry_split_probe_abort_reason") or "unknown")
        for row in residual_not_submitted_rows
    )
    residual_terminal_abort_detail_reason_counts = Counter(
        str(row.get("entry_split_probe_terminal_abort_detail_reason") or "unknown")
        for row in residual_not_submitted_rows
    )
    residual_terminal_failure_signature_coverage_count = sum(
        1
        for row in residual_not_submitted_rows
        if str(row.get("entry_split_probe_terminal_failure_signature") or "").strip()
        not in {"", "-"}
    )
    resolved_probe_record_ids = {
        str(row.get("record_id") or "")
        for row in residual_submitted_rows + residual_not_submitted_rows
    }
    unresolved_probe_rows = [
        row
        for row in probe_first_submit_with_provenance_rows
        if str(row.get("record_id") or "") not in resolved_probe_record_ids
    ]
    probe_to_residual_resolution_count = len(resolved_probe_record_ids)
    probe_to_residual_resolution_coverage_pct = (
        round(
            probe_to_residual_resolution_count
            / len(probe_first_submit_with_provenance_rows)
            * 100.0,
            4,
        )
        if probe_first_submit_with_provenance_rows
        else None
    )
    probe_to_residual_status = (
        "no_natural_sample"
        if not probe_first_submitted_rows
        else (
            "instrumentation_gap"
            if probe_first_provenance_gap_count > 0 or unresolved_probe_rows
            else "observed"
        )
    )
    probe_to_residual_by_entry_date: dict[str, dict[str, Any]] = {}
    probe_entry_dates = {
        str(row.get("entry_date") or "")
        for row in probe_first_submitted_rows
        if str(row.get("entry_date") or "")
    }
    probe_entry_dates.add(target_date)
    for entry_date in sorted(probe_entry_dates):
        date_submitted_rows = [
            row
            for row in probe_first_submitted_rows
            if str(row.get("entry_date") or "") == entry_date
        ]
        date_provenance_rows = [
            row
            for row in date_submitted_rows
            if str(row.get("entry_split_probe_bundle_id") or "").strip()
            or str(row.get("entry_split_order_variant_id") or "").strip()
        ]
        date_residual_submitted_rows = [
            row
            for row in date_provenance_rows
            if row.get("entry_split_residual_submitted_observed") is True
        ]
        date_residual_blocked_rows = [
            row
            for row in date_provenance_rows
            if row.get("entry_split_residual_blocked_observed") is True
        ]
        date_residual_not_submitted_rows = [
            row for row in date_provenance_rows if _residual_not_submitted_source(row)
        ]
        date_resolved_record_ids = {
            str(row.get("record_id") or "")
            for row in date_residual_submitted_rows + date_residual_not_submitted_rows
        }
        date_unresolved_count = sum(
            1
            for row in date_provenance_rows
            if str(row.get("record_id") or "") not in date_resolved_record_ids
        )
        date_provenance_gap_count = len(date_submitted_rows) - len(date_provenance_rows)
        date_status = (
            "no_natural_sample"
            if not date_submitted_rows
            else (
                "instrumentation_gap"
                if date_provenance_gap_count > 0 or date_unresolved_count > 0
                else "observed"
            )
        )
        probe_to_residual_by_entry_date[entry_date] = {
            "status": date_status,
            "probe_first_submitted_count": len(date_submitted_rows),
            "probe_first_submit_with_provenance_count": len(date_provenance_rows),
            "probe_first_submit_provenance_gap_count": (date_provenance_gap_count),
            "resolution_count": len(date_resolved_record_ids),
            "resolution_coverage_pct": (
                round(
                    len(date_resolved_record_ids) / len(date_provenance_rows) * 100.0,
                    4,
                )
                if date_provenance_rows
                else None
            ),
            "residual_submitted_record_count": len(date_residual_submitted_rows),
            "residual_blocked_record_count": len(date_residual_blocked_rows),
            "residual_not_submitted_record_count": len(
                date_residual_not_submitted_rows
            ),
            "residual_not_submitted_source_counts": dict(
                sorted(
                    Counter(
                        _residual_not_submitted_source(row)
                        for row in date_residual_not_submitted_rows
                    ).items()
                )
            ),
            "residual_terminal_abort_detail_reason_counts": dict(
                sorted(
                    Counter(
                        str(
                            row.get("entry_split_probe_terminal_abort_detail_reason")
                            or "unknown"
                        )
                        for row in date_residual_not_submitted_rows
                    ).items()
                )
            ),
            "unresolved_record_count": date_unresolved_count,
        }
    probe_split_attribution = {
        "status": (
            "no_natural_sample"
            if not rows
            else (
                "instrumentation_gap"
                if probe_first_provenance_gap_count > 0
                else "observed"
            )
        ),
        "intent_record_count": len(rows),
        "actual_submit_observed_count": len(submitted_rows),
        "probe_first_observed_count": len(probe_first_rows),
        "entry_split_variant_observed_count": len(variant_rows),
        "submitted_split_provenance_count": len(submitted_split_provenance_rows),
        "submitted_split_provenance_gap_count": (probe_first_provenance_gap_count),
        "probe_first_submitted_count": len(probe_first_submitted_rows),
        "probe_first_submit_with_provenance_count": len(
            probe_first_submit_with_provenance_rows
        ),
        "probe_to_residual_status": probe_to_residual_status,
        "probe_to_residual_resolution_count": (probe_to_residual_resolution_count),
        "probe_to_residual_resolution_coverage_pct": (
            probe_to_residual_resolution_coverage_pct
        ),
        "residual_submitted_record_count": len(residual_submitted_rows),
        "residual_blocked_record_count": len(residual_blocked_rows),
        "residual_not_submitted_record_count": len(residual_not_submitted_rows),
        "residual_not_submitted_source_counts": dict(
            sorted(residual_not_submitted_source_counts.items())
        ),
        "residual_terminal_abort_reason_counts": dict(
            sorted(residual_terminal_abort_reason_counts.items())
        ),
        "residual_terminal_abort_detail_reason_counts": dict(
            sorted(residual_terminal_abort_detail_reason_counts.items())
        ),
        "residual_terminal_failure_signature_coverage_count": (
            residual_terminal_failure_signature_coverage_count
        ),
        "probe_to_residual_unresolved_record_count": len(unresolved_probe_rows),
        "probe_to_residual_by_entry_date": probe_to_residual_by_entry_date,
        "target_date_probe_to_residual": probe_to_residual_by_entry_date[target_date],
        "legacy_or_non_split_submit_count": (
            len(submitted_rows) - len(probe_first_submitted_rows)
        ),
        "post_sell_joined_count": len(joined),
        "pending_or_unjoined_count": len(rows) - len(joined),
        "join_owner": "record_id_to_post_sell_recommendation_id",
        "execution_shape_owner": "entry_split_order_plan",
        "scale_in_owner": "scale_in_split_order_plan_avg_down_only",
        "probe_to_residual_contract": {
            "metric_role": "real_execution_quality_attribution",
            "decision_authority": "source_only_probe_residual_attribution",
            "window_policy": (
                "record_lineage_from_probe_submit_to_residual_terminal_event"
            ),
            "sample_floor": "one_probe_first_submit_with_split_provenance",
            "primary_decision_metric": ("probe_to_residual_resolution_coverage_pct"),
            "source_quality_gate": (
                "record_id_split_bundle_or_variant_and_terminal_event_or_"
                "legacy_aborted_phase_fallback"
            ),
            "forbidden_uses": FORBIDDEN_USES,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "decision_authority": "source_only_probe_split_attribution",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": FORBIDDEN_USES,
    }
    source_processing["elapsed_seconds"] = round(
        time.monotonic() - started_monotonic, 6
    )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "window": {
            "since_date": since_date,
            "until_date": target_date,
            "clean_baseline_ts_kst": CLEAN_BASELINE_TS_KST,
            "window_policy": "all_available_since_clean_baseline_or_configured_start",
            "baseline_row_filter": "pipeline rows before clean_baseline_ts_kst are excluded",
        },
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "source_only_threshold_opportunity_audit",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": {
            "metric_role": "real_one_share_probe_source_only_ev",
            "decision_authority": "source_only_threshold_opportunity_audit",
            "window_policy": "all_available_one_share_forced_events_since_configured_start",
            "sample_floor": "3_valid_profit_post_sell_rows_per_exclusive_first_blocker_for_workorder",
            "primary_decision_metric": "equal_weight_avg_profit_pct",
            "profit_rate_source": (
                "post_sell_profit_rate_from_fee_aware_or_broker_reconciled_"
                "terminal_execution"
            ),
            "source_quality_gate": (
                "unambiguous_record_id_and_stock_code_joined_forced_one_share_"
                "event_to_post_sell_outcome_and_single_group_first_explicit_blocker"
            ),
            "forbidden_uses": FORBIDDEN_USES,
        },
        "threshold_group_contract": {
            "version": THRESHOLD_GROUP_CONTRACT_VERSION,
            "configured_group_count": len(THRESHOLD_GROUPS),
            "configured_groups": sorted(THRESHOLD_GROUPS),
            "group_evaluations_are_fixed_taxonomy": True,
            "group_evaluations_are_mutually_exclusive": False,
            "group_evaluations_are_new_candidates": False,
            "candidate_requires_exclusive_first_explicit_blocker": True,
            "candidate_blocker_must_not_follow_forced_event": True,
            "candidate_requires_positive_ev_and_sample_floor": True,
        },
        "source_paths": source_paths,
        "source_processing": source_processing,
        "post_sell_identity_diagnostics": {
            **{
                key: value
                for key, value in post_sell_identity_diagnostics.items()
                if key != "ambiguous_record_ids"
            },
            "ambiguous_record_id_examples": (
                post_sell_identity_diagnostics.get("ambiguous_record_ids") or []
            )[:50],
            "ambiguous_forced_record_id_count": len(post_sell_ambiguous_record_ids),
            "ambiguous_forced_record_ids": sorted(post_sell_ambiguous_record_ids),
        },
        "source_coverage_manifest": coverage_manifest,
        "probe_split_attribution": probe_split_attribution,
        "summary": {
            "forced_record_count": len(rows),
            "post_sell_joined_count": len(joined),
            "profitable_joined_count": sum(
                1 for row in joined if row.get("profitable")
            ),
            "loss_or_flat_joined_count": sum(
                1
                for row in joined
                if row.get("profit_rate") is not None and row.get("profit_rate") <= 0
            ),
            "threshold_group_counts": [
                {"threshold_group": key, "count": value}
                for key, value in threshold_group_counts.most_common()
            ],
            "configured_threshold_group_count": len(THRESHOLD_GROUPS),
            "observed_threshold_group_evaluation_count": len(group_evaluations),
            "primary_blocker_evaluation_count": len(primary_blocker_evaluations),
            "primary_attributed_opportunity_count": len(opportunities),
            "ambiguous_primary_blocker_record_count": sum(
                1
                for row in rows
                if row.get("primary_blocker_attribution_status")
                == "ambiguous_multi_group_first_blocker"
            ),
            "missing_primary_blocker_record_count": sum(
                1
                for row in rows
                if row.get("primary_blocker_attribution_status")
                == "missing_explicit_blocker"
            ),
            "post_force_or_unordered_blocker_record_count": sum(
                1
                for row in rows
                if row.get("primary_blocker_attribution_status")
                == "post_force_or_unordered_blocker_only"
            ),
            "source_identity_conflict_record_count": len(
                source_identity_conflict_record_ids
            ),
            "threshold_opportunity_count": len(opportunities),
            "code_improvement_order_count": len(orders),
            "actionable_candidate_count": len(orders),
            "actionable_candidate_scope": (
                "source_only_existing_family_review_not_implement_now"
            ),
            "source_only_existing_family_evidence_count": len(orders),
            "automatic_implementation_candidate_count": 0,
            "source_coverage_status": coverage_manifest.get("status"),
            "source_coverage_gap_count": coverage_manifest.get("gap_count"),
        },
        "profit_summary": _profit_summary(joined),
        "threshold_group_evaluations": group_evaluations,
        "primary_blocker_evaluations": primary_blocker_evaluations,
        "threshold_opportunities": opportunities,
        "joined_examples": joined[:30],
        "source_identity_conflict_examples": [
            row for row in rows if row.get("source_identity_status") != "valid"
        ][:30],
        "code_improvement_orders": orders,
    }
    previous_report_path = None
    if (
        previous_report is None
        and using_default_pipeline_paths
        and using_default_post_sell_paths
    ):
        previous_report, previous_report_path = _load_previous_report(target_date)
    _annotate_candidate_change(
        report,
        previous_report=previous_report,
        previous_report_path=previous_report_path,
        ai_provider=ai_provider,
    )
    return _apply_ai_review(
        report, provider=ai_provider, previous_report=previous_report
    )


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
    probe_split = (
        report.get("probe_split_attribution")
        if isinstance(report.get("probe_split_attribution"), dict)
        else {}
    )
    source_processing = (
        report.get("source_processing")
        if isinstance(report.get("source_processing"), dict)
        else {}
    )
    candidate_change = (
        report.get("candidate_change")
        if isinstance(report.get("candidate_change"), dict)
        else {}
    )
    lines = [
        f"# {report.get('target_date')} One Share Threshold Opportunity",
        "",
        f"- generated_at: {report.get('generated_at')}",
        f"- window: {((report.get('window') or {}).get('since_date'))} -> {((report.get('window') or {}).get('until_date'))}",
        "- decision_authority: source_only_threshold_opportunity_audit",
        "- runtime_effect: false",
        "- allowed_runtime_apply: false",
        "- forbidden_uses: " + ", ".join(FORBIDDEN_USES),
        f"- ai_review_status: {(summary.get('ai_review_status') or '-')}",
        f"- source_coverage_status: {summary.get('source_coverage_status')}",
        f"- source_coverage_gap_count: {summary.get('source_coverage_gap_count')}",
        "",
        "## Summary",
        "",
        f"- forced_record_count: {summary.get('forced_record_count')}",
        f"- post_sell_joined_count: {summary.get('post_sell_joined_count')}",
        f"- profitable_joined_count: {summary.get('profitable_joined_count')}",
        f"- loss_or_flat_joined_count: {summary.get('loss_or_flat_joined_count')}",
        f"- threshold_opportunity_count: {summary.get('threshold_opportunity_count')}",
        f"- configured_threshold_group_count: {summary.get('configured_threshold_group_count')}",
        f"- observed_threshold_group_evaluation_count: {summary.get('observed_threshold_group_evaluation_count')}",
        f"- primary_blocker_evaluation_count: {summary.get('primary_blocker_evaluation_count')}",
        f"- primary_attributed_opportunity_count: {summary.get('primary_attributed_opportunity_count')}",
        f"- actionable_candidate_count: {summary.get('actionable_candidate_count')}",
        f"- actionable_candidate_scope: {summary.get('actionable_candidate_scope')}",
        f"- source_only_existing_family_evidence_count: {summary.get('source_only_existing_family_evidence_count')}",
        f"- automatic_implementation_candidate_count: {summary.get('automatic_implementation_candidate_count')}",
        f"- code_improvement_order_count: {summary.get('code_improvement_order_count')}",
        f"- candidate_change_status: {candidate_change.get('status')}",
        f"- source_processing_mode: {source_processing.get('mode')}",
        f"- source_file_count: {source_processing.get('source_file_count')}",
        f"- cache_hit_count: {source_processing.get('cache_hit_count')}",
        f"- cache_miss_count: {source_processing.get('cache_miss_count')}",
        f"- source_bytes_scanned: {source_processing.get('source_bytes_scanned')}",
        f"- source_bytes_reused: {source_processing.get('source_bytes_reused')}",
        f"- source_io_bytes_estimated: {source_processing.get('source_io_bytes_estimated')}",
        f"- cache_miss_source_pass_count: {source_processing.get('cache_miss_source_pass_count')}",
        f"- source_reuse_pct: {source_processing.get('source_reuse_pct')}",
        f"- elapsed_seconds: {source_processing.get('elapsed_seconds')}",
        f"- probe_split_attribution_status: {probe_split.get('status')}",
        f"- probe_intent_record_count: {probe_split.get('intent_record_count')}",
        f"- actual_submit_observed_count: {probe_split.get('actual_submit_observed_count')}",
        f"- submitted_split_provenance_gap_count: {probe_split.get('submitted_split_provenance_gap_count')}",
        f"- probe_to_residual_status: {probe_split.get('probe_to_residual_status')}",
        f"- probe_to_residual_resolution_count: {probe_split.get('probe_to_residual_resolution_count')}",
        f"- probe_to_residual_resolution_coverage_pct: {probe_split.get('probe_to_residual_resolution_coverage_pct')}",
        f"- residual_submitted_record_count: {probe_split.get('residual_submitted_record_count')}",
        f"- residual_blocked_record_count: {probe_split.get('residual_blocked_record_count')}",
        f"- residual_not_submitted_record_count: {probe_split.get('residual_not_submitted_record_count')}",
        f"- residual_not_submitted_source_counts: {json.dumps(probe_split.get('residual_not_submitted_source_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_abort_reason_counts: {json.dumps(probe_split.get('residual_terminal_abort_reason_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_abort_detail_reason_counts: {json.dumps(probe_split.get('residual_terminal_abort_detail_reason_counts') or {}, ensure_ascii=False, sort_keys=True)}",
        f"- residual_terminal_failure_signature_coverage_count: {probe_split.get('residual_terminal_failure_signature_coverage_count')}",
        f"- probe_to_residual_unresolved_record_count: {probe_split.get('probe_to_residual_unresolved_record_count')}",
        f"- target_date_probe_to_residual: {json.dumps(probe_split.get('target_date_probe_to_residual') or {}, ensure_ascii=False, sort_keys=True)}",
        "",
        "## Fixed Taxonomy Group Evaluations",
        "",
    ]
    for item in report.get("threshold_group_evaluations") or []:
        lines.extend(
            [
                f"### {item.get('threshold_group')}",
                "",
                f"- evaluation_id: {item.get('evaluation_id')}",
                "- classification_role: overlapping_fixed_taxonomy_diagnostic",
                "- is_actionable_candidate: false",
                f"- sample: {item.get('sample')}",
                f"- valid_profit_sample: {item.get('valid_profit_sample')}",
                f"- equal_weight_avg_profit_pct: {item.get('equal_weight_avg_profit_pct')}",
                "",
            ]
        )
    lines.extend(["## Primary-blocker Evaluations", ""])
    for item in report.get("primary_blocker_evaluations") or []:
        lines.extend(
            [
                f"### {item.get('threshold_group')}",
                "",
                f"- candidate_id: {item.get('candidate_id')}",
                f"- mapped_family: {item.get('mapped_family')}",
                f"- classification_role: {item.get('classification_role')}",
                f"- candidate_status: {item.get('candidate_status')}",
                f"- is_actionable_candidate: {str(item.get('is_actionable_candidate')).lower()}",
                f"- sample: {item.get('sample')}",
                f"- valid_profit_sample: {item.get('valid_profit_sample')}",
                f"- equal_weight_avg_profit_pct: {item.get('equal_weight_avg_profit_pct')}",
                f"- profitable_count: {item.get('profitable_count')}",
                f"- loss_or_flat_count: {item.get('loss_or_flat_count')}",
                "",
            ]
        )
    lines.extend(["## Threshold Opportunities", ""])
    for item in report.get("threshold_opportunities") or []:
        lines.extend(
            [
                f"### {item.get('threshold_group')}",
                "",
                f"- candidate_id: {item.get('candidate_id')}",
                f"- mapped_family: {item.get('mapped_family')}",
                f"- classification_role: {item.get('classification_role')}",
                f"- sample: {item.get('sample')}",
                f"- valid_profit_sample: {item.get('valid_profit_sample')}",
                f"- equal_weight_avg_profit_pct: {item.get('equal_weight_avg_profit_pct')}",
                "",
            ]
        )
    lines.append("## Workorders")
    lines.append("")
    for order in report.get("code_improvement_orders") or []:
        lines.extend(
            [
                f"### {order.get('order_id')}",
                "",
                f"- mapped_family: {order.get('mapped_family')}",
                f"- runtime_effect: {str(order.get('runtime_effect')).lower()}",
                f"- allowed_runtime_apply: {str(order.get('allowed_runtime_apply')).lower()}",
                f"- ai_recommended_disposition: {order.get('ai_recommended_disposition') or '-'}",
                "- evidence:",
            ]
        )
        for item in order.get("evidence") or []:
            lines.append(f"  - {item}")
        lines.append("")
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build one-share threshold opportunity audit."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--since-date")
    parser.add_argument("--pipeline-path", action="append", type=Path)
    parser.add_argument("--post-sell-path", action="append", type=Path)
    parser.add_argument("--partition-cache-dir", type=Path)
    parser.add_argument("--no-partition-cache", action="store_true")
    parser.add_argument(
        "--ai-provider",
        default=os.getenv(
            "KORSTOCKSCAN_ONE_SHARE_THRESHOLD_OPPORTUNITY_AI_PROVIDER", "none"
        ),
    )
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--generated-at")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(
        args.target_date,
        since_date=args.since_date,
        pipeline_paths=args.pipeline_path,
        post_sell_paths=args.post_sell_path,
        generated_at=args.generated_at,
        ai_provider=args.ai_provider,
        partition_cache_dir=args.partition_cache_dir,
        use_partition_cache=(
            False
            if args.no_partition_cache
            else (True if args.partition_cache_dir is not None else None)
        ),
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
