# Rising-missed 직접 paired 경제 튜닝 및 런타임 소비 개선 계획

작성일: 2026-09-19 KST

범위: `rising_missed_classifier_prior`의 구조 결손 제거, 비용 후 EV 탐색, 기존 TP1 selector의 조건부 정책 소비

권한: 계획 수립만 수행한다. 코드·정책·wrapper·schedule·산출물·런타임은 변경하지 않는다.

관련 owner: [Daily 튜닝 퇴역·runtime owner 분리 계획](./daily-threshold-cycle-tuning-retirement-and-runtime-owner-separation-plan-2026-09-19.md), [runtime approval 직접 증거 계획](./runtime-approval-summary-direct-evidence-handoff-optimization-plan-2026-09-19.md), [현행 장후 작업목록](../audit-reports/2026-09-05-postclose-work-inventory.md)

## 1. 결정

현행 `rising_missed_classifier_prior`를 source-signature별 승자·회피 손실 건수 집계기로 계속 미세 조정하지 않는다. 퇴역한 lifecycle bucket을 복구하지도 않는다. 기존 모듈 경로와 산출물 계열을 호환 표면으로 유지하면서 다음 세 역할을 명확히 분리한다.

1. `rising_missed_intraday_feedback`과 missed-entry counterfactual은 원천·진단 생산자로 유지한다.
2. `rising_missed_classifier_prior`는 같은 attempt에서 incumbent와 서로 다른 단일축 challenger를 비교하는 direct-family paired evaluator로 축소한다.
3. 검증된 비용 후 우위만 기존 `rising_missed_tp1` selector의 날짜별 정책으로 전달한다. 진단, gross first-hit proxy, 표본 증가만으로 장중 결정을 바꾸지 않는다.

최적화 목표는 `loss_filter` 수나 승률의 증가가 아니다. 동일 관측 모집단에서 비용 후 EV와 일별 순익을 동시에 개선하고, 하방·source quality·실행 가능성을 악화시키지 않는 정책을 찾는 것이다.

## 2. 현재 기준선과 최초 구조 결손

최신 산출물은 `data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_2026-09-16.json`이다.

| 항목 | 현재 값 | 판정 |
| --- | ---: | --- |
| prior | 31 | source-signature 건수 집계 |
| `positive_prior` / `recheck_prior` | 0 / 0 | EV 후보 없음 |
| `loss_filter` / `hold_sample` | 14 / 17 | 건수 분류이며 경제 우위 아님 |
| lifecycle source | 0 | 퇴역 owner이므로 시간 경과로 복구되지 않음 |
| 선택된 EV window | 0 / 31 | `window_metrics`가 비어 있음 |
| bounded probe 후보 | 2 | gross proxy이며 순EV 아님 |
| runtime effect / apply | false / false | 장중 직접 소비 없음 |

현재 `build_report()`는 `_merge_lifecycle_windows()`를 호출하지 않는다. 동시에 lifecycle bucket은 퇴역 필터 대상이다. 따라서 `source_quality_adjusted_ev_pct` 기반 `positive_prior`는 현행 경로에서 도달 불가능하다. `tuning_input_allowed=true`는 실제 source 결손과 독립적으로 고정되어 있고, JSON 파싱 실패는 빈 객체가 되어 정상 empty와 구분되지 않는다.

분류 순서도 경제 목표에 맞지 않는다. `counterfactual_avoided_loser_count > counterfactual_missed_winner_count`가 비용 후 EV보다 먼저 `loss_filter`를 결정한다. 손익 크기, 비용, 수량, 자본 점유, no-hit 청산을 사용하지 않으므로 이 결과로 EV 개선을 주장할 수 없다.

## 3. 보존·퇴역·금지 경계

### 보존

- clean tuning baseline `2026-06-05T00:00:00+09:00`
- `rising_missed_intraday_feedback`의 exact attempt/evaluation, TP1 결정 입력, source quality, blocker와 first-hit 관측
- missed-entry counterfactual의 candidate identity, venue/session, source signature, forward outcome와 명시적 simulation 권한
- 기존 TP1 selector의 lane, source readiness, hard-negative, quote freshness, downstream submit safety 및 주문 보호
- 실제 거래의 `COMPLETED + valid profit_rate`, broker 비용, fill·quantity·capital·custody 원장
- 기존 wrapper의 자원 대기·원자적 산출물 작성·strict handoff 계약

