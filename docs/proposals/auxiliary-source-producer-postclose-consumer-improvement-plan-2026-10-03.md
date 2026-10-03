# 삼성전자 이외 보조 AI 원천 생산자·장후 소비자 개선 계획 — 2026-10-03

## 1. 결정·범위

현재 최종 연구를 기준으로 **삼성전자 이외 종목의 보조판정 연구·정책 비교와, 이를 지원하는 공통 입력·응답·운영 owner 원천 연결을 개선**한다. 정책 비교 대상은 유효한 `stock_code != 005930`이며 삼성전자는 [별도 연구 계획](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md) §3으로 분리한다. 종목 식별 결손은 삼성전자 이외 집합에 편입하지 않는다. 공통 producer는 삼성전자 원천도 보존하며 양쪽 source 품질을 검사한다.

이 문서는 구현 계획과 실행 결과를 함께 보존한다. 사용자의 후속 실행 지시로 A0~A5 source/소비자 개선과 격리 검증을 완료했다. prompt/provider/운영 정책은 변경하지 않았으며 새 API 수집이나 모델 재호출은 실행하지 않았다.

**후속 목적 정정:** 기계·보조 모두 기존 정책보다 높은 승률을 우선한다. `successful_pass_lost == 0` 또는 기존 성공100% 보존을 연구 후보 탈락 조건으로 사용하지 않는다. 성공 제외·실패 회피·순손익은 별도 지표로 보고한다. 아래 과거 후보0은 당시 결과이며 성공 제외 자체가 현재 탈락 근거는 아니다. [이번 승률 우선 재계산](../audits/main-machine-decision-cohort-target-first-research-review-2026-10-03.md)의 보조 selector 수정과 A6 production 이행 대상을 구분한다.

초안은 완료된 `MachineConfirmationCandidateResearch1003`의 산출물이며, 이번 범위 보완 소유자는 `SamsungPolicyScopeReplan1003`이다. 후속 코드 구현·격리 검증은 `NonSamsungAuxiliarySourceConsumerImplementation1003`, 향후 자연 수용은 10/6의 기존 `DirectFamilySourceRepairCompactAuxiliary`다. PREOPEN/PID는 기존 `DirectFamilyPreopenPolicyHandoff`를 사용한다. 연구/계획 완료가 자연 수용의 완료를 뜻하지 않는다. 배포는 별도 지시까지 대기한다.

## 2. 최종 연구 근거와 현재 구현

### 2.1 이번 보완의 삼성전자 제외 기준선

`tmp/samsung-nonsamsung-policy-scope-replan-20261003/scope-census.json`에서 원천 SHA를 확인하고 직접 분리했다.

| 항목 | 삼성전자 제외 결과 | 처리 |
|---|---|---|
| KRX 유효 응답 | 34개, 모두 기존 PASS; 9/29 22·9/30 4·10/2 8 | 학습26·후단8로 고정한다. 삼성전자9개는 별도 연구 자료다. |
| exact pre-AI 연결 | 12개 | 연결되지 않은22개는 해당 연결이 필요한 분석에서 제외한다. 유효 응답 자체를 실패로 바꾸지 않는다. |
| 전체 scope operating 원천 | 42행; 10/2 KRX10행, writer plan0 | 유효 응답34개와 다른 분모다. |
| 10/2 원천 blocker | conditional probe 범위8, exact capacity1, latency danger1 | source 생산 경계별로 수리/미지원/실제 guard를 구분한다. |
| 같은10행의 소비 제외 | exact stop 결손8, transport 결함2 | 위 blocker와 다른 축이므로 합산하지 않는다. |
| flow 양수/가격 비양수 및 매수비중/가격 조건 재계산 | 각각 학습9·후단0 CAUTION 가정; 1/3/5/10분 성공 제외2/1/1/0 | 10분 성공 제외0만으로 채택하지 않는다. 이전에 고정한 여러 horizon의 부작용을 공개한다. |
| spread>tick 및 가격 비양수 | 학습6·후단0 변경; 성공 제외1/1/1/0 | 기계적으로 규칙 강화하지 않는다. |
| 과거 flow 악화+spread 확대 | 학습·후단 변경0 | 개선 후보에 포함하지 않는다. |

