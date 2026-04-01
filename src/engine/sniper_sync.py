"""Account/DB sync helpers for the sniper engine."""

import time
from datetime import datetime
from math import isclose

from src.database.models import RecommendationHistory
from src.engine.sniper_scale_in_utils import record_add_history_event, find_latest_open_add_order_no
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.engine import kiwoom_orders


KIWOOM_TOKEN = None
DB = None
ACTIVE_TARGETS = None
EVENT_BUS = None
HIGHEST_PRICES = None
STATE_LOCK = None
CONF = None


def bind_sync_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    active_targets=None,
    event_bus=None,
    highest_prices=None,
    state_lock=None,
    conf=None,
):
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS, HIGHEST_PRICES, STATE_LOCK, CONF
    if kiwoom_token is not None:
        KIWOOM_TOKEN = kiwoom_token
    if db is not None:
        DB = db
    if active_targets is not None:
        ACTIVE_TARGETS = active_targets
    if event_bus is not None:
        EVENT_BUS = event_bus
    if highest_prices is not None:
        HIGHEST_PRICES = highest_prices
    if state_lock is not None:
        STATE_LOCK = state_lock
    if conf is not None:
        CONF = conf


def _refresh_kiwoom_token(reason, error_detail=None):
    """토큰 문제 발생 시 즉시 재발급 시도."""
    global KIWOOM_TOKEN, CONF
    detail_str = f" | detail={error_detail}" if error_detail else ""
    log_info(f"🔄 [TOKEN 재발급] 사유={reason}{detail_str}")
    if not CONF:
        log_error("❌ [TOKEN 재발급] CONF가 없어 재발급 불가")
        return None
    new_token = kiwoom_utils.get_kiwoom_token(CONF)
    if new_token:
        KIWOOM_TOKEN = new_token
        log_info("✅ [TOKEN 재발급] 성공")
    else:
        log_error("❌ [TOKEN 재발급] 실패")
    return new_token


def _detect_auth_failure():
    """최근 잔고 조회 오류에서 인증 실패 여부를 판단."""
    errors = kiwoom_orders.get_last_inventory_errors()
    for err in errors:
        msg = str(err.get('return_msg', ''))
        code = str(err.get('return_code', ''))
        if '8005' in code or 'Token' in msg or '토큰' in msg or '인증' in msg:
            return True, err
    return False, errors[0] if errors else None


