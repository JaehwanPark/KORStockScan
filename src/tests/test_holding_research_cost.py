"""Native cost/registry producers feed holding research without actual uplift."""
from copy import deepcopy
from datetime import datetime
import json

import pytest

from src.engine.lifecycle import holding_research_cost as adapter
from src.engine.lifecycle import broker_cost_allocation as allocation
from src.engine.lifecycle import broker_cost_source as official
from src.engine.lifecycle import research_input_budget as budget
from src.engine.lifecycle import research_storage as storage
from src.engine.automation import main_trailing_source_assembler as assembler
from src.engine.automation import main_trailing_all_scope_research as research
from src.engine.automation import main_trailing_research_diagnostics as diagnostic
from src.tests.test_broker_cost_allocation import position, source, DAY


def registry(root, item, monkeypatch):
    from src.trading.order import owner_custody_registry as registry
    monkeypatch.setattr(registry, 'broker_account_key', lambda **kwargs: 'test_account')
    owner = 'main_scalping:' + item['record_id']
    context = registry.OwnerOrderContext(owner_type='main_scalping', owner_id=owner,
        position_id=owner, client_intent_id='holding-cost-test-' + item['record_id'])
    ledger = registry.OrderOwnerRegistry(root/'runtime/order_owner_registry.jsonl')
    for leg in item['buy_legs']:
        intent = ledger.reserve(context=context, symbol=item['symbol'], side='BUY', quantity=leg['qty'],
            route=leg['route'], order_date=str(leg['at'])[:10])
        ledger.transition(intent,state='ORDER_BOUND',broker_order_no=leg['order_no'])
        ledger.record_fill(context=context,symbol=item['symbol'],side='BUY',order_quantity=leg['qty'],
            order_date=str(leg['at'])[:10],broker_order_no=leg['order_no'],cumulative_filled_qty=leg['qty'],
            cumulative_fill_amount=round(leg['qty']*leg['price']),execution_no=leg['execution_no'])


def fixture(tmp_path, monkeypatch):
    data, costs = tmp_path/'data', tmp_path/'costs'
    item = position(1)
    item['buy_legs'][0]['order_no']='0000011'
    registry(data,item,monkeypatch)
    trade = dict(id=1,code=item['symbol'],status='COMPLETED',strategy='SCALPING',
        main_automatic_management_allowed=False,buy_fill_legs=item['buy_legs'],sell_fill_legs=item['sell_legs'],
        sell_quantity_conserved=True,position_residual_qty=0,terminal_decision_authority='broker_sell_fill_observation_only',
        terminal_population_scope='real_record_bound',sell_time_forbidden_for_intraday_horizon=False,
        strict_completion_reasons=['source_gap_broker_actual_cost_missing'])
    observed = source(costs,buy_qty=2,sell_qty=2,buy_amount=20000,sell_amount=20200,cost=10)
    official.atomic(official.source_path(costs,DAY),observed)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        item['custody_rows'] = prepared._custody(trade,item['buy_legs'])
    receipts = allocation.build_research_cost_allocations({DAY:observed},[item])
    allocation.persist_research_costs(costs,DAY,receipts,[DAY])
    return data,costs,trade,receipts['1']


@pytest.mark.parametrize('mutation', ['future_owner', 'historical_owner', 'historical_date', 'historical_after_blank', 'rewrite', 'broken_chain'])
def test_closed_registry_prefix_accepts_only_unrelated_future_owners(tmp_path, monkeypatch, mutation):
    from datetime import date, timedelta
    data, costs, trade, _ = fixture(tmp_path, monkeypatch)
    path = data/'runtime/order_owner_registry.jsonl'
    if mutation == 'historical_after_blank':
        path.write_bytes(b'\n' + path.read_bytes())
    generation = adapter.byte_generation(path)
    future = (date.fromisoformat(DAY) + timedelta(days=1)).isoformat()
    with adapter.Source(data, cost_data_root=costs, registry_source_date=DAY) as prepared:
        original = prepared.record(trade, completion_date=DAY)
        if mutation == 'rewrite':
            path.write_bytes(path.read_bytes().replace(b'test_account', b'bad__account'))
        elif mutation == 'broken_chain':
            with path.open('a') as stream: stream.write('{}\n')
        else:
            from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerOrderContext
            owner = 'main_scalping:1' if mutation == 'historical_owner' else 'main_scalping:2'
            context = OwnerOrderContext(owner_type='main_scalping', owner_id=owner,
                position_id=owner, client_intent_id='later-' + mutation)
            OrderOwnerRegistry(path).reserve(context=context, symbol=trade['code'], side='BUY',
                quantity=1, route='KRX', order_date=DAY if mutation in {'historical_date', 'historical_after_blank'} else future)
        expected = mutation == 'future_owner'
        assert adapter.historical_registry_generation_matches(path, generation, DAY) is expected
        old = [{'path': str(path), 'generation': generation}]
        current = [{'path': str(path), 'generation': adapter.byte_generation(path)}]
        assert assembler.inventory_matches(data, DAY, old, current) is expected
        if expected:
            assert prepared.record(trade, completion_date=DAY) == original
            assert prepared.sources[str(path)] == generation


