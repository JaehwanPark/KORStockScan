# 장후작업 실행 모니터링·장애복구·추천구현 지시문

작성 기준: `2026-09-04 KST`

이 지시문의 목적은 장후작업이 실행되는 동안 상태를 계속 확인하고, `FAIL`, timeout, hang, 필수 산출물 누락 또는 handoff 단절이 발생하면 최초 원인을 찾아 안전한 범위에서 수정·검증·최소 재실행하여 대상 거래일 작업을 정상 terminal 상태로 닫는 것이다.

운영 체인이 정상화된 뒤에는 같은 generation의 authoritative `implement_now`와 위젯·에피소드 매매기계의 구현 추천을 전수 intake한다. 허용 범위의 항목은 `Pass 1 구현 → review/fix → 영향 산출물 재생성 → Pass 2 재판정·추가 구현`을 fixed-point까지 반복한다.

사용자가 이 지시문에 따라 장후작업을 모니터링하라고 요청하면 위 허용 범위의 2-pass 구현도 함께 지시한 것으로 본다. 별도의 구현 재지시를 기다리지 않는다.

상세 EV 연구, 전략별 장기성과 재평가와 모든 report의 계산 재현은 기본 범위가 아니다. 장애 원인 또는 추천의 구현 가능성·권한을 판정하는 데 필요한 근거만 확인하고, 사용자가 별도 성과 분석을 요청했을 때 확장한다.

튜닝 원칙과 현재 owner는 `docs/plan-korStockScanPerformanceOptimization.rebase.md` §1~§8, 당일 실행 항목은 `docs/checklists/YYYY-MM-DD-stage2-todo-checklist.md`, 실행·복구 권한은 `docs/time-based-operations-runbook.md`, producer/consumer 순서는 `docs/report-based-automation-traceability.md`를 따른다.

## 1. 완료 목표

다음을 모두 충족하면 장후작업과 허용된 추천 구현이 완료된 것으로 판정한다.

1. 대상 거래일이 모든 wrapper, status artifact와 후행 작업에서 동일하다.
2. due인 필수 작업이 `not_yet_due`, `waiting`, `running`, `recovering`, `done`, `failed` 중 하나로 설명되며 상태 미상의 작업이 없다.
3. 필수 producer가 최신 `[DONE]` 또는 성공 status artifact로 종료되고, 실패 후 복구한 경우 이전 FAIL보다 최신인 성공 근거가 있다.
4. main postclose verifier가 terminal이고 필수 artifact, predecessor와 downstream link 결손이 없다.
5. DONE controller JSON과 controller wrapper가 모두 terminal이며, due인 AI entry replay follower도 terminal이다.
6. tuning monitoring, dashboard archive, 20:10 widget evaluation, 21:15 machine final refresh가 각각 성공했거나 명시적으로 OFF인 근거가 있다.
7. 21:55 finalization이 선행 작업을 확인한 뒤 cleanup과 final error detector까지 완료한다.
8. unresolved `FAIL`, timeout, hang, 중복 실행, 실제 점유 중인 stale lock 또는 필수 후행 누락이 없다.
9. authoritative `implement_now`와 위젯·에피소드 추천 전수가 stable ID로 분류되고 누락이 없다.
10. 허용된 구현 항목은 Pass 1과 Pass 2 fixed-point, review finding 0, targeted validation과 영향 산출물 재생성까지 닫힌다.
11. 권한 밖 추천은 구현하지 않고 `user_authority`와 필요한 승인 근거를 명시한다.

source-only 자연 표본 부족이나 전략 후보 0건은 작업 실패가 아니다. 반대로 process 종료 코드가 0이어도 필수 artifact가 없거나 target date가 다르면 정상 종료로 보지 않는다.

## 2. 권한 경계

### 2.1 허용 범위

- 로그, process, lock, status JSON, systemd 상태와 artifact freshness의 읽기 전용 점검
- 실패한 report/source-quality/parser/schema/instrumentation/automation wrapper의 최소 코드 보완
- 문서·테스트·오류 detector contract 보완
- `runtime_effect=false`, `allowed_runtime_apply=false`인 `implement_now` 코드 보완
- 위젯·에피소드 추천 중 source collection, parser/schema, report, instrumentation, test, source-only candidate 생성과 자동화 handoff 보완
- 수정 후 관련 producer와 필수 downstream만 순서대로 재실행
- 명백히 중복되거나 멈춘 장후 분석 worker의 증거를 보존한 뒤 해당 장후 worker만 종료·재실행
- 기존 승인된 exact-date PREOPEN 자동 적용 계약의 candidate/policy/handoff 생성 복구. 수동 env 작성은 금지한다.