동일4개 고정 규칙을9/29→9/30, 9/29+9/30→10/2 분리로 다시 계산했고 후보 선정0이다. 원천 결손·변경0·정상 성공 제외를 서로 구분한다. 새 prompt 응답은0이다.

### 2.2 분리 전 전체 연구 참고

아래43/14,59/15 및 학습11/7 등의 수치는 삼성전자를 포함한 기존 연구 이력이다. 삼성전자 제외 정책의 분모·성능으로 재사용하지 않는다.

| 확인한 사실 | 해석·개선 방향 |
|---|---|
| [최종 순서 검증](../audits/main-machine-auxiliary-path-sequence-validation-review-2026-10-03.md): KRX 유효 응답43, 학습34·후단9; exact pre-AI 연결14 | 43은 전체 AI 호출 수가 아니다. 관측 연결 실패와 응답 결함, 정책 변화 부재를 분리한다. 14를 다른29개에 유사시각으로 확장하지 않는다. |
| flow 양수/가격 비양수 조건은 학습11개 CAUTION 가정, 후단 변경0; 1/3/5/10분 성공2/1/1/1개 제외 | flow와 가격의 단일 부호만으로 veto/CAUTION을 강화하는 방향은 현재 자료로 지지되지 않는다. 성공 제외와 지연 후 회복을 같이 분석한다. |
| spread>tick 및 가격 비양수 조건은 학습7개, 후단0; 과거 flow 악화+spread 확대는 양쪽 변경0 | 행동이 안 바뀌는 조건을 개선 후보로 세지 않는다. 미관측·결손·실제 변화0을 구분한다. |
| [초기 확대 연구](../audits/main-machine-auxiliary-retained-source-hypothesis-research-review-2026-10-03.md): soft438개 조합 변경0, 실제 인용수3~8 대비 단순 count1~3 범위 포화 | citation 개수 확대보다 위험별 관련성·서로 다른 사실인지·materiality 적용 결과를 진단한다. 기존 v2 materiality 계산을 먼저 계측한다. |
| 새 prompt의 exact variant 응답0 | 기존 답변을 새 prompt 결과로 재명명하거나 새 prompt 성능을 추정하지 않는다. 지금 검증 가능한 범위는 동일 응답의 deterministic adjudication이다. |
| `tmp/main-machine-auxiliary-source-remediation-20261003/after-auxiliary-metrics.json`: 전체 scope59행, 10/2 15행; 15행의 writer plan0 | KRX 유효43과 서로 다른 분모다. 10/2 source blocker는 conditional probe 예약 범위12, exact capacity2, latency danger1. stop 결손11·semantic2·transport2는 같은15행의 **다른 축**이며 합산하지 않는다. |
| 같은 operating 진단의 full-cost 적격0, 실제 completed 비교0 | 실행 경제성 미입증. 별도 AI-stage의 비용 차감 가격 CF 진단까지 전부0이라고 해석하지 않는다. |

이미 반영된 작업본도 보존한다. `compact_pre_ai_execution_source_v9`는 자연 응답의 transport/semantic 실패를 분리하고, native lineage 보완과 AI-stage 독립 평가가 존재한다. `evaluate_auxiliary_stage`는 운영 자본·exact stop gate를 그대로 상속하지 않는다. 조건부 probe 관측 계약도 이미 코드에 추가되었으나 unknown fill-anchored price 때문에 실행 재생은 unsupported로 남는다. 이 기능들을 신규 과제로 중복 구현하지 않는다. 위 변경의 배포/PID 소비는 별도 증거다.

## 3. 생산자→소비자 책임 지도

