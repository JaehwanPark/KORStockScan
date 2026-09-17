"""Order-free, hash-bound research lifecycle contracts.

Monitoring owns admissions, frozen experiments and consumer evidence. None of
these records grants custody, capital, API, restart or order authority.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import re
import stat
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

SCHEMA = "machine_research_closed_loop_v1"
DIRECTORY = DATA_DIR / "runtime" / "machine_research_closed_loop"
AUTHORITY = dict(
    runtime_effect=False,
    allowed_runtime_apply=False,
    actual_order_submitted=False,
    broker_order_forbidden=True,
)


_RESEARCH_SCOPE = ContextVar("machine_research_directory", default=None)


@contextmanager
def research_scope(directory):
    token = _RESEARCH_SCOPE.set(Path(directory))
    try:
        yield
    finally:
        _RESEARCH_SCOPE.reset(token)


def _directory(directory):
    return (
        _RESEARCH_SCOPE.get() or DIRECTORY
        if directory == DIRECTORY
        else Path(directory)
    )


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def read_object(path, limit=4 * 1024 * 1024):
    """Read a stable bounded regular file without following its final symlink."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        raise ValueError("research_source_not_bounded_regular_file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read(limit + 1)
        after = os.fstat(handle.fileno())

    def generation(s):
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    if (
        len(raw) > limit
        or generation(before) != generation(opened)
        or generation(opened) != generation(after)
        or generation(after) != generation(path.lstat())
    ):
        raise ValueError("research_source_changed_during_read")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("research_source_not_object")
    return value