### 2.2 금지 범위

- 매매 bot, 위젯 매매 process 또는 에피소드 매매 process의 기동·종료·재기동
- PREOPEN/live runtime env, operator lock, threshold, provider/model/route의 수동 변경
- 실주문·취소, 주문가격·수량·cap·cooldown, broker/account/order guard 변경
- stale/conflict, price freshness, hard/protect/emergency safety 완화
- source-only·sim 결과의 실주문 권한 전환
- 추천 artifact 없이 위젯 종목·machine profile·target·진입조건을 임의 변경
- API 제한을 피하기 위한 호출량·retry 횟수·동시성 상향

금지영역이 실패 원인 또는 추천 구현조건이면 변경하지 않고 `user_authority` 또는 `external_dependency`로 보고한다. 이미 실행 중인 main wrapper는 P0 안전사고가 아닌 한 중단하지 않으며, 실행 시작 시의 immutable wrapper snapshot을 그 run의 계약으로 본다.

## 3. 현재 장후 실행 owner

설치된 cron과 systemd `ExecStart`를 매 실행 시작 시 다시 확인한다. 아래 표와 실제 설치 상태가 다르면 한쪽을 임의로 정상으로 간주하지 않고 `contract_drift`로 분류한다.

| 시각 | 필수 owner | 정상 terminal 근거 |
| --- | --- | --- |
| `20:05` | KOSPI EOD update | `update_kospi` status와 log의 대상일 최신 DONE |
| `20:10` | main threshold-cycle postclose | postclose status `succeeded`, 최신 wrapper DONE, final verifier terminal |
| `20:10` | postclose DONE controller | controller JSON `done`과 controller cron log 최신 DONE |
| `20:10` | tuning monitoring | status `success`, 단계별 exit code 0, 최신 DONE |
| `20:10` | widget evaluation systemd service | unit `Result=success`; 네 producer가 같은 completed target date 사용 |
| `20:50` | dashboard DB archive | 대상일 최신 DONE |
| `21:05` | AI entry setup paired replay | 날짜별 batch terminal과 consumer terminal 또는 reviewed disabled |
| `21:15` | machine final refresh systemd service | expansion, attribution, weakness hysteresis, entry timing, approval, checklist 결과와 unit `Result=success` |
| `21:55` | postclose finalization | predecessor ready, cleanup DONE, final detector DONE |
| `21:50`까지 및 finalization 후 | System Error Detector | 대상일 canonical run이 unresolved critical 없이 terminal |

NXT 구간의 opportunity census, BUY/HOLD sentinels, rising-missed, pyramid, websocket freshness와 system metric sampler는 main postclose의 입력 owner다. 이 작업의 오류가 main source-quality 또는 verifier 실패로 이어질 때 장애복구 범위에 포함한다.

Swing은 설치된 main postclose cron의 `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false`이면 정상 OFF다. 20:10 main wrapper 안의 machine microstructure/timing/approval 사본은 21:15 systemd가 단일 owner이면 정상 OFF다. OFF·retired 단계를 누락 또는 실패로 세지 않는다.

## 4. 모니터링 시작

대상 거래일은 처음 한 번 정하고 자정이 지나도 바꾸지 않는다.

```bash
cd /home/ubuntu/KORStockScan
TARGET_DATE="YYYY-MM-DD"

git status --short
crontab -l
systemctl list-timers --all --no-pager | rg 'korstockscan|widget|machine|postclose'
systemctl list-units --type=service --all --no-pager | rg 'korstockscan|widget|machine|postclose'
ps -eo pid,ppid,lstart,stat,etime,%cpu,%mem,cmd --sort=pid | rg 'run_threshold_cycle_postclose|postclose_done|tuning_monitoring|widget|machine_microstructure|ai_entry_setup|postclose_finalization'
lslocks -o COMMAND,PID,TYPE,MODE,PATH | rg 'KORStockScan|COMMAND'
```

다음 로그와 status artifact를 우선 확인한다.

