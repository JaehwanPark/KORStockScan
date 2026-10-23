"""Quantity research costs allocated from confirmed broker day/symbol totals.

This is an offline research producer. Allocated costs never become exact fill
costs, canonical realized PnL, custody, or execution authority. Unknown account
activity keeps its own share of the confirmed total.
"""
from __future__ import annotations

from copy import deepcopy
from contextlib import ExitStack
from datetime import datetime
from decimal import Decimal, ROUND_FLOOR
import fcntl
import json
import math
import os
from pathlib import Path
import stat

from .broker_cost_reconciliation import (KST, digest, RESEARCH_COST_INDEX_SCHEMA,
                                         RESEARCH_COST_MAX_DATES, RESEARCH_COST_MAX_RECORDS)
from .broker_cost_source import atomic, load_source, number, rows, source_path, symbol, validate

SCHEMA = "initial_quantity_broker_total_allocated_cost_v1"
INDEX_SCHEMA = RESEARCH_COST_INDEX_SCHEMA
ALGORITHM = "broker_day_symbol_turnover_largest_remainder_v1"
SCOPE = "initial_quantity_research_only"
MAX_RECORDS = RESEARCH_COST_MAX_RECORDS
MAX_DATES = RESEARCH_COST_MAX_DATES
CACHED_RECEIPT_MAX_BYTES = 256 * 1024


def _clock(value):
    at = datetime.fromisoformat(str(value))
    return at.replace(tzinfo=KST) if at.tzinfo is None else at.astimezone(KST)


def _record(value):
    text = str(value)
    if isinstance(value, bool) or not text.isdigit() or int(text) <= 0:
        raise ValueError("research_cost_record_identity_invalid")
    return str(int(text))


def _legs(values):
    if not isinstance(values, list):
        raise ValueError("research_cost_fill_legs_missing")
    result = []
    seen = set()
    for leg in values:
        at = _clock(leg["at"])
        qty, price = number(leg["qty"]), number(leg["price"])
        order, execution = str(leg["order_no"]), str(leg["execution_no"])
        if (not order.isdigit() or not execution.isdigit() or not int(order)
                or not int(execution) or qty <= 0 or qty != qty.to_integral_value()
                or price <= 0 or leg.get("route") not in {"KRX", "NXT", "SOR"}):
            raise ValueError("research_cost_fill_identity_invalid")
        identity = (at.date().isoformat(), str(int(order)), str(int(execution)))
        if identity in seen:
            raise ValueError("research_cost_duplicate_fill")
        seen.add(identity)
        result.append((at, qty, qty * price, identity))
    return result


def fill_identity(values):
    parsed = _legs(values)
    return digest([{"at": at.isoformat(), "qty": str(qty), "amount": str(amount),
                    "order_no": identity[1], "execution_no": identity[2],
                    "route": leg["route"]}
                   for leg, (at, qty, amount, identity) in zip(values, parsed)])


def _custody_identity(record_id, custody_rows):
    keys = ("record_id", "owner_id", "owner_type", "account_key", "state",
            "filled_qty", "source_quality_reasons")
    selected = [{k: row.get(k) for k in keys} for row in custody_rows
                if str(row.get("record_id")) == str(record_id)]
    return digest(sorted(selected, key=digest))


def custody_account(record_id, buy_legs, custody_rows, *, allow_open=False):
    """Return the proven local account hash; never synthesize missing custody."""
    selected = [r for r in custody_rows if str(r.get("record_id")) == str(record_id)]
    qty = sum((leg[1] for leg in _legs(buy_legs)), Decimal(0))
    states = {"full", "partial_terminal"} | ({"partial_open", "cancel_pending"} if allow_open else set())
    if (not selected or qty <= 0 or any(
            r.get("source_quality_reasons") or r.get("state") not in states
            or r.get("owner_type") != "main_scalping"
            or r.get("owner_id") != "main_scalping:" + str(record_id)
            or not str(r.get("account_key") or "").strip()
            for r in selected)
            or sum((number(r.get("filled_qty")) for r in selected), Decimal(0)) != qty):
        raise ValueError("research_cost_main_custody_unproven")
    accounts = {str(r["account_key"]) for r in selected}
    if len(accounts) != 1:
        raise ValueError("research_cost_account_conflict")
    return digest(["broker_account", accounts.pop()])


def _missing(reason, *, status="research_cost_invalid", **extra):
    return {"schema": SCHEMA, "status": status, "reason": str(reason),
            "economics_scope": SCOPE, "cost_basis": "broker_confirmed_total_allocated",
            "actual_execution_cost": False, "allocated_fees_taxes_krw": None,
            "allocated_net_pnl_krw": None, "allocated_profit_rate": None, **extra}


def _split_integer(total, weights):
    """Allocate whole KRW with a deterministic largest remainder, including outside."""
    denominator = sum(weights.values(), Decimal(0))
    if denominator <= 0 or total != total.to_integral_value():
        raise ValueError("research_cost_total_or_turnover_invalid")
    exact = {key: total * weight / denominator for key, weight in weights.items()}
    result = {key: int(value.to_integral_value(rounding=ROUND_FLOOR)) for key, value in exact.items()}
    order = sorted(weights, key=lambda key: (-(exact[key] - result[key]), key))
    remainder = int(total) - sum(result.values())
    for key in order[:remainder]:
        result[key] += 1
    assert sum(result.values()) == int(total)
    return result


def _allocation_proofs(weights, allocated):
    keys = sorted(weights)
    levels = [[digest([key, str(weights[key]), allocated[key]]) for key in keys]]
    while len(levels[-1]) > 1:
        level = levels[-1]
        levels.append([digest(["research_cost_merkle_v1", level[i],
                               level[i + 1] if i + 1 < len(level) else level[i]])
                       for i in range(0, len(level), 2)])
    proofs = {}
    for index, key in enumerate(keys):
        proof = []
        for level in levels[:-1]:
            sibling = index - 1 if index % 2 else min(index + 1, len(level) - 1)
            proof.append({"side": "left" if index % 2 else "right", "sha256": level[sibling]})
            index //= 2
        proofs[key] = proof
    return levels[-1][0], proofs


