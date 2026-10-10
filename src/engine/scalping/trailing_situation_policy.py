"""Causal entry pin and typed effective trailing vectors, all Main scopes.

BASE is exactly the approved market parent. No numeric classifier threshold is
implicitly authorized: absent/unbound configuration carries the parent.
"""
from dataclasses import dataclass
from collections import OrderedDict
from contextlib import contextmanager
from datetime import date
import math
from types import MappingProxyType
import json
import os

from .pre_submit_delay_initial_policy import digest, number
from .trailing_mechanical_policy import (START_MARKETS, normalize_values, market_values_hash,
                                        market_classifier_from_env, selected_policy_env)

SCHEMA = "main_trailing_situation_policy_v1"
PIN_SCHEMA = "main_trailing_situation_pin_v1"
CLASSIFIER_SCHEMA = "main_trailing_entry_situation_classifier_v1"
TYPES = ("HIGH_VARIABILITY", "TREND_CONTINUATION", "REBOUND_RANGE", "BASE")
FEATURES = ("range_pct", "return_pct", "trend_efficiency", "vwap_distance_pct", "spread_pct", "rebound_pct")


def entry_features(bars, *, anchor_at, ask, bid, session_vwap, source_sha256, expected_route):
    """Only supplied shared completed bars; never a fresh history/API query."""
    if (number(anchor_at) is None or number(anchor_at) <= 0
        or not isinstance(source_sha256, str) or len(source_sha256) != 64
        or any(c not in '0123456789abcdef' for c in source_sha256) or not expected_route
        or not isinstance(bars, list) or not 2 <= len(bars) <= 120
        or any(number(row.get("known_at")) is None or number(row['known_at']) > anchor_at
               or number(row.get("closed_at")) is None or number(row['closed_at']) > anchor_at
               or row.get("route") != expected_route for row in bars)):
        return {"status": "classification_source_gap"}
    ordered = sorted(bars, key=lambda row: number(row['closed_at']))
    if len({row["closed_at"] for row in ordered}) != len(ordered):
        return {"status": "classification_source_gap"}
    close = [number(row.get("close")) for row in ordered]
    high = [number(row.get("high")) for row in ordered]
    low = [number(row.get("low")) for row in ordered]
    values = close + high + low + [number(ask), number(bid), number(session_vwap)]
    ask, bid, session_vwap = number(ask), number(bid), number(session_vwap)
    if any(value is None or value <= 0 for value in values) or bid > ask:
        return {"status": "classification_source_gap"}
    if any(lo > c or c > hi for lo, c, hi in zip(low, close, high)):
        return {"status": "classification_source_gap"}
    travel = math.fsum(abs(right - left) for left, right in zip(close, close[1:]))
    features = {"range_pct": 100 * (max(high) - min(low)) / close[-1],
                "return_pct": 100 * (close[-1] / close[0] - 1),
                "trend_efficiency": abs(close[-1] - close[0]) / travel if travel > 0 else 0,
                "vwap_distance_pct": 100 * (close[-1] / session_vwap - 1),
                "spread_pct": 100 * (ask - bid) / ((ask + bid) / 2),
                "rebound_pct": 100 * (close[-1] / min(low) - 1)}
    return {"status": "ready", "known_at": max(number(row['known_at']) for row in ordered),
            "anchor_at": anchor_at, "source_sha256": source_sha256, "route": expected_route,
            "window_bars":len(ordered), "features": features, "feature_sha256": digest(features)}


def validate_classifier(config):
    required = {"schema", "window_bars", "thresholds", "trained_through", "classifier_sha256"}
    if not isinstance(config, dict) or set(config) != required or config["schema"] != CLASSIFIER_SCHEMA:
        raise ValueError("trailing_situation_classifier_invalid")
    if type(config["window_bars"]) is not int or not 2 <= config["window_bars"] <= 120:
        raise ValueError("trailing_situation_window_invalid")
    if set(config["thresholds"]) != {"range_min", "spread_min", "trend_return_min", "trend_efficiency_min", "vwap_min", "rebound_min"}:
        raise ValueError("trailing_situation_threshold_keys_invalid")
    if any(type(v) not in (int, float) or number(v) is None or abs(v) > 100 for v in config["thresholds"].values()):
        raise ValueError("trailing_situation_threshold_invalid")
    if type(config['trained_through']) not in (int, float) or number(config['trained_through']) is None:
        raise ValueError('trailing_situation_training_clock_invalid')
    if config["classifier_sha256"] != digest({k: v for k, v in config.items() if k != "classifier_sha256"}):
        raise ValueError("trailing_situation_classifier_hash_invalid")
    return config


