"""Read-only terminal allocation references for holding research.

The automation report consumer preserves the quantity producer's scope. It
does not make allocated costs exact, change custody, replay an alternative
exit, select policy, or repair unavailable historical AI/quote observations.
"""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import stat
import time

from src.engine.lifecycle import broker_cost_allocation as allocation
from src.engine.lifecycle import broker_cost_source as official
from src.engine.lifecycle import broker_cost_reconciliation as reconciliation
from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.research_input_budget import Claim, LIMIT_BYTES
from src.engine.scalping.pre_submit_delay_initial_policy import digest

SCHEMA = 'main_holding_allocated_cost_diagnostics_v1'
REGISTRATION_SCHEMA = 'main_trailing_followup_registration_v1'
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_NATIVE_BYTES = 4 * 1024 * 1024
MAX_RECORDS = 10000
MAX_FILES = 2048
OUTPUT_NAME = 'holding-allocated-cost-diagnostics.json'
NATIVE_AUDIT_PRODUCER = Path(__file__).parents[1] / 'sniper_trade_review_report.py'


def _path(value):
    path = Path(value).absolute()
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('allocated_diagnostic_symlink')
    return path.resolve()


def _clock(value):
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError('allocated_diagnostic_clock_timezone_missing')
        value = parsed.timestamp()
    if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
        raise ValueError('allocated_diagnostic_clock_invalid')
    return value


class _Reader:
    """Conservative retained-decode claims and a bounded before/after ledger."""
    def __init__(self, claim):
        self.claim, self.sources, self.stats = claim, {}, {}
        self.bytes = Counter()

    @staticmethod
    def stat_key(value):
        return [value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns]

    def read(self, path, *, stage, expected=None, sealed=False):
        path = _path(path)
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_FILE_BYTES:
            raise ValueError('allocated_diagnostic_file_budget')
        if len(self.sources) >= MAX_FILES and str(path) not in self.sources:
            raise ValueError('allocated_diagnostic_file_count')
        self.claim.grow(before.st_size * 8)
        with path.open('rb') as handle:
            raw = handle.read(before.st_size + 1)
        self.bytes[stage] += len(raw)
        if self.stat_key(path.stat()) != self.stat_key(before) or len(raw) != before.st_size:
            raise ValueError('allocated_diagnostic_source_changed')
        ref = dict(path=str(path), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if expected is not None and any(ref[k] != expected.get(k) for k in ('size', 'sha256')):
            raise ValueError('allocated_diagnostic_physical_reference_mismatch')
        prior = self.sources.get(str(path))
        if prior is not None and prior != ref:
            raise ValueError('allocated_diagnostic_source_changed')
        self.sources[str(path)] = ref
        self.stats[str(path)] = self.stat_key(before)
        value = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('allocated_diagnostic_nonfinite_json')))
        if sealed and (not isinstance(value, dict) or value.get('artifact_sha256') !=
                       digest({k: v for k, v in value.items() if k != 'artifact_sha256'})):
            raise ValueError('allocated_diagnostic_seal_invalid')
        return value

    def tree(self, root, reference):
        # Track all bounded carriers before using the native logical-tree reader.
        def pin(ref, depth=0):
            if depth > 16:
                raise ValueError('allocated_diagnostic_tree_depth')
            if ref.get('kind') == 'inline':
                return
            body = self.read(storage.safe_path(root, ref['path']), stage='input_tree', expected=ref)
            self.bytes['native_tree_validation'] += ref['size']
            for child in body.get('children', []):
                pin(child, depth + 1)
        pin(reference)
        for row in storage.iter_tree(root, reference):
            yield row

    def finish(self):
        for ref in self.sources.values():
            path = _path(ref['path'])
            if self.stat_key(path.stat()) != self.stats[str(path)]:
                raise ValueError('allocated_diagnostic_source_changed')
            sha, size = hashlib.sha256(), 0
            with path.open('rb') as handle:
                while True:
                    chunk = handle.read(65536)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > ref['size']:
                        raise ValueError('allocated_diagnostic_source_changed')
                    sha.update(chunk)
            self.bytes['final_source_verification'] += size
            if (size != ref['size'] or sha.hexdigest() != ref['sha256']
                    or self.stat_key(path.stat()) != self.stats[str(path)]):
                raise ValueError('allocated_diagnostic_source_changed')


