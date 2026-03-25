# 실시간 종목분석 고도화 통합본 (기존 코드베이스 참조형 / 바이브코딩용)

## 0) 목표

이 문서는 **현재 코드베이스(`ai_engine.py`, `kiwoom_websocket.py`, `kiwoom_utils.py`)를 기준으로**  
실시간 종목 정밀 분석을 아래 방향으로 업그레이드하기 위한 **바로 붙여넣기 가능한 통합 가이드**다.

핵심 목표는 4가지다.

1. **텔레그램 입력은 종목코드만 유지**
2. **전략 분기는 서버 내부에서 `AUTO -> SCALP / SWING / DUAL`로 결정**
3. **`ai_engine.py`는 LLM 프롬프트/리포트 생성만 담당**
4. **실시간/REST 데이터 수집은 `kiwoom_websocket.py`, `kiwoom_utils.py`에서 최대한 풍부하게 수집**

---

## 1) 현재 코드베이스 현실 진단

### `ai_engine.py`
현재 구조는 아래와 같다.

- `analyze_target(...)`는 이미 `strategy`에 따라 `SCALPING_SYSTEM_PROMPT` / `SWING_SYSTEM_PROMPT`를 분기한다.
- 그러나 `generate_realtime_report(stock_name, stock_code, input_data_text)`는 **단일 `REALTIME_ANALYSIS_PROMPT`**만 사용한다.
- 즉, 자동매매 경로는 전략 분기가 있는데, **텔레그램 수동 정밀 분석 경로는 전략 분기가 없다.**

이게 현재 리포트가 평균적으로 얕아지는 가장 큰 이유다.

### `kiwoom_websocket.py`
현재 실시간 파서는 이미 꽤 잘 짜여 있다.

- `0B` 계열에서 현재가/시가/거래량/등락률/체결강도/총잔량을 저장
- `0D` 에서 1~5호가를 파싱
- `0w` 에서 프로그램 순매수량/증감/금액/금액증감을 파싱

다만 **실제 등록 패킷 `_send_reg()`는 `0B`, `0D`만 등록**하고 있다.  
즉, 코드상 `0w` 파서가 있어도 **실시간 프로그램 데이터가 실제로 안 들어올 가능성**이 높다.

### `kiwoom_utils.py`
현재는 이미 `build_realtime_analysis_context(token, stock_code, position_status="NONE", ws_data=None)`가 존재한다.

좋은 점:
- `ws_data`와 REST 데이터를 합쳐 표준 `ctx`를 만들어 주려는 구조
- `ka10100`, `ka90008`, `ka10046`, `ka10081`, `ka10080` 등을 이미 사용 중

아쉬운 점:
- `prog_delta_qty`, `prog_delta_amt`는 아직 실제 delta가 아니라 net 값을 그대로 복사
- `foreign_net`, `inst_net`은 TODO
- `score`, `conclusion`은 placeholder
- `buy_ratio`, `tape_bias`, `ask_absorption_status`, `daily_setup_desc` 등은 비어 있음
- 즉, **입력 필드 뼈대는 좋지만 실제 채움 정도가 아직 약하다**

---

## 2) 최종 구조

```text
Telegram
  └─ 종목코드 입력

bot / service layer
  └─ token 확보
  └─ ws_data 확보 (KiwoomWSManager.realtime_data[code])
  └─ realtime_ctx = build_realtime_analysis_context(token, code, position_status, ws_data)

ai_engine.py
  ├─ selected_mode = _infer_realtime_mode(realtime_ctx)
  ├─ packet_text = build_realtime_quant_packet(realtime_ctx, selected_mode)
  └─ prompt = SCALP / SWING / DUAL 프롬프트 선택 후 LLM 호출
```

### 역할 분리
- `kiwoom_websocket.py`
  - 실시간 틱/호가/프로그램/주문체결 수집
- `kiwoom_utils.py`
  - REST API 수집 + 파생값 계산 + `realtime_ctx` 생성
- `ai_engine.py`
  - 전략 자동 분기 + 프롬프트 선택 + 마크다운 리포트 생성

---

## 3) 반드시 지킬 구현 원칙

1. **전략 분기는 텔레그램 UI에서 하지 않는다.**
2. **`ai_engine.py`에서 데이터 수집하지 않는다.**
3. **주입 데이터는 “있으면 좋음”이 아니라 “최대한 전부 수집”이 원칙이다.**
4. **WebSocket 데이터는 `kiwoom_websocket.py`에서 파싱한다.**
5. **REST 데이터는 `kiwoom_utils.py`에서 함수화한다.**
6. **REST 함수명은 `기능명_APIID` 형식**
7. **REST 함수는 첫 번째 인자로 `token`을 필수로 받는다**
8. **REST 함수 내부 `url`은 반드시 `get_api_url("/...")`로 생성**
9. **`ai_engine.py`는 오직 `realtime_ctx` 또는 `packet_text`만 받아 분석한다**

---

## 4) `ai_engine.py` 수정안

## 4-1. 프롬프트를 3개로 분리

### `REALTIME_ANALYSIS_PROMPT_SCALP`

```python
REALTIME_ANALYSIS_PROMPT_SCALP = """
너는 상위 1% 초단타 프랍 트레이더다.
목표는 1~2%의 짧은 파동만 빠르게 먹고, 모멘텀이 식는 즉시 손절하는 것이다.

[분석 원칙]
1. 현재값보다 변화율을 우선하라. 특히 체결강도, 매수세, 프로그램 순매수의 1~5분 변화가 핵심이다.
2. 호가가 매도 우위여도 실제 체결이 매도벽을 먹고 올라가면 강한 돌파다.
3. VWAP 아래, 고가 돌파 실패, 스프레드 확대, 체결 둔화는 추격 금지 신호다.
4. 기계목표가보다 중요한 것은 "지금 진입하면 즉시 반응이 나오는 자리인가"다.
5. 이미 보유 중이면 신규 진입과 다르게 판단하라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

📍 **[한 줄 결론]**
- 지금 이 종목의 스캘핑 타점 상태를 한 문장으로 평가

🧠 **[핵심 해석]**
- 체결/호가/VWAP/고가돌파 여부를 연결해서 왜 그런지 설명

⚠️ **[리스크 포인트]**
- 실패 시 가장 먼저 무너질 조건 1~2개

🎯 **[실전 행동 지침]**
- 반드시 아래 다섯 가지 중 하나로 시작:
  [즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

길이 350~520자. 애매한 표현 금지.
"""
```

### `REALTIME_ANALYSIS_PROMPT_SWING`

