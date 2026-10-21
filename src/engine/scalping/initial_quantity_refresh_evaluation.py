"""Versioned quantity refresh: causal execution and train-only selection.

Owns offline quantity evaluation, never price discovery, orders or pointers.
The same comparison cost model is applied to both arms; realized PnL supplies
winner weights only. Missing sources are excluded, not incumbent earnings.
Execution evidence retains v2; new selection uses all-trade EV in v3.
"""
from __future__ import annotations
from collections import Counter, defaultdict, OrderedDict
from datetime import timedelta
import math
from src.engine.scalping.initial_quantity_type import finite_number, kst_timestamp
from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule
from src.engine.scalping.entry_split_order_plan import build_initial_quantity_type_legs

VERSION = 'initial_quantity_execution_cost_split_v2'
SELECTION_VERSION = 'initial_quantity_all_trade_ev_selection_v3'
VALID_OUTCOMES = {'paired', 'partial_unfilled', 'modeled_no_fill'}
EXECUTION_READERS = ('initial_quantity_refresh_evaluation.py', 'initial_quantity_timeout_research.py',
                     'initial_quantity_policy.py', 'initial_quantity_cap_observation.py',
                     'initial_quantity_timeout.py', 'entry_split_order_plan.py')
_VERIFIED_EXECUTIONS = OrderedDict()


def economic_sample_status(report):
    """Separate absent eligible trades from evidence rejected by readers."""
    if report['trades']:
        return 'cost_eligible'
    excluded = report['census']['excluded']
    costs = {'terminal_cost_or_quantity_missing', 'actual_cost_identity_or_amount_invalid',
             'actual_cost_provenance_missing', 'terminal_cost_contract_mismatch'}
    if any(excluded.get(key, 0) for key in costs):
        return 'cost_missing'
    benign = {'not_completed', 'other_strategy', 'other_custody', 'scale_in_position',
              'before_refresh_start', 'duplicate_fact', 'date_outside_baseline_or_as_of'}
    return 'source_gap' if any(n for key,n in excluded.items() if key not in benign) else 'valid_empty'


def _execution_key(trade,path,source,grid):
    from pathlib import Path
    import hashlib
    from src.engine.scalping.initial_quantity_source_cache import encode
    from src.engine.scalping.initial_quantity_policy import _digest
    readers={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in EXECUTION_READERS}
    readers['trading/market/execution_venue.py']=hashlib.sha256(
        (Path(__file__).resolve().parents[2]/'trading/market/execution_venue.py').read_bytes()).hexdigest()
    return _digest(dict(trade=trade,path=encode(path),source=source,grid=grid,readers=readers))


def modeled_parent(row):
    value = row.get('modeled_parent_net_pnl_krw')
    return value if finite_number(value) is not None else row['actual_net_pnl_krw']


def _selection_version(value):
    version = SELECTION_VERSION if value is None else value
    if version not in {VERSION, SELECTION_VERSION}:
        raise ValueError('refresh_selection_algorithm_invalid')
    return version


def _comparison_parent(row, value):
    parent = finite_number(value.get('modeled_parent_net_pnl_krw'))
    return parent if parent is not None else finite_number(row.get('modeled_parent_net_pnl_krw'))


def _cap_delta_pct(row, value):
    """Use the original trade notional, never the candidate filled amount."""
    notional = finite_number(row.get('original_notional_krw'))
    if notional is None:
        quantity, price = finite_number(row.get('buy_qty')), finite_number(row.get('buy_price'))
        notional = quantity * price if quantity and price else None
    if notional is not None and notional > 0:
        parent = _comparison_parent(row, value)
        if parent is None:
            return None
        return 100 * (value['candidate_net_pnl_krw'] - parent) / notional
    parent_pct = finite_number(value.get('parent_net_pct_on_parent_notional'))
    if parent_pct is not None:
        return value['candidate_net_pct_on_parent_notional'] - parent_pct
    return None


