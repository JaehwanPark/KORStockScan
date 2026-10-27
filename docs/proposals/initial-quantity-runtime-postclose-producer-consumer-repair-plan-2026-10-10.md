# 최초 매수 수량 런타임·장후 튜닝 생산자/소비자 상세 보완계획

작성일: 2026-10-10 KST

상태: **Q0–Q7 구현·추가 반복 리뷰·회귀 및 Q8 승인된 배포·장후 인계·PREOPEN 준비 완료**. 실제 비용/NULL·probe/slot·epoch·train/holdout·frozen reader·generation CAS·공유 자원과 native route 연결을 보완했다. 추가 재리뷰의 capture 결손 소비·시계/terminal·bounded cache/전이 reader 결함도 보완했다. 현재 선택 릴리스는 `initial-quantity-repair-20261011-v2`이며 초기수량은 부모 유지다. [실행 리뷰와 성능·운영 근거](../audits/initial-quantity-producer-consumer-implementation-review-2026-10-11.md)에 앞선 v1 및 최신 v2 영수증과 회복 불가 원천을 구분했다. native finalization08:52:58 DONE·10/12 current_full_contract PASS를 확인했다. 10/11 구현 작업은 종료하고 10/12 실제 인증/PID·자연 terminal·경제성은 기존 `DirectFamilyPreopenPolicyHandoff`의 미래 수용으로 인계한다.

## 1 범위와 실행 소유

- 원칙은 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 구현·배포 실행 기록은 [10/11 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md)의 `InitialQuantityProducerConsumerRepair1010`이다. Q0–Q8은 같은 작업의 내부 단계다. 다음 자연 수용은 10/12 기존 `DirectFamilyPreopenPolicyHandoff`가 맡는다. 실행일이 바뀌면 stable ID·수용·잔여 단계를 이전하고 현재 parsed owner는 하나만 둔다.
- 대상은 Main `SCALPING/SCALP` 최초 진입 수량, 유형별 cap·분할·총 대기시간, 실적/비용/호가/후행 틱 원천, 장후 재생·선정·발행·PREOPEN 소비다. [원 수량 계획](scalping-initial-entry-quantity-type-policy-closed-loop-plan-2026-09-26.md)의 사용자 결정은 유지하고, 9월의 진행·릴리스 기록은 역사적 증거로 읽는다.
- AVG_DOWN·holding exit의 전략 결정, 가격 소유자 P1, Main/manual 수탁, 계좌/현금/수량/호가/주문 guard는 각 기존 소유자에게 남긴다. episode/widget의 자동 BUY/SELL/CANCEL/retry와 PYRAMID를 복원하지 않는다. 역사적 퇴역 소유 잔량은 Main 진입 차단이나 Main 자동 청산 근거가 아니다.
- 비용 생산자·장후 wrapper·bootstrap은 trailing/delay 작업과 공유한다. [잔여작업 W0–W5](main-trailing-delay-residual-work-completion-plan-2026-10-10.md)의 수정본을 보존하고 실제 변경 계약을 대사한다. 공통 비용 원천을 따로 복제하거나 이 계획의 PASS로 다른 작업을 완료 처리하지 않는다.
- 알림 전송·복구는 [의미적 감시기 M1/M7](semantic-monitor-latest-release-followup-repair-plan-2026-10-10.md)의 소유다. 이 계획은 수량 native 상태·정확한 원인·원천 참조를 생산하고 양쪽 교차 회귀를 제공한다. 새 detector/notifier나 상주 worker를 만들지 않는다.

### 유지할 사용자 결정

| 항목 | 고정 계약 |
| --- | --- |
| 최초 생성 | 2026-06-05 KST 클린베이스라인 이후 가능한 모든 적격 완료 실거래를 열거한다. 익절한 거래의 실현 순이익 원화가 가중치다. 손실 거래도 전체 EV·손실 위험·원모수에 유지한다. |
| 최초와 갱신 | 최초 발행에 부모 대비 우월성·30건/80%·독립 holdout·자연 소비·정확한 초를 추가 요구하지 않는다. 확인되지 않는 유형의 시간은 검증된 기존 프로필을 유지한다. 유효한 현재 최초 정책을 재승인 대상으로 만들지 않는다. 갱신은 기존 적용 세대의 원천·비용·쌍비교·독립 검증 계약을 따른다. |
| 시간 | 저가 연구의 기준은 최초 진입 판정 시각이다. 주문 타임아웃은 `entry_cancel_wait`의 시작 결정 이후 실제 첫 주문 시작부터다. `T <= 1200초`, probe 포함 실제 leg 수로 T를 나누고 순차 활성화한다. 취소 요청·broker 최종 확인 시간도 T에 포함한다. |
| 초과 수량 | 10/15/20% cap의 실제 체결 초과분은 당시 호가 잔량과 후행 틱으로 보수적으로 재생한다. 부족분은 미체결로 남긴다. 유효한 부분 체결 결과 자체를 원천 결손이나 부모 성과로 대체하지 않는다. |
| 정책 지속 | `ACTIVE_DATE == today` 또는 날짜 경과만으로 최초 정책을 끄는 조건을 도입하지 않는다. 적용 시작일·후속 세대·원천일·당시 PID 결속은 증거 계약으로 유지한다. |

Plan Rebase §1의 `entry_cancel_wait_runtime` 취소시간 소유 설명과 위 사용자 확정 내용 사이의 잔여 충돌은 Q0에서 기존 프로필 호환 경로/신규 순차 경로별로 대사한다. 현재 문서 작업에서 Rebase·runbook·AGENTS를 변경하지 않는다. 수량 후속 구현은 사용자가 확정한 두 시계 계약을 따른다.

## 2 조사 기준과 결함 명세

아래는 **10/10 선행 읽기 전용 점검의 결과**이며 이번 계획 작성에서 다시 실행한 성능 측정이 아니다. 선택 릴리스는 `main-trailing-delay-20261010-v1`, commit `d61b36b00696865ca9dd13a466d8544a886e2e28`였다. 표의 수량/실적/로그 관련 소스는 그 릴리스와 작업공간의 바이트가 같았다. 구현 직전 Q0에서 다시 고정한다.

| ID | 우선순위·결함 | 재현·영향 | 수정 단계 |
| --- | --- | --- | --- |
| IQ-F1 | P1 비용 미확인 NULL이 0으로 저장 | `bulk_insert_mappings`의 NULL 생략과 `profit_rate`/`realized_pnl_krw`의 server default가 결합한다. 같은 ORM 경로를 메모리 DB에 실행하면 `(None, None) -> (0.0, 0)`. 미확인 실적이 손익 0으로 변한다. | Q1 |
| IQ-F2 | P1 실제 비용 생산자와 고정 비용률 소비자 충돌 | producer는 broker 실제 비용 실적을 만든다. census는 고정 비용률과 1원/0.02%p 초과 차이를 모두 제외한다. 매수 100,000원·매도 101,000원·실제 비용 200원·순이익 800원의 유효 사례도 제외됐다. | Q1 |
| IQ-F3 | P1 후행 틱 transport epoch 자료형 불일치 | logger는 필드를 문자열로 저장하고 cap context JSON은 정수를 보존한다. consumer의 `'4' != 4` 때문에 같은 원천의 추가 체결 근거를 버린다. 2주 후보가 1주만 체결된 것으로 계산됐고 정수 정규화 대조군은 2주였다. | Q3 |
| IQ-F4 | P1 probe leg/가격/시간 재생 불일치 | 4주·`two_leg_0_1tick`·probe·T=60초: 런타임 `[1,3]`, 2구간/30초지만 연구는 probe를 추가해 3구간/20초다. 기존 개별 테스트도 서로 다른 leg 수를 통과시킨다. | Q2 |
| IQ-F5 | P2 갱신 forward 경계 누락 | CLI가 부모 `effective_from=2026-09-24`만 넘겨 9/29 경계 이전을 읽는다. 10/8 replay의 `entry_on_or_after`는 9/24이고 9/28 거래가 입력에 있다. | Q4 |
| IQ-F6 | P2 부분 체결 cap EV가 선정에서 유실 | replay는 `partial_unfilled` 손익을 계산하지만 선정기는 `paired`만 세고 나머지를 부모 실적으로 대체한다. 가상 유효 부분 체결 3건의 후보 순이익 60원이 부모 30원으로 치환되는 격리 사례를 재현했다. 실제 수익 실적을 뜻하지 않는다. | Q3·Q5 |
| IQ-F7 | P2 holdout이 후보 선택에 개입 | cap별 holdout 통과를 보며 후보를 고른다. 학습 자료를 고정하고 holdout만 바꾸면 10%에서 15%로 후보가 바뀐다. 형상/시간은 전체 기간으로 순위를 정한다. 독립 검증이 아니다. | Q5 |
| IQ-D1 | 진단 보완: 표본 0과 PID 미소비 혼동 | `_natural_refresh_pid_receipt`는 거래 배열이 비면 바로 None을 반환한다. 9/30·10/8의 검증 가능한 보관 PID 증거가 있어도 10/8 평가에 `parent_pid_consumption_missing`이 표시된다. 거래 결속 미평가와 정책 소비 부재를 분리해야 한다. | Q4·Q6 |

근거 소스: [fact 생산·저장](../../src/engine/strategy_position_performance_report.py), [ORM](../../src/database/models.py), [pipeline logger](../../src/utils/pipeline_event_logger.py), [수량 census·재생·선정](../../src/engine/scalping/initial_quantity_policy.py), [런타임 leg](../../src/engine/scalping/entry_split_order_plan.py), [시간 연구](../../src/engine/scalping/initial_quantity_timeout_research.py).

운영 스냅샷: [10/8 replay](../../data/report/initial_entry_quantity_type_policy/refresh_postclose_2026-10-08/initial_quantity_refresh_replay_2026-10-08_142ac3634b49.json)는 3건을 읽어 미완료 1건·비용 계약 불일치 2건을 제외하고 유효 표본 0건으로 부모를 유지했다. 읽기 전용 DB 조회에서도 record 48296/49013의 순손익/수익률 필드는 0이며, 9/29 이후 최초 완료 fact는 49013 한 건이었다. 이 숫자는 향후 복원/신규 실적 후 바뀔 수 있다. [current 포인터](../../data/runtime/initial_quantity/current.json)가 참조하는 정책 파일의 당시 SHA는 `ba72d720a4c11dbcfd18a667d2f47a648c0e7b792fe9a3edbb7193f674870cca`이고 10/12 대상 연결 검증은 통과했다. 당시 Main 신규 PID 소비는 예약 기동 전이었다.

선행 회귀는 수량 관련 6개 suite **202 passed / 106.00초 / 경고 1건**이다. 이는 장후 전체 성능 수용이나 위 7건의 수정 완료가 아니다. 별도 재현이 기존 테스트의 연결 범위 누락을 드러냈다.

### 2.1 계획 재리뷰에서 보완한 연결 계약