### 사용 중지

- 퇴역한 `lifecycle_bucket_discovery`, `lifecycle_decision_matrix`를 EV 원천으로 복원하는 경로
- `key_lineage_ledger`, `conversion_lane`를 경제성 완료 조건으로 사용하는 경로
- `missed_winner`와 `avoided_loser` 단순 건수로 정책 우위를 판정하는 경로
- 동일 정책 baseline/challenger, gross first-hit만 있는 후보, 구현 완료 workorder의 반복 생성

### 금지

- missing cost/outcome/no-hit을 0으로 대체
- counterfactual EV를 실제 실현 EV와 합산
- 1주 또는 가상 수량을 실제 일별 순익으로 환산
- hard safety, broker/order, quantity, cap, provider, cooldown, bot-state guard 완화
- 양수 결과를 만들기 위한 source 제외, holdout 재사용, 후보 재선택
- 새 shadow alpha 축, 새 daemon/service, 새 `src/engine` root module, 범용 optimizer 생성

## 4. 목표 producer → evaluator → policy → consumer 구조

```text
rising_missed runtime events
        ├─ rising_missed_intraday_feedback
        ├─ missed_entry_counterfactual
        └─ actual submit/fill/COMPLETED ledger
                         │
                         ▼
rising_missed_classifier_prior v2 compatibility owner
        ├─ source-quality and identity gate
        ├─ incumbent/challenger paired replay
        ├─ cost-adjusted EV and daily-net evaluation
        └─ edge / no-edge / maturity / structural disposition
                         │
              validated edge only
                         ▼
shared dated runtime policy/bootstrap owner
        (implementation prerequisite)
                         │
                         ▼
existing rising_missed_tp1 selector consumer
                         │
                         ▼
actual PID receipt → natural decisions → fills → COMPLETED post-apply EV
```

보고서 PASS, 정책 파일 생성, selected release, 실제 PID 소비, 자연 실행과 경제적 개선은 각각 별도 상태로 보고한다.

## 5. RM0 — 입력 동결과 exact identity

먼저 최신 선택 release와 실제 사용할 source date를 동결한다. 64MiB 이상이거나 쓰기 중인 JSONL은 `stat` 후 manifest/summary/streaming projection만 사용한다. 추가 REST 조회나 전체 보고서 재생성을 입력 확보 수단으로 사용하지 않는다.

paired row의 최소 identity는 다음과 같다.

- `target_date`
- `evaluation_attempt_id` 또는 `rising_missed_tp1_evaluation_id`
- symbol, venue, session
- decision timestamp와 effective price timestamp
- incumbent policy version/hash
- source packet hash
- terminal/outcome identity

retry/recheck는 같은 attempt의 최신 유효 terminal 하나로 보존하고 독립 표본으로 중복 집계하지 않는다. identity가 없거나 서로 다른 시점의 source를 결합해야 하는 행은 `source_gap`으로 제외한다.

Closure:

- 원천별 date, size, mtime, SHA256, schema와 authority가 산출물에 기록됨
- malformed, stale, changing source가 `tuning_input_allowed=false`로 차단됨
- valid empty, missing, parse failure, retired, future-due가 서로 다른 상태로 남음

## 6. RM1 — 직접 원천과 결과 계약

기존 report의 기본 입력을 살아 있는 direct-family 원천으로 한정한다.

| 증거 | 역할 | 허용 판정 |
| --- | --- | --- |
| TP1 selector decision packet | incumbent/challenger 입력 | 정책 재현, blocker attribution |
| missed-entry counterfactual | `sim_probe_ev` | source-only 기회비용·후보 탐색 |
| exact effective BBO/tick/minute outcome | counterfactual execution model | target/adverse/no-hit 결과 |
| actual submit/fill/terminal | 실행 품질 | 실제 적용 여부·fill/cost/capital |
| actual `COMPLETED + valid profit_rate` | `primary_ev` | 실제 비용 후 post-apply EV |