def cap_selection(rows, parent_mode, minimum_count, *, evaluation_algorithm=None):
    """Freeze one train winner before looking at any holdout outcomes."""
    from src.engine.scalping.initial_quantity_policy import _CAP_MODES, _digest
    version = _selection_version(evaluation_algorithm)
    legacy = version == VERSION
    dates = sorted({row['entry_date'] for row in rows})
    if not dates:
        return parent_mode, {}
    holdout = dates[-1]
    train = [row for row in rows if row['entry_date'] < holdout]
    test = [row for row in rows if row['entry_date'] == holdout]
    metrics, ranks = {}, []
    for mode in _CAP_MODES:
        def measure(cohort):
            valid = [r for r in cohort if (r.get('cap_candidates') or {}).get(mode, {}).get('status') in VALID_OUTCOMES
                     and (legacy or _comparison_parent(r, r['cap_candidates'][mode]) is not None)]
            values = [r['cap_candidates'][mode] for r in valid]
            def parent_net(row, value):
                return value.get('modeled_parent_net_pnl_krw', modeled_parent(row)) if legacy else _comparison_parent(row, value)
            delta = sum(v['candidate_net_pnl_krw'] - parent_net(r, v) for r,v in zip(valid,values))
            winners = [(r,v) for r,v in zip(valid,values) if r['actual_net_pnl_krw'] > 0 and r['actual_profit_rate'] > 0]
            weight = sum(r['actual_net_pnl_krw'] for r,v in winners)
            score = sum(r['actual_net_pnl_krw'] * v['candidate_net_pct_on_parent_notional'] for r,v in winners)/weight if weight else None
            parent_score = sum(r['actual_net_pnl_krw'] * v.get('parent_net_pct_on_parent_notional',r['actual_profit_rate']) for r,v in winners)/weight if weight else None
            if not legacy:
                winner_deltas = [_cap_delta_pct(row, value) for row, value in winners]
                parent_score = (score - sum(row['actual_net_pnl_krw'] * change for (row, value), change in zip(winners, winner_deltas)) / weight
                                if weight and all(change is not None for change in winner_deltas) else None)
            daily = defaultdict(float)
            for r,v in zip(valid,values):
                daily[r['entry_date']] += v['candidate_net_pnl_krw'] - parent_net(r, v)
            result = dict(count=len(valid), coverage=len(valid)/len(cohort) if cohort else 0., delta=delta, score=score, parent_score=parent_score, daily=dict(daily), candidate_net=sum(v['candidate_net_pnl_krw'] for v in values))
            if not legacy:
                # Both arms use each original trade's notional. The paired
                # parent amount is modeled with the same comparison costs.
                deltas = [_cap_delta_pct(row, value) for row, value in zip(valid, values)]
                result['mean_delta_pct'] = sum(deltas) / len(deltas) if deltas and all(value is not None for value in deltas) else None
            return result
        a,b = measure(train), measure(test)
        score_ok = (a['score'] is not None and a['parent_score'] is not None and a['score'] > a['parent_score'] + 1e-6) if legacy else a['mean_delta_pct'] is not None and a['mean_delta_pct'] > 0
        eligible = (len(dates) >= 3 and a['count'] >= minimum_count and a['coverage'] >= .8 and a['delta'] > 0
                    and score_ok and a['daily'] and min(a['daily'].values()) >= -.001)
        metrics[mode] = dict(train=a, holdout=b, train_eligible=bool(eligible), selection_eligible=False,
                             paired_count=a['count']+b['count'], delta_net_pnl_krw=a['delta']+b['delta'],
                             winner_weighted_net_pct=a['score'], candidate_net_pnl_krw=a['candidate_net']+b['candidate_net'],
                             train_paired_count=a['count'],holdout_paired_count=b['count'],holdout_date=holdout,
                             coverage=(a['count']+b['count'])/len(rows),holdout_coverage=b['coverage'])
        if eligible and mode != parent_mode:
            ranks.append((a['score'] if legacy else a['mean_delta_pct'], a['delta'], -list(_CAP_MODES).index(mode), mode))
    winner = max(ranks)[-1] if ranks else parent_mode
    if ranks:
        metrics[winner]['train_selected_candidate_sha256'] = _digest({'mode':winner, 'version':version})
        b=metrics[winner]['holdout']
        metrics[winner]['selection_eligible'] = (b['count'] > 0 and b['coverage'] >= .8 and b['delta'] >= 0
            and (legacy or b['mean_delta_pct'] is not None and b['mean_delta_pct'] >= 0))
    return (winner if ranks and metrics[winner]['selection_eligible'] else parent_mode), metrics


