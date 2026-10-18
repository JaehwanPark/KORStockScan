"""Automatic source-only Main exit research input assembly.

Consumes verified master, original bootstrap/census and native AI traces. It
never reads the holding report it extends, rewrites journals, calls providers,
or allocates aggregate broker costs. Missing paths/costs remain census gaps.
"""
from collections import Counter
from datetime import date, datetime, timedelta
import gzip
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo
import time

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, capture_window, verify_window
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import digest, _atomic, number
from src.engine.scalping.universal_trailing_replay import (
    completed_sources, research_entry_window_start, apply_research_entry_window,
)
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster

SCHEMA = 'main_all_scope_exit_automatic_source_v1'


def input_inventory(root,days,master_path,parent_path,*,cost_data_root=None):
    if not days: raise ValueError('all_scope_assembly_date_window_empty')
    paths={Path(master_path),Path(parent_path)}
    for day in days:
        for namespace,stem in (('ai_decision_trace','ai_decision_trace'),('ai_decision_payloads','ai_decision_payloads'),('ai_decision_prompts','ai_decision_prompts'),
                               ('ai_decision_requests','ai_decision_requests'), ('pipeline_events','pipeline_events')):
            paths.update((Path(root)/namespace).glob(stem+'_'+day+'.jsonl*'))
        from src.engine.lifecycle.snapshot_archive import logical_path, identity_available
        for path in (Path(root)/'report/monitor_snapshots').glob('trade_review_'+day+'*.json*'):
            if (path.name.endswith(('.json', '.json.gz')) and not path.name.endswith('.archive_receipt.json')
                    and identity_available(path)):
                paths.add(logical_path(path))
    from src.engine.lifecycle.holding_research_cost import inventory as cost_inventory
    paths.update(cost_inventory(cost_data_root or root, days))
    paths.add(Path(root)/'runtime/order_owner_registry.jsonl')
    paths.update((Path(root)/'runtime/holding_path_votes').glob('*.jsonl*'))
    paths.update((Path(root)/'runtime/mechanistic_entry_policy/decisions'/days[-1]).glob('*/*.json'))
    from src.engine.lifecycle.snapshot_archive import present
    return [{'path':str(p.resolve()),'generation':byte_generation(p)} for p in sorted(paths)
            if p.is_file() or (p.parent.name=='monitor_snapshots' and present(p))]


def verify_inventory(manifest, assembly_root):
    """Detect new files as well as changes to previously consumed sources."""
    if 'assembly_inventory_ref' not in manifest:
        return  # Historical manually normalized manifests retain their contract.
    from .main_trailing_all_scope_research import code_contract
    if manifest.get('assembly_code_contract_sha256')!=code_contract():
        raise ValueError('all_scope_assembly_code_changed')
    root=Path(manifest['source_data_root']).resolve()
    _,master=universe(root,manifest['source_date'])
    current=input_inventory(root,manifest['consumed_dates'],master['path'],
        root/'runtime/policy_bootstrap'/f"runtime_policy_bootstrap_{manifest['source_date']}.json",
        cost_data_root=manifest.get('holding_research_cost_data_root'))
    from itertools import zip_longest
    if any(old!=new for old,new in zip_longest(
            storage.iter_tree(assembly_root,manifest['assembly_inventory_ref']),current)):
        raise ValueError('all_scope_assembly_inventory_changed')


def read(path):
    before = byte_generation(path)
    opener = gzip.open if path.suffix=='.gz' else open
    with Claim(4*1024*1024*8),opener(path,'rb') as handle:
        raw=handle.read(4*1024*1024+1)
        if len(raw)>4*1024*1024: raise ValueError('all_scope_source_partition_required')
        value=json.loads(raw)
    if byte_generation(path)!=before: raise ValueError('all_scope_source_changed')
    return value,before


def _bounded_calendar_source(path):
    """Read diagnostic bytes only after a bounded regular-file intake."""
    import io
    import os
    import stat
    from src.engine.lifecycle.holding_window_generation import source_stat
    limit=4*1024*1024
    path=Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('all_scope_calendar_source_path_invalid')
    before=path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_size>limit:
        raise ValueError('all_scope_calendar_source_unbounded_or_nonregular')
    with Claim(limit*10+1):
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
        try:
            opened=os.fstat(fd)
            if not stat.S_ISREG(opened.st_mode) or source_stat(opened)!=source_stat(before):
                raise ValueError('all_scope_calendar_source_changed')
            with os.fdopen(fd,'rb',closefd=False) as handle:
                physical=handle.read(limit+1)
            if (len(physical)!=before.st_size or source_stat(os.fstat(fd))!=source_stat(before)
                    or source_stat(path.lstat())!=source_stat(before)):
                raise ValueError('all_scope_calendar_source_changed')
        finally:
            os.close(fd)
        if path.suffix=='.gz':
            with gzip.GzipFile(fileobj=io.BytesIO(physical)) as handle:
                raw=handle.read(limit+1)
            # Reading through EOF validates every gzip member and its CRC.
            if len(raw)>limit:
                raise ValueError('all_scope_calendar_decoded_source_unbounded')
        else:
            raw=physical
        def unique_pairs(pairs):
            result={}
            for key,value in pairs:
                if key in result:
                    raise ValueError('all_scope_calendar_duplicate_key')
                result[key]=value
            return result
        value=json.loads(raw,object_pairs_hook=unique_pairs)
        if source_stat(path.lstat())!=source_stat(before):
            raise ValueError('all_scope_calendar_source_changed')
        return value,dict(path=path.name,size=len(physical),sha256=hashlib.sha256(physical).hexdigest())


