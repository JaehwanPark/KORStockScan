# 장후 튜닝결과 점검 작업지시문

작성 기준: `2026-09-01 KST`

현재 대상 거래일의 키움증권 연동 SCALPING 장후 자동화 산출물을 대상으로 자동화체인 완결성, source quality, 비용 차감 EV, owner별 실현 결과, sim/source-only 후보, 다음 PREOPEN handoff와 code-improvement workorder를 점검한다. 메인 봇, 위젯 매매기계, 에피소드 매매기계는 서로 독립된 주문 owner로 유지하며 주문번호·보유수량·청산·손익 귀속을 혼합하지 않는다.

튜닝 원칙과 active/open 상태는 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8, 당일 실행 항목은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 `docs/time-based-operations-runbook.md`, producer/consumer 의존 순서와 R0→R6 추적성은 `docs/report-based-automation-traceability.md`를 기준으로 한다. 실제 실행 단계는 대상 run이 시작할 때 검증한 immutable wrapper snapshot과 설치된 cron/systemd `ExecStart`를 함께 대조한다. runbook·traceability·설치 trigger·wrapper snapshot의 단계, 조건, 실패 우선순위가 다르면 최신 mtime이나 실제 실행 사실만으로 한쪽을 권한 계약으로 선택하지 않고 `contract_drift`로 fail-closed한 뒤 owner 문서와 구현을 review gate로 정합화한다. 이 문서는 반복 점검 절차이며 특정 날짜의 family 목록, report 존재 또는 과거 추천을 현재 runtime 적용 권한으로 만들지 않는다.

이 지시문으로 장후 점검을 실행하라는 사용자 요청은 §2의 허용 범위에 속하는 `implement_now` 중 `runtime_effect=false`인 항목을 §9의 2-pass로 구현·리뷰·재판정하라는 지시를 포함한다. 별도의 “구현해줘” 재지시나 controller/runner opt-in을 기다리지 않는다. 다만 대상 workorder가 `not_yet_due|in_progress`이거나 필수 계약 증거가 없으면 구현을 추정하지 않고 해당 gate를 미완료로 남긴다. `runtime_effect=true`나 §2 금지 권한은 이 자동 구현 지시에 포함되지 않는다.

## 1. 목표와 완료 정의

목표는 장후 job이 단순 종료됐는지 확인하는 데 그치지 않고 다음 질문에 답하는 것이다.

1. 당일 실제 기회·주문·체결·보유·청산 결과가 정확한 owner와 executable 시장 정보에 결속됐는가?
2. 비용 차감 후 EV와 누적 순이익을 높이거나 훼손한 최초 단계와 직접 원인은 무엇인가?
3. 당일 ON runtime 또는 exact-date policy가 eligible 표본에서 실제 호출되고 의도한 효과를 냈는가?
4. source-quality·AI·smoothing·parser·schema·report 결손이 전략 성과로 잘못 해석되지 않았는가?
5. daily 결과가 각 owner/artifact의 `window_policy`가 선언한 rolling·MTD·clean-baseline cumulative 결과와 일치하며, 미선언 window를 억지로 요구하지 않았는가?
6. 발견된 후보가 sim policy, runtime bridge, next PREOPEN 후보 중 어디까지 실제로 전달됐고 무엇이 남았는가?
7. 구조적 결함은 최소 보완과 review gate로 닫혔으며 관련 산출물이 올바른 순서와 generation으로 재생성됐는가?
8. AI 판단품질, micro-reversion 등 다단계 계산은 원천 row부터 최종 집계까지 독립 재현되며 leakage·중복·단위·시간·비용 오류가 없는가?
9. 당일 적용된 입력은 메인·위젯·에피소드 process에 실제 소비됐으며, 당일 장후 생성된 다음-session 산출물은 그 authority에 맞는 마지막 consumer와 handoff까지만 정확히 전달됐는가?
10. 실행 예정 process가 살아 있고 의미 있는 output과 consumer를 가지며 dead·hung·duplicate·no-op·orphan 경로가 남지 않았는가?
11. 보고서의 각 표본·모집단 부족은 `시간이 해결하는 부족`과 `구조적으로 모집단이 고갈되는 부족` 중 무엇이며, 최초 고갈 단계·예상 해소 시점 또는 구조 보완·재판정 조건이 근거와 함께 닫혔는가?
12. 대상 generation의 `implement_now` 전수가 stable `order_id`로 intake됐고, 허용 범위의 `runtime_effect=false` 항목이 Pass 1 구현과 재생성 후 Pass 2 fixed-point 재판정까지 누락 없이 닫혔는가?

장후 완료는 다음 두 층을 분리한다.

- 운영 완료: main postclose wrapper와 verifier가 terminal이고, controller artifact뿐 아니라 controller wrapper의 대상일 latest `[DONE]`, 필수 follower, 20:50/21:00 보관 작업과 21:55 detector final window가 계약에 맞게 닫혔다.
- 튜닝 판정 완료: source quality, EV, handoff, workorder lineage와 미해결 blocker가 근거와 함께 판정됐다.

`postclose_done_controller status=done` JSON만으로 운영 완료를 선언하지 않는다. controller JSON 뒤에 실행되는 paired-replay follower와 opt-in runner가 있으므로 controller cron log의 대상일 latest `[DONE]`까지 확인해야 한다. 이 운영 완료도 수익성 우수, live 승격 가능 또는 실주문 권한 획득을 뜻하지 않는다.

## 2. 권한 경계

이 지시문은 읽기 전용 점검과 source-quality·parser/schema·report·test·instrumentation·sim/source-only 범위의 보완을 허용한다. 대상 workorder의 `decision=implement_now`, `runtime_effect=false`, `allowed_runtime_apply=false`가 확인되고 보완이 이 허용 범위에 속하면 §9 2-pass는 선택 항목이 아니라 필수 실행 항목이다. 구현된 것으로 보이는 항목도 source→producer→consumer→acceptance-test 근거로 `already_implemented_verified`를 입증하지 못하면 미완료로 유지한다. 다음 변경은 별도 사용자 지시와 유효한 approval/apply artifact 없이는 수행하지 않는다.

- PREOPEN live env 선택 또는 수동 작성
- provider route, model, failback 순서, timeout 정책 변경
- bot·위젯·에피소드 process 기동·종료·재기동
- 실주문, 미체결 취소, 보유수량 조정 또는 owner 간 custody 이동
- cap·수량·가격·cooldown·broker/account/order guard 변경
- score·entry·holding·scale-in·exit threshold의 수동 변경
- stale/conflict·price freshness·hard/protect/emergency safety 완화
- source-only·sim·counterfactual 결과의 실주문 권한 전환

자동 복구 controller의 기존 bounded recovery는 그 계약 안에서만 인정한다. 수동 full-wrapper 재실행, 비싼 report 재생성, bot 재기동은 원인과 적용 권한을 확인하기 전 실행하지 않는다.

## 3. 점검 시작 전 기준 고정

매 실행 시작 시 다음을 새로 읽고 대상 거래일을 명시한다.

1. Plan Rebase §1~§8과 당일 checklist의 `오늘 목적`, `오늘 강제 규칙`, POSTCLOSE 실행 항목
2. `clean_tuning_baseline_date=2026-06-05`, `clean_tuning_baseline_ts_kst=2026-06-05T00:00:00+09:00` 및 `data/source_quality/clean_baseline_policy.json`
3. 대상일 postclose status, cron log, final verifier, controller, source-quality audit
4. 대상일 PREOPEN apply plan/runtime env와 실제 당일 PID/process가 사용한 commit·policy·runtime provenance
5. main/widget/episode/manual owner별 broker receipt, 미체결, custody와 terminal ledger
6. artifact 계약이 선언한 경우 generation ID/source hash/input artifact hash, 선언하지 않은 경우 direct source path/fingerprint·generated/completion time·downstream link
7. 현재 worktree·branch·commit·source-dirty 상태와 이미 존재하는 사용자 변경
8. 대상 workorder JSON의 `implement_now` 전수, stable `order_id`, `runtime_effect`, `allowed_runtime_apply`, 현재 implementation evidence와 2-pass 진행 상태

### 3.1 High/XHigh 실행 원칙

이 지시문은 `high` 또는 `xhigh(extra high)` reasoning effort로 실행하는 것을 전제로 한다. 실행 시작 기록에 실제 effort를 남기고 다음 phase gate를 순서대로 닫는다.

1. Contract gate: source-of-truth, target date, active/OFF/retired owner와 권한 경계 고정
2. Chain gate: process·wrapper·artifact·producer/consumer 전체 inventory와 terminal 상태 확인
3. Calculation gate: 결정론적 층화 표본 독립 재계산, 전체 집계 reconciliation, AI/micro negative·boundary case 검증
4. Consumption gate: 당일 적용 입력의 main/widget/episode 실제 소비와 당일 장후 생성 입력의 다음-PREOPEN handoff를 서로 다른 시간축으로 확인
5. Implement-now intake gate: authoritative workorder의 `implement_now` 전수와 권한·구현 상태를 stable `order_id`로 고정하고 Pass 1 대상 누락 0을 확인
6. Repair/Pass 1 gate: 허용 범위의 `runtime_effect=false` 항목 전수에 대한 구현 또는 `already_implemented_verified`, 독립 코드리뷰, finding 수정과 targeted validation 반복
7. Regeneration/Pass 2 gate: upstream부터 ordered regeneration, old/new workorder diff, 신규·판정변경 `implement_now` 추가 구현, fixed-point 확인, verifier/controller 최종 판정

high/xhigh의 추가 추론은 조사 깊이를 높이는 데 사용하고 scope나 실행 권한을 넓히지 않는다. `high`는 위 7개 gate, 독립 producer/consumer review와 finding-0 재검증을 모두 수행한다. `xhigh`는 여기에 반대 가설·오탐/누락·경계 표본·authority leak를 겨냥한 adversarial second pass와 수정 후 전체 영향면 재리뷰를 추가한다. 현재 target date와 직접 연결된 producer/consumer부터 닫고, 무관한 repository 전역 개선은 별도 backlog로 분리한다.

긴 실행에서는 최소 `target date / commit·dirty / artifact path·hash·time / process PID·start·status / finding severity / shortage_id·shortage_class·evidence window·ETA 또는 구조 보완 / workorder generation·source hash / implement_now order_id·2-pass status / 수정 파일 / validation / regeneration step`을 evidence ledger로 유지한다. context가 축약되거나 작업이 다음 turn으로 이어져도 이 ledger와 마지막 완료 gate에서 재개하고 이미 닫힌 단계를 무근거로 반복하지 않는다.

서로 독립된 read-only 계산, process inventory와 producer/consumer review는 병렬 검토할 수 있다. 최종 판정은 단일 owner가 source hash와 finding을 합쳐 내며, sub-review의 추정만으로 결함을 확정하거나 runtime을 변경하지 않는다.

finding은 `P0 safety/owner breach`, `P1 incorrect result or machine input`, `P2 source/process/contract defect`, `P3 documentation/maintainability`로 분류한다. P0~P2가 남아 있으면 finding 0이 아니며, 수정 후 동일 범위 재리뷰와 targeted validation을 반복한다. 외부 source 부재나 사용자 권한처럼 코드로 닫을 수 없는 항목은 숨기지 않고 blocked owner와 acceptance condition을 기록한다.

표준 읽기 전용 시작 명령은 다음과 같다.

```bash
cd /home/ubuntu/KORStockScan
TARGET_DATE="YYYY-MM-DD"  # 점검할 KRX 거래일을 명시한다.
git status --short
tail -n 240 logs/update_kospi.log
tail -n 320 logs/threshold_cycle_postclose_cron.log
tail -n 240 logs/postclose_done_controller_cron.log
tail -n 240 logs/tuning_monitoring_postclose_cron.log
tail -n 200 logs/ai_entry_setup_paired_replay_postclose.log
tail -n 200 logs/run_error_detection.log
ps -eo pid,ppid,lstart,stat,etime,%cpu,%mem,cmd --sort=pid | rg 'KORStockScan|run_|src\.engine|widget|machine|bot'
systemctl list-timers --all --no-pager | rg 'korstockscan|threshold|widget|machine|postclose'
systemctl list-units --type=service --all --no-pager | rg 'korstockscan|threshold|widget|machine|postclose'
tmux ls
ls -l \
  "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${TARGET_DATE}.status.json" \
  "data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json" \
  "data/report/postclose_done_controller/postclose_done_controller_${TARGET_DATE}.json"
```

