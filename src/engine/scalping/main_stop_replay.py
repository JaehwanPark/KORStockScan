"""Causal stop-confirmation comparison. No synthetic AI, fills or broker calls."""
from dataclasses import asdict, replace
from datetime import datetime
import math
from .main_stop_policy import StopValues, soft_decision, safety_decision, protect_confirmed, append_sample, digest, finite, TUNABLE

SCHEMA = 'main_stop_research_v1'


def cost_known_epoch(value):
    """Read the native aware ISO clock or legacy epoch without rewriting it."""
    if finite(value):
        return float(value) if value > 0 else None
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            return None
        epoch = stamp.timestamp()
        return epoch if finite(epoch) and epoch > 0 else None
    except (ValueError, OverflowError, OSError):
        return None


def _sealed(row):
    try:
        return (isinstance(row, dict) and row.get('source_sha256') ==
            digest({k:v for k,v in row.items() if k != 'source_sha256'}))
    except (ValueError, TypeError):
        return False


def preset_decision(row):
    """Evaluate only the observed preset contract, ahead of common soft stop."""
    receipt = row.get('preset_stop')
    if not isinstance(receipt, dict):
        raise ValueError('preset_effective_stop_unobserved')
    if (receipt.get('schema') != 'main_preset_stop_receipt_v1'
            or receipt.get('sha256') != digest({k:v for k,v in receipt.items() if k != 'sha256'})
            or any(receipt.get(k) != row.get(k) for k in ('position_key', 'pin_sha256', 'at'))
            or not isinstance(receipt.get('evaluator'), str) or not receipt['evaluator']
            or not all(finite(receipt.get(k)) for k in ('hard_stop_pct', 'grace_sec', 'held_sec'))
            or receipt['hard_stop_pct'] >= 0 or min(receipt['grace_sec'], receipt['held_sec']) < 0
            or type(receipt.get('enabled')) is not bool
            or (receipt.get('emergency_pct') is not None and (not finite(receipt['emergency_pct'])
                or receipt['emergency_pct'] > receipt['hard_stop_pct']))
            or (receipt.get('protect_pct') is not None and not finite(receipt['protect_pct']))
            or not finite(row.get('decision_profit_pct')) or type(row.get('handoff_enabled')) is not bool):
        raise ValueError('preset_effective_stop_invalid')
    return safety_decision(profit_pct=row['decision_profit_pct'], hard_pct=receipt['hard_stop_pct'],
        emergency_pct=receipt.get('emergency_pct'), protect_pct=receipt.get('protect_pct'),
        preset_grace_sec=receipt['grace_sec'], held_sec=receipt['held_sec'],
        handoff_enabled=row['handoff_enabled'], manual=bool(row.get('manual')),
        pending=bool(row.get('pending_exit'))) if (receipt['enabled']
            and row.get('automatic_management_allowed', True) is True) else None


def valid_handoff(row):
    return (_sealed(row) and row.get('schema') == 'main_stop_handoff_source_v1'
        and row.get('owner') == 'main' and type(row.get('registered')) is bool
        and finite(row.get('at')) and row['at'] > 0
        and bool(row.get('position_key') and row.get('pin_sha256') and row.get('source_stage'))
        and row.get('exit_rule') in {'scalp_hard_stop_pct', 'scalp_preset_hard_stop_pct'}
        and finite(row.get('decision_profit_pct'))
        and row.get('actual_order_submitted') is False
        and row.get('handoff_enabled') is True
        and row.get('actual_realized_net_krw') is None
        and row.get('allowed_runtime_apply') is False)


