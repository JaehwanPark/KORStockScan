# 2026-09-16 장중 후속 작업지시문

작성 기준: `2026-09-16 07:24 KST`

## 1. 목적과 범위

9월 15일 장후 체인은 terminal로 종료됐지만 strict verifier와 final detector는 warning이었다. 오늘은 전일 source date와 당일 effective date를 분리한 상태에서 다음 항목을 장중 자연 실행으로 확인한다.

1. 07:32 exact-date 소유권 정책, 07:35 PREOPEN, 07:55 main PID가 모두 `2026-09-16`을 소비하는지 확인한다.
2. 공통 main release, 위젯·episode 공통 release와 위젯 trader override가 실제 PID까지 일치하는지 확인한다.
3. 전일 submit drought의 `exact_attempt_source_quality_gap`이 오늘 같은 attempt의 정상 submit 경로에서 재현되는지 확인한다.
4. 위젯·episode의 신호, micro 확인, submit/fill, target/보조익절, terminal/custody를 분리해 확인한다.
5. 전일 safe quarantine과 source-only warning을 성공이나 runtime 결함으로 바꾸지 않고 오늘 자연 원천으로 재판정한다.

이 문서는 오늘 점검 순서와 판정 기준이다. 실주문, 수동 env·operator lock·threshold·provider·수량·target·safety 변경, 매매 process 재기동 권한을 추가하지 않는다. 결함이 확인되면 [장중 모니터링 지시문](../intraday-monitoring-task-instructions.md)의 권한과 review gate를 따른다.

## 2. 기준 상태

| 구분 | 기준 |
| --- | --- |
| 전일 source date | `2026-09-15` |
| 당일 target/effective date | `2026-09-16` |
| 공통 postclose/PREOPEN/main | `916c675fcf9e42073f241989dd9d9fd62b0e506e` |
| 위젯·episode 공통 service | `eed1b63a236413c65a100ec319a1e9133f48da71` |
| 위젯 trader override | `abffdecf7a41fce96c77586f0be5ece2dc22a09f` |
| 2-pass | intake 75, 요청 20, 구현 검증 11, evidence 차단 9, actionable open 0, 미분류 0 |
| 전일 terminal | main `23:11:21`, strict warning `01:18:01`, final detector warning `01:23:58` |

기준 artifact는 [release audit](/home/ubuntu/KORStockScan/data/runtime/runtime_release_audit_2026-09-16.json), [postclose verifier](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-15.json), [2-pass 리뷰](../audit-reports/2026-09-15-implement-now-widget-episode-two-pass-review.md)다.

## 3. 시간순 필수 작업

### 3.1 07:24~07:31 사전 고정

- `data/runtime/runtime_release_selection.json`의 root/commit과 `preopen 2026-09-16 --print-plan`, `start 2026-09-16 --print-plan`을 대사한다.
- `korstockscan-symbol-owner-policy-auto-apply.timer`가 `07:32 active/waiting`인지 확인한다.
- 위젯 trader, collector 3개와 fill notifier의 현재 PID·WorkingDirectory·ExecStart를 기록한다.
- 이전 날짜 low-price preflight `failed` 3건은 원래 `exit 4`와 quarantine reason을 보존한다. `reset-failed`, 조기 실행 또는 수동 policy 적용을 하지 않는다.

판정은 `ready_for_natural_boundary | route_mismatch | timer_missing | deployment_route_blocked` 중 하나다.

### 3.2 07:32 소유권 정책 경계

Owner는 `korstockscan-symbol-owner-policy-auto-apply.timer`이며 기존 `[EntryAxesClosedLoopPreopen0916]` handoff에 결속한다.

다음을 모두 확인한다.

1. service `Result=success`, 실행 target date `2026-09-16`.
2. `symbol_owner_policy_2026-09-16.json`, request, receipt, auto-apply 결과가 같은 policy ID/hash를 사용한다.
3. `owner_custody.env`가 9월 16일 policy를 가리킨다.
4. broker KRX·NXT 잔고/미체결과 owner registry 보존식이 통과한다.
5. wrapper가 당시 active였던 위젯·episode 주문 service만 정지·복원했으며 새 PID가 같은 검증 코드와 정책을 소비한다.
6. 제외된 symbol은 직접 blocker가 있고 다른 symbol의 정상 정책을 차단하지 않는다.

