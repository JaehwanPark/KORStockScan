# 10/8 장후 결과 점검·복구 검토

사용자가 실행 중 장후작업 중지, 실패 지점 보완·재개와 정상 종료 작업의 결과 점검·보완·재실행을 지시했다. 기존 `DirectFamilySourceRepairMainMechanisticEntry` owner에서 처리한다. 원천일·발행일은 2026-10-08, 운영 달력의 다음 거래일은 2026-10-12다. 매매 재기동이나 주문·provider/model·threshold·수량·hard safety 변경을 수행하지 않는다.

## 최초 상태와 원인

- EOD는 20:56:13 completed_with_warnings, 성공 2,626/2,629종목, DB 178,342행이며 최신 일자 10/8과 failed_steps 0을 확인했다. 제외한 OHLCV 부족 종목은 성공으로 바꾸지 않는다. archive는 20:56:31 종료했다.
- Main 장후 run `bd2c1f8aaee44794a5fa08f3a864bd47`, release `main-retired-postclose-cleanup-20261008-v1` / `0c1f68968906395f12c121862876704afadc1e83`는 21:34:21 실패했다. summary producer의 Main-only 9개 원천은 완결됐으나 checklist 소비자는 과거 label map의 `machine_entry`, `low_price_two_leg`, `low_price_expansion`까지 필수로 요구했다.
- 기계·보조·legacy Main report·outcome labels·pre-submit delay stage는 모두 exit 0였다. 그러나 보조 candidate는 입력 v2이고 운영 입력은 v3였다. 원천 127,916확인점 중 109,973건이 `typed_candidate_incompatible`, 준비 쌍/요청 0, comparison_complete/paired_metrics_ready false였다. 데이터나 호출 예산 부족으로 진단하지 않는다.
- 기계 원천의 resolved 82,121와 unresolved 45,795는 별도다. 기계 replay의 membership pending과 실제 등록 정책의 carry는 다른 산출물이다. 등록 128경로 준비는 실제 비교 완료나 PID 소비가 아니다.
- cancel-wait의 historical_submission_or_source_unreconciled, entry-split의 operating_paired_source_missing은 경제성 원천 결손으로 남긴다. pre-submit delay의 순수 quote-pattern 결과와 executable fill/cost model을 구분한다. scale-in·WS·rising-missed의 not_applicable/valid-empty는 복원 대상으로 바꾸지 않는다. source audit은 hard contract gap/excluded row 0이며 원 관측 경고를 보존한다.
- 21:56에 대기 중인 controller/tuning 두 process group의 정확한 wrapper·PID·하위 프로세스를 대사한 후 TERM으로 종료했다. [중지 영수증](../../data/report/postclose_recovery/2026-10-08/operator-stop-2156.json)에 종료 후 잔여 PID 0을 기록했다.

## 구현과 리뷰

1. checklist 필수 census는 summary producer의 PRIMARY_DIRECT_OWNERS를 소비한다. 과거 label map은 sealed 역사 자료의 reader로 남긴다. 생존 원천 하나라도 누락하면 여전히 실패한다.
2. 튜너에 명시적 `rebind-input` source-only 복구를 추가했다. 원 config SHA의 CAS와 configure 공통 lock, 이전/새 공통 PROMPT·arm suffix 동일성, 변경 없는 후보 문구를 요구한다. v3 registry는 새 불변 정의이며 원 v2 정의·scope·seed·max_pairs·개발 제외·누적 예산을 보존한다. 다른 프롬프트 계약·동일 입력 버전·compact registry의 임의 변환은 거부한다. 이 CLI는 운영 prompt를 직접 선택하지 않는다.
3. summary는 비교 미완료와 검증된 정책 승계를 분리한다. 실제 개선으로 선택한 scope만 comparison_selected이고 원 정책 carry·초기 지정·source gap은 신규 승률 선정으로 표시하지 않는다.
4. 보조 stage의 코드 fingerprint에 registry/tuner/intraday/wire reader를, summary stage에는 실제 summary producer를 추가했다. 변경된 실행 코드를 이전 성공 영수증으로 덮지 않는다.
5. 원천 census·권한·예산 유지·CAS·다른 프롬프트 계약 거부·stage code 변경·비교/carry 투영을 회귀 검증한다. 기존 strict 회귀의 삭제된 저가/연구-capacity fixture는 생존 entry-split/outcome-label owner로 이관하며 검증 강도를 유지한다.

