"""
[KOSDAQ 하이브리드 AI 스캐너 (Kosdaq Scanner)]

이 모듈은 장중 코스닥 시장의 수급 폭발 종목을 찾아내고, 
AI 앙상블 모델을 통해 승률이 높은 타점만 선별해내는 '정밀 타격 스캐너'입니다.

💡 아키텍처 관점에서의 핵심 설계 (Event-Driven & Decoupling):
1. 뇌(AI)의 분리:
   이 스캐너는 무거운 AI 모델을 직접 들고 있지 않습니다. 순수 추론 도구인 `ml_predictor.py`에 
   데이터프레임만 넘겨주고 확신도(Prob) 결과만 받아오는 가벼운 구조를 가집니다.
2. 입(알림)의 분리:
   타겟을 발굴했을 때 텔레그램 서버와 직접 통신(HTTP Request)하지 않습니다.
   대신 EventBus를 통해 "TELEGRAM_BROADCAST" 이벤트를 쏘아, 알림 계층(Telegram Manager)에 역할을 위임합니다.
   (네트워크 지연으로 인해 스캐너 루프가 멈추는 현상 완벽 차단)
3. 눈(감시)의 연동:
   타겟 발굴 즉시 "COMMAND_WS_REG" 이벤트를 발행하여, 
   웹소켓 모듈이 1초의 딜레이도 없이 해당 종목의 실시간 틱 데이터 추적을 시작하도록 파이프라인을 구축했습니다.
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import os
import time
from datetime import datetime

# 💡 Level 1 & 2 공통 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.utils.constants import TRADING_RULES
import src.engine.ml_predictor as ml_predictor

# ==========================================
# 🧠 KOSDAQ 하이브리드 AI 스캐너 엔진
# ==========================================
def run_kosdaq_scanner(is_test_mode=False):
    print("🚀 [KOSDAQ 스캐너] 코스닥 하이브리드 AI 감시 가동...")
    db = DBManager()
    event_bus = EventBus() # 💡 이벤트 버스 연결 (웹소켓/텔레그램 통신용)

    # 💡 [수정] ml_predictor의 순수 함수를 사용하여 AI 모델 로드
    models = ml_predictor.load_models()
    if not models: 
        print("❌ 모델 로드 실패!")
        log_error("❌ AI 모델 로드 실패. KOSDAQ 스캐너를 종료합니다.")
        return
    
    # 환경 설정 및 토큰
    while True:
        now = datetime.now()
        # 💡 [핵심 3] 테스트 모드일 때는 09:05 ~ 19:15 시간 제한을 무시하고 즉시 실행합니다!
        is_market_open = datetime.strptime("09:05:00", "%H:%M:%S").time() <= now.time() <= datetime.strptime("19:15:00", "%H:%M:%S").time()
        
        if not is_test_mode and not is_market_open:
            print("🌙 [KOSDAQ] 대기 중...")
            time.sleep(60)
            continue

        token = kiwoom_utils.get_kiwoom_token()
        if not token:
            time.sleep(10)
            continue

        print(f"\n🔍 [{now.strftime('%H:%M:%S')}] KOSDAQ 수급 주도주 정밀 스캔 중...")

        # 🚀 1. 1차 필터링 (통신 유틸리티 호출)
        # 💡 [핵심 교체] ka10027(전일대비) ➡️ ka10028(시가대비)로 전격 교체!
        raw_targets = kiwoom_utils.get_top_open_fluctuation_ka10028(token, mrkt_tp="101", limit=40)
        supernova = kiwoom_utils.scan_volume_spike_ka10023(token, mrkt_tp="101")
        
        # 💡 [핵심 교정 1] 데이터 병합 로직 완전 무결점화 (딕셔너리 키 매핑 안전하게 처리)
        all_candidate_codes = {}
        
        # 트랙 A: 시가대비 상위 종목 맵핑
        for t in raw_targets:
            all_candidate_codes[t['Code']] = {
                'Code': t['Code'], 
                'Name': t['Name'], 
                'Price': t['Price'],
                'flu_rate': t.get('FluRate', 0.0), # 💡 대문자(FluRate)를 소문자(flu_rate)로 안전하게 치환
                'spike_rate': 0.0,
                'source': 'TOP'
            }
            
        # 트랙 B: 초신성 수급 종목 병합
        for s in supernova:
            # ka10023이 소문자(code)와 대문자(Code)를 혼용할 경우를 모두 방어
            code = s.get('code', s.get('Code'))
            if code not in all_candidate_codes:
                all_candidate_codes[code] = {
                    'Code': code, 
                    'Name': s.get('name', s.get('Name')), 
                    'Price': s.get('Price', s.get('cur_prc', 0)),
                    'flu_rate': s.get('flu_rate', s.get('FluRate', 0.0)),
                    'spike_rate': s.get('spike_rate', 0.0),
                    'source': 'SUPERNOVA' 
                }
            else:
                # 이미 트랙 A로 뽑힌 종목이면, 초신성의 '거래량 급증률' 데이터만 추가 주입
                all_candidate_codes[code]['spike_rate'] = s.get('spike_rate', 0.0)

        kosdaq_picks = []
        new_codes_found = [] # 웹소켓 등록용

        # 🚀 2. 개별 종목 정밀 분석 루프
        # 💡 [핵심 교정 2] 수급 강도가 높은(spike_rate) 순서로 먼저 분석하여 API 할당량 아끼기
        sorted_candidates = sorted(all_candidate_codes.values(), key=lambda x: x.get('spike_rate', 0), reverse=True)

        for item in sorted_candidates:
            code = item['Code']
            name = item.get('Name', 'Unknown')
            curr_p = float(item.get('Price', 0))
            flu_rate = item.get('flu_rate', 0.0)
            
            # 💡 [활용 1] 리스크 필터: 음봉이거나 25% 이상 과열 종목은 AI 분석 전에 쳐냄
            if flu_rate <= 0 or flu_rate >= 25:
                continue
            
            # 불순물 필터
            if not kiwoom_utils.is_valid_stock(code, name, token=token, current_price=curr_p):
                continue
            
            # 🚀 [개선] 프로그램 매수 데이터 패키지 획득
            prm_data = kiwoom_utils.check_program_buying_ka90008(token, code)
            # 💡 [하드 필터] 프로그램 순매도가 2억(200M) 이상 쏟아지는 종목은 분석 중단
            if prm_data['net_amt'] < -200:
                continue

            # 상태 메시지 고도화 (금액 정보 결합)
            p_status = f"🔥 매수중 (+{prm_data['net_amt']}M)" if prm_data['is_buying'] else f"⚪ 관망 ({prm_data['net_amt']}M)"
            # 일봉 차트 기반 필터링
            df = kiwoom_utils.get_daily_ohlcv_ka10081_df(token, code)
            if df is None or len(df) < 60: continue
            
            curr_price = int(df['Close'].iloc[-1])
            

            
            # 수급/신용 데이터 병합
            df_investor = kiwoom_utils.get_investor_daily_ka10059_df(token, code)
            df_margin = kiwoom_utils.get_margin_daily_ka10013_df(token, code)

            # 💡 [핵심 교정] 확장된 수급 컬럼 리스트 정의
            investor_cols = [
                'Retail_Net', 'Foreign_Net', 'Inst_Net', 
                'Fin_Net', 'Trust_Net', 'Pension_Net', 'Private_Net'
            ]
            
            if not df_investor.empty: 
                df = df.join(df_investor, how='left')
            else: 
                # 💡 데이터가 없을 경우 모든 수급 주체를 0.0으로 채움
                df[investor_cols] = 0.0
             
            if not df_margin.empty: df = df.join(df_margin, how='left')
            else: df['Margin_Rate'] = 0.0
            
            df.fillna(0.0, inplace=True)


            # 💡 [활용 2] AI 피처 엔지니어링 (데이터 풍성화)
            df['Spike_Rate'] = item.get('spike_rate', 0.0)
            df['Prm_Net_Amt'] = prm_data['net_amt'] # 실시간 순매수 금액
            df['Prm_Net_Irds'] = prm_data['net_irds_amt'] # 실시간 수급 가속도

            # 🚀 3. AI 앙상블 분석 (ml_predictor 사용)
            try:
                # 💡 [수정] ml_predictor에게 순수하게 예측만 요청
                prob = ml_predictor.predict_prob_for_df(df, models)

                # 💡 [테스트용 교정] 평소에는 0.80 이상이어야 하지만, 
                # test_threshold = 0.60 if is_test_mode else 0.80
                test_threshold = 0.60 if is_test_mode else 0.58 

                # 💡 [조건 강화] AI 확률 + 프로그램 수급이 '순매수(+)' 상태일 때만 픽
                if prob >= test_threshold and prm_data['net_amt'] > 0:
                    kosdaq_picks.append({
                        'Code': code, 'Name': name, 'Price': curr_price,
                        'Prob': prob, 'Position': 'MIDDLE',
                        'ProgramStatus': p_status,
                        'SpikeRate': item.get('spike_rate', 0.0),
                        'IsSupernova': item.get('source') == 'SUPERNOVA',
                        'PrmData': prm_data # 🚀 나중에 텔레그램이나 DB에서 쓰기 위해 전체 저장
                    })
                    new_codes_found.append(code)
            except Exception as e:
                log_info(f"⚠️ {name} AI 분석 실패: {e}")

            time.sleep(0.3) # API 제한 방어

        # 🚀 4. DB 저장 및 이벤트 브로드캐스트 (ORM & EventBus)
        if kosdaq_picks:
            new_picks = []
            # 💡 [핵심] Date 객체로 변환하여 저장하는 것이 안전합니다.
            today_date = datetime.now().date() 
            
            try:
                with db.get_session() as session:
                    for r in kosdaq_picks:
                        # 💡 [교정] 모델 규격에 맞게 필터 조건 수정 (rec_date, stock_code)
                        record = session.query(RecommendationHistory).filter_by(
                            rec_date=today_date, 
                            stock_code=r['Code']
                        ).first()

                        if not record:
                            # 💡 [교정] 모든 속성명을 실제 모델 클래스의 필드명과 일치시킵니다.
                            new_record = RecommendationHistory(
                                rec_date=today_date,       #
                                stock_code=r['Code'],      #
                                stock_name=r['Name'],      #
                                trade_type='RUNNER',         # (기존 type에서 변경)
                                buy_price=r['Price'], 
                                position_tag=r['Position'], 
                                prob=r['Prob'], 
                                strategy='KOSDAQ_ML', 
                                status='WATCHING'
                            )
                            session.add(new_record)
                            new_picks.append(r)
                # (with 블록 종료 시 자동 commit)
            except Exception as e:
                log_error(f"DB 저장 에러: {e}")

            # 💡 [핵심] EventBus를 통해 텔레그램 매니저에게 알림 쏘기 (비동기)
            if new_picks:
                event_bus.publish("TELEGRAM_BROADCAST", {
                    "type": "KOSDAQ_REPORT",
                    "picks": new_picks
                })
                
                # 웹소켓 감시망에도 등록하여 실시간 타점 추적 시작!
                event_bus.publish("COMMAND_WS_REG", {"codes": new_codes_found})

        print(f"✅ [{now.strftime('%H:%M:%S')}] KOSDAQ 스캔 완료. 30분 대기...")
        time.sleep(1800)

if __name__ == "__main__":
    """
    이 블록 내부의 코드는 'python src/scanners/kosdaq_scanner.py'로 
    직접 실행할 때만 동작합니다. 
    main.py 등에서 호출할 때는 절대 실행되지 않으므로 운영계 이관 시 수정이 필요 없습니다.
    """
    
    # 1. 💡 [테스트 전용 임포트] 
    # 모듈을 임포트하는 순간, telegram_manager.py 하단의 
    # event_bus.subscribe()가 실행되어 자동으로 리스너가 깨어납니다.
    try:
        import src.notify.telegram_manager 
        print("🔔 [Test Mode] 텔레그램 알림 리스너가 가동되었습니다.")
    except ImportError as e:
        print(f"⚠️ 텔레그램 매니저 로드 실패. 알림 없이 진행합니다: {e}")

    # 2. 💡 [스캐너 실행]
    # 테스트 모드(is_test_mode=True)로 실행하여 시간 제한을 무시합니다.
    try:
        run_kosdaq_scanner(is_test_mode=True)
    except KeyboardInterrupt:
        print("\n🛑 테스트를 사용자에 의해 종료합니다.")