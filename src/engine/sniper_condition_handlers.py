"""Condition scan handlers for the sniper engine.

Also includes Big-Bite trigger detector helpers.
"""

import threading
import time
from datetime import datetime, time as dt_time
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd

from src.database.models import RecommendationHistory
from src.engine.sniper_time import _in_time_window
from src.engine.sniper_s15_fast_track import (
    _now_ts,
    _arm_s15_candidate,
    _unarm_s15_candidate,
    _is_s15_armed,
    _is_s15_reentry_blocked,
    _get_fast_state,
    _set_fast_state,
    create_s15_shadow_record,
    execute_fast_track_scalp_v2,
)
from src.engine.sniper_position_tags import (
    default_position_tag_for_strategy,
    is_default_position_tag,
    normalize_position_tag,
    normalize_strategy,
    target_identity,
)
from src.utils import kiwoom_utils
from src.utils.constants import TRADING_RULES
from src.utils.logger import log_error


KIWOOM_TOKEN = None
WS_MANAGER = None
DB = None
EVENT_BUS = None
ACTIVE_TARGETS = None
ESCAPE_MARKDOWN = None

# Flicker control (condition scan)
CONDITION_DEBOUNCE_SEC = 10          # 포착 상태 유지 시간(초) 후에만 확정
DEBOUNCE_NOISE_SEC = 3               # 3초 내 이탈은 노이즈로 즉시 폐기
DEBOUNCE_STABLE_SEC = 7              # 7초 이상 유지 후 이탈 시 60초 유지
DEBOUNCE_HOLD_SEC = 60               # 이탈 후 유지 시간
STRENGTH_SPIKE_PCT = 10.0            # 체결강도 급등(10%p 이상) 시 즉시 진입
UNMATCH_GRACE_SEC = 30               # 이탈 이벤트 후 유예 시간(초)
HYSTERESIS_USE_MA20 = False          # 3분봉 20MA 완전 이탈 체크 사용 여부 (API 호출 부담 큼)
UNMATCH_MAX_HOLD_SEC = 600           # 이탈 상태가 길게 지속될 때 최종 정리 (안전장치)

HYSTERESIS_DROP_PCT_STRONG = 0.006   # -0.6% (s15_trigger_break, scalp_candid_aggressive_01)
HYSTERESIS_DROP_PCT_MED = 0.012      # -1.2% (scalp_underpress_01, scalp_afternoon_01)
HYSTERESIS_DROP_PCT_SWING = 0.040    # -4.0% (kospi_short_swing_01, kospi_midterm_swing_01)

_CONDITION_STATE = {}
_UNMATCH_LOG_STATE = {}


def bind_condition_dependencies(
    *,
    kiwoom_token=None,
    ws_manager=None,
    db=None,
    event_bus=None,
    active_targets=None,
    escape_markdown_fn=None,
):
    global KIWOOM_TOKEN, WS_MANAGER, DB, EVENT_BUS, ACTIVE_TARGETS, ESCAPE_MARKDOWN
    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if ws_manager is not None:
        WS_MANAGER = ws_manager
    if db is not None:
        DB = db
    if event_bus is not None:
        EVENT_BUS = event_bus
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if escape_markdown_fn is not None:
        ESCAPE_MARKDOWN = escape_markdown_fn


def _escape(text):
    if ESCAPE_MARKDOWN is None:
        return text
    return ESCAPE_MARKDOWN(text)


def _should_log_unmatch_event(key, cooldown_sec=300):
    now_ts = time.time()
    last_ts = float(_UNMATCH_LOG_STATE.get(key, 0) or 0)
    if now_ts - last_ts < cooldown_sec:
        return False
    _UNMATCH_LOG_STATE[key] = now_ts
    return True


def _should_log_match_event(key, cooldown_sec=300):
    now_ts = time.time()
    last_ts = float(_UNMATCH_LOG_STATE.get(f"match:{key}", 0) or 0)
    if now_ts - last_ts < cooldown_sec:
        return False
    _UNMATCH_LOG_STATE[f"match:{key}"] = now_ts
    return True