def _native_inventory(root, day, index):
    base = root / 'runtime/initial_quantity_research_costs' / day
    paths = [base / 'index.json']
    for sha in index['receipts'].values():
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError('allocated_diagnostic_receipt_reference_invalid')
        paths.append(base / 'generations' / (sha + '.json'))
    paths += [official.source_path(root, date) for date in index['source_dates']]
    if official.source_path(root, day).exists():
        paths.append(official.source_path(root, day))
    exact = _path(root / 'runtime/holding_actual_costs' / day)
    paths += sorted(exact.glob('*.json')) if exact.exists() else []
    paths = sorted(set(paths))
    if len(paths) > MAX_FILES or sum(_path(p).stat().st_size for p in paths) > MAX_NATIVE_BYTES:
        raise ValueError('allocated_diagnostic_native_generation_budget')
    return paths


def _native_generation_read_bytes(root, day, index):
    """The native reader reads target source once, then indexed dependencies."""
    base = root / 'runtime/initial_quantity_research_costs' / day
    total = (base / 'index.json').stat().st_size
    total += sum((base / 'generations' / (sha + '.json')).stat().st_size for sha in index['receipts'].values())
    total += sum(official.source_path(root, date).stat().st_size for date in index['source_dates'])
    target = official.source_path(root, day)
    total += target.stat().st_size if target.exists() else 0
    exact = root / 'runtime/holding_actual_costs' / day
    total += sum(path.stat().st_size for path in exact.glob('*.json')) if exact.exists() else 0
    return total


def _source_population(reader, manifest, root):
    rows, ids, counts = {}, set(), Counter()
    for ref in reader.tree(root, manifest['partitions_ref']):
        partition = reader.read(storage.safe_path(root, ref['path']), stage='input_partition', sealed=True)
        if digest(partition) != ref['artifact_sha256']:
            raise ValueError('allocated_diagnostic_partition_reference_invalid')
        for position in partition['positions']:
            identity = position['position_key']
            if identity in ids or len(ids) >= MAX_RECORDS:
                raise ValueError('allocated_diagnostic_population_duplicate_or_budget')
            ids.add(identity)
            counts[position['evidence_kind']] += 1
            if position['evidence_kind'] == 'actual_completed':
                rows[identity] = position
    expected = list(reader.tree(root, manifest['population_ids_ref']))
    if len(expected) != len(set(expected)) or set(expected) != ids:
        raise ValueError('allocated_diagnostic_population_mismatch')
    return rows, counts


def _leg_clock(value):
    """Only native fill/observation labels, explicitly owned as KST naive."""
    parsed = datetime.fromisoformat(value)
    return _clock(parsed.replace(tzinfo=reconciliation.KST).isoformat() if parsed.tzinfo is None else value)