def execution_case(trade, path, source, *, mode, shape, horizon, reserve=5):
    """Replay a single executable cap/shape/T tuple without future price choice."""
    from src.engine.scalping.initial_quantity_policy import (_cap_target_qty, _costed_fixed_exit_pnl, _SHAPES, _timestamp, canonical_epoch, _capture_source_issue)
    from src.engine.scalping.initial_quantity_timeout_research import (_unique_fills, _decision_before_fill, _order_start_before_fill, _prices, _fill_latest_possible_at)
    if path.get('source_gap'):
        return {'status':'source_gap', 'reason':'capture_window_gap'}
    fills=_unique_fills(path)
    if (not fills or any(type(r.get('qty')) is not int or r['qty']<=0 or finite_number(r.get('price')) is None or r['price']<=0 for r in fills)
        or sum(r['qty'] for r in fills)!=trade['buy_qty']):
        return {'status':'source_gap','reason':'fill_ledger_missing_or_conflicting'}
    first=fills[0]; decision=_decision_before_fill(path,first)
    start=_order_start_before_fill(path,first,decision) if decision else None
    if not start or start['source'] not in {'initial_quantity_bundle_order_start_at','entry_cancel_wait_submission_context_frozen_at'}:
        return {'status':'source_gap','reason':'frozen_order_start_missing'}
    if start['source']=='entry_cancel_wait_submission_context_frozen_at' and start.get('frozen_context_valid') is not True:
        return {'status':'source_gap','reason':'frozen_submission_context_invalid'}
    context=source.get('context') if isinstance(source,dict) else None
    if not isinstance(context,dict):
        return {'status':'source_gap','reason':'target_quantity_context_missing'}
    target=context.get('actual_effective_qty') if mode=='parent_5stage' else _cap_target_qty(context,mode)
    if type(target) is not int or target<1 or shape not in _SHAPES:
        return {'status':'source_gap','reason':'target_quantity_invalid'}
    # Incumbent actual fills remain a control. Known sampling/clock loss must
    # never become counterfactual no-fill or zero economics.
    if not (shape=='parent' and horizon is None and mode=='parent_5stage'):
        observed_horizon = (horizon if type(horizon) is int else
            start.get('total_wait_sec') if shape != 'parent' and horizon is None else 1200)
        issue=_capture_source_issue(source, horizon_seconds=observed_horizon,
                                    order_start_epoch=start['at'].timestamp())
        if issue:
            return {'status':'source_gap','reason':issue}
    if shape=='parent' and horizon is None:
        # Existing parallel/probe profiles retain their actual fill-price
        # sequence. They must not be silently modeled as a new single leg.
        if mode=='parent_5stage':
            rate=trade['comparison_cost_rate'];notional=trade['buy_qty']*trade['buy_price']
            net=_costed_fixed_exit_pnl([(trade['buy_qty'],trade['buy_price'])],trade['sell_price'],rate)
            return dict(status='paired' if trade['buy_qty']==target else 'partial_unfilled',target_qty=target,modeled_filled_qty=trade['buy_qty'],unfilled_qty=max(0,target-trade['buy_qty']),candidate_net_pnl_krw=net,modeled_parent_net_pnl_krw=net,candidate_net_pct_on_parent_notional=100*net/notional,parent_net_pct_on_parent_notional=100*net/notional,cost_model='canonical_sell_notional_only_v1',observation_coverage='actual_fills',verified_price_cross_count=0,cancel_confirmation_model='incumbent_actual_execution')
        from src.engine.scalping.initial_quantity_policy import _cap_candidate_trade
        value=_cap_candidate_trade({**trade,'realized_net_pnl_krw':None},source,mode,trade['comparison_cost_rate'])
        if value.get('status') not in VALID_OUTCOMES:return {'status':'source_gap','reason':value.get('status')}
        value.pop('actual_net_pnl_krw',None)
        return {**value,'parent_net_pct_on_parent_notional':100*value['modeled_parent_net_pnl_krw']/(trade['buy_price']*trade['buy_qty']),
                'verified_price_cross_count':0,'observation_coverage':'actual_fill_prefix_and_sampled_ticks'}
    # T is frozen at submission, never read from today's environment.
    if horizon is None:
        horizon=start.get('total_wait_sec')
    if type(horizon) is not int or not 1<=horizon<=1200:
        return {'status':'source_gap','reason':'frozen_timeout_missing'}
    from src.engine.scalping.initial_quantity_cap_observation import quote_route_binding
    depth=context.get('ask_depth_source') or {}
    binding=quote_route_binding(depth.get('item'),depth.get('market_route'),legacy=True)
    route=binding['order_route'] if binding else first.get('route', first.get('venue'))
    fill_venues=binding['fill_venues'] if binding else (route,)
    probe=bool(start.get('probe_applied'))
    if route not in {'KRX','NXT','SOR'}:
        return {'status':'source_gap','reason':'route_missing'}
    if shape=='parent':
        quantities=[target]
        if probe and target>1:
            quantities=[1,target-1]
    else:
        try:
            quantities=[r['qty'] for r in build_initial_quantity_type_legs(total_qty=target,selected_shape=shape,probe_first=probe,route=route)]
        except ValueError:
            return {'status':'source_gap','reason':'quantity_not_splittable'}
    try:
        schedule=build_bundle_timeout_schedule(quantity_type=trade['quantity_type'],policy_sha256='0'*64,decision_at=decision['at'].isoformat(),order_start_at=start['at'].isoformat(),total_wait_sec=horizon,leg_count=len(quantities),cancel_confirm_reserve_sec=reserve)
    except ValueError:
        return {'status':'source_gap','reason':'timeout_slot_invalid'}
    from src.trading.order.tick_utils import get_tick_size
    anchor=first['price']; exit_at=_timestamp(trade['exit_at'])
    if not float(anchor).is_integer() or int(anchor)%get_tick_size(anchor):
        return {'status':'source_gap','reason':'anchor_tick_invalid'}
    if not exit_at or first['at']>=exit_at:
        return {'status':'source_gap','reason':'exit_clock_invalid'}
    prices=([anchor]*len(quantities) if shape=='parent' else _prices(int(anchor),shape)[:len(quantities)])
    depth=context.get('ask_depth_source') or {}; epoch=canonical_epoch(depth.get('transport_epoch'))
    depth_valid=bool(depth.get('source_type')=='ws_0D_bound_snapshot' and epoch is not None
                     and binding is not None and depth.get('item')
                     and finite_number(depth.get('observed_epoch')) is not None
                     and 0<=start['at'].timestamp()-depth['observed_epoch']<=120)
    if depth_valid:
        levels=depth.get('levels')
        if (not isinstance(levels,list) or not levels or any(not isinstance(r,dict) or type(r.get('price_krw')) is not int or r['price_krw']<=0 or r['price_krw']%get_tick_size(r['price_krw']) or type(r.get('quantity')) is not int or r['quantity']<0 for r in levels)
            or any(b['price_krw']<=a['price_krw'] for a,b in zip(levels,levels[1:]))):
            return {'status':'source_gap','reason':'depth_levels_invalid'}
    if target>trade['buy_qty'] and not depth_valid:
        return {'status':'source_gap','reason':'expansion_depth_missing'}
    identity=(source.get('attempt_id'),source.get('plan_sha256'))
    if not all(identity):
        return {'status':'source_gap','reason':'attempt_plan_missing'}
    decisions=decision.get('fields') or {}
    if (str(decisions.get('entry_submit_attempt_id') or ''),str(decisions.get('entry_execution_sizing_plan_sha256') or ''))!=identity:
        return {'status':'source_gap','reason':'decision_attempt_plan_changed'}
    ticks={}
    for tick in source.get('following_ticks') or []:
        if ((tick.get('attempt_id'),tick.get('plan_sha256'))!=identity or tick.get('depth_item')!=depth.get('item')
            or tick.get('market_route')!=depth.get('market_route') or canonical_epoch(tick.get('transport_epoch'))!=epoch
            or type(tick.get('quantity')) is not int or tick['quantity']<=0
            or type(tick.get('price_krw')) is not int or finite_number(tick.get('observed_epoch')) is None):continue
        key=(tick['observed_epoch'],tick['price_krw'],tick.get('item'))
        if key in ticks and ticks[key]!=tick:
            return {'status':'source_gap','reason':'conflicting_tick_identity'}
        ticks[key]=tick
    used_ticks=Counter();used_fills=Counter();used_depth=Counter();legs=[];crosses=0
    for i,(qty,limit) in enumerate(zip(quantities,prices)):
        slot=schedule['slots'][i];left=qty
        for j,fill in enumerate(fills):
            latest=_fill_latest_possible_at(fill)
            if (latest and fill.get('venue') in fill_venues and slot['slot_start_epoch']<=fill['at'].timestamp()
                and latest.timestamp()<min(slot['cancel_request_by_epoch'],exit_at.timestamp()) and fill['price']<=limit):
                take=min(left,fill['qty']-used_fills[j]);used_fills[j]+=take;left-=take
                if take:legs.append((take,fill['price']));used_depth[fill['price']]+=take
        if left and depth_valid:
            for key,tick in sorted(ticks.items()):
                if not slot['slot_start_epoch']<=tick['observed_epoch']<min(slot['cancel_request_by_epoch'],exit_at.timestamp()):continue
                price=tick['price_krw']
                if price>limit:continue
                level=sum(r.get('quantity',0) for r in depth.get('levels',[]) if r.get('price_krw')==price and type(r.get('quantity')) is int and r['quantity']>=0)
                # All actual prints at this price reserve observed liquidity,
                # even those outside the candidate slot; no double use.
                actual_at_price=sum(f['qty'] for f in fills if f['price']==price)
                available=max(0,min(tick['quantity']-used_ticks[key],level-max(used_depth[price],actual_at_price)))
                take=min(left,available);left-=take;used_ticks[key]+=take;used_depth[price]+=take
                if take:legs.append((take,price));crosses+=int(price<anchor)
    cost=trade['comparison_cost_rate']; parent=_costed_fixed_exit_pnl([(trade['buy_qty'],trade['buy_price'])],trade['sell_price'],cost)
    pnl=_costed_fixed_exit_pnl(legs,trade['sell_price'],cost);filled=sum(q for q,p in legs)
    notional=trade['buy_qty']*trade['buy_price']
    return dict(status='paired' if filled==target else 'partial_unfilled' if filled else 'modeled_no_fill',
                target_qty=target,modeled_filled_qty=filled,unfilled_qty=target-filled,
                candidate_net_pnl_krw=pnl,modeled_parent_net_pnl_krw=parent,
                candidate_net_pct_on_parent_notional=100*pnl/notional,
                parent_net_pct_on_parent_notional=100*parent/notional,
                observation_coverage='sampled_last_trade_tick',cost_model='canonical_sell_notional_only_v1',
                verified_price_cross_count=crosses,
                cancel_confirmation_model='assumed_within_reserve_not_broker_verified')


