from sqlalchemy import Column, Integer, BigInteger, Float, String, Text, Date, DateTime, Boolean, Index, UniqueConstraint, ForeignKey, text
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
    entry_armed_at_epoch = Column(Float)
    
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


class TradePerformanceFact(Base):
    __tablename__ = 'trade_performance_facts'
    __table_args__ = (
        Index("idx_tpf_rec_date", "rec_date"),
        Index("idx_tpf_rec_date_status", "rec_date", "status"),
        Index("idx_tpf_rec_date_strategy_tag", "rec_date", "strategy", "position_tag"),
        Index("idx_tpf_rec_date_pnl_profit", "rec_date", "realized_pnl_krw", "profit_rate"),
    )

    recommendation_id = Column(Integer, primary_key=True)
    rec_date = Column(Date, nullable=False)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(Text)
    strategy = Column(Text, nullable=False)
    position_tag = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    buy_price = Column(Float, server_default=text("0"))
    buy_qty = Column(Integer, server_default=text("0"))
    buy_time = Column(DateTime)
    sell_price = Column(Float, server_default=text("0"))
    sell_time = Column(DateTime)
    profit_rate = Column(Float, server_default=text("0"))
    realized_pnl_krw = Column(Integer, server_default=text("0"))
    holding_seconds = Column(Integer)
    exit_rule = Column(Text)
    sell_reason_type = Column(Text)
    add_count = Column(Integer, server_default=text("0"))
    avg_down_count = Column(Integer, server_default=text("0"))
    pyramid_count = Column(Integer, server_default=text("0"))
    ai_review_headline = Column(Text)
    gatekeeper_action = Column(Text)
    gatekeeper_allow_entry = Column(Boolean)
    synced_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<TradePerformanceFact(recommendation_id={self.recommendation_id}, strategy='{self.strategy}', position_tag='{self.position_tag}')>"


class StrategyPositionPerformanceDaily(Base):
    __tablename__ = 'strategy_position_performance_daily'
    __table_args__ = (
        Index("idx_sppd_rec_date_pnl_entered", "rec_date", "realized_pnl_krw", "entered_count"),
        Index("idx_sppd_strategy_tag_date", "strategy", "position_tag", "rec_date"),
    )

    rec_date = Column(Date, primary_key=True)
    strategy = Column(Text, primary_key=True)
    position_tag = Column(Text, primary_key=True)
    entered_count = Column(Integer, server_default=text("0"))
    completed_count = Column(Integer, server_default=text("0"))
    open_count = Column(Integer, server_default=text("0"))
    win_count = Column(Integer, server_default=text("0"))
    loss_count = Column(Integer, server_default=text("0"))
    flat_count = Column(Integer, server_default=text("0"))
    realized_pnl_krw = Column(Integer, server_default=text("0"))
    avg_profit_rate = Column(Float, server_default=text("0"))
    avg_holding_seconds = Column(Float, server_default=text("0"))
    best_trade_code = Column(String(10))
    best_trade_name = Column(Text)
    best_profit_rate = Column(Float)
    worst_trade_code = Column(String(10))
    worst_trade_name = Column(Text)
    worst_profit_rate = Column(Float)
    synced_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<StrategyPositionPerformanceDaily(rec_date='{self.rec_date}', strategy='{self.strategy}', position_tag='{self.position_tag}')>"


