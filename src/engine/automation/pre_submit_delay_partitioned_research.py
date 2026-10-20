"""Offline all-population timing source and sharded evidence orchestration.

The scalping owner defines qualification/selection and runtime lookup. This
producer replaces resident raw indexes and ID lists with bounded disk work.
No broker, model, order or runtime configuration calls are permitted here.
"""
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation, source_stat
from src.engine.scalping import pre_submit_delay_initial_policy as initial
from src.engine.scalping import pre_submit_delay_tuning as owner

STORAGE_SCHEMA = 'pre_submit_delay_sharded_evidence_v3'


class EvidenceDocument(dict):
    """The verified file location is reader context, not source JSON metadata."""
    def __init__(self, value, root):
        super().__init__(value)
        self.evidence_root = Path(root)


def inventory(root, day):
    return sorted((date, path) for directory in (Path(root)/'threshold_cycle').glob(
        'date=*/family=pre_submit_delay')
        if owner.policy_refresh_start_date(day) <= (date := directory.parent.name.removeprefix('date=')) <= day
        for path in directory.glob('part-execution-*.jsonl'))


class Source:
    def __init__(self, day, root, connection, source):
        self.target_date, self.data_root, self.connection, self.source = day, Path(root).resolve(), connection, source

    @property
    def rows(self):
        return (row for _, row, _ in storage.records(self.connection))

    def verify(self, day, root):
        if day != self.target_date or Path(root).resolve() != self.data_root:
            raise ValueError('delay_snapshot_date_or_root_changed')
        if [str(p) for _,p in inventory(root, day)] != self.source['paths']:
            raise ValueError('delay_snapshot_inventory_changed')
        for name, expected in self.source['partition_generations'].items():
            current = byte_generation(Path(name))
            if {k:current[k] for k in ('size','sha256')} != expected:
                raise ValueError('delay_snapshot_generation_changed')


def compact_projection(row, date):
    from src.engine.pipeline_event_summary import execution_projection_identity
    if row.get('emitted_date') != date or row.get('family') != owner.FAMILY:
        raise ValueError('delay_partition_date_or_family_mismatch')
    if row.get('stage') not in owner.SOURCE_STAGES: return None
    identity=row.get('execution_source_event_sha256')
    if identity!=execution_projection_identity(row):
        raise ValueError('delay_partition_projection_identity_mismatch')
    fields=row['fields']
    retained={k:v for k,v in row.items() if k!='fields'}
    retained['fields']={k:v for k,v in fields.items() if k in owner._V2_SOURCE_FIELDS}
    retained['fields']['_source_fields_sha256']=owner._digest(fields)
    return {'identity':identity,'content_sha256':owner._digest({k:v for k,v in row.items()
        if k!='execution_source_event_sha256'}),'row':retained}


@contextmanager
def source(root, day, scratch, *, checkpoint_root=None):
    from src.engine.lifecycle.research_jsonl_jobs import scan
    paths=inventory(root,day)
    cache=Path(checkpoint_root) if checkpoint_root is not None else Path(scratch)/'scan-cache'
    with storage.index(scratch) as db:
        sha,dates,generations,cumulative,stages=hashlib.sha256(),set(),{},{},Counter()
        raw_n,invalid_n,scan_bytes,jobs,reused=0,0,0,0,0
        projection=initial.digest([initial.code_contract(),initial.projection_contract()])
        for date,path in paths:
            storage.safe_path(Path(root),str(path.relative_to(root)))
            for item in scan(path,output_root=cache,project=lambda row:compact_projection(row,date),
                projection_sha256=initial.digest([projection,date]),job_bytes=owner.MAX_V2_SCAN_BYTES):
                if item['kind']=='row':
                    value=item['value'];row=value['row'];raw_n+=1;stages[row['stage']]+=1
                    storage.put(db,value['identity'],row,content_sha=value['content_sha256'])
                elif item['kind']=='checkpoint':
                    jobs+=1;reused+=int(item['reused']);invalid_n+=item['receipt']['census'].get('isolated_records',0)
                elif item['kind']=='source':
                    generation=item['generation'];scan_bytes+=generation['size']
                    generations[str(path)]={k:generation[k] for k in ('size','sha256')}
            # Global/cumulative ledger seals are exact concatenated source bytes.
            with path.open('rb') as handle:
                for block in iter(lambda:handle.read(65536),b''): sha.update(block)
            cumulative[date]={'sha256':sha.hexdigest(),'paths':list(generations)};dates.add(date)
        conflicts=db.execute('SELECT count(*) FROM records WHERE conflicted=1').fetchone()[0]
        duplicates=db.execute('SELECT count(*) FROM records WHERE copies>1').fetchone()[0]
        receipt=dict(paths=[str(p) for _,p in paths],partition_generations=generations,
            cumulative_generations=cumulative,source_dates=sorted(dates),sha256=sha.hexdigest() if paths else None,
            raw_stage_counts=dict(stages),raw_event_count=raw_n,bytes_read=scan_bytes,
            isolated_records=invalid_n,conflicted_records=conflicts,duplicate_event_count=duplicates,
            scan_jobs=jobs,scan_jobs_reused=reused)
        snapshot=Source(day,root,db,receipt);snapshot.verify(day,root)
        yield snapshot
        snapshot.verify(day,root)


