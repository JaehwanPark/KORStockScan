"""Bounded, generation keyed facts shared by seed-specific research readers.

The cache has a fixed byte budget. It never manufactures old seeds
or changes quote clocks, quantities, venue, session, or execution semantics.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
from collections import OrderedDict
from threading import RLock

_CACHE = OrderedDict()
_CACHE_BYTES = 0
MAX_CACHE_BYTES = 32 * 1024 * 1024
_LOCK = RLock()
MAX_BYTES = 64 * 1024 * 1024
COUNTERS = dict(full_decodes=0, cache_hits=0, decoded_bytes=0, point_decodes=0)
_INDEX = OrderedDict()
_INDEX_BYTES = 0


_INDEX_CODE_SHA = hashlib.sha256(
    Path(__file__).read_bytes()
    + Path(__file__).with_name("research_fact_archive.py").read_bytes()
).hexdigest()


def _persisted_index(path, source_generation, value=None):
    """Optional writer-issued raw digest/index; never replace original facts."""
    import base64
    import zlib
    import sys
    from array import array
    from src.engine.monitoring import research_closed_loop as loop
    from src.utils.constants import DATA_DIR

    if not path.resolve().is_relative_to(DATA_DIR.resolve()):
        return None
    root = loop._directory(loop.DIRECTORY) / "cache"
    key = loop.digest([str(path.resolve()), source_generation, _INDEX_CODE_SHA])
    target = root / "fact_indexes" / f"{key}.json.z"
    if value is not None:
        sha, clocks, offsets, _ = value
        body = dict(
            source_sha256=sha,
            generation=source_generation,
            algorithm_sha256=_INDEX_CODE_SHA,
            byte_order=sys.byteorder,
            clocks=base64.b64encode(clocks.tobytes()).decode("ascii"),
            offsets=base64.b64encode(offsets.tobytes()).decode("ascii"),
        )
        raw = json.dumps(
            {**body, "index_sha256": loop.digest(body)}, sort_keys=True
        ).encode()
        if len(raw) <= 8 * 1024 * 1024:
            try:
                loop.optional_cache_write(target, zlib.compress(raw), cache_root=root)
            except (OSError, ValueError):
                pass
        return None
    try:
        before = target.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 4 * 1024 * 1024:
            return None
        fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            raw = handle.read(4 * 1024 * 1024 + 1)
            if generation(os.fstat(handle.fileno())) != generation(before):
                return None
        decoder = zlib.decompressobj()
        raw = decoder.decompress(raw, 8 * 1024 * 1024)
        if not decoder.eof or decoder.unused_data:
            return None
        body = json.loads(raw)
        expected = body.pop("index_sha256")
        if (
            expected != loop.digest(body)
            or body["generation"] != list(source_generation)
            or body["algorithm_sha256"] != _INDEX_CODE_SHA
            or body["byte_order"] != sys.byteorder
        ):
            return None
        clocks, offsets = array("d"), array("Q")
        clocks.frombytes(base64.b64decode(body["clocks"], validate=True))
        offsets.frombytes(base64.b64decode(body["offsets"], validate=True))
        if (
            len(clocks) != len(offsets)
            or len(clocks) * 16 + 1024 > MAX_CACHE_BYTES
            or any(not math.isfinite(clock) for clock in clocks)
            or any(a > b for a, b in zip(clocks, clocks[1:]))
            or any(a >= b for a, b in zip(offsets, offsets[1:]))
            or any(
                (offset >> (8 if path.suffix == ".zfb" else 0)) >= source_generation[2]
                for offset in offsets
            )
        ):
            return None
        return body["source_sha256"], clocks, offsets, len(clocks) * 16 + 1024
    except (OSError, ValueError, TypeError, KeyError, zlib.error):
        return None


def source_integrity(path):
    path = Path(path)
    original = path.name.removesuffix(".zfb")
    marker = path.with_name(
        original.replace("prospective_facts_", "source_gap_", 1).replace(
            ".jsonl", ".json"
        )
    )
    if marker != path and os.path.lexists(marker):
        raise ValueError("native_book_identity_conflict_scope")
    return True


def indexed_day_facts(path, *, windows):
    """Audit a frozen file once, then decode only requested causal intervals.

    Offsets, rather than decoded books, are shared by seed readers. The index
    is bounded separately; eviction causes a fresh audit, never a weaker check.
    """
    from array import array
    from bisect import bisect_left, bisect_right
    from datetime import datetime
    from types import MappingProxyType

    global _INDEX_BYTES, _CACHE_BYTES
    path = Path(path)
    source_integrity(path)
    with _LOCK:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise ValueError("research_facts_not_bounded_regular_file")
        key = str(path.absolute()), generation(before)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as handle:
            if path.suffix == ".zfb":
                from src.engine.monitoring.research_fact_archive import FactReader

                handle = FactReader(handle)
            if generation(os.fstat(handle.fileno())) != key[1]:
                raise ValueError("research_facts_open_generation_changed")
            persisted = _persisted_index(path, key[1]) if key not in _INDEX else None
            if persisted is not None:
                while _INDEX and _INDEX_BYTES + persisted[3] > MAX_CACHE_BYTES:
                    _INDEX_BYTES -= _INDEX.popitem(last=False)[1][3]
                _INDEX[key] = persisted
                _INDEX_BYTES += persisted[3]
            if key not in _INDEX:
                clocks, offsets = array("d"), array("Q")
                sha = hashlib.sha256()
                total = 0
                last = float("-inf")
                previous_offset = handle.tell()
                while line := handle.readline(MAX_BYTES + 1):
                    offset = previous_offset
                    total += len(line)
                    if total > MAX_BYTES:
                        raise ValueError("research_facts_growing_source")
                    sha.update(line)
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("research_facts_record_not_object")
                    clock = datetime.fromisoformat(row["observed_at_kst"])
                    if clock.tzinfo is None or not math.isfinite(clock.timestamp()):
                        raise ValueError("research_facts_clock_invalid")
                    if clock.timestamp() < last:
                        raise ValueError("research_facts_clock_regression")
                    last = clock.timestamp()
                    clocks.append(last)
                    offsets.append(offset)
                    previous_offset = handle.tell()
                charge = len(clocks) * 16 + 1024
                if charge > MAX_CACHE_BYTES:
                    raise ValueError("research_facts_index_budget_exceeded")
                for old in list(_INDEX):
                    if old[0] == key[0]:
                        _INDEX_BYTES -= _INDEX.pop(old)[3]
                while _INDEX and _INDEX_BYTES + charge > MAX_CACHE_BYTES:
                    _INDEX_BYTES -= _INDEX.popitem(last=False)[1][3]
                _INDEX[key] = sha.hexdigest(), clocks, offsets, charge
                _INDEX_BYTES += charge
                _persisted_index(path, key[1], _INDEX[key])
                COUNTERS["full_decodes"] += 1
                COUNTERS["decoded_bytes"] += total
            else:
                COUNTERS["cache_hits"] += 1
            _INDEX.move_to_end(key)
            sha, clocks, offsets, _ = _INDEX[key]
            positions = set()
            for start, end in windows:
                if start.tzinfo is None or end.tzinfo is None or end < start:
                    raise ValueError("research_facts_window_invalid")
                positions.update(
                    range(
                        bisect_left(clocks, start.timestamp()),
                        bisect_right(clocks, end.timestamp()),
                    )
                )

            def freeze(value):
                if isinstance(value, dict):
                    return MappingProxyType({k: freeze(v) for k, v in value.items()})
                if isinstance(value, list):
                    return tuple(freeze(v) for v in value)
                return value

            rows = []
            charged = 0
            for index in sorted(positions):
                point_key = (*key, index)
                if point_key in _CACHE:
                    cached = _CACHE[point_key]
                    charged += cached[2]
                    if charged > MAX_CACHE_BYTES:
                        raise ValueError(
                            "research_facts_selected_window_budget_exceeded"
                        )
                    _CACHE.move_to_end(point_key)
                    rows.append(cached[1][0])
                    continue
                handle.seek(offsets[index])
                line = handle.readline(MAX_BYTES + 1)
                charge = len(line) * 8 + 512
                charged += charge
                if charged > MAX_CACHE_BYTES:
                    raise ValueError("research_facts_selected_window_budget_exceeded")
                row = freeze(json.loads(line))
                COUNTERS["point_decodes"] += 1
                while _CACHE and _CACHE_BYTES + charge > MAX_CACHE_BYTES:
                    _CACHE_BYTES -= _CACHE.popitem(last=False)[1][2]
                _CACHE[point_key] = sha, (row,), charge
                _CACHE_BYTES += charge
                rows.append(row)
            if (
                generation(os.fstat(handle.fileno())) != key[1]
                or generation(path.lstat()) != key[1]
            ):
                raise ValueError("research_facts_read_generation_changed")
            return sha, tuple(rows)


def generation(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def completed_day_facts(path):
    """Return immutable raw JSON bytes with digest, decoded only once/generation.

    Files with malformed records are rejected, never silently dropped. The
    returned rows are immutable so a seed cannot mutate another.
    """
    global _CACHE_BYTES
    path = Path(path)
    source_integrity(path)
    with _LOCK:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise ValueError("research_facts_not_bounded_regular_file")
        key = str(path.absolute()), generation(before)
        if key in _CACHE:
            COUNTERS["cache_hits"] += 1
            _CACHE.move_to_end(key)
            return _CACHE[key][0], _CACHE[key][1]
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        raw_hash = hashlib.sha256()
        rows = []
        cache_bytes = 0
        with os.fdopen(fd, "rb") as handle:
            if generation(os.fstat(handle.fileno())) != generation(before):
                raise ValueError("research_facts_open_generation_changed")
            total = 0
            for line in handle:
                total += len(line)
                if total > MAX_BYTES:
                    raise ValueError("research_facts_growing_source")
                raw_hash.update(line)
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("research_facts_record_not_object")
                value = {
                    field: value[field]
                    for field in (
                        "symbol",
                        "observed_at_kst",
                        "observation_role",
                        "advisory_generated",
                        "observation_seed",
                        "advisory",
                        "bbo",
                        "market_venue",
                        "seed_memberships",
                        "producer_code_sha256",
                        "schema",
                        "source_quality_status",
                        "source_gap_reasons",
                        "source_epoch",
                        "source_sequence",
                        "market_session",
                        "runtime_effect",
                        "allowed_runtime_apply",
                        "actual_order_submitted",
                        "broker_order_forbidden",
                    )
                    if field in value
                }
                advisory = value.get("advisory")
                if isinstance(advisory, dict):
                    value["advisory"] = {
                        k: advisory[k]
                        for k in ("session", "state", "source_quality")
                        if k in advisory
                    }
                # Charge Python container/string overhead conservatively.
                import sys

                def size(item):
                    return sys.getsizeof(item) + (
                        sum(sys.getsizeof(k) + size(v) for k, v in item.items())
                        if isinstance(item, dict)
                        else sum(size(v) for v in item)
                        if isinstance(item, list)
                        else 0
                    )

                cache_bytes += size(value) + 256
                rows.append(value)
            if generation(os.fstat(handle.fileno())) != generation(before):
                raise ValueError("research_facts_read_generation_changed")
        if generation(path.lstat()) != generation(before):
            raise ValueError("research_facts_path_generation_changed")
        # Seed consumers only read these values; do not expose mutable rows.
        from types import MappingProxyType

        def freeze(value):
            if isinstance(value, dict):
                return MappingProxyType({k: freeze(v) for k, v in value.items()})
            if isinstance(value, list):
                return tuple(freeze(v) for v in value)
            return value

        facts = tuple(freeze(value) for value in rows)
        sha = raw_hash.hexdigest()
        if cache_bytes <= MAX_CACHE_BYTES:
            for old in list(_CACHE):
                if old[0] == key[0]:
                    _CACHE_BYTES -= _CACHE.pop(old)[2]
            while _CACHE and _CACHE_BYTES + cache_bytes > MAX_CACHE_BYTES:
                _, removed = _CACHE.popitem(last=False)
                _CACHE_BYTES -= removed[2]
            _CACHE[key] = sha, facts, cache_bytes
            _CACHE_BYTES += cache_bytes
        COUNTERS["full_decodes"] += 1
        COUNTERS["decoded_bytes"] += total
        return sha, facts


def normalized_shared_books(snapshot, *, now, symbols):
    """Consume the existing normalized WS contract; never change subscriptions."""
    from collections.abc import Mapping
    from datetime import datetime
    from src.trading.market.micro_confirmation import LIVE_SNAPSHOT_SCHEMA

    from datetime import time
    from src.utils.market_day import is_krx_trading_day

    if not is_krx_trading_day(now.date()) or not time(9, 0) <= now.time().replace(
        tzinfo=None
    ) <= time(15, 20):
        return []
    contract = snapshot.get("machine_confirmation_input_contract") or {}
    if (
        snapshot.get("schema_version") != "kiwoom_ws_dashboard_snapshot_v1"
        or snapshot.get("decision_authority") != "source_quality_only"
        or snapshot.get("runtime_effect") is not False
        or contract.get("schema") != LIVE_SNAPSHOT_SCHEMA
        or contract.get("exact_route_required") is not True
        or contract.get("causal_past_only") is not True
        or contract.get("runtime_effect") is not False
        or contract.get("decision_authority")
        != "market_data_input_only_no_order_authority"
        or contract.get("actual_order_submitted") is not False
        or contract.get("broker_order_forbidden") is not True
    ):
        return []
    output = []
    for symbol in sorted(symbols):
        stock = (snapshot.get("stocks") or {}).get(symbol) or {}
        for route in (stock.get("machine_confirmation_routes") or {}).values():
            if not isinstance(route, Mapping):
                continue
            types = route.get("realtime_types") or {}
            trade, depth = types.get("0B") or {}, types.get("0D") or {}
            epoch = depth.get("transport_epoch")
            if (
                type(epoch) is not int
                or epoch <= 0
                or trade.get("transport_epoch") != epoch
                or trade.get("item") != symbol
                or depth.get("item") != symbol
            ):
                continue
            for book in route.get("recent_depth") or []:
                if (
                    not isinstance(book, Mapping)
                    or book.get("item") != symbol
                    or book.get("transport_epoch") != epoch
                    or type(book.get("route_sequence")) is not int
                ):
                    continue
                clock = book.get("received_at_ms")
                if (
                    type(clock) is not int
                    or not 0 <= now.timestamp() * 1000 - clock <= 5000
                ):
                    continue
                if (
                    any(
                        type(book.get(key)) not in (int, float)
                        or not math.isfinite(book[key])
                        or book[key] <= 0
                        for key in (
                            "best_bid",
                            "best_ask",
                            "best_bid_qty",
                            "best_ask_qty",
                        )
                    )
                    or book["best_bid"] > book["best_ask"]
                ):
                    continue
                output.append(
                    dict(
                        symbol=symbol,
                        market_venue="KRX",
                        market_session="KRX_REGULAR",
                        source_epoch=epoch,
                        source_sequence=book["route_sequence"],
                        observed_at_kst=datetime.fromtimestamp(
                            clock / 1000, tz=now.tzinfo
                        ).isoformat(),
                        bbo={
                            **{
                                key: book[key]
                                for key in (
                                    "best_bid",
                                    "best_ask",
                                    "best_bid_qty",
                                    "best_ask_qty",
                                )
                            },
                            "received_at": datetime.fromtimestamp(
                                clock / 1000, tz=now.tzinfo
                            ).isoformat(),
                            "source_epoch": epoch,
                            "source_sequence": book["route_sequence"],
                        },
                    )
                )
    return output


class SharedResearchFactWriter:
    """Poll already subscribed WS rows within an existing order-free worker.

    Sparse REST collection remains a raw chart source. This writer has zero
    remote calls and records only currently available exact KRX book facts for
    seeds registered before the fact clock. Missing scope is explicit defer.
    """

    def __init__(self, symbols, *, directory=None, snapshot_path=None):
        from src.engine.monitoring.research_closed_loop import DIRECTORY

        self.symbols = set(symbols)
        self.directory = Path(directory or DIRECTORY)
        self.snapshot_path = snapshot_path
        self.seen = {}
        self.native_books = {}
        self.conflicts = set()
        self.capture_day = None
        self.revisions = {}
        self.buckets = {}
        self.code_sha256 = _INDEX_CODE_SHA
        self.sealed_day = None
        self.refresh_at = None

    def collect_once(self, now):
        from src.engine.monitoring import research_closed_loop as loop
        from src.trading.market.micro_confirmation import _live_snapshot_path

        if self.capture_day != now.date():
            self.capture_day = now.date()
            self.conflicts = {
                p.name.split("_")[2]
                for p in (self.directory / "facts").glob(
                    f"source_gap_*_{now:%Y%m%d}.json"
                )
            }
            self.native_books.clear()
        if self.refresh_at is None or (now - self.refresh_at).total_seconds() >= 30:
            self.symbols.update(
                loop.admission_symbols(
                    now.date(), owner="widget", directory=self.directory
                )
            )
            self.symbols.update(
                loop.admission_symbols(
                    now.date(), owner="episode", directory=self.directory
                )
            )
            revisions = {}
            for path in (self.directory / "candidates").glob("*.json"):
                value = loop.validate_revision(loop.read_object(path))
                # Existing actual profiles already have an episode owner. A
                # registered paired seed consumes their received native books;
                # this adds no subscription, polling or order permission.
                if value["owner"] == "episode":
                    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
                    native = profiles_for_target_date(now.date()).get(value["lane_id"])
                    if (native is not None and native.symbol == value["symbol"]
                            and value.get("baseline_policy_id") == native.profile_id
                            and native.entry_runtime_eligible
                            and value["calibration_dates"][0] <= now.date().isoformat() <= value["holdout_dates"][-1]):
                        self.symbols.add(value["symbol"])
                if (
                    value["symbol"] in self.symbols
                    and value["calibration_dates"][0]
                    <= now.date().isoformat()
                    <= value["holdout_dates"][-1]
                ):
                    revisions.setdefault(value["symbol"], []).append(value)
            self.revisions = revisions
            self.refresh_at = now
        try:
            snapshot = loop.read_object(
                _live_snapshot_path(self.snapshot_path), limit=8 * 1024 * 1024
            )
        except (OSError, ValueError, TypeError):
            snapshot = {}
        from datetime import time

        if (
            now.time().replace(tzinfo=None) > time(15, 21)
            and self.sealed_day != now.date()
        ):
            for path in sorted(
                (self.directory / "facts").glob(
                    f"prospective_facts_*_{now:%Y%m%d}.jsonl"
                )
            ):
                try:
                    source_sha, _ = indexed_day_facts(path, windows=[])
                    old_key = str(path.absolute()), generation(path.lstat())
                    prior = _INDEX.get(old_key)
                    from array import array
                    from src.engine.monitoring.research_fact_archive import (
                        seal_fact_file,
                    )

                    offsets = array("Q")
                    archived = seal_fact_file(
                        path, offsets=offsets, expected_sha256=source_sha
                    )
                    if prior is not None and len(offsets) == len(prior[1]):
                        value = source_sha, prior[1], offsets, prior[3]
                        _persisted_index(archived, generation(archived.lstat()), value)
                except (OSError, ValueError, KeyError, TypeError):
                    symbol = path.name.split("_")[2]
                    self.conflicts.add(symbol)
                    loop.atomic_write(
                        self.directory
                        / "facts"
                        / f"source_gap_{symbol}_{now:%Y%m%d}.json",
                        dict(
                            status="source_gap",
                            reason="sealed_source_integrity_gap",
                            **loop.AUTHORITY,
                        ),
                    )
            self.sealed_day = now.date()
        books = normalized_shared_books(snapshot, now=now, symbols=self.revisions)
        for book in books:
            symbol = book["symbol"]
            identity = book["source_epoch"], book["source_sequence"]
            value = loop.digest(book["bbo"])
            history = self.native_books.setdefault(symbol, OrderedDict())
            old = history.get(identity)
            if old is not None and old != value:
                self.conflicts.add(symbol)
                loop.atomic_write(
                    self.directory / "facts" / f"source_gap_{symbol}_{now:%Y%m%d}.json",
                    dict(
                        status="source_gap",
                        reason="native_book_identity_conflict",
                        symbol=symbol,
                        source_date=str(now.date()),
                        identity=list(identity),
                        **loop.AUTHORITY,
                    ),
                )
            history[identity] = value
            history.move_to_end(identity)
            while len(history) > 64:
                history.popitem(last=False)
        books = [book for book in books if book["symbol"] not in self.conflicts]
        written, available = 0, {book["symbol"] for book in books}
        sampled = {}
        for book in books:
            bucket = (
                book["symbol"],
                book["source_epoch"],
                book["observed_at_kst"][:19],
            )
            if (
                bucket not in sampled
                or book["source_sequence"] > sampled[bucket]["source_sequence"]
            ):
                sampled[bucket] = book
        for book in sorted(
            sampled.values(),
            key=lambda value: (
                value["symbol"],
                value["source_epoch"],
                value["source_sequence"],
            ),
        ):
            symbol = book["symbol"]
            identity = book["source_epoch"], book["source_sequence"]
            previous = self.seen.get(symbol)
            if (
                previous is not None
                and identity[0] == previous[0]
                and identity[1] <= previous[1]
            ):
                continue
            at = book["observed_at_kst"]
            bucket = (identity[0], at[:19])
            if self.buckets.get(symbol) == bucket:
                continue
            memberships = [
                {
                    "revision_sha256": value["revision_sha256"],
                    "parameters_sha256": value["parameters_sha256"],
                    "owner": value["owner"],
                    "lane_id": value["lane_id"],
                    "frozen_at": value["frozen_at"],
                }
                for value in self.revisions.get(symbol, [])
                if value["frozen_at"] < at
                and value["calibration_dates"][0] + "T09:03:00+09:00" <= at
            ]
            if not memberships:
                continue
            book.update(
                schema="prospective_registered_seed_market_facts_v1",
                seed_memberships=memberships,
                observation_role="prospective_registered_seed_market_fact",
                advisory_generated=False,
                source_quality_status="PASS",
                source_gap_reasons=[],
                producer_code_sha256=self.code_sha256,
                writer_pid=os.getpid(),
                capture_precision="one_native_depth_checkpoint_per_second",
                sequence_authority="local_projection_continuity_not_exchange_completeness",
                **loop.AUTHORITY,
            )
            path = (
                self.directory
                / "facts"
                / f"prospective_facts_{symbol}_{now:%Y%m%d}.jsonl"
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            import shutil

            if shutil.disk_usage(path.parent).free < 10 * 1024**3:
                available.discard(symbol)
                continue
            fd = os.open(
                path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600
            )
            with os.fdopen(fd, "a") as handle:
                import fcntl

                fcntl.flock(handle, fcntl.LOCK_EX)
                handle.write(json.dumps(book, sort_keys=True, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.seen[symbol] = identity
            self.buckets[symbol] = bucket
            available.add(symbol)
            written += 1
        receipt = dict(
            schema=loop.SCHEMA,
            status="complete" if snapshot else "waiting",
            reason="existing_ws_scope_checked"
            if snapshot
            else "existing_shared_ws_source_missing",
            source_date=now.date().isoformat(),
            observed_at=now.isoformat(),
            writer_pid=os.getpid(),
            admitted_symbol_count=len(self.symbols),
            active_seed_symbol_count=len(self.revisions),
            raw_only_symbols=sorted(self.symbols - set(self.revisions)),
            written_facts=written,
            remote_requests=0,
            capture_precision="one_native_depth_checkpoint_per_second",
            deferred_symbols=sorted(set(self.revisions) - available)
            if now.time().replace(tzinfo=None) <= time(15, 21)
            else [],
            source_gap_symbols=sorted(self.conflicts),
            completed_day_sealed=self.sealed_day == now.date(),
            capacity_role="existing_ws_scope_only_no_new_subscription_or_rest_budget",
            **loop.AUTHORITY,
        )
        # A bounded summary is the capacity owner; raw facts stay append-only.
        if (
            getattr(self, "receipt_at", None) is None
            or (now - self.receipt_at).total_seconds() >= 30
        ):
            loop.atomic_write(self.directory / f"capacity_{now:%Y-%m-%d}.json", receipt)
            self.receipt_at = now
        return receipt

    def run(self, stop):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        while not stop.is_set():
            try:
                self.collect_once(datetime.now(ZoneInfo("Asia/Seoul")))
            except (OSError, ValueError, TypeError, KeyError):
                print("research_shared_fact_writer_source_gap", flush=True)
            stop.wait(1)