실패 시 전일 env를 복사하거나 수동 파일을 작성하지 않는다. 해당 widget/episode entry scope는 fail-closed로 두고 `owner_policy_apply_failed | custody_mismatch | service_restore_failed | policy_date_mismatch`를 직접 원인으로 기록한다.

### 3.3 07:35 PREOPEN

- 공통 runner가 `916c675f`, target date `2026-09-16`으로 실행됐는지 확인한다.
- apply plan, runtime env, verify가 `source_date=2026-09-15`, `target_date=2026-09-16`으로 연결되는지 확인한다.
- selected family, dated policy, prompt/bundle과 operator override를 각각 확인한다.
- 후보 block은 baseline/fallback 또는 정확한 차단으로 보존한다. 전일 후보를 강제 선택하지 않는다.
- PREOPEN exit 0만 보지 말고 status artifact, verify findings, policy/source hash와 07:55 intended consumer까지 연결한다.

판정은 `preopen_pass | partial_with_blocked_families | policy_rejected | preopen_failed`로 기록한다.

### 3.4 07:55~08:05 main 실제 기동

- 실제 PID의 cwd, commit, launcher, `PROJECT_DIR/PYTHONPATH/VENV_PY`가 `916c675f`와 일치하는지 확인한다.
- 9월 16일 runtime env·prompt·policy·market weakness bundle의 실제 PID 소비 receipt를 확인한다.
- broker/custody owner, WS login/REG와 첫 0B/0D, AI 첫 request/response를 분리한다.
- 중복 PID, restart loop, 전일 lock의 실제 점유가 없는지 확인한다.

PID가 없거나 다른 root이면 PREOPEN PASS로 대신하지 않는다. `startup_failed | pid_release_mismatch | policy_not_consumed | ws_first_data_missing` 중 최초 원인을 고정한다.

### 3.5 08:05~09:20 위젯·episode release와 자연 정책 소비

- 위젯 trader는 `abffdecf`, collector 3개와 fill notifier는 `eed1b63a`를 실제 PID가 소비해야 한다.
- 보조익절, 주문직전 악화보류, 목표가 상향 policy path/hash가 startup pin과 일치해야 한다.
- Telegram은 BUY/SELL 체결에만 발생하고 관찰 신호, 표본 수집, 거절·미전송 주문에는 발생하지 않는지 확인한다.
- signal → market weakness/global safety → owner/episode lock → submit/fill → target/보조익절 → terminal/custody를 같은 owner·symbol·policy hash로 결속한다.
- 자연 진입이 없으면 `on_no_natural_sample`이다. 신호를 만들기 위한 guard 완화나 수동 주문을 하지 않는다.

08:05 이후 설치 root와 PID root가 다르면 `unit_process_release_mismatch` incident로 처리한다.

### 3.6 09:05 및 13:10 low-price quarantine 재판정

| 시각 | Profile | 전일 직접 사유 |
| --- | --- | --- |
| 09:05 | `cj_cgv_morning` | `research_half_robustness_review_requires_new_profile_revision` |
| 13:10 | `sk_telecom_midday` | `research_economics_nonpositive_under_current_cost` |
| 13:10 | `youngone_midday` | `research_half_robustness_review_requires_new_profile_revision` |

- 당일 timer의 새 preflight receipt와 target date를 확인한다.
- 같은 blocker가 유지되면 정상 safe quarantine이다.
- 통과했으면 exact-date policy/hash, profile readiness, owner/custody와 live service의 후행 시작을 확인한다.
- 전일 `failed` unit 상태를 지우는 것으로 오늘 성공을 만들지 않는다.

### 3.7 09:05~09:20 main runtime provenance

현재 체크리스트 `[RuntimeEnvIntradayObserve0916]`을 수행한다.

- PREOPEN selected family와 실제 PID의 runtime event provenance를 연결한다.
- carry-forward, 새 ON, 정책 갱신, OFF/제외를 구분한다.
- rollback guard, hard safety, operator override를 확인한다.
- policy 존재만으로 효과를 인정하지 않고 첫 자연 평가와 action을 확인한다.

### 3.8 장중 submit drought 확인

전일 canonical handoff는 PASS였지만 root cause는 `source_quality_blocked: exact_attempt_source_quality_gap`이었다. 오늘은 정상 submit-path 가설을 다음 순서로 확인한다.

`scanner promotion → AI request/response → trusted action → latency/price revalidation → final authority → broker receipt`