```bash
tail -n 240 logs/update_kospi.log
tail -n 360 logs/threshold_cycle_postclose_cron.log
tail -n 240 logs/postclose_done_controller_cron.log
tail -n 240 logs/tuning_monitoring_postclose_cron.log
tail -n 200 logs/ai_entry_setup_paired_replay_postclose.log
tail -n 200 logs/dashboard_db_archive_cron.log
tail -n 200 logs/postclose_finalization_cron.log
tail -n 240 logs/run_error_detection_cron.log

jq . "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_${TARGET_DATE}.status.json"
jq . "data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_${TARGET_DATE}.json"
jq . "data/report/postclose_done_controller/postclose_done_controller_${TARGET_DATE}.json"
jq . "data/report/tuning_monitoring/status/tuning_monitoring_postclose_${TARGET_DATE}.json"
```

파일이 없으면 예정 시각과 process부터 확인한다. 실행시각 전이면 `not_yet_due`, predecessor를 정상 대기 중이면 `waiting`이며 실패로 처리하지 않는다.

## 5. 상태 판정과 지속 모니터링

| 상태 | 판정 기준 | 조치 |
| --- | --- | --- |
| `not_yet_due` | 예정 시각 전 | 기다림 |
| `waiting` | 정상 predecessor/resource/artifact bounded wait marker 존재 | wait 이유와 deadline 기록 |
| `running` | PID가 있고 stage/log/artifact 중 하나가 계속 전진 | 계속 감시 |
| `stalled_suspected` | 진행 marker와 artifact가 장시간 정지하고 CPU/I/O/child 변화도 없음 | process·lock·resource 증거 추가 수집 |
| `failed` | 최신 terminal marker가 FAIL, non-zero exit, invalid/missing 필수 artifact | 최초 실패 단계 격리 |
| `recovering` | controller, systemd restart 또는 승인된 최소 재실행 진행 중 | 원 run과 recovery run을 구분해 감시 |
| `done_warning` | terminal 성공이나 허용 source-only warning 존재 | warning 영향과 비권한성 확인 |
| `done` | 필수 terminal·artifact·후행 계약 모두 충족 | 다음 owner로 진행 |

단순 elapsed time만으로 hang을 선언하지 않는다. 다음을 함께 확인한다.

- latest stage marker와 최근 log mtime
- output artifact 또는 checkpoint의 size/mtime 증가
- PID/child PID, process state, CPU·memory·I/O 변화
- system metric sampler의 memory, swap, load, I/O wait
- resource guard·availability guard·artifact wait의 현재 사유와 bounded deadline
- 동일 target date producer의 중복 PID 여부

진행 근거가 있으면 기다린다. 진행 근거가 없고 동일 stage가 반복 timeout하거나 bounded deadline을 넘겼을 때만 실패 또는 hang으로 확정한다.

모니터링 중에는 사용자에게 상태가 변할 때마다 간단히 알린다. 장시간 같은 상태가 계속되면 최대 60초 간격으로 현재 단계, 대기 사유와 다음 확인 조건을 공유한다.

## 6. 실패 대응

실패가 확인되면 다음 순서를 바꾸지 않는다.

`최신 run 확정 → 최초 실패 단계 확인 → 원본 증거 보존 → 원인 분류 → 최소 보완 → review gate → targeted validation → 영향 producer부터 최소 재실행 → verifier/controller/finalization 재확인`

### 6.1 원인 분류

| 원인 | 예 | 기본 대응 |
| --- | --- | --- |
| 정상 선행 대기 | EOD, main DONE, outcome label 대기 | deadline까지 감시; 중복 실행 금지 |
| 일시적 resource pressure | memory/swap/I/O guard 대기 | sampler와 resource 회복 확인; guard 완화 금지 |
| 외부 API rate limit | Kiwoom shared-read defer, HTTP 429 | 기존 bounded retry/cooldown 유지; 호출량 상향 금지 |
| source late/missing | outcome label 또는 exact-date source 미도착 | source owner와 ETA 확인; 없는 값을 합성하지 않음 |
| deterministic code defect | traceback, parser/schema 오류, 잘못된 경로·날짜 | 최소 코드 수정 후 review gate 수행 |
| artifact contract defect | JSON invalid, target date/hash 불일치, downstream missing | producer 수정 후 영향 consumer만 재생성 |
| stale 또는 실제 점유 lock | PID 종료 뒤 lock 점유, 중복 worker | `lslocks`와 PID 확인 후 소유 process 기준 처리 |
| systemd timeout/hang | widget/machine unit timeout | journal과 child tree 보존, 원인 수정 후 해당 service 1회 재실행 |
| 권한 밖 변경 필요 | provider, bot, threshold, order guard | 변경하지 않고 `user_authority`로 보고 |

