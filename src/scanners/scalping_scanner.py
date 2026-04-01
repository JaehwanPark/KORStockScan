import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime

# 💡 Level 1 & 2 공통 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.engine.signal_radar import SniperRadar

# ==========================================
# 🦅 스캘핑 스캐너 (전방 탐색조)
# ==========================================
def run_scalper(is_test_mode=False):
    """
    [역할] 
    1분 주기로 시장을 스캔하여 당일 수급이 폭발하거나 급등 전조가 보이는 '초단타(Scalping)' 타겟을 발굴합니다.
    
    [아키텍처 흐름]
    1. 데이터 수집: kiwoom_utils/signal_radar(REST API)를 호출하여 등락률 상위 및 거래량 급증 종목을 가져옵니다.
    2. 필터링: is_valid_stock을 통해 동전주, ETF, 스팩주 등의 불순물을 걸러냅니다.
    3. DB 저장: 발굴된 종목을 SQLAlchemy ORM을 사용하여 안전하게 Upsert(삽입/업데이트) 합니다.
    4. 이벤트 발행: 'COMMAND_WS_REG' 이벤트를 EventBus에 쏘아, 웹소켓 모듈이 해당 종목의 실시간 틱 데이터 감시를 즉각 시작하도록 지시합니다.
    """
    print("⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (30분 주기)...")
    db = DBManager()
    event_bus = EventBus() # 💡 전역 싱글톤 이벤트 버스
    
    today = datetime.now().strftime('%Y-%m-%d')
    already_picked = set()
    last_closed_msg_time = 0 # 💡 장 마감 도배 방지용 타이머 추가

    # 💡 무한 루프 밖에서 토큰과 레이더를 한 번만 초기화하여 부하 감소
    # (실제 운영 시에는 토큰 만료를 대비한 갱신 로직이 추가로 필요할 수 있음)
    
    token = kiwoom_utils.get_kiwoom_token()
    
    if not token:
        log_error("❌ 키움 토큰 발급 실패. 스캐너를 종료합니다.")
        return

    while True:
        now = datetime.now()
        now_time = now.time()

        # 장 운영 시간 체크 (09:05 ~ 15:00) - 장 초반 감시 5분 후부터 장 마감 1시간 전까지 가동
        market_open = datetime.strptime("09:05:00", "%H:%M:%S").time()
        market_close = datetime.strptime("15:00:00", "%H:%M:%S").time()
        
        if not is_test_mode and not (market_open <= now_time <= market_close):
            if time.time() - last_closed_msg_time > 3600:
                print("🌙 장 마감 혹은 개장 전입니다. 대기 중...")
                last_closed_msg_time = time.time()
            time.sleep(60)
            continue

        # 💡 [핵심 1] 갭상승 함정을 피하기 위해 시가대비 상위(ka10028)로 전격 교체! 코스피 코스닥 전종목 탐색
        soaring_targets = kiwoom_utils.get_top_open_fluctuation_ka10028(token, mrkt_tp="000", limit=30)
        
        radar = SniperRadar(token) 
        supernova_targets = radar.find_supernova_targets(mrkt_tp="000")
        
        # 💡 [핵심 2] 대소문자 키 충돌을 완벽히 방어하는 무결점 병합 로직
        all_targets = {}
        for t in soaring_targets:
            all_targets[t['Code']] = {
                'Code': t['Code'],
                'Name': t['Name'],
                'FluRate': t.get('FluRate', 0.0), # 시가대비 등락률
                'CntrStr': t.get('CntrStr', 0.0),
                'Price': t.get('Price', 0),
                'Source': 'OPEN_TOP'
            }
            
        for t in supernova_targets:
            code = t.get('code', t.get('Code'))
            if code not in all_targets:
                all_targets[code] = {
                    'Code': code,
                    'Name': t.get('name', t.get('Name')),
                    'FluRate': t.get('flu_rate', t.get('FluRate', 0.0)),
                    'CntrStr': t.get('cntr_str', t.get('CntrStr', 150.0)),
                    'Price': t.get('Price', t.get('cur_prc', 0)),
                    'Source': 'SUPERNOVA'
                }
            else:
                all_targets[code]['Source'] = 'BOTH' # 두 조건 모두 만족하는 초강력 타겟
            
        new_codes_found = []
        max_new_codes = 5

        for code, t in all_targets.items():
            if code not in already_picked:
                curr_p = float(t.get('Price', 0))

                if not kiwoom_utils.is_valid_stock(code, t['Name'], token=token, current_price=curr_p):
                    already_picked.add(code)
                    continue

                # 💡 로그 메시지도 통일된 규격으로 수정
                print(f"🎯 [타겟 포착] {t['Name']} (등락률: +{t['FluRate']}%, 체결강도: {t['CntrStr']} | 출처: {t['Source']})")
                already_picked.add(code)
                new_codes_found.append(code)

                try:
                    with db.get_session() as session:
                        today_date = datetime.now().date()

                        record = session.query(RecommendationHistory).filter_by(
                            rec_date=today_date,
                            stock_code=code
                        ).first()

                        if record:
                            if record.status in ('WATCHING', 'COMPLETED', 'EXPIRED'):
                                record.strategy = 'SCALPING'
                                record.buy_price = 0
                                record.status = 'WATCHING'
                                record.position_tag = 'SCANNER'
                        else:
                            new_record = RecommendationHistory(
                                rec_date=today_date,
                                stock_code=code,
                                stock_name=t['Name'],
                                buy_price=0,
                                trade_type='SCALP',
                                strategy='SCALPING',
                                status='WATCHING',
                                position_tag='SCANNER'
                            )
                            session.add(new_record)
                except Exception as e:
                    log_info(f"⚠️ DB 저장 실패 ({code}): {e}")
                
                # 최대 5개까지만 선택
                if len(new_codes_found) >= max_new_codes:
                    break
            
        if new_codes_found:
            event_bus.publish("COMMAND_WS_REG", {"codes": new_codes_found})
            print(f"📡 웹소켓 감시 등록 요청 완료: {len(new_codes_found)} 종목")

        time.sleep(1800)

if __name__ == "__main__":
    run_scalper(is_test_mode=True)
