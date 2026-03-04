import os
import sqlite3
import pandas as pd
import numpy as np
import joblib
import FinanceDataReader as fdr
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import precision_score
import warnings

warnings.filterwarnings('ignore')

# --- [신규] 경로 설정 (상대 참조) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, 'kospi_stock_data.db')
BULL_XGB_PATH = os.path.join(DATA_DIR, 'bull_xgb_model.pkl')
BULL_LGBM_PATH = os.path.join(DATA_DIR, 'bull_lgbm_model.pkl')


# ==========================================
# 1. 우량 대장주 필터링 (FDR + DB Fallback 적용)
# ==========================================
def get_bull_target_codes():
    print("[1/4] 우량 대장주 필터링 중 (Bull 모델용)...")
    try:
        df_krx = fdr.StockListing('KOSPI')
        # 💡 시총 상위 500개 중 거래량 상위 300개 추출 (잡주 배제 & 풀 확대)
        top_500 = df_krx.sort_values(by='Marcap', ascending=False).head(500)
        target_top = top_500.sort_values(by='Volume', ascending=False).head(300)
        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top['Code'].tolist()

    except Exception as e:
        print(f"⚠️ FDR 종목 리스트 수집 실패 ({e}). DB 데이터로 우회합니다...")
        try:
            conn = sqlite3.connect(DB_NAME)
            max_date_query = "SELECT MAX(Date) FROM daily_stock_quotes"
            latest_date = pd.read_sql(max_date_query, conn).iloc[0, 0]

            # 💡 DB 우회 시에도 300개 추출
            query = f"SELECT Code FROM daily_stock_quotes WHERE Date = '{latest_date}' ORDER BY Volume DESC LIMIT 300"
            top_codes_df = pd.read_sql(query, conn)
            conn.close()

            if top_codes_df.empty:
                return []
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['Code'].tolist()
        except Exception as db_e:
            print(f"🚨 DB Fallback 실패: {db_e}")
            return []

# ==========================================
# 2. 데이터 로드 및 전처리 (최적화)
# ==========================================
def load_and_preprocess_bull(codes):
    print(f"[2/4] {len(codes)}개 종목 상승장 데이터 로드 및 최신 지표 생성 중...")
    conn = sqlite3.connect(DB_NAME)
    all_processed_data = []

    # 💡 [최적화] 두 모델이 사용하는 모든 컬럼만 명시적으로 가져옴
    cols_to_fetch = "Date, Code, Open, High, Low, Close, Volume, MA5, MA20, MACD, MACD_Sig, VWAP, OBV, BBL, BBU, RSI, ATR, BBB, BBP, Return, Foreign_Net, Inst_Net, Margin_Rate"

    for code in codes:
        # 상승장 국면(25.08 ~ 26.01) 데이터만 필터링
        query = f"SELECT {cols_to_fetch} FROM daily_stock_quotes WHERE Code = '{code}' AND Date >= '2025-08-01' AND Date <= '2026-01-15' ORDER BY Date ASC"
        df = pd.read_sql(query, conn)

        if len(df) < 60:
            continue

        # 파생 지표 생성
        df['Vol_Change'] = df['Volume'].pct_change()
        df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
        df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
        df['RSI_Slope'] = df['RSI'].diff()
        df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
        df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(window=5).mean() + 1e-9)
        df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
        # [추가할 파생 지표 로직] df['Dist_MA5'] = ... 바로 밑에 삽입
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

        # 필수 특징 생성 (추세)
        df['Up_Trend_2D'] = (df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)
        df['Up_Trend_2D'] = df['Up_Trend_2D'].astype(int)

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
        if not df.empty:
            all_processed_data.append(df)

    conn.close()
    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()


# ==========================================
# 3. 모델 학습 메인 함수
# ==========================================
def train_bull_specialists():
    target_codes = get_bull_target_codes()
    if not target_codes:
        print("[-] 학습할 대상 종목이 없습니다.")
        return

    total_df = load_and_preprocess_bull(target_codes)
    if total_df.empty:
        print("[-] 상승장 기간의 데이터가 부족합니다.")
        return

    features_xgb = ['Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'VWAP', 'OBV', 'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy',
                    'Foreign_Net_Roll5', 'Inst_Net_Roll5']
    features_lgbm = ['BB_Pos', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change', 'ATR', 'BBB', 'BBP',
                     'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Margin_Rate_Change', 'Margin_Rate_Roll5']

    # 시간순 정렬 및 데이터 분할
    total_df = total_df.sort_values(by='Date')
    split_idx = int(len(total_df) * 0.8)
    train_df, test_df = total_df.iloc[:split_idx], total_df.iloc[split_idx:]
    y_train, y_test = train_df['Target'], test_df['Target']

    # --- 동적 가중치 계산 ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count
    print(f"\n📊 [데이터 현황] 오답: {neg_count}개 | 정답: {pos_count}개 (가중치: {dynamic_weight:.1f}배)")

    # ==========================================
    # [Bull XGBoost: 추세 전문가]
    # ==========================================
    print(f"\n[3/4] Bull XGBoost 학습 중...")
    bull_xgb = XGBClassifier(
        n_estimators=1000, learning_rate=0.01, max_depth=6,
        scale_pos_weight=dynamic_weight, random_state=42, n_jobs=-1
    )
    bull_xgb.fit(train_df[features_xgb], y_train)

    prob_x = bull_xgb.predict_proba(test_df[features_xgb])[:, 1]
    max_x = prob_x.max()
    th_x = 0.50 if max_x >= 0.50 else max_x * 0.9
    pred_x = (prob_x >= th_x).astype(int)
    print(f"💡 [Bull XGB] 최고 확신도: {max_x * 100:.2f}% | 정밀도: {precision_score(y_test, pred_x, zero_division=0):.2%}")

    joblib.dump(bull_xgb, BULL_XGB_PATH)

    # ==========================================
    # [Bull LightGBM: 변동성 전문가]
    # ==========================================
    print(f"\n[4/4] Bull LightGBM 학습 중...")
    bull_lgbm = LGBMClassifier(
        n_estimators=1000, learning_rate=0.01, max_depth=6,
        scale_pos_weight=dynamic_weight, random_state=42, n_jobs=-1, force_col_wise=True
    )
    bull_lgbm.fit(train_df[features_lgbm], y_train)

    prob_l = bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    max_l = prob_l.max()
    th_l = 0.50 if max_l >= 0.50 else max_l * 0.9
    pred_l = (prob_l >= th_l).astype(int)
    print(f"💡 [Bull LGBM] 최고 확신도: {max_l * 100:.2f}% | 정밀도: {precision_score(y_test, pred_l, zero_division=0):.2%}")

    joblib.dump(bull_lgbm, BULL_LGBM_PATH)

    print("\n✅ 상승장 전용 모델 2종 갱신 및 파일 저장 완료!")


if __name__ == "__main__":
    train_bull_specialists()