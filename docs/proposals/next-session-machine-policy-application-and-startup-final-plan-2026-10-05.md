# 다음 영업일 기계 정책 적용·정상 기동 최종계획 — 2026-10-05

## 1. 목적·범위·날짜

사용자의 요청은 최종 적용계획, 디스크 정리계획, 다음 장후 생성 방식의 설명이다. 이번 작업은 현재 경로를 읽기 전용으로 확인하고 계획을 확정한다. 코드 수정·정책 발행·배포·기동·삭제는 이 문서 작성으로 실행되지 않는다.

[프로젝트 거래일 판정](../../src/utils/market_day.py) 기준10/5는 개천절 대체휴일, 다음 거래일은 **10/6**, 그 다음은 **10/7**이다. 따라서10/6 장전 정책은 이미 확보한10/2까지의 자료로 준비하고,10/6 새 자료의 장후 평가 결과는10/7 적용 대상으로 만든다.10/6 자료를10/6 장전 검증으로 소급하지 않는다.

목표는 다음 세 가지를 각각 닫는 것이다.

1. 비삼성 `pullback_p60_v0`의 공용 판정·운영 정책 연결 및 선정 가능 여부를 확정한다.
2. Main·Widget·Episode의 허용된 운영 범위에서 정확한 유효일 정책과 기동 경로를 검증한다.
3.10/6 장후에 삼성/비삼성을 분리하여 고정 후보와 부모를 비교하고, 선정 또는 승계 사유를 남기는 생산자→소비자 경로를 마련한다.

현재 연구는 [최종 비교](../audits/non-samsung-final-policy-decision-review-2026-10-05.md)의 `candidate_recommended`로 종료됐다. 재사용한9/29·9/30·10/2 자료로 새 임계치를 반복 탐색하지 않는다. 운영 구현의 세부 규칙은 [고정 후보 구현계획](non-samsung-pullback-candidate-implementation-plan-2026-10-05.md)을 따른다.

## 2. 현재 확인된 상태와 선행 결손

10/5 읽기 전용 점검 결과다. 이후 실행 직전에 selector·원천 세대·서비스·PID를 다시 확인한다.

| 항목 | 확인한 상태 | 의미와 다음 조치 |
| --- | --- | --- |
| Main 선택 release | `integrated-source-review-20261004-9c0c0632`, commit `9c0c0632faaf61c7c4434c2fa77b8673125e050d` | 작업본 HEAD `99cf22c1` 및 미커밋 연구 수정과 다르다. 작업본의 후보 함수를 운영 반영으로 계산하지 않는다. |
|10/6 prepared | index의 기존 receipt는 `prepared_verified`, `actual_pid_consumed=false` | 현재 검증을 대신하지 못한다. 아래 현재 실패를 복구한 뒤 최종 세대로 다시 봉인한다. |
| **현재 PREOPEN 검증** | 선택 release cwd에서 `--verify --target-date 2026-10-06` **FAIL** | `postclose_controller_not_closed:strict_current_contract:postclose_stage_invalid:collector_recommendation`. 현재 정상 준비 완료 선언 불가. |
| collector 상세 원인 | `stage_receipt_issues(..., '2026-10-02', 'collector_recommendation')` → `collector_recommendation:history_generation_changed` | 저장된 history manifest와 현재 manifest가 다르다. 변경된 파일 목록/바이트·reader 범위를 먼저 대사한다. 원천 손상 또는 정책 품질 저하로 단정하지 않는다. |
| Widget | trader PID3614517, collector PID3137230의 실제 cwd가 `postclose-winrate-readiness-20261003-e6d4d3b9` | 독립 service pin과 실제 PID가 일치하는 별도 release다. Main selector와 다르다는 이유로 강제 통합하지 않는다.10/6 정책 reload 증거는 별도 필요하다. |
| Episode |10/5 `cj_cgv_morning` preflight: `blocked_invalid_candidate / candidate_source_quality_hash_mismatch`, exit2 | 전체 profile의 현재 실패 원인을 분류해야 한다. 과거 격리3개와 오늘의 source hash 실패는 다른 분류다.10/4의58개 baseline valid를 오늘 기동 PASS로 쓰지 않는다. |
| 신규 비삼성 후보 | 연구·구현계획만 존재. 선택 release에는 `entry_pullback_buy_flow_research.py`, `entry_observation_recipe_policy.py`가 없음 | 명시적 운영 schema·공용 evaluator·publisher·loader 연결 필요. 연구 JSON 복사로 적용하지 않는다. |
| 장후 자동 생성 경로 | `main_machine_policy`는 `ai_action_outcome_calibration --winrate-policy-only` | 현행 VWAP veto 계열 생성이며 새 pullback 관측 후보를 자동 소비하지 않는다. 자동화 연결이 필수 작업이다. |