자정 이후 tail repair를 점검할 때 wall-clock 날짜로 `TARGET_DATE`를 다시 계산하지 않는다. main wrapper, controller와 후행 producer가 처음 결속한 동일 거래일을 계속 사용한다.

파일이 없으면 즉시 실패로 단정하지 않는다. 예정 시각, wrapper/process 실행 여부, bounded predecessor wait와 target date를 먼저 확인해 `not_yet_due`, `in_progress`, `warning`, `fail`, `done`으로 분류한다.

## 4. 자동화체인 실행·복구 점검

### 4.1 EOD 선행 체인

`20:05` EOD 갱신은 threshold-cycle과 분리해 확인한다.

- `logs/update_kospi.log`의 대상일 `[START]`, `[DONE]` 또는 `[FAIL]`
- `update_kospi_YYYY-MM-DD.json`의 `status`, `failed_steps`, `warning_steps`, `recovered_steps`
- `db_state.latest_quote_date`, `db_state.rows_on_latest_date`
- `data/daily_recommendations_v2.csv`와 diagnostics의 content date·row contract
- `completed_with_warnings`와 DB 적재 실패를 분리하고, operator OFF인 swing step을 누락으로 세지 않았는지

EOD 실행이 정상 허용시간 안에서 진행 중이면 기다린다. 최신 DB quote와 exact trade performance fact가 동기화되기 전에 EV만 재생성하지 않는다.

### 4.2 Main postclose wrapper

대상일 latest run 하나를 기준으로 다음을 확인한다.

- `[START]`와 `[DONE]` 또는 `[FAIL]` marker가 같은 target date인지
- status JSON의 `status=succeeded`, `ai_correction_status=parsed`, 유효 provider provenance와 log의 최신 `[DONE]`·종료시각·실행 profile이 일치하는지
- wrapper code snapshot은 시작 시 검증한 복사본·`bash -n`·실행 inode·unlink lifecycle이 한 run에 결속됐는지
- data snapshot/checkpoint reuse는 별도로 source path/hash/count·checkpoint identity와 target date가 일치하는지
- 명시적 OFF stage가 `disabled` 또는 `skipped_disabled`로 분류됐는지, 완전히 은퇴한 opening rotation·upper-limit rotation·panic-buying·WAIT6579 독립 bridge는 active producer/verifier/runtime inventory에서 빠지고 historical artifact만 archive로 남았는지
- 필수 producer가 오류 후 조용히 건너뛰지 않았는지
- `AI correction`, pattern-lab review 등 AI 필수 단계가 parsed terminal 상태인지
- calibration → EV → workorder fingerprint → runtime summary → verifier 순서가 보존됐는지

세부 producer 순서는 `docs/report-based-automation-traceability.md`의 `Postclose Chain Contract`가 소유한다. 임의로 단계를 생략하거나 뒤집지 않고, 특히 `threshold_cycle_ev` pre-pass → workorder → EV refresh/propagation → runtime summary → gap/key-lineage/conversion → conversion 반영 workorder refresh → final EV → final workorder fingerprint → runtime summary → checklist → verifier의 후단 순서를 보존한다.

`START-only` 또는 predecessor `running|started|in_progress`는 12시간 bounded wait 안에서는 복구 attempt를 소비하는 실패가 아니다. 같은 날짜 wrapper가 이미 실행 중이면 중복 실행하지 않는다.

장시간 wrapper는 시작 시 검증한 immutable snapshot을 실행한다. 실행 중 repository 파일이 바뀌었다는 이유로 현재 run에 새 코드가 반영됐다고 보지 않으며, 새 revision 검증이 필요하면 현재 run의 terminal 상태와 review gate를 먼저 닫는다.

### 4.3 Verifier와 DONE controller

다음 artifact를 같은 target date, 직접 downstream link/fingerprint와 생성 순서로 대조한다. 여러 artifact에 공통 `generation_id`가 있다고 가정하지 않으며, `generation_id/source_hash/lineage`는 workorder snapshot 안에서 비교한다.

- `threshold_cycle_postclose_verification_YYYY-MM-DD.{json,md}`
- `postclose_done_controller_YYYY-MM-DD.{json,md}`
- `runtime_apply_gap_audit_YYYY-MM-DD.{json,md}`
- `tuning_performance_control_tower_YYYY-MM-DD.{json,md}`
- `code_improvement_workorder_YYYY-MM-DD.json`과 docs workorder

최소 확인 필드는 다음과 같다.

- verifier `status`, predecessor status/wait/timeout, `log_issues`
- `missing_required_artifacts`, `missing_downstream_links`, `stale_downstream_links`
- source-quality hard blocker와 warning follow-up 상태
- AI review provider/parse/schema 상태
- entry/submit/holding/scale-in/exit/lifecycle bucket handoff 상태
- workorder `implement_now_total`, stable `order_id` census, 2-pass ledger/fixed-point, `final_eligible_actionable_open_count`, `implement_now_unaccounted_count`
- controller `status`, `final_verifier_status`, `root_cause`, `selected_recovery_action`, attempts
- full-wrapper rerun 여부와 rerun 사유가 허용된 recoverable 범위인지
- `logs/postclose_done_controller_cron.log`의 대상일 latest `[DONE]`과, default-enabled paired replay는 21:05 이후 batch `status=completed_offline_only` 및 follower state `terminal_ready:validated_batch_and_candidate|terminal_ready:no_krx_candidate` 중 하나가 exact hash 검증으로 닫혔는지. 명시적으로 reviewed disabled인 경로는 `[SKIP] ... reason=disabled`와 설정 provenance를 남기고 AI replay 성공으로 세지 않는다.

`warning`은 항목별로 판정한다. source-only observer의 자연 표본 부재처럼 명시적으로 허용된 warning은 controller `DONE`과 공존할 수 있지만, 해당 candidate의 evidence readiness나 live 승격에는 계속 blocker다. 필수 artifact·lineage·AI receipt·runtime authority 결손을 단순 warning으로 낮추지 않는다.

### 4.4 후행 작업

main controller와 병렬 또는 후행으로 실행되는 owner를 각각 분리해 확인한다.

- `run_tuning_monitoring_postclose.sh`: predecessor DONE/pass, Parquet/DuckDB late-pass, `canonical_runner=THRESHOLD_CYCLE_POSTCLOSE`, per-step exit code
- `run_widget_evaluation.sh` 20:10 systemd owner: 시작 시 한 번 결정한 completed KRX target date를 네 producer가 공유하는지, 각 producer return code, exact next-session policy와 unit terminal status
- `run_machine_microstructure_final_refresh.sh` 21:15 owner: 현재 reviewed wrapper 계약의 한 번 결정한 completed target date, expansion → attribution → market-weakness-hysteresis → entry-timing → approval/notification → checklist builder 단계별 return code와 `builder > policy > weakness-hysteresis > entry-timing > attribution > expansion` 실패 우선순위. weakness-hysteresis와 entry-timing은 `attribution_rc==0`일 때만 실행되며, attribution 실패 때의 각 `rc=0`은 성공이 아니라 `skipped_due_to_attribution_failure`로 판정한다. weakness-hysteresis는 차단·실행 진입의 1·3·5·10·20·30분 executable-BBO 반사실, 최신 3거래일 holdout과 충분한 누적 표본을 통과한 단일 activation/release 축만 다음 exact KRX session 정책으로 발행하고 당일 hot mutation은 금지한다. 시작 시점 wrapper snapshot·설치 unit·runbook·traceability 중 단계 또는 실패 우선순위가 어긋나면 이 고정 예시로 정상화하지 않고 `contract_drift`로 차단한다.
- AI paired replay: 대상 stage/venue/session별 terminal batch, exact source/batch hash, checkpoint, provider receipt, `completed_offline_only`
- 20:50 dashboard DB archive: wrapper `[DONE]/[FAIL]`, `DASHBOARD_ARCHIVE_*`, verified/backfilled source와 `skipped_unverified`
- 21:00 log rotation/cleanup: wrapper terminal marker, declared writer별 pre-open rollover receipt, archive generation/source hash·gzip roundtrip, open-inode 0·owner lock, writer-active defer, escalation/state failure와 원본 보존
- 21:55 error detector final window: 대상일 canonical report, 고유 `run_id`, 7개 detector accounting, `summary_severity`, wrapper `[DONE]/[FAIL]`

후행 source-only replay의 성공을 live 적용으로 해석하지 않는다. `runtime_effect=false`, `allowed_runtime_apply=false`, `actual_order_submitted=false`, `broker_order_forbidden=true` 계약을 확인한다.

### 4.5 실패 또는 재실행

실패 시 다음 순서를 지킨다.

`terminal 상태 확인 → 최초 실패 단계 분리 → 입력·프로세스·artifact generation 확인 → 최소 복구 또는 코드 보완 → review gate → targeted validation → 필요한 producer부터 순서대로 재생성 → verifier → controller`

- 이전 실패 log의 마지막 traceback만 보고 현재 상태를 단정하지 말고 latest target-date run을 찾는다.
- controller가 이미 수행한 source refresh/retry/workorder regeneration을 중복 수행하지 않는다.
- wrapper 재실행은 missing DONE/START marker, recoverable artifact missing, stale source chain 등 runbook 허용 조건에만 사용한다.
- structural defect가 코드 변경을 요구하면 report를 먼저 억지로 재생성하지 않는다.
- package/auth, provider route, real-runtime authority, broker/cap/hard-safety 문제는 숨기지 않고 `blocked_non_recoverable` 또는 `user_authority`로 남긴다.

## 5. Source-quality와 lineage 점검

`observation_source_quality_audit`는 튜닝 입력의 선행 hard gate다.

- `tuning_input_allowed`, status, hard-blocking contract gap, required-field missing, invalid canonical label을 확인한다.
- 결손 row는 0수익·정상·미체결로 보간하지 않는다.
- `raw_row_exclusion`으로 격리 가능한 일부 row 결함과 전체 날짜 차단을 구분한다.
- 동일 report의 JSON/Markdown과 producer completion time을 대조한다. schema가 generation/source hash를 선언한 artifact만 그 값을 검증하고, 선언하지 않은 artifact는 direct source path/fingerprint, generated/completion time과 downstream link를 사용한다.
- pre-baseline raw/report/analytics는 archive/audit evidence로만 유지한다.
- KRX, `PREMARKET_KRX_LIKE`, NXT의 venue/session/route를 합치지 않는다.
- full fill과 partial fill, completed와 active/HELD, real과 sim/source-only, 실현손익과 counterfactual을 합산하지 않는다.
- main/widget/episode/manual owner의 order ID, lifecycle/episode/profile/leg ID와 broker receipt를 상호 대체하지 않는다.
- late arrival, fill-before-submit, event-time regression은 local arrival provenance와 broker event time을 함께 보존한다.

source-quality가 막히면 EV, rolling/MTD/cumulative tuning, live-auto promotion과 runtime approval을 `source_quality_blocked`, `runtime_effect=false`로 닫고 직접 원인·owner artifact·다음 보완·acceptance test를 기록한다.

## 6. 장후 튜닝결과 판정

### 6.1 공통 경제성 기준

성과는 후보 수, 승률, gross MFE 또는 report 생성 건수로 판정하지 않는다.

- primary metric은 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 계약에 맞는 EV다.
- 승률은 `diagnostic_win_rate`, `simple_sum_profit_pct`는 비-EV 보조값으로만 사용한다.
- 손익에는 실제 또는 정책상 고정된 수수료·세금·spread·slippage와 fill feasibility를 반영한다.
- `2026-08-18` 이후 R0→R3 비교는 effective-dated 정책의 매수 수수료 1.5bps, 매도 수수료 1.5bps, 매도 세금 20bps, Provider 비용 0원 계약과 공식 보통주 master를 사용한다.
- exact broker receipt 비용은 실거래 reconciliation 근거로 별도 보존하고 R0→R3 비교비용을 암묵적으로 대체하지 않는다.
- 비용모델 effective date, source hash 또는 symbol master가 맞지 않으면 해당 EV 입력을 차단한다.
- 미청산·right-censored row는 completed EV에서 제외하고 custody·자본점유로 별도 보고한다.
- daily 결과만으로 live/canary/threshold를 승인하지 않고 rolling/cumulative 또는 post-apply version window를 함께 본다.

