"""Bounded post-fill statement reconciliation; never grants order authority.

This reader preserves the exact-execution receipt contract. Official whole-day
position totals are reconciled separately by broker_cost_source; they are not
rewritten into invented per-fill allocations. Missing values remain unknown.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = "holding_actual_cost_settlement_v1"
MAX_BYTES = 256 * 1024
MAX_GENERATION_BYTES = 32 * 1024 * 1024
KST = ZoneInfo("Asia/Seoul")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def _at(value) -> float:
    parsed = datetime.fromisoformat(str(value))
    if parsed.tzinfo is None:
        raise ValueError("cost_timestamp_timezone_missing")
    return parsed.timestamp()


def _number(value) -> float:
    if isinstance(value, bool):
        raise ValueError("cost_numeric_boolean")
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("cost_numeric_invalid")
    return result


def receipt_path(data_root: Path, completion_date: str, record_id: str) -> Path:
    if datetime.strptime(completion_date, "%Y-%m-%d").date().isoformat() != completion_date:
        raise ValueError("cost_completion_date_invalid")
    if not str(record_id).isdigit() or int(record_id) <= 0:
        raise ValueError("cost_record_id_invalid")
    return Path(data_root) / "runtime/holding_actual_costs" / completion_date / f"{record_id}.json"


def load_receipt(data_root: Path, completion_date: str, record_id: str) -> dict | None:
    path = receipt_path(data_root, completion_date, record_id)
    if not path.exists():
        return None
    if (any(parent.is_symlink() for parent in (path, path.parent, path.parent.parent))
            or path.stat().st_size > MAX_BYTES):
        raise ValueError("cost_source_path_or_size_invalid")
    with path.open("rb") as handle:
        raw = handle.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("cost_source_size_invalid")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("cost_source_object_invalid")
    return value


def source_generation(data_root: Path, completion_date: str) -> dict:
    directory = receipt_path(data_root, completion_date, "1").parent
    if any(parent.is_symlink() for parent in (directory, directory.parent, directory.parent.parent)):
        raise ValueError("cost_source_directory_symlink")
    rows = []
    paths = []
    if directory.exists():
        for path in directory.glob("*.json"):
            if len(paths) >= 10000:
                raise ValueError("cost_source_population_limit")
            paths.append(path)
    paths.sort()
    total_bytes = 0
    for path in paths:
        if not path.stem.isdigit() or path.is_symlink() or path.stat().st_size > MAX_BYTES:
            raise ValueError("cost_source_path_or_size_invalid")
        if total_bytes + path.stat().st_size > MAX_GENERATION_BYTES:
            raise ValueError("cost_source_generation_size_limit")
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("cost_source_size_invalid")
        total_bytes += len(raw)
        if total_bytes > MAX_GENERATION_BYTES:
            raise ValueError("cost_source_generation_size_limit")
        rows.append({"record_id": path.stem, "sha256": hashlib.sha256(raw).hexdigest()})
    result = {"schema": "holding_actual_cost_source_generation_v1",
            "completion_date": completion_date, "count": len(rows),
            "sha256": digest(rows), "status": "observed" if rows else "cost_source_unavailable"}
    from .broker_cost_source import source_path, MAX_BYTES as SOURCE_MAX_BYTES
    official = source_path(data_root, completion_date)
    if official.exists():
        if official.is_symlink() or official.parent.is_symlink() or official.stat().st_size > SOURCE_MAX_BYTES:
            raise ValueError("broker_cost_source_path_or_size_invalid")
        with official.open("rb") as handle:
            raw = handle.read(SOURCE_MAX_BYTES + 1)
        if len(raw) > SOURCE_MAX_BYTES:
            raise ValueError("broker_cost_source_size_limit")
        result["official_source_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def reconcile(receipt: dict | None, *, context: dict, buy_legs: list,
              sell_legs: list, knowledge_cutoff: float | None = None) -> dict:
    missing = {"status": "cost_source_unavailable", "actual_fees_taxes_krw": None,
               "exact_pnl_krw": None, "exact_profit_rate": None,
               "reason": "exact_execution_statement_not_available"}
    if receipt is None:
        return missing
    try:
        if receipt.get("schema") != SCHEMA or receipt.get("status") != "complete":
            raise ValueError("cost_receipt_contract_invalid")
        body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        if digest(body) != receipt.get("receipt_sha256"):
            raise ValueError("cost_receipt_hash_mismatch")
        for key in ("position_key", "symbol", "buy_fill_identity", "account_scope_sha256",
                    "completion_observed_date", "owner"):
            if not context.get(key) or receipt.get(key) != context[key]:
                raise ValueError("cost_context_mismatch:" + key)
        if context["owner"] != "main" or any(
            len(str(context[k])) != 64 or any(c not in "0123456789abcdef" for c in str(context[k]))
            for k in ("buy_fill_identity", "account_scope_sha256")
        ):
            raise ValueError("cost_owner_or_generation_invalid")
        available, reconciled = _at(receipt["cost_available_at"]), _at(receipt["reconciled_at"])
        completed_at = float(context["completed_at"])
        if (not math.isfinite(completed_at) or completed_at <= 0
                or reconciled < available or available < completed_at):
            raise ValueError("cost_availability_clock_invalid")
        if knowledge_cutoff is not None and max(available, reconciled) > knowledge_cutoff:
            return {**missing, "status": "actual_cost_pending", "reason": "cost_after_knowledge_cutoff"}
        revision = receipt.get("revision")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
            raise ValueError("cost_revision_invalid")
        source = receipt.get("source") or {}
        raw = source.get("raw_statement")
        if (source.get("kind") != "broker_statement_exact_execution_costs"
                or source.get("environment") != "real"
                or source.get("allocation_scope") != "exact_execution"
                or not isinstance(raw, dict) or source.get("raw_sha256") != digest(raw)
                or raw.get("currency") != "KRW"
                or raw.get("legs") != receipt.get("legs")
                or any(raw.get(k) != context[k] for k in (
                    "position_key", "symbol", "account_scope_sha256", "buy_fill_identity"))):
            raise ValueError("cost_source_allocation_unproven")
        if not buy_legs or not sell_legs:
            raise ValueError("cost_execution_coverage_missing")
        expected = {}
        for side, legs in (("BUY", buy_legs), ("SELL", sell_legs)):
            for leg in legs:
                key = (side, str(leg["order_no"]), str(leg["execution_no"]))
                if key in expected:
                    raise ValueError("cost_execution_identity_duplicate")
                expected[key] = leg
        actual = {}
        total_cost = 0.0
        for leg in receipt.get("legs") or []:
            key = (leg["side"], str(leg["order_no"]), str(leg["execution_no"]))
            if key in actual or key not in expected:
                raise ValueError("cost_execution_identity_conflict")
            fill = expected[key]
            if (str(leg["trade_date"]) != str(fill["at"])[:10]
                    or _number(leg["qty"]) != _number(fill["qty"])
                    or _number(leg["price"]) != _number(fill["price"])
                    or leg.get("route") != fill.get("route")
                    or leg.get("route") not in {"KRX", "NXT", "SOR"}
                    or _number(leg["qty"]) <= 0 or _number(leg["price"]) <= 0):
                raise ValueError("cost_execution_quantity_price_or_route_mismatch")
            actual[key] = leg
            total_cost += _number(leg["fee_krw"]) + _number(leg["tax_krw"])
        if set(actual) != set(expected):
            raise ValueError("cost_execution_coverage_incomplete")
        buy_qty = sum(_number(x["qty"]) for x in buy_legs)
        sell_qty = sum(_number(x["qty"]) for x in sell_legs)
        buy_amount = sum(_number(x["qty"]) * _number(x["price"]) for x in buy_legs)
        sell_amount = sum(_number(x["qty"]) * _number(x["price"]) for x in sell_legs)
        if (not all(math.isfinite(value) for value in (
                buy_qty, sell_qty, buy_amount, sell_amount, total_cost))
                or buy_qty != sell_qty or buy_amount <= 0):
            raise ValueError("cost_final_quantity_unreconciled")
        exact = sell_amount - buy_amount - total_cost
        rate = exact / buy_amount * 100
        if not math.isfinite(exact) or not math.isfinite(rate):
            raise ValueError("cost_aggregate_economics_nonfinite")
        statement_pnl = float(receipt["realized_pnl_krw"])
        if (isinstance(receipt["realized_pnl_krw"], bool)
                or not math.isfinite(statement_pnl) or abs(statement_pnl - exact) > 0.01):
            raise ValueError("cost_statement_pnl_mismatch")
        return {"status": "actual_cost_reconciled", "actual_fees_taxes_krw": total_cost,
                "exact_pnl_krw": exact, "exact_profit_rate": rate,
                "cost_available_at": receipt["cost_available_at"],
                "reconciled_at": receipt["reconciled_at"], "revision": revision,
                "receipt_sha256": receipt["receipt_sha256"], "raw_sha256": source["raw_sha256"],
                "reason": None}
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return {**missing, "status": "actual_cost_invalid", "reason": str(exc)}
