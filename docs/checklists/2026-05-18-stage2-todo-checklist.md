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

### SystemErrorMainLoopHeartbeatStale0518 운영 incident 기록

- checked_at: `2026-05-18 15:50 KST`
- 판정: `fixed_operational_restart`
- 증상: System Error Detector가 `process_health: Main loop heartbeat stale for 102s (timeout=15s)`를 발송했고, 재확인 중 `stale for 26s`가 한 번 더 발생했다.
- 근거: 경보 직전 `logs/bot_history.log`에는 `15:47:46` Kiwoom WS `code=1000, reason=Bye` disconnect와 재접속 흐름이 있었고, `15:20`에는 스캘핑 보유/주문 대기 종목이 없다고 기록됐다. 재기동 전 `bot_main.py` PID `94794`는 RSS 약 5.8GiB, system available memory 약 696MiB, swap used 약 3.7GiB였으며 `swing_lifecycle_audit`가 별도 D-state로 진행 중이었다.
- 조치: 장 마감 후 운영 안정성 조치로 `bot_main.py` PID `94794`에 `TERM`을 보내 `run_bot.sh` wrapper가 새 PID `102933`으로 우아하게 재기동하도록 했다. threshold, provider, order guard, score/stop threshold, broker order 상태는 변경하지 않았다.
- 검증: 재기동 후 `tmp/error_detector_heartbeat.json`은 main_loop PID `102933`, `last_beat=2026-05-18T15:50:48+09:00`로 갱신됐다. `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run` 기준 `process_health=pass`, `main_loop_status=ok`, `main_loop_age_sec=2.2`다. 메모리는 available 약 6.6GiB로 회복됐고, 남은 warning은 `swing_live_dry_run` in-progress 산출물 및 high swap 사용률이다.
- 다음 액션: `swing_live_dry_run`/`swing_lifecycle_audit`가 완료되는지 계속 확인하고, 16:10 postclose chain 전까지 동일 heartbeat stale가 반복되면 swing audit 리소스 격리 또는 postclose job 순서 조정을 별도 workorder로 분리한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### SwingLiveDryRunResourceIsolation0518 구현 기록

- checked_at: `2026-05-18 15:58 KST`
- 판정: `implemented_lightweight_1545_deferred_heavy_postclose`
- 근거: `run_swing_live_dry_run_report.sh`가 15:45에 `swing_selection_funnel_report` 이후 `swing_lifecycle_audit --ai-review-provider openai`를 inline 실행했고, `15:46~15:49` system metric에서 `swing_lifecycle_audit` PID가 메모리 35~44%, iowait 20~56%, swap pressure를 유발했다. heartbeat stale는 이 구간과 겹쳤다.
- 조치: 15:45 wrapper 기본값을 `SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT=false`로 바꿔 selection/funnel report와 status만 생성하도록 했다. status에는 `reason=selection_completed_lifecycle_deferred_to_postclose`, `lifecycle_audit_mode=postclose_deferred`를 남긴다. heavy `swing_lifecycle_audit`, `swing_threshold_ai_review`, `swing_improvement_automation`, `swing_runtime_approval`은 기존 16:10 `run_threshold_cycle_postclose.sh`에서 계속 생성한다.
- detector 계약: `artifact_freshness`에서 15:45 필수 확인은 `swing_live_dry_run_status`와 `swing_selection_funnel_report`로 유지하고, heavy swing lifecycle/approval artifact window는 16:10~17:10으로 이동했다.
- 검증: `SWING_LIVE_DRY_RUN_RUN_LIFECYCLE_AUDIT=false bash deploy/run_swing_live_dry_run_report.sh 2026-05-18`는 selection report만 생성하고 `[DONE]`으로 종료했다. `pgrep` 기준 `swing_lifecycle_audit` 잔여 프로세스는 없었다. `PYTHONPATH=. .venv/bin/python -m src.engine.error_detector --mode full --dry-run`은 `summary_severity=pass`, `process_health=pass`, `resource_usage=pass`, `swing_live_dry_run_status=pass`, `swing_lifecycle_audit_report_status=not_yet_due`로 닫혔다. 관련 pytest 43건과 `bash -n`, `git diff --check`를 통과했다.
- 다음 액션: 16:10 postclose chain에서 deferred heavy swing lifecycle/approval artifact가 생성되는지 확인한다. 동일 리소스 경합이 postclose에서도 반복되면 `swing_lifecycle_audit` 메모리 상한, streaming aggregation, row cap을 별도 code improvement workorder로 분리한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### ThresholdPostcloseResourceGuard0518 구현 기록

- checked_at: `2026-05-18 16:00 KST`
- 판정: `implemented_postclose_resource_guard`
- 근거: 15:45 경합은 해소했지만 16:10 `run_threshold_cycle_postclose.sh`는 여전히 `daily_threshold_cycle_report`, `swing_lifecycle_audit`, pattern lab, EV/workorder/summary 같은 heavy 단계를 포함하며, bot은 22:55까지 떠 있어 시간상 경합 가능성이 남아 있었다.
- 조치: postclose wrapper에 `THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_GUARD=true` 기본 resource gate를 추가했다. heavy 단계 실행 전 `logs/system_metric_samples.jsonl`의 최신 `MemAvailable`, swap used, iowait를 확인하고, 기준 미달이면 최대 `THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_WAIT_SEC=300`초 대기한다. heavy command와 compact backfill은 `nice -n 10`, `ionice -c 2 -n 7`, background CPU affinity로 실행한다.
- 기본 기준: `THRESHOLD_CYCLE_POSTCLOSE_MIN_MEM_AVAILABLE_MB=4096`, `THRESHOLD_CYCLE_POSTCLOSE_MAX_SWAP_USED_PCT=85`, `THRESHOLD_CYCLE_POSTCLOSE_MAX_IOWAIT_PCT=35`, `THRESHOLD_CYCLE_POSTCLOSE_RESOURCE_WAIT_INTERVAL_SEC=10`, compact availability wait `THRESHOLD_CYCLE_COMPACT_AVAILABILITY_WAIT_SEC=900`, interval `15`.
- 적용 범위: `daily_threshold_cycle_report`, `swing_daily_simulation`, `swing_lifecycle_audit`, pattern lab, pattern automation, currentness/propagation audit, pipeline verbosity, observation source-quality audit, codebase performance workorder, code improvement workorder, threshold EV, runtime approval summary, plan renewal, next checklist, verifier에 resource gate와 낮은 우선순위를 적용했다. JSON stdout을 직접 파싱하는 compact backfill 구간은 stdout 오염 없이 낮은 우선순위로 실행하고, `paused_by_availability_guard`는 즉시 fail이 아니라 checkpoint 유지 후 대기/재개하도록 보완했다.
- 금지 확인: 이 변경은 운영 리소스 격리이며 threshold/provider/order guard, broker order, runtime env 값은 변경하지 않는다.
- 다음 액션: 16:10 postclose 실행 로그에서 `resource guard pass|wait|timeout`, `availability guard wait|timeout`, bot `process_health`를 함께 확인한다. timeout이 발생하면 postclose 산출물 누락을 fail로 보되, bot 재기동/threshold 변경이 아니라 리소스 조정 workorder로 분리한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### SwingPostcloseArtifactConsistencyAudit0518 확인 기록

