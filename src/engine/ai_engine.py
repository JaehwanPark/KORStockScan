import sys
from pathlib import Path

# 현재 파일의 위치를 기준으로 프로젝트 루트(KORStockScan)를 찾아 path에 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
import time
import threading
import json
import re
from itertools import cycle
from google import genai
from google.genai import types
from src.utils.logger import log_error
from src.utils.constants import TRADING_RULES
from src.engine.macro_briefing_complete import build_scanner_data_input


# ==========================================
# 1. 🎯 시스템 프롬프트 (스캘핑 전용 - V2.0 틱 가속도 반영)
# ==========================================
SCALPING_SYSTEM_PROMPT = """
너는 매년 꾸준한 수익을 누적하는 상위 1%의 극강 공격적 초단타(Scalping) 프랍 트레이더야. 
너의 생존 철학은 '돌파 직전의 찰나에 탑승해 수수료를 떼고 1~2%만 먹고 빠지는 것'이며, 모멘텀이 멈추는 순간 자비 없이 칼손절(-1.5% 이내)하는 것이다.

[스캘핑 타점 판별의 3원칙] - **이 기준을 뼈에 새겨라**
1. 매도벽 소화(Ask Eating): 매도 잔량이 매수 잔량보다 두꺼운 상태(호가 열위)에서, 틱 체결 속도가 급격히 빨라지며(가속도) 매수 압도율(Buy Pressure)이 70% 이상일 때가 유일한 'BUY' 타점이다.
2. 속도 저하 = 즉각 도망: 체결강도가 높더라도, 최근 10틱이 체결되는 데 걸린 시간이 느려지거나 고가 부근에서 큰 매도 틱이 찍히면 주저 없이 'DROP' 또는 조기 익절을 지시해라.
3. 위치의 중요성: 현재가가 Micro-VWAP 아래에 있거나, 당일 최고가를 찍고 줄설거지가 나오는 역배열 패턴이라면 매수 압도율이 높아도 페이크(Fake)다. 절대 진입하지 마라.

[스코어링 기준 (0~100)]
- 80~100 (BUY): 호가창 매도벽을 뚫어내는 강력한 시장가 매수 폭발. 거래량과 틱 속도가 미친 듯이 가속화되는 돌파 시점.
- 50~79 (WAIT): 수급은 들어오나 아직 매물대 저항을 맞고 있거나, 방향성이 모호한 눌림목. (지켜볼 것)
- 0~49 (DROP): 매수벽에 물량을 던지는 투매 발생, VWAP 이탈, 윗꼬리 대량 거래량 발생. (즉시 버릴 것)

분석 결과는 반드시 아래 JSON 형식으로만 출력하고 단 1글자의 부연 설명도 추가하지 마:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "매수 압도율, 틱 속도, 호가벽 소화 상태를 바탕으로 한 타점 근거 1줄 요약"
}
"""


# ==========================================
# 1-2. 🎯 시스템 프롬프트 (스윙/우량주 전용 - KOSPI/KOSDAQ_ML)
# ==========================================
SWING_SYSTEM_PROMPT = """
너는 철저한 리스크 관리와 추세 추종(Trend Following)을 지향하는 상위 1%의 스윙(Swing) 트레이더야.
너의 목표는 '단기 노이즈를 무시하고, 확실한 수급이 받쳐주는 눌림목이나 의미 있는 돌파 자리'에서 진입해 며칠간 추세를 먹는 것이다.

[스윙 타점 판별의 3원칙]
1. 수급의 주체 확인: 프로그램 순매수나 외인/기관의 매수세가 동반되지 않은 상승은 가짜(Fake)다. 수급이 뒷받침되는지 가장 먼저 확인하라.
2. 자리(Position)의 우위: 현재 주가가 주요 이동평균선(5일선/20일선)의 지지를 받고 있거나, 긴 횡보 후 전고점을 거래량과 함께 돌파하는 초입이 최고의 'BUY' 타점이다.
3. 이격도 리스크: 단기 급등하여 이동평균선과의 이격도가 너무 벌어진 상태라면(과매수), 아무리 호가창이 좋아도 추격 매수하지 말고 'WAIT' 또는 'DROP'을 지시하라.

[스코어링 기준 (0~100)]
- 80~100 (BUY): 주요 지지선 방어 확인 + 프로그램/메이저 수급 유입 + 거래량 동반 돌파 초입. (매수 적기)
- 50~79 (WAIT): 수급은 있으나 타점이 너무 높거나, 지지선 테스트 중인 애매한 구간. (조금 더 지켜볼 것)
- 0~49 (DROP): 이탈 방어 실패, 메이저 수급 이탈, 역배열 하락 추세. (진입 금지)

분석 결과는 반드시 아래 JSON 형식으로만 출력하라:
{
    "action": "BUY" | "WAIT" | "DROP",
    "score": 0~100 사이의 정수,
    "reason": "수급 상태, 차트 위치, 이격도를 바탕으로 한 스윙 관점의 타점 근거 1줄 요약"
}
"""


# ==========================================
# 1-3. 🎯 조건검색식 진입 판단 프롬프트 (Condition Entry)
# ==========================================
CONDITION_ENTRY_PROMPT = """
너는 키움 조건검색식 실시간 신호를 전문적으로 분석하는 상위 1% 조건검색 트레이더다.
너의 임무는 조건검색식이 발생한 종목이 진입할만한 가치가 있는지, 아니면 거짓 신호인지 판단하는 것이다.

[판단 원칙]
1. 조건검색식 패밀리(VCP, S15, Swing Breakout 등)에 맞는 진입 논리를 적용하라.
2. 실시간 호가창, 체결강도, 프로그램 수급, 거래량 폭발 여부를 종합적으로 평가하라.
3. 조건검색식이 발생한 직후 3분 이내의 데이터만 신뢰하라. 시간이 지날수록 신호 신뢰도가 떨어진다.

출력 형식은 반드시 아래 JSON으로만 응답하라:
{
  "decision": "BUY|WAIT|SKIP",
  "confidence": 0~100 사이의 정수,
  "order_type": "MARKET|LIMIT_TOP|NONE",
  "position_size_ratio": 0.0~1.0,
  "invalidation_price": 0 (정수),
  "reasons": [""],
  "risks": [""]
}
"""

# ==========================================
# 1-4. 🎯 조건검색식 청산 판단 프롬프트 (Condition Exit)
# ==========================================
CONDITION_EXIT_PROMPT = """
너는 조건검색식으로 진입한 포지션의 청산 시점을 판단하는 전문 트레이더다.
너의 임무는 보유 포지션의 실시간 데이터를 바탕으로 홀드, 부분 청산, 전량 청산을 결정하는 것이다.

[판단 원칙]
1. 조건검색식 패밀리에 맞는 청산 논리(VCP는 익절 빠르게, S15는 트레일링 등)를 적용하라.
2. 실시간 수익률, 최고점 대비 하락폭, AI 점수 하락, 매도 압력 증가를 주요 신호로 삼아라.
3. 손절은 신호 실패 시 즉시, 익절은 추세가 꺾일 때 점진적으로 실행하라.

출력 형식은 반드시 아래 JSON으로만 응답하라:
{
  "decision": "HOLD|TRIM|EXIT",
  "confidence": 0~100 사이의 정수,
  "trim_ratio": 0.0~1.0,
  "new_stop_price": 0 (정수),
  "reason_primary": "",
  "warning": ""
}
"""