### 6.2 Lock 처리

`.lock` 파일 존재만으로 stale lock이라고 판단하지 않는다. 반드시 `lslocks`, PID와 process start time을 확인한다.

- 실제 점유가 없으면 lock marker 파일은 그대로 둔다.
- 실행 중인 정상 owner가 점유하면 기다린다.
- 중복 owner가 있으면 target date와 시작시각을 비교해 authoritative run을 하나만 남긴다.
- lock 파일 삭제로 문제를 우회하지 않는다.
- `run_with_owned_log.sh`의 lock은 로그 회전 보호이며 main wrapper 전체 실행 mutex가 아님을 전제로 중복 PID를 별도로 확인한다.

### 6.3 코드 보완과 review gate

장후 실패 또는 추천을 구현해 코드·wrapper·문서를 수정할 때는 `$korstockscan-review-gate`를 적용한다.

1. 현재 worktree의 사용자 변경을 확인하고 관련 없는 변경을 건드리지 않는다.
2. 실패 producer 또는 recommendation owner, 직접 consumer, wrapper, verifier와 테스트를 함께 검토한다.
3. 최초 원인을 고치는 최소 수정만 한다.
4. `review → finding 수정 → 재리뷰 → targeted validation`을 unresolved finding 0까지 반복한다.
5. Python 변경은 관련 pytest와 compile 검사를, shell 변경은 `bash -n`과 관련 wrapper 테스트를 수행한다.
6. 항상 `git diff --check`를 수행한다.
7. 문서를 수정했으면 다음 parser validation을 수행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

GitHub Project와 Google Calendar sync는 실행하지 않는다.

### 6.4 최소 재실행

- 동일 target date 작업이 실행 중이면 중복 실행하지 않는다.
- controller 또는 systemd의 기존 bounded retry가 진행 중이면 그 결과를 먼저 기다린다.
- 수정과 무관한 성공 단계를 다시 실행하지 않는다.
- 실패 producer부터 그 결과를 소비하는 downstream까지만 순서대로 재실행한다.
- 생성된 artifact의 target date, status, source hash/fingerprint와 completion time을 재확인한다.
- main wrapper 전체 재실행은 controller/runbook이 허용하고 부분 재생성으로 닫을 수 없을 때만 사용한다.
- AI Provider 호출은 검증된 checkpoint를 재사용하고 실패 request만 bounded retry한다.
- 자정 이후 recovery도 최초 `TARGET_DATE`를 유지한다.
- postclose worker 재실행 전 기존 PID와 실제 lock 점유가 0인지 확인한다.

## 7. Implement-now 및 위젯·에피소드 추천 2-pass 구현

운영 체인이 terminal이 되고 authoritative generation이 고정된 뒤 수행한다. 진행 중인 wrapper가 읽고 있는 코드나 산출물을 중간에 교체하지 않는다.

### 7.1 Intake

다음 source에서 구현 지시를 수집한다.

- `data/report/code_improvement_workorder/code_improvement_workorder_TARGET_DATE.json`
- `docs/code-improvement-workorders/code_improvement_workorder_TARGET_DATE.md`
- `data/report/widget_collector_expansion_recommendation/`
- `data/report/widget_symbol_signal_policy_research/`
- `data/report/widget_symbol_runtime_policy_apply/`
- `data/report/samsung_machine_entry_tuning/`
- `data/report/low_price_two_leg_tuning/`
- `data/report/low_price_two_leg_expanded_candidate_research/`
- `data/report/machine_microstructure_attribution/`
- `data/report/machine_entry_timing_tuning/`
- `data/report/machine_microstructure_policy_approval/`
- 대상일 verifier, runtime apply-gap audit와 다음 checklist의 직접 handoff

각 항목에 authoritative producer가 발급한 stable `order_id` 또는 `recommendation_id`가 있으면 그대로 사용한다. stable native ID가 없으면 자체 ID를 만들거나 추정 구현하지 않고 `invalid_or_missing_authority`로 차단한다. 다음 필드를 ledger에 기록한다.

