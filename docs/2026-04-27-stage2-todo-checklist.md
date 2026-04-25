# 2026-04-27 Stage 2 To-Do Checklist

## 오늘 목적

- `2026-04-24` 장중에 잠근 `quote_fresh family` 이후 다음 독립축을 `gatekeeper_fast_reuse signature/window`로 고정하고 PREOPEN 승인/보류를 닫는다.
- PREOPEN에서는 live 승인 전에 `fallback 비결합`, `단일 live 1축`, `restart.flag` 반영 순서를 먼저 점검한다.
- submitted 증가 전제로 보유/청산 계획 공백을 메우고, `gatekeeper_fast_reuse signature/window`와 stage-disjoint 예외가 성립하면 보유/청산 live canary도 별도 cohort tag/rollback으로 병렬 승인 가능성을 검토한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 `1축 canary`만 허용하고, replacement도 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 예외: 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되고 판정이 provisional임을 명시할 때만 `stage-disjoint concurrent canary`로 검토할 수 있다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- 보유/청산 관찰은 `holding_exit_observation` 스냅샷으로만 판정하고, `partial/full`, `initial/pyramid`, `normal_only/post_fallback_deprecation`을 합산 결론으로 섞지 않는다.
- `soft_stop` 휩쏘 판정은 하방카운트(`low_score_hits`) 작동 여부와 함께 본다. 하드스탑은 `hard_stop_whipsaw_aux` 보조 관찰로만 두고, severe-loss guard 완화 canary로 바로 올리지 않는다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
- 대량 재처리는 `saved snapshot 우선 -> safe wrapper async dispatch -> completion artifact/Telegram` 순서만 허용하며, foreground direct build는 금지한다.
- 새 `shadow/canary` 경로 추가 또는 기존 분류(`remove / observe-only / baseline-promote / active-canary`) 변경은 같은 change set에서 [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md) 판정표를 함께 갱신해야 하며, 장후 review 항목은 누락 보정용으로만 쓴다.

## 장전 체크리스트 (08:20~)

- [ ] `[LatencyOps0427] gatekeeper_fast_reuse signature/window 독립축 PREOPEN 승인 판정` (`Due: 2026-04-27`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)
  - 판정 기준: `reuse window expired`와 `signature changed`를 분리하는 단일 조작점 1개와 rollback guard를 먼저 고정하고, `fallback 비결합`, `단일 live 1축`, `restart.flag` 반영 순서가 준비됐을 때만 live 승인/보류를 닫는다.
  - why: `2026-04-24 14:00 KST` 기준 `quote_fresh family`는 `submitted=0`, `quote_fresh_latency_pass_rate=0.0%`로 잠겼고, next independent axis는 `gatekeeper_fast_reuse signature/window`로만 남았다.
  - 다음 액션: 승인되면 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서로 PREOPEN 반영하고, 미승인이면 same-day `08:35 KST` 안에 막힌 이유 1개와 POSTCLOSE 재판정 시각 1개를 같이 고정한다.

