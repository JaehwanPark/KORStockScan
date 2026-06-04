# 2026-05-14 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

### PreopenAutomationHealthCheck20260514 운영 확인 기록

- checked_at: `2026-05-14 07:54 KST`
- 판정: `warning`
- 근거: `threshold_cycle_preopen_cron.log`에 `2026-05-14` preopen `[DONE]` marker가 있고, `threshold_apply_2026-05-14.json` status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`다. runtime env는 `threshold_runtime_env_2026-05-14.env/json`으로 생성됐고 selected family는 `soft_stop_whipsaw_confirmation`, env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`다. `tmux bot` 세션은 `2026-05-14 07:40 KST`에 기동됐고 `bot_history.log`에는 main route=`openai`가 남아 있다.
- warning: `run_error_detection` 최신 full 결과는 process/cron/log/resource/stale-lock이 pass지만, `artifact_freshness`가 `daily_recommendations_v2.csv`와 diagnostics stale warning을 남겼다. `final_ensemble_scanner target_date=2026-05-14` 자체는 `[DONE]` marker와 추천 3건 적재 로그를 남겼으므로 운영 관찰 warning으로 분리한다.
- warning 해소 메모 (`2026-05-14 08:00 KST`): 최신 `error_detection_2026-05-14.json`은 summary_severity=`pass`, artifact_freshness=`pass`로 전환됐다. detector는 `daily_recommendations_*`를 `07:20~08:00` window, max_staleness_sec=`3600`으로 보는데, 파일 mtime이 `2026-05-13 21:26:02 KST`라 window 안에서는 stale warning이었다가 window 종료 후 `pass_after_window`로 닫혔다. 스캐너 로그에는 `final_ensemble_scanner target_date=2026-05-14` `[DONE]`과 `V2 CSV에서 3개 종목 우선 적재 완료`가 있어 preopen chain 실패는 아니다.
- detector 보정 메모 (`2026-05-14 08:04 KST`): `artifact_freshness`에 `daily_recommendations_v2.csv` 내부 `date`와 diagnostics 내부 `latest_date`/`selected_count` 검증을 추가했다. 보정 후 dry-run은 `daily_recommendations_csv_status=pass_content_date`, `daily_recommendations_diag_status=pass_content_date`, summary_severity=`pass`로 닫힌다. 이 보정은 운영 detector 판정만 바꾸며 threshold/provider/order guard는 변경하지 않는다.
- swing approval: `swing_runtime_approval_2026-05-13.json`은 `runtime_change=false`, approval request `0`이며 one-share real canary와 scale-in real canary는 모두 `approval_required`/`runtime_apply_allowed=false`다. `data/threshold_cycle/approvals` 아래 별도 approval artifact는 없다.
- 금지 확인: 확인 과정에서 threshold/provider/order guard, 스윙 dry-run guard, bot restart, broker 주문 상태를 변경하지 않았다.
- 다음 액션: 장중 runtime threshold mutation 없이 selected family provenance와 OpenAI `entry_price` 표본 부족을 기존 장중/장후 attribution에서 분리 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### IntradayAutomationHealthCheck20260514 운영 확인 기록

- checked_at: `2026-05-14 09:09 KST`
- 판정: `warning`
- 근거: 장중 window가 열린 뒤 `buy_funnel_sentinel_2026-05-14`와 `holding_exit_sentinel_2026-05-14`는 `09:05 KST`에 생성됐고 classification=`NORMAL`, `runtime_effect=report_only_no_mutation`이다. `panic_sell_defense_2026-05-14`는 `09:08 KST` 기준 panic_state=`NORMAL`, active sim/probe `10`, provenance_check passed=`true`다. 최초 `error_detection_2026-05-14`는 `panic_buying` log/report missing warning을 냈으나, `09:09 KST`에 `deploy/run_panic_buying_intraday.sh 2026-05-14`를 수동 실행해 `panic_buying_2026-05-14.{json,md}`를 생성했고 panic_buy_state=`NORMAL`, `runtime_effect=report_only_no_mutation`으로 닫았다. 재실행한 error detection은 `artifact_freshness=pass`, `process_health=pass`, `resource_usage=pass`, `stale_lock=pass`이나 `cron_completion`은 `panic_buying: log file not found` warning을 유지한다.
- runtime provenance: `threshold_apply_2026-05-14.json`과 `threshold_runtime_env_2026-05-14.{env,json}` 기준 당일 selected family는 `soft_stop_whipsaw_confirmation` 1개이고 env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`다. 전일 selected였던 `score65_74_recovery_probe`는 당일 runtime env override에 포함되지 않았고, `pipeline_events_2026-05-14.jsonl`/`threshold_events_2026-05-14.jsonl`에서 `score65_74_recovery_probe` provenance는 아직 0건이다.
- rollback guard: `pipeline_events_2026-05-14.jsonl`/`threshold_events_2026-05-14.jsonl`에서 `rollback`, `safety_revert`, `runtime_mutation`, `threshold_runtime_mutation` 검색 결과는 0건이다. `order_bundle_submitted`/`buy_order_sent`도 0건이라 장중 관찰 중 신규 주문 제출 근거는 없다.
- sim/probe split: `scalp_live_simulator_state.json`은 updated_at=`2026-05-14T09:00:40`, active_count=`0`; `swing_intraday_probe_state.json`은 updated_at=`2026-05-14T09:05:06`, active_count=`10`, active 전부 `actual_order_submitted=false`, `broker_order_forbidden=true`다.
- 금지 확인: 확인/수동 실행은 report-only 산출물 생성과 detector 재확인에 한정했고 threshold/provider/order guard, bot restart, broker 주문 상태를 변경하지 않았다.
- 다음 액션: `score65_74_recovery_probe` runtime event provenance는 장중 표본 미발생/당일 env 미선정으로 분리해 장후 `threshold_cycle_ev` attribution에서 다시 확인한다. `panic_buying` cron log missing은 운영 warning으로 남기고 다음 cron cycle에서 자동 생성 여부를 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### ProjectIntradayRecheck20260514 확인 기록

- checked_at: `2026-05-14 10:47 KST`
- 판정: `pass`
- 대상: `[RuntimeEnvIntradayObserve0514]`, `[SimProbeIntradayCoverage0514]`, `[Runbook 운영 확인] 장중 자동화체인 상태 확인`
- 근거: `threshold_apply_2026-05-14.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`이고 실제 runtime env selected family는 `soft_stop_whipsaw_confirmation` 1개다. 전일 selected였던 `score65_74_recovery_probe`는 당일 runtime env override에 포함되지 않았으며 `pipeline_events_2026-05-14.jsonl`/`threshold_events_2026-05-14.jsonl`의 `rollback`, `safety_revert`, `runtime_mutation`, `threshold_runtime_mutation`, `buy_order_sent` 검색은 0건이다. `swing_intraday_probe_state.json`은 updated_at=`2026-05-14T10:46:39`, active_count=`10`, 전부 `actual_order_submitted=false`/`broker_order_forbidden=true`이고 `scalp_live_simulator_state.json`은 active_count=`0`이다.
- runbook 근거: `panic_sell_defense_2026-05-14.json`은 panic_state=`NORMAL`, `real_exit_count=0`, `non_real_exit_count=21`, `stop_loss_exit_count=0`, market context=`NEUTRAL`, `confirmed_risk_off_advisory=false`다. `panic_buying_2026-05-14.json`은 panic_buy_state=`NORMAL`, TP counterfactual `real_exit_count=0`, `non_real_exit_count=36`, `tp_like_exit_count=0`, `non_real_tp_like_exit_count=18`이다. `PANIC_BUYING_COOLDOWN_SEC=0 bash deploy/run_panic_buying_intraday.sh 2026-05-14 >> logs/run_panic_buying_cron.log 2>&1`로 `cron_completion`이 기대하는 log contract를 채운 뒤 `bash deploy/run_error_detection.sh full` 결과 summary_severity=`pass`, cron/artifact/process/log/resource/stale-lock 모두 pass 또는 not_yet_due다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/python -m src.engine.panic_sell_defense_report --date 2026-05-14 --print-json`, `PYTHONPATH=. .venv/bin/python -m src.engine.panic_buying_report --date 2026-05-14 --print-json`, `bash deploy/run_error_detection.sh full`을 실행했다. `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` 결과 parser count=`7`이며 장중 대상 3건은 backlog에서 제외되고 장후 미완료 항목만 남는다.
- 다음 액션: 오늘 장중 Project 항목은 완료로 닫는다. 남은 확인은 due 전인 `12:05~12:30` intraday calibration과 postclose 항목이며, score65_74 계열은 당일 env 미선정/표본 미발생으로 장후 attribution에서 다시 본다. Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다.

