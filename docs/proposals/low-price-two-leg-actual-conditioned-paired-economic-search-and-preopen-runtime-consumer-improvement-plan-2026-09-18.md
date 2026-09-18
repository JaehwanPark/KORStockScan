# Low-price two-leg actual 튜닝 — paired 경제성 탐색·PREOPEN 자동 소비 상세계획

작성: 2026-09-18 KST. 상태: **LP-A0–A7 구현·반복 리뷰·제한 재생성 완료 / 다음 정상 PREOPEN·자연 적용·실제 개선 Acceptance OPEN**. 최종 증거: [구현 종결](../audit-reports/2026-09-19-low-price-actual-paired-implementation-closure.md).

## 1. 목표·범위·종결 원칙

`monitoring.low_price_two_leg_tuning`을 실제 실적 확인과 기존 정책 보존에 사용하면서, 기존 economic replay를 통해 검증한 **서로 다른 정책의 비용 후 EV·유효 관측일당 순익 개선**을 다음 정규 PREOPEN에 전달한다. 구조 결손→경제성 비교→정책 전달/자연 소비→실행시간 순으로 구현한다.

완료 조건은 보고서 생성이 아니라 **actual 원천→paired 평가→선정→dated candidate→공통 PREOPEN applied 파일→서비스/machine의 같은 정책 소비→완료 비용 성과**가 연결되는 것이다. 개선이 입증된 날은 검증된 bounded 정책을, 미성숙·no-edge·source gap인 날은 검증된 incumbent 보존 정책을 생성한다. 양수 개선안 생성은 보장하지 않는다. 불확실성을0이나 성공으로 바꾸지 않는다.

최초 문서는 계획 수립 범위였다. 이후 사용자가 구현·반복 리뷰·commit/push·배포 및 다음 장전 정책 준비를 승인하여 아래 구현을 실행했다. 주문·거래 프로세스 restart·조기 PREOPEN 권한을 추가하지 않는다.