class SwingStrategyDiscoveryCandidate(Base):
    __tablename__ = 'swing_strategy_discovery_candidates'
    __table_args__ = (
        UniqueConstraint('source_date', 'stock_code', 'policy_version', name='uq_ssd_candidate_date_code_policy'),
        Index('idx_ssd_candidate_date_arm', 'source_date', 'selection_arm'),
        Index('idx_ssd_candidate_date_score', 'source_date', 'lifecycle_exploration_score'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_date = Column(Date, nullable=False)
    stock_code = Column(String(10), nullable=False)
    stock_name = Column(Text)
    policy_version = Column(Text, nullable=False)
    selection_arm = Column(Text, nullable=False)
    diversity_bucket = Column(Text)
    position_tag = Column(Text)
    block_reason = Column(Text)
    volatility_bucket = Column(Text)
    sector = Column(Text)
    industry = Column(Text)
    theme_tags = Column(Text)
    legacy_model_prob = Column(Float)
    legacy_model_rank = Column(Integer)
    legacy_selection_mode = Column(Text)
    legacy_pick_type = Column(Text)
    legacy_meta_score = Column(Float)
    legacy_hybrid_mean = Column(Float)
    lifecycle_exploration_score = Column(Float)
    source_features = Column(Text)
    decision_authority = Column(Text, server_default=text("'swing_sim_exploration_only'"))
    actual_order_submitted = Column(Boolean, server_default=text("false"))
    broker_order_forbidden = Column(Boolean, server_default=text("true"))
    runtime_effect = Column(Boolean, server_default=text("false"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<SwingStrategyDiscoveryCandidate(source_date='{self.source_date}', stock_code='{self.stock_code}', policy_version='{self.policy_version}')>"


class SwingStrategyDiscoveryArm(Base):
    __tablename__ = 'swing_strategy_discovery_arms'
    __table_args__ = (
        UniqueConstraint('candidate_id', 'arm_id', 'policy_version', name='uq_ssd_arm_candidate_arm_policy'),
        Index('idx_ssd_arm_date_status', 'source_date', 'status'),
        Index('idx_ssd_arm_date_policy', 'source_date', 'entry_policy', 'sizing_policy', 'exit_policy'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('swing_strategy_discovery_candidates.id'), nullable=False)
    source_date = Column(Date, nullable=False)
    stock_code = Column(String(10), nullable=False)
    policy_version = Column(Text, nullable=False)
    arm_id = Column(Text, nullable=False)
    entry_policy = Column(Text, nullable=False)
    sizing_policy = Column(Text, nullable=False)
    exit_policy = Column(Text, nullable=False)
    status = Column(Text, server_default=text("'PENDING_ENTRY'"))
    virtual_entry_price = Column(Float)
    virtual_qty = Column(Integer, server_default=text("0"))
    virtual_notional_krw = Column(BigInteger, server_default=text("0"))
    entry_at = Column(DateTime)
    exit_at = Column(DateTime)
    exit_price = Column(Float)
    final_return_pct = Column(Float)
    arm_features = Column(Text)
    actual_order_submitted = Column(Boolean, server_default=text("false"))
    broker_order_forbidden = Column(Boolean, server_default=text("true"))
    runtime_effect = Column(Boolean, server_default=text("false"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<SwingStrategyDiscoveryArm(candidate_id={self.candidate_id}, arm_id='{self.arm_id}', policy_version='{self.policy_version}')>"


class SwingStrategyDiscoveryLabel(Base):
    __tablename__ = 'swing_strategy_discovery_labels'
    __table_args__ = (
        UniqueConstraint('arm_row_id', 'label_horizon', 'label_version', name='uq_ssd_label_arm_horizon_version'),
        Index('idx_ssd_label_date_horizon', 'source_date', 'label_horizon'),
        Index('idx_ssd_label_date_status', 'source_date', 'label_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    arm_row_id = Column(Integer, ForeignKey('swing_strategy_discovery_arms.id'), nullable=False)
    source_date = Column(Date, nullable=False)
    stock_code = Column(String(10), nullable=False)
    policy_version = Column(Text, nullable=False)
    label_horizon = Column(Text, nullable=False)
    label_version = Column(Text, nullable=False)
    label_status = Column(Text, server_default=text("'pending'"))
    mfe_pct = Column(Float)
    mae_pct = Column(Float)
    close_return_pct = Column(Float)
    final_return_pct = Column(Float)
    realized_exit_return_pct = Column(Float)
    exit_only_delta_pct = Column(Float)
    scale_in_delta_pct = Column(Float)
    label_features = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    def __repr__(self):
        return f"<SwingStrategyDiscoveryLabel(arm_row_id={self.arm_row_id}, label_horizon='{self.label_horizon}', label_version='{self.label_version}')>"


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
