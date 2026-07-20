import os
import pandas as pd
import numpy as np
import joblib
import FinanceDataReader as fdr
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import precision_score
from sqlalchemy import create_engine, text
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. 디렉토리 및 DB 경로 설정
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# 🎯 PostgreSQL 연결 설정
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan",
)
engine = create_engine(DB_URL)

BULL_XGB_PATH = os.path.join(DATA_DIR, "bull_xgb_model.pkl")
BULL_LGBM_PATH = os.path.join(DATA_DIR, "bull_lgbm_model.pkl")


# ==========================================
# 2. 우량 대장주 필터링 (FDR + PostgreSQL Fallback 적용)
# ==========================================
def get_bull_target_codes():
    print("[1/4] 우량 대장주 필터링 중 (Bull 모델용)...")
    try:
        df_krx = fdr.StockListing("KOSPI")
        # 시총 상위 500개 중 거래량 상위 300개 추출
        top_500 = df_krx.sort_values(by="Marcap", ascending=False).head(500)
        target_top = top_500.sort_values(by="Volume", ascending=False).head(300)
        print(f"✅ FDR 기반으로 시총/거래량 상위 {len(target_top)}종목을 추출했습니다.")
        return target_top["Code"].tolist()

    except Exception as e:
        print(f"⚠️ FDR 종목 리스트 수집 실패 ({e}). DB 데이터로 우회합니다...")
        try:
            with engine.connect() as conn:
                max_date_query = "SELECT MAX(quote_date) FROM daily_stock_quotes"
                latest_date = pd.read_sql(text(max_date_query), conn).iloc[0, 0]

                query = f"""
                    SELECT stock_code FROM daily_stock_quotes 
                    WHERE quote_date = '{latest_date}' 
                    ORDER BY volume DESC LIMIT 300
                """
                top_codes_df = pd.read_sql(text(query), conn)

            if top_codes_df.empty:
                return []
            print(
                f"✅ DB 기반 최근 거래량 상위 {len(top_codes_df)}종목을 추출했습니다."
            )
            return top_codes_df["stock_code"].tolist()
        except Exception as db_e:
            print(f"🚨 DB Fallback 실패: {db_e}")
            return []


# ==========================================
# 3. 데이터 로드 및 전처리 (DB 스키마 최적화)
# ==========================================
def load_and_preprocess_bull(codes):
    print(f"[2/4] {len(codes)}개 종목 상승장 데이터 로드 및 최신 지표 생성 중...")
    all_processed_data = []

    # 💡 두 모델이 사용하는 컬럼명 소문자로 매핑 (DB 스키마)
    cols_to_fetch = """
        quote_date, stock_code, open_price, high_price, low_price, close_price, volume, 
        ma5, ma20, macd, macd_sig, vwap, obv, rsi, atr, bbb, bbp, daily_return, 
        foreign_net, inst_net, margin_rate
    """

    with engine.connect() as conn:
        for code in codes:
            # 상승장 국면(25.08 ~ 26.01) 데이터만 필터링
            query = f"""
                SELECT {cols_to_fetch} 
                FROM daily_stock_quotes 
                WHERE stock_code = '{code}' 
                AND quote_date >= '2025-08-01' 
                AND quote_date <= '2026-01-15' 
                ORDER BY quote_date ASC
            """
            df = pd.read_sql(text(query), conn)

            if len(df) < 60:
                continue

            # 파생 지표 생성
            df["vol_change"] = df["volume"].pct_change()
            df["ma_ratio"] = df["close_price"] / (df["ma20"] + 1e-9)
            df["rsi_slope"] = df["rsi"].diff()
            df["range_ratio"] = (df["high_price"] - df["low_price"]) / (
                df["close_price"] + 1e-9
            )
            df["vol_momentum"] = df["volume"] / (
                df["volume"].rolling(window=5).mean() + 1e-9
            )
            df["dist_ma5"] = df["close_price"] / (df["ma5"] + 1e-9)

            # 💡 [여기에 추가!!] atr_ratio 파생 지표 생성
            df["atr_ratio"] = df["atr"] / (df["close_price"] + 1e-9)

            # 수급 및 신용 지표 계산
            vol_safe = df["volume"] + 1e-9
            df["foreign_net"] = df["foreign_net"].fillna(0)
            df["inst_net"] = df["inst_net"].fillna(0)
            df["margin_rate"] = df["margin_rate"].fillna(0)

            df["foreign_net_roll5"] = df["foreign_net"].rolling(5).sum() / (
                df["volume"].rolling(5).sum() + 1e-9
            )
            df["inst_net_roll5"] = df["inst_net"].rolling(5).sum() / (
                df["volume"].rolling(5).sum() + 1e-9
            )
            df["dual_net_buy"] = (
                (df["foreign_net"] > 0) & (df["inst_net"] > 0)
            ).astype(int)
            df["foreign_vol_ratio"] = df["foreign_net"] / vol_safe
            df["inst_vol_ratio"] = df["inst_net"] / vol_safe
            df["margin_rate_change"] = df["margin_rate"].diff()
            df["margin_rate_roll5"] = df["margin_rate"].rolling(5).mean()

            # 필수 특징 생성 (추세)
            df["up_trend_2d"] = (df["close_price"].diff(1) > 0) & (
                df["close_price"].shift(1).diff(1) > 0
            )
            df["up_trend_2d"] = df["up_trend_2d"].astype(int)

            # 🎯 3일 단기 스윙 정답지(Target) 생성 로직
            df["next1_open"] = df["open_price"].shift(-1)

            for i in range(1, 4):
                df[f"next{i}_high"] = df["high_price"].shift(-i)
                df[f"next{i}_low"] = df["low_price"].shift(-i)

            df["max_high_3d"] = df[["next1_high", "next2_high", "next3_high"]].max(
                axis=1
            )
            df["min_low_3d"] = df[["next1_low", "next2_low", "next3_low"]].min(axis=1)

            hit_target = (df["max_high_3d"] / (df["next1_open"] + 1e-9)) >= 1.045
            no_stop_loss = (df["min_low_3d"] / (df["next1_open"] + 1e-9)) >= 0.970

            df["target"] = np.where(hit_target & no_stop_loss, 1, 0)

            df = df.replace([np.inf, -np.inf], np.nan).dropna()
            if not df.empty:
                all_processed_data.append(df)

    return pd.concat(all_processed_data) if all_processed_data else pd.DataFrame()