근거: [release selector](../../data/runtime/runtime_release_selection.json), [prepared index](../../data/runtime/policy_bootstrap/prepared/2026-10-06/latest.json), [collector terminal](../../data/report/postclose_stage_terminal/2026-10-02/collector_recommendation.json), [handoff 생산자](../../src/engine/automation/postclose_summary_handoff.py), [이전 배포 기록](../audits/integrated-deployment-and-disk-cleanup-review-2026-10-04.md). 이전 배포 PASS는 당시 증거로 보존한다.

### 적용 정책의 기본 결정

| 범위 |10/6 적용계획 | 적용 보류 시 |
| --- | --- | --- |
| 삼성전자 `005930` | 현재 유효한 기계 정책을 명시적으로 상속. 기존 삼성 연구는 별도 고정 후보/날짜 검증 owner 유지 | 비삼성 성과로 삼성 정책을 변경하지 않는다. 새 삼성 전용 정책이 생겼다고 표시하지 않는다. |
| 비삼성 `KRX / KRX_REGULAR` | `pullback_p60_v0`의 구현 및 운영 자격을 충족하면 해당 component만 교체 | 현행 적격 정책을 승계하며 `candidate_pending`의 정확한 사유를 기록한다. 후보 적용 완료로 세지 않는다. |
| 비삼성 다른 venue/session | 기존 유효 component 승계 | 정규장 연구의 성과를 NXT·장전·장후에 전용하지 않는다. |
| 보조 AI·보유/청산·주문 | 각 기존 owner/정책을 보존하고 별도 유효성 확인 | 기계 후보 선정에 보조 AI 결과를 혼합하지 않는다. |
| Widget / Episode | 각 symbol/profile의 유효한 적용 정책·custody·service pin 확인 | 기존 격리/OFF 유지. 원천 결손 profile을 무조건 가동하거나 Main 정책을 복사하지 않는다. |

현재 자동 발행 계약은 native opportunity와 독립 검증을 요구한다. 연구 관측을 native ID로 바꾸거나 재사용한10/2를 새 holdout으로 표기할 수 없다. 따라서 **현 상태만으로10/6 신규 후보의 자동 적용을 확정할 수 없다**. 관측 기반 최초 도입 계약이 필요하면 기존 자동 갱신 계약과 차이·불확실성·적용 범위·되돌림을 먼저 구체화하고 해당 계약 변경 권한 안에서 처리한다. 이 계획 자체가 새 발행 자격을 만들지는 않는다.

## 3. 실행 순서와 종료 기준

