"""
[KORStockScan AI Inference Module (ML Predictor)]

이 모듈은 KORStockScan의 두뇌 역할을 하는 '순수 AI 추론 도구상자'입니다.
오직 "DataFrame을 입력받아 AI 앙상블 확신도(Probability)를 반환한다"는 단일 책임(SRP)만 수행합니다.

💡 아키텍처 관점에서의 독립(Decoupling) 사유:
1. 스캐너 엔진과의 완벽한 분리:
   기존에는 무거운 배치 작업(장중 스캔, 장 마감 스캔)을 수행하는 스캐너 파일 내부에 추론 로직이 섞여 있었습니다.
   이를 분리함으로써, 코스닥 스캐너나 스캘핑 스캐너가 순수하게 '추론(Inference)'만 필요할 때 
   불필요한 설정 파일 로드, 텔레그램 연동 로직, 무거운 루프문 등을 메모리에 끌고 오지 않게 방어합니다.
2. 재사용성(Reusability) 극대화:
   이제 시스템 내의 어떤 모듈이든 (예: 텔레그램 봇에서 특정 종목을 즉석에서 물어볼 때) 
   이 모듈만 가볍게 import하면 즉시 AI의 판독 결과를 얻을 수 있습니다.
"""
import os
import joblib
import pandas as pd
import numpy as np

# 💡 Level 1 공통 모듈 (경로, 로거, 피처 엔지니어링)
from src.utils.constants import DATA_DIR
from src.utils.logger import log_error
from src.model.feature_engineering_v2 import calculate_all_features

# ==========================================
# 🧠 AI 앙상블 모델 Feature 리스트 (PostgreSQL 스키마 완벽 동기화)
# ==========================================
# 💡 [핵심 교정 1] XGBoost가 학습한 15개 소문자(snake_case) 피처 리스트
FEATURES_XGB = [
    'daily_return', 'ma_ratio', 'macd', 'macd_sig', 'vwap', 'obv', 
    'up_trend_2d', 'dist_ma5', 'dual_net_buy', 'foreign_net_roll5', 'inst_net_roll5',
    'bbb', 'bbp', 'atr_ratio', 'rsi'
]

# 💡 [핵심 교정 2] LightGBM이 학습한 12개 소문자(snake_case) 피처 리스트
FEATURES_LGBM = [
    'bbp', 'rsi', 'rsi_slope', 'range_ratio', 'vol_momentum', 
    'vol_change', 'atr', 'bbb', 'foreign_vol_ratio', 
    'inst_vol_ratio', 'margin_rate_change', 'margin_rate_roll5'
]

# ==========================================
# 🚀 AI 추론 도구 (Inference Utilities)
# ==========================================
def load_models():
    """
    AI 앙상블 모델(XGB, LGBM, Meta 등)들을 메모리에 한 번만 로드하여 튜플로 반환합니다.
    """
    try:
        m_xgb = joblib.load(os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl'))
        m_lgbm = joblib.load(os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl'))
        b_xgb = joblib.load(os.path.join(DATA_DIR, 'bull_xgb_model.pkl'))
        b_lgbm = joblib.load(os.path.join(DATA_DIR, 'bull_lgbm_model.pkl'))
        meta_model = joblib.load(os.path.join(DATA_DIR, 'stacking_meta_model.pkl'))
        
        return (m_xgb, m_lgbm, b_xgb, b_lgbm, meta_model)
    except Exception as e:
        log_error(f"❌ AI 모델 로드 실패: {e}")
        return None

def predict_prob_for_df(df: pd.DataFrame, models: tuple) -> float:
    """
    일봉 DataFrame을 입력받아 피처를 계산하고,
    최종 AI Stacking 확신지수(Prob)를 반환하는 순수 함수(Pure Function)입니다.
    """
    if not models or df is None or df.empty:
        return 0.0

    # 🛡️ [핵심 교정] try-except 블록을 함수 최상단으로 끌어올렸습니다!
    # 이제 피처 계산, 이름 변경, 모델 추론 등 어디서 에러가 나든 무조건 0점을 반환합니다.
    try:
        m_xgb, m_lgbm, b_xgb, b_lgbm, meta_model = models

        # [절대 방어막] 대문자/소문자 상관없이 수급/신용 데이터 누락 시 강제 0 주입
        for col in ['Retail_Net', 'retail_net', 'Foreign_Net', 'foreign_net', 'Inst_Net', 'inst_net', 'Margin_Rate', 'margin_rate']:
            if col not in df.columns:
                df[col] = 0.0

        # 1. 기술적 지표(피처) 일괄 계산 (🚨 이제 여기서 에러가 나도 안전합니다)
        df = calculate_all_features(df)

        # 2. 방탄 매핑 (Bulletproof Mapping)
        rename_map = {
            'Return': 'daily_return', 'MA_Ratio': 'ma_ratio', 'MACD': 'macd', 'MACD_Sig': 'macd_sig',
            'VWAP': 'vwap', 'OBV': 'obv', 'Up_Trend_2D': 'up_trend_2d', 'Dist_MA5': 'dist_ma5',
            'Dual_Net_Buy': 'dual_net_buy', 'Foreign_Net_Roll5': 'foreign_net_roll5', 'Inst_Net_Roll5': 'inst_net_roll5',
            'BB_Width': 'bbb', 'BBB': 'bbb', 'BB_Pos': 'bbp', 'BBP': 'bbp', 'ATR_Ratio': 'atr_ratio', 'RSI': 'rsi',
            'RSI_Slope': 'rsi_slope', 'Range_Ratio': 'range_ratio', 'Vol_Momentum': 'vol_momentum', 'Vol_Change': 'vol_change',
            'ATR': 'atr', 'Foreign_Vol_Ratio': 'foreign_vol_ratio', 'Inst_Vol_Ratio': 'inst_vol_ratio',
            'Margin_Rate_Change': 'margin_rate_change', 'Margin_Rate_Roll5': 'margin_rate_roll5'
        }
        
        # DataFrame에 존재하는 컬럼만 안전하게 이름 변경
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # 3. 가장 최신 일자(오늘)의 데이터 한 줄만 추출
        latest_row = df.iloc[[-1]].replace([np.inf, -np.inf], np.nan).fillna(0)

        # 4. 4개의 개별 베이스 모델 예측
        preds = [
            m_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
            m_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1],
            b_xgb.predict_proba(latest_row[FEATURES_XGB])[0][1],
            b_lgbm.predict_proba(latest_row[FEATURES_LGBM])[0][1]
        ]

        # 5. 메타 모델(Stacking) 최종 예측
        p_final = meta_model.predict_proba(
            pd.DataFrame([preds], columns=['XGB_Prob', 'LGBM_Prob', 'Bull_XGB_Prob', 'Bull_LGBM_Prob'])
        )[0][1]

        return float(p_final)

    except Exception as e:
        # 에러 발생 시 0.0을 반환하여, 스캐너가 이 종목을 'AI 확신도 부족(0점)' 통계로 정상 분류하게 만듭니다.
        # log_error(f"⚠️ AI 추론 연산 중 에러 발생: {e}") # 로그가 너무 많이 찍히는 것을 방지하려면 주석 처리
        return 0.0