def build_research_cost_allocations(sources_by_date, positions):
    """Allocate confirmed day/symbol totals across known Main turnover and outside.

    Open positions participate with observed fills. A completed record needs all
    its entry/exit dates, closed quantity and exact Main custody. Broker totals
    supply the denominator, so omitted/manual activity cannot inflate Main's share.
    """
    if not isinstance(positions, list) or len(positions) > MAX_RECORDS:
        raise ValueError("research_cost_population_limit")
    prepared, output, groups = {}, {}, {}
    for item in positions:
        record = _record(item["record_id"])
        if record in prepared or record in output:
            raise ValueError("research_cost_duplicate_record")
        try:
            stock = symbol(item["symbol"])
            buys, sells = _legs(item["buy_legs"]), _legs(item["sell_legs"])
            completed = str(item.get("status", "")).upper() == "COMPLETED"
            permitted = {"source_gap_sell_leg_configured_cost"}
            if not completed:
                permitted |= {"source_gap_final_sell_fill_missing", "source_gap_position_quantity_not_conserved",
                              "source_gap_buy_order_terminal_missing"}
            if set(item.get("execution_source_quality_reasons", [])) - permitted:
                raise ValueError("research_cost_execution_source_invalid")
            if completed and item.get("terminal_observed") is not True:
                raise ValueError("research_cost_terminal_unobserved")
            account = custody_account(record, item["buy_legs"], item.get("custody_rows", []),
                                      allow_open=not completed)
            if not buys:
                raise ValueError("research_cost_buy_fills_missing")
            running = Decimal(0)
            for at, sign, qty in sorted([(x[0], 0, x[1]) for x in buys]
                                        + [(x[0], 1, x[1]) for x in sells]):
                running += qty if sign == 0 else -qty
                if running < 0:
                    raise ValueError("research_cost_sell_precedes_buy")
            info = {"item": item, "symbol": stock, "buys": buys, "sells": sells,
                    "account": account, "parts": [], "issues": []}
            prepared[record] = info
            for side, legs in (("BUY", buys), ("SELL", sells)):
                for at, qty, amount, identity in legs:
                    day = at.date().isoformat()
                    group = groups.setdefault((day, stock), {"legs": [], "records": set(), "weights": {}})
                    group["legs"].append((record, side, at, qty, amount, identity))
                    group["records"].add(record)
                    group["weights"][record] = group["weights"].get(record, Decimal(0)) + amount
        except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
            output[record] = _missing(exc, record_id=record)
    if len({key[0] for key in groups}) > MAX_DATES:
        raise ValueError("research_cost_source_date_limit")
    for (day, stock), group in sorted(groups.items()):
        try:
            source = sources_by_date.get(day)
            if source is None:
                raise ValueError("research_cost_official_source_missing:" + day)
            validate(source, day)
            if {prepared[r]["account"] for r in group["records"]} != {source["local_account_key_sha256"]}:
                raise ValueError("research_cost_account_source_conflict")
            if len({leg[-1] for leg in group["legs"]}) != len(group["legs"]):
                raise ValueError("research_cost_fill_ownership_conflict")
            diary = [row for row in rows(source, "ka10170") if symbol(row.get("stk_cd")) == stock]
            if len(diary) != 1:
                raise ValueError("research_cost_diary_symbol_scope_ambiguous")
            row = diary[0]
            buy_amount, sell_amount = number(row["buy_amt"]), number(row["sell_amt"])
            total = number(row["cmsn_alm_tax"])
            denominator = buy_amount + sell_amount
            for side, official_qty, official_amount in (
                    ("BUY", number(row["buy_qty"]), buy_amount),
                    ("SELL", number(row["sell_qty"]), sell_amount)):
                selected = [leg for leg in group["legs"] if leg[1] == side]
                if (sum((leg[3] for leg in selected), Decimal(0)) > official_qty
                        or sum((leg[4] for leg in selected), Decimal(0)) > official_amount):
                    raise ValueError("research_cost_local_activity_exceeds_broker")
            observed = _clock(source["observations"]["ka10170"]["observed_at"])
            if any(leg[2] > observed for leg in group["legs"]):
                raise ValueError("research_cost_source_precedes_fill")
            weights = dict(group["weights"])
            outside = denominator - sum(weights.values(), Decimal(0))
            if outside < 0:
                raise ValueError("research_cost_turnover_exceeds_broker")
            if outside:
                weights["~outside"] = outside
            allocated = _split_integer(total, weights)
            allocation_root, proofs = _allocation_proofs(weights, allocated)
            cohort = {"source_date": day, "symbol": stock,
                      "source_sha256": source["source_sha256"], "observed_at": observed.isoformat(),
                      "broker_account_sha256": source["broker_account_sha256"],
                      "diary_row_sha256": digest(row), "confirmed_total_cost_krw": int(total),
                      "confirmed_buy_amount_krw": float(buy_amount),
                      "confirmed_sell_amount_krw": float(sell_amount),
                      "turnover_krw": float(denominator),
                      "outside_turnover_krw": float(outside),
                      "outside_allocated_cost_krw": allocated.get("~outside", 0),
                      "known_allocated_cost_krw": sum(allocated[r] for r in group["records"]),
                      "known_record_count": len(group["records"]),
                      "allocation_merkle_root": allocation_root}
            cohort["cohort_sha256"] = digest(cohort)
            for record in group["records"]:
                prepared[record]["parts"].append({**cohort,
                    "record_turnover_krw": str(weights[record]),
                    "allocated_cost_krw": allocated[record],
                    "allocation_membership_proof": proofs[record]})
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            for record in group["records"]:
                prepared[record]["issues"].append(str(exc))
    for record, info in prepared.items():
        item, buys, sells = info["item"], info["buys"], info["sells"]
        if info["issues"]:
            output[record] = _missing(";".join(sorted(set(info["issues"]))), record_id=record,
                                      required_dates=sorted({x[0].date().isoformat() for x in buys + sells}))
            continue
        buy_qty = sum((x[1] for x in buys), Decimal(0))
        sell_qty = sum((x[1] for x in sells), Decimal(0))
        if str(item.get("status", "")).upper() != "COMPLETED" or not sells or buy_qty != sell_qty:
            output[record] = _missing("research_cost_position_not_completed", record_id=record,
                                      status="research_cost_pending")
            continue
        try:
            completed = _clock(item["completed_at"])
            completion_date = completed.date().isoformat()
            if (completion_date != item["completion_observed_date"]
                    or max(x[0] for x in buys + sells) > completed):
                raise ValueError("research_cost_completion_clock_invalid")
            if len({part["broker_account_sha256"] for part in info["parts"]}) != 1:
                raise ValueError("research_cost_source_account_conflict")
            available = max(_clock(p["observed_at"]) for p in info["parts"])
            if available < completed:
                raise ValueError("research_cost_source_before_completion")
            buy_amount = sum((x[2] for x in buys), Decimal(0))
            sell_amount = sum((x[2] for x in sells), Decimal(0))
            fact_buy = number(item.get("fact_buy_price") if item.get("fact_buy_price") is not None else buy_amount / buy_qty)
            fact_sell = number(item.get("fact_sell_price") if item.get("fact_sell_price") is not None else sell_amount / sell_qty)
            if (abs(fact_buy - buy_amount / buy_qty) > 1
                    or abs(fact_sell - sell_amount / sell_qty) > 1):
                raise ValueError("research_cost_fact_reference_price_conflict")
            cost = sum(p["allocated_cost_krw"] for p in info["parts"])
            pnl = sell_amount - buy_amount - cost
            receipt = {"schema": SCHEMA, "status": "research_cost_allocated", "record_id": record,
                       "symbol": info["symbol"], "owner": "main", "economics_scope": SCOPE,
                       "cost_basis": "broker_confirmed_total_allocated", "actual_execution_cost": False,
                       "allocation_algorithm": ALGORITHM, "account_scope_sha256": info["account"],
                       "buy_fill_identity": fill_identity(item["buy_legs"]),
                       "sell_fill_identity": fill_identity(item["sell_legs"]),
                       "custody_sha256": _custody_identity(record, item.get("custody_rows", [])),
                       "completion_observed_date": completion_date,
                       "completed_at": completed.isoformat(), "cost_available_at": available.isoformat(),
                       "buy_qty": float(buy_qty), "sell_qty": float(sell_qty),
                       "fact_buy_price": float(fact_buy), "fact_sell_price": float(fact_sell),
                       "buy_amount_krw": float(buy_amount), "sell_amount_krw": float(sell_amount),
                       "allocated_fees_taxes_krw": cost, "allocated_net_pnl_krw": float(pnl),
                       "allocated_profit_rate": float(pnl / buy_amount * 100),
                       "sources": sorted(info["parts"], key=lambda p: p["source_date"])}
            receipt["receipt_sha256"] = digest(receipt)
            output[record] = receipt
        except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
            output[record] = _missing(exc, record_id=record)
    return output


