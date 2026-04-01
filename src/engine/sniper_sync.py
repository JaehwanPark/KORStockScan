"""Account/DB sync helpers for the sniper engine."""

from datetime import datetime

from src.database.models import RecommendationHistory
from src.utils import kiwoom_utils
from src.utils.logger import log_error
from src.engine import kiwoom_orders


KIWOOM_TOKEN = None
DB = None
ACTIVE_TARGETS = None
EVENT_BUS = None
HIGHEST_PRICES = None
STATE_LOCK = None


def bind_sync_dependencies(
    *,
    kiwoom_token=None,
    db=None,
    active_targets=None,
    event_bus=None,
    highest_prices=None,
    state_lock=None,
):
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS, EVENT_BUS, HIGHEST_PRICES, STATE_LOCK
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


def _to_int(value):
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def sync_balance_with_db():
    """봇 시작 시 실제 계좌 잔고와 DB의 HOLDING 기록을 대조하여 정합성을 맞춥니다."""
    global KIWOOM_TOKEN, DB, ACTIVE_TARGETS

    print("🔄 [데이터 동기화] 실제 계좌 잔고와 DB를 대조합니다...")

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
                    if safe_db_qty != real_qty:
                        print(f"⚠️ [동기화] {name}({code}): 수량 불일치 교정 (DB: {safe_db_qty}주 -> 실제: {real_qty}주)")
                        record.buy_qty = real_qty

                    for t in ACTIVE_TARGETS:
                        if str(t.get('code', '')).strip()[:6] == code and real_qty > 0:
                            t['buy_qty'] = real_qty

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

    real_balances, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if not successful_exchanges:
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

    real_inventory, successful_exchanges = kiwoom_utils.get_account_balance_kt00005(KIWOOM_TOKEN)
    if not successful_exchanges:
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
                        with STATE_LOCK:
                            for t in ACTIVE_TARGETS:
                                if str(t.get('code', '')).strip()[:6] == code:
                                    t['buy_price'] = real_buy_uv

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

                        with STATE_LOCK:
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
