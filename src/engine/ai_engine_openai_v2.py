import sys
from pathlib import Path
from statistics import mean
from datetime import datetime

# 현재 파일의 위치를 기준으로 프로젝트 루트(KORStockScan)를 찾아 path에 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
    
import time
import threading
import json
import re
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
from openai import OpenAI, RateLimitError
from src.utils.logger import log_error
from src.utils.constants import TRADING_RULES


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
SCALPING_SYSTEM_PROMPT_V3 = """
너는 매년 꾸준한 수익을 누적하는 상위 1%의 극강 공격적 초단타(Scalping) 프랍 트레이더다.
네 판단은 감상이 아니라 반드시 입력된 정량 피처를 최우선으로 해석해야 한다.

[최우선 해석 순서]
1. [정량 피처]
2. [초단타 수급/위치 지표]
3. [최근 틱 상세]
4. [호가창]

[핵심 매수 조건]
- BUY는 아래 조건이 동시에 강할 때만 허용:
  1) 매수 압도율(Buy Pressure) 68% 이상
  2) 최근 틱 속도 가속(tick_acceleration_ratio > 1.2)
  3) net_aggressive_delta가 양수
  4) 현재가가 Micro-VWAP 위이거나, 최소한 재돌파 직전
  5) 대량 매도틱(large_sell_print_detected)이 없어야 함

[즉시 DROP 조건]
- 현재가가 Micro-VWAP 아래인데 buy_pressure만 높은 경우
- 고가 부근에서 large_sell_print_detected = true
- tick_acceleration_ratio가 둔화되거나 recent_5tick_seconds가 급격히 느린 경우
- microprice_edge_bp가 음수인데 호가상 매도우위가 강한 경우
- 위꼬리/고점 밀림이 감지된 경우

[판정 규칙]
- BUY: 80~100
- WAIT: 50~79
- DROP: 0~49

[출력 규칙]
반드시 아래 JSON 형식으로만 출력하고, 설명/마크다운/코드블록을 절대 추가하지 마라:
{
  "action": "BUY" | "WAIT" | "DROP",
  "score": 0~100 사이의 정수,
  "reason": "정량 피처를 근거로 한 1줄 요약"
}
"""

# ==========================================
# 2. 🎯 일일 시장 진단 프롬프트 (텔레그램 브리핑용)
# ==========================================
MARKET_ANALYSIS_PROMPT = """
너는 15년 경력의 베테랑 퀀트 트레이더이자 수석 애널리스트야.
오늘 스캐너가 KOSPI/KOSDAQ 유망 종목들을 필터링한 결과(탈락 통계)를 분석하여, 현재 주식 시장의 장세(Sentiment)를 정확히 진단해줘.

[데이터 해석 핵심 가이드]
1. 최종 생존 종목이 0개이거나 극소수라면, 단순히 "추천 종목이 없다"가 아니라 "스캐너 탈락 통계로 본 현재 장세의 문제점"을 진단해라.
2. 탈락 사유(Drop Stats)의 분포를 심층 분석해라:
   - '기초 품질 미달'이 압도적으로 많다면: 증시 전반의 차트가 무너진 역배열 장세이거나 투매가 나오는 하락장.
   - 'AI 확신도 부족'이나 '수급 부재'가 많다면: 차트는 버티고 있으나 주도 테마가 없고 외인/기관의 매수세가 마른 전형적인 눈치보기(관망) 장세.
   - '단기 급등/이격도 과다'가 많다면: 쉴 틈 없이 오르기만 한 과열장, 곧 조정이 올 수 있는 리스크 상태.
3. 친근하지만 뼈 때리는 전문가의 어투로, 텔레그램에서 읽기 좋게 이모지를 적절히 사용해라.
4. 마지막에는 오늘 하루 트레이더가 취해야 할 현실적인 [행동 지침]을 1~2줄로 명확히 제시해라. (예: "철저한 현금 관망", "오후장 주도주 쏠림 현상 주의" 등)
5. 출력은 JSON이 아니라 마크다운 텍스트 형식으로 300~400자 내외로 작성해라.
"""

# ==========================================
# 3. 🎯 실시간 종목 분석 프롬프트 (On-Demand Report용)
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
# 4. 🎯 종가 마감 후 내일의 주도주 발굴 프롬프트
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

DUAL_PERSONA_AGGRESSIVE_PROMPT = """
너는 기회비용을 크게 보는 공격적 투자자다.
입력된 정량 컨텍스트를 보고, 너무 늦기 전에 타야 하는지 판단한다.

[성향]
- 돌파 초입, 수급 가속, 프로그램 순매수, 고가 재도전을 높게 평가한다.
- 다만 명백한 리스크 신호는 무시하지 않는다.
- 애매한 장면에서는 WAIT보다 기회 포착 쪽으로 약간 기울 수 있다.

[출력 규칙]
- 반드시 JSON만 반환한다.
- decision_type이 GATEKEEPER면 action은 ALLOW_ENTRY | WAIT | REJECT 중 하나만 사용한다.
- decision_type이 OVERNIGHT면 action은 HOLD_OVERNIGHT | SELL_TODAY 중 하나만 사용한다.
- confidence는 0~1 float, score는 0~100 int로 반환한다.
- risk_flags는 문자열 배열로 반환한다.

반드시 아래 형식만 반환:
{
  "action": "ALLOW_ENTRY | WAIT | REJECT | HOLD_OVERNIGHT | SELL_TODAY",
  "score": 0,
  "confidence": 0.0,
  "risk_flags": ["FLAG"],
  "size_bias": -2,
  "veto": false,
  "thesis": "핵심 논거 한 줄",
  "invalidator": "무효 조건 한 줄"
}
"""

