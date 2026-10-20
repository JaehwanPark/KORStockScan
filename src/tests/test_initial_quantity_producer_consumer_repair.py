"""Integration regressions for quantity source, clocks and frozen selection."""
import copy
import hashlib
import json
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.database.models import TradePerformanceFact, StrategyPositionPerformanceDaily
from src.engine.scalping import initial_quantity_policy as policy
from src.engine.scalping.initial_quantity_refresh_evaluation import cap_selection, execution_case
from src.tests.test_initial_quantity_policy import _cap_context, _quality, _facts, _event
from src.tests.test_initial_quantity_timeout import _research_trade_path


@pytest.mark.parametrize('population', ['source_quality_by_entry_date', 'source_quality_by_exit_date'])
def test_refresh_refuses_preflight_replaced_by_final_quality(tmp_path, population):
    source = tmp_path / 'quality.json'
    source.write_text(json.dumps(dict(status='warning', tuning_input_allowed=True, phase='preflight')))
    binding = dict(artifact=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    report = dict(census={population: {'2026-10-19': binding}})
    policy.verify_refresh_source_generations(report)
    source.write_text(json.dumps(dict(status='warning', tuning_input_allowed=True, phase='final')))
    with pytest.raises(ValueError, match='quantity_source_quality_generation_changed'):
        policy.verify_refresh_source_generations(report)
    binding['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    policy.verify_refresh_source_generations(report)


@pytest.mark.parametrize('late_identity', [False, True])
@pytest.mark.parametrize('padding', ['x' * 150000, '\uac00' * 30000])
def test_oversized_unrelated_pipeline_row_preserves_next_record(late_identity, padding):
    import io
    fields = {'record_id': None, 'fields': {'payload': padding}}
    if late_identity:
        fields = dict(reversed(list(fields.items())))
    relevant = json.dumps({'record_id': 7, 'fields': {}}) + '\n'
    source = relevant + json.dumps(fields, ensure_ascii=False) + '\n' + relevant
    receipt = {}
    assert list(policy._quantity_pipeline_rows(io.StringIO(source), {'7': []}, receipt)) == [relevant, relevant]
    assert receipt == {'oversized_out_of_cohort_records': 1}


@pytest.mark.parametrize('identity', ['', '"record_id":null,"record_id":8,'])
def test_oversized_unidentified_pipeline_row_stays_blocked(identity):
    import io
    source = '{' + identity + '"fields":{"payload":"' + 'x' * 150000 + '"}}\n'
    with pytest.raises(ValueError):
        list(policy._quantity_pipeline_rows(io.StringIO(source), {'7': []}, {}))


def test_oversized_relevant_row_marks_only_identified_trade_unusable(tmp_path):
    day = '2026-10-08'
    _quality(tmp_path, day)
    pipeline = tmp_path/'pipeline_events'; pipeline.mkdir()
    oversized = json.dumps(dict(record_id=1, fields=dict(payload='x'*150000)))
    (pipeline/f'pipeline_events_{day}.jsonl').write_text(oversized+'\n{}\n')
    rows, _ = policy.completed_trade_fact_census(day, data_dir=tmp_path,
        fact_rows=[actual_fact(1), actual_fact(2)], entry_on_or_after='2026-09-29')
    receipts = {}
    paths = policy._join_post_fill_paths_uncached(rows, data_dir=tmp_path, source_receipts=receipts)
    for row in rows:
        path = paths[row['trade_id']]
        assert path['source_gap'] == (['pipeline_record_partition_required'] if row['record_id']=='1' else [])
        if row['record_id']=='1':
            assert policy._paired_candidate(row, path, 'two_leg_0_1tick')['status']=='path_source_gap'
            assert policy._paired_candidate(row, path, 'parent')['status']=='paired'
    assert receipts[day]['oversized_in_cohort_record_ids']==['1']


@pytest.mark.parametrize('late_identity', [False, True])
@pytest.mark.parametrize('padding', ['x' * 150000, '\uac00' * 50000])
def test_large_native_quantity_row_preserves_policy_fields(late_identity, padding):
    import io
    fields = dict(entry_execution_sizing_valid=True,
                  entry_submit_attempt_id='attempt', entry_execution_sizing_plan_sha256='a'*64,
                  position_sizing_policy_status='initial_policy_v2_loaded',
                  position_sizing_policy_sha256='b'*64, initial_quantity_runtime_pid='123',
                  initial_quantity_cap_research_context=json.dumps(_cap_context()),
                  unused_context=padding)
    fields.update({f'unused_{n}': n for n in range(300)})
    row = dict(record_id=7, stock_code='005930', stage='entry_execution_sizing_plan',
               emitted_at='2026-10-16T09:00:00+09:00', fields=fields)
    if late_identity:
        row = dict(reversed(list(row.items())))
    receipt = {}
    parsed = [json.loads(value) for value in policy._quantity_pipeline_rows(
        io.StringIO(json.dumps(row, ensure_ascii=False)+'\n'), {'7': []}, receipt)]
    assert len(parsed)==1 and parsed[0]['record_id']==7
    assert parsed[0]['fields']=={k:v for k,v in fields.items() if k in policy._QUANTITY_PIPELINE_FIELDS}
    assert receipt==dict(oversized_projected_rows=1, oversized_projection_contract='quantity_execution_fields_v1')


def test_large_quantity_decision_keeps_exact_sent_fill_policy_join(tmp_path):
    day='2026-10-08'
    _quality(tmp_path,day)
    pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    path=pipeline/f'pipeline_events_{day}.jsonl'
    def event(stage, clock, **fields):
        return dict(record_id=1,stock_code='005930',stage=stage,emitted_at=day+'T'+clock+'+09:00',fields=fields)
    identity=dict(entry_submit_attempt_id='exact-attempt',entry_execution_sizing_plan_sha256='a'*64)
    events=[event('entry_execution_sizing_plan','09:29:59',**identity,
                  entry_execution_sizing_valid=True,position_sizing_policy_status='initial_policy_v2_loaded',
                  position_sizing_policy_sha256='b'*64,initial_quantity_runtime_pid='123'),
            event('order_leg_sent','09:29:59.500000',**identity,tag='entry_leg',
                  actual_order_submitted=True,broker_order_no='11'),
            event('position_rebased_after_fill','09:30:00',entry_mode='normal',
                  fill_price=100000,fill_qty=1,order_no='11',execution_no='1',actual_execution_venue='KRX',
                  broker_execution_observed_at=day+'T09:30:00+09:00')]
    rows,_=policy.completed_trade_fact_census(day,data_dir=tmp_path,fact_rows=[actual_fact()],entry_on_or_after='2026-09-29')
    path.write_text(''.join(json.dumps(row)+'\n' for row in events))
    expected=policy._join_post_fill_paths_uncached(rows,data_dir=tmp_path)
    events[0]['fields']['unused_large_context']='x'*200000
    path.write_text(''.join(json.dumps(row)+'\n' for row in events))
    receipts={}
    actual=policy._join_post_fill_paths_uncached(rows,data_dir=tmp_path,source_receipts=receipts)
    assert actual==expected
    joined=policy._paired_candidate(rows[0],actual['fact:1'],'parent')
    assert joined['applied_policy_file_sha256']=='b'*64
    assert joined['applied_policy_runtime_pid']=='123'
    assert joined['policy_decision_stage']=='entry_execution_sizing_plan'
    assert not actual['fact:1']['source_gap']
    assert receipts[day]['oversized_projected_rows']==1


def test_large_required_quantity_field_remains_an_identified_gap():
    import io
    row=dict(record_id=7,stock_code='005930',stage='entry_execution_sizing_plan',
             emitted_at='2026-10-16T09:00:00+09:00',
             fields=dict(initial_quantity_cap_research_context='x'*150000))
    receipt={}
    assert list(policy._quantity_pipeline_rows(io.StringIO(json.dumps(row)+'\n'),{'7':[]},receipt))==[]
    assert receipt['oversized_in_cohort_record_ids']==['7']


def test_native_fact_sync_preserves_null_real_zero_and_provenance(monkeypatch,tmp_path):
    from src.engine import strategy_position_performance_report as mod
    from src.engine.scalping import scale_in_split_order_plan as scale
    engine=create_engine('sqlite:///:memory:')
    TradePerformanceFact.__table__.create(engine)
    StrategyPositionPerformanceDaily.__table__.create(engine)
    class DB:
        def init_db(self):pass
        def analyze_performance_tables(self):pass
        @contextmanager
        def get_session(self):
            with Session(engine) as session, session.begin():yield session
    day='2026-10-08'
    facts=[]
    for rid,value in ((1,None),(2,0)):
        facts.append(dict(recommendation_id=rid,rec_date=date.fromisoformat(day),stock_code='005930',strategy='SCALPING',position_tag='SCANNER',status='COMPLETED',buy_price=100,buy_qty=1,sell_price=100,buy_time=datetime(2026,10,8,9),sell_time=datetime(2026,10,8,10),profit_rate=value,realized_pnl_krw=value,
                          economics_source_status='unresolved' if value is None else 'broker_actual_cost_reconciled',actual_cost_reconciliation_status='actual_cost_reconciled' if value==0 else 'cost_source_unavailable',actual_cost_source_generation='generation',completion_census_run_id='run',completion_census_projection_sha256='projection',broker_actual_fees_taxes_krw=value))
    monkeypatch.setattr(mod,'_DB',DB())
    monkeypatch.setattr(mod,'_FACT_SYNC_STATUS_DIR',tmp_path)
    monkeypatch.setattr(mod,'_build_trade_fact_rows',lambda *a,**k:(facts,[]))
    monkeypatch.setattr(scale,'_query_actual_fill_inventory',lambda *a:[])
    result=mod.sync_trade_performance_for_date(day)
    assert result['status']=='succeeded'
    with Session(engine) as session:
        a=session.get(TradePerformanceFact,1);b=session.get(TradePerformanceFact,2)
        assert (a.profit_rate,a.realized_pnl_krw)==(None,None)
        assert (b.profit_rate,b.realized_pnl_krw)==(0,0)
        assert b.actual_cost_source_generation=='generation'
        assert b.broker_actual_fees_taxes_krw==0
        summary=session.get(StrategyPositionPerformanceDaily,(date.fromisoformat(day),'SCALPING','SCANNER'))
        assert summary.realized_pnl_krw==0


def actual_fact(rid=1,day='2026-10-08',fees=200):
    return dict(recommendation_id=rid,rec_date=day,stock_code='005930',strategy='SCALPING',position_tag='SCANNER',status='COMPLETED',buy_price=100000,buy_qty=1,sell_price=101000,buy_time=day+'T09:30:00+09:00',sell_time=day+'T10:00:00+09:00',profit_rate=(1000-fees)/1000,realized_pnl_krw=1000-fees,
                economics_source_status='broker_actual_cost_reconciled',actual_cost_reconciliation_status='actual_cost_reconciled',actual_cost_source_generation='a'*64,completion_census_run_id='run',completion_census_projection_sha256='b'*64,broker_actual_fees_taxes_krw=fees)


def test_actual_cost_census_accepts_broker_cost_not_configured_rate(tmp_path):
    fact=actual_fact();_quality(tmp_path,'2026-10-08')
    rows,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[fact],entry_on_or_after='2026-09-29')
    assert len(rows)==1 and rows[0]['realized_net_pnl_krw']==800
    assert rows[0]['cost_basis']=='broker_actual'
    assert rows[0]['modeled_parent_net_pnl_krw']!=800
    bad={**fact,'completion_census_run_id':None}
    good,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[fact,{**bad,'recommendation_id':2}],entry_on_or_after='2026-09-29')
    assert len(good)==1 and census['excluded']=={'actual_cost_identity_or_amount_invalid':1}


@pytest.mark.parametrize('issued_physical', [False, True])
@pytest.mark.parametrize('damage', [None, 'seal', 'physical', 'logical', 'ctime', 'authority', 'receipt_symlink', 'issued_sha', 'issued_size', 'issued_path', 'issued_cost'])
def test_native_pipeline_gzip_preserves_issued_quantity_timeout_generation(tmp_path, monkeypatch, damage, issued_physical):
    import gzip
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research, timeout_research_valid
    from src.engine.scalping.micro_reversion.economic_reference import content_sha256
    day='2026-10-08'; _quality(tmp_path,day)
    monkeypatch.setattr(policy,'DATA_DIR',tmp_path)
    pipeline=tmp_path/'pipeline_events'/f'pipeline_events_{day}.jsonl'
    pipeline.parent.mkdir(); original=b'{}\n'; pipeline.write_bytes(original)
    fact=actual_fact()
    before=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=[fact],entry_on_or_after='2026-09-29')
    timeout=build_timeout_research(day,data_dir=tmp_path,fact_rows=before['census']['input_fact_rows'],
                                   entry_on_or_after='2026-09-29',replay=before)
    assert timeout_research_valid(timeout,replay=before)
    archived=Path(str(pipeline)+'.gz'); archived.write_bytes(gzip.compress(original)); pipeline.unlink()
    info=archived.stat()
    if issued_physical:
        # An issued legacy report can bind gzip bytes while its successor
        # reader binds the native archiver's identical logical input.
        before['pipeline_source_receipts'][day].update(path=str(archived),size_bytes=info.st_size,
            sha256=hashlib.sha256(archived.read_bytes()).hexdigest(),archive_identity_valid=True)
        if damage=='issued_sha':before['pipeline_source_receipts'][day]['sha256']='0'*64
        if damage=='issued_size':before['pipeline_source_receipts'][day]['size_bytes']+=1
        if damage=='issued_path':before['pipeline_source_receipts'][day]['path']=str(archived.with_name('other.gz'))
        if damage=='issued_cost':before['census']['cost_rate']+=0.001
        before['report_content_sha256']=policy._digest({k:v for k,v in before.items() if k!='report_content_sha256'})
        timeout['pipeline_source_receipts']=copy.deepcopy(before['pipeline_source_receipts'])
        timeout['joint_replay_content_sha256']=before['report_content_sha256']
        timeout['report_content_sha256']=policy._digest({k:v for k,v in timeout.items() if k!='report_content_sha256'})
    receipt=dict(schema='pipeline_raw_archive_identity_v1',logical_path=str(pipeline),
        logical_content_sha256=hashlib.sha256(original).hexdigest(),logical_size_bytes=len(original),
        archive_generation=dict(device=info.st_dev,inode=info.st_ino,size_bytes=info.st_size,
                                mtime_ns=info.st_mtime_ns,ctime_ns=info.st_ctime_ns),
        verification_contract='logical_sha256_size_crc_to_eof_v1',runtime_effect=False,allowed_runtime_apply=False)
    if issued_physical:
        from src.engine.automation.main_trailing_source_store import migrate_frozen_source
        receipt['artifact_content_sha256']=content_sha256(receipt)
        Path(str(archived)+'.archive_receipt.json').write_text(json.dumps(receipt))
        migrate_frozen_source(tmp_path,pipeline)
        del receipt['artifact_content_sha256']
    if damage=='logical':receipt['logical_content_sha256']='0'*64
    if damage=='ctime':receipt['archive_generation']['ctime_ns']+=1
    if damage=='authority':receipt['allowed_runtime_apply']=True
    receipt['artifact_content_sha256']=content_sha256(receipt)
    if damage=='seal':receipt['artifact_content_sha256']='0'*64
    receipt_path=Path(str(archived)+'.archive_receipt.json');receipt_path.write_text(json.dumps(receipt))
    if damage=='physical':archived.write_bytes(gzip.compress(original+b'{}\n'))
    if damage=='receipt_symlink':
        saved=receipt_path.with_suffix('.saved');receipt_path.rename(saved);receipt_path.symlink_to(saved)
    if damage=='receipt_symlink':
        with pytest.raises(ValueError,match='window_dependency_path_invalid'):
            policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=before['census']['input_fact_rows'],entry_on_or_after='2026-09-29')
        assert not timeout_research_valid(timeout,replay=before)
        return
    after=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=before['census']['input_fact_rows'],entry_on_or_after='2026-09-29')
    if damage is None or not issued_physical and damage.startswith('issued_'):
        if not issued_physical:assert after==before
        assert timeout_research_valid(timeout,replay=before)
    else:
        assert after!=before
        assert not timeout_research_valid(timeout,replay=before)
    assert gzip.decompress(archived.read_bytes())==(original+b'{}\n' if damage=='physical' else original)


def _allocated_quantity_fact(tmp_path, *, record_id=7):
    from src.tests.test_broker_cost_source import broker_fixture
    from src.engine.lifecycle.broker_cost_allocation import build_research_cost_allocations
    source, context, _, _ = broker_fixture(tmp_path)
    context['custody_rows'][0]['filled_qty'] = 2
    context['custody_rows'][0].update(record_id=record_id, owner_id=f'main_scalping:{record_id}')
    position = dict(record_id=str(record_id), symbol='005930', status='COMPLETED', terminal_observed=True,
        buy_legs=context['buy_legs'], sell_legs=context['sell_legs'], custody_rows=context['custody_rows'],
        completed_at='2026-10-08T10:01:00+09:00', completion_observed_date='2026-10-08')
    receipt = build_research_cost_allocations({'2026-10-08': source}, [position])[str(record_id)]
    assert receipt['status'] == 'research_cost_allocated', receipt.get('reason')
    from src.engine.lifecycle.broker_cost_allocation import persist_research_costs
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    persist_research_costs(tmp_path, '2026-10-08', {str(record_id): receipt}, ['2026-10-08'])
    return {**actual_fact(record_id), 'buy_price': 10000, 'buy_qty': 2, 'sell_price': 10100,
            'buy_time': '2026-10-08T10:00:00+09:00', 'sell_time': '2026-10-08T10:01:00+09:00',
            'profit_rate': None, 'realized_pnl_krw': None, 'broker_actual_fees_taxes_krw': None,
            'economics_source_status': 'source_gap_broker_actual_cost_missing',
            'actual_cost_reconciliation_status': 'actual_cost_unallocated', 'quantity_research_cost': receipt,
            'actual_cost_source_generation': source_generation(tmp_path, '2026-10-08')}


