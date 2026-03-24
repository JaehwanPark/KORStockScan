# 실시간 종목분석 고도화 통합본

## 1) 왜 지금 구조가 얕게 나오는가

현재 `ai_engine.py`는 **실시간 자동 매매용 JSON 판정 경로**와 **텔레그램 수동 리포트 경로**가 분리되어 있다.

- `analyze_target()`는 이미 `strategy`에 따라 `SCALPING_SYSTEM_PROMPT`와 `SWING_SYSTEM_PROMPT`를 분기한다.
- 반면 `generate_realtime_report()`는 여전히 단일 `REALTIME_ANALYSIS_PROMPT`만 사용한다.
- 그래서 텔레그램 수동 분석은 **스캘핑/스윙 구분 없이 평균적인 설명문**으로 흐르기 쉽다.
- 또 현재 주입 데이터는 "지금 상태 스냅샷"은 있지만 **1~5분 변화율, VWAP, 고가 돌파, 일봉 구조, 보유 맥락**이 약해서 깊은 분석이 어렵다.

핵심 처방은 아래 3가지다.

1. **프롬프트를 SCALP / SWING / DUAL 로 분리**
2. **입력 데이터를 스냅샷에서 전술 패킷(tactical packet)으로 승격**
3. **텔레그램에서는 종목코드만 받고, 서버 내부에서 AUTO 전략분기**

---

## 2) 목표 구조

### 사용자 경험
- 텔레그램 입력: `005930`
- 내부 처리:
  - `analysis_mode="AUTO"`
  - 서버가 `SCALP / SWING / DUAL` 자동 판정
  - 모드별 프롬프트와 패킷으로 리포트 생성

### 설계 원칙
- `ai_engine.py`는 **판단과 리포트 생성만 담당**
- `kiwoom_utils.py`는 **REST / WebSocket 수집 + 파생지표 계산 + 표준화된 dict 반환**
- `ai_engine.py` 안에서 키움 API 직접 호출 금지

---

## 3) 파일 책임 분리

### `kiwoom_utils.py`,`kiwoom_websocket.py`
역할:
- 키움 REST API 호출
- 키움 WebSocket 구독
- 실시간 버퍼링
- 1분/3분/5분 변화율 계산
- VWAP / 고가돌파 / 호가불균형 / 체결속도 / 프로그램 증감 등 파생값 계산
- `RealtimeAnalysisContext` 반환

### `ai_engine.py`
역할:
- `REALTIME_ANALYSIS_PROMPT_SCALP`
- `REALTIME_ANALYSIS_PROMPT_SWING`
- `REALTIME_ANALYSIS_PROMPT_DUAL`
- `_infer_realtime_mode()`
- `build_realtime_quant_packet()`
- `generate_realtime_report_v2()`

---

## 4) 권장 데이터 계약서

### `RealtimeAnalysisContext` 표준 dict