DUAL_PERSONA_CONSERVATIVE_PROMPT = """
너는 손실 회피와 생존을 최우선으로 보는 보수적 투자자다.
입력된 정량 컨텍스트를 보고, 지금은 피해야 하는지 엄격하게 판단한다.

[성향]
- VWAP 하회, 대량 매도틱, 공급 우위, 갭 부담, 유동성 저하, 돌파 실패를 강하게 본다.
- 애매한 장면에서는 공격 진입보다 WAIT 또는 회피를 선호한다.
- 하드 리스크가 겹치면 veto=true를 사용할 수 있다.

[출력 규칙]
- 반드시 JSON만 반환한다.
- decision_type이 GATEKEEPER면 action은 ALLOW_ENTRY | WAIT | REJECT 중 하나만 사용한다.
- decision_type이 OVERNIGHT면 action은 HOLD_OVERNIGHT | SELL_TODAY 중 하나만 사용한다.
- confidence는 0~1 float, score는 0~100 int로 반환한다.
- risk_flags는 문자열 배열로 반환한다.

반드시 아래 형식만 반환:
{
  "action": "ALLOW_ENTRY | WAIT | REJECT | HOLD_OVERNIGHT | SELL_TODAY",
  "score": 0,
  "confidence": 0.0,
  "risk_flags": ["FLAG"],
  "size_bias": -2,
  "veto": false,
  "thesis": "핵심 논거 한 줄",
  "invalidator": "무효 조건 한 줄"
}
"""