def partial_publication_calendar_diagnostic(root, day):
    """Explain an original partial report without turning it into postclose."""
    from src.utils import market_day
    import zlib
    trading,reason=market_day.get_krx_trading_day_status(date.fromisoformat(day))
    if trading is not False:
        return None
    logical=Path(root)/'report/monitor_snapshots'/f'trade_review_{day}.json'
    physical=logical if logical.exists() or logical.is_symlink() else Path(str(logical)+'.gz')
    try:
        value,generation=_bounded_calendar_source(physical)
        meta=value.get('meta');metrics=value.get('metrics');sections=value.get('sections')
        if (value.get('date')!=day or value.get('code') or value.get('since')
                or value.get('scope')!='entered' or not isinstance(meta,dict)
                or meta.get('snapshot_profile')!='intraday_light'
                or not isinstance(metrics,dict) or not isinstance(sections,dict)):
            return None
        census=meta.get('completed_census_manifest') or {}
        metric_keys=('total_trades','completed_trades','canonical_completed_trades','entered_rows','open_trades',
                     'open_scalp_position_projection_count','full_fill_events','partial_fill_events','carry_completed_rows')
        census_keys=('raw_terminal_count','raw_completion_event_count','projected_count','valid_profit_count',
                     'strict_count','excluded_count','unobserved_count')
        row_keys=('recent_trades','completed_trade_projection','open_scalp_position_projection','completed_trades','open_trades')
        zero=(isinstance(census,dict) and not meta.get('warnings')
              and all(type(metrics.get(k)) is int and metrics[k]==0 for k in metric_keys)
              and all(type(census.get(k)) is int and census[k]==0 for k in census_keys)
              and meta.get('sell_completed_event_ids')==[] and census.get('raw_terminal_ids')==[]
              and all(type(meta.get(k)) is int and meta[k]==0 for k in (
                  'completion_event_id_count','completion_event_unresolved_id_count'))
              and all(sections.get(k)==[] for k in row_keys))
        holding_events=metrics.get('holding_events')
        return dict(date=day,publication_status='not_due',calendar_reason=reason,
            calendar_owner='src.utils.market_day:get_krx_trading_day_status',
            calendar_source=byte_generation(Path(market_day.__file__)),
            original_snapshot_profile=meta['snapshot_profile'],original_native_postclose_status='unverified_partial',
            source_path=str(physical),source_generation=generation,
            observed_counts={k:metrics.get(k) for k in metric_keys},
            original_census_counts={k:census.get(k) for k in census_keys} if isinstance(census,dict) else None,
            original_holding_event_count=holding_events,zero_trade_observations=zero,
            source_gap_preserved=True,native_postclose_valid_empty=False,
            original_metrics=metrics,original_source_receipts=meta.get('trailing_event_source_receipts'),
            original_receipt_role='original_cutoff_reference_no_later_source_merge',
            runtime_effect=False,allowed_runtime_apply=False)
    except (OSError,ValueError,TypeError,KeyError,AttributeError,EOFError,RecursionError,zlib.error):
        return None


def universe(root, day):
    directory=Path(root)/'report/micro_reversion_economic_reference'
    candidates=[p for p in directory.glob('micro_reversion_symbol_master_????-??-??.json*')
        if p.name.removesuffix('.gz').removesuffix('.json')[-10:]<=day and p.name.endswith(('.json','.json.gz'))]
    if not candidates: raise ValueError('all_scope_verified_universe_missing')
    latest=max(p.name.removesuffix('.gz').removesuffix('.json')[-10:] for p in candidates)
    aliases=[p for p in candidates if p.name.removesuffix('.gz').removesuffix('.json')[-10:]==latest]
    values=[(p,*read(p)) for p in aliases]
    if len({digest(value) for _,value,_ in values})!=1:
        raise ValueError('all_scope_universe_alias_conflict')
    path,payload,generation=values[0]
    master=VerifiedSymbolMaster.from_payload(payload,require_canonical_owner=True)
    rows=[]
    for code in sorted({r['symbol'] for r in payload['records']}):
        found=master.lookup(code,as_of=date.fromisoformat(day))
        record=found.record
        known=datetime.fromisoformat(record.verified_at).timestamp() if record else None
        # Listing metadata alone cannot prove a current trading halt is absent.
        rows.append({'code':code,'known_at':known,'tradable':None,
                     'master_lookup_status':found.status.value})
    return rows,{'path':str(path),'generation':generation,'semantic_sha256':digest(payload)}


def select_stream(root,namespace,day,sources):
    plain=Path(root)/namespace/f'{namespace}_{day}.jsonl'
    aliases=[p for p in (plain,Path(str(plain)+'.gz')) if p.exists()]
    if not aliases:return None
    hashes=[]
    for path in aliases:
        generation=byte_generation(path);sources[str(path)]=generation
        if path.suffix=='.gz':
            sha=hashlib.sha256()
            with gzip.open(path,'rb') as handle:
                for block in iter(lambda:handle.read(65536),b''):sha.update(block)
            hashes.append(sha.hexdigest())
        else:hashes.append(generation['sha256'])
        if byte_generation(path)!=generation:raise ValueError('all_scope_stream_changed')
    if len(set(hashes))!=1:raise ValueError('all_scope_plain_gzip_conflict')
    return aliases[0]


def _native_index(root,days,sources,gaps,db):
    from src.engine.scalping.ai_decision_trace import _json_bytes
    db.execute('CREATE TABLE native(id TEXT PRIMARY KEY,body TEXT,semantic TEXT,conflict INTEGER DEFAULT 0) WITHOUT ROWID')
    for day in days:
        path=select_stream(root,'ai_decision_payloads',day,sources)
        if path is None:continue
        generation=sources[str(path)]
        opener=gzip.open if path.suffix=='.gz' else open
        limit=2*1024*1024
        with opener(path,'rb') as handle,Claim(limit*8):
            while True:
                offset=handle.tell();raw=handle.readline(limit+1)
                if not raw:break
                if len(raw)>limit or not raw.endswith(b'\n'):
                    while raw and not raw.endswith(b'\n'):raw=handle.readline(storage.RECORD_BYTES)
                    gaps['native_payload_oversize_or_partial']+=1;continue
                try:
                    row=json.loads(raw)
                    if row.get('schema')!='mechanistic_entry_observation_v1':continue
                    identity=row['machine_observation_sha256']
                    if hashlib.sha256(_json_bytes({k:v for k,v in row.items() if k!='machine_observation_sha256'})).hexdigest()!=identity:
                        raise ValueError('native_observation_hash_invalid')
                    source=row['source'];assessment=source['assessment'];event=assessment.get('event') or {}
                    if assessment.get('action')!='ENTER_NOW':continue
                    if not (assessment.get('canonical_opportunity_id') and row['label_context'].get('evaluation_attempt_id')):continue
                    fields={k:event[k] for k in ('at','event_id','native_epoch','entry_ask','planned_qty','buy_basis_krw','entry_cost_model','item','source_item',
                        'execution_plan_sha256','entry_depth_verified','trailing_entry_context','universal_trailing_quote') if k in event}
                    minimal={'canonical_opportunity_id':assessment['canonical_opportunity_id'],
                        'machine_observation_sha256':identity,'evaluation_attempt_id':row['label_context']['evaluation_attempt_id'],
                        'symbol':row['label_context']['stock_code'],'bundle_sha256':row['bundle_sha256'],
                        'captured_at':row['captured_at'],'fields':fields,
                        'source_reference':{'path':str(path),'decoded_offset':offset,'sha256':hashlib.sha256(raw).hexdigest()}}
                    body=storage.encoded(minimal).decode()
                    if len(body.encode())>storage.RECORD_BYTES:raise ValueError('native_projection_partition_required')
                    semantic=digest({k:v for k,v in minimal.items() if k!='source_reference'})
                    db.execute('INSERT INTO native(id,body,semantic) VALUES (?,?,?) ON CONFLICT(id) DO UPDATE SET '
                        'conflict=CASE WHEN native.semantic!=excluded.semantic THEN 1 ELSE conflict END, '
                        'body=CASE WHEN native.semantic=excluded.semantic AND excluded.body<native.body '
                        'THEN excluded.body ELSE native.body END',(identity,body,semantic))
                except (ValueError,TypeError,KeyError,AttributeError):gaps['native_payload_binding_invalid']+=1
        if byte_generation(path)!=generation:raise ValueError('all_scope_native_payload_changed')