def _fractional_allocated_quantity_fact(tmp_path, *, record_id=7):
    from src.engine.lifecycle import broker_cost_source as official, broker_cost_allocation as allocation
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    day = '2026-10-08'
    def transport(api, payload):
        result = {'return_code': 0}
        if api == 'ka00001': result['acctNo'] = '1234567890'
        elif api == 'ka10170': result[official.LISTS[api]] = [dict(stk_cd='005930', buy_qty='3', sell_qty='3',
            buy_amt='30050', sell_amt='30100', cmsn_alm_tax='10', pl_amt='40')]
        else: result['trst_ovrl_trde_prps_array' if api == 'kt00015' else official.LISTS[api]] = []
        return [result], dict(page_count=1, continuous_terminal_received=True)
    source = official.collect(tmp_path, day, transport=transport, now=datetime.fromisoformat(day+'T21:00:00+09:00'))
    def leg(side, second, qty, price, execution):
        return dict(at=f'{day}T10:0{int(side == "SELL")}:{second:02d}+09:00', qty=qty, price=price,
            order_no=str(record_id*2+int(side == 'SELL')), execution_no=str(execution), route='KRX')
    position = dict(record_id=str(record_id), symbol='005930', status='COMPLETED', terminal_observed=True,
        fact_buy_price=10017, fact_sell_price=10033, completed_at=day+'T10:01:02+09:00',
        completion_observed_date=day, buy_legs=[leg('BUY', 0, 2, 10000, 1), leg('BUY', 1, 1, 10050, 2)],
        sell_legs=[leg('SELL', 0, 1, 10000, 3), leg('SELL', 1, 1, 10000, 4), leg('SELL', 2, 1, 10100, 5)],
        custody_rows=[dict(record_id=record_id, owner_type='main_scalping', owner_id=f'main_scalping:{record_id}',
            account_key='test_account', state='full', filled_qty=3, source_quality_reasons=[])])
    receipt = allocation.build_research_cost_allocations({day: source}, [position])[str(record_id)]
    assert receipt['status'] == 'research_cost_allocated', receipt
    allocation.persist_research_costs(tmp_path, day, {str(record_id): receipt}, [day])
    return {**actual_fact(record_id), 'buy_price': 10017, 'buy_qty': 3, 'sell_price': 10033,
        'buy_time': day+'T10:00:00+09:00', 'sell_time': day+'T10:01:02+09:00',
        'profit_rate': None, 'realized_pnl_krw': None, 'broker_actual_fees_taxes_krw': None,
        'economics_source_status': 'source_gap_broker_actual_cost_missing',
        'actual_cost_reconciliation_status': 'actual_cost_unallocated', 'quantity_research_cost': receipt,
        'actual_cost_source_generation': source_generation(tmp_path, day)}