def _verified(receipt, record_id, stock, completion_date, knowledge_cutoff=None):
    if (not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA
            or receipt.get("status") != "research_cost_allocated"
            or receipt.get("receipt_sha256") != digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
            or receipt.get("record_id") != _record(record_id) or receipt.get("symbol") != symbol(stock)
            or receipt.get("owner") != "main" or receipt.get("economics_scope") != SCOPE
            or receipt.get("actual_execution_cost") is not False
            or receipt.get("cost_basis") != "broker_confirmed_total_allocated"
            or receipt.get("allocation_algorithm") != ALGORITHM
            or receipt.get("completion_observed_date") != completion_date):
        raise ValueError("research_cost_receipt_contract_invalid")
    for key in ("account_scope_sha256", "buy_fill_identity", "sell_fill_identity", "custody_sha256"):
        value = receipt[key]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("research_cost_receipt_identity_invalid")
    completed, available = _clock(receipt["completed_at"]), _clock(receipt["cost_available_at"])
    if completed.date().isoformat() != completion_date or available < completed:
        raise ValueError("research_cost_receipt_clock_invalid")
    if knowledge_cutoff is not None:
        if isinstance(knowledge_cutoff, bool) or not math.isfinite(float(knowledge_cutoff)):
            raise ValueError("research_cost_knowledge_cutoff_invalid")
        if available.timestamp() > knowledge_cutoff:
            return _missing("research_cost_after_knowledge_cutoff", status="research_cost_pending")
    parts = receipt["sources"]
    if not isinstance(parts, list) or not 1 <= len(parts) <= MAX_DATES or len({p["source_date"] for p in parts}) != len(parts):
        raise ValueError("research_cost_receipt_sources_invalid")
    total = 0
    accounts = set()
    for part in parts:
        cohort = {k: v for k, v in part.items() if k not in {"record_turnover_krw", "allocated_cost_krw", "cohort_sha256", "allocation_membership_proof"}}
        if part["cohort_sha256"] != digest(cohort):
            raise ValueError("research_cost_cohort_hash_invalid")
        for key in ("allocated_cost_krw", "known_allocated_cost_krw", "outside_allocated_cost_krw", "confirmed_total_cost_krw"):
            if type(part[key]) is not int or part[key] < 0:
                raise ValueError("research_cost_cohort_cost_invalid")
        if (type(part["known_record_count"]) is not int or not 1 <= part["known_record_count"] <= MAX_RECORDS
                or part.get("symbol") != symbol(stock) or part["source_date"] > completion_date
                or _clock(part["source_date"] + "T00:00:00+09:00").date().isoformat() != part["source_date"]
                or number(part["turnover_krw"]) <= 0
                or number(part["confirmed_buy_amount_krw"]) + number(part["confirmed_sell_amount_krw"]) != number(part["turnover_krw"])
                or not 0 < number(part["record_turnover_krw"]) <= number(part["turnover_krw"])
                or number(part["outside_turnover_krw"]) > number(part["turnover_krw"])):
            raise ValueError("research_cost_cohort_activity_invalid")
        for key in ("source_sha256", "broker_account_sha256", "allocation_merkle_root", "diary_row_sha256"):
            if not isinstance(part[key], str) or len(part[key]) != 64 or any(c not in "0123456789abcdef" for c in part[key]):
                raise ValueError("research_cost_source_identity_invalid")
        accounts.add(part["broker_account_sha256"])
        if (type(part["allocated_cost_krw"]) is not int
                or part["known_allocated_cost_krw"] + part["outside_allocated_cost_krw"] != part["confirmed_total_cost_krw"]
                or _clock(part["observed_at"]) > available):
            raise ValueError("research_cost_cohort_conservation_invalid")
        proportional = (number(part["confirmed_total_cost_krw"]) * number(part["record_turnover_krw"])
                        / number(part["turnover_krw"]))
        floor = int(proportional.to_integral_value(rounding=ROUND_FLOOR))
        if part["allocated_cost_krw"] not in {floor, floor + (proportional != floor)}:
            raise ValueError("research_cost_proportional_share_invalid")
        leaf = digest([_record(record_id), str(number(part["record_turnover_krw"])), part["allocated_cost_krw"]])
        if len(part["allocation_membership_proof"]) > 15:
            raise ValueError("research_cost_membership_proof_limit")
        for sibling in part["allocation_membership_proof"]:
            if sibling["side"] == "left":
                leaf = digest(["research_cost_merkle_v1", sibling["sha256"], leaf])
            elif sibling["side"] == "right":
                leaf = digest(["research_cost_merkle_v1", leaf, sibling["sha256"]])
            else:
                raise ValueError("research_cost_membership_side_invalid")
        if leaf != part["allocation_merkle_root"]:
            raise ValueError("research_cost_membership_invalid")
        number(part["allocated_cost_krw"])
        total += part["allocated_cost_krw"]
    if len(accounts) != 1 or max(_clock(p["observed_at"]) for p in parts) != available:
        raise ValueError("research_cost_source_account_or_clock_conflict")
    buy, sell = number(receipt["buy_amount_krw"]), number(receipt["sell_amount_krw"])
    if (buy <= 0 or number(receipt["buy_qty"]) <= 0
            or number(receipt["buy_qty"]) != number(receipt["sell_qty"])
            or number(receipt["allocated_fees_taxes_krw"]) != total
            or abs(sum((number(p["record_turnover_krw"]) for p in parts), Decimal(0)) - buy - sell) > Decimal("0.00001")
            or abs(number(receipt["allocated_net_pnl_krw"], signed=True) - (sell - buy - total)) > Decimal("0.00001")
            or abs(number(receipt["allocated_profit_rate"], signed=True) - (sell - buy - total) / buy * 100) > Decimal("0.0000001")):
        raise ValueError("research_cost_receipt_amount_invalid")
    if (abs(number(receipt["fact_buy_price"]) - buy / number(receipt["buy_qty"])) > 1
            or abs(number(receipt["fact_sell_price"]) - sell / number(receipt["sell_qty"])) > 1):
        raise ValueError("research_cost_fact_reference_price_conflict")
    return deepcopy(receipt)


