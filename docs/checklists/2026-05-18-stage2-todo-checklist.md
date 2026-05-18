# 2026-05-18 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

### PreopenAutomationHealthCheck20260518 운영 확인 기록

- checked_at: `2026-05-18 08:50 KST`
- 판정: `pass`
- 대상: `[ThresholdEnvAutoApplyPreopen0518]`, `[OpenAIWSPreopenConfirm0518]`, `[SwingApprovalArtifactPreopen0518]`, `[Runbook 운영 확인] 장전 자동화체인 상태 확인`
- 근거: `logs/threshold_cycle_preopen_cron.log`에 `2026-05-18` preopen `[DONE]` marker가 있고, `threshold_apply_2026-05-18.json`은 status=`auto_bounded_live_ready`, apply_mode=`auto_bounded_live`, runtime_change=`true`, source_date=`2026-05-15`다. runtime env는 `threshold_runtime_env_2026-05-18.{env,json}`으로 생성됐고 selected family는 `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이다. env override는 `KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 포함한다.
- OpenAI WS: `src/run_bot.sh`는 startup env로 `KORSTOCKSCAN_SCALPING_AI_ROUTE=openai`, `KORSTOCKSCAN_OPENAI_TRANSPORT_MODE=responses_ws`, `KORSTOCKSCAN_OPENAI_RESPONSES_WS_ENABLED=true`를 고정하고, `openai_ws_stability_2026-05-15.md`는 decision=`keep_ws`, unique WS calls=`763`, WS fallback=`0/763`, endpoint counts=`analyze_target:762`, `entry_price:1`, entry_price instrumentation_gap=`False`로 닫혔다.
- swing approval: `swing_runtime_approval_2026-05-15.json`은 approval request 3건을 만들었고, 별도 approval artifact `data/threshold_cycle/approvals/swing_runtime_approvals_2026-05-15.json`과 `data/threshold_cycle/approvals/swing_one_share_real_canary_2026-05-15.json`이 존재한다. preopen apply는 `swing_gatekeeper_reject_cooldown`과 `swing_one_share_real_canary_phase0`만 env에 반영했고, `swing_model_floor`는 selected=`false`, decision_reason=`no_runtime_env_override`로 유지했다. `swing_scale_in_real_canary_phase0`는 scale-in approval artifact 없음으로 차단 상태다.
- runbook 운영 확인: `tmux bot` 세션은 `2026-05-18 07:40 KST`에 기동 상태이고, `src/run_bot.sh`는 오늘 runtime env 파일을 기다린 뒤 source하도록 되어 있다. `logs/ensemble_scanner.log`에는 `final_ensemble_scanner target_date=2026-05-18` `[DONE]` marker와 V2 CSV 3개 종목 적재 로그가 있다. `data/daily_recommendations_v2.csv`는 3행이며 diagnostics는 selected_count=`3`, selection_mode=`SELECTED`다.
- 금지 확인: 확인 과정에서 threshold/provider/order guard, 스윙 dry-run guard, bot restart, broker 주문 상태를 변경하지 않았다. OpenAI provider provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리했다.
- 다음 액션: 오늘 PREOPEN Project 항목은 완료로 닫는다. 장중에는 runtime threshold mutation 없이 selected family provenance, one-share real canary receipt, sim/probe `actual_order_submitted=false` split을 기존 INTRADAY checklist에서 계속 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### PanicSellNotificationOrderFix0518 확인 기록