def _entry_plan_index(root, days, sources, gaps, db):
    """Index original producer receipts and quoted paths without materializing a day.

    Only the new receipt/ref fields are consumed. Historical unbound pipeline
    observations remain unbound; symbol or nearby timestamps are never joins.
    """
    from src.engine.scalping.trailing_entry_research_source import validate
    from src.engine.scalping.universal_trailing_replay import quote_source_digest, MAX_QUOTE_ENVELOPE_BYTES
    db.execute('CREATE TABLE trailing_plans(sha TEXT PRIMARY KEY, observation TEXT, attempt TEXT, known REAL, body TEXT) WITHOUT ROWID')
    db.execute('CREATE INDEX trailing_plan_identity ON trailing_plans(observation,attempt)')
    db.execute('CREATE TABLE trailing_quotes(plan TEXT, clock REAL, sequence INTEGER, sha TEXT, body TEXT, '
               'PRIMARY KEY(plan,clock,sequence,sha)) WITHOUT ROWID')
    db.execute('CREATE TABLE trailing_buy_accounts(record TEXT,ord TEXT,body TEXT,conflict INTEGER DEFAULT 0, '
               'PRIMARY KEY(record,ord)) WITHOUT ROWID')
    limit = 2*1024*1024
    for day in days:
        path = select_stream(root, 'pipeline_events', day, sources)
        if path is None: continue
        generation = sources[str(path)]
        opener = gzip.open if path.suffix == '.gz' else open
        with opener(path, 'rb') as handle, Claim(limit*8):
            while True:
                offset=handle.tell(); raw=handle.readline(limit+1)
                if not raw: break
                relevant = b'trailing_entry_plan_receipt' in raw or b'"order_leg_sent"' in raw
                if len(raw)>limit or not raw.endswith(b'\n'):
                    while raw and not raw.endswith(b'\n'): raw=handle.readline(storage.RECORD_BYTES)
                    gaps['trailing_plan_pipeline_envelope_unread']+=1
                    continue
                if not relevant: continue
                try:
                    event=json.loads(raw);fields=event.get('fields') or {}
                    reference=dict(path=str(path),decoded_offset=offset,sha256=hashlib.sha256(raw).hexdigest())
                    if event.get('stage')=='order_leg_sent':
                        record=str(event.get('record_id') or '')
                        account=str(fields.get('buy_account_key') or '').strip()
                        order=str(fields.get('order_no') or '').strip()
                        if (not record.isdigit() or not order or not account or account.lower() in {'default','none','-'}
                                or fields.get('buy_owner_type')!='main_scalping'
                                or fields.get('buy_owner_id')!='main_scalping:'+record
                                or fields.get('buy_registry_mode')!='registry_managed'
                                or not fields.get('owner_registry_intent_id')
                                or fields.get('pipeline_lifecycle_population_scope')!='real_record_bound'
                                or str(fields.get('actual_order_submitted')).lower()!='true'
                                or str(fields.get('broker_order_forbidden')).lower()!='false'):
                            continue
                        body=storage.encoded(dict(account_scope_sha256=digest(['broker_account',account]),
                            symbol=event.get('stock_code'),route=fields.get('broker_route'),
                            qty=int(fields['qty']),at=fields.get('entry_split_submitted_at'),
                            source_reference=reference)).decode()
                        previous=db.execute('SELECT body FROM trailing_buy_accounts WHERE record=? AND ord=?',(record,order)).fetchone()
                        # Duplicate aliases may differ in byte pointer only.
                        same=not previous or {k:v for k,v in json.loads(previous[0]).items() if k!='source_reference'}=={k:v for k,v in json.loads(body).items() if k!='source_reference'}
                        db.execute('INSERT INTO trailing_buy_accounts VALUES(?,?,?,?) ON CONFLICT(record,ord) '
                            'DO UPDATE SET conflict=MAX(conflict,excluded.conflict)',(record,order,body,int(not same)))
                    elif event.get('stage')=='entry_execution_sizing_plan':
                        receipt=validate(fields.get('trailing_entry_plan_receipt'))
                        if event.get('stock_code')!=receipt['symbol']:
                            raise ValueError('trailing_plan_event_symbol_mismatch')
                        value=dict(receipt=receipt,source_reference=reference)
                        db.execute('INSERT OR IGNORE INTO trailing_plans VALUES(?,?,?,?,?)',(
                            receipt['receipt_sha256'],receipt['machine_observation_sha256'],
                            receipt['evaluation_attempt_id'],receipt['known_at'],storage.encoded(value).decode()))
                    elif event.get('stage')=='scalp_trailing_input_transition':
                        plan=fields.get('trailing_entry_plan_receipt_sha256')
                        if not isinstance(plan,str) or len(plan)!=64: continue
                        quote=fields.get('universal_trailing_quote')
                        if isinstance(quote,str): quote=json.loads(quote)
                        if (not isinstance(quote,dict) or quote.get('kind')!='QUOTE'
                                or quote.get('source_sha256')!=quote_source_digest(quote)
                                or type(quote.get('sequence')) is not int
                                or type(quote.get('known_at')) not in (int,float)
                                or number(quote['known_at']) is None
                                or len(storage.encoded(quote))>MAX_QUOTE_ENVELOPE_BYTES):
                            raise ValueError('trailing_plan_forward_quote_invalid')
                        value=dict(quote=quote,symbol=event.get('stock_code'),source_reference=reference,
                            holding_link=fields.get('trailing_entry_plan_holding_link'))
                        db.execute('INSERT OR IGNORE INTO trailing_quotes VALUES(?,?,?,?,?)',(
                            plan,quote['known_at'],quote['sequence'],quote['source_sha256'],storage.encoded(value).decode()))
                except (ValueError,TypeError,KeyError,AttributeError):
                    gaps['trailing_plan_source_invalid']+=1
        if byte_generation(path)!=generation: raise ValueError('trailing_plan_pipeline_changed')