def _condition_key(code, target_date, strategy, position_tag):
    normalized_strategy = normalize_strategy(strategy)
    normalized_tag = normalize_position_tag(normalized_strategy, position_tag)
    return (str(code).strip()[:6], str(target_date), normalized_strategy, normalized_tag)


def _find_reusable_watch_record(session, *, rec_date, stock_code, strategy):
    if DB is not None and hasattr(DB, "find_reusable_watching_record"):
        return DB.find_reusable_watching_record(
            session,
            rec_date=rec_date,
            stock_code=stock_code,
            strategy=strategy,
        )
    return session.query(RecommendationHistory).filter_by(
        rec_date=rec_date,
        stock_code=stock_code,
        strategy=strategy,
    ).first()


def _has_active_target(code, strategy):
    identity = target_identity(code, strategy)
    return any(
        target_identity(t.get('code', ''), t.get('strategy', '')) == identity
        for t in (ACTIVE_TARGETS or [])
    )


def _get_latest_price(code):
    ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
    try:
        current_price = int(float(ws_data.get('curr', 0) or 0))
    except Exception:
        current_price = 0

    if current_price > 0:
        return current_price

    try:
        best_bid = int(float(ws_data.get('best_bid', 0) or 0))
    except Exception:
        best_bid = 0
    try:
        best_ask = int(float(ws_data.get('best_ask', 0) or 0))
    except Exception:
        best_ask = 0

    if best_bid > 0 and best_ask > 0:
        return int((best_bid + best_ask) / 2)
    if best_bid > 0:
        return best_bid
    if best_ask > 0:
        return best_ask

    if KIWOOM_TOKEN:
        try:
            candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=5)
            for candle in candles or []:
                candle_close = int(float(candle.get("현재가", 0) or 0))
                if candle_close > 0:
                    return candle_close
        except Exception:
            pass

    return 0


def _get_latest_open_and_vwap(code):
    ws_data = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
    try:
        open_price = int(float(ws_data.get('open', 0) or 0))
    except Exception:
        open_price = 0

    vwap_price = 0
    if KIWOOM_TOKEN:
        try:
            candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=120)
            if candles:
                total_turnover = 0
                total_volume = 0
                for candle in candles:
                    c_close = int(float(candle.get("현재가", 0) or 0))
                    c_vol = abs(int(float(candle.get("거래량", 0) or 0)))
                    c_open = int(float(candle.get("시가", 0) or 0))
                    if open_price <= 0 and c_open > 0:
                        open_price = c_open
                    if c_close > 0 and c_vol > 0:
                        total_turnover += c_close * c_vol
                        total_volume += c_vol
                if total_volume > 0:
                    vwap_price = int(total_turnover / total_volume)
        except Exception:
            pass

    return open_price, vwap_price


def _get_latest_strength(code):
    if WS_MANAGER is None:
        return 0.0
    ws_data = WS_MANAGER.get_latest_data(code) or {}
    try:
        return float(ws_data.get('v_pw', 0) or 0.0)
    except Exception:
        return 0.0


def _passes_vwap_reclaim_precheck(code):
    current_price = float(_get_latest_price(code) or 0)
    _, vwap_price = _get_latest_open_and_vwap(code)
    vwap_price = float(vwap_price or 0)

    if current_price <= 0 or vwap_price <= 0:
        return False, {
            'reason': 'missing_price_or_vwap',
            'current_price': current_price,
            'vwap_price': vwap_price,
            'vwap_gap_pct': 0.0,
        }

    vwap_gap_pct = ((current_price - vwap_price) / vwap_price) * 100.0
    allowed = current_price > vwap_price and 0.1 <= vwap_gap_pct <= 1.0
    reason = 'ok' if allowed else 'outside_vwap_reclaim_band'
    return allowed, {
        'reason': reason,
        'current_price': current_price,
        'vwap_price': vwap_price,
        'vwap_gap_pct': vwap_gap_pct,
    }