아래는 현재 소스를 대조해 추가한 **구현·검증 의무**다. IQ-F 표의 격리 재현 결과와 구분하며, 아직 코드 수정이나 운영 실패 재현을 완료한 것으로 표시하지 않는다.

| ID | 확인한 코드 경계와 계획의 누락 | 보완·종료 시험 | 단계 |
| --- | --- | --- | --- |
| IQ-R1 | state handler의 cap trace는 sizing 계획 시각부터 1200초 후 제거되지만, 주문 T는 실제 주문 시작 기준이다. tick observer는 `last_trade_tick`을 읽으므로 시장의 모든 체결 관측을 보장하지 않는다. | 판정/수집/주문 시작/fill 시계를 분리하고 지연 시작·무주문·restart·연결 단절 때 수집 종료와 coverage를 검증한다. 희소 관측을 확정 무체결로 해석하지 않는다. | Q2·Q3 |
| IQ-R2 | fact sync는 날짜별 원천 세대를 검증하지만 수량은 누적 창을 읽는다. 고정 비용률로 쓰는 status 상단 설명과 실제 비용 row가 충돌할 수 있다. | 입력에 포함된 모든 날짜의 persisted fact·비용 세대를 일관된 snapshot으로 봉인한다. 과거 날짜의 비용 정정·부분 write·저장 후 NULL/0 readback을 검사한다. | Q1·Q4 |
| IQ-R3 | 일부 거래의 부모 결속 실패가 평가 전체 blocker가 되고 source-quality 플래그만으로 행 제외 수행 여부를 알 수 없다. | 식별 가능한 record/attempt/window를 제외하고 나머지 집합을 보존한다. 전역 원천 무효·격리 불가만 전체 차단한다. 한 행 결손/전수 결손을 나누어 회귀한다. | Q3·Q4·Q5 |
| IQ-R4 | 미체결 시도·계획 목표량과 완료 실적의 분모 구분이 불충분하다. | 전체 시도 진단 ledger와 완료·비용 적격 경제 ledger를 분리한다. 무주문/취소 시도를 실제 손익 0인 완료 거래로 추가하지 않는다. | Q2·Q4·Q5 |
| IQ-R5 | stage validator가 현재 evaluator를 다시 호출하고 activation이 부모를 재귀 검증한다. evaluator 수정만으로 구 부모의 저장된 evaluation과 불일치할 수 있다. | schema/평가/실행/비용 버전별 reader, 구 pin의 검증과 신규 successor 선정 분리를 먼저 구현한다. 구 최초·여러 ancestor·신규 후보 로딩을 교차 시험한다. | Q0·Q6 선행 |
| IQ-R6 | report 파일은 해시별이지만 stage는 날짜별 고정 이름의 immutable 파일이며 wrapper도 고정 경로를 읽는다. | 같은 source date의 정정은 새 run/generation 경로와 봉인된 stage 참조를 사용한다. 모든 reader 이관, CAS 전후 crash·동시 발행·재실행을 시험한다. | Q6·Q8 |
| IQ-R7 | 누적 거래·결합 후보 확대 시 현재의 전수 순회/재검증 비용과 실제 병목을 나눠 측정하는 기준이 없다. | 기능 수정 기준과 최적화 기준을 분리하고 단일 scan·증분 계산·warm 검증의 작업량 및 시간/CPU 절감을 증명한다. 장중 지연·메모리·기한 회귀는 별도 필수 gate다. | Q0·Q7 |
| IQ-R8 | 공통 research admission의 heavy 등록은 현재 trailing/delay용이다. 수량 wrapper/직접 CLI의 공유 예산 연결은 확인되지 않았다. | 수량 stage도 같은 admission/저장 예산에 명시 등록·결속한다. 중첩 호출의 중복 예약, CLI 우회, 합산 RSS·디스크·대기 상한을 검증한다. | Q6·Q7 |

추가 근거: [수집·수량 caller](../../src/engine/sniper_state_handlers.py), [분봉 보강](../../src/engine/scalping/initial_quantity_following_bars.py), [activation](../../src/engine/scalping/initial_quantity_activation.py), [장후 wrapper](../../deploy/run_threshold_cycle_postclose.sh), [공통 admission](../../src/engine/lifecycle/research_admission.py), [공통 저장](../../src/engine/lifecycle/research_storage.py), [디스크 예산](../../src/engine/lifecycle/research_disk_budget.py). 공통 연구 코드는 작업공간에서 진행 중인 의존성이며, 파일 존재를 선택 릴리스에 설치됐다는 근거로 사용하지 않는다.

## 3 생산자부터 마지막 소비자까지의 목표 계약

| 구간·기존 소유자 | 입력/출력과 필수 결속 | 마지막 소비자·종료 조건 |
| --- | --- | --- |
| 최초 allocator / state handlers | 판정 전 유형·예산/상한·정책 파일 SHA·attempt·계획 SHA·수량, route/item/epoch·원 관측 시각 | 실행 계획과 장후가 같은 입력을 읽고 동일 수량을 산출 |
| entry split / P1 / timeout / bundle / terminal | 목표·계획·제출·체결·미체결 수량 분리, 실제 leg 배열·가격 의미·시계·취소 reserve·종결 | 후속 BUY는 선행 terminal 확인 후 해당 slot 안에서만; 연구도 같은 배열/slot 소비 |
| pipeline logger → cap reader | JSON 문자열 안의 구조체와 바깥 문자열 필드를 구분한 schema·정규화·원본 보존 | 원천 유효/부족/손상을 구분하며 같은 route/epoch만 체결량으로 계산 |
| completed/cost 원천 → fact mart | record/owner/buy-fill/exit/cost 세대, actual cost status·출처 SHA, null과 진짜 0 | 수량 census·기존 성과 소비자가 실제 비용 값을 그대로 사용 |
| census → 가격/틱/분봉/시간 재생 | 원모수와 비용 적격·가격 지원·모델링 가능 집합을 별도 보존, 동일 input manifest | cap·형상·T의 결합 후보를 같은 실행 계약과 비용 모델로 평가 |
| train → 후보 확정 → holdout | 전역 고유 거래·유형·부모 정책·후보 집합·비교 비용 모델·split/hash | holdout 실패 시 부모 유지, 같은 holdout으로 차순위 탐색 금지 |
| stage → activation → bootstrap | source/evaluation/candidate/parent SHA·불변 artifact·CAS·적용일 | [activation](../../src/engine/scalping/initial_quantity_activation.py)·[bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py)·실제 PID가 같은 정책을 소비 |
| wrapper → summary/strict → 의미 감시 | 정확한 source date·완료/부모 유지/원천 결손·관측된 PID 상태 | [장후 wrapper](../../deploy/run_threshold_cycle_postclose.sh)·[summary](../../src/engine/automation/postclose_summary_handoff.py)·native validator·감시가 같은 원인을 보고 |

신규 지표는 기존 report/stage를 버전 확장한다. 품질 진단은 `metric_role=source_quality_gate`, `decision_authority=report_only`, `window_policy=exact_source_generation`, `sample_floor=contract_required_no_statistical_floor`, `primary_decision_metric=producer_consumer_binding_and_census_conservation`, `source_quality_gate=typed_identity_cost_and_declared_observation_coverage`으로 선언한다. 추정 경제 지표는 `primary_ev`로 별도 선언하고 `estimated`/`fixed_exit_assumption`/비용 모델·분모를 명시한다. 모두 원천 결손의 0 EV 치환, CF를 실현손익으로 합산, 신규 주문/수량 상한 완화에 사용하는 것을 금지한다.

경제 지표의 나머지 계약은 `decision_authority=bounded_candidate_recommendation_only`, `window_policy=initial_clean_baseline_or_refresh_parent_forward_window`, `sample_floor=generation_specific_existing_contract`, `primary_decision_metric=winner_pnl_weighted_modeled_return_with_all_trade_net_ev_and_risk`, `source_quality_gate=cost_identity_execution_model_and_frozen_cohort`, `forbidden_uses=actual_fill_claim_or_initial_uplift_gate_or_runtime_guard_bypass`다. 익절 가중치는 `actual_net_pnl > 0 AND actual_profit_rate > 0`인 거래의 원화 순이익이며 합계가 0이면 가중 지표는 null이다. 쌍비교 coverage는 비용 적격인 해당 유형 원모수 중 선언된 관측·보수 체결 모델에서 유효 full/partial/modeled no-fill을 계산한 고유 거래 비율이다. 실제 체결·미체결 확인과 modeled outcome을 별도 필드로 둔다. 비용 미확인 완료 거래 수와 가격/호가 결손 수는 별도 원모수/사유로 공개한다. 후보마다 지원 집합이 다르면 공통 비교집합과 전체 집합 민감도를 함께 보고해 분모 선택으로 우월성을 만들지 않는다.

## 4 단계별 구현·수정 계획

### Q0 기준 고정과 실패 fixture

1. selected release·소스 SHA, dirty diff, 현재 정책/부모·stage·예상 적용일·PID 증거를 고정한다. 날짜가 지난 조사 결과를 현재 기동 증거로 재사용하지 않는다.
2. IQ-F1–F7/IQ-D1의 입력·기대값·실패 지점·영향 소비자를 기존 테스트에 재현한다. 실제 입력은 record/date/SHA를 남기고 비밀·계좌 정보는 fixture에 넣지 않는다. 실제 wire 문자열·ORM 저장을 통과시키며 dict에 정수만 직접 넣는 검증으로 끝내지 않는다.
3. 공통 파일의 진행 중 변경과 실제 배포본을 대사한다. 새 모듈이 필요하면 위치 gate를 적용해 순수 수량 계약은 `src/engine/scalping`, 장후 orchestration은 `src/engine/automation`, tests는 `src/tests`에 둔다. `src/engine` 루트에 새 모듈을 만들지 않는다.
4. `entry_cancel_wait`·레거시 TTL·새 bundle schedule caller를 구분한다. 호환 프로필이 아직 쓰이는 위치와 삭제 가능한 중복 계산을 목록화한다. 파일 이름/주석만으로 퇴역시키지 않는다.
5. IQ-R1–R8의 실제 caller·누적 비용 세대·정책 ancestor·stage 경로를 고정하고 실패/정상 fixture를 추가한다. 특히 Q6의 버전별 구 artifact 검증과 새 generation 참조 수용은 evaluator 의미 변경을 운영 경로에 연결하기 전에 준비한다. Q1–Q5 격리 구현과 병행할 수 있으나 구 부모가 읽히지 않는 중간 상태를 배포하지 않는다.
6. Q7의 성능 기준을 먼저 봉인한다. 동일 호스트/CPU 조건·프로젝트 Python·코드/입력/정책 SHA·후보 grid·행/틱/유형 수·캐시 상태·반복 수·기존 지연/메모리/디스크/완료기한 예산과 baseline 편차를 기록한다. 원 릴리스와 기능 수리본의 결과 차이 검증, 기능 수리본과 최적화본의 동등 결과 성능 비교를 분리한다. 성능 개선 목표·허용 편차·측정 구간을 결과 확인 후 바꾸지 않는다.