def _cf_original_holding(db, receipt, output):
    """Reuse the already verified completed row, not a second account scan."""
    key=receipt.get('position_key') or ''
    if not key.startswith('record:') or not key[7:].isdigit() or output is None:
        raise ValueError('cf_original_holding_source_missing')
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='records'").fetchone():
        raise ValueError('cf_original_holding_source_missing')
    found=db.execute('SELECT body FROM records WHERE id=? AND conflicted=0',(key[7:],)).fetchone()
    if found is None:raise ValueError('cf_original_holding_source_missing')
    row=json.loads(found[0]);original=row['position']
    if (original.get('evidence_kind')!='actual_completed' or original.get('position_key')!=key[7:]
            or original.get('symbol')!=receipt.get('symbol')
            or (original.get('source_reference') or {}).get('id')!=key[7:]
            or original.get('source_gap') or original.get('terminal_status')!='COMPLETED'):
        raise ValueError('cf_original_holding_source_invalid')
    reference=original.get('holding_vote_replay_ref') or {}
    if reference.get('status')!='source_bound' or reference.get('original_position_key')!=key:
        raise ValueError('cf_original_holding_ai_source_missing')
    diagnostic_ref=original.get('holding_path_diagnostic_ref') or {}
    if diagnostic_ref.get('count')!=1:raise ValueError('cf_original_holding_buy_source_missing')
    diagnostic=list(storage.iter_tree(output,diagnostic_ref))
    if len(diagnostic)!=1:raise ValueError('cf_original_holding_buy_source_missing')
    buys=storage.iter_tree(output,diagnostic[0]['buys_ref'])
    first=next(buys,None)
    if first is None or next(buys,None) is not None:
        raise ValueError('cf_original_holding_multi_buy_unmodeled')
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_legs
    identity=buy_fill_identity_from_legs([first])
    if identity is None:raise ValueError('cf_original_holding_buy_identity_missing')
    account=db.execute('SELECT body FROM trailing_buy_accounts WHERE record=? AND ord=? AND conflict=0',
        (key[7:],first['order_no'])).fetchone()
    if account is None:raise ValueError('cf_original_holding_account_unobserved')
    account=json.loads(account[0])
    from src.engine.scalping.trailing_entry_research_source import epoch
    # Both fields are the requested broker order route. The native completed
    # producer (sniper_trade_review_report) copies broker_route into leg.route;
    # neither field is the exchange execution venue nor the 0D data route.
    if (account['account_scope_sha256']!=receipt.get('account_scope_sha256')
            or account['symbol']!=receipt['symbol'] or account['qty']!=original.get('qty')
            or account['route']!=first.get('route') or epoch(account['at'])>original['entry_at']):
        raise ValueError('cf_original_holding_account_mismatch')
    interval=db.execute('SELECT first_sell FROM cf_original_intervals WHERE id=?',(key[7:],)).fetchone()
    if not interval or interval[0] is None:raise ValueError('cf_original_holding_interval_unobserved')
    return original,identity,interval[0],account['source_reference']


def _bound_entry_plan(db, position, projected, *, as_of, gaps, output=None):
    from src.engine.scalping.trailing_entry_research_source import model_entry, epoch
    native=db.execute('SELECT body FROM native WHERE id=? AND conflict=0',
        (position.get('machine_observation_sha256'),)).fetchone()
    native=json.loads(native[0]) if native else None
    if (not native or native['evaluation_attempt_id']!=position['native_evaluation_id']
            or native['symbol']!=position['symbol'] or native['bundle_sha256']!=projected['machine_hash']):
        gaps['trailing_plan_native_original_unverified']+=1
        position['entry_plan_source_status']='trailing_plan_native_original_unverified'
        return None
    try:
        native_signal=epoch(native['fields'].get('at'))
        if (not native_signal <= epoch(native['captured_at']) <= epoch(position['auxiliary_completed_at'])
                or native_signal != epoch(position['native_signal_at'])):
            raise ValueError('trailing_plan_native_anchor_clock_conflict')
    except (ValueError,TypeError,KeyError,OverflowError):
        gaps['trailing_plan_native_anchor_clock_conflict']+=1
        position['entry_plan_source_status']='trailing_plan_native_anchor_clock_conflict'
        return None
    # An original signal ask can anchor a price-only diagnostic even when an
    # execution plan is absent. It is never a modeled fill, quantity or basis.
    position.update(entry_reference_ask=native['fields'].get('entry_ask'),
                    entry_reference_role='native_entry_ask_price_path_only')
    matches=db.execute('SELECT body FROM trailing_plans WHERE observation=? AND attempt=? AND known<=? LIMIT 2',(
        position.get('machine_observation_sha256'),position['native_evaluation_id'],as_of or float('inf'))).fetchall()
    if len(matches)!=1:
        reason='trailing_plan_source_missing' if not matches else 'trailing_plan_multiple_attempt_plans'
        gaps[reason]+=1
        position['entry_plan_source_status']=reason
        return None
    value=json.loads(matches[0][0]);receipt=value['receipt']
    try:
        if epoch(native['captured_at'])>epoch(receipt['known_at']):
            raise ValueError('trailing_plan_precedes_native_capture')
        model=model_entry(receipt,symbol=position['symbol'],attempt=position['native_evaluation_id'],
            observation_sha=position.get('machine_observation_sha256'),bundle_sha=projected['machine_hash'],
            route=position['route'],signal_at=position['native_signal_at'],
            pass_at=position['auxiliary_completed_at'],as_of=as_of)
    except (ValueError,TypeError,KeyError) as exc:
        reason=str(exc); gaps[reason]+=1
        position.update(entry_plan_source_status=reason,entry_plan_source_reference=value['source_reference'])
        return None
    position.update(model,entry_plan_source_status='bound_visible_depth_model',
                    entry_plan_source_reference=value['source_reference'])
    original=None;buy_identity=None;first_sell=None;account_reference=None
    try:
        original,buy_identity,first_sell,account_reference=_cf_original_holding(db,receipt,output)
    except (ValueError,TypeError,KeyError,OSError) as exc:
        reason=str(exc);gaps[reason]+=1
        position.update(holding_ai_source_status=reason,source_gap=reason)
    plan=receipt['receipt_sha256']
    count=db.execute('SELECT COUNT(*) FROM trailing_quotes WHERE plan=? AND clock>=? AND clock<=?',
        (plan,model['entry_at'],as_of or float('inf'))).fetchone()[0]
    if not count:
        gaps['trailing_plan_bound_forward_path_unobserved']+=1
    position['forward_source_status']='bound_observations' if count else 'unobserved'
    def quotes():
        from src.engine.scalping.trailing_entry_research_source import validate_holding_link, equivalent_holding_link
        generation = None
        for (body,) in db.execute('SELECT body FROM trailing_quotes WHERE plan=? AND clock>=? AND clock<=? '
                'ORDER BY clock,sequence,sha',(plan,model['entry_at'],as_of or float('inf'))):
            row=json.loads(body)
            if row['symbol']!=position['symbol']:
                gaps['trailing_plan_forward_symbol_mismatch']+=1
                yield dict(kind='SOURCE_GAP', known_at=None)
            else:
                try:
                    link=validate_holding_link(row.get('holding_link'),receipt=receipt,quote=row['quote'])
                    current=(link['position_key'],link['buy_fill_identity'],link['first_buy_at'])
                    if generation is not None and current!=generation:
                        raise ValueError('trailing_plan_forward_generation_changed')
                    generation=current
                    if original is not None:
                        if row['quote']['known_at']>=first_sell:
                            raise ValueError('cf_original_holding_after_first_sale')
                        if not db.execute('SELECT 1 FROM cf_original_quotes WHERE id=? AND sha=?',
                                (original['position_key'],row['quote']['source_sha256'])).fetchone():
                            raise ValueError('cf_original_holding_quote_unbound')
                        vote_source=row['quote'].get('holding_vote_source')
                        equivalent_holding_link(link,receipt=receipt,position=position,original=original,source=vote_source)
                        if link['buy_fill_identity']!=buy_identity:
                            raise ValueError('cf_holding_buy_generation_mismatch')
                        if position.get('holding_vote_replay_ref') is None:
                            equivalence=dict(schema='cf_original_holding_equivalence_v1',
                                position_key=receipt['position_key'],buy_fill_identity=buy_identity,
                                entry_at=position['entry_at'],qty=position['qty'],buy_basis_krw=position['buy_basis_krw'],
                                sell_cost_rate=position['cost_model']['sell_cost_rate'],first_sell_at=first_sell)
                            equivalence['sha256']=digest(equivalence)
                            position.update(holding_vote_replay_ref={**original['holding_vote_replay_ref'],
                                    'candidate_position_equivalence':equivalence},
                                holding_ai_source_status='original_position_equivalent',
                                original_holding_position_key=receipt['position_key'],
                                original_holding_source_reference=original['source_reference'],
                                original_holding_account_reference=account_reference)
                    yield row['quote']
                except (ValueError,TypeError,KeyError,OverflowError) as exc:
                    gaps['trailing_plan_forward_holding_link_invalid']+=1
                    if str(exc).startswith('cf_'):
                        gaps[str(exc)]+=1
                        if position.get('holding_vote_replay_ref') is None:
                            position.update(holding_ai_source_status=str(exc),source_gap=str(exc))
                    yield dict(kind='SOURCE_GAP',known_at=None)
    return quotes()