def _semantic(row):
    return initial.digest({k:v for k,v in row.items() if k not in {'alias', 'decision_source_sha256'}})


def project(rows, db):
    """Global qualification before split, including cross-shard late conflicts."""
    db.execute('CREATE TABLE events (intent TEXT, stage TEXT, horizon REAL, sha TEXT, '
               'body TEXT, conflict INTEGER DEFAULT 0, PRIMARY KEY(intent,stage,horizon)) WITHOUT ROWID')
    census, exclusions = Counter(), Counter()
    for row in rows:
        fields = row.get('fields')
        if not isinstance(fields, dict):
            exclusions['fields_missing'] += 1; continue
        identity = [str(row.get('emitted_date')), str(row.get('stock_code')), str(fields.get('delay_intent_id') or '')]
        if not identity[-1]:
            exclusions['intent_identity_missing'] += 1; continue
        stage = row.get('stage')
        horizon = initial.number(fields.get('target_delay_sec')) if stage == 'pre_submit_delay_quote_observed' else -1
        if stage not in {'pre_submit_delay_committed','pre_submit_delay_quote_observed'} or (
                stage == 'pre_submit_delay_quote_observed' and horizon not in owner.OBSERVATION_HORIZONS):
            continue
        sha = fields.get('_source_fields_sha256') or owner._digest(fields)
        db.execute('INSERT INTO events(intent,stage,horizon,sha,body) VALUES (?,?,?,?,?) '
            'ON CONFLICT(intent,stage,horizon) DO UPDATE SET conflict=CASE WHEN events.sha!=excluded.sha '
            'THEN 1 ELSE conflict END', (initial.digest(identity), stage, horizon, sha, storage.encoded(row).decode()))
    for intent, in db.execute('SELECT DISTINCT intent FROM events ORDER BY intent'):
        parts, commit_conflict, bad_quotes = [], False, 0
        for stage, body, conflict in db.execute('SELECT stage,body,conflict FROM events WHERE intent=? '
                                               'ORDER BY stage,horizon', (intent,)):
            if conflict:
                if stage == 'pre_submit_delay_committed':
                    commit_conflict = True
                else:
                    bad_quotes += 1
            else:
                parts.append(json.loads(body))
        if commit_conflict:
            census['raw_commit_n'] += 1; exclusions['commit_or_effective_pass_invalid'] += 1
            continue
        projected, counts = initial.project_rows(parts)
        census['raw_commit_n'] += counts['raw_commit_n']
        exclusions.update(counts['exclusions'])
        if projected:
            exclusions['quote:values_or_conflict_invalid'] += bad_quotes
        for row in projected:
            row['pairs'] = {str(k):v for k,v in row['pairs'].items()}
            storage.put(db, row['identity'], row, content_sha=_semantic(row))
    for _,row,copies in storage.records(db):
        census['qualified_pass_n'] += 1
        census['p0_valid_n'] += int(row['p0_valid'])
        census['native_evaluation_unverified_n'] += int(not row['native_evaluation_bound'])
        census['parent_compatibility_unverified_n'] += int(any(len(p)!=64 or any(c not in '0123456789abcdef' for c in p)
            for p in row['parent_compatibility']))
        exclusions['duplicate_opportunity_alias'] += copies-1
    conflicts = db.execute('SELECT count(*) FROM records WHERE conflicted=1').fetchone()[0]
    if conflicts:
        exclusions['canonical_opportunity_conflict'] += conflicts
    return {**{k:census[k] for k in ('raw_commit_n','qualified_pass_n','p0_valid_n',
        'native_evaluation_unverified_n','parent_compatibility_unverified_n')},
        'exclusions':{k:v for k,v in exclusions.items() if v}}