### 6.2 메인 봇

다음 lifecycle을 candidate와 실제 order/receipt 단위로 재구성한다.

`selection → entry → entry-price → submit → probe/residual → holding → scale-in → partial TP/trailing/exit → broker reconciliation`

확인 항목:

- 최초 차단 owner와 직접 원인이 scanner, AI, latency, micro, price, account, order, quantity, cooldown 중 무엇인지
- score가 prior/feature 역할을 넘어 단독 BUY 또는 DROP 권한이 되지 않았는지
- probe/residual/scale-in 수량과 가격이 `position_sizing_dynamic_formula`, fresh BBO, owner 계약을 지켰는지
- 주문 API와 WS receipt 도착 순서가 바뀌어도 exact 주문번호와 immutable owner가 유지됐는지
- continuation 참여 부족, avg-down 손실 확대, 부분익절·runner·trailing 지연 또는 조기청산이 순이익을 훼손했는지
- 실제 청산과 1·3·5·10·20·30·60분 post-sell counterfactual이 분리됐는지

### 6.3 위젯 매매기계

`signal → source/policy match → episode lock → entry order → fill → target order → terminal/custody reconciliation`을 종목·episode별로 점검한다.

- allowed signal, source date/hash, policy version, venue/session과 episode ID 일치
- stale/repeated snapshot의 중복 episode 생성 여부
- entry/target 주문번호, partial fill, 남은 수량 owner 정합성
- completed episode 비용 차감 EV, signal-to-fill, fill-to-target, 목표 완료시간, 자본점유시간
- 목표 선후를 executable 가격으로 판단했는지와 same-bar high 오판 여부
- `HELD`·미청산을 0수익 또는 completed로 섞지 않았는지
- research watch와 expansion recommendation을 live policy 승격으로 오인하지 않았는지

### 6.4 에피소드 매매기계

`exact-date profile → setup → leg별 제출 → leg별 체결 → leg별 target → COMPLETE/NO_TRADE/HELD/BLOCKED → custody reconciliation`을 profile/leg별로 점검한다.

- exact-date policy/profile hash와 실제 process·state·ledger 일치
- 신규 episode의 두 개 10주 leg와 최대 20주 계약, legacy 1주 custody 비확대
- 원주문번호별 지정가·부분체결·잔량취소·target 귀속
- KRX entry와 NXT exit를 동일 lifecycle의 phase venue로 보존했는지
- owner별 terminal sample, 실현비용, HELD·미해결 custody와 자본점유
- machine entry timing 후보가 entry 확인 지연 단일 축만 바꾸고 수량·가격·target·holding/exit 권한을 만들지 않았는지

### 6.5 Micro-reversion·AI·Smoothing

Micro-reversion은 executable BBO, quote age, spread, fill feasibility, target/adverse first-hit와 tail loss를 본다. ask depletion은 0B 공격적 매수 backing, 0D 미설명 또는 cancel-like 감소, refill, bid 지지와 가격 반응을 함께 결속하고 단일 ask 잔량 감소를 상승 label로 쓰지 않는다. exact order identity가 없는 감소를 실제 취소로 확정하지 않는다.

AI는 세 층을 분리한다.

1. 호출 품질: provider, model, transport, timeout, failback, cache, response ID
2. 입력 품질: exact snapshot/payload, 완성 분봉, BBO/tape, venue/session, request·prompt·bundle version과 hash
3. 판단 품질: raw/normalized/final action, edge/risk/reason, mature outcome, first-hit, downstream submit/holding/exit와 비용 차감 EV

AI가 필수인 경로는 `provider=none`, unparsed, schema reject, missing receipt를 fail-closed한다. 의도적으로 AI를 사용하지 않는 OFF/disabled 경로는 provider 부재를 장애로 세지 않되 AI 검토 성공으로 포장하지 않는다. provider/schema 성공만으로 판단 품질 성공을 주장하지 않는다. 일반 paired replay는 동일 payload 계약을 사용하고, 의도된 feature/prompt ablation은 아래 R0→R3의 manipulated-field 계약으로 따로 검증한다.

Smoothing은 raw/smoothed score, EWMA state, persistence, snapshot age, policy version과 최종 action을 결속한다. whipsaw 감소와 함께 늦은 손절, 이익반납, 진입·익절 지연이 증가했는지 확인하며 stale/observer-unhealthy 입력의 smoothed 값을 사용하지 않는다.

## 7. 계산·입력소비·프로세스 유효성 감사

장후 report의 최종 숫자만 읽지 않는다. 결정론적으로 선택한 층화 표본과 집계 전체를 `raw source → parser/normalization → join → cohort/filter → label → executable price/cost → aggregation/window → candidate/decision → consumer` 순서로 역추적한다.

### 7.1 계산 lineage와 재현성

각 primary 결과에 대해 다음을 확인한다.

1. 원본 physical file, partition, DB row 또는 immutable snapshot의 경로·크기·hash·target date
2. parser/schema version, canonical field mapping, sign·unit·timezone·venue/session 변환
3. dedup key, event order, owner/lifecycle join key와 unmatched·duplicate·conflict count
4. cohort inclusion/exclusion 사유, missing/null/right-censored 처리와 분모
5. entry/exit executable price, tick rounding, partial/full fill, fee/tax/spread/slippage 계산
6. target/adverse first-hit 순서, label horizon과 mature cutoff
7. artifact의 `window_policy`/registry가 선언한 daily·rolling 5일·10일·20일·MTD·cumulative 중 해당 window의 경계와 clean-baseline 적용. 선언하지 않은 window의 부재를 결함으로 만들지 않고, 필수 window 누락 여부는 owner 계약으로 판정
8. sample floor, p10/tail, EV와 net-profit aggregation 공식
9. candidate ranking, deterministic guard, selected/rejected/blocked 이유
10. output row count·summary count·JSON/Markdown parity와 downstream input hash

표본 검증은 실행자가 임의로 고른 몇 건으로 끝내지 않는다. 고정 seed 또는 stable row-key hash로 `sample_manifest`를 만들고, 존재하는 범위에서 owner, venue/session, lifecycle stage/action, full/partial/unfilled, terminal/right-censored, target-first/adverse-first/same-hit/unresolved, source-quality pass/excluded, 장 시작·종료·자정·window 경계 층을 포함한다. 선택 row/trace/episode/order ID, 선택 규칙, strata별 모집단·선택 건수와 manifest hash를 evidence ledger에 남기며 표본을 원천 row부터 독립 재계산한다.

표본 검증과 별도로 producer schema가 먼저 선언한 mutually-exclusive primary state와 denominator 계약을 고정하고 전체 row 보존식을 전수 대조한다. 아래 식은 해당 상태들이 실제로 exhaustive/disjoint일 때만 적용하며 artifact별 N/A를 기록한다.

- source census = 서로 배타적인 primary-state count 합. `accepted|excluded|unresolved`는 해당 schema가 이 셋을 primary partition으로 선언한 경우에만 합산
- unique primary/join key 수, dedup 전후 row, duplicate/conflict/unmatched와 downstream row 수
- group별 count·notional·profit numerator/denominator의 합 = summary 값
- eligible denominator = 그 eligible set 안에서 선언된 completed/right-censored/invalid 상태 합. excluded row는 eligible denominator 밖에서 source census로 별도 reconciliation
- excluded row는 단 하나의 `primary_exclusion_reason`으로 보존식을 닫고, 겹칠 수 있는 secondary reason은 별도 multi-label census로만 보고
- first-hit denominator = target-first + adverse-first + same-hit/ambiguous + unresolved. 해당 artifact가 이 상태를 배타적 primary first-hit partition으로 선언한 경우에만 적용

golden fixture와 synthetic boundary case를 사용해 timezone·tick·partial fill·same-hit·window 경계를 검증하고, 행 순서 변경·gzip/plain 동등 입력·허용된 partition 재배치에 결과가 불변인 metamorphic test를 수행한다. 미래 label/outcome 값을 교란해도 당시 live/AI decision input, original action과 R0 request cohort/admission은 변하지 않아야 한다. 반대로 R1/R2 label·EV는 perturbation oracle에 맞게 재계산되고, R3는 모든 outcome-dependent guard/ranking을 다시 평가해 기대 selection과 일치해야 한다. threshold/ranking 경계를 넘지 않아 R3 selection이 동일한 경우도 정상이며 이때 unchanged guard/ranking 근거를 남긴다. 미래값이 R0 request/prompt로 역류하는 경우만 leakage다. producer schema가 정한 Decimal/rounding mode와 표시 자릿수를 사용하고, 부동소수 비교 tolerance는 필드별 절대·상대 허용값과 근거를 기록한다. 허용범위 밖 차이를 반올림 차이로 넘기지 않는다.

deterministic producer는 같은 immutable input과 policy version의 재실행에서 timestamp 등 schema가 허용한 비결정 필드를 제외한 canonical content hash 또는 명시된 semantic digest가 같아야 한다. AI Provider 출력에는 byte-identical hash를 강제하지 않고 exact request/source hash, persisted response·receipt·checkpoint provenance, 동일 contract와 중복 호출 방지를 검증한다.

다음은 계산 결함으로 본다.

- 같은 event/episode/order가 중복 집계되거나 owner·venue·session을 넘겨 join됨
- 미래 outcome, 미완성 분봉 또는 label이 decision input에 들어가는 leakage
- 결손을 0·정상·미체결·무손익으로 보간하거나 right-censored를 completed로 합산
- percent/bps/KRW, 부호, 세금·수수료, tick size 또는 KST/UTC 변환 오류
- mark/high/low를 executable fill·exit로 대체하거나 target/adverse 동시 hit 순서를 추정
- daily child의 얇은 표본이 rolling parent 또는 live authority를 대신함
- report summary와 실제 row, JSON과 Markdown, producer와 consumer의 count/hash가 불일치
- `NaN`, infinity, malformed JSON/JSONL, plain/gzip divergence 또는 stale generation을 정상값으로 소비

계산이 맞더라도 primary decision field가 metric contract의 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 갖지 않으면 `instrumentation_gap` 또는 `source_quality_blocker`로 분류한다.

계산 감사 중 `sample_floor` 미달, underproduction, natural match 0, submit/terminal/mature outcome 부족을 발견하면 최종 count만 읽지 않고 §8.4의 reachability 계산과 `shortage_ledger`를 함께 작성한다. `hold_sample|EVIDENCE_ACCUMULATING|defer_until_more_sample` 상태나 그 반복 횟수 자체는 구조적 고갈 증거가 아니며, declared window 안의 유입·maturity·expiry와 최초 funnel 고갈 stage로 판정한다.

### 7.2 AI 판단품질 계산 감사

AI endpoint별로 자연 호출, offline replay와 결과 평가를 같은 trace lineage로 연결한다.

- request/trace/snapshot ID, exact prepared payload hash, prompt/schema/bundle version
- provider/model/temperature/reasoning budget, key alias, attempt, timeout/failback, cache key와 response ID
- raw response, parsed response, normalization, semantic validation과 final action의 변환 단계
- 입력 시점에 이용 가능했던 완성 분봉, BBO, 0B/0D, venue/session, account-independent context
- action-neutral mature label, MFE/MAE, target/adverse first-hit, missed-upside와 downstream submit/holding/exit
- 일반 동일-payload Control/Candidate replay는 같은 eligible source pool, exact payload, provider/model/temperature/reasoning budget과 비용·outcome 계약을 사용했는지

outcome label이나 미래 상태가 R0 provider request cohort/admission 또는 prompt input selection에 들어가면 leakage로 차단한다. R1/R2 평가와 R3 outcome-based tuning candidate selection이 mature outcome을 사용하는 것은 정상 계약이며, 그 결과가 R0로 역류하지 않는지 확인한다. `BUY`, `WAIT + probe intent`, `WAIT observation-only`, `DROP`, `INSUFFICIENT_DATA`를 같은 action으로 합치지 않는다. transport/schema 성공률과 판단 EV를 분리하고, cache hit는 exact payload/prompt/schema hash가 일치할 때만 재사용한다.