- [ ] `[HoldingExitPrep0427] 보유/청산 관찰축 소스/부하분산 가드 및 stage-disjoint 예외 확인` (`Due: 2026-04-27`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:45`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `holding_exit_observation` 입력을 saved monitor snapshots, `data/post_sell/*.jsonl`, `data/pipeline_events/*.jsonl*`로 제한하고, fresh snapshot이 필요하면 `deploy/run_monitor_snapshot_incremental_cron.sh 2026-04-27` 또는 `deploy/run_monitor_snapshot_cron.sh 2026-04-27`만 쓴다.
  - why: 4월 보유/청산 분해는 표본이 커질 수 있어 장중 foreground direct build를 금지하고, existing full snapshot 또는 safe wrapper async 결과만 기준으로 삼아야 한다.
  - 다음 액션: `submitted_orders/full_fill/partial_fill/completed_valid` 잠금 필드와 `load_distribution_evidence` 존재를 확인하고, 보유/청산 live 후보가 있으면 `gatekeeper_fast_reuse`와 조작점/적용시점/cohort tag/rollback guard가 분리되는지 먼저 판정한다.

- [ ] `[HoldingExitData0427] holding_exit_observation 저장본 정합성 잠금` (`Due: 2026-04-27`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/report/monitor_snapshots/holding_exit_observation_2026-04-25.json`의 `soft_stop_rebound.rebound_above_sell_10m_rate/rebound_above_buy_10m_rate`를 raw `data/post_sell/post_sell_candidates_2026-04-09~2026-04-24.jsonl`, `data/post_sell/post_sell_evaluations_2026-04-09~2026-04-24.jsonl`와 현행 `holding_exit_observation_report` 로직으로 대조한다. 불일치 시 저장본은 stale로 잠그고 same-day 판정 basis는 raw 재집계값 `57/61(93.4%)`, `16/61(26.2%)`, `20m buy recovery 21/61(34.4%)`로 고정한다.
  - why: 현재 저장본에는 `4.9%/1.6%`가 남아 있지만 현행 raw+코드 재집계는 `93.4%/26.2%`로 크게 달라, soft_stop whipsaw 우선순위와 canary 승인 여부를 왜곡할 수 있다.
  - 다음 액션: 가능하면 safe wrapper 기준 산출물을 same-day 재생성하고, 재생성이 막히면 stale 사유와 raw basis 수치를 checklist/판정 메모에 함께 잠근다.

## 장중 체크리스트 (10:00~)

- [ ] `[HoldingExitCanary0427] soft_stop 1차 live canary 10시 중간점검` (`Due: 2026-04-27`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:10`, `Track: Plan`)
  - Source: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: PREOPEN에 soft_stop 보유/청산 live canary가 stage-disjoint 예외로 켜졌다면, `soft_stop qualifying cohort`, `submitted_orders/full_fill/partial_fill/completed_valid`, `soft_stop exit count`, `same_symbol_reentry_loss_count`, `fallback_regression=0`, `gatekeeper_fast_reuse` cohort tag 분리 여부, `rebound_above_sell_1m/3m`, `mfe_ge_0_5`, `low_score_hits`, `held_sec`, `ai_score`, `hard_stop_whipsaw_aux` 표본수를 잠근다.
  - why: 10시 중간점검은 pass/fail이 아니라 조기 오염 탐지다. 진입병목 canary가 유입 cohort를 바꾸더라도 보유/청산 canary cohort tag가 분리되면 병렬 관찰을 유지할 수 있다.
  - 다음 액션: cohort tag 혼선, fallback 회귀, soft_stop 전환율 급증, 매도 실패/복구 실패가 보이면 보유/청산 canary를 우선 OFF 후보로 올리고 11시 1차 판정을 기다리지 않는다.

- [ ] `[HoldingExitObs0427] submitted 회복 시 1차 관찰 개시 판정` (`Due: 2026-04-27`, `Slot: INTRADAY`, `TimeWindow: 11:00~11:15`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `submitted_orders >= 20` 또는 `full_fill + partial_fill >= 5`이면 관찰 개시로 잠그고, `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail 없이 방향성 판정만 한다. soft_stop 휩쏘는 `rebound_above_sell_10m`, `rebound_above_buy_10m`, `hit_up_05_10m`, `hit_up_10_10m`, `mfe_ge_0_5`, `mfe_ge_1_0`, `down_count_evidence.hit_distribution`, `qualified_loss_low_score_but_zero_hit`을 함께 본다.
  - why: submitted 회복 시 보유/청산 표본이 늦게 폭증할 수 있으므로, 1차 창에서 `normal_only/post_fallback_deprecation/full_fill/partial_fill/initial-only/pyramid-activated` 분리 카운트를 먼저 고정한다. 기존 4월 로그는 soft_stop 61건 중 10분 내 매도가 재상회 `57건(93.4%)`, +0.5% 이상 반등 `43건(70.5%)`이라 휩쏘 가설을 별도 축으로 확인해야 한다.
  - 다음 액션: `holding_exit_observation` snapshot의 `readiness`, `cohorts`, `soft_stop_rebound.whipsaw_windows`, `soft_stop_rebound.down_count_evidence`, `soft_stop_rebound.hard_stop_auxiliary`를 checklist에 반영하고, 1차 live canary는 `유지/축소/OFF/판정유예` 중 하나로 잠근다. `partial/full`, `initial/pyramid` 합산 결론이 있으면 무효 처리한다.

- [ ] `[HoldingExitObs0427] trailing/soft_stop/same_symbol 재분해` (`Due: 2026-04-27`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `scalp_trailing_take_profit`, `scalp_soft_stop_pct`, `scalp_ai_early_exit`, `scalp_preset_hard_stop_pct`, `scalp_hard_stop_pct`, `EOD/NXT`를 분리하고 `MISSED_UPSIDE/GOOD_EXIT/NEUTRAL`, `capture_efficiency`, `avg_extra_upside_10m_pct`, `soft_stop whipsaw_windows`, `down_count_evidence`, `hard_stop_auxiliary`, `COMPLETED valid profit_rate`를 함께 기록한다.
  - why: 4월 post-sell에서는 `MISSED_UPSIDE`와 `GOOD_EXIT`가 동시에 커서, trailing 연장 후보와 soft-stop rebound 후보를 같은 청산 개선축으로 묶으면 단일 조작점이 흐려진다.
  - 다음 액션: `soft_stop_rebound_split`을 손익 훼손 1순위로 먼저 산출하되, cooldown live는 `rebound_above_buy_10m`이 낮고 동일종목 재진입 손실이 확인될 때만 후보화한다. `low_score_hits`가 대부분 0이면 하방카운트는 휩쏘 방지장치가 아니라 미작동/후행 신호로 기록한다. `hard_stop_whipsaw_aux`는 보조 관찰로만 parking하고, `trailing_continuation_micro_canary`는 upside capture 2순위 후보로 남긴다.

## 장후 체크리스트 (15:40~)

- [ ] `[HoldingExitPlan0427] soft_stop 1순위 보유/청산 canary 승인 또는 보류+재시각 확정` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 1순위는 `soft_stop_rebound_split`이며, live 승인은 `soft_stop completed_valid 손익 훼손`, `rebound_above_sell_10m`, `rebound_above_buy_10m`, `mfe_ge_0_5`, `mfe_ge_1_0`, `same_symbol_reentry_loss_count`, `low_score_hits` 미작동 여부, `fallback_regression = 0`, stage-disjoint 예외 충족 여부를 함께 본다. 하드스탑은 `hard_stop_whipsaw_aux` 보조축으로만 해석한다.
  - why: 4월 기준 soft_stop의 realized loss 축이 trailing upside capture보다 직접 손익 훼손이 크고, 기존 로그는 soft_stop 이후 매도가 재상회/단기 반등이 많아 휩쏘 가능성이 높다. 다만 매수가 회복까지 높은 경우에는 cooldown live를 금지하고 threshold/AI 재판정 후보로 둔다.
  - 다음 액션: 승인 후보가 열리면 단일 조작점은 soft_stop qualifying cohort의 `whipsaw confirmation/micro grace` 1개로만 고정하고, `partial fill`, `pyramid-activated`, `EOD/NXT`, `fallback` 경로 제외와 rollback guard를 함께 남긴다. trailing은 `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`를 충족할 때만 2순위 후보로 재개한다.

## 장후 체크리스트 (18:05~18:20)

- [ ] `[OpsFollowup0427] pattern lab postclose 산출물/로그 보수 및 재실행 확인` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: Plan`)
  - Source: [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/2026-04-24-stage2-todo-checklist.md)
  - 판정 기준: `deploy/run_tuning_monitoring_postclose.sh` 기준 실제 로그 경로를 `logs/tuning_monitoring_postclose_cron.log`로 통일해 확인하고, Gemini pattern lab의 `trade_id` dtype merge 오류를 해소한 뒤 `analysis/gemini_scalping_pattern_lab/outputs/*`, `analysis/claude_scalping_pattern_lab/outputs/*` 최신 산출물이 `2026-04-27 POSTCLOSE` 시각으로 갱신되어야 한다.
  - why: `2026-04-24` 점검에서 전용 cron log 두 개는 더 이상 생성되지 않았고, 통합 로그에는 Gemini 분석이 `trade_id str/float64 merge` 예외로 실패한 흔적이 남았다.
  - 다음 액션: 보수 완료 시 same-day 결과를 checklist와 execution delta에 함께 반영한다.

- [x] `[LoopMetrics0427] LOOP_METRICS 실로그 분포 확인` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: ScalpingLogic`)
  - Source: [workorder-kiwoom-sniper-v2-loop-performance-improvement.md](/home/ubuntu/KORStockScan/docs/workorder-kiwoom-sniper-v2-loop-performance-improvement.md)
  - 판정 기준: 장중/장후 생성된 `[LOOP_METRICS]` 실로그에서 `loop_elapsed_ms`, `db_active_targets_ms`, `account_sync_ms`, `target_count`, `watching`, `holding`이 최소 1회 이상 기록되고, 값 누락/파싱불가 없이 운영 해석 가능한지 확인한다.
  - why: 이번 P0/P1은 테스트 통과만으로 닫을 수 없고, 실제 장중 로그에서 루프 지연과 동기 I/O 시간이 기대한 형식으로 남는지 확인해야 후속 `sleep` canary와 주문/AI worker 판단 근거가 생긴다.
  - 다음 액션: `loop_elapsed_ms` 상위 구간, `db_active_targets_ms`/`account_sync_ms` 이상치, 샘플 수 부족 여부를 same-day 메모로 잠그고, 후속 P2 착수 전 기준선으로 재사용한다.

- [x] `[GatekeeperAsync0427] sniper_gatekeeper_replay.py 비동기 writer + dedup 롤백 구현 완료` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: ScalpingLogic`)
  - Source: [workorder-sniper-codebase-performance-audit-followup.md](/home/ubuntu/KORStockScan/docs/workorder-sniper-codebase-performance-audit-followup.md)
  - 완료 내역:
    - 축 A: `_ensure_state_handler_deps()`를 6개 wrapper에서 제거하고 `run_sniper()` loop 상단(1224)으로 이동
    - 축 B: `_RECENT_SNAPSHOT_SIGNATURES` TTL prune (`_prune_stale_signatures`, 5분 간격)
    - 축 B: `_append_jsonl_async()` — single-thread ThreadPoolExecutor writer
    - 축 B: `atexit.register(_flush_jsonl_writer)` — process-exit flush
    - 축 B: `submit()` done callback + `_rollback_signature` dedup 롤백 (worker write 실패 시)
    - 축 B: enqueue 실패 → 동기 fallback write 실패 시 dedup 롤백 (내부 try/except)
    - 축 B: 모든 `_RECENT_SNAPSHOT_SIGNATURES` 접근을 `_WRITE_LOCK` 아래 통일
    - 축 B: dedup 시그니처를 main thread에서 즉시 기록 (중복 enqueue 방지)
    - 축 B: `_replay_dir()`의 `mkdir` 실패를 try/except로 감싸서 `_WRITE_LOCK` 블록 내 예외 방지
  - 검증: 29개 테스트 전부 PASSED
  - 리스크 해소: `enqueue 실패 -> fallback write 실패 -> 성공처럼 반환`, `callback dedup 갱신 중 concurrent mutation`, `동일 payload 중복 enqueue`, `worker/fallback write 실패 후 dedup 오염`을 모두 차단했다.
  - 잔여 운영 리스크: `record_gatekeeper_snapshot()`의 성공 반환은 `persist confirmed`가 아니라 `enqueue accepted 또는 동기 fallback write 성공` 의미다. worker thread의 후행 write 실패는 callback `log_error + dedup rollback`으로만 관측된다.
  - 다음 액션: 실제 장중 `[GATEKEEPER_SNAPSHOT]` 로그와 replay jsonl 파일을 대조해 `enqueue accepted`와 `persist confirmed`가 어긋나는 사례가 있는지 운영 acceptance로 확인한다.

- [ ] `[GatekeeperAsyncOps0427] GATEKEEPER_SNAPSHOT async persist 운영 acceptance 확인` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: ScalpingLogic`)
  - Source: [workorder-sniper-codebase-performance-audit-followup.md](/home/ubuntu/KORStockScan/docs/workorder-sniper-codebase-performance-audit-followup.md)
  - 판정 기준: 장중/장후 `[GATEKEEPER_SNAPSHOT]` 성공 로그와 `data/gatekeeper/gatekeeper_snapshots_2026-04-27.jsonl` 실제 line 증가를 대조해, `enqueue accepted` 후 worker write 실패가 있었다면 callback `log_error`와 dedup rollback이 같은 구간에 남는지 확인한다.
  - why: 현재 구현은 동기 fallback 실패는 `None`으로 닫지만, async worker 실패는 best-effort 규약상 후행 rollback으로만 관측된다. 따라서 코드 테스트 통과와 별개로 실로그 기준 persist 정합성 확인이 필요하다.
  - 다음 액션: mismatch가 없으면 async writer 규약을 운영 기준선으로 잠그고, mismatch가 있으면 `persist confirmed` 필요 구간을 동기 write 또는 명시적 ack 구조로 재분해한다.

- [ ] `[CodeDebt0427] shadow/canary 런타임 경로 일일 분류/정리 판정` (`Due: 2026-04-27`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 당일 코드/운영 결과를 기준으로 `dual_persona`, `watching_prompt_75_shadow`, `hard_time_stop_shadow`, `ai_holding_shadow_band`, `dynamic_strength_canary(dynamic_strength_relief)`, `other_danger_relief_canary`, `partial_fill_ratio_canary(partial_fill_ratio_guard)`의 분류(`remove`, `observe-only`, `baseline-promote`, `active-canary`)에 변동이 있는지 닫고, 변동 시 same-day 코드정리 후보 또는 다음 독립축 후보까지 함께 기록한다.
  - why: `shadow 금지`, `canary-only`, `baseline 승격` 원칙은 문서 선언만으로 유지되지 않고, 매일 장후 실코드/실운영 상태와 다시 맞춰야 다음 기대값 개선축의 원인귀속이 흐려지지 않는다.
  - 다음 액션: 분류 변경이 있으면 checklist와 관련 기준문서에 함께 반영하고, 변경이 없으면 `변동 없음`과 근거만 잠근다.