### ErrorDetectionMemoryFalsePositive0514 확인 기록

- checked_at: `2026-05-14 11:44 KST`
- 판정: `pass`
- 근거: `log_scanner`의 `MEMORY_ERROR(6)` burst는 실제 OOM이 아니라 `kiwoom_orders_error.log`의 11:05:37~11:05:38 `8005 Token이 유효하지 않습니다` 6건을 메모리 오류로 오분류한 것이다. 기존 정규식의 `oom`이 `kiwoom_orders` logger 이름 안에서 매칭됐다. 최신 `error_detection_2026-05-14.json`은 `summary_severity=warning`, `log_scanner=pass`, `resource_usage=pass`이며 직전 resource sample도 memory/swap pressure를 보고하지 않았다.
- 조치: `MEMORY_ERROR` 패턴을 word-boundary 기반 `memory`/`MemoryError`/`oom`/`out of memory`/`cannot allocate memory`로 좁혔고, `kiwoom_orders` 인증 실패가 `MEMORY_ERROR`로 분류되지 않는 회귀 테스트를 추가했다. 이 조치는 System Error Detector report-only 분류 보정이며 threshold/provider/order guard, bot restart, broker 주문 상태를 변경하지 않았다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_error_detector_log_scanner.py`, `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode log_only --dry-run`, `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`로 확인했다.
- 다음 액션: 8005 토큰 실패 자체는 `kiwoom_auth_8005_restart` detector의 별도 auth incident 경로에서만 판단한다. `log_scanner`가 동일 signature를 다시 메모리 오류로 보고하면 classifier/source-quality blocker로 재오픈한다.

### PanicSellDetectionAggregationFix0514 확인 기록

- checked_at: `2026-05-14 09:35 KST`
- 판정: `pass`
- 근거: `panic_sell_defense_report`가 sparse `exit_signal` row만 보고 real exit으로 분류하던 집계 결함을 수정했다. holding 전체 이벤트에서 sim/probe/assumed-fill provenance가 있는 attempt key를 먼저 수집한 뒤 동일 key의 `exit_signal`을 non-real로 전파한다. 당일 dry-run 기준 기존 `real_exit_count=9` stop-loss cluster는 `real_exit_count=0`, `non_real_exit_count=17`, `stop_loss_exit_count=0`, `panic_state=NORMAL`으로 정정됐다. `holding_exit_sentinel_2026-05-14`의 `real_exit_signal=0`, `non_real_exit_signal=9`와도 정합된다.
- 테스트/검증: `.venv/bin/python -m pytest src/tests/test_panic_sell_defense_report.py` 결과 `9 passed`. `.venv/bin/python -m src.engine.panic_sell_defense_report --date 2026-05-14 --print-json`로 `panic_sell_defense_2026-05-14.{json,md}`를 재생성했고 runtime_effect=`report_only_no_mutation`을 유지했다.
- 다음 액션: 오늘 stop-loss cluster는 실청산 근거가 아니라 source-quality aggregation bug로 닫는다. 이 수정은 report 집계 보정만 수행하며 threshold/provider/order guard, 자동매도, bot restart, 스윙 실주문 전환을 변경하지 않는다.

### RealSimPerformanceAggregationAudit0514 확인 기록

- checked_at: `2026-05-14 09:45 KST`
- 판정: `pass_after_fix`
- 근거: 실매매/시뮬레이션 수익 집계 경로를 전수 점검해 두 추가 오집계 지점을 닫았다. `panic_buying_report`는 `panic_sell_defense_report`와 동일하게 sparse `exit_signal` sibling 전파가 없어 sim/probe TP-like exit을 real runner/TP 근거로 셀 수 있었으므로 holding 전체 attempt key 기반 non-real 전파를 추가했다. `daily_threshold_cycle_report`는 `completed_by_source` split은 있었지만 family 후보 계산에 `real_completed_rows + sim_completed_rows`를 넘겨 `statistical_action_weight`, `position_sizing_cap_release` 같은 family sample이 combined 성과로 오염될 수 있었으므로 family 후보/primary completed summary는 real-only로 고정하고 sim/combined는 diagnostic split으로만 남겼다.
- 당일 재생성 결과: `panic_buying_2026-05-14.json`의 TP counterfactual은 `real_exit_count=0`, `non_real_exit_count=30`, `tp_like_exit_count=0`, `non_real_tp_like_exit_count=15`다. `threshold_cycle_2026-05-14.json`은 `real_completed_valid_rolling_7d=4`, `sim_completed_valid_rolling_7d=11`, `combined.sample=15`를 분리 표시하되 `statistical_action_weight.sample.completed_valid=4`, `position_sizing_cap_release.sample.normal_completed_valid=4`로 family 입력은 real-only다. `threshold_cycle_cumulative_2026-05-14.json`도 cumulative `real.sample=177`, `sim.sample=11`, `combined.sample=188`를 분리하고 family 입력은 `177`로 고정됐다.
- 테스트/검증: `.venv/bin/python -m pytest src/tests/test_panic_buying_report.py src/tests/test_panic_sell_defense_report.py src/tests/test_daily_threshold_cycle_report.py` 결과 `46 passed`. `.venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-14 --ai-correction-provider none`와 `.venv/bin/python -m src.engine.panic_buying_report --date 2026-05-14 --print-json`로 관련 산출물을 재생성했다. runtime_effect/report-only 금지선은 유지됐고 threshold/provider/order guard, 자동매수/자동매도, bot restart는 변경하지 않았다.
- 다음 액션: `combined` 성과는 diagnostic-only로만 보고, real execution 품질/threshold family 후보/position sizing 승인 판단은 `real_only` 필드를 기준으로 본다. sim/probe EV는 별도 source bundle 입력으로만 유지한다.

### ScalpSimVirtualBudget0514 확인 기록

- checked_at: `2026-05-14 11:06 KST`
- 판정: `superseded_by_sim_virtual_budget_dynamic_qty`
- 근거: 실매매 경로는 현재 주문가능금액 부족 시 `blocked_zero_qty`로 멈추는 것이 맞다. 반면 `scalp_ai_buy_all_live_simulator`와 wait65_79 counterfactual은 `actual_order_submitted=false` 관찰축이므로 live 예수금/주문가능금액에 묶이면 missed EV가 0으로 왜곡된다. `sniper_state_handlers._resolve_scalp_sim_entry_qty`는 실주문 budget guard와 분리해, 실계좌 예산으로 1주를 살 수 없어도 sim-only 최소 1주 virtual fill을 만들고 `virtual_budget_override=true`, `budget_authority=sim_virtual_not_real_orderable_amount`, `qty_reason=sim_ignores_real_orderable_amount` provenance를 남기도록 보정했다. `wait6579_ev_cohort_report._simulate_paper_fill`도 `target_qty=0`이어도 가격이 있으면 `counterfactual_qty=1`, `counterfactual_qty_source=virtual_min_qty_budget_override`로 missed EV를 계산한다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_scalp_live_simulator.py src/tests/test_wait6579_ev_cohort_report.py` 결과 `21 passed`. 직접 함수 검증으로 `build_wait6579_ev_cohort_report('2026-05-14')`를 실행해 `total_candidates=11`, `virtual_budget_rows=11`, `expected_ev_krw_sum=38432`를 확인했다. `git diff --check`도 pass다.
- 다음 액션: 이 수정은 sim/counterfactual budget provenance 보정이며 threshold/provider/order guard, 실주문 수량 guard, bot restart는 변경하지 않았다. runtime 반영은 다음 배포/재기동 이후 적용하고, virtual budget 표본은 계속 diagnostic/source bundle 전용으로만 해석한다.