def replay_valid(report):
    from src.engine.scalping.initial_quantity_policy import _digest, _cap_candidate_trade, get_trade_cost_rate, _quantity_research_replay_costs_valid
    from src.engine.scalping.initial_quantity_legacy_reader import initial_replay_economics_valid as legacy
    try:
        if (report.get('report_content_sha256')!=_digest({k:v for k,v in report.items() if k!='report_content_sha256'})
            or report.get('evaluation_algorithm')!=VERSION):return False
        # Preserve old shape aggregate conservation, while v2 cap economics
        # are validated with the new reader rather than silently reinterpreted.
        copy={**report,'generation_kind':'initial_completed_trade_seed'}
        if not legacy(copy) or not _quantity_research_replay_costs_valid(report):return False
        facts={str(r['recommendation_id']):r for r in report['census']['input_fact_rows']}
        for row in report['trades']:
            fact=facts[str(row['record_id'])];source=row['cap_source']
            receipt = row.get('quantity_research_cost') if row.get('cost_basis') == 'broker_confirmed_total_allocated' else None
            notional = receipt['buy_amount_krw'] if receipt else fact['buy_qty'] * fact['buy_price']
            if ('original_notional_krw' in row and
                (finite_number(row['original_notional_krw']) is None or
                 row['original_notional_krw'] != notional)):
                return False
            trade=dict(buy_qty=fact['buy_qty'],
                buy_price=receipt['buy_amount_krw']/receipt['buy_qty'] if receipt else fact['buy_price'],
                sell_price=receipt['sell_amount_krw']/receipt['sell_qty'] if receipt else fact['sell_price'],
                realized_net_pnl_krw=row['actual_net_pnl_krw'])
            if any(value!=_cap_candidate_trade(trade,source,mode,report['census']['cost_rate']) for mode,value in row['cap_candidates'].items()):return False
        return True
    except (TypeError,ValueError,KeyError,OverflowError):return False



