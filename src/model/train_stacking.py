import os
import pandas as pd
import numpy as np
import joblib
import FinanceDataReader as fdr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
from sqlalchemy import create_engine, text
import warnings

warnings.filterwarnings('ignore')

# --- 경로 및 DB 설정 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# 🎯 PostgreSQL 연결 설정
DB_URL = os.getenv("DATABASE_URL", "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan")
engine = create_engine(DB_URL)

HYBRID_XGB_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
HYBRID_LGBM_PATH = os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl')
BULL_XGB_PATH = os.path.join(DATA_DIR, 'bull_xgb_model.pkl')
BULL_LGBM_PATH = os.path.join(DATA_DIR, 'bull_lgbm_model.pkl')
META_MODEL_PATH = os.path.join(DATA_DIR, 'stacking_meta_model.pkl')


# ==========================================
# 1. 우량 대장주 필터링 (FDR + PostgreSQL Fallback)
# ==========================================
def get_stacking_target_codes():
    print("[1/5] 우량 대장주 필터링 (메타 모델용)...")
    try:
        df_krx = fdr.StockListing('KOSPI')
        top_500 = df_krx.sort_values(by='Marcap', ascending=False).head(500)
        target_top = top_500.sort_values(by='Volume', ascending=False).head(300)
        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top['Code'].tolist()
    except Exception:
        try:
            with engine.connect() as conn:
                latest_date_query = "SELECT MAX(quote_date) FROM daily_stock_quotes"
                latest_date = pd.read_sql(text(latest_date_query), conn).iloc[0, 0]
                
                query = f"""
                    SELECT stock_code FROM daily_stock_quotes 
                    WHERE quote_date = '{latest_date}' 
                    ORDER BY volume DESC LIMIT 300
                """
                top_codes_df = pd.read_sql(text(query), conn)
                
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['stock_code'].tolist() if not top_codes_df.empty else []
        except Exception as e: 
            print(f"❌ DB 종목 추출 실패: {e}")
            return []


