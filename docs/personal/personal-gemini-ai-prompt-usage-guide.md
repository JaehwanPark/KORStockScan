# Gemini AI 프롬프트 사용 맵 (개인 정리)

버전: Gemini 기준 / 작성일: 2026-04-23  
목표: `SCALPING`(초단타)와 `SWING/KOSPI_ML/KOSDAQ_ML` 경로에서 어떤 프롬프트가 언제 호출되는지, 입력 피처와 액션 타입을 한 번에 확인한다.

## 2026-05-02 Live Model/Interval Update

| 프롬프트/경로 | live model tier | 상태 |
| --- | --- | --- |
| `SCALPING_WATCHING_SYSTEM_PROMPT` | Tier1 fast | 실전 WATCHING hot path |
| `SCALPING_HOLDING_SYSTEM_PROMPT` | Tier1 fast | 일반 보유 감시 hot path |
| `SCALPING_SYSTEM_PROMPT` | Tier1 fast | legacy/shared fallback. 신규 주 경로 아님 |
| `SCALPING_EXIT_SYSTEM_PROMPT` | Tier2 balanced | router 지원은 유지하지만 실전 주 caller는 `holding` |
| `SCALPING_ENTRY_PRICE_PROMPT` | Tier2 balanced | submitted 직전 가격결정 canary |
| `SCALPING_HOLDING_FLOW_SYSTEM_PROMPT` | Tier2 balanced | holding/overnight flow override |
| `SCALPING_OVERNIGHT_DECISION_PROMPT` | Tier2 balanced | 15:20 오버나이트 1차 판단 |
| `EOD_TOMORROW_LEADER_JSON_PROMPT` | Tier3 deep | 장후 심층 후보 선정 |

- OpenAI runtime tier 기본값은 `FAST=gpt-5-nano`, `reasoning=minimal`, `REPORT=gpt-5.4-mini`, `DEEP=gpt-5.4`다. Threshold AI correction은 별도 proposal layer로 `gpt-5.5 -> gpt-5.4 -> gpt-5.4-mini` fallback을 사용한다.
- 호출 interval 기본값은 WATCHING `90초`, HOLDING 일반 `45~180초`, HOLDING critical `20~45초`다.
- `prompt_profile` 개선작업은 코드에는 남아 있지만, 4/22 이후 `shared`/`exit`/canary prompt 정리 항목이 5월 체크리스트에 재등록되지 않아 추적이 끊겼다. 정리 후보는 `2026-05-06` `AIEngineFlagOffBacklog0506`에서 cleanup/backlog/live 유지로 재분류한다.
- Tier1 fast 경로의 prompt 문자열은 `상위 1%`, `프랍 트레이더`, `극강 공격적`, 장황한 해석 역할극을 제거하고, enum action contract와 핵심 피처 기준만 남기는 방향으로 정리한다.

## Mermaid Flow (Gemini 중심)

```mermaid
flowchart TD
  A["전략 진입"] --> B{"전략 타입"}
  B -->|SCALPING| C["analyze_target()"]
  B -->|KOSPI_ML/KOSDAQ_ML| J["analyze_target()"]

  C -->|strategy=SCALPING| D{"prompt_profile"}
  D -->|shared (기본)| E["SCALPING_SYSTEM_PROMPT<br/>Action: BUY/WAIT/DROP"]
  D -->|watching| F["SCALPING_WATCHING_SYSTEM_PROMPT<br/>Action: BUY/WAIT/DROP"]
  D -->|holding / exit alias| G["SCALPING_HOLDING_SYSTEM_PROMPT<br/>Action: HOLD/TRIM/EXIT (action_v2)"]
  D -->|watching 75 shadow 조건| K["SCALPING_SYSTEM_PROMPT_75_CANARY<br/>analyze_target_shadow_prompt()<br/>Action: BUY/WAIT/DROP"]
  D -->|watching buy_recovery_canary 조건| L["SCALPING_BUY_RECOVERY_CANARY_PROMPT<br/>analyze_target_shadow_prompt(prompt_override)<br/>Action: BUY/WAIT/DROP"]

  J --> I["SWING_SYSTEM_PROMPT<br/>Action: BUY/WAIT/DROP"]

  E --> M["결과 정규화"]
  F --> M
  G --> M
  I --> M
  K --> M
  L --> M

  M --> N["공통 출력: action/action_v2/score/reason"]
```

## 공통 실행 규칙 (Gemini 전용)

1. 전략이 `SCALPING`이면 `analyze_target()`에서 프롬프트를 고른다.
2. 전략이 `KOSPI_ML` 또는 `KOSDAQ_ML`이면 바로 `SWING_SYSTEM_PROMPT` 경로로 이동한다.
3. `holding`과 `exit alias`는 같은 `SCALPING_HOLDING_SYSTEM_PROMPT`와 `holding_exit_v1` 스키마를 쓴다.
4. `watching_prompt75_shadow`/`watching_buy_recovery_canary`는 `analyze_target_shadow_prompt()`를 사용하며, 본문 로직은 "감시 축 보조 판단/비교용 분석" 성격이다.

---

## SCALPING 프롬프트 맵