종료: 결함별 실패 재현과 기존 정상 회귀·성능 기준, 공유 소유자·데이터 세대·검증 명령이 고정된다. 이 단계는 정책이나 DB를 쓰지 않는다.

### Q1 비용 원천·NULL 저장·소비 계약 수리 — IQ-F1/F2

1. fact/summary 일괄 저장의 명시적 NULL을 보존한다. ORM의 NULL 생략·DB default·조회 직렬화까지 통합 검증한다. 진짜 비용 후 손익 0, 미확인, 미완료를 다른 상태로 저장한다. 전체 0원 거래를 결손으로 바꾸지 않는다.
2. fact mart까지 비용 출처·reconciliation 상태·원 record/체결/청산 identity·census/projection/actual-cost generation을 전달한다. 기존 테이블에 없는 필드를 `_trade_fact_db_payload`가 버리는 경계를 해소한다. 호환 schema 확장과 영속 필드를 우선 검토하고 동일 truth를 가진 별도 저장소는 만들지 않는다. 기존 row는 출처 미확인으로 읽으며 출처를 사후 추정해 채우지 않는다.
3. 수량 census는 실제 비용 영수증·정확한 identity와 수량·금액/반올림 계약으로 실제 실적을 검증한다. 고정 0.23% 계산과 일치 여부를 실제 실적의 적격 조건에서 제거한다. 임의로 차이 허용치만 넓히지 않는다. 이미 승인된 최초 정책/역사적 초기 입력의 알려진 비교 비용 계약은 버전과 출처를 유지해 읽으며, 이 수리로 최초 생성에 새로운 broker 실제 비용 영수증 gate를 붙이지 않는다. 최근 actual-cost 원천의 결손을 역사적 비교 모델로 채워 실제 비용 확인을 주장하지 않는다.
4. `actual_net_pnl`은 실제 비용 기준, CF의 `modeled_parent_net_pnl`/`modeled_candidate_net_pnl`은 같은 버전의 명시된 비교 비용 모델로 계산한다. 실제 비용과 비교 모델의 차이 자체를 후보 개선으로 세지 않는다. 가중치는 실제 익절 순이익을 사용한다. 후보를 원 실행과 같게 만들면 비교 delta가 0이어야 한다. 근거 없는 실제 수수료의 단순 수량 비례 확대는 금지한다.
5. 당시 48296/49013 등을 포함해 오염 후보 목록을 읽기 전용으로 먼저 만든다. 복원은 exact rec_date/record·원 terminal/cost 증거가 확인된 행만 기존 fact sync 경로로 수행한다. 원천 부재는 NULL+사유다. 9/28 복원은 감사용이고 갱신 학습에 넣지 않는다. 운영 DB 변경은 후속 실행 범위에서 트랜잭션·전후 영수증·중단/복구 절차와 함께 한다.
6. 비용 사후 정정 시 연결 census→projection→fact→quantity replay/evaluation/stage의 무효화·재봉인을 수행한다. 오래된 as-of 비용으로 최신 정책을 선정하지 않는다. shared 성과·scanner 소비자의 NULL 처리도 회귀한다.
7. 누적 평가에 포함되는 모든 rec_date의 fact status·completed census·actual-cost 세대·source digest를 검증한다. 당일 fact sync PASS로 과거 날짜의 유효성을 대신하지 않는다. 누적 입력은 DB의 일관된 읽기 snapshot과 연결 manifest를 사용하며, 읽는 동안 비용 세대가 바뀌면 해당 계산을 재시도/무효화한다. 과거 비용 정정은 영향 날짜/행과 후속 계산만 갱신한다.
8. status의 비용 설명은 실제 persisted row의 actual/model/unresolved 내역을 반영한다. 저장 전 payload만으로 성공을 선언하지 않고 NULL·비용 출처·행 수를 저장 후 대사한다. 거래 진입일·청산일·rec_date·KST as-of가 다른 사례도 검증한다.

운영 DB 복원 전에는 대상 row/세대의 읽기 전용 목록과 변경 예정 payload를 먼저 확정한다. 기존 sync가 rec_date 전체를 삭제/재삽입하는 경로이면 같은 날짜의 비대상 행까지 원천 완전성을 검증하고, 불완전한 날짜는 운영 쓰기를 중단한다. schema 변경은 additive/구 reader 호환으로 시작하고 migration 실패·부분 write·동시 갱신을 시험한다. 비용 생산자 수정 권한이나 필요한 원천이 없으면 코드/격리 검증은 계속하고 운영 복원만 해당 소유자·artifact·closure 조건으로 남긴다.

종료: NULL round-trip, 진짜 0원 보존, 실제 비용 정상 수용, 출처 결손 배제, 동일 실행 delta=0, 비용 revision·중복 수리 idempotence가 통과한다. 회복 불가 실적은 미복구 목록으로 남기며 코드 수리와 구분한다.

### Q2 런타임과 장후의 수량·분할·시간 공통화 — IQ-F4

1. `build_initial_quantity_type_legs`와 기존 순수 timeout schedule을 공통 실행 계약으로 삼는다. probe는 형상의 첫 leg이며 형상 앞에 별도 leg를 추가하지 않는다. 런타임·형상 재생·timeout 연구가 같은 수량 배열·가격 offset 의미·leg index·cancel reserve를 소비한다. 숫자 주문 가격은 계속 P1이 실제 제출 시점에 정한다.
2. `target_qty`, `planned_qty`, `submitted_qty`, 실제 fill/잔량을 분리한다. 갱신용 exact 재생은 봉인된 목표수량을 사용하고, 실제로 체결된 수량을 목표로 바꿔 probe-only/부분 체결 기회를 누락하지 않는다. 목표 원천이 없는 역사적 coarse 재생은 별도 source grade로 남긴다.
3. Q0에서 잡은 4주/probe 사례 외에 수량 1/2/3/4/7, 부모·2/3분할, probe 유무, 총시간과 나눗셈 나머지, T 상한·reserve 경계를 대사한다. 분할 불가 수량의 fallback/차단 의미도 공통화한다.
4. `decision_at`, `order_start_at`, fill·후행 저가·각 slot·bundle deadline을 분리한다. T의 나머지 초 배분과 취소 reserve를 동일 적용하고, 판정→시작 지연을 주문 대기시간에서 차감하지 않는다. 각 leg는 정해진 구간과 선행 terminal 확인을 모두 만족해야 활성화된다.
5. 모든 가상 체결 관측은 해당 slot의 활성화/취소 경계, 실제 청산 시각, 최대 수집 horizon에 제한한다. cap replay의 무조건 `first_fill+1200` 관측도 실제 후보 시간표 밖 체결을 허용하지 않도록 결합한다. 취소/최종 확인 미관측을 성공으로 합성하지 않는다.
6. 기존 실주문 중복 제출 방지·영속 intent·불확실 응답·restart 복원·owner/broker/계좌 terminal을 유지한다. 실제 broker request/parser/FID/recovery를 수정해야 한다면 AGENTS의 최신 공식 Kiwoom reference gate를 그 변경 전에 수행하고 SHA·경로·조회 시각을 기록한다. 역사적 9월 upstream 영수증으로 대체하지 않는다.
7. `capture_at`은 관측 시각일 뿐 주문 시계를 대신하지 않는다. 계획 생성부터 1200초 후 trace를 버리는 현재 경계를 바꿔, 실제 시작·bundle deadline에 필요한 원천이 수집되도록 한다. 판정 기준 저가 연구창과 주문 기준 실행 관측창을 각각 저장한다. 시작 전 관측은 기존 진입 대기 만료/attempt 종료에 묶어 유한하게 유지하고, 시작한 bundle은 durable 시작시각·상한을 복원한다. 재시작/후행 tick이 시작시각이나 T를 연장하지 않는다. deadline 뒤 terminal 확인 책임은 기존 안전 경로에 남기며 새 BUY를 허용하지 않는다.
8. 과거 프로필 시간의 exact 재생은 당시 선택된 profile/value/source SHA를 사용한다. 현재 env 값으로 과거 거래의 T를 다시 만들지 않는다. 당시 근거가 없는 최초 입력은 기존 coarse 등급과 승인된 기존 정책/프로필 시간 계승을 유지하고 이를 과거 exact 증거로 표시하지 않는다. 지연 시작 때 오래된 depth를 새 관측으로 표시하지 않으며, 후보 가격을 미래 저가로 선택하거나 실제 첫 체결이 slot 밖인데도 후보의 보장 체결로 넣지 않는다.

종료: 동일 입력의 런타임/재생 leg 수·수량·offset·slot·deadline 불일치 0. 4주/probe/2분할/60초가 모두 `[1,3]`·30초 두 구간이다. 안전 guard·미확정 주문의 재전송 회귀가 없다.

### Q3 호가·후행 틱과 부분 체결 cap 평가 — IQ-F3/F6

1. 기존 pipeline wire 계약을 전역 변경하지 않고 cap consumer 경계에서 숫자 자료형을 검증·정규화한다. canonical 정수/문자열 정수는 같은 epoch로 읽되 bool·소수·NaN·빈값·잘못된 형식은 명시 결손 처리한다. 변환 실패를 epoch 0으로 보정하지 않는다.
2. 원 snapshot의 item/venue/route/epoch·관측 시각과 attempt/plan SHA를 후행 틱에 결속한다. 중복 틱, route 변경, reconnect epoch 변경, stale, 청산 후/후보 deadline 밖 관측은 제외 사유를 남긴다. 원 체결과 동일 유동성의 이중 사용을 막는다.
3. CF 상태는 `full`, `partial_unfilled`, `modeled_no_fill`, `source_gap/censored`로 구분하고 `observation_coverage`를 별도 기록한다. 승인된 보수 모델은 유효하게 관측된 잔량/틱까지만 체결시키고 나머지를 **모델상** 미체결로 남긴다. 모든 시장 틱의 보유를 새 필수 gate로 추가하지 않는다. 다만 필수 depth/identity 부재, 수집 종료 오류·알려진 구간 단절은 결손이며 무체결 0으로 채우지 않는다. `verified_no_fill`은 실제 주문 terminal 등 검증 가능한 별도 증거에만 사용한다.
4. 정책 평가가 유효 partial/무체결을 같은 원거래 분모로 소비하도록 바꾼다. 부모 실적 치환을 제거하고 모델링 가능 집합·원천 결손 집합·보수 민감도를 분리한다. CF 결과를 actual fill로 표기하지 않는다.
5. 원수량 초과분은 Q2의 후보 가격/시간표와 depth/틱 한도 안에서만 채운다. cap·분할·시간을 각각 따로 통과시킨 뒤 평가하지 않은 조합으로 묶지 않는다. 관련 결합 평가의 최종 소유는 Q5다.
6. 기존 `last_trade_tick` 관측의 sampling/중복 제거/누락 계수와 지원 가능 범위를 명세한다. 필요한 보강은 기존 수집 경로·bounded projection/queue를 사용하며 별도 전종목 snapshot·무제한 tick 저장/worker를 추가하지 않는다. 분봉은 허용된 coarse 가격/시간 연구에만 사용하고 호가 잔량이나 정확한 bar 내 체결 순서를 만들어내지 않는다.