## 복구 실행 계약과 수용

현재 배포 커밋 기준의 격리 작업본만 사용하고 다른 세션의 dirty source/document를 포함하지 않는다. gate 통과 후 shared state/docs를 연결한 불변 release를 선택한다. frozen 원천·원 status/stage 영수증·기존 정책 부모를 보존하고 candidate 입력 결속을 수정한 뒤 Main 장후 wrapper와 controller/tuning을 한 회차 재개한다. 완료 EOD는 다시 수집하지 않는다. 기존 incremental cache와 검증된 보고서 재사용은 허용하되 결함 stage는 실제 재계산한다. 신규 보조 호출은 원천일 누적 100회이며 failed/uncertain도 차감한다.

종료는 최신 stage별 결과→summary/tower→10/12 checklist→strict/controller, tuning terminal과 exact-date 준비의 현재 해시를 대사해 판정한다. 운영 종결, 분석 유효성, 등록/carry/선정, 다음 PREOPEN·실제 PID·비용 후 자연 성과는 별도로 보고한다. 10/12 예정 finalization·PREOPEN·기동은 미도래 상태로 남긴다. 이전 10/7 strict의 stale checklist 기록은 10/8 복구 성공으로 숨기지 않는다.

검증 및 최종 실행 결과는 아래에 보완한다. 증거 디렉터리: [postclose_recovery/2026-10-08](../../data/report/postclose_recovery/2026-10-08).

## 코드 gate 완료

확장 회귀 318 PASS 뒤 최종 영향 경로 재검증 169 PASS를 확인했다. compile, wrapper bash syntax, diff, 실제 링크와 print-only backlog parser가 통과했다. 범위 내 미해결 구현 finding은 0이며 정상 종료 결과의 원천 결손과 미래 자연 수용은 별도다. old v2/v3 공통 PROMPT와 전체 arm suffix equality를 실제 코드로 확인했다. 새 연구 가설이나 주문/provider/threshold 변경 없이 typed candidate 결속만 복구한다.

## 실제 재개에서 발견한 controller 순서 결함

22:12 V1 재개는 이전 stage 영수증 존재 시 controller가 Main terminal을 기다리기 전에 summary stage로 분기하는 결함을 확인했다. 변경된 보조 코드 영수증이 갱신되기 전에 independent producer 검증이 종료됐다. 22:14:38에 해당 Main/tuning 회차를 TERM으로 중지했으며 신규 보조 호출은 시작하지 않았다. 첫 실패·중지 영수증은 보존한다.

V2는 Main 완료 대기를 stage 분기보다 먼저 수행한다. timeout이면 stale summary를 실행하지 않고 blocked_predecessor 영수증을 남기며 summary-only worker는 대기·재분기하지 않는다. 기존 영수증을 둔 CLI 순서, timeout, worker 재진입을 포함한 controller/summary/strict 회귀 99 PASS, compile·bash syntax·diff 검사를 확인했다. 이는 재개 순서 보완이며 Main 거래 프로세스 재기동이 아니다.

## 실제 비교 경로의 예산 DB 계약 보완

V2 기계 stage는 22:23:39, pre-submit delay는 22:24:41, labels는 22:25:05 재실행 완료했다. 보조 비교가 실제 요청 예약 경로에 도달한 뒤 `attempt_budgets.attempt` 단일 PK로 실행일/원천일 두 예산을 동시에 기록할 수 없어 `UNIQUE constraint failed`로 종료했다. 22:27:53 Main/controller/tuning과 분리된 legacy stage를 TERM으로 종료하고 그 영수증·checkpoint를 보존했다.

