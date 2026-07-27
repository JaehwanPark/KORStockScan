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
DEFAULT_BASELINE = datetime.fromisoformat("2026-06-04T14:29:09+09:00")


@dataclass(frozen=True, slots=True)
class ScannerReplaySample:
    code: str
    promotion_id: str
    venue: str
    promotion_epoch: float
    attach_epoch: float
    first_precheck_epoch: float

    @property
    def promotion_to_attach_sec(self) -> float:
        return max(0.0, self.attach_epoch - self.promotion_epoch)

    @property
    def attach_to_first_precheck_sec(self) -> float:
        return max(0.0, self.first_precheck_epoch - self.attach_epoch)


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
    attach_epoch = _event_epoch(event)
    code = str(event.get("stock_code") or "").strip()[:6]
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
    sampled_keys: set[tuple[str, str]] = set()
    samples: list[ScannerReplaySample] = []
    exclusions: dict[str, int] = {}

    ordered = sorted(
        (
            (epoch, event)
            for event in events
            if isinstance(event, dict)
            for epoch in [_event_epoch(event)]
            if epoch is not None and epoch >= float(baseline_epoch)
        ),
        key=lambda item: item[0],
    )
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
            for key in [key for key in pending if key[0] == code]:
                pending.pop(key, None)
                exclusions["superseded_before_precheck"] = (
                    exclusions.get("superseded_before_precheck", 0) + 1
                )
            pending[(code, attach["promotion_id"])] = attach
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
    return _summarize(samples, exclusions=exclusions)


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
    samples: Iterable[ScannerReplaySample], *, exclusions: dict[str, int]
) -> dict[str, Any]:
    sample_list = list(samples)
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
    return {
        "schema_version": 1,
        "replay_contract": "scanner_deadline_scheduler_historical_baseline_v1",
        "decision_authority": "diagnostic_replay_only_no_runtime_activation",
        "clean_baseline_ts_kst": DEFAULT_BASELINE.isoformat(),
        "valid_generation_count": len(sample_list),
        "excluded_count": sum(exclusions.values()),
        "exclusions": dict(sorted(exclusions.items())),
        "venues": by_venue,
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
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
