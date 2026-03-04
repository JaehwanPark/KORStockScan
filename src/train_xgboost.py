import sqlite3
import os
import FinanceDataReader as fdr
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score
from xgboost import XGBClassifier

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
MODEL_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
FEATURE_PATH = os.path.join(DATA_DIR, 'hybrid_features.pkl')


# ==========================================
# 1. 우량 대장주 필터링 (FDR + DB Fallback)
# ==========================================
def get_hybrid_top_codes():
    print("[1/5] 최신 시장 데이터 기반 우량 대장주 필터링 중...")
    try:
        df_krx = fdr.StockListing('KOSPI')
        top_500 = df_krx.sort_values(by='Marcap', ascending=False).head(500)
        target_top = top_500.sort_values(by='Volume', ascending=False).head(300)
        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top['Code'].tolist()
    except Exception:
        try:
            print(f"⚠️ FDR 종목 리스트 수집 실패. DB 데이터로 우회합니다...")
            conn = sqlite3.connect(DB_NAME)
            latest_date = pd.read_sql("SELECT MAX(Date) FROM daily_stock_quotes", conn).iloc[0, 0]
            top_codes_df = pd.read_sql(f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300", conn)
            conn.close()
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist() if not top_codes_df.empty else []
        except: return []


# ==========================================
# 2. 데이터 로드 및 전처리 (최적화 적용)
# ==========================================
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 정답지 생성 중...")
    conn = sqlite3.connect(DB_NAME)
    all_data = []

    # 💡 [핵심] 수급 컬럼 명시적 로드
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV, Foreign_Net, Inst_Net"

    for code in codes:
        df = pd.read_sql(f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date DESC LIMIT 750", conn)
        df = df.sort_values('Date', ascending=True).reset_index(drop=True)
        if len(df) < 150: continue

        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

        # 💡 [신규] 수급 추세 피처 생성
        df['Foreign_Net'] = df['Foreign_Net'].fillna(0)
        df['Inst_Net'] = df['Inst_Net'].fillna(0)
        df['Foreign_Net_Roll5'] = df['Foreign_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Inst_Net_Roll5'] = df['Inst_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Dual_Net_Buy'] = ((df['Foreign_Net'] > 0) & (df['Inst_Net'] > 0)).astype(int)

        df['Return'] = df['Close'].pct_change()
        # ==========================================
        # 🎯 [변경] 3일 단기 스윙 정답지(Target) 생성 로직
        # ==========================================
        df['Next1_Open'] = df['Open'].shift(-1)  # 다음날 아침 시가(매수가)

        # 1일차 ~ 3일차의 고가, 저가, 종가 미리보기
        for i in range(1, 4):
            df[f'Next{i}_High'] = df['High'].shift(-i)
            df[f'Next{i}_Low'] = df['Low'].shift(-i)
            df[f'Next{i}_Close'] = df['Close'].shift(-i)

        # 3일 동안의 최고가와 최저가 계산
        df['Max_High_3D'] = df[['Next1_High', 'Next2_High', 'Next3_High']].max(axis=1)
        df['Min_Low_3D'] = df[['Next1_Low', 'Next2_Low', 'Next3_Low']].min(axis=1)

        # 타겟 조건: 3일 안에 +4.5% 도달 & 3일 동안 -3.0% 손절선 방어 성공
        hit_target = (df['Max_High_3D'] / (df['Next1_Open'] + 1e-9)) >= 1.045
        no_stop_loss = (df['Min_Low_3D'] / (df['Next1_Open'] + 1e-9)) >= 0.970

        df['Target'] = np.where(hit_target & no_stop_loss, 1, 0)

        # 결측치(최근 3일 데이터가 없어 정답을 알 수 없는 마지막 행들) 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        if not df.empty: all_data.append(df)

    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()


# ==========================================
# 3. 모델 학습 (경로 분리 적용)
# ==========================================
def train_hybrid_xgb():
    target_codes = get_hybrid_top_codes()
    if not target_codes: return
    total_df = load_and_preprocess(target_codes)
    if total_df.empty: return

    # 💡 [신규] 수급 피처 3개 탑재
    features = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5',
                'Dual_Net_Buy', 'Foreign_Net_Roll5', 'Inst_Net_Roll5']

    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    train_df, test_df = total_df[total_df['Date'] < split_date], total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    neg_count, pos_count = (y_train == 0).sum(), (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count

    print(f"[3/5] XGBoost 모델 학습 시작...")
    model = XGBClassifier(
        n_estimators=2000, learning_rate=0.005, max_depth=5, min_child_weight=5, gamma=0.1,
        subsample=0.8, colsample_bytree=0.8, scale_pos_weight=dynamic_weight, random_state=42, n_jobs=-1,
        early_stopping_rounds=100, eval_metric='logloss'
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

    print("\n[4/5] 성능 검증 중...")
    prob = model.predict_proba(X_test)[:, 1]
    th = 0.50 if prob.max() >= 0.50 else prob.max() * 0.9
    pred = (prob >= th).astype(int)
    print(f"✅ XGBoost 검증 정밀도: {precision_score(y_test, pred, zero_division=0):.2%}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURE_PATH)
    print(f"[5/5] 모델 저장 완료: {MODEL_PATH}")

if __name__ == "__main__":
    train_hybrid_xgb()