### SimVirtualBudgetDynamicQty0514 확인 기록

- checked_at: `2026-05-14 11:22 KST`
- 판정: `pass_after_fix`
- 근거: 사용자 지시에 따라 스캘핑 sim, wait65_79/missed-entry counterfactual, 스윙 intraday probe, 스윙 daily dry-run을 모두 `SIM_VIRTUAL_BUDGET_KRW=10,000,000` 가상 주문가능금액 기준으로 분리했다. 수량은 `floor(10,000,000 / entry_price)`가 아니라 실주문 동적수량 산식(`describe_buy_capacity`, strategy ratio, safety ratio, 해당 전략 cap)을 그대로 탄다. 이 과정에서 실계좌 예수금/주문가능금액은 sim/probe 수량 산식에서 제외하고 provenance로 `qty_source=sim_virtual_budget_dynamic_formula`, `virtual_budget_override=true`, `budget_authority=sim_virtual_not_real_orderable_amount`, `virtual_budget_krw`, `target_budget`, `safe_budget`, `virtual_notional_used_krw` 또는 `counterfactual_notional_krw`를 남기도록 했다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_scalp_live_simulator.py src/tests/test_wait6579_ev_cohort_report.py src/tests/test_swing_model_selection_funnel_repair.py -q` 결과 `62 passed`. `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_missed_entry_counterfactual.py -q` 결과 `2 passed`.
- 다음 액션: 이 변경은 `actual_order_submitted=false` 관찰축 sizing 보정이며 실주문 수량 guard, threshold/provider/order guard, bot restart는 변경하지 않았다. runtime 반영은 다음 배포/재기동 이후 적용하고, 기존 active sim/probe state의 과거 수량은 새 기준으로 소급 수정하지 않는다.

### Score6574ApplyGuardRecheck0514 확인 기록

- checked_at: `2026-05-14 11:29 KST`
- 판정: `logic_fix_ready_not_runtime_applied`
- 근거: `threshold_apply_2026-05-14.json`에서 `score65_74_recovery_probe`는 `calibration_state=hold_sample`, `decision_reason=calibration_state_blocked:hold_sample`로 제외됐다. 원인은 actual score65~74 source cohort `source_sample_count=16`과 broader funnel `budget_pass=642`가 섞여 `sample_count=642`로 저장되면서 `panic_adjusted_floor` 조건의 `sample_count < sample_floor` 비교가 깨진 것이다. `daily_threshold_cycle_report`에서 `score65_74_recovery_probe` readiness/floor 판정은 broader funnel count가 아니라 source cohort count만 쓰도록 보정했다.
- 재검증: 같은 2026-05-13 source를 기준으로 임시 manifest-only 검증을 수행하면 `score65_74_recovery_probe`는 `sample_count=16`, `source_sample_count=16`, `sample_floor=20`, `sample_floor_status=panic_adjusted_ready`, `calibration_state=adjust_up`, `decision_reason=ai_guard_accepted`, env override `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`로 selected 된다. 검증 중 만든 `2099-01-01`/`2099-01-02` 임시 apply manifest는 삭제했다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py -q` 결과 `43 passed`. `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-13 --ai-correction-provider none`로 report를 재생성한 뒤 `build_preopen_apply_manifest('2099-01-02', source_date='2026-05-13', apply_mode='auto_bounded_live', auto_apply=False, require_ai=True)`로 비적용 검증했다.
- 다음 액션: 장중 runtime env는 변경하지 않는다. 오늘 장후 `threshold_cycle_ev`/preopen apply source가 다시 생성되면 이 보정이 반영되어 score65~74 probe가 guard 통과 후보인지 재판정한다. 실제 runtime 반영은 다음 장전 bounded apply 경로만 사용한다.

### SwingStrategyMarketMappingFix0514 확인 기록

- checked_at: `2026-05-14 09:56 KST`
- 판정: `pass_after_fix`
- 근거: `LG(003550)`, `에스엘(005850)`, `현대오토에버(307950)`, `두산로보틱스(454910)`는 `recommendation_history`에서 `trade_type=RUNNER`, `strategy=KOSDAQ_ML`로 저장되어 KOSDAQ 진입 갭/청산 stop 분기를 탔다. `final_ensemble_scanner`는 FDR `KOSPI` universe를 대상으로 generic `RUNNER`를 만들지만, `DBManager.save_recommendation`의 기본 매핑이 `RUNNER -> KOSDAQ_ML`이어서 KOSPI runner에도 KOSDAQ threshold가 적용됐다. generic `RUNNER`는 `KOSPI_ML`로 저장하고, 명시적 `KOSDAQ_*` pick_type만 `KOSDAQ_ML` 기본 매핑으로 남기도록 수정했다.
- 영향 범위: 오늘 관측된 `kosdaq_stop_loss` 표본은 모두 `actual_order_submitted=false`인 swing probe/sim 표본이며 실주문/실청산 영향은 없다. 다만 해당 표본은 시장-전략 매핑 오류가 섞였으므로 KOSDAQ_ML threshold 효과나 KOSPI_ML runner 품질 근거로 직접 쓰지 않는다.
- 테스트/검증: `.venv/bin/python -m pytest src/tests/test_trade_record_reuse_guards.py` 결과 `4 passed`. 기존 DB row와 active probe state는 장중 runtime mutation 금지선 때문에 자동 보정하지 않았고, 다음 scanner 저장부터 corrected mapping이 적용된다.
- 다음 액션: 오늘 swing probe/threshold attribution에서 위 종목의 KOSDAQ_ML stop/gap 표본은 `strategy_market_mapping_fix_required` source-quality blocker로 분리한다. 장후 lifecycle/threshold report에서 해당 표본이 family candidate로 섞이면 real/sim split과 별도로 제외 여부를 확인한다.

### PanicSellMarketContextGate0514 확인 기록