def test_fractional_partial_fill_ledger_economics_preserves_integer_fact_reference(tmp_path):
    fact = _fractional_allocated_quantity_fact(tmp_path)
    original = copy.deepcopy(fact)
    _quality(tmp_path, '2026-10-08')
    rows, _ = policy.completed_trade_fact_census('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    assert len(rows) == 1 and rows[0]['realized_net_pnl_krw'] == 40
    assert rows[0]['buy_price'] == 30050/3 and rows[0]['sell_price'] == 30100/3
    assert fact == original and fact['profit_rate'] is None and fact['sell_price'] == 10033
    report = policy.build_initial_quantity_replay('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    assert report['trades'][0]['original_notional_krw'] == 30050
    assert report['trades'][0]['modeled_parent_net_pnl_krw'] == pytest.approx(
        50-30100*report['census']['cost_rate'])
    assert policy.initial_replay_economics_valid(report)
    assert policy._quantity_research_fact_cost({**fact, 'sell_price': 10034})['status'] == 'research_cost_invalid'
    forged = copy.deepcopy(report)
    forged['trades'][0]['original_notional_krw'] = 30051
    forged['report_content_sha256'] = policy._digest({k:v for k,v in forged.items() if k != 'report_content_sha256'})
    assert policy.initial_replay_economics_valid(forged) is False


def _multidate_quantity_receipt(tmp_path):
    from src.engine.lifecycle import broker_cost_source as official, broker_cost_allocation as allocation
    days = [(date(2026, 9, 29)+timedelta(days=i)).isoformat() for i in range(18)
            if (date(2026, 9, 29)+timedelta(days=i)).weekday() < 5]
    qty = len(days)
    sources = {}
    for day in days:
        def transport(api, payload):
            result = {'return_code': 0}
            if api == 'ka00001': result['acctNo'] = '1234567890'
            elif api == 'ka10170': result[official.LISTS[api]] = [dict(stk_cd='005930',
                buy_qty=str(qty*8 if day == days[0] else 0), sell_qty='8',
                buy_amt=str(qty*80000 if day == days[0] else 0), sell_amt='80800',
                cmsn_alm_tax='8', pl_amt='792')]
            else: result['trst_ovrl_trde_prps_array' if api == 'kt00015' else official.LISTS[api]] = []
            return [result], dict(page_count=1, continuous_terminal_received=True)
        sources[day] = official.collect(tmp_path, day, transport=transport,
            now=datetime.fromisoformat(day+'T21:00:00+09:00'))
    position = dict(record_id='1', symbol='005930', status='COMPLETED', terminal_observed=True,
        completion_observed_date=days[-1], completed_at=days[-1]+'T10:01:00+09:00',
        buy_legs=[dict(at=days[0]+'T10:00:00+09:00', qty=qty, price=10000, order_no='1', execution_no='1', route='KRX')],
        sell_legs=[dict(at=day+'T10:01:00+09:00', qty=1, price=10100, order_no=str(i+2),
            execution_no=str(i+2), route='KRX') for i,day in enumerate(days)],
        custody_rows=[dict(record_id=1, owner_type='main_scalping', owner_id='main_scalping:1',
            account_key='test_account', state='full', filled_qty=qty, source_quality_reasons=[])])
    positions = []
    for rid in range(1, 9):
        item = copy.deepcopy(position)
        item['record_id'] = str(rid)
        item['custody_rows'][0].update(record_id=rid, owner_id=f'main_scalping:{rid}')
        for index, leg in enumerate(item['buy_legs']+item['sell_legs']):
            leg.update(order_no=str(rid*100+index), execution_no=str(rid*100+index))
        positions.append(item)
    position = positions[0]
    receipt = allocation.build_research_cost_allocations(sources, positions)['1']
    assert receipt['status'] == 'research_cost_allocated', receipt
    assert allocation.validate_research_cost(receipt, record_id='1', symbol='005930',
        buy_legs=position['buy_legs'], sell_legs=position['sell_legs'], custody_rows=position['custody_rows'],
        completion_date=days[-1]) == receipt
    assert 16*1024 < len(json.dumps(receipt).encode()) < allocation.CACHED_RECEIPT_MAX_BYTES
    allocation.persist_research_costs(tmp_path, days[-1], {'1': receipt}, days)
    return receipt


@pytest.mark.parametrize('oversize', [False, True])
def test_native_original_streams_bound_multidate_quantity_receipt_by_its_own_contract(tmp_path, monkeypatch, oversize):
    from src.engine import strategy_position_performance_report as native
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    from src.engine.lifecycle.broker_cost_allocation import CACHED_RECEIPT_MAX_BYTES
    receipt = _multidate_quantity_receipt(tmp_path)
    day = receipt['completion_observed_date']
    if oversize: receipt = {**receipt, 'untrusted_padding': 'x'*CACHED_RECEIPT_MAX_BYTES}
    _, path = _quantity_completion_overlay_fixture(tmp_path, monkeypatch, day=day, identity=dict(
        rec_date=receipt['sources'][0]['source_date'], buy_price=10000, buy_qty=receipt['buy_qty'],
        buy_time=receipt['sources'][0]['source_date']+'T10:00:00+09:00', sell_price=10100,
        sell_time=receipt['completed_at'], completion_observed_date=day, quantity_research_cost=receipt),
        meta_overrides=dict(completed_census_input_sha256='c'*64, completion_event_id_count=1,
            trailing_event_source_receipts=[dict(path='fixture-completion-source', sha256='a'*64)]))
    sidecar = path.with_suffix('.completed_projection.json')
    source = json.loads(sidecar.read_bytes())
    native_reference = dict(census_sha256=digest(source['meta']['completed_census_manifest']),
        projection=dict(snapshot_identity=source['snapshot_identity']))
    if oversize:
        with pytest.raises(ValueError, match='research_legacy_json_field_partition_required'):
            native._stream_original_fact_projection(day, path, sidecar, native_reference)
        with pytest.raises(native.FactSyncSourceError, match='selected_metadata_partition_required'):
            native._legacy_original_stream(sidecar, day)
    else:
        scalar = native._stream_original_fact_projection(day, path, sidecar, native_reference)
        assert scalar['sections']['completed_trade_projection'][0]['quantity_research_cost'] == receipt
        original = native._legacy_original_stream(sidecar, day)
        assert original['sections']['completed_trade_projection'][0]['quantity_research_cost'] == receipt
        assert scalar['sections']['completed_trade_projection'][0]['profit_rate'] is None


def test_quantity_allocated_research_cost_never_rewrites_canonical_actual_economics(tmp_path):
    fact = _allocated_quantity_fact(tmp_path)
    original = copy.deepcopy(fact)
    _quality(tmp_path, '2026-10-08')
    rows, census = policy.completed_trade_fact_census('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    assert fact == original and census['input_fact_rows'][0] == original
    assert len(rows) == 1 and rows[0]['realized_net_pnl_krw'] == 190
    assert rows[0]['profit_rate'] == .95
    assert rows[0]['cost_basis'] == 'broker_confirmed_total_allocated'
    assert rows[0]['actual_execution_cost'] is False
    assert census['actual_completed_net_pnl_krw'] is None
    assert census['actual_completed_mean_profit_rate_pct'] is None
    assert census['research_completed_net_pnl_krw'] == 190
    assert census['actual_execution_cost_complete'] is False
    assert original['profit_rate'] is None and original['realized_pnl_krw'] is None


@pytest.mark.parametrize('fault', ['owner', 'actual_flag', 'seal', 'amount', 'partial_fact', 'completion', 'missing_binding'])
def test_quantity_allocated_research_cost_rejects_identity_amount_and_authority_gaps(tmp_path, fault):
    from src.engine.lifecycle.broker_cost_reconciliation import digest
    fact = _allocated_quantity_fact(tmp_path)
    receipt = fact['quantity_research_cost']
    if fault == 'owner': receipt['owner'] = 'manual'
    elif fault == 'actual_flag': receipt['actual_execution_cost'] = True
    elif fault == 'amount': receipt['allocated_net_pnl_krw'] = 99999
    elif fault == 'partial_fact': fact['buy_qty'] = 1
    elif fault == 'completion': fact['completion_source_date'] = '2026-10-09'
    elif fault == 'missing_binding': fact['completion_census_run_id'] = None
    if fault == 'seal': receipt['receipt_sha256'] = 'f'*64
    else: receipt['receipt_sha256'] = digest({k:v for k,v in receipt.items() if k != 'receipt_sha256'})
    rows, census = policy.completed_trade_fact_census('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    assert rows == []
    assert sum(census['excluded'].values()) == 1
    assert census['actual_completed_net_pnl_krw'] is None


@pytest.mark.parametrize('fault', ['absent_index', 'receipt_seal', 'receipt_content', 'source_logical', 'source_missing'])
def test_quantity_cost_admission_requires_native_record_and_original_source_generation(tmp_path, fault):
    fact = _allocated_quantity_fact(tmp_path)
    generation = fact['actual_cost_source_generation']['quantity_research_cost_generation']
    if fault == 'absent_index': fact['actual_cost_source_generation'].pop('quantity_research_cost_generation')
    elif fault == 'receipt_seal': generation['receipts'][0]['receipt_sha256'] = 'f'*64
    elif fault == 'receipt_content': generation['receipts'][0]['content_sha256'] = 'f'*64
    elif fault == 'source_logical': generation['source_dates'][0]['source_sha256'] = 'f'*64
    else: generation['source_dates'] = []
    rows, census = policy.completed_trade_fact_census('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    assert rows == [] and census['excluded'] == {'quantity_research_cost_invalid': 1}


@pytest.mark.parametrize('fault', ['generation_sha', 'scope', 'record', 'parent', 'research_sha'])
def test_quantity_cost_admission_rejects_unbound_compact_record_generations(tmp_path, fault):
    from src.engine.lifecycle.broker_cost_reconciliation import record_source_projector
    fact = _allocated_quantity_fact(tmp_path)
    fact['actual_cost_source_generation'] = record_source_projector(fact['actual_cost_source_generation'])(
        str(fact['recommendation_id']), fact['quantity_research_cost'])
    assert policy._quantity_research_fact_cost(fact)['status'] == 'research_cost_allocated'
    generation = fact['actual_cost_source_generation']
    research = generation['quantity_research_cost_generation']
    if fault == 'generation_sha': generation['sha256'] = 'invalid'
    elif fault == 'scope': research['projection_scope'] = 'unknown'
    elif fault == 'record': research['record_id'] = '999'
    elif fault == 'parent': research['parent_generation_sha256'] = 'f'*64
    else: research['research_generation_sha256'] = 'invalid'
    assert policy._quantity_research_fact_cost(fact)['status'] == 'research_cost_invalid'


def test_allocated_cost_replay_preserves_positive_weights_and_same_comparison_costs(tmp_path):
    fact = _allocated_quantity_fact(tmp_path)
    _quality(tmp_path, '2026-10-08')
    report = policy.build_initial_quantity_replay('2026-10-08', data_dir=tmp_path,
        fact_rows=[fact], entry_on_or_after='2026-09-29')
    row = report['trades'][0]
    assert row['actual_net_pnl_krw'] == 190 and row['actual_execution_cost'] is False
    assert report['selections']['SAFE_UNKNOWN']['winner_weight_sum_krw'] == 190
    assert row['modeled_parent_net_pnl_krw'] != row['actual_net_pnl_krw']
    assert row['quantity_research_cost'] == fact['quantity_research_cost']
    assert policy.initial_replay_economics_valid(report)
    forged = copy.deepcopy(report)
    forged['trades'][0]['actual_execution_cost'] = True
    forged['report_content_sha256'] = policy._digest({k:v for k,v in forged.items() if k != 'report_content_sha256'})
    assert policy.initial_replay_economics_valid(forged) is False
    from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate, VERSION
    with pytest.raises(ValueError, match='refresh_research_cost_requires_v3_selection'):
        evaluate(report, parent_policy={}, evaluation_algorithm=VERSION)


@pytest.mark.parametrize('case,expected', [('empty', None), ('missing_cost', None),
                                         ('measured_zero', 0), ('partial_valid', 800)])
def test_actual_census_keeps_missing_aggregate_distinct_from_measured_zero(tmp_path, case, expected):
    day = '2026-10-08'
    _quality(tmp_path, day)
    missing = {**actual_fact(2), 'profit_rate': None, 'realized_pnl_krw': None}
    zero = {**actual_fact(fees=0), 'sell_price': 100000, 'profit_rate': 0,
            'realized_pnl_krw': 0}
    facts = {'empty': [], 'missing_cost': [missing], 'measured_zero': [zero],
             'partial_valid': [actual_fact(), missing]}[case]
    rows, census = policy.completed_trade_fact_census(day, data_dir=tmp_path,
        fact_rows=facts, entry_on_or_after='2026-09-29')
    assert census['actual_completed_net_pnl_krw'] == expected
    assert census['all_completed_initial_trades'] == len(rows)
    assert (census['actual_completed_mean_profit_rate_pct'] is None) == (not rows)


@pytest.mark.parametrize('value,expected',[('4',4),(4,4),(True,None),('4.0',None),(4.0,None),('',None),('nan',None),('-1',None),('0',0)])
def test_epoch_is_canonical_and_never_default_zero(value,expected):
    assert policy.canonical_epoch(value)==expected


def test_wire_epoch_connects_and_same_execution_has_zero_modeled_delta():
    start=datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    context=_cap_context(actual_qty=2)
    context['ask_depth_source']=dict(source_type='ws_0D_bound_snapshot',market_route='KRX',transport_epoch=4,observed_epoch=start-1,item='005930',levels=[dict(price_krw=101,quantity=2)])
    source=dict(context=context,attempt_id='attempt',plan_sha256='a'*64,fills=[dict(at='2026-10-08T09:30:00+09:00',price=100,qty=1,venue='KRX')],following_ticks=[dict(observed_epoch=start+1,price_krw=101,quantity=2,item='005930',depth_item='005930',market_route='KRX',transport_epoch='4',attempt_id='attempt',plan_sha256='a'*64)])
    trade=dict(buy_qty=1,buy_price=100,sell_price=110,realized_net_pnl_krw=8)
    assert policy._cap_candidate_trade(trade,source,'cap_20pct',.0023)['modeled_filled_qty']==2
    result=policy._cap_candidate_trade(trade,source,'cap_10pct',.0023)
    assert result['candidate_net_pnl_krw']==pytest.approx(result['modeled_parent_net_pnl_krw'],abs=.001)
    assert result['actual_net_pnl_krw']==8


def test_holdout_changes_acceptance_never_train_choice_or_next_best():
    rows=[]
    for day in ('2026-10-05','2026-10-06','2026-10-07'):
        for i in range(20):
            rows.append(dict(trade_id=f'{day}:{i}',entry_date=day,actual_net_pnl_krw=10,actual_profit_rate=1,modeled_parent_net_pnl_krw=10,original_notional_krw=1000,
                cap_candidates={mode:dict(status='partial_unfilled',candidate_net_pnl_krw=value,candidate_net_pct_on_parent_notional=value/10) for mode,value in [('cap_10pct',20),('cap_15pct',15)]}))
    selected,metrics=cap_selection(rows,'parent_5stage',30)
    assert selected=='cap_10pct'
    before=metrics['cap_10pct']['train_selected_candidate_sha256']
    for row in rows[-20:]:row['cap_candidates']['cap_10pct']['candidate_net_pnl_krw']=-100
    selected,metrics=cap_selection(rows,'parent_5stage',30)
    assert selected=='parent_5stage'
    assert metrics['cap_10pct']['train_selected_candidate_sha256']==before
    assert metrics['cap_15pct']['selection_eligible'] is False


def _prevalidated_joint_selection(tmp_path, monkeypatch, outcomes, *, algorithm=None,
                                 shapes=None, following=None, cost_available_at=None):
    """Exercise aggregation/selection after independently validated source intake.

    Source protocol validation has integration coverage below; this fixture
    controls each paired economic outcome without inventing broker data.
    """
    from src.engine.lifecycle import research_storage as storage
    from src.engine.scalping import initial_quantity_refresh_evaluation as evaluation
    from src.engine.scalping import initial_quantity_timeout_research as timeout_module
    from src.engine.scalping import initial_quantity_following_bars as following_module
    parent, path = parent_fixture(tmp_path)
    days = ('2026-10-05', '2026-10-06', '2026-10-07')
    rows, facts, cases = [], [], []
    grid = {mode: dict(mode=mode, shape=(shapes or {}).get(mode, 'parent'),
                      horizon=None, reserve=5) for mode in outcomes}
    for day in days:
        for index in range(20):
            tid = f'{day}:{index}'
            parent_net = 20. if index % 2 == 0 else -18.
            rows.append(dict(trade_id=tid, record_id=tid, entry_date=day,
                             quantity_type='KRX_PARENT', actual_net_pnl_krw=parent_net,
                             actual_profit_rate=parent_net / 10))
            if cost_available_at is not None and day < days[-1]:
                rows[-1]['cost_available_at'] = cost_available_at
            facts.append(dict(recommendation_id=tid, sell_time=day+'T10:00:00+09:00'))
            for key, callback in outcomes.items():
                result = callback(day, index, parent_net)
                candidate, status = result if isinstance(result, tuple) else (result, 'paired')
                cases.append(dict(trade_id=tid, key=key, outcome=dict(status=status,
                    candidate_net_pnl_krw=candidate, modeled_parent_net_pnl_krw=parent_net,
                    candidate_net_pct_on_parent_notional=candidate / 10,
                    parent_net_pct_on_parent_notional=parent_net / 10,
                    verified_price_cross_count=1)))
    report = dict(trades=rows, source_date=days[-1], report_content_sha256='c'*64,
                  census=dict(input_fact_rows=facts, entry_on_or_after=policy.refresh_window(parent), excluded={}))
    evidence = tmp_path / 'joint'
    evidence.mkdir()
    timeout = dict(joint_grid=grid, joint_evidence_root=str(evidence.resolve()),
                   joint_outcomes_ref=storage.write_tree(evidence, cases), census=report['census'])
    monkeypatch.setattr(evaluation, 'replay_valid', lambda _: True)
    monkeypatch.setattr(timeout_module, 'timeout_research_valid', lambda *a, **kw: True)
    monkeypatch.setattr(following_module, 'following_bar_source_valid', lambda *a: True)
    receipt = dict(actual_pid_consumed=True, policy_content_sha256=parent['policy_content_sha256'],
                   daily_pid_receipts=[dict(entry_date=day, pid=123, verified_at=day+'T08:00:00+09:00') for day in days])
    return evaluation.evaluate(report, parent_policy=parent, parent_policy_file_sha256=policy._file_sha256(path),
        pid_receipt=receipt, terminal_receipt=dict(report_content_sha256=report['report_content_sha256'],
            terminal=True, costed_completed_trade_count=len(rows)), timeout_research=timeout,
        enforce_trade_lineage=False, following_bars=following, evaluation_algorithm=algorithm)


def test_joint_selection_ranks_all_trade_ev_and_keeps_v2_frozen(tmp_path, monkeypatch):
    from src.engine.scalping.initial_quantity_refresh_evaluation import VERSION, SELECTION_VERSION
    outcomes = {'cap_10pct': lambda day, i, p: 15 if p > 0 else -7,
                'cap_15pct': lambda day, i, p: 23 if p > 0 else -19}
    result = _prevalidated_joint_selection(tmp_path / 'current', monkeypatch, outcomes)
    choice = result['type_decisions']['KRX_PARENT']
    assert result['evaluation_algorithm'] == SELECTION_VERSION
    assert result['global_blockers'] == [] and result['state'] == 'eligible_source_only'
    assert choice['selected_ratio_mode'] == 'cap_10pct'
    assert choice['joint_candidate_metrics']['cap_10pct']['train']['winner_weighted_delta_pct'] < 0
    assert choice['joint_candidate_metrics']['cap_10pct']['train']['mean_delta_pct'] == pytest.approx(.3)
    old = _prevalidated_joint_selection(tmp_path / 'legacy', monkeypatch, outcomes, algorithm=VERSION)
    assert old['evaluation_algorithm'] == VERSION
    assert old['type_decisions']['KRX_PARENT']['selected_ratio_mode'] == 'cap_15pct'


def test_joint_selection_rejects_winner_gain_with_worse_all_trade_profit(tmp_path, monkeypatch):
    result = _prevalidated_joint_selection(tmp_path, monkeypatch,
        {'cap_10pct': lambda day, i, p: 25 if p > 0 else -30})
    choice = result['type_decisions']['KRX_PARENT']
    metric = choice['joint_candidate_metrics']['cap_10pct']
    assert metric['train']['winner_weighted_delta_pct'] > 0
    assert metric['train']['delta'] < 0 and metric['train_eligible'] is False
    assert choice['train_selected_candidate'] is None
    assert result['state'] == 'carry_parent'


def test_joint_partial_and_no_fill_remain_in_same_denominator(tmp_path, monkeypatch):
    statuses = ('paired', 'partial_unfilled', 'modeled_no_fill')
    result = _prevalidated_joint_selection(tmp_path, monkeypatch,
        {'cap_10pct': lambda day, i, p: (0 if i % 3 == 2 else p + 6, statuses[i % 3])})
    metric = result['type_decisions']['KRX_PARENT']['joint_candidate_metrics']['cap_10pct']['train']
    assert metric['count'] == 40 and metric['coverage'] == 1
    deltas = [(0 if i % 3 == 2 else (20 if i % 2 == 0 else -18) + 6)
              - (20 if i % 2 == 0 else -18) for i in range(20)]
    assert metric['mean_delta_pct'] == pytest.approx(sum(deltas) / 20 / 10)


def test_joint_holdout_cannot_choose_next_candidate_or_change_train_sha(tmp_path, monkeypatch):
    outcomes = {'cap_10pct': lambda day, i, p: p + 6,
                'cap_15pct': lambda day, i, p: p + 4}
    before = _prevalidated_joint_selection(tmp_path / 'before', monkeypatch, outcomes)
    outcomes['cap_10pct'] = lambda day, i, p: p - 100 if day == '2026-10-07' else p + 6
    after = _prevalidated_joint_selection(tmp_path / 'after', monkeypatch, outcomes)
    a, b = (value['type_decisions']['KRX_PARENT'] for value in (before, after))
    assert a['train_selected_candidate'] == b['train_selected_candidate'] == 'cap_10pct'
    assert a['train_selected_candidate_sha256'] == b['train_selected_candidate_sha256']
    assert a['holdout_passed'] is True and b['holdout_passed'] is False
    assert b['selected_ratio_mode'] == 'parent_5stage'


def test_joint_train_following_coverage_is_independent_of_holdout(tmp_path, monkeypatch):
    outcomes = {'cap_10pct': lambda day, i, p: p + 6}
    train_links = {f'{day}:{i}': dict(first_lower_elapsed_from_fill_minute=2)
                   for day in ('2026-10-05', '2026-10-06') for i in range(0, 20, 2)}
    before = _prevalidated_joint_selection(tmp_path / 'before', monkeypatch, outcomes,
        shapes={'cap_10pct': 'two_leg_0_1tick'}, following=dict(trades=train_links,
            weighted_by_type={'KRX_PARENT': dict(observed_minute_lower_count=20)}))
    holdout_links = {f'2026-10-07:{i}': dict(first_lower_elapsed_from_fill_minute=2) for i in range(0, 20, 2)}
    after = _prevalidated_joint_selection(tmp_path / 'after', monkeypatch, outcomes,
        shapes={'cap_10pct': 'two_leg_0_1tick'}, following=dict(trades={**train_links, **holdout_links},
            weighted_by_type={'KRX_PARENT': dict(observed_minute_lower_count=30)}))
    a, b = (value['type_decisions']['KRX_PARENT'] for value in (before, after))
    assert a['train_selected_candidate'] == b['train_selected_candidate'] == 'cap_10pct'
    assert a['train_selected_candidate_sha256'] == b['train_selected_candidate_sha256']


def test_refresh_unknown_selection_algorithm_fails_closed():
    with pytest.raises(ValueError, match='refresh_selection_algorithm_invalid'):
        cap_selection([], 'parent_5stage', 30, evaluation_algorithm='future-unknown')


def test_v3_cannot_use_costs_first_available_in_holdout_for_train_selection(tmp_path, monkeypatch):
    from src.engine.scalping.initial_quantity_refresh_evaluation import VERSION
    outcomes = {'cap_10pct': lambda day, i, p: p + 6}
    result = _prevalidated_joint_selection(tmp_path/'current', monkeypatch, outcomes,
        cost_available_at='2026-10-07T08:00:00+09:00')
    assert len(result['purged_trade_ids']) == 40 and result['train_trade_ids'] == []
    assert result['type_decisions']['KRX_PARENT']['train_selected_candidate'] is None
    old = _prevalidated_joint_selection(tmp_path/'old', monkeypatch, outcomes, algorithm=VERSION,
        cost_available_at='2026-10-07T08:00:00+09:00')
    assert old['purged_trade_ids'] == []
    assert old['type_decisions']['KRX_PARENT']['selected_ratio_mode'] == 'cap_10pct'


def test_joint_replay_probe_is_two_slots_and_price_time_bound():
    trade,path=_research_trade_path();trade['quantity_type']='KRX_PARENT';trade['comparison_cost_rate']=.0023
    start=path['order_starts'][0];start.update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60,probe_applied=True)
    path['fills'][0]['qty']=1
    path['fills'].append({**path['fills'][0], 'at':path['fills'][0]['at']+timedelta(seconds=1), 'qty':3, 'execution_no':'residual'})
    context=_cap_context(budget=1600,actual_qty=4)
    source=dict(context=context,attempt_id='a',plan_sha256='b'*64,following_ticks=[])
    path['decisions'][0]['fields'].update(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64)
    result=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert result['target_qty']==4 and result['modeled_filled_qty']==1
    assert result['status']=='partial_unfilled'
    # A fill outside the active second slot cannot complete a hypothetical leg.
    path['fills'][1]['at']=path['fills'][0]['at']+timedelta(seconds=90)
    result=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert result['modeled_filled_qty']==1


def test_refresh_window_and_empty_policy_consumption_are_independent(tmp_path):
    assert policy.refresh_window({'effective_from':'2026-09-24'})=='2026-09-29'
    assert policy.refresh_window({'effective_from':'2026-10-01'})=='2026-10-01'
    assert policy._natural_refresh_pid_receipt({'trades':[],'source_date':'2026-10-08'},dict(effective_from='2026-09-24'),tmp_path/'parent.json',tmp_path) is None


def test_cost_only_warm_features_do_not_decode_pipeline(tmp_path,monkeypatch):
    day='2026-10-08';_quality(tmp_path,day)
    facts=[actual_fact()]
    pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/f'pipeline_events_{day}.jsonl').write_text(json.dumps(_event(1,'nothing',day+'T09:30:00+09:00'))+'\n')
    cold=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    def forbidden(*a,**k):raise AssertionError('warm feature cache rescanned the source')
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',forbidden)
    warm=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert warm==cold
    corrected=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=[actual_fact(fees=300)],entry_on_or_after='2026-09-29')
    assert corrected['census']['actual_completed_net_pnl_krw']==700
    assert corrected['report_content_sha256']!=cold['report_content_sha256']


def test_refresh_original_notional_is_fact_bound_and_old_rows_remain_readable(tmp_path):
    day = '2026-10-08'
    _quality(tmp_path, day)
    report = policy.build_initial_quantity_replay(day, data_dir=tmp_path,
        fact_rows=[actual_fact()], entry_on_or_after='2026-09-29')
    assert report['trades'][0]['original_notional_krw'] == 100000
    assert policy.initial_replay_economics_valid(report)
    changed = copy.deepcopy(report)
    changed['trades'][0]['original_notional_krw'] = 1
    changed['report_content_sha256'] = policy._digest({k: v for k, v in changed.items()
                                                     if k != 'report_content_sha256'})
    assert policy.initial_replay_economics_valid(changed) is False
    legacy = copy.deepcopy(report)
    del legacy['trades'][0]['original_notional_krw']
    legacy['report_content_sha256'] = policy._digest({k: v for k, v in legacy.items()
                                                    if k != 'report_content_sha256'})
    assert policy.initial_replay_economics_valid(legacy)


def parent_fixture(tmp_path):
    from src.engine.scalping.initial_quantity_activation import build_initial_quantity_baseline
    from src.engine.scalping.initial_quantity_following_bars import build_following_bar_source
    day='2026-09-24';_quality(tmp_path,day)
    facts=_facts([dict(recommendation_id=9,stock_code='005930',strategy='SCALPING',position_tag='SCANNER',buy_price=100,sell_price=99,buy_qty=4,sell_time='09:35:00',held_sec=300)],day)
    seed=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts)
    following=build_following_bar_source(seed,fetch=lambda *a: (_ for _ in ()).throw(AssertionError('no winners')))
    stage=policy.publish_initial_quantity_candidate(seed,output_dir=tmp_path/'seed',following_bars=following)
    parent=build_initial_quantity_baseline(stage);path=(tmp_path/'parent.json').resolve();policy._write_immutable_json(path,parent)
    return parent,path


def test_v2_same_date_successors_and_consumer_pointer(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    parent,path=parent_fixture(tmp_path);base=tmp_path/'refresh';day='2026-10-08'
    before=None
    for facts in ([],[{**actual_fact(),'profit_rate':None,'realized_pnl_krw':None}]):
        shared={};report=policy.build_initial_quantity_replay(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared)
        timeout=build_timeout_research(day,data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared,replay=report)
        stage=policy.publish_refresh_quantity_evaluation(report,parent_policy=parent,parent_policy_path=path,output_dir=base,timeout_research=timeout,terminal_receipt=policy._natural_refresh_terminal_receipt(report))
        assert policy.refresh_quantity_stage_terminal_valid(stage)
        current=policy.committed_refresh_stage_path(base,day)
        assert current.exists() and json.loads(current.read_bytes())==stage
        assert stage['decision']=='carry_parent'
        if before:
            assert before!=current and before.exists()
        before=current
    ref=json.loads((base/'committed_stage.json').read_bytes());ref['stage_sha256']='0'*64
    (base/'committed_stage.json').write_text(json.dumps(ref))
    with pytest.raises(ValueError,match='quantity_stage_reference_invalid'):policy.committed_refresh_stage_path(base,day)


def test_public_stage_validator_preserves_v2_and_accepts_v3_selection(tmp_path, monkeypatch):
    from src.engine.scalping.initial_quantity_refresh_evaluation import VERSION, SELECTION_VERSION
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    parent, path = parent_fixture(tmp_path)
    day = '2026-10-08'
    report = policy.build_initial_quantity_replay(day, data_dir=tmp_path, fact_rows=[],
        entry_on_or_after=policy.refresh_window(parent))
    timeout = build_timeout_research(day, data_dir=tmp_path, fact_rows=[],
        entry_on_or_after=policy.refresh_window(parent), replay=report)
    original = policy.evaluate_refresh_quantity_candidate
    def frozen_v2(*args, **kwargs):
        kwargs.setdefault('evaluation_algorithm', VERSION)
        return original(*args, **kwargs)
    monkeypatch.setattr(policy, 'evaluate_refresh_quantity_candidate', frozen_v2)
    old_stage = policy.publish_refresh_quantity_evaluation(report, parent_policy=parent,
        parent_policy_path=path, output_dir=tmp_path/'old', timeout_research=timeout,
        terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    monkeypatch.setattr(policy, 'evaluate_refresh_quantity_candidate', original)
    assert policy.refresh_quantity_stage_terminal_valid(old_stage)
    assert json.loads(Path(old_stage['evaluation_path']).read_bytes())['evaluation_algorithm'] == VERSION
    stage = policy.publish_refresh_quantity_evaluation(report, parent_policy=parent,
        parent_policy_path=path, output_dir=tmp_path/'current', timeout_research=timeout,
        terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert policy.refresh_quantity_stage_terminal_valid(stage)
    evaluation_path = Path(stage['evaluation_path'])
    evaluation = json.loads(evaluation_path.read_bytes())
    assert evaluation['evaluation_algorithm'] == SELECTION_VERSION
    evaluation['evaluation_algorithm'] = 'future-unknown'
    evaluation_path.write_text(json.dumps(evaluation))
    changed = {**stage, 'evaluation_file_sha256': policy._file_sha256(evaluation_path)}
    changed['receipt_content_sha256'] = policy._digest({k: v for k, v in changed.items()
                                                       if k != 'receipt_content_sha256'})
    assert policy.refresh_quantity_stage_terminal_valid(changed) is False


def test_refresh_publication_accepts_only_the_known_release_data_link(tmp_path, monkeypatch):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    shared = tmp_path / 'shared'
    shared.mkdir()
    release = tmp_path / 'release'
    release.mkdir()
    (release / 'data').symlink_to(shared, target_is_directory=True)
    monkeypatch.setattr(policy, 'PROJECT_ROOT', release)
    monkeypatch.setattr(policy, 'DATA_DIR', shared)
    parent, parent_path = parent_fixture(shared)
    day = '2026-10-08'
    report = policy.build_initial_quantity_replay(day, data_dir=shared, fact_rows=[],
        entry_on_or_after=policy.refresh_window(parent))
    timeout = build_timeout_research(day, data_dir=shared, fact_rows=[],
        entry_on_or_after=policy.refresh_window(parent), replay=report)
    base = release / 'data' / 'refresh'
    stage = policy.publish_refresh_quantity_evaluation(report, parent_policy=parent,
        parent_policy_path=parent_path, output_dir=base, timeout_research=timeout,
        terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert policy.refresh_quantity_stage_terminal_valid(stage)
    path = policy.committed_refresh_stage_path(base, day)
    assert path.is_relative_to(shared) and json.loads(path.read_bytes()) == stage
    assert stage['decision'] == 'carry_parent'
    assert stage['runtime_apply_allowed'] is False
    assert stage['actual_order_submitted'] is False
    assert policy._write_immutable_json(path, stage) == policy._file_sha256(path)
    with pytest.raises(ValueError, match='immutable_artifact_conflict'):
        policy._write_immutable_json(path, {'changed': True})


@pytest.mark.parametrize('kind', ['foreign_root', 'data_child', 'output_file', 'wrong_data_mount', 'parent_escape'])
def test_quantity_publication_rejects_unowned_links_before_creating_output(tmp_path, monkeypatch, kind):
    release = tmp_path / 'release'
    shared = tmp_path / 'shared'
    foreign = tmp_path / 'foreign'
    for root in (release, shared, foreign):
        root.mkdir()
    monkeypatch.setattr(policy, 'PROJECT_ROOT', release)
    monkeypatch.setattr(policy, 'DATA_DIR', shared)
    (release / 'data').symlink_to(foreign if kind == 'wrong_data_mount' else shared,
                                target_is_directory=True)
    if kind == 'foreign_root':
        (tmp_path / 'alias').symlink_to(foreign, target_is_directory=True)
        path = tmp_path / 'alias' / 'created' / 'report.json'
    elif kind == 'data_child':
        (shared / 'child').symlink_to(foreign, target_is_directory=True)
        path = release / 'data' / 'child' / 'created' / 'report.json'
    elif kind == 'output_file':
        (shared / 'report.json').symlink_to(foreign / 'report.json')
        path = release / 'data' / 'report.json'
    elif kind == 'parent_escape':
        path = release / 'data' / '..' / 'created' / 'report.json'
    else:
        path = release / 'data' / 'created' / 'report.json'
    with pytest.raises(ValueError, match='quantity_output_path_invalid'):
        policy._write_immutable_json(path, {'value': 1})
    assert list(foreign.iterdir()) == []


def test_recent_replay_missing_cost_is_not_no_real_trade_or_no_pid(tmp_path):
    from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate
    parent,path=parent_fixture(tmp_path)
    report=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=[{**actual_fact(),'profit_rate':None}],entry_on_or_after=policy.refresh_window(parent))
    result=evaluate(report,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),pid_receipt=dict(actual_pid_consumed=True,policy_content_sha256=parent['policy_content_sha256'],daily_pid_receipts=[dict(entry_date='2026-10-08',pid=123,verified_at='2026-10-08T08:00:00+09:00')]),terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert result['policy_pid_status']=='verified_archive'
    assert result['economic_sample_status']=='cost_missing'
    assert 'parent_pid_consumption_missing' not in result['global_blockers']


def test_actual_cost_object_survives_text_db_and_quantity_consumer(monkeypatch,tmp_path):
    from src.engine import strategy_position_performance_report as mod
    native=dict(schema='holding_actual_cost_source_generation_v1',completion_date='2026-10-08',count=1,sha256='a'*64,status='observed')
    fact={**actual_fact(),'actual_cost_source_generation':native}
    persisted=mod._trade_fact_db_payload(fact)
    assert json.loads(persisted['actual_cost_source_generation'])==native
    _quality(tmp_path,'2026-10-08')
    rows,_=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[persisted],entry_on_or_after='2026-09-29')
    assert len(rows)==1


def test_late_invalid_fact_duplicate_invalidates_earlier_good_row(tmp_path):
    _quality(tmp_path,'2026-10-08')
    good=actual_fact();bad={**good,'realized_pnl_krw':None}
    rows,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=[good,bad],entry_on_or_after='2026-09-29')
    assert rows==[] and census['excluded']=={'conflicting_duplicate_fact':2}


def test_frozen_order_start_extends_capture_once_and_queue_is_nonblocking(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    from src.trading.market import quote_consistency
    start=datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    stock=dict(id=1,name='test',_initial_quantity_cap_trace=dict(started_at_epoch=start-1100,entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,depth_item='005930',depth_route='KRX',transport_epoch=4))
    handler._start_initial_quantity_cap_capture(stock,attempt_id='a',submission_fields=dict(entry_cancel_wait_submission_context=json.dumps(dict(frozen_at=datetime.fromtimestamp(start,handler._KST).isoformat()))))
    handler._start_initial_quantity_cap_capture(stock,attempt_id='a',submission_fields=dict(entry_cancel_wait_submission_context=json.dumps(dict(frozen_at=datetime.fromtimestamp(start+100,handler._KST).isoformat()))))
    assert stock['_initial_quantity_cap_trace']['order_capture_end_epoch']==start+1200
    events=[]
    observer.configure_sink(lambda *args,**kw:(events.append((args,kw)) or {'status':'queued'}))
    monkeypatch.setattr(handler,'_log_holding_pipeline',lambda *a,**k:pytest.fail('synchronous cap writer'))
    monkeypatch.setattr(quote_consistency,'ws_quote_source_receipt',lambda *a,**kw:dict(source_type='0B',observed_epoch=start+200,item='005930',market_route='KRX',transport_epoch=4,depth_receipt=dict(item='005930',market_route='KRX',transport_epoch=4)))
    tick=dict(aggressor_source='kiwoom_0b_signed_trade_volume',signed_trade_volume='+10',price=100,ts=start+200)
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+200)
    assert len(events)==1 and events[0][1]['record_id']==1
    assert events[0][1]['fields']['cap_tick_observation_coverage']=='sampled_last_trade_tick'
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+200)
    assert len(events)==1 and stock['_initial_quantity_cap_trace']['duplicate_observation_count']==1
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',dict(last_trade_tick=tick),now_ts=start+1201)
    assert '_initial_quantity_cap_trace' not in stock and events[-1][0][-1]=='initial_quantity_cap_capture_finished'
    observer.configure_sink(None)


@pytest.mark.parametrize('route,item,venue,order_route',[
    ('krx_only','005930','KRX','KRX'),
    ('nxt_only','005930_NX','NXT','NXT'),
    ('krx_nxt_integrated','005930_AL','KRX','SOR'),
    ('krx_nxt_integrated','005930_AL','NXT','SOR'),
])
def test_native_quote_route_reaches_live_quantity_capture(monkeypatch,route,item,venue,order_route):
    from src.engine import sniper_state_handlers as handler
    from src.trading.market import quote_consistency
    from src.engine.scalping import position_sizing_allocator as allocator
    from src.tests.test_scalping_position_sizing_allocator import _context
    at=datetime.fromisoformat('2026-10-08T10:00:00+09:00').timestamp()
    context=_context('2026-10-08T10:00:00',venue=venue)
    decision=allocator.resolve_scalping_allocation(context)
    receipt=dict(source_type='0D',item=item,market_route=route,transport_epoch=4,
                 depth_receipt=dict(item=item,market_route=route,transport_epoch=4,observed_epoch=at))
    monkeypatch.setattr(quote_consistency,'ws_quote_source_receipt',lambda *a,**kw:receipt)
    raw=dict(orderbook=dict(asks=[dict(price=100,volume=20)]))
    value=handler._initial_quantity_cap_research_context(context,decision,ws_data=raw,now_ts=at)
    assert value['ask_depth_source']['market_route']==route
    assert value['ask_depth_source']['order_route']==order_route
    assert value['ask_depth_source']['underlying_event_venue_proven'] is (order_route!='SOR')
    receipt['depth_receipt']['item']='005930_NX' if item!='005930_NX' else '005930'
    value=handler._initial_quantity_cap_research_context(context,decision,ws_data=raw,now_ts=at)
    assert 'ask_depth_source' not in value


def test_integrated_quote_is_sor_replay_without_manufacturing_fill_venue():
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    first=path['fills'][0];first['qty']=1
    path['fills'].append({**first,'at':first['at']+timedelta(seconds=30),'qty':3,'venue':'NXT','execution_no':'2'})
    start=path['order_starts'][0];start.update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60,probe_applied=True)
    at=start['at'].timestamp();context=_cap_context(budget=1600,actual_qty=4)
    context['ask_depth_source']=dict(source_type='ws_0D_bound_snapshot',item='005930_AL',market_route='krx_nxt_integrated',observed_epoch=at,transport_epoch=4,levels=[dict(price_krw=99,quantity=20),dict(price_krw=100,quantity=20)])
    source=dict(context=context,attempt_id='a',plan_sha256='b'*64,following_ticks=[dict(attempt_id='a',plan_sha256='b'*64,depth_item='005930_AL',item='005930_AL',market_route='krx_nxt_integrated',transport_epoch='4',observed_epoch=at+40,price_krw=99,quantity=20)])
    path['decisions'][0]['fields'].update(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64)
    value=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert value['status']=='paired' and value['modeled_filled_qty']==4
    assert [row['venue'] for row in path['fills']]==['KRX','NXT']
    source['following_ticks'][0]['market_route']='nxt_only'
    value=execution_case(trade,path,source,mode='parent_5stage',shape='two_leg_0_1tick',horizon=60)
    assert value['status']=='partial_unfilled' and value['modeled_filled_qty']==1


