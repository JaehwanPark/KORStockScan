"""Big-Bite trigger detector (runtime-ready helper).

This module is intentionally separate from sniper_condition_handlers.py to avoid
changing existing flow. It provides a minimal stateful detector that can be
integrated later where exec ticks + orderbook snapshots are available.
"""

import time
from typing import Tuple, Dict, Any

from src.utils.constants import TRADING_RULES


# -----------------------------
# Runtime-state helpers
# -----------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _get_or_init_state(runtime_state: dict, code: str) -> dict:
    code = str(code).strip()[:6]
    per_code = runtime_state.setdefault('big_bite', {}).setdefault(code, {})
    per_code.setdefault('recent_exec_ticks', [])
    per_code.setdefault('last_orderbook_snapshot', None)
    per_code.setdefault('last_big_bite_at', 0)
    per_code.setdefault('armed_big_bite_until', 0)
    per_code.setdefault('trigger_price', 0)
    per_code.setdefault('trigger_vpw', 0.0)
    per_code.setdefault('trigger_ts', 0)
    per_code.setdefault('trigger_info', {})
    return per_code


def _prune_ticks(ticks: list, window_ms: int, now_ms: int) -> list:
    if not ticks:
        return []
    cutoff = now_ms - window_ms
    return [t for t in ticks if t.get('ts_ms', 0) >= cutoff]


# -----------------------------
# Direction inference
# -----------------------------

def _normalize_side(side: str) -> str:
    if not side:
        return ''
    s = str(side).strip().upper()
    if s in {'BUY', 'B', 'BID'}:
        return 'BUY'
    if s in {'SELL', 'S', 'ASK'}:
        return 'SELL'
    if '매수' in s:
        return 'BUY'
    if '매도' in s:
        return 'SELL'
    return ''


def _infer_side_from_orderbook(price: int, orderbook: dict) -> str:
    if not orderbook:
        return ''
    asks = orderbook.get('asks') or []
    bids = orderbook.get('bids') or []
    ask1 = asks[0].get('price') if asks else None
    bid1 = bids[0].get('price') if bids else None
    if price and ask1 and price >= ask1:
        return 'BUY'
    if price and bid1 and price <= bid1:
        return 'SELL'
    return ''


# -----------------------------
# Main detector
# -----------------------------

def detect_big_bite_trigger(code, tick_data: dict, ws_data: dict, runtime_state: dict) -> Tuple[bool, Dict[str, Any]]:
    """Detect Big-Bite trigger using aggregated ticks within a short window.

    Args:
        code: stock code
        tick_data: execution tick (dict). Expected keys (best-effort):
            - price / exec_price / curr
            - qty / volume / exec_qty
            - side / buy_flag / exec_type (BUY/SELL/매수/매도)
            - ts_ms / timestamp (optional; otherwise uses now)
        ws_data: latest WS snapshot (dict) with orderbook
            - ws_data['orderbook']['asks'|'bids'] each list of dicts with price/volume
        runtime_state: caller-maintained dict used to store per-code buffers

    Returns:
        (is_triggered, info)
    """
    info = {
        'buy_flag': False,
        'agg_value': 0,
        'agg_volume': 0,
        'impact_ratio': 0.0,
        'window_ms': int(getattr(TRADING_RULES, 'BIG_BITE_WINDOW_MS', 500) or 500),
        'reason': 'insufficient_data',
    }

    if not code or tick_data is None or runtime_state is None:
        return False, info

    window_ms = int(getattr(TRADING_RULES, 'BIG_BITE_WINDOW_MS', 500) or 500)
    min_value = int(getattr(TRADING_RULES, 'BIG_BITE_MIN_VALUE', 50_000_000) or 50_000_000)
    impact_ratio_min = float(getattr(TRADING_RULES, 'BIG_BITE_IMPACT_RATIO', 0.30) or 0.30)
    cooldown_ms = int(getattr(TRADING_RULES, 'BIG_BITE_COOLDOWN_MS', 1500) or 1500)

    now_ms = _now_ms()
    per_code = _get_or_init_state(runtime_state, code)

    # update last orderbook snapshot
    if ws_data and ws_data.get('orderbook'):
        per_code['last_orderbook_snapshot'] = ws_data.get('orderbook')

    last_big_bite_at = int(per_code.get('last_big_bite_at', 0) or 0)
    if now_ms - last_big_bite_at < cooldown_ms:
        info['reason'] = 'cooldown'
        return False, info

    # Extract tick fields
    price = tick_data.get('price') or tick_data.get('exec_price') or tick_data.get('curr') or 0
    qty = tick_data.get('qty') or tick_data.get('volume') or tick_data.get('exec_qty') or 0
    try:
        price = int(float(price or 0))
    except Exception:
        price = 0
    try:
        qty = int(float(qty or 0))
    except Exception:
        qty = 0

    side = _normalize_side(tick_data.get('side') or tick_data.get('buy_flag') or tick_data.get('exec_type'))
    if not side:
        side = _infer_side_from_orderbook(price, per_code.get('last_orderbook_snapshot') or {})

    # If still unknown, be conservative
    if side != 'BUY':
        info['reason'] = 'not_buy_side'
        return False, info

    ts_ms = tick_data.get('ts_ms') or tick_data.get('timestamp') or now_ms
    try:
        ts_ms = int(ts_ms)
    except Exception:
        ts_ms = now_ms

    # Buffer ticks and prune
    ticks = per_code.get('recent_exec_ticks', [])
    ticks.append({'ts_ms': ts_ms, 'price': price, 'qty': qty, 'side': side})
    ticks = _prune_ticks(ticks, window_ms, now_ms)
    per_code['recent_exec_ticks'] = ticks

    # Aggregate BUY-only
    buy_ticks = [t for t in ticks if t.get('side') == 'BUY']
    agg_volume = sum(int(t.get('qty', 0) or 0) for t in buy_ticks)
    agg_value = sum(int(t.get('qty', 0) or 0) * int(t.get('price', 0) or 0) for t in buy_ticks)

    # Impact ratio
    orderbook = per_code.get('last_orderbook_snapshot') or {}
    asks = orderbook.get('asks') or []
    ask_1_3_total = 0
    for i in range(min(3, len(asks))):
        ask_1_3_total += int(asks[i].get('volume', 0) or 0)

    if ask_1_3_total <= 0:
        info.update({
            'buy_flag': True,
            'agg_value': agg_value,
            'agg_volume': agg_volume,
            'impact_ratio': 0.0,
            'reason': 'ask_depth_empty',
        })
        return False, info

    impact_ratio = agg_volume / ask_1_3_total

    info.update({
        'buy_flag': True,
        'agg_value': agg_value,
        'agg_volume': agg_volume,
        'impact_ratio': impact_ratio,
        'window_ms': window_ms,
    })

    if agg_value < min_value:
        info['reason'] = 'below_min_value'
        return False, info
    if impact_ratio < impact_ratio_min:
        info['reason'] = 'below_impact_ratio'
        return False, info

    # Triggered
    per_code['last_big_bite_at'] = now_ms
    info['reason'] = 'buy_aggressive + agg_value + ask_impact'
    return True, info


