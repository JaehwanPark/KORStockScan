import numpy as np
import pandas as pd
import FinanceDataReader as fdr
from sqlalchemy import text

from common_v2 import engine, sql_code_tuple, normalize_codes
from feature_engineering_v2 import calculate_all_features


RAW_COLS = """
    quote_date, stock_code, stock_name,
    open_price, high_price, low_price, close_price, volume,
    foreign_net, inst_net, margin_rate
"""


def fetch_raw_quotes(codes, start_date, end_date):
    codes = normalize_codes(codes)
    code_str = sql_code_tuple(codes)

    query = f"""
        SELECT {RAW_COLS}
        FROM daily_stock_quotes
        WHERE stock_code IN {code_str}
          AND quote_date >= '{start_date}'
          AND quote_date <= '{end_date}'
        ORDER BY stock_code ASC, quote_date ASC
    """
    with engine.connect() as conn:
        raw = pd.read_sql(text(query), conn)

    if raw.empty:
        return raw

    raw['quote_date'] = pd.to_datetime(raw['quote_date']).dt.normalize()
    raw['stock_code'] = raw['stock_code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)
    return raw


def build_path_targets(df, tp=0.045, sl=0.03, hold_days=3):
    """
    signal day = row i
    entry day  = row i+1 open
    path-based label:
      - 갭 TP / 갭 SL 우선
      - 같은 날 TP/SL 둘 다 닿으면 보수적으로 SL 우선
      - strict: 3일 내 +4.5% TP 먼저
      - loose : 최종 realized_ret_3d >= +2.0%
    """
    df = df.copy().reset_index(drop=True)

    strict = np.full(len(df), np.nan)
    loose = np.full(len(df), np.nan)
    realized_ret = np.full(len(df), np.nan)
    exit_reason = np.array([''] * len(df), dtype=object)

    for i in range(len(df) - hold_days - 1):
        entry_idx = i + 1
        buy_price = df.loc[entry_idx, 'open']

        if pd.isna(buy_price) or buy_price <= 0:
            continue

        tp_price = buy_price * (1.0 + tp)
        sl_price = buy_price * (1.0 - sl)

        final_ret = np.nan
        final_strict = 0
        reason = ""

        for j in range(entry_idx, min(entry_idx + hold_days, len(df))):
            op = df.loc[j, 'open']
            hi = df.loc[j, 'high']
            lo = df.loc[j, 'low']
            cl = df.loc[j, 'close']

            # 갭 처리
            if op >= tp_price:
                final_ret = (op / buy_price) - 1.0
                final_strict = 1
                reason = "TP_GAP"
                break
            if op <= sl_price:
                final_ret = (op / buy_price) - 1.0
                final_strict = 0
                reason = "SL_GAP"
                break

            hit_tp = hi >= tp_price
            hit_sl = lo <= sl_price

            # 같은 날 둘 다 닿으면 보수적 SL 우선
            if hit_tp and hit_sl:
                final_ret = -sl
                final_strict = 0
                reason = "AMBIG_SL_FIRST"
                break

            if hit_tp:
                final_ret = tp
                final_strict = 1
                reason = "TP"
                break

            if hit_sl:
                final_ret = -sl
                final_strict = 0
                reason = "SL"
                break

            if j == entry_idx + hold_days - 1:
                final_ret = (cl / buy_price) - 1.0
                final_strict = 0
                reason = "TIME"
                break

        if pd.notna(final_ret):
            strict[i] = final_strict
            loose[i] = 1 if final_ret >= 0.02 else 0
            realized_ret[i] = final_ret
            exit_reason[i] = reason

    df['target_strict'] = strict
    df['target_loose'] = loose
    df['realized_ret_3d'] = realized_ret
    df['exit_reason_3d'] = exit_reason

    return df


def fetch_kospi_index(start_date, end_date):
    try:
        idx = fdr.DataReader('KS11', start_date, end_date).reset_index()
        idx.columns = [str(c).lower() for c in idx.columns]
        idx = idx.rename(columns={'date': 'date'})
        idx['date'] = pd.to_datetime(idx['date']).dt.normalize()

        idx['idx_ma20'] = idx['close'].rolling(20).mean()
        idx['idx_ma60'] = idx['close'].rolling(60).mean()
        idx['idx_ret20'] = idx['close'].pct_change(20)

        tr1 = idx['high'] - idx['low']
        tr2 = (idx['high'] - idx['close'].shift(1)).abs()
        tr3 = (idx['low'] - idx['close'].shift(1)).abs()
        idx['true_range'] = np.maximum(tr1, np.maximum(tr2, tr3))
        idx['idx_atr_ratio'] = idx['true_range'].rolling(14).mean() / (idx['close'] + 1e-9)

        idx['bull_regime'] = (
            (idx['close'] > idx['idx_ma20']) &
            (idx['idx_ma20'] > idx['idx_ma60']) &
            (idx['idx_ret20'] > 0)
        ).astype(int)

        return idx[['date', 'bull_regime', 'idx_ret20', 'idx_atr_ratio']].copy()

    except Exception as e:
        # 이 프린트문을 추가하여 실제 에러 원인을 터미널에 출력합니다.
        print(f"⚠️ [오류] FinanceDataReader 지수 추출 실패: {e}")
        
        # fallback: 전부 0
        date_range = pd.date_range(start=start_date, end=end_date, freq='B')
        idx = pd.DataFrame({'date': date_range})
        idx['bull_regime'] = 0
        idx['idx_ret20'] = 0.0
        idx['idx_atr_ratio'] = 0.0
        return idx


def add_market_features(panel, start_date, end_date):
    idx = fetch_kospi_index(start_date, end_date)
    panel = panel.merge(idx, on='date', how='left')
    panel['bull_regime'] = panel['bull_regime'].fillna(0).astype(int)
    panel['idx_ret20'] = panel['idx_ret20'].fillna(0.0)
    panel['idx_atr_ratio'] = panel['idx_atr_ratio'].fillna(0.0)
    panel['rs_20_vs_index'] = panel['return_20d'].fillna(0.0) - panel['idx_ret20']
    return panel


def build_panel_dataset(codes, start_date, end_date, min_rows=150, include_labels=True):
    raw = fetch_raw_quotes(codes, start_date, end_date)
    if raw.empty:
        return pd.DataFrame()

    frames = []
    for code, g in raw.groupby('stock_code', sort=False):
        g = g.sort_values('quote_date').reset_index(drop=True)
        if len(g) < min_rows:
            continue

        feat = calculate_all_features(g)

        if include_labels:
            feat = build_path_targets(feat, tp=0.045, sl=0.03, hold_days=3)
            feat = feat.dropna(subset=['target_strict', 'target_loose', 'realized_ret_3d'])

        frames.append(feat)

    if not frames:
        return pd.DataFrame()

    panel = pd.concat(frames, axis=0).reset_index(drop=True)
    panel = add_market_features(panel, start_date, end_date)

    # 안전장치
    panel = panel.replace([np.inf, -np.inf], np.nan)
    panel = panel.fillna(0.0)

    return panel