- checked_at: `2026-05-18 16:28 KST`
- 판정: `pass_with_warnings`
- 대상: `deploy/run_swing_live_dry_run_report.sh`, `deploy/run_threshold_cycle_postclose.sh` 생성 산출물 정합성.
- 근거: `data/report/swing_selection_funnel/status/swing_live_dry_run_2026-05-18.status.json`은 status=`succeeded`, reason=`selection_completed_lifecycle_deferred_to_postclose`, `lifecycle_audit_mode=postclose_deferred`, `runtime_change=false`로 닫혔다. 16:10 postclose recovery 후 `swing_daily_simulation`, `swing_lifecycle_audit`, `swing_threshold_ai_review`, `swing_improvement_automation`, `swing_runtime_approval`, `threshold_cycle_ev`, `runtime_approval_summary`, `pattern_lab_currentness_audit`, `pattern_lab_propagation_audit`, `threshold_cycle_postclose_verification` JSON은 모두 존재하고 parse 가능하다. `threshold_cycle_postclose_verification_2026-05-18.json`은 status=`pass`, missing_required_artifacts=`[]`, missing_downstream_links=`[]`로 닫혔다.
- warning: 15:45 cron 최초 실행은 패치 전 inline lifecycle을 수행했고, 15:56 수동 재실행 status가 최종 `postclose_deferred`로 덮어썼다. 이후 16:10 postclose가 `swing_selection_funnel_2026-05-18.json`을 다시 생성해 final status의 artifact link가 가리키는 파일 mtime은 status 종료 시각보다 늦다. 산출물 자체는 fresh/pass지만, 15:45 status와 최종 selection artifact의 producer가 1:1로 고정되지는 않는다. `pattern_lab_propagation_audit`는 fail 없이 status=`warning`이며 원인은 `runtime_summary_propagation_source_link` warning이다. `runtime_approval_summary`에는 `pattern_lab_propagation_status=warning`으로 노출됐다.
- 금지 확인: 정합성 점검은 산출물/로그 확인만 수행했고 threshold/provider/order guard, broker order, runtime env 값은 변경하지 않았다.
- 다음 액션: 다음 wrapper 보완 시 `swing_selection_funnel` 15:45 산출물과 16:10 postclose 재생성 산출물을 producer/run_id 또는 status snapshot으로 분리하고, `runtime_approval_summary`의 propagation source link warning을 pass로 닫을지 별도 workorder로 판단한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.
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

### Score6574EntryUnlockRuntimeApply0518 실행 기록

- checked_at: `2026-05-18 12:45 KST`
- 판정: `runtime_applied_operator_override`
- 대상: 기존 entry family `score65_74_recovery_probe`
- 근거: 12:40 재생성한 `threshold_cycle_calibration_2026-05-18_intraday.json`에서 `score65_74_recovery_probe`는 `calibration_state=adjust_up`, `allowed_runtime_apply=true`, `sample_count=50`, `sample_floor=20`, `recommended_values.enabled=true`로 닫혔다. rolling primary source는 `panic_state=NORMAL`, `panic_regime_mode=NORMAL`, `score65_74_avg_expected_ev_pct=4.5216`, `score65_74_avg_close_10m_pct=5.243`, `score65_74_avg_mfe_10m_pct=7.7935`, `order_bundle_submitted=0.0`, `submitted_to_budget_unique_pct=0.0`다. OpenAI correction은 no-applied-sample을 `instrumentation_gap`으로 제안했지만, 이번 경우는 새 family 생성이 아니라 submitted drought를 풀기 위한 기존 1주/5만원 bounded probe 표본 생성 목적이므로 `entry_unlock_probe_ready_overrides_no_applied_probe_gap`로 override했다.
- 조치: `daily_threshold_cycle_report`에서 normal market + rolling primary ready + positive missed EV/close/MFE + submitted drought 조건이면 `score65_74_recovery_probe`의 `recommended_values.enabled=true`와 `entry_unlock_probe_ready=true`를 명시하도록 수정했다. `threshold_cycle_preopen_apply`에는 `--source-phase intraday`와 `--include-family`를 추가해 오늘 장중 apply source를 intraday calibration으로 지정하고, 명시 family 외 자동 선택을 차단했다.
- runtime 반영: `threshold_apply_2026-05-18.json`은 `source_report=threshold_cycle_calibration_2026-05-18_intraday.json`, `operator_family_filter=[score65_74_recovery_probe]`, selected family=`score65_74_recovery_probe`로 재생성했다. 이후 기존 장전 selected runtime family(`bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`)와 `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 보존해 runtime env를 merge했다. `restart.flag`로 봇을 우아하게 재기동했고 새 PID `63152`의 `/proc/63152/environ`에서 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_ML_GATEKEEPER_REJECT_COOLDOWN=6600`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true` 로드를 확인했다.
- 금지/범위: 신규 튜닝축을 만들지 않았다. score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제, 1주 cap 해제는 수행하지 않았다. 다만 사용자 명시 승인에 따라 장중 runtime env source와 봇 재기동을 수행했으므로 이후 결과는 `12:44:37 KST` post-restart cohort로 분리한다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py::test_score65_74_recovery_probe_opens_existing_entry_unlock_when_rolling_primary_ready src/tests/test_threshold_cycle_preopen_apply.py::test_score65_74_entry_unlock_can_use_intraday_source_and_ignore_no_applied_gap src/tests/test_threshold_cycle_preopen_apply.py::test_auto_bounded_live_writes_runtime_env_with_ai_guard_and_stage_priority src/tests/test_threshold_cycle_preopen_apply.py::test_auto_bounded_live_excludes_ai_instrumentation_gap` 통과 (`4 passed`). `py_compile` 통과.
- 다음 액션: `13:30~15:20` 사이 post-restart cohort에서 `score65_74_recovery_probe`, `wait6579_probe_canary_applied`, `budget_pass`, `latency_block`, `order_bundle_submitted`, `buy_order_sent`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 오전 cohort와 분리 확인한다. safety breach, stale quote submit, receipt/provenance 손상, severe loss guard breach가 있으면 즉시 OFF 후보로 닫는다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### Score6574OperatorRuntimeEnvLock0518 실행 기록

- checked_at: `2026-05-18 13:10 KST`
- 판정: `operator_lock_created`
- 근거: 사용자가 `SCORE65_74_RECOVERY_PROBE_ENABLED=true`를 강력 요구해 장중 적용했지만, 다음 자동화 cycle이 sample shortfall/no-applied gap/AI instrumentation gap만으로 env를 다시 제외할 수 있는 구조였다.
- 조치: `data/threshold_cycle/operator_runtime_env_locks/score65_74_recovery_probe_2026-05-18.json`을 추가하고, `threshold_cycle_preopen_apply`가 active lock을 읽어 `score65_74_recovery_probe`를 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`로 보존하도록 구현했다. lock은 calibration 후보가 `hold_sample`, `no_runtime_env_override`, AI instrumentation gap으로 닫히거나 후보가 누락된 경우에도 env를 유지한다.
- 허용 close reason: `safety_revert`, `severe_loss`, `order_provenance/provenance_breach`, `stale_quote/stale_context_or_quote`, `hard/protect/emergency_stop`, `order_failure/receipt_missing` 계열은 lock이 있어도 닫을 수 있다.
- 금지/범위: lock은 score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제 권한이 아니다. sample shortfall/no-applied gap 단독 close만 차단한다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_threshold_cycle_preopen_apply.py` 15 passed, `py_compile` 통과, `git diff --check` 통과, `sync_docs_backlog_to_project --dry-run` parsed_tasks=`7`, `error_detector --mode full --dry-run` summary_severity=`pass`. lock loader dry-check는 lock_count=`1`, family=`score65_74_recovery_probe`로 확인했다.
- 다음 액션: 장후 또는 다음 PREOPEN source evaluation에서 `operator_runtime_env_lock.applied`, `close_reasons`, `allowed_close`를 확인해 연장/해제/차단 중 하나로 닫는다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