def arm_big_bite_if_triggered(stock, code, ws_data: dict, tick_data: dict, runtime_state: dict) -> Tuple[bool, Dict[str, Any]]:
    """Arm a short confirmation window when Big-Bite trigger fires in valid position."""
    window_ms = int(getattr(TRADING_RULES, 'BIG_BITE_CONFIRM_MS', 1000) or 1000)
    now_ms = _now_ms()
    per_code = _get_or_init_state(runtime_state, code)

    triggered, info = detect_big_bite_trigger(code, tick_data, ws_data, runtime_state)
    if not triggered:
        return False, info

    # position filter (breakout context)
    pos_tag = str((stock or {}).get('position_tag', '') or '').upper()
    scanner_price = (stock or {}).get('buy_price') or 0
    curr_price = int(float((ws_data or {}).get('curr', 0) or 0))
    position_ok = (
        any(key in pos_tag for key in ('VCP', 'BREAK', 'BRK', 'SHOOT', 'NEXT', 'SCANNER'))
        or (scanner_price > 0 and curr_price >= scanner_price * 0.995)
    )
    if not position_ok:
        info = dict(info)
        info['reason'] = 'position_filter_reject'
        return False, info

    per_code['armed_big_bite_until'] = now_ms + window_ms
    per_code['trigger_price'] = curr_price
    per_code['trigger_vpw'] = float((ws_data or {}).get('v_pw', 0.0) or 0.0)
    per_code['trigger_ts'] = now_ms
    per_code['trigger_info'] = info

    info = dict(info)
    info['armed_until_ms'] = per_code['armed_big_bite_until']
    return True, info


