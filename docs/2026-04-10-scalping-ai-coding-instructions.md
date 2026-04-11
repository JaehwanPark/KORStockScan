# 스캘핑 AI 코딩 작업지시서

## 목적

- 이번 작업의 목적은 `청산 전면 개편`이 아니다.
- 현재 최대 EV 누수 구간인 아래 3개를 코드베이스에 맞게 단계적으로 보강한다.
  - `budget_pass 이후 latency_block`
  - `AI 확정 이후 상류 필터 과차단`
  - `partial fill 이후 체결/청산 정합성 검증`

## 코드베이스 적합성 원칙

1. 새 로깅 체계를 만들지 말고 기존 `ENTRY_PIPELINE`, `HOLDING_PIPELINE`, `pipeline_events JSONL`을 확장한다.
2. `partial fill 처리`와 `preset TP 재발행`은 이미 존재하므로, 먼저 `mismatch 관측/리포트`를 만든다.
3. `common hard time stop`은 현재 `shadow-only`이므로 live exit 로직으로 승격하지 않는다.
4. 전략 의미를 바꾸는 실전 로직 변경은 `원격서버`에 먼저 넣고, `본서버`는 현행 점검계획을 그대로 유지한다.
5. 한 번에 한 축만 바꾼다.

## 이번 작업에서 하지 말 것

- `overbought` 전역 완화
- `청산 전략` 전면 교체
- `fallback`을 즉시 `FOK`로 전환
- `async/프로세스 분리` 같은 대형 인프라 리팩터링 선행
- `AI 재학습` 또는 장기 drift 대응부터 착수

## 실행 시점 가이드

### `2026-04-11` 상태 메모

- 이 문서는 `Phase 0~3`의 기준 작업지시서다.
- 현재 구현 상태는 아래로 읽는다.
  - 완료:
    - `0-1 latency 판정 상세 로그`
    - `0-2 expired_armed 분리`
    - `0-3 partial fill sync 검증`
    - `0-4 AI overlap audit`
    - `0-5 live hard stop taxonomy audit`
    - `1-1 리포트 확장`
  - 잔여:
    - `0-1b 원격 경량 프로파일링`
    - `Phase 2` 원격 전용 로직 변경
    - `Phase 3` 분석 품질 고도화
- 즉, 현재는 `Phase 0/1 일부 착수 전`이 아니라 `Phase 0/1 대부분 완료 후 잔여/후속 단계 정리` 문서로 읽는 것이 맞다.

- `2026-04-13` 기준 남은 즉시 진행 대상:
  - `0-1b 원격 경량 프로파일링`
  - `Phase 0/1` 결과의 장중/장후 검증
- 이유:
  - `Phase 0/1` 본체는 대부분 반영 완료 상태이고, 다음 영업일 체크리스트의 핵심은 남은 관측/검증 항목을 실제 표본으로 확인하는 것이다.
- 아직 즉시 진행하지 않는 대상:
  - `Phase 2` 원격 실전 로직 변경
  - `Phase 3` 분석 고도화 중 후순위 항목
- 착수 조건:
  - `Phase 2`는 `Phase 0/1` 결과로 `latency`, `AI overlap`, `partial fill sync`, `hard stop taxonomy` 중 어떤 축을 먼저 건드릴지 분명해진 뒤 시작한다.

## 단계별 구현 순서

### Phase 0. 관측 보강만 수행

#### 0-1. latency 판정 상세 로그 보강