counterfactual 결과는 다음 세 상태를 모두 보존한다.

1. target-first 또는 adverse-first: 고정된 진입·청산 모델과 exact 비용이 있을 때만 비용 후 outcome 계산
2. no-hit: 20분 horizon의 executable exit bid 또는 계약상 정해진 exit price가 있을 때 계산
3. missing/truncated/held/custody-censored: EV를 null로 두고 원인과 owner 기록

확정된 no-trade baseline은 final no-submit과 capital-neutral이 같은 identity에서 확인될 때만 opportunity comparison의 0으로 사용할 수 있다. source가 없어서 거래 여부를 모르는 행을 0으로 바꾸지 않는다.

## 7. RM2 — 희소 signature 대신 계층형 비교 단위

현재 scanner token 전체 조합은 31개 prior로 빠르게 분할되어 표본을 소진한다. 기본 비교 key를 다음 안정 차원으로 제한한다.

1. venue + market session
2. TP1 candidate lane
3. TP1 candidate reason 또는 최초 blocker
4. promotion reason family
5. source-quality state

전체 `source_signature`는 진단 필드로 보존하되 기본 정책 key로 쓰지 않는다. 세부 key가 성숙하지 않으면 미리 고정한 순서로 상위 key에 합치며, 결과를 본 뒤 임의로 bucket을 재조합하지 않는다.

추천 계층은 `venue/session/lane/reason` → `venue/session/lane` → `venue/session`이다. symbol과 개별 scanner token은 leakage·과적합 점검용이며 기본 정책 분할에 사용하지 않는다.

## 8. RM3 — bounded candidate 생성

baseline은 source date에 실제 선택된 TP1 selector 정책이다. challenger는 기존 selector의 한 축만 변경한다. 최초 연구 범위는 다음 세 축으로 제한한다.

| 축 | 현재 기준 | offline 후보 | 제한 |
| --- | ---: | --- | --- |
| positive support family 수 | 2 | 1, 2, 3 | 한 번에 한 값만 비교; 1은 report-only 완화 후보 |
| spread caution ratio | 0.002 | 0.0015, 0.0020, 0.0025 | hard spread/order guard는 변경하지 않음 |
| chase recheck delta | 3.0% | 2.5%, 3.0%, 3.5% | recheck 조건만 비교; stale/price guard 유지 |

후보는 baseline + 단일축 challenger 최대 6개로 제한한다. lane eligibility, hard-negative evidence, input readiness, explicit venue/session, quote freshness, broker/order/quantity/cap/cooldown은 후보 축이 아니다.

동일 decision을 내는 후보는 `identical_policy`로 제외한다. source packet에서 재현할 수 없는 후보는 실행하지 않고 `unsupported_design`으로 남긴다. 후보 수를 늘리기 전에 최초 세 축의 distinct paired coverage를 확인한다.

## 9. RM4 — 비용 후 paired 경제평가

같은 attempt와 같은 source packet에서 baseline과 challenger를 모두 계산한다. 한쪽에만 유리한 행을 선택하지 않는다.

Primary metrics:

- `baseline_cost_adjusted_ev_pct`
- `challenger_cost_adjusted_ev_pct`
- `paired_delta_ev_pct`
- `baseline_daily_net_profit_krw`
- `challenger_daily_net_profit_krw`
- `paired_delta_daily_net_profit_krw`

Supporting metrics:

- paired sample, distinct day, full/partial/no-fill/no-trade/censored 수
- MFE, MAE, adverse-first, no-hit, worst-day와 loss-tail
- turnover, executed notional, capital occupancy
- source-quality exclusion과 exclusion sensitivity

비용은 같은 source packet에 결속된 broker-reconciled cost를 우선한다. counterfactual에 실제 비용이 없으면 현재 비교 비용 계약을 명시하고 `sim_probe_ev`로만 표시한다. 실제 수량과 자본 제약이 없으면 equal-weight EV까지만 계산하고 원화 일별 순익은 null로 둔다.

후보 순서는 다음 lexicographic 기준을 사용한다.