종료: 실제 logger 문자열→parser→cap evaluator 통합 재현이 통과한다. 동일 epoch는 연결되고 다른 epoch는 제외된다. 부분 체결의 후보 손익이 집계 끝까지 보존되며 결손 원천은 coverage/사유로 남는다.

### Q4 학습창·원모수·PID 진단 — IQ-F5/D1

1. 갱신 시작을 `max(clean baseline, forward 2026-09-29, selected parent effective_from)`으로 계산하는 공통 계약을 만든다. 최신 적용 정책과 실제 진입 당시 정책 hash/PID가 같은 거래만 그 정책의 적용 후 집합으로 사용한다. 최초 생성 경로는 전체 클린베이스라인 계약을 유지한다.
2. DB 읽기, 수량 replay, timeout 연구, 외부 분봉 보강, `--replay` 재사용, publisher/validator에 같은 창·as-of·적용 정책·input manifest를 전달한다. CLI만 고치고 재사용 보고서로 경계를 우회할 수 없게 한다. 시간대·자정·익일 청산을 시험한다.
3. 전체 최초 시도, 실제 완료 원모수, 비용 적격, 원천 지원, 동일 부모 결속, 비교 가능 집합의 개수·고유 ID 보존식을 보고한다. 비용 결손으로 전부 탈락한 경우와 실제 완료 거래 0건을 다른 상태로 표현한다. `valid_empty`에는 완전한 원천 검증이 필요하다.
4. 정책 소비 증거 조회는 거래 배열 0건과 독립적으로 정확 적용일/부모의 archive/manifest를 조사할 수 있게 분리한다. `policy_pid_status`, `trade_policy_binding_status`, `economic_sample_status`를 구분한다. 역사적 유효 PID 증거는 현재 실행 중 증거로 바꾸지 않는다.
5. 유효 PID·표본 0, 비용 결손·표본 0, PID 부재·관측 불가, 미래 기동, 다른 부모 PID를 구분한다. 정보가 없다는 이유로 `consumed=true`도 `not_consumed=true`도 합성하지 않는다.
6. 전체 attempt/bundle의 진단 ledger와 `COMPLETED + valid profit_rate + 해당 비용 계약`의 경제 ledger를 연결하되 분리한다. 무주문·취소·불확실/미청산 시도를 실제 손익 0인 완료 거래로 늘리지 않는다. 완료 원거래의 고정 exit 가정 안에서만 CF partial/no-fill을 평가하고 실제 비용·가상 비용을 섞지 않는다.
7. source-quality의 제외 플래그만 읽지 않고 실제 record/attempt/window selector가 적용됐는지 count/ID 보존식으로 검사한다. 식별 가능한 비용·부모·route 결손은 해당 행/창 또는 의존 유형만 격리한다. 전역 preflight 무효, 원천 식별/격리 실패만 전체 평가를 막는다. 선택 입력에 필요 없는 보강 원천 결손은 그 원천을 쓰는 후보의 결손으로 한정한다. 유효 표본+결손 1건과 전수 무효 fixture를 구분한다.

종료: 9/28 제외·9/29 포함·부모 경계·최초 생성 전수 사례가 통과한다. 10/8과 같은 비용 탈락 0건이 자연소비 부재로 잘못 설명되지 않는다. 손상/오래된 replay의 신규 발행은 거부된다.

### Q5 결합 후보 선정·독립 검증 — IQ-F6/F7

1. 유형별 후보를 `(ratio_mode, shape, timeout_mode/T, probe 규칙, 실행/비용 모델 버전)`의 고정 조합으로 봉인한다. 승인된 10/15/20% cap·부모, 기존 2/3분할 형상, 1200초 이내 시간 후보만 사용한다. 탐색 범위 확대로 통과 후보를 만들지 않는다. 기존 분류 기준·SAFE_UNKNOWN 부모를 유지한다.
2. Q1의 비용 모델, Q2의 실행 계획, Q3의 유효 부분 체결로 부모와 각 후보를 동일 거래·원 notional 분모에 재생한다. 2026-10-17 사용자 확정에 따라 익절 실현 순이익 원화 가중치는 후행 가격·시간·분할 후보 산출에 사용하고, 최종 갱신 선정은 전체 승패의 비용 후 평균 EV 개선과 원화 순이익 개선으로 평가한다. 익절 거래의 가중 성과 증가를 별도 필수조건으로 강제하지 않는다. 익절 가중치가 없는 후보 연구값은 산출 불가로 남기며 기존 프로필을 계승한다. 기존 v2 평가 영수증은 당시 알고리즘으로 재현하고 신규 선정만 버전으로 구별한다.
3. 최초 생성과 refresh의 entry point·validator·테스트를 분리한다. 현재 유효한 최초 정책을 다시 만드는 작업은 기본 범위가 아니다. 필요한 최초 발행은 낮은 허들·부모/프로필 계승 계약을 그대로 따른다.
4. refresh는 전체 고유 거래를 전역 시간순으로 train/holdout에 분리한다. 같은 포지션·attempt·후행 가격창을 양쪽에 중복 사용하지 않는다. 재생 horizon이 경계를 넘는 행은 제외/격리하고 shard별 split을 합치지 않는다. 기존 최소 표본·coverage·날짜 요건을 명시해 유지하며 수량 작업에 다른 family의 완화/강화 기준을 가져오지 않는다.
5. train에서 점수·tie-break로 후보 **하나**를 고른 후 후보 SHA를 고정한다. 그 후보를 holdout에서 검증하고 실패하면 부모를 유지한다. 같은 holdout으로 차순위 cap/형상/T를 재선택하거나 창·grid를 바꾸지 않는다. 동일 세대 재시도도 같은 결과여야 한다.
6. train/holdout 각각의 부모/후보 모수·비용·손익·coverage를 봉인한다. 미지원 원천을 부모 수익으로 채워 비교하지 않으며, 전체 원모수와 비교가능 집합의 차이를 표시한다. 비용/원천 정정으로 세대가 바뀌면 이전 후보/검증을 재사용하지 않는다.
7. 유형은 최초 판정 시점에 관측 가능한 특성과 당시 classifier 버전으로 고정한다. 후행 저가·체결 성공·실현손익으로 유형을 재분류하지 않는다. 목표수량·예산 원천이 있는 완료 실적에서 같은 자금/가격 제약으로 후보를 만들며, 목표가 불명확한 역사 입력을 cap 확대의 exact 증거로 사용하지 않는다.

Q0에서 현재 적용 부모에 대한 기존 refresh 수치도 봉인한다. 조사 코드의 v2 부모는 유형별 최소 30건, 형상/시간 coverage 80%, 독립 날짜 3개, 형상/시간의 부모 대비 비용 후 +0.10%p 조건을 사용하며 cap은 train 최소 30건·train/holdout coverage 80%·일별 손익 조건을 별도로 사용한다. Q5는 독립 검증/결합 실행 계약을 수리하며 이 수치를 임의로 올리거나 최초 정책에 전용하지 않는다. 경계 변경으로 요건을 어느 집합에 적용할지 불명확하면 기존 요건의 의미와 제안 차이를 문서화해 사용자 결정 대상으로 남긴다. 표본이 적다는 이유로 자동 완화하지 않는다.

종료: holdout만 바꿔도 train 선택 후보 SHA는 같고 승인/부모 유지 결과만 달라진다. 실제 실행 가능한 하나의 조합만 발행 후보가 되며 최초 발행에 refresh 허들이 유입되지 않는다.

### Q6 정규 장후·정책 인계·감시 연결과 퇴역 정리

1. 새 비용/재생/평가 schema를 기존 publisher·stage validator·activation·summary·strict verifier·bootstrap·감시 reader까지 함께 이관한다. 구 artifact는 감사·기존 부모 pin 검증 용도로 보존하되 구 평가를 새 successor 선정 증거로 사용하지 않는다. 해시만 재계산한 기존 보고서의 재명명은 금지한다.
2. 기존 wrapper의 fact sync→수량/후행/timeout→평가 stage→strict/정식 인계→eligible 선택→PREOPEN 순서와 late CAS 뒤 최종 검증을 대사한다. 비용 세대가 바뀌었는데 이전 summary/strict/DONE을 재사용하는 경로를 차단한다. 운영 automation 변경 시 owning 운영문서·체크리스트도 같은 구현 변경에 반영한다.
3. `complete_source_only`, `carry_parent`, `insufficient_sample`, `source_gap`, `eligible`, `selected`, `consumed`의 의미를 마지막 소비자까지 일치시킨다. Q4의 빈 원모수·비용 결손·PID 미관측을 별도 원인으로 전달한다. 의미적 감시기 M1/M7에는 native 상태/identity fixture를 제공하며 운영 Telegram으로 시험하지 않는다.
4. 중복 probe 추가·독립 수량 배분·고정 비용률에 의한 actual 적격 판정·부분 체결 부모 치환·holdout 차순위 탐색을 삭제/교체한다. 레거시 프로필/TTL·v1 reader는 실제 caller·핀된 ancestor·롤백 호환을 확인하고 도달성 0인 실행 경로만 퇴역한다. `entry_cancel_wait` 시작 owner 자체를 삭제하지 않는다.
5. 반복 평가/발행·부모 CAS 경쟁·정책 파일 변조·구 loader/new schema 혼합·process restart를 격리 주입한다. 실패 시 current는 마지막 유효 정책을 유지하고 원 artifact/주문 journal을 보존한다.
6. 현재 `refresh_quantity_stage_terminal_valid`의 evaluator 재실행과 activation의 ancestor 재귀를 버전 계약으로 분리한다. 과거 artifact는 당시 schema/평가/실행/비용 버전으로 검증하며, 현재 evaluator에 입력해 과거 evaluation을 다시 해석하지 않는다. 구 pin reader의 범위는 이미 선택된 유효 ancestor의 검증/호환으로 한정하고 신규 후보는 신규 평가 계약을 통과시킨다. 단순 파일 hash 확인만으로 필수 평가 검증을 생략하지 않는다.
7. 같은 날짜에 비용/코드/입력이 정정되면 새 run/generation 디렉터리에 report/evaluation/candidate/stage를 함께 봉인한다. wrapper·summary·strict·activation·bootstrap·감시는 committed stage의 정확한 참조를 전달받도록 이관한다. 날짜별 고정 stage 파일을 덮어쓰거나 삭제 후 재발행하지 않는다. 무거운 재생·hash 검증은 CAS 밖에서 수행하고, 짧은 임계 구역에서 검증된 부모/세대의 포인터만 전환한다. 전환 중 변경과 crash는 새 검증 없이 선택 완료로 처리하지 않는다.
8. Q7의 공통 admission/저장/증분 검증을 wrapper와 직접 CLI 양쪽에 연결한다. 진행 중인 trailing/delay 구현의 설치 버전·예약 계약을 먼저 확인하고 수량 stage를 명시 등록한다. 공통 코드 변경은 기존 caller 회귀를 포함하며 별도 예산을 더해 전체 허용량을 늘리지 않는다.

