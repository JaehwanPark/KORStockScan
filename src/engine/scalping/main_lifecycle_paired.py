"""Materialize compact, source-only main-bot lifecycle rows.

The default producer makes one streaming pass over the existing pipeline event
file and consumes only strict stages carrying an explicit lifecycle identity.
An explicit transition journal remains a supported audit/test source.  The
producer never reconstructs identity from symbol or time proximity and never
grants runtime, order, provider, threshold, or promotion authority.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, BinaryIO, Iterator, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.scalping.main_lifecycle_journal import (
    AUTHORITY_CONTRACT,
    BROKER_EXECUTION_PROVENANCE_SCHEMA,
    BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA,
    JOURNAL_SCHEMA,
    KIWOOM_OFFICIAL_REFERENCE_SHA,
    PIPELINE_IDENTITY_SCHEMA,
    PIPELINE_STAGE_MAP,
    SHA256_RE,
    VALID_STAGES,
    build_broker_execution_provenance,
    build_transition,
)
from src.utils.constants import DATA_DIR

REPORT_SCHEMA = "main_scalping_lifecycle_paired_daily_v1"
LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_lifecycle_window_exclusion_manifest_v1"
)
PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA = (
    "main_scalping_pipeline_owner_exclusion_manifest_v1"
)
REPORT_DIR = DATA_DIR / "report" / "main_scalping_lifecycle_paired"
PIPELINE_EVENT_DIR = DATA_DIR / "pipeline_events"

_TRACE_ID_LIMIT = 256
_GAP_EXAMPLE_LIMIT = 20
_EVENT_ID_LIMIT_PER_LIFECYCLE = 4_096
MAX_LIFECYCLE_ACCUMULATORS = 50_000
MAX_TRANSITION_EVENT_IDENTITIES = 500_000
PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS = 1_000
_QUANTITY_EPSILON = 1e-8
_BROKER_SUBMIT_CLOCK_SKEW_SEC = 2
KST = ZoneInfo("Asia/Seoul")
_REQUIRED_COMPLETE_STAGES = frozenset(
    {
        "scanner",
        "entry_decision",
        "submit",
        "fill",
        "holding",
        "scale_in",
        "exit",
    }
)

REPORT_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "main_scalping_lifecycle_paired_source_quality",
    "decision_authority": "source_only_candidate_evidence",
    "window_policy": "exact_trade_date_scanner_attempt_to_reconciled_final_exit",
    "sample_floor": "one_complete_exact_lineage_lifecycle",
    "primary_decision_metric": "complete_reconciled_lifecycle_coverage",
    "source_quality_gate": (
        "exact_lineage_complete_lifecycle_reconciled_cost_symbol_and_market_depth"
    ),
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "direct_runtime_or_order_apply",
        "provider_model_bot_threshold_price_quantity_or_cap_change",
        "hard_safety_or_broker_guard_bypass",
        "cross_attempt_symbol_or_timestamp_join",
        "label_horizon_as_actual_holding_duration",
        "raw_fallback_without_explicit_main_lifecycle_id_for_promotion",
    ],
}

PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT: dict[str, Any] = {
    "metric_role": "source_quality_gate",
    "decision_authority": "pipeline_owner_window_exclusion_only",
    "window_policy": "exact_trade_date_record_id_and_stock_code",
    "sample_floor": "not_applicable_source_quality_manifest",
    "primary_decision_metric": "excluded_pipeline_owner_count",
    "source_quality_gate": "missing_explicit_lifecycle_identity_owner_quarantine",
    "exclusion_scope": "exact_pipeline_owner_window",
    "runtime_effect": False,
    "runtime_authority": False,
    "order_authority": False,
    "provider_authority": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "forbidden_uses": [
        "infer_or_reconstruct_main_lifecycle_id",
        "join_by_symbol_or_timestamp_proximity",
        "exclude_other_clean_pipeline_owner_windows",
        "direct_runtime_or_order_apply",
    ],
}


def paired_report_path(target_date: str | date) -> Path:
    """Return the daily compact artifact path."""

    value = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    value = date.fromisoformat(value).isoformat()
    return REPORT_DIR / f"main_scalping_lifecycle_paired_{value}.json"


def report_path(target_date: str | date) -> Path:
    """Return the stable orchestration name for the daily report path."""

    return paired_report_path(target_date)


def pipeline_event_path(target_date: str | date) -> Path:
    """Return the existing live pipeline stream used by the default producer."""

    value = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    value = date.fromisoformat(value).isoformat()
    return PIPELINE_EVENT_DIR / f"pipeline_events_{value}.jsonl"


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(
                payload,
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        Path(temporary_name).unlink(missing_ok=True)


class _DigestingReader:
    """Proxy a binary source while hashing exactly the bytes read once."""

    def __init__(self, raw: BinaryIO) -> None:
        self._raw = raw
        self._hasher = hashlib.sha256()
        self.byte_count = 0

    def _record(self, payload: bytes) -> bytes:
        if payload:
            self._hasher.update(payload)
            self.byte_count += len(payload)
        return payload

    def read(self, size: int = -1) -> bytes:
        return self._record(self._raw.read(size))

    def readline(self, size: int = -1) -> bytes:
        return self._record(self._raw.readline(size))

    def readable(self) -> bool:
        return True

    @property
    def digest(self) -> str:
        return self._hasher.hexdigest()


@dataclass
class _StreamCensus:
    source_path: str
    source_exists: bool = False
    source_is_gzip: bool = False
    source_raw_sha256: str = field(
        default_factory=lambda: hashlib.sha256(b"").hexdigest()
    )
    source_raw_bytes: int = 0
    source_decoded_sha256: str = field(
        default_factory=lambda: hashlib.sha256(b"").hexdigest()
    )
    source_decoded_bytes: int = 0
    physical_line_count: int = 0
    blank_line_count: int = 0
    json_object_count: int = 0
    malformed_json_count: int = 0
    non_object_count: int = 0
    source_read_error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source_exists": self.source_exists,
            "source_is_gzip": self.source_is_gzip,
            "source_raw_sha256": self.source_raw_sha256,
            "source_raw_bytes": self.source_raw_bytes,
            "source_decoded_sha256": self.source_decoded_sha256,
            "source_decoded_bytes": self.source_decoded_bytes,
            "physical_line_count": self.physical_line_count,
            "blank_line_count": self.blank_line_count,
            "json_object_count": self.json_object_count,
            "malformed_json_count": self.malformed_json_count,
            "non_object_count": self.non_object_count,
            "source_read_error": self.source_read_error,
        }


def _resolve_source_path(path: Path) -> Path:
    if path.exists():
        return path
    gzip_path = path.with_name(path.name + ".gz")
    return gzip_path if gzip_path.exists() else path


def _stream_json_objects(
    path: Path,
) -> tuple[Iterator[tuple[int, dict[str, Any]]], _StreamCensus]:
    """Yield JSON objects and fill a census without retaining source rows."""

    resolved = _resolve_source_path(path)
    census = _StreamCensus(
        source_path=str(resolved),
        source_exists=resolved.exists(),
        source_is_gzip=resolved.suffix == ".gz",
    )

    def iterator() -> Iterator[tuple[int, dict[str, Any]]]:
        if not resolved.exists():
            return
        decoded_hasher = hashlib.sha256()
        try:
            with resolved.open("rb") as physical_handle:
                digesting_reader = _DigestingReader(physical_handle)
                decoded_stream: BinaryIO
                if resolved.suffix == ".gz":
                    decoded_stream = gzip.GzipFile(
                        fileobj=digesting_reader,
                        mode="rb",
                    )
                else:
                    decoded_stream = digesting_reader  # type: ignore[assignment]
                try:
                    while True:
                        raw_line = decoded_stream.readline()
                        if not raw_line:
                            break
                        census.physical_line_count += 1
                        census.source_decoded_bytes += len(raw_line)
                        decoded_hasher.update(raw_line)
                        stripped = raw_line.strip()
                        if not stripped:
                            census.blank_line_count += 1
                            continue
                        try:
                            payload = json.loads(stripped.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            census.malformed_json_count += 1
                            continue
                        if not isinstance(payload, dict):
                            census.non_object_count += 1
                            continue
                        census.json_object_count += 1
                        yield census.physical_line_count, payload
                finally:
                    if resolved.suffix == ".gz":
                        decoded_stream.close()
                    digesting_reader.read()
                    census.source_raw_sha256 = digesting_reader.digest
                    census.source_raw_bytes = digesting_reader.byte_count
                    census.source_decoded_sha256 = decoded_hasher.hexdigest()
        except (EOFError, OSError) as exc:
            census.source_read_error = type(exc).__name__

    return iterator(), census


def _aware_datetime(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError("timestamp_not_timezone_aware")
    return parsed


def _finite_number(
    value: Any,
    *,
    positive: bool = False,
    nonnegative: bool = False,
) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if (
        not math.isfinite(number)
        or (positive and number <= 0)
        or (nonnegative and number < 0)
    ):
        return None
    return number


def _pipeline_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _pipeline_text(value: Any) -> str:
    normalized = str(value or "").strip()
    return "" if normalized.lower() in {"", "-", "none", "null"} else normalized


def _pipeline_broker_order_numbers(
    fields: Mapping[str, Any],
) -> tuple[list[str] | None, str | None]:
    list_text = _pipeline_text(fields.get("broker_order_no_list"))
    primary = _pipeline_text(
        fields.get("broker_order_no") or fields.get("order_no") or fields.get("ord_no")
    )
    raw_values = list_text.split(",") if list_text else ([primary] if primary else [])
    order_numbers: list[str] = []
    for raw_value in raw_values:
        order_no = str(raw_value or "").strip()
        if not re.fullmatch(r"[0-9]{7}", order_no) or int(order_no) == 0:
            return None, "pipeline_broker_order_no_invalid"
        if order_no not in order_numbers:
            order_numbers.append(order_no)
    if not order_numbers:
        return None, "pipeline_broker_order_no_missing"
    if primary and primary not in order_numbers:
        return None, "pipeline_broker_order_primary_not_in_list"
    return order_numbers, None


def _pipeline_scale_in_decision(
    source_stage: str, fields: Mapping[str, Any]
) -> str | None:
    if source_stage in {"scale_in_order_submitted", "scale_in_executed"}:
        return (
            "ADD"
            if _pipeline_bool(fields.get("actual_order_submitted")) is True
            else None
        )
    if source_stage != "stat_action_decision_snapshot":
        return None
    chosen_action = _pipeline_text(fields.get("chosen_action")).lower()
    if chosen_action in {"avg_down_wait", "pyramid_wait"}:
        action_type = _pipeline_text(fields.get("scale_in_action_type")).upper()
        if action_type not in {"AVG_DOWN", "PYRAMID"}:
            return None
        if _pipeline_bool(fields.get("scale_in_gate_allowed")) is not True:
            return None
        return "ADD"
    if chosen_action == "hold_wait":
        return "NO_ADD"
    if chosen_action == "exit_now":
        return "NOT_APPLICABLE"
    return None


def _pipeline_transition_data(
    *,
    lifecycle_stage: str,
    source_stage: str,
    fields: Mapping[str, Any],
    lifecycle_stock_code: str,
    lifecycle_venue: str,
) -> tuple[dict[str, Any] | None, str | None]:
    data: dict[str, Any] = {}
    decision_trace_id = _pipeline_text(fields.get("main_lifecycle_decision_trace_id"))
    if decision_trace_id:
        data["decision_trace_id"] = decision_trace_id
    for source_key, destination_key in (
        (
            "main_lifecycle_market_observation_expected",
            "market_observation_expected",
        ),
        ("main_lifecycle_bbo_observed", "bbo_observed"),
        ("main_lifecycle_depth_observed", "depth_observed"),
        ("main_lifecycle_heartbeat", "heartbeat"),
    ):
        parsed = _pipeline_bool(fields.get(source_key))
        if parsed is not None:
            data[destination_key] = parsed

    action = _pipeline_text(fields.get("action"))
    reason = _pipeline_text(fields.get("reason"))
    if action:
        data["action"] = action
    if reason:
        data["reason"] = reason

    if lifecycle_stage == "submit":
        if _pipeline_bool(fields.get("actual_order_submitted")) is not True:
            return None, "pipeline_submit_not_explicitly_broker_submitted"
        data["actual_broker_order_submitted"] = True
        broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
        if broker_order_numbers is None:
            return None, order_error or "pipeline_submit_broker_order_no_missing"
        data["broker_order_no"] = broker_order_numbers[0]
        data["broker_order_no_list"] = ",".join(broker_order_numbers)
        requested_qty = _finite_number(
            fields.get("submitted_qty")
            if "submitted_qty" in fields
            else fields.get("requested_qty"),
            positive=True,
        )
        if requested_qty is None:
            return None, "pipeline_submit_requested_qty_invalid"
        data["requested_qty"] = requested_qty

    if lifecycle_stage == "fill":
        fill_state = _pipeline_text(fields.get("fill_state")).lower()
        if not fill_state:
            fill_quality = _pipeline_text(fields.get("fill_quality")).upper()
            fill_state = {
                "PARTIAL_FILL": "partial",
                "FULL_FILL": "full",
            }.get(fill_quality, "")
        if fill_state not in {"partial", "full"}:
            return None, "pipeline_fill_state_invalid"
        fill_qty = _finite_number(fields.get("fill_qty"), positive=True)
        fill_price = _finite_number(fields.get("fill_price"), positive=True)
        if fill_qty is None or fill_price is None:
            return None, "pipeline_fill_price_or_qty_invalid"
        data.update(
            {
                "fill_state": fill_state,
                "fill_qty": fill_qty,
                "fill_price": fill_price,
            }
        )
        requested_qty = _finite_number(fields.get("requested_qty"), positive=True)
        if requested_qty is not None:
            data["requested_qty"] = requested_qty

    if lifecycle_stage == "holding":
        data.setdefault("action", "HOLD")

    if lifecycle_stage == "scale_in":
        decision = _pipeline_scale_in_decision(source_stage, fields)
        if decision is None:
            return None, "pipeline_scale_in_decision_unmapped"
        data["scale_in_decision"] = decision
        if source_stage == "scale_in_order_submitted":
            broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
            if broker_order_numbers is None:
                return None, order_error or "pipeline_scale_in_order_no_missing"
            requested_qty = _finite_number(
                fields.get("submitted_qty")
                if "submitted_qty" in fields
                else fields.get("qty"),
                positive=True,
            )
            if requested_qty is None:
                return None, "pipeline_scale_in_submitted_qty_invalid"
            data.update(
                {
                    "actual_broker_order_submitted": True,
                    "broker_order_no": broker_order_numbers[0],
                    "broker_order_no_list": ",".join(broker_order_numbers),
                    "requested_qty": requested_qty,
                }
            )
        if source_stage == "scale_in_executed":
            fill_qty = _finite_number(fields.get("fill_qty"), positive=True)
            fill_price = _finite_number(fields.get("fill_price"), positive=True)
            if fill_qty is None or fill_price is None:
                return None, "pipeline_scale_in_fill_price_or_qty_invalid"
            data.update({"fill_qty": fill_qty, "fill_price": fill_price})

    if lifecycle_stage == "exit" and source_stage == "sell_order_sent":
        if _pipeline_bool(fields.get("actual_order_submitted")) is not True:
            return None, "pipeline_sell_not_explicitly_broker_submitted"
        broker_order_numbers, order_error = _pipeline_broker_order_numbers(fields)
        if broker_order_numbers is None:
            return None, order_error or "pipeline_sell_order_no_missing"
        requested_qty = _finite_number(
            fields.get("qty") if "qty" in fields else fields.get("requested_qty"),
            positive=True,
        )
        if requested_qty is None:
            return None, "pipeline_sell_submitted_qty_invalid"
        data.update(
            {
                "actual_broker_order_submitted": True,
                "broker_order_no": broker_order_numbers[0],
                "broker_order_no_list": ",".join(broker_order_numbers),
                "requested_qty": requested_qty,
            }
        )

    execution_exit_stages = {
        "nxt_rising_missed_tp1_partial_fill_progress",
        "nxt_rising_missed_tp1_partial_sell_completed",
        "sell_completed",
    }
    if lifecycle_stage == "exit" and source_stage in execution_exit_stages:
        if (
            "main_lifecycle_exit_qty" not in fields
            or "main_lifecycle_exit_price" not in fields
        ):
            return None, "pipeline_execution_exit_exact_price_or_qty_missing"
        exit_qty = _finite_number(fields.get("main_lifecycle_exit_qty"), positive=True)
        exit_price = _finite_number(
            fields.get("main_lifecycle_exit_price"), positive=True
        )
        if exit_qty is None or exit_price is None:
            return None, "pipeline_execution_exit_exact_price_or_qty_invalid"
        data["exit_qty"] = exit_qty
        data["exit_price"] = exit_price
        basis_price_present = "main_lifecycle_slippage_basis_price" in fields
        basis_source_present = "main_lifecycle_slippage_basis_source" in fields
        if basis_price_present != basis_source_present:
            return None, "pipeline_slippage_basis_pair_incomplete"
        if basis_price_present:
            slippage_basis_price = _finite_number(
                fields.get("main_lifecycle_slippage_basis_price"), positive=True
            )
            slippage_basis_source = _pipeline_text(
                fields.get("main_lifecycle_slippage_basis_source")
            )
            if slippage_basis_price is None or not slippage_basis_source:
                return None, "pipeline_slippage_basis_pair_invalid"
            data["slippage_basis_price"] = slippage_basis_price
            data["slippage_basis_source"] = slippage_basis_source

    terminal_no_fill = _pipeline_bool(fields.get("main_lifecycle_terminal_no_fill"))
    if terminal_no_fill is True:
        data["terminal_no_fill"] = True
        data["terminal_reason"] = (
            _pipeline_text(fields.get("main_lifecycle_terminal_reason"))
            or "explicit_pipeline_terminal_no_fill"
        )

    reconciled_final_exit = _pipeline_bool(
        fields.get("main_lifecycle_reconciled_final_exit")
    )
    if reconciled_final_exit is True:
        if lifecycle_stage != "exit" or source_stage != "sell_completed":
            return None, "pipeline_final_exit_stage_invalid"
        if _pipeline_bool(fields.get("main_lifecycle_broker_reconciled")) is not True:
            return None, "pipeline_final_exit_not_broker_reconciled"
        if "exit_qty" not in data or "exit_price" not in data:
            return None, "pipeline_final_exit_price_or_qty_missing"
        data["broker_reconciled"] = True
        data["reconciled_final_exit"] = True

    for source_key, destination_key, nonnegative in (
        ("main_lifecycle_fees_taxes_krw", "fees_taxes_krw", True),
        ("main_lifecycle_slippage_krw", "slippage_krw", True),
        ("main_lifecycle_realized_net_pnl_krw", "realized_net_pnl_krw", False),
    ):
        value = _finite_number(fields.get(source_key), nonnegative=nonnegative)
        if value is not None:
            data[destination_key] = value

    execution_qty: Any | None = None
    execution_price: Any | None = None
    if lifecycle_stage == "fill":
        execution_qty = data.get("fill_qty")
        execution_price = data.get("fill_price")
    elif (
        lifecycle_stage == "scale_in"
        and source_stage == "scale_in_executed"
        and data.get("scale_in_decision") == "ADD"
    ):
        execution_qty = data.get("fill_qty")
        execution_price = data.get("fill_price")
    elif lifecycle_stage == "exit" and source_stage in execution_exit_stages:
        execution_qty = data.get("exit_qty")
        execution_price = data.get("exit_price")
    if execution_qty is not None and execution_price is not None:
        broker_provenance = build_broker_execution_provenance(
            fields,
            expected_qty=execution_qty,
            expected_price=execution_price,
            expected_stock_code=lifecycle_stock_code,
            expected_side="SELL" if lifecycle_stage == "exit" else "BUY",
            lifecycle_venue=lifecycle_venue,
            # The official quantity/remainder pair owns partial/full.  A
            # producer label is never allowed to duplicate one execution by
            # relabeling the same raw identity on replay.
            expected_fill_state=None,
        )
        data.update(broker_provenance)
        if (
            lifecycle_stage == "fill"
            and broker_provenance.get("broker_execution_provenance_state") == "complete"
        ):
            data["fill_state"] = broker_provenance["broker_execution_fill_state"]
    return data, None


def _validated_pipeline_transition(
    raw_row: Mapping[str, Any], *, target_date: str
) -> tuple[dict[str, Any] | None, str | None, bool]:
    """Validate one explicitly instrumented pipeline row.

    The final boolean marks whether the raw pipeline/stage is in the strict
    lifecycle allowlist.  Out-of-scope pipeline rows are ignored; an in-scope
    row without exact identity is an instrumentation gap, never a join input.
    """

    if raw_row.get("event_type") != "pipeline_event":
        return None, None, False
    pipeline = _pipeline_text(raw_row.get("pipeline")).upper()
    source_stage = _pipeline_text(raw_row.get("stage"))
    lifecycle_stage = PIPELINE_STAGE_MAP.get((pipeline, source_stage))
    if lifecycle_stage is None:
        return None, None, False
    fields = raw_row.get("fields")
    if not isinstance(fields, dict):
        return None, "pipeline_lifecycle_fields_invalid", True
    if fields.get(
        "pipeline_lifecycle_population_scope"
    ) == "sim_observation_only" and raw_row.get("record_id") in {None, ""}:
        return None, None, False
    # Statistical action snapshots also serve a separate simulator lane.  A
    # source-declared sim-only snapshot has no real RecommendationHistory
    # record and is not a main-bot lifecycle transition.  Keep it out of the
    # strict denominator instead of turning expected sim telemetry into an
    # unbound global instrumentation failure.
    if (
        source_stage == "stat_action_decision_snapshot"
        and raw_row.get("record_id") in {None, ""}
        and str(fields.get("decision_authority") or "").strip()
        == "sim_observation_only"
        and _pipeline_bool(fields.get("snapshot_observe_only")) is True
    ):
        return None, None, False
    if fields.get("main_lifecycle_identity_schema") != PIPELINE_IDENTITY_SCHEMA:
        return None, "pipeline_lifecycle_identity_missing", True
    if fields.get("main_lifecycle_source_pipeline") != pipeline:
        return None, "pipeline_lifecycle_source_pipeline_mismatch", True
    if fields.get("main_lifecycle_source_stage") != source_stage:
        return None, "pipeline_lifecycle_source_stage_mismatch", True
    if fields.get("main_lifecycle_stage") != lifecycle_stage:
        return None, "pipeline_lifecycle_stage_mapping_mismatch", True
    if fields.get("main_lifecycle_trade_date") != target_date:
        return None, "pipeline_lifecycle_trade_date_mismatch", True
    if fields.get("main_lifecycle_decision_authority") != (
        "source_only_lifecycle_observation"
    ):
        return None, "pipeline_lifecycle_authority_mismatch", True
    for key in (
        "main_lifecycle_runtime_effect",
        "main_lifecycle_order_authority",
        "main_lifecycle_provider_authority",
    ):
        if _pipeline_bool(fields.get(key)) is not False:
            return None, f"pipeline_lifecycle_authority_mismatch:{key}", True

    record_id = raw_row.get("record_id")
    stock_code = _pipeline_text(raw_row.get("stock_code"))
    attempt_id = _pipeline_text(fields.get("attempt_id"))
    if attempt_id != _pipeline_text(fields.get("main_lifecycle_attempt_id")):
        return None, "pipeline_lifecycle_attempt_id_mismatch", True
    if str(record_id if record_id is not None else "").strip() != _pipeline_text(
        fields.get("main_lifecycle_record_id")
    ):
        return None, "pipeline_lifecycle_record_id_mismatch", True
    if stock_code != _pipeline_text(fields.get("main_lifecycle_stock_code")):
        return None, "pipeline_lifecycle_stock_code_mismatch", True
    observed_at = _pipeline_text(fields.get("main_lifecycle_observed_at"))
    try:
        _aware_datetime(observed_at)
    except (TypeError, ValueError):
        return None, "pipeline_lifecycle_explicit_timestamp_invalid", True

    data, data_error = _pipeline_transition_data(
        lifecycle_stage=lifecycle_stage,
        source_stage=source_stage,
        fields=fields,
        lifecycle_stock_code=stock_code,
        lifecycle_venue=(
            _pipeline_text(fields.get("main_lifecycle_venue")) or "UNKNOWN"
        ),
    )
    if data is None:
        return None, data_error or "pipeline_lifecycle_data_invalid", True
    try:
        transition = build_transition(
            main_lifecycle_id=_pipeline_text(fields.get("main_lifecycle_id")),
            record_id=record_id,
            stock_code=stock_code,
            attempt_id=attempt_id,
            trade_date=target_date,
            stage=lifecycle_stage,
            observed_at=observed_at,
            venue=_pipeline_text(fields.get("main_lifecycle_venue")) or "UNKNOWN",
            session_bucket=(
                _pipeline_text(fields.get("main_lifecycle_session_bucket")) or "unknown"
            ),
            data=data,
        )
    except (TypeError, ValueError) as exc:
        return None, f"pipeline_lifecycle_contract_invalid:{exc}", True
    return transition, None, True


def _validated_transition(
    raw_row: Mapping[str, Any], *, target_date: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Return an exact canonical transition or a non-joinable reason."""

    if raw_row.get("schema") != JOURNAL_SCHEMA:
        return None, "transition_schema_mismatch"
    if raw_row.get("trade_date") != target_date:
        return None, "transition_trade_date_mismatch"
    if raw_row.get("stage") not in VALID_STAGES:
        return None, "transition_stage_invalid"
    if not isinstance(raw_row.get("data"), dict):
        return None, "transition_data_invalid"
    for key, expected in AUTHORITY_CONTRACT.items():
        if raw_row.get(key) != expected:
            return None, f"transition_authority_contract_mismatch:{key}"
    try:
        canonical = build_transition(
            main_lifecycle_id=str(raw_row.get("main_lifecycle_id") or ""),
            record_id=raw_row.get("record_id"),
            stock_code=raw_row.get("stock_code"),
            attempt_id=raw_row.get("attempt_id"),
            trade_date=target_date,
            stage=str(raw_row.get("stage") or ""),
            observed_at=str(raw_row.get("observed_at") or ""),
            venue=str(raw_row.get("venue") or "UNKNOWN"),
            session_bucket=str(raw_row.get("session_bucket") or "unknown"),
            data=raw_row.get("data"),
        )
    except (TypeError, ValueError) as exc:
        return None, f"transition_contract_invalid:{exc}"
    if dict(raw_row) != canonical:
        return None, "transition_content_or_lineage_mismatch"
    return canonical, None