def policy_decision_precedes_fill(row, fact):
    """Verify either exact chronology or the native same-second submit proof."""
    from src.engine.scalping.initial_quantity_policy import _digest
    decision, fill = kst_timestamp(row.get('policy_decision_at')),kst_timestamp(row.get('entry_fill_at'))
    if decision is None or fill is None:return False
    if decision <= fill:return True
    try:
        proof = row['policy_decision_clock_proof']
        body = {k:v for k,v in proof.items() if k != 'proof_sha256'}
        source = row['cap_source']
        request,sent,received = (kst_timestamp(proof[k]) for k in ('request_at','sent_at','fill_received_at'))
        return bool(proof.get('schema') == 'initial_quantity_policy_clock_interval_v1'
            and proof.get('proof_sha256') == _digest(body)
            and (row.get('shapes') or {}).get('parent',{}).get('policy_decision_clock_proof') == proof
            and proof.get('broker_precision_sec') == row.get('entry_fill_clock_precision_sec') == 1
            and row.get('entry_fill_clock_source') == 'broker_execution_observed_at'
            and kst_timestamp(proof['decision_at']) == decision
            and kst_timestamp(proof['fill_at']) == fill
            and kst_timestamp(fact['buy_time']) is not None and fill <= kst_timestamp(fact['buy_time'])
            and fill.date() == kst_timestamp(fact['buy_time']).date()
            and decision < fill + timedelta(seconds=1)
            and request is not None and sent is not None and received is not None
            and decision <= request <= sent <= received
            and request < fill + timedelta(seconds=1) and sent-request <= timedelta(seconds=120)
            and proof['attempt_id'] == source['attempt_id'] and proof['attempt_id']
            and proof['plan_sha256'] == source['plan_sha256'] and proof['plan_sha256']
            and isinstance(proof['plan_sha256'],str) and len(proof['plan_sha256']) == 64
            and all(c in '0123456789abcdef' for c in proof['plan_sha256'])
            and proof['order_no'] == row['entry_fill_order_no'] and proof['order_no']
            and proof['execution_no'] == row['entry_fill_execution_no'] and proof['execution_no']
            and proof['request_tag'] and type(proof['fill_qty']) is int and proof['fill_qty'] > 0
            and proof['fill_qty'] <= fact['buy_qty']
            and len(source['fills']) >= 1 and source['fills'][0]['qty'] == proof['fill_qty']
            and kst_timestamp(source['fills'][0]['at']) == fill)
    except (KeyError,TypeError,ValueError):return False


