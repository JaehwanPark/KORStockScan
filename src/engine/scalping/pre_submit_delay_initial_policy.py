"""Initial paired-quote timing contracts, owned by pre_submit_delay_tuning.

Quotes are estimates of price timing, never fills or net PnL. Publication uses
one committed manifest pointer; runtime reads only a prepared immutable map.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
import fcntl
import hashlib
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import tempfile
from types import MappingProxyType

REPORT_SCHEMA = "pre_submit_delay_tuning_v2"
POLICY_SCHEMA = "pre_submit_delay_policy_v2"
MANIFEST_SCHEMA = "pre_submit_delay_committed_generation_v2"
LEGACY_ALGORITHM = "qualified_anchor_shared_chronological_purged_split_v2"
PAIRED_ALGORITHM = "qualified_anchor_candidate_paired_chronological_split_v3"
ALGORITHM = "qualified_anchor_short_and_long_paired_chronological_split_v4"
ALGORITHMS = (LEGACY_ALGORITHM, PAIRED_ALGORITHM, ALGORITHM)
LEGACY_MAPPING_VERSION = "registered_machine_primary_or_sorted_union_v1"
MAPPING_VERSION = "native_machine_definition_bound_situation_v2"
HORIZONS = (0, 30, 60, 120, 180)
SHORT_AND_LONG_HORIZONS = (0, 1, 3, 5, 30, 60, 120, 180)
MARKETS = ('PREMARKET', 'REGULAR', 'INTEGRATED_AFTERMARKET')
MAX_BYTES = 4 * 1024 * 1024
MAX_OPPORTUNITIES = 20000
MAX_CELLS = 4096
CONTRACT_PATHS = (
    'src/engine/scalping/pre_submit_delay_initial_policy.py',
    'src/engine/scalping/pre_submit_delay_tuning.py',
    'src/engine/infrastructure/main_policy_loading.py',
    'src/engine/scalping/pre_submit_delay_observation.py',
    'src/engine/scalping/reversal_registered_catalog.py',
    'src/engine/sniper_state_handlers.py', 'src/engine/kiwoom_sniper_v2.py',
    'src/engine/scalping/scanner_async_eval.py', 'src/utils/pipeline_event_logger.py',
    'src/engine/pipeline_event_summary.py', 'src/utils/threshold_cycle_registry.py',
    'src/engine/automation/runtime_policy_bootstrap.py',
    'src/engine/automation/postclose_summary_handoff.py',
    'src/engine/runtime_approval_summary.py',
    'src/engine/lifecycle/research_input_budget.py',
    'src/engine/lifecycle/research_admission.py',
    'src/engine/lifecycle/research_storage.py',
    'src/engine/lifecycle/research_disk_budget.py',
    'src/engine/lifecycle/research_jsonl_jobs.py',
    'src/engine/automation/pre_submit_delay_source_ledger.py',
    'src/engine/infrastructure/research_release_transition.py',
    'src/engine/automation/pre_submit_delay_partitioned_research.py',
    'src/engine/automation/pre_submit_delay_situation_projection.py',
    'src/engine/scalping/reversal_extended_catalog.py',
    'src/engine/monitoring/submission_bottleneck_monitor.py',
    'src/engine/scalping/continuous_reversal_policy.py',
    'src/engine/scalping/reversal_auxiliary_registry.py',
    'src/engine/ai_engine_openai.py',
)


def code_contract(root=None):
    root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    return digest({name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in CONTRACT_PATHS})


def projection_contract():
    """Qualification dependencies, separate from consumers and selection."""
    import inspect
    from . import pre_submit_delay_tuning as owner
    from .reversal_registered_catalog import MANIFEST
    from .reversal_extended_catalog import DEFINITIONS
    from src.engine.automation.pre_submit_delay_partitioned_research import project as partitioned_project
    from src.engine.automation import pre_submit_delay_situation_projection as recovery
    from .reversal_auxiliary_registry import timing_compatibility_identity, response_contract_shape
    functions = (project_rows, partitioned_project, recovery.prepare, recovery.enrich,
                 number, digest, session, situation, situation_fields, _situation_definition_ref, _legacy_situation, owner._source_rows,
                 owner._number, owner._digest, owner.decision_source_sha256,
                 owner.quote_source_sha256, owner._quote_source_issue,
                 timing_compatibility_identity, response_contract_shape)
    return digest({'functions':{f.__module__+'.'+f.__name__:inspect.getsource(f) for f in functions},
                   'decision_keys':owner._DECISION_SOURCE_KEYS, 'quote_keys':owner._QUOTE_SOURCE_KEYS,
                   'minimal_fields':sorted(owner._V2_SOURCE_FIELDS),
                   'stages':sorted(owner.SOURCE_STAGES), 'mapping':MANIFEST, 'mapping_version':MAPPING_VERSION,
                   'observation_contract': {
                       'grid': owner.OBSERVATION_GRID_VERSION,
                       'horizons': owner.OBSERVATION_HORIZONS,
                       'short_horizons': owner.SHORT_RESEARCH_HORIZONS,
                       'short_tolerance_sec': owner.SHORT_OBSERVATION_TOLERANCE_SEC,
                       'implementation': inspect.getsource(owner.observation_horizons),
                   },
                   'native_definitions':DEFINITIONS})


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def number(value):
    if isinstance(value, bool):
        return None
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def session(value):
    text = str(value or "").upper()
    if "PREMARKET" in text or text == "PRE":
        return "PREMARKET"
    if "AFTERMARKET" in text or text == "AFTER":
        return "INTEGRATED_AFTERMARKET"
    if text in {"REGULAR", "KRX_REGULAR"}:
        return "REGULAR"
    return "UNKNOWN"


def _legacy_situation(fields):
    primary = str(fields.get("primary_branch_id") or "")
    matched = fields.get("matched_branch_ids") or []
    if isinstance(matched, str):
        try:
            matched = json.loads(matched)
        except ValueError:
            matched = []
    from .reversal_registered_catalog import MANIFEST
    definitions = MANIFEST["definitions"]
    if primary in definitions:
        return primary
    if (isinstance(matched, list) and 0 < len(matched) <= 32
        and all(isinstance(x, str) and x in definitions for x in matched)):
        return "+".join(sorted(set(matched)))
    return "UNKNOWN"



@lru_cache(maxsize=512)
def _situation_definition_ref(identity):
    from .reversal_extended_catalog import branch, DEFINITIONS
    from .continuous_reversal_postclose import digest as native_digest
    definition = branch(identity)
    return identity + ':' + (definition.get('definition_sha256') or native_digest(DEFINITIONS[identity]))


def situation_fields(fields):
    """Freeze the already validated machine's situation; no file or model calls.

    UNION legitimately has no primary. Definition references come from the
    machine receipt, with catalog validation limited to the matched branches.
    This projection cannot change the machine or auxiliary decision.
    """
    from collections.abc import Mapping
    from .reversal_extended_catalog import DEFINITIONS
    assessment = fields.get('entry_mechanistic_policy_decision') or {}
    if not isinstance(assessment, Mapping):
        assessment = {}
    primary = fields.get('continuous_reversal_primary_branch', fields.get('primary_branch_id'))
    matched = fields.get('continuous_reversal_matched_branches', fields.get('matched_branch_ids'))
    if matched is None:
        matched = assessment.get('matched_branches')
    if primary is None:
        primary = assessment.get('primary_branch')
    primary = primary or None
    if isinstance(matched, (tuple, list)):
        matched = list(matched)
    elif isinstance(matched, str) and len(matched) <= 8192:
        try: matched = json.loads(matched)
        except ValueError: matched = []
    result = dict(primary_branch_id=primary, matched_branch_ids=[],
                  situation_definition_refs=[], situation_mapping_version=MAPPING_VERSION,
                  situation_key='UNKNOWN', situation_source_status='machine_branches_missing')
    if matched is None and isinstance(primary, str) and primary:
        matched = [primary]
    if (not isinstance(matched, list) or not 0 < len(matched) <= 32
            or any(not isinstance(b, str) or b not in DEFINITIONS for b in matched)):
        return result
    matched = sorted(set(matched))
    result['matched_branch_ids'] = json.dumps(matched, separators=(',', ':'))
    if primary is not None and primary not in matched:
        result['situation_source_status'] = 'primary_matched_conflict'
        return result
    expected = [_situation_definition_ref(b) for b in matched]
    refs = fields.get('continuous_reversal_matched_policy_refs', assessment.get('matched_policy_refs'))
    if isinstance(refs, str) and len(refs) <= 16384:
        try: refs = json.loads(refs)
        except ValueError: refs = []
    if refs is not None and (not isinstance(refs, (list, tuple)) or any(not isinstance(r, str) for r in refs) or sorted(refs) != expected):
        result['situation_source_status'] = 'machine_definition_reference_conflict'
        return result
    result.update(situation_definition_refs=json.dumps(expected, separators=(',', ':')), situation_key=primary or '+'.join(matched),
                  situation_source_status='native_machine_bound')
    return result


def situation(fields):
    if fields.get('situation_mapping_version') == MAPPING_VERSION:
        # Source receipts bind these fields to the original machine. Do not
        # reinterpret old definitions with today's installed catalog.
        ids, refs = fields.get('matched_branch_ids'), fields.get('situation_definition_refs')
        primary = fields.get('primary_branch_id')
        primary = None if primary in (None, '', 'None', 'null') else primary
        try:
            ids = json.loads(ids) if isinstance(ids, str) and len(ids) <= 8192 else ids
            refs = json.loads(refs) if isinstance(refs, str) and len(refs) <= 16384 else refs
        except ValueError:
            return 'UNKNOWN'
        if (fields.get('situation_source_status') == 'native_machine_bound'
                and isinstance(ids, list) and 0 < len(ids) <= 32
                and all(isinstance(b, str) and b and len(b) <= 160 for b in ids)
                and ids == sorted(set(ids)) and isinstance(refs, list) and len(refs) == len(ids)
                and all(isinstance(r, str) and r.startswith(b + ':')
                        and len(r[len(b)+1:]) == 64 and all(c in '0123456789abcdef' for c in r[len(b)+1:])
                        for b, r in zip(ids, refs))
                and (primary is None or primary in ids)):
            key = primary or '+'.join(ids)
            return key if fields.get('situation_key') == key else 'UNKNOWN'
        return 'UNKNOWN'
    if 'continuous_reversal_matched_branches' in fields or 'entry_mechanistic_policy_decision' in fields:
        return situation(situation_fields(fields))
    return _legacy_situation(fields)


def cell_key(anchor, market, kind="ALL", context="ALL", *, parents=None):
    key = "|".join((anchor, market, kind, context))
    return digest(list(parents)) + "|" + key if parents is not None else key


def _stats(values, denominator):
    ordered = sorted(values)
    n = len(ordered)
    def quantile(fraction):
        if not n:
            return None
        at = (n - 1) * fraction
        low, high = int(at), math.ceil(at)
        return ordered[low] + (ordered[high] - ordered[low]) * (at - low)
    return {"n": n, "eligible_n": denominator, "coverage": n / denominator if denominator else 0,
            "mean_bp": math.fsum(ordered) / n if n else None,
            "median_bp": quantile(.5), "p10_bp": quantile(.1), "p90_bp": quantile(.9),
            "improved_n": sum(v > 0 for v in ordered),
            "worsened_n": sum(v < 0 for v in ordered), "equal_n": sum(v == 0 for v in ordered)}


def project_rows(rows):
    """Verify exact legacy/new receipts without changing their source bytes."""
    from .pre_submit_delay_tuning import (decision_source_sha256, _quote_source_issue,
        OBSERVATION_HORIZONS, SHORT_RESEARCH_HORIZONS, SHORT_OBSERVATION_TOLERANCE_SEC)
    commits, quotes, conflicts, reasons = {}, defaultdict(dict), set(), Counter()
    for row in rows:
        fields = row.get("fields")
        if not isinstance(fields, dict):
            reasons["fields_missing"] += 1
            continue
        identity = (str(row.get("emitted_date")), str(row.get("stock_code")),
                    str(fields.get("delay_intent_id") or ""))
        if not identity[-1]:
            reasons["intent_identity_missing"] += 1
            continue
        if row.get("stage") == "pre_submit_delay_committed":
            if identity in commits and commits[identity] != fields:
                conflicts.add(identity)
            commits[identity] = fields
        elif row.get("stage") == "pre_submit_delay_quote_observed":
            horizon = number(fields.get("target_delay_sec"))
            if horizon in OBSERVATION_HORIZONS:
                if horizon in quotes[identity] and quotes[identity][horizon] != fields:
                    conflicts.add((identity, horizon))
                quotes[identity][horizon] = fields
    result, canonical_rows, canonical_conflicts = [], {}, set()
    for identity, fields in commits.items():
        if len(result) >= MAX_OPPORTUNITIES:
            raise ValueError("initial_delay_projection_budget_exceeded")
        machine = str(fields.get("original_machine_observation_sha256") or "")
        stamp = number(fields.get("decision_committed_at_epoch"))
        verdict = fields.get("auxiliary_effective_action")
        if (identity in conflicts or fields.get("owner") != "main_scalping"
            or fields.get("entry_action") != "ENTER_NOW" or verdict != "PASS"
            or len(machine) != 64 or any(c not in "0123456789abcdef" for c in machine)
            or fields.get("decision_source_sha256") != decision_source_sha256(fields)
            or stamp is None or stamp <= 0):
            reasons["commit_or_effective_pass_invalid"] += 1
            continue
        from datetime import datetime
        from zoneinfo import ZoneInfo
        if (not identity[1].isdigit() or len(identity[1]) != 6
                or datetime.fromtimestamp(stamp, ZoneInfo('Asia/Seoul')).date().isoformat() != identity[0]):
            reasons['commit_date_or_symbol_identity_invalid'] += 1
            continue
        anchor = str(fields.get("anchor_kind") or "price_ready")
        market = session(fields.get("market_session_bucket"))
        if anchor not in {"price_ready", "signal_ready"} or market == "UNKNOWN":
            reasons["anchor_or_session_unknown"] += 1
            continue
        planned_qty = number(fields.get('planned_qty'))
        if anchor == 'price_ready' and (planned_qty is None or planned_qty <= 0 or not planned_qty.is_integer()):
            reasons['price_ready_quantity_unverified'] += 1
            continue
        parent = (str(fields.get("entry_mechanistic_policy_sha256") or "legacy"),
                  str(fields.get("entry_ai_soft_policy_sha256") or "legacy"))
        captured_parent = parent
        # A machine observation belongs to one native evaluation. Proven retry
        # aliases share that original observation; distinct native observations
        # are never merged merely because the symbol or primary branch matches.
        native = fields.get('original_evaluation_attempt_id') or fields.get('evaluation_attempt_id') or fields.get('request_id')
        native_bound = isinstance(native, str) and 0 < len(native) <= 512 and native.strip() == native
        if fields.get('entry_auxiliary_policy_identity_version') not in (None,'','None','null'):
            from .reversal_auxiliary_registry import validate_identity, timing_compatibility_identity
            try:
                proof = fields.get('entry_auxiliary_policy_identity')
                if isinstance(proof,str):proof=json.loads(proof)
                proof = validate_identity(proof)
                if (proof['schema'] != fields['entry_auxiliary_policy_identity_version']
                        or proof['identity_sha256'] != parent[1]):
                    raise ValueError('auxiliary_identity_parent_mismatch')
                # Request-local wire citation aliases are not policy changes.
                # Preserve captured hashes and derive only the verified timing
                # equivalence key; prompt/risk/model/code remain exact.
                parent = (parent[0], timing_compatibility_identity(proof))
            except (ValueError, TypeError):
                native_bound = False
                reasons['auxiliary_identity_unverified'] += 1
        canonical = digest([identity[0], identity[1], machine, native if native_bound else list(identity), parent, anchor])
        valid = {}
        for horizon, quote in quotes.get(identity, {}).items():
            ask, bid, depth = (number(quote.get(key)) for key in ("ask_price", "best_bid", "ask_qty"))
            issue = _quote_source_issue(fields, quote)
            if ((identity, horizon) in conflicts or issue or ask is None or bid is None
                or depth is None or not 0 < bid <= ask or depth <= 0
                or str(quote.get("quote_valid")).lower() not in {"true", "1"}
                or quote.get("quote_consistency_state") not in {"single_source", "fresh_consistent"}):
                reasons["quote:" + (issue or "values_or_conflict_invalid")] += 1
                continue
            valid[horizon] = quote
        zero = valid.get(0)
        pairs = {int(horizon): (float(zero["ask_price"]) - float(quote["ask_price"]))
                 / float(zero["ask_price"]) * 10000 for horizon, quote in valid.items()
                 if horizon in HORIZONS[1:] and zero}
        # Keep short observations separate so frozen v2/v3 selectors ignore
        # them. V4 admits them only with the strict short-clock P0 baseline.
        short_zero = (zero if zero and number(zero.get('actual_offset_sec')) is not None
                      and 0 <= number(zero.get('actual_offset_sec')) <= SHORT_OBSERVATION_TOLERANCE_SEC
                      else None)
        short_pairs = {int(horizon): (float(short_zero['ask_price']) - float(quote['ask_price']))
                       / float(short_zero['ask_price']) * 10000 for horizon, quote in valid.items()
                       if horizon in SHORT_RESEARCH_HORIZONS and short_zero}
        situation_source = fields.get('_native_situation_projection')
        if situation_source and (not isinstance(situation_source, dict)
                or situation_source.get('native_observation_sha256') != fields.get('original_machine_observation_sha256')
                or situation_source.get('attempt') != fields.get('evaluation_attempt_id')
                or situation_source.get('parent') != fields.get('entry_mechanistic_policy_sha256')
                or situation_source.get('symbol') != str(identity[1])):
            raise ValueError('delay_situation_projection_identity_invalid')
        kind = situation(situation_source['fields']) if situation_source else situation(fields)
        opportunity = {"identity": canonical, "alias": list(identity), "anchor_kind": anchor,
                       "session": market, "parent_compatibility": list(parent),
                       "captured_parent_compatibility": list(captured_parent),
                       "native_evaluation_bound":native_bound,
                       "committed_at": stamp, "observation_end_at": stamp + 183,
                       "p0_valid": zero is not None, "pairs": pairs,
                       "situation": kind, "execution_context": "ALL",
                       "decision_source_sha256": fields["decision_source_sha256"]}
        frozen_type = fields.get('delay_decision_type')
        if isinstance(frozen_type, str):
            try:
                frozen_type = json.loads(frozen_type) if len(frozen_type) <= 8192 else None
            except ValueError:
                frozen_type = None
        reference_price = number(fields.get('original_signal_reference_price'))
        reference_epoch = number(fields.get('original_signal_reference_epoch'))
        reference_id = fields.get('original_signal_id')
        reference_valid = (fields.get('signal_reference_contract_version') == 'native_confirmation_price_v1'
                           and reference_price is not None and reference_price > 0
                           and reference_epoch is not None and 0 < reference_epoch <= stamp
                           and isinstance(reference_id, str) and 0 < len(reference_id) <= 512)
        opportunity.update(
            original_machine_observation_sha256=machine,
            native_evaluation_attempt_id=native if native_bound else None,
            independent_opportunity_sha256=(digest([identity[0], identity[1], machine, native, parent])
                                           if native_bound else None),
            research_short_pairs=short_pairs,
            research_short_p0_valid=short_zero is not None,
            execution_features={
                'schema': 'pre_submit_delay_frozen_execution_features_v1',
                'planned_qty': planned_qty,
                'price_cap': number(fields.get('price_cap')),
                'decision_type': (frozen_type if isinstance(frozen_type, dict)
                                  and frozen_type.get('schema') == 'pre_submit_delay_decision_type_v1'
                                  else None),
                'p0_ask': number(zero.get('ask_price')) if zero else None,
                'p0_bid': number(zero.get('best_bid')) if zero else None,
                'p0_ask_qty': number(zero.get('ask_qty')) if zero else None,
                'p0_actual_offset_sec': number(zero.get('actual_offset_sec')) if zero else None,
                'p0_source_age_sec': (number(zero['quote_observed_at_epoch']) - number(zero['ws_last_0d_epoch'])
                                      if zero else None),
                'original_signal_reference_price': reference_price if reference_valid else None,
                'original_signal_reference_epoch': reference_epoch if reference_valid else None,
                'original_signal_id': reference_id if reference_valid else None,
            })
        if situation_source:
            opportunity['situation_projection'] = situation_source
        # A retry is an alias only when its native evaluation and immutable
        # anchor/outcomes agree. Late conflicts invalidate every alias.
        semantic = digest({k:v for k,v in opportunity.items() if k not in {'alias','decision_source_sha256'}})
        previous = canonical_rows.get(canonical)
        if previous is not None:
            if previous[0] != semantic:
                canonical_conflicts.add(canonical)
                reasons['canonical_opportunity_conflict'] += 1
            else:
                reasons['duplicate_opportunity_alias'] += 1
                if tuple(opportunity['alias']) < tuple(previous[1]['alias']):
                    canonical_rows[canonical] = semantic, opportunity
        else:
            canonical_rows[canonical] = semantic, opportunity
    result = [row for key, (_,row) in canonical_rows.items() if key not in canonical_conflicts]
    return result, {"raw_commit_n": len(commits), "qualified_pass_n": len(result),
                    "p0_valid_n": sum(row["p0_valid"] for row in result),
                    "native_evaluation_unverified_n":sum(not row['native_evaluation_bound'] for row in result),
                    "parent_compatibility_unverified_n":sum(any(len(p)!=64 or any(c not in '0123456789abcdef' for c in p)
                        for p in row['parent_compatibility']) for row in result),
                    "exclusions": dict(reasons)}


def _selection_legacy(train, validation):
    candidates = [d for d in HORIZONS[1:] if any(d in r["pairs"] for r in train)]
    common = [r for r in train if candidates and all(d in r["pairs"] for d in candidates)]
    empty = {"delay_sec": None, "selection_basis": "unsupported", "runtime_apply_allowed": False,
             "train": _stats([], len(train)), "validation": _stats([], len(validation)),
             "candidate_delays_sec": candidates, "comparison_delay_sec": None}
    if not common:
        return empty
    means = {d: math.fsum(r["pairs"][d] for r in common) / len(common) for d in candidates}
    best = min(candidates, key=lambda d: (-means[d], d))
    holdout = [r["pairs"][best] for r in validation if best in r["pairs"]]
    if not holdout:
        return {**empty, "comparison_delay_sec": best, "train": _stats([r["pairs"][best] for r in common], len(train))}
    mean = math.fsum(holdout) / len(holdout)
    basis = ("paired_quote_initial" if means[best] > 0 and mean > 0 else
             "paired_quote_immediate" if means[best] <= 0 and mean <= 0 else
             "incumbent_on_unconfirmed_pattern")
    return {**empty, "delay_sec": best if basis == "paired_quote_initial" else 0,
            "selection_basis": basis, "runtime_apply_allowed": True,
            "comparison_delay_sec": best,
            "train": _stats([r["pairs"][best] for r in common], len(train)),
            "validation": _stats(holdout, len(validation)),
            "train_ids_sha256": digest([r["identity"] for r in common]),
            "validation_ids_sha256": digest([r["identity"] for r in validation if best in r["pairs"]])}


def candidate_horizons(algorithm):
    if algorithm not in ALGORITHMS:
        raise ValueError('initial_delay_algorithm_invalid')
    return SHORT_AND_LONG_HORIZONS if algorithm == ALGORITHM else HORIZONS


def selection_evidence(cell):
    """Classify comparative evidence independently of the operational delay."""
    if cell.get("runtime_apply_allowed") is not False:
        if cell.get("selection_basis") == "paired_quote_initial" and (number(cell.get("delay_sec")) or 0) > 0:
            return "positive_delay_supported"
        if cell.get("selection_basis") == "paired_quote_immediate" and cell.get("delay_sec") == 0:
            return "immediate_supported_on_observed_pairs"
    return "indeterminate"


def selection_pairs(row, algorithm):
    """Only v4 may select already-qualified short observations; v2/v3 are frozen."""
    pairs = {int(k): v for k, v in row['pairs'].items()}
    if algorithm == ALGORITHM:
        short = row.get('research_short_pairs') or {}
        if (not isinstance(short, dict) or
            (short and (row.get('research_short_p0_valid') is not True or row.get('p0_valid') is not True))
            or any(str(k) not in {'1', '3', '5'} or number(v) is None for k,v in short.items())):
            raise ValueError('initial_delay_short_pair_contract_invalid')
        pairs.update({int(k): v for k,v in short.items()})
    return pairs


def _selection(train, validation, *, horizons=HORIZONS):
    """Each horizon competes against its own same-opportunity P0 pairs."""
    candidates = [d for d in horizons[1:] if any(d in r['pairs'] for r in train)]
    stats = {d:_stats([r['pairs'][d] for r in train if d in r['pairs']], len(train)) for d in candidates}
    empty = dict(delay_sec=None, selection_basis='unsupported', runtime_apply_allowed=False,
        train=_stats([], len(train)), validation=_stats([], len(validation)),
        candidate_delays_sec=candidates, comparison_delay_sec=None,
        candidate_train_stats={str(d):s for d,s in stats.items()},
        population_role='candidate_same_opportunity_p0_pairs')
    if not candidates:
        return empty
    best = min(candidates, key=lambda d:(-stats[d]['mean_bp'], d))
    holdout = _stats([r['pairs'][best] for r in validation if best in r['pairs']], len(validation))
    if not holdout['n']:
        return {**empty, 'comparison_delay_sec':best, 'train':stats[best]}
    basis = ('paired_quote_initial' if stats[best]['mean_bp'] > 0 and holdout['mean_bp'] > 0 else
        'paired_quote_immediate' if stats[best]['mean_bp'] <= 0 and holdout['mean_bp'] <= 0 else
        'incumbent_on_unconfirmed_pattern')
    return {**empty, 'delay_sec':best if basis == 'paired_quote_initial' else 0,
        'selection_basis':basis, 'runtime_apply_allowed':True, 'comparison_delay_sec':best,
        'train':stats[best], 'validation':holdout,
        'train_ids_sha256':digest([r['identity'] for r in train if best in r['pairs']]),
        'validation_ids_sha256':digest([r['identity'] for r in validation if best in r['pairs']])}


def lineage_eligible(row, effective_date):
    return effective_date < '2026-10-10' or (row.get('native_evaluation_bound') is True
        and len(row.get('parent_compatibility',()))==2
        and all(isinstance(p,str) and len(p)==64 and all(c in '0123456789abcdef' for c in p)
                for p in row.get('parent_compatibility', ())))


def build_initial(rows, *, source_date, publication_date, effective_date, source_sha256, code_contract_sha256,
                  _projected=None, source_receipt=None, _algorithm=None, _projection_contract=None, _mapping_version=None):
    algorithm = _algorithm or ALGORITHM
    if algorithm not in ALGORITHMS:
        raise ValueError('initial_delay_algorithm_invalid')
    if not date.fromisoformat(source_date) < date.fromisoformat(effective_date) or not (
        date.fromisoformat(source_date) <= date.fromisoformat(publication_date) < date.fromisoformat(effective_date)
    ):
        raise ValueError("initial_delay_dates_invalid")
    opportunities, census = project_rows(rows) if _projected is None else _projected
    groups = defaultdict(list)
    for row in opportunities:
        if row["p0_valid"]:
            groups[(row["anchor_kind"], row["session"], tuple(row["parent_compatibility"]))].append(row)
    cells, partitions = {}, []
    for (anchor, market, parents), group in sorted(groups.items()):
        ordered = sorted((r for r in group if algorithm == LEGACY_ALGORITHM or
                          lineage_eligible(r,effective_date)), key=lambda r: (r["committed_at"], r["identity"]))
        split = min(len(ordered) - 1, max(1, int(len(ordered) * .7))) if len(ordered) > 1 else len(ordered)
        validation = ordered[split:]
        cutoff = validation[0]["committed_at"] if validation else None
        train = [r for r in ordered[:split] if cutoff is None or r["observation_end_at"] < cutoff]
        partition = {"anchor_kind": anchor, "session": market, "parent_compatibility": list(parents),
                     "train_ids": [r["identity"] for r in train],
                     "validation_ids": [r["identity"] for r in validation],
                     "purged_ids": [r["identity"] for r in ordered[:split] if r not in train],
                     "qualified_ids": [r["identity"] for r in ordered]}
        partition["sha256"] = digest(partition)
        partitions.append(partition)
        kinds = {"ALL"} | {r["situation"] for r in group if r["situation"] != "UNKNOWN"}
        for kind in sorted(kinds):
            key = cell_key(anchor, market, kind, parents=parents)
            # A cell cannot silently pool incompatible machine/aux parents.
            if key in cells:
                raise ValueError("initial_delay_parent_compatibility_conflict")
            learning = [r for r in train if kind == "ALL" or r["situation"] == kind]
            holdout = [r for r in validation if kind == "ALL" or r["situation"] == kind]
            selection = (_selection_legacy(learning, holdout) if algorithm == LEGACY_ALGORITHM else
                _selection([{**r, 'pairs':selection_pairs(r,algorithm)} for r in learning],
                           [{**r, 'pairs':selection_pairs(r,algorithm)} for r in holdout],
                           horizons=candidate_horizons(algorithm)))
            if algorithm != LEGACY_ALGORITHM and not ordered:
                selection = {**selection,'delay_sec':0,'selection_basis':'unverified_lineage_immediate_default',
                             'runtime_apply_allowed':False}
            if algorithm == LEGACY_ALGORITHM and effective_date >= '2026-10-10' and (any(len(p)!=64 or any(c not in '0123456789abcdef' for c in p) for p in parents)
                    or any(not row.get('native_evaluation_bound') for row in learning+holdout)):
                # Historical valid quotes still support the neutral zero-delay
                # initial default. Unknown parents/native IDs cannot authorize
                # a positive timing rule or borrow another policy's evidence.
                selection = {**selection, 'delay_sec':0,
                    'selection_basis':'unverified_lineage_immediate_default', 'runtime_apply_allowed':False}
            cells[key] = {**selection, "anchor_kind": anchor, "session": market, "situation": kind,
                          "execution_context": "ALL", "parent_compatibility": list(parents),
                          "partition_sha256": partition["sha256"],
                          "fallback_key": cell_key(anchor, market, parents=parents) if kind != "ALL" else None,
                          "evidence_grade": "estimated_provisional"}
            if len(cells) > MAX_CELLS:
                raise ValueError("initial_delay_cell_budget_exceeded")
    price_pairs = sum(len(selection_pairs(r,algorithm)) for r in opportunities if r["anchor_kind"] == "price_ready")
    blocked = not price_pairs or not source_sha256
    report = {"schema": REPORT_SCHEMA, "analysis_axis": "pre_submit_delay", "source_date": source_date,
              "publication_date": publication_date, "effective_date": effective_date,
              "source_sha256": source_sha256, "code_contract_sha256": code_contract_sha256,
              'source_projection_contract_sha256':_projection_contract or projection_contract(),
              "source_receipt": source_receipt,
              "algorithm": algorithm, "mapping_version": _mapping_version or MAPPING_VERSION,
              "status": "blocked" if blocked else "initial_timing_policy_selected" if any(
                  cell["anchor_kind"] == "price_ready" and (cell["delay_sec"] or 0) > 0 for cell in cells.values()
              ) else "initial_baseline_immediate", "census": census, "price_ready_pair_n": price_pairs,
              "partitions": partitions, "cells": cells, "default_delay_sec": 0,
              # JSON object keys are strings. Canonicalize horizon keys before
              # sealing, so a multi-horizon projection has the same generation
              # before and after persistence (30/120 numeric sorting differs).
              "qualified_projection": [{**row, 'pairs': {str(k): v for k, v in row['pairs'].items()}}
                                       for row in opportunities],
              "runtime_effect": False, "actual_order_submitted": False,
              "paired_net_ev_delta_pct": None, "realized_pnl_krw": None,
              "metric_role": "initial_entry_price_timing_estimate",
              "decision_authority": "next_preopen_initial_pre_submit_timing_policy",
              "primary_decision_metric": "mean_paired_price_improvement_bp"}
    policy = {key: report[key] for key in ("source_date", "publication_date", "source_sha256",
              "code_contract_sha256", "algorithm", "mapping_version", "cells", "default_delay_sec",
              "metric_role", "decision_authority", "primary_decision_metric")}
    policy.update(schema=POLICY_SCHEMA, policy_kind="initial_paired_quote_timing",
                  effective_from=effective_date, expires_on=effective_date,
                  supported_anchor_kind="price_ready", selection_status=report["status"],
                  runtime_apply_allowed=not blocked, report_sha256=digest(report))
    policy["policy_sha256"] = digest(policy)
    report["policy_sha256"] = policy["policy_sha256"]
    return report, policy


def frozen_projection_contract(report):
    """Selection validation reuses the sealed qualification generation.

    This is not fresh source qualification: source bytes/ledgers and the
    candidate code handoff retain their independent verification owners.
    """
    value = report.get('source_projection_contract_sha256')
    if not isinstance(value, str) or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('initial_delay_projection_contract_invalid')
    return value


def validate(policy, report, *, target_date=None):
    if policy.get('storage_schema') or report.get('storage_schema'):
        from src.engine.automation.pre_submit_delay_partitioned_research import validate as validate_sharded
        return validate_sharded(policy, report, target_date=target_date)
    if policy.get("schema") != POLICY_SCHEMA or report.get("schema") != REPORT_SCHEMA:
        raise ValueError("initial_delay_schema_invalid")
    sha = policy.get("policy_sha256")
    if (sha != digest({k: v for k, v in policy.items() if k != "policy_sha256"})
        or sha != report.get("policy_sha256")
        or policy.get("report_sha256") != digest({k: v for k, v in report.items() if k != "policy_sha256"})
        or policy.get("cells") != report.get("cells") or policy.get("default_delay_sec") != 0
        or policy.get("source_date") != report.get("source_date")
        or policy.get("effective_from") != report.get("effective_date")
        or policy.get("supported_anchor_kind") != "price_ready"
        or policy.get("algorithm") not in ALGORITHMS
        or policy.get('algorithm') != report.get('algorithm') or policy.get("mapping_version") not in (MAPPING_VERSION, LEGACY_MAPPING_VERSION)
        or policy.get("runtime_apply_allowed") is not True or report.get("price_ready_pair_n", 0) < 1):
        raise ValueError("initial_delay_contract_invalid")
    for key in ("source_sha256", "code_contract_sha256"):
        value = policy.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("initial_delay_generation_invalid")
    if target_date and not policy["effective_from"] <= target_date <= policy["expires_on"]:
        raise ValueError("initial_delay_date_invalid")
    projected = report.get('qualified_projection')
    if not isinstance(projected, list) or len(projected) > MAX_OPPORTUNITIES:
        raise ValueError('initial_delay_projection_invalid')
    ids = set()
    for row in projected:
        if (not isinstance(row, dict) or row.get('identity') in ids
                or not isinstance(row.get('identity'), str) or len(row['identity']) != 64
                or row.get('anchor_kind') not in {'price_ready', 'signal_ready'}
                or row.get('session') not in MARKETS
                or number(row.get('committed_at')) is None
                or row.get('observation_end_at') != row['committed_at'] + 183
                or type(row.get('p0_valid')) is not bool
                or not isinstance(row.get('parent_compatibility'), list)
                or len(row['parent_compatibility']) != 2
                or not isinstance(row.get('pairs'), dict)
                or any(int(d) not in HORIZONS[1:] or number(v) is None for d, v in row['pairs'].items())):
            raise ValueError('initial_delay_projection_invalid')
        ids.add(row['identity'])
    # JSON map keys are strings; normalize only the bounded minimal projection.
    projected = [{**row, 'pairs': {int(k): v for k, v in row['pairs'].items()}} for row in projected]
    rebuilt_report, rebuilt_policy = build_initial([], source_date=report['source_date'],
        publication_date=report['publication_date'], effective_date=report['effective_date'],
        source_sha256=report['source_sha256'], code_contract_sha256=report['code_contract_sha256'],
        _projected=(projected, report['census']), source_receipt=report.get('source_receipt'),
        _algorithm=report['algorithm'],
        _projection_contract=frozen_projection_contract(report),
        _mapping_version=report.get('mapping_version'))
    if digest(rebuilt_policy) != digest(policy) or digest(rebuilt_report) != digest(report):
        raise ValueError('initial_delay_deterministic_selection_invalid')
    for key, cell in policy["cells"].items():
        if key != cell_key(cell["anchor_kind"], cell["session"], cell["situation"], cell["execution_context"], parents=cell["parent_compatibility"]):
            raise ValueError("initial_delay_cell_key_invalid")
        delay = cell.get("delay_sec")
        if delay is not None and (isinstance(delay, bool) or delay not in candidate_horizons(policy['algorithm'])):
            raise ValueError("initial_delay_cell_value_invalid")
        if delay and (cell.get("selection_basis") != "paired_quote_initial" or any(
            cell[split].get("n", 0) < 1 or (cell[split].get("mean_bp") or 0) <= 0 for split in ("train", "validation")
        )):
            raise ValueError("initial_delay_cell_evidence_invalid")


def _read(path):
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents) or path.stat().st_size > MAX_BYTES:
        raise ValueError("initial_delay_artifact_path_or_budget_invalid")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("initial_delay_artifact_budget_invalid")
    value = json.loads(raw)
    if isinstance(value,dict) and value.get('storage_schema'):
        from src.engine.automation.pre_submit_delay_partitioned_research import EvidenceDocument
        return EvidenceDocument(value, path.parent)
    return value


def verify_source(data_root, report, *, pipeline_reference_only=False):
    """Verify compact evidence; consumers may trust sealed raw references.

    Research defaults to full raw verification. Approved policy consumers
    retain the ledger seal, compact bytes and overlap checks without rehashing
    the historical pipeline represented by that ledger.
    """
    from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
    receipt = report.get('source_receipt')
    if not isinstance(receipt, dict) or receipt.get('schema') != 'pre_submit_delay_input_generation_v1':
        raise ValueError('initial_delay_source_window_unverified')
    if report.get('machine_parent_compatibility') is not None:
        from src.engine.automation.pre_submit_delay_situation_projection import machine_parent_mapping
        machine_parent_mapping(report['machine_parent_compatibility'], target_date=report['effective_date'])
    if receipt.get('native_situation_projection'):
        from src.engine.automation.pre_submit_delay_situation_projection import verify
        verify(receipt['native_situation_projection'])
    root = Path(data_root).resolve()
    day = report['source_date']
    if receipt.get('through_date') != day:
        raise ValueError('initial_delay_source_date_invalid')
    def inventory():
        return sorted(str(p) for directory in (root / 'threshold_cycle').glob('date=*/family=pre_submit_delay')
                      if '2026-09-29' <= directory.parent.name.removeprefix('date=') <= day
                      for p in directory.glob('part-execution-*.jsonl'))
    paths = inventory()
    generations = receipt.get('partition_generations')
    if not isinstance(generations, dict) or sorted(generations) != paths:
        raise ValueError('initial_delay_source_inventory_changed')
    dates = {Path(name).parent.parent.name.removeprefix('date=') for name in paths}
    if report['effective_date'] >= '2026-10-10' and not dates - set(receipt.get('isolated_dates', {})) <= set(receipt.get('ledger_generations', {})):
        raise ValueError('initial_delay_exact_raw_compact_window_unverified')
    sha = hashlib.sha256()
    cumulative_generations = {}
    cumulative_paths = []
    identities = {}
    for name in paths:
        path = Path(name)
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise ValueError('window_dependency_path_invalid')
        before = source_stat(path.stat())
        part_sha = hashlib.sha256()
        size = 0
        with path.open('rb') as handle:
            if source_stat(os.fstat(handle.fileno())) != before:
                raise ValueError('window_dependency_changed_during_read')
            for block in iter(lambda:handle.read(64*1024), b''):
                size += len(block)
                part_sha.update(block)
                sha.update(block)
            if (source_stat(os.fstat(handle.fileno())) != before
                    or source_stat(path.stat()) != before or size != before[2]):
                raise ValueError('window_dependency_changed_during_read')
        if {'size':size, 'sha256':part_sha.hexdigest()} != generations[name]:
            raise ValueError('initial_delay_source_generation_changed')
        identities[name] = before
        cumulative_paths.append(name)
        source_day = path.parent.parent.name.removeprefix('date=')
        cumulative_generations[source_day] = {'sha256':sha.hexdigest(), 'paths':list(cumulative_paths)}
    if sha.hexdigest() != report['source_sha256']:
        raise ValueError('initial_delay_source_generation_changed')
    from .pre_submit_delay_tuning import family_source_ledger_path, family_source_ledger_issues
    class ReceiptSnapshot:
        # Ledger validation needs cumulative byte seals, not another JSON scan.
        target_date = day
        source = {'sha256':report['source_sha256'], 'paths':paths,
                  'cumulative_generations':cumulative_generations}
        def verify(self, *_):
            if inventory() != paths:
                raise ValueError('initial_delay_source_inventory_changed')
            for name, expected in identities.items():
                path = Path(name)
                if (path.is_symlink() or any(parent.is_symlink() for parent in path.parents)
                        or source_stat(path.stat()) != expected):
                    raise ValueError('initial_delay_source_generation_changed')
        rows = []
    snapshot = ReceiptSnapshot()
    for source_day, expected in receipt.get('ledger_generations', {}).items():
        path = family_source_ledger_path(root, source_day)
        if byte_generation(path) != expected or family_source_ledger_issues(
                root, source_day, source_snapshot=snapshot,
                pipeline_reference_only=pipeline_reference_only):
            raise ValueError('initial_delay_raw_compact_generation_changed')
    snapshot.verify()


def _atomic(path, value):
    from src.engine.lifecycle.research_disk_budget import atomic
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('initial_delay_artifact_path_or_budget_invalid')
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode()
    if len(data) > MAX_BYTES:
        raise ValueError("initial_delay_artifact_budget_invalid")
    from src.engine.infrastructure.research_release_transition import journal_write
    if journal_write(path,data):return
    with atomic(path,len(data)):
        fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, path)
            directory = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(name).unlink(missing_ok=True)


def committed_paths(data_root, source_date, *, validate_selection=True):
    from src.engine.infrastructure.research_release_transition import assert_readable
    assert_readable(data_root)
    directory = Path(data_root).resolve() / "threshold_cycle/pre_submit_delay_policy"
    pointer = directory / f"committed_{source_date}.json"
    manifest = _read(pointer)
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    if (manifest.get("schema") != MANIFEST_SCHEMA or manifest.get("source_date") != source_date
        or manifest.get("manifest_sha256") != digest(body)):
        raise ValueError("initial_delay_committed_manifest_invalid")
    generation = str(manifest.get("generation") or "")
    if len(generation) != 64 or any(c not in "0123456789abcdef" for c in generation):
        raise ValueError("initial_delay_generation_path_invalid")
    base = directory / "generations" / generation
    report, policy = base / "report.json", base / "policy.json"
    values = {}
    for key, path in (("report", report), ("policy", policy)):
        values[key] = _read(path)
        if (path.is_symlink() or base.is_symlink() or base.parent.is_symlink()
                or digest(values[key]) != manifest[key + "_artifact_sha256"]):
            raise ValueError("initial_delay_generation_artifact_invalid")
    if validate_selection:
        validate(values['policy'], values['report'])
    elif (values['policy'].get('schema') != POLICY_SCHEMA or values['report'].get('schema') != REPORT_SCHEMA
            or values['policy'].get('policy_sha256') != digest({
                k:v for k,v in values['policy'].items() if k != 'policy_sha256'})
            or values['policy'].get('report_sha256') != digest({
                k:v for k,v in values['report'].items() if k != 'policy_sha256'})
            or values['policy'].get('policy_sha256') != values['report'].get('policy_sha256')):
        # Projection reuse has no runtime authority and recalculates selection
        # under the new code. Runtime consumers always use the strict default.
        raise ValueError('initial_delay_projection_pair_invalid')
    if (generation != digest([values['report'], values['policy']]) or any(
        manifest.get(k) != values['policy'].get(k) or values['report'].get(k) != values['policy'].get(k)
        for k in ('source_sha256', 'code_contract_sha256'))
        or values['policy'].get('source_date') != source_date or values['report'].get('source_date') != source_date):
        raise ValueError('initial_delay_manifest_source_or_code_invalid')
    return report, policy, pointer, manifest


def publish(data_root, report, policy, *, expected_incumbent, source_verifier=None):
    validate(policy, report)
    directory = Path(data_root).resolve() / "threshold_cycle/pre_submit_delay_policy"
    if directory.is_symlink() or any(parent.is_symlink() for parent in directory.parents):
        raise ValueError('initial_delay_artifact_path_or_budget_invalid')
    directory.mkdir(parents=True, exist_ok=True)
    pointer = directory / f"committed_{policy['source_date']}.json"
    with (directory / ".publication.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = _read(pointer).get("manifest_sha256") if pointer.exists() else None
        if current != expected_incumbent:
            raise ValueError("initial_delay_incumbent_cas_failed")
        if source_verifier is not None:
            source_verifier()
        generation = digest([report, policy])
        base = directory / "generations" / generation
        if report.get('storage_schema'):
            from src.engine.automation.pre_submit_delay_partitioned_research import copy_evidence
            copy_evidence(report,base)
        for key, value in (("report", report), ("policy", policy)):
            path = base / (key + ".json")
            if path.exists() and _read(path) != value:
                raise ValueError("initial_delay_immutable_generation_conflict")
            if not path.exists():
                _atomic(path, value)
        manifest = {"schema": MANIFEST_SCHEMA, "source_date": policy["source_date"],
                    "generation": generation, "parent_manifest_sha256": current,
                    "report_artifact_sha256": digest(report), "policy_artifact_sha256": digest(policy),
                    "source_sha256": policy["source_sha256"], "code_contract_sha256": policy["code_contract_sha256"]}
        manifest["manifest_sha256"] = digest(manifest)
        # Validate the durable generation before replacing the incumbent
        # pointer. A failed write must never leave a committed mixed pair.
        durable_report, durable_policy = _read(base / 'report.json'), _read(base / 'policy.json')
        if (digest(durable_report) != manifest['report_artifact_sha256']
                or digest(durable_policy) != manifest['policy_artifact_sha256']):
            raise ValueError('initial_delay_generation_artifact_invalid')
        validate(durable_policy, durable_report)
        if source_verifier is not None:
            source_verifier()
        _atomic(pointer, manifest)
        committed_paths(data_root, policy["source_date"])
        return pointer


@dataclass(frozen=True)
class PreparedPolicy:
    policy_sha256: str
    effective_from: str
    expires_on: str
    cells: object
    code_contract_sha256: str

    @classmethod
    def from_artifacts(cls, policy, report, *, target_date, active_parents=None):
        validate(policy, report, target_date=target_date)
        source_cells = policy.get('cells')
        if policy.get('storage_schema'):
            from src.engine.lifecycle.research_storage import iter_tree
            # Research can exceed this population. An active map cannot exceed
            # its existing explicit preparation budget or silently truncate.
            source_cells = {}
            for row in iter_tree(policy.evidence_root,policy['cells_ref']):
                if row['value']['anchor_kind'] != 'price_ready':
                    continue
                # A supported zero cell masks a positive parent. Only unsupported
                # cells may fall back; zero is a decision, not absence.
                if row['value'].get('delay_sec') is None or row['value'].get('runtime_apply_allowed') is False:
                    continue
                if active_parents is not None and tuple(row['value']['parent_compatibility']) not in active_parents:
                    continue
                if len(source_cells)>=MAX_CELLS:
                    raise ValueError('initial_delay_active_preparation_budget_exceeded')
                if row['key'] in source_cells:
                    raise ValueError('initial_delay_cell_key_conflict')
                source_cells[row['key']] = row['value']
        cells = MappingProxyType({key: MappingProxyType({k: tuple(cell[k]) if k == 'parent_compatibility' else cell.get(k) for k in (
            "delay_sec", "selection_basis", "fallback_key", "parent_compatibility", "runtime_apply_allowed")})
            for key, cell in source_cells.items() if cell["anchor_kind"] == "price_ready"})
        return cls(policy["policy_sha256"], policy["effective_from"], policy["expires_on"], cells,
                   policy["code_contract_sha256"])

    def lookup(self, *, target_date, market, kind="UNKNOWN", parents=None):
        if not self.effective_from <= target_date <= self.expires_on:
            return {"delay_sec": 0, "status": "policy_identity_or_date_invalid", "policy_sha256": None}
        # Legacy parent-less callers may use only the legacy stratum; a new
        # machine/aux generation never inherits another parent's positive cell.
        parents = list(parents) if parents is not None else ["legacy", "legacy"]
        key = cell_key("price_ready", session(market), kind, parents=parents)
        fallback = cell_key("price_ready", session(market), parents=parents)
        cell = self.cells.get(key)
        if cell is None or cell["delay_sec"] is None:
            key, cell = fallback, self.cells.get(fallback)
        if cell is None or cell["delay_sec"] is None or tuple(parents) != cell["parent_compatibility"]:
            return {"delay_sec": 0, "status": "unsupported_existing_behavior", "policy_sha256": self.policy_sha256,
                    "evidence_verdict": "indeterminate"}
        return {"delay_sec": cell["delay_sec"], "status": "loaded", "policy_sha256": self.policy_sha256,
                "selected_cell_key": key, "selection_basis": cell["selection_basis"], "schema": POLICY_SCHEMA,
                "evidence_verdict": selection_evidence(cell)}
