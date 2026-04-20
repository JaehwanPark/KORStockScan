# 2026-04-20 장후 판정 결과보고서 (감사용)

> 작성시각: `2026-04-20 15:58 KST`  
> 기준 Source/Section: `docs/2026-04-20-stage2-todo-checklist.md` / `장후 체크리스트 (15:30~)`  
> 작성 원칙: `거짓/과장 금지`, `판정-근거-다음 액션 분리`, `오판/수정 이력 명시`

---

## 1. 총평

오늘 장후 작업은 `완료된 구현`, `오늘 기준 판정만 완료된 항목`, `근거 부족으로 보류된 항목`이 섞여 있다.  
따라서 이 보고서는 "많이 처리했다"는 식으로 서술하지 않고, **무엇이 실제로 닫혔고 무엇은 닫히지 않았는지**를 분리해서 기록한다.

핵심 결론은 아래 4가지다.

1. `main runtime OpenAI 라우팅 + 감사필드 실표본`은 오늘 확인됐다.
2. `OpenAI 모델 하드코딩 제거`는 맞았지만, 그 과정에서 내가 `gpt-5.4-nano -> gpt-4.1-mini`로 잘못 내린 오판이 있었고, 이는 같은 날 즉시 수정했다.
3. `2026-04-17` 및 전체 분석기간 baseline 해석은 `문서 파생값`보다 `DB/monitor snapshot 실필드` 기준으로 다시 고정해야 한다는 결론이 오늘 확정됐다.
4. 오늘 soft-stop 대량발생의 우선 원인축은 `same-symbol` 단독이 아니라 `latency + partial/rebase` 쪽으로 재고정하는 것이 더 타당하다. 단, 처방과 내일 검증은 `latency`와 `partial/rebase`를 분리해서 본다.

---

## 2. 판정

### 2-1. 오늘 확정된 항목

| 항목 | 판정 | 비고 |
| --- | --- | --- |
| `main runtime OPENAI 라우팅/감사필드 실표본 확인` | `완료` | 실로그 확인 |
| `main runtime OpenAI 모델 식별자 검증/수정` | `완료` | 단, 중간 오판 1회 발생 후 수정 |
| `작업 6/7 보류 유지 또는 착수 전환 재판정` | `보류 유지` | HOLDING 선행축 미충족 |
| `작업 9 정량형 수급 피처 이식 1차 판정` | `입력 계측 확인 / 출력 경로 부분 미완성 / 확대 보류` | 감사 필드 주입은 확인, 결과 경로는 미완료 |
| `작업 10 HOLDING hybrid 1차 결과 평가` | `shadow-only 유지 / 확대 보류` | 적용 표본 0 |
| `작업 8 감사용 핵심값 3종 투입` | `미완료 유지` | `*_sent` 감사필드 미확인 |
| `작업 11 HOLDING critical 경량 프롬프트 분리` | `오늘 착수 보류` | 선행 HOLDING 축 미정리 |
| `partial-only timeout shadow 1일차 판정` | `폐기` | 표본 0 |
| `04-17 baseline source-of-truth 정합성 감사` | `보정 완료` | hard KPI 기준 수정 |
| `04-06~04-17 전체 분석기간 raw baseline 재감사` | `우선축 재고정 완료` | `latency + partial/rebase` 우선 |
| `legacy shadow 축 전수조사` | `우선순위 고정` | convert/deprecate 분류 |
| `SoftStop0420 RCA` | `1차 확정` | 원인축 1개 + 즉시 파라미터 1개 기록 |
| `리스크 사이즈 긴급 하향 적용 및 기동 확인` | `완료` | 재기동 포함 |

### 2-2. 오늘 확정하지 못한 항목

| 항목 | 오늘 미확정 사유 |
| --- | --- |
| `작업 9 확대 여부` | `ai_parse_ok=False`, `ai_response_ms=0`, `ai_result_source=-` 표본 잔존 |
| `작업 10 확대 여부` | `holding_action_applied=0`, `holding_force_exit_triggered=0`, `force_exit_shadow_samples=0` |
| `작업 8 완료 여부` | `buy_pressure_10t_sent`, `distance_from_day_high_pct_sent`, `intraday_range_pct_sent` 미확인 |
| `budget cap 1일차 효과` | 장중 추가 하향이 들어간 날이라 clean 1일차 표본 아님 |
| `서버 장애 자원수치` | CPU/메모리/IO 과거 시계열이 남아 있지 않음 |

---

## 3. 근거

### 3-1. OpenAI 라우팅/감사필드

#### 확인된 사실