def _ids_digest(db, where, args):
    sha, first = hashlib.sha256(), True
    sha.update(b'[')
    for identity, in db.execute('SELECT id FROM population WHERE '+where+' ORDER BY at,id', args):
        if not first: sha.update(b',')
        sha.update(storage.encoded(identity)); first = False
    sha.update(b']')
    return sha.hexdigest()


def _stats(db, where, args, horizon, denominator):
    query = f'SELECT p{horizon} FROM population WHERE {where} AND p{horizon} IS NOT NULL'
    count = db.execute('SELECT count(*) FROM ('+query+')', args).fetchone()[0]
    def quantile(fraction):
        if not count: return None
        at = (count-1)*fraction; lo, hi = int(at), math.ceil(at)
        values = [r[0] for r in db.execute(query+f' ORDER BY p{horizon} LIMIT ? OFFSET ?', (*args, hi-lo+1, lo))]
        return values[0]+(values[-1]-values[0])*(at-lo)
    total = math.fsum(r[0] for r in db.execute(query+f' ORDER BY p{horizon}', args))
    signs = dict(db.execute('SELECT sign,count(*) FROM (SELECT CASE WHEN v>0 THEN 1 WHEN v<0 THEN -1 ELSE 0 END sign '
        'FROM ('+query.replace(f'SELECT p{horizon}', f'SELECT p{horizon} v')+')) GROUP BY sign', args))
    return dict(n=count, eligible_n=denominator, coverage=count/denominator if denominator else 0,
        mean_bp=total/count if count else None, median_bp=quantile(.5), p10_bp=quantile(.1), p90_bp=quantile(.9),
        improved_n=signs.get(1,0), worsened_n=signs.get(-1,0), equal_n=signs.get(0,0))


def _select_legacy(db, base, args):
    train, validation = base+" AND split='train'", base+" AND split='validation'"
    train_n = db.execute('SELECT count(*) FROM population WHERE '+train,args).fetchone()[0]
    validation_n = db.execute('SELECT count(*) FROM population WHERE '+validation,args).fetchone()[0]
    candidates = [d for d in initial.HORIZONS[1:] if db.execute(
        f'SELECT 1 FROM population WHERE {train} AND p{d} IS NOT NULL LIMIT 1',args).fetchone()]
    common = train + ''.join(f' AND p{d} IS NOT NULL' for d in candidates)
    common_n = db.execute('SELECT count(*) FROM population WHERE '+common,args).fetchone()[0] if candidates else 0
    empty = dict(delay_sec=None, selection_basis='unsupported', runtime_apply_allowed=False,
        train=initial._stats([],train_n), validation=initial._stats([],validation_n),
        candidate_delays_sec=candidates, comparison_delay_sec=None)
    if not common_n: return empty
    metrics = {d:_stats(db,common,args,d,train_n) for d in candidates}
    best = min(candidates,key=lambda d:(-metrics[d]['mean_bp'],d))
    holdout = _stats(db,validation,args,best,validation_n)
    if not holdout['n']:
        return {**empty,'comparison_delay_sec':best,'train':metrics[best]}
    basis = ('paired_quote_initial' if metrics[best]['mean_bp']>0 and holdout['mean_bp']>0 else
        'paired_quote_immediate' if metrics[best]['mean_bp']<=0 and holdout['mean_bp']<=0 else 'incumbent_on_unconfirmed_pattern')
    return {**empty, 'delay_sec':best if basis=='paired_quote_initial' else 0,'selection_basis':basis,
        'runtime_apply_allowed':True,'comparison_delay_sec':best,'train':metrics[best], 'validation':holdout,
        'train_ids_sha256':_ids_digest(db,common,args),
        'validation_ids_sha256':_ids_digest(db,validation+f' AND p{best} IS NOT NULL',args)}


