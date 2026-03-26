import os
import warnings
import joblib
import numpy as np
import pandas as pd
import pandas_ta as ta
from pandas.api.types import is_string_dtype, is_bool_dtype, is_numeric_dtype
import FinanceDataReader as fdr

from sqlalchemy import create_engine, text
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, precision_score

warnings.filterwarnings("ignore")
pd.set_option('future.no_silent_downcasting', True)

# =========================================================
# 0. 공통 경로 / DB
# =========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..'))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
MODELS_DIR = os.path.join(DATA_DIR, 'models_v2')
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan"
)
engine = create_engine(DB_URL)

# =========================================================
# 1. 공통 파일 경로
# =========================================================
HYBRID_XGB_PACK = os.path.join(MODELS_DIR, 'hybrid_xgb_pack.pkl')
HYBRID_LGBM_PACK = os.path.join(MODELS_DIR, 'hybrid_lgbm_pack.pkl')
BULL_XGB_PACK = os.path.join(MODELS_DIR, 'bull_xgb_pack.pkl')
BULL_LGBM_PACK = os.path.join(MODELS_DIR, 'bull_lgbm_pack.pkl')
META_MODEL_PACK = os.path.join(MODELS_DIR, 'stacking_meta_pack.pkl')

AI_PRED_PATH = os.path.join(DATA_DIR, 'ai_predictions_v2.csv')
AI_PICKS_PATH = os.path.join(DATA_DIR, 'ai_picks_v2.csv')

# =========================================================
# 2. 기본 피처 목록
# =========================================================
XGB_FEATURES = [
    'Return', 'MA_Ratio', 'MACD', 'MACD_Sig', 'Close_VWAP_Ratio', 'OBV_Change_5',
    'Up_Trend_2D', 'Dist_MA5', 'Dual_Net_Buy', 'Foreign_Net_Roll5', 'Inst_Net_Roll5',
    'BBB', 'BBP', 'ATR_Ratio', 'RSI', 'Breakout_20', 'Turnover_Shock',
    'Idx_Ret20', 'Idx_ATR_Ratio'
]

LGBM_FEATURES = [
    'BBP', 'RSI', 'RSI_Slope', 'Range_Ratio', 'Vol_Momentum', 'Vol_Change',
    'ATR_Ratio', 'BBB', 'Foreign_Vol_Ratio', 'Inst_Vol_Ratio',
    'Margin_Rate_Change', 'Margin_Rate_Roll5', 'Turnover_Shock', 'Breakout_20',
    'Idx_Ret20', 'Idx_ATR_Ratio'
]

META_FEATURES = [
    'HX', 'HL', 'BX', 'BL',
    'Mean_Prob', 'Std_Prob', 'Max_Prob', 'Min_Prob',
    'Bull_Mean', 'Hybrid_Mean', 'Bull_Hybrid_Gap',
    'Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio',
    'Breakout_20', 'Turnover_Shock'
]

# =========================================================
# 3. 공통 유틸
# =========================================================
def save_pickle(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(obj, path)

def load_pickle(path):
    return joblib.load(path)

def zfill_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)