```python
REALTIME_ANALYSIS_PROMPT_SWING = """
너는 상위 1% 스윙 트레이더다.
목표는 단기 노이즈를 무시하고, 수급과 일봉 구조가 받쳐주는 자리에서 며칠간 추세를 먹는 것이다.

[분석 원칙]
1. 순간 체결보다 일봉 구조와 수급 지속성을 우선하라.
2. 현재가가 5일선/20일선/전일고점/VWAP 대비 어디에 있는지 해석하라.
3. 프로그램, 외인, 기관의 개입이 지속 가능한지 판단하라.
4. 기계목표가가 현실적인지, 손절가 대비 손익비가 합리적인지 검증하라.
5. 이미 많이 오른 자리라면 좋은 종목이어도 추격 금지를 명확히 말하라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

📍 **[한 줄 결론]**
- 지금 이 종목의 스윙 관점 매력도를 한 문장으로 평가

🧠 **[핵심 해석]**
- 일봉 구조 + 수급 + 현재 위치를 연결해서 설명

⚠️ **[리스크 포인트]**
- 스윙 관점에서 깨지면 안 되는 조건 1~2개

🎯 **[실전 행동 지침]**
- 반드시 아래 다섯 가지 중 하나로 시작:
  [즉시 매수] [눌림 대기] [보유 지속] [일부 익절] [전량 회피]

길이 350~520자. 애매한 표현 금지.
"""
```

### `REALTIME_ANALYSIS_PROMPT_DUAL`

```python
REALTIME_ANALYSIS_PROMPT_DUAL = """
너는 초단타와 스윙을 모두 수행하는 베테랑 프랍 트레이더다.
입력 종목을 스캘핑 관점과 스윙 관점에서 각각 평가하되, 최종적으로 어느 관점이 더 유효한지 결정하라.

[출력 형식]
텔레그램 마크다운으로 아래 형식만 사용하라.

⚡ **[스캘핑 판단]**
- 한 줄 결론 + 핵심 근거

📈 **[스윙 판단]**
- 한 줄 결론 + 핵심 근거

🎯 **[최종 채택 관점]**
- 반드시 하나를 선택:
  [스캘핑 우선] [스윙 우선] [둘 다 아님]

🧭 **[실전 행동 지침]**
- 지금 당장 어떻게 대응할지 한 줄로 명확히 지시

길이 420~650자.
"""
```

---

## 4-2. `AUTO` 전략 분기 함수 추가

```python
from datetime import datetime

def _infer_realtime_mode(
    self,
    *,
    strat_label: str = "",
    position_status: str = "NONE",
    fluctuation: float = 0.0,
    vol_ratio: float = 0.0,
    v_pw_now: float = 0.0,
    v_pw_3m: float = 0.0,
    prog_delta_qty: int = 0,
    curr_price: int = 0,
    vwap_price: int = 0,
    high_breakout_status: str = "",
    daily_setup_desc: str = "",
    now_hhmm: str | None = None,
):
    if strat_label in {"KOSPI_ML", "KOSDAQ_ML", "SWING", "MIDTERM", "POSITION"}:
        return "SWING"

    if position_status == "HOLDING":
        return "SWING"

    if not now_hhmm:
        now_hhmm = datetime.now().strftime("%H%M")

    scalp_score = 0
    swing_score = 0

    if "0900" <= now_hhmm <= "1030":
        scalp_score += 2
    elif "1300" <= now_hhmm <= "1500":
        swing_score += 1

    if abs(fluctuation) >= 3.0:
        scalp_score += 1

    if vol_ratio >= 150:
        scalp_score += 2
    elif 70 <= vol_ratio <= 130:
        swing_score += 1

    if v_pw_now >= 120 and (v_pw_now - v_pw_3m) >= 15:
        scalp_score += 2

    if prog_delta_qty > 0:
        scalp_score += 1
        swing_score += 1

    if curr_price > 0 and vwap_price > 0 and curr_price >= vwap_price:
        scalp_score += 1

    if "돌파" in high_breakout_status:
        scalp_score += 1

    if any(k in daily_setup_desc for k in ["눌림", "정배열", "전고점", "박스상단", "추세전환"]):
        swing_score += 2

    if any(k in daily_setup_desc for k in ["급등후", "이격", "과열", "장대음봉"]):
        swing_score -= 1

    if abs(scalp_score - swing_score) <= 1:
        return "DUAL"

    return "SCALP" if scalp_score > swing_score else "SWING"
```

---

## 4-3. 전술 패킷 빌더 추가

```python
def build_realtime_quant_packet(self, ctx: dict, trade_mode: str) -> str:
    orderbook_imbalance = ctx.get("orderbook_imbalance", 0.0)
    smart_money_net = ctx.get("smart_money_net", 0)

    common_block = (
        f"[기본]\n"
        f"- 종목명: {ctx.get('stock_name', '')}\n"
        f"- 종목코드: {ctx.get('stock_code', '')}\n"
        f"- 매매모드: {trade_mode}\n"
        f"- 감시전략: {ctx.get('strat_label', 'AUTO')}\n"
        f"- 보유상태: {ctx.get('position_status', 'NONE')}\n"
        f"- 평균단가: {ctx.get('avg_price', 0):,}원\n"
        f"- 현재손익률: {ctx.get('pnl_pct', 0.0):+.2f}%\n"
        f"- 현재가격: {ctx.get('curr_price', 0):,}원 (전일비 {ctx.get('fluctuation', 0.0):+.2f}%)\n"
        f"- 기계목표가: {ctx.get('target_price', 0):,}원 (사유: {ctx.get('target_reason', '')})\n"
        f"- 손절가: {ctx.get('stop_price', 0):,}원 / 손절률 {ctx.get('stop_pct', 0.0)}%\n"
        f"- 익절가: {ctx.get('take_profit_price', 0):,}원 / 익절률 {ctx.get('trailing_pct', 0.0)}%\n"
        f"- 퀀트 점수 분해: 추세 {ctx.get('trend_score', 0.0):.1f} / 수급 {ctx.get('flow_score', 0.0):.1f} / "
        f"호가 {ctx.get('orderbook_score', 0.0):.1f} / 타점 {ctx.get('timing_score', 0.0):.1f}\n"
        f"- 퀀트 종합점수: {ctx.get('score', 0.0):.1f}\n"
        f"- 퀀트 엔진 결론: {ctx.get('conclusion', '')}\n"
        f"\n"
        f"[수급/체결]\n"
        f"- 누적거래량: {ctx.get('today_vol', 0):,}주 (20일 평균대비 {ctx.get('vol_ratio', 0.0):.1f}%)\n"
        f"- 누적거래대금: {ctx.get('today_turnover', 0):,}원\n"
        f"- 체결강도 현재/1분전/3분전/5분전: "
        f"{ctx.get('v_pw_now', 0.0):.1f} / {ctx.get('v_pw_1m', 0.0):.1f} / "
        f"{ctx.get('v_pw_3m', 0.0):.1f} / {ctx.get('v_pw_5m', 0.0):.1f}\n"
        f"- 매수세 현재/1분/3분: {ctx.get('buy_ratio_now', 0.0):.1f}% / "
        f"{ctx.get('buy_ratio_1m', 0.0):.1f}% / {ctx.get('buy_ratio_3m', 0.0):.1f}%\n"
        f"- 프로그램 순매수 현재/증감: {ctx.get('prog_net_qty', 0):,}주 / {ctx.get('prog_delta_qty', 0):+,}주\n"
        f"- 프로그램 순매수 금액 현재/증감: {ctx.get('prog_net_amt', 0):,} / {ctx.get('prog_delta_amt', 0):+,}\n"
        f"- 외인/기관 당일 순매수: 외인 {ctx.get('foreign_net', 0):+,}주 / 기관 {ctx.get('inst_net', 0):+,}주\n"
        f"- 외인+기관 합산: {smart_money_net:+,}주\n"
        f"\n"
        f"[호가/구조]\n"
        f"- 시가/고가/저가/전일종가: {ctx.get('open_price', 0):,} / {ctx.get('high_price', 0):,} / "
        f"{ctx.get('low_price', 0):,} / {ctx.get('prev_close', 0):,}\n"
        f"- VWAP: {ctx.get('vwap_price', 0):,}원 ({ctx.get('vwap_status', '')})\n"
        f"- 시가 위치: {ctx.get('open_position_desc', '')}\n"
        f"- 고가 돌파 여부: {ctx.get('high_breakout_status', '')}\n"
        f"- 직전 박스 상단/하단: {ctx.get('box_high', 0):,} / {ctx.get('box_low', 0):,}\n"
        f"- 고가 대비 눌림률: {ctx.get('drawdown_from_high_pct', 0.0):.2f}%\n"
        f"- 최우선 매도/매수호가: {ctx.get('best_ask', 0):,} / {ctx.get('best_bid', 0):,}\n"
        f"- 총매도/총매수잔량: {ctx.get('ask_tot', 0):,} / {ctx.get('bid_tot', 0):,}\n"
        f"- 호가 불균형비: {orderbook_imbalance:.2f}\n"
        f"- 5호가 누적 잔량: 매도 {ctx.get('ask_top5_qty', 0):,} / 매수 {ctx.get('bid_top5_qty', 0):,}\n"
        f"- 스프레드: {ctx.get('spread_tick', 0)}틱\n"
        f"- 테이프 편향: {ctx.get('tape_bias', '')}\n"
        f"- 매도벽 소화 상태: {ctx.get('ask_absorption_status', '')}\n"
    )

    scalp_block = (
        f"\n[스캘핑 관점 핵심]\n"
        f"- 체결강도 가속도(현재-3분): {ctx.get('v_pw_now', 0.0) - ctx.get('v_pw_3m', 0.0):+.1f}\n"
        f"- 즉시성 평가 포인트: VWAP / 고가 돌파 / 스프레드 / 테이프 편향 / 프로그램 가속\n"
    )

    swing_block = (
        f"\n[스윙 관점 핵심]\n"
        f"- 일봉 구조: {ctx.get('daily_setup_desc', '')}\n"
        f"- 5/20/60일선: {ctx.get('ma5', 0):,} / {ctx.get('ma20', 0):,} / {ctx.get('ma60', 0):,}\n"
        f"- 5/20/60일선 상태: {ctx.get('ma5_status', '')}, {ctx.get('ma20_status', '')}, {ctx.get('ma60_status', '')}\n"
        f"- 전일 고점/저점: {ctx.get('prev_high', 0):,} / {ctx.get('prev_low', 0):,}\n"
        f"- 최근 20일 신고가 근접도: {ctx.get('near_20d_high_pct', 0.0):.1f}%\n"
    )

    if trade_mode == "SCALP":
        return common_block + scalp_block
    if trade_mode == "SWING":
        return common_block + swing_block
    return common_block + scalp_block + swing_block
```

