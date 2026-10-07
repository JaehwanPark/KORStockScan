"""Main postclose adapter for the common offline comparison store.

Frozen v3/v4 strategy modules remain byte-identical. Only storage, preparation
reuse and offline reservation change; the primary, labels and raw PASS ranking
remain native. Live AI and order ledgers are not consumers of this module.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import concurrent.futures
import copy
from fractions import Fraction
import gzip
import itertools
import json
import math
import os
from pathlib import Path
import time
import tempfile

from src.engine.ai import offline_comparison_store as S
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_auxiliary_contract as V1


def enabled(data_root):
    path = S.store_root(data_root) / 'current.json'
    if not path.exists():
        return False
    with S.Store(data_root, readonly=True) as store:
        store.activation()
    return True


class Adapter:
    def __init__(self, backend):
        self.backend = backend

    def __getattr__(self, name):
        return getattr(self.backend, name)

    def prepare_inputs(self, data_root, day, machine):
        return prepare_inputs(self.backend, data_root, day, machine)

    def calls(self, data_root, day, **kwargs):
        return calls(self.backend, data_root, day, **kwargs)

    def auxiliary_report(self, data_root, day, publication, parent_bundle, **kwargs):
        return auxiliary_report(self.backend, data_root, day, publication, parent_bundle, **kwargs)


def adapt(backend, data_root):
    return Adapter(backend) if enabled(data_root) else backend


def directory(backend, data_root, day):
    return backend.directory(data_root, day) / 'shared-ledger'


def freeze_receipt(out, origin):
    # This pure custody helper is frozen and does not access a legacy ledger.
    from src.engine.scalping.continuous_reversal_path_postclose import freeze_receipt as freeze
    return freeze(out, origin)


def code_receipts(out, backend):
    import inspect
    modules = (S, __import__(__name__, fromlist=['*']), backend, backend.A, backend.C, K, B, V1)
    return [freeze_receipt(out, Path(inspect.getfile(m))) for m in modules]


def eligible(backend, machine, population):
    if hasattr(backend, 'eligible_population_points'):
        yield from backend.eligible_population_points(machine, population)
        return
    # Frozen v3 compares only selected and applied baseline owners. v4 also
    # compares consumed versions through its native declaration above.
    C, V = backend.C, backend.V3
    winner = {c['key']: c for c in machine['cells']}
    baseline = {c['key']: c for c in machine['baseline_cells']}
    seen = set(machine.get('duplicate_census', {}).get('quarantined_identities', []))
    for point in backend.iter_points(population):
        event = point['event']; identity = point['canonical_id']
        if identity in seen:
            continue
        seen.add(identity)
        if point['outcome']['status'] == 'UNRESOLVED':
            continue
        key = C.cell_key(event['symbol'], event['market'], event['confirmation_price'])
        owners = {}
        for label, cells in [('selected', winner), ('applied_baseline', baseline)]:
            cell = cells[key]['routes'][event['venue']]
            hits = [b['branch_id'] for b in cell['payload']['branches'] if b['branch_id'] in point['branch_hits']]
            if hits:
                owners.setdefault(V.primary(cell, hits), []).append(label)
        for bid, labels in owners.items():
            branch = C.branch(bid)
            yield dict(comparison='|'.join((key, event['venue'], bid, branch.get('definition_sha256', P.digest(C.definition(bid))), branch['decision_phase'])),
                       canonical_id=identity, branch_id=bid, owners=labels, outcome=point['outcome'])


def owner_census(points):
    from src.engine.scalping.continuous_reversal_path_postclose import input_owner_census
    return input_owner_census(points)


def point_components(store, point):
    # Labels do not duplicate the reusable input/event bodies.
    return dict(input=store.put(point['input']), event=store.put(point['event']),
                meta=store.put({k: v for k, v in point.items() if k not in ('input', 'event', 'outcome')}),
                outcome=point['outcome'])


def materialize_point(store, record):
    return dict(store.get(record['meta']), input=store.get(record['input']),
                event=store.get(record['event']), outcome=record['outcome'])


def project_partition(backend, part, declarations, out):
    """Native prefix projection, independently declared owners, no provider IO."""
    from src.engine.scalping.continuous_reversal_path_postclose import grouped_partition_points
    C = backend.C
    rec = part['normalized_source']
    if P.file_hash(rec['path']) != rec['sha256']:
        raise ValueError('shared_input_source_changed')
    raw = json.loads(gzip.decompress(Path(rec['path']).read_bytes()))['symbols']
    features = {}
    seen = set()
    for point in grouped_partition_points(part, out):
        event = point['event']; identity = point['canonical_id']
        if identity in seen:
            continue
        seen.add(identity)
        wanted = declarations.get(identity, [])
        if not wanted:
            continue
        fk = event['symbol'], event['source_item']
        for declared in wanted:
            bid = declared['branch_id']
            signal = copy.deepcopy(point['confirmed_signals'].get(bid) or point.get('first_signal') or dict(event, decision_phase=B.FIRST))
            if bid in point.get('path_inputs', {}):
                inp = copy.deepcopy(point['path_inputs'][bid])
            else:
                if fk not in features:
                    features.clear()
                    rows = [r[:] for r in raw[event['symbol']]]
                    for r in rows:
                        if r[9] != event['source_item']:
                            r[8] = 0
                    features[fk] = (rows, K.build_features(rows))
                rows, fs = features[fk]; index = point['entry_index']
                values = {k: float(v[index]) if math.isfinite(v[index]) else None for k, v in fs.items()}
                values.update({k: signal[k] for k in K.INPUT_FEATURES[4:]})
                signal['entry_index'] = index
                inp = K.make_input(signal, rows, values)
            yield dict(declared, event_id=signal['event_id'], event=signal, input=inp,
                       phase=C.branch(bid)['decision_phase'])


def import_responses(store, backend, data_root, day, machine):
    paths = {str(p): None for p in P.result_paths(data_root, day) + sorted((Path(data_root) / 'report/continuous_reversal_v2').glob('????-??-??/provider-results.jsonl'))}
    for cell in machine['baseline_auxiliary_cells']:
        for route in cell['routes'].values():
            for policy in route['payload']['branch_policies'].values():
                refs = policy.get('actual_response_evidence') or []
                for ref in [refs] if isinstance(refs, dict) else refs:
                    paths[ref['path']] = ref['sha256']
    imported = 0
    for name, required_hash in sorted(paths.items()):
        path = Path(name)
        h = P.file_hash(path)
        if required_hash and required_hash != h:
            raise ValueError('shared_actual_export_changed')
        ck = 'response-import:' + h
        if store.checkpoint(ck):
            continue
        opener = gzip.open if path.suffix == '.gz' else open
        with opener(path, 'rt') as f:
            for line in f:
                row = json.loads(line); req = row.get('request'); result = row.get('result') or {}
                response = result.get('provider_provenance', {}).get('response_id')
                if not req or not response:
                    continue
                try:
                    d, venue, session, symbol, epoch, sequence = req['paired_replay_parent_id'].split(':')
                    inp = req['candidate_input']; phase = inp['observation_phase']['stage']
                    canonical = P.digest([d, symbol, K.market_bucket(session), venue, inp['source_item'], int(epoch), int(sequence)])
                    body = {k: req[k] for k in ('candidate_input', 'candidate', 'control', 'stage')}
                    req = dict(req, paired_replay_id=P.digest([canonical, phase, body]))
                    errors = backend.A.validate_response(result['candidate_response'], inp, arm=req['micro_reversion_replay_arm'], phase=phase)
                except (KeyError, TypeError, ValueError):
                    continue
                rid, _ = store.add_request(req)
                record = dict(result=result, validation_errors=errors, source_record_path=str(path.resolve()), source_record_sha256=h)
                obj = store.put(record)
                attempt = S.digest(['provider', req['control'], req['paired_replay_id'], response])
                old = store.db.execute('SELECT result_obj FROM attempts WHERE attempt=?', (attempt,)).fetchone()
                if old and store.get(old[0]).get('result') != result:
                    raise ValueError('shared_actual_response_conflict')
                store.db.execute('INSERT OR IGNORE INTO attempts VALUES(?,?,?,?,?,?,?)', (attempt, rid, 'completed', obj, None, 0, 'import:' + h))
                store.db.execute("UPDATE requests SET state='completed',result_obj=coalesce(result_obj,?) WHERE id=?", (obj, rid))
                imported += 1
        store.checkpoint(ck, dict(path=str(path), sha256=h))
        store.commit()
    return imported


def prepare_inputs(backend, data_root, day, machine):
    if machine['artifact_content_sha256'] != P.seal(machine)['artifact_content_sha256']:
        raise ValueError('shared_machine_report_changed')
    out = directory(backend, data_root, day)
    (out / 'frozen').mkdir(parents=True, exist_ok=True)
    population = json.loads(Path(machine['population_path']).read_text())
    if population['artifact_content_sha256'] != P.seal(population)['artifact_content_sha256']:
        raise ValueError('shared_population_hash_changed')
    declarations = defaultdict(list)
    for value in eligible(backend, machine, population):
        declarations[value['canonical_id']].append(value)
    expected = owner_census(v for rows in declarations.values() for v in rows)
    gen = machine['artifact_content_sha256']
    receipts = code_receipts(out, backend)
    universe = P.seal(dict(schema=backend.SCHEMA, machine_report_sha256=gen,
                          population_sha256=P.file_hash(machine['population_path']),
                          **expected, **P.AUTH))
    P.write(out / 'frozen' / ('universe-' + gen + '.json'), universe)
    groups = defaultdict(list)
    count = 0
    seen = set()
    input_file = out / 'frozen' / ('inputs-' + gen + '.jsonl.gz')
    tmp = input_file.with_suffix('.partial')
    input_contract = P.digest([(r['sha256']) for r in receipts])
    request_contract = P.digest([P.file_hash(backend.A.__file__), P.file_hash(backend.__file__)])
    with S.Store(data_root) as store:
        store.activation()
        imported = import_responses(store, backend, data_root, day, machine)
        old_members = {(r[0], r[1], r[2]): (r[6], r[7]) for r in store.owners(gen)}
        with tmp.open('wb') as raw_out, gzip.GzipFile(filename='', mode='wb', fileobj=raw_out, mtime=0) as gz:
            for part in population['partitions']:
                if P.file_hash(part['path']) != part['sha256']:
                    raise ValueError('shared_population_partition_changed')
                part_ids = set()
                with gzip.open(part['path'], 'rt') as f:
                    for line in f:
                        part_ids.add(json.loads(line)['canonical_id'])
                local = {i: declarations[i] for i in sorted(part_ids - seen) if i in declarations}
                seen.update(part_ids)
                rec = part['normalized_source']
                if P.file_hash(rec['path']) != rec['sha256']:
                    raise ValueError('shared_normalized_source_changed')
                # The point partition binds labels and all native lookback/
                # lookahead dependencies; no metadata-only validity shortcut.
                cache_key = 'input-partition:' + P.digest([part['sha256'], rec['sha256'], local, input_contract])
                cached = store.checkpoint(cache_key)
                if cached:
                    points = ((materialize_point(store, r), r) for r in cached['points'])
                else:
                    points = ((p, None) for p in project_partition(backend, part, local, out))
                records = []
                for point, cached_record in points:
                    record = cached_record or point_components(store, point)
                    # Labels and comparison ownership do not invalidate the
                    # exact arm transmission. Pin the actual serializer code.
                    request_cache = 'request-binding:' + P.digest([record['input'], record['event'], point['phase'], request_contract])
                    request_refs = record.setdefault('requests', store.checkpoint(request_cache) or {})
                    records.append(record)
                    # A compact owner/input-reference file replaces full input
                    # exports. Only the adapter materializes the immutable body.
                    small = {k: point[k] for k in ('comparison', 'canonical_id', 'branch_id', 'owners', 'outcome')}
                    small['objects'] = {k: record[k] for k in ('input', 'event', 'meta')}
                    gz.write(S.encode(small) + b'\n')
                    count += 1
                    for arm in V1.ARMS:
                        if arm in request_refs:
                            rid = request_refs[arm]
                        else:
                            req = backend.request(point, arm)
                            priority = 3 if 'selected' in point['owners'] and not point['branch_id'].startswith('legacy_') else 2 if 'selected' in point['owners'] else 1
                            rid, _ = store.add_request(req, priority=priority)
                            request_refs[arm] = rid
                        existing = old_members.get((point['comparison'], point['canonical_id'], arm))
                        if existing:
                            if existing[0] != rid:
                                raise ValueError('shared_existing_owner_identity_changed')
                            mid = existing[1]
                        else:
                            mid = store.add_member(point['comparison'], point['canonical_id'], arm, rid, point['outcome']['status'])
                        event = point['event']
                        group = json.dumps([point['comparison'], str(point['event_id']).split(':')[0], event['symbol']], separators=(',', ':'))
                        groups[group].append(mid)
                    if store.checkpoint(request_cache) is None:
                        store.checkpoint(request_cache, request_refs)
                    if count % 1000 == 0:
                        store.commit()
                if not cached:
                    store.checkpoint(cache_key, dict(points=records, source=rec, partition_sha256=part['sha256']))
                store.commit()
            gz.close()
            raw_out.flush()
            os.fsync(raw_out.fileno())
        with gzip.open(tmp, 'rt') as f:
            actual = owner_census(json.loads(line) for line in f)
        if actual != expected:
            raise ValueError('shared_expected_population_input_mismatch')
        desc = dict(machine_report_sha256=gen, expected=expected, universe_sha256=universe['artifact_content_sha256'])
        old = store.db.execute('SELECT descriptor_obj FROM generations WHERE generation=?', (gen,)).fetchone()
        store.bind_generation(gen, groups, store.get(old[0]) if old else desc, expected['expected_requests'])
        states = store.states(gen)
        store.commit()
        if input_file.exists():
            if S.file_hash(input_file) != S.file_hash(tmp):
                raise ValueError('shared_frozen_input_changed')
            tmp.unlink()
        else:
            os.replace(tmp, input_file)
        manifest = P.seal(dict(schema=backend.SCHEMA, machine_report_sha256=gen,
                              input_sha256=P.file_hash(input_file), universe_sha256=universe['artifact_content_sha256'], **expected, **P.AUTH))
        P.write(out / 'frozen' / ('expected-' + gen + '.json'), manifest)
        census = dict(eligible_points=count, eligible_requests=5 * count, expected_owner_requests=5 * count,
                      imported_exact_responses=imported, **states)
        result = P.seal(dict(schema=backend.SCHEMA, source_date=day, machine_report_sha256=gen,
                            input_path=str(input_file.resolve()), input_sha256=P.file_hash(input_file),
                            input_generation_sha256=input_contract, source_receipts=receipts,
                            expected_manifest_sha256=manifest['artifact_content_sha256'], census=census,
                            call_limit=None, status='prepared', storage_schema=S.FORMAT, **P.AUTH))
        P.write(out / 'input-census.json', result)
        return result


def calls(backend, data_root, day, *, stop_epoch=None, workers=4, transport=None):
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ValueError('shared_provider_concurrency_invalid')
    if transport is None:
        from src.engine.scalping.ai_decision_quality import execute_openai_prompt_v2_candidate
        transport = execute_openai_prompt_v2_candidate
    out = directory(backend, data_root, day)
    census, _, _ = validate_census(out)
    gen = census['machine_report_sha256']
    count = 0
    with S.Store(data_root) as store:
        store.reconcile()
        fence = store.activation()['writer_epoch']
        queue = store.pending(gen)
        def send(req, attempt):
            if store.activation()['writer_epoch'] != fence:
                record = dict(error_type='writer_fenced_before_send', validation_errors=['provider_not_sent'], transport_invoked=False)
                store.land_response(attempt, record)
                return record
            try:
                result = transport(req, timeout_sec=30)
                phase = req['candidate_input'].get('observation_phase', {}).get('stage', B.FIRST)
                try:
                    errors = backend.A.validate_response(result['candidate_response'], req['candidate_input'], arm=req['micro_reversion_replay_arm'], phase=phase)
                except (KeyError, TypeError, ValueError):
                    errors = ['response_validation_failed']
                record = dict(result=result, validation_errors=errors, transport_invoked=True)
            except Exception as exc:
                record = dict(error_type=type(exc).__name__, validation_errors=['provider_attempt_uncertain'], transport_invoked=True)
            store.land_response(attempt, record)
            return record
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            running = {}
            exhausted = False
            while True:
                while not exhausted and len(running) < workers and (stop_epoch is None or time.time() < stop_epoch):
                    row = queue.fetchone()
                    if row is None:
                        exhausted = True
                        break
                    req = store.request(row[0])  # validate materialization before reservation
                    attempt = store.reserve(row[0], fence)
                    running[pool.submit(send, req, attempt)] = attempt
                if not running:
                    break
                done, _ = concurrent.futures.wait(running, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    record = future.result()
                    store.finish(running.pop(future), record)
                    count += bool(record.get('transport_invoked'))
        queue.close()
        states = store.states(gen)
        uncertain = store.db.execute('''SELECT count(*) FROM attempts a WHERE a.state='reserved' AND a.request_id IN
          (SELECT m.request_id FROM generation_parts gp JOIN partition_members pm ON pm.partition_id=gp.partition_id
          JOIN members m ON m.id=pm.member_id WHERE gp.generation=?)''', (gen,)).fetchone()[0]
        result = P.seal(dict(schema=backend.SCHEMA, source_date=day,
                            status='evaluation_incomplete' if any(states.get(k) for k in ('planned', 'reserved', 'failed')) else 'completed',
                            new_calls=count, census=states, call_limit=None,
                            census_unit='unique_requests', uncertain_attempts_require_reconciliation=uncertain, **P.AUTH))
        P.write(out / 'call-completion.json', result)
        return result


def validate_census(out):
    census = json.loads((out / 'input-census.json').read_text())
    gen = census['machine_report_sha256']
    manifest = json.loads((out / 'frozen' / ('expected-' + gen + '.json')).read_text())
    universe = json.loads((out / 'frozen' / ('universe-' + gen + '.json')).read_text())
    if (any(v['artifact_content_sha256'] != P.seal(v)['artifact_content_sha256'] for v in (census, manifest, universe))
            or census['expected_manifest_sha256'] != manifest['artifact_content_sha256']
            or manifest['universe_sha256'] != universe['artifact_content_sha256']
            or manifest['machine_report_sha256'] != gen or universe['machine_report_sha256'] != gen
            or P.file_hash(census['input_path']) != census['input_sha256']
            or manifest['input_sha256'] != census['input_sha256']):
        raise ValueError('shared_expected_census_changed')
    with gzip.open(census['input_path'], 'rt') as f:
        actual = owner_census(json.loads(line) for line in f)
    if any(actual[k] != manifest[k] or actual[k] != universe[k] for k in actual):
        raise ValueError('shared_expected_population_incomplete')
    return census, manifest, universe


def comparison_metrics(store, backend, snapshot):
    """Immutable response-selection/label partitions, replace-on-change totals."""
    metrics = defaultdict(lambda: {a: Counter() for a in V1.ARMS})
    gaps = Counter(); expected = Counter(); states = Counter()
    validator = P.file_hash(backend.A.__file__)
    for partition, obj in snapshot['partitions'].items():
        key = 'metrics:' + S.digest([obj, validator])
        cached = store.checkpoint(key)
        if cached is None:
            store.db.execute('CREATE TEMP TABLE IF NOT EXISTS selected_members(mid INTEGER PRIMARY KEY,state TEXT,result_obj INTEGER)')
            store.db.execute('DELETE FROM selected_members')
            store.db.executemany('INSERT INTO selected_members VALUES(?,?,?)', store.get(obj))
            rows = store.db.execute('''SELECT c.value,o.value,a.value,m.outcome,s.state,s.result_obj,m.request_id
              FROM selected_members s JOIN members m ON m.id=s.mid
              JOIN strings c ON c.id=m.comparison JOIN strings o ON o.id=m.opportunity
              JOIN strings a ON a.id=m.arm ORDER BY c.value,o.value,a.value''')
            pm = defaultdict(lambda: {a: Counter() for a in V1.ARMS}); pg = Counter(); pe = Counter(); ps = Counter(); validations = []
            for (comparison, opportunity), values in itertools.groupby(rows, key=lambda r: r[:2]):
                records = list(values)
                pe[comparison] += 1
                ps.update(r[4] for r in records)
                arms = {r[2]: r for r in records}
                if len(records) != 5 or set(arms) != set(V1.ARMS) or any(r[4] != 'completed' or not r[5] for r in records):
                    pg[comparison] += 1
                    continue
                for arm, row in arms.items():
                    result = store.get(row[5]); req = store.request(row[6]); inp = req['candidate_input']
                    phase = inp.get('observation_phase', {}).get('stage', B.FIRST)
                    validation_id = S.digest([row[5], S.digest(inp), validator, arm, phase])
                    prior = store.db.execute('SELECT result_obj FROM validations WHERE identity=?', (validation_id,)).fetchone()
                    if prior:
                        validation_obj = prior[0]
                        errors = store.get(validation_obj)['errors']
                    else:
                        try:
                            errors = backend.A.validate_response(result['result']['candidate_response'], inp, arm=arm, phase=phase)
                        except (KeyError, TypeError, ValueError):
                            errors = ['response_validation_failed']
                        validation_obj = store.put(dict(response_obj=row[5], input_sha256=S.digest(inp), validator_sha256=validator,
                                                        arm=arm, phase=phase, errors=errors))
                        store.db.execute('INSERT INTO validations VALUES(?,?)', (validation_id, validation_obj))
                    validations.append(validation_obj)
                    m = pm[comparison][arm]; m['points'] += 1; m['invalid_responses'] += bool(errors)
                    if result.get('result', {}).get('candidate_response', {}).get('risk_verdict') == 'PASS':
                        m['pass_count'] += 1; m['pass_wins'] += row[3] == 'WIN'
            cached = dict(metrics=pm, gaps=pg, expected=pe, states=ps, validator_sha256=validator, validations=validations)
            store.checkpoint(key, cached)
        for comparison, arms in cached['metrics'].items():
            for arm, counts in arms.items():
                metrics[comparison][arm].update(counts)
        gaps.update(cached['gaps']); expected.update(cached['expected']); states.update(cached['states'])
    return metrics, gaps, expected, dict(states)


def response_evidence(store, out, snapshot):
    """One hash-addressed compatibility export of chosen actual responses."""
    key = 'actual-export:' + snapshot['snapshot_sha256']
    old = store.checkpoint(key)
    if old and P.file_hash(old['path']) == old['sha256']:
        return Path(old['path'])
    selected = set()
    for obj in snapshot['partitions'].values():
        for mid, state, result in store.get(obj):
            if state == 'completed' and result:
                rid = store.db.execute('SELECT request_id FROM members WHERE id=?', (mid,)).fetchone()[0]
                selected.add((rid, result))
    fd, name = tempfile.mkstemp(prefix='.actual-', suffix='.jsonl.gz', dir=out / 'frozen')
    os.close(fd); tmp = Path(name)
    try:
        with tmp.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as handle:
            for rid, result in sorted(selected):
                req = store.request(rid)
                handle.write(S.encode(dict(request_identity=req['paired_replay_id'], request=req, **store.get(result))) + b'\n')
        with tmp.open('rb') as raw:
            os.fsync(raw.fileno())
        # Global exports are shared across report dates/generations.
        target = store.root / 'exports' / (P.file_hash(tmp) + '.jsonl.gz')
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if P.file_hash(target) != P.file_hash(tmp):
                raise ValueError('shared_actual_export_hash_changed')
            tmp.unlink()
        else:
            os.replace(tmp, target)
            S.fsync_directory(target.parent)
        store.checkpoint(key, dict(path=str(target.resolve()), sha256=P.file_hash(target)))
        return target
    finally:
        tmp.unlink(missing_ok=True)


def auxiliary_report(backend, data_root, day, publication, parent_bundle, *, publish_policy=True):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    C, A, V3, SCHEMA = backend.C, backend.A, backend.V3, backend.SCHEMA
    out = directory(backend, data_root, day)
    machine = json.loads((backend.directory(data_root, day) / 'machine-comparison.json').read_text())
    gen = machine['artifact_content_sha256']
    if gen != P.seal(machine)['artifact_content_sha256']:
        raise ValueError('shared_machine_report_changed')
    baseline = {c['key']: c for c in machine['baseline_cells']}
    oldaux = {c['key']: c for c in machine['baseline_auxiliary_cells']}
    quality, quality_path = backend.source_quality(data_root, day, json.loads(Path(machine['population_path']).read_text()))
    input_census, expected_manifest, universe = validate_census(out)
    if input_census['machine_report_sha256'] != gen:
        raise ValueError('shared_machine_input_generation_changed')
    declared = Counter(expected_manifest['comparisons'])
    with S.Store(data_root) as store:
        store.activation(); store.reconcile()
        snapshot = store.snapshot(gen)
        metrics, gaps, expected, owner_states = comparison_metrics(store, backend, snapshot)
        missing_owner_requests = expected_manifest['expected_requests'] - sum(owner_states.values())
        if missing_owner_requests < 0 or any(expected[c] > declared[c] for c in expected):
            raise ValueError('shared_unexpected_owner_requests')
        for comparison, count in declared.items():
            gaps[comparison] += count - expected[comparison]
        gaps = +gaps; expected = declared
        evidence = response_evidence(store, out, snapshot)
        # Mutable queue/WAL paths never enter a published source hash.
        validation_parts = [store.checkpoint('metrics:' + S.digest([obj, P.file_hash(backend.A.__file__)]))
                            for obj in snapshot['partitions'].values()]
        revision = dict(snapshot, validation_partitions=validation_parts,
                        label_contract=machine['label_contract'], primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS')
        snapshot_path = out / 'frozen' / ('comparison-' + S.digest(revision) + '.json')
        S.atomic_json(snapshot_path, revision)
        input_census = dict(input_census, source_receipts=input_census['source_receipts'] + [
            dict(path=str(snapshot_path.resolve()), sha256=P.file_hash(snapshot_path))])
    proof=dict(path=str(evidence.resolve()),sha256=P.file_hash(evidence));published=[];acs=[];pending=[];regular_aux={};regular_machine={}
    for mc in machine['cells']:
        key=mc['key'];published_cell=dict(key=key,routes={});aux_cell=dict(key=key,routes={})
        for route,cell in mc['routes'].items():
            policies={};not_ready=[]
            regular=key.replace('|PRE|','|REGULAR|').replace('|AFTER|','|REGULAR|')
            inherited=(cell.get('local_metrics') is None and regular!=key
                       and cell.get('carry_source',{}).get('cell_key')==regular
                       and regular_machine.get((regular,route),{}).get('payload_sha256')==cell['payload_sha256'])
            for b in cell['payload']['branches']:
                bid=b['branch_id'];comparison='|'.join((key,route,bid,b.get('definition_sha256',P.digest(C.definition(bid))),b['decision_phase']))
                old=oldaux[key]['routes'][route]['payload']['branch_policies'].get(bid)
                if inherited:
                    old=regular_aux[regular,route]['branch_policies'].get(bid)
                    if old:
                        old=copy.deepcopy(old);old['local_metrics']=None
                        old['carry_source']=dict(comparison_report_sha256=gen,cell_key=regular,
                                                branch_id=bid,binding_sha256=P.digest(old['binding']),reason='no_sample_compatible_regular_selected')
                eligible=[a for a in V1.TIE_ORDER if metrics[comparison][a]['pass_count']]
                # No partial comparison is allowed to masquerade as a winner.
                if expected[comparison] and not gaps[comparison] and eligible:
                    arm=max(eligible,key=lambda a:(Fraction(metrics[comparison][a]['pass_wins'],metrics[comparison][a]['pass_count']),bool(old and old['arm']==a)))
                    policies[bid]=dict(arm=arm,binding=A.binding(b['decision_phase'],arm),local_metrics=dict(metrics[comparison][arm]),
                                       actual_response_evidence=[proof],comparison_key=comparison,candidates={a:dict(m) for a,m in metrics[comparison].items()})
                elif old:
                    policies[bid]=copy.deepcopy(old)
                else:not_ready.append(bid)
            if not_ready:
                pending.append(dict(cell_key=key,route=route,status='machine_selected_auxiliary_pending',branches=not_ready,comparison_gaps={b:gaps.get('|'.join((key,route,b,C.branch(b).get('definition_sha256',P.digest(C.definition(b))),C.branch(b)['decision_phase'])),0) for b in not_ready}))
                selected=copy.deepcopy(baseline[key]['routes'][route]);ap=copy.deepcopy(oldaux[key]['routes'][route]['payload'])
                selected['status']='carry_machine_selected_auxiliary_pending'
            else:
                selected=copy.deepcopy(cell);selected['status']='selected' if cell['local_metrics'] else 'carry'
                ap=dict(branch_policies=policies)
            selected.pop('candidates',None)
            selected['comparison_report_sha256']=gen
            published_cell['routes'][route]=selected
            aux_cell['routes'][route]=dict(payload=ap,payload_sha256=P.digest(ap),status='carry' if not_ready else 'selected_or_verified_carry')
            if '|REGULAR|' in key:
                regular_aux[key,route]=ap;regular_machine[key,route]=selected
        published.append(published_cell);acs.append(aux_cell)
    # The comparison report remains intact; issued reports explicitly separate
    # machine winners from the deployable machine+auxiliary pairs.
    comparison_path=out/'frozen'/('machine-comparison-'+gen+'.json')
    P.write(comparison_path,machine)
    input_receipts=[freeze_receipt(out,origin) for origin in (
        out/'input-census.json',out/'frozen'/('universe-'+gen+'.json'),
        out/'frozen'/('expected-'+gen+'.json'))]
    issued=P.seal(dict(machine,cells=published,comparison_report_sha256=gen,
                       source_receipts=machine['source_receipts']+input_census['source_receipts']+[
                           dict(path=str(comparison_path.resolve()),sha256=P.file_hash(comparison_path)),
                           dict(path=str(quality_path.resolve()),sha256=P.file_hash(quality_path))]+input_receipts,
                       source_row_exclusions=quality['totals'],
                       status='completed_with_scope_carry' if pending else 'completed',scope_pending=pending))
    auxiliary=P.seal(dict(schema=SCHEMA,source_date=day,target_date=day,publication_date=publication,
        status='completed_with_scope_carry' if pending else 'completed',cells=acs,machine_report_sha256=issued['artifact_content_sha256'],
        results_sources=[proof],source_receipts=[],scope_pending=pending,comparison_complete=not bool(gaps),
        owner_request_census=dict(expected=expected_manifest['expected_requests'],missing=missing_owner_requests,reconciled=not missing_owner_requests,**owner_states),
        comparison_statuses={c:'evaluation_incomplete' if gaps[c] else 'completed' if any(metrics[c][a]['pass_count'] for a in V1.ARMS) else 'completed_no_pass' for c in declared},
        eligible_comparisons=dict(expected),incomplete_comparisons=dict(gaps),primary_metric='actual_raw_PASS_wins_over_all_actual_raw_PASS',
        call_limit=None,validity_adjustment_in_rank=False,**P.AUTH))
    P.write(out/'machine.json',issued);P.write(out/'auxiliary.json',auxiliary)
    # Machine-stage bytes remain frozen once its terminal receipt commits.
    # Issued runtime pairs are a separate compiled source bound to that report.
    freeze=P.seal(dict(schema=SCHEMA,source_date=day,status='frozen',machine_report_sha256=gen,
                       call_limit=None,census=input_census['census'],input_sha256=input_census['input_sha256'],**P.AUTH))
    if publish_policy:
        P.write(P.directory(data_root,day)/'auxiliary.json',auxiliary)
        P.write(P.directory(data_root,day)/'call-freeze.json',freeze)
        canonical=P.directory(data_root,day)/'provider-results.jsonl';canonical.parent.mkdir(parents=True,exist_ok=True)
        with gzip.open(evidence,'rt') as src,canonical.open('w') as dst:
            for line in src:dst.write(line)
        import subprocess
        commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bundle=V3.stage(data_root,day,publication,issued,auxiliary,target_date=N.next_target(publication),release_commit=commit)
        P.write(Path(data_root)/'report/ai_entry_setup_paired_replay_batch'/f'compact_auxiliary_paired_economic_{day}.json',P.seal(dict(auxiliary,staged=dict(status='prepared',bundle_sha256=bundle['bundle_sha256'],target_date=bundle['target_date']))))
    return auxiliary
