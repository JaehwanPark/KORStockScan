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
CONFIG_PATH = os.path.join(DATA_DIR, 'config_prod.json')
REPORT_PATH = os.path.join(CURRENT_DIR, 'scanner_report.html')

FEATURES_XGB = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy', 'Foreign_Net_Roll5', 'Inst_Net_Roll5']
FEATURES_LGBM = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP', 'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']

def generate_web_report():
    print("🔍 [시장 건전성 및 AI 심리 진단] 리포트 생성을 시작합니다...")
    db = DBManager()
    report_data = []

    # 1. 모델 로드
    try:
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return

    # 키움 토큰 발급
    kiwoom_token = None
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            conf = json.load(f)
        kiwoom_token = kiwoom_utils.get_kiwoom_token(conf)
    except Exception as e:
        pass

    # 2. 기초 타겟 150개 추출 (로컬 DB 기반)
    query = "SELECT Code, Name FROM daily_stock_quotes WHERE Date = (SELECT MAX(Date) FROM daily_stock_quotes) ORDER BY Marcap DESC LIMIT 200"
    with db._get_connection() as conn:
        db_targets = pd.read_sql(query, conn)
    target_list = db_targets.head(150).to_dict('records')

    kospi_5d_return = 0
    if kiwoom_token:
        latest_prc, before_prc = kiwoom_utils.get_index_daily_ka20006(kiwoom_token, "001")
        if latest_prc and before_prc: kospi_5d_return = (latest_prc / before_prc) - 1

    # 🚀 시장 건전성 통계용 변수
    total_valid_stocks = 0
    above_20ma_count = 0
    avg_rsi_sum = 0
    avg_final_prob_sum = 0

    print(f"🚀 총 {len(target_list)}개 종목 진단 중...")

    for i, stock in enumerate(target_list, 1):
        code = str(stock['Code']).strip().zfill(6)
        name = stock['Name']
        
        row_data = {
            "종목코드": code, "종목명": name, "현재가": "-", 
            "20일선돌파": "-", "최종AI확신도": "-", "개별AI모델분석(일반/상승장)": "-", 
            "수급(외인/기관)": "-", "최종결과": "통과 대기"
        }

        df = db.get_stock_data(code, limit=60)
        
        if len(df) < 30:
            row_data["최종결과"] = "❌ 데이터 부족 (<30일)"
            report_data.append(row_data)
            continue

        df = df.sort_values('Date')
        current_price = int(df.iloc[-1]['Close'])
        row_data["현재가"] = f"{current_price:,}원"

        if not kiwoom_utils.is_valid_stock(code, name, current_price=current_price):
            row_data["최종결과"] = f"❌ 저가주/불량종목"
            report_data.append(row_data)
            continue

        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        is_above_ma20 = current_price > ma20
        row_data["20일선돌파"] = "🔴 이탈 (역배열)" if not is_above_ma20 else "🟢 돌파 (정배열)"
        
        # 건전성 집계
        total_valid_stocks += 1
        if is_above_ma20: above_20ma_count += 1

        try:
            for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
                if col not in df.columns: df[col] = 0.0

            df = calculate_all_features(df)
            latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)
            
            avg_rsi_sum += latest_row['RSI'].values[0]

            # 💡 [핵심] 개별 모델 결과 분리 추출
            p_xgb = m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_lgb = m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
            p_bxgb = b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1]
            p_blgb = b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]

            preds = [p_xgb, p_lgb, p_bxgb, p_blgb]
            p_final = meta_model.predict_proba(pd.DataFrame([preds], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob']))[0][1]

            avg_final_prob_sum += p_final

            # 웹 리포트에 개별 모델 수치 표기
            row_data["최종AI확신도"] = f"⭐ {p_final:.1%}"
            row_data["개별AI모델분석(일반/상승장)"] = f"일반[{p_xgb:.1%}/{p_lgb:.1%}] | 상승장[{p_bxgb:.1%}/{p_blgb:.1%}]"

            f_roll5, i_roll5 = latest_row['Foreign_Net_Roll5'].values[0], latest_row['Inst_Net_Roll5'].values[0]
            f_accel, i_accel = latest_row['Foreign_Net_Accel'].values[0], latest_row['Inst_Net_Accel'].values[0]

            is_for_buy = (f_roll5 > 0 and f_accel > 0)
            is_inst_buy = (i_roll5 > 0 and i_accel > 0)
            row_data["수급(외인/기관)"] = f"{'양호' if is_for_buy else '이탈'} / {'양호' if is_inst_buy else '이탈'}"

            if p_final < TRADING_RULES.get('PROB_RUNNER_PICK', 0.70):
                row_data["최종결과"] = "❌ 점수 미달"
            elif not (is_for_buy or is_inst_buy):
                row_data["최종결과"] = "❌ 수급 부재"
            else:
                row_data["최종결과"] = "✅ [합격]"
            
            report_data.append(row_data)

        except Exception as e:
            row_data["최종결과"] = f"❌ 계산 에러"
            report_data.append(row_data)

    # 5. 요약 대시보드 계산
    ma20_ratio = (above_20ma_count / total_valid_stocks * 100) if total_valid_stocks > 0 else 0
    avg_rsi = (avg_rsi_sum / total_valid_stocks) if total_valid_stocks > 0 else 0
    avg_prob = (avg_final_prob_sum / total_valid_stocks * 100) if total_valid_stocks > 0 else 0

    market_health_color = "green" if ma20_ratio >= 50 else ("orange" if ma20_ratio >= 30 else "red")
    market_status_text = "상승장 (안정)" if ma20_ratio >= 50 else ("조정장 (관망 요망)" if ma20_ratio >= 30 else "하락장 (매수 금지)")

    df_report = pd.DataFrame(report_data)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>KORStockScan 진단 리포트</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ padding: 20px; background-color: #f8f9fa; font-family: 'Malgun Gothic', sans-serif; }}
            .dashboard {{ background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .stat-box {{ text-align: center; padding: 15px; border-right: 1px solid #eee; }}
            .stat-box:last-child {{ border-right: none; }}
            .stat-title {{ font-size: 14px; color: #7f8c8d; font-weight: bold; }}
            .stat-value {{ font-size: 24px; font-weight: 900; color: #2c3e50; }}
            h2 {{ color: #2c3e50; font-weight: bold; }}
            .table {{ background-color: white; box-shadow: 0 0 15px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden; font-size: 14px; }}
            .table thead {{ background-color: #34495e; color: white; }}
            .badge-pass {{ background-color: #27ae60; color: white; padding: 4px 8px; border-radius: 8px; font-weight: bold; }}
            .badge-fail {{ background-color: #e74c3c; color: white; padding: 4px 8px; border-radius: 8px; }}
            .bull-model {{ color: #e67e22; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <h2>📊 KORStockScan 시장 건전성 및 AI 심리 분석 리포트</h2>
            <p class="text-muted">생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="dashboard row">
                <div class="col-md-3 stat-box">
                    <div class="stat-title">거시 시장 상태 (KOSPI 150종목)</div>
                    <div class="stat-value" style="color: {market_health_color};">{market_status_text}</div>
                </div>
                <div class="col-md-3 stat-box">
                    <div class="stat-title">20일 이동평균선 돌파 비율</div>
                    <div class="stat-value">{ma20_ratio:.1f}%</div>
                </div>
                <div class="col-md-3 stat-box">
                    <div class="stat-title">시장 평균 과열도 (RSI)</div>
                    <div class="stat-value">{avg_rsi:.1f} / 100</div>
                </div>
                <div class="col-md-3 stat-box">
                    <div class="stat-title">AI 메타모델 평균 확신도</div>
                    <div class="stat-value">{avg_prob:.1f}%</div>
                </div>
            </div>

            <p>※ <b>해석 가이드:</b> 개별AI모델에서 <span class="bull-model">상승장(Bull) 모델 수치</span>가 10% 미만으로 극단적으로 낮다면, AI가 현재 시장을 완벽한 역배열/하락장으로 인식하여 방어 모드에 돌입한 것입니다.</p>

            {df_report.to_html(index=False, classes="table table-hover text-center align-middle", border=0)}
        </div>
        <script>
            document.querySelectorAll('td').forEach(td => {{
                if(td.innerText.includes('✅')) td.innerHTML = `<span class="badge-pass">${{td.innerText}}</span>`;
                else if(td.innerText.includes('❌')) td.innerHTML = `<span class="badge-fail">${{td.innerText}}</span>`;
                else if(td.innerText.includes('상승장[')) {{
                    td.innerHTML = td.innerHTML.replace('상승장[', '<span class="bull-model">상승장[').replace(']', ']</span>');
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("\n" + "="*50)
    print(f"🎉 웹 리포트 생성 완료! ({REPORT_PATH})")
    print("="*50)

if __name__ == "__main__":
    generate_web_report()