종료: 정규 caller를 통과하는 입력→비용→재생→선정/부모 유지→정책 검증→PREOPEN fixture가 연결된다. unresolved source는 정상/완료로 숨기지 않고 해당 소유자에 인계한다.

### Q7 데이터 기반 결과·성능·반복 코드리뷰

#### Q7.1 결과 정합성과 실제 작업량

기존 suite를 우선 확장한다: `test_strategy_position_performance_report.py`, `test_pipeline_event_logger.py`, `test_initial_quantity_policy.py`, `test_initial_quantity_timeout.py`, `test_initial_quantity_bundle_state.py`, `test_initial_quantity_terminal.py`, `test_scalping_position_sizing_allocator.py`, `test_entry_split_order_plan.py`, `test_entry_execution_sizing_plan.py`, 영향 bootstrap/summary/strict/semantic suite. 개별 순수 함수 테스트와 실제 producer→저장/직렬화→consumer 통합 테스트를 모두 요구한다.

| 자료/시험 | 결과 검증 | 성능·한계 |
| --- | --- | --- |
| 동결 실제 fact·pipeline·비용 세대 | 10/8 스냅샷의 제외 원인 전후, 9/29 이후 전수 census, 복원 가능/불가를 분리 | 유효 표본 0이면 비용 적격 0을 보고한다. 가상 fixture로 실제 EV 개선을 주장하지 않는다. |
| 실제 형식의 결정적 fixture | 7개 결함과 IQ-R1–R8, 비용 NULL/0·과거 비용 정정, probe/부분·무체결·취소/불확실/restart, 다른 route/epoch, 지연 시작·다음 leg deadline | 임의 int dict만 사용하지 않고 logger wire·ORM round-trip·publisher/loader까지 연결 |
| 초기/갱신 경계 | 최초 부모 계승·프로필 시간·부정확 초 허용, refresh의 exact 부모/창/독립 holdout | 첫 정책 배포 전 자연소비 요구가 재유입되면 실패 |
| 원천/캐시/반복 | 동일 입력 재실행·교차 chunk 중복·late conflict·비용만 변경·raw 변경/손상·예산 중단/재개·같은 날짜 successor | output 논리 결과/census 동등성, 누락 0, 같은 세대 중복 발행 0; 구/신 정책 ancestor reader 호환 |
| 전체 장후 경로 | fact read/sync, 단일 pipeline scan, 후행 보강, 형상×cap×T, 평가·직렬화·검증 | wall/CPU/peak RSS·읽기/쓰기 byte·decode/hash 횟수·API 요청 수/대기·캐시 hit/miss를 분리 |
| 장중 영향 | 기존/수정 allocator·공통 leg·후행 tick 기록·bundle/취소 처리에 같은 정상/burst/느린 writer 입력 | 수량/guard/제출 횟수 불변, hot-path 지연 p50/p95/p99·메모리·I/O 비교 |

성능 지표는 기존 품질 진단 역할 안에서 `metric_role=source_quality_gate`, `metric_domain=operational_performance`, `decision_authority=report_only`, `window_policy=same_frozen_workload_and_environment`, `sample_floor=declared_event_count_and_repeated_runs`, `primary_decision_metric=deadline_preservation_and_end_to_end_work_cost`, `source_quality_gate=equal_cohort_candidate_grid_and_result_contract`, `forbidden_uses=economic_approval_or_runtime_guard_change`로 선언한다. 구현 수용 근거로 사용하며 새 자동 매매 gate나 정책 family를 만들지 않는다. 속도 개선을 정책 EV·실현이익·안전 guard 완화 근거로 사용하지 않는다.

#### Q7.2 성능 저하 방지와 개선의 필수 요건

| ID·경로 | 구현 요건·개선 대상 | 완료 근거 |
| --- | --- | --- |
| IQ-P1 장중 수량 결정·정책 조회 | 검증된 정책 세대의 준비된 immutable lookup과 공통 leg/schedule을 사용한다. 매 결정마다 조상 정책 재평가·전파일 hash/JSON decode·동기 DB/API 조회를 추가하지 않는다. 기존 허용된 로딩/재적용 경계에서 검증·준비 후 원자 교체하고 진행 중 bundle은 기존 pin을 유지한다. 장중 정책 변경 권한을 추가하지 않는다. | cold 준비와 warm 결정 분리. 동일 입력의 수량/slot/guard 동일, warm 경로의 불필요한 조회·재계산 제거, p95/p99/max·CPU·지연 예산 비악화. 구/신 세대 전환과 변조 거부를 동시에 확인. |
| IQ-P2 후행 원천 생산·로그 | 기존 관측에서 필요한 필드만 projection하고 event당 작업·payload·큐·trace 수를 제한한다. 중복 decode/직렬화를 줄인다. 느린 writer가 Main 결정·보유 보호·취소 확인을 동기 대기시키지 않도록 기존 저장 경계를 사용한다. | 정상/burst/slow writer에서 queue depth·체류시간·누락 계수·byte/event·RSS, 실제 handler 지연을 측정. 결속 필드가 logger compact limit으로 잘리지 않아야 한다. queue 상한 초과는 명시 source gap이며 샘플 성공으로 숨기지 않는다. |
| IQ-P3 장후 전수·결합 재생 | 동일 source 세대는 작업 내 한 번 정규화/scan하고 수량·timeout이 공유한다. DB 필요한 열/행을 일관된 snapshot에서 읽고, 후보 공통 feature·유동성/시간창 계산을 재사용한다. 모든 거래×후보의 중간 결과를 동시에 메모리에 보관하지 않는다. | 입력 수 N·후보 수 C·source byte·scan/decode/DB query 수와 CPU/wall/RSS 공개. 후보 grid 증가가 원천/API 읽기 증가로 이어지지 않고, candidate block/partition 실행이 일괄 참조 결과·전역 split과 동일. |
| IQ-P4 동일 입력·비용/원천 증분 | 원천 feature와 비용·후보 평가 캐시를 분리한다. 비용만 변하면 검증된 시장 feature를 재사용하고 해당 손익/가중치/선정 및 후속 영수증을 다시 계산한다. 새 자료는 영향 partition과 전역 중복/집계를 갱신한다. | warm 재실행·cost-only·일부 신규 입력 각각에서 cold와 논리 결과 동일, 불변 source의 중복 JSON decode 제거, raw 읽기/hash/CPU/wall 절감 측정. 비용·창·classifier·정책/grid 변경 시 필요한 재계산을 생략하면 실패. |
| IQ-P5 외부 후행 보강 | 기존 종목/날짜/venue 요청·캐시·rate limit을 공유하고 cap/형상/T별 재호출을 금지한다. 같은 cache miss 요청의 동시 중복을 합치고 timeout/retry는 기존 유한 예산 내에서 수행한다. | 고유 요청 수·cache hit/miss·대기/재시도 공개. 동결 API 응답 fixture로 단독/동시 작업의 호출 수·결과 대사. API 결손/예산 소진을 빈 정상 자료로 반환하지 않음. |
| IQ-P6 발행·검증·PREOPEN | Q6 버전 reader로 cold 검증한 세대의 공유 검증 결과를 재사용한다. 동일 조상/source를 각 reader가 반복 전수 재생하지 않도록 검증 컨텍스트를 공유하되 exact byte·버전·세대 계약을 보존한다. CAS/selector 잠금 안에서 대규모 읽기/연구를 실행하지 않는다. | ancestor 깊이·artifact 수별 cold/warm 시간·hash/replay 횟수·lock hold/wait를 측정. 캐시 변조·부분 publish·부모 교체를 거부하고 PREOPEN 기존 기한 준수. 캐시 hit를 이유로 필수 provenance 검증 생략 금지. |
| IQ-P7 공통 자원·동시 실행 | 수량 wrapper와 직접 CLI가 동일 writer/admission·resident memory·디스크 예산을 사용한다. 기존 stage별 weight/slot 규칙을 대사해 수량의 실제 최악 작업량에 맞춰 등록한다. 상속 예약은 stage/day/root/process/유효 lock 증거를 확인하고 중복 예약을 막는다. | 단독 및 trailing/delay 동시 요청, 중첩 CLI·이전 worker 생존·cancel/crash/retry 시험. 부모+자식+이전 job 합산 RSS·CPU·active slot·대기기한·참조 중 cache와 old/new 출력의 디스크 peak가 공통 상한 이내. |
| IQ-P8 성능 퇴행 검출·운영 인계 | 측정용 원천과 성능 결과에 baseline/수리/최적화 commit·입력/정책 SHA·예산·cohort/grid·환경·반복별 원값을 보존한다. 기존 native report/stage의 단계 timing·작업량을 bounded 집계로 연결한다. | 누가 같은 명령으로 재측정해도 비교 가능한 영수증. performance PASS와 sample/source/경제성 상태를 분리하며, 미래 표본이나 빠른 empty 실행으로 전체 성능 수용을 대체하지 않음. |

**캐시·분할의 정확성 계약:** 키에 원천 content manifest/coverage·as-of/입력창·부모 정책·유형 classifier·실행/비용/평가 버전·grid·전역 split을 필요한 계층별로 결속한다. 물리 partition 변경은 동일 논리 입력 identity를 보존한다. inode/mtime/size만으로 원천 동일성을 인정하지 않는다. warm 검증에도 요구되는 원 leaf/manifest byte 검증을 예산에 포함하며, 동일 검증 컨텍스트 안에서만 중복 hash를 줄인다. late conflict는 이미 계산한 해당 고유 거래도 전역 무효화한다. 캐시 정리 시 진행 중 reader/pin이 참조하는 데이터는 보존한다. 손상 캐시는 명시적으로 재구축하고 authoritative 원천 결손은 source gap으로 남긴다.

**유한 작업과 자원 계약:** 기존 [공통 저장](../../src/engine/lifecycle/research_storage.py)·[디스크 예산](../../src/engine/lifecycle/research_disk_budget.py)의 record/index/temp/resident 상한과 예산 합산 범위를 Q0에서 고정한다. 단일 큰 record도 별도 무제한 버퍼로 우회하지 않는다. DB snapshot은 필요한 추출 구간에서만 유지하고 재생/API/발행 동안 운영 DB transaction/lock을 붙잡지 않는다. 실제 조회계획·행 수·lock wait로 필요한 인덱스/추출 방식만 보완한다. 초과는 누락 없는 분할·checkpoint/재개 또는 명시적 budget 상태로 처리한다. 필수 입력을 버리거나 0건 성공으로 바꾸지 않는다. 분할은 최종 census·train/holdout·선정의 전역 의미를 유지해야 한다. admission 미연결을 단순 설치 대기로 남기지 않고 Q6의 필수 구현으로 닫는다.

