"""Completed-trade census and conditional initial-entry split research.

This producer is source-only. A lower observed price is a counterfactual fill
scenario, never a broker execution receipt or runtime policy approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import tempfile
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from src.trading.order.split_execution_math import pct_price_offset
from src.trading.order.tick_utils import get_tick_size, move_price_by_ticks
from src.engine.trade_profit import (calculate_net_profit_rate,
                                     calculate_net_realized_pnl, get_trade_cost_rate)
from src.engine.scalping.initial_quantity_type import (
    CLASSIFIER_VERSION, QUANTITY_TYPES as _TYPES,
    finite_number as _number,
    kst_timestamp as _timestamp, type_from_decision_receipt as _type_from_decision_receipt,
)
from src.utils.constants import DATA_DIR, PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

BASELINE = date(2026, 6, 5)
REPORT_SCHEMA = "initial_entry_quantity_completed_trade_replay_v1"
POLICY_SCHEMA = "initial_entry_quantity_type_policy_v1"
COST_MODEL = "canonical_sell_notional_only_v1"
CAP_FILL_MODEL = "actual_fill_prefix_bound_0d_0b_partial_v1"
REPAIR_VERSION = "initial_quantity_execution_cost_split_v2"

def refresh_window(parent):
    return max(BASELINE.isoformat(), "2026-09-29", str(parent["effective_from"]))

def canonical_epoch(value):
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        try:
            return int(value)
        except ValueError:
            return None
    return None

MAX_QUOTE_AGE_MS = 1000.0
LEG_TTL_SECONDS = 600
_RECORD_ID = re.compile(r'"record_id"\s*:\s*(?:"([^"\\]*)"|(\d+))')
_SHAPES = {
    "parent": (1.0, (0.0,)),
    "two_leg_0_0p3": (0.5, (0.0, 0.3)),
    "three_leg_0_0p3_0p8": (0.5, (0.0, 0.3, 0.8)),
    "two_leg_0_1tick": (0.5, (0, 1)),
    "three_leg_0_1_2tick": (0.5, (0, 1, 2)),
}
_TICK_SHAPES = {"two_leg_0_1tick", "three_leg_0_1_2tick"}
_CAP_MODES = {"cap_10pct": 0.10, "cap_15pct": 0.15,
              "cap_20pct": 0.20}


def _select_initial_winner_shape(
    quantity_type: str, candidates: dict[str, dict[str, Any]],
) -> str:
    """Choose a first seed from observed winner-weighted shapes.

    The first seed has no deployed predecessor to outperform. An unobserved
    split has no shape evidence; ties and unknown types keep the parent.
    """
    best = "parent"
    if quantity_type == "SAFE_UNKNOWN":
        return best
    parent_score = candidates.get("parent", {}).get(
        "winner_weighted_conservative_ev_pct")
    best_score = parent_score if isinstance(parent_score, (int, float)) else None
    for shape in _SHAPES:
        if shape == "parent":
            continue
        metric = candidates.get(shape) or {}
        score = metric.get("winner_weighted_conservative_ev_pct")
        if (metric.get("state") != "paired_with_parent_fallback"
                or not isinstance(metric.get("winner_comparable_count"), int)
                or metric["winner_comparable_count"] < 1
                or not isinstance(score, (int, float))
                or not math.isfinite(score)):
            continue
        if best_score is None or score > best_score + 1e-9:
            best, best_score = shape, score
    return best


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                     separators=(",", ":")).encode()).hexdigest()


def _pctl(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(len(ordered) * percentile) - 1
    return round(ordered[max(0, min(index, len(ordered) - 1))], 6)


def _block_io_wait_ms() -> float | None:
    try:
        stat = Path("/proc/self/stat").read_text()
        ticks = int(stat[stat.rfind(")") + 2:].split()[39])
        return 1000.0 * ticks / os.sysconf("SC_CLK_TCK")
    except (OSError, ValueError, IndexError):
        return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_quality_state(day: str, data_dir: Path) -> dict[str, Any]:
    path = data_dir / "report" / "observation_source_quality_audit" / f"observation_source_quality_audit_{day}.json"
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, ValueError):
        return {"status": "missing_or_invalid", "tuning_input_allowed": False,
                "artifact": str(path), "sha256": None}
    if not isinstance(payload, dict):
        return {"status": "invalid", "tuning_input_allowed": False,
                "artifact": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    status = str(payload.get("status") or "invalid")
    hard_count = _number(summary.get("hard_blocking_contract_gap_count"))
    allowed = (status in {"pass", "warning"}
               and payload.get("target_date") == day
               and summary.get("tuning_input_allowed") is True
               and hard_count == 0)
    excluded_ids=sorted({str(row['record_id']) for row in payload.get('hard_blocking_row_exclusions') or []
                         if isinstance(row,dict) and str(row.get('record_id') or '').isdigit()})
    return {"status": status, "tuning_input_allowed": allowed,
            "artifact": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
            **({'excluded_record_ids':excluded_ids} if excluded_ids else {}),
            "raw_row_exclusion_applied": bool(payload.get("raw_row_exclusion")
                                              or summary.get("raw_row_exclusion_applied"))}


def trade_source_allowed(census,trade):
    return all(source.get('tuning_input_allowed') is True and str(trade['record_id']) not in source.get('excluded_record_ids',[])
               for source in (census['source_quality_by_entry_date'][trade['entry_date']],census['source_quality_by_exit_date'][trade['exit_date']]))


def _quantity_compact_fact_issue(day, sidecar, dependency):
    """Join a producer-verified census to the fact seal through bounded metadata.

    The native dependency receipt already verifies the complete projection
    bytes and original snapshot identity. Its census digest binds the leading
    metadata; no timeline or completion row needs to be decoded again here.
    """
    import codecs
    import gzip
    import io
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    from src.engine.lifecycle.research_input_budget import Claim
    from src.engine.lifecycle.research_json_stream import Reader
    from src.engine.strategy_position_performance_report import _status_path, _canonical_sha256

    physical = sidecar if sidecar.is_file() else Path(str(sidecar) + '.gz')
    opener = gzip.open if physical.suffix == '.gz' else open
    with Claim(MAX_METADATA_BYTES * 8):
        with opener(physical, 'rb') as handle:
            prefix = handle.read(MAX_METADATA_BYTES)
        # A bounded prefix can end inside a UTF-8 code point. Invalid complete
        # sequences still fail; only the unfinished final code point is held.
        text = codecs.getincrementaldecoder('utf-8')().decode(prefix, final=False)
        reader = Reader(io.StringIO(text))
        reader.take('{')
        header = {}
        # This is the existing projection producer's order. Unexpected layouts
        # fail closed rather than scanning through an arbitrarily large field.
        for index, key in enumerate(('schema', 'date', 'code', 'since', 'meta')):
            if index:
                reader.take(',')
            if reader.value(1024) != key:
                return 'fact_snapshot_native_projection_metadata_invalid'
            reader.take(':')
            header[key] = reader.value(MAX_METADATA_BYTES)
        meta = header.get('meta')
        census = meta.get('completed_census_manifest') if isinstance(meta, dict) else None
        if (header.get('schema') != 'trade_review_completed_projection_sidecar_v1'
                or header.get('date') != day or header.get('code') or header.get('since')
                or not isinstance(census, dict)
                or census.get('source_date') != day
                or census.get('schema') != 'trade_review_completed_census_v1'
                or digest(census) != dependency.get('census_sha256')
                or meta.get('snapshot_profile') != dependency.get('profile')
                or meta.get('actual_cost_source_generation') != dependency.get('cost_generation')):
            return 'fact_snapshot_native_projection_metadata_invalid'
        status_path = _status_path(day)
        try:
            if status_path.is_symlink() or status_path.stat().st_size > MAX_METADATA_BYTES:
                return 'fact_sync_receipt_missing_or_invalid'
            with status_path.open('rb') as handle:
                raw = handle.read(MAX_METADATA_BYTES + 1)
            if len(raw) > MAX_METADATA_BYTES:
                return 'fact_sync_receipt_missing_or_invalid'
            receipt = json.loads(raw)
        except (OSError, ValueError):
            return 'fact_sync_receipt_missing_or_invalid'
        if not isinstance(receipt, dict):
            return 'fact_sync_receipt_missing_or_invalid'
        expected_sha = receipt.pop('artifact_sha256', None)
        if expected_sha != _canonical_sha256(receipt):
            return 'fact_sync_receipt_sha_mismatch'
        if receipt.get('target_date') != day or receipt.get('status') not in {'succeeded', 'valid_empty'}:
            return 'fact_sync_receipt_not_current_success'
        if (receipt.get('completed_census_run_ids') != [census.get('run_id')]
                or receipt.get('completed_census_projection_sha256') != [census.get('projection_sha256')]):
            return 'stale_fact_source_generation'
        if receipt.get('actual_cost_source_generation') != dependency.get('cost_generation'):
            return 'persisted_fact_cost_generation_stale'
        proof = receipt.get('completion_snapshot_source')
        if proof is not None:
            from src.engine.lifecycle.snapshot_archive import generation
            fact_path = sidecar.with_name(f'trade_review_{day}.fact_projection.json')
            if (not isinstance(proof, dict) or proof.get('schema') != 'strategy_position_fact_snapshot_source_v1'
                    or proof.get('source_date') != day or proof.get('projection') != dependency.get('projection')
                    or proof.get('actual_cost_source_generation') != dependency.get('cost_generation')
                    or not re.fullmatch(r'[0-9a-f]{64}', str(proof.get('scalar_projection_sha256') or ''))):
                return 'stale_fact_snapshot_projection_generation'
            if proof.get('source_basis') == 'native_original_snapshot_stream':
                if proof.get('fact_projection') is not None:
                    return 'stale_fact_snapshot_projection_generation'
            elif (proof.get('source_basis') != 'native_bounded_fact_projection'
                    or proof.get('fact_projection') != generation(fact_path)):
                return 'stale_fact_snapshot_projection_generation'
    return None


def _quantity_fact_generation_issue(day):
    """Validate the native fact seal without loading historical timelines.

    Oversized legacy snapshots need the original bounded native projection;
    a missing projection is a dated source gap, not a reason to exhaust RAM.
    """
    from src.engine.strategy_position_performance_report import _saved_fact_generation_issue, _legacy_original_generation_issue
    legacy, issue = _legacy_original_generation_issue(day, data_dir=DATA_DIR)
    if legacy:
        return issue
    from src.engine.log_archive_service import MONITOR_SNAPSHOT_DIR
    from src.engine.lifecycle.holding_window_generation import _capture_day, MAX_PROJECTION_BYTES, source_stat
    from src.engine.lifecycle.research_input_budget import Claim
    from src.engine.lifecycle.snapshot_archive import identity_available, present
    import gzip
    directory = MONITOR_SNAPSHOT_DIR
    path = directory / f'trade_review_{day}.json'
    sidecar = path.with_suffix('.completed_projection.json')
    candidate = sidecar if ((present(sidecar) and identity_available(path))
                            or (path.is_file() and path.stat().st_size > MAX_PROJECTION_BYTES)) else path
    if candidate == sidecar and present(sidecar):
        # Bind both logical sources and any native archive receipts while the
        # native verifier hashes the projection and the bounded reader joins it.
        sources = tuple(p for logical in (path, sidecar)
                        for p in (logical, Path(str(logical) + '.gz'),
                                  Path(str(logical) + '.gz.archive_receipt.json'))
                        ) + (Path(str(sidecar) + '.dependencies.json'),)
        try:
            before = tuple((str(p), source_stat(p.stat()) if p.exists() else None) for p in sources)
            dependency = _capture_day(DATA_DIR, directory, day)
            issue = _quantity_compact_fact_issue(day, sidecar, dependency)
            after = tuple((str(p), source_stat(p.stat()) if p.exists() else None) for p in sources)
            if before != after:
                return 'fact_snapshot_native_projection_changed_during_read'
            return issue
        except (OSError, ValueError, TypeError, KeyError) as exc:
            if str(exc).startswith('shared_research_budget_'):
                raise
            if str(exc) == 'window_dependency_legacy_metadata_required':
                return 'fact_snapshot_requires_bounded_native_projection'
            if str(exc) in {'research_legacy_json_incomplete', 'research_legacy_json_field_partition_required',
                            'window_dependency_metadata_budget_exceeded'}:
                return 'fact_snapshot_requires_bounded_native_metadata'
            return 'fact_snapshot_native_projection_invalid'
    if not candidate.exists() and Path(str(path)+'.gz').exists():
        candidate = Path(str(path)+'.gz')
    if not candidate.exists():
        return 'trade_review_snapshot_missing'
    if candidate.stat().st_size > MAX_PROJECTION_BYTES:
        return 'fact_snapshot_requires_bounded_native_projection'
    try:
        with Claim(MAX_PROJECTION_BYTES * 8):
            opener = gzip.open if candidate.suffix == '.gz' else open
            with opener(candidate, 'rb') as handle:
                raw = handle.read(MAX_PROJECTION_BYTES + 1)
            if len(raw) > MAX_PROJECTION_BYTES:
                return 'fact_snapshot_requires_bounded_native_projection'
            snapshot = json.loads(raw)
            return _saved_fact_generation_issue(day, snapshot=snapshot)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        if 'budget' in str(exc):
            raise
        return 'fact_snapshot_native_projection_invalid'


def _read_trade_facts(as_of: str, *, entry_on_or_after: str | None = None) -> list[dict[str, Any]]:
    """Read the completed-trade fact owner without mutating its database."""
    from sqlalchemy import or_
    from src.database.db_manager import DBManager
    from src.database.models import TradePerformanceFact

    start = max(BASELINE, date.fromisoformat(entry_on_or_after)) if entry_on_or_after else BASELINE
    end = date.fromisoformat(as_of)
    from src.engine.strategy_position_performance_report import _saved_fact_generation_issue, _status_path
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.lifecycle.research_input_budget import Claim
    from sqlalchemy import text
    from src.engine.scalping.initial_quantity_source_cache import QUANTITY_FACT_STRATEGIES, QUANTITY_FACT_CUSTODIES
    keys = ("recommendation_id", "rec_date", "stock_code", "strategy", "position_tag", "status",
            "buy_price", "buy_qty", "buy_time", "sell_price", "sell_time", "profit_rate",
            "realized_pnl_krw", "add_count", "avg_down_count", "pyramid_count",
            "economics_source_status", "actual_cost_reconciliation_status", "actual_cost_source_generation",
            "completion_census_run_id", "completion_census_projection_sha256", "broker_actual_fees_taxes_krw")
    with DBManager().get_session() as session, Claim(0) as resident:
        if session.bind.dialect.name == "postgresql":
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
        query = session.query(*(getattr(TradePerformanceFact,k) for k in keys)).filter(
            or_(TradePerformanceFact.rec_date >= start, TradePerformanceFact.buy_time >= datetime.combine(start,datetime.min.time())),
            or_(TradePerformanceFact.rec_date <= end, TradePerformanceFact.buy_time < datetime.combine(end+timedelta(days=1),datetime.min.time())),
            TradePerformanceFact.strategy.in_(QUANTITY_FACT_STRATEGIES),
            TradePerformanceFact.position_tag.in_(QUANTITY_FACT_CUSTODIES))
        days = [row[0].isoformat() for row in query.with_entities(TradePerformanceFact.rec_date).distinct()]
        generations = {}
        for day in days:
            path = _status_path(day)
            issue = _quantity_fact_generation_issue(day)
            costs=source_generation(DATA_DIR,day)
            if issue is None and json.loads(path.read_bytes()).get('actual_cost_source_generation')!=costs:
                issue='persisted_fact_cost_generation_stale'
            generations[day] = {"path":str(path), "sha256":_file_sha256(path) if path.is_file() else None,
                                "issue":issue,"cost_generation":costs}
        rows=[]
        for fact in query.order_by(TradePerformanceFact.recommendation_id).yield_per(256):
            row = {k:(value.isoformat() if isinstance(value,(date,datetime)) else value) for k,value in zip(keys,fact)}
            row["fact_generation"] = generations[row["rec_date"]]
            resident.grow(len(json.dumps(row,default=str).encode())*8)
            rows.append(row)
        for day,gen in generations.items():
            path=Path(gen["path"])
            if (gen["sha256"] != (_file_sha256(path) if path.exists() else None)
                    or gen['cost_generation']!=source_generation(DATA_DIR,day)):
                raise ValueError("quantity_fact_generation_changed_during_snapshot")
        from src.engine.scalping.initial_quantity_source_cache import completion_overlay
        overlaid = completion_overlay(rows, as_of=as_of, data_dir=DATA_DIR,
            entry_on_or_after=start.isoformat(), entry_generations=generations,
            validate_day=_quantity_fact_generation_issue)
        for day, gen in generations.items():
            path = Path(gen['path'])
            if (gen['sha256'] != (_file_sha256(path) if path.exists() else None)
                    or gen['cost_generation'] != source_generation(DATA_DIR, day)):
                raise ValueError('quantity_fact_generation_changed_during_snapshot')
        return overlaid


def completed_trade_fact_census(as_of: str, *, fact_rows: list[dict[str, Any]] | None = None,
                                data_dir: Path = DATA_DIR,
                                entry_on_or_after: str | None = None,
                                source_census: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Seal every eligible completed initial position from the costed fact owner."""
    date.fromisoformat(as_of)
    refresh_start = date.fromisoformat(entry_on_or_after) if entry_on_or_after else None
    from src.engine.scalping.initial_quantity_source_cache import ResidentFacts
    raw_source = (_read_trade_facts(as_of, entry_on_or_after=entry_on_or_after)
                  if fact_rows is None else fact_rows)
    source = ResidentFacts(sorted(raw_source, key=lambda item: str(item.get("recommendation_id") or "")
                    if isinstance(item, dict) else ""),claim=raw_source.claim if isinstance(raw_source,ResidentFacts) else None)
    if source_census is not None and (not isinstance(source_census, dict)
            or source_census.get('input_manifest_sha256') != _digest(source)
            or source_census.get('input_manifest_sha256') != _digest(source_census.get('input_fact_rows'))
            or source_census.get('entry_on_or_after') != entry_on_or_after):
        raise ValueError('quantity_shared_fact_census_mismatch')
    # JSON rows carry their economics and exact terminal references. The full
    # native census also observes foreign/excluded terminals, including when no
    # economic rows remain. Preserve that separate context explicitly during a
    # shared or serialized replay; list attributes alone do not survive JSON.
    completion_generations = (source_census.get('completion_overlay_generations', {})
        if source_census is not None else getattr(raw_source, 'completion_generations', {}))
    completion_summary = (source_census.get('completion_overlay_summary', {})
        if source_census is not None else getattr(raw_source, 'completion_overlay_summary', {}))
    if (not isinstance(completion_generations, dict) or not isinstance(completion_summary, dict)
            or completion_summary and completion_summary.get('as_of') != as_of):
        raise ValueError('quantity_shared_fact_census_mismatch')
    if source_census is not None:
        from src.engine.scalping.initial_quantity_source_cache import verify_completion_census_context
        verify_completion_census_context(source, source_census, as_of=as_of,
            data_dir=data_dir, entry_on_or_after=entry_on_or_after)
    source.completion_generations = completion_generations
    source.completion_overlay_summary = completion_summary
    exclusions: Counter[str] = Counter()
    rows: dict[str, dict[str, Any]] = {}
    conflicts: set[str] = set()
    raw_identity={}
    for fact in source:
        if not isinstance(fact,dict) or not fact.get('recommendation_id'):continue
        identity=str(fact['recommendation_id'])
        if identity in raw_identity and raw_identity[identity]!=fact:
            conflicts.add(identity)
        else:raw_identity[identity]=fact
    cost_rate = get_trade_cost_rate()
    for fact in source:
        if not isinstance(fact, dict):
            exclusions["invalid_fact_row"] += 1
            continue
        if str(fact.get('recommendation_id') or '') in conflicts:
            exclusions['conflicting_duplicate_fact']+=1
            continue
        if isinstance(fact.get("fact_generation"), dict) and fact["fact_generation"].get("issue"):
            exclusions["persisted_fact_generation_invalid"] += 1
            continue
        if str(fact.get("status") or "").upper() != "COMPLETED":
            exclusions["not_completed"] += 1
            continue
        if str(fact.get("strategy") or "").upper() not in {"SCALPING", "SCALP"}:
            exclusions["other_strategy"] += 1
            continue
        if str(fact.get("position_tag") or "").upper() not in {"SCANNER", "SCALP_BASE"}:
            exclusions["other_custody"] += 1
            continue
        if any(_number(fact.get(key)) not in (None, 0) for key in
               ("add_count", "avg_down_count", "pyramid_count")):
            exclusions["scale_in_position"] += 1
            continue
        rid = str(fact.get("recommendation_id") or "").strip()
        buy_at = _timestamp(fact.get("buy_time"))
        sell_at = _timestamp(fact.get("sell_time"))
        buy_price = _number(fact.get("buy_price"))
        sell_price = _number(fact.get("sell_price"))
        qty = _number(fact.get("buy_qty"))
        profit = _number(fact.get("profit_rate"))
        pnl = _number(fact.get("realized_pnl_krw"))
        if not rid or not str(fact.get("stock_code") or ""):
            exclusions["identity_missing"] += 1
            continue
        if not buy_at or not sell_at or sell_at <= buy_at:
            exclusions["trade_clock_missing_or_invalid"] += 1
            continue
        if not BASELINE <= buy_at.date() <= sell_at.date() <= date.fromisoformat(as_of):
            exclusions["date_outside_baseline_or_as_of"] += 1
            continue
        if refresh_start and buy_at.date() < refresh_start:
            exclusions["before_refresh_start"] += 1
            continue
        if (buy_price is None or buy_price <= 0 or sell_price is None or sell_price <= 0
                or qty is None or qty <= 0 or not qty.is_integer()
                or profit is None or pnl is None):
            exclusions["terminal_cost_or_quantity_missing"] += 1
            continue
        expected_pnl = calculate_net_realized_pnl(buy_price, sell_price, qty,
                                                   cost_rate=cost_rate)
        expected_profit = calculate_net_profit_rate(buy_price, sell_price,
                                                    cost_rate=cost_rate)
        actual = fact.get("economics_source_status") == "broker_actual_cost_reconciled"
        if actual:
            fees = _number(fact.get("broker_actual_fees_taxes_krw"))
            notional = buy_price * qty
            actual_expected = (sell_price - buy_price) * qty - (fees or 0)
            generation=fact.get('actual_cost_source_generation')
            if isinstance(generation,str) and generation.startswith('{'):
                try:generation=json.loads(generation)
                except ValueError:generation=None
            generation_valid=bool(re.fullmatch(r'[0-9a-f]{64}',generation or '')) if isinstance(generation,str) else bool(
                isinstance(generation,dict) and generation.get('schema')=='holding_actual_cost_source_generation_v1'
                and generation.get('completion_date')==str(fact.get('completion_source_date') or fact.get('rec_date'))
                and re.fullmatch(r'[0-9a-f]{64}',str(generation.get('sha256') or ''))
                and type(generation.get('count')) is int and generation['count']>=0)
            if (fees is None or fees < 0
                    or fact.get("actual_cost_reconciliation_status") != "actual_cost_reconciled"
                    or not fact.get("completion_census_run_id")
                    or not generation_valid
                    or not re.fullmatch(r"[0-9a-f]{64}", str(fact.get('completion_census_projection_sha256') or ""))
                    or abs(actual_expected - pnl) > 1
                    or abs(100 * actual_expected / notional - profit) > 0.02):
                exclusions["actual_cost_identity_or_amount_invalid"] += 1
                continue
        elif (fact.get("economics_source_status") not in (None, "configured_comparison_model", "fixed_comparison_cost_model")
              or buy_at.date() >= date(2026, 9, 29)):
            exclusions["actual_cost_provenance_missing"] += 1
            continue
        elif abs(expected_pnl - pnl) > 1 or abs(expected_profit - profit) > 0.02:
            exclusions["terminal_cost_contract_mismatch"] += 1
            continue
        row = {"trade_id": f"fact:{rid}", "record_id": rid,
               "entry_date": buy_at.date().isoformat(),
               "exit_date": sell_at.date().isoformat(),
               "stock_code": str(fact["stock_code"]),
               "buy_price": buy_price, "sell_price": sell_price,
               "buy_qty": int(qty), "profit_rate": profit,
               "realized_net_pnl_krw": pnl,
               "exit_at": sell_at.isoformat(),
               "entry_at_fact_buy_time": buy_at.isoformat(),
               "entry_date_source": "trade_performance_facts.buy_time",
               "terminal_source": ("native_completion_date_projection.completed_costed"
                    if fact.get('completion_generation') else "trade_performance_facts.completed_costed"),
               **({"completion_generation": fact['completion_generation'],
                   "completion_source_date": fact['completion_source_date'],
                   "fact_generation": fact.get('fact_generation')}
                  if fact.get('completion_generation') else {}),
               "cost_basis": "broker_actual" if actual else "historical_comparison_model",
               "modeled_parent_net_pnl_krw": _costed_fixed_exit_pnl(
                    [(int(qty), buy_price)], sell_price, cost_rate)}
        prior = rows.get(rid)
        if rid in conflicts:
            exclusions["conflicting_duplicate_fact"] += 1
        elif prior is not None and prior != row:
            exclusions["conflicting_duplicate_fact"] += 2
            rows.pop(rid, None)
            conflicts.add(rid)
        elif prior is None:
            rows[rid] = row
        else:
            exclusions["duplicate_fact"] += 1
    result = sorted(rows.values(), key=lambda item: (item["entry_date"], item["record_id"]))
    entry_days = sorted({row["entry_date"] for row in result})
    exit_days = sorted({row["exit_date"] for row in result})
    census = {"census_source": "trade_performance_facts",
                    **({"entry_on_or_after": entry_on_or_after} if refresh_start else {}),
                    "all_completed_initial_trades": len(result),
                    "actual_completed_net_pnl_krw": (round(sum(
                        row["realized_net_pnl_krw"] for row in result), 3)
                        if result else None),
                    "actual_completed_mean_profit_rate_pct": (
                        round(sum(row["profit_rate"] for row in result) / len(result), 6)
                        if result else None),
                    "fact_rows_read": len(source), "excluded": dict(sorted(exclusions.items())),
                    "as_of_completed_population_count": sum(str(f.get('status')).upper() == 'COMPLETED'
                        for f in source if isinstance(f, dict)),
                    "completion_overlay_generations": completion_generations,
                    "completion_overlay_summary": completion_summary,
                    "cost_rate": cost_rate, "input_fact_rows": source,
                    "input_manifest_sha256": _digest(source),
                    "persisted_fact_generations": {str(f.get("rec_date")): f["fact_generation"] for f in source if isinstance(f,dict) and isinstance(f.get("fact_generation"),dict)},
                    "source_quality_by_entry_date": {
                        day: _source_quality_state(day, data_dir) for day in entry_days},
                    "source_quality_by_exit_date": {
                        day: _source_quality_state(day, data_dir) for day in exit_days}}
    if source_census is not None and census != source_census:
        raise ValueError('quantity_shared_fact_census_mismatch')
    return result, census