모든 실험 row는 `declared_manipulated_fields`를 갖고 그 외 source pool, parent/request identity, provider/model/temperature/reasoning/retry·budget, economic/cost와 outcome-label 계약이 같아야 한다. 의도된 실험축이 있는 arm 전체에 identical prompt/payload를 강제하지 않는다.

R0→R3는 다음을 각각 검증한다.

- R0: exact request/trace/source census와 immutable payload capture
- R1: target-date mature daily label과 action-neutral outcome
- R2: 겹치는 날짜 generation dedup, common parent·거래일·종목 floor와 rolling aggregation
- R3: 검증된 R2 artifact hash, cost/master binding, source-only manifest와 forbidden authority

현재 A/B/C 계약은 다음처럼 고정한다.

- A: current prompt + exact tactical micro
- B: A와 동일한 control decision/execution contract·tactical micro에 ask-depletion feature만 추가한다. A→B의 `declared_manipulated_fields`는 ask-depletion feature와 그 content hash뿐이다.
- C: candidate prompt/response contract와 B의 byte-identical tactical micro·ask-depletion candidate input을 사용한다.
- B/C 공통 parent identity는 `paired_replay_parent_id`, decision trace, stage/endpoint, symbol, venue/session, payload·request-envelope·source-exact-payload hash로 고정한다.
- B/C locked execution fields는 provider, model, temperature, reasoning effort, transport, max output tokens, response-schema mode, require-JSON과 schema-registry-used다.
- B→C에서 달라질 수 있는 decision-contract fields는 prompt version, system prompt 본문/hash, schema name, response schema 본문/hash와 semantic-validator version이다. `response_schema_application`은 provider별 schema 전달 계약과 해당 response schema에 일치하는 값만 허용한다.
- `paired_replay_id`, arm name, physical request/attempt/response receipt ID는 arm별 고유값이 정상이다. shared parent mapping과 arm별 고유성·receipt binding을 검증하며 이 값을 byte-identical 대상으로 삼지 않는다.
- locked execution field, shared candidate input 또는 shared parent identity의 차이는 두 번째 실험축으로 거부한다. arm별 고유 metadata 자체를 신규 request metadata drift로 오판하지 않는다.
- A→B 비열화 방지와 A→C 비용 차감 EV·uplift·p10·severe-tail gate를 분리해 재계산한다. A/B/C는 모두 source-only이며 R3만으로 runtime/prompt/order 권한을 만들지 않는다.

Provider 호출이 필요한 단계에서 `provider=none`, key/provider preflight 실패, unparsed/schema reject, missing receipt가 있으면 결과 생성을 성공으로 보지 않는다. 일부 결과만 있는 retry는 검증된 checkpoint를 재사용하고 실패 request ID만 bounded retry하며, 중복 provider 호출이나 일부 성공을 완전한 census로 포장하지 않는다.

### 7.3 Micro-reversion 계산 감사

Micro-reversion과 ask-depletion 계열은 다음 불변조건을 표본별로 확인한다.

- 0B와 0D가 동일 symbol·venue·session·sequence epoch이며 각 stream monotonic sequence를 독립 검증했는지
- broker/event time과 local receive time을 구분하고 past-only 허용창 밖 row를 결합하지 않았는지
- best bid/ask, depth 1~5, quote age, spread, tick size와 executable quantity가 신호 시점에 fresh했는지
- ask 감소를 `aggressive_buy_trade_backed`와 `unexplained_or_cancel_like`로 구분하고 refill/replenishment, bid 붕괴·가격 반응을 함께 봤는지. exact order identity가 있는 경우에만 실제 취소로 확정했는지
- `bid+1`은 venue-effective tick table로 계산하고 `< best_ask`일 때만 passive queue/TTL 3·5·10초 arm으로 분류했는지. `>= best_ask`이면 bounded ask/marketable arm으로 재분류해 passive fill·cost 분모와 합치지 않고 timeout exit를 같은 lineage로 결속했는지
- 3·10·20·30초와 1·3·5분 target/adverse first-hit가 event order로 계산됐는지
- fill 이전 고가·저가를 outcome으로 쓰지 않고, 동시 hit·결측·right-censored를 별도 상태로 보존했는지
- 총비용 차감 EV, adverse-first, p10/severe tail과 기존 정상 경로 비훼손을 함께 판정했는지

정상 reconnect가 명시한 새 transport sequence epoch는 결함이 아니라 분리 경계다. 새 epoch의 event를 이전 epoch와 join하지 않고, 새 epoch에 causal market row가 아직 없으면 이전 epoch로 후퇴하지 않는다. 반면 undeclared reset, 한 join window 안의 competing epoch, cross-epoch join, crossed BBO(`ask < bid`), nonpositive price, negative quantity, stale quote, route conflict와 physical partition 불일치는 해당 scope를 fail-closed한다. zero quantity row는 ask-depletion feature, path, refill과 first-hit lineage에 유효 source로 계속 보존한다. 단, exact entry/exit timestamp·side에서 required quantity 대비 capacity가 0이면 그 counterfactual exposure만 fill-ineligible로 분류한다. 이미 broker-confirmed된 actual fill, earlier valid entry parent 또는 다른 side/horizon을 후행 zero depth 때문에 EV에서 제외하지 않는다. locked quote(`ask == bid`)는 venue/session/source 계약에 따라 `locked_quote`로 분리하고 해당 consumer 계약이 금지할 때만 affected scope를 차단한다. synthetic boundary test와 실제 exact-date 표본 재계산을 모두 통과해야 parser/calculation 결함이 닫힌다.

### 7.4 실제 매매기계 입력 소비와 다음-session handoff 감사

report나 policy 파일 존재만으로 매매기계에 입력됐다고 보지 않는다. 다음 두 시간축을 섞지 않고 artifact authority에 허용된 마지막 consumer까지만 확인한다.

#### A. 대상일 execution acceptance

대상일 장전까지 검증·적용된 artifact가 대상일 실제 process에 소비된 경로다.

- 메인 봇: prior postclose/PREOPEN candidate·apply plan → runtime env JSON/env hash → launcher load order → 대상일 PID env/commit → stage adapter 호출 → pass/block/recheck/submit/holding/exit event → broker terminal receipt
- 위젯: 대상일 execution-qualified exact policy → `WidgetAutoTradePolicyLoader`/systemd service가 읽은 policy·source date → episode state/lock → entry/target order와 terminal ledger
- 에피소드: 대상일 approved/exact-date applied profile hash → timer/service/process → profile/leg state → leg별 entry/target order number → COMPLETE/HELD/BLOCKED와 custody reconciliation

#### B. 대상일 postclose generation과 다음-session handoff

대상일 장후 산출물은 producer·schema·source/hash·authority·loader dry-validation과 다음 PREOPEN handoff까지만 현재 완료 범위다. 다음 거래일 PID가 실제로 읽었는지, 자연 표본에서 호출됐는지와 post-apply attribution은 다음 거래일 checklist의 OPEN acceptance다.

- 메인: postclose candidate → authority/registry/bridge guard → 다음 PREOPEN apply-candidate 또는 source-only blocker. current R0→R3 source-only production은 active하게 검증하되, fail-closed/disabled인 legacy main-AI PREOPEN/live consumer와 혼동하지 않는다.
- 위젯: source-qualified report → 20:10 advisory·auto-trade calibration·symbol research·runtime-policy producer → exact next-session policy. observation collector policy는 collector/report만, execution-qualified subset만 loader 입력, research recommendation은 operator review까지만 허용한다.
- 에피소드: recommendation/candidate는 operator review 또는 다음 exact-date policy builder까지만 확인한다. `machine_created=false|service_started=false`인 source-only candidate를 실패나 실행 input으로 오인하지 않는다. 승인되고 exact-date로 applied된 profile만 다음-session timer/service/order 경로의 후보가 된다.

각 artifact는 schema가 선언한 `decision_authority`, `runtime_effect`, `allowed_runtime_apply`, `execution_enabled` 또는 동등 authority 필드를 우선 읽어 intended last consumer를 정한다. 해당 artifact 계약상 필수 authority 필드가 없거나 서로 모순되면 실행 경로로 추정하지 않고 contract gap으로 차단한다. producer output field가 intended consumer의 실제 input field·version·hash와 일치하는지 확인한다. 대상일 execution에서 default/fallback 값이 fresh applied policy를 가렸거나, 대상일 PID가 old env/policy를 유지하거나, eligible input이 있었는데 consumer counter가 0인 경우는 `runtime_hook|env_mapping|process_reflection` 결함이다. 장후 생성된 다음-session artifact에 대상일 PID 소비 증거가 없다는 이유만으로 결함 판정하지 않는다.

main/widget/episode 간 공통 symbol이 있어도 policy, state, lock, order, quantity, custody와 exit owner를 공유하지 않는다. 잘못된 입력을 감지했을 때 기존 hard safety와 owner isolation으로 주문을 차단한 경우 안전장치는 정상으로, upstream mapping/parser 결함은 별도로 기록한다.

### 7.5 Dead·무의미·중복 process 감사

먼저 runbook, 실제 설치된 crontab/systemd timer·unit와 trusted runtime registry/launcher manifest를 대조해 대상일 authoritative expected set을 동결한다. 선언됐지만 미설치, 설치됐지만 미등록, reviewed disabled/retired 차이도 set 안에 상태와 근거로 보존한다. `ps`, `pgrep`, command-name 검색은 후보 발견용 triage일 뿐 expected/dead/orphan 판정의 최종 권한이 아니다. cron, systemd timer/service, tmux bot, long-running worker/thread, postclose one-shot wrapper와 writer를 inventory로 만든다. 각 항목은 다음 계약을 가져야 한다.

`declared owner → installed/enabled trigger → expected window → PID/exit/heartbeat → artifact or valid terminal skip → registered consumer → consumed field → decision/report role → downstream freshness`

읽기 전용으로 다음을 확인한다.

- crontab/systemd timer의 실제 설치·enable·last/next trigger와 runbook 선언 일치
- systemd `MainPID`·cgroup, declared supervisor, singleton lock와 service state를 우선하고 PID start time, executable/cwd, commit/source-dirty, env/policy hash, heartbeat와 latest progress marker를 교차검증
- singleton lock, 중복 PID/thread/writer, zombie, declared supervisor/cgroup/owner/consumer contract가 없는 orphan, crash loop, timeout/hang과 stale lock
- CPU·RSS·swap·disk·queue/drop·writer error가 main WS·scanner·AI·submit을 방해했는지
- 성공 exit인데 artifact가 없거나 stale한 `no_op_success`, 매번 빈 결과만 내는 경로의 valid-empty 근거
- producer는 계속 실행되지만 current consumer가 없거나 field를 전혀 읽지 않는 `orphan_producer|unconsumed_artifact`
- 같은 source를 중복 계산하고 어느 쪽도 authoritative하지 않은 `duplicate_or_redundant_owner`
- retired code/artifact compatibility parser를 active process로 오인했는지

process 상태는 다음으로 분류한다.

- `healthy_active`
- `healthy_no_natural_sample`
- `one_shot_completed`
- `disabled_by_contract`
- `retired_absent`
- `not_yet_due|bounded_wait`
- `dead_expected_process`
- `hung_or_stale`
- `crash_or_restart_loop`
- `duplicate_owner`
- `no_op_success`
- `orphan_producer|unconsumed_artifact`
- `meaningless_redundant_process`
- `unknown_contract`

각 inventory row에 expected-set source, unit/timer/launcher ID, `MainPID`·cgroup·lock·heartbeat, owner/consumer, expected window, artifact/terminal evidence와 분류 사유를 남긴다. PPID=1만으로 orphan을 선언하지 않는다. 현재 감사용 command/test process, 정상 one-shot 종료의 PID 부재, reviewed disabled/retired 경로, eligible input 0과 valid-empty/terminal skip이 증명된 경로는 dead/no-op 오탐에서 제외한다. 반대로 이름·로그·PID만 있고 output/consumer/decision role이 연결되지 않으면 가동 중으로 판정하지 않는다.

