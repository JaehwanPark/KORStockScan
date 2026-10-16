# 최초 매수 수량 런타임·장후 결과 및 생산자/소비자 점검

점검일: 2026-10-17 KST. 원천일: 2026-10-16, 수량 갱신 창: 2026-09-29 이후.

## 1 판정과 범위

**정책 소비와 자연 수량 생산은 확인했다. 장후 수량 튜닝은 원천 결손으로 비교 불가이며, 최신 선택 코드에서 소비자 결함 3개를 확인했다. 단순한 자연소비 부재나 통계 표본 부족으로 설명할 수 없다.** 부모 정책 유지는 적절하나 `valid_empty`/lineage `ready`를 전체 연결 정상으로 해석하면 안 된다.

- 읽기 전용 결과 점검이다. 운영 코드·DB·정책·서비스·주문을 변경하거나 장후 재생을 실행하지 않았다. 아래 재현은 선택 릴리스의 읽기 전용 함수와 메모리 내 대조 입력을 사용했다.
- 적용 원칙: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [장후 결과 점검의 권한·판정](../postclose-tuning-result-review-task-instructions.md), [수량 상세계획](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md), [의미 감시 현행화 C08/C09/C14](../proposals/semantic-monitor-producer-consumer-currentization-plan-2026-10-16.md).
- 10/17 일일 체크리스트는 없다. 10/16 자료는 역사적 실행 근거로 읽었으며 오늘의 실행 owner로 대체하지 않았다. 10/19에는 기존 `DirectFamilyPreopenPolicyHandoff`가 있으나 새 코드 결함의 수리 완료를 뜻하지 않는다.
- 10/11 구현·성능·배포 완료 기록은 당시 범위로 유지한다. 이번에 확인한 새 연결 결함만 별도 후속 대상으로 기록한다.

## 2 선택 정책·실제 소비

| 구간 | 확인 결과 |
| --- | --- |
| 선택 릴리스 | `postclose-semantic-consumers-20261017-68be02a77`, commit `68be02a77c5bc02c71d985643d8eed9b451ed4c2`. selector의 승인 범위는 `after_postclose_deploy_for_next_regular_start`, 다음 운영일 10/19, `actual_pid_consumed=false`. |
| 현재 Main | 점검 시 Main 프로세스를 관측하지 못했다. 새 릴리스의 기동·소비 완료로 표시하지 않는다. |
| 수량 정책 | `initial-quantity-runtime-v2-a247aca92079`, file SHA `ba72d720a4c11dbcfd18a667d2f47a648c0e7b792fe9a3edbb7193f674870cca`. 6유형 모두 `parent_5stage / parent / existing_runtime_profile`. 기존 10/15/20/25/25% 단계·분할·프로필 시간 계승이며 새 유형별 cap/형상/T 선정은 없다. |
| loader | 선택 릴리스의 `selected_initial_quantity_env(current, '2026-10-19')` 검증 성공. 정책의 과거 effective date 때문에 차단되지 않는다. 실제 10/19 PREOPEN/PID 증거와 구분한다. |
| 10/16 PID 소비 | 수량 archive 21개 검증 영수증. 마지막 bootstrap 검증 PID `389707`, `19:53:53+09:00`, 동일 수량 SHA. 이는 10/16 당시 PID의 소비 증거다. |
| 자연 수량 결정 | 검증된 실행 partition에서 sizing 이벤트 9개: 발행된 plan 8개, `deferred_no_plan` 1개. 모두 동일 수량 SHA. `KRX_THIN_HIGH_TICK` 7개, `SAFE_UNKNOWN` 2개. 로그의 valid 9개를 실제 발행 plan 9개로 합치지 않는다. |
| probe와 총량 | 예: 49340 목표10/즉시1/조건부9, 49345 목표9/즉시1/조건부8. 49350의 잔여 제출은 1주+2주이며 원 목표4와 구분한다. probe 1주는 allocator가 총량을 1로 정했다는 의미가 아니다. |