- checked_at: `2026-05-18 09:35 KST`
- 판정: `fixed_report_only_notification`
- 근거: `logs/run_panic_sell_defense_cron.log`에서 `PANIC_SELL -> RECOVERY_CONFIRMED -> RECOVERY_WATCH -> RECOVERY_CONFIRMED -> RECOVERY_WATCH/PANIC_SELL` 전이가 짧은 간격으로 발생했고, 기존 notifier는 `RECOVERY_CONFIRMED`를 즉시 release로 보내 다음 `RECOVERY_WATCH`를 새 start로 보내는 구조였다. 이 때문에 사용자 수신 순서가 `패닉셀 경보 해제` 뒤 `패닉셀 주의`로 보일 수 있었다.
- 조치: `notify_panic_state_transition`에서 패닉셀 `RECOVERY_CONFIRMED` 1회 관측은 `release_pending`으로 보류하고, 다음 관측이 계속 `RECOVERY_CONFIRMED` 또는 `NORMAL`일 때만 해제 알림을 보내도록 수정했다. 다음 관측이 `RECOVERY_WATCH` 또는 `PANIC_SELL`이면 해제 알림 없이 active 상태를 유지한다.
- 금지 확인: 알림 hysteresis만 보정했고 panic report 판정, threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 다음 액션: 장중 panic sell defense 다음 cycle에서 `panic state Telegram notify status`가 `release_pending`, `no_transition`, `sent` 중 어떤 상태로 닫히는지 로그로 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### PanicSellRecoveryConfirmedSensitivityFix0518 확인 기록

- checked_at: `2026-05-18 09:45 KST`
- 판정: `fixed_report_only_state_gate`
- 근거: `RECOVERY_CONFIRMED`는 active sim/probe, post-sell rebound, microstructure recovery 중 하나만 만족해도 열릴 수 있었다. 오늘처럼 live market breadth `risk_off_advisory=true`와 market risk-off가 남아 있는 구간에서는 개별 microstructure `recovery_confirmed_count>0` 단독으로 경보 해제 성격의 `RECOVERY_CONFIRMED`를 여는 것이 과민했다.
- 조치: `panic_sell_defense_report`에서 `confirmed_risk_off_advisory=true` 또는 `market_panic_breadth_risk_off_advisory=true`가 남아 있으면 `micro_recovery_confirmed` 단독으로는 `RECOVERY_CONFIRMED`를 반환하지 않고 `RECOVERY_WATCH`로 제한하도록 보정했다. active sim/probe와 post-sell rebound 기반 confirmation은 기존 기준을 유지한다.
- 금지 확인: report-only 상태 판정 gate만 보정했고 threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 다음 액션: 다음 panic sell defense cycle에서 market risk-off가 유지되는 동안 `microstructure recovery confirmed but market risk-off remains` reason이 `RECOVERY_WATCH`로 라우팅되는지 확인한다.

### IntradayAutomationHealthCheck20260518 운영 확인 기록

