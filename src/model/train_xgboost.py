import os
import FinanceDataReader as fdr
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score
from xgboost import XGBClassifier
from sqlalchemy import create_engine, text

# ==========================================
# 1. 디렉토리 및 DB 경로 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))

DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

MODEL_PATH = os.path.join(DATA_DIR, 'hybrid_xgb_model.pkl')
FEATURE_PATH = os.path.join(DATA_DIR, 'hybrid_features.pkl')
# 🎯 PostgreSQL 연결 설정 (환경 변수 우선, 기본값 세팅).
DB_URL = os.getenv("DATABASE_URL", "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan")
engine = create_engine(DB_URL)

# ==========================================
# 2. 우량 대장주 필터링 (FDR + PostgreSQL Fallback)
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
            with engine.connect() as conn:
                # 테이블 스키마 적용: quote_date, volume, stock_code
                latest_date_query = "SELECT MAX(quote_date) FROM daily_stock_quotes"
                latest_date = pd.read_sql(text(latest_date_query), conn).iloc[0, 0]
                
                top_codes_query = f"""
                    SELECT stock_code FROM daily_stock_quotes 
                    WHERE quote_date = '{latest_date}' 
                    ORDER BY volume DESC LIMIT 300
                """
                top_codes_df = pd.read_sql(text(top_codes_query), conn)
                
            print(f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다.")
            return top_codes_df['stock_code'].tolist() if not top_codes_df.empty else []
        except Exception as e: 
            print(f"❌ DB 종목 추출 실패: {e}")
            return []


# ==========================================
# 3. 데이터 로드 및 전처리 (DB 스키마 완벽 반영)
# ==========================================
def load_and_preprocess(codes):
    print(f"[2/5] {len(codes)}개 종목 데이터 로드 및 정답지 생성 중...")
    all_data = []

    # DB에 이미 계산된 훌륭한 지표들(bbb, bbp, atr, rsi)을 바로 가져옵니다.
    cols_to_fetch = """
        quote_date, stock_code, open_price, high_price, low_price, close_price, volume, 
        ma5, ma20, rsi, macd, macd_sig, bbb, bbp, vwap, obv, atr, daily_return, 
        foreign_net, inst_net
    """

    with engine.connect() as conn:
        for code in codes:
            query = f"""
                SELECT {cols_to_fetch} 
                FROM daily_stock_quotes 
                WHERE stock_code = '{code}' 
                  AND quote_date >= '2024-11-01' 
                  AND quote_date <= '2025-07-31'
                ORDER BY quote_date ASC
            """
            df = pd.read_sql(text(query), conn)
            
            if df.empty or len(df) < 150: 
                continue

            # 과거 날짜부터 정렬
            df = df.sort_values('quote_date', ascending=True).reset_index(drop=True)

            # 파생 변수 계산
            df['ma_ratio'] = df['close_price'] / (df['ma20'] + 1e-9)
            df['dist_ma5'] = df['close_price'] / (df['ma5'] + 1e-9)
            df['up_trend_2d'] = ((df['close_price'].diff(1) > 0) & (df['close_price'].shift(1).diff(1) > 0)).astype(int)

            # 수급 지표 롤링 (결측치는 0으로 처리)
            df['foreign_net'] = df['foreign_net'].fillna(0)
            df['inst_net'] = df['inst_net'].fillna(0)
            df['foreign_net_roll5'] = df['foreign_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
            df['inst_net_roll5'] = df['inst_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
            df['dual_net_buy'] = ((df['foreign_net'] > 0) & (df['inst_net'] > 0)).astype(int)

            # 종가 대비 ATR 비율 (DB의 atr 컬럼 활용)
            df['atr_ratio'] = df['atr'] / (df['close_price'] + 1e-9)

            # 🎯 3일 단기 스윙 정답지(Target) 생성
            df['next1_open'] = df['open_price'].shift(-1)
            for i in range(1, 4):
                df[f'next{i}_high'] = df['high_price'].shift(-i)
                df[f'next{i}_low'] = df['low_price'].shift(-i)

            df['max_high_3d'] = df[['next1_high', 'next2_high', 'next3_high']].max(axis=1)
            df['min_low_3d'] = df[['next1_low', 'next2_low', 'next3_low']].min(axis=1)

            # 조건: 3일 내 +4.5% 도달 & -3.0% 손절 방어
            hit_target = (df['max_high_3d'] / (df['next1_open'] + 1e-9)) >= 1.045
            no_stop_loss = (df['min_low_3d'] / (df['next1_open'] + 1e-9)) >= 0.970
            df['target'] = np.where(hit_target & no_stop_loss, 1, 0)

            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if not df.empty: 
                all_data.append(df)

    return pd.concat(all_data, axis=0) if all_data else pd.DataFrame()


# ==========================================
# 4. 모델 학습 
# ==========================================
def train_hybrid_xgb():
    target_codes = get_hybrid_top_codes()
    if not target_codes: 
        print("❌ 대상 종목이 없어 학습을 종료합니다.")
        return
        
    total_df = load_and_preprocess(target_codes)
    if total_df.empty: 
        print("❌ 학습할 데이터가 존재하지 않습니다.")
        return

    # 💡 [업데이트] DB 스키마에 맞춘 소문자 컬럼명 적용 및 rsi, bbb, bbp 추가
    features = [
        'daily_return', 'ma_ratio', 'macd', 'macd_sig', 'vwap', 'obv', 
        'up_trend_2d', 'dist_ma5', 'dual_net_buy', 'foreign_net_roll5', 'inst_net_roll5',
        'bbb', 'bbp', 'atr_ratio', 'rsi'
    ]

    unique_dates = sorted(total_df['quote_date'].unique())
    split_date = unique_dates[int(len(unique_dates) * 0.8)]
    train_df, test_df = total_df[total_df['quote_date'] < split_date], total_df[total_df['quote_date'] >= split_date]

    X_train, y_train = train_df[features], train_df['target']
    X_test, y_test = test_df[features], test_df['target']

    neg_count, pos_count = (y_train == 0).sum(), (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count

    print(f"[3/5] XGBoost 모델 학습 시작... (Train: {len(train_df)}행, Test: {len(test_df)}행)")
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