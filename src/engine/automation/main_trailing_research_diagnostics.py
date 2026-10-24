"""Source-bound exit research diagnostics, without selection/order authority.

The automation package owns this report consumer. Existing replay/selector
metrics retain their realized-profit floor. Pure modeled exit differences and
incomplete observed price paths are separately labeled diagnostics.
"""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.scalping.main_stop_replay import cost_known_epoch
from src.engine.scalping.pre_submit_delay_initial_policy import digest, number
from src.engine.scalping.trailing_threshold_policy import market_type_at
from src.engine.scalping.universal_trailing_replay import quote_source_digest, expand_ws, _route_depths
from .main_trailing_all_scope_research import _sealed, _source_path, code_contract

SCHEMA = 'main_trailing_execution_diagnostics_v1'


def _verified_touch(event, position, entry, cutoff):
    at, known = number(event.get('event_at')), number(event.get('known_at'))
    age = number(event.get('max_quote_age_sec'))
    route, item, epoch = (event.get(k) for k in ('route', 'item', 'transport_epoch'))
    market = market_type_at(known) if known is not None else None
    expected_route = (position.get('routes_by_market') or {}).get(market, position.get('route'))
    expected_item = (position.get('items_by_market') or {}).get(market, position.get('item'))
    if (at is None or known is None or age is None or not 0 < age <= .7
            or at < entry or at > known or known > cutoff or known-at > age
            or route != expected_route or item != expected_item
            or not item or type(epoch) is not int or epoch < 0
            or type(event.get('sequence')) is not int or event['sequence'] <= 0
            or event.get('coverage_complete') is not True
            or event.get('source_kind') != 'tick_depth'
            or event.get('source_sha256') != quote_source_digest(event)
            or not isinstance(event.get('ws_data'), dict)
            or event.get('quote_snapshot_sha256') != digest(event['ws_data'])):
        return False
    try:
        ws = expand_ws(event['ws_data'])
        if (ws.get('market_data_transport_epoch') != epoch
                or (ws.get('last_realtime_type_item') or {}).get('0D') != item
                or str((ws.get('last_realtime_type_market_route') or {}).get('0D') or '').upper() != str(route).upper()):
            return False
        latest = max(_route_depths(ws, route, item, epoch),
                     key=lambda r:number(r.get('received_at_ms')) or 0, default={})
        bid = (latest.get('bid_levels') or [{}])[0]
        ask = (latest.get('ask_levels') or [{}])[0]
        received = number(latest.get('received_at_ms'))
        return (received is not None and 0 <= known-received/1000 <= age
                and latest.get('route_sequence') == event['sequence']
                and number(bid.get('price')) == number(event.get('bid'))
                and number(ask.get('price')) == number(event.get('ask'))
                and number(bid.get('quantity')) == number(event.get('bid_qty'))
                and number(event.get('bid')) is not None and 0 < number(event['bid']) <= number(event['ask'])
                and number(event.get('bid_qty')) is not None and number(event['bid_qty']) >= 0)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False


def _observation(position, events, parent, cutoff):
    """Describe verified observed quotes; never assert missing path outcomes."""
    qty = number(position.get('qty'))
    basis = number(position.get('buy_basis_krw'))
    entry = number(position.get('entry_at'))
    model = position.get('cost_model') or {}
    cost, rate = number(model.get('buy_cost_krw')), number(model.get('sell_cost_rate'))
    known = cost_known_epoch(model.get('known_at'))
    usable = (qty is not None and qty > 0 and qty.is_integer() and basis is not None and basis > 0
              and entry is not None and entry > 0 and known is not None and known <= entry
              and cost is not None and cost >= 0 and rate is not None and 0 <= rate < .05
              and bool(model.get('source_sha256')))
    counts, reasons = Counter(), Counter()
    peak_net, bid_net = None, None
    first, last, previous, reached = None, None, None, False
    lifecycle_changed = False
    for event in events:
        counts['events'] += 1
        if not isinstance(event, dict):
            reasons['event_not_object'] += 1
            continue
        if event.get('kind') == 'ADD':
            lifecycle_changed = True
            reasons['add_observation_requires_separate_generation'] += 1
            continue
        if event.get('kind') != 'QUOTE':
            continue
        counts['quote_events'] += 1
        available = number(event.get('known_at'))
        if available is not None and available > cutoff:
            reasons['quote_after_cutoff'] += 1
            continue
        if entry is None or not _verified_touch(event, position, entry, cutoff):
            reasons['quote_source_or_entry_unverified'] += 1
            continue
        if previous is not None and available < previous:
            reasons['quote_clock_regression'] += 1
            continue
        if previous is not None and available - previous > 2:
            counts['observed_gaps_over_two_seconds'] += 1
        previous = available
        first = available if first is None else first
        last = available
        counts['source_verified_observed_quotes'] += 1
        if not usable or lifecycle_changed:
            continue
        bid, peak = number(event.get('bid')), number(event.get('trade_peak_price'))
        if bid is None or bid <= 0 or peak is None or peak <= 0:
            reasons['observed_price_missing'] += 1
            continue
        current_net = round(100 * ((bid * qty * (1-rate) - basis-cost) / basis), 2)
        current_peak = round(100 * ((peak * qty * (1-rate) - basis-cost) / basis), 2)
        bid_net = current_net if bid_net is None else max(bid_net, current_net)
        peak_net = current_peak if peak_net is None else max(peak_net, current_peak)
        market = market_type_at(available)
        values = parent.get(market)
        if values and current_peak >= values['SCALP_TRAILING_START_PCT']:
            reached = True
    state = ('observed_start_reached' if reached else 'observed_start_not_reached') if peak_net is not None else 'unassessable'
    return dict(state=state, counts=dict(counts), reasons=dict(reasons),
                first_observed_at=first, last_observed_at=last,
                observation_delay_sec=first-entry if first is not None and entry is not None else None,
                maximum_observed_peak_net_pct=peak_net, maximum_observed_bid_net_pct=bid_net,
                complete_lifecycle_verified=False, actual_profit_verified=False,
                model_cost_usable=bool(usable), lifecycle_changed=lifecycle_changed)