| 경계 | 현재 코드 소유자 | 계획할 변경 | 종료 시험 |
|---|---|---|---|
| 기계 판정→AI 요청 | `ai_decision_trace.capture_machine_observation`, `capture_ai_request`; `sniper_state_handlers._observe_entry_economics_before_ai` | 동일 native attempt/revision을 기준으로 입력 capsule과 단계별 상태를 먼저 확정한다. 운영 plan 실패가 이미 있는 predecision 입력을 소실시키지 않도록 전파 경로를 검사한다. | BLOCK/RECHECK 미호출, ENTER 호출, timeout, semantic 실패를 서로 다른 상태로 회수하며 stock/order 상태 불변 |
| 요청→응답 | `ai_decision_trace.record_ai_decision_trace`, `ai_decision_quality` | request envelope/payload/system·user prompt/schema/parent policy/provider·model/response SHA와 원응답·수선응답의 계보를 보존한다. 기존 필드 누락 지점만 보완한다. | 다른 요청·prompt·재시도·정책 세대 응답을 join하면 명시 제외; 정상 응답은 정확히 한 번 소비 |
| pre-AI 경제 입력 | 위 observer, `entry_split_order_plan.apply_entry_split_order_policy`/`compose_entry_execution_sizing_plan`, `strategy_owner_replay.freeze_entry_operating_context` | 확정 입력·조건부 probe 구조·미확정 fill 기준 값을 분리한다. existing cached capacity의 유효기간·가격·route·계정 범위와 실패 사유를 기록한다. | 관측으로 예약/주문/추가 REST 호출0, expired/mismatched capacity를 적격 처리하지 않음 |
| 입력→결과 label | `ai_decision_quality.annotate_materialized_label_contract`/`write_source_label_materialization`과 `compact_auxiliary_paired_replay.stage_path_label_matches`/`bind_stage_full_cost` | 원천 trace·payload·시점·scope·cost generation을 일대일 연결하고 경로 상태를 보존한다. | 충돌·다른 route·미래 feature·가격/비용 결손이 점수에 들어가지 않음 |
| operating stop/terminal | `strategy_owner_replay`의 freeze/replay, `entry_split_order_plan` 장후 producer | 당시 owner stop/exit/cost와 terminal·부분체결·취소 대사를 각각 결합한다. | current default로 과거 stop 대체 금지; terminal pending의 EV=null |
| 장후 정책 비교 | `compact_auxiliary_paired_replay.prepare`, `evaluate_auxiliary_stage`, `primary_input_blocker`, `operating_comparison_metrics` | 전체 상태 ledger, 단계별 적격성, 실제 행동 변화·승자 제외·원천별 책임을 별도 투영한다. | 같은 입력은 warm/cold 동일 결과; source gap이 빈 집합이나 무수익으로 바뀌지 않음 |
| 장후 handoff | `entry_setup_paired_replay_batch`, `automation/postclose_summary_handoff.py`의 `main_auxiliary_policy` | 새 evidence schema가 준비된 뒤 frozen source generation을 동일 날짜 report→summary→strict→controller로 전달한다. | 코드 PASS, report 재생성, 정책 선정, PREOPEN/PID를 별개 상태로 보고 |

실제 수정 파일은 위 기존 role package를 사용한다. 신규 원천 분석 모듈이 필요하면 `src/engine/scalping`에 두고 root module을 만들지 않는다.

## 4. 구현 순서

### A0. 분모·불변성 기준선 — 최우선

1. 동일 날짜·정책·venue/session별 `machine observed → machine ENTER → provider attempted → response received → semantic valid → stage outcome eligible → operating comparable` 상태 ledger를 만든다. 각 전이의 native attempt 목록·SHA와 배타적 주사유/보조사유를 남긴다.
2. `not_called_by_machine`, `transport_invalid`, `semantic_invalid`, `label_pending`, `source_gap`, `unsupported_scope`, `valid_no_change`, `comparable`을 별도로 보존한다. 주사유별 합은 해당 분모와 일치해야 한다. 원천·stop·response 등 교차축 사유는 합계에 중복 가산하지 않는다.
3. baseline은 §2.1의 operating42/10, KRX 유효34/exact pre-AI12를 **각 exact manifest**로 고정한다. 삼성전자9개와 그 외34개의 유효 응답 집합이 서로 겹치지 않고 원래43개와 일치하는지 확인한다. 종목 식별 결손은 별도 집합이다. 단계별 분모 차이는 row ID로 설명한다. historical 원본·기존 보고서·live bundle을 덮어쓰지 않는다.

### A1. 기존 원천의 lossless capsule — 최우선

필수 identity: `source_date`, `decision_ts`, `stock_code`, `effective_venue`, `session_bucket`, `broker_route`, native `evaluation_attempt_id`/trace, scanner promotion 또는 native watch lineage, machine observation/revision SHA, machine bundle/policy SHA, payload/envelope/prompt/schema SHA.