dead/no-op/orphan 판정만으로 process를 즉시 kill·disable·restart하거나 코드를 삭제하지 않는다. active consumer 검색, runbook/registry/installer/error-detector coverage, 최근 거래일 source lineage와 custody 영향까지 확인한다. report-only 구조 결함은 최소 wrapper/instrumentation 보완과 review gate로 닫고, live process state 변경은 별도 사용자 권한과 broker reconciliation을 요구한다.

### 7.6 결함 보완과 결과 재생성

계산·consumer·process 결함은 다음 loop로 닫는다.

`최초 잘못된 row/stage 확인 → 단일 owner와 producer/consumer 분리 → 최소 코드·schema·instrumentation 보완 → regression/경계 테스트 → review finding 0 → immutable source 재계산 → 관련 downstream 순차 재생성 → old/new diff → verifier/controller 재판정`

보완 후에는 단순히 status가 pass로 바뀌었는지뿐 아니라 다음을 확인한다.

- 결함 표본의 기대값이 정확해졌고 정상 표본이 비훼손됐는지
- row/group/summary count와 hash가 producer/consumer 전 구간에서 일치하는지
- 잘못된 candidate/workorder/runtime handoff가 제거 또는 blocked됐는지
- 필요한 새 instrumentation이 실제 다음 consumer와 verifier에 나타나는지
- 재생성된 결과가 새 generation/source fingerprint를 가지며 이전 stale artifact를 참조하지 않는지

재생성 전에는 대상 artifact의 path, hash, generation/source date와 producer command를 pre-snapshot manifest로 고정하고 이전 generation bytes와 rollback reference를 감사용으로 보존한다. 발견된 결함이 이전 generation의 decision, source-quality 또는 runtime eligibility에 영향을 주면 즉시 `quarantined|source_quality_blocked|not_authoritative`로 표시하고 consumer를 fail-closed하며 다음 PREOPEN handoff에서 제외한다. 이 known-bad generation으로 authority pointer를 되돌리지 않는다. 이전 generation을 authoritative rollback 대상으로 유지할 수 있는 경우는 결함 영향 밖이고 schema·source·authority가 여전히 유효함을 별도로 증명했을 때뿐이다.

새 산출물은 staging 경로에서 schema·hash·count·downstream consistency를 검증한다. multi-artifact generation은 모든 file path/hash/source generation을 열거한 transaction manifest 또는 generation pointer를 마지막 commit point로 atomic publish하고, consumer가 그 pinned generation을 읽었다는 receipt를 남긴다. 이 계약이 없는 producer는 consumer quiescence와 shared lock으로 old/new 혼합 불가를 증명해야 한다. mixed-generation census가 0이 아니면 publish를 차단한다. verifier 실패 또는 중간 producer 실패 시 partial output을 승격하지 않는다. 영향 밖임이 검증된 이전 generation만 유지하고, known-bad이면 차단 pointer/receipt와 함께 audit-only로 보존한다. 두 경우 모두 rollback 또는 blocked receipt를 남긴다. 재생성은 다음 의존 순서를 사용한다.

1. 결함이 난 raw snapshot/checkpoint와 source-quality audit를 검증한다.
2. 수정된 calculation/parser producer와 AI 또는 micro exact-date report를 재생성한다.
3. 해당 producer를 소비하는 ADM/LDM·bucket·machine attribution/calibration을 필요한 범위에서 재생성한다.
4. `threshold_cycle_ev` pre-pass를 생성한다.
5. first workorder를 생성한다.
6. EV post-pass → pattern-lab propagation/AI provenance refresh → refreshed EV를 순서대로 닫는다.
7. runtime summary를 생성한 뒤 runtime apply gap → key lineage → conversion을 생성한다.
8. conversion을 반영한 workorder를 갱신한다.
9. final EV → final workorder fingerprint → final runtime summary 순서로 고정한다.
10. 다음 checklist가 영향받으면 generator로 갱신하고 parser validation을 실행한다.
11. verifier를 재실행하고 controller는 runbook이 허용한 same-date recovery 또는 최종 판정 경로로만 닫는다.

§9 Pass 1을 시작할 때는 수정 전 authoritative final workorder를 intake한다. 위 ordered regeneration의 중간 workorder는 lineage diff로만 추적하고, step 9의 final workorder가 terminal이 된 뒤 Pass 2 전수 재점검을 수행한다. Pass 2 수정으로 영향 producer가 바뀐 경우에는 관련 부분만 이 순서로 다시 재생성하고, eligible `new|decision_changed implement_now=0`인 fixed-point를 확인한 뒤에만 verifier/controller 최종 판정을 최신으로 인정한다.

각 step은 exact command, input/output hash, 시작·종료시각, exit code, reused checkpoint와 skipped reason을 기록한다. 중간 step이 실패하면 뒤 결과를 최신으로 표시하지 않는다. 결함 영향 밖으로 검증된 마지막 유효 generation만 authoritative하게 유지하고, known-bad generation은 audit bytes로만 보존하며 consumer reference를 0건 또는 명시적 blocked receipt로 닫는다. full wrapper 재실행이 필요하면 현재 동일 날짜 process가 없고 controller의 `allow_wrapper_rerun` 사유가 맞는지 먼저 확인한다.

이 순서는 해당 날짜 execution profile에서 enabled된 producer에만 적용한다. OFF/disabled/retired stage를 freshness 충족 목적으로 임의 실행하거나 빈 artifact로 합성하지 않는다.

실데이터를 수정·삭제해 테스트를 맞추지 않고 immutable raw와 reconciliation evidence를 보존한다. 결손 원천을 소급 추정할 수 없으면 `not_available|source_quality_blocked`로 남기고 계산값을 만들지 않는다.

## 8. Runtime·handoff 판정

### 8.1 R0→R6 tuning family와 sim 경로

LDM/bucket/active-sim/scalp-sim/swing-sim family·arm은 다음 순서로 보고한다.

`identified → source quality valid → sim policy/catalog 반영 → PREOPEN sim 후보 → runtime observation match → terminal outcome → rolling/cumulative EV → real bridge blocker → post-apply attribution`

반드시 다음 세 질문에 먼저 답한다.

1. 유효한 source quality로 flow/bucket/arm이 식별됐는가?
2. policy catalog·PREOPEN env·runtime observation을 통해 sim에 실제 적용됐는가?
3. real runtime 반영까지 무엇이 남았는가?

Swing dry-run, sim/probe/counterfactual은 source와 후보 생성에는 사용할 수 있지만 broker execution 품질이나 실주문 전환의 단독 근거가 아니다.

### 8.2 메인 live family와 독립 매매기계

메인 live family는 `PREOPEN candidate/apply plan → runtime env/PID → eligible stage call → order/terminal outcome → rolling EV → post-apply attribution`을 따른다.

위젯과 에피소드는 대상일 실제 소비와 장후 다음-session handoff를 분리한다. 대상일 execution-qualified applied policy/profile은 `process/state → order/terminal/custody`까지 확인한다. 장후 생성된 exact next-session policy/profile candidate는 현재 postclose에서 authority와 intended last consumer까지만 확인하고, 다음 거래일 실제 PID load·자연 호출·post-apply는 다음 checklist acceptance로 넘긴다. 위젯·에피소드에는 LDM sim catalog나 메인 PID env를 강제하지 않는다.

- 위젯 observation-only policy: prospective collector/report까지만 소비하며 loader/order 경로 진입은 결함이다.
- 위젯 execution-qualified policy: `execution_enabled=true`와 source/execution safety, loader round-trip이 닫힌 subset만 다음 PREOPEN loader 후보가 된다.
- 위젯 research recommendation: `runtime_effect=false`, `allowed_runtime_apply=false`, `collector_created=false`, `service_started=false`를 유지하고 operator review에서 끝난다.
- 에피소드 recommendation/candidate: `machine_created=false|service_started=false`이면 review-only다.
- 에피소드 approved/exact-date applied profile: 명시된 effective date에만 timer/service/order 경로가 열리며 target/quantity/holding 계약을 임의 확대하지 않는다.

각 owner는 다음을 답한다.

1. 대상일 applied policy/input을 실제 process가 읽었는가? 장후 다음-session 산출물은 authority에 맞는 handoff·loader dry-validation까지만 닫혔는가?
2. eligible 자연 표본에서 consumer가 호출됐으며 pass/block/submit/terminal 증거가 있는가?
3. 미호출·미반영·source-only·HELD를 정상 효과와 분리했는가?
4. 다음 exact-date 적용 또는 real authority에 필요한 blocker와 rollback owner는 무엇인가?

### 8.3 공통 상태와 blocker

상태는 다음 중 하나로 분류한다.

- 정상 호출·의도한 효과 확인
- ON이지만 자연 표본 없음
- ON이지만 호출되지 않음
- 호출됐지만 source/venue/policy/provenance 결손
- sim 적용 완료, real runtime 미반영
- source-only 정상 관측, 실주문 효과 없음
- 구현됐지만 현재 PID/process/policy 미반영
- 과차단·과제출·익절 지연·조기청산·손실 확대
- OFF·disabled·은퇴 상태로 현재 모집단 아님

blocked 상태는 `source_quality`, `sample_floor`, `submit_drought`, `env_mapping`, `runtime_hook`, `process_reflection`, `post_apply_attribution`, `AI_review`, `safety_or_broker_guard`, `user_authority`로 분리한다. `contract not closed`, `표본 부족`처럼 뭉뚱그리지 말고 owner artifact, 관측 근거, next repair action과 acceptance test를 각각 기록한다.

`sample_floor`는 다시 `natural_sample_wait`, `no_natural_sample`, `instrumentation_or_join_gap`, `terminal_or_right_censored_gap`, `fragmented_child_bucket`, `window_floor_unattainable`로 세분한다. 각 owner/scope/window마다 eligible opportunity, captured source-qualified row, mature terminal row, 최근 창의 일별 yield, floor까지 남은 수와 observed-yield 기준 예상 추가 거래일을 기록한다. yield가 0이면 도달일을 계산하지 않고 최초 0 stage와 upstream/downstream census를 기록한다. handoff·guard가 정상이고 opportunity 자체가 없으면 `natural_absence`로 두며 결손 owner를 만들지 않는다. required input이나 consumer가 있어야 하는데 contract breach로 0이 된 증거가 있을 때만 producer/join/terminal owner를 지정한다. exact owner의 선언된 일일 최대 lifecycle 수와 window 길이의 곱보다 floor가 크거나, rolling child를 계속 분할해 최대 관측 가능 수가 floor 아래이면 단순 이월하지 않고 `window_floor_unattainable` 또는 `fragmented_child_bucket`으로 fail-closed한다. 이때 floor를 자동 완화하거나 owner·venue·session을 합치지 않는다. 기존 metric contract가 이미 소유한 canonical rolling/cumulative parent의 원래 authority와 child-dimension 진단을 사용하는 것은 신규 authority 이전이 아니다. 새 parent·denominator·window를 만들거나 child authority를 parent로 이전할 때만 별도 metric-contract 변경과 review gate를 요구한다.

이 세부 원인 코드는 §8.4의 최종 `shortage_class`를 대체하지 않는다. 예를 들어 `natural_sample_wait`도 reachability 증거에 따라 시간 해결형 또는 `pending_declared_window`가 될 수 있고, 반복 `no_natural_sample`도 handoff 정상·finite reach가 입증되면 즉시 구조형으로 승격하지 않는다. 반대로 `fragmented_child_bucket|window_floor_unattainable`은 계약상 최대 도달치가 floor 아래임이 계산으로 확인될 때 구조형으로 연결한다.

은퇴한 opening rotation·upper-limit rotation·panic-buying과 WAIT6579 독립 bridge의 historical artifact는 archive/audit evidence일 뿐 재기동·재활성화 경로가 아니다.

### 8.4 부족의 시간성·구조적 모집단 고갈 판정

