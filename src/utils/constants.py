# src/utils/constants.py
from dataclasses import dataclass
from pathlib import Path

# Pathlib을 사용하면 os.path.join 보다 훨씬 우아하게 경로를 관리할 수 있습니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
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

    # [매매 비중 설정] 전략별 주문 가능 현금 대비 1회 매수 투입 비율
    INVEST_RATIO_KOSPI: float = 0.25  # 1. 코스피 우량주 (25% - 묵직하게 스윙)
    INVEST_RATIO_KOSDAQ: float = 0.15  # 2. 코스닥 주도주 (15% - 중간 비중)
    INVEST_RATIO_SCALPING_MIN: float = 0.05  # 초단타 스캘핑 AI 점수 0일 때 최소 투자 비율 (5%)
    INVEST_RATIO_SCALPING_MAX: float = 0.15  # 초단타 스캘핑 AI 점수 100일 때 최대 투자 비율 (15%)

    # 💡 [신규 추가] 스윙 AI 동적 비중 조절용 (Min~Max)
    INVEST_RATIO_KOSDAQ_MIN: float = 0.05  # 코스닥 AI 점수 60점일 때 (5%)
    INVEST_RATIO_KOSDAQ_MAX: float = 0.15  # 코스닥 AI 점수 100점일 때 (15%)
    INVEST_RATIO_KOSPI_MIN: float = 0.10   # 코스피 우량주 AI 점수 60점일 때 (10%)
    INVEST_RATIO_KOSPI_MAX: float = 0.30   # 코스피 우량주 AI 점수 100점일 때 (30%)

    # 💡 [변경] 스윙 손절선 (백테스트 기준 -3.0% 반영)
    STOP_LOSS_BULL: float = -3.0  # 🏆 상승장 손절선 (최적화 결과 -3.0 반영)
    STOP_LOSS_BEAR: float = -3.0  # 🏆 하락장 손절선 (최적화 결과 -3.0 통일)
    STOP_LOSS_BREAKOUT: float = -1.5  # 돌파 실패 시 칼손절 (-1.5%)
    STOP_LOSS_BOTTOM: float = -4.0  # 바닥권 매물 소화 버티기용 (-4.0%)

    # 💡 [변경] 가변 익절 (Trailing Stop) 룰
    TRAILING_START_PCT: float = 2.5  # 🏆 방어선 가동 시작 수익률
    TRAILING_DRAWDOWN_PCT: float = 0.5  # 🏆 고점 대비 익절 하락폭 (%)
    MIN_PROFIT_PRESERVE: float = 1.5  # 어떤 흔들기가 와도 최소 +1.5% 수익은 무조건 보존


    # 💡 [신규] 초단타 스캐너 설정
    SCALP_TIME_LIMIT_MIN: int = 60  # 최대 보유 허용 시간 (60분)
    MIN_FEE_COVER: float = 0.3  # 세금(0.2%) + 수수료 보존용 최소 익절선 (0.3%)
    VPW_SCALP_LIMIT: int = 120  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    SCALP_TARGET: float = 1.5  # 초단타 익절 1.5%
    SCALP_STOP: float = -2.5  # 초단타 손절 -2.5%
    SCALP_TRAILING_LIMIT: float = 0.5  # 고가 대비 특정 비율(0.5%) 이상 밀리면 즉시 수익을 확정
    MIN_SCALP_LIQUIDITY: int = 500_000_000  # 최소 호가 잔량 대금 (5억)
    MAX_SCALP_SURGE_PCT: float = 20.0  # 초단타 진입 금지 급등률 (20%)
    MAX_INTRADAY_SURGE: float = 15.0  # 당일 시가 대비 최대 급등률 (15%)
    # [V3 스캘핑 동적 트레일링 전용 상수]
    SCALP_SAFE_PROFIT = 0.5            # 💡 [신규] 수수료/세금/슬리피지를 커버하는 최소 안전 마진 (이 선을 넘으면 무조건 수익 마감 모드 돌입)
    SCALP_TRAILING_LIMIT_STRONG = 0.8  # 💡 [신규] AI 점수가 75점 이상(수급 폭발)일 때 허용하는 고점 대비 눌림폭 (%)
    SCALP_TRAILING_LIMIT_WEAK = 0.4    # 💡 [신규] AI 점수가 75점 미만(수급 애매)일 때 타이트하게 끊어내는 고점 대비 눌림폭 (%)

    # 💡 [신규] 코스닥 스캐너 설정
    KOSDAQ_TARGET: float = 4.0  # 코스닥은 조금 더 높게 목표 (예: 4.0%)
    KOSDAQ_STOP: float = -2.5  # 타이트한 칼손절 적용
    VPW_KOSDAQ_LIMIT: int = 115  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    HOLDING_DAYS: int = 3  # KOSPI 최대 보유 영업일
    KOSDAQ_HOLDING_DAYS: int = 2  # 코스닥 최대 보유 영업일
    MAX_SWING_GAP_UP_PCT: float = 3.0  # 💡 [신규] 스윙 전략 아침 갭상승/급등 출발 시 추격 매수 방지 기준 (%)

    # ==========================================
    # 🎯 추가된 스나이퍼 매매/운영 세부 설정값
    # ==========================================
    BUY_SCORE_THRESHOLD: int = 75  # AI 봇이 매수 버튼을 누르는 최소 종합 점수
    BUY_SCORE_KOSDAQ_THRESHOLD: int = 80  # AI 봇이 KOSDAQ 매수 버튼을 누르는 최소 종합 점수
    VPW_STRONG_LIMIT: int = 115  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    VPW_STRONG_KOSDAQ_LIMIT: int = 120  # 확신도가 낮을 때 매수를 강행하기 위한 체결강도 허들(%)
    RALLY_TARGET_PCT: float = 5.0  # 신고가 돌파 시 기본 목표가 (%)
    ORDER_TIMEOUT_SEC: int = 30  # 미체결 주문 취소 대기 시간 (초)
    SCAN_INTERVAL_SEC: int = 1800  # 장중 스캐너 재가동 주기 (초 / 1800초 = 30분)
    MAX_WATCHING_SLOTS: int = 5  # 장중 감시 종목 최대 유지 개수

    # ==========================================
    # 🎯 유저권한별 기능 제한 설정값
    # ==========================================
    VIP_LIQUIDITY_THRESHOLD: int = 1_000_000_000  # VIP 전용 호가 잔량 대금 기준 (10억)
    VIP_PROB_THRESHOLD: float = 0.75  # VIP 전용 AI 확신도 기준 (0.75)
    VIP_MAX_INVEST_RATIO: float = 0.30  # VIP 전용 최대 투자 비율 (30%) 

    # ==========================================
    # 🎯 AI 엔진 제어값 (제미나이)
    # ==========================================
    GEMINI_ENGINE_MIN_INTERVAL: float = 0.5 # 구글 서버에 쏘는 최소 간격 (초 단위, 0.5초 = 500ms)
    AI_MAX_CONSECUTIVE_FAILURES: int = 5   # 연속 API 실패 시 AI 엔진 일시 중단 임계값
    AI_SCORE_THRESHOLD_KOSDAQ: int = 60    # KOSDAQ_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_SCORE_THRESHOLD_KOSPI: int = 60     # KOSPI_ML AI 점수 매수 보류 임계값 (60점 미만 보류)
    AI_WATCHING_COOLDOWN: int = 180  # 신규 진입 감시(WATCHING) 쿨타임 (초)
    # [AI 보유 종목 감시 쿨타임 설정 - 비용 절감형]
    AI_HOLDING_MIN_COOLDOWN = 15          # 💡 (기존 5초 -> 15초) 주가가 미친듯이 널뛰어도 최소 15초는 무조건 대기
    AI_HOLDING_MAX_COOLDOWN = 50          # 💡 (기존 30초 -> 50초) 평상시 횡보장에서는 50초에 딱 한 번만 AI 호출
    AI_HOLDING_CRITICAL_COOLDOWN = 10     # 💡 [신규 추가] 익절/손절 임박 구간에서는 20초마다 호출
    AI_WAIT_DROP_COOLDOWN = 300           # 💡 ai score 75점 이하 대기시간 300초

    # ==========================================
    # 🎯 AI 엔진 제어값 (OpenAI)
    # ==========================================
    GPT_FAST_MODEL = "gpt-4.1-mini"
    GPT_DEEP_MODEL = "gpt-4o"
    GPT_ENGINE_MIN_INTERVAL: float = 0.5 # OpenAI 서버에 쏘는 최소 간격 (초 단위, 0.5초 = 500ms)


# 전역 싱글톤 인스턴스 생성
TRADING_RULES = TradingConfig()