근거: [selector](../../data/runtime/runtime_release_selection.json), [수량 current](../../data/runtime/initial_quantity/current.json), [10/16 마지막 bootstrap 검증](../../data/runtime/policy_bootstrap/runtime_policy_bootstrap_verify_2026-10-16.json), [해당 수량 PID archive](../../data/runtime/policy_bootstrap/verified_initial_quantity_pid/2026-10-16/initial_quantity_pid_389707_f6fc86709c86.json), [분할 실행 보고서](../../data/report/entry_split_order_plan/entry_split_order_plan_2026-10-16.json).

## 3 최신 장후 결과

[committed stage](../../data/report/initial_entry_quantity_type_policy/refresh_postclose_2026-10-16/committed_stage.json)는 `generations/99dc8c37fb50905a9c06d31c960b79c6ba98b5334967d1bdf47b36412e9a645c/`를 참조한다. stage SHA는 `3498bba900a84ab67c0428e1b2e4b4d39a0798d1227f696a05333263e84ff0df`다. 선택 릴리스 native validator는 이 stage를 유효하게 읽는다. 이는 부모 유지 산출물의 계약 검증이며 경제 비교 성공이 아니다.

| 항목 | 값·해석 |
| --- | --- |
| 실행/정책 결과 | `complete_source_only`, `carry_parent`, 신규 적용 없음 |
| 읽은 fact | 16개: `COMPLETED` 9개, `HOLDING` 7개. 완료 적격 모수와 전체 읽기 행을 구분한다. |
| 최초 제외 사유 | 16개 전부 `persisted_fact_generation_invalid`; 날짜별 세부 사유는 `fact_snapshot_requires_bounded_native_projection` |
| 날짜 | 9/30·10/15·10/16 입력 날짜 모두 동일 크기 계약에서 거부 |
| 적격 경제 모수 | 0, train/holdout 0, 각 유형 비교 결과 없음. 성과 0원이나 무효과를 측정한 결과가 아니다. |
| 진단 | `policy_pid_status=verified_archive`, `economic_sample_status=source_gap`; global blocker는 독립 적용일 3일 미달. 날짜 수보다 먼저 원천 결손을 설명해야 한다. |
| 후행/시간 | `following_bar_source_status=no_winners`, pipeline receipt 0. 현재 평가가 raw 틱 0건을 증명하지 않는다. 적격 거래가 없어 후행 결합 단계로 넘어가지 못했다. |

## 4 확인한 결함·결손과 종료 조건

### IQ171 P1 — 현재 대용량 projection 생산자와 수량 consumer 불일치

- 10/15 sidecar `97,583,390 bytes`, 10/16 `261,811,082 bytes`. 각각 약93/250MiB이며 수량 reader 상한은4MiB다. 원 trade review는 약2GiB다.
- 생산자는 원 projection과 약1KiB의 `.dependencies.json`을 발행한다. 공통 holding reader는 dependency receipt로 대용량 세대를 검증할 수 있지만 `_quantity_fact_generation_issue`는 그 경로에 도달하기 **전에** sidecar 크기로 거부한다. 과거 자료에만 해당하는 문제가 아니라 10/15·10/16 신규 원천도 거부한다.
- 선택 릴리스에서 해당 함수를 9/30·10/15·10/16에 직접 실행해 같은 사유를 확인했다. 단순 용량 상한 해제나 대용량 JSON 전체 decode는 해결책이 아니다.
- 소유: `log_archive_service._save_trade_review_completed_projection`, `lifecycle/holding_window_generation`, `scalping/initial_quantity_policy._quantity_fact_generation_issue`, fact seal.
- 조치/종료: 기존 봉인 metadata 또는 bounded projection을 통해 fact run/projection/cost generation을 정확히 대사한다. 같은 원천의 작은/큰 표현, 손상·stale·비용 정정 사례가 동일 적격 결과를 내고 RSS/읽기 예산을 지켜야 한다. 이 수리 후에도 아래 비용 결손은 별도로 남는다.

### IQ172 P1 — 실행 이벤트 날짜 누락과 모수 유실의 정상 판정

