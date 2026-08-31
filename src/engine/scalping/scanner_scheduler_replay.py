"""Read-only replay of scanner attach/precheck latency by canonical venue.

Historical rows are diagnostic input only.  The replay never infers venue,
promotion identity, attach action time, or a missing precheck.  It therefore
cannot authorize runtime activation; it provides the clean baseline against
which ``scanner_deadline_scheduler_v1`` post-apply attribution is compared.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
VALID_VENUES = frozenset({"KRX", "PREMARKET_KRX_LIKE", "NXT"})
VALID_ATTACH_OUTCOMES = frozenset({"attached", "refreshed", "db_poll_attached"})
ATTACH_STAGE = "scalping_scanner_runtime_target_attach"
PRECHECK_STAGE = "scalping_scanner_fast_precheck"
SCHEDULER_DISPATCH_STAGE = "scalping_scanner_scheduler_work_dispatched"
HEAVY_EVAL_STAGE = "scalping_scanner_heavy_eval_lag"
DEFAULT_BASELINE = datetime.fromisoformat("2026-06-05T00:00:00+09:00")


@dataclass(frozen=True, slots=True)
class ScannerReplaySample:
    code: str
    promotion_id: str
    venue: str
    promotion_epoch: float
    attach_epoch: float
    first_precheck_epoch: float
    attach_epoch_source: str = "diagnostic_event_proxy"

    @property
    def promotion_to_attach_sec(self) -> float:
        return max(0.0, self.attach_epoch - self.promotion_epoch)

    @property
    def attach_to_first_precheck_sec(self) -> float:
        return max(0.0, self.first_precheck_epoch - self.attach_epoch)


@dataclass(frozen=True, slots=True)
class ScannerSourceReadySample:
    code: str
    promotion_id: str
    venue: str
    attach_epoch: float
    first_entry_realtime_epoch: float
    first_heavy_eval_epoch: float
    first_entry_realtime_type: str

    @property
    def attach_to_first_entry_realtime_sec(self) -> float:
        return max(0.0, self.first_entry_realtime_epoch - self.attach_epoch)

    @property
    def first_entry_realtime_to_heavy_eval_sec(self) -> float:
        return max(0.0, self.first_heavy_eval_epoch - self.first_entry_realtime_epoch)


def _event_epoch(event: dict[str, Any]) -> float | None:
    raw = str(event.get("emitted_at") or "").strip()
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=KST)
    return value.timestamp()


def _float_or_none(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _event_order_epoch(event: dict[str, Any], emitted_epoch: float) -> float:
    fields = event.get("fields")
    if (
        str(event.get("stage") or "") == ATTACH_STAGE
        and isinstance(fields, dict)
        and fields.get("scanner_attach_provenance_version")
        == "scanner_runtime_handoff_v1"
    ):
        return _float_or_none(fields.get("scanner_runtime_handoff_epoch")) or float(
            emitted_epoch
        )
    return float(emitted_epoch)


def _canonical_attach(event: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    fields = event.get("fields")
    if not isinstance(fields, dict):
        return None, "attach_fields_missing"
    if fields.get("runtime_target_attach_outcome") not in VALID_ATTACH_OUTCOMES:
        return None, "attach_not_applied"
    venue = str(fields.get("effective_venue") or "").strip().upper()
    resolution = str(fields.get("venue_resolution") or "").strip().lower()
    if venue not in VALID_VENUES:
        return None, "attach_explicit_venue_missing"
    if any(token in resolution for token in ("conflict", "missing", "unknown")):
        return None, "attach_venue_resolution_invalid"
    promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
    promotion_epoch = _float_or_none(fields.get("scanner_promotion_emitted_epoch"))
    event_proxy_epoch = _event_epoch(event)
    code = str(event.get("stock_code") or "").strip()[:6]
    handoff_epoch = _float_or_none(fields.get("scanner_runtime_handoff_epoch"))
    handoff_promotion_id = str(
        fields.get("scanner_runtime_handoff_promotion_id") or ""
    ).strip()
    handoff_instance_id = str(fields.get("scanner_runtime_instance_id") or "").strip()
    handoff_version = str(fields.get("scanner_attach_provenance_version") or "").strip()
    explicit_handoff_observed = bool(
        handoff_epoch
        or handoff_promotion_id
        or handoff_version
        or (
            handoff_instance_id and not handoff_instance_id.startswith("not_applicable")
        )
    )
    if explicit_handoff_observed:
        if (
            handoff_epoch is None
            or handoff_promotion_id != promotion_id
            or not handoff_instance_id
            or handoff_instance_id.startswith("not_applicable")
            or handoff_version != "scanner_runtime_handoff_v1"
        ):
            return None, "attach_handoff_provenance_invalid"
        attach_epoch = handoff_epoch
        attach_epoch_source = "exact_runtime_handoff"
    else:
        attach_epoch = event_proxy_epoch
        attach_epoch_source = "diagnostic_event_proxy"
    if (
        not code
        or not promotion_id
        or promotion_id.startswith("not_")
        or promotion_epoch is None
        or attach_epoch is None
        or attach_epoch < promotion_epoch
    ):
        return None, "attach_generation_action_unrestorable"
    return {
        "code": code,
        "promotion_id": promotion_id,
        "venue": venue,
        "promotion_epoch": promotion_epoch,
        "attach_epoch": attach_epoch,
        "attach_epoch_source": attach_epoch_source,
    }, "valid_attach"


def _canonical_initial_precheck_dispatch(
    event: dict[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    fields = event.get("fields")
    if not isinstance(fields, dict):
        return None, "scheduler_dispatch_fields_missing"
    if (
        str(fields.get("scheduler_version") or "").strip()
        != "scanner_deadline_scheduler_v1"
        or str(fields.get("scheduler_action") or "").strip() != "dispatch"
        or str(fields.get("scanner_scheduler_lane") or "").strip() != "fast_precheck"
        or str(fields.get("scanner_scheduler_precheck_phase") or "").strip()
        != "initial"
    ):
        return None, "not_initial_deadline_precheck_dispatch"
    code = str(event.get("stock_code") or "").strip()[:6]
    promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
    venue = str(fields.get("effective_venue") or "").strip().upper()
    attach_epoch = _float_or_none(fields.get("scanner_attach_epoch"))
    dispatch_epoch = _float_or_none(fields.get("scanner_scheduler_dispatched_epoch"))
    if dispatch_epoch is None:
        dispatch_epoch = _float_or_none(fields.get("scanner_scheduler_action_epoch"))
    if venue not in VALID_VENUES:
        return None, "scheduler_dispatch_explicit_venue_missing"
    if (
        not code
        or not promotion_id
        or promotion_id.startswith("not_")
        or attach_epoch is None
        or dispatch_epoch is None
        or dispatch_epoch < attach_epoch
    ):
        return None, "scheduler_dispatch_action_unrestorable"
    return {
        "code": code,
        "promotion_id": promotion_id,
        "venue": venue,
        "attach_epoch": attach_epoch,
        "dispatch_epoch": dispatch_epoch,
    }, "valid_initial_precheck_dispatch"


def replay_scanner_events(
    events: Iterable[dict[str, Any]],
    *,
    baseline_epoch: float = DEFAULT_BASELINE.timestamp(),
) -> dict[str, Any]:
    pending: dict[tuple[str, str], dict[str, Any]] = {}
    canonical_attaches: dict[tuple[str, str], dict[str, Any]] = {}
    active_generation_by_code: dict[str, tuple[str, str]] = {}
    superseded_at: dict[tuple[str, str], float] = {}
    sampled_keys: set[tuple[str, str]] = set()
    samples: list[ScannerReplaySample] = []
    exclusions: dict[str, int] = {}

    ordered = [
        (epoch, event, _event_order_epoch(event, epoch))
        for event in events
        if isinstance(event, dict)
        for epoch in [_event_epoch(event)]
        if epoch is not None
        and _event_order_epoch(event, epoch) >= float(baseline_epoch)
    ]
    ordered.sort(key=lambda item: item[2])
    ordered = [(epoch, event) for epoch, event, _order_epoch in ordered]
    for event_epoch, event in ordered:
        stage = str(event.get("stage") or "")
        if stage == ATTACH_STAGE:
            attach, reason = _canonical_attach(event)
            if attach is None:
                exclusions[reason] = exclusions.get(reason, 0) + 1
                continue
            # A newer canonical attach supersedes every older generation for
            # the same symbol, even if no precheck was observed.
            code = attach["code"]
            key = (code, attach["promotion_id"])
            active_key = active_generation_by_code.get(code)
            if active_key is not None and active_key != key:
                superseded_at[active_key] = attach["attach_epoch"]
            active_generation_by_code[code] = key
            for key in [key for key in pending if key[0] == code]:
                pending.pop(key, None)
                exclusions["superseded_before_precheck"] = (
                    exclusions.get("superseded_before_precheck", 0) + 1
                )
            pending[(code, attach["promotion_id"])] = attach
            canonical_attaches.setdefault((code, attach["promotion_id"]), attach)
            continue
        if stage == SCHEDULER_DISPATCH_STAGE:
            dispatch, reason = _canonical_initial_precheck_dispatch(event)
            if dispatch is None:
                if reason != "not_initial_deadline_precheck_dispatch":
                    exclusions[reason] = exclusions.get(reason, 0) + 1
                continue
            key = (dispatch["code"], dispatch["promotion_id"])
            if key in sampled_keys:
                continue
            attach = pending.get(key)
            if attach is None:
                exclusions["scheduler_dispatch_without_canonical_attach"] = (
                    exclusions.get("scheduler_dispatch_without_canonical_attach", 0) + 1
                )
                continue
            if dispatch["venue"] != attach["venue"]:
                pending.pop(key, None)
                exclusions["scheduler_dispatch_venue_conflict"] = (
                    exclusions.get("scheduler_dispatch_venue_conflict", 0) + 1
                )
                continue
            if dispatch["attach_epoch"] < attach["promotion_epoch"]:
                pending.pop(key, None)
                exclusions["scheduler_dispatch_attach_before_promotion"] = (
                    exclusions.get("scheduler_dispatch_attach_before_promotion", 0) + 1
                )
                continue
            samples.append(
                ScannerReplaySample(
                    code=attach["code"],
                    promotion_id=attach["promotion_id"],
                    venue=attach["venue"],
                    promotion_epoch=attach["promotion_epoch"],
                    attach_epoch=dispatch["attach_epoch"],
                    first_precheck_epoch=dispatch["dispatch_epoch"],
                    attach_epoch_source=attach["attach_epoch_source"],
                )
            )
            sampled_keys.add(key)
            pending.pop(key, None)
            continue
        if stage != PRECHECK_STAGE:
            continue
        fields = event.get("fields")
        if not isinstance(fields, dict):
            exclusions["precheck_fields_missing"] = (
                exclusions.get("precheck_fields_missing", 0) + 1
            )
            continue
        code = str(event.get("stock_code") or "").strip()[:6]
        promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
        key = (code, promotion_id)
        if key in sampled_keys:
            continue
        attach = pending.get(key)
        if attach is None:
            exclusions["precheck_without_canonical_attach"] = (
                exclusions.get("precheck_without_canonical_attach", 0) + 1
            )
            continue
        precheck_venue = str(fields.get("effective_venue") or "").strip().upper()
        if precheck_venue and precheck_venue not in {
            attach["venue"],
            "UNKNOWN",
        }:
            pending.pop(key, None)
            exclusions["precheck_venue_conflict"] = (
                exclusions.get("precheck_venue_conflict", 0) + 1
            )
            continue
        if event_epoch < attach["attach_epoch"]:
            pending.pop(key, None)
            exclusions["precheck_before_attach"] = (
                exclusions.get("precheck_before_attach", 0) + 1
            )
            continue
        samples.append(
            ScannerReplaySample(
                **attach,
                first_precheck_epoch=event_epoch,
            )
        )
        sampled_keys.add(key)
        pending.pop(key, None)

    if pending:
        exclusions["attach_without_precheck"] = exclusions.get(
            "attach_without_precheck", 0
        ) + len(pending)
    source_ready_samples, source_ready_exclusions = _source_ready_handoffs(
        ordered,
        canonical_attaches=canonical_attaches,
        superseded_at=superseded_at,
    )
    return _summarize(
        samples,
        exclusions=exclusions,
        source_ready_samples=source_ready_samples,
        source_ready_exclusions=source_ready_exclusions,
    )


def _source_ready_handoffs(
    ordered_events: Iterable[tuple[float, dict[str, Any]]],
    *,
    canonical_attaches: dict[tuple[str, str], dict[str, Any]],
    superseded_at: dict[tuple[str, str], float],
) -> tuple[list[ScannerSourceReadySample], dict[str, int]]:
    ready_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    heavy_by_key: dict[tuple[str, str], list[float]] = {}
    exclusions: dict[str, int] = {}

    for event_epoch, event in ordered_events:
        stage = str(event.get("stage") or "")
        if stage not in {PRECHECK_STAGE, HEAVY_EVAL_STAGE}:
            continue
        fields = event.get("fields")
        if not isinstance(fields, dict):
            exclusions[f"{stage}_fields_missing"] = (
                exclusions.get(f"{stage}_fields_missing", 0) + 1
            )
            continue
        code = str(event.get("stock_code") or "").strip()[:6]
        promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
        key = (code, promotion_id)
        attach = canonical_attaches.get(key)
        if attach is None:
            exclusions[f"{stage}_without_canonical_attach"] = (
                exclusions.get(f"{stage}_without_canonical_attach", 0) + 1
            )
            continue
        generation_end_epoch = superseded_at.get(key)
        if generation_end_epoch is not None and event_epoch >= generation_end_epoch:
            exclusions[f"{stage}_superseded_generation"] = (
                exclusions.get(f"{stage}_superseded_generation", 0) + 1
            )
            continue
        venue = str(fields.get("effective_venue") or "").strip().upper()
        if venue and venue not in {attach["venue"], "UNKNOWN"}:
            exclusions[f"{stage}_venue_conflict"] = (
                exclusions.get(f"{stage}_venue_conflict", 0) + 1
            )
            continue

        if stage == HEAVY_EVAL_STAGE:
            heavy_epoch = _float_or_none(fields.get("heavy_eval_started_epoch"))
            if heavy_epoch is None:
                heavy_epoch = event_epoch
            if heavy_epoch >= attach["attach_epoch"]:
                heavy_by_key.setdefault(key, []).append(heavy_epoch)
            else:
                exclusions["heavy_eval_before_attach"] = (
                    exclusions.get("heavy_eval_before_attach", 0) + 1
                )
            continue

        if str(fields.get("scanner_entry_realtime_state") or "").strip() != "received":
            continue
        realtime_epoch = _float_or_none(
            fields.get("scanner_first_entry_realtime_epoch")
        )
        realtime_type = str(
            fields.get("scanner_first_entry_realtime_type") or ""
        ).strip()
        if realtime_epoch is None or not realtime_type:
            exclusions["source_ready_timestamp_or_type_missing"] = (
                exclusions.get("source_ready_timestamp_or_type_missing", 0) + 1
            )
            continue
        if realtime_epoch < attach["attach_epoch"]:
            exclusions["source_ready_before_attach"] = (
                exclusions.get("source_ready_before_attach", 0) + 1
            )
            continue
        if generation_end_epoch is not None and realtime_epoch >= generation_end_epoch:
            exclusions["source_ready_superseded_generation"] = (
                exclusions.get("source_ready_superseded_generation", 0) + 1
            )
            continue
        existing = ready_by_key.get(key)
        if existing is None or realtime_epoch < existing["realtime_epoch"]:
            ready_by_key[key] = {
                "attach": attach,
                "realtime_epoch": realtime_epoch,
                "realtime_type": realtime_type,
            }

    samples: list[ScannerSourceReadySample] = []
    for key, ready in ready_by_key.items():
        heavy_epochs = [
            value
            for value in heavy_by_key.get(key, [])
            if value >= ready["realtime_epoch"]
            and (key not in superseded_at or value < superseded_at[key])
        ]
        if not heavy_epochs:
            reason = (
                "source_ready_superseded_before_heavy_eval"
                if key in superseded_at
                else "source_ready_without_heavy_eval"
            )
            exclusions[reason] = exclusions.get(reason, 0) + 1
            continue
        attach = ready["attach"]
        samples.append(
            ScannerSourceReadySample(
                code=attach["code"],
                promotion_id=attach["promotion_id"],
                venue=attach["venue"],
                attach_epoch=attach["attach_epoch"],
                first_entry_realtime_epoch=ready["realtime_epoch"],
                first_heavy_eval_epoch=min(heavy_epochs),
                first_entry_realtime_type=ready["realtime_type"],
            )
        )
    return samples, exclusions


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(len(ordered) - 1, lower + 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _summarize(
    samples: Iterable[ScannerReplaySample],
    *,
    exclusions: dict[str, int],
    source_ready_samples: Iterable[ScannerSourceReadySample] = (),
    source_ready_exclusions: dict[str, int] | None = None,
) -> dict[str, Any]:
    sample_list = list(samples)
    source_ready_sample_list = list(source_ready_samples)
    by_venue: dict[str, dict[str, Any]] = {}
    for venue in sorted(VALID_VENUES):
        venue_samples = [sample for sample in sample_list if sample.venue == venue]
        attach_lags = [sample.attach_to_first_precheck_sec for sample in venue_samples]
        promotion_lags = [sample.promotion_to_attach_sec for sample in venue_samples]
        p95 = _percentile(attach_lags, 0.95)
        maximum = max(attach_lags) if attach_lags else None
        by_venue[venue] = {
            "valid_generation_count": len(venue_samples),
            "promotion_to_attach_p95_sec": (
                round(_percentile(promotion_lags, 0.95), 6) if promotion_lags else None
            ),
            "attach_to_first_precheck_p50_sec": (
                round(_percentile(attach_lags, 0.50), 6) if attach_lags else None
            ),
            "attach_to_first_precheck_p95_sec": (
                round(p95, 6) if p95 is not None else None
            ),
            "attach_to_first_precheck_max_sec": (
                round(maximum, 6) if maximum is not None else None
            ),
            "historical_phase1_target_met": bool(
                p95 is not None and maximum is not None and p95 <= 7 and maximum <= 10
            ),
        }
    source_ready_by_venue: dict[str, dict[str, Any]] = {}
    for venue in sorted(VALID_VENUES):
        venue_samples = [
            sample for sample in source_ready_sample_list if sample.venue == venue
        ]
        source_lags = [
            sample.attach_to_first_entry_realtime_sec for sample in venue_samples
        ]
        handoff_lags = [
            sample.first_entry_realtime_to_heavy_eval_sec for sample in venue_samples
        ]
        source_ready_by_venue[venue] = {
            "valid_generation_count": len(venue_samples),
            "first_entry_realtime_type_counts": dict(
                sorted(
                    {
                        source_type: sum(
                            sample.first_entry_realtime_type == source_type
                            for sample in venue_samples
                        )
                        for source_type in {
                            sample.first_entry_realtime_type for sample in venue_samples
                        }
                    }.items()
                )
            ),
            "attach_to_first_entry_realtime_p50_sec": (
                round(_percentile(source_lags, 0.50), 6) if source_lags else None
            ),
            "attach_to_first_entry_realtime_p95_sec": (
                round(_percentile(source_lags, 0.95), 6) if source_lags else None
            ),
            "attach_to_first_entry_realtime_max_sec": (
                round(max(source_lags), 6) if source_lags else None
            ),
            "first_entry_realtime_to_heavy_eval_p50_sec": (
                round(_percentile(handoff_lags, 0.50), 6) if handoff_lags else None
            ),
            "first_entry_realtime_to_heavy_eval_p95_sec": (
                round(_percentile(handoff_lags, 0.95), 6) if handoff_lags else None
            ),
            "first_entry_realtime_to_heavy_eval_max_sec": (
                round(max(handoff_lags), 6) if handoff_lags else None
            ),
        }
    return {
        "schema_version": 2,
        "replay_contract": "scanner_deadline_scheduler_historical_baseline_v2",
        "decision_authority": "diagnostic_replay_only_no_runtime_activation",
        "clean_baseline_ts_kst": DEFAULT_BASELINE.isoformat(),
        "valid_generation_count": len(sample_list),
        "attach_epoch_source_counts": dict(
            sorted(
                {
                    source: sum(
                        sample.attach_epoch_source == source for sample in sample_list
                    )
                    for source in {sample.attach_epoch_source for sample in sample_list}
                }.items()
            )
        ),
        "excluded_count": sum(exclusions.values()),
        "exclusions": dict(sorted(exclusions.items())),
        "venues": by_venue,
        "source_ready_handoff": {
            "metric_role": "source_quality_gate",
            "decision_authority": "diagnostic_replay_only_no_runtime_activation",
            "window_policy": "canonical_generation_attach_to_first_entry_realtime_to_heavy_eval",
            "sample_floor": "one_canonical_generation_with_source_ready_and_heavy_eval",
            "primary_decision_metric": "first_entry_realtime_to_heavy_eval_p95_sec",
            "external_wait_metric": "attach_to_first_entry_realtime_sec",
            "external_wait_owner": (
                "external_or_subscription_state_first_post_attach_entry_realtime"
            ),
            "external_wait_causal_attribution": (
                "not_assigned_without_server_subscription_ack"
            ),
            "external_wait_excluded_from_internal_root_cause": True,
            "internal_latency_anchor": "first_post_attach_entry_realtime",
            "source_quality_gate": (
                "canonical_attach_explicit_venue_absolute_first_entry_realtime_and_heavy_eval"
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "forbidden_uses": (
                "standalone_buy|threshold_mutation|provider_route_change|"
                "order_price_or_quantity_change|broker_guard_bypass|"
                "stale_quote_bypass|hard_safety_bypass|bot_restart"
            ),
            "valid_generation_count": len(source_ready_sample_list),
            "excluded_count": sum((source_ready_exclusions or {}).values()),
            "exclusions": dict(sorted((source_ready_exclusions or {}).items())),
            "venues": source_ready_by_venue,
            "samples": [
                {
                    **asdict(sample),
                    "attach_to_first_entry_realtime_sec": round(
                        sample.attach_to_first_entry_realtime_sec, 6
                    ),
                    "first_entry_realtime_to_heavy_eval_sec": round(
                        sample.first_entry_realtime_to_heavy_eval_sec, 6
                    ),
                }
                for sample in source_ready_sample_list
            ],
        },
        "samples": [asdict(sample) for sample in sample_list],
    }


def load_jsonl_events(paths: Iterable[Path]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
    return events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="pipeline JSONL paths; defaults to data/pipeline_events/*.jsonl",
    )
    parser.add_argument("--include-samples", action="store_true")
    args = parser.parse_args()
    paths = args.paths or sorted(Path("data/pipeline_events").glob("*.jsonl"))
    result = replay_scanner_events(load_jsonl_events(paths))
    if not args.include_samples:
        result.pop("samples", None)
        source_ready_handoff = result.get("source_ready_handoff")
        if isinstance(source_ready_handoff, dict):
            source_ready_handoff.pop("samples", None)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
