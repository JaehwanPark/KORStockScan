# 장후 정책 생성의 구조적 결손·퇴역 잔재 전수 점검 — 2026-10-11

## 1. 판정과 범위

**시간·표본 증가만으로 새 정책을 선택할 수 없는 경로가 남아 있다.** 현재 정책 파일 발행·기존값 승계와 신규 후보의 비교·선정 완료를 구분해야 한다. 확인한 핵심은 cancel-wait의 누적 과거 원천 결손 veto, rising-missed의 항상 NULL인 선정 필수 지표, holding vote의 기본값 전용 발행/검증, 새 보호선 생성자 부재, 보조 비교의 동결된 미해결 표본이다. 이것이 모든 장후 작업 실패나 다음 영업일 기동 불가를 뜻하지는 않는다.

- 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [10/11 현행 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md), [장후 점검 지시문](../postclose-tuning-result-review-task-instructions.md)의 구조적 결손 분류. 과거 계획의 미구현 문구 대신 현재 생산자·선정기·발행기·소비자를 대사했다.
- 검사 시점: 2026-10-11 12:08 KST 스냅샷. workspace `38f66369c74f7773822fa8b8b03c4d645eba83d3`; selected release `main-stop-semantic-20261011-v1` / `91edc62844180be6a279e761f32996c3c76ce72e`.
- workspace와 selected release의 `src`/`deploy` Python·shell **1,112개 비교, 차이 0**. production Python **591개 AST 파싱, 파싱 오류 0**, 정적 내부 import 결손 2곳은 동일한 고립 파일에서 발견했다. shell wrapper **55개**, 리터럴 Python 모듈 호출 **71개**를 대사했다.
- 현재 summary의 필수 원천 **9/9**와 부가 정책·PREOPEN, 활성/퇴역 wrapper, cron·설치 unit, selected release 및 release 디렉터리 바로 아래 29개 디렉터리의 지정 퇴역 표면을 확인했다. 이 29개에는 snapshot/backup 등 보조 디렉터리 6개가 포함되며 전부 실행 릴리스라는 뜻은 아니다.
- 점검과 근거 문서화만 수행했다. 정책 재생성·provider 호출·주문·배포·재기동·삭제·Project/Calendar 동기화는 실행하지 않았다. 229 MB entry-split 보고서는 전체 재생성/재파싱 대신 해시 결속된 bounded companion 및 생산/소비 코드를 사용했다.

전수의 범위는 현재 설치된 장후 stage/정책 family·정적 파일 census다. 동적 import의 모든 실행 분기, 비활성 과거 릴리스 전체 소스, 실제 다음 영업일 PID/주문 결과까지 무결함을 입증한 것은 아니다.

## 2. 현재 발행·기동 상태

| 검사 | 현재 증거 | 의미 |
| --- | --- | --- |
| source 10/8 summary | `direct_evidence_complete`, required 9/available 9, blocking reasons 0; 10/11 11:29:12 생성 | 필수 원천의 존재·계약 완료. 모든 신규 정책의 우월성 완료가 아님 |
| target 10/12 PREOPEN | 재검증 `current_full_contract=pass`, findings 0 | 기존/초기 정책과 선택 코드로 준비 가능 |
| 예약 경로 | router `cron_routing_verified=true`, required targets 8 | 설치된 필수 cron의 선택 릴리스 연결 확인 |
| 실제 소비 | selector와 PREOPEN 모두 `actual_pid_consumed=false` | 다음 영업일 자연 기동·소비는 아직 미래 증거 |
| Main stop stage | source 10/12부터 설치 적용; 10/8 summary는 `not_installed` | 과거 source date의 미설치 표시는 cutover 계약이며 생성기 부재와 구분 |

[PREOPEN 검증](../../data/report/postclose_structural_audit/2026-10-11/preopen-verification.json), [cron 검증](../../data/report/postclose_structural_audit/2026-10-11/cron-routing-verification.json), [고정 스냅샷](../../data/report/postclose_structural_audit/2026-10-11/audit-snapshot.json).

## 3. 시간 경과로 닫히지 않는 경로

### F1 — cancel-wait: 과거 결손이 미래 선정도 계속 차단할 수 있음 / 우선순위 높음

