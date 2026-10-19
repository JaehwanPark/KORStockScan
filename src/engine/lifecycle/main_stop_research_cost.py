"""Read-only economics overlay for offline Main stop research.

Original completed fills and later cost observations have separate generations.
This adapter never reseals the original report, mutates canonical PnL, publishes
a policy, or turns a quantity-research allocation into exact execution costs.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

from . import broker_cost_allocation as allocation
from . import broker_cost_reconciliation as exact
from . import broker_cost_source as official
from .holding_window_generation import (MAX_METADATA_BYTES, MAX_PROJECTION_BYTES,
                                         byte_generation, source_stat)
from .research_json_stream import Reader
from .research_input_budget import Claim

SCHEMA = "main_stop_research_cost_v1"
SCOPE = "main_stop_research_only"
COST_GRADES = ("exact_execution", "exact_position_total", "broker_total_allocated")
MAX_RECORDS = allocation.MAX_RECORDS
MAX_COMPACT_RESIDENT_BYTES = 64 * 1024 * 1024
MAX_REGISTRY_BYTES = 4 * 1024 * 1024
_FIELDS = frozenset((
    "id", "rec_date", "code", "status", "strategy", "position_tag", "buy_qty",
    "buy_price", "sell_price", "buy_time", "sell_time", "completion_observed_date",
    "exact_sell_fill_time", "sell_time_forbidden_for_intraday_horizon",
    "buy_fill_legs", "sell_fill_legs", "buy_filled_qty", "sell_filled_qty",
    "buy_fill_amount", "sell_fill_amount", "position_residual_qty", "sell_quantity_conserved",
    "main_automatic_management_allowed", "main_custody_source_sha256",
    "holding_path_buy_fill_identity", "terminal_decision_authority", "terminal_population_scope",
    "exit_signal", "strict_completion_status", "strict_completion_reasons",
    "actual_cost_reconciliation", "quantity_research_cost", "profit_rate",
    "realized_pnl_krw", "broker_actual_fees_taxes_krw", "market_session_bucket",
    "effective_venue", "actual_execution_venue", "actual_execution_venue_verified"))


def _canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _cutoff(value):
    if value is None:
        return None
    if isinstance(value, (str, datetime)):
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else value
        if parsed.tzinfo is None:
            raise ValueError("stop_research_knowledge_timezone_missing")
        value = parsed.timestamp()
    if isinstance(value, bool) or not math.isfinite(float(value)):
        raise ValueError("stop_research_knowledge_cutoff_invalid")
    return float(value)


def _read(path, maximum):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("stop_research_source_symlink")
    before = source_stat(path.stat())
    if not path.is_file() or before[2] > maximum:
        raise ValueError("stop_research_source_partition_required")
    raw = path.read_bytes()
    if len(raw) > maximum or before != source_stat(path.stat()):
        raise ValueError("stop_research_source_changed")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("stop_research_source_object_invalid")
    return value


def _signature(paths):
    return {str(p): source_stat(p.lstat()) if p.exists() or p.is_symlink() else None for p in paths}


def _admit_cost_inputs(root, day, claims):
    """Reserve the native cost decoder population before opening its JSON.

    Only the current index's immutable receipt generations participate. Old
    retained revisions do not consume the active batch's memory budget.
    """
    paths, admitted = [], set()
    def admit(path, maximum):
        paths.append(path)
        if not path.exists():
            return
        if path in admitted:
            return
        if (path.is_symlink() or any(parent.is_symlink() for parent in path.parents)
                or not path.is_file() or path.stat().st_size > maximum):
            raise ValueError("stop_research_cost_input_path_or_size_invalid")
        # Raw bytes plus the retained Python object and native validation copy.
        claims.append(Claim(path.stat().st_size * 12))
        admitted.add(path)
    index_path = root / "runtime/initial_quantity_research_costs" / day / "index.json"
    admit(index_path, exact.MAX_GENERATION_BYTES)
    dates = {day}
    if index_path.exists():
        index = _read(index_path, exact.MAX_GENERATION_BYTES)
        references = index.get("receipts")
        source_dates = index.get("source_dates")
        if (not isinstance(references, dict) or len(references) > allocation.MAX_RECORDS
                or not isinstance(source_dates, list) or len(source_dates) > allocation.MAX_DATES
                or len(set(references.values())) != len(references)):
            raise ValueError("stop_research_cost_index_population_invalid")
        for record, reference in references.items():
            allocation._record(record)
            if (not isinstance(reference, str) or len(reference) != 64
                    or any(c not in "0123456789abcdef" for c in reference)):
                raise ValueError("stop_research_cost_index_reference_invalid")
            admit(index_path.parent / "generations" / (reference + ".json"), exact.MAX_BYTES)
        for source_day in source_dates:
            if date.fromisoformat(source_day).isoformat() != source_day or source_day > day:
                raise ValueError("stop_research_cost_source_date_invalid")
            dates.add(source_day)
    directory = exact.receipt_path(root, day, "1").parent
    paths.append(directory)
    if directory.exists():
        for count, path in enumerate(directory.glob("*.json"), 1):
            if count > allocation.MAX_RECORDS:
                raise ValueError("stop_research_cost_receipt_population_invalid")
            admit(path, exact.MAX_BYTES)
    for source_day in dates:
        admit(official.source_path(root, source_day), official.MAX_BYTES)
    return paths


def _native_projection(root, day):
    """Verify native byte receipts independently of the current cost generation."""
    claims, transient_claims = [], []
    try:
        return _native_projection_read(root, day, claims, transient_claims)
    except BaseException:
        # Exceptions may retain their traceback frames beyond this call.
        for claim in claims:
            claim.close()
        raise
    finally:
        for claim in transient_claims:
            claim.close()


def _native_projection_read(root, day, claims, transient_claims):
    raw = root / "report/monitor_snapshots" / f"trade_review_{day}.json"
    sidecar = raw.with_suffix(".completed_projection.json")
    dependency = Path(str(sidecar) + ".dependencies.json")
    paths = [p for logical in (raw, sidecar) for p in
             (logical, Path(str(logical) + ".gz"), Path(str(logical) + ".gz.archive_receipt.json"))]
    paths.append(dependency)
    before = _signature(paths)
    resident = 0
    def account_row(row, claim=None):
        nonlocal resident
        amount = len(json.dumps(row, ensure_ascii=False, allow_nan=False).encode()) * 8
        if resident + amount > MAX_COMPACT_RESIDENT_BYTES:
            raise ValueError("stop_research_compact_census_partition_required")
        if claim is None:
            claims.append(Claim(amount))
        else:
            claim.grow(amount)
        resident += amount
    if not dependency.is_file():
        # Small legacy native projections retain their full original self-seal.
        transient_claims.append(Claim(sidecar.stat().st_size * 12))
        value = _read(sidecar, MAX_PROJECTION_BYTES)
        from src.engine.sniper_trade_review_report import verify_completed_census_manifest
        if (value.get("artifact_sha256") != _canonical({k: v for k, v in value.items() if k != "artifact_sha256"})
                or verify_completed_census_manifest(value, day) is not None):
            raise ValueError("stop_research_native_projection_invalid")
        generation = byte_generation(sidecar)
        rows = (value.get("sections") or {}).get("completed_trade_projection")
        rows = [{k: v for k, v in row.items() if k in _FIELDS} for row in rows]
        for row in rows:
            account_row(row)
        proof = {"projection": generation, "legacy_self_seal": value["artifact_sha256"]}
    else:
        transient_claims.append(Claim(dependency.stat().st_size * 12))
        receipt = _read(dependency, MAX_METADATA_BYTES)
        generation = byte_generation(sidecar)
        if (receipt.get("schema") != "holding_projection_dependency_receipt_v1"
                or receipt.get("date") != day or receipt.get("projection") != generation
                or receipt.get("artifact_sha256") != exact.digest({k: v for k, v in receipt.items() if k != "artifact_sha256"})):
            raise ValueError("stop_research_native_dependency_invalid")
        header, rows = {}, []
        def project(reader):
            row = {}
            row_claim = Claim(0)
            claims.append(row_claim)
            def selected(key, child):
                if key in _FIELDS:
                    row[key] = child.value(allocation.CACHED_RECEIPT_MAX_BYTES)
                    # Reader owns transient decode; each returned field must
                    # remain admitted while the rest of this row is streamed.
                    account_row({key: row[key]}, row_claim)
                else:
                    child.skip()
                return iter(())
            for _ in reader.fields(selected):
                pass
            if len(rows) >= MAX_RECORDS:
                raise ValueError("stop_research_completion_partition_required")
            rows.append(row)
            return row
        def visit(key, reader):
            if key == "sections":
                def section(name, child):
                    if name == "completed_trade_projection":
                        for _ in child.array(project):
                            pass
                    else:
                        child.skip()
                    return iter(())
                for _ in reader.fields(section):
                    pass
            elif key in {"date", "code", "since", "schema", "meta", "metrics", "snapshot_identity"}:
                header[key] = reader.value(MAX_METADATA_BYTES)
                transient_claims.append(Claim(len(json.dumps(header[key]).encode()) * 8))
            else:
                reader.skip()
            return iter(())
        physical = sidecar if sidecar.exists() else Path(str(sidecar) + ".gz")
        if physical.is_symlink() or any(p.is_symlink() for p in physical.parents):
            raise ValueError("stop_research_source_symlink")
        with physical.open("rb") as stream:
            decoder = gzip.GzipFile(fileobj=stream) if physical.suffix == ".gz" else stream
            with io.TextIOWrapper(decoder, encoding="utf-8") as handle:
                reader = Reader(handle)
                for _ in reader.fields(visit):
                    pass
                reader.spaces()
                if reader.peek():
                    raise ValueError("stop_research_native_trailing_json")
        value = header
        census = (value.get("meta") or {}).get("completed_census_manifest")
        if (not isinstance(census, dict) or exact.digest(census) != receipt.get("census_sha256")
                or receipt.get("completed_count") != len(rows)
                or receipt.get("snapshot_identity") != value.get("snapshot_identity")
                or (receipt.get("meta") or {}).get("actual_cost_source_generation")
                   != (value.get("meta") or {}).get("actual_cost_source_generation")
                or (receipt.get("meta") or {}).get("snapshot_profile") != "postclose_exit"):
            raise ValueError("stop_research_native_census_binding_invalid")
        proof = {"projection": generation, "dependency_receipt": byte_generation(dependency),
                 "dependency_artifact_sha256": receipt["artifact_sha256"]}
    census = (value.get("meta") or {}).get("completed_census_manifest") or {}
    from src.engine.lifecycle.snapshot_archive import snapshot_identity_matches
    identity = value.get('snapshot_identity')
    ids = [allocation._record(row.get("id")) for row in rows]
    if (value.get("schema") != "trade_review_completed_projection_sidecar_v1"
            or value.get("date") != day or value.get("code") or value.get("since")
            or (value.get("meta") or {}).get("snapshot_profile") != "postclose_exit"
            or not snapshot_identity_matches(raw, value.get("snapshot_identity"))
            or census.get("schema") != "trade_review_completed_census_v1"
            or census.get("source_date") != day or census.get("profile") != "postclose_exit"
            or census.get("projected_count") != len(rows) or len(rows) > MAX_RECORDS
            or (value.get("metrics") or {}).get("canonical_completed_trades") != len(rows)
            or sorted(ids) != sorted(census.get("raw_terminal_ids") or []) or len(set(ids)) != len(ids)
            or any(row.get("status") != "COMPLETED" or row.get("completion_observed_date") != day for row in rows)):
        raise ValueError("stop_research_native_completion_invalid")
    census_rows = {str(row.get("id")): row for row in census.get("rows", [])}
    if len(census_rows) != len(rows):
        raise ValueError("stop_research_native_census_ids_invalid")
    for row in rows:
        sealed = census_rows.get(str(row["id"]))
        if sealed is None or any(sealed.get(a) != row.get(b) for a, b in (
                ("entry_date", "rec_date"), ("owner_scope", "terminal_population_scope"),
                ("strategy", "strategy"), ("position_tag", "position_tag"),
                ("strict_status", "strict_completion_status"))):
            raise ValueError("stop_research_native_census_row_invalid")
    if before != _signature(paths):
        raise ValueError("stop_research_source_changed")
    proof.update(source_date=day, snapshot_identity=identity, census_sha256=exact.digest(census),
                 original_cost_generation=(value.get("meta") or {}).get("actual_cost_source_generation"))
    claims.append(Claim(len(json.dumps(proof).encode()) * 8))
    class BudgetedRows(dict):
        pass
    indexed = BudgetedRows({str(row["id"]): row for row in rows})
    indexed.budget_claims = claims
    return indexed, proof, paths


def _registry(root):
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry
    path = root / "runtime/order_owner_registry.jsonl"
    if not path.exists():
        return [], {"status": "source_gap", "reason": "registry_missing"}, path
    before = _signature([path])
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("stop_research_registry_symlink")
    events = OrderOwnerRegistry(path).verified_events_snapshot(max_bytes=MAX_REGISTRY_BYTES)
    generation = byte_generation(path)
    if before != _signature([path]):
        raise ValueError("stop_research_registry_changed")
    return events, {**generation, "status": "verified",
                    "tail_hash": events[-1]["event_hash"] if events else "0" * 64}, path


@dataclass
class PreparedEconomicSource:
    """One bounded native census and immutable cost overlay per research batch."""
    data_root: Path
    cost_data_root: Path
    source_date: str
    knowledge_cutoff: float | None
    rows: dict = field(default_factory=dict)
    source_reference: dict = field(default_factory=dict)
    cost_generation: dict = field(default_factory=dict)
    cost_generation_sha256: str | None = None
    status: str = "source_gap"
    reason: str | None = None
    _results: dict = field(default_factory=dict, repr=False)
    _paths: list = field(default_factory=list, repr=False)
    _signature: dict = field(default_factory=dict, repr=False)
    _memory_claims: list = field(default_factory=list, repr=False)

    def close(self):
        """Release retained native rows after the batch consumer has finished."""
        for claim in getattr(self.rows, "budget_claims", ()):
            claim.close()
        for claim in self._memory_claims:
            claim.close()
        self._memory_claims.clear()
        self.rows.clear()
        self._results.clear()
        self.source_reference = {}
        self.cost_generation = {}
        self.cost_generation_sha256 = None
        self._paths.clear()
        self._signature.clear()
        if hasattr(self.rows, "budget_claims"):
            self.rows.budget_claims.clear()
        if self.status == "verified":
            self.status, self.reason = "closed", "stop_research_prepared_source_closed"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def validate_unchanged(self):
        """Call once before publishing a batch; never rehash huge files per row."""
        if self.status == "closed":
            raise ValueError("stop_research_prepared_source_closed")
        if self._signature != _signature(self._paths):
            raise ValueError("stop_research_prepared_source_changed")
        if self.status == "verified" and exact.source_generation(self.cost_data_root, self.source_date) != self.cost_generation:
            raise ValueError("stop_research_prepared_cost_changed")
        return True


def _base(row, prepared):
    return dict(schema=SCHEMA, economics_scope=SCOPE, status="source_gap", reason=None,
        record_id=str(row.get("id", "")), source_date=prepared.source_date, evidence_grade=None,
        research_cost_krw=None, research_net_pnl_krw=None, research_profit_rate=None,
        actual_execution_cost=False, runtime_effect=False, allowed_runtime_apply=False,
        canonical_pnl_mutated=False, knowledge_cutoff=prepared.knowledge_cutoff,
        completion_source=prepared.source_reference, cost_source_generation_sha256=prepared.cost_generation_sha256,
        original_economics_scope=None, cost_receipt_sha256=None, cost_available_at=None,
        known_at=None, quantity_basis=None, fill_state="unverified", custody_status="unverified",
        manual_exit=False, terminal_observation=None)


def _raw_allocation_sources(receipt, sources, buy_legs, sell_legs):
    """The merkle/allocation validator alone cannot authenticate broker totals."""
    for part in receipt["sources"]:
        source = sources.get(part["source_date"])
        if source is None:
            raise ValueError("stop_research_official_source_missing")
        # load_source validated this immutable object once for the whole batch.
        diary = [r for r in official.rows(source, "ka10170") if official.symbol(r.get("stk_cd")) == receipt["symbol"]]
        if len(diary) != 1:
            raise ValueError("stop_research_official_symbol_ambiguous")
        row = diary[0]
        if (source["source_sha256"] != part["source_sha256"]
                or source["broker_account_sha256"] != part["broker_account_sha256"]
                or source["local_account_key_sha256"] != receipt["account_scope_sha256"]
                or exact.digest(row) != part["diary_row_sha256"]
                or allocation._clock(source["observations"]["ka10170"]["observed_at"]) != allocation._clock(part["observed_at"])
                or official.number(row["cmsn_alm_tax"]) != official.number(part["confirmed_total_cost_krw"])
                or official.number(row["buy_amt"]) != official.number(part["confirmed_buy_amount_krw"])
                or official.number(row["sell_amt"]) != official.number(part["confirmed_sell_amount_krw"])):
            raise ValueError("stop_research_official_allocation_binding_invalid")
        for legs, qty_key, amount_key in ((buy_legs, "buy_qty", "buy_amt"), (sell_legs, "sell_qty", "sell_amt")):
            selected = [leg for leg in allocation._legs(legs) if leg[0].date().isoformat() == part["source_date"]]
            if (sum((leg[1] for leg in selected), Decimal(0)) > official.number(row[qty_key])
                    or sum((leg[2] for leg in selected), Decimal(0)) > official.number(row[amount_key])):
                raise ValueError("stop_research_official_quantity_unreconciled")


def _main_exit_signal(row, signal, account, completed):
    """Bind the native Main decision to its terminal order, reject custody conflicts.

    The native same-order validator predates optional submission owner/account
    fields. Their absence is retained; their presence must agree with custody.
    """
    fields, submission = signal.get("fields") or {}, signal.get("submission") or {}
    raw = fields.get("exit_signal_contract")
    contract = json.loads(raw) if isinstance(raw, str) else raw
    if (signal.get("inferred") is not False or signal.get("binding_status") != "same_order_generation"
            or not isinstance(contract, dict) or not isinstance(submission, dict)):
        raise ValueError("stop_research_main_exit_source_unproven")
    stock, record = row["code"], str(row["id"])
    order = submission.get("order_no")
    if (contract.get("schema") != "holding_exit_signal_receipt_v1"
            or exact.digest(contract) != fields.get("exit_signal_contract_sha256")
            or contract.get("decision_owner_type") != "main_scalping"
            or contract.get("record_id") != record or contract.get("code") != stock
            or contract.get("strategy") not in {"SCALPING", "SCALP"}
            or contract.get("strategy") != row.get("strategy")
            or contract.get("position_key") != "record:" + record
            or not contract.get("exit_rule") or contract.get("exit_rule") != signal.get("exit_rule")
            or not contract.get("buy_fill_identity")
            or contract.get("buy_fill_identity") != fields.get("exit_signal_buy_fill_identity")
            or row.get("holding_path_buy_fill_identity") not in (None, contract["buy_fill_identity"])
            or contract.get("source_date") != str(contract.get("signal_at"))[:10]
            or contract.get("source_date") != row["completion_observed_date"]
            or submission.get("owner_id") not in (None, "", "main_scalping:" + record)
            or submission.get("account_key") and exact.digest(["broker_account", submission["account_key"]]) != account
            or not str(order).isdigit() or int(order) <= 0
            or not any(int(leg["order_no"]) == int(order) for leg in row["sell_fill_legs"])
            or submission.get("broker_route") not in {"KRX", "NXT", "SOR"}
            or not submission.get("sell_submit_generation")
            or not submission.get("sell_submit_context_sha256")):
        raise ValueError("stop_research_main_exit_identity_invalid")
    signal_at = allocation._clock(contract["signal_at"])
    submitted_at = allocation._clock(submission["submitted_at"])
    # Native log timestamps are second precision; the signed decision retains
    # microseconds. Reuse the native binder's one-second representation bound.
    if (min(allocation._clock(leg["at"]) for leg in row["buy_fill_legs"]) > signal_at
            or signal_at > submitted_at + timedelta(seconds=1) or submitted_at > completed):
        raise ValueError("stop_research_main_exit_clock_invalid")
    return {"status": "verified_native_decision_submit_chain", "exit_rule": contract["exit_rule"],
            "signal_contract_sha256": exact.digest(contract), "submission_order_no": str(order),
            "submission_context_sha256": submission["sell_submit_context_sha256"],
            "seller_attribution_basis": "native_main_decision_same_order_generation",
            "explicit_submission_owner_observed": bool(submission.get("owner_id")),
            "explicit_submission_account_observed": bool(submission.get("account_key"))}


def _record_result(row, prepared, registry, registry_generation, registry_index, receipts, sources):
    from src.engine.sniper_trade_review_report import _quantity_registry_fill_custody
    result = _base(row, prepared)
    try:
        buy, sell = row.get("buy_fill_legs"), row.get("sell_fill_legs")
        buys, sells = allocation._legs(buy), allocation._legs(sell)
        bq = sum((leg[1] for leg in buys), Decimal(0))
        sq = sum((leg[1] for leg in sells), Decimal(0))
        result["quantity_basis"] = {"buy_qty": float(bq), "sell_qty": float(sq), "residual_qty": float(bq - sq),
            "buy_fill_identity": allocation.fill_identity(buy), "sell_fill_identity": allocation.fill_identity(sell)}
        if (bq <= 0 or bq != sq or row.get("sell_quantity_conserved") is not True
                or row.get("position_residual_qty") != 0):
            return {**result, "status": "censored", "reason": "position_not_fully_closed", "fill_state": "partial_or_open"}
        result["fill_state"] = "fully_closed_multi_fill" if len(buys) > 1 or len(sells) > 1 else "fully_closed"
        if (row.get("terminal_decision_authority") != "broker_sell_fill_observation_only"
                or row.get("terminal_population_scope") != "real_record_bound"
                or row.get("sell_time_forbidden_for_intraday_horizon") is not False):
            raise ValueError("stop_research_terminal_authority_or_clock_unproven")
        completed = (allocation._clock(row["exact_sell_fill_time"]) if row.get("exact_sell_fill_time")
                     else max(leg[0] for leg in sells))
        result["terminal_time_basis"] = "native_exact_sell_fill_time" if row.get("exact_sell_fill_time") else "native_sell_fill_legs"
        if completed.date().isoformat() != prepared.source_date or completed < max(leg[0] for leg in sells):
            raise ValueError("stop_research_terminal_clock_conflict")
        permitted = {"source_gap_sell_leg_configured_cost", "source_gap_broker_actual_cost_missing",
                     "source_gap_actual_cost_missing"}
        reasons = set(row.get("strict_completion_reasons") or []) - permitted
        if reasons:
            raise ValueError("stop_research_completion_source_invalid:" + ",".join(sorted(reasons)))
        signal = row.get("exit_signal") or {}
        fields = signal.get("fields") or {}
        manual = any(str(value).upper() == "MANUAL" for value in (
            signal.get("exit_decision_source"), signal.get("sell_reason_type"), fields.get("exit_decision_source"), fields.get("sell_reason_type")))
        result["manual_exit"] = manual
        custody = _quantity_registry_fill_custody(row, {"buy_fill_legs": buy}, registry,
                                                  registry_generation, registry_index=registry_index)
        account = allocation.custody_account(row["id"], buy, custody)
        result["custody_status"] = "verified_registry_fill_census"
        result["custody_source"] = {"registry": registry_generation, "custody_sha256": allocation._custody_identity(row["id"], custody)}
        result["terminal_observation"] = {k: deepcopy(row.get(k)) for k in (
            "id", "code", "status", "main_automatic_management_allowed", "strategy", "position_tag", "rec_date", "completion_observed_date", "exact_sell_fill_time",
            "terminal_decision_authority", "terminal_population_scope", "exit_signal", "buy_fill_legs", "sell_fill_legs",
            "holding_path_buy_fill_identity", "market_session_bucket", "effective_venue", "actual_execution_venue", "actual_execution_venue_verified")}
        result["terminal_observation"].update(terminal_fill_time=completed.isoformat(),
                                               terminal_time_basis=result["terminal_time_basis"])
        if manual:
            return {**result, "status": "censored", "reason": "manual_exit"}
        try:
            result["main_exit_source"] = _main_exit_signal(row, signal, account, completed)
        except (ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
            return {**result, "status": "censored", "reason": str(exc)}
        if prepared.knowledge_cutoff is not None and completed.timestamp() > prepared.knowledge_cutoff:
            return {**result, "status": "pending", "reason": "completion_after_knowledge_cutoff"}
        raw_exact = exact.load_receipt(prepared.cost_data_root, prepared.source_date, str(row["id"]))
        if raw_exact is not None:
            verified = exact.reconcile(raw_exact, context={"position_key": "record:" + str(row["id"]),
                "symbol": row["code"], "owner": "main", "account_scope_sha256": account,
                "buy_fill_identity": exact.digest(buy), "completion_observed_date": prepared.source_date,
                "completed_at": completed.timestamp()}, buy_legs=buy, sell_legs=sell,
                knowledge_cutoff=prepared.knowledge_cutoff)
            if verified["status"] != "actual_cost_reconciled":
                return {**result, "status": "pending" if verified["status"] == "actual_cost_pending" else "source_gap", "reason": verified["reason"]}
            return {**result, "status": "eligible", "reason": None, "evidence_grade": "exact_execution",
                "actual_execution_cost": True, "original_economics_scope": "exact_execution",
                "research_cost_krw": verified["actual_fees_taxes_krw"], "research_net_pnl_krw": verified["exact_pnl_krw"],
                "research_profit_rate": verified["exact_profit_rate"], "cost_receipt_sha256": verified["receipt_sha256"],
                "raw_source_sha256": verified["raw_sha256"], "cost_available_at": verified["cost_available_at"],
                "known_at": max(verified["cost_available_at"], verified["reconciled_at"], key=lambda at: allocation._clock(at))}
        native_actual = row.get("actual_cost_reconciliation") or {}
        prior_actual = (native_actual.get("status") == "actual_cost_reconciled"
                        and native_actual.get("allocation_scope") in {
                            "broker_settled_whole_position", "broker_day_symbol_whole_position"})
        source = sources.get(prepared.source_date)
        if prior_actual and source is None:
            raise ValueError("stop_research_native_actual_source_changed")
        if source is not None:
            verified = official.reconcile_position(source, target_date=prepared.source_date,
                record_id=row["id"], stock_code=row["code"], buy_legs=buy, sell_legs=sell,
                custody_rows=custody, peer_records=[r["id"] for r in prepared.rows.values() if r["code"] == row["code"]],
                knowledge_cutoff=prepared.knowledge_cutoff)
            if verified["status"] == "actual_cost_pending":
                return {**result, "status": "pending", "reason": verified["reason"]}
            same_actual_source = prior_actual and source.get("source_sha256") == native_actual.get("source_sha256")
            if prior_actual and (verified["status"] != "actual_cost_reconciled"
                    or same_actual_source and verified.get("receipt_sha256") != native_actual.get("receipt_sha256")):
                raise ValueError("stop_research_native_actual_reconciliation_invalid")
            if verified["status"] == "actual_cost_reconciled":
                return {**result, "status": "eligible", "reason": None, "evidence_grade": "exact_position_total",
                    "actual_execution_cost": False, "actual_position_cost": True,
                    "original_economics_scope": verified["allocation_scope"],
                    "research_cost_krw": verified["actual_fees_taxes_krw"], "research_net_pnl_krw": verified["exact_pnl_krw"],
                    "research_profit_rate": verified["exact_profit_rate"], "cost_receipt_sha256": verified["receipt_sha256"],
                    "raw_source_sha256": verified["source_sha256"], "cost_available_at": verified["cost_available_at"],
                    "known_at": verified["cost_available_at"],
                    "prior_native_actual_receipt_sha256": native_actual.get("receipt_sha256") if prior_actual else None,
                    "prior_native_actual_source_sha256": native_actual.get("source_sha256") if prior_actual else None,
                    "cost_overlay_basis": "original_native_actual_reverified" if same_actual_source else "later_official_whole_position_reconciled"}
        receipt = receipts.get(str(row["id"]))
        if receipt is None:
            return {**result, "status": "pending", "reason": "verified_cost_receipt_missing"}
        verified = allocation.validate_research_cost(receipt, record_id=row["id"], symbol=row["code"],
            buy_legs=buy, sell_legs=sell, custody_rows=custody, completion_date=prepared.source_date,
            knowledge_cutoff=prepared.knowledge_cutoff)
        if verified["status"] != "research_cost_allocated":
            return {**result, "status": "pending" if verified["status"] == "research_cost_pending" else "source_gap", "reason": verified["reason"]}
        if allocation._clock(verified["completed_at"]) != completed:
            raise ValueError("stop_research_allocation_terminal_clock_conflict")
        _raw_allocation_sources(verified, sources, buy, sell)
        return {**result, "status": "eligible", "reason": None, "evidence_grade": "broker_total_allocated",
            "original_economics_scope": verified["economics_scope"], "actual_execution_cost": False,
            "research_cost_krw": verified["allocated_fees_taxes_krw"], "research_net_pnl_krw": verified["allocated_net_pnl_krw"],
            "research_profit_rate": verified["allocated_profit_rate"], "cost_receipt_sha256": verified["receipt_sha256"],
            "original_cost_receipt_content_sha256": exact.digest(receipt), "cost_available_at": verified["cost_available_at"],
            "known_at": verified["cost_available_at"], "allocation_algorithm": verified["allocation_algorithm"],
            "raw_sources": [{k: part[k] for k in ("source_date", "source_sha256", "observed_at", "diary_row_sha256")} for part in verified["sources"]]}
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError, AttributeError) as exc:
        return {**result, "status": "source_gap", "reason": str(exc)}


def prepare_economic_source(data_root, source_date, knowledge_cutoff=None, *, cost_data_root=None):
    """Prepare once per completion day; all broker/registry operations are reads."""
    if date.fromisoformat(source_date).isoformat() != source_date:
        raise ValueError("stop_research_source_date_invalid")
    root = Path(data_root).absolute()
    costs = Path(cost_data_root).absolute() if cost_data_root is not None else root
    prepared = PreparedEconomicSource(root, costs, source_date, _cutoff(knowledge_cutoff))
    transient_claims = []
    try:
        prepared.rows, prepared.source_reference, paths = _native_projection(root, source_date)
        prepared._paths = paths
        prepared._signature = _signature(paths)
        cost_paths = _admit_cost_inputs(costs, source_date, transient_claims)
        prepared._paths.extend(cost_paths)
        prepared._signature.update(_signature(cost_paths))
        generation = exact.source_generation(costs, source_date)
        prepared.cost_generation = generation
        prepared.cost_generation_sha256 = exact.digest(generation)
        prepared._memory_claims.append(Claim(len(json.dumps(generation).encode()) * 8))
        receipts, sources = {}, {}
        research = generation.get("quantity_research_cost_generation") or {}
        for reference in research.get("receipts", []):
            path = costs / "runtime/initial_quantity_research_costs" / source_date / "generations" / (reference["content_sha256"] + ".json")
            value = _read(path, allocation.CACHED_RECEIPT_MAX_BYTES)
            if exact.digest(value) != reference["content_sha256"]:
                raise ValueError("stop_research_cost_receipt_changed")
            receipts[reference["record_id"]] = value
        source_dates = {reference["source_date"] for reference in research.get("source_dates", [])}
        if official.source_path(costs, source_date).exists():
            source_dates.add(source_date)
        for day in source_dates:
            try:
                sources[day] = official.load_source(costs, day)
            except (OSError, ValueError, TypeError, KeyError):
                # An identifiable bad source date does not erase unrelated rows.
                sources[day] = None
        registry_path = root / "runtime/order_owner_registry.jsonl"
        if registry_path.exists():
            if registry_path.stat().st_size > MAX_REGISTRY_BYTES:
                raise ValueError("stop_research_registry_partition_required")
            transient_claims.append(Claim(registry_path.stat().st_size * 12))
        registry, registry_generation, registry_path = _registry(root)
        prepared._paths.append(registry_path)
        prepared._signature.update(_signature([registry_path]))
        from src.engine.sniper_trade_review_report import _quantity_registry_index
        registry_index = _quantity_registry_index(registry)
        for record, row in prepared.rows.items():
            result = _record_result(row, prepared, registry, registry_generation, registry_index, receipts, sources)
            result["artifact_sha256"] = exact.digest(result)
            prepared._memory_claims.append(Claim(len(json.dumps(result).encode()) * 8))
            prepared._results[record] = result
        prepared.status = "verified"
        prepared.validate_unchanged()
    except (OSError, ValueError, TypeError, KeyError, ArithmeticError, RuntimeError, AttributeError) as exc:
        prepared.close()
        if str(exc).startswith("shared_research_budget_"):
            raise
        prepared.status, prepared.reason = "source_gap", str(exc)
        prepared._results.clear()
    finally:
        for claim in transient_claims:
            claim.close()
    return prepared


def prepare_economic_record(record, *, data_root, source_date, knowledge_cutoff=None,
                            prepared=None, cost_data_root=None):
    """Return a detached report-only result; caller fields cannot override proof."""
    if not isinstance(record, dict):
        raise ValueError("stop_research_record_object_invalid")
    if prepared is None:
        with prepare_economic_source(data_root, source_date, knowledge_cutoff, cost_data_root=cost_data_root) as owned:
            return prepare_economic_record(record, data_root=data_root, source_date=source_date,
                knowledge_cutoff=knowledge_cutoff, prepared=owned, cost_data_root=cost_data_root)
    root = Path(data_root).absolute()
    costs = Path(cost_data_root).absolute() if cost_data_root is not None else root
    if (not isinstance(prepared, PreparedEconomicSource) or prepared.data_root != root
            or prepared.cost_data_root != costs or prepared.source_date != source_date
            or prepared.knowledge_cutoff != _cutoff(knowledge_cutoff)):
        raise ValueError("stop_research_prepared_context_mismatch")
    key = allocation._record(record.get("id", record.get("record_id")))
    result = _base({"id": key}, prepared)
    if prepared.status != "verified":
        result["reason"] = prepared.reason
    elif key not in prepared.rows:
        result["reason"] = "native_completed_record_missing"
    elif any(k in prepared.rows[key] and k not in {"id", "record_id"} and v != prepared.rows[key][k] for k, v in record.items()):
        result["reason"] = "caller_native_record_conflict"
    else:
        result = prepared._results[key]
        with Claim(len(json.dumps(result).encode()) * 8):
            return deepcopy(result)
    result["artifact_sha256"] = exact.digest(result)
    return deepcopy(result)


def selection_grade(economic, source):
    """Eligibility for one modeled comparison, never an actual-PnL relabel.

    The normal publisher obtains ``economic`` from this module's native batch
    producer. This check additionally binds that result to the exact source
    position; a self-seal alone is not a substitute for the native producer.
    """
    quantity = economic.get('quantity_basis') or {}
    terminal = economic.get('terminal_observation') or {}
    grade = economic.get('evidence_grade')
    from src.engine.scalping.main_stop_quantity_source import validate_quantity_source
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_legs
    proof=source.get('quantity_source') or {}
    try:
        exact_quantity=(validate_quantity_source(proof,position_key=source['position_key'],at=source['at'],
            quantity=source['quantity'],buy_basis_krw=source['buy_basis_krw'])
            and proof.get('buy_fill_identity')==buy_fill_identity_from_legs(terminal.get('buy_fill_legs'))
            and max(allocation._clock(leg['at']).timestamp() for leg in terminal['buy_fill_legs'])<=source['at']
            <=allocation._clock(terminal['terminal_fill_time']).timestamp())
    except (KeyError,TypeError,ValueError):exact_quantity=False
    valid = (economic.get('schema') == SCHEMA and economic.get('economics_scope') == SCOPE
        and economic.get('artifact_sha256') == exact.digest({k:v for k,v in economic.items() if k != 'artifact_sha256'})
        and economic.get('status') == 'eligible' and grade in COST_GRADES and exact_quantity
        and economic.get('manual_exit') is False and economic.get('runtime_effect') is False
        and economic.get('allowed_runtime_apply') is False and economic.get('canonical_pnl_mutated') is False
        and economic.get('custody_status') == 'verified_registry_fill_census'
        and economic.get('fill_state') in {'fully_closed', 'fully_closed_multi_fill'}
        and (economic.get('main_exit_source') or {}).get('status') == 'verified_native_decision_submit_chain'
        and str(economic.get('record_id')) == str(source.get('record_id'))
        and quantity.get('buy_qty') == source.get('quantity')
        and quantity.get('sell_qty') == source.get('quantity') and quantity.get('residual_qty') == 0
        and str(terminal.get('code')) == str(source.get('item')).split('_', 1)[0]
        and economic.get('actual_execution_cost') is (grade == 'exact_execution')
        and (grade != 'exact_position_total' or economic.get('actual_position_cost') is True))
    return grade if valid else None


def selection_source_generation(data_root, days):
    """Pin present and absent native dependencies before a normal publication.

    Completion batches are decoded one day at a time by the caller. Every
    input is rechecked at commit/consume, including a formerly absent receipt.
    """
    root = Path(data_root).absolute()
    paths = [root / 'runtime/order_owner_registry.jsonl']
    generations = {}
    for day in sorted(set(days)):
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError('stop_research_source_date_invalid')
        raw = root / 'report/monitor_snapshots' / f'trade_review_{day}.json'
        sidecar = raw.with_suffix('.completed_projection.json')
        paths.extend(p for logical in (raw, sidecar) for p in
            (logical, Path(str(logical)+'.gz'), Path(str(logical)+'.gz.archive_receipt.json')))
        paths.append(Path(str(sidecar)+'.dependencies.json'))
        generations[day] = exact.source_generation(root, day)
    signatures = {name: list(value) if value is not None else None
                  for name,value in _signature(paths).items()}
    files = {str(path): byte_generation(path) for path in paths if path.is_file()}
    return dict(schema='main_stop_selection_sources_v1', source_dates=sorted(generations),
                files=files, path_signatures=signatures, cost_generations=generations)


def verify_selection_source_generation(data_root, expected, *, verify_full=False):
    """Routine committed consumption checks identity without rehashing reports.

    Native cost generations still receive their existing bounded semantic
    validation. Large immutable completed reports are byte-verified at publish
    and on explicit full verification, never on every routine observer read.
    """
    root=Path(data_root).absolute()
    if (expected.get('schema')!='main_stop_selection_sources_v1'
            or not isinstance(expected.get('path_signatures'),dict)
            or not isinstance(expected.get('files'),dict)
            or sorted(expected.get('cost_generations',{}))!=expected.get('source_dates')):
        raise ValueError('stop_native_selection_cost_generation_changed')
    observed={name:list(value) if value is not None else None for name,value in
              _signature([Path(name) for name in expected['path_signatures']]).items()}
    if observed!=expected['path_signatures']:
        raise ValueError('stop_native_selection_cost_generation_changed')
    for day,generation in expected['cost_generations'].items():
        if exact.source_generation(root,day)!=generation:
            raise ValueError('stop_native_selection_cost_generation_changed')
    if verify_full:
        for name,generation in expected['files'].items():
            if byte_generation(Path(name))!=generation:
                raise ValueError('stop_native_selection_cost_generation_changed')
    return True


def selection_completed_evidence(data_root, days):
    """Real bounded batch producer for normal postclose; no caller cost claims."""
    root = Path(data_root).absolute()
    for day in sorted(set(days)):
        with prepare_economic_source(root, day) as prepared:
            if prepared.status != 'verified':
                yield dict(source_date=day,native_batch_diagnostic=dict(
                    status=prepared.status,reason=prepared.reason))
                continue
            for record in prepared.rows:
                economic = prepare_economic_record({'id':record}, data_root=root,
                                                    source_date=day, prepared=prepared)
                yield dict(id=record, source_date=day, main_stop_economic_source=economic)
            prepared.validate_unchanged()
