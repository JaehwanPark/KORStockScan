"""Coverage-aware historical replay for the source-only micro-reversion V0."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, TextIO

from src.utils.constants import DATA_DIR

from .contracts import (
    CLEAN_BASELINE_DATE,
    OutcomeLabel,
    PriceObservation,
    ShockEvent,
    coverage_tier_for,
    normalize_symbol,
    normalize_venue,
)
from .detector import DetectorConfig, ShockDetector
from .outcome_labeler import OutcomeLabeler, OutcomeLabelerConfig
from .symbol_master import SymbolLookupStatus, VerifiedSymbolMaster
from .tax import InstrumentMetadata, metadata_from_mapping

KST = timezone(timedelta(hours=9))
DEFAULT_REPORT_ROOT = DATA_DIR / "report" / "scalp_micro_reversion_v0"
DEFAULT_PIPELINE_ROOT = DATA_DIR / "pipeline_events"


@dataclass(frozen=True, slots=True)
class ReplayConfig:
    session_start: time = time(9, 0)
    session_end: time = time(15, 30)
    dedupe_interval_ms: int = 1_000
    current_price_fields: tuple[str, ...] = (
        "current_price_observed",
        "current_price",
    )
    conservative_total_cost_bps: float = 23.0
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    max_path_gap_ms: int = 10_000
    instrument_metadata_by_symbol: Mapping[str, Mapping[str, object]] = field(
        default_factory=dict
    )
    verified_symbol_master: VerifiedSymbolMaster | None = None

    def __post_init__(self) -> None:
        if self.session_start >= self.session_end:
            raise ValueError("session_start must be before session_end")
        if self.dedupe_interval_ms <= 0:
            raise ValueError("dedupe_interval_ms must be positive")
        if not self.current_price_fields:
            raise ValueError("current_price_fields must not be empty")
        if self.max_path_gap_ms <= 0:
            raise ValueError("max_path_gap_ms must be positive")
        normalized_metadata: dict[str, Mapping[str, object]] = {}
        for raw_symbol, metadata in self.instrument_metadata_by_symbol.items():
            symbol = normalize_symbol(raw_symbol)
            if not symbol or not isinstance(metadata, Mapping):
                raise ValueError("instrument metadata entries must be objects")
            normalized_metadata[symbol] = metadata
        object.__setattr__(self, "instrument_metadata_by_symbol", normalized_metadata)


@dataclass(frozen=True, slots=True)
class ReplayInputStats:
    input_paths: tuple[str, ...]
    raw_row_count: int
    invalid_json_count: int
    invalid_timestamp_count: int
    prebaseline_row_count: int
    outside_session_row_count: int
    missing_symbol_count: int
    missing_price_count: int
    invalid_price_count: int
    accepted_row_count: int
    deduplicated_observation_count: int
    coverage_tier_counts: dict[str, int]
    dedupe_interval_ms: int
    conservative_total_cost_bps: float
    max_path_gap_ms: int
    detector_config: dict[str, Any]
    instrument_metadata_override_symbol_count: int
    verified_symbol_master_symbol_count: int
    verified_symbol_master_lookup_counts: dict[str, int]
    raw_bbo_candidate_rows: int
    raw_micro_capture_rows: int
    raw_micro_context_candidate_rows: int

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReplayResult:
    input_stats: ReplayInputStats
    observations: tuple[PriceObservation, ...]
    events: tuple[ShockEvent, ...]
    labels: tuple[OutcomeLabel, ...]

    def as_dict(self, *, include_observations: bool = False) -> dict[str, Any]:
        payload = {
            "input_stats": self.input_stats.as_dict(),
            "events": [event.as_dict() for event in self.events],
            "labels": [label.as_dict() for label in self.labels],
        }
        if include_observations:
            payload["observations"] = [
                observation.as_dict() for observation in self.observations
            ]
        return payload


def replay_paths(
    paths: Iterable[Path],
    *,
    config: ReplayConfig | None = None,
) -> ReplayResult:
    replay_config = config or ReplayConfig()
    normalized_paths = tuple(sorted(Path(path) for path in paths))
    if not normalized_paths:
        raise ValueError("at least one replay input path is required")

    observations_by_bucket: dict[tuple[str, str, str, str, int], PriceObservation] = {}
    counters: Counter[str] = Counter()

    for path in normalized_paths:
        with _open_text(path) as handle:
            for line in handle:
                counters["raw_row_count"] += 1
                try:
                    row = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    counters["invalid_json_count"] += 1
                    continue
                if not isinstance(row, dict):
                    counters["invalid_json_count"] += 1
                    continue
                parsed = _parse_observation(
                    row,
                    config=replay_config,
                    counters=counters,
                )
                if parsed is None:
                    continue
                counters["accepted_row_count"] += 1
                if (
                    parsed.best_bid is not None
                    and parsed.best_ask is not None
                    and parsed.best_ask >= parsed.best_bid
                ):
                    counters["raw_bbo_candidate_rows"] += 1
                if any(
                    value is not None
                    for value in (
                        parsed.aggressive_sell_ratio,
                        parsed.ofi,
                        parsed.qi,
                    )
                ):
                    counters["raw_micro_capture_rows"] += 1
                if parsed.coverage_tier.value == "micro_context":
                    counters["raw_micro_context_candidate_rows"] += 1
                bucket_ms = (
                    parsed.observed_at_ms // replay_config.dedupe_interval_ms
                ) * replay_config.dedupe_interval_ms
                bucket_key = (*parsed.series_key, bucket_ms)
                existing = observations_by_bucket.get(bucket_key)
                if existing is None or _observation_rank(parsed) > _observation_rank(
                    existing
                ):
                    observations_by_bucket[bucket_key] = parsed

    observations = tuple(
        sorted(
            observations_by_bucket.values(),
            key=lambda item: (*item.series_key, item.observed_at_ms),
        )
    )
    coverage_counts = Counter(
        observation.coverage_tier.value for observation in observations
    )
    stats = ReplayInputStats(
        input_paths=tuple(str(path) for path in normalized_paths),
        raw_row_count=counters["raw_row_count"],
        invalid_json_count=counters["invalid_json_count"],
        invalid_timestamp_count=counters["invalid_timestamp_count"],
        prebaseline_row_count=counters["prebaseline_row_count"],
        outside_session_row_count=counters["outside_session_row_count"],
        missing_symbol_count=counters["missing_symbol_count"],
        missing_price_count=counters["missing_price_count"],
        invalid_price_count=counters["invalid_price_count"],
        accepted_row_count=counters["accepted_row_count"],
        deduplicated_observation_count=len(observations),
        coverage_tier_counts=dict(sorted(coverage_counts.items())),
        dedupe_interval_ms=replay_config.dedupe_interval_ms,
        conservative_total_cost_bps=replay_config.conservative_total_cost_bps,
        max_path_gap_ms=replay_config.max_path_gap_ms,
        detector_config=asdict(replay_config.detector),
        instrument_metadata_override_symbol_count=len(
            replay_config.instrument_metadata_by_symbol
        ),
        verified_symbol_master_symbol_count=(
            0
            if replay_config.verified_symbol_master is None
            else replay_config.verified_symbol_master.symbol_count
        ),
        verified_symbol_master_lookup_counts={
            status.value: counters[f"symbol_master_{status.value}"]
            for status in SymbolLookupStatus
        },
        raw_bbo_candidate_rows=counters["raw_bbo_candidate_rows"],
        raw_micro_capture_rows=counters["raw_micro_capture_rows"],
        raw_micro_context_candidate_rows=counters["raw_micro_context_candidate_rows"],
    )

    grouped: dict[tuple[str, str, str, str], list[PriceObservation]] = defaultdict(list)
    for observation in observations:
        grouped[observation.series_key].append(observation)

    events = []
    for series_key in sorted(grouped):
        detector = ShockDetector(replay_config.detector)
        events.extend(detector.process_many(grouped[series_key]))
    events_tuple = tuple(
        sorted(events, key=lambda item: (item.detected_at_ms, item.event_id))
    )

    labeler = OutcomeLabeler(
        OutcomeLabelerConfig(
            conservative_total_cost_bps=replay_config.conservative_total_cost_bps,
            max_internal_gap_ms=replay_config.max_path_gap_ms,
        )
    )
    labels = tuple(
        labeler.label(event, grouped[event.series_key]) for event in events_tuple
    )
    return ReplayResult(
        input_stats=stats,
        observations=observations,
        events=events_tuple,
        labels=labels,
    )


def _parse_observation(
    row: dict[str, Any],
    *,
    config: ReplayConfig,
    counters: Counter[str],
) -> PriceObservation | None:
    symbol = normalize_symbol(row.get("stock_code") or row.get("symbol"))
    if not symbol:
        counters["missing_symbol_count"] += 1
        return None
    observed_at = _parse_datetime(
        row.get("emitted_at") or row.get("event_time") or row.get("timestamp")
    )
    if observed_at is None:
        counters["invalid_timestamp_count"] += 1
        return None
    local_datetime = observed_at.astimezone(KST)
    if local_datetime.date() < CLEAN_BASELINE_DATE:
        counters["prebaseline_row_count"] += 1
        return None
    local_time = local_datetime.time().replace(tzinfo=None)
    if not config.session_start <= local_time <= config.session_end:
        counters["outside_session_row_count"] += 1
        return None

    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    metadata = _instrument_metadata(
        row,
        fields=fields,
        symbol=symbol,
        trade_date=local_datetime.date(),
        counters=counters,
        verified_symbol_master=config.verified_symbol_master,
        explicit_by_symbol=config.instrument_metadata_by_symbol,
    )
    price_source_field, raw_price = _first_present_item(
        fields, config.current_price_fields
    )
    if raw_price is None:
        counters["missing_price_count"] += 1
        return None
    price = _positive_float(raw_price)
    if price is None:
        counters["invalid_price_count"] += 1
        return None

    venue = _first_present(
        fields,
        ("effective_venue", "execution_venue", "venue", "market"),
    )
    normalized_venue = normalize_venue(venue)
    session_bucket = _session_bucket(normalized_venue, local_time)
    best_bid = _positive_float(
        _first_present(fields, ("best_bid", "bid_price", "best_bid_price"))
    )
    best_ask = _positive_float(
        _first_present(fields, ("best_ask", "ask_price", "best_ask_price"))
    )
    quote_age_ms = _nonnegative_float(
        _first_present(
            fields,
            ("quote_age_ms", "best_quote_age_ms", "orderbook_age_ms"),
        )
    )
    micro_vwap = _positive_float(
        _first_present(fields, ("micro_vwap", "orderbook_micro_vwap"))
    )
    aggressive_sell_ratio = _bounded_float(
        _first_present(
            fields,
            ("aggressive_sell_ratio", "sell_ratio", "tick_sell_ratio"),
        ),
        lower=0.0,
        upper=1.0,
    )
    ofi = _finite_float(
        _first_present(fields, ("ofi", "ofi_z", "order_flow_imbalance"))
    )
    qi = _finite_float(_first_present(fields, ("qi", "qi_ewma", "queue_imbalance")))
    source_quality_status = coverage_tier_for(
        best_bid=best_bid,
        best_ask=best_ask,
        quote_age_ms=quote_age_ms,
        aggressive_sell_ratio=aggressive_sell_ratio,
        ofi=ofi,
        qi=qi,
    ).value

    observed_at_ms = int(observed_at.timestamp() * 1_000)
    source_event_id = str(
        row.get("event_id") or row.get("record_id") or fields.get("record_id") or ""
    )
    return PriceObservation(
        symbol=symbol,
        observed_at_ms=observed_at_ms,
        price=price,
        trade_date=local_datetime.date().isoformat(),
        venue=normalized_venue,
        session_bucket=session_bucket,
        source_event_id=source_event_id,
        price_source_field=price_source_field,
        best_bid=best_bid,
        best_ask=best_ask,
        quote_age_ms=quote_age_ms,
        micro_vwap=micro_vwap,
        aggressive_sell_ratio=aggressive_sell_ratio,
        ofi=ofi,
        qi=qi,
        source_quality_status=source_quality_status,
        listing_market=metadata.listing_market,
        instrument_type=metadata.instrument_type,
        instrument_metadata_source=metadata.source,
        instrument_metadata_verified=metadata.verified,
    )


def _instrument_metadata(
    row: Mapping[str, Any],
    *,
    fields: Mapping[str, Any],
    symbol: str,
    trade_date: date,
    counters: Counter[str],
    verified_symbol_master: VerifiedSymbolMaster | None,
    explicit_by_symbol: Mapping[str, Mapping[str, object]],
) -> InstrumentMetadata:
    if verified_symbol_master is not None:
        lookup = verified_symbol_master.lookup(symbol, as_of=trade_date)
        counters[f"symbol_master_{lookup.status.value}"] += 1
        if lookup.status is SymbolLookupStatus.VERIFIED and lookup.record is not None:
            return InstrumentMetadata(
                listing_market=lookup.record.listing_market,
                instrument_type=lookup.record.instrument_type,
                source=(
                    f"verified_symbol_master:{lookup.record.metadata_source}:"
                    f"{lookup.record.source_reference}"
                ),
                verified=True,
            )
    explicit = explicit_by_symbol.get(symbol)
    if explicit is not None:
        return metadata_from_mapping(explicit)
    listing_market = _first_present(
        dict(fields),
        ("listing_market", "market_type", "market_name", "universe"),
    ) or row.get("listing_market")
    instrument_type = _first_present(
        dict(fields),
        ("instrument_type", "security_type", "stock_type", "asset_type"),
    ) or row.get("instrument_type")
    return metadata_from_mapping(
        {
            "listing_market": listing_market,
            "instrument_type": instrument_type,
            "source": (
                "pipeline_event_fields"
                if listing_market is not None or instrument_type is not None
                else "missing"
            ),
        }
    )


def _parse_datetime(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(UTC)


def _observation_rank(observation: PriceObservation) -> tuple[int, str, float]:
    return (
        observation.observed_at_ms,
        observation.source_event_id,
        observation.price,
    )


def _session_bucket(venue: str, local_time: time) -> str:
    normalized = venue if venue in {"KRX", "NXT", "SOR"} else "UNKNOWN"
    if local_time < time(9, 0):
        return f"{normalized}_PREMARKET"
    if local_time <= time(15, 30):
        return f"{normalized}_REGULAR"
    return f"{normalized}_AFTERMARKET"


def _first_present(fields: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = fields.get(key)
        if value not in (None, "", "-"):
            return value
    return None


def _first_present_item(fields: dict[str, Any], keys: Iterable[str]) -> tuple[str, Any]:
    for key in keys:
        value = fields.get(key)
        if value not in (None, "", "-"):
            return key, value
    return "", None


def _finite_float(value: object) -> float | None:
    if value in (None, "", "-"):
        return None
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _positive_float(value: object) -> float | None:
    number = _finite_float(value)
    if number is None:
        return None
    number = abs(number)
    return number if number > 0 else None


def _nonnegative_float(value: object) -> float | None:
    number = _finite_float(value)
    return number if number is not None and number >= 0 else None


def _bounded_float(
    value: object,
    *,
    lower: float,
    upper: float,
) -> float | None:
    number = _finite_float(value)
    return number if number is not None and lower <= number <= upper else None


def _open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def resolve_target_date_path(target_date: date) -> Path:
    if target_date < CLEAN_BASELINE_DATE:
        raise ValueError("target date is before the clean tuning baseline")
    plain = DEFAULT_PIPELINE_ROOT / f"pipeline_events_{target_date.isoformat()}.jsonl"
    compressed = plain.with_suffix(f"{plain.suffix}.gz")
    if compressed.exists():
        return compressed
    return plain


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", type=Path, default=[])
    parser.add_argument("--target-date", type=date.fromisoformat)
    parser.add_argument("--cost-bps", type=float, default=23.0)
    parser.add_argument("--instrument-metadata", type=Path)
    parser.add_argument("--symbol-master", type=Path)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--test-result", default="not_run_for_this_manifest")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_REPORT_ROOT)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    paths = list(args.input)
    if not paths:
        if args.target_date is None:
            raise SystemExit("--input or --target-date is required")
        paths.append(resolve_target_date_path(args.target_date))
    instrument_metadata = _load_instrument_metadata(args.instrument_metadata)
    symbol_master = (
        None
        if args.symbol_master is None
        else VerifiedSymbolMaster.from_json_path(args.symbol_master)
    )
    result = replay_paths(
        paths,
        config=ReplayConfig(
            conservative_total_cost_bps=args.cost_bps,
            instrument_metadata_by_symbol=instrument_metadata,
            verified_symbol_master=symbol_master,
        ),
    )
    from .report import build_report, write_report

    report = build_report(result)
    written = None
    if args.write:
        written = write_report(
            report,
            output_root=args.output_root,
            test_result=args.test_result,
        )
    print(
        json.dumps(
            {
                "status": report["decision"]["status"],
                "event_count": report["summary"]["event_count"],
                "fully_mature_event_count": report["summary"][
                    "fully_mature_event_count"
                ],
                "runtime_effect": False,
                "written": (
                    None if written is None else [str(path) for path in written]
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _load_instrument_metadata(
    path: Path | None,
) -> dict[str, Mapping[str, object]]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("instrument metadata must be a JSON object keyed by symbol")
    normalized: dict[str, Mapping[str, object]] = {}
    for raw_symbol, raw_metadata in payload.items():
        symbol = normalize_symbol(raw_symbol)
        if not symbol or not isinstance(raw_metadata, dict):
            raise ValueError("instrument metadata entries must be objects")
        normalized[symbol] = raw_metadata
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