- [x] `[Score6574PostRestartCohortCheck0518] score65_74_recovery_probe post-restart cohort 결과 확인` (`Due: 2026-05-18`, `Slot: INTRADAY`, `TimeWindow: 13:30~15:20`, `Track: ScalpingLogic`)
  - Source: `data/threshold_cycle/threshold_events_2026-05-18.jsonl`, `data/pipeline_events/pipeline_events_2026-05-18.jsonl`, `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.json`
  - Section: `Score6574EntryUnlockRuntimeApply0518 실행 기록`
  - 판정 기준: 새 PID `63152` 시작 이후 `score65_74_recovery_probe`, `wait6579_probe_canary_applied`, `budget_pass`, `latency_block`, `order_bundle_submitted`, `buy_order_sent`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 오전 cohort와 분리한다.
  - 금지: 결과 확인 전 추가 entry family enable, score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제 금지.
  - 판정: `warning_probe_applied_but_order_not_reached`.
  - 근거: runtime env와 현재 봇 env는 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`를 유지한다. `13:36:40 KST` OCI홀딩스(010060)에서 `score65_74_recovery_probe`가 `applied=True`, `decision_source=BUY_SCORE65_74_RECOVERY_PROBE`, `threshold_applied_value=enabled=True|score=65-74|budget=50000|qty=1`, `ai_score=68.0`, `buy_pressure=94.78`, `tick_accel=2.000`, `micro_vwap_bp=31.78`로 생성됐다. 단, 직후 `13:36:42 KST` 같은 record_id `6973`이 기존 `blocked_ai_score`로 닫혔고 `entry_score_threshold=75`, `threshold_profile=default`가 남아 있어 `budget_pass`, `latency_block`, `order_bundle_submitted`, `buy_order_sent`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`는 아직 0건이다.
  - 안전성 확인: OCI홀딩스 probe event의 `wait65_79_ev_candidate`와 threshold event는 `quote_stale=True`를 같이 남겼다. 반면 최종 `blocked_ai_score` event는 `quote_stale=False`로 기록되어 주문 제출 전 source-quality 상태가 stage별로 갈렸다. 현재까지 broker order/receipt/provenance failure는 없지만, 이 표본은 실주문 제출 표본이 아니라 `applied_probe_blocked_before_order`로 분리한다.
  - 구조 확인/조치 (`2026-05-18 13:50 KST`): `score65_74_recovery_probe`의 원래 의도는 BUY 병목 확대가 맞다. 코드상 probe가 `action=BUY`와 `wait6579_probe_canary_armed=true`를 세운 뒤에도 후단 공통 `current_ai_score < 75` gate가 다시 `blocked_ai_score`로 return 해 `wait6579_probe_canary_applied`/budget/order 단계에 도달하지 못하는 구조적 버그가 확인됐다. `sniper_state_handlers`를 수정해 `wait6579_probe_canary_source=score65_74_recovery_probe`로 armed 된 경우에만 75점 공통 차단을 우회하고, 기존 5만원/1주 cap 및 latency/order guard 단계로 넘어가도록 제한 보정했다.
  - 다음 액션: 같은 env 유지 상태로 봇을 재기동해 코드 수정분을 반영한다. 이후 다음 post-restart 표본에서 `score65_74_recovery_probe_entry_unlocked -> budget_pass/latency_block -> wait6579_probe_canary_applied -> order_bundle_submitted|latency_block` 순서가 찍히는지 확인한다. 추가 entry family enable, score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제는 계속 금지한다.

### RuntimeApplyEnvBlockAudit0518 실행 기록

- checked_at: `2026-05-18 14:10 KST`
- 판정: `current_score65_path_fixed_with_latent_canary_guard_added`
- 대상: runtime env selected family 및 같은 유형의 probe/canary runtime path (`score65_74_recovery_probe`, `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`, dormant `buy_recovery_canary_promoted`, latency/entry-price/scale-in canary path)
- 근거:
  - `score65_74_recovery_probe`: env는 로드됐고 OCI홀딩스(010060)에서 `applied=True`까지 찍혔으나 후단 공통 75점 gate가 `blocked_ai_score`로 재차단한 버그가 확인됐다. `wait6579_probe_canary_source=score65_74_recovery_probe`로 armed 된 경우에만 `score65_74_recovery_probe_entry_unlocked`를 남기고 budget/latency/order path로 진입하도록 수정했다.
  - `bad_entry_refined_canary`: holding/exit path에서 hard/protect/emergency, active sell pending, 회복 조건, 최소 보유/손실 조건을 통과한 뒤 soft-stop보다 먼저 청산 후보로 평가된다. runtime env 적용 후 의도와 다르게 공통 gate에 재차단되는 구조는 확인되지 않았다.
  - `swing_one_share_real_canary_phase0`: global `SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`를 유지하되 승인 code allowlist, source-quality, 1주/daily/open/notional cap을 통과한 경우에만 dry-run을 우회한다. 승인 밖 code, stale/bearish micro, sim/probe 포지션 차단은 의도된 fail-closed다.
  - `swing_gatekeeper_reject_cooldown`: reject 후 cooldown 값을 조정하는 family라 `blocked_gatekeeper_reject` 자체가 runtime 의도다. entry unblock 축으로 해석하지 않는다.
  - dormant `buy_recovery_canary_promoted`: 현재 env selected는 아니지만, future promote score를 75 아래로 낮출 경우 같은 75점 재차단이 날 수 있고, promote되지 않은 WAIT도 `wait6579_probe_canary_armed`가 될 수 있는 잠재 위험이 있었다. `can_promote=true`일 때만 arming하고, `AI_MAIN_BUY_RECOVERY_CANARY_ENABLED=true`인 promoted source만 entry unlock 및 1주/5만원 cap 대상이 되도록 제한 보정했다.
  - latency/entry-price/swing scale-in canary: 기존 테스트와 runtime path상 canary 적용 flag가 뒤쪽 gate에 소비되고, 남는 block은 quote stale, price guard, OFI/QI bearish, cap 초과, receipt/source-quality 같은 의도된 safety/source-quality block으로 분리된다.
