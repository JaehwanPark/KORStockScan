# 스캘핑 전문가 의견 검증 및 현행 플랜 보완안

## 목적

- 전문가 2인 의견을 현재 코드베이스와 운영 플랜에 대조해 `즉시 채택`, `감사 후 채택`, `현 단계 부적합`으로 구분한다.
- 기준은 `기대값/순이익 극대화`, `한 번에 한 축 canary`, `원격 선행 적용`, `리포트 정합성 우선`이다.

## 1. 종합 판정

- 판정:
  - 전문가 의견의 큰 방향은 `대체로 타당`하다.
  - 다만 현재 플랜과 이미 맞물려 있는 제안이 많고, 일부는 `이미 구현됨`, `shadow-only`, `근거 부족` 상태라 바로 실행안으로 넣으면 오히려 계획이 흐려진다.
- 핵심 결론:
  - 현재 플랜의 대축은 유지한다.
    - `1순위 latency`
    - `2순위 dynamic strength 재설계`
    - `3순위 overbought 보류`
    - `full fill / partial fill 분리`
    - `원격 선행, 본서버 후행`
  - 이번 비교검토로 추가할 것은 `튜닝 전 감사/관측 축` 3개다.
    - `latency 세부 판정근거 분해`
    - `partial fill 동기화 검증 리포트`
    - `AI 입력 피처 vs 상류 필터 중복 감사`
  - 추가 점수 재판정(`2026-04-10-operator-message-validation`)으로 아래 2개를 더 반영한다.
    - `원격 경량 프로파일링`
    - `scalping live hard stop taxonomy audit`

## 2. 현행 플랜과 전문가 의견 비교

| 항목 | 현재 플랜 | 전문가 의견 | 보완 판정 |
| --- | --- | --- | --- |
| `latency` 우선순위 | `1순위`, `quote_stale=False` 중심, 원격 `remote_v2` 선행 | `최우선 병목` | `유지 + 세부 이유 로그 강화` |
| `dynamic strength` | 전역 완화 금지, `momentum_tag/threshold_profile`별 재설계 | 국소 재설계 권고 | `유지` |
| `overbought` | 표본 부족으로 유지 | 즉시 완화 근거 약함 | `유지` |
| `full/partial fill 분리` | 이미 운영 원칙에 포함 | partial fill 별도 해석 권고 | `유지 + sync mismatch 리포트 추가` |
| `hard time stop` | `shadow-only` 유지 | AI 충돌 가능성 점검 | `실전 수정 아님, 감사 항목으로만 유지` |
| `counterfactual` | optimistic 중심 | 낙관 편향 보정 필요 | `realistic/conservative 추가` |
| `원격 우선 적용` | 이미 원칙으로 반영 | 선행 canary 권고 | `유지` |

## 3. 전문가 의견 타당성 검증

### A. 즉시 채택할 의견

1. `budget_pass 이후 latency_block`이 최우선 병목
   - 현재 체크리스트와 장후 결론이 이미 이 축으로 정리되어 있다.
   - 보완점은 완화보다 먼저 `why DANGER` 분포를 더 잘 남기는 것이다.

2. `dynamic strength`는 전역 완화가 아니라 국소 재설계
   - 현재 플랜과 일치한다.
   - 다음 단계는 `below_window_buy_value / below_buy_ratio / below_strength_base`를 `momentum_tag/threshold_profile`로 재분해하는 것이다.

3. `counterfactual` 보수형 추정 필요
   - 현재 missed winner 해석은 방향성 판단에는 유효하지만 절대 EV 해석에는 낙관 편향이 있다.
   - `optimistic / realistic / conservative` 3계층으로 올리는 게 맞다.

### B. 감사 후 채택할 의견

1. `AI 확정 후 strength/momentum 필터는 이중 검열일 수 있다`
   - 방향은 타당하다.
   - 다만 현재 OpenAI 실시간 입력에는 이미 `latest_strength`, `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct`가 들어간다.
   - 반면 `momentum_tag`, `threshold_profile`, `blocked_overbought`의 기준과 완전히 동일한 피처가 AI에 들어간다고 단정할 수는 없다.
   - 결론:
     - `즉시 필터 제거`는 금지
     - `AI 입력 피처 vs 상류 필터 중복 감사`를 먼저 수행

2. `partial fill이 구조적 음수 원인일 수 있다`
   - 타당하다.
   - 다만 현재 코드에는 partial/full fill 누적 처리와 preset TP 재발행 로직이 이미 있다.
   - 결론:
     - `기능 신규 구현`보다 `sync mismatch 관측/리포트`가 우선

3. `preset_exit_setup / ai_holding_review / hard_time_stop 충돌 가능성`
   - 점검 가설로는 타당하다.
   - 다만 `common hard time stop`은 현재 `shadow-only`다.
   - 결론:
     - live conflict로 단정하지 않고 `state machine 명문화 + shadow 영향 점검`으로 내린다.

