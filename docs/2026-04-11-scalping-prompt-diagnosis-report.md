# 2026-04-11 스캘핑 AI 프롬프트 진단용 팩트 리포트

## 목적

- 시스템트레이딩 전문가가 현재 스캘핑 자동매매의 `WATCHING(감시)` 진입판단과 `HOLDING(보유)` 판단 구조를 코드 기준으로 검토할 수 있도록, 프롬프트/판단기준/입력 데이터/미입력 가능 데이터를 객관적 사실만 정리한다.
- 해석 대상은 현재 라이브 경로의 `SCALPING` 전략이다.

## 범위와 근거 소스

- 라이브 AI 엔진 초기화: `src/engine/kiwoom_sniper_v2.py:1041-1067`
- 스캘핑 AI 프롬프트: `src/engine/ai_engine.py:27-47`
- 스캘핑 AI 호출 경로: `src/engine/ai_engine.py:969-1037`
- 감시 상태 진입 로직: `src/engine/sniper_state_handlers.py:1155-1724`
- 보유 상태 청산/AI 리뷰 로직: `src/engine/sniper_state_handlers.py:2384-3014`
- 표준 실시간 컨텍스트 빌더: `src/utils/kiwoom_utils.py:1726-2035`
- OpenAI 정량형 대체 프롬프트/피처 추출기: `src/engine/ai_engine_openai_v2.py:46-83`, `src/engine/ai_engine_openai_v2.py:427-655`
- 웹소켓 실시간 필드 기본셋: `src/engine/kiwoom_websocket.py:205-231`, `src/engine/kiwoom_websocket.py:784-810`

## 현재 런타임 구조

- 현재 라이브 실거래 경로의 주 AI 엔진은 `GeminiSniperEngine`이다.
- `OpenAIDualPersonaShadowEngine`은 gatekeeper/overnight용 `shadow-only` 보정 엔진이다. 스캘핑 `WATCHING` 진입과 일반 `HOLDING` 청산의 라이브 의사결정에는 직접 관여하지 않는다.
- 현재 셸에서 `KORSTOCKSCAN_*`, `GEMINI_*`, `OPENAI_*` 환경변수 override는 확인되지 않았다.
- 따라서 아래 임계값 수치는 `src/utils/constants.py`의 코드 기본값 기준이다.

## 1. WATCHING 감시종목 진입판단

### 1-1. 현재 라이브 호출 경로

1. `handle_watching_state()`가 `SCALPING` 종목을 순회한다.
2. 사전 기계 게이트를 통과한 경우에만 `recent_ticks(10)`, `recent_candles(40)`를 조회한다.
3. `ai_engine.analyze_target(stock['name'], ws_data, recent_ticks, recent_candles)`를 호출한다.
4. `GeminiSniperEngine.analyze_target()`는 `strategy="SCALPING"` 기본값으로 `SCALPING_SYSTEM_PROMPT`와 `_format_market_data()` 출력물을 함께 보낸다.
5. AI 응답의 `score`를 `rt_ai_prob`에 반영하고, 최종적으로 `current_ai_score >= 75`일 때만 `entry_armed`로 넘어간다.

### 1-2. 현재 라이브 프롬프트 전문

현재 라이브 경로에서 사용하는 스캘핑 프롬프트는 아래와 같다.

```text
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
```

### 1-3. 현재 라이브 기계 판단기준

#### A. AI 호출 전 사전 차단 기준

- 거래시간:
  - 일반 스캘핑은 `09:03` 이후만 허용
  - `VCP_NEXT`는 `09:00` 이후 허용
  - 신규 스캘핑 진입은 기본값 기준 `15:00` 이후 차단
- 공통 차단:
  - 매수 일시중지 상태
  - 종목별 cooldown 진행 중
  - 이미 `alerted_stocks`에 포함
  - `curr_price <= 0`
  - `position_tag == VCP_CANDID`
- 과열 차단:
  - `fluctuation >= max_surge`
  - 또는 `intraday_surge >= max_intraday_surge`
  - 코드 기본값은 `20.0%`, `16.0%`
  - 실제 적용값은 `get_dynamic_scalp_thresholds()`로 시총/turnover hint에 따라 조정될 수 있음
- Big-Bite 하드게이트:
  - 기능이 켜지고 태그가 대상이면 `confirmed=False`에서 차단
  - 코드 기본값은 `BIG_BITE_HARD_GATE_ENABLED=False`
- 동적 체결강도 게이트:
  - `evaluate_scalping_strength_momentum()` 결과가 `allowed=False`이고 `SCALP_DYNAMIC_VPW_OBSERVE_ONLY=False`이면 차단