- 수정 파일:
  - `src/engine/sniper_entry_latency.py`
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_entry_pipeline_report.py`
  - `src/engine/sniper_performance_tuning_report.py`
- 작업:
  - 기존 `latency_pass`, `latency_block`에 아래 필드를 빠짐없이 남긴다.
    - `quote_stale`
    - `ws_age_ms`
    - `ws_jitter_ms`
    - `spread_ratio`
    - `signal_price`
    - `latest_price`
    - `computed_allowed_slippage`
    - `decision`
    - `reason`
    - `latency_canary_applied`
    - `latency_canary_reason`
  - 필요하면 신규 stage는 `latency_evaluated` 1개만 추가하고, 별도 로깅 시스템은 만들지 않는다.
- 완료 기준:
  - `quote_stale=False latency_block` 표본만 바로 필터링 가능
  - 일별로 `why DANGER` 분포를 볼 수 있음

#### 0-1b. 원격 경량 프로파일링

- 대상:
  - `songstockscan` only
- 작업:
  - 패키지 설치 없이 가능한 범위에서 표준 도구 기반 관측만 수행한다.
  - 우선순위:
    - `cProfile` 또는 내장 timing instrumentation
    - OS 기본 sampling 도구가 이미 있으면 그것만 사용
  - 측정 목적:
    - `quote_stale=False`인데 `latency_block`로 끝나는 케이스의 hot path 추정
    - `budget_pass -> latency_block` 직전 구간의 처리 지연 관측
- 주의:
  - 원인 단정 금지
  - 실전 로직 변경 금지
  - 환경 변경이나 패키지 설치 금지
- 완료 기준:
  - 원격 관측 결과로 `hot path 후보`를 1~3개 설명 가능

#### 0-2. `expired_armed` 이벤트 분리

- 수정 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_missed_entry_counterfactual.py`
  - `src/engine/sniper_entry_pipeline_report.py`
- 작업:
  - `entry_armed` TTL 만료를 `latency_block`과 분리한다.
  - stage 후보:
    - `entry_armed_expired`
    - `entry_armed_expired_after_wait`
- 완료 기준:
  - 리포트에서 `latency_block`과 `expired_armed`가 별도 축으로 집계됨

#### 0-3. partial fill sync 검증 로그 추가

- 수정 파일:
  - `src/engine/sniper_execution_receipts.py`
  - `src/engine/sniper_trade_review_report.py`
  - `src/engine/sniper_performance_tuning_report.py`
- 작업:
  - `ENTRY_FILL` 처리 시 아래를 구조화 로그로 남긴다.
    - `fill_qty`
    - `cum_filled_qty`
    - `requested_qty`
    - `remaining_qty`
    - `avg_buy_price`
    - `entry_mode`
    - `fill_quality`
    - `preset_tp_price`
    - `preset_tp_ord_no_before`
    - `preset_tp_ord_no_after`
    - `sync_status`
  - 신규 stage 후보:
    - `position_rebased_after_fill`
    - `preset_exit_sync_ok`
    - `preset_exit_sync_mismatch`
- 주의:
  - `_refresh_scalp_preset_exit_order()`를 새로 만들지 말고 기존 경로 위에 계측만 추가
- 완료 기준:
  - partial fill 후 `buy_qty != exit qty` 여부를 자동 검증 가능

#### 0-4. AI 입력 피처 vs 상류 필터 감사 로그

- 수정 파일:
  - `src/engine/ai_engine_openai_v2.py`
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_strength_momentum.py`
- 작업:
  - 각 `ai_confirmed` 시도마다 아래를 남긴다.
    - `ai_score`
    - `latest_strength`
    - `buy_pressure_10t`
    - `distance_from_day_high_pct`
    - `intraday_range_pct`
    - `momentum_tag`
    - `threshold_profile`
    - `overbought_blocked`
    - `blocked_stage`
  - AI에 이미 들어가는 피처와 후단 필터 값을 같은 row에 남겨 중복 여부를 감사한다.
- 완료 기준:
  - `AI가 이미 본 것`과 `후단에서 다시 막은 것`을 같은 표에서 비교 가능

#### 0-5. live hard stop taxonomy audit

- 수정 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_trade_review_report.py`
  - 필요 시 관련 테스트
