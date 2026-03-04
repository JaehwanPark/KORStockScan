import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
import FinanceDataReader as fdr
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score
import warnings

warnings.filterwarnings('ignore')

# --- 경로 설정 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')

HYBRID_XGB_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
HYBRID_LGBM_PATH = os.path.join(DATA_DIR, 'hybrid_lgbm_model.pkl')
BULL_XGB_PATH = os.path.join(DATA_DIR, 'bull_xgb_model.pkl')
BULL_LGBM_PATH = os.path.join(DATA_DIR, 'bull_lgbm_model.pkl')
META_MODEL_PATH = os.path.join(DATA_DIR, 'stacking_meta_model.pkl')


# ==========================================
# [수정] 우량 대장주 필터링 (종목 대폭 확대)
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
            conn = sqlite3.connect(DB_NAME)
            latest_date = pd.read_sql("SELECT MAX(Date) FROM daily_stock_quotes", conn).iloc[0, 0]
            top_codes_df = pd.read_sql(f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300", conn)
            conn.close()
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist() if not top_codes_df.empty else []
        except: return []


# ==========================================
# 2. 데이터 로드 및 전처리 (최적화)
# ==========================================
def load_and_preprocess_stacking(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 가공 및 전체 지표(수급/신용 포함) 생성 중...")
    conn = sqlite3.connect(DB_NAME)
    all_processed_data = []

    # 💡 [변경] 수급/신용 컬럼 3개 추가 로드
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV, BBL, BBU, RSI, ATR, BBB, BBP, Return, Foreign_Net, Inst_Net, Margin_Rate"

    for code in codes:
        query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' ORDER BY Date DESC LIMIT 750"
        df = pd.read_sql(query, conn)
        df = df.sort_values('Date', ascending=True).reset_index(drop=True)

        if len(df) < 150: continue

        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

        # 💡 [신규] 수급 및 신용잔고 파생 피처 계산
        vol_safe = df['Volume'] + 1e-9
        df['Foreign_Net'] = df['Foreign_Net'].fillna(0)
        df['Inst_Net'] = df['Inst_Net'].fillna(0)
        df['Margin_Rate'] = df['Margin_Rate'].fillna(0)

        df['Foreign_Net_Roll5'] = df['Foreign_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Inst_Net_Roll5'] = df['Inst_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Dual_Net_Buy'] = ((df['Foreign_Net'] > 0) & (df['Inst_Net'] > 0)).astype(int)
        df['Foreign_Vol_Ratio'] = df['Foreign_Net'] / vol_safe
        df['Inst_Vol_Ratio'] = df['Inst_Net'] / vol_safe
        df['Margin_Rate_Change'] = df['Margin_Rate'].diff()
        df['Margin_Rate_Roll5'] = df['Margin_Rate'].rolling(5).mean()

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
        if not df.empty: all_processed_data.append(df)

    conn.close()
    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()


# ==========================================
# 3. 스태킹 앙상블 메인 로직
# ==========================================
def train_meta_model():
    target_codes = get_stacking_target_codes()
    if not target_codes: return

    total_df = load_and_preprocess_stacking(target_codes)
    if total_df.empty: return

    print("[3/5] 하위 전문가 모델(Base Models) 로드 중...")
    try:
        xgb_model = joblib.load(HYBRID_XGB_PATH)
        lgbm_model = joblib.load(HYBRID_LGBM_PATH)
        bull_xgb = joblib.load(BULL_XGB_PATH)
        bull_lgbm = joblib.load(BULL_LGBM_PATH)
    except Exception as e:
        print(f"[-] 모델 로드 실패. 하위 모델을 먼저 학습하세요. 에러: {e}")
        return

    # 💡 [변경] 학습 시 사용했던 신규 피처 리스트로 완벽히 교체
    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy',
                    'Foreign_Net_Roll5', 'Inst_Net_Roll5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP',
                     'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']

    unique_dates = sorted(total_df['Date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]

    train_df = total_df[total_df['Date'] < split_date]
    test_df = total_df[total_df['Date'] >= split_date]
    y_train = train_df['Target']
    y_test = test_df['Target']

    print("[4/5] 메타 학습용 OOF(Out-of-Fold) 확률 데이터 생성 중...")

    meta_X_train = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(train_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(train_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(train_df[features_xgb])[:, 1],
        'Bull_LGBM_Prob': bull_lgbm.predict_proba(train_df[features_lgbm])[:, 1]
    })

    meta_X_test = pd.DataFrame({
        'XGB_Prob': xgb_model.predict_proba(test_df[features_xgb])[:, 1],
        'LGBM_Prob': lgbm_model.predict_proba(test_df[features_lgbm])[:, 1],
        'Bull_XGB_Prob': bull_xgb.predict_proba(test_df[features_xgb])[:, 1],
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
    # 🚀 [추가] 정밀 백테스트(V2)를 위한 AI 예측 결과 저장
    # ==========================================
    print("\n💾 백테스트용 AI 예측 결과(ai_predictions.csv)를 생성합니다...")

    # 원본 test_df의 Date와 Code만 복사해 옵니다. ('Name' 삭제)
    df_results = test_df[['Date', 'Code']].copy()

    # 방금 구한 각 모델들의 OOF 예측 확률과 최종 Stacking 확률을 주입합니다.
    df_results['XGB_Prob'] = np.round(meta_X_test['XGB_Prob'].values, 4)
    df_results['LGBM_Prob'] = np.round(meta_X_test['LGBM_Prob'].values, 4)
    df_results['Bull_XGB_Prob'] = np.round(meta_X_test['Bull_XGB_Prob'].values, 4)
    df_results['Bull_LGBM_Prob'] = np.round(meta_X_test['Bull_LGBM_Prob'].values, 4)
    df_results['Stacking_Prob'] = np.round(meta_pred_proba, 4)
    df_results['Actual_Target'] = y_test.values

    # 시간순 백테스트를 위해 날짜 오름차순 정렬
    df_results = df_results.sort_values(by=['Date', 'Code']).reset_index(drop=True)

    # CSV 저장
    save_path = os.path.join(DATA_DIR, 'ai_predictions.csv')
    df_results.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"✅ 테스트 세트(총 {len(df_results):,}건) 예측 결과가 저장되었습니다: {save_path}")


if __name__ == "__main__":
    train_meta_model()