| 단계 | 실행 내용 | 완료 증거·실패 시 처리 |
| --- | --- | --- |
| P0 입력 고정 | dirty diff, HEAD, selector/previous, 독립 service pin, 실제 PID/custody/open order, source·policy·prepared SHA를 수집한다. [정리계획](runtime-and-research-storage-cleanup-plan-2026-10-05.md)의 보호 목록도 만든다. | 원본/rollback/고유 연구 자료 보존. 주문 상태 확인은 기존 read-only receipt/API 권한 범위이며 주문 변경 금지. |
| P1 현재 준비 결손 복구 | collector history manifest의 추가/삭제/변경 경로를 대사하고 유효 입력으로 해당 stage부터 필요한 의존 단계만 갱신한다. Episode는 profile별 candidate hash, 실제 source hash, 유효일/적용 정책/authority를 대조한다. | terminal status나 기대 hash만 고쳐 PASS를 만들지 않는다. `history_generation_changed` 소멸, Episode마다 eligible / quarantined / source-blocked / disabled 구분. 손실된 원천은 null/결손 유지. |
| P2 후보 운영 구현 | 공용 evaluator·명시적 삼성 제외 scope·recipe schema·판정 capture·policy parent/hash·dated publisher/loader를 연결한다. `postclose_summary_handoff`의 등록 stage, CLI, terminal, summary consumer까지 연결한다. | 연구와 공용 판정 차이0, source/hard guard 우회0, 대상 밖 상속. research adapter와 live 구현의 중복 규칙 제거. 자동화 변경 시 관련 운영 문서/checklist도 같은 변경에 반영한다. |
| P3 선정 계약 대사·리뷰 | 현재 parent와 연구 parent의 행동 차이, native/probe 분모, 날짜·지원조정 승률·coverage·기존 publisher 요건을 대사한다. 구현→리뷰→수정→표적 회귀→재리뷰를 반복한다. | 후보 발행 가능/불가 및 정확한 결손을 확정. 기존 성공100%/80% 보존 veto와 양의 청산CF 조건을 새 진입 탈락 조건으로 추가하지 않는다. |
| P4 불변 배포·준비 | 실행 권한 안에서 검증된 변경만 commit/release에 봉인한다. Main·Widget·Episode별 변경 파일/consumer를 대조해 영향 있는 pin만 전환한다. 관련 source stage→summary/checklist 확정→strict `--require-summary-handoff`→controller→prepared 순서로 같은 세대를 만든다. | 선택 release 물리 경로에서10/6 `current_full_contract` PASS. 최종 checklist/source가 바뀌면 기존 PASS 재사용 금지. 유효 정책/rollback hash 및 loader 수용 증거 확보. |
| P5 당일 소비 검증 |10/6 PREOPEN activation, Main 실제 PID, Widget reload, Episode 각 profile preflight/PID를 확인한다. | release·source day·effective day·parent/component·scope hash를 실제 consumer에 결속. 삼성/비삼성 최소 한 건씩 자연 판정 receipt를 확인하며 없으면 `not_observed`. |

P2/P3 표적 검증에는 조건 경계(60/100/0/10), NaN/누락/stale/future 입력, 기존 BLOCK 유지, 허용된 confirmation fact만 상쇄, 미해소 위험/situation veto,005930 제외, NXT/다른 세션 상속, 잘못된 parent·유효일·recipe 거절, 이전 정책 되돌림을 포함한다. Python compile/해당 pytest, wrapper 변경 시 `bash -n`/계약 검사, diff/link/단일 owner/parser를 수행한다. API 요청·파서·FID 변경이 필요해질 때만 공식 Kiwoom 참조 gate를 추가 적용한다.

발행 충돌도 검사한다. `main_machine_policy`, `legacy_machine_report`, 기존 runtime publisher의 쓰기 대상·순서를 대조해 **하나의 machine component에는 하나의 최종 발행 owner**만 둔다. 동일 실행에서 새 recipe가 이전 veto 보고서로 덮이는 경로를 허용하지 않는다. 삼성/비삼성 component를 한 bundle로 묶더라도 각 부모·근거·선정 상태를 분리한다.

### 일정과 결정 시점

아래 시각 중 자동 trigger는 현재 설치값, 마감 시각은 이 계획의 제안이다. trigger 도래는 실행 성공이나 시장일 허가 증거가 아니다.