- checked_at: `2026-05-18 09:41 KST`
- 판정: `pass_with_not_yet_due_subcheck`
- 대상: `[RuntimeEnvIntradayObserve0518]`, `[SimProbeIntradayCoverage0518]`, `[Runbook 운영 확인] 장중 자동화체인 상태 확인`
- 근거: `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.json`은 selected family=`bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이고 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 유지한다. `data/threshold_cycle/threshold_events_2026-05-18.jsonl`은 09:39 기준 fresh이며 `bad_entry_refined_candidate` 8건, `actual_order_submitted=False` 16건, rollback mention 0건을 기록했다. `soft_stop_whipsaw_confirmation`은 전일 checklist 원문 기준 selected로 적혀 있었지만 오늘 runtime env에는 포함되지 않았으므로 현재 장중 owner로 보지 않는다.
- sim/probe split: `data/pipeline_events/pipeline_events_2026-05-18.jsonl`은 09:40 기준 fresh이고 `actual_order_submitted=False` 1336건, `decision_authority=source_quality_only` 78827건을 기록했다. `scalp_sim_*`, `swing_probe_*`, `swing_sim_*`, `blocked_swing_*` stage가 관찰됐고 sim/probe는 real execution이나 broker order submit 근거로 사용하지 않았다.
- runbook 운영 확인: buy funnel sentinel, holding/exit sentinel, panic sell defense, panic buying은 09:40 전후 `[DONE]` marker와 fresh report를 생성했다. `panic_sell_defense_report --print-json`은 `panic_state=PANIC_SELL`, `runtime_effect=report_only_no_mutation`이고 `panic_buying_report --print-json`은 `panic_buy_state=NORMAL`, `runtime_effect=report_only_no_mutation`이다. `threshold_cycle_calibration_intraday`는 12:05~12:30 window 전이라 `not_yet_due`로 분리했다.
- 검증: `bash deploy/run_error_detection.sh full` 결과 summary_severity=`pass`, detector_count=`7`, `cron_completion`은 intraday calibration 등 미래 window를 `not_yet_due`로 분류했고 process/artifact/resource/lock detector는 pass였다.
- 금지 확인: 장중 threshold mutation, provider 변경, order guard 변경, bot restart, broker order submit, 스윙 dry-run guard 변경을 수행하지 않았다.
- 다음 액션: 12:05 이후 `threshold_cycle_calibration_intraday` `[DONE]` marker와 `threshold_cycle_ai_review_2026-05-18_intraday.md` 생성을 다시 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### SwingOneShareProbeAndSimulationMidcheck0518 확인 기록

- checked_at: `2026-05-18 09:48 KST`
- 판정: `pass_probe_env_allowed_but_dry_run_guarded`
- 대상: 스윙 1주 probe 허용 env 중간점검, 스캘핑/스윙 시뮬레이션 중간점검
- 스윙 1주 env: `threshold_runtime_env_2026-05-18.json`은 selected family=`swing_one_share_real_canary_phase0`를 포함하고 `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, allowed_codes=`000100,032830,136490`, max_qty=`1`, max_new_entries_per_day=`1`, max_open_positions=`3`, max_total_notional_krw=`300000`, require_approval_artifact=`true`를 선언한다. approval artifact `swing_one_share_real_canary_2026-05-15.json`은 approved=`true`, target_date=`2026-05-18`다.
- guard 판정: 같은 runtime env가 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 유지하므로, 1주 canary 허용은 승인/대상/한도 provenance 확인으로만 보고 스윙 live order 제출 허용으로 해석하지 않는다. 주문 로그 검색에서도 오늘 1주 canary 실주문 제출 증적은 확인되지 않았다.
- 스윙 probe/sim: `pipeline_events_2026-05-18.jsonl` 기준 swing 관련 stage는 `blocked_swing_score_vpw` 47704건, `blocked_swing_gap` 2690건, `swing_probe_discarded` 1301건, `swing_probe_entry_candidate` 25건, `swing_probe_holding_started` 25건, `swing_probe_exit_signal` 27건, `swing_probe_sell_order_assumed_filled` 27건, `swing_sim_scale_in_order_assumed_filled` 12건, `swing_probe_scale_in_order_assumed_filled` 12건이다. swing 관련 `actual_order_submitted=False`는 1621건이고, `runtime_effect`는 `in_memory_probe_only`/`counterfactual_only`/`in_memory_completed_only`로 분리됐다.
- 스캘핑 sim: `threshold_events_2026-05-18.jsonl` 기준 `scalp_sim_entry_ai_price_applied` 1건, `scalp_sim_entry_armed` 1건, `scalp_sim_buy_order_virtual_pending` 1건, `scalp_sim_buy_order_assumed_filled` 1건, `scalp_sim_holding_started` 1건, `scalp_sim_sell_order_assumed_filled` 1건, `scalp_sim_duplicate_buy_signal` 10건이다. `actual_order_submitted=False` 16건, `simulation_book=scalp_ai_buy_all`, `calibration_authority=equal_weight`, `budget_authority=sim_virtual_not_real_orderable_amount`가 유지됐다.
- 상태 파일: `data/runtime/swing_intraday_probe_state.json`은 updated_at=`2026-05-18T09:45:11`, open_count=`0`, completed_count=`0`로 저장됐다. 장중 event stream에는 과거 복원/폐기/assumed fill provenance가 있지만 현재 상태 파일에는 active probe가 없다.
- 검증: `bash deploy/run_error_detection.sh full` 결과 summary_severity=`pass`, detector_count=`7`, process/artifact/resource/lock detector는 pass이고 `threshold_cycle_calibration_intraday`, `swing_live_dry_run_status` 등 미래 window는 `not_yet_due`로 분리됐다.
- 금지 확인: 장중 threshold mutation, 스윙 dry-run guard 변경, 실주문 cap 해제, broker order submit, provider 변경, bot restart를 수행하지 않았다.
- 다음 액션: 15:45 이후 `swing_live_dry_run_status`와 장후 `swing_lifecycle_audit`에서 1주 canary 대상 코드별 selected/blocked/receipt provenance를 다시 확인한다. 스캘핑/스윙 sim 손익은 장후 `threshold_cycle_ev`의 real/sim/combined split에서만 판정한다.