def test_capture_terminal_queue_gap_is_preserved_in_source_features(tmp_path):
    day='2026-10-08';_quality(tmp_path,day)
    trades,_=policy.completed_trade_fact_census(day,data_dir=tmp_path,fact_rows=[actual_fact()],entry_on_or_after='2026-09-29')
    directory=tmp_path/'pipeline_events';directory.mkdir()
    event=_event(1,'initial_quantity_cap_capture_finished',day+'T09:51:00+09:00',entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_queue_rejected_count=7,capture_queued_count=20,observation_coverage='sampled_last_trade_tick')
    event['stock_code']='005930'
    (directory/f'pipeline_events_{day}.jsonl').write_text(json.dumps(event)+'\n')
    paths=policy.join_post_fill_paths(trades,data_dir=tmp_path)
    value=paths[trades[0]['trade_id']]['capture_receipts'][0]['fields']
    assert value['capture_queue_rejected_count']==7
    assert value['observation_coverage']=='sampled_last_trade_tick'


def test_quantity_fact_validator_never_decodes_oversized_legacy_timeline(monkeypatch,tmp_path):
    from src.engine import log_archive_service as archive
    from src.engine import strategy_position_performance_report as fact
    from src.engine.lifecycle.holding_window_generation import MAX_PROJECTION_BYTES
    monkeypatch.setattr(policy,'DATA_DIR',tmp_path)
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',tmp_path)
    monkeypatch.setattr(fact,'_saved_fact_generation_issue',lambda *a,**k:pytest.fail('unbounded snapshot decode'))
    path=tmp_path/'trade_review_2026-09-30.json'
    with path.open('wb') as handle:handle.truncate(MAX_PROJECTION_BYTES+1)
    assert policy._quantity_fact_generation_issue('2026-09-30')=='trade_review_snapshot_missing'
    with path.with_suffix('.completed_projection.json').open('wb') as handle:handle.truncate(MAX_PROJECTION_BYTES+1)
    assert policy._quantity_fact_generation_issue('2026-09-30')=='fact_snapshot_requires_bounded_native_projection'


def test_quantity_raw_hash_reuses_only_invocation_local_verified_bytes(tmp_path):
    import os
    from src.engine.infrastructure import validation_digest_session as digests
    from src.engine.lifecycle.holding_window_generation import byte_generation
    path=tmp_path/'pipeline_events/day.jsonl';path.parent.mkdir()
    path.write_bytes(b'a'*(digests.MIN_BYTES+1))
    with digests.postclose_session(tmp_path,'2026-10-19') as session:
        expected=policy._file_sha256(path)
        assert policy._file_sha256(path)==expected
        assert byte_generation(path)['sha256']==expected
        assert session.stats['full_reads']==1 and session.stats['reused_reads']==2
        before=path.stat();path.write_bytes(b'b'*before.st_size)
        os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
        assert policy._file_sha256(path)!=expected
        assert session.stats['full_reads']==2
    assert digests.ACTIVE.get() is None
    assert not (tmp_path/'runtime/validation_digests').exists()


def test_quantity_cli_establishes_digest_scope_after_native_admission(tmp_path,monkeypatch):
    from contextlib import contextmanager
    from src.engine.infrastructure import validation_digest_session as digests
    from src.engine.lifecycle import research_admission,research_disk_budget
    @contextmanager
    def admitted(*args,**kwargs):
        assert digests.ACTIVE.get() is None
        yield
    @contextmanager
    def no_output(*args,**kwargs):yield
    monkeypatch.setattr(research_admission,'direct_job',admitted)
    monkeypatch.setattr(research_disk_budget,'use',no_output)
    def run(argv):
        session=digests.ACTIVE.get()
        assert session is not None and session.binding['role']=='postclose'
        assert session.data_root==tmp_path
        return 0
    monkeypatch.setattr(policy,'_main_impl',run)
    assert policy.main(['--as-of','2026-10-19','--data-dir',str(tmp_path)])==0
    assert digests.ACTIVE.get() is None


def _native_quantity_fact_source(tmp_path, monkeypatch, *, large=True):
    from src.engine import log_archive_service as archive
    from src.engine import strategy_position_performance_report as fact
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    from src.engine.sniper_trade_review_report import completed_census_manifest
    day = '2026-10-08'
    directory = tmp_path / 'report/monitor_snapshots'
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', directory)
    monkeypatch.setattr(fact, '_FACT_SYNC_STATUS_DIR', tmp_path / 'fact_sync')
    monkeypatch.setattr(policy, 'DATA_DIR', tmp_path)
    costs = source_generation(tmp_path, day)
    row = dict(id='1', status='COMPLETED', completion_observed_date=day,
               profit_rate=None, strict_completion_status='excluded',
               timeline=[{'original_observation': 'x' * (5 * 1024 * 1024)}] if large else [])
    payload = dict(date=day, metrics={'canonical_completed_trades': 1},
                   meta={'snapshot_profile': 'postclose_exit',
                         'actual_cost_source_generation': costs,
                         'sell_completed_event_ids': ['1']},
                   sections={'completed_trade_projection': [row],
                             'open_scalp_position_projection': []})
    census = completed_census_manifest(payload)
    payload['meta']['completed_census_manifest'] = census
    path = archive.save_monitor_snapshot('trade_review', day, payload)
    receipt = fact._write_status(day, dict(status='succeeded',
        completed_census_run_ids=[census['run_id']],
        completed_census_projection_sha256=[census['projection_sha256']],
        actual_cost_source_generation=costs))
    return day, path, receipt


@pytest.mark.parametrize('large', [False, True])
def test_quantity_fact_native_size_parity_and_no_timeline_decode(tmp_path, monkeypatch, large):
    from src.engine import strategy_position_performance_report as fact
    from src.engine.lifecycle.holding_window_generation import MAX_METADATA_BYTES
    day, path, _ = _native_quantity_fact_source(tmp_path, monkeypatch, large=large)
    decoded = []
    original = json.loads
    def bounded(raw, *args, **kwargs):
        decoded.append(len(raw))
        assert len(raw) <= MAX_METADATA_BYTES
        return original(raw, *args, **kwargs)
    monkeypatch.setattr(json, 'loads', bounded)
    if large:
        monkeypatch.setattr(fact, '_saved_fact_generation_issue',
            lambda *a, **k: pytest.fail('large completion projection decoded'))
    assert policy._quantity_fact_generation_issue(day) is None
    assert max(decoded) < MAX_METADATA_BYTES
    assert path.with_suffix('.completed_projection.json').stat().st_size > (4 * 1024 * 1024 if large else 0)
    # A current native source generation does not fill the missing actual cost.
    _quality(tmp_path, day)
    rows, census = policy.completed_trade_fact_census(day, data_dir=tmp_path,
        fact_rows=[{**actual_fact(), 'profit_rate': None, 'realized_pnl_krw': None,
                    'fact_generation': {'issue': None}}])
    assert rows == []
    assert census['excluded'] == {'terminal_cost_or_quantity_missing': 1}


@pytest.mark.parametrize('mutation,expected', [
    ('missing_receipt', 'fact_sync_receipt_missing_or_invalid'),
    ('invalid_receipt', 'fact_sync_receipt_missing_or_invalid'),
    ('receipt_hash', 'fact_sync_receipt_sha_mismatch'),
    ('wrong_day', 'fact_sync_receipt_not_current_success'),
    ('failed', 'fact_sync_receipt_not_current_success'),
    ('run', 'stale_fact_source_generation'),
    ('projection', 'stale_fact_source_generation'),
    ('fact_cost', 'persisted_fact_cost_generation_stale'),
    ('source_cost', 'fact_snapshot_native_projection_invalid'),
    ('sidecar', 'fact_snapshot_native_projection_invalid'),
    ('dependency', 'fact_snapshot_native_projection_invalid'),
    ('snapshot', 'fact_snapshot_native_projection_invalid'),
])
def test_quantity_compact_fact_rejects_stale_corrupt_and_cost_revisions(tmp_path, monkeypatch, mutation, expected):
    from src.engine import strategy_position_performance_report as fact
    from src.engine.lifecycle.broker_cost_reconciliation import receipt_path
    day, path, receipt = _native_quantity_fact_source(tmp_path, monkeypatch)
    receipt.pop('artifact_sha256')
    if mutation == 'missing_receipt':
        fact._status_path(day).unlink()
    elif mutation == 'invalid_receipt':
        fact._status_path(day).write_text('{invalid')
    elif mutation == 'receipt_hash':
        receipt['artifact_sha256'] = '0' * 64
        fact._status_path(day).write_text(json.dumps(receipt))
    elif mutation in {'wrong_day', 'failed', 'run', 'projection', 'fact_cost'}:
        key, value = {
            'wrong_day': ('target_date', '2026-10-07'),
            'failed': ('status', 'failed'),
            'run': ('completed_census_run_ids', ['another']),
            'projection': ('completed_census_projection_sha256', ['0' * 64]),
            'fact_cost': ('actual_cost_source_generation', {'stale': True}),
        }[mutation]
        receipt[key] = value
        receipt['artifact_sha256'] = fact._canonical_sha256(receipt)
        fact._status_path(day).write_text(json.dumps(receipt))
    elif mutation == 'source_cost':
        cost = receipt_path(tmp_path, day, '1')
        cost.parent.mkdir(parents=True)
        cost.write_text('{"corrected_actual_cost":1}')
    elif mutation == 'snapshot':
        with path.open('ab') as handle:
            handle.write(b' ')
    else:
        target = path.with_suffix('.completed_projection.json')
        if mutation == 'dependency':
            target = Path(str(target) + '.dependencies.json')
        with target.open('ab') as handle:
            handle.write(b'x')
    assert policy._quantity_fact_generation_issue(day) == expected


def test_quantity_compact_fact_accepts_native_lossless_gzip(tmp_path, monkeypatch):
    from src.engine import compress_db_backfilled_files as archive
    day, path, _ = _native_quantity_fact_source(tmp_path, monkeypatch)
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', path.parent)
    sidecar = path.with_suffix('.completed_projection.json')
    assert policy._quantity_fact_generation_issue(day) is None
    assert archive._gzip_file(path, dry_run=False)[0]
    assert archive._gzip_file(sidecar, dry_run=False)[0]
    assert not path.exists() and not sidecar.exists()
    assert policy._quantity_fact_generation_issue(day) is None
    compressed = Path(str(sidecar) + '.gz')
    with compressed.open('ab') as handle:
        handle.write(b'changed')
    assert policy._quantity_fact_generation_issue(day) == 'fact_snapshot_native_projection_invalid'