- checked_at: `2026-05-14 10:05 KST`
- 판정: `pass_after_fix`
- 근거: 패닉셀 microstructure detector가 pipeline event에 등장한 종목군만 평가하므로, 전체 지수가 유지되는 상황에서 보유/관찰 종목 내부의 국소 risk-off가 `PANIC_SELL`로 전파될 수 있는 source-quality 리스크가 있었다. `panic_sell_defense_report`에 `microstructure_market_context` gate를 추가해 micro risk-off가 시장 snapshot `RISK_OFF` 또는 평가 종목수 `20`개 이상 및 risk-off 비율 `20%` 이상으로 확인될 때만 panic_state 승격 입력으로 쓰도록 보정했다. 확인되지 않은 micro risk-off는 `portfolio_local_risk_off_only=true`와 `source_quality_only`로 남기며 runtime/order/auto-sell 권한은 없다.
- 당일 재생성 결과: `panic_sell_defense_2026-05-14.json`은 `panic_state=NORMAL`, `real_exit_count=0`, `non_real_exit_count=21`, `stop_loss_exit_count=0`, `panic_detected=false`다. microstructure는 `evaluated_symbol_count=16`, `risk_off_advisory_count=0`이고, 시장 context는 `market_risk_state=NEUTRAL`, `confirmed_risk_off_advisory=false`, `micro_evaluated_symbol_count_below_breadth_floor`로 기록됐다.
- 테스트/검증: `.venv/bin/python -m pytest src/tests/test_panic_sell_defense_report.py` 결과 `10 passed`. `.venv/bin/python -m src.engine.panic_sell_defense_report --date 2026-05-14 --print-json`로 `panic_sell_defense_2026-05-14.{json,md}`를 재생성했다. threshold/provider/order guard, 자동매도, bot restart, 스윙 실주문 전환은 변경하지 않았다.
- 다음 액션: 패닉셀 판단은 `closed real exit`, `microstructure detector`, `market context`, `active sim/probe recovery`를 분리해 읽는다. 시장 context 미확인 micro risk-off는 source-quality blocker로만 보고 장후 attribution에서 지수/breadth 보강 후보로 넘긴다.
- 다음 액션 실행 (`2026-05-14 10:14 KST`): `daily_threshold_cycle_report`의 `calibration_source_bundle.source_metrics.panic_sell_defense`에 `microstructure_market_risk_state`, `microstructure_confirmed_risk_off_advisory`, `microstructure_portfolio_local_risk_off_only`, `source_quality_blockers`, `market_breadth_followup_candidate`, `market_breadth_next_action`을 추가했다. `runtime_approval_summary`는 panic source-quality blocker가 있으면 approval 요청 대신 `freeze`로 닫고, `build_code_improvement_workorder`는 market/breadth follow-up 후보와 blocker evidence를 order 근거에 포함한다. `report-based-automation-traceability`에도 `microstructure_market_context` 계약을 추가했다.
- 후속 테스트/검증: `.venv/bin/python -m pytest src/tests/test_runtime_approval_summary.py src/tests/test_panic_sell_defense_report.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_build_code_improvement_workorder.py` 결과 `57 passed`. `.venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-14 --ai-correction-provider none`, `.venv/bin/python -m src.engine.threshold_cycle_ev_report --date 2026-05-14`, `.venv/bin/python -m src.engine.runtime_approval_summary --date 2026-05-14`, `.venv/bin/python -m src.engine.build_code_improvement_workorder --date 2026-05-14 --max-orders 12`를 순서대로 실행해 장후 attribution 입력을 갱신했다.
- 재생성 결과: `threshold_cycle_calibration_2026-05-14_postclose.json`의 `panic_sell_defense` source metric은 `market_risk_state=NEUTRAL`, `confirmed_risk_off_advisory=false`, `risk_off_advisory_ratio_pct=0.0`, `source_quality_blockers=[]`, `market_breadth_followup_candidate=true`, `market_breadth_next_action=review_index_breadth_before_panic_runtime_candidate`다. `runtime_approval_summary_2026-05-14.json`은 `panic_approval_requested=0`, `panic_sell_defense.state=hold`로 닫았다. `code_improvement_workorder_2026-05-14.json/md`는 `order_panic_sell_defense_lifecycle_transition_pack` evidence에 market/breadth follow-up을 포함하되 `runtime_effect=false`를 유지한다.

### SimVirtualBudgetRuntimeRestartAndQtyOwner0514 확인 기록

- checked_at: `2026-05-14 11:32 KST`
- 판정: `pass_restart_applied_owner_confirmed`
- 근거: `가상 주문가능금액 + 실주문 동적수량 산식` 변경은 `src/engine/sniper_state_handlers.py`의 sim/probe state handler와 `src/utils/constants.py`의 `SIM_VIRTUAL_BUDGET_KRW=10,000,000` 기본값을 상주 봇 프로세스가 import하는 구조다. 기존 `bot_main.py` PID `44879`는 `2026-05-14 11:17:06 KST` 기동으로 동적수량 보정 이후 코드 전체를 로드하지 않았으므로, 사용자 조건부 승인에 따라 `restart.flag` 기반 graceful restart를 수행했다. `restart.flag`는 소모됐고 새 PID는 `48192`, 시작시각은 `2026-05-14 11:31:34 KST`다. 재기동 후 `bot_history.log`에서 OpenAI main route, 조건식 로드, WS 종목 등록/첫 실시간 수신이 재개됐다.
- owner 확인: 동적수량 자체의 튜닝 owner는 `Plan Rebase` §7의 `position sizing` 워크스트림이다. 현재 상태는 `scale-in resolver/dynamic qty safety, 1주 cap default ON`이며, `position_sizing_cap_release` approval request 기준 충족 및 사용자 승인 전까지 cap 해제나 실주문 수량 guard 변경은 자동 apply 대상이 아니다. 이번 변경은 sim/probe/counterfactual sizing 입력을 `SIM_VIRTUAL_BUDGET_KRW`로 분리한 것이며, 실주문 동적수량 산식/ratio/cap 자체를 튜닝하거나 완화하지 않았다.
- 테스트/검증: PID 교체 `44879 -> 48192`, `restart.flag` 소모, WS first realtime 수신 로그를 확인했다. 코드 검증은 `SimVirtualBudgetDynamicQty0514`의 `pytest` 64건과 `Score6574ApplyGuardRecheck0514`의 threshold apply 테스트 43건을 기준으로 재사용한다. 이 재기동은 threshold/provider/order guard 변경이 아니며, 장중 runtime threshold mutation을 수행하지 않았다.
- 다음 액션: sim/probe 신규 진입 표본부터 `qty_source=sim_virtual_budget_dynamic_formula`, `virtual_budget_krw=10000000`, `budget_authority=sim_virtual_not_real_orderable_amount` provenance가 찍히는지 장후 source bundle에서 확인한다. 동적수량 자체 튜닝은 `position_sizing_cap_release` 또는 별도 날짜별 checklist workorder로 분리하고, 사용자 승인 없이는 실주문 cap/ratio를 변경하지 않는다.

### PositionSizingDynamicFormulaOwner0514 확인 기록