### ScalpingSimEVMidcheck0518 확인 기록

- checked_at: `2026-05-18 09:54 KST`
- 판정: `warning_hold_sample_negative_ev`
- 대상: 스캘핑 `scalp_ai_buy_all` sim EV 중간점검
- EV 표본: `threshold_events_2026-05-18.jsonl` 기준 `scalp_sim_sell_order_assumed_filled` completed 표본은 1건이며, 종목은 `이수화학(005950)`, `profit_rate=-2.54`다. `COMPLETED + valid profit_rate`만 EV 표본으로 인정했고 open/pending/duplicate context는 EV에서 제외했다.
- metric: `equal_weight_avg_profit_pct=-2.54`, `simple_sum_profit_pct=-2.54`, `diagnostic_win_rate_pct=0.0`, completed_count=`1`, duplicate_signal_count=`10`, active_or_pending_context_count=`3`이다. 표본 1건이므로 hard fail/pass가 아니라 `hold_sample` 성격의 negative 중간 관찰로 둔다.
- provenance: 스캘핑 sim event 16건 모두 `actual_order_submitted=False`이고, `simulation_book=scalp_ai_buy_all`, `calibration_authority=equal_weight`, `budget_authority=sim_virtual_not_real_orderable_amount`, `fill_source=best_ask`, `would_limit_fill=False`가 확인됐다. 이는 broker execution 품질이나 실주문 전환 근거가 아니다.
- Sentinel context: `buy_funnel_sentinel_2026-05-18.json`은 primary=`UPSTREAM_AI_THRESHOLD`, `holding_exit_sentinel_2026-05-18.json`은 primary=`HOLD_DEFER_DANGER`/secondary=`AI_HOLDING_OPS`로 fresh하게 생성됐지만 둘 다 `live_runtime_effect=false`이며 threshold/order/bot 변경 권한이 없다.
- 검증: `bash deploy/run_error_detection.sh full` 결과 summary_severity=`pass`, detector_count=`7`, process/artifact/resource/lock detector는 pass이고 `threshold_cycle_calibration_intraday`, postclose reports 등 미래 window는 `not_yet_due`로 분리됐다.
- 금지 확인: 장중 threshold mutation, score threshold 완화, fallback 재개, order guard 변경, provider 변경, bot restart, broker order submit을 수행하지 않았다.
- 다음 액션: 12:05 이후 intraday calibration이 생성되면 현재 negative sim 표본이 source-quality/coverage warning으로만 라우팅되는지 확인한다. 최종 EV 판정은 장후 `threshold_cycle_ev_2026-05-18`의 real/sim/combined split에서 completed 표본만으로 다시 닫는다.

### ScalpSimPostSellMFEInstrumentation0518 구현 기록