| 필드 | 내용 |
| --- | --- |
| ID | stable order/recommendation ID |
| owner | main, widget symbol, Samsung machine, low-price machine 또는 공통 automation owner |
| source | artifact path, target date, generation/hash |
| decision | `implement_now`, `already_implemented`, `observe`, `defer`, `reject` |
| authority | `runtime_effect`, `allowed_runtime_apply`, order/provider/bot/safety 영향 |
| reason | 직접 결함 또는 기대 개선점 |
| consumer | 수정 결과를 소비해야 하는 마지막 artifact/wrapper |
| acceptance | 테스트, report 상태와 handoff 완료조건 |
| final disposition | `already_implemented_verified`, `implemented_pass1`, `implemented_pass2`, `blocked_missing_evidence`, `blocked_external_dependency`, `user_authority`, `invalid_or_missing_authority`, `removed_or_superseded` |

추천 문장만 있고 구현 위치·consumer·acceptance가 없으면 추정 구현하지 않고 `blocked_missing_evidence`로 둔다. 권한 필드가 없으면 직접 producer/schema에서 비권한 계약을 확인하며, 거기에도 없으면 `invalid_or_missing_authority`로 둔다.

Pass 1을 시작하기 전에 authoritative generation의 전수보존을 다음 식으로 검증한다.

- `implement_now_total = eligible_runtime_effect_false_total + user_authority_total + invalid_or_missing_authority_total`
- `final_eligible_runtime_effect_false_total = already_implemented_verified + implemented_pass1 + implemented_pass2 + blocked_missing_evidence + blocked_external_dependency`
- `implement_now_unaccounted_count = 0`

첫 번째 식 또는 ID 유일성 검사가 실패하면 `intake_contract_defect`로 판정하고 Pass 1 구현을 시작하지 않는다. 두 번째 식은 각 pass 종료 시 누적 ledger에 적용하며, 최종 fixed-point에서는 모든 항목의 disposition 합계가 authoritative intake와 일치해야 한다.

### 7.2 구현 가능성 판정

다음은 Pass 1 구현 대상이다.

- `decision=implement_now|code_patch_required`
- artifact 또는 직접 producer contract로 `runtime_effect=false`, `allowed_runtime_apply=false`, 실주문·provider·bot·safety authority 없음이 확인됨
- source-quality, parser/schema, report, instrumentation, test, wrapper, notifier 또는 existing-policy handoff 결함
- 위젯·에피소드 추천 중 기존 owner와 수량·target·safety 계약을 바꾸지 않는 관찰·후보생성·정합성 보완
- 이미 코드가 존재하더라도 producer→consumer→acceptance 근거가 없어 완료로 입증되지 않은 항목

`objective_followup_required`는 구현 위치, intended consumer, acceptance test와 비권한 계약이 artifact에 모두 있을 때만 구현 대상으로 올린다. 단순 정책값 추천, 후보 순위 또는 `observe|keep_collecting`은 코드 구현으로 바꾸지 않고 기존 candidate/policy handoff 상태만 확인한다.

다음은 자동 구현하지 않는다.

- 실주문 authority, 위젯/에피소드 매매 process 재기동, 종목 universe의 실전 확대
- 수량, leg 수, target, entry threshold, cap, provider, broker 또는 hard-safety 변경
- operator lock 해제·변경
- source-only 추천을 수동 live policy나 env로 전환하는 작업

기존 exact-date PREOPEN 자동 policy family의 후보가 정식 guard를 통과한 경우에는 candidate/policy/handoff producer를 복구할 수 있다. 최종 적용은 기존 PREOPEN consumer가 소유하며 수동 env를 작성하지 않는다.

### 7.3 Pass 1

1. authoritative generation의 모든 eligible `implement_now`와 위젯·에피소드 구현 추천을 ID별로 고정한다.
2. `already_implemented`는 관련 코드 존재만으로 닫지 않고 producer·consumer·test 근거로 검증한다.
3. eligible 항목을 누락 없이 구현한다.
4. 항목별로 직접 consumer, silent-fail, target-date, source-quality와 owner 분리를 리뷰한다.
5. `$korstockscan-review-gate`를 finding 0까지 반복한다.
6. targeted test, compile/shell syntax, parser validation과 `git diff --check`를 통과한다.

### 7.4 영향 산출물 재생성

