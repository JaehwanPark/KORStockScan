"""Causal stop-confirmation comparison. No synthetic AI, fills or broker calls."""
from dataclasses import asdict, replace
import math
from .main_stop_policy import StopValues, soft_decision, protect_confirmed, append_sample, digest, finite, TUNABLE

SCHEMA = 'main_stop_research_v1'


def candidates(parent):
    """One axis per candidate; safety references are immutable."""
    grid = {'soft_stop_pct': [parent.soft_stop_pct + d for d in (-.5, -.25, .25, .5)],
            'grace_sec': [0, 15, 30, 45, 60], 'window_sec': [10, 20, 30],
            'min_span_sec': [0, 4, 8], 'min_samples': [2, 3, 5],
            'below_ratio': [.5, .67, .8], 'buffer_pct': [0., .1, .2]}
    result = {'parent': parent}
    for field, values in grid.items():
        for value in values:
            if value == getattr(parent, field):
                continue
            try:
                parsed = StopValues.parse(asdict(replace(parent, **{field: value})))
            except ValueError:
                continue
            result[f'{field}:{value}'] = parsed
    return result


def replay(rows, values, *, vote_reader=None):
    """First crossing on actual supplied receipts, bounded memory per position.

    A changed exit is a modeled full-depth alternative, never an actual fill.
    Original votes must already permit that exact crossing. Different/missing
    vote inputs, ADD, partial fills, manual custody and other exits censor it.
    """
    touch = None
    samples = []
    previous = None
    birth = None
    identity = None
    worst = 0.
    count = 0
    vote_hold = None
    result = dict(status='censored', reason='crossing_not_observed', modeled_net_krw=None,
                  actual_order_submitted=False, allowed_runtime_apply=False)
    for row in rows:
        count += 1
        at, bid = row.get('at'), row.get('bid')
        if (row.get('schema') != 'main_stop_source_v1' or not finite(at) or not finite(bid)
                or bid <= 0 or row.get('coverage_complete') is not True
                or row.get('owner') != 'main' or not row.get('route') or not row.get('transport_epoch')
                or not row.get('position_key') or not row.get('pin_sha256')
                or row.get('source_sha256') != digest({k:v for k,v in row.items() if k!='source_sha256'})):
            return dict(result, status='source_gap', reason='quote_or_position_source_invalid')
        current_identity = tuple(row.get(k) for k in ('position_key','pin_sha256','role','market','item','route','transport_epoch','quantity','buy_basis_krw','capture_rejected_count'))
        try:
            original = StopValues.parse(row['source_stop_values'])
            if digest(asdict(original)) != row.get('parent_values_sha256'):
                raise ValueError('original_values_hash')
        except (ValueError, TypeError, KeyError):
            return dict(result,status='source_gap',reason='original_stop_values_unverified')
        if previous is not None and (at <= previous or at-previous > 1.5 or current_identity != identity):
            return dict(result, reason='coverage_or_position_generation_changed')
        if not row.get('automatic_management_allowed') or row.get('manual') or row.get('pending_exit'):
            return dict(result, reason='custody_or_existing_exit')
        if (any(type(row.get(k)) is not bool for k in ('grace_enabled','protect_enabled','handoff_enabled'))
                or not finite(row.get('vote_max_worsen_pct'))):
            return dict(result, status='source_gap', reason='runtime_flags_unobserved')
        qty, basis = row.get('quantity'), row.get('buy_basis_krw')
        model = row.get('cost_model') or {}
        buy_cost, sell_rate = model.get('buy_cost_krw'), model.get('sell_cost_rate')
        if (not all(finite(x) for x in (qty,basis,buy_cost,sell_rate,model.get('known_at')))
                or qty <= 0 or int(qty)!=qty or basis<=0 or buy_cost<0 or not 0<=sell_rate<.05
                or model['known_at']>at or not model.get('source_sha256')):
            return dict(result,status='source_gap',reason='cost_model_source_missing')
        if row.get('add_count',0) or row.get('partial_fill') or row.get('other_exit'):
            return dict(result,reason='alternative_lifecycle_unidentified')
        quote_at = row.get('quote_at')
        if not finite(quote_at) or not 0 <= at - quote_at <= 3:
            return dict(result, status='source_gap', reason='quote_clock_unverified')
        if not finite(row.get('decision_profit_pct')):
            return dict(result, status='source_gap', reason='runtime_decision_profit_unobserved')
        previous, identity = at, current_identity
        if birth is None:birth = at
        pnl = bid*qty*(1-sell_rate)-basis-buy_cost
        # Runtime crossing uses the actually observed decision basis. Exact
        # costs evaluate the alternative economics without rewriting that rule.
        profit = row['decision_profit_pct']
        line = row.get('protect_line')
        if finite(line) and line>0:
            # Current Main has no active source-bound line generator. A legacy
            # database number alone cannot prove custody/arm/monotonicity for
            # this experiment. Runtime safety still honors the existing line.
            return dict(result,status='source_gap',reason='protect_line_producer_unidentified')
        if count == 1 and (profit <= values.soft_stop_pct or
                           (finite(line) and line > 0 and bid <= line)):
            return dict(result, reason='pre_crossing_source_missing')
        worst = min(worst, profit)
        samples, quality = append_sample(samples,at=at,price=bid)
        if quality == 'capacity_censored':return dict(result,reason='sample_capacity_censored')
        decision = soft_decision(values,profit_pct=profit,now=at,touch_at=touch,
                                 enabled=row.get('grace_enabled',True),after_add=False)
        touch = decision.touch_at
        if decision.rule == 'soft_recovered': vote_hold = None
        rule = decision.rule if decision.disposition=='exit_candidate' else None
        if finite(line) and line>0 and bid<=line:
            confirmed,_ = protect_confirmed(values,samples,now=at,price_line=line,profit_pct=profit,
                                            enabled=row.get('protect_enabled',True))
            if confirmed:rule='protect_trailing_stop'
        if not rule:continue
        # Never infer an earlier crossing from a series starting below threshold.
        if count == 1:return dict(result,reason='pre_crossing_source_missing')
        # Runtime EXIT_SOFT_STOP also releases VETO at the existing protective
        # emergency threshold. Keep that effective priority; do not extend it.
        safety = profit <= values.hard_stop_pct or profit <= values.protect_emergency_pct
        if profit <= values.hard_stop_pct and row.get('handoff_enabled'):
            return dict(result,reason='manual_handoff_not_sell')
        if row.get('role') == 'SCALP_PRESET_TP':
            return dict(result,reason='preset_safety_precedes_soft_policy')
        if row.get('holding_ai_required') is not False and not safety and rule!='protect_trailing_stop':
            if vote_hold is None:
                vote = vote_reader(row, at) if vote_reader is not None else (row.get('original_vote') or {})
                if not (vote.get('decision') in {'PASS','VETO','INSUFFICIENT'}
                        and vote.get('source_verified') is True):
                    return dict(result,reason='original_crossing_vote_unidentified')
                vote_hold = dict(vote=vote, at=at, profit=profit, started=touch or at)
            from .trailing_exit_decision import evaluate_exit_deferral
            vote = vote_hold['vote']
            outcome = evaluate_exit_deferral(decision=vote['decision'],now=at,signal_at=vote_hold['at'],
                started_at=vote_hold['started'],anchor_profit=vote_hold['profit'],profit=profit,
                max_defer_sec=vote['max_defer_sec'],max_worsen_pct=row.get('vote_max_worsen_pct',.8),
                policy_valid=True,quote_fresh=True,safety=safety,same_generation=True,same_market=True)
            if not outcome.proceeds:continue
        if not finite(row.get('bid_qty')) or row['bid_qty']<qty:
            return dict(result,reason='full_executable_depth_unobserved')
        return dict(result,status='modeled',reason=rule,modeled_net_krw=pnl,
                    crossing_at=at,exposure_sec=at-birth,mae_pct=worst,
                    evidence_kind='actual_entry_alternative_exit',cost_source_sha256=model['source_sha256'])
    return result