def _terminal_clock_binding(original, normalized, acceptance, *, knowledge_cutoff):
    try:
        occurred, projected = _clock(original['completed_at']), _clock(normalized['completion_at'])
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    if occurred == projected:
        return dict(mode='same_terminal_clock', broker_terminal_occurred_at=original['completed_at'],
                    original_projection_completion_at=normalized['completion_at'])
    # A registered native producer proved unchanged broker-clock-bound receipt
    # reobservations. Its audit is a reference to that proof, not a newly read
    # raw event or permission to accept an approximate timestamp.
    producer = [(path, sha) for path, sha in acceptance.get('code_sha256', {}).items()
                if Path(path).name == NATIVE_AUDIT_PRODUCER.name]
    if len(producer) != 1 or producer[0][1] != hashlib.sha256(NATIVE_AUDIT_PRODUCER.read_bytes()).hexdigest():
        return None
    summaries = [row for row in acceptance.get('summary', []) if row.get('record_id') == original['record_id']]
    if len(summaries) != 1:
        return None
    summary = summaries[0]
    if (summary.get('symbol') != original['symbol'] or summary.get('status') != 'COMPLETED'
            or summary.get('terminal_observed') is not True
            or summary.get('completed_at') != original['completed_at']
            or summary.get('allocation_status') != 'research_cost_allocated'):
        return None
    sells = original['sell_legs']
    clocks = [_leg_clock(leg['at']) for leg in sells]
    if not clocks or max(clocks) != occurred:
        return None
    terminal_legs = [leg for leg, at in zip(sells, clocks) if at == occurred]
    audits = summary.get('receipt_reobservations')
    if not isinstance(audits, list) or not audits:
        return None
    linked, identities = [], set()
    try:
        for audit in audits:
            if not isinstance(audit, dict):
                return None
            identity = (audit['order_no'], audit['execution_no'])
            if identity in identities:
                return None
            identities.add(identity)
            legs = [leg for leg in sells if (leg['order_no'], leg['execution_no']) == identity]
            at, received = _clock(audit['original_occurred_at']), _clock(audit['original_received_at'])
            first, last = _leg_clock(audit['first_observed_at']), _leg_clock(audit['last_observed_at'])
            if (len(legs) != 1 or audit['record_id'] != original['record_id']
                    or _leg_clock(legs[0]['at']) != at or at != int(at)
                    or not at <= received <= first <= last <= knowledge_cutoff
                    or type(audit['observation_count']) is not int or audit['observation_count'] < 2
                    or type(audit['reobserved_count']) is not int
                    or audit['reobserved_count'] != audit['observation_count'] - 1
                    or any(not isinstance(audit.get(key), str) or len(audit[key]) != 64
                           or any(c not in '0123456789abcdef' for c in audit[key])
                           for key in ('native_identity_sha256', 'source_event_digests_sha256'))):
                return None
            linked.append((legs[0], at, first, audit))
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
    final = [audit for leg, at, first, audit in linked if at == occurred and first == projected]
    # Every terminal fill must have the same exact projection/occurrence bridge.
    if len(final) != len(terminal_legs) or not final:
        return None
    return dict(mode='registered_native_reobservation_audit',
        broker_terminal_occurred_at=original['completed_at'], original_projection_completion_at=normalized['completion_at'],
        source_audit_producer_path=producer[0][0], source_audit_producer_sha256=producer[0][1],
        source_summary_sha256=digest(summary), receipt_reobservations=final,
        raw_source_events_reverified_here=False, timestamp_tolerance_seconds=0)


def _position_binding(original, normalized, acceptance, *, knowledge_cutoff):
    """Bind the same original record; initial qty need not equal post-ADD qty."""
    source = normalized.get('source_reference') or {}
    carrier = acceptance['sidecar_extraction']
    expected = dict(path=Path(carrier['source_path']).name,
                    sha256=carrier['source_byte_sha256'], size=carrier['source_size'])
    if (normalized.get('symbol') != original['symbol']
            or source.get('id') != original['record_id']
            or source.get('path') != carrier['source_path']
            or source.get('projection_generation') != expected
            or normalized.get('terminal_status') != 'COMPLETED'
            or original.get('terminal_observed') is not True):
        return None
    # Native fill timestamps are explicitly KST-naive, unlike knowledge clocks.
    first = min(_leg_clock(leg['at']) for leg in original['buy_legs'])
    if normalized.get('entry_at') != first:
        return None
    return _terminal_clock_binding(original, normalized, acceptance, knowledge_cutoff=knowledge_cutoff)


