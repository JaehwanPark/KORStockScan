import sqlite3
import pandas as pd
from datetime import datetime
import json
import os

def get_db_path(config_path='config_prod.json'):
    """설정 파일에서 DB 경로를 안전하게 가져옵니다."""
    if not os.path.exists(config_path):
        config_path = 'config_prod.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f).get('DB_PATH', 'kospi_stock_data.db')
    except:
        return 'kospi_stock_data.db'

DB_PATH = get_db_path()

def init_tables():
    """DB 테이블이 없다면 생성하고, 필요한 컬럼을 마이그레이션합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 추천 이력 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendation_history (
                date TEXT,
                code TEXT,
                name TEXT,
                buy_price INTEGER,
                type TEXT,
                status TEXT,
                nxt REAL,
                position_tag TEXT DEFAULT 'MIDDLE',
                PRIMARY KEY (date, code)
            )
        ''')
        
        # 텔레그램 유저 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                user_level INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"🔥 DB 초기화 오류: {e}")

def get_active_targets():
    """[스나이퍼 엔진용] 오늘 감시할 종목 + 전일 홀딩 종목을 불러옵니다."""
    targets = []
    try:
        conn = sqlite3.connect(DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')
        query = "SELECT * FROM recommendation_history WHERE date=? OR status='HOLDING'"
        df = pd.read_sql(query, conn, params=(today,))
        conn.close()

        if df.empty: return targets

        # Pandas로 중복 제거 (HOLDING 우선)
        df = df.sort_values(by='status').drop_duplicates(subset=['code'], keep='first')
        targets = df.to_dict('records')
        
        for t in targets:
            t['prob'] = t.get('prob', 0.75)
            t['buy_qty'] = t.get('buy_qty', 0)
        return targets
    except Exception as e:
        print(f"🔥 DB 감시 대상 로드 오류: {e}")
        return targets

def update_stock_status(code, status, buy_price=0, buy_qty=0, buy_time=''):
    """[스나이퍼 엔진용] 종목의 현재 상태(WATCHING, PENDING, HOLDING, COMPLETED)를 갱신합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        today = datetime.now().strftime('%Y-%m-%d')
        
        sql = """
            UPDATE recommendation_history 
            SET status = ?, buy_price = ?, nxt = ? 
            WHERE code = ? AND (date = ? OR status IN ('PENDING', 'HOLDING'))
        """
        # 임시로 nxt 컬럼에 buy_qty를 넣거나, 
        # 향후 스키마를 업데이트하여 buy_qty, buy_time 컬럼을 명시적으로 관리하는 것이 좋습니다.
        conn.execute(sql, (status, buy_price, buy_qty, str(code).zfill(6), today))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"🔥 DB 상태 업데이트 오류: {e}")

def register_manual_stock(code, name):
    """[관제탑용] 수동 감시 종목을 DB에 밀어 넣습니다."""
    today = datetime.now().strftime('%Y-%m-%d')
    try:
        conn = sqlite3.connect(DB_PATH)
        sql = """
            INSERT INTO recommendation_history (date, code, name, buy_price, type, status, position_tag)
            VALUES (?, ?, ?, 0, 'MANUAL', 'WATCHING', 'MIDDLE')
            ON CONFLICT(date, code) DO UPDATE SET
                status = 'WATCHING', type = 'MANUAL'
        """
        conn.execute(sql, (today, str(code).zfill(6), name))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"🔥 수동 타겟 DB 등록 오류: {e}")
        return False
    
def add_telegram_user(chat_id):
    """[텔레그램 봇용] 신규 사용자를 DB에 등록합니다."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"🔥 유저 등록 에러: {e}")