[entry_cancel_wait_tuning.py](../../src/engine/automation/entry_cancel_wait_tuning.py)의 `_history_dates`(825–836)는 refresh 시작일부터 target 전일까지 모든 거래일을 요구한다. `_hydrate_missing_history`는 기존 sealed projection 복구를 시도하지만, `_reconcile_history`는 missing/predecessor gap을 전체 coverage에 반영하고, 평가 후 history가 `source_gap`이면 선정 결과를 다시 지운다(1186 부근).

현재 10/8 보고서는 당일 제출 0건을 검증했지만 **9/29·9/30·10/1 원천 대사 결손**, `historical_zero_is_verified=false`, `unresolved_prior_custody_count=null`, `economic_tuning_input_allowed=false`다. known open 0과 역사적 주문 부재 검증은 다르다. 과거 원천이 복구되지 않으면 이후 정상 표본을 쌓아도 동일 결손을 반복해서 요구한다. 기존값 정책 파일은 발행할 수 있다.

- 소유: `entry_cancel_wait_tuning`. 보고서의 과거 식별자는 `EntryCancelWaitSourceReconciliation1002`이며, 현행 실행 인계는 [10/12 체크리스트](../checklists/2026-10-12-stage2-todo-checklist.md)의 `DirectFamilySourceRepairEntryCancelWait`다.
- 보완: 원래 custody 대사와 후보 경제 비교 모집단을 분리한다. 원천 복구 가능성을 먼저 판정하고, 회복 불가 과거 구간을 명시한 prospective 학습 경계를 설계한다. 실제 미종결·unknown custody 안전 조건을 지우거나 과거 제출 0을 조작해서는 안 된다.
- 종료 시험: 과거 한 날짜 결손 + 이후 완전한 적격 표본 fixture에서 과거 결손은 남기되, 독립 경제 비교의 허용/차단 사유가 정확히 분리되어야 한다. known open 주문 fixture는 계속 차단해야 한다.

### F2 — rising-missed: 선정 필수 순이익이 구현상 항상 NULL / 우선순위 높음

[rising_missed_classifier_prior.py](../../src/engine/monitoring/rising_missed_classifier_prior.py) `_metrics`(341–372)는 baseline/candidate/delta daily net profit, worst-day net profit, model notional을 항상 `None`으로 만든다. `_evaluate_candidate`(375–439)는 충분한 calibration/holdout 및 양수 EV를 통과한 뒤에도 이 NULL 때문에 `structurally_blocked`로 판정한다. `validated_edge`로 갈 정상 경로가 현재 계산으로는 열리지 않는다.

현재 당일 상태는 `valid_empty`다. 당일 표본 0과 **미래 표본이 충분해져도 남는 수량·자본 모델 미구현**을 함께 표시해야 한다. 기존 테스트도 `unavailable_quantity_and_capital_constraints_missing`를 명시적으로 기대한다. 비용을 제외한 평균 수익률은 계산하지만 실현/가상 일별 순이익으로 둔갑시키지 않는 차단 자체는 올바르다.

- 소유: `rising_missed_classifier_prior` 및 rising-missed 원천/selector.
- 보완: 정책 자동변경을 유지할 것이면 수량·동시 자본 제약·비용을 가진 paired 모델과 독립 holdout을 구현한다. 진단 전용이면 역할을 명시하고 자동 정책 개선을 기다리는 상태로 표시하지 않는다. NULL을 0으로 바꾸거나 순이익 gate만 삭제하는 수리는 제외한다.
- 종료 시험: 충분한 양의 후보가 유효 수량·자본 원천으로 실제 `validated_edge`에 도달하는 시험과, 그 원천이 없으면 여전히 차단되는 시험을 모두 요구한다.

### F3 — holding path vote: replay·publisher·validator 모두 기본값 전용 / 기존 OPEN 잔여

[holding_path_vote_replay.py](../../src/engine/scalping/holding_path_vote_replay.py)는 후보별 paired EV를 `None`으로 두고 independent economic comparison 부재를 기록한다(102–108). 결과는 `selected_policy=None`이다. [holding_path_vote_policy.py](../../src/engine/scalping/holding_path_vote_policy.py)는 `PATH_POLICY_BY_MARKET` 기본값을 발행하며, validator도 정책이 baseline과 동일하고 경제값이 NULL이어야 통과한다(248–257).