def _trace_rows(root, days, sources, gaps, exclude=lambda *args:None,db=None,as_of=None,output=None):
    from src.engine.scalping.market_weakness_research import project_trace
    for day in days:
        path=select_stream(root,'ai_decision_trace',day,sources)
        if path is None:
            gaps['native_trace_missing']+=1;continue
        generation=sources[str(path)]
        opener=gzip.open if path.suffix=='.gz' else open
        # Legacy trace envelopes may include replay context above the compact
        # row limit. Decode one bounded complete envelope and retain primitives
        # only; larger records are drained and explicitly quarantined.
        envelope_limit=2*1024*1024
        with opener(path,'rb') as handle,Claim(envelope_limit*8):
            while True:
                start=handle.tell();raw=handle.readline(envelope_limit+1)
                if not raw: break
                reference={'path':str(path),'decoded_offset':start,'encoding':'gzip' if path.suffix=='.gz' else 'plain'}
                if len(raw)>envelope_limit or not raw.endswith(b'\n'):
                    while raw and not raw.endswith(b'\n'): raw=handle.readline(storage.RECORD_BYTES)
                    gaps['native_trace_oversize_or_partial']+=1
                    exclude('native_trace_oversize_or_partial',reference);continue
                if len(raw)>storage.RECORD_BYTES: gaps['native_large_envelope_projected']+=1
                try:
                    original=json.loads(raw)
                    projected,reason=project_trace(original,day)
                except (ValueError,TypeError,KeyError):
                    projected,reason=None,'native_trace_invalid'
                if not projected:
                    gaps[reason]+=1
                    if reason!='not_entry_trace': exclude(reason,reference)
                    continue
                if projected['machine_action']!='ENTER_NOW' or projected['auxiliary_verdict']!='PASS':
                    gaps['native_not_enter_pass']+=1;continue
                if projected['identity_grade']!='canonical':
                    found=db.execute('SELECT body FROM native WHERE id=? AND conflict=0',
                        (original.get('machine_observation_sha256'),)).fetchone() if db is not None else None
                    bound=json.loads(found[0]) if found else None
                    if (not bound or bound['evaluation_attempt_id']!=projected['evaluation_attempt_id']
                        or bound['symbol']!=projected['symbol'] or bound['bundle_sha256']!=projected['machine_hash']
                        or datetime.fromisoformat(bound['captured_at'])>datetime.fromisoformat(projected['decision_ts'])):
                        gaps['native_canonical_identity_missing']+=1
                        exclude('native_canonical_identity_missing',{**reference,'evaluation_attempt_id':projected['evaluation_attempt_id'],
                            'decision_trace_id':projected['decision_trace_id']});continue
                    projected['opportunity_id']=bound['canonical_opportunity_id']
                    original['entry_mechanistic_policy_decision']={'event':bound['fields'],
                        'observation_sha256':bound['machine_observation_sha256']}
                    gaps['native_canonical_identity_recovered']+=1
                assessment=original.get('entry_mechanistic_policy_decision') or {}
                event=assessment.get('event') or {}
                clock=datetime.fromisoformat(projected['decision_ts']).timestamp()
                if as_of is not None and clock>as_of:
                    gaps['native_decision_after_cutoff']+=1
                    exclude('native_decision_after_cutoff',reference);continue
                native_at=event.get('at')
                try:
                    native_clock=datetime.fromisoformat(native_at)
                    if native_clock.tzinfo is None or native_clock.timestamp()>clock: raise ValueError('native_clock_invalid')
                    native_clock=native_clock.timestamp()
                except (ValueError,TypeError):
                    native_clock=None;gaps['native_signal_clock_missing']+=1
                source_quote=event.get('universal_trailing_quote')
                path_events=[source_quote] if isinstance(source_quote,dict) else []
                position=dict(position_key='cf:'+projected['opportunity_id'],evidence_kind='enter_pass_opportunity_cf',
                    owner='main',automatic_management_allowed=True,symbol=projected['symbol'],entry_at=clock,
                    qty=event.get('planned_qty'),buy_basis_krw=event.get('buy_basis_krw'),cost_model=event.get('entry_cost_model') or {},
                    route=projected['route'],item=event.get('item') or event.get('source_item'),entry_action='ENTER_NOW',auxiliary_effective_verdict='PASS',
                    machine_observation_sha256=assessment.get('observation_sha256') or original.get('machine_observation_sha256'),native_evaluation_id=projected['evaluation_attempt_id'],
                    native_signal_at=native_clock,auxiliary_completed_at=clock,
                    entry_reference_ask=None,entry_reference_role='native_entry_ask_price_path_only',
                    execution_plan_sha256=None,entry_depth_verified=False,
                    entry_context=event.get('trailing_entry_context'),operating_ai_required=True,
                    source_reference={'path':str(path),'decoded_offset':start,'size':handle.tell()-start,
                        'encoding':'gzip' if path.suffix=='.gz' else 'plain','sha256':hashlib.sha256(raw).hexdigest()})
                if not path_events: gaps['native_forward_path_unobserved']+=1
                if db is not None:
                    bound_path=_bound_entry_plan(db,position,projected,as_of=as_of,gaps=gaps,output=output)
                    if bound_path is not None: path_events=bound_path
                yield position,path_events
        if byte_generation(path)!=generation: raise ValueError('all_scope_native_trace_changed')