- 원칙: [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), clean baseline `2026-06-05T00:00:00+09:00`, `main-only/normal_only/post_fallback_deprecation`.
- 현황 근거: [Final 재리뷰·actual 튜닝 분석](../audit-reports/2026-09-18-observation-final-rereview-and-low-price-two-leg-tuning-analysis.md), `tmp/observation-final-rereview-low-price-20260918/`.
- 기존 연구와의 분담: [expanded 연구 LP0–LP6](low-price-two-leg-expanded-candidate-economic-logic-improvement-plan-2026-09-18.md)은 이미 구현한 policy identity·0/null·held·독립 challenger/paired 의미의 소유자다. 재구현하지 않고 재사용한다. 이 계획은 **actual 조건부 탐색·승격 계약·PREOPEN 소비**의 남은 연결을 담당한다.
- 실행 owner: [9/18 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 기존 low-price family `LowPriceExpandedResearchRepair0918`에 상세 package로 연결한다. LP-A0–A7은 별도 checkbox/일정 owner가 아니다. 다음 실행일 이관 시 동일 ID·Acceptance·History를 유지하고 한 parsed owner만 둔다. 완료된 LP0–LP6을 표본0 때문에 재개하지 않는다.
- 초기 replay 범위는 실제 체결 실적이 있는 기존 profile과 두 entry filter다. 종목/session/profile 확대·수량·목표·lookback·유효bar·손절/강제청산·Main AVG_DOWN/PYRAMID·widget/manual custody 변경은 포함하지 않는다.

## 2. 현재 확인한 결손과 재사용 경계

검증 기준 source는 selected immutable `35947abb64e8c920424c56670544e4fab19ffe5e`다. 후속 구현 직전 selector/source와 병행 변경을 다시 확인한다. Canonical workspace가 dirty이므로 그 diff 전체를 배포 source로 삼지 않는다.

| 지점 | 현재 동작 | 필요한 최소 보완 |
|---|---|---|
| Actual producer |최신9/16 actual v8;9/17 보고서/후보 없음 |기존 producer로 dated terminal 결과를 명시적으로 생성·후행 소비; 복구 불가 원천은 gap 유지 |
| Actual admission |flags/status/SHA 확인, 내부 날짜/type/final freshness 자체 검사 없음 |기존 shared source gate의 exact-date/content 역할 적용 |
| Subset 진단 |최대2개 엄격한 필터 부분집합 비교; 신규 승격 retired |진단은 보존, causal 선정은 existing replay 결과로만 수행 |
| Existing replay |`existing_axis_economic_replay`가 두 필터를 replay; 동일 전체 기간 비교, source-only |Actual applied baseline·시간순 calibration/독립 holdout·execution/capital 증거 결속 |
| Candidate v3 |source actual v7/v8, prior 정책 그대로; mutation 있으면 `candidate_subset_promotion_authority_retired` |v3 보존 의미를 유지하고 검증된 paired 결과용 명시적 successor 계약 추가 |
| Policy 발행 |`run_low_price_two_leg_preflight.sh`가 profile 기동 전 apply 실행 |공통 PREOPEN에서 한 번 발행, profile preflight는 frozen 파일 재검증 |
| Runtime |service 시작에서 exact-date policy 로드→profile hash→machine |Entry 적용값·release/PID·기존 재고 policy custody를 검증하고 post-apply 귀속 연결 |

Native source9/17은 publication9/18/effective9/21과 구분한다.9/18 applied 파일은 source9/16/정책 변경0이다.9/21 exact-date applied 파일의 정규 PREOPEN 전 부재는 실행 결함이 아니다. 최근 current epoch 합계139 episode/80 완료 leg/16 held·unresolved와 exact 비용10/추정70은 현황이며 신규 개선 증거가 아니다.

## 3. LP-A0 — 원천 동결·dated native 결과 복구

1. Native source date, release/implementation, actual state/snapshot, 기존 report/candidate/applied, broker/order ownership, final audit/binding, bar/cache·capital·same-stage receipt의 path/SHA/as-of를 기존 manifest에 기록한다. Active writer/lock과 현재 입력을 보호한다.
2.9/17 보고서가 없어진 최초 경계를 wrapper marker·status·native CLI 결과에서 식별한다. 이력에 있는 resource/predecessor 실패를 새로 확인하지 않고 직접 원인이라고 단정하지 않는다. Full wrapper rerun 대신 그 producer와 영향받는 후행 consumer만 대상으로 한다.
3. Target-date state/archive가 복구 가능하면 actual row를 생성한다. 현재 날짜 state를 과거 날짜로 바꾸거나9/16 결과를9/17 실적으로 재봉인하지 않는다. 복구 불가는 `source_gap` row/원인/관측 분모로 종결하며 actual EV=null이다.
4. 현행 profile의 actual 체결 실적이 전혀 없으면 `valid_empty_no_fill` 또는 source gap을 구분한다. Cheap census와 보존 정책까지만 수행하고 expensive paired replay는 생략한다. 실제 체결이 있어도 completed/cost/terminal이 없으면 진단만 한다.
5. 보존 정책 출처는 유효한 실제 applied artifact다. Missing/invalid incumbent provenance를 compiled baseline으로 바꿔 실제 적용이라고 보고하지 않는다. 기존 missing/stale fallback만 별도 명시하고 malformed/tampered artifact는 fail closed한다.

Closure: dated native JSON/MD/candidate가 정상 생성되거나 exact gap으로 명시 종결됨; 모든 profile이 하나의 disposition에 대사됨; 역사/현재 state와 ledger 변경0; source와 publication/effective 날짜를 후행 consumer가 구분함.

## 4. LP-A1 — actual admission·비용·표본 수리

기존 `automation.source_quality_hard_gate.load_source_quality_preflight(..., require_final=True)`와 final reusable 계약을 재사용한다. Internal target_date/report_type/schema/status, artifact SHA, raw generation/projection 및 dependency freshness가 일치해야 새 economic intake를 허용한다. Source input 허용을 전체 운영 terminal·경제성 허용으로 해석하지 않는다. 무관한 main PASS gap으로 independently reconciled low-price profile의 실제 실적을 전역 폐기하지 않는다.

Actual profile별 broker entry/exit·owner·venue/session·policy version·full/partial fill을 대사한다. `COMPLETED + valid profit_rate/cost`만 실제 성과에 넣고 proxy·CF·수동 exit를 별도 cohort로 유지한다. Exact ka10073 attribution은 기존 symbol/day/수량/매입·매도 평균가/commission·tax의 유일 매칭 계약을 사용한다.0.23% fixed 추정은 별도 cost source이며 exact 비용으로 이름을 바꾸지 않는다. 수동 청산 손실을 제외해 양수 결과를 만들지 않는다.

Actual 탐색 eligibility는 기존 source-valid 관측5일·broker 가격 완료8 leg와 flat/terminal 계약을 유지한다. Episode와 leg를 각각 집계하고 profile/적용 구간/거래 venue를 섞어 floor를 채우지 않는다. Coverage 결손은 전역 차단 대신 식별 가능한 row/window를 manifest로 제외한다. 양측 비교의 공통 날짜는 성과를 보기 전에 정하며 좋은 날짜만 추려서는 안 된다.

Closure: 다른 날짜의 allowed=true audit, stale final, SHA/content 불일치, missing cost, ambiguous owner, partial/held/no-fill fixture가 구분됨; 현재 정책 구간과 수동 손실 귀속이 원 ledger로 대사됨. 기존 live API 요청/parser/FID를 수정해야 하는 별도 결함이 나오면 official Kiwoom reference gate를 먼저 적용하며 이번 계획으로 protocol 변경을 추정하지 않는다.

## 5. LP-A2 — 기존 replay 재사용과 실행 가능한 비교

**Subset 진단을 causal 결과로 승격하지 않는다.** `low_price_two_leg_entry_spot_research.existing_axis_economic_replay`, `evaluate_candidate`, `paired_economics`, 현재 completed-bar/cache/context를 재사용한다. Expanded 전체204종목/1,020profile grid·시장 이력 조회·보고서 전체 재계산은 요구하지 않는다. Actual eligibility profile에 한해 두 filter axis의 기존 bound만 평가한다.

Baseline은 해당 actual 정책 epoch의 실제 applied policy/hash다. Compiled baseline과 다르면 기존 profile/SpotCandidate 변환 경로에서 실제 값을 결속한다. Quantity, target, offsets, lookback, 유효bar, scan/session/venue, execution/cost version은 양측 동일하게 유지한다. Alternative는 **한 profile의 한 axis**를 기존 bound 안에서 엄격하게 조정하며 threshold 완화/두 축 동시 변경은 금지한다.

두 arm은 같은 immutable signal/quote/bar 입력, opening inventory/cash/reservation, 주문 validity·거래일/시간, capital limit·same-stage owner를 사용한다. 두 leg의 주문→full/partial/no-fill→target/actual manual exit→다음 기회/자본 해제까지 시간순으로 replay한다. Baseline 거래를 거절한 뒤 생기는 다음 진입을 당시 기록된 관측 stream에서 다시 찾는다. 해당 관측·BBO/체결 모델·자본 원천이 없으면 `execution_source_gap`/`capital_source_gap`으로 보류한다. 실제 거래 몇 개를 삭제하거나 무제약 가상 cash를 공급하지 않는다.

기존 bar replay는 **CF/model**이며 real broker fill이 아니다. `live_replay_supported=True`라는 enum만으로 실제 execution 동등성 검증을 대체하지 않는다. Price touch, 보수적 carry, `low_price_original_target_continuation_price_touch_cf_v1` 결과는 source-only다. 다음 날 carry 청산은 기존 target/order custody 계약과 실행 원천으로 증명할 때만 인정하고 bar-touch를 actual COMPLETE로 바꾸지 않는다. Current runtime의 target/reconcile/roll/custody와 다른 모델이면 원인·권한 차이를 기록한다.

원천 capture는 별도 수집기 대신 기존 machine과 `src/utils/pipeline_event_logger.py:emit_pipeline_event`의 공개 인터페이스를 사용한다. Shared base machine의 `_record`는 state audit를 최근100개만 유지하므로 이를 전체 시간순 관측 stream으로 간주하지 않는다. 기존 stage/field 계약으로 충분한지 먼저 확인하고 부족한 필드만 low-price producer에 추가한다. Completed-bar/entry 판단·fill/exit transition 시 profile/episode/leg/order owner·logical date/as-of·venue/session·policy hash·필터값·원 bar/cache identity·기존 호출로 이미 받은 quote/execution·cash/reservation source identity를 남긴다. 다음 기회는 체결 거래뿐 아니라 당시 관측한 filter 결과도 보존해야 재구성할 수 있다. 틱 전량 복제·추가 API polling은 하지 않으며 quote/capital이 당시 없었다면 unavailable이다. Pipeline verbosity 점검은 병행 세션 소유이므로 logger compaction/운영 정책을 수정하지 않는다. 필수 경제 lineage가 lossless로 보존되는 기존 계약인지 writer→raw/projection path→actual reader→replay manifest를 검증하고 보장이 없으면 승격 blocker로 남긴다. 새 stage가 필요하면 기존 native schema/source-quality field contract에 함께 선언한다.

실행 모델은 실제 체결 episode에 결속한 입력과 broker receipt로 기존 baseline의 order/fill/exit를 재현 검증한다. 미선택 arm의 가격/queue/latency 추정과 stress contract는 실제 증거와 분리한다. 미정 비용·슬리피지·exit 모델은0으로 대체하지 않는다. 이 준비가 닫히기 전에는 재생성 결과가 candidate research 및 incumbent carry까지만 도달한다.

Closure: 실제 applied baseline hash 재현; 양측 동일 날짜/예산·다음 진입/자본 점유 경로 대사; actual/CF/proxy 불혼합; bounded state audit와 durable capture의 분모 대사; source가 없는 경로를 성공으로 만들지 않음. Framework/service/병렬 alpha 모델을 신설하지 않는다.

## 6. LP-A3 — EV·일별 순익 동시 개선과 독립 검증

지표는 기존 경제 계약을 재사용한다.

- `notional_weighted_ev_pct = 100 × Σ유효 완료 net / Σ해당 executed entry notional`. Actual·CF/model·정확/추정 비용, full/partial fill을 구분한다.
- 일별 순익은 같은 사전 고정 source-valid 관측일의 비용 후 순익합/일수다. 정상 flat/no-trade0은 포함하지만 held/carry·source gap의 미확정 손익은0이 아니다. Entry cohort EV와 exit-date cash 실현 귀속은 분리한다.
- 동시 개선은 **distinct policy, resolved terminal/cost, 양측 유효 EV, ΔEV≥기존0.005%p, Δ순익/일>0, 양수 후보 EV**가 모두 필요하다. No-fill baseline EV=null인 참여효과는 별도 분류하며 joint 개선으로 세지 않는다.
- 미청산/tail/MAE·capital occupancy·same-stage 계약은 기존 guard를 유지한다. CF 합계나 win rate를 primary EV로 바꾸지 않는다. Cost stress 조건은 기존 증거 계약을 사용하며 임의 완화·새 universal uplift floor를 추가하지 않는다.

Calibration/holdout은 기존 research owner의 시간순 계약을 적용한다: 최소 calibration30거래일/holdout16거래일, calibration6 episode/8 leg 및 holdout3 episode/4 leg floor. Actual 관측5일/8 leg floor는 이를 대체하지 않는다. Actual epoch 성과와 그 정책을 적용한 clean market replay 기간을 별도로 명시한다. 해당 epoch의 실제 source 부족과 model coverage를 혼합하지 않는다.

최대2개 대안을 calibration에서만 평가해 joint 경제조건을 통과한 distinct challenger1개를 고정한다. Baseline rank1은 보존 판단이고 개선 검증 성공이 아니다. 후보가 없으면 보존한다. Profile 간 next-policy 순위도 calibration 기준으로 고정한 한 profile/axis만 unused holdout에 확인한다. 확인된 holdout으로 다른 profile/후보를 바꿔 적용하지 않는다. 이미 본9/17 holdout은 exploratory이며 새 독립 승격 증거가 아니다. 신규/미사용 window가 부족하면 `hold_unused_holdout`다.

Family의 실제 execution-quality 계약 및 기존 승인·canary/post-apply 조건이 없으면 양수 CF 결과만으로 자동 real 승격하지 않는다. 기존 canary가 요구되는 경우 stage 단일 owner·N_min·적용/미적용 contamination 및 rollback 계약을 명시한 뒤 한 profile/axis의 bounded canary policy만 다음 PREOPEN에 선택한다. N_min은 기존 family floor/owner에서 확인하며 미정이면 보류한다. 새로운 alpha를 shadow-only로 여는 경로는 만들지 않는다. Full 전환은 자연 post-apply actual 경제성·guard acceptance 이후다.

Disposition은 `incumbent_preserved`, `valid_empty_no_fill`, `hold_sample`, `hold_inventory_custody`, `source_gap`, `self_comparison`, `measured_no_edge`, `hold_unused_holdout`, `hold_execution_confirmation`, `eligible_bounded_canary`, `eligible_paired_policy`로 분리한다. 단순 개선0 대신 각 단계의 tested/eligible/blocked·전후 값·owner/closure를 대사한다.

Closure: self/held/flat/proxy 비교가 joint 개선 집계에서 제외됨; 학습 challenger 및 profile 선택이 holdout 전에 고정됨; 실제 execution/canary 권한이 CF flag만으로 열리지 않음; 동일 policy/date/cost에서 계산 재현 가능.

## 7. LP-A4 — 단일 선정·candidate successor 계약

기존 candidate v3의 subset promotion retired 규칙을 삭제하거나 `ready=False`만 True로 바꾸지 않는다. 기존 validator/writer에 **`low_price_two_leg_policy_candidate_v4`** paired successor를 추가하는 방안을 채택한다. Actual report는 필요한 새 section/계약 변경에 맞춰 v9로 올리고 v7/v8·candidate v3는 역사/보존 reader로 유지한다. 새 Python CLI/root module은 만들지 않는다.

V4 필수 계약: source/publication/effective date, actual report hash, final audit hash/binding, applied baseline artifact/hash·policy identity, calibration 선정 manifest, unused holdout receipt, execution/capital/cost/authority version 및 hash, baseline/challenger identity·changed fields, disposition, policy_mutations, incumbent policies, selected profile/axis, owner conflict/rollback.

Postclose candidate 자체는 계속 `runtime_effect=False`, `allowed_runtime_apply=False`, `actual_order_submitted=False`다. Candidate ready는 **PREOPEN intake eligibility**이며 실주문 permission이 아니다. Explicit paired authority로 검증된 payload만 새 조건을 고를 수 있다. 전부 탈락한 날도 전체 profile의 유효 incumbent copy와 reason을 담은 carry candidate를 생성한다. Empty profiles/zero fallback으로 native loop를 끝내지 않는다.

Source gap carry는 입력 품질을 pass로 꾸미지 않는다. 유효 incumbent artifact·hard authority·custody가 독립 검증됐고 mutation0일 때 보존 reader가 명시적으로 받는다. Bad audit/schema를 통과시킨 뒤 새 조건을 적용하는 우회는 금지한다. Incumbent도 invalid면 exact blocker를 발행하고 해당 신규 entry를 차단한다. 기존 verified baseline missing/stale fallback과 malformed candidate 처리는 분리한다.

`validate_candidate`는 선언된 ΔEV/Δ순익·ready를 신뢰하지 않고 source/actual/replay/holdout proof의 canonical hash와 재계산된 비교, baseline match, 한 profile/axis mutation, unchanged execution fields, family authority를 검사한다. Applied schema는 기존 구조가 충분하면 유지하며 새 selection/proof/date 필드만 reader/writer/strict에서 일치시킨다. 의미가 바뀌는 곳만 version을 올린다.

Closure: v3 subset mutation은 계속 거절; v4 forged economics/date/hash·wrong baseline·stale holdout·extra axis/quantity/target mutation은 거절; valid carry 및 실제 승인 경계를 닫은 positive fixture는 같은 producer→validator→apply 경로에서 성공. Positive fixture 성공은 실제 market EV 개선 증거와 분리한다.

## 8. LP-A5 — 장후 재생성·PREOPEN 단일 발행·runtime 소비

연결 순서는 다음 하나로 고정한다.

```text
final audit + actual state/receipts + cached replay evidence
  -> low_price_two_leg_tuning actual/paired decision
  -> dated candidate v4 (source_date=D, effective_date=next KRX trading day)
  -> daily EV/runtime summary/tower/checklist/strict intake
  -> normal PREOPEN low_price_two_leg_policy_apply --target-date effective_date
  -> exact-date applied policy (mutation or verified carry)
  -> profile preflight -> service load -> machine entry policy hash
  -> actual broker terminal/cost -> next postclose attribution
```

`deploy/run_threshold_cycle_postclose.sh`의 기존 final 이후 actual producer 한 번과 필요한 replay dependency를 연결한다. Existing cache/완료 checkpoint와 immutable receipt를 재사용한다. 실제로 쓰는 replay section만 갱신하며 unrelated expanded grid, 다른 세션 producer, 전체 wrapper를 재실행하지 않는다. Stage marker에는 completed_with_gap/valid_empty/carry/selected를 명확히 기록한다.

`deploy/run_threshold_cycle_preopen.sh`의 existing native automation 순서에 기존 `low_price_two_leg_policy_apply`를 **한 번** 추가한다. Next trading day는 project calendar/KST에서 정하고 effective date가 caller target과 다르면 거절한다. 공통 적용은 가장 이른 profile preflight/entry 이전 정상 PREOPEN 창에서 수행한다. 실제 cron/systemd timing과 main startup predecessor를 확인해 기존 checklist 시간창에 배치한다. 추가 독립 timer/daemon은 기본으로 만들지 않는다.

기존 `data/runtime/low_price_two_leg/policy_apply.lock`과 atomic writer를 재사용한다. Profile별 preflight는 같은 날짜/hash의 frozen applied 파일을 검증하는 idempotent fallback이다. Same-date 기존 파일이 있으면 기존 freeze 규칙대로 검증 후 유지하며 overwrite하지 않는다. 다른 candidate generation을 섞거나 profile별로 서로 다른 global policy를 발행하지 않는다. 효과가 다음 장전이어야 하므로 그 날짜 파일이 최초 발행되기 전에 최종 candidate와 proof를 준비한다.

PREOPEN은 exact source/effective date·age·profile set·quarantine·operator transition·same-stage owner·hash/guard/proof를 재확인한다. Valid carry도 성공적으로 발행하되 selection_status는 `incumbent_preserved_*`다. Missing/stale에만 기존 승인 fallback을 쓰고 invalid payload는 fail closed한다. 다른 family의 전역 strict FAIL은 독립 family readiness와 분리해 기록하며 전체 native DONE을 PASS로 바꾸지 않는다. 실제 wrapper가 전역 blocker로 멈추는 mandatory predecessor이면 먼저 그 원인을 닫고 우회하지 않는다.

Service의 기존 `_profile_with_applied_policy`/`load_applied_profile_policy`를 사용한다. Start 당시 runtime date·profile·applied hash·selected release·정책값을 existing state/evaluation receipt에 남긴다. 이미 실행 중인 서비스는 자동 hot reload하지 않는다. 다음 정상 기동이 새 release를 소비하도록 실제 systemd WorkingDirectory/ExecStart를 확인한다. 조기 PREOPEN·Main/거래 서비스 임의 restart는 구현 검증에 포함하지 않는다.

재고/미체결 주문은 생성 당시 policy/target/owner를 유지한다. 새 entry filter의 정책 파일 적용이 기존 주문 취소·target 재산정·수량 변경·강제 exit로 번지면 거절한다. Exit/custody 복구는 entry source gate와 분리하여 신규 정책 결손 때문에 기존 재고 관리를 막지 않는다. 현재 exclusion3 profile 및 operator veto도 해제하지 않는다.

Closure: gap/empty/carry/positive 모두 candidate→정규 PREOPEN file→profile loader가 같은 date/hash로 이어짐; two simultaneous preflights/idempotent rerun에도 파일/hash 하나; service consumer receipt에서 적용값 확인; existing-held fixture의 target/qty/ownership 변화0. 자연 PID/주문/fill/economic acceptance는 실제 발생 후 별도로 기록한다.

## 9. LP-A6 — 마지막 소비·post-apply 귀속·rollback

Daily EV/runtime summary와 tower/checklist/strict에 actual 실적, source/censored 이유, **distinct paired 비교**, selection, effective 정책 hash 및 자연 적용 여부를 구분해 전달한다. Current report generation에 귀속된 recommendation/source proof가 native intake에서 소비돼야 한다. Unknown/invalid producer field는 기존 source-quality workorder에 보낸다. 새 중복 보고서/workorder catalog는 만들지 않는다.

장후 재생성의 fixed point는 affected producer→candidate→EV/runtime→tower/checklist→strict `--require-summary-handoff`→controller다. 변동없는 원천 재실행은 멈춘다. 다음 단계가 source gap이면 owner/closure/as-of를 명시하고 valid carry/blocked로 종결한다. Verifier/controller self hash를 summary dependency에 넣지 않는다. Whole DONE에 필요한 무관한 선행 실패는 별도 owner로 남기고 가족 단위 완료로 위장하지 않는다.

Post-apply actual 결과는 machine state의 applied policy hash·profile·venue/session·entry/exit owner로 귀속한다. Deployment, file publish, loader ready, PID consumption, actual entry/fill, COMPLETED full-cost EV/일별 순익은 각각 다른 상태다. Profile별 source-valid 공통 epoch/cohort·actual 적용/미적용 및 full/partial/manual를 기존 attribution window에서 비교한다. CF PnL과 역사 비용 복구를 새 실현 이익에 더하지 않는다.

Rollback은 유효한 마지막 incumbent artifact/proof를 다음 exact-date 정책으로 발행하는 기존 경로를 사용한다. Tampered/missing hash·source damage·same-stage conflict·기존 손실/주문 hard guard는 신규 entry를 fail closed한다. 현재 날짜 정책을 덮거나 existing position을 강제 정리하지 않는다. Canary/full 정책은 prior version과 guard/rollback proof를 보존한다.

Closure: strict가 candidate/applied/summary/state의 policy/hash/date 불일치를 검출; 새 결과가 실제 후행 consumer에서 소비됨; post-apply 손익이 정확한 적용 version에 귀속됨; rollback carry loader valid 및 custody 보존. 신규 실현 개선을 아직 측정 못하면 Acceptance는 OPEN이다.

## 10. LP-A7 — 구현 순서·검증·비용 제한

| 순서 | 수정 소유 위치 | 필수 검증 / 종결 |
|---|---|---|
|A0–A1 |기존 `monitoring/low_price_two_leg_tuning.py`, shared source gate |dated missing/valid-empty/source gap·phase/hash/role·actual cost/held fixture |
|A2–A3 |기존 replay section·entry spot research 및 low-price machine capture hook |applied baseline·same-budget next-entry/custody·actual/CF·시간순 unused holdout·joint/no-edge fixture |
|A4 |기존 `trading/low_price_two_leg/policy_runtime.py`, actual producer의 candidate writer |v3 retired 보존·v4 validated carry/positive·forged proof/mutation 거절 |
|A5 |기존 `automation/low_price_two_leg_policy_apply.py`, 두 native wrapper/preflight, service 필요부 |정규 PREOPEN target·single lock/hash/freeze·loader·held custody; existing systemd route receipt |
|A6 |기존 Daily/summary/tower/checklist/strict consumer·actual attribution |same generation fixed point·version economics·rollback/외부 predecessor 분리 |

각 묶음은 implementation→self review→보완→re-review→targeted validation을 닫는다. Python pytest/compile, wrapper `bash -n` 및 기존 contract tests, `git diff --check`, docs print-only parser를 수행한다. Existing `src/tests/test_low_price_two_leg.py`, `test_low_price_two_leg_entry_spot_research.py`, `test_low_price_two_leg_expanded_candidate_research.py`, `test_threshold_cycle_preopen_apply.py`의 해당 owner에 회귀를 추가한다. 새 root Python module·새 CLI·generic schema framework·duplicate matcher/replay engine·독립 realtime daemon을 만들지 않는다. 필요한 schema branch/section/helper는 기존 role package 안에 둔다.

이미 구현·검증된 expanded LP0–LP6/Final Q0–Q5 및 unaffected source tests는 code/dependency equivalence를 확인해 receipt를 재사용한다. 반복 테스트는 새 변경·실패·불확실성에 한정한다. 대형 growing JSONL은 stat 후 manifest/summary/bounded streaming,82MB actual report와 expanded 보고서는 필요한 section만 읽는다. Pipeline cache/공유 raw 새 재구축·과도한 benchmark/성능 guard는 하지 않는다.

시간이 길면 eligible profile·두 기존 축·고정 challenger1개와 저장 원천으로 분석 범위를 줄이고 미처리 profile을 pending/carry로 표시한다. Signal 후보 수·report 상세·진단 범위를 줄일 수 있지만 holdout/floor/cost/terminal/owner 안전 계약은 줄이지 않는다. 완료 입력 지문이 같은 retry는 완료 checkpoint부터 재개하고 계산을 반복하지 않는다. 성능 개선이 어려우면 범위를 줄여 종결하며 양수 정책을 만들려고 기준을 완화하지 않는다.

Future 구현 closure에는 선택 commit/release, targeted receipts, source date와 next effective date, native regenerate command/terminal state, candidate/proof/applied/consumer hash, actual PID 여부, 전체 strict/controller 외부 blocker, measured joint 개선 여부를 기록한다. 커밋·push·immutable deployment는 구현 검증 이후의 승인된 후속 단계이며 이번 문서 수립에서 실행하지 않는다.

## 11. 최종 Acceptance

1. 실제 체결이 없는 profile은 cheap terminal census+보존 정책으로 끝나며 불필요 replay를 돌리지 않는다. 실제 체결이 있는 profile의 baseline·source·cost·custody가 대사된다.
2. 기존 두 filter의 distinct challenger를 same-budget/next-entry 경로로 비교하고 calibration 선정/미사용 holdout·family real execution/권한 조건을 닫는다.0건은 no-edge/sample/source/retired/self를 구분한다.
3. 장후 재생성은 전체 profile을 포함하는 유효 dated candidate를 남긴다. 증거가 충분하면 bounded 선정, 부족하면 verified incumbent carry, incumbent 자체가 invalid면 explicit entry blocker다.
4. 다음 정규 PREOPEN에 공통 apply 한 번으로 exact-date policy가 생성되고 profile preflight/service/machine이 동일 hash를 자동 소비한다. 기존 재고/주문/guard는 보존된다.
5. 후행 summary/tower/checklist/strict/controller가 동일 generation을 소비하고 자연 applied-version 실제 완료 비용 손익으로 돌아온다. Test fixture·배포·loader PASS와 실제 EV·일별 순익 개선은 따로 종결한다.

## 12. 구현 종결 및 자연 Acceptance

LP-A0–A7은 기존 모듈과 두 wrapper에서 구현했다. Actual report v9/candidate v4, 실제 applied baseline, 조건부 두 축 calibration, 사전 고정 미래30/16일 독립 window, 양측 execution·일별 native capital·실제 broker terminal 재현·기존 family authority 재검산, lossless native observation과 등록된 실제 profile seed의 기존 호가 소비, 단일 lock/atomic/freeze PREOPEN 발행 및 후행 brief 결속을 닫았다. V3 subset 승격·수량/target 변경·재고 재계산은 허용하지 않는다.

9/17 native 61profile은 hold_sample24/valid_empty_no_fill19/source_gap9/hold_inventory_custody9로 대사된다. Eligible0이므로 추가 CF replay0이며 검증된 개선0을 no-edge로 해석하지 않는다. Source9/17·publication9/18·effective9/21의 mutation0 보존 candidate와 격리된 prepared applied/loader를 검증했다. 실제9/21 applied 파일 발행은 정상 PREOPEN에 맡긴다. 자세한 검사·선택 commit/release·service pin·전체 chain 외부 blocker는 owning closure를 따른다.

9/19 KST checklist는 존재하지 않는다. 주말 임시 owner를 신설하지 않고 사용자 명시 승인과 기존 LowPriceExpandedResearchRepair0918의 Acceptance를 보존한다. [9/21 자연 PREOPEN/PID/체결/완료 비용 경제성](../checklists/2026-09-21-stage2-todo-checklist.md)은 동일 ID로 이관했으며 새 구현 완료로 계산하지 않는다.