# ==========================================
# 4. 모델 학습 메인 함수
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

    # 💡 DB 스키마에 맞춘 소문자 피처 리스트
    features_xgb = [
        "daily_return",
        "ma_ratio",
        "macd",
        "macd_sig",
        "vwap",
        "obv",
        "up_trend_2d",
        "dist_ma5",
        "dual_net_buy",
        "foreign_net_roll5",
        "inst_net_roll5",
        "bbb",
        "bbp",
        "atr_ratio",
        "rsi",  # 👈 이 4개가 추가됨!
    ]
    features_lgbm = [
        "bbp",
        "rsi",
        "rsi_slope",
        "range_ratio",
        "vol_momentum",
        "vol_change",
        "atr",
        "bbb",
        "foreign_vol_ratio",
        "inst_vol_ratio",
        "margin_rate_change",
        "margin_rate_roll5",
    ]

    # 시간순 정렬 및 데이터 분할
    total_df = total_df.sort_values(by="quote_date")
    split_idx = int(len(total_df) * 0.8)
    train_df, test_df = total_df.iloc[:split_idx], total_df.iloc[split_idx:]
    y_train, y_test = train_df["target"], test_df["target"]

    # --- 동적 가중치 계산 ---
    neg_count = (y_train == 0).sum()
    pos_count = (y_train == 1).sum()
    dynamic_weight = 1.0 if pos_count == 0 else neg_count / pos_count
    print(
        f"\n📊 [데이터 현황] 오답: {neg_count}개 | 정답: {pos_count}개 (가중치: {dynamic_weight:.1f}배)"
    )

    # ==========================================
    # [Bull XGBoost: 추세 전문가]
    # ==========================================
    print(f"\n[3/4] Bull XGBoost 학습 중...")
    bull_xgb = XGBClassifier(
        n_estimators=1000,
        learning_rate=0.01,
        max_depth=6,
        scale_pos_weight=dynamic_weight,
        random_state=42,
        n_jobs=-1,
    )
    bull_xgb.fit(train_df[features_xgb], y_train)

    prob_x = bull_xgb.predict_proba(test_df[features_xgb])[:, 1]
    max_x = prob_x.max()
    th_x = 0.50 if max_x >= 0.50 else max_x * 0.9
    pred_x = (prob_x >= th_x).astype(int)
    print(
        f"💡 [Bull XGB] 최고 확신도: {max_x * 100:.2f}% | 정밀도: {precision_score(y_test, pred_x, zero_division=0):.2%}"
    )

    joblib.dump(bull_xgb, BULL_XGB_PATH)

    # ==========================================
    # [Bull LightGBM: 변동성 전문가]
    # ==========================================
    print(f"\n[4/4] Bull LightGBM 학습 중...")
    bull_lgbm = LGBMClassifier(
        n_estimators=1000,
        learning_rate=0.01,
        max_depth=6,
        scale_pos_weight=dynamic_weight,
        random_state=42,
        n_jobs=-1,
        force_col_wise=True,
    )
    bull_lgbm.fit(train_df[features_lgbm], y_train)

    prob_l = bull_lgbm.predict_proba(test_df[features_lgbm])[:, 1]
    max_l = prob_l.max()
    th_l = 0.50 if max_l >= 0.50 else max_l * 0.9
    pred_l = (prob_l >= th_l).astype(int)
    print(
        f"💡 [Bull LGBM] 최고 확신도: {max_l * 100:.2f}% | 정밀도: {precision_score(y_test, pred_l, zero_division=0):.2%}"
    )

    joblib.dump(bull_lgbm, BULL_LGBM_PATH)

    print("\n✅ 상승장 전용 모델 2종 갱신 및 파일 저장 완료!")


if __name__ == "__main__":
    train_bull_specialists()
