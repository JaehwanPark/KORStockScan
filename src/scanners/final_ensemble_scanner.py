"""
[KORStockScan Final Ensemble Scanner (Batch Engine)]

이 모듈은 시스템의 최종 결정을 내리는 '장 마감(또는 장 전) 통합 스캐너' 및 '장중 지능형 재스캔' 엔진입니다.
시장 전체의 데이터를 분석하여 승률이 가장 높은 타겟을 찾아내고, 알림/감시 계층으로 데이터를 전달합니다.

💡 핵심 기능 명세 (Feature Spec):
-run_integrated_scanner() - 장 마감/장전 배치 작업:
   1. 코스피 시총/거래량 상위 150~200개 종목을 대상으로 AI 콰트로 앙상블(XGB/LGBM) 예측 수행.
   2. 지수 상대강도(RS), 단기 정배열, 수급(스마트 머니) 필터를 거쳐 'MAIN', 'RUNNER' 추천 종목을 DB에 적재.
   3. Gemini 및 OpenAI 등 LLM 합의체에 장전 브리핑 데이터(Context)를 제공.

💡 아키텍처 설계 사상 (Decoupling & Event-Driven):
- 이 파일은 오직 '계산(Compute)과 필터링(Filtering)'에만 집중합니다.
- 알림 전송: 텔레그램 서버와 직접 통신하지 않으며, 결과물은 EventBus를 통해 알림 계층으로 던집니다. (TELEGRAM_BROADCAST)
- AI 추론: 무거운 ML 예측 연산은 `ml_predictor.py` 모듈로 철저하게 위임(Delegate)하여 책임을 분리했습니다.
"""
import sys
from pathlib import Path

# ==========================================
# 🚀 [핵심 방어] 프로젝트 루트 경로를 sys.path에 동적으로 추가
# ==========================================
# 현재 파일(scanners) -> 부모(src) -> 부모(KORStockScan) 경로를 찾아냅니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

import os
import json
import warnings
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import FinanceDataReader as fdr

# 💡 Level 1 & 2 공통 모듈
from src.utils import kiwoom_utils
from src.utils.constants import TRADING_RULES, DATA_DIR, CONFIG_PATH, DEV_PATH
from src.database.db_manager import DBManager
from src.core.event_bus import EventBus
from src.model.feature_engineer import calculate_all_features

# 💡 [교정] 커스텀 로거 적용
from src.utils.logger import log_error
from src.engine.macro_briefing_complete import MacroBriefingBuilder

# 💡 [수정] 순수 AI 추론 도구
import src.engine.ml_predictor as ml_predictor

# 💡 [신규] AI 합의체 (Gemini + OpenAI) 엔진 준비
from src.engine.ai_engine import GeminiSniperEngine
from src.engine.ai_engine_openai import GPTSniperEngine 

# 💡 [핵심 교정] 텔레그램 매니저를 초대해야 수신기가 EventBus에 정상 등록됩니다!
import src.notify.telegram_manager as telegram_manager

warnings.filterwarnings('ignore')