def evaluate(report, *, parent_policy, pid_receipt=None, terminal_receipt=None, following_bars=None,
             timeout_research=None, parent_policy_file_sha256=None, enforce_trade_lineage=True,
             evaluation_algorithm=None):
    from src.engine.scalping.initial_quantity_policy import _digest, _TYPES, _SHAPES, _CAP_MODES, refresh_window
    from src.engine.scalping.initial_quantity_activation import refresh_parent_policy_valid
    version = _selection_version(evaluation_algorithm)
    legacy = version == VERSION
    if legacy and any(row.get('cost_basis') == 'broker_confirmed_total_allocated' for row in report.get('trades', [])):
        raise ValueError('refresh_research_cost_requires_v3_selection')
    if (not refresh_parent_policy_valid(parent_policy) or not replay_valid(report)
        or report['census'].get('entry_on_or_after')!=refresh_window(parent_policy)
        or any(r['entry_date']<refresh_window(parent_policy) for r in report['trades'])):
        raise ValueError('refresh_parent_or_replay_contract_invalid')
    if timeout_research is not None:
        from src.engine.scalping.initial_quantity_timeout_research import timeout_research_valid
        if not timeout_research_valid(timeout_research, replay=report) or timeout_research.get('census')!=report['census']:
            raise ValueError('refresh_timeout_source_invalid')
    if following_bars is not None:
        from src.engine.scalping.initial_quantity_following_bars import following_bar_source_valid
        if not following_bar_source_valid(following_bars,report):raise ValueError('refresh_following_source_invalid')
    receipts=(pid_receipt or {}).get('daily_pid_receipts') or []
    expected_status = ('initial_policy_refresh_loaded' if parent_policy.get('schema_version') == 'initial_entry_quantity_runtime_refresh_v1'
                       else 'initial_policy_v2_loaded' if parent_policy.get('schema_version') == 'initial_entry_quantity_runtime_v2'
                       else 'initial_policy_loaded')
    bound=[];excluded=[]
    facts={str(r['recommendation_id']):r for r in report['census']['input_fact_rows']}
    for row in report['trades']:
        dt=kst_timestamp(row.get('policy_decision_at'))
        ok=(row.get('applied_policy_status')==expected_status and row.get('policy_decision_stage')=='entry_execution_sizing_plan' and row.get('applied_policy_file_sha256')==parent_policy_file_sha256
            and dt is not None and policy_decision_precedes_fill(row,facts[str(row['record_id'])])
            and any(p.get('entry_date')==row['entry_date'] and str(p.get('pid'))==str(row.get('applied_policy_runtime_pid'))
                    and kst_timestamp(p.get('verified_at')) is not None and kst_timestamp(p['verified_at'])<=dt for p in receipts))
        if ok or not enforce_trade_lineage:bound.append(row)
        else:excluded.append(row['trade_id'])
    dates=sorted({r['entry_date'] for r in bound});cut=dates[-1] if dates else None
    # A position's observation horizon is never split across train/holdout.
    split_at=kst_timestamp(cut+'T00:00:00+09:00') if cut else None
    facts={str(r['recommendation_id']):r for r in report['census']['input_fact_rows']}
    purged=[r['trade_id'] for r in bound if r['entry_date']<cut and
        (kst_timestamp(facts[str(r['record_id'])]['sell_time'])>=split_at or
         not legacy and r.get('cost_available_at') is not None and
         (kst_timestamp(r['cost_available_at']) is None or kst_timestamp(r['cost_available_at'])>=split_at))]
    train=[r for r in bound if r['entry_date']<cut and r['trade_id'] not in purged]
    test=[r for r in bound if r['entry_date']==cut]
    blockers=[]
    if len(dates)<3:blockers.append('independent_post_apply_dates_below_three')
    pid_ok=bool((pid_receipt or {}).get('actual_pid_consumed') is True and (pid_receipt or {}).get('policy_content_sha256')==parent_policy['policy_content_sha256']
                and receipts and all(type(p.get('pid')) is int and p['pid']>0 and kst_timestamp(p.get('verified_at')) is not None for p in receipts))
    if not pid_ok:blockers.append('parent_pid_consumption_missing')
    if not terminal_receipt or terminal_receipt.get('report_content_sha256')!=report['report_content_sha256'] or terminal_receipt.get('terminal') is not True or terminal_receipt.get('costed_completed_trade_count')!=len(report['trades']):blockers.append('post_apply_terminal_cost_binding_missing')
    decisions={};train_rows_by_type=defaultdict(list);test_rows_by_type=defaultdict(list)
    for r in train:train_rows_by_type[r['quantity_type']].append(r)
    for r in test:test_rows_by_type[r['quantity_type']].append(r)
    stats=aggregate_joint(timeout_research, train, test) if timeout_research else {}
    for name in _TYPES:
        parent=parent_policy['type_policies'][name];incumbent=(parent.get('ratio_mode','parent_5stage'),parent.get('selected_shape','parent'),parent.get('selected_total_wait_sec'))
        keys=sorted((stats.get('train',{}).get(name) or {}))
        def measure(cohort,key):
            partition='train' if cohort is train_rows_by_type[name] else 'holdout'
            values=stats.get(partition,{}).get(name,{}).get(key,{})
            weight=values.get('weight',0)
            return dict(count=values.get('count',0), coverage=values.get('count',0)/len(cohort) if cohort else 0.,
                        delta=values.get('delta',0),winner_weighted_delta_pct=values.get('weighted_delta',0)/weight if weight else None,
                        mean_delta_pct=values.get('delta_pct',0)/values['count'] if values.get('count') else None,
                        verified_cross_count=values.get('verified_cross_count',0),
                        daily=values.get('daily',{}))
        ranked=[];metrics={}
        for key in keys:
            a=measure(train_rows_by_type[name],key);config=(timeout_research or {}).get('joint_grid',{}).get(key)
            if not config:continue
            minimum=30
            shape_change=config['shape']!=incumbent[1] or config['horizon']!=incumbent[2]
            following=(following_bars or {}).get('weighted_by_type',{}).get(name,{})
            if legacy:
                winner_count=sum(r['actual_net_pnl_krw']>0 and r['actual_profit_rate']>0 for r in train_rows_by_type[name]+test_rows_by_type[name])
                following_ok=bool(winner_count and following.get('observed_minute_lower_count',0)/winner_count>=.8)
            else:
                train_winners=[r for r in train_rows_by_type[name] if r['actual_net_pnl_krw']>0 and r['actual_profit_rate']>0]
                linked=sum(((following_bars or {}).get('trades',{}).get(r['trade_id']) or {}).get('first_lower_elapsed_from_fill_minute') is not None for r in train_winners)
                following_ok=bool(train_winners and linked/len(train_winners)>=.8)
            score_ok=(a['winner_weighted_delta_pct'] is not None and a['winner_weighted_delta_pct']>1e-6) if legacy else a['mean_delta_pct'] is not None and a['mean_delta_pct']>0
            eligible=(a['count']>=minimum and a['coverage']>=.8 and a['delta']>0 and score_ok
                      and (not shape_change or a['mean_delta_pct'] is not None and a['mean_delta_pct']>.10
                           and a['verified_cross_count']>0 and following_ok)
                      and len(a['daily'])>=2 and min(a['daily'].values())>=-.001)
            metrics[key]={'train':a,'train_eligible':eligible}
            if eligible:ranked.append((a['winner_weighted_delta_pct'] if legacy else a['mean_delta_pct'],a['delta'],key))
        winner=max(ranked)[-1] if ranked else None
        approved=False;holdout=None
        if winner:
            holdout=measure(test_rows_by_type[name],winner)
            approved=bool(holdout['count'] and holdout['coverage']>=.8 and holdout['delta']>=0
                and (legacy or holdout['mean_delta_pct'] is not None and holdout['mean_delta_pct']>=0))
        config=timeout_research['joint_grid'][winner] if winner and approved and not blockers and name!='SAFE_UNKNOWN' else None
        decisions[name]=dict(selected_shape=config['shape'] if config else incumbent[1],selected_ratio_mode=config['mode'] if config else incumbent[0],
                             selected_total_wait_sec=config['horizon'] if config and config['horizon']!=incumbent[2] else None,
                             minimum_completed_count=30,observed_completed_count=len(train_rows_by_type[name])+len(test_rows_by_type[name]),
                             reason='post_apply_hurdles_passed' if config else 'refresh_hurdles_or_evidence_not_met',
                             cap_candidate_metrics={},joint_candidate_metrics=metrics,train_selected_candidate=winner,
                             train_selected_candidate_sha256=_digest(timeout_research['joint_grid'][winner]) if winner else None,
                             holdout=holdout,holdout_passed=approved)
    changed=any(d['selected_shape']!=parent_policy['type_policies'][n].get('selected_shape','parent') or d['selected_ratio_mode']!=parent_policy['type_policies'][n].get('ratio_mode','parent_5stage') or d['selected_total_wait_sec'] is not None for n,d in decisions.items())
    return dict(schema_version='initial_entry_quantity_refresh_evaluation_v1',evaluation_algorithm=version,generation_kind='refresh',source_date=report['source_date'],
                parent_policy_content_sha256=parent_policy['policy_content_sha256'],report_content_sha256=report['report_content_sha256'],
                state='eligible_source_only' if changed and not blockers else 'carry_parent',global_blockers=blockers,type_decisions=decisions,
                parent_policy_bound_trade_count=len(bound),excluded_trade_ids=excluded,purged_trade_ids=purged,
                train_trade_ids=[r['trade_id'] for r in train],holdout_trade_ids=[r['trade_id'] for r in test],
                policy_pid_status='verified_archive' if pid_ok else 'unobservable',
                trade_policy_binding_status=('valid_empty' if economic_sample_status(report)=='valid_empty'
                    else 'source_gap') if not report['trades'] else 'partial' if excluded else 'bound',
                economic_sample_status=economic_sample_status(report),
                runtime_apply_allowed=False,runtime_effect=False)


