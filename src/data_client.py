import pandas as pd
import FinanceDataReader as fdr
import logging
from datetime import datetime
import time

# 기존 키움 API 유틸리티
import kiwoom_utils

# DB 매니저 연동 (종목 리스트 우회용)
from db_manager import DBManager


class DataClient:
    """
    KORStockScan 데이터 수집 전담 클래스 (수집 창구 단일화)
    메인 로직이 데이터 출처를 신경 쓰지 않고 항상 동일한 DataFrame을 받을 수 있도록 캡슐화합니다.
    """

    def __init__(self, kiwoom_token=None):
        self.kiwoom_token = kiwoom_token
        self.db = DBManager()  # 로컬 DB 접근을 위한 매니저 초기화

    def get_kospi_symbols(self) -> pd.DataFrame:
        """코스피 종목 리스트를 가져옵니다. (FDR 실패 시 로컬 DB 우회)"""
        # 1차 시도: FinanceDataReader
        try:
            df = fdr.StockListing('KOSPI')
            if 'Marcap' not in df.columns:
                df['Marcap'] = 0
            return df[['Code', 'Name', 'Marcap']]
        except Exception as e:
            logging.warning(f"FDR KOSPI 종목 리스트 수집 실패. 로컬 DB 우회 시도... (사유: {e})")

        # 2차 시도: 로컬 DB (방어 로직)
        try:
            # 💡 [핵심 수정] 단순 조회가 아니라, 종목별로 0이 아닌 가장 최근의 시가총액을 복구해서 가져옵니다.
            query = "SELECT Code, Name, MAX(Marcap) as Marcap FROM daily_stock_quotes GROUP BY Code, Name"
            with self.db._get_connection() as conn:
                df_db = pd.read_sql(query, conn)

            if not df_db.empty:
                logging.info(f"로컬 DB에서 {len(df_db)}개의 종목 정보를 성공적으로 복원했습니다.")
                return df_db[['Code', 'Name', 'Marcap']]
        except Exception as db_e:
            logging.error(f"로컬 DB KOSPI 종목 리스트 수집 마저 실패: {db_e}")

        return pd.DataFrame()

    def get_ohlcv(self, code: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        특정 종목의 일봉 데이터를 수집합니다.
        [1순위] FDR 시도 -> [2순위] Kiwoom API 우회
        """
        df = pd.DataFrame()

        # --------------------------------------------------------
        # 1차 시도: FinanceDataReader
        # --------------------------------------------------------
        try:
            if end_date:
                df = fdr.DataReader(code, start_date, end_date)
            else:
                df = fdr.DataReader(code, start_date)

            if not df.empty:
                df = df.reset_index()
                return df

        except Exception as e:
            logging.warning(f"[{code}] FDR 수집 실패. 키움 API 우회 시도... (사유: {e})")

        # --------------------------------------------------------
        # 2차 시도: Kiwoom REST API (kiwoom_utils.get_daily_data_ka10005_df 사용)
        # --------------------------------------------------------
        if self.kiwoom_token:
            try:
                # 💡 실전투자 API 기반의 일봉 수집 함수 호출
                df_kiwoom = kiwoom_utils.get_daily_data_ka10005_df(self.kiwoom_token, code)

                if df_kiwoom is not None and not df_kiwoom.empty:
                    # kiwoom_utils의 반환값은 인덱스가 Date이므로 이를 컬럼으로 빼줌
                    df_kiwoom = df_kiwoom.reset_index()

                    # 키움 API는 한번에 데이터를 많이 주므로, 요청받은 start_date와 end_date 기간만큼 필터링
                    mask = df_kiwoom['Date'] >= pd.to_datetime(start_date)
                    if end_date:
                        mask &= df_kiwoom['Date'] <= pd.to_datetime(end_date)

                    return df_kiwoom.loc[mask]

            except Exception as e:
                logging.error(f"[{code}] 키움 API 수집 마저 실패: {e}")
        else:
            logging.debug(f"[{code}] 키움 토큰이 없어 우회를 진행하지 못했습니다.")

        return pd.DataFrame()  # 두 방식 모두 실패 시 빈 데이터프레임 반환

    def get_full_daily_data(self, code: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        OHLCV 데이터에 키움 API의 수급 및 신용잔고율 데이터를 Left Join 하여 반환합니다.
        """
        # 1. 일봉 가져오기 (기존 우회 로직 활용)
        df = self.get_ohlcv(code, start_date, end_date)
        if df.empty:
            return df

        if 'Date' in df.columns:
            # 💡 [핵심 방어] 타임존(tz) 정보가 붙어있을 경우 강제로 떼어버려서 병합 에러 차단
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
            df.set_index('Date', inplace=True)

        # 2. 수급 및 신용 데이터 가져오기
        if self.kiwoom_token:
            today_str = datetime.now().strftime("%Y%m%d")
            df_investor = kiwoom_utils.get_investor_daily_ka10059_df(self.kiwoom_token, code, today_str)
            time.sleep(0.3)  # 💡 [추가] 수급 요청과 신용 요청 사이에 0.3초 대기
            df_margin = kiwoom_utils.get_margin_daily_ka10013_df(self.kiwoom_token, code, today_str)

            # 날짜를 기준으로 병합 (과거 100일 치)
            if not df_investor.empty:
                df_investor.index = pd.to_datetime(df_investor.index).tz_localize(None)
                df = df.join(df_investor, how='left')
            if not df_margin.empty:
                df_margin.index = pd.to_datetime(df_margin.index).tz_localize(None)
                df = df.join(df_margin, how='left')

        # 3. 결측치 안전 처리 (100일 이전 과거 데이터는 API가 안 주므로 0으로 처리)
        for col in ['Retail_Net', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']:
            if col not in df.columns:
                df[col] = 0
            else:
                df[col] = df[col].fillna(0)

        # 💡 [디버깅] 삼성전자(005930)일 때 조인 결과를 화면에 직접 출력해 봅니다.
        if code == '005930':
            print("\n👀 [디버그] 삼성전자(005930) 수급/신용 데이터 병합 결과:")
            print(df[['Close', 'Foreign_Net', 'Inst_Net', 'Margin_Rate']].tail(3))
            print("-" * 50)

        return df.reset_index()