4. `latency gate를 EV 조건부 강도 조절로 전환`
   - 설계 방향은 매우 좋다.
   - 다만 현재는 `원격 선행`, `quote_stale=False`, `한 축 canary` 원칙 아래에서만 진행해야 한다.

### C. 현 단계 부적합 또는 우선순위 하향 의견

1. `텔레그램 실시간 알림 연동이 필요하다`
   - 이미 `TELEGRAM_BROADCAST`, `buy_pause_guard`, `entry_metrics`가 동작 중이다.
   - 필요한 것은 새 채널이 아니라 `latency / partial fill / mismatch`의 구조화 데이터다.

2. `latency 원인을 내부 처리 지연/async/EC2 문제로 단정`
   - 현재 데이터는 `symptom`은 보여주지만 `root cause`는 고정하지 못한다.
   - 인프라/프로세스 분리 리팩터링은 `세부 이유 로그` 이후에 판단해야 한다.

3. `fallback 주문을 즉시 FOK로 교체`
   - 현재 구조는 `fallback_scout=IOC`, `fallback_main=DAY` 번들 설계다.
   - FOK로 바로 바꾸면 fill opportunity를 크게 줄여 EV 회수보다 기회 상실이 커질 수 있다.
   - 우선은 `partial fill sync`와 `min fill ratio` 계열 canary가 맞다.

4. `hard_time_stop이 AI를 구조적으로 무력화하므로 즉시 수정`
   - 현재 common hard time stop은 `shadow-only`다.
   - 실전 충돌보다 관측 항목이다.

## 4. 튜닝 전 점검 우선순위

### P0. 다음 로직 변경 전 반드시 확인

1. `latency_block` 상세 이유 분해
   - `quote_stale`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, slippage 허용치, 최종 decision reason
2. `expired_armed` 분리
   - TTL 만료와 latency 차단을 분리 집계
3. `partial fill sync mismatch` 검증
   - 실제 보유수량, preset exit 수량, ord_no 재발행, cancel ack 지연 여부
4. `AI 입력 피처 vs 상류 필터` 중복 감사
   - OpenAI 실시간 입력과 `dynamic strength / overbought` 차단의 중복 여부 확인
5. 원격 경량 프로파일링
   - `quote_stale=False` 코호트에서 표준 도구 기반으로 hot path를 관측
   - 단, 원인 단정이나 구조 리팩터링까지 바로 연결하지는 않음
6. `hard stop` taxonomy audit
   - `COMMON shadow-only`와 별개로 존재하는 live hard stop 계열(`preset/protect/scalp_hard_stop`)을 구분 정리

### P1. 감사 완료 후 바로 이어질 작업

1. `quote_stale=False` 원격 latency canary 고도화
2. `momentum_tag/threshold_profile`별 dynamic strength 교차표
3. `optimistic/realistic/conservative` counterfactual 추가
4. `fill quality` 복원 품질 보강

## 5. 매매로직 개선 우선순위

1. `Latency gate`를 EV-aware 강도 조절로 확장
   - 단, `quote_stale=True`는 계속 fail-closed
   - 적용은 원격만

2. `partial fill sync`를 리포트 가능한 상태로 만들기
   - 현재는 처리 로직이 있으므로 `mismatch=0`을 증명하는 쪽이 우선

3. `AI-필터 중복 감사` 후 selective 완화
   - 감사 전 필터 제거 금지

4. `dynamic strength` selective override
   - 전역 임계값 조정 금지

5. `counterfactual` 현실화
   - 분석 품질 개선이 다음 완화 판단의 전제

6. `청산 구조 명문화`
   - 실전 충돌 수정이 아니라 `우선순위 설명 가능 상태`로 정리

## 6. 보완된 운영 전략

- `원격서버(songstockscan)`:
  - `latency EV-aware degrade`
  - `dynamic strength selective override`
  - `latency 경량 프로파일링`
- `본서버`:
  - 현행 점검계획 유지
  - 로그/리포트 보강과 결과 검증만 수행
- 공통:
  - 실전 변경은 항상 `1축`, `shadow/canary`, `롤백 가드` 포함

## 7. 이번 비교검토로 플랜에 추가할 문서/산출물

1. `latency reason breakdown` 리포트
2. `partial fill sync mismatch` 리포트
3. `AI-필터 overlap audit` 리포트
4. `expert proposals not fit` 메모

## 8. 최종 결론

- 현재 플랜의 큰 축은 바꿀 필요가 없다.
- 다만 다음 로직 완화 전에 `latency 이유`, `partial fill 동기화`, `AI-필터 중복` 3가지를 먼저 감사해야 한다.
- 즉, 이번 비교검토의 결론은 `플랜 교체`가 아니라 `플랜 선행 조건 강화`다.

## 참고 문서

- [2026-04-10-stage2-todo-checklist.md](./2026-04-10-stage2-todo-checklist.md)
- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [2026-04-10-scalping-expert-proposals-not-fit.md](./2026-04-10-scalping-expert-proposals-not-fit.md)
- [2026-04-10-operator-message-validation.md](./2026-04-10-operator-message-validation.md)