보고서에서 `부족`, `미달`, `자연 표본 없음`, `sample_floor`, `submit_drought`, `terminal outcome 부족`으로 해석하거나 required population의 `0건`을 문제로 제시하는 모든 항목은 stable한 `shortage_id`를 부여해 `shortage_ledger`에서 전수 관리한다. 오류·충돌·authority leak 0건처럼 0이 정상 목표인 metric은 부족으로 세지 않는다. 실질적인 표본·모집단 부족의 최종 `shortage_class`는 다음 둘 중 정확히 하나여야 한다.

- `time_resolvable_shortage` (`시간이 해결하는 부족`): producer부터 artifact authority가 선언한 intended last consumer 또는 sample-floor-owning stage까지의 경로가 정상이고 source quality도 유효하며, 같은 floor denominator 아래 새 qualifying unique 표본이 계속 유입될 수 있고 rolling-window expiry까지 차감한 보수적 도달 가능 표본이 선언된 관찰 horizon 안에 sample floor를 채운다는 유한한 근거가 있는 상태다. 계약상 유한한 maturity/terminal deadline과 별도 주문·청산 권한 변경 없이 자연 전환될 근거가 있는 right-censor 대기, 정상 handoff 뒤의 일시적 `natural_match_0`가 여기에 포함될 수 있다. 무기한 HELD 또는 deadline·자연 전환 근거가 없는 active-unrealized row를 시간 해결분으로 더하지 않는다.
- `structural_population_exhaustion` (`구조적으로 모집단이 고갈되는 부족`): 단순 대기로는 현재 계약의 eligible·matched·mature 모집단이 늘지 않거나, 예상 유입량으로는 sample floor·결정 horizon에 도달할 수 없는 상태다. 과도하게 잘게 나눈 child bucket, 불가능한 predicate나 posterior-only runtime match, source/policy key 불일치, systematic join/exclusion, eligible upstream은 있는데 특정 funnel 단계가 계속 0이 되는 hook·consumer 결손, 구조적 submit drought가 여기에 해당한다.

source-quality 결손 때문에 실제 모집단을 셀 수 없거나 owner의 `window_policy`, sample floor, maturity cutoff, effective/expiry horizon이 없어 둘 중 하나를 입증할 수 없으면 임의로 `time_resolvable_shortage`로 두지 않는다. `shortage_classification_status=blocked_missing_evidence`와 실제 blocker를 기록해 먼저 계약을 보완한다. 신규 경로의 declared minimum classification window가 아직 닫히지 않아 유입률을 계산할 수 없는 경우는 `shortage_classification_status=pending_declared_window`, 필요한 completed trading day 수와 earliest review date를 기록한다. 두 상태는 세 번째 최종 부족 유형이 아니며, 증거가 복구되거나 창이 닫히기 전에는 live-auto나 runtime approval의 정상 대기 근거로 사용할 수 없다. `pending_declared_window`는 명시한 earliest review date까지 제한적으로 `defer_evidence`에 둘 수 있지만 시간 해결형으로 포장하지 않는다. `not_yet_due|bounded_wait`, reviewed OFF/disabled, 완전 은퇴 family, artifact authority상 해당 consumer 표본을 요구하지 않는 경로, `user_authority` 대기, AI/source/env 계약 결손 자체는 표본 부족으로 위장하지 않고 `N/A_by_contract` 또는 각각의 원래 상태로 보고한다. 계약 결손이 stage count를 0으로 만든 사실이 유효 upstream/downstream census로 입증된 경우에만 그 결손을 구조적 고갈의 root cause로 함께 기록한다.

`shortage_class`는 기존 producer/verifier의 canonical 상태를 대체하거나 runtime schema를 새로 만드는 값이 아니라 장후 감사·결과보고 metadata다. 각 row에 `canonical_source_state`를 함께 보존하고 `hold_sample`, `no_natural_sample`, `source_outcome_underproduction`, `lifecycle_stage_underproduction`, `not_applicable`, `keep_visible_by_design`의 원래 의미와 status를 덮어쓰지 않는다.

각 `shortage_id`는 다음 funnel을 owner·family·stage·venue/session별 unique key로 재구성해 최초 고갈 단계를 고정한다. 모든 항목에 terminal까지 강제하지 않고 artifact의 `decision_authority`, intended last consumer와 floor denominator가 요구하는 단계에서 자른다.

`raw source population → source-quality-valid → contract eligible [→ catalog/policy selected → PREOPEN loaded → runtime natural matched when authority requires] → authority-declared last consumer/floor-owning stage [→ decision/submit/terminal mature/completed when the floor contract requires]`

최소 증거는 `metric_contract_version`, `shortage_metric`, `floor_denominator_key/unit`, denominator dedup key, `required_sample_floor`, `current_floor_qualified_unique`, `remaining_deficit`, 적용 `window_policy`, clean-baseline 시작, observed trading dates, completed due trading-day 수, source-available due-day 비율, 일별 `new_floor_qualified_unique`, 0건인 due day 수, `expiring_floor_qualified_unique`, 계약상 필요한 경우의 maturity backlog와 예정시각, first depleted stage, stage별 upstream count·conversion, policy effective/expiry 또는 다음 decision horizon, source/artifact hash다. `floor_qualifying_arrival_rate`는 exact floor denominator를 새로 충족한 unique row만 분자에 넣고, source-quality-valid census가 가능한 정상 due day의 0건도 분모에 포함해 `new_floor_qualified_unique / completed due trading days`로 계산한다. eligible/opportunity/matched/mature 등 다른 stage의 rate는 bottleneck 진단값일 뿐 floor ETA에 대입하지 않는다. source-quality 차단으로 census 자체가 불가능한 날은 자연 0일로 세지 않고 별도 excluded day로 보존한다. 같은 floor denominator의 `net_floor_accumulation_rate = floor_qualifying_arrival_rate - floor_expiry_rate`와 함께 사용한 lookback·분모를 명시한다. forecast는 metric contract가 선언한 minimum completed due days, source-available day floor, fixed lower-bound estimator를 충족해야 하며 양(+) 유입일만 골라 계산하지 않는다. 이 계약이 없거나 최소 창이 덜 찼으면 deterministic maturity deadline 근거가 있는 경우를 제외하고 `pending_declared_window|blocked_missing_evidence`로 둔다. cumulative 창은 expiry를 0으로 두며, rolling 창은 날짜별 신규 floor-qualifying 유입·maturity·expiry를 함께 투영한다. `conservative_reachable_n = current_floor_qualified_unique - expiring_floor_qualified_unique_before_horizon + conservative_expected_new_floor_qualified_unique`가 sample floor 이상이어야 시간 해결형이다. 비만료 창에서 `net_floor_accumulation_rate > 0`일 때만 `estimated_trading_days_to_floor=ceil(remaining_deficit / net_floor_accumulation_rate)`를 보조값으로 사용할 수 있고, rolling 창은 일별 expiry schedule을 반영한 earliest reach date를 사용한다. rate가 0, net accumulation이 0 이하, `conservative_reachable_n < required_sample_floor`, 또는 earliest reach date가 effective/decision horizon 밖이면 시간 해결을 주장하지 않는다. 단일 거래일 `natural_match_0`는 catalog/PREOPEN/key lineage가 정상이고 해당 natural-match floor denominator의 clean-baseline 또는 계약 window 비영(非零) base rate로 유한 reach date를 보일 때만 시간 해결형 warning이다.

판정과 보완은 다음 규칙을 따른다.

1. `time_resolvable_shortage`는 현재 수집 경로를 임의로 바꾸지 않고 `as_of`, conservative reachable N, ETA 범위, 다음 maturity/recheck 시각, 예상 신규·expiry 표본 수, 재분류 trigger를 남긴다. 시간 지정 후속은 당일 checklist에 `Due`, `Slot`, `TimeWindow`, `Track`을 가진 OPEN 항목으로 기록하되 같은 stable `shortage_id`의 기존 OPEN 항목을 갱신하고 중복 생성하지 않는다. ETA가 지났거나 최근 10개 completed trading day 안에서 동일 due check가 3회 이상 기록된 예상 유입 하한을 충족하지 못하거나, policy/key가 만료·미반영되면 즉시 다시 계산해 구조적 고갈 또는 실제 contract blocker로 재분류한다.
2. `structural_population_exhaustion`는 기다림이나 반복 `defer_evidence`로 닫지 않는다. 최초 고갈 stage의 단일 owner를 지정하고, 허용 범위에서 parent bucket widening과 child dimension/provenance 보존, safe sim/source-only 수집 확대, parser/schema/key-lineage/runtime-hook/instrumentation 보완, maturity scheduler 또는 consumer 연결 보완 중 최소 조치를 workorder로 넘긴다. 단, 정당한 safety guard가 계약대로 제외한 모집단은 `structural_by_design_safety_exclusion`, `action=reject_nonpromotion`으로 두고 safety 완화나 구현 workorder 대상으로 만들지 않는다. live threshold·실주문 authority·provider·bot·cap·broker/hard-safety 변경이 필요하면 구현하지 않고 `user_authority`로 분리한다.
3. 구조 보완 acceptance는 report row 생성이 아니라 같은 corrected path에서 신규 source-quality-valid이면서 exact floor denominator를 충족한 unique 표본이 first depleted stage를 통과하고, owner/venue/session 분리·전수 보존식·downstream hash가 닫히며, 재계산된 finite ETA 또는 sample floor 충족이 확인되는 것이다. 영향 artifact를 재생성할 때는 §7.6 순서와 review gate를 따른다.
4. 표본 수를 맞추기 위해 row 복제·가중치로 unique 수 부풀리기, pre-baseline 자료 재사용, right-censored/HELD를 completed로 전환, main/widget/episode 또는 KRX/NXT 모집단 병합, child provenance 삭제, sample floor 임의 하향, hard-safety·broker guard·threshold 완화, OFF/은퇴 family 재활성화를 하지 않는다.
5. submit drought는 upstream 후보 수가 많다는 이유만으로 시간 해결형이 아니다. `budget/latency/price/broker receipt` 등 최초 0-conversion 축을 확인하고, 정상적인 희소 도착인지 동일 guard·hook에서 반복 소멸하는 구조적 funnel 고갈인지 분리한다. 유효 floor와 source quality로 `SUBMIT_DROUGHT_CRITICAL|SWING_ENTRY_DROUGHT_CRITICAL`이 발행됐으면 단순 wait로 닫지 않고 구조적 병목 조사를 강제한다. BUY Funnel Sentinel 또는 Swing improvement source에서 LDM submit attribution·lifecycle bucket discovery, source-only code-improvement workorder와 postclose verifier까지의 필수 handoff를 확인하며 `runtime_effect=false`, `allowed_runtime_apply=false`, broker/order/provider/bot/threshold 권한 없음 상태를 유지한다. 정당한 hard-safety 차단이 원인이면 safety를 완화하지 않고 `structural_by_design_safety_exclusion`, 비승격·재설계·reject로 닫는다.

오탐 방지를 위해 반복된 `implemented_but_hold_sample`, quiet-gap rollup, `no_current_signal`, negative-EV `hold_no_edge`, 단 한 번의 정상 safety-guard 차단을 그 자체로 구조적 고갈로 승격하지 않는다. child combo 하나의 모집단만 고갈되고 canonical parent가 floor·EV를 충족하면 child scope의 진단·exclusion 후보로만 남기고 전체 parent/family 고갈로 확대하지 않는다. 새 postclose 후보의 next PREOPEN이 아직 오지 않았거나 fixed maturity deadline 전인 row도 구조적 고갈이 아니다.

상태 전이는 `blocked_missing_evidence → pending_declared_window|time_resolvable_shortage|structural_population_exhaustion|N/A_by_contract`, `pending_declared_window → time_resolvable_shortage|structural_population_exhaustion|blocked_missing_evidence|N/A_by_contract`, `time_resolvable_shortage → resolved|structural_population_exhaustion`, `structural_population_exhaustion → collecting_after_structural_repair → time_resolvable_shortage|resolved`로 추적한다. `pending_declared_window`는 earliest review date에 반드시 재판정하며 근거 없이 다음 창으로 미루지 않는다. 구조 보완 코드·report 생성·PREOPEN handoff만으로 `resolved`라고 하지 않는다. `collecting_after_structural_repair`는 review finding 0과 targeted validation, exact producer/consumer receipt가 닫힌 뒤에만 열고, 수정 generation에서 신규 floor-qualified unique 표본이 first depleted stage를 실제 통과해야 다음 상태로 이동한다. `resolved`는 source quality·authority handoff와 exact floor denominator의 sample floor가 함께 충족될 때만 허용한다.