def atomic_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("research_output_symlink")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(value, handle, sort_keys=True, ensure_ascii=True, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def writer_lock(directory, *, blocking=True):
    directory = _directory(directory)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    fd = os.open(
        directory / ".writer.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600
    )
    with os.fdopen(fd, "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        yield


def trading_dates_after(day, count):
    dates = []
    while len(dates) < count:
        day += timedelta(days=1)
        if is_krx_trading_day(day):
            dates.append(day.isoformat())
    return dates


def candidate_revision(
    *,
    symbol,
    parameters,
    source_date,
    source_sha256,
    owner="widget",
    calibration_days=10,
    holdout_days=16,
    cost_sha256,
    frozen_at=None,
    lane_id=None,
    baseline_parameters=None,
    baseline_policy_id=None,
    supersedes_revision_sha256=None,
    supersession_reason=None,
):
    frozen_at = frozen_at or datetime.now(ZoneInfo("Asia/Seoul"))
    if frozen_at.tzinfo is not None:
        frozen_at = frozen_at.astimezone(ZoneInfo("Asia/Seoul"))
    if frozen_at.tzinfo is None or frozen_at.date() < source_date:
        raise ValueError("research_candidate_freeze_clock_invalid")
    dates = trading_dates_after(frozen_at.date(), calibration_days + holdout_days)
    body = dict(
        schema=SCHEMA,
        symbol=symbol,
        owner=owner,
        parameters=parameters,
        parameters_sha256=digest(parameters),
        baseline_parameters=baseline_parameters,
        baseline_policy_id=baseline_policy_id,
        supersedes_revision_sha256=supersedes_revision_sha256,
        supersession_reason=supersession_reason,
        frozen_source_date=source_date.isoformat(),
        frozen_at=frozen_at.isoformat(),
        lane_id=lane_id or symbol,
        frozen_source_sha256=source_sha256,
        cost_sha256=cost_sha256,
        calibration_dates=dates[:calibration_days],
        holdout_dates=dates[calibration_days:],
        selection_rule="one_prespecified_historical_calibration_winner_no_holdout_substitution",
        **AUTHORITY,
    )
    return {**body, "revision_sha256": digest(body)}


def validate_revision(value, *, symbol=None, owner=None):
    if (
        not isinstance(value, dict)
        or value.get("schema") != SCHEMA
        or value.get("revision_sha256")
        != digest({k: v for k, v in value.items() if k != "revision_sha256"})
    ):
        raise ValueError("research_candidate_revision_invalid")
    if (
        (symbol is not None and value.get("symbol") != symbol)
        or (owner is not None and value.get("owner") != owner)
        or any(value.get(k) is not v for k, v in AUTHORITY.items())
        or digest(value.get("parameters")) != value.get("parameters_sha256")
    ):
        raise ValueError("research_candidate_revision_identity_invalid")
    if (
        re.fullmatch(r"[0-9]{6}", str(value.get("symbol") or "")) is None
        or value.get("owner") not in {"widget", "episode"}
        or re.fullmatch(r"[A-Za-z0-9_]{1,100}", str(value.get("lane_id") or "")) is None
    ):
        raise ValueError("research_candidate_identity_invalid")
    source_date = date.fromisoformat(value["frozen_source_date"])
    frozen_at = datetime.fromisoformat(value["frozen_at"])
    if (
        source_date < date(2026, 6, 5)
        or frozen_at.tzinfo is None
        or frozen_at.date() < source_date
    ):
        raise ValueError("research_candidate_source_clock_invalid")
    for key in ("frozen_source_sha256", "cost_sha256"):
        if re.fullmatch(r"[0-9a-f]{64}", str(value.get(key) or "")) is None:
            raise ValueError("research_candidate_provenance_hash_invalid")
    calibration, holdout = value["calibration_dates"], value["holdout_dates"]
    floor = 10 if value["owner"] == "widget" else 30
    if len(calibration) != floor or len(holdout) != 16:
        raise ValueError("research_candidate_window_floor_invalid")
    if (
        not calibration
        or not holdout
        or calibration + holdout
        != trading_dates_after(frozen_at.date(), len(calibration) + len(holdout))
    ):
        raise ValueError("research_candidate_calendar_invalid")
    return value


def load_candidate(symbol, *, owner="widget", lane_id=None, directory=DIRECTORY):
    directory = _directory(directory)
    lane_id = symbol if lane_id is None else lane_id
    if re.fullmatch(r"[A-Za-z0-9_]{1,100}", str(lane_id)) is None or owner not in {
        "widget",
        "episode",
    }:
        raise ValueError("research_candidate_identity_invalid")
    try:
        return validate_revision(
            read_object(Path(directory) / "candidates" / f"{owner}_{lane_id}.json"),
            symbol=symbol,
            owner=owner,
        )
    except FileNotFoundError:
        return None


def freeze_candidate(value, *, directory=DIRECTORY):
    directory = _directory(directory)
    value = validate_revision(value)
    path = Path(directory) / "candidates" / f"{value['owner']}_{value['lane_id']}.json"
    with writer_lock(path.parent):
        existing = load_candidate(
            value["symbol"],
            owner=value["owner"],
            lane_id=value["lane_id"],
            directory=directory,
        )
        if existing is not None and existing != value:
            if value.get("supersedes_revision_sha256") != existing[
                "revision_sha256"
            ] or value.get("supersession_reason") not in {
                "source_or_cost_correction",
                "incumbent_parent_changed",
                "mature_nonperforming_revision",
            }:
                return existing
            atomic_write(
                path.parent / ".history" / f"{existing['revision_sha256']}.json",
                existing,
            )
        atomic_write(
            path.parent / ".history" / f"{value['revision_sha256']}.json", value
        )
        atomic_write(path, value)
    return value


def seal_execution_receipt(value):
    return {**value, "execution_receipt_sha256": digest(value)}


def verified_execution_receipt(value):
    from src.engine.monitoring.research_source_facts import generation, source_integrity

    try:
        body = {k: v for k, v in value.items() if k != "execution_receipt_sha256"}
        return (
            value.get("status") == "pass"
            and value.get("execution_receipt_sha256") == digest(body)
            and bool(value.get("source_hashes"))
            and set(value["source_hashes"])
            == set(value.get("source_generations") or {})
            and all(
                source_integrity(Path(name))
                and list(generation(Path(name).lstat())) == list(expected)
                and not Path(name).is_symlink()
                for name, expected in value["source_generations"].items()
            )
        )
    except (OSError, ValueError, TypeError, KeyError):
        return False


def widget_prospective_summary_valid(result, revision):
    """Recompute supplied economics and calendar partitions from native CF rows."""
    from src.engine.monitoring.widget_symbol_signal_policy_research import (
        _summarize_episodes,
    )

    try:
        cal, hold = revision["calibration_dates"], revision["holdout_dates"]
        rows = {
            name: (result.get(name) or {}).get(
                "episodes", (result.get("selected_episodes") or {}).get(name, [])
            )
            for name in ("calibration", "holdout")
        }
        all_rows = rows["calibration"] + rows["holdout"]
        dates = dict(
            calibration=cal,
            holdout=hold,
            calibration_first_half=cal[: len(cal) // 2],
            calibration_second_half=cal[len(cal) // 2 :],
        )
        identities = [(r["entry_at"], r["exit_at"]) for r in all_rows]
        if len(set(identities)) != len(identities):
            return False
        for name, window in dates.items():
            selected = [row for row in all_rows if row["trade_date"] in window]
            if name in rows and rows[name] != selected:
                return False
            expected = _summarize_episodes(selected)
            supplied = result[name]
            if any(supplied.get(key) != value for key, value in expected.items()):
                return False
            if any(
                not 1
                <= row["daily_entry_ordinal"]
                <= revision["parameters"]["max_completed_entries_per_day"]
                for row in selected
            ):
                return False
        return True
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def registered_revision(value, *, directory=DIRECTORY):
    directory = _directory(directory)
    value = validate_revision(value)
    try:
        stored = read_object(
            Path(directory)
            / "candidates"
            / ".history"
            / f"{value['revision_sha256']}.json"
        )
    except FileNotFoundError:
        return False
    return stored == value


def prospective_window(value, *, source_date, qualified_dates):
    value = validate_revision(value)
    required = value["calibration_dates"] + value["holdout_dates"]
    qualified = {str(day) for day in qualified_dates}
    missing = [
        day
        for day in required
        if day <= source_date.isoformat() and day not in qualified
    ]
    due = [day for day in required if day > source_date.isoformat()]
    return dict(
        status="source_gap" if missing else "waiting" if due else "ready",
        missing_dates=missing,
        not_yet_due_dates=due,
        revision_sha256=value["revision_sha256"],
        **AUTHORITY,
    )


def publication_transaction(
    directory, *, effective_date, files, expected_generation=None
):
    """Commit immutable files and materializations under one writer lock.

    The manifest is the last commit point. Interrupted writes are never
    accepted. An explicit compare-and-swap successor is restricted to a future
    date; loaded holdings retain their original immutable execution version.
    """
    directory = _directory(directory)
    directory = Path(directory)
    payloads = {str(name): digest(value) for name, value in sorted(files.items())}
    if not payloads or any(Path(name).name != name for name in payloads):
        raise ValueError("research_publication_filename_invalid")
    pointer = directory / f"research_publication_{effective_date.isoformat()}.json"
    with writer_lock(directory):
        try:
            previous = read_object(pointer)
        except FileNotFoundError:
            previous = None
        previous_files = previous.get("files") if previous else None
        identical = previous_files == payloads
        if previous and not identical:
            if (
                expected_generation != previous.get("generation_sha256")
                or effective_date <= datetime.now(ZoneInfo("Asia/Seoul")).date()
                or set(previous_files) != set(payloads)
            ):
                raise ValueError("research_same_date_publication_conflict")
        body = dict(
            schema=SCHEMA,
            effective_date=effective_date.isoformat(),
            files=payloads,
            parent_generation_sha256=(
                previous.get("generation_sha256")
                if previous and not identical
                else None
            ),
            **AUTHORITY,
        )
        manifest = (
            previous if identical else {**body, "generation_sha256": digest(body)}
        )
        generation = manifest["generation_sha256"]
        immutable = directory / ".generations" / generation
        for name, value in files.items():
            path = immutable / name
            try:
                existing = read_object(path, limit=64 * 1024 * 1024)
            except FileNotFoundError:
                existing = None
            if existing is not None and digest(existing) != payloads[name]:
                raise ValueError("research_immutable_generation_corrupt")
            if existing is None:
                atomic_write(path, value)
        # Old readers reject the v2 policy. New readers require the complete
        # bundle and manifest. A kill before the final rename fails closed.
        for name, value in files.items():
            atomic_write(directory / name, value)
        atomic_write(pointer, manifest)
    return manifest


def future_publication_parent(directory, effective_date):
    """Return a validated future parent for the existing nightly fixed point."""
    directory = _directory(directory)
    if effective_date <= datetime.now(ZoneInfo("Asia/Seoul")).date():
        return None
    try:
        pointer = read_object(
            Path(directory) / f"research_publication_{effective_date.isoformat()}.json"
        )
    except FileNotFoundError:
        return None
    body = {k: v for k, v in pointer.items() if k != "generation_sha256"}
    if (
        pointer.get("schema") != SCHEMA
        or pointer.get("generation_sha256") != digest(body)
        or pointer.get("effective_date") != effective_date.isoformat()
    ):
        raise ValueError("research_publication_parent_invalid")
    return pointer["generation_sha256"]


def verify_publication(directory, *, effective_date, name, value):
    directory = _directory(directory)
    manifest = read_object(
        Path(directory) / f"research_publication_{effective_date.isoformat()}.json"
    )
    body = {k: v for k, v in manifest.items() if k != "generation_sha256"}
    if (
        manifest.get("schema") != SCHEMA
        or manifest.get("effective_date") != effective_date.isoformat()
        or manifest.get("generation_sha256") != digest(body)
        or manifest.get("files", {}).get(name) != digest(value)
    ):
        raise ValueError("research_publication_not_committed")
    for filename, sha256 in manifest["files"].items():
        if (
            Path(filename).name != filename
            or digest(read_object(Path(directory) / filename, limit=64 * 1024 * 1024))
            != sha256
            or digest(
                read_object(
                    Path(directory)
                    / ".generations"
                    / manifest["generation_sha256"]
                    / filename,
                    limit=64 * 1024 * 1024,
                )
            )
            != sha256
        ):
            raise ValueError("research_publication_incomplete_bundle")
    immutable = read_object(
        Path(directory) / ".generations" / manifest["generation_sha256"] / name,
        limit=64 * 1024 * 1024,
    )
    if immutable != value:
        raise ValueError("research_publication_generation_mismatch")
    return manifest


def consumer_receipt(
    *, owner, effective_date, accepted, rejected=None, directory=DIRECTORY
):
    """Called by the actual consumer after validation, never by the publisher."""
    directory = _directory(directory)
    body = dict(
        schema=SCHEMA,
        status="published_not_consumed"
        if rejected
        else "consumed"
        if accepted
        else "valid_empty",
        rejected=rejected or {},
        owner=owner,
        effective_date=effective_date.isoformat(),
        pid=os.getpid(),
        process_start_ticks=Path("/proc/self/stat")
        .read_text()
        .rsplit(") ", 1)[1]
        .split()[19],
        boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        cwd=os.getcwd(),
        import_root=str(Path(__file__).resolve().parents[3]),
        accepted_policy_sha256=digest(accepted),
        accepted=accepted,
        observed_at=datetime.now().astimezone().isoformat(),
        **AUTHORITY,
    )
    path = (
        Path(directory)
        / "consumers"
        / f"{owner}_{effective_date.isoformat()}_{os.getpid()}.json"
    )
    atomic_write(path, {**body, "receipt_sha256": digest(body)})
    return path


def joint_allocation(episodes, *, snapshot, source_date, parent_sha256):
    """Fixed incumbent allocator feasibility, with no hindsight trade pruning."""
    blocked = dict(
        schema=SCHEMA,
        status="allocation_blocked",
        feasible_combined_net_profit_krw=None,
        source_date=source_date.isoformat(),
        parent_sha256=parent_sha256,
        **AUTHORITY,
    )
    if not isinstance(snapshot, dict):
        return {**blocked, "reason": "exact_date_allocator_snapshot_missing"}
    try:
        body = {k: v for k, v in snapshot.items() if k != "snapshot_sha256"}
        valid = (
            snapshot.get("schema") == "machine_research_allocator_snapshot_v1"
            and snapshot.get("source_date") == source_date.isoformat()
            and snapshot.get("snapshot_sha256") == digest(body)
        )
        valid &= (
            snapshot.get("allocator_rule")
            == "fixed_existing_allocator_no_research_arbitration"
        )
        valid &= (
            snapshot.get("source_quality_status") == "PASS"
            and snapshot.get("owner_conflict") is False
        )
        valid &= all(snapshot.get(k) is v for k, v in AUTHORITY.items())
        valid &= all(
            type(snapshot.get(k)) in (int, float)
            and math.isfinite(snapshot[k])
            and snapshot[k] >= 0
            for k in (
                "available_cash_krw",
                "exposure_limit_krw",
                "holding_notional_krw",
                "reserved_notional_krw",
            )
        )
        valid &= (
            isinstance(snapshot.get("owner_contract_sha256"), str)
            and len(snapshot["owner_contract_sha256"]) == 64
        )
        constraints = snapshot.get("constraints") or {}
        contract_body = {k: v for k, v in constraints.items() if k != "contract_sha256"}
        valid &= (
            snapshot.get("exposure_limit_basis") == "native_existing_allocator_contract"
            and constraints.get("contract_sha256") == digest(contract_body)
            and constraints.get("source_date") == str(source_date)
            and constraints.get("owner_contract_sha256")
            == snapshot.get("owner_contract_sha256")
            and constraints.get("same_stage_clear") is True
            and constraints.get("cooldown_contract_status")
            == "verified_native_family_policy"
            and constraints.get("venue_session_contract") == "KRX/KRX_REGULAR"
            and constraints.get("per_leg_quantity") == 10
            and type(constraints.get("buy_fee_bps")) in (int, float)
            and math.isfinite(constraints["buy_fee_bps"])
            and constraints["buy_fee_bps"] >= 0
            and all(constraints.get(k) is v for k, v in AUTHORITY.items())
        )
        if not valid:
            raise ValueError("allocator_snapshot_contract_invalid")
        blocked_symbols = set(constraints.get("blocked_symbols") or [])
        if any(
            lane.split(":")[1] in blocked_symbols for lane in episodes if ":" in lane
        ):
            return {**blocked, "reason": "native_operator_or_owner_veto"}
        limit = min(
            snapshot["available_cash_krw"] - snapshot["reserved_notional_krw"],
            snapshot["exposure_limit_krw"]
            - snapshot["holding_notional_krw"]
            - snapshot["reserved_notional_krw"],
        )
        from src.engine.monitoring.policy_research_economics import joint_capital_demand

        demand = joint_capital_demand(
            episodes,
            capital_limit_krw=limit,
            buy_fee_bps=constraints["buy_fee_bps"],
        )
        return {
            **blocked,
            "status": "pass" if demand["capital_feasible"] else "allocation_blocked",
            "reason": "fixed_allocator_feasible"
            if demand["capital_feasible"]
            else "joint_demand_exceeds_available_capacity_or_invalid",
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "demand": demand,
            "feasible_combined_net_profit_krw": demand[
                "feasible_combined_net_profit_krw"
            ],
        }
    except (TypeError, ValueError, KeyError):
        return {**blocked, "reason": "allocator_snapshot_contract_invalid"}


def load_allocator(source_date, *, directory=DIRECTORY):
    directory = _directory(directory)
    try:
        snapshot = read_object(
            Path(directory) / f"allocator_{source_date.isoformat()}.json"
        )
        if snapshot.get("source_quality_status") == "PASS":
            acquisition_path = snapshot.get("native_acquisition_path")
            if not acquisition_path:
                return None
            acquisition = read_object(Path(acquisition_path))
            if (
                acquisition.get("status") != "complete"
                or acquisition.get("receipt_sha256")
                != snapshot.get("native_acquisition_sha256")
                or acquisition.get("receipt_sha256")
                != digest(
                    {k: v for k, v in acquisition.items() if k != "receipt_sha256"}
                )
            ):
                return None
            for name in ("cash", "inventory"):
                path = snapshot.get(f"native_{name}_path")
                if not path:
                    return None
                native = read_object(Path(path))
                if native.get("native_sha256") != snapshot.get(
                    f"native_{name}_sha256"
                ) or native.get("native_sha256") != digest(
                    {k: v for k, v in native.items() if k != "native_sha256"}
                ):
                    return None
            constraints = snapshot.get("constraints") or {}
            if (
                not constraints.get("same_stage_source_path")
                or not snapshot.get("owner_policy_path")
                or digest(
                    read_object(
                        Path(constraints["same_stage_source_path"]),
                        limit=32 * 1024 * 1024,
                    )
                )
                != constraints.get("same_stage_source_sha256")
                or digest(read_object(Path(snapshot["owner_policy_path"])))
                != snapshot.get("owner_contract_sha256")
            ):
                return None
        return snapshot
    except (OSError, ValueError):
        return None


def report_joint_gate(report, *, source_date, directory=DIRECTORY):
    directory = _directory(directory)
    return combined_joint_gate(
        report, family="widget", source_date=source_date, directory=directory
    )


def admission_catalog(census):
    """Admit causal scanner rows, never forward winners or their PnL/rank."""
    day = date.fromisoformat(census["target_date"])
    receipts = (census.get("scanner_source_census") or {}).get("receipts", [])
    rows, seen, invalid = [], {}, 0
    for receipt in receipts:
        native = receipt.get("causal_rows")
        if receipt.get("contract_valid") is not True or not isinstance(native, list):
            invalid += 1
            continue
        at = datetime.fromisoformat(receipt["emitted_at"])
        if at.tzinfo is None or at.date() != day:
            invalid += 1
            continue
        for index, source in enumerate(native):
            symbol = str(source.get("stock_code") or "")
            if len(symbol) != 6 or not symbol.isdigit():
                invalid += 1
                continue
            identity = digest(
                dict(
                    cycle=receipt["source_cycle_id"],
                    symbol=symbol,
                    venue=source.get("venue"),
                    routes=source.get(
                        "market_data_routes", source.get("market_data_route")
                    ),
                )
            )
            fingerprint = digest(source)
            if identity in seen:
                # Pool and adapter projections of one candidate share a parent.
                continue
            seen[identity] = fingerprint
            venue = source.get("venue")
            common = (
                source.get("symbol_master_status") == "verified"
                and source.get("instrument_type") == "EQUITY"
                and source.get("listing_market") in {"KOSPI", "KOSDAQ"}
            )
            rows.append(
                dict(
                    native_opportunity_id=identity,
                    stock_code=symbol,
                    name=str(source.get("name") or symbol),
                    source_index=index,
                    source_rows_sha256=receipt["rows_sha256"],
                    canonical_scanner_row_sha256=source.get(
                        "canonical_scanner_row_sha256"
                    ),
                    native_parent_count=source.get("native_parent_count", 1),
                    native_projection_count=source.get("native_projection_count", 1),
                    parent_bindings_sha256=source.get("parent_bindings_sha256"),
                    source_date=day.isoformat(),
                    source_clock=at.isoformat(),
                    first_seen_at=at.isoformat(),
                    original_owner="main_scanner",
                    venue=venue,
                    market_data_route=source.get(
                        "market_data_route", source.get("market_data_routes")
                    ),
                    admission_reason="causal_scanner_candidate_not_forward_label",
                    disposition="raw_only"
                    if venue == "KRX" and common
                    else "research_blocked_unknown_venue_or_common_master",
                    research_lanes=["widget", "episode"]
                    if venue == "KRX" and common
                    else [],
                )
            )
    omitted = sum(
        int((receipt.get("declared_counts") or {}).get("omitted") or 0)
        for receipt in receipts
    )
    body = dict(
        schema=SCHEMA,
        source_date=day.isoformat(),
        native_count=len(rows),
        native_parent_count=sum(row["native_parent_count"] for row in rows),
        projection_count=sum(row["native_projection_count"] for row in rows),
        duplicate_projection_count=sum(
            row["native_projection_count"] - row["native_parent_count"] for row in rows
        ),
        parent_disposition_counts={
            reason: sum(
                row["native_parent_count"]
                for row in rows
                if row["disposition"] == reason
            )
            for reason in {row["disposition"] for row in rows}
        },
        parent_receipts_sha256=digest(
            [
                {k: v for k, v in receipt.items() if k != "causal_rows"}
                for receipt in receipts
            ]
        ),
        rows=rows,
        invalid_receipt_count=invalid,
        omitted_native_row_count=omitted,
        coverage_status="source_gap" if invalid or omitted else "complete",
        order_authority_granted=False,
        **AUTHORITY,
    )
    return {**body, "catalog_sha256": digest(body)}


def write_admissions(census, *, directory=DIRECTORY):
    directory = _directory(directory)
    catalog = admission_catalog(census)
    folder = Path(directory) / "admissions"
    path = folder / f"admissions_{catalog['source_date']}.json"
    with writer_lock(folder):
        try:
            index = read_object(folder / "symbol_index.json")
            body = {k: v for k, v in index.items() if k != "index_sha256"}
            if index.get("index_sha256") != digest(body):
                raise ValueError("research_admission_index_invalid")
            days = dict(index["days"])
        except FileNotFoundError:
            days = {}
        names = dict(index.get("symbol_names", {})) if days else {}
        for record in days.values():
            for symbol, row in list(record["symbols"].items()):
                if isinstance(row, dict):
                    names.setdefault(symbol, row["name"])
                    record["symbols"][symbol] = sum(
                        1 if lane == "widget" else 2
                        for lane in row["lanes"]
                        if lane in {"widget", "episode"}
                    )
        for row in catalog["rows"]:
            if row["disposition"] == "raw_only":
                names.setdefault(row["stock_code"], row["name"])
        days[catalog["source_date"]] = dict(
            catalog_sha256=catalog["catalog_sha256"],
            coverage_status=catalog["coverage_status"],
            symbols={
                row["stock_code"]: sum(
                    1 if lane == "widget" else 2
                    for lane in row["research_lanes"]
                    if lane in {"widget", "episode"}
                )
                for row in catalog["rows"]
                if row["disposition"] == "raw_only"
            },
        )
        body = dict(
            schema=SCHEMA,
            days=days,
            symbol_names=names,
            order_authority_granted=False,
            **AUTHORITY,
        )
        atomic_write(path, catalog)
        atomic_write(
            folder / "symbol_index.json", {**body, "index_sha256": digest(body)}
        )
    return path


def admission_symbols(observed_date, *, owner, directory=DIRECTORY):
    directory = _directory(directory)
    try:
        index = read_object(Path(directory) / "admissions" / "symbol_index.json")
    except FileNotFoundError:
        return {}
    body = {k: v for k, v in index.items() if k != "index_sha256"}
    if (
        index.get("schema") != SCHEMA
        or index.get("index_sha256") != digest(body)
        or any(index.get(k) is not v for k, v in AUTHORITY.items())
    ):
        raise ValueError("research_admission_index_invalid")
    symbols = {}
    for day, record in sorted(index["days"].items()):
        if date.fromisoformat(day) > observed_date:
            continue
        for symbol, row in record["symbols"].items():
            if isinstance(row, dict):
                admitted, name = owner in row["lanes"], row["name"]
            else:
                admitted = bool(row & ({"widget": 1, "episode": 2}.get(owner, 0)))
                name = index["symbol_names"][symbol]
            if admitted:
                symbols.setdefault(symbol, name)
    return symbols


def joint_inputs(report, *, family):
    source_date = str(report.get("end_date") or report.get("target_date"))
    selected, deferred = {}, []
    if family == "widget":
        for symbol, result in report.get("symbols", {}).items():
            if result.get("decision") != "holdout_pass_widget_signal_policy_candidate":
                if result.get("candidate_revision"):
                    deferred.append(result["candidate_revision"]["revision_sha256"])
                continue
            selected[f"widget:{symbol}"] = [
                row
                for window in ("calibration", "holdout")
                for row in (result.get(window) or {}).get(
                    "episodes", (result.get("selected_episodes") or {}).get(window, [])
                )
            ]
    elif family == "episode":
        for profile_id, result in report.get("profiles", {}).items():
            if result.get("decision") != "holdout_pass_source_only_early_candidate":
                if result.get("candidate_revision"):
                    deferred.append(result["candidate_revision"]["revision_sha256"])
                continue
            rows = []
            for episode in ((result.get("selected") or {}).get("full") or {}).get(
                "episodes", []
            ):
                for index, leg in enumerate(episode.get("legs") or []):
                    if leg.get("status") == "COMPLETE":
                        rows.append(
                            dict(
                                entry_at=leg.get("fill_at"),
                                exit_at=leg.get("target_at"),
                                entry_price=leg.get("entry_price"),
                                net_return_pct=leg.get("net_profit_pct"),
                                leg_index=index,
                            )
                        )
            # Separate leg lanes preserve native identity even for equal-price,
            # equal-clock fills. Quantity and aggregate depth remain shared.
            for index in (0, 1):
                selected[f"episode:{result['symbol']}:{profile_id}:{index}"] = [
                    row for row in rows if row["leg_index"] == index
                ]
    else:
        raise ValueError("research_joint_family_invalid")
    from src.engine.monitoring.research_portfolio_economics import reference_inputs
    try:
        portfolio_reference = reference_inputs(report, family)
    except (ValueError, TypeError, KeyError):
        portfolio_reference = dict(lanes={}, missing_reference_lanes=["invalid_native_reference"])
    body = dict(
        portfolio_reference=portfolio_reference,
        schema=SCHEMA,
        family=family,
        source_date=source_date,
        selected_episodes=selected,
        depth_demands=[
            row
            for value in report.get("symbols", report.get("profiles", {})).values()
            if value.get("decision")
            in {
                "holdout_pass_widget_signal_policy_candidate",
                "holdout_pass_source_only_early_candidate",
            }
            for row in (value.get("execution_feasibility") or {}).get(
                "depth_demands", []
            )
        ],
        candidate_revisions={
            key: value["candidate_revision"]
            for key, value in report.get("symbols", report.get("profiles", {})).items()
            if value.get("candidate_revision")
        },
        deferred_revision_hashes=sorted(deferred),
        semantic_inputs_sha256=digest(
            dict(
                source_meta=report.get("source_meta"),
                parameters={
                    key: value.get(
                        "candidate_revision",
                        value.get("selected_policy", value.get("selected")),
                    )
                    for key, value in report.get(
                        "symbols", report.get("profiles", {})
                    ).items()
                },
            )
        ),
        allocator_rule="fixed_existing_allocator_no_research_arbitration",
        **AUTHORITY,
    )
    return {**body, "inputs_sha256": digest(body)}


def write_joint_inputs(report, *, family, directory=DIRECTORY):
    directory = _directory(directory)
    inputs = joint_inputs(report, family=family)
    path = Path(directory) / f"joint_inputs_{family}_{inputs['source_date']}.json"
    atomic_write(path, inputs)
    return path


def _joint_cohorts(inputs):
    cohorts = {}
    for item in inputs:
        for value in item.get("candidate_revisions", {}).values():
            value = validate_revision(value)
            key = digest(
                {
                    "owner": value["owner"],
                    "calibration_dates": value["calibration_dates"],
                    "holdout_dates": value["holdout_dates"],
                }
            )
            cohorts.setdefault(key, []).append(value)
    return cohorts


def frozen_joint_bundle(inputs, *, directory=DIRECTORY):
    """Verify each causal cohort before its own fixed holdout cutoff.

    A later admission must not retroactively change an earlier cohort or move
    its holdout. The joint composition rule is fixed; it never chooses a
    profitable subset after seeing combined outcomes.
    """
    directory = _directory(directory)
    cohorts = _joint_cohorts(inputs)
    if not cohorts:
        return None
    receipts = {}
    for key, revisions in sorted(cohorts.items()):
        try:
            frozen = read_object(Path(directory) / "joint_bundles" / f"{key}.json")
        except FileNotFoundError:
            return None
        body = {k: v for k, v in frozen.items() if k != "bundle_sha256"}
        cutoff = revisions[0]["holdout_dates"][0]
        membership = {v["revision_sha256"] for v in revisions}
        registered = set(frozen.get("members") or [])
        at = datetime.fromisoformat(frozen["frozen_at"])
        if (
            frozen.get("bundle_sha256") != digest(body)
            or not membership <= registered
            or frozen.get("cohort_id") != key
            or frozen.get("first_holdout_date") != cutoff
            or at.tzinfo is None
            or at.date().isoformat() >= cutoff
            or any(frozen.get(k) is not v for k, v in AUTHORITY.items())
            or frozen.get("allocator_rule")
            != "fixed_existing_allocator_no_research_arbitration"
            or frozen.get("selection")
            != "all_registered_members_no_holdout_substitution"
        ):
            raise ValueError("frozen_joint_bundle_invalid")
        # Removed members remain in the immutable manifest. Only explicit
        # source/parent supersession can explain a registry replacement.
        for removed in registered - membership:
            original = read_object(
                Path(directory) / "candidates" / ".history" / f"{removed}.json"
            )
            validate_revision(original)
            if original["revision_sha256"] != removed:
                raise ValueError("joint_cohort_original_revision_missing")
            current = load_candidate(
                original["symbol"],
                owner=original["owner"],
                lane_id=original["lane_id"],
                directory=directory,
            )
            visited = set()
            while current and current["revision_sha256"] != removed:
                identity = current["revision_sha256"]
                if identity in visited:
                    raise ValueError("joint_cohort_supersession_cycle")
                visited.add(identity)
                parent = current.get("supersedes_revision_sha256")
                if not parent:
                    current = None
                    break
                current = validate_revision(
                    read_object(
                        Path(directory) / "candidates" / ".history" / f"{parent}.json"
                    )
                )
            if not current or not visited:
                raise ValueError("joint_cohort_member_pruned_without_supersession")
        receipts[key] = frozen
    body = dict(
        schema=SCHEMA,
        cohort_manifests=receipts,
        members=sorted(
            v["revision_sha256"] for values in cohorts.values() for v in values
        ),
        selection="fixed_joint_composition_of_prespecified_causal_cohorts_no_hindsight_pruning",
        **AUTHORITY,
    )
    return {**body, "bundle_sha256": digest(body)}


def freeze_joint_bundle(inputs, *, directory=DIRECTORY):
    directory = _directory(directory)
    cohorts = _joint_cohorts(inputs)
    if not cohorts:
        return None
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    with writer_lock(Path(directory) / "joint_bundles"):
        for key, revisions in cohorts.items():
            path = Path(directory) / "joint_bundles" / f"{key}.json"
            membership = sorted(v["revision_sha256"] for v in revisions)
            cutoff = revisions[0]["holdout_dates"][0]
            if path.exists():
                old = read_object(path)
                if set(membership) <= set(old.get("members") or []):
                    continue
                if now.date().isoformat() >= cutoff or not set(
                    old.get("members") or []
                ) <= set(membership):
                    raise ValueError("joint_cohort_membership_conflict")
                prior_body = {k: v for k, v in old.items() if k != "bundle_sha256"}
                if old.get("bundle_sha256") != digest(prior_body):
                    raise ValueError("joint_cohort_prior_manifest_invalid")
                atomic_write(
                    Path(directory)
                    / "joint_bundles"
                    / ".history"
                    / f"{old['bundle_sha256']}.json",
                    old,
                )
            if now.date().isoformat() >= cutoff:
                continue
            if any(datetime.fromisoformat(v["frozen_at"]) > now for v in revisions):
                raise ValueError("joint_cohort_candidate_not_yet_registered")
            body = dict(
                schema=SCHEMA,
                cohort_id=key,
                members=membership,
                frozen_at=now.isoformat(),
                first_holdout_date=cutoff,
                allocator_rule="fixed_existing_allocator_no_research_arbitration",
                selection="all_registered_members_no_holdout_substitution",
                **AUTHORITY,
            )
            atomic_write(path, {**body, "bundle_sha256": digest(body)})
    return frozen_joint_bundle(inputs, directory=directory)


def combined_joint_gate(report, *, family, source_date, directory=DIRECTORY):
    directory = _directory(directory)
    own = joint_inputs(report, family=family)
    other_family = "episode" if family == "widget" else "widget"
    try:
        other = read_object(
            Path(directory)
            / f"joint_inputs_{other_family}_{source_date.isoformat()}.json"
        )
        body = {k: v for k, v in other.items() if k != "inputs_sha256"}
        if (
            other.get("schema") != SCHEMA
            or other.get("family") != other_family
            or other.get("source_date") != source_date.isoformat()
            or other.get("inputs_sha256") != digest(body)
            or any(other.get(k) is not v for k, v in AUTHORITY.items())
        ):
            raise ValueError("joint_peer_contract_invalid")
    except (OSError, ValueError, TypeError):
        return dict(
            schema=SCHEMA,
            status="allocation_blocked",
            reason="exact_date_joint_peer_missing_or_invalid",
            feasible_combined_net_profit_krw=None,
            parent_sha256=own["inputs_sha256"],
            **AUTHORITY,
        )
    bundle = frozen_joint_bundle([own, other], directory=directory)
    if (
        own.get("candidate_revisions") or other.get("candidate_revisions")
    ) and bundle is None:
        return dict(
            schema=SCHEMA,
            status="allocation_blocked",
            reason="joint_bundle_not_frozen_before_holdout",
            feasible_combined_net_profit_krw=None,
            **AUTHORITY,
        )
    episodes = {**own["selected_episodes"], **other["selected_episodes"]}
    quote_demand = {}
    for row in own.get("depth_demands", []) + other.get("depth_demands", []):
        prior, available = quote_demand.get(
            row["quote_id"], (0, row["available_quantity"])
        )
        if (
            available != row["available_quantity"]
            or prior + row["stress_quantity"] > available
        ):
            return dict(
                schema=SCHEMA,
                status="allocation_blocked",
                reason="shared_cross_owner_stress_depth_insufficient",
                feasible_combined_net_profit_krw=None,
                **AUTHORITY,
            )
        quote_demand[row["quote_id"]] = prior + row["stress_quantity"], available
    parent = digest(
        {family: own["inputs_sha256"], other_family: other["inputs_sha256"]}
    )
    result = joint_allocation(
        episodes,
        snapshot=load_allocator(source_date, directory=directory),
        source_date=source_date,
        parent_sha256=parent,
    )
    if result["status"] == "pass" and (own.get("candidate_revisions") or other.get("candidate_revisions")):
        from src.engine.monitoring.research_portfolio_economics import paired_joint_economics
        economics = paired_joint_economics([own, other], load_allocator(source_date, directory=directory))
        result["paired_joint_economics"] = economics
        if economics["status"] != "pass":
            result.update(status="allocation_blocked", reason=economics["reason"], feasible_combined_net_profit_krw=None)
    return {
        **result,
        "family_inputs": {
            family: own["inputs_sha256"],
            other_family: other["inputs_sha256"],
        },
        "joint_bundle_sha256": (bundle or {}).get("bundle_sha256"),
        "bundle_selection": "all_individually_qualified_prespecified_seeds_fixed_allocator_no_hindsight_pruning",
    }


def optional_cache_write(
    path, raw, *, cache_root, soft_cap=2 * 1024**3, reserve=10 * 1024**3
):
    """LRU only optional caches, retaining process and persistent pins."""
    from src.engine.monitoring.research_cache_storage import write
    path, cache_root = Path(path), Path(cache_root)
    aggregate = _directory(DIRECTORY) / "cache"
    if path.absolute().is_relative_to(aggregate.absolute()):
        cache_root = aggregate
    return write(path, raw, cache_root=cache_root, soft_cap=soft_cap, reserve=reserve)


def version_economics(rows, *, strategy_revision=False):
    """Return exact realized costs per original version; unresolved stays null."""
    versions, identities = {}, set()
    for row in rows:
        version = (row.get("signal_features") or {}).get(
            "runtime_policy_hash"
        ) or row.get("execution_policy_content_sha256")
        original_version = version
        if strategy_revision:
            version = (row.get("signal_features") or {}).get(
                "candidate_revision_sha256"
            ) or row.get("candidate_revision_sha256")
        identity = (
            row.get("native_attempt_id") or row.get("profile_id"),
            row.get("target_date"),
            original_version,
        )
        if identity in identities:
            raise ValueError("duplicate_native_version_outcome")
        identities.add(identity)
        key = version or "unattributed_version"
        bucket = versions.setdefault(
            key,
            dict(
                profile_ids=[],
                exact_completed_legs=0,
                first_source_date=row.get("target_date"),
                last_source_date=row.get("target_date"),
                decision_count=0,
                attempted_count=0,
                exact_completed_count=0,
                missing_cost_or_terminal_count=0,
                realized_net_profit_krw=None,
                realized_buy_notional_krw=None,
                realized_net_return_pct=None,
            ),
        )
        if row.get("profile_id") not in bucket["profile_ids"]:
            bucket["profile_ids"].append(row.get("profile_id"))
        bucket["last_source_date"] = row.get("target_date")
        bucket["decision_count"] += 1
        bucket["attempted_count"] += bool(row.get("attempted"))
        economics = row.get("broker_realized_economics") or {}
        complete = (
            row.get("outcome_complete_for_ev") is True
            and row.get("source_quality") == "pass"
            and row.get("eligible_for_tuning") is True
        )
        fields = (
            "realized_net_profit_krw",
            "buy_notional_krw",
            "commission_krw",
            "tax_krw",
            "realized_net_return_pct",
        )
        valid = all(
            type(economics.get(k)) in (int, float) and math.isfinite(economics[k])
            for k in fields
        )
        if (
            version
            and complete
            and economics.get("status") == "matched_exact"
            and valid
            and economics["buy_notional_krw"] > 0
            and economics["commission_krw"] >= 0
            and economics["tax_krw"] >= 0
        ):
            bucket["exact_completed_count"] += 1
            bucket["exact_completed_legs"] += sum(
                leg.get("completed") is True for leg in row.get("legs", [])
            )
            bucket["realized_net_profit_krw"] = (
                bucket["realized_net_profit_krw"] or 0
            ) + economics["realized_net_profit_krw"]
            bucket["realized_buy_notional_krw"] = (
                bucket["realized_buy_notional_krw"] or 0
            ) + economics["buy_notional_krw"]
            bucket["realized_net_return_pct"] = (
                bucket["realized_net_profit_krw"]
                / bucket["realized_buy_notional_krw"]
                * 100
            )
        elif row.get("attempted"):
            bucket["missing_cost_or_terminal_count"] += 1
    return dict(
        schema=SCHEMA,
        versions=versions,
        economic_basis="actual_exact_cost_completed_only_CF_separate",
        strategy_revisions={}
        if strategy_revision
        else version_economics(rows, strategy_revision=True)["versions"],
        **AUTHORITY,
    )
