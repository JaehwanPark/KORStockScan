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
        for p in files:
            name=p.name.removesuffix('.gz')
            if name not in logical or p.suffix!='.gz':logical[name]=p
        if not logical:continue
        day=folder.parts[-3].split('=')[1]
        venue=folder.parts[-2].split('=')[1]
        session=folder.parts[-1].split('=')[1]
        result.append(dict(day=day,venue=venue,session=session,
            files=[dict(path=str(p),bytes=p.stat().st_size) for p in sorted(logical.values())]))
    return result


def freeze_normalized_sources(data_root, day, out):
    OUT=Path(out)
    OUT.mkdir(parents=True,exist_ok=True)
    snapshot=discover(data_root, day)
    dump(OUT/'frozen-input-list.json',dict(captured_at=datetime.now(KST).isoformat(),partitions=snapshot))
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
                        assert type(ep) is int and type(seq) is int and seq>0
                    except (KeyError,TypeError,ValueError,AssertionError):
                        issues['identity_clock_invalid']+=1;continue
                    t=dt.timestamp();exchange=ex.timestamp()
                    price,bid,ask,qty=(num(r.get(k)) for k in ('trade_price','best_bid','best_ask','trade_qty'))
                    valid=(r.get('path_consumer_eligible') is True and r.get('path_order_status')=='accept'
                           and price is not None and price>0 and 0<=t-exchange<=5)
                    side={'BUY':1,'SELL':-1}.get(r.get('aggressor_side'),0)
                    # Preserve invalid rows to break paths. Never turn them into
                    # missing zero returns or delete a price gap silently.
                    groups[code].append([t,ep,seq,price,bid,ask,qty,side,int(valid),
                                         r.get('source_item'),r.get('quote_age_ms')])
                    row_count+=1
                end=os.fstat(raw.fileno())
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
            ['receive_epoch','transport_epoch','series_sequence','trade_price','bid','ask','qty','side','valid','source_item','quote_age_ms'],
            symbols=groups,source_receipts=receipts,issues=dict(issues),runtime_effect=False)
        target.write_bytes(gzip.compress(json.dumps(body,separators=(',',':'),allow_nan=False).encode(),compresslevel=1,mtime=0))
        outputs.append(dict(day=spec['day'],venue=spec['venue'],session=spec['session'],path=str(target),sha256=sha(target),
            rows=sum(map(len,groups.values())),symbols=len(groups),samsung_rows=len(groups.get('005930',[])),issues=dict(issues)))
        print(spec['day'],spec['venue'],spec['session'],'rows',outputs[-1]['rows'],'symbols',len(groups),'Samsung',outputs[-1]['samsung_rows'],flush=True)
    dump(OUT/'source-manifest.json',dict(captured_at=datetime.now(KST).isoformat(),partitions=outputs,
        extraction_sha256=sha(Path(__file__)),frozen_list_sha256=sha(OUT/'frozen-input-list.json'),
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False))

    return outputs