현재 **12 cell의 `estimated_provisional_published`**는 초기 정책 발행의 증거다. 더 많은 거래를 입력하는 것만으로 다른 정책/프롬프트가 선택되지는 않는다.

- 소유: 현행 OPEN `MainStopLossRetirementRuntimeTuning1010`, SL-F11.
- 보완: 대안 vote를 인과적으로 식별할 입력·실행 재생·비교/선정 계약을 구현한 뒤 publisher와 validator를 함께 이행한다. 초기 baseline 채택에 새 경제 선행 gate를 붙이지 않는다.
- 종료 시험: 비기본 후보의 유효 비교→선정→발행→검증→loader/pin fixture와 미식별 vote의 source-gap 유지를 동시에 확인한다.

### F4 — 새 protect/trailing 보호선의 active Main 생성자 부재 / 기존 OPEN 잔여

[main_stop_postclose.py](../../src/engine/automation/main_stop_postclose.py):455–456이 `vote_selection_mode=baseline_only_unidentified_counterfactual_votes`, `protect_line_generator_status=source_gap_no_active_main_generator`를 명시한다. Main handler에는 `protect_profit_pct`·`trailing_stop_price`의 소비 경로가 있지만 현행 경로의 값 쓰기는 초기화/해제와 구분해야 한다. 확인한 active Main 경로에는 새 유효 보호선을 만드는 생산·provenance 연결이 없다.

- 소유: 현행 OPEN `MainStopLossRetirementRuntimeTuning1010`, SL-F8.
- 보완: 보호선 생성 규칙·position/owner/clock/source lineage와 정상/fast 소비 계약을 연결한다. 이미 존재하는 수동/역사 보호선의 소비나 7축/9cell Main stop 확인 정책 전체가 없다는 뜻은 아니다.
- 종료 시험: 새 Main position의 적격 관측으로 보호선 생성→정책/position pin→정상/fast 소비를 입증하고 manual/retired owner의 선을 자동 인수하지 않아야 한다.

### F5 — 보조 비교: 동결된 미해결 pair는 단순 재대기로 완료되지 않음 / 우선순위 높음

[reversal_auxiliary_tuning.py](../../src/engine/scalping/reversal_auxiliary_tuning.py):137–181의 일반 운영 캠페인은 미해결 outcome도 표집할 수 있다. `calls`는 WIN/FAIL_STOP/FAIL_TIMEOUT이 아니면 호출하지 않으며(321–324), campaign checkpoint는 원래 pair를 보존한다. 완료된 invalid response도 일반 planned 호출 경로로 재처리되지 않는다.

현재 동결된 **50 pair 중 비교 가능 17, label 미해결 29, 추가 planned pair 3, invalid response pair 1**이다. 미해결 29개의 사유는 모두 `path_end_before_horizon`이다. 해당 과거 가격 경로/label 계약의 보완 없이 시간이 지나거나 같은 campaign을 재실행하는 것만으로 요청/비교가 모두 완료되지는 않는다. 추가 planned pair에는 원래 source-day budget 제약도 있다. 이번 점검에서 호출 budget을 리셋하거나 추가 호출하지 않았다.

또한 `improves`(389–393)는 incumbent의 PASS 분모가 0이면 항상 false다. 현재 유효 pair가 있는 9 scope 중 6 scope가 해당하며, 그중 일부는 candidate가 WIN을 추가로 PASS해도 개선으로 선택되지 않는다. 이는 무표본/0분모 비교 규칙의 미정의 범위이지, 모든 미래 scope의 영구 실패라는 주장은 아니다.

- 소유: `continuous_reversal_postclose`의 auxiliary campaign/registry 및 `reversal_auxiliary_tuning`; 10/12 현행 인계는 `DirectFamilySourceRepairCompactAuxiliary`다.
- 보완: unresolved의 미래 성숙 가능/과거 source-gap을 분리하고 terminal exclusion·캠페인 완결 의미를 명시한다. 표집 교체가 필요하면 원 캠페인을 보존한 successor와 선택 편향 통제·기존 누적 budget을 함께 설계한다. 0-PASS incumbent의 비교 가능성/기준을 별도로 정의한다.
- 종료 시험: 영구 censored pair가 있어도 무한 planned 대기가 아닌 명시적 종결 상태로 대사되어야 한다. transport 요청 완료, 유효 paired 비교 완료, 후보 개선 선정은 각각 검사한다. invalid response를 성공 비교로 세지 않는다.

