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
CREDENTIALS_PATH = DATA_DIR / 'credentials.json'
DEV_PATH = DATA_DIR / 'config_dev.json'
UTILS_DIR = PROJECT_ROOT / 'src' / 'utils'
ENGINE_DIR = PROJECT_ROOT / 'src' / 'engine'
MODEL_DIR = PROJECT_ROOT / 'src' / 'model'
NOTIFY_DIR = PROJECT_ROOT / 'src' / 'notify'
# INTEGRATED_DB_PATH = DATA_DIR / 'korstockscan.db'
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
    ADD_JUDGMENT_LOCK_SEC: int = 20  # 추가매수 판단 락(스팸 판단 방지)

    # ==========================================
    # 3.2 추가매수(스캘핑) 설정
    # ==========================================
    SCALPING_ENABLE_AVG_DOWN: bool = False
    SCALPING_MAX_AVG_DOWN_COUNT: int = 0
    SCALPING_MAX_PYRAMID_COUNT: int = 2
    SCALPING_AVG_DOWN_MIN_DROP_PCT: float = -3.0
    SCALPING_AVG_DOWN_MAX_DROP_PCT: float = -6.0
    SCALPING_PYRAMID_MIN_PROFIT_PCT: float = 1.5

    # ==========================================
    # 3.3 추가매수(스윙) 설정
    # ==========================================
    SWING_ENABLE_AVG_DOWN: bool = True
    SWING_MAX_AVG_DOWN_COUNT: int = 1
    SWING_MAX_PYRAMID_COUNT: int = 1
    SWING_AVG_DOWN_MIN_DROP_PCT: float = -5.0
    SWING_PYRAMID_MIN_PROFIT_PCT: float = 4.0
    BLOCK_SWING_AVG_DOWN_IN_BEAR: bool = True

    # [매매 비중 설정] 전략별 주문 가능 현금 대비 1회 매수 투입 비율
    INVEST_RATIO_KOSPI: float = 0.25  # DEPRECATED: MIN/MAX 비중으로 대체됨
    INVEST_RATIO_KOSDAQ: float = 0.15  # DEPRECATED: MIN/MAX 비중으로 대체됨
    INVEST_RATIO_SCALPING_MIN: float = 0.10  # 초단타 스캘핑 AI 점수 0일 때 최소 투자 비율 (10%)
    INVEST_RATIO_SCALPING_MAX: float = 0.30  # 초단타 스캘핑 AI 점수 100일 때 최대 투자 비율 (30%)
    SCALPING_MAX_BUY_BUDGET_KRW: int = 1_000_000  # 스캘핑 신규 진입 1회 절대 투자금 상한

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
    SCALP_AI_EARLY_EXIT_MAX_SCORE: int = 35  # AI 하방 리스크 조기손절 점수 상한
    SCALP_AI_EARLY_EXIT_MIN_LOSS_PCT: float = -0.7  # 조기손절을 허용하는 최소 손실폭
    SCALP_AI_EARLY_EXIT_MIN_HOLD_SEC: int = 180  # 진입 직후 블라인드 타임(초)
    SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS: int = 3  # 연속 저점수 확인 횟수
    SCALP_AI_EARLY_EXIT_CONSECUTIVE_HITS_OPEN_RECLAIM: int = 4  # OPEN_RECLAIM 전용 조기손절 확인 횟수(완화)
    SCALP_AI_MOMENTUM_DECAY_SCORE_LIMIT: int = 45  # 이 값 미만일 때만 AI 모멘텀 둔화 익절 검토
    SCALP_AI_MOMENTUM_DECAY_MIN_HOLD_SEC: int = 90  # AI 모멘텀 둔화 익절 최소 보유시간(초)
    SCALP_PRESET_HARD_STOP_PCT: float = -0.7  # SCALP_PRESET_TP 기본 손절선
    SCALP_PRESET_HARD_STOP_GRACE_SEC: int = 0  # SCALP_PRESET_TP 공통 유예시간(초)
    SCALP_PRESET_HARD_STOP_EMERGENCY_PCT: float = -1.2  # 유예 중에도 강제 청산하는 비상 손절선
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_PCT: float = -0.7  # SCALP_BASE + fallback 전용 기본 손절선
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_GRACE_SEC: int = 35  # SCALP_BASE + fallback 전용 유예시간
    SCALP_PRESET_HARD_STOP_FALLBACK_BASE_EMERGENCY_PCT: float = -1.2  # SCALP_BASE + fallback 비상 손절선
    SCALP_FALLBACK_ENTRY_QTY_MULTIPLIER: float = 0.70  # 2026-04-09 canary: fallback 진입 수량 배율(한 축만 적용)
    SCALP_OPEN_RECLAIM_NEVER_GREEN_HOLD_SEC: int = 300  # OPEN_RECLAIM never-green 조기 정리 최소 보유시간
    SCALP_OPEN_RECLAIM_NEVER_GREEN_PEAK_MAX_PCT: float = 0.20  # OPEN_RECLAIM never-green 최대 허용 고점수익
    SCALP_OPEN_RECLAIM_NEAR_AI_EXIT_SCORE_BUFFER: int = 5  # OPEN_RECLAIM near_ai_exit 점수 여유폭
    SCALP_OPEN_RECLAIM_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC: int = 120  # OPEN_RECLAIM 양전환 이력 케이스 near_ai_exit 지속 필요시간
    SCALP_SCANNER_FALLBACK_NEVER_GREEN_HOLD_SEC: int = 420  # SCANNER fallback never-green 조기 정리 최소 보유시간
    SCALP_SCANNER_FALLBACK_NEVER_GREEN_PEAK_MAX_PCT: float = 0.20  # SCANNER fallback 최대 허용 고점수익
    SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SCORE_BUFFER: int = 8  # SCANNER fallback near_ai_exit 점수 여유폭
    SCALP_SCANNER_FALLBACK_NEAR_AI_EXIT_SUSTAIN_SEC: int = 120  # SCANNER fallback near_ai_exit 지속 필요시간
    SCALP_SCANNER_FALLBACK_RETRACE_NEAR_AI_EXIT_SUSTAIN_SEC: int = 150  # SCANNER fallback 양전환 이력 케이스 near_ai_exit 지속 필요시간
    SCALP_LATENCY_GUARD_CANARY_ENABLED: bool = True  # REJECT_DANGER 중 조건부 케이스만 fallback 허용
    SCALP_LATENCY_GUARD_CANARY_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # latency canary 적용 태그
    SCALP_LATENCY_GUARD_CANARY_MIN_SIGNAL_SCORE: float = 85.0  # latency canary 최소 AI 점수
    SCALP_LATENCY_GUARD_CANARY_MAX_WS_AGE_MS: int = 450  # latency canary 최대 ws_age
    SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS: int = 260  # latency canary 최대 ws_jitter
    SCALP_LATENCY_GUARD_CANARY_MAX_SPREAD_RATIO: float = 0.0100  # latency canary 최대 spread_ratio
    SCALP_LATENCY_GUARD_CANARY_ALLOWED_DANGER_REASONS: tuple = ()  # 비어 있으면 전체 허용, 값이 있으면 해당 danger reason만 canary 허용
    SCALP_DYNAMIC_STRENGTH_CANARY_ENABLED: bool = True  # dynamic strength 근소 미달 조건부 완화
    SCALP_DYNAMIC_STRENGTH_CANARY_TAGS: tuple = ("SCANNER", "VWAP_RECLAIM", "OPEN_RECLAIM")  # dynamic canary 적용 태그
    SCALP_DYNAMIC_STRENGTH_CANARY_ALLOWED_REASONS: tuple = (
        "below_exec_buy_ratio",
        "below_buy_ratio",
        "below_window_buy_value",
    )
    SCALP_DYNAMIC_STRENGTH_CANARY_MIN_BUY_VALUE_RATIO: float = 0.85  # buy_value 최소 허용 비율
    SCALP_DYNAMIC_STRENGTH_CANARY_BUY_RATIO_TOL: float = 0.03  # buy_ratio 부족 허용폭
    SCALP_DYNAMIC_STRENGTH_CANARY_EXEC_BUY_RATIO_TOL: float = 0.03  # exec_buy_ratio 부족 허용폭
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY: bool = True  # 공통 hard time stop은 shadow-only 관찰 고정
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES: tuple = (3, 5, 7)  # 공통 hard time stop shadow 후보 분(실전 미적용)
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MIN_LOSS_PCT: float = -0.7  # shadow 후보 기록 최소 손실폭
    SCALP_COMMON_HARD_TIME_STOP_SHADOW_MAX_PEAK_PCT: float = 0.20  # shadow 후보 기록 최대 고점수익(never-green 기준)
    SCALP_TRAILING_START_PCT: float = 0.6  # 초단타 트레일링 시작 수익률
    SCALP_TRAILING_LIMIT: float = 0.5  # DEPRECATED: STRONG/WEAK로 대체됨
    MIN_SCALP_LIQUIDITY: int = 500_000_000  # 최소 호가 잔량 대금 (5억)
    MAX_SCALP_SURGE_PCT: float = 20.0  # 초단타 진입 금지 급등률 (20%)
    MAX_INTRADAY_SURGE: float = 16.0  # 당일 시가 대비 최대 급등률 (1차 완화: 16%)
    # [V3 스캘핑 동적 트레일링 전용 상수]
    SCALP_SAFE_PROFIT = 0.5            # 💡 [신규] 수수료/세금/슬리피지를 커버하는 최소 안전 마진 (이 선을 넘으면 무조건 수익 마감 모드 돌입)
    SCALP_TRAILING_LIMIT_STRONG = 0.8  # 💡 [신규] AI 점수가 75점 이상(수급 폭발)일 때 허용하는 고점 대비 눌림폭 (%)
    SCALP_TRAILING_LIMIT_WEAK = 0.4    # 💡 [신규] AI 점수가 75점 미만(수급 애매)일 때 타이트하게 끊어내는 고점 대비 눌림폭 (%)

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
    SCALPING_OVERNIGHT_DECISION_TIME: str = "15:15:00"
    MARKET_CLOSE_TIME: str = "15:30:00"
    SYSTEM_SHUTDOWN_TIME: str = "20:00:00"

    # ==========================================
    # 🎯 유저권한별 기능 제한 설정값
    # ==========================================
    VIP_LIQUIDITY_THRESHOLD: int = 1_000_000_000  # keep: VIP 전용 호가 잔량 대금 기준 (10억)
    VIP_PROB_THRESHOLD: float = 0.75  # DEPRECATED: 런타임 미사용
    VIP_MAX_INVEST_RATIO: float = 0.30  # DEPRECATED: 런타임 미사용

    # ==========================================
    # 🎯 AI 엔진 제어값 (제미나이)
    # ==========================================
    AI_MODEL_TIER1: str = "models/gemini-3.1-flash-lite-preview"  # 초단타/조건검색용 초저지연 티어
    AI_MODEL_TIER2: str = "models/gemini-3-flash-preview"  # 스윙/실시간 리포트용 균형 티어
    AI_MODEL_TIER3: str = "models/gemini-3.1-pro-preview-customtools"  # 시장 브리핑/EOD용 심층 추론 티어
    GEMINI_ENGINE_MIN_INTERVAL: float = 0.5 # 구글 서버에 쏘는 최소 간격 (초 단위, 0.5초 = 500ms)
    AI_MAX_CONSECUTIVE_FAILURES: int = 5   # 연속 API 실패 시 AI 엔진 일시 중단 임계값
    AI_SCORE_THRESHOLD_KOSDAQ: int = 60    # KOSDAQ_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_SCORE_THRESHOLD_KOSPI: int = 60     # KOSPI_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_WATCHING_COOLDOWN: int = 180  # 신규 진입 감시(WATCHING) 쿨타임 (초)
    AI_WATCHING_75_PROMPT_SHADOW_ENABLED: bool = False  # 작업 4: 75 정합화 shadow canary (remote 전용)
    AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE: int = 75  # shadow 재평가 시작 점수
    AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE: int = 79  # shadow 재평가 종료 점수
    ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN: int = 60 * 20  # 게이트키퍼 '눌림 대기' 재평가 쿨다운
    ML_GATEKEEPER_REJECT_COOLDOWN: int = 60 * 60 * 2  # 게이트키퍼 '전량 회피' 계열 쿨다운
    ML_GATEKEEPER_NEUTRAL_COOLDOWN: int = 60 * 30  # 게이트키퍼 중립/애매 응답 재평가 쿨다운
    ML_GATEKEEPER_ERROR_COOLDOWN: int = 60 * 10  # 게이트키퍼 오류 재시도 쿨다운
    # [AI 보유 종목 감시 쿨타임 설정 - 비용 절감형]
    AI_HOLDING_MIN_COOLDOWN = 15          # 💡 (기존 5초 -> 15초) 주가가 미친듯이 널뛰어도 최소 15초는 무조건 대기
    AI_HOLDING_MAX_COOLDOWN = 50          # 💡 (기존 30초 -> 50초) 평상시 횡보장에서는 50초에 딱 한 번만 AI 호출
    AI_HOLDING_CRITICAL_COOLDOWN = 10     # 💡 [신규 추가] 익절/손절 임박 구간에서는 20초마다 호출
    AI_WAIT_DROP_COOLDOWN = 300           # 💡 ai score 75점 이하 대기시간 300초

    # ==========================================
    # 🎯 AI 엔진 제어값 (OpenAI)
    # ==========================================
    GPT_FAST_MODEL = "gpt-4.1-mini"
    GPT_DEEP_MODEL = "gpt-4.1-mini"
    GPT_REPORT_MODEL = "gpt-4.1-mini"
    GPT_ENABLE_SCALPING_DEEP_RECHECK: bool = False
    GPT_ENGINE_MIN_INTERVAL: float = 0.5 # OpenAI 서버에 쏘는 최소 간격 (초 단위, 0.5초 = 500ms)
    OPENAI_DUAL_PERSONA_ENABLED: bool = True
    OPENAI_DUAL_PERSONA_SHADOW_MODE: bool = True
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

    # ==========================================
    # 📝 로그 운영 설정
    # ==========================================
    MODULE_LOG_MAX_BYTES: int = 20 * 1024 * 1024  # 파일별 info/error 로그 최대 20MB
    MODULE_LOG_BACKUP_COUNT: int = 10  # 파일별 순환 보관 개수
    LOG_RETENTION_DAYS: int = 14  # 오래된 로그 자동 삭제 기준
    BOT_HISTORY_BACKUP_COUNT: int = 7  # 콘솔 히스토리 일별 보관 개수
    PIPELINE_EVENT_JSONL_ENABLED: bool = True
    PIPELINE_EVENT_SCHEMA_VERSION: int = 1


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
    if (
        env_ws_jitter is not None
        or env_ws_age is not None
        or env_spread_ratio is not None
        or env_allowed_danger_reasons is not None
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
        )

    env_prompt_shadow_enabled = _env_bool("AI_WATCHING_75_PROMPT_SHADOW_ENABLED")
    env_prompt_shadow_min = _env_int("AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE")
    env_prompt_shadow_max = _env_int("AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE")
    if (
        env_prompt_shadow_enabled is not None
        or env_prompt_shadow_min is not None
        or env_prompt_shadow_max is not None
    ):
        config = replace(
            config,
            AI_WATCHING_75_PROMPT_SHADOW_ENABLED=env_prompt_shadow_enabled
            if env_prompt_shadow_enabled is not None
            else config.AI_WATCHING_75_PROMPT_SHADOW_ENABLED,
            AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE=env_prompt_shadow_min
            if env_prompt_shadow_min is not None
            else config.AI_WATCHING_75_PROMPT_SHADOW_MIN_SCORE,
            AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE=env_prompt_shadow_max
            if env_prompt_shadow_max is not None
            else config.AI_WATCHING_75_PROMPT_SHADOW_MAX_SCORE,
        )
    return config


# 전역 싱글톤 인스턴스 생성
TRADING_RULES = _build_trading_rules()