- 체결강도 기본 허들:
  - `current_vpw < VPW_SCALP_LIMIT`이고 동적 override가 없으면 차단
  - 코드 기본값 `VPW_SCALP_LIMIT=120`
- 유동성 차단:
  - `(ask_tot + bid_tot) * curr_price < MIN_SCALP_LIQUIDITY`
  - 코드 기본값 `500,000,000원`
- 스캐너 포착가 대비 추격 차단:
  - `gap_pct >= 1.5%`

#### B. AI 호출 조건

- `radar.get_smart_target_price()`로 계산한 `target_buy_price`가 0보다 커야 함
- `curr_price <= target_buy_price * 1.015` 이어야 함
- 즉 `is_vip_target == True`일 때만 AI를 부른다
- 추가 조건:
  - `AI_WATCHING_COOLDOWN` 경과 또는 첫 호출
  - `ws_data['orderbook']` 존재
  - `recent_ticks` 존재
- 코드 기본값 `AI_WATCHING_COOLDOWN=180초`

#### C. AI 호출 후 적용 기준

- 첫 AI 호출 턴에서는 `Big-Bite confirmed`가 아니면 즉시 주문하지 않고 `first_ai_wait`로 한 루프 대기한다
- Big-Bite 보정:
  - `confirmed=True`면 `+5점`
  - `armed=True`면 `+2점`
- 진입 허용 기준:
  - `current_ai_score < 75` 이고 `!= 50`이면 차단
  - 차단 시 `AI_WAIT_DROP_COOLDOWN=300초`
  - `50점`은 폴백/보류 응답으로 취급되어 즉시 차단하지 않음
- 통과 시:
  - `entry_armed` 생성
  - 투자비중은 `INVEST_RATIO_SCALPING_MIN~MAX` 범위에서 현재 AI 점수에 따라 선형 계산
  - 코드 기본값 `0.10 ~ 0.30`

### 1-4. 현재 라이브 프롬프트에 실제로 입력되는 데이터

`_format_market_data(ws_data, recent_ticks, recent_candles)`가 현재 프롬프트에 넣는 항목은 아래뿐이다.

#### A. 현재 상태

- 현재가
- 전일대비 등락률
- 웹소켓 체결강도(`v_pw`)

#### B. 초단타 수급/위치 지표

- 최근 분봉 기반 `MA5`
- 최근 분봉 기반 `Micro-VWAP`
- 최근 분봉 고점 대비 현재가 이격도
- 호가 불균형 문장 요약

#### C. 거래량 분석

- 최근 분봉 마지막 봉 거래량 vs 직전 평균 거래량 비율 문장 요약

#### D. 최근 틱 요약

- 최근 틱 가격 추세
- 최근 틱 묶음이 발생하는 데 걸린 시간(속도)
- 최근 틱 매수 압도율
- 최근 틱 최신 체결강도

#### E. 원본 시퀀스

- 최근 1분봉 시계열
  - 체결시간, 시가, 고가, 저가, 종가, 거래량
- 실시간 호가창
  - 1~5호가 매도/매수 가격과 잔량
- 최근 10틱 상세
  - 시간, 방향(BUY/SELL), 체결가, 체결량, 강도

### 1-5. 현재 공급 가능하지만 프롬프트에는 넣지 않는 데이터

#### A. `ws_data`에 이미 존재하지만 현재 프롬프트 미입력

- 프로그램:
  - `prog_net_qty`
  - `prog_delta_qty`
  - `prog_net_amt`
  - `prog_delta_amt`
  - `prog_buy_qty`
  - `prog_sell_qty`
  - `prog_buy_amt`
  - `prog_sell_amt`
- 체결/체결량:
  - `tick_trade_value`
  - `cum_trade_value`
  - `buy_exec_volume`
  - `sell_exec_volume`
  - `net_buy_exec_volume`
  - `buy_exec_single`
  - `sell_exec_single`
  - `buy_ratio`
- 호가/잔량 변화:
  - `net_bid_depth`
  - `bid_depth_ratio`
  - `net_ask_depth`
  - `ask_depth_ratio`
- 세션/신선도:
  - `market_session_state`
  - `market_session_remaining`
  - `last_ws_update_ts`
  - `last_prog_update_ts`
- 히스토리:
  - `program_history`
  - `strength_momentum_history`
  - `last_trade_tick`

#### B. `handle_watching_state()`에 이미 존재하지만 현재 프롬프트 미입력

