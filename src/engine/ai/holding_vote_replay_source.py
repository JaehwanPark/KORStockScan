"""Original holding request references and pre-signal replay evidence.

AI owns this source adapter. It adds no provider call or execution authority.
Full requests remain in the existing evidence writer; quotes carry references.
"""

from functools import lru_cache
from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from .holding_exit_vote import (
    path_vote_store_path,
    path_signal_snapshot,
    path_vote_input_hashes,
    input_snapshot_id,
    validate_path_policy,
    iter_path_events_file,
)

SCHEMA = "holding_pre_signal_replay_source_v1"
PROCESS_STARTED_AT = time.time()


def begin_coverage(stock, now, *, generation=None):
    """Current-PID native fills prove no pre-birth vote could have existed.

    Restarted holdings start at observed collection, never a historical clock.
    A new ADD generation starts at its last native fill, preserving the old pin.
    """
    from .holding_exit_vote import (
        buy_fill_legs_from_runtime,
        buy_fill_identity_from_runtime,
    )

    generation = generation or buy_fill_identity_from_runtime(stock)
    if (
        stock.get("holding_vote_coverage_generation") == generation
        and stock.get("holding_vote_coverage_pid") == os.getpid()
    ):
        stock["holding_vote_coverage_checked_at"] = now
        return
    birth = None
    try:
        legs = buy_fill_legs_from_runtime(stock)
        # Native identity legs contain order/execution/quantity, not clocks.
        # The receipt consumer sets these position clocks when accepting BUY.
        entry_orders = stock.get("_entry_receipt_filled_by_order_no") or {}
        has_add = bool(
            stock.get("_add_receipt_filled_by_order_no")
            or any(
                leg.get("order_no") not in entry_orders
                for leg in (stock.get("holding_buy_fill_legs") or [])
            )
        )
        stamp = stock.get("last_add_at") if has_add else stock.get("buy_time")
        if isinstance(stamp, str):
            stamp = datetime.fromisoformat(stamp)
        if (
            isinstance(stamp, datetime)
            and generation
            and legs
            and sum(leg["qty"] for leg in legs) == stock.get("buy_qty")
            and (has_add or not stock.get("holding_vote_coverage_generation"))
        ):
            birth = (
                stamp.replace(tzinfo=ZoneInfo("Asia/Seoul"))
                if stamp.tzinfo is None
                else stamp
            ).timestamp()
    except (ValueError, TypeError, KeyError, OverflowError):
        pass
    proven_birth = birth is not None and PROCESS_STARTED_AT <= birth <= now
    stock.update(
        holding_vote_coverage_started_at=birth if proven_birth else now,
        holding_vote_coverage_birth_at=birth if proven_birth else None,
        holding_vote_coverage_generation=generation,
        holding_vote_coverage_checked_at=now,
        holding_vote_coverage_pid=os.getpid(),
    )


@lru_cache(maxsize=128)
def _store_name(position_key):
    # This is only a deterministic basename, never a cached file or policy.
    return path_vote_store_path(Path("."), position_key).name


def runtime_source(
    stock,
    *,
    position_key,
    buy_fill_identity,
    market,
    now,
    policy,
    data_root,
    model,
    path_id="EXIT_TRAILING_TP",
):
    """No IO: use the collector's already observed state and original policy."""
    ledger = stock.get("holding_path_vote_ledger") or []
    return dict(
        schema=SCHEMA,
        required=True,
        path_id=path_id,
        position_key=position_key,
        buy_fill_identity=buy_fill_identity,
        market=market,
        model=model,
        policy=policy,
        policy_sha256=input_snapshot_id(policy),
        store_name=_store_name(position_key),
        coverage_started_at=stock.get("holding_vote_coverage_started_at"),
        coverage_checked_at=stock.get("holding_vote_coverage_checked_at"),
        generation_birth_at=stock.get("holding_vote_coverage_birth_at"),
        collector_pid=stock.get("holding_vote_coverage_pid"),
        coverage_complete=not stock.get("holding_path_vote_store_gap")
        and not stock.get("holding_vote_coverage_store_gap")
        and stock.get("holding_vote_coverage_pid") == os.getpid()
        and bool(re.fullmatch("[0-9a-f]{64}", str(buy_fill_identity)))
        and stock.get("holding_vote_coverage_generation") == buy_fill_identity,
        latest_persisted_at=max(
            (r.get("persisted_at", 0) for r in ledger), default=None
        ),
        observed_at=now,
    )


