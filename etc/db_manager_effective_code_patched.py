# src/database/db_manager.py
import pandas as pd
import src.utils.constants as const
from datetime import datetime
from datetime import timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.utils.constants import POSTGRES_URL 
from sqlalchemy import func
from sqlalchemy import text
from contextlib import contextmanager
from src.utils.constants import TRADING_RULES

# 💡 MacroAlert 등 새로 추가된 모델들도 모두 임포트합니다.
from src.database.models import Base, User, RecommendationHistory, DailyStockQuote, MacroAlert
from src.utils.logger import log_error

class DBManager:
    """
    KORStockScan 시스템의 데이터베이스 접근 및 세션 관리를 전담하는 ORM 매니저
    """
    def __init__(self, db_url=POSTGRES_URL):
        self.engine = create_engine(
            db_url,
            pool_size=20,          
            max_overflow=10,       
            pool_timeout=30,       
            pool_pre_ping=True     
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def init_db(self):
        """프로그램 기동 시 테이블이 없으면 생성합니다."""
        Base.metadata.create_all(bind=self.engine)
        
        # 💡 [자동 마이그레이션] users 테이블에 신규 컬럼이 없으면 자동 추가 (PostgreSQL)
        try:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_analyze_count INTEGER DEFAULT 0;"))
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_analyze_date DATE;"))
                conn.execute(text("ALTER TABLE daily_stock_quotes ADD COLUMN IF NOT EXISTS is_nxt BOOLEAN;"))
        except Exception as e:
            print(f"⚠️ 컬럼 추가 확인 중 에러 (최초 생성 시 무시 가능): {e}")
            
        print("✅ 데이터베이스 초기화 및 테이블 검증 완료")
    
    @contextmanager
    def get_session(self):
        """DB 세션을 안전하게 열고 닫는 제너레이터 (에러 발생 시 롤백 보장)"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error(f"DB Transaction Error: {str(e)}")
            print(f"⚠️ DB Transaction Error: {e}")
            raise
        finally:
            session.close()

    # --------------------------------------------------------
    # 1. Pandas DataFrame 연동
    # --------------------------------------------------------
    def get_stock_data(self, code: str, limit: int = 60) -> pd.DataFrame:
        """Pandas는 SQLAlchemy engine을 직접 지원하므로 안전하게 연동 가능"""
        # 💡 [변경] code -> stock_code, date -> quote_date 반영
        query = f"SELECT * FROM daily_stock_quotes WHERE stock_code='{code}' ORDER BY quote_date DESC LIMIT {limit}"
        df = pd.read_sql(query, self.engine)
        if not df.empty:
            df = df.sort_values('quote_date').reset_index(drop=True)
        return df

    def get_latest_is_nxt(self, code: str) -> bool:
        """최신 거래일 기준 NXT 대상 종목 여부를 반환합니다."""
        target_code = str(code).replace('.0', '').strip().split('_')[0].replace('A', '').zfill(6)
        query = text("""
            SELECT COALESCE(is_nxt, FALSE) AS is_nxt
            FROM daily_stock_quotes
            WHERE stock_code = :code
            ORDER BY quote_date DESC
            LIMIT 1
        """)
        try:
            with self.engine.connect() as conn:
                row = conn.execute(query, {"code": target_code}).fetchone()
            return bool(row[0]) if row is not None else False
        except Exception as e:
            log_error(f"🚨 get_latest_is_nxt 실패 [{target_code}]: {e}")
            return False

    def get_latest_is_nxt_map(self, codes: list[str]) -> dict:
        """복수 종목에 대해 최신 거래일 기준 NXT 대상 여부를 dict로 반환합니다."""
        normalized = []
        for code in codes or []:
            if not code:
                continue
            normalized.append(str(code).replace('.0', '').strip().split('_')[0].replace('A', '').zfill(6))
        if not normalized:
            return {}

        query = text("""
            SELECT DISTINCT ON (stock_code) stock_code, COALESCE(is_nxt, FALSE) AS is_nxt
            FROM daily_stock_quotes
            WHERE stock_code = ANY(:codes)
            ORDER BY stock_code, quote_date DESC
        """)
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(query, {"codes": normalized}).fetchall()
            result = {str(code): bool(flag) for code, flag in rows}
            for code in normalized:
                result.setdefault(code, False)
            return result
        except Exception as e:
            log_error(f"🚨 get_latest_is_nxt_map 실패: {e}")
            return {code: False for code in normalized}

    # --------------------------------------------------------
    # 2. 매매 이력 및 종목 관리
    # --------------------------------------------------------
    def save_recommendation(self, date: str, code: str, name: str, price: int, pick_type: str, position: str, prob: float = 0.7, strategy: str = None):
        """종목 추천 이력 저장 (3대 표준 trade_type 강제 정규화)"""
        
        # 💡 [핵심 교정 1] 스캐너가 넘겨준 pick_type을 3대 표준 태그로 강제 매핑합니다.
        pick_type_upper = pick_type.upper()
        if 'SCALP' in pick_type_upper:
            normalized_type = 'SCALP'
        elif 'RUNNER' in pick_type_upper or 'KOSDAQ' in pick_type_upper:
            normalized_type = 'RUNNER'
        else:
            normalized_type = 'MAIN' # 기본값

        # 💡 [핵심 교정 2] 정규화된 태그에 맞춰 실제 매매 로직(strategy)을 짝지어줍니다.
        if not strategy:
            if normalized_type == 'SCALP':
                strategy = 'SCALPING'
            elif normalized_type == 'RUNNER':
                strategy = 'KOSDAQ_ML'
            else:
                strategy = 'KOSPI_ML'

        with self.get_session() as session:
            record = session.query(RecommendationHistory).filter_by(rec_date=date, stock_code=code).first()
            
            if record: # Update
                record.buy_price = price
                record.trade_type = normalized_type # 💡 표준화된 태그 저장
                record.strategy = strategy          # 💡 매핑된 전략 저장
                record.position_tag = position
                record.prob = prob
                
                if record.status == 'EXPIRED':
                    record.status = 'WATCHING'
            else:      # Insert
                new_record = RecommendationHistory(
                    rec_date=date,           
                    stock_code=code,         
                    stock_name=name,         
                    buy_price=price, 
                    trade_type=normalized_type, # 💡 표준화된 태그 저장
                    strategy=strategy,          # 💡 매핑된 전략 저장
                    status='WATCHING',
                    position_tag=position, 
                    prob=prob
                )
                session.add(new_record)
    
    def register_manual_stock(self, code: str, name: str) -> bool:
        """수동 감시 종목을 DB에 등록합니다."""
        today_date = datetime.now().date()
        target_code = str(code).zfill(6)

        try:
            with self.get_session() as session:
                record = session.query(RecommendationHistory).filter_by(
                    rec_date=today_date,
                    stock_code=target_code
                ).first()

                if record:
                    record.status = 'WATCHING'
                    record.trade_type = 'SCALP' 
                    record.strategy = 'SCALPING' # 💡 수동 등록 시 확실하게 단타 전략으로 덮어씌움
                else:
                    new_record = RecommendationHistory(
                        rec_date=today_date,     
                        stock_code=target_code,  
                        stock_name=name,         
                        buy_price=0,
                        trade_type='SCALP', # 태그는 단타로
                        strategy='SCALPING',       # 💡 실제 매매 로직은 확실한 SCALPING으로!
                        status='WATCHING',
                        position_tag='MIDDLE'
                    )
                    session.add(new_record)
                
            return True

        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"수동 타겟 DB 등록 오류 (ORM): {e}")
            return False
    
    def get_latest_history_date(self) -> str:
        """가장 최근 AI 스캐너 추천 기록의 날짜를 반환합니다."""
        try:
            with self.get_session() as session:
                # 💡 [변경] RecommendationHistory.date -> RecommendationHistory.rec_date
                latest_date = session.query(func.max(RecommendationHistory.rec_date)).scalar()
                
                # DB가 비어있을 경우 None 처리, 날짜 객체일 경우 문자열로 변환하여 리턴
                if latest_date:
                    return latest_date.strftime('%Y-%m-%d') if hasattr(latest_date, 'strftime') else str(latest_date)
                return None
                
        except Exception as e:
            log_error(f"최근 추천 기록 날짜 조회 실패: {e}")
            return None
    
    def get_history_by_date(self, date: str) -> pd.DataFrame:
        """특정 일자의 추천 종목 기록을 가져옵니다."""
        try:
            with self.get_session() as session:
                # 💡 [변경] date -> rec_date
                query = session.query(RecommendationHistory).filter_by(rec_date=date)
                df = pd.read_sql(query.statement, session.bind)
                return df

        except Exception as e:
            log_error(f"추천 기록 조회 실패 (날짜: {date}): {e}")
            return pd.DataFrame()
    
    def save_macro_alert(self, alert_data):
        """💡 [핵심] 글로벌 위기 알림을 DB에 저장 (중복 방어 포함)"""
        query = text("""
            INSERT INTO macro_alerts (alert_time, category, source, title, link, severity_score)
            VALUES (:alert_time, :category, :source, :title, :link, :severity_score)
            ON CONFLICT (link) DO NOTHING
        """)
        try:
            with self.get_session() as session:
                session.execute(query, alert_data)
                session.commit()
                return True
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 위기 경보 저장 실패: {e}")
            return False

    def get_recent_risk_count(self, hours=12, min_severity=2):
        """💡 [핵심] 최근 N시간 동안 발생한 심각한 위기 건수를 반환"""
        threshold = datetime.now() - timedelta(hours=hours)
        query = text("""
            SELECT COUNT(*) FROM macro_alerts 
            WHERE alert_time >= :threshold AND severity_score >= :min_severity
        """)
        try:
            with self.get_session() as session:
                return session.execute(query, {'threshold': threshold, 'min_severity': min_severity}).scalar()
        except Exception:
            return 0
    
    def get_active_targets(self) -> list:
        """
        💡 [핵심] 당일 감시 대상(WATCHING) 및 기존 보유 종목(HOLDING) 리스트를 
        엔진 규격에 맞는 딕셔너리 리스트로 반환합니다.
        고유 PK인 `id`를 포함하여 다중 스캘핑 시 데이터 덮어쓰기를 방지합니다.
        """
        import pandas as pd
        from datetime import datetime
        from src.utils.constants import TRADING_RULES
        
        try:
            today = datetime.now().date()
            
            with self.get_session() as session:
                # 💡 [핵심 교정 2] 이미 매매가 끝났거나(COMPLETED) 버려진(EXPIRED) 종목은 
                # 아예 DB에서 가져오지 않도록 쿼리단에서 컷오프! (메모리 낭비 완벽 차단)
                query = f"""
                    SELECT 
                        id, rec_date as date, stock_code as code, stock_name as name, 
                        trade_type as type, status, strategy, position_tag, prob, nxt, 
                        buy_price, buy_qty, buy_time, sell_price, sell_time, profit_rate 
                    FROM recommendation_history 
                    WHERE (rec_date='{today}' AND status NOT IN ('COMPLETED', 'EXPIRED')) 
                       OR status='HOLDING'
                """
                df = pd.read_sql(query, session.bind)

            if df.empty:
                return []

            # 💡 [핵심 교정 2] 상태값(status) 우선순위 강제 지정 (알파벳 정렬 버그 차단)
            # 가장 중요한 상태(HOLDING)부터 먼저 오도록 랭킹을 매깁니다.
            status_priority = {
                'HOLDING': 1, 
                'SELL_ORDERED': 2, 
                'BUY_ORDERED': 3, 
                'WATCHING': 4, 
                'COMPLETED': 5
            }
            df['priority'] = df['status'].map(status_priority).fillna(99)
            
            # 우선순위가 높은 순(오름차순), 그리고 id가 최신인 순(내림차순)으로 정렬 후 중복 제거
            df = df.sort_values(by=['priority', 'id'], ascending=[True, False])
            df = df.drop_duplicates(subset=['code'], keep='first')
            
            # 엔진에 넘기기 전에 임시 컬럼 삭제
            df = df.drop(columns=['priority'])
            
            targets = df.to_dict('records')

            # 기본값 보정 (스나이퍼 엔진의 부담을 DB 매니저가 덜어줍니다)
            default_prob = getattr(TRADING_RULES, 'SNIPER_AGGRESSIVE_PROB', 0.8)
            
            for t in targets:
                t['prob'] = t.get('prob', default_prob)
                t['buy_qty'] = t.get('buy_qty', 0)
                t['strategy'] = t.get('strategy', 'KOSPI_ML')

            return targets
            
        except Exception as e:
            from src.utils.logger import log_error
            print(f"감시 대상 로드 에러: {e}")
            log_error(f"감시 대상 로드 에러: {e}")
            return []

    # --------------------------------------------------------
    # 3. 텔레그램 유저 관리
    # --------------------------------------------------------
    
    def get_telegram_chat_ids(self) -> list:
        with self.get_session() as session:
            users = session.query(User.chat_id).all()
            return [user.chat_id for user in users]
        
    def check_special_auth(self, chat_id: int) -> bool:
        with self.get_session() as session:
            user = session.query(User).filter_by(chat_id=chat_id).first()
            # return bool(user and user.auth_group in ['A', 'V'])
            return bool(user and user.auth_group in ['A']) # VIP 등급 제거 (관리자만 허용), VIP는 일반 유저와 동일하게 취급, 추가기능개발시 VIP 등급 활용 예정


    def add_new_user(self, chat_id: int):
        with self.get_session() as session:
            exists = session.query(User).filter_by(chat_id=chat_id).first()
            if not exists:
                new_user = User(chat_id=chat_id)
                session.add(new_user)
    
    def check_analyze_quota(self, chat_id, consume=False):
        """
        사용자의 일일 AI 분석 횟수 제한을 확인하고, 필요시 차감합니다.
        반환: (is_allowed: bool, remaining: int, msg_text: str)
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter_by(chat_id=str(chat_id)).first()
                if not user:
                    # 사용자가 없으면 기본 허용 (무제한)
                    return True, 999, "무제한 분석 가능"
                
                today = datetime.now().date()
                last_date = user.last_analyze_date
                
                # 마지막 분석 날짜가 오늘이 아니면 카운트 리셋
                if last_date != today:
                    user.daily_analyze_count = 0
                    user.last_analyze_date = today
                
                # 일일 제한은 TRADING_RULES에서 가져오거나 기본값 10으로 설정
                from src.utils.constants import TRADING_RULES
                daily_limit = getattr(TRADING_RULES, 'DAILY_ANALYZE_LIMIT', 10)
                
                remaining = daily_limit - user.daily_analyze_count
                if remaining <= 0:
                    return False, 0, f"일일 분석 횟수({daily_limit}회)를 모두 사용했습니다. 내일 다시 시도해주세요."
                
                if consume:
                    user.daily_analyze_count += 1
                    remaining -= 1
                
                return True, remaining, f"남은 분석 횟수: {remaining}회"
        except Exception as e:
            # 에러 발생 시 안전하게 허용 처리
            import traceback
            traceback.print_exc()
            return True, 999, f"쿼터 확인 중 에러: {e}"
    
    def update_user_active_status(self, chat_id: int, is_active: bool = True) -> bool:
        """
        💡 [핵심] 사용자의 봇 활성화 상태(차단/해제)를 업데이트합니다.
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter_by(chat_id=chat_id).first()
                
                if user:
                    user.is_active = is_active
                    # session.commit()은 get_session() 제너레이터에서 자동 처리됨
                    
                    status_str = "활성화(복귀)" if is_active else "비활성화(차단)"
                    print(f"🔄 [DBManager] 유저({chat_id}) 상태가 '{status_str}'(으)로 변경되었습니다.")
                    return True
                else:
                    print(f"⚠️ [DBManager] 상태를 변경할 유저({chat_id})를 찾을 수 없습니다.")
                    return False
                    
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 유저 활성화 상태 업데이트 에러: {e}")
            return False
            
    def delete_user(self, chat_id: int) -> bool:
        """
        💡 [핵심] 사용자가 봇을 차단하거나 방을 나갔을 때 DB에서 완전히 삭제합니다.
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter_by(chat_id=chat_id).first()
                if user:
                    session.delete(user)
                    print(f"🗑️ [DBManager] 유저({chat_id})가 DB에서 완전히 삭제되었습니다.")
                    return True
                else:
                    print(f"⚠️ [DBManager] 삭제할 유저({chat_id})를 DB에서 찾을 수 없습니다.")
                    return False
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 유저 삭제 DB 에러: {e}")
            return False
    
    def get_user_level(self, chat_id):
        """
        💡 [핵심] 특정 사용자의 등급(Admin/VIP/User)을 조회합니다.
        - 'A': 관리자 (Admin)
        - 'V': VIP 후원자 (VIP)
        - 'U': 일반 사용자 (User) - 기본값
        """
        chat_id_str = str(chat_id)
        
        try:
            from src.database.models import User # 💡 순환 참조 방지를 위한 지역 임포트
            
            with self.get_session() as session:
                # 1. DB에서 해당 chat_id를 가진 사용자 검색
                user = session.query(User).filter_by(chat_id=chat_id_str).first()
                
                # 2. 사용자가 존재하면 해당 레벨 반환, 없으면 기본값 'U' 반환
                if user and user.auth_group:
                    return user.auth_group
                
                # 💡 사용자가 없거나 레벨이 비어있다면 일반 유저('U')로 간주
                return 'U'
                
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"❌ 사용자 레벨 조회 중 에러 ({chat_id_str}): {e}")
            return 'U' # 에러 발생 시 보안을 위해 가장 낮은 등급 반환
    
    def upgrade_user_level(self, chat_id: int, level: str = 'V') -> bool:
        """
        사용자의 등급을 업데이트합니다. (기본값: 'V')
        """
        # 💡 [아키텍처 포인트] 파일 최상단에 User 모델이 임포트되어 있지 않다면
        # 순환 참조 방지를 위해 함수 내부에서 임포트합니다.
        from src.database.models import User 

        try:
            # 💡 [핵심 교정] sqlite3 원시 쿼리 대신 SQLAlchemy 세션 사용
            with self.get_session() as session:
                # 1. 대상 유저 조회 (chat_id를 문자열로 캐스팅하여 안전하게 비교)
                user = session.query(User).filter_by(chat_id=str(chat_id)).first()
                
                if user:
                    # 2. 유저가 존재하면 등급 업데이트 (숫자 1 대신 'VIP' 같은 문자열 사용)
                    user.auth_group = level
                    # session.commit()은 get_session()의 Context Manager(with문)가 
                    # 정상 종료될 때 자동으로 수행되지만, 명시적으로 적어주어도 좋습니다.
                    session.commit()
                    print(f"✅ [DBManager] 유저({chat_id}) 등급이 '{level}'(으)로 승격되었습니다.")
                    return True
                else:
                    print(f"⚠️ [DBManager] 승격할 유저({chat_id})를 DB에서 찾을 수 없습니다.")
                    return False
                    
        except Exception as e:
            from src.utils.logger import log_error
            log_error(f"유저 등급 업데이트 DB 에러: {e}")
            return False