- `marcap`
- `liquidity_value`
- `intraday_surge`
- `scanner_price`, `gap_pct`
- `target_buy_price`, `used_drop_pct`
- `position_tag`
- 동적 체결강도 게이트 산출값:
  - `reason`
  - `window_buy_value`
  - `window_buy_ratio`
  - `window_exec_buy_ratio`
  - `window_net_buy_qty`
  - `threshold_profile`
  - `position_tag`
- Big-Bite 산출값:
  - `impact_ratio`
  - `agg_value`
  - `chase_pct`
  - `triggered/confirmed`
- `ratio`(실제 주문 비중)

#### C. 저장은 하지만 프롬프트에 직접 넣지 않는 AI 감사용 값

- `latest_strength`
- `buy_pressure_10t`
- `distance_from_day_high_pct`
- `intraday_range_pct`
- `momentum_tag`
- `threshold_profile`
- `overbought_blocked`
- `blocked_stage`

이 값들은 `ENTRY_PIPELINE` 로그에는 남기지만, 현재 라이브 Gemini 프롬프트 본문에는 넣지 않는다.

## 2. HOLDING 보유종목 판단

### 2-1. 현재 라이브 호출 경로

보유 상태에서 스캘핑 AI는 두 경로로만 호출된다.

#### A. 일반 보유 중 AI 리뷰

1. `handle_holding_state()`가 현재 손익률, 최고수익률, 보유시간을 계산한다.
2. `time_elapsed > dynamic_min_cd` 이고 `price_change >= dynamic_price_trigger` 또는 `time_elapsed > dynamic_max_cd`일 때만 후보가 된다.
3. 동일 시장 스냅샷/근접 밴드가 아니면 `recent_ticks(10)`, `recent_candles(40)`를 조회한다.
4. `ai_engine.analyze_target(..., cache_profile="holding")`를 호출한다.
5. 응답에서 `raw_ai_score`만 꺼내 `기존 점수 60% + 신규 점수 40%`로 평활화한다.

#### B. `SCALP_PRESET_TP` 출구엔진 1회 AI 검문

- `profit_rate >= 0.8%`이고 아직 `ai_review_done=False`일 때 1회 호출한다.
- 이때는 `recent_ticks`만 넣고 `recent_candles=[]`로 호출한다.
- AI 응답의 `action`이 `DROP`이면 즉시 청산하고, `WAIT/BUY`면 `+0.3%` 보호선만 설정한다.

### 2-2. HOLDING 전용 프롬프트 존재 여부

- 현재 일반 `HOLDING`용 별도 프롬프트는 없다.
- 일반 보유 중 리뷰와 `SCALP_PRESET_TP` 1회 검문 모두 `WATCHING` 진입판단과 동일한 `SCALPING_SYSTEM_PROMPT`를 재사용한다.
- `cache_profile="holding"`은 캐시 키/TTL만 바꾸며, 프롬프트 본문 필드는 바꾸지 않는다.

### 2-3. 일반 HOLDING의 기계 판단기준

#### A. AI 리뷰를 아예 생략하는 조건

- `ai_engine` 또는 `radar`가 없으면 생략
- `time_elapsed <= dynamic_min_cd`면 생략
- `price_change < dynamic_price_trigger`이고 `time_elapsed <= dynamic_max_cd`면 생략
- 아래 fast reuse 조건을 모두 만족하면 AI를 다시 부르지 않고 skip한다.
  - 이전 시장 signature와 동일
  - reuse 시간창 내
  - `price_change` 작음
  - websocket age fresh
  - `near_ai_exit_band` 아님
  - `near_safe_profit_band` 아님
  - `near_low_score_band` 아님

#### B. 일반 HOLDING AI 리뷰 트리거 수치

- `safe_profit_pct = 0.5%`
- critical zone:
  - `profit_rate >= 0.5%`
  - 또는 `profit_rate < 0`
- cooldown:
  - critical zone이면 `dynamic_min_cd=3초`, `dynamic_max_cd=10초`
  - 그 외 `dynamic_min_cd=15초`, `dynamic_max_cd=50초`
- 가격 변화 허들:
  - critical zone이면 `0.20%`
  - 그 외 `0.40%`

#### C. 일반 HOLDING AI 응답 사용 방식

- 일반 보유 상태에서는 AI의 `action`과 `reason`을 실시간 청산에 직접 사용하지 않는다
- 일반 보유 상태에서 실제로 사용하는 것은 `smoothed_score`뿐이다
- `smoothed_score = 기존 score * 0.6 + 신규 raw score * 0.4`
- 저점수 연속 카운트 증가 조건:
  - `held_sec >= 180`
  - `profit_rate <= -0.7%`
  - `current_ai_score <= 35`