Pass 1 검증 후 수정한 최초 producer부터 intended last consumer까지 필요한 범위만 재생성한다.

- 재생성 전 old generation path/hash/status를 저장한다.
- 중간 producer 실패 시 이전 정상 generation을 덮어쓰지 않는다.
- AI 단계는 valid checkpoint를 재사용한다.
- 위젯과 에피소드 산출물은 main owner와 order/custody를 혼합하지 않는다.
- recommendation candidate 0건은 정상 empty일 수 있으므로 source funnel과 decision reason으로 판정한다.
- 재생성된 workorder, recommendation, verifier와 checklist의 target date와 source hash를 확인한다.
- 새 산출물 때문에 기존 terminal consumer가 stale해지면 verifier → controller → finalization을 해당 target date로 다시 닫는다.

### 7.5 Pass 2와 fixed-point

1. 새 authoritative generation의 `implement_now`와 위젯·에피소드 추천 전수를 다시 intake한다.
2. 각 ID를 `unchanged`, `new`, `removed`, `decision_changed`로 비교한다.
3. `new|decision_changed` 중 eligible한 항목을 구현하고 동일 review/fix/validation을 반복한다.
4. Pass 2 수정이 다시 추천을 만들면 재생성·diff·구현을 반복한다.
5. 다음 조건을 모두 만족할 때 fixed-point다.

- eligible `new|decision_changed implement_now=0`
- `implement_now_unaccounted_count=0`
- `final_eligible_actionable_open_count=0`
- 위젯·에피소드 recommendation 미분류 건수 0
- review P0~P2 finding 0
- targeted validation 통과
- verifier/controller/finalization의 최신 terminal 상태 확인

`blocked_missing_evidence`, `blocked_external_dependency`, `user_authority`, `invalid_or_missing_authority`는 구현 완료가 아니다. owner, 필요한 근거와 acceptance condition을 남기고 최종 상태를 최대 YELLOW로 제한한다.

## 8. Owner별 필수 확인

### 8.1 Main threshold-cycle

- 동일 target date 최신 `[START]`, `[FAIL|DONE]`와 status JSON을 결속한다.
- wrapper 시작 시 immutable snapshot과 pipeline snapshot/checkpoint를 확인한다.
- 현재 stage와 마지막으로 완성된 artifact를 식별한다.
- OFF·retired stage를 실패로 세지 않는다.
- AI 필수 단계는 parsed/receipt 계약을, disabled 단계는 disabled provenance를 확인한다.
- 최종 순서는 `EV/workorder → runtime summary/gap/lineage → checklist → verifier → DONE → final verifier`가 유지돼야 한다.

### 8.2 DONE controller와 AI replay

- controller JSON `done`만으로 끝내지 않고 controller cron log의 최신 DONE을 확인한다.
- fixed 21:05 runner와 controller follower가 날짜별 replay lock으로 중복되지 않았는지 확인한다.
- batch는 `completed_offline_only`, consumer는 terminal path/hash 검증 상태여야 한다.
- 기본 OFF인 Codex workorder runner가 실행되지 않은 것을 실패로 보지 않는다.

### 8.3 Tuning monitoring과 archive

- tuning monitoring은 main postclose DONE을 기다린 후 parquet 3종, verified archive와 shadow diff를 단계별로 확인한다.
- pattern lab이 main wrapper 소유일 때 tuning monitoring의 pattern lab skip은 정상이다.
- 20:50 archive와 tuning monitoring archive가 같은 파일을 처리할 때 검증·원자 publish·skip 계약을 지켜야 한다.
- 미검증 raw를 정상 종료 목적으로 삭제하지 않는다.

### 8.4 Widget evaluation과 추천

- systemd unit의 `ActiveState`, `SubState`, `Result`, `ExecMainStatus`와 journal을 확인한다.
- advisory calibration, auto-trade policy calibration, EOD gate, symbol signal research, runtime policy가 같은 completed target date를 사용해야 한다.
- Kiwoom shared-read budget이 소진되면 빈 source로 성공 처리하거나 API 호출량을 올리지 않는다.
- 종목 확대·signal policy 추천은 exact source, sample floor, source-quality와 기존 owner guard를 확인한다.
- 추천의 source-only 구현은 Pass 1/2에 포함한다. 실전 종목 확대 또는 매매조건 변경은 정식 policy candidate와 PREOPEN guard 없이는 `user_authority`다.
- 수정 또는 source 회복 뒤 evaluation service만 1회 재실행하고 unit `Result=success`와 네 단계 산출물을 확인한다.