V3는 `(attempt,budget_key)` 복합 PK와 writer lock 내 원자적 이전을 사용한다. 이전 budget 행을 그대로 복사하고 예기치 않은 schema/invalid row는 rollback한다. 재개 seed는 이미 차감한 호출을 다른 실행일로 임의 재배정하지 않는다. 실패/uncertain도 두 날짜의 cap에 남으며 한 날짜라도 소진되면 provider 예약 전에 거부한다. 원 budget table 15,881행(10/7 postclose 15,228, 기존 별도 승인 연구 653)은 [원 예산 사본](../../data/report/postclose_recovery/2026-10-08/budget-table-before-migration.json)으로 보존한다. 과거 over-budget는 복구 시 0-new-call 제약으로 유지한다. 초기 budget/store/tuner/stage 회귀 98 PASS를 확인했고 실제 튜너의 다른 원천일 비교·캐시 재개를 추가 검증한다.

별도 삼성 frozen 연구 sidecar는 9/29 압축 원천의 기존 frozen hash 불일치로 실패를 정확히 기록한다. 원 frozen candidate나 기대 hash를 현재 파일에 맞춰 바꾸지 않는다. report-only·policy_publication=false이며 startup gate가 아니다. owner는 SamsungFrozenCandidateValidation1006, 원 결과는 `data/report/samsung_tick_transition_forward_validation/2026-10-08/latest.json`; 정확한 원 frozen source 복원이 closure 조건이다.

V3 최종 store/tuner/stage/wrapper 회귀 127 PASS. 실제 튜너에서 다른 원천일의 current/candidate 비교가 끝나고 재호출 0을 확인했다. wrapper의 초기수량 소비자 검사는 live ROOT/data 존재에 의존하던 fixture를 tmp/명시적 policy-due fixture로 격리했으며 selected policy 부재 때 소비 경로가 제외되는 검증도 유지한다. compile·bash syntax·diff·print-only parser가 통과했다. V2 신규 캠페인은 50쌍/100요청으로 생성되어 typed_candidate_incompatible 제외가 사라졌고, 실제 provider 결과는 V3 재개에서 확인한다.

## 요약 소비자의 기계/보조·부분 선정 보완

보조 comparison이 처음 실제 비교를 시작하면서 최종 소비자를 다시 리뷰했다. 기존 direct_handoff의 policy_states는 마지막에 읽은 보조 component 상태다. 기계와 보조 요약 모두 이 공통 상태를 사용하면 보조 신규 선정을 기계 선정으로 표시하거나, 일부 scope의 유효한 선정까지 전체 request 미완료 때문에 후보 0으로 덮을 수 있다.

V4 요약은 각 owner의 정확한 불변 component를 policy에 결속된 report hash로 다시 검증한다. 기계 carry와 보조 선정은 개별 component에서 투영한다. 보조 promoted scope는 improved=true·paired_points>0인 원 metrics를 요구하고 scope별 후보 수를 표시한다. 남은 전체 비교 미완료는 comparison_complete=false로 유지하며 PID·주문·경제성 권한을 만들지 않는다. component 재작성과 형식 결함은 source_gap으로 닫는다. summary/controller/stage/strict 회귀 141 PASS를 확인했다. V3 계산 worker는 유지하고 terminal 후 summary/controller·준비만 갱신한다.

Labels 19건은 mature 11·partial 8이며 원 canonical bars/context/input bundle·exact preflight v2/payload store와 natural control semantics 결속이 부족하여 diagnostic 학습 대상에서 제외된다. owner `ai_decision_quality_original_price_and_context_source`, closure `exact_route_original_window_and_primary_identity_valid`를 보존한다. 가격 창 성숙만으로 원 입력 손상을 해소하거나 비용 후 EV를 생성하지 않는다.

