import numpy as np
import pandas as pd
import pandas_ta as ta

pd.set_option('future.no_silent_downcasting', True)


def calculate_all_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()

    rename_map = {
        'quote_date': 'date',
        'stock_code': 'code',
        'stock_name': 'name',
        'open_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'close_price': 'close',
        'volume': 'volume',
        'foreign_net': 'foreign_net',
        'inst_net': 'inst_net',
        'margin_rate': 'margin_rate'
    }
    df = df.rename(columns=rename_map)

    req = ['date', 'code', 'open', 'high', 'low', 'close', 'volume']
    for col in req:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼 누락: {col}")

    df['date'] = pd.to_datetime(df['date']).dt.normalize()
    df['code'] = df['code'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.zfill(6)
    if 'name' not in df.columns:
        df['name'] = ''

    num_cols = ['open', 'high', 'low', 'close', 'volume', 'foreign_net', 'inst_net', 'margin_rate']
    for col in num_cols:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Flow류는 결측 시 0으로
    df['foreign_net'] = df['foreign_net'].fillna(0.0)
    df['inst_net'] = df['inst_net'].fillna(0.0)
    df['margin_rate'] = df['margin_rate'].fillna(0.0)

    # 기본 지표
    df['return_1d'] = df['close'].pct_change()
    df['return_5d'] = df['close'].pct_change(5)
    df['return_20d'] = df['close'].pct_change(20)

    df['ma5'] = ta.sma(df['close'], length=5)
    df['ma20'] = ta.sma(df['close'], length=20)
    df['ma60'] = ta.sma(df['close'], length=60)
    df['ma120'] = ta.sma(df['close'], length=120)
    df['ma20_slope_5'] = df['ma20'].pct_change(5)

    df['rsi'] = ta.rsi(df['close'], length=14)

    macd_df = ta.macd(df['close'])
    if macd_df is not None and not macd_df.empty:
        df['macd'] = macd_df.iloc[:, 0]
        df['macd_hist'] = macd_df.iloc[:, 1]
        df['macd_sig'] = macd_df.iloc[:, 2]
    else:
        df['macd'] = 0.0
        df['macd_hist'] = 0.0
        df['macd_sig'] = 0.0

    bb_df = ta.bbands(df['close'], length=20, std=2, ddof=1)
    if bb_df is not None and not bb_df.empty:
        df['bbl'] = bb_df.iloc[:, 0]
        df['bbm'] = bb_df.iloc[:, 1]
        df['bbu'] = bb_df.iloc[:, 2]
        df['bbb'] = bb_df.iloc[:, 3]
        df['bbp'] = bb_df.iloc[:, 4]
    else:
        for col in ['bbl', 'bbm', 'bbu', 'bbb', 'bbp']:
            df[col] = 0.0

    df['obv'] = ta.obv(close=df['close'], volume=df['volume'])
    df['obv_change_5'] = df['obv'].diff(5)

    df['atr'] = ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14)

    # 일봉용 rolling VWAP 20일
    typical = (df['high'] + df['low'] + df['close']) / 3.0
    df['vwap20'] = (typical * df['volume']).rolling(20).sum() / (df['volume'].rolling(20).sum() + 1e-9)

    # 파생
    df['vol_change'] = df['volume'].pct_change()
    df['vol_momentum'] = df['volume'] / (df['volume'].rolling(5).mean() + 1e-9)
    df['ma_ratio'] = df['close'] / (df['ma20'] + 1e-9)
    df['dist_ma5'] = df['close'] / (df['ma5'] + 1e-9)
    df['atr_ratio'] = df['atr'] / (df['close'] + 1e-9)
    df['rsi_slope'] = df['rsi'].diff()
    df['range_ratio'] = (df['high'] - df['low']) / (df['close'] + 1e-9)
    df['up_trend_2d'] = ((df['close'].diff(1) > 0) & (df['close'].shift(1).diff(1) > 0)).astype(int)

    df['close_vwap_ratio'] = df['close'] / (df['vwap20'] + 1e-9)

    # 수급 / 신용
    vol_safe = df['volume'] + 1e-9
    df['foreign_vol_ratio'] = df['foreign_net'] / vol_safe
    df['inst_vol_ratio'] = df['inst_net'] / vol_safe
    df['foreign_net_roll5'] = df['foreign_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
    df['inst_net_roll5'] = df['inst_net'].rolling(5).sum() / (df['volume'].rolling(5).sum() + 1e-9)
    df['dual_net_buy'] = ((df['foreign_net'] > 0) & (df['inst_net'] > 0)).astype(int)

    df['foreign_net_accel'] = df['foreign_net'].ewm(span=5, adjust=False).mean() - df['foreign_net'].ewm(span=20, adjust=False).mean()
    df['inst_net_accel'] = df['inst_net'].ewm(span=5, adjust=False).mean() - df['inst_net'].ewm(span=20, adjust=False).mean()

    df['margin_rate_change'] = df['margin_rate'].diff()
    df['margin_rate_roll5'] = df['margin_rate'].rolling(5).mean()

    # 캔들 / 돌파 / 거래대금
    prev_close = df['close'].shift(1)
    day_range = (df['high'] - df['low']).abs() + 1e-9

    df['gap_ratio'] = df['open'] / (prev_close + 1e-9) - 1.0
    df['body_ratio'] = (df['close'] - df['open']).abs() / day_range
    df['upper_wick_ratio'] = (df['high'] - np.maximum(df['open'], df['close'])) / day_range
    df['lower_wick_ratio'] = (np.minimum(df['open'], df['close']) - df['low']) / day_range

    df['turnover'] = df['close'] * df['volume']
    df['turnover_shock'] = df['turnover'] / (df['turnover'].rolling(20).median() + 1e-9)

    df['breakout_20'] = df['close'] / (df['high'].rolling(20).max().shift(1) + 1e-9)
    df['breakdown_20'] = df['close'] / (df['low'].rolling(20).min().shift(1) + 1e-9)

    # 정리
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.fillna(0.0)

    return df