- 작업:
  - `COMMON shadow-only`와 별개로 존재하는 live stop 계열을 정리한다.
  - 최소 분류:
    - `scalp_preset_hard_stop_pct`
    - `protect_hard_stop`
    - `scalp_hard_stop_pct`
    - `hard_time_stop_shadow`
  - 각 exit rule이
    - `live인지`
    - `shadow-only인지`
    - `어느 분기에서 호출되는지`
    - `entry_mode/position_tag`와 어떤 관계인지
    를 리포트 가능 상태로 만든다.
- 완료 기준:
  - `hard stop` 관련 질문에 대해 `어떤 stop이 live이고 어떤 stop이 shadow인지` 로그/리포트로 설명 가능

### Phase 1. 리포트/집계 반영

#### 1-1. 리포트 확장

- 수정 파일:
  - `src/engine/sniper_entry_pipeline_report.py`
  - `src/engine/sniper_missed_entry_counterfactual.py`
  - `src/engine/sniper_trade_review_report.py`
  - `src/engine/sniper_performance_tuning_report.py`
- 작업:
  - 필수 집계:
    - `budget_pass -> submitted` 전환율
    - `latency_block reason 분포`
    - `quote_stale=False` cohort 성과
    - `expired_armed` 건수
    - `full fill vs partial fill` 성과
    - `preset_exit_sync_mismatch` 건수
    - `AI overlap audit` 요약
- 완료 기준:
  - 다음 완화 판단이 `손익 단일치`가 아니라 `퍼널/체결 품질/감사 결과`로 가능

### Phase 2. 원격 전용 로직 변경

#### 2-1. EV-aware latency degrade

- 수정 파일:
  - `src/engine/sniper_entry_latency.py`
  - `src/utils/constants.py`
  - 필요한 경우 `src/tests/test_sniper_entry_latency.py`
- 구현 원칙:
  - 기존 `SAFE/CAUTION/DANGER` 분류는 유지
  - action만 원격 canary로 조정
  - `quote_stale=True`는 그대로 차단
  - `quote_stale=False`이며 기대값이 slippage보다 충분히 클 때만 `DANGER -> degraded fallback` 허용
- feature flags:
  - `ENABLE_EV_AWARE_LATENCY_GATE`
  - `ENABLE_DANGER_DEGRADE_WHEN_FRESH_QUOTE`
  - `LATENCY_GATE_DANGER_EV_MULTIPLIER`
  - `LATENCY_GATE_CAUTION_QTY_MULTIPLIER`
  - `LATENCY_GATE_DANGER_QTY_MULTIPLIER`
- rollout:
  - `songstockscan` only
  - `position_tag` 제한 또는 별도 canary profile로만 적용
- 완료 기준:
  - 원격에서 `budget_pass -> submitted` 전환율이 개선되고, slippage 악화가 허용 범위 내임

#### 2-2. dynamic strength selective override

- 선행 조건:
  - `AI overlap audit` 완료
  - `momentum_tag/threshold_profile`별 missed winner 분포 확보
- 수정 파일:
  - `src/engine/sniper_strength_momentum.py`
  - `src/utils/constants.py`
  - `src/tests/test_strength_momentum_gate.py`
- 구현 원칙:
  - 전역 threshold 변경 금지
  - 특정 `momentum_tag × threshold_profile`만 override
  - `overbought`는 건드리지 않음
- 완료 기준:
  - 원격 selective cohort에서만 `entry_armed` 또는 `submitted` 개선 근거 확보

### Phase 3. 분석 품질 고도화

#### 3-1. realistic/conservative counterfactual 추가

- 수정 파일:
  - `src/engine/sniper_missed_entry_counterfactual.py`
  - `src/tests/test_missed_entry_counterfactual.py`
- 작업:
  - 기존 방식은 `optimistic`으로 유지
  - 추가 모드:
    - `realistic`
    - `conservative`
  - 출력 필드:
    - `counterfactual_mode`
    - `estimated_entry_price`
    - `estimated_exit_price`
    - `estimated_return_pct`
    - `estimated_pnl_krw`
- 완료 기준:
  - latency 완화 효과를 낙관/현실/보수 3계층으로 비교 가능