## 4. 활성 family 전수 대사와 과거 원천 결손

| family/작업 | 생산→소비 연결 및 현재 결과 | 판정·다음 조건 |
| --- | --- | --- |
| source quality | audit→행별 격리→native reports/summary; 필수 원천 존재 | warning 전체를 일괄 실패로 바꾸지 않는다. 원천 결손은 해당 cohort에 유지 |
| Main 기계판정 | continuous reversal→typed operating policy→Main loader/PREOPEN | 현재 `identical_policy`/등록 정책 승계. 생산 경로 존재; 새 우월 후보 부재와 미생성 구분 |
| Main 보조판정 | frozen pair/registry→auxiliary 비교→동일 Main policy/compact 소비 | target12 128 scope 준비 증거와 F5 비교 미완료를 분리 |
| pre-submit delay | commit/quote ledger→partitioned 가격 비교/선정→세대 정책→loader | 현재 `initial_baseline_immediate`, 가격 pair 21. 가격 연구는 체결·청산 증명을 요구하지 않음. 현대 생성/선정 경로 존재 |
| entry cancel wait | 원천 제출/주문 대사→paired replay→정책 | 당일 0 verified, 과거 source-gap; F1 |
| entry split | operating contract/arms→strategy-owner replay→모델/후보 train/holdout→정책 companion | 현재 `operating_paired_source_missing`. producer는 존재하므로 모두 미구현이라고 단정하지 않음 |
| scale-in split | 실제 ADD 원천/종결→split 분석/정책 | 당일 실제 fill 0, `skipped_no_actual_fill`; 해당 경제 분석은 미적용. 최초 진입 가격 연구와 혼합하지 않음 |
| WS/lookup attention | native scanner partition/선택→opportunity 또는 executable paired book→정책 | 내부 결과는 `source_gap`, `complete_partition_or_actual_selection_missing`. prospective 대안 경로 존재. 요약의 `not_applicable`만으로 완료 판정 금지 |
| rising-missed | native feedback→paired 지표→classifier/TP1 정책 | 당일 valid-empty와 F2 구조적 미구현 공존 |
| 최초 수량 | native 원천/공통 실행 모델→joint train 확정·holdout→v2 refresh/정책→Main | 현재 유효 incumbent 유지. 구현 경로 확인; 과거 원천/비용 결손과 적격 0은 별도 |
| holding exit/trailing | postclose_exit snapshot→holding report→all-scope/partitioned replay→typed 선택·발행→bootstrap | 최신 all-scope census 20,832 scope 완료. 완료는 전체 scope의 source-valid/우월성 의미가 아님. 선택기 구현 존재 |
| holding path vote | holding report/replay→12 cell baseline 정책→loader | 초기 발행 가능, 경제값 변경 불가: F3 |
| Main stop confirmation | quote/stop ledger→정규 장후 stage→replay/정책→strict/PREOPEN/pin | source10/12부터 7축/9cell 설치. operator 실험 계약 없는 축의 baseline carry는 권한 설계. 새 보호선과 vote 잔여는 F3/F4 |
| legacy outcome labels | canonical context/input bundle/bars→label→quality report | 10/8 mature11/partial8의 19건 모두 source-ineligible. canonical/input/payload 누락은 과거 source 복구/격리 대상이며 벽시계 성숙으로 복구되지 않음 |
| Main 시장약세 야간 연구 | 선택 릴리스 wrapper→as-of source join/paired 연구→advisory 결과 | 별도 야간 스케줄 존재. `postclose_research_advisory_only`; 자동 live 정책 발행을 기대할 작업이 아님 |
| EOD/archive/summary/controller/finalization | source 보존→보고서/세대 대사→다음 날 준비 | 정상 종료는 source·경제·선정·실제 소비 모두 PASS의 대용이 아님 |