# ==========================================
# 2. 🎯 [신규] 일일 시장 진단 프롬프트 (텔레그램 브리핑용)
# ==========================================
ENHANCED_MARKET_ANALYSIS_PROMPT = """
너는 여의도 15년차 베테랑 퀀트 트레이더이자 매크로-주식 연계 해석에 능한 수석 애널리스트다.
너의 임무는 '스캐너 내부 체력'과 '밤사이 미국/국제 거시환경'을 함께 읽어, 오늘 KOSPI/KOSDAQ 장세를 텔레그램 아침 브리핑으로 압축 정리하는 것이다.

[분석 원칙]
1. 반드시 입력 데이터를 두 축으로 나누어 해석하라.
   - 축 A: 스캐너 통계 = 국내 종목들의 내부 체력, breadth, 수급 질
   - 축 B: 오버나이트 매크로 = 지수 방향을 흔드는 외생 변수
2. 두 축이 같은 방향이면 확신도를 높여라.
3. 두 축이 충돌하면, 어느 쪽이 더 강한지와 왜 충돌하는지 설명하라.
4. 최종 생존 종목이 0개여도 절대 단순히 '추천 종목 없음'으로 끝내지 마라.
   아래 셋 중 하나 이상으로 구체적으로 분류하라.
   - 지수 반등형
   - 좁은 주도주형
   - 관망형
   - 리스크오프형
   - 과열 조심형
5. 입력된 오버나이트 데이터가 없으면, 그 사실을 1문장으로 명시하고 스캐너 통계 중심으로만 판단하라.
   없는 데이터를 추정해서 쓰지 마라.

[오버나이트 매크로 해석 우선순위]
1. 미국 정치/전쟁/제재/관세/중동 관련 headline risk
2. S&P500, Nasdaq, 가능하면 반도체 관련 위험선호 흐름
3. VIX, 미 10년물 금리, 달러/원
4. Brent/WTI 유가
5. 외국인 수급에 유리/불리한 환경인지
6. 한국 시장에서 유리한 업종/불리한 업종

[스캐너 통계 해석 가이드]
1. '기초 품질 미달' 비중이 높다 -> 시장 전반 차트가 무너졌거나 하락 추세 종목이 많다
2. 'AI 확신도 부족' / '수급 부재' 비중이 높다 -> 종목은 버티지만 주도주가 없고 외인/기관 확신이 부족한 장
3. '단기 급등/이격도 과다' 비중이 높다 -> 지수는 버텨도 개별주는 추격 매수 위험이 큰 장
4. 생존 종목이 적더라도 특정 업종에만 몰려 있으면 -> 전면 강세장이 아니라 좁은 주도주 장세로 진단

[출력 규칙]
1. 텔레그램용 마크다운 텍스트로 작성하라. JSON 금지.
2. 길이는 350~500자 내외.
3. 말투는 친근하지만 냉정한 전문가 톤.
4. 아래 4개 섹션 구조를 반드시 지켜라.

📌 **[오버나이트 매크로]**
📊 **[스캐너 내부 체력]**
🧭 **[오늘 장 해석]**
🎯 **[행동 지침]**

[가장 중요한 금지사항]
- 입력되지 않은 뉴스나 숫자를 지어내지 마라.
- 스캐너 결과만 보고 지수 방향을 단정하지 마라.
- 매크로와 스캐너가 충돌하면 반드시 '충돌' 자체를 설명하라.
"""
# ==========================================
# 3. 🎯 [신규] 실시간 종목 분석 프롬프트 (AUTO -> SCALP / SWING / DUAL)
# ==========================================
REALTIME_ANALYSIS_PROMPT_SCALP = """
너는 상위 1% 초단타 프랍 트레이더다.
목표는 1~2%의 짧은 파동만 빠르게 먹고, 모멘텀이 식는 순간 손절하는 것이다.

[분석 원칙]
1. 현재값보다 변화율을 우선하라. 특히 체결강도, 매수세, 프로그램 순매수의 최근 변화가 핵심이다.
2. VWAP 아래, 고가 돌파 실패, 스프레드 확대, 체결 둔화는 추격 금지 신호다.
3. 기계 목표가보다 중요한 것은 "지금 진입하면 즉시 반응이 나오는 자리인가"다.
4. 이미 보유 중이라면 신규 진입과 다르게 판단하라.
5. 결론은 반드시 행동 가능한 문장으로 끝내라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

📍 **[한 줄 결론]**
🧠 **[핵심 해석]**
⚠️ **[리스크 포인트]**
🎯 **[실전 행동 지침]**

[실전 행동 지침]은 반드시 아래 다섯 가지 중 하나로 시작:
[즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

길이 350~520자. 애매한 표현 금지.
"""

REALTIME_ANALYSIS_PROMPT_SWING = """
너는 상위 1% 스윙 트레이더다.
목표는 단기 노이즈를 무시하고, 수급과 일봉 구조가 받쳐주는 자리에서 며칠간 추세를 먹는 것이다.

[분석 원칙]
1. 순간 체결보다 일봉 구조와 수급 지속성을 우선하라.
2. 현재가가 5일선/20일선/전일고점/VWAP 대비 어디에 있는지 해석하라.
3. 프로그램, 외인, 기관의 개입이 지속 가능한지 판단하라.
4. 기계 목표가와 손절가의 손익비가 합리적인지 검증하라.
5. 이미 많이 오른 자리라면 좋은 종목이어도 추격 금지를 명확히 말하라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

📍 **[한 줄 결론]**
🧠 **[핵심 해석]**
⚠️ **[리스크 포인트]**
🎯 **[실전 행동 지침]**

[실전 행동 지침]은 반드시 아래 다섯 가지 중 하나로 시작:
[즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

길이 350~520자. 애매한 표현 금지.
"""

REALTIME_ANALYSIS_PROMPT_DUAL = """
너는 초단타와 스윙을 모두 수행하는 베테랑 프랍 트레이더다.
입력 종목을 스캘핑 관점과 스윙 관점에서 각각 평가하되, 최종적으로 어느 관점이 더 유효한지 결정하라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

⚡ **[스캘핑 판단]**
📈 **[스윙 판단]**
🎯 **[최종 채택 관점]**
🧭 **[실전 행동 지침]**

[최종 채택 관점]은 반드시 하나를 선택:
[스캘핑 우선] [스윙 우선] [둘 다 아님]

길이 420~650자.
"""

# ==========================================
# 3-2. 🎯 [신규] 스캘핑 오버나이트 의사결정 프롬프트 (15:15 전용)
# ==========================================
SCALPING_OVERNIGHT_DECISION_PROMPT = """
너는 장 마감 직전 15년 경력의 베테랑 프랍 트레이더이자 리스크 매니저다.
네 임무는 원래 당일 청산이 원칙인 SCALPING 포지션을 15시 15분 시점에서 검토해,
'오늘 무조건 시장가 청산'할지, 아니면 '예외적으로 오버나이트 보유'할지를 결정하는 것이다.

[핵심 원칙]
1. 기본값은 SELL_TODAY 이다. HOLD_OVERNIGHT 는 매우 예외적인 경우에만 선택한다.
2. HOLD_OVERNIGHT 는 아래가 동시에 충족될 때만 허용하라.
   - 일봉 구조가 무너지지 않았고
   - VWAP/당일 고점/프로그램 수급/외인기관 흐름이 약하지 않으며
   - 단순 초단타 잔불이 아니라 다음날까지 이어질 추세 근거가 있다.
3. SELL_ORDERED 상태에서 HOLD_OVERNIGHT 를 선택하려면, 기존 매도 주문을 취소하고도 들고 갈 가치가 충분한지 더 엄격하게 보라.
4. 입력 데이터가 부족하거나 애매하면 무조건 SELL_TODAY 를 선택하라.
5. 출력은 반드시 JSON만 반환하라.

반드시 아래 JSON 형식으로만 응답하라:
{
  "action": "SELL_TODAY" | "HOLD_OVERNIGHT",
  "confidence": 0~100 사이 정수,
  "reason": "판단 근거 1줄",
  "risk_note": "가장 큰 리스크 1줄"
}
"""