@pytest.mark.parametrize('protected,expected', [(None, False),
    (frozenset({'main_scalping:1'}), False),
    (frozenset({'main_scalping:2'}), True), (set(), False)])
def test_frozen_report_registry_scope_preserves_unrelated_carry_owners(
        tmp_path, monkeypatch, protected, expected):
    """An open carry's later order is not a closed research cohort member."""
    from datetime import date, timedelta
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerOrderContext
    data, _, trade, _ = fixture(tmp_path, monkeypatch)
    path = data/'runtime/order_owner_registry.jsonl'
    generation = adapter.byte_generation(path)
    owner = 'main_scalping:1'
    context = OwnerOrderContext(owner_type='main_scalping', owner_id=owner,
        position_id=owner, client_intent_id='later-carry-order')
    OrderOwnerRegistry(path).reserve(context=context, symbol=trade['code'], side='SELL',
        quantity=1, route='KRX',
        order_date=(date.fromisoformat(DAY)+timedelta(days=1)).isoformat())
    assert adapter.historical_registry_generation_matches(path, generation, DAY,
        protected_owners=protected) is expected



@pytest.mark.parametrize('case', ['prefix_terminal', 'prefix_retirement', 'future_terminal',
    'historical_terminal', 'orphan_terminal', 'changed_proof', 'new_retirement'])
def test_registry_prefix_resolves_native_dateless_events_without_ignoring_new_custody(tmp_path, monkeypatch, case):
    from datetime import date, timedelta
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerOrderContext, _terminal_proof
    data, _, trade, _ = fixture(tmp_path, monkeypatch)
    path = data/'runtime/order_owner_registry.jsonl'
    ledger = OrderOwnerRegistry(path)
    historical = next(iter(ledger._state(ledger.verified_events_snapshot()).values()))
    ledger.transition(historical['intent_id'], state='ORDER_TERMINAL', broker_order_no=historical['broker_order_no'])
    def reconcile(intent, changed=False):
        events = ledger.verified_events_snapshot()
        current = ledger._state(events)[intent]
        proof = _terminal_proof(current, 'a'*64)
        if changed: proof['order_date'] = '2000-01-01'
        ledger._append_locked(events, dict(event='TERMINAL_RECONCILIATION_RECORDED',
            intent_id=intent, account_key=current['account_key'], terminal_reconciliation=proof))
    if case == 'prefix_terminal': reconcile(historical['intent_id'])
    if case == 'prefix_retirement': ledger.retire_automatic_owners_to_manual()
    generation = adapter.byte_generation(path)
    future = (date.fromisoformat(DAY)+timedelta(days=1)).isoformat()
    context = OwnerOrderContext(owner_type='main_scalping',owner_id='main_scalping:2',
        position_id='main_scalping:2',client_intent_id='future-owner')
    intent = ledger.reserve(context=context,symbol=trade['code'],side='BUY',quantity=1,
                            route='KRX',order_date=future)
    ledger.transition(intent,state='ORDER_BOUND',broker_order_no='0000222')
    ledger.transition(intent,state='ORDER_TERMINAL',broker_order_no='0000222')
    if case in {'future_terminal', 'changed_proof'}: reconcile(intent, case=='changed_proof')
    elif case == 'historical_terminal': reconcile(historical['intent_id'])
    elif case == 'new_retirement': ledger.retire_automatic_owners_to_manual()
    elif case == 'orphan_terminal':
        ledger._append_locked(ledger.verified_events_snapshot(),dict(event='TERMINAL_RECONCILIATION_RECORDED',
            intent_id='unknown',account_key='test_account',terminal_reconciliation={}))
    assert adapter.historical_registry_generation_matches(path,generation,DAY) is (
        case in {'prefix_terminal','prefix_retirement','future_terminal'})