| 시점 | 수행·판정 |
| --- | --- |
|10/5 준비 창 | P0~P3, 검증된 정리 대상만 별도 실행, release/정책/원천 세대 동결 준비. |
|10/6 05:00 설치된 finalizer 이후 | P4의 최종 세대를 확인. finalizer가 오래된 stage 실패를 자동으로 해결했다고 가정하지 않는다. |
|10/6 **07:20 결정 마감(제안)** | 후보가 P2~P4를 통과했으면 후보 적용 대상으로 확정. 부족하면 적격 incumbent 승계 여부를 검증. incumbent도 준비 계약 실패라면 해당 consumer를 준비 완료로 선언하지 않고 원인 복구 대상으로 남긴다. |
|07:32 정책 auto-apply /07:35 Main PREOPEN | symbol/profile별 정책 및 Main bootstrap accepted/rejected 확인. |
|07:55 Main start /07:58 Widget timer | 실제 PID cwd·시작 시각·policy 소비 검증. 이미 active인 Widget은 timer만으로 새 코드/정책 소비를 입증하지 못한다. 필요한 reload/restart는 해당 실행 권한·custody 확인 후 수행한다. |
|Episode profile별 시간 창 | 해당 profile의 당일 preflight→정책→PID→자연 receipt를 확인. 전체 profile 수를 일괄 성공 수로 보고하지 않는다. |
|20:05 EOD /20:10 postclose | 아래 §4의 원천 날짜10/6 평가 및10/7 정책 준비. 실제 stage는 predecessor 완료를 기다리며,20:50 archive와 원천 봉인/reader가 충돌하지 않는지 확인한다. |

정상 기동의 최종 수용은 `준비 PASS → 당일 activation → 허용된 consumer의 실제 PID/정책 hash → 자연 관측`이다. 모든 종목에 ENTER가 발생하거나 주문/수익이 발생해야 기동 성공인 것은 아니다. 실제 경제성은 `COMPLETED + valid profit_rate` 및 정확한 비용 원천으로 별도 보고한다. 원천/정책 불일치, guard 우회 또는 잘못된 scope가 나오면 해당 변경을 멈추고 직전 적격 component/release로 되돌릴 수 있는지 검증한다. 단기 승률만으로 operator lock이나 격리를 해제하지 않는다.

## 4.10/6 장후에는 어떻게 분석하고 생성하는가

### 4.1 현재 설치된 방식

[등록 dispatcher](../../src/engine/automation/postclose_summary_handoff.py)의 `main_machine_policy`는 `ai_action_outcome_calibration --target-date <source_date> --write --winrate-policy-only --publication-date <publication_date>`를 호출한다. 선택 release와 작업본의 `load_machine_observation_rows`, `build_winrate_policy_report`, CLI `main` 함수 내용 SHA가 이번 점검에서 각각 동일했다. 새 관측 연구 함수가 작업본에 있는 것만으로 이 호출이 바뀌지 않는다.

1. 당일 natural source receipt와 tuning input 허용 여부를 먼저 확인한다. 현재 원천 계약 실패를 과거 정상 자료로 덮지 않는다.
2. 정책 기간의 capture/trace/pipeline·source-quality·원 비용·완료 가격 경로를 읽는다. 현재 관측 loader의 하한은9/29이며 target date 이후는 제외한다. 동일 source/kernel hash의 cache만 재사용한다.
3. 유효 원 비용 결합 경로의 `net_target_first` / `exact_stop_first`와 실제 scanner/fixed-watch의 native opportunity identity를 사용한다. probe·ID 결손·모호한 결과는 분리한다.
4. 현재 `KRX|KRX_REGULAR` 정책에서 **micro VWAP 괴리 veto 임계값**을 학습 자료로 비교한다. 기존 base ENTER의 필터 조정이며, 고정 pullback 조건으로 RECHECK를 새 ENTER로 바꾸는 탐색은 이 경로에 없다.
5. 최신 미소비 날짜를 검증으로 분리한다. 최초 forward일만 있는 경우의 시간순 기회 분할과 그 receipt도 별도로 검사한다. 기존 자동 successor 계약은 학습 선택30기회·검증10기회 이상, 양쪽 raw 승률 개선, 지원조정 승률+5pp 이상, 부모 대비 선택 기회50% 이상 및 source/holdout 계약을 요구한다. 최초 도입의 고정 재현 경로는 별도다. **50%는 선택 기회 coverage이며 기존 성공 종목 보존율이 아니다.** 성공100%/80% 보존은 이 successor 탈락 조건이 아니다.
6. 통과하면 dated 정책을 stage하고, 미충족이면 원인과 incumbent 승계를 남긴다. 보고서 생성·stage·다음날 activation·실제 PID 소비는 각각 별도다. 보조판정은 별도 family가 수행한다.