- checked_at: `2026-05-18 10:25 KST`
- 판정: `implemented_report_only_sim_post_sell_join`
- 근거: `scalp_sim_sell_order_assumed_filled` 표본을 실주문 `post_sell_candidates/evaluations`와 분리해 `sim_post_sell_candidates/evaluations`에 기록하도록 구현했다. 2026-05-18 이수화학(005950) 표본은 `sim_record_id=SCALPSIM-005950-1779063285868-171e63`, `profit_rate=-2.54`, `actual_order_submitted=false`, `broker_order_forbidden=true`로 backfill/evaluate 됐다. `threshold_cycle_ev`의 `scalp_simulator.post_sell_join`은 `joined_completed=1`, `pending_completed=0`, 10분 기준 `GOOD_EXIT`, `mfe_10m=-0.475`, `mae_10m=-4.179`, `close_10m=-2.754`를 노출한다. 단, 30분/60분 forward에서는 `mfe_30m=3.324`, `mfe_60m=8.927`로 장후 long-horizon rebound forensic 확인 대상이다.
- 영향도: 기존 real `post_sell_feedback` 파일과 DB/주문/threshold/provider 경로는 변경하지 않았다. postclose wrapper는 compact threshold event 수집 직후 sim post-sell backfill/evaluate를 수행하고, `daily_threshold_cycle_report`/`threshold_cycle_ev`가 join summary를 읽는다. pattern lab과 code-improvement workorder는 EV summary를 통해서만 간접 소비하며 runtime mutation 권한은 없다.
- 다음 액션: 장후 `[ScalpSimPostSellMFECheck0518]`에서 10m GOOD_EXIT와 30m/60m rebound를 분리해 `good_cut_after_rebound_check` 또는 `mfe_positive_missed_upside_long_horizon`으로 닫는다.

### PanicSellNotificationDebounce0518 추가 보정 기록

- checked_at: `2026-05-18 11:35 KST`
- 판정: `fixed_report_only_notification_debounce`
- 근거: 사용자 수신 순서가 `경보해제 -> 경보 -> 경보해제`로 다시 뒤집힌 것은 notifier가 `RECOVERY_CONFIRMED`만 1회 보류하고 `NORMAL`은 active 직후 즉시 release로 발송했기 때문이다. panic sell intraday job은 봇 프로세스가 아니라 cron wrapper가 매번 새 Python 프로세스로 실행하는 report-only notifier이므로 봇 재기동 대상이 아니다.
- 조치: `notify_panic_state_transition`에서 `PANIC_SELL/RECOVERY_WATCH` active 상태 다음에 오는 모든 release 상태(`NORMAL`, `RECOVERY_CONFIRMED`)를 1회 `release_pending`으로 보류하도록 수정했다. 다음 cycle도 release 상태이면 그때만 `패닉셀 경보 해제`를 보내고, 중간에 다시 `PANIC_SELL/RECOVERY_WATCH`가 오면 추가 경보/해제 없이 active 상태를 유지한다.
- 금지 확인: Telegram 알림 debounce만 보정했고 panic report 판정, threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_notify_panic_state_transition.py src/tests/test_panic_sell_defense_report.py` 통과 (`18 passed`). `py_compile`, `bash -n deploy/run_panic_sell_defense_intraday.sh`, `git diff --check` 통과.
- 다음 액션: 다음 panic sell defense cycle에서 `panic state Telegram notify status=release_pending|no_transition|sent` 순서를 확인한다. 동일 현상이 반복되면 report state 자체의 `NORMAL/PANIC_SELL` bounce를 source-quality incident로 분리한다.

### PanicSellMarketBreadthWatch0518 추가 보정 기록

- checked_at: `2026-05-18 11:50 KST`
- 판정: `fixed_report_only_market_breadth_watch`
- 근거: `market_panic_breadth_2026-05-18.json`은 KOSDAQ 하락과 업종 breadth 악화로 `risk_off_advisory=true`였지만, `panic_sell_defense_2026-05-18.json`의 microstructure detector는 `risk_off_advisory_count=0`, `panic_signal_count=0`, `max_panic_score=0.366`였고 실현 손절 cluster도 없었다. 따라서 코스닥/업종 breadth-only 경고를 `PANIC_SELL`로 단정하는 것은 과했다.
- 조치: `panic_sell_defense_report`에서 `confirmed_micro_risk_off_advisory`와 시장 breadth 포함 `confirmed_risk_off_advisory`를 분리했다. 시장 breadth-only risk-off이고 micro panic/손절 cluster가 없으면 `PANIC_SELL`이 아니라 `RECOVERY_WATCH`/`STABILIZING`으로 라우팅하고, Telegram 문구도 `시장 breadth risk-off 주의`로 구분하도록 보정했다.
- 금지 확인: report-only 판정/알림 문구만 보정했고 threshold/provider/order guard, 자동매도, bot restart, broker 주문 상태는 변경하지 않았다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_panic_sell_defense_report.py src/tests/test_notify_panic_state_transition.py` 통과 (`19 passed`). `py_compile`, `git diff --check` 통과. `panic_sell_defense_report --date 2026-05-18 --print-json` 재생성 결과 저장 JSON은 `panic_state=RECOVERY_WATCH`, `panic_regime_mode=STABILIZING`, `confirmed_micro_risk_off_advisory=false`, `market_panic_breadth_risk_off_advisory=true`로 닫혔다.
- 다음 액션: 다음 intraday panic sell defense cycle에서 동일 시장 breadth-only 상황이 `PANIC_SELL` 경보가 아니라 breadth 주의 또는 release-pending 흐름으로 발송되는지 로그를 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### MarketPanicBreadthWeightedComposite0518 추가 보정 기록