```python
realtime_ctx = {
    # 기본
    "stock_name": "삼성전자",
    "stock_code": "005930",
    "position_status": "NONE",         # NONE / HOLDING
    "avg_price": 0,
    "pnl_pct": 0.0,
    "strat_label": "AUTO",

    # 현재 시세
    "curr_price": 60200,
    "fluctuation": -0.17,
    "open_price": 60300,
    "high_price": 60700,
    "low_price": 59800,
    "prev_close": 60300,
    "vwap_price": 60120,

    # 거래량/거래대금
    "today_vol": 128152628,
    "today_turnover": 7720000000000,
    "vol_ratio": 146.3,
    "turnover_ratio": 138.1,

    # 체결/체결강도
    "v_pw_now": 98.92,
    "v_pw_1m": 103.4,
    "v_pw_3m": 108.7,
    "v_pw_5m": 111.2,
    "trade_qty_signed_now": -82,
    "buy_exec_qty": 0,
    "sell_exec_qty": 0,
    "buy_ratio_now": 49.2,
    "buy_ratio_1m": 52.8,
    "buy_ratio_3m": 55.1,

    # 호가
    "best_ask": 60200,
    "best_bid": 60100,
    "ask_tot": 420123,
    "bid_tot": 365100,
    "spread_tick": 1,
    "orderbook_imbalance": 1.15,
    "ask_top5_qty": 180000,
    "bid_top5_qty": 152000,
    "ask_absorption_status": "보통",
    "tape_bias": "SELL_DOMINANT",

    # 프로그램/수급
    "prog_net_qty": 8043,
    "prog_delta_qty": 0,
    "prog_net_amt": 483,
    "prog_delta_amt": 0,
    "foreign_net": 0,
    "inst_net": 0,
    "smart_money_net": 0,

    # 구조
    "high_breakout_status": "미돌파",
    "open_position_desc": "시가 하회",
    "vwap_status": "VWAP 상회",
    "box_high": 60300,
    "box_low": 60050,
    "drawdown_from_high_pct": -0.82,

    # 일봉
    "ma5": 59820,
    "ma20": 59050,
    "ma60": 57510,
    "ma5_status": "상회",
    "ma20_status": "상회",
    "ma60_status": "상회",
    "prev_high": 60600,
    "prev_low": 59500,
    "near_20d_high_pct": 1.8,
    "daily_setup_desc": "정배열 눌림 후 전일고점 재도전",

    # 퀀트 엔진 분해 점수
    "trend_score": 72.0,
    "flow_score": 61.0,
    "orderbook_score": 55.0,
    "timing_score": 44.0,
    "score": 58.0,
    "conclusion": "조건부 관찰",
    "target_price": 61500,
    "target_reason": "전일고점 돌파 시 1차 탄력",
    "stop_price": 59500,
    "stop_pct": 1.2,
    "take_profit_price": 61500,
    "trailing_pct": 1.5,

    # 운영 정보
    "session_stage": "REGULAR",        # PRE / REGULAR / AFTER
    "captured_at": "2026-03-24 09:17:12",
}
```

---

## 5) 전략 분기 위치

### 결론
전략 분기는 텔레그램이 아니라 **`generate_realtime_report_v2()` 진입 직전**에 한다.

### 분기 순서
1. 명시적 전략이 있으면 우선
2. 보유 종목이면 스윙 가중치
3. 장초반 + 체결가속 + VWAP 상회 + 고가돌파 시도면 스캘핑 가중치
4. 애매하면 DUAL

### AUTO 모드 판단 함수

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

    # 시간대
    if "0900" <= now_hhmm <= "1030":
        scalp_score += 2
    elif "1300" <= now_hhmm <= "1500":
        swing_score += 1

    # 당일 변동성/거래량
    if abs(fluctuation) >= 3.0:
        scalp_score += 1
    if vol_ratio >= 150:
        scalp_score += 2
    elif 70 <= vol_ratio <= 130:
        swing_score += 1

    # 체결강도 가속
    if v_pw_now >= 120 and (v_pw_now - v_pw_3m) >= 15:
        scalp_score += 2

    # 프로그램 가속
    if prog_delta_qty > 0:
        scalp_score += 1
        swing_score += 1

    # 위치
    if curr_price > 0 and vwap_price > 0 and curr_price >= vwap_price:
        scalp_score += 1
    if "돌파" in high_breakout_status:
        scalp_score += 1

    # 일봉 구조
    if any(k in daily_setup_desc for k in ["눌림", "정배열", "전고점", "박스상단", "추세전환"]):
        swing_score += 2
    if any(k in daily_setup_desc for k in ["급등후", "이격", "과열", "장대음봉"]):
        swing_score -= 1

    if abs(scalp_score - swing_score) <= 1:
        return "DUAL"

    return "SCALP" if scalp_score > swing_score else "SWING"
