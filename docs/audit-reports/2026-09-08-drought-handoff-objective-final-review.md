# Drought workorder → EV → summary → strict verifier 목적·자동화 최종 리뷰

최초 관찰 기준: **2026-09-08 13:03 KST**. 아래 최초 리뷰는 읽기 전용 기록이다. 이후 사용자의 권장보완 구현 요청에 따른 수정·검증은 [후속 구현](#후속-권장보완-구현)에 구분해 기록한다.

## 판정

현재 코드 보완 상태는 아래 후속 구현을 따른다. 이 절의 P1/P2는 수정 전 발견 기록이며 과거 원천 결손과 자연·경제성 acceptance는 계속 별도다.

**보완 필요: P1 1건, P2 3건(기존 OPEN 이력 결손 F3 포함). 전달 기능과 조건부 PREOPEN 자동 적용은 존재하지만, 이 경로 전체를 ‘실효성까지 닫힌 자동 개선’으로 승인할 수 없다.** 고정된 큰 양수 수익률을 요구하는 초기 ON 문턱은 발견하지 않았다. 핵심 문제는 지시별 전달 대사, controller 소비 가능성의 조기 검증, schema 전환 이력과 무효 경로의 유지 판단이다.

당일 main PID682672는 실행 코드 `b27a67dc`를 사용하며 `KORSTOCKSCAN_ENTRY_OPPORTUNITY_RECHECK_ENABLED=false`, allowed scopes는 빈 문자열이다. 전체 runtime env 검증 PASS와 이 family의 OFF는 양립한다. `early_accel_recheck_runtime` 등 다른 recheck owner의 ON을 이 family의 적용으로 세지 않는다.

## 확인된 연결과 권한

| 단계 | 실제 구현과 검토 결과 |
| --- | --- |
| Sentinel → workorder | native drought ID와 5개 weak-contract ID를 source-only 지시로 수집한다. 생성 자체는 코드 자동 수정이나 실주문 권한이 아니다. |
| workorder → EV → runtime summary | EV가 지시 목록/판정의 진단 사본과 `entry_submit_drought_handoff_selected`를 만들고 runtime summary가 critical/selected 및 Sentinel contract를 전달한다. EV 사본은 명시적으로 `diagnostic_previous_generation_not_ev_decision_input`이며 최종 workorder의 권위를 대체하지 않는다. |
| tower/checklist → strict verifier | 현재 원본 파일들의 SHA256과 날짜를 대사한다. 실제 wrapper 마지막 명령은 `--require-summary-handoff`다. 파일 최신성 검증은 개별 지시의 마지막 consumer·정책 선택·실효성 대사와 다르다. |
| Sentinel → daily controller → PREOPEN | 별도의 `entry_recheck_drought_controller`가 같은 scope의 drought와 exact attribution으로 기존 family 후보 최대1개를 만든다. PREOPEN은 workorder/summary가 아니라 이 controller를 직접 소비한다. |
| 설치된 자동 적용 | cron은 20:10 postclose, 다음 거래일07:35 `auto_bounded_live`/`auto_apply=true`, 07:55 launcher 기동이다. recheck의 deterministic 후보는 별도 AI 재승인을 요구하지 않는다. PREOPEN의 schema/source/owner/dependency/override 검사는 유지된다. |
| 실제 적용 | 9/8 apply plan의 controller 상태는 loaded/adjust_down, 허용 후보1개였지만 추천값은 enabled=false다. 이는 OFF 정책이 자동 전달된 것이며 자동화 미기동과 다르다. 이후 코드의 validator를 다시 실행한 결과와 당시 apply receipt는 별도 시점으로 보존한다. |

## 최종 finding

### F1 · P1 — strict verifier가 다음 PREOPEN의 controller 소비 계약을 검사하지 않음

- 위치: `src/engine/verify_threshold_cycle_postclose_chain.py`의 `_artifact_paths` 및 `_buy_funnel_submit_drought_handoff_status`; `src/engine/automation/postclose_summary_handoff.py`의 `source_paths`.
- 근거: verifier artifact registry와 tower/checklist source hash 목록에 `entry_recheck_drought_controller`가 없다. drought 검사 함수는 controller 또는 PREOPEN contract를 받지 않는다. wrapper의 생성 직후 파일 대기는 있지만, JSON에 유효한 후보가 있는지와 최종 Sentinel generation을 소비했는지까지 마지막 verifier가 보장하지 않는다.
- 직접 영향: controller가 유효 JSON이지만 소비 불가능한 상태이거나 이후 누락·변경돼도 이 전달 검사는 통과할 수 있다. 다음 PREOPEN은 별도 validator에서 안전하게 freeze할 수 있지만, 전날 완료 판정이 이 연결 결손을 조기에 드러내지 못한다. 안전 우회가 아닌 운영 handoff 검증 결함이다.
- 실제 재현: 9/7 canonical controller를 **현재** PREOPEN contract checker로 읽기 검증하면 `drought_sentinel_exact_contract_invalid`다. 이는 9/8 오전 당시 성공 receipt를 소급 취소하는 판정이 아니다.
- 보완: 설치 flag가 ON인 controller의 target date·policy version·source evidence hash·후보 ON/OFF 판정을 shared pure validator로 최종 검증하고, 다음 PREOPEN이 같은 후보를 재검증한 receipt까지 기존 owner에 연결한다. valid OFF/정상 무표본은 실패로 바꾸지 않는다. 불량 family 때문에 무관한 다른 family를 차단하는 새 전역 gate도 만들지 않는다.

### F2 · P2 — 개별 지시의 EV 전달 누락·판정 변경을 aggregate flag가 가림

- 위치: `src/engine/threshold_cycle_ev_report.py`의 `_code_improvement_workorder_summary`, `src/engine/verify_threshold_cycle_postclose_chain.py`의 `_buy_funnel_submit_drought_handoff_status`.
- 재현: 현행 producer fixture(schema6/exact3)로 canonical workorder의 필수6개 ID를 보존하고 EV의 `code_improvement_workorder.orders=[]`, selected flag=true로 주었다. Sentinel contract 사본을 일치시킨 상태에서 결과는 `status=pass`, `downstream_closure_status=pass`, `missing=[]`였다.
- 의미: 이는 직접 handoff 검사 함수의 재현이며 전체 운영 strict 명령을 실행한 결과는 아니다. 별도의 summary SHA 검사도 EV 파일의 현재 bytes를 확인하는 검사라서, 원본과 사본 사이 ID/decision 의미 대사를 대신하지 않는다. 현재 9/7 산출물의 해당6개 판정은 실제 대사 결과 일치했으므로 과거 누락이 발생했다고 주장하지 않는다.
- 보완: canonical의 ID/decision/implementation/후속 consumer를 전수 정규화한 semantic receipt를 마지막 요약에서 대사한다. 최종 workorder는 EV 뒤 다시 생성되므로 EV 진단 사본의 full-file hash를 canonical과 동일하게 강제하여 순환 재생성하지 않는다. 이전 EV 사본은 진단으로 남기고 최종 요약의 authoritative 현재 disposition을 검사하는 방식이 적절하다.
- 제거 검토: 단일 `selected=true`를 ‘전수 지시 전달 완료’의 단독 승인 근거로 쓰는 경로를 제거한다. 지시문/보고서 체인 전체를 제거할 사유는 아니다.

### F3 · P2 — schema 전환 때 rolling 이력 재확보가 반복되며 자동 복구/전환 판정이 없음

- 위치: `src/engine/automation/submit_drought_contract.py`의 `CURRENT_SCHEMA_VERSION=6`, `validate_submit_drought_contract(require_current=True)`, `validate_scope_evidence`; `src/engine/scalping/entry_ai_gate_backtest.py`의 `_drought_day_summary`.
- 재현: 현행 검사에서 9/4 schema3와 9/7 schema5는 `current_schema_required`로 탈락했다. 9/8의 현행 KRX scope는 검사에 통과했다. 9/7 controller가 처음 만들어질 때에도 9/3·9/4 이력 결손으로 `history_source_quality_pass=false`, desired_enabled=false였고 이것이 9/8 OFF 추천으로 전달됐다.
- 달성 가능성: 과거 원천 복원/검증된 호환 전환 없이 새 날짜만 사용한다면 9/8·9/9·9/10의 유효 이력을 얻은 뒤 **가장 빠른 자연 ON 검토는 9/11 PREOPEN**이다. 3일 source 품질과 최근일 포함2일 addressable drought를 모두 충족한다는 조건부 하한이며 적용 예정 확약이 아니다. 버전 변경이 반복되면 이 대기 창도 반복된다.
- 보완: 단순 버전 숫자 차이와 실제 required-field/identity 결손을 분리하는 버전 전환 검토를 둔다. 원본·제외 이력 보존, 직접 원천으로 검증 가능한 필드만 deterministic 재구성, 불가능한 과거 결손은 제외하고 선언된 새 관찰창으로 넘긴다. schema 숫자만 바꾸거나 current-schema 검사를 해제하는 완화는 부적절하다.
- 현재 상태: 버전 전환으로 생긴 이력 결손이며 경제 표본 부족과 구분한다. 신규 원천으로 닫을 경우 위의 조건부 관찰창을 선언하고, 과거 복원 경로는 원본의 실제 필드·identity로 따로 검증해야 한다. 기존 `EntryRecheckNaturalAttribution0907`의 이력 복원 가능성 검토와 같은 미완료 범위이며 새 결함으로 중복 집계하지 않는다.

### F4 · P2 — 무효 경로를 계속 유지할 수 있고 개선 검토 지침에 순환 조건이 있음

- 위치: `src/engine/scalping/entry_recheck_policy.py`의 `_scope_controller_decision`, `src/engine/scalping/entry_recheck_drought_controller.py`의 Markdown next action; `src/engine/build_code_improvement_workorder.py`의 drought implementation marker와 repeated structural blocker 제외 분기.
- 재현: 같은 scope에 정확하고 addressable한 drought history를 연속 공급하되 recheck evaluated/armed/submit/paired를 모두0으로 유지했다. 20개 유효 거래일 모두 desired_enabled=true, stop_reasons=[]였다. ON일 수는 있어도 실제로 평가되는 경로라는 보장은 없다. 이 synthetic 결과를 현재 실전에서20일간 발생한 일로 보고하지 않는다.
- 추가 근거: exact 원인 분류가 끝나면 submit0/critical 상태에서도 marker는 `implemented`, `root_cause_closed`가 되며 반복 구조 blocker 승격에서 제외된다. 진단 수리 완료 표시는 적절하지만, 별도 경제성/효용 owner 연결 없이 이를 개선 종결로 읽으면 잘못이다. controller next action은 “paired economics floor 이후에만 지배적인 evaluated blocker의 non-safety 개선을 설계”하라고 해 no-arm→paired0 경로에서 검토조차 영구 대기할 수 있다.
- 보완: 코드 수리 완료는 그대로 유지하고, 유효 source 거래일·실제 policy/PID 소비·eligible 원천→evaluated→armed→submit→filled→paired 전환에 근거한 유한 유지 판단을 별도 연결한다. `repair_source|keep_collecting|merge_with_existing_owner|retire_redundant_path`는 명확한 owner·증거·수용조건을 가져야 한다. 자연 기회가 없는 날은 결함으로 세지 않는다.
- 제거 검토: paired/economic floor를 **원인 조사·source-only 설계의 선행조건**으로 요구하는 문구는 제거하는 것이 타당하다. 실제 runtime 확대의 비용·표본·guard는 별도 유지한다. 충분한 유효 관찰창 뒤에도 eligible 입력은 있는데 전환이 없고 기존 WAIT/recheck owner와 중복이면 해당 중복 경로의 통합/퇴역을 검토한다. 자동 disable·cap 변경은 이번 리뷰에서 하지 않았다.

## 비용 차감 소액 반복수익과 조건의 타당성

| 조건 | 판정 |
| --- | --- |
| 초기 활성 | 최신일 포함3거래일 중2일 동일 scope의 addressable critical. 분모는 ai≥20 또는 budget≥3이고 각각 submit 비율<20%, ≤10%. 실현 양수 EV10건을 초기 ON 전에 요구하지 않음. 미제출 상태에서 실체결을 먼저 요구하는 초기 순환 gate는 없다. |
| 실전 경로 | canonical WAIT/WAIT_REQUOTE·EDGE·eligible probe intent·recovery_required, fresh quote·micro 확인·probe dependency와 기존 broker safety가 필요하다. score69~74.999는 코드에서 prior band로 기록되며 단독 점수 차단으로 해석하면 안 된다. 현행 여러 recheck owner와의 중복/유효 모집단은 별도 확인 대상이다. |
| 확대/중단 | 같은 scope·fill-quality의 paired≥10, 순EV>0 및 실제 순손익>0이면 확대 검토 가능. armed≥20에서 direct submit<10% 또는 mature cohort 순성과≤0이면 중단. fixed +1%·+2% 같은 큰 수익률 문턱은 없음. |
| 작은 양수 수익 재현 | 격리 fixture에서 paired10, 순EV0.000001%, 순손익0.01원을 넣어 desired_enabled=true 및 escalation=true 확인. 산술 gate 수용성 증거이며 이 값이 실제 주문에서 경제적으로 실현 가능하다는 주장은 아님. |
| 표본 달성 | 기본3회/일 recovery와 rolling20거래일은 산술상 최대60회 제출 여지를 가진다. 같은 scope/cohort의10건은 최상의 경우4거래일이지만, 실제 eligible/fill/terminal/비용 결속률이 필요하다. 20일 창에서 cohort별 paired 유입이 평균0.5건/일 미만이면 floor 유지가 어렵다. 현재 OFF·미평가 상태로 finite 경제성 ETA나 성공확률을 산출할 수 없다. |
| 목적 부합 범위 | 이 축은 기존 기회를 다시 평가하고 제출 병목을 드러내는 보조 owner다. 작은 순수익·빈도·자본점유를 직접 최적화하거나 최적 entry/exit 정책을 탐색하는 엔진은 아니다. 기존 가격·holding/trailing·Daily 승인 owner의 실현 순성과에 연결돼야 목적 달성을 판정할 수 있다. |

따라서 **안전·비용 검증과 family별10건 floor를 일괄 낮추는 것은 권고하지 않는다. 먼저 F1/F2의 자동 전달 보증, F3의 이력 전환, F4의 source-only 유지/제거 판단을 보완**하는 순서가 적절하다. 그 뒤 실제 자연 funnel이 성립하는지 확인해야 확대 조건의 과도함을 경제적 근거로 판단할 수 있다.

## 검증과 범위

- 관련 테스트: `test_entry_recheck_policy`, `test_entry_recheck_drought_controller`, `test_postclose_summary_handoff`, `test_verify_threshold_cycle_postclose_chain`, `test_build_code_improvement_workorder`, `test_threshold_cycle_ev_report`에 `-k 'drought or summary_handoff or scope or economic or paired or activation or recheck'` 적용. **86 passed, 329 deselected**. 기존 테스트 통과는 위 미검증 계약의 finding을 무효화하지 않는다.
- 추가 재현은 기존 producer fixture·pure validator·controller 함수를 메모리상 호출했다. broker/Provider 요청·운영 report 재생성·runtime apply·재기동·주문을 하지 않았다. 전체 strict 운영 명령은 실행하지 않았다.
- 문서 링크, 기존 OPEN owner의 print-only parser 포함과 `git diff --check`를 검증했다. 외부 Project/Calendar sync는 실행하지 않았다.
- 9/8 마지막 장후 canonical 산출물은 아직 due 전이다. 9/7 canonical과9/8 장중 source/현재 코드 검토를 당일 장후 자연 성공으로 혼합하지 않는다.
- 리뷰 기준 HEAD는 `1010e97a`. 다른 세션의 `build_code_improvement_workorder.py` 및 AI/scanner 수정이 존재하며 이를 이번 작업의 수정·배포로 주장하지 않는다. 해당 파일을 포함한 당시 작업 트리에서 관련 테스트를 실행했다.
- 13:03 SHA256: verifier `809268e67f49f9a487442f7cb402c4c8e436fc151c730bef216f7e1bb8470ca9`; recheck policy `05b5949fb6d4ff3bc9eec44d3794ceb3cbc776511b5b9f5a534c69f5aaac2187`; drought contract `9c97029170338a0beed0b4999401eb15412e66884122a67ca79a7d63dc04659f`; PREOPEN `e4b163c4f41dcce42758961a3d4b7381105d29bb01f94d03bfa9a4d1a556341a`; workorder `9f729be8d50cfee3f90ba03ad5f50528a0047d06fdb0eef68f086deb95c97855`.
- 기존 OPEN owner: [당일 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 `EntryRecheckNaturalAttribution0907`, `CodeImprovementWorkorderReview0908`, `PostcloseRecoverySourceAcceptance0908`. 별도 중복 실행 ID를 만들지 않는다. 기준/권한은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md), [traceability](../report-based-automation-traceability.md), [장후 지시문](../postclose-tuning-result-review-task-instructions.md)을 따른다.

## 후속 권장보완 구현

사용자 후속 요청에 따라 F1~F4의 source-only 코드·계약을 보완했다. 검토 범위의 미해결 코드 finding은 0이며, F3의 과거 원천 복원과 다음 자연 적용·실현 순이익은 완료로 바꾸지 않는다.

| Finding | 구현 결과 | 남은 수용조건 |
| --- | --- | --- |
| F1 | `automation/drought_handoff.py`가 canonical Sentinel bytes·scope/preflight 의미와 controller candidate의 동일 policy를 검증한다. strict와 PREOPEN은 기존 결정 validator를 공유하며 missing/changed/malformed/ON·OFF 불일치를 차단한다. tower/checklist는 recheck controller를 source로 결속한다. | 정기 장후의 새 source binding 및 다음 정기 PREOPEN/PID 소비 |
| F2 | 최종 runtime summary가 최신 canonical 전체 지시·판정·권한·acceptance와 hash를 보존한다. EV 이전 세대 사본의 ID 누락·제거·판정 변경은 명시적 진단 diff다. `selected=true`만으로 전수 전달을 승인하지 않는다. | 새 canonical→summary→strict의 자연 receipt |
| F3 | 일별 source schema/hash와 직접 validation·scope exclusion을 보존한다. 전환 결손과 조건부 신규 이력 확보일을 별도 출력하며 역사 데이터를 합성하지 않는다. | 새 exact 3거래일 및 동일 scope 조건. 9/8만 유효한 fixture에서는 조건부 가장 이른 PREOPEN=9/11 |
| F4 | `scalping/entry_recheck_review.py`가 첫 고갈 stage·유효 source 날짜·floor·유한 유지 검토를 출력한다.20 유효 drought 거래일에도 전환/paired 부족이면 repair/merge/retire 검토다. 경제성 floor를 원인 조사 선행조건으로 삼던 문구를 제거했다. | 실제 policy/PID와 자연 funnel을 기존 owner에서 대사. 자동 disable·cap 변경 없음 |

유지 검토의 native ID 두 개는 producer 원판정 `objective_followup_required`를 보존하고 canonical에서는 `defer_evidence`/기존 natural acceptance owner로 연결한다. `max_orders=1`에서도 누락되지 않음을 실제 producer의 임시 파일 생성으로 검증했다. 이미 닫힌 진단 코드를 매번 새 `implement_now`로 만들거나 자연 증거 대기를 구현 완료로 분류하지 않는다.

리뷰 중 추가로 보완한 사항:

- 실제 workorder 날짜 필드 `date`와 canonical 경로를 사용하도록 정정했다.
- hash만 바꾼 stale 의미, candidate와 root policy 불일치, source 생성 도중 변경, malformed JSON 계약, 지시 중복·권한 누출을 검증한다.
- 20일 유지 진단의 source drift는 장후 재검토 사유이며 PREOPEN에 새 표본/활성화 문턱을 만들지 않는다. PREOPEN의 직접 결정용 3일 source는 계속 검증한다.
- controller source 변경으로 workorder fingerprint도 함께 stale해지는 복구를 같은 최소 체인에 포함했다. 복구 계획은 controller→workorder→summary→일반 verifier→tower→checklist→strict이며 EV/Provider/수동 env 적용 명령이 없다.
- 자연 기회 없음, policy/PID 소비 미확인, 실제 evaluated 이후 차단과 paired floor 부족을 분리했다. 진단 bound는 runtime 중단 명령이 아니다.

새 모듈 위치는 공통 전달 검증을 `automation`, recheck 유지 진단을 `scalping`, 회귀 검증을 `src/tests`로 정했다. `src/engine` root에 모듈을 추가하지 않았다. 기존 동시 작업의 AI/scanner 변경은 보존하고 이번 보완으로 보고하지 않는다.

최종 검증: 관련12개 테스트 파일 **556 PASS**, PREOPEN 직접 recheck/drought **9 PASS,233 deselected**, 합계 **565 PASS**다. 실제 strict verifier 호출부에서 controller 필수/설치 OFF를 검증했으며, source-quality 실패가 겉보기 경제성 건수보다 먼저 드러나는 회귀도 포함한다. Python compile, 문서 링크·anchor, print-only parser와 `git diff --check` PASS. parser의 기존 `EntryRecheckNaturalAttribution0907`은 당일 owner로 정확히1개다. 작은 양수 순EV 허용, 초기 ON에 paired10 미요구, same-scope/cohort stop·확대 guard를 유지한 기존 테스트도 통과했다. self-review→보완→재리뷰 후 검토 범위 P0~P2 finding0이다.

운영 범위: 테스트는 임시 디렉터리의 producer/consumer fixture와 순수 검증·복구 계획을 사용했다. 운영 controller/EV/summary 재생성, runtime env·threshold·provider·수량·safety 변경, 주문, 재기동을 실행하지 않았다. 새 코드의 정기 장후 소비와 다음 PREOPEN/PID 및 실현 순이익은 당일 checklist의 기존 OPEN owner에서 확인한다.