def validate_research_cost(receipt, *, record_id, symbol, buy_legs, sell_legs,
                           custody_rows, completion_date, knowledge_cutoff=None):
    try:
        result = _verified(receipt, record_id, symbol, completion_date, knowledge_cutoff)
        if result["status"] != "research_cost_allocated":
            return result
        if (receipt["buy_fill_identity"] != fill_identity(buy_legs)
                or receipt["sell_fill_identity"] != fill_identity(sell_legs)
                or receipt["account_scope_sha256"] != custody_account(record_id, buy_legs, custody_rows)
                or receipt["custody_sha256"] != _custody_identity(record_id, custody_rows)):
            raise ValueError("research_cost_context_identity_mismatch")
        return result
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return _missing(exc)


def validate_research_fact_cost(receipt, *, record_id, symbol, buy_qty, buy_price,
                               sell_qty, sell_price, completion_date, knowledge_cutoff=None):
    """Verify a receipt already bound by the native fact projection generation."""
    try:
        result = _verified(receipt, record_id, symbol, completion_date, knowledge_cutoff)
        if result["status"] != "research_cost_allocated":
            return result
        for side, qty, price in (("buy", buy_qty, buy_price), ("sell", sell_qty, sell_price)):
            if (number(receipt[side + "_qty"]) != number(qty)
                    or abs(number(receipt["fact_" + side + "_price"]) - number(price)) > Decimal("0.000001")):
                raise ValueError("research_cost_fact_amount_mismatch")
        return result
    except (ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return _missing(exc)


def refresh_native_research_costs(data_root, completion_date, *, completion_source):
    """Reallocate late costs from original native fills without resealing facts.

    The quantity owner verifies the original fact/projection seal before this
    call. A changed dated source refreshes only this derived allocation index;
    canonical PnL, policy receipts and original report bytes remain immutable.
    """
    from . import main_stop_research_cost as native
    from .research_input_budget import Claim
    root = Path(data_root)
    claims = []
    try:
        paths = native._admit_cost_inputs(root, completion_date, claims)
        registry = root / 'runtime/order_owner_registry.jsonl'
        if registry.exists():
            if registry.stat().st_size > native.MAX_REGISTRY_BYTES:
                raise ValueError('stop_research_registry_partition_required')
            claims.append(Claim(registry.stat().st_size * 12))
        paths.append(registry)
        before = native._signature(paths)
        return _refresh_native_research_costs(root, completion_date,
            completion_source=completion_source, input_paths=paths, input_signature=before)
    finally:
        for claim in claims:
            claim.close()


def _native_missing_buy_position(root, trade, position, registry, generation, registry_index):
    """Consume accepted BUY receipts when recovery emitted no pipeline event.

    This is a research projection of existing executions, not a reconstructed
    HOLDING event. Partial or conflicting pipeline executions stay excluded.
    """
    from . import main_stop_research_cost as native
    from src.engine.ai import holding_exit_vote as vote
    from src.engine.scalping.main_stop_quantity_source import _fill_facts
    from src.engine.sniper_trade_review_report import _quantity_registry_fill_custody
    missing = {'source_gap_buy_fill_missing', 'source_gap_negative_position_balance',
               'source_gap_position_quantity_not_conserved'}
    reasons = set(position['execution_source_quality_reasons'])
    if (position['buy_legs'] or not missing <= reasons
            or reasons - missing - {'source_gap_sell_leg_configured_cost'}
            or not position['terminal_observed'] or position['status'] != 'COMPLETED'):
        return position, None
    record = _record(position['record_id'])
    path = root/'runtime/holding_buy_fill_receipts'/(record+'.json')
    if not path.exists():
        return position, None
    from .research_input_budget import Claim
    with Claim(path.stat().st_size * 12):
        receipt = native._read(path, vote._BUY_FILL_RECEIPT_MAX_BYTES)
        stock = dict(id=int(record), code=trade['code'], buy_time=receipt.get('buy_time'),
                     buy_qty=trade['buy_qty'], buy_price=trade['buy_price'])
        entry_at, fact_at = _clock(stock['buy_time']), _clock(trade['buy_time'])
        if (receipt.get('source') != 'accepted_broker_execution'
                or fact_at not in {entry_at, entry_at.replace(microsecond=0)}
                or vote.restore_buy_fill_receipt(stock, root) != 'restored'
                or stock.get('_add_receipt_filled_by_order_no')
                or stock.get('_add_receipt_executions_by_order_no')):
            return position, None
        facts, identity = _fill_facts(stock)
        legs, hashes = [], []
        owners, _ = registry_index
        fills = [event for event in owners.get('main_scalping:'+record, [])
                 if event.get('event') == 'FILL_RECORDED']
        for leg in vote.buy_fill_legs_from_runtime(stock):
            matches = [event for event in fills if event.get('broker_order_no') == leg['order_no']
                       and event.get('execution_no') == leg['execution_no']]
            if len(matches) != 1:
                return position, None
            event = matches[0]
            signature = stock['_entry_receipt_executions_by_order_no'][leg['order_no']][leg['execution_no']]
            # A single complete execution per order supplies an exact price.
            # Do not infer per-fill clocks or prices from cumulative averages.
            at = _clock(event['observed_at_kst'])
            if (facts[leg['order_no']]['filled_qty'] != leg['qty']
                    or facts[leg['order_no']]['remaining_qty'] != 0
                    or signature.get('unit_exec_qty') != leg['qty']
                    or event.get('filled_qty') != leg['qty']
                    or event.get('fill_amount') != leg['qty'] * signature.get('unit_exec_price', 0)
                    or at.date().isoformat() != event.get('order_date')):
                return position, None
            legs.append(dict(at=at.isoformat(), order_no=leg['order_no'], execution_no=leg['execution_no'],
                qty=leg['qty'], price=signature['unit_exec_price'], route=event.get('route')))
            hashes.append(event['event_hash'])
        if (not legs or min(_clock(leg['at']) for leg in legs) != _clock(stock['buy_time'])
                or sum(number(leg['qty']) for leg in position['sell_legs']) != number(trade['buy_qty'])):
            return position, None
        custody = _quantity_registry_fill_custody(trade, {'buy_fill_legs':legs}, registry,
            generation, registry_index=registry_index)
        # The shared custody owner validates exact account/owner/route and the
        # complete registry fill census, including conflicting foreign claims.
        custody_account(record, legs, custody)
        proof = dict(receipt=native.byte_generation(path), buy_fill_identity=identity,
            registry_sha256=generation['sha256'], fill_event_hashes=sorted(hashes),
            clock_source='native_registry_fill_observed_at_kst')
        return {**position, 'buy_legs':legs, 'custody_rows':custody,
                'execution_source_quality_reasons':sorted(reasons-missing)}, proof


def _refresh_native_research_costs(root, completion_date, *, completion_source, input_paths, input_signature):
    from . import main_stop_research_cost as native
    from src.engine.automation import main_trailing_source_store as indexed
    from src.engine import sniper_trade_review_report as review
    from src.engine.sniper_trade_review_report import (
        _quantity_registry_index, _quantity_registry_fill_custody)
    directory = root / 'runtime/initial_quantity_research_costs' / completion_date
    index_path = directory / 'index.json'
    previous = native._read(index_path, 4 * 1024 * 1024) if index_path.exists() else {}
    if previous and (previous.get('schema') != INDEX_SCHEMA
            or previous.get('completion_date') != completion_date
            or previous.get('index_sha256') != digest({k:v for k,v in previous.items() if k != 'index_sha256'})):
        raise ValueError('research_cost_index_invalid')
    dates = previous.get('source_dates', [completion_date])
    if not isinstance(dates, list) or len(dates) > MAX_DATES:
        raise ValueError('research_cost_dependency_dates_invalid')
    rows = None
    extra_claims = []
    def completion_dates(rows):
        return {_clock(row.get('buy_time') or row['rec_date']).date().isoformat() for row in rows.values()} | {
            _clock(leg['at']).date().isoformat() for row in rows.values()
            for leg in (row.get('buy_fill_legs') or []) + (row.get('sell_fill_legs') or [])}
    try:
        # Legacy indices have no BUY-source contract. Read each original cohort
        # once when migrating; subsequent unchanged revisions reuse their sealed
        # native index without traversing the original timeline or raw windows.
        if (previous.get('native_revision') or {}).get('schema') != 'initial_quantity_late_cost_revision_v2':
            rows, proof, paths = native._native_projection(root, completion_date, execution_events=True)
            dates = sorted(set(dates) | completion_dates(rows))
        from .broker_cost_source import source_path, MAX_BYTES
        from .research_input_budget import Claim
        extra_paths = [source_path(root, day) for day in dates if source_path(root, day) not in input_paths]
        if input_signature != native._signature(input_paths):
            raise ValueError('research_cost_revision_source_changed')
        input_paths = input_paths + extra_paths
        input_signature = native._signature(input_paths)
        for path in extra_paths:
            if path.exists():
                if path.is_symlink() or path.stat().st_size > MAX_BYTES:
                    raise ValueError('research_cost_dependency_input_invalid')
                extra_claims.append(Claim(path.stat().st_size * 12))
        sources = {}
        for day in dates:
            if (not isinstance(day, str) or _clock(day + 'T00:00:00+09:00').date().isoformat() != day
                    or day > completion_date):
                raise ValueError('research_cost_dependency_dates_invalid')
            try:
                sources[day] = load_source(root, day)
            except (OSError, ValueError, TypeError, KeyError):
                sources[day] = None
        registry, registry_generation, registry_path = native._registry(root)
        records = rows.keys() if rows is not None else previous.get('receipts', {}).keys()
        buy_receipt_paths = [root/'runtime/holding_buy_fill_receipts'/(_record(record)+'.json')
                             for record in records]
        if input_signature != native._signature(input_paths):
            raise ValueError('research_cost_revision_source_changed')
        input_paths += buy_receipt_paths
        input_signature = native._signature(input_paths)
        buy_receipt_bytes = 0
        def buy_receipt_generation(path):
            nonlocal buy_receipt_bytes
            if not path.exists():
                return None
            metadata = path.lstat()
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError('research_cost_buy_receipt_not_regular')
            size = metadata.st_size
            buy_receipt_bytes += size
            if size > CACHED_RECEIPT_MAX_BYTES or buy_receipt_bytes > 4 * 1024 * 1024:
                raise ValueError('research_cost_buy_receipt_budget')
            return native.byte_generation(path)
        buy_receipts = {path.stem:buy_receipt_generation(path) for path in buy_receipt_paths}
        buy_sources = {}
        for day in dates:
            path = root/'pipeline_events'/f'pipeline_events_{day}.jsonl'
            if path.exists() or Path(str(path)+'.gz').exists():
                buy_sources[day] = indexed.generation(root, path)
        from .holding_window_generation import cached_code_generation
        engine = Path(__file__).resolve().parents[1]
        owners = ['lifecycle/broker_cost_allocation.py', 'lifecycle/main_stop_research_cost.py',
            'automation/main_trailing_source_store.py', 'sniper_trade_review_report.py',
            'lifecycle/broker_cost_source.py', 'lifecycle/broker_cost_reconciliation.py',
            'lifecycle/holding_window_generation.py', 'lifecycle/research_json_stream.py',
            'lifecycle/snapshot_archive.py', 'ai/holding_exit_vote.py',
            'scalping/main_stop_quantity_source.py']
        implementation = cached_code_generation([engine/name for name in owners])
        revision = dict(schema='initial_quantity_late_cost_revision_v2',
            completion_source_sha256=digest(completion_source), registry=registry_generation,
            official_sources={day:(source or {}).get('source_sha256') for day,source in sources.items()},
            buy_sources=buy_sources, native_buy_receipts=buy_receipts, allocation_algorithm=ALGORITHM,
            implementation={name:implementation[str(engine/name)] for name in owners})
        if all((previous.get('native_revision') or {}).get(key) == value for key,value in revision.items()):
            if input_signature != native._signature(input_paths):
                raise ValueError('research_cost_revision_source_changed')
            return previous
        if rows is None:
            rows, proof, paths = native._native_projection(root, completion_date, execution_events=True)
        for record in rows:
            if record not in buy_receipts:
                path = root/'runtime/holding_buy_fill_receipts'/(_record(record)+'.json')
                input_paths.append(path)
                input_signature[str(path)] = native._signature([path])[str(path)]
                buy_receipts[record] = buy_receipt_generation(path)
        # A new original completion generation can add an entry date. Admit
        # its official source before decoding, without a second timeline scan.
        added_dates = completion_dates(rows) - set(dates)
        if added_dates:
            if len(set(dates) | added_dates) > MAX_DATES or any(day > completion_date for day in added_dates):
                raise ValueError('research_cost_dependency_dates_invalid')
            if input_signature != native._signature(input_paths):
                raise ValueError('research_cost_revision_source_changed')
            added_paths = [source_path(root, day) for day in sorted(added_dates)]
            input_paths += added_paths
            input_signature = native._signature(input_paths)
            for day,path in zip(sorted(added_dates),added_paths):
                if path.exists():
                    if path.is_symlink() or path.stat().st_size > MAX_BYTES:
                        raise ValueError('research_cost_dependency_input_invalid')
                    extra_claims.append(Claim(path.stat().st_size * 12))
                try: sources[day] = load_source(root, day)
                except (OSError, ValueError, TypeError, KeyError): sources[day] = None
                logical = root/'pipeline_events'/f'pipeline_events_{day}.jsonl'
                if logical.exists() or Path(str(logical)+'.gz').exists():
                    buy_sources[day] = indexed.generation(root, logical)
            dates = sorted(set(dates) | added_dates)
            revision['official_sources'] = {day:(source or {}).get('source_sha256') for day,source in sources.items()}
        # The original native reader verifies bytes and census. Join its
        # original generation to the exact fact seal supplied by the caller.
        original_projection = dict(completion_source.get('projection') or {})
        original_projection.pop('dependency_receipt', None)
        original_projection.pop('snapshot_identity', None)
        if (completion_source.get('source_date') != completion_date
                or original_projection != proof.get('projection')
                or completion_source.get('actual_cost_source_generation') != proof.get('original_cost_generation')):
            raise ValueError('research_cost_original_completion_binding_invalid')
        paths = paths + input_paths
        before = native._signature(paths)
        registry_index = _quantity_registry_index(registry)
        observations = {}
        missing = {}
        def ledger_for(record):
            observations[record].sort(key=review._event_sort_key)
            return review._completed_execution_ledger(rows[record], observations[record])
        for record,row in rows.items():
            if 'timeline' not in row:
                continue
            observations[record] = [review.HoldingEvent(event['timestamp'], '', row['code'],
                event['stage'], event.get('fields') or {}, '') for event in row['timeline']]
            if ledger_for(record)['buy_filled_qty'] < number(row['buy_qty']):
                missing.setdefault(_clock(row.get('buy_time') or row['rec_date']).date().isoformat(), set()).add(record)
        recovered = []
        recovered_claim = Claim(0)
        extra_claims.append(recovered_claim)
        original_observations = {}
        seen_source_refs = set()
        def observation_key(event):
            return digest(dict(timestamp=event.timestamp, code=event.code, stage=event.stage, fields=event.fields))
        for record,events in observations.items():
            counts = original_observations[record] = {}
            for event in events:
                if event.stage in {'position_rebased_after_fill','scale_in_executed'}:
                    key = observation_key(event)
                    counts[key] = counts.get(key,0) + 1
        def add_observation(payload, reference):
            record = str(payload.get('record_id'))
            if record not in observations or str(payload.get('stock_code'))[:6] != rows[record]['code']:
                raise ValueError('research_cost_buy_record_binding_invalid')
            source_key = (reference['path'], reference['decoded_offset'], reference['size'], reference['sha256'])
            if source_key in seen_source_refs:
                return
            seen_source_refs.add(source_key)
            recovered_claim.grow(len(indexed.encode(payload)) * 12)
            fields = review._decode_threshold_json_fields(dict(payload.get('fields') or {}))
            fields['id'] = record
            event = review.HoldingEvent(str(payload['emitted_at'])[:19].replace('T',' '),
                '', rows[record]['code'], payload['stage'], fields, payload.get('text_payload') or '')
            key = observation_key(event)
            joined = original_observations[record].get(key,0) > 0
            if joined:
                original_observations[record][key] -= 1
            else:
                observations[record].append(event)
            # Join one identical original observation once. A second physical
            # event or conflicting payload still reaches native duplicate guards.
            recovered.append(dict(record_id=record, reference=reference, joined_original=joined))
        migration_io = {}
        for day,records in missing.items():
            if day not in buy_sources:
                continue  # Immutable source loss remains an invalid receipt.
            path = root/'pipeline_events'/f'pipeline_events_{day}.jsonl'
            for value,reference in indexed.read_rows(root, path, kinds=['pipeline_fill_receipt'], identities=sorted(records)):
                add_observation(value['row'], reference)
            remaining = {record for record in records if ledger_for(record)['buy_filled_qty'] < number(rows[record]['buy_qty'])}
            if remaining:
                migration_io[day] = indexed.read_order_fill_windows(root, path, remaining,
                    expected_generation=buy_sources[day], consume=add_observation)
        positions, native_buy_recoveries = [], {}
        cost_only = {'source_gap_sell_leg_configured_cost', 'source_gap_profit_rate_unreconciled',
                     'source_gap_exact_cost_missing', 'source_gap_broker_actual_cost_missing'}
        for record, row in rows.items():
            if record in observations:
                observations[record].sort(key=review._event_sort_key)
                ledger = ledger_for(record)
                custody = _quantity_registry_fill_custody(row, ledger, registry,
                    registry_generation, registry_index=registry_index)
                position = review._quantity_research_position(row, observations[record], ledger, custody)
                try:
                    position, recovery = _native_missing_buy_position(root, row, position,
                        registry, registry_generation, registry_index)
                except (ValueError, TypeError, KeyError, OSError) as exc:
                    if str(exc).startswith('shared_research_budget_'):
                        raise
                    position = {**position, 'execution_source_quality_reasons':
                        position['execution_source_quality_reasons'] + ['source_gap_native_buy_receipt_invalid']}
                    recovery = None
                if recovery is not None:
                    native_buy_recoveries[record] = recovery
                positions.append(position)
                continue
            buy, sell = row.get('buy_fill_legs'), row.get('sell_fill_legs')
            custody = _quantity_registry_fill_custody(row, {'buy_fill_legs':buy}, registry,
                registry_generation, registry_index=registry_index)
            positions.append(dict(record_id=record, symbol=row['code'], status='COMPLETED',
                buy_legs=buy, sell_legs=sell, custody_rows=custody,
                completion_observed_date=completion_date,
                completed_at=row.get('exact_sell_fill_time') or max(
                    (leg['at'] for leg in (sell or [])), key=_clock, default=None),
                terminal_observed=(row.get('terminal_decision_authority') == 'broker_sell_fill_observation_only'
                    and row.get('terminal_population_scope') == 'real_record_bound'
                    and row.get('sell_quantity_conserved') is True and row.get('position_residual_qty') == 0),
                fact_buy_price=row.get('buy_price'), fact_sell_price=row.get('sell_price'),
                execution_source_quality_reasons=sorted(set(row.get('strict_completion_reasons') or []) - cost_only)))
        needed = {completion_date}
        for item in positions:
            for leg in (item['buy_legs'] or []) + (item['sell_legs'] or []):
                needed.add(_clock(leg['at']).date().isoformat())
        if needed - set(dates):
            raise ValueError('research_cost_original_dependency_dates_missing')
        allocated = build_research_cost_allocations(sources, positions)
        receipts = {}
        for item in positions:
            record = item['record_id']; produced = allocated.get(record)
            receipts[record] = (produced if isinstance(produced, dict) and produced.get('status') in {
                'research_cost_invalid', 'research_cost_pending'} else validate_research_cost(produced,
                    record_id=record, symbol=item['symbol'], buy_legs=item['buy_legs'], sell_legs=item['sell_legs'],
                    custody_rows=item['custody_rows'], completion_date=completion_date))
        if before != native._signature(paths) or input_signature != native._signature(input_paths):
            raise ValueError('research_cost_revision_source_changed')
        for day,expected in buy_sources.items():
            if indexed.generation(root, root/'pipeline_events'/f'pipeline_events_{day}.jsonl') != expected:
                raise ValueError('research_cost_buy_generation_changed')
        revision.update(recovered_buy_events=recovered, migration_io=migration_io,
                        native_buy_recoveries=native_buy_recoveries)
        return persist_research_costs(root, completion_date, receipts, dates, native_revision=revision)
    finally:
        for claim in extra_claims + (rows.budget_claims if rows is not None else []):
            claim.close()


def persist_research_costs(data_root, completion_date, receipts, required_dates, *, native_revision=None):
    """Publish research receipts independently from immutable exact-cost receipts."""
    day = _clock(completion_date + "T00:00:00+09:00").date().isoformat()
    dates = sorted(set(required_dates))
    if len(dates) > MAX_DATES or any(d > day or _clock(d + "T00:00:00+09:00").date().isoformat() != d for d in dates):
        raise ValueError("research_cost_dependency_dates_invalid")
    directory = Path(data_root) / "runtime/initial_quantity_research_costs" / day
    if directory.is_symlink() or directory.parent.is_symlink():
        raise ValueError("research_cost_output_symlink")
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / "publisher.lock"
    with os.fdopen(os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), "a") as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode):
            raise ValueError("research_cost_lock_not_regular")
        fcntl.flock(lock, fcntl.LOCK_EX)
        with ExitStack() as stack:
            for source_date in dates:
                path = source_path(data_root, source_date).with_suffix(".lock")
                if path.parent.is_symlink():
                    raise ValueError("research_cost_source_lock_symlink")
                path.parent.mkdir(parents=True, exist_ok=True)
                handle = stack.enter_context(os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600), "a"))
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise ValueError("research_cost_source_lock_not_regular")
                fcntl.flock(handle, fcntl.LOCK_EX)
            current = {}
            for source_date in dates:
                try:
                    current[source_date] = load_source(data_root, source_date)
                except (ValueError, TypeError, KeyError, OSError):
                    # A malformed source has already excluded its own records;
                    # it cannot suppress unrelated verified allocations.
                    current[source_date] = None
            for record, receipt in receipts.items():
                if receipt.get("status") == "research_cost_allocated":
                    _verified(receipt, record, receipt["symbol"], day)
                    for part in receipt["sources"]:
                        observed = current.get(part["source_date"])
                        if observed is None or observed["source_sha256"] != part["source_sha256"]:
                            raise ValueError("research_cost_source_changed_before_publication")
            return _persist_locked(directory, day, receipts, dates, native_revision=native_revision)


