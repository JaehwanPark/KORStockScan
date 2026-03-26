"""
[KORStockScan Feature Engineering Module]

이 모듈은 AI 모델 학습 및 실시간 추론에 필요한 모든 파생 변수(Feature)를 계산하는 
순수 데이터 전처리(Data Preprocessing) 도구입니다.

💡 아키텍처 관점에서의 독립(Decoupling) 사유:
1. MLOps '학습-추론 불일치(Training-Serving Skew)' 원천 차단:
   과거 데이터를 DB에 적재할 때(학습용)와 장중 실시간으로 타점을 계산할 때(추론용),
   100% 동일한 수학 공식을 사용하도록 보장하는 단일 진실 공급원(SSOT) 역할을 수행합니다.
2. 무거운 의존성 격리(Isolation):
   pandas_ta와 같은 무거운 통계/수학 연산 라이브러리를 이 모듈 내부에만 가두어, 
   단순 통신/스캔 모듈들이 불필요하게 무거운 라이브러리를 메모리에 올리지 않도록 방어합니다.
3. 전처리 확장성(Scalability):
   향후 1분봉 데이터 피처, 호가창(Orderbook) 피처 등 시스템이 고도화될 때 
   모든 데이터 가공 로직이 모이는 중앙 베이스캠프 역할을 합니다.
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from pandas.api.types import is_string_dtype, is_bool_dtype, is_numeric_dtype
# 🚀 판다스 경고 숨김 및 미래 규칙 적용 선언 (import 바로 아래에 추가)
pd.set_option('future.no_silent_downcasting', True)

def calculate_all_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    OHLCV(고가/저가/종가/거래량) 및 수급/신용 데이터를 입력받아
    KORStockScan의 AI 앙상블 모델(XGB/LGBM)에 주입할 파생 피처를 일괄 계산하는 순수 함수(Pure Function)입니다.
    """
    df = df.copy()

    # 💡 [아키텍트의 무적 방어막] DB에서 온 소문자 스네이크 케이스를 AI 표준(대문자)으로 강제 통일
    COLUMN_NORMALIZER = {
        'quote_date': 'Date', 'stock_code': 'Code', 'stock_name': 'Name',
        'open_price': 'Open', 'high_price': 'High', 'low_price': 'Low', 
        'close_price': 'Close', 'volume': 'Volume',
        'foreign_net': 'Foreign_Net', 'inst_net': 'Inst_Net', 'margin_rate': 'Margin_Rate'
    }
    df = df.rename(columns=COLUMN_NORMALIZER)

    # Ensure chronological order for time‑series calculations
    if 'Date' in df.columns:
        # Convert to datetime if not already
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)
    elif isinstance(df.index, pd.DatetimeIndex):
        df = df.sort_index()

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
    
    # 💡 [신규 추가] 모델이 요구하는 ATR_Ratio 피처 계산
    df['ATR_Ratio'] = df['ATR'] / (df['Close'] + 1e-9)
    
    df['RSI_Slope'] = df['RSI'].diff()
    df['Range_Ratio'] = (df['High'] - df['Low']) / (df['Close'] + 1e-9)
    df['Vol_Momentum'] = df['Volume'] / (df['Volume'].rolling(5).mean() + 1e-9)
    df['Dist_MA5'] = df['Close'] / (df['MA5'] + 1e-9)
    df['Up_Trend_2D'] = ((df['Close'].diff(1) > 0) & (df['Close'].shift(1).diff(1) > 0)).astype(int)

    # ----------------------------------------------------
    # 3. [신규] 수급 및 신용잔고 파생 피처 (AI 재학습용 핵심 데이터)
    # ----------------------------------------------------
    if 'Foreign_Net' in df.columns and 'Inst_Net' in df.columns:
        vol_safe = df['Volume'] + 1e-9

        # 1) 당일 수급 비중
        df['Foreign_Vol_Ratio'] = df['Foreign_Net'] / vol_safe
        df['Inst_Vol_Ratio'] = df['Inst_Net'] / vol_safe

        # 2) 최근 5일 누적 수급 비중
        df['Foreign_Net_Roll5'] = df['Foreign_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)
        df['Inst_Net_Roll5'] = df['Inst_Net'].rolling(5).sum() / (df['Volume'].rolling(5).sum() + 1e-9)

        # 3) 쌍끌이 매수
        df['Dual_Net_Buy'] = ((df['Foreign_Net'] > 0) & (df['Inst_Net'] > 0)).astype(int)
        
        # 4) 스마트 머니 가속도 지표 (MACD 방식)
        df['Foreign_Net_Accel'] = df['Foreign_Net'].ewm(span=5, adjust=False).mean() - df['Foreign_Net'].ewm(span=20, adjust=False).mean()
        df['Inst_Net_Accel'] = df['Inst_Net'].ewm(span=5, adjust=False).mean() - df['Inst_Net'].ewm(span=20, adjust=False).mean()
    else:
        # 🚨 [핵심 교정] 데이터 누락 시 Accel 지표도 반드시 0으로 생성해야 에러가 안 납니다!
        missing_cols = ['Foreign_Vol_Ratio', 'Inst_Vol_Ratio', 'Foreign_Net_Roll5', 'Inst_Net_Roll5', 'Dual_Net_Buy', 'Foreign_Net_Accel', 'Inst_Net_Accel']
        for col in missing_cols:
            df[col] = 0

    if 'Margin_Rate' in df.columns:
        # 4) 신용잔고율 증감
        df['Margin_Rate_Change'] = df['Margin_Rate'].diff()
        # 5) 신용잔고율 5일 평균
        df['Margin_Rate_Roll5'] = df['Margin_Rate'].rolling(5).mean()
    else:
        df['Margin_Rate_Change'] = 0
        df['Margin_Rate_Roll5'] = 0

    # ----------------------------------------------------
    # 4. 결측치(NaN) 처리 및 반환
    # ----------------------------------------------------
    df = df.replace([np.inf, -np.inf], np.nan)
    
    # 🚨 [핵심 교정] 미래 데이터 참조(Data Leakage)를 유발하는 bfill 삭제
    # df.bfill(inplace=True) <-- 절대 금지!
    
    # 과거 데이터로 빈칸을 채우거나(ffill), 아예 0으로 채워 무로부터 시작하게 만듭니다.
    df.ffill(inplace=True)

    # Fill remaining NaN according to column dtype
    for col in df.columns:
        if is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        elif is_string_dtype(df[col]):
            df[col] = df[col].fillna('')
        elif is_bool_dtype(df[col]):
            df[col] = df[col].fillna(False)
        else:
            # fallback: fill with empty string
            df[col] = df[col].fillna('')

    return df