---

## 4-4. `generate_realtime_report()`를 갈아끼우기

> 핵심: 텔레그램은 계속 종목코드만 받고, **분기와 포맷팅은 내부에서 처리**한다.

```python
def generate_realtime_report(self, stock_name, stock_code, realtime_ctx: dict, analysis_mode: str = "AUTO"):
    """
    텔레그램 수동 종목 정밀 분석
    - analysis_mode: AUTO / SCALP / SWING / DUAL
    - realtime_ctx는 kiwoom_utils.build_realtime_analysis_context()가 만든 dict
    """
    with self.lock:
        selected_mode = analysis_mode

        if selected_mode == "AUTO":
            selected_mode = self._infer_realtime_mode(
                strat_label=realtime_ctx.get("strat_label", ""),
                position_status=realtime_ctx.get("position_status", "NONE"),
                fluctuation=realtime_ctx.get("fluctuation", 0.0),
                vol_ratio=realtime_ctx.get("vol_ratio", 0.0),
                v_pw_now=realtime_ctx.get("v_pw_now", 0.0),
                v_pw_3m=realtime_ctx.get("v_pw_3m", 0.0),
                prog_delta_qty=realtime_ctx.get("prog_delta_qty", 0),
                curr_price=realtime_ctx.get("curr_price", 0),
                vwap_price=realtime_ctx.get("vwap_price", 0),
                high_breakout_status=realtime_ctx.get("high_breakout_status", ""),
                daily_setup_desc=realtime_ctx.get("daily_setup_desc", ""),
            )

        packet_text = self.build_realtime_quant_packet(realtime_ctx, selected_mode)

        if selected_mode == "SCALP":
            prompt = REALTIME_ANALYSIS_PROMPT_SCALP
        elif selected_mode == "SWING":
            prompt = REALTIME_ANALYSIS_PROMPT_SWING
        else:
            prompt = REALTIME_ANALYSIS_PROMPT_DUAL

        user_input = (
            f"🚨 [요청 종목]\n"
            f"종목명: {stock_name}\n"
            f"종목코드: {stock_code}\n"
            f"선택된 분석 모드: {selected_mode}\n\n"
            f"📊 [실시간 전술 패킷]\n{packet_text}"
        )

        try:
            return self._call_gemini_safe(
                prompt,
                user_input,
                require_json=False,
                context_name=f"실시간 분석({selected_mode})",
                model_override="gemini-pro-latest"
            )
        except Exception as e:
            log_error(f"🚨 [실시간 분석:{selected_mode}] AI 에러: {e}")
            return f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
```

---

## 5) `kiwoom_websocket.py` 수정안

## 5-1. 결론부터: `_send_reg()`에 반드시 `0w`를 추가

현재는 `0B`, `0D`만 등록하고 있다.  
그러면 아래처럼 고친다.

```python
async def _send_reg(self, codes):
    try:
        for _ in range(50):
            if self.websocket:
                break
            await asyncio.sleep(0.1)

        if self.websocket:
            print(f"📝 [WS] 종목 등록(REG) 전송 시도: {codes}")
            reg_packet = {
                'trnm': 'REG',
                'grp_no': '1',
                'refresh': '1',
                'data': [
                    {'item': codes, 'type': ['0B']},  # 주식체결
                    {'item': codes, 'type': ['0D']},  # 주식호가잔량
                    {'item': codes, 'type': ['0w']},  # 종목프로그램매매
                ]
            }
            await self.websocket.send(json.dumps(reg_packet))
            self.subscribed_codes.update(codes)
            print(f"📡 [WS] 종목 등록 완료 및 데이터 수신 시작: {codes}")
        else:
            print(f"⚠️ [WS] 연결된 웹소켓이 없어 전송 실패: {codes}")

    except Exception as e:
        log_error(f"🚨 [WS] _send_reg 에러 발생: {e}")
        print(f"🚨 [WS] _send_reg 내부 치명적 에러 발생: {e}")
```

---