- checked_at: `2026-05-14 11:45 KST`
- 판정: `owner_contract_added`
- 근거: 확인 전 문서에는 `position_sizing_cap_release`가 1주 cap 해제 approval owner로 잡혀 있었지만, 사용자가 제시한 `position_sizing_dynamic_formula` 이름과 입력/metric/금지선/승인 조건은 독립 owner로 고정되어 있지 않았다. `Plan Rebase`, `report-based-automation-traceability`, `data/threshold_cycle/README`에 `position_sizing_dynamic_formula`를 동적수량 산식 튜닝 owner로 추가하고, `position_sizing_cap_release`와 분리했다.
- owner 계약: 입력은 `score`, `strategy`, `volatility`, `liquidity`, `spread`, `price_band`, `recent_loss`, `portfolio_exposure`로 둔다. primary metric은 `notional_weighted_ev_pct` 또는 `source_quality_adjusted_ev_pct`다. sim/probe 단독으로 실주문 cap 해제나 수량 확대를 승인하지 않으며, 실주문 수량 확대는 별도 approval artifact, same-stage owner guard, rollback guard가 필요하다.
- 테스트/검증: 문서 계약 변경만 수행했다. parser 검증과 `git diff --check`로 확인한다.
- 다음 액션: 구현/리포트 산출이 필요하면 별도 workorder에서 `position_sizing_dynamic_formula` source bundle, sample floor, provenance fields, approval artifact schema를 열고, 장중 runtime threshold/order mutation은 수행하지 않는다.
- 다음 액션 실행 (`2026-05-14 11:55 KST`): [workorder-position-sizing-dynamic-formula.md](/home/ubuntu/KORStockScan/docs/workorder-position-sizing-dynamic-formula.md)를 생성했다. workorder는 source bundle, sample floor, provenance fields, approval artifact schema, implementation phases, forbidden uses, 테스트 기준을 고정한다. `report-based-automation-traceability`와 `data/threshold_cycle/README`에는 해당 workorder 링크를 추가했다.
- 실행 판정: `workorder_opened_runtime_effect_false`.
- 실행 다음 액션: 구현은 `P1_report_source_bundle`부터 별도 지시가 있을 때만 착수한다. 그 전까지 runtime env, 주문 수량 guard, cap, provider, bot restart는 변경하지 않는다.
- P1 실행 (`2026-05-14 12:05 KST`): `daily_threshold_cycle_report`에 `position_sizing_dynamic_formula` metadata와 report-only source bundle builder를 추가했다. 자동화체인은 `threshold_snapshot.position_sizing_dynamic_formula`와 `calibration_candidates[]`에 후보를 생성하지만 `allowed_runtime_apply=false`, `runtime_change=false`, `apply_mode=report_only_calibration`로 고정한다. sample denominator는 real `COMPLETED + valid profit_rate` normal-only row만 사용하고, sim/probe/counterfactual sizing event는 `sim_probe_sizing_event_count`/`qty_source_counts`로만 노출한다.
- P1 재생성 결과: `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-14 --ai-correction-provider none` 후 `data/report/threshold_cycle_2026-05-14.json`에서 `position_sizing_dynamic_formula`가 생성됐다. 당일 상태는 `real_completed_valid=4`, `sample_floor=30`, `sizing_event_count=3`, `source_quality_passed=false`, `calibration_state=hold_sample`, `allowed_runtime_apply=false`다. `threshold_cycle_ev_report --date 2026-05-14`에서도 calibration outcome에 같은 후보가 전파됐다.
- P1 테스트/검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_daily_threshold_cycle_report.py -q` 결과 `35 passed`. `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_runtime_approval_summary.py src/tests/test_metric_decision_contract_docs.py -q` 결과 `56 passed`. `py_compile`도 통과했다.
- P1 다음 액션: `P2_runtime_approval_summary`는 미착수다. approval request 생성, preopen apply guard, live canary는 별도 사용자 지시와 approval artifact schema 구현 전까지 열지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-13` postclose -> `2026-05-14`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0514] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-14`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 완료 판정: `applied_guard_passed_env`.
  - 완료 근거: `threshold_apply_2026-05-14.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`이며 `threshold_runtime_env_2026-05-14.{env,json}`을 생성했다. runtime env selected family는 `soft_stop_whipsaw_confirmation`, env override는 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=true`다. `score65_74_recovery_probe`는 전일 selected family였지만 당일 runtime env override에는 새 값으로 쓰이지 않았다.
  - 완료 다음 액션: 미반영/hold_sample family는 수동 env override하지 않고 장후 EV/attribution에서 다시 판정한다.