def _select(db, base, args, *, horizons=initial.HORIZONS):
    train, validation = base+" AND split='train'", base+" AND split='validation'"
    train_n = db.execute('SELECT count(*) FROM population WHERE '+train,args).fetchone()[0]
    validation_n = db.execute('SELECT count(*) FROM population WHERE '+validation,args).fetchone()[0]
    candidates = [d for d in horizons[1:] if db.execute(
        f'SELECT 1 FROM population WHERE {train} AND p{d} IS NOT NULL LIMIT 1',args).fetchone()]
    metrics = {d:_stats(db,train,args,d,train_n) for d in candidates}
    empty = dict(delay_sec=None,selection_basis='unsupported',runtime_apply_allowed=False,
        train=initial._stats([],train_n),validation=initial._stats([],validation_n),
        candidate_delays_sec=candidates,comparison_delay_sec=None,
        candidate_train_stats={str(d):s for d,s in metrics.items()},
        population_role='candidate_same_opportunity_p0_pairs')
    if not candidates: return empty
    best = min(candidates,key=lambda d:(-metrics[d]['mean_bp'],d))
    holdout = _stats(db,validation,args,best,validation_n)
    if not holdout['n']:
        return {**empty,'comparison_delay_sec':best,'train':metrics[best]}
    basis = ('paired_quote_initial' if metrics[best]['mean_bp']>0 and holdout['mean_bp']>0 else
        'paired_quote_immediate' if metrics[best]['mean_bp']<=0 and holdout['mean_bp']<=0 else
        'incumbent_on_unconfirmed_pattern')
    return {**empty,'delay_sec':best if basis=='paired_quote_initial' else 0,
        'selection_basis':basis,'runtime_apply_allowed':True,'comparison_delay_sec':best,
        'train':metrics[best],'validation':holdout,
        'train_ids_sha256':_ids_digest(db,train+f' AND p{best} IS NOT NULL',args),
        'validation_ids_sha256':_ids_digest(db,validation+f' AND p{best} IS NOT NULL',args)}


def _populate(db, projected, *, effective_date, algorithm):
    horizons = initial.candidate_horizons(algorithm)[1:]
    db.execute('CREATE TABLE population (id TEXT PRIMARY KEY, body TEXT, gid TEXT, anchor TEXT, '
        'market TEXT, parents TEXT, kind TEXT, at REAL, end REAL, native INTEGER, p0 INTEGER, '
        + ','.join(f'p{d} REAL' for d in horizons) + ',split TEXT,eligible INTEGER) WITHOUT ROWID')
    for row in projected:
        parents = row.get('parent_compatibility')
        pairs = row.get('pairs')
        if (not isinstance(row.get('identity'),str) or len(row['identity'])!=64
                or any(c not in '0123456789abcdef' for c in row['identity'])
                or initial.number(row.get('committed_at')) is None
                or row.get('observation_end_at') != row['committed_at']+183
                or row.get('anchor_kind') not in {'price_ready','signal_ready'}
                or row.get('session') not in initial.MARKETS
                or not isinstance(parents,list) or len(parents)!=2
                or any(not isinstance(p,str) for p in parents)
                or type(row.get('native_evaluation_bound')) is not bool
                or type(row.get('p0_valid')) is not bool or not isinstance(pairs,dict)
                or any(str(k) not in {'30','60','120','180'} or initial.number(v) is None for k,v in pairs.items())
                or not isinstance(row.get('situation'),str) or len(row['situation'])>2048):
            raise ValueError('initial_delay_projection_invalid')
        group = [row['anchor_kind'],row['session'],row['parent_compatibility']]
        pairs = initial.selection_pairs(row, algorithm)
        db.execute('INSERT INTO population VALUES (' + ','.join('?' for _ in range(13+len(horizons))) + ')',
            (row['identity'],storage.encoded(row).decode(),initial.digest(group),row['anchor_kind'],
             row['session'],storage.encoded(row['parent_compatibility']).decode(),row['situation'],
             row['committed_at'],row['observation_end_at'],int(row['native_evaluation_bound']),int(row['p0_valid']),
             *(pairs.get(d) for d in horizons), 'unqualified',
             int(row['p0_valid'] and (algorithm==initial.LEGACY_ALGORITHM or initial.lineage_eligible(row,effective_date)))))
    db.execute('CREATE INDEX population_time ON population(gid,at,id)')
    db.execute('CREATE INDEX population_cells ON population(gid,kind,split)')
    for group,count in db.execute('SELECT gid,count(*) FROM population WHERE eligible=1 GROUP BY gid ORDER BY gid'):
        split = min(count-1,max(1,int(count*.7))) if count>1 else count
        boundary = db.execute('SELECT at,id FROM population WHERE gid=? AND eligible=1 ORDER BY at,id LIMIT 1 OFFSET ?',
                              (group,split)).fetchone()
        if boundary:
            at, identity = boundary
            db.execute("UPDATE population SET split=CASE WHEN at>? OR (at=? AND id>=?) THEN 'validation' "
                       "WHEN end>=? THEN 'purged' ELSE 'train' END WHERE gid=? AND eligible=1",(at,at,identity,at,group))
        else:
            db.execute("UPDATE population SET split='train' WHERE gid=? AND eligible=1",(group,))