- 선택 릴리스 `_bounded_execution_projection`은 hash가 맞는33개 partition(합계9,923,956 bytes)에서112개 이벤트를 반환한다. 날짜는 `emitted_date/emitted_at`에 있다.
- `_source_quality_filtered_events`가 사용하는 `_event_date`는 이 두 키를 읽지 않는다. 실제 날짜별 source-quality는 `warning / tuning_input_allowed=true / hard_blocking_stages=[]`인데 **112개 전부 제외**된다. 메모리 내에서 이미 검증된 `emitted_date`를 source date로 전달한 대조군은112개를 유지한다. 저장 원본은 바꾸지 않았다.
- 이어지는 `build_atomic_execution_sizing_lineage`는 retained 수가 producer보다 **많은 경우만** 불일치로 검사한다. producer census의 plan9/bundle8/leg10과 reader의 전부0이 함께 있어도 `ready`가 된다. 현재 보고서는 `status=pass`, `selection_blocked=false`다.
- 삼성49350의 잔여 제출2개는 원 plan SHA가 직접 없고 별도 probe context/registry로 복원해야 하는 사건이다. 이번 입력 소실로 복원/미결 판정 모두0이 되어 검증되지 않았다. broker 거절이나 실제 수량 오류로 단정하지 않는다.
- 소유: 선택 릴리스 `scalping/entry_split_order_plan.py`의 `_event_date:1824`, `_source_quality_filtered_events:2309`, census 비교`:3761`, `_refresh_execution_model_only:6544`.
- 조치/종료: 실제 emitted 날짜 계약을 정규화하고 제외 행을 사유/ID로 보존한다. producer valid = 소비+검증된 제외+명시 미관측 보존식을 닫고, 누락된 입력은 ready가 될 수 없어야 한다. 실제112개 fixture, 해당 residual2개 복원/실패, 전수 유실·부분 제외 회귀가 필요하다.

### IQ173 P2 — 수량 의미 감시기가 source gap을 valid-empty로 표시

- 최신 저장 detector와 선택 릴리스 `_initial_quantity_semantics` 직접 조회 모두 `status=valid_empty`, `postclose_stage_status=valid_empty`, `findings=[]`, `observation_complete=true`를 반환한다.
- native 코드는 stage의 count=0 및 carry_parent만으로 valid-empty를 정한다. 평가의 `economic_sample_status=source_gap`, 입력16개 전부 제외라는 원인을 소비하지 않는다. bundle0도 현재 선택된 parent 정책의 별도 집행 경로와 구분해야 한다.
- 소유: `error_detectors/artifact_freshness.py`의 `_initial_quantity_semantics_native`(선택 코드671행), 기존 semantic incident 소비자.
- 조치/종료: 정책 선택·PID archive·원모수·원천 제외·경제 적격·bundle 관측을 별도 상태로 전달한다. 자연 무거래와 비용 탈락/reader 결손/미관측 fixture를 분리하고 결손을 valid-empty/정상 복구로 알리지 않아야 한다. 최초 정책에 새 경제 승인 gate를 붙이지 않는다.

### IQ174 원천 결손 — 거래별 실제 비용 배분 미완료

- [10/16 fact sync](../../data/report/strategy_position_fact_sync/strategy_position_fact_sync_2026-10-16.status.json)는 completed5, economics-valid0, economics-missing5, 모두 `actual_cost_unallocated`다. 해당 fact의 손익/수익률은 NULL이다.
- [10/15 fact sync](../../data/report/strategy_position_fact_sync/strategy_position_fact_sync_2026-10-15.status.json)는 completed3 중 비용 미배분2·completion projection identity 결손1이다. 9/30의 오래된0값은 현 경제 실적으로 인정하지 않는다.
- [10/16 공식 비용 수집 결과](../../data/report/holding_broker_cost_source/2026-10-16.json)는 `observed`: ka10076 20행, ka10170 5행, kt00015 buy/sell 각0행. API 수집 자체가 없었던 것은 아니다. 별도 `holding_actual_costs/2026-10-16` exact settlement는0개다.
- 기존 `broker_cost_source.reconcile_position`은 동일 종목/날짜의 유일한 완결 포지션·Main custody·전체 체결량이 증명된 경우에만 일별 합계를 배분한다. 수집 성공과 각 포지션 실제 비용 확인은 다른 단계다. 이번 점검은 각 미배분의 세부 사유까지 재생성하지 않았으므로 모두 같은 원인이라고 단정하지 않는다.
- 소유: `lifecycle/broker_cost_source.py`, `broker_cost_reconciliation.py` → `sniper_trade_review_report` completion projection → fact.
- 조치/종료: record별 비용/체결/수탁/다중 포지션 배분 실패 사유를 보존하고 실제 근거가 있는 행만 수정된 세대로 재결속한다. 동종목 여러 거래의 일별 비용을 임의 비례 배분하거나 고정 비용률로 actual을 채우지 않는다. 복원 불가와 생산자 연결 결함을 분리한다.