- checked_at: `2026-05-18 12:05 KST`
- 판정: `implemented_report_only_weighted_composite`
- 근거: 기존 `market_panic_breadth_collector`는 KOSPI/KOSDAQ 중 더 나쁜 지수 변화율(`min_index_change`)과 시장별 하락 종목 비율 최댓값(`max_stock_fall_ratio`)을 사용해 한 시장만 급락해도 `risk_off_advisory=true`가 될 수 있었다. 이는 코스닥 단독 하락을 시장 전체 패닉으로 과대 해석할 위험이 있다.
- 조치: KOSPI/KOSDAQ index change는 기본 weight `KOSPI=0.65`, `KOSDAQ=0.35`로 weighted composite을 만들고, 시장별 stock fall/rise ratio는 listed count가 있으면 listed count, 없으면 기본 market weight로 병합하도록 수정했다. 전체 composite 조건을 충족하지 못한 단일시장 악화는 `single_market_risk_off_advisory=true`로 별도 노출하고, `risk_off_advisory`는 전체 시장 패닉 근거로만 유지한다.
- 영향도: `panic_sell_defense_report`와 `panic_buying_report`는 weighted composite `risk_off_advisory`/`risk_on_advisory`만 시장 전체 confirmation으로 소비하고, single-market advisory는 source-quality/운영 주의 필드로만 노출한다. threshold/provider/order guard, 자동매수/자동매도, bot restart 권한은 없다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_market_panic_breadth_collector.py src/tests/test_panic_sell_defense_report.py src/tests/test_panic_buying_report.py src/tests/test_notify_panic_state_transition.py` 통과 (`31 passed`). `py_compile`, `git diff --check` 통과. 2026-05-18 report 재생성 결과 `market_panic_breadth.risk_off_advisory=false`, `single_market_risk_off_advisory=true`, weighted index change=`-0.091`, weighted stock fall ratio=`68.288`로 전체 패닉 threshold 미달이며, `panic_sell_defense`는 `panic_state=NORMAL`, `panic_regime_mode=NORMAL`로 닫혔다.
- 다음 액션: 다음 intraday cycle에서 KOSPI/KOSDAQ 중 한쪽만 악화된 경우 `single_market_risk_off_advisory`로만 노출되고 `PANIC_SELL`로 승격되지 않는지 로그와 Telegram transition state를 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### ApprovalArtifactRunbookProcedure0518 문서 보강 기록

- checked_at: `2026-05-18 12:20 KST`
- 판정: `documented_manual_approval_gate`
- 근거: approval request는 `swing_runtime_approval`/`runtime_approval_summary`/다음 영업일 checklist에 표면화되지만, `신규 Code Improvement Order 처리 절차`처럼 사람이 approval artifact 생성 여부를 판단하는 독립 절차가 런북에 없었다. 이로 인해 스윙 1주 real canary 같은 승인 요청이 code workorder와 같은 수동 triage 대상인지 불명확했다.
- 조치: `time-based-operations-runbook.md`에 `신규 Approval Artifact 처리 절차`를 추가해 intake artifact, 확인 필드, 사람 승인 판정, artifact JSON 형식, 다음 PREOPEN 확인, checklist/Project 반영 기준을 분리 명시했다. `build_next_stage2_checklist`의 `HumanInterventionSummary`도 `approval_artifact_required|created|missing|blocked_by_policy|observe_only` 분류와 approval id/artifact path/PREOPEN 확인 항목을 남기도록 보강했다.
- 금지 확인: 문서/체크리스트 생성 문구만 보강했고 approval artifact를 생성하거나 env 파일, threshold/provider/order guard, broker 주문 상태를 변경하지 않았다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_build_next_stage2_checklist.py src/tests/test_build_codex_daily_workorder.py` 통과 (`19 passed`). `py_compile`, `git diff --check`, `sync_docs_backlog_to_project --dry-run` 통과. `test_sync_docs_backlog_to_project.py` 전체 실행은 기존 prompt/scalping 문서 파싱 기대값 불일치 5건으로 실패했으며 이번 변경과 직접 관련된 실패는 아니다.
- 다음 액션: 오늘 POSTCLOSE `HumanInterventionSummary0518`에서 approval request가 있으면 새 절차 기준으로 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 확인 항목을 분리 보고한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.
- 추가 명확화 (`2026-05-18 12:30 KST`): `Approval Artifact 작성 형식` 제목을 `현재 지원되는 Approval Artifact 작성 형식`으로 바꾸고, 런북의 3개 artifact 형식은 단순 예시가 아니라 `threshold_cycle_preopen_apply`가 현재 소비하는 형식임을 명시했다. panic/position sizing 등 `approval_contract_missing` 축은 artifact loader/env mapping/runtime guard/rollback test 구현 전에는 approval artifact를 만들어도 소비되지 않는다고 분리했다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-05-15` postclose -> `2026-05-18`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ThresholdEnvAutoApplyPreopen0518] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 판정: `applied_guard_passed_env`.
  - 근거: `threshold_apply_2026-05-18.json` status=`auto_bounded_live_ready`, runtime env selected families=`bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`; `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true` 유지.

- [x] `[OpenAIWSPreopenConfirm0518] OpenAI WS 유지 설정 및 entry_price/analyze_target provenance 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: RuntimeStability`)
  - Source: [openai_ws_stability_2026-05-15.md](/home/ubuntu/KORStockScan/data/report/openai_ws/openai_ws_stability_2026-05-15.md), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py)
  - 판정 기준: startup env의 OpenAI route/Responses WS 설정과 `analyze_target`, `entry_price` transport provenance를 분리 확인한다.
  - 금지: provider transport 확인을 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경으로 해석하지 않는다.
  - 다음 액션: entry_price transport 표본이 부족하면 장중 표본 재확인 항목과 연결한다.
  - 판정: `pass_keep_ws`.
  - 근거: startup env는 OpenAI Responses WS 고정이고, `openai_ws_stability_2026-05-15.md`는 decision=`keep_ws`, analyze_target=`762`, entry_price=`1`, WS fallback=`0/763`, entry_price instrumentation_gap=`False`.

- [x] `[SwingApprovalArtifactPreopen0518] 스윙 approval request 및 별도 승인 artifact 존재 여부 확인` (`Due: 2026-05-18`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: RuntimeStability`)
  - Source: [swing_runtime_approval_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-15.json), [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: approval request가 있더라도 사용자 승인 artifact가 없으면 env apply 대상이 아니다.
  - 금지: 스윙 dry-run 해제, real canary, floor, scale-in real canary를 서로 자동 승인하지 않는다.
  - 사용자 승인 요청/승인 현황 표면화: `swing_model_floor` approval_id=`swing_runtime_approval:2026-05-15:swing_model_floor`, `swing_gatekeeper_reject_cooldown` approval_id=`swing_runtime_approval:2026-05-15:swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0` approval_id=`swing_one_share_real_canary:2026-05-15:phase0`는 사용자 승인 artifact 생성 완료 상태로 확인한다.
  - 다음 액션: 최종 보고에 `사용자 승인 필요/승인 완료` 섹션을 별도로 쓰고, 각 approval_id, artifact path, selected env, blocked reason을 `approval_artifact_present`, `approval_artifact_missing`, `blocked_by_policy` 중 하나로 닫는다.
  - 판정: `approval_artifact_present`.
  - 근거: `swing_runtime_approvals_2026-05-15.json`과 `swing_one_share_real_canary_2026-05-15.json`이 존재한다. preopen apply는 `swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0`를 selected env로 반영했고 `swing_model_floor`는 selected=`false`/`no_runtime_env_override`, scale-in real canary는 approval artifact 없음으로 차단했다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RuntimeEnvIntradayObserve0518] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-05-18`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.
  - 판정: `pass_current_runtime_env_provenance`.
  - 근거: 오늘 runtime env selected family는 `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이며, `soft_stop_whipsaw_confirmation`은 현재 env owner가 아니다. threshold event stream에는 `bad_entry_refined_candidate` 8건과 rollback mention 0건이 확인됐다.