def pin_context(context, *, position_key, entry_at, classifier=None):
    kind, reason = "BASE", "legacy_context_unbound"
    classifier_sha = None
    if classifier is not None:
        validate_classifier(classifier)
        classifier_sha = classifier["classifier_sha256"]
        if (not isinstance(context, dict) or context.get("status") != "ready"
            or context.get('window_bars') != classifier['window_bars']
            or not isinstance(context.get('source_sha256'), str) or len(context['source_sha256']) != 64
            or any(c not in '0123456789abcdef' for c in context['source_sha256'])
            or number(context.get("known_at")) is None or number(context['known_at']) > entry_at
            or number(classifier.get("trained_through")) is None or classifier["trained_through"] > entry_at
            or any(type((context.get('features') or {}).get(key)) not in (int, float)
                   or number((context.get("features") or {}).get(key)) is None for key in FEATURES)
            or context.get('feature_sha256') != digest(context.get('features'))):
            reason = "classification_source_gap"
        else:
            f, t = context["features"], classifier["thresholds"]
            reason = "classified"
            if f["range_pct"] >= t["range_min"] or f["spread_pct"] >= t["spread_min"]:
                kind = "HIGH_VARIABILITY"
            elif (f["return_pct"] >= t["trend_return_min"] and f["trend_efficiency"] >= t["trend_efficiency_min"]
                  and f["vwap_distance_pct"] >= t["vwap_min"]):
                kind = "TREND_CONTINUATION"
            elif f["rebound_pct"] >= t["rebound_min"]:
                kind = "REBOUND_RANGE"
    body = {"schema": PIN_SCHEMA, "position_key": position_key, "entry_at": entry_at,
            "situation_type": kind, "reason": reason, "classifier_sha256": classifier_sha,
            "feature_sha256": (context or {}).get("feature_sha256") if isinstance(context, dict) else None}
    return {**body, "classification_origin_hash": digest(body)}


def validate_pin(pin, position_key):
    return (isinstance(pin, dict) and set(pin) == {'schema', 'position_key', 'entry_at', 'situation_type',
            'reason', 'classifier_sha256', 'feature_sha256', 'classification_origin_hash'}
            and number(pin.get('entry_at')) is not None
            and pin.get("schema") == PIN_SCHEMA and pin.get("position_key") == position_key
            and pin.get("situation_type") in TYPES and pin.get("classification_origin_hash") == digest({
                k: v for k, v in pin.items() if k != "classification_origin_hash"}))