#### Q7.3 측정 설계와 합격 기준

1. **비교 기준 두 개:** 선택 릴리스→기능 수리본은 IQ-F/IQ-R별 입력/출력 변화와 비용을 대사한다. 성능 최적화는 같은 올바른 결과를 내는 기능 수리 기준본→최적화본으로 비교한다. 결함 때문에 더 적게 처리하던 구 경로의 빠른 시간을 전수 정상 처리의 동등 baseline으로 삼지 않는다. 그렇더라도 수정 후 실제 장중 지연·자원·완료기한은 기존 운영 예산을 충족해야 한다.
2. **동일 자료·실행:** 동결 실제 자료와 충분한 적격 거래/유형·depth/tick·전체 후보를 가진 결정적 fixture를 각각 사용한다. 정상/상한 근접/결손·재개 및 cold/warm/cost-only/new-source 모드마다 동일 환경에서 기본 3회 측정하고 반복별 원값·범위를 보고한다. 실패 직후 종료나 eligible 0의 실행시간만으로 전체 성공 작업의 성능을 판정하지 않는다. cold/warm 캐시 정의·예열 비용·검증/직렬화/정리 비용도 포함한다.
3. **장중 비악화 필수:** 실제 allocator/observer/bundle/취소 handler와 Main due·보유 보호가 공유하는 경로를 격리 adapter/동결 계좌·broker 응답으로 실행한다. p50/p95/p99/max, N, deadline miss·guard 처리·제출 횟수·queue 적체·CPU/RSS를 비교한다. 기존 hard deadline 위반·수량/terminal 의미 변화·누락 은폐는 허용 편차와 관계없이 실패다. 표본이 적으면 불안정한 p99만으로 PASS하지 않고 max/원값·결정적 fake-clock 경계시험을 함께 쓴다.
4. **장후 개선 필수:** 동일 전수·전체 grid의 cold 성공 경로는 시간/CPU/RSS·완료기한이 사전 예산과 허용 편차 내여야 한다. warm 및 cost-only/증분 경로는 불필요한 scan/decode/호출/재생 작업량 감소와 end-to-end wall 또는 CPU의 측정 가능한 감소를 함께 입증한다. 감소가 baseline 변동폭 안이면 개선 미입증이다. 병목별 절감이 전체 시간/다른 단계 악화로 상쇄되는지도 보고한다. 숫자 목표는 Q0에서 실측 기준과 기존 예산으로 고정하며 근거 없는 일괄 개선율을 만들지 않는다.
5. **결합 부하 필수:** 수량 단독·정규 장후 다른 heavy job과 동시 요청·느린 저장소·Main 정상/burst/취소 due의 공유 자원 경합을 시험한다. 기존 공통 admission을 지키는 대기 시간도 전체 완료기한에 포함한다. 앞 job/자식 RSS와 캐시·임시·구/신 출력 동시 peak를 제외한 개별 함수 숫자로 PASS하지 않는다. 실운영 주문/불필요한 API 호출로 부하를 만들지 않는다.
6. **결과 동등성 우선:** 최적화본의 logical census·행별 손익·유효 부분 체결·보수 미체결·single train winner/holdout·선정/부모 유지가 기능 수리 기준과 같아야 한다. 물리 artifact 분할·timing 메타데이터 차이는 별도 정규화해 비교한다. 성능 때문에 후보/모수/guard를 줄이거나 처음 정책에 우월성/자연소비를 추가하지 않는다. 실제 표본 0이면 실제 EV 개선은 미평가이며, synthetic 성능 통과와 구분한다.
7. **퇴행 처리:** 사전 예산을 넘거나 개선이 미입증이면 원인 단계와 다음 수리/재측정 범위를 명시하고 Q7 전체 완료를 선언하지 않는다. 최적화 철회 시에도 NULL 보존·비용/epoch/probe·독립 holdout 수리를 유지한다. 잘못된 과거 평가나 퇴역 실행을 성능 rollback으로 복원하지 않는다. 영향 수정의 검증이 끝나면 목적 없는 추가 반복/전수 재생은 중단한다.

#### Q7.4 리뷰·검증 영수증

각 단계의 순서는 **구현 → self review → 영향 생산자/소비자 리뷰 → 보완 → 재리뷰 → 표적 회귀**다. Python compile·영향 pytest, wrapper 변경 시 bash 문법/계약, `git diff --check`, 문서 print-only parser를 수행한다. 실제 과거 원천의 회복 불가와 아직 발생하지 않은 자연 사건은 코드 finding과 분리한다. 다만 원천 수집/소비가 미구현인 상태를 자연 표본 대기로 닫지 않는다.

실행일 audit에는 각 IQ-F/IQ-R/IQ-P별 owner·코드/입력 SHA·실행 명령·결과/성능 파일·다음 조건을 연결한다. 성능 영수증에는 각 단계의 wall/CPU, process tree 합산 peak RSS, read/write/temp byte, decode/hash/API/DB query 수, cache hit/miss, admission/lock wait, 후보/원모수/누락 수를 남긴다. 사용자 대기 중인 결정이 생기면 그 항목만 질문하고 독립 작업을 계속한다.

종료: IQ-F1–F7/IQ-D1과 IQ-R1–R8의 회귀 및 결과 차이 대사, IQ-P1–P8의 장중 비악화·장후 개선·결합 예산, 미해결 구현 finding 0. 테스트 건수나 일부 microbenchmark만으로 전체 gate를 대신하지 않는다.

### Q8 승인된 배포·정식 인계와 자연 수용

1. Q7의 기능/성능 영수증과 공통 admission·구 정책 reader를 포함한 설치 범위를 확인한 뒤 기존 사용자 승인 범위에서 불변 릴리스·실제 caller/root·의존 schema를 재검증한다. 데이터 복원/정책 재생이 필요한 범위를 구체화하고 원천일을 고정한다. 코드 준비·배포·정책 선택·PID·경제성을 별도 상태로 보고한다.
2. 아직 유효한 최초 정책은 유지할 수 있다. 코드 수리 배포에 새로운 정책의 우월성이나 자연 주문을 선행 조건으로 붙이지 않는다. successor가 적격일 때만 단일 수량×분할×시간 정책을 기존 CAS로 선택하고, 표본 부족이면 근거가 정확한 부모 유지 stage를 발행한다.
3. 기존 승인된 dispatcher/회복 경로로 영향받는 producer→summary/checklist→strict `--require-summary-handoff`→controller/finalization을 닫는다. 봉인된 과거 파일을 덮어쓰지 않고 successor 세대를 만든다. 기준 source date를 자정 뒤에도 보존하고 독립한 종료 영수증만 허용된 규칙으로 재사용한다.
4. release/policy/준비 입력이 바뀌면 해당 적용일의 PREOPEN을 새 세대로 준비·검증한다. 현재 예정일은 10/12이나 실행 때 실제 영업일/스케줄을 확인한다. 본 계획 단계에서는 봉인된 10/12 checklist·prepared를 변경하지 않는다. 구현 후 변경이 필요하면 기존 owner와 정식 승계한다.
5. 실제 기동 후 PID/cwd/start ticks·정책 파일 SHA·첫 수량 결정의 attempt/type/plan을 확인한다. 발생한 자연 주문에 한해 leg·취소·terminal을 추적한다. 사건 0건은 `not_observed/future_due` 등 정확한 상태로 남기며 사건을 만들기 위한 주문/AI 호출은 하지 않는다. 첫 정규 장후에서 비용 적격/결손·부모 유지/갱신 사유를 끝까지 대사한다.
6. 실패 복구는 호환되는 release·policy/parent·reader·bootstrap/prepared 전환 세트를 함께 검증한다. 비용 오염을 재도입하는 무검증 DB 덮어쓰기, 새 pointer와 구 reader 혼합, retired 실행 복원, journal 삭제는 하지 않는다.

종료 보고는 `document_complete`, `code_review_complete`, `data_repair_disposition`, `performance_verified`, `release_selected`, `policy_selected_or_carried`, `preopen_prepared`, `pid_consumed`, `natural_terminal`, `economics`를 구분한다. 미래 자연 수용에는 적용일의 기존 담당 작업을 연결하고, 이를 최초 배포 전 모순적 차단 조건으로 삼지 않는다.

## 5 단계별 실행 지시문

한 번에 전체를 실행하기보다 아래 묶음으로 지시할 수 있다. 각 지시는 위 동일 stable ID의 진척을 갱신하며 다른 단계의 완료를 주장하지 않는다. 선행 공통 계약이 바뀌면 영향 단계만 다시 검증한다.

의존 순서는 `Q0 → Q1 → Q2/Q3 → Q4/Q5 → Q6/Q7 → Q8`이다. 단, **Q6의 구 평가 버전 reader/신규 세대 참조 골격은 Q0 뒤에 먼저 준비**해 Q1–Q5의 의미 변경과 함께 검증한다. 성능 측정·예산 고정도 Q7 말미로 미루지 않고 Q0 및 각 단계 회귀에서 누적한다.

| 순서 | 복사해서 사용할 지시문 |
| --- | --- |
| 1 | `수량 생산자/소비자 상세 보완계획 Q0을 실행하라. 현재 release·정책·원천 세대와 IQ-F1~F7/IQ-D1·IQ-R1~R8 fixture, 장중/장후 성능 기준·예산을 고정하라. Q6의 구 버전 reader·세대 참조 선행 작업을 명세하고 리뷰하라. 운영 DB·정책은 변경하지 마라.` |
| 2 | `같은 계획 Q1을 구현하고 비용 NULL 저장·실제 비용 출처·수량 소비 계약을 통합 테스트하라. 역사적 복원 대상과 회복 불가를 먼저 명세하고, 운영 복원 권한이 확인된 범위만 실행하라. 리뷰·수정·재검증을 반복하라.` |
| 3 | `같은 계획 Q2와 Q3을 구현하라. probe 포함 수량·가격 offset·slot을 런타임/재생에서 공통화하고 실제 주문 시작에 맞춘 bounded 원천 수집, wire epoch·부분 체결 cap 결과를 검증하라. 장중 지연·수집 예산·안전 terminal 회귀 후 재리뷰하라.` |
| 4 | `같은 계획 Q4와 Q5를 구현하라. 최초/갱신 창·비용 모수·PID 진단을 분리하고 결합 후보를 train에서 먼저 확정하라. holdout 실패 시 부모 유지, 최초 정책의 낮은 허들 보존을 회귀 검증하라.` |
| 5 | `같은 계획 Q6과 Q7을 실행하라. 구 정책 reader·같은 날짜 successor·정규 장후/직접 CLI의 공통 admission부터 publisher/validator/bootstrap/감시까지 연결하라. 동결 실제 자료와 전수 fixture로 장중 비악화, cold 예산 준수, warm/비용 증분 개선, 결합 성능을 IQ-P1~P8별 입증하고 미해결 결함을 수정·재리뷰하라.` |
| 6 | `Q7 완료 근거를 확인한 뒤 Q8을 기존 승인 범위에서 수행하라. 불변 릴리스·정식 장후 인계·부모 유지 또는 적격 successor·새 PREOPEN을 검증하고, 실제 PID/자연 terminal/경제성은 각 관측 단계로 인계하라.` |

