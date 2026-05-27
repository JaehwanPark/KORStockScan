# src/utils/constants.py
import os
from dataclasses import dataclass, replace
from pathlib import Path

# Pathlib을 사용하면 os.path.join 보다 훨씬 우아하게 경로를 관리할 수 있습니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
LEGACY_LOGS_DIR = PROJECT_ROOT / 'src' / 'logs'
RESTART_FLAG_PATH = PROJECT_ROOT / 'restart.flag'
CONFIG_PATH = DATA_DIR / 'config_prod.json'
DEV_PATH = DATA_DIR / 'config_dev.json'
UTILS_DIR = PROJECT_ROOT / 'src' / 'utils'
ENGINE_DIR = PROJECT_ROOT / 'src' / 'engine'
MODEL_DIR = PROJECT_ROOT / 'src' / 'model'
NOTIFY_DIR = PROJECT_ROOT / 'src' / 'notify'
POSTGRES_URL = "postgresql://quant_admin:quant_password_123!@localhost:5432/korstockscan"

@dataclass(frozen=True) # frozen=True로 설정하면 읽기 전용(상수)이 되어 안전하게 사용할 수 있습니다.
class TradingConfig:
    # ==========================================
    # 1. 기초 필터 (유동성 및 대상 조건)
    # ==========================================
    MIN_PRICE: int = 5000  # 최소 주가 (동전주 및 초저가 잡주 배제)
    TOP_N_MARCAP: int = 200  # 시가총액 상위 N개 추출
    TOP_N_VOLUME: int = 150  # 그 중 거래량 상위 N개 추출

    # ==========================================
    # 2. AI 판독 확신도 (Probability Thresholds)
    # ==========================================
    # PROB_MAIN_PICK: float = 0.82  # 정규 스캐너 '강력 추천(MAIN)' 기준 점수
    # PROB_RUNNER_PICK: float = 0.75  # 정규 스캐너 '관심 종목(RUNNER)' 기준 점수
    PROB_MAIN_PICK: float = 0.58  # 2025년부터 2026년까지의 최적화 결과 반영 (0.58로 완화) '강력 추천(MAIN)' 기준 점수
    PROB_RUNNER_PICK: float = 0.52  # 2025년부터 2026년까지의 최적화 결과 반영 (0.52로 완화) '관심 종목(RUNNER)' 기준 점수

    # ==========================================
    # 3. 매매 타점 및 익절/손절 (Sniper Engine)
    # ==========================================
    SNIPER_AGGRESSIVE_PROB: float = 0.75     # 🏆 AI 진입 확신도 임계값 (기존 0.85 -> 0.75 완화)

    # ==========================================
    # 3.1 추가매수(물타기/불타기) 공통 설정
    # ==========================================
    ENABLE_SCALE_IN: bool = True  # add scale-in 활성화
    SCALE_IN_REQUIRE_HISTORY_TABLE: bool = False  # holding_add_history 준비 완료
    SCALE_IN_FAIL_CLOSED_ON_PROTECTION_ERROR: bool = True  # 보호선 재설정 실패 시 fail-closed
    MAX_POSITION_PCT: float = 0.20  # 남은 리스크 예산 우선
    SCALE_IN_COOLDOWN_SEC: int = 180  # 추가매수 재시도 쿨다운
    SCALE_IN_CANCEL_COOLDOWN_SEC: int = 120  # 미체결 추가매수 취소 후 재접수 쿨다운
    ADD_JUDGMENT_LOCK_SEC: int = 20  # 추가매수 판단 락(스팸 판단 방지)
    SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC: int = 180  # 불타기 체결 직후 trailing 조기청산 억제
    SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED: bool = True  # 추가매수 주문 직전 P1 지정가 resolver
    SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED: bool = True  # 추가매수 live 수량 safety 결정
    SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP: int = 1  # 추가매수 수량 hard cap. 0 이하는 수량 cap 없음
    SCALPING_SCALE_IN_MAX_SPREAD_BPS: float = 80.0  # 추가매수 resolver 스프레드 상한(bp)
    SCALPING_PYRAMID_PRICE_GUARD_ENABLED: bool = True  # 불타기 추격 지정가 안전장치
    SCALPING_PYRAMID_MAX_SPREAD_BPS: float = 80.0  # 호환 alias: scale-in spread guard
    SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS: float = 60.0  # micro-VWAP 대비 과열 추격 상한(bp)
    SCALPING_PYRAMID_MIN_AI_SCORE: int = 70  # PYRAMID 허용 AI 최소점수
    SCALPING_PYRAMID_MIN_BUY_PRESSURE: float = 60.0  # PYRAMID 허용 매수압 최소값
    SCALPING_PYRAMID_MIN_TICK_ACCEL: float = 0.5  # PYRAMID 허용 틱 가속 최소값
    STAT_ACTION_DECISION_SNAPSHOT_ENABLED: bool = True  # 행동가중치용 HOLDING decision snapshot observe-only
    STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC: int = 30  # IO guard: 종목별 snapshot 최소 간격

    # ==========================================
    # 3.2 추가매수(스캘핑) 설정
    # ==========================================
    SCALPING_ENABLE_PYRAMID: bool = True
    SCALPING_MAX_AVG_DOWN_COUNT: int = 0  # DEPRECATED: reversal_add/AVG_DOWN receipt attribution only
    SCALPING_MAX_PYRAMID_COUNT: int = 0  # DEPRECATED: runtime count gate removed; counter remains for attribution
    SCALPING_PYRAMID_MIN_PROFIT_PCT: float = 1.5
    SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED: bool = True  # buy_qty*ratio가 0일 때 최소 1주 floor 허용
    SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED: bool = True  # 손실 청산 후 동일종목 신규 BUY 재시도 차단
    SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC: int = 3600  # soft/protect/refined 손실 후 60분 재진입 금지
    SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_ENABLED: bool = False  # live loss reentry cooldown 전환 후 shadow 기본 OFF
    SCALP_SOFT_STOP_SAME_SYMBOL_COOLDOWN_SHADOW_SEC: int = 600  # historical/replay 전용 기준

    # ==========================================
    # 3.3 추가매수(스윙) 설정
    # ==========================================
    SWING_ENABLE_PYRAMID: bool = True
    SWING_ENABLE_AVG_DOWN_SIMULATION: bool = True  # dry-run/probe 전용 물타기 후보 관찰
    SWING_MAX_AVG_DOWN_COUNT: int = 0  # DEPRECATED: historical AVG_DOWN receipt attribution only
    SWING_MAX_PYRAMID_COUNT: int = 0  # DEPRECATED: runtime count gate removed; counter remains for attribution
    SWING_PYRAMID_MIN_PROFIT_PCT: float = 4.0
    SWING_AVG_DOWN_MIN_LOSS_PCT: float = -3.0  # simulation-only AVG_DOWN 손실 하한
    SWING_AVG_DOWN_MAX_LOSS_PCT: float = -0.8  # simulation-only AVG_DOWN 손실 상한
    SWING_AVG_DOWN_MAX_PEAK_PROFIT_PCT: float = 1.0  # 이미 충분히 green이었던 표본 제외
    SWING_AVG_DOWN_MIN_HOLD_SEC: int = 300  # 너무 이른 스윙 물타기 관찰 방지
    SWING_SCALE_IN_DYNAMIC_QTY_ENABLED: bool = True  # 스윙 sim/probe scale-in 수량 provenance
    SWING_SCALE_IN_EFFECTIVE_QTY_CAP: int = 0  # 0 이하는 sim/probe 수량 cap 없음
    SWING_SCALE_IN_REAL_CANARY_ENABLED: bool = False  # phase0 real canary is enabled only by PREOPEN auto-approval env
    SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS: str = "PYRAMID,AVG_DOWN"
    SWING_SCALE_IN_REAL_CANARY_MAX_QTY: int = 1
    SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY: int = 1
    SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION: int = 1
    SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW: int = 100000
    SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT: bool = False
    SWING_ONE_SHARE_REAL_CANARY_ENABLED: bool = False  # phase0 real canary is enabled only by PREOPEN auto-approval env
    SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES: str = ""  # PREOPEN auto approval or optional artifact allowlist only
    SWING_ONE_SHARE_REAL_CANARY_MAX_QTY: int = 1
    SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY: int = 1
    SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS: int = 3
    SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW: int = 300000
    SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT: bool = False
    SWING_LIVE_ORDER_DRY_RUN_ENABLED: bool = True  # 스윙 live 로직은 동일 실행, 실제 주문 접수만 차단
    SWING_LIVE_ORDER_DRY_RUN_OWNER: str = "SwingLiveOrderDryRunSimulation0511"
    SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED: bool = True  # 스윙 차단 stage 이후 live-equivalent observe-only probe
    SWING_INTRADAY_PROBE_OWNER: str = "SwingIntradayLiveEquivalentProbe0511"
    SWING_INTRADAY_PROBE_MAX_OPEN: int = 10
    SWING_INTRADAY_PROBE_MAX_DAILY: int = 30
    SWING_INTRADAY_PROBE_MAX_PER_SYMBOL: int = 1
    SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN: int = 4
    SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC: int = 60
    SWING_INTRADAY_PROBE_PERSIST_ENABLED: bool = True
    SWING_INTRADAY_PROBE_COUNTERFACTUAL_GATEKEEPER_ENABLED: bool = True
    SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED: bool = True
    SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC: int = 3600
    SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT: float = -2.5
    SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES: int = 2
    SWING_SAME_SYMBOL_LOSS_REENTRY_COUNTERFACTUAL_ENABLED: bool = True
    SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED: bool = True  # 스윙 OFI/QI observe/proposal-only context
    SCALP_LIVE_SIMULATOR_ENABLED: bool = True  # 스캘핑 AI BUY 전체 대상 live simulator 기본 ON
    SCALP_LIVE_SIMULATOR_OWNER: str = "ScalpAiBuyAllLiveSimulator0511"
    SCALP_LIVE_SIMULATOR_FILL_POLICY: str = "signal_inclusive_best_ask_v1"
    SCALP_LIVE_SIMULATOR_QTY: int = 0  # 0 이하는 SIM_VIRTUAL_BUDGET_KRW 기준 실주문 동적수량 산식 사용
    SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC: int = 90  # deprecated: BUY signal inclusion no longer expires on quote touch
    SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED: bool = False
    SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE: int = 55
    SCALP_SIM_CANDIDATE_WINDOW_MAX_SCORE: int = 100
    SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN: int = 20
    SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY: int = 160
    SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT: int = 60
    SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT: int = 30
    SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY: str = (
        "09:00-10:00=56,10:00-12:00=32,12:00-14:00=40,14:00-15:30=32"
    )
    SCALP_SIM_AI_BUDGET_ENABLED: bool = False
    SCALP_SIM_AI_MAX_CALLS_PER_MIN: int = 10
    SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC: int = 90
    SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC: int = 30
    SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC: int = 180
    SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED: bool = True
    SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT: float = -0.70
    SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED: bool = True
    SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED: bool = False
    SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT: float = 0.50
    SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED: bool = False
    SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS: str = "PYRAMID,AVG_DOWN"
    SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT: float = -2.5
    SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT: float = 2.5
    SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION: int = 1
    SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY: int = 30
    SCALP_SIM_PANIC_LIFECYCLE_ENABLED: bool = True
    SCALP_SIM_PANIC_ENTRY_BLOCK_ENABLED: bool = True
    SCALP_SIM_PANIC_SCALE_IN_BLOCK_ENABLED: bool = True
    SCALP_SIM_PANIC_HOLDING_EXIT_ENABLED: bool = True
    SCALP_SIM_PANIC_PARTIAL_SELL_ENABLED: bool = True
    SCALP_SIM_PANIC_FORCE_NOOP: bool = False
    SCALP_SIM_PANIC_BLOCK_ENTRY_LEVEL: int = 1
    SCALP_SIM_PANIC_DISABLE_SCALE_IN_LEVEL: int = 1
    SCALP_SIM_PANIC_BOTTOMING_ENTRY_ENABLED: bool = True
    SCALP_SIM_PANIC_BOTTOMING_ENTRY_MAX_LEVEL: int = 1
    SCALP_SIM_PANIC_BOTTOMING_MIN_AI_SCORE: float = 60.0
    SCALP_SIM_PANIC_BOTTOMING_MIN_BUY_PRESSURE: float = 55.0
    SCALP_SIM_PANIC_BOTTOMING_MAX_DISTANCE_FROM_HIGH_PCT: float = -3.0
    SCALP_SIM_PANIC_BOTTOMING_MIN_STRENGTH: float = 65.0
    SCALP_SIM_PANIC_MIN_REMAINING_QTY: int = 1
    SCALP_SIM_PANIC_MAX_PARTIAL_COUNT_PER_EPOCH: int = 1
    SCALP_SIM_PANIC_CONTEXT_MAX_AGE_SEC: int = 600
    SCALP_SIM_PANIC_FALLBACK_SLIPPAGE_BPS: float = 10.0
    SCALP_SIM_PANIC_BROKEN_LIQUIDITY_HAIRCUT_BPS: float = 30.0
    SIM_VIRTUAL_BUDGET_KRW: int = 10_000_000  # sim/probe/counterfactual 전용 가상 주문가능금액. 실계좌 예산과 분리

    # [매매 비중 설정] 전략별 주문 가능 현금 대비 1회 매수 투입 비율
    INVEST_RATIO_KOSPI: float = 0.25  # DEPRECATED: MIN/MAX 비중으로 대체됨
    INVEST_RATIO_KOSDAQ: float = 0.15  # DEPRECATED: MIN/MAX 비중으로 대체됨
    INVEST_RATIO_SCALPING_MIN: float = 0.07  # 2026-04-20 risk cut: 스캘핑 최소 투자 비율 (10% -> 7%)
    INVEST_RATIO_SCALPING_MAX: float = 0.22  # 2026-04-20 risk cut: 스캘핑 최대 투자 비율 (30% -> 22%)
    SCALPING_MAX_BUY_BUDGET_KRW: int = 1_200_000  # 2026-04-20 risk cut: 스캘핑 신규 진입 1회 절대 투자금 상한 (1,600,000 -> 1,200,000)
    SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED: bool = True  # 신규 BUY 접수 1주 cap 기본 ON
    SCALPING_INITIAL_ENTRY_MAX_QTY: int = 1  # 0 이하는 신규 BUY 수량 cap 없음
    BUY_SIDE_TIME_BLOCK_ENABLED: bool = True  # 신규 매수/추가매수 브로커 제출 시간 차단
    BUY_SIDE_TIME_BLOCK_UNTIL_HHMM: str = "10:00"  # KST 기준, 이 시각 전 BUY 제출 차단

    # 💡 [신규 추가] 스윙 AI 동적 비중 조절용 (Min~Max)
    INVEST_RATIO_KOSDAQ_MIN: float = 0.05  # 코스닥 AI 점수 60점일 때 (5%)
    INVEST_RATIO_KOSDAQ_MAX: float = 0.15  # 코스닥 AI 점수 100점일 때 (15%)
    INVEST_RATIO_KOSPI_MIN: float = 0.10   # 코스피 우량주 AI 점수 60점일 때 (10%)
    INVEST_RATIO_KOSPI_MAX: float = 0.40   # 코스피 우량주 AI 점수 100점일 때 (40%)
    BUY_BUDGET_SAFETY_RATIO: float = 0.95  # 기본 주문 안전계수
    BUY_BUDGET_RELAXED_SAFETY_RATIO: float = 1.00  # 1주도 안 나올 때만 재시도하는 완화 안전계수
    DEPOSIT_API_RETRY_COUNT: int = 2  # 주문가능금액 조회 일시 실패 시 재시도 횟수
    DEPOSIT_API_RETRY_DELAY_SEC: float = 0.15  # 주문가능금액 재시도 간격(초)
    DEPOSIT_CACHE_FALLBACK_TTL_SEC: int = 30  # 최근 정상 주문가능금액 fallback 허용 시간(초)
    ZERO_DEPOSIT_RETRY_COOLDOWN_SEC: int = 20  # 주문가능금액 0원 단발성 조회 실패 의심 시 재조회 대기

    # 💡 [변경] 스윙 손절선 (백테스트 기준 -3.0% 반영)
    STOP_LOSS_BULL: float = -3.0  # 🏆 상승장 손절선 (최적화 결과 -3.0 반영)
    STOP_LOSS_BEAR: float = -3.0  # 🏆 하락장 손절선 (최적화 결과 -3.0 통일)
    STOP_LOSS_BREAKOUT: float = -1.5  # 돌파 실패 시 칼손절 (-1.5%)
    STOP_LOSS_BOTTOM: float = -4.0  # 바닥권 매물 소화 버티기용 (-4.0%)

    # 💡 [변경] 스윙 트레일링 룰
    TRAILING_START_PCT: float = 2.5  # 🏆 스윙 트레일링 시작 수익률
    TRAILING_DRAWDOWN_PCT: float = 0.5  # 🏆 스윙 고점 대비 허용 되밀림 폭 (%)
    MIN_PROFIT_PRESERVE: float = 1.5  # DEPRECATED: 런타임 미사용 (과거 최소 수익 보존)


    # 💡 [신규] 초단타 스캐너 설정
    SCALP_TIME_LIMIT_MIN: int = 60  # DEPRECATED: 런타임 미사용 (과거 스캘핑 시간 제한)
    MIN_FEE_COVER: float = 0.3  # 세금(0.2%) + 수수료 보존용 최소 익절선 (0.3%)
    TRADE_COST_RATE: float = 0.0023  # 실체결 수익률/손익 계산에 쓰는 보수적 거래비용 비율
    VPW_SCALP_LIMIT: int = 120  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    SCALP_DYNAMIC_VPW_ENABLED: bool = True  # 동적 체결강도 게이트 관측/사용 여부
    SCALP_DYNAMIC_VPW_OBSERVE_ONLY: bool = False  # False면 동적 체결강도 게이트를 실전 진입에 적용
    SCALP_PRE_AI_SOFT_GATE_ENABLED: bool = True  # pre-AI mechanical gate는 기본 risk context로 낮춘다
    SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED: bool = True  # stale/insufficient/extreme sell source는 AI 전 차단
    SCALP_PRE_AI_MAX_WS_AGE_SEC: float = 3.0  # pre-AI source-quality stale 판단 기준
    SCALP_PRE_AI_EXTREME_SELL_BUY_RATIO_MAX: float = 0.35  # 극단 매도우위 risk source block 기준
    SCALP_PRE_AI_EXTREME_SELL_EXEC_BUY_RATIO_MAX: float = 0.35
    SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED: bool = True  # overbought 후보는 AI 후 submit 직전 pullback/rebreak 확인
    SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT: float = -0.35
    SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH: float = 120.0
    SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE: float = 60.0
    SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED: bool = True  # liquidity는 AI 전 관찰, 주문 직전 hard guard 유지
    SCALP_ENTRY_ARM_TTL_SEC: int = 20  # 스캘핑 자격 게이트 통과 후 재평가 없이 주문 단계로 유지할 시간
    WS_REG_BATCH_SIZE: int = 20  # 웹소켓 REG 패킷당 종목 등록 개수
    SCALP_VPW_WINDOW_SECONDS: int = 8  # 단기 체결 가속도 판정 시간창(초)
    SCALP_VPW_MIN_BASE: float = 95.0  # 누적 체결강도 최소 베이스
    SCALP_VPW_TARGET_DELTA: float = 0.0  # DEPRECATED: 로그 관측용만 유지, 진입 조건문에는 미사용
    SCALP_VPW_MIN_BUY_VALUE: int = 20_000  # 키움 1313 원시값 기준 WINDOW 최소 매수 체결대금
    SCALP_VPW_MIN_BUY_RATIO: float = 0.75  # WINDOW 동안 필요한 최소 매수 체결대금 비중
    SCALP_VPW_MIN_EXEC_BUY_RATIO: float = 0.56  # WINDOW 동안 필요한 최소 매수 체결량 비중
    SCALP_VPW_MIN_NET_BUY_QTY: int = 1  # WINDOW 동안 순매수 체결수량 최소 기준
    SCALP_VPW_RELAX_TAGS: tuple = ("VWAP_RECLAIM", "OPEN_RECLAIM")  # 1차 진입 민감도 완화 대상 태그
    SCALP_VPW_RELAX_MIN_BASE: float = 93.0  # 완화 태그 전용 최소 체결강도 베이스
    SCALP_VPW_RELAX_MIN_BUY_VALUE: int = 16_000  # 완화 태그 전용 WINDOW 최소 매수 체결대금
    SCALP_VPW_RELAX_MIN_BUY_RATIO: float = 0.72  # 완화 태그 전용 WINDOW 최소 매수 체결대금 비중
    SCALP_VPW_RELAX_MIN_EXEC_BUY_RATIO: float = 0.53  # 완화 태그 전용 WINDOW 최소 매수 체결량 비중
    SCALP_VPW_HISTORY_MAXLEN: int = 120  # 종목별 동적 체결강도 히스토리 최대 보관 개수
    SCALP_VPW_STRONG_ABSOLUTE: float = 115.0  # 강한 절대 체결강도 예외 통과 기준
    SCALP_VPW_STRONG_BUY_VALUE: int = 40_000  # WINDOW 강한 매수 체결대금 예외 기준
    SCALP_TARGET: float = 1.5  # 초단타 익절 1.5% (분석용 목표)
    SCALP_STOP: float = -1.5  # 초단타 완충 손절(soft stop)
    SCALP_HARD_STOP: float = -2.5  # 초단타 최종 안전장치(hard stop)
    SCALP_SOFT_STOP_MICRO_GRACE_ENABLED: bool = True  # soft_stop 휩쏘 완화 canary
    SCALP_SOFT_STOP_MICRO_GRACE_SEC: int = 20  # soft_stop 최초 터치 후 확인유예(초)
    SCALP_SOFT_STOP_MICRO_GRACE_EMERGENCY_PCT: float = -2.0  # 유예 중에도 즉시 청산하는 손실폭
    SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_ENABLED: bool = False  # 예비 파라미터: threshold 근처 1회 추가 확인유예
    SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_SEC: int = 10  # 추가 확인유예 최대 초
    SCALP_SOFT_STOP_MICRO_GRACE_EXTEND_BUFFER_PCT: float = 0.20  # soft stop 기준선 아래 추가 유예 허용폭
    SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED: bool = False  # soft_stop whipsaw 확인 canary 기본 OFF
    SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC: int = 60  # soft_stop grace 종료 후 최대 확인 시간
    SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT: float = 0.20  # soft stop 기준선 아래 허용 악화폭
    SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT: float = 0.30  # 확인 중 추가 악화 허용폭
    SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED: bool = False  # 2026-04-30 same-day v2 수집 종료: 다음 승인 전 기본 OFF
    SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT: str = ""  # env override로만 재개
    SCALP_SOFT_STOP_ABSORPTION_EXTENSION_SEC: int = 20  # orderbook absorption 확인유예(초)
    SCALP_SOFT_STOP_ABSORPTION_MIN_SCORE: int = 3  # absorption 조건 최소 충족 개수
    SCALP_SOFT_STOP_ABSORPTION_MAX_EXTENSIONS: int = 1  # 포지션당 absorption 유예 1회
    SCALP_SOFT_STOP_ABSORPTION_MIN_BUY_PRESSURE: float = 55.0
    SCALP_SOFT_STOP_ABSORPTION_MIN_TICK_ACCEL: float = 0.95
    SCALP_SOFT_STOP_ABSORPTION_MIN_MICRO_VWAP_BP: float = -5.0
    SCALP_SOFT_STOP_ABSORPTION_MAX_TOP3_DEPTH_RATIO: float = 1.35
    SCALP_SOFT_STOP_THESIS_TICK_ACCEL_MIN: float = 0.60
    SCALP_SOFT_STOP_THESIS_MICRO_VWAP_BP_MIN: float = -20.0
    SCALP_AI_MOMENTUM_DECAY_SCORE_LIMIT: int = 45  # 이 값 미만일 때만 AI 모멘텀 둔화 익절 검토
    SCALP_AI_MOMENTUM_DECAY_MIN_HOLD_SEC: int = 90  # AI 모멘텀 둔화 익절 최소 보유시간(초)
    SCALP_PRESET_HARD_STOP_PCT: float = -0.7  # SCALP_PRESET_TP 기본 손절선
    SCALP_PRESET_HARD_STOP_GRACE_SEC: int = 0  # SCALP_PRESET_TP 공통 유예시간(초)
    SCALP_PRESET_HARD_STOP_EMERGENCY_PCT: float = -1.2  # 유예 중에도 강제 청산하는 비상 손절선
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT: float = -0.7  # SCALP_BASE + fallback 전용 기본 손절선
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC: int = 35  # SCALP_BASE + fallback 전용 유예시간
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT: float = -1.2  # SCALP_BASE + fallback 비상 손절선
    SCALP_FALLBACK_ENTRY_QTY_MULTIPLIER: float = 0.70  # historical-only: fallback 경로 복기용 잔존 상수
    SCALP_LATENCY_FALLBACK_ENABLED: bool = False  # 폐기 확정: CAUTION fallback 진입 재개 금지
    SCALP_SPLIT_ENTRY_ENABLED: bool = False  # 폐기 확정: fallback scout/main split-entry 재개 금지
    SPLIT_ENTRY_REBASE_INTEGRITY_SHADOW_ENABLED: bool = False  # 폐기 정합화: split-entry runtime shadow 기본 OFF
    SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_ENABLED: bool = False  # 폐기 정합화: split-entry immediate recheck shadow 기본 OFF
    SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_WINDOW_SEC: int = 90  # historical-only: shadow 재생 분석용 기준창
    SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED: bool = True  # 2026-04-20 immediate fix: partial fill 최소 체결비율 guard on
    SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT: float = 0.20  # 기본 최소 체결비율
    SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE: float = 0.10  # strong_absolute_override 예외
    SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP: float = 0.00  # SCALP_PRESET_TP 예외(적용 제외)
    SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED: bool = True  # submitted 전 비정상 저가 지정가 차단
    SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS: int = 80  # best_bid 대비 허용 하향 괴리(bp)
    SCALPING_ENTRY_PRICE_RESOLVER_ENABLED: bool = True  # 스캘핑 기준가/제출가 분리 resolver
    SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS: int = 80  # 기준가 적용 허용 하향 괴리(bp)
    SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED: bool = True  # submitted 직전 Tier2 AI 가격결정 canary
    SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE: int = 60
    SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE: int = 80
    SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED: bool = True  # P2 저신뢰 SKIP을 OFI 완충으로 P1 방어가 demotion
    SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE: int = 90  # confidence >= 90 SKIP은 유지
    SCALPING_ENTRY_AI_PRICE_TICK_LIMIT: int = 20
    SCALPING_ENTRY_AI_PRICE_CANDLE_LIMIT: int = 20
    SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED: bool = True  # P2 entry price OFI/QI feature input
    SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED: bool = False  # 명시 manifest 기반 bucket threshold, 기본 OFF
    OFI_AI_SMOOTHING_STALE_THRESHOLD_MS: int = 700
    OFI_AI_SMOOTHING_RAW_WEIGHT: float = 0.30
    OFI_AI_SMOOTHING_BULLISH_THRESHOLD: float = 0.45
    OFI_AI_SMOOTHING_BEARISH_THRESHOLD: float = -0.45
    OFI_AI_SMOOTHING_RELEASE_THRESHOLD: float = 0.15
    OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED: int = 2
    SCALPING_ENTRY_TIMEOUT_SEC: int = 90  # 스캘핑 일반 매수 미체결 취소 대기
    SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC: int = 120  # 돌파형 스캘핑 미체결 취소 대기
    SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC: int = 600  # 눌림/예약형 스캘핑 미체결 취소 대기
    SCALPING_RESERVE_ENTRY_TIMEOUT_SEC: int = 1200  # 명시적 예약형 스캘핑 미체결 취소 대기
    SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC: int = 300  # OPEN_RECLAIM never-green 조기 정리 최소 보유시간
    SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT: float = 0.20  # OPEN_RECLAIM never-green 최대 허용 고점수익
    SCALP_OPEN_RECLAIM_NEAR_AI_EXIT_SCORE_BUFFER: int = 5  # OPEN_RECLAIM near_ai_exit 점수 여유폭
    SCALP_OPEN_RECLAIM_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC: int = 120  # OPEN_RECLAIM 양전환 이력 케이스 near_ai_exit 지속 필요시간
    SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC: int = 420  # SCANNER fallback never-green 조기 정리 최소 보유시간
    SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT: float = 0.20  # SCANNER fallback 최대 허용 고점수익
    SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SCORE_BUFFER: int = 8  # SCANNER fallback near_ai_exit 점수 여유폭
    SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SUSTAIN_SEC: int = 120  # SCANNER fallback near_ai_exit 지속 필요시간
    SCALP_SCANNER_FALLBACK_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC: int = 150  # SCANNER fallback 양전환 이력 케이스 near_ai_exit 지속 필요시간
    SCALP_LATENCY_GUARD_CANARY_ENABLED: bool = False  # 긴급 운영가드: REJECT_DANGER -> fallback canary override 비활성화
    SCALP_LATENCY_GUARD_CANARY_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # latency canary 적용 태그
    SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE: float = 85.0  # latency canary 최소 AI 점수
    SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS: int = 450  # latency canary 최대 ws_age
    SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS: int = 260  # latency canary 최대 ws_jitter
    SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO: float = 0.0100  # latency canary 최대 spread_ratio
    SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS: tuple = ()  # 비어 있으면 전체 허용, 값이 있으면 해당 danger reason만 canary 허용
    SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION: int = 700  # latency classifier CAUTION 최대 ws_age
    SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION: int = 300  # latency classifier CAUTION 최대 ws_jitter
    SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION: float = 0.005  # latency classifier CAUTION 최대 spread_ratio
    SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED: bool = False  # legacy recovery flag; CAUTION now follows normal submit after slippage
    SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE: float = 75.0  # recovery canary 최소 AI 점수
    SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS: int = 1200  # recovery canary 최대 ws_age
    SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS: int = 1500  # recovery canary 최대 ws_jitter
    SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO: float = 0.0100  # recovery canary 최대 spread_ratio
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED: bool = False  # 2026-04-29 OFF 확정: quote freshness 복합 residual canary 기본 비활성
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # composite relief 적용 태그
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MIN_SIGNAL_SCORE: float = 88.0  # 단일축 실패 후 복합축은 더 강한 신호만 허용
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_AGE_MS: int = 950  # 복합축 최대 ws_age
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_WS_JITTER_MS: int = 450  # 복합축 최대 ws_jitter
    SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_MAX_SPREAD_RATIO: float = 0.0075  # 복합축 최대 spread_ratio
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED: bool = False  # 2026-04-29 12:50 운영 override 종료
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_SIGNAL_SCORE: float = 90.0
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_STRENGTH: float = 110.0
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MIN_BUY_PRESSURE: float = 65.0
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_AGE_MS: int = 1200
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_WS_JITTER_MS: int = 500
    SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_MAX_SPREAD_RATIO: float = 0.0085
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED: bool = False  # DANGER latency hard safety blocks submit
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE: float = 75.0
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH: float = 110.0
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE: float = 50.0
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS: int = 1200
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS: int = 500
    SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO: float = 0.0085
    SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED: bool = False  # replacement 완료: spread-only relief는 parking 유지
    SCALP_LATENCY_SPREAD_RELIEF_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # spread relief 적용 태그
    SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE: float = 85.0  # spread relief 최소 AI 점수
    SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO: float = 0.0120  # spread relief 최대 허용 spread_ratio
    SCALP_LATENCY_WS_JITTER_RELIEF_CANARY_ENABLED: bool = False  # 2026-04-27 15:00 미개선 종료: ws_jitter-only residual live 축 OFF
    SCALP_LATENCY_WS_JITTER_RELIEF_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # ws_jitter relief 적용 태그
    SCALP_LATENCY_WS_JITTER_RELIEF_MIN_SIGNAL_SCORE: float = 85.0  # ws_jitter relief 최소 AI 점수
    SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_AGE_MS: int = 450  # ws_jitter relief 최대 ws_age
    SCALP_LATENCY_WS_JITTER_RELIEF_MAX_WS_JITTER_MS: int = 360  # ws_jitter relief 최대 허용 ws_jitter
    SCALP_LATENCY_WS_JITTER_RELIEF_MAX_SPREAD_RATIO: float = 0.0050  # ws_jitter relief 최대 허용 spread_ratio
    SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED: bool = False  # 2026-04-27 13:00 미개선 종료: other_danger-only residual live 축 OFF
    SCALP_LATENCY_OTHER_DANGER_RELIEF_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # other_danger relief 적용 태그
    SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE: float = 85.0  # other_danger relief 최소 AI 점수
    SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_AGE_MS: int = 400  # other_danger relief 최대 ws_age
    SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_WS_JITTER_MS: int = 80  # other_danger relief 최대 허용 ws_jitter
    SCALP_LATENCY_OTHER_DANGER_RELIEF_MAX_SPREAD_RATIO: float = 0.0080  # other_danger relief 최대 허용 spread_ratio
    SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED: bool = True  # dynamic strength 근소 미달 조건부 완화
    SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # dynamic relief 적용 태그
    SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS: tuple = (
        "below_exec_buy_ratio",
        "below_buy_ratio",
        "below_window_buy_value",
    )
    SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO: float = 0.85  # buy_value 최소 허용 비율
    SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL: float = 0.03  # buy_ratio 부족 허용폭
    SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL: float = 0.03  # exec_buy_ratio 부족 허용폭
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY: bool = False  # shadow-only hard time stop 기본 OFF
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES: tuple = (3, 5, 7)  # 공통 hard time stop shadow 후보 분(실전 미적용)
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MIN_LOSS_PCT: float = -0.7  # shadow 후보 기록 최소 손실폭
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MAX_PEAK_PCT: float = 0.20  # shadow 후보 기록 최대 고점수익(never-green 기준)
    SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_ENABLED: bool = False  # partial-only timeout shadow 기본 OFF
    SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_SEC: int = 180  # historical/replay 전용 기준
    SCALP_PARTIAL_ONLY_TIMEOUT_SHADOW_MAX_PEAK_PCT: float = 0.20  # historical/replay 전용 기준
    SCALP_TRAILING_START_PCT: float = 0.6  # 초단타 트레일링 시작 수익률
    SCALP_TRAILING_LIMIT: float = 0.5  # DEPRECATED: STRONG/WEAK로 대체됨
    MIN_SCALP_LIQUIDITY: int = 500_000_000  # 최소 호가 잔량 대금 (5억)
    MAX_SCALP_SURGE_PCT: float = 20.0  # 초단타 진입 금지 급등률 (20%)
    MAX_INTRADAY_SURGE: float = 16.0  # 당일 시가 대비 최대 급등률 (1차 완화: 16%)
    # [V3 스캘핑 동적 트레일링 전용 상수]
    SCALP_SAFE_PROFIT = 0.5            # 💡 [신규] 수수료/세금/슬리피지를 커버하는 최소 안전 마진 (이 선을 넘으면 무조건 수익 마감 모드 돌입)
    SCALP_TRAILING_LIMIT_STRONG = 0.8  # 💡 [신규] AI 점수가 75점 이상(수급 폭발)일 때 허용하는 고점 대비 눌림폭 (%)
    SCALP_TRAILING_LIMIT_WEAK = 0.4    # 💡 [신규] AI 점수가 75점 미만(수급 애매)일 때 타이트하게 끊어내는 고점 대비 눌림폭 (%)
    SCALP_PROTECT_TRAILING_SMOOTH_ENABLED: bool = True  # 보호 트레일링은 단일 tick 대신 평탄화 이탈 확인
    SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC: int = 20  # 보호 트레일링 평탄화 샘플 윈도우
    SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC: int = 8  # 최소 관측 기간
    SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES: int = 3  # 최소 샘플 수
    SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO: float = 0.67  # 버퍼 하단 이탈 샘플 비율
    SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT: float = 1.00  # 보호선 대비 노이즈 허용폭
    SCALP_PROTECT_TRAILING_EMERGENCY_PCT: float = -2.0  # 평탄화 전에도 즉시 청산할 손실폭

    # ── reversal_add ────────────────────────────────────────
    REVERSAL_ADD_ENABLED: bool = True              # 2026-04-30 canary: 역전 확인 추가매수 소형 실험
    REVERSAL_ADD_PNL_MIN: float = -0.70            # 2026-04-30 intraday override: 손실 확대 회수용 허용 손실 하한 (%)
    REVERSAL_ADD_PNL_MAX: float = -0.10            # 허용 손실 상한 (%)
    REVERSAL_ADD_MIN_HOLD_SEC: int = 20            # 최소 보유시간(초)
    REVERSAL_ADD_MAX_HOLD_SEC: int = 180           # 2026-04-30 intraday override: 회복 확인 최대 보유시간(초)
    REVERSAL_ADD_MIN_AI_SCORE: int = 60            # 실행 직전 최소 AI 점수
    REVERSAL_ADD_MIN_AI_RECOVERY_DELTA: int = 15   # AI bottom 대비 최소 회복폭
    REVERSAL_ADD_MIN_BUY_PRESSURE: float = 55.0    # 최소 매수 압도율(%)
    REVERSAL_ADD_MIN_TICK_ACCEL: float = 0.95      # 최소 틱 가속도 비율
    REVERSAL_ADD_VWAP_BP_MIN: float = -5.0         # 최소 Micro-VWAP 대비 (bp)
    REVERSAL_ADD_SIZE_RATIO: float = 0.33          # 추가매수 수량 비율 (기존 보유 대비)
    REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED: bool = True  # buy_qty*ratio가 0일 때 reversal_add 최소 1주 floor 허용
    REVERSAL_ADD_POST_EVAL_SEC: int = 25           # POST_ADD_EVAL 감시 시간(초)
    REVERSAL_ADD_SESSION_CUTOFF: str = "14:30"     # 허용 시간대 상한
    REVERSAL_ADD_BOX_RANGE_MAX_PCT: float = 0.20   # 박스 폭 허용 최대치 (%p)
    REVERSAL_ADD_STAGNATION_LOW_FLOOR_MARGIN: float = 0.05  # 저점 미갱신 허용 마진 (%p)
    SCALP_LOSS_FALLBACK_ENABLED: bool = True        # 운영 override: 손절 직전 ADM/fallback 추가매수 실전 적용
    SCALP_LOSS_FALLBACK_OBSERVE_ONLY: bool = False  # 운영 override: 후보 기록에 그치지 않고 scale-in safety 후 실행
    SCALP_LOSS_FALLBACK_ALLOWED_REASONS: tuple = (
        "reversal_add_ok",
        "holding_exit_matrix_avg_down_bias",
    )  # 손절 fallback 허용 reason
    SCALP_LOSS_FALLBACK_MIN_AI_SCORE: int = 65      # 손절 fallback 후보 최소 AI 점수
    SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED: bool = True  # soft_stop 선행 불량진입 유형 observe-only
    SCALP_BAD_ENTRY_BLOCK_MIN_HOLD_SEC: int = 60
    SCALP_BAD_ENTRY_BLOCK_MIN_LOSS_PCT: float = -0.70
    SCALP_BAD_ENTRY_BLOCK_MAX_PEAK_PROFIT_PCT: float = 0.20
    SCALP_BAD_ENTRY_BLOCK_AI_SCORE_LIMIT: int = 45
    SCALP_BAD_ENTRY_BLOCK_LOG_INTERVAL_SEC: int = 30
    SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED: bool = False  # 2026-05-04 postclose rollback: sell_order_failed/flow-defer 혼입으로 OFF
    SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED: bool = True  # canary OFF 이후 refined counterfactual 후보는 report-only로 유지
    SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC: int = 180
    SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT: float = -1.16
    SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT: float = 0.05
    SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT: int = 45
    SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX: float = 0.30

    # 💡 [신규] 코스닥 스캐너 설정
    KOSDAQ_TARGET: float = 4.0  # 코스닥은 조금 더 높게 목표 (예: 4.0%)
    KOSDAQ_STOP: float = -2.5  # 타이트한 칼손절 적용
    VPW_KOSDAQ_LIMIT: int = 115  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    HOLDING_DAYS: int = 4  # KOSPI 최대 보유 영업일
    KOSDAQ_HOLDING_DAYS: int = 3  # 코스닥 최대 보유 영업일
    MAX_SWING_GAP_UP_PCT: float = 3.0  # DEPRECATED: 전략별 갭 기준의 공통 폴백
    MAX_SWING_GAP_UP_PCT_KOSDAQ: float = 3.0  # 코스닥 스윙 갭상승 차단 기준
    MAX_SWING_GAP_UP_PCT_KOSPI: float = 3.5  # 코스피 스윙 갭상승 차단 기준 (1차 완화)

    # ==========================================
    # 🎯 추가된 스나이퍼 매매/운영 세부 설정값
    # ==========================================
    BUY_SCORE_THRESHOLD: int = 75  # AI 봇이 매수 버튼을 누르는 최소 종합 점수
    BUY_SCORE_KOSDAQ_THRESHOLD: int = 80  # AI 봇이 KOSDAQ 매수 버튼을 누르는 최소 종합 점수
    VPW_STRONG_LIMIT: int = 115  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    VPW_STRONG_KOSDAQ_LIMIT: int = 120  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    RALLY_TARGET_PCT: float = 5.0  # 신고가 돌파 시 기본 목표가 (%)
    ORDER_TIMEOUT_SEC: int = 30  # 미체결 주문 취소 대기 시간 (초)
    SCAN_INTERVAL_SEC: int = 1800  # DEPRECATED: 런타임 미사용
    MAX_WATCHING_SLOTS: int = 5  # DEPRECATED: 런타임 미사용

    # ==========================================
    # 🧪 Big-Bite 보조 확증 신호 (Scalping)
    # ==========================================
    BIG_BITE_WINDOW_MS: int = 500  # 체결 집계 시간창(ms)
    BIG_BITE_MIN_VALUE: int = 50_000_000  # 집계 체결대금 최소 기준
    BIG_BITE_IMPACT_RATIO: float = 0.30  # ask1~3 잔량 대비 소진 비율 기준
    BIG_BITE_COOLDOWN_MS: int = 1500  # 동일 묶음 중복 트리거 방지 쿨다운
    BIG_BITE_CONFIRM_MS: int = 1000  # 트리거 이후 후속 확인 시간창
    BIG_BITE_MAX_CHASE_PCT: float = 0.8  # 트리거 대비 허용 추격 폭(%)
    BIG_BITE_MIN_ASK_1_3_TOTAL: int = 8_000  # ask1~3 최소 잔량 기준 (과민반응 방지)
    BIG_BITE_MIN_VPW_AFTER_TRIGGER: int = 110  # 트리거 이후 체결강도 유지 최소치
    BIG_BITE_BOOST_SCORE: int = 5  # 확증 시 진입 점수 보수적 가산치
    BIG_BITE_ARMED_ENTRY_BONUS: int = 2  # armed 상태 가벼운 보너스(옵션)
    BIG_BITE_HARD_GATE_ENABLED: bool = False  # 특정 구간에서 Big-Bite 없으면 진입 차단
    BIG_BITE_HARD_GATE_TAGS_SCALPING = ("VCP", "BREAK", "BRK", "SHOOT", "NEXT", "SCANNER")  # 스캘핑 하드 게이트 태그
    BIG_BITE_HARD_GATE_TAGS_KOSDAQ = ()  # 코스닥 스윙 하드 게이트 태그(기본 미사용)
    BIG_BITE_HARD_GATE_TAGS_KOSPI = ()  # 코스피 스윙 하드 게이트 태그(기본 미사용)

    # ==========================================
    # 🕒 거래 시간 제어값 (KRX 거래시간 확대 대응)
    # ==========================================
    MARKET_OPEN_TIME: str = "09:00:00"
    SCALPING_EARLIEST_BUY_TIME: str = "09:03:00"
    SWING_EARLIEST_BUY_TIME: str = "09:05:00"
    SCALPING_NEW_BUY_CUTOFF: str = "15:00:00"
    SCALPING_OVERNIGHT_DECISION_TIME: str = "15:10:00"
    MARKET_CLOSE_TIME: str = "15:30:00"
    SYSTEM_SHUTDOWN_TIME: str = "20:00:00"

    # ==========================================
    # 🎯 유저권한별 기능 제한 설정값
    # ==========================================
    VIP_LIQUIDITY_THRESHOLD: int = 1_000_000_000  # keep: VIP 전용 호가 잔량 대금 기준 (10억)
    VIP_PROB_THRESHOLD: float = 0.75  # DEPRECATED: 런타임 미사용
    VIP_MAX_INVEST_RATIO: float = 0.30  # DEPRECATED: 런타임 미사용

    # ==========================================
    # 🎯 AI 엔진 공통 제어값
    # ==========================================
    AI_MAX_CONSECUTIVE_FAILURES: int = 5   # 연속 API 실패 시 AI 엔진 일시 중단 임계값
    AI_SCORE_THRESHOLD_KOSDAQ: int = 60    # KOSDAQ_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_SCORE_THRESHOLD_KOSPI: int = 60     # KOSPI_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_WATCHING_COOLDOWN: int = 90  # 신규 진입 감시(WATCHING) 재평가 간격 (초)
    AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED: bool = True  # score=50 fallback/neutral 진입은 매수보류
    AI_MAIN_BUY_RECOVERY_CANARY_ENABLED: bool = False  # same-day 교체: BUY recovery canary 기본 OFF
    AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE: int = 65  # 재평가 시작 점수
    AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE: int = 79  # 재평가 종료 점수
    AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE: int = 75  # BUY 승격 최소 점수
    AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE: float = 65.0  # 최소 매수 압도율(%)
    AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL: float = 1.20  # 최소 틱 가속 비율
    AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP: float = 0.0  # 최소 micro VWAP bp
    AI_WAIT6579_PROBE_CANARY_ENABLED: bool = False  # 2026-04-27: soft_stop live canary 관찰 중 entry probe OFF
    AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW: int = 50_000  # probe 최대 예산
    AI_WAIT6579_PROBE_CANARY_MIN_QTY: int = 1  # probe 최소 수량
    AI_WAIT6579_PROBE_CANARY_MAX_QTY: int = 1  # probe 최대 수량. 0 이하는 수량 cap 없음
    AI_SCORE65_74_RECOVERY_PROBE_ENABLED: bool = False  # 2026-05-06: score60~74 전용 신규 canary 기본 OFF
    AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE: int = 60
    AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE: int = 74
    AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE: float = 65.0
    AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL: float = 1.20
    AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP: float = 0.0
    AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION: str = "runtime_default"
    AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE: str = "runtime_default"
    SCALPING_PROMPT_SPLIT_ENABLED: bool = True  # WATCHING/HOLDING 프롬프트 분리 on/off 롤백 토글
    ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN: int = 60 * 20  # 게이트키퍼 '눌림 대기' 재평가 쿨다운
    ML_GATEKEEPER_REJECT_COOLDOWN: int = 60 * 60 * 2  # 게이트키퍼 '전량 회피' 계열 쿨다운
    ML_GATEKEEPER_NEUTRAL_COOLDOWN: int = 60 * 30  # 게이트키퍼 중립/애매 응답 재평가 쿨다운
    ML_GATEKEEPER_ERROR_COOLDOWN: int = 60 * 10  # 게이트키퍼 오류 재시도 쿨다운
    # [AI 보유 종목 감시 쿨타임 설정 - 비용 절감형]
    AI_HOLDING_MIN_COOLDOWN: int = 45          # 일반 보유 감시 최소 재평가 간격
    AI_HOLDING_MAX_COOLDOWN: int = 180         # 일반 횡보 구간 최대 재평가 간격
    AI_HOLDING_CRITICAL_MIN_COOLDOWN: int = 20 # 익절/손절 임박 구간 최소 재평가 간격
    AI_HOLDING_CRITICAL_COOLDOWN: int = 45     # 익절/손절 임박 구간 최대 재평가 간격
    AI_WAIT_DROP_COOLDOWN: int = 300           # 💡 ai score 75점 이하 대기시간 300초

    # ==========================================
    # 🎯 AI 엔진 제어값 (OpenAI)
    # ==========================================
    GPT_FAST_MODEL = "gpt-5-nano"
    GPT_DEEP_MODEL = "gpt-5.4"
    GPT_REPORT_MODEL = "gpt-5.4-mini"
    GPT_THRESHOLD_CORRECTION_MODEL: str = "gpt-5.5"
    GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS: tuple = ("gpt-5.4", "gpt-5.4-mini")
    GPT_ENABLE_SCALPING_DEEP_RECHECK: bool = False
    GPT_ENGINE_MIN_INTERVAL: float = 0.5 # OpenAI 서버에 쏘는 최소 간격 (초 단위, 0.5초 = 500ms)
    OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED: bool = False  # JSON path에만 deterministic temperature 적용
    OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED: bool = False  # endpoint별 OpenAI structured output schema 적용 토글
    OPENAI_TRANSPORT_MODE: str = "http"  # http | responses_ws
    OPENAI_RESPONSES_WS_ENABLED: bool = False  # Responses WebSocket shadow-first 토글
    OPENAI_RESPONSES_WS_POOL_SIZE: int = 2  # persistent Responses WebSocket worker 수
    OPENAI_RESPONSES_WS_TIMEOUT_MS: int = 700  # hot path 판단 timeout
    OPENAI_SCANNER_REPORT_TIMEOUT_MS: int = 15000  # source-only morning scanner report timeout
    OPENAI_OVERNIGHT_TIMEOUT_MS: int = 12000  # source-only overnight_v1 batch 판단 timeout
    OPENAI_RESPONSES_MAX_OUTPUT_TOKENS: int = 512  # OpenAI live JSON 응답 토큰 상한
    OPENAI_REASONING_EFFORT: str = "auto"  # hot path 추론 effort
    OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED: bool = True  # deadline 초과 응답 discard
    OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED: bool = True  # buy-side hot path timeout/parse failure 시 reject fallback
    OPENAI_SCALPING_COMPACT_INPUT_ENABLED: bool = True  # OpenAI live route hot path 입력 compact JSON 사용
    OPENAI_PREVIOUS_RESPONSE_ID_ENABLED: bool = False  # phase1: stateless 유지
    OPENAI_DUAL_PERSONA_ENABLED: bool = False  # Plan Rebase: AI 엔진 A/B/shadow 비교는 기본 튜닝 로직 정렬 이후 재개
    OPENAI_DUAL_PERSONA_SHADOW_MODE: bool = False
    OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER: bool = False  # 장중 긴급 완화: Gatekeeper dual-persona shadow 일시 비활성화
    OPENAI_DUAL_PERSONA_APPLY_OVERNIGHT: bool = True
    OPENAI_DUAL_PERSONA_WORKERS: int = 2
    OPENAI_DUAL_PERSONA_MAX_EXTRA_MS: int = 2500
    OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_SAMPLES: int = 30
    OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_OVERRIDE_RATIO: float = 3.0
    OPENAI_DUAL_PERSONA_GATEKEEPER_MAX_EVAL_MS_P95: int = 5000
    OPENAI_DUAL_PERSONA_GATEKEEPER_G_WEIGHT: float = 0.50
    OPENAI_DUAL_PERSONA_GATEKEEPER_A_WEIGHT: float = 0.20
    OPENAI_DUAL_PERSONA_GATEKEEPER_C_WEIGHT: float = 0.30
    OPENAI_DUAL_PERSONA_OVERNIGHT_G_WEIGHT: float = 0.45
    OPENAI_DUAL_PERSONA_OVERNIGHT_A_WEIGHT: float = 0.10
    OPENAI_DUAL_PERSONA_OVERNIGHT_C_WEIGHT: float = 0.45

    # ==========================================
    # 📉 post-sell 피드백 설정
    # ==========================================
    POST_SELL_FEEDBACK_ENABLED: bool = True
    POST_SELL_FEEDBACK_EVAL_ENABLED: bool = True
    POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT: float = 0.8
    POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT: float = 0.3
    POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT: float = -0.6
    POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT: float = -0.2
    POST_SELL_WS_RETAIN_MINUTES: int = 0  # 0이면 매도 이후 WS 유지 비활성(MVP 기본값)

    # ==========================================
    # ⚡ 성능 최적화 캐시 설정
    # ==========================================
    KIWOOM_TICK_CACHE_TTL_SEC: float = 1.0  # 최근 틱 체결 조회 캐시
    KIWOOM_MINUTE_CACHE_TTL_SEC: float = 3.0  # 최근 1분봉 조회 캐시
    KIWOOM_STRENGTH_CACHE_TTL_SEC: float = 1.0  # 체결강도 패킷 캐시
    KIWOOM_DAILY_CACHE_TTL_SEC: float = 30.0  # 일봉/이평 계산용 캐시
    KIWOOM_INVESTOR_CACHE_TTL_SEC: float = 60.0  # 외인/기관 수급 캐시
    KIWOOM_PROGRAM_CACHE_TTL_SEC: float = 20.0  # 프로그램 fallback 캐시
    AI_ANALYZE_RESULT_CACHE_TTL_SEC: float = 5.0  # 스캘핑/보유 AI 재평가 결과 캐시
    AI_HOLDING_RESULT_CACHE_TTL_SEC: float = 60.0  # 보유 AI 재평가 결과 캐시
    AI_GATEKEEPER_RESULT_CACHE_TTL_SEC: float = 30.0  # 스윙 Gatekeeper 결과 캐시
    GATEKEEPER_SNAPSHOT_DEDUP_TTL_SEC: float = 10.0  # 동일 Gatekeeper 스냅샷 중복 기록 억제
    AI_HOLDING_FAST_REUSE_CRITICAL_SEC: float = 5.0  # 위기구간 동일 시장상태 재평가 생략
    AI_HOLDING_FAST_REUSE_NORMAL_SEC: float = 12.0  # 일반구간 동일 시장상태 재평가 생략
    AI_GATEKEEPER_FAST_REUSE_SEC: float = 30.0  # 동일 감시 스냅샷 재평가 생략
    AI_HOLDING_FAST_REUSE_MAX_WS_AGE_SEC: float = 1.5  # 보유 AI fast reuse 허용 최대 WS 나이
    AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC: float = 2.0  # Gatekeeper fast reuse 허용 최대 WS 나이
    SCALP_ENTRY_ADM_ADVISORY_ENABLED: bool = True  # 운영 override: 스캘핑 entry ADM prompt advisory 기본 ON
    SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED: bool = False  # context-only 기본값: 명시적 운영 override에서만 entry AI action 보정
    SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED: bool = True  # joined sample 부족 시 stale/chase/weak-momentum 가설 provenance
    SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED: bool = False  # hypothesis fallback의 직접 action 보정은 명시 override에서만 허용
    SCALP_ENTRY_ADM_NEGATIVE_EV_BLOCK_ENABLED: bool = True  # BUY bucket이라도 source-quality EV<기준이면 즉시 진입 대기
    SCALP_ENTRY_ADM_NEGATIVE_EV_FORCE_WAIT_THRESHOLD_PCT: float = 0.0
    SCALP_ENTRY_ADM_MIN_BUCKET_SAMPLE: int = 20
    SCALP_ENTRY_ADM_MIN_JOINED_SAMPLE: int = 10
    LIFECYCLE_DECISION_MATRIX_ENABLED: bool = False
    LIFECYCLE_DECISION_MATRIX_POLICY_FILE: str = ""
    LIFECYCLE_DECISION_MATRIX_POLICY_VERSION: str = ""
    LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED: bool = False
    LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY: int = 3
    LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE: float = 0.60
    LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED: bool = False
    LIFECYCLE_AI_CONTEXT_ENABLED: bool = False
    LIFECYCLE_AI_CONTEXT_FILE: str = ""
    LIFECYCLE_AI_CONTEXT_VERSION: str = ""
    LIFECYCLE_BUCKET_DISCOVERY_ENABLED: bool = False
    LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE: str = ""
    LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION: str = ""
    LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED: bool = False
    HOLDING_EXIT_MATRIX_ADVISORY_ENABLED: bool = True  # 운영 override: holding/exit matrix prompt advisory 기본 ON
    HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED: bool = False  # context-only 기본값: 명시적 운영 override에서만 HOLD/EXIT action 보정
    HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED: bool = True
    HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED: bool = False
    HOLDING_EXIT_MATRIX_HOLD_TO_EXIT_ENABLED: bool = True
    HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED: bool = False
    HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT: float = -1.20
    HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT: float = -0.10
    HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE: int = 65
    HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_HELD_SEC: int = 10
    HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_HELD_SEC: int = 240
    HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT: float = 0.80
    HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE: int = 75
    HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT: float = 0.35
    HOLDING_FLOW_OVERRIDE_ENABLED: bool = True  # 운영 override: 단일 보유/청산 점수 대신 흐름 판단으로 최종 청산
    HOLDING_FLOW_OVERRIDE_WORSEN_PCT: float = 0.80  # 최초 후보 대비 추가 악화 허용폭(%p)
    HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC: int = 90  # flow HOLD/TRIM 보류 최대 시간
    HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED: bool = True  # holding_flow_override 내부 OFI 완충 postprocessor
    HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT: float = 0.30  # flow HOLD/TRIM 중 bearish 확정 최소 추가악화(%p)
    HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC: int = 30
    HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC: int = 90
    HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT: float = 0.35
    HOLDING_FLOW_REVIEW_TICK_LIMIT: int = 30
    HOLDING_FLOW_REVIEW_CANDLE_LIMIT: int = 60
    HOLDING_FLOW_REVIEW_MAX_WS_AGE_SEC: float = 3.0

    # ==========================================
    # 📝 로그 운영 설정
    # ==========================================
    MODULE_LOG_MAX_BYTES: int = 20 * 1024 * 1024  # 파일별 info/error 로그 최대 20MB
    MODULE_LOG_BACKUP_COUNT: int = 10  # 파일별 순환 보관 개수
    LOG_RETENTION_DAYS: int = 14  # 오래된 로그 자동 삭제 기준
    BOT_HISTORY_BACKUP_COUNT: int = 7  # 콘솔 히스토리 일별 보관 개수
    PIPELINE_EVENT_JSONL_ENABLED: bool = True
    PIPELINE_EVENT_SCHEMA_VERSION: int = 1
    PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED: bool = False
    PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST: tuple = (
        "order_bundle_submitted",
        "entry_order_cancel_requested",
        "entry_order_cancel_confirmed",
        "entry_order_cancel_failed",
        "partial_fill_ratio_below_min_exit_ordered",
        "partial_fill_ratio_below_min_exit_failed",
        "buy_signal_telegram_enqueue_failed",
        "sell_order_sent",
        "sell_order_failed",
        "sell_order_rejected",
        "swing_real_order_submitted",
        "swing_real_order_failed",
        "swing_scale_in_real_canary_order_submitted",
        "swing_scale_in_real_canary_order_failed",
    )
    WATCHING_STATE_DEBUG_LOG_ENABLED: bool = False

    # ==========================================
    # 시스템 에러 탐지 설정
    # ==========================================
    ERROR_DETECTOR_ENABLED: bool = True
    ERROR_DETECTOR_DAEMON_INTERVAL_SEC: int = 60
    ERROR_DETECTOR_PROCESS_MAIN_LOOP_TIMEOUT_SEC: int = 15
    ERROR_DETECTOR_PROCESS_THREAD_TIMEOUT_SEC: int = 7200
    ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC: int = 30
    ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED: bool = True
    ERROR_DETECTOR_BOT_EXPECTED_START_HHMM: str = "07:40"
    ERROR_DETECTOR_BOT_EXPECTED_END_HHMM: str = "22:55"
    ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC: int = 180
    ERROR_DETECTOR_LOG_BURST_THRESHOLD: int = 4
    ERROR_DETECTOR_LOG_SCAN_MAX_LINES: int = 2000
    ERROR_DETECTOR_CPU_BUSY_MAX_PCT: float = 95.0
    ERROR_DETECTOR_MEM_AVAILABLE_MIN_MB: float = 500.0
    ERROR_DETECTOR_DISK_FREE_MIN_MB: float = 2048.0
    ERROR_DETECTOR_SWAP_USED_MAX_PCT: float = 80.0
    ERROR_DETECTOR_LOADAVG_15M_MAX: float = 8.0
    ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC: int = 600
    ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED: bool = True
    ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC: int = 3600
    ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED: bool = True