def _records(path):
    # Existing writer rotates/compresses through its own retention contract.
    import gzip

    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline(2 * 1024 * 1024 + 1)
            if not line:
                break
            if len(line.encode()) > 2 * 1024 * 1024:
                raise ValueError("holding_request_unbounded")
            yield json.loads(line), dict(
                path=str(path.resolve()),
                offset=offset,
                line_sha256=hashlib.sha256(line.encode()).hexdigest(),
            )


def request_source_shadowed(path):
    """A surviving regular original owns its optional compression companion."""
    path = Path(path)
    if not path.name.endswith(".jsonl.gz"):
        return False
    try:
        return stat.S_ISREG(path.with_suffix("").stat(follow_symlinks=False).st_mode)
    except FileNotFoundError:
        return False


def request_source_metadata(path):
    """Native archive receipts describe original bytes; they are not JSONL rows."""
    path = Path(path)
    namespace = path.parent.name
    return (
        namespace
        in {"ai_decision_payloads", "ai_decision_prompts", "ai_decision_requests"}
        and re.fullmatch(
            re.escape(namespace)
            + r"_\d{4}-\d{2}-\d{2}\.jsonl\.gz\.archive_receipt\.json",
            path.name,
        )
        is not None
    )


def original_request_paths(root, namespace, day):
    return tuple(
        path
        for path in sorted(
            (Path(root) / namespace).glob(namespace + "_" + day + ".jsonl*")
        )
        if not request_source_metadata(path) and not request_source_shadowed(path)
    )


def _request_index(root, output, day, sources):
    """One disposable, bounded disk index per original request date."""
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day)):
        raise ValueError("holding_request_date_invalid")
    directory = output / "holding_request_index"
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / (day + ".sqlite")
    db = sqlite3.connect(path)
    db.execute("PRAGMA cache_size=-1024")
    try:
        db.execute(
            "CREATE TABLE IF NOT EXISTS original(kind TEXT,key TEXT,body TEXT,PRIMARY KEY(kind,key)) WITHOUT ROWID"
        )
        db.execute("CREATE TABLE IF NOT EXISTS loaded(generation TEXT)")
        originals = []
        for namespace, stem in (
            ("ai_decision_payloads", "ai_decision_payloads"),
            ("ai_decision_prompts", "ai_decision_prompts"),
            ("ai_decision_requests", "ai_decision_requests"),
        ):
            for original in original_request_paths(root, namespace, day):
                from src.engine.automation.main_trailing_source_store import (
                    input_generation,
                )

                if str(original) not in sources:
                    sources[str(original)] = input_generation(root, original)
                originals.append((str(original), sources[str(original)]))
        generation = input_snapshot_id(originals)
        loaded = db.execute("SELECT generation FROM loaded").fetchone()
        if loaded and loaded[0] != generation:
            db.close()
            raise ValueError("holding_request_index_stale")
        if not db.execute("SELECT 1 FROM loaded").fetchone():
            for namespace, stem, kind, key in (
                (
                    "ai_decision_payloads",
                    "ai_decision_payloads",
                    "payload",
                    "request_envelope_sha256",
                ),
                (
                    "ai_decision_prompts",
                    "ai_decision_prompts",
                    "prompt",
                    "prompt_sha256",
                ),
                (
                    "ai_decision_requests",
                    "ai_decision_requests",
                    "request",
                    "request_id",
                ),
            ):
                for original in original_request_paths(root, namespace, day):
                    before = sources[str(original)]
                    from src.engine.automation import (
                        main_trailing_source_store as indexed,
                    )

                    if before.get("schema") == indexed.SCHEMA + ":generation":
                        selected = indexed.read_rows(
                            root, original, kinds=["holding_" + kind]
                        )
                        records = (
                            (
                                value["row"],
                                dict(
                                    path=reference["path"],
                                    offset=reference["decoded_offset"],
                                    line_sha256=reference["sha256"],
                                    native_source_index_schema=indexed.SCHEMA,
                                ),
                            )
                            for value, reference in selected
                        )
                    else:
                        indexed.claim_legacy_bytes(before["size"])
                        records = _records(original)
                    for row, pointer in records:
                        if row.get("endpoint") != "holding_path_vote":
                            continue
                        content_sha256 = input_snapshot_id(row)
                        encoded = storage.encoded(
                            {
                                **pointer,
                                "generation": before,
                                "content_sha256": content_sha256,
                            }
                        ).decode()
                        prior = db.execute(
                            "SELECT body FROM original WHERE kind=? AND key=?",
                            (kind, row[key]),
                        ).fetchone()
                        if prior and prior[0] != encoded:
                            previous = json.loads(prior[0])
                            previous_sha = previous.get(
                                "content_sha256"
                            ) or input_snapshot_id(_source_row(previous))
                            if previous_sha != content_sha256:
                                raise ValueError("holding_request_alias_conflict")
                        db.execute(
                            "INSERT OR IGNORE INTO original VALUES (?,?,?)",
                            (kind, row[key], encoded),
                        )
                    from src.engine.automation.main_trailing_source_assembler import (
                        source_generation_matches,
                    )

                    if not source_generation_matches(root, day, original, before):
                        raise ValueError("holding_request_changed")
            db.execute("INSERT INTO loaded VALUES (?)", (generation,))
            db.commit()
    except BaseException:
        db.close()
        raise
    return db