#### D. 일반 HOLDING의 실제 청산 기준

- 보호선 우선:
  - `hard_stop_price` 이탈
  - `trailing_stop_price` 이탈
- 스캘핑 공통 손절:
  - `SCALP_HARD_STOP = -2.5%`
  - `SCALP_STOP = -1.5%`
  - `current_ai_score >= 75`면 soft stop도 `-2.5%`로 완화
  - `current_ai_score < 75`면 soft stop은 `-1.5%`
- OPEN_RECLAIM 전용:
  - `never_green`
  - `양전환 후 재약세`
- SCANNER + fallback 전용:
  - `never_green`
  - `양전환 후 재약세`
- AI 조기손절:
  - `held_sec >= 180`
  - `profit_rate <= -0.7%`
  - `current_ai_score <= 35`
  - `ai_low_score_hits >= 3`
- AI 모멘텀 둔화 익절:
  - `profit_rate >= 0.5%`
  - `current_ai_score < 45`
  - `held_sec >= 90`
- 트레일링 익절:
  - `profit_rate >= 0.5%` 구간에서
  - `current_ai_score >= 75`면 허용 drawdown `0.8%`
  - `current_ai_score < 75`면 허용 drawdown `0.4%`

### 2-4. HOLDING에서 현재 프롬프트에 실제로 입력되는 데이터

#### A. 일반 HOLDING AI 리뷰

- `WATCHING`과 동일한 `_format_market_data()` 출력
- 즉 현재가/등락률/체결강도, MA5/Micro-VWAP/고점대비이격, 거래량 분석, 최근 분봉, 최근 틱, 실시간 호가창만 들어간다
- 보유 전용 데이터는 프롬프트에 직접 들어가지 않는다

#### B. `SCALP_PRESET_TP` 1회 AI 검문

- `WATCHING`과 같은 프롬프트를 사용한다
- 차이점:
  - `recent_ticks`는 공급
  - `recent_candles=[]`
- 코드상 즉시 청산 비교식은 `['SELL', 'DROP']`이지만, 현재 프롬프트 정의상 반환 가능 action은 `BUY|WAIT|DROP`뿐이다
- 따라서 이 경로에서는 아래 데이터가 빠진다
  - 분봉 시계열
  - 분봉 기반 MA5
  - 분봉 기반 Micro-VWAP
  - 분봉 기반 거래량 분석
  - 분봉 기반 고점 대비 이격도

### 2-5. HOLDING에서 공급 가능하지만 프롬프트에는 넣지 않는 데이터

#### A. 보유 상태에서 이미 계산하지만 미입력인 포지션 데이터

- `buy_price`
- `profit_rate`
- `peak_profit`
- `held_sec`
- `held_time_min`
- `highest_prices[code]`
- `trailing_stop_price`
- `hard_stop_price`
- `ai_low_score_hits`
- `last_ai_profit`
- `exit_mode`
- `entry_mode`
- `position_tag`
- `protect_profit_pct`

#### B. 보유 상태 분기 판단에 쓰지만 미입력인 태그/코호트 정보

- `OPEN_RECLAIM`
- `SCANNER`
- `fallback`
- `SCALP_PRESET_TP`

#### C. 보유 상태 전용 지속시간/근접밴드 계산값

- `near_ai_exit_band`
- `near_safe_profit_band`
- `near_low_score_band`
- `open_reclaim_near_ai_exit_sustain_sec`
- `scanner_fallback_near_ai_exit_sustain_runtime_sec`

#### D. 일반 보유 청산 판단에 실사용하지만 프롬프트 미입력인 threshold 값

- `dynamic_stop_pct`
- `dynamic_trailing_limit`
- `ai_exit_score_limit`
- `ai_exit_min_loss_pct`
- `ai_exit_min_hold_sec`
- `momentum_decay_score_limit`
- `momentum_decay_min_hold_sec`

## 3. 이미 구현돼 있지만 현재 라이브 스캘핑 경로에는 안 들어가는 더 풍부한 데이터 경로

### 3-1. 표준 `realtime_ctx` 패킷 빌더

`build_realtime_analysis_context()`는 이미 아래 데이터를 묶어 `realtime_ctx`로 만들 수 있다.

#### A. 기본/포지션

- `market_cap`
- `strat_label`
- `position_status`
- `avg_price`
- `pnl_pct`
- `target_price`
- `target_reason`
- `trailing_pct`
- `stop_pct`
- `score`
- `conclusion`