def _group_rows(db, root):
    for group,anchor,market,parents in db.execute('SELECT DISTINCT gid,anchor,market,parents FROM population '
                                                 'WHERE p0=1 ORDER BY anchor,market,parents'):
        ref = storage.write_tree(root, ({'identity':i,'split':s} for i,s in db.execute(
            'SELECT id,split FROM population WHERE gid=? AND p0=1 ORDER BY at,id',(group,))))
        body = dict(anchor_kind=anchor,session=market,parent_compatibility=json.loads(parents),membership=ref)
        body['sha256'] = initial.digest(storage.logical_value(body))
        db.execute('CREATE TABLE IF NOT EXISTS groups (gid TEXT PRIMARY KEY, body TEXT) WITHOUT ROWID')
        db.execute('INSERT INTO groups VALUES (?,?)',(group,storage.encoded(body).decode()))
        yield body


def _cell_rows(db, effective, algorithm):
    for group,anchor,market,parents in db.execute('SELECT DISTINCT gid,anchor,market,parents FROM population '
                                                 'WHERE p0=1 ORDER BY anchor,market,parents'):
        parent = json.loads(parents)
        partition = json.loads(db.execute('SELECT body FROM groups WHERE gid=?',(group,)).fetchone()[0])
        kinds = ['ALL'] + [k for k, in db.execute("SELECT DISTINCT kind FROM population WHERE gid=? AND p0=1 "
            "AND kind NOT IN ('ALL','UNKNOWN') ORDER BY kind",(group,))]
        for kind in kinds:
            base,args = 'gid=? AND p0=1',(group,)
            if kind != 'ALL': base += ' AND kind=?'; args += (kind,)
            selected = (_select_legacy(db,base,args) if algorithm==initial.LEGACY_ALGORITHM else
                        _select(db,base,args,horizons=initial.candidate_horizons(algorithm)))
            if algorithm!=initial.LEGACY_ALGORITHM and not db.execute(
                    'SELECT 1 FROM population WHERE gid=? AND eligible=1 LIMIT 1',(group,)).fetchone():
                selected = {**selected,'delay_sec':0,'selection_basis':'unverified_lineage_immediate_default',
                            'runtime_apply_allowed':False}
            unverified = any(len(p)!=64 or any(c not in '0123456789abcdef' for c in p) for p in parent)
            unverified = unverified or bool(db.execute('SELECT 1 FROM population WHERE '+base+
                " AND split IN ('train','validation') AND native=0 LIMIT 1",args).fetchone())
            if algorithm==initial.LEGACY_ALGORITHM and effective >= '2026-10-10' and unverified:
                selected = {**selected,'delay_sec':0,'selection_basis':'unverified_lineage_immediate_default',
                            'runtime_apply_allowed':False}
            key = initial.cell_key(anchor,market,kind,parents=parent)
            yield {'key':key,'value':{**selected,'anchor_kind':anchor,'session':market,'situation':kind,
                'execution_context':'ALL','parent_compatibility':parent,'partition_sha256':partition['sha256'],
                'fallback_key':initial.cell_key(anchor,market,parents=parent) if kind!='ALL' else None,
                'evidence_grade':'estimated_provisional'}}