def _env_int(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(str(raw).strip())
    except Exception:
        return None


def _env_float(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(str(raw).strip())
    except Exception:
        return None


def _env_bool(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return None
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_str(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = str(raw).strip()
    return value or None


def _env_csv_tuple(name: str) -> tuple | None:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return None
    parts = tuple(part.strip() for part in str(raw).split(",") if part.strip())
    return parts


def _build_trading_rules() -> TradingConfig:
    config = TradingConfig()
    latency_profile = str(os.getenv("KORSTOCKSCAN_LATENCY_CANARY_PROFILE", "") or "").strip().lower()
    if latency_profile == "remote_v2":
        config = replace(
            config,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=400,
        )

    env_ws_jitter = _env_int("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS")
    env_ws_age = _env_int("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS")
    env_spread_ratio = _env_float("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO")
    env_allowed_danger_reasons = _env_csv_tuple("KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS")
    env_entry_latency_max_ws_age_caution = _env_int(
        "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION"
    )
    env_entry_latency_max_ws_jitter_caution = _env_int(
        "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION"
    )
    env_entry_latency_max_spread_caution = _env_float(
        "KORSTOCKSCAN_SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION"
    )
    env_latency_submit_recovery_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED"
    )
    env_latency_submit_recovery_min_signal = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE"
    )
    env_latency_submit_recovery_max_ws_age = _env_int(
        "KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS"
    )
    env_latency_submit_recovery_max_ws_jitter = _env_int(
        "KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS"
    )
    env_latency_submit_recovery_max_spread = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO"
    )
    env_spread_relief_enabled = _env_bool("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED")
    env_spread_relief_tags = _env_csv_tuple("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_TAGS")
    env_spread_relief_min_signal = _env_float("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE")
    env_spread_relief_max_spread = _env_float("KORSTOCKSCAN_SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO")
    env_mechanical_momentum_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED"
    )
    env_mechanical_momentum_tags = _env_csv_tuple(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS"
    )
    env_mechanical_momentum_max_signal = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE"
    )
    env_mechanical_momentum_min_strength = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH"
    )
    env_mechanical_momentum_min_buy_pressure = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE"
    )
    env_mechanical_momentum_max_ws_age = _env_int(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS"
    )
    env_mechanical_momentum_max_ws_jitter = _env_int(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS"
    )
    env_mechanical_momentum_max_spread = _env_float(
        "KORSTOCKSCAN_SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO"
    )
    if (
        env_ws_jitter is not None
        or env_ws_age is not None
        or env_spread_ratio is not None
        or env_allowed_danger_reasons is not None
        or env_entry_latency_max_ws_age_caution is not None
        or env_entry_latency_max_ws_jitter_caution is not None
        or env_entry_latency_max_spread_caution is not None
        or env_latency_submit_recovery_enabled is not None
        or env_latency_submit_recovery_min_signal is not None
        or env_latency_submit_recovery_max_ws_age is not None
        or env_latency_submit_recovery_max_ws_jitter is not None
        or env_latency_submit_recovery_max_spread is not None
        or env_spread_relief_enabled is not None
        or env_spread_relief_tags is not None
        or env_spread_relief_min_signal is not None
        or env_spread_relief_max_spread is not None
        or env_mechanical_momentum_enabled is not None
        or env_mechanical_momentum_tags is not None
        or env_mechanical_momentum_max_signal is not None
        or env_mechanical_momentum_min_strength is not None
        or env_mechanical_momentum_min_buy_pressure is not None
        or env_mechanical_momentum_max_ws_age is not None
        or env_mechanical_momentum_max_ws_jitter is not None
        or env_mechanical_momentum_max_spread is not None
    ):
        config = replace(
            config,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS=env_ws_jitter
            if env_ws_jitter is not None
            else config.SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS,
            SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS=env_ws_age
            if env_ws_age is not None
            else config.SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS,
            SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO=env_spread_ratio
            if env_spread_ratio is not None
            else config.SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO,
            SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS=env_allowed_danger_reasons
            if env_allowed_danger_reasons is not None
            else config.SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS,
            SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION=env_entry_latency_max_ws_age_caution
            if env_entry_latency_max_ws_age_caution is not None
            else config.SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION,
            SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION=env_entry_latency_max_ws_jitter_caution
            if env_entry_latency_max_ws_jitter_caution is not None
            else config.SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION,
            SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION=env_entry_latency_max_spread_caution
            if env_entry_latency_max_spread_caution is not None
            else config.SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION,
            SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED=env_latency_submit_recovery_enabled
            if env_latency_submit_recovery_enabled is not None
            else config.SCALP_LATENCY_SUBMIT_RECOVERY_CANARY_ENABLED,
            SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE=env_latency_submit_recovery_min_signal
            if env_latency_submit_recovery_min_signal is not None
            else config.SCALP_LATENCY_SUBMIT_RECOVERY_MIN_SIGNAL_SCORE,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS=env_latency_submit_recovery_max_ws_age
            if env_latency_submit_recovery_max_ws_age is not None
            else config.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_AGE_MS,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS=env_latency_submit_recovery_max_ws_jitter
            if env_latency_submit_recovery_max_ws_jitter is not None
            else config.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_WS_JITTER_MS,
            SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO=env_latency_submit_recovery_max_spread
            if env_latency_submit_recovery_max_spread is not None
            else config.SCALP_LATENCY_SUBMIT_RECOVERY_MAX_SPREAD_RATIO,
            SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED=env_spread_relief_enabled
            if env_spread_relief_enabled is not None
            else config.SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED,
            SCALP_LATENCY_SPREAD_RELIEF_TAGS=env_spread_relief_tags
            if env_spread_relief_tags is not None
            else config.SCALP_LATENCY_SPREAD_RELIEF_TAGS,
            SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE=env_spread_relief_min_signal
            if env_spread_relief_min_signal is not None
            else config.SCALP_LATENCY_SPREAD_RELIEF_MIN_SIGNAL_SCORE,
            SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO=env_spread_relief_max_spread
            if env_spread_relief_max_spread is not None
            else config.SCALP_LATENCY_SPREAD_RELIEF_MAX_SPREAD_RATIO,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=env_mechanical_momentum_enabled
            if env_mechanical_momentum_enabled is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS=env_mechanical_momentum_tags
            if env_mechanical_momentum_tags is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_TAGS,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE=env_mechanical_momentum_max_signal
            if env_mechanical_momentum_max_signal is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SIGNAL_SCORE,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH=env_mechanical_momentum_min_strength
            if env_mechanical_momentum_min_strength is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_STRENGTH,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE=env_mechanical_momentum_min_buy_pressure
            if env_mechanical_momentum_min_buy_pressure is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MIN_BUY_PRESSURE,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS=env_mechanical_momentum_max_ws_age
            if env_mechanical_momentum_max_ws_age is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_AGE_MS,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS=env_mechanical_momentum_max_ws_jitter
            if env_mechanical_momentum_max_ws_jitter is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_WS_JITTER_MS,
            SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO=env_mechanical_momentum_max_spread
            if env_mechanical_momentum_max_spread is not None
            else config.SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_MAX_SPREAD_RATIO,
        )

    env_main_buy_recovery_enabled = _env_bool("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_ENABLED")
    env_main_buy_recovery_min = _env_int("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE")
    env_main_buy_recovery_max = _env_int("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE")
    env_main_buy_recovery_promote = _env_int("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE")
    env_main_buy_recovery_min_pressure = _env_float("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE")
    env_main_buy_recovery_min_accel = _env_float("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL")
    env_main_buy_recovery_min_vwap_bp = _env_float("KORSTOCKSCAN_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP")
    env_wait6579_probe_enabled = _env_bool("KORSTOCKSCAN_WAIT6579_PROBE_CANARY_ENABLED")
    env_wait6579_probe_max_budget = _env_int("KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW")
    env_wait6579_probe_min_qty = _env_int("KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MIN_QTY")
    env_wait6579_probe_max_qty = _env_int("KORSTOCKSCAN_WAIT6579_PROBE_CANARY_MAX_QTY")
    env_score6574_probe_enabled = _env_bool("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED")
    env_score6574_probe_min = _env_int("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_SCORE")
    env_score6574_probe_max = _env_int("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MAX_SCORE")
    env_score6574_probe_min_pressure = _env_float("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE")
    env_score6574_probe_min_accel = _env_float("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL")
    env_score6574_probe_min_vwap_bp = _env_float("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP")
    env_score6574_probe_threshold_version = _env_str("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION")
    env_score6574_probe_calibration_state = _env_str("KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE")
    env_scalping_prompt_split_enabled = _env_bool("KORSTOCKSCAN_SCALPING_PROMPT_SPLIT_ENABLED")
    env_ai_watching_cooldown = _env_int("KORSTOCKSCAN_AI_WATCHING_COOLDOWN")
    env_ai_holding_min_cooldown = _env_int("KORSTOCKSCAN_AI_HOLDING_MIN_COOLDOWN")
    env_ai_holding_max_cooldown = _env_int("KORSTOCKSCAN_AI_HOLDING_MAX_COOLDOWN")
    env_ai_holding_critical_min_cooldown = _env_int("KORSTOCKSCAN_AI_HOLDING_CRITICAL_MIN_COOLDOWN")
    env_ai_holding_critical_cooldown = _env_int("KORSTOCKSCAN_AI_HOLDING_CRITICAL_COOLDOWN")
    env_ai_score_50_buy_hold = _env_bool("KORSTOCKSCAN_AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED")
    if (
        env_main_buy_recovery_enabled is not None
        or env_main_buy_recovery_min is not None
        or env_main_buy_recovery_max is not None
        or env_main_buy_recovery_promote is not None
        or env_main_buy_recovery_min_pressure is not None
        or env_main_buy_recovery_min_accel is not None
        or env_main_buy_recovery_min_vwap_bp is not None
        or env_wait6579_probe_enabled is not None
        or env_wait6579_probe_max_budget is not None
        or env_wait6579_probe_min_qty is not None
        or env_wait6579_probe_max_qty is not None
        or env_score6574_probe_enabled is not None
        or env_score6574_probe_min is not None
        or env_score6574_probe_max is not None
        or env_score6574_probe_min_pressure is not None
        or env_score6574_probe_min_accel is not None
        or env_score6574_probe_min_vwap_bp is not None
        or env_score6574_probe_threshold_version is not None
        or env_score6574_probe_calibration_state is not None
        or env_scalping_prompt_split_enabled is not None
        or env_ai_watching_cooldown is not None
        or env_ai_holding_min_cooldown is not None
        or env_ai_holding_max_cooldown is not None
        or env_ai_holding_critical_min_cooldown is not None
        or env_ai_holding_critical_cooldown is not None
        or env_ai_score_50_buy_hold is not None
    ):
        config = replace(
            config,
            AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=env_main_buy_recovery_enabled
            if env_main_buy_recovery_enabled is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_ENABLED,
            AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE=env_main_buy_recovery_min
            if env_main_buy_recovery_min is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_MIN_SCORE,
            AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE=env_main_buy_recovery_max
            if env_main_buy_recovery_max is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_MAX_SCORE,
            AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE=env_main_buy_recovery_promote
            if env_main_buy_recovery_promote is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE,
            AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE=env_main_buy_recovery_min_pressure
            if env_main_buy_recovery_min_pressure is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_MIN_BUY_PRESSURE,
            AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL=env_main_buy_recovery_min_accel
            if env_main_buy_recovery_min_accel is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_MIN_TICK_ACCEL,
            AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP=env_main_buy_recovery_min_vwap_bp
            if env_main_buy_recovery_min_vwap_bp is not None
            else config.AI_MAIN_BUY_RECOVERY_CANARY_MIN_MICRO_VWAP_BP,
            AI_WAIT6579_PROBE_CANARY_ENABLED=env_wait6579_probe_enabled
            if env_wait6579_probe_enabled is not None
            else config.AI_WAIT6579_PROBE_CANARY_ENABLED,
            AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW=env_wait6579_probe_max_budget
            if env_wait6579_probe_max_budget is not None
            else config.AI_WAIT6579_PROBE_CANARY_MAX_BUDGET_KRW,
            AI_WAIT6579_PROBE_CANARY_MIN_QTY=env_wait6579_probe_min_qty
            if env_wait6579_probe_min_qty is not None
            else config.AI_WAIT6579_PROBE_CANARY_MIN_QTY,
            AI_WAIT6579_PROBE_CANARY_MAX_QTY=env_wait6579_probe_max_qty
            if env_wait6579_probe_max_qty is not None
            else config.AI_WAIT6579_PROBE_CANARY_MAX_QTY,
            AI_SCORE65_74_RECOVERY_PROBE_ENABLED=env_score6574_probe_enabled
            if env_score6574_probe_enabled is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_ENABLED,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE=env_score6574_probe_min
            if env_score6574_probe_min is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_MIN_SCORE,
            AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE=env_score6574_probe_max
            if env_score6574_probe_max is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_MAX_SCORE,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE=env_score6574_probe_min_pressure
            if env_score6574_probe_min_pressure is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_MIN_BUY_PRESSURE,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL=env_score6574_probe_min_accel
            if env_score6574_probe_min_accel is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_MIN_TICK_ACCEL,
            AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP=env_score6574_probe_min_vwap_bp
            if env_score6574_probe_min_vwap_bp is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_MIN_MICRO_VWAP_BP,
            AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION=env_score6574_probe_threshold_version
            if env_score6574_probe_threshold_version is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_THRESHOLD_VERSION,
            AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE=env_score6574_probe_calibration_state
            if env_score6574_probe_calibration_state is not None
            else config.AI_SCORE65_74_RECOVERY_PROBE_CALIBRATION_STATE,
            SCALPING_PROMPT_SPLIT_ENABLED=env_scalping_prompt_split_enabled
            if env_scalping_prompt_split_enabled is not None
            else config.SCALPING_PROMPT_SPLIT_ENABLED,
            AI_WATCHING_COOLDOWN=env_ai_watching_cooldown
            if env_ai_watching_cooldown is not None
            else config.AI_WATCHING_COOLDOWN,
            AI_HOLDING_MIN_COOLDOWN=env_ai_holding_min_cooldown
            if env_ai_holding_min_cooldown is not None
            else config.AI_HOLDING_MIN_COOLDOWN,
            AI_HOLDING_MAX_COOLDOWN=env_ai_holding_max_cooldown
            if env_ai_holding_max_cooldown is not None
            else config.AI_HOLDING_MAX_COOLDOWN,
            AI_HOLDING_CRITICAL_MIN_COOLDOWN=env_ai_holding_critical_min_cooldown
            if env_ai_holding_critical_min_cooldown is not None
            else config.AI_HOLDING_CRITICAL_MIN_COOLDOWN,
            AI_HOLDING_CRITICAL_COOLDOWN=env_ai_holding_critical_cooldown
            if env_ai_holding_critical_cooldown is not None
            else config.AI_HOLDING_CRITICAL_COOLDOWN,
            AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=env_ai_score_50_buy_hold
            if env_ai_score_50_buy_hold is not None
            else config.AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED,
        )

    env_dynamic_strength_enabled = _env_bool("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED")
    if env_dynamic_strength_enabled is None:
        env_dynamic_strength_enabled = _env_bool("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED")
    env_dynamic_strength_tags = _env_csv_tuple("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS")
    if env_dynamic_strength_tags is None:
        env_dynamic_strength_tags = _env_csv_tuple("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_TAGS")
    env_dynamic_strength_reasons = _env_csv_tuple("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS")
    if env_dynamic_strength_reasons is None:
        env_dynamic_strength_reasons = _env_csv_tuple("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_ALLOWED_REASONS")
    env_dynamic_strength_min_buy_value_ratio = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO")
    if env_dynamic_strength_min_buy_value_ratio is None:
        env_dynamic_strength_min_buy_value_ratio = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_MIN_BUY_VALUE_RATIO")
    env_dynamic_strength_buy_ratio_tol = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL")
    if env_dynamic_strength_buy_ratio_tol is None:
        env_dynamic_strength_buy_ratio_tol = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_BUY_RATIO_TOL")
    env_dynamic_strength_exec_buy_ratio_tol = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL")
    if env_dynamic_strength_exec_buy_ratio_tol is None:
        env_dynamic_strength_exec_buy_ratio_tol = _env_float("KORSTOCKSCAN_SCALP_DYNAMIC_STRENGTH_CANARY_EXEC_BUY_RATIO_TOL")
    env_pre_ai_soft_gate_enabled = _env_bool("KORSTOCKSCAN_SCALP_PRE_AI_SOFT_GATE_ENABLED")
    env_pre_ai_source_quality_block_enabled = _env_bool("KORSTOCKSCAN_SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED")
    env_pre_ai_max_ws_age_sec = _env_float("KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC")
    env_pre_ai_extreme_sell_buy_ratio = _env_float("KORSTOCKSCAN_SCALP_PRE_AI_EXTREME_SELL_BUY_RATIO_MAX")
    env_pre_ai_extreme_sell_exec_buy_ratio = _env_float(
        "KORSTOCKSCAN_SCALP_PRE_AI_EXTREME_SELL_EXEC_BUY_RATIO_MAX"
    )
    env_overbought_pullback_guard_enabled = _env_bool("KORSTOCKSCAN_SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED")
    env_overbought_pullback_min_distance = _env_float("KORSTOCKSCAN_SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT")
    env_overbought_rebreak_min_strength = _env_float("KORSTOCKSCAN_SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH")
    env_overbought_rebreak_min_buy_pressure = _env_float("KORSTOCKSCAN_SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE")
    env_liquidity_pre_submit_guard_enabled = _env_bool("KORSTOCKSCAN_SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED")
    env_partial_fill_enabled = _env_bool("KORSTOCKSCAN_SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED")
    if env_partial_fill_enabled is None:
        env_partial_fill_enabled = _env_bool("KORSTOCKSCAN_SCALP_PARTIAL_FILL_RATIO_CANARY_ENABLED")
    env_partial_fill_min_default = _env_float("KORSTOCKSCAN_SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT")
    env_partial_fill_min_strong = _env_float("KORSTOCKSCAN_SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE")
    env_partial_fill_min_preset = _env_float("KORSTOCKSCAN_SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP")
    env_pre_submit_price_guard_enabled = _env_bool("KORSTOCKSCAN_SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED")
    env_pre_submit_max_below_bid_bps = _env_int("KORSTOCKSCAN_SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS")
    env_entry_price_resolver_enabled = _env_bool("KORSTOCKSCAN_SCALPING_ENTRY_PRICE_RESOLVER_ENABLED")
    env_entry_price_resolver_max_below_bid_bps = _env_int(
        "KORSTOCKSCAN_SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS"
    )
    env_entry_ai_price_enabled = _env_bool("KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED")
    env_entry_ai_price_min_confidence = _env_int("KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE")
    env_entry_ai_price_skip_min_confidence = _env_int("KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE")
    env_entry_ai_price_ofi_skip_demotion_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED"
    )
    env_entry_ai_price_ofi_skip_demotion_max_confidence = _env_int(
        "KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE"
    )
    env_entry_ai_price_tick_limit = _env_int("KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_TICK_LIMIT")
    env_entry_ai_price_candle_limit = _env_int("KORSTOCKSCAN_SCALPING_ENTRY_AI_PRICE_CANDLE_LIMIT")
    env_entry_price_orderbook_micro_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED"
    )
    env_entry_price_orderbook_micro_bucket_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED"
    )
    env_ofi_ai_smoothing_stale_threshold_ms = _env_int("KORSTOCKSCAN_OFI_AI_SMOOTHING_STALE_THRESHOLD_MS")
    env_ofi_ai_smoothing_raw_weight = _env_float("KORSTOCKSCAN_OFI_AI_SMOOTHING_RAW_WEIGHT")
    env_ofi_ai_smoothing_bullish_threshold = _env_float("KORSTOCKSCAN_OFI_AI_SMOOTHING_BULLISH_THRESHOLD")
    env_ofi_ai_smoothing_bearish_threshold = _env_float("KORSTOCKSCAN_OFI_AI_SMOOTHING_BEARISH_THRESHOLD")
    env_ofi_ai_smoothing_release_threshold = _env_float("KORSTOCKSCAN_OFI_AI_SMOOTHING_RELEASE_THRESHOLD")
    env_ofi_ai_smoothing_persistence_required = _env_int("KORSTOCKSCAN_OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED")
    env_scalping_entry_timeout = _env_int("KORSTOCKSCAN_SCALPING_ENTRY_TIMEOUT_SEC")
    env_scalping_breakout_entry_timeout = _env_int("KORSTOCKSCAN_SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC")
    env_scalping_pullback_entry_timeout = _env_int("KORSTOCKSCAN_SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC")
    env_scalping_reserve_entry_timeout = _env_int("KORSTOCKSCAN_SCALPING_RESERVE_ENTRY_TIMEOUT_SEC")
    env_reversal_add_enabled = _env_bool("KORSTOCKSCAN_REVERSAL_ADD_ENABLED")
    env_reversal_add_min_ai_score = _env_int("KORSTOCKSCAN_REVERSAL_ADD_MIN_AI_SCORE")
    env_reversal_add_min_buy_pressure = _env_float("KORSTOCKSCAN_REVERSAL_ADD_MIN_BUY_PRESSURE")
    env_reversal_add_min_tick_accel = _env_float("KORSTOCKSCAN_REVERSAL_ADD_MIN_TICK_ACCEL")
    env_reversal_add_size_ratio = _env_float("KORSTOCKSCAN_REVERSAL_ADD_SIZE_RATIO")
    env_reversal_add_min_qty_floor_enabled = _env_bool("KORSTOCKSCAN_REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED")
    env_bad_entry_observe_enabled = _env_bool("KORSTOCKSCAN_SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED")
    env_bad_entry_refined_enabled = _env_bool("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED")
    env_bad_entry_refined_min_hold = _env_int("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC")
    env_bad_entry_refined_min_loss = _env_float("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT")
    env_bad_entry_refined_max_peak = _env_float("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT")
    env_bad_entry_refined_ai_limit = _env_int("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT")
    env_bad_entry_refined_recovery_max = _env_float("KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX")
    env_soft_stop_expert_enabled = _env_bool("KORSTOCKSCAN_SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED")
    env_soft_stop_expert_activate_at = _env_str("KORSTOCKSCAN_SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT")
    env_soft_stop_whipsaw_enabled = _env_bool("KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED")
    env_soft_stop_whipsaw_sec = _env_int("KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC")
    env_soft_stop_whipsaw_buffer = _env_float("KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT")
    env_soft_stop_whipsaw_worsen = _env_float("KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT")
    env_protect_trailing_smooth_enabled = _env_bool("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_ENABLED")
    env_protect_trailing_smooth_window = _env_int("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC")
    env_protect_trailing_smooth_min_span = _env_int("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC")
    env_protect_trailing_smooth_min_samples = _env_int("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES")
    env_protect_trailing_smooth_below_ratio = _env_float("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO")
    env_protect_trailing_smooth_buffer = _env_float("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT")
    env_protect_trailing_emergency = _env_float("KORSTOCKSCAN_SCALP_PROTECT_TRAILING_EMERGENCY_PCT")
    if (
        env_dynamic_strength_enabled is not None
        or env_dynamic_strength_tags is not None
        or env_dynamic_strength_reasons is not None
        or env_dynamic_strength_min_buy_value_ratio is not None
        or env_dynamic_strength_buy_ratio_tol is not None
        or env_dynamic_strength_exec_buy_ratio_tol is not None
        or env_pre_ai_soft_gate_enabled is not None
        or env_pre_ai_source_quality_block_enabled is not None
        or env_pre_ai_max_ws_age_sec is not None
        or env_pre_ai_extreme_sell_buy_ratio is not None
        or env_pre_ai_extreme_sell_exec_buy_ratio is not None
        or env_overbought_pullback_guard_enabled is not None
        or env_overbought_pullback_min_distance is not None
        or env_overbought_rebreak_min_strength is not None
        or env_overbought_rebreak_min_buy_pressure is not None
        or env_liquidity_pre_submit_guard_enabled is not None
        or env_partial_fill_enabled is not None
        or env_partial_fill_min_default is not None
        or env_partial_fill_min_strong is not None
        or env_partial_fill_min_preset is not None
        or env_pre_submit_price_guard_enabled is not None
        or env_pre_submit_max_below_bid_bps is not None
        or env_entry_price_resolver_enabled is not None
        or env_entry_price_resolver_max_below_bid_bps is not None
        or env_entry_ai_price_enabled is not None
        or env_entry_ai_price_min_confidence is not None
        or env_entry_ai_price_skip_min_confidence is not None
        or env_entry_ai_price_ofi_skip_demotion_enabled is not None
        or env_entry_ai_price_ofi_skip_demotion_max_confidence is not None
        or env_entry_ai_price_tick_limit is not None
        or env_entry_ai_price_candle_limit is not None
        or env_entry_price_orderbook_micro_enabled is not None
        or env_entry_price_orderbook_micro_bucket_enabled is not None
        or env_ofi_ai_smoothing_stale_threshold_ms is not None
        or env_ofi_ai_smoothing_raw_weight is not None
        or env_ofi_ai_smoothing_bullish_threshold is not None
        or env_ofi_ai_smoothing_bearish_threshold is not None
        or env_ofi_ai_smoothing_release_threshold is not None
        or env_ofi_ai_smoothing_persistence_required is not None
        or env_scalping_entry_timeout is not None
        or env_scalping_breakout_entry_timeout is not None
        or env_scalping_pullback_entry_timeout is not None
        or env_scalping_reserve_entry_timeout is not None
        or env_reversal_add_enabled is not None
        or env_reversal_add_min_ai_score is not None
        or env_reversal_add_min_buy_pressure is not None
        or env_reversal_add_min_tick_accel is not None
        or env_reversal_add_size_ratio is not None
        or env_reversal_add_min_qty_floor_enabled is not None
        or env_bad_entry_observe_enabled is not None
        or env_bad_entry_refined_enabled is not None
        or env_bad_entry_refined_min_hold is not None
        or env_bad_entry_refined_min_loss is not None
        or env_bad_entry_refined_max_peak is not None
        or env_bad_entry_refined_ai_limit is not None
        or env_bad_entry_refined_recovery_max is not None
        or env_soft_stop_expert_enabled is not None
        or env_soft_stop_expert_activate_at is not None
        or env_soft_stop_whipsaw_enabled is not None
        or env_soft_stop_whipsaw_sec is not None
        or env_soft_stop_whipsaw_buffer is not None
        or env_soft_stop_whipsaw_worsen is not None
        or env_protect_trailing_smooth_enabled is not None
        or env_protect_trailing_smooth_window is not None
        or env_protect_trailing_smooth_min_span is not None
        or env_protect_trailing_smooth_min_samples is not None
        or env_protect_trailing_smooth_below_ratio is not None
        or env_protect_trailing_smooth_buffer is not None
        or env_protect_trailing_emergency is not None
    ):
        config = replace(
            config,
            SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED=env_dynamic_strength_enabled
            if env_dynamic_strength_enabled is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_ENABLED,
            SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS=env_dynamic_strength_tags
            if env_dynamic_strength_tags is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_TAGS,
            SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS=env_dynamic_strength_reasons
            if env_dynamic_strength_reasons is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_ALLOWED_REASONS,
            SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO=env_dynamic_strength_min_buy_value_ratio
            if env_dynamic_strength_min_buy_value_ratio is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_MIN_BUY_VALUE_RATIO,
            SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL=env_dynamic_strength_buy_ratio_tol
            if env_dynamic_strength_buy_ratio_tol is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_BUY_RATIO_TOL,
            SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL=env_dynamic_strength_exec_buy_ratio_tol
            if env_dynamic_strength_exec_buy_ratio_tol is not None
            else config.SCALP_DYNAMIC_STRENGTH_RELIEF_EXEC_BUY_RATIO_TOL,
            SCALP_PRE_AI_SOFT_GATE_ENABLED=env_pre_ai_soft_gate_enabled
            if env_pre_ai_soft_gate_enabled is not None
            else config.SCALP_PRE_AI_SOFT_GATE_ENABLED,
            SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=env_pre_ai_source_quality_block_enabled
            if env_pre_ai_source_quality_block_enabled is not None
            else config.SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED,
            SCALP_PRE_AI_MAX_WS_AGE_SEC=env_pre_ai_max_ws_age_sec
            if env_pre_ai_max_ws_age_sec is not None
            else config.SCALP_PRE_AI_MAX_WS_AGE_SEC,
            SCALP_PRE_AI_EXTREME_SELL_BUY_RATIO_MAX=env_pre_ai_extreme_sell_buy_ratio
            if env_pre_ai_extreme_sell_buy_ratio is not None
            else config.SCALP_PRE_AI_EXTREME_SELL_BUY_RATIO_MAX,
            SCALP_PRE_AI_EXTREME_SELL_EXEC_BUY_RATIO_MAX=env_pre_ai_extreme_sell_exec_buy_ratio
            if env_pre_ai_extreme_sell_exec_buy_ratio is not None
            else config.SCALP_PRE_AI_EXTREME_SELL_EXEC_BUY_RATIO_MAX,
            SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=env_overbought_pullback_guard_enabled
            if env_overbought_pullback_guard_enabled is not None
            else config.SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED,
            SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT=env_overbought_pullback_min_distance
            if env_overbought_pullback_min_distance is not None
            else config.SCALP_OVERBOUGHT_PULLBACK_MIN_DISTANCE_PCT,
            SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH=env_overbought_rebreak_min_strength
            if env_overbought_rebreak_min_strength is not None
            else config.SCALP_OVERBOUGHT_REBREAK_MIN_STRENGTH,
            SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE=env_overbought_rebreak_min_buy_pressure
            if env_overbought_rebreak_min_buy_pressure is not None
            else config.SCALP_OVERBOUGHT_REBREAK_MIN_BUY_PRESSURE,
            SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED=env_liquidity_pre_submit_guard_enabled
            if env_liquidity_pre_submit_guard_enabled is not None
            else config.SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED,
            SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED=env_partial_fill_enabled
            if env_partial_fill_enabled is not None
            else config.SCALP_PARTIAL_FILL_RATIO_GUARD_ENABLED,
            SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT=env_partial_fill_min_default
            if env_partial_fill_min_default is not None
            else config.SCALP_PARTIAL_FILL_MIN_RATIO_DEFAULT,
            SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE=env_partial_fill_min_strong
            if env_partial_fill_min_strong is not None
            else config.SCALP_PARTIAL_FILL_MIN_RATIO_STRONG_ABS_OVERRIDE,
            SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP=env_partial_fill_min_preset
            if env_partial_fill_min_preset is not None
            else config.SCALP_PARTIAL_FILL_MIN_RATIO_PRESET_TP,
            SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=env_pre_submit_price_guard_enabled
            if env_pre_submit_price_guard_enabled is not None
            else config.SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED,
            SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=env_pre_submit_max_below_bid_bps
            if env_pre_submit_max_below_bid_bps is not None
            else config.SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS,
            SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=env_entry_price_resolver_enabled
            if env_entry_price_resolver_enabled is not None
            else config.SCALPING_ENTRY_PRICE_RESOLVER_ENABLED,
            SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS=env_entry_price_resolver_max_below_bid_bps
            if env_entry_price_resolver_max_below_bid_bps is not None
            else config.SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS,
            SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED=env_entry_ai_price_enabled
            if env_entry_ai_price_enabled is not None
            else config.SCALPING_ENTRY_AI_PRICE_CANARY_ENABLED,
            SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE=env_entry_ai_price_min_confidence
            if env_entry_ai_price_min_confidence is not None
            else config.SCALPING_ENTRY_AI_PRICE_MIN_CONFIDENCE,
            SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE=env_entry_ai_price_skip_min_confidence
            if env_entry_ai_price_skip_min_confidence is not None
            else config.SCALPING_ENTRY_AI_PRICE_SKIP_MIN_CONFIDENCE,
            SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED=env_entry_ai_price_ofi_skip_demotion_enabled
            if env_entry_ai_price_ofi_skip_demotion_enabled is not None
            else config.SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_ENABLED,
            SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE=env_entry_ai_price_ofi_skip_demotion_max_confidence
            if env_entry_ai_price_ofi_skip_demotion_max_confidence is not None
            else config.SCALPING_ENTRY_AI_PRICE_OFI_SKIP_DEMOTION_MAX_CONFIDENCE,
            SCALPING_ENTRY_AI_PRICE_TICK_LIMIT=env_entry_ai_price_tick_limit
            if env_entry_ai_price_tick_limit is not None
            else config.SCALPING_ENTRY_AI_PRICE_TICK_LIMIT,
            SCALPING_ENTRY_AI_PRICE_CANDLE_LIMIT=env_entry_ai_price_candle_limit
            if env_entry_ai_price_candle_limit is not None
            else config.SCALPING_ENTRY_AI_PRICE_CANDLE_LIMIT,
            SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED=env_entry_price_orderbook_micro_enabled
            if env_entry_price_orderbook_micro_enabled is not None
            else config.SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_ENABLED,
            SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED=env_entry_price_orderbook_micro_bucket_enabled
            if env_entry_price_orderbook_micro_bucket_enabled is not None
            else config.SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED,
            OFI_AI_SMOOTHING_STALE_THRESHOLD_MS=env_ofi_ai_smoothing_stale_threshold_ms
            if env_ofi_ai_smoothing_stale_threshold_ms is not None
            else config.OFI_AI_SMOOTHING_STALE_THRESHOLD_MS,
            OFI_AI_SMOOTHING_RAW_WEIGHT=env_ofi_ai_smoothing_raw_weight
            if env_ofi_ai_smoothing_raw_weight is not None
            else config.OFI_AI_SMOOTHING_RAW_WEIGHT,
            OFI_AI_SMOOTHING_BULLISH_THRESHOLD=env_ofi_ai_smoothing_bullish_threshold
            if env_ofi_ai_smoothing_bullish_threshold is not None
            else config.OFI_AI_SMOOTHING_BULLISH_THRESHOLD,
            OFI_AI_SMOOTHING_BEARISH_THRESHOLD=env_ofi_ai_smoothing_bearish_threshold
            if env_ofi_ai_smoothing_bearish_threshold is not None
            else config.OFI_AI_SMOOTHING_BEARISH_THRESHOLD,
            OFI_AI_SMOOTHING_RELEASE_THRESHOLD=env_ofi_ai_smoothing_release_threshold
            if env_ofi_ai_smoothing_release_threshold is not None
            else config.OFI_AI_SMOOTHING_RELEASE_THRESHOLD,
            OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED=env_ofi_ai_smoothing_persistence_required
            if env_ofi_ai_smoothing_persistence_required is not None
            else config.OFI_AI_SMOOTHING_PERSISTENCE_REQUIRED,
            SCALPING_ENTRY_TIMEOUT_SEC=env_scalping_entry_timeout
            if env_scalping_entry_timeout is not None
            else config.SCALPING_ENTRY_TIMEOUT_SEC,
            SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC=env_scalping_breakout_entry_timeout
            if env_scalping_breakout_entry_timeout is not None
            else config.SCALPING_BREAKOUT_ENTRY_TIMEOUT_SEC,
            SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC=env_scalping_pullback_entry_timeout
            if env_scalping_pullback_entry_timeout is not None
            else config.SCALPING_PULLBACK_ENTRY_TIMEOUT_SEC,
            SCALPING_RESERVE_ENTRY_TIMEOUT_SEC=env_scalping_reserve_entry_timeout
            if env_scalping_reserve_entry_timeout is not None
            else config.SCALPING_RESERVE_ENTRY_TIMEOUT_SEC,
            REVERSAL_ADD_ENABLED=env_reversal_add_enabled
            if env_reversal_add_enabled is not None
            else config.REVERSAL_ADD_ENABLED,
            REVERSAL_ADD_MIN_AI_SCORE=env_reversal_add_min_ai_score
            if env_reversal_add_min_ai_score is not None
            else config.REVERSAL_ADD_MIN_AI_SCORE,
            REVERSAL_ADD_MIN_BUY_PRESSURE=env_reversal_add_min_buy_pressure
            if env_reversal_add_min_buy_pressure is not None
            else config.REVERSAL_ADD_MIN_BUY_PRESSURE,
            REVERSAL_ADD_MIN_TICK_ACCEL=env_reversal_add_min_tick_accel
            if env_reversal_add_min_tick_accel is not None
            else config.REVERSAL_ADD_MIN_TICK_ACCEL,
            REVERSAL_ADD_SIZE_RATIO=env_reversal_add_size_ratio
            if env_reversal_add_size_ratio is not None
            else config.REVERSAL_ADD_SIZE_RATIO,
            REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=env_reversal_add_min_qty_floor_enabled
            if env_reversal_add_min_qty_floor_enabled is not None
            else config.REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED,
            SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=env_bad_entry_observe_enabled
            if env_bad_entry_observe_enabled is not None
            else config.SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED,
            SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=env_bad_entry_refined_enabled
            if env_bad_entry_refined_enabled is not None
            else config.SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED,
            SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC=env_bad_entry_refined_min_hold
            if env_bad_entry_refined_min_hold is not None
            else config.SCALP_BAD_ENTRY_REFINED_MIN_HOLD_SEC,
            SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT=env_bad_entry_refined_min_loss
            if env_bad_entry_refined_min_loss is not None
            else config.SCALP_BAD_ENTRY_REFINED_MIN_LOSS_PCT,
            SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT=env_bad_entry_refined_max_peak
            if env_bad_entry_refined_max_peak is not None
            else config.SCALP_BAD_ENTRY_REFINED_MAX_PEAK_PROFIT_PCT,
            SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT=env_bad_entry_refined_ai_limit
            if env_bad_entry_refined_ai_limit is not None
            else config.SCALP_BAD_ENTRY_REFINED_AI_SCORE_LIMIT,
            SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX=env_bad_entry_refined_recovery_max
            if env_bad_entry_refined_recovery_max is not None
            else config.SCALP_BAD_ENTRY_REFINED_RECOVERY_PROB_MAX,
            SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=env_soft_stop_expert_enabled
            if env_soft_stop_expert_enabled is not None
            else config.SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED,
            SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT=env_soft_stop_expert_activate_at
            if env_soft_stop_expert_activate_at is not None
            else config.SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT,
            SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=env_soft_stop_whipsaw_enabled
            if env_soft_stop_whipsaw_enabled is not None
            else config.SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED,
            SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC=env_soft_stop_whipsaw_sec
            if env_soft_stop_whipsaw_sec is not None
            else config.SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_SEC,
            SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT=env_soft_stop_whipsaw_buffer
            if env_soft_stop_whipsaw_buffer is not None
            else config.SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_BUFFER_PCT,
            SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT=env_soft_stop_whipsaw_worsen
            if env_soft_stop_whipsaw_worsen is not None
            else config.SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_MAX_WORSEN_PCT,
            SCALP_PROTECT_TRAILING_SMOOTH_ENABLED=env_protect_trailing_smooth_enabled
            if env_protect_trailing_smooth_enabled is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_ENABLED,
            SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC=env_protect_trailing_smooth_window
            if env_protect_trailing_smooth_window is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_WINDOW_SEC,
            SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC=env_protect_trailing_smooth_min_span
            if env_protect_trailing_smooth_min_span is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_MIN_SPAN_SEC,
            SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES=env_protect_trailing_smooth_min_samples
            if env_protect_trailing_smooth_min_samples is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_MIN_SAMPLES,
            SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO=env_protect_trailing_smooth_below_ratio
            if env_protect_trailing_smooth_below_ratio is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_BELOW_RATIO,
            SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT=env_protect_trailing_smooth_buffer
            if env_protect_trailing_smooth_buffer is not None
            else config.SCALP_PROTECT_TRAILING_SMOOTH_BUFFER_PCT,
            SCALP_PROTECT_TRAILING_EMERGENCY_PCT=env_protect_trailing_emergency
            if env_protect_trailing_emergency is not None
            else config.SCALP_PROTECT_TRAILING_EMERGENCY_PCT,
        )

    env_scalping_enable_pyramid = _env_bool("KORSTOCKSCAN_SCALPING_ENABLE_PYRAMID")
    env_invest_ratio_scalping_min = _env_float("KORSTOCKSCAN_INVEST_RATIO_SCALPING_MIN")
    env_invest_ratio_scalping_max = _env_float("KORSTOCKSCAN_INVEST_RATIO_SCALPING_MAX")
    env_scalping_max_buy_budget = _env_int("KORSTOCKSCAN_SCALPING_MAX_BUY_BUDGET_KRW")
    env_scalping_max_avg_down_count = _env_int("KORSTOCKSCAN_SCALPING_MAX_AVG_DOWN_COUNT")
    env_scalping_max_pyramid_count = _env_int("KORSTOCKSCAN_SCALPING_MAX_PYRAMID_COUNT")
    env_swing_enable_pyramid = _env_bool("KORSTOCKSCAN_SWING_ENABLE_PYRAMID")
    env_swing_enable_avg_down_simulation = _env_bool("KORSTOCKSCAN_SWING_ENABLE_AVG_DOWN_SIMULATION")
    env_swing_max_avg_down_count = _env_int("KORSTOCKSCAN_SWING_MAX_AVG_DOWN_COUNT")
    env_swing_max_pyramid_count = _env_int("KORSTOCKSCAN_SWING_MAX_PYRAMID_COUNT")
    env_swing_scale_in_dynamic_qty_enabled = _env_bool("KORSTOCKSCAN_SWING_SCALE_IN_DYNAMIC_QTY_ENABLED")
    env_swing_scale_in_effective_qty_cap = _env_int("KORSTOCKSCAN_SWING_SCALE_IN_EFFECTIVE_QTY_CAP")
    env_swing_scale_in_real_canary_enabled = _env_bool("KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ENABLED")
    env_swing_scale_in_real_canary_allowed_arms = _env_str(
        "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS"
    )
    env_swing_scale_in_real_canary_max_qty = _env_int("KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_MAX_QTY")
    env_swing_scale_in_real_canary_max_orders_per_day = _env_int(
        "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY"
    )
    env_swing_scale_in_real_canary_max_orders_per_position = _env_int(
        "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION"
    )
    env_swing_scale_in_real_canary_max_daily_notional = _env_int(
        "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW"
    )
    env_swing_scale_in_real_canary_require_approval = _env_bool(
        "KORSTOCKSCAN_SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT"
    )
    env_swing_one_share_real_canary_enabled = _env_bool("KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED")
    env_swing_one_share_real_canary_allowed_codes = _env_str(
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES"
    )
    env_swing_one_share_real_canary_max_qty = _env_int("KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_QTY")
    env_swing_one_share_real_canary_max_new_entries_per_day = _env_int(
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY"
    )
    env_swing_one_share_real_canary_max_open_positions = _env_int(
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS"
    )
    env_swing_one_share_real_canary_max_total_notional = _env_int(
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW"
    )
    env_swing_one_share_real_canary_require_approval = _env_bool(
        "KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT"
    )
    env_ml_gatekeeper_reject_cooldown = _env_int("KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN")
    env_swing_live_order_dry_run_enabled = _env_bool(
        "KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED"
    )
    env_swing_intraday_probe_enabled = _env_bool(
        "KORSTOCKSCAN_SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED"
    )
    env_swing_intraday_probe_max_open = _env_int("KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_OPEN")
    env_swing_intraday_probe_max_daily = _env_int("KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_DAILY")
    env_swing_intraday_probe_max_per_symbol = _env_int("KORSTOCKSCAN_SWING_INTRADAY_PROBE_MAX_PER_SYMBOL")
    env_swing_intraday_probe_score_vpw_max_open = _env_int(
        "KORSTOCKSCAN_SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN"
    )
    env_swing_intraday_probe_discard_log_min_interval = _env_int(
        "KORSTOCKSCAN_SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC"
    )
    env_swing_same_symbol_loss_reentry_guard_enabled = _env_bool(
        "KORSTOCKSCAN_SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED"
    )
    env_swing_same_symbol_loss_reentry_cooldown_sec = _env_int(
        "KORSTOCKSCAN_SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC"
    )
    env_swing_same_symbol_loss_reentry_loss_threshold_pct = _env_float(
        "KORSTOCKSCAN_SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT"
    )
    env_swing_same_symbol_loss_reentry_consecutive_losses = _env_int(
        "KORSTOCKSCAN_SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES"
    )
    env_swing_same_symbol_loss_reentry_counterfactual_enabled = _env_bool(
        "KORSTOCKSCAN_SWING_SAME_SYMBOL_LOSS_REENTRY_COUNTERFACTUAL_ENABLED"
    )
    env_swing_orderbook_micro_context_enabled = _env_bool(
        "KORSTOCKSCAN_SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED"
    )
    env_scalp_live_simulator_enabled = _env_bool("KORSTOCKSCAN_SCALP_LIVE_SIMULATOR_ENABLED")
    env_scalp_live_simulator_owner = _env_str("KORSTOCKSCAN_SCALP_LIVE_SIMULATOR_OWNER")
    env_scalp_live_simulator_fill_policy = _env_str("KORSTOCKSCAN_SCALP_LIVE_SIMULATOR_FILL_POLICY")
    env_scalp_live_simulator_qty = _env_int("KORSTOCKSCAN_SCALP_LIVE_SIMULATOR_QTY")
    env_scalp_sim_candidate_window_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED"
    )
    env_scalp_sim_candidate_window_min_score = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE"
    )
    env_scalp_sim_candidate_window_max_score = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_SCORE"
    )
    env_scalp_sim_candidate_window_max_open = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN"
    )
    env_scalp_sim_candidate_window_max_daily = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY"
    )
    env_scalp_sim_candidate_window_blocked_ai_max_share = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT"
    )
    env_scalp_sim_candidate_window_first_ai_min_share = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT"
    )
    env_scalp_sim_candidate_window_time_bucket_policy = _env_str(
        "KORSTOCKSCAN_SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY"
    )
    env_scalp_sim_ai_budget_enabled = _env_bool("KORSTOCKSCAN_SCALP_SIM_AI_BUDGET_ENABLED")
    env_scalp_sim_ai_max_calls_per_min = _env_int("KORSTOCKSCAN_SCALP_SIM_AI_MAX_CALLS_PER_MIN")
    env_scalp_sim_ai_holding_min_cooldown = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC"
    )
    env_scalp_sim_ai_holding_critical_cooldown = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC"
    )
    env_scalp_sim_ai_holding_max_cooldown = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC"
    )
    env_scalp_sim_ai_deferred_review_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED"
    )
    env_scalp_sim_ai_hard_critical_min_loss = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT"
    )
    env_scalp_sim_ai_soft_loss_defer_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED"
    )
    env_scalp_sim_ai_safe_profit_bypass_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED"
    )
    env_scalp_sim_ai_critical_drawdown = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT"
    )
    env_scalp_sim_scale_in_window_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"
    )
    env_scalp_sim_scale_in_window_allowed_arms = _env_str(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS"
    )
    env_scalp_sim_scale_in_window_min_profit = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT"
    )
    env_scalp_sim_scale_in_window_max_profit = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT"
    )
    env_scalp_sim_scale_in_window_max_orders_position = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION"
    )
    env_scalp_sim_scale_in_window_max_orders_day = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY"
    )
    env_scalp_sim_panic_lifecycle_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_LIFECYCLE_ENABLED"
    )
    env_scalp_sim_panic_entry_block_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_ENTRY_BLOCK_ENABLED"
    )
    env_scalp_sim_panic_scale_in_block_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_SCALE_IN_BLOCK_ENABLED"
    )
    env_scalp_sim_panic_holding_exit_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_HOLDING_EXIT_ENABLED"
    )
    env_scalp_sim_panic_partial_sell_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_PARTIAL_SELL_ENABLED"
    )
    env_scalp_sim_panic_force_noop = _env_bool("KORSTOCKSCAN_SCALP_SIM_PANIC_FORCE_NOOP")
    env_scalp_sim_panic_block_entry_level = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BLOCK_ENTRY_LEVEL"
    )
    env_scalp_sim_panic_disable_scale_in_level = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_DISABLE_SCALE_IN_LEVEL"
    )
    env_scalp_sim_panic_bottoming_entry_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_ENTRY_ENABLED"
    )
    env_scalp_sim_panic_bottoming_entry_max_level = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_ENTRY_MAX_LEVEL"
    )
    env_scalp_sim_panic_bottoming_min_ai_score = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_MIN_AI_SCORE"
    )
    env_scalp_sim_panic_bottoming_min_buy_pressure = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_MIN_BUY_PRESSURE"
    )
    env_scalp_sim_panic_bottoming_max_distance = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_MAX_DISTANCE_FROM_HIGH_PCT"
    )
    env_scalp_sim_panic_bottoming_min_strength = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BOTTOMING_MIN_STRENGTH"
    )
    env_scalp_sim_panic_min_remaining_qty = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_MIN_REMAINING_QTY"
    )
    env_scalp_sim_panic_max_partial_count = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_MAX_PARTIAL_COUNT_PER_EPOCH"
    )
    env_scalp_sim_panic_context_max_age = _env_int(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_CONTEXT_MAX_AGE_SEC"
    )
    env_scalp_sim_panic_fallback_slippage = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_FALLBACK_SLIPPAGE_BPS"
    )
    env_scalp_sim_panic_broken_liquidity_haircut = _env_float(
        "KORSTOCKSCAN_SCALP_SIM_PANIC_BROKEN_LIQUIDITY_HAIRCUT_BPS"
    )
    env_sim_virtual_budget_krw = _env_int("KORSTOCKSCAN_SIM_VIRTUAL_BUDGET_KRW")
    if env_sim_virtual_budget_krw is None:
        env_sim_virtual_budget_krw = _env_int("KORSTOCKSCAN_SIM_VIRTUAL_NOTIONAL_KRW")
    env_pipeline_event_text_info_log_enabled = _env_bool(
        "KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED"
    )
    env_pipeline_event_text_info_stage_allowlist = _env_csv_tuple(
        "KORSTOCKSCAN_PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST"
    )
    env_watching_state_debug_log_enabled = _env_bool(
        "KORSTOCKSCAN_WATCHING_STATE_DEBUG_LOG_ENABLED"
    )
    env_scalp_live_simulator_timeout = _env_int("KORSTOCKSCAN_SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC")
    env_stat_action_snapshot_enabled = _env_bool("KORSTOCKSCAN_STAT_ACTION_DECISION_SNAPSHOT_ENABLED")
    env_stat_action_snapshot_min_interval = _env_int("KORSTOCKSCAN_STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC")
    env_scalping_initial_entry_qty_cap_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED"
    )
    env_scalping_initial_entry_max_qty = _env_int(
        "KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY"
    )
    env_buy_side_time_block_enabled = _env_bool("KORSTOCKSCAN_BUY_SIDE_TIME_BLOCK_ENABLED")
    env_buy_side_time_block_until = _env_str("KORSTOCKSCAN_BUY_SIDE_TIME_BLOCK_UNTIL_HHMM")
    env_scale_in_price_resolver_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED"
    )
    env_scale_in_dynamic_qty_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED"
    )
    env_scale_in_effective_qty_cap = _env_int("KORSTOCKSCAN_SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP")
    env_scale_in_max_spread_bps = _env_float("KORSTOCKSCAN_SCALPING_SCALE_IN_MAX_SPREAD_BPS")
    env_pyramid_price_guard_enabled = _env_bool("KORSTOCKSCAN_SCALPING_PYRAMID_PRICE_GUARD_ENABLED")
    env_pyramid_max_spread_bps = _env_float("KORSTOCKSCAN_SCALPING_PYRAMID_MAX_SPREAD_BPS")
    env_pyramid_max_micro_vwap_bps = _env_float("KORSTOCKSCAN_SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS")
    env_pyramid_min_ai_score = _env_int("KORSTOCKSCAN_SCALPING_PYRAMID_MIN_AI_SCORE")
    env_pyramid_min_buy_pressure = _env_float("KORSTOCKSCAN_SCALPING_PYRAMID_MIN_BUY_PRESSURE")
    env_pyramid_min_tick_accel = _env_float("KORSTOCKSCAN_SCALPING_PYRAMID_MIN_TICK_ACCEL")
    env_scalping_pyramid_zero_qty_stage1_enabled = _env_bool(
        "KORSTOCKSCAN_SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED"
    )
    env_same_symbol_loss_reentry_cooldown_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED"
    )
    env_same_symbol_loss_reentry_cooldown_sec = _env_int(
        "KORSTOCKSCAN_SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC"
    )
    if (
        env_scalping_enable_pyramid is not None
        or env_invest_ratio_scalping_min is not None
        or env_invest_ratio_scalping_max is not None
        or env_scalping_max_buy_budget is not None
        or env_scalping_max_avg_down_count is not None
        or env_scalping_max_pyramid_count is not None
        or env_swing_enable_pyramid is not None
        or env_swing_enable_avg_down_simulation is not None
        or env_swing_max_avg_down_count is not None
        or env_swing_max_pyramid_count is not None
        or env_swing_scale_in_dynamic_qty_enabled is not None
        or env_swing_scale_in_effective_qty_cap is not None
        or env_swing_scale_in_real_canary_enabled is not None
        or env_swing_scale_in_real_canary_allowed_arms is not None
        or env_swing_scale_in_real_canary_max_qty is not None
        or env_swing_scale_in_real_canary_max_orders_per_day is not None
        or env_swing_scale_in_real_canary_max_orders_per_position is not None
        or env_swing_scale_in_real_canary_max_daily_notional is not None
        or env_swing_scale_in_real_canary_require_approval is not None
        or env_swing_one_share_real_canary_enabled is not None
        or env_swing_one_share_real_canary_allowed_codes is not None
        or env_swing_one_share_real_canary_max_qty is not None
        or env_swing_one_share_real_canary_max_new_entries_per_day is not None
        or env_swing_one_share_real_canary_max_open_positions is not None
        or env_swing_one_share_real_canary_max_total_notional is not None
        or env_swing_one_share_real_canary_require_approval is not None
        or env_ml_gatekeeper_reject_cooldown is not None
        or env_swing_live_order_dry_run_enabled is not None
        or env_swing_intraday_probe_enabled is not None
        or env_swing_intraday_probe_max_open is not None
        or env_swing_intraday_probe_max_daily is not None
        or env_swing_intraday_probe_max_per_symbol is not None
        or env_swing_intraday_probe_score_vpw_max_open is not None
        or env_swing_intraday_probe_discard_log_min_interval is not None
        or env_swing_same_symbol_loss_reentry_guard_enabled is not None
        or env_swing_same_symbol_loss_reentry_cooldown_sec is not None
        or env_swing_same_symbol_loss_reentry_loss_threshold_pct is not None
        or env_swing_same_symbol_loss_reentry_consecutive_losses is not None
        or env_swing_same_symbol_loss_reentry_counterfactual_enabled is not None
        or env_swing_orderbook_micro_context_enabled is not None
        or env_scalp_live_simulator_enabled is not None
        or env_scalp_live_simulator_owner is not None
        or env_scalp_live_simulator_fill_policy is not None
        or env_scalp_live_simulator_qty is not None
        or env_scalp_sim_candidate_window_enabled is not None
        or env_scalp_sim_candidate_window_min_score is not None
        or env_scalp_sim_candidate_window_max_score is not None
        or env_scalp_sim_candidate_window_max_open is not None
        or env_scalp_sim_candidate_window_max_daily is not None
        or env_scalp_sim_candidate_window_blocked_ai_max_share is not None
        or env_scalp_sim_candidate_window_first_ai_min_share is not None
        or env_scalp_sim_candidate_window_time_bucket_policy is not None
        or env_scalp_sim_ai_budget_enabled is not None
        or env_scalp_sim_ai_max_calls_per_min is not None
        or env_scalp_sim_ai_holding_min_cooldown is not None
        or env_scalp_sim_ai_holding_critical_cooldown is not None
        or env_scalp_sim_ai_holding_max_cooldown is not None
        or env_scalp_sim_ai_deferred_review_enabled is not None
        or env_scalp_sim_ai_hard_critical_min_loss is not None
        or env_scalp_sim_ai_soft_loss_defer_enabled is not None
        or env_scalp_sim_ai_safe_profit_bypass_enabled is not None
        or env_scalp_sim_ai_critical_drawdown is not None
        or env_sim_virtual_budget_krw is not None
        or env_scalp_live_simulator_timeout is not None
        or env_stat_action_snapshot_enabled is not None
        or env_stat_action_snapshot_min_interval is not None
        or env_scalping_initial_entry_qty_cap_enabled is not None
        or env_scalping_initial_entry_max_qty is not None
        or env_buy_side_time_block_enabled is not None
        or env_buy_side_time_block_until is not None
        or env_scale_in_price_resolver_enabled is not None
        or env_scale_in_dynamic_qty_enabled is not None
        or env_scale_in_effective_qty_cap is not None
        or env_scale_in_max_spread_bps is not None
        or env_pyramid_price_guard_enabled is not None
        or env_pyramid_max_spread_bps is not None
        or env_pyramid_max_micro_vwap_bps is not None
        or env_pyramid_min_ai_score is not None
        or env_pyramid_min_buy_pressure is not None
        or env_pyramid_min_tick_accel is not None
        or env_scalping_pyramid_zero_qty_stage1_enabled is not None
        or env_same_symbol_loss_reentry_cooldown_enabled is not None
        or env_same_symbol_loss_reentry_cooldown_sec is not None
    ):
        config = replace(
            config,
            SCALPING_ENABLE_PYRAMID=env_scalping_enable_pyramid
            if env_scalping_enable_pyramid is not None
            else config.SCALPING_ENABLE_PYRAMID,
            INVEST_RATIO_SCALPING_MIN=env_invest_ratio_scalping_min
            if env_invest_ratio_scalping_min is not None
            else config.INVEST_RATIO_SCALPING_MIN,
            INVEST_RATIO_SCALPING_MAX=env_invest_ratio_scalping_max
            if env_invest_ratio_scalping_max is not None
            else config.INVEST_RATIO_SCALPING_MAX,
            SCALPING_MAX_BUY_BUDGET_KRW=env_scalping_max_buy_budget
            if env_scalping_max_buy_budget is not None
            else config.SCALPING_MAX_BUY_BUDGET_KRW,
            SCALPING_MAX_AVG_DOWN_COUNT=env_scalping_max_avg_down_count
            if env_scalping_max_avg_down_count is not None
            else config.SCALPING_MAX_AVG_DOWN_COUNT,
            SCALPING_MAX_PYRAMID_COUNT=env_scalping_max_pyramid_count
            if env_scalping_max_pyramid_count is not None
            else config.SCALPING_MAX_PYRAMID_COUNT,
            SWING_ENABLE_PYRAMID=env_swing_enable_pyramid
            if env_swing_enable_pyramid is not None
            else config.SWING_ENABLE_PYRAMID,
            SWING_ENABLE_AVG_DOWN_SIMULATION=env_swing_enable_avg_down_simulation
            if env_swing_enable_avg_down_simulation is not None
            else config.SWING_ENABLE_AVG_DOWN_SIMULATION,
            SWING_MAX_AVG_DOWN_COUNT=env_swing_max_avg_down_count
            if env_swing_max_avg_down_count is not None
            else config.SWING_MAX_AVG_DOWN_COUNT,
            SWING_MAX_PYRAMID_COUNT=env_swing_max_pyramid_count
            if env_swing_max_pyramid_count is not None
            else config.SWING_MAX_PYRAMID_COUNT,
            SWING_SCALE_IN_DYNAMIC_QTY_ENABLED=env_swing_scale_in_dynamic_qty_enabled
            if env_swing_scale_in_dynamic_qty_enabled is not None
            else config.SWING_SCALE_IN_DYNAMIC_QTY_ENABLED,
            SWING_SCALE_IN_EFFECTIVE_QTY_CAP=env_swing_scale_in_effective_qty_cap
            if env_swing_scale_in_effective_qty_cap is not None
            else config.SWING_SCALE_IN_EFFECTIVE_QTY_CAP,
            SWING_SCALE_IN_REAL_CANARY_ENABLED=env_swing_scale_in_real_canary_enabled
            if env_swing_scale_in_real_canary_enabled is not None
            else config.SWING_SCALE_IN_REAL_CANARY_ENABLED,
            SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS=env_swing_scale_in_real_canary_allowed_arms
            if env_swing_scale_in_real_canary_allowed_arms is not None
            else config.SWING_SCALE_IN_REAL_CANARY_ALLOWED_ARMS,
            SWING_SCALE_IN_REAL_CANARY_MAX_QTY=env_swing_scale_in_real_canary_max_qty
            if env_swing_scale_in_real_canary_max_qty is not None
            else config.SWING_SCALE_IN_REAL_CANARY_MAX_QTY,
            SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY=env_swing_scale_in_real_canary_max_orders_per_day
            if env_swing_scale_in_real_canary_max_orders_per_day is not None
            else config.SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_DAY,
            SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION=env_swing_scale_in_real_canary_max_orders_per_position
            if env_swing_scale_in_real_canary_max_orders_per_position is not None
            else config.SWING_SCALE_IN_REAL_CANARY_MAX_ORDERS_PER_POSITION,
            SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW=env_swing_scale_in_real_canary_max_daily_notional
            if env_swing_scale_in_real_canary_max_daily_notional is not None
            else config.SWING_SCALE_IN_REAL_CANARY_MAX_DAILY_NOTIONAL_KRW,
            SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT=env_swing_scale_in_real_canary_require_approval
            if env_swing_scale_in_real_canary_require_approval is not None
            else config.SWING_SCALE_IN_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT,
            SWING_ONE_SHARE_REAL_CANARY_ENABLED=env_swing_one_share_real_canary_enabled
            if env_swing_one_share_real_canary_enabled is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_ENABLED,
            SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES=env_swing_one_share_real_canary_allowed_codes
            if env_swing_one_share_real_canary_allowed_codes is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_ALLOWED_CODES,
            SWING_ONE_SHARE_REAL_CANARY_MAX_QTY=env_swing_one_share_real_canary_max_qty
            if env_swing_one_share_real_canary_max_qty is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_MAX_QTY,
            SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY=env_swing_one_share_real_canary_max_new_entries_per_day
            if env_swing_one_share_real_canary_max_new_entries_per_day is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_MAX_NEW_ENTRIES_PER_DAY,
            SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS=env_swing_one_share_real_canary_max_open_positions
            if env_swing_one_share_real_canary_max_open_positions is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_MAX_OPEN_POSITIONS,
            SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW=env_swing_one_share_real_canary_max_total_notional
            if env_swing_one_share_real_canary_max_total_notional is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_MAX_TOTAL_NOTIONAL_KRW,
            SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT=env_swing_one_share_real_canary_require_approval
            if env_swing_one_share_real_canary_require_approval is not None
            else config.SWING_ONE_SHARE_REAL_CANARY_REQUIRE_APPROVAL_ARTIFACT,
            ML_GATEKEEPER_REJECT_COOLDOWN=env_ml_gatekeeper_reject_cooldown
            if env_ml_gatekeeper_reject_cooldown is not None
            else config.ML_GATEKEEPER_REJECT_COOLDOWN,
            SWING_LIVE_ORDER_DRY_RUN_ENABLED=env_swing_live_order_dry_run_enabled
            if env_swing_live_order_dry_run_enabled is not None
            else config.SWING_LIVE_ORDER_DRY_RUN_ENABLED,
            SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED=env_swing_intraday_probe_enabled
            if env_swing_intraday_probe_enabled is not None
            else config.SWING_INTRADAY_LIVE_EQUIV_PROBE_ENABLED,
            SWING_INTRADAY_PROBE_MAX_OPEN=env_swing_intraday_probe_max_open
            if env_swing_intraday_probe_max_open is not None
            else config.SWING_INTRADAY_PROBE_MAX_OPEN,
            SWING_INTRADAY_PROBE_MAX_DAILY=env_swing_intraday_probe_max_daily
            if env_swing_intraday_probe_max_daily is not None
            else config.SWING_INTRADAY_PROBE_MAX_DAILY,
            SWING_INTRADAY_PROBE_MAX_PER_SYMBOL=env_swing_intraday_probe_max_per_symbol
            if env_swing_intraday_probe_max_per_symbol is not None
            else config.SWING_INTRADAY_PROBE_MAX_PER_SYMBOL,
            SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN=env_swing_intraday_probe_score_vpw_max_open
            if env_swing_intraday_probe_score_vpw_max_open is not None
            else config.SWING_INTRADAY_PROBE_SCORE_VPW_MAX_OPEN,
            SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC=env_swing_intraday_probe_discard_log_min_interval
            if env_swing_intraday_probe_discard_log_min_interval is not None
            else config.SWING_INTRADAY_PROBE_DISCARD_LOG_MIN_INTERVAL_SEC,
            SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED=env_swing_same_symbol_loss_reentry_guard_enabled
            if env_swing_same_symbol_loss_reentry_guard_enabled is not None
            else config.SWING_SAME_SYMBOL_LOSS_REENTRY_GUARD_ENABLED,
            SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=env_swing_same_symbol_loss_reentry_cooldown_sec
            if env_swing_same_symbol_loss_reentry_cooldown_sec is not None
            else config.SWING_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC,
            SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT=env_swing_same_symbol_loss_reentry_loss_threshold_pct
            if env_swing_same_symbol_loss_reentry_loss_threshold_pct is not None
            else config.SWING_SAME_SYMBOL_LOSS_REENTRY_LOSS_THRESHOLD_PCT,
            SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES=env_swing_same_symbol_loss_reentry_consecutive_losses
            if env_swing_same_symbol_loss_reentry_consecutive_losses is not None
            else config.SWING_SAME_SYMBOL_LOSS_REENTRY_CONSECUTIVE_LOSSES,
            SWING_SAME_SYMBOL_LOSS_REENTRY_COUNTERFACTUAL_ENABLED=env_swing_same_symbol_loss_reentry_counterfactual_enabled
            if env_swing_same_symbol_loss_reentry_counterfactual_enabled is not None
            else config.SWING_SAME_SYMBOL_LOSS_REENTRY_COUNTERFACTUAL_ENABLED,
            SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED=env_swing_orderbook_micro_context_enabled
            if env_swing_orderbook_micro_context_enabled is not None
            else config.SWING_ORDERBOOK_MICRO_CONTEXT_ENABLED,
            SCALP_LIVE_SIMULATOR_ENABLED=env_scalp_live_simulator_enabled
            if env_scalp_live_simulator_enabled is not None
            else config.SCALP_LIVE_SIMULATOR_ENABLED,
            SCALP_LIVE_SIMULATOR_OWNER=env_scalp_live_simulator_owner
            if env_scalp_live_simulator_owner is not None
            else config.SCALP_LIVE_SIMULATOR_OWNER,
            SCALP_LIVE_SIMULATOR_FILL_POLICY=env_scalp_live_simulator_fill_policy
            if env_scalp_live_simulator_fill_policy is not None
            else config.SCALP_LIVE_SIMULATOR_FILL_POLICY,
            SCALP_LIVE_SIMULATOR_QTY=env_scalp_live_simulator_qty
            if env_scalp_live_simulator_qty is not None
            else config.SCALP_LIVE_SIMULATOR_QTY,
            SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED=env_scalp_sim_candidate_window_enabled
            if env_scalp_sim_candidate_window_enabled is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_EXPANSION_ENABLED,
            SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE=env_scalp_sim_candidate_window_min_score
            if env_scalp_sim_candidate_window_min_score is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_MIN_SCORE,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_SCORE=env_scalp_sim_candidate_window_max_score
            if env_scalp_sim_candidate_window_max_score is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_MAX_SCORE,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN=env_scalp_sim_candidate_window_max_open
            if env_scalp_sim_candidate_window_max_open is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_MAX_OPEN,
            SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY=env_scalp_sim_candidate_window_max_daily
            if env_scalp_sim_candidate_window_max_daily is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_MAX_DAILY,
            SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT=env_scalp_sim_candidate_window_blocked_ai_max_share
            if env_scalp_sim_candidate_window_blocked_ai_max_share is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_BLOCKED_AI_SCORE_MAX_SHARE_PCT,
            SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT=env_scalp_sim_candidate_window_first_ai_min_share
            if env_scalp_sim_candidate_window_first_ai_min_share is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_FIRST_AI_WAIT_MIN_SHARE_PCT,
            SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY=env_scalp_sim_candidate_window_time_bucket_policy
            if env_scalp_sim_candidate_window_time_bucket_policy is not None
            else config.SCALP_SIM_CANDIDATE_WINDOW_TIME_BUCKET_POLICY,
            SCALP_SIM_AI_BUDGET_ENABLED=env_scalp_sim_ai_budget_enabled
            if env_scalp_sim_ai_budget_enabled is not None
            else config.SCALP_SIM_AI_BUDGET_ENABLED,
            SCALP_SIM_AI_MAX_CALLS_PER_MIN=env_scalp_sim_ai_max_calls_per_min
            if env_scalp_sim_ai_max_calls_per_min is not None
            else config.SCALP_SIM_AI_MAX_CALLS_PER_MIN,
            SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC=env_scalp_sim_ai_holding_min_cooldown
            if env_scalp_sim_ai_holding_min_cooldown is not None
            else config.SCALP_SIM_AI_HOLDING_MIN_COOLDOWN_SEC,
            SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC=env_scalp_sim_ai_holding_critical_cooldown
            if env_scalp_sim_ai_holding_critical_cooldown is not None
            else config.SCALP_SIM_AI_HOLDING_CRITICAL_COOLDOWN_SEC,
            SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC=env_scalp_sim_ai_holding_max_cooldown
            if env_scalp_sim_ai_holding_max_cooldown is not None
            else config.SCALP_SIM_AI_HOLDING_MAX_COOLDOWN_SEC,
            SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED=env_scalp_sim_ai_deferred_review_enabled
            if env_scalp_sim_ai_deferred_review_enabled is not None
            else config.SCALP_SIM_AI_DEFERRED_REVIEW_ENABLED,
            SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT=env_scalp_sim_ai_hard_critical_min_loss
            if env_scalp_sim_ai_hard_critical_min_loss is not None
            else config.SCALP_SIM_AI_HARD_CRITICAL_MIN_LOSS_PCT,
            SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED=env_scalp_sim_ai_soft_loss_defer_enabled
            if env_scalp_sim_ai_soft_loss_defer_enabled is not None
            else config.SCALP_SIM_AI_SOFT_LOSS_DEFER_ENABLED,
            SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED=env_scalp_sim_ai_safe_profit_bypass_enabled
            if env_scalp_sim_ai_safe_profit_bypass_enabled is not None
            else config.SCALP_SIM_AI_SAFE_PROFIT_BYPASS_ENABLED,
            SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT=env_scalp_sim_ai_critical_drawdown
            if env_scalp_sim_ai_critical_drawdown is not None
            else config.SCALP_SIM_AI_CRITICAL_DRAWDOWN_PCT,
            SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED=env_scalp_sim_scale_in_window_enabled
            if env_scalp_sim_scale_in_window_enabled is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED,
            SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS=env_scalp_sim_scale_in_window_allowed_arms
            if env_scalp_sim_scale_in_window_allowed_arms is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_ALLOWED_ARMS,
            SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT=env_scalp_sim_scale_in_window_min_profit
            if env_scalp_sim_scale_in_window_min_profit is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_MIN_PROFIT_PCT,
            SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT=env_scalp_sim_scale_in_window_max_profit
            if env_scalp_sim_scale_in_window_max_profit is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_MAX_PROFIT_PCT,
            SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION=env_scalp_sim_scale_in_window_max_orders_position
            if env_scalp_sim_scale_in_window_max_orders_position is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_POSITION,
            SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY=env_scalp_sim_scale_in_window_max_orders_day
            if env_scalp_sim_scale_in_window_max_orders_day is not None
            else config.SCALP_SIM_SCALE_IN_WINDOW_MAX_ORDERS_PER_DAY,
            SCALP_SIM_PANIC_LIFECYCLE_ENABLED=env_scalp_sim_panic_lifecycle_enabled
            if env_scalp_sim_panic_lifecycle_enabled is not None
            else config.SCALP_SIM_PANIC_LIFECYCLE_ENABLED,
            SCALP_SIM_PANIC_ENTRY_BLOCK_ENABLED=env_scalp_sim_panic_entry_block_enabled
            if env_scalp_sim_panic_entry_block_enabled is not None
            else config.SCALP_SIM_PANIC_ENTRY_BLOCK_ENABLED,
            SCALP_SIM_PANIC_SCALE_IN_BLOCK_ENABLED=env_scalp_sim_panic_scale_in_block_enabled
            if env_scalp_sim_panic_scale_in_block_enabled is not None
            else config.SCALP_SIM_PANIC_SCALE_IN_BLOCK_ENABLED,
            SCALP_SIM_PANIC_HOLDING_EXIT_ENABLED=env_scalp_sim_panic_holding_exit_enabled
            if env_scalp_sim_panic_holding_exit_enabled is not None
            else config.SCALP_SIM_PANIC_HOLDING_EXIT_ENABLED,
            SCALP_SIM_PANIC_PARTIAL_SELL_ENABLED=env_scalp_sim_panic_partial_sell_enabled
            if env_scalp_sim_panic_partial_sell_enabled is not None
            else config.SCALP_SIM_PANIC_PARTIAL_SELL_ENABLED,
            SCALP_SIM_PANIC_FORCE_NOOP=env_scalp_sim_panic_force_noop
            if env_scalp_sim_panic_force_noop is not None
            else config.SCALP_SIM_PANIC_FORCE_NOOP,
            SCALP_SIM_PANIC_BLOCK_ENTRY_LEVEL=env_scalp_sim_panic_block_entry_level
            if env_scalp_sim_panic_block_entry_level is not None
            else config.SCALP_SIM_PANIC_BLOCK_ENTRY_LEVEL,
            SCALP_SIM_PANIC_DISABLE_SCALE_IN_LEVEL=env_scalp_sim_panic_disable_scale_in_level
            if env_scalp_sim_panic_disable_scale_in_level is not None
            else config.SCALP_SIM_PANIC_DISABLE_SCALE_IN_LEVEL,
            SCALP_SIM_PANIC_BOTTOMING_ENTRY_ENABLED=env_scalp_sim_panic_bottoming_entry_enabled
            if env_scalp_sim_panic_bottoming_entry_enabled is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_ENTRY_ENABLED,
            SCALP_SIM_PANIC_BOTTOMING_ENTRY_MAX_LEVEL=env_scalp_sim_panic_bottoming_entry_max_level
            if env_scalp_sim_panic_bottoming_entry_max_level is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_ENTRY_MAX_LEVEL,
            SCALP_SIM_PANIC_BOTTOMING_MIN_AI_SCORE=env_scalp_sim_panic_bottoming_min_ai_score
            if env_scalp_sim_panic_bottoming_min_ai_score is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_MIN_AI_SCORE,
            SCALP_SIM_PANIC_BOTTOMING_MIN_BUY_PRESSURE=env_scalp_sim_panic_bottoming_min_buy_pressure
            if env_scalp_sim_panic_bottoming_min_buy_pressure is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_MIN_BUY_PRESSURE,
            SCALP_SIM_PANIC_BOTTOMING_MAX_DISTANCE_FROM_HIGH_PCT=env_scalp_sim_panic_bottoming_max_distance
            if env_scalp_sim_panic_bottoming_max_distance is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_MAX_DISTANCE_FROM_HIGH_PCT,
            SCALP_SIM_PANIC_BOTTOMING_MIN_STRENGTH=env_scalp_sim_panic_bottoming_min_strength
            if env_scalp_sim_panic_bottoming_min_strength is not None
            else config.SCALP_SIM_PANIC_BOTTOMING_MIN_STRENGTH,
            SCALP_SIM_PANIC_MIN_REMAINING_QTY=env_scalp_sim_panic_min_remaining_qty
            if env_scalp_sim_panic_min_remaining_qty is not None
            else config.SCALP_SIM_PANIC_MIN_REMAINING_QTY,
            SCALP_SIM_PANIC_MAX_PARTIAL_COUNT_PER_EPOCH=env_scalp_sim_panic_max_partial_count
            if env_scalp_sim_panic_max_partial_count is not None
            else config.SCALP_SIM_PANIC_MAX_PARTIAL_COUNT_PER_EPOCH,
            SCALP_SIM_PANIC_CONTEXT_MAX_AGE_SEC=env_scalp_sim_panic_context_max_age
            if env_scalp_sim_panic_context_max_age is not None
            else config.SCALP_SIM_PANIC_CONTEXT_MAX_AGE_SEC,
            SCALP_SIM_PANIC_FALLBACK_SLIPPAGE_BPS=env_scalp_sim_panic_fallback_slippage
            if env_scalp_sim_panic_fallback_slippage is not None
            else config.SCALP_SIM_PANIC_FALLBACK_SLIPPAGE_BPS,
            SCALP_SIM_PANIC_BROKEN_LIQUIDITY_HAIRCUT_BPS=env_scalp_sim_panic_broken_liquidity_haircut
            if env_scalp_sim_panic_broken_liquidity_haircut is not None
            else config.SCALP_SIM_PANIC_BROKEN_LIQUIDITY_HAIRCUT_BPS,
            SIM_VIRTUAL_BUDGET_KRW=env_sim_virtual_budget_krw
            if env_sim_virtual_budget_krw is not None
            else config.SIM_VIRTUAL_BUDGET_KRW,
            SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC=env_scalp_live_simulator_timeout
            if env_scalp_live_simulator_timeout is not None
            else config.SCALP_LIVE_SIMULATOR_ENTRY_TIMEOUT_SEC,
            STAT_ACTION_DECISION_SNAPSHOT_ENABLED=env_stat_action_snapshot_enabled
            if env_stat_action_snapshot_enabled is not None
            else config.STAT_ACTION_DECISION_SNAPSHOT_ENABLED,
            STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC=env_stat_action_snapshot_min_interval
            if env_stat_action_snapshot_min_interval is not None
            else config.STAT_ACTION_DECISION_SNAPSHOT_MIN_INTERVAL_SEC,
            SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED=env_scalping_initial_entry_qty_cap_enabled
            if env_scalping_initial_entry_qty_cap_enabled is not None
            else config.SCALPING_INITIAL_ENTRY_QTY_CAP_ENABLED,
            SCALPING_INITIAL_ENTRY_MAX_QTY=env_scalping_initial_entry_max_qty
            if env_scalping_initial_entry_max_qty is not None
            else config.SCALPING_INITIAL_ENTRY_MAX_QTY,
            BUY_SIDE_TIME_BLOCK_ENABLED=env_buy_side_time_block_enabled
            if env_buy_side_time_block_enabled is not None
            else config.BUY_SIDE_TIME_BLOCK_ENABLED,
            BUY_SIDE_TIME_BLOCK_UNTIL_HHMM=env_buy_side_time_block_until
            if env_buy_side_time_block_until is not None
            else config.BUY_SIDE_TIME_BLOCK_UNTIL_HHMM,
            SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED=env_scale_in_price_resolver_enabled
            if env_scale_in_price_resolver_enabled is not None
            else config.SCALPING_SCALE_IN_PRICE_RESOLVER_ENABLED,
            SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED=env_scale_in_dynamic_qty_enabled
            if env_scale_in_dynamic_qty_enabled is not None
            else config.SCALPING_SCALE_IN_DYNAMIC_QTY_ENABLED,
            SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP=env_scale_in_effective_qty_cap
            if env_scale_in_effective_qty_cap is not None
            else config.SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP,
            SCALPING_SCALE_IN_MAX_SPREAD_BPS=env_scale_in_max_spread_bps
            if env_scale_in_max_spread_bps is not None
            else config.SCALPING_SCALE_IN_MAX_SPREAD_BPS,
            SCALPING_PYRAMID_PRICE_GUARD_ENABLED=env_pyramid_price_guard_enabled
            if env_pyramid_price_guard_enabled is not None
            else config.SCALPING_PYRAMID_PRICE_GUARD_ENABLED,
            SCALPING_PYRAMID_MAX_SPREAD_BPS=env_pyramid_max_spread_bps
            if env_pyramid_max_spread_bps is not None
            else config.SCALPING_PYRAMID_MAX_SPREAD_BPS,
            SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS=env_pyramid_max_micro_vwap_bps
            if env_pyramid_max_micro_vwap_bps is not None
            else config.SCALPING_PYRAMID_MAX_MICRO_VWAP_BPS,
            SCALPING_PYRAMID_MIN_AI_SCORE=env_pyramid_min_ai_score
            if env_pyramid_min_ai_score is not None
            else config.SCALPING_PYRAMID_MIN_AI_SCORE,
            SCALPING_PYRAMID_MIN_BUY_PRESSURE=env_pyramid_min_buy_pressure
            if env_pyramid_min_buy_pressure is not None
            else config.SCALPING_PYRAMID_MIN_BUY_PRESSURE,
            SCALPING_PYRAMID_MIN_TICK_ACCEL=env_pyramid_min_tick_accel
            if env_pyramid_min_tick_accel is not None
            else config.SCALPING_PYRAMID_MIN_TICK_ACCEL,
            SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED=env_scalping_pyramid_zero_qty_stage1_enabled
            if env_scalping_pyramid_zero_qty_stage1_enabled is not None
            else config.SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED,
            SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED=env_same_symbol_loss_reentry_cooldown_enabled
            if env_same_symbol_loss_reentry_cooldown_enabled is not None
            else config.SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_ENABLED,
            SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC=env_same_symbol_loss_reentry_cooldown_sec
            if env_same_symbol_loss_reentry_cooldown_sec is not None
            else config.SCALP_SAME_SYMBOL_LOSS_REENTRY_COOLDOWN_SEC,
        )

    env_openai_json_deterministic = _env_bool("KORSTOCKSCAN_OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED")
    env_openai_schema_registry = _env_bool("KORSTOCKSCAN_OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED")
    env_openai_transport_mode = str(os.getenv("KORSTOCKSCAN_OPENAI_TRANSPORT_MODE", "") or "").strip().lower()
    env_openai_ws_enabled = _env_bool("KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED")
    env_openai_ws_pool_size = _env_int("KORSTOCKSCAN_OPENAI_RESPONSES_WS_POOL_SIZE")
    env_openai_ws_timeout_ms = _env_int("KORSTOCKSCAN_OPENAI_RESPONSES_WS_TIMEOUT_MS")
    env_openai_scanner_report_timeout_ms = _env_int("KORSTOCKSCAN_OPENAI_SCANNER_REPORT_TIMEOUT_MS")
    env_openai_overnight_timeout_ms = _env_int("KORSTOCKSCAN_OPENAI_OVERNIGHT_TIMEOUT_MS")
    env_openai_max_output_tokens = _env_int("KORSTOCKSCAN_OPENAI_RESPONSES_MAX_OUTPUT_TOKENS")
    env_openai_reasoning_effort = _env_str("KORSTOCKSCAN_OPENAI_REASONING_EFFORT")
    env_openai_ws_late_discard = _env_bool("KORSTOCKSCAN_OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED")
    env_openai_entry_timeout_reject = _env_bool("KORSTOCKSCAN_OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED")
    env_openai_previous_response_id = _env_bool("KORSTOCKSCAN_OPENAI_PREVIOUS_RESPONSE_ID_ENABLED")
    env_openai_threshold_correction_model = _env_str("KORSTOCKSCAN_GPT_THRESHOLD_CORRECTION_MODEL")
    env_openai_threshold_correction_fallback_models = _env_csv_tuple(
        "KORSTOCKSCAN_GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS"
    )
    if (
        env_openai_json_deterministic is not None
        or env_openai_schema_registry is not None
        or env_openai_transport_mode
        or env_openai_ws_enabled is not None
        or env_openai_ws_pool_size is not None
        or env_openai_ws_timeout_ms is not None
        or env_openai_scanner_report_timeout_ms is not None
        or env_openai_overnight_timeout_ms is not None
        or env_openai_max_output_tokens is not None
        or env_openai_reasoning_effort is not None
        or env_openai_ws_late_discard is not None
        or env_openai_entry_timeout_reject is not None
        or env_openai_previous_response_id is not None
        or env_openai_threshold_correction_model is not None
        or env_openai_threshold_correction_fallback_models is not None
    ):
        config = replace(
            config,
            OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED=env_openai_json_deterministic
            if env_openai_json_deterministic is not None
            else config.OPENAI_JSON_DETERMINISTIC_CONFIG_ENABLED,
            OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED=env_openai_schema_registry
            if env_openai_schema_registry is not None
            else config.OPENAI_RESPONSE_SCHEMA_REGISTRY_ENABLED,
            OPENAI_TRANSPORT_MODE=env_openai_transport_mode or config.OPENAI_TRANSPORT_MODE,
            OPENAI_RESPONSES_WS_ENABLED=env_openai_ws_enabled
            if env_openai_ws_enabled is not None
            else config.OPENAI_RESPONSES_WS_ENABLED,
            OPENAI_RESPONSES_WS_POOL_SIZE=env_openai_ws_pool_size
            if env_openai_ws_pool_size is not None
            else config.OPENAI_RESPONSES_WS_POOL_SIZE,
            OPENAI_RESPONSES_WS_TIMEOUT_MS=env_openai_ws_timeout_ms
            if env_openai_ws_timeout_ms is not None
            else config.OPENAI_RESPONSES_WS_TIMEOUT_MS,
            OPENAI_SCANNER_REPORT_TIMEOUT_MS=env_openai_scanner_report_timeout_ms
            if env_openai_scanner_report_timeout_ms is not None
            else config.OPENAI_SCANNER_REPORT_TIMEOUT_MS,
            OPENAI_OVERNIGHT_TIMEOUT_MS=env_openai_overnight_timeout_ms
            if env_openai_overnight_timeout_ms is not None
            else config.OPENAI_OVERNIGHT_TIMEOUT_MS,
            OPENAI_RESPONSES_MAX_OUTPUT_TOKENS=env_openai_max_output_tokens
            if env_openai_max_output_tokens is not None
            else config.OPENAI_RESPONSES_MAX_OUTPUT_TOKENS,
            OPENAI_REASONING_EFFORT=env_openai_reasoning_effort
            if env_openai_reasoning_effort is not None
            else config.OPENAI_REASONING_EFFORT,
            OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED=env_openai_ws_late_discard
            if env_openai_ws_late_discard is not None
            else config.OPENAI_RESPONSES_WS_LATE_DISCARD_ENABLED,
            OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED=env_openai_entry_timeout_reject
            if env_openai_entry_timeout_reject is not None
            else config.OPENAI_ENTRY_TIMEOUT_REJECT_ENABLED,
            OPENAI_PREVIOUS_RESPONSE_ID_ENABLED=env_openai_previous_response_id
            if env_openai_previous_response_id is not None
            else config.OPENAI_PREVIOUS_RESPONSE_ID_ENABLED,
            GPT_THRESHOLD_CORRECTION_MODEL=env_openai_threshold_correction_model
            if env_openai_threshold_correction_model is not None
            else config.GPT_THRESHOLD_CORRECTION_MODEL,
            GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS=env_openai_threshold_correction_fallback_models
            if env_openai_threshold_correction_fallback_models is not None
            else config.GPT_THRESHOLD_CORRECTION_FALLBACK_MODELS,
        )

    env_scalp_entry_adm_advisory_enabled = _env_bool("KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED")
    env_scalp_entry_adm_runtime_bias_enabled = _env_bool("KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED")
    env_scalp_entry_adm_hypothesis_fallback_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED"
    )
    env_scalp_entry_adm_hypothesis_force_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED"
    )
    env_scalp_entry_adm_negative_ev_block_enabled = _env_bool(
        "KORSTOCKSCAN_SCALP_ENTRY_ADM_NEGATIVE_EV_BLOCK_ENABLED"
    )
    env_scalp_entry_adm_negative_ev_force_wait_threshold = _env_float(
        "KORSTOCKSCAN_SCALP_ENTRY_ADM_NEGATIVE_EV_FORCE_WAIT_THRESHOLD_PCT"
    )
    env_scalp_entry_adm_min_bucket_sample = _env_int("KORSTOCKSCAN_SCALP_ENTRY_ADM_MIN_BUCKET_SAMPLE")
    env_scalp_entry_adm_min_joined_sample = _env_int("KORSTOCKSCAN_SCALP_ENTRY_ADM_MIN_JOINED_SAMPLE")
    env_lifecycle_decision_matrix_enabled = _env_bool("KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_ENABLED")
    env_lifecycle_decision_matrix_policy_file = _env_str("KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_FILE")
    env_lifecycle_decision_matrix_policy_version = _env_str("KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_POLICY_VERSION")
    env_lifecycle_decision_matrix_promote_enabled = _env_bool(
        "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED"
    )
    env_lifecycle_decision_matrix_max_promotes = _env_int(
        "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY"
    )
    env_lifecycle_decision_matrix_min_confidence = _env_float(
        "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE"
    )
    env_lifecycle_decision_matrix_runtime_effect_enabled = _env_bool(
        "KORSTOCKSCAN_LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED"
    )
    env_lifecycle_ai_context_enabled = _env_bool("KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_ENABLED")
    env_lifecycle_ai_context_file = _env_str("KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_FILE")
    env_lifecycle_ai_context_version = _env_str("KORSTOCKSCAN_LIFECYCLE_AI_CONTEXT_VERSION")
    env_lifecycle_bucket_discovery_enabled = _env_bool("KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_ENABLED")
    env_lifecycle_bucket_discovery_policy_file = _env_str(
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE"
    )
    env_lifecycle_bucket_discovery_policy_version = _env_str(
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION"
    )
    env_lifecycle_bucket_discovery_live_auto_apply_enabled = _env_bool(
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED"
    )
    env_scalp_loss_fallback_enabled = _env_bool("KORSTOCKSCAN_SCALP_LOSS_FALLBACK_ENABLED")
    env_scalp_loss_fallback_observe_only = _env_bool("KORSTOCKSCAN_SCALP_LOSS_FALLBACK_OBSERVE_ONLY")
    env_holding_exit_matrix_advisory_enabled = _env_bool("KORSTOCKSCAN_HOLDING_EXIT_MATRIX_ADVISORY_ENABLED")
    env_holding_exit_matrix_runtime_bias_enabled = _env_bool(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED"
    )
    env_holding_exit_matrix_exit_to_hold_enabled = _env_bool(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED"
    )
    env_holding_exit_matrix_trim_to_hold_enabled = _env_bool(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED"
    )
    env_holding_exit_matrix_hold_to_exit_enabled = _env_bool(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_HOLD_TO_EXIT_ENABLED"
    )
    env_holding_exit_matrix_scale_in_bias_enabled = _env_bool(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED"
    )
    env_holding_exit_matrix_avg_down_min_profit = _env_float(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT"
    )
    env_holding_exit_matrix_avg_down_max_profit = _env_float(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT"
    )
    env_holding_exit_matrix_avg_down_min_ai = _env_int(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE"
    )
    env_holding_exit_matrix_avg_down_min_held = _env_int(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_HELD_SEC"
    )
    env_holding_exit_matrix_avg_down_max_held = _env_int(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_HELD_SEC"
    )
    env_holding_exit_matrix_pyramid_min_profit = _env_float(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT"
    )
    env_holding_exit_matrix_pyramid_min_ai = _env_int(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE"
    )
    env_holding_exit_matrix_pyramid_max_drawdown = _env_float(
        "KORSTOCKSCAN_HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT"
    )
    env_holding_flow_override_enabled = _env_bool("KORSTOCKSCAN_HOLDING_FLOW_OVERRIDE_ENABLED")
    env_holding_flow_worsen = _env_float("KORSTOCKSCAN_HOLDING_FLOW_OVERRIDE_WORSEN_PCT")
    env_holding_flow_max_defer = _env_int("KORSTOCKSCAN_HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC")
    env_holding_flow_ofi_smoothing_enabled = _env_bool("KORSTOCKSCAN_HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED")
    env_holding_flow_ofi_bearish_confirm_worsen = _env_float(
        "KORSTOCKSCAN_HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT"
    )
    env_holding_flow_min_interval = _env_int("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC")
    env_holding_flow_max_interval = _env_int("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC")
    env_holding_flow_price_trigger = _env_float("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT")
    env_holding_flow_tick_limit = _env_int("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_TICK_LIMIT")
    env_holding_flow_candle_limit = _env_int("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_CANDLE_LIMIT")
    env_holding_flow_max_ws_age = _env_float("KORSTOCKSCAN_HOLDING_FLOW_REVIEW_MAX_WS_AGE_SEC")
    if (
        env_scalp_entry_adm_advisory_enabled is not None
        or env_scalp_entry_adm_runtime_bias_enabled is not None
        or env_scalp_entry_adm_hypothesis_fallback_enabled is not None
        or env_scalp_entry_adm_hypothesis_force_enabled is not None
        or env_scalp_entry_adm_negative_ev_block_enabled is not None
        or env_scalp_entry_adm_negative_ev_force_wait_threshold is not None
        or env_scalp_entry_adm_min_bucket_sample is not None
        or env_scalp_entry_adm_min_joined_sample is not None
        or env_lifecycle_decision_matrix_enabled is not None
        or env_lifecycle_decision_matrix_policy_file is not None
        or env_lifecycle_decision_matrix_policy_version is not None
        or env_lifecycle_decision_matrix_promote_enabled is not None
        or env_lifecycle_decision_matrix_max_promotes is not None
        or env_lifecycle_decision_matrix_min_confidence is not None
        or env_lifecycle_decision_matrix_runtime_effect_enabled is not None
        or env_lifecycle_ai_context_enabled is not None
        or env_lifecycle_ai_context_file is not None
        or env_lifecycle_ai_context_version is not None
        or env_lifecycle_bucket_discovery_enabled is not None
        or env_lifecycle_bucket_discovery_policy_file is not None
        or env_lifecycle_bucket_discovery_policy_version is not None
        or env_lifecycle_bucket_discovery_live_auto_apply_enabled is not None
        or env_scalp_loss_fallback_enabled is not None
        or env_scalp_loss_fallback_observe_only is not None
        or env_holding_exit_matrix_advisory_enabled is not None
        or env_holding_exit_matrix_runtime_bias_enabled is not None
        or env_holding_exit_matrix_exit_to_hold_enabled is not None
        or env_holding_exit_matrix_trim_to_hold_enabled is not None
        or env_holding_exit_matrix_hold_to_exit_enabled is not None
        or env_holding_exit_matrix_scale_in_bias_enabled is not None
        or env_holding_exit_matrix_avg_down_min_profit is not None
        or env_holding_exit_matrix_avg_down_max_profit is not None
        or env_holding_exit_matrix_avg_down_min_ai is not None
        or env_holding_exit_matrix_avg_down_min_held is not None
        or env_holding_exit_matrix_avg_down_max_held is not None
        or env_holding_exit_matrix_pyramid_min_profit is not None
        or env_holding_exit_matrix_pyramid_min_ai is not None
        or env_holding_exit_matrix_pyramid_max_drawdown is not None
        or env_holding_flow_override_enabled is not None
        or env_holding_flow_worsen is not None
        or env_holding_flow_max_defer is not None
        or env_holding_flow_ofi_smoothing_enabled is not None
        or env_holding_flow_ofi_bearish_confirm_worsen is not None
        or env_holding_flow_min_interval is not None
        or env_holding_flow_max_interval is not None
        or env_holding_flow_price_trigger is not None
        or env_holding_flow_tick_limit is not None
        or env_holding_flow_candle_limit is not None
        or env_holding_flow_max_ws_age is not None
    ):
        config = replace(
            config,
            SCALP_ENTRY_ADM_ADVISORY_ENABLED=env_scalp_entry_adm_advisory_enabled
            if env_scalp_entry_adm_advisory_enabled is not None
            else config.SCALP_ENTRY_ADM_ADVISORY_ENABLED,
            SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=env_scalp_entry_adm_runtime_bias_enabled
            if env_scalp_entry_adm_runtime_bias_enabled is not None
            else config.SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED,
            SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED=env_scalp_entry_adm_hypothesis_fallback_enabled
            if env_scalp_entry_adm_hypothesis_fallback_enabled is not None
            else config.SCALP_ENTRY_ADM_HYPOTHESIS_FALLBACK_ENABLED,
            SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED=env_scalp_entry_adm_hypothesis_force_enabled
            if env_scalp_entry_adm_hypothesis_force_enabled is not None
            else config.SCALP_ENTRY_ADM_HYPOTHESIS_FORCE_ENABLED,
            SCALP_ENTRY_ADM_NEGATIVE_EV_BLOCK_ENABLED=env_scalp_entry_adm_negative_ev_block_enabled
            if env_scalp_entry_adm_negative_ev_block_enabled is not None
            else config.SCALP_ENTRY_ADM_NEGATIVE_EV_BLOCK_ENABLED,
            SCALP_ENTRY_ADM_NEGATIVE_EV_FORCE_WAIT_THRESHOLD_PCT=env_scalp_entry_adm_negative_ev_force_wait_threshold
            if env_scalp_entry_adm_negative_ev_force_wait_threshold is not None
            else config.SCALP_ENTRY_ADM_NEGATIVE_EV_FORCE_WAIT_THRESHOLD_PCT,
            SCALP_ENTRY_ADM_MIN_BUCKET_SAMPLE=env_scalp_entry_adm_min_bucket_sample
            if env_scalp_entry_adm_min_bucket_sample is not None
            else config.SCALP_ENTRY_ADM_MIN_BUCKET_SAMPLE,
            SCALP_ENTRY_ADM_MIN_JOINED_SAMPLE=env_scalp_entry_adm_min_joined_sample
            if env_scalp_entry_adm_min_joined_sample is not None
            else config.SCALP_ENTRY_ADM_MIN_JOINED_SAMPLE,
            LIFECYCLE_DECISION_MATRIX_ENABLED=env_lifecycle_decision_matrix_enabled
            if env_lifecycle_decision_matrix_enabled is not None
            else config.LIFECYCLE_DECISION_MATRIX_ENABLED,
            LIFECYCLE_DECISION_MATRIX_POLICY_FILE=env_lifecycle_decision_matrix_policy_file
            if env_lifecycle_decision_matrix_policy_file is not None
            else config.LIFECYCLE_DECISION_MATRIX_POLICY_FILE,
            LIFECYCLE_DECISION_MATRIX_POLICY_VERSION=env_lifecycle_decision_matrix_policy_version
            if env_lifecycle_decision_matrix_policy_version is not None
            else config.LIFECYCLE_DECISION_MATRIX_POLICY_VERSION,
            LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED=env_lifecycle_decision_matrix_promote_enabled
            if env_lifecycle_decision_matrix_promote_enabled is not None
            else config.LIFECYCLE_DECISION_MATRIX_PROMOTE_ENABLED,
            LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY=env_lifecycle_decision_matrix_max_promotes
            if env_lifecycle_decision_matrix_max_promotes is not None
            else config.LIFECYCLE_DECISION_MATRIX_MAX_PROMOTES_PER_DAY,
            LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE=env_lifecycle_decision_matrix_min_confidence
            if env_lifecycle_decision_matrix_min_confidence is not None
            else config.LIFECYCLE_DECISION_MATRIX_MIN_STAGE_CONFIDENCE,
            LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED=env_lifecycle_decision_matrix_runtime_effect_enabled
            if env_lifecycle_decision_matrix_runtime_effect_enabled is not None
            else config.LIFECYCLE_DECISION_MATRIX_RUNTIME_EFFECT_ENABLED,
            LIFECYCLE_AI_CONTEXT_ENABLED=env_lifecycle_ai_context_enabled
            if env_lifecycle_ai_context_enabled is not None
            else config.LIFECYCLE_AI_CONTEXT_ENABLED,
            LIFECYCLE_AI_CONTEXT_FILE=env_lifecycle_ai_context_file
            if env_lifecycle_ai_context_file is not None
            else config.LIFECYCLE_AI_CONTEXT_FILE,
            LIFECYCLE_AI_CONTEXT_VERSION=env_lifecycle_ai_context_version
            if env_lifecycle_ai_context_version is not None
            else config.LIFECYCLE_AI_CONTEXT_VERSION,
            LIFECYCLE_BUCKET_DISCOVERY_ENABLED=env_lifecycle_bucket_discovery_enabled
            if env_lifecycle_bucket_discovery_enabled is not None
            else config.LIFECYCLE_BUCKET_DISCOVERY_ENABLED,
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE=env_lifecycle_bucket_discovery_policy_file
            if env_lifecycle_bucket_discovery_policy_file is not None
            else config.LIFECYCLE_BUCKET_DISCOVERY_POLICY_FILE,
            LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION=env_lifecycle_bucket_discovery_policy_version
            if env_lifecycle_bucket_discovery_policy_version is not None
            else config.LIFECYCLE_BUCKET_DISCOVERY_POLICY_VERSION,
            LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED=env_lifecycle_bucket_discovery_live_auto_apply_enabled
            if env_lifecycle_bucket_discovery_live_auto_apply_enabled is not None
            else config.LIFECYCLE_BUCKET_DISCOVERY_LIVE_AUTO_APPLY_ENABLED,
            SCALP_LOSS_FALLBACK_ENABLED=env_scalp_loss_fallback_enabled
            if env_scalp_loss_fallback_enabled is not None
            else config.SCALP_LOSS_FALLBACK_ENABLED,
            SCALP_LOSS_FALLBACK_OBSERVE_ONLY=env_scalp_loss_fallback_observe_only
            if env_scalp_loss_fallback_observe_only is not None
            else config.SCALP_LOSS_FALLBACK_OBSERVE_ONLY,
            HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=env_holding_exit_matrix_advisory_enabled
            if env_holding_exit_matrix_advisory_enabled is not None
            else config.HOLDING_EXIT_MATRIX_ADVISORY_ENABLED,
            HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=env_holding_exit_matrix_runtime_bias_enabled
            if env_holding_exit_matrix_runtime_bias_enabled is not None
            else config.HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED,
            HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED=env_holding_exit_matrix_exit_to_hold_enabled
            if env_holding_exit_matrix_exit_to_hold_enabled is not None
            else config.HOLDING_EXIT_MATRIX_EXIT_TO_HOLD_ENABLED,
            HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED=env_holding_exit_matrix_trim_to_hold_enabled
            if env_holding_exit_matrix_trim_to_hold_enabled is not None
            else config.HOLDING_EXIT_MATRIX_TRIM_TO_HOLD_ENABLED,
            HOLDING_EXIT_MATRIX_HOLD_TO_EXIT_ENABLED=env_holding_exit_matrix_hold_to_exit_enabled
            if env_holding_exit_matrix_hold_to_exit_enabled is not None
            else config.HOLDING_EXIT_MATRIX_HOLD_TO_EXIT_ENABLED,
            HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=env_holding_exit_matrix_scale_in_bias_enabled
            if env_holding_exit_matrix_scale_in_bias_enabled is not None
            else config.HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED,
            HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT=env_holding_exit_matrix_avg_down_min_profit
            if env_holding_exit_matrix_avg_down_min_profit is not None
            else config.HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_PROFIT_PCT,
            HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT=env_holding_exit_matrix_avg_down_max_profit
            if env_holding_exit_matrix_avg_down_max_profit is not None
            else config.HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_PROFIT_PCT,
            HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE=env_holding_exit_matrix_avg_down_min_ai
            if env_holding_exit_matrix_avg_down_min_ai is not None
            else config.HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_AI_SCORE,
            HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_HELD_SEC=env_holding_exit_matrix_avg_down_min_held
            if env_holding_exit_matrix_avg_down_min_held is not None
            else config.HOLDING_EXIT_MATRIX_AVG_DOWN_MIN_HELD_SEC,
            HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_HELD_SEC=env_holding_exit_matrix_avg_down_max_held
            if env_holding_exit_matrix_avg_down_max_held is not None
            else config.HOLDING_EXIT_MATRIX_AVG_DOWN_MAX_HELD_SEC,
            HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT=env_holding_exit_matrix_pyramid_min_profit
            if env_holding_exit_matrix_pyramid_min_profit is not None
            else config.HOLDING_EXIT_MATRIX_PYRAMID_MIN_PROFIT_PCT,
            HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE=env_holding_exit_matrix_pyramid_min_ai
            if env_holding_exit_matrix_pyramid_min_ai is not None
            else config.HOLDING_EXIT_MATRIX_PYRAMID_MIN_AI_SCORE,
            HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT=env_holding_exit_matrix_pyramid_max_drawdown
            if env_holding_exit_matrix_pyramid_max_drawdown is not None
            else config.HOLDING_EXIT_MATRIX_PYRAMID_MAX_DRAWDOWN_FROM_PEAK_PCT,
            HOLDING_FLOW_OVERRIDE_ENABLED=env_holding_flow_override_enabled
            if env_holding_flow_override_enabled is not None
            else config.HOLDING_FLOW_OVERRIDE_ENABLED,
            HOLDING_FLOW_OVERRIDE_WORSEN_PCT=env_holding_flow_worsen
            if env_holding_flow_worsen is not None
            else config.HOLDING_FLOW_OVERRIDE_WORSEN_PCT,
            HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC=env_holding_flow_max_defer
            if env_holding_flow_max_defer is not None
            else config.HOLDING_FLOW_OVERRIDE_MAX_DEFER_SEC,
            HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED=env_holding_flow_ofi_smoothing_enabled
            if env_holding_flow_ofi_smoothing_enabled is not None
            else config.HOLDING_FLOW_OFI_SMOOTHING_OVERRIDE_ENABLED,
            HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT=env_holding_flow_ofi_bearish_confirm_worsen
            if env_holding_flow_ofi_bearish_confirm_worsen is not None
            else config.HOLDING_FLOW_OFI_BEARISH_CONFIRM_WORSEN_PCT,
            HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC=env_holding_flow_min_interval
            if env_holding_flow_min_interval is not None
            else config.HOLDING_FLOW_REVIEW_MIN_INTERVAL_SEC,
            HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC=env_holding_flow_max_interval
            if env_holding_flow_max_interval is not None
            else config.HOLDING_FLOW_REVIEW_MAX_INTERVAL_SEC,
            HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT=env_holding_flow_price_trigger
            if env_holding_flow_price_trigger is not None
            else config.HOLDING_FLOW_REVIEW_PRICE_TRIGGER_PCT,
            HOLDING_FLOW_REVIEW_TICK_LIMIT=env_holding_flow_tick_limit
            if env_holding_flow_tick_limit is not None
            else config.HOLDING_FLOW_REVIEW_TICK_LIMIT,
            HOLDING_FLOW_REVIEW_CANDLE_LIMIT=env_holding_flow_candle_limit
            if env_holding_flow_candle_limit is not None
            else config.HOLDING_FLOW_REVIEW_CANDLE_LIMIT,
            HOLDING_FLOW_REVIEW_MAX_WS_AGE_SEC=env_holding_flow_max_ws_age
            if env_holding_flow_max_ws_age is not None
            else config.HOLDING_FLOW_REVIEW_MAX_WS_AGE_SEC,
        )

    if (
        env_pipeline_event_text_info_log_enabled is not None
        or env_pipeline_event_text_info_stage_allowlist is not None
        or env_watching_state_debug_log_enabled is not None
    ):
        config = replace(
            config,
            PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=env_pipeline_event_text_info_log_enabled
            if env_pipeline_event_text_info_log_enabled is not None
            else config.PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED,
            PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST=env_pipeline_event_text_info_stage_allowlist
            if env_pipeline_event_text_info_stage_allowlist is not None
            else config.PIPELINE_EVENT_TEXT_INFO_STAGE_ALLOWLIST,
            WATCHING_STATE_DEBUG_LOG_ENABLED=env_watching_state_debug_log_enabled
            if env_watching_state_debug_log_enabled is not None
            else config.WATCHING_STATE_DEBUG_LOG_ENABLED,
        )

    env_ed_enabled = _env_bool("KORSTOCKSCAN_ERROR_DETECTOR_ENABLED")
    env_ed_daemon_interval = _env_int("KORSTOCKSCAN_ERROR_DETECTOR_DAEMON_INTERVAL_SEC")
    env_ed_process_restart_grace = _env_int("KORSTOCKSCAN_ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC")
    env_ed_bot_window_enabled = _env_bool("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED")
    env_ed_bot_window_start = _env_str("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_START_HHMM")
    env_ed_bot_window_end = _env_str("KORSTOCKSCAN_ERROR_DETECTOR_BOT_EXPECTED_END_HHMM")
    env_ed_bot_startup_grace = _env_int("KORSTOCKSCAN_ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC")
    env_ed_cpu_busy_max_pct = _env_float("KORSTOCKSCAN_ERROR_DETECTOR_CPU_BUSY_MAX_PCT")
    env_ed_resource_max_sample_age = _env_int("KORSTOCKSCAN_ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC")
    env_ed_stale_lock_cleanup = _env_bool("KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED")
    env_ed_stale_lock_max_age = _env_int("KORSTOCKSCAN_ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC")
    env_ed_disk_log_rotate = _env_bool("KORSTOCKSCAN_ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED")
    if (
        env_ed_enabled is not None
        or env_ed_daemon_interval is not None
        or env_ed_process_restart_grace is not None
        or env_ed_bot_window_enabled is not None
        or env_ed_bot_window_start is not None
        or env_ed_bot_window_end is not None
        or env_ed_bot_startup_grace is not None
        or env_ed_cpu_busy_max_pct is not None
        or env_ed_resource_max_sample_age is not None
        or env_ed_stale_lock_cleanup is not None
        or env_ed_stale_lock_max_age is not None
        or env_ed_disk_log_rotate is not None
    ):
        config = replace(
            config,
            ERROR_DETECTOR_ENABLED=env_ed_enabled
            if env_ed_enabled is not None
            else config.ERROR_DETECTOR_ENABLED,
            ERROR_DETECTOR_DAEMON_INTERVAL_SEC=env_ed_daemon_interval
            if env_ed_daemon_interval is not None
            else config.ERROR_DETECTOR_DAEMON_INTERVAL_SEC,
            ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC=env_ed_process_restart_grace
            if env_ed_process_restart_grace is not None
            else config.ERROR_DETECTOR_PROCESS_RESTART_GRACE_SEC,
            ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED=env_ed_bot_window_enabled
            if env_ed_bot_window_enabled is not None
            else config.ERROR_DETECTOR_BOT_EXPECTED_RUNTIME_WINDOW_ENABLED,
            ERROR_DETECTOR_BOT_EXPECTED_START_HHMM=env_ed_bot_window_start
            if env_ed_bot_window_start is not None
            else config.ERROR_DETECTOR_BOT_EXPECTED_START_HHMM,
            ERROR_DETECTOR_BOT_EXPECTED_END_HHMM=env_ed_bot_window_end
            if env_ed_bot_window_end is not None
            else config.ERROR_DETECTOR_BOT_EXPECTED_END_HHMM,
            ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC=env_ed_bot_startup_grace
            if env_ed_bot_startup_grace is not None
            else config.ERROR_DETECTOR_BOT_STARTUP_GRACE_SEC,
            ERROR_DETECTOR_CPU_BUSY_MAX_PCT=env_ed_cpu_busy_max_pct
            if env_ed_cpu_busy_max_pct is not None
            else config.ERROR_DETECTOR_CPU_BUSY_MAX_PCT,
            ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC=env_ed_resource_max_sample_age
            if env_ed_resource_max_sample_age is not None
            else config.ERROR_DETECTOR_RESOURCE_MAX_SAMPLE_AGE_SEC,
            ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED=env_ed_stale_lock_cleanup
            if env_ed_stale_lock_cleanup is not None
            else config.ERROR_DETECTOR_STALE_LOCK_CLEANUP_ENABLED,
            ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC=env_ed_stale_lock_max_age
            if env_ed_stale_lock_max_age is not None
            else config.ERROR_DETECTOR_STALE_LOCK_MAX_AGE_SEC,
            ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED=env_ed_disk_log_rotate
            if env_ed_disk_log_rotate is not None
            else config.ERROR_DETECTOR_DISK_LOG_ROTATE_ENABLED,
        )
    return config


# 전역 싱글톤 인스턴스 생성
TRADING_RULES = _build_trading_rules()