def test_quantity_compact_fact_bounded_metadata_gap_and_concurrent_change(tmp_path, monkeypatch):
    from src.engine.lifecycle import holding_window_generation as window
    day, path, _ = _native_quantity_fact_source(tmp_path, monkeypatch)
    original = policy._quantity_compact_fact_issue
    def changed(*args):
        issue = original(*args)
        with path.open('ab') as handle:
            handle.write(b' ')
        return issue
    monkeypatch.setattr(policy, '_quantity_compact_fact_issue', changed)
    assert policy._quantity_fact_generation_issue(day) == 'fact_snapshot_native_projection_changed_during_read'

    day, path, _ = _native_quantity_fact_source(tmp_path, monkeypatch)
    monkeypatch.setattr(policy, '_quantity_compact_fact_issue', original)
    sidecar = path.with_suffix('.completed_projection.json')
    payload = json.loads(sidecar.read_bytes())
    payload['meta']['warnings'] = ['x' * window.MAX_METADATA_BYTES]
    payload['artifact_sha256'] = hashlib.sha256(json.dumps(
        {k: v for k, v in payload.items() if k != 'artifact_sha256'},
        sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    sidecar.write_text(json.dumps(payload))
    window.seal_dependency_receipt(sidecar, payload)
    assert policy._quantity_fact_generation_issue(day) == 'fact_snapshot_requires_bounded_native_metadata'


def test_quantity_reservation_uses_shared_slots_and_verified_nested_owner(tmp_path):
    from src.engine.lifecycle import research_admission as mod
    r=mod.acquire(tmp_path,'initial_entry_quantity_refresh','2026-10-08')
    assert len(r.handles)==2
    try:
        assert mod.acquire(tmp_path,'main_trailing_all_scope','2026-10-08') is None
        with r.worker(),mod.direct_job(tmp_path,'initial_entry_quantity_refresh','2026-10-08',timeout=0):pass
        with r.worker(),pytest.raises(ValueError,match='identity_invalid'):
            with mod.direct_job(tmp_path,'pre_submit_delay','2026-10-08',timeout=0):pass
    finally:r.close()
    r=mod.acquire(tmp_path,'pre_submit_delay','2026-10-08');assert len(r.handles)==2;r.close()


def _positive_joint_fixture(root):
    parent,parent_path=parent_fixture(root);sha=policy._file_sha256(parent_path)
    facts=[];pid=[];pipeline=root/'pipeline_events';pipeline.mkdir()
    for di,day in enumerate(('2026-10-05','2026-10-06','2026-10-07')):
        _quality(root,day);events=[];pid.append(dict(entry_date=day,pid=123,verified_at=day+'T08:00:00+09:00'))
        for i in range(20):
            rid=100+di*20+i;start=datetime.fromisoformat(day+'T09:30:00+09:00')+timedelta(minutes=i)
            decision=start-timedelta(seconds=1);first=start+timedelta(seconds=5);exit=start+timedelta(seconds=300)
            facts.append({**actual_fact(rid,day),'buy_price':100,'buy_qty':4,'sell_price':110,'profit_rate':9.75,'realized_pnl_krw':39,'broker_actual_fees_taxes_krw':1,'buy_time':first.isoformat(),'sell_time':exit.isoformat()})
            context=_cap_context(budget=1600,actual_qty=4);context.update(quantity_type='KRX_PARENT',ask_depth_source=dict(source_type='ws_0D_bound_snapshot',observed_epoch=decision.timestamp(),item='005930',market_route='KRX',transport_epoch=4,levels=[dict(price_krw=99,quantity=20),dict(price_krw=100,quantity=20)]))
            base=dict(entry_submit_attempt_id=str(rid),entry_execution_sizing_plan_sha256='b'*64)
            def event(stage,at,**fields):
                v=_event(rid,stage,at.isoformat(),**fields);v['stock_code']='005930';events.append(v)
            event('entry_execution_sizing_plan',decision,**base,entry_execution_sizing_valid=True,effective_venue='KRX',quantity_type='KRX_PARENT',quantity_type_classifier_version='initial_quantity_type_v1',ratio=.25,effective_qty=4,reference_time=decision.isoformat(),position_sizing_policy_status='initial_policy_loaded',position_sizing_policy_sha256=sha,scalping_sizing_position_sizing_policy_sha256=sha,initial_quantity_runtime_pid=123,initial_quantity_cap_research_context=json.dumps(context))
            event('order_leg_sent',start,**base,tag='initial_quantity_leg_0',broker_order_no=str(rid),actual_order_submitted=True,initial_quantity_order_start_at=start.isoformat(),initial_quantity_bundle_total_wait_sec=60,initial_quantity_schedule_sha256='c'*64,initial_quantity_policy_file_sha256=sha,initial_quantity_attempt_id=str(rid),initial_quantity_leg_index=0)
            event('position_rebased_after_fill',first,fill_qty=4,fill_price=100,entry_mode='normal',order_no=str(rid),execution_no='1',actual_execution_venue='KRX',broker_execution_observed_at=first.isoformat())
            event('initial_quantity_cap_following_tick',start+timedelta(seconds=40),**base,cap_tick_observed_epoch=(start+timedelta(seconds=40)).timestamp(),cap_tick_price_krw=99,cap_tick_quantity=20,cap_tick_item='005930',cap_tick_depth_item='005930',cap_tick_market_route='KRX',cap_tick_transport_epoch='4',decision_authority='source_only_cap_fill_research',actual_order_submitted=False)
            event('initial_quantity_cap_capture_finished', start+timedelta(seconds=1201), **base,
                  capture_clock_status='frozen_order_start', capture_order_start_epoch=start.timestamp(),
                  capture_end_epoch=start.timestamp()+1200, capture_queue_rejected_count=0,
                  capture_queued_count=1)
        (pipeline/f'pipeline_events_{day}.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
    receipt=dict(source='verified_daily_preopen_main_pid_env',data_root=str(root.resolve()),first_consumed_date='2026-10-05',policy_file_sha256=sha,actual_pid_consumed=True,policy_content_sha256=parent['policy_content_sha256'],daily_pid_receipts=pid)
    return parent,parent_path,facts,receipt


def test_joint_eligible_shape_publishes_and_isolates_one_bad_binding(monkeypatch,tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    parent,path,facts,pid=_positive_joint_fixture(tmp_path);cache={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache,replay=report)
    monkeypatch.setattr(policy,'_natural_refresh_pid_receipt',lambda *a,**kw:pid)
    from src.engine.scalping.initial_quantity_following_bars import build_following_bar_source
    def fetch(code,day,limit):
        base=datetime.strptime(day,'%Y%m%d').replace(hour=9,minute=30,tzinfo=__import__('zoneinfo').ZoneInfo('Asia/Seoul'))
        candles=[dict(source_timestamp=(base+timedelta(minutes=i)).strftime('%Y%m%d%H%M%S'),저가=99) for i in range(61)]
        return candles,dict(api_id='ka10080',request_code=code,request_base_dt=day)
    following=build_following_bar_source(report,fetch=fetch)
    stage=policy.publish_refresh_quantity_evaluation(report,parent_policy=parent,parent_policy_path=path,output_dir=tmp_path/'refresh',pid_receipt=pid,following_bars=following,terminal_receipt=policy._natural_refresh_terminal_receipt(report),timeout_research=timeout)
    evaluation=json.loads(Path(stage['evaluation_path']).read_bytes())
    assert evaluation['state']=='eligible_source_only'
    assert evaluation['type_decisions']['KRX_PARENT']['selected_shape']!='parent'
    assert stage['following_bar_source_status']=='source_bound'
    assert policy.refresh_quantity_stage_terminal_valid(stage)
    # One identifiable binding loss leaves the remaining 59 trades usable.
    changed=copy.deepcopy(report);changed['trades'][0]['applied_policy_status']='wrong'
    changed['report_content_sha256']=policy._digest({k:v for k,v in changed.items() if k!='report_content_sha256'})
    from src.engine.scalping.initial_quantity_refresh_evaluation import evaluate
    result=evaluate(changed,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),pid_receipt=pid,terminal_receipt=policy._natural_refresh_terminal_receipt(changed))
    assert result['parent_policy_bound_trade_count']==59
    assert result['trade_policy_binding_status']=='partial'


def test_cache_corruption_rebuild_and_incremental_date_scan(tmp_path,monkeypatch):
    _quality(tmp_path,'2026-10-08');pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/'pipeline_events_2026-10-08.jsonl').write_text('{}\n')
    facts=[actual_fact()]
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    index=next((tmp_path/'report/initial_entry_quantity_type_policy/source_features').rglob('index.json'))
    value=json.loads(index.read_bytes());base=Path(value['tree_root'])
    shard=base/value['tree']['path'];shard.write_bytes(shard.read_bytes()+b' ')
    scans=[];original=policy._join_post_fill_paths_uncached
    def count(rows,**kw):scans.extend(r['entry_date'] for r in rows);return original(rows,**kw)
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',count)
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert scans==['2026-10-08'];scans.clear()
    policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    assert scans==[]
    _quality(tmp_path,'2026-10-09');(pipeline/'pipeline_events_2026-10-09.jsonl').write_text('{}\n')
    policy.build_initial_quantity_replay('2026-10-09',data_dir=tmp_path,fact_rows=facts+[actual_fact(2,'2026-10-09')],entry_on_or_after='2026-09-29')
    assert scans==['2026-10-09']


def test_joint_byte_verified_memo_rejects_resealed_changed_outcome(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research,timeout_research_valid
    from src.engine.lifecycle import research_storage as storage
    parent,path,facts,pid=_positive_joint_fixture(tmp_path);cache={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=cache,replay=report)
    assert timeout_research_valid(timeout,replay=report)
    root=Path(timeout['joint_evidence_root'])
    def corrupt():
        for i,item in enumerate(storage.iter_tree(root,timeout['joint_outcomes_ref'])):
            if i==0:item={**item,'outcome':{**item['outcome'],'candidate_net_pnl_krw':999999}}
            yield item
    altered={**timeout,'joint_outcomes_ref':storage.write_tree(root,corrupt())}
    altered['report_content_sha256']=policy._digest({k:v for k,v in altered.items() if k!='report_content_sha256'})
    assert not timeout_research_valid(altered,replay=report)


def test_empty_completed_census_with_open_rows_is_valid_empty(tmp_path):
    parent,path=parent_fixture(tmp_path)
    report=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=[{**actual_fact(),'status':'OPEN'}],entry_on_or_after=policy.refresh_window(parent))
    result=policy.evaluate_refresh_quantity_candidate(report,parent_policy=parent,parent_policy_file_sha256=policy._file_sha256(path),terminal_receipt=policy._natural_refresh_terminal_receipt(report))
    assert result['economic_sample_status']=='valid_empty'


@pytest.mark.parametrize('fields,reason',[
    ({'capture_queue_rejected_count':'7'},'capture_queue_gap'),
    ({'capture_clock_status':'order_start_source_gap'},'capture_clock_gap'),
    ({'capture_clock_status':'capture_clock_invalid'},'capture_clock_gap'),
    ({'capture_queue_rejected_count':True},'capture_queue_count_invalid'),
    ({'capture_queued_count':-1},'capture_queue_count_invalid'),
    ({'capture_queued_count':'9'*5000},'capture_queue_count_invalid'),
])
def test_capture_loss_excludes_counterfactuals_and_preserves_actual_control(fields,reason):
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    path['order_starts'][0].update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60)
    source=dict(context=_cap_context(budget=1600,actual_qty=4),attempt_id='a',plan_sha256='b'*64,
        capture_receipts=[dict(fields=dict(entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,**fields))])
    assert policy._cap_candidate_trade(trade,source,'cap_10pct',.0023)=={'status':reason}
    # All non-control tuples must be loss, even if their model would fill nothing.
    for mode in ('parent_5stage',*policy._CAP_MODES):
        for shape in policy._SHAPES:
            for horizon in (None,60,1200):
                value=execution_case(trade,path,source,mode=mode,shape=shape,horizon=horizon)
                if (mode,shape,horizon)==('parent_5stage','parent',None):
                    assert value['observation_coverage']=='actual_fills'
                    assert value['modeled_filled_qty']==4
                else:
                    assert value==dict(status='source_gap',reason=reason)
    source['capture_receipts'][0]['fields']['entry_submit_attempt_id']='foreign'
    assert policy._capture_source_issue(source) is None
    source['capture_receipts']=[]
    assert policy._capture_source_issue(source) is None


def _complete_capture_source():
    start = datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    identity = dict(entry_submit_attempt_id='a', entry_execution_sizing_plan_sha256='b'*64,
        capture_source_date='2026-10-08', capture_runtime_pid=123, capture_runtime_start_ticks='456')
    order = dict(capture_order_start_epoch=start, capture_end_epoch=start+1200,
        capture_queue_rejected_count=0, capture_queued_count=5, capture_clock_status='frozen_order_start')
    return dict(attempt_id='a', plan_sha256='b'*64, runtime_pid=123,
        capture_source_date='2026-10-08', capture_terminal_required=True, capture_receipts=[
            dict(stage='initial_quantity_cap_capture_started', at='2026-10-08T09:29:59+09:00',
                fields={**identity, 'capture_clock_status': 'no_order_start_observed'}),
            dict(stage='initial_quantity_cap_capture_order_started', at='2026-10-08T09:30:00+09:00', fields={**identity, **order}),
            dict(stage='initial_quantity_cap_capture_finished', at='2026-10-08T09:50:01+09:00', fields={**identity, **order})])


@pytest.mark.parametrize('mutation,reason', [
    ('complete', None), ('missing', 'capture_terminal_missing'),
    ('interrupt', 'capture_interrupted'), ('conflict', 'capture_terminal_conflict'),
    ('pid', 'capture_runtime_identity_mismatch'), ('start_ticks', 'capture_runtime_identity_mismatch'),
    ('date', 'capture_runtime_identity_mismatch'), ('short_horizon', 'capture_horizon_unverified'),
    ('early_terminal', 'capture_horizon_unverified'),
])
def test_capture_lifecycle_requires_original_identity_and_real_horizon(mutation, reason):
    source = _complete_capture_source()
    terminal = source['capture_receipts'][-1]
    if mutation == 'missing':
        source['capture_receipts'].pop()
    elif mutation == 'interrupt':
        terminal['stage'] = 'initial_quantity_cap_capture_interrupted'
        terminal['at'] = '2026-10-08T09:31:00+09:00'
        terminal['fields'].update(capture_disposition='interrupted', capture_interruption_reason='position_completed_before_capture_horizon')
    elif mutation == 'conflict':
        source['capture_receipts'].append({**copy.deepcopy(terminal), 'stage': 'initial_quantity_cap_capture_interrupted'})
    elif mutation in {'pid', 'start_ticks', 'date'}:
        key, value = {'pid': ('capture_runtime_pid', 999), 'start_ticks': ('capture_runtime_start_ticks', '457'),
                      'date': ('capture_source_date', '2026-10-07')}[mutation]
        terminal['fields'][key] = value
    elif mutation == 'short_horizon':
        terminal['fields']['capture_end_epoch'] -= 1
    elif mutation == 'early_terminal':
        terminal['at'] = '2026-10-08T09:49:59+09:00'
    assert policy._capture_source_issue(source) == reason


def test_capture_interruption_uses_candidate_horizon_and_original_fixed_exit():
    source = _complete_capture_source()
    source['capture_receipts'][-1].update(stage='initial_quantity_cap_capture_interrupted',
                                         at='2026-10-08T09:31:00+09:00')
    source['capture_receipts'][-1]['fields'].update(capture_disposition='interrupted',
        capture_interruption_reason='position_completed_before_capture_horizon')
    start = datetime.fromisoformat('2026-10-08T09:30:00+09:00').timestamp()
    assert policy._capture_source_issue(source, horizon_seconds=60, order_start_epoch=start) is None
    assert policy._capture_source_issue(source, horizon_seconds=61, order_start_epoch=start) == 'capture_interrupted'
    assert policy._capture_source_issue(source) == 'capture_interrupted'
    source['capture_exit_epoch'] = start + 60
    assert policy._capture_source_issue(source) is None
    source['capture_receipts'][-1]['fields']['capture_interruption_reason'] = 'prior_process_ended_before_terminal'
    source['capture_receipts'][-1]['at'] = '2026-10-09T08:00:00+09:00'
    assert policy._capture_source_issue(source, horizon_seconds=30) == 'capture_interrupted'
    assert policy._capture_source_issue(source, horizon_seconds=None) == 'capture_horizon_unverified'


def test_capture_tick_cannot_cross_original_process_epoch():
    source = _complete_capture_source()
    source['following_ticks'] = [dict(attempt_id='a', plan_sha256='b'*64,
        capture_source_date='2026-10-08', capture_runtime_pid='123', capture_runtime_start_ticks='456')]
    assert policy._capture_source_issue(source) is None
    source['following_ticks'][0]['capture_runtime_start_ticks'] = '457'
    assert policy._capture_source_issue(source) == 'capture_runtime_identity_mismatch'


def _durable_interruption(root, *, record_id=1):
    from src.engine.scalping import initial_quantity_cap_observation as producer
    fields = _complete_capture_source()['capture_receipts'][-1]['fields']
    fields = {**fields, 'capture_disposition': 'interrupted',
              'capture_record_id': record_id, 'capture_stock_code': '005930',
              'capture_interruption_reason': 'prior_process_ended_before_terminal'}
    capture_id = producer._capture_id(fields)
    path = root/'runtime/initial_quantity/cap_capture_receipts/2026-10-08'/f'{capture_id}.json'
    producer._atomic_receipt(path, dict(schema='initial_quantity_cap_capture_lifecycle_v1',
        capture_id=capture_id, code='005930', name='native', record_id=record_id,
        fields=fields, observed_at_epoch=datetime.fromisoformat('2026-10-09T08:00:00+09:00').timestamp(),
        status='interrupted', raw_event_durable=True, raw_event_id='a'*64,
        raw_event_identity_contract='canonical_original_pipeline_event_sha256_v1',
        raw_event_stage='initial_quantity_cap_capture_interrupted', runtime_effect=False))
    return path


def test_late_capture_interruption_invalidates_feature_cache_and_report_source(tmp_path, monkeypatch):
    day = '2026-10-08'
    _quality(tmp_path, day)
    trades, _ = policy.completed_trade_fact_census(day, data_dir=tmp_path, fact_rows=[actual_fact()])
    pipeline = tmp_path/'pipeline_events'
    pipeline.mkdir()
    (pipeline/f'pipeline_events_{day}.jsonl').write_text('{}\n')
    before = policy.join_post_fill_paths(trades, data_dir=tmp_path)
    assert before[trades[0]['trade_id']]['capture_receipts'] == []
    path = _durable_interruption(tmp_path)
    original = policy._join_post_fill_paths_uncached
    scans = []
    def counted(rows, **kwargs):
        scans.append(len(rows))
        return original(rows, **kwargs)
    monkeypatch.setattr(policy, '_join_post_fill_paths_uncached', counted)
    sources = {}
    after = policy.join_post_fill_paths(trades, data_dir=tmp_path, source_receipts=sources)
    assert scans == [1]
    receipts = after[trades[0]['trade_id']]['capture_receipts']
    assert len(receipts) == 1 and receipts[0]['durable_source'] == 'native_closed_lifecycle_receipt'
    assert receipts[0]['fields']['capture_source_date'] == day
    assert receipts[0]['at'].astimezone(ZoneInfo('Asia/Seoul')).date().isoformat() == '2026-10-09'
    source = {**_complete_capture_source(), 'capture_receipts': receipts}
    assert policy._capture_source_issue(source) == 'capture_interrupted'
    policy.join_post_fill_paths(trades, data_dir=tmp_path)
    assert scans == [1]
    monkeypatch.setattr(policy, 'DATA_DIR', tmp_path)
    report = {'census': {}, 'pipeline_source_receipts': sources}
    policy.verify_refresh_source_generations(report)
    with path.open('ab') as handle:
        handle.write(b' ')
    with pytest.raises(ValueError, match='quantity_capture_lifecycle_generation_changed'):
        policy.verify_refresh_source_generations(report)


@pytest.mark.parametrize('mutation', ['hash', 'day', 'pid', 'ticks', 'attempt', 'plan', 'raw_durable', 'stage', 'link'])
def test_durable_capture_receipt_rejects_unbound_or_corrupt_proof(tmp_path, mutation):
    from src.engine.scalping import initial_quantity_cap_observation as producer
    path = _durable_interruption(tmp_path)
    body = json.loads(path.read_bytes())
    if mutation == 'link':
        other = path.with_suffix('.saved')
        path.rename(other)
        path.symlink_to(other)
    elif mutation == 'hash':
        with path.open('ab') as handle:
            handle.write(b'x')
    else:
        if mutation in {'day', 'pid', 'ticks', 'attempt', 'plan'}:
            key, value = {'day': ('capture_source_date', '2026-10-07'), 'pid': ('capture_runtime_pid', 999),
                'ticks': ('capture_runtime_start_ticks', '457'), 'attempt': ('entry_submit_attempt_id', 'foreign'),
                'plan': ('entry_execution_sizing_plan_sha256', 'c'*64)}[mutation]
            body['fields'][key] = value
        elif mutation == 'raw_durable':
            body['raw_event_durable'] = False
        elif mutation == 'stage':
            body['raw_event_stage'] = 'initial_quantity_cap_capture_finished'
        body.pop('sha256')
        producer._atomic_receipt(path, body)
    with pytest.raises((ValueError, OSError)):
        policy._quantity_capture_lifecycle_sources(tmp_path, '2026-10-08', decode=True)


@pytest.mark.parametrize('end,now',[(True,1),(float('nan'),1),(0,1),(1200,-1)])
def test_capture_invalid_bounds_are_explicit_not_normal_completion(monkeypatch,end,now):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    start=1000.;events=[]
    monkeypatch.setattr(observer,'append',lambda **kw:(events.append(kw) or True))
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=start,order_capture_end_epoch=end,
               entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_clock_status='frozen_order_start'))
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=start+now)
    assert len(events)==1
    assert events[0]['fields']['capture_clock_status']=='capture_clock_invalid'
    json.dumps(events[0],allow_nan=False)
    assert '_initial_quantity_cap_trace' not in stock