def build(projected, census, *, output_root, source_date, publication_date, effective_date,
          source_sha256, code_contract_sha256, source_receipt, _algorithm=None, _projection_contract=None, _mapping_version=None):
    algorithm = _algorithm or initial.ALGORITHM
    if algorithm not in initial.ALGORITHMS:
        raise ValueError('initial_delay_algorithm_invalid')
    from datetime import date
    if not date.fromisoformat(source_date) <= date.fromisoformat(publication_date) < date.fromisoformat(effective_date):
        raise ValueError('initial_delay_dates_invalid')
    root = Path(output_root)
    with storage.index(root) as db:
        _populate(db,projected,effective_date=effective_date,algorithm=algorithm)
        observed = {'qualified_pass_n':0,'p0_valid_n':0,'native_evaluation_unverified_n':0,
                    'parent_compatibility_unverified_n':0}
        for body, in db.execute('SELECT body FROM population'):
            row=json.loads(body); observed['qualified_pass_n']+=1
            observed['p0_valid_n']+=int(row['p0_valid'])
            observed['native_evaluation_unverified_n']+=int(not row['native_evaluation_bound'])
            observed['parent_compatibility_unverified_n']+=int(any(len(p)!=64 or any(c not in '0123456789abcdef' for c in p)
                for p in row['parent_compatibility']))
        if any(census.get(k)!=v for k,v in observed.items()):
            raise ValueError('initial_delay_global_census_invalid')
        projection_ref = storage.write_tree(root,(json.loads(b) for b, in db.execute('SELECT body FROM population ORDER BY id')))
        partitions_ref = storage.write_tree(root,_group_rows(db,root))
        cells_ref = storage.write_tree(root,_cell_rows(db,effective_date,algorithm))
        price_pairs = db.execute('SELECT sum(' + '+'.join(f'(p{d} IS NOT NULL)'
            for d in initial.candidate_horizons(algorithm)[1:]) + ') '
            "FROM population WHERE anchor='price_ready'").fetchone()[0] or 0
    positive_n = sum(int(row['value']['anchor_kind']=='price_ready' and (row['value']['delay_sec'] or 0)>0)
                     for row in storage.iter_tree(root,cells_ref))
    blocked = not price_pairs or not source_sha256
    report = EvidenceDocument(dict(schema=initial.REPORT_SCHEMA,storage_schema=STORAGE_SCHEMA,
        analysis_axis='pre_submit_delay',source_date=source_date,publication_date=publication_date,effective_date=effective_date,
        source_sha256=source_sha256,code_contract_sha256=code_contract_sha256,
        source_projection_contract_sha256=_projection_contract or initial.projection_contract(),source_receipt=source_receipt,
        algorithm=algorithm,mapping_version=_mapping_version or initial.MAPPING_VERSION,
        status='blocked' if blocked else 'initial_timing_policy_selected' if positive_n else 'initial_baseline_immediate',
        census=census,price_ready_pair_n=price_pairs,partitions_ref=partitions_ref,cells_ref=cells_ref,
        qualified_projection_ref=projection_ref,default_delay_sec=0,runtime_effect=False,actual_order_submitted=False,
        paired_net_ev_delta_pct=None,realized_pnl_krw=None,metric_role='initial_entry_price_timing_estimate',
        decision_authority='next_preopen_initial_pre_submit_timing_policy',
        primary_decision_metric='mean_paired_price_improvement_bp'),root)
    policy = EvidenceDocument({k:report[k] for k in ('storage_schema','source_date','publication_date','source_sha256',
        'code_contract_sha256','algorithm','mapping_version','cells_ref','default_delay_sec',
        'metric_role','decision_authority','primary_decision_metric')},root)
    policy.update(schema=initial.POLICY_SCHEMA,policy_kind='initial_paired_quote_timing',effective_from=effective_date,
        expires_on=effective_date,supported_anchor_kind='price_ready',selection_status=report['status'],
        runtime_apply_allowed=not blocked,report_sha256=initial.digest(report))
    policy['policy_sha256'] = initial.digest(policy)
    report['policy_sha256'] = policy['policy_sha256']
    return report,policy