def validate_experiment(contract, *, parent_sha, source_sha, code_sha):
    """A numerical acceptance contract is frozen before source/holdout evaluation."""
    if not isinstance(contract,dict):raise ValueError('stop_experiment_missing')
    body={k:v for k,v in contract.items() if k!='experiment_sha256'}
    if (contract.get('schema')!='main_stop_experiment_v1' or contract.get('experiment_sha256')!=digest(body)
            or contract.get('parent_sha256')!=parent_sha or contract.get('source_sha256')!=source_sha
            or contract.get('code_sha256')!=code_sha or not contract.get('operator_lock_sha256')
            or not finite(contract.get('frozen_at')) or not finite(contract.get('split_at'))
            or type(contract.get('min_train')) is not int or contract['min_train']<2
            or type(contract.get('min_holdout')) is not int or contract['min_holdout']<2
            or not finite(contract.get('minimum_paired_ev_krw')) or contract['minimum_paired_ev_krw']<0
            or not isinstance(contract.get('allowed_keys'),list)
            or not contract['allowed_keys']
            or not set(contract['allowed_keys'])<=TUNABLE
            or not finite(contract.get('embargo_sec')) or contract['embargo_sec']<60):
        raise ValueError('stop_experiment_binding_invalid')
    if (not finite(contract.get('max_censoring_ratio')) or not 0<=contract['max_censoring_ratio']<1
            or not finite(contract.get('max_standard_error_krw')) or contract['max_standard_error_krw']<0
            or not isinstance(contract.get('max_daily_change'),dict)
            or set(contract['max_daily_change'])!=set(contract['allowed_keys'])
            or any(not finite(x) or x<=0 for x in contract['max_daily_change'].values())
            or not isinstance(contract.get('performance_receipt'),dict)):
        raise ValueError('stop_acceptance_limits_not_frozen')
    from .main_stop_policy import bounded_object
    performance,sha=bounded_object(contract['performance_receipt'].get('path',''))
    if (sha!=contract['performance_receipt'].get('sha256')
            or performance.get('schema')!='main_stop_performance_v1'
            or performance.get('status')!='pass'
            or performance.get('code_sha256')!=code_sha
            or performance.get('scope')!='runtime_and_postclose'
            or performance.get('unresolved_findings')!=[]):
        raise ValueError('stop_performance_gate_unverified')
    if contract['frozen_at'] >= contract['split_at'] - contract['embargo_sec']:
        raise ValueError('stop_experiment_not_frozen_before_holdout')
    return contract