@pytest.mark.parametrize('now',[float('nan'),True,0])
def test_capture_invalid_observer_clock_retains_gap_until_real_terminal(monkeypatch,now):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    events=[];monkeypatch.setattr(observer,'append',lambda **kw:(events.append(kw) or True))
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=1000.,order_capture_end_epoch=2200.,capture_clock_status='frozen_order_start'))
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=now)
    assert events==[] and stock['_initial_quantity_cap_trace']['capture_clock_status']=='capture_clock_invalid'
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=2201.)
    assert events[0]['fields']['capture_clock_status']=='capture_clock_invalid'


def test_oversized_execution_index_rebuilds_without_unbounded_read(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    trade,path=_research_trade_path();trade.update(quantity_type='KRX_PARENT',comparison_cost_rate=.0023)
    path['order_starts'][0].update(source='initial_quantity_bundle_order_start_at',total_wait_sec=60)
    tid=trade['trade_id'];source=dict(context=_cap_context(budget=1600,actual_qty=4),attempt_id='a',plan_sha256='b'*64)
    rows={tid:dict(quantity_type='KRX_PARENT',cap_source=source)}
    grid={'control':dict(mode='parent_5stage',shape='parent',horizon=None,reserve=5)}
    def run():return list(cache.joint_records([trade],{tid:path},rows,grid,data_dir=tmp_path,cost_rate=.0023))
    expected=run();index=next(tmp_path.rglob('index.json'))
    with index.open('wb') as handle:handle.truncate(cache.storage.RECORD_BYTES+1)
    original=Path.read_bytes
    def checked(p):
        if p==index:pytest.fail('unbounded index read')
        return original(p)
    monkeypatch.setattr(Path,'read_bytes',checked)
    assert run()==expected
    assert len(list(index.parent.glob('repair-*')))==1
    assert run()==expected


def test_capture_terminal_refusal_keeps_exact_gap_for_bounded_retry(monkeypatch):
    from src.engine import sniper_state_handlers as handler
    from src.engine.scalping import initial_quantity_cap_observation as observer
    events=[]
    def submit(**kw):
        events.append(kw)
        return len(events)==3
    monkeypatch.setattr(observer,'append',submit)
    stock=dict(_initial_quantity_cap_trace=dict(started_at_epoch=1000.,order_capture_end_epoch=2200.,
        entry_submit_attempt_id='a',entry_execution_sizing_plan_sha256='b'*64,capture_clock_status='frozen_order_start'))
    for now in (2201.,2202.):
        handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=now)
        assert stock['_initial_quantity_cap_trace']['capture_terminal_pending'] is True
    handler._observe_initial_quantity_cap_following_tick(stock,'005930',{},now_ts=2203.)
    assert '_initial_quantity_cap_trace' not in stock
    assert [e['fields']['capture_queue_rejected_count'] for e in events]==[0,1,2]
    assert all(e['fields']['entry_submit_attempt_id']=='a' for e in events)


def test_feature_cache_invalidates_transitive_reader_change(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    _quality(tmp_path,'2026-10-08');pipeline=tmp_path/'pipeline_events';pipeline.mkdir()
    (pipeline/'pipeline_events_2026-10-08.jsonl').write_text('{}\n')
    facts=[actual_fact()]
    def run():return policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=facts,entry_on_or_after='2026-09-29')
    expected=run();scans=[];join=policy._join_post_fill_paths_uncached
    def count(rows,**kw):scans.extend(r['entry_date'] for r in rows);return join(rows,**kw)
    monkeypatch.setattr(policy,'_join_post_fill_paths_uncached',count)
    assert run()==expected and scans==[]
    original=Path.read_bytes;reader=Path(cache.__file__).with_name('initial_quantity_cap_observation.py')
    monkeypatch.setattr(Path,'read_bytes',lambda p:original(p)+b'\n# changed reader\n' if p==reader else original(p))
    assert run()==expected and scans==['2026-10-08']
    scans.clear()
    assert run()==expected and scans==[]


def test_index_growth_race_is_bounded_before_decode(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    import os
    index=tmp_path/'index.json'
    with index.open('wb') as handle:handle.truncate(cache.storage.RECORD_BYTES+1)
    original=Path.stat
    def old_size(p,**kw):
        stat=original(p,**kw)
        if p==index:
            parts=list(stat);parts[6]=1
            return os.stat_result(parts)
        return stat
    monkeypatch.setattr(Path,'stat',old_size)
    monkeypatch.setattr(cache.json,'loads',lambda *a,**k:pytest.fail('oversize decode'))
    with pytest.raises(ValueError,match='cache_index_invalid'):cache._read_index(index)


def test_native_capture_loss_is_isolated_before_joint_policy_selection(tmp_path):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research,timeout_research_valid
    from src.engine.scalping.initial_quantity_refresh_evaluation import read_joint_cases
    parent,path,facts,pid=_positive_joint_fixture(tmp_path)
    leaf=tmp_path/'pipeline_events/pipeline_events_2026-10-05.jsonl'
    event=_event(100,'initial_quantity_cap_capture_finished','2026-10-05T09:51:00+09:00',
        entry_submit_attempt_id='100',entry_execution_sizing_plan_sha256='b'*64,
        capture_queue_rejected_count='1',capture_queued_count='20',capture_clock_status='frozen_order_start')
    event['stock_code']='005930'
    with leaf.open('a') as handle:handle.write(json.dumps(event)+'\n')
    shared={}
    report=policy.build_initial_quantity_replay('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared)
    timeout=build_timeout_research('2026-10-07',data_dir=tmp_path,fact_rows=facts,entry_on_or_after=policy.refresh_window(parent),path_cache=shared,replay=report)
    assert timeout_research_valid(timeout,replay=report)
    cases=read_joint_cases(timeout)
    affected=next(r for r in report['trades'] if str(r['record_id'])=='100')
    assert all(v['status']=='capture_queue_gap' for v in affected['cap_candidates'].values())
    valid={tid for tid,values in cases.items() if any(v['status']!='source_gap' for key,v in values.items() if key!='parent_5stage:parent:None')}
    assert len(valid)==59 and affected['trade_id'] not in valid


def _quantity_completion_overlay_fixture(tmp_path, monkeypatch, *, day='2026-10-08', actual=False,
                                         terminal_price=101000, identity=None, meta_overrides=None):
    from src.engine import log_archive_service as archive
    from src.engine import strategy_position_performance_report as native
    from src.engine.lifecycle import broker_cost_reconciliation as costs
    from src.engine.sniper_trade_review_report import completed_census_manifest, strategy_fact_projection_rows
    monkeypatch.setattr(archive, 'MONITOR_SNAPSHOT_DIR', tmp_path/'report/monitor_snapshots')
    monkeypatch.setattr(native, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(native, '_FACT_SYNC_STATUS_DIR', tmp_path/'report/strategy_position_fact_sync')
    monkeypatch.setattr(policy, 'DATA_DIR', tmp_path)
    if actual:
        monkeypatch.setattr(costs, 'source_generation', lambda root, target: dict(
            schema='holding_actual_cost_source_generation_v1', completion_date=target,
            count=1, sha256='d'*64, status='observed'))
        from src.engine.lifecycle import holding_window_generation
        monkeypatch.setattr(holding_window_generation, 'source_generation', costs.source_generation)
    entry='2026-10-07'
    original={**actual_fact(day=entry), 'status':'HOLDING', 'sell_price':None, 'sell_time':None,
              'profit_rate':None, 'realized_pnl_krw':None, 'economics_source_status':'fixed_comparison_cost_model',
              'actual_cost_reconciliation_status':None, 'actual_cost_source_generation':None,
              'completion_census_run_id':None,'completion_census_projection_sha256':None,
              'broker_actual_fees_taxes_krw':None,'add_count':0,'avg_down_count':0,'pyramid_count':0,
              'fact_generation':{'issue':None, 'path':str(tmp_path/'entry.json'),'sha256':'a'*64}}
    row=dict(id=1, rec_date=entry, code='005930', name='native', strategy='SCALPING',position_tag='SCANNER',
             status='COMPLETED',buy_price=100000,buy_qty=1,buy_time=entry+'T09:30:00+09:00',
             sell_price=terminal_price,sell_time='2026-10-08T10:00:00+09:00',
             completion_observed_date=day,terminal_population_scope='real_record_bound',
             strict_completion_status='eligible' if actual else 'excluded',
             broker_actual_cost_observed=actual,broker_actual_fees_taxes_krw=200 if actual else None,
             realized_pnl_krw=terminal_price-100000-200 if actual else None,
             profit_rate=(terminal_price-100000-200)/1000 if actual else None,
             realized_pnl_krw_source='broker_actual_fee_reconciled' if actual else 'missing_exact_cost',
             actual_cost_reconciliation={'status':'actual_cost_reconciled' if actual else 'actual_cost_unallocated'},
             exit_signal={'inferred':False,'binding_status':'same_order_generation'})
    row.update(identity or {})
    payload=dict(date=day,code=None,since=None,scope='entered',
                 meta=dict(snapshot_profile='postclose_exit',warnings=[],sell_completed_event_ids=[1],
                           actual_cost_source_generation=costs.source_generation(tmp_path,day)),
                 metrics=dict(total_trades=0,canonical_completed_trades=1),
                 sections=dict(recent_trades=[],strategy_position_fact_projection=strategy_fact_projection_rows([]),
                               completed_trade_projection=[row],open_scalp_position_projection=[]))
    payload['meta'].update(meta_overrides or {})
    payload['meta']['completed_census_manifest']=completed_census_manifest(payload)
    path=archive.save_monitor_snapshot('trade_review',day,payload)
    source=native._load_completion_fact_projection(day,path)
    native._write_status(day,dict(status='valid_empty',consumer_ready=True,
        completed_census_run_ids=[payload['meta']['completed_census_manifest']['run_id']],
        completed_census_projection_sha256=[payload['meta']['completed_census_manifest']['projection_sha256']],
        actual_cost_source_generation=payload['meta']['actual_cost_source_generation'],
        completion_snapshot_source=source['_native_source_proof']))
    return original,path


def _overlay_for_test(tmp_path, rows, *, as_of='2026-10-08', issue=None):
    from src.engine.scalping.initial_quantity_source_cache import completion_overlay
    return completion_overlay(rows, as_of=as_of, data_dir=tmp_path, entry_on_or_after='2026-09-29',
        entry_generations={'2026-10-08':{'issue':issue}}, validate_day=lambda day:None)


@pytest.mark.parametrize('fault',[None,'missing_manifest','archive_changed'])
def test_original_stream_entry_seal_survives_preservation_then_compression(tmp_path,monkeypatch,fault):
    import os,hashlib
    from src.engine import strategy_position_performance_report as facts
    from src.engine import compress_db_backfilled_files as compression
    from src.engine.lifecycle.holding_window_generation import seal_dependency_receipt
    day='2026-10-08'
    _,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,day=day)
    sidecar=path.with_suffix('.completed_projection.json');projection=json.loads(sidecar.read_bytes())
    # Older native entry batches have an original stream proof and no scalar
    # projection. Reproduce that native producer/consumer contract unchanged.
    seal_dependency_receipt(sidecar,projection)
    path.with_suffix('.fact_projection.json').unlink()
    source=facts._load_completion_fact_projection(day,path)
    assert source['_native_source_proof']['source_basis']=='native_original_snapshot_stream'
    census=projection['meta']['completed_census_manifest']
    facts._write_status(day,dict(status='valid_empty',consumer_ready=True,
        completed_census_run_ids=[census['run_id']],
        completed_census_projection_sha256=[census['projection_sha256']],
        actual_cost_source_generation=projection['meta']['actual_cost_source_generation'],
        completion_snapshot_source=source['_native_source_proof']))
    original_status=facts._status_path(day).read_bytes()
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=path.parent/'manifests'/f'monitor_snapshot_manifest_{day}_postclose_exit.json'
    manifest.parent.mkdir(exist_ok=True)
    manifest.write_text(json.dumps(dict(target_date=day,profile='postclose_exit',
        snapshot_paths={'trade_review':str(path)},snapshot_sha256={'trade_review':sha})))
    os.link(path,path.with_suffix('.preserved'))
    monkeypatch.setattr(compression,'MONITOR_SNAPSHOT_DIR',path.parent)
    assert compression._gzip_file(path,dry_run=False)[0]
    if fault=='missing_manifest':manifest.unlink()
    elif fault=='archive_changed':
        archived=Path(str(path)+'.gz');archived.write_bytes(archived.read_bytes()+b'x')
    issue=policy._quantity_original_fact_generation_issue(day)
    assert (issue is None) is (fault is None)
    assert facts._status_path(day).read_bytes()==original_status


@pytest.mark.parametrize('missing_source', [False, True])
def test_late_cost_revision_reallocates_without_resealing_original_facts(tmp_path, monkeypatch, missing_source):
    from copy import deepcopy
    from src.engine.lifecycle import broker_cost_allocation as allocation
    from src.engine.lifecycle import broker_cost_source as official
    from src.engine.lifecycle import broker_cost_reconciliation as costs
    from src.engine.lifecycle import main_stop_research_cost as native_cost
    from src.engine.scalping import initial_quantity_source_cache as cache
    from src.engine.scalping import initial_quantity_monitor_projection as monitor
    from src.tests.test_broker_cost_allocation import source, position
    from src.tests.test_main_stop_research_cost import registry
    day = '2026-10-08'
    item = position(1)
    observed = source(tmp_path)
    official.atomic(official.source_path(tmp_path, day), observed)
    registry(tmp_path, [item])
    receipts = allocation.build_research_cost_allocations({day:observed}, [item])
    allocation.persist_research_costs(tmp_path, day, receipts, [day])
    original, path = _quantity_completion_overlay_fixture(tmp_path, monkeypatch, identity=dict(
        rec_date=day, buy_time=day+'T10:00:00+09:00', sell_time=day+'T10:01:00+09:00',
        buy_qty=2, buy_price=10000, sell_price=10100, buy_fill_legs=item['buy_legs'],
        sell_fill_legs=item['sell_legs'], sell_quantity_conserved=True, position_residual_qty=0,
        exact_sell_fill_time=item['completed_at'],
        terminal_decision_authority='broker_sell_fill_observation_only',
        strict_completion_reasons=['source_gap_broker_actual_cost_missing'], quantity_research_cost=receipts['1']))
    original.update(rec_date=day, buy_time=day+'T10:00:00+09:00', buy_qty=2, buy_price=10000)
    immutable = [path, path.with_suffix('.completed_projection.json'),
                 path.with_suffix('.fact_projection.json'),
                 Path(str(path.with_suffix('.completed_projection.json'))+'.dependencies.json'),
                 tmp_path/'report/strategy_position_fact_sync'/f'strategy_position_fact_sync_{day}.status.json']
    before = {p:p.read_bytes() for p in immutable}
    index_path = tmp_path/'runtime/initial_quantity_research_costs'/day/'index.json'
    index_before = index_path.read_bytes()
    revised = deepcopy(observed)
    revised['observations']['ka10170']['pages'][0]['tdy_trde_diary'][0]['cmsn_alm_tax'] = '41'
    revised['source_sha256'] = costs.digest({k:v for k,v in revised.items() if k != 'source_sha256'})
    official.atomic(official.source_path(tmp_path, day), revised)
    if missing_source:
        official.source_path(tmp_path, day).unlink()
    assert policy._quantity_fact_generation_issue(day) == 'fact_snapshot_native_projection_invalid'
    assert policy._quantity_original_fact_generation_issue(day) is None
    calls = []
    full_read = native_cost._native_projection
    def counted(*args, **kwargs):
        calls.append(args[1])
        return full_read(*args, **kwargs)
    monkeypatch.setattr(native_cost, '_native_projection', counted)
    for _ in range(2):
        cache.prepare_completion_cost_revisions(tmp_path, day, day,
            validate_day=policy._quantity_original_fact_generation_issue)
    assert calls == [day]
    assert {p:p.read_bytes() for p in immutable} == before
    import hashlib
    assert (index_path.parent/'index_generations'/(hashlib.sha256(index_before).hexdigest()+'.json')).read_bytes() == index_before
    rows = _overlay_for_test(tmp_path, [original])
    current = rows[0]
    assert current['profit_rate'] is None and current['realized_pnl_krw'] is None
    assert current['economics_source_status'] != 'broker_actual_cost_reconciled'
    receipt = policy._quantity_research_fact_cost(current)
    if missing_source:
        assert receipt['status'] == 'research_cost_invalid'
        assert receipt.get('allocated_net_pnl_krw') is None
    else:
        assert receipt['status'] == 'research_cost_allocated'
        assert receipt['allocated_fees_taxes_krw'] == 21
        assert receipt['sources'][0]['source_sha256'] == revised['source_sha256']
        assert receipt['actual_execution_cost'] is False
    report = {'census':{'completion_overlay_generations':rows.completion_generations}}
    assert monitor._costs(report, tmp_path) == [{'source_date':day, 'generation':costs.source_generation(tmp_path,day)}]
    cache.verify_completion_overlay_generations(rows.completion_generations, data_dir=tmp_path)
    from src.engine.lifecycle import holding_window_generation as window
    current_window = window.capture_window(tmp_path, [day], allow_cost_revision=True)
    dependency = current_window['dependencies'][day]
    assert dependency['status'] == 'observed'
    assert dependency['original_cost_generation'] == json.loads(before[immutable[2]])['meta']['actual_cost_source_generation']
    assert dependency['cost_generation'] == costs.source_generation(tmp_path, day)
    window.verify_window(tmp_path, current_window)
    assert window.capture_window(tmp_path, [day])['dependencies'][day]['status'] == 'source_gap'
    from src.tests.test_main_trailing_source_assembler import fixture as trailing_fixture
    from src.engine.automation import main_trailing_source_assembler as assembler
    from src.engine.automation import main_trailing_all_scope_research as research
    from src.engine.lifecycle import research_storage as storage
    trailing_fixture(tmp_path)
    manifest_path = assembler.assemble(tmp_path, tmp_path.parent/(tmp_path.name+'-trailing'),
        source_date=day, target_date='2026-10-12', start_date=day)
    manifest = research._sealed(manifest_path)
    positions = [position for part in storage.iter_tree(manifest_path.parent, manifest['partitions_ref'])
                 for position in research._sealed(manifest_path.parent/part['path'])['positions']
                 if position['evidence_kind'] == 'actual_completed']
    assert [position['position_key'] for position in positions] == ['1']
    assert manifest['assembly_census']['source_gaps'].get('completed_snapshot_source_gap',0) == 0
    assert positions[0]['actual_cost_reconciliation'] == {'status':'actual_cost_unallocated', 'reason':'late_cost_revision'}
    assert positions[0]['current_cost_generation_sha256'] == costs.digest(dependency['cost_generation'])
    index_after = index_path.read_bytes()
    # A further source revision invalidates the derivative, never the original
    # terminal bytes. No observer may silently refresh it while validating.
    if not missing_source:
        revised['observations']['ka10170']['pages'][0]['tdy_trde_diary'][0]['cmsn_alm_tax'] = '43'
        revised['source_sha256'] = costs.digest({k:v for k,v in revised.items() if k != 'source_sha256'})
        official.atomic(official.source_path(tmp_path,day), revised)
        with pytest.raises(ValueError, match='quantity_completion_generation_changed'):
            cache.verify_completion_overlay_generations(rows.completion_generations, data_dir=tmp_path)
    assert {p:p.read_bytes() for p in immutable} == before
    assert index_path.read_bytes() == index_after


@pytest.mark.parametrize('fractional', [False, True])
def test_bounded_completion_projection_retains_quantity_receipt_without_global_pnl(monkeypatch, tmp_path, fractional):
    from src.engine import strategy_position_performance_report as native
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    fact = (_fractional_allocated_quantity_fact if fractional else _allocated_quantity_fact)(tmp_path, record_id=1)
    receipt = fact['quantity_research_cost']
    identity = dict(rec_date='2026-10-08', buy_price=fact['buy_price'], buy_qty=fact['buy_qty'],
        buy_time=fact['buy_time'], sell_price=fact['sell_price'], sell_time=fact['sell_time'],
        quantity_research_cost=receipt)
    original, path = _quantity_completion_overlay_fixture(tmp_path, monkeypatch, identity=identity)
    original.update({key:fact[key] for key in ('rec_date', 'buy_price', 'buy_qty', 'buy_time')})
    projected = native._load_completion_fact_projection('2026-10-08', path)
    assert projected['sections']['completed_trade_projection'][0]['quantity_research_cost'] == receipt
    completed = [{**row, 'strategy': 'SCALPING'} for row in projected['sections']['completed_trade_projection']]
    canonical = native._trade_fact_rows_from_report('2026-10-08', {
        'meta': projected['meta'], 'sections': {'recent_trades': completed,
        'completed_trade_projection': completed}})
    assert canonical[0]['profit_rate'] is None and canonical[0]['realized_pnl_krw'] is None
    overlaid = _overlay_for_test(tmp_path, [original])
    assert overlaid[0]['quantity_research_cost'] == receipt
    assert overlaid[0]['profit_rate'] is None and overlaid[0]['realized_pnl_krw'] is None
    assert overlaid[0]['actual_cost_source_generation']['quantity_research_cost_generation']['projection_scope'] == 'record'
    assert overlaid[0]['completion_generation']['schema'] == 'initial_quantity_completion_generation_reference_v1'
    assert overlaid.completion_generations['2026-10-08']['completion_snapshot_source']['actual_cost_source_generation']['quantity_research_cost_generation'].get('projection_scope') is None
    _quality(tmp_path, '2026-10-08')
    report = policy.build_initial_quantity_replay('2026-10-08', data_dir=tmp_path,
        fact_rows=overlaid, entry_on_or_after='2026-09-29')
    assert report['trades'][0]['actual_net_pnl_krw'] == receipt['allocated_net_pnl_krw']
    assert report['trades'][0]['actual_execution_cost'] is False
    assert policy.initial_replay_economics_valid(report)
    serialized = json.loads(json.dumps(report))
    timeout = build_timeout_research('2026-10-08', data_dir=tmp_path,
        fact_rows=serialized['census']['input_fact_rows'], entry_on_or_after='2026-09-29', replay=serialized)
    assert timeout['census'] == serialized['census']


def test_native_fact_record_cost_generations_remain_linear_for_1000_positions():
    from src.engine import strategy_position_performance_report as native
    day = '2026-10-08'
    generation = dict(schema='holding_actual_cost_source_generation_v1', completion_date=day,
        count=0, sha256='g'*64, status='cost_source_unavailable', quantity_research_cost_generation=dict(
            receipts=[dict(record_id=str(rid), sha256='a'*64, content_sha256='b'*64, receipt_sha256='c'*64)
                      for rid in range(1, 1001)],
            source_dates=[dict(source_date=day, sha256='d'*64, source_sha256='e'*64)]))
    original = copy.deepcopy(generation)
    completed = [dict(id=rid, rec_date=day, code='005930', strategy='SCALPING', position_tag='SCANNER',
        status='COMPLETED', buy_price=100, buy_qty=4, buy_time=day+'T09:30:00+09:00',
        sell_price=110, sell_time=day+'T09:35:00+09:00', completion_observed_date=day,
        terminal_population_scope='real_record_bound', strict_completion_status='excluded',
        quantity_research_cost=dict(sources=[dict(source_date=day)])) for rid in range(1, 1001)]
    report = dict(meta=dict(completed_census_manifest=dict(actual_cost_source_generation=generation)),
        sections=dict(recent_trades=completed, completed_trade_projection=completed))
    converted = native._trade_fact_rows_from_report(day, report)
    costs = [row['actual_cost_source_generation'] for row in converted]
    assert len(costs) == 1000 and generation == original
    assert all(len(cost['quantity_research_cost_generation']['receipts']) == 1 for cost in costs)
    assert all(cost['quantity_research_cost_generation']['parent_generation_sha256'] == generation['sha256'] for cost in costs)
    assert sum(len(json.dumps(cost)) for cost in costs) < 2 * 1024 * 1024
    assert all(row['profit_rate'] is None and row['realized_pnl_krw'] is None for row in converted)


def test_newer_completion_without_research_receipt_clears_stale_cost(monkeypatch, tmp_path):
    original, _ = _quantity_completion_overlay_fixture(tmp_path, monkeypatch)
    original['quantity_research_cost'] = {'stale': True}
    overlaid = _overlay_for_test(tmp_path, [original])
    assert 'quantity_research_cost' not in overlaid[0]
    assert overlaid[0]['profit_rate'] is None and overlaid[0]['realized_pnl_krw'] is None


@pytest.mark.parametrize('actual',[False,True])
def test_native_completion_overlay_counts_carry_terminal_without_rewriting_entry_source(tmp_path,monkeypatch,actual):
    from src.engine.scalping.initial_quantity_source_cache import verify_completion_overlay_generations
    original,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,actual=actual)
    before=copy.deepcopy(original);raw=path.read_bytes()
    rows=_overlay_for_test(tmp_path,[original]);_quality(tmp_path,'2026-10-07');_quality(tmp_path,'2026-10-08')
    trades,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows)
    assert original==before and path.read_bytes()==raw
    assert rows[0]['status']=='COMPLETED' and rows[0]['original_fact_status']=='HOLDING'
    assert rows[0]['completion_source_date']=='2026-10-08' and rows[0]['rec_date']=='2026-10-07'
    assert rows[0]['fact_generation']==before['fact_generation']
    assert census['as_of_completed_population_count']==1
    assert census['completion_overlay_summary']['overlaid_record_ids']==['1']
    assert verify_completion_overlay_generations(census['completion_overlay_generations'],data_dir=tmp_path)['2026-10-08'][0]['status']=='COMPLETED'
    if actual:
        assert len(trades)==1 and trades[0]['realized_net_pnl_krw']==800
        assert trades[0]['terminal_source']=='native_completion_date_projection.completed_costed'
        assert census['excluded']=={}
    else:
        assert trades==[] and census['excluded']=={'terminal_cost_or_quantity_missing':1}
        assert census['actual_completed_net_pnl_krw'] is None
        assert rows[0]['profit_rate'] is rows[0]['realized_pnl_krw'] is None