- 각 필드의 **source clock·producer version·원본 위치/해시**와 구조화 append 성공 영수증을 남긴다. nullable 값과 `missing_reason`을 함께 보존한다. 실패한 경제 plan에도 이미 확정된 identity와 기계/AI 입력 capsule을 유지한다.
- append 전후 프로세스 중단, 같은 attempt 재시도, hash 충돌, 파일 회전/압축, source cache 재개를 검증한다. 동일 native ID 다른 payload는 명시 충돌로 격리한다.
- 기존 archive에서 exact key와 해시가 맞는 필드만 복원한다. 앞서 복원한 metadata7행의 방식과 검증을 재사용한다. 날짜/종목/근접시각만 맞는 유추 join은 금지한다.
- API 구독·호출 횟수·관측 주기는 유지한다. 이 작업의 원천 생산은 **이미 메모리에 있거나 저장된 입력의 보존·연결**이다.

### A2. 조건부 plan 및 stop 의미 보존 — 최우선

- `entry_pre_ai_conditional_probe_observation_v1`의 기존 continuation, probe qty, conditional residual qty, anchor mode, TTL, max slippage, operating context SHA를 소비자까지 전달한다.
- `plan_known_pre_ai`, `conditional_on_unknown_fill`, `capacity_receipt_missing`, `guard_blocked`를 구분한다. 조건부 plan을 완성 주문계획으로 표현하지 않는다. 당시 fill 기준 가격이 없으면 historical executable replay는 unsupported로 유지한다.
- stop은 당시 실제 사용 owner의 **가격 또는 거리·단위·기준 가격·유효시점·owner/policy SHA**가 있어야 한다. exit 정책 계약과 숫자 stop은 다른 필드다. 단순 TTL/현재 stop/env/최신 policy로 재구성하지 않는다.
- 비용은 fee/tax/slippage/기타 적용 비용과 실제 inference 비용을 기존 owner 계약의 적용 범위에 맞게 기록한다. 증권 거래비용과 토큰비용의 KRW/pct 단위를 혼합하지 않는다. 비용 미상은 null이다.
- source-only observer가 실거래 reservation/custody를 변경하지 않음을 회귀 검사한다. exact capacity를 얻기 위한 새 반복 호출은 이 계획에 포함하지 않는다.

### A3. AI-stage와 운영 결과 소비 분리 — 최우선

- 이미 존재하는 독립 AI-stage 평가를 유지한다. 유효 원응답+exact machine 입력+scope/time/price/cost가 있는 행은 운영 plan/stop 결손과 별개로 deterministic soft policy를 평가한다.
- stage outcome은 `target_first`, `adverse_first`, `neither_hit`, `same_bar_ambiguous`, `censored`, `source_gap`을 보존한다. 연구의 1/3/5/10분 비교를 정식10분 목적함수로 몰래 대체하지 않는다. 여러 horizon은 민감도 표시다.
- `COMPLETED + valid profit_rate` 실제 실현 결과, owner-model 실행 재생, 고정 경로 CF를 각자 집계한다. 부분체결과 미체결의 해제 시점/late fill 확인 없는 경제성은 pending/null로 남긴다.
- source-only 결과0·행동 변화0·실제 손실·모델 미지원은 서로 다른 종료 상태다. 새로운 요약의 cost gap 수는 원래 comparison의 포괄 사유 문자열 대신 exact contract 실패 항목에서 계산한다.

### A4. 보조 판단의 가설 재설계 — A0~A3 후

삼성전자 제외 재계산에서도 채택되지 않은 단일부호 규칙을 운영 기본값으로 추가하지 않는다. 삼성전자 이외의 동일 원응답에서 아래 순서로 **작은 가설 집합을 학습 전에 봉인**한다. 전체 집합에서 선택한 조건이나 삼성전자 성과를 후보 선택에 가져오지 않는다.

