"""Read-only holding research use of independently verified broker allocations.

Lifecycle owns cost attribution. This adapter does not change canonical actual
costs, Main custody, replay eligibility, or the existing actual-profit selector.
"""
from collections import OrderedDict
from contextlib import ExitStack
from datetime import date
from decimal import Decimal
import json
import hashlib
import os
import stat
from pathlib import Path

from . import broker_cost_allocation as allocation
from . import broker_cost_source as official
from .broker_cost_reconciliation import digest
from .holding_window_generation import byte_generation, source_stat
from .research_input_budget import Claim

SCHEMA = 'main_holding_research_cost_v1'
SCOPE = 'main_holding_exit_research_only'
MAX_REGISTRY_BYTES = 4 * 1024 * 1024


def historical_registry_generation_matches(path, generation, source_date, *, protected_owners=None):
    """Accept only a verified original prefix plus unrelated later-day owners.

    Historical orders, existing historical owners, rewrites, invalid hash chains
    and ambiguous dates still invalidate research. This never changes custody.
    """
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerRegistryError
    path = Path(path)
    try:
        cutoff = date.fromisoformat(source_date)
        before = path.stat()
        size = generation['size']
        if (path.name != 'order_owner_registry.jsonl' or path.parent.name != 'runtime'
                or path.is_symlink() or any(p.is_symlink() for p in path.parents)
                or not stat.S_ISREG(before.st_mode) or type(size) is not int
                or not 0 < size <= before.st_size <= MAX_REGISTRY_BYTES):
            return False
        with Claim(before.st_size * 12 + 4096):
            with path.open('rb') as stream:
                prefix = stream.read(size)
            if (len(prefix) != size or not prefix.endswith(b'\n')
                    or hashlib.sha256(prefix).hexdigest() != generation['sha256']):
                return False
            events = OrderOwnerRegistry(path).verified_events_snapshot(max_bytes=MAX_REGISTRY_BYTES)
            count = sum(bool(line.strip()) for line in prefix.splitlines())
            # Native terminal-reconciliation rows refer to an existing intent
            # and omit its date/owner. Global retired-owner disposition also
            # has no order date. Fold the sealed prefix through its native
            # projection instead of treating these valid events as bad dates.
            state = OrderOwnerRegistry._state(events[:count])
            historical_owners = {
                row.get('owner_id') for row in state.values()
                if date.fromisoformat(row['order_date']) <= cutoff
            }
            if protected_owners is not None:
                if not isinstance(protected_owners, frozenset) or any(
                        not isinstance(owner, str) or not owner.startswith('main_scalping:')
                        for owner in protected_owners):
                    return False
                historical_owners = historical_owners.intersection(protected_owners)
                # A later order for a frozen completed owner also invalidates
                # that report, even if its original registry intent is absent.
                historical_owners.update(protected_owners)
            for row in events[count:]:
                resolved = row
                if row.get('event') == 'TERMINAL_RECONCILIATION_RECORDED':
                    from src.trading.order.owner_custody_registry import _terminal_proof
                    current = state[row['intent_id']]
                    proof = row['terminal_reconciliation']
                    if (current.get('state') != 'ORDER_TERMINAL'
                            or row.get('account_key') != current.get('account_key')
                            or proof != _terminal_proof(current, proof['receipt_sha256'])):
                        return False
                    resolved = {**current, **row}
                if (date.fromisoformat(resolved['order_date']) <= cutoff
                        or not resolved.get('owner_id') or resolved['owner_id'] in historical_owners
                        or resolved.get('side') not in {'BUY', 'SELL'}):
                    return False
                if row.get('intent_id'):
                    state.setdefault(row['intent_id'], {}).update(row)
        return source_stat(path.stat()) == source_stat(before)
    except (OSError, ValueError, KeyError, TypeError, OwnerRegistryError):
        return False


def _json(path, before, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, 'rb') as stream:
        observed = os.fstat(stream.fileno())
        if not stat.S_ISREG(observed.st_mode) or source_stat(observed) != source_stat(before):
            raise ValueError('holding_research_cost_input_changed_before_read')
        raw = stream.read(maximum + 1)
        if len(raw) != before.st_size or len(raw) > maximum:
            raise ValueError('holding_research_cost_input_size_invalid')
        return json.loads(raw)