def get_period_liquid_codes(start_date: str, end_date: str, top_n: int = 300, min_days: int = 80):
    """
    point-in-time 완전판은 아니지만,
    적어도 '현재 시총/거래량'이 아니라 '해당 기간 평균 거래대금' 기준으로 universe 선정.
    """
    print(f"[Universe] {start_date} ~ {end_date} 구간 평균 거래대금 상위 {top_n} 종목 추출...")
    query = f"""
        SELECT stock_code,
               COUNT(*) AS n_days,
               AVG(close_price * volume) AS avg_turnover
        FROM daily_stock_quotes
        WHERE quote_date >= '{start_date}'
          AND quote_date <= '{end_date}'
        GROUP BY stock_code
        HAVING COUNT(*) >= {min_days}
        ORDER BY avg_turnover DESC
        LIMIT {top_n}
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    if df.empty:
        print("⚠️ DB 거래대금 기준 universe 추출 실패. FDR fallback 시도...")
        try:
            df_krx = fdr.StockListing('KOSPI')
            top = df_krx.sort_values('Marcap', ascending=False).head(500)
            top = top.sort_values('Volume', ascending=False).head(top_n)
            return top['Code'].astype(str).str.zfill(6).tolist()
        except Exception as e:
            print(f"❌ universe fallback 실패: {e}")
            return []

    return zfill_code(df['stock_code']).tolist()

# =========================================================
# 4. Raw 데이터 fetch
# =========================================================
def fetch_raw_quotes_by_code(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    query = f"""
        SELECT
            quote_date, stock_code,
            open_price, high_price, low_price, close_price, volume,
            foreign_net, inst_net, margin_rate
        FROM daily_stock_quotes
        WHERE stock_code = '{code}'
          AND quote_date >= '{start_date}'
          AND quote_date <= '{end_date}'
        ORDER BY quote_date ASC
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    if df.empty:
        return df

    df['quote_date'] = pd.to_datetime(df['quote_date'])
    df['stock_code'] = zfill_code(df['stock_code'])
    return df

