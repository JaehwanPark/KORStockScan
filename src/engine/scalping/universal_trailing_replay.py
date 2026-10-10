"""Main all-market execution-path replay with explicit actual/CF populations.

Consumes bounded route-owned tick/depth projections. OHLC, unidentified AI or
missing fill/cost evidence are censored, never invented terminal economics.
The trading decision and M1 classifier are shared with runtime.
"""
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
import math
from zoneinfo import ZoneInfo

from src.trading.market.session_contract import resolve_market_session
from .pre_submit_delay_initial_policy import digest, number
from .trailing_exit_decision import evaluate_trailing_take_profit, evaluate_exit_deferral
from .trailing_mechanical_strength import classify_ws_history, _rows_by_item, HISTORY_LIMIT
from .trailing_mechanical_policy import normalize_values, START_MARKETS, market_values_hash, classifier_hash
from .trailing_threshold_policy import market_type_at, closed_exit_gap
from .trailing_situation_policy import PreparedPin, pin_context, validate_pin

SCHEMA = "main_universal_trailing_replay_v1"
MAX_EVENTS = 100000
MAX_POSITIONS = 20000
SLIPPAGE_BPS = (0, 30, 100)
MAX_QUOTE_ENVELOPE_BYTES = 12 * 1024
WS_PROJECTION_SCHEMA = 'main_m1_route_touch_tape_projection_v1'


def quote_source_digest(event):
    # The later AI receipt is an overlay on an already sealed quote. Including
    # its input hash in the quote hash would create a circular receipt.
    return digest({key:value for key,value in event.items()
                   if key not in {'source_sha256', 'holding_ai'}})


def holding_ai_context_digest(*, identity, crossing_at, event, market, values,
                              classifier_config, strength, pin, quantity, remaining,
                              basis, allocated_cost, sell_rate, peak, profit,
                              peak_profit, armed):
    """Bind an observed vote to the candidate's exact first-crossing input.

    This diagnostic hash never substitutes for a recorded AI request/response.
    Missing original binding censors the candidate, even on the same quote.
    """
    return digest(dict(schema='main_trailing_ai_crossing_context_v1',
        position_key=identity, crossing_at=crossing_at,
        quote_source_sha256=event['source_sha256'], market=market,
        policy_values=dict(values), m1_classifier_sha256=classifier_hash(classifier_config),
        strength=asdict(strength), situation_pin=asdict(pin),
        quantity=quantity, remaining=remaining, basis=basis,
        allocated_cost=allocated_cost, sell_rate=sell_rate, peak=peak,
        profit=profit, peak_profit=peak_profit, armed=armed))


def compact_ws(ws):
    """Project only fields consumed by M1, with its existing history limit.

    This is an internal source projection, not a Kiwoom packet parser. One
    route's touch/tape arrays avoid repeating unrelated routes, raw payloads
    and ten-level books in every holding event. Invalid direction stays invalid.
    """
    items = ws.get('last_realtime_type_item') or {}
    routes = ws.get('last_realtime_type_market_route') or {}
    suffixes = ws.get('last_realtime_type_market_suffix') or {}
    item = str(items.get('0D') or '').strip().upper()
    epoch = ws.get('market_data_transport_epoch')
    route_key = str(suffixes.get('0D') or 'KRX') + '|' + str(routes.get('0D') or '')
    depths = _rows_by_item(ws.get('recent_depth_ticks_by_route'), item, epoch, route_key)
    trades = _rows_by_item(ws.get('recent_trade_ticks_by_route'), item, epoch, route_key)
    def touch(row, key):
        levels = row.get(key)
        first = levels[0] if isinstance(levels, list) and levels else None
        return [first.get('price'), first.get('quantity')] if isinstance(first, dict) else [None, None]
    sources, qualities = [], []
    def origin(rows,key):
        return min((r[key] for r in rows),default=0) if all(type(r[key]) is int for r in rows) else 0
    def shift(raw,base):
        return raw-base if base else raw
    clock_origin = origin(depths+trades,'received_at_ms')
    depth_origin = origin(depths,'route_sequence')
    trade_origin = origin(trades,'route_sequence')
    def intern(values, value):
        if value not in values:
            values.append(value)
        return values.index(value)
    return {'schema':WS_PROJECTION_SCHEMA, 'item':item, 'epoch':epoch, 'route_key':route_key,
        'items':{k:items.get(k) for k in ('0B','0D')},
        'routes':{k:routes.get(k) for k in ('0B','0D')},
        'suffixes':{k:suffixes.get(k) for k in ('0B','0D')},
        'clock_origin_ms':clock_origin, 'depth_sequence_origin':depth_origin, 'trade_sequence_origin':trade_origin,
        'depths':[[shift(r['route_sequence'],depth_origin), shift(r['received_at_ms'],clock_origin), *touch(r,'bid_levels'), *touch(r,'ask_levels')]
                  for r in depths],
        'trades':[[shift(r['route_sequence'],trade_origin), shift(r['received_at_ms'],clock_origin), r.get('price'), r.get('volume'), r.get('aggressor_side'),
                   intern(sources, r.get('aggressor_source')), intern(qualities, r.get('aggressor_quality'))]
                  for r in trades], 'sources':sources, 'qualities':qualities}