### SCALPING_SYSTEM_PROMPT (프로파일: `shared`)

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target(..., strategy=SCALPING, prompt_profile=...)` 기본값/미지정 |
| 프롬프트명 | `SCALPING_SYSTEM_PROMPT` |
| 입력 피처명 | `[현재 상태]`: `curr`, `fluctuation`, `v_pw`<br> `[정량형 수급 피처]`: `packet_version`, `curr_price`, `latest_strength`, `spread_krw`, `spread_bp`, `top1_depth_ratio`, `top3_depth_ratio`, `orderbook_total_ratio`, `micro_price`, `microprice_edge_bp`, `buy_pressure_10t`, `net_aggressive_delta_10t`, `price_change_10t_pct`, `recent_5tick_seconds`, `prev_5tick_seconds`, `tick_acceleration_ratio`, `same_price_buy_absorption`, `large_sell_print_detected`, `large_buy_print_detected`, `distance_from_day_high_pct`, `intraday_range_pct`, `volume_ratio_pct`, `curr_vs_micro_vwap_bp`, `curr_vs_ma5_bp`, `micro_vwap_value`, `ma5_value`, `ask_depth_ratio`, `net_ask_depth`<br> `[초단타 수급/위치 지표]`: `MA5`, `Micro_VWAP` (또는 상태에서 계산 불가 시 미표기)<br> `[최근 1분봉 흐름]`/`[실시간 호가창]`/`[최근 10틱 상세]` 텍스트 |
| 액션 타입 | `BUY`, `WAIT`, `DROP` (`action`, `action_v2` 동일) |
| 스코어 구간 | 80~100 BUY / 50~79 WAIT / 0~49 DROP |

### SCALPING_WATCHING_SYSTEM_PROMPT (프로파일: `watching`)

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target(..., prompt_profile="watching")` |
| 프롬프트명 | `SCALPING_WATCHING_SYSTEM_PROMPT` |
| 입력 피처명 | 위 SCALPING 공통 피처 + 핵심 조합 위주로 우선 사용: `curr_vs_micro_vwap_bp`, `curr_vs_ma5_bp`, `tick_acceleration_ratio`, `recent_5tick_seconds`, `prev_5tick_seconds`, `buy_pressure_10t`, `net_aggressive_delta_10t`, `same_price_buy_absorption`, `large_sell_print_detected`, `distance_from_day_high_pct`, `top3_depth_ratio` |
| 액션 타입 | `BUY`, `WAIT`, `DROP` (`action`, `action_v2` 동일) |
| 스코어 구간 | 80~100 BUY / 50~79 WAIT / 0~49 DROP |

### SCALPING_HOLDING_SYSTEM_PROMPT (프로파일: `holding`, `exit` alias)

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target(..., prompt_profile="holding")`; legacy/adapter 호환상 `prompt_profile="exit"`도 이 경로로 alias 처리 |
| 프롬프트명 | `SCALPING_HOLDING_SYSTEM_PROMPT` |
| 입력 피처명 | SCALPING 공통 정량 피처 전체 + 실시간 주문서/틱/1분봉 맥락 |
| 액션 타입 | `HOLD`, `TRIM`, `EXIT` (`action_v2`), `action`은 호환용으로 `WAIT`, `SELL`, `DROP` 매핑 |
| 스키마 | `action_schema=holding_exit_v1`, `reason` 1줄 |

### SCALPING_SYSTEM_PROMPT_75_CANARY (shadow)

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target_shadow_prompt(..., prompt_type="scalping_prompt75_shadow")` |
| 프롬프트명 | `SCALPING_SYSTEM_PROMPT_75_CANARY` |
| 입력 피처명 | SCALPING 공통 정량 피처 + 실시간 호가창/틱/분봉 텍스트 |
| 액션 타입 | `BUY`, `WAIT`, `DROP` (shadow 분석 로그 목적) |
| 역할 | 동시 보조 판단으로 메인 판단과 비교 분석 |

### SCALPING_BUY_RECOVERY_CANARY_PROMPT (watching canary)

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target_shadow_prompt(..., prompt_override=SCALPING_BUY_RECOVERY_CANARY_PROMPT, prompt_type="scalping_buy_recovery_canary")` |
| 프롬프트명 | `SCALPING_BUY_RECOVERY_CANARY_PROMPT` |
| 입력 피처명 | `curr_vs_micro_vwap_bp`, `curr_vs_ma5_bp`, `tick_acceleration_ratio`, `buy_pressure_10t`, `net_aggressive_delta_10t`, `same_price_buy_absorption`, `large_sell_print_detected`, `distance_from_day_high_pct`, `top3_depth_ratio`, plus 공통 SCALPING 정량 패킷 |
| 액션 타입 | `BUY`, `WAIT`, `DROP` |
| 역할 | `WAIT 65~79` 후보 중 `promote` 가능 구간만 추려 메인 `BUY`로 승격할지 판단 |

---

## SWING 프롬프트 맵

### SWING_SYSTEM_PROMPT

| 항목 | 내용 |
| --- | --- |
| 호출 위치 | `analyze_target(..., strategy in ["KOSPI_ML", "KOSDAQ_ML"])` |
| 프롬프트명 | `SWING_SYSTEM_PROMPT` |
| 입력 피처명 | `curr`, `fluctuation`, `v_pw`, `volume` (당일 누적 거래량), `program_net_qty`(메이저 수급)<br> 차트 맥락: `MA5`, `MA20`, 추세(`MA5>MA20`/`MA5<MA20`), `주가 위치`, 최근 5봉 가격 흐름 |
| 액션 타입 | `BUY`, `WAIT`, `DROP` |
| 스코어 구간 | 80~100 BUY / 50~79 WAIT / 0~49 DROP |

---

## 기록/분석에서 자주 쓰는 연동 값

| 용도 | 추적 필드/값 |
| --- | --- |
| 결과 판정 | `ai_prompt_type`, `ai_prompt_version`, `result_source` |
| 스키마 판별 | `action_schema`, `action_v2`, `action` |
| 정합성 | `scalp_feature_packet_version`, `tick_acceleration_ratio_sent`, `same_price_buy_absorption_sent` |
| 실패 처리 | `ai_parse_ok`, `ai_parse_fail`, `ai_fallback_score_50`, `cache_hit`, `cache_mode` |