def freeze_shared_entry_context(candle_context, ws, *, anchor_at):
    """Use the already captured causal AI context; never fetch or reconstruct."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from .entry_strategy_policy import digest as source_digest
    frozen = (candle_context or {}).get('strategy_completed_bars') or {}
    body = frozen.get('body') or {}
    try:
        def stamp(text):
            value = datetime.fromisoformat(text)
            return (value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
        known = stamp(body['observed_at'])
        if (frozen.get('sha256') != source_digest(body) or known > anchor_at
                or not isinstance(body.get('bars'), list)):
            raise ValueError('entry_context_hash_or_clock_invalid')
        route = (candle_context or {}).get('market_data_route')
        bars = []
        for row in body['bars'][-120:]:
            closed = stamp(row['dt']) + 60
            if row.get('forming') or closed > anchor_at:
                continue
            bars.append(dict(known_at=known, closed_at=closed, close=row['c'], high=row['h'], low=row['l'], route=route))
        window = (_CLASSIFIER or {}).get('window_bars')
        if window is not None:
            if len(bars) < window:
                raise ValueError('entry_classifier_window_unobserved')
            bars = bars[-window:]
        return entry_features(bars, anchor_at=anchor_at, ask=ws.get('best_ask'), bid=ws.get('best_bid'),
            session_vwap=ws.get('session_vwap') or ws.get('vwap'), source_sha256=frozen['sha256'], expected_route=route)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return {'status':'classification_source_gap', 'anchor_at':anchor_at}


@contextmanager
def _selector_reference(reference):
    """Prepare byte-pinned selector evidence without embedding its large grid.

    Read only during policy preparation; warm effective lookup keeps primitives.
    The existing selector remains the sole source of economic authority.
    """
    import hashlib
    from pathlib import Path
    from contextlib import ExitStack
    from src.utils.constants import DATA_DIR
    from src.engine.lifecycle.holding_window_generation import source_stat, byte_generation
    from src.engine.lifecycle.research_input_budget import Claim
    if not isinstance(reference, dict) or set(reference) != {
        'report_path','report_byte_sha256','policy_path','policy_byte_sha256'}:
        raise ValueError('trailing_situation_selector_reference_invalid')
    root = Path(DATA_DIR).resolve()
    values, generations = {}, {}
    with ExitStack() as retained:
        for kind in ('report','policy'):
            name = reference[kind+'_path']
            if (not isinstance(name,str) or not name.startswith('report/') or Path(name).is_absolute()
                    or '..' in Path(name).parts):
                raise ValueError('trailing_situation_selector_reference_path_invalid')
            path = root / name
            if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
                raise ValueError('trailing_situation_selector_reference_path_invalid')
            before = path.stat()
            if before.st_size > 4*1024*1024:
                raise ValueError('trailing_situation_selector_reference_budget_invalid')
            retained.enter_context(Claim(before.st_size*8))
            raw = path.read_bytes()
            if (source_stat(path.stat()) != source_stat(before) or len(raw)!=before.st_size
                    or hashlib.sha256(raw).hexdigest() != reference[kind+'_byte_sha256']):
                raise ValueError('trailing_situation_selector_reference_generation_invalid')
            values[kind] = json.loads(raw)
            generations[path] = reference[kind+'_byte_sha256']
        if any(byte_generation(path)['sha256'] != sha for path,sha in generations.items()):
            raise ValueError('trailing_situation_selector_reference_generation_invalid')
        yield values['report'], values['policy'], reference['report_byte_sha256']


def _override_values(override, *, market, kind, parent_sha256, target_date,
                     parent_classifier_parameters=None, situation_classifier_sha256=None):
    if (kind == 'BASE' or override.get('evidence_kind') != 'actual_completed_paired'
            or override.get('parent_sha256') != parent_sha256):
        raise ValueError('trailing_situation_override_authority_invalid')
    reference = override.get('selector_evidence_reference')
    if reference is not None:
        with _selector_reference(reference) as (report, policy, report_sha):
            return _checked_override(report, policy, report_sha, inline=False, market=market, kind=kind,
                parent_sha256=parent_sha256, target_date=target_date,
                parent_classifier_parameters=parent_classifier_parameters,
                situation_classifier_sha256=situation_classifier_sha256)
    return _checked_override(override.get('selector_report'), override.get('selector_policy'),
        override.get('selector_report_sha256'), inline=True, market=market, kind=kind,
        parent_sha256=parent_sha256, target_date=target_date,
        parent_classifier_parameters=parent_classifier_parameters,
        situation_classifier_sha256=situation_classifier_sha256)


def _checked_override(report, policy, report_sha, *, inline, market, kind, parent_sha256,
                      target_date, parent_classifier_parameters, situation_classifier_sha256):
    if not isinstance(report, dict) or not isinstance(policy, dict):
        raise ValueError('trailing_situation_selector_evidence_missing')
    selected_policy_env(policy, report, target_date=target_date, report_sha256=report_sha)
    if (policy.get('rollback_market_values_sha256') != parent_sha256
            or report.get('situation_scope') != {'market': market, 'situation_type': kind}
            or report.get('situation_classifier_sha256') != situation_classifier_sha256
            or (inline and report_sha != digest(report))):
        raise ValueError('trailing_situation_selector_scope_invalid')
    expected_m1 = parent_classifier_parameters or market_classifier_from_env({})
    if policy.get('classifier_parameters') != expected_m1:
        raise ValueError('trailing_situation_selector_m1_must_remain_fixed')
    return normalize_values(policy['market_values'][market])


def initial_bundle(parent_values, *, parent_sha256, source_date, target_date, classifier=None, overrides=None,
                   parent_classifier_parameters=None):
    if (date.fromisoformat(source_date).isoformat() != source_date
            or date.fromisoformat(target_date).isoformat() != target_date
            or source_date > target_date or source_date < '2026-06-05'):
        raise ValueError('trailing_situation_policy_dates_invalid')
    if set(parent_values) != set(START_MARKETS) or market_values_hash(parent_values, parent_classifier_parameters) != parent_sha256:
        raise ValueError("trailing_situation_parent_invalid")
    if classifier is not None:
        validate_classifier(classifier)
    normalized = {market: normalize_values(parent_values[market]) for market in START_MARKETS}
    cells = {}
    for market in START_MARKETS:
        for kind in TYPES:
            override = (overrides or {}).get(market + "|" + kind)
            if override is not None:
                # Economic overrides enter only via the existing selector's
                # exact parent/source-bound receipt. CF cannot grant approval.
                if classifier is None:
                    raise ValueError("trailing_situation_override_authority_invalid")
                values = _override_values(override, market=market, kind=kind,
                    parent_sha256=parent_sha256, target_date=target_date,
                    parent_classifier_parameters=parent_classifier_parameters,
                    situation_classifier_sha256=classifier['classifier_sha256'])
                status = 'qualified_candidate'
            else:
                values, status = dict(normalized[market]), "parent_carry"
            cells[market + "|" + kind] = {"values": values, "disposition": status,
                                        "parent_sha256": parent_sha256, "evidence": override}
    changed_markets = {key.split('|')[0] for key,cell in cells.items()
                       if cell['values'] != normalized[key.split('|')[0]]}
    if len(changed_markets)>1:
        raise ValueError('trailing_situation_one_market_canary_required')
    body = {"schema": SCHEMA, "source_date": source_date, "target_date": target_date,
            "parent_sha256": parent_sha256, "parent_values": normalized,
            "parent_classifier_parameters": parent_classifier_parameters,
            "classifier": classifier, "cells": cells, "runtime_effect": False,
            "allowed_runtime_apply": False,
            "evidence_kind": "actual_completed_paired_selected" if changed_markets else "approved_parent_equivalence"}
    return {**body, "policy_sha256": digest(body)}


def research_registered_grid(partitions, *, grid, candidates, parent_values,
                             parent_classifier_parameters, evaluation):
    """Train a registered finite entry-type grid on minimal replay results.

    Numeric replay is done once upstream. Types only partition that common
    cohort; neither holdout returns nor a second-best holdout candidate can
    choose thresholds. Economic candidates remain under the existing selector.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from .trailing_threshold_policy import market_type_at
    from .trailing_mechanical_policy import classifier_hash
    from src.engine.lifecycle.research_input_budget import Claim
    from contextlib import ExitStack
    if not grid:
        return {'schema':'main_trailing_situation_research_v1', 'status':'grid_not_registered',
                'classifier':None, 'cells':{}, 'allowed_runtime_apply':False}
    if not isinstance(grid, list) or not 1 <= len(grid) <= 16:
        raise ValueError('trailing_situation_registered_grid_budget_invalid')
    grid = [validate_classifier(dict(item)) for item in grid]
    if any(item['trained_through'] != 0 for item in grid):
        raise ValueError('trailing_situation_grid_must_be_untrained_hypotheses')
    if len({item['classifier_sha256'] for item in grid}) != len(grid):
        raise ValueError('trailing_situation_grid_duplicate')
    parent_m1 = classifier_hash(parent_classifier_parameters)
    eligible = {'incumbent':{m:normalize_values(parent_values[m]) for m in START_MARKETS}}
    rejected = []
    for name, item in candidates.items():
        values = item.get('market_values', item)
        config = item.get('classifier_parameters') if 'market_values' in item else None
        if classifier_hash(config) != parent_m1:
            rejected.append(name)
            continue
        eligible[name] = {m:normalize_values(values[m]) for m in START_MARKETS}
    context, rows, aliases = {}, {}, None
    with ExitStack() as retained:
        for part in partitions() if callable(partitions) else partitions:
            if aliases is None:
                aliases = part['candidate_aliases']
            if aliases != part['candidate_aliases'] or set(context) & set(part['population_context']):
                raise ValueError('trailing_situation_population_generation_invalid')
            retained.enter_context(Claim(len(part['population_context']) * (2048 + (len(eligible)+1)*256)))
            context.update(part['population_context'])
            if len(context) > 20000:
                raise ValueError('trailing_situation_partition_resume_required')
            for identity in part['common_ids']:
                rows[identity] = {name:part['minimal_results'][identity][aliases[name]] for name in eligible}
        strata = evaluation.get('strata') or {}
        training_kind = next((kind for kind in ('actual_completed', 'actual_entry_alternative_exit',
            'enter_pass_opportunity_cf') if (strata.get(kind) or {}).get('train_ids')), None)
        if training_kind is None:
            return {'schema':'main_trailing_situation_research_v1', 'status':'hold_sample_or_source',
                    'classifier':None, 'grid_sha256':digest(grid), 'cells':{}, 'allowed_runtime_apply':False}
        def classify(config, identities):
            labels = {}
            for identity in identities:
                row = context[identity]
                pin = pin_context(row.get('entry_context'), position_key=identity,
                                  entry_at=row['entry_at'], classifier=config)
                labels[identity] = (market_type_at(row['entry_at']), pin['situation_type'], pin['reason'])
            return labels
        def stats(identities, name, evidence):
            deltas, stress, adverse = [], [], []
            notional, pnl = 0., 0.
            days = {}
            for identity in identities:
                amount = number(context[identity]['buy_basis_krw'])
                candidate, incumbent = rows[identity][name], rows[identity]['incumbent']
                if amount is None or amount <= 0:
                    raise ValueError('trailing_situation_notional_unverified')
                reference = max(incumbent['modeled_net_pnl_krw'], candidate['actual_pnl_krw']) if evidence == 'actual_completed' else incumbent['modeled_net_pnl_krw']
                delta = candidate['modeled_net_pnl_krw'] - reference
                deltas.append(delta / amount * 100); pnl += delta; notional += amount
                worst = candidate['slippage_net_pnl_krw'][2] - reference
                stress.append(worst / amount * 100)
                if delta < 0:
                    adverse.append(identity)
                clock = number(context[identity].get('completion_at')) if evidence == 'actual_completed' else context[identity]['entry_at']
                if clock is not None:
                    day = datetime.fromtimestamp(clock, ZoneInfo('Asia/Seoul')).date().isoformat()
                    days.setdefault(day, []).append(worst / amount * 100)
            return dict(n=len(identities), equal_weight_avg_profit_pct=math.fsum(deltas)/len(deltas) if deltas else None,
                notional_weighted_ev_pct=100*pnl/notional if notional else None, paired_delta_net_krw=pnl if deltas else None,
                worst_paired_delta_pct=min(deltas) if deltas else None, worsened_ids=adverse,
                worst_slippage_ev_pct=math.fsum(stress)/len(stress) if stress else None,
                worst_slippage_min_day_ev_pct=min(math.fsum(v)/len(v) for v in days.values()) if days else None,
                verified_days=sorted(days), completion_clock_verified=len(identities)==sum(map(len, days.values())))
        train_ids = strata[training_kind]['train_ids']
        grid_scores, trained = {}, {}
        for config in grid:
            labels = classify(config, train_ids)
            selection, score = {}, 0.
            for market in START_MARKETS:
                allowed = [name for name, values in eligible.items() if all(
                    values[other] == eligible['incumbent'][other] for other in START_MARKETS if other != market)]
                for kind in TYPES:
                    ids = [i for i in train_ids if labels[i][:2] == (market,kind)]
                    metrics = {name:stats(ids,name,training_kind) for name in allowed}
                    winner = min(allowed, key=lambda name:(-(metrics[name]['equal_weight_avg_profit_pct'] or 0), name)) if ids and kind != 'BASE' else 'incumbent'
                    if (metrics[winner]['equal_weight_avg_profit_pct'] or 0) <= 0:
                        winner = 'incumbent'
                    selection[market+'|'+kind] = winner
                    score += max(0., metrics[winner]['paired_delta_net_krw'] or 0)
            grid_scores[config['classifier_sha256']] = score
            trained[config['classifier_sha256']] = selection
        winning_sha = min(grid_scores, key=lambda sha:(-grid_scores[sha],sha))
        hypothesis = next(item for item in grid if item['classifier_sha256']==winning_sha)
        frozen = {**hypothesis, 'trained_through':max(context[i]['observation_end_at'] for i in train_ids)}
        frozen['classifier_sha256'] = digest({k:v for k,v in frozen.items() if k!='classifier_sha256'})
        cells = {}
        for evidence, cohort in strata.items():
            # Train labels are explicitly in-sample hypotheses; holdout uses
            # the final trained clock and original causal entry features.
            training_labels = classify(hypothesis, cohort['train_ids'])
            holdout_labels = classify(frozen, cohort['holdout_ids'])
            for market in START_MARKETS:
                for kind in TYPES:
                    key = market+'|'+kind
                    winner = trained[winning_sha][key]
                    train = [i for i in cohort['train_ids'] if training_labels[i][:2]==(market,kind)]
                    holdout = [i for i in cohort['holdout_ids'] if holdout_labels[i][:2]==(market,kind)]
                    tr, ho = stats(train,winner,evidence), stats(holdout,winner,evidence)
                    compatible = all(context[i].get('operating_ai_required') is True
                        and validate_pin(context[i].get('situation_pin'),i)
                        and context[i]['situation_pin']['classifier_sha256']==frozen['classifier_sha256']
                        and context[i]['situation_pin']['situation_type']==kind for i in train+holdout)
                    qualified = (evidence=='actual_completed' and winner!='incumbent'
                        and len(set(tr['verified_days']+ho['verified_days']))>=7 and tr['n']>=30 and ho['n']>=10
                        and len(ho['verified_days'])>=2 and tr['completion_clock_verified'] and ho['completion_clock_verified']
                        and all((x or 0)>0 for x in (tr['equal_weight_avg_profit_pct'],ho['equal_weight_avg_profit_pct'],
                            ho['worst_slippage_ev_pct'],ho['worst_slippage_min_day_ev_pct']))
                        and not tr['worsened_ids'] and not ho['worsened_ids'] and compatible)
                    cells[evidence+'|'+key] = {'train_selected_candidate':winner, 'train':tr, 'holdout':ho,
                        'candidate_values':eligible[winner][market], 'effective_initial_values':eligible['incumbent'][market],
                        'disposition':'research_candidate_requires_existing_selector_review' if qualified else 'parent_carry',
                        'parent_values':eligible['incumbent'][market], 'holdout_reselected':False,
                        'operating_ai_type_input_compatible':compatible,
                        'training_evidence_kind':training_kind, 'allowed_runtime_apply':False}
        body = dict(schema='main_trailing_situation_research_v1',status='research_complete',
            classifier=frozen, grid_sha256=digest(grid), train_grid_scores=grid_scores,
            train_winner_hypothesis_sha256=winning_sha, cells=cells,
            fixed_m1_classifier_sha256=parent_m1, rejected_m1_candidates=rejected,
            input_common_ids_sha256=digest(sorted(rows)), allowed_runtime_apply=False)
        return {**body,'artifact_sha256':digest(body)}


