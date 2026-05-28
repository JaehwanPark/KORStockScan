# 2026-05-07 Stage2 To-Do Checklist

## 오늘 목적

- `statistical_action_weight` 2차 고급축 중 `SAW-3 eligible_but_not_chosen` 후행 성과 연결을 설계한다.
- 선택된 행동만 보는 selection bias를 줄이고, 물타기/불타기/청산 후보의 기회비용을 후행 MFE/MAE로 복원할 수 있는지 판정한다.
- AI 보유/청산 판단에 `holding_exit_decision_matrix`를 shadow prompt context로 주입할 수 있는지 확인한다.
- 5/6 threshold-cycle 누적/rolling 결과에서 상위 후보로 남은 `protect_trailing_smoothing`, `scale_in_price_guard`, `statistical_action_weight`를 live 변경이 아니라 단일 owner/manifest/shadow context로 분리한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- `statistical_action_weight`는 report-only/decision-support 축이며 직접 runtime threshold나 주문 행동을 바꾸지 않는다.
- `holding_exit_decision_matrix`는 장중 self-updating 금지다. 전일 장후 산정 matrix를 다음 장전 로드하고 장중에는 immutable context로만 쓴다.
- `AI decision matrix`는 `ADM-1 report-only -> ADM-2 shadow prompt -> ADM-3 advisory nudge -> ADM-4 weighted live -> ADM-5 policy gate` 순서로만 전환한다. 5/7의 허용 범위는 ADM-2 설계이며 live AI 응답 변경은 금지한다.
- `preclose_sell_target`는 5/6 P1 report-only dry-run 통과 후에도 AI/Telegram acceptance, cron 등록, threshold/ADM consumer 연결을 분리한다. 자동 주문, live threshold mutation, bot restart와 연결하지 않는다.
- `BUY Funnel Sentinel`과 `HOLD/EXIT Sentinel`은 detection/report-only 운영 감시축이다. 매일 산출물과 Telegram false-positive/false-negative를 보고 신규 이상치 후보를 backlog에 추가하되, 자동 score/threshold/청산/재시작 변경은 금지한다. 반복 이상치는 `incident`, `threshold-family 후보`, `instrumentation gap`, `normal drift` 중 하나로 분류하고, threshold-cycle에는 sample floor와 rollback owner가 있는 후보만 연결한다.
- `protect_trailing_smoothing`은 5/6 threshold-cycle daily에서 `next_preopen_single_owner` 후보지만 5/7 PREOPEN의 `soft_stop whipsaw confirmation`과 같은 holding/exit 단계다. 같은 장전에서 둘을 동시에 live enable하지 않고, 충돌 시 둘 다 hold 또는 하나만 명시 승인한다.
- `scale_in_price_guard`는 현행 `80bps / 1주 cap` 유지가 기본이며, `spread_bps_p90=83.26`은 완화 근거가 아니라 manifest/report-only 관찰값이다.
- `statistical_action_weight`의 `time_1030_1400 + pyramid_wait`, `volume_2m_10m + pyramid_wait`, `price_gte_70k + pyramid_wait`는 ADM/SAW 입력 후보일 뿐 live 주문/청산 판단에 직접 연결하지 않는다.
- 후행 성과 연결은 `COMPLETED + valid profit_rate`와 분리해 보고, full/partial fill은 합치지 않는다.
- raw full scan 반복은 금지하고 compact partition/checkpoint 경로만 사용한다.
- daily 정기작업은 cron 발화 성공과 산출물 완성 성공을 분리해 검증한다. 실패 재시도/lock/status manifest/운영 알림이 없는 작업은 live 전략 변경과 별개인 RuntimeStability backlog로 관리한다.

## 장전 체크리스트 (08:45~09:00)