def _persist_locked(directory, day, receipts, dates, *, native_revision=None):
    if not isinstance(receipts, dict) or len(receipts) > MAX_RECORDS:
        raise ValueError("research_cost_population_limit")
    refs = {}
    generations = directory / "generations"
    if generations.is_symlink():
        raise ValueError("research_cost_generation_symlink")
    generations.mkdir(exist_ok=True)
    for record, receipt in sorted(receipts.items()):
        record = _record(record)
        path = directory / (record + ".json")
        if path.is_symlink():
            raise ValueError("research_cost_output_symlink")
        generation = generations / (digest(receipt) + ".json")
        if generation.is_symlink():
            raise ValueError("research_cost_generation_symlink")
        if generation.exists():
            if generation.stat().st_size > CACHED_RECEIPT_MAX_BYTES or json.loads(generation.read_bytes()) != receipt:
                raise ValueError("research_cost_generation_collision")
        else:
            atomic(generation, receipt)
        if path.exists() and path.stat().st_size > CACHED_RECEIPT_MAX_BYTES:
            raise ValueError("research_cost_alias_size_limit")
        if not path.exists() or json.loads(path.read_bytes()) != receipt:
            atomic(path, receipt)
        refs[record] = digest(receipt)
    index = {"schema": INDEX_SCHEMA, "completion_date": day,
             "source_dates": dates, "receipts": refs}
    if native_revision is not None:
        index['native_revision'] = native_revision
    index["index_sha256"] = digest(index)
    path = directory / "index.json"
    if path.is_symlink():
        raise ValueError("research_cost_index_symlink")
    if path.exists() and path.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("research_cost_index_size_limit")
    if path.exists() and json.loads(path.read_bytes()) != index:
        # Retain the exact prior index bytes, in addition to its immutable
        # receipt bodies. A later cost correction is a new generation.
        import hashlib
        raw = path.read_bytes()
        history = directory / 'index_generations'
        if history.is_symlink():
            raise ValueError('research_cost_index_history_symlink')
        history.mkdir(exist_ok=True)
        archived = history / (hashlib.sha256(raw).hexdigest() + '.json')
        if archived.exists():
            if archived.is_symlink() or archived.read_bytes() != raw:
                raise ValueError('research_cost_index_history_collision')
        else:
            with os.fdopen(os.open(archived, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), 'wb') as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    if not path.exists() or json.loads(path.read_bytes()) != index:
        atomic(path, index)
    return index
