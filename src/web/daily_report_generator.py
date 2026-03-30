import os
import json
import pandas as pd
import numpy as np
import joblib
from datetime import datetime, timedelta
import kiwoom_utils
from db_manager import DBManager
from src.model.feature_engineering_v2 import calculate_all_features
from constants import TRADING_RULES

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))

# 💡 [핵심 수정] data 디렉토리 아래에 'report' 디렉토리를 지정하고, 없으면 생성합니다.
REPORT_DIR = os.path.join(DATA_DIR, 'report')
os.makedirs(REPORT_DIR, exist_ok=True) 

CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')

FEATURES_XGB = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy', 'Foreign_Net_Roll5', 'Inst_Net_Roll5']
FEATURES_LGBM = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP', 'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']

def generate_daily_report():
    today_str = datetime.now().strftime('%Y-%m-%d')
    # 💡 [핵심 수정] 생성된 json 파일이 REPORT_DIR에 저장되도록 설정
    report_file = os.path.join(REPORT_DIR, f'report_{today_str}.json')
    
    print(f"🔍 [{today_str}] 일일 진단 리포트 생성을 시작합니다...")
    db = DBManager()
    stocks_data = []

    # 1. 모델 로드
    try:
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))
    except:
        return print("❌ 모델 로드 실패")

    # 2. 기초 타겟 150개 추출
    query = "SELECT Code, Name FROM daily_stock_quotes WHERE Date = (SELECT MAX(Date) FROM daily_stock_quotes) ORDER BY Marcap DESC LIMIT 200"
    with db._get_connection() as conn:
        db_targets = pd.read_sql(query, conn)
    target_list = db_targets.head(150).to_dict('records')

    # 통계 변수
    total_valid = 0
    above_20ma_count = 0
    avg_rsi_sum = 0
    avg_final_prob_sum = 0
    bull_model_prob_sum = 0

    print(f"🚀 총 {len(target_list)}개 종목 분석 중...")
    for stock in target_list:
        code, name = str(stock['Code']).strip().zfill(6), stock['Name']
        df = db.get_stock_data(code, limit=60)
        
        if len(df) < 30: continue
        df = df.sort_values('Date')
        curr_p = int(df.iloc[-1]['Close'])
        
        if not kiwoom_utils.is_valid_stock(code, name, current_price=curr_p): continue

        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        is_above_20ma = curr_p > ma20
        total_valid += 1
        if is_above_20ma: above_20ma_count += 1

        try:
            for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
                if col not in df.columns: df[col] = 0.0
            
            df = calculate_all_features(df)
            latest = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
            avg_rsi_sum += latest['RSI'].values[0]

            p_xgb = float(m_xgb.predict_proba(latest[FEATURES_XGB])[0][1])
            p_lgb = float(m_lgbm.predict_proba(latest[FEATURES_LGBM])[0][1])
            p_bxgb = float(b_xgb.predict_proba(latest[FEATURES_XGB])[0][1])
            p_blgb = float(b_lgbm.predict_proba(latest[FEATURES_LGBM])[0][1])
            
            bull_model_prob_sum += ((p_bxgb + p_blgb) / 2)

            p_final = float(meta_model.predict_proba(pd.DataFrame([[p_xgb, p_lgb, p_bxgb, p_blgb]], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob']))[0][1])
            avg_final_prob_sum += p_final

            f_roll5, i_roll5 = float(latest['Foreign_Net_Roll5'].values[0]), float(latest['Inst_Net_Roll5'].values[0])
            f_accel, i_accel = float(latest['Foreign_Net_Accel'].values[0]), float(latest['Inst_Net_Accel'].values[0])
            is_for_buy = (f_roll5 > 0 and f_accel > 0)
            is_inst_buy = (i_roll5 > 0 and i_accel > 0)

            result_str = "✅ [합격]" if (p_final >= 0.70 and (is_for_buy or is_inst_buy)) else ("❌ 수급 부재" if p_final >= 0.70 else "❌ 점수 미달")

            stocks_data.append({
                "code": code, "name": name, "price": f"{curr_p:,}원",
                "ma20": "🟢 돌파 (정배열)" if is_above_20ma else "🔴 이탈 (역배열)",
                "ai_prob": f"⭐ {p_final:.1%}",
                "ai_details": f"일반[{p_xgb:.1%}/{p_lgb:.1%}] | 상승장[{p_bxgb:.1%}/{p_blgb:.1%}]",
                "supply": f"{'양호' if is_for_buy else '이탈'} / {'양호' if is_inst_buy else '이탈'}",
                "result": result_str
            })
        except Exception: pass

    # 3. 자동 해석 AI 브레인 가동
    ma20_ratio = (above_20ma_count / total_valid * 100) if total_valid > 0 else 0
    avg_rsi = (avg_rsi_sum / total_valid) if total_valid > 0 else 0
    avg_prob = (avg_final_prob_sum / total_valid * 100) if total_valid > 0 else 0
    avg_bull = (bull_model_prob_sum / total_valid * 100) if total_valid > 0 else 0

    analysis_dashboard = f"현재 대한민국 시총 상위 우량주 중 {ma20_ratio:.1f}%만이 추세선(20일선) 위에 있습니다. 시장 평균 과열도(RSI)는 {avg_rsi:.1f}입니다."
    
    if ma20_ratio < 40:
        analysis_psy = f"상승장 전용 모델의 평균 확신도가 {avg_bull:.1f}%로 처참하게 박살 났습니다. AI는 현재 시장을 '가랑비에 옷 젖는 계단식 하락장'으로 규정하고 전면 파업에 돌입했습니다."
        analysis_strat = "✅ [현금도 종목이다] 봇의 브레이크를 믿고 현금을 보유하십시오. RSI가 30 밑으로 떨어지는 패닉셀 장세가 오거나, 20일선 돌파 비율이 50%를 회복할 때까지 매수 버튼을 뽑아두는 것을 권장합니다."
    elif ma20_ratio >= 60:
        analysis_psy = f"상승장 전용 모델이 평균 {avg_bull:.1f}%의 높은 가산점을 주며 적극적으로 매수를 독려하고 있습니다."
        analysis_strat = "🔥 [적극 매수 구간] 수급이 들어오는 주도주를 중심으로 스윙 포지션을 길게 가져가도 좋은 완벽한 상승장입니다."
    else:
        analysis_psy = "AI 모델들의 의견이 엇갈리고 있습니다. 방향성을 탐색하는 횡보장세입니다."
        analysis_strat = "⚖️ [기회주의적 스캘핑] 비중을 줄이고 짧게 치고 빠지는 초단타(SCALPING) 전략 위주로 대응하십시오."

    # 4. JSON 저장
    report_json = {
        "date": today_str,
        "stats": {
            "ma20_ratio": round(ma20_ratio, 1),
            "avg_rsi": round(avg_rsi, 1),
            "avg_prob": round(avg_prob, 1),
            "status_text": "상승장" if ma20_ratio >= 60 else ("조정장" if ma20_ratio >= 40 else "하락장(매수금지)"),
            
            # 💡 [여기 수정] 'red', 'green' 대신 Bootstrap 클래스명으로 변경
            "color": "text-success" if ma20_ratio >= 60 else ("text-warning" if ma20_ratio >= 40 else "text-danger")
        },
        "insights": {
            "dashboard": analysis_dashboard,
            "psychology": analysis_psy,
            "strategy": analysis_strat
        },
        "stocks": stocks_data
    }

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_json, f, ensure_ascii=False, indent=4)
    print(f"🎉 리포트 저장 완료: {report_file}")

if __name__ == "__main__":
    generate_daily_report()