# --- [1. 성과 복기 엔진] ---
def get_performance_report(db):
    """전일 추천 종목의 성과를 계산하여 반환합니다. (DB 스키마 변경 완벽 대응)"""
    last_date = db.get_latest_history_date()
    if not last_date: return "📊 신규 가동을 시작합니다.\n"

    try:
        history = db.get_history_by_date(last_date)
        if history is None or history.empty:
            return f"📊 <b>[전일 성적표 ({last_date})]</b>\n기록 없음\n" + "-" * 20 + "\n"
    except Exception as e:
        return f"📊 성과 데이터 로드 실패: {e}\n"

    report_msg = f"📊 <b>[전일 성적표 ({last_date})]</b>\n"

    # 💡 [핵심 교정 1] DB 스키마 버전에 따라 유연하게 컬럼명 매핑
    # 'trade_type'이나 'strategy'가 있으면 그것을 쓰고, 없으면 기존 'type' 사용
    type_col = 'trade_type' if 'trade_type' in history.columns else 'type'
    if 'strategy' in history.columns and type_col not in history.columns:
        type_col = 'strategy'
        
    code_col = 'stock_code' if 'stock_code' in history.columns else 'code'
    price_col = 'buy_price' if 'buy_price' in history.columns else 'price'

    for r_type in ['MAIN', 'RUNNER']:
        # 해당 컬럼 자체가 없으면 스킵하여 에러 방어
        if type_col not in history.columns:
            continue
            
        subset = history[history[type_col] == r_type]
        if subset.empty: continue

        profits = []
        for _, row in subset.iterrows():
            try:
                # 💡 [핵심 교정 2] 종목코드 6자리 규격화 및 가격 유효성 검사
                target_code = str(row.get(code_col, '')).replace('.0', '').strip().zfill(6)
                target_price = float(row.get(price_col, 0)) if pd.notna(row.get(price_col)) else 0
                
                # 매수가가 0이면 수익률 계산이 불가능하므로 스킵
                if target_price <= 0: continue

                try:
                    df = fdr.DataReader(target_code, start=last_date)
                    close_price = df.iloc[-1]['Close']
                except:
                    # FDR 수집 실패 시 DB 데이터로 폴백 (대소문자 완벽 대응)
                    db_last = db.get_stock_data(target_code, limit=1)
                    if db_last is not None and not db_last.empty:
                        close_price = db_last.iloc[0]['close_price'] if 'close_price' in db_last.columns else db_last.iloc[0]['Close']
                    else:
                        close_price = target_price # 최후의 수단: 본전 처리

                p = (close_price / target_price - 1) * 100
                profits.append(p)
                
            except Exception as e:
                print(f"⚠️ [{target_code}] 성과 계산 중 오류: {e}")
                continue

        if profits:
            win_rate = (len([p for p in profits if p > 0]) / len(profits)) * 100
            avg_p = sum(profits) / len(profits)
            label = "✅ 강력추천" if r_type == 'MAIN' else "🥈 아차상"
            report_msg += f"{label}: 승률 {win_rate:.0f}% / 수익 {avg_p:+.2f}%\n"

    return report_msg + "-" * 20 + "\n"