# ==========================================
# 2. 데이터 로드 및 전처리 (DB 스키마 최적화)
# ==========================================
def load_and_preprocess_stacking(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 전체 지표(수급/신용 포함) 생성 중...")
    all_processed_data = []

    # 💡 DB 컬럼 소문자 매핑
    cols_to_fetch = """
        quote_date, stock_code, open_price, high_price, low_price, close_price, volume, 
        ma5, ma20, macd, macd_sig, vwap, obv, rsi, atr, bbb, bbp, daily_return, 
        foreign_net, inst_net, margin_rate
    """

    with engine.connect() as conn:
        for code in codes:
            query = f"""
                SELECT {cols_to_fetch} 
                FROM daily_stock_quotes 
                WHERE stock_code = '{code}' 
                  AND quote_date >= '2026-01-16' 
                  AND quote_date <= '2026-02-28'
                ORDER BY quote_date ASC
            """
            df = pd.read_sql(text(query), conn)
            
            # 기존
            # if df.empty or len(df) < 150: 
            #     continue

            # 수정 (10~15일 정도의 여유만 있으면 파생 변수 계산에 충분함)
            if df.empty or len(df) < 15: 
                continue

            df = df.sort_values('quote_date', ascending=True).reset_index(drop=True)

            # 파생 변수 계산
            df['vol_change'] = df['volume'].pct_change()
            df['ma_ratio'] = df['close_price'] / (df['ma20'] + 1e-9)
            df['rsi_slope'] = df['rsi'].diff()
            df['range_ratio'] = (df['high_price'] - df['low_price']) / (df['close_price'] + 1e-9)
            df['vol_momentum'] = df['volume'] / (df['volume'].rolling(window=5).mean() + 1e-9)
            df['dist_ma5'] = df['close_price'] / (df['ma5'] + 1e-9)
            df['up_trend_2d'] = ((df['close_price'].diff(1) > 0) & (df['close_price'].shift(1).diff(1) > 0)).astype(int)
            
            # 💡 [추가] Hybrid XGBoost가 요구하는 atr_ratio 계산 로직
            df['atr_ratio'] = df['atr'] / (df['close_price'] + 1e-9)

            # 수급 및 신용 파생 피처
            vol_safe = df['volume'] + 1e-9
            df['foreign_net'] = df['foreign_net'].fillna(0)
            df['inst_net'] = df['inst_net'].fillna(0)
            df['margin_rate'] = df['margin_rate'].fillna(0)

            df['foreign_net_roll5'] = df['foreign_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
            df['inst_net_roll5'] = df['inst_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
            df['dual_net_buy'] = ((df['foreign_net'] > 0) & (df['inst_net'] > 0)).astype(int)
            df['foreign_vol_ratio'] = df['foreign_net'] / vol_safe
            df['inst_vol_ratio'] = df['inst_net'] / vol_safe
            df['margin_rate_change'] = df['margin_rate'].diff()
            df['margin_rate_roll5'] = df['margin_rate'].rolling(5).mean()

            # 🎯 3일 단기 스윙 정답지(Target) 생성
            df['next1_open'] = df['open_price'].shift(-1)

            for i in range(1, 4):
                df[f'next{i}_high'] = df['high_price'].shift(-i)
                df[f'next{i}_low'] = df['low_price'].shift(-i)

            df['max_high_3d'] = df[['next1_high', 'next2_high', 'next3_high']].max(axis=1)
            df['min_low_3d'] = df[['next1_low', 'next2_low', 'next3_low']].min(axis=1)

            hit_target = (df['max_high_3d'] / (df['next1_open'] + 1e-9)) >= 1.045
            no_stop_loss = (df['min_low_3d'] / (df['next1_open'] + 1e-9)) >= 0.970

            df['target'] = np.where(hit_target & no_stop_loss, 1, 0)

            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if not df.empty: 
                all_processed_data.append(df)

    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()


# ==========================================
# 3. 스태킹 앙상블 메인 로직
# ==========================================
def train_meta_model():
    target_codes = get_stacking_target_codes()
    if not target_codes: 
        return

    total_df = load_and_preprocess_stacking(target_codes)
    # 기존
    # if total_df.empty: 
    #     return

    # 수정
    if total_df.empty: 
        print("❌ 에러: 전처리 후 남은 데이터가 없습니다. (날짜 범위나 데이터 길이를 확인하세요)")
        return

    print("[3/5] 하위 전문가 모델(Base Models) 로드 중...")
    try:
        xgb_model = joblib.load(HYBRID_XGB_PATH)
        lgbm_model = joblib.load(HYBRID_LGBM_PATH)
        bull_xgb = joblib.load(BULL_XGB_PATH)
        bull_lgbm = joblib.load(BULL_LGBM_PATH)
    except Exception as e:
        print(f"[-] 모델 로드 실패. 하위 모델을 먼저 학습하세요. 에러: {e}")
        return

    # 💡 [핵심 수정] 각 모델이 학습할 때 사용했던 피처 리스트를 명확하게 분리
    features_hybrid_xgb = [
        'daily_return', 'ma_ratio', 'macd', 'macd_sig', 'vwap', 'obv', 
        'up_trend_2d', 'dist_ma5', 'dual_net_buy', 'foreign_net_roll5', 'inst_net_roll5',
        'bbb', 'bbp', 'atr_ratio', 'rsi'
    ]
    
    features_bull_xgb = [
        'daily_return', 'ma_ratio', 'macd', 'macd_sig', 'vwap', 'obv', 
        'up_trend_2d', 'dist_ma5', 'dual_net_buy', 'foreign_net_roll5', 'inst_net_roll5',
        'bbb', 'bbp', 'atr_ratio', 'rsi'  # 👈 메타 모델도 이 4개를 넘겨주도록 수정!
    ]
    
    features_lgbm = [
        'bbp', 'rsi', 'rsi_slope', 'range_ratio', 'vol_momentum', 'vol_change', 
        'atr', 'bbb', 'foreign_vol_ratio', 'inst_vol_ratio', 'margin_rate_change', 'margin_rate_roll5'
    ]

    unique_dates = sorted(total_df['quote_date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]

    train_df = total_df[total_df['quote_date'] < split_date]
    test_df = total_df[total_df['quote_date'] >= split_date]
    y_train = train_df['target']
    y_test = test_df['target']

    print("[4/5] 메타 학습용 OOF(Out-of-Fold) 확률 데이터 생성 중...")

    # 하위 모델별로 각자에게 맞는 피처 리스트를 전달하도록 수정
    meta_X_train = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(train_df[features_hybrid_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(train_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(train_df[features_bull_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(train_df[features_lgbm])[:, 1]
    })

    meta_X_test = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(test_df[features_hybrid_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(test_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(test_df[features_bull_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    })

    print("[5/5] 최종 결정권자(Meta-Model) 학습 및 임계값 테스트 중...")
    
    meta_model = LogisticRegression(class_weight='balanced', random_state=42)
    meta_model.fit(meta_X_train, y_train)

    meta_pred_proba = meta_model.predict_proba(meta_X_test)[:, 1]

    print("\n[전문가 의견 상관관계 분석]")
    print(meta_X_test.corr().round(3))

    thresholds = [0.5, 0.6, 0.7, 0.75, 0.8, 0.85]
    print("\n=============================================")
    print("   임계값(Th) | 정밀도(Precision) | 매수횟수(Test)")
    print("---------------------------------------------")
    for th in thresholds:
        pred = (meta_pred_proba >= th).astype(int)
        precision = precision_score(y_test, pred, zero_division=0)
        picks = pred.sum()
        print(f"      {th:.2f}    |      {precision:.2%}      |    {picks} 회")

    joblib.dump(meta_model, META_MODEL_PATH)
    print("=============================================\n")
    print(f"✅ Stacking 메타 모델이 성공적으로 갱신되었습니다! ({META_MODEL_PATH})")

    # ==========================================
    # 🚀 백테스트용 AI 예측 결과(ai_predictions.csv) 저장
    # ==========================================
    print("\n💾 백테스트용 AI 예측 결과(ai_predictions.csv)를 생성합니다...")

    df_results = test_df[['quote_date', 'stock_code']].copy()
    df_results.rename(columns={'quote_date': 'Date', 'stock_code': 'Code'}, inplace=True)

    df_results['XGB_Prob'] = np.round(meta_X_test['XGB_Prob'].values, 4)
    df_results['LGBM_Prob'] = np.round(meta_X_test['LGBM_Prob'].values, 4)
    df_results['Bull_XGB_Prob'] = np.round(meta_X_test['Bull_XGB_Prob'].values, 4)
    df_results['Bull_LGBM_Prob'] = np.round(meta_X_test['Bull_LGBM_Prob'].values, 4)
    df_results['Stacking_Prob'] = np.round(meta_pred_proba, 4)
    df_results['Actual_Target'] = y_test.values

    df_results = df_results.sort_values(by=['Date', 'Code']).reset_index(drop=True)

    save_path = os.path.join(DATA_DIR, 'ai_predictions.csv')
    df_results.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"✅ 테스트 세트(총 {len(df_results):,}건) 예측 결과가 저장되었습니다: {save_path}")


if __name__ == "__main__":
    train_meta_model()