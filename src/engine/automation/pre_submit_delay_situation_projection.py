"""Offline native situation join; original delay and quote receipts stay sealed.

Existing partitioned research owns invocation and resource admission. SQLite
bounds retained memory; each required native date is streamed once. This module
has no runtime, provider, order or policy publication authority.
"""
import gzip
import hashlib
import json
from datetime import datetime
from pathlib import Path

from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.engine.lifecycle.holding_window_generation import byte_generation

MAX_LINE = 6 * 1024 * 1024


def prepare(rows, db, root):
    db.execute('CREATE TABLE situation_needed(day TEXT,machine TEXT,attempt TEXT,symbol TEXT,parent TEXT,'
               'PRIMARY KEY(day,machine,attempt,symbol,parent)) WITHOUT ROWID')
    db.execute('CREATE TABLE situation_native(day TEXT,machine TEXT,body TEXT,conflict INTEGER DEFAULT 0,'
               'PRIMARY KEY(day,machine)) WITHOUT ROWID')
    for row in rows:
        f = row.get('fields') or {}
        if row.get('stage') != 'pre_submit_delay_committed' or str(f.get('anchor_contract_version')) == '4':
            continue
        machine = f.get('original_machine_observation_sha256')
        attempt = f.get('evaluation_attempt_id')
        parent = f.get('entry_mechanistic_policy_sha256')
        if not all(isinstance(v,str) and v for v in (machine,attempt,parent)) or len(machine)!=64 or len(parent)!=64:
            continue
        db.execute('INSERT OR IGNORE INTO situation_needed VALUES (?,?,?,?,?)',
            (row['emitted_date'],machine,attempt,str(row['stock_code']),parent))
    sources, logical_sources, census = {}, {}, dict(captured=0, recovered=0, unresolved=0, invalid_native_rows=0, logical_bytes=0)
    from src.engine.scalping.ai_decision_trace import _json_bytes
    for day, in db.execute('SELECT DISTINCT day FROM situation_needed ORDER BY day'):
        logical=Path(root)/'ai_decision_payloads'/f'ai_decision_payloads_{day}.jsonl'
        aliases=[p for p in (logical,Path(str(logical)+'.gz')) if p.exists()]
        seals=[]
        for alias_n,path in enumerate(aliases):
            if path.is_symlink():raise ValueError('delay_native_situation_symlink')
            before=byte_generation(path);logical_sha=hashlib.sha256();size=0
            opener=gzip.open if path.suffix=='.gz' else open
            with opener(path,'rb') as handle:
                while True:
                    raw=handle.readline(MAX_LINE+1)
                    if not raw:break
                    logical_sha.update(raw);size+=len(raw)
                    if len(raw)>MAX_LINE or not raw.endswith(b'\n'):
                        raise ValueError('delay_native_situation_record_invalid')
                    if alias_n:continue
                    try:r=json.loads(raw)
                    except (ValueError,UnicodeDecodeError):
                        census['invalid_native_rows']+=1;continue
                    if not isinstance(r,dict):continue
                    machine=r.get('machine_observation_sha256')
                    needed=db.execute('SELECT attempt,symbol,parent FROM situation_needed WHERE day=? AND machine=?',
                                      (day,machine)).fetchall() if isinstance(machine,str) else []
                    if not needed:continue
                    context=r.get('label_context') or {};source=r.get('source') or {}
                    assessment=source.get('assessment') or {} if isinstance(source,dict) else None
                    if (hashlib.sha256(_json_bytes({k:v for k,v in r.items() if k!='machine_observation_sha256'})).hexdigest()!=machine
                            or not isinstance(context,dict) or not isinstance(assessment,dict)):
                        census['invalid_native_rows']+=1;continue
                    if assessment.get('action') != 'ENTER_NOW':
                        census['invalid_native_rows']+=1;continue
                    native=(context.get('evaluation_attempt_id'),str(context.get('stock_code')),assessment.get('machine_component_sha256'))
                    if native not in needed:
                        census['invalid_native_rows']+=1;continue
                    fields=initial.situation_fields(dict(entry_mechanistic_policy_decision=assessment))
                    if initial.situation(fields)=='UNKNOWN':continue
                    body=json.dumps(dict(fields=fields,attempt=native[0],symbol=native[1],parent=native[2],
                        native_observation_sha256=machine,captured_at=r.get('captured_at')),sort_keys=True,separators=(',',':'))
                    db.execute('INSERT INTO situation_native(day,machine,body) VALUES (?,?,?) '
                        'ON CONFLICT(day,machine) DO UPDATE SET conflict=CASE WHEN body!=excluded.body THEN 1 ELSE conflict END',
                        (day,machine,body));census['captured']+=1
            if byte_generation(path)!=before:raise ValueError('delay_native_situation_source_changed')
            sources[str(path.resolve())]={k:before[k] for k in ('size','sha256')}
            seals.append((size,logical_sha.hexdigest()));census['logical_bytes']+=size
        if len(set(seals))>1:raise ValueError('delay_native_situation_alias_conflict')
        if seals:logical_sources[str(logical.resolve())] = dict(size=seals[0][0],sha256=seals[0][1])
    return dict(schema='pre_submit_delay_native_situation_projection_v1',sources=sources,logical_sources=logical_sources,census=census,
                mapping_version=initial.MAPPING_VERSION)