def build(*, registration, input_manifest, input_root, source_acceptance, cost_root, output_root):
    """Build a new report from registered immutable local artifacts only."""
    started = time.monotonic()
    modules = (__file__, allocation.__file__, official.__file__, reconciliation.__file__, storage.__file__,
               NATIVE_AUDIT_PRODUCER)
    code = {str(_path(module)): hashlib.sha256(Path(module).read_bytes()).hexdigest() for module in modules}
    paths = {k: _path(v) for k, v in dict(registration=registration, input_manifest=input_manifest,
        input_root=input_root, source_acceptance=source_acceptance, cost_root=cost_root,
        output_root=output_root).items()}
    if (any(paths['output_root'].is_relative_to(paths[k]) or paths[k].is_relative_to(paths['output_root'])
            for k in ('input_root', 'cost_root'))
            or any(paths[k].is_relative_to(paths['output_root']) for k in ('registration', 'source_acceptance'))):
        raise ValueError('allocated_diagnostic_output_source_overlap')
    with Claim(0) as claim:
        reader = _Reader(claim)
        registered = reader.read(paths['registration'], stage='registration', sealed=True)
        spec = registered['diagnostics']['allocated_cost']
        if (registered.get('schema') != REGISTRATION_SCHEMA
                or registered.get('allowed_runtime_apply') is not False
                or registered.get('runtime_effect') is not False
                or spec.get('allowed_source_scope') != allocation.SCOPE
                or spec.get('automatic_management_change') is not False
                or spec.get('canonical_actual_economics_change') is not False
                or spec.get('strategy_replay_common_population_change') is not False
                or any(str(paths[k]) != spec.get(k) for k in ('cost_root', 'output_root'))
                or any(str(paths[k]) != spec[k].get('path') for k in ('input_manifest', 'source_acceptance'))
                or not paths['input_manifest'].is_relative_to(paths['input_root'])):
            raise ValueError('allocated_diagnostic_registration_binding_invalid')
        cutoff = _clock(spec['knowledge_cutoff'])
        if _clock(registered['registered_at']) < cutoff:
            raise ValueError('allocated_diagnostic_registration_before_cutoff')
        manifest = reader.read(paths['input_manifest'], stage='manifest', expected=spec['input_manifest'], sealed=True)
        if (manifest.get('schema') != 'main_all_scope_exit_input_manifest_v2'
                or manifest.get('allowed_runtime_apply') is not False
                or manifest.get('runtime_effect') is not False or cutoff > _clock(manifest['as_of'])):
            raise ValueError('allocated_diagnostic_manifest_contract_invalid')
        acceptance = reader.read(paths['source_acceptance'], stage='acceptance', expected=spec['source_acceptance'])
        day = acceptance['temp_generation']['completion_date']
        positions = acceptance['positions']
        originals = {row['record_id']: row for row in positions}
        if (len(originals) != len(positions) or len(positions) > MAX_RECORDS
                or set(originals) != set(acceptance['receipts'])):
            raise ValueError('allocated_diagnostic_original_population_invalid')
        base = paths['cost_root'] / 'runtime/initial_quantity_research_costs' / day
        index = reader.read(base / 'index.json', stage='cost_index')
        inventory = _native_inventory(paths['cost_root'], day, index)
        source_values, receipt_values = {}, {}
        for path in inventory:
            value = reader.read(path, stage='cost_native_inputs')
            if path.parent.name == 'holding_broker_cost_sources':
                source_values[path.stem] = official.validate(value, path.stem)
            elif path.parent.name == 'generations':
                receipt_values[path.stem] = value
        native = reconciliation.source_generation(paths['cost_root'], day)
        reader.bytes['native_cost_generation'] += _native_generation_read_bytes(paths['cost_root'], day, index)
        if native != acceptance['temp_generation']:
            raise ValueError('allocated_diagnostic_native_generation_mismatch')
        # Replay only the pure allocation arithmetic, never report/provider APIs.
        rebuilt = allocation.build_research_cost_allocations(source_values, positions)
        for identity, sha in index['receipts'].items():
            if identity not in originals or receipt_values[sha] != acceptance['consumer_receipts'][identity]:
                raise ValueError('allocated_diagnostic_receipt_acceptance_mismatch')
        actual, counts = _source_population(reader, manifest, paths['input_root'])
        output, unmatched, open_rows = [], [], []
        cohorts = {}
        for identity, original in originals.items():
            receipt = acceptance['receipts'][identity]
            if original['status'] != 'COMPLETED':
                open_rows.append(dict(record_id=identity, symbol=original['symbol'], status=receipt['status'],
                    reason=receipt.get('reason'), allocated_observed_exit_net_pnl_krw=None,
                    original_position_sha256=digest(original), source_receipt_sha256=digest(receipt)))
                continue
            if identity not in actual:
                unmatched.append(dict(record_id=identity, reason='original_terminal_absent_from_research_population'))
        for identity, normalized in sorted(actual.items()):
            original, receipt = originals.get(identity), acceptance['receipts'].get(identity)
            row = dict(record_id=identity, symbol=normalized.get('symbol'),
                normalized_position_sha256=digest(normalized),
                automatic_management_allowed=normalized.get('automatic_management_allowed'),
                operating_ai_required=normalized.get('operating_ai_required'),
                original_source_gap=normalized.get('source_gap'),
                original_entry_at=normalized.get('entry_at'), original_completion_at=normalized.get('completion_at'),
                original_qty=normalized.get('qty'), original_buy_basis_krw=normalized.get('buy_basis_krw'),
                actual_cost_reconciliation_sha256=digest(normalized.get('actual_cost_reconciliation')),
                allocation_status='source_unavailable', reason='original_allocation_position_missing',
                allocated_observed_exit_net_pnl_krw=None, allocated_observed_exit_fees_taxes_krw=None,
                actual_profit_verified=False, paired_strategy_economic_eligible=False)
            if original is not None:
                row.update(original_position_sha256=digest(original), source_receipt_content_sha256=digest(receipt),
                    source_economics_scope=receipt.get('economics_scope'),
                    source_actual_execution_cost=receipt.get('actual_execution_cost'),
                    source_cost_basis=receipt.get('cost_basis'), allocation_status=receipt.get('status'),
                    source_cost_available_at=receipt.get('cost_available_at'),
                    reason=receipt.get('reason'), source_receipt_sha256=receipt.get('receipt_sha256'))
                if receipt.get('status') == 'research_cost_allocated':
                    result = allocation.validate_research_cost(receipt, record_id=identity, symbol=original['symbol'],
                        buy_legs=original['buy_legs'], sell_legs=original['sell_legs'], custody_rows=original['custody_rows'],
                        completion_date=original['completion_observed_date'], knowledge_cutoff=cutoff)
                    if (rebuilt.get(identity) != receipt or identity not in index['receipts']
                            or receipt_values[index['receipts'][identity]] != receipt):
                        raise ValueError('allocated_diagnostic_original_allocation_mismatch')
                    clock_binding = _position_binding(original, normalized, acceptance, knowledge_cutoff=cutoff)
                    if not clock_binding:
                        row.update(allocation_status='research_cost_invalid', reason='original_position_binding_mismatch')
                    elif result['status'] != 'research_cost_allocated':
                        row.update(allocation_status=result['status'], reason=result.get('reason'))
                    else:
                        row.update(allocation_status='allocated_terminal_reference', reason=None,
                            cost_available_at=receipt['cost_available_at'], completed_at=receipt['completed_at'],
                            allocated_observed_exit_net_pnl_krw=receipt['allocated_net_pnl_krw'],
                            allocated_observed_exit_fees_taxes_krw=receipt['allocated_fees_taxes_krw'],
                            allocated_observed_exit_rate_pct=receipt['allocated_profit_rate'],
                            observed_buy_qty=receipt['buy_qty'], observed_sell_qty=receipt['sell_qty'],
                            observed_buy_amount_krw=receipt['buy_amount_krw'], observed_sell_amount_krw=receipt['sell_amount_krw'],
                            buy_fill_identity=receipt['buy_fill_identity'], sell_fill_identity=receipt['sell_fill_identity'],
                            custody_sha256=receipt['custody_sha256'], account_scope_sha256=receipt['account_scope_sha256'],
                            terminal_clock_binding=clock_binding,
                            buy_leg_count=len(original['buy_legs']), sell_leg_count=len(original['sell_legs']),
                            source_parts=receipt['sources'])
                        for part in receipt['sources']:
                            key = (part['source_date'], part['symbol'], part['cohort_sha256'])
                            cohorts[key] = {k: part[k] for k in ('source_date', 'symbol', 'cohort_sha256',
                                'confirmed_total_cost_krw', 'known_allocated_cost_krw', 'outside_allocated_cost_krw',
                                'known_record_count', 'source_sha256', 'observed_at')}
            output.append(row)
        admitted = [row for row in output if row['allocation_status'] == 'allocated_terminal_reference']
        if (_native_inventory(paths['cost_root'], day, index) != inventory
                or reconciliation.source_generation(paths['cost_root'], day) != native):
            raise ValueError('allocated_diagnostic_native_generation_changed')
        reader.bytes['native_cost_generation'] += _native_generation_read_bytes(paths['cost_root'], day, index)
        reader.finish()
        if code != {str(_path(module)): hashlib.sha256(Path(module).read_bytes()).hexdigest() for module in modules}:
            raise ValueError('allocated_diagnostic_code_changed')
        body = dict(schema=SCHEMA, diagnostic_use='observed_filled_position_terminal_allocation_reference',
            source_economics_scope=allocation.SCOPE, knowledge_cutoff=cutoff, source_date=manifest['source_date'],
            target_date=manifest['target_date'], as_of=manifest['as_of'],
            registration_path=str(paths['registration']), input_manifest_path=str(paths['input_manifest']),
            source_acceptance_path=str(paths['source_acceptance']), cost_root=str(paths['cost_root']),
            population_counts=dict(counts), actual_completed_rows=output, open_source_rows=open_rows,
            unmatched_terminal_source_rows=unmatched, allocated_terminal_reference_count=len(admitted),
            terminal_reference_totals=dict(allocated_observed_exit_net_pnl_krw=sum(
                row['allocated_observed_exit_net_pnl_krw'] for row in admitted) if admitted else None,
                allocated_observed_exit_fees_taxes_krw=sum(row['allocated_observed_exit_fees_taxes_krw'] for row in admitted)
                if admitted else None), participating_cohorts=list(cohorts.values()),
            participating_cohort_totals={k: sum(row[k] for row in cohorts.values()) if cohorts else None for k in
                ('confirmed_total_cost_krw', 'known_allocated_cost_krw', 'outside_allocated_cost_krw')},
            denominator_contract='terminal_reference_totals_cover_admitted_completed_rows_only; '
                'cohort_totals_also_include_open_and_outside_turnover',
            economic_eligible_count=0, canonical_realized_pnl_modified=False, custody_modified=False,
            ai_inputs_or_responses_modified=False, actual_profit_verified=False, allowed_runtime_apply=False,
            runtime_effect=False, selector_metrics_redefined=False, provider_calls=0, orders=0,
            metric_contract=dict(metric_role='funnel_count', decision_authority='report_only',
                window_policy='registered_source_window_and_cost_knowledge_cutoff',
                sample_floor='diagnostic_no_promotion', primary_decision_metric='none',
                source_quality_gate='native_quantity_allocation_scope_receipt_and_source_hash_exact_binding',
                forbidden_uses=['canonical_actual_pnl', 'actual_execution_cost', 'strategy_selection',
                    'alternative_exit_cost', 'runtime_apply', 'custody_override', 'AI_input_or_response_change']),
            limitations=['Allocated observed terminal reference is not exact broker per-position settlement.',
                'No attribution of the observed result to automatic management or a trailing policy.',
                'No counterfactual fill, alternative-exit cost, valid historical AI, or continuous custody is created.',
                'Costs become knowable only at cost_available_at; unavailable rows are never zero.',
                'Multiple BUY legs remain a terminal aggregate, not a modeled ADD lifecycle.'],
            source_generations=list(reader.sources.values()), code_sha256=code,
            budget=dict(shared_limit_bytes=LIMIT_BYTES, conservative_claim_bytes=claim.size,
                max_file_bytes=MAX_FILE_BYTES, max_native_generation_bytes=MAX_NATIVE_BYTES,
                tracked_read_bytes_by_stage=dict(reader.bytes),
                native_generation_invocations=2, elapsed_seconds=time.monotonic()-started))
        body['artifact_sha256'] = digest(body)
        return body