@lru_cache(maxsize=128)
def _verified_generation(path, fingerprint):
    generation = byte_generation(Path(path))
    if source_stat(Path(path).stat()) != fingerprint:
        raise ValueError("holding_request_changed")
    return generation


def _source_row(pointer):
    path = Path(pointer["path"])
    if pointer.get("native_source_index_schema"):
        from src.engine.automation.main_trailing_source_store import read_at, SCHEMA

        if pointer["native_source_index_schema"] != SCHEMA:
            raise ValueError("holding_request_index_schema_changed")
        value, raw_sha = read_at(
            path.parent.parent, path, pointer["offset"], pointer["generation"]
        )
        if (
            raw_sha != pointer["line_sha256"]
            or input_snapshot_id(value) != pointer["content_sha256"]
        ):
            raise ValueError("holding_request_reference_invalid")
        return value
    if (
        _verified_generation(str(path), source_stat(path.stat()))
        != pointer["generation"]
    ):
        raise ValueError("holding_request_reference_changed")
    import gzip

    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        handle.seek(pointer["offset"])
        line = handle.readline(2 * 1024 * 1024 + 1)
    if (
        len(line.encode()) > 2 * 1024 * 1024
        or hashlib.sha256(line.encode()).hexdigest() != pointer["line_sha256"]
    ):
        raise ValueError("holding_request_reference_invalid")
    return json.loads(line)


def _verify_projection(projection, vote, *, candidate_position=None):
    ref = vote.get("actual_request_reference") or {}
    if (
        ref.get("schema") != "holding_actual_request_reference_v1"
        or ref.get("replay_exact") is not True
        or not re.fullmatch("[0-9a-f]{64}", str(ref.get("response_sha256")))
    ):
        raise ValueError("holding_actual_request_missing")
    request = _source_row(projection["request"])
    payload = _source_row(projection["payload"])
    prompt = _source_row(projection["prompt"])
    if (
        request.get("request_envelope_sha256") != ref["request_envelope_sha256"]
        or payload.get("request_envelope_sha256") != ref["request_envelope_sha256"]
        or payload.get("prompt_sha256") != ref["prompt_sha256"]
        or payload.get("payload_sha256") != ref["payload_sha256"]
        or not payload.get("replay_exact")
        or not prompt.get("replay_exact")
        or hashlib.sha256(prompt["sanitized_prompt"].encode()).hexdigest()
        != ref["prompt_sha256"]
        or ref["prompt_sha256"] != vote.get("prompt_sha256")
        or not payload.get("holding_provider_contract")
    ):
        raise ValueError("holding_actual_request_contract_invalid")
    raw = payload.get("holding_raw_user_input")
    if (
        not isinstance(raw, str)
        or hashlib.sha256(raw.encode()).hexdigest() != ref["payload_sha256"]
    ):
        raise ValueError("holding_actual_request_bytes_invalid")
    actual = json.loads(raw)
    if (
        actual.get("position_key") != vote["position_key"]
        or actual.get("buy_fill_identity") != vote["buy_fill_identity"]
        or actual.get("market") != vote["market"]
        or actual.get("session_key") != vote["session_key"]
        or vote["path_id"] not in actual.get("requested_paths", [])
        or str((actual.get("source") or {}).get("route")) != str(vote["route"])
        or str((actual.get("source") or {}).get("transport_epoch"))
        != str(vote["transport_epoch"])
        or path_vote_input_hashes(actual, model=vote["model"])["request_payload_sha256"]
        != vote.get("request_payload_sha256")
    ):
        raise ValueError("holding_actual_input_mismatch")
    if actual.get("input_schema") != vote.get("prompt_version"):
        raise ValueError("holding_actual_input_schema_mismatch")
    contract = payload["holding_provider_contract"]
    if (
        contract.get("instructions") != prompt["sanitized_prompt"]
        or contract.get("model") != vote["model"]
    ):
        raise ValueError("holding_provider_definition_mismatch")
    if candidate_position is not None:
        _verify_cf_input_position(actual, vote, candidate_position)


