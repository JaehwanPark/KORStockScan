"""Registered, offline completed-bar path geometry; never an exit policy.

Automation owns this separate report consumer beside the minute diagnostic.
The existing minute source reader owns exact chart identity and DB/WAL copies.
Prefix geometry is retrospective, not a reconstructed entry/holding feature.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import date, datetime
import math
from pathlib import Path

from src.engine.lifecycle import research_storage as storage
from src.engine.lifecycle.holding_window_generation import byte_generation
from src.engine.lifecycle.research_input_budget import Claim
from src.engine.scalping.pre_submit_delay_initial_policy import _atomic, digest, number
from src.engine.scalping.trailing_threshold_policy import market_type_at
from . import main_trailing_all_scope_research as owner
from . import main_trailing_minute_path_diagnostics as minute

SCHEMA = 'main_trailing_followup_path_research_v1'
REGISTRATION_SCHEMA = 'main_trailing_followup_registration_v1'
LANDMARKS = (30, 60, 120, 180)
HORIZONS = (3, 5, 10, 20, 30, 60)
MODEL_COST = .0023
TARGET = .4
COMPARISON_LOSS = -3.
OUTCOME_WINDOW = 'landmark_to_entry_horizon_completed_bars'
MAX_POSITIONS = 20000
GEOMETRY_LABELS = ['below_break_even', 'at_or_above_break_even', 'mixed', 'no_full_bar', 'gap']
SPLIT_CONTRACT = dict(basis='KST entry date',
    components='same_symbol_connected_intervals_over_entry_to_60_minutes',
    holdout='entry_date_at_or_after_holdout_start',
    purge='exclude earlier-split members of any component intersecting holdout; retain their IDs and reason',
    selection='none; descriptive diagnostics only; no thresholds fitted',
    train='entry_date_before_holdout_start')


def _code_generation():
    return dict(existing_research_contract_sha256=owner.code_contract(), files={
        str(Path(module.__file__).resolve()): byte_generation(Path(module.__file__))
        for module in (minute, minute.completed_history)
    }, report_producer=byte_generation(Path(__file__)))


def _safe_absolute(path):
    path = Path(path).absolute()
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('followup_path_invalid')
    return path


def _registration(path, manifest, generation):
    before = byte_generation(path)
    with Claim(before['size'] * 8):
        value = owner._sealed(path)
    fixed = dict(schema=REGISTRATION_SCHEMA, source_date=manifest['source_date'],
        target_date=manifest['target_date'], as_of=manifest['as_of'],
        input_manifest_generation=generation, landmarks_seconds=list(LANDMARKS),
        horizon_minutes=list(HORIZONS), modeled_cost_rate=MODEL_COST,
        target_net_pct=TARGET, comparison_loss_net_pct=COMPARISON_LOSS,
        outcome_window=OUTCOME_WINDOW, decision_authority='report_only',
        prefix_window='entry_to_landmark_completed_bars_only', path_geometry_labels=GEOMETRY_LABELS,
        split_contract=SPLIT_CONTRACT,
        allowed_runtime_apply=False)
    if any(value.get(key) != expected for key, expected in fixed.items()):
        raise ValueError('followup_registration_contract_invalid')
    holdout = value.get('holdout_start_date')
    if (not isinstance(holdout, str) or date.fromisoformat(holdout).isoformat() != holdout
            or not min(manifest['consumed_dates']) < holdout <= max(manifest['consumed_dates'])):
        raise ValueError('followup_holdout_boundary_invalid')
    if any(value.get(key) is not False for key in ('allowed_runtime_apply', 'runtime_effect', 'actual_pid_consumed')):
        raise ValueError('followup_registration_authority_invalid')
    if value.get('holdout_end_date', manifest['source_date']) != manifest['source_date']:
        raise ValueError('followup_holdout_end_invalid')
    return value, before


def completed_window(reference_price, bars, start_at, end_at):
    """Only wholly contained completed minutes; contacts are observed bounds."""
    price, start, end = map(number, (reference_price, start_at, end_at))
    if price is None or price <= 0 or start is None or end is None or end < start:
        raise ValueError('followup_window_input_invalid')
    first, stop = math.ceil(start / 60) * 60, math.floor(end / 60) * 60
    expected = list(range(first, stop, 60))
    selected = [(int(at), low, high) for at, low, high in bars if first <= at < stop]
    if len({at for at, _, _ in selected}) != len(selected):
        raise ValueError('followup_duplicate_minute')
    missing = sorted(set(expected) - {at for at, _, _ in selected})
    duration = end - start
    leading = min(duration, first - start)
    trailing = min(duration - leading, end - stop)
    coverage = ('no_full_bar' if not expected else 'gap' if missing
                else 'complete_completed_bar_window')
    result = dict(start_at=start, end_at=end, expected_completed_bar_count=len(expected),
        observed_completed_bar_count=len(selected), missing_completed_bar_count=len(missing),
        first_missing_completed_bar_at=missing[0] if missing else None,
        leading_unobserved_seconds=leading, trailing_unobserved_seconds=trailing,
        coverage=coverage, full_interval_observed=bool(expected and not missing and not leading and not trailing),
        net_low_bound_pct=None, net_high_bound_pct=None,
        target_in_observed_completed_bars=None, comparison_loss_in_observed_completed_bars=None,
        first_target_bar_at=None, first_comparison_loss_bar_at=None,
        both_levels_same_bar_count=0, observed_contact_order='unobserved',
        intrabar_order_known=False)
    if not selected:
        return result
    values = [(at, 100 * (low * (1 - MODEL_COST) / price - 1),
               100 * (high * (1 - MODEL_COST) / price - 1)) for at, low, high in selected]
    target = [at for at, _, high in values if high >= TARGET]
    loss = [at for at, low, _ in values if low <= COMPARISON_LOSS]
    order = ('same_first_bar_ambiguous' if target and loss and target[0] == loss[0]
             else 'observed_target_bar_before_loss_bar' if target and loss and target[0] < loss[0]
             else 'observed_loss_bar_before_target_bar' if target and loss
             else 'target_only_observed' if target else 'loss_only_observed' if loss else 'neither_observed')
    result.update(net_low_bound_pct=min(low for _, low, _ in values),
        net_high_bound_pct=max(high for _, _, high in values),
        target_in_observed_completed_bars=bool(target), comparison_loss_in_observed_completed_bars=bool(loss),
        first_target_bar_at=target[0] if target else None,
        first_comparison_loss_bar_at=loss[0] if loss else None,
        both_levels_same_bar_count=sum(low <= COMPARISON_LOSS and high >= TARGET for _, low, high in values),
        observed_contact_order=order)
    return result


def prefix_geometry(window):
    """Geometry labels do not claim trend, recovery, arming or AI decisions."""
    if window['coverage'] in {'no_full_bar', 'gap'}:
        return window['coverage']
    if window['net_high_bound_pct'] < 0:
        return 'below_break_even'
    if window['net_low_bound_pct'] >= 0:
        return 'at_or_above_break_even'
    return 'mixed'


def _position_row(position, as_of, *, window_end_at):
    kind = position['evidence_kind']
    at = number(position.get('entry_at'))
    price, role = number(position.get('entry_reference_ask')), position.get('entry_reference_role')
    if kind == 'actual_completed' and not position.get('source_gap'):
        qty, basis = number(position.get('qty')), number(position.get('buy_basis_krw'))
        if qty is not None and qty > 0 and qty.is_integer() and basis is not None and basis > 0:
            price, role = basis / qty, 'verified_buy_leg_price_path_only'
    row = dict(identity=position['position_key'], evidence_kind=kind, symbol=position.get('symbol'),
        item=position.get('item'), route=position.get('route'), entry_at=at,
        reference_price=price, reference_role=role,
        automatic_management_allowed=position.get('automatic_management_allowed'),
        original_source_gap=position.get('source_gap'),
        research_entry_window_exclusion=position.get('research_entry_window_exclusion'),
        research_entry_window_end_at=window_end_at,
        source_reference=position.get('source_reference'),
        native_signal_at=position.get('native_signal_at'),
        auxiliary_completed_at=position.get('auxiliary_completed_at'),
        market=market_type_at(at) if at is not None else None,
        status='pending', reason=None, landmarks=[],
        decision_feature_reconstructed=False, runtime_effect=False, actual_profit_verified=False)
    if at is not None and 0 < window_end_at <= at <= as_of:
        row.update(status='research_excluded', reason='entry_after_research_window')
    elif (at is None or not 0 < at <= as_of or price is None or price <= 0
            or not isinstance(row['item'], str) or row['item'].split('_', 1)[0] != row['symbol']
            or role not in {'native_entry_ask_price_path_only', 'verified_buy_leg_price_path_only'}):
        row.update(status='source_gap', reason='native_entry_reference_or_exact_item_missing')
    elif row['research_entry_window_exclusion']:
        row.update(status='research_excluded', reason=row['research_entry_window_exclusion'])
    return row


def _clusters(rows, holdout, as_of):
    """Conservative symbol/time components span route and evidence namespaces."""
    boundary = datetime.fromisoformat(holdout + 'T00:00:00+09:00').timestamp()
    groups = defaultdict(list)
    for row in rows:
        at = row['entry_at']
        if at is None or at <= 0 or not isinstance(row['symbol'], str):
            row.update(overlap_cluster_id=None, overlap_cluster_size=None, split='source_gap')
            continue
        row['entry_date'] = datetime.fromtimestamp(at, minute.KST).date().isoformat()
        if row.get('reason') == 'entry_after_research_window':
            row.update(overlap_cluster_id=None, overlap_cluster_size=None, split='outside_source_period')
            continue
        row['planned_outcome_end_at'] = at + max(HORIZONS) * 60
        row['outcome_right_censored_by_as_of'] = row['planned_outcome_end_at'] > as_of
        groups[row['symbol']].append(row)
    cluster_rows = []

    def finish(group):
        start = min(r['entry_at'] for r in group)
        end = max(r['planned_outcome_end_at'] for r in group)
        split = 'holdout' if start >= boundary else 'purged_overlap_boundary' if end >= boundary else 'train'
        identity = digest(dict(symbol=group[0]['symbol'], identities=sorted(r['identity'] for r in group),
                               start_at=start, end_at=end))
        for row in group:
            member_split = 'holdout' if row['entry_at'] >= boundary else split
            row.update(overlap_cluster_id=identity, overlap_cluster_size=len(group), split=member_split)
        cluster_rows.append(dict(cluster_id=identity, symbol=group[0]['symbol'], count=len(group),
            start_at=start, end_at=end, split=split, entry_dates=sorted({r['entry_date'] for r in group})))

    for symbol in sorted(groups):
        group, end = [], None
        for row in sorted(groups[symbol], key=lambda r: (r['entry_at'], r['identity'])):
            if group and row['entry_at'] > end:
                finish(group)
                group = []
            group.append(row)
            end = max(end or 0, row['planned_outcome_end_at'])
        if group:
            finish(group)
    return cluster_rows


def _measure_row(row, source):
    at, price = row['entry_at'], row['reference_price']
    row.update(status='retrospective_path_geometry', reason=None,
        revision_sha256=source['revision_sha256'], selected_revision_available_at=source['available_at'],
        adjustment_equivalence_to_reference='unproven')
    for seconds in LANDMARKS:
        landmark = at + seconds
        prefix = completed_window(price, source['bars'], at, landmark)
        row['landmarks'].append(dict(landmark_seconds=seconds, landmark_at=landmark,
            geometry=prefix_geometry(prefix), prefix=prefix,
            selected_revision_available_at_or_before_landmark=source['available_at'] <= landmark,
            entry_feature=False, historical_revision_absence_proven=False,
            outcomes=[dict(horizon_minutes=horizon,
                **completed_window(price, source['bars'], landmark, at + horizon * 60))
                for horizon in HORIZONS if at + horizon * 60 >= landmark]))
    return row


def run(registration_path, manifest_path, *, input_root, data_root, output_root):
    """Write only a new explicit output directory after registered validation."""
    root, data, out = map(_safe_absolute, (input_root, data_root, output_root))
    manifest_path, registration_path = map(_safe_absolute, (manifest_path, registration_path))
    if (not manifest_path.is_relative_to(root) or any(out.is_relative_to(p) or p.is_relative_to(out)
            for p in (root, data)) or registration_path.is_relative_to(out)
            or out.exists() and any(out.iterdir())):
        raise ValueError('followup_output_or_input_path_invalid')
    manifest_before, code_before = byte_generation(manifest_path), _code_generation()
    with Claim(manifest_before['size'] * 8), Claim(0) as retained:
        manifest = owner._sealed(manifest_path)
        if (manifest.get('schema') != 'main_all_scope_exit_input_manifest_v2'
                or number(manifest.get('as_of')) is None or manifest['as_of'] <= 0
                or Path(manifest['source_data_root']).resolve() != data.resolve()
                or manifest.get('assembly_code_contract_sha256') != code_before['existing_research_contract_sha256']):
            raise ValueError('followup_manifest_contract_invalid')
        registration, registration_before = _registration(registration_path, manifest, manifest_before)
        if registration.get('input_manifest_path') != str(manifest_path):
            raise ValueError('followup_registration_manifest_path_invalid')
        generations = {}
        with Claim(0) as scope_budget:
            scope = owner.preflight_header(manifest, root, generations, scope_budget=scope_budget)
            out.mkdir(parents=True, exist_ok=True)
            scope_ref = storage.write_tree(out, scope.pop('scopes'))
            scope['scopes_ref'] = scope_ref
        rows, identities, excluded, partitions = [], set(), [], {}
        window_end_at = datetime.fromisoformat(manifest['source_date'] + 'T00:00:00+09:00').timestamp() + 86400
        for path, generation, part in minute._partitions(root, manifest):
            if str(path) in partitions:
                raise ValueError('followup_duplicate_partition')
            partitions[str(path)] = generation
            if (part.get('source_date') != manifest['source_date']
                    or part.get('target_date', manifest['target_date']) != manifest['target_date']):
                raise ValueError('followup_partition_scope_invalid')
            for position in part['positions']:
                identity, kind = position['position_key'], position['evidence_kind']
                if (not isinstance(identity, str) or not identity or identity in identities
                        or len(identities) >= MAX_POSITIONS):
                    raise ValueError('followup_position_census_invalid')
                identities.add(identity)
                retained.grow(512)
                if kind == 'actual_entry_alternative_exit':
                    excluded.append(dict(identity=identity, reason='duplicate_actual_entry_alternative_exit'))
                elif kind in {'actual_completed', 'enter_pass_opportunity_cf'}:
                    row = _position_row(position, manifest['as_of'], window_end_at=window_end_at)
                    retained.grow(len(storage.encoded(row)) * 8 + 1024)
                    rows.append(row)
                else:
                    raise ValueError('followup_evidence_kind_invalid')
            # The generator's decode Claim ends on its next iteration. Do not
            # retain that unclaimed last partition during minute-source reads.
            position = None
            del part
        expected = set()
        for identity in storage.iter_tree(root, manifest['population_ids_ref']):
            if not isinstance(identity, str) or identity in expected:
                raise ValueError('followup_population_manifest_invalid')
            expected.add(identity)
        if expected != identities:
            raise ValueError('followup_population_mismatch')
        del expected
        clusters = _clusters(rows, registration['holdout_start_date'], manifest['as_of'])
        cluster_ref = storage.write_tree(out, clusters)
        excluded_ref = storage.write_tree(out, excluded)
        population_ref = storage.write_tree(out, sorted(identities))
        groups = defaultdict(list)
        for row in rows:
            if row['status'] == 'pending':
                groups[(row['entry_date'].replace('-', ''), row['item'])].append(row)
        sources, carriers, missing_carriers, statuses, aggregate = [], {}, set(), Counter(), {}

        def counted(row):
            statuses[(row['evidence_kind'], row['status'], row.get('reason'))] += 1
            for landmark in row['landmarks']:
                for outcome in landmark['outcomes']:
                    key = (row['evidence_kind'], row['market'], row['route'], row['split'],
                           landmark['landmark_seconds'], landmark['geometry'], outcome['horizon_minutes'])
                    if key not in aggregate:
                        retained.grow(2048)
                        aggregate[key] = dict(rows=0, observed=0, full=0, target=0, loss=0, ambiguous=0, clusters=set())
                    value = aggregate[key]
                    value['rows'] += 1
                    value['observed'] += outcome['observed_completed_bar_count'] > 0
                    value['full'] += outcome['full_interval_observed']
                    value['target'] += outcome['target_in_observed_completed_bars'] is True
                    value['loss'] += outcome['comparison_loss_in_observed_completed_bars'] is True
                    value['ambiguous'] += outcome['both_levels_same_bar_count'] > 0
                    if row['overlap_cluster_id'] not in value['clusters']:
                        retained.grow(128)
                        value['clusters'].add(row['overlap_cluster_id'])
            return row

        def measured():
            for row in rows:
                if row['status'] != 'pending':
                    yield counted(row)
            for day in sorted({key[0] for key in groups}):
                try:
                    with Claim(minute.completed_history.MAX_ROWS * 4096 + 2 * 1024 * 1024 * 8), minute._snapshot(data, day) as snapshot:
                        for (group_day, item), group in sorted(groups.items()):
                            if group_day != day:
                                continue
                            source, issue = minute._read_series(snapshot, day, item, as_of=manifest['as_of'])
                            if source:
                                provenance = {k: v for k, v in source.items() if k != 'bars'}
                                retained.grow(len(storage.encoded(provenance)) * 8)
                                sources.append(provenance)
                            for base in group:
                                with Claim(256 * 1024):
                                    row = dict(base, landmarks=[])
                                    if issue:
                                        row.update(status='source_gap', reason=issue)
                                    else:
                                        _measure_row(row, source)
                                    yield counted(row)
                            source = None
                        carriers[str(snapshot['path'])] = snapshot['generation']
                except (OSError, ValueError, TypeError, OverflowError) as exc:
                    # Source-read gaps are per-day, but provenance mutation and
                    # budget/consumer failures must never produce a partial PASS.
                    reason = str(exc)
                    if reason not in {'minute_history_not_stored', 'minute_history_copy_resource_budget_exceeded',
                                      'minute_history_path_invalid'}:
                        raise
                    if reason == 'minute_history_not_stored':
                        missing_carriers.add(data / 'runtime/main_minute_history' / day / 'completed.sqlite3')
                    for (group_day, _), group in sorted(groups.items()):
                        if group_day == day:
                            for base in group:
                                yield counted(dict(base, status='source_gap', reason=reason))

        rows_ref = storage.write_tree(out, measured())
        if rows_ref['count'] + len(excluded) != len(identities):
            raise ValueError('followup_result_population_mismatch')
        for path, generation in carriers.items():
            if minute.carrier_generation(path) != generation:
                raise ValueError('followup_source_carrier_changed')
        if any(path.exists() for path in missing_carriers):
            raise ValueError('followup_source_carrier_appeared')
        for path, generation in partitions.items():
            if byte_generation(Path(path)) != generation:
                raise ValueError('followup_partition_changed')
        for path, sha in generations.items():
            if byte_generation(Path(path))['sha256'] != sha:
                raise ValueError('followup_parent_changed')
        for key in ('partitions_ref', 'population_ids_ref'):
            for _ in storage.iter_tree(root, manifest[key]):
                pass
        for reference in (rows_ref, scope_ref, cluster_ref, excluded_ref, population_ref):
            for _ in storage.iter_tree(out, reference):
                pass
        if (byte_generation(manifest_path) != manifest_before
                or byte_generation(registration_path) != registration_before or _code_generation() != code_before):
            raise ValueError('followup_input_or_code_changed')
        summaries = []
        for key, value in sorted(aggregate.items(), key=lambda item: str(item[0])):
            summaries.append(dict(evidence_kind=key[0], market=key[1], route=key[2], split=key[3],
                landmark_seconds=key[4], geometry=key[5], horizon_minutes=key[6],
                row_count=value['rows'], overlap_cluster_count=len(value['clusters']),
                observed_window_count=value['observed'], full_interval_count=value['full'],
                target_contact_row_count=value['target'], comparison_loss_contact_row_count=value['loss'],
                same_bar_ambiguous_row_count=value['ambiguous']))
        body = dict(schema=SCHEMA, status='complete', source_date=manifest['source_date'],
            target_date=manifest['target_date'], as_of=manifest['as_of'],
            input_manifest_path=str(manifest_path), input_manifest_generation=manifest_before,
            registration_path=str(registration_path), registration_generation=registration_before,
            registration_sha256=registration['artifact_sha256'], code_generation=code_before,
            input_population_count=len(identities), population_count=rows_ref['count'],
            excluded_alternative_exit_count=len(excluded), excluded_alternative_exit_ids_ref=excluded_ref,
            population_ids_ref=population_ref, rows_ref=rows_ref, clusters_ref=cluster_ref,
            source_revisions=sources, scope=scope,
            source_carriers=carriers, missing_source_carriers=[str(path) for path in sorted(missing_carriers)],
            input_partition_generations=partitions,
            status_counts=[dict(evidence_kind=k[0], status=k[1], reason=k[2], count=v)
                           for k, v in sorted(statuses.items(), key=lambda item: str(item[0]))],
            summaries=summaries, holdout_start_date=registration['holdout_start_date'],
            split_contract={**SPLIT_CONTRACT, 'interval_endpoints': 'closed; touching intervals share a component',
                'boundary_rule': 'earlier entry whose component end equals or exceeds holdout start is purged'},
            model=dict(cost_rate=MODEL_COST, target_net_pct=TARGET, comparison_loss_net_pct=COMPARISON_LOSS,
                adjustment_equivalence_to_reference='unproven', executable_ordering=False,
                outcome_window=OUTCOME_WINDOW, prefix_role='retrospective_path_geometry'),
            metric_contract=dict(metric_role='funnel_count', decision_authority='report_only',
                window_policy='registered_completed_bar_landmarks_and_later_windows',
                sample_floor='diagnostic_no_promotion', primary_decision_metric='none',
                source_quality_gate='native_revision_exact_item_and_sealed_population',
                forbidden_uses=['entry_feature', 'holding_AI', 'armed_state', 'actual_pnl', 'fill',
                                'winrate_selection', 'runtime_apply', 'threshold_selection']),
            economic_eligible_count=0, actual_profit_verified=False, allowed_runtime_apply=False,
            actual_pid_consumed=False, runtime_effect=False)
        body['artifact_sha256'] = digest(body)
        _atomic(out / 'report.json', body)
        return body


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ('registration', 'manifest', 'input-root', 'data-root', 'output-root'):
        parser.add_argument('--' + argument, required=True)
    args = parser.parse_args(argv)
    result = run(args.registration, args.manifest, input_root=args.input_root,
                 data_root=args.data_root, output_root=args.output_root)
    print(f"{result['status']} population={result['population_count']} scope={result['scope']['scope_count']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