@dataclass
class _LifecycleAccumulator:
    main_lifecycle_id: str
    record_id: str
    stock_code: str
    attempt_id: str
    trade_date: str
    venue: str
    session_bucket: str
    stage_counts: dict[str, int] = field(default_factory=dict)
    transition_count: int = 0
    invalid_transition_count: int = 0
    invalid_reasons: list[str] = field(default_factory=list)
    first_observed_at: datetime | None = None
    last_observed_at: datetime | None = None
    scanner_first_at: datetime | None = None
    scanner_last_at: datetime | None = None
    scanner_sample_count: int = 0
    explicit_exposure_total_sec: float = 0.0
    explicit_exposure_current_start: datetime | None = None
    explicit_exposure_current_end: datetime | None = None
    explicit_exposure_last_start: datetime | None = None
    explicit_exposure_interval_count: int = 0
    market_observation_expected_count: int = 0
    bbo_observed_count: int = 0
    depth_observed_count: int = 0
    decision_trace_ids: list[str] = field(default_factory=list)
    trace_ids_overflow_count: int = 0
    partial_fill_event_count: int = 0
    full_fill_event_count: int = 0
    first_fill_at: datetime | None = None
    final_exit_at: datetime | None = None
    terminal_no_fill_at: datetime | None = None
    terminal_no_fill_reason: str | None = None
    final_exit_reconciled: bool = False
    requested_qty_max: float | None = None
    entry_fill_qty: float = 0.0
    scale_in_fill_qty: float = 0.0
    exit_qty: float = 0.0
    exit_amount_krw: float = 0.0
    exit_execution_leg_count: int = 0
    slippage_basis_covered_qty: float = 0.0
    slippage_basis_source_covered_qty: float = 0.0
    slippage_basis_amount_krw: float = 0.0
    slippage_basis_sources: list[str] = field(default_factory=list)
    economics_covered_exit_qty: dict[str, float] = field(default_factory=dict)
    open_qty: float = 0.0
    open_cost_krw: float = 0.0
    capital_time_krw_seconds: float = 0.0
    scale_in_decisions: list[str] = field(default_factory=list)
    fees_taxes_krw: float = 0.0
    slippage_krw: float = 0.0
    realized_net_pnl_krw: float = 0.0
    economics_observation_count: int = 0
    reviewed_cost_profile_sha256: str | None = None
    cost_hash_conflict: bool = False
    symbol_master_artifact_sha256: str | None = None
    symbol_hash_conflict: bool = False
    cost_verified_seen: bool = False
    cost_verified_all: bool = True
    symbol_verified_seen: bool = False
    symbol_verified_all: bool = True
    economics_fields_seen: set[str] = field(default_factory=set)
    observed_actual_broker_order_submitted: bool = False
    event_content_by_id: dict[str, str] = field(default_factory=dict)
    transition_replay_duplicate_count: int = 0
    broker_execution_content_by_identity: dict[str, str] = field(default_factory=dict)
    broker_execution_unique_count: int = 0
    broker_execution_replay_duplicate_count: int = 0
    broker_execution_conflict_count: int = 0
    broker_execution_order_progress_conflict_count: int = 0
    broker_execution_submission_link_conflict_count: int = 0
    broker_execution_provenance_state_counts: dict[str, int] = field(
        default_factory=dict
    )
    broker_order_progress_by_no: dict[str, tuple[int, int, int, int, int]] = field(
        default_factory=dict
    )
    submitted_order_phase_by_no: dict[str, str] = field(default_factory=dict)
    submitted_order_observed_seconds_by_no: dict[str, int] = field(default_factory=dict)
    submitted_requested_qty_by_order_no: dict[str, int] = field(default_factory=dict)
    submitted_order_group_keys: set[tuple[str, tuple[str, ...], int]] = field(
        default_factory=set
    )
    submitted_requested_qty_by_phase: dict[str, int] = field(default_factory=dict)
    executed_order_qty_by_phase: dict[str, dict[str, int]] = field(default_factory=dict)
    broker_submission_replay_duplicate_count: int = 0
    broker_execution_provenance_gap_count: int = 0
    broker_execution_provenance_gap_reasons: list[str] = field(default_factory=list)
    broker_execution_entry_covered_qty: float = 0.0
    broker_execution_exit_covered_qty: float = 0.0
    broker_execution_partial_count: int = 0
    broker_execution_full_count: int = 0
    broker_order_no_cross_lifecycle_conflict_count: int = 0
    broker_execution_cross_lifecycle_identity_conflict_count: int = 0

    @classmethod
    def from_transition(cls, row: Mapping[str, Any]) -> _LifecycleAccumulator:
        return cls(
            main_lifecycle_id=str(row["main_lifecycle_id"]),
            record_id=str(row["record_id"]),
            stock_code=str(row["stock_code"]),
            attempt_id=str(row["attempt_id"]),
            trade_date=str(row["trade_date"]),
            venue=str(row["venue"]),
            session_bucket=str(row["session_bucket"]),
        )

    def _invalid(self, reason: str) -> None:
        self.invalid_transition_count += 1
        if reason not in self.invalid_reasons and len(self.invalid_reasons) < 20:
            self.invalid_reasons.append(reason)

    def _matches_lineage(self, row: Mapping[str, Any]) -> bool:
        return all(
            (
                str(row.get("record_id")) == self.record_id,
                str(row.get("stock_code")) == self.stock_code,
                str(row.get("attempt_id")) == self.attempt_id,
                str(row.get("trade_date")) == self.trade_date,
                str(row.get("venue")) == self.venue,
                str(row.get("session_bucket")) == self.session_bucket,
            )
        )

    def _stage_contract_error(self, row: Mapping[str, Any]) -> str | None:
        stage = str(row.get("stage") or "")
        data = row.get("data")
        assert isinstance(data, dict)
        if self.final_exit_at is not None or self.terminal_no_fill_at is not None:
            return "transition_after_terminal"
        if self.transition_count == 0 and stage != "scanner":
            return "scanner_transition_must_start_lifecycle"
        if stage == "scanner" and any(
            existing_stage != "scanner" for existing_stage in self.stage_counts
        ):
            return "scanner_after_entry_phase"
        if stage == "entry_decision":
            if "scanner" not in self.stage_counts:
                return "entry_decision_before_scanner"
            if any(
                existing_stage in self.stage_counts
                for existing_stage in {"submit", "fill", "holding", "scale_in", "exit"}
            ):
                return "entry_decision_after_submit_phase"
        if stage == "submit":
            if "entry_decision" not in self.stage_counts:
                return "submit_before_entry_decision"
            if self.first_fill_at is not None or any(
                existing_stage in self.stage_counts
                for existing_stage in {"holding", "scale_in", "exit"}
            ):
                return "submit_after_fill_phase"
        if stage == "fill" and "submit" not in self.stage_counts:
            return "fill_before_submit"
        if stage == "fill" and "exit" in self.stage_counts:
            return "fill_after_exit_phase"
        if stage == "holding" and self.first_fill_at is None:
            return "holding_before_fill"
        if stage == "scale_in":
            if self.first_fill_at is None:
                return "scale_in_before_fill"
            if "holding" not in self.stage_counts:
                return "scale_in_before_holding"
        if (
            stage == "exit"
            and data.get("terminal_no_fill") is not True
            and self.first_fill_at is None
        ):
            return "exit_before_fill"
        return None

    def _duplicate_event_state(self, row: Mapping[str, Any]) -> str:
        event_id = str(row.get("event_id") or "").strip()
        content_hash = str(row.get("transition_content_sha256") or "").strip()
        previous = self.event_content_by_id.get(event_id)
        if previous is not None:
            if previous == content_hash:
                return "replay"
            return "conflict"
        if len(self.event_content_by_id) >= _EVENT_ID_LIMIT_PER_LIFECYCLE:
            return "limit"
        return "new"

    def _retain_event_identity(self, row: Mapping[str, Any]) -> None:
        event_id = str(row.get("event_id") or "").strip()
        content_hash = str(row.get("transition_content_sha256") or "").strip()
        self.event_content_by_id[event_id] = content_hash

    @staticmethod
    def _submission_phase(stage: str, data: Mapping[str, Any]) -> str | None:
        if stage == "submit" and data.get("terminal_no_fill") is not True:
            return "entry"
        if (
            stage == "scale_in"
            and data.get("scale_in_decision") == "ADD"
            and "fill_qty" not in data
            and data.get("actual_broker_order_submitted") is True
        ):
            return "scale_in"
        if (
            stage == "exit"
            and "exit_qty" not in data
            and data.get("actual_broker_order_submitted") is True
        ):
            return "exit"
        return None

    @staticmethod
    def _execution_phase(stage: str) -> str:
        if stage == "fill":
            return "entry"
        if stage == "scale_in":
            return "scale_in"
        return "exit"

    def _observe_order_submission(
        self,
        stage: str,
        data: Mapping[str, Any],
        *,
        observed_at: datetime,
    ) -> str:
        phase = self._submission_phase(stage, data)
        if phase is None:
            return "not_applicable"
        raw_order_numbers = str(data.get("broker_order_no_list") or "").split(",")
        order_numbers = tuple(
            order_no.strip() for order_no in raw_order_numbers if order_no.strip()
        )
        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if (
            not order_numbers
            or len(order_numbers) != 1
            or requested_qty is None
            or not requested_qty.is_integer()
        ):
            return "conflict"
        requested_int = int(requested_qty)
        group_key = (phase, order_numbers, requested_int)
        if group_key in self.submitted_order_group_keys:
            self.broker_submission_replay_duplicate_count += 1
            return "replay"
        for order_no in order_numbers:
            previous_phase = self.submitted_order_phase_by_no.get(order_no)
            if previous_phase is not None:
                return "conflict"
        self.submitted_order_group_keys.add(group_key)
        self.submitted_requested_qty_by_phase[phase] = (
            self.submitted_requested_qty_by_phase.get(phase, 0) + requested_int
        )
        observed_kst = observed_at.astimezone(KST)
        observed_seconds = (
            observed_kst.hour * 3600 + observed_kst.minute * 60 + observed_kst.second
        )
        for order_no in order_numbers:
            self.submitted_order_phase_by_no[order_no] = phase
            self.submitted_order_observed_seconds_by_no[order_no] = observed_seconds
            self.submitted_requested_qty_by_order_no[order_no] = requested_int
        return "new"

    @staticmethod
    def _execution_bearing_data(stage: str, data: Mapping[str, Any]) -> bool:
        if stage == "fill":
            return True
        if stage == "scale_in":
            return data.get("scale_in_decision") == "ADD" and "fill_qty" in data
        return stage == "exit" and "exit_qty" in data

    @staticmethod
    def _broker_execution_semantic_sha256(stage: str, data: Mapping[str, Any]) -> str:
        keys = (
            "broker_execution_content_sha256",
            "fill_state",
            "fill_qty",
            "fill_price",
            "exit_qty",
            "exit_price",
            "broker_reconciled",
            "reconciled_final_exit",
            "fees_taxes_krw",
            "slippage_krw",
            "slippage_basis_price",
            "slippage_basis_source",
            "realized_net_pnl_krw",
        )
        return _sha256(
            {
                "stage": stage,
                "data": {key: data.get(key) for key in keys if key in data},
            }
        )

    def _existing_broker_execution_state(
        self, stage: str, data: Mapping[str, Any]
    ) -> str:
        if (
            not self._execution_bearing_data(stage, data)
            or data.get("broker_execution_provenance_state") != "complete"
        ):
            return "new"
        identity = str(data.get("broker_execution_identity") or "").strip()
        previous = self.broker_execution_content_by_identity.get(identity)
        if previous is None:
            return "new"
        semantic_hash = self._broker_execution_semantic_sha256(stage, data)
        return "replay" if previous == semantic_hash else "conflict"

    def _observe_broker_execution(
        self,
        stage: str,
        data: Mapping[str, Any],
        *,
        observed_at: datetime,
    ) -> str:
        """Return a bounded execution observation state."""

        if not self._execution_bearing_data(stage, data):
            return "not_applicable"
        state = (
            str(data.get("broker_execution_provenance_state") or "missing")
            .strip()
            .lower()
        )
        if state not in {"complete", "missing", "incomplete", "invalid"}:
            state = "invalid"
        if state != "complete":
            self.broker_execution_provenance_state_counts[state] = (
                self.broker_execution_provenance_state_counts.get(state, 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = str(
                data.get("broker_execution_provenance_error")
                or "broker_execution_provenance_not_complete"
            )[:256]
            if (
                reason not in self.broker_execution_provenance_gap_reasons
                and len(self.broker_execution_provenance_gap_reasons) < 20
            ):
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"

        identity = str(data.get("broker_execution_identity") or "").strip()
        content_hash = str(data.get("broker_execution_content_sha256") or "").strip()
        if not identity or not SHA256_RE.fullmatch(content_hash):
            self.broker_execution_provenance_state_counts["invalid"] = (
                self.broker_execution_provenance_state_counts.get("invalid", 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = "broker_execution_identity_or_hash_invalid"
            if reason not in self.broker_execution_provenance_gap_reasons:
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"
        semantic_hash = self._broker_execution_semantic_sha256(stage, data)
        previous = self.broker_execution_content_by_identity.get(identity)
        if previous is not None:
            if previous == semantic_hash:
                self.broker_execution_replay_duplicate_count += 1
                return "replay"
            self.broker_execution_conflict_count += 1
            return "conflict"

        order_no = str(data.get("broker_execution_order_no") or "")
        execution_phase = self._execution_phase(stage)
        if self.submitted_order_phase_by_no.get(order_no) != execution_phase:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        submitted_seconds = self.submitted_order_observed_seconds_by_no.get(order_no)
        submitted_order_qty = self.submitted_requested_qty_by_order_no.get(order_no)
        if submitted_seconds is None or submitted_order_qty is None:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        expected_side = "SELL" if execution_phase == "exit" else "BUY"
        if (
            str(data.get("broker_execution_stock_code") or "") != self.stock_code
            or str(data.get("broker_execution_side") or "") != expected_side
        ):
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        try:
            order_qty = int(data["broker_execution_order_qty"])
            cumulative_qty = int(data["broker_execution_cumulative_fill_qty"])
            cumulative_amount = int(data["broker_execution_cumulative_fill_amount_krw"])
            remaining_qty = int(data["broker_execution_remaining_qty"])
            execution_price = int(data["broker_execution_price"])
            unit_qty = int(data["broker_execution_unit_fill_qty"])
            execution_time_text = str(data["broker_execution_time_hhmmss"])
            execution_time_seconds = (
                int(execution_time_text[:2]) * 3600
                + int(execution_time_text[2:4]) * 60
                + int(execution_time_text[4:])
            )
        except (KeyError, TypeError, ValueError):
            self.broker_execution_provenance_state_counts["invalid"] = (
                self.broker_execution_provenance_state_counts.get("invalid", 0) + 1
            )
            self.broker_execution_provenance_gap_count += 1
            reason = "broker_execution_canonical_numeric_fields_invalid"
            if reason not in self.broker_execution_provenance_gap_reasons:
                self.broker_execution_provenance_gap_reasons.append(reason)
            return "gap"
        if order_qty != submitted_order_qty:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        previous_progress = self.broker_order_progress_by_no.get(order_no)
        observed_kst = observed_at.astimezone(KST)
        observed_time_seconds = (
            observed_kst.hour * 3600 + observed_kst.minute * 60 + observed_kst.second
        )
        if execution_time_seconds + _BROKER_SUBMIT_CLOCK_SKEW_SEC < submitted_seconds:
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        if previous_progress is None:
            progress_valid = (
                cumulative_qty == unit_qty
                and cumulative_amount == unit_qty * execution_price
                and execution_time_seconds <= observed_time_seconds
            )
        else:
            (
                previous_order_qty,
                previous_cumulative_qty,
                previous_cumulative_amount,
                previous_remaining_qty,
                previous_execution_time_seconds,
            ) = previous_progress
            progress_valid = all(
                (
                    order_qty == previous_order_qty,
                    cumulative_qty - previous_cumulative_qty == unit_qty,
                    cumulative_amount - previous_cumulative_amount
                    == unit_qty * execution_price,
                    remaining_qty < previous_remaining_qty,
                    execution_time_seconds >= previous_execution_time_seconds,
                    execution_time_seconds <= observed_time_seconds,
                )
            )
        if not progress_valid:
            self.broker_execution_order_progress_conflict_count += 1
            return "order_progress_conflict"

        self.broker_execution_content_by_identity[identity] = semantic_hash
        self.broker_order_progress_by_no[order_no] = (
            order_qty,
            cumulative_qty,
            cumulative_amount,
            remaining_qty,
            execution_time_seconds,
        )
        phase_orders = self.executed_order_qty_by_phase.setdefault(execution_phase, {})
        previous_phase_order_qty = phase_orders.get(order_no)
        if (
            previous_phase_order_qty is not None
            and previous_phase_order_qty != order_qty
        ):
            self.broker_execution_submission_link_conflict_count += 1
            return "submission_conflict"
        phase_orders[order_no] = order_qty
        self.broker_execution_unique_count += 1
        self.broker_execution_provenance_state_counts["complete"] = (
            self.broker_execution_provenance_state_counts.get("complete", 0) + 1
        )
        fill_state = str(data.get("broker_execution_fill_state") or "")
        if fill_state == "partial":
            self.broker_execution_partial_count += 1
        elif fill_state == "full":
            self.broker_execution_full_count += 1
        return "new"

    def _integrate_capital(self, timestamp: datetime) -> bool:
        if self.last_observed_at is None:
            return True
        elapsed = (timestamp - self.last_observed_at).total_seconds()
        if elapsed < 0:
            self._invalid("lifecycle_timestamp_regression")
            return False
        self.capital_time_krw_seconds += self.open_cost_krw * elapsed
        return True

    def _observe_trace_id(self, value: Any) -> None:
        trace_id = str(value or "").strip()
        if not trace_id or trace_id in self.decision_trace_ids:
            return
        if len(self.decision_trace_ids) >= _TRACE_ID_LIMIT:
            self.trace_ids_overflow_count += 1
            self._invalid("decision_trace_id_limit_exceeded")
            return
        self.decision_trace_ids.append(trace_id)

    def _observe_interval(self, data: Mapping[str, Any]) -> None:
        start_value = data.get("session_exposure_start_at")
        end_value = data.get("session_exposure_end_at")
        if start_value is None and end_value is None:
            return
        if start_value is None or end_value is None:
            self._invalid("session_exposure_interval_incomplete")
            return
        try:
            start_at = _aware_datetime(start_value)
            end_at = _aware_datetime(end_value)
        except (TypeError, ValueError):
            self._invalid("session_exposure_interval_invalid")
            return
        if end_at <= start_at:
            self._invalid("session_exposure_interval_non_positive")
            return
        if (
            self.explicit_exposure_last_start is not None
            and start_at < self.explicit_exposure_last_start
        ):
            self._invalid("session_exposure_interval_out_of_order")
            return
        self.explicit_exposure_last_start = start_at
        self.explicit_exposure_interval_count += 1
        if self.explicit_exposure_current_start is None:
            self.explicit_exposure_current_start = start_at
            self.explicit_exposure_current_end = end_at
            return
        assert self.explicit_exposure_current_end is not None
        if start_at <= self.explicit_exposure_current_end:
            self.explicit_exposure_current_end = max(
                self.explicit_exposure_current_end,
                end_at,
            )
            return
        self.explicit_exposure_total_sec += (
            self.explicit_exposure_current_end - self.explicit_exposure_current_start
        ).total_seconds()
        self.explicit_exposure_current_start = start_at
        self.explicit_exposure_current_end = end_at

    def _observe_hashes(self, data: Mapping[str, Any]) -> None:
        cost_hash = str(data.get("cost_artifact_sha256") or "").strip()
        if cost_hash:
            if not SHA256_RE.fullmatch(cost_hash):
                self._invalid("cost_artifact_sha256_invalid")
            elif self.reviewed_cost_profile_sha256 is None:
                self.reviewed_cost_profile_sha256 = cost_hash
            elif self.reviewed_cost_profile_sha256 != cost_hash:
                self.cost_hash_conflict = True
                self._invalid("cost_artifact_hash_conflict")
            self.cost_verified_seen = True
            self.cost_verified_all = (
                self.cost_verified_all and data.get("cost_artifact_verified") is True
            )
        symbol_hash = str(data.get("symbol_master_sha256") or "").strip()
        if symbol_hash:
            if not SHA256_RE.fullmatch(symbol_hash):
                self._invalid("symbol_master_sha256_invalid")
            elif self.symbol_master_artifact_sha256 is None:
                self.symbol_master_artifact_sha256 = symbol_hash
            elif self.symbol_master_artifact_sha256 != symbol_hash:
                self.symbol_hash_conflict = True
                self._invalid("symbol_master_hash_conflict")
            self.symbol_verified_seen = True
            self.symbol_verified_all = (
                self.symbol_verified_all and data.get("symbol_master_verified") is True
            )

    def bind_reference_contract(
        self,
        *,
        reviewed_cost_profile_sha256: str | None,
        reviewed_cost_profile_verified: bool,
        symbol_master_artifact_sha256: str | None,
        symbol_master_artifact_verified: bool,
    ) -> None:
        if reviewed_cost_profile_sha256 is not None:
            self.reviewed_cost_profile_sha256 = reviewed_cost_profile_sha256
            self.cost_verified_seen = True
            self.cost_verified_all = reviewed_cost_profile_verified
        if symbol_master_artifact_sha256 is not None:
            self.symbol_master_artifact_sha256 = symbol_master_artifact_sha256
            self.symbol_verified_seen = True
            self.symbol_verified_all = symbol_master_artifact_verified

    def _observe_economics(self, stage: str, data: Mapping[str, Any]) -> None:
        found = False
        for key in ("fees_taxes_krw", "slippage_krw", "realized_net_pnl_krw"):
            if key not in data:
                continue
            if stage != "exit":
                self._invalid(f"{key}_outside_exit")
                continue
            value = _finite_number(
                data.get(key),
                nonnegative=key in {"fees_taxes_krw", "slippage_krw"},
            )
            if value is None:
                self._invalid(f"{key}_invalid")
                continue
            setattr(self, key, getattr(self, key) + value)
            self.economics_fields_seen.add(key)
            found = True
        if found:
            self.economics_observation_count += 1

    def _add_fill(self, *, quantity: float, price: float, scale_in: bool) -> None:
        self.open_qty += quantity
        self.open_cost_krw += quantity * price
        if scale_in:
            self.scale_in_fill_qty += quantity
        else:
            self.entry_fill_qty += quantity

    def _apply_exit(self, quantity: float, price: float) -> None:
        if quantity > self.open_qty + _QUANTITY_EPSILON:
            self._invalid("exit_qty_exceeds_open_qty")
            return
        average_cost = self.open_cost_krw / self.open_qty if self.open_qty > 0 else 0.0
        self.open_qty = max(0.0, self.open_qty - quantity)
        self.open_cost_krw = max(0.0, self.open_cost_krw - average_cost * quantity)
        self.exit_qty += quantity
        self.exit_amount_krw += quantity * price
        self.exit_execution_leg_count += 1

    def consume(self, row: Mapping[str, Any]) -> None:
        if not self._matches_lineage(row):
            self._invalid("cross_attempt_join_blocked")
            return
        duplicate_state = self._duplicate_event_state(row)
        if duplicate_state == "replay":
            self.transition_replay_duplicate_count += 1
            return
        if duplicate_state == "conflict":
            self._invalid("duplicate_event_id_content_conflict")
            return
        if duplicate_state == "limit":
            self._invalid("transition_event_identity_limit_exceeded")
            return
        stage = str(row["stage"])
        data = row["data"]
        assert isinstance(data, dict)
        existing_broker_execution = self._existing_broker_execution_state(stage, data)
        if existing_broker_execution == "replay":
            self.broker_execution_replay_duplicate_count += 1
            return
        if existing_broker_execution == "conflict":
            self.broker_execution_conflict_count += 1
            self._invalid("broker_execution_identity_content_conflict")
            return
        stage_error = self._stage_contract_error(row)
        if stage_error is not None:
            self._invalid(stage_error)
            return
        try:
            timestamp = _aware_datetime(row.get("observed_at"))
        except (TypeError, ValueError):
            self._invalid("transition_timestamp_invalid")
            return
        if self.last_observed_at is not None and timestamp < self.last_observed_at:
            self._invalid("lifecycle_timestamp_regression")
            return
        submission_state = self._observe_order_submission(
            stage,
            data,
            observed_at=timestamp,
        )
        if submission_state == "replay":
            return
        if submission_state == "conflict":
            self.broker_execution_submission_link_conflict_count += 1
            self._invalid("broker_submission_identity_or_quantity_conflict")
            return
        broker_execution_state = self._observe_broker_execution(
            stage,
            data,
            observed_at=timestamp,
        )
        if broker_execution_state == "replay":
            return
        if broker_execution_state == "conflict":
            self._invalid("broker_execution_identity_content_conflict")
            return
        if broker_execution_state == "order_progress_conflict":
            self._invalid("broker_execution_order_progress_conflict")
            return
        if broker_execution_state == "submission_conflict":
            self._invalid("broker_execution_submission_link_conflict")
            return
        if not self._integrate_capital(timestamp):
            return
        self._retain_event_identity(row)

        self.transition_count += 1
        self.first_observed_at = self.first_observed_at or timestamp
        self.last_observed_at = timestamp
        self.stage_counts[stage] = self.stage_counts.get(stage, 0) + 1

        if data.get("market_observation_expected") is not False:
            self.market_observation_expected_count += 1
            if data.get("bbo_observed") is True:
                self.bbo_observed_count += 1
            if data.get("depth_observed") is True:
                self.depth_observed_count += 1
        self._observe_trace_id(data.get("decision_trace_id"))
        self._observe_interval(data)
        self._observe_hashes(data)
        self._observe_economics(stage, data)
        if data.get("actual_broker_order_submitted") is True:
            self.observed_actual_broker_order_submitted = True

        requested_qty = _finite_number(data.get("requested_qty"), positive=True)
        if "requested_qty" in data and requested_qty is None:
            self._invalid("requested_qty_invalid")
        if requested_qty is not None:
            self.requested_qty_max = max(self.requested_qty_max or 0.0, requested_qty)

        if stage == "scanner":
            if self.scanner_first_at is None:
                self.scanner_first_at = timestamp
                self.scanner_last_at = timestamp
                self.scanner_sample_count = 1
            elif data.get("heartbeat") is True:
                self.scanner_last_at = timestamp
                self.scanner_sample_count += 1
        elif data.get("heartbeat") is True:
            if self.scanner_first_at is None:
                self.scanner_first_at = timestamp
            self.scanner_last_at = timestamp
            self.scanner_sample_count += 1

        if data.get("terminal_no_fill") is True:
            if self.first_fill_at is not None:
                self._invalid("terminal_no_fill_after_fill")
            self.terminal_no_fill_at = timestamp
            self.terminal_no_fill_reason = str(data.get("terminal_reason") or "unknown")

        if stage == "fill":
            if self.terminal_no_fill_at is not None:
                self._invalid("fill_after_terminal_no_fill")
            fill_state = str(data.get("fill_state"))
            if fill_state == "partial":
                self.partial_fill_event_count += 1
            elif fill_state == "full":
                self.full_fill_event_count += 1
            quantity = _finite_number(data.get("fill_qty"), positive=True)
            price = _finite_number(data.get("fill_price"), positive=True)
            if quantity is not None and price is not None:
                self.first_fill_at = self.first_fill_at or timestamp
                self._add_fill(quantity=quantity, price=price, scale_in=False)
                if broker_execution_state == "new":
                    self.broker_execution_entry_covered_qty += quantity

        if stage == "scale_in":
            decision = str(data.get("scale_in_decision") or "")
            if decision and decision not in self.scale_in_decisions:
                self.scale_in_decisions.append(decision)
            if decision == "ADD":
                quantity = _finite_number(data.get("fill_qty"), positive=True)
                price = _finite_number(data.get("fill_price"), positive=True)
                if quantity is not None and price is not None:
                    if self.first_fill_at is None:
                        self._invalid("scale_in_add_before_entry_fill")
                    else:
                        self._add_fill(quantity=quantity, price=price, scale_in=True)
                        if broker_execution_state == "new":
                            self.broker_execution_entry_covered_qty += quantity

        if stage == "exit":
            quantity = _finite_number(data.get("exit_qty"), positive=True)
            price = _finite_number(data.get("exit_price"), positive=True)
            if "exit_qty" in data and quantity is None:
                self._invalid("exit_qty_invalid")
            if "exit_price" in data and price is None:
                self._invalid("exit_price_invalid")
            if (quantity is None) != (price is None):
                self._invalid("exit_price_qty_pair_incomplete")
            if quantity is not None and price is not None:
                open_qty_before = self.open_qty
                self._apply_exit(quantity, price)
                if self.open_qty < open_qty_before:
                    if broker_execution_state == "new":
                        self.broker_execution_exit_covered_qty += quantity
                    basis_price = _finite_number(
                        data.get("slippage_basis_price"), positive=True
                    )
                    if basis_price is not None:
                        self.slippage_basis_covered_qty += quantity
                        self.slippage_basis_amount_krw += quantity * basis_price
                        basis_source = str(
                            data.get("slippage_basis_source") or ""
                        ).strip()
                        if basis_source:
                            self.slippage_basis_source_covered_qty += quantity
                            if basis_source not in self.slippage_basis_sources:
                                self.slippage_basis_sources.append(basis_source)
                    for field_name in (
                        "fees_taxes_krw",
                        "slippage_krw",
                        "realized_net_pnl_krw",
                    ):
                        value = _finite_number(
                            data.get(field_name),
                            nonnegative=field_name
                            in {"fees_taxes_krw", "slippage_krw"},
                        )
                        if value is not None:
                            self.economics_covered_exit_qty[field_name] = (
                                self.economics_covered_exit_qty.get(field_name, 0.0)
                                + quantity
                            )
            if data.get("reconciled_final_exit") is True:
                self.final_exit_at = timestamp
                self.final_exit_reconciled = data.get("broker_reconciled") is True
                if self.first_fill_at is None:
                    self._invalid("final_exit_without_fill")
                if self.open_qty > _QUANTITY_EPSILON:
                    self._invalid("final_exit_leaves_open_quantity")

    def _explicit_session_exposure_sec(self) -> float | None:
        total = self.explicit_exposure_total_sec
        if (
            self.explicit_exposure_current_start is not None
            and self.explicit_exposure_current_end is not None
        ):
            total += (
                self.explicit_exposure_current_end
                - self.explicit_exposure_current_start
            ).total_seconds()
        return total if self.explicit_exposure_interval_count > 0 else None

    def _session_exposure_sec(self) -> float | None:
        explicit = self._explicit_session_exposure_sec()
        if explicit is not None:
            return explicit
        if (
            self.scanner_sample_count >= 2
            and self.scanner_first_at is not None
            and self.scanner_last_at is not None
        ):
            elapsed = (self.scanner_last_at - self.scanner_first_at).total_seconds()
            return elapsed if elapsed >= 0 else None
        return None

    def _fill_completion_class(self) -> str:
        if self.partial_fill_event_count and self.full_fill_event_count:
            return "partial_then_full"
        if self.partial_fill_event_count:
            return "partial_only"
        if self.full_fill_event_count:
            return "full_only"
        return "no_fill"

    def _terminal_state(self) -> tuple[str, bool]:
        if self.terminal_no_fill_at is not None and self.first_fill_at is None:
            return "TERMINAL_NO_FILL", False
        if (
            self.final_exit_at is not None
            and self.final_exit_reconciled
            and self.open_qty <= _QUANTITY_EPSILON
        ):
            return "FINAL_EXIT_RECONCILED", False
        if self.first_fill_at is not None:
            return "HELD", True
        return "INCOMPLETE", False

    def finalize(self) -> dict[str, Any]:
        terminal_state, right_censored = self._terminal_state()
        actual_duration: float | None = None
        if self.first_fill_at is not None and self.final_exit_at is not None:
            duration = (self.final_exit_at - self.first_fill_at).total_seconds()
            if duration < 0:
                self._invalid("final_exit_precedes_first_fill")
            else:
                actual_duration = duration

        bbo_coverage = (
            100.0 * self.bbo_observed_count / self.market_observation_expected_count
            if self.market_observation_expected_count
            else None
        )
        depth_coverage = (
            100.0 * self.depth_observed_count / self.market_observation_expected_count
            if self.market_observation_expected_count
            else None
        )
        session_exposure = self._session_exposure_sec()
        lifecycle_rate = (
            3600.0 / session_exposure
            if session_exposure is not None and session_exposure > 0
            else None
        )
        reviewed_cost_hash = (
            None if self.cost_hash_conflict else self.reviewed_cost_profile_sha256
        )
        symbol_master_hash = (
            None if self.symbol_hash_conflict else self.symbol_master_artifact_sha256
        )

        blockers: list[str] = []
        missing_stages = sorted(_REQUIRED_COMPLETE_STAGES - self.stage_counts.keys())
        if missing_stages:
            blockers.append("missing_required_stages:" + ",".join(missing_stages))
        if terminal_state != "FINAL_EXIT_RECONCILED":
            blockers.append("reconciled_final_exit_required")
        if actual_duration is None:
            blockers.append("actual_first_fill_to_final_exit_duration_required")
        if session_exposure is None:
            blockers.append("session_exposure_requires_interval_or_two_samples")
        if not self.scale_in_decisions:
            blockers.append("scale_in_decision_missing")
        if not self.observed_actual_broker_order_submitted:
            blockers.append("actual_broker_order_submission_required")
        if bbo_coverage is None or bbo_coverage < 95.0:
            blockers.append("bbo_coverage_below_95pct")
        if depth_coverage is None or depth_coverage < 90.0:
            blockers.append("depth_coverage_below_90pct")
        if reviewed_cost_hash is None or not (
            self.cost_verified_seen and self.cost_verified_all
        ):
            blockers.append("reviewed_cost_profile_required")
        if symbol_master_hash is None or not (
            self.symbol_verified_seen and self.symbol_verified_all
        ):
            blockers.append("verified_symbol_master_required")
        missing_economics = {
            "fees_taxes_krw",
            "slippage_krw",
            "realized_net_pnl_krw",
        } - self.economics_fields_seen
        if missing_economics:
            blockers.append(
                "realized_economics_fields_missing:"
                + ",".join(sorted(missing_economics))
            )
        for field_name in (
            "fees_taxes_krw",
            "slippage_krw",
            "realized_net_pnl_krw",
        ):
            if (
                self.exit_qty > _QUANTITY_EPSILON
                and self.economics_covered_exit_qty.get(field_name, 0.0)
                + _QUANTITY_EPSILON
                < self.exit_qty
            ):
                blockers.append(f"{field_name}_exit_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.slippage_basis_covered_qty + _QUANTITY_EPSILON < self.exit_qty
        ):
            blockers.append("slippage_basis_exit_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.slippage_basis_source_covered_qty + _QUANTITY_EPSILON
            < self.exit_qty
        ):
            blockers.append("slippage_basis_source_exit_qty_coverage_incomplete")
        total_entry_execution_qty = self.entry_fill_qty + self.scale_in_fill_qty
        unreconciled_broker_order_count = sum(
            1
            for _, _, _, remaining_qty, _ in self.broker_order_progress_by_no.values()
            if remaining_qty > 0
        )
        submitted_order_coverage_gap_phases: list[str] = []
        submitted_order_qty_mismatch_phases: list[str] = []
        for phase, submitted_qty in sorted(
            self.submitted_requested_qty_by_phase.items()
        ):
            submitted_order_nos = {
                order_no
                for order_no, submitted_phase in self.submitted_order_phase_by_no.items()
                if submitted_phase == phase
            }
            executed_order_qty = self.executed_order_qty_by_phase.get(phase, {})
            if submitted_order_nos != set(executed_order_qty):
                submitted_order_coverage_gap_phases.append(phase)
            if sum(executed_order_qty.values()) != submitted_qty:
                submitted_order_qty_mismatch_phases.append(phase)
        if self.broker_execution_provenance_gap_count:
            blockers.append("broker_execution_raw_provenance_gap")
        if self.broker_execution_conflict_count:
            blockers.append("broker_execution_identity_content_conflict")
        if self.broker_execution_order_progress_conflict_count:
            blockers.append("broker_execution_order_progress_conflict")
        if self.broker_execution_submission_link_conflict_count:
            blockers.append("broker_execution_submission_link_conflict")
        if self.broker_order_no_cross_lifecycle_conflict_count:
            blockers.append("broker_order_no_cross_lifecycle_conflict")
        if self.broker_execution_cross_lifecycle_identity_conflict_count:
            blockers.append("broker_execution_identity_cross_lifecycle_conflict")
        if submitted_order_coverage_gap_phases:
            blockers.append(
                "broker_execution_submitted_order_coverage_incomplete:"
                + ",".join(submitted_order_coverage_gap_phases)
            )
        if submitted_order_qty_mismatch_phases:
            blockers.append(
                "broker_execution_submitted_qty_mismatch:"
                + ",".join(submitted_order_qty_mismatch_phases)
            )
        if unreconciled_broker_order_count:
            blockers.append("broker_execution_order_remaining_unreconciled")
        if (
            total_entry_execution_qty > _QUANTITY_EPSILON
            and self.broker_execution_entry_covered_qty + _QUANTITY_EPSILON
            < total_entry_execution_qty
        ):
            blockers.append("broker_execution_entry_qty_coverage_incomplete")
        if (
            self.exit_qty > _QUANTITY_EPSILON
            and self.broker_execution_exit_covered_qty + _QUANTITY_EPSILON
            < self.exit_qty
        ):
            blockers.append("broker_execution_exit_qty_coverage_incomplete")
        if self.invalid_transition_count:
            blockers.append("invalid_transition_present")

        row = {
            "main_lifecycle_id": self.main_lifecycle_id,
            "record_id": self.record_id,
            "stock_code": self.stock_code,
            "attempt_id": self.attempt_id,
            "trade_date": self.trade_date,
            "venue": self.venue,
            "session_bucket": self.session_bucket,
            "decision_trace_ids": self.decision_trace_ids,
            "transition_count": self.transition_count,
            "stage_counts": dict(sorted(self.stage_counts.items())),
            "terminal_state": terminal_state,
            "right_censored": right_censored,
            "terminal_no_fill_reason": self.terminal_no_fill_reason,
            "first_fill_at": (
                self.first_fill_at.isoformat() if self.first_fill_at else None
            ),
            "final_exit_at": (
                self.final_exit_at.isoformat() if self.final_exit_at else None
            ),
            "actual_holding_duration_sec": actual_duration,
            "duration_source": "actual_first_fill_to_reconciled_final_exit",
            "label_horizon_used": False,
            "session_exposure_sec": session_exposure,
            "lifecycle_rate_per_exposure_hour": lifecycle_rate,
            "capital_time_krw_hours": self.capital_time_krw_seconds / 3600.0,
            "requested_qty_max": self.requested_qty_max,
            "entry_fill_qty": self.entry_fill_qty,
            "scale_in_fill_qty": self.scale_in_fill_qty,
            "exit_qty": self.exit_qty,
            "exit_execution_leg_count": self.exit_execution_leg_count,
            "exit_vwap_price": (
                self.exit_amount_krw / self.exit_qty
                if self.exit_qty > _QUANTITY_EPSILON
                else None
            ),
            "slippage_basis_covered_qty": self.slippage_basis_covered_qty,
            "slippage_basis_source_covered_qty": (
                self.slippage_basis_source_covered_qty
            ),
            "slippage_basis_sources": self.slippage_basis_sources,
            "slippage_basis_vwap_price": (
                self.slippage_basis_amount_krw / self.slippage_basis_covered_qty
                if self.slippage_basis_covered_qty > _QUANTITY_EPSILON
                else None
            ),
            "economics_covered_exit_qty": dict(
                sorted(self.economics_covered_exit_qty.items())
            ),
            "open_qty_at_censor": self.open_qty,
            "partial_fill_event_count": self.partial_fill_event_count,
            "full_fill_event_count": self.full_fill_event_count,
            "fill_completion_class": self._fill_completion_class(),
            "broker_execution_official_reference_sha": (KIWOOM_OFFICIAL_REFERENCE_SHA),
            "broker_execution_provenance_schema": (BROKER_EXECUTION_PROVENANCE_SCHEMA),
            "broker_execution_raw_envelope_schema": (
                BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA
            ),
            "broker_execution_unique_count": self.broker_execution_unique_count,
            "broker_execution_replay_duplicate_count": (
                self.broker_execution_replay_duplicate_count
            ),
            "broker_execution_conflict_count": (self.broker_execution_conflict_count),
            "broker_execution_order_progress_conflict_count": (
                self.broker_execution_order_progress_conflict_count
            ),
            "broker_execution_submission_link_conflict_count": (
                self.broker_execution_submission_link_conflict_count
            ),
            "broker_order_no_cross_lifecycle_conflict_count": (
                self.broker_order_no_cross_lifecycle_conflict_count
            ),
            "broker_execution_cross_lifecycle_identity_conflict_count": (
                self.broker_execution_cross_lifecycle_identity_conflict_count
            ),
            "broker_submission_replay_duplicate_count": (
                self.broker_submission_replay_duplicate_count
            ),
            "broker_submitted_order_count": len(self.submitted_order_phase_by_no),
            "broker_submitted_requested_qty_by_phase": dict(
                sorted(self.submitted_requested_qty_by_phase.items())
            ),
            "broker_submitted_requested_qty_by_order_no": dict(
                sorted(self.submitted_requested_qty_by_order_no.items())
            ),
            "broker_executed_order_qty_by_phase": {
                phase: dict(sorted(order_qty.items()))
                for phase, order_qty in sorted(self.executed_order_qty_by_phase.items())
            },
            "broker_submitted_order_coverage_gap_phases": (
                submitted_order_coverage_gap_phases
            ),
            "broker_submitted_order_qty_mismatch_phases": (
                submitted_order_qty_mismatch_phases
            ),
            "broker_execution_provenance_state_counts": dict(
                sorted(self.broker_execution_provenance_state_counts.items())
            ),
            "broker_execution_provenance_gap_count": (
                self.broker_execution_provenance_gap_count
            ),
            "broker_execution_provenance_gap_reasons": (
                self.broker_execution_provenance_gap_reasons
            ),
            "broker_execution_entry_covered_qty": (
                self.broker_execution_entry_covered_qty
            ),
            "broker_execution_exit_covered_qty": (
                self.broker_execution_exit_covered_qty
            ),
            "broker_execution_partial_count": (self.broker_execution_partial_count),
            "broker_execution_full_count": self.broker_execution_full_count,
            "broker_execution_unreconciled_order_count": (
                unreconciled_broker_order_count
            ),
            "transition_replay_duplicate_count": (
                self.transition_replay_duplicate_count
            ),
            "scale_in_decisions": self.scale_in_decisions,
            "scale_in_contract_state": (
                "explicit" if self.scale_in_decisions else "missing"
            ),
            "market_observation_expected_count": (
                self.market_observation_expected_count
            ),
            "bbo_observed_count": self.bbo_observed_count,
            "depth_observed_count": self.depth_observed_count,
            "bbo_coverage_pct": bbo_coverage,
            "depth_coverage_pct": depth_coverage,
            "fees_taxes_krw": self.fees_taxes_krw,
            "slippage_krw": self.slippage_krw,
            "realized_net_pnl_krw": self.realized_net_pnl_krw,
            "observed_actual_broker_order_submitted": (
                self.observed_actual_broker_order_submitted
            ),
            "reviewed_cost_profile_sha256": reviewed_cost_hash,
            "reviewed_cost_profile_verified": (
                self.cost_verified_seen and self.cost_verified_all
            ),
            "symbol_master_artifact_sha256": symbol_master_hash,
            "symbol_master_artifact_verified": (
                self.symbol_verified_seen and self.symbol_verified_all
            ),
            "invalid_transition_count": self.invalid_transition_count,
            "invalid_transition_reasons": self.invalid_reasons,
            "decision_trace_id_overflow_count": self.trace_ids_overflow_count,
            "row_source_quality_gate_pass": not blockers,
            "promotion_evidence_eligible": not blockers,
            "promotion_blockers": blockers,
            **REPORT_AUTHORITY_CONTRACT,
        }
        return row


def _bounded_gap(
    examples: list[dict[str, Any]], *, reason: str, source: str, line_number: int
) -> None:
    if len(examples) >= _GAP_EXAMPLE_LIMIT:
        return
    examples.append(
        {
            "reason": reason,
            "source": source,
            "line_number": line_number,
        }
    )


def _pipeline_owner_scoped_identity_gap(
    raw_row: Mapping[str, Any], *, target_date: str, reason: str | None
) -> tuple[str, str] | None:
    """Return the exact owner window for an isolatable pre-identity row.

    This deliberately does not reconstruct a lifecycle attempt.  A legacy
    mapped row can be quarantined only when the raw pipeline event itself
    carries an exact DB record id, six-digit stock code, and target date.  All
    attempts for that owner are excluded; unrelated owner windows remain
    eligible.  Every other validation failure stays a global source gap.
    """

    if reason != "pipeline_lifecycle_identity_missing":
        return None
    if str(raw_row.get("emitted_date") or "").strip() != target_date:
        return None
    record_id = str(raw_row.get("record_id") or "").strip()
    stock_code = str(raw_row.get("stock_code") or "").strip()
    if (
        not record_id
        or len(record_id) > 160
        or any(char in record_id for char in "\r\n\x00")
        or not re.fullmatch(r"[0-9]{6}", stock_code)
    ):
        return None
    return record_id, stock_code


def _lifecycle_window_exclusion_taxonomies(
    reason_codes: Sequence[str],
) -> list[str]:
    """Classify row-local blockers without granting promotion authority."""

    taxonomies: set[str] = set()
    for reason in reason_codes:
        if reason in {
            "broker_order_no_cross_lifecycle_conflict",
            "broker_execution_identity_cross_lifecycle_conflict",
        }:
            taxonomies.add("cross_lifecycle_identity_conflict")
        elif reason.startswith("broker_execution_") or reason == (
            "actual_broker_order_submission_required"
        ):
            taxonomies.add("broker_execution_provenance_or_custody_gap")
        elif reason.startswith(("bbo_", "depth_", "session_exposure_")):
            taxonomies.add("market_observation_coverage_gap")
        elif reason.startswith(("reviewed_cost_", "verified_symbol_")):
            taxonomies.add("economic_reference_gap")
        elif reason.startswith(
            (
                "realized_economics_",
                "fees_taxes_",
                "slippage_",
                "realized_net_pnl_",
            )
        ):
            taxonomies.add("realized_economics_gap")
        else:
            taxonomies.add("lifecycle_completeness_or_consistency_gap")
    return sorted(taxonomies)


def _reference_hash_contract(
    value: str | None,
    *,
    verified: bool,
    field: str,
) -> tuple[str | None, bool, list[str]]:
    blockers: list[str] = []
    if not isinstance(verified, bool):
        blockers.append(f"{field}_verified_flag_invalid")
        verified = False
    normalized = str(value or "").strip() or None
    if normalized is not None and not SHA256_RE.fullmatch(normalized):
        blockers.append(f"{field}_invalid")
        normalized = None
    if verified and normalized is None:
        blockers.append(f"{field}_missing_for_verified_contract")
        verified = False
    return normalized, verified, blockers


def _scan_fallback_source(
    path: Path | None,
) -> tuple[dict[str, Any] | None, int, list[dict[str, Any]]]:
    if path is None:
        return None, 0, []
    rows, census = _stream_json_objects(path)
    missing_id_count = 0
    explicit_id_nonjoined_count = 0
    gaps: list[dict[str, Any]] = []
    for line_number, row in rows:
        lifecycle_id = str(row.get("main_lifecycle_id") or "").strip()
        if lifecycle_id:
            explicit_id_nonjoined_count += 1
            continue
        missing_id_count += 1
        _bounded_gap(
            gaps,
            reason="raw_fallback_missing_explicit_main_lifecycle_id",
            source=census.source_path,
            line_number=line_number,
        )
    result = census.as_dict()
    result.update(
        {
            "missing_main_lifecycle_id_count": missing_id_count,
            "explicit_main_lifecycle_id_nonjoined_count": (explicit_id_nonjoined_count),
            "join_policy": "never_join_raw_fallback",
            "promotion_evidence_eligible": False,
        }
    )
    parse_gap_count = census.malformed_json_count + census.non_object_count
    read_gap_count = int(census.source_read_error is not None)
    if parse_gap_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_parse_gap",
            source=census.source_path,
            line_number=0,
        )
    if read_gap_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_read_error",
            source=census.source_path,
            line_number=0,
        )
    missing_source_count = int(not census.source_exists)
    if missing_source_count:
        _bounded_gap(
            gaps,
            reason="raw_fallback_source_missing",
            source=census.source_path,
            line_number=0,
        )
    return (
        result,
        missing_id_count + parse_gap_count + read_gap_count + missing_source_count,
        gaps,
    )


def _apply_cross_lifecycle_broker_ownership_gate(
    accumulators: Mapping[str, _LifecycleAccumulator],
) -> tuple[int, int]:
    """Fail closed when one broker identity is claimed by two lifecycles."""

    order_owners: dict[str, list[_LifecycleAccumulator]] = {}
    execution_owners: dict[str, list[_LifecycleAccumulator]] = {}
    for accumulator in accumulators.values():
        for order_no in accumulator.submitted_order_phase_by_no:
            order_owners.setdefault(order_no, []).append(accumulator)
        for identity in accumulator.broker_execution_content_by_identity:
            execution_owners.setdefault(identity, []).append(accumulator)

    conflicting_orders = {
        order_no: owners
        for order_no, owners in order_owners.items()
        if len({owner.main_lifecycle_id for owner in owners}) > 1
    }
    conflicting_executions = {
        identity: owners
        for identity, owners in execution_owners.items()
        if len({owner.main_lifecycle_id for owner in owners}) > 1
    }
    for owners in conflicting_orders.values():
        for owner in owners:
            owner.broker_order_no_cross_lifecycle_conflict_count += 1
            owner._invalid("broker_order_no_cross_lifecycle_conflict")
    for owners in conflicting_executions.values():
        for owner in owners:
            owner.broker_execution_cross_lifecycle_identity_conflict_count += 1
            owner._invalid("broker_execution_identity_cross_lifecycle_conflict")
    return len(conflicting_orders), len(conflicting_executions)


def build_daily_report(
    target_date: str | date,
    *,
    source_path: Path | None = None,
    raw_fallback_path: Path | None = None,
    output_path: Path | None = None,
    reviewed_cost_profile_sha256: str | None = None,
    reviewed_cost_profile_verified: bool = False,
    symbol_master_artifact_sha256: str | None = None,
    symbol_master_artifact_verified: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Build one compact row per explicit lifecycle from one streaming scan."""

    target = (
        target_date.isoformat() if isinstance(target_date, date) else str(target_date)
    )
    target = date.fromisoformat(target).isoformat()
    logical_source = source_path or pipeline_event_path(target)
    streamed_rows, census = _stream_json_objects(logical_source)
    accumulators: dict[str, _LifecycleAccumulator] = {}
    source_invalid_transition_count = 0
    journal_transition_source_row_count = 0
    pipeline_event_source_row_count = 0
    pipeline_lifecycle_mapped_row_count = 0
    pipeline_lifecycle_accepted_row_count = 0
    pipeline_lifecycle_out_of_scope_row_count = 0
    pipeline_lifecycle_instrumentation_gap_count = 0
    pipeline_lifecycle_missing_identity_count = 0
    pipeline_lifecycle_owner_scoped_gap_count = 0
    pipeline_lifecycle_unscoped_gap_count = 0
    pipeline_owner_scoped_gaps: dict[tuple[str, str], dict[str, int]] = {}
    mixed_source_row_count = 0
    lifecycle_accumulator_overflow_row_count = 0
    transition_event_identity_overflow_row_count = 0
    retained_transition_event_identity_count = 0
    selected_source_mode: str | None = None
    gap_examples: list[dict[str, Any]] = []
    reviewed_cost_hash, reviewed_cost_verified, cost_reference_blockers = (
        _reference_hash_contract(
            reviewed_cost_profile_sha256,
            verified=reviewed_cost_profile_verified,
            field="reviewed_cost_profile_sha256",
        )
    )
    symbol_master_hash, symbol_master_verified, symbol_reference_blockers = (
        _reference_hash_contract(
            symbol_master_artifact_sha256,
            verified=symbol_master_artifact_verified,
            field="symbol_master_artifact_sha256",
        )
    )
    reference_contract_blockers = [
        *cost_reference_blockers,
        *symbol_reference_blockers,
    ]

    for line_number, raw_row in streamed_rows:
        if raw_row.get("schema") == JOURNAL_SCHEMA:
            journal_transition_source_row_count += 1
            row_source_mode = "transition_journal"
        elif raw_row.get("event_type") == "pipeline_event":
            pipeline_event_source_row_count += 1
            row_source_mode = "pipeline_events"
        else:
            row_source_mode = None

        if row_source_mode is not None:
            if selected_source_mode is None:
                selected_source_mode = row_source_mode
            elif selected_source_mode != row_source_mode:
                mixed_source_row_count += 1
                source_invalid_transition_count += 1
                _bounded_gap(
                    gap_examples,
                    reason="mixed_transition_source_kinds_forbidden",
                    source=census.source_path,
                    line_number=line_number,
                )
                continue

        if row_source_mode == "transition_journal":
            transition, reason = _validated_transition(raw_row, target_date=target)
        elif row_source_mode == "pipeline_events":
            transition, reason, lifecycle_in_scope = _validated_pipeline_transition(
                raw_row, target_date=target
            )
            if not lifecycle_in_scope:
                pipeline_lifecycle_out_of_scope_row_count += 1
                continue
            pipeline_lifecycle_mapped_row_count += 1
            if transition is not None:
                pipeline_lifecycle_accepted_row_count += 1
            else:
                pipeline_lifecycle_instrumentation_gap_count += 1
                if reason == "pipeline_lifecycle_identity_missing":
                    pipeline_lifecycle_missing_identity_count += 1
        else:
            transition, reason = _validated_transition(raw_row, target_date=target)
        if transition is None:
            scoped_owner = (
                _pipeline_owner_scoped_identity_gap(
                    raw_row,
                    target_date=target,
                    reason=reason,
                )
                if row_source_mode == "pipeline_events"
                else None
            )
            if scoped_owner is not None:
                pipeline_lifecycle_owner_scoped_gap_count += 1
                owner_reasons = pipeline_owner_scoped_gaps.setdefault(scoped_owner, {})
                reason_key = reason or "transition_invalid"
                owner_reasons[reason_key] = owner_reasons.get(reason_key, 0) + 1
            else:
                source_invalid_transition_count += 1
                if row_source_mode == "pipeline_events":
                    pipeline_lifecycle_unscoped_gap_count += 1
            _bounded_gap(
                gap_examples,
                reason=reason or "transition_invalid",
                source=census.source_path,
                line_number=line_number,
            )
            continue
        lifecycle_id = str(transition["main_lifecycle_id"])
        accumulator = accumulators.get(lifecycle_id)
        if accumulator is None:
            if len(accumulators) >= MAX_LIFECYCLE_ACCUMULATORS:
                lifecycle_accumulator_overflow_row_count += 1
                _bounded_gap(
                    gap_examples,
                    reason="lifecycle_accumulator_limit_exceeded",
                    source=census.source_path,
                    line_number=line_number,
                )
                continue
            accumulator = _LifecycleAccumulator.from_transition(transition)
            accumulator.bind_reference_contract(
                reviewed_cost_profile_sha256=reviewed_cost_hash,
                reviewed_cost_profile_verified=reviewed_cost_verified,
                symbol_master_artifact_sha256=symbol_master_hash,
                symbol_master_artifact_verified=symbol_master_verified,
            )
            accumulators[lifecycle_id] = accumulator
        event_id = str(transition.get("event_id") or "").strip()
        is_new_event_identity = event_id not in accumulator.event_content_by_id
        if (
            is_new_event_identity
            and retained_transition_event_identity_count
            >= MAX_TRANSITION_EVENT_IDENTITIES
        ):
            transition_event_identity_overflow_row_count += 1
            accumulator._invalid("global_transition_event_identity_limit_exceeded")
            _bounded_gap(
                gap_examples,
                reason="global_transition_event_identity_limit_exceeded",
                source=census.source_path,
                line_number=line_number,
            )
            continue
        retained_before = len(accumulator.event_content_by_id)
        accumulator.consume(transition)
        retained_transition_event_identity_count += max(
            0, len(accumulator.event_content_by_id) - retained_before
        )

    (
        broker_order_no_cross_lifecycle_conflict_count,
        broker_execution_cross_lifecycle_identity_conflict_count,
    ) = _apply_cross_lifecycle_broker_ownership_gate(accumulators)
    if broker_order_no_cross_lifecycle_conflict_count:
        _bounded_gap(
            gap_examples,
            reason="broker_order_no_cross_lifecycle_conflict",
            source=census.source_path,
            line_number=0,
        )
    if broker_execution_cross_lifecycle_identity_conflict_count:
        _bounded_gap(
            gap_examples,
            reason="broker_execution_identity_cross_lifecycle_conflict",
            source=census.source_path,
            line_number=0,
        )

    fallback_census, fallback_gap_count, fallback_gaps = _scan_fallback_source(
        raw_fallback_path
    )
    if census.malformed_json_count or census.non_object_count:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_parse_gap",
            source=census.source_path,
            line_number=0,
        )
    if census.source_read_error is not None:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_read_error",
            source=census.source_path,
            line_number=0,
        )
    if not census.source_exists:
        _bounded_gap(
            gap_examples,
            reason="transition_journal_missing",
            source=census.source_path,
            line_number=0,
        )
    gap_examples.extend(fallback_gaps[: max(0, _GAP_EXAMPLE_LIMIT - len(gap_examples))])
    rows = [
        accumulators[lifecycle_id].finalize() for lifecycle_id in sorted(accumulators)
    ]
    pipeline_owner_excluded_lifecycle_count = 0
    for row in rows:
        owner = (str(row["record_id"]), str(row["stock_code"]))
        if owner not in pipeline_owner_scoped_gaps:
            continue
        pipeline_owner_excluded_lifecycle_count += 1
        blocker = "pipeline_owner_window_missing_explicit_lifecycle_identity"
        if blocker not in row["promotion_blockers"]:
            row["promotion_blockers"].append(blocker)
        row["row_source_quality_gate_pass"] = False
        row["promotion_evidence_eligible"] = False

    pipeline_owner_reason_counts: dict[str, int] = {}
    pipeline_owner_entries: list[dict[str, Any]] = []
    for (record_id, stock_code), reason_counts in sorted(
        pipeline_owner_scoped_gaps.items()
    ):
        for reason, count in reason_counts.items():
            pipeline_owner_reason_counts[reason] = (
                pipeline_owner_reason_counts.get(reason, 0) + count
            )
        owner_payload = {
            "target_date": target,
            "record_id": record_id,
            "stock_code": stock_code,
        }
        pipeline_owner_entries.append(
            {
                **owner_payload,
                "owner_key_sha256": _sha256(owner_payload),
                "gap_count": sum(reason_counts.values()),
                "reason_code_counts": dict(sorted(reason_counts.items())),
            }
        )
    pipeline_owner_exclusion_manifest = {
        "schema": PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA,
        **PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT,
        "target_date": target,
        "excluded_owner_count": len(pipeline_owner_entries),
        "excluded_lifecycle_count": pipeline_owner_excluded_lifecycle_count,
        "gap_count": pipeline_lifecycle_owner_scoped_gap_count,
        "reason_code_counts": dict(sorted(pipeline_owner_reason_counts.items())),
        "entries": pipeline_owner_entries,
    }
    lifecycle_window_exclusion_entries: list[dict[str, Any]] = []
    lifecycle_window_exclusion_reason_counts: dict[str, int] = {}
    lifecycle_window_exclusion_taxonomy_counts: dict[str, int] = {}
    locally_excluded_lifecycle_ids: set[str] = set()
    for row in rows:
        reason_codes = [
            str(reason)
            for reason in row.get("promotion_blockers", [])
            if str(reason).strip()
        ]
        if not reason_codes:
            row["lifecycle_window_source_quality_disposition"] = (
                "eligible_before_global_source_contract_gate"
            )
            row["lifecycle_window_exclusion_taxonomies"] = []
            continue
        taxonomies = _lifecycle_window_exclusion_taxonomies(reason_codes)
        row["lifecycle_window_source_quality_disposition"] = (
            "excluded_exact_lifecycle_window"
        )
        row["lifecycle_window_exclusion_taxonomies"] = taxonomies
        locally_excluded_lifecycle_ids.add(str(row["main_lifecycle_id"]))
        for reason in reason_codes:
            lifecycle_window_exclusion_reason_counts[reason] = (
                lifecycle_window_exclusion_reason_counts.get(reason, 0) + 1
            )
        for taxonomy in taxonomies:
            lifecycle_window_exclusion_taxonomy_counts[taxonomy] = (
                lifecycle_window_exclusion_taxonomy_counts.get(taxonomy, 0) + 1
            )
        lifecycle_window_exclusion_entries.append(
            {
                "main_lifecycle_id": row["main_lifecycle_id"],
                "exclusion_scope": "exact_main_lifecycle_window",
                "taxonomies": taxonomies,
                "reason_codes_sha256": _sha256(reason_codes),
            }
        )
    lifecycle_window_exclusion_manifest = {
        "schema": LIFECYCLE_WINDOW_EXCLUSION_MANIFEST_SCHEMA,
        "metric_role": "source_quality_gate",
        "decision_authority": "exact_lifecycle_window_exclusion_only",
        "window_policy": "exact_trade_date_and_main_lifecycle_id",
        "sample_floor": "not_applicable_source_quality_manifest",
        "primary_decision_metric": "excluded_lifecycle_count",
        "source_quality_gate": "row_local_promotion_blocker_taxonomy",
        "evaluation_phase": "before_global_source_contract_gate",
        "exclusion_scope": "exact_main_lifecycle_window",
        "excluded_lifecycle_count": len(lifecycle_window_exclusion_entries),
        "eligible_lifecycle_count": (
            len(rows) - len(lifecycle_window_exclusion_entries)
        ),
        "taxonomy_counts": dict(
            sorted(lifecycle_window_exclusion_taxonomy_counts.items())
        ),
        "reason_code_counts": dict(
            sorted(lifecycle_window_exclusion_reason_counts.items())
        ),
        "entries": lifecycle_window_exclusion_entries,
        "runtime_effect": False,
        "runtime_authority": False,
        "order_authority": False,
        "provider_authority": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "direct_runtime_or_order_apply",
            "provider_model_bot_threshold_price_quantity_or_cap_change",
            "exclude_other_clean_lifecycle_windows",
        ],
    }
    reference_binding_mode = (
        "postclose_explicit"
        if reviewed_cost_hash is not None or symbol_master_hash is not None
        else "missing"
    )
    if reviewed_cost_hash is None:
        observed_cost_hashes = {
            str(row["reviewed_cost_profile_sha256"])
            for row in rows
            if row["reviewed_cost_profile_sha256"] is not None
        }
        if len(observed_cost_hashes) == 1:
            reviewed_cost_hash = next(iter(observed_cost_hashes))
            reviewed_cost_verified = bool(rows) and all(
                row["reviewed_cost_profile_sha256"] == reviewed_cost_hash
                and row["reviewed_cost_profile_verified"] is True
                for row in rows
            )
            reference_binding_mode = "transition_consensus"
        elif len(observed_cost_hashes) > 1:
            reference_contract_blockers.append(
                "reviewed_cost_profile_hash_conflict_across_lifecycles"
            )
    if symbol_master_hash is None:
        observed_symbol_hashes = {
            str(row["symbol_master_artifact_sha256"])
            for row in rows
            if row["symbol_master_artifact_sha256"] is not None
        }
        if len(observed_symbol_hashes) == 1:
            symbol_master_hash = next(iter(observed_symbol_hashes))
            symbol_master_verified = bool(rows) and all(
                row["symbol_master_artifact_sha256"] == symbol_master_hash
                and row["symbol_master_artifact_verified"] is True
                for row in rows
            )
            if reference_binding_mode == "missing":
                reference_binding_mode = "transition_consensus"
        elif len(observed_symbol_hashes) > 1:
            reference_contract_blockers.append(
                "symbol_master_artifact_hash_conflict_across_lifecycles"
            )
    lifecycle_invalid_transition_count = sum(
        int(row["invalid_transition_count"]) for row in rows
    )
    broker_execution_provenance_gap_count = sum(
        int(row["broker_execution_provenance_gap_count"]) for row in rows
    )
    broker_execution_conflict_count = sum(
        int(row["broker_execution_conflict_count"]) for row in rows
    )
    broker_execution_order_progress_conflict_count = sum(
        int(row["broker_execution_order_progress_conflict_count"]) for row in rows
    )
    broker_execution_submission_link_conflict_count = sum(
        int(row["broker_execution_submission_link_conflict_count"]) for row in rows
    )
    broker_execution_replay_duplicate_count = sum(
        int(row["broker_execution_replay_duplicate_count"]) for row in rows
    )
    broker_execution_unique_count = sum(
        int(row["broker_execution_unique_count"]) for row in rows
    )
    candidate_row_gate_failure_count = sum(
        1
        for row in rows
        if row["terminal_state"] == "FINAL_EXIT_RECONCILED"
        and row["promotion_evidence_eligible"] is not True
    )
    pipeline_owner_scoped_gap_high_volume = (
        pipeline_lifecycle_owner_scoped_gap_count
        >= PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        and pipeline_lifecycle_owner_scoped_gap_count
        > pipeline_lifecycle_accepted_row_count
    )
    global_gate_blockers: list[str] = []
    if not census.source_exists:
        global_gate_blockers.append("transition_journal_missing")
    global_gate_blockers.extend(reference_contract_blockers)
    if census.malformed_json_count or census.non_object_count:
        global_gate_blockers.append("transition_journal_parse_gap")
    if census.source_read_error is not None:
        global_gate_blockers.append("transition_journal_read_error")
    if source_invalid_transition_count:
        global_gate_blockers.append("invalid_or_cross_attempt_transition_present")
    if mixed_source_row_count:
        global_gate_blockers.append("mixed_transition_source_kinds_forbidden")
    if lifecycle_accumulator_overflow_row_count:
        global_gate_blockers.append("lifecycle_accumulator_limit_exceeded")
    if transition_event_identity_overflow_row_count:
        global_gate_blockers.append("global_transition_event_identity_limit_exceeded")
    if pipeline_lifecycle_unscoped_gap_count:
        global_gate_blockers.append("pipeline_lifecycle_instrumentation_gap")
    if pipeline_owner_scoped_gap_high_volume:
        global_gate_blockers.append("pipeline_owner_scoped_gap_high_volume")
    # Row-local lifecycle, broker-provenance, execution-progress, and candidate
    # gate failures are already bound to an exact main_lifecycle_id in the
    # exclusion manifest above.  They must not quarantine unrelated clean
    # lifecycle windows.  Unbound source failures and cross-lifecycle identity
    # conflicts remain global below.
    if broker_order_no_cross_lifecycle_conflict_count:
        global_gate_blockers.append("broker_order_no_cross_lifecycle_conflict")
    if broker_execution_cross_lifecycle_identity_conflict_count:
        global_gate_blockers.append(
            "broker_execution_identity_cross_lifecycle_conflict"
        )
    if fallback_gap_count:
        global_gate_blockers.append("raw_fallback_instrumentation_gap")
    if raw_fallback_path is not None and not bool(
        (fallback_census or {}).get("source_exists")
    ):
        global_gate_blockers.append("raw_fallback_source_missing")
    if not rows:
        global_gate_blockers.append("no_explicit_lifecycle_rows")

    if global_gate_blockers:
        for row in rows:
            if row["promotion_evidence_eligible"]:
                row["promotion_evidence_eligible"] = False
                row["promotion_blockers"] = [
                    *row["promotion_blockers"],
                    "daily_source_quality_gate_failed",
                ]

    for row in rows:
        if row["promotion_evidence_eligible"] is True:
            row["promotion_disposition"] = "eligible_source_only"
        elif str(row["main_lifecycle_id"]) in locally_excluded_lifecycle_ids:
            row["promotion_disposition"] = "excluded_exact_lifecycle_window"
        else:
            row["promotion_disposition"] = "global_source_contract_blocked"

    eligible_count = sum(
        1 for row in rows if row["promotion_evidence_eligible"] is True
    )
    terminal_state_counts: dict[str, int] = {}
    fill_completion_counts: dict[str, int] = {}
    for row in rows:
        terminal = str(row["terminal_state"])
        terminal_state_counts[terminal] = terminal_state_counts.get(terminal, 0) + 1
        fill_class = str(row["fill_completion_class"])
        fill_completion_counts[fill_class] = (
            fill_completion_counts.get(fill_class, 0) + 1
        )

    source_census = census.as_dict()
    if pipeline_event_source_row_count and journal_transition_source_row_count:
        source_kind = "mixed_pipeline_and_transition_journal"
    elif pipeline_event_source_row_count:
        source_kind = "pipeline_events_explicit_id_only"
    elif journal_transition_source_row_count:
        source_kind = "transition_journal"
    else:
        source_kind = "unknown_or_empty"
    report: dict[str, Any] = {
        "schema": REPORT_SCHEMA,
        "target_date": target,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_transition_schema": JOURNAL_SCHEMA,
        "source_pipeline_identity_schema": PIPELINE_IDENTITY_SCHEMA,
        "broker_execution_provenance_schema": (BROKER_EXECUTION_PROVENANCE_SCHEMA),
        "broker_execution_raw_envelope_schema": (BROKER_EXECUTION_RAW_ENVELOPE_SCHEMA),
        "broker_execution_official_reference_sha": (KIWOOM_OFFICIAL_REFERENCE_SHA),
        "source_kind": source_kind,
        "source_path": census.source_path,
        "source_raw_sha256": census.source_raw_sha256,
        "source_content_sha256": census.source_decoded_sha256,
        "source_raw_census": source_census,
        "source_census_content_sha256": _sha256(source_census),
        "raw_fallback_census": fallback_census,
        "reviewed_cost_profile_sha256": reviewed_cost_hash,
        "reviewed_cost_profile_verified": reviewed_cost_verified,
        "symbol_master_artifact_sha256": symbol_master_hash,
        "symbol_master_artifact_verified": symbol_master_verified,
        "reference_contract_blockers": reference_contract_blockers,
        "reference_binding_mode": reference_binding_mode,
        "instrumentation_gap_count": (
            source_invalid_transition_count
            + census.malformed_json_count
            + census.non_object_count
            + int(census.source_read_error is not None)
            + fallback_gap_count
            + candidate_row_gate_failure_count
            + broker_execution_provenance_gap_count
            + broker_execution_conflict_count
            + broker_execution_order_progress_conflict_count
            + broker_execution_submission_link_conflict_count
            + broker_order_no_cross_lifecycle_conflict_count
            + broker_execution_cross_lifecycle_identity_conflict_count
            + lifecycle_accumulator_overflow_row_count
            + transition_event_identity_overflow_row_count
            + pipeline_lifecycle_owner_scoped_gap_count
            + int(not census.source_exists)
            + int(not rows)
        ),
        "instrumentation_gap_examples": gap_examples,
        "source_invalid_transition_count": source_invalid_transition_count,
        "journal_transition_source_row_count": journal_transition_source_row_count,
        "pipeline_event_source_row_count": pipeline_event_source_row_count,
        "pipeline_lifecycle_mapped_row_count": (pipeline_lifecycle_mapped_row_count),
        "pipeline_lifecycle_accepted_row_count": (
            pipeline_lifecycle_accepted_row_count
        ),
        "pipeline_lifecycle_out_of_scope_row_count": (
            pipeline_lifecycle_out_of_scope_row_count
        ),
        "pipeline_lifecycle_instrumentation_gap_count": (
            pipeline_lifecycle_instrumentation_gap_count
        ),
        "pipeline_lifecycle_missing_identity_count": (
            pipeline_lifecycle_missing_identity_count
        ),
        "pipeline_lifecycle_owner_scoped_gap_count": (
            pipeline_lifecycle_owner_scoped_gap_count
        ),
        "pipeline_lifecycle_unscoped_gap_count": (
            pipeline_lifecycle_unscoped_gap_count
        ),
        "pipeline_owner_exclusion_manifest": pipeline_owner_exclusion_manifest,
        "pipeline_owner_scoped_gap_high_volume_min_rows": (
            PIPELINE_OWNER_SCOPED_GAP_HARD_BLOCK_MIN_ROWS
        ),
        "pipeline_owner_scoped_gap_high_volume_blocked": (
            pipeline_owner_scoped_gap_high_volume
        ),
        "mixed_source_row_count": mixed_source_row_count,
        "lifecycle_accumulator_overflow_row_count": (
            lifecycle_accumulator_overflow_row_count
        ),
        "transition_event_identity_overflow_row_count": (
            transition_event_identity_overflow_row_count
        ),
        "lifecycle_invalid_transition_count": lifecycle_invalid_transition_count,
        "broker_execution_provenance_gap_count": (
            broker_execution_provenance_gap_count
        ),
        "broker_execution_conflict_count": broker_execution_conflict_count,
        "broker_execution_order_progress_conflict_count": (
            broker_execution_order_progress_conflict_count
        ),
        "broker_execution_submission_link_conflict_count": (
            broker_execution_submission_link_conflict_count
        ),
        "broker_order_no_cross_lifecycle_conflict_count": (
            broker_order_no_cross_lifecycle_conflict_count
        ),
        "broker_execution_cross_lifecycle_identity_conflict_count": (
            broker_execution_cross_lifecycle_identity_conflict_count
        ),
        "broker_execution_replay_duplicate_count": (
            broker_execution_replay_duplicate_count
        ),
        "broker_execution_unique_count": broker_execution_unique_count,
        "candidate_row_gate_failure_count": candidate_row_gate_failure_count,
        "lifecycle_window_exclusion_manifest": (lifecycle_window_exclusion_manifest),
        "lifecycle_count": len(rows),
        "terminal_state_counts": dict(sorted(terminal_state_counts.items())),
        "fill_completion_class_counts": dict(sorted(fill_completion_counts.items())),
        "promotion_evidence_eligible_count": eligible_count,
        "promotion_ready": eligible_count > 0 and not global_gate_blockers,
        "promotion_ready_lifecycle_ids": [
            str(row["main_lifecycle_id"])
            for row in rows
            if row["promotion_evidence_eligible"] is True
        ],
        "global_source_quality_gate_pass": not global_gate_blockers,
        "global_source_quality_gate_blockers": global_gate_blockers,
        "rows": rows,
        "streaming_memory_contract": {
            "source_scan_count": 1,
            "source_rows_retained": 0,
            "transition_buffers_retained": 0,
            "accumulator_count": len(accumulators),
            "accumulator_limit": MAX_LIFECYCLE_ACCUMULATORS,
            "materialized_report_row_count": len(rows),
            "retained_transition_event_identity_count": (
                retained_transition_event_identity_count
            ),
            "global_transition_event_identity_limit": (MAX_TRANSITION_EVENT_IDENTITIES),
            "decision_trace_ids_per_lifecycle_limit": _TRACE_ID_LIMIT,
            "event_ids_per_lifecycle_limit": _EVENT_ID_LIMIT_PER_LIFECYCLE,
            "instrumentation_gap_example_limit": _GAP_EXAMPLE_LIMIT,
        },
        **REPORT_AUTHORITY_CONTRACT,
    }
    digest = _sha256(report)
    report["content_sha256"] = digest
    report["report_content_sha256"] = digest
    report["artifact_content_sha256"] = _sha256(report)
    if write:
        _atomic_write_json(output_path or paired_report_path(target), report)
    return report


def build_main_lifecycle_paired_report(
    target_date: str | date,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility name for postclose orchestration."""

    return build_daily_report(target_date, **kwargs)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, dest="target_date")
    parser.add_argument(
        "--journal", "--source", "--pipeline", dest="journal", type=Path
    )
    parser.add_argument("--raw-fallback", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reviewed-cost-profile-sha256")
    parser.add_argument("--reviewed-cost-profile-verified", action="store_true")
    parser.add_argument("--symbol-master-artifact-sha256")
    parser.add_argument("--symbol-master-artifact-verified", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    report = build_daily_report(
        args.target_date,
        source_path=args.journal,
        raw_fallback_path=args.raw_fallback,
        output_path=args.output,
        reviewed_cost_profile_sha256=args.reviewed_cost_profile_sha256,
        reviewed_cost_profile_verified=args.reviewed_cost_profile_verified,
        symbol_master_artifact_sha256=args.symbol_master_artifact_sha256,
        symbol_master_artifact_verified=args.symbol_master_artifact_verified,
        write=args.write,
    )
    stdout_payload: Mapping[str, Any]
    if args.write:
        stdout_payload = {
            "schema": "main_scalping_lifecycle_paired_cli_result_v1",
            "target_date": args.target_date,
            "output_path": str(args.output or paired_report_path(args.target_date)),
            "artifact_content_sha256": report["artifact_content_sha256"],
            "lifecycle_count": report["lifecycle_count"],
            "promotion_ready": report["promotion_ready"],
            "runtime_authority": False,
            "order_authority": False,
            "provider_authority": False,
        }
    else:
        stdout_payload = report
    print(json.dumps(stdout_payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "PIPELINE_OWNER_EXCLUSION_AUTHORITY_CONTRACT",
    "PIPELINE_OWNER_EXCLUSION_MANIFEST_SCHEMA",
    "REPORT_AUTHORITY_CONTRACT",
    "REPORT_SCHEMA",
    "build_daily_report",
    "build_main_lifecycle_paired_report",
    "main",
    "paired_report_path",
    "pipeline_event_path",
    "report_path",
]