# ==========================================
# 🎯 [신규] 종가 마감 후 내일의 주도주 발굴 프롬프트 (Gemini 3.0 Pro 전용)
# ==========================================
EOD_TOMORROW_LEADER_PROMPT = """
너는 여의도 최상위 0.1% 수익률을 자랑하는 전설적인 기관 프랍 트레이더이자 수석 모멘텀 전략가야.
너의 특기는 장 마감 후 '에너지가 극도로 응축된 눌림목'과 '메이저 수급(외인/기관)이 몰래 매집한 흔적'을 찾아내어, 내일 당장 급등할 주도주를 선점하는 것이다.

사용자가 오늘 장 마감 데이터(종가, 수급, 거래량, 보조지표 등)를 바탕으로 1차 필터링한 10~20개의 후보 종목 리스트를 줄 것이다. 
이 데이터를 심층 분석하여 **내일 반드시 눈여겨봐야 할 '최우선 주도주 TOP 5'**를 엄선하고 텔레그램 리포트를 작성해라.

[종목 선정 및 분석 가이드]
1. 수급과 차트의 괴리 찾기: 주가 변동성이나 거래량은 죽어있는데(수렴), 외인/기관의 순매수가 연속으로 들어온 종목은 세력의 '매집'이다. 이런 종목에 가장 높은 가산점을 주어라.
2. 볼린저밴드 스퀴즈 & 정배열 초입: 에너지가 압축되었다가 발산하기 직전의 자리(MA5가 MA20을 뚫으려 하거나, 밴드 상단을 돌파하려는 자리)를 우선해라.
3. 뻔한 상승주 배제: 이미 오늘 15% 이상 급등하여 내일 갭하락이나 차익실현 매물이 쏟아질 확률이 높은 과열 종목은 과감히 버려라.

[출력 양식 설정]
1. 텔레그램 마크다운 텍스트 형식으로 작성해라. (JSON 아님)
2. 어투는 전문가의 냉철함과 자신감이 묻어나게 하고, 쓸데없는 인사말 없이 핵심만 전달해라.
3. 리포트 구조는 반드시 아래 형식을 지켜라:

📊 **[여의도 프랍 데스크] 내일의 주도주 TOP 5 마감 브리핑**
(오늘 시장의 전반적인 수급 흐름과 내일 장세 예상 1~2줄 요약)

🥇 **1. [종목명] (종목코드)**
- 💰 종가: 00,000원
- 🧠 선정 사유: (수급과 차트 응축 상태를 기반으로 세력의 의도를 읽어내는 날카로운 1~2줄 분석)
- 🎯 타점 전략: 시초가 눌림 매수 / 돌파 매수 등 전략 제시, 목표가/손절가 가이드라인 포함

🥈 **2. [종목명] (종목코드)**
... (위와 동일한 양식으로 TOP 5까지 작성) ...

💡 **[수석 트레이더의 내일 장 원포인트 레슨]**
(내일 아침 시초가 대응이나 주의해야 할 리스크에 대한 뼈 때리는 조언 1줄)
"""

EOD_TOMORROW_LEADER_JSON_PROMPT = """
너는 여의도 최상위 0.1% 수익률의 기관 프랍 트레이더다.
입력된 후보군 중에서 내일 가장 유력한 주도주 TOP 5를 골라 반드시 JSON만 반환하라.

[선정 원칙]
1. 외인/기관 수급 누적 및 가속, 차트 응축, 정배열 초입, 전고점 돌파 직전 자리를 높게 평가한다.
2. 이미 과열된 종목은 낮게 평가하거나 제외한다.
3. 종목코드는 반드시 6자리 문자열로 반환한다.
4. confidence는 0~1 사이 float로 반환한다.
5. JSON 외의 텍스트는 절대 출력하지 마라.

반드시 아래 형식만 반환:
{
  "market_summary": "오늘 시장과 내일 장세를 보는 1~2줄 요약",
  "one_point_lesson": "내일 시초가 대응이나 주의할 리스크 한 줄",
  "top5": [
    {
      "rank": 1,
      "stock_name": "종목명",
      "stock_code": "000000",
      "close_price": 12345,
      "reason": "선정 사유 1~2줄",
      "entry_plan": "시초가 눌림 / 돌파 등",
      "target_price_guide": "목표가 가이드",
      "stop_price_guide": "손절가 가이드",
      "confidence": 0.91
    }
  ]
}
"""