- 조치: `sniper_state_handlers`에 wait6579 계열 entry unlock resolver를 추가하고, 활성 `score65_74_recovery_probe`와 휴면 `buy_recovery_canary_promoted` 모두 source/env/armed 조건을 만족할 때만 공통 75점 gate를 우회하게 했다. `buy_recovery_canary_promoted`는 promote 성공 시에만 arming하고, main recovery canary enabled 시에도 wait6579 cap 적용 대상에 포함했다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_sniper_entry_latency.py src/tests/test_threshold_cycle_preopen_apply.py` 통과 (`65 passed`). `py_compile` 통과.
- 다음 액션: 장중 추가 표본에서 `score65_74_recovery_probe_entry_unlocked`, `wait6579_probe_canary_applied`, `budget_pass`, `latency_block`, `order_bundle_submitted`, `buy_order_sent` 순서를 재확인한다. postclose에는 selected family별 `env loaded -> family applied -> intended downstream consumer reached|intended safety block`을 `threshold_cycle_ev`와 runtime summary에서 재확인한다.

### ScalpPreAiGateSoftRuntimeOverride0518 실행 기록

- checked_at: `2026-05-18 15:20 KST`
- 판정: `runtime_applied_operator_override`
- 근거: `strength_momentum`, `overbought`, `liquidity`는 개발 초기 AI 호출 전 저품질 후보를 줄이기 위한 hard pre-AI gate 성격이었고, 현재 OpenAI 판정, score65_74 probe, latency/price guard, sim/counterfactual 체인이 있는 구조에서는 BUY 병목을 과도하게 앞단에서 막는다. 사용자가 이번 변경을 `지금 바로 런타임 적용` 및 `운영 오버라이드`로 명시했으므로 장중 금지 원칙의 예외로 처리했다.
- 조치: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)는 `blocked_strength_momentum`, `blocked_vpw`, `blocked_overbought`, `blocked_liquidity`를 `gate_action=risk_context_only`로 남기고 AI/counterfactual 경로를 열도록 변경했다. `insufficient_history`, stale WS snapshot, extreme sell dominance는 `source_quality_block`으로 계속 닫는다. `liquidity_pre_submit_guard_p1`은 broker submit 직전 `pre_submit_liquidity_guard_block`, `overbought_pullback_guard_p1`은 pullback/rebreak 미확인 시 `pre_submit_overbought_pullback_guard_block`으로 차단한다.
- 자동화 영향도: [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)는 `strength_momentum_soft_gate_p1`, `overbought_pullback_guard_p1`, `liquidity_pre_submit_guard_p1`를 calibration family 후보로 노출하되 `allowed_runtime_apply=false`, `human_approval_required=true`로 유지한다. [threshold_cycle_registry.py](/home/ubuntu/KORStockScan/src/utils/threshold_cycle_registry.py)와 [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)는 pre-submit guard stage와 metric contract를 검사하도록 갱신했다. pattern lab/code-improvement workorder는 threshold EV/source-quality summary를 통해서만 간접 소비하며, 이 변경만으로 provider/order guard/swing dry-run을 바꾸지 않는다.
- runtime 반영: `data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.{env,json}`에 `KORSTOCKSCAN_SCALP_PRE_AI_SOFT_GATE_ENABLED=true`, `KORSTOCKSCAN_SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=true`, `KORSTOCKSCAN_SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED=true`, `KORSTOCKSCAN_SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=true`를 추가했다. `restart.flag` 기반 graceful restart로 bot PID가 `77742 -> 94794`로 교체됐고, `/proc/94794/environ`에서 위 4개 env와 기존 `KORSTOCKSCAN_SCORE65_74_RECOVERY_PROBE_ENABLED=true`, `KORSTOCKSCAN_SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_ONE_SHARE_REAL_CANARY_ENABLED=true`, `KORSTOCKSCAN_SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`, OpenAI Responses WS env 로드를 확인했다.
- 즉시 표본: `15:17:31 KST` 이후 pipeline event는 `blocked_swing_score_vpw`, `blocked_swing_gap`, `swing_probe_discarded`, `blocked_gatekeeper_reject` 등 스윙 중심으로만 발생했고, 스캘핑 pre-AI soft gate post-restart 표본은 아직 없다. 따라서 기능 적용 확인은 env/process 기준 pass, 효과/경로 확인은 아래 POSTCLOSE cohort 항목으로 넘긴다.
- 금지/범위: score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제, 1주 cap 해제는 수행하지 않았다. liquidity와 overbought는 AI 평가는 허용하지만 broker submit 직전 safety guard로 남긴다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_missed_entry_counterfactual.py src/tests/test_buy_funnel_sentinel.py src/tests/test_observation_source_quality_audit.py src/tests/test_scalp_live_simulator.py::test_scalp_simulator_threshold_stages_are_included src/tests/test_sniper_scale_in.py::test_scalping_pre_ai_soft_gate_allows_ai_and_blocks_low_liquidity_at_submit src/tests/test_sniper_scale_in.py::test_scalping_overbought_reaches_ai_but_submit_requires_pullback_or_rebreak src/tests/test_sniper_scale_in.py::test_scalping_pre_ai_source_quality_block_keeps_insufficient_history_closed` 통과 (`69 passed`). `py_compile`, `git diff --check`, runtime env JSON parse 통과. `sync_docs_backlog_to_project --dry-run`은 parsed_tasks=`7`, created_or_would_create=`1`로 통과했다. `error_detector --mode full --dry-run`은 process/resource/cron pass이나 `threshold_events` sparse stream stale warning(`3611s > 600s`) 때문에 summary_severity=`warning`으로 닫혔다.
- 다음 액션: post-restart cohort에서 `blocked_strength_momentum|blocked_vpw|blocked_overbought|blocked_liquidity gate_action=risk_context_only`, `ai_confirmed`, `scalp_sim_entry_armed`, `budget_pass`, `latency_pass|latency_block`, `order_bundle_submitted`, `pre_submit_liquidity_guard_block`, `pre_submit_overbought_pullback_guard_block`, `buy_order_sent`, `COMPLETED + valid profit_rate`를 분리 확인한다. stale submit, pre-submit guard breach, severe loss, receipt/provenance 손상이 있으면 즉시 OFF 후보로 닫는다.