entry-split의 [strategy_owner_replay.py](../../src/engine/scalping/strategy_owner_replay.py):1360–1392는 operating contract가 있으면 arms를 만들고 [entry_split_order_plan.py](../../src/engine/scalping/entry_split_order_plan.py):5502 이후가 소비한다. passive queue/unknown partial fill, 미확인 cancel/late fill, 후속 ADD/partial SELL, state별 입력 누락은 지원 범위를 명시한다. 현재 결손만으로 미래 complete native source까지 불가능하다고 확대하지 않는다.

legacy label 19건은 canonical bars/context/schema/input bundle/exact-v2 preflight/payload store 결손을 가진다. 현행 v6 auxiliary의 전체 모집단을 이 legacy label 19건으로 대신 평가하지 않는다. [ai_decision_quality.py](../../src/engine/scalping/ai_decision_quality.py)의 exact input 검증을 무조건 제거하는 방식으로 복구하지 않는다. entry-split의 기존 원천 수리 인계는 10/12 `DirectFamilySourceRepairEntrySplit`다.

WS selection은 [scanner_lookup_attention_resource.py](../../src/engine/scalping/scanner_lookup_attention_resource.py):980 이후에 과거 execution 원천이 회복 불가일 때 prospective 시장 경로 연구를 평가하는 경로가 있다. 그래서 현행 `source_gap`을 생성기 자체의 영구 부재로 판정하지 않았다. 새 완전 partition·독립 표본의 실제 생성/소비는 미래 수용으로 남는다.

## 5. 퇴역·삭제 후보 및 남겨야 할 코드

### R1 — 고립된 import 파손 파일 / 삭제 후보

삭제 전 `src/trading/order/target_amend.py`의 9,32행은 삭제된 `src.trading.order.adaptive_exit.broker`를 import했다. production 정적 import caller는 0개였다. 당시 Main 경로의 실패로 관측된 것은 아니지만 파일 자체는 정상 import가 불가능한 잔재였다. 당시 selected release를 포함한 지정 표면 검사에서 23개 릴리스 디렉터리에 같은 잔재가 있었다. 후속 구현에서 이 파일을 삭제했으며, 이 문단은 삭제 전 점검 기록이다.

조치 방향은 제거 대상/호환 계약을 확정하여 고립 파일을 제거하는 것이다. 삭제된 adaptive-exit broker를 복원하지 않는다. 과거 릴리스는 runtime/rollback/source 의존성 census 없이 함께 삭제하지 않는다.

### R2 — 삭제된 모듈을 호출하고 성공 종료하는 shadow wrapper / 삭제 후보

삭제 전 `deploy/run_shadow_canary_check.sh`의 20행은 없는 `src.engine.check_watching_prompt_75_shadow_canary`를 호출했다. 실패 exit를 출력한 뒤 마지막 `exit 0`으로 끝났다. 당시 설치 cron/unit 및 repo caller에서는 실행 연결을 찾지 못했다. 직접 호출되면 기계적 성공을 오인할 수 있어 퇴역 entrypoint 삭제/명시적 퇴역 응답 대상으로 분류했다. 후속 구현에서 이 wrapper를 삭제했으며, 이 문단은 삭제 전 점검 기록이다.

### R3 — 퇴역 산출물을 여전히 기다리는 감시·intake / 실제 경고 원인

[run_threshold_cycle_postclose.sh](../../deploy/run_threshold_cycle_postclose.sh):194는 `BUILD_CODE_IMPROVEMENT_WORKORDER=false`로 생산을 퇴역시켰다. 그런데 [artifact_freshness.py](../../src/engine/error_detectors/artifact_freshness.py):2209–2216은 해당 일자 workorder를 여전히 요구한다. 최신 detector의 missing 경고와 일치한다.

[postclose_recommendation_intake.py](../../src/engine/automation/postclose_recommendation_intake.py):31의 source label도 이 퇴역 산출물 하나다. missing은 전체 summary blocker로 추가하지 않는 코드여서 현재 기동 차단 원인은 아니지만, 현행 native 권고를 종합하는 intake라고 간주하면 누락된다. 현재 권고 owner 계약으로 이행하거나 퇴역 intake를 제거해야 하며 구 workorder 생산자를 되살리는 수리는 제외한다.

### R4 — 이름이 퇴역 registry와 일치하는 대형 모듈·활성 공통 함수 의존

명시적 퇴역 이름 및 opening-rotation/구 sim/workorder 대조에서 **18모듈, 46,050행**을 찾았다. 이는 삭제 가능한 순수 dead-code 행 수가 아니다. 일부 현재 Main 생산자가 공통 함수/상수를 import한다.