1. `logs/runtime_ai_router_info.log`에서 `role=main`, `scalping_openai=on` 실표본을 확인했다.
2. `logs/pipeline_event_logger_info.log`의 `ai_confirmed`, `ai_holding_review` 표본에서 아래 필드를 확인했다.
   - `scalp_feature_packet_version=scalp_feature_packet_v1`
   - `tick_acceleration_ratio_sent=True`
   - `same_price_buy_absorption_sent=True`
   - `large_sell_print_detected_sent=True`
   - `ask_depth_ratio_sent=True`

#### 아직 확인되지 않은 것

1. OpenAI 결과 경로의 안정성은 오늘 닫히지 않았다.
2. 일부 표본에 `ai_parse_ok=False`, `ai_response_ms=0`, `ai_result_source=-`가 남아 있다.
3. 따라서 오늘 확인된 것은 **"입력 계측이 붙었다"**이지, **"OpenAI 결과 경로가 완전히 정상이다"**는 뜻이 아니다.

---

### 3-2. 모델 식별자 관련 오판 및 수정

#### 사실

1. 오늘 나는 `gpt-5.4-nano` 하드코딩 제거를 수행했다.
2. 그 자체는 맞는 작업이었다.
3. 그러나 그 과정에서 운영 상수까지 `gpt-4.1-mini`로 바꾸는 잘못된 판단을 했다.
4. 사용자가 즉시 지적했고, 내가 재검토한 결과 이 지적이 맞았다.

#### 왜 오판이었는가

1. 이 프로젝트의 운영 의사결정은 이미 `경량/비용효율` 관점에서 `nano 유지`로 정해져 있었다.
2. 수정 대상은 `모델 전략`이 아니라 `하드코딩`이었다.
3. 내가 `식별자 리스크 점검`과 `운영 모델 전략 변경`을 혼동했다.

#### 현재 상태

1. `TRADING_RULES.GPT_FAST_MODEL/GPT_DEEP_MODEL/GPT_REPORT_MODEL`은 다시 `gpt-5.4-nano`로 복구했다.
2. `kiwoom_sniper_v2.py`는 이제 하드코딩이 아니라 상수 주입으로 모델명을 사용한다.
3. `bot_main` 재기동 후 startup log에서 `gpt-5.4-nano` 반영을 재확인했다.

#### 감사상 판단

이 항목은 **"문제 발견 후 수정 완료"**가 아니라, 더 정확히는  
**"작업 중 오판 1회 발생, 사용자 지적으로 즉시 시정, 현재 상태 정상화"**로 기록하는 것이 맞다.

---

### 3-3. baseline source-of-truth 정합성

#### 오늘 확정한 원칙

1. 과거 운영 판정은 `DB 우선`으로 본다.
2. 수동 감사/포렌식은 `monitor_snapshots/*.json.gz`를 우선 사용한다.
3. 평문 `*.json`은 당일 임시 산출물 또는 fallback으로만 본다.
4. 문서에 적힌 파생 지표는 원 raw 필드/산식이 추적되기 전까지 hard KPI나 rollback 기준으로 쓰지 않는다.

#### 오늘 보정한 대표 사례

1. `trade_review.realized_pnl_krw=-223,423`는 `2026-04-17` 당일 실현손익 baseline으로 유지한다.
2. `performance_tuning.trends.*`는 rolling trend이므로 당일 손익 baseline이나 rollback 기준으로 쓰지 않는다.
3. `same_symbol_repeat_flag=55.1%`는 raw 산식 추적 전까지 hard KPI에서 제외한다.

#### 감사상 판단

이 보정은 단순 문서 정리가 아니라,  
**"지금까지 잘못된 기준으로 판정했을 위험을 줄이는 정합성 통제"**로 봐야 한다.

다만 오늘 하루에 모든 과거 판정의 무효/유효를 완전히 확정한 것은 아니다.  
오늘 한 일은 **기준을 다시 세운 것**이지, **모든 과거 결론을 전면 재판정 완료한 것**은 아니다.

---

### 3-4. 전체 분석기간 raw baseline 재감사

`2026-04-13 ~ 2026-04-17` 실필드 재집계에서 확인한 흐름은 아래와 같다.

| 날짜 | latency_ratio | partial_fill_completed_avg_profit_rate | soft_stop_count | capture_efficiency_avg_pct |
| --- | ---: | ---: | ---: | ---: |
| `2026-04-13` | `99.8%` | `0.73` | `0` | `60.6` |
| `2026-04-14` | `99.5%` | `-0.041` | `1` | `50.0` |
| `2026-04-15` | `98.5%` | `-0.282` | `4` | `50.387` |
| `2026-04-16` | `99.4%` | `-0.393` | `5` | `47.837` |
| `2026-04-17` | `99.0%` | `-0.261` | `26` | `39.784` |

#### 해석