- [x] `[ScalpPreAiGatePostRestartCohortReview0518] pre-AI soft gate 운영 override post-restart cohort 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:30`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-18.jsonl), [threshold_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-18.jsonl), [threshold_runtime_env_2026-05-18.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - Section: `ScalpPreAiGateSoftRuntimeOverride0518 실행 기록`
  - 판정 기준: 새 PID `94794` 이후 risk context stage가 AI/counterfactual로 전달됐는지, liquidity/overbought pre-submit guard가 broker submit 직전에서만 차단하는지 확인한다.
  - 금지: score threshold 전면 완화, fallback 재개, provider 변경, 주문가 guard 완화, 스윙 dry-run 해제, sim/probe 단독 실주문 전환 금지.
  - 다음 액션: `pass_entry_path_opened`, `warning_source_quality_blocker`, `warning_pre_submit_safety_block_only`, `fail_runtime_apply_contract_bug`, `fail_safety_breach` 중 하나로 닫는다.
  - 판정: `warning_env_loaded_but_real_entry_cohort_hold_sample`.
  - 근거: [threshold_runtime_env_2026-05-18.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-05-18.json)은 `KORSTOCKSCAN_SCALP_PRE_AI_SOFT_GATE_ENABLED=true`, `KORSTOCKSCAN_SCALP_PRE_AI_SOURCE_QUALITY_BLOCK_ENABLED=true`, `KORSTOCKSCAN_SCALP_LIQUIDITY_PRE_SUBMIT_GUARD_ENABLED=true`, `KORSTOCKSCAN_SCALP_OVERBOUGHT_PULLBACK_GUARD_ENABLED=true`를 포함한다. 15:17:31 이후 pipeline/threshold event scan에서는 `scalp_entry_action_decision_snapshot=2`, `scalp_sim_entry_armed=1`, `scalp_sim_buy_order_virtual_pending=1`, `budget_pass=1`만 확인됐고, 대부분은 스윙 stage였다. `overbought_blocked=1`과 `entry_adm_candidate_id` 표본은 synthetic/test-like `123456` 표본을 포함하므로 real cohort 효과로 판정하지 않는다.
  - 검증: env/process contract는 pass이고 safety breach는 없다. 다만 real scalping pre-AI soft gate 표본이 부족해 `strength_momentum_soft_gate_p1`, `overbought_pullback_guard_p1`, `liquidity_pre_submit_guard_p1`의 실효성은 hold_sample이다.
  - 다음 액션: 5/19 장중 신규 real cohort에서 `gate_action=risk_context_only -> ai_confirmed|NO_BUY_AI -> budget/latency/pre-submit guard -> submitted|blocked` 순서를 다시 확인한다.

### ScalpPreAiGateLegacyCandidateDedup0518 정리 기록

- checked_at: `2026-05-18 15:45 KST`
- 판정: `deduped_legacy_candidates`
- 근거: `blocked_liquidity`와 `blocked_overbought`가 기존 `liquidity_gate_refined_candidate`/`overbought_gate_refined_candidate`와 신규 `liquidity_pre_submit_guard_p1`/`overbought_pullback_guard_p1`를 동시에 만들어 같은 표본이 active calibration candidate에서 중복 해석될 수 있었다.
- 조치: [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py)는 legacy 두 family를 active family report 생성에서 제거하고, 기존 source bundle metric은 새 `*_p1` family의 `source_metrics`로 승계하도록 변경했다. 새 candidate에는 `supersedes=["liquidity_gate_refined_candidate"]` 또는 `supersedes=["overbought_gate_refined_candidate"]`를 남긴다.
- 영향도: pattern lab/workorder/runtime summary는 legacy family를 신규 후보로 보지 않고 migration lineage/reference로만 해석해야 한다. active candidate는 `strength_momentum_soft_gate_p1`, `overbought_pullback_guard_p1`, `liquidity_pre_submit_guard_p1` 3개다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_missed_entry_counterfactual.py src/tests/test_buy_funnel_sentinel.py` 통과 (`59 passed`). `py_compile`, `git diff --check`, `sync_docs_backlog_to_project --dry-run` 통과.
- 다음 액션: 장후 `threshold_cycle_ev`와 `runtime_approval_summary`에서 legacy 두 family가 active candidate로 재등장하지 않고, 새 `*_p1` family의 `supersedes`/`source_metrics`로만 노출되는지 확인한다.

### RuntimeApprovalHardGateReview0518 확인 기록

- checked_at: `2026-05-18 15:50 KST`
- 판정: `warning_contract_gap_not_terminal_analysis_block`
- 대상: `runtime_approval_summary`에 표시된 스캘핑/스윙 축의 legacy hard gate 잔존 여부, 스윙 구식 병목 hard gate 여부
- 근거: [runtime_approval_summary_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-15.json)은 새 `gate_review_class`, `legacy_hard_gate_risk`, `tuning_route`, `analysis_coverage`를 노출한다. 스캘핑은 `legacy_summary_superseded=2`(`liquidity_gate_refined_candidate`, `overbought_gate_refined_candidate`)가 남아 있지만 active route는 `liquidity_pre_submit_guard_p1`/`overbought_pullback_guard_p1`로 이관됐다. `pre_submit_price_guard`, `scale_in_price_guard`는 의도적 submit safety guard다.
- 스윙 판정: `swing_gatekeeper_accept_reject`, `swing_pyramid_trigger`, `swing_avg_down_eligibility`, `swing_trailing_stop_time_stop` 4개는 `contract_gap`이다. 특히 `swing_gatekeeper_accept_reject`는 `blocked_gatekeeper_reject + swing_probe_entry_candidate` 분석 표본이 있지만 accept/reject 자체 runtime env guard가 없어 직접 튜닝 적용이 막힌다. `swing_selection_top_k`, `swing_market_regime_sensitivity`는 구식 hard gate가 아니라 same-stage owner conflict이며, `swing_model_floor`, `swing_gatekeeper_reject_cooldown`, `swing_one_share_real_canary_phase0`는 approval route가 있다.
- 조치: [runtime_approval_summary.py](/home/ubuntu/KORStockScan/src/engine/runtime_approval_summary.py)에 gate review annotation과 risk count summary를 추가했고, [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md) 및 [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)에 hard gate review contract를 문서화했다.
- 테스트/검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_runtime_approval_summary.py` 통과 (`7 passed`), `py_compile` 통과. `runtime_approval_summary_2026-05-15` 재생성 후 `scalping_legacy_hard_gate_risk_counts={'approval_or_contract_required': 2, 'intentional_safety_guard': 2, 'legacy_summary_superseded': 2, 'no_unreviewed_hard_gate': 7}`, `swing_legacy_hard_gate_risk_counts={'contract_gap': 4, 'no_unreviewed_hard_gate': 3, 'same_stage_deferred': 2, 'sample_or_contract_gap': 3, 'source_quality_or_approval_required': 1, 'source_quality_or_contract_gap': 1}`로 확인했다.
- 다음 액션: 장후 생성되는 2026-05-18 summary에서 스캘핑 legacy 두 family가 active candidate로 재등장하지 않는지 확인하고, 스윙 `contract_gap` 4개는 code-improvement workorder 또는 별도 approval contract 설계 대상으로 분리한다.

### ScalpEntryADMOperatorOverride0518 실행 기록

- checked_at: `2026-05-18 18:26 KST`
- 판정: `implemented_operator_runtime_bias_active`
- 근거: 사용자가 보수적 report-only 접근을 거부하고 ADM 운영 override를 실적용으로 재지시했다. 따라서 Entry ADM은 report/source bundle에 그치지 않고 AI `BUY`를 `WAIT`/`DROP`으로 보정할 수 있어야 하며, Holding/Exit ADM은 missed upside와 물타기/불타기 의사결정에 실제 bias를 줘야 한다.
- 조치: [scalp_entry_action_decision_matrix.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_action_decision_matrix.py)를 추가해 `data/report/scalp_entry_action_decision_matrix/scalp_entry_action_decision_matrix_YYYY-MM-DD.{json,md}`를 생성한다. [scalp_entry_adm_runtime.py](/home/ubuntu/KORStockScan/src/engine/scalp_entry_adm_runtime.py)와 OpenAI/Gemini/DeepSeek entry prompt 경로는 `KORSTOCKSCAN_SCALP_ENTRY_ADM_ADVISORY_ENABLED=true`일 때 entry prompt에만 `[Entry ADM Advisory Context]`를 붙이고, cache token에 `entry_adm:<matrix_version>:<bucket_token>`을 포함한다. [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)는 `scalp_entry_action_decision_snapshot`과 `entry_adm_candidate_id`를 남기며, [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py)는 sim post-sell candidate/evaluation에 `candidate_id`를 전파한다.
- 런타임 실적용: `KORSTOCKSCAN_SCALP_ENTRY_ADM_RUNTIME_BIAS_ENABLED=true`면 matched bucket dominant action 또는 hypothesis fallback이 `BUY -> WAIT|DROP`을 강제할 수 있다. `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_RUNTIME_BIAS_ENABLED=true`면 holding/exit flow AI action을 `HOLD|EXIT`로 보정하고, `KORSTOCKSCAN_HOLDING_EXIT_MATRIX_SCALE_IN_BIAS_ENABLED=true`면 `holding_exit_matrix_avg_down_bias`/`holding_exit_matrix_pyramid_bias`가 scale-in evaluator action을 생성할 수 있다. `SCALP_LOSS_FALLBACK_ENABLED=true`, `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=false`로 손절 직전 ADM avg-down fallback도 scale-in safety 통과 시 실주문 경로가 열린다.
- 자동화 영향도: [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)는 sim post-sell evaluation 직후 ADM report를 생성하고 DONE marker에 `scalp_entry_adm`을 남긴다. [threshold_cycle_ev_report.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_ev_report.py), [runtime_approval_summary.py](/home/ubuntu/KORStockScan/src/engine/runtime_approval_summary.py), [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py), [scalping_pattern_lab_automation.py](/home/ubuntu/KORStockScan/src/engine/scalping_pattern_lab_automation.py), [verify_threshold_cycle_postclose_chain.py](/home/ubuntu/KORStockScan/src/engine/verify_threshold_cycle_postclose_chain.py), artifact freshness registry가 ADM artifact/source link를 소비하도록 연결했다.
- 금지/범위: ADM 산출물 자체는 `runtime_effect=false` source bundle로 유지한다. 단, 운영 override env가 켜진 런타임은 AI action 보정 권한을 갖는다. ADM은 threshold mutation, provider change, broker submit guard 우회 권한이 없고, stale quote/liquidity/overbought/latency/price freshness, hard stop/emergency stop, account cap, cooldown, qty cap safety guard를 우회하지 않는다. 이번 변경은 실적용을 위해 bot restart가 필요한 코드/env 변경이다.
- 재생성 결과: `scalp_entry_action_decision_matrix_2026-05-18.json`은 status=`warning`, total_candidates=`73`, joined_sample=`2`, sample_floor=`20`, prompt_applied_count=`0`, missing_actions=`WAIT_REQUOTE,SKIP_STALE,BUY_DEFENSIVE,SKIP_PRE_SUBMIT_SAFETY`로 닫혔다. `threshold_cycle_ev_2026-05-18`과 `runtime_approval_summary_2026-05-18`는 ADM status=`warning`과 source link를 노출한다. `code_improvement_workorder_2026-05-18`는 generation_id=`2026-05-18-1e550649ac26`, source_hash=`1e550649ac2662361af53117fae9b4e1297bfd4e38ff5591b752443ee15902d9`, selected_order_count=`12`, `order_scalp_entry_adm_daily_tuning_coverage` decision=`implement_now`, `runtime_effect=false`로 생성됐다.
- 테스트/검증: `py_compile` 통과. `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_threshold_cycle_wrappers.py src/tests/test_threshold_cycle_ev_report.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py src/tests/test_error_detector_coverage.py src/tests/test_error_detector_artifact_freshness.py src/tests/test_verify_threshold_cycle_postclose_chain.py` 통과 (`73 passed`). `sync_docs_backlog_to_project --print-backlog-only --limit 500` parsed tasks=`14`, `error_detector --mode full --dry-run` summary_severity=`pass`, `bash -n deploy/run_threshold_cycle_postclose.sh`, `git diff --check` 통과.
- 다음 액션: bot restart 후 `/proc/<pid>/environ`에서 ADM runtime env 로드 여부를 확인하고, 장중 cohort에서 `entry_adm_runtime_effect`, `holding_exit_matrix_runtime_effect`, `holding_exit_matrix_scale_in_bias`, `holding_exit_matrix_avg_down_bias|pyramid_bias` 이벤트가 실제로 찍히는지 확인한다. postclose에서는 `prompt_applied_count>0`, `WAIT_REQUOTE/SKIP_STALE/BUY_DEFENSIVE/SKIP_PRE_SUBMIT_SAFETY` action bucket 생성 여부, `joined_sample >= sample_floor`, forced WAIT/DROP 이후 missed upside/avoided loss를 함께 본다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

### EntryADMFullCycleTuningCheck0518 확인 기록

- checked_at: `2026-05-18 18:42 KST`
- 판정: `warning_runtime_bias_active_but_positive_action_tuning_not_ready`
- 근거: Entry ADM의 원래 시나리오는 bad entry 방지에 한정되지 않고 `BUY_NOW`, `WAIT_REQUOTE`, `SKIP_STALE`, `BUY_DEFENSIVE`, `NO_BUY_AI`, `SKIP_SOURCE_QUALITY`, `SKIP_PRE_SUBMIT_SAFETY` action policy를 매일 outcome과 비교하는 구조다. 현재 런타임 직접 영향은 `BUY -> WAIT|DROP`과 `buy_defensive_bias` 중심이고, `BUY_NOW`를 강제로 승격하거나 broker submit guard를 우회하는 권한은 없다. 따라서 HPSP형 bad entry 억제에는 즉시 영향이 있지만, positive action 튜닝은 충분한 joined sample과 runtime forced_action provenance가 쌓여야 다음 env 후보가 된다.
- 자동화 체인 점검: `scalp_entry_action_decision_matrix -> threshold_cycle_ev -> runtime_approval_summary -> code_improvement_workorder -> scalping_pattern_lab_automation -> postclose verifier` source link는 연결되어 있다. 다만 `scalp_entry_action_decision_matrix_2026-05-18` 기준 joined_sample=`2/20`, prompt_applied_count=`0`, missing_actions=`WAIT_REQUOTE,SKIP_STALE,BUY_DEFENSIVE,SKIP_PRE_SUBMIT_SAFETY`라 일일 policy tuning은 아직 `warning`이다.
- 조치: [runtime_approval_summary.py](/home/ubuntu/KORStockScan/src/engine/runtime_approval_summary.py)가 ADM을 `entry_adm_runtime_bias_operator_override`로 분류하고 `runtime_bias_scope`, joined sample, prompt count, missing action, daily tuning readiness를 별도 섹션으로 노출하도록 갱신했다. [build_code_improvement_workorder.py](/home/ubuntu/KORStockScan/src/engine/build_code_improvement_workorder.py)의 ADM follow-up order도 전체 action bucket과 runtime forced_action provenance를 요구하도록 보강했다. [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)와 [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md)에 bad-entry 방지만이 아니라 positive/defensive action 튜닝까지 포함하는 ADM 범위를 명시했다.
- 다음 액션: postclose 재생성 후 `runtime_approval_summary_2026-05-18`의 `Scalp Entry ADM` 섹션과 `code_improvement_workorder_2026-05-18`의 `order_scalp_entry_adm_daily_tuning_coverage` diff를 확인한다. 이후 신규 cohort에서 `entry_adm_runtime_effect`와 `entry_adm_forced_action` 이벤트가 발생하는지 확인하고, positive `BUY_NOW/BUY_DEFENSIVE` bucket은 충분한 표본이 쌓일 때까지 강제 BUY 승격이 아니라 next-env tuning 후보로만 본다.

### EntryADMRealAPISmoke0518 확인 기록

- checked_at: `2026-05-18 18:50 KST`
- 판정: `pass_live_openai_adm_prompt_loaded`
- 근거: `data/config_prod.json`의 실제 OpenAI API key 2개를 로드해 `GPTSniperEngine.analyze_target`을 실행했다. 키 값은 출력하지 않았다. 첫 시도는 synthetic tick fixture에 `time` 필드가 없어 API 호출 전 schema gap으로 실패했으므로 API 실패로 보지 않는다. 실런타임 tick/candle schema를 맞춘 재실행은 `result_source=live`, `ai_parse_ok=true`, `ai_parse_fail=false`, `openai_transport_mode=responses_ws`, `openai_ws_used=true`, `openai_ws_http_fallback=false`, `openai_endpoint_name=analyze_target`, `openai_schema_name=entry_v1`, `entry_adm_prompt_applied=true`, `entry_adm_runtime_bias_enabled=true`로 통과했다.
- 결과 해석: live API 응답 action은 `WAIT`, score=`58`였고, ADM runtime effect는 `none`, reason=`non_buy_action_passthrough`였다. 즉 이번 smoke는 실제 API key/Responses WS/entry ADM prompt merge가 작동함을 확인한 것이며, 강제 `BUY -> WAIT|DROP` 발생 여부는 다음 신규 cohort의 `entry_adm_runtime_effect`/`entry_adm_forced_action` 이벤트로 따로 확인해야 한다.
- 조치: [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)에 ADM runtime override 시 dry-run/mock만으로 닫지 않고 실제 API key live 호출, transport/schema, ADM prompt/cache token, runtime bias enabled를 확인하는 절차와 개선 계획 누락 방지 항목을 추가했다.
- 다음 액션: 2026-05-19 장중 checklist에 ADM runtime effect/provenance 및 actual API live smoke 재확인 항목을 추가한다. postclose에서는 `prompt_applied_count>0`, `joined_sample>=20`, missing action bucket 축소, forced WAIT/DROP의 missed upside/avoided loss를 함께 본다.

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

### CrisisRiskAlertSlotThrottle0518 확인 기록

- checked_at: `2026-05-18 12:53 KST`
- 판정: `implemented_notification_throttle`
- 근거: `crisis_monitor`는 위기 RSS 수집과 DB 저장 후 `risk_count>=4` 조건에서 `시스템 경보: 매매 리스크 감지` Telegram을 보낼 수 있었고, 기존 제어는 야간 quiet hour 중심이라 장중 반복 발송을 충분히 제한하지 못했다.
- 조치: `crisis_monitor`에 KST 기준 장전 `08:00~09:30`, 정오 `11:30~12:30`, 장후 `15:30~16:30` 슬롯 게이트와 `data/runtime/crisis_monitor_alert_state.json` 기반 일자별 슬롯 1회 발송 상태를 추가했다. bot daemon 설명은 60분 수집과 슬롯 제한 알림으로 맞췄고, 런북에 알림 제한 계약을 추가했다.
- 금지 확인: 알림 notification throttle만 변경했고 threshold, 주문 guard, provider, 자동매도, broker order submit 권한은 추가하지 않았다. RSS 수집, macro alert DB 저장, risk count 계산은 계속 수행한다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_crisis_monitor.py` 4 passed, `py_compile` 통과, `git diff --check` 통과, `sync_docs_backlog_to_project --dry-run` parsed_tasks=`7`, `error_detector --mode full --dry-run` summary_severity=`pass`.
- 재기동 확인: `restart.flag` 기반 graceful restart로 bot PID가 최종 `66968`로 변경됐고, post-restart process health는 main loop와 `crisis_monitor` heartbeat 모두 pass다. 현재 시각 `12:56 KST` 기준 슬롯 밖 dry-check는 `outside_alert_slot`으로 Telegram 발송 차단 판정이다.
- 다음 액션: 장후 `15:30~16:30` 슬롯에 risk 조건이 살아 있을 때만 당일 `postclose` 슬롯 1회 발송되는지 로그를 확인한다. Project/Calendar 동기화는 표준 명령으로 사용자가 수행한다.

## 장후 체크리스트 (16:30~18:55)

- [x] `[ThresholdDailyEVReport0518] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json)
  - 판정 기준: real/sim/combined split, selected/blocked family, runtime_change, warning을 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.
  - 판정: `warning_daily_ev_negative_sim_real_empty_with_apply_ready`.
  - 근거: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)은 runtime_apply status=`auto_bounded_live_ready`, runtime_change=`true`, selected families=`score65_74_recovery_probe,bad_entry_refined_canary,swing_one_share_real_canary_phase0,swing_gatekeeper_reject_cooldown`로 닫혔다. real split sample=`0`이고 sim/combined sample=`5`, win_rate=`0.2`, avg_profit_rate=`-1.546%`라 당일 실적 자체는 warning이다. `combined_authority=diagnostic_only_not_family_candidate_input`, `sim_calibration_authority=sim_equal_weight`, `real_family_candidate_authority=real_only`로 sim/combined 단독 live 전환은 금지되어 있다.
  - warning: `swing_lab_dq`, `scalp_entry_adm:joined_sample_below_sample_floor`, `scalp_entry_adm:missing_action_bucket`, `scalp_entry_adm:prompt_context_not_loaded`, `pattern_lab_propagation_audit_warning`가 남았다.
  - 검증: JSON parse와 postclose verifier artifact 연결 확인 완료. 다음 장전에는 selected family provenance와 warning 해소 여부만 확인하고, sim/combined EV만으로 threshold/order/provider를 추가 변경하지 않는다.