def _operating(root, day, sources, gaps):
    """Exact-date native decision receipts prove operation, not full coverage."""
    operating=set()
    base=Path(root)/'runtime/mechanistic_entry_policy/decisions'/day
    for path in sorted(base.glob('*/*.json')):
        try:
            value,generation=read(path)
            if (value.get('schema')!='main_policy_decision_status_v1' or value.get('target_date')!=day
                or value.get('policy_validation_state')!='valid'
                or value.get('artifact_content_sha256')!=digest({k:v for k,v in value.items()
                    if k!='artifact_content_sha256'})):
                raise ValueError('native_receipt_invalid')
            parts=value['scope'].split('|')
            if len(parts)!=4: raise ValueError('native_scope_invalid')
            symbol,market,_,route=parts
            if market=='AFTER': market='INTEGRATED_AFTERMARKET'
            if market=='PRE': market='PREMARKET'
            operating.add('|'.join((symbol,market,route)))
            sources[str(path)]=generation
        except (ValueError,TypeError,KeyError,AttributeError):
            gaps['native_operating_receipt_invalid']+=1
    return sorted(operating)


def large_completed_sources(root,raw,day,output,dependency,*,sources=None):
    """Stream a legacy projection sealed by its original census producer."""
    from src.engine.lifecycle.research_json_stream import completed_rows
    from src.engine.scalping.pre_submit_delay_initial_policy import number
    from src.engine.lifecycle.snapshot_archive import present
    sidecar=raw.with_suffix('.completed_projection.json')
    if not present(sidecar):sidecar=raw
    receipt_path=Path(str(sidecar)+'.dependencies.json')
    generation=byte_generation(sidecar)
    retained = not receipt_path.is_file()
    if retained:
        from src.engine.lifecycle.holding_window_generation import verified_legacy_projection_dependency
        receipt,bound_generation=verified_legacy_projection_dependency(root,day,projection_generation=generation)
        if receipt['observed_actual_cost_source_generation']!=dependency['cost_generation']:
            raise ValueError('all_scope_large_completed_cost_generation_changed')
        receipt_generation=None
        if sources is not None:
            validation=bound_generation['legacy_validation']
            proof=Path(root)/'report/strategy_position_fact_sync/legacy_sources'/day/validation['proof']['path']
            status=Path(root)/'report/strategy_position_fact_sync'/validation['status']['path']
            sources[str(proof)]=validation['proof'];sources[str(status)]=validation['status']
            original_manifest=receipt.get('original_snapshot_manifest')
            if original_manifest is not None:
                manifest_path=Path(original_manifest['path'])
                sources[str(manifest_path)]={**original_manifest,'path':manifest_path.name}
    else:
        receipt,receipt_generation=read(receipt_path)
    if (not retained and (receipt.get('schema')!='holding_projection_dependency_receipt_v1'
        or receipt.get('date')!=day or receipt.get('projection')!=generation
        or receipt.get('artifact_sha256')!=digest({k:v for k,v in receipt.items() if k!='artifact_sha256'})
        or not receipt.get('census_sha256') or receipt.get('meta',{}).get('snapshot_profile')!='postclose_exit'
        or receipt.get('meta',{}).get('actual_cost_source_generation')!=dependency['cost_generation'])):
        raise ValueError('all_scope_large_completed_receipt_invalid')
    from src.engine.lifecycle.snapshot_archive import snapshot_identity
    identity=snapshot_identity(raw)
    if raw.is_symlink() or receipt.get('snapshot_identity')!=identity:
        raise ValueError('all_scope_large_completed_snapshot_changed')
    count=0
    for trade,quote_ref in completed_rows(sidecar,output):
        count+=1
        quotes=lambda:storage.iter_tree(output,quote_ref)
        first=next(quotes(),{})
        for key,quote_key in (('entry_quote_route','route'),('entry_quote_item','item'),('trailing_replay_cost_model','entry_cost_model')):
            if not trade.get(key):trade[key]=first.get(quote_key)
        buy_ref=trade.get('buy_fill_legs_ref');sell_ref=trade.get('sell_fill_legs_ref')
        buys=lambda:storage.iter_tree(output,buy_ref) if buy_ref else iter(())
        first_leg=next(buys(),None);trade['buy_fill_legs']=[first_leg] if first_leg is not None else []
        invalid_sell=False
        if sell_ref:
            latest=None;latest_at=None
            for leg in storage.iter_tree(output,sell_ref):
                try:
                    value=datetime.fromisoformat(leg['at']);clock=(value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
                    if latest_at is None or clock>latest_at:latest,latest_at=leg,clock
                except (ValueError,TypeError,KeyError,AttributeError):invalid_sell=True
            trade['sell_fill_legs']=[latest] if latest is not None and not invalid_sell else []
        def adds(trade=trade,buys=buys):
            iterator=buys();next(iterator,None);model=trade.get('trailing_replay_cost_model') or {}
            for leg in iterator:
                try:
                    value=datetime.fromisoformat(leg['at']);clock=(value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
                    cost=leg.get('buy_cost_krw')
                    if (cost is None and model.get('allocation')=='frozen_configured_round_trip_rate_on_sell_model_only'
                        and number(model.get('buy_cost_krw'))==0):cost=0
                    yield dict(kind='ADD',event_at=clock,known_at=clock,qty=leg['qty'],buy_amount_krw=leg['amount_krw'],
                        buy_cost_krw=cost,buy_generation_sha256=digest(leg))
                except (ValueError,TypeError,KeyError,AttributeError):
                    yield dict(kind='ADD',known_at=None)
        # The resident producer sorts quotes plus every ADD when fills exist.
        # Sort on disk as well: timeline append order is not event-time proof.
        invalid_buy=False
        if buy_ref:
            for leg in buys():
                try:
                    datetime.fromisoformat(leg['at']);leg['qty'];leg['amount_krw']
                except (ValueError,TypeError,KeyError,AttributeError,OverflowError):invalid_buy=True
        if first_leg is not None:
            with storage.index(output/'scratch') as ordering:
                ordering.execute('CREATE TABLE events(clock REAL,ordinal INTEGER,body TEXT)')
                for ordinal,event in enumerate(__import__('itertools').chain(quotes(),adds())):
                    clock=number(event.get('known_at'))
                    if clock is None:invalid_buy=True
                    ordering.execute('INSERT INTO events VALUES (?,?,?)',
                        (clock,ordinal,storage.encoded(event).decode()))
                event_ref=storage.write_tree(output,(json.loads(body) for body, in
                    ordering.execute('SELECT body FROM events ORDER BY clock,ordinal')))
        else:event_ref=quote_ref
        positions,_=completed_sources([trade])
        for position in positions:
            if invalid_buy or trade.get('projection_source_gap'):position['entry_at']=None
            position['symbol']=str(trade.get('stock_code') or trade.get('code') or '')
            position['source_reference']={'path':str(sidecar),'id':position['position_key'],'projection_generation':generation}
            yield trade,position,storage.iter_tree(output,event_ref)
    if count!=receipt.get('completed_count'):raise ValueError('all_scope_large_completed_census_changed')
    if byte_generation(sidecar)!=generation:
        raise ValueError('all_scope_large_completed_source_changed')
    if retained:
        current,current_generation=verified_legacy_projection_dependency(root,day,projection_generation=generation)
        if current!=receipt or current_generation!=bound_generation:
            raise ValueError('all_scope_large_completed_source_changed')
    elif byte_generation(receipt_path)!=receipt_generation:
        raise ValueError('all_scope_large_completed_source_changed')


def assemble(root, output, *, source_date, target_date, start_date='2026-09-29', as_of=None, immutable=False, cost_data_root=None):
    from src.engine.lifecycle.research_disk_budget import use
    from src.engine.lifecycle.holding_research_cost import Source
    with use(output),storage.compact_trees(),Source(root,cost_data_root=cost_data_root,knowledge_cutoff=as_of) as costs:
        return _assemble(root,output,source_date=source_date,target_date=target_date,
            start_date=start_date,as_of=as_of,immutable=immutable,costs=costs)


def _assemble(root, output, *, source_date, target_date, start_date='2026-09-29', as_of=None, immutable=False, costs):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output==root or output.is_relative_to(root):
        raise ValueError('all_scope_isolated_assembly_required')
    output.mkdir(parents=True,exist_ok=True)
    days=[];cursor=date.fromisoformat(max(start_date,'2026-09-29'))
    while cursor<=date.fromisoformat(source_date): days.append(cursor.isoformat());cursor+=timedelta(days=1)
    if not days: raise ValueError('all_scope_assembly_date_window_empty')
    entry_window_start=research_entry_window_start(days)
    rows,master_source=universe(root,source_date)
    window=capture_window(root,days)
    parent_path=root/'runtime/policy_bootstrap'/f'runtime_policy_bootstrap_{source_date}.json'
    parent,parent_generation=read(parent_path)
    from .main_trailing_all_scope_research import code_contract
    code=code_contract();inventory=input_inventory(root,days,master_source['path'],parent_path,cost_data_root=costs.cost_root)
    signature=digest([source_date,target_date,days,as_of,code,window['input_window_generation_sha256'],inventory,str(costs.cost_root)])
    if immutable:
        output=output/'generations'/signature
        output.mkdir(parents=True,exist_ok=True)
    existing=output/'manifest.json'
    if existing.exists():
        try:
            previous,_=read(existing)
            if (previous.get('artifact_sha256')==digest({k:v for k,v in previous.items() if k!='artifact_sha256'})
                and previous.get('assembly_input_generation_sha256')==signature):
                for part in storage.iter_tree(output,previous['partitions_ref']):
                    value,_=read(output/part['path'])
                    if digest(value)!=part['artifact_sha256']:raise ValueError('assembly_partition_changed')
                    for ref in value['paths'].values():
                        for _ in storage.iter_tree(output,ref):pass
                for _ in storage.iter_tree(output,previous['population_ids_ref']):pass
                return existing
        except (ValueError,TypeError,KeyError,OSError):pass
    from src.engine.automation.runtime_policy_bootstrap import _digest_json
    if parent.get('manifest_sha256')!=_digest_json({k:v for k,v in parent.items() if k!='manifest_sha256'}):
        raise ValueError('all_scope_parent_manifest_invalid')
    parent_copy=output/'parent.json';_atomic(parent_copy,parent)
    sources={str(parent_path):parent_generation,master_source['path']:master_source['generation']}
    gaps=Counter();publication_diagnostics=[];as_of=time.time() if as_of is None else number(as_of)
    if as_of is None or as_of<datetime.fromisoformat(source_date+'T00:00:00+09:00').timestamp():
        raise ValueError('all_scope_assembly_cutoff_invalid')
    costs.cutoff=as_of
    costs.sources=sources
    operating=_operating(root,source_date,sources,gaps)
    from src.engine.holding_exit_observation_report import _verified_trade_review_projection
    def records():
        from src.engine.lifecycle.snapshot_archive import present, identity_available
        for day in days:
            dependency=window['dependencies'][day]
            calendar=partial_publication_calendar_diagnostic(root,day)
            if calendar is not None:
                calendar['original_window_status']=dependency['status']
                publication_diagnostics.append(calendar)
                sources[calendar['source_path']]=calendar['source_generation']
            if dependency['status']=='source_gap': gaps['completed_snapshot_source_gap']+=1;continue
            raw=root/'report/monitor_snapshots'/f'trade_review_{day}.json'
            if not present(raw):
                if date.fromisoformat(day).weekday()<5: gaps['completed_snapshot_missing']+=1
                continue
            sidecar=raw.with_suffix('.completed_projection.json')
            projection=sidecar if present(sidecar) else raw
            empty_archive=(dependency.get('projection') or {}).get('source_basis')=='current_native_gzip_empty_postclose'
            if not empty_archive and not identity_available(projection):
                gaps['completed_snapshot_unverified']+=1;continue
            if not empty_archive and identity_available(raw) and byte_generation(projection)['size']>4*1024*1024:
                sources[str(projection)]=byte_generation(projection)
                receipt=Path(str(projection)+'.dependencies.json')
                if receipt.is_file():sources[str(receipt)]=byte_generation(receipt)
                cohort=large_completed_sources(root,raw,day,output,dependency,sources=sources)
            else:
                original_sources={}
                projection=_verified_trade_review_projection(raw,day,data_root=root,source_generations=original_sources)
                if projection is None: gaps['completed_snapshot_unverified']+=1;continue
                if original_sources:sources.update(original_sources)
                else:sources[str(sidecar)]=byte_generation(sidecar)
                def resident(projection=projection,sidecar=sidecar):
                    for trade in projection['sections']['completed_trade_projection']:
                        positions,paths=completed_sources([trade])
                        for position in positions:
                            position['symbol']=str(trade.get('stock_code') or trade.get('code') or '')
                            position['source_reference']={'path':str(sidecar),'id':position['position_key']}
                            yield trade,position,paths[position['position_key']]
                cohort=resident()
            for trade,position,events in cohort:
                if str(trade.get('strategy') or '').upper() not in {'SCALP','SCALPING'}:
                    gaps['non_main_trade']+=1;continue
                position['holding_research_cost']=costs.record(trade,completion_date=day,assembly_root=output)
                from src.engine.ai.holding_vote_replay_source import assemble_votes
                from src.engine.scalping.holding_path_vote_replay import freeze_replay_trade
                position['holding_path_diagnostic_ref']=storage.write_tree(output,
                    [freeze_replay_trade(trade,root,output,sources)])
                def original_events():
                    for event in events:
                        if event.get('kind')=='QUOTE' and event.get('source_sha256'):
                            db.execute('INSERT OR IGNORE INTO cf_original_quotes VALUES (?,?)',
                                (position['position_key'],event['source_sha256']))
                        yield event
                event_ref=storage.write_tree(output,original_events())
                first = next(storage.iter_tree(output,event_ref), {})
                source = position.get('holding_vote_source') or first.get('holding_vote_source')
                if source is not None:
                    position['operating_ai_required'] = source.get('required')
                    position['holding_vote_replay_ref'] = assemble_votes(root,output,source,sources)
                first_sell=None
                sells=(storage.iter_tree(output,trade['sell_fill_legs_ref']) if trade.get('sell_fill_legs_ref')
                       else iter(trade.get('sell_fill_legs') or []))
                try:
                    for leg in sells:
                        stamp=datetime.fromisoformat(leg['at'])
                        stamp=(stamp.replace(tzinfo=ZoneInfo('Asia/Seoul')) if stamp.tzinfo is None else stamp).timestamp()
                        if first_sell is None or stamp<first_sell:first_sell=stamp
                except (ValueError,TypeError,KeyError,OverflowError):first_sell=None
                db.execute('INSERT INTO cf_original_intervals VALUES (?,?) ON CONFLICT(id) DO UPDATE SET '
                    'first_sell=CASE WHEN cf_original_intervals.first_sell=excluded.first_sell '
                    'THEN excluded.first_sell ELSE NULL END',(position['position_key'],first_sell))
                yield position,event_ref
                alternative={**position,'position_key':'alternative:'+position['position_key'],
                    'evidence_kind':'actual_entry_alternative_exit','actual_cost_reconciliation':None,'situation_pin':None}
                yield alternative,event_ref
        yield from _trace_rows(root,days,sources,gaps,exclude,db,as_of=as_of,output=output)
    with storage.index(output/'scratch') as db:
        db.execute('CREATE TABLE exclusions(id TEXT PRIMARY KEY,body TEXT) WITHOUT ROWID')
        db.execute('CREATE TABLE cf_original_intervals(id TEXT PRIMARY KEY,first_sell REAL) WITHOUT ROWID')
        db.execute('CREATE TABLE cf_original_quotes(id TEXT,sha TEXT,PRIMARY KEY(id,sha)) WITHOUT ROWID')
        def exclude(reason,reference):
            value={'reason':reason,'source_reference':reference}
            db.execute('INSERT OR IGNORE INTO exclusions VALUES (?,?)',(digest(value),storage.encoded(value).decode()))
        _native_index(root,days,sources,gaps,db)
        _entry_plan_index(root,days,sources,gaps,db)
        # Dedup whole populations before any replay/selection, not partition by
        # partition. Position and CF identities stay in disjoint namespaces.
        for position,events in records():
            event_ref=events if isinstance(events,dict) and events.get('schema')==storage.SCHEMA else storage.write_tree(output,iter(events))
            position=apply_research_entry_window(position,window_start_at=entry_window_start)
            if position.get('research_entry_window_exclusion'):
                gaps[position['research_entry_window_exclusion']]+=1
            value={'position':position,'events_ref':event_ref}
            semantic={'position':{k:v for k,v in position.items() if k!='source_reference'},'events_ref':event_ref}
            storage.put(db,position['position_key'],value,content_sha=digest(storage.logical_value(semantic)))
        def parts():
            # A bounded batch amortizes metadata fsync/hash without sharing
            # position state. Record limits cap this batch below 1 MiB.
            batch=[]
            def emit(batch):
                payload={'source_date':source_date,'positions':[v['position'] for _,v in batch],
                    'paths':{i:v['events_ref'] for i,v in batch},'cost_generations':{
                        day:window['dependencies'][day]['cost_generation'] for day in days}}
                payload['artifact_sha256']=digest(payload)
                name='inputs/'+digest(payload)+'.json';_atomic(output/name,payload)
                return {'path':name,'artifact_sha256':digest(payload),'consumed_dates':days}
            with Claim(16*storage.RECORD_BYTES*8):
                for identity,value,_ in storage.records(db):
                    batch.append((identity,value))
                    if len(batch)==16:
                        yield emit(batch);batch=[]
                if batch:yield emit(batch)
        partition_ref=storage.write_tree(output,parts())
        population_ref=storage.write_tree(output,(i for i,_,_ in storage.records(db)))
        quarantined_ref=storage.write_tree(output,({'identity':i,'copies':n,'reason':'canonical_source_conflict'}
                                                  for i,_,n in storage.records(db,conflicts=True)))
        excluded_ref=storage.write_tree(output,(json.loads(b) for b, in db.execute('SELECT body FROM exclusions ORDER BY id')))
    for name,generation in sources.items():
        if byte_generation(Path(name))!=generation: raise ValueError('all_scope_assembly_source_changed')
    verify_window(root,window)
    source_ref=storage.write_tree(output,({'path':name,'generation':generation} for name,generation in sorted(sources.items())))
    if input_inventory(root,days,master_source['path'],parent_path,cost_data_root=costs.cost_root)!=inventory:
        raise ValueError('all_scope_assembly_inventory_changed')
    inventory_ref=storage.write_tree(output,inventory)
    from src.engine.scalping.trailing_situation_policy import registered_research_grid
    receipt=parent['scalp_trailing_mechanical_policy_receipt']
    candidates,grid=registered_research_grid(receipt['market_values'],receipt['classifier_parameters'])
    manifest=dict(schema='main_all_scope_exit_input_manifest_v2',source_date=source_date,target_date=target_date,
        as_of=as_of,universe=rows,universe_source_sha256=master_source['semantic_sha256'],
        approved_parent_receipt=parent['scalp_trailing_mechanical_policy_receipt'],
        approved_parent_source={'path':'parent.json','sha256':byte_generation(parent_copy)['sha256']},
        consumed_dates=days,partitions_ref=partition_ref,population_ids_ref=population_ref,
        source_data_root=str(root),holding_research_cost_data_root=str(costs.cost_root),source_generations_ref=source_ref,
        assembly_code_contract_sha256=code,assembly_input_generation_sha256=signature,
        assembly_inventory_ref=inventory_ref,input_window_generation_sha256=window['input_window_generation_sha256'],
        assembly_census={'source_gaps':dict(gaps),'quarantined':quarantined_ref,'excluded_native_sources_ref':excluded_ref,
            'publication_due_diagnostics':publication_diagnostics},
        candidates=candidates,situation_classifier_grid=grid,
        operating=operating,coverage={},runtime_effect=False,allowed_runtime_apply=False)
    manifest['artifact_sha256']=digest(manifest)
    path=output/'manifest.json';_atomic(path,manifest)
    return path
