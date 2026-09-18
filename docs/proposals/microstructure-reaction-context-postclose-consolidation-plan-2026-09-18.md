# Microstructure 전용 장후 집계 폐기·현행 판정기 평가 통합 상세계획

작성: 2026-09-18 KST. 상태: **계획 작성 후 사용자 구현·반복 리뷰/검증·commit/push·배포·제한 장후 결과 갱신 지시 수신. 구현/검증과 배포·결과 receipt는 [실행 review](../audit-reports/2026-09-18-microstructure-postclose-consolidation-review.md)를 따른다.**

## 1. 결정·목표·권한

`microstructure_reaction_context`의 대용량 raw 재스캔·구 진입 단계 분석·전용 누적 연구를 독립 정기 장후작업에서 제거한다. 실시간 특징 계산과 holding/entry 안전 guard는 보존하고, 필요한 원천 품질·수집 분모·비용·결과 진단은 기존 기계판정기·보조 AI 평가에 통합한다. 새로운 튜너·후보 grid·collector·정기 job·shadow 평가를 만들지 않는다.

계획 수립 당시 요청은 상세계획 수립이다. 아래 권한 문단은 계획 작성 당시 범위이며, 후속 사용자의 구현·배포·결과 갱신 지시가 해당 실행을 승인했다. 계획과 현재 실행 owner의 계획 참조만 작성한다. 코드 구현, 과거 산출물 삭제, 정책 발행, commit/push, 배포·기동, cron/env/lock/provider/threshold/quantity/cap 변경 및 주문은 실행하지 않는다. 과거 다른 작업의 배포 승인을 이 계획의 실행 승인으로 사용하지 않는다. 구현이 지시되면 구현→리뷰→보완→재리뷰→대상 검증을 단계별 재승인 없이 반복하고, 승인된 후속 실행만 수행한다.