def aggregate_joint(timeout, train, holdout):
    from pathlib import Path
    from src.engine.lifecycle import research_storage as storage
    by_id={r['trade_id']:(part,r) for part,rows in (('train',train),('holdout',holdout)) for r in rows}
    stats={}
    for item in storage.iter_tree(Path(timeout['joint_evidence_root']),timeout['joint_outcomes_ref']):
        if item['trade_id'] not in by_id or item['outcome'].get('status') not in VALID_OUTCOMES:continue
        partition,row=by_id[item['trade_id']];case=item['outcome'];key=item['key']
        value=stats.setdefault(partition,{}).setdefault(row['quantity_type'],{}).setdefault(key,
            dict(count=0,delta=0.,delta_pct=0.,verified_cross_count=0,weight=0.,weighted_delta=0.,daily={}))
        delta=case['candidate_net_pnl_krw']-case['modeled_parent_net_pnl_krw']
        value['count']+=1;value['delta']+=delta
        value['delta_pct']+=case['candidate_net_pct_on_parent_notional']-case['parent_net_pct_on_parent_notional']
        value['verified_cross_count']+=int(case.get('verified_price_cross_count',0)>0)
        value['daily'][row['entry_date']]=value['daily'].get(row['entry_date'],0.)+delta
        if row['actual_net_pnl_krw']>0 and row['actual_profit_rate']>0:
            value['weight']+=row['actual_net_pnl_krw']
            value['weighted_delta']+=row['actual_net_pnl_krw']*(case['candidate_net_pct_on_parent_notional']-case['parent_net_pct_on_parent_notional'])
    return stats


def read_joint_cases(timeout):
    """Decode bounded shards; never trust an alternate ad-hoc matrix."""
    from src.engine.lifecycle import research_storage as storage
    from src.engine.lifecycle.research_input_budget import LIMIT_BYTES
    from pathlib import Path
    result={};size=0
    root=Path(timeout['joint_evidence_root'])
    if not root.is_absolute():raise ValueError('joint_evidence_root_invalid')
    for row in storage.iter_tree(root,timeout['joint_outcomes_ref']):
        size+=len(storage.encoded(row))*8
        if size>LIMIT_BYTES:raise ValueError('quantity_candidate_block_partition_required')
        cases=result.setdefault(row['trade_id'],{})
        if row['key'] in cases:raise ValueError('joint_candidate_duplicate')
        cases[row['key']]=row['outcome']
    return result