1. source·identity·cost·outcome 계약 유효
2. distinct paired comparison
3. `paired_delta_ev_pct > 0`
4. `paired_delta_daily_net_profit_krw > 0`
5. worst-day, MAE, adverse-first와 capital occupancy 비악화
6. 날짜별 방향 일관성과 독립 holdout 유지

승률, target-first 비율, gross payoff proxy는 동률 진단에만 사용한다.

## 10. RM5 — 탐색·고정·holdout 분리

표본 단계는 과도한 통계 framework를 새로 만들지 않고 세 단계로 제한한다.

| 단계 | 기본 최소치 | 허용 결과 |
| --- | --- | --- |
| diagnostic | 비용·결과 유효 paired 10건 | 구조·방향 진단만 |
| calibration | paired 30건, 거래일 3일 이상 | 단일 후보 고정 가능 |
| untouched holdout | paired 20건, 미사용 거래일 2일 이상 | promotion 검토 가능 |

위 숫자는 연구 착수와 후보 고정을 위한 최소치이며 양수 EV를 보장하지 않는다. 표본이 많아도 source-quality adjusted EV나 daily-net이 null이면 성숙으로 판정하지 않는다. 반대로 충분한 distinct paired 표본에서 음수이면 `measured_no_edge`로 닫고 표본 부족 상태로 되돌리지 않는다.

후보를 고정한 뒤 holdout 결과를 보고 threshold, bucket, exit horizon 또는 source 제외 규칙을 바꾸지 않는다. 바꿔야 한다면 새 revision과 새 unused holdout을 요구한다.

## 11. RM6 — 상태 모델과 시간 경과 판정

| 상태 | 의미 | 다음 동작 |
| --- | --- | --- |
| `structurally_blocked` | producer/identity/cost/outcome/consumer 부재 | 해당 owner 보완 전 실행 중지 |
| `insufficient_mature_sample` | 모든 계약은 유효하고 표본만 부족 | 다음 자연 거래일 누적 |
| `valid_empty` | 대상 attempt가 실제 0건 | 정책 유지, 재실행 반복 금지 |
| `measured_no_edge` | 유효 paired EV 또는 daily-net 비개선 | incumbent 유지, 후보 종료 |
| `validated_edge` | calibration·holdout·risk 조건 통과 | dated policy publication 검토 |
| `post_apply_pending` | 정책은 소비됐으나 실제 완료 성과 미성숙 | 자연 receipt와 COMPLETED 대기 |
| `retired_or_not_applicable` | 퇴역 source 또는 runtime 권한 없음 | 복구 task 생성 금지 |

현재 판정은 `structurally_blocked`다. 9월 17일 counterfactual 표본을 다시 읽으면 건수는 늘 수 있지만 direct paired cost/outcome과 정책 consumer가 없으므로 시간만으로 `validated_edge`가 되지 않는다.

## 12. RM7 — 정책 publication과 장중 consumer

`rising_missed_classifier_prior` JSON을 장중 코드가 직접 읽지 않는다. 검증된 단일 후보만 공유 날짜별 runtime policy/bootstrap에 `rising_missed_tp1_selector` family section으로 발행한다.

계획 수립 시점의 선택 배포본에는 `runtime_policy_bootstrap` 구현 파일이 없다. 따라서 구현 시작 시 다음 location gate를 먼저 수행한다.

1. 다른 승인 작업이 `src/engine/automation/runtime_policy_bootstrap.py`를 구현했으면 그 단일 owner를 재사용한다.
2. 아직 없다면 [Daily 튜닝 퇴역·runtime owner 분리 계획](./daily-threshold-cycle-tuning-retirement-and-runtime-owner-separation-plan-2026-09-19.md)의 location·authority 계약에 따라 공유 bootstrap을 먼저 구현하거나, 그 owner가 준비될 때까지 rising-missed runtime handoff를 `structurally_blocked`로 유지한다.
3. rising-missed 전용 bootstrap, service, daemon, env loader를 별도로 만들지 않는다. 기존 `threshold_cycle_preopen_apply`에 임시 우회 경로도 추가하지 않는다.

필수 policy 필드:

- source date, publication date, effective date
- baseline and challenger policy hash
- selected axis and before/after value
- calibration and holdout artifact/hash
- paired EV, daily-net, cost and risk disposition
- authority, apply scope, rollback value and trigger
- source-quality and exact consumer schema

장중 [rising_missed_candidate.py](../../src/engine/scalping/rising_missed_candidate.py)는 다음 PREOPEN에 검증된 dated policy만 읽는다. missing/stale/hash mismatch/unsupported axis이면 코드 baseline을 유지한다. 정책은 TP1 selector의 기존 bounded parameter만 바꾸며 downstream submit safety와 hard guard를 우회할 수 없다.

최초 canary는 한 venue/session cohort, 한 축, 한 policy version으로 제한한다. same-stage의 다른 canary나 operator override가 있으면 발행하지 않는다. 실제 주문 수를 만들기 위해 gate를 완화하지 않는다.

## 13. RM8 — post-apply 경제성 및 rollback

정책 적용 뒤 다음 항목을 같은 policy version과 actual PID receipt로 결속한다.

- eligible, allowed, deferred, blocked decision 수
- submit intent, broker dispatch, full/partial/no-fill
- 실제 quantity, notional, fee, tax, slippage
- COMPLETED + valid profit_rate
- 일별 순익, EV, downside, capital occupancy

실제 post-apply 평가는 counterfactual과 분리한다. 자연 완료 표본이 부족하면 `post_apply_pending`이며 deployment 성공을 EV 개선으로 바꾸지 않는다.

Rollback은 기존 값으로의 원자적 복귀만 허용한다. source stale/hash conflict, hard-safety incident, 비용 후 누적 delta의 음수 전환, worst-day/tail 악화 또는 consumer contract failure가 발생하면 canary를 중지하고 incumbent를 복원한다. 수동 env 변경이나 장중 hot reload 대신 기존 다음 PREOPEN 정책 경계를 사용한다.

## 14. RM9 — wrapper와 workorder 정리

구현 완료 전에는 `rising_missed_classifier_prior`를 main postclose 필수 단계로 취급하지 않는다. 현재 main wrapper의 설치 schedule가 없다는 사실과 wrapper 내부 기본값을 구분한다.

구현 시 다음을 함께 정리한다.

1. dead lifecycle/key-lineage/conversion 입력 제거
2. `tuning_input_allowed`의 fail-closed 계산
3. parse/missing/empty/stale 상태 분리와 source hash 기록
4. 이미 `implemented`인 bridge workorder 반복 생성 제거
5. direct evaluator가 활성화될 경우에만 feedback/counterfactual 이후, runtime summary 이전에 조건부 실행
6. source date가 없거나 valid empty이면 빠르게 종료하고 동일 입력 재실행 금지

자동 장후 chain에 다시 넣는 조건은 paired evaluator, dated publisher, strict consumer verification이 모두 구현되고 targeted validation을 통과한 뒤다. 그 전에는 명시적 수동 분석만 허용한다.

## 15. 수정 위치와 최소 구현 범위

새 report family나 root module을 만들지 않는다.

| 역할 | 기존 파일 |
| --- | --- |
| direct paired evaluator·JSON/Markdown | `src/engine/monitoring/rising_missed_classifier_prior.py` |
| 원천 필드가 실제로 누락된 경우만 생산자 보완 | `src/engine/monitoring/rising_missed_intraday_feedback.py` |
| bounded TP1 policy consumer | `src/engine/scalping/rising_missed_candidate.py` |
| dated policy 합성 | 공유 `src/engine/automation/runtime_policy_bootstrap.py`; 구현 시작 시 존재 여부를 확인하는 선행 조건 |
| final source/policy/consumer receipt | `runtime_approval_summary`와 direct verifier |
| 실행 순서 | `deploy/run_threshold_cycle_postclose.sh` |
| 회귀 | 기존 rising-missed, wrapper, PREOPEN/runtime policy 테스트 |

원천 필드가 이미 존재하면 producer를 수정하지 않는다. evaluator에서 필요한 projection만 읽는다. 대용량 pipeline event를 매 후보마다 다시 순회하지 않고 한 번의 bounded projection과 attempt index를 모든 후보가 공유한다.