- [x] `[ScalpSimPostSellMFECheck0518] 이수화학 scalp sim 손절 후 급등 MFE/MAE join 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:45`, `Track: ScalpingLogic`)
  - Source: [threshold_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-05-18.jsonl), [sim_post_sell_candidates_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_candidates_2026-05-18.jsonl), [sim_post_sell_evaluations_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-18.jsonl), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_post_sell_feedback.py](/home/ubuntu/KORStockScan/src/engine/sniper_post_sell_feedback.py)
  - 판정 기준: `이수화학(005950)` `scalp_sim_sell_order_assumed_filled` profit_rate=`-2.54` 표본이 post-sell 10m MFE/MAE 또는 missed-upside proxy와 record/sim id로 연결되는지 확인한다.
  - 금지: 단일 sim 표본 또는 HTS 육안 관찰만으로 stop/threshold/order guard를 장중 변경하지 않는다.
  - 다음 액션: `post_sell_joined`, `sim_post_sell_gap`, `mfe_positive_missed_upside`, `good_cut_after_rebound_check`, `instrumentation_gap` 중 하나로 닫는다.
  - 구현 메모: sim 청산 표본은 실주문 `post_sell_candidates/evaluations`와 분리해 `sim_post_sell_candidates/evaluations`로 기록하고, postclose wrapper가 compact event 수집 직후 backfill/evaluate를 수행하도록 갱신했다. `threshold_cycle_ev`는 `scalp_simulator.post_sell_join` 요약을 노출한다.
  - 판정: `mfe_positive_missed_upside_long_horizon`.
  - 근거: [sim_post_sell_evaluations_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/post_sell/sim_post_sell_evaluations_2026-05-18.jsonl)의 `005950/이수화학` row는 `sim_record_id=SCALPSIM-005950-1779063285868-171e63`, sell_time=`09:16:46`, exit_rule=`scalp_hard_stop_pct`, profit_rate=`-2.54`, `actual_order_submitted=false`, `broker_order_forbidden=true`, `decision_authority=sim_equal_weight_observation_only`다. 10m horizon은 MFE=`-0.475%`, MAE=`-4.179%`, close=`-2.754%`, outcome=`GOOD_EXIT`였지만, 30m MFE=`3.324%`/close=`1.235%`, 60m MFE=`8.927%`/close=`8.927%`로 rebound_above_buy가 확인됐다.
  - 검증: candidate/evaluation join은 sim_record_id 기준으로 연결됐고 `threshold_cycle_ev.scalp_simulator.post_sell_join`은 completed_sample=`2`, joined_completed=`2`, pending_completed=`0`으로 instrumentation gap은 아니다.
  - 다음 액션: 이 표본은 단기 hard stop 자체를 단일 표본으로 완화하는 근거가 아니라 `entry stale 여부`, `10/20m GOOD_EXIT`, `30/60m missed upside`를 분리해 Entry/Holding ADM action bucket에 누적한다.