```

---

## 6) 프롬프트 3종

### 6-1. 스캘핑 전용

```python
REALTIME_ANALYSIS_PROMPT_SCALP = """
너는 상위 1% 초단타 프랍 트레이더다.
목표는 1~2%의 짧은 파동만 빠르게 먹고, 모멘텀이 식는 즉시 손절하는 것이다.

[분석 원칙]
1. 현재값보다 변화율을 우선하라. 특히 체결강도, 매수세, 프로그램 순매수의 1~5분 변화가 핵심이다.
2. 호가가 매도 우위여도 실제 체결이 매도벽을 먹고 올라가면 강한 돌파다.
3. VWAP 아래, 고가 돌파 실패, 스프레드 확대, 체결 둔화는 추격 금지 신호다.
4. 기계목표가보다 중요한 것은 '지금 진입하면 즉시 반응이 나오는 자리인가'다.
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

### 6-2. 스윙 전용

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

### 6-3. 듀얼 전용

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

## 7) 주입데이터 빌더

```python
def build_realtime_quant_packet(
    *,
    stock_name: str,
    stock_code: str,
    curr_price: int,
    fluctuation: float,
    strat_label: str,
    trailing_pct: float,
    stop_pct: float,
    target_price: int,
    target_reason: str,
    today_vol: int,
    vol_ratio: float,
    v_pw_now: float,
    v_pw_1m: float = 0.0,
    v_pw_3m: float = 0.0,
    v_pw_5m: float = 0.0,
    prog_net_qty: int = 0,
    prog_delta_qty: int = 0,
    prog_net_amt: int = 0,
    prog_delta_amt: int = 0,
    foreign_net: int = 0,
    inst_net: int = 0,
    ask_tot: int = 0,
    bid_tot: int = 0,
    buy_ratio_now: float = 0.0,
    buy_ratio_3m: float = 0.0,
    score: float = 0.0,
    trend_score: float = 0.0,
    flow_score: float = 0.0,
    orderbook_score: float = 0.0,
    timing_score: float = 0.0,
    conclusion: str = "",
    trade_mode: str = "AUTO",
    position_status: str = "NONE",
    avg_price: int = 0,
    pnl_pct: float = 0.0,
    vwap_price: int = 0,
    high_breakout_status: str = "정보없음",
    spread_tick: int = 0,
    tape_bias: str = "중립",
    daily_setup_desc: str = "정보없음",
    ma5_status: str = "정보없음",
    ma20_status: str = "정보없음",
    ma60_status: str = "정보없음",
    prev_high: int = 0,
    prev_low: int = 0,
    near_20d_high_pct: float = 0.0,
):
    orderbook_imbalance = (ask_tot / bid_tot) if bid_tot > 0 else 999.0
    smart_money_net = foreign_net + inst_net

    common_block = (
        f"[기본]\n"
        f"- 종목명: {stock_name}\n"
        f"- 종목코드: {stock_code}\n"
        f"- 매매모드: {trade_mode}\n"
        f"- 감시전략: {strat_label}\n"
        f"- 보유상태: {position_status}\n"
        f"- 평균단가: {avg_price:,}원\n"
        f"- 현재손익률: {pnl_pct:+.2f}%\n"
        f"- 현재가격: {curr_price:,}원 (전일비 {fluctuation:+.2f}%)\n"
        f"- 기계목표가: {target_price:,}원 (사유: {target_reason})\n"
        f"- 익절/손절: {trailing_pct}% / {stop_pct}%\n"
        f"- 퀀트 점수 분해: 추세 {trend_score:.1f} / 수급 {flow_score:.1f} / 호가 {orderbook_score:.1f} / 타점 {timing_score:.1f}\n"
        f"- 퀀트 종합점수: {score:.1f}\n"
        f"- 퀀트 엔진 결론: {conclusion}\n"
        f"\n"
        f"[수급/체결]\n"
        f"- 누적거래량: {today_vol:,}주 (20일 평균대비 {vol_ratio:.1f}%)\n"
        f"- 체결강도 현재/1분전/3분전/5분전: {v_pw_now:.1f} / {v_pw_1m:.1f} / {v_pw_3m:.1f} / {v_pw_5m:.1f}\n"
        f"- 매수세 현재/3분평균: {buy_ratio_now:.1f}% / {buy_ratio_3m:.1f}%\n"
        f"- 프로그램 순매수 현재/증감: {prog_net_qty:,}주 / {prog_delta_qty:+,}주\n"
        f"- 프로그램 순매수 금액/증감: {prog_net_amt:,} / {prog_delta_amt:+,}\n"
        f"- 외인/기관 당일 가집계: 외인 {foreign_net:,}주 / 기관 {inst_net:,}주\n"
        f"- 외인+기관 합산: {smart_money_net:+,}주\n"
        f"\n"
        f"[호가/구조]\n"
        f"- 매도잔량/매수잔량: {ask_tot:,} / {bid_tot:,}\n"
        f"- 호가 불균형비: {orderbook_imbalance:.2f}\n"
        f"- 스프레드: {spread_tick}틱\n"
        f"- 직전 체결 방향 우세: {tape_bias}\n"
        f"- VWAP: {vwap_price:,}원 ({'상회' if curr_price >= vwap_price else '하회'})\n"
        f"- 고가 돌파 여부: {high_breakout_status}\n"
    )

    scalp_block = (
        f"\n[스캘핑 관점 핵심]\n"
        f"- 체결강도 가속도: {v_pw_now - v_pw_3m:+.1f}\n"
        f"- 프로그램 가속: {prog_delta_qty:+,}주\n"
        f"- 즉시성 평가 포인트: VWAP / 고가 돌파 / 스프레드 / 테이프 편향\n"
    )

    swing_block = (
        f"\n[스윙 관점 핵심]\n"
        f"- 일봉 구조: {daily_setup_desc}\n"
        f"- 5/20/60일선 상태: {ma5_status}, {ma20_status}, {ma60_status}\n"
        f"- 전일 고점/저점: {prev_high:,} / {prev_low:,}\n"
        f"- 최근 20일 신고가 근접도: {near_20d_high_pct:.1f}%\n"
    )

    if trade_mode == "SCALP":
        return common_block + scalp_block
    if trade_mode == "SWING":
        return common_block + swing_block
    return common_block + scalp_block + swing_block
```

---

## 8) `generate_realtime_report_v2()` 교체안

```python
def generate_realtime_report_v2(
    self,
    stock_name: str,
    stock_code: str,
    realtime_ctx: dict,
    analysis_mode: str = "AUTO",
):
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

        packet_text = build_realtime_quant_packet(
            stock_name=stock_name,
            stock_code=stock_code,
            trade_mode=selected_mode,
            **realtime_ctx,
        )

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
                model_override="gemini-pro-latest",
            )
        except Exception as e:
            log_error(f"🚨 [실시간 분석:{selected_mode}] AI 에러: {e}")
            return f"⚠️ AI 실시간 분석 생성 중 에러 발생: {e}"
```

---

## 9) `kiwoom_utils.py` 에 필요한 인터페이스

### 최소 인터페이스

```python
class KiwoomRealtimeAnalyzerDataSource:
    def build_realtime_analysis_context(self, stock_code: str, position_status: str = "NONE") -> dict:
        """ai_engine.py 로 넘길 표준 realtime_ctx 반환"""
        raise NotImplementedError
```

### 권장 호출 흐름

```python
# telegram handler
stock_code = user_input.strip()
realtime_ctx = kiwoom_utils.build_realtime_analysis_context(stock_code)
report = ai_engine.generate_realtime_report_v2(
    stock_name=realtime_ctx["stock_name"],
    stock_code=stock_code,
    realtime_ctx=realtime_ctx,
    analysis_mode="AUTO",
)
```

---

## 10) 주입데이터 목록 + 키움 API 매핑

아래 표의 원칙은 단순하다.

- **Raw field**: 키움 REST/WebSocket에서 직접 수집
- **Derived field**: `kiwoom_utils.py`가 계산해서 `ai_engine.py`에 넘김
- `ai_engine.py`는 수집하지 않고 소비만 함

### A. 공통 필수 필드

| 필드 | 설명 | 소스 구분 | 권장 키움 API | 비고 |
|---|---|---:|---|---|
| `stock_name` | 종목명 | Raw | `ka10001`, `ka10100` | 기초 종목정보 |
| `stock_code` | 종목코드 | Raw | 입력값 | |
| `curr_price` | 현재가 | Raw | 실시간 `0B` 또는 `0A` | 둘 다 가능, `0B` 우선 |
| `fluctuation` | 전일비 등락률 | Raw | `0B`, `0A`, `ka10095` | |
| `open_price` | 시가 | Raw | `0B`, `0A`, `ka10001` | 장중은 `0B` 우선 |
| `high_price` | 고가 | Raw | `0B`, `0A`, `ka10001` | |
| `low_price` | 저가 | Raw | `0B`, `0A`, `ka10001` | |
| `prev_close` | 전일종가 | Raw | `ka10100` | `lastPrice` |
| `today_vol` | 누적거래량 | Raw | `0B`, `0A`, `ka10095` | |
| `today_turnover` | 누적거래대금 | Raw | `0B`, `0A` | |
| `v_pw_now` | 현재 체결강도 | Raw | `0B`의 `228`, `ka10095`의 `cntr_str` | 실시간은 `0B` 우선 |
| `best_ask` | 최우선 매도호가 | Raw | `0B`, `0C` | |
| `best_bid` | 최우선 매수호가 | Raw | `0B`, `0C` | |
| `ask_tot` | 총매도잔량 | Derived | `0D` | 10호가 합산 |
| `bid_tot` | 총매수잔량 | Derived | `0D` | 10호가 합산 |
| `prog_net_qty` | 프로그램 순매수수량 | Raw | 실시간 `0w`의 `210` 또는 `ka90008` | 장중 실시간은 `0w` 우선 |
| `prog_delta_qty` | 프로그램 순매수수량 증감 | Raw / Derived | `0w`의 `211`, `ka90008`의 `prm_netprps_qty_irds` | 실시간 즉시값은 `0w` 우선 |
| `target_price` | 기계 목표가 | Derived | 퀀트 엔진 | 키움 아님 |
| `target_reason` | 목표가 사유 | Derived | 퀀트 엔진 | |
| `score` | 종합 점수 | Derived | 퀀트 엔진 | |
| `conclusion` | 퀀트 결론 | Derived | 퀀트 엔진 | |

### B. 스캘핑 핵심 필드

| 필드 | 설명 | 소스 구분 | 권장 키움 API | 비고 |
|---|---|---:|---|---|
| `v_pw_1m`, `v_pw_3m`, `v_pw_5m` | 체결강도 변화 | Derived | `0B` 누적 버퍼 또는 `ka10046` | 즉시성은 WS 버퍼가 더 좋음 |
| `buy_exec_qty` | 매수체결량 | Raw | `0B`의 `1031` | 비어있을 수 있어 fallback 필요 |
| `sell_exec_qty` | 매도체결량 | Raw | `0B`의 `1030` | 비어있을 수 있음 |
| `buy_ratio_now` | 현재 매수비율 | Raw | `0B`의 `1032` | 값 비어있으면 체결부호로 계산 |
| `buy_ratio_1m`, `buy_ratio_3m` | 분단위 매수비율 평균 | Derived | `0B` 또는 `ka10046` | |
| `trade_qty_signed_now` | 단건 체결 방향성 | Raw | `0B`의 `15` | +매수 / -매도 |
| `spread_tick` | 스프레드 틱 수 | Derived | `0C` 또는 `0D` | |
| `orderbook_imbalance` | 호가 불균형비 | Derived | `0D` | `ask_tot / bid_tot` |
| `ask_top5_qty`, `bid_top5_qty` | 상위 5호가 잔량 합 | Derived | `0D` | |
| `tape_bias` | 직전 체결 편향 | Derived | `0B` 버퍼 | 최근 n틱 매수/매도 우세 |
| `vwap_price` | 당일 VWAP | Derived | `0B` + 분봉/틱 누적 | 키움 원시 필드 직접 제공 아님 |
| `high_breakout_status` | 당일 고가 돌파 여부 | Derived | `0B`의 고가 + 현재가 | |
| `box_high`, `box_low` | 직전 5분 박스 | Derived | `ka10080` 또는 0B 버퍼 | |
| `drawdown_from_high_pct` | 당일 고가 대비 이격 | Derived | `0B` | |

### C. 스윙 핵심 필드

| 필드 | 설명 | 소스 구분 | 권장 키움 API | 비고 |
|---|---|---:|---|---|
| `ma5`, `ma20`, `ma60` | 이동평균선 | Derived | `ka10080`, `ka10081` | 분봉/일봉 선택 |
| `ma5_status`, `ma20_status`, `ma60_status` | 이평선 상하관계 | Derived | 위 파생값 | |
| `prev_high`, `prev_low` | 전일 고가/저가 | Derived | `ka10081` 또는 `ka10080` | 일봉 권장 |
| `near_20d_high_pct` | 20일 신고가 근접도 | Derived | `ka10081` | 20일 최고가와 비교 |
| `daily_setup_desc` | 일봉 패턴 설명 | Derived | `ka10081` + 퀀트 규칙 | 눌림/돌파/이격 등 |
| `foreign_net` | 외인 순매수 | Raw / Derived | `ka10045`, `ka10061`, `ka10063~65`, `ka10015` | 용도별 선택 |
| `inst_net` | 기관 순매수 | Raw / Derived | `ka10045`, `ka10061`, `ka10015` | |
| `smart_money_net` | 외인+기관 합 | Derived | 위 raw 합산 | |
| `prog_net_amt` | 프로그램 순매수금액 | Raw | `0w`의 `212`, `ka90008` | |
| `prog_delta_amt` | 프로그램 순매수금액 증감 | Raw | `0w`의 `213`, `ka90008`의 `prm_netprps_amt_irds` | |

### D. 보조 필드

| 필드 | 설명 | 소스 구분 | 권장 키움 API | 비고 |
|---|---|---:|---|---|
| `session_stage` | 장전/정규장/장후 | Raw / Derived | 실시간 `0s`, `0B`의 `290`, 시스템시각 | |
| `exp_cntr_price` | 예상체결가 | Raw | `0H`, `ka10001`, `ka10095` | 장전/장후 유용 |
| `exp_cntr_qty` | 예상체결량 | Raw | `0H`, `ka10001`, `ka10095` | |
| `position_status` | 미보유/보유 | External | 계좌/전략엔진 | 키움 계좌 API 연동 가능 |
| `avg_price` | 평균단가 | External | 계좌 API | 텔레그램 사용자 계좌와 연동 시 |
| `pnl_pct` | 현재 손익률 | Derived | 계좌 API + 현재가 | |

---

## 11) 키움 API별 실무 추천 우선순위

### 반드시 붙일 것
1. 실시간 `0B` 주식체결
2. 실시간 `0D` 주식호가잔량
3. 실시간 `0w` 종목프로그램매매
4. `ka10080` 주식분봉차트조회
5. `ka10081` 주식일봉차트조회
6. `ka10046` 체결강도추이시간별
7. `ka10045` 또는 `ka10061` 외인/기관 추이

### 있으면 좋은 것
1. `0C` 주식우선호가
2. `0H` 주식예상체결
3. `ka10095` 관심종목정보요청
4. `ka90008` 종목시간별프로그램매매추이
5. `ka10015` 일별거래상세요청

### 실무 해석
- **스캘핑 즉시성**은 `0B + 0D + 0w` 조합이 핵심
- **스윙 구조**는 `ka10080/81 + ka10045/61` 조합이 핵심
- `ka10095`는 멀티 종목 일괄 조회에는 좋지만, 단일 종목 정밀 분석의 주 소스보다는 보조 소스가 적절

---

## 12) 키움에서 직접 안 나오는 값들

아래는 키움에서 raw로 딱 떨어지지 않으므로 `kiwoom_utils.py`가 계산해야 한다.

| 파생값 | 계산 방식 |
|---|---|
| `vwap_price` | 장중 누적 `가격 * 거래량 / 누적거래량` |
| `vol_ratio` | `오늘 누적거래량 / 최근 20일 동일시각 평균 거래량` 또는 단순 20일 평균 대비 |
| `turnover_ratio` | `오늘 누적거래대금 / 최근 20일 동일시각 평균 거래대금` |
| `buy_ratio_1m`, `buy_ratio_3m` | 최근 체결 버퍼에서 매수체결량 / 전체체결량 |
| `tape_bias` | 최근 n틱의 방향/체결량 가중 판단 |
| `high_breakout_status` | `현재가 >= 당일고가`, 실패 여부 포함 |
| `daily_setup_desc` | 일봉 패턴 규칙 기반 라벨링 |
| `near_20d_high_pct` | `현재가 / 최근20일최고가 - 1` |
| `orderbook_imbalance` | `총매도잔량 / 총매수잔량` |
| `ask_absorption_status` | 호가 잔량 감소 + 체결량 증가 조합으로 추정 |

---

## 13) `kiwoom_utils.py`,`kiwoom_websocket.py` 구현 체크리스트

### 수집 : `kiwoom_utils.py`,`kiwoom_websocket.py` 내에 이미 구현되어 있는 TR 코드와 API 코드를 탐색하여 활용하고 없을경우 새로운 함수로 만든다.
- [ ] `0B` 실시간 등록/버퍼링 (`kiwoom_websocket.py`)
- [ ] `0D` 실시간 등록/버퍼링 (`kiwoom_websocket.py`)
- [ ] `0w` 실시간 등록/버퍼링 (`kiwoom_websocket.py`)
- [ ] `ka10080` 최근 분봉 조회 (`kiwoom_utils.py`)
- [ ] `ka10081` 최근 일봉 조회 (`kiwoom_utils.py`)
- [ ] `ka10046` 체결강도 시간별 조회 (`kiwoom_utils.py`)
- [ ] `ka10045` 또는 `ka10061` 투자자/기관 조회 (`kiwoom_utils.py`)

### 파생
- [ ] VWAP 계산
- [ ] 최근 1/3/5분 체결강도 변화
- [ ] 최근 1/3분 매수비율
- [ ] 호가 총합/상위5합
- [ ] 스프레드 틱 계산
- [ ] 고가 돌파/실패 판정
- [ ] 5/20/60일선 계산
- [ ] 20일 신고가 근접도 계산
- [ ] 퀀트 점수 분해

### 전달
- [ ] `RealtimeAnalysisContext` dict 조립
- [ ] 텔레그램 요청 시 `build_realtime_analysis_context(stock_code)` 제공

---

## 14) 실무적 권장안

### 가장 먼저 바꿀 것
1. `generate_realtime_report()`를 `generate_realtime_report_v2()`로 교체
2. `REALTIME_ANALYSIS_PROMPT` 단일 구조 폐기
3. `AUTO` 전략분기 추가
4. `build_realtime_quant_packet()` 도입
5. `kiwoom_utils.py`에서 `realtime_ctx` 표준 계약서 반환

### 가장 큰 성능 개선 포인트
- 프롬프트보다 **입력 패킷 구조**가 더 중요하다.
- 스캘핑은 **속도 / 호가 / VWAP / 돌파즉시성**이 핵심이다.
- 스윙은 **일봉 구조 / 수급 지속성 / 손익비**가 핵심이다.
- 같은 종목이라도 오전 9시 5분과 오후 2시 20분의 분석 문법은 달라야 한다.

---

## 15) 한 줄 결론

**텔레그램에서는 종목코드만 받고, `kiwoom_utils.py`가 풍부한 `realtime_ctx`를 만들어 넘기고, `ai_engine.py`는 `AUTO -> SCALP/SWING/DUAL` 분기 후 모드별 프롬프트로 깊게 해석하는 구조가 가장 좋다.**