def build(manifest_path, *, input_root, report_path):
    """Consume sealed input/results; bounded cost evidence, no operational files."""
    from src.engine.lifecycle.research_disk_budget import use
    output = Path(report_path).resolve().parent
    with use(output), storage.index(output / 'scratch') as allocated_index:
        return _build(manifest_path,input_root=input_root,report_path=report_path,allocated_index=allocated_index)


def _build(manifest_path, *, input_root, report_path, allocated_index):
    root, report_path = Path(input_root).resolve(), Path(report_path).resolve()
    output = report_path.parent
    before = byte_generation(report_path)
    manifest_before = byte_generation(Path(manifest_path))
    manifest, report = _sealed(Path(manifest_path)), _sealed(report_path)
    if (report.get('status') != 'complete'
            or report.get('schema') != 'main_all_scope_exit_research_v2'
            or report.get('code_contract_sha256') != code_contract()
            or report.get('input_manifest_path') != str(Path(manifest_path).resolve())
            or report.get('input_manifest_generation') != manifest_before
            or report.get('source_date') != manifest.get('source_date')
            or report.get('target_date') != manifest.get('target_date')
            or report.get('allowed_runtime_apply') is not False):
        raise ValueError('trailing_diagnostic_report_binding_invalid')
    cohort_counts, statuses = Counter(), Counter()
    comparisons = defaultdict(lambda: dict(n=0, delta=0., notional=0., percent=0.))
    result_ids = set()
    allocated_counts = Counter()
    allocated_comparisons = defaultdict(lambda: dict(n=0, delta=0., notional=0.))
    from src.engine.lifecycle.holding_research_cost import valid_annotation
    for reference in storage.iter_tree(output, report['partition_results_ref']):
        checkpoint = _sealed(_source_path(output, reference['path']))
        if checkpoint['artifact_sha256'] != reference['artifact_sha256']:
            raise ValueError('trailing_diagnostic_checkpoint_binding_invalid')
        aliases = checkpoint['candidate_aliases']
        parent_sha = aliases['incumbent']
        for row in storage.iter_tree(output, checkpoint['result_records_ref']):
            row = storage.expand_outcomes(output, row)
            identity, context = row['identity'], row['context']
            if identity in result_ids:
                raise ValueError('trailing_diagnostic_duplicate_identity')
            result_ids.add(identity)
            kind = context['evidence_kind']
            cohort_counts[kind] += 1
            baseline = row['outcomes'][parent_sha]
            statuses[(kind, baseline['status'], baseline.get('reason'))] += 1
            basis = number(context.get('buy_basis_krw'))
            base_net = number(baseline.get('modeled_net_pnl_krw'))
            allocated = context.get('holding_research_cost')
            if allocated is not None and not valid_annotation(allocated,dict(context,position_key=identity)):
                raise ValueError('holding_research_cost_annotation_invalid')
            if allocated is not None and kind == 'actual_completed':
                storage.put(allocated_index,identity,dict(identity=identity,**allocated))
                allocated_counts[allocated['status']] += 1
            for name, sha in aliases.items():
                outcome = row['outcomes'][sha]
                net = number(outcome.get('modeled_net_pnl_krw'))
                if (basis is None or basis <= 0 or base_net is None or net is None
                        or baseline.get('status') != 'modeled_full_exit'
                        or outcome.get('status') != 'modeled_full_exit'):
                    continue
                if (kind == 'actual_entry_alternative_exit' and allocated is not None
                        and allocated.get('status') == 'research_cost_allocated'):
                    reference = number(allocated.get('allocated_net_pnl_krw'))
                    total_basis = number(allocated.get('buy_basis_krw'))
                    known = cost_known_epoch(allocated.get('cost_available_at'))
                    if reference is None or total_basis is None or total_basis <= 0 or known is None or known > manifest['as_of']:
                        raise ValueError('holding_research_cost_annotation_economics_invalid')
                    diagnostic = allocated_comparisons[name]
                    diagnostic['n'] += 1
                    diagnostic['delta'] += net-max(base_net,reference)
                    diagnostic['notional'] += total_basis
                metric = comparisons[(kind, name)]
                metric['n'] += 1
                metric['delta'] += net-base_net
                metric['percent'] += 100*(net-base_net)/basis
                metric['notional'] += basis
    observations, input_ids = [], set()
    parent = manifest['approved_parent_receipt']['market_values']
    for reference in storage.iter_tree(root, manifest['partitions_ref']):
        partition = _sealed(_source_path(root, reference['path']), reference['artifact_sha256'])
        for position in partition['positions']:
            identity = position['position_key']
            if identity in input_ids:
                raise ValueError('trailing_diagnostic_duplicate_input')
            input_ids.add(identity)
            if position['evidence_kind'] == 'actual_entry_alternative_exit':
                continue
            observation = _observation(position, storage.iter_tree(root, partition['paths'][identity]),
                                       parent, manifest['as_of'])
            observations.append(dict(identity=identity, symbol=position.get('symbol'),
                evidence_kind=position['evidence_kind'], automatic_management_allowed=position.get('automatic_management_allowed'),
                route=position.get('route'), **observation))
    if input_ids != result_ids:
        raise ValueError('trailing_diagnostic_population_mismatch')
    observed = Counter((row['evidence_kind'], row['state']) for row in observations)
    metrics = []
    for (kind, name), value in sorted(comparisons.items()):
        metrics.append(dict(evidence_kind=kind, candidate=name, paired_count=value['n'],
            exit_only_paired_delta_net_krw=value['delta'],
            exit_only_equal_weight_delta_pct=value['percent']/value['n'],
            exit_only_notional_weighted_delta_pct=100*value['delta']/value['notional']))
    if (byte_generation(report_path) != before or byte_generation(Path(manifest_path)) != manifest_before
            or code_contract() != report['code_contract_sha256']):
        raise ValueError('trailing_diagnostic_input_changed')
    body = dict(schema=SCHEMA, source_date=manifest['source_date'], target_date=manifest['target_date'],
        diagnostic_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        report_path=str(report_path), report_generation=before, input_manifest_path=str(Path(manifest_path).resolve()),
        input_manifest_generation=manifest_before, population_count=len(result_ids), cohort_counts=dict(cohort_counts),
        incumbent_outcomes=[dict(evidence_kind=k[0], status=k[1], reason=k[2], count=n)
                            for k,n in sorted(statuses.items(), key=lambda x:str(x[0]))],
        observation_counts=[dict(evidence_kind=k[0], state=k[1], count=n) for k,n in sorted(observed.items())],
        position_observations=observations, exit_only_comparisons=metrics,
        holding_allocated_cost_rows_ref=storage.write_tree(output,(value for _,value,_ in storage.records(allocated_index))),
        holding_allocated_cost_status_counts=dict(allocated_counts),
        holding_allocated_cost_comparisons=[dict(candidate=name,paired_count=value['n'],
            candidate_minus_max_parent_allocated_net_krw=value['delta'],
            notional_weighted_delta_pct=100*value['delta']/value['notional'],
            economics_scope='main_holding_exit_research_only',actual_execution_cost=False,
            actual_pnl_krw=None,selector_eligible=False,allowed_runtime_apply=False)
            for name,value in sorted(allocated_comparisons.items())],
        economic_comparison_state='paired_modeled' if metrics else 'source_or_execution_insufficient',
        selector_metrics_redefined=False, actual_profit_verified=False, runtime_effect=False, allowed_runtime_apply=False,
        metric_contract=dict(metric_role='funnel_count', decision_authority='report_only',
            window_policy='frozen_source_window', sample_floor='existing_family_contract',
            primary_decision_metric='existing_selector_unchanged',
            source_quality_gate='sealed_input_and_result_identity',
            forbidden_uses=['runtime_apply','actual_pnl','source_gap_as_zero','parent_carry_as_uplift']))
    body['artifact_sha256'] = digest(body)
    return body
