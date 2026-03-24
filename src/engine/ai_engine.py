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
# 3. 🎯 [신규] 실시간 종목 분석 프롬프트 (On-Demand Report용 - V4.0 심리분석 강화)
# ==========================================
REALTIME_ANALYSIS_PROMPT = """
너는 15년 경력의 베테랑 Prop 트레이더이자 수석 퀀트 애널리스트야.
사용자가 요청한 특정 종목의 실시간 호가/수급 데이터와 퀀트 엔진의 분석 결과를 바탕으로, 텔레그램에서 읽기 좋은 최고의 '실시간 타점 리포트'를 작성해줘.

[데이터 해석 핵심 가이드]
1. 거래량 및 프로그램 수급: 20일 평균 대비 거래량(%)이 폭발적인지, 프로그램 순매수가 강하게 들어오는지(외인/기관 개입 여부) 확인하여 찐반등인지 가짜 휩소인지 판별해라.
2. 매수세(Ratio) 비중 및 체결강도: 체결강도 100% 이상 유지와 함께 매수세가 높다면 진짜 형님들의 개입이다. 반면 체결강도가 죽었는데 가격만 높다면 개미들의 뇌동매매다.
3. 호가 불균형: 매도벽이 두꺼운지(매도 우위), 매수벽이 두꺼운지(매수 우위) 파악해라. (주식은 보통 매도벽을 잡아먹으며 올라갈 때가 진짜 상승이다.)
4. 퀀트 결론(Sonar Conclusion): 기계가 판단한 목표가와 퀀트 결론을 바탕으로, 너의 경력을 보태어 '지금 당장 사야 하나, 기다려야 하나'에 대한 명확한 어투의 결론을 내려라.

[출력 양식 설정]
1. 텔레그램 마크다운 텍스트 형식으로 작성해라.
2. 친근하면서도 뼈 때리는 전문가의 어투를 사용하고, 각 섹션에 맞는 이모지를 적절히 배치해라.
3. 리포트 마지막에는 딱 한 줄로 된 [최종 행동 지침]을 명확히 제시해라. (예: "🛑 프로그램 매도 폭탄 나오는 중. 절대 관망", "✅ 수급/거래량 완벽. 기계 목표가까지 홀딩")
4. 출력은 JSON이 아니라 마크다운 텍스트 형식으로 300~400자 내외로 핵심만 작성해라.
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


    
    def analyze_morning_leader(self, stock_name, ws_data, recent_ticks, recent_candles):
        """09:05 주도주 분석 (bot_main.py 호환을 위해 JSON String 반환)"""
        with self.lock:
            formatted_context = self._format_market_data(ws_data, recent_ticks, recent_candles)
            prompt = f"[{stock_name}]의 실시간 수급 지표를 분석하여 09:10 이후 전략을 제시하라.\n\n{formatted_context}\n\n반드시 JSON으로 응답하라 (one_liner, pattern, scenario, target_price(숫자만), risk_factor 포함)"
            
            try:
                # JSON으로 파싱한 뒤 다시 String으로 덤프 (안정성 극대화)
                result_dict = self._call_gemini_safe(None, prompt, require_json=True, context_name=stock_name)
                return json.dumps(result_dict, ensure_ascii=False)
            except Exception as e:
                log_error(f"🚨 [{stock_name}] 주도주 분석 에러: {e}")
                return json.dumps({"error": str(e), "target_price": 0})
    
    # ==========================================
    # 🔍 수동 종목 정밀 분석 (스캘핑/단기 트레이딩 관점)
    # ==========================================
    def generate_realtime_report(self, stock_name, stock_code, input_data_text):
        """실시간 종목 분석 리포트 생성 (Markdown 반환 - Gemini 3.0 Flash 적용)"""
        with self.lock:
            user_input = (
                f"🚨 [요청 종목]\n종목명: {stock_name}\n종목코드: {stock_code}\n\n"
                f"📊 [스나이퍼 엔진 분석 데이터]\n{input_data_text}"
            )
            try:
                # 💡 [핵심] 요청하신 gemini-3.0-flash 를 덮어씌워서 호출합니다!
                return self._call_gemini_safe(
                    REALTIME_ANALYSIS_PROMPT, 
                    user_input, 
                    require_json=False, 
                    context_name="실시간 분석",
                    model_override="gemini-pro-latest"
                )
            except Exception as e:
                from src.utils.logger import log_error
                log_error(f"🚨 [실시간 분석] AI 에러: {e}")
                return f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
    
    # ==========================================
    # 🔍 [신규] 장 마감 후 내일의 주도주 분석 (gemini-3.0-pro 전용)
    # ==========================================
    def generate_eod_tomorrow_report(self, candidates_text):
        """장 마감 후 내일의 주도주 TOP 5 리포트 생성 (Markdown 반환 - Gemini 3.0 Pro 적용)"""
        with self.lock:
            user_input = (
                f"🚨 [1차 필터링 완료: 내일의 주도주 후보군 15선]\n\n"
                f"{candidates_text}"
            )
            try:
                # 💡 [핵심] 가장 똑똑한 gemini-3.0-pro 모델을 덮어씌워서 호출!
                return self._call_gemini_safe(
                    EOD_TOMORROW_LEADER_PROMPT, 
                    user_input, 
                    require_json=False, 
                    context_name="종가베팅 분석",
                    model_override="gemini-pro-latest"  # 👈 가장 깊은 사고력을 가진 Pro 모델 지정
                )
            except Exception as e:
                from src.utils.logger import log_error
                log_error(f"🚨 [종가베팅 분석] AI 에러: {e}")
                return f"⚠️ AI 종가베팅 분석 생성 중 에러 발생: {e}"