V3의 모든 계산 stage는 정상 종료했고 비교 가능 쌍 17개·보조 실제 새 호출 35회(원천일 누적 36회), 신규 선정 0을 확인했다. 마지막 checklist는 새 incomplete 비교 표시가 policy_handoff_state=verified로 남아 non-edge apply 계약에서 거부됐다. 요약 producer가 검증된 기존 정책 승계를 incumbent_preserved로 전달하며 receipt.valid=true·policy_apply_allowed=false를 유지하도록 보완했다. 실제 producer→checklist 연결을 포함한 최종 영향 회귀 194 PASS. 계산 결과와 원 예산은 유지하고 Main terminal·summary/controller·준비를 정상 흐름으로 재생성한다.

최종 native 요약 리뷰에서 native current를 옛 strategy_activation reader에 전달해 active_generation_invalid로 표시하던 진단 오분류도 보완했다. native family의 옛 strategy receipt는 not_applicable이며 실제 native/PID 검증은 계속 별도 계약을 요구한다. legacy 정책의 실제 오류는 숨기지 않는다. PREOPEN을 포함한 최종 회귀 205 PASS, compile·diff·print-only parser를 통과했다. Main 계산 terminal 이후 검증된 cache로 새 release의 native stage·summary/controller·준비 증빙을 갱신하며 추가 보조 호출을 하지 않는다. Stage 코드 fingerprint가 release의 절대 경로를 포함하므로 변경 없는 계산도 새 root의 실행 영수증으로 대사한다.

## 최종 실행·현재 세대 대사

23:10 KST 기준 선택 release는 `postclose-main-census-recovery-20261008-v5`, commit `4e13ecf5a16e993571b4081afd53f7ec93c8aab5`다. 선택 root의 runtime source clean·HEAD·shared path·퇴역 구성 차단과 설치 cron 8개 routing을 검증했다. 다른 작업본의 source/doc 변경은 이 release에 포함하지 않았다.

Main run `38f988b691f84ee38e4a49e9d3470c72`는 V4 `169603cc5d8bc9f68a530bedadbd11da6c28cbcf`에서 22:58:39 `succeeded / verified_main_completed`로 종료했다. Tuning은 같은 V4에서 23:00:41 `success`, 실패 step 0으로 종료했다. 마지막 V5 수정은 summary 진단 분류이므로 완료된 Main/tuning/EOD를 다시 열지 않고, 기존 recovery dispatcher로 새 root의 계산 stage 5개와 summary/controller를 갱신했다. 이 historical Main receipt와 V5 stage·controller·PREOPEN 영수증을 구분하며 Main의 실행 commit을 V5로 바꾸지 않았다.

| 작업 | V5 실제 종료 | 결과 확인 |
| --- | --- | --- |
| main_machine_policy | 23:05:56, succeeded | 등록/carry와 실제 승률 비교·PID 소비를 분리 |
| outcome_labels | 23:06:06, succeeded | 원 입력 결손 19건을 eligible 0으로 유지 |
| legacy_machine_report | 23:06:12, succeeded | Main 호환 report-only; 신규 운영 권한 없음 |
| main_auxiliary_policy | 23:06:44, succeeded | 비교 가능 17쌍, 개선·신규 선정 0, comparison_complete=false, incumbent carry |
| pre_submit_delay | 23:06:45, succeeded | quote 분석 완료/부분 coverage; 29기회·21 delay 비교, 추천 null·report-only |
| summary_handoff | 23:07, succeeded | 직접 필수 원천 9/9, runtime summary blocking 0, 신규 policy candidate 0 |

Controller는 23:07:14 `done`, whole_native_chain_done_claimed=true, strict `pass`, blocked_reasons=[]다. 23:10:02에 immutable strict attempt를 현재 전체 계약으로 다시 검증해 finding 0을 확인했다. [현재 strict 대사](../../data/report/postclose_recovery/2026-10-08/final-strict-current-verification.json)는 과거 PASS의 metadata-only 재사용이 아니다.