def test_completion_overlay_preserves_asof_and_invalid_original_entry_proof(tmp_path,monkeypatch):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    before=_overlay_for_test(tmp_path,[original],as_of='2026-10-07')
    assert before[0]['status']=='HOLDING' and before.completion_generations=={}
    original['fact_generation']['issue']='original_entry_source_stale'
    rows=_overlay_for_test(tmp_path,[original])
    trades,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows)
    assert rows[0]['status']=='COMPLETED' and trades==[]
    assert census['excluded']=={'persisted_fact_generation_invalid':1}


@pytest.mark.parametrize('mutation',['code','quantity','buy_clock','owner','entry_date','terminal'])
def test_completion_overlay_rejects_contradictory_entry_or_existing_terminal(tmp_path,monkeypatch,mutation):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    if mutation=='code':original['stock_code']='000660'
    if mutation=='quantity':original['buy_qty']=2
    if mutation=='buy_clock':original['buy_time']='2026-10-07T09:31:00+09:00'
    if mutation=='owner':original['position_tag']='SCALP_BASE'
    if mutation=='entry_date':original['rec_date']='2026-10-06'
    if mutation=='scale_in':original['add_count']=1
    if mutation=='terminal':original.update(status='COMPLETED',sell_time='2026-10-08T10:01:00+09:00',sell_price=101000)
    with pytest.raises(ValueError,match='quantity_completion_'):_overlay_for_test(tmp_path,[original])


@pytest.mark.parametrize('mutation',['unsealed','dependency','cost','missing_entry','invalid_native','wrong_data_root'])
def test_completion_overlay_fails_closed_on_unsealed_stale_missing_or_foreign_source(tmp_path,monkeypatch,mutation):
    from src.engine.lifecycle import broker_cost_reconciliation as costs
    original,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    if mutation=='unsealed':
        with path.with_suffix('.fact_projection.json').open('ab') as handle:handle.write(b' ')
    if mutation=='dependency':
        with Path(str(path.with_suffix('.completed_projection.json'))+'.dependencies.json').open('ab') as handle:handle.write(b' ')
    if mutation=='cost':monkeypatch.setattr(costs,'source_generation',lambda *a:{'changed':True})
    if mutation=='wrong_data_root':
        # Explicit isolated input cannot borrow the globally configured native receipt.
        from src.engine.scalping.initial_quantity_source_cache import _completion_day
        with pytest.raises(FileNotFoundError):_completion_day(tmp_path/'other','2026-10-08')
        return
    with pytest.raises(ValueError,match='quantity_completion_'):
        _overlay_for_test(tmp_path,[] if mutation=='missing_entry' else [original],
                          issue='stale' if mutation=='invalid_native' else None)


def test_completion_overlay_source_changes_during_conversion_fail_before_escape(tmp_path,monkeypatch):
    from src.engine import strategy_position_performance_report as native
    original,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    converter=native._trade_fact_rows_from_report
    def changed(*args):
        result=converter(*args)
        with path.with_suffix('.fact_projection.json').open('ab') as handle:handle.write(b' ')
        return result
    monkeypatch.setattr(native,'_trade_fact_rows_from_report',changed)
    with pytest.raises(ValueError,match='quantity_completion_source_changed'):_overlay_for_test(tmp_path,[original])


@pytest.mark.parametrize('conflict',[False,True])
def test_completion_overlay_multiple_dates_preserve_one_monotonic_terminal(tmp_path,monkeypatch,conflict):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    _quantity_completion_overlay_fixture(tmp_path,monkeypatch,day='2026-10-09',terminal_price=102000 if conflict else 101000)
    if conflict:
        with pytest.raises(ValueError,match='quantity_completion_terminal_identity_conflict'):
            _overlay_for_test(tmp_path,[original],as_of='2026-10-09')
    else:
        rows=_overlay_for_test(tmp_path,[original],as_of='2026-10-09')
        assert len(rows)==1 and rows[0]['completion_source_date']=='2026-10-09'
        assert rows.completion_overlay_summary['overlaid_completed_count']==1
        assert set(rows.completion_generations)=={'2026-10-08','2026-10-09'}


def test_completion_overlay_bounded_observer_reads_only_three_small_files(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    from src.engine.lifecycle import snapshot_archive
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    rows=_overlay_for_test(tmp_path,[original]);reads=[]
    monkeypatch.setattr(snapshot_archive,'snapshot_identity',lambda *a:pytest.fail('native full archive verifier'))
    def bounded(path,*,expected_sha=None,limit):
        reads.append(path)
        raw=Path(path).read_bytes();assert len(raw)<=limit
        if expected_sha:assert hashlib.sha256(raw).hexdigest()==expected_sha
        return json.loads(raw)
    actual=cache.verify_completion_overlay_generations(rows.completion_generations,data_dir=tmp_path,read=bounded)
    assert actual['2026-10-08'][0]['recommendation_id']==1
    assert len(reads)==len(set(reads))==3
    assert all(p.stat().st_size<128*1024 for p in reads)


def test_completion_overlay_metadata_rejects_fifo_before_open(tmp_path):
    import os
    from src.engine.scalping.initial_quantity_source_cache import _completion_json
    path=tmp_path/'fifo.json';os.mkfifo(path)
    with pytest.raises(ValueError,match='quantity_completion_metadata_invalid'):_completion_json(path,128)


def test_completion_overlay_survives_native_snapshot_and_scalar_lossless_compression(tmp_path,monkeypatch):
    from src.engine import compress_db_backfilled_files as archive
    from src.engine.scalping import initial_quantity_source_cache as cache
    original,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    before=_overlay_for_test(tmp_path,[original]);proof=before.completion_generations
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',path.parent)
    for source in (path,path.with_suffix('.completed_projection.json'),path.with_suffix('.fact_projection.json')):
        assert archive._gzip_file(source,dry_run=False)[0]
    after=_overlay_for_test(tmp_path,[original])
    assert before==after and proof==after.completion_generations
    def bounded(logical,*,expected_sha=None,limit):
        from src.engine.lifecycle.snapshot_archive import read_bytes
        raw=read_bytes(logical,maximum=limit)
        if expected_sha:assert hashlib.sha256(raw).hexdigest()==expected_sha
        return json.loads(raw)
    # Original raw gzip is never decoded by this observer callback.
    assert cache.verify_completion_overlay_generations(proof,data_dir=tmp_path,read=bounded)['2026-10-08'][0]['status']=='COMPLETED'


def test_completion_overlay_cache_key_contains_terminal_generation_even_with_same_prices(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    monkeypatch.setattr(policy,'_quantity_capture_lifecycle_sources',lambda *a:({},[]))
    raw=tmp_path/'pipeline_events/pipeline_events_2026-10-07.jsonl';raw.parent.mkdir();raw.write_bytes(b'')
    trade=dict(trade_id='fact:1',record_id='1',stock_code='005930',entry_date='2026-10-07',exit_date='2026-10-08',
               entry_at_fact_buy_time='2026-10-07T09:30:00',exit_at='2026-10-08T10:00:00',completion_generation={'sha256':'a'*64})
    first=cache.fingerprint([trade],raw,600)
    second=cache.fingerprint([{**trade,'completion_generation':{'sha256':'b'*64}}],raw,600)
    assert first!=second


def test_allocated_cost_price_cache_reuses_only_identical_execution_inputs(tmp_path, monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    captures = {}
    monkeypatch.setattr(policy, '_quantity_capture_lifecycle_sources', lambda *a: (copy.deepcopy(captures), []))
    raw = tmp_path/'pipeline_events/pipeline_events_2026-10-07.jsonl'
    raw.parent.mkdir(); raw.write_bytes(b'')
    trade = dict(trade_id='fact:1', record_id='1', stock_code='005930', entry_date='2026-10-07',
        exit_date='2026-10-08', entry_at_fact_buy_time='2026-10-07T09:30:00', exit_at='2026-10-08T10:00:00',
        buy_qty=4, buy_price=100, sell_price=110, cost_basis='broker_confirmed_total_allocated',
        completion_generation={'sha256': 'a'*64}, fact_generation={'sha256': 'b'*64})
    first = cache.fingerprint([trade], raw, 600)
    assert first['schema'] == 'initial_quantity_source_features_v6'
    changed_cost = {**trade, 'completion_generation': {'sha256': 'c'*64},
        'fact_generation': {'sha256': 'd'*64}, 'realized_net_pnl_krw': 20, 'cost_available_at': 'later'}
    assert cache.fingerprint([changed_cost], raw, 600) == first
    for field, value in [('record_id', '2'), ('entry_at_fact_buy_time', '2026-10-07T09:31:00'),
                         ('exit_at', '2026-10-08T10:01:00'), ('buy_qty', 5), ('buy_price', 101), ('sell_price', 111)]:
        assert cache.fingerprint([{**trade, field: value}], raw, 600) != first
    assert cache.fingerprint([trade], raw, 1200) != first
    raw.write_bytes(b'changed')
    assert cache.fingerprint([trade], raw, 600) != first
    raw.write_bytes(b'')
    before_capture = cache.fingerprint([trade], raw, 600)
    captures['changed'] = 'source'
    assert cache.fingerprint([trade], raw, 600) != before_capture


def test_quantity_database_reader_overlays_carry_only_in_memory_and_keeps_entry_receipt(tmp_path,monkeypatch):
    from src.database import db_manager
    from src.engine import strategy_position_performance_report as native
    from src.engine.lifecycle.broker_cost_reconciliation import source_generation
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    engine=create_engine('sqlite:///:memory:');TradePerformanceFact.__table__.create(engine)
    native._write_status('2026-10-07',dict(status='succeeded',consumer_ready=True,
        actual_cost_source_generation=source_generation(tmp_path,'2026-10-07')))
    receipt=native._status_path('2026-10-07').read_bytes()
    record={k:v for k,v in original.items() if k!='fact_generation'}
    record.update(rec_date=date.fromisoformat(record['rec_date']),buy_time=datetime(2026,10,7,9,30))
    with Session(engine) as session,session.begin():session.add(TradePerformanceFact(**record))
    with Session(engine) as session:
        old_row=session.get(TradePerformanceFact,1)
        old_status=(old_row.status,old_row.sell_time,old_row.realized_pnl_krw)
    class DB:
        @contextmanager
        def get_session(self):
            with Session(engine) as session:yield session
    monkeypatch.setattr(db_manager,'DBManager',DB)
    monkeypatch.setattr(policy,'_quantity_fact_generation_issue',lambda day:None)
    before=policy._read_trade_facts('2026-10-07');after=policy._read_trade_facts('2026-10-08')
    assert before[0]['status']=='HOLDING' and after[0]['status']=='COMPLETED'
    assert after[0]['original_fact_status']=='HOLDING' and after[0]['fact_generation']['issue'] is None
    assert native._status_path('2026-10-07').read_bytes()==receipt
    with Session(engine) as session:
        row=session.get(TradePerformanceFact,1)
        assert (row.status,row.sell_time,row.realized_pnl_krw)==old_status


def test_completion_overlay_known_scale_in_stays_excluded_not_new_zero_history(tmp_path,monkeypatch):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    original['add_count']=1;original['avg_down_count']=1
    rows=_overlay_for_test(tmp_path,[original])
    trades,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows)
    assert rows[0]['add_count']==rows[0]['avg_down_count']==1
    assert trades==[] and census['excluded']=={'scale_in_position':1}


@pytest.mark.parametrize('field',['add_count','avg_down_count','pyramid_count'])
def test_completion_overlay_observed_positive_scale_in_excludes_economic_initial_trade(tmp_path,monkeypatch,field):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,actual=True,identity={field:1})
    rows=_overlay_for_test(tmp_path,[original]);trades,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows)
    assert rows[0][field]==1 and original[field]==0
    assert rows[0]['completion_scale_in_observations'][field]=={'source_date':'2026-10-08','value':1}
    assert trades==[] and census['excluded']=={'scale_in_position':1}


@pytest.mark.parametrize('value',[-1,0.5,True,None])
def test_completion_overlay_observed_invalid_scale_in_is_not_defaulted_to_zero(tmp_path,monkeypatch,value):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity={'add_count':value})
    with pytest.raises(ValueError,match='quantity_completion_scale_in_count_invalid'):_overlay_for_test(tmp_path,[original])


