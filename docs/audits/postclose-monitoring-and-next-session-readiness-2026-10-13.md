# 2026-10-13 EOD 대기 및 장후 모니터링

대상 source 거래일은 `2026-10-13`으로 고정했다. 초기 fingerprint 관측은 `2026-10-13T21:17:21+09:00`, terminal 보완 관측은 `2026-10-13T21:24:04+09:00`, 마지막 detector 확인은 `2026-10-13T21:30:14+09:00`이다. 이후 변할 수 있는 진행 중 상태를 전체 장후 완료로 표시하지 않는다.

운영은 EOD·archive 종결 / **Main wrapper failed·필수 machine stage failed**, 분석은 preflight 경고·기계/보조 비교 미완결, 경제성은 미확정이다. Wrapper의 직접 종료 원인은 초기 수량 연구의 자원 입장 timeout이며, 별도로 machine stage 산출물 계약과 이전 최종화 역사 검증이 차단돼 있다. 기존 운영 지정의 등록·채택과 경제성 비교 완료는 별도 상태다.

## 범위와 실행 세대

- 요청: EOD 완료까지 대기한 후 장후 작업 모니터링. 20:05 예약 전부터 완료까지 실제로 대기하고, 종료 후 로그·status·stage receipt·producer/consumer를 조회했다.
- 조회 기준: [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [현재 체크리스트](../checklists/2026-10-13-stage2-todo-checklist.md), [장후 지침](../postclose-tuning-result-review-task-instructions.md), [활성 목록](../audit-reports/2026-09-05-postclose-work-inventory.md).
- `--check-cron`: `cron_routing_verified=true`, required targets 8. `postclose`·`finalize --print-plan`의 선택 release는 `/home/ubuntu/KORStockScan-runtime-releases/main-rest-reduction-20261013`, commit `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`다. 해당 release의 `src`·`deploy` 변경은 없었다. 공유 data/docs/logs/tmp/.venv 경로는 작업본으로 결속돼 있다.
- Main wrapper run ID: `1f46324c3f4d4598a9a05aa295949abb`; PID `3546399`, start ticks `13914798`, 해당 release cwd와 `.run_threshold_cycle_postclose.snapshot.gL6jP3.sh` 실행을 확인했다. Controller PID `3546582`, tuning wrapper PID `3546403`도 같은 release를 소비한다.
- 매매 프로세스 종료는 설치 cron의 `THRESHOLD_CYCLE_POSTCLOSE_BOT_ACTION=stop`에 따른 자동 owner 동작이었다. 모니터링에서 재기동·선택 release 변경·provider 호출·수동 env/lock/threshold/주문 변경·worker 수리/재실행을 하지 않았다. 이 감사 기록만 추가했다.

## 작업별 관측 결과

| 작업 / owner | 실행·terminal | 분석·직접 소비 / 다음 경계 |
| --- | --- | --- |
| EOD / `update_kospi` | 20:05:05 시작, **20:57:16 `completed_with_warnings`** | DB latest date `2026-10-13`, 대상일 2,622종목, bulk insert 172,858행. 추천 후처리 완료. Main·archive exact-date EOD gate가 동일 결과를 소비했다. |
| Main threshold-cycle | 20:10:01 시작, EOD 대기 2,850초 뒤 계산; **21:18:12 failed, exit 1** | 직접 실패는 `initial_quantity_policy`의 60초 resource admission timeout이다. 앞서 machine stage도 실패했다. 독립 비동기 worker의 후행 성공은 원 wrapper 실패를 대체하지 않는다. |
| Rising-missed feedback / Main 내부 producer | command exit 0, JSON/Markdown ready | 20:57:38 분석 as-of의 결과가 21:04경 게시됐다. `no_actionable_source_rows` 진단이며 실제 수익 또는 모든 기계 판단의 무신호 판정이 아니다. |
| Source-quality preflight / `observation_source_quality_audit` | 출력 `warning`, wrapper가 다음 단계로 진행 | raw 463,969 events, hard-blocking gap/exclusion 0, raw tuning input allowed. 별도의 기계 attempt 보존·current prompt measurement gate는 아래 결손으로 차단돼 있다. Final phase receipt는 아직 미확인이다. |
| `main_machine_policy` | **21:11:29 시작 → 21:11:40 failed, exit 1** | 운영 비교 보고서는 생성됐으나 stage가 구 산출물 목록을 요구해 실패했다. 필수 stage closure·auxiliary prerequisite·summary/strict/controller에 영향. 다음 조치는 아래 blocker 2를 따른다. |
| `main_auxiliary_policy` | stage receipt 미생성 | 같은 run에서 요구하는 선행 `main_machine_policy`가 failed다. 이미 있는 `auxiliary.json`은 stage 성공 영수증을 대신하지 않는다. |
| `outcome_labels` | 21:15:17 시작, resource admission 대기 후 **21:21:23 succeeded, exit 0, issues 0** | 라벨 stage 종결은 확인됐다. 뒤의 full 평가·auxiliary·summary 소비와 원 wrapper 종결은 별도이며 미완결이다. |
| `legacy_machine_report` | stage receipt 미생성 | compatibility full 평가의 실행·정책 선택·consumer 결과는 미확인이다. 보고서 존재만으로 완료하지 않는다. |
| `pre_submit_delay` | 21:12:52 시작 → **21:19:57 succeeded, exit 0, issues 0** | V2 committed report/policy/manifest와 source ledger를 stage가 결속했다. Report는 `initial_baseline_immediate`, receipt disposition은 `incumbent_carry`다. 전체 summary·다음 PID 소비는 별도다. 실제 fill/PnL을 이 quote 연구의 추가 완료 조건으로 요구하지 않는다. |
| `main_stop_confirmation` | stage receipt 미생성 | 기존 conditional owner의 parent carry/연구·committed 결과를 추후 확인해야 한다. 부재를 신규 손절 정책 또는 재기동 권한으로 바꾸지 않는다. |
| Trade fact sync / Main 내부 producer | status `valid_empty` | 동일 대상일 fact-sync 결과가 scale-in census 평가에 전달됐다. Main 기계 판단 전체의 무기회 또는 비용 후 EV 0을 뜻하지 않는다. |
| Scale-in split / Main 내부 producer | report·policy ready, `skipped_no_actual_fill` | actual fill/completed/applicable receipts 0, raw bytes read 0, modeled EV null. 실제 체결 조건부 skip이며 경제성 개선이 아니다. |
| Entry split / Main 내부 producer | wrapper에서 report JSON/Markdown·policy ready 확인 | JSON 539,058,129바이트. 64MiB 조회 경계에 따라 본문 재스캔을 하지 않았다. 경제성·paired 모델·최종 consumer는 미검증이며, 파일 크기를 source missing으로 재분류하지 않는다. |
| Entry cancel-wait / Main 내부 producer | command exit 0, report·policy ready | Census coverage verified, target-date submitted parents 0, `no_submitted_orders`, `incumbent_carried`, economic tuning false, realized profit null. 불확실한 broker 호출/이전 custody를 체결·순익 0으로 바꾸지 않는다. |
| Initial-entry quantity refresh / Main 내부 producer | **command exit 1, wall 60.1425초** | `research_resource_admission_timeout`으로 `_main_impl` 전에 실패했다. 실제 새 수량 연구·정책 생성 또는 소비 성공이 아니며 아래 blocker 1을 따른다. |
| `summary_handoff`·strict / Main 내부 consumer | stage receipt·오늘 verifier 미생성 | failed machine을 포함한 현재 terminal·source hash를 검증해야 한다. 이전 날짜 PASS 또는 prepared component로 대체할 수 없다. |
| DONE controller | 실제 worker 생존·선행 대기, 오늘 JSON 미생성 | 최신 strict와 같은 generation의 `done`은 아직 없다. |
| Tuning monitoring | 오늘 status `running`, 단계 결과 없음; Main 선행 대기 | Parquet/DuckDB/archive의 최종 target/hash/count 소비는 아직 미검증이다. |
| Dashboard archive | **20:57:32 DONE** | 20:50:01 시작 후 EOD 대기 450초, 동일 target/date/2,622 rows gate 통과 뒤 native 종료. wrapper terminal을 확인했으며 archive 내용 전체 재검증·별도 압축 실행은 하지 않았다. |
| Finalization·cleanup·final detector | **10/13 source run은 not_yet_due** | 설치 cron은 **10/14 05:35 KST**다. 지침·활성 목록의 05:00과 불일치하므로 설치 trigger를 기준으로 구분한다. 다음날 준비·PID·실현성과는 아직 확인하지 않았다. |
| System Error Detector | **21:30:14 `fail`** | 오늘 `threshold_cycle_postclose: status artifact failed`와 10/12 source → 10/13 effective의 이전 `strict_checklist_generation_stale`를 각각 확인했다. 이전 오류는 아래 blocker 3을 따른다. |
| Main market-weakness advisory research | 첫 야간 21:40 경계 전 `not_yet_due` | 현재 checklist의 기존 `MainMarketWeaknessPostcloseObservation1008`가 소유한다. WR0–WR5 구현은 계획 범위로 유지하며 새 연구/collector·정책·주문을 실행하지 않았다. |

Episode/widget/독립 IPO와 퇴역 generic Daily/EV/standalone replay는 현재 필수 작업에 포함하지 않았다. 그 산출물 부재에 복구 OPEN을 만들지 않았다.

## 확정 blocker와 closure

### 1. Initial quantity의 60초 자원 입장 대기 실패

직접 근거는 [Main terminal](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_2026-10-13.status.json)과 동일 run ID의 마지막 native command metrics/traceback이다. `src.engine.scalping.initial_quantity_policy` command wall `60.14253849600209`초, exit 1, `_main_impl` 진입 전 `research_admission.direct_job`에서 `research_resource_admission_timeout`이 발생했고 wrapper가 21:18:12에 종료됐다. 이는 앞선 machine stage 실패와 별도 원인이다.

`initial_quantity_policy.main`은 `initial_entry_quantity_refresh`를 `direct_job(..., timeout=60)` 기본값으로 실행한다. 이 stage와 `pre_submit_delay`는 모두 `HEAVY_STAGES`이고 `acquire`가 기존 compute slot 두 개를 함께 예약한다. 해당 direct command의 대기 구간은 21:17경~21:18:12이며 pre-submit stage 실행 21:12:52~21:19:57와 겹친다. Slot 예약을 기다리는 운영 실패이며 실제 provider timeout·수량 모델 실패·경제성 탈락으로 분류하지 않는다.

Owner는 기존 `DirectFamilyPreopenPolicyHandoff` / initial quantity refresh와 `research_admission`·Main wrapper의 호출 순서다. 다음 수리/복구는 기존 heavy writer/slot custody와 owner deadline을 유지한 admission 대기·실행 순서 정합화다. Slot cap 증가·lock 삭제·memory guard 우회·실수량 변경이 아니다. Closure는 두 슬롯이 점유된 정상 선행 작업에서 초기 수량이 owner의 bounded 대기 후 실행하거나 명시 deferred로 남고, 계산 전 timeout을 허위 terminal/policy 성공으로 만들지 않는 회귀와 해당 producer → 직접 소비 → summary/strict/controller다. 이미 끝난 wrapper를 다시 실행하거나 진행 중 worker를 종료하지 않았다. 해당 source generation의 실제 필요 계산·인계 재개 여부는 아직 미확인이다.

### 2. Machine stage의 산출물 계약 불일치

직접 근거는 [failed stage receipt](/home/ubuntu/KORStockScan/data/report/postclose_stage_terminal/2026-10-13/main_machine_policy.json)다. Schema `postclose_stage_terminal_v3`, source/publication `2026-10-13`, effective `2026-10-14`, stage run `4902ed620a7241f1b0004a6ae6938455`, child PID/start ticks `3588145/14283603`, exit 1이다.

- Missing/invalid 요구: `reversal_source_manifest`, aggregate `main_fixed_watch_policy_research`, 그리고 `403870`·`196170`·`036930` 개별 연구 출력. 전체 issues 9개다.
- `continuous_reversal_postclose.main`의 pending joint registration 분기는 `reversal_joint_registration.run_postclose`로 조기 반환한다. 이 실행은 `continuous_reversal_operating_comparison_v1`의 `machine.json`·`auxiliary.json` 및 winrate report/terminal을 발행했다. `comparison_complete=false`, `comparison_state=incomplete`, `adoption_basis=operator_designated`, registration/membership `registered`다.
- 반면 `postclose_summary_handoff.stage_artifacts`는 10/6 이후 모든 machine에 `continuous_reversal/<day>/source.json`을 필수로 추가하고, 그 파일이 없으면 구 fixed-watch sidecar도 추가한다. 현재 생산 분기와 검증 요구가 일치하지 않는다.
- Winrate terminal의 `continuous_reversal_selected`·`machine_component_prepared`는 생산자 결과다. Stage receipt의 `policy_disposition=incumbent_carry`와 구분하며 전체 정책/consumer 성공 또는 실제 PID 소비로 바꾸지 않는다. 운영자의 최초 지정에 추가 경제성 승격 gate를 붙이지 않는다.

Owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry` / `DirectFamilyPreopenPolicyHandoff`와 해당 stage producer/consumer다. 다음 수리는 등록 분기의 실제 원천·등록·보고서·terminal을 정확 날짜/schema/hash/권한으로 결속하는 산출물 계약 정합화다. 구 보고서나 terminal을 합성해 PASS를 만드는 수리가 아니다. Closure는 영향받은 stage와 auxiliary/summary의 동일 generation 검증, tower/checklist → 성공한 `--require-summary-handoff` strict → controller/finalization이다. 현재 실행본 교체·전체 wrapper 반복·재기동은 수행하지 않았다. 같은 입력에서 시간만 더 기다려 이 계약 오류가 해소될 ETA는 null이다.

### 3. 자동 Main 종료 후 이전 최종화의 역사 검증 실패

[오류 탐지](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-10-13.json)의 `cron_completion`은 source `2026-10-12`, effective `2026-10-13`, 완료시각 `07:00:37`, issues `strict_checklist_generation_stale`, historical fallback reason `intraday_observer_receipt_unavailable:FileNotFoundError`를 기록했다.

선택 commit의 handoff·consumed JSON과 historical checklist는 실제 존재한다. REST 배포 completion이 기록한 Main identity는 PID `3517912`, start ticks `13710100`, 해당 release `/src` cwd이며 EOD 뒤 `/proc/3517912`는 사라졌다. `intraday_release_handoff._historical_checklist_for_observer`는 역사 관찰에서도 consumed identity에 대해 `_identity(pid)`와 current PID bootstrap 검증을 요구한다. 20:56 detector는 warning, 설치된 stop 뒤 21:00 detector는 이 경로의 fail이 됐다. 선택 release에서 pure historical observer를 읽기 전용 재조회한 traceback도 해당 `_identity` → `/proc` stat read를 직접 확인했다. 이 재현은 새 finalization/strict/보고서 발행이 아니다.

Owner는 기존 `DirectFamilyPreopenPolicyHandoff`의 소비/역사 인계와 `postclose_finalization_generation.finalization_marker_issues` 관찰 경로다. 다음 확인/수리는 봉인된 원 checklist·소비·종료 provenance로 이전 종결을 관찰하는 계약과 현재 살아 있는 PID의 startup/activation 계약을 구분해야 한다. 원 source/manifest/strict/DONE hash는 계속 검증해야 한다. Closure는 정상 postclose stop 뒤 이전 역사 검증이 원 세대만 검증하고 새 PID/새 finalization/PASS를 합성하지 않는 회귀다. 경고 억제·bot 재기동·이전 최종화 재실행을 하지 않았다. ETA는 null이다.

## 원천·submit·경제성 구분

[Preflight](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-10-13.json)의 전역 raw input 허용과 family별 gate를 구분한다.

- 기계 evaluation 1,624: `ENTER_NOW=1531`, `BLOCK=8`, `RECHECK=6`, `SOURCE_INVALID=79`. Trace join은 exact snapshot/bundle/action 350, action mismatch 1,194, snapshot/bundle missing 80이다. 다른 분모·단계를 더해 unique submit 기회로 계산하지 않는다.
- Entry screen trace 2,582, 실제 provider-called 265; provider request/outcome 265가 각각 연결된다. `assessment_contract_invalid_trace_count=1038`, 해당 행 격리 true. `warning_machine_attempt_conservation_gap`으로 machine threshold tuning input은 false다. Raw 날짜 전체 차단이나 1,038 broker 거절로 해석하지 않는다.
- 현재 compact prompt `continuous_reversal_auxiliary_production_v1:reversal_citation_v6`의 natural traces 1,070, provider-called 0, eligible partition 0, `prompt_receipt_gap`, measurement allowed false다. 다른 prompt/provider 시도의 성공을 현 prompt의 성과로 승계하지 않는다.
- 19:55:24 [Sentinel](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-10-13.json)은 `SUBMIT_DROUGHT_CRITICAL`, submitted unique 0을 기록한다. 우선 점검은 같은 intent/attempt의 `ENTER_NOW` → 실제 auxiliary PASS/CAUTION → 정상 submit/terminal 연결이다. 새 root-cause taxonomy나 threshold 완화를 실행하지 않는다.
- Preflight의 terminal tuning gate는 `no_terminal_rows_admitted`, cost-adjusted EV null, economic comparison eligible false다. 운영 연결·관측 건수·선택 component를 비용 후 EV/순익 또는 broker rejection으로 바꾸지 않는다.
- EOD 3종목 `266690`·`468670`·`486510`는 OHLCV 이력 부족으로 제외됐다. 이 특정 경고만으로 오늘 모든 튜닝 원천을 차단하지 않는다.

## 관측 fingerprint와 검증 범위

21:17:21의 canonical file byte SHA256이다. 내부 `artifact_content_sha256`·`receipt_sha256`와 다른 계약이다.

| 산출물 | byte SHA256 |
| --- | --- |
| Preflight | `17391fbc2a9108ea2dc53cdb3f6083169c22e469872fa8ee0b50f31b25df6ec0` |
| Failed machine stage | `f196ac6e49c87f5e68d11c3a831963a35dcaa219693e2d7114dc595bc77460e2` |
| Machine operating report | `68fdfcb31219b91a94150003d10d22b7f85d0125198c53256666a59f0f585a64` |
| Auxiliary operating report | `2fd7962a555498c950fad03186952e78850052cd0f7850c8104e234484a0b4c8` |

대용량 원천은 stat/기존 요약과 bounded log tail로만 조회했다. 첫 feedback worker의 관측 중 physical read 약 25.5GB, 임시 파일 약 2.47GB는 producer 진행/비용 관찰이며 이 세션의 raw 스캔이나 성능 개선 결과가 아니다. Wrapper native metrics는 해당 명령 exit 0을 확인했다. 이 데이터로 IO0–IO5 계획을 구현·배포하지 않았다.

문서만 추가했으므로 링크·권한·source-date·owner를 self review했다. 링크 9개 missing 0, 새 OPEN row 0, print-only parser exit 0·현재 checklist stable owner 8개 중복 0, `git diff --check` 및 추가된 untracked 문서의 별도 whitespace 검사를 통과했다. Python/runtime/order 코드 변경이 없어 pytest·compile·provider/replay·보고서 재생성·strict 재실행은 하지 않았다. 아직 미완결인 분석·final phase·whole-chain terminal·05:35 finalization·07:35 PREOPEN·다음 Main PID/자연 주문/실현 손익은 미확인으로 남는다. Main PID `3546399` 종료와 controller `3546582`·tuning wrapper `3546403`의 원 start ticks/cwd·대기 생존을 마지막에 다시 확인했다. 관측용 임시 EOD watcher와 Main terminal watcher는 조건 충족 후 각각 종료됐으며 새 collector/service/cron을 남기지 않았다.

## 실패 지점 수리·재실행 후속

위 기록은 원 모니터링 시점의 실패와 권한 범위를 보존한다. 이후 사용자가 실패 지점 수리·재실행을 지시해 [구현·검증·복구 근거](postclose-failed-stage-recovery-implementation-review-2026-10-13.md)의 source-only 수리를 수행했다. 선택·실제 postclose release는 commit `ced94113652aa56261f5633bb3e372101992190d`다. Admission 대기와 joint 최초 등록 산출물 계약을 보완했고, symlink 경로와 영향받은 코드 결속을 검증했다. 기존 prefix는 native 완료 증거로 재사용하고 source/publication `2026-10-13`을 유지했다.

Machine·delay·auxiliary와 재실행한 legacy report가 exit 0·issues 0으로 종료했다. 원 outcome labels는 검증된 성공을 재사용했다. Main native run `bdb70729be21466b96816bb2f46f322c`가 23:01:44에 실패했던 초기 수량부터 재개됐고 해당 명령은 wall 1.939초·exit 0·`carry_parent`로 통과했다. 초기 수량 완료 거래는 0이다. 원 failed Main·stage 이력은 attempts에 보존한다. 기존 활성 정책 bundle은 byte 동일한 33개 코드와 승인 원천 784개를 검증한 인계 metadata로 유지했고 새 정책 선정·provider·주문 권한은 만들지 않았다.

23:12 관측에서 하류 청산 snapshot과 stop confirmation·whole-chain strict·summary/controller·tuning의 최종 종결은 아직 진행 중이다. 최종 audit는 raw/source 입력 허용과 `machine_threshold_tuning_input_allowed=false`·`economic_comparison_eligible=false`·`cost_adjusted_ev=null`을 따로 기록한다. Delay는 `initial_baseline_immediate`, qualified PASS 107·valid executable anchor 73이며 원천 결손 행을 제외한다. 운영 연결 통과를 지연 우위나 비용 후 실현성과로 바꾸지 않는다.

### 10/14 00:51 최종 관측

수리 commit `5cffbc22a61995d8d0233ca95bb2c95915610ba7`의 실제 source 10/13 재실행은 Main 00:38:00 success, tuning 00:42:11 success, summary handoff 00:42:56 success, whole-native strict 00:46:10 PASS·issues 0, controller JSON 00:48:28 DONE 및 준비 포함 wrapper 00:51:00 DONE으로 종결됐다. 활성 stage 7개 모두 succeeded이며 실제 native run은 `195effbea22446479f7ff97eef091f4b`다. 완료된 원천/계산은 재사용했고 원 failure/attempt 이력은 보존했다. [상세 수리·원 SHA·검증·terminal](postclose-failed-stage-recovery-implementation-review-2026-10-13.md)을 기준으로 읽는다.

장전 준비는 source/publication 10/13·적용 10/14의 `prepared_verified`이며 선택 commit·manifest/env·verification·controller/summary SHA가 결속됐다. `actual_pid_consumed=false`, day-of activation required다. 05:35 최종화와 07:35 PREOPEN·다음 실제 Main PID/자연 주문/비용 후 성과는 예정된 후속이며 현재 완료가 아니다. 비용 원천의 default local account alias는 source_gap으로 보존하고 승인 account의 성과로 승계하지 않는다. Holding policy_binding_gap와 family 경제성/자연 원천 OPEN도 10/14 checklist에 유지한다. 실제 bot 재기동·주문·threshold/quantity 변경이나 퇴역 worker 복원은 수행하지 않았다.