def run(**kwargs):
    output = _path(kwargs['output_root'])
    target = output / OUTPUT_NAME
    if target.exists():
        raise ValueError('allocated_diagnostic_output_already_exists')
    if output.exists() and any(output.iterdir()):
        raise ValueError('allocated_diagnostic_output_not_empty')
    report = build(**kwargs)
    # A build caller can retain the returned body; publication performs another
    # bounded CAS against those exact carriers and code, without regeneration.
    publication_bytes = 0
    for ref in report['source_generations']:
        path = _path(ref['path'])
        if path.stat().st_size != ref['size']:
            raise ValueError('allocated_diagnostic_source_changed_before_publication')
        with Claim(ref['size'] * 2), path.open('rb') as handle:
            raw = handle.read(ref['size'] + 1)
            publication_bytes += len(raw)
            if len(raw) != ref['size'] or hashlib.sha256(raw).hexdigest() != ref['sha256']:
                raise ValueError('allocated_diagnostic_source_changed_before_publication')
    if any(hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha
           for path, sha in report['code_sha256'].items()):
        raise ValueError('allocated_diagnostic_code_changed_before_publication')
    report['budget']['tracked_read_bytes_by_stage']['publication_source_verification'] = publication_bytes
    report['artifact_sha256'] = digest({k:v for k,v in report.items() if k != 'artifact_sha256'})
    raw = (json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False) + '\n').encode()
    if len(raw) > MAX_FILE_BYTES:
        raise ValueError('allocated_diagnostic_output_budget')
    output.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(raw)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('registration', 'input-manifest', 'input-root', 'source-acceptance', 'cost-root', 'output-root'):
        parser.add_argument('--' + name, required=True)
    args = vars(parser.parse_args(argv))
    result = run(**args)
    print(json.dumps(dict(schema=result['schema'], allocated_terminal_reference_count=
        result['allocated_terminal_reference_count'], economic_eligible_count=0, allowed_runtime_apply=False)))


if __name__ == '__main__':
    main()