10/12 준비는 V5 선택 commit과 새 controller·정책·checklist hash로 23:07:17 `prepared_verified`가 발행됐다. [현재 PREOPEN 전체 계약 대사](../../data/report/postclose_recovery/2026-10-08/final-preopen-verification.json)는 pass/findings=[]/actual_pid_consumed=false다. 10/12 05:00 finalization, 07:35 PREOPEN, 07:55 Main 기동은 예정이며 자연 실행/PID 소비/비용 후 성과는 아직 증명하지 않는다. 현재 장후 worker 잔여 PID는 0이며 trading bot·web 재기동이나 주문을 수행하지 않았다.

보조 실제 신규 호출은 V3 비교 35회였고 원천일 누적은 36/100이다. V5 직전/직후 예산 행수는 동일하여 마지막 재실행 신규 호출 0을 확인했다. [호출 예산 대사](../../data/report/postclose_recovery/2026-10-08/v5-budget-after.json). 과거 예산 15,881행과 10/7 over-budget 기록은 유지했다.

## 마지막 의미 감시와 남은 원천 제약

23:07:45 selected V5의 native error-detector full/source-date recovery를 실행했다. 7/7 detector 초기화, failure 0, operational mutation 0이다. 기계·보조·cancel-wait·handoff·functional semantic coverage의 findings=[]/semantic_alerts=[]이며 cron은 정상 또는 미도래다. 전체 severity는 warning으로 유지한다. EOD 제외 3종목, 비필수 code_improvement_workorder 미생성, 이전 로그의 감사 경고를 PASS로 덮지 않는다. 원 보고서는 [현재 감시 결과](../../data/report/error_detection/error_detection_2026-10-08.json)이며 이번 실행은 read-only checks로 token/lock/restart 변경이나 외부 알림을 수행하지 않았다.

| 남은 제약 | owner/원 artifact | 다음 조치·closure test |
| --- | --- | --- |
| cancel-wait 과거 9/29·9/30·10/1 대사 결손 | EntryCancelWaitSourceReconciliation1002 / entry_cancel_wait_tuning_2026-10-08.json | 원 source ledger·policy·consumer projection의 동일 세대 대사. 당일 제출 0만 verified이며 이전 미해결 custody는 null; 기존 정책 유지 |
| entry-split operating paired source missing | entry_split_order_plan / 같은 날짜 report·정책 companion | frozen 제출 cohort와 실제 비용 모델·독립 paired calibration/holdout 결속 전 신규 승격 금지 |
| labels 원 canonical bars/context/input bundle 결손 | ai_decision_quality_original_price_and_context_source / ai_decision_quality 10/8 | exact_route_original_window_and_primary_identity_valid. 성숙 11·부분 8의 관측을 원 입력으로 합성하지 않음 |
| pre-submit quote coverage 부족 | pre_submit_delay / 같은 날짜 price_pattern_analysis | 기존 동일 intent의 0초 quote와 지연 quote provenance 대사. 실제 체결·청산은 순수 가격 패턴 분석의 필수조건이 아님; 0초 quote 결손 23건을 제외하고 fill/PnL 주장 없이 유지 |
| 삼성 frozen 연구 9/29 원 projection hash 불일치 | SamsungFrozenCandidateValidation1006 / samsung_tick_transition_forward_validation/2026-10-08/latest.json | 정확한 기존 frozen source 복원. 기대 hash를 현재 파일로 재결속하지 않으며 report-only·startup gate 아님 |

검토·수정 범위의 구현 finding은 닫았으나 위 원천 제약은 미해결 상태로 명시한다. 새 후보 0은 비교/원천 조건에 따른 결과이며 원천 부재를 zero EV/no edge로 해석하지 않는다. 이전 10/7 strict의 stale checklist와 초과 예산 기록도 별도 감사 부채로 보존한다.