| 잔존 모듈군 | 현행 의존/퇴역 상태 | 정리 전제 |
| --- | --- | --- |
| `lifecycle_ai_context`, `lifecycle_decision_matrix`, `lifecycle_bucket_discovery`, `lifecycle_decision_matrix_runtime` | retired/neutral facade와 AI/handler/AVG_DOWN 상수·reader 의존 공존 | active helper를 역할 패키지로 이전 후 과거 튜닝 본체 분리 |
| `scalp_entry_action_decision_matrix` | `scalping.entry_observation_source`가 row/event/backfill helper 사용 | 원천 reader 먼저 이전; 바로 삭제하면 현재 분석 입력 손상 |
| `institutional_flow_context`, `runtime_apply_bridge` | 퇴역 matrix 또는 runtime-apply audit 의존 | 현재 감사 계약까지 대사 후 정리 |
| `build_code_improvement_workorder` | `pattern_lab_propagation_audit`가 helper import | R3 consumer 이행과 helper 분리 후 본체 제거 |
| `scalping_avg_down_recovery_calibration` | 현재 `strategy_owner_replay`가 event-path/reader 사용 | AVG_DOWN 수탁·native source reader 보존 후 이행 |
| `scalping_pyramid_intraday_feedback`, `scalping_pyramid_quality_calibration` | 퇴역 entrypoint; succession에 옛 branch 잔존 | PYRAMID 자동 권한 부활 없이 호출·schema 이전 |
| `ldm_hypothesis_parent_refinement`, `ldm_hypothesis_discovery` | 퇴역/그 내부 참조 | 외부 CLI/과거 증거 계약 대사 후 제거 후보 |
| `opening_rotation`, `opening_rotation_backtest`, `opening_rotation_tuning` | Main/scanner는 RETIRED fence; 직접 평가/tuning 본체는 남음 | 직접 CLI까지 퇴역 계약을 닫고 active import 상수/표시 의존 이전 |
| `scalp_sim_ev_midcheck`, `scale_in_incremental_counterfactual` | 구 분석 본체/공통 계산 함수 잔존 | 실제 유지할 공통 수학·archive reader와 구 정책 생산 분리 |

상세 파일별 행 수·정적 caller는 [정적 census](../../data/report/postclose_structural_audit/2026-10-11/static-source-census.json)에 기록했다. 이 외 neutral compatibility facade도 있으므로 18을 모든 제거 후보의 절대 총계로 사용하지 않는다.

### R5 — 퇴역 계약 테스트·운영 inventory 드리프트

- `src/tests/test_adm_ldm_retirement.py:281`은 퇴역된 `samsung_machine_entry_tuning` 명령이 wrapper에 있어야 한다고 요구한다. 실제 wrapper:239는 Main fixed-watch로 이관된 해당 작업을 false로 고정한다. 실패 수리는 테스트를 현행 퇴역 계약에 맞추는 방향이며 명령 복원이 아니다.
- [장후 inventory](../audit-reports/2026-09-05-postclose-work-inventory.md)는 6개 stage와 10/8 checklist 링크를 남긴다. source10/12부터 활성인 Main stop stage 및 별도 야간 Main 시장약세 연구를 current inventory에 반영해야 한다. 과거 source10/8의 6-stage 정상 결과는 그대로 유효하다.
- wrapper의 retired false 변수·DONE 출력·호환 schema는 실행 중인 작업으로 세지 않는다. 제거 시 parser/fixture/운영 문서도 함께 이행해야 한다.

### 보존 대상

현재 설치 unit에서는 episode/widget/IPO 전용 실행 unit을 찾지 못했고, 검사한 릴리스 바로 아래 지정 경로에 episode/widget/adaptive-exit 실행 디렉터리는 없었다. 이것만으로 모든 과거 보관물의 퇴역 잔재가 없다고 주장하지 않는다.

`owner_retirement.py`, journal의 원래 owner/custody, manual veto, 과거 수탁·주문 증거, active Main이 사용하는 reader/수학 helper는 보존 대상이다. 이름에 episode가 포함된 `scalping/samsung_policy_episode_research.py`는 오프라인 가격 구간 연구이며 이름만 보고 퇴역 episode 자동주문 worker와 함께 삭제하면 안 된다.