def _to_int(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def _to_float(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _with_state_lock():
    class _DummyLock:
        def __enter__(self):
            return None
        def __exit__(self, exc_type, exc, tb):
            return False

    return STATE_LOCK if STATE_LOCK is not None else _DummyLock()


def _reconcile_scale_in_lock(record, real_qty, real_buy_uv):
    """
    계좌 truth 기준으로 scale_in_locked 자동 해제 여부를 판단합니다.
    - DB/메모리/계좌 수량과 평단이 정합하면 자동 해제
    - 불일치가 남아 있으면 lock 유지
    """
    target_stock = next(
        (t for t in (ACTIVE_TARGETS or []) if str(t.get('code', '')).strip()[:6] == str(record.stock_code).strip()[:6]),
        None,
    )
    mem_pending = bool(target_stock.get('pending_add_order')) if target_stock else False
    if mem_pending:
        return False

    db_qty = _to_int(record.buy_qty)
    db_avg = _to_float(record.buy_price)
    qty_match = db_qty == real_qty
    avg_match = (real_buy_uv <= 0) or isclose(db_avg, float(real_buy_uv), rel_tol=0.0, abs_tol=1.0)

    if qty_match and avg_match:
        reconcile_order_no = find_latest_open_add_order_no(DB, getattr(record, 'id', None))
        record.scale_in_locked = False
        if target_stock:
            target_stock['scale_in_locked'] = False
        record_add_history_event(
            DB,
            recommendation_id=getattr(record, 'id', None),
            stock_code=record.stock_code,
            stock_name=record.stock_name,
            strategy=getattr(record, 'strategy', None),
            add_type=getattr(record, 'last_add_type', None),
            event_type='RECONCILED',
            order_no=reconcile_order_no,
            executed_qty=real_qty,
            executed_price=real_buy_uv,
            new_buy_price=record.buy_price,
            new_buy_qty=record.buy_qty,
            add_count_after=getattr(record, 'add_count', 0),
            reason='scale_in_lock_auto_release',
        )
        log_info(f"✅ [ADD_RECONCILED] {record.stock_name}({record.stock_code}) scale_in_locked 자동 해제")
        return True

    log_info(
        f"⚠️ [ADD_RECONCILE_PENDING] {record.stock_name}({record.stock_code}) "
        f"lock 유지 (db_qty={db_qty}, real_qty={real_qty}, db_avg={db_avg}, real_avg={real_buy_uv})"
    )
    return False


def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS

    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")
    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(초기 동기화)")
        if not KIWOOM_TOKEN:
            log_error("❌ [동기화 중단] 토큰 재발급 실패")
            return

    real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
    if not successful_exchanges:
        last_errors = kiwoom_orders.get_last_inventory_errors()
        if last_errors:
            log_info(f"⚠️ [동기화 원인] 잔고 조회 실패 상세: {last_errors}")
        auth_failed, auth_err = _detect_auth_failure()
        if auth_failed:
            _refresh_kiwoom_token("인증 실패(8005)", auth_err)
            if KIWOOM_TOKEN:
                real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
        print("⚠️ [동기화 보류] 모든 거래소 잔고 조회 실패, 1회 재시도합니다.")
        time.sleep(1.5)
        real_inventory, successful_exchanges = kiwoom_orders.get_my_inventory(KIWOOM_TOKEN)
        if not successful_exchanges:
            print("⚠️ [동기화 보류] 모든 거래소 잔고 조회 실패, 동기화를 건너뜁니다.")
            return

    real_codes = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_inventory
        if item.get('code')
    }

    def get_exchange(code):
        is_nxt = DB.get_latest_is_nxt(code)
        return 'NXT' if is_nxt else 'KRX'

    try:
        with DB.get_session() as session:
            db_holdings = session.query(RecommendationHistory).filter_by(status='HOLDING').all()

            for record in db_holdings:
                code = str(record.stock_code).strip()[:6]
                name = record.stock_name
                safe_db_qty = _to_int(record.buy_qty)

                if code not in real_codes:
                    exchange = get_exchange(code)
                    if exchange in successful_exchanges:
                        print(f"⚠️ [동기화] {name}({code}): 실제 잔고 0주. 상태를 COMPLETED로 강제 변경.")
                        record.status = 'COMPLETED'
                        if not record.sell_time:
                            record.sell_time = datetime.now()

                        target = next((t for t in ACTIVE_TARGETS if str(t.get('code', '')).strip()[:6] == code), None)
                        if target:
                            target['status'] = 'COMPLETED'
                    else:
                        print(f"⚠️ [동기화] {name}({code}): {exchange} 거래소 잔고 조회 실패로 상태 변경 생략.")
                else:
                    real_qty = _to_int(real_codes[code].get('qty', 0))
                    raw_price = (
                        real_codes[code].get('buy_price')
                        or real_codes[code].get('purchase_price')
                        or real_codes[code].get('pchs_avg_pric')
                        or 0
                    )
                    real_buy_uv = _to_int(raw_price)
                    if safe_db_qty != real_qty:
                        print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                        record.buy_qty = real_qty

                    for t in ACTIVE_TARGETS:
                        if str(t.get('code', '')).strip()[:6] == code and real_qty > 0:
                            t['buy_qty'] = real_qty

                    if real_buy_uv > 0 and not isclose(_to_float(record.buy_price), float(real_buy_uv), rel_tol=0.0, abs_tol=1.0):
                        record.buy_price = real_buy_uv
                        for t in ACTIVE_TARGETS:
                            if str(t.get('code', '')).strip()[:6] == code and real_qty > 0:
                                t['buy_price'] = real_buy_uv

                    if bool(record.scale_in_locked):
                        _reconcile_scale_in_lock(record, real_qty, real_buy_uv)

    except Exception as exc:
        log_error(f"🚨 DB 동기화 중 에러 발생: {exc}")

    print("✅ [데이터 동기화] 완료. 봇 메모리가 실제 계좌와 완벽히 일치합니다.")


def sync_state_with_broker():
    """
    [Fallback 로직] 웹소켓 재접속 시 증권사 실제 잔고를 불러와
    누락된 체결 건(BUY_ORDERED -> HOLDING)을 강제로 동기화합니다.
    """
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS

    print("🔄 [상태 동기화] 웹소켓 재접속 감지! 증권사 잔고와 봇 상태를 대조합니다...")
    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(상태 동기화)")

    real_balances, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if not successful_exchanges:
        log_info("⚠️ [상태 동기화] 잔고 조회 실패 -> 토큰 재발급 후 재시도")
        _refresh_kiwoom_token("잔고 조회 실패(상태 동기화)")
        if KIWOOM_TOKEN:
            real_balances, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
        print("⚠️ [상태 동기화] 모든 거래소 잔고 조회 실패. 다음 턴에 재시도합니다.")
        return

    balance_dict = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_balances
        if item.get('code')
    }

    synced_count = 0

    try:
        with DB.get_session() as session:
            pending_records = session.query(RecommendationHistory).filter_by(status='BUY_ORDERED').all()

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in balance_dict:
                    real_data = balance_dict[code]
                    cur_qty = _to_int(real_data.get('qty', 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get('buy_price')
                            or real_data.get('purchase_price')
                            or real_data.get('pchs_avg_pric')
                            or 0
                        )
                        buy_uv = _to_int(raw_price)

                        print(f"✅ [동기화 완료] 누락 체결 확인! {record.stock_name}({code}) | 수량: {cur_qty} | 평단가: {buy_uv:,}원")

                        record.status = 'HOLDING'
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        if not record.buy_time:
                            record.buy_time = datetime.now()

                        for t in ACTIVE_TARGETS:
                            if str(t.get('code', '')).strip()[:6] == code:
                                t['status'] = 'HOLDING'
                                t['buy_price'] = buy_uv
                                t['buy_qty'] = cur_qty

                        synced_count += 1

    except Exception as exc:
        log_error(f"🚨 [상태 동기화] DB 처리 중 에러 발생: {exc}")

    if synced_count > 0:
        msg = f"🔄 <b>[시스템 복구 알림]</b>\n웹소켓 단절 시간 동안 체결된 <b>{synced_count}건</b>의 종목을 성공적으로 동기화하여 감시망에 편입했습니다."
        EVENT_BUS.publish('TELEGRAM_BROADCAST', {'message': msg, 'audience': 'ADMIN_ONLY', 'parse_mode': 'HTML'})
    else:
        print("✅ [상태 동기화] 누락된 체결 건이 없습니다.")


# =====================================================================
# 🔄 3분 주기 강제 계좌 동기화 (웹소켓 영수증 누락 방어)
# =====================================================================

def periodic_account_sync():
    """
    주기적으로 실제 증권사 잔고를 조회하여, 웹소켓 체결 누락으로 인해
    DB와 메모리가 꼬이는 현상을 강제로 바로잡습니다.
    """
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, HIGHEST_PRICES, STATE_LOCK

    if not KIWOOM_TOKEN:
        _refresh_kiwoom_token("토큰 없음(정기 동기화)")
    real_inventory, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if not successful_exchanges:
        log_info("⚠️ [정기 동기화] 잔고 조회 실패 -> 토큰 재발급 후 재시도")
        _refresh_kiwoom_token("잔고 조회 실패(정기 동기화)")
        if KIWOOM_TOKEN:
            real_inventory, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
        print("⚠️ [정기 동기화] 모든 거래소 잔고 조회 실패, 동기화를 건너뜁니다.")
        return

    real_codes = {
        str(item.get('code', '')).strip()[:6]: item
        for item in real_inventory
        if item.get('code')
    }

    def get_exchange(code):
        is_nxt = DB.get_latest_is_nxt(code)
        return 'NXT' if is_nxt else 'KRX'

    synced_count = 0

    try:
        with DB.get_session() as session:
            # 1️⃣ [매도 누락 방어] DB엔 HOLDING/SELL_ORDERED 인데, 실제 계좌엔 없는 경우 -> 팔렸음 (COMPLETED)
            active_records = session.query(RecommendationHistory).filter(
                RecommendationHistory.status.in_(['HOLDING', 'SELL_ORDERED'])
            ).all()

            for record in active_records:
                code = str(record.stock_code).strip()[:6]

                if code not in real_codes:
                    exchange = get_exchange(code)
                    if exchange in successful_exchanges:
                        print(f"⚠️ [정기 동기화] {record.stock_name}({code}) 잔고 없음. 매도 영수증 누락으로 판단하여 COMPLETED 강제 전환.")
                        record.status = 'COMPLETED'
                        record.sell_time = datetime.now()

                        with STATE_LOCK:
                            target_stock = next((t for t in ACTIVE_TARGETS if str(t.get('code', '')).strip()[:6] == code), None)
                            estimated_sell_price = target_stock.get('sell_target_price', 0) if target_stock else 0
                            fallback_price = record.buy_price if record.buy_price is not None else 0

                            if not record.sell_price or record.sell_price == 0:
                                record.sell_price = estimated_sell_price if estimated_sell_price > 0 else fallback_price

                            if record.buy_price and record.buy_price > 0 and record.sell_price and record.sell_price > 0:
                                record.profit_rate = round(((record.sell_price - record.buy_price) / record.buy_price) * 100, 2)

                            if target_stock:
                                target_stock['status'] = 'COMPLETED'

                            if HIGHEST_PRICES is not None:
                                HIGHEST_PRICES.pop(code, None)
                        synced_count += 1
                    else:
                        print(f"⚠️ [정기 동기화] {record.stock_name}({code}): {exchange} 거래소 잔고 조회 실패로 상태 변경 생략.")

                else:
                    real_data = real_codes[code]
                    real_qty = _to_int(real_data.get('qty', 0))

                    raw_price = (
                        real_data.get('buy_price')
                        or real_data.get('purchase_price')
                        or real_data.get('pchs_avg_pric')
                        or 0
                    )
                    real_buy_uv = _to_int(raw_price)

                    if real_qty > 0 and _to_int(record.buy_qty) != real_qty:
                        print(f"🔄 [정기 동기화] {record.stock_name} 수량 오차 교정 (기존: {_to_int(record.buy_qty)}주 ➡️ 실제: {real_qty}주)")
                        record.buy_qty = real_qty
                        with STATE_LOCK:
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['buy_qty'] = real_qty

                    if real_buy_uv > 0 and record.buy_price != real_buy_uv:
                        print(f"🔄 [정기 동기화] {record.stock_name} 매입단가 오차 교정 (기존: {record.buy_price}원 ➡️ 실제: {real_buy_uv}원)")
                        record.buy_price = real_buy_uv
                        with _with_state_lock():
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['buy_price'] = real_buy_uv

                    if bool(record.scale_in_locked):
                        _reconcile_scale_in_lock(record, real_qty, real_buy_uv)

            # 2️⃣ [매수 누락 방어] DB엔 BUY_ORDERED 인데, 실제 잔고에 들어와 있는 경우 -> 샀음 (HOLDING)
            pending_records = session.query(RecommendationHistory).filter_by(status='BUY_ORDERED').all()

            for record in pending_records:
                code = str(record.stock_code).strip()[:6]

                if code in real_codes:
                    real_data = real_codes[code]
                    cur_qty = _to_int(real_data.get('qty', 0))

                    if cur_qty > 0:
                        raw_price = (
                            real_data.get('buy_price')
                            or real_data.get('purchase_price')
                            or real_data.get('pchs_avg_pric')
                            or 0
                        )
                        buy_uv = _to_int(raw_price)

                        print(f"⚠️ [정기 동기화] {record.stock_name}({code}) 매수 체결 확인! HOLDING 강제 전환 (평단가 {buy_uv:,}원)")

                        record.status = 'HOLDING'
                        record.buy_price = buy_uv
                        record.buy_qty = cur_qty
                        record.buy_time = datetime.now()

                        with _with_state_lock():
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['status'] = 'HOLDING'
                                    t['buy_price'] = buy_uv
                                    t['buy_qty'] = cur_qty

                        synced_count += 1

    except Exception as exc:
        log_error(f"🚨 정기 계좌 동기화 DB 에러: {exc}")

    if synced_count > 0:
        print(f"🔄 [정기 동기화 완료] 총 {synced_count}건의 웹소켓 누락 체결 상태를 바로잡았습니다.")
    else:
        pass  # 조용히 넘어갑니다. (로그 기록 안 함)