1. `latency_ratio`는 특정 하루만의 이상치가 아니라, 거의 전 구간에서 높다.
2. `partial_fill_completed_avg_profit_rate`는 4월 중반부터 지속적으로 악화됐다.
3. `soft_stop_count`는 4월 17일에 급증했지만, 그 전부터 누적 악화 흐름이 있었다.
4. 따라서 우선축을 `same-symbol repeat` 단독으로 두는 것은 과도하게 좁다.
5. 오늘 기준 더 타당한 우선축은 `latency + partial/rebase`다.

---

### 3-5. soft-stop RCA

#### 오늘 1차 판정

- 원인축 1개: `partial/rebase`
- 즉시 파라미터 1개: `SCALPING_MAX_BUY_BUDGET_KRW=1,200,000`

#### 근거

`2026-04-20` 기준:

- `soft_stop_count=18`
- `partial_fill_events=31`
- `full_fill_events=11`
- `position_rebased_after_fill_events=44`
- `partial_fill_completed_avg_profit_rate=-0.25`
- `latency_block_events=838`
- `budget_pass_events=866`

#### 제한

1. 오늘 soft-stop RCA는 `최종 결론`이 아니라 **내일 장전 전까지 운영자가 다시 확인해야 하는 1차 판정**이다.
2. workorder에 따라 이 결론은 사용자 승인 전 자동 반영 완료로 보면 안 된다.

---

## 4. 테스트 및 검증

### 4-1. 코드 검증

```bash
PYTHONPATH=. .venv/bin/python -m py_compile \
  src/utils/constants.py \
  src/engine/kiwoom_sniper_v2.py \
  src/engine/runtime_ai_router.py \
  src/engine/ai_engine_openai_v2.py \
  src/engine/sniper_state_handlers.py
```

결과:

- 통과

### 4-2. 테스트

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  src/tests/test_ai_engine_openai_v2_audit_fields.py \
  src/tests/test_scalping_feature_packet.py