def inventory(root, days):
    """Current committed dependencies, excluding unreferenced old generations."""
    root = Path(root)
    paths = set()
    for day in days:
        date.fromisoformat(day)
        directory = root / 'runtime/initial_quantity_research_costs' / day
        index_path = directory / 'index.json'
        if not index_path.exists():
            continue
        paths.add(index_path)
        before = index_path.stat()
        if index_path.is_symlink() or any(p.is_symlink() for p in index_path.parents) or not stat.S_ISREG(before.st_mode) or before.st_size > official.MAX_BYTES:
            raise ValueError('holding_research_cost_index_partition_required')
        with Claim(before.st_size * 8 + 4096):
            try:
                index = _json(index_path, before, official.MAX_BYTES)
                receipts, dates = index['receipts'], index['source_dates']
                if (not isinstance(receipts, dict) or len(receipts) > allocation.MAX_RECORDS
                    or not isinstance(dates, list) or len(dates) > allocation.MAX_DATES):
                    raise ValueError('holding_research_cost_inventory_invalid')
                for sha in receipts.values():
                    if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                        raise ValueError('holding_research_cost_inventory_reference_invalid')
                    paths.add(directory / 'generations' / (sha + '.json'))
                for source_day in dates:
                    paths.add(official.source_path(root, source_day))
            except (ValueError, TypeError, KeyError):
                # Its exact index bytes remain evidence. Each identifiable
                # record receives a gap; malformed costs do not erase prices.
                pass
        if source_stat(index_path.stat()) != source_stat(before):
            raise ValueError('holding_research_cost_inventory_changed')
    return paths


def frozen_index(root, path, generation):
    """Read exact prior native index bytes, never promote a later cost revision."""
    root, path = Path(root).resolve(strict=True), Path(path)
    day = path.parent.name
    if (path != root/'runtime/initial_quantity_research_costs'/day/'index.json'
            or date.fromisoformat(day).isoformat() != day
            or generation.get('path') != 'index.json'
            or type(generation.get('size')) is not int
            or not 0 < generation['size'] <= MAX_REGISTRY_BYTES
            or not isinstance(generation.get('sha256'), str)
            or len(generation['sha256']) != 64
            or any(c not in '0123456789abcdef' for c in generation['sha256'])):
        raise ValueError('holding_research_cost_frozen_index_identity_invalid')

    def read(source):
        before = source.stat()
        if (source.is_symlink() or any(p.is_symlink() for p in source.parents)
                or not stat.S_ISREG(before.st_mode) or before.st_size > MAX_REGISTRY_BYTES):
            raise ValueError('holding_research_cost_frozen_index_source_invalid')
        value = _json(source, before, MAX_REGISTRY_BYTES)
        if (source_stat(source.stat()) != source_stat(before)
                or not isinstance(value, dict) or value.get('schema') != allocation.INDEX_SCHEMA
                or value.get('completion_date') != day
                or value.get('index_sha256') != digest({k:v for k,v in value.items() if k != 'index_sha256'})
                or not isinstance(value.get('receipts'), dict) or len(value['receipts']) > allocation.MAX_RECORDS
                or any(not isinstance(sha, str) or len(sha) != 64
                    or any(c not in '0123456789abcdef' for c in sha) for sha in value['receipts'].values())
                or not isinstance(value.get('source_dates'), list)
                or len(value['source_dates']) > allocation.MAX_DATES
                or any(not isinstance(d, str) or date.fromisoformat(d).isoformat() != d
                    for d in value['source_dates'])):
            raise ValueError('holding_research_cost_frozen_index_contract_invalid')
        return value

    current = read(path)
    if byte_generation(path) == generation:
        return current
    # The native publisher archives the physical original before replacing its
    # alias. Keep this a logical proof; never cache its SHA against the alias.
    archive = path.parent/'index_generations'/(generation['sha256']+'.json')
    old = read(archive)
    observed = byte_generation(archive)
    if any(observed.get(key) != generation[key] for key in ('size', 'sha256')):
        raise ValueError('holding_research_cost_frozen_index_bytes_changed')
    return old


def _seal(body):
    return {**body, 'artifact_sha256': digest(body)}