## 6 계획 수용과 구현 완료의 구분

계획 수용은 7개 결함 및 IQ-D1, IQ-R1–R8 연결 보완의 원인·기존 소유자·단계·실패 fixture·종료 조건, IQ-P1–P8의 측정/개선 의무, 초기/갱신·시간/수량·권한·문서 연결의 일치로 판단한다. 문서 단계에서는 로컬 링크·현재 owner 단일성·공백·diff와 print-only parser만 검증한다. 테스트·API·장후 연구를 계획 작성 때문에 재실행하지 않는다.

구현 완료는 Q1–Q7의 실제 수정·회귀·성능 증거로 판단한다. 정책 표본 0, 미복구 역사 원천, 미래 PID/주문은 별도 수용 상태다. 형식상 정상인 stage나 오래된 PASS로 결과 결함을 덮지 않는다. 이 문서에는 계획 검증 결과만 기록하며 실제 구현·배포 결과는 실행일 checklist/audit에 남긴다.

문서 재리뷰에서는 실제 비용/비교 모델 분리, 누적 날짜별 비용 세대, 주문 시작과 수집 horizon, 진단/경제 분모·식별 가능한 결손 격리, 구 evaluator reader·동일 날짜 successor의 선행 의존을 보완했다. 성능 요건은 장중 결정/원천 기록·장후 전수/증분·검증/PREOPEN·공통 자원 8경로로 명세하고, 올바른 기준본과의 결과 동등성·장중 비악화·장후 개선을 필수 수용으로 추가했다. 최초 정책의 기존 허들, P1/시작/수탁·퇴역 경계는 유지한다. 코드·정책·운영 실적을 수정하거나 성능을 실측한 영수증은 아니다.

## 7 2026-10-17 후속 연구 실행 계약

사용자 확정: **익절 순이익 가중 후보 생성 → 전체 거래 비용 후 EV·순이익 최종 선정**. 현재 유효한 최초 정책을 재승인 대상으로 만들지 않는다. 앞선 IQ171–IQ175 감사는 당시 세대의 증거이며, 실행 직전 최신 선택 코드·원천에서 재현 여부를 다시 고정한다.

| 단계 | 작업·산출물 | 종료 조건 |
| --- | --- | --- |
| 1 입력 보존 | 최신 release/정책/원천 SHA, 날짜별 fact·실행 모수와 제외 ID; bounded reader와 emitted 시각 정규화·공통 census | 생산 입력 = 정상 소비 + 검증된 제외 + 명시 미관측. 미설명 결손은 source gap이며 0행 ready 금지. 과거16/112는 봉인 fixture에서만 고정 기대값으로 사용한다. |
| 2 비용·후행 종료 | record별 비용·custody·완료 identity 사유와 attempt별 수집 시작/종료/중단 disposition | 검증 복구·회복 불가·추가 근거 대기를 구별한다. 공식 문서에서 의미가 미정인 주문별 비용 집계를 exact 비용으로 간주하지 않는다. §8의 사용자 승인 총비용 배분은 연구 전용으로 구분해 사용한다. 역사 terminal을 재작성하지 않고 신규 lifecycle의 중단/재시작/queue 계약을 검증한다. |
| 3 선정기 | `initial_quantity_all_trade_ev_selection_v3`; 원거래 기준금액·동일 비교 비용·부분체결/미체결 보존 | 학습의 전체 거래 평균 EV 개선 → 원화 순이익 개선 순으로 후보 하나를 고정한다. 독립 holdout의 EV·순이익 비악화를 검증한다. 익절 가중 성과 개선은 필수조건이 아니다. 기존 표본/coverage/날짜/형상·시간 위험 요건은 변경하지 않는다. |
| 4 결합 재생 | 여섯 유형의 부모/10·15·20% cap × 기존 형상 × T≤1200초 결과와 원모수·결손표 | 실행 가능 순차 leg/probe/취소 확인 시간에 맞춘 같은 거래 비교. canonical exact 비용 또는 §8의 승인된 연구 배분 비용이 검증된 적격 거래가 모두 0건이면 경제성은 미평가이며 현 정책을 유지한다. |
| 5 검증·성능 | 실제 자료 점검 + 적격 전수 fixture의 cold/warm/비용 증분·원천 변경 실행, wall/CPU/RSS/I/O | 결과 동등성과 기존 예산 준수를 검증한다. 선정 의미 변경과 실행 결과의 성능 비교를 분리한다. 0건 처리 결함본의 빠른 시간을 정상 전수 기준으로 쓰지 않는다. |
| 6 발행·인계 | 새 평가 버전의 불변 stage 또는 명시 부모 유지, 구 stage reader·선정 정책·PREOPEN 준비 검증 | 새 코드/정책 준비·선택·PID 소비·자연 주문·경제성을 각각 보고한다. 최초 정책에 배포 전 자연소비나 갱신 경제 요건을 소급 적용하지 않는다. |

실행 owner와 결과는 현재 일일 체크리스트의 `InitialQuantityResearchRepair1017` 및 실행일 audit가 소유한다. 정책·원천 세대가 달라지면 앞선 결과를 그대로 승계하지 않는다.


## 8 2026-10-17 비용 생산자·소비자 보완 계약

사용자는 **키움 확정 총비용을 매수·매도 거래대금에 따라 배분하여 수량 연구에 사용하고, 거래별 API 확정 비용과 구분**하도록 확정했다. 같은 종목의 복수 거래를 단순 제외하거나 정산 자료가 언젠가 생기기를 기다리는 상태를 구현 완료로 보지 않는다.

### 8.1 비용의 의미와 데이터 경계

- `broker_confirmed_total_allocated`는 키움의 날짜·종목별 확정 관측 총비용을 해당 날짜의 BUY+SELL 거래대금으로 배분한 연구 비용이다. `actual_execution_cost=false`, `economics_scope=initial_quantity_research_only`를 반드시 전달한다.
- 정수 원화 배분은 거래대금 비례 계산 후 최대 나머지 방식으로 합계를 보존한다. Main으로 확인되지 않은 거래금액의 몫은 별도로 남겨 Main에 전가하지 않는다. 식별되지 않은 거래를 임의로 Main custody로 만들지 않는다.
- 익일 청산은 실제 매수·매도 체결 날짜별 원천을 각각 사용한다. 미청산 포지션의 확인된 체결도 비용 몫을 남기며, 청산·취소 terminal을 만들지 않는다.
- 연구 배분 비용으로 canonical actual 수수료·실현손익·profit_rate·strict 완료 상태를 변경하지 않는다. 수량 후보의 익절 가중치·전체 거래 비용 후 EV·순이익에는 승인된 연구 비용을 일관되게 사용하고 비용 기준을 표시한다.
- 실제 계좌·Main owner·record·체결 수량/가격/일자·완료 terminal이 검증되어야 한다. 모의/CF/수동/퇴역 owner의 비용은 Main 실제 비용으로 승격하지 않는다.

### 8.2 구현 및 마지막 소비자

| 단계 | 소유 코드/산출물 | 검증·종료 조건 |
| --- | --- | --- |
| 공식 원천 | `lifecycle/broker_cost_source.py` | 기존 ka00001·ka10170·ka10076·kt00015의 실전 계좌/연속조회/날짜 계약 유지. 주문별 수수료 합산을 최종 비용으로 가정하지 않는다. |
| 연구 비용 생산자 | `lifecycle/broker_cost_allocation.py` | 전체 거래/미청산의 확인 체결을 선구성하고 날짜·종목 총비용을 배분한다. 배분+별도 잔여 몫=공식 총비용, 중복 체결/초과 거래금액/미확인 custody/보유수량을 초과한 선행 매도/최종 완료 뒤 체결은 거부한다. |
| 보고서/영수증 | `sniper_trade_review_report.py`, `runtime/initial_quantity_research_costs/<완료일>/` | 기본 보고서는 읽기 전용. 장후 snapshot writer만 비용 영수증·불변 세대·의존 날짜 index를 기록한다. 잘못된 exact 파일을 다른 경로로 정상화하지 않는다. |
| 세대/정정 | `broker_cost_reconciliation.source_generation` | index가 가리키는 불변 영수증과 실제 의존하는 과거 원천 SHA를 결속한다. 현재 원천과 다른 영수증은 연구 입력에서 제외하고 재생산한다. 과거 원본과 정정 전 세대는 보존한다. |
| bounded 전달 | log archive·strategy performance·initial quantity source cache | 전체 보고서→bounded fact→완료 overlay→수량 연구→수량/분할/timeout replay까지 비용 기준·영수증·최초 확보 시각을 보존한다. 사라진 영수증은 오래된 값으로 보충하지 않는다. |
| 선정기 | 수량 v3 | persisted index·record/원천 SHA가 일치하는 연구 비용만 인정한다. holdout 이후 확보된 비용을 학습에 사용하지 않으며 배분 자료를 구 v2로 우회하지 않는다. |

- 같은 매도 체결의 재관측은 원 native receipt 신원·원 clock·경제/수량/route/owner payload가 모두 일치할 때만 하나의 체결로 해석하고 재관측 횟수·원천 digest를 남긴다. 같은 주문/체결번호의 충돌은 결손으로 보존한다.
- 전일 매수의 연구 custody는 검증된 원 BUY ledger와 계좌/intent/주문/체결/수량/금액이 일치하는 bounded registry로 연결한다. 명시된 수동/외부 owner·veto·충돌을 과거 Main 기록으로 대체하지 않는다. stale 로컬 정리만으로 broker 체결/terminal을 확정하지 않는다.
- 부분 청산의 DB 정수 가격과 원 체결 가중평균 가격을 구분한다. 원 fact 가격을 별도 결속하고 기존 단가 일치 guard를 유지하면서 연구 계산에는 원 체결 총금액/수량을 사용한다. canonical 가격은 수정하지 않는다.

### 8.3 정규 장후 운영과 정산 대기

기존 `deploy/run_threshold_cycle_postclose.sh`의 비용 단계는 같은 resource owner와 180초 외부 timeout 안에서 다음 경로를 호출한다. 새 cron은 추가하지 않는다.

```bash
PYTHONPATH=. "$VENV_PY" -m src.engine.lifecycle.broker_cost_source --date "$TARGET_DATE" --drain-pending
```