- 원칙 owner: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md). clean baseline은 `2026-06-05T00:00:00+09:00` 이후다.
- 실행 owner: [9/18 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `MicrostructureMachineAuxiliaryNaturalAcceptance0918` 하나를 재사용한다. 아래 MC0–MC6은 순차 작업 묶음이며 별도 OPEN owner를 만들지 않는다.
- 현황 근거: [기존 작업 결과 분석](../audit-reports/2026-09-18-microstructure-reaction-context-result-review.md), [원천·경제성 통합 검증](../audit-reports/2026-09-18-disk-cleanup-and-microstructure-integration-review.md).
- 현재 계약: [장후 결과 리뷰 지침 §5.1.1](../postclose-tuning-result-review-task-instructions.md#511-microstructure의-현행-평가-결속). 이번 문서 작성은 모니터링 지침 호출이 아니다.

목표는 진단 파일 수를 늘리는 것이 아니라 중복 작업을 줄이고 현행 판정기의 비용 차감 경제성 판단에 쓸 수 있는 입력을 유지하는 것이다. 전용 작업 폐기 acceptance에 양의 EV나 실체결 발생을 요구하지 않는다. 경제성 개선 판정은 별도로 닫는다.

## 2. 현재 증거와 변경 필요성

| 항목 | 확인된 사실 | 결정에 주는 의미 |
| --- | --- | --- |
| 전용 장후 실행 | wrapper 기본 활성; 9/17 raw 약5.71GB, wall68.84초, child peak RSS 약215.7MiB | 기존 판정기 평가와 별도로 수행하는 집계 비용 |
| 알고리즘 | 고정 특징 점수·favorable/risk 분류, 구 단계별 전달·미제출 결과 진단 | 가중치/기준을 최적화하는 정책 튜너가 아님 |
| 경제성 | 누적 원천76일 중 포함3일, 독립 기회38, quality-pass13; 고정 추정비용 차감20분 CF 평균−0.803769% | 부분 표본 진단이며 실제 전략 EV·순익·특징 ΔEV가 아님 |
| 과거 결손 | 73일 rollup schema/signature 불일치, outcome/venue/anchor 결손 | 단순 표본 대기만으로 기존 원천이 복구되지 않음 |
| 사용처 | EV/daily/runtime summary 및 source-only workorder; 매수 런타임은 해당 보고서를 로드하지 않음 | 보고서 폐기는 실시간 특징 폐기와 별개 |
| 현행 통합 | 작업본 calibration 전체 case 통계·원천 SHA·같은 날짜 late link 구현 존재; legacy 보고서 없이 최소 보고서 생성 가능 | 전용 raw 작업 없이 필요한 진단 유지 가능 |
| 통합 결과 | 9/16 full-cost CF1,213건; auxiliary 경제성 연결1건. 9/17 verified3,342건은 당일 비용 결손 | source 수리는 가능하지만 현행 정책의 개선 효과 증명은 아직 없음 |

위 숫자는 기존 검증의 as-of다. 새 배포/PID·자연 소비·누적 실현 성과로 해석하지 않는다. 전용 작업 폐기는 음수 CF만으로 결정하는 것이 아니라 독립 정책 산출 부재·현행 평가와의 중복·구 분모 의존에 근거한다.

## 3. MC0 — 변경 경계와 기존 경로 고정

구현 시작 때 git diff·selected managed release·각 wrapper/service의 실제 코드 root를 확인한다. 진행 중 프로세스가 읽는 코드·원천·체크포인트를 보존하고 다른 세션의 dirty 변경을 분리한다. selected source, workspace source, 실제 PID 소비를 서로 대체하지 않는다.

| 소유 파일/경로 | 계획상 역할 | 변경 원칙 |
| --- | --- | --- |
| `deploy/run_threshold_cycle_postclose.sh` | 전용 raw 집계 호출과 실행 표시 제거, 기존 비용/calibration/요약 순서 연결 | 관련 block만 변경; 다른 연구·resource guard·schedule 유지 |
| `src/engine/scalping/microstructure_reaction_context.py` | live builder 및 공용 통합 진단 계약 | live builder 보존; raw-only 연구 코드는 caller 조사 후 제거 |
| `src/engine/scalping/ai_action_outcome_calibration.py` | 현행 기계/보조 AI 수집·사례·full-cost 평가와 late link | 기존 원천·case·holdout/promotion gate 재사용 |
| `src/engine/scalping_feature_packet.py`, `src/engine/ai_engine_openai.py`, `src/trading/market/entry_adverse_flow.py` | 실시간 특징·same-snapshot route·holding/entry 안전 소비 | 이번 폐기를 이유로 특징/guard 삭제·완화 금지 |
| `src/engine/threshold_cycle_ev_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py` | 통합 진단 소비 | legacy 미실행과 modern source gap을 구분 |
| `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py` | 원천 결손 업무 인계·strict 검증 | 기존 handoff 계약을 modern-only 모드에 맞게 전환 |
| `src/engine/monitoring/machine_microstructure_attribution.py`, `deploy/run_machine_microstructure_final_refresh.sh` | 별도 현행 machine/widget lifecycle 귀속·정책 경로 | 이름 유사성을 이유로 폐기하지 않음; 기존 owner 유지 |
| `src/engine/automation/machine_research_closed_loop_refresh.py` | 다른 연구의 기존 종료·비용 경로 | 새 통합 실행 owner로 사용하거나 중복 호출하지 않음 |

새 production 모듈은 기본적으로 필요 없다. 기능 이동이 필요하면 기존 역할 package 안으로 이동하며, live builder를 root wrapper 뒤에 복제하지 않는다. 테스트도 기존 `src/tests` 대상 파일을 우선 사용한다.

산출물: 변경 대상/caller 목록과 짧은 source manifest. closure: 전용 raw CLI, live builder, 현대 calibration, 별도 machine attribution의 경계가 확인되고 미식별 소비자가 없다.

## 4. MC1 — 전용 정기 raw 집계와 구 연구 표면 제거

1. wrapper의 `RUN_MICROSTRUCTURE_REACTION_CONTEXT` 선언·env enable 표면·전용 resource wait·`-m ...microstructure_reaction_context --date` 실행·전용 artifact wait를 제거한다. 기본 false만 바꿔 env로 재활성화되는 상태를 종료점으로 삼지 않는다.
2. terminal marker/실행 계약에는 전용 작업 폐기와 통합 진단 producer를 구분한다. 단일 기존 family flag가 필요하면 의미를 명시적으로 전환하고 verifier도 함께 수정한다. 과거 `true` 값으로 전용 실행을 주장하지 않는다.
3. 전용 raw projector·구 stage funnel·독립20분 favorable 연구·전용 clean-baseline rollup/backfill CLI·해당 source order 생성기의 caller를 조사한다. 공유하지 않는 부분만 제거한다. live 특징/context hash/품질 builder·통합 source binder·summary linker는 남긴다.
4. README/runbook/Plan Rebase/prompt/AGENTS 같은 baseline 문서는 별도 문서 갱신 지시 없이 수정하지 않는다. 관련 운영 지침과 현재 checklist의 owning contract는 코드/automation 변경과 같은 change set에서 갱신한다.
5. 과거 보고서·rollup의 일괄 삭제는 이번 계획의 필수 단계가 아니다. 재사용을 막고 원 as-of 증거를 보존한다. 삭제가 별도로 지시되면 active process·rollback·custody/PnL 증거를 확인하고 전용 파일만 manifest 기반으로 삭제한다. 최소 modern 보고서와 live 원천까지 glob으로 제거하지 않는다.

closure: 정기 wrapper에서 전용 raw CLI가 호출되지 않고 env 값으로 복원되지 않으며, live 특징/holding 안전 및 별도 machine attribution 호출 계약이 유지된다. 기존5.71GB raw를 다시 읽어 확인할 필요는 없다.

## 5. MC2 — 기존 calibration 안에서 가벼운 진단 생산

기본 순서는 다음과 같다.

`당일 비용 source 준비 → verified machine capture 전체 분모 → 기존 case/price labeler → 전체 deduplicated case 통계 → 같은 날짜 modern 진단 → 최종 EV/daily/runtime/workorder → strict verifier/controller`

- 기존 early `--ensure-economic-reference-only`를 재사용한다. AI replay OFF/미호출과 비용 source 확보를 혼동하지 않는다. 원 target date를 자정 후에도 유지하고 과거 날짜에 현재 official master를 소급하지 않는다.
- 전체 capture census는 비용·path 제외 전에 계산한다. case 통계는 상세200행 export 전에 계산한다. exact capture SHA 중복만 수집 분모에서 제거하고, 같은 attempt의 충돌은 기존 계약대로 제외한다.
- snapshot/capture hash·applied bundle·setup/flow hash·symbol·venue/session·cutoff·market-data route/item을 보존한다. 비용의 broker route와 WS 시장데이터 route를 구분한다. integrated/premarket alias 자체를 KRX/NXT/SOR item으로 추정하지 않는다.
- modern section은 기존 부모 calibration JSON의 schema/date/generation/SHA에 결속한다. 별도 raw report가 없어도 최소 dated JSON/MD를 만든다. legacy absence는 `retired/not_applicable`로 표시하며 modern source gap과 구분한다.
- 비용/가격 결손 상태에서도 전체 수집 분모와 제외 사유를 출력한다. empty modern section을 이전 날짜 또는 원 legacy CF로 대체하지 않는다.
- 기존 동일 날짜 보고서가 있으면 legacy 값은 historical as-of로 명시하고 현행 평가·정책 근거에 합산하지 않는다. timestamp만 새로 바꿔 구 통계가 재산출된 것으로 보이게 하지 않는다. 예전 `legacy_reaction_report_not_available` 경고는 의도된 폐기 상태로 전환한다.
- 기존 case labeler의3분 마지막 관측·90초 endpoint lag와 cadence 계약을 유지한다. horizon/정책 exit를 확장하거나 모델 가격을 실제 fill/close로 바꾸지 않는다.

보고 최소 필드: raw/verified unique capture 수, invalid/conflict/cost/path 제외 수, case/evaluable outcome 수, bundle·venue/session·action·AI prompt/verdict partition, source usable 수, CF 비용 차감 평균/tail와 metric 정의, 부모 path/SHA, status/reason, runtime/apply 권한 false. 실제 미확보 손익과 인과 ΔEV는 null이다.

closure: legacy report가 없는 작은 fixture에서도 modern JSON/MD가 생성되고, capture/case/결과 분모가 검증된 부모와 일치한다. full-cost0건은 source gap이며 no-edge가 아니다.

## 6. MC3 — 소비 계약·실행 순서·결손 handoff 전환

현재 wrapper는 비용 source-only 선행 실행과 후행 calibration 본 실행을 구분하며 EV/daily 요약이 여러 시점에 생성될 수 있다. 전용 block 삭제만으로 끝내지 않고 **마지막 유효 부모를 최종 소비자가 읽는지** 확인한다.

1. EV/daily/runtime 요약은 `machine_primary_auxiliary_evaluation`을 현행 진단으로 소비한다. 구 favorable/AI 점수 단계 통계는 legacy as-of 또는 N/A다. 구 통계 부재를0% 전달 실패·필수 report 누락으로 바꾸지 않는다.
2. 마지막 calibration의 SHA와 세 요약의 parent SHA를 비교한다. 기존 duplicate-refresh/source dependency 목록에 modern report/부모가 빠져 있으면 추가한다. 날짜만 같거나 생성시각이 새롭다는 이유로 재사용하지 않는다.
3. 기존 downstream refresh 경로를 우선 사용한다. 필요한 consumer만 한 번 갱신하고 calibration/정책 grid/raw 연구 전체를 추가 실행하지 않는다. daily에 이미 존재하는 다른 section·source hash를 잃는 부분 덮어쓰기를 하지 않는다.
4. workorder에는 현행 producer가 확인한 exact-date 결손만 기존 native order 계약으로 전달한다. 하나의 원인/source identity를 여러 평가 행이나 세 요약에서 중복 업무로 만들지 않는다. retired ADM anchor/compact AI가 요구하지 않는 raw payload를 복원 업무로 생성하지 않는다.
5. modern source gap이면 owner artifact·affected cohort/count·원인·다음 조치·closure test를 남긴다. row/cohort가 식별되면 해당 부분만 제외하며 무관한 정책 전체를 차단하지 않는다. 필수 active handoff 자체가 invalid한 경우에는 기존 strict gate로 실패한다.
6. `_microstructure_diagnostic_handoff_status`와 실행 flags를 함께 검토한다. modern-only report를 정상 검사하고 legacy required coverage/order를 강제하지 않는다. 현대 source 존재를 선언했는데 파일/부모 SHA/인계가 없으면 fail; calibration가 지시된 OFF이면 disabled, enabled인데 source gap이면 명시적 gap이다.
7. 최종 native source→control tower/checklist→strict verifier `--require-summary-handoff`→controller의 기존 종료 계약을 유지한다. verifier/controller self hash는 summary 입력에 넣지 않는다. 계약 전환을 핑계로 verifier warning/실패를 성공으로 바꾸지 않는다.

closure: modern-only, modern cost-gap, disabled, parent-hash 변경의 네 경우가 각기 올바른 상태로 세 요약/workorder/verifier에 인계된다. 전용 작업은 retired지만 현행 필수 인계 실패가 숨겨지지 않는다.

## 7. MC4 — 경제성 평가와 현행 튜닝의 연결

### 7.1 진단과 개선 판단 분리

| 평가 층 | 측정값 | 허용 결론 |
| --- | --- | --- |
| source/분모 | 전체 capture, 제외/연결/usable 수 | 수집·소비 계약 정상 여부 |
| 기존 가격 CF | 같은 cutoff/venue의 관측 경로에서 검증 비용 차감 평균·tail | 놓친/차단된 경로의 기술적 진단 |
| 기존 owner의 독립 정책 비교 | 동일 기회·비용·체결/exit 계약에서 다른 effective policy의 paired 결과와 holdout | 해당 owner가 규정한 model ΔEV/순익 개선 판단 |
| 실제 적용 성과 | applied version별 실제 COMPLETED·정산 비용·episode 손익 | 실제 비용 차감 EV·순익·노출·tail |

source-bound cases가 많거나 BLOCK 경로 평균이 음수라는 사실만으로 특징의 ΔEV가 양수라고 판정하지 않는다. 같은 정책의 자기 비교도 개선0 또는 incumbent 보존이다. 보조 AI는 machine ENTER_NOW·실제 provider 호출·정상 semantic verdict·exact snapshot join인 기회만 평가하며 미호출은 N/A다.

### 7.2 튜닝 역할

microstructure 전용 후보 producer/publisher/PREOPEN family는 만들지 않는다. 기존 기계/보조 AI owner가 해당 feature를 실제 사용하고 기존 후보 계약에 비교 축이 있으면 그 안에서 동일 source의 calibration→고정 후보→기존 holdout 평가를 수행한다. 원 grid·floor·cost·stress/tail·promotion guard를 유지한다. 단순 진단 연결에 새20건/양의ΔEV 허들을 추가하지 않는다.

기존 owner에 feature 변경 비교 축이 없으면 `feature_incremental_effect_not_identified`로 닫는다. 이를 해결하기 위해 자동으로 새 grid·실시간 shadow·canary를 만들지 않는다. 그때만 실제 제출 병목/오류와 연결된 한 가지 비교 가설을 후속 owner 작업으로 제시한다. 안전 guard OFF 비교는 live 실행하지 않는다.

기존 selection/publisher/PREOPEN/rollback 계약을 통과한 정책만 기존 경로에서 자동 적용될 수 있다. 이번 통합 진단은 `runtime_effect=false`, `allowed_runtime_apply=false`를 유지한다. diagnostic의 false가 별도 승인된 live owner를 OFF시키지는 않는다.

### 7.3 실제 성과·모델 오차

기존 custody/order/episode 원장에서 실제 적용 버전을 join한다. 날짜별 보고서 중복·event 재전송·동일 episode 재집계를 제거하고 실제 unique 완료 episode를 rolling/cumulative에서 각각 한 번만 집계한다. owner·real/sim/probe/CF·full/partial fill·venue/session은 분리한다. 여러 날에 걸친 보유분은 완료일 실제 PnL에 한 번 귀속하고 일별 노출 시간은 별도로 계산한다.

episode 중 정책 버전이 바뀌면 entry 적용 버전과 이후 변경 이력을 함께 보존한다. 같은 손익을 버전마다 복제하지 않고 mixed-version 표본을 별도 표기한다. 효과 귀속이 불가능하면 단일 버전 causal 비교에서 제외하되 실제 총손익 원장에서는 유실하지 않는다.

기존 원천으로 계산 가능한 비용 차감 equal-weight/notional-weighted EV, 실제 원화 순익, sample/유효 관측일, 실제 loss quantile/tail, 최대 노출/자본·보유시간을 보고한다. 근거 없는 capital occupancy·원화 비용·tail은 null과 gap으로 둔다. 원천에 이미 정의된 rolling window를 사용하며 새 임의 기간/허들을 추가하지 않는다.

모델 오차는 같은 episode·수량/비용·exit/horizon 정의의 예측이 실제 결과와 연결된 경우에만 실제−모델을 계산한다.3분 관측 CF와 며칠 후 완료 손익의 차이를 모델 오차라고 부르지 않는다. 실제 이익과 모델 ΔEV는 별도 필드/분모이며 합산하지 않는다.

closure: 비용·적용 버전·완료 lineage가 유효한 표본만 실제 성과에 들어가고, 아직 그런 표본이 없으면 acceptance는 OPEN/null이다. 구현 closure 또는 배포 receipt를 경제적 성공으로 바꾸지 않는다.

## 8. MC5 — 최소 검증·반복 리뷰

우선 기존 테스트의 관련 cases를 선택한다. 아래 목록은 후보이며 무조건 전체 실행하는 명령이 아니다.

| 검증 범위 | 기존 대상 | 확인할 계약 |
| --- | --- | --- |
| modern producer/linker | `src/tests/test_ai_action_outcome_calibration.py`, `src/tests/test_microstructure_reaction_context_report.py` | legacy 없이 생성, 전체 분모/200행 전 통계, 비용 결손, cutoff/venue/route, source SHA |
| live 기능 보존 | `src/tests/test_microstructure_reaction_context.py`, `src/tests/test_entry_adverse_flow.py` | 특징/holding/entry fail-closed 유지, integrated/premarket source routing |
| consumer/workorder | `src/tests/test_threshold_cycle_ev_report.py`, `src/tests/test_daily_threshold_cycle_report.py`, `src/tests/test_runtime_approval_summary.py`, `src/tests/test_build_code_improvement_workorder.py` | modern-only/N/A/누락/변경 부모, 최종 SHA 일치, native order dedup |
| strict closure | `src/tests/test_verify_threshold_cycle_postclose_chain.py`, `src/tests/test_postclose_summary_handoff.py` | 의도된 retirement 허용, active handoff 실패 검출 |
| wrapper | 기존 shell contract 검사와 작은 stub fixture | legacy raw 호출0, calibration OFF/source gap/최종 refresh 순서, target date 유지 |

기존 테스트가 old CLI 존재를 고정하면 폐기 계약으로 수정한다. 제거한 구현을 그대로 복제하는 테스트는 만들지 않는다. 필요한 fixture는 기존 테스트 파일에 추가하고 실제 raw5.71GB·broker/provider·알림 호출을 사용하지 않는다. 이름이 비슷한 attribution/policy 경로가 변경되지 않았으면 전체 suite 재실행 대신 호출/import 경계 확인으로 보존 여부를 검증한다.

Python 변경 파일 compile/import, wrapper `bash -n`, `git diff --check`, 문서 링크/owner/authority와 print-only parser를 검증한다. 실패하면 관련 수정→리뷰→검증을 반복한다. 통과 후 새로운 defect/변경이 없으면 전체 테스트·기존368PASS 재실행·성능 benchmark를 추가하지 않는다.

성능 acceptance는 전용 raw CLI 호출과 전용 scan bytes가0이고 기존 한 번의 case 평가를 재사용한다는 실행 증거다. 총 장후 시간 감소를 단일 날짜 wall 차이로 단정하지 않는다. 최초 자연 실행의 기존 PERF receipt로 비용을 확인하고 의심되는 regression이 있을 때만 제한 측정한다.

closure: 관련 producer/consumer/guard/strict 인계에 미해결 in-scope finding0, 대상 검증 통과, 생략한 검증·잔여 자연/경제성 acceptance 명시.

## 9. MC6 — 승인된 배포와 자연 확인

구현 완료 후 배포가 지시되면 변경 파일·검증 증거를 동결하고 기존 clean managed release 절차를 사용한다. 관련 기존 source-only 수리를 포함하는지 명시하고 다른 dirty source/별도 machine/widget/저가주 연구 변경을 무심코 합치지 않는다. 진행 중 작업은 기존 source로 완료하게 하고 다음 정상 스케줄에 적용할 수 있으면 그 경계를 우선한다.

전용 장후 wrapper/보고 경로만 바뀌면 trading bot 재기동을 필수로 만들지 않는다. live route 보완 등 실제 runtime source가 함께 배포되면 해당 권한·기존 graceful startup 절차와 current PID 소비를 별도로 확인한다. 정지 cron 복원·전체 장후 재실행·lock/env 수동 교체를 배포의 암묵적 단계로 넣지 않는다.

첫 자연 실행 확인 항목:

1. original target date·selected source·실제 wrapper code root가 일치하고 전용 raw job이 호출되지 않는다.
2. 같은 날짜 early cost source와 verified capture 분모가 확보되며 결손은 원인별 제외된다.
3. 마지막 calibration→modern 보고서→최종 EV/daily/runtime/workorder가 같은 parent SHA를 소비한다.
4. legacy absence는 retired/N/A이고 필요한 현대 source gap은 숨기지 않는다. strict verifier/controller 종료가 유효하다.
5. 실제 정책 후보·PREOPEN·PID·자연 행동은 기존 owner에서 별도로 확인한다. 이 통합 자체는 새 정책을 생성하지 않는다.
6. 성숙한 실제 완료 episode가 생긴 경우에만 기존 성과 경로에서 version별 비용 차감 EV/순익/tail/노출/모델 오차를 평가한다.

첫 자연 실행에서 source gap이 발견되면 같은 입력을 무한 재실행하지 않는다. 다음 표에 따라 수리 가능성과 증거 손실을 구분한다.

| 상태 | 다음 조치 | closure test |
| --- | --- | --- |
| enabled producer/cost/late link 누락 | 현행 wrapper/producer 계약 수리 | 같은 날짜 원천·부모 SHA·최종 소비 재현 |
| target-date 원천의 역사적 소실 | retained provenance만 제한 확인; 없으면 irrecoverable/null | 제외 이유/영향 분모 보존, 소급 master·가짜 outcome 없음 |
| 유효하지만 결과 미성숙 | 기존 horizon/terminal 성숙 대기 | 동일 기회의 새 source-valid 결과 연결 |
| 유효 경제성 비교에서 후보0 | incumbent 유지; 실제 비교 수와 탈락 사유 확인 | 동일 정책 자기 비교·source gap과 분리된 기존 hold_no_edge |
| 비교 축/사용 authority 없음 | 진단 종료 또는 기존 owner의 후속 가설 제시 | 독립 튜너/승격 권한이 만들어지지 않음 |
| 실제 결과 미확보/비용 미정산 | 경제성 acceptance OPEN/null | unique 완료 episode·비용 정산·버전 결속 |

## 10. 완료 산출물과 후속 실행 지시

최종 보고는 전용 정기 작업 제거 범위, 보존한 live/안전/별도 attribution 경로, modern 소비/strict 계약 변경, review findings와 수리, 대상 검증·생략 검사, 배포/자연/경제성 상태를 구분한다. source commit/release/PID receipt가 있는 경우만 각각 제시한다. 기존 과거 PnL을 복원한 값은 신규 발생 이익으로 보고하지 않는다.

구현 지시 예시:

> 이 계획의 MC0–MC5를 구현하라. 전용 raw 장후 집계를 제거하고 현행 calibration의 modern 진단·최종 consumer·strict handoff를 유지하라. live 특징/holding·entry 안전 guard와 별도 machine microstructure attribution/정책 경로는 보존하라. in-scope 코드리뷰·보완·재검증을 완료까지 반복하고 변경과 증거를 전달하라. 전체 연구 재실행·새 튜너/grid/shadow·provider/주문·cron/env/lock/threshold/cap 변경은 실행하지 말라.

배포까지 원하는 경우 추가 지시 예시:

> 검증 완료 변경을 다른 세션 변경과 분리하여 커밋·푸시하고 기존 managed release 절차로 배포하라. 현재 진행 중 작업의 source를 보존하고 다음 정상 실행에 적용하라. 실제 live source 교체로 필요한 기동은 승인한다. 정지 schedule 복원과 비싼 전체 장후 재실행은 하지 말라. MC6의 자연 인계와 기존 applied-version 실제 완료 성과는 확보된 증거만 보고하고 부족한 원천/미성숙 결과는 OPEN으로 남겨라.