class Source:
    """One bounded registry and four cost objects, released at batch completion."""
    def __init__(self, data_root, *, cost_data_root=None, knowledge_cutoff=None, sources=None,
                 registry_source_date=None):
        self.root = Path(data_root).resolve()
        self.cost_root = Path(cost_data_root or data_root).resolve()
        self.cutoff = knowledge_cutoff
        self.registry_source_date = registry_source_date
        self.sources = sources if sources is not None else {}
        self.cache = OrderedDict()
        self.registry = None
        self.registry_index = None
        self.registry_generation = None
        self.registry_stat = None
        self.registry_claim = None
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        for _, claim, _, _ in self.cache.values():
            claim.close()
        self.cache.clear()
        if self.registry_claim is not None:
            self.registry_claim.close()
        self.registry = self.registry_index = self.registry_generation = self.registry_stat = None
        self.registry_claim = None
        self.closed = True

    def _read(self, path, maximum):
        if self.closed:
            raise ValueError('holding_research_cost_source_closed')
        path = Path(path)
        from src.engine.automation.main_trailing_source_reuse import frozen_official_source
        frozen = frozen_official_source(self.cost_root,path)
        physical = frozen[0] if frozen is not None else path
        def signature():
            current = source_stat(path.stat())
            return (current,source_stat(physical.stat())) if frozen is not None else current
        if path in self.cache:
            value, claim, observed, validated = self.cache[path]
            if path.is_symlink() or any(p.is_symlink() for p in path.parents) or signature() != observed:
                self.cache.pop(path)
                claim.close()
                raise ValueError('holding_research_cost_source_changed')
            self.cache.move_to_end(path)
            return value
        before = physical.stat(); observed = signature()
        if physical.is_symlink() or any(p.is_symlink() for p in physical.parents) or not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise ValueError('holding_research_cost_partition_required')
        while len(self.cache) >= 4:
            _, (_, claim, _, _) = self.cache.popitem(last=False)
            claim.close()
        while True:
            try:
                claim = Claim(before.st_size * 8 + 4096)
                break
            except ValueError:
                if not self.cache:
                    raise
                _, (_, claim, _, _) = self.cache.popitem(last=False)
                claim.close()
        try:
            value = _json(physical, before, maximum)
            generation = frozen[1] if frozen is not None else byte_generation(path)
            if signature() != observed:
                raise ValueError('holding_research_cost_source_changed')
        except BaseException:
            claim.close()
            raise
        self.cache[path] = (value, claim, observed, False)
        self.sources[str(path)] = generation
        return value

    def _custody(self, trade, buys):
        from src.trading.order.owner_custody_registry import OrderOwnerRegistry
        from src.engine.sniper_trade_review_report import _quantity_registry_fill_custody, _quantity_registry_index
        path = self.root / 'runtime/order_owner_registry.jsonl'
        if self.registry is None:
            before = path.stat()
            if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not stat.S_ISREG(before.st_mode) or before.st_size > MAX_REGISTRY_BYTES:
                raise ValueError('holding_research_cost_registry_partition_required')
            claim = Claim(before.st_size * 12 + 4096)
            try:
                registry = OrderOwnerRegistry(path).verified_events_snapshot(max_bytes=MAX_REGISTRY_BYTES)
                generation = byte_generation(path)
                if source_stat(path.stat()) != source_stat(before):
                    raise ValueError('holding_research_cost_registry_changed')
                index = _quantity_registry_index(registry)
            except BaseException:
                claim.close()
                raise
            self.registry, self.registry_index, self.registry_claim = registry, index, claim
            self.registry_stat = source_stat(before)
            self.registry_generation = dict(generation, status='verified',
                tail_hash=registry[-1]['event_hash'] if registry else '0' * 64)
            self.sources[str(path)] = generation
        if path.is_symlink() or any(p.is_symlink() for p in path.parents) or source_stat(path.stat()) != self.registry_stat:
            refreshed_stat = source_stat(path.stat())
            if (not self.registry_source_date or not historical_registry_generation_matches(
                    path, self.registry_generation, self.registry_source_date)
                    or source_stat(path.stat()) != refreshed_stat):
                raise ValueError('holding_research_cost_registry_changed')
            self.registry_stat = refreshed_stat
        row = dict(trade, code=trade.get('code') or trade.get('stock_code'))
        return _quantity_registry_fill_custody(row, {'buy_fill_legs': buys}, self.registry,
            self.registry_generation, registry_index=self.registry_index)

    def _official(self, receipt, buys, sells):
        for part in receipt['sources']:
            day = part['source_date']
            path = official.source_path(self.cost_root, day)
            source = self._read(path, official.MAX_BYTES)
            value, claim, signature, validated = self.cache[path]
            if not validated:
                official.validate(source, day)
                self.cache[path] = (value, claim, signature, True)
            diary = [r for r in official.rows(source, 'ka10170')
                     if official.symbol(r.get('stk_cd')) == receipt['symbol']]
            if len(diary) != 1:
                raise ValueError('holding_research_cost_official_symbol_ambiguous')
            row = diary[0]
            if (source['source_sha256'] != part['source_sha256']
                or source['broker_account_sha256'] != part['broker_account_sha256']
                or source['local_account_key_sha256'] != receipt['account_scope_sha256']
                or digest(row) != part['diary_row_sha256']
                or allocation._clock(source['observations']['ka10170']['observed_at']) != allocation._clock(part['observed_at'])
                or official.number(row['cmsn_alm_tax']) != official.number(part['confirmed_total_cost_krw'])
                or official.number(row['buy_amt']) != official.number(part['confirmed_buy_amount_krw'])
                or official.number(row['sell_amt']) != official.number(part['confirmed_sell_amount_krw'])):
                raise ValueError('holding_research_cost_official_binding_invalid')
            for legs, quantity, amount in ((buys, 'buy_qty', 'buy_amt'), (sells, 'sell_qty', 'sell_amt')):
                selected = [leg for leg in allocation._legs(legs) if leg[0].date().isoformat() == day]
                if (sum((leg[1] for leg in selected), Decimal(0)) > official.number(row[quantity])
                    or sum((leg[2] for leg in selected), Decimal(0)) > official.number(row[amount])):
                    raise ValueError('holding_research_cost_official_quantity_invalid')

    def record(self, trade, *, completion_date, assembly_root=None):
        """Called only after the existing native completed projection verifier."""
        body = dict(schema=SCHEMA, economics_scope=SCOPE, record_id=str(trade.get('id') or ''),
            symbol=str(trade.get('code') or trade.get('stock_code') or ''), status='source_gap', reason=None,
            original_economics_scope=allocation.SCOPE, actual_execution_cost=False,
            evidence_grade='broker_confirmed_total_allocated', allocated_cost_krw=None,
            allocated_net_pnl_krw=None, allocated_profit_rate=None, cost_available_at=None,
            original_receipt_sha256=None, original_automatic_management_allowed=trade.get('main_automatic_management_allowed'),
            actual_pnl_krw=None, selector_eligible=False, allowed_runtime_apply=False, actual_order_submitted=False)
        try:
            with ExitStack() as budget:
                record = allocation._record(body['record_id'])
                day = date.fromisoformat(completion_date).isoformat()
                directory = self.cost_root / 'runtime/initial_quantity_research_costs' / day
                if not (directory / 'index.json').exists():
                    body['reason'] = 'holding_research_cost_index_missing'
                    return _seal(body)
                index = self._read(directory / 'index.json', official.MAX_BYTES)
                if (index.get('schema') != allocation.INDEX_SCHEMA or index.get('completion_date') != day
                    or index.get('index_sha256') != digest({k:v for k,v in index.items() if k != 'index_sha256'})
                    or not isinstance(index.get('receipts'), dict) or len(index['receipts']) > allocation.MAX_RECORDS):
                    raise ValueError('holding_research_cost_index_invalid')
                sha = index['receipts'].get(record)
                if sha is None:
                    body['reason'] = 'holding_research_cost_receipt_missing'
                    return _seal(body)
                if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
                    raise ValueError('holding_research_cost_reference_invalid')
                del index
                receipt = self._read(directory / 'generations' / (sha + '.json'), allocation.CACHED_RECEIPT_MAX_BYTES)
                if digest(receipt) != sha:
                    raise ValueError('holding_research_cost_receipt_changed')
                # Hold a separate receipt reservation: the bounded LRU may
                # evict it while official sources are validated below.
                budget.enter_context(Claim(len(json.dumps(receipt).encode()) * 16 + 4096))
                legs = []
                from . import research_storage as storage
                for name in ('buy_fill_legs', 'sell_fill_legs'):
                    claim = budget.enter_context(Claim(0))
                    values = []
                    iterator = (storage.iter_tree(assembly_root, trade[name + '_ref'])
                                if trade.get(name + '_ref') and assembly_root is not None
                                else iter(trade.get(name) or []))
                    for leg in iterator:
                        size = len(json.dumps(leg).encode())
                        if claim.size + size * 8 > allocation.CACHED_RECEIPT_MAX_BYTES * 8:
                            raise ValueError('holding_research_cost_fill_partition_required')
                        claim.grow(size * 8)
                        values.append(leg)
                    legs.append(values)
                buys, sells = legs
                parsed_buys, parsed_sells = allocation._legs(buys), allocation._legs(sells)
                permitted = {'source_gap_sell_leg_configured_cost', 'source_gap_actual_cost_missing',
                             'source_gap_broker_actual_cost_missing', 'source_gap_exact_cost_missing'}
                if (trade.get('status') != 'COMPLETED' or not parsed_buys or not parsed_sells
                    or set(trade.get('strict_completion_reasons') or []) - permitted
                    or trade.get('sell_quantity_conserved') is not True
                    or trade.get('position_residual_qty') != 0
                    or trade.get('terminal_decision_authority') != 'broker_sell_fill_observation_only'
                    or trade.get('terminal_population_scope') != 'real_record_bound'
                    or trade.get('sell_time_forbidden_for_intraday_horizon') is not False):
                    raise ValueError('holding_research_cost_terminal_unverified')
                custody = self._custody(trade, buys)
                verified = allocation.validate_research_cost(receipt, record_id=record, symbol=body['symbol'],
                    buy_legs=buys, sell_legs=sells, custody_rows=custody, completion_date=day,
                    knowledge_cutoff=self.cutoff)
                if verified['status'] != 'research_cost_allocated':
                    body.update(status='pending' if verified['status'] == 'research_cost_pending' else 'source_gap',
                                reason=verified['reason'])
                    return _seal(body)
                completed = max(leg[0] for leg in parsed_sells)
                if completed != allocation._clock(verified['completed_at']):
                    raise ValueError('holding_research_cost_terminal_clock_mismatch')
                for key, parsed, column in (('buy_qty',parsed_buys,1),('sell_qty',parsed_sells,1),
                        ('buy_amount_krw',parsed_buys,2),('sell_amount_krw',parsed_sells,2)):
                    if official.number(verified[key]) != sum((leg[column] for leg in parsed), Decimal(0)):
                        raise ValueError('holding_research_cost_fill_economics_mismatch')
                if min(leg[0] for leg in parsed_sells) < max(leg[0] for leg in parsed_buys):
                    raise ValueError('holding_research_cost_interleaved_buy_sell_unsupported')
                self._official(verified, buys, sells)
                body.update(status='research_cost_allocated', reason=None,
                    original_receipt_sha256=verified['receipt_sha256'], original_receipt_content_sha256=sha,
                    original_receipt_path=str(directory / 'generations' / (sha + '.json')),
                    allocated_cost_krw=verified['allocated_fees_taxes_krw'],
                    allocated_net_pnl_krw=verified['allocated_net_pnl_krw'], allocated_profit_rate=verified['allocated_profit_rate'],
                    cost_available_at=verified['cost_available_at'], completed_at=verified['completed_at'],
                    account_scope_sha256=verified['account_scope_sha256'], buy_fill_identity=verified['buy_fill_identity'],
                    sell_fill_identity=verified['sell_fill_identity'], custody_sha256=verified['custody_sha256'],
                    registry_generation=self.registry_generation, quantity=verified['buy_qty'], buy_basis_krw=verified['buy_amount_krw'],
                    allocation_algorithm=verified['allocation_algorithm'],
                    source_parts=[{key:part[key] for key in ('source_date','source_sha256','observed_at',
                        'broker_account_sha256','allocated_cost_krw','confirmed_total_cost_krw')}
                        for part in verified['sources']])
        except (ValueError, TypeError, KeyError, OSError, ArithmeticError) as exc:
            if 'shared_research_budget' in str(exc):
                raise
            body.update(status='source_gap', reason=str(exc))
        return _seal(body)


def valid_annotation(value, position):
    """Sealed assembly metadata is diagnostic only, never actual-PnL authority."""
    record = str(position.get('position_key') or '').removeprefix('alternative:')
    return (isinstance(value, dict) and value.get('schema') == SCHEMA
        and value.get('artifact_sha256') == digest({k:v for k,v in value.items() if k != 'artifact_sha256'})
        and value.get('record_id') == record and value.get('symbol') == position.get('symbol')
        and value.get('economics_scope') == SCOPE and value.get('original_economics_scope') == allocation.SCOPE
        and value.get('actual_execution_cost') is False and value.get('actual_pnl_krw') is None
        and value.get('evidence_grade') == 'broker_confirmed_total_allocated'
        and value.get('selector_eligible') is False and value.get('allowed_runtime_apply') is False
        and value.get('actual_order_submitted') is False)
