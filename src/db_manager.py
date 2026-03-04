import sqlite3
import pandas as pd
import os

# ==========================================
# DB 경로 설정 (상대 참조)
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'data'))
STOCK_DB_PATH = os.path.join(DATA_DIR, 'kospi_stock_data.db')
USER_DB_PATH = os.path.join(DATA_DIR, 'users.db')


class DBManager:
    """
    KORStockScan 시스템의 모든 데이터베이스 접근을 전담하는 클래스
    """

    def __init__(self, db_path=STOCK_DB_PATH):
        self.db_path = db_path

    def _get_connection(self):
        """DB 커넥션을 반환합니다. (with문과 함께 사용 권장)"""
        return sqlite3.connect(self.db_path)

    # --------------------------------------------------------
    # 1. 데이터 조회 (Read)
    # --------------------------------------------------------
    def get_stock_data(self, code: str, limit: int = 60) -> pd.DataFrame:
        """특정 종목의 최근 주가 데이터를 불러와 날짜 오름차순으로 정렬해 반환합니다."""
        query = f"SELECT * FROM daily_stock_quotes WHERE Code='{code}' ORDER BY Date DESC LIMIT {limit}"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)

        if not df.empty:
            df = df.sort_values('Date').reset_index(drop=True)
        return df

    def get_last_date(self, table_name: str, date_col: str = 'Date', code_col: str = None, code: str = None) -> str:
        """특정 테이블(또는 특정 종목)의 마지막 저장 날짜를 조회합니다."""
        query = f"SELECT MAX({date_col}) FROM {table_name}"
        if code_col and code:
            query += f" WHERE {code_col} = '{code}'"

        try:
            with self._get_connection() as conn:
                df = pd.read_sql(query, conn)
                return df.iloc[0, 0]
        except Exception:
            return None

    def get_latest_history_date(self) -> str:
        """가장 최근 AI 스캐너 추천 기록의 날짜를 반환합니다."""
        query = "SELECT MAX(date) as last_date FROM recommendation_history"
        with self._get_connection() as conn:
            df = pd.read_sql(query, conn)
        return df.iloc[0]['last_date'] if not df.empty else None

    def get_history_by_date(self, date: str) -> pd.DataFrame:
        """특정 일자의 추천 종목 기록을 가져옵니다."""
        query = f"SELECT * FROM recommendation_history WHERE date = '{date}'"
        with self._get_connection() as conn:
            return pd.read_sql(query, conn)

    # --------------------------------------------------------
    # 2. 데이터 저장 (Write)
    # --------------------------------------------------------
    def save_recommendation(self, date: str, code: str, name: str, price: int, pick_type: str, position: str,
                            prob: float = 0.7):
        """AI가 발굴한 종목을 히스토리 테이블에 저장(또는 업데이트)합니다. (진짜 확신도 반영)"""

        # 💡 [핵심] INSERT와 UPDATE 쿼리 양쪽 모두에 prob 컬럼을 추가했습니다.
        query = """
                INSERT INTO recommendation_history (date, code, name, buy_price, type, status, position_tag, prob)
                VALUES (?, ?, ?, ?, ?, 'WATCHING', ?, ?) ON CONFLICT(date, code) DO \
                UPDATE SET
                    buy_price=excluded.buy_price, \
                    type =excluded.type, \
                    position_tag=excluded.position_tag, \
                    prob=excluded.prob
                """
        with self._get_connection() as conn:
            # 전달받은 파라미터 튜플의 맨 마지막에 prob를 넣어줍니다.
            conn.execute(query, (date, code, name, price, pick_type, position, prob))
            conn.commit()

    def execute_query(self, query: str, params: tuple = ()):
        """단순 쿼리(INSERT, UPDATE, DELETE 등)를 직접 실행합니다."""
        with self._get_connection() as conn:
            conn.execute(query, params)
            conn.commit()

    # --------------------------------------------------------
    # 3. 텔레그램 유저 조회 (users.db 전용)
    # --------------------------------------------------------
    def get_telegram_chat_ids(self) -> list:
        """텔레그램 알림을 수신할 유저들의 chat_id 목록을 반환합니다."""
        with sqlite3.connect(USER_DB_PATH) as conn:
            rows = conn.execute("SELECT chat_id FROM users WHERE chat_id IS NOT NULL").fetchall()
            return [row[0] for row in rows]