## 5-2. 현재 구조를 살리면서 `realtime_data`를 확장

```python
if item_code not in self.realtime_data:
    self.realtime_data[item_code] = {
        'curr': 0,
        'open': 0,
        'high': 0,
        'low': 0,
        'volume': 0,
        'fluctuation': 0.0,
        'v_pw': 0.0,
        'ask_tot': 0,
        'bid_tot': 0,
        'time': '',
        'orderbook': {'asks': [], 'bids': []},
        'prog_net_qty': 0,
        'prog_delta_qty': 0,
        'prog_net_amt': 0,
        'prog_delta_amt': 0,

        # 추가 파생용 히스토리
        'v_pw_history': [],
        'price_history': [],
        'volume_history': [],
        'prog_net_qty_history': [],
        'ask_bid_ratio_history': [],
    }
```

---

## 5-3. 실시간 히스토리도 같이 쌓기

```python
from collections import deque

# __init__ 쪽에서 권장
self.max_hist_len = 20

# 초기화 시
'v_pw_history': deque(maxlen=self.max_hist_len),
'price_history': deque(maxlen=self.max_hist_len),
'volume_history': deque(maxlen=self.max_hist_len),
'prog_net_qty_history': deque(maxlen=self.max_hist_len),
'ask_bid_ratio_history': deque(maxlen=self.max_hist_len),

# 파싱 후
target['v_pw_history'].append(target['v_pw'])
target['price_history'].append(target['curr'])
target['volume_history'].append(target['volume'])
target['prog_net_qty_history'].append(target['prog_net_qty'])

if target['bid_tot'] > 0:
    target['ask_bid_ratio_history'].append(target['ask_tot'] / target['bid_tot'])
```

---

## 5-4. `real_type`별 책임 명시

### WebSocket에서 가져와야 하는 데이터
아래는 **무조건 `kiwoom_websocket.py`에서 수집**한다.

- 현재가 / 시가 / 거래량 / 등락률 / 체결강도
- 총매도잔량 / 총매수잔량
- 1~5호가 상세
- 프로그램 순매수량 / 순매수량 증감 / 순매수금액 / 순매수금액 증감
- 주문체결 통보
- 조건검색 실시간 편입/이탈

### WebSocket 파싱 규칙 예시

```python
# '0w' 프로그램 매매 데이터 파싱
if real_type == '0w':
    if '210' in values:
        target['prog_net_qty'] = safe_int(values['210'])
    if '211' in values:
        target['prog_delta_qty'] = safe_int(values['211'])
    if '212' in values:
        target['prog_net_amt'] = safe_int(values['212'])
    if '213' in values:
        target['prog_delta_amt'] = safe_int(values['213'])
```

### 현재 문서 기준 `real_type` 사용안
- `00`: 주문/체결 통보
- `02`: 조건검색 실시간 편입/이탈
- `0B`: 주식체결
- `0D`: 주식호가잔량
- `0w`: 종목프로그램매매

---

## 6) `kiwoom_utils.py` 수정안

## 6-1. REST 함수 작성 규칙

### 함수명 규칙
- `기능을_설명하는_이름_APIID`
- 예: `check_execution_strength_ka10046`
- 예: `get_minute_candles_ka10080`
- 예: `get_orderbook_snapshot_ka10004`

### 공통 규칙
- 첫 번째 인자: `token`
- `url = get_api_url("/...")`
- `fetch_kiwoom_api_continuous(...)` 호출
- API 별 응답 바디를 안전하게 파싱
- 숫자는 부호/콤마 제거 후 파싱
- 반환값은 dict 또는 list[dict]로 표준화

---

## 6-2. 추가 권장 REST 함수

### 1) 주식호가요청 `ka10004`
> WebSocket이 이미 호가를 주지만, REST fallback 또는 장중 보정용으로 매우 유용하다.

```python
def get_orderbook_snapshot_ka10004(token, code):
    """[ka10004] 주식호가요청 - 호가창 스냅샷 반환"""
    url = get_api_url("/api/dostk/mrkcond")
    payload = {"stk_cd": str(code)}

    results = fetch_kiwoom_api_continuous(
        url=url,
        token=token,
        api_id="ka10004",
        payload=payload,
        use_continuous=False
    )

    res = {
        "best_ask": 0,
        "best_bid": 0,
        "ask_tot": 0,
        "bid_tot": 0,
        "ask_top5_qty": 0,
        "bid_top5_qty": 0,
        "orderbook_imbalance": 0.0,
    }

    if not results:
        return res

    data = results[0]

    def to_i(v):
        if not v:
            return 0
        try:
            clean_v = str(v).replace(",", "").replace("+", "").replace("-", "").strip()
            return int(float(clean_v))
        except (ValueError, TypeError):
            return 0

    # 아래 키들은 실제 응답명세에 맞게 엑셀 시트 기준으로 매핑 교체
    best_ask = to_i(data.get("sel_pric_1"))
    best_bid = to_i(data.get("buy_pric_1"))
    ask_tot = to_i(data.get("tot_sel_req"))
    bid_tot = to_i(data.get("tot_buy_req"))

    res["best_ask"] = best_ask
    res["best_bid"] = best_bid
    res["ask_tot"] = ask_tot
    res["bid_tot"] = bid_tot

    ask_top5 = 0
    bid_top5 = 0
    for i in range(1, 6):
        ask_top5 += to_i(data.get(f"sel_req_{i}"))
        bid_top5 += to_i(data.get(f"buy_req_{i}"))

    res["ask_top5_qty"] = ask_top5
    res["bid_top5_qty"] = bid_top5

    if bid_tot > 0:
        res["orderbook_imbalance"] = ask_tot / bid_tot

    return res
```

---

### 2) 투자자 수급 요약 `ka10059`
현재 `get_investor_daily_ka10059_df()`는 존재한다.  
실시간 정밀 분석에서는 **DataFrame을 그대로 넘기지 말고 요약 dict**를 주는 게 좋다.

```python
def get_investor_flow_summary_ka10059(token, code, base_dt=None):
    """[ka10059] 외인/기관/세부 기관 수급 요약"""
    df = get_investor_daily_ka10059_df(token, code, base_dt=base_dt)

    res = {
        "foreign_net": 0,
        "inst_net": 0,
        "retail_net": 0,
        "fin_net": 0,
        "trust_net": 0,
        "pension_net": 0,
        "private_net": 0,
        "smart_money_net": 0,
    }

    if df.empty:
        return res

    latest = df.iloc[-1]
    res["foreign_net"] = int(latest.get("Foreign_Net", 0))
    res["inst_net"] = int(latest.get("Inst_Net", 0))
    res["retail_net"] = int(latest.get("Retail_Net", 0))
    res["fin_net"] = int(latest.get("Fin_Net", 0))
    res["trust_net"] = int(latest.get("Trust_Net", 0))
    res["pension_net"] = int(latest.get("Pension_Net", 0))
    res["private_net"] = int(latest.get("Private_Net", 0))
    res["smart_money_net"] = res["foreign_net"] + res["inst_net"]

    return res
```

---

