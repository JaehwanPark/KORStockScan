# Latency recommendation 폐기·진단 통합 최종 리뷰 — 2026-09-06

## 1. 최종 판정

- 독립 `latency_classifier_recommendation`은 목적을 달성하지 못하는 중복 장후 작업이므로 `latency_recommendation_retirement_20260906`으로 폐기했다. scheduled producer, PREOPEN loader/candidate, AI review 예외와 current approval 승격 경로가 모두 제거됐다.
- 실제 runtime `LatencyMonitor`와 `EntryPolicy`, `latency_block`/`latency_pass`, quote freshness와 DANGER/stale/broker 차단은 유지한다. `SAFE`와 `CAUTION`은 기존처럼 slippage 검사 뒤 normal submit으로 진행한다.
- latency/freshness의 사후 기회 분석은 BUY Funnel, performance tuning, daily threshold report의 `diagnostic_only`로 통합했다. 표본 수와 양의 사후 수익이 커져도 독립 threshold 후보나 code-improvement candidate로 승격하지 않는다.
- 별도 `latency_spread_relief_real_operator_override`는 이번 폐기 대상이 아니다. 현재 exact-date PREOPEN 환경의 fresh spread-only operator lock과 기존 rollback/safety 계약을 그대로 유지했으며 값·주문·provider·bot을 변경하지 않았다.

## 2. 목적·기대효과·기존 조건 재평가

- 구 목적은 관측된 latency 분포와 counterfactual을 이용해 다음 PREOPEN의 latency 경계값을 추천하는 것이었다. 그러나 runtime은 이미 단순화돼 CAUTION과 SAFE가 같은 submit 의미를 가졌고 report 자체도 `eligible=false`를 영구 출력해 실제 자동 적용 가능성이 없었다.
- 2026-09-04 artifact는 270행/63 unique attempt였으나 recovery와 유효 counterfactual이 0건이고 RTT 재현도 없었다. 선택된 CAUTION age가 59 ms로 SAFE age 250 ms보다 엄격해 의미가 역전됐으며, counterfactual은 비용 차감 순이익이 아닌 gross 관측이었다.
- clean baseline 이후 64개 historical artifact에서 apply 허용·bounded candidate·recovery evidence가 모두 0건이었다. 따라서 표본·EV 조건을 완화해 경로를 살리는 것보다 중복 권한을 제거하고 실제 safety/submit funnel 계측을 보존하는 편이 목적과 기대효과에 부합한다.
- 기대효과는 죽은 후보 대기·AI 예외·PREOPEN 재활성화 위험과 중복 장후 비용의 제거, 그리고 submit drought 원인을 latency/freshness/hard safety와 실제 경제성으로 일관되게 분리하는 것이다. 이 작업 자체를 수익 개선 증거로 해석하지 않는다.

## 3. 구현 및 재활성화 방지

1. 공통 retirement 계약에 report와 calibration family를 등록했다. runtime telemetry family는 broad retired family로 넣지 않아 안전 계측을 보존했다.
2. postclose wrapper에서 producer 명령을 제거하고 상태 marker를 영구 `false`로 고정했다. producer 모듈과 전용 테스트는 삭제했고 engine-root allowlist도 정리했다.
3. PREOPEN에서 report loader를 제거하고 historical primary/separate artifact에 악성 `allowed_runtime_apply=true` candidate가 남아도 selection/env override가 생성되지 않게 했다. 동일 폐기 family의 오래된 operator lock도 합성 candidate로 복원되지 않는다.
4. threshold EV, daily report, runtime approval summary는 historical recommendation을 읽지 않는다. 실제 latency pass/block 성과만 diagnostic owner로 표시하며 recommendation/runtime apply는 `retired`, `false`로 고정한다.
5. verifier의 AI exemption을 제거했다. stale historical selected family도 current runtime selection 수에 포함하지 않는다.
6. one-share의 `latency_or_freshness`를 BUY Funnel hard-safety attribution으로 통합하고 diagnostic-only 그룹으로 고정했다. 3건 이상의 양의 결과가 있어도 threshold opportunity/workorder로 승격되지 않는 반례 테스트를 추가했다.

## 4. 코드리뷰와 검증

- 1차 리뷰 finding: one-share first-blocker 경로가 latency/freshness를 기존-family 개선 후보로 다시 만들 수 있었다. diagnostic-only allowlist와 workorder 이중 방어를 추가하고 양의 표본 floor 반례로 닫았다.
- 2차 리뷰 finding: report candidate는 제거됐지만 동일 family의 stale operator lock이 합성 candidate를 만들 수 있었다. retired calibration family를 lock 보존보다 먼저 거부하고 force-emit 대상에서도 제거했으며 악성 lock 반례로 닫았다.
- historical report의 primary calibration list, 별도 report와 stale operator lock이 동시에 악성 candidate를 포함하는 경우를 재현했고 PREOPEN runtime 변경·env key·selected family가 모두 생성되지 않음을 확인했다.
- producer/report/approval/one-share/location 회귀: **318 PASS**.
- PREOPEN/verifier/wrapper 회귀: **510 PASS**.
- `LatencyMonitor`, entry latency, pipeline event, source-quality와 backfill 회귀: **420 PASS**, 외부 `pandas_ta` deprecation warning 1건만 존재한다.
- 합계 **1,248 PASS**. 변경 Python Black/Ruff, compile, wrapper `bash -n`, 문서 parser와 `git diff --check`를 최종 gate에서 확인했다.
- 최종 self-review의 이 범위 미해결 finding은 **0건**이다. bot restart, report 대량 재생성, 실주문, threshold/operator-lock 값, provider, quantity/cap과 hard safety 변경은 수행하지 않았다.

## 5. 런타임 적용 가능성과 남은 자연 확인

- 폐기 적용은 코드와 예약 wrapper에 자동 반영된다. 다음 postclose에서 사용자가 개입하지 않아도 독립 producer가 실행되지 않으며, 다음 PREOPEN은 과거 artifact를 candidate로 읽지 않는다.
- 현재 `threshold_runtime_env_2026-09-07.json`을 읽기 전용으로 대조한 결과 selected family에는 `latency_classifier_runtime_profile`이 없고 `latency_spread_relief_real_operator_override`만 별도 owner로 존재했다. 이는 새 코드의 실제 PID 소비 증거가 아니라 장전 파일의 권한 분리 확인이다.
- 실제 정상 기동 PID에서 DANGER/stale/broker 차단과 `latency_block/pass`가 계속 기록되는지, 다음 postclose marker가 recommendation `false`인지, PREOPEN selected family에 폐기 family가 없는지는 2026-09-07 자연 실행에서 확인한다.
- 현재 exact-date env의 `latency_spread_relief_real_operator_override`는 별도 owner다. 이를 폐기 family로 오인해 제거하거나 recommendation 폐기를 근거로 spread/safety 경계를 완화하지 않는다.
- 자연 latency 대상 0건은 `not_observed`이며 성공·실패 또는 threshold 변경 근거가 아니다. 자연 증거가 생길 때까지 기존 안전 계측과 BUY Funnel 진단만 계속한다.