## 6. 의미적 감시와 후속 수리 순서

summary의 required9/9, stage succeeded, `valid_empty`, `not_applicable`는 신규 후보 생성 능력을 입증하지 않는다. rising-missed의 당일 empty 뒤에 있는 필수 지표 미구현, holding vote의 기본값 전용 validator, 누적 과거 결손 veto를 별도 구조 상태로 노출할 필요가 있다. 현행 WS 내부 source-gap도 요약 not-applicable과 구분한다.

| 순서 | 소유 경로 | 다음 조치 | 종료 기준 |
| --- | --- | --- | --- |
| 1 | cancel-wait, rising-missed | F1/F2 계산·원천 경계의 구체적 보완 | 정상 미래 원천의 선정 가능 경로와 결손 차단을 같은 fixture에서 검증 |
| 2 | auxiliary campaign | F5 영구 unresolved/invalid/0분모 및 예산 의미 정리 | 원 campaign 보존, terminal exclusion과 비교/선정 상태 분리, 예산 비증가 |
| 3 | 기존 Main stop OPEN owner | F3/F4 잔여 구현 수용 | baseline 초기 채택 유지, 새 후보/보호선의 실제 producer→consumer 입증 |
| 4 | semantic monitor / native summary | 구조 상태와 원천·표본 상태를 동시 보고; R3 phantom 요구 제거 | source-gap을 0·성공으로 바꾸지 않고 반복 실행/대기 ETA 오판 방지 |
| 5 | 퇴역 경계와 공통 source owner | R1/R2 고립 entrypoint, R4 helper migration, R5 테스트/문서 이행 | active import/CLI/단위 테스트 회귀, 현재 원천·수탁·PREOPEN 불변 |

여기서 소유 경로는 수리할 코드/현재 owner를 지칭하며 새 일정·권한을 발급하지 않는다. 현재 checklist의 Main stop/semantic OPEN owner, 10/12 세 source-repair owner 및 `DirectFamilyPreopenPolicyHandoff`의 자연 수용을 중복 생성하거나 봉인된 준비를 변경하지 않았다. F2 rising-missed의 구조적 결손 전용 실행 owner는 현행 parsed 목록에 없으므로 후속 구현 범위를 정할 때 소유를 명시해야 한다. 무거운 전체 재실행보다 구조 수리를 먼저 검증해야 한다.

## 7. 검증과 한계

- 기존 퇴역 계약 회귀: `test_main_only_retirement.py`, `test_widget_retirement.py`, `test_adm_ldm_retirement.py` → **165 passed, 1 failed**. 실패는 R5의 낡은 삼성 전용 producer 기대값이다. [출력](../../data/report/postclose_structural_audit/2026-10-11/retirement-contract-tests.txt).
- `test_rising_missed_classifier_prior.py` → **10 passed**. 기존 차단 계약이 테스트에서 통과하는 것과 F2의 신규 정책 생성 경로가 구현됐다는 것은 다르다. [출력](../../data/report/postclose_structural_audit/2026-10-11/rising-missed-tests.txt).
- 현재 PREOPEN 전체 계약과 cron 8개 경로 PASS. 실제 PID 소비는 미래 수용이며 이번 검증으로 대체하지 않는다.
- AST/import·wrapper 대상 검사는 정적 검사다. provider/broker 호출, 보고서 재생성, 봇 기동, 실제 종결·순이익 시험은 수행하지 않았다. 점검 결과를 무결함 인증으로 표현하지 않는다.
- 문서 재리뷰에서 잘못된 원천 파일 링크와 과거 owner/현행 실행 owner의 혼동을 보완했다. 최종 로컬 링크·보호 입력 해시·공백 및 print-only parser 결과는 동일 evidence 디렉터리의 `document-validation.json` 및 `print-backlog.txt`에 기록한다. 소스·정책 수리는 이번 검사에서 수행하지 않았다.

후속 구현 때는 source/runtime/helper 이전을 구현→리뷰→보완→표적 검증으로 닫고, 현재 승인 경계와 native successor 절차를 따라야 한다. 이 문서는 검사 결과이며 구조적 미구현을 완료 처리하는 근거가 아니다.