### 3) 최근 체결정보 요약 `ka10003`
현재 `get_tick_history_ka10003()`는 이미 존재한다.  
여기서 바로 **테이프 편향 / 매수세 비율**을 계산하는 보조 함수를 붙이면 좋다.

```python
def summarize_ticks_for_realtime_ka10003(token, code, limit=20):
    """[ka10003] 최근 체결정보를 매수/매도 편향 요약으로 변환"""
    ticks = get_tick_history_ka10003(token, code, limit=limit)

    res = {
        "trade_qty_signed_now": 0,
        "buy_exec_qty": 0,
        "sell_exec_qty": 0,
        "buy_ratio_now": 0.0,
        "buy_ratio_1m": 0.0,
        "buy_ratio_3m": 0.0,
        "tape_bias": "중립",
    }

    if not ticks:
        return res

    buy_qty = sum(t["volume"] for t in ticks if t["dir"] == "BUY")
    sell_qty = sum(t["volume"] for t in ticks if t["dir"] == "SELL")
    total = buy_qty + sell_qty

    res["buy_exec_qty"] = buy_qty
    res["sell_exec_qty"] = sell_qty
    if total > 0:
        res["buy_ratio_now"] = (buy_qty / total) * 100

    if buy_qty > sell_qty:
        res["tape_bias"] = "매수 우세"
        res["trade_qty_signed_now"] = buy_qty - sell_qty
    elif sell_qty > buy_qty:
        res["tape_bias"] = "매도 우세"
        res["trade_qty_signed_now"] = -(sell_qty - buy_qty)

    # 간단 버전: 현재와 동일값으로 세팅, 추후 1분/3분 창 분리 가능
    res["buy_ratio_1m"] = res["buy_ratio_now"]
    res["buy_ratio_3m"] = res["buy_ratio_now"]

    return res
```

---

## 6-3. `build_realtime_analysis_context()`를 실전형으로 업그레이드

> 현재 함수는 이미 뼈대가 매우 좋다.  
> 아래처럼 **WebSocket 우선 + REST 보강 + 파생값 계산** 구조로 강화하면 된다.

