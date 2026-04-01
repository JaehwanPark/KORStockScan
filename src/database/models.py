from sqlalchemy import Column, Integer, BigInteger, Float, String, Text, Date, DateTime, Boolean, text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class DailyStockQuote(Base):
    __tablename__ = 'daily_stock_quotes'

    # 💡 [핵심] Date -> quote_date, Code -> stock_code로 명확화 및 복합키 설정
    quote_date = Column(Date, primary_key=True)
    stock_code = Column(String(10), primary_key=True)
    stock_name = Column(Text)
    
    # 가격 및 거래량
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Float)
    
    # 기술적 지표
    ma5 = Column(Float)
    ma20 = Column(Float)
    ma60 = Column(Float)
    ma120 = Column(Float)
    rsi = Column(Float)
    macd = Column(Float)
    macd_sig = Column(Float)
    macd_hist = Column(Float)

    # 💡 [신규 추가] sqlite.sql에 명시된 지표들 완벽 동기화
    bbl = Column(Float)
    bbm = Column(Float)
    bbu = Column(Float)
    bbb = Column(Float)
    bbp = Column(Float)
    vwap = Column(Float)
    obv = Column(Float)
    atr = Column(Float)
    
    # 파이썬 예약어인 'return'과 충돌을 피하기 위해 변수명은 'daily_return'으로 명명
    daily_return = Column(Float)
    
    # 수급 및 기타 지표
    marcap = Column(BigInteger, server_default=text("0"))
    retail_net = Column(Float, server_default=text("0"))
    foreign_net = Column(Float, server_default=text("0"))
    inst_net = Column(Float, server_default=text("0"))
    margin_rate = Column(Float, server_default=text("0"))
    is_nxt = Column(Boolean, server_default=text("false"))

    def __repr__(self):
        return f"<DailyStockQuote(quote_date='{self.quote_date}', stock_code='{self.stock_code}')>"


class MacroAlert(Base):
    __tablename__ = 'macro_alerts'

    # 💡 신규 추가된 거시경제 알림 테이블
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_time = Column(DateTime)
    category = Column(Text)
    source = Column(Text)
    title = Column(Text)
    link = Column(Text, unique=True) # UNIQUE 제약조건 반영
    severity_score = Column(Integer)

    def __repr__(self):
        return f"<MacroAlert(id={self.id}, category='{self.category}')>"


class RecommendationHistory(Base):
    __tablename__ = 'recommendation_history'

    # 💡 [핵심 교정] 새롭게 추가된 id를 Primary Key로 지정합니다.
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 기존에 PK 역할을 하던 두 컬럼은 일반 컬럼으로 강등(?) 시킵니다.
    rec_date = Column(Date, nullable=False) 
    stock_code = Column(String(10), nullable=False)
    
    stock_name = Column(Text)
    trade_type = Column(Text)
    status = Column(Text, server_default=text("'WATCHING'"))
    strategy = Column(Text, server_default=text("'KOSPI_ML'"))
    position_tag = Column(Text, server_default=text("'MIDDLE'"))
    prob = Column(Float, server_default=text("0.70"))
    nxt = Column(Float)
    
    buy_price = Column(Float)
    buy_qty = Column(Integer, server_default=text("0"))
    buy_time = Column(DateTime) # DDL에 맞춰 진정한 DateTime으로 복귀!
    
    sell_price = Column(Integer, server_default=text("0"))
    sell_time = Column(DateTime)
    profit_rate = Column(Float, server_default=text("0.0"))

    # ---- 추가매수(물타기/불타기) 제어 필드 ----
    add_count = Column(Integer, nullable=True, server_default=text("0"))
    avg_down_count = Column(Integer, nullable=True, server_default=text("0"))
    pyramid_count = Column(Integer, nullable=True, server_default=text("0"))
    last_add_type = Column(Text, nullable=True)
    last_add_at = Column(DateTime, nullable=True)
    scale_in_locked = Column(Boolean, nullable=True, server_default=text("false"))
    hard_stop_price = Column(Float, nullable=True)
    trailing_stop_price = Column(Float, nullable=True)

    def __repr__(self):
        return f"<RecommendationHistory(rec_date='{self.rec_date}', stock_code='{self.stock_code}')>"


class HoldingAddHistory(Base):
    __tablename__ = 'holding_add_history'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, nullable=False)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(Text)
    strategy = Column(Text)
    add_type = Column(Text)
    event_type = Column(Text, nullable=False)
    event_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    order_no = Column(Text)
    request_qty = Column(Integer, server_default=text("0"))
    executed_qty = Column(Integer, server_default=text("0"))
    request_price = Column(Float)
    executed_price = Column(Float)
    prev_buy_price = Column(Float)
    new_buy_price = Column(Float)
    prev_buy_qty = Column(Integer, server_default=text("0"))
    new_buy_qty = Column(Integer, server_default=text("0"))
    add_count_after = Column(Integer, server_default=text("0"))
    reason = Column(Text)
    note = Column(Text)

    def __repr__(self):
        return f"<HoldingAddHistory(recommendation_id={self.recommendation_id}, event_type='{self.event_type}')>"


class User(Base):
    __tablename__ = 'users'

    # 💡 Telegram ID를 위한 BigInteger
    chat_id = Column(BigInteger, primary_key=True)
    joined_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    auth_group = Column(Text, server_default=text("'USER'"))
    # 💡 [신규 추가] 봇 활성화 상태 (차단/나가기 감지용)
    is_active = Column(Boolean, default=True, server_default=text("true"))
    
    # 💡 [신규 추가] 실시간 종목분석 일일 사용량 제한용
    daily_analyze_count = Column(Integer, default=0, server_default=text("0"))
    last_analyze_date = Column(Date)

    def __repr__(self):
        return f"<User(chat_id={self.chat_id}, auth_group='{self.auth_group}')>"