## 16. 성능 범위

- source read 1회, identity index 1회, baseline replay 1회
- 단일축 challenger 최대 6개
- 세부 signature 전수 조합 탐색 금지
- 동일 source packet과 outcome cache 재사용
- 새 입력이나 producer 수리가 없으면 unchanged replay 중지
- 실행 시간이 길면 후보·세부 진단을 줄이고 pending으로 남긴다. 비용, outcome, holdout, source-quality gate를 줄이지 않는다.

성능 목표는 현재 source 크기에서 bounded하게 끝나는 것이다. 별도 wall-clock guard, daemon, checkpoint framework를 추가하지 않는다.

## 17. 구현·리뷰·검증 순서

1. RM0 exact source와 selected release 동결
2. source loader fail-closed 및 provenance 보완
3. direct paired row와 cost/no-hit/censor 계약 구현
4. 단일축 candidate replay와 distinct/self-comparison 검증
5. EV·daily-net·tail disposition 구현
6. calibration/holdout candidate freeze 구현
7. dated policy publisher와 existing TP1 consumer 연결
8. wrapper 조건부 단계·summary·strict verifier 연결
9. self review → 수정 → 재리뷰
10. targeted tests·compile·wrapper 검증·`git diff --check`
11. 허용된 source date에만 bounded regeneration
12. 별도 승인된 immutable release, 다음 정상 PREOPEN, PID와 post-apply 확인

필수 회귀:

- retired lifecycle source가 있어도 tuning 입력으로 사용하지 않음
- malformed/missing/stale/changing source fail-closed
- identical policy가 improvement로 집계되지 않음
- retry·recheck 중복 제거와 attempt identity 보존
- actual, sim, counterfactual, probe와 full/partial/no-fill/censored 분리
- no-hit exit와 exact cost 부재 시 EV null
- 비용 후 EV 양수·daily-net 음수 후보 승격 거절
- holdout 재사용·후보 재선택 검출
- 정책 없음/stale/hash mismatch 시 runtime baseline 유지
- source-only artifact가 iteration priority·BUY 권한을 바꾸지 않음
- hard safety 및 downstream submit guard 보존

검증 명령은 영향 범위의 pytest, Python compile/import, wrapper 변경 시 `bash -n`과 wrapper contract tests, `git diff --check`를 사용한다. 문서 변경은 link/owner/authority와 print-only backlog parser를 검증한다. Provider 호출, 주문, 봇 재기동, Project/Calendar sync는 수행하지 않는다.

## 18. Acceptance

### A. 구조 종결

- `window_metrics` dead path와 퇴역 source 의존이 제거됨
- 모든 source가 date/schema/hash/authority와 결속되고 `tuning_input_allowed`가 fail-closed임
- 건수 기반 `loss_filter`가 primary EV 판정을 대신하지 않음
- 반복되는 implemented bridge workorder가 사라짐

### B. 경제 증거

- baseline과 distinct challenger가 같은 attempt에서 paired됨
- 비용·no-hit·수량·자본의 가용성과 null 이유가 명시됨
- EV, 일별 순익, tail이 actual/sim/CF별로 분리됨
- 개선이 없으면 `measured_no_edge`, 구조 결손이면 `structurally_blocked`, 표본만 부족하면 `insufficient_mature_sample`로 종결됨

### C. 런타임 전달

- validated edge만 dated policy로 발행됨
- PREOPEN source/policy/consumer hash와 selected release가 일치함
- 실제 PID 소비와 자연 TP1 decision receipt가 확인됨
- missing/stale/conflict에서 incumbent가 유지되고 hard safety가 보존됨

### D. 실제 성과

- 적용 version의 actual full/partial fill과 COMPLETED 비용 결과가 분리 집계됨
- post-apply cost-adjusted EV와 일별 순익이 incumbent 대비 개선됨
- 성숙 전에는 `post_apply_pending`이며 코드·배포 완료를 경제성 완료로 표시하지 않음

## 19. 예상 결과와 중단 조건

첫 bounded 실행에서 가능한 결론은 세 가지다.