def _verify_cf_input_position(actual, vote, expected):
    """The original request must describe this unchanged initial position.

    The native age producer emits integer seconds. Only the same request
    second is admitted here; an older evaluation-age clock without its own
    original receipt stays unobserved. No timestamp or input is rewritten.
    """

    def finite(value):
        return type(value) in (float, int) and math.isfinite(value)

    if (
        not isinstance(expected, dict)
        or type(expected.get("qty")) is not int
        or expected["qty"] <= 0
        or any(
            not finite(expected.get(key)) or expected[key] <= 0
            for key in ("buy_basis_krw", "entry_at", "first_sell_at")
        )
        or not finite(expected.get("sell_cost_rate"))
        or not 0 <= expected["sell_cost_rate"] < 0.05
        or not finite(vote.get("requested_at"))
        or expected.get("schema") != "cf_original_holding_equivalence_v1"
        or expected.get("sha256")
        != input_snapshot_id({k: v for k, v in expected.items() if k != "sha256"})
        or actual.get("position_key") != expected.get("position_key")
        or actual.get("buy_fill_identity") != expected.get("buy_fill_identity")
        or not expected["entry_at"] <= vote["requested_at"] < expected["first_sell_at"]
    ):
        raise ValueError("cf_holding_request_position_unproven")
    position = actual.get("position")
    flow = actual.get("flow")
    if not isinstance(position, dict) or not isinstance(flow, dict):
        raise ValueError("cf_holding_request_context_shape")
    lifecycle = flow.get("position_lifecycle", {})
    if not isinstance(lifecycle, dict):
        raise ValueError("cf_holding_request_context_shape")
    price = expected["buy_basis_krw"] / expected["qty"]
    for key, target in (
        ("memory_qty", expected["qty"]),
        ("broker_qty", expected["qty"]),
        ("average_entry_price", price),
    ):
        value = lifecycle.get(key)
        if value is not None and (not finite(value) or value != target):
            raise ValueError("cf_holding_request_lifecycle_not_equivalent")
    if (
        not finite(position.get("buy_price"))
        or position["buy_price"] != price
        or not finite(position.get("held_sec"))
        or position["held_sec"] != int(vote["requested_at"] - expected["entry_at"])
        or position.get("reversal_add_state") not in (None, "")
        or position.get("reversal_add_executed_at") not in (None, 0, 0.0, "")
        or any(
            not finite(position.get(key))
            for key in (
                "curr_price",
                "profit_rate",
                "peak_profit",
                "drawdown_from_peak_pct",
            )
        )
        or position["curr_price"] <= 0
    ):
        raise ValueError("cf_holding_request_position_not_equivalent")
    from src.engine.trade_profit import calculate_net_profit_rate

    profit = calculate_net_profit_rate(
        price, position["curr_price"], cost_rate=expected["sell_cost_rate"]
    )
    if (
        position["profit_rate"] != profit
        or position["peak_profit"] < profit
        or abs(
            position["drawdown_from_peak_pct"]
            - max(0.0, position["peak_profit"] - profit)
        )
        > 1e-9
    ):
        raise ValueError("cf_holding_request_profit_not_equivalent")
    if lifecycle.get("scale_in_filled_qty") not in (None, 0):
        raise ValueError("cf_holding_request_add_unmodeled")