1. **중복/무관 인용:** 인용 수가 아니라 risk fact ID·predecision evidence type·부호/단위·내용 일치 여부를 확인한다. 기존 materiality score와 PASS/CAUTION/VETO가 실제 어디서 달라지는지 분해한다. 정상 성공을 과도하게 제외하는지 함께 비교한다.
2. **CAUTION 경로:** 당시 응답→동일 native opportunity의 후속 응답/기계판정→실제 terminal 연결이 있는 경우에만 지연 해소·영구 누락·다른 사유 종료를 비교한다. 후속 연결이 없는 행을 실패나 성공으로 보정하지 않는다. 가상의 가격 touch는 재진입 실행 증거가 아니다.
3. **유형 내 오류:** 사전 phase·flow·liquidity별로 false caution/loss pass를 분석하되, UNKNOWN fallback과 작은 셀 지원수를 공개한다. 종목·기회 반복을 독립 표본으로 늘리지 않는다.
4. **재현 가능한 prompt 진단:** retained 응답은 해당 exact prompt의 증거다. 신규 prompt는 텍스트/schema 정적 검토까지 가능하며, exact 응답이 없는 성능 비교는 `not_evaluated_new_prompt_response_absent`로 종료한다. 추가 provider 실험은 현재 계획의 실행 범위가 아니다.

공통 결과: 기존 대비 비용 결합 승률, changed opportunities, 회피 손실, 제외 성공, 미해결 CAUTION, 비용 차감 paired delta, source coverage, 종목/날짜 민감도. 후보 적격성은 기존 대비 승률 개선으로 정하고 표본 수 보정 승률로 학습 순위를 매긴다. 기존 성공100% 보존은 요구하지 않는다. 학습에서 후보 선택 후 동결하고 이미 재사용한10/2는 exploratory로만 표기한다. 후단에서 조건/표본/목표를 다시 선택하지 않는다. 원천·비용·지원수·안전 조건과 승률 목적 이행을 분리한다.

### A5. cache·재생성·handoff — 마지막

- cache key에 source manifest/원천 계약/입력 identity/parent policy/prompt schema/cost·stop generation/소비 코드 버전과 대상 종목 분리 계약을 결합한다. 전체/삼성전자/삼성전자 이외 cache를 혼용하지 않는다. 현재 v9 자료의 lossless metadata 보완과 원천 의미 변경을 구분한다.
- frozen source는 한 번 순차 읽고 필요한 필드만 보존한다. 입력 manifest가 같은 warm 재개는 큰 원본을 반복 스캔하지 않는다. scan budget 초과/미완성 checkpoint는 empty로 발표하지 않는다.
- 구현 후 작은 fixture→retained exact 자료 cold/warm 비교→native row별 차이→격리 report 재생성으로 검증한다. wall/CPU/RSS·source read count를 baseline과 함께 보고한다. 성능 숫자는 실제 실행 전 정하지 않는다.
- 마지막으로 summary/strict/controller의 target date·source generation 결합을 검증한다. canonical 재생성·배포·PID 확인은 그 작업이 별도로 실행될 때 해당 권한과 existing owner gate에 따라 수행한다.

### A6. 승률 우선 정책 선정 계약 이행 — 사용자 후속 기준

**후속 실행 완료:** [전체 목적 이행 계획](postclose-policy-winrate-objective-migration-plan-2026-10-03.md)과 [실행 리뷰](../audits/postclose-policy-winrate-objective-migration-review-2026-10-03.md). 실제 보조 stage의 성공 제외0·paired EV 우선 조건을 v5 승률 개선으로 교체하고 동결/cache/publisher/health를 정리했다. 기존 보유 원천에서 그 외 KRX12개 조합은 행동 변화0으로 승계했다. 기계100%·등록80%도 정리했으며 등록 경로의 trace→기회 결함은 native v3로 보완했다. 통합1,460 tests 및 최종411 tests PASS. 배포·canonical 발행 대기는 유지한다.

연구 selector 수정·보유 응답 재계산은 완료했다. 운영 장후 publisher/loader 이행은 다음 구현 범위이며 현재 작업에서 변경하지 않았다.