def test_native_registry_allocation_and_raw_source_are_bound_without_actual_mutation(tmp_path,monkeypatch):
    data,costs,trade,receipt = fixture(tmp_path,monkeypatch)
    original=deepcopy(trade);before=budget.health()['used_bytes']
    with adapter.Source(data,cost_data_root=costs) as prepared:
        result=prepared.record(trade,completion_date=DAY)
        assert result['status']=='research_cost_allocated',result
        assert result['allocated_net_pnl_krw']==190
        assert result['allocated_cost_krw']==10
        assert result['original_receipt_sha256']==receipt['receipt_sha256']
        assert result['economics_scope']=='main_holding_exit_research_only'
        assert result['original_economics_scope']=='initial_quantity_research_only'
        assert result['actual_execution_cost'] is result['selector_eligible'] is result['allowed_runtime_apply'] is False
        assert result['actual_pnl_krw'] is None
        assert result['original_automatic_management_allowed'] is False
        assert prepared.record(trade,completion_date=DAY)==result
        assert budget.health()['used_bytes']>before
    assert budget.health()['used_bytes']==before
    assert prepared.registry is None and not prepared.cache
    assert trade==original


@pytest.mark.parametrize('additional_reason',[None,'source_gap_duplicate_sell_execution','unknown_completion_reason'])
def test_native_missing_exact_cost_label_allows_allocated_research_only(tmp_path,monkeypatch,additional_reason):
    from src.tests.test_broker_cost_reconciliation import fixture as native_fixture
    from src.engine import sniper_trade_review_report as producer
    raw,events,_,_,_=native_fixture()
    raw.update(code='005930',rec_date=DAY)
    for event in events:
        event.timestamp=event.timestamp.replace('2026-10-08',DAY)
        event.code='005930'
        event.fields['order_no']={'B':'0000011','S':'0000012'}[event.fields['order_no']]
        event.fields['execution_no']={'B1':'101','S1':'102','S2':'103'}[event.fields['execution_no']]
    events[-1].fields.update(profit_rate=.8,
        main_lifecycle_execution_occurred_at=DAY+'T10:01:01+09:00')
    trade=producer._completed_trade_projection(raw,events,{})
    assert 'source_gap_exact_cost_missing' in trade['strict_completion_reasons']
    if additional_reason:trade['strict_completion_reasons'].append(additional_reason)
    original=deepcopy(trade);data,costs=tmp_path/'data',tmp_path/'costs'
    item=dict(record_id='1',symbol='005930',status='COMPLETED',terminal_observed=True,
        completion_observed_date=DAY,completed_at=DAY+'T10:01:01+09:00',
        buy_legs=trade['buy_fill_legs'],sell_legs=trade['sell_fill_legs'])
    registry(data,item,monkeypatch)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        item['custody_rows']=prepared._custody(trade,item['buy_legs'])
    observed=source(costs,buy_qty=2,sell_qty=2,buy_amount=20000,sell_amount=20200,cost=10)
    official.atomic(official.source_path(costs,DAY),observed)
    receipts=allocation.build_research_cost_allocations({DAY:observed},[item])
    allocation.persist_research_costs(costs,DAY,receipts,[DAY])
    with adapter.Source(data,cost_data_root=costs) as prepared:
        result=prepared.record(trade,completion_date=DAY)
    assert result['status']==('source_gap' if additional_reason else 'research_cost_allocated'),result
    assert result['allocated_net_pnl_krw']==(None if additional_reason else 190)
    assert result['actual_pnl_krw'] is None and result['selector_eligible'] is False
    assert trade==original