@dataclass(frozen=True)
class PreparedTrailingPolicy:
    policy_sha256: str
    parent_sha256: str
    classifier_sha256: str | None
    target_date: str
    cells: object

    @classmethod
    def prepare(cls, policy, *, target_date, parent_sha256):
        if (policy.get("schema") != SCHEMA or policy.get("target_date") != target_date
            or policy.get("parent_sha256") != parent_sha256
            or policy.get("policy_sha256") != digest({k: v for k, v in policy.items() if k != "policy_sha256"})
            or set(policy.get("cells", {})) != {m + "|" + kind for m in START_MARKETS for kind in TYPES}):
            raise ValueError("trailing_situation_policy_invalid")
        if policy.get("classifier") is not None:
            validate_classifier(policy["classifier"])
        expected = initial_bundle(policy['parent_values'], parent_sha256=parent_sha256,
            source_date=policy['source_date'], target_date=target_date, classifier=policy.get('classifier'),
            parent_classifier_parameters=policy.get('parent_classifier_parameters'),
            overrides={key: cell['evidence'] for key, cell in policy['cells'].items() if cell.get('evidence') is not None})
        if expected != policy:
            raise ValueError('trailing_situation_policy_parent_or_authority_invalid')
        values = {key: MappingProxyType(normalize_values(cell["values"])) for key, cell in policy["cells"].items()}
        return cls(policy["policy_sha256"], parent_sha256, (policy.get("classifier") or {}).get("classifier_sha256"),
                   target_date, MappingProxyType(values))

    def effective(self, market, pin, *, position_key, target_date):
        if target_date != self.target_date:
            raise ValueError("trailing_situation_policy_date_invalid")
        # PreparedPin is validated at position hydration, once per generation.
        kind = pin.situation_type if (isinstance(pin, PreparedPin) and pin.position_key == position_key
              and pin.classifier_sha256 == self.classifier_sha256) else 'BASE'
        return self.cells[market + "|" + kind]