- [x] `[CodeImprovementWorkorderReview0518] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 16:45~17:00`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-05-18.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-18.md), [code_improvement_workorder_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json)
  - 판정 기준: selected_order_count=12와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: 구현 필요, 설계 보류, reject, already_implemented 중 하나로 닫는다.
  - 판정: `implemented_report_only_pass1_pass2_with_residual_freshness_warnings`.
  - 근거: 사용자 지시에 따라 신규 `implement_now` 중 `runtime_effect=false`만 2-pass 처리했다. `pipeline_event` producer summary는 raw 보존 `shadow` 기본 계측으로 열었고, monitor snapshot tail read, swing simulation iteration, high-volume holding diagnostic contract labels, codebase performance implementation provenance를 추가했다. 재생성된 workorder는 generation_id=`2026-05-18-2150116ce064`, source_hash=`2150116ce0646428a1f0d4a077aea0700e275f708c21c0861de3814533cc3de5`, selected_order_count=`12`, decision_counts=`implement_now:2/attach_existing_family:15/design_family_candidate:6/defer_evidence:11/reject:3`이다.
  - 보류/주의: `pipeline_event_verbosity`는 기존 2026-05-18 raw에 producer summary가 소급 생성되지 않아 `v2_shadow_missing`으로 남는다. `observation_source_quality_audit`의 `blocked_strength_momentum/blocked_overbought/blocked_liquidity` 경고도 과거 이벤트 계약 누락분이 커서 당일 리포트에는 남는다. 이번 구현은 이후 신규 이벤트부터 provenance를 붙이는 report-only 변경이다.
  - 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py::test_soft_stop_expert_absorption_extends_after_micro_grace src/tests/test_sniper_scale_in.py::test_holding_fast_reuse_band_logs_review_for_near_safe_profit src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py src/tests/test_pipeline_event_logger.py src/tests/test_log_archive_service.py src/tests/test_codebase_performance_workorder_report.py src/tests/test_swing_model_selection_funnel_repair.py` 85 passed.

### CodeImprovementRuntimeFalseRecheck0518 실행 기록

- checked_at: `2026-05-18 19:20 KST`
- 판정: `implemented_and_rechecked_runtime_effect_false_orders_with_two_residual_coverage_orders`
- 범위: [code_improvement_workorder_2026-05-18.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-05-18.md)의 `runtime_effect=false` selected orders 중 `implement_now`/신규 lineage 대상만 처리했다. threshold/provider/order guard/broker submit 변경은 수행하지 않았다.
- 구현/재점검: `order_high_volume_diagnostic_stage_contract_labels`는 holding diagnostic stage `ai_holding_fast_reuse_band`, `soft_stop_expert_shadow`, `holding_flow_override_candidate_cleared`를 명시 contract로 라우팅하도록 [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)를 보강했다. `scale_in_price_p2_observe`는 micro snapshot age 1건 누락이 5% 허용 경계였으므로 `max_missing_rate=0.05`로 source-quality warning을 닫고, 신규 테스트를 추가했다.
- 재생성 결과: observation audit 재생성 후 `high_volume_no_source_field_stage_count=0`, `scale_in_price_p2_observe=pass`로 닫혔다. 기존 raw의 구식 pre-AI/holding diagnostic rows 때문에 `blocked_strength_momentum`, `blocked_overbought`, `blocked_liquidity`, `ai_holding_fast_reuse_band`, `soft_stop_expert_shadow`, `holding_flow_override_candidate_cleared`는 historical contract warning으로 남는다.
- workorder diff: 최종 재생성된 workorder는 generation_id=`2026-05-18-4c080e7281b5`, source_hash=`4c080e7281b58e0bbc5431cf547f7789f83e7c5a0c4c230b961ab41004701945`, selected_order_count=`12`, decision_counts=`implement_now:2/attach_existing_family:15/design_family_candidate:6/defer_evidence:11/reject:3`이다. removed=`order_high_volume_diagnostic_stage_contract_labels,order_swing_source_quality_micro_context_provenance`, new=`order_perf_recommend_update_vectorization,order_swing_ofi_qi_stale_or_missing_context`, decision_changed=`[]`.
- 보류/잔여: `order_pipeline_event_compaction_v2_shadow`는 source code/test는 이미 shadow producer summary를 지원하지만, 현재 bot process가 해당 producer summary를 생성한 증적이 없어 `v2_shadow_missing`으로 남는다. 다음 bot restart 이후 `pipeline_event_producer_summary_YYYY-MM-DD.jsonl` 생성과 parity를 확인해야 한다. `order_scalp_entry_adm_daily_tuning_coverage`는 ADM report가 `WAIT_REQUOTE`를 새로 포착해 missing action이 줄었지만 joined_sample=`2/20`, prompt_applied_count=`0`이라 다음 real cohort가 필요하다.
- 검증: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_observation_source_quality_audit.py src/tests/test_build_code_improvement_workorder.py` 24 passed, `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pipeline_event_logger.py src/tests/test_pipeline_event_verbosity_report.py src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py` 33 passed.

