import sqlite3
import pandas as pd
import os
from datetime import datetime  # 💡 [추가] 시간 기록을 위해 필요합니다!

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
    # 3. 텔레그램 유저 관리 (users.db 전용)
    # --------------------------------------------------------
    def init_user_db(self):
        """사용자 관리 DB를 초기화하고 테이블을 생성합니다."""
        with sqlite3.connect(USER_DB_PATH) as conn:
            # auth_group 컬럼을 기본적으로 포함하도록 안전하게 구성합니다.
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    user_level INTEGER DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    auth_group TEXT DEFAULT 'U'
                )
            ''')
            conn.commit()

    def get_telegram_chat_ids(self) -> list:
        """텔레그램 알림을 수신할 유저들의 chat_id 목록을 반환합니다."""
        with sqlite3.connect(USER_DB_PATH) as conn:
            rows = conn.execute("SELECT chat_id FROM users WHERE chat_id IS NOT NULL").fetchall()
            return [row[0] for row in rows]

    def check_special_auth(self, chat_id: str) -> bool:
        """DB에서 권한 그룹을 조회하여 특수 권한(A: 어드민, V: VIP) 여부를 반환합니다."""
        try:
            with sqlite3.connect(USER_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT auth_group FROM users WHERE chat_id = ?", (str(chat_id),))
                result = cursor.fetchone()
                return bool(result and result[0] in ['A', 'V'])
        except Exception as e:
            print(f"⚠️ 권한 체크 중 DB 에러 발생: {e}")
            return False

    def get_user_level(self, chat_id: int) -> int:
        """사용자의 등급 레벨을 반환합니다."""
        try:
            with sqlite3.connect(USER_DB_PATH) as conn:
                row = conn.execute("SELECT auth_group FROM users WHERE chat_id = ?", (chat_id,)).fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def add_new_user(self, chat_id: int):
        """신규 사용자를 등록합니다."""
        with sqlite3.connect(USER_DB_PATH) as conn:
            conn.execute('INSERT OR IGNORE INTO users (chat_id) VALUES (?)', (chat_id,))
            conn.commit()

    def upgrade_user_level(self, chat_id: int, level: int = 1):
        """사용자의 등급을 업데이트합니다."""
        with sqlite3.connect(USER_DB_PATH) as conn:
            conn.execute("UPDATE users SET user_level = ? WHERE chat_id = ?", (level, chat_id))
            conn.commit()
    # --------------------------------------------------------
    # 4. 매매 일지 기록 (매도 완료 시)
    # --------------------------------------------------------
    def update_sell_record(self, code: str, sell_price: int, profit_rate: float, status: str = 'COMPLETED'):
        """매도(익절/손절) 발생 시 매도가, 시간, 수익률을 DB에 영구 기록합니다."""
        today = datetime.now().strftime('%Y-%m-%d')
        sell_time = datetime.now().strftime('%H:%M:%S')

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 💡 [핵심 방어막] 기존 DB 테이블에 매도 관련 컬럼이 없다면 '자동으로' 생성합니다! (에러 완벽 차단)
            cursor.execute("PRAGMA table_info(recommendation_history)")
            columns = [info[1] for info in cursor.fetchall()]

            if 'sell_price' not in columns:
                cursor.execute("ALTER TABLE recommendation_history ADD COLUMN sell_price INTEGER DEFAULT 0")
                cursor.execute("ALTER TABLE recommendation_history ADD COLUMN sell_time TEXT")
                cursor.execute("ALTER TABLE recommendation_history ADD COLUMN profit_rate REAL DEFAULT 0.0")
                conn.commit()

            # 🎯 매도가, 매도시간, 수익률, 그리고 상태(COMPLETED or WATCHING) 업데이트
            query = """
                    UPDATE recommendation_history
                    SET status      = ?, \
                        sell_price  = ?, \
                        sell_time   = ?, \
                        profit_rate = ?
                    WHERE code = ? AND date = ? \
                    """
            cursor.execute(query, (status, sell_price, sell_time, profit_rate, code, today))
            conn.commit()