@dataclass(frozen=True)
class PreparedPin:
    position_key: str
    situation_type: str
    classifier_sha256: str | None
    classification_origin_hash: str

    @classmethod
    def prepare(cls, pin, position_key):
        if not validate_pin(pin, position_key):
            raise ValueError('trailing_situation_pin_invalid')
        return cls(position_key, pin['situation_type'], pin['classifier_sha256'], pin['classification_origin_hash'])


_PREPARED = None
_CLASSIFIER = None
_PIN_CACHE = OrderedDict()
ENV_KEY = 'KORSTOCKSCAN_TRAILING_SITUATION_POLICY_JSON'


def prepare_runtime(*, env, parent_sha256, target_date):
    global _PREPARED, _CLASSIFIER
    _PREPARED = _CLASSIFIER = None
    _PIN_CACHE.clear()
    raw = env.get(ENV_KEY)
    if not raw:
        return {'status': 'parent_only'}
    if len(raw.encode()) > 64 * 1024:
        raise ValueError('trailing_situation_runtime_budget_invalid')
    policy = json.loads(raw)
    _PREPARED = PreparedTrailingPolicy.prepare(policy, target_date=target_date, parent_sha256=parent_sha256)
    _CLASSIFIER = policy.get('classifier')
    return {'status': 'prepared', 'policy_sha256': _PREPARED.policy_sha256}