def _record_id(raw: str) -> str:
    match = _RECORD_ID.search(raw)
    if match is None:
        return ""
    return match.group(1) or match.group(2)


def _exit_at(trade: dict[str, Any]) -> datetime | None:
    return _timestamp(trade.get("exit_at"))


def _fresh_observed_price(fields: dict[str, Any]) -> tuple[float | None, str]:
    """Never use an unclocked current_price_observed as a post-fill print."""
    if str(fields.get("quote_stale") or "").lower() in {"true", "1"}:
        return None, "stale_quote"
    consistency = str(fields.get("quote_consistency_state") or "").strip().lower()
    if consistency and consistency not in {"ok", "warning", "single_source"}:
        return None, "quote_consistency_invalid"
    age = _number(fields.get("ws_age_ms"))
    price = _number(fields.get("latest_price"))
    if price and price > 0 and age is not None and 0 <= age <= MAX_QUOTE_AGE_MS:
        return price, "fresh_ws_latest_price"
    return None, "price_source_clock_missing_or_stale"


def join_post_fill_paths(trades, **kwargs):
    from src.engine.scalping.initial_quantity_source_cache import join
    return join(trades, **kwargs)


def _quantity_capture_lifecycle_sources(data_dir, day, *, decode=False):
    """Bound native closed receipts without adopting a later process's identity."""
    from src.engine.scalping.initial_quantity_cap_observation import MAX_RECEIPT_BYTES, _capture_id
    from src.engine.lifecycle.holding_window_generation import source_stat
    directory = Path(data_dir) / 'runtime/initial_quantity/cap_capture_receipts' / day
    if directory.is_symlink() or any(p.is_symlink() for p in directory.parents):
        raise ValueError('quantity_capture_receipt_path_invalid')
    paths = []
    for path in directory.glob('*.json'):
        if len(paths) >= 4096:
            raise ValueError('quantity_capture_receipt_partition_required')
        paths.append(path)
    from src.engine.scalping.initial_quantity_source_cache import ResidentFacts
    generation, receipts = [], ResidentFacts([]) if decode else []
    for path in sorted(paths):
        before = source_stat(path.stat())
        if path.is_symlink() or before[2] > MAX_RECEIPT_BYTES or not re.fullmatch(r'[0-9a-f]{64}', path.stem):
            raise ValueError('quantity_capture_receipt_path_invalid')
        with path.open('rb') as handle:
            raw = handle.read(MAX_RECEIPT_BYTES + 1)
        if len(raw) > MAX_RECEIPT_BYTES or source_stat(path.stat()) != before:
            raise ValueError('quantity_capture_receipt_changed_during_read')
        generation.append({'path': str(path), 'size': len(raw),
                           'sha256': hashlib.sha256(raw).hexdigest()})
        if not decode:
            continue
        body = json.loads(raw)
        fields = body.get('fields') if isinstance(body, dict) else None
        if not isinstance(fields, dict):
            raise ValueError('quantity_capture_receipt_identity_invalid')
        capture_id = _capture_id(fields)
        if (body.get('schema') != 'initial_quantity_cap_capture_lifecycle_v1'
                or body.get('sha256') != _digest({k: v for k, v in body.items() if k != 'sha256'})
                or body.get('capture_id') != path.stem or capture_id != path.stem
                or fields.get('capture_source_date') != day
                or canonical_epoch(fields.get('capture_runtime_pid')) in (None, 0)
                or canonical_epoch(fields.get('capture_runtime_start_ticks')) in (None, 0)
                or not fields.get('entry_submit_attempt_id')
                or not re.fullmatch(r'[0-9a-f]{64}', str(fields.get('entry_execution_sizing_plan_sha256') or ''))
                or body.get('status') not in {'finished', 'interrupted'}
                or body.get('raw_event_durable') is not True
                or not re.fullmatch(r'[0-9a-f]{64}', str(body.get('raw_event_id') or ''))
                or body.get('raw_event_identity_contract') != 'canonical_original_pipeline_event_sha256_v1'
                or body.get('raw_event_stage') != 'initial_quantity_cap_capture_' + body.get('status')
                or not re.fullmatch(r'[0-9]{6}', str(body.get('code') or ''))
                or canonical_epoch(body.get('record_id')) in (None, 0)
                or str(fields.get('capture_record_id')) != str(body.get('record_id'))
                or fields.get('capture_stock_code') != body.get('code')
                or body.get('runtime_effect') is not False):
            raise ValueError('quantity_capture_receipt_identity_invalid')
        receipts.append(body)
    return {'schema': 'initial_quantity_cap_capture_source_generation_v1',
            'source_date': day, 'files': generation}, receipts