def _verified_request(root, output, vote, sources):
    ref = vote.get("actual_request_reference") or {}
    with closing(_request_index(root, output, ref.get("date"), sources)) as db:

        def pointer(kind, key):
            found = db.execute(
                "SELECT body FROM original WHERE kind=? AND key=?", (kind, key)
            ).fetchone()
            if found is None:
                raise ValueError("holding_actual_request_dangling")
            return json.loads(found[0])

        projection = dict(
            request=pointer("request", ref.get("request_id")),
            payload=pointer("payload", ref.get("request_envelope_sha256")),
            prompt=pointer("prompt", ref.get("prompt_sha256")),
        )
    _verify_projection(projection, vote)
    # Immutable byte pointers, no second full-payload comparison ledger.
    return projection


def assemble_votes(root, output, source, sources):
    try:
        if source.get("schema") != SCHEMA:
            raise ValueError("holding_source_schema_invalid")
        path = path_vote_store_path(root, source["position_key"])
        if path.name != source.get("store_name"):
            raise ValueError("holding_vote_path_mismatch")
        if not path.exists() and not list(path.parent.glob(path.name + ".segment-*")):
            raise ValueError("holding_vote_store_missing")
        from datetime import datetime
        from zoneinfo import ZoneInfo

        source_date = (
            datetime.fromtimestamp(source["observed_at"], ZoneInfo("Asia/Seoul"))
            .date()
            .isoformat()
            if source.get("observed_at") is not None
            else None
        )
        from src.engine.automation.main_trailing_source_store import (
            vote_rows,
            scoped_vote_generation,
            InputPending,
            claim_legacy_bytes,
        )

        def original_votes():
            # Prove complete index coverage before emitting any row. A later
            # typed index failure is not allowed to duplicate an emitted prefix.
            try:
                bound = (
                    scoped_vote_generation(root, path, source_date)
                    if source_date
                    else None
                )
            except InputPending:
                bound = None
            if bound is not None:
                sources[str(path)] = bound
                yield from vote_rows(
                    root, path, source["position_key"], source_date=source_date
                )
                return
            for segment in sorted(path.parent.glob(path.name + ".segment-*")) + [path]:
                if not segment.exists():
                    continue
                before = byte_generation(segment)
                sources[str(segment)] = before
                claim_legacy_bytes(before["size"])
                yield from iter_path_events_file(segment, source["position_key"])
                if byte_generation(segment) != before:
                    raise ValueError("holding_vote_segment_changed")

        def rows():
            for vote in original_votes():
                if source.get("path_id", "EXIT_TRAILING_TP") is not None and vote.get(
                    "path_id"
                ) != source.get("path_id", "EXIT_TRAILING_TP"):
                    continue
                try:
                    ref = (
                        _verified_request(root, output, vote, sources)
                        if vote["status"] == "VALID"
                        else None
                    )
                    yield {
                        **vote,
                        "actual_input_ref": ref,
                        "actual_input_verified": ref is not None,
                    }
                except (ValueError, OSError, KeyError, TypeError):
                    yield {**vote, "actual_input_verified": False}

        reference = storage.write_tree(output, rows())
        return dict(
            schema=SCHEMA,
            root=str(output.resolve()),
            events_ref=reference,
            original_position_key=source["position_key"],
            status="source_bound",
        )
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return dict(schema=SCHEMA, status="source_gap", reason=str(exc))