즉 현재 설치 그대로라면10/6 장후에도 위 방식이 실행된다. 아래 개선 방식에는 P2의 자동화·schema·발행 경로 연결이 필요하다.

### 4.2 연결 완료 후의 목표 방식

| 단계 | 소비·계산·출력 |
| --- | --- |
| A. 원천 묶기 |10/6 기존 관측 원천의 ENTER_NOW/BLOCK/RECHECK를 같은 분모에 모으고 `005930`과 그 외 종목을 처음부터 분리한다. venue/session·policy parent·원 capture hash·as-of cutoff·품질을 유지한다. 보조 AI의 허용/거절은 기계 승패 label에 넣지 않는다. |
| B. 미래 가격 평가 | 최초10분의 목표/손절 선도달 결과를 보존한다. 미도달에 한해 이후 최대60분의 기존 가격 경로로 순서를 보완하고 별도 horizon 필드를 남긴다. 손절 후 뒤늦은 상승을 목표 선도달로 바꾸지 않는다. 분봉 내 선후 모호, 경로 공백, 장마감 검열, 비용/stop 결손은 미확정으로 남긴다. |
| C. 반복 관측 정리 | 고정 최초 신호/동일 사건 묶음과 군집 동일 가중 계약을 사용한다. 반복 캡처 수를 독립 기회 수로 세지 않는다. 연구 관측 cluster와 native 실행 opportunity의 identity·분모를 병기하며 가짜 promotion ID를 만들지 않는다. |
| D. 고정 정책 대조 | 비삼성은 동결한 `pullback_p60_v0`와 정확한 incumbent를 같은 입력에 적용한다. 삼성은 별도 기존 고정 후보/부모 비교 owner로 인계한다. 후보별 목표·손절·미도달·미확정, 선택 수·coverage·주승률/지원조정 승률·공통 집단과 변경 집단을 낸다. |
| E. 새 날짜 검증 |9/29·9/30·10/2는 이미 사용한 탐색 자료다.10/6은 미리 고정한 후보의 이후 날짜 검증으로 한 번 소비한다.10/6 결과로 조건을 바꾸면 같은 결과를 수정 후보의 독립 검증으로 쓰지 않는다.10/6에 후보가 운영됐다면 적용된 후보와 동결한 이전 부모를 비교한다. |
| F. 선정·승계 | 기존 정책보다 나은 승률을 우선 비교한다. 기존 성공100%/80% 보존은 diagnostic으로만 남긴다. 기존 운영 자격·source 계약과 새 observation 계약의 차이는 명시적으로 검증하고, 미달이면 어떤 조건 때문인지 수치로 남긴다. 결손 전체를 일괄 해소해야 한다는 새 gate를 만들지 않는다. |
| G. 발행·인계 | source_date10/6·effective_date10/7·scope·parent/source/kernel SHA·정책 행동 차이·선정/승계 이유를 봉인한다. stage terminal→summary/checklist→strict→controller→prepared로 인계하고10/7 실제 소비는 별도 확인한다. |