def enrich(rows, db, receipt):
    for row in rows:
        fields=row.get('fields') or {}
        if row.get('stage')=='pre_submit_delay_committed' and str(fields.get('anchor_contract_version'))!='4':
            item=db.execute('SELECT body,conflict FROM situation_native WHERE day=? AND machine=?',
                (row['emitted_date'],fields.get('original_machine_observation_sha256'))).fetchone()
            if item and not item[1]:
                proof=json.loads(item[0])
                try:
                    capture_clock = datetime.fromisoformat(proof.get('captured_at') or '')
                    if capture_clock.tzinfo is None:raise ValueError('native_capture_clock_unbound')
                    captured = capture_clock.timestamp()
                    committed = float(fields.get('decision_committed_at_epoch'))
                    causal = captured <= committed
                except (TypeError, ValueError, OverflowError):
                    causal = False
                if (causal and proof['attempt']==fields.get('evaluation_attempt_id')
                    and proof['symbol']==str(row['stock_code'])
                    and proof['parent']==fields.get('entry_mechanistic_policy_sha256')):
                    row={**row,'fields':{**fields,'_native_situation_projection':proof}}
                    receipt['census']['recovered']+=1
                else:receipt['census']['unresolved']+=1
            else:receipt['census']['unresolved']+=1
        yield row


def verify(receipt):
    if receipt.get('schema')!='pre_submit_delay_native_situation_projection_v1':
        raise ValueError('delay_native_situation_receipt_invalid')
    for name,expected in receipt['logical_sources'].items():
        logical=Path(name)
        aliases=[p for p in (logical,Path(name+'.gz')) if p.exists()]
        if not aliases:raise ValueError('delay_native_situation_source_missing')
        for path in aliases:
            if path.is_symlink():raise ValueError('delay_native_situation_symlink')
            physical=byte_generation(path)
            # prepare fully decoded this exact physical generation, including
            # CRC/EOF. Reuse that native validation when its bytes are unchanged.
            if receipt['sources'].get(str(path)) == {k:physical[k] for k in ('size','sha256')}:
                continue
            before=path.stat()
            sha=hashlib.sha256();size=0
            with (gzip.open if path.suffix=='.gz' else open)(path,'rb') as handle:
                for block in iter(lambda:handle.read(1024*1024),b''):
                    sha.update(block);size+=len(block)
            after=path.stat()
            identity=lambda st:(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
            if identity(before)!=identity(after) or dict(size=size,sha256=sha.hexdigest())!=expected:
                raise ValueError('delay_native_situation_source_changed')