- [x] `[SimProbeIntradayCoverage0518] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-05-18`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.
  - 판정: `pass_sim_probe_split_preserved`.
  - 근거: pipeline events 기준 `actual_order_submitted=False` 1336건, threshold events 기준 `actual_order_submitted=False` 16건이 확인됐고, `decision_authority=source_quality_only`와 report-only/runtime_effect split이 유지됐다.

## 장후 체크리스트 (16:30~18:55)

- [ ] `[ThresholdDailyEVReport0518] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[ScalpSimPostSellMFECheck0518] 이수화학 scalp sim 손절 후 급등 MFE/MAE join 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: ScalpingLogic`)
  - Source: [threshold_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-18.jsonl), [sim_post_sell_candidates_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-18.jsonl), [sim_post_sell_evaluations_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-18.jsonl), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py)
  - 판정 기준: `이수화학(005950)` `scalp_sim_sell_order_assumed_filled` profit_rate=`-2.54` 표본이 post-sell 10m MFE/MAE 또는 missed-upside proxy와 record/sim id로 연결되는지 확인한다.
  - 금지: 단일 sim 표본 또는 HTS 육안 관찰만으로 stop/threshold/order guard를 장중 변경하지 않는다.
  - 다음 액션: `post_sell_joined`, `sim_post_sell_gap`, `mfe_positive_missed_upside`, `good_cut_after_rebound_check`, `instrumentation_gap` 중 하나로 닫는다.
  - 구현 메모: sim 청산 표본은 실주문 `post_sell_candidates/evaluations`와 분리해 `sim_post_sell_candidates/evaluations`로 기록하고, postclose wrapper가 compact event 수집 직후 backfill/evaluate를 수행하도록 갱신했다. `threshold_cycle_ev`는 `scalp_simulator.post_sell_join` 요약을 노출한다.

- [ ] `[CodeImprovementWorkorderReview0518] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-15.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-15.md), [code_improvement_workorder_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-15.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.

- [ ] `[HumanInterventionSummary0518] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 최종 사용자 보고에 `승인 필요/승인 완료`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`을 별도 소제목으로 풀어 쓰고, approval request가 있으면 항목별 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 여부를 반드시 노출한다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[ShadowCanaryCohortReview0518] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