```python
def build_realtime_analysis_context(token, stock_code, position_status="NONE", ws_data=None):
    """
    ai_engine.py 로 넘길 표준 realtime_ctx 반환
    - token 필수
    - ws_data는 KiwoomWSManager.realtime_data[code]를 그대로 넣어도 됨
    """
    from datetime import datetime
    from src.utils.logger import log_error

    ctx = {
        "stock_name": "",
        "stock_code": stock_code,
        "position_status": position_status,
        "avg_price": 0,
        "pnl_pct": 0.0,
        "strat_label": "AUTO",

        # 현재 시세
        "curr_price": 0,
        "fluctuation": 0.0,
        "open_price": 0,
        "high_price": 0,
        "low_price": 0,
        "prev_close": 0,
        "vwap_price": 0,

        # 거래량/거래대금
        "today_vol": 0,
        "today_turnover": 0,
        "vol_ratio": 0.0,
        "turnover_ratio": 0.0,

        # 체결/체결강도
        "v_pw_now": 0.0,
        "v_pw_1m": 0.0,
        "v_pw_3m": 0.0,
        "v_pw_5m": 0.0,
        "trade_qty_signed_now": 0,
        "buy_exec_qty": 0,
        "sell_exec_qty": 0,
        "buy_ratio_now": 0.0,
        "buy_ratio_1m": 0.0,
        "buy_ratio_3m": 0.0,

        # 호가
        "best_ask": 0,
        "best_bid": 0,
        "ask_tot": 0,
        "bid_tot": 0,
        "spread_tick": 0,
        "orderbook_imbalance": 0.0,
        "ask_top5_qty": 0,
        "bid_top5_qty": 0,
        "ask_absorption_status": "",
        "tape_bias": "",

        # 프로그램/수급
        "prog_net_qty": 0,
        "prog_delta_qty": 0,
        "prog_net_amt": 0,
        "prog_delta_amt": 0,
        "foreign_net": 0,
        "inst_net": 0,
        "smart_money_net": 0,

        # 구조
        "high_breakout_status": "",
        "open_position_desc": "",
        "vwap_status": "",
        "box_high": 0,
        "box_low": 0,
        "drawdown_from_high_pct": 0.0,

        # 일봉
        "ma5": 0,
        "ma20": 0,
        "ma60": 0,
        "ma5_status": "",
        "ma20_status": "",
        "ma60_status": "",
        "prev_high": 0,
        "prev_low": 0,
        "near_20d_high_pct": 0.0,
        "daily_setup_desc": "",

        # 퀀트 엔진 점수
        "trend_score": 0.0,
        "flow_score": 0.0,
        "orderbook_score": 0.0,
        "timing_score": 0.0,
        "score": 0.0,
        "conclusion": "",
        "target_price": 0,
        "target_reason": "",
        "stop_price": 0,
        "stop_pct": 0.0,
        "take_profit_price": 0,
        "trailing_pct": 0.0,

        "session_stage": "REGULAR",
        "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 1) 종목 기본 정보
    try:
        item_info = get_item_info_ka10100(token, stock_code)
        if item_info:
            ctx["stock_name"] = item_info.get("stk_nm", "")
            ctx["prev_close"] = int(item_info.get("lastPrice", 0))
            ctx["open_price"] = int(item_info.get("openPrice", 0))
            ctx["high_price"] = int(item_info.get("highPrice", 0))
            ctx["low_price"] = int(item_info.get("lowPrice", 0))
    except Exception as e:
        log_error(f"build_realtime_analysis_context get_item_info_ka10100 error: {e}")

    # 2) WebSocket 우선 반영
    if ws_data:
        ctx["curr_price"] = ws_data.get("curr", 0)
        ctx["fluctuation"] = ws_data.get("fluctuation", 0.0)
        ctx["v_pw_now"] = ws_data.get("v_pw", 0.0)
        ctx["ask_tot"] = ws_data.get("ask_tot", 0)
        ctx["bid_tot"] = ws_data.get("bid_tot", 0)
        ctx["prog_net_qty"] = ws_data.get("prog_net_qty", 0)
        ctx["prog_delta_qty"] = ws_data.get("prog_delta_qty", 0)
        ctx["prog_net_amt"] = ws_data.get("prog_net_amt", 0)
        ctx["prog_delta_amt"] = ws_data.get("prog_delta_amt", 0)

        orderbook = ws_data.get("orderbook", {})
        asks = orderbook.get("asks", [])
        bids = orderbook.get("bids", [])

        if asks:
            ctx["best_ask"] = asks[-1]["price"]
            ctx["ask_top5_qty"] = sum(a["volume"] for a in asks[:5])

        if bids:
            ctx["best_bid"] = bids[0]["price"]
            ctx["bid_top5_qty"] = sum(b["volume"] for b in bids[:5])

        if ctx["best_ask"] > 0 and ctx["best_bid"] > 0:
            tick = get_tick_size(ctx["best_bid"])
            if tick > 0:
                ctx["spread_tick"] = max(0, (ctx["best_ask"] - ctx["best_bid"]) // tick)

        if ctx["bid_tot"] > 0:
            ctx["orderbook_imbalance"] = ctx["ask_tot"] / ctx["bid_tot"]

        ctx["today_vol"] = ws_data.get("volume", 0)

    # 3) 프로그램 수급 REST 보정
    try:
        prog = check_program_buying_ka90008(token, stock_code)
        if ctx["prog_net_qty"] == 0:
            ctx["prog_net_qty"] = prog.get("net_qty", 0)
        if ctx["prog_net_amt"] == 0:
            ctx["prog_net_amt"] = prog.get("net_amt", 0)
    except Exception as e:
        log_error(f"build_realtime_analysis_context check_program_buying_ka90008 error: {e}")

    # 4) 체결강도 REST 보정
    try:
        strength = check_execution_strength_ka10046(token, stock_code)
        ctx["v_pw_now"] = strength.get("strength", ctx["v_pw_now"])
        ctx["v_pw_1m"] = strength.get("s5", 0.0)
        ctx["v_pw_3m"] = strength.get("s20", 0.0)
        ctx["v_pw_5m"] = strength.get("s60", 0.0)
        if ctx["today_turnover"] == 0:
            ctx["today_turnover"] = strength.get("acc_amt", 0)
        if ctx["today_vol"] == 0:
            ctx["today_vol"] = strength.get("trde_qty", 0)
    except Exception as e:
        log_error(f"build_realtime_analysis_context check_execution_strength_ka10046 error: {e}")

    # 5) 틱 요약
    try:
        tape = summarize_ticks_for_realtime_ka10003(token, stock_code, limit=20)
        ctx["trade_qty_signed_now"] = tape.get("trade_qty_signed_now", 0)
        ctx["buy_exec_qty"] = tape.get("buy_exec_qty", 0)
        ctx["sell_exec_qty"] = tape.get("sell_exec_qty", 0)
        ctx["buy_ratio_now"] = tape.get("buy_ratio_now", 0.0)
        ctx["buy_ratio_1m"] = tape.get("buy_ratio_1m", 0.0)
        ctx["buy_ratio_3m"] = tape.get("buy_ratio_3m", 0.0)
        ctx["tape_bias"] = tape.get("tape_bias", "")
    except Exception as e:
        log_error(f"build_realtime_analysis_context summarize_ticks_for_realtime_ka10003 error: {e}")

    # 6) 분봉 / VWAP / 박스
    try:
        minute_candles = get_minute_candles_ka10080(token, stock_code, limit=30)
        if minute_candles:
            total_volume = sum(c.get("거래량", 0) for c in minute_candles)
            total_turnover = sum(c.get("현재가", 0) * c.get("거래량", 0) for c in minute_candles)

            if total_volume > 0:
                ctx["vwap_price"] = int(total_turnover / total_volume)
                if ctx["today_turnover"] == 0:
                    ctx["today_turnover"] = total_turnover
                if ctx["today_vol"] == 0:
                    ctx["today_vol"] = total_volume

            highs = [c.get("고가", 0) for c in minute_candles[-5:]]
            lows = [c.get("저가", 0) for c in minute_candles[-5:]]
            if highs:
                ctx["box_high"] = max(highs)
            if lows:
                ctx["box_low"] = min(lows)
    except Exception as e:
        log_error(f"build_realtime_analysis_context get_minute_candles_ka10080 error: {e}")

    # 7) 일봉
    try:
        daily_df = get_daily_ohlcv_ka10081_df(token, stock_code)
        if not daily_df.empty:
            closes = daily_df["Close"].tail(60).values

            if len(closes) >= 5:
                ctx["ma5"] = int(closes[-5:].mean())
            if len(closes) >= 20:
                ctx["ma20"] = int(closes[-20:].mean())
            if len(closes) >= 60:
                ctx["ma60"] = int(closes[-60:].mean())

            prev_day = daily_df.iloc[-1] if len(daily_df) >= 1 else None
            if prev_day is not None:
                ctx["prev_high"] = int(prev_day["High"])
                ctx["prev_low"] = int(prev_day["Low"])

            if len(closes) >= 20:
                highest_20 = closes[-20:].max()
                if highest_20 > 0 and ctx["curr_price"] > 0:
                    ctx["near_20d_high_pct"] = ((ctx["curr_price"] - highest_20) / highest_20) * 100

            avg_volume_20 = daily_df["Volume"].tail(20).mean() if len(daily_df) >= 20 else 0
            if avg_volume_20 > 0 and ctx["today_vol"] > 0:
                ctx["vol_ratio"] = (ctx["today_vol"] / avg_volume_20) * 100
    except Exception as e:
        log_error(f"build_realtime_analysis_context get_daily_ohlcv_ka10081_df error: {e}")

    # 8) 외인/기관 수급
    try:
        flow = get_investor_flow_summary_ka10059(token, stock_code)
        ctx["foreign_net"] = flow.get("foreign_net", 0)
        ctx["inst_net"] = flow.get("inst_net", 0)
        ctx["smart_money_net"] = flow.get("smart_money_net", 0)
    except Exception as e:
        log_error(f"build_realtime_analysis_context get_investor_flow_summary_ka10059 error: {e}")

    # 9) 파생값
    if ctx["curr_price"] > 0 and ctx["high_price"] > 0:
        ctx["high_breakout_status"] = "돌파" if ctx["curr_price"] >= ctx["high_price"] else "미돌파"
        ctx["drawdown_from_high_pct"] = ((ctx["curr_price"] - ctx["high_price"]) / ctx["high_price"]) * 100

    if ctx["curr_price"] > 0 and ctx["vwap_price"] > 0:
        ctx["vwap_status"] = "VWAP 상회" if ctx["curr_price"] >= ctx["vwap_price"] else "VWAP 하회"

    if ctx["curr_price"] > 0 and ctx["open_price"] > 0:
        if ctx["curr_price"] > ctx["open_price"]:
            ctx["open_position_desc"] = "시가 위"
        elif ctx["curr_price"] < ctx["open_price"]:
            ctx["open_position_desc"] = "시가 아래"
        else:
            ctx["open_position_desc"] = "시가 부근"

    if ctx["ma5"] > 0:
        ctx["ma5_status"] = "MA5 상회" if ctx["curr_price"] >= ctx["ma5"] else "MA5 하회"
    if ctx["ma20"] > 0:
        ctx["ma20_status"] = "MA20 상회" if ctx["curr_price"] >= ctx["ma20"] else "MA20 하회"
    if ctx["ma60"] > 0:
        ctx["ma60_status"] = "MA60 상회" if ctx["curr_price"] >= ctx["ma60"] else "MA60 하회"

    # 10) 단순한 미시구조 해석
    if ctx["ask_tot"] > 0 and ctx["bid_tot"] > 0:
        if ctx["orderbook_imbalance"] >= 1.5 and ctx["buy_ratio_now"] >= 60:
            ctx["ask_absorption_status"] = "매도벽 소화 시도"
        elif ctx["orderbook_imbalance"] <= 0.7:
            ctx["ask_absorption_status"] = "매수 우위 / 하락 방어"
        else:
            ctx["ask_absorption_status"] = "중립"

    # 11) 일봉 구조 요약
    if ctx["curr_price"] > 0:
        if ctx["ma5"] > ctx["ma20"] > 0:
            ctx["daily_setup_desc"] = "정배열 / 상승추세"
        elif ctx["curr_price"] >= ctx["prev_high"] > 0:
            ctx["daily_setup_desc"] = "전일 고점 돌파 시도"
        elif ctx["curr_price"] >= ctx["ma20"] > 0:
            ctx["daily_setup_desc"] = "20일선 위 눌림"
        else:
            ctx["daily_setup_desc"] = "중립 또는 약세"

    # 12) 임시 퀀트 점수
    trend_score = 25.0 if ctx["curr_price"] >= ctx["ma20"] > 0 else 10.0
    flow_score = 25.0 if ctx["smart_money_net"] > 0 or ctx["prog_net_qty"] > 0 else 10.0
    orderbook_score = 25.0 if ctx["buy_ratio_now"] >= 55 and ctx["vwap_status"] == "VWAP 상회" else 10.0
    timing_score = 25.0 if ctx["high_breakout_status"] == "돌파" or ctx["drawdown_from_high_pct"] > -1.0 else 10.0

    ctx["trend_score"] = trend_score
    ctx["flow_score"] = flow_score
    ctx["orderbook_score"] = orderbook_score
    ctx["timing_score"] = timing_score
    ctx["score"] = trend_score + flow_score + orderbook_score + timing_score
    ctx["conclusion"] = "데이터 수집 및 파생 계산 완료"

    return ctx
```