def _join_post_fill_paths_uncached(trades: list[dict[str, Any]], *, data_dir: Path = DATA_DIR,
                         scan_seconds: dict[str, float] | None = None,
                         source_receipts: dict[str, Any] | None = None,
                         price_horizon_seconds: int = LEG_TTL_SECONDS) -> dict[str, dict[str, Any]]:
    """Stream only matching record IDs from each native pipeline partition."""
    by_date: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for trade in trades:
        by_date[trade["entry_date"]][trade["record_id"]].append(trade)
    from src.engine.scalping.initial_quantity_source_cache import ResidentPaths, BoundedRows
    result = ResidentPaths()
    for trade in trades:
        entry_clock = _timestamp(trade.get("entry_at_fact_buy_time"))
        exit_clock = _exit_at(trade)
        result[trade["trade_id"]] = {
            "decisions": [], "fills": [], "prices": [], "order_starts": [],
            "order_requests": [], "order_sent": [], "cap_ticks": [],
            "capture_receipts": [],
            "source_path": None, "source_gap": [],
            "join_start": entry_clock - timedelta(hours=1) if entry_clock else None,
            "join_end": entry_clock + timedelta(hours=1) if entry_clock else None,
            "price_start": entry_clock - timedelta(minutes=5) if entry_clock else None,
            "price_end": (min(entry_clock + timedelta(seconds=price_horizon_seconds + 300),
                              exit_clock) if entry_clock and exit_clock else None),
        }
        bucket=result[trade["trade_id"]]
        result.claim.grow(4096)
        for key,value in list(bucket.items()):
            if isinstance(value,list):bucket[key]=BoundedRows(result.claim)
    for day, records in sorted(by_date.items()):
        date_started = time.perf_counter()
        lifecycle_generation, lifecycle_receipts = _quantity_capture_lifecycle_sources(data_dir, day, decode=True)
        path = existing_or_gzip_path(data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl")
        if not path.exists():
            for group in records.values():
                for trade in group:
                    result[trade["trade_id"]]["source_gap"].append("pipeline_missing")
            continue
        stat = path.stat()
        archive_receipt_path = Path(f"{path}.archive_receipt.json")
        archive_identity_valid: bool | None = None
        if path.suffix == ".gz" and archive_receipt_path.is_file():
            try:
                archive = json.loads(archive_receipt_path.read_text(encoding="utf-8"))
                generation = archive["archive_generation"]
                archive_identity_valid = bool(
                    archive.get("schema") == "pipeline_raw_archive_identity_v1"
                    and generation.get("device") == stat.st_dev
                    and generation.get("inode") == stat.st_ino
                    and generation.get("size_bytes") == stat.st_size
                    and generation.get("mtime_ns") == stat.st_mtime_ns)
            except (OSError, ValueError, KeyError, TypeError):
                archive_identity_valid = False
        if source_receipts is not None:
            source_receipts[day] = {"path": str(path), "size_bytes": stat.st_size,
                                    "sha256": _file_sha256(path),
                                    "archive_identity_valid": archive_identity_valid,
                                    "capture_lifecycle_generation": lifecycle_generation}
        if archive_identity_valid is False:
            for group in records.values():
                for trade in group:
                    result[trade["trade_id"]]["source_gap"].append("archive_identity_invalid")
            continue
        for group in records.values():
            for trade in group:
                result[trade["trade_id"]]["source_path"] = str(path)
        with open_text_auto(path) as handle:
            for raw in iter(lambda: handle.readline(64 * 1024 + 1), ""):
                if len(raw.encode("utf-8")) > 64 * 1024:
                    raise ValueError("quantity_pipeline_record_partition_required")
                rid = _record_id(raw)
                group = records.get(rid)
                if not group:
                    continue
                try:
                    event = json.loads(raw)
                except ValueError:
                    continue
                if str(event.get("stock_code") or "") not in {x["stock_code"] for x in group}:
                    continue
                fields = event.get("fields") or {}
                if not isinstance(fields, dict):
                    continue
                stage = str(event.get("stage") or "")
                emitted = _timestamp(event.get("emitted_at"))
                if emitted is None:
                    continue
                for trade in group:
                    if trade["stock_code"] != str(event.get("stock_code") or ""):
                        continue
                    bucket = result[trade["trade_id"]]
                    within_entry_join = bool(bucket["join_start"] and bucket["join_end"]
                                             and bucket["join_start"] <= emitted <= bucket["join_end"])
                    if ((stage == "entry_execution_sizing_plan"
                         and fields.get("entry_execution_sizing_valid") in (True, "True"))
                            or (stage == "order_bundle_submitted"
                                and fields.get("actual_order_submitted") in (True, "True"))) and within_entry_join:
                        bucket["decisions"].append({"at": emitted, "stage": stage, "fields": {
                                key: fields.get(key) for key in (
                                    "effective_venue", "sizing_venue_at_allocation",
                                    "market_session_bucket", "source_signature",
                                    "reference_time", "current_price", "latest_price", "tier", "ratio",
                                    "requested_qty", "effective_qty", "pre_cap_qty", "binding_caps",
                                    "quantity_type", "quantity_type_classifier_version",
                                    "scalping_sizing_quantity_type",
                                    "scalping_sizing_quantity_type_classifier_version",
                                    "quantity_type_policy_row",
                                    "position_sizing_policy_status",
                                    "position_sizing_policy_sha256",
                                    "initial_quantity_runtime_pid",
                                    "initial_quantity_cap_research_context",
                                    "entry_submit_attempt_id",
                                    "entry_execution_sizing_plan_sha256",
                                    "scalping_sizing_quantity_type_policy_row",
                                    "scalping_sizing_position_sizing_policy_status",
                                    "scalping_sizing_position_sizing_policy_sha256",
                                    "buy_pressure_10t", "tick_aggressor_pressure_usable",
                                    "tick_context_quality", "quote_stale", "quote_consistency_state",
                                    "classifier_route_key", "classifier_transport_epoch",
                                    "ws_route", "market_data_transport_epoch",
                                    "entry_split_order_probe_first_applied",
                                    "entry_split_order_probe_qty",
                                    "entry_split_order_leg_count",
                                )}})
                    if stage == "entry_cancel_wait_submission" and within_entry_join:
                        context_raw = fields.get("entry_cancel_wait_submission_context")
                        try:
                            context = json.loads(context_raw) if isinstance(context_raw, str) else {}
                        except ValueError:
                            context = {}
                        order_start = _timestamp(context.get("frozen_at"))
                        order_no = str(fields.get("broker_order_no") or "")
                        if (fields.get("actual_order_submitted") in (True, "True")
                                and order_no and order_start and order_start <= emitted
                                and context.get("stock_code") == trade["stock_code"]):
                            bucket["order_starts"].append({
                                "at": order_start, "order_no": order_no,
                                "source": "entry_cancel_wait_submission_context_frozen_at",
                                "total_wait_sec": context.get('actual_timeout_sec'),
                                "frozen_context_valid": bool(context.get('schema')=='entry_cancel_wait_submitted_paired_v2'
                                    and context.get('sha256')==_digest({k:v for k,v in context.items() if k!='sha256'})),
                                "probe_applied": str(context.get("child_id") or "").startswith(
                                    "entry_split_probe"),
                                "emitted_at": emitted})
                    if stage in {"order_leg_request", "order_leg_sent"} and within_entry_join:
                        attempt_id = str(fields.get("entry_submit_attempt_id") or "")
                        plan_sha = str(fields.get("entry_execution_sizing_plan_sha256") or "")
                        tag = str(fields.get("tag") or "")
                        if attempt_id and plan_sha and tag:
                            event_row = {"at": emitted, "attempt_id": attempt_id,
                                         "plan_sha": plan_sha, "tag": tag,
                                         "probe_applied": tag.startswith("entry_split_probe")}
                            if stage == "order_leg_request":
                                bucket["order_requests"].append(event_row)
                            else:
                                order_no = str(fields.get("broker_order_no")
                                               or fields.get("order_no") or "")
                                if (order_no and fields.get("actual_order_submitted")
                                        in (True, "True")):
                                    bucket["order_sent"].append({**event_row,
                                                                 "order_no": order_no})
                                    initial_start = _timestamp(fields.get(
                                        "initial_quantity_order_start_at"))
                                    schedule_sha = str(fields.get(
                                        "initial_quantity_schedule_sha256") or "")
                                    policy_sha = str(fields.get(
                                        "initial_quantity_policy_file_sha256") or "")
                                    if (initial_start is not None
                                            and initial_start <= emitted
                                            and fields.get("initial_quantity_leg_index")
                                            in (0, "0")
                                            and fields.get("initial_quantity_attempt_id")
                                            == attempt_id
                                            and re.fullmatch(r"[0-9a-f]{64}", schedule_sha)
                                            and re.fullmatch(r"[0-9a-f]{64}", policy_sha)
                                            and any(
                                                decision["fields"].get(
                                                    "entry_submit_attempt_id") ==
                                                attempt_id
                                                and decision["fields"].get(
                                                    "entry_execution_sizing_plan_sha256")
                                                == plan_sha
                                                and decision["fields"].get(
                                                    "scalping_sizing_position_sizing_policy_sha256")
                                                == policy_sha
                                                for decision in bucket["decisions"])):
                                        bucket["order_starts"].append({
                                            "at": initial_start,
                                            "order_no": order_no,
                                            "source":
                                                "initial_quantity_bundle_order_start_at",
                                            "probe_applied": tag ==
                                                "initial_quantity_probe_0",
                                            "total_wait_sec": (int(_number(fields.get("initial_quantity_bundle_total_wait_sec")))
                                                if _number(fields.get("initial_quantity_bundle_total_wait_sec")) is not None else None),
                                            "emitted_at": emitted,
                                            "attempt_id": attempt_id,
                                            "plan_sha": plan_sha,
                                            "schedule_sha256": schedule_sha,
                                            "policy_sha256": policy_sha,
                                        })
                    if stage in {"initial_quantity_cap_capture_started", "initial_quantity_cap_capture_order_started",
                                 "initial_quantity_cap_capture_finished", "initial_quantity_cap_capture_interrupted"} and within_entry_join:
                        # A sampled observer never proves full market coverage.
                        # Preserve the terminal queue/clock evidence separately
                        # from the prints usable inside the trade's price window.
                        bucket["capture_receipts"].append({
                            "at": emitted, "stage": stage,
                            "fields": {key: fields.get(key) for key in (
                                "capture_id", "capture_source_date", "capture_runtime_pid", "capture_runtime_start_ticks",
                                "capture_record_id", "capture_stock_code",
                                "entry_submit_attempt_id", "entry_execution_sizing_plan_sha256",
                                "capture_clock_status", "capture_planned_epoch",
                                "capture_order_start_epoch", "capture_end_epoch",
                                "capture_queue_rejected_count", "capture_queued_count",
                                "capture_disposition", "capture_interruption_reason", "observation_coverage")}})
                    if (stage == "initial_quantity_cap_following_tick"
                            and within_entry_join and bucket["price_end"] is not None
                            and emitted <= bucket["price_end"]):
                        observed_epoch = _number(fields.get("cap_tick_observed_epoch"))
                        price = _number(fields.get("cap_tick_price_krw"))
                        quantity = _number(fields.get("cap_tick_quantity"))
                        observed_at = (datetime.fromtimestamp(observed_epoch, tz=timezone.utc)
                                       if observed_epoch is not None and
                                       0 < observed_epoch < 4_000_000_000 else None)
                        if (observed_at is not None
                                and bucket["price_start"] <= observed_at <= bucket["price_end"]
                                and price is not None
                                and quantity is not None and price > 0
                                and quantity > 0 and price.is_integer()
                                and quantity.is_integer()
                                and fields.get("decision_authority") ==
                                "source_only_cap_fill_research"
                                and fields.get("actual_order_submitted") in (False, "False")):
                            bucket["cap_ticks"].append({
                                "observed_epoch": observed_epoch,
                                "price_krw": int(price), "quantity": int(quantity),
                                "item": str(fields.get("cap_tick_item") or ""),
                                "depth_item": str(fields.get("cap_tick_depth_item") or ""),
                                "market_route": str(fields.get("cap_tick_market_route") or ""),
                                "transport_epoch": fields.get("cap_tick_transport_epoch"),
                                "attempt_id": str(fields.get("entry_submit_attempt_id") or ""),
                                "plan_sha256": str(fields.get(
                                    "entry_execution_sizing_plan_sha256") or ""),
                                **{key: fields.get(key) for key in ('capture_source_date',
                                   'capture_runtime_pid', 'capture_runtime_start_ticks',
                                   'capture_record_id', 'capture_stock_code')},
                            })
                    elif (stage == "position_rebased_after_fill" and within_entry_join
                          and str(fields.get("entry_mode") or "").lower() == "normal"):
                        price = _number(fields.get("fill_price") or fields.get("avg_buy_price"))
                        qty = _number(fields.get("fill_qty"))
                        broker_fill_raw = fields.get("broker_execution_observed_at")
                        fill_at = _timestamp(broker_fill_raw) or emitted
                        if fill_at and price and qty and qty > 0 and qty.is_integer():
                            bucket["fills"].append({"at": fill_at, "emitted_at": emitted,
                                "clock_precision_sec": (
                                    1 if broker_fill_raw and "." not in
                                    str(broker_fill_raw).split("T")[-1] else 0),
                                "price": price,
                                "qty": int(qty), "venue": str(fields.get("actual_execution_venue") or "UNKNOWN"),
                                "order_no": str(fields.get("order_no") or ""),
                                "execution_no": str(fields.get("execution_no") or ""),
                                "clock_source": ("broker_execution_observed_at"
                                                 if fields.get("broker_execution_observed_at")
                                                 else "position_rebased_emitted_at_proxy")})
                    if trade["buy_qty"] >= 2:
                        price_window = bool(bucket["price_start"] and bucket["price_end"]
                                            and bucket["price_start"] <= emitted <= bucket["price_end"])
                        if price_window:
                            price, source = _fresh_observed_price(fields)
                            if price is not None:
                                bucket["prices"].append({"at": emitted, "price": price,
                                    "source": source,
                                    "venue": str(fields.get("effective_venue") or ""),
                                    "route": str(fields.get("classifier_route_key")
                                                 or fields.get("ws_route") or ""),
                                    "epoch": str(fields.get("classifier_transport_epoch")
                                                 or fields.get("market_data_transport_epoch") or ""),
                                    "stage": stage})
        try:
            stat_after = path.stat()
            source_stable = (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns) == (
                stat_after.st_dev, stat_after.st_ino, stat_after.st_size,
                stat_after.st_mtime_ns)
        except OSError:
            source_stable = False
        if source_receipts is not None:
            source_receipts[day]["stable_during_scan"] = source_stable
        if not source_stable:
            for group in records.values():
                for trade in group:
                    bucket = result[trade["trade_id"]]
                    bucket["decisions"].clear()
                    bucket["fills"].clear()
                    bucket["prices"].clear()
                    bucket["order_starts"].clear()
                    bucket["order_requests"].clear()
                    bucket["order_sent"].clear()
                    bucket["cap_ticks"].clear()
                    bucket["capture_receipts"].clear()
                    bucket["source_gap"].append("pipeline_changed_during_scan")
        if source_stable:
            for group in records.values():
                for trade in group:
                    bucket = result[trade["trade_id"]]
                    # Late dead-PID reconciliation is a negative observation,
                    # never a substitute for the original horizon completion.
                    for receipt in lifecycle_receipts:
                        if (str(receipt.get('record_id')) != str(trade['record_id'])
                                or receipt.get('code') != trade['stock_code']
                                or receipt.get('status') != 'interrupted'):
                            continue
                        at = _number(receipt.get('observed_at_epoch'))
                        if at is None or not 0 < at < 4_000_000_000:
                            raise ValueError('quantity_capture_receipt_clock_invalid')
                        bucket['capture_receipts'].append({
                            'at': datetime.fromtimestamp(at, tz=timezone.utc),
                            'stage': receipt['raw_event_stage'], 'fields': receipt['fields'],
                            'durable_source': 'native_closed_lifecycle_receipt'})
                    requests = bucket["order_requests"]
                    sent_counts = Counter((row["attempt_id"], row["plan_sha"], row["tag"])
                                          for row in bucket["order_sent"])
                    for sent in bucket["order_sent"]:
                        identity = (sent["attempt_id"], sent["plan_sha"], sent["tag"])
                        if sent_counts[identity] != 1:
                            continue
                        matches = [request for request in requests
                                   if request["attempt_id"] == sent["attempt_id"]
                                   and request["plan_sha"] == sent["plan_sha"]
                                   and request["tag"] == sent["tag"]
                                   and 0 <= (sent["at"] - request["at"]).total_seconds() <= 120]
                        if len(matches) == 1:
                            bucket["order_starts"].append({
                                "at": matches[0]["at"], "latest_at": sent["at"],
                                "order_no": sent["order_no"],
                                "probe_applied": matches[0]["probe_applied"],
                                "source": "order_leg_request_to_sent_bracket"})
        if scan_seconds is not None:
            scan_seconds[day] = round(time.perf_counter() - date_started, 6)
    # A late contradictory broker identity invalidates this trade everywhere;
    # last-write-wins must not turn conflicting evidence into an exact fill.
    for bucket in result.values():
        seen={}
        for fill in bucket['fills']:
            key=(fill['order_no'],fill['execution_no']) if fill['order_no'] and fill['execution_no'] else (fill['at'],fill['price'],fill['qty'])
            if key in seen and any(seen[key].get(k)!=fill.get(k) for k in ('at','price','qty','venue')):
                bucket['source_gap'].append('conflicting_broker_fill_identity')
                bucket['fills'].clear()
                break
            seen[key]=fill
    return result


def _quantity_parts(qty: int, shape: str, *, probe_first: bool = False) -> list[int]:
    from src.engine.scalping.entry_split_order_plan import build_initial_quantity_type_legs
    if shape == "parent":
        return [qty]
    return [row["qty"] for row in build_initial_quantity_type_legs(
        total_qty=qty, selected_shape=shape, probe_first=probe_first, route="SOR")]


def _costed_fixed_exit_pnl(
    legs: list[tuple[int, float]], sell_price: float, cost_rate: float,
) -> float:
    """Match trade_profit's sell-notional cost contract before final rounding."""
    if not legs:
        return 0.0
    buy_amount = sum(qty * price for qty, price in legs)
    sell_amount = sell_price * sum(qty for qty, _ in legs)
    return sell_amount - buy_amount - cost_rate * sell_amount


def _cap_target_qty(context: Any, mode: str) -> int | None:
    """Replay the allocator's ratio and every captured hard quantity cap."""
    if not isinstance(context, dict) or mode not in _CAP_MODES:
        return None
    from src.engine.kiwoom_orders import describe_buy_capacity
    from src.engine.scalping.position_sizing_allocator import DEFAULT_TIER_RATIOS

    required_ints = ("budget_base_krw", "price_krw", "absolute_budget_cap_krw",
                     "current_position_qty", "actual_tier", "actual_pre_cap_qty",
                     "actual_effective_qty")
    if (context.get("schema_version") != "initial_quantity_cap_context_v1"
            or any(type(context.get(key)) is not int or context[key] < 0
                   for key in required_ints)
            or not 1 <= context["actual_tier"] <= len(DEFAULT_TIER_RATIOS)
            or context["price_krw"] <= 0
            or _number(context.get("safety_ratio")) is None
            or not 0 < context["safety_ratio"] <= 1
            or _number(context.get("actual_ratio")) is None
            or not 0 < context["actual_ratio"] <= DEFAULT_TIER_RATIOS[
                context["actual_tier"] - 1]):
        return None
    cap_names = ("max_position_qty_cap", "cash_orderable_qty_cap",
                 "remaining_position_qty_cap", "stage_qty_cap", "broker_qty_cap")
    if any(context.get(name) is not None
           and (type(context[name]) is not int or context[name] < 0)
           for name in cap_names):
        return None

    def allocate(ratio: float) -> tuple[int, int]:
        price = context["price_krw"]
        absolute = context["absolute_budget_cap_krw"]
        allow_floor = bool(context.get("min_one_share_floor_enabled")) and (
            absolute <= 0 or absolute >= price)
        _, _, pre_cap, _ = describe_buy_capacity(
            price, context["budget_base_krw"], ratio,
            safety_ratio=context["safety_ratio"], max_budget=absolute,
            allow_min_one_share_over_budget=allow_floor)
        effective = max(0, pre_cap)
        position_cap = context.get("max_position_qty_cap")
        if position_cap is not None:
            position_cap = max(0, position_cap - context["current_position_qty"])
            if (context.get("broker_confirmed_one_share_floor") is True
                    and context["current_position_qty"] == 0
                    and context.get("stage_qty_cap") == 1
                    and (context.get("broker_qty_cap") or 0) >= 1):
                position_cap = max(1, position_cap)
        for cap in (context.get("cash_orderable_qty_cap"), position_cap,
                    context.get("remaining_position_qty_cap"),
                    context.get("stage_qty_cap"), context.get("broker_qty_cap")):
            if cap is not None:
                effective = min(effective, cap)
        return max(0, pre_cap), effective

    actual = allocate(float(context["actual_ratio"]))
    if actual != (context["actual_pre_cap_qty"],
                  context["actual_effective_qty"]):
        return None
    cap_ratio = min(DEFAULT_TIER_RATIOS[context["actual_tier"] - 1],
                    _CAP_MODES[mode])
    return allocate(cap_ratio)[1]


def _capture_source_issue(source: dict[str, Any], *, horizon_seconds=1200, order_start_epoch=None) -> str | None:
    """Exclude lost/censored capture without changing the actual-fill control."""
    identity = tuple(str(source.get(key)) if source.get(key) is not None else None
                     for key in ('attempt_id', 'plan_sha256'))
    if not all(identity):
        return None
    matching = []
    for receipt in source.get("capture_receipts") or []:
        if not isinstance(receipt, dict):
            continue
        fields = receipt.get("fields")
        if not isinstance(fields, dict) or tuple(
                str(fields.get(key)) if fields.get(key) is not None else None for key in (
                'entry_submit_attempt_id', 'entry_execution_sizing_plan_sha256')) != identity:
            continue
        matching.append(receipt)
        for key in ("capture_queue_rejected_count", "capture_queued_count"):
            raw = fields.get(key)
            if raw is None:
                continue
            try:
                count = canonical_epoch(raw)
            except (ValueError, OverflowError):
                count = None
            if count is None:
                return "capture_queue_count_invalid"
            if key == "capture_queue_rejected_count" and count > 0:
                return "capture_queue_gap"
        stage = receipt.get('stage') or 'initial_quantity_cap_capture_finished'
        clock = fields.get("capture_clock_status")
        if (clock is not None and clock != "frozen_order_start"
                and not (stage == 'initial_quantity_cap_capture_started' and clock == 'no_order_start_observed')):
            return "capture_clock_gap"
    producer_identities = set()
    finished = []
    interrupted = []
    for receipt in matching:
        fields = receipt['fields']
        stage = receipt.get('stage') or 'initial_quantity_cap_capture_finished'
        native_identity = tuple(fields.get(key) for key in ('capture_source_date', 'capture_runtime_pid',
            'capture_runtime_start_ticks'))
        if any(value is not None for value in native_identity):
            day, pid, ticks = native_identity
            if (not isinstance(day, str) or source.get('capture_source_date', day) != day
                    or canonical_epoch(pid) in (None, 0) or canonical_epoch(ticks) in (None, 0)
                    or (source.get('runtime_pid') is not None
                        and canonical_epoch(source['runtime_pid']) != canonical_epoch(pid))):
                return 'capture_runtime_identity_mismatch'
            producer_identities.add((day, canonical_epoch(pid), canonical_epoch(ticks)))
        if ((fields.get('capture_record_id') is not None and source.get('record_id') is not None
                and str(fields['capture_record_id']) != str(source['record_id']))
                or (fields.get('capture_stock_code') is not None and source.get('stock_code') is not None
                    and fields['capture_stock_code'] != source['stock_code'])):
            return 'capture_runtime_identity_mismatch'
        if stage == 'initial_quantity_cap_capture_interrupted' or fields.get('capture_disposition') == 'interrupted':
            interrupted.append(receipt)
        elif stage == 'initial_quantity_cap_capture_finished':
            finished.append(receipt)
    if len(producer_identities) > 1:
        return 'capture_runtime_identity_mismatch'
    for tick in source.get('following_ticks') or []:
        if not isinstance(tick, dict) or tuple(str(tick.get(key)) if tick.get(key) is not None else None
                for key in ('attempt_id', 'plan_sha256')) != identity:
            continue
        day, pid, ticks = (tick.get(key) for key in ('capture_source_date', 'capture_runtime_pid', 'capture_runtime_start_ticks'))
        if all(value is None for value in (day, pid, ticks)):
            continue  # Original pre-lifecycle observations retain their provenance.
        native = (day, canonical_epoch(pid), canonical_epoch(ticks))
        if (not isinstance(day, str) or source.get('capture_source_date', day) != day
                or native[1] in (None, 0) or native[2] in (None, 0)
                or (source.get('runtime_pid') is not None and canonical_epoch(source['runtime_pid']) != native[1])
                or (producer_identities and native not in producer_identities)):
            return 'capture_runtime_identity_mismatch'
        producer_identities.add(native)
    if interrupted and finished:
        return 'capture_terminal_conflict'
    if source.get('capture_terminal_required') is True:
        if type(horizon_seconds) is not int or not 1 <= horizon_seconds <= 1200:
            return 'capture_horizon_unverified'
        if not finished and not interrupted:
            return 'capture_terminal_missing'
        for receipt in finished + interrupted:
            fields = receipt['fields']
            start = _number(fields.get('capture_order_start_epoch'))
            end = _number(fields.get('capture_end_epoch'))
            observed = _timestamp(receipt.get('at'))
            if (fields.get('capture_clock_status') != 'frozen_order_start'
                    or start is None or start <= 0 or end is None or end != start + 1200
                    or (order_start_epoch is not None and start != order_start_epoch)
                    or observed is None):
                return 'capture_horizon_unverified'
            if receipt in interrupted:
                # A recovery timestamp proves when the dead producer was
                # noticed, not how long its original capture stayed alive.
                required_end = start + horizon_seconds
                fixed_exit = _number(source.get('capture_exit_epoch'))
                if fixed_exit is not None and fixed_exit > start:
                    required_end = min(required_end, fixed_exit)
                if (fields.get('capture_interruption_reason') not in {
                        'position_completed_before_capture_horizon', 'attempt_replaced',
                        'process_shutdown_observation_censored'}
                        or not producer_identities
                        or observed.timestamp() < required_end):
                    return 'capture_interrupted'
            elif observed.timestamp() < end:
                return 'capture_horizon_unverified'
    elif interrupted:
        return 'capture_interrupted'
    return None


def _cap_candidate_trade(
    trade: dict[str, Any], source: dict[str, Any], mode: str,
    cost_rate: float,
) -> dict[str, Any]:
    """Use exact fills first; require bound depth and later prints for extras."""
    issue = _capture_source_issue(source)
    if issue:
        return {"status": issue}
    context = source.get("context")
    target = _cap_target_qty(context, mode)
    if target is None:
        return {"status": "allocator_context_missing_or_invalid"}
    if target == 0:
        return {"status": "zero_quantity_action_change_forbidden"}
    fills = source.get("fills")
    if not isinstance(fills, list) or not fills:
        return {"status": "broker_fill_ledger_missing"}
    ordered = sorted(fills, key=lambda item: str(item.get("at") or ""))
    if (any(type(fill.get("qty")) is not int or fill["qty"] <= 0
            or _number(fill.get("price")) is None or fill["price"] <= 0
            or _timestamp(fill.get("at")) is None for fill in ordered)
            or sum(fill["qty"] for fill in ordered) != trade["buy_qty"]
            or abs(sum(fill["qty"] * fill["price"] for fill in ordered)
                   / trade["buy_qty"] - trade["buy_price"]) > 1.0
            or context["actual_effective_qty"] < trade["buy_qty"]):
        return {"status": "broker_fill_ledger_fact_mismatch"}
    remaining = target
    candidate_legs: list[tuple[int, float]] = []
    for fill in ordered:
        taken = min(remaining, fill["qty"])
        if taken:
            candidate_legs.append((taken, fill["price"]))
            remaining -= taken
    extra_source = "not_needed"
    if remaining:
        depth = context.get("ask_depth_source")
        from src.engine.scalping.initial_quantity_cap_observation import quote_route_binding
        binding = (quote_route_binding(depth.get('item'), depth.get('market_route'), legacy=True)
                   if isinstance(depth, dict) else None)
        ticks = source.get("following_ticks")
        first_at = _timestamp(ordered[0]["at"])
        if (isinstance(depth, dict) and isinstance(ticks, list)
                and depth.get("source_type") == "ws_0D_bound_snapshot"
                and binding is not None
                and type(depth.get("transport_epoch")) is int
                and _number(depth.get("observed_epoch")) is not None
                and isinstance(depth.get("levels"), list)
                and all(fill.get("venue") in binding['fill_venues']
                        for fill in ordered)
                and first_at is not None
                and 0 <= first_at.timestamp() - float(depth["observed_epoch"]) <= 120):
            identity = (source.get("attempt_id"), source.get("plan_sha256"))
            unique_ticks = {(_number(tick.get("observed_epoch")),
                             tick.get("price_krw"), tick.get("quantity"),
                             tick.get("item")): tick for tick in ticks
                            if isinstance(tick, dict)
                            and (tick.get("attempt_id"), tick.get("plan_sha256"))
                            == identity
                            and tick.get("depth_item") == depth.get("item")
                            and tick.get("market_route") == depth.get("market_route")
                            and canonical_epoch(tick.get("transport_epoch")) ==
                            canonical_epoch(depth.get("transport_epoch"))
                            and type(tick.get("observed_epoch")) in (int, float)
                            and math.isfinite(tick["observed_epoch"])
                            and type(tick.get("price_krw")) is int
                            and type(tick.get("quantity")) is int
                            and tick["quantity"] > 0}
            previous_level_price = 0
            for level in depth["levels"][:5]:
                if (not isinstance(level, dict)
                        or type(level.get("price_krw")) is not int
                        or type(level.get("quantity")) is not int
                        or level["price_krw"] <= 0 or level["quantity"] < 0):
                    break
                price = level["price_krw"]
                if (price <= previous_level_price or price % get_tick_size(price)
                        or candidate_legs and price <
                        min(fill_price for _, fill_price in candidate_legs)):
                    break
                previous_level_price = price
                observed_buy = sum(tick["quantity"] for tick in unique_ticks.values()
                                   if tick["price_krw"] == price
                                   and first_at.timestamp() <
                                   tick["observed_epoch"] <=
                                   first_at.timestamp() + 1200)
                already_filled = sum(qty for qty, fill_price in candidate_legs
                                     if fill_price == price)
                available = max(0, min(level["quantity"], observed_buy)
                                - already_filled)
                taken = min(remaining, available)
                if taken:
                    candidate_legs.append((taken, price))
                    remaining -= taken
                if remaining == 0:
                    break
            extra_source = ("bound_depth_and_following_0b" if remaining == 0
                            else "insufficient_bound_depth_or_following_0b")
        else:
            extra_source = "bound_depth_or_following_0b_missing"
    pnl = _costed_fixed_exit_pnl(candidate_legs, trade["sell_price"], cost_rate)
    modeled_parent = _costed_fixed_exit_pnl(
        [(trade["buy_qty"], trade["buy_price"])], trade["sell_price"], cost_rate)
    denominator = trade["buy_price"] * trade["buy_qty"]
    return {"status": "paired" if remaining == 0 else "partial_unfilled",
            "target_qty": target, "modeled_filled_qty": target - remaining,
            "unfilled_qty": remaining, "extra_fill_source": extra_source,
            "candidate_net_pnl_krw": round(pnl, 3),
            "candidate_net_pct_on_parent_notional": round(pnl / denominator * 100, 6),
            "parent_net_pnl_krw": modeled_parent,
            "actual_net_pnl_krw": trade["realized_net_pnl_krw"],
            "modeled_parent_net_pnl_krw": modeled_parent,
            "cost_model": COST_MODEL}


def _paired_candidate(trade: dict[str, Any], path: dict[str, Any], shape: str) -> dict[str, Any]:
    if shape == "parent":
        entry_at = _timestamp(trade.get("entry_at_fact_buy_time"))
        decisions = [item for item in path.get("decisions") or []
                     if entry_at and abs((item["at"] - entry_at).total_seconds()) <= 3600
                     and (item["at"] <= entry_at or item["stage"] == "order_bundle_submitted"
                          and (item["at"] - entry_at).total_seconds() <= 30)]
        # The submitted bundle is often closer to the fill than the sizing
        # decision.  It is an execution event, not proof of which policy
        # calculated the quantity.  Keep that fallback for historical type
        # research, but bind a refresh trade to the actual sizing event.
        sizing_decisions = [item for item in decisions
                            if item["stage"] == "entry_execution_sizing_plan"
                            and item["at"] <= entry_at]
        decision = (max(sizing_decisions, key=lambda item: item["at"])
                    if sizing_decisions else
                    min(decisions, key=lambda item: abs((item["at"] - entry_at).total_seconds()))
                    if decisions else None)
        fields = dict(decision["fields"]) if decision else {}
        fields["effective_venue"] = fields.get("effective_venue") or fields.get("sizing_venue_at_allocation")
        if decision:
            fields["reference_time"] = fields.get("reference_time") or decision["at"].isoformat()
        quantity_type = (_type_from_decision_receipt(
            fields, decision_at=decision["at"], entry_at=entry_at)
            if decision and entry_at else "SAFE_UNKNOWN")
        first_fill = min(path.get("fills") or [], key=lambda item: item["at"],
                         default=None)
        order_no = str(first_fill.get("order_no") or "") if first_fill else ""
        sent = [item for item in path.get("order_sent") or []
                if order_no and item["order_no"] == order_no]
        sent_identity = ((sent[0]["attempt_id"], sent[0]["plan_sha"])
                         if sent and all(
                             (item["attempt_id"], item["plan_sha"]) ==
                             (sent[0]["attempt_id"], sent[0]["plan_sha"])
                             for item in sent) else None)
        bound_decisions = [item for item in sizing_decisions
                           if sent_identity and (
                               item["fields"].get("entry_submit_attempt_id"),
                               item["fields"].get("entry_execution_sizing_plan_sha256"))
                           == sent_identity]
        bound_decision = (max(bound_decisions, key=lambda item: item["at"])
                          if bound_decisions else None)
        bound_fields = bound_decision["fields"] if bound_decision else {}
        raw_cap_context = bound_fields.get("initial_quantity_cap_research_context")
        try:
            cap_context = (json.loads(raw_cap_context)
                           if isinstance(raw_cap_context, str) else raw_cap_context)
        except (ValueError, TypeError):
            cap_context = None
        if (not isinstance(cap_context, dict)
                or cap_context.get("schema_version") !=
                "initial_quantity_cap_context_v1"
                or _number(cap_context.get("actual_ratio")) is None
                or _number(bound_fields.get("ratio")) is None
                or abs(_number(cap_context["actual_ratio"])
                       - _number(bound_fields["ratio"])) > 1e-9
                or _number(cap_context.get("actual_effective_qty")) is None
                or _number(bound_fields.get("effective_qty")) is None
                or _number(cap_context["actual_effective_qty"]) !=
                _number(bound_fields["effective_qty"])
                or cap_context.get("quantity_type") != quantity_type):
            cap_context = None
        return {"status": "paired", "quantity_type": quantity_type,
                "candidate_net_pct": trade["profit_rate"], "fill_state": "actual_parent",
                "candidate_net_pnl_krw": trade["realized_net_pnl_krw"],
                "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
                "decision_snapshot_status": "joined" if decision else "missing_unknown_type",
                "policy_decision_stage": (bound_decision["stage"]
                                          if bound_decision else None),
                "policy_decision_at": (bound_decision["at"].isoformat()
                                       if bound_decision else None),
                "applied_policy_status": (bound_fields.get("position_sizing_policy_status")
                                          or bound_fields.get("scalping_sizing_position_sizing_policy_status")),
                "applied_policy_file_sha256": (bound_fields.get("position_sizing_policy_sha256")
                                                or bound_fields.get("scalping_sizing_position_sizing_policy_sha256")),
                "applied_policy_runtime_pid": bound_fields.get(
                    "initial_quantity_runtime_pid"),
                "applied_cap_attempt_id": (sent_identity[0]
                                           if bound_decision and sent_identity else None),
                "applied_cap_plan_sha256": (sent_identity[1]
                                            if bound_decision and sent_identity else None),
                **({"applied_cap_research_context": cap_context}
                   if cap_context is not None else {}),
                "fixed_exit_assumption": False}
    if path.get("source_gap"):
        return {"status": "path_source_gap",
                "source_gap": sorted(set(path["source_gap"]))}
    fills = sorted(path["fills"], key=lambda x: x["at"])
    unique = {((x["order_no"], x["execution_no"]) if x["order_no"] and x["execution_no"]
              else (x["at"].isoformat(), x["price"], x["qty"])): x for x in fills}
    fills = sorted(unique.values(), key=lambda x: x["at"])
    if not fills:
        proxy = _timestamp(trade.get("entry_at_fact_buy_time"))
        if proxy is None:
            return {"status": "fill_receipt_missing"}
        fills = [{"at": proxy, "price": trade["buy_price"], "qty": trade["buy_qty"],
                  "venue": "UNKNOWN", "order_no": "", "execution_no": "",
                  "clock_source": "trade_performance_fact_buy_time"}]
    first = fills[0]
    if first["at"].date().isoformat() != trade["entry_date"]:
        return {"status": "fill_entry_date_mismatch"}
    exit_at = _exit_at(trade)
    if exit_at is None or exit_at <= first["at"]:
        return {"status": "exit_clock_unsupported"}
    decisions = [item for item in path.get("decisions") or []
                 if (item["at"] <= first["at"]
                     or item["stage"] == "order_bundle_submitted"
                     and (item["at"] - first["at"]).total_seconds() <= 30)
                 and abs((first["at"] - item["at"]).total_seconds()) <= 3600]
    decision = min(decisions, key=lambda x: abs((first["at"] - x["at"]).total_seconds())) if decisions else None
    if not decision:
        return {"status": "decision_snapshot_missing"}
    fields = dict(decision["fields"])
    fields["effective_venue"] = fields.get("effective_venue") or fields.get("sizing_venue_at_allocation")
    fields["reference_time"] = fields.get("reference_time") or decision["at"].isoformat()
    observed_qty = sum(x["qty"] for x in fills)
    if observed_qty != trade["buy_qty"]:
        return {"status": "fill_quantity_mismatch", "observed_qty": observed_qty}
    quantity_type = _type_from_decision_receipt(fields, decision_at=decision["at"],
                                                entry_at=first["at"])
    if observed_qty < (4 if shape.startswith("three_leg_") else 2):
        return {"status": "paired", "quantity_type": quantity_type,
                "candidate_net_pct": trade["profit_rate"],
                "conservative_net_pct": trade["profit_rate"],
                "upper_net_pct": trade["profit_rate"],
                "parent_net_pct": trade["profit_rate"],
                "candidate_net_pnl_krw": trade["realized_net_pnl_krw"],
                "conservative_net_pnl_krw": trade["realized_net_pnl_krw"],
                "upper_net_pnl_krw": trade["realized_net_pnl_krw"],
                "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
                "fill_state": "quantity_too_small_parent_fallback",
                "fixed_exit_assumption": True}
    candidate_qty = observed_qty
    parts = _quantity_parts(candidate_qty, shape)
    anchor = first["price"]
    if not float(anchor).is_integer() or int(anchor) % get_tick_size(anchor):
        return {"status": "entry_anchor_not_tick_aligned", "quantity_type": quantity_type,
                "fill_clock_source": first["clock_source"]}
    prices = [float(move_price_by_ticks(int(anchor), -int(offset))
                    if shape in _TICK_SHAPES else pct_price_offset(int(anchor), offset))
              for offset in _SHAPES[shape][1]]
    if not prices or any(price <= 0 for price in prices):
        return {"status": "invalid_p1_price", "quantity_type": quantity_type}
    if any(later >= earlier for earlier, later in zip(prices, prices[1:])):
        return {"status": "price_offset_collapsed", "quantity_type": quantity_type}
    deadline = min(first["at"] + timedelta(seconds=LEG_TTL_SECONDS), exit_at)
    decision_venue = str(fields.get("effective_venue") or "")
    decision_route = str(fields.get("classifier_route_key") or fields.get("ws_route") or "")
    decision_epoch = str(fields.get("classifier_transport_epoch")
                         or fields.get("market_data_transport_epoch") or "")
    observations = sorted((x for x in path["prices"] if first["at"] < x["at"] <= deadline
                          and (x["venue"] == decision_venue or not x["venue"] and not decision_venue)),
                          key=lambda x: x["at"])
    if not observations:
        return {"status": "path_source_gap", "quantity_type": quantity_type}
    cost_rate = get_trade_cost_rate()
    first_qty = parts[0]
    conditionally_filled = [(first_qty, anchor)]
    touch_legs: list[tuple[int, float]] = []
    verified_cross_count = 0
    for qty, limit in zip(parts[1:], prices[1:]):
        if qty <= 0:
            continue
        crosses = [x for x in observations if x["price"] < limit]
        if crosses:
            conditionally_filled.append((qty, limit))
            if (first["clock_source"] == "broker_execution_observed_at"
                    and first["order_no"] and first["execution_no"]
                    and decision_venue in {"KRX", "NXT"} and first["venue"] == decision_venue
                    and decision_route and decision_epoch
                    and any(x["route"] == decision_route and x["epoch"] == decision_epoch
                            for x in crosses)):
                verified_cross_count += 1
        elif any(x["price"] == limit for x in observations):
            touch_legs.append((qty, limit))
    def net_pnl(legs: list[tuple[int, float]]) -> float:
        return _costed_fixed_exit_pnl(legs, trade["sell_price"], cost_rate)
    no_extra_pnl = net_pnl([(first_qty, anchor)])
    crossed_pnl = net_pnl(conditionally_filled)
    touched_pnl = net_pnl(conditionally_filled + touch_legs)
    conservative_pnl = min(no_extra_pnl, crossed_pnl, touched_pnl)
    optimistic_pnl = max(no_extra_pnl, crossed_pnl, touched_pnl)
    original_notional = trade["buy_price"] * candidate_qty
    def pct(net_pnl_krw: float) -> float:
        return 100.0 * net_pnl_krw / original_notional
    return {"status": "paired", "quantity_type": quantity_type,
            "candidate_net_pct": round(pct(crossed_pnl), 6),
            "conservative_net_pct": round(pct(conservative_pnl), 6),
            "upper_net_pct": round(pct(optimistic_pnl), 6),
            "parent_net_pct": trade["profit_rate"],
            "candidate_net_pnl_krw": round(crossed_pnl, 3),
            "conservative_net_pnl_krw": round(conservative_pnl, 3),
            "upper_net_pnl_krw": round(optimistic_pnl, 3),
            "parent_net_pnl_krw": trade["realized_net_pnl_krw"],
            "fill_state": "price_cross_conditional" if len(conditionally_filled) > 1 else (
                "price_touch_only" if touch_legs else "no_cross_observed"),
            "conditional_filled_qty": sum(q for q, _ in conditionally_filled),
            "conditional_crossed_leg_count": len(conditionally_filled) - 1,
            "verified_route_epoch_price_cross_count": verified_cross_count,
            "target_qty": candidate_qty, "fixed_exit_assumption": True,
            "counterfactual_anchor_price": anchor,
            "parent_avg_buy_price": trade["buy_price"],
            "candidate_notional_denominator_krw": original_notional,
            "price_source": "fresh_ws_latest_price", "exit_at": exit_at.isoformat(),
            "fill_at": first["at"].isoformat(), "fill_clock_source": first["clock_source"],
            "decision_stage": decision["stage"],
            "decision_emitted_after_fill_proxy": decision["at"] > first["at"],
            "venue_provenance": "verified" if decision_venue in {"KRX", "NXT"}
                and first["venue"] == decision_venue else "unverified_conditional"}


def build_initial_quantity_replay(as_of: str, *, data_dir: Path = DATA_DIR,
                                  fact_rows: list[dict[str, Any]] | None = None,
                                  performance: dict[str, Any] | None = None,
                                  entry_on_or_after: str | None = None,
                                  path_cache: dict[str, Any] | None = None,
                                  source_census: dict[str, Any] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    wait_start = _block_io_wait_ms()
    trades, census = completed_trade_fact_census(as_of, fact_rows=fact_rows,
                                                  data_dir=data_dir,
                                                  entry_on_or_after=entry_on_or_after,
                                                  source_census=source_census)
    eligible_trades = [trade for trade in trades if trade_source_allowed(census,trade)]
    date_scan_seconds: dict[str, float] = {}
    source_receipts: dict[str, Any] = {}
    horizon = 1200 if path_cache is not None else LEG_TTL_SECONDS
    if path_cache and path_cache.get("census") == census and path_cache.get("price_horizon_seconds", 0) >= horizon:
        paths = path_cache["paths"]
        source_receipts = path_cache["pipeline_source_receipts"]
        date_scan_seconds = path_cache.get("date_scan_seconds", {})
    else:
        paths = join_post_fill_paths(eligible_trades, data_dir=data_dir,
                                     scan_seconds=date_scan_seconds,
                                     source_receipts=source_receipts,
                                     price_horizon_seconds=horizon)
    if path_cache is not None:
        path_cache.update({"census": census, "paths": paths,
                           "pipeline_source_receipts": source_receipts,
                           "date_scan_seconds": date_scan_seconds,
                           "price_horizon_seconds": horizon})
    counts: Counter[str] = Counter()
    paired: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    rows: list[dict[str, Any]] = []
    trade_seconds: list[float] = []
    for trade in trades:
        trade_started = time.perf_counter()
        quality = trade_source_allowed(census,trade)
        shape_rows = ({shape: _paired_candidate(trade, paths[trade["trade_id"]], shape)
                       for shape in _SHAPES} if quality else
                      {shape: {"status": "source_quality_blocked"} for shape in _SHAPES})
        parent = shape_rows["parent"]
        path = paths.get(trade["trade_id"], {})
        first_fill = min(path.get("fills") or [], key=lambda item: item["at"],
                         default=None)
        matched_starts = ([item for item in path.get("order_starts") or []
                           if first_fill and item.get("order_no") == first_fill.get("order_no")]
                          if first_fill else [])
        quantity_type = parent.get("quantity_type") or next(
            (x.get("quantity_type") for x in shape_rows.values() if x.get("quantity_type")), "SAFE_UNKNOWN")
        cap_source = None
        cap_candidates = None
        if entry_on_or_after:
            bound_context = parent.get("applied_cap_research_context")
            bound_orders = {item["order_no"] for item in path.get("order_sent") or []
                            if item.get("attempt_id") ==
                            parent.get("applied_cap_attempt_id")
                            and item.get("plan_sha") ==
                            parent.get("applied_cap_plan_sha256")}
            unique_fills = {}
            for fill in path.get("fills") or []:
                if not fill.get("order_no") or fill["order_no"] not in bound_orders:
                    continue
                identity = ((fill["order_no"], fill["execution_no"])
                            if fill.get("order_no") and fill.get("execution_no")
                            else (fill["at"].isoformat(), fill["price"],
                                  fill["qty"]))
                unique_fills[identity] = fill
            cap_source = {
                "context": bound_context,
                "attempt_id": parent.get("applied_cap_attempt_id"),
                "plan_sha256": parent.get("applied_cap_plan_sha256"),
                "runtime_pid": parent.get("applied_policy_runtime_pid"),
                "record_id": trade['record_id'], "stock_code": trade['stock_code'],
                "capture_source_date": trade['entry_date'],
                "capture_terminal_required": True,
                "capture_exit_epoch": _timestamp(trade['exit_at']).timestamp(),
                "fills": [
                    {"at": fill["at"].isoformat(), "price": fill["price"],
                     "qty": fill["qty"], "venue": fill["venue"]}
                    for fill in sorted(unique_fills.values(),
                                       key=lambda item: item["at"])],
                "following_ticks": path.get("cap_ticks") or [],
                "capture_receipts": [
                    {**receipt, "at": (receipt["at"].isoformat()
                        if isinstance(receipt.get("at"), datetime)
                        else receipt.get("at"))}
                    for receipt in path.get("capture_receipts") or []],
            }
            cap_candidates = {mode: _cap_candidate_trade(
                trade, cap_source, mode, census["cost_rate"])
                for mode in _CAP_MODES}
        for shape, value in list(shape_rows.items()):
            if (shape != "parent" and value.get("status") == "paired"
                    and value.get("quantity_type") != quantity_type):
                value = {"status": "decision_type_mismatch",
                         "parent_quantity_type": quantity_type,
                         "candidate_quantity_type": value.get("quantity_type")}
                shape_rows[shape] = value
            counts[f"{shape}:{value['status']}"] += 1
            if value["status"] == "paired":
                paired[quantity_type][shape].append(value)
        rows.append({"trade_id": trade["trade_id"], "record_id": trade["record_id"],
                     "stock_code": trade["stock_code"],
                     "entry_date": trade["entry_date"], "quantity_type": quantity_type,
                     "entry_fill_at": first_fill["at"].isoformat() if first_fill else None,
                     "entry_fill_venue": first_fill.get("venue") if first_fill else None,
                     "entry_fill_clock_source": (first_fill.get("clock_source")
                                                 if first_fill else None),
                     "applied_policy_status": parent.get("applied_policy_status"),
                     "applied_policy_file_sha256": parent.get("applied_policy_file_sha256"),
                     "applied_policy_runtime_pid": parent.get("applied_policy_runtime_pid"),
                     **({"applied_cap_research_context":
                         parent["applied_cap_research_context"]}
                        if "applied_cap_research_context" in parent else {}),
                     "policy_decision_stage": parent.get("policy_decision_stage"),
                     "policy_decision_at": parent.get("policy_decision_at"),
                     "entry_order_start_at": (matched_starts[0]["at"].isoformat()
                                              if len(matched_starts) == 1 else None),
                     "modeled_parent_net_pnl_krw": trade["modeled_parent_net_pnl_krw"],
                     "actual_profit_rate": trade["profit_rate"],
                     "actual_net_pnl_krw": trade["realized_net_pnl_krw"],
                     **({"original_notional_krw": trade["buy_price"] * trade["buy_qty"],
                         "cap_source": cap_source,
                         "cap_candidates": cap_candidates}
                        if entry_on_or_after else {}),
                     "source_gap": paths.get(trade["trade_id"], {}).get("source_gap", []),
                     "shapes": shape_rows})
        trade_seconds.append(time.perf_counter() - trade_started)
    selections: dict[str, Any] = {}
    type_trade_counts = Counter(row["quantity_type"] for row in rows)
    for quantity_type in _TYPES:
        winners = [row for row in rows if row["quantity_type"] == quantity_type
                   and row["actual_net_pnl_krw"] > 0
                   and row["actual_profit_rate"] > 0]
        winner_weight = sum(row["actual_net_pnl_krw"] for row in winners)
        weighted_parent = (sum(row["actual_profit_rate"] * row["actual_net_pnl_krw"]
                               for row in winners) / winner_weight if winner_weight else None)
        incumbent = paired[quantity_type].get("parent") or []
        incumbent_ev = sum(x["candidate_net_pct"] for x in incumbent) / len(incumbent) if incumbent else None
        incumbent_net = sum(x["parent_net_pnl_krw"] for x in incumbent)
        candidates: dict[str, Any] = {}
        for shape in _SHAPES:
            values = paired[quantity_type].get(shape) or []
            winner_comparable = [row for row in winners
                                 if (row["shapes"].get(shape) or {}).get("status") == "paired"]
            winner_comparable_ids = {row["trade_id"] for row in winner_comparable}
            weighted_candidate = (sum(
                row["actual_net_pnl_krw"] * (
                    (row["shapes"].get(shape) or {}).get("conservative_net_pct",
                     row["actual_profit_rate"])
                    if row["trade_id"] in winner_comparable_ids
                    else row["actual_profit_rate"])
                for row in winners) / winner_weight if winner_weight else None)
            if not values:
                candidates[shape] = {"paired_count": 0, "state": "no_comparable_trade",
                                     "winner_comparable_count": 0,
                                     "winner_weighted_conservative_ev_pct": (
                                         round(weighted_candidate, 6)
                                         if weighted_candidate is not None else None)}
                continue
            estimate = (incumbent_ev + sum(x["candidate_net_pct"] - x.get("parent_net_pct", x["candidate_net_pct"])
                                            for x in values) / len(incumbent)) if incumbent_ev is not None else None
            lower = (incumbent_ev + sum(x.get("conservative_net_pct", x["candidate_net_pct"])
                                         - x.get("parent_net_pct", x["candidate_net_pct"])
                                         for x in values) / len(incumbent)) if incumbent_ev is not None else None
            estimated_net = incumbent_net + sum(
                x["candidate_net_pnl_krw"] - x["parent_net_pnl_krw"]
                for x in values)
            conservative_net = incumbent_net + sum(
                x.get("conservative_net_pnl_krw", x["candidate_net_pnl_krw"])
                - x["parent_net_pnl_krw"] for x in values)
            modeled = sum(x.get("fill_state") in {"price_cross_conditional", "price_touch_only", "no_cross_observed"}
                          for x in values)
            crossed = sum(x.get("fill_state") == "price_cross_conditional" for x in values)
            verified_crossed = sum(x.get("verified_route_epoch_price_cross_count", 0) > 0
                                   and x.get("verified_route_epoch_price_cross_count", 0)
                                   == x.get("conditional_crossed_leg_count", 0)
                                   for x in values)
            candidates[shape] = {"paired_count": len(values), "modeled_count": modeled,
                                 "winner_comparable_count": len(winner_comparable),
                                 "winner_weighted_conservative_ev_pct": (
                                     round(weighted_candidate, 6)
                                     if weighted_candidate is not None else None),
                                 "price_cross_count": crossed,
                                 "verified_route_epoch_price_cross_count": verified_crossed,
                                 "price_touch_only_count": sum(x.get("fill_state") == "price_touch_only" for x in values),
                                 "no_cross_observed_count": sum(x.get("fill_state") == "no_cross_observed" for x in values),
                                 "coverage_of_type": round(len(values) / type_trade_counts[quantity_type], 6)
                                     if type_trade_counts[quantity_type] else 0.0,
                                 "coverage_of_all_completed": round(len(values) / len(trades), 6)
                                     if trades else 0.0,
                                 "estimated_ev_pct": round(estimate, 6) if estimate is not None else None,
                                 "conservative_ev_pct": round(lower, 6) if lower is not None else None,
                                 "actual_parent_net_pnl_krw": round(incumbent_net, 3),
                                 "estimated_net_pnl_krw": round(estimated_net, 3),
                                 "conservative_net_pnl_krw": round(conservative_net, 3),
                                 "missing_paths_carry_parent": max(0, len(incumbent) - len(values)),
                                 "state": "paired_with_parent_fallback"}
        best = _select_initial_winner_shape(quantity_type, candidates)
        selections[quantity_type] = {"selected_shape": best, "parent_ev_pct": incumbent_ev,
                                     "winner_weight_kind": "positive_realized_net_pnl_krw",
                                     "winner_count": len(winners),
                                     "winner_weight_sum_krw": round(winner_weight, 3),
                                     "winner_weighted_parent_ev_pct": (
                                         round(weighted_parent, 6)
                                         if weighted_parent is not None else None),
                                     "candidate_metrics": candidates,
                                     "selection_reason": "initial_winner_weighted_shape" if best != "parent" else "parent_or_source_gap"}
    body = {"schema_version": REPORT_SCHEMA, "source_date": as_of,
            "classifier_version": CLASSIFIER_VERSION,
            "cost_model": COST_MODEL,
            **({"cap_fill_model": CAP_FILL_MODEL,
                 "evaluation_algorithm": REPAIR_VERSION} if entry_on_or_after else {}),
            "generation_kind": ("refresh_post_apply_replay" if entry_on_or_after
                                else "initial_completed_trade_seed"),
            "runtime_effect": False, "runtime_apply_allowed": False,
            "actual_order_submitted": False, "broker_order_forbidden": True,
            "census": census, "replay_counts": dict(sorted(counts.items())),
            "pipeline_source_receipts": source_receipts,
            "quantity_type_counts": dict(sorted(Counter(
                row["quantity_type"] for row in rows).items())),
            "selections": selections, "trades": rows,
            "model_limitations": ["fixed_actual_exit", "conditional_price_cross_is_not_broker_fill",
                                   *(["quantity_expansion_requires_bound_depth_and_following_tick",
                                      "partial_unfilled_not_promotable"]
                                     if entry_on_or_after else
                                     ["quantity_expansion_not_estimated"]),
                                   "unclocked_price_excluded",
                                   "decision_and_fill_join_within_one_hour_of_fact_buy_time"]}
    if performance is not None:
        usage_end = resource.getrusage(resource.RUSAGE_SELF)
        wait_end = _block_io_wait_ms()
        performance.update({
            "wall_seconds": round(time.perf_counter() - started, 3),
            "cpu_user_seconds": round(usage_end.ru_utime - usage_start.ru_utime, 3),
            "cpu_system_seconds": round(usage_end.ru_stime - usage_start.ru_stime, 3),
            "peak_rss_kb": usage_end.ru_maxrss,
            "swap_operations": usage_end.ru_nswap - usage_start.ru_nswap,
            "read_blocks": usage_end.ru_inblock - usage_start.ru_inblock,
            "write_blocks": usage_end.ru_oublock - usage_start.ru_oublock,
            "block_io_wait_ms": (round(wait_end - wait_start, 3)
                                 if wait_start is not None and wait_end is not None else None),
            "trade_evaluation_p95_ms": (_pctl(trade_seconds, 0.95) or 0.0) * 1000.0,
            "trade_evaluation_p99_ms": (_pctl(trade_seconds, 0.99) or 0.0) * 1000.0,
            "date_scan_seconds": date_scan_seconds,
            "census_count": census["all_completed_initial_trades"],
        })
    return {**body, "report_content_sha256": _digest(body)}


def build_initial_quantity_policy(
    report: dict[str, Any], *, following_bars: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a candidate type policy; activation remains a separate handoff."""
    source_date = str(report.get("source_date") or "")
    date.fromisoformat(source_date)
    if (report.get("schema_version") != REPORT_SCHEMA
            or report.get("generation_kind") != "initial_completed_trade_seed"
            or report.get("cost_model") != COST_MODEL
            or report.get("report_content_sha256") != _digest({
                k: v for k, v in report.items() if k != "report_content_sha256"})):
        raise ValueError("initial_replay_integrity_invalid")
    census = report.get("census") or {}
    if census.get("census_source") != "trade_performance_facts":
        raise ValueError("completed_trade_fact_source_required")
    if census.get("input_manifest_sha256") != _digest(census.get("input_fact_rows")):
        raise ValueError("trade_fact_manifest_invalid")
    if not isinstance(census.get("all_completed_initial_trades"), int) or census["all_completed_initial_trades"] <= 0:
        raise ValueError("completed_trade_census_empty")
    if (report.get("replay_counts") or {}).get("parent:paired", 0) <= 0:
        raise ValueError("completed_parent_economics_missing")
    if not initial_replay_economics_valid(report):
        raise ValueError("initial_replay_economics_invalid")
    if following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if not following_bar_source_valid(following_bars, report):
            raise ValueError("following_bar_source_invalid")
    selections = report.get("selections") or {}
    if set(selections) != set(_TYPES):
        raise ValueError("quantity_type_coverage_invalid")
    types: dict[str, Any] = {}
    for quantity_type in _TYPES:
        row = selections[quantity_type]
        shape = row.get("selected_shape")
        if shape not in _SHAPES:
            raise ValueError("selected_shape_not_allowlisted")
        metric = (row.get("candidate_metrics") or {}).get(shape) or {}
        if quantity_type == "SAFE_UNKNOWN" and shape != "parent":
            raise ValueError("unknown_type_must_keep_parent")
        if shape != "parent" and (metric.get("state") != "paired_with_parent_fallback"
                                  or not isinstance(metric.get("paired_count"), int)
                                  or metric.get("winner_comparable_count", 0) < 1):
            raise ValueError("selected_shape_pairing_missing")
        types[quantity_type] = {"ratio_mode": "parent_5stage",
                                "selected_shape": shape,
                                "selection_reason": row.get("selection_reason"),
                                "paired_count": metric.get("paired_count", 0),
                                "winner_weight_kind": "positive_realized_net_pnl_krw",
                                "winner_count": row.get("winner_count", 0),
                                "winner_weight_sum_krw": row.get("winner_weight_sum_krw", 0),
                                "winner_weighted_parent_ev_pct": row.get(
                                    "winner_weighted_parent_ev_pct"),
                                "winner_weighted_selected_ev_pct": metric.get(
                                    "winner_weighted_conservative_ev_pct"),
                                "timeout_mode": "existing_runtime_profile",
                                "selected_total_wait_sec": None,
                                **({"following_lower_observed_minute_count":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "observed_minute_lower_count", 0),
                                    "following_weighted_lower_from_fill_minute":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "weighted_lower_elapsed_from_fill_minute"),
                                    "following_order_start_linked_count":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "order_start_linked_count", 0),
                                    "following_weighted_lower_from_order_start_minute":
                                    (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                                        "weighted_lower_elapsed_from_order_start_minute")}
                                   if following_bars is not None else {})}
    core = {"schema_version": POLICY_SCHEMA, "generation_kind": "initial_completed_trade_seed",
            "classifier_version": CLASSIFIER_VERSION,
            "policy_owner": "entry_execution_sizing_owner",
            "source_date": source_date,
            "effective_from": (date.fromisoformat(source_date) + timedelta(days=1)).isoformat(),
            "report_content_sha256": report["report_content_sha256"],
            **({"following_bar_source_content_sha256":
                following_bars["report_content_sha256"]}
               if following_bars is not None else {}),
            "input_manifest_sha256": census.get("input_manifest_sha256"),
            "census_source": "trade_performance_facts",
            "all_completed_initial_trades": census["all_completed_initial_trades"],
            "type_policies": types,
            "action_authority": False, "price_authority": False,
            "scale_in_authority": False, "quantity_cap_relaxation": False,
            "runtime_effect": False, "runtime_apply_allowed": False,
            "actual_order_submitted": False, "broker_order_forbidden": True,
            "activation_state": "candidate_requires_contract_migration_and_preopen_validation"}
    body = {**core, "policy_version": f"initial-type-{source_date}-{_digest(core)[:12]}"}
    policy = {**body, "policy_content_sha256": _digest(body)}
    if not initial_quantity_policy_valid(policy, report=report,
                                         following_bars=following_bars):
        raise ValueError("initial_policy_self_validation_failed")
    return policy


def initial_replay_economics_valid(report: Any) -> bool:
    if isinstance(report, dict) and report.get("evaluation_algorithm") == REPAIR_VERSION:
        from src.engine.scalping.initial_quantity_refresh_evaluation import replay_valid
        return replay_valid(report)
    from src.engine.scalping.initial_quantity_legacy_reader import initial_replay_economics_valid as legacy
    return legacy(report)




def _eligible_refresh_total_wait(*args, **kwargs):
    from src.engine.scalping.initial_quantity_legacy_reader import _eligible_refresh_total_wait as legacy
    return legacy(*args, **kwargs)


def _refresh_cap_decision(rows, parent_mode, minimum_count):
    from src.engine.scalping.initial_quantity_refresh_evaluation import cap_selection
    return cap_selection(rows, parent_mode, minimum_count)


def evaluate_refresh_quantity_candidate(report, **kwargs):
    if not isinstance(report, dict):
        raise ValueError("refresh_parent_or_replay_contract_invalid")
    if report.get("evaluation_algorithm") == REPAIR_VERSION:
        from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate
        return evaluate(report, **kwargs)
    from src.engine.scalping.initial_quantity_legacy_reader import evaluate_refresh_quantity_candidate as legacy
    return legacy(report, **kwargs)




def _natural_refresh_pid_receipt(
    report: dict[str, Any], parent_policy: dict[str, Any],
    parent_policy_path: Path, data_dir: Path,
) -> dict[str, Any] | None:
    """Read each entry day's verified Main PID/environment handoff.

    A selected release or a PREOPEN manifest alone is insufficient. Missing
    daily PID proof leaves the refresh evaluator's existing blocker in place.
    """
    from src.engine.scalping.initial_quantity_activation import ENV_FILE, ENV_SHA

    days = sorted({row["entry_date"] for row in report.get("trades") or []})
    diagnostic_only = not days
    if not days:
        start = refresh_window(parent_policy)
        archive_base = data_dir / "runtime/policy_bootstrap/verified_initial_quantity_pid"
        days = sorted(p.name for p in archive_base.glob("????-??-??")
                      if start <= p.name <= report["source_date"])
        if not days:
            return None
    parent_file_sha = _file_sha256(parent_policy_path)
    bootstrap_dir = data_dir / "runtime" / "policy_bootstrap"
    receipts = []
    for day in days:
        archived = []
        archive_dir = bootstrap_dir / "verified_initial_quantity_pid" / day
        for archive_path in sorted(archive_dir.glob("initial_quantity_pid_*.json")):
            try:
                archive = json.loads(archive_path.read_text(encoding="utf-8"))
                archive_sha = _file_sha256(archive_path)
            except (OSError, ValueError, TypeError):
                continue
            if not isinstance(archive, dict):
                continue
            archive_body = {key: value for key, value in archive.items()
                            if key != "receipt_content_sha256"}
            verify = archive.get("verification") or {}
            verified_at = _timestamp(archive.get("verified_at"))
            if (archive.get("schema_version") !=
                    "initial_quantity_pid_verification_v1"
                    or archive.get("receipt_content_sha256") !=
                    _digest(archive_body)
                    or archive_path.name !=
                    f"initial_quantity_pid_{archive.get('pid')}_"
                    f"{archive['receipt_content_sha256'][:12]}.json"
                    or archive.get("target_date") != day
                    or type(archive.get("pid")) is not int or archive["pid"] <= 0
                    or verified_at is None or verified_at.date().isoformat() != day
                    or archive.get("policy_file_sha256") != parent_file_sha
                    or archive.get("policy_content_sha256") !=
                    parent_policy["policy_content_sha256"]
                    or Path(str(archive.get("policy_file") or "")).resolve()
                    != parent_policy_path.resolve()
                    or not isinstance(verify, dict)
                    or verify.get("pid_passed") is not True
                    or verify.get("status") != "pass"
                    or verify.get("passed") is not True
                    or verify.get("pid_env_available") is not True
                    or verify.get("pid") != archive.get("pid")
                    or verify.get("target_date") != day
                    or verify.get("verified_at") != archive.get("verified_at")
                    or verify.get("manifest_sha256") !=
                    archive.get("manifest_sha256")
                    or verify.get("findings") != []
                    or verify.get("pid_mismatches") != []):
                continue
            archived.append({"entry_date": day, "pid": archive["pid"],
                             "verified_at": archive["verified_at"],
                             "archive_path": str(archive_path.resolve()),
                             "archive_file_sha256": archive_sha})
        if archived:
            receipts.extend(archived)
            continue
        if diagnostic_only:
            continue
        manifest_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.json"
        verify_path = bootstrap_dir / f"runtime_policy_bootstrap_verify_{day}.json"
        env_path = bootstrap_dir / f"runtime_policy_bootstrap_{day}.env"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            verify = json.loads(verify_path.read_text(encoding="utf-8"))
            env_sha = _file_sha256(env_path)
            manifest_file_sha = _file_sha256(manifest_path)
            verify_file_sha = _file_sha256(verify_path)
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(manifest, dict) or not isinstance(verify, dict):
            return None
        manifest_body = {key: value for key, value in manifest.items()
                         if key != "manifest_sha256"}
        policy_receipt = manifest.get("initial_quantity_policy_receipt") or {}
        env = manifest.get("env_overrides") or {}
        if (manifest.get("target_date") != day
                or manifest.get("manifest_sha256") != _digest(manifest_body)
                or Path(str(manifest.get("env_file") or "")).resolve()
                != env_path.resolve()
                or manifest.get("env_sha256") != env_sha
                or not isinstance(policy_receipt, dict)
                or policy_receipt.get("policy_file_sha256") != parent_file_sha
                or env.get(ENV_FILE) != str(parent_policy_path.resolve())
                or env.get(ENV_SHA) != parent_file_sha
                or verify.get("target_date") != day
                or verify.get("manifest_sha256") != manifest["manifest_sha256"]
                or Path(str(verify.get("manifest_file") or "")).resolve()
                != manifest_path.resolve()
                or Path(str(verify.get("env_file") or "")).resolve()
                != env_path.resolve()
                or (_timestamp(verify.get("verified_at")) is None
                    or _timestamp(verify["verified_at"]).date().isoformat() != day)
                or verify.get("status") != "pass"
                or verify.get("passed") is not True
                or verify.get("pid_passed") is not True
                or verify.get("pid_env_available") is not True
                or type(verify.get("pid")) is not int
                or verify["pid"] <= 0
                or verify.get("findings") != []
                or verify.get("pid_mismatches") != []):
            return None
        receipts.append({"entry_date": day, "pid": verify["pid"],
                         "verified_at": verify["verified_at"],
                         "manifest_file_sha256": manifest_file_sha,
                         "verify_file_sha256": verify_file_sha,
                         "env_file_sha256": env_sha})
    if not receipts:
        return None
    return {"actual_pid_consumed": True,
            "policy_content_sha256": parent_policy["policy_content_sha256"],
            "policy_file_sha256": parent_file_sha,
            "first_consumed_date": min(row["entry_date"] for row in receipts), "daily_pid_receipts": receipts,
            "data_root": str(data_dir.resolve()),
            "source": "verified_daily_preopen_main_pid_env"}


def _natural_refresh_terminal_receipt(report: dict[str, Any]) -> dict[str, Any]:
    """Bind the already validated completed costed fact census to replay."""
    census = report["census"]
    return {"terminal": True,
            "costed_completed_trade_count": census["all_completed_initial_trades"],
            "report_content_sha256": report["report_content_sha256"],
            "input_manifest_sha256": census["input_manifest_sha256"],
            "source": "trade_performance_facts_completed_costed"}


def build_refresh_type_policy_candidate(
    report: dict[str, Any], evaluation: dict[str, Any],
    parent_policy: dict[str, Any], timeout_research: dict[str, Any],
) -> dict[str, Any]:
    """Seal eligible type choices without granting runtime or order authority."""
    if not all(isinstance(value, dict) for value in (
            report, evaluation, parent_policy, timeout_research)):
        raise ValueError("refresh_type_candidate_source_invalid")
    from src.engine.scalping.initial_quantity_activation import (
        refresh_parent_policy_valid,
    )
    from src.engine.scalping.initial_quantity_timeout_research import (
        timeout_research_valid,
    )

    decisions = evaluation.get("type_decisions") or {}
    timeout_types = timeout_research.get("selections") or {}
    if (report.get("generation_kind") != "refresh_post_apply_replay"
            or report.get("cost_model") != COST_MODEL
            or report.get("cap_fill_model") != CAP_FILL_MODEL
            or report.get("report_content_sha256") != _digest({
                key: value for key, value in report.items()
                if key != "report_content_sha256"})
            or not initial_replay_economics_valid(report)
            or not refresh_parent_policy_valid(parent_policy)
            or not timeout_research_valid(timeout_research)
            or evaluation.get("state") != "eligible_source_only"
            or evaluation.get("global_blockers")
            or evaluation.get("report_content_sha256") !=
            report["report_content_sha256"]
            or evaluation.get("parent_policy_content_sha256") !=
            parent_policy["policy_content_sha256"]
            or set(decisions) != set(_TYPES)
            or set(timeout_types) != set(_TYPES)
            or timeout_research.get("source_date") != report.get("source_date")
            or timeout_research.get("census") != report.get("census")):
        raise ValueError("refresh_type_candidate_source_invalid")
    types = {}
    for name in _TYPES:
        shape = decisions[name].get("selected_shape")
        if (shape not in _SHAPES
                or (name == "SAFE_UNKNOWN" and shape != "parent")):
            raise ValueError("refresh_type_candidate_shape_invalid")
        selected_wait = decisions[name].get("selected_total_wait_sec")
        if (report.get("evaluation_algorithm") != REPAIR_VERSION
                and selected_wait is not None and selected_wait !=
                _eligible_refresh_total_wait(
                    report, timeout_research, name, shape,
                    decisions[name]["minimum_completed_count"])):
            raise ValueError("refresh_type_candidate_timeout_unsupported")
        parent_row = parent_policy["type_policies"][name]
        if selected_wait is not None:
            timeout_mode = "selected_total_wait_sec"
        elif shape == parent_row.get("selected_shape", "parent"):
            timeout_mode = parent_row.get(
                "timeout_mode", "existing_runtime_profile")
            selected_wait = parent_row.get("selected_total_wait_sec")
        else:
            timeout_mode = "existing_runtime_profile"
        types[name] = {
            "ratio_mode": decisions[name].get(
                "selected_ratio_mode", parent_row.get("ratio_mode", "parent_5stage")),
            "selected_shape": shape,
            "timeout_mode": timeout_mode,
            "selected_total_wait_sec": selected_wait,
        }
        from src.engine.scalping.initial_quantity_legacy_reader import _refresh_cap_decision as legacy_cap
        expected_ratio, expected_metrics = legacy_cap(
            [row for row in report.get("trades") or []
             if row.get("quantity_type") == name],
            parent_row.get("ratio_mode", "parent_5stage"),
            decisions[name].get("minimum_completed_count", 30))
        if (report.get("evaluation_algorithm") != REPAIR_VERSION and (
                types[name]["ratio_mode"] != expected_ratio
                or ("cap_candidate_metrics" in decisions[name]
                    and decisions[name]["cap_candidate_metrics"] != expected_metrics)
                or ("cap_candidate_metrics" not in decisions[name]
                    and expected_ratio != parent_row.get("ratio_mode", "parent_5stage"))
                or (name == "SAFE_UNKNOWN"
                    and types[name]["ratio_mode"] != "parent_5stage"))):
            raise ValueError("refresh_type_candidate_cap_unsupported")
        if report.get("evaluation_algorithm") == REPAIR_VERSION:
            changed = (types[name]["ratio_mode"] != parent_row.get("ratio_mode", "parent_5stage")
                       or shape != parent_row.get("selected_shape", "parent")
                       or decisions[name].get("selected_total_wait_sec") is not None)
            if changed:
                chosen = (timeout_research.get("joint_grid") or {}).get(decisions[name].get("train_selected_candidate"))
                if (not chosen or _digest(chosen) != decisions[name].get("train_selected_candidate_sha256")
                        or decisions[name].get("holdout_passed") is not True
                        or chosen["mode"] != types[name]["ratio_mode"] or chosen["shape"] != shape
                        or chosen["horizon"] != types[name]["selected_total_wait_sec"]):
                    raise ValueError("refresh_joint_candidate_unsupported")
    if all(row == {
            "ratio_mode": parent_policy["type_policies"][name].get(
                "ratio_mode", "parent_5stage"),
            "selected_shape": parent_policy["type_policies"][name].get(
                "selected_shape", "parent"),
            "timeout_mode": parent_policy["type_policies"][name].get(
                "timeout_mode", "existing_runtime_profile"),
            "selected_total_wait_sec": parent_policy["type_policies"][name].get(
                "selected_total_wait_sec"),
        } for name, row in types.items()):
        raise ValueError("refresh_type_candidate_no_selected_change")
    body = {
        "schema_version": "initial_entry_quantity_refresh_candidate_v1",
        "generation_kind": "refresh_post_apply",
        "source_date": report["source_date"],
        "effective_from": (date.fromisoformat(report["source_date"])
                           + timedelta(days=1)).isoformat(),
        "cost_model": COST_MODEL,
        "cap_fill_model": CAP_FILL_MODEL,
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "report_content_sha256": report["report_content_sha256"],
        "evaluation_content_sha256": _digest(evaluation),
        "timeout_research_content_sha256": timeout_research["report_content_sha256"],
        "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
        "type_policies": types,
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "price_authority": False,
        "quantity_cap_relaxation": False,
    }
    return {**body, "policy_content_sha256": _digest(body)}


def publish_refresh_quantity_evaluation(
    report: dict[str, Any], *, parent_policy: dict[str, Any],
    parent_policy_path: Path, output_dir: Path,
    pid_receipt: dict[str, Any] | None = None,
    terminal_receipt: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
    timeout_research: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal a post-apply replay and carry/eligible research decision.

    This receipt has no current-pointer or broker authority. A later reviewed
    policy publisher must consume it before any runtime change is possible.
    """
    output_dir = _quantity_output_path(output_dir)
    from src.engine.scalping.initial_quantity_activation import (
        refresh_parent_policy_valid,
    )

    if (not parent_policy_path.is_absolute()
            or not refresh_parent_policy_valid(parent_policy)
            or json.loads(parent_policy_path.read_text(encoding="utf-8")) != parent_policy):
        raise ValueError("refresh_parent_file_invalid")
    if timeout_research is None:
        raise ValueError("refresh_timeout_research_required")
    winners = [row for row in report.get("trades") or []
               if row.get("actual_net_pnl_krw", 0) > 0
               and row.get("actual_profit_rate", 0) > 0]
    if (winners and report.get('evaluation_algorithm') != REPAIR_VERSION) or following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import (
            following_bar_source_valid,
        )
        if following_bars is None or not following_bar_source_valid(following_bars, report):
            raise ValueError("refresh_winner_following_source_required")
    if timeout_research is not None:
        from src.engine.scalping.initial_quantity_timeout_research import (
            timeout_research_valid,
        )
        if (not timeout_research_valid(timeout_research)
                or timeout_research.get("generation_kind") !=
                "refresh_post_apply_timeout_research"
                or timeout_research.get("source_date") != report.get("source_date")
                or timeout_research.get("entry_on_or_after") !=
                (report.get("census") or {}).get("entry_on_or_after")
                or timeout_research.get("census") != report.get("census")
                or timeout_research.get("quantity_type_counts") !=
                report.get("quantity_type_counts")
                or timeout_research.get("pipeline_source_receipts") !=
                report.get("pipeline_source_receipts")):
            raise ValueError("refresh_timeout_research_source_mismatch")
    evaluation = evaluate_refresh_quantity_candidate(
        report, parent_policy=parent_policy, pid_receipt=pid_receipt,
        terminal_receipt=terminal_receipt,
        following_bars=following_bars,
        timeout_research=timeout_research,
        parent_policy_file_sha256=_file_sha256(parent_policy_path))
    day = report["source_date"]
    base_output = output_dir
    committed = base_output / "committed_stage.json"
    previous_commit = committed.read_bytes() if committed.exists() else None
    if report.get("evaluation_algorithm") == REPAIR_VERSION:
        verify_refresh_source_generations(report)
        run_hash = _digest({"report": report["report_content_sha256"],
            "evaluation": evaluation, "timeout":timeout_research["report_content_sha256"],
            "following":following_bars, "pid":pid_receipt})
        output_dir = base_output / "generations" / run_hash
    report_path = output_dir / (
        f"initial_quantity_refresh_replay_{day}_{report['report_content_sha256'][:12]}.json")
    evaluation_hash = _digest(evaluation)
    evaluation_path = output_dir / (
        f"initial_quantity_refresh_evaluation_{day}_{evaluation_hash[:12]}.json")
    report_file_sha = _write_immutable_json(report_path, report)
    evaluation_file_sha = _write_immutable_json(evaluation_path, evaluation)
    candidate_receipt = {}
    if evaluation["state"] == "eligible_source_only":
        candidate = build_refresh_type_policy_candidate(
            report, evaluation, parent_policy, timeout_research)
        candidate_path = output_dir / (
            f"initial_quantity_refresh_candidate_{day}_"
            f"{candidate['policy_content_sha256'][:12]}.json")
        candidate_receipt = {
            "candidate_status": "source_only",
            "candidate_path": str(candidate_path.resolve()),
            "candidate_file_sha256": _write_immutable_json(
                candidate_path, candidate),
            "candidate_content_sha256": candidate["policy_content_sha256"],
        }
    following_receipt = {"following_bar_source_status": "cap_profile_only" if winners else "no_winners"}
    if following_bars is not None:
        following_hash = following_bars["report_content_sha256"]
        following_path = output_dir / (
            f"initial_quantity_refresh_following_bars_{day}_{following_hash[:12]}.json")
        following_receipt = {
            "following_bar_source_status": "source_bound",
            "following_bar_source_path": str(following_path.resolve()),
            "following_bar_source_file_sha256": _write_immutable_json(
                following_path, following_bars),
            "following_bar_source_content_sha256": following_hash,
        }
    timeout_receipt = {"timeout_research_status": "not_provided"}
    if timeout_research is not None:
        timeout_hash = timeout_research["report_content_sha256"]
        timeout_path = output_dir / (
            f"initial_quantity_refresh_timeout_research_{day}_{timeout_hash[:12]}.json")
        timeout_receipt = {
            "timeout_research_status": "source_bound",
            "timeout_research_path": str(timeout_path.resolve()),
            "timeout_research_file_sha256": _write_immutable_json(
                timeout_path, timeout_research),
            "timeout_research_content_sha256": timeout_hash,
        }
    body = {
        "schema_version": "initial_entry_quantity_refresh_stage_v1",
        "stage": "initial_entry_quantity_refresh",
        "source_date": day,
        "generation_kind": "refresh",
        "stage_status": "complete_source_only",
        "applied_policy_lineage_schema": "initial_quantity_trade_policy_binding_v1",
        "terminal": True,
        "parent_policy_path": str(parent_policy_path),
        "parent_policy_file_sha256": _file_sha256(parent_policy_path),
        "parent_policy_content_sha256": parent_policy["policy_content_sha256"],
        "report_path": str(report_path.resolve()),
        "report_file_sha256": report_file_sha,
        "report_content_sha256": report["report_content_sha256"],
        "evaluation_path": str(evaluation_path.resolve()),
        "evaluation_file_sha256": evaluation_file_sha,
        "evaluation_content_sha256": evaluation_hash,
        **candidate_receipt,
        **following_receipt,
        **timeout_receipt,
        "pid_receipt": pid_receipt,
        "terminal_receipt": terminal_receipt,
        "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
        "decision": evaluation["state"],
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    stage = {**body, "receipt_content_sha256": _digest(body)}
    stage_path = output_dir / f"initial_quantity_refresh_stage_{day}.json"
    stage_sha = _write_immutable_json(stage_path, stage)
    if report.get("evaluation_algorithm") == REPAIR_VERSION:
        from src.engine.scalping.pre_submit_delay_initial_policy import _atomic
        import fcntl
        if not refresh_quantity_stage_terminal_valid(stage):
            raise ValueError("quantity_generation_validation_failed")
        with (base_output / ".commit.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            latest = committed.read_bytes() if committed.exists() else None
            if latest != previous_commit:
                if latest and json.loads(latest).get("stage_sha256") == stage_sha:
                    return stage
                raise ValueError("quantity_stage_cas_conflict")
            _atomic(committed, {"schema":"initial_quantity_stage_reference_v2",
                "source_date":day, "stage_path":str(stage_path.resolve()),
                "stage_sha256":stage_sha})
    return stage


def verify_refresh_source_generations(report, *, pipeline_reference_only=False):
    census = report["census"]
    from src.engine.strategy_position_performance_report import _saved_fact_generation_issue
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    for day, gen in census.get("persisted_fact_generations", {}).items():
        if gen.get("sha256") and _file_sha256(Path(gen["path"])) != gen["sha256"]:
            raise ValueError("quantity_fact_source_generation_changed")
        current_issue=_quantity_fact_generation_issue(day)
        if current_issue is None and json.loads(Path(gen['path']).read_bytes()).get('actual_cost_source_generation')!=gen.get('cost_generation'):
            current_issue='persisted_fact_cost_generation_stale'
        if current_issue != gen.get("issue") or gen.get('cost_generation')!=source_generation(DATA_DIR,day):
            raise ValueError("quantity_fact_cost_generation_changed")
    from src.engine.scalping.initial_quantity_source_cache import verify_completion_overlay_generations
    verify_completion_overlay_generations(census.get('completion_overlay_generations', {}), data_dir=DATA_DIR)
    for gen in (report.get("pipeline_source_receipts") or {}).values():
        lifecycle = gen.get('capture_lifecycle_generation')
        if lifecycle is not None:
            current, _ = _quantity_capture_lifecycle_sources(DATA_DIR, lifecycle['source_date'])
            if current != lifecycle:
                raise ValueError('quantity_capture_lifecycle_generation_changed')
        if pipeline_reference_only:
            from . import mechanistic_entry_runtime_policy as native
            if native.is_pipeline_source_reference(gen['path'], data_root=DATA_DIR):
                if not native.source_receipt_matches(gen, data_root=DATA_DIR):
                    raise ValueError("quantity_pipeline_source_generation_changed")
                continue
        if _file_sha256(Path(gen["path"])) != gen.get("sha256"):
            raise ValueError("quantity_pipeline_source_generation_changed")
    for key in ("source_quality_by_entry_date", "source_quality_by_exit_date"):
        for gen in census.get(key, {}).values():
            if gen.get("sha256") and _file_sha256(Path(gen["artifact"])) != gen["sha256"]:
                raise ValueError("quantity_source_quality_generation_changed")


def committed_refresh_stage_path(output_dir: Path, day: str) -> Path:
    legacy = output_dir / f"initial_quantity_refresh_stage_{day}.json"
    pointer = output_dir / "committed_stage.json"
    if not pointer.exists():
        return legacy
    if pointer.is_symlink() or pointer.stat().st_size > 65536:
        raise ValueError("quantity_stage_reference_invalid")
    ref = json.loads(pointer.read_bytes())
    path = Path(ref["stage_path"])
    if (ref.get("schema") != "initial_quantity_stage_reference_v2"
            or ref.get("source_date") != day
            or not path.is_absolute() or path.is_symlink()
            or not path.resolve().is_relative_to(output_dir.resolve() / "generations")
            or _file_sha256(path) != ref.get("stage_sha256")):
        raise ValueError("quantity_stage_reference_invalid")
    return path


def refresh_quantity_stage_terminal_valid(receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    try:
        body = {key: value for key, value in receipt.items()
                if key != "receipt_content_sha256"}
        if (receipt.get("schema_version") != "initial_entry_quantity_refresh_stage_v1"
                or receipt.get("stage") != "initial_entry_quantity_refresh"
                or receipt.get("generation_kind") != "refresh"
                or receipt.get("stage_status") != "complete_source_only"
                or receipt.get("terminal") is not True
                or receipt.get("runtime_apply_allowed") is not False
                or receipt.get("runtime_effect") is not False
                or receipt.get("actual_order_submitted") is not False
                or receipt.get("receipt_content_sha256") != _digest(body)):
            return False
        if receipt.get("applied_policy_lineage_schema") not in (
                None, "initial_quantity_trade_policy_binding_v1"):
            return False
        if (receipt.get("applied_policy_lineage_schema") !=
                "initial_quantity_trade_policy_binding_v1"
                or receipt.get("timeout_research_status") != "source_bound"):
            return False
        paths = {name: Path(receipt[f"{name}_path"])
                 for name in ("parent_policy", "report", "evaluation")}
        if (any(not path.is_absolute() or not path.is_file()
                or _file_sha256(path) != receipt[f"{name}_file_sha256"]
                for name, path in paths.items())
                or paths["report"].parent != paths["evaluation"].parent):
            return False
        parent = json.loads(paths["parent_policy"].read_text(encoding="utf-8"))
        report = json.loads(paths["report"].read_text(encoding="utf-8"))
        evaluation = json.loads(paths["evaluation"].read_text(encoding="utf-8"))
        if report.get("evaluation_algorithm") == REPAIR_VERSION:
            verify_refresh_source_generations(report, pipeline_reference_only=True)
        if (receipt.get("terminal_receipt") is None
                and receipt.get("decision") == "carry_parent"
                and not any(key.startswith("candidate_") for key in receipt)):
            pass  # Historical source-only stages had no derived cost receipt.
        elif receipt.get("terminal_receipt") != _natural_refresh_terminal_receipt(report):
            return False
        pid_receipt = receipt.get("pid_receipt")
        if pid_receipt is not None:
            if (not isinstance(pid_receipt, dict)
                    or pid_receipt.get("source") !=
                    "verified_daily_preopen_main_pid_env"
                    or not Path(str(pid_receipt.get("data_root") or "")).is_absolute()):
                return False
            from src.engine.scalping.initial_quantity_legacy_reader import _natural_refresh_pid_receipt as old_pid_reader
            pid_reader = (_natural_refresh_pid_receipt if report.get("evaluation_algorithm") == REPAIR_VERSION else old_pid_reader)
            current_pid_source = pid_reader(
                report, parent, paths["parent_policy"],
                Path(pid_receipt["data_root"]))
            if (current_pid_source is None
                    or any(pid_receipt.get(key) != current_pid_source.get(key)
                           for key in ("actual_pid_consumed",
                                       "policy_content_sha256",
                                       "policy_file_sha256",
                                       "first_consumed_date", "data_root", "source"))
                    or not isinstance(pid_receipt.get("daily_pid_receipts"), list)
                    or not pid_receipt["daily_pid_receipts"]
                    or any(row not in current_pid_source["daily_pid_receipts"]
                           for row in pid_receipt["daily_pid_receipts"])):
                return False
        winners = [row for row in report.get("trades") or []
                   if row.get("actual_net_pnl_krw", 0) > 0
                   and row.get("actual_profit_rate", 0) > 0]
        if receipt.get("following_bar_source_status") == "source_bound":
            from src.engine.scalping.initial_quantity_following_bars import (
                following_bar_source_valid,
            )
            following_path = Path(receipt["following_bar_source_path"])
            if (not following_path.is_absolute()
                    or following_path.parent != paths["report"].parent
                    or _file_sha256(following_path) !=
                    receipt["following_bar_source_file_sha256"]):
                return False
            following = json.loads(following_path.read_text(encoding="utf-8"))
            if (not following_bar_source_valid(following, report)
                    or following["report_content_sha256"] !=
                    receipt["following_bar_source_content_sha256"]):
                return False
        elif (not ((receipt.get("following_bar_source_status") == "no_winners" and not winners)
                   or (report.get('evaluation_algorithm') == REPAIR_VERSION
                       and receipt.get('following_bar_source_status') == 'cap_profile_only' and winners))
              or any(key.startswith("following_bar_source_") and key !=
                     "following_bar_source_status" for key in receipt)):
            return False
        timeout_research = None
        if receipt.get("timeout_research_status") == "source_bound":
            from src.engine.scalping.initial_quantity_timeout_research import (
                timeout_research_valid,
            )
            timeout_path = Path(receipt["timeout_research_path"])
            if (not timeout_path.is_absolute()
                    or timeout_path.parent != paths["report"].parent
                    or _file_sha256(timeout_path) !=
                    receipt["timeout_research_file_sha256"]):
                return False
            timeout_research = json.loads(timeout_path.read_text(encoding="utf-8"))
            if (not timeout_research_valid(timeout_research)
                    or timeout_research.get("generation_kind") !=
                    "refresh_post_apply_timeout_research"
                    or timeout_research.get("source_date") != report.get("source_date")
                    or timeout_research.get("entry_on_or_after") !=
                    (report.get("census") or {}).get("entry_on_or_after")
                    or timeout_research.get("census") != report.get("census")
                    or timeout_research.get("quantity_type_counts") !=
                    report.get("quantity_type_counts")
                    or timeout_research.get("pipeline_source_receipts") !=
                    report.get("pipeline_source_receipts")
                    or timeout_research.get("report_content_sha256") !=
                    receipt["timeout_research_content_sha256"]):
                return False
        elif (receipt.get("timeout_research_status") not in (None, "not_provided")
              or any(key.startswith("timeout_research_") and key !=
                     "timeout_research_status" for key in receipt)):
            return False
        selection_version = ({"evaluation_algorithm": evaluation.get("evaluation_algorithm")}
                             if report.get("evaluation_algorithm") == REPAIR_VERSION else {})
        expected = evaluate_refresh_quantity_candidate(
            report, parent_policy=parent,
            pid_receipt=receipt["pid_receipt"],
            terminal_receipt=receipt["terminal_receipt"],
            following_bars=(following if receipt["following_bar_source_status"]
                            == "source_bound" else None),
            timeout_research=timeout_research,
            parent_policy_file_sha256=receipt["parent_policy_file_sha256"],
            enforce_trade_lineage=bool(receipt.get("applied_policy_lineage_schema")),
            **selection_version)
        if receipt.get("decision") == "eligible_source_only":
            if (receipt.get("candidate_status") != "source_only"
                    or not isinstance(timeout_research, dict)):
                return False
            candidate_path = Path(receipt["candidate_path"])
            if (not candidate_path.is_absolute()
                    or candidate_path.parent != paths["report"].parent
                    or _file_sha256(candidate_path) !=
                    receipt["candidate_file_sha256"]):
                return False
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            if (candidate != build_refresh_type_policy_candidate(
                    report, evaluation, parent, timeout_research)
                    or candidate["policy_content_sha256"] !=
                    receipt["candidate_content_sha256"]):
                return False
        elif any(key.startswith("candidate_") for key in receipt):
            return False
        return bool(
            evaluation == expected
            and receipt["parent_policy_content_sha256"] == parent["policy_content_sha256"]
            and receipt["report_content_sha256"] == report["report_content_sha256"]
            and receipt["evaluation_content_sha256"] == _digest(evaluation)
            and receipt["source_date"] == report["source_date"]
            and receipt["all_completed_initial_trades"] == report["census"]["all_completed_initial_trades"]
            and receipt["decision"] == evaluation["state"]
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def initial_quantity_policy_valid(
    policy: Any, *, report: dict[str, Any] | None = None,
    following_bars: dict[str, Any] | None = None,
) -> bool:
    """Reject a tampered or broadened seed even while it is report-only."""
    if not isinstance(policy, dict) or not isinstance(report, dict):
        return False
    try:
        body = {key: value for key, value in policy.items() if key != "policy_content_sha256"}
        source_date = date.fromisoformat(policy["source_date"])
        effective_from = date.fromisoformat(policy["effective_from"])
        types = policy["type_policies"]
        if not (
            policy.get("schema_version") == POLICY_SCHEMA
            and policy.get("generation_kind") == "initial_completed_trade_seed"
            and policy.get("classifier_version") == CLASSIFIER_VERSION
            and policy.get("policy_owner") == "entry_execution_sizing_owner"
            and policy.get("census_source") == "trade_performance_facts"
            and policy.get("policy_content_sha256") == _digest(body)
            and policy.get("policy_version", "").startswith(f"initial-type-{source_date.isoformat()}-")
            and effective_from > source_date
            and type(policy.get("all_completed_initial_trades")) is int
            and policy["all_completed_initial_trades"] > 0
            and isinstance(types, dict) and set(types) == set(_TYPES)
            and all(isinstance(item, dict)
                    and item.get("ratio_mode") == "parent_5stage"
                    and item.get("selected_shape") in _SHAPES
                    and type(item.get("paired_count")) is int
                    and item["paired_count"] >= 0
                    and item.get("timeout_mode") == "existing_runtime_profile"
                    and item.get("selected_total_wait_sec") is None
                    and item.get("winner_weight_kind") == "positive_realized_net_pnl_krw"
                    and type(item.get("winner_count")) is int
                    and item["winner_count"] >= 0
                    and type(item.get("winner_weight_sum_krw")) in (int, float)
                    and math.isfinite(item["winner_weight_sum_krw"])
                    and item["winner_weight_sum_krw"] >= 0 for item in types.values())
            and types["SAFE_UNKNOWN"]["selected_shape"] == "parent"
            and all(policy.get(key) is False for key in (
                "action_authority", "price_authority", "scale_in_authority",
                "quantity_cap_relaxation", "runtime_effect", "runtime_apply_allowed",
                "actual_order_submitted"))
            and policy.get("broker_order_forbidden") is True
            and policy.get("activation_state")
            == "candidate_requires_contract_migration_and_preopen_validation"
        ):
            return False
        if (
            not initial_replay_economics_valid(report)
            or report.get("report_content_sha256") != _digest({
                key: value for key, value in report.items()
                if key != "report_content_sha256"})
            or report.get("schema_version") != REPORT_SCHEMA
            or report.get("report_content_sha256") != policy.get("report_content_sha256")
            or (report.get("census") or {}).get("input_manifest_sha256")
            != policy.get("input_manifest_sha256")
            or (report.get("census") or {}).get("input_manifest_sha256")
            != _digest((report.get("census") or {}).get("input_fact_rows"))
            or (report.get("census") or {}).get("all_completed_initial_trades")
            != policy.get("all_completed_initial_trades")
            or any(types[quantity_type]["selected_shape"] !=
                   (report.get("selections") or {}).get(quantity_type, {}).get("selected_shape")
                   for quantity_type in _TYPES)
            or any(types[quantity_type]["winner_count"] !=
                   report["selections"][quantity_type].get("winner_count", 0)
                   or types[quantity_type]["winner_weight_sum_krw"] !=
                   report["selections"][quantity_type].get("winner_weight_sum_krw", 0)
                   or types[quantity_type]["winner_weighted_parent_ev_pct"] !=
                   report["selections"][quantity_type].get("winner_weighted_parent_ev_pct")
                   or types[quantity_type]["winner_weighted_selected_ev_pct"] !=
                   report["selections"][quantity_type]["candidate_metrics"][
                       types[quantity_type]["selected_shape"]].get(
                           "winner_weighted_conservative_ev_pct")
                   for quantity_type in _TYPES)
        ):
            return False
        if "following_bar_source_content_sha256" in policy:
            from src.engine.scalping.initial_quantity_following_bars import (
                following_bar_source_valid,
            )
            if (not isinstance(following_bars, dict)
                    or not following_bar_source_valid(following_bars, report)
                    or policy["following_bar_source_content_sha256"] !=
                    following_bars["report_content_sha256"]
                    or any(
                        types[quantity_type].get("following_lower_observed_minute_count") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "observed_minute_lower_count", 0)
                        or types[quantity_type].get("following_weighted_lower_from_fill_minute") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "weighted_lower_elapsed_from_fill_minute")
                        or types[quantity_type].get("following_order_start_linked_count") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "order_start_linked_count", 0)
                        or types[quantity_type].get(
                            "following_weighted_lower_from_order_start_minute") !=
                        (following_bars["weighted_by_type"].get(quantity_type) or {}).get(
                            "weighted_lower_elapsed_from_order_start_minute")
                        for quantity_type in _TYPES)):
                return False
        elif following_bars is not None:
            return False
    except (KeyError, TypeError, ValueError):
        return False
    return True


def _quantity_output_path(path: Path) -> Path:
    # Immutable releases share only the repository's top-level data directory.
    # Canonicalize that known mount, without following any output subtree links.
    path = path.absolute()
    if ".." in path.parts:
        raise ValueError("quantity_output_path_invalid")
    release_data = PROJECT_ROOT / "data"
    if (release_data.is_symlink() and path.is_relative_to(release_data)
            and release_data.resolve() == DATA_DIR):
        path = DATA_DIR / path.relative_to(release_data)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("quantity_output_path_invalid")
    return path


def _write_immutable_json(path: Path, payload: dict[str, Any]) -> str:
    """Bounded streaming write; shared disk accounts for old/new coexistence."""
    from src.engine.lifecycle.research_disk_budget import atomic
    path = _quantity_output_path(path)
    encoder = json.JSONEncoder(ensure_ascii=False, indent=2, allow_nan=False)
    def pieces():
        for piece in encoder.iterencode(payload):
            raw = piece.encode("utf-8")
            if len(raw) > 65536:
                raise ValueError("quantity_output_record_partition_required")
            yield raw
        yield b"\n"
    size = sum(map(len, pieces()))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError("quantity_output_path_invalid")
    temporary = None
    digest = hashlib.sha256()
    try:
        with atomic(path,size):
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
                temporary=Path(handle.name)
                for raw in pieces():
                    handle.write(raw); digest.update(raw)
                handle.flush(); os.fsync(handle.fileno())
            try:
                os.link(temporary,path)
            except FileExistsError:
                if _file_sha256(path)!=digest.hexdigest():
                    raise ValueError(f"immutable_artifact_conflict:{path}")
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return digest.hexdigest()


def publish_initial_quantity_candidate(
    report: dict[str, Any], *, output_dir: Path,
    following_bars: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind the full replay and source-only seed to one immutable stage receipt."""
    output_dir = _quantity_output_path(output_dir)
    policy = build_initial_quantity_policy(report, following_bars=following_bars)
    source_date = policy["source_date"]
    report_hash = report["report_content_sha256"]
    policy_hash = policy["policy_content_sha256"]
    report_path = output_dir / f"initial_quantity_replay_{source_date}_{report_hash[:12]}.json"
    policy_path = output_dir / f"initial_quantity_candidate_{source_date}_{policy_hash[:12]}.json"
    report_file_sha = _write_immutable_json(report_path, report)
    policy_file_sha = _write_immutable_json(policy_path, policy)
    following_receipt = {}
    if following_bars is not None:
        following_hash = following_bars["report_content_sha256"]
        following_path = output_dir / (f"initial_quantity_following_bars_{source_date}_"
                                       f"{following_hash[:12]}.json")
        following_receipt = {
            "following_bar_source_path": str(following_path.resolve()),
            "following_bar_source_file_sha256": _write_immutable_json(
                following_path, following_bars),
            "following_bar_source_content_sha256": following_hash,
        }
    body = {
        "schema_version": "initial_entry_quantity_stage_terminal_v1",
        "stage": "initial_entry_quantity_type_policy",
        "source_date": source_date,
        "generation_kind": "initial_completed_trade_seed",
        "stage_status": "complete_source_only",
        "terminal": True,
        "report_path": str(report_path.resolve()),
        "report_file_sha256": report_file_sha,
        "report_content_sha256": report_hash,
        "candidate_policy_path": str(policy_path.resolve()),
        "candidate_policy_file_sha256": policy_file_sha,
        "candidate_policy_content_sha256": policy_hash,
        **following_receipt,
        "input_manifest_sha256": policy["input_manifest_sha256"],
        "all_completed_initial_trades": policy["all_completed_initial_trades"],
        "runtime_apply_allowed": False,
        "runtime_effect": False,
        "actual_order_submitted": False,
    }
    receipt = {**body, "receipt_content_sha256": _digest(body)}
    receipt_path = output_dir / f"initial_quantity_stage_{source_date}.json"
    _write_immutable_json(receipt_path, receipt)
    return receipt


def initial_quantity_stage_terminal_valid(receipt: Any) -> bool:
    """Validate stage bytes and both linked inputs before a handoff reads them."""
    if not isinstance(receipt, dict):
        return False
    try:
        body = {key: value for key, value in receipt.items()
                if key != "receipt_content_sha256"}
        if not (
            receipt.get("schema_version") == "initial_entry_quantity_stage_terminal_v1"
            and receipt.get("stage") == "initial_entry_quantity_type_policy"
            and receipt.get("generation_kind") == "initial_completed_trade_seed"
            and receipt.get("stage_status") == "complete_source_only"
            and receipt.get("terminal") is True
            and receipt.get("runtime_apply_allowed") is False
            and receipt.get("runtime_effect") is False
            and receipt.get("actual_order_submitted") is False
            and receipt.get("receipt_content_sha256") == _digest(body)
        ):
            return False
        report_path = Path(receipt["report_path"])
        policy_path = Path(receipt["candidate_policy_path"])
        if (not report_path.is_absolute() or not policy_path.is_absolute()
                or report_path.parent != policy_path.parent
                or not report_path.is_file() or not policy_path.is_file()
                or _file_sha256(report_path) != receipt["report_file_sha256"]
                or _file_sha256(policy_path) != receipt["candidate_policy_file_sha256"]):
            return False
        report = json.loads(report_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        following_bars = None
        if "following_bar_source_path" in receipt:
            following_path = Path(receipt["following_bar_source_path"])
            if (not following_path.is_absolute()
                    or following_path.parent != report_path.parent
                    or _file_sha256(following_path) !=
                    receipt["following_bar_source_file_sha256"]):
                return False
            following_bars = json.loads(following_path.read_text(encoding="utf-8"))
            if (following_bars.get("report_content_sha256") !=
                    receipt["following_bar_source_content_sha256"]):
                return False
        elif any(key.startswith("following_bar_source_") for key in receipt):
            return False
        return bool(
            initial_quantity_policy_valid(policy, report=report,
                                          following_bars=following_bars)
            and report["source_date"] == policy["source_date"] == receipt["source_date"]
            and report["report_content_sha256"] == receipt["report_content_sha256"]
            and policy["policy_content_sha256"] == receipt["candidate_policy_content_sha256"]
            and policy["input_manifest_sha256"] == receipt["input_manifest_sha256"]
            and policy["all_completed_initial_trades"] == receipt["all_completed_initial_trades"]
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _main_impl(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of")
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--policy-output", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--following-bars", type=Path)
    parser.add_argument("--parent-current", type=Path)
    parser.add_argument("--pid-receipt", type=Path)
    parser.add_argument("--terminal-receipt", type=Path)
    args = parser.parse_args(argv)
    if bool(args.as_of) == bool(args.replay):
        parser.error("exactly one of --as-of or --replay is required")
    if args.output_dir and (args.output or args.policy_output):
        parser.error("--output-dir cannot be combined with explicit output paths")
    if args.parent_current and (not args.output_dir or args.policy_output
                                or args.output):
        parser.error("refresh requires --output-dir and no seed output paths")
    if (args.pid_receipt or args.terminal_receipt) and not args.parent_current:
        parser.error("post-apply receipts require --parent-current")
    parent = None
    parent_path = None
    if args.parent_current:
        from src.engine.scalping.initial_quantity_activation import (
            ENV_FILE, selected_initial_quantity_env,
        )
        target_date = args.as_of
        if args.replay:
            target_date = json.loads(args.replay.read_text(encoding="utf-8"))["source_date"]
        env = selected_initial_quantity_env(args.parent_current, target_date)
        parent_path = Path(env[ENV_FILE])
        parent = json.loads(parent_path.read_text(encoding="utf-8"))
    performance: dict[str, Any] = {}
    path_cache: dict[str, Any] | None = {} if parent is not None and not args.replay else None
    if args.replay:
        report = json.loads(args.replay.read_text(encoding="utf-8"))
        if (not isinstance(report, dict)
                or report.get("report_content_sha256") != _digest({
                    key: value for key, value in report.items()
                    if key != "report_content_sha256"})
                or not initial_replay_economics_valid(report)):
            raise ValueError("existing_replay_invalid")
        if parent is not None and (report.get("evaluation_algorithm") != REPAIR_VERSION
                or report.get("generation_kind") != "refresh_post_apply_replay"
                or report["census"].get("entry_on_or_after") != refresh_window(parent)):
            raise ValueError("existing_replay_refresh_window_invalid")
    else:
        report = build_initial_quantity_replay(
            args.as_of, data_dir=args.data_dir, performance=performance,
            entry_on_or_after=refresh_window(parent) if parent else None,
            path_cache=path_cache)
    following_bars = (json.loads(args.following_bars.read_text(encoding="utf-8"))
                      if args.following_bars else None)
    if parent is not None:
        following_performance: dict[str, Any] = {}
        if following_bars is None and any(
                row["actual_net_pnl_krw"] > 0 and row["actual_profit_rate"] > 0
                for row in report["trades"]):
            from src.engine.scalping.initial_quantity_following_bars import (
                build_following_bar_source,
            )
            from src.utils import kiwoom_utils

            token_state: dict[str, Any] = {"attempted": False, "token": None,
                                           "error": None}

            def fetch(code: str, base_dt: str, limit: int):
                if not token_state["attempted"]:
                    token_state["attempted"] = True
                    try:
                        token_state["token"] = kiwoom_utils.get_kiwoom_token()
                    except Exception as exc:
                        token_state["error"] = exc
                if token_state["error"] is not None:
                    raise token_state["error"]
                return kiwoom_utils.get_minute_candles_ka10080_with_meta(
                    token_state["token"], code, limit=limit, explicit_request_code=True,
                    base_dt=base_dt)

            following_bars = build_following_bar_source(
                report, fetch=fetch, performance=following_performance)
        from src.engine.scalping.initial_quantity_timeout_research import (
            build_timeout_research,
        )
        timeout_performance: dict[str, Any] = {}
        timeout_research = build_timeout_research(
            report["source_date"],
            data_dir=args.data_dir,
            fact_rows=report["census"]["input_fact_rows"],
            entry_on_or_after=refresh_window(parent),
            path_cache=path_cache,
            performance=timeout_performance, replay=report)
        pid_receipt = _natural_refresh_pid_receipt(
            report, parent, parent_path, args.data_dir)
        terminal_receipt = _natural_refresh_terminal_receipt(report)
        if (args.pid_receipt
                and json.loads(args.pid_receipt.read_text(encoding="utf-8"))
                != pid_receipt):
            raise ValueError("refresh_pid_receipt_source_mismatch")
        if (args.terminal_receipt
                and json.loads(args.terminal_receipt.read_text(encoding="utf-8"))
                != terminal_receipt):
            raise ValueError("refresh_terminal_receipt_source_mismatch")
        stage = publish_refresh_quantity_evaluation(
            report, parent_policy=parent, parent_policy_path=parent_path,
            output_dir=args.output_dir,
            pid_receipt=pid_receipt,
            terminal_receipt=terminal_receipt,
            following_bars=following_bars,
            timeout_research=timeout_research)
        if not refresh_quantity_stage_terminal_valid(stage):
            raise ValueError("refresh_stage_self_validation_failed")
        print(json.dumps({"source_date": report["source_date"],
                          "all_completed_initial_trades": stage["all_completed_initial_trades"],
                          "decision": stage["decision"],
                          "receipt_content_sha256": stage["receipt_content_sha256"],
                          "performance": performance,
                          "following_performance": following_performance,
                          "timeout_performance": timeout_performance}))
        return 0
    if args.output_dir:
        publish_initial_quantity_candidate(
            report, output_dir=args.output_dir, following_bars=following_bars)
    elif args.output:
        _write_immutable_json(args.output, report)
    if args.policy_output:
        policy = build_initial_quantity_policy(report, following_bars=following_bars)
        _write_immutable_json(args.policy_output, policy)
    print(json.dumps({"source_date": report["source_date"],
                      "all_completed_initial_trades": report["census"]["all_completed_initial_trades"],
                      "replay_counts": report["replay_counts"],
                      "performance": performance,
                      "report_content_sha256": report["report_content_sha256"]}))
    return 0


def main(argv: list[str] | None = None) -> int:
    import sys
    from src.engine.lifecycle.research_admission import direct_job
    from src.engine.lifecycle.research_disk_budget import use
    probe = argparse.ArgumentParser(add_help=False)
    probe.add_argument("--as-of")
    probe.add_argument("--replay", type=Path)
    probe.add_argument("--data-dir", type=Path, default=DATA_DIR)
    probe.add_argument("--output-dir", type=Path)
    args, _ = probe.parse_known_args(sys.argv[1:] if argv is None else argv)
    day = args.as_of or (json.loads(args.replay.read_bytes())["source_date"] if args.replay else None)
    if not day:
        return _main_impl(argv)
    root = args.output_dir or args.data_dir / "report/initial_entry_quantity_type_policy"
    # Match the existing dispatcher admission deadline. Another heavy owner
    # legitimately reserves both slots for longer than the direct CLI's 60s.
    with direct_job(args.data_dir, "initial_entry_quantity_refresh", day, timeout=14400), use(root), use(args.data_dir / "report/initial_entry_quantity_type_policy"):
        return _main_impl(argv)


if __name__ == "__main__":
    raise SystemExit(main())