def expand_ws(ws):
    if ws.get('schema') != WS_PROJECTION_SCHEMA:
        return ws
    clock_origin = ws.get('clock_origin_ms',0)
    depth_origin = ws.get('depth_sequence_origin',0)
    trade_origin = ws.get('trade_sequence_origin',0)
    if any(type(value) is not int or value<0 for value in (clock_origin,depth_origin,trade_origin)):
        raise ValueError('main_m1_compact_origin_invalid')
    if (not isinstance(ws.get('depths'), list) or not isinstance(ws.get('trades'), list)
            or len(ws['depths']) > HISTORY_LIMIT or len(ws['trades']) > HISTORY_LIMIT
            or not isinstance(ws.get('sources'), list) or not isinstance(ws.get('qualities'), list)
            or len(ws['sources']) > HISTORY_LIMIT or len(ws['qualities']) > HISTORY_LIMIT
            or any(not isinstance(r, list) or len(r) != 6 for r in ws['depths'])
            or any(not isinstance(r, list) or len(r) != 7 or type(r[5]) is not int or type(r[6]) is not int
                   or not 0 <= r[5] < len(ws['sources']) or not 0 <= r[6] < len(ws['qualities'])
                   for r in ws['trades'])):
        raise ValueError('main_m1_compact_source_invalid')
    def restore(raw,base):
        return raw+base if base else raw
    depths = [dict(item=ws['item'], transport_epoch=ws['epoch'], route_sequence=restore(r[0],depth_origin), received_at_ms=restore(r[1],clock_origin),
                   bid_levels=[dict(price=r[2],quantity=r[3])], ask_levels=[dict(price=r[4],quantity=r[5])])
              for r in ws['depths']]
    trades = [dict(item=ws['item'], transport_epoch=ws['epoch'], route_sequence=restore(r[0],trade_origin), received_at_ms=restore(r[1],clock_origin),
                   price=r[2],volume=r[3],aggressor_side=r[4],aggressor_source=ws['sources'][r[5]],
                   aggressor_quality=ws['qualities'][r[6]]) for r in ws['trades']]
    return dict(last_realtime_type_item=ws['items'], last_realtime_type_market_route=ws['routes'],
                last_realtime_type_market_suffix=ws['suffixes'], market_data_transport_epoch=ws['epoch'],
                recent_depth_ticks_by_route={ws['route_key']:depths}, recent_trade_ticks_by_route={ws['route_key']:trades})


def _route_depths(ws, route, item, epoch):
    ws = expand_ws(ws)
    suffix = (ws.get('last_realtime_type_market_suffix') or {}).get('0D')
    route_key = str(suffix).upper() + '|' + str(route).upper()
    return [row for key, rows in (ws.get('recent_depth_ticks_by_route') or {}).items()
            if str(key).upper() == route_key for row in rows
            if row.get('item') == item and row.get('transport_epoch') == epoch
            and str(row.get('market_route', route)).upper() == str(route).upper()]