def split_acceptable(row, split, contract):
    n,total=row[split+'_n'],row[split+'_total']
    if n<contract['min_'+split] or total<n or not total:return False
    variance=max(0.,(row[split+'_delta_sq']-row[split+'_delta']**2/n)/(n-1))
    return (1-n/total<=contract['max_censoring_ratio']
            and math.sqrt(variance/n)<=contract['max_standard_error_krw'])


def choose(aggregates, contract):
    """Use global identical eligible denominators, one train winner then holdout."""
    if not contract:return None,'baseline_carry'
    for row in aggregates.values():
        if (not isinstance(row, dict) or any(type(row.get(k)) is not int or row[k] < 0
                for k in ('train_n', 'holdout_n', 'train_total', 'holdout_total', 'train_safety_regressions', 'holdout_safety_regressions'))
                or any(not finite(row.get(k)) for k in ('train_delta', 'holdout_delta', 'train_delta_sq', 'holdout_delta_sq'))
                or row['train_delta_sq']<0 or row['holdout_delta_sq']<0):
            raise ValueError('stop_selection_aggregate_invalid')
        for split in ('train','holdout'):
            n=row[split+'_n']
            if row[split+'_total']<n or (n and row[split+'_delta_sq']+1e-6<row[split+'_delta']**2/n):
                raise ValueError('stop_selection_aggregate_invalid')
    rows = [(name,row) for name,row in aggregates.items() if name!='parent'
            and name.split(':')[0] in contract['allowed_keys']]
    eligible=[(name,row) for name,row in rows if split_acceptable(row,'train',contract)
        and row['train_delta']/row['train_n']>contract['minimum_paired_ev_krw'] and row['train_safety_regressions']==0]
    if not eligible:return None,'hold_sample' if not rows or not any(r['train_n'] for _,r in rows) else 'hold_no_edge'
    name,row=max(eligible,key=lambda pair:(pair[1]['train_delta']/pair[1]['train_n'],pair[0]))
    if not split_acceptable(row,'holdout',contract):return None,'hold_sample'
    if row['holdout_safety_regressions']:return None,'hold_no_edge'
    if row['holdout_delta']/row['holdout_n']<=contract['minimum_paired_ev_krw']:return None,'hold_no_edge'
    return name,'selected'
