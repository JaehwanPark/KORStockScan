import os
import sqlite3
import FinanceDataReader as fdr
import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.metrics import precision_score

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
MODEL_PATH = os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl')
FEATURE_PATH = os.path.join(DATA_DIR, 'lgbm_features.pkl')


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
            conn = sqlite3.connect(DB_NAME)
            latest_date = pd.read_sql("SELECT MAX(Date) FROM daily_stock_quotes", conn).iloc[0, 0]
            top_codes_df = pd.read_sql(f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300", conn)
            conn.close()
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist() if not top_codes_df.empty else []
        except: return []


# ==========================================
# 2. 데이터 로드 및 전처리 (최적화 적용 & 엄격한 타겟 유지)
# ==========================================
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 최신 지표 적용 중...")
    conn = sqlite3.connect(DB_NAME)
    all_data = []

    # 💡 [핵심] 수급 및 신용잔고 컬럼 로드
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, BBL, BBU, RSI, ATR, BBB, BBP, Foreign_Net, Inst_Net, Margin_Rate"

    for code in codes:
        df = pd.read_sql(
            f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date DESC LIMIT 750", conn)
        df = df.sort_values('Date', ascending=True).reset_index(drop=True)
        if len(df) < 150: continue

        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)

        # 💡 [신규] 수급 비율 및 신용잔고 피처 생성
        vol_safe = df['Volume'] + 1e-9
        df['Foreign_Net'] = df['Foreign_Net'].fillna(0)
        df['Inst_Net'] = df['Inst_Net'].fillna(0)
        df['Margin_Rate'] = df['Margin_Rate'].fillna(0)

        df['Foreign_Vol_Ratio'] = df['Foreign_Net'] / vol_safe
        df['Inst_Vol_Ratio'] = df['Inst_Net'] / vol_safe
        df['Margin_Rate_Change'] = df['Margin_Rate'].diff()
        df['Margin_Rate_Roll5'] = df['Margin_Rate'].rolling(5).mean()

        df['Next_Open'] = df['Open'].shift(-1)
        df['Next_High'] = df['High'].shift(-1)
        df['Next_Low'] = df['Low'].shift(-1)
        df['Next_Close'] = df['Close'].shift(-1)

        hit_target = (df['Next_High'] / (df['Next_Open'] + 1e-9)) >= 1.020
        no_stop_loss = (df['Next_Low'] / (df['Next_Open'] + 1e-9)) >= 0.975
        solid_close = df['Next_Close'] > df['Next_Open']

        df['Target'] = np.where(hit_target & no_stop_loss & solid_close, 1, 0)
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        if not df.empty: all_data.append(df)

    conn.close()
    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()


# ==========================================
# 3. LightGBM 모델 학습
# ==========================================
def train_hybrid_lgbm():
    target_codes = get_hybrid_top_codes()
    if not target_codes: return
    total_df = load_and_preprocess(target_codes)
    if total_df.empty: return

    # 💡 [신규] 수급/신용 피처 4개 탑재
    features = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP',
                'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']

    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    train_df, test_df = total_df[total_df['Date'] < split_date], total_df[total_df['Date'] >= split_date]

    X_train, y_train = train_df[features], train_df['Target']
    X_test, y_test = test_df[features], test_df['Target']

    neg_count, pos_count = (y_train == 0).sum(), (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count

    model = LGBMClassifier(
        n_estimators=2000, learning_rate=0.005, num_leaves=31, max_depth=5, min_child_samples=20,
        feature_fraction=0.8, bagging_fraction=0.8, subsample_freq=5, scale_pos_weight=dynamic_weight,
        random_state=42, n_jobs=-1, force_col_wise=True
    )
    print("[3/5] LightGBM 모델 학습 시작...")
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], eval_metric='logloss',
              callbacks=[early_stopping(100), log_evaluation(100)])

    print("\n[4/5] 성능 검증 중...")
    prob = model.predict_proba(X_test)[:, 1]
    th = 0.50 if prob.max() >= 0.50 else prob.max() * 0.9
    pred = (prob >= th).astype(int)
    print(f"✅ LightGBM 검증 정밀도: {precision_score(y_test, pred, zero_division=0):.2%}")

    joblib.dump(model, MODEL_PATH)
    joblib.dump(features, FEATURE_PATH)
    print(f"[5/5] 모델 저장 완료: {MODEL_PATH}")


if __name__ == "__main__":
    train_hybrid_lgbm()