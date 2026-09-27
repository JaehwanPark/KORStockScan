# 장중 생산자–장후 소비자 S0 경로·소유권 조사

실행일: 2026-09-27 KST. 범위: [단계 계획 §3 S0](../proposals/intraday-producer-postclose-consumer-codebase-gap-repair-plan-2026-09-27.md), [현행 checklist `IntradayPostcloseHandoffS0`](../checklists/2026-09-28-stage2-todo-checklist.md). **판정: S0 목록과 인계 작성 완료; 데이터 계약·자연 소비 검증은 미완료.** 이 문서는 S1–S8을 실행하거나 장후 전체 체인을 승인하지 않는다.

## 1. 조사 기준과 발견 방법

- `rg --files src deploy`로 작업공간의 `src` 1,050개(그중 `src/tests` 제외 593개), `deploy` 263개 파일을 열거했다. `deploy/systemd`의 service/timer 파일 157개, `src/trading/config`의 11개 파일도 설정·설치 후보에 포함했다. 이름 검색에 더해 `emit_pipeline_event`/writer와 경로 상수에서 **정방향**, `read`/`source_paths`/stage 입력과 policy loader에서 **역방향**으로 추적했다. `src/utils/threshold_cycle_registry.py`의 stage→family 맵과 명시적 source-only 집합, `src/engine/automation/postclose_summary_handoff.py`의 `STAGE_REGISTRY`·`stage_commands`·`stage_input_paths`, `src/engine/automation/postclose_recommendation_intake.py`의 `SOURCE_LABELS`, `src/engine/infrastructure/runtime_release_router.py`의 `OWNED`·`OPERATIONS`를 등록 관점으로 교차 확인했다. 후보는 아래 연결표의 소유 family로 묶었다. 856개 비테스트 파일 각각이 장중 생산자 또는 장후 소비자라는 뜻은 아니다.
- 설치된 `crontab -l`의 실행 행 43개, `deploy/run_threshold_cycle_postclose.sh`·`deploy/run_threshold_cycle_preopen.sh`의 실제 module 호출, `systemctl`의 설치 서비스/타이머 및 `data/runtime/runtime_release_selection.json`을 대사했다. cron 문구의 존재는 해당 날짜 실행 영수증이 아니다. `bash deploy/run_runtime_release.sh --check-cron`은 필수 대상 8개 경로를, `--check-release-set`은 선택기와 별도 owner pin을 확인했다.
- 2026-09-22~25의 `data/report/postclose_stage_terminal/<source-date>/` 영수증은 **과거 세대의 상태 예시**로만 읽었다. 현재 선택 릴리스에서 같은 날짜의 산출물 해시·run·원모수/제외/출력 수를 다시 검증하지 않았다. `data/pipeline_events/pipeline_events_2026-09-27.jsonl` 파일 존재도 정상 장중 거래나 소비 증거로 승격하지 않는다.
- 경로 코드에서 확인한 것은 `C`(호출/등록), cron·systemd 설치는 `D`(dispatch 예정/별도 owner), 파일·영수증은 `A`(artifact), PID는 `P`로 구분한다. 아래 `미확인`은 0건·valid-empty가 아니다. source/effective date, run ID, SHA-256, record ID, 원본/유효/제외/미관측 수, 비용은 S0에서 각 행별로 확정하지 않았으며 S1–S5의 검사 항목이다.

## 2. 릴리스·실제 dispatch·owner 경계