def _quote_projection(ws_data, *, known_at, event_at, route, item, transport_epoch,
                     sequence, bid, ask, bid_qty, peak, quantity, coverage_complete, entry_cost_model=None):
    """Reuse Main's supplied snapshot; no WS getter or independent sampling."""
    import json
    if not isinstance(ws_data, dict) or coverage_complete is not True:
        return {'status':'source_gap', 'reason':'shared_quote_coverage_unverified'}
    view = compact_ws(ws_data)
    depths = _route_depths(view, route, item, transport_epoch)
    latest = max(depths, key=lambda row:number(row.get('received_at_ms')) or 0, default={})
    native_sequence = latest.get('route_sequence')
    if type(native_sequence) is not int or native_sequence <= 0:
        return {'status':'source_gap', 'reason':'shared_quote_native_depth_unobserved'}
    try:
        sha = digest(view)
    except (ValueError, TypeError, OverflowError):
        return {'status':'source_gap', 'reason':'shared_quote_serialization_invalid'}
    quote = dict(kind='QUOTE', event_at=event_at, known_at=known_at, source_kind='tick_depth',
        coverage_complete=True, route=route, item=item, transport_epoch=transport_epoch,
        sequence=native_sequence, sample_sequence=sequence,
        max_quote_age_sec=.7, bid=bid, ask=ask, bid_qty=bid_qty, trade_peak_price=peak,
        ws_data=view, quote_snapshot_sha256=sha, sell_execution_plan={
            'valid_until':number(event_at) + .7 if number(event_at) is not None else None,
            'quote_source_sha256':sha, 'limit_price':bid, 'quantity':quantity})
    quote['entry_cost_model'] = entry_cost_model
    quote['source_sha256'] = digest(quote)
    try:
        encoded = json.dumps(quote, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    except (ValueError, TypeError, OverflowError):
        return {'status':'source_gap', 'reason':'shared_quote_serialization_invalid'}
    if len(encoded) > MAX_QUOTE_ENVELOPE_BYTES:
        return {'status':'source_gap', 'reason':'shared_quote_envelope_budget_exceeded'}
    return quote


def quote_projection(ws_data, **kwargs):
    # Optional diagnostics never suppress mandatory holding telemetry.
    try:
        return _quote_projection(ws_data, **kwargs)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return {'status':'source_gap', 'reason':'shared_quote_projection_contract_invalid'}


def completed_census(trades, *, incumbent):
    """Every completed Main ID remains visible, including unallocated costs."""
    positions, paths = [], {}
    for trade in trades:
        identity = str(trade.get('id') or trade.get('record_id') or '')
        if not identity:
            raise ValueError('universal_completed_population_identity_missing')
        events, entry_context, entry_pin = [], trade.get('trailing_entry_context'), trade.get('trailing_situation_pin')
        for event in trade.get('timeline') or []:
            if not isinstance(event, dict) or event.get('stage') != 'scalp_trailing_input_transition':
                continue
            source = (event.get('fields') or {}).get('universal_trailing_quote')
            if isinstance(source, str):
                import json
                try:
                    source = json.loads(source)
                except ValueError:
                    source = None
            if isinstance(source, dict) and source.get('kind') == 'QUOTE':
                events.append(source)
                for key in ('trailing_entry_context', 'trailing_situation_pin'):
                    value = (event.get('fields') or {}).get(key)
                    if isinstance(value, str) and len(value.encode()) <= 2048:
                        import json
                        try:
                            value = json.loads(value)
                        except ValueError:
                            value = None
                    if isinstance(value, dict):
                        if key == 'trailing_entry_context' and entry_context is None:
                            entry_context = value
                        elif key == 'trailing_situation_pin' and entry_pin is None:
                            entry_pin = value
        model = trade.get('trailing_replay_cost_model') or (events[0].get('entry_cost_model') if events else None) or {}
        first_quote = events[0] if events else {}
        legs = trade.get('buy_fill_legs') or []
        # An identifiable malformed fill must remain a source-gap row; it
        # cannot abort the entire completed-position census or become a
        # partially reconstructed entry with invented quantity/cost.
        valid_legs = isinstance(legs, list) and all(isinstance(leg, dict) for leg in legs)
        first_leg = legs[0] if valid_legs and legs else {}
        reconstructed_adds = []
        entry = number(trade.get('first_buy_at_epoch'))
        if legs:
            try:
                if not valid_legs:
                    raise ValueError('buy_fill_legs_contract_invalid')
                first = first_leg
                def stamp(text):
                    value = datetime.fromisoformat(text)
                    return (value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp()
                entry = stamp(first['at'])
                for leg in legs[1:]:
                    add_cost = leg.get('buy_cost_krw')
                    if (add_cost is None and model.get('allocation') == 'frozen_configured_round_trip_rate_on_sell_model_only'
                            and number(model.get('buy_cost_krw')) == 0):
                        add_cost = 0
                    reconstructed_adds.append(dict(kind='ADD', event_at=stamp(leg['at']), known_at=stamp(leg['at']),
                        qty=leg['qty'], buy_amount_krw=leg['amount_krw'], buy_cost_krw=add_cost,
                        buy_generation_sha256=digest(leg)))
                # Ordering is proven by the canonical fill/event timestamps.
                events = sorted(events + reconstructed_adds, key=lambda row:row['known_at'])
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                entry = None
        sell_clocks = []
        try:
            for leg in trade.get('sell_fill_legs') or []:
                value = datetime.fromisoformat(leg['at'])
                sell_clocks.append((value.replace(tzinfo=ZoneInfo('Asia/Seoul')) if value.tzinfo is None else value).timestamp())
        except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
            sell_clocks = []
        positions.append(dict(position_key=identity, evidence_kind='actual_completed', owner='main',
            automatic_management_allowed=trade.get('main_automatic_management_allowed') is True,
            entry_at=entry, qty=first_leg.get('qty') if legs else trade.get('buy_fill_quantity'),
            buy_basis_krw=first_leg.get('amount_krw') if legs else trade.get('buy_fill_amount'), cost_model=model,
            route=trade.get('entry_quote_route') or first_quote.get('route'),
            item=trade.get('entry_quote_item') or first_quote.get('item'),
            terminal_status=trade.get('status'), actual_cost_reconciliation=trade.get('actual_cost_reconciliation'),
            operating_ai_required=trade.get('holding_ai_required', True),
            holding_ai_policy_sha256=trade.get('holding_ai_policy_sha256')))
        positions[-1].update(entry_context=entry_context, situation_pin=entry_pin,
                             completion_at=max(sell_clocks) if sell_clocks else None)
        paths[identity] = events
    if incumbent is None:
        body = {'schema':SCHEMA, 'status':'source_gap', 'reason':'approved_parent_receipt_missing',
                'population_ids':sorted(row['position_key'] for row in positions),
                'common_ids':[], 'actual_cost_status_counts':dict(Counter(
                    (row.get('actual_cost_reconciliation') or {}).get('status', 'actual_cost_unallocated') for row in positions)),
                'runtime_effect':False, 'allowed_runtime_apply':False}
        return {**body, 'artifact_sha256':digest(body)}
    return summarize_partitions(positions, paths, {}, incumbent=incumbent)


@dataclass(frozen=True)
class PreparedPath:
    events: tuple
    features: tuple
    classifier_sha256: str
    pair_stream: object = None
    observation_end_at: float | None = None

    def __len__(self):
        return len(self.events)

    def pairs(self):
        return self.pair_stream() if self.pair_stream is not None else zip(self.events, self.features)


@dataclass(frozen=True)
class PreparedVariants:
    """Source-verified feature projections, independent of numeric candidates."""
    paths: dict


def prepare_path(events, *, classifier_config=None):
    """M1 and session feature state is shared only within one position path."""
    state, features = {}, []
    for event in events:
        known = number(event.get('known_at'))
        market = market_type_at(known) if known is not None else None
        permission = resolve_market_session(datetime.fromtimestamp(known, ZoneInfo('Asia/Seoul'))) if known is not None else None
        strength = None
        age = number(event.get('max_quote_age_sec'))
        if event.get('kind') == 'QUOTE' and known is not None and age is not None and 0 < age <= .7 and event.get('ws_data') is not None:
            try:
                strength, state = classify_ws_history(expand_ws(event['ws_data']), state, now_ms=int(known * 1000),
                    max_quote_age_ms=int(age * 1000), market=market, config=(classifier_config or {}).get(market))
            except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
                strength = None
        features.append((market, permission, strength))
    return PreparedPath(tuple(events), tuple(features), classifier_hash(classifier_config))


def replay(position, events, vector, *, typed_policy=None, classifier_config=None):
    """Isolate a malformed identified row without dropping unrelated IDs."""
    try:
        return _replay(position, events, vector, typed_policy=typed_policy, classifier_config=classifier_config)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return dict(identity=str(position.get('position_key') or position.get('opportunity_id') or ''),
                    evidence_kind=position.get('evidence_kind'), status='source_gap',
                    reason='replay_row_contract_invalid:' + type(exc).__name__,
                    actual_pnl_krw=None, modeled_net_pnl_krw=None,
                    actual_order_submitted=False, allowed_runtime_apply=False)


def _replay(position, events, vector, *, typed_policy=None, classifier_config=None):
    """First crossing, current session permission, partial execution, censoring."""
    identity = str(position.get("position_key") or position.get("opportunity_id") or "")
    evidence = position.get("evidence_kind")
    result = {"identity": identity, "evidence_kind": evidence, "status": "source_gap",
              "reason": None, "actual_pnl_krw": None, "modeled_net_pnl_krw": None,
              "actual_order_submitted": False, "allowed_runtime_apply": False}
    def stop(reason, *, status="source_gap"):
        return {**result, "status": status, "reason": reason}
    if (not identity or evidence not in {"actual_completed", "actual_entry_alternative_exit", "enter_pass_opportunity_cf"}
        or position.get("owner") != "main" or position.get("automatic_management_allowed") is not True):
        return stop("position_identity_or_custody_unverified")
    entry = number(position.get("entry_at"))
    qty, basis = number(position.get("qty")), number(position.get("buy_basis_krw"))
    model = position.get("cost_model") or {}
    buy_cost, sell_rate = number(model.get("buy_cost_krw")), number(model.get("sell_cost_rate"))
    if (entry is None or qty is None or basis is None or buy_cost is None or sell_rate is None
        or entry <= 0 or qty <= 0 or not qty.is_integer() or basis <= 0 or buy_cost < 0 or not 0 <= sell_rate < .05
        or not model.get("source_sha256")):
        return stop("execution_plan_or_cost_model_missing")
    if model.get('known_at') is not None and (number(model['known_at']) is None or number(model['known_at']) > entry):
        return stop('cost_model_not_known_at_entry')
    if evidence == "enter_pass_opportunity_cf" and (
        position.get("entry_action") != "ENTER_NOW" or position.get("auxiliary_effective_verdict") != "PASS"
        or not position.get("machine_observation_sha256") or not position.get("native_evaluation_id")
        or not position.get("execution_plan_sha256") or not position.get("entry_depth_verified")
    ):
        return stop("exact_enter_pass_plan_or_cf_entry_missing")
    if len(events) > MAX_EVENTS or set(vector) != set(START_MARKETS):
        return stop("replay_input_budget_or_market_contract_invalid")
    vector = {market: normalize_values(vector[market]) for market in START_MARKETS}
    if evidence == "actual_completed":
        actual = position.get("actual_cost_reconciliation") or {}
        if (position.get("terminal_status") != "COMPLETED" or actual.get("status") != "actual_cost_reconciled"
            or number(actual.get("exact_pnl_krw")) is None
            or number(actual.get("exact_profit_rate")) is None
            or not actual.get('receipt_sha256') or not actual.get('raw_sha256')):
            return stop("actual_completed_cost_or_terminal_unverified")
        result["actual_pnl_krw"] = number(actual["exact_pnl_krw"])
    remaining, proceeds, allocated_cost, peak, armed = qty, 0.0, buy_cost, basis / qty, False
    crossing, deferred = None, None
    used, last_clock, last_sequence, last_epoch = set(), entry, None, None
    strength_counts = Counter()
    pin = position.get("situation_pin")
    if not validate_pin(pin, identity):
        pin = pin_context(None, position_key=identity, entry_at=entry)
    pin = PreparedPin.prepare(pin, identity)
    full_quantity, full_basis = qty, basis
    prepared = events if isinstance(events, PreparedPath) else prepare_path(events, classifier_config=classifier_config)
    if prepared.classifier_sha256 != classifier_hash(classifier_config):
        return stop('m1_prepared_classifier_generation_changed')
    last_quote_at = None
    for event, (market, permission, strength) in prepared.pairs():
        at, known = number(event.get("event_at")), number(event.get("known_at"))
        if at is None or known is None or at > known or known < entry:
            return stop("source_clock_invalid")
        if known < last_clock:
            return stop("source_clock_regression")
        last_clock = known
        if event.get('kind') == 'SAFETY_EXIT':
            return stop('higher_priority_safety_exit', status='censored')
        if event.get("kind") == "ADD":
            add_qty, amount = number(event.get("qty")), number(event.get("buy_amount_krw"))
            add_cost = number(event.get("buy_cost_krw"))
            if (add_qty is None or amount is None or add_cost is None or add_qty <= 0 or not add_qty.is_integer() or amount <= 0
                or add_cost < 0 or not event.get("buy_generation_sha256") or crossing is not None):
                return stop("add_state_transition_unobserved", status="censored")
            remaining += add_qty
            full_quantity += add_qty
            full_basis += amount
            allocated_cost += add_cost
            # Preserve price peak, latch and the original situation pin.
            continue
        if event.get("kind") != "QUOTE":
            continue
        if last_quote_at is None and known - entry > 2:
            return stop('first_buy_forward_path_start_unobserved', status='censored')
        if event.get("source_kind") != "tick_depth":
            return stop("bar_path_has_no_executable_ordering", status="censored")
        if (event.get('source_sha256') != quote_source_digest(event)
                or event.get("coverage_complete") is not True):
            return stop("route_path_coverage_unverified", status="censored")
        route, item, epoch, sequence = (event.get(k) for k in ("route", "item", "transport_epoch", "sequence"))
        expected_route = (position.get('routes_by_market') or {}).get(market, position.get('route'))
        expected_item = (position.get('items_by_market') or {}).get(market, position.get('item'))
        if route != expected_route or item != expected_item or not item or type(epoch) is not int or epoch < 0:
            return stop("execution_route_or_item_changed", status="censored")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence <= 0:
            return stop("source_sequence_invalid")
        source_key = (epoch, sequence)
        if source_key in used:
            return stop("source_identity_duplicate")
        used.add(source_key)
        closed_gap = (last_quote_at is not None and known - last_quote_at < 14 * 86400
                      and closed_exit_gap(last_quote_at, known))
        if last_quote_at is not None and known - last_quote_at > 2 and not closed_gap:
            return stop('open_session_forward_path_gap', status='censored')
        if last_epoch is not None and epoch != last_epoch and not closed_gap:
            return stop("transport_epoch_changed", status="censored")
        if last_sequence is not None and sequence != last_sequence + 1 and not closed_gap:
            return stop("source_sequence_gap", status="censored")
        last_epoch, last_sequence = epoch, sequence
        last_quote_at = known
        max_age = number(event.get("max_quote_age_sec"))
        if max_age is None or not 0 < max_age <= .7 or known - at > max_age:
            return stop("quote_stale_or_freshness_contract_missing", status="censored")
        if market is None or permission.blocker or not permission.exit_allowed_by_clock:
            continue
        bid, ask, depth, mark = (number(event.get(k)) for k in ("bid", "ask", "bid_qty", "trade_peak_price"))
        if bid is None or ask is None or depth is None or not 0 < bid <= ask or depth < 0 or mark is None or mark <= 0:
            return stop("executable_depth_or_peak_missing")
        peak = max(peak, mark)
        profit = round(100 * ((bid * full_quantity * (1 - sell_rate) - full_basis - allocated_cost) / full_basis), 2)
        peak_profit = round(100 * ((peak * full_quantity * (1 - sell_rate) - full_basis - allocated_cost) / full_basis), 2)
        if event.get("ws_data") is None:
            return stop("m1_raw_source_missing", status="censored")
        if event.get('quote_snapshot_sha256') != digest(event['ws_data']):
            return stop('m1_snapshot_hash_invalid', status='censored')
        ws = expand_ws(event['ws_data'])
        if (ws.get('market_data_transport_epoch') != epoch
                or (ws.get('last_realtime_type_item') or {}).get('0D') != item
                or str((ws.get('last_realtime_type_market_route') or {}).get('0D') or '').upper() != str(route).upper()):
            return stop('m1_snapshot_route_or_epoch_invalid', status='censored')
        depths = _route_depths(ws, route, item, epoch)
        latest = max(depths, key=lambda row:number(row.get('received_at_ms')) or 0, default={})
        touch = (latest.get('bid_levels') or [{}])[0]
        ask_touch = (latest.get('ask_levels') or [{}])[0]
        if (latest.get('route_sequence') != sequence or number(touch.get('price')) != bid
                or number(ask_touch.get('price')) != ask or number(touch.get('quantity')) != depth):
            return stop('m1_snapshot_execution_touch_mismatch', status='censored')
        if strength is None:
            return stop('m1_feature_path_missing', status='censored')
        strength_counts[strength.state] += 1
        values = vector[market]
        if typed_policy is not None:
            values = typed_policy.effective(market, pin, position_key=identity,
                target_date=datetime.fromtimestamp(known, ZoneInfo("Asia/Seoul")).date().isoformat())
        decision = evaluate_trailing_take_profit(peak_price=peak, executable_bid=bid,
            peak_profit_pct=peak_profit, start_pct=values["SCALP_TRAILING_START_PCT"],
            strong=strength.state == "STRONG", weak_limit_pct=values["SCALP_TRAILING_LIMIT_WEAK"],
            strong_limit_pct=values["SCALP_TRAILING_LIMIT_STRONG"], already_armed=armed)
        armed = decision.armed
        if crossing is None and decision.triggered:
            crossing = {"at": known, "market": market, "profit": profit,
                        "policy_values": dict(values), "source_sha256": event["source_sha256"]}
            if position.get('operating_ai_required'):
                crossing['input_context_sha256'] = holding_ai_context_digest(
                    identity=identity, crossing_at=known, event=event, market=market,
                    values=values, classifier_config=classifier_config, strength=strength,
                    pin=pin, quantity=full_quantity, remaining=remaining, basis=full_basis,
                    allocated_cost=allocated_cost, sell_rate=sell_rate, peak=peak,
                    profit=profit, peak_profit=peak_profit, armed=armed)
            result["first_crossing"] = crossing
        if crossing is None:
            continue
        if position.get("operating_ai_required"):
            vote = event.get("holding_ai") or {}
            if (vote.get("signal_at") != crossing["at"] or vote.get("input_source_sha256") != crossing["source_sha256"]
                or vote.get('input_context_sha256') != crossing['input_context_sha256']
                or vote.get('receipt_sha256') != digest({k:v for k,v in vote.items() if k != 'receipt_sha256'})
                or number(vote.get("known_at")) is None or not crossing['at'] <= number(vote["known_at"]) <= known
                or not isinstance(vote.get('policy_sha256'), str) or len(vote['policy_sha256']) != 64
                or any(c not in '0123456789abcdef' for c in vote['policy_sha256'])
                or vote.get("policy_sha256") != position.get("holding_ai_policy_sha256")
                or vote.get('decision') not in {'PASS', 'VETO'}):
                return stop("candidate_holding_ai_input_unobserved", status="censored")
            if (any(number(vote.get(key)) is None for key in ('started_at', 'max_defer_sec', 'max_worsen_pct'))
                    or number(vote['started_at']) > known or number(vote['max_defer_sec']) < 0 or number(vote['max_worsen_pct']) < 0):
                return stop('candidate_holding_ai_deferral_contract_invalid', status='censored')
            gate = evaluate_exit_deferral(decision=vote.get("decision"), now=known,
                signal_at=crossing["at"], started_at=number(vote.get("started_at")),
                anchor_profit=crossing["profit"], profit=profit,
                max_defer_sec=number(vote.get("max_defer_sec")), max_worsen_pct=number(vote.get("max_worsen_pct")),
                same_market=market == crossing["market"])
            if not gate.proceeds:
                deferred = gate.reason
                continue
        if depth <= 0:
            continue
        execution = event.get('sell_execution_plan') or {}
        if (number(execution.get('valid_until')) is None or number(execution['valid_until']) < known
                or execution.get('quote_source_sha256') != event.get('quote_snapshot_sha256')
                or number(execution.get('limit_price')) is None or number(execution['limit_price']) > bid
                or execution.get('quantity') != remaining):
            return stop('sell_execution_plan_unverified', status='censored')
        fill = min(remaining, depth)
        proceeds += bid * fill * (1 - sell_rate)
        remaining -= fill
        result.update(modeled_sold_qty=full_quantity - remaining, modeled_residual_qty=remaining,
                      modeled_partial_proceeds_krw=proceeds, last_sell_permission_at=known)
        if remaining == 0:
            if any(other.get('kind') == 'ADD' and (number(other.get('known_at')) or 0) > known
                   for other in prepared.events):
                return stop('candidate_exit_changes_observed_add_path', status='censored')
            modeled = proceeds - full_basis - allocated_cost
            result.update(status="modeled_full_exit", reason=None, modeled_net_pnl_krw=modeled,
                          strength_counts=dict(strength_counts), deferred_reason=deferred,
                          modeled_profit_rate_pct=100 * modeled / full_basis,
                          slippage_net_pnl_krw=[modeled - proceeds * bps / 10000 for bps in SLIPPAGE_BPS])
            return result
        # A later quote is not evidence that the same displayed depth can be
        # consumed twice. Partial execution remains a separate censored row.
        return stop('partial_depth_residual_unobserved', status='censored')
    return stop("remaining_quantity_or_forward_path_unobserved" if crossing else "trailing_crossing_not_observed",
                status="censored")


def summarize_partitions(positions, paths, candidates, *, incumbent, typed_policy=None):
    from src.engine.lifecycle.research_input_budget import Claim
    unique = set()
    for candidate in [incumbent,*candidates.values()]:
        values = candidate.get('market_values',candidate)
        config = candidate.get('classifier_parameters') if 'market_values' in candidate else None
        unique.add(market_values_hash(values,config))
    # Admit candidate result construction before allocating its dictionaries.
    # The source caller retains its separate raw/feature claim throughout.
    with Claim(len(positions)*(4096+2048*len(unique))):
        return _summarize_partitions(positions,paths,candidates,incumbent=incumbent,typed_policy=typed_policy)


def _summarize_partitions(positions, paths, candidates, *, incumbent, typed_policy=None):
    """Canonical candidates, per-position state isolation and common-ID metrics."""
    if 'incumbent' in candidates:
        raise ValueError('universal_candidate_cannot_replace_approved_parent')
    if len(positions) > MAX_POSITIONS:
        raise ValueError("universal_replay_position_budget_exceeded")
    seen, vectors, aliases = set(), {}, {}
    for name, candidate in {"incumbent": incumbent, **candidates}.items():
        values = candidate.get('market_values', candidate)
        config = candidate.get('classifier_parameters') if 'market_values' in candidate else None
        sha = market_values_hash(values, config)
        aliases[name] = sha
        vectors.setdefault(sha, (values, config))
    minimal, counters, context = {}, Counter(), {}
    for position in positions:
        identity = position.get("position_key") or position.get("opportunity_id")
        if not identity or identity in seen:
            raise ValueError("universal_replay_population_identity_invalid")
        seen.add(identity)
        events = paths.get(identity, [])
        variants = events.paths if isinstance(events, PreparedVariants) else None
        invalid_path = (not variants if isinstance(events, PreparedVariants) else
                        not isinstance(events, (list, tuple)) or any(not isinstance(event, dict) for event in events))
        if invalid_path:
            events, variants = [], None
        primary = next(iter(variants.values())) if variants else events
        if len(primary) > MAX_EVENTS:
            raise ValueError('universal_replay_path_budget_exceeded')
        prepared_paths = {}
        context[identity] = {key:position.get(key) for key in (
            'entry_at', 'evidence_kind', 'symbol', 'buy_basis_krw', 'entry_context', 'completion_at',
            'situation_pin', 'operating_ai_required')}
        if context[identity]['entry_context'] is not None:
            import json
            if len(json.dumps(context[identity]['entry_context'], allow_nan=False).encode()) > 2048:
                context[identity]['entry_context'] = None
        context[identity]['entry_at'] = number(position.get('entry_at'))
        context[identity]['observation_end_at'] = (primary.observation_end_at if variants else max(
            (number(event.get('known_at')) or 0 for event in events), default=number(position.get('entry_at')) or 0))
        # No candidate x event details retained. Each candidate state is local.
        minimal[identity] = {}
        for sha, (vector, config) in vectors.items():
            feature_sha = classifier_hash(config)
            if feature_sha not in prepared_paths:
                if variants is not None:
                    if feature_sha not in variants:
                        raise ValueError('universal_prepared_classifier_missing')
                    prepared_paths[feature_sha] = variants[feature_sha]
                else:
                    prepared_paths[feature_sha] = prepare_path(events, classifier_config=config)
            outcome = replay(position, prepared_paths[feature_sha], vector, typed_policy=typed_policy,
                             classifier_config=config)
            if invalid_path:
                outcome.update(status='source_gap', reason='identified_event_path_contract_invalid',
                               modeled_net_pnl_krw=None, actual_pnl_krw=None)
            minimal[identity][sha] = {key: outcome.get(key) for key in (
                "status", "reason", "evidence_kind", "modeled_net_pnl_krw", "modeled_profit_rate_pct",
                "actual_pnl_krw", "slippage_net_pnl_krw", "modeled_residual_qty")}
            counters[outcome["status"]] += 1
    common = sorted(identity for identity, rows in minimal.items()
                    if all(row["modeled_net_pnl_krw"] is not None for row in rows.values()))
    body = {"schema": SCHEMA, "population_ids": sorted(seen), "common_ids": common,
            "excluded_ids": sorted(seen - set(common)), "candidate_aliases": aliases,
            "unique_candidate_count": len(vectors), "minimal_results": minimal,
            'population_context':context,
            "status_counts": dict(counters), "runtime_effect": False, "allowed_runtime_apply": False}
    return {**body, "artifact_sha256": digest(body)}


def _cohort_day(row, evidence):
    completion = number(row.get('completion_at'))
    verified = evidence != 'actual_completed' or (completion is not None and completion >= row['entry_at'])
    clock = completion if evidence == 'actual_completed' and verified else row['entry_at']
    return datetime.fromtimestamp(clock, ZoneInfo('Asia/Seoul')).date().isoformat(), verified


def common_evaluation(partitions):
    """One chronological split across partitions and disjoint evidence classes.

    Economic diagnostics use common IDs, the original notional, actual costs
    where observed, and all 0/30/100bp stress cases. Nothing here selects live
    values or converts an opportunity CF into a completed broker trade.
    """
    if callable(partitions):
        return _stream_evaluation(partitions)
    if not partitions:
        return {'status':'valid_empty', 'strata':{}, 'allowed_runtime_apply':False}
    aliases = partitions[0]['candidate_aliases']
    if any(part['candidate_aliases'] != aliases for part in partitions):
        raise ValueError('universal_candidate_generation_changed_between_partitions')
    strata = {}
    context = {identity:row for part in partitions for identity,row in part['population_context'].items()}
    results = {identity:row for part in partitions for identity,row in part['minimal_results'].items()}
    common = sorted(identity for part in partitions for identity in part['common_ids'])
    for evidence in ('actual_completed', 'actual_entry_alternative_exit', 'enter_pass_opportunity_cf'):
        ids = sorted((identity for identity in common if context[identity]['evidence_kind'] == evidence),
                     key=lambda identity:(context[identity]['entry_at'], identity))
        day_receipts = {identity:_cohort_day(context[identity], evidence) for identity in ids}
        days = {identity:receipt[0] for identity,receipt in day_receipts.items()}
        ordered_days = sorted(set(days.values()))
        split = max(1, min(len(ordered_days)-1, int(len(ordered_days)*.7))) if len(ordered_days)>1 else len(ordered_days)
        train_days, holdout_days = ordered_days[:split], ordered_days[split:]
        train, holdout = ([i for i in ids if days[i] in selected] for selected in (train_days, holdout_days))
        cutoff = min((context[i]['entry_at'] for i in holdout), default=None)
        purged = [i for i in train if cutoff is not None and context[i]['observation_end_at'] >= cutoff]
        purged_set = set(purged)
        train = [i for i in train if i not in purged_set]
        metrics = {}
        for name, sha in aliases.items():
            def metric(cohort):
                values, adverse = [], []
                stress = {str(bps):[] for bps in SLIPPAGE_BPS}
                for identity in cohort:
                    row = results[identity][sha]
                    base = results[identity][aliases['incumbent']]
                    notional = number(context[identity]['buy_basis_krw'])
                    if notional is None or notional <= 0:
                        raise ValueError('universal_notional_unverified')
                    reference = max(base['modeled_net_pnl_krw'], row['actual_pnl_krw']) if evidence == 'actual_completed' else base['modeled_net_pnl_krw']
                    delta = row['modeled_net_pnl_krw'] - reference
                    values.append(delta / notional * 100)
                    if delta < 0:
                        adverse.append(identity)
                    for index,bps in enumerate(SLIPPAGE_BPS):
                        stress[str(bps)].append((row['slippage_net_pnl_krw'][index] - reference) / notional * 100)
                return {'n':len(cohort), 'paired_ev_pct':math.fsum(values)/len(values) if values else None,
                        'worst_paired_delta_pct':min(values) if values else None,
                        'worsened_ids':adverse, 'slippage_ev_pct':{key:math.fsum(v)/len(v) if v else None for key,v in stress.items()}}
            metrics[name] = {'train':metric(train), 'holdout':metric(holdout)}
        completion_verified = all(receipt[1] for receipt in day_receipts.values())
        eligible = evidence == 'actual_completed' and completion_verified and len(ordered_days)>=7 and len(train)>=30 and len(holdout)>=10 and len(holdout_days)>=2
        strata[evidence] = {'common_ids':ids, 'train_ids':train, 'holdout_ids':holdout, 'purged_ids':purged,
                           'train_days':train_days, 'holdout_days':holdout_days, 'metrics':metrics,
                           'completion_date_verified':completion_verified,
                           'existing_selector_sample_floor_met':eligible,
                           'candidate_review_required':True, 'allowed_runtime_apply':False}
    return {'status':'evaluated' if common else 'source_gap', 'common_ids':common, 'strata':strata,
            'decision_authority':'research_only_existing_selector_review_required', 'allowed_runtime_apply':False}


def _stream_evaluation(partitions):
    """Two passes of small checkpoints, never retained candidate event paths."""
    from src.engine.lifecycle.research_input_budget import Claim
    with Claim(0) as retained:
        return _stream_evaluation_bounded(partitions, retained)


def _stream_evaluation_bounded(partitions, retained):
    aliases, context, common = None, {}, set()
    for part in partitions():
        if aliases is None:
            aliases = part['candidate_aliases']
        if part['candidate_aliases'] != aliases:
            raise ValueError('universal_candidate_generation_changed_between_partitions')
        if set(context) & set(part['population_context']):
            raise ValueError('universal_replay_population_identity_invalid')
        retained.grow(len(part['population_context']) * 2560
                      + len(part['common_ids']) * len(set(aliases.values())) * 160)
        context.update(part['population_context'])
        common.update(part['common_ids'])
        if len(context) > MAX_POSITIONS:
            raise ValueError('universal_replay_position_budget_exceeded')
    if aliases is None:
        return {'status':'valid_empty', 'strata':{}, 'allowed_runtime_apply':False}
    unique = set(aliases.values())
    # The input and result allowance was admitted incrementally before keeping
    # each checkpoint's context, rather than after the whole population grew.
    return _aggregate_streamed_evaluation(partitions, aliases, context, common, unique)


def _aggregate_streamed_evaluation(partitions, aliases, context, common, unique):
    strata, membership, accumulators = {}, {}, {}
    for evidence in ('actual_completed', 'actual_entry_alternative_exit', 'enter_pass_opportunity_cf'):
        ids = sorted((i for i in common if context[i]['evidence_kind'] == evidence),
                     key=lambda i:(context[i]['entry_at'], i))
        day_receipts = {i:_cohort_day(context[i], evidence) for i in ids}
        days = {i:receipt[0] for i,receipt in day_receipts.items()}
        ordered = sorted(set(days.values()))
        split = max(1, min(len(ordered)-1, int(len(ordered)*.7))) if len(ordered)>1 else len(ordered)
        train_days, holdout_days = ordered[:split], ordered[split:]
        train = [i for i in ids if days[i] in train_days]
        holdout = [i for i in ids if days[i] in holdout_days]
        cutoff = min((context[i]['entry_at'] for i in holdout), default=None)
        purged = [i for i in train if cutoff is not None and context[i]['observation_end_at'] >= cutoff]
        purged_set = set(purged)
        train = [i for i in train if i not in purged_set]
        for cohort, identities in (('train',train), ('holdout',holdout)):
            for i in identities:
                membership[i] = (evidence, cohort)
            for sha in unique:
                accumulators[evidence,cohort,sha] = {'values':[], 'adverse':[], 'stress':[[],[],[]]}
        strata[evidence] = {'common_ids':ids, 'train_ids':train, 'holdout_ids':holdout,
            'purged_ids':purged, 'train_days':train_days, 'holdout_days':holdout_days,
            'completion_date_verified':all(receipt[1] for receipt in day_receipts.values()),
            'metrics':{}, 'existing_selector_sample_floor_met':evidence=='actual_completed'
                and all(receipt[1] for receipt in day_receipts.values())
                and len(ordered)>=7 and len(train)>=30 and len(holdout)>=10 and len(holdout_days)>=2,
            'candidate_review_required':True, 'allowed_runtime_apply':False}
    for part in partitions():
        if part['candidate_aliases'] != aliases:
            raise ValueError('universal_candidate_generation_changed_between_partitions')
        for identity, rows in part['minimal_results'].items():
            if identity not in membership:
                continue
            evidence, cohort = membership[identity]
            notional = number(context[identity]['buy_basis_krw'])
            if notional is None or notional <= 0:
                raise ValueError('universal_notional_unverified')
            base = rows[aliases['incumbent']]
            for sha in unique:
                row = rows[sha]
                reference = max(base['modeled_net_pnl_krw'], row['actual_pnl_krw']) if evidence=='actual_completed' else base['modeled_net_pnl_krw']
                delta = row['modeled_net_pnl_krw'] - reference
                acc = accumulators[evidence,cohort,sha]
                acc['values'].append(delta / notional * 100)
                if delta < 0:
                    acc['adverse'].append(identity)
                for index in range(3):
                    acc['stress'][index].append((row['slippage_net_pnl_krw'][index]-reference)/notional*100)
    for evidence, record in strata.items():
        for name, sha in aliases.items():
            record['metrics'][name] = {}
            for cohort in ('train','holdout'):
                acc = accumulators[evidence,cohort,sha]
                values = acc['values']
                record['metrics'][name][cohort] = {'n':len(values),
                    'paired_ev_pct':math.fsum(values)/len(values) if values else None,
                    'worst_paired_delta_pct':min(values) if values else None,
                    'worsened_ids':sorted(acc['adverse'], key=lambda i:(context[i]['entry_at'], i)),
                    'slippage_ev_pct':{str(bps):math.fsum(v)/len(v) if v else None
                                       for bps,v in zip(SLIPPAGE_BPS,acc['stress'])}}
    return {'status':'evaluated' if common else 'source_gap', 'common_ids':sorted(common), 'strata':strata,
        'decision_authority':'research_only_existing_selector_review_required', 'allowed_runtime_apply':False}