- [x] `[ProtectTrailingSmoothingPreopen0507] protect trailing smoothing 단일 owner 충돌 확인 및 live hold/후보 판정` (`Due: 2026-05-07`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_2026-05-06.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-05-06.json), [threshold_cycle_cumulative_2026-05-06.md](/home/ubuntu/KORStockScan/data/report/threshold_cycle_cumulative/threshold_cycle_cumulative_2026-05-06.md), [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: 5/6 daily threshold-cycle에서 `protect_trailing_smoothing`은 `apply_ready=True`, `apply_mode=next_preopen_single_owner`, sample `smooth_hold=115`, `smooth_confirmed=8`, 추천값 `window_sec=19`, `min_span_sec=19`, `min_samples=8`, `below_ratio=0.5`다. 누적/rolling은 report-only reference이며 누적 평균 단독으로 live threshold를 바꾸지 않는다.
  - 충돌 확인: 같은 holding/exit 단계 PREOPEN 후보인 `SoftStopWhipsawConfirmationPreopen0507`과 동시에 live enable하지 않는다. whipsaw confirmation을 live 후보로 검토하면 protect trailing smoothing은 `report_only_reference`로 hold한다. protect trailing smoothing을 단일 owner 후보로 채택하려면 whipsaw confirmation은 기본 OFF/hold로 명시하고, rollback guard와 cohort를 분리한다.
  - 금지선: protect hard stop/emergency stop은 평탄화 대상이 아니다. 자동 청산 threshold mutation, bot restart, scale-in price guard 완화, holding_flow override mutation은 이 항목에서 금지한다.
  - 판정: live hold. 5/7 PREOPEN의 holding/exit 단일 owner는 추가 live enable 없이 유지한다.
  - 근거: `protect_trailing_smoothing`은 5/6 daily threshold-cycle에서 `apply_ready=True`, `apply_mode=next_preopen_single_owner`지만, 같은 holding/exit 단계의 `soft_stop_whipsaw_confirmation`과 동시 live enable 금지 원칙에 걸린다. current owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`이고, protect trailing smoothing을 같은 PREOPEN에서 올리면 same-stage owner가 중첩된다.
  - 다음 액션: 5/7에는 `SentinelThresholdFeedback0507-Intraday`와 threshold-cycle 후보 라우팅으로만 유지한다. live 후보를 유지하려면 별도 checklist에서 rollback owner, baseline/candidate/observe/excluded cohort, approval 기준을 새로 잠근다.

- [x] `[Wait6579RecoveryProbePreopen0507] score65_74 recovery probe 로드 확인 및 live enable/hold 판정` (`Due: 2026-05-07`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py), [wait6579_ev_cohort_2026-05-06.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-06.json)
  - 판정 기준: `AI_SCORE65_74_RECOVERY_PROBE_ENABLED=False` 기본값과 env override 미설정 상태를 먼저 확인한다. live enable은 별도 사용자 승인 또는 명시된 preopen 판정 없이는 금지한다.
  - live enable 조건: 1주/5만원 cap, score65~74, fallback score 50 제외, latency DANGER 제외, buy_pressure/tick_accel/micro_vwap gate, `score65_74_recovery_probe` 및 `wait6579_probe_canary_applied` 로그가 모두 유지되어야 한다.
  - rollback guard: `submitted/full/partial`, `COMPLETED + valid profit_rate`, soft_stop tail, missed/avoided counterfactual을 장중 Sentinel/장후 threshold-cycle과 분리해 본다. broad score threshold 완화, fallback 재개, spread cap 완화는 이 항목에서 금지한다.
  - 판정: live enable 보류. 기본값은 `AI_SCORE65_74_RECOVERY_PROBE_ENABLED=False`이고 `KORSTOCKSCAN_AI_SCORE65_74_RECOVERY_PROBE_*` env override는 로드되지 않았다.
  - 근거: 코드상 score 65~74, fallback score 50 제외, BUY 제외, latency `DANGER` 제외, buy_pressure/tick_accel/micro_vwap gate가 유지된다. 5/6 report는 `total_candidates=414`, `probe_applied_candidates=0`, `budget_pass_candidates=10`, `latency_pass_candidates=0`, `submitted_candidates=0`, `observability_passed=true`, `behavior_change=none`이라 live 주문 표본 없이 장전 즉시 ON 근거가 부족하다.
  - 다음 액션: 5/7 장중 `BUY Funnel Sentinel`과 장후 threshold/action report에서 score65~74 blocker, submitted/full/partial, `COMPLETED + valid profit_rate`, missed/avoided counterfactual을 분리해 본다. broad score threshold 완화, fallback 재개, spread cap 완화는 계속 금지한다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -q` 통과.

- [x] `[SoftStopWhipsawConfirmationPreopen0507] soft_stop whipsaw confirmation 로드 확인 및 live enable/hold 판정` (`Due: 2026-05-07`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [holding_exit_observation_2026-05-06.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/holding_exit_observation_2026-05-06.json)
  - 판정 기준: `SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=False` 기본값과 env override 미설정 상태를 먼저 확인한다. live enable은 별도 사용자 승인 또는 명시된 preopen 판정 없이는 금지한다.
  - live enable 조건: hard/protect stop 우선, emergency stop 우선, base grace 종료 후 1회 confirmation cap, `rebound_above_sell/buy`, `flow_state`, `additional_worsen`, expired stage 로그가 유지되어야 한다.
  - rollback guard: sell receipt/completed, same-symbol reentry loss, GOOD_EXIT/MISSED_UPSIDE, soft stop tail 악화 여부를 본다. 자동 청산 변경, hard/protect stop 완화, holding_flow override mutation은 이 항목에서 금지한다.
  - 판정: live enable 보류. 기본값은 `SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_ENABLED=False`이고 `KORSTOCKSCAN_SCALP_SOFT_STOP_WHIPSAW_CONFIRMATION_*` env override는 로드되지 않았다.
  - 근거: 코드상 emergency/hard/protect 우선 조건, base grace 종료 후 confirmation, 1회 cap, `additional_worsen <= max_worsen`, `soft_stop_whipsaw_confirmation`/`soft_stop_whipsaw_confirmation_expired` stage가 유지된다. 5/6 holding/exit report는 `total_soft_stop=14`, 10분 `rebound_above_sell_rate=92.9%`, `rebound_above_buy_rate=35.7%`, `mfe_ge_0_5_rate=71.4%`, `same_symbol_reentry_loss_count=2`, `whipsaw_signal=true`라 후보성은 있지만, 같은 holding/exit 단계의 `protect_trailing_smoothing` PREOPEN 후보와 충돌하므로 장전 동시 live enable은 금지한다.
  - 다음 액션: 5/7 장중 `HOLD/EXIT Sentinel`에서 `SOFT_STOP_WHIPSAW`를 report-only로 감시하고, `SentinelThresholdFeedback0507-Intraday`에서 threshold-family 후보 또는 별도 단일 owner workorder로 라우팅한다. 자동 청산 변경, hard/protect stop 완화, holding_flow override mutation은 계속 금지한다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_state_handler_fast_signatures.py -q` 통과.

## 장중 체크리스트 (09:00~15:20)

- [x] `[SentinelDiscoveryLoop0507-Intraday] BUY/HOLD-EXIT Sentinel 신규 이상치 후보 발굴 및 운영 메시지 품질 점검` (`Due: 2026-05-07`, `Slot: INTRADAY`, `TimeWindow: 15:20~15:40`, `Track: RuntimeStability`)
  - Source: [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [holding_exit_sentinel.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_sentinel.py), [buy_funnel_sentinel report](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel), [holding_exit_sentinel report](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 당일 `BUY Funnel Sentinel`과 `HOLD/EXIT Sentinel`의 primary/secondary 분포, Telegram 발송 횟수, false-positive 의심, 운영자가 수동으로 발견한 병목과의 불일치를 점검한다. 후보는 `신규 classification`, `기존 classification threshold 조정`, `메시지 포맷 개선`, `데이터/로그 누락` 중 하나로 분류한다.
  - 신규 후보 seed: entry는 `entry_armed_expiry_spike`, `buy_signal_telegram_only_no_order`, `price_resolver_skip_cluster`, `quote_stale_runtime_ops`를 검토한다. holding/exit는 `exit_signal_no_receipt`, `holding_flow_defer_worsen_cluster`, `ai_holding_cache_miss_spike`, `soft_stop_rebound_intraday`, `trailing_missed_upside_intraday`, `sell_order_market_closed_cluster`를 검토한다.
  - 운영 규칙: Sentinel 개선은 감지/리포트/알림 계층만 수정한다. score threshold 완화, spread cap 완화, fallback 재개, 자동 매도, holding threshold mutation, bot restart는 별도 단일축 workorder와 rollback guard 없이는 금지한다.
  - 다음 액션: 채택 후보는 날짜별 checklist 신규 항목 또는 Plan Rebase sentinel backlog 문장으로 반영하고 parser 검증을 실행한다. 미채택 후보는 false-positive 사유와 추가 필요 로그를 문서화한다.
  - 11:28 KST 중간 점검: `PYTHONPATH=. .venv/bin/python -m src.engine.buy_funnel_sentinel --date 2026-05-07 --dry-run --print-json`와 `PYTHONPATH=. .venv/bin/python -m src.engine.holding_exit_sentinel --date 2026-05-07 --dry-run --print-json`로 당일 산출물을 재생성했다.
  - 중간 판정: BUY는 `UPSTREAM_AI_THRESHOLD` primary, `LATENCY_DROUGHT` secondary다. `ai_confirmed=96`, `budget_pass=20`, `latency_pass=6`, `submitted=6`, `submitted/ai=6.2%`이고 upstream 상위는 `blocked_ai_score:score_65.0=167`, `wait65_79_ev_candidate:score_65.0=162`, `blocked_ai_score:ai_score_50_buy_hold_override=82`다. HOLD/EXIT는 `HOLD_DEFER_DANGER` primary, `AI_HOLDING_OPS` secondary다. `exit_signal=6`, `sell_order_sent=6`, `sell_completed=6`으로 청산 전송/완료 drought는 없고, `flow_defer=67`, `ai_cache_miss=100%`, `soft_stop_grace=157`이 상위다.
  - 중간 다음 액션: BUY는 score50/wait65_74 missed-winner/avoided-loser cohort를 장후 report-only review에 붙인다. score threshold 완화, fallback 재개, spread cap 완화는 금지한다. HOLD/EXIT는 holding_flow_override defer 표본과 worsen floor 증거를 장후 확인한다. 자동 매도, holding threshold/flow override/AI cache TTL mutation, bot restart는 금지한다.
  - 후속 진행 (`2026-05-07 11:34 KST`): [sentinel_followup_2026-05-07.md](/home/ubuntu/KORStockScan/data/report/sentinel_followup_2026-05-07.md)를 생성했다. `wait6579_ev_cohort_2026-05-07` 기준 `blocked_ai_score=155/182(85.2%)`, score65 `135건`, score74 `19건`, `threshold_relaxation_approved=false(partial_samples=0)`로 기록했다. HOLD/EXIT는 `sell drought 없음`, `defer=67`, 주요 defer anchor `심텍(222800) record_id=5370 trailing TP defer 44건, max profit_rate +2.32%`, `AI cache MISS 100%`로 기록했다.
  - 최종 판정 (`2026-05-07 15:40 KST`): 신규 classification 추가는 보류한다. BUY는 [buy_funnel_sentinel_2026-05-07.md](/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-07.md) 기준 `UPSTREAM_AI_THRESHOLD` primary, `LATENCY_DROUGHT` secondary로 기존 분류에 수렴한다. HOLD/EXIT는 [holding_exit_sentinel_2026-05-07.md](/home/ubuntu/KORStockScan/data/report/holding_exit_sentinel/holding_exit_sentinel_2026-05-07.md) 기준 `HOLD_DEFER_DANGER` primary, `AI_HOLDING_OPS`, `SOFT_STOP_WHIPSAW`, `TRAILING_EARLY_EXIT` secondary로 기존 분류 조합에 수렴한다.
  - 메시지 품질 판정: 5분 반복 발송 false-positive는 코드 보정 완료로 `duplicate_signature` skip이 확인됐다. 현재 남은 개선 후보는 신규 classification이 아니라 `AI_HOLDING_OPS`의 cache/provenance logging backlog와 `HOLD_DEFER_DANGER`의 defer cost/worsen floor report-only enrichment다.
  - 최종 검증: `PYTHONPATH=. .venv/bin/python -m src.engine.buy_funnel_sentinel --date 2026-05-07 --dry-run --print-json`, `PYTHONPATH=. .venv/bin/python -m src.engine.holding_exit_sentinel --date 2026-05-07 --dry-run --print-json` 통과. `--notify-admin --print-json` 경로도 BUY/HOLD-EXIT 모두 `skipped/duplicate_signature`로 반복 전송 차단을 확인했다.

- [x] `[SentinelThresholdFeedback0507-Intraday] Sentinel 이상치의 threshold-cycle 연결/비연결 라우팅 표준화` (`Due: 2026-05-07`, `Slot: INTRADAY`, `TimeWindow: 15:40~15:55`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [buy_funnel_sentinel.py](/home/ubuntu/KORStockScan/src/engine/buy_funnel_sentinel.py), [holding_exit_sentinel.py](/home/ubuntu/KORStockScan/src/engine/holding_exit_sentinel.py)
  - 판정 기준: 각 Sentinel classification을 `incident/playbook`, `threshold-cycle family candidate`, `instrumentation/logging backlog`, `normal drift/no action` 중 하나로 매핑한다. `UPSTREAM_AI_THRESHOLD`, `LATENCY_DROUGHT`, `PRICE_GUARD_DROUGHT`, `HOLD_DEFER_DANGER`, `SOFT_STOP_WHIPSAW`, `TRAILING_EARLY_EXIT`, `AI_HOLDING_OPS`, `RUNTIME_OPS`별 sample floor, 반복 기준, owner 문서, 금지된 자동변경을 표로 닫는다.
  - why: 이상치를 매번 관찰만 하면 tuning이 끝나지 않는다. 반대로 이상치마다 즉시 threshold를 바꾸면 원인귀속과 rollback guard가 깨진다. 따라서 Sentinel은 자동 튜너가 아니라 threshold-cycle 후보 생성과 incident playbook 분기를 담당한다.
  - 다음 액션: threshold 후보는 `R3_manifest_only`까지만 연결하고, R5 live mutation은 `ThresholdOpsTransition` acceptance와 별도 rollback guard가 없으면 금지한다. instrumentation gap은 다음 거래일 logging workorder로, incident는 사용자 승인 playbook으로 분리한다.
  - 11:28 KST 중간 라우팅: `UPSTREAM_AI_THRESHOLD`는 threshold-cycle 직결이 아니라 score50/wait65_74 report-only cohort review로 라우팅한다. `LATENCY_DROUGHT`는 두산 rollback 직후라 spread cap 재완화 후보가 아니며, latency DANGER 원인 분해와 `SAFE normal submit 직전 음수 수급/strength fade` 분리 관찰로 둔다. `HOLD_DEFER_DANGER`는 holding_flow_override defer cost/worsen floor 검증으로 라우팅한다. `AI_HOLDING_OPS`는 cache MISS 100% 재확인이므로 AI cache/Tier provenance logging backlog로 둔다. 직전 리포트의 `RUNTIME_OPS`는 재실행 후 `stale_sec=0`으로 사라져 현 시점 incident로 승격하지 않는다.
  - 코드 보정 (`2026-05-07 11:34 KST`): `holding_exit_sentinel`의 `RUNTIME_OPS` stale 판정을 수정했다. 세션 내 마지막 stage가 `sell_completed`로 끝난 key는 active/pending으로 보지 않고, `stale_sec > 900`, `ai_review > 0`, `active_holding > 0`일 때만 stale runtime 이상으로 분류한다. 11:25 as-of 재생성 결과도 `HOLD_DEFER_DANGER + AI_HOLDING_OPS`이며 `RUNTIME_OPS`는 사라졌다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_holding_exit_sentinel.py src/tests/test_buy_funnel_sentinel.py -q` 통과. `PYTHONPATH=. .venv/bin/python -m src.engine.holding_exit_sentinel --date 2026-05-07 --as-of 11:25:04 --dry-run --print-json`에서 primary `HOLD_DEFER_DANGER`, secondary `AI_HOLDING_OPS` 확인.
  - 알림 보정 (`2026-05-07 15:10 KST`): BUY/HOLD-EXIT Sentinel Telegram 전송에 날짜별 notify state를 추가했다. `primary + secondary` semantic signature가 동일하면 5분 cron 반복 실행에서도 `duplicate_signature`로 전송하지 않고, `NORMAL`을 한 번 관측하면 reset되어 다음 동일 이상치 재발 시 다시 1회 전송한다. 메시지 중복 방지만 수행하며 report JSON/Markdown 생성과 classification은 계속 매 실행 갱신한다.
  - 알림 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py -q` 통과. 첫 이상치 `sent`, 동일 이상치 반복 `skipped/duplicate_signature`, `NORMAL` 후 재발 `sent` 흐름을 테스트로 고정했다.
  - 표준 라우팅 (`2026-05-07 15:55 KST`): `UPSTREAM_AI_THRESHOLD`는 threshold-cycle 직결이 아니라 score50/wait65_74 cohort review와 단일축 canary 승인 후보로 둔다. `LATENCY_DROUGHT`/`PRICE_GUARD_DROUGHT`는 두산 rollback 이후 spread cap 자동완화 금지, latency/가격가드 원인분해 owner로 둔다. `HOLD_DEFER_DANGER`/`SOFT_STOP_WHIPSAW`/`TRAILING_EARLY_EXIT`는 holding/exit threshold-family 후보가 될 수 있지만 sample floor, daily/rolling/cumulative 방향 일치, rollback owner가 없으면 `R3_manifest_only`에도 연결하지 않는다. `AI_HOLDING_OPS`와 `RUNTIME_OPS`는 각각 instrumentation/logging backlog와 incident/playbook으로 우선 라우팅한다.
  - 금지선 재확인: Sentinel 이상치만으로 score threshold 완화, spread cap 완화, fallback 재개, 자동 매도, holding threshold mutation, AI cache TTL mutation, bot restart를 실행하지 않는다. `report-based-automation-traceability.md`에 Sentinel routing 표준을 추가했다.
  - 최종 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_buy_funnel_sentinel.py src/tests/test_holding_exit_sentinel.py -q` 통과. parser 검증은 문서 반영 후 별도 실행한다.

## 장후 체크리스트 (16:00~18:30)

- [x] `[StatActionEligibleOutcome0507] SAW-3 eligible-but-not-chosen 후행 MFE/MAE 연결 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: `stat_action_decision_snapshot`의 `eligible_actions/rejected_actions/chosen_action`을 후행 quote/position outcome과 연결해 `post_decision_mfe`, `post_decision_mae`, `missed_upside`, `avoided_loss`를 계산할 수 있는지 확인한다. join key, time horizon, quote source, compact partition read cap, selection-bias caveat를 같이 잠근다.
  - why: 선택된 행동의 realized PnL만 보면 “하지 않은 물타기/불타기/청산”의 기대값을 복원할 수 없다. 이 축이 열려야 행동가중치가 단순 사후 평균이 아니라 기회비용까지 반영한다.
  - 다음 액션: 연결 가능하면 Markdown 리포트에 `eligible_but_not_chosen` 섹션을 추가하고, 불가능하면 누락 필드와 추가 snapshot 필드를 명시한다.
  - 판정: report-only 구현 완료. [statistical_action_weight_2026-05-07.json](/home/ubuntu/KORStockScan/data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json)과 Markdown에 `eligible_but_not_chosen` 섹션을 추가했다. live 주문/청산 판단 변경은 없다.
  - 근거: 5/7 재생성 결과 `completed_valid=47`, `compact_decision_snapshot=459`, `exit_only=40`, `avg_down_wait=1`, `pyramid_wait=6`, `weight_source_ready=false`, `runtime_change=false`다. `eligible_but_not_chosen`은 `sample_snapshots=459`, `sample_candidates=465`, `post_sell_joined_candidates=465`이며 action별 10분 proxy는 `exit_now mfe=0.3368/mae=-8.7306`, `avg_down_wait mfe=0.1589/mae=-9.9169`, `hold_wait mfe=-0.0968/mae=-12.4638`이다.
  - 다음 액션: true 후행 quote join과 snapshot 중복 downsample은 후속 품질 보강으로 분리한다. 현재 섹션은 selection-bias 점검과 후보 발굴 전용이며 realized PnL과 합산하거나 live threshold/AI 응답에 연결하지 않는다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-07`, `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_daily_threshold_cycle_report.py src/tests/test_preclose_sell_target_report.py -q` 통과.

- [x] `[AIDecisionMatrixShadow0507] ADM-2 holding/exit shadow prompt matrix 주입 설계` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~17:00`, `Track: AIPrompt`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py), [ai_engine_openai.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_openai.py), [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py)
  - 판정 기준: `holding_exit_decision_matrix`를 `prompt_profile=holding` 경로에 shadow-only context로 넣는 설계를 확정한다. legacy/adapter의 `prompt_profile=exit`는 별도 프롬프트가 아니라 holding route alias로만 본다. 확인 항목은 token budget, cache key 영향, matrix_version provenance, Gemini/OpenAI/DeepSeek parity, `action_label/confidence/reason` drift 로그다. live AI 응답 변경은 금지한다.
  - ON/OFF 기준: `ADM-1 report-only`는 ON, `ADM-2 shadow prompt`는 이 항목에서 ON 후보로 설계, `ADM-3 advisory nudge`, `ADM-4 weighted live`, `ADM-5 policy gate`는 OFF 유지다. ADM-3 이상은 별도 checklist에서 `COMPLETED + valid profit_rate`, `GOOD_EXIT/MISSED_UPSIDE`, soft stop tail, 추가매수 기회비용의 비악화가 확인될 때만 연다.
  - why: threshold 산정 결과가 AI 보유/청산 판단에 쓰이려면 사람이 보는 리포트만으로는 부족하다. 다만 첫 단계는 AI 판단 변경이 아니라 동일 장면에서 matrix context가 응답을 어떻게 바꾸는지 shadow diff로 봐야 한다.
  - 다음 액션: shadow diff가 안정적이면 `ADM-3 observe-only nudge`로 넘어가고, 불안정하면 prompt_hint 표현/토큰 범위부터 줄인다.
  - 판정: `AIDecisionMatrixShadow0507`의 shadow naming은 stale이고, 현재 matrix 자체도 live enable 근거가 약하다. [holding_exit_decision_matrix_2026-05-07.json](/home/ubuntu/KORStockScan/data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json)은 `matrix_version=holding_exit_decision_matrix_v1_2026-05-07`, `valid_for_date=next_preopen`, `entries=14`, `runtime_change=false`다. 하지만 entry 대부분이 `recommended_bias=no_clear_edge`, `policy_hint=candidate_weight_source/defensive_only_high_loss_rate`라 same-day live AI 응답 변경까지 올릴 강한 edge가 아니다.
  - 근거: Gemini/OpenAI/DeepSeek 모두 `prompt_profile=exit`를 holding route alias로 정규화하는 경로는 존재한다. 다만 현재 코드에는 matrix loader, runtime flag, cache key 분리, matrix provenance logging이 없다. 동시에 Rebase 원칙상 신규/보완 alpha의 `shadow-only`는 금지라, 다음 유효 축은 `ADM-2 shadow`가 아니라 `single-owner advisory/live canary`다.
  - 다음 액션: [2026-05-08 checklist](./checklists/2026-05-08-stage2-todo-checklist.md) `ADMCanaryLivePivot0508`에서 runtime loader/flag/cache key/provenance logging을 구현하고, matrix가 `no_clear_edge` 위주인 현재 상태에서 live canary readiness가 실제로 닫히는지 다시 판정한다. 현재 5/7 same-day live enable은 불허한다.
  - 후속 반영 (`2026-05-07 16:50 KST`): [2026-05-08 checklist](./checklists/2026-05-08-stage2-todo-checklist.md) `ADMCanaryLivePivot0508`를 선실행해 runtime loader/flag/cache/provenance plumbing과 provider parity test를 닫았다. 다만 same-day live enable 판정은 그대로 HOLD다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-05-07` 통과.

- [x] `[PrecloseSellTargetAITelegram0507] preclose sell target AI/Telegram acceptance 분리 검증` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:20`, `Track: Plan`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/proposals/preclose-sell-target-revival-plan.md), [2026-05-06-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-06-stage2-todo-checklist.md), [preclose_sell_target_report.py](/home/ubuntu/KORStockScan/src/scanners/preclose_sell_target_report.py)
  - 판정 기준: 5/6 P1 산출물의 `policy_status=report_only`, `live_runtime_effect=false`, `automation_stage=R1_daily_report`를 유지한 채 AI 호출 가능성, 응답 JSON contract, Telegram 전송 대상을 각각 분리 검증한다. 실패 시 AI key/SDK, schema parse, Telegram publish 중 어느 축인지 분리하고 cron 등록은 보류한다.
  - 다음 액션: AI/Telegram acceptance가 통과하면 cron 등록 검토로 넘기되, 자동 주문/threshold mutation과 연결하지 않는다.
  - 판정: AI 재수행 성공 후 실제 Telegram 전송까지 실행했다. 다만 이 리포트의 정책 상태는 계속 `report_only`이며 자동 주문/threshold mutation 연결은 없다.
  - 근거: `deploy/run_preclose_sell_target_report.sh 2026-05-07 --no-legacy-markdown`에서 `GEMINI_API_KEY` 1차는 503으로 실패했고, fallback이 `GEMINI_API_KEY_2`에서 성공했다. 이후 Telegram manager 초기화 로그가 남았고, [preclose_sell_target_2026-05-07.json](/home/ubuntu/KORStockScan/data/report/preclose_sell_target/preclose_sell_target_2026-05-07.json)은 `ai_requested=true`, `ai_provider_status.status=success`, `key_name=GEMINI_API_KEY_2`, `sell_target_count=5`, `policy_status=report_only`, `live_runtime_effect=false`다.
  - 다음 액션: Telegram enable은 닫혔고 남은 open 범위는 consumer 연결뿐이다. 자동 주문/threshold mutation 연결은 계속 금지한다.
  - 검증: `PYTHONPATH=. .venv/bin/python -m pytest src/tests/test_preclose_sell_target_report.py -q` 통과. `logs/preclose_sell_target/preclose_sell_target_2026-05-07.log`에 Telegram init 후 완료 로그가 남았다.

- [x] `[PrecloseSellTargetCron0507] preclose sell target report-only cron 등록 여부 판정` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:20~17:35`, `Track: RuntimeStability`)
  - Source: [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/proposals/preclose-sell-target-revival-plan.md), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [deploy/run_preclose_sell_target_report.sh](/home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh)
  - 판정 기준: cron 등록은 `--no-ai --no-telegram` report-only 또는 AI/Telegram acceptance 후 별도 profile 중 하나로만 승인한다. 실행 시간, lock/cooldown 필요 여부, 로그 경로, 실패 알림, holiday skip을 문서화한다.
  - 다음 액션: 승인 시 deploy/cron 문서와 wrapper를 같은 change set으로 맞추고, 미승인 시 수동 실행 명령만 유지한다.
  - 판정: cron 등록 승인 및 반영 완료. 다만 등록된 작업도 `report_only` 산출물 생성/전송용이며 runtime threshold/order 행동은 바꾸지 않는다.
  - 근거: wrapper [run_preclose_sell_target_report.sh](/home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh)에 lock, log path, status manifest, venv guard, weekend/holiday guard가 들어간 상태에서 `crontab -l`에 `0 15 * * 1-5 /home/ubuntu/KORStockScan/deploy/run_preclose_sell_target_report.sh $(TZ=Asia/Seoul date +\%F) --no-legacy-markdown ... # PRECLOSE_SELL_TARGET_1500`를 등록했다. [status manifest](/home/ubuntu/KORStockScan/data/report/preclose_sell_target/status/preclose_sell_target_2026-05-07.status.json)은 `status=succeeded`, `exit_code=0`, `runtime_change=false`다.
  - 다음 액션: cron은 등록됐고 남은 open 범위는 consumer 연결과 failure alert 정교화뿐이다. live threshold mutation, bot restart, 자동 주문 제출 연결은 계속 금지한다.
  - 검증: `bash -n deploy/run_preclose_sell_target_report.sh`, `crontab -l | rg "PRECLOSE_SELL_TARGET_1500"` 통과.

- [x] `[PrecloseSellTargetConsumer0507] preclose sell target threshold/ADM consumer 연결 범위 확정` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:50`, `Track: Plan`)
  - Source: [report-based-automation-traceability.md](/home/ubuntu/KORStockScan/docs/report-based-automation-traceability.md), [data/report/README.md](/home/ubuntu/KORStockScan/data/report/README.md), [preclose-sell-target-revival-plan.md](/home/ubuntu/KORStockScan/docs/proposals/preclose-sell-target-revival-plan.md)
  - 판정 기준: `data/report/preclose_sell_target/preclose_sell_target_YYYY-MM-DD.json`을 threshold/ADM/swing trailing에서 어떤 단계(`operator review`, `shadow context`, `manifest_only`)까지 소비할지 고정한다. R5 live threshold apply, 자동 주문, bot restart는 금지한다.
  - 다음 액션: consumer가 필요하면 schema field와 consumer owner를 추가 checklist로 분리하고, 필요 없으면 report-only 운영자 검토 산출물로 유지한다.
  - 판정: 5/7 소비 범위는 `operator_preclose_review`까지만 승인한다. threshold/ADM/swing trailing 자동 소비는 후보로만 유지하고 연결하지 않는다.
  - 근거: 5/7 JSON은 `future_consumers`에 `holding_overnight_decision_support`, `threshold_cycle_report_context`, `swing_trailing_policy_review`, `ADM_ladder_context`를 명시하지만 `forbidden_use_before_acceptance`에 `live_threshold_mutation`, `bot_restart`, `automatic_order_submit`, `automatic_sell_submit`가 잠겨 있다. AI fallback/Telegram/cron은 닫혔지만 consumer는 아직 operator review를 넘지 않았다.
  - 다음 액션: consumer 연결은 별도 owner로 다시 판단한다. 현재는 canonical JSON을 운영자 검토 산출물로만 유지한다.
  - 검증: [postclose_decision_support_followup_2026-05-07.md](/home/ubuntu/KORStockScan/data/report/postclose_decision_support_followup_2026-05-07.md)에 판정/근거/다음 액션을 분리 기록했다.

- [x] `[MonitorSnapshotAsyncCompletion0507] monitor snapshot async completion/failure propagation 보강` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 17:50~18:10`, `Track: RuntimeStability`)
  - Source: [run_monitor_snapshot_cron.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_cron.sh), [run_monitor_snapshot_incremental_cron.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_incremental_cron.sh), [run_monitor_snapshot_safe.sh](/home/ubuntu/KORStockScan/deploy/run_monitor_snapshot_safe.sh), [monitor_snapshot_runner.py](/home/ubuntu/KORStockScan/src/engine/monitor_snapshot_runner.py)
  - 판정 기준: cron wrapper가 async dispatch만 성공하고 실제 snapshot worker 실패를 놓칠 수 있는지 확인한다. 필요한 경우 `run_id`, expected output manifest, completion marker, stale/incomplete alert, retry/cooldown 경계를 추가한다.
  - 다음 액션: 보강은 산출물 완성/실패 가시성까지만 허용한다. snapshot 결과로 score threshold, spread cap, bot restart를 자동 실행하지 않는다.
  - 반영: `run_monitor_snapshot_safe.sh`에 `MONITOR_SNAPSHOT_ASYNC_WAIT_SEC` 완료 대기 옵션을 추가했다. full snapshot cron은 기본 `1200초` 대기로 async worker 종료를 기다리고, worker 실패/timeout/unknown artifact는 cron exit code로 전파한다. cooldown/lock/preopen/existing manifest skip도 JSON completion artifact에 `status=skipped`, `reason`을 남긴다.
  - 검증: `bash -n deploy/run_monitor_snapshot_cron.sh deploy/run_monitor_snapshot_incremental_cron.sh deploy/run_monitor_snapshot_safe.sh` 통과. cooldown skip 경로에서 async worker completion artifact가 `status=skipped`, `reason=cooldown_active`로 생성되고 wrapper exit code 0을 반환하는 것을 확인했다.