원천 feature는 항상 판단 당시 값만 사용한다. 이후 가격은 정답 label에만 사용한다. 목표 선도달 승률은 실제 매매 승률과 다르므로 청산/체결/실현 순수익은 분리한다. 분류별 지표를 보고하되10/6 결과를 본 뒤 유리한 분류만 골라 독립 검증 PASS를 만들지 않는다.

## 5. 실행 소유자와 유한 종료

- 오늘 준비 구현/선정 대사: [10/5 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md) `MachinePolicyCutoverPreparation1005`.
- 디스크: 같은 체크리스트 `VerifiedStorageCleanup1005`.
- 비삼성10/6 고정 후보 관측 비교: 같은 체크리스트 `NonSamsungMachineForwardComparison1006`. 기존 자료 연구를 다시 OPEN으로 만들지 않는다.
- Main 당일 적용: [10/6 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md) `DirectFamilyPreopenPolicyHandoff`.
- Widget/Episode:10/5 체크리스트 `WidgetEpisodeNextSessionStartup1006`.10/4의 동일 ID·수용/이력을 이관했다. 당시58/3 분할은 역사 기준이며 현재 profile별 hash/자격/기동 결과로 다시 분류한다.
- 운영 경제성 원천:10/6의 `DirectFamilySourceRepairMainMechanisticEntry`, 보조는 `DirectFamilySourceRepairCompactAuxiliary`, Episode sequence는 `EpisodeCaptureSequence1006`를 유지한다. 새 비교 보고서가 이 원천 결손을 자동 해결하지 않는다.
- 삼성 별도 고정 검증:10/5의 `SamsungFrozenCandidateValidation1006`, `SamsungPremarketForwardValidation1006`.10/4에 있던 동일 ID·수용/권한·준비 이력을 보존하여 이관했다.

print-only parser가 현재10/6·10/5 문서를 소비해10/4의 미래 OPEN3개를 누락하는 것을 확인했다. 위3개를 현재 문서로 옮기고10/4에는 이관 기록만 남겨, 각 항목에 현재 parsed owner가 하나씩 존재하도록 한다.10/6 체크리스트 bytes는 변경하지 않는다.

현재 계획 확정의 종료는 경로·결손·단계·수용/되돌림·owner 명시 및 문서 검증이다. 후속 실행은07:20에 적용/승계/준비실패를 확정하고, 각 시간 창 종료에 PASS/blocked/not_observed로 보고한다.10/6 장후는 고정 후보의 한 번의 비교와 발행/승계 사유를 내면 종료하며 가설 추가로 무기한 연장하지 않는다.

## 6. 이번 계획 작업의 검증

문서 리뷰에서10/4 미래 OPEN3개의 parser 누락을 수정하고 현재 owner로 이관했다. 원천/정책의 옛 PASS와 현재 실패, 연구 후보와 설치된 생성기, 삭제 후보 용량과 실제 회수 가능량을 분리해 재검토했다. 링크·현재 parsed owner·whitespace/diff·print-only parser 결과는 [문서 검증 기록](../../tmp/next-session-policy-storage-plan-20261005/validation.json)에 남긴다. 코드·wrapper 변경이 없어 거래 pytest/compile·광범위 장후 재생성은 수행하지 않는다. 이번 문서 검증 PASS가 §2의 운영 결손 복구를 뜻하지 않는다.

## 10/5 실행 인계

최신 사용자 지시로 위 계획을 실행한다. 공용 판정/장후 생성 연결, 원천 복구 및 검증된 정리는 [실행 리뷰](../audits/machine-policy-cutover-and-storage-execution-review-2026-10-05.md)와 그 closure에 기록한다. 계획 작성 시점의 미실행 문구는 역사 상태다.10/6 실제 activation/PID와 자연 수용은 해당 당일 owner에서 확인한다. 기존 압축 캐시3개의 물리 SHA 보존 제한과6,550개 원 capture/행동 차이0을 분리해 공개했다.