@pytest.mark.parametrize('damage',['unknown','raw_missing','raw_changed','receipt_changed','terminal','residual','duplicate','custody','future'])
def test_cost_gaps_never_become_zero_or_exact_cost(tmp_path,monkeypatch,damage):
    data,costs,trade,receipt=fixture(tmp_path,monkeypatch)
    cutoff=None
    if damage=='unknown':(costs/'runtime/initial_quantity_research_costs'/DAY/'index.json').unlink()
    elif damage=='raw_missing':official.source_path(costs,DAY).unlink()
    elif damage=='raw_changed':
        raw=json.loads(official.source_path(costs,DAY).read_text());raw['observed_at']=DAY+'T22:00:00+09:00'
        raw['source_sha256']=allocation.digest({k:v for k,v in raw.items() if k!='source_sha256'})
        official.atomic(official.source_path(costs,DAY),raw)
    elif damage=='receipt_changed':
        path=costs/'runtime/initial_quantity_research_costs'/DAY/'generations'/(allocation.digest(receipt)+'.json')
        raw=json.loads(path.read_text());raw['allocated_net_pnl_krw']=999
        raw['receipt_sha256']=allocation.digest({k:v for k,v in raw.items() if k!='receipt_sha256'})
        path.write_text(json.dumps(raw))
    elif damage=='terminal':trade['terminal_decision_authority']=None
    elif damage=='residual':trade['position_residual_qty']=1
    elif damage=='duplicate':trade['sell_fill_legs']*=2
    elif damage=='custody':(data/'runtime/order_owner_registry.jsonl').unlink()
    elif damage=='future':cutoff=datetime.fromisoformat(DAY+'T20:00:00+09:00').timestamp()
    before=budget.health()['used_bytes']
    with adapter.Source(data,cost_data_root=costs,knowledge_cutoff=cutoff) as prepared:
        result=prepared.record(trade,completion_date=DAY)
    assert result['status'] in {'source_gap','pending'},result
    assert result['allocated_net_pnl_krw'] is result['allocated_cost_krw'] is result['actual_pnl_krw'] is None
    assert budget.health()['used_bytes']==before


def test_late_cost_changes_overlay_only_and_generation_inventory(tmp_path,monkeypatch):
    data,costs,trade,_=fixture(tmp_path,monkeypatch)
    index=costs/'runtime/initial_quantity_research_costs'/DAY/'index.json';saved=index.read_bytes();index.unlink()
    original=deepcopy(trade)
    before=adapter.inventory(costs,[DAY])
    with adapter.Source(data,cost_data_root=costs) as prepared:
        missing=prepared.record(trade,completion_date=DAY)
    index.write_bytes(saved)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        arrived=prepared.record(trade,completion_date=DAY)
    assert missing['status']=='source_gap' and arrived['status']=='research_cost_allocated'
    assert before!=adapter.inventory(costs,[DAY]) and trade==original


def test_native_projection_to_assembly_replay_and_separate_cost_diagnostic(tmp_path,monkeypatch):
    from src.tests.test_main_trailing_source_assembler import _cf_original_ai_pipeline,TARGET
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    cf,_,old_manifest=_cf_original_ai_pipeline(tmp_path,monkeypatch,official_actual_cost=True,buy_order_number='0000011')
    root=tmp_path/'source';costs=tmp_path/'costs';out=tmp_path/'new-research';assembly=tmp_path/'new-assembly'
    raw=root/'report/monitor_snapshots'/f'trade_review_{DAY}.json'
    trade=_verified_trade_review_projection(raw,DAY,data_root=root)['sections']['completed_trade_projection'][0]
    item=dict(record_id='7',symbol='005930',status='COMPLETED',terminal_observed=True,completion_observed_date=DAY,
        completed_at=trade['exact_sell_fill_time'],buy_legs=trade['buy_fill_legs'],sell_legs=trade['sell_fill_legs'])
    registry(root,item,monkeypatch)
    with adapter.Source(root,cost_data_root=costs) as prepared:item['custody_rows']=prepared._custody(trade,item['buy_legs'])
    observed=official.load_source(root,DAY)
    official.atomic(official.source_path(costs,DAY),observed)
    receipts=allocation.build_research_cost_allocations({DAY:observed},[item])
    allocation.persist_research_costs(costs,DAY,receipts,[DAY])
    before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
    manifest=assembler.assemble(root,assembly,source_date=DAY,target_date=TARGET,start_date=DAY,
        as_of=old_manifest['as_of'],cost_data_root=costs)
    result=research.run(manifest,input_root=assembly,output_root=out,dry_run=False)
    report=diagnostic.build(manifest,input_root=assembly,report_path=out/f'research_{DAY}.json')
    assert report['holding_allocated_cost_status_counts']=={'research_cost_allocated':1}
    assert next(storage.iter_tree(out,report['holding_allocated_cost_rows_ref']))['allocated_net_pnl_krw']==1
    assert report['holding_allocated_cost_comparisons']
    assert all(r['actual_pnl_krw'] is None and r['selector_eligible'] is False
               for r in report['holding_allocated_cost_comparisons'])
    assert set(storage.iter_tree(out,result['common_population_evaluation']['common_ids_ref']))=={'7','alternative:7',cf['position_key']}
    assert report['selector_metrics_redefined'] is False
    from src.engine.automation.main_trailing_research_handoff import verify_report
    assert verify_report(out/f'research_{DAY}.json',target_date=TARGET)[0]==result
    assert all(p.read_bytes()==body for p,body in before.items())
    # A later external cost generation invalidates reuse without touching the
    # immutable native snapshot, selected policy, or existing completed report.
    path=official.source_path(costs,DAY);body=json.loads(path.read_text());body['observed_at']=DAY+'T23:00:00+09:00'
    body['source_sha256']=allocation.digest({k:v for k,v in body.items() if k!='source_sha256'})
    official.atomic(path,body)
    with pytest.raises(ValueError,match='inventory_changed'):
        verify_report(out/f'research_{DAY}.json',target_date=TARGET)