1. `entry_policy_hypothesis_research`의 보조 feature fold/최종 선택에서 성공 제외0 조건을 제거하고 승률 개선→표본 수 보정 승률 순위를 구현했다. 기계의 현재 cohort 연구도 같은 목적을 따른다. raw 응답·fact·hard veto를 변경하지 않는다.
2. `compact_auxiliary_paired_replay.evaluate_auxiliary_stage`에는 `successful_pass_changed_count == 0`, `train_successful_pass_changed_count == 0` 및 EV 우선 rank가 남아 있다. 다음 이행에서 성공100% 조건을 제거하고 같은 frozen population의 parent 대비 train/holdout PASS 승률·지원수 보정 순위로 변경한다. 성공 제외 자체를 신규 탈락 사유로 재도입하지 않는다.
3. 기계의 `ai_action_outcome_calibration.build_main_strategy_refinement`와 `entry_strategy_policy.promotion_errors`에도 같은 기존 성공100% 조건이 있다. 기계·보조의 새 목적을 candidate evidence/validator에서 일치시키고, old version cache/selection을 새 기준의 검증 결과로 재사용하지 않는다.
4. 새 selection contract/version, baseline·candidate의 분모/성공/실패/PASS 수, nullable outcome·성공 제외·실패 회피·순손익 필드를 명시한다. 비용/원천/의미 오류·날짜 누출·지원수 및 기존 hard safety는 보존한다. 단순 성공 제외를 원천 결함이나 safety 위반으로 분류하지 않는다.
5. 테스트: 일부 기존 성공을 놓쳐도 승률이 높은 후보 수용, 성공100%를 보존해도 승률 비개선이면 미선정, 극소표본·PASS0·미평가 행의 승률 null, train-only 동결·후단 재선정 금지, validator/producer 목적 버전 불일치 거부. 같은 보유 원천에서 이전/새 목적의 후보 수·순위·탈락 사유를 비교한다.
6. canonical 재생성·정책 선정·PREOPEN/PID·배포를 연구 완료와 구분한다. 배포는 별도 지시까지 대기한다.10/6 기존 자연 수용 owner를 이 연구로 닫지 않는다.

## 5. 리뷰·검증 계획 및 종료 조건

| 검증 묶음 | 필수 사례 |
|---|---|
| lineage | 정상 exact join, 같은 종목 다른 attempt, hash 충돌, payload 세대 변경, retry 중복, warm cache upgrade, gzip/partial write |
| 시간·scope | 이후 snapshot 혼입, stale capacity, `_AL`/정확 route 불일치, 타세션·타정책 응답, 명시 UNKNOWN |
| 응답 | 정상 PASS/CAUTION/VETO, transport timeout, schema/semantic 오류, citation 중복/없는 fact, 수선 전후 provenance |
| operating | 조건부 probe 관측 무예약, fill anchor 미상, 당시 stop 없음, 비용 일부 없음, 부분체결·취소 pending·late fill |
| 연구 소비 | 변화0 후보 제외, 성공 제외 집계, 중복기회 가중, train-only 조건/선택, reused holdout, 분모 보존, 원천 gap의 null 유지 |
| 종목 분리 | 유효 종목 식별, 삼성전자/그 외 집합 교집합0·합계 일치, 미식별 별도 제외, 타 집합 cache/후보/응답 누출 차단, 공통 producer의 양쪽 원천 보존 |
| 불변성 | 테스트/격리 계산 전후 policy hash 동일, live import/caller 추가0, provider/REST/주문·reservation 호출0 |

종료 단계는 `계획 검토 → 구현/재리뷰 → 표적 회귀/compile/diff → 격리 재생성 → source/행동/성능 audit → 허용된 후속 작업`이다. lossless 복원 가능한 결함만 닫고, 과거 미기록 stop/fill 원천은 `historical_source_gap`으로 명시 종료한다. 존재하지 않는 응답/경제성을 만드는 재실행을 반복하지 않는다.

**현재 상태:** A0~A5 구현·리뷰·보완·표적 회귀·격리 재생성 완료. [실행 리뷰](../audits/samsung-auxiliary-scope-execution-review-2026-10-03.md) 참조. plan 실패의 capsule/capacity 보존, 단계 ledger, 비용 scope 대소문자 결함, CAUTION 계보, 종목 분리 cache/발행 차단을 보완했다. 그 외34개 유효 응답 중 native15기회가 비용 결합 stage에 적격했으며12조합의 행동 변화는0이다. 과거 미기록 stop/fill은 historical source gap으로 남는다. canonical 장후 재생성·prompt 호출·배포·재기동은 하지 않았고10/6 자연 수용 owner는 유지한다.