# --- [2. 메인 스캐너 엔진 (장 마감(또는 장 전) 배치 작업)] ---
def run_integrated_scanner():
    print(f"=== KORStockScan v14 (Stacking Ensemble + Event-Driven) ===")
    
    db = DBManager()
    event_bus = EventBus() # 💡 이벤트 버스 장착!

    try:
        # ==========================================
        # 1. 💡 가벼워진 ml_predictor를 통해 모델 로드
        # ==========================================
        models = ml_predictor.load_models()
        if not models:
            print("❌ AI 모델 로드 실패로 스캐너를 종료합니다.")
            return

        kiwoom_token = None
        target_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else DEV_PATH
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                CONF = json.load(f)
            kiwoom_token = kiwoom_utils.get_kiwoom_token(CONF)
        except Exception as e:
            print(f"⚠️ 키움 토큰 발급 생략 (FDR 단독 모드): {e}")

        # ==========================================
        # 2. 지수 상대강도(RS)용 지수 데이터 확보 (FDR 우선 -> Kiwoom ka20006 우회)
        # ==========================================
        kospi_5d_return = 0
        try:
            print("📈 FDR을 통해 최신 KOSPI 지수 데이터를 가져오는 중...")
            kospi_df = fdr.DataReader('KS11', start=(datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'))
            if not kospi_df.empty and len(kospi_df) >= 5:
                kospi_5d_return = (kospi_df['Close'].iloc[-1] / kospi_df['Close'].iloc[-5]) - 1
            else:
                raise ValueError("FDR 데이터 부족")
        except Exception as e:
            if kiwoom_token:
                latest_prc, before_prc = kiwoom_utils.get_index_daily_ka20006(kiwoom_token, "001")
                if latest_prc and before_prc:
                    kospi_5d_return = (latest_prc / before_prc) - 1

        # ==========================================
        # 3. 기초 유동성 필터 (FDR -> DB Fallback)
        # ==========================================
        print("🔍 [1/4] 분석 대상 종목 리스트 구성 중...")
        target_list = []
        try:
            df_krx = fdr.StockListing('KOSPI')
            top_m = df_krx.sort_values(by='Marcap', ascending=False).head(TRADING_RULES.TOP_N_MARCAP)
            target_df = top_m.sort_values(by='Volume', ascending=False).head(TRADING_RULES.TOP_N_VOLUME)
            target_list = [{'Code': r['Code'], 'Name': r['Name']} for _, r in target_df.iterrows()]
        except Exception as e:
            query = """
                SELECT stock_code AS "Code", stock_name AS "Name" 
                FROM daily_stock_quotes 
                WHERE quote_date = (SELECT MAX(quote_date) FROM daily_stock_quotes) 
                ORDER BY marcap DESC 
                LIMIT 200
                """
            with db.get_session() as session:
                # 💡 ORM/Core 방식으로 변경 필요 시 추후 대응, 현재는 pandas 연동 유지
                db_targets = pd.read_sql(query, session.bind)
            target_list = db_targets.head(150).to_dict('records')

        # ==========================================
        # 4. AI 앙상블 스캐닝 루프 (💡 except 블록 밖으로 완벽 탈출!)
        # ==========================================
        print(f"🚀 [2/4] AI 콰트로 앙상블 분석 시작 ({len(target_list)} 종목)...")
        all_results = []
        drop_stats = {'short_data': 0, 'invalid_type': 0, 'low_price': 0, 'quality': 0, 'ai_prob': 0, 'trend': 0, 'supply': 0, 'error': 0}

        # 💡 [핵심] DB의 스네이크 케이스를 AI가 아는 기존 대문자 포맷으로 원상복구하는 사전
        REVERSE_MAPPING = {
            'quote_date': 'Date', 'stock_code': 'Code', 'stock_name': 'Name',
            'open_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 'close_price': 'Close', 'volume': 'Volume',
            'ma5': 'MA5', 'ma20': 'MA20', 'ma60': 'MA60', 'ma120': 'MA120', 'rsi': 'RSI', 
            'macd': 'MACD', 'macd_sig': 'MACD_Sig', 'macd_hist': 'MACD_Hist',
            'bbl': 'BBL', 'bbm': 'BBM', 'bbu': 'BBU', 'bbb': 'BBB', 'bbp': 'BBP', 
            'vwap': 'VWAP', 'obv': 'OBV', 'atr': 'ATR', 'daily_return': 'Return',
            'marcap': 'Marcap', 'retail_net': 'Retail_Net', 'foreign_net': 'Foreign_Net', 'inst_net': 'Inst_Net', 'margin_rate': 'Margin_Rate'
        }

        for stock in target_list:
            code = str(stock['Code']).strip().zfill(6)
            name = stock['Name']
            
            df = db.get_stock_data(code, limit=60)
            if len(df) < 30: 
                drop_stats['short_data'] += 1
                continue

            # 💡 [핵심 로직] 꺼내온 즉시 컬럼명을 AI용으로 갈아입힙니다.
            df = df.rename(columns=REVERSE_MAPPING)

            df = df.sort_values('Date')
            current_price = df.iloc[-1]['Close']

            if not kiwoom_utils.is_valid_stock(code, name, current_price=current_price):
                if current_price < TRADING_RULES.MIN_PRICE: drop_stats['low_price'] += 1
                else: drop_stats['invalid_type'] += 1
                continue

            # =================================================================
            # 🛡️ 기초품질(Quality) 필터: 하락 추세 및 소외주 1차 컷오프
            # 아래 3가지 모멘텀 조건 중 **단 1개도 만족하지 못하는(sum < 1)** 종목은 폐기
            #   1) 상대강도: 최근 5일 수익률이 코스피 지수 5일 수익률보다 높을 것
            #   2) 단기추세: 현재가 > 5일선 > 20일선 (단기 완전 정배열)
            #   3) 가격방어: 최근 20일(약 1달) 최고점 대비 하락폭이 -10% 이내일 것
            # =================================================================
            stock_5d_return = (current_price / df.iloc[-5]['Close']) - 1
            ma5, ma20 = df['Close'].rolling(5).mean().iloc[-1], df['Close'].rolling(20).mean().iloc[-1]
            high_20d = df['High'].tail(20).max()

            if sum([stock_5d_return > kospi_5d_return, (current_price > ma5 > ma20), current_price >= (high_20d * 0.90)]) < 1:
                drop_stats['quality'] += 1  
                continue

            try:
                # 추론을 ml_predictor에게 위임!
                p_final = ml_predictor.predict_prob_for_df(df, models)

                if p_final < getattr(TRADING_RULES, 'PROB_RUNNER_PICK', 0.70):
                    drop_stats['ai_prob'] += 1  
                    continue

                # AI를 통과한 녀석들만 수급 필터를 위해 피처 계산
                df_feat = calculate_all_features(df)
                latest_row = df_feat.iloc[[-1]]

                f_roll5 = latest_row['Foreign_Net_Roll5'].values[0]
                i_roll5 = latest_row['Inst_Net_Roll5'].values[0]
                f_accel = latest_row['Foreign_Net_Accel'].values[0]
                i_accel = latest_row['Inst_Net_Accel'].values[0]

                if not ((f_roll5 > 0 and f_accel > 0) or (i_roll5 > 0 and i_accel > 0)):
                    drop_stats['supply'] += 1
                    continue

                h60, l60 = df_feat['High'].tail(60).max(), df_feat['Low'].tail(60).min()
                pos_pct = (current_price - l60) / (h60 - l60 + 1e-9)
                pos_tag = 'BREAKOUT' if pos_pct >= 0.8 else ('BOTTOM' if pos_pct <= 0.3 else 'MIDDLE')

                all_results.append({'Name': name, 'Prob': p_final, 'Price': int(current_price), 'Code': code, 'Position': pos_tag})

            except Exception as e:
                drop_stats['error'] += 1  
                continue
        
        today = datetime.now().strftime('%Y-%m-%d')

        # ==========================================
        # 💡 [신규/순서변경] 4.5 V2 Meta Ranker (CSV) 우선 로드 및 DB 적재
        # ==========================================
        csv_path = os.path.join(DATA_DIR, 'daily_recommendations_v2.csv')
        csv_count = 0
        csv_picks = []  # 텔레그램 아침 브리핑에 합류시킬 임시 리스트
        
        if os.path.exists(csv_path):
            try:
                df_csv = pd.read_csv(csv_path)
                for _, row in df_csv.iterrows():
                    csv_code = str(row['code']).replace('.0', '').strip().zfill(6)
                    csv_name = row.get('name', 'Unknown')
                    csv_price = int(row.get('close', 0)) if 'close' in df_csv.columns else 0
                    csv_prob = float(row.get('score', 0.99))
                    
                    # 💡 [핵심] Base 모델의 절대 확률을 읽어옵니다. (없으면 1.0으로 간주)
                    hybrid_mean = float(row.get('hybrid_mean', 1.0))
                    
                    # 🛡️ 깐깐한 동적 할당 로직: 안전망(0.35)을 통과하지 못한 임시 10개 종목은 RUNNER로 강등!
                    if hybrid_mean < 0.35:
                        pick_type = 'RUNNER'
                        position_tag = 'META_FALLBACK'  # 텔레그램에서 쉽게 구분하기 위한 태그
                        star_icon = "🥈"                 # 임시 종목은 은메달 아이콘
                    else:
                        pick_type = 'MAIN'
                        position_tag = 'META_V2'
                        star_icon = "🌟"                 # 확실한 종목은 빛나는 별 아이콘

                    # 1. DB 우선 적재 (MAIN 또는 RUNNER 동적 할당)
                    db.save_recommendation(
                        date=today,
                        code=csv_code,
                        name=csv_name,
                        price=csv_price,
                        pick_type=pick_type,
                        position=position_tag,     
                        prob=csv_prob,
                        strategy='KOSPI_ML'     
                    )
                    
                    # 2. 리포트 결합용 데이터 보관
                    csv_picks.append({
                        'Code': csv_code,
                        'Name': f"{star_icon}{csv_name}", 
                        'Price': csv_price,
                        'Prob': csv_prob,
                        'Position': position_tag
                    })
                    csv_count += 1
                print(f"✅ V2 CSV에서 {csv_count}개 종목 우선 적재 완료")
            except Exception as e:
                print(f"⚠️ V2 CSV 적재 실패: {e}")
        else:
            print(f"ℹ️ V2 CSV 파일이 존재하지 않아 실시간 스캐닝 결과만 처리합니다.")

        # ==========================================
        # 5. 결과 기록 및 텔레그램 전송 (Event-Driven)
        # ==========================================
        print("📊 [3/4] 리포트 생성 및 전송 중...")
        
        # 💡 [핵심] 텔레그램 발송 메시지에 CSV 적재 건수(csv_count)를 한 줄 추가!
        debug_msg = (
            f"🛑 *[AI 스캐너 필터링 결과]*\n"
            f"총 {len(target_list)}개 중 *{len(all_results)}개 생존 (실시간)*\n"
            f"🌟 *V2 앙상블 (CSV) 추가 적재: {csv_count}개*\n\n"
            f"📉 *탈락 사유 통계 (실시간)*\n"
            f" • 데이터 부족: {drop_stats['short_data']}개\n"
            f" • ETF/동전주: {drop_stats['invalid_type'] + drop_stats['low_price']}개\n"
            f" • 기초 품질 미달: {drop_stats['quality']}개\n"
            f" • AI 확신도 부족: {drop_stats['ai_prob']}개\n"
            f" • 수급 부재(이탈): {drop_stats['supply']}개\n"
        )

        # 관리자용 디버그 메시지 발송
        event_bus.publish("TELEGRAM_ADMIN_NOTIFY", {"text": debug_msg})

        # --- 기존 실시간 추천 종목 분류 및 DB 저장 ---
        main_picks = sorted([r for r in all_results if r['Prob'] >= TRADING_RULES.PROB_MAIN_PICK], key=lambda x: x['Prob'], reverse=True)[:3]
        runner_ups = sorted([r for r in all_results if TRADING_RULES.PROB_RUNNER_PICK <= r['Prob'] < TRADING_RULES.PROB_MAIN_PICK], key=lambda x: x['Prob'], reverse=True)[:50]

        for r in main_picks:
            db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'MAIN', r['Position'], prob=r['Prob'])
        for r in runner_ups:
            db.save_recommendation(today, r['Code'], r['Name'], r['Price'], 'RUNNER', r['Position'], prob=r['Prob'])

        # 💡 [핵심] 아침 브리핑(START_OF_DAY_REPORT)을 위해 CSV 종목을 실시간 MAIN 종목 맨 앞에 병합
        main_picks = csv_picks + main_picks

        # --- Gemini AI 수석 트레이더 장전 브리핑 ---
        ai_briefing = "⚠️ GEMINI_API_KEY 미설정"
        
        # 💡 [핵심 교정 1] 복수형 api_keys 변수로 정확히 받음
        api_keys = [v for k, v in CONF.items() if k.startswith("GEMINI_API_KEY")]
    
        # 매크로 데이터 수집
        try:
            macro_builder = MacroBriefingBuilder.from_system_config()
            _, macro_text = macro_builder.build_macro_context(include_debug=False)
        except Exception as e:
            log_error(f"매크로 데이터 수집 실패: {e}")
            macro_text = ""

        if not api_keys:
            log_error("❌ 제미나이 키 발급 실패로 엔진을 중단합니다.")
            event_bus.publish('TELEGRAM_BROADCAST', {'message': "🚨 [시스템 에러] 제미나이 키 발급 실패로 엔진을 중단합니다."})
        else:
            try:
                # 💡 [핵심 교정 2] api_keys=api_keys 로 오타 수정!
                ai_engine = GeminiSniperEngine(api_keys=api_keys)
                ai_briefing = ai_engine.analyze_scanner_results(len(target_list), len(all_results), debug_msg, macro_text)
            except Exception as e:
                ai_briefing = f"⚠️ AI 브리핑 생성 실패: {e}"

        perf_report = get_performance_report(db)

        # 💡 [핵심 교정 3] 텔레그램 매니저의 '0개 스킵' 로직을 우회하는 방어막 추가
        if len(main_picks) == 0 and len(runner_ups) == 0:
            # 종목이 0개일 때는 START_OF_DAY_REPORT 양식을 쓰지 않고, 통짜 텍스트로 강제 전송합니다.
            fallback_msg = (
                f"{perf_report}\n"
                f"{ai_briefing}\n\n"
                f"🛡️ <b>[시스템 알림]</b>\n"
                f"오늘은 AI 필터링을 통과한 생존 종목이 0개입니다.\n무리한 진입을 피하고 현금을 보호합니다."
            )
            event_bus.publish("TELEGRAM_BROADCAST", {"message": fallback_msg, "parse_mode": "HTML"})
        else:
            # 📢 정상적으로 생존 종목이 있을 때 (기존 로직)
            payload = {
                "type": "START_OF_DAY_REPORT",
                "date": today,
                "performance_report": perf_report,
                "ai_briefing": ai_briefing,
                "main_picks": main_picks,
                "runner_ups": runner_ups
            }
            event_bus.publish("TELEGRAM_BROADCAST", payload)

    except Exception as e:
        print(f"❌ 시스템 에러 발생: {e}")
    finally:
        print("🏁 [4/4] 스캐닝 프로세스가 종료되었습니다.")

if __name__ == "__main__":
    run_integrated_scanner()