def _issued_replay_representation(rebuilt, timeout, root):
    """Compare issued gzip receipts through the native lossless custody proof.

    Only the in-memory comparison uses the issued representation. Producers
    keep canonical logical receipts; no report, timeout or source is rewritten.
    """
    from pathlib import Path
    from src.engine.automation.main_trailing_source_store import _archive_generation, _archive_logical_authority, signature
    from src.engine.scalping.initial_quantity_policy import _digest, _file_sha256
    current=rebuilt['pipeline_source_receipts'];issued=timeout['pipeline_source_receipts']
    if current==issued:return rebuilt
    if not isinstance(issued,dict) or current.keys()!=issued.keys():return None
    for day,receipt in current.items():
        if receipt==issued[day]:continue
        logical=root/'pipeline_events'/f'pipeline_events_{day}.jsonl'
        physical=Path(str(logical)+'.gz')
        authority=Path(str(physical)+'.archive_receipt.json')
        if logical.exists() or logical.is_symlink() or physical.is_symlink():return None
        checked=_archive_logical_authority(logical)
        if checked is None:return None
        # Enrollment has independently checked the complete logical SHA and
        # gzip CRC. A report reader never performs an offline migration.
        _archive_generation(root,logical)
        proof,epoch=checked;info=physical.stat()
        generation=dict(device=info.st_dev,inode=info.st_ino,size_bytes=info.st_size,
                        mtime_ns=info.st_mtime_ns,ctime_ns=info.st_ctime_ns)
        if (proof['archive_generation']!=generation or receipt.get('path')!=str(logical)
                or receipt.get('sha256')!=proof['logical_content_sha256']
                or receipt.get('size_bytes')!=proof['logical_size_bytes']
                or receipt.get('archive_identity_valid') is not None):return None
        expected={**receipt,'path':str(physical),'size_bytes':info.st_size,
                  'sha256':_file_sha256(physical),'archive_identity_valid':True}
        if (issued[day]!=expected or signature(physical.stat())!=signature(info)
                or signature(authority.lstat())!=epoch):return None
    comparable={**rebuilt,'pipeline_source_receipts':issued}
    comparable['report_content_sha256']=_digest({k:v for k,v in comparable.items() if k!='report_content_sha256'})
    return comparable


def joint_evidence_valid(timeout, *, replay=None):
    from pathlib import Path
    from src.engine.scalping.initial_quantity_policy import build_initial_quantity_replay, _SHAPES, _CAP_MODES
    from src.engine.lifecycle import research_storage as storage
    try:
        root=Path(timeout['joint_data_root'])
        if not root.is_absolute() or Path(timeout['joint_evidence_root']) != root/'report/initial_entry_quantity_type_policy/joint_evidence':return False
        grid={f'{mode}:{shape}:{h}':dict(mode=mode,shape=shape,horizon=h,reserve=5)
              for mode in ('parent_5stage',*_CAP_MODES) for shape in _SHAPES for h in (None,*timeout['horizons_sec'])}
        if timeout['joint_grid']!=grid:return False
        shared={}
        rebuilt=build_initial_quantity_replay(timeout['source_date'],data_dir=root,fact_rows=timeout['census']['input_fact_rows'],
            entry_on_or_after=timeout['entry_on_or_after'],path_cache=shared,source_census=timeout['census'])
        comparable=_issued_replay_representation(rebuilt,timeout,root)
        if (comparable is None or comparable['report_content_sha256']!=timeout['joint_replay_content_sha256']
            or rebuilt['census']!=timeout['census'] or replay is not None and comparable!=replay):return False
        facts={str(f['recommendation_id']):f for f in rebuilt['census']['input_fact_rows']}
        rows={r['trade_id']:r for r in rebuilt['trades']};expected_ids=iter((tid,key) for tid in rows for key in grid);count=0
        from src.engine.scalping.initial_quantity_policy import _digest
        import hashlib
        active=None;digest=None;memo_key=None;known=None
        def finish():
            if active is None:return True
            actual=digest.hexdigest()
            if known is not None and known!=actual:return False
            _VERIFIED_EXECUTIONS[memo_key]=actual
            _VERIFIED_EXECUTIONS.move_to_end(memo_key)
            while len(_VERIFIED_EXECUTIONS)>256:_VERIFIED_EXECUTIONS.popitem(last=False)
            return True
        for item in storage.iter_tree(Path(timeout['joint_evidence_root']),timeout['joint_outcomes_ref']):
            tid,key=item['trade_id'],item['key'];identity=(tid,key)
            if identity!=next(expected_ids,None):return False
            count+=1;r=rows[tid];f=facts[str(r['record_id'])];cfg=grid[key]
            receipt = r.get('quantity_research_cost') if r.get('cost_basis') == 'broker_confirmed_total_allocated' else None
            trade=dict(buy_qty=f['buy_qty'],
                       buy_price=receipt['buy_amount_krw']/receipt['buy_qty'] if receipt else f['buy_price'],
                       sell_price=receipt['sell_amount_krw']/receipt['sell_qty'] if receipt else f['sell_price'],exit_at=f['sell_time'],
                       quantity_type=r['quantity_type'],comparison_cost_rate=timeout['census']['cost_rate'])
            if tid!=active:
                if not finish():return False
                active=tid;digest=hashlib.sha256()
                memo_key=_execution_key(trade,shared['paths'].get(tid,{}),r.get('cap_source') or {},grid)
                known=_VERIFIED_EXECUTIONS.get(memo_key)
            digest.update(storage.encoded(item)+b'\n')
            if known is None:
                expected=execution_case(trade,shared['paths'].get(tid,{}),r.get('cap_source') or {},mode=cfg['mode'],shape=cfg['shape'],horizon=cfg['horizon'],reserve=cfg['reserve'])
                if item['outcome']!=expected:return False
        return finish() and count==len(rows)*len(grid) and next(expected_ids,None) is None
    except (OSError,ValueError,KeyError,TypeError,OverflowError):return False