def holding_contracts(rows):
    """Parallel operating evidence; no research relabeling or realized PnL.

    Keep scanning after a candidate crossing to bind the actual registration
    result. Only exact position/pin receipts can attest manual custody.
    """
    result = dict(schema='main_holding_contract_comparison_v1', status='observed',
        common_stop_values=None, effective_preset=None, preset_crossing=None,
        manual_handoff=dict(status='not_observed', attempts=0), actual_realized_net_krw=None)
    identity = None
    previous = None
    for row in rows:
        if not _sealed(row) or row.get('schema') not in {'main_stop_source_v1', 'main_stop_handoff_source_v1'}:
            return dict(result, status='source_gap', reason='holding_contract_source_invalid')
        current = tuple(row.get(k) for k in ('position_key', 'pin_sha256', 'role', 'market', 'record_id'))
        if not all(current[:4]) or (identity is not None and current != identity):
            return dict(result, status='source_gap', reason='holding_contract_identity_changed')
        at = row.get('at')
        if not finite(at) or (previous is not None and at < previous):
            return dict(result, status='source_gap', reason='holding_contract_clock_invalid')
        identity, previous = current, at
        try:
            common = asdict(StopValues.parse(row.get('source_stop_values')))
        except (ValueError, TypeError):
            return dict(result, status='source_gap', reason='original_stop_values_unverified')
        if result['common_stop_values'] is not None and common != result['common_stop_values']:
            return dict(result, status='source_gap', reason='original_stop_values_changed')
        result['common_stop_values'] = common
        terminal = row['schema'] == 'main_stop_handoff_source_v1'
        if terminal:
            if not valid_handoff(row):
                return dict(result, status='source_gap', reason='manual_handoff_receipt_invalid')
            old = result['manual_handoff']
            if old['status'] == 'registered' and not row['registered']:
                return dict(result, status='source_gap', reason='manual_custody_regressed')
            result['manual_handoff'] = dict(status='registered' if row['registered'] else 'pending',
                at=at, source_sha256=row['source_sha256'], attempts=old['attempts']+1,
                exit_rule=row['exit_rule'], observed_profit_pct=row['decision_profit_pct'])
        if row.get('role') == 'SCALP_PRESET_TP':
            try:
                decision = preset_decision(row)
            except ValueError as exc:
                result.update(status='source_gap', reason=str(exc))
                continue
            result['effective_preset'] = row['preset_stop']
            if not terminal and (row.get('coverage_complete') is not True
                    or not row.get('item') or not row.get('route') or not row.get('transport_epoch')
                    or not finite(row.get('quote_at')) or not 0 <= at-row['quote_at'] <= 3):
                result.update(status='source_gap', reason='operating_quote_source_unverified')
                continue
            if not terminal and result['manual_handoff']['status'] == 'registered':
                if row.get('automatic_management_allowed') is True and not row.get('manual'):
                    result.update(status='source_gap', reason='automatic_source_after_manual_handoff')
                continue
            if decision is not None and decision.disposition in {'exit_candidate', 'manual_handoff'} and result['preset_crossing'] is None:
                result['preset_crossing'] = dict(at=at, rule=decision.rule, disposition=decision.disposition,
                    evidence_kind='observed_safety_candidate_not_sell', first_crossing_proven=False,
                    source_sha256=row['source_sha256'])
    return result


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