1. 유효 paired 비교가 없으면 최초 source/identity/cost/outcome 결손 하나를 구조 수리 대상으로 확정한다.
2. 비교가 유효하지만 EV 또는 일별 순익이 개선되지 않으면 incumbent를 유지하고 해당 후보를 `measured_no_edge`로 닫는다.
3. calibration과 untouched holdout에서 EV·daily-net·tail 조건을 모두 통과하면 단일 dated canary 후보만 전달한다.

양수 후보가 없다고 threshold 탐색 범위를 자동 확장하지 않는다. 세 축이 모두 no-edge이면 이 family의 적극적 장후 튜닝을 종료하고 intraday feedback을 진단 원천으로만 유지한다. 이 중단 조건이 불필요한 반복 재실행과 과적합을 막는 최종 성능 최적화다.

## 20. 이번 계획 범위

이 절은 계획 수립 당시의 범위다. 당시에는 코드, 테스트, wrapper, schedule, policy, runtime selector, 산출물을 변경하거나 재실행하지 않았다. 승인 뒤 수행한 구현 결과는 다음 절에 기록하며, immutable deployment, 정상 PREOPEN/PID 소비, 자연 체결과 비용 후 EV 개선은 계속 별도로 검증한다.

## 21. 2026-09-19 구현 결과

RM0–RM9의 코드 경로를 기존 owner 안에서 구현했다. `rising_missed_classifier_prior`는 퇴역 lifecycle·key-lineage·conversion 입력과 건수 기반 primary 판정, 완료된 bridge workorder 반복 생성을 제거하고 최근 최대 20개 feedback의 exact evaluation ID를 직접 비교한다. producer는 이후 생성분부터 각 horizon의 마지막 실행가능 bid 시각·수익률·source를 기록한다. 과거 `no_hit` 중 이 필드가 없는 행은 0으로 바꾸지 않고 censored다.

source 20일에서 2,861개 paired 행을 구성했다. 인과적으로 결정 변화가 확인된 후보는 `positive_support_min 2→1` 한 개였고 342건이었다. 비용 후 calibration은 252건/12일, EV `-0.76333333%`; untouched holdout은 50건/4일, EV `-0.85%`; 100만원 고정 모형 holdout 일평균은 `-106,250원`, 최악일은 `-296,200원`이다. 따라서 상태는 `measured_no_edge`다. `positive_support_min=3`, spread 두 값, chase 두 값은 관측된 차단 population에서 결정 변화가 없어 `identical_policy`로 제외했다.

effective date `2026-09-21`에는 challenger를 발행하지 않고 `incumbent_preserved` receipt를 생성한다. 이 receipt의 runtime env override는 비어 있어 기존 임계값과 주문 권한을 바꾸지 않는다. validated edge가 생긴 경우에만 allowlist와 범위 검증을 통과한 단일축 값을 shared bootstrap이 기존 TP1 selector에 전달한다. 실제 PID 소비, 자연 TP1 decision, fill, `COMPLETED + valid profit_rate`와 비용 후 post-apply EV는 다음 정상 PREOPEN 이후 확인할 별도 acceptance이며 이 구현 결과에 포함하지 않는다.

배포 전 PREOPEN 사전 조립에서 9월 18일 legacy manifest의 선택 family·dated override 검증 실패 수는 모두 0이지만 퇴역 공통 handoff의 `runtime_env_handoff_missing` 때문에 전체 verify만 fail인 cutover 결함을 발견했다. shared bootstrap은 이 정확한 legacy 상태에서만 최초 incumbent seed를 허용하도록 보완했다. 허용 finding은 미선택 `integrated_entry_axis_bundle`의 기존 세 handoff finding으로 제한하며, active runtime policy 실패·미검증 selected family·missing family·dated override 실패가 하나라도 있으면 기존대로 fail-closed다.

9월 17일 raw pipeline은 약 5.71GB다. 이미 성숙한 target/adverse 비교가 명확한 음수인 상태에서 과거 censored `no_hit` 40건을 채우기 위해 전체 raw를 재주사하지 않는다. 이는 계산 생략으로 양수 결론을 만드는 조치가 아니라, 결손 행을 계속 제외하고 향후 자연 producer에서 계약을 닫는 선택이다.