`shortage_id`는 `owner|family/arm/bucket|stage|venue/session|metric_contract_version|window_policy|floor_denominator_key`의 canonical key로 결정하고 target date, generation, source hash가 바뀌어도 같은 부족이면 유지한다. 최종 `shortage_ledger`의 각 row에는 최소 `shortage_id`, `canonical_source_state`, owner/family/stage/venue/session, decision authority와 intended last consumer, metric contract/version, shortage metric/floor denominator·unit·dedup key, required/current/deficit, observed dates와 source-available day ratio, first depleted stage와 funnel counts, window·floor-qualified arrival/expiry rate·maturity backlog·conservative reachable N, `shortage_class`와 classification status/reason code, 판정 근거, ETA 또는 `why_waiting_cannot_resolve`, 보완 owner/artifact/workorder, 다음 due/recheck, reclassification trigger, acceptance test, `runtime_effect`, `allowed_runtime_apply`, `forbidden_uses`를 기록한다. 같은 shortage의 날짜별 row는 stable ID와 source hash로 이어서 분류 변화와 보완 효과를 추적한다.

## 9. Code-improvement workorder 2-pass 처리

사용자가 이 지시문에 따른 장후 점검을 Codex에 요청한 실행에서 authoritative workorder가 terminal이고 `implement_now`를 하나라도 선언하면 이 절의 2-pass는 필수다. 이 요청을 runbook의 “사용자가 Codex 구현을 명시적으로 지시”한 경로로 고정하며, 스케줄된 controller와 runner에 새 자동 권한을 부여하지 않는다. 별도 사용자 재지시, controller `DONE`, 수동 opt-in runner 설정 또는 runner 실행 여부를 면제 근거로 삼지 않는다. 합법적인 skip은 authoritative intake의 `implement_now_total=0`일 때뿐이다. workorder가 `not_yet_due|in_progress`이면 bounded wait하고, 끝내 terminal intake를 못 했으면 2-pass 미완료로 보고하며 튜닝 판정 완료를 선언하지 않는다.

2-pass의 자동 구현 범위는 `decision=implement_now`, `runtime_effect=false`, `allowed_runtime_apply=false`이고 §2가 허용한 calculation/parser/schema/instrumentation/report/provenance/process-liveness/test/documentation/sim/source-only 보완으로 한정한다. 권한 필드가 누락·충돌하거나 구현이 PREOPEN live env, provider/model, bot/process, cap, 실주문, broker/order guard, threshold, hard safety를 바꾸어야 하면 추정 구현하지 않고 `blocked_missing_evidence|user_authority`로 분리한다. 이를 허용 범위의 `implement_now`를 건너뛰는 근거로 사용하지 않는다.

### 9.1 Intake와 snapshot 고정

대상일 machine-readable JSON workorder를 authority로 삼고 Markdown parity를 대조한다. workorder 내 selected/non-selected·source-gap·root-cause follow-up에 퍼져 있는 모든 `implement_now`를 stable `order_id`로 전수 집계해 run evidence ledger의 `implement_now_2pass_ledger`로 만든다. 스키마가 별도 stable native ID를 선언한 항목은 `<source_schema>:<native_id>`를 canonical order ID로 보존하고, stable ID가 전혀 없으면 자체 ID를 추정 생성하지 않고 `invalid_or_missing_authority`로 차단한다. 각 row의 다음 값을 먼저 기록한다.

- `generation_id`, `source_hash`
- selected/non-selected order count와 고유 `order_id`
- `lineage.new_order_ids`, `removed_order_ids`, `decision_changed_order_ids`
- `runtime_effect`, `allowed_runtime_apply`, `target_subsystem`, `lifecycle_stage`
- `root_cause_followup_contract`, acceptance tests, expected EV effect
- source/producer/consumer path, 기존 구현 후보, 예상 수정 파일과 validation owner
- `pass1_status`, `regeneration_status`, `pass2_status`, finding severity, 최종 `implementation_disposition`

`duplicate_order_warnings`가 비어 있고 summary count와 실제 order가 일치해야 한다. 같은 날짜 artifact는 mtime이 아니라 generation ID, source hash와 lineage diff로 구분한다. 다음 intake 보존식을 닫지 못하면 Pass 1을 시작하지 않고 workorder contract defect로 fail-closed한다.

- `all_order_id_total = selected_order_count + non_selected_order_count = source_order_count = 전체 고유 order_id 수`
- `implement_now_total = orders + non_selected_orders에서 decision=implement_now인 고유 order_id 수`; summary가 `implementation_required_count` 또는 동등 count를 선언하면 일치해야 함
- `implement_now_total = eligible_runtime_effect_false_total + user_authority_total + invalid_or_missing_authority_total`
- producer가 선언한 lineage scope를 기록하고, 이전 generation이 있으면 `prior_lineage_scope_total = unchanged_total + removed_total + decision_changed_total`
- 이전 generation이 있으면 `current_lineage_scope_total = unchanged_total + new_total + decision_changed_total`
- first generation은 `prior_lineage_scope_total=0`, `unchanged_total=removed_total=decision_changed_total=0`, `new_total=current_lineage_scope_total`로 기록
- `implement_now_unaccounted_count=0`

이미 구현된 것으로 보이는 order는 코드 존재만으로 닫지 않는다. exact source→producer→consumer, target-date output, acceptance test와 현재 authority 비확대를 재검증한 경우에만 `already_implemented_verified`로 분류한다.

`eligible_actionable_open_count`는 허용 범위의 eligible order 중 `already_implemented_verified|implemented_pass1|implemented_pass2`로 닫히지 않았고, 외부 증거·권한 부족으로 terminal blocked 분류도 되지 않은 현재 구현 가능 항목 수다. blocked row는 이 count에서 빼더라도 별도 blocker count와 severity로 계속 보존한다.

### 9.2 Pass 1

1. intake에서 고정한 `eligible_runtime_effect_false_total` 전수를 순회한다. 각 order를 `already_implemented_verified|implemented_pass1|blocked_missing_evidence|blocked_external_dependency` 중 하나로 닫고 근거 없이 skip하지 않는다.
2. 미구현 order의 calculation/parser/schema/instrumentation/report/provenance/process-liveness/test/documentation/sim/source-only 결함을 target date와 직접 연결된 최소 범위로 구현한다. 목록 순서를 구현 우선순위로 삼아 뒷순위 order를 생략하지 않는다.
3. 실제 raw→producer→모든 consumer→machine input 경로, parser/schema, silent-fail, no-op/orphan process와 authority leak를 함께 검토한다.
4. 관련 targeted test, compile/syntax, parser validation과 `git diff --check`를 실행한다.
5. `$korstockscan-review-gate`에 따라 `review → defect fix → re-review → validation`을 finding 0까지 반복한다.
6. `pass1_eligible_actionable_open_count=0`, `pass1_unaccounted_count=0`을 확인한 뒤에만 재생성 gate로 이동한다. 코드로 닫을 수 없는 blocker는 owner·직접 원인·acceptance test·severity를 가진 상태로 보존하고, P0~P2이면 GREEN/튜닝 판정 완료를 차단한다.

Pass 1 review gate가 닫히기 전 bot 재기동, 비싼 report 재생성, runtime apply를 수행하지 않는다.

### 9.3 Regeneration과 diff

review finding 0과 targeted validation 후 필요한 producer부터 consumer 순서로 관련 report와 workorder만 재생성한다. 변경과 무관한 전체 체인을 습관적으로 재실행하지 않는다. 재생성 전 pre-snapshot과 transaction/publish 계약은 §7.6을 따르며, AI Provider 신규 호출, full-wrapper rerun, runtime apply가 필요하다면 2-pass 구현 권한으로 추정하지 않고 checkpoint 재사용·runbook 권한·user authority를 별도 판정한다.

재생성 후 다음을 비교한다.

- 이전/신규 generation ID와 source hash
- new/removed/decision-changed order ID
- source-quality warning·missing/stale downstream 변화
- EV/calibration/runtime-summary generation 순서
- workorder source fingerprint와 downstream lineage
- verifier와 controller의 최종 판정
- pre/post 각 `order_id`의 `unchanged|new|removed|decision_changed` 분류와 `implement_now_unaccounted_count=0`

중간 producer 실패, publish 미완료, workorder terminal 미도달을 valid-empty나 Pass 2 완료로 정규화하지 않는다. 그 상태에서는 이전 authoritative generation을 유지하고 `regeneration_blocked` 및 acceptance condition을 남긴다.

### 9.4 Pass 2와 final freeze

1. 재생성된 authoritative workorder의 `implement_now` 전수를 다시 intake하고, 기존 각 `order_id`와 `unchanged|new|removed|decision_changed`로 대조한다.
2. `new|decision_changed` 중 `runtime_effect=false`이고 허용 범위인 항목을 전수 구현한다. Pass 1에서 누락된 order가 발견되면 신규 order로 포장하지 않고 `pass1_omission` finding으로 복구한다.
3. 동일 review/fix/re-review/validation loop를 finding 0까지 반복한다.
4. Pass 2 수정이 producer/workorder 판정을 바꾸면 영향 report와 workorder를 다시 생성하고 diff를 재계산한다. 이 최종 재생성에서 또 다른 eligible `new|decision_changed implement_now`가 나오면 Pass 2 내부의 `구현→리뷰→재생성→diff` 루프를 fixed-point까지 반복한다. “2-pass”를 딱 두 번만 보고 신규 order를 남기는 면제로 해석하지 않는다.
5. 최신 두 generation 사이에 eligible `new|decision_changed implement_now=0`, `final_eligible_actionable_open_count=0`, `implement_now_unaccounted_count=0`, review finding 0이 모두 확인될 때 fixed-point로 판정한다.
6. 최종 generation ID와 source hash를 고정하고 `already_implemented_verified`, `implemented_pass1`, `implemented_pass2`, `blocked_missing_evidence`, `blocked_external_dependency`, `user_authority`, `removed|superseded`를 분리한다.

최종 ledger에서 다음 보존식을 모두 닫는다.

- `final_eligible_runtime_effect_false_total = already_implemented_verified_total + implemented_pass1_total + implemented_pass2_total + blocked_missing_evidence_total + blocked_external_dependency_total`
- `final_implement_now_total = final_eligible_runtime_effect_false_total + user_authority_total + invalid_or_missing_authority_total`
- `final_eligible_actionable_open_count=0`, `implement_now_unaccounted_count=0`

`blocked_missing_evidence|blocked_external_dependency`는 계상에서 숨기지 않는 것이지 구현 완료가 아니다. 필수 P0~P2 범위에 남으면 튜닝 판정 완료와 GREEN을 차단하고 owner·acceptance condition을 최종 보고에 남긴다.

`runtime_effect=true`, 실주문 권한, provider/bot/cap, broker/order guard, hard safety 또는 PREOPEN live env 변경이 필요한 항목은 구현하지 않고 `user_authority`로 보류한다.

### 9.5 Non-implement 재판정

- `attach_existing_family`: 기존 family report/calibration에 실제 source metric이 나타났는지 확인한다.
- `design_family_candidate`: sample floor, source-quality gate, env mapping, runtime hook, rollback, post-apply attribution이 모두 설계됐는지 확인한다.
- `defer_evidence`: `time_resolvable_shortage`로 입증됐거나 신규 경로의 `pending_declared_window`가 명시한 earliest review date까지인 항목만 사용한다. 새 표본으로 승격됐는지, ETA·예상 유입량을 지켰는지, 구조적 고갈로 재분류할지, stale로 폐기할지 판정하며 단순한 반복 `hold_sample`만으로 구조적 승격하지 않는다.
- `structural_population_exhaustion`: 최초 고갈 stage와 최소 source/instrumentation/sim 보완이 명확하면 `implement_now|attach_existing_family|design_family_candidate`로 보내고, 안전 우회나 폐기축 부활만 가능한 경우 `reject`, 권한 변경이 필요하면 `user_authority`로 보류한다.
- `reject`: safety 우회, 폐기축 부활, fallback/shadow 재개 요구는 사유와 함께 유지한다.