### IQ175 관측 한계 — 후행 틱은 있으나 수집 종료 검증 미완료

- 10/16 raw에서 `initial_quantity_cap_following_tick`453개, `initial_quantity_cap_capture_finished`1개를 확인했다. 틱이 있는 record는49340(55), 49343(243), 49347(20), 49345(1), 49351(19), 49350(115)이다.
- 종료 증거는49343만 있으며 첫 주문 시작+1200초, `frozen_order_start`, queue rejected0, queued243이다. 나머지5개는 종료 증거 미관측이다. 재기동·조기 청산/attempt 정리 등 중단 이유의 대사는 남아 있다. 곧바로 producer 부재·무체결 또는 모든 구간 정상으로 판단하지 않는다.
- 현재 cap trace는 sampled last tick이며 전 시장 체결 전수 기록이 아니다. 적격 경제 모수0 때문에 장후 join0인 사실과 raw 생산453개를 분리한다.
- 소유: `sniper_state_handlers` capture 시작/종료·기존 observation queue → `initial_quantity_policy.join_post_fill_paths`.
- 조치/종료: 원 attempt/plan/PID별 시작·재시작·정리·종료 disposition과 queue/durable 기록을 대사하고 알려진 단절이 candidate source gap으로 전달되는지 확인한다. 무손실 수집이나 정확한 초를 최초 정책의 추가 gate로 요구하지 않는다.

## 5 검증과 후속 순서

1. 최신 선택 코드에서 stage native 검증 성공, 정책 loader의10/19 검증 성공. 이것은 새 릴리스의 PID 소비 영수증이 아니다.
2. 실제 실행 partition33개 SHA 일치,112개 이벤트의 날짜 필터 결함과0행 ready를 읽기 전용으로 재현했다. 실제 날짜별 quality를 사용한 경우도112개 제외였다.
3. 수량 의미 감시 결과를 저장본과 직접 실행 모두에서 재현했다. 10/16 마지막 PID archive도 동일 수량 SHA다.
4. 후행 원천 존재 여부를 확정하기 위해 변경 없는 raw2,179,360,249 bytes를 한 번 streaming 집계했다. SHA `082820c17d5547dc649b84c197d234e9ef35ecabc06e2994a7d60a2db702b890`; 집계10.279초는 점검 비용이며 장후 성능 benchmark가 아니다. 대용량 snapshot 전체 decode·반복 raw scan은 수행하지 않았다.
5. 10/11 synthetic 성능 검증은 역사적 근거다. 최신 장후는 적격 경제 거래0이므로 실제 전수 후보 처리 성능이나 EV 개선을 입증하지 않는다.

수리 순서: **IQ171 크기/세대 계약 + IQ172 날짜/보존식 → IQ174 비용 결속 → IQ175 수집 종료 대사 → IQ173 의미 감시와 마지막 소비자**. IQ173의 진단 개선은 나머지 수리와 독립적으로 진행 가능하다. 후속 구현은 각 변경의 리뷰·표적 회귀·성능 비악화 검증 후 영향 생산자부터 summary/strict까지 새 세대로 인계한다. 기존 최초 정책은 유지하며 refresh 우월성·표본·자연소비를 최초 배포에 소급 적용하지 않는다.

이번 변경은 이 감사 문서뿐이다. 코드 수리·거래 suite·API·DB 복원·연구 재생·배포/재시작·외부 동기화는 실행하지 않았다. 기존 source gap과 위 코드 결함은 미해결이며 새 정책의 경제성도 미평가다.