def _get_hysteresis_drop_pct(cnd_name):
    name = (cnd_name or '').lower()
    if 's15_trigger_break' in name or 'scalp_candid_aggressive_01' in name:
        return HYSTERESIS_DROP_PCT_STRONG
    if 'scalp_underpress_01' in name or 'scalp_afternoon_01' in name:
        return HYSTERESIS_DROP_PCT_MED
    if 'kospi_short_swing_01' in name or 'kospi_midterm_swing_01' in name:
        return HYSTERESIS_DROP_PCT_SWING
    return HYSTERESIS_DROP_PCT_MED


def _big_bite_trigger_placeholder():
    """
    정의 기준: 『Big-Bite (대량 갉아먹기) 트리거』
    다음 세 가지 조건이 동시에(또는 1초 이내에) 발생할 때를 '대량 물량 소화'로 정의합니다.

    체결 방향 (Buy/Sell Flag): 체결 건이 반드시 **'매수 체결'**이어야 합니다. (체결가가 매도 1호가 이상에서 발생)

    절대 금액 기준 (Absolute Value): 단일 틱(또는 동일 밀리초 내 연속된 틱의 합)의 체결 대금이
    5,000만 원(또는 1억 원) 이상이어야 합니다. (종목 시총에 따라 파라미터화 필요)

    호가창 타격률 (Orderbook Impact): 해당 매수 체결량이 직전 수신된 매도 1~3호가 잔량 총합의
    30% 이상을 단숨에 소진시켜야 합니다.

    💡 실전 팁 (쪼개기 체결 주의): 기관이나 큰손의 시장가 주문은 증권사 시스템을 거치며 1개의 큰 틱이 아니라,
    동일한 타임스탬프(09:15:30.123)를 가진 수십 개의 틱으로 쪼개져서 웹소켓으로 날아옵니다.
    따라서 시간 단위(예: 0.5초)로 틱 볼륨을 묶어서(Aggregating) 계산해야 정확합니다.
    """
    return False


def _is_3min_ma20_broken(code):
    if not HYSTERESIS_USE_MA20:
        return False
    if KIWOOM_TOKEN is None:
        return False

    try:
        candles = kiwoom_utils.get_minute_candles_ka10080(KIWOOM_TOKEN, code, limit=120)
        if not candles or len(candles) < 60:
            return False
        df = pd.DataFrame(candles)
        if df.empty or '체결시간' not in df or '현재가' not in df:
            return False

        today = datetime.now().date()
        df['dt'] = pd.to_datetime(
            df['체결시간'].apply(lambda t: f"{today} {t}"), errors='coerce'
        )
        df = df.dropna(subset=['dt']).set_index('dt').sort_index()
        if df.empty:
            return False

        resampled = df['현재가'].resample('3T').last().dropna()
        if len(resampled) < 20:
            return False

        ma20 = resampled.rolling(20).mean().iloc[-1]
        last_close = resampled.iloc[-1]
        return last_close < ma20
    except Exception:
        return False


def resolve_condition_profile(cnd_name):
    profile = {
        'strategy': 'SCALPING',
        'trade_type': 'SCALP',
        'is_next_day_target': False,
        'position_tag': default_position_tag_for_strategy('SCALPING'),
        'start': None,
        'end': None,
        'use_debounce': True,
    }

    if "scalp_candid_aggressive_01" in cnd_name or "scalp_candid_normal_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 0), dt_time(9, 30)
    elif "scalp_open_reclaim_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 3), dt_time(9, 20)
        profile['position_tag'] = 'OPEN_RECLAIM'
        profile['use_debounce'] = False
    elif "scalp_vwap_reclaim_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(10, 0), dt_time(14, 0)
        profile['position_tag'] = 'VWAP_RECLAIM'
        profile['use_debounce'] = False
    elif "scalp_dryup_squeeze_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 30), dt_time(13, 30)
        profile['position_tag'] = 'DRYUP_SQUEEZE'
        profile['use_debounce'] = False
    elif "scalp_preclose_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(14, 30), dt_time(15, 20)
        profile['position_tag'] = 'PRECLOSE'
        profile['use_debounce'] = False
    elif "scalp_strong_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 20), dt_time(11, 0)
    elif "scalp_underpress_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 40), dt_time(13, 0)
    elif "scalp_shooting_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 40), dt_time(13, 30)
    elif "scalp_afternoon_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(13, 0), dt_time(15, 20)
    elif "kospi_short_swing_01" in cnd_name or "kospi_midterm_swing_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(14, 30), dt_time(15, 30)
        profile['strategy'] = 'KOSPI_ML'
        profile['trade_type'] = 'MAIN'
        profile['is_next_day_target'] = True
        profile['position_tag'] = default_position_tag_for_strategy('KOSPI_ML')
    elif "vcp_candid_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(15, 30), dt_time(7, 0)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'VCP_CANDID'
    elif "vcp_shooting_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 0), dt_time(15, 0)
        profile['position_tag'] = 'VCP_SHOOTING'
    elif "vcp_shooting_next_01" in cnd_name:
        profile['start'], profile['end'] = dt_time(15, 30), dt_time(23, 59, 59)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'VCP_NEXT'
    elif "s15_scan_base" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 2), dt_time(10, 30)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'S15_CANDID'
    elif "s15_trigger_break" in cnd_name:
        profile['start'], profile['end'] = dt_time(9, 5), dt_time(11, 0)
        profile['is_next_day_target'] = True
        profile['position_tag'] = 'S15_SHOOTING'
    else:
        return None

    return profile