def validate(policy, report, *, target_date=None):
    if (report.get('storage_schema')!=STORAGE_SCHEMA or policy.get('storage_schema')!=STORAGE_SCHEMA
            or policy.get('policy_sha256')!=initial.digest({k:v for k,v in policy.items() if k!='policy_sha256'})
            or report.get('policy_sha256')!=policy.get('policy_sha256')
            or policy.get('report_sha256')!=initial.digest({k:v for k,v in report.items() if k!='policy_sha256'})
            or policy.get('runtime_apply_allowed') is not True or report.get('price_ready_pair_n',0)<1
            or policy.get('cells_ref')!=report.get('cells_ref') or policy.get('default_delay_sec')!=0
            or report.get('schema')!=initial.REPORT_SCHEMA or policy.get('schema')!=initial.POLICY_SCHEMA
            or policy.get('algorithm') not in initial.ALGORITHMS
            or policy.get('algorithm')!=report.get('algorithm')):
        raise ValueError('initial_delay_sharded_contract_invalid')
    root = getattr(report,'evidence_root',None)
    if root is None or getattr(policy,'evidence_root',None)!=root:
        raise ValueError('initial_delay_evidence_location_unverified')
    for key in ('source_sha256','code_contract_sha256'):
        value=policy.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('initial_delay_generation_invalid')
    if target_date and not policy['effective_from']<=target_date<=policy['expires_on']:
        raise ValueError('initial_delay_date_invalid')
    from src.engine.infrastructure.startup_validation_code_context import validate_preparation_delay_selection
    if validate_preparation_delay_selection(policy,report,target_date=target_date):
        return
    # Rebuild from the frozen *whole* population. Shard-local winners or split
    # labels never authorize a policy. Verifier scratch is removed on exit.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='.verify-',dir=root) as scratch:
        rebuilt_report,rebuilt_policy = build(storage.iter_tree(root,report['qualified_projection_ref']),
            report['census'],output_root=scratch,source_date=report['source_date'],
            publication_date=report['publication_date'],effective_date=report['effective_date'],
            source_sha256=report['source_sha256'],code_contract_sha256=report['code_contract_sha256'],
            source_receipt=report.get('source_receipt'),_algorithm=report['algorithm'],
            _projection_contract=initial.frozen_projection_contract(report),
            _mapping_version=report.get('mapping_version'))
        # Physical layout belongs to its own verified generation. Selection and
        # split must match by canonical semantic digests, independently of it.
        for key in ('qualified_projection_ref','partitions_ref','cells_ref'):
            if report[key]['logical_sha256']!=rebuilt_report[key]['logical_sha256']:
                raise ValueError('initial_delay_deterministic_selection_invalid')
            for _ in storage.iter_tree(root,report[key]): pass
        if any(report.get(k)!=rebuilt_report.get(k) for k in ('status','price_ready_pair_n','census','source_date',
                'publication_date','effective_date','source_sha256','algorithm','mapping_version',
                'source_projection_contract_sha256')):
            raise ValueError('initial_delay_deterministic_selection_invalid')
        if set(policy)!=set(rebuilt_policy) or any(policy.get(k)!=rebuilt_policy.get(k) for k in policy if k not in {'cells_ref','report_sha256','policy_sha256'}):
            raise ValueError('initial_delay_deterministic_selection_invalid')


def copy_evidence(report, destination):
    """Pin and copy only referenced immutable nodes/leaves, never raw ledgers."""
    root = report.evidence_root
    def copy(reference,depth=0):
        if depth>16: raise ValueError('research_tree_depth_invalid')
        source_path = storage.safe_path(root,reference['path'])
        generation = byte_generation(source_path)
        if generation['sha256']!=reference['sha256'] or generation['size']!=reference['size']:
            raise ValueError('research_shard_generation_changed')
        value=json.loads(source_path.read_bytes())
        target=storage.safe_path(destination,reference['path'])
        initial._atomic(target,value)
        if byte_generation(source_path)!=generation:
            raise ValueError('research_shard_generation_changed')
        for child in value.get('children',[]): copy(child,depth+1)
        for row in value.get('rows',[]):
            if 'membership' in row: copy(row['membership'],depth+1)
    for key in ('qualified_projection_ref','partitions_ref','cells_ref'): copy(report[key])