---

## 7) 주입데이터 목록 + 수집 위치 + 키움 API 매핑

> 원칙: **주입 데이터는 있으면 좋은 것이 아니라 최대한 모두 수집한다.**

## 7-1. 수집 위치 원칙

### A. `kiwoom_websocket.py`에서 수집
- 실시간성이 중요한 값
- 호가/체결/프로그램/주문체결/조건검색 편입이탈

### B. `kiwoom_utils.py`에서 수집
- REST API 조회값
- 분봉/일봉/투자자/체결강도/프로그램 fallback
- 파생 계산
- 표준 `realtime_ctx` 완성

---

## 7-2. 필드별 매핑표

| 필드 | 수집 위치 | 방식 | API ID / real_type | URL / 엔드포인트 | 구현 상태 | 비고 |
|---|---|---|---|---|---|---|
| `curr_price` | `kiwoom_websocket.py` | WS | `0B` | WS | 일부 구현 | 현재 `curr`로 저장 |
| `open_price` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST 보정 | `0B`, `ka10100` | WS / `/api/dostk/stkinfo` | 일부 구현 | WS 우선, REST 보정 |
| `high_price` | `kiwoom_utils.py` | REST | `ka10100` | `/api/dostk/stkinfo` | 일부 구현 | 필요시 WS FID 추가 가능 |
| `low_price` | `kiwoom_utils.py` | REST | `ka10100` | `/api/dostk/stkinfo` | 일부 구현 | 필요시 WS FID 추가 가능 |
| `prev_close` | `kiwoom_utils.py` | REST | `ka10100` | `/api/dostk/stkinfo` | 일부 구현 | 명세 실제 키 확인 필요 |
| `fluctuation` | `kiwoom_websocket.py` | WS | `0B` | WS | 구현 | 현재 `fluctuation` 저장 |
| `today_vol` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST | `0B`, `ka10046`, `ka10080` | WS / `/api/dostk/mrkcond` / `/api/dostk/chart` | 일부 구현 | 누적거래량 보정 |
| `today_turnover` | `kiwoom_utils.py` | REST 계산 | `ka10046`, `ka10080` | `/api/dostk/mrkcond`, `/api/dostk/chart` | 일부 구현 | VWAP 계산에도 사용 |
| `vol_ratio` | `kiwoom_utils.py` | 파생 | `ka10081` | `/api/dostk/chart` | 일부 구현 | 20일 평균 대비 |
| `turnover_ratio` | `kiwoom_utils.py` | 파생 | `ka10081` + 당일 | `/api/dostk/chart` | 미구현 | 필요시 추가 |
| `v_pw_now` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST | `0B`, `ka10046` | WS / `/api/dostk/mrkcond` | 구현 | REST 보정 권장 |
| `v_pw_1m` | `kiwoom_utils.py` | REST | `ka10046` | `/api/dostk/mrkcond` | 일부 구현 | 현재 `s5` 대응 |
| `v_pw_3m` | `kiwoom_utils.py` | REST | `ka10046` | `/api/dostk/mrkcond` | 일부 구현 | 현재 `s20` 대응 |
| `v_pw_5m` | `kiwoom_utils.py` | REST | `ka10046` | `/api/dostk/mrkcond` | 일부 구현 | 현재 `s60` 대응 |
| `trade_qty_signed_now` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 틱 방향성 요약 |
| `buy_exec_qty` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 최근 체결 매수량 |
| `sell_exec_qty` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 최근 체결 매도량 |
| `buy_ratio_now` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 체결방향 기반 |
| `buy_ratio_1m` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 창 분리 가능 |
| `buy_ratio_3m` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | 창 분리 가능 |
| `best_ask` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0D`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 현재 WS는 5호가 보유 |
| `best_bid` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0D`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 현재 WS는 5호가 보유 |
| `ask_tot` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0B`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 현재 WS 값 존재 |
| `bid_tot` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0B`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 현재 WS 값 존재 |
| `spread_tick` | `kiwoom_utils.py` | 파생 | `0D` / `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | `get_tick_size()` 사용 |
| `orderbook_imbalance` | `kiwoom_utils.py` | 파생 | `0D` / `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | `ask_tot / bid_tot` |
| `ask_top5_qty` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST | `0D`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 5호가 합 |
| `bid_top5_qty` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST | `0D`, `ka10004` | WS / `/api/dostk/mrkcond` | 일부 구현 | 5호가 합 |
| `ask_absorption_status` | `kiwoom_utils.py` | 파생 | WS/REST 혼합 | - | 미구현 | 호가 불균형 + 매수세로 계산 |
| `tape_bias` | `kiwoom_utils.py` | REST 파생 | `ka10003` | `/api/dostk/stkinfo` | 추가 구현 필요 | BUY/SELL 편향 |
| `prog_net_qty` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0w`, `ka90008` | WS / `/api/dostk/mrkcond` | 일부 구현 | `_send_reg`에 0w 추가 필수 |
| `prog_delta_qty` | `kiwoom_websocket.py` | WS | `0w` | WS | 구현 | 현재 REST delta는 placeholder |
| `prog_net_amt` | `kiwoom_websocket.py` + `kiwoom_utils.py` | WS + REST fallback | `0w`, `ka90008` | WS / `/api/dostk/mrkcond` | 일부 구현 | |
| `prog_delta_amt` | `kiwoom_websocket.py` | WS | `0w` | WS | 구현 | |
| `foreign_net` | `kiwoom_utils.py` | REST | `ka10059` | `/api/dostk/stkinfo` | TODO 해결 필요 | 요약 함수 권장 |
| `inst_net` | `kiwoom_utils.py` | REST | `ka10059` | `/api/dostk/stkinfo` | TODO 해결 필요 | 요약 함수 권장 |
| `smart_money_net` | `kiwoom_utils.py` | 파생 | `ka10059` | `/api/dostk/stkinfo` | TODO 해결 필요 | `foreign + inst` |
| `vwap_price` | `kiwoom_utils.py` | 분봉 파생 | `ka10080` | `/api/dostk/chart` | 일부 구현 | 30분봉 누적 기준 |
| `high_breakout_status` | `kiwoom_utils.py` | 파생 | WS/REST 혼합 | - | 일부 구현 | 현재가 vs 고가 |
| `open_position_desc` | `kiwoom_utils.py` | 파생 | WS/REST 혼합 | - | 일부 구현 | 현재가 vs 시가 |
| `vwap_status` | `kiwoom_utils.py` | 파생 | `ka10080` | `/api/dostk/chart` | 일부 구현 | 현재가 vs VWAP |
| `box_high` | `kiwoom_utils.py` | 파생 | `ka10080` | `/api/dostk/chart` | 일부 구현 | 최근 5분 고가 |
| `box_low` | `kiwoom_utils.py` | 파생 | `ka10080` | `/api/dostk/chart` | 일부 구현 | 최근 5분 저가 |
| `drawdown_from_high_pct` | `kiwoom_utils.py` | 파생 | WS/REST 혼합 | - | 일부 구현 | 고가 대비 눌림 |
| `ma5` / `ma20` / `ma60` | `kiwoom_utils.py` | REST 파생 | `ka10081` | `/api/dostk/chart` | 일부 구현 | 일봉 기반 |
| `ma5_status` / `ma20_status` / `ma60_status` | `kiwoom_utils.py` | 파생 | `ka10081` | `/api/dostk/chart` | 일부 구현 | 현재가 대비 |
| `prev_high` / `prev_low` | `kiwoom_utils.py` | REST | `ka10081` | `/api/dostk/chart` | 일부 구현 | 전일 고저 |
| `near_20d_high_pct` | `kiwoom_utils.py` | 파생 | `ka10081` | `/api/dostk/chart` | 일부 구현 | 신고가 근접도 |
| `daily_setup_desc` | `kiwoom_utils.py` | 파생 | `ka10081` | `/api/dostk/chart` | 미흡 | 구조 해석 강화 필요 |
| `trend_score` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | 실제 점수화 권장 |
| `flow_score` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | |
| `orderbook_score` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | |
| `timing_score` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | |
| `score` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | |
| `conclusion` | `kiwoom_utils.py` | 파생 | 전체 | - | placeholder | |

---

## 7-3. 현재 문서에서 사용하는 키움 API ID / URL 정리

> 아래 URL은 업로드된 엑셀의 `API 리스트` 시트를 기준으로 정리한 값이다.

| API ID | API 명 | URL |
|---|---|---|
| `ka10100` | 종목정보 조회 | `/api/dostk/stkinfo` |
| `ka10003` | 체결정보요청 | `/api/dostk/stkinfo` |
| `ka10059` | 종목별투자자기관별요청 | `/api/dostk/stkinfo` |
| `ka10004` | 주식호가요청 | `/api/dostk/mrkcond` |
| `ka10005` | 주식일주월시분요청 | `/api/dostk/mrkcond` |
| `ka10046` | 체결강도추이시간별요청 | `/api/dostk/mrkcond` |
| `ka90008` | 종목시간별프로그램매매추이요청 | `/api/dostk/mrkcond` |
| `ka10080` | 주식분봉차트조회요청 | `/api/dostk/chart` |
| `ka10081` | 주식일봉차트조회요청 | `/api/dostk/chart` |
| `ka10171` | 조건검색 목록조회 | `/api/dostk/websocket` |
| `ka10173` | 조건검색 요청 실시간 | `/api/dostk/websocket` |
| `kt00005` | 체결잔고요청 | `/api/dostk/acnt` |

---

## 8) 실제 적용 순서

### 1단계
- `ai_engine.py`
  - 프롬프트 3개 추가
  - `_infer_realtime_mode()` 추가
  - `build_realtime_quant_packet()` 추가
  - `generate_realtime_report()`를 `realtime_ctx` 기반으로 교체

### 2단계
- `kiwoom_websocket.py`
  - `_send_reg()`에 `0w` 추가
  - 히스토리 deque 추가

### 3단계
- `kiwoom_utils.py`
  - `get_orderbook_snapshot_ka10004()` 추가
  - `get_investor_flow_summary_ka10059()` 추가
  - `summarize_ticks_for_realtime_ka10003()` 추가
  - `build_realtime_analysis_context()` 강화

### 4단계
- 서비스 레이어
  - `ws_data = ws_manager.realtime_data.get(code)`
  - `ctx = build_realtime_analysis_context(token, code, position_status="NONE", ws_data=ws_data)`
  - `engine.generate_realtime_report(stock_name, code, ctx, analysis_mode="AUTO")`

---

## 9) 서비스 레이어 호출 예시

```python
token = get_kiwoom_token()