def test_completion_overlay_absent_terminal_scale_in_is_not_attested_zero(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    original['add_count']=1
    rows=_overlay_for_test(tmp_path,[original])
    projected=cache.verify_completion_overlay_generations(rows.completion_generations,data_dir=tmp_path)['2026-10-08'][0]
    assert 'add_count' not in projected
    assert rows[0]['add_count']==1 and rows[0]['completion_observed_scale_in_fields']==[]
    assert rows[0]['completion_scale_in_observations']=={}


def test_completion_overlay_rejects_decreasing_observed_scale_in_count(tmp_path,monkeypatch):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity={'add_count':0})
    original['add_count']=1
    with pytest.raises(ValueError,match='quantity_completion_scale_in_count_conflict'):_overlay_for_test(tmp_path,[original])


@pytest.mark.parametrize('mutation',['missing_receipt','unknown_basis'])
def test_completion_overlay_does_not_silently_skip_unowned_native_scalar(tmp_path,monkeypatch,mutation):
    from src.engine import strategy_position_performance_report as native
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    path=native._status_path('2026-10-08')
    if mutation=='missing_receipt':path.unlink()
    else:
        receipt=json.loads(path.read_bytes());receipt['completion_snapshot_source']['source_basis']='unknown'
        receipt['artifact_sha256']=native._canonical_sha256({k:v for k,v in receipt.items() if k!='artifact_sha256'})
        path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='quantity_completion_'):_overlay_for_test(tmp_path,[original])


def test_completion_overlay_metadata_open_race_cannot_block_on_fifo(tmp_path,monkeypatch):
    import os
    from src.engine.scalping.initial_quantity_source_cache import _completion_json
    path=tmp_path/'receipt.json';path.write_text('{}')
    original=os.open
    def replace(name,flags,*args,**kwargs):
        if Path(name)==path:
            path.unlink();os.mkfifo(path)
        return original(name,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',replace)
    with pytest.raises(ValueError,match='quantity_completion_source_changed'):_completion_json(path,128)


def test_completion_overlay_uses_actual_entry_time_for_refresh_window(tmp_path,monkeypatch):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity={'rec_date':'2026-09-01'})
    original['rec_date']='2026-09-01'
    rows=_overlay_for_test(tmp_path,[original])
    assert rows[0]['status']=='COMPLETED' and rows[0]['rec_date']=='2026-09-01'
    assert rows.completion_overlay_summary['overlaid_completed_count']==1


@pytest.mark.parametrize('identity,reason',[({'position_tag':'MANUAL'},'other_custody'),
                                          ({'strategy':'KOSPI_ML'},'other_strategy')])
def test_completion_overlay_preserves_full_native_census_but_excludes_other_owners(tmp_path,monkeypatch,identity,reason):
    _quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity=identity)
    rows=_overlay_for_test(tmp_path,[])
    assert rows==[]
    summary=rows.completion_overlay_summary
    assert summary['native_terminal_record_count']==1 and summary['applicable_terminal_record_count']==0
    assert summary['excluded_native_terminal_observation_counts']=={reason:1}
    assert set(rows.completion_generations)=={'2026-10-08'}
    trades,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows)
    assert trades==[] and census['fact_rows_read']==0 and census['excluded']=={}


@pytest.mark.parametrize('identity',[{'position_tag':'MANUAL'},{'strategy':'KOSPI_ML'}])
def test_completion_overlay_same_record_other_owner_remains_conflict(tmp_path,monkeypatch,identity):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity=identity)
    with pytest.raises(ValueError,match='quantity_completion_entry_binding_conflict'):_overlay_for_test(tmp_path,[original])


@pytest.mark.parametrize('actual',[False,True])
def test_completion_overlay_context_survives_shared_timeout_and_serialized_replay(tmp_path,monkeypatch,actual):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research,timeout_research_valid
    from src.engine.scalping.initial_quantity_refresh_evaluation import joint_evidence_valid
    from src.engine.scalping.initial_quantity_following_bars import build_following_bar_source,following_bar_source_valid
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,actual=actual)
    rows=_overlay_for_test(tmp_path,[original])
    for day in ('2026-10-07','2026-10-08'):_quality(tmp_path,day)
    shared={}
    replay=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=rows,
        entry_on_or_after='2026-10-07',path_cache=shared)
    serialized=json.loads(json.dumps(replay))
    assert serialized['census']['completion_overlay_generations']
    assert serialized['census']['completion_overlay_summary']['overlaid_completed_count']==1
    monkeypatch.setattr(policy,'_read_trade_facts',lambda *a,**k:pytest.fail('shared context must not requery database'))
    timeout=build_timeout_research('2026-10-08',data_dir=tmp_path,
        fact_rows=serialized['census']['input_fact_rows'],entry_on_or_after='2026-10-07',
        path_cache=shared,replay=serialized)
    independent=build_timeout_research('2026-10-08',data_dir=tmp_path,fact_rows=rows,
        entry_on_or_after='2026-10-07')
    assert timeout==independent
    assert timeout['census']==serialized['census']
    assert timeout_research_valid(timeout,replay=serialized) and joint_evidence_valid(timeout,replay=serialized)
    assert timeout['census']['actual_completed_net_pnl_krw']==(800 if actual else None)
    if not actual:assert timeout['census']['excluded']=={'terminal_cost_or_quantity_missing':1}
    following=build_following_bar_source(serialized,fetch=lambda *a:pytest.fail('no supported source needs provider call'))
    assert following_bar_source_valid(following,serialized)
    changed=copy.deepcopy(serialized)
    changed['census']['completion_overlay_summary']['overlaid_completed_count']=0
    changed['report_content_sha256']=policy._digest({k:v for k,v in changed.items() if k!='report_content_sha256'})
    assert not following_bar_source_valid(following,changed)


@pytest.mark.parametrize('mutation',['summary_count','native_count','status_counts','summary_only_omission','missing_context','missing_all_overlay_evidence',
    'original_status','row_price','row_cost','missing_row','extra_completion_row','economic_count','wrong_generation'])
def test_shared_overlay_context_independently_rejects_resealed_header_row_and_cohort(tmp_path,monkeypatch,mutation):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,actual=True)
    rows=_overlay_for_test(tmp_path,[original]);shared={}
    for day in ('2026-10-07','2026-10-08'):_quality(tmp_path,day)
    replay=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=rows,
        entry_on_or_after='2026-10-07',path_cache=shared)
    # Warm the same-process memo before forging a new, internally rehashed input.
    build_timeout_research('2026-10-08',data_dir=tmp_path,fact_rows=replay['census']['input_fact_rows'],
        entry_on_or_after='2026-10-07',path_cache=shared,replay=replay)
    changed=json.loads(json.dumps(replay));census=changed['census']
    if mutation=='summary_count':census['completion_overlay_summary']['overlaid_completed_count']=0
    elif mutation=='native_count':census['completion_overlay_summary']['native_terminal_record_count']=2
    elif mutation=='status_counts':census['completion_overlay_summary']['original_fact_status_counts']={'COMPLETED':1}
    elif mutation=='summary_only_omission':census['completion_overlay_summary']={}
    elif mutation=='missing_context':
        census['completion_overlay_generations']={};census['completion_overlay_summary']={}
    elif mutation=='missing_all_overlay_evidence':
        census['completion_overlay_generations']={};census['completion_overlay_summary']={}
        for key in ('completion_generation','completion_source_date','completion_observed_scale_in_fields',
                    'completion_scale_in_observations','original_fact_status'):
            census['input_fact_rows'][0].pop(key,None)
    elif mutation=='original_status':census['input_fact_rows'][0]['original_fact_status']='COMPLETED'
    elif mutation=='row_price':census['input_fact_rows'][0]['sell_price']=102000
    elif mutation=='row_cost':census['input_fact_rows'][0]['broker_actual_fees_taxes_krw']=0
    elif mutation=='missing_row':census['input_fact_rows']=[]
    elif mutation=='extra_completion_row':census['input_fact_rows'].append({**census['input_fact_rows'][0],'recommendation_id':2})
    elif mutation=='economic_count':census['all_completed_initial_trades']=2
    else:census['completion_overlay_generations']['2026-10-08']['fact_receipt']['sha256']='f'*64
    census['input_manifest_sha256']=policy._digest(census['input_fact_rows'])
    changed['report_content_sha256']=policy._digest({k:v for k,v in changed.items() if k!='report_content_sha256'})
    monkeypatch.setattr(policy,'_read_trade_facts',lambda *a,**k:pytest.fail('no database replay'))
    monkeypatch.setattr(policy,'_quantity_fact_generation_issue',lambda *a,**k:pytest.fail('no native large-source verifier'))
    with pytest.raises(ValueError,match='quantity_|timeout_research_'):
        build_timeout_research('2026-10-08',data_dir=tmp_path,fact_rows=census['input_fact_rows'],
            entry_on_or_after='2026-10-07',replay=changed)


def test_shared_overlay_context_memo_avoids_repeat_decode_and_rechecks_late_generation(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    rows=_overlay_for_test(tmp_path,[original])
    _,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows,entry_on_or_after='2026-10-07')
    serialized=json.loads(json.dumps(census));cache._VERIFIED_COMPLETION_CONTEXTS.clear()
    validate=lambda:policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,
        fact_rows=serialized['input_fact_rows'],entry_on_or_after='2026-10-07',source_census=serialized)
    validate()
    monkeypatch.setattr(cache,'_completion_json',lambda *a,**k:pytest.fail('memo must not decode again'))
    validate()
    from src.engine import strategy_position_performance_report as native
    path=tmp_path/'report/strategy_position_fact_sync/strategy_position_fact_sync_2026-10-08.status.json'
    original_signature=native._completion_source_signature;changed=False
    def signature(paths):
        nonlocal changed
        result=original_signature(paths)
        if not changed:
            changed=True;path.write_text(path.read_text()+' ')
        return result
    monkeypatch.setattr(native,'_completion_source_signature',signature)
    with pytest.raises(ValueError,match='quantity_completion_source_changed'):validate()


def test_shared_overlay_context_detects_source_change_during_independent_reconstruction(tmp_path,monkeypatch):
    from src.engine.scalping import initial_quantity_source_cache as cache
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    rows=_overlay_for_test(tmp_path,[original])
    _,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,fact_rows=rows,entry_on_or_after='2026-10-07')
    serialized=json.loads(json.dumps(census));cache._VERIFIED_COMPLETION_CONTEXTS.clear()
    original_overlay=cache.completion_overlay
    def overlay(*a,**kw):
        result=original_overlay(*a,**kw)
        path=tmp_path/'report/strategy_position_fact_sync/strategy_position_fact_sync_2026-10-08.status.json'
        path.write_text(path.read_text()+' ')
        return result
    monkeypatch.setattr(cache,'completion_overlay',overlay)
    with pytest.raises(ValueError,match='quantity_completion_source_changed'):
        policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,
            fact_rows=serialized['input_fact_rows'],entry_on_or_after='2026-10-07',source_census=serialized)


@pytest.mark.parametrize('first,last',[(1,2),(1,None),(None,None)])
def test_shared_overlay_context_rebuilds_observed_count_sequence_without_inventing_entry_zero(tmp_path,monkeypatch,first,last):
    original,_=_quantity_completion_overlay_fixture(tmp_path,monkeypatch,
        identity={} if first is None else {'add_count':first})
    _quantity_completion_overlay_fixture(tmp_path,monkeypatch,day='2026-10-09',
        identity={} if last is None else {'add_count':last})
    if first is None:original['add_count']=3
    rows=_overlay_for_test(tmp_path,[original],as_of='2026-10-09')
    _,census=policy.completed_trade_fact_census('2026-10-09',data_dir=tmp_path,
        fact_rows=rows,entry_on_or_after='2026-10-07')
    serialized=json.loads(json.dumps(census))
    _,rebuilt=policy.completed_trade_fact_census('2026-10-09',data_dir=tmp_path,
        fact_rows=serialized['input_fact_rows'],entry_on_or_after='2026-10-07',source_census=serialized)
    assert rebuilt==serialized and rebuilt['excluded']=={'scale_in_position':1}
    assert rebuilt['input_fact_rows'][0]['add_count']==(last if last is not None else first if first is not None else 3)
    if first is None:assert rebuilt['input_fact_rows'][0]['completion_scale_in_observations']=={}


def test_empty_shared_cohort_preserves_native_foreign_custody_and_rejects_whole_context_omission(tmp_path,monkeypatch):
    from src.engine.scalping.initial_quantity_timeout_research import build_timeout_research
    _quantity_completion_overlay_fixture(tmp_path,monkeypatch,identity={'position_tag':'MANUAL'})
    rows=_overlay_for_test(tmp_path,[]);shared={}
    replay=policy.build_initial_quantity_replay('2026-10-08',data_dir=tmp_path,fact_rows=rows,
        entry_on_or_after='2026-10-07',path_cache=shared)
    serialized=json.loads(json.dumps(replay))
    timeout=build_timeout_research('2026-10-08',data_dir=tmp_path,fact_rows=[],
        entry_on_or_after='2026-10-07',path_cache=shared,replay=serialized)
    assert timeout['census']==serialized['census']
    assert timeout['census']['input_fact_rows']==[]
    assert timeout['census']['completion_overlay_summary']['excluded_native_terminal_observation_counts']=={'other_custody':1}
    stripped=copy.deepcopy(serialized)
    stripped['census']['completion_overlay_generations']={};stripped['census']['completion_overlay_summary']={}
    stripped['report_content_sha256']=policy._digest({k:v for k,v in stripped.items() if k!='report_content_sha256'})
    with pytest.raises(ValueError,match='quantity_completion_generation_changed'):
        build_timeout_research('2026-10-08',data_dir=tmp_path,fact_rows=[],
            entry_on_or_after='2026-10-07',replay=stripped)


def test_serialized_completion_context_accepts_compression_without_full_snapshot_read(tmp_path,monkeypatch):
    from src.engine import compress_db_backfilled_files as archive
    from src.engine.lifecycle import snapshot_archive
    original,path=_quantity_completion_overlay_fixture(tmp_path,monkeypatch)
    rows=_overlay_for_test(tmp_path,[original])
    _,census=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,
        fact_rows=rows,entry_on_or_after='2026-10-07')
    serialized=json.loads(json.dumps(census))
    monkeypatch.setattr(archive,'MONITOR_SNAPSHOT_DIR',path.parent)
    for source in (path,path.with_suffix('.completed_projection.json'),path.with_suffix('.fact_projection.json')):
        assert archive._gzip_file(source,dry_run=False)[0]
    monkeypatch.setattr(snapshot_archive,'snapshot_identity',lambda *a:pytest.fail('no full archived snapshot verification'))
    _,rebuilt=policy.completed_trade_fact_census('2026-10-08',data_dir=tmp_path,
        fact_rows=serialized['input_fact_rows'],entry_on_or_after='2026-10-07',source_census=serialized)
    assert rebuilt==serialized


@pytest.mark.parametrize('fault',[None,'no_request','duplicate_request','different_plan','different_order',
    'late_decision','next_second','proxy_clock','exact_clock','quantity_conflict','sent_after_receipt','partial_position'])
def test_same_broker_second_policy_requires_exact_causal_request_sent_full_fill(fault):
    from copy import deepcopy
    from datetime import timedelta
    from src.engine.scalping.initial_quantity_refresh_evaluation import policy_decision_precedes_fill
    at=policy._timestamp('2026-10-16T12:31:28+09:00')
    fields=dict(entry_submit_attempt_id='attempt',entry_execution_sizing_plan_sha256='a'*64,
        position_sizing_policy_status='initial_policy_v2_loaded',position_sizing_policy_sha256='b'*64,
        initial_quantity_runtime_pid='123',quantity_type='KRX_THIN_HIGH_TICK',
        quantity_type_classifier_version=policy.CLASSIFIER_VERSION,reference_time=at.isoformat())
    decision=dict(at=at+timedelta(milliseconds=100),stage='entry_execution_sizing_plan',fields=fields)
    request=dict(at=at+timedelta(milliseconds=200),attempt_id='attempt',plan_sha='a'*64,tag='entry_probe')
    sent={**request,'at':at+timedelta(milliseconds=300),'order_no':'11'}
    fill=dict(at=at,emitted_at=at+timedelta(seconds=2),clock_precision_sec=1,
        clock_source='broker_execution_observed_at',qty=1,price=100000,order_no='11',execution_no='1')
    trade=dict(entry_at_fact_buy_time=at.isoformat(),buy_qty=1,profit_rate=1,realized_net_pnl_krw=1000)
    path=dict(decisions=[decision],order_requests=[request],order_sent=[sent],fills=[fill])
    if fault=='no_request':path['order_requests']=[]
    elif fault=='duplicate_request':path['order_requests'].append(deepcopy(request))
    elif fault=='different_plan':sent['plan_sha']='c'*64
    elif fault=='different_order':sent['order_no']='12'
    elif fault=='late_decision':decision['at']=request['at']+timedelta(milliseconds=1)
    elif fault=='next_second':decision['at']=at+timedelta(seconds=1)
    elif fault=='proxy_clock':fill['clock_source']='position_rebased_emitted_at_proxy'
    elif fault=='exact_clock':fill['clock_precision_sec']=0
    elif fault=='quantity_conflict':fill['qty']=2
    elif fault=='partial_position':
        trade['buy_qty']=2;trade['entry_at_fact_buy_time']=(at+timedelta(seconds=2)).isoformat()
    elif fault=='sent_after_receipt':sent['at']=fill['emitted_at']+timedelta(milliseconds=1)
    parent=policy._paired_candidate(trade,path,'parent')
    if fault and fault!='partial_position':
        assert parent['applied_policy_file_sha256'] is None
        assert 'policy_decision_clock_proof' not in parent
        return
    assert parent['applied_policy_file_sha256']=='b'*64
    assert parent['quantity_type']=='KRX_THIN_HIGH_TICK'
    row={**parent, 'entry_fill_at':at.isoformat(),'entry_fill_clock_source':fill['clock_source'],
        'entry_fill_clock_precision_sec':1,'entry_fill_order_no':'11','entry_fill_execution_no':'1',
        'shapes':{'parent':deepcopy(parent)},
        'cap_source':dict(attempt_id='attempt',plan_sha256='a'*64,
                         fills=[dict(at=at.isoformat(),qty=1)])}
    fact=dict(buy_time=trade['entry_at_fact_buy_time'],buy_qty=trade['buy_qty'])
    assert policy_decision_precedes_fill(row,fact)
    for field,value in [('proof_sha256','0'*64),('request_at',(at-timedelta(seconds=1)).isoformat()),
                        ('order_no','wrong'),('fill_qty',3)]:
        broken=deepcopy(row);broken['policy_decision_clock_proof'][field]=value
        if field!='proof_sha256':
            proof=broken['policy_decision_clock_proof'];proof['proof_sha256']=policy._digest({k:v for k,v in proof.items()if k!='proof_sha256'})
        broken['shapes']['parent']['policy_decision_clock_proof']=deepcopy(broken['policy_decision_clock_proof'])
        assert not policy_decision_precedes_fill(broken,fact)