| 경계 | 2026-09-27 확인 근거 | 판정 |
| --- | --- | --- |
| 작업공간/선택 main | [전체 미커밋 재검토·배포 영수증](2026-09-27-uncommitted-worktree-review-deployment.md)의 불변 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-review-holdout-20260927`, `9a03c939aa1aff3830057d855ebbdbc955793f89`; 이전 선택 `50ffc08e…`. `data/runtime/runtime_release_selection.json` 19:07 KST 선택. | 코드 선택 완료. 공유 `data/docs/logs/tmp`와 작업공간 미커밋 파일은 불변 source 자체가 아니다. |
| main cron | `run_runtime_release.sh` → router가 `preopen`, `start`, `eod`, `postclose`, `controller`, `tuning`, `archive`, `finalize`, `buy-funnel`, `holding-exit-sentinel`을 선택 릴리스로 라우팅한다. cron 8개 필수 target 확인 통과. | 설치/선택 경로 확인. 오늘 자연 dispatch·consumer PID 미확인. |
| 작업공간 직접 cron | `final_ensemble_scanner`, `buy_pause_guard`, `ipo_listing_day_autorun`, `bd_fbuy_accum_pre_intraday`, `panic_sell_defense`, `rising_missed_intraday_feedback`, `intraday_ws_freshness`, `monitor_snapshot_incremental`, `market_opportunity_census`, `system_metric_sampler`, `error_detection`, `monitoring_instruction_refresh` 등이 workspace `src` 또는 `deploy`를 직접 참조한다. | 선택 main 릴리스와 동일하다고 추정하지 않는다. 각 독립 producer/observer의 실행 영수증은 후속 조사. |
| 별도 systemd | release-set 점검: episode profile 122개 모두 inactive, policy pin 366/366 확인; widget signal auto trader와 low-price auto expansion inactive/PID 0, 이전 `2e1d935f…` pin. 실행 중은 Doosan/Hanwha/Samsung **읽기 전용** widget collector 3개와 gunicorn. | widget/episode는 별도 owner. collector PID는 main bot PID나 주문 권한이 아니다. |
| 실제 main PID/자연 결과 | release-set 점검 `main_pid_binding.pid=null`, 선택기 `actual_pid_consumed=false`; 선택 릴리스에서 정상 PREOPEN·main PID·당일 terminal·비용 후 EV 수용 근거 없음. | 모두 `not_observed`. `--print-plan`/선택기/파일 존재는 상위 단계로 자동 승격하지 않는다. |

## 3. 양방향 연결표

`A`=설치 dispatch 후보 또는 코드상 활성, `O`=관측/source-only, `F`=명시 OFF/퇴역. 모든 행의 세대/hash/입력·유효·제외·미관측 건수는 **미확인**이다. `C+D`는 코드 연결과 설치 경로를 확인했다는 뜻이며 정상 산출·경제성 수용을 뜻하지 않는다. 같은 원천을 여러 consumer가 읽으면 나누어 적었다.

| ID·상태/owner | 실제 진입·생산자 → 원천/투영 → 장후 reader·마지막 소비자 | 연결 근거·S1 이후 검사 |
| --- | --- | --- |
| H00 A/main | `run_runtime_release.sh start` → `kiwoom_sniper_v2`/`sniper_state_handlers` → pipeline/order/position 산출 → 아래 H01–H12 | C+D; 07:55 cron. main PID 미확인. 실행 없이 각 원천을 자연 생성으로 간주 금지. |
| H01 A/main 공통 | scanner `final_ensemble_scanner`·main scanner hook → scanner/target pipeline event → `strategy_position_performance_report` scanner lineage 및 `market_opportunity_census` | C+D; scanner는 07:20 workspace 직접 cron, census는 5분 직접 cron. record ID·session/venue 역대사 S1/S4. |
| H02 A/main 공통 | Kiwoom WS/REST quote·orderbook, `kiwoom_sniper_v2` → quote/source status 및 pipeline fields → `observation_source_quality_audit`, `intraday_ws_freshness_monitor`, machine attribution | C+D; WS freshness는 직접 cron/장후 finalize. raw packet→투영의 epoch·FID·route·누락 S1. |
| H03 A/main 공통 | `emit_pipeline_event` (`kiwoom_sniper_v2`, `sniper_state_handlers`, low-price machine) → `data/pipeline_events/pipeline_events_<date>.jsonl` → `pipeline_event_verbosity_report`, source-quality preflight/final | C+D; postclose wrapper 17:xx/20:10 경로. stage·schema·날짜·원본/격리 수 S1. |
| H04 A/main 공통 | pipeline logger/`threshold_cycle_registry` → `pipeline_event_producer_summary_manifest_<date>.json` → `pre_submit_delay_tuning` stage 입력 및 runtime summary/strict | C; `stage_input_paths('pre_submit_delay')` 명시. manifest 세대와 raw 원본 동일성 S1/S5. |
| H05 A/main 안전 | pipeline/AI payload·threshold observation → `observation_source_quality_audit`/`raw_row_exclusion` → machine/auxiliary 정책 평가 | C+D; preflight·final wrapper. 누락과 valid-empty, 격리 실패, 식별 불능 계약 손실은 S1. |
| H06 A/main 진입 | machine BLOCK/RECHECK/ENTER_NOW 및 AI payload → `data/ai_decision_payloads` + pipeline events → `ai_decision_quality` outcome labels → `main_auxiliary_policy`/`collector_recommendation` | C; `outcome_labels` stage는 payload input hash, auxiliary는 label prerequisite를 선언. 주문/비주문 분모 S2. |
| H07 A/main 진입 | machine 판정·pre-submit clock → pipeline summary/latency rows → `pre_submit_delay_tuning` + policy → PREOPEN bootstrap | C; 9/23부터 필수 stage. 현행 checklist `DirectFamilySourceRepairPreSubmitDelay`; 시간축 S1/S2. |
| H08 A/main 진입 | 수량 유형·entry split/probe·BUY submit/cancel/timeout → pipeline/terminal/order-owner registry → `entry_split_order_plan`, `entry_cancel_wait_tuning`, `initial_quantity_policy` refresh | C+D; postclose wrapper 직접 호출. 별도 checklist `DirectFamilySourceRepairEntrySplit`, `DirectFamilySourceRepairEntryCancelWait`, `InitialQuantityClosedLoop0928`; pending/partial 별도 S2. |
| H09 A/main 진입 | AI action·주문 outcome → pipeline/AI payload/결과 → `ai_action_outcome_calibration` (`main_machine_policy`, `legacy_machine_report`) → win-rate stage terminal/PREOPEN policy | C; `stage_commands` 두 모드. cost/PnL·holdout·source gap S2/S5; 정책 선택 ≠ PID 소비. |
| H10 A/main 진입 | main/low-price/samsung machine trace → pipeline/DB/report → `machine_microstructure_attribution`, `machine_entry_timing_tuning`, `samsung_machine_entry_tuning`, `low_price_two_leg_tuning` | C+D; stage 및 wrapper 직접 호출 혼합. episode 저가 owner와 main owner 분리 S2/S4. |
| H11 A/main 보유 | `sniper_state_handlers` holding/trailing/scale-in 판단·주문 → pipeline/order registry/position fact → `scale_in_split_order_plan`, `holding_exit_sentinel`, `post_sell_feedback` | C+D; sentinel은 선택 릴리스 cron, feedback은 postclose wrapper. `DirectFamilySourceRepairScaleInSplit`; partial·open S3. |
| H12 A/main 손익 | broker order/fill/cancel reconciliation + `order_owner_registry.jsonl` → `sniper_trade_review_report`/`strategy_position_performance_report` fact sync → monitor `trade_review`/`holding_exit_observation`/`postclose_exit` → `runtime_approval_summary` | C+D; `COMPLETED + valid profit_rate`만 실현 PnL. 원가 불명은 null, owner/venue/session S3. |
| H13 A/별도 widget | 읽기 전용 collector 3개와 widget auto-trade owner → collector/advisory/EOD source → `run_widget_evaluation.sh` → `widget_policy` 5 artifacts → research allocation | C+D; collector 실행은 확인, trader inactive. widget EOD exact-date 입력(`stage_input_paths`)과 source 세대 S4/S5. |
| H14 A/별도 episode | low-price machine/preflight·episode policy source → expanded candidate research/refresh → `episode_policy` terminal → allocation | C+D; 122 profile units inactive, policy pins 366 확인. 자연 거래·정책 활성은 미확인; S4/S5. |
| H15 A/main 관측 | `rising_missed_intraday_feedback`/`market_opportunity_census`/market breadth → feedback·market report → rising classifier prior, `market_weakness` stage, runtime summary | C+D; 직접 intraday cron과 wrapper. no-entry opportunity/valid source 분모 S4. |
| H16 A/main·widget 연구 | native capacity, widget/episode stage terminal → `machine_research_closed_loop_refresh` allocation → `research_allocation` stage terminal | C; stage prerequisites 명시. 실패한 capacity가 allocation을 defer한 9/23 사례, S4/S5. |
| H17 A/관측 | buy-funnel sentinel, panic-sell sim defense, error detector, monitor snapshot, metric sampler → 진단/감시 artifact → postclose detector/summary 또는 운영자가 소비 | C+D; source-only/시뮬레이션은 실주문 권한 없음. 최종 소비자가 기계 정책인지 관측인지 S4. |
| H18 A/장후 | wrapper 직접 family H03/H05/H08/H10/H11/H12/H15 + registry 15 stages → `postclose_stage_terminal/<date>/*.json` → `postclose_summary_handoff`, strict verifier, controller/finalizer | C+D; 20:10/21:55 선택 릴리스 cron. 동일 source date/run/hash 및 누락 stage S5. |
| H19 A/장후→장전 | runtime summary·stage terminal·holding vote·initial quantity refresh → `runtime_policy_bootstrap`와 PREOPEN policy applies → exact-date env/manifest → main start PID | C+D; 07:35/07:55 선택 릴리스 cron. future env 파일 존재는 정상 PREOPEN/PID 아님; S5. |

장후 stage의 역방향 등록표는 다음과 같다. 명칭만 모은 것이 아니라 `stage_commands`의 실행 producer, `STAGE_REGISTRY`의 출력, prerequisite/`stage_input_paths`를 대사했다.

| stage (15개) | 실행 producer → 등록 output / prerequisite |
| --- | --- |
| `main_machine_policy` | `scalping.ai_action_outcome_calibration --winrate-policy-only` → `machine_policy`, `machine_policy_terminal` |
| `pre_submit_delay` | `scalping.pre_submit_delay_tuning` → tuning, policy / pipeline summary manifest |
| `main_auxiliary_policy` | `scalping.entry_setup_paired_replay_batch` → compact paired economic / `outcome_labels` |
| `legacy_machine_report` | `scalping.ai_action_outcome_calibration --machine-only` → action outcome calibration |
| `outcome_labels` | `scalping.ai_decision_quality` → outcome labels / AI payloads |
| `widget_policy` | `deploy/run_widget_evaluation.sh` → advisory, auto trade, symbol research/apply, refresh / exact-date EOD status |
| `episode_policy` | low-price expanded research + episode refresh → expanded candidate, episode refresh |
| `collector_recommendation` | widget collector expansion → recommendation / `outcome_labels`, AI payloads |
| `machine_attribution` | machine microstructure attribution → attribution |
| `machine_timing` | machine entry timing → timing / `machine_attribution` |
| `market_weakness` | market weakness hysteresis → weakness / `machine_attribution` |
| `research_capacity` | native capacity source → capacity source |
| `research_allocation` | closed-loop allocation refresh → allocation / widget, episode, capacity |
| `legacy_policy_approval` | microstructure policy approval → approval / `machine_attribution` |
| `summary_handoff` | postclose done controller summary-only → controller / 그 날짜의 다른 모든 필수 stage |

`postclose_recommendation_intake.SOURCE_LABELS`의 12개 label 중 `samsung_machine_entry_tuning`, `low_price_two_leg_tuning`, `code_improvement_workorder`처럼 registry stage 출력과 일대일이 아닌 항목은 wrapper 직접 단계 또는 OFF/legacy 문맥을 별도로 확인해야 한다. `SOURCE_LABELS`에 있다는 이유만으로 오늘 필수 stage/실행으로 보지 않는다.

## 4. 고아 후보·미분류 및 명시적 제외

아래는 **확정 고아/결함이 아니라 S0에서 양방향 세대 대사가 닫히지 않은 후보**다. 다음 단계는 동일 ID를 유지하고 실제 orphan 여부를 판정한다. 영향 family와 임시 처리는 원천 불명 시 정책·주문 승격 금지, 원본 보존이다.

| 인계 ID·우선순위 | 역/정방향 빈 고리·영향 | 다음 owner·닫힘 검사 |
| --- | --- | --- |
| `S0-COM-01` P1 | quote/orderbook/WS·REST 원본 → scanner/main pipeline 필드: route/epoch/시각/record identity와 원본·투영 건수 미확인(H01–H03). | **S1** `src/engine/kiwoom_sniper_v2.py`, `src/engine/sniper_state_handlers.py`, `src/engine/observation_source_quality_audit.py`; 원본→투영→첫 reader 같은 ID/시각/건수와 valid-empty/누락 fixture. 프로토콜 변경이면 공식 Kiwoom reference gate 선행. |
| `S0-COM-02` P1 | pipeline JSONL → producer summary manifest → pre-submit stage/quality: 날짜·stage·hash/중복·제외 수 미확인(H03–H05). | **S1** `src/utils/pipeline_event_logger.py`, `src/utils/threshold_cycle_registry.py`, `src/engine/automation/postclose_summary_handoff.py`; raw/summary/reader 동세대·입력=유효+제외+미관측 대사. |
| `S0-COM-03` P1 | broker 주문·체결·취소 → owner registry/DB projection → 첫 장후 fact: parent/leg, 부분체결, 종결 상태와 비용 미확인(H08,H12). | **S1** custody registry·fact sync에서 최초 소비까지; **S2/S3** 경제성/의사결정 추적. `DirectFamilySourceRepairEntryCancelWait` 등 기존 owner 유지. |
| `S0-ENT-01` P1 | AI payload/판정·BUY plan → labels, machine/auxiliary, entry split/cancel/initial quantity: 각 거절 사유·leg 분모/최종 broker 확인 미확인(H06–H10). | **S2** main/scalping owner; 기존 `DirectFamilySourceRepairEntrySplit`, `DirectFamilySourceRepairEntryCancelWait`, `DirectFamilySourceRepairCompactAuxiliary`, `InitialQuantityClosedLoop0928`. |
| `S0-EXIT-01` P1 | holding/SELL → terminal·position fact·비용 → postclose_exit/summary: partial/open/censored 및 widget/episode/manual 구분 미확인(H11–H14). | **S3** holding/order/report owner; `HoldingExitPositionOutcomeLineageClosure`. |
| `S0-OTHER-01` P2 | 직접 workspace cron의 scanner, panic sim, census, rising missed, WS freshness, monitor/metric/error detector와 widget/episode가 각각 어떤 최종 artifact/reader를 갖는지 미분류(H01,H13–H17). | **S4** 각 별도 owner; 실행 receipt → source-only/active/OFF → 최종 consumer 또는 의도된 종료까지 분류. |
| `S0-FINAL-01` P1 | wrapper 직접 family, 15 stage, 12 intake label 간 비일대일 관계와 stage output → summary/strict/controller/finalizer/PREOPEN 같은 run/hash 미확인(H18–H19). | **S5** `postclose_summary_handoff`·strict/finalizer·PREOPEN owner; `PostcloseFinalizerControllerTerminalReceipt`. stage별 동세대 receipt와 실패/valid-empty 처리. |

명시적 제외·경계: Swing은 설치 postclose cron의 `THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE=false`와 wrapper 하위 flag false로 OFF다. ADM/LDM·institutional flow·lifecycle matrix/context/bucket/bridge·opening rotation·latency classifier recommendation은 retired; PYRAMID feedback/AVG_DOWN calibration은 operator OFF. `scalp_sim`과 panic defense simulation, 일부 workorder/research 옵션은 source-only 또는 기본 OFF다. `codebase_performance_workorder`, time-window counterfactual, producer-gap discovery, stage-hook workorder/scaffold는 wrapper 기본 false/조건부 실행이므로 산출물 부재를 고아 결함으로 세지 않는다. 별도 명시 활성 증거 없이 퇴역 consumer를 복원하지 않는다.

## 5. 과거 terminal과 다음 단계 인계

`2026-09-22` stage 14개는 기록상 succeeded, `2026-09-23`은 15개 중 `research_capacity=failed`, `research_allocation=deferred`, `summary_handoff=failed`; `2026-09-24`·`09-25`에는 `episode_policy=failed`, `main_machine_policy=deferred` 두 개씩만 영수증이 있다. 이는 S0의 **실패/누락 후보 발견 증거**이지 현재 선택 릴리스에서 재검증된 오늘의 PASS/FAIL이 아니다. 9/28 source date의 자연 입력·stage terminal은 아직 관측하지 않았다.

**S1 착수 범위:** `S0-COM-01`~`03`과 H01–H05/H12의 첫 공통 투영까지만 받는다. `S0-ENT-01`, `S0-EXIT-01`, `S0-OTHER-01`, `S0-FINAL-01`은 각각 S2/S3/S4/S5의 기존 owner를 유지한다. S1은 raw source → projection → 최초 장후 reader별 schema·시장/세션·clock/epoch·route·ID·건수·결측/valid-empty·source-quality 격리를 한 행씩 검증하고 최소 fixture/원천 증거와 수리 owner를 기록한다. 원천 gap을 no-edge/0 PnL로 치환하지 않는다. S0의 완료는 코드 수정·서비스 재기동·정규 장후 실행·실주문·경제성 승인이 아니다.

## 6. S0 자체 검토 및 검증

정방향 writer 목록을 역방향 stage 등록·wrapper/cron·loader와 재대사하고, stage 15개·intake label 12개·직접 wrapper family·별도 systemd owner를 연결표/미분류에 포함했다. S0는 인벤토리이므로 개별 row의 schema·세대·hash/건수 검사와 자연 PID 소비는 후속 단계의 미해결 항목이다. 문서 링크/owner·권한 경계를 검토하고 print-only backlog parser와 `git diff --check`로 문서 변경을 확인한다. 정규 장후와 provider 호출은 실행하지 않았다.