def confirm_big_bite_follow_through(stock, code, ws_data: dict, runtime_state: dict) -> Tuple[bool, Dict[str, Any]]:
    """Confirm follow-through after Big-Bite arm window."""
    now_ms = _now_ms()
    per_code = _get_or_init_state(runtime_state, code)

    armed_until = int(per_code.get('armed_big_bite_until', 0) or 0)
    if armed_until <= 0:
        return False, {'reason': 'not_armed'}

    if now_ms > armed_until:
        per_code['armed_big_bite_until'] = 0
        return False, {'reason': 'confirm_window_expired'}

    # thresholds
    min_vpw = float(getattr(TRADING_RULES, 'BIG_BITE_MIN_VPW_AFTER_TRIGGER', 110) or 110)
    base_max_chase_pct = float(getattr(TRADING_RULES, 'BIG_BITE_MAX_CHASE_PCT', 0.8) or 0.8)
    min_ask_1_3 = int(getattr(TRADING_RULES, 'BIG_BITE_MIN_ASK_1_3_TOTAL', 8000) or 8000)
    max_surge = float(getattr(TRADING_RULES, 'MAX_SCALP_SURGE_PCT', 20.0) or 20.0)
    max_intraday = float(getattr(TRADING_RULES, 'MAX_INTRADAY_SURGE', 15.0) or 15.0)

    curr_price = int(float((ws_data or {}).get('curr', 0) or 0))
    open_price = float((ws_data or {}).get('open', curr_price) or curr_price)
    fluctuation = float((ws_data or {}).get('fluctuation', 0.0) or 0.0)
    current_vpw = float((ws_data or {}).get('v_pw', 0.0) or 0.0)

    trigger_price = float(per_code.get('trigger_price', 0) or 0)
    chase_pct = ((curr_price - trigger_price) / trigger_price * 100) if trigger_price > 0 else 0.0
    intraday_surge = ((curr_price - open_price) / open_price * 100) if open_price > 0 else fluctuation

    if fluctuation >= max_surge or intraday_surge >= max_intraday:
        return False, {'reason': 'overheated'}
    if current_vpw < min_vpw:
        return False, {'reason': 'vpw_not_sustained', 'current_vpw': current_vpw}

    orderbook = (ws_data or {}).get('orderbook') or {}
    asks = orderbook.get('asks') or []
    ask_1_3_total = sum(int((asks[i].get('volume', 0) or 0)) for i in range(min(3, len(asks))))
    if ask_1_3_total < min_ask_1_3:
        return False, {'reason': 'ask_depth_too_thin', 'ask_1_3_total': ask_1_3_total}

    dynamic_max_chase_pct = get_dynamic_big_bite_max_chase_pct(ws_data, base_max_chase_pct)
    if chase_pct > dynamic_max_chase_pct:
        return False, {
            'reason': 'chase_too_large',
            'chase_pct': chase_pct,
            'max_chase_pct': dynamic_max_chase_pct,
        }

    ask_tot = float((ws_data or {}).get('ask_tot', 0) or 0)
    bid_tot = float((ws_data or {}).get('bid_tot', 0) or 0)
    if bid_tot > 0 and ask_tot > 0:
        imbalance = bid_tot / ask_tot
        if imbalance < 0.6:
            return False, {'reason': 'orderbook_deteriorated', 'imbalance': imbalance}

    if trigger_price > 0 and curr_price < trigger_price:
        return False, {'reason': 'breakout_failed'}

    return True, {
        'reason': 'follow_through_ok',
        'current_vpw': current_vpw,
        'chase_pct': chase_pct,
        'ask_1_3_total': ask_1_3_total,
        'max_chase_pct': dynamic_max_chase_pct,
    }


def get_dynamic_big_bite_max_chase_pct(ws_data: dict, base_max: float) -> float:
    """Minimal dynamic tuning based on orderbook depth (conservative)."""
    ws_data = ws_data or {}
    orderbook = ws_data.get('orderbook') or {}
    asks = orderbook.get('asks') or []
    ask_1_3_total = sum(int((asks[i].get('volume', 0) or 0)) for i in range(min(3, len(asks))))

    # 기본 캡
    min_cap = max(0.3, base_max * 0.5)
    max_cap = min(1.5, base_max * 1.5)

    if ask_1_3_total >= 20000:
        return min(max_cap, base_max + 0.3)
    if ask_1_3_total >= 12000:
        return min(max_cap, base_max + 0.15)
    if ask_1_3_total <= 5000:
        return max(min_cap, base_max - 0.2)
    if ask_1_3_total <= 8000:
        return max(min_cap, base_max - 0.1)
    return base_max

def build_tick_data_from_ws(ws_data: dict) -> dict:
    """Best-effort adapter from WS snapshot to tick_data shape.

    Notes:
    - Kiwoom real-time trade fields for '0B' are not parsed in this codebase.
    - We keep a raw snapshot under ws_data['last_trade_tick'] in KiwoomWSManager.
    - This adapter uses known 0B field mappings when present.
    """
    ws_data = ws_data or {}
    last_tick = ws_data.get('last_trade_tick') or {}
    raw = last_tick.get('values') or {}

    def _safe_int(val, default=0):
        try:
            return int(float(str(val).replace('+', '').replace(',', '').strip()))
        except Exception:
            return default

    # Known 0B mappings (provided): 20=체결시간, 10=현재가, 15=거래량(+매수/-매도)
    price = raw.get('10')
    if price is None:
        price = ws_data.get('curr')

    qty_raw = raw.get('15') or 0
    qty_val = _safe_int(qty_raw, 0)
    side = 'BUY' if str(qty_raw).strip().startswith('+') else ('SELL' if str(qty_raw).strip().startswith('-') else '')

    return {
        'price': _safe_int(price, 0),
        'qty': abs(int(qty_val or 0)),
        'side': side,
        'ts_ms': int((last_tick.get('ts', time.time())) * 1000),
        'raw': raw,
    }

# -----------------------------
# Notes on available data
# -----------------------------
# - Orderbook snapshot source: KiwoomWSManager stores ws_data['orderbook'] with asks/bids.
# - Execution tick source:
#   - If using account execution stream (real_type '00'), only own orders are available.
#   - Market-wide trade ticks (0B) can be used via build_tick_data_from_ws():
#       20=체결시간, 10=현재가, 15=거래량(+매수/-매도)
