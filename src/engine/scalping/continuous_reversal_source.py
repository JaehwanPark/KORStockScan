"""Freeze normalized continuous trade sources. Never read machine decisions.

Owned postclose raw envelope consumer; no broker protocol parsing or requests.
"""
import gzip
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from src.trading.market.session_contract import market_source_partition_venue
from src.engine.scalping.micro_reversion.contracts import registration_item_market_data_identity


KST=ZoneInfo('Asia/Seoul')


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def dump(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2))


def num(v):
    return float(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) else None


def discover(data_root, day):
    base = Path(data_root)/"observations/scalp_micro_reversion_forward"
    result=[]
    for folder in sorted(base.glob(f'trade_date={day}/venue=*/session=*')):
        files=[p for p in folder.glob('market_stream*.jsonl*') if 'event_references' not in p.name
               and p.name.endswith(('.jsonl','.jsonl.gz'))]
        # A .gz is an archive of the same logical shard, not a second series.
        logical={}
        for p in sorted(files):
            name=p.name.removesuffix('.gz')
            other=logical.get(name)
            if other is not None:
                def content_hash(candidate):
                    opener=gzip.open if candidate.suffix=='.gz' else open
                    with opener(candidate,'rb') as handle:return hashlib.file_digest(handle,'sha256').hexdigest()
                if content_hash(other)!=content_hash(p):
                    raise ValueError('compressed_source_alias_conflict:'+str(p))
            if name not in logical or p.suffix!='.gz':logical[name]=p
        if not logical:continue
        day=folder.parts[-3].split('=')[1]
        venue=folder.parts[-2].split('=')[1]
        session=folder.parts[-1].split('=')[1]
        result.append(dict(day=day,venue=venue,session=session,
            files=[dict(path=str(p),bytes=p.stat().st_size) for p in sorted(logical.values())]))
    return result


def _source_quality_receipt(data_root, day):
    from src.engine.scalping.micro_reversion.observer_source_quality import main_raw_epoch_validation
    paths = [Path(data_root)/"runtime/scalp_micro_reversion_forward_collector/latest.json",
             Path(data_root)/"source_quality/scalp_micro_reversion_canary_daily"/f"scalp_micro_reversion_canary_snapshot_{day}.json"]
    paths += sorted((paths[0].parent/'closed').glob(day+'-*.json'))
    records=[];allowed=set();denied=set()
    for path in paths:
        if not path.is_file():continue
        content=path.read_bytes()
        try:value=json.loads(content)
        except ValueError:continue
        if not isinstance(value,dict):continue
        if not str(value.get("generated_at", "")).startswith(day):continue
        record=dict(path=str(path.resolve()),sha256=hashlib.sha256(content).hexdigest(),
                    **main_raw_epoch_validation(value,source_date=day))
        records.append(record)
        if record['eligible']:allowed.update(record['allowed_sequence_epochs'])
        elif isinstance(value.get('collector_snapshot'),dict) and value['collector_snapshot'].get('collector_lifecycle')=='closed':
            c=value['collector_snapshot'];epochs=c.get('reconciled_sequence_epochs')
            if not isinstance(epochs,(list,tuple)):epochs=[]
            denied.update(e for e in [*epochs,c.get('sequence_epoch')] if type(e) is int and e>0)
    allowed-=denied
    return dict(path=None,sha256=None,eligible=bool(allowed),
                status='closed_main_raw_epochs' if allowed else 'main_raw_epoch_receipt_missing_or_invalid',
                allowed_sequence_epoch=max(allowed) if allowed else None,allowed_sequence_epochs=sorted(allowed),denied_sequence_epochs=sorted(denied),receipts=records)