def run(root, output, day, *, publication_date, effective_date, require_ledger, dry_run,
        contract, cached=None):
    import tempfile
    root,output=Path(root).resolve(),Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    from src.engine.lifecycle.research_disk_budget import use
    # Canonical input == output is the normal dispatcher path. Only this
    # family's durable generations and private scratch belong to its output
    # budget; unrelated raw sources and their aliases are not research output.
    family_output=output/'report/pre_submit_delay_tuning'
    family_output.mkdir(parents=True,exist_ok=True)
    with use(family_output) as disk,tempfile.TemporaryDirectory(prefix='.delay-research-',dir=family_output) as scratch:
        disk.include(output/'threshold_cycle/pre_submit_delay_policy')
        if cached is not None:
            saved,projection=cached
            report,policy=build(projection,saved['census'],output_root=scratch,source_date=day,
                publication_date=publication_date,effective_date=effective_date,source_sha256=saved['source_sha256'],
                code_contract_sha256=contract,source_receipt=saved['source_receipt'])
            decode_passes=0
            def verify():
                initial.verify_source(root,saved)
                if initial.code_contract()!=contract: raise ValueError('delay_code_changed_during_research')
            finish(output,day,report,policy,verify,dry_run)
        else:
            with source(root,day,Path(scratch)/'source',checkpoint_root=family_output/'.source-scan-cache') as snapshot:
                with storage.index(Path(scratch)/'projection') as db:
                    db.execute('CREATE TABLE matched (day TEXT,id TEXT,PRIMARY KEY(day,id)) WITHOUT ROWID')
                    ledger_generations,isolated={},{}
                    if require_ledger:
                        for date in snapshot.source['source_dates']:
                            issues=owner.family_source_ledger_issues(root,date,source_snapshot=snapshot)
                            if issues:
                                isolated[date]=issues;continue
                            path=owner.family_source_ledger_path(root,date)
                            before=byte_generation(path)
                            if before['size']>4*1024*1024: raise ValueError('delay_ledger_partition_required')
                            ledger=json.loads(path.read_bytes())
                            if byte_generation(path)!=before: raise ValueError('delay_family_ledger_changed_during_read')
                            ledger_generations[date]=before
                            identities=(storage.iter_tree(path.parent,ledger['matched_event_ids_ref'])
                                if ledger.get('schema')=='pre_submit_delay_family_source_ledger_v2'
                                else iter(ledger['matched_event_ids']))
                            for identity in identities:
                                db.execute('INSERT OR IGNORE INTO matched VALUES (?,?)',(date,identity))
                    def qualified_source():
                        for row in snapshot.rows:
                            if not require_ledger or db.execute('SELECT 1 FROM matched WHERE day=? AND id=?',
                                (row['emitted_date'],row['execution_source_event_sha256'])).fetchone():
                                yield row
                    from . import pre_submit_delay_situation_projection as situations
                    situation_receipt=situations.prepare(qualified_source(),db,root)
                    census=project(situations.enrich(qualified_source(),db,situation_receipt),db)
                    receipt=dict(schema='pre_submit_delay_input_generation_v1',through_date=day,
                        partition_generations=snapshot.source['partition_generations'],
                        ledger_generations=ledger_generations,isolated_dates=isolated,
                        native_situation_projection=situation_receipt)
                    report,policy=build((row for _,row,_ in storage.records(db)),census,
                        output_root=scratch,source_date=day,publication_date=publication_date,effective_date=effective_date,
                        source_sha256=snapshot.source['sha256'],code_contract_sha256=contract,source_receipt=receipt)
                    report['source_scan_census']={k:snapshot.source[k] for k in ('raw_event_count','isolated_records',
                        'conflicted_records','scan_jobs','bytes_read')}
                    # The scan census is diagnostic and part of the report seal.
                    policy['report_sha256']=initial.digest({k:v for k,v in report.items() if k!='policy_sha256'})
                    policy['policy_sha256']=initial.digest({k:v for k,v in policy.items() if k!='policy_sha256'})
                    report['policy_sha256']=policy['policy_sha256']
                    def verify():
                        snapshot.verify(day,root)
                        initial.verify_source(root,report)
                        if initial.code_contract()!=contract: raise ValueError('delay_code_changed_during_research')
                    finish(output,day,report,policy,verify,dry_run)
                    decode_passes=1
        return {**owner.initial_policy_projection(report),'source_decode_passes':decode_passes,
                'minimal_projection_reused':cached is not None,'storage_schema':STORAGE_SCHEMA}


def finish(output, day, report, policy, verify, dry_run):
    verify()
    if dry_run: return
    if policy['runtime_apply_allowed']:
        pointer=Path(output)/'threshold_cycle/pre_submit_delay_policy'/f'committed_{day}.json'
        incumbent=initial.committed_paths(output,day,validate_selection=False)[3]['manifest_sha256'] if pointer.exists() else None
        initial.publish(output,report,policy,expected_incumbent=incumbent,source_verifier=verify)
    else:
        # A blocked root still retains its full census without activating it.
        base=Path(output)/'report/pre_submit_delay_tuning'/f'blocked-{day}-{initial.digest(report)}'
        copy_evidence(report,base)
        initial._atomic(base/'report.json',report)