class PreparedVotes:
    def __init__(self, reference, scratch):
        self.reference = reference
        self.db = None
        if not reference or reference.get("status") != "source_bound":
            return
        self.db = sqlite3.connect(Path(scratch) / "holding-votes.sqlite")
        self.db.execute("PRAGMA cache_size=-1024")
        self.db.execute("CREATE TABLE votes(at REAL,body TEXT)")
        for row in storage.iter_tree(reference["root"], reference["events_ref"]):
            if row["status"] == "VALID" and row.get("actual_input_verified"):
                try:
                    _verify_projection(
                        row["actual_input_ref"],
                        row,
                        candidate_position=reference.get(
                            "candidate_position_equivalence"
                        ),
                    )
                except (ValueError, OSError, KeyError, TypeError):
                    row = {**row, "actual_input_verified": False}
            self.db.execute(
                "INSERT INTO votes VALUES (?,?)",
                (row["requested_at"], storage.encoded(row).decode()),
            )
        self.db.execute("CREATE INDEX vote_clock ON votes(at)")

    def snapshot(
        self,
        source,
        signal_at,
        *,
        market,
        route,
        epoch,
        entry_at,
        candidate_policy=None,
    ):
        if (
            self.db is None
            or not isinstance(source, dict)
            or source.get("schema") != SCHEMA
            or source.get("position_key") != self.reference["original_position_key"]
            or source.get("coverage_complete") is not True
            or not validate_path_policy(
                source.get("policy"), path_id=source.get("path_id", "EXIT_TRAILING_TP")
            )
            or source.get("policy_sha256") != input_snapshot_id(source["policy"])
            or source.get("market") != market
        ):
            raise ValueError("holding_vote_coverage_missing")
        policy = candidate_policy or source["policy"]
        if not validate_path_policy(
            policy, path_id=source.get("path_id", "EXIT_TRAILING_TP")
        ):
            raise ValueError("holding_vote_candidate_policy_invalid")
        start, checked = source.get("coverage_started_at"), source.get(
            "coverage_checked_at"
        )
        observed = source.get("observed_at")
        if (
            any(
                not isinstance(clock, (int, float))
                or isinstance(clock, bool)
                or not math.isfinite(clock)
                for clock in (start, checked, observed)
            )
            or start
            > max(
                entry_at,
                source.get("generation_birth_at") or entry_at,
                signal_at - policy["window_sec"],
            )
            or not start <= checked <= observed <= signal_at
            or observed - checked > policy["max_gap_sec"]
        ):
            raise ValueError("holding_vote_coverage_window_unobserved")
        window = (signal_at - policy["window_sec"], signal_at)
        size, count = self.db.execute(
            "SELECT COALESCE(SUM(length(body)),0),COUNT(*) FROM votes WHERE at>=? AND at<?",
            window,
        ).fetchone()
        with Claim(size * 8 + count * 1024):
            return self._snapshot_window(
                source, signal_at, market, route, epoch, window, candidate_policy=policy
            )

    def _snapshot_window(
        self, source, signal_at, market, route, epoch, window, *, candidate_policy=None
    ):
        policy = candidate_policy or source["policy"]
        rows = [
            json.loads(body)
            for body, in self.db.execute(
                "SELECT body FROM votes WHERE at>=? AND at<? ORDER BY at", window
            )
        ]
        applicable = [
            r
            for r in rows
            if r["market"] == market
            and r["buy_fill_identity"] == source["buy_fill_identity"]
            and r["path_policy_sha256"] == source["policy_sha256"]
            and r["persisted_at"] < signal_at
        ]
        # Threshold/type changes do not alter the original pre-exit position
        # payload. The candidate has made no sale before its first crossing.
        # Validate actual full bytes, not the collector's coarser dedup hash.
        if any(
            r["status"] == "VALID"
            and (
                r.get("actual_input_verified") is not True
                or str(r["route"]) != str(route)
                or str(r["transport_epoch"]) != str(epoch)
            )
            for r in applicable
        ):
            raise ValueError("holding_vote_actual_input_not_equivalent")
        decision = path_signal_snapshot(
            applicable,
            position_key=source["position_key"],
            buy_fill_identity=source["buy_fill_identity"],
            market=market,
            session_key=__import__("datetime")
            .datetime.fromtimestamp(
                signal_at, __import__("zoneinfo").ZoneInfo("Asia/Seoul")
            )
            .date()
            .isoformat(),
            path_id=source.get("path_id", "EXIT_TRAILING_TP"),
            model=source["model"],
            signal_at=signal_at,
            policy=policy,
            source_policy_sha256=source["policy_sha256"],
        )
        return {**decision, "max_defer_sec": policy["max_defer_sec"]}

    def close(self):
        if self.db is not None:
            self.db.close()
            self.db = None