def freeze_normalized_sources(data_root, day, out):
    OUT=Path(out)
    OUT.mkdir(parents=True,exist_ok=True)
    snapshot=discover(data_root, day)
    quality=_source_quality_receipt(data_root,day)
    dump(OUT/'frozen-input-list.json',dict(captured_at=datetime.now(KST).isoformat(),partitions=snapshot,source_quality_receipt=quality))
    outputs=[]
    for spec in snapshot:
        target=OUT/f"stream-{spec['day']}-{spec['venue']}-{spec['session']}.json.gz"
        groups=defaultdict(list);issues=Counter();receipts=[];row_count=0
        for source in spec['files']:
            path=Path(source['path']);digest=hashlib.sha256();processed=0;lines=0
            with path.open('rb') as raw:
                start=os.fstat(raw.fileno())
                compressed=path.suffix=='.gz'
                handle=gzip.GzipFile(fileobj=raw) if compressed else raw
                while True:
                    remaining=source['bytes']-raw.tell() if not compressed else None
                    if remaining is not None and remaining<=0:break
                    line=handle.readline(remaining if remaining is not None else -1)
                    if not line:break
                    if not line.endswith(b'\n'):
                        issues['incomplete_last_line']+=1;break
                    digest.update(line);processed+=len(line);lines+=1
                    try:r=json.loads(line)
                    except ValueError:issues['invalid_json']+=1;continue
                    if not isinstance(r,dict):issues['invalid_json_row_type']+=1;continue
                    if r.get('schema')!='scalp_micro_reversion_market_stream_point_v3':
                        issues['unsupported_schema']+=1;continue
                    code=r.get('symbol')
                    if not isinstance(code,str) or len(code)!=6 or not code.isdigit():
                        issues['invalid_symbol']+=1;continue
                    try:
                        dt=datetime.fromisoformat(r['local_receive_timestamp'])
                        ex=datetime.fromisoformat(r['exchange_timestamp'])
                        assert dt.tzinfo and ex.tzinfo and dt.date().isoformat()==spec['day']
                        assert r['venue']==spec['venue'] and r['session_bucket']==spec['session']
                        ep,seq=r['sequence_epoch'],r['series_sequence']
                        assert type(ep) is int and ep>0 and type(seq) is int and seq>0
                    except (KeyError,TypeError,ValueError,AssertionError):
                        issues['identity_clock_invalid']+=1;continue
                    t=dt.timestamp();exchange=ex.timestamp()
                    price,bid,ask,qty=(num(r.get(k)) for k in ('trade_price','best_bid','best_ask','trade_qty'))
                    source_contract=r.get("source_contract")
                    verified=True
                    if source_contract is not None:
                        if source_contract!="main_market_source_v1":
                            verified=False;issues['unsupported_source_contract']+=1
                        elif not quality['eligible']:
                            verified=False;issues['source_quality:'+quality['status']]+=1
                        elif ep not in quality['allowed_sequence_epochs']:
                            verified=False;issues['source_epoch_unverified']+=1
                        item=r.get('source_item')
                        if registration_item_market_data_identity(item)[0]!=code or market_source_partition_venue(item)!=spec['venue']:
                            verified=False;issues['source_item_identity_invalid']+=1
                        for name in ('native_transport_epoch','native_route_sequence'):
                            value=r.get(name)
                            if value is not None and (type(value) is not int or value<=0):
                                verified=False;issues['native_namespace_invalid']+=1
                    if r.get('native_receive_session') is not None and r['native_receive_session'] != r['session_bucket']:
                        verified=False;issues['receive_exchange_session_boundary_mismatch']+=1
                    valid=(verified and r.get('path_consumer_eligible') is True and r.get('path_order_status')=='accept'
                           and price is not None and price>0 and 0<=t-exchange<=5)
                    side={'BUY':1,'SELL':-1}.get(r.get('aggressor_side'),0)
                    # Preserve invalid rows to break paths. Never turn them into
                    # missing zero returns or delete a price gap silently.
                    groups[code].append([t,ep,seq,price,bid,ask,qty,side,int(valid),
                                         r.get('source_item'),r.get('quote_age_ms'),
                                         r.get('native_transport_epoch'),r.get('native_route_sequence'),
                                         r.get('native_receive_session'),r['session_bucket']])
                    row_count+=1
                end=os.fstat(raw.fileno())
                current=path.stat()
                if (current.st_dev,current.st_ino)!=(start.st_dev,start.st_ino):
                    raise RuntimeError('source_replaced:'+str(path))
                if not compressed:
                    raw.seek(0);check=hashlib.sha256();remaining=processed
                    while remaining:
                        block=raw.read(min(1024*1024,remaining))
                        if not block:raise RuntimeError('source_truncated:'+str(path))
                        check.update(block);remaining-=len(block)
                    if check.hexdigest()!=digest.hexdigest():raise RuntimeError('source_prefix_changed:'+str(path))
            if compressed and (start.st_size!=end.st_size or start.st_mtime_ns!=end.st_mtime_ns):
                raise RuntimeError('compressed_source_changed:'+str(path))
            if not compressed and end.st_size<source['bytes']:
                raise RuntimeError('source_truncated:'+str(path))
            receipts.append(dict(**source,complete_uncompressed_bytes=processed,lines=lines,
                uncompressed_complete_prefix_sha256=digest.hexdigest(),compressed=compressed,
                snapshot_semantics='frozen byte prefix; last partial line omitted' if not compressed else 'fixed archive'))
        # Shards can overlap after maintenance. Deduplicate by native record
        # identity; conflicting copies mark the observation invalid.
        for code,rows in groups.items():
            identities={}
            for row in rows:
                key=(row[1],row[2]);old=identities.get(key)
                if old is not None:
                    if old!=row:old[8]=0;issues['conflicting_duplicate']+=1
                    else:issues['identical_duplicate']+=1
                else:identities[key]=row
            groups[code]=sorted(identities.values(),key=lambda x:(x[0],x[1],x[2]))
        body=dict(day=spec['day'],venue=spec['venue'],session=spec['session'],columns=
            ['receive_epoch','transport_epoch','series_sequence','trade_price','bid','ask','qty','side','valid','source_item','quote_age_ms','native_transport_epoch','native_route_sequence','native_receive_session','exchange_session'],
            symbols=groups,source_receipts=receipts,source_quality_receipt=quality,issues=dict(issues),runtime_effect=False,
            namespace_contract=dict(transport_epoch_column='collector_sequence_epoch',native_transport_epoch='ws_native_epoch',native_route_sequence='ws_native_route_sequence'),
            metric_role='source_quality_gate',decision_authority='report_only',window_policy='sealed_complete_prefix_exact_route_epoch',
            sample_floor='none',primary_decision_metric='eligible_source_rows',source_quality_gate='row_clock_sequence_and_versioned_closed_epoch',
            forbidden_uses=['order_authority','execution_venue_claim','economic_claim','policy_promotion'])
        target.write_bytes(gzip.compress(json.dumps(body,separators=(',',':'),allow_nan=False).encode(),compresslevel=1,mtime=0))
        outputs.append(dict(day=spec['day'],venue=spec['venue'],session=spec['session'],path=str(target),sha256=sha(target),
            rows=sum(map(len,groups.values())),symbols=len(groups),samsung_rows=len(groups.get('005930',[])),issues=dict(issues)))
        print(spec['day'],spec['venue'],spec['session'],'rows',outputs[-1]['rows'],'symbols',len(groups),'Samsung',outputs[-1]['samsung_rows'],flush=True)
    dump(OUT/'source-manifest.json',dict(captured_at=datetime.now(KST).isoformat(),partitions=outputs,
        extraction_sha256=sha(Path(__file__)),frozen_list_sha256=sha(OUT/'frozen-input-list.json'),
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False))

    return outputs