- [x] `[TuningMonitoringPostcloseFallback0507] tuning monitoring postclose lock/retry/status manifest 보강` (`Due: 2026-05-07`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:30`, `Track: RuntimeStability`)
  - Source: [run_tuning_monitoring_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_tuning_monitoring_postclose.sh), [build_tuning_monitoring_parquet.py](/home/ubuntu/KORStockScan/src/engine/build_tuning_monitoring_parquet.py), [compare_tuning_shadow_diff.py](/home/ubuntu/KORStockScan/src/engine/compare_tuning_shadow_diff.py)
  - 판정 기준: parquet build, shadow diff, Gemini lab, Claude lab 각 step을 독립 status로 남기고 중간 실패 시 후속 step 차단이 적절한지 판정한다. lock, retry, fail-closed summary, Telegram/admin alert 필요 여부를 함께 확인한다.
  - 다음 액션: 구현 시 status manifest와 retry wrapper는 RuntimeStability 산출물로만 본다. lab/report 결과를 live threshold mutation으로 연결하지 않는다.
  - 반영: `run_tuning_monitoring_postclose.sh`에 lock, per-step retry, fail-closed exit propagation, status manifest를 추가했다. 산출물은 `data/report/tuning_monitoring/status/tuning_monitoring_postclose_YYYY-MM-DD.json`이며, 각 step은 `started/success/failed`, attempt, exit_code, command를 남긴다.
  - 검증: `bash -n deploy/run_tuning_monitoring_postclose.sh` 통과. `TUNING_MONITORING_DRY_RUN=1 TUNING_MONITORING_MAX_RETRIES=1 deploy/run_tuning_monitoring_postclose.sh 2026-05-06`에서 6개 step, 12개 started/success event와 최종 `status=success` manifest 생성을 확인했다.

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-05-07 15:48:26`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-05-07.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