def get_condition_target_date(is_next_day_target):
    if not is_next_day_target:
        return datetime.now().date()

    import holidays

    kr_hols = holidays.KR(years=[datetime.now().year, datetime.now().year + 1])
    hol_dates = np.array([np.datetime64(d) for d in kr_hols.keys()], dtype='datetime64[D]')
    today_np = np.datetime64(datetime.now().date())
    next_bday_np = np.busday_offset(today_np, 1, holidays=hol_dates)
    return pd.to_datetime(next_bday_np).date()


def handle_condition_matched(payload):
    """실시간 조건검색(Push)으로 날아온 종목을 즉각 감시망(WATCHING)에 올립니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS

    code = str(payload.get('code', '')).strip()[:6]
    cnd_name = str(payload.get('condition_name', '') or '')
    if not code:
        return

    now_t = datetime.now().time()

    profile = resolve_condition_profile(cnd_name)
    if not profile:
        return

    if not _in_time_window(now_t, profile['start'], profile['end']):
        return

    target_strategy = profile['strategy']
    target_trade_type = profile['trade_type']
    is_next_day_target = profile['is_next_day_target']
    target_position_tag = normalize_position_tag(target_strategy, profile['position_tag'])

    if ACTIVE_TARGETS is None or DB is None or EVENT_BUS is None:
        return

    key = _condition_key(code, get_condition_target_date(profile['is_next_day_target']), target_strategy, target_position_tag)
    now_ts = time.time()
    is_debounce_target = (
        bool(profile.get('use_debounce', True))
        and not profile['is_next_day_target']
        and target_position_tag not in ['S15_CANDID', 'S15_SHOOTING', 'VCP_NEXT']
    )
    if is_debounce_target:
        state = _CONDITION_STATE.get(key)
        if state is None:
            _CONDITION_STATE[key] = {
                'first_seen': now_ts,
                'last_seen': now_ts,
                'confirmed': False,
                'captured_price': _get_latest_price(code),
                'last_strength': _get_latest_strength(code),
                'hold_until': 0,
                'last_unmatched': 0,
                'unmatched_since': 0,
            }
            return

        state['last_seen'] = now_ts
        state['last_unmatched'] = 0
        state['unmatched_since'] = 0
        current_strength = _get_latest_strength(code)
        strength_jump = current_strength - float(state.get('last_strength') or 0.0)
        state['last_strength'] = current_strength

        if state.get('hold_until', 0) > now_ts:
            state['confirmed'] = True
        elif not state.get('confirmed'):
            if (now_ts - state['first_seen']) >= CONDITION_DEBOUNCE_SEC or strength_jump >= STRENGTH_SPIKE_PCT:
                state['confirmed'] = True
            else:
                return

    # 당일 감시망에 이미 있으면 일반 케이스는 스킵
    # 단, VCP_SHOOTING은 기존 CANDID -> SHOOTING 승격이 있으므로 통과
    if _has_active_target(code, target_strategy):
        if not is_next_day_target and target_position_tag != 'VCP_SHOOTING':
            return

    if target_position_tag == 'VWAP_RECLAIM':
        passed, precheck = _passes_vwap_reclaim_precheck(code)
        if not passed:
            log_key = f"{code}:{cnd_name}:{precheck.get('reason')}"
            if _should_log_match_event(log_key, cooldown_sec=120):
                gap_pct = float(precheck.get('vwap_gap_pct', 0.0) or 0.0)
                current_price = int(precheck.get('current_price', 0) or 0)
                vwap_price = int(precheck.get('vwap_price', 0) or 0)
                print(
                    f"⏭️ [조건검색 전처리 스킵] {code} {cnd_name} "
                    f"reason={precheck.get('reason')} curr={current_price:,} vwap={vwap_price:,} gap={gap_pct:+.2f}%"
                )
            return

    try:
        basic_info = kiwoom_utils.get_basic_info_ka10001(KIWOOM_TOKEN, code)
        name = basic_info.get('Name', code)
        target_date = get_condition_target_date(is_next_day_target)

        # =========================================================
        # ⚡ [S15 v2] Fast-Track 하이패스
        # =========================================================
        if target_position_tag == 'S15_CANDID':
            _arm_s15_candidate(code, name, cnd_name, ttl_sec=180)
            return

        if target_position_tag == 'S15_SHOOTING':
            if not _is_s15_armed(code):
                return
            if _is_s15_reentry_blocked(code):
                return
            if _get_fast_state(code):
                return

            shadow_id = create_s15_shadow_record(code, name)
            state = {
                'lock': threading.RLock(),
                'name': name,
                'status': 'ARMED',
                'buy_ord_no': '',
                'sell_ord_no': '',
                'pending_cancel_ord_no': '',
                'req_buy_qty': 0,
                'cum_buy_qty': 0,
                'cum_buy_amount': 0,
                'avg_buy_price': 0,
                'cum_sell_qty': 0,
                'cum_sell_amount': 0,
                'avg_sell_price': 0,
                'created_at': _now_ts(),
                'updated_at': _now_ts(),
                'target_price': 0,
                'stop_price': 0,
                'shadow_id': shadow_id,
                'trigger_price': 0,
            }
            _set_fast_state(code, state)

            rt = WS_MANAGER.get_latest_data(code) if WS_MANAGER else {}
            trigger_price = int(float((rt or {}).get('curr', 0) or 0))
            state['trigger_price'] = trigger_price

            threading.Thread(
                target=execute_fast_track_scalp_v2,
                args=(code, name, trigger_price, 0.10),
                daemon=False
            ).start()
            return
        # =========================================================

        with DB.get_session() as session:
            # =====================================================
            # 1) VCP_SHOOTING: 전일 VCP_CANDID가 있어야 승격
            # =====================================================
            if target_position_tag == 'VCP_SHOOTING':
                candid_record = session.query(RecommendationHistory).filter_by(
                    rec_date=target_date,
                    stock_code=code,
                    position_tag='VCP_CANDID'
                ).first()

                if not candid_record:
                    return

                candid_record.position_tag = 'VCP_SHOOTING'
                candid_record.status = 'WATCHING'
                candid_record.strategy = 'SCALPING'
                candid_record.trade_type = 'SCALP'

                if not _has_active_target(code, 'SCALPING'):
                    marcap = int(DB.get_latest_marcap(code) or 0) if DB is not None else 0
                    new_target = {
                        'id': candid_record.id,
                        'code': code,
                        'name': name,
                        'strategy': 'SCALPING',
                        'status': 'WATCHING',
                        'added_time': time.time(),
                        'position_tag': 'VCP_SHOOTING',
                        'marcap': marcap,
                    }
                    ACTIVE_TARGETS.append(new_target)
                    EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code]})

                esc_name = _escape(name)
                esc_code = _escape(code)
                msg = (
                    f"🎯 **[VCP 돌파 포착]**\n"
                    f"종목: **{esc_name} ({esc_code})**\n"
                    f"전일 CANDID 포착 후 금일 슈팅 조건을 만족하여 스캘핑 감시망에 투입됩니다."
                )
                EVENT_BUS.publish(
                    'TELEGRAM_BROADCAST',
                    {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                )
                log_key = f"{code}:{cnd_name}:vcp_shooting"
                if _should_log_match_event(log_key):
                    print(f"🎯 [조건검색 포착] {name}({code}) VCP_SHOOTING 승격 및 감시망 투입 (출처: {cnd_name})")
                return

            # =====================================================
            # 2) VCP_NEXT: 당일 SHOOTING 완료 종목만 다음날 예약
            # =====================================================
            elif target_position_tag == 'VCP_NEXT':
                today = datetime.now().date()
                today_record = session.query(RecommendationHistory).filter_by(
                    rec_date=today,
                    stock_code=code,
                    strategy='SCALPING',
                    position_tag='VCP_SHOOTING'
                ).first()

                if not today_record:
                    return

                next_record = _find_reusable_watch_record(
                    session,
                    rec_date=target_date,
                    stock_code=code,
                    strategy='SCALPING',
                )

                if not next_record:
                    new_record = RecommendationHistory(
                        rec_date=target_date,
                        stock_code=code,
                        stock_name=name,
                        buy_price=0,
                        trade_type='SCALP',
                        strategy='SCALPING',
                        status='WATCHING',
                        position_tag='VCP_NEXT'
                    )
                    session.add(new_record)

                    esc_name = _escape(name)
                    esc_code = _escape(code)
                    msg = (
                        f"🌙 **[내일의 VCP 슈팅 예약]**\n"
                        f"종목: **{esc_name} ({esc_code})**\n"
                        f"금일 슈팅 후 강력한 마감 패턴을 보여 내일 시초가 매수를 예약합니다."
                    )
                    EVENT_BUS.publish(
                        'TELEGRAM_BROADCAST',
                        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                    )
                    log_key = f"{code}:{cnd_name}:vcp_next"
                    if _should_log_match_event(log_key):
                        print(f"🌙 [조건검색 포착] {name}({code}) 익일 VCP_NEXT 예약 생성 (출처: {cnd_name})")
                return

            # =====================================================
            # 3) 일반 로직 / VCP_CANDID 저장
            # =====================================================
            record = _find_reusable_watch_record(
                session,
                rec_date=target_date,
                stock_code=code,
                strategy=target_strategy,
            )

            newly_created = False
            if not record:
                record = RecommendationHistory(
                    rec_date=target_date,
                    stock_code=code,
                    stock_name=name,
                    buy_price=0,
                    trade_type=target_trade_type,
                    strategy=target_strategy,
                    status='WATCHING',
                    position_tag=target_position_tag
                )
                session.add(record)
                session.flush()
                newly_created = True
            else:
                record.stock_name = name
                if hasattr(record, 'position_tag'):
                    record.position_tag = normalize_position_tag(record.strategy or target_strategy, record.position_tag)
                # 기존 record가 있는데 position_tag가 비어 있거나 약한 값이면 보강
                if hasattr(record, 'position_tag') and not is_default_position_tag(target_strategy, target_position_tag):
                    record.position_tag = target_position_tag

            if not is_next_day_target:
                newly_added_to_active = False
                if not _has_active_target(code, target_strategy):
                    marcap = int(DB.get_latest_marcap(code) or 0) if DB is not None else 0
                    active_strategy = normalize_strategy(record.strategy or target_strategy)
                    new_target = {
                        'id': record.id,
                        'code': code,
                        'name': name,
                        'strategy': active_strategy,
                        'status': 'WATCHING',
                        'added_time': time.time(),
                        'position_tag': normalize_position_tag(
                            active_strategy,
                            getattr(record, 'position_tag', target_position_tag) or target_position_tag,
                        ),
                        'marcap': marcap,
                    }
                    ACTIVE_TARGETS.append(new_target)
                    newly_added_to_active = True

                EVENT_BUS.publish("COMMAND_WS_REG", {"codes": [code]})
                if is_debounce_target:
                    state = _CONDITION_STATE.get(key)
                    if state:
                        state['confirmed'] = True

                if newly_created or newly_added_to_active:
                    log_key = f"{code}:{cnd_name}:{target_position_tag}:active"
                    active_strategy = normalize_strategy(record.strategy or target_strategy)
                    active_position_tag = normalize_position_tag(active_strategy, getattr(record, 'position_tag', target_position_tag))
                    if _should_log_match_event(log_key):
                        detail = f"strategy={record.strategy or target_strategy}"
                        if not is_default_position_tag(active_strategy, active_position_tag):
                            detail += f", tag={active_position_tag}"
                        print(f"🎯 [조건검색 포착] {name}({code}) 감시망 편입 완료 (출처: {cnd_name}, {detail})")

            else:
                if newly_created:
                    if target_position_tag == 'VCP_CANDID':
                        esc_name = _escape(name)
                        esc_code = _escape(code)
                        msg = (
                            f"🌙 **[VCP 스캘핑 예비 후보 포착]**\n"
                            f"종목: **{esc_name} ({esc_code})**\n"
                            f"내일 오전 VCP 슈팅 조건 만족 시 감시망에 투입됩니다."
                        )

                    elif target_position_tag == 'S15_CANDID':
                        esc_name = _escape(name)
                        esc_code = _escape(code)
                        msg = (
                            f"🌙 **[S15 스캘핑 예비 후보 포착]**\n"
                            f"종목: **{esc_name} ({esc_code})**\n"
                            f"S15 슈팅 조건 만족 시 감시망에 투입됩니다."
                        )

                    else:
                        esc_name = _escape(name)
                        esc_code = _escape(code)
                        esc_target_strategy = _escape(target_strategy)
                        msg = (
                            f"🌙 **[내일의 스윙 주도주 예약]**\n"
                            f"종목: **{esc_name} ({esc_code})**\n"
                            f"다음 영업일 감시망에 전략({esc_target_strategy})으로 자동 투입됩니다."
                        )

                    EVENT_BUS.publish(
                        'TELEGRAM_BROADCAST',
                        {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'Markdown'}
                    )
                    log_key = f"{code}:{cnd_name}:{target_position_tag}:nextday"
                    if _should_log_match_event(log_key):
                        print(f"🌙 [조건검색 포착] {name}({code}) 내일({target_date}) 감시 예약 완료 (출처: {cnd_name}, strategy={target_strategy}, tag={target_position_tag})")

    except Exception as exc:
        log_error(f"🚨 조건검색 편입 처리 에러: {exc}")


def handle_condition_unmatched(payload):
    """실시간 조건검색(D) 이탈 시 WATCHING 상태 대상을 즉시 제거합니다."""
    global DB, ACTIVE_TARGETS, EVENT_BUS

    code = str(payload.get('code', '')).strip()[:6]
    cnd_name = str(payload.get('condition_name', '') or '')
    if not code:
        return

    profile = resolve_condition_profile(cnd_name)
    if not profile:
        return

    if profile['position_tag'] == 'S15_CANDID':
        _unarm_s15_candidate(code)
        return

    if profile['position_tag'] == 'S15_SHOOTING':
        return

    if ACTIVE_TARGETS is None or DB is None or EVENT_BUS is None:
        return

    target_date = get_condition_target_date(profile['is_next_day_target'])
    target_strategy = profile['strategy']
    target_position_tag = normalize_position_tag(target_strategy, profile['position_tag'])
    key = _condition_key(code, target_date, target_strategy, target_position_tag)
    now_ts = time.time()
    state = _CONDITION_STATE.get(key)
    removed = False
    removal_reason = "unmatched"
    unmatched_age_sec = 0

    if state and not state.get('confirmed'):
        age = now_ts - state.get('first_seen', now_ts)
        if age <= DEBOUNCE_NOISE_SEC:
            _CONDITION_STATE.pop(key, None)
            return
        if age >= DEBOUNCE_STABLE_SEC:
            state['hold_until'] = now_ts + DEBOUNCE_HOLD_SEC
            return
        _CONDITION_STATE.pop(key, None)
        return

    if state and state.get('confirmed'):
        unmatched_age_sec = max(0, int(now_ts - state.get('last_seen', now_ts)))
        if state.get('hold_until', 0) > now_ts:
            return
        if state.get('last_unmatched') == 0:
            state['last_unmatched'] = now_ts
        if (now_ts - state.get('last_seen', now_ts)) < UNMATCH_GRACE_SEC:
            return

        captured_price = float(state.get('captured_price') or 0)
        current_price = float(_get_latest_price(code) or 0)
        open_price, vwap_price = _get_latest_open_and_vwap(code)
        if open_price > 0 and current_price > 0 and current_price < open_price:
            removal_reason = "below_open"
            _CONDITION_STATE.pop(key, None)
        elif vwap_price > 0 and current_price > 0 and current_price < vwap_price:
            removal_reason = "below_vwap"
            _CONDITION_STATE.pop(key, None)
        else:
            drop_pct = _get_hysteresis_drop_pct(cnd_name)
            drop_triggered = False
            if captured_price > 0 and current_price > 0:
                drop_triggered = current_price <= captured_price * (1 - drop_pct)

            ma_broken = _is_3min_ma20_broken(code) if HYSTERESIS_USE_MA20 else False

            if not drop_triggered and not ma_broken:
                if state.get('unmatched_since') == 0:
                    state['unmatched_since'] = now_ts
                if (now_ts - state['unmatched_since']) < UNMATCH_MAX_HOLD_SEC:
                    return
                removal_reason = "unmatched_timeout"
            else:
                removal_reason = "drop_trigger" if drop_triggered else "ma20_broken"
                _CONDITION_STATE.pop(key, None)

    if state:
        _CONDITION_STATE.pop(key, None)

    try:
        with DB.get_session() as session:
            query = session.query(RecommendationHistory).filter_by(
                rec_date=target_date,
                stock_code=code,
                status='WATCHING',
                strategy=target_strategy
            )

            if not is_default_position_tag(target_strategy, target_position_tag):
                query = query.filter_by(position_tag=target_position_tag)

            records = query.all()
            for record in records:
                record.status = 'EXPIRED'
                removed = True

        retained_targets = []
        for target in ACTIVE_TARGETS:
            target_code = str(target.get('code', '')).strip()[:6]
            target_status = target.get('status')
            normalized_strategy = normalize_strategy(target.get('strategy', ''))
            target_position = normalize_position_tag(normalized_strategy, target.get('position_tag'))

            should_remove = (
                target_code == code and
                target_status == 'WATCHING' and
                normalized_strategy == target_strategy and
                target_position == target_position_tag
            )

            if should_remove:
                removed = True
                continue

            retained_targets.append(target)

        if removed:
            ACTIVE_TARGETS[:] = retained_targets

            still_tracking = any(
                str(t.get('code', '')).strip()[:6] == code and
                t.get('status') not in ['COMPLETED', 'EXPIRED']
                for t in ACTIVE_TARGETS
            )
            log_key = f"{code}:{cnd_name}:{removal_reason}"
            if _should_log_unmatch_event(log_key):
                detail = f"reason={removal_reason}"
                if unmatched_age_sec > 0:
                    detail += f", unmatched_age={unmatched_age_sec}s"
                if not is_default_position_tag(target_strategy, target_position_tag):
                    detail += f", tag={target_position_tag}"
                print(f"🧹 [조건검색 실제 이탈] {code} 이탈 처리 완료 (출처: {cnd_name}, {detail})")
            if not still_tracking:
                EVENT_BUS.publish("COMMAND_WS_UNREG", {"codes": [code]})

    except Exception as exc:
        log_error(f"🚨 조건검색 이탈 처리 에러: {exc}")


# -----------------------------
# Big-Bite trigger detector
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


def detect_big_bite_trigger(code, tick_data: dict, ws_data: dict, runtime_state: dict) -> Tuple[bool, Dict[str, Any]]:
    """Detect Big-Bite trigger using aggregated ticks within a short window."""
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
    """Best-effort adapter from WS snapshot to tick_data shape."""
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