- TARGET를 먼저 처리하고 과거 대기 날짜는 한 번에 최대1개 추가한다. 150초 소프트 예산은 기존 요청 사이에서 확인하고, 진행 중 transport의 최종 제한은 기존 180초 외부 timeout이 맡는다.
- 실제 KST 날짜별 claim을 호출 전에 기록한다. 같은 날 실패·중단을 성공으로 표시하거나 무한 재조회하지 않는다. 당일 20시 전 관측은 같은 날 최종 TARGET 관측으로 갱신할 수 있다. 수집 성공만으로 거래의 비용 해결을 승인하지 않는다.
- 보고서 소비자가 검증된 exact/연구 영수증을 기록한 뒤에만 해당 record를 acknowledge한다. 미해결은 다음 날짜에 재조회하고 지원 기간 밖이면 `expired`와 추가 검증 원천 필요 사유를 보존한다.
- 과거 날짜의 원 ka10076 관측은 보존한다. 날짜 필터가 없는 ka10076을 과거 실적으로 새로 조회하지 않는다. 동일 날짜 계좌 원천 정정은 원 bytes를 불변 history에 저장한 후 alias를 변경한다.
- 기존 수집 지원 범위는 2026-09-29 이후이면서 현재 KST 날짜부터 60일 이내다. 기간 밖의 결손은 외부 검증 원천 필요 상태로 남긴다. 대기 상태는 4MiB·512 source 날짜·10,000 record/date 의무로 제한한다.
- 대기 상태는 `runtime/holding_broker_cost_pending/state.json`, 실제 시도는 별도 불변 attempt 영수증이다. 중복 enqueue/ack는 멱등이며 동시 수집·갱신과 기존 상태를 보존한다.

다음 정규 기동용 코드 배포는 원 준비 정책의 `7f2552` source→검토한 후속 source의 정확한 두 경로쌍 인계와 새 holding capability fixture를 요구한다. 원 report capability `057c127…`에서 정확한 후속 세대로 직접 검증하며 과거 호환성을 포괄 허용하지 않는다. 기존 미래 정책값·128개 보조 binding·승인된 두 PRE 변경·rollback을 보존하고 native `current_full_contract`를 검증한다. 코드 배포 준비를 위해 운영 비용/index/fact를 임의 생성하지 않는다.

### 8.4 필수 검증과 완료 구분

- 복수 포지션·익일 매도·부분 체결·미청산·수동 잔여·정수 반올림·원천 누락/정정·계좌 충돌·clock 역전·손상 exact 파일·동시 index 발행·예산/크기 제한의 반례를 검증한다.
- 비용 세대 전체는 공통 metadata에 한 번만 저장하고 거래별로는 해당 record/날짜의 증명만 전달한다. 비용 세대나 완료 원천 전체를 거래마다 복제하는 제곱 증가를 금지한다.
- 영수증 필드는 생산자와 모든 bounded 원문/sidecar reader가 같은 256KiB 한도를 사용한다. 다일 분할 체결의 16KiB 초과 정상 영수증을 누락시키지 않고 256KiB 초과는 명시 거부한다. 일반 scalar/전체 보고서 한도를 넓혀 우회하지 않는다.
- 의미 감시기는 공통 함수로 만든 compact completion/fact 참조를 원 native 전체 증명과 결속한다. 구 전체 참조도 유지하며, terminal의 연구 비용 영수증과 fact의 영수증이 다르거나 사라진 경우를 거부한다.
- 당일 stage 관측과 이미 승인된 정책의 issued ancestry 관측을 명시적으로 구분한다. 당일 관측은 현재 원천·비용·코드를 재검증한다. 과거 승인 이력은 발행 당시 증명·원 stage/선언 child·정책 연결을 검증하며, 이후 비용 정정·원천 압축·검증 코드 변경만으로 유효한 기존 정책을 무효화하거나 최초 채택 허들을 추가하지 않는다.
- 생산자가 허용하는 4MiB 초과 연구 보고서/timeout 결과도 마지막 감시 소비자에 도달해야 한다. 기존 scalping projection 역할 안에서 생산자가 native 검증 후 bounded 감시 요약·증명을 발행하고, 감시기는 원 stage/보고서의 실제 identity·SHA·검증 code·모수/제외·원천 결손 의미를 확인한다. 원 보고서 bytes·정책 검증은 보존하고 감시의 전체 파일 한도 확대나 hash만 있는 요약으로 우회하지 않는다. 구 작은 보고서는 기존 reader를 유지한다.
- 실제 계약으로 생성한 1,000건 이상/4MiB 초과 입력의 감시까지 연결하고, compact/full 참조·연구 영수증 누락/변조·요약 변조/교체·원천 교체·구 stage·불변 세대·cold/warm 및 감시 hot path의 대형 원문 미해독을 회귀 검증한다. 일자별 증명/projector는 한 번 준비해 건별 전체 세대 복사를 반복하지 않는다.
- 실제 봉인 자료의 연구 적격/제외 ID와 비용 보존식을 대사하고, 적격 비어 있지 않은 fixture의 전체 비용→연구→재생 성능을 측정한다. 0건 경로의 빠른 시간을 성능 증거로 삼지 않는다.
- 후행 가격 소비자는 검증된 연구 배분 손익을 canonical 실제 손익(NULL)과 직접 비교해 누락시키지 않는다. native 비용 세대/거래별 영수증·금액/수량·확보 시각을 결속한 뒤 연구용 순이익과 가중평균을 사용하고, 후행 결과에도 비용 기준·actual_execution_cost=false·연구 영수증 SHA를 전달한다. 거래별 API 확정 비용 경로와 원 요청/route/시간/예산 guard는 보존한다.
- 완료 census 재검증은 일자별 native metadata를 제한 없이 보관하지 않는다. 전체 1,000건의 연구 비용 영수증·제외 사유를 유지한 상태로 기존 64MiB 공통 resident 예산 안에서 일자별 증명을 검증·해제한다. 예산 확대나 비적격 거래의 영수증 삭제로 성능 검증을 통과시키지 않는다.
- 최초 정책의 별도 경제/자연소비 허들을 추가하지 않는다. 수리 코드 검증·선택 배포·정규 장후 자연 생산·실제 PID 소비·비용 후 성과는 각각의 근거로 보고한다.
- 보완 owner는 동일한 `InitialQuantityBrokerCostClosure1017`이며 현재 실행은 [10/18 체크리스트](../checklists/2026-10-18-stage2-todo-checklist.md)에 이관했다. 기존 `InitialQuantityProducerConsumerRepair1010`의 남은 역사 원천/정산·경제성 Acceptance와 `DirectFamilyPreopenPolicyHandoff`의 실제 소비 조건은 유지한다.


### 2026-10-21 배포 전 수량 feature 검증

자연 종료 대기는 실제 최초 전환에 적용한다. 닫힌 과거 원천의 reader/소비 검증은 그 전에 수행한다. 기존 source cache는 대형 pipeline의 native indexed coverage·chain generation과 별도의 물리 identity를 사용한다. cold feature 생성은 현재 streaming reader의 같은 물리 읽기에서 SHA를 계산하고, immutable cache의 정확한 byte proof만 native digest session에 결속한다. 작은 원천의 byte 검증과 전체 원천32MiB digest budget을 유지한다. native gzip은 원 plain identity와 현재 archive identity를 혼동하지 않으며 full source validator도 기존 archiver/enrollment의 완전 논리 SHA·size·CRC·현재 세대 증명으로 검증한다.

코드 변경/원천 변경/새 cohort/horizon은 기존 cache 계약대로 무효화한다. source-only 재계산·private successor·native 검증을 실제 운영 stage 선택/정책 적용/PID 소비와 구별하고 원 generation은 보존한다. 이전 plain path가 없다는 이유로 raw를 재생성하거나 hash/size 한도를 늘리지 않는다. [현재 리뷰](../audits/postclose-root-cause-recovery-review-2026-10-19.md#수량-통합-검증-즉시-재개와-후보-구분--2026-10-21).


### 동일 날짜 후속 stage의 배포 준비 인계 — 2026-10-21

기존 publish_refresh_quantity_evaluation의 publish_current=False는 운영 정책·공용 committed 참조를 유지하며 같은 날짜의 새 immutable generation을 검증된 후보 코드에만 결속한다. full native report/evaluation/timeout/census/terminal/source 검증 후 원 공용 참조 SHA를 CAS 부모로 포함한 code-addressed stage reference를 같은 commit lock에서 발행한다. 감시·summary는 기존 committed_refresh_stage_path의 공통 bounded parser를 사용하며, 정확한 코드 참조가 손상되거나 부모·날짜·경로·SHA가 달라지면 실패한다. 준비된 코드와 다른 기존 reader는 원 공용 참조를 계속 읽는다. 실제 선택 후 정상 native 발행은 공용 참조와 이미 준비된 같은 코드 참조를 이관하며 원 generation을 보존한다. 실제 정책 활성화/PID/자연 closed 수용은 별도다. [원인·검증](../audits/postclose-root-cause-recovery-review-2026-10-19.md#수량-후속-stage의-후보별-인계--2026-10-21).

### 역사적 수량 결손의 일일 인계 — 2026-10-27

기존 `initial_quantity_monitor_projection` 생산자가 같은 날짜의 committed 후속 세대 또는 native 달력상 직전 거래일의 committed stage에서 승인된 역사 진단을 읽는다. 임의 최신 파일·오래된 임의 날짜로 대체하지 않는다. 현재 날짜의 native stage·census·비용·원천 검증을 먼저 통과한 건만, 원 ID·종목·결손 사유·fact 해시/내용과 대조한다. 공식 비용 조회 구간 확장에 따른 aggregate 해시 변경은 기존 `broker_cost_source.declared_source_bytes`가 보존 원문과 기존 구간의 동일성을 증명하고 거래별 참조도 같은 경우에만 허용한다.

후속 증명은 원 승인 projection의 경로/SHA, 최초 fact 해시, 현재 fact 해시와 필요한 witness를 함께 보존한다. 기존 stage/report, 원 결손 사유와 손익 null은 변경하지 않는다. 새 ID·바뀐 fact/사유·비용 정정·미확인 원문은 현재 결손으로 남으며 현재 검증 실패를 역사 진단으로 넘기지 않는다. 혼합 모집단에서도 검증된 역사 ID만 분리한다.

기존 publisher lock·원천 재검증·불변 세대·코드별 포인터를 사용한다. 실패 후 재시도는 원 승인 바이트를 바꾸지 않고 같은 native 경로에서 재검증한다. 감시 소비자는 원 승인과 직전 stage/projection의 SHA도 자신의 bounded read 경로로 확인한다. 대형 과거 report의 일회성 이관은 기존 4MiB 한도를 넘겨 읽지 않으며, 정확한 witness가 없는 행은 현재 결손으로 유지한다. 새 worker/정책/검증 한도 확대는 없다. 정규 장후→다음 PREOPEN/PID 자연 수용은 현재 `InitialQuantityProducerConsumerRepair1010`에서 계속 확인한다.