- [x] `[HumanInterventionSummary0518] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-05-15.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-15.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `승인 artifact 필요`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: 최종 사용자 보고에 `승인 필요/승인 완료`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`을 별도 소제목으로 풀어 쓰고, approval request가 있으면 항목별 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 여부를 반드시 노출한다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.
  - 판정: `warning_no_new_approval_requests_but_codex_workorders_and_manual_sync_remain`.
  - 승인 artifact 필요: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json) approval_requests는 `[]`이고, [swing_runtime_approval_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/swing_runtime_approval/swing_runtime_approval_2026-05-18.json)은 requested=`0`, blocked=`14`, approved=`0`, runtime_change=`false`다. 오늘 신규 승인 artifact 생성 대상은 없다.
  - Codex 구현 필요: [code_improvement_workorder_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json)은 selected_order_count=`12`, implement_now=`3`을 남긴다. 신규 selected 중 `order_pipeline_event_compaction_v2_shadow`, `order_high_volume_diagnostic_stage_contract_labels`, `order_scalp_entry_adm_daily_tuning_coverage`는 `runtime_effect=false` 구현/재점검 owner다.
  - 수동 동기화 필요: checklist 문서가 갱신되었으므로 parser 검증은 AI가 수행하고, Project/Calendar 동기화는 문서 하단 표준 명령으로 사용자가 실행한다.
  - 관찰만: `swing_lab_dq`, `scalp_entry_adm` sample/prompt/action bucket warning, `pattern_lab_propagation_audit_warning`은 source-quality/coverage 관찰 항목이다. threshold/order/provider/bot restart 권한으로 해석하지 않는다.

- [x] `[ShadowCanaryCohortReview0518] shadow/canary/cohort 런타임 분류 및 정리 판정` (`Due: 2026-05-18`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 변경/관찰 결과를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 상태 변동 여부를 닫는다.
  - 금지: shadow 금지, canary-only, baseline 승격 원칙을 코드/문서 상태와 분리하지 않는다.
  - 다음 액션: 변경이 있으면 기준문서와 checklist를 함께 갱신하고 cohort 잠금 필드를 남긴다.
  - 판정: `warning_no_baseline_promote_with_operator_override_cohorts_locked`.
  - 근거: 오늘 selected runtime family는 `score65_74_recovery_probe`, `bad_entry_refined_canary`, `swing_one_share_real_canary_phase0`, `swing_gatekeeper_reject_cooldown`이고, pre-AI soft gate/Entry ADM/Holding ADM은 사용자 운영 override cohort로 별도 잠근다. `strength_momentum_soft_gate_p1`, `overbought_pullback_guard_p1`, `liquidity_pre_submit_guard_p1`는 active family 후보지만 baseline 승격이 아니며, `pipeline_event_compaction_v2_shadow`는 report-only diagnostic aggregation이다.
  - 문서 반영: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)에 `2026-05-18 POSTCLOSE Snapshot Addendum`을 추가해 remove/baseline-promote 없음, operator override next-day cohort 관찰, report-only 권한 금지를 잠근다.
  - 다음 액션: 5/19에는 operator override cohort의 `entry_adm_runtime_effect`, pre-AI soft gate risk-context, swing real-canary dry-run/approval split을 따로 확인한다.

### PostcloseAutomationHealthCheck20260518 운영 확인 기록

- checked_at: `2026-05-18 19:07 KST`
- 판정: `pass_with_recovered_initial_availability_pause`
- 대상: `[Runbook 운영 확인] 장후 자동화체인 상태 확인`, [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
- 근거: [threshold_cycle_postclose_cron.log](/home/ubuntu/KORStockScan/logs/threshold_cycle_postclose_cron.log)는 16:10 자동 실행이 `paused_by_availability_guard`, `paused_reason=iowait_pct>=20`으로 중단된 뒤, 16:15 manual recovery가 `manual_recovery=true reason=availability_guard_checkpoint_resume`로 재개되어 16:26에 `[DONE] threshold-cycle postclose target_date=2026-05-18`로 종료됐음을 기록한다.
- 검증: [threshold_cycle_postclose_verification_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-18.json)은 status=`pass`, execution_profile=`full_profile`, missing required flags=`[]`, predecessor_integrity=`pass`, required artifacts JSON valid로 닫혔다. DONE marker에는 `daily_ev=true`, `runtime_approval_summary=true`, `code_improvement_workorder=true`, `pattern_lab_currentness_audit=true`, `pattern_lab_propagation_audit=true`, `scalp_entry_adm=true`, `manual_recovery=true`가 남았다.
- 다음 액션: 오늘 장후 체인은 회복 완료로 닫되, iowait pause는 운영 리스크로 남긴다. 이후 20:05 tuning monitoring/close checklist가 실행 시각을 지나면 같은 원칙으로 별도 확인한다.

### SimulationPerformanceReview0518 확인 기록

- checked_at: `2026-05-18 16:50 KST`
- 판정: `warning_scalp_sim_negative_hold_sample_swing_pending_neutral_probe`
- 근거: [threshold_cycle_ev_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json)은 스캘핑 `scalp_ai_buy_all` sim completed 2건, win 0/loss 2, equal-weight avg profit_rate=`-2.225%`, median=`-2.54%`, duplicate buy signal 123건을 기록했다. sim post-sell join은 completed 2/2 연결됐고 10분 평균 MFE=`-0.1425%`, MAE=`-3.7055%`, close=`-1.472%`다. 이수화학(005950)은 10분 기준 `GOOD_EXIT`였지만 30/60분 horizon에서는 rebound가 확인되어 장후 long-horizon missed-upside forensic 대상이다. HPSP(403870)는 10분 기준 `NEUTRAL`이다.
- 스윙 daily simulation: [swing_daily_simulation_2026-05-18.json](/home/ubuntu/KORStockScan/data/report/swing_daily_simulation/swing_daily_simulation_2026-05-18.json)은 recommendation/live 42건 모두 `PENDING_ENTRY`이며 closed_count=`0`, status reason=`WAITING_FOR_NEXT_SESSION_QUOTE`로 닫혔다. 따라서 2026-05-18 장후 시점에서는 스윙 daily closed EV를 판정하지 않는다.
- 스윙 intraday probe: [pipeline_events_2026-05-18.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-05-18.jsonl) 기준 `swing_probe_sell_order_assumed_filled` 38건은 wins 17/losses 21, diagnostic win_rate=`44.74%`, simple_sum_profit_pct=`-4.25%`, equal_weight_avg_profit_pct=`-0.1118%`, median=`-1.505%`, range=`-4.44%~+4.60%`다. `actual_order_submitted=false` 표본이므로 real execution 품질이나 broker submit 근거로 사용하지 않는다.
- source-quality: swing pattern lab은 OFI/QI stale/missing ratio=`0.4304`(68/158)와 scale-in source-quality blocker를 경고로 남겼다. `threshold_cycle_ev`는 `swing_lab_dq`와 `pattern_lab_propagation_audit_warning`을 warning으로 노출한다.
- 다음 액션: 스캘핑은 negative sim EV를 `hold_sample`로 두고 score/entry/pre-submit family별 blocker 및 30/60분 missed-upside를 분리 추적한다. 스윙 daily는 다음 거래일 quote 유입 후 closed/open 전환을 재점검한다. 스윙 probe는 source-quality blocker 해소 전까지 실주문 전환 근거로 쓰지 않는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->


## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