def replay(rows, values, *, vote_reader=None, post_add_generation=False):
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
        if row.get('schema') == 'main_stop_handoff_source_v1':
            if (not valid_handoff(row) or (identity is not None
                    and (row['position_key'], row['pin_sha256']) != identity[:2])):
                return dict(result, status='source_gap', reason='manual_handoff_receipt_invalid')
            return dict(result, reason='manual_handoff_not_sell' if row['registered'] else 'manual_handoff_pending')
        count += 1
        at, bid = row.get('at'), row.get('bid')
        if (row.get('schema') != 'main_stop_source_v1' or not finite(at) or not finite(bid)
                or bid <= 0 or row.get('coverage_complete') is not True
                or row.get('owner') != 'main' or not row.get('route') or not row.get('transport_epoch')
                or not row.get('position_key') or not row.get('pin_sha256')
                or row.get('source_sha256') != digest({k:v for k,v in row.items() if k!='source_sha256'})):
            return dict(result, status='source_gap', reason='quote_or_position_source_invalid')
        current_identity = tuple(row.get(k) for k in ('position_key','pin_sha256','role','market','item','route','transport_epoch','quantity','buy_basis_krw','capture_rejected_count'))
        if post_add_generation:
            current_identity += ((row.get('post_add_generation') or {}).get('sha256'),)
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
        model = row.get('cost_model')
        if not isinstance(model, dict):
            return dict(result,status='source_gap',reason='cost_model_source_missing')
        buy_cost, sell_rate = model.get('buy_cost_krw'), model.get('sell_cost_rate')
        known_at = cost_known_epoch(model.get('known_at'))
        if (not all(finite(x) for x in (qty,basis,buy_cost,sell_rate,known_at))
                or qty <= 0 or int(qty)!=qty or basis<=0 or buy_cost<0 or not 0<=sell_rate<.05
                or known_at>at or not model.get('source_sha256')):
            return dict(result,status='source_gap',reason='cost_model_source_missing')
        if post_add_generation:
            aggregate=row.get('post_add_generation') or {}
            if (aggregate.get('schema')!='verified_post_add_generation_v1'
                or aggregate.get('sha256')!=digest({k:v for k,v in aggregate.items() if k!='sha256'})
                or aggregate.get('position_key')!=row['position_key']
                or aggregate.get('quantity')!=qty or aggregate.get('buy_basis_krw')!=basis
                or aggregate.get('cost_source_sha256')!=model['source_sha256']
                or not finite(aggregate.get('completed_at')) or aggregate['completed_at']>at
                or not aggregate.get('add_receipt_sha256') or aggregate.get('pending_add') is not False
                or aggregate.get('partial_fill') is not False or row.get('pending_add')):
                return dict(result,status='source_gap',reason='post_add_aggregate_generation_unverified')
        if (row.get('add_count',0) and not post_add_generation) or row.get('pending_add') or row.get('partial_fill') or row.get('other_exit'):
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
        if row.get('role') == 'SCALP_PRESET_TP':
            try:
                safety = preset_decision(row)
            except ValueError as exc:
                return dict(result, status='source_gap', reason=str(exc))
            if safety is not None and safety.disposition in {'exit_candidate', 'manual_handoff'}:
                return dict(result, reason='preset_pre_crossing_source_missing' if count == 1
                    else 'preset_safety_precedes_soft_policy', operating_rule=safety.rule,
                    operating_disposition=safety.disposition, crossing_at=at)
            continue
        line = row.get('protect_line')
        if finite(line) and line>0:
            # Current Main has no active source-bound line generator. A legacy
            # database number alone cannot prove custody/arm/monotonicity for
            # this experiment. Runtime safety still honors the existing line.
            return dict(result,status='source_gap',reason='protect_line_producer_unidentified')
        if count == 1 and not post_add_generation and (profit <= values.soft_stop_pct or
                           (finite(line) and line > 0 and bid <= line)):
            return dict(result, reason='pre_crossing_source_missing')
        worst = min(worst, profit)
        samples, quality = append_sample(samples,at=at,price=bid)
        if quality == 'capacity_censored':return dict(result,reason='sample_capacity_censored')
        decision = soft_decision(values,profit_pct=profit,now=at,touch_at=touch,
                                 enabled=row.get('grace_enabled',True),after_add=post_add_generation)
        touch = decision.touch_at
        if decision.rule == 'soft_recovered' and not post_add_generation: vote_hold = None
        rule = decision.rule if decision.disposition=='exit_candidate' else None
        if post_add_generation and rule != 'scalp_hard_stop_pct':
            from .holding_vote_exit_models import post_add_failure
            inputs=row.get('post_add_failure_inputs') or {}
            if (any(not finite(inputs.get(k)) for k in ('executed_at','floor','eval_sec','tick_acceleration'))
                or any(type(inputs.get(k)) is not bool for k in ('active','feature_usable','large_sell_print'))
                or inputs['executed_at']>at or inputs['eval_sec']<=0):
                return dict(result,status='source_gap',reason='post_add_failure_inputs_missing')
            rule='reversal_add_post_eval_fail' if inputs['active'] and post_add_failure(
                profit=profit,floor=inputs['floor'],elapsed=at-inputs['executed_at'],
                eval_sec=inputs['eval_sec'],feature_usable=inputs['feature_usable'],
                large_sell_print=inputs['large_sell_print'],tick_acceleration=inputs['tick_acceleration']) else None
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