class GeminiSniperEngine:
    def __init__(self, api_keys):
        if isinstance(api_keys, str):
            api_keys = [api_keys]
            
        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys) 
        self._rotate_client()

        # self.current_model_name = 'gemini-flash-lite-latest'
        self.current_model_name = 'gemini-2.5-flash-lite'
        self.lock = threading.Lock()
        self.last_call_time = 0
        self.min_interval = getattr(TRADING_RULES, 'GEMINI_ENGINE_MIN_INTERVAL', 0.5)
        self.consecutive_failures = 0
        self.ai_disabled = False
        self.max_consecutive_failures = getattr(TRADING_RULES, 'AI_MAX_CONSECUTIVE_FAILURES', 5)
        self.current_api_key_index = 0
        print(f"🧠 [AI 엔진] {len(self.api_keys)}개 키 로테이션 가동! (선봉: {self.current_model_name})")

    def _rotate_client(self):
        self.current_key = next(self.key_cycle)
        self.client = genai.Client(api_key=self.current_key)
        # 현재 API 키 인덱스 추적 (로그용)
        try:
            self.current_api_key_index = self.api_keys.index(self.current_key)
        except ValueError:
            self.current_api_key_index = 0
    
    # ==========================================
    # 3. 💡 [아키텍처 포인트] 만능 API 호출기 (중복 코드 완벽 제거)
    # ==========================================
    def _call_gemini_safe(self, prompt, user_input, require_json=True, context_name="Unknown", model_override=None):
        """키 로테이션, 예외 처리, 모델 덮어쓰기를 모두 전담하는 중앙 집중식 호출기"""
        contents = [prompt, user_input] if prompt else [user_input]
        
        config = None
        if require_json:
            config = {'response_mime_type': "application/json"}
            
        # 💡 [핵심] model_override가 지정되면 해당 모델을, 아니면 기본 모델(flash-lite)을 사용
        target_model = model_override if model_override else self.current_model_name
        last_error = ""

        for attempt in range(len(self.api_keys)):
            try:
                response = self.client.models.generate_content(model=target_model, contents=contents, config=config)
                raw_text = response.text.strip()
                
                if require_json:
                    # 💡 [개선] JSON 블록만 정밀하게 추출 (뒤에 붙은 부연설명 무시)
                    import re
                    # { 로 시작해서 } 로 끝나는 가장 큰 덩어리를 찾습니다.
                    match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if match:
                        clean_json = match.group()
                        return json.loads(clean_json)
                    else:
                        # { } 자체가 없는 경우
                        raise ValueError(f"JSON 형식을 찾을 수 없음: {raw_text[:100]}...")
                else:
                    return raw_text

            except Exception as e:
                last_error = str(e).lower()
                # 💡 [핵심 교정] 429(한도초과)뿐만 아니라 503(서버과부하) 에러도 로테이션 대상에 포함합니다.
                if any(x in last_error for x in ["429", "quota", "503", "unavailable", "high demand", "too_many_requests"]):
                    old_key = self.current_key[-5:]
                    self._rotate_client()
                    
                    # 📢 로그 기록 강화
                    warn_msg = f"⚠️ [AI 서버 과부하/한도] {context_name} | {old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})"
                    print(warn_msg)
                    log_error(warn_msg) 
                    
                    # 서버 안정을 위해 약간의 지연 후 재시도
                    time.sleep(0.8) 
                    continue
                else:
                    # 그 외 예측 불가능한 치명적 에러는 즉시 보고
                    raise RuntimeError(f"API 응답/파싱 실패: {e}")
                
        # 💡 [최종 방어선] 모든 키를 소진했을 때의 처리
        fatal_msg = f"🚨 [AI 고갈] 모든 API 키 사용 불가. 마지막 에러: {last_error}"
        log_error(fatal_msg)
        raise RuntimeError(fatal_msg)
        

    # ==========================================
    # 4. 🛠️ 데이터 포맷팅 (AI 전용 번역기 - V3.0 스캘퍼의 눈)
    # ==========================================
    def _format_market_data(self, ws_data, recent_ticks, recent_candles=None):
        """키움 API의 딕셔너리 데이터를 AI가 읽을 수 있는 텍스트로 예쁘게 포장합니다."""
        if recent_candles is None:
            recent_candles = []
            
        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        fluctuation = ws_data.get('fluctuation', 0.0) 
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)

        # 🚀 [무기 1] 호가 불균형 (Orderbook Imbalance) 계산
        imbalance_str = "데이터 없음"
        if ask_tot > 0 and bid_tot > 0:
            ratio = ask_tot / bid_tot
            if ratio >= 2.0:
                imbalance_str = f"매도벽 압도적 우위 ({ratio:.1f}배) - 돌파 시 급등 패턴"
            elif ratio <= 0.5:
                imbalance_str = f"매수벽 우위 ({1/ratio:.1f}배) - 하락 방어 또는 휩소(가짜) 패턴"
            else:
                imbalance_str = f"팽팽함 (매도 {ask_tot:,} vs 매수 {bid_tot:,})"

        # 🚀 [무기 2] 당일 고점 대비 이격도 (Drawdown from High)
        high_price = curr_price
        if recent_candles:
            # 1분봉 데이터들을 훑어 가장 높았던 고점을 찾습니다.
            high_price = max(c.get('고가', curr_price) for c in recent_candles)
        
        drawdown_str = "0.0%"
        if high_price > 0:
            drawdown = ((curr_price - high_price) / high_price) * 100
            drawdown_str = f"{drawdown:.2f}% (당일 고가 {high_price:,}원)"

        # 호가창 조립
        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']:,}원 ({a['volume']:,}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']:,}원 ({b['volume']:,}주)" for i, b in enumerate(orderbook['bids'])])
        
        # 🚀 [무기 3] 틱 흐름 분석 및 틱 체결 가속도(Tick Speed) 계산
        tick_summary = "틱 데이터 부족"
        tick_str = ""
        
        if recent_ticks and len(recent_ticks) > 0:
            buy_vol = sum(t['volume'] for t in recent_ticks if t.get('dir') == 'BUY')
            sell_vol = sum(t['volume'] for t in recent_ticks if t.get('dir') == 'SELL')
            total_vol = buy_vol + sell_vol
            buy_pressure = (buy_vol / total_vol * 100) if total_vol > 0 else 50.0
            
            latest_price = recent_ticks[0]['price']
            oldest_price = recent_ticks[-1]['price']
            trend_str = "상승 돌파 중 🚀" if latest_price > oldest_price else "하락 밀림 📉" if latest_price < oldest_price else "횡보 중 ➖"
            latest_strength = recent_ticks[0].get('strength', 0.0)

            # 10틱이 터지는 데 걸린 시간(초)을 계산하여 '가속도'를 측정합니다.
            time_diff_sec = 0
            try:
                from datetime import datetime
                # 시간 포맷(HHMMSS) 문자열을 파싱
                t1_str = str(recent_ticks[-1]['time']).replace(':', '').zfill(6)
                t2_str = str(recent_ticks[0]['time']).replace(':', '').zfill(6)
                t1 = datetime.strptime(t1_str, "%H%M%S")
                t2 = datetime.strptime(t2_str, "%H%M%S")
                time_diff_sec = (t2 - t1).total_seconds()
                if time_diff_sec < 0: time_diff_sec += 86400 # 자정 넘어가는 경우
            except:
                time_diff_sec = 999
            
            speed_str = f"🚀 매우 빠름 ({len(recent_ticks)}틱에 {time_diff_sec}초)" if time_diff_sec <= 2.0 else f"보통 ({time_diff_sec}초)" if time_diff_sec <= 10.0 else f"느림 ({time_diff_sec}초 - 소강상태)"

            tick_summary = (
                f"⏱️ [최근 {len(recent_ticks)}틱 정밀 브리핑]\n"
                f"- 단기 흐름: {trend_str}\n"
                f"- 틱 체결 속도(가속도): {speed_str}\n"
                f"- 🔥 매수 압도율(Buy Pressure): {buy_pressure:.1f}% (매수 {buy_vol:,}주 vs 매도 {sell_vol:,}주)\n"
                f"- 현재 체결강도: {latest_strength}%"
            )
            
            tick_str = "\n".join([f"[{t['time']}] {t.get('dir', 'NEUTRAL')} 체결: {t['price']:,}원 ({t['volume']:,}주) | 강도:{t.get('strength', 0)}%" for t in recent_ticks[:10]])

        # 1분봉 차트 조립
        candle_str = ""
        if recent_candles:
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c['시가']:,} 고가:{c['고가']:,} 저가:{c['저가']:,} 종가:{c['현재가']:,} 거래량:{c['거래량']:,}" 
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

        # 직전 캔들 대비 거래량 폭증 여부 계산
        volume_analysis = "비교 불가 (데이터 부족)"
        if recent_candles and len(recent_candles) >= 2:
            current_volume = recent_candles[-1]['거래량']
            prev_volumes = [c['거래량'] for c in recent_candles[:-1]]
            avg_prev_volume = sum(prev_volumes) / len(prev_volumes) if prev_volumes else 0
            
            if avg_prev_volume > 0:
                vol_ratio = (current_volume / avg_prev_volume) * 100
                if vol_ratio >= 200:
                    volume_analysis = f"🔥 폭증! (이전 평균 대비 {vol_ratio:.0f}% 수준 / 현재 {current_volume:,}주)"
                elif vol_ratio >= 100:
                    volume_analysis = f"상승 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"
                else:
                    volume_analysis = f"감소 추세 (이전 평균 대비 {vol_ratio:.0f}% 수준)"

        # 지표 조립
        indicators_str = "지표 계산 불가"
        if recent_candles and len(recent_candles) >= 5:
            from src.engine.signal_radar import SniperRadar
            temp_radar = SniperRadar(token=None)
            ind = temp_radar.calculate_micro_indicators(recent_candles) 
            
            ma5_status = "상회" if curr_price > ind['MA5'] else "하회"
            vwap_status = "상회 (수급강세)" if curr_price > ind['Micro_VWAP'] else "하회 (수급약세)"
            
            indicators_str = (
                f"- 단기 5-MA: {ind['MA5']:,}원 (현재가 {ma5_status})\n"
                f"- Micro-VWAP: {ind['Micro_VWAP']:,}원 (현재가 {vwap_status})\n"
                f"- 고점 대비 이격도: {drawdown_str}\n"
                f"- 호가 불균형: {imbalance_str}"
            )

        # 최종 프롬프트 조합
        user_input = f"""
[현재 상태]
- 현재가: {curr_price:,}원
- 전일대비 등락률: {fluctuation}%
- 웹소켓 체결강도: {v_pw}%

[초단타 수급/위치 지표]
{indicators_str}

[거래량 분석]
- {volume_analysis}

{tick_summary}

[최근 1분봉 흐름 (과거 -> 최신순)]
{candle_str}

[실시간 호가창]
{ask_str}
-------------------------
{bid_str}

[최근 10틱 상세 내역 (최신순)]
{tick_str}
"""
        return user_input
    
    def _format_swing_market_data(self, ws_data, recent_candles, program_net_qty=0):
        """스윙 매매를 위해 넓은 시야(차트, 수급) 위주로 데이터를 포장합니다."""
        curr_price = ws_data.get('curr', 0)
        fluctuation = ws_data.get('fluctuation', 0.0)
        v_pw = ws_data.get('v_pw', 0)
        today_vol = ws_data.get('volume', 0)
        
        # 1. 캔들 분석 (추세 및 지지/저항)
        candle_str = "분봉 데이터 없음"
        ma5, ma20 = 0, 0
        if recent_candles and len(recent_candles) >= 20:
            closes = [c['현재가'] for c in recent_candles]
            ma5 = sum(closes[-5:]) / 5
            ma20 = sum(closes[-20:]) / 20
            
            trend = "정배열 (상승세)" if ma5 > ma20 else "역배열 (하락세)"
            position = "MA5 위 (강세)" if curr_price > ma5 else "MA5 아래 (조정)"
            
            candle_str = (
                f"- 현재 단기 추세: {trend}\n"
                f"- MA5: {ma5:,.0f}원 / MA20: {ma20:,.0f}원\n"
                f"- 주가 위치: {position}\n"
                f"- 최근 5봉 흐름: " + " -> ".join([f"{c['현재가']:,}" for c in recent_candles[-5:]])
            )

        # 2. 수급 분석
        prog_sign = "🔴 순매수" if program_net_qty > 0 else "🔵 순매도"
        
        user_input = f"""
[현재 상태 (스윙 관점)]
- 현재가: {curr_price:,}원 (전일대비 {fluctuation:+.2f}%)
- 당일 누적 거래량: {today_vol:,}주
- 당일 체결강도: {v_pw}%

[메이저 수급 지표]
- 프로그램 동향: {prog_sign} ({program_net_qty:,}주)

[차트/위치 분석]
{candle_str}
"""
        return user_input

    # ==========================================
    # 4. 🚀 실전 분석 실행 (스나이퍼가 호출할 메인 함수)
    # ==========================================
    # strategy 파라미터 추가 (기본값 SCALPING)
    def analyze_target(self, target_name, ws_data, recent_ticks, recent_candles, strategy="SCALPING", program_net_qty=0):
        if not self.lock.acquire(blocking=False):
            return {"action": "WAIT", "score": 50, "reason": "AI 경합 (다른 종목 분석 중)"}
            
        try:
            # AI 엔진이 비활성화되었을 경우 즉시 DROP 반환
            if self.ai_disabled:
                return {"action": "DROP", "score": 0, "reason": "AI 엔진 일시 중단 (연속 실패)"}

            if time.time() - self.last_call_time < self.min_interval:
                return {"action": "WAIT", "score": 50, "reason": "AI 쿨타임"}

            # 💡 [핵심] 전략에 따른 지능(Prompt)과 데이터(Context) 분기
            if strategy in ["KOSPI_ML", "KOSDAQ_ML"]:
                prompt = SWING_SYSTEM_PROMPT
                formatted_data = self._format_swing_market_data(ws_data, recent_candles, program_net_qty)
                # 스윙은 조금 더 깊은 사고력이 필요하므로 Flash 대신 Pro 모델을 고려할 수도 있습니다.
                target_model = "gemini-pro-latest"
            else:
                prompt = SCALPING_SYSTEM_PROMPT
                formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
                target_model = self.current_model_name # 속도가 생명인 flash-lite 유지

            result = self._call_gemini_safe(
                prompt,
                formatted_data,
                require_json=True,
                context_name=f"{target_name}({strategy})",
                model_override=target_model
            )
            
            # 호출 성공 시 실패 횟수 리셋
            self.consecutive_failures = 0
            self.last_call_time = time.time()
            return result
                
        except Exception as e:
            # 실패 횟수 증가
            self.consecutive_failures += 1
            log_error(f"🚨 [{target_name}][{strategy}] AI 실시간 분석 에러 (연속 실패 {self.consecutive_failures}회, API키 인덱스 {self.current_api_key_index}): {e}")
            
            # 임계값 초과 시 AI 엔진 비활성화
            if self.consecutive_failures >= self.max_consecutive_failures:
                self.ai_disabled = True
                log_error(f"🚨 AI 엔진 비활성화 (연속 실패 {self.consecutive_failures}회 초과, API키 인덱스 {self.current_api_key_index})")
            
            return {"action": "WAIT", "score": 50, "reason": f"에러: {e}"}
        finally:
            self.lock.release()
            
        def analyze_condition_target(self, target_name, ws_data, recent_ticks, recent_candles, condition_profile):
            """
            조건검색 특화 AI 분석 (condition_profile에 따른 프롬프트 선택)
            condition_profile은 resolve_condition_profile에서 반환된 딕셔너리입니다.
            """
            # 전략과 포지션 태그에 따라 프롬프트 분기 (기본은 SCALPING)
            strategy = condition_profile.get('strategy', 'SCALPING')
            position_tag = condition_profile.get('position_tag', 'MIDDLE')
            # TODO: 조건별 프롬프트 추가 (VCP, S15 등)
            # 현재는 기존 analyze_target에 위임
            return self.analyze_target(target_name, ws_data, recent_ticks, recent_candles, strategy)
    
        def evaluate_condition_gatekeeper(self, stock_name, stock_code, realtime_ctx, condition_profile):
            """
            조건검색 특화 게이트키퍼 (condition_profile에 따른 판단)
            """
            # 현재는 기존 evaluate_realtime_gatekeeper에 위임
            return self.evaluate_realtime_gatekeeper(stock_name, stock_code, realtime_ctx, analysis_mode="AUTO")
    
    
    def analyze_scanner_results(self, total_count, survived_count, stats_text, macro_text=""):
        """텔레그램 아침 브리핑 (Macro + Scanner 통합)"""
        with self.lock:
            data_input = build_scanner_data_input(
                total_count=total_count,
                survived_count=survived_count,
                stats_text=stats_text,
                macro_text=macro_text,
            )
            try:
                return self._call_gemini_safe(
                    ENHANCED_MARKET_ANALYSIS_PROMPT,
                    data_input,
                    require_json=False,
                    context_name="시장 브리핑",
                    model_override="gemini-pro-latest",
                )
            except Exception as e:
                log_error(f"🚨 [시장 브리핑] AI 에러: {e}")
                return f"⚠️ AI 시장 진단 생성 중 에러 발생: {e}"


    
    
    def _infer_realtime_mode(self, realtime_ctx):
        """텔레그램 입력은 종목코드만 받고, 서버 내부에서 AUTO -> SCALP / SWING / DUAL 분기"""
        strat_label = str(realtime_ctx.get("strat_label", "")).upper()
        position_status = str(realtime_ctx.get("position_status", "NONE")).upper()
        fluctuation = float(realtime_ctx.get("fluctuation", 0.0) or 0.0)
        vol_ratio = float(realtime_ctx.get("vol_ratio", 0.0) or 0.0)
        v_pw_now = float(realtime_ctx.get("v_pw_now", 0.0) or 0.0)
        v_pw_3m = float(realtime_ctx.get("v_pw_3m", 0.0) or 0.0)
        prog_delta_qty = int(realtime_ctx.get("prog_delta_qty", 0) or 0)
        curr_price = int(realtime_ctx.get("curr_price", 0) or 0)
        vwap_price = int(realtime_ctx.get("vwap_price", 0) or 0)
        high_breakout_status = str(realtime_ctx.get("high_breakout_status", ""))
        daily_setup_desc = str(realtime_ctx.get("daily_setup_desc", ""))
        session_stage = str(realtime_ctx.get("session_stage", "REGULAR")).upper()
        captured_at = str(realtime_ctx.get("captured_at", ""))

        if strat_label in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "MIDTERM", "POSITION"}:
            return "SWING"

        scalp_score = 0
        swing_score = 0

        if position_status == "HOLDING":
            swing_score += 2

        hhmm = ""
        if captured_at and len(captured_at) >= 16:
            hhmm = captured_at[11:16].replace(":", "")
        if not hhmm:
            hhmm = time.strftime("%H%M")

        if session_stage in {"PREOPEN", "OPENING"} or "0900" <= hhmm <= "1030":
            scalp_score += 2
        elif "1300" <= hhmm <= "1500":
            swing_score += 1

        if abs(fluctuation) >= 3.0:
            scalp_score += 1
        if vol_ratio >= 150:
            scalp_score += 2
        elif 70 <= vol_ratio <= 130:
            swing_score += 1

        if v_pw_now >= 120 and (v_pw_now - v_pw_3m) >= 10:
            scalp_score += 2

        if prog_delta_qty > 0:
            scalp_score += 1
            swing_score += 1

        if curr_price > 0 and vwap_price > 0 and curr_price >= vwap_price:
            scalp_score += 1
        if "돌파" in high_breakout_status:
            scalp_score += 1

        if any(k in daily_setup_desc for k in ["정배열", "눌림", "전고점", "추세", "돌파"]):
            swing_score += 2
        if any(k in daily_setup_desc for k in ["급등후", "과열", "이격", "장대음봉"]):
            swing_score -= 1

        if abs(scalp_score - swing_score) <= 1:
            return "DUAL"
        return "SCALP" if scalp_score > swing_score else "SWING"

    def _get_realtime_prompt(self, selected_mode):
        if selected_mode == "SCALP":
            return REALTIME_ANALYSIS_PROMPT_SCALP
        if selected_mode == "SWING":
            return REALTIME_ANALYSIS_PROMPT_SWING
        return REALTIME_ANALYSIS_PROMPT_DUAL

    def _build_realtime_quant_packet(self, stock_name, stock_code, realtime_ctx, selected_mode):
        def i(key, default=0):
            try:
                return int(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        def f(key, default=0.0):
            try:
                return float(realtime_ctx.get(key, default) or default)
            except Exception:
                return default

        curr_price = i("curr_price")
        vwap_price = i("vwap_price")
        ask_tot = i("ask_tot")
        bid_tot = i("bid_tot")
        orderbook_imbalance = f("orderbook_imbalance")
        best_ask = i("best_ask")
        best_bid = i("best_bid")

        common_block = f"""[기본]
- 종목명: {stock_name}
- 종목코드: {stock_code}
- 분석모드: {selected_mode}
- 감시전략: {realtime_ctx.get('strat_label', 'AUTO')}
- 보유상태: {realtime_ctx.get('position_status', 'NONE')}
- 평균단가: {i('avg_price'):,}원
- 현재손익률: {f('pnl_pct'):+.2f}%
- 현재가격: {curr_price:,}원 (전일비 {f('fluctuation'):+.2f}%)
- 기계목표가: {i('target_price'):,}원 (사유: {realtime_ctx.get('target_reason', '')})
- 익절/손절: {f('trailing_pct'):.2f}% / {f('stop_pct'):.2f}%
- 퀀트 점수: 추세 {f('trend_score'):.1f} / 수급 {f('flow_score'):.1f} / 호가 {f('orderbook_score'):.1f} / 타점 {f('timing_score'):.1f} / 종합 {f('score'):.1f}
- 퀀트 엔진 결론: {realtime_ctx.get('conclusion', '')}

[수급/체결]
- 누적거래량: {i('today_vol'):,}주 (20일 평균대비 {f('vol_ratio'):.1f}%)
- 거래대금: {i('today_turnover'):,}원
- 체결강도 현재/1분/3분/5분: {f('v_pw_now'):.1f} / {f('v_pw_1m'):.1f} / {f('v_pw_3m'):.1f} / {f('v_pw_5m'):.1f}
- 매수세 현재/1분/3분: {f('buy_ratio_now'):.1f}% / {f('buy_ratio_1m'):.1f}% / {f('buy_ratio_3m'):.1f}%
- 프로그램 순매수 현재/증감: {i('prog_net_qty'):+,}주 / {i('prog_delta_qty'):+,}주
- 외인/기관 당일 가집계: 외인 {i('foreign_net'):+,}주 / 기관 {i('inst_net'):+,}주
- 외인+기관 합산: {i('smart_money_net'):+,}주

[호가/구조]
- 최우선 매도/매수호가: {best_ask:,} / {best_bid:,}
- 매도잔량/매수잔량: {ask_tot:,} / {bid_tot:,}
- 호가 불균형비: {orderbook_imbalance:.2f}
- 스프레드: {i('spread_tick')}틱
- 체결 편향: {realtime_ctx.get('tape_bias', '중립')}
- 매도벽 소화 여부: {realtime_ctx.get('ask_absorption_status', '')}
- VWAP: {vwap_price:,}원 ({realtime_ctx.get('vwap_status', '정보없음')})
- 시가 위치: {realtime_ctx.get('open_position_desc', '')}
- 고가 돌파 여부: {realtime_ctx.get('high_breakout_status', '')}
- 최근 5분 박스 상단/하단: {i('box_high'):,} / {i('box_low'):,}
"""

        scalp_block = f"""
[스캘핑 관점]
- 체결강도 가속도: {f('v_pw_now') - f('v_pw_3m'):+.1f}
- 체결 signed 수량: {i('trade_qty_signed_now'):+,}주
- 프로그램 delta: {i('prog_delta_qty'):+,}주
- 눌림/돌파 즉시성 체크: VWAP / 고가 / 스프레드 / 테이프 편향
"""

        swing_block = f"""
[스윙 관점]
- 일봉 구조: {realtime_ctx.get('daily_setup_desc', '')}
- 5/20/60일선 상태: {realtime_ctx.get('ma5_status', '')}, {realtime_ctx.get('ma20_status', '')}, {realtime_ctx.get('ma60_status', '')}
- 전일 고점/저점: {i('prev_high'):,} / {i('prev_low'):,}
- 최근 20일 신고가 근접도: {f('near_20d_high_pct'):.2f}%
- 고가 대비 눌림폭: {f('drawdown_from_high_pct'):.2f}%
"""

        if selected_mode == "SCALP":
            return common_block + scalp_block
        if selected_mode == "SWING":
            return common_block + swing_block
        return common_block + scalp_block + swing_block

    # ==========================================
    # 🔍 수동 종목 정밀 분석 (AUTO -> SCALP / SWING / DUAL)
    # ==========================================
    def generate_realtime_report(self, stock_name, stock_code, input_data_text, analysis_mode="AUTO"):
        """실시간 종목 분석 리포트 생성 (dict realtime_ctx 권장, legacy string 지원)"""
        with self.lock:
            selected_mode = (analysis_mode or "AUTO").upper()
            realtime_ctx = input_data_text if isinstance(input_data_text, dict) else None

            if realtime_ctx is not None:
                if selected_mode == "AUTO":
                    selected_mode = self._infer_realtime_mode(realtime_ctx)
                prompt = self._get_realtime_prompt(selected_mode)
                packet_text = self._build_realtime_quant_packet(stock_name, stock_code, realtime_ctx, selected_mode)
                user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 전술 패킷]
{packet_text}"""
                context_name = f"실시간 분석({selected_mode})"
            else:
                if selected_mode == "AUTO":
                    selected_mode = "DUAL"
                prompt = self._get_realtime_prompt(selected_mode)
                user_input = f"""🚨 [요청 종목]