```

결과:

- `4 passed, 1 warning`
- 경고는 `pandas_ta` deprecation warning 1건

### 4-3. runtime 재기동 검증

1. `tmux bot` 세션을 재생성해 `src/bot_main.py`를 다시 기동했다.
2. 프로세스 실행 중임을 확인했다.
3. 재기동 후 log에서 아래를 확인했다.
   - `FAST: gpt-5.4-nano / DEEP: gpt-5.4-nano / REPORT: gpt-5.4-nano`
   - `AI 라우팅 활성화: role=main (main_scalping_openai=ON)`

---

## 5. 오늘 내가 잘못 분석하거나 과하게 말한 지점

감사용으로는 이 항목을 빼면 안 된다.

### 5-1. 모델 전략 오판

- 잘못: `gpt-5.4-nano` 하드코딩 문제를 `gpt-4.1-mini`로 내려야 하는 문제처럼 처리했다.
- 실제: 운영 전략은 `nano 유지`, 수정 대상은 `하드코딩`이었다.
- 현재 상태: `nano 복구 완료`, 하드코딩 제거 유지.

### 5-2. 작업 9 상태를 확대 가능처럼 읽을 위험

- 잘못 위험: 감사필드 실표본을 확인한 사실을 곧바로 OpenAI 결과 경로 정상화처럼 읽을 수 있었다.
- 실제: 오늘 확인한 것은 `입력 계측`이며, 결과 경로는 아직 불안정 표본이 있다.
- 현재 상태: `입력 계측 확인 / 출력 경로 부분 미완성 / 확대 보류`.

### 5-3. 과거 데이터 재판정 완료처럼 읽힐 위험

- 잘못 위험: source-of-truth 정합성 보정이 곧 전체 과거 결론 재판정 완료처럼 들릴 수 있다.
- 실제: 오늘 한 일은 `기준 재고정`이다.
- 현재 상태: 과거 결론 전면 재판정은 아직 아니다.

---

## 6. 남은 불확실성

1. `gpt-5.4-nano` 식별자가 실제 API 호출에서 장중에도 완전히 문제 없는지는 추가 표본이 더 필요하다.
2. OpenAI 결과 경로의 `ai_parse_ok=False` 표본은 아직 정리되지 않았다.
3. HOLDING hybrid는 관찰축 baseline만 있고 적용 표본이 0이므로, 오늘은 확대/축소 결론을 내릴 수 없다.
4. 작업 8 감사필드 3종은 여전히 미구현 또는 미노출 상태다.
5. 오전 서버 장애의 CPU/메모리/IO 수치는 현재 저장된 자료만으로는 확정 불가다.

---

## 7. 다음 액션

### 7-1. 즉시 유지할 것

1. `gpt-5.4-nano` 운영 전략 유지
2. `DB 우선 + gz snapshot 보조` 원칙 유지
3. `same-symbol 단독`보다 `latency + partial/rebase` 우선축 유지

### 7-1A. 감사인 검토 후 즉시 착수한 개선

1. `partial fill min_fill_ratio` 메인 canary를 같은 날 즉시 활성화했다.
   - 목적: `partial_fill -> rebase -> soft_stop` 연쇄를 주문 직후 단계에서 잘라내기 위함
   - 범위: 기존 구현 경로 사용, 설계값은 `default=0.20`, `strong_absolute_override=0.10`, `preset_tp=0.00`
   - 한계: 이는 `partial/rebase` 축 처방이지 `latency` 축 처방은 아니다
2. `system metric sampling`을 1분 주기 경로로 추가했다.
   - 목적: 다음 장애 시 CPU/메모리/IO 사후 확정 불가 상태를 반복하지 않기 위함
   - 저장: `logs/system_metric_samples.jsonl`
   - 포함 항목: loadavg, CPU busy/iowait delta, memory, disk read/write delta, top process
3. `gatekeeper fast_reuse` 시그니처를 즉시 완화했다.
   - 목적: `gatekeeper_fast_reuse_ratio=0.0%` 상태에서 같은 장면을 반복 재평가하던 지연을 줄이기 위함
   - 방식: 미세 가격/호가/잔량 변화가 있어도 동일 장면으로 간주할 수 있도록 fast signature bucket을 coarse 하게 조정
   - 한계: 이는 `latency` 축 중 `AI gatekeeper 재평가 남발` 처방이며, `quote_stale`나 `spread_too_wide` 자체를 해결하는 것은 아니다
4. OpenAI parse fallback 메타를 즉시 복구했다.
   - 목적: `ai_parse_ok=False` 표본이 실제로 얼마나 발생하는지, fallback이 어느 경로로 일어나는지 다음날 바로 판정 가능하게 만들기 위함
   - 방식: `analyze_target()` 정상/실패 경로 모두에서 `ai_parse_ok`, `ai_parse_fail`, `ai_fallback_score_50`, `ai_response_ms`, `ai_result_source`를 일관되게 남기도록 수정
   - 한계: 이는 관측 메타 복구이자 실패경로 명시화이며, 모델 응답 자체의 품질 개선은 아니다
5. OpenAI JSON 응답 파서를 즉시 강건화했다.
   - 목적: fenced JSON, 앞뒤 설명 텍스트, 래핑된 응답 때문에 생기던 불필요 parse fallback을 직접 줄이기 위함
   - 방식: `json.loads` 직파싱 실패 시 ` ```json ... ``` ` 블록과 본문 내 첫 JSON object를 순차 추출해 재파싱하도록 보강
   - 기대효과: `ai_parse_ok=False`와 `openai_parse_fallback` 건수를 모델 변경 없이 직접 축소
   - 한계: 응답이 아예 JSON이 아니거나 필드 스키마 자체가 망가진 경우는 여전히 fallback으로 남는다

### 7-2. 익일 재판정 대상

1. `partial/rebase` 기준 soft-stop 비중
2. 긴급 하향된 risk size의 full-day 효과
3. OpenAI 결과 경로의 parse 안정성

### 7-3. 2026-04-22로 넘길 것

1. `작업 8` 완료 여부
2. `작업 10` 확대 여부
3. `작업 11` 착수 여부
4. `작업 6/7` 보류 해제 여부

---

## 8. 감사인에게 요청하는 검토 포인트

1. 오늘 내가 잡은 `latency + partial/rebase 우선축` 재고정이 과도하게 넓은지, 아니면 오히려 지금까지가 과도하게 좁았는지 검토해 달라.
2. `same-symbol`을 hard KPI에서 제외한 오늘 판단이 적절한지 검토해 달라.
3. `작업 9 입력 계측 확인 / 출력 경로 부분 미완성 / 확대 보류` 판정이 보수적인지, 아니면 아직도 낙관적인지 검토해 달라.
4. `모델 전략 오판`을 단순 실수로 볼지, 아니면 운영 판단 체계의 결함으로 볼지 엄격하게 지적해 달라.

---

## 9. 참고 문서

- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-18-aiprompt-task9-main-openai-audit-report.md](./2026-04-18-aiprompt-task9-main-openai-audit-report.md)
- [2026-04-19-aiprompt-task8-task10-holiday-recheck.md](./2026-04-19-aiprompt-task8-task10-holiday-recheck.md)
- [2026-04-17-midterm-tuning-performance-report.md](./2026-04-17-midterm-tuning-performance-report.md)
- [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)
- [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md)
- [workorder-softstop-0420-postclose.md](./workorder-softstop-0420-postclose.md)