# 예: ws_manager는 KiwoomWSManager 인스턴스
ws_data = ws_manager.realtime_data.get(stock_code, {})

realtime_ctx = build_realtime_analysis_context(
    token=token,
    stock_code=stock_code,
    position_status="NONE",
    ws_data=ws_data,
)

report = ai_engine.generate_realtime_report(
    stock_name=realtime_ctx.get("stock_name", stock_code),
    stock_code=stock_code,
    realtime_ctx=realtime_ctx,
    analysis_mode="AUTO",
)

print(report)
```

---

## 10) 최종 체크리스트

### `ai_engine.py`
- [ ] `generate_realtime_report()` 입력이 `input_data_text` -> `realtime_ctx`로 바뀌었는가
- [ ] 프롬프트가 `SCALP / SWING / DUAL`로 분리되었는가
- [ ] `AUTO` 분기가 들어갔는가

### `kiwoom_websocket.py`
- [ ] `_send_reg()`에 `0w`가 포함되었는가
- [ ] `0w` 파서가 실제 활성화되는가
- [ ] `realtime_data`에 히스토리 필드가 생겼는가

### `kiwoom_utils.py`
- [ ] 모든 REST 함수가 `token`을 첫 인자로 받는가
- [ ] 함수명이 `기능명_APIID` 규칙을 따르는가
- [ ] `url = get_api_url(...)`를 사용하는가
- [ ] `build_realtime_analysis_context()`가 실제로 외인/기관/체결/호가/분봉/일봉을 다 수집하는가
- [ ] placeholder 값(`TODO`, `50.0`, `데이터 수집 완료`)이 실값으로 대체되었는가

---

## 11) 한 줄 결론

이 작업의 본질은 단순 프롬프트 개선이 아니라:

**`단일 스냅샷 분석` -> `전략 분기형 전술 패킷 분석`으로 바꾸는 것**이다.

즉,
- 텔레그램 입력은 그대로 두고
- 엔진 내부에서 전략을 고르고
- 키움 WebSocket/REST에서 최대한 많은 데이터를 수집해
- `ai_engine.py`는 오직 해석과 문장화만 맡게 만드는 것이 정답이다.