#### B. 퀀트/시장 구조

- `trend_score`
- `flow_score`
- `orderbook_score`
- `timing_score`
- `today_vol`
- `vol_ratio`
- `today_turnover`
- `v_pw_now/1m/3m/5m`
- `buy_ratio_now/1m/3m`
- `trade_qty_signed_now`

#### C. 프로그램/체결/투자주체

- `prog_net_qty`
- `prog_delta_qty`
- `prog_buy_qty`
- `prog_sell_qty`
- `prog_buy_amt`
- `prog_sell_amt`
- `foreign_net`
- `inst_net`
- `smart_money_net`
- `tick_trade_value`
- `cum_trade_value`
- `buy_exec_volume`
- `sell_exec_volume`
- `net_buy_exec_volume`
- `buy_exec_single`
- `sell_exec_single`
- `buy_ratio_ws`
- `exec_buy_ratio`

#### D. 호가/깊이

- `net_bid_depth`
- `bid_depth_ratio`
- `net_ask_depth`
- `ask_depth_ratio`
- `micro_flow_desc`
- `depth_flow_desc`
- `program_flow_desc`
- `best_ask`
- `best_bid`
- `ask_tot`
- `bid_tot`
- `orderbook_imbalance`
- `spread_tick`
- `tape_bias`
- `ask_absorption_status`

#### E. 위치/일봉 구조

- `vwap_price`
- `vwap_status`
- `open_position_desc`
- `high_breakout_status`
- `box_high`
- `box_low`
- `daily_setup_desc`
- `ma5_status`
- `ma20_status`
- `ma60_status`
- `prev_high`
- `prev_low`
- `near_20d_high_pct`
- `drawdown_from_high_pct`

현재 이 패킷은 `SWING gatekeeper`와 수동 실시간 리포트 경로에는 쓰지만, 라이브 `SCALPING WATCHING/HOLDING analyze_target()`에는 쓰지 않는다.

### 3-2. OpenAI 정량형 스캘핑 대체 프롬프트와 추가 피처

리포지토리에는 라이브 Gemini 경로와 별개로 아래 정량형 피처가 이미 구현돼 있다.

- `spread_krw`
- `spread_bp`
- `top1_depth_ratio`
- `top3_depth_ratio`
- `orderbook_total_ratio`
- `micro_price`
- `microprice_edge_bp`
- `buy_pressure_10t`
- `net_aggressive_delta_10t`
- `price_change_10t_pct`
- `recent_5tick_seconds`
- `prev_5tick_seconds`
- `tick_acceleration_ratio`
- `same_price_buy_absorption`
- `large_sell_print_detected`
- `large_buy_print_detected`
- `distance_from_day_high_pct`
- `intraday_range_pct`
- `volume_ratio_pct`
- `curr_vs_micro_vwap_bp`
- `curr_vs_ma5_bp`
- `micro_vwap_value`
- `ma5_value`

이 정량형 패킷과 `SCALPING_SYSTEM_PROMPT_V3`는 `src/engine/ai_engine_openai_v2.py`에 구현돼 있으나, 현재 라이브 스캘핑 의사결정 경로에는 연결되어 있지 않다.

## 4. 전문가 전달용 핵심 사실 요약

- 현재 라이브 스캘핑 `WATCHING`과 일반 `HOLDING`은 같은 `SCALPING_SYSTEM_PROMPT`를 사용한다.
- 일반 `HOLDING`에는 보유시간, 현재손익률, 최고수익률, 진입태그, fallback 여부, stop 가격이 프롬프트에 들어가지 않는다.
- 일반 `HOLDING`에서 AI의 `action`과 `reason`은 실시간 청산에 직접 사용되지 않고, `score`만 사용된다.
- `SCALP_PRESET_TP` 1회 AI 검문은 같은 프롬프트를 쓰지만 `recent_candles=[]`로 호출되어 분봉 기반 데이터가 빠진다.
- `SCALP_PRESET_TP` 경로에는 `SELL` 비교가 있으나, 현재 프롬프트 정의상 실제 반환 가능 값은 `BUY|WAIT|DROP`이다.
- 현재 라이브 스캘핑 프롬프트에는 프로그램 절대매수/절대매도, 외인/기관 순매수, 체결대금, 체결량 세부, 잔량 변화율, 세션 신선도 정보가 직접 들어가지 않는다.
- 더 풍부한 `realtime_ctx` 패킷과 정량형 OpenAI 대체 프롬프트는 이미 코드에 존재하지만, 현재 라이브 스캘핑 경로에는 미연결 상태다.