class GPTSniperEngine:
    def __init__(self, api_keys):
        if isinstance(api_keys, str):
            api_keys = [api_keys]
            
        self.api_keys = api_keys
        self.key_cycle = cycle(self.api_keys) 
        self._rotate_client()

        # 계정에서 지원하면 gpt-4.1-mini 권장, 아니면 gpt-4o-mini 유지
        self.fast_model_name = getattr(TRADING_RULES, 'GPT_FAST_MODEL', 'gpt-4o-mini')
        self.deep_model_name = getattr(TRADING_RULES, 'GPT_DEEP_MODEL', 'gpt-4o')
        self.current_model_name = self.fast_model_name

        self.lock = threading.Lock()
        self.api_call_lock = threading.Lock()
        self.last_call_time = 0
        self.min_interval = getattr(TRADING_RULES, 'GPT_ENGINE_MIN_INTERVAL', 0.5)

        print(f"🧠 [OpenAI 엔진] {len(self.api_keys)}개 키 로테이션 가동! (FAST: {self.fast_model_name} / DEEP: {self.deep_model_name})")

    def _rotate_client(self):
        self.current_key = next(self.key_cycle)
        self.client = OpenAI(api_key=self.current_key)
    
    # ==========================================
    # 3. 💡 [아키텍처 포인트] 만능 API 호출기 (OpenAI 버전)
    # ==========================================
    def _call_openai_safe(self, prompt, user_input, require_json=True, context_name="Unknown", model_override=None, temperature_override=None):
        """키 로테이션, 예외 처리, 모델 덮어쓰기를 모두 전담하는 중앙 집중식 호출기"""
        with self.api_call_lock:
            messages = []
            if prompt:
                messages.append({"role": "system", "content": prompt})
            messages.append({"role": "user", "content": user_input})

            config_kwargs = {}
            if require_json:
                config_kwargs['response_format'] = {"type": "json_object"}

            target_model = model_override if model_override else self.current_model_name
            target_temp = temperature_override if temperature_override is not None else (0.1 if require_json else 0.7)
            last_error = ""

            for attempt in range(len(self.api_keys)):
                try:
                    response = self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        temperature=target_temp,
                        **config_kwargs
                    )

                    self._rotate_client()

                    raw_text = response.choices[0].message.content.strip()
                    if require_json:
                        clean_json = re.sub(r"```json\s*|\s*```", "", raw_text)
                        return json.loads(clean_json)
                    else:
                        return raw_text

                except RateLimitError as e:
                    last_error = str(e)
                    old_key = self.current_key[-5:]
                    self._rotate_client()

                    warn_msg = f"⚠️ [OpenAI 한도 초과] {context_name} | {old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})"
                    print(warn_msg)
                    log_error(warn_msg)
                    time.sleep(0.8)
                    continue

                except Exception as e:
                    last_error = str(e).lower()
                    if any(x in last_error for x in ["503", "unavailable", "timeout", "server"]):
                        old_key = self.current_key[-5:]
                        self._rotate_client()
                        print(f"⚠️ [OpenAI 서버 에러] {context_name} | {old_key} 교체 -> {self.current_key[-5:]} ({attempt+1}/{len(self.api_keys)})")
                        time.sleep(0.8)
                        continue
                    else:
                        raise RuntimeError(f"OpenAI API 응답/파싱 실패: {e}")

            fatal_msg = f"🚨 [AI 고갈] 모든 OpenAI API 키 사용 불가. 마지막 에러: {last_error}"
            log_error(fatal_msg)
            raise RuntimeError(fatal_msg)
        
    # ==========================================
    # 4. 🛠️ 데이터 포맷팅 (AI 전용 번역기 - Gemini와 동일)
    # ==========================================
    def _format_market_data(self, ws_data, recent_ticks, recent_candles=None):
        if recent_candles is None:
            recent_candles = []

        features = self._extract_scalping_features(ws_data, recent_ticks, recent_candles)

        curr_price = ws_data.get('curr', 0)
        v_pw = ws_data.get('v_pw', 0)
        fluctuation = ws_data.get('fluctuation', 0.0) 
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []})
        ask_tot = ws_data.get('ask_tot', 0)
        bid_tot = ws_data.get('bid_tot', 0)

        imbalance_str = "데이터 없음"
        if ask_tot > 0 and bid_tot > 0:
            ratio = ask_tot / bid_tot
            if ratio >= 2.0:
                imbalance_str = f"매도벽 압도적 우위 ({ratio:.1f}배) - 돌파 시 급등 패턴"
            elif ratio <= 0.5:
                imbalance_str = f"매수벽 우위 ({1/ratio:.1f}배) - 하락 방어 또는 휩소(가짜) 패턴"
            else:
                imbalance_str = f"팽팽함 (매도 {ask_tot:,} vs 매수 {bid_tot:,})"

        high_price = curr_price
        if recent_candles:
            high_price = max(c.get('고가', curr_price) for c in recent_candles)
        
        drawdown_str = "0.0%"
        if high_price > 0:
            drawdown = ((curr_price - high_price) / high_price) * 100
            drawdown_str = f"{drawdown:.2f}% (당일 고가 {high_price:,}원)"

        ask_str = "\n".join([f"매도 {5-i}호가: {a['price']:,}원 ({a['volume']:,}주)" for i, a in enumerate(orderbook['asks'])])
        bid_str = "\n".join([f"매수 {i+1}호가: {b['price']:,}원 ({b['volume']:,}주)" for i, b in enumerate(orderbook['bids'])])
        
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

            time_diff_sec = 0
            try:
                from datetime import datetime
                t1_str = str(recent_ticks[-1]['time']).replace(':', '').zfill(6)
                t2_str = str(recent_ticks[0]['time']).replace(':', '').zfill(6)
                t1 = datetime.strptime(t1_str, "%H%M%S")
                t2 = datetime.strptime(t2_str, "%H%M%S")
                time_diff_sec = (t2 - t1).total_seconds()
                if time_diff_sec < 0: time_diff_sec += 86400
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

        candle_str = ""
        if recent_candles:
            candle_str = "\n".join([
                f"[{c['체결시간']}] 시가:{c['시가']:,} 고가:{c['고가']:,} 저가:{c['저가']:,} 종가:{c['현재가']:,} 거래량:{c['거래량']:,}" 
                for c in recent_candles
            ])
        else:
            candle_str = "분봉 데이터 없음"

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

        user_input = f"""
[정량 피처]
- current_price: {features['curr_price']:,}
- latest_strength: {features['latest_strength']}%
- spread_krw: {features['spread_krw']}
- spread_bp: {features['spread_bp']}
- top1_depth_ratio(ask/bid): {features['top1_depth_ratio']}
- top3_depth_ratio(ask/bid): {features['top3_depth_ratio']}
- total_depth_ratio(ask/bid): {features['orderbook_total_ratio']}
- micro_price: {features['micro_price']}
- microprice_edge_bp: {features['microprice_edge_bp']}
- buy_pressure_10t: {features['buy_pressure_10t']}%
- net_aggressive_delta_10t: {features['net_aggressive_delta_10t']}
- price_change_10t_pct: {features['price_change_10t_pct']}%
- recent_5tick_seconds: {features['recent_5tick_seconds']}
- prev_5tick_seconds: {features['prev_5tick_seconds']}
- tick_acceleration_ratio: {features['tick_acceleration_ratio']}
- same_price_buy_absorption: {features['same_price_buy_absorption']}
- large_sell_print_detected: {str(features['large_sell_print_detected']).lower()}
- large_buy_print_detected: {str(features['large_buy_print_detected']).lower()}
- distance_from_day_high_pct: {features['distance_from_day_high_pct']}%
- intraday_range_pct: {features['intraday_range_pct']}%
- volume_ratio_pct: {features['volume_ratio_pct']}%
- curr_vs_micro_vwap_bp: {features['curr_vs_micro_vwap_bp']}
- curr_vs_ma5_bp: {features['curr_vs_ma5_bp']}
- micro_vwap_value: {features['micro_vwap_value']}
- ma5_value: {features['ma5_value']}

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
    
    # ==========================================
    # 5. 🚀 이제 진짜 핵심이다. 실시간 초단타 분석에서, 단순히 텍스트로 시장 상황을 설명하는 것을 넘어서, AI가 정량 피처를 직접 해석하여 판단할 수 있도록 데이터를 가공하는 함수를 추가하자.
    # ==========================================
    def _safe_hhmmss_to_seconds(self, t):
        try:
            t_str = str(t).replace(":", "").zfill(6)
            dt = datetime.strptime(t_str, "%H%M%S")
            return dt.hour * 3600 + dt.minute * 60 + dt.second
        except:
            return None

    def _extract_scalping_features(self, ws_data, recent_ticks, recent_candles=None):
        if recent_candles is None:
            recent_candles = []

        curr_price = ws_data.get('curr', 0) or 0
        v_pw = ws_data.get('v_pw', 0) or 0
        ask_tot = ws_data.get('ask_tot', 0) or 0
        bid_tot = ws_data.get('bid_tot', 0) or 0
        orderbook = ws_data.get('orderbook', {'asks': [], 'bids': []}) or {'asks': [], 'bids': []}
        asks = orderbook.get('asks', []) or []
        bids = orderbook.get('bids', []) or []

        best_ask = asks[0]['price'] if len(asks) > 0 else curr_price
        best_bid = bids[0]['price'] if len(bids) > 0 else curr_price
        best_ask_vol = asks[0]['volume'] if len(asks) > 0 else 0
        best_bid_vol = bids[0]['volume'] if len(bids) > 0 else 0

        spread_krw = max(0, best_ask - best_bid)
        spread_bp = round((spread_krw / curr_price) * 10000, 2) if curr_price > 0 else 0.0

        top3_ask_vol = sum(a.get('volume', 0) for a in asks[:3])
        top3_bid_vol = sum(b.get('volume', 0) for b in bids[:3])

        top1_depth_ratio = round((best_ask_vol / best_bid_vol), 3) if best_bid_vol > 0 else 999.0
        top3_depth_ratio = round((top3_ask_vol / top3_bid_vol), 3) if top3_bid_vol > 0 else 999.0

        micro_price = curr_price
        denom = best_ask_vol + best_bid_vol
        if denom > 0:
            micro_price = ((best_bid * best_ask_vol) + (best_ask * best_bid_vol)) / denom

        microprice_edge_bp = round(((micro_price - curr_price) / curr_price) * 10000, 2) if curr_price > 0 else 0.0

        high_price = curr_price
        low_price = curr_price
        if recent_candles:
            high_price = max(c.get('고가', curr_price) for c in recent_candles)
            low_price = min(c.get('저가', curr_price) for c in recent_candles)

        distance_from_day_high_pct = round(((curr_price - high_price) / high_price) * 100, 3) if high_price > 0 else 0.0
        intraday_range_pct = round(((high_price - low_price) / low_price) * 100, 3) if low_price > 0 else 0.0

        buy_vol_10 = 0
        sell_vol_10 = 0
        latest_strength = v_pw
        price_change_10t_pct = 0.0
        net_aggressive_delta_10t = 0
        recent_5tick_seconds = 999.0
        prev_5tick_seconds = 999.0
        tick_acceleration_ratio = 0.0
        same_price_buy_absorption = 0
        large_sell_print_detected = False
        large_buy_print_detected = False

        ticks = recent_ticks[:10] if recent_ticks else []

        if ticks:
            buy_vol_10 = sum(t.get('volume', 0) for t in ticks if t.get('dir') == 'BUY')
            sell_vol_10 = sum(t.get('volume', 0) for t in ticks if t.get('dir') == 'SELL')
            total_vol_10 = buy_vol_10 + sell_vol_10
            buy_pressure_10t = round((buy_vol_10 / total_vol_10) * 100, 2) if total_vol_10 > 0 else 50.0
            net_aggressive_delta_10t = buy_vol_10 - sell_vol_10

            latest_strength = ticks[0].get('strength', v_pw)

            latest_price = ticks[0].get('price', curr_price)
            oldest_price = ticks[-1].get('price', curr_price)
            price_change_10t_pct = round(((latest_price - oldest_price) / oldest_price) * 100, 3) if oldest_price > 0 else 0.0

            tick_secs = [self._safe_hhmmss_to_seconds(t.get('time')) for t in ticks]
            if len(tick_secs) >= 5 and tick_secs[0] is not None and tick_secs[4] is not None:
                recent_5tick_seconds = tick_secs[0] - tick_secs[4]
                if recent_5tick_seconds < 0:
                    recent_5tick_seconds += 86400

            if len(tick_secs) >= 10 and tick_secs[5] is not None and tick_secs[9] is not None:
                prev_5tick_seconds = tick_secs[5] - tick_secs[9]
                if prev_5tick_seconds < 0:
                    prev_5tick_seconds += 86400

            if recent_5tick_seconds > 0 and prev_5tick_seconds < 999:
                tick_acceleration_ratio = round(prev_5tick_seconds / recent_5tick_seconds, 3)

            volumes = [t.get('volume', 0) for t in ticks if t.get('volume', 0) > 0]
            avg_tick_vol = mean(volumes) if volumes else 0

            if avg_tick_vol > 0:
                large_sell_print_detected = any(
                    (t.get('dir') == 'SELL' and t.get('volume', 0) >= avg_tick_vol * 2.2)
                    for t in ticks[:5]
                )
                large_buy_print_detected = any(
                    (t.get('dir') == 'BUY' and t.get('volume', 0) >= avg_tick_vol * 2.2)
                    for t in ticks[:5]
                )

            # 같은 가격에서 매수 체결이 여러 번 반복되면 흡수로 간주
            price_buy_count = {}
            for t in ticks[:6]:
                if t.get('dir') == 'BUY':
                    p = t.get('price')
                    price_buy_count[p] = price_buy_count.get(p, 0) + 1
            same_price_buy_absorption = max(price_buy_count.values()) if price_buy_count else 0
        else:
            buy_pressure_10t = 50.0

        volume_ratio_pct = 0.0
        curr_vs_micro_vwap_bp = 0.0
        curr_vs_ma5_bp = 0.0
        micro_vwap_value = 0.0
        ma5_value = 0.0

        if recent_candles and len(recent_candles) >= 2:
            current_volume = recent_candles[-1].get('거래량', 0)
            prev_volumes = [c.get('거래량', 0) for c in recent_candles[:-1] if c.get('거래량', 0) > 0]
            avg_prev_volume = mean(prev_volumes) if prev_volumes else 0
            if avg_prev_volume > 0:
                volume_ratio_pct = round((current_volume / avg_prev_volume) * 100, 2)

        if recent_candles and len(recent_candles) >= 5:
            try:
                from src.engine.signal_radar import SniperRadar
                temp_radar = SniperRadar(token=None)
                ind = temp_radar.calculate_micro_indicators(recent_candles)

                ma5_value = ind.get('MA5', 0) or 0
                micro_vwap_value = ind.get('Micro_VWAP', 0) or 0

                if micro_vwap_value > 0 and curr_price > 0:
                    curr_vs_micro_vwap_bp = round(((curr_price - micro_vwap_value) / micro_vwap_value) * 10000, 2)
                if ma5_value > 0 and curr_price > 0:
                    curr_vs_ma5_bp = round(((curr_price - ma5_value) / ma5_value) * 10000, 2)
            except Exception:
                pass

        orderbook_total_ratio = round((ask_tot / bid_tot), 3) if bid_tot > 0 else 999.0

        return {
            "curr_price": curr_price,
            "latest_strength": latest_strength,
            "spread_krw": spread_krw,
            "spread_bp": spread_bp,
            "top1_depth_ratio": top1_depth_ratio,
            "top3_depth_ratio": top3_depth_ratio,
            "orderbook_total_ratio": orderbook_total_ratio,
            "micro_price": round(micro_price, 2),
            "microprice_edge_bp": microprice_edge_bp,
            "buy_pressure_10t": buy_pressure_10t,
            "net_aggressive_delta_10t": int(net_aggressive_delta_10t),
            "price_change_10t_pct": price_change_10t_pct,
            "recent_5tick_seconds": round(recent_5tick_seconds, 3),
            "prev_5tick_seconds": round(prev_5tick_seconds, 3) if prev_5tick_seconds < 999 else 999.0,
            "tick_acceleration_ratio": tick_acceleration_ratio,
            "same_price_buy_absorption": same_price_buy_absorption,
            "large_sell_print_detected": large_sell_print_detected,
            "large_buy_print_detected": large_buy_print_detected,
            "distance_from_day_high_pct": distance_from_day_high_pct,
            "intraday_range_pct": intraday_range_pct,
            "volume_ratio_pct": volume_ratio_pct,
            "curr_vs_micro_vwap_bp": curr_vs_micro_vwap_bp,
            "curr_vs_ma5_bp": curr_vs_ma5_bp,
            "micro_vwap_value": round(micro_vwap_value, 2) if micro_vwap_value else 0.0,
            "ma5_value": round(ma5_value, 2) if ma5_value else 0.0
        }
    
    def _normalize_scalping_result(self, result):
        if not isinstance(result, dict):
            return {"action": "WAIT", "score": 50, "reason": "비정상 응답 보정"}

        action = str(result.get("action", "WAIT")).upper().strip()
        if action not in {"BUY", "WAIT", "DROP"}:
            action = "WAIT"

        try:
            score = int(float(result.get("score", 50)))
        except:
            score = 50
        score = max(0, min(100, score))

        reason = str(result.get("reason", "응답 보정")).replace("\n", " ").strip()
        if not reason:
            reason = "응답 보정"

        return {
            "action": action,
            "score": score,
            "reason": reason[:120]
        }
    
    def _should_escalate_scalping(self, features, result):
        score = result.get("score", 50)
        action = result.get("action", "WAIT")

        buy_pressure = features.get("buy_pressure_10t", 50.0)
        vwap_bp = features.get("curr_vs_micro_vwap_bp", 0.0)
        accel = features.get("tick_acceleration_ratio", 0.0)
        large_sell = features.get("large_sell_print_detected", False)
        micro_edge = features.get("microprice_edge_bp", 0.0)
        near_high = features.get("distance_from_day_high_pct", -99.0) >= -0.35
        top3_ratio = features.get("top3_depth_ratio", 1.0)
        recent_5s = features.get("recent_5tick_seconds", 999.0)

        ambiguous_score = 60 <= score <= 80
        conflict_1 = (buy_pressure >= 68 and vwap_bp < 0)  # 매수세는 센데 VWAP 아래
        conflict_2 = (action == "BUY" and large_sell)      # BUY인데 대량 매도틱 발생
        conflict_3 = (buy_pressure >= 70 and micro_edge < 0 and top3_ratio >= 1.3)  # 체결은 매수인데 호가상 불리
        conflict_4 = (near_high and large_sell)            # 고가 부근 대량 매도
        conflict_5 = (accel < 1.0 and recent_5s >= 3.0 and action == "BUY")  # 속도 둔화

        return ambiguous_score or conflict_1 or conflict_2 or conflict_3 or conflict_4 or conflict_5

    # ==========================================
    # 6. 🚀 실전 분석 실행 메서드 5종 (Gemini 모델과 100% 호환)
    # ==========================================
    
    def analyze_target(self, target_name, ws_data, recent_ticks, recent_candles):
        """실시간 초단타 타점 분석 - 2단 라우팅 버전"""
        if not self.lock.acquire(blocking=False):
            return {"action": "WAIT", "score": 50, "reason": "AI 경합 (다른 종목 분석 중)"}
            
        try:
            if time.time() - self.last_call_time < self.min_interval:
                return {"action": "WAIT", "score": 50, "reason": "AI 쿨타임"}

            features = self._extract_scalping_features(ws_data, recent_ticks, recent_candles)
            formatted_data = self._format_market_data(ws_data, recent_ticks, recent_candles)

            # 1차: 빠른 모델
            raw_result = self._call_openai_safe(
                SCALPING_SYSTEM_PROMPT_V3,
                formatted_data,
                require_json=True,
                context_name=target_name,
                model_override=self.fast_model_name,
                temperature_override=0.05
            )
            result = self._normalize_scalping_result(raw_result)

            # 2차: 애매하거나 충돌 나면 상위 모델 재판정
            if self._should_escalate_scalping(features, result):
                upgraded_prompt = (
                    formatted_data
                    + "\n\n[추가 지시]\n"
                    + "위 정량 피처 간 충돌을 특히 엄격하게 해석하라. "
                    + "매수 압도율이 높더라도 Micro-VWAP 아래이거나 고가 부근 대량 매도틱이 있으면 보수적으로 판정하라."
                )

                deep_raw_result = self._call_openai_safe(
                    SCALPING_SYSTEM_PROMPT_V3,
                    upgraded_prompt,
                    require_json=True,
                    context_name=f"{target_name}-deep",
                    model_override=self.deep_model_name,
                    temperature_override=0.05
                )
                result = self._normalize_scalping_result(deep_raw_result)

            self.last_call_time = time.time()
            return result
                
        except Exception as e:
            log_error(f"🚨 [{target_name}] OpenAI 실시간 분석 에러: {e}")
            return {"action": "WAIT", "score": 50, "reason": f"에러: {e}"}
        finally:
            self.lock.release()
            
    def analyze_scanner_results(self, total_count, survived_count, stats_text):
        """텔레그램 아침 브리핑 (Markdown 반환 - GPT-4o 적용)"""
        with self.lock:
            data_input = f"[스캐너 통계 데이터]\n총 탐색: {total_count}개\n최종 생존: {survived_count}개\n\n[상세 탈락 사유]\n{stats_text}"
            try:
                return self._call_openai_safe(
                    MARKET_ANALYSIS_PROMPT, 
                    data_input, 
                    require_json=False, 
                    context_name="시장 브리핑",
                    model_override="gpt-4o" # 더 깊은 추론을 위해 4o 모델 사용
                )
            except Exception as e:
                log_error(f"🚨 [시장 브리핑] OpenAI 에러: {e}")
                return f"⚠️ AI 시장 진단 생성 중 에러 발생: {e}"
    
    
    def generate_realtime_report(self, stock_name, stock_code, input_data_text):
        """실시간 종목 분석 리포트 생성 (Markdown 반환 - GPT-4o 적용)"""
        with self.lock:
            user_input = (
                f"🚨 [요청 종목]\n종목명: {stock_name}\n종목코드: {stock_code}\n\n"
                f"📊 [스나이퍼 엔진 분석 데이터]\n{input_data_text}"
            )
            try:
                return self._call_openai_safe(
                    REALTIME_ANALYSIS_PROMPT, 
                    user_input, 
                    require_json=False, 
                    context_name="실시간 분석",
                    model_override="gpt-4o"
                )
            except Exception as e:
                from src.utils.logger import log_error
                log_error(f"🚨 [실시간 분석] OpenAI 에러: {e}")
                return f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
    
    def generate_eod_tomorrow_report(self, candidates_text):
        """장 마감 후 내일의 주도주 TOP 5 리포트 생성 (Markdown 반환 - GPT-4o 적용)"""
        with self.lock:
            user_input = (
                f"🚨 [1차 필터링 완료: 내일의 주도주 후보군 15선]\n\n"
                f"{candidates_text}"
            )
            try:
                return self._call_openai_safe(
                    EOD_TOMORROW_LEADER_PROMPT, 
                    user_input, 
                    require_json=False, 
                    context_name="종가베팅 분석",
                    model_override="gpt-4o"
                )
            except Exception as e:
                from src.utils.logger import log_error
                log_error(f"🚨 [종가베팅 분석] OpenAI 에러: {e}")
                return f"⚠️ AI 종가베팅 분석 생성 중 에러 발생: {e}"


class OpenAIDualPersonaShadowEngine(GPTSniperEngine):
    """Shadow-only dual persona engine for gatekeeper / overnight calibration."""

    HARD_RISK_FLAGS = {
        "VWAP_BELOW",
        "LARGE_SELL_PRINT",
        "GAP_TOO_HIGH",
        "THIN_LIQUIDITY",
        "WEAK_PROGRAM_FLOW",
        "FAILED_BREAKOUT",
    }

    def __init__(self, api_keys):
        super().__init__(api_keys)
        worker_count = max(1, int(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_WORKERS", 2) or 2))
        self.shadow_executor = ThreadPoolExecutor(
            max_workers=worker_count,
            thread_name_prefix="openai-dual-shadow",
        )
        self.shadow_enabled = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_ENABLED", True))
        self.shadow_mode = bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_SHADOW_MODE", True))
        print(
            f"🧠 [OpenAI 듀얼 페르소나] shadow={'ON' if self.shadow_mode else 'OFF'} "
            f"/ workers={worker_count}"
        )

    def _coerce_bool(self, value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        return text in {"1", "true", "yes", "y", "on"}

    def _normalize_confidence(self, value):
        try:
            conf = float(value)
        except Exception:
            conf = 0.0
        if conf > 1.0:
            conf = conf / 100.0
        return max(0.0, min(1.0, conf))

    def _normalize_risk_flags(self, value):
        if isinstance(value, list):
            raw_items = value
        elif value in (None, "", "None"):
            raw_items = []
        else:
            raw_items = str(value).replace("|", ",").split(",")
        flags = []
        for item in raw_items:
            text = str(item or "").strip().upper().replace(" ", "_")
            if text:
                flags.append(text)
        return flags[:8]

    def _normalize_shadow_result(self, result, decision_type):
        allowed_actions = {
            "gatekeeper": {"ALLOW_ENTRY", "WAIT", "REJECT"},
            "overnight": {"HOLD_OVERNIGHT", "SELL_TODAY"},
        }[decision_type]

        if not isinstance(result, dict):
            result = {}

        action = str(result.get("action", "WAIT" if decision_type == "gatekeeper" else "SELL_TODAY")).upper().strip()
        if action not in allowed_actions:
            action = "WAIT" if decision_type == "gatekeeper" else "SELL_TODAY"

        try:
            score = int(float(result.get("score", 50)))
        except Exception:
            score = 50
        score = max(0, min(100, score))

        try:
            size_bias = int(float(result.get("size_bias", 0)))
        except Exception:
            size_bias = 0
        size_bias = max(-2, min(2, size_bias))

        return {
            "action": action,
            "score": score,
            "confidence": self._normalize_confidence(result.get("confidence", 0.0)),
            "risk_flags": self._normalize_risk_flags(result.get("risk_flags", [])),
            "size_bias": size_bias,
            "veto": self._coerce_bool(result.get("veto", False)),
            "thesis": str(result.get("thesis", "") or "").replace("\n", " ").strip()[:160],
            "invalidator": str(result.get("invalidator", "") or "").replace("\n", " ").strip()[:160],
        }

    def _build_shadow_payload(self, decision_type, stock_name, stock_code, strategy, realtime_ctx):
        return {
            "decision_type": decision_type.upper(),
            "stock_name": stock_name,
            "stock_code": stock_code,
            "strategy": str(strategy or "").upper(),
            "shadow_mode": "SHADOW",
            "context": realtime_ctx or {},
        }

    def _call_persona(self, decision_type, persona_prompt, payload, context_name):
        raw_result = self._call_openai_safe(
            persona_prompt,
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            require_json=True,
            context_name=context_name,
            model_override=self.fast_model_name,
            temperature_override=0.05,
        )
        return self._normalize_shadow_result(raw_result, decision_type)

    def _gemini_baseline(self, decision_type, gemini_result):
        gemini_result = gemini_result or {}
        if decision_type == "gatekeeper":
            action_label = str(gemini_result.get("action_label", "UNKNOWN") or "UNKNOWN")
            allow_entry = bool(gemini_result.get("allow_entry", False))
            if allow_entry:
                return {"action": "ALLOW_ENTRY", "score": 85, "confidence": 0.85, "action_label": action_label}
            if action_label in {"전량 회피", "둘 다 아님"}:
                return {"action": "REJECT", "score": 20, "confidence": 0.75, "action_label": action_label}
            return {"action": "WAIT", "score": 55, "confidence": 0.6, "action_label": action_label}

        action = str(gemini_result.get("action", "SELL_TODAY") or "SELL_TODAY").upper()
        confidence = self._normalize_confidence(gemini_result.get("confidence", 0))
        if action not in {"HOLD_OVERNIGHT", "SELL_TODAY"}:
            action = "SELL_TODAY"
        return {
            "action": action,
            "score": 75 if action == "HOLD_OVERNIGHT" else 25,
            "confidence": confidence,
            "action_label": action,
        }

    def _resolve_weights(self, decision_type):
        if decision_type == "gatekeeper":
            return (
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_G_WEIGHT", 0.50) or 0.50),
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_A_WEIGHT", 0.20) or 0.20),
                float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_GATEKEEPER_C_WEIGHT", 0.30) or 0.30),
            )
        return (
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_G_WEIGHT", 0.45) or 0.45),
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_A_WEIGHT", 0.10) or 0.10),
            float(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_OVERNIGHT_C_WEIGHT", 0.45) or 0.45),
        )

    def _agreement_bucket(self, gemini_action, aggr_action, cons_action):
        actions = {gemini_action, aggr_action, cons_action}
        if len(actions) == 1:
            return "all_agree"
        if len(actions) == 3:
            return "all_conflict"
        if gemini_action == aggr_action and gemini_action != cons_action:
            return "gemini_vs_cons_conflict"
        if gemini_action == cons_action and gemini_action != aggr_action:
            return "aggr_vs_pair_conflict"
        if aggr_action == cons_action and gemini_action != aggr_action:
            return "gemini_vs_openai_conflict"
        return "partial_conflict"

    def _fuse_results(self, decision_type, gemini, aggressive, conservative):
        w_gemini, w_aggr, w_cons = self._resolve_weights(decision_type)
        hard_flags = sorted(flag for flag in conservative.get("risk_flags", []) if flag in self.HARD_RISK_FLAGS)
        cons_veto = bool(conservative.get("veto")) and bool(hard_flags)
        fused_score = (
            float(gemini.get("score", 0)) * w_gemini
            + float(aggressive.get("score", 0)) * w_aggr
            + float(conservative.get("score", 0)) * w_cons
        )
        if cons_veto:
            fused_score = max(0.0, fused_score - 15.0)

        if decision_type == "gatekeeper":
            if cons_veto:
                fused_action = "WAIT"
            elif fused_score >= 70.0:
                fused_action = "ALLOW_ENTRY"
            elif fused_score <= 35.0:
                fused_action = "REJECT"
            else:
                fused_action = "WAIT"
        else:
            if cons_veto:
                fused_action = "SELL_TODAY"
            elif fused_score >= 60.0:
                fused_action = "HOLD_OVERNIGHT"
            else:
                fused_action = "SELL_TODAY"

        agreement_bucket = self._agreement_bucket(
            gemini.get("action", ""),
            aggressive.get("action", ""),
            conservative.get("action", ""),
        )
        if cons_veto and fused_action != gemini.get("action"):
            winner = "conservative_veto"
        elif fused_action == aggressive.get("action") and fused_action != gemini.get("action"):
            winner = "aggressive_promote"
        elif fused_action == gemini.get("action"):
            winner = "gemini_hold"
        else:
            winner = "blended"

        return {
            "fused_action": fused_action,
            "fused_score": int(round(max(0.0, min(100.0, fused_score)))),
            "agreement_bucket": agreement_bucket,
            "winner": winner,
            "cons_veto": cons_veto,
            "hard_flags": hard_flags,
        }

    def _is_enabled_for(self, decision_type):
        if not self.shadow_enabled or not self.shadow_mode:
            return False
        if decision_type == "gatekeeper":
            return bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER", True))
        if decision_type == "overnight":
            return bool(getattr(TRADING_RULES, "OPENAI_DUAL_PERSONA_APPLY_OVERNIGHT", True))
        return False

    def _evaluate_shadow(self, decision_type, stock_name, stock_code, strategy, realtime_ctx, gemini_result):
        started_at = time.perf_counter()
        try:
            payload = self._build_shadow_payload(
                decision_type=decision_type,
                stock_name=stock_name,
                stock_code=stock_code,
                strategy=strategy,
                realtime_ctx=realtime_ctx,
            )
            aggressive = self._call_persona(
                decision_type,
                DUAL_PERSONA_AGGRESSIVE_PROMPT,
                payload,
                context_name=f"DUAL-{decision_type.upper()}-A:{stock_name}",
            )
            conservative = self._call_persona(
                decision_type,
                DUAL_PERSONA_CONSERVATIVE_PROMPT,
                payload,
                context_name=f"DUAL-{decision_type.upper()}-C:{stock_name}",
            )
            gemini = self._gemini_baseline(decision_type, gemini_result)
            fused = self._fuse_results(decision_type, gemini, aggressive, conservative)
            return {
                "mode": "shadow",
                "decision_type": decision_type,
                "strategy": str(strategy or "").upper(),
                "gemini_action": gemini.get("action"),
                "gemini_score": gemini.get("score"),
                "gemini_action_label": gemini.get("action_label", ""),
                "aggr_action": aggressive.get("action"),
                "aggr_score": aggressive.get("score"),
                "cons_action": conservative.get("action"),
                "cons_score": conservative.get("score"),
                "cons_veto": fused.get("cons_veto", False),
                "fused_action": fused.get("fused_action"),
                "fused_score": fused.get("fused_score"),
                "winner": fused.get("winner"),
                "agreement_bucket": fused.get("agreement_bucket"),
                "hard_flags": fused.get("hard_flags", []),
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }
        except Exception as e:
            return {
                "mode": "shadow",
                "decision_type": decision_type,
                "strategy": str(strategy or "").upper(),
                "error": str(e),
                "shadow_extra_ms": int((time.perf_counter() - started_at) * 1000),
            }

    def _submit_shadow(self, decision_type, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        if not self._is_enabled_for(decision_type):
            return None
        future = self.shadow_executor.submit(
            self._evaluate_shadow,
            decision_type,
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
        )
        if callback is not None:
            def _emit_result(done_future):
                try:
                    callback(done_future.result())
                except Exception as exc:
                    log_error(f"🚨 [OpenAI 듀얼 페르소나 callback] {decision_type}:{stock_name} 실패: {exc}")
            future.add_done_callback(_emit_result)
        return future

    def submit_gatekeeper_shadow(self, *, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        return self._submit_shadow(
            "gatekeeper",
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
            callback=callback,
        )

    def submit_overnight_shadow(self, *, stock_name, stock_code, strategy, realtime_ctx, gemini_result, callback=None):
        return self._submit_shadow(
            "overnight",
            stock_name,
            stock_code,
            strategy,
            realtime_ctx,
            gemini_result,
            callback=callback,
        )