# =========================================================
# 5. SSOT Feature Engineering
# =========================================================
def calculate_all_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    반드시 종목별(single-code) 데이터로 호출.
    """
    if raw_df.empty:
        return raw_df.copy()

    df = raw_df.copy().sort_values('quote_date').reset_index(drop=True)

    rename_map = {
        'quote_date': 'Date', 'stock_code': 'Code',
        'open_price': 'Open', 'high_price': 'High', 'low_price': 'Low',
        'close_price': 'Close', 'volume': 'Volume',
        'foreign_net': 'Foreign_Net', 'inst_net': 'Inst_Net', 'margin_rate': 'Margin_Rate'
    }
    df = df.rename(columns=rename_map)

    required = ['Date', 'Code', 'Open', 'High', 'Low', 'Close', 'Volume']
    for c in required:
        if c not in df.columns:
            raise ValueError(f"필수 컬럼 누락: {c}")

    # 원시 flow 결측 처리: 전일 값 ffill 금지
    for c in ['Foreign_Net', 'Inst_Net', 'Margin_Rate']:
        if c not in df.columns:
            df[c] = 0.0
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)

    # 기본 지표
    df['Return'] = df['Close'].pct_change()
    df['MA5'] = ta.sma(df['Close'], length=5)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA60'] = ta.sma(df['Close'], length=60)
    df['MA120'] = ta.sma(df['Close'], length=120)

    df['RSI'] = ta.rsi(df['Close'], length=14)

    macd_df = ta.macd(df['Close'])
    if macd_df is not None and not macd_df.empty:
        # pandas_ta 컬럼 순서 기준
        df['MACD'] = macd_df.iloc[:, 0]
        df['MACD_Hist'] = macd_df.iloc[:, 1]
        df['MACD_Sig'] = macd_df.iloc[:, 2]
    else:
        df['MACD'] = 0
        df['MACD_Hist'] = 0
        df['MACD_Sig'] = 0

    bb_df = ta.bbands(df['Close'], length=20, std=2, ddof=1)
    if bb_df is not None and not bb_df.empty:
        df['BBL'] = bb_df.iloc[:, 0]
        df['BBM'] = bb_df.iloc[:, 1]
        df['BBU'] = bb_df.iloc[:, 2]
        df['BBB'] = bb_df.iloc[:, 3]
        df['BBP'] = bb_df.iloc[:, 4]
    else:
        for c in ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']:
            df[c] = 0

    df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])
    df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)

    # 일봉 VWAP 유사치: 누적 typical price * volume / cumulative volume
    typical = (df['High'] + df['Low'] + df['Close']) / 3.0
    df['VWAP'] = (typical * df['Volume']).cumsum() / (df['Volume'].cumsum() + 1e-9)

    # 파생
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['ATR_Ratio'] = df['ATR'] / (df['Close'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

    # 수급/신용 파생
    vol_safe = df['Volume'] + 1e-9
    df['Foreign_Vol_Ratio'] = df['Foreign_Net'] / vol_safe
    df['Inst_Vol_Ratio'] = df['Inst_Net'] / vol_safe

    df['Foreign_Net_Roll5'] = df['Foreign_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
    df['Inst_Net_Roll5'] = df['Inst_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
    df['Dual_Net_Buy'] = ((df['Foreign_Net'] > 0) & (df['Inst_Net'] > 0)).astype(int)

    df['Foreign_Net_Accel'] = (
        df['Foreign_Net'].ewm(span=5, adjust=False).mean() -
        df['Foreign_Net'].ewm(span=20, adjust=False).mean()
    )
    df['Inst_Net_Accel'] = (
        df['Inst_Net'].ewm(span=5, adjust=False).mean() -
        df['Inst_Net'].ewm(span=20, adjust=False).mean()
    )

    df['Margin_Rate_Change'] = df['Margin_Rate'].diff()
    df['Margin_Rate_Roll5'] = df['Margin_Rate'].rolling(5).mean()

    # scale-invariant + 스윙용 추가
    df['Close_VWAP_Ratio'] = df['Close'] / (df['VWAP'] + 1e-9)
    df['Turnover'] = df['Close'] * df['Volume']
    df['Turnover_Shock'] = df['Turnover'] / (df['Turnover'].rolling(20).median() + 1e-9)
    df['Breakout_20'] = df['Close'] / (df['High'].rolling(20).max().shift(1) + 1e-9)
    df['Breakdown_20'] = df['Close'] / (df['Low'].rolling(20).min().shift(1) + 1e-9)
    df['OBV_Change_5'] = df['OBV'].diff(5)
    df['Gap_Return'] = df['Open'] / (df['Close'].shift(1) + 1e-9) - 1.0
    df['OC_Return'] = df['Close'] / (df['Open'] + 1e-9) - 1.0
    df['Body_Ratio'] = (df['Close'] - df['Open']) / ((df['High'] - df['Low']) + 1e-9)
    df['Upper_Wick_Ratio'] = (df['High'] - df[['Open', 'Close']].max(axis=1)) / ((df['High'] - df['Low']) + 1e-9)
    df['Lower_Wick_Ratio'] = (df[['Open', 'Close']].min(axis=1) - df['Low']) / ((df['High'] - df['Low']) + 1e-9)

    # 이상치 clip
    clip_cols = [
        'Return', 'Vol_Change', 'Vol_Momentum', 'RSI_Slope', 'Range_Ratio',
        'Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Foreign_Net_Roll5', 'Inst_Net_Roll5',
        'Turnover_Shock', 'Gap_Return', 'OC_Return', 'OBV_Change_5'
    ]
    for c in clip_cols:
        if c in df.columns:
            df[c] = df[c].clip(lower=df[c].quantile(0.01), upper=df[c].quantile(0.99))

    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.ffill()
    # Fill NaN according to column dtype
    for col in df.columns:
        if is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        elif is_string_dtype(df[col]):
            df[col] = df[col].fillna('')
        elif is_bool_dtype(df[col]):
            df[col] = df[col].fillna(False)
        else:
            df[col] = df[col].fillna('')

    return df

# =========================================================
# 6. 시장 레짐 피처
# =========================================================
def fetch_kospi_index(start_date: str, end_date: str) -> pd.DataFrame:
    try:
        idx = fdr.DataReader('KS11', start_date, end_date).reset_index()
        idx = idx.rename(columns={
            'Date': 'Date', 'Open': 'Idx_Open', 'High': 'Idx_High',
            'Low': 'Idx_Low', 'Close': 'Idx_Close', 'Volume': 'Idx_Volume'
        })
        idx['Date'] = pd.to_datetime(idx['Date']).dt.normalize()
        return idx[['Date', 'Idx_Open', 'Idx_High', 'Idx_Low', 'Idx_Close', 'Idx_Volume']]
    except Exception as e:
        print(f"⚠️ KOSPI index 로드 실패: {e}")
        return pd.DataFrame(columns=['Date', 'Idx_Open', 'Idx_High', 'Idx_Low', 'Idx_Close', 'Idx_Volume'])

def build_market_regime(index_df: pd.DataFrame) -> pd.DataFrame:
    if index_df.empty:
        return pd.DataFrame(columns=['Date', 'Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio'])

    df = index_df.copy().sort_values('Date').reset_index(drop=True)
    df['Idx_MA20'] = df['Idx_Close'].rolling(20).mean()
    df['Idx_MA60'] = df['Idx_Close'].rolling(60).mean()
    df['Idx_Ret20'] = df['Idx_Close'].pct_change(20)
    df['Idx_ATR_Ratio'] = ta.atr(
        high=df['Idx_High'], low=df['Idx_Low'], close=df['Idx_Close'], length=14
    ) / (df['Idx_Close'] + 1e-9)

    df['Bull_Regime'] = (
        (df['Idx_Close'] > df['Idx_MA20']) &
        (df['Idx_MA20'] > df['Idx_MA60']) &
        (df['Idx_Ret20'] > 0)
    ).astype(int)

    df = df[['Date', 'Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio']].copy()
    # Fill NaN according to column dtype
    for col in df.columns:
        if is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        elif is_string_dtype(df[col]):
            df[col] = df[col].fillna('')
        elif is_bool_dtype(df[col]):
            df[col] = df[col].fillna(False)
        else:
            df[col] = df[col].fillna('')
    return df

# =========================================================
# 7. Path-based 라벨 생성
# =========================================================
def build_path_targets(df: pd.DataFrame, tp=0.045, sl=0.03, hold_days=3) -> pd.DataFrame:
    """
    오늘 신호 발생 -> 다음날 시가 진입.
    이후 hold_days 동안 TP/SL/TimeStop을 실제 경로 기준으로 판정.
    """
    if df.empty:
        return df.copy()

    out = df.copy().reset_index(drop=True)
    n = len(out)

    strict = np.full(n, np.nan)
    loose = np.full(n, np.nan)
    realized = np.full(n, np.nan)

    for i in range(n):
        entry_idx = i + 1
        if entry_idx >= n:
            continue

        buy_price = out.loc[entry_idx, 'Open']
        if pd.isna(buy_price) or buy_price <= 0:
            continue

        tp_price = buy_price * (1.0 + tp)
        sl_price = buy_price * (1.0 - sl)

        done = False
        ret = np.nan
        strict_hit = 0

        end_idx = min(entry_idx + hold_days - 1, n - 1)

        for j in range(entry_idx, end_idx + 1):
            op = out.loc[j, 'Open']
            hi = out.loc[j, 'High']
            lo = out.loc[j, 'Low']
            cl = out.loc[j, 'Close']

            # 갭 우선
            if op >= tp_price:
                ret = (op / buy_price) - 1.0
                strict_hit = 1
                done = True
                break
            if op <= sl_price:
                ret = (op / buy_price) - 1.0
                strict_hit = 0
                done = True
                break

            hit_tp = hi >= tp_price
            hit_sl = lo <= sl_price

            # 같은 날 둘 다 닿으면 보수적으로 SL 우선
            if hit_tp and hit_sl:
                ret = -sl
                strict_hit = 0
                done = True
                break
            elif hit_tp:
                ret = tp
                strict_hit = 1
                done = True
                break
            elif hit_sl:
                ret = -sl
                strict_hit = 0
                done = True
                break

            if j == end_idx:
                ret = (cl / buy_price) - 1.0
                strict_hit = 0
                done = True
                break

        if done:
            realized[i] = ret
            strict[i] = strict_hit
            # coverage 확보용 loose label
            # 실현수익 2.0% 이상이면 loose positive
            loose[i] = 1 if ret >= 0.02 else 0

    out['Realized_Ret_3D'] = realized
    out['Target_Strict'] = strict
    out['Target_Loose'] = loose

    return out

# =========================================================
# 8. 패널 빌더
# =========================================================
def build_panel(
    codes,
    start_date: str,
    end_date: str,
    warmup_days: int = 160,
    min_rows: int = 150,
    with_target: bool = True
) -> pd.DataFrame:
    print(f"[Panel] {len(codes)}개 종목 패널 생성 중...")
    frames = []

    ext_start = (pd.to_datetime(start_date) - pd.Timedelta(days=warmup_days)).strftime('%Y-%m-%d')
    idx = fetch_kospi_index(ext_start, end_date)
    regime_df = build_market_regime(idx)

    for i, code in enumerate(codes, 1):
        raw = fetch_raw_quotes_by_code(code, ext_start, end_date)
        if raw.empty or len(raw) < min_rows:
            continue

        feat = calculate_all_features(raw)

        if with_target:
            feat = build_path_targets(feat, tp=0.045, sl=0.03, hold_days=3)

        feat['Date'] = pd.to_datetime(feat['Date']).dt.normalize()
        feat['Code'] = zfill_code(feat['Code'])

        feat = feat.merge(regime_df, on='Date', how='left')
        feat[['Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio']] = feat[['Bull_Regime', 'Idx_Ret20', 'Idx_ATR_Ratio']].fillna(0)

        # 최종 기간만 잘라서 반환
        feat = feat[(feat['Date'] >= pd.to_datetime(start_date)) & (feat['Date'] <= pd.to_datetime(end_date))].copy()

        if with_target:
            feat = feat.dropna(subset=['Target_Loose', 'Target_Strict', 'Realized_Ret_3D'])

        if not feat.empty:
            frames.append(feat)

        if i % 50 == 0:
            print(f"  - 진행률: {i}/{len(codes)}")

    if not frames:
        return pd.DataFrame()

    panel = pd.concat(frames, axis=0).reset_index(drop=True)
    panel = panel.replace([np.inf, -np.inf], np.nan).fillna(0)
    return panel

# =========================================================
# 9. 시간 분할 / 가중치
# =========================================================
def split_dates_4way(panel: pd.DataFrame, train_ratio=0.65, valid_ratio=0.15, calib_ratio=0.10):
    dates = sorted(panel['Date'].dropna().unique())
    n = len(dates)
    if n < 40:
        raise ValueError("날짜 수가 너무 적어 4분할이 어렵습니다.")

    train_end = dates[int(n * train_ratio)]
    valid_end = dates[int(n * (train_ratio + valid_ratio))]
    calib_end = dates[int(n * (train_ratio + valid_ratio + calib_ratio))]

    train_df = panel[panel['Date'] <= train_end].copy()
    valid_df = panel[(panel['Date'] > train_end) & (panel['Date'] <= valid_end)].copy()
    calib_df = panel[(panel['Date'] > valid_end) & (panel['Date'] <= calib_end)].copy()
    test_df = panel[panel['Date'] > calib_end].copy()

    return train_df, valid_df, calib_df, test_df

def recency_weights(date_series: pd.Series, half_life_days: int = 90) -> np.ndarray:
    dt = pd.to_datetime(date_series)
    age_days = (dt.max() - dt).dt.days
    w = np.exp(-np.log(2) * age_days / half_life_days)
    return w

# =========================================================
# 10. Pack 저장/예측
# =========================================================
def build_model_pack(model, calibrator, features, target_col, name, extra=None):
    return {
        'name': name,
        'model': model,
        'calibrator': calibrator,
        'features': features,
        'target_col': target_col,
        'extra': extra or {}
    }

def predict_with_pack(pack: dict, df: pd.DataFrame) -> np.ndarray:
    X = df[pack['features']]
    raw_prob = pack['model'].predict_proba(X)[:, 1]
    if pack.get('calibrator') is not None:
        return pack['calibrator'].transform(raw_prob)
    return raw_prob

# =========================================================
# 11. 리포트
# =========================================================
def print_basic_report(name: str, y_true: pd.Series, prob: np.ndarray):
    ap = average_precision_score(y_true, prob)
    print(f"\n[{name}]")
    print(f"- AP(PR-AUC): {ap:.4f}")
    print(f"- Prob Min/Median/95%/Max: {prob.min():.4f} / {np.median(prob):.4f} / {np.quantile(prob, 0.95):.4f} / {prob.max():.4f}")

def daily_topk_precision(df: pd.DataFrame, score_col: str, target_col: str, k: int = 5):
    if df.empty:
        return 0.0, 0
    topk = df.sort_values(['Date', score_col], ascending=[True, False]).groupby('Date').head(k)
    if topk.empty:
        return 0.0, 0
    return topk[target_col].mean(), len(topk)

def print_topk_report(name: str, df: pd.DataFrame, score_col: str, target_col: str):
    for k in [1, 3, 5]:
        p, n = daily_topk_precision(df, score_col, target_col, k=k)
        print(f"- Daily Top{k} Precision: {p:.4f} (표본 {n})")

# =========================================================
# 12. 메타 피처 생성
# =========================================================
def build_meta_frame(panel: pd.DataFrame, hx_pack: dict, hl_pack: dict, bx_pack: dict, bl_pack: dict) -> pd.DataFrame:
    meta = panel.copy()

    meta['HX'] = predict_with_pack(hx_pack, meta)
    meta['HL'] = predict_with_pack(hl_pack, meta)
    meta['BX'] = predict_with_pack(bx_pack, meta)
    meta['BL'] = predict_with_pack(bl_pack, meta)

    meta['Mean_Prob'] = meta[['HX', 'HL', 'BX', 'BL']].mean(axis=1)
    meta['Std_Prob'] = meta[['HX', 'HL', 'BX', 'BL']].std(axis=1)
    meta['Max_Prob'] = meta[['HX', 'HL', 'BX', 'BL']].max(axis=1)
    meta['Min_Prob'] = meta[['HX', 'HL', 'BX', 'BL']].min(axis=1)
    meta['Bull_Mean'] = meta[['BX', 'BL']].mean(axis=1)
    meta['Hybrid_Mean'] = meta[['HX', 'HL']].mean(axis=1)
    meta['Bull_Hybrid_Gap'] = meta['Bull_Mean'] - meta['Hybrid_Mean']

    return meta

# =========================================================
# 13. 일별 추천 종목 선정
# =========================================================
def select_daily_topk(
    scored_df: pd.DataFrame,
    score_col: str = 'Meta_Score',
    top_k_bull: int = 5,
    top_k_bear: int = 2,
    floor_bull: float = 0.46,
    floor_bear: float = 0.52,
    fallback_bull_floor: float = 0.43
) -> pd.DataFrame:
    picks = []

    for dt, g in scored_df.groupby('Date'):
        g = g.sort_values(score_col, ascending=False).copy()
        bull = int(g['Bull_Regime'].iloc[0]) if 'Bull_Regime' in g.columns else 0

        top_k = top_k_bull if bull == 1 else top_k_bear
        floor = floor_bull if bull == 1 else floor_bear

        day_pick = g[g[score_col] >= floor].head(top_k)

        # 추천 0건 방지 장치: bull regime에서만 fallback 1종목 허용
        if day_pick.empty and bull == 1:
            fallback = g[g[score_col] >= fallback_bull_floor].head(1)
            day_pick = fallback

        picks.append(day_pick)

    if not picks:
        return pd.DataFrame()

    out = pd.concat(picks, axis=0).reset_index(drop=True)
    return out