def test_official_revision_uses_new_receipt_without_resealing_old_trade(tmp_path,monkeypatch):
    data,costs,trade,_=fixture(tmp_path,monkeypatch)
    before=deepcopy(trade)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        old=prepared.record(trade,completion_date=DAY)
        custody=prepared._custody(trade,trade['buy_fill_legs'])
    value=source(costs,buy_qty=2,sell_qty=2,buy_amount=20000,sell_amount=20200,cost=20)
    official.atomic(official.source_path(costs,DAY),value)
    item=position(1);item['buy_legs']=trade['buy_fill_legs'];item['custody_rows']=custody
    receipts=allocation.build_research_cost_allocations({DAY:value},[item])
    allocation.persist_research_costs(costs,DAY,receipts,[DAY])
    with adapter.Source(data,cost_data_root=costs) as prepared:
        new=prepared.record(trade,completion_date=DAY)
    assert new['status']=='research_cost_allocated' and new['allocated_net_pnl_krw']==180
    assert old['allocated_net_pnl_krw']==190 and old['original_receipt_sha256']!=new['original_receipt_sha256']
    assert trade==before


def test_referenced_generations_only_and_fifo_fails_before_read(tmp_path,monkeypatch):
    import os
    data,costs,trade,_=fixture(tmp_path,monkeypatch)
    directory=costs/'runtime/initial_quantity_research_costs'/DAY/'generations'
    unreferenced=directory/('f'*64+'.json');unreferenced.write_text('{}')
    assert unreferenced not in adapter.inventory(costs,[DAY])
    path=official.source_path(costs,DAY);path.unlink();os.mkfifo(path)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        result=prepared.record(trade,completion_date=DAY)
    assert result['status']=='source_gap' and 'partition_required' in result['reason']


def test_same_batch_reuses_verified_cost_bytes_and_registry_but_detects_same_size_replacement(tmp_path,monkeypatch):
    import os
    data,costs,trade,_=fixture(tmp_path,monkeypatch)
    calls=[];native=adapter.byte_generation
    def observe(path):
        calls.append(str(path));return native(path)
    monkeypatch.setattr(adapter,'byte_generation',observe)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        first=prepared.record(trade,completion_date=DAY)
        assert first['status']=='research_cost_allocated'
        read_count=len(calls)
        for _ in range(20):assert prepared.record(trade,completion_date=DAY)==first
        assert len(calls)==read_count==4
        path=official.source_path(costs,DAY);before=path.stat();raw=path.read_bytes()
        replacement=path.with_suffix('.replacement');replacement.write_bytes(raw)
        os.utime(replacement,ns=(before.st_atime_ns,before.st_mtime_ns));replacement.replace(path)
        changed=prepared.record(trade,completion_date=DAY)
        assert changed['status']=='source_gap' and changed['reason']=='holding_research_cost_source_changed'


@pytest.mark.parametrize('which',['cost','registry'])
def test_cached_source_rejects_ancestor_alias_without_changing_original_inode(tmp_path,monkeypatch,which):
    data,costs,trade,_=fixture(tmp_path,monkeypatch)
    with adapter.Source(data,cost_data_root=costs) as prepared:
        assert prepared.record(trade,completion_date=DAY)['status']=='research_cost_allocated'
        directory=(costs if which=='cost' else data)/'runtime'
        moved=directory.with_name('retained-runtime');directory.rename(moved);directory.symlink_to(moved,target_is_directory=True)
        result=prepared.record(trade,completion_date=DAY)
        assert result['status']=='source_gap'
        assert result['reason']=='holding_research_cost_'+('source_changed' if which=='cost' else 'registry_changed')