- 같은 attempt ID에서 최초 terminal과 pending/submitted 보존식을 확인한다.
- source 필드 결손과 정상 WAIT/DROP/BLOCK을 분리한다.
- accepted submit, broker receipt, fill과 terminal을 별도로 기록한다.
- 한 건 submit 또는 경보 해제를 drought 해소로 확정하지 않는다.
- 실제 submit 회복과 비용 차감 순이익은 독립 판정한다.

`SUBMIT_DROUGHT_CRITICAL`만으로 봇을 재기동하거나 threshold·stale/price guard를 완화하지 않는다.

### 3.9 위젯·episode 진입·청산 품질 확인

전일 timing 상태는 `baseline_immediate`, `terminal_or_right_censored_gap`, `blocked_missing_evidence`였다.

- 원 신호/확인 횟수와 signal 이후 micro 0/1/3/5초를 분리한다.
- 실제 submit/full·partial fill/미체결, HELD/terminal과 비용을 이어 붙인다.
- `machine_confirmation_fixed_price_window_v1`의 window completeness와 실제 PID adapter 소비를 확인한다.
- 보조익절은 정체 조건 전환과 목표가 1호가 상향을 구분한다. 원 주문 취소확정, successor 주문, TTL/부분체결 복원과 수량 보존을 확인한다.
- 자연 표본이 없거나 terminal pair가 없으면 evidence gap으로 남긴다. 양수 EV나 주문 건수를 만들기 위한 target·entry guard 변경을 하지 않는다.

### 3.10 09:35~09:50 sim/probe, 14:20~14:35 source-quality

- `[SimProbeIntradayCoverage0916]`: `actual_order_submitted=false`와 real/sim/probe 분리를 확인한다.
- `[IntradaySourceQualityGateCheck0916]`: 최신 source audit를 실행 또는 확인하고 hard gap, excluded row/window, unknown warning을 기록한다.
- identifiable 결손은 해당 row/window만 제외한다. 전체 날짜 차단은 preflight invalid, 격리 실패 또는 고용량 비식별 결손에 한정한다.
- 전일 Pattern Lab warning은 새 concrete workorder가 생길 때만 구현 재판정한다.

## 4. 전일 2-pass 차단 항목 취급

- 검증된 기존 구현 11건은 새 runtime defect 또는 consumer failure가 없으면 재구현하지 않는다.
- evidence 차단 9건은 오늘 자연 원천을 수집하는 항목이다. `eligible_actionable_open=0`을 임의 코드 작업으로 바꾸지 않는다.
- prompt revision은 exact 비용 parent가 materialize되고 기존 bounded offline consumer가 이를 읽을 때만 재판정한다.
- Pattern Lab 관련 항목은 fresh currentness/AI review가 stable native ID와 구현 위치·consumer·acceptance를 발급할 때만 구현 대상으로 올린다.

## 5. 장애 처리 우선순위

1. broker/custody·중복주문·잘못된 owner 같은 안전 결함
2. 07:32 policy/date/PID 또는 07:35/07:55 release 경계 결함
3. source writer·WS·schema·identity 결함
4. submit drought exact-attempt 결손
5. 위젯·episode 신호/micro/terminal pair 결손
6. source-only warning과 경제성 미성숙

실패 시 `증거 보존 → 최초 원인 → 최소 수정 → review/fix 반복 → targeted validation → 직접 consumer` 순서를 지킨다. 배포·재기동은 현재 요청에 포함되지 않는다.

## 6. 완료 조건과 보고

오늘 장중 점검은 다음을 모두 설명해야 한다.

- 07:32 policy, 07:35 PREOPEN, 07:55 PID의 날짜·release·hash·consumer
- main/widget/episode 각 PID와 owner/custody·WS 첫 소비
- submit drought의 같은 attempt 최초 병목과 실제 submit/fill 여부
- 위젯·episode의 signal/micro/submit/fill/target/terminal·비용 분모
- low-price 3건의 당일 preflight 결과와 safe quarantine 또는 정상 후행 시작
- source-quality audit와 제외 row/window, 남은 evidence blocker

보고 순서는 `판정 → 직접 근거 → 조치 → 다음 확인 시각`이다. 상태는 `not_yet_due | waiting | running | done | done_warning | failed`로 기록한다. 코드 구현, 배포, PID 소비, 자연 action, 주문, 비용 차감 경제성을 각각 별도 상태로 유지한다.