#### 3-2. exit authority 명문화

- 수정 파일:
  - `src/engine/sniper_state_handlers.py`
  - `src/engine/sniper_trade_review_report.py`
  - 관련 테스트
- 작업:
  - live 동작을 바꾸기 전에 `exit_decision_source`만 먼저 로깅
  - 값 후보:
    - `PRESET_HARD_STOP`
    - `PRESET_PROTECT`
    - `AI_REVIEW_EXIT`
    - `SOFT_STOP`
    - `TIMEOUT`
    - `MANUAL`
- 주의:
  - `hard_time_stop_shadow`는 여전히 `shadow-only`
- 완료 기준:
  - 청산 충돌 논의를 로그/리포트로 검증 가능

## 로그 항목 표준

### ENTRY_PIPELINE 필수 필드

- `id`
- `entry_mode`
- `position_tag`
- `decision`
- `reason`
- `quote_stale`
- `ws_age_ms`
- `ws_jitter_ms`
- `spread_ratio`
- `signal_price`
- `latest_price`
- `computed_allowed_slippage`
- `latency_canary_applied`
- `latency_canary_reason`

### HOLDING_PIPELINE 필수 필드

- `id`
- `entry_mode`
- `buy_qty`
- `fill_qty`
- `cum_filled_qty`
- `remaining_qty`
- `preset_tp_price`
- `preset_tp_ord_no`
- `sync_status`
- `exit_rule`
- `exit_decision_source`

## 테스트 기준

### 단위 테스트

- `src/tests/test_sniper_entry_latency.py`
  - SAFE/CAUTION/DANGER 유지
  - `quote_stale=False` degrade branch
  - `quote_stale=True` fail-closed 유지
- `src/tests/test_missed_entry_counterfactual.py`
  - `expired_armed` 집계
  - optimistic/realistic/conservative 산출
- `src/tests/test_entry_pipeline_report.py`
  - 신규 stage 노출
  - reason breakdown 집계
- `src/tests/test_performance_tuning_report.py`
  - JSONL 기반 신규 필드 반영
- `src/tests/test_trade_review_report_revival.py`
  - `fill_quality`
  - `exit_decision_source`
- `src/tests/test_sniper_scale_in.py`
  - partial fill 누적
  - preset 재발행
  - duplicate exit 방지

### 권장 실행 명령

```bash
PYTHONPATH=. .venv/bin/pytest -q \
  src/tests/test_sniper_entry_latency.py \
  src/tests/test_missed_entry_counterfactual.py \
  src/tests/test_entry_pipeline_report.py \
  src/tests/test_performance_tuning_report.py \
  src/tests/test_trade_review_report_revival.py \
  src/tests/test_sniper_scale_in.py \
  src/tests/test_strength_momentum_gate.py \
  src/tests/test_kiwoom_orders.py
```

### 리포트 검증 기준

- `budget_pass -> submitted` 전환율이 자동 계산될 것
- `quote_stale=False latency_block` 표본이 따로 보일 것
- `expired_armed`가 따로 보일 것
- `full fill / partial fill` 성과가 분리될 것
- `preset_exit_sync_mismatch` 건수가 보일 것
- `optimistic / realistic / conservative` counterfactual 비교가 가능할 것

## 롤아웃 규칙

1. `Phase 0~1`은 로컬/원격 공통 반영 가능
2. `Phase 2`는 원격 전용
3. 본서버는 원격 결과가 확인되기 전 로직 변경 금지
4. 모든 canary는 `rollback env flag`를 갖출 것

## 최종 지시

- 이번 작업의 본질은 새 전략 발명이 아니라 `관측 보강 -> 원격 단일축 실험 -> 본서버 후행 반영`이다.
- 순서를 바꾸지 않는다.
  1. `관측`
  2. `리포트`
  3. `원격 latency`
  4. `AI overlap audit`
  5. `dynamic strength selective override`
  6. `counterfactual 현실화`
