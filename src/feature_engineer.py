import pandas as pd
import numpy as np
import pandas_ta as ta


def calculate_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    OHLCV 데이터프레임을 입력받아 KORStockScan의 모든 기술적 지표와
    AI 모델용 파생 피처(수급/신용 포함)를 계산하여 반환합니다.
    """
    df = df.copy()

    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"입력 데이터에 필수 컬럼 '{col}'이 없습니다.")

    # ----------------------------------------------------
    # 1. 기본 기술적 지표
    # ----------------------------------------------------
    df['Return'] = df['Close'].pct_change()
    df['MA5'] = ta.sma(df['Close'], length=5)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA60'] = ta.sma(df['Close'], length=60)
    df['MA120'] = ta.sma(df['Close'], length=120)

    df['RSI'] = ta.rsi(df['Close'], length=14)

    macd_df = ta.macd(df['Close'])
    if macd_df is not None and not macd_df.empty:
        df['MACD'] = macd_df.iloc[:, 0]
        df['MACD_Hist'] = macd_df.iloc[:, 1]
        df['MACD_Sig'] = macd_df.iloc[:, 2]
    else:
        df['MACD'] = df['MACD_Hist'] = df['MACD_Sig'] = 0

    bb_df = ta.bbands(df['Close'], length=20, std=2, ddof=1)
    if bb_df is not None and not bb_df.empty:
        df['BBL'] = bb_df.iloc[:, 0]
        df['BBM'] = bb_df.iloc[:, 1]
        df['BBU'] = bb_df.iloc[:, 2]
        df['BBB'] = bb_df.iloc[:, 3]
        df['BBP'] = bb_df.iloc[:, 4]
    else:
        for col in ['BBL', 'BBM', 'BBU', 'BBB', 'BBP']:
            df[col] = 0

    df['OBV'] = ta.obv(close=df['Close'], volume=df['Volume'])
    df['ATR'] = ta.atr(high=df['High'], low=df['Low'], close=df['Close'], length=14)

    v = df['Volume']
    p = (df['High'] + df['Low'] + df['Close']) / 3
    vwap_calc = None

    if isinstance(df.index, pd.DatetimeIndex):
        vwap_calc = ta.vwap(high=df['High'], low=df['Low'], close=df['Close'], volume=df['Volume'])
    elif 'Date' in df.columns:
        temp_idx = pd.to_datetime(df['Date'])
        vwap_calc = ta.vwap(
            high=df['High'].set_axis(temp_idx),
            low=df['Low'].set_axis(temp_idx),
            close=df['Close'].set_axis(temp_idx),
            volume=df['Volume'].set_axis(temp_idx)
        )
        if vwap_calc is not None:
            vwap_calc = vwap_calc.values

    if vwap_calc is None:
        df['VWAP'] = (p * v).cumsum() / v.cumsum()
    else:
        df['VWAP'] = vwap_calc

    df['VWAP'] = pd.to_numeric(df['VWAP'], errors='coerce')

    # ----------------------------------------------------
    # 2. 기존 AI 앙상블 모델용 차트 파생 피처
    # ----------------------------------------------------
    df['Vol_Change'] = df['Volume'].pct_change()
    df['MA_Ratio'] = df['Close'] / (df['MA20'] + 1e-9)
    df['BB_Pos'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

    # ----------------------------------------------------
    # 3. [신규] 수급 및 신용잔고 파생 피처 (AI 재학습용 핵심 데이터)
    # ----------------------------------------------------
    # 데이터베이스에 수급 컬럼이 존재할 경우에만 계산 (하위 호환성 방어)
    if 'Foreign_Net' in df.columns and 'Inst_Net' in df.columns:
        vol_safe = df['Volume'] + 1e-9

        # 1) 당일 수급 비중 (0~1 사이의 비율로 스케일링)
        df['Foreign_Vol_Ratio'] = df['Foreign_Net'] / vol_safe
        df['Inst_Vol_Ratio'] = df['Inst_Net'] / vol_safe

        # 2) 최근 5일 누적 수급 비중 (외국인/기관이 꾸준히 매집 중인가?)
        df['Foreign_Net_Roll5'] = df['Foreign_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Inst_Net_Roll5'] = df['Inst_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)

        # 3) 쌍끌이 매수 (강력한 상승 시그널)
        df['Dual_Net_Buy'] = ((df['Foreign_Net'] > 0) & (df['Inst_Net'] > 0)).astype(int)
    else:
        for col in ['Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Foreign_Net_Roll5', 'Inst_Net_Roll5', 'Dual_Net_Buy']:
            df[col] = 0

    if 'Margin_Rate' in df.columns:
        # 4) 신용잔고율 증감 (빚투 개미들이 털려나가는지 확인)
        df['Margin_Rate_Change'] = df['Margin_Rate'].diff()

        # 5) 신용잔고율 5일 평균 (종목의 전반적인 신용 부담감)
        df['Margin_Rate_Roll5'] = df['Margin_Rate'].rolling(5).mean()
    else:
        df['Margin_Rate_Change'] = 0
        df['Margin_Rate_Roll5'] = 0

    # ----------------------------------------------------
    # 4. 결측치(NaN) 처리 및 반환
    # ----------------------------------------------------
    df = df.replace([np.inf, -np.inf], np.nan)
    df.bfill(inplace=True)
    df.fillna(0, inplace=True)

    return df


if __name__ == "__main__":
    from db_manager import DBManager

    print("Feature Engineer (수급/신용 통합) 테스트 중...")

    db = DBManager()
    # 삼성전자 데이터 꺼내오기 (DB에 새로 쌓인 수급 데이터 확인)
    test_df = db.get_stock_data('005930', limit=100)

    if not test_df.empty:
        processed_df = calculate_all_features(test_df)
        print("✅ 계산 완료! 신규 수급/신용 피처 샘플:")
        print(
            processed_df[['Date', 'Dual_Net_Buy', 'Foreign_Vol_Ratio', 'Inst_Net_Roll5', 'Margin_Rate_Change']].tail(5))
    else:
        print("❌ DB에서 데이터를 가져오지 못했습니다.")