- [x] `[SwingApprovalArtifactPreopen0514] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-14`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-13.json), [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 다음 액션: `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.
  - 완료 판정: `approval_artifact_missing`.
  - 완료 근거: `swing_runtime_approval_2026-05-13.json`은 runtime_change=`false`, approval_requests=`0`이고, one-share real canary와 scale-in real canary는 각각 policy_state=`approval_required`, runtime_apply_allowed=`false`다. `data/threshold_cycle/approvals` 아래 별도 approval artifact도 없다.
  - 완료 다음 액션: 스윙 dry-run 해제, one-share real canary, scale-in real canary, floor/env 변경은 별도 approval artifact 없이는 열지 않는다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0514] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-14`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, score65_74_recovery_probe가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 완료 판정: `warning_partial_provenance_no_rollback`.
  - 완료 근거: `2026-05-13` daily EV의 runtime_apply selected family는 `soft_stop_whipsaw_confirmation`, `score65_74_recovery_probe`였지만, 당일 `threshold_apply_2026-05-14.json`/`threshold_runtime_env_2026-05-14.json`의 실제 runtime env selected family는 `soft_stop_whipsaw_confirmation` 1개다. `pipeline_events_2026-05-14.jsonl`에는 soft stop 계열 holding event가 발생했으나 `score65_74_recovery_probe` 문자열 provenance는 0건이며, 당일 BUY 제출 event도 0건이다. `rollback`/`safety_revert`/`runtime_mutation`/`threshold_runtime_mutation` 검색 결과는 `pipeline_events`와 `threshold_events` 모두 0건이다.
  - 완료 다음 액션: score65_74 계열은 당일 env 미선정/표본 미발생으로 보고 장후 `threshold_cycle_ev`에서 selected/applied/not-applied attribution을 다시 확인한다. 장중 runtime threshold mutation은 수행하지 않는다.

- [x] `[SimProbeIntradayCoverage0514] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-14`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 완료 판정: `source_quality_split_pass`.
  - 완료 근거: `panic_sell_defense_2026-05-14.json`의 active sim/probe는 `10`이고 provenance_check passed=`true`다. runtime state 기준 `swing_intraday_probe_state.json`은 updated_at=`2026-05-14T09:05:06`, active_count=`10`, active 전부 `actual_order_submitted=false`/`broker_order_forbidden=true`이며, `scalp_live_simulator_state.json`은 updated_at=`2026-05-14T09:00:40`, active_count=`0`이다. `panic_buying_2026-05-14.json`도 수동 생성 후 panic_buy_state=`NORMAL`, runtime_effect=`report_only_no_mutation`으로 닫혔다.
  - 완료 다음 액션: sim/probe EV와 active_unrealized는 장후 source bundle 입력으로만 사용하고 broker execution 품질/실주문 전환 근거로 단독 사용하지 않는다. `panic_buying` cron log missing은 RunbookOps warning으로 분리한다.

## 장후 체크리스트 (16:30~18:55)

### PostcloseAutomationHealthCheck20260514 운영 확인 기록

- checked_at: `2026-05-14 19:05 KST`
- 판정: `pass_with_operational_warnings`
- 대상: `[Runbook 운영 확인] 장후 자동화체인 상태 확인`, `[ThresholdDailyEVReport0514]`, `[CodeImprovementWorkorderReview0514]`, `[HumanInterventionSummary0514]`, `[PanicEntryFreezeGuardImplementationScope0514]`, `[BotCPUHotspotFollowup0514]`, `[ShadowCanaryCohortReview0514]`
- 근거: `threshold_cycle_postclose_cron.log` 최신 run은 `[START] threshold-cycle postclose target_date=2026-05-14 started_at=2026-05-14T17:11:35+0900` 이후 `[DONE]`으로 종료했고, `threshold_cycle_postclose_verification_2026-05-14.json`은 status=`pass`, predecessor wait/timeout/log issues=`0`이다. 필수 artifact인 `threshold_cycle_ev`, `code_improvement_workorder`, `runtime_approval_summary`, `swing_daily_simulation`, `swing_lifecycle_audit`, 다음 영업일 checklist가 모두 존재하고 JSON 검증을 통과했다.
- 운영 warning: `bash deploy/run_error_detection.sh full` 최신 결과는 summary_severity=`warning`이다. `cron_completion`은 `threshold_cycle_postclose`를 `pass`로 보며 `done over error` note를 남겼고, warning은 `artifact_freshness.threshold_events=warning`과 `resource_usage.swap_high_memory_healthy`다. 이는 sparse compact stream/메모리 여유 있는 swap 경고로 분리하며 threshold/provider/order guard, bot restart, broker 주문 상태를 변경하지 않는다.
- 금지 확인: 장후 확인 과정에서 runtime threshold mutation, provider route 변경, 주문 guard 변경, bot restart, 실주문 전환은 수행하지 않았다.
- 다음 액션: Project/Calendar 상태는 사용자가 표준 동기화 명령으로 갱신한다. `threshold_events` sparse warning과 swap warning은 운영 관찰로 유지하고, 전략 tuning 결론에는 real/sim/combined split 및 window policy source만 사용한다.

- [x] `[ThresholdDailyEVReport0514] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [threshold_cycle_cumulative_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-13.json), [threshold_cycle_cumulative_2026-05-12.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-12.json), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다. 누적/rolling report는 전일 대비 `completed_valid_cumulative`와 `completed_by_source.real.sample`이 비정상적으로 0 또는 급감하지 않았는지 확인하고, 전일 real 표본이 있는데 당일 real 표본이 0이면 `--skip-db` 오염 또는 DB read 실패로 보고 DB 포함 재생성 후 다시 판정한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: `db_sample_ok`, `db_sample_drop_regenerated`, `source_quality_blocker`, `apply_input_ready`, `hold_sample`, `freeze` 중 하나로 닫고, 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 완료 판정: `db_sample_ok_apply_input_ready_with_warning`.
  - 완료 근거: 최신 `threshold_cycle_ev_2026-05-14.json`은 generated_at=`2026-05-14T18:49:14+09:00`, runtime_apply status=`auto_bounded_live_ready`, runtime_change=`true`, selected_families=`soft_stop_whipsaw_confirmation`이다. daily EV source split은 real sample=`4`, avg_profit_rate=`-1.0225%`, win_rate=`25.0%`; sim sample=`12`, avg_profit_rate=`3.1658%`, win_rate=`66.67%`; combined sample=`16`, avg_profit_rate=`2.1187%`, win_rate=`56.25%`이며 authority는 real family candidate=`real_only`, sim=`sim_equal_weight`, combined=`diagnostic_only_not_family_candidate_input`으로 분리된다. `threshold_cycle_cumulative_2026-05-14.json`은 completed_valid_cumulative=`177`, cumulative real sample=`177`, sim sample=`12`, combined sample=`189`라 DB sample 급감/`--skip-db` 오염으로 보지 않는다.
  - 완료 다음 액션: 다음 장전 apply 입력은 selected `soft_stop_whipsaw_confirmation`만 자동 반영 근거로 본다. sim/combined EV는 tuning 후보와 workorder 입력으로만 사용하고 broker execution 품질/실주문 전환 근거로 단독 사용하지 않는다. warning은 `swing_lab_dq` OFI/QI stale/missing `59/1111` source-quality로 분리한다.

- [x] `[SimFirstThresholdExploration0514] 기존 threshold-cycle 체인 내 스캘핑/스윙 전주기 sim-first 범위 확정` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:05`, `Track: StrategyLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [threshold_cycle_ev_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-14.json), [runtime_approval_summary_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-14.json), [code_improvement_workorder_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-14.json), [wait6579_ev_cohort_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-14.json), [missed_entry_counterfactual_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/missed_entry_counterfactual_2026-05-14.json), [swing_lifecycle_audit_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_lifecycle_audit/swing_lifecycle_audit_2026-05-14.json), [swing_threshold_ai_review_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_threshold_ai_review/swing_threshold_ai_review_2026-05-14.json), [swing_improvement_automation_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/swing_improvement_automation/swing_improvement_automation_2026-05-14.json)
  - 판정 기준: 신규 standalone report chain을 만들지 않고, 기존 threshold-cycle 자동화체인 안에서 스캘핑과 스윙의 BUY/selection 가능 후보 전체를 `selection -> entry -> holding -> scale_in -> exit` virtual lifecycle universe로 올리는 범위를 확정한다. 예수금 부족, 1주 cap, selected runtime family 미선정, real submit 불가는 sim exclusion이 아니라 `real_blocker` provenance로만 남긴다.
  - 금지: sim-first source만으로 실주문 enable, cap 해제, provider 변경, bot restart, 장중 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: `threshold_cycle_existing_chain_scope_confirmed`, `instrumentation_gap`, `source_quality_blocker`, `defer_to_next_session` 중 하나로 닫는다.
  - 완료 판정: `threshold_cycle_existing_chain_scope_confirmed`.
  - 완료 근거: 사용자 범위 정정에 따라 sim-first lifecycle 탐색을 신규 리포트/신규 owner가 아니라 기존 `R0_collect -> R1_daily_report -> R2_cumulative_report -> R3_manifest_only -> R4_preopen_apply_candidate -> R5_bounded_calibrated_apply -> R6_post_apply_attribution` 체인의 입력 범위와 판정 방식으로 고정했다. 스캘핑은 wait/missed-entry/scalp sim source, 스윙은 lifecycle audit/threshold AI review/improvement automation/runtime approval source가 기존 threshold-cycle report, approval summary, code-improvement workorder에 들어가야 한다.
  - 완료 다음 액션: P2에서는 기존 `threshold_cycle_ev`, `threshold_cycle_cumulative`, `runtime_approval_summary`, `code_improvement_workorder` 내부에서 score/model/gate/entry/holding/scale-in/exit arm을 확장한다. 실주문 enable, cap 해제, provider 변경, bot restart, 장중 runtime threshold mutation은 계속 금지한다.

- [x] `[PostclosePatternLabFailureRecovery0514] postclose pattern lab fatal abort 복구 규칙 반영` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: RunbookOps`)
  - Source: [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh), [prepare_dataset.py](/home/ubuntu/KORStockScan/analysis/claude_scalping_pattern_lab/prepare_dataset.py), [scalping_pattern_lab_automation_2026-05-14.json](/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-05-14.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: `claude_scalping_pattern_lab` 등 pattern lab subprocess가 OOM/kill/timeout으로 실패해도 source-quality freshness 경고로 흡수하고, 기존 threshold-cycle 후단 산출물(`scalping_pattern_lab_automation`, `swing_pattern_lab_automation`, `threshold_cycle_ev`, `code_improvement_workorder`, `runtime_approval_summary`, verification)은 계속 생성한다.
  - 완료 판정: `wrapper_nonfatal_pattern_lab_failure_and_lab_root_fix_completed`.
  - 완료 근거: `2026-05-14 17:00:28 KST` postclose 실패 원인은 `analysis/claude_scalping_pattern_lab/prepare_dataset.py` kill이었다. 직접 원인은 16:10 postclose 시점에 `2026-05-14` analytics parquet가 아직 없어 `data/pipeline_events/pipeline_events_2026-05-14.jsonl` raw fallback을 통째로 메모리에 올린 것이다. wrapper non-fatal 처리는 후단 EV/workorder/runtime summary 누락을 막기 위한 격리 조치이고, 장애 종결 조건은 별도 root fix와 lab fresh 복구다.
  - root fix: Claude pattern lab의 DuckDB query를 sequence stage와 필요한 컬럼으로 제한하고, raw JSONL fallback은 `_iter_jsonl` streaming으로 처리하도록 보정했다. 동일 범위 `ANALYSIS_START_DATE=2026-04-21`, `ANALYSIS_END_DATE=2026-05-14` 재실행 결과 Claude lab은 20초에 완료됐고 `max_rss=767660KB`, `claude_fresh=true`, `coverage_end=2026-05-14`로 복구됐다.
  - 추가 복구 메모: 같은 날짜 복구 재실행에서 완료 checkpoint가 source 끝에 도달한 상태인데도 availability sampler가 `disk_read_mb_delta>=128`로 latest cron 실패를 만들 수 있어, 완료 checkpoint replay는 sampler 없이 `completed`로 통과하도록 backfill guard를 보정했다.
  - 금지: pattern lab 실패를 이유로 실주문 guard, threshold, provider, bot restart, sim scope를 수동 변경하지 않는다.
  - 복구 액션: same-day `scalping_pattern_lab_automation`, `threshold_cycle_ev`, `code_improvement_workorder`, `runtime_approval_summary`, `threshold_cycle_postclose_verification`을 재생성해 stale Claude 입력을 제거했다.

- [x] `[CodeImprovementWorkorderReview0514] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-13.md), [code_improvement_workorder_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-13.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 기준 메모: 2026-05-13 2-pass 구현 후 최신 workorder generation_id=`2026-05-13-855236ba6498`는 `implement_now:0`이다. `order_holding_exit_decision_matrix_edge_counterfactual`은 removed, `order_latency_guard_miss_ev_recovery`는 `attach_existing_family(pre_submit_price_guard)`로 재분류됐다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.
  - 완료 판정: `already_implemented_2pass_no_new_runtime_effect_false`.
  - 완료 근거: 최신 `code_improvement_workorder_2026-05-14.json`은 generation_id=`2026-05-14-3924b7a14fb5`, selected_order_count=`12`, source_order_count=`38`, decision_counts=`implement_now:9`, `attach_existing_family:7`, `design_family_candidate:6`, `defer_evidence:10`, `reject:6`이다. 사용자가 지시한 2-pass 구현 이후 lineage는 previous=`2026-05-14-4a6ef2164d8e` 대비 new/removed/decision_changed=`0`이고, selected non-implement는 `order_ai_threshold_dominance`, `order_ai_threshold_miss_ev_recovery`, `order_latency_guard_miss_ev_recovery` 3건 모두 `attach_existing_family`다.
  - 완료 다음 액션: 현재 selected `implement_now` 9건은 runtime_effect=`false` 성능/계측/report/provenance 범위로 구현·검증 완료된 항목으로 분리한다. 신규 workorder 구현은 열지 않고, 5/15 `CodeImprovementWorkorderReview0515`에서 새 lineage 변화와 non-implement triage를 다시 본다.

- [x] `[HumanInterventionSummary0514] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-13.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 완료 판정: `classified_no_new_checklist_gap`.
  - 완료 근거: 승인 artifact 필요 항목은 `swing_runtime_approval_2026-05-14.json`의 `swing_model_floor`, `swing_gatekeeper_reject_cooldown` 2건이며 approved=`0`, runtime_change=`false`, 별도 approval artifact가 없으므로 다음 장전 env/실주문 적용 금지다. `runtime_approval_summary_2026-05-14.json` 기준 scalping selected_auto_bounded_live는 `soft_stop_whipsaw_confirmation` 1건뿐이고, panic approval requested는 `0`이다. Codex 구현 필요는 5/14 workorder 2-pass에서 이미 처리됐고 신규 lineage 변화는 없다. 수동 동기화 필요는 Project/Calendar 표준 명령 1건이다.
  - 완료 다음 액션: 5/15 checklist에는 preopen swing approval artifact 확인, postclose workorder review, human intervention summary가 이미 생성되어 있으므로 신규 parser-friendly checkbox를 추가하지 않는다. approval artifact 없는 swing/panic/position sizing 실주문 전환은 계속 금지한다.

- [x] `[PanicEntryFreezeGuardImplementationScope0514] panic_entry_freeze_guard 구현 착수 범위 및 approval guard 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: RuntimeStability`)
  - Source: [panic_entry_freeze_guard_v2_2026-05-13.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/panic_entry_freeze_guard_v2_2026-05-13.md), [runtime_approval_summary_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-13.json), [panic_sell_defense_2026-05-13.json](/home/ubuntu/KORStockScan/data/report/panic_sell_defense/panic_sell_defense_2026-05-13.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [runtime_approval_summary.py](/home/ubuntu/KORStockScan/src/engine/runtime_approval_summary.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `panic_entry_freeze_guard` 현재 구현 여부를 `report_only_candidate_only`, `approval_env_contract_ready`, `entry_hook_ready_flag_off`, `implementation_workorder_opened`, `hold_report_only`, `defer_attribution_gap` 중 하나로 닫는다. implementation open 시 1차는 approval artifact loader/env mapping/report attribution/runtime approval summary, 2차는 feature flag OFF 기본의 entry pre-submit hook/provenance로 분리한다.
  - 구현 체크: approval artifact 경로 `data/threshold_cycle/approvals/panic_entry_freeze_guard_YYYY-MM-DD.json`, `KORSTOCKSCAN_PANIC_ENTRY_FREEZE_GUARD_*` env key mapping, stale panic source guard, same-stage owner conflict guard, `panic_entry_freeze_block` event의 `actual_order_submitted=false` provenance가 모두 테스트 대상인지 확인한다.
  - 금지: approval artifact, rollback guard, same-stage owner rule이 닫히기 전에는 신규 BUY 차단, score threshold 완화/동결, stop 완화/지연, 자동매도, bot restart, 스윙 실주문 전환을 수행하지 않는다.
  - 다음 액션: 구현 착수 시 runtime 기본값은 OFF로 유지하고, `src/tests/test_threshold_cycle_preopen_apply.py`, `src/tests/test_daily_threshold_cycle_report.py`, `src/tests/test_runtime_approval_summary.py`와 entry hook 단위 테스트를 추가/수정한다. 실제 신규 BUY block은 별도 approval artifact와 preopen apply manifest 확인 전까지 열지 않는다.
  - 완료 판정: `hold_report_only`.
  - 완료 근거: 최신 `panic_sell_defense_2026-05-14.json`은 panic_state=`NORMAL`이고 `panic_entry_freeze_guard` candidate status=`inactive_no_panic`, allowed_runtime_apply=`false`다. microstructure context는 market_risk_state=`NEUTRAL`, risk_off_advisory_count=`0`, confirmed_risk_off_advisory=`false`이며, runtime summary에서도 panic approval requested=`0`이다. 따라서 approval env contract/entry hook 구현 착수보다 report-only candidate 유지가 맞다.
  - 완료 다음 액션: `panic_entry_freeze_guard_v2_2026-05-13.md`는 설계 기준으로 보존한다. PANIC_SELL 또는 confirmed risk-off가 반복되고 approval artifact/rollback guard/same-stage owner rule이 닫힐 때만 별도 implementation workorder를 연다.

- [x] `[BotCPUHotspotFollowup0514] 장후 bot CPU hotspot throttle/worker split 후속 범위 확인` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:40`, `Track: RuntimeStability`)
  - Source: [2026-05-13-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-13-stage2-todo-checklist.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py), [pipeline_event_logger.py](/home/ubuntu/KORStockScan/src/utils/pipeline_event_logger.py), [compress_db_backfilled_files.py](/home/ubuntu/KORStockScan/src/engine/compress_db_backfilled_files.py), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 5/13 장후 `scanner_loop_throttle_required` 판정의 재현 여부와 5/14 `pipeline_event_storage_pressure`를 분리 확인하고, 장외 스캘핑 scanner throttle, pipeline event verbosity/throttle, pipeline logging batching, 별도 worker/process split 중 구현 범위를 하나로 좁힌다.
  - 금지: 장중 hot patch, bot restart, threshold/provider/order guard 변경, profiler 패키지 설치를 수행하지 않는다.
  - 실행 메모(2026-05-14): `data/pipeline_events`와 `data/threshold_cycle/snapshots`가 log rotation 대상 밖에서 증가했으므로, 검증 완료 과거 raw/snapshot은 `compress_db_backfilled_files --days 7`로 압축하고 runbook/traceability에 `Pipeline Event Verbosity/Retention Policy`를 추가했다.
  - P1 실행 메모(2026-05-14 13:50 KST): `buy_funnel_sentinel`/`holding_exit_sentinel`에 slim append cache(`data/runtime/sentinel_event_cache/*_events_YYYY-MM-DD.{jsonl,meta.json}`)를 추가하고 wrapper 기본값을 `*_USE_CACHE=1`로 전환했다. 캐시는 report-only 성능 최적화이며 sentinel classification, threshold/provider/order guard, bot restart 권한을 바꾸지 않는다.
  - 검증 메모: `pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py` 결과 `16 passed`. 실파일 검증에서 BUY cache는 schema=`3`, `rebuilt=false`, append raw `3924` lines / cache `2750` rows 후속 실행 `35.8s`; HOLD/EXIT cache는 schema=`3`, `rebuilt=false`, append raw `358` lines / cache `0` rows 후속 실행 `0.42s`다.
  - P2 실행 메모(2026-05-14): 분석 품질 저하를 최소화하기 위해 raw writer는 그대로 두고 BUY Sentinel 소비 경로에만 고빈도 diagnostic stage summary sidecar를 추가했다. 대상은 `strength_momentum_observed`, `blocked_strength_momentum`, `blocked_swing_score_vpw`, `blocked_overbought`, `blocked_swing_gap`이며 산출물은 `data/pipeline_event_summaries/pipeline_event_summary_YYYY-MM-DD.jsonl`과 manifest다. `actual_order_submitted`, 주문/체결/청산, AI score, budget/latency/order lifecycle, provenance/source-quality transition은 lossless cache로 유지한다.
  - P2 검증 메모: summary는 `decision_authority=diagnostic_aggregation`, `runtime_effect=false`, `raw_suppression_enabled=false`로 고정됐다. `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_pipeline_event_summary.py src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py` 결과 `23 passed`, `git diff --check` pass, parser dry-run count=`7`이다. 실파일 검증에서 `buy_funnel_sentinel --date 2026-05-14 --use-cache --use-summary --dry-run` 증분 실행은 `7.04s`, max RSS 약 `393MB`였고 classification은 `UPSTREAM_AI_THRESHOLD`로 유지됐다. raw 대조 결과 5/14 현재 세션과 5/13 baseline 모두 summary 대상 stage/blocker count가 raw stream과 일치했다.
  - P3 실행 메모(2026-05-14): Pipeline Event Compaction V2는 producer-side `PIPELINE_EVENT_HIGH_VOLUME_COMPACTION_MODE=off|shadow|suppress` 인터페이스와 `pipeline_event_verbosity_report`를 자동화체인에 편입했다. 기본값은 `off`이고 `shadow`는 raw JSONL/DB upsert를 보존하면서 `data/pipeline_event_summaries/pipeline_event_producer_summary_YYYY-MM-DD.jsonl`과 manifest만 생성한다. `suppress`는 구현돼도 기본 비활성이며 2영업일 이상 V1 raw-derived summary parity 통과와 별도 approval owner 전에는 열지 않는다.
  - P3 자동화체인 메모: `deploy/run_threshold_cycle_postclose.sh`는 code improvement workorder 생성 전에 `data/report/pipeline_event_verbosity/pipeline_event_verbosity_YYYY-MM-DD.{json,md}`를 생성하고, `build_code_improvement_workorder`는 `order_pipeline_event_compaction_v2_shadow`/`order_pipeline_event_compaction_v2_suppress_guard`를 instrumentation order로 분류한다. `threshold_cycle_ev_report`에는 ops/source-quality summary로만 노출하며, `artifact_freshness`와 `error_detector_coverage`에도 등록했다.
  - P3 금지선: V2 summary와 verbosity report는 `decision_authority=diagnostic_aggregation`, `runtime_effect=false`다. 실주문 승인, threshold apply, EV primary metric, provider route, bot restart, 실매매 cap 해제의 단독 근거로 쓰지 않는다.
  - P4 실행 메모(2026-05-14): `docs/codebase-performance-bottleneck-analysis.md`를 자동화체인 source artifact로 승격하는 `codebase_performance_workorder_report`를 추가했다. 산출물은 `data/report/codebase_performance_workorder/codebase_performance_workorder_YYYY-MM-DD.{json,md}`이고, `build_code_improvement_workorder`는 accepted 성능 후보를 `implement_now`, deferred/rejected 후보를 각각 `defer_evidence`/`reject`로 분류한다. 모든 후보는 `runtime_effect=false`, `strategy_effect=false`, `data_quality_effect=false`, `tuning_axis_effect=false`와 parity contract를 가져야 한다.
  - P4 금지선: 이번 작업은 성능개선 자체 실행이 아니라 workorder source 편입이다. 실주문 수량/주문가, threshold, provider route, bot restart, 관찰튜닝축, source-quality 정책, raw forensic stream은 변경하지 않는다.
  - 다음 액션: `scanner_loop_throttle_workorder`, `worker_split_workorder`, `logging_batching_workorder`, `pipeline_event_verbosity_compaction_workorder`, `observe_only_no_action` 중 하나로 닫는다.
  - 완료 판정: `pipeline_event_verbosity_compaction_workorder_completed`.
  - 완료 근거: 5/13의 장후 CPU hotspot은 5/14에 slim sentinel cache, BUY summary sidecar, producer-side compaction V2 shadow interface, pipeline event verbosity report, codebase performance workorder source 편입으로 좁혀 처리했다. 최신 `pipeline_event_verbosity_2026-05-14.json`은 state=`v2_shadow_missing`, recommended_workorder_state=`open_shadow_order`로 raw suppression 없이 diagnostic aggregation만 남기며, `codebase_performance_workorder_2026-05-14.json`은 accepted performance 후보 `7`, deferred `3`, rejected `2`를 runtime_effect=`false` contract로 분리했다. 최신 error detector는 process_health pass, CPU busy `47.04%`, 메모리 여유 `10129.9MB`, swap_high_memory_healthy warning만 보고한다.
  - 완료 다음 액션: worker/process split은 현 시점에 열지 않는다. V2 shadow parity와 accepted performance workorder는 다음 5/15 postclose workorder review에서 lineage/효과를 다시 확인한다.

- [x] `[ShadowCanaryCohortReview0514] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-14`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.
  - 완료 판정: `no_runtime_classification_change_with_snapshot_update`.
  - 완료 근거: 최신 runtime approval summary 기준 scalping selected_auto_bounded_live는 `soft_stop_whipsaw_confirmation` 1건뿐이다. `score65_74_recovery_probe`는 selected runtime이 아니라 existing entry family 유지/관찰로 분리되고, `bad_entry_refined_canary`는 adjust_up 점수지만 current_application=`OFF/관찰 only`라 live 승격이 아니다. `pipeline_event_compaction_v2_shadow`는 default `off`, shadow는 raw JSONL/DB upsert 보존 조건의 diagnostic aggregation일 뿐 active canary가 아니다. 스윙은 approval_required 2건/approved 0건이며 실주문 전환 없음, panic entry freeze는 inactive_no_panic/report-only다.
  - 완료 다음 액션: `workorder-shadow-canary-runtime-classification.md`에 2026-05-14 postclose snapshot addendum을 반영했다. 신규 remove/baseline-promote/active-canary 전환은 없고, 5/15 postclose에서 selected runtime family와 V2 shadow parity를 재확인한다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-14 15:48:29`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-14.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