def runtime_values(stock, *, position_key, market, target_date, parent_values, restore=None, persist=None):
    """Only prepared maps on warm evaluation; position hydration writes once."""
    if _PREPARED is None or _PREPARED.target_date != target_date:
        return parent_values
    original_pin = stock.get('trailing_situation_pin') or {}
    cache_key = (position_key, original_pin.get('classification_origin_hash'), _PREPARED.policy_sha256)
    cached = _PIN_CACHE.get(cache_key)
    if not isinstance(cached, PreparedPin) or cached.position_key != position_key:
        pin = stock.get('trailing_situation_pin')
        if not validate_pin(pin, position_key) and restore is not None:
            pin = restore()
        if not validate_pin(pin, position_key):
            context = stock.get('trailing_entry_context')
            anchor = number((context or {}).get('anchor_at')) if isinstance(context, dict) else None
            # Existing holdings never classify from a post-entry quote.
            pin = pin_context(context if anchor is not None else None, position_key=position_key,
                              entry_at=anchor or 0, classifier=_CLASSIFIER)
            if persist is not None and persist(pin) is not True:
                pin = pin_context(None, position_key=position_key, entry_at=anchor or 0)
                stock['trailing_situation_persist_gap'] = True
        cached = PreparedPin.prepare(pin, position_key)
        stock['trailing_situation_pin'] = pin
        cache_key = (position_key, pin['classification_origin_hash'], _PREPARED.policy_sha256)
        _PIN_CACHE[cache_key] = cached
        _PIN_CACHE.move_to_end(cache_key)
        while len(_PIN_CACHE) > 512:
            _PIN_CACHE.popitem(last=False)
    stock['effective_trailing_policy_sha256'] = _PREPARED.policy_sha256
    return _PREPARED.effective(market, cached, position_key=position_key, target_date=target_date)