eligible `implement_now` 항목을 2-pass에서 제외하기 위해 `defer_evidence|attach_existing_family|design_family_candidate|reject`로 임의 재분류하지 않는다. non-implement 전환은 source hash가 바뀐 authoritative workorder의 명시적 decision change와 직접 근거·acceptance contract가 있을 때만 인정한다.

최근 10일 창에서 3회 이상 반복되고 downstream closure가 계속 필요한 구조적 항목은 `repeat_unresolved_structural_blocker`로 재분류해 root cause, 장기 미해결 이유, 최소 안전 보완, 새 evidence requirement와 acceptance test를 다시 확인한다. 명백한 impossible predicate, key/hook 단절 또는 ETA 초과는 3회 반복을 기다리지 않고 즉시 구조적 고갈로 판정한다. 설계상 visibility만 유지하는 rollup은 `keep_visible_by_design`으로 분리한다.

## 10. 코드·문서 보완 검증

코드 또는 자동화 파일을 변경했다면 최소 다음을 수행한다.

```bash
PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>
PYTHONPATH=. .venv/bin/python -m compileall -q <변경 Python 경로>
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
git diff --check
```

wrapper·cron·threshold/postclose 체인을 변경했다면 관련 shell syntax와 postclose/preopen targeted tests를 추가한다. Kiwoom REST/WS 요청·parser·FID·주문·계좌 코드를 변경할 때는 현재 공식 Kiwoom reference revision과 관련 upstream path를 먼저 확인하고 SHA·조회 시각을 review evidence에 남긴다.

문서/checklist parser validation은 AI가 수행한다. GitHub Project와 Google Calendar sync는 직접 실행하지 않는다.

## 11. 최종 완료 조건

다음을 모두 충족해야 장후 튜닝결과 점검을 완료로 보고한다.

1. EOD는 `completed|completed_with_warnings`의 failed/warning step 의미와 latest `[DONE]`가 확인됐고, main postclose는 대상일 `succeeded`와 latest `[DONE]`가 확인됐다.
2. final verifier가 pass이거나, 허용 warning의 영향과 blocker가 명시됐다.
3. controller JSON이 `done`이고 root cause/recovery action이 실제 artifact와 일치하며, controller wrapper의 대상일 latest `[DONE]`과 due follower terminal 상태가 확인됐다.
4. source-quality gate와 clean-baseline 범위가 확인됐다.
5. 필수 AI 경로의 provider가 `none`이 아니며 parsed/schema/receipt 계약이 닫혔다.
6. main/widget/episode owner와 real/sim/source-only, completed/HELD가 분리됐다.
7. 고정 seed/stable-hash 층화 sample manifest의 row 독립 재계산, synthetic/golden/metamorphic 경계 테스트와 전체 count/key/notional/numerator/denominator/exclusion 보존식으로 각 owner/artifact의 `window_policy`가 선언한 applicable daily·rolling·MTD·cumulative 계산, 비용·표본·tail risk가 검증됐다. 미선언 window는 N/A이고 계약상 required window 누락만 blocker다.
8. 검증 coverage 안에서 AI 판단품질과 micro-reversion의 exact input, join, label, cost, first-hit, aggregation 결과에 leakage·중복·단위·시간·venue 오류가 없다.
9. 대상일 applied main runtime, widget exact policy와 episode exact profile이 실제 process/state/ledger에 정확히 소비됐고 미호출·old policy·fallback을 정상 효과와 분리했다. 대상일 장후 생성된 다음-session artifact는 authority별 intended last consumer·schema/hash·loader dry-validation·PREOPEN handoff까지만 확인했으며, 다음 거래일 실제 PID load·자연 호출·post-apply를 다음 checklist OPEN acceptance로 남겼다.
10. runtime/bridge 후보의 실제 sim 적용과 real 반영 blocker가 구분됐다.
11. authoritative workorder의 `implement_now` 전수 intake와 2-pass ledger가 존재한다. `implement_now_total=0`이 아니면 Pass 1→ordered regeneration→Pass 2 fixed-point가 필수로 실행됐고, pre/post `order_id` diff·generation/source hash/lineage 보존식·review finding 0·targeted validation이 닫혔으며 `final_eligible_actionable_open_count=0`, `implement_now_unaccounted_count=0`이다. `not_yet_due|in_progress`, 미생성 workorder, 코드로 닫을 수 없는 P0~P2 blocker는 2-pass skip 사유가 아니며 튜닝 판정 완료를 차단한다.
12. tuning monitoring, 20:10 widget evaluation, 21:15 machine final refresh와 paired replay가 due인 경우 각 owner의 terminal 상태와 authority가 확인됐다.
13. 20:50 archive, 21:00 log rotation/cleanup과 21:55 detector final window가 terminal이며 미검증 원본을 손상하지 않았다.
14. authoritative expected set의 process 전체가 근거 있는 liveness/meaningfulness 분류를 가졌고 unexplained dead·hung·duplicate·no-op·orphan·unconsumed process가 없다.
15. 미해결 항목마다 owner, 직접 원인, 영향, 다음 보완과 acceptance test가 있다.
16. 무단 runtime·주문·provider·bot·cap·safety 변경이나 불필요한 재기동이 없었다.
17. “오류 없음”은 위 sample manifest·전수 보존식·targeted test가 검증한 coverage 안에서만 선언했고, 미표본 strata·결손 source·외부 broker/provider 불확실성과 다음 거래일 acceptance를 잔여 위험으로 명시했다.
18. multi-artifact를 재생성했다면 pre/post snapshot, transaction manifest/pointer의 atomic publish 또는 동등한 consumer quiescence/lock, consumer pinned-generation receipt와 mixed-generation census 0이 확인됐다. 실패 시 결함 영향 밖의 이전 generation만 유지됐고, known-bad generation은 consumer reference 0건 또는 명시적 blocked receipt와 함께 audit-only로 격리됐다.
19. 모든 표본·모집단 부족 후보가 deterministic stable `shortage_id`로 전수 집계됐고 `classified_shortage_total = time_resolvable_shortage_count + structural_population_exhaustion_count`, `shortage_candidate_total = classified_shortage_total + blocked_missing_evidence_count + pending_declared_window_count` 두 보존식이 실제 ledger row와 일치한다. `N/A_by_contract` census는 부족 후보 합계 밖에 별도로 보존됐다. 시간 해결형은 exact floor denominator와 rolling expiry를 반영한 conservative reachable N·finite ETA·다음 due·재분류 trigger, 구조적 고갈형은 first depleted stage·보완 owner·acceptance test를 가지며 blind wait 상태가 없다.

## 12. 최종 보고 형식

각 항목은 `판정 → 근거 → 다음 액션` 순서로 작성한다.

Tuning Chain Control State는 다음처럼 사용한다.

- `GREEN`: 필수 체인과 후행 process가 terminal이고 계산·consumer lineage 및 source quality에 hard blocker가 없으며 허용 warning의 영향과 다음 관찰이 명확하다.
- `YELLOW`: controller wrapper는 완료됐지만 표본·source readiness·handoff·post-apply attribution 또는 비권한 process warning과 후속 관찰이 남아 있다.
- `RED`: 필수 artifact/lineage/provider receipt가 없거나 계산 오류, consumer 오입력, expected process death/hang, verifier/controller fail·blocked가 안전하게 닫히지 않았다.

shortage class 하나만으로 색을 자동 결정하지 않는다. 수집 경로와 finite ETA가 검증된 `time_resolvable_shortage`는 후속 관찰이 남은 `YELLOW` 근거가 될 수 있다. source-only 범위에서 fail-closed되고 구조 보완 owner가 지정된 `structural_population_exhaustion`도 영향에 따라 `YELLOW`일 수 있지만, 필수 입력·consumer를 고갈시켰거나 잘못된 정상 판정을 만들었거나 보완·차단이 없는 경우는 `RED`다. 필수 scope에 unresolved structural shortage 또는 `blocked_missing_evidence|pending_declared_window`가 남으면 `GREEN`으로 판정하지 않는다.

허용 범위의 `runtime_effect=false implement_now`가 actionable/open으로 남았거나 `implement_now_unaccounted_count>0`이면 shortage class와 무관하게 `GREEN`을 금지하고 2-pass 미완료로 보고한다. 그 누락이 잘못된 machine input, source-quality pass, verifier/controller pass를 만들었으면 `RED`, 영향 scope가 source-only로 fail-closed되고 owner·acceptance·due가 명시된 외부 blocker라면 최대 `YELLOW`로 한정한다.

마지막에는 반드시 다음을 분리한다.

- Tuning Chain Control State: `GREEN|YELLOW|RED`, 막힌 단계, 영향, 조치
- 자동화체인: EOD, postclose wrapper, verifier, controller JSON/wrapper, 후행 작업 terminal 상태
- source quality: pass/block/warning, clean-baseline·venue·owner·lineage 결손
- 부족 분류 ledger: `시간이 해결하는 부족` 표와 `구조적으로 모집단이 고갈되는 부족` 표를 분리하고, stable `shortage_id`별 shortage metric/floor denominator·required/current/deficit·intended last consumer·first depleted stage·funnel count, floor-qualified arrival·expiry rate·conservative reachable N·ETA 또는 대기로 해소 불가능한 이유, 보완 owner·due·재분류 trigger·acceptance test를 기록한다. `blocked_missing_evidence|pending_declared_window|N/A_by_contract`는 두 표의 합계에 섞지 않고 별도 예외 표로 제시한다.
- 계산 정확성: raw→parser→join→label→cost→aggregation→candidate 재계산, deterministic strata sample manifest, 전수 보존식, rounding/tolerance, golden/metamorphic test와 count/hash/JSON·Markdown parity
- process 감사: authoritative expected-set source와 systemd MainPID/cgroup/lock/heartbeat 근거, dead/hung/duplicate/no-op/orphan/unconsumed 판정과 오탐 제외
- 메인 봇: lifecycle별 기회·차단·제출·체결·보유·청산과 비용 차감 EV
- 위젯: exact input/policy/process 소비, signal/episode/fill/target/terminal, completed EV와 custody
- 에피소드: exact profile/process 소비, profile/leg별 submit/fill/target/COMPLETE/HELD/BLOCKED와 실현비용
- micro-reversion: sequence/epoch·executable BBO·0B/0D join, fill feasibility, target/adverse first-hit, 비용·tail loss와 source-only authority
- AI: exact payload/prompt/label lineage, 호출·입력·판단 품질, provider/parse/schema/receipt, R0→R3·paired replay 상태
- smoothing: whipsaw 감소와 진입·청산 지연·이익반납 trade-off
- runtime/handoff: 대상일 applied input 실제 소비와 장후 생성 next-session artifact의 authority별 intended last consumer를 분리하고, R0→R6 sim 경로와 main/widget/episode 독립 handoff, 다음 거래일 OPEN acceptance, real runtime remaining blocker와 post-apply attribution
- workorder 2-pass: intake/final generation ID·source hash, `implement_now_total`, eligible/user-authority/invalid 전수, stable `order_id` pre/post diff, `already_implemented_verified|implemented_pass1|implemented_pass2|blocked|removed` disposition, Pass 1/Pass 2 validation, fixed-point 근거, `final_eligible_actionable_open_count`, `implement_now_unaccounted_count`, non-implement 재판정
- 재생성: 수정 전/후 result·generation·source fingerprint diff, 해결된 오류와 남은 blocker
- 장기 미해결: shortage class의 날짜별 변화, 반복 횟수, root cause, 기존 wait/보완 시도 실패 이유, 새 처리방안과 acceptance test

report 이름이나 `DONE` marker의 존재만으로 효과를 주장하지 않는다. 최종 정상 효과는 `source quality → owner/stage 식별 → policy/runtime 소비 → executable order/terminal outcome → 비용 차감 rolling/cumulative EV → post-apply attribution`이 연결됐을 때만 인정한다. 장후 생성된 다음-session artifact에는 아직 이 효과를 주장하지 않고, handoff 완료와 다음 거래일 acceptance OPEN을 분리 보고한다.