종목명: {stock_name}
종목코드: {stock_code}
선택된 분석 모드: {selected_mode}

📊 [실시간 분석 입력]
{str(input_data_text)}"""
                context_name = f"실시간 분석(LEGACY:{selected_mode})"

            try:
                return self._call_gemini_safe(
                    prompt,
                    user_input,
                    require_json=False,
                    context_name=context_name,
                    model_override="gemini-pro-latest"
                )
            except Exception as e:
                log_error(f"🚨 [{context_name}] AI 에러: {e}")
                return f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
    
    def extract_realtime_gatekeeper_action(self, report_text):
        """실시간 리포트 본문에서 최종 행동 라벨을 추출합니다."""
        if not isinstance(report_text, str) or not report_text:
            return "UNKNOWN"

        action_labels = [
            "[즉시 매수]",
            "[눌림 대기]",
            "[보유 지속]",
            "[일부 익절]",
            "[전량 회피]",
            "[스캘핑 우선]",
            "[스윙 우선]",
            "[둘 다 아님]",
        ]
        for label in action_labels:
            if label in report_text:
                return label.strip("[]")
        return "UNKNOWN"

    def evaluate_realtime_gatekeeper(self, stock_name, stock_code, realtime_ctx, analysis_mode="AUTO"):
        """generate_realtime_report 결과를 마지막 진입 게이트 판단용으로 정규화합니다."""
        report = self.generate_realtime_report(
            stock_name=stock_name,
            stock_code=stock_code,
            input_data_text=realtime_ctx,
            analysis_mode=analysis_mode,
        )
        action_label = self.extract_realtime_gatekeeper_action(report)
        allow_entry = action_label == "즉시 매수"
        return {
            "allow_entry": allow_entry,
            "action_label": action_label,
            "report": report,
        }

    # ==========================================
    # 🔍 [신규] 스캘핑 오버나이트 의사결정 (15:15 전용)
    # ==========================================
    def _format_scalping_overnight_context(self, realtime_ctx):
        ctx = realtime_ctx or {}
        lines = [
            f"- 포지션상태: {ctx.get('position_status', 'UNKNOWN')}",
            f"- 평균단가: {int(ctx.get('avg_price', 0) or 0):,}원",
            f"- 현재가: {int(ctx.get('curr_price', 0) or 0):,}원 (손익 {float(ctx.get('pnl_pct', 0.0) or 0.0):+.2f}%)",
            f"- 보유분수: {float(ctx.get('held_minutes', 0.0) or 0.0):.1f}분",
            f"- 현재 전략라벨: {ctx.get('strat_label', 'SCALPING')}",
            f"- VWAP: {int(ctx.get('vwap_price', 0) or 0):,}원 / 상태: {ctx.get('vwap_status', '')}",
            f"- 체결강도 현재/3분전/5분전: {float(ctx.get('v_pw_now', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_3m', 0.0) or 0.0):.1f} / {float(ctx.get('v_pw_5m', 0.0) or 0.0):.1f}",
            f"- 프로그램 순매수 현재/증감: {int(ctx.get('prog_net_qty', 0) or 0):,}주 / {int(ctx.get('prog_delta_qty', 0) or 0):+,}주",
            f"- 외인/기관 순매수: {int(ctx.get('foreign_net', 0) or 0):,}주 / {int(ctx.get('inst_net', 0) or 0):,}주",
            f"- 고가돌파 상태: {ctx.get('high_breakout_status', '')}",
            f"- 일봉 구조: {ctx.get('daily_setup_desc', '')}",
            f"- 5/20/60일선 상태: {ctx.get('ma5_status', '')}, {ctx.get('ma20_status', '')}, {ctx.get('ma60_status', '')}",
            f"- 전일 고점/저점: {int(ctx.get('prev_high', 0) or 0):,} / {int(ctx.get('prev_low', 0) or 0):,}",
            f"- 최근 20일 신고가 근접도: {float(ctx.get('near_20d_high_pct', 0.0) or 0.0):+.2f}%",
            f"- 퀀트 종합점수/결론: {float(ctx.get('score', 0.0) or 0.0):.1f} / {ctx.get('conclusion', '')}",
            f"- 주문상태 참고: {ctx.get('order_status_note', '')}",
        ]
        return "\n".join(lines)

    def evaluate_scalping_overnight_decision(self, stock_name, stock_code, realtime_ctx):
        """15:15 SCALPING 포지션의 오버나이트/당일청산 의사결정을 JSON으로 반환합니다."""
        with self.lock:
            user_input = (
                f"🚨 [15:15 SCALPING 오버나이트 판정 요청]\n"
                f"종목명: {stock_name}\n종목코드: {stock_code}\n\n"
                f"📊 [판정 입력 데이터]\n{self._format_scalping_overnight_context(realtime_ctx)}"
            )
            try:
                result = self._call_gemini_safe(
                    SCALPING_OVERNIGHT_DECISION_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"SCALP_OVERNIGHT:{stock_name}",
                    model_override="gemini-pro-latest"
                )
                action = str(result.get('action', 'SELL_TODAY') or 'SELL_TODAY').upper()
                if action not in {'SELL_TODAY', 'HOLD_OVERNIGHT'}:
                    action = 'SELL_TODAY'
                return {
                    'action': action,
                    'confidence': int(result.get('confidence', 0) or 0),
                    'reason': str(result.get('reason', '') or ''),
                    'risk_note': str(result.get('risk_note', '') or ''),
                    'raw': result,
                }
            except Exception as e:
                log_error(f"🚨 [SCALPING 오버나이트 판정] AI 에러: {e}")
                return {
                    'action': 'SELL_TODAY',
                    'confidence': 0,
                    'reason': f'AI 판정 실패로 보수적 청산 폴백: {e}',
                    'risk_note': '데이터 부족 또는 AI 응답 오류',
                    'raw': {},
                }

    def evaluate_condition_entry(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile):
        """
        조건검색식 진입 판단 (프롬프트: CONDITION_ENTRY_PROMPT)
        """
        with self.lock:
            # 데이터 포맷팅
            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            # 조건 프로필 정보 추가
            profile_text = f"조건검색식 프로필: {condition_profile}"
            user_input = f"{stock_name}({stock_code}) - 조건검색식 진입 판단 요청\n{profile_text}\n\n{formatted_data}"
            try:
                result = self._call_gemini_safe(
                    CONDITION_ENTRY_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"COND_ENTRY:{stock_name}",
                    model_override="gemini-pro-latest"
                )
                return result
            except Exception as e:
                log_error(f"🚨 [조건검색식 진입 판단] AI 에러: {e}")
                return {
                    "decision": "SKIP",
                    "confidence": 0,
                    "order_type": "NONE",
                    "position_size_ratio": 0.0,
                    "invalidation_price": 0,
                    "reasons": [f"AI 판정 실패: {e}"],
                    "risks": ["데이터 부족 또는 AI 응답 오류"]
                }

    def evaluate_condition_exit(self, stock_name, stock_code, ws_data, recent_ticks, recent_candles, condition_profile, profit_rate, peak_profit, current_ai_score):
        """
        조건검색식 청산 판단 (프롬프트: CONDITION_EXIT_PROMPT)
        """
        with self.lock:
            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)
            profile_text = f"조건검색식 프로필: {condition_profile}, 수익률: {profit_rate:.2f}%, 최고수익률: {peak_profit:.2f}%, AI 점수: {current_ai_score}"
            user_input = f"{stock_name}({stock_code}) - 조건검색식 청산 판단 요청\n{profile_text}\n\n{formatted_data}"
            try:
                result = self._call_gemini_safe(
                    CONDITION_EXIT_PROMPT,
                    user_input,
                    require_json=True,
                    context_name=f"COND_EXIT:{stock_name}",
                    model_override="gemini-pro-latest"
                )
                return result
            except Exception as e:
                log_error(f"🚨 [조건검색식 청산 판단] AI 에러: {e}")
                return {
                    "decision": "HOLD",
                    "confidence": 0,
                    "trim_ratio": 0.0,
                    "new_stop_price": 0,
                    "reason_primary": f"AI 판정 실패: {e}",
                    "warning": "데이터 부족 또는 AI 응답 오류"
                }

    # ==========================================
    # 🔍 [신규] 장 마감 후 내일의 주도주 분석 (gemini-3.0-pro 전용)
    # ==========================================

    def _render_eod_tomorrow_markdown(self, market_summary, one_point_lesson, top5):
        medals = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}
        lines = [
            "📊 **[여의도 프랍 데스크] 내일의 주도주 TOP 5 마감 브리핑**",
            str(market_summary or "").strip(),
            ""
        ]

        for item in top5[:5]:
            rank = int(item.get("rank", 0) or 0)
            medal = medals.get(rank, "⭐")
            stock_name = str(item.get("stock_name", "") or "")
            stock_code = str(item.get("stock_code", "") or "").zfill(6)

            try:
                close_price = int(float(item.get("close_price", 0) or 0))
            except Exception:
                close_price = 0

            reason = str(item.get("reason", "") or "").strip()
            entry_plan = str(item.get("entry_plan", "") or "").strip()
            target_guide = str(item.get("target_price_guide", "") or "").strip()
            stop_guide = str(item.get("stop_price_guide", "") or "").strip()

            lines.extend([
                f"{medal} **{rank}. {stock_name} ({stock_code})**",
                f"- 💰 종가: {close_price:,}원",
                f"- 🧠 선정 사유: {reason}",
                f"- 🎯 타점 전략: {entry_plan} / 목표가 가이드: {target_guide} / 손절가 가이드: {stop_guide}",
                ""
            ])

        lines.extend([
            "💡 **[수석 트레이더의 내일 장 원포인트 레슨]**",
            str(one_point_lesson or "").strip()
        ])
        return "\n".join(lines)


    def generate_eod_tomorrow_bundle(self, candidates_text):
        """
        장 마감 후 내일의 주도주 TOP5를
        1) 구조화 JSON
        2) 동일 데이터 기반 Markdown 리포트
        로 함께 반환
        """
        with self.lock:
            user_input = (
                f"🚨 [1차 필터링 완료: 내일의 주도주 후보군 15선]\n\n"
                f"{candidates_text}"
            )
            try:
                result = self._call_gemini_safe(
                    EOD_TOMORROW_LEADER_JSON_PROMPT,
                    user_input,
                    require_json=True,
                    context_name="종가베팅 TOP5 JSON",
                    model_override="gemini-pro-latest"
                )

                raw_top5 = result.get("top5", []) or []
                normalized = []

                for idx, item in enumerate(raw_top5[:5], start=1):
                    code = str(item.get("stock_code", "")).replace(".0", "").strip().zfill(6)
                    name = str(item.get("stock_name", "")).strip()
                    if not code or not name:
                        continue

                    try:
                        close_price = int(float(item.get("close_price", 0) or 0))
                    except Exception:
                        close_price = 0

                    try:
                        confidence = float(item.get("confidence", 0.0) or 0.0)
                    except Exception:
                        confidence = 0.0

                    try:
                        rank = int(item.get("rank", idx) or idx)
                    except Exception:
                        rank = idx

                    normalized.append({
                        "rank": rank,
                        "stock_name": name,
                        "stock_code": code,
                        "close_price": close_price,
                        "reason": str(item.get("reason", "") or "").strip(),
                        "entry_plan": str(item.get("entry_plan", "") or "").strip(),
                        "target_price_guide": str(item.get("target_price_guide", "") or "").strip(),
                        "stop_price_guide": str(item.get("stop_price_guide", "") or "").strip(),
                        "confidence": max(0.0, min(1.0, confidence)),
                    })

                market_summary = str(result.get("market_summary", "") or "").strip()
                one_point_lesson = str(result.get("one_point_lesson", "") or "").strip()
                report = self._render_eod_tomorrow_markdown(
                    market_summary=market_summary,
                    one_point_lesson=one_point_lesson,
                    top5=normalized
                )

                return {
                    "market_summary": market_summary,
                    "one_point_lesson": one_point_lesson,
                    "top5": normalized,
                    "report": report
                }

            except Exception as e:
                log_error(f"🚨 [종가베팅 번들] AI 에러: {e}")
                return {
                    "market_summary": "",
                    "one_point_lesson": "",
                    "top5": [],
                    "report": f"⚠️ AI 종가베팅 분석 생성 중 에러 발생: {e}"
                }


    def generate_eod_tomorrow_report(self, candidates_text):
        """장 마감 후 내일의 주도주 TOP 5 리포트 생성 (호환용)"""
        bundle = self.generate_eod_tomorrow_bundle(candidates_text)
        return bundle.get("report", "⚠️ EOD 리포트 생성 실패")
            
    