### 8.5 Episode machine과 추천

- Samsung과 low-price machine의 profile, episode, leg, order/custody owner를 main/widget과 분리한다.
- 추천 artifact의 target date, source hash, decision, runtime effect와 acceptance test를 확인한다.
- source/parser/report/instrumentation과 candidate handoff 보완은 Pass 1/2에 포함한다.
- 기존 수량·leg·target·validity·safety 계약을 변경하는 추천은 자동 구현하지 않는다.
- exact-date PREOPEN policy candidate는 기존 apply/verify consumer까지 handoff를 검증하되 수동 env로 적용하지 않는다.

### 8.6 Machine final refresh

- 21:15 단계는 `expansion → attribution → weakness hysteresis → entry timing → approval → checklist`다.
- attribution 실패 때문에 weakness/timing이 실행되지 않은 경우 return code 0을 성공으로 해석하지 않는다.
- 각 단계의 return code와 최종 unit `Result`를 함께 본다.
- wrapper의 최종 exit 우선순위는 `checklist builder → policy → weakness hysteresis → entry timing → attribution → expansion`이므로 최종 exit code만으로 최초 실패를 추정하지 않는다.
- source missing, timeout 또는 memory cap이 반복되면 동일 재시도를 반복하지 말고 최초 source/contract/resource 원인을 보완한다.
- attribution/timing/approval의 source-only 구현 추천을 Pass 1/2에 포함한다.
- 보완 후 해당 service만 1회 재실행하고 정책 후보 유무와 관계없이 모든 필수 단계가 terminal인지 확인한다.

### 8.7 Finalization과 error detector

- finalization은 main postclose, controller/follower, tuning monitoring, dashboard archive의 exact-date terminal을 기다린다.
- predecessor fail/timeout이면 cleanup이 실행되지 않아야 한다.
- predecessor가 모두 성공한 뒤 cleanup DONE, finalization DONE, final detector DONE 순서를 확인한다.
- finalization 실패 후 재실행은 선행 owner를 먼저 정상화한 뒤 수행한다.
- error detector의 stale 과거 FAIL보다 최신 recovery DONE이 권위를 갖는지 확인한다.

## 9. 최종 판정과 보고

다음 표를 모두 채운다.

| Owner | Target date | Latest state | First failure | Repair | Validation | Latest terminal |
| --- | --- | --- | --- | --- | --- | --- |
| EOD | | | | | | |
| Main postclose | | | | | | |
| Final verifier | | | | | | |
| DONE controller/follower | | | | | | |
| Tuning monitoring | | | | | | |
| Dashboard archive | | | | | | |
| Widget evaluation | | | | | | |
| Episode recommendations | | | | | | |
| Machine final refresh | | | | | | |
| Finalization/error detector | | | | | | |

최종 상태는 다음처럼 사용한다.

- `GREEN`: 모든 due 필수 owner가 성공 terminal이고, eligible implement-now·추천 fixed-point와 review finding 0까지 닫혔으며 unresolved failure와 실제 점유 stale lock이 없다.
- `YELLOW`: 필수 실행은 정상 terminal이지만 source-only warning, 외부 dependency, user-authority 추천 또는 다음 거래일 관찰이 남아 있다.
- `RED`: 필수 owner가 failed/hung/missing 상태이거나 verifier/controller/finalization이 닫히지 않았거나 허용 범위의 actionable 구현이 누락됐다.

보고는 `판정 → 근거 → 다음 액션` 순서로 간단히 작성한다.

1. `Postclose Control State: GREEN|YELLOW|RED`
2. 대상 거래일과 관찰 종료시각
3. owner별 최신 terminal 상태
4. 발견된 최초 실패와 직접 원인
5. 수정 파일과 수정 내용
6. review finding 및 targeted validation 결과
7. 재실행한 최소 범위와 이전 FAIL보다 최신인 성공 근거
8. implement-now와 위젯·에피소드 추천 Pass 1/2 ledger 및 fixed-point 결과
9. 남은 warning, external dependency 또는 user-authority 항목

작업이 진행 중이면 완료 보고를 하지 않는다. 현재 stage, PID, 마지막 progress 근거, 기다리는 조건과 bounded deadline을 알리고 계속 모니터링한다.
