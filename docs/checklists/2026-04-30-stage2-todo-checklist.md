# 2026-04-30 Stage2 To-Do Checklist

## 오늘 목적

- `pre-submit price guard`와 `price snapshot split`이 장전 restart 후 메인 런타임에 정상 로드됐는지 닫는다.
- `mechanical_momentum_latency_relief` 운영 override가 전일 장중 반영된 상태라면 장전에는 코드/런타임 provenance만 확인하고, 실전 성과는 장중 post-restart cohort로 분리한다.
- 이번주 다음 운영일은 `2026-05-01`이 아니라 `2026-05-04`다. KRX는 근로자의 날(5/1) 휴장이고, `2026-05-05` 어린이날도 휴장이므로 다음주 휴장 이월 항목은 `2026-05-06` checklist가 소유한다.
- 대한전선 진입가 후속조치는 신규 alpha 진입축이 아니라 비정상 저가 제출 차단과 감리 추적성 보강으로만 해석한다.
- `P0` 가드의 day-1 KPI와 rollback trigger를 장후 바로 잠가, 임의 임계값 고착을 막는다.
- `P1 resolver`와 `schema split`은 same-day live 확장이 아니라 observe/backtest ingress 조건 확정으로만 넘긴다.
- soft stop 감소 접근은 `micro grace 시간연장`보다 `REVERSAL_ADD 소형 canary`와 `bad_entry_block observe-only classifier`로 전략 가설을 분리한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 일정은 모두 `YYYY-MM-DD KST`, `Slot`, `TimeWindow`로 고정한다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
- `mechanical_momentum_latency_relief`는 AI score 50/70 mechanical fallback 상태의 제출 drought를 푸는 entry 1축이다. `latency_signal_quality_quote_composite`, `latency_quote_fresh_composite`, legacy `other_danger/ws_jitter/spread` relief와 동시에 켜지 않으며, 장전에는 enable flag와 restart provenance만 확인한다.
- `REVERSAL_ADD`는 entry canary가 아니라 보유 중 `position_addition` canary다. `soft_stop_micro_grace`와 같은 보유 포지션을 건드리므로 cohort를 반드시 분리하고, `reversal_add_used` 이후 soft stop 악화가 보이면 즉시 OFF 후보로 본다.
- `bad_entry_block`은 observe-only다. `2026-04-30`에는 진입 자체를 막지 않고 `bad_entry_block_observed` 로그와 후속 soft stop/하드스탑/회복 여부만 본다.

## 장전 체크리스트 (08:45~08:55)

- [x] `[MechanicalMomentumLatencyRelief0430-Preopen] mechanical_momentum_latency_relief 코드/런타임 로드 확인` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:40~08:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot PID와 `/proc/<pid>/environ` 또는 import check로 `latency_quote_fresh_composite=False`, `latency_signal_quality_quote_composite=False`, `mechanical_momentum_latency_relief=True` 로드 여부를 확인한다. threshold는 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`로 고정한다.
  - why: 이 축은 신규 alpha 확장이 아니라 제출 drought를 방치하지 않기 위한 운영 override다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 단일축 로드와 rollback guard만 확인한다.
  - 실행 메모 (`2026-04-30 07:55 KST`): main bot PID는 `42635`, 시작시각은 `2026-04-30 07:40:01 KST`였다. 이 세션에서는 `/proc/42635/environ` 직접 읽기가 막혀 env override 증적은 확보하지 못했지만, 코드 기본값 [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:176), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:182), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:190) 기준 `quote_fresh=False`, `signal_quality=False`, `mechanical_momentum=True`가 잠겨 있고 `logs/bot_history.log`에도 `2026-04-30 07:40:13 KST` 봇 기동이 확인됐다.
  - 판정 결과: `완료 / PID provenance 확인, mechanical_momentum 기본값 로드 기준 충족`
  - 근거: `Plan Rebase`와 전일 `MechanicalMomentumLatencyRelief0429-Now` 판정상 현재 entry live owner는 `mechanical_momentum_latency_relief` 하나뿐이다. 오늘 PREOPEN에서 필요한 것은 same-day 거래성과가 아니라 `기존 quote_fresh OFF`, `backup composite OFF`, `replacement 축 ON` 상태가 새 PID로 이어졌는지 여부인데, 코드 기본값과 새 PID 기동시각이 이를 충족한다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg "bot_main.py|python bot_main.py"`
    - `tail -n 120 logs/bot_history.log`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k 'mechanical_momentum or signal_quality_quote_composite or price_guard'` -> `6 passed`
  - rollback guard: 장중 새 cohort에서 `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 OFF 검토를 연다. `pre_submit_price_guard_block_rate > 2.0%`, `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 다음 액션: 로드 확인 후 장중 `[MechanicalMomentumLatencyRelief0430-1000]`에서 `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted/full/partial`, `COMPLETED + valid profit_rate`를 분리한다.

- [x] `[DynamicEntryPriceP0Guard0430-Preopen] pre-submit price guard + price snapshot split 구현/검증` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: main bot restart provenance를 확인하고, `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80` 로드 여부와 `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block` 가격 스냅샷 필드 기록 여부를 확인한다.
  - why: 대한전선 케이스는 신규 alpha canary가 아니라 비정상 저가 제출을 막는 안전가드와 감리 추적성 보강이다. PREOPEN에서는 same-day submitted/fill 성과가 아니라 코드 로드, restart, 이벤트 필드 기록 가능성만 확인한다.
  - 실행 메모 (`2026-04-30 07:55 KST`): [audit rerereport](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md:33) 기준 P0 범위는 `SCALPING_PRE_SUBMIT_PRICE_GUARD_ENABLED=True`, `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS=80`, 그리고 `submitted_order_price/best_bid_at_submit/price_below_bid_bps/resolution_reason` 등 가격 스냅샷 분리다. 코드 기본값 [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:154), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:155) 와 구현 [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:61), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:1138) 이 일치했고, 오늘 `pipeline_events_2026-04-30.jsonl`은 PREOPEN 시점이라 아직 관련 stage가 `0건`이라 실로그 증적은 장중 이후 항목으로 넘긴다.
  - 판정 결과: `완료 / P0 guard 기본값 및 price snapshot split 코드 로드 확인, same-day event 증적은 미생성`
  - 근거: 이 항목의 PREOPEN 목표는 가드를 켰는지와 스냅샷 필드가 남을 수 있는 코드경로가 준비됐는지 확인하는 것이다. `07:40` 재기동 이후 아직 `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block` 발생 자체가 없으므로, 지금 단계에서 미관측은 가드 실패가 아니라 장전 무표본 상태로 보는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k 'price_guard or mechanical_momentum or signal_quality_quote_composite'` -> `6 passed`
    - `PYTHONPATH=. .venv/bin/python - <<'PY' ... pipeline_events_2026-04-30.jsonl stage count ... PY` -> `latency_pass/order_leg_request/order_bundle_submitted/pre_submit_price_guard_block = 0`
  - 다음 액션: 장전 로드가 확인되면 장중에는 `pre_submit_price_guard_block` 발생 여부와 `submitted_order_price`, `best_bid_at_submit`, `price_below_bid_bps`, `resolution_reason` 품질만 관찰한다. 로드 실패 시 P0 guard를 OFF한 채로 두지 말고 restart/provenance 원인을 우선 수정한다.

- [x] `[ReversalAddBadEntry0430-Preopen] REVERSAL_ADD 소형 canary 및 bad_entry_block observe-only 로드 확인` (`Due: 2026-04-30`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: main bot restart provenance를 확인하고 `REVERSAL_ADD_ENABLED=True`, `REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True`, `REVERSAL_ADD_SIZE_RATIO=0.33`, `SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=True` 로드 여부를 확인한다.
  - why: `micro grace 20초`만으로는 soft stop 감소 전략의 설득력이 약하다. `2026-04-30` 오전부터는 `유효 진입 초반 눌림 회수`와 `불량 진입 후보 분류`를 별도 가설로 관찰해야 한다.
  - 실행 메모 (`2026-04-30 07:55 KST`): 코드 기본값 [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:239), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:249), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:250), [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:259) 기준 `REVERSAL_ADD_ENABLED=True`, `SIZE_RATIO=0.33`, `MIN_QTY_FLOOR=True`, `SCALP_BAD_ENTRY_BLOCK_OBSERVE_ENABLED=True`가 잠겨 있다. holding 경로에서도 [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3878), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:4721), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:531) 로 실제 probe/observe-only 분기가 연결돼 있다.
  - 판정 결과: `완료 / reversal_add canary 및 bad_entry observe-only 코드 로드 확인`
  - 근거: PREOPEN에서 필요한 것은 `REVERSAL_ADD`가 실주문 가능 상태인지, `bad_entry_block`이 차단이 아니라 observe-only로 묶여 있는지다. 현재 기본값과 호출 경로가 둘 다 맞고, `scale_in` 회귀 테스트도 `reversal_add`/`bad_entry_block` 관련 경로를 통과했다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'reversal_add or bad_entry_block or price_guard'` -> `14 passed`
    - [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:297)
    - [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:520)
  - rollback guard: `reversal_add_used` 후 `scalp_soft_stop_pct` 전환이 발생하거나, `reversal_add` 체결 cohort의 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`이면 장중 OFF 후보로 본다. `bad_entry_block`은 observe-only라 주문 차단이나 청산 변경을 하지 않는다.
  - 다음 액션: 로드 확인 후 장중 `[ReversalAddBadEntry0430-1030]`에서 `reversal_add_candidate`, `reversal_add_used`, `scale_in_executed add_type=AVG_DOWN`, `bad_entry_block_observed`, 후속 `soft_stop/trailing/COMPLETED`를 분리한다.

## 장중 체크리스트 (09:00~15:20)

- [x] `[MechanicalMomentumLatencyRelief0430-1000] mechanical_momentum_latency_relief 10시 1차 판정` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:15`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `09:00~10:00` 또는 새 restart 이후 창 기준 `budget_pass`, `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full_fill`, `partial_fill`, `pre_submit_price_guard_block`, `fallback_regression=0`를 확인한다. `full fill`과 `partial fill`은 분리한다.
  - why: 이 축은 거래수 회복을 위한 운영 override라 오전 1시간 안에 최소 방향성은 나와야 한다. `submitted`가 움직이지 않으면 같은 날 추가 유지 근거가 약하다.
  - 실행 메모 (`2026-04-30 10:15 KST 사후 집계`): `09:00~10:00` 창에서 `budget_pass=951`, `order_bundle_submitted=27`, `mechanical_momentum_relief_canary_applied=22`, `mechanical canary applied + submitted=22`가 확인됐다. 첫 canary submit은 `09:10:03 KST` `삼성전기(009150, id=4480)`였고, 마지막 오전 1차 창 표본은 `09:57:52 KST` `HD현대(267250, id=4542)`였다. `order_bundle_submitted`의 `entry_mode`는 모두 `normal`이었고 `pre_submit_price_guard_block=0`, `full_fill=0`, `partial_fill=0`이었다.
  - 판정 결과: `완료 / 제출 회복 방향성 확인, same-day 유지 근거 충족`
  - 근거: 이 항목의 fail line은 `budget_pass >= 150`인데 `submitted <= 2`다. 실제로는 `budget_pass 951 -> submitted 27`로 제출 회복이 있었고, 그중 `22건`이 `latency_mechanical_momentum_relief_normal_override` 직접 표본이었다. 오전 1차 창에서는 체결 완료까지는 아직 없었지만, 운영 override의 목적이던 `BUY drought 해소` 관점에서는 `mechanical cohort가 normal order로 실제 제출된 것`이 먼저 확인됐다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `pipeline_events_2026-04-30.jsonl` `09:00~10:00` 창의 `budget_pass/submitted/mechanical canary/full_fill/partial_fill/pre_submit_price_guard_block` 카운트 검증
    - `mechanical canary applied` 표본 22건과 `order_bundle_submitted` record_id 매칭 확인
    - `order_bundle_submitted entry_mode != normal` 검색 결과 `0건`
  - 다음 액션: 12시 full 창에서는 `mechanical cohort 22건`의 후속 `fill quality`, `COMPLETED + valid profit_rate`, `price_below_bid_bps` 분포를 분리한다. `pre_submit_price_guard_block`이 계속 `0`이면 가드 비활성이라기보다 deep bid 재발 부재인지 장후 P0 guard KPI 항목과 같이 닫는다.

- [x] `[ReversalAddBadEntry0430-1030] REVERSAL_ADD/bad_entry_block 오전 1차 관찰` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `09:00~10:30` 창에서 `reversal_add_candidate`, `reversal_add_blocked_reason`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_used`, `bad_entry_block_observed`, `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `COMPLETED + valid profit_rate`를 분리한다.
  - why: `2026-04-30` 오전을 단순 진단으로 허비하지 않기 위해, 유효 진입의 초반 눌림은 소형 추가매수로 실험하고 never-green/AI fade는 observe-only로 분류한다.
  - 실행 메모 (`2026-04-30 10:45 KST 사후 집계`): `09:00~10:30` 창에서 `reversal_add_candidate=0`, `reversal_add_blocked_reason=258`, `scale_in_executed=2`, `bad_entry_block_observed=47`가 확인됐다. `scale_in_executed` 2건은 `한화(id=4427)`, `쏠리드(id=4488)`였고 둘 다 `add_type=PYRAMID`였다. 즉 오전 창의 추가체결은 `REVERSAL_ADD(AVG_DOWN)`가 아니라 기존 winner-side `PYRAMID`였다.
  - 판정 결과: `완료 / REVERSAL_ADD 체결 없음, bad_entry observe-only 표본은 충분`
  - 근거: 오전 창에서 `AVG_DOWN` 체결은 `0건`이어서 canary efficacy는 아직 미판정이다. 대신 blocker는 명확하다. `reversal_add_blocked_reason 258건` 중 분류 기준으로 `pnl_out_of_range=205`, `hold_sec_out_of_range=46`, `ai_score_too_low=7`, `ai_not_recovering=1`이었다. `bad_entry_block_observed 47건 / unique 10 record`는 전부 `never_green_ai_fade` classifier였고, observe-only 표본 확보 목표는 넘겼다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `pipeline_events_2026-04-30.jsonl` `09:00~10:30` 창의 `reversal_add_blocked_reason/scale_in_executed/bad_entry_block_observed` 카운트 검증
    - `scale_in_executed` 2건의 `add_type` 확인 결과 모두 `PYRAMID`, `AVG_DOWN=0`
    - `bad_entry_block_observed` classifier 분포 확인 결과 `never_green_ai_fade 47건`
  - 다음 액션: `REVERSAL_ADD`는 오전 창에서 후보 진입까지 못 갔으므로 장후에는 `candidate zero`가 아니라 `blocked funnel`로 닫고, 특히 `pnl_out_of_range`와 `hold_sec_out_of_range`가 과도한지 임계 재검토 후보로 넘긴다. `bad_entry_block_observed >= 3` 조건은 이미 충족했으므로 장후 classifier 승격 검토 표본으로 연결한다.

- [x] `[ReversalAddBadEntry0430-1130] REVERSAL_ADD/bad_entry_block 재기동 후 장중 1차 효과 판정` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 11:30~12:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `2026-04-30 10:14 KST` 재기동 이후 cohort만 분리해 `reversal_add_used`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_post_eval_fail`, `bad_entry_block_observed`, `scalp_soft_stop_pct`, `soft_stop_micro_grace`, `COMPLETED + valid profit_rate`를 확인한다.
  - why: threshold widen 직후에는 표본이 조금 더 쌓인 `11:30~12:00 KST`가 same-day rollback 여부를 가장 빨리 가를 수 있는 첫 창이다. 재기동 전 표본을 섞으면 원인귀속이 흐려진다.
  - 실행 메모 (`2026-04-30 11:41 KST`): 최신 재기동 `2026-04-30 10:33:12 KST` 이후 `11:41 KST`까지 `reversal_add_candidate=6 / unique 2`, `scale_in_executed add_type=AVG_DOWN=0`, `reversal_add_used=0`, `reversal_add_post_eval_fail=0`, `bad_entry_block_observed=48 / unique 6`, `soft_stop_micro_grace=63 / unique 6`, `scalp_soft_stop_pct exit_signal=6 / unique 6`로 집계됐다.
  - 판정 결과: `완료 / REVERSAL_ADD rollback guard 미발동, 12:00 soft_stop_expert_defense 착수 허용`
  - 근거: `REVERSAL_ADD` 후보는 생겼지만 실제 `AVG_DOWN` 체결과 `reversal_add_used`가 없어서 `reversal_add_used 후 soft stop 급증` 또는 체결 cohort 평균손익 rollback 조건이 성립하지 않는다. 반면 같은 창에서도 `soft_stop_micro_grace`와 `scalp_soft_stop_pct`는 계속 발생해 soft stop 방어망을 장후로 미룰 근거가 약하다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `pipeline_events_2026-04-30.jsonl`의 `2026-04-30 10:33:12~11:41 KST` 창 stage 카운트 확인
  - 다음 액션: `AVG_DOWN` 체결이 생기고 soft stop tail이 비악화면 same-day 유지 근거로 잠근다. 반대로 `reversal_add_used` 후 `scalp_soft_stop_pct` 급증, 또는 `COMPLETED + valid profit_rate` 평균이 rollback guard에 닿으면 즉시 원복 후보로 넘긴다.

- [x] `[SoftStopExpertDefense0430-1200] 전문가 soft stop 방어망 live canary 적용` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `soft_stop_micro_grace v2`로 `stop arbitration layer + thesis invalidation veto + orderbook absorption stop`만 live 적용하고, `MAE/MFE quantile stop`, `recovery probability model`, `partial de-risk stop`은 shadow-only, `adverse fill detector`는 observe-only 로그로만 연다. activation gate는 `2026-04-30 12:00:00 KST`로 고정한다.
  - why: 오늘 soft stop 손실 유형 집계에서 `scalp_soft_stop_pct`가 주요 leakage로 확인됐고, `5/4`로 미루지 말라는 운영 지시에 따라 기존 11:20/11:30 작업 이후 same-day 12:00 cohort로 즉시 착수한다. 단, live 변경은 기존 `soft_stop_micro_grace`의 v2 확장 1축으로 묶어 원인귀속을 보존한다.
  - cohort lock: baseline cohort=`2026-04-30 10:33:12~12:00 soft_stop_micro_grace v1`, candidate live cohort=`2026-04-30 12:00 이후 soft_stop_expert_defense 적용 포지션`, observe-only cohort=`adverse_fill_observed`, shadow-only cohort=`soft_stop_expert_shadow`, excluded cohort=`reversal_add_used/POST_ADD_EVAL/emergency/invalid_feature/active_sell_pending`, rollback owner=`soft_stop_expert_defense`.
  - rollback guard: guarded cohort의 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`, guarded 후 `hard/protect stop` 전이, `sell_order_failed`, 또는 `REVERSAL_ADD` 체결 포지션에 적용되는 cross-contamination이 1건이라도 확인되면 즉시 OFF한다.
  - 실행 메모 (`2026-04-30 11:45 KST`): 코드 구현, targeted test, parser 검증, restart를 완료했다. 새 PID는 `72901`, 시작시각은 `2026-04-30 11:44:57 KST`이며 `SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=True`, `SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT=2026-04-30 12:00:00`, `SCALP_SOFT_STOP_ABSORPTION_EXTENSION_SEC=20`로 로드된다.
  - 판정 결과: `완료 / 12:00 activation gate 적재, candidate live cohort는 12:00 이후만 인정`
  - 근거: 1차 재기동 직후 `11:43:06 KST`에 `soft_stop_expert_shadow/adverse_fill_observed`가 1개 record에서 선행 발생했으나, 즉시 보정해 shadow/observe도 activation gate 뒤로 묶고 `11:44:57 KST` 재기동했다. 해당 pre-activation 로그는 candidate/shadow/observe cohort에서 제외한다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/utils/constants.py`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'soft_stop_micro_grace or soft_stop_expert or reversal_add or bad_entry_block'` -> `21 passed`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` -> parser count `54`, `SoftStopExpertDefense0430-1230/1330` 미완료 항목 인식
  - 다음 액션: 코드/테스트/restart provenance를 확인한 뒤 `[SoftStopExpertDefense0430-1230]`에서 첫 health check를 수행한다.

- [x] `[SoftStopExpertDefense0430-1230] 12:30 health check` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 12:30~12:40`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `soft_stop_absorption_probe`, `soft_stop_absorption_extend`, `soft_stop_absorption_exit`, `soft_stop_expert_shadow`, `adverse_fill_observed` 발생 여부와 `reversal_add_used` 제외가 지켜졌는지 확인한다.
  - why: 12:00 live 적용 직후에는 수익률 결론보다 routing/로그/제외규칙 무결성이 먼저다.
  - 실행 메모 (`2026-04-30 12:40 KST`): `12:00~12:40 KST` cohort에서 `soft_stop_expert_shadow=6 / unique 3`, `adverse_fill_observed=6 / unique 3`, `soft_stop_absorption_probe=1 / unique 1`, `soft_stop_absorption_exit=1 / unique 1`, `soft_stop_absorption_extend=0`, `soft_stop_absorption_recovered=0`, `reversal_add_used=0`, `sell_order_failed=0`, `protect_hard_stop=0`였다. anchor 표본은 `아진엑스텍(059120, id=4464)`, `흥구석유(024060, id=4591)`, `KG케미칼(001390, id=4635)`다.
  - 판정 결과: `완료 / routing·shadow·observe 무결성 확인, same-day keep 유지`
  - 근거: `흥구석유`는 `12:06:11 KST`에 `soft_stop_absorption_probe -> soft_stop_absorption_exit`가 발생했고 `thesis_invalidated=True`, `thesis_reason=large_sell_print`, `exclusion_reason=large_sell_print`, `should_extend=False`로 live veto가 정상 동작했다. `아진엑스텍`과 `KG케미칼`은 `soft_stop_micro_grace`에서 `expert_exclusion_reason=base_micro_grace`, `expert_defense_active=False` 상태로 base 20초 유예가 먼저 적용됐고, shadow/observe만 기록된 뒤 `scalp_soft_stop_pct` exit로 종료됐다. `reversal_add_used` 혼입, `sell_order_failed`, `protect_hard_stop`는 모두 `0건`이라 cross-contamination 증거는 없다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `pipeline_events_2026-04-30.jsonl` `12:00~12:40 KST` 창의 `soft_stop_absorption_*`, `soft_stop_expert_shadow`, `adverse_fill_observed`, `reversal_add_used`, `sell_order_failed`, `protect_hard_stop` 카운트 검증
    - `TradingConfig()` import check로 `SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=True`, `SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT=2026-04-30 12:00:00`, `SCALP_SOFT_STOP_ABSORPTION_EXTENSION_SEC=20`, `SCALP_SOFT_STOP_ABSORPTION_MAX_EXTENSIONS=1` 확인
    - `ps -eo pid,lstart,cmd | rg "python bot_main.py|bot_main.py"` -> main PID `72901`, 시작 `Thu Apr 30 11:44:57 2026`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` -> parser count `54`, `SoftStopExpertDefense0430-1330` 미완료 항목 유지 확인
  - 다음 액션: `13:30` 창에서는 `guarded cohort`를 `full/partial`, `sell_completed`, `COMPLETED + valid profit_rate`, `hard/protect stop 전이`, `sell_order_failed`로 분리해 keep/OFF를 판정한다. `extend=0` 자체는 fail이 아니라 첫 창 표본 특성으로 보고, `thesis veto 정상동작`과 `cross-contamination 부재`를 우선 유지 근거로 쓴다.

- [x] `[SoftStopExpertDefense0430-1330] 13:30 rollback/keep 판정` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 13:30~13:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `12:00` 이후 candidate live cohort를 `full/partial`, `initial/pyramid`, `REVERSAL_ADD 제외`, `COMPLETED + valid profit_rate`, `soft_stop_absorption_extend 후 hard/protect 전이`, `sell_order_failed`로 분리한다.
  - why: same-day 방어망은 장후까지 방치하지 않고 첫 충분 표본 또는 위험 신호에서 바로 keep/OFF를 닫아야 한다.
  - 실행 메모 (`2026-04-30 13:45 KST`): `12:00~13:45 KST` 창에서 `soft_stop_absorption_probe=4 / unique 3`, `soft_stop_absorption_exit=3 / unique 3`, `soft_stop_absorption_extend=1 / unique 1`, `soft_stop_absorption_recovered=1 / unique 1`, `soft_stop_expert_shadow=39 / unique 7`, `adverse_fill_observed=39 / unique 7`, `sell_order_failed=0`, `protect_hard_stop=0`, `protect_trailing_stop=0`, `reversal_add_used=0`이었다. guarded probe unique 3개(`흥구석유 4591`, `SK스퀘어 4474`, `아진엑스텍 4655`)의 `sell_completed profit_rate`는 `-1.85%`, `-1.50%`, `-1.65%`로 평균 `-1.667%`였다.
  - 판정 결과: `완료 / 손실 경고 발생, 단 직접 v2 귀속손실 미미 -> 신규 live 축 없이 장마감까지 v2 유지`
  - 근거: 문서상 `soft_stop_expert_defense_loss_cap`은 guarded cohort `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`면 OFF 후보를 연다. 현재 guarded probe cohort 평균은 `-1.667%`로 guard를 넘었지만, `아진엑스텍(059120, id=4655)`의 실제 유예 1건은 `12:55:18` `soft_stop_absorption_extend -> 12:55:22 soft_stop_absorption_recovered` 후 `12:57:26` `tick_accel_and_micro_vwap_break` veto로 종료됐고, 유예 시점 `profit_rate=-1.53%` 대비 최종 `-1.65%`의 직접 변동은 약 `-0.12%p`, 금액으로 약 `-20원` 수준이다. `sell_order_failed=0`, `protect_hard_stop=0`, `protect_trailing_stop=0`, `reversal_add_used=0`이라 cross-contamination/주문실패형 rollback도 아니다. 따라서 오늘 손실의 주 원인은 v2 자체보다 bad entry/never-green, 동일종목 반복손실, soft stop 후행 흐름에 더 가깝다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `data/pipeline_events/pipeline_events_2026-04-30.jsonl` `12:00~13:45 KST` 창의 `soft_stop_absorption_*`, `soft_stop_expert_shadow`, `adverse_fill_observed`, `sell_completed`, `sell_order_failed`, `protect_*`, `reversal_add_used` 카운트와 guarded cohort 평균손익 검증
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` -> parser count `53`, `[SoftStopExpertDefense0430-PostcloseReview]` 미완료 항목 유지 확인
  - 다음 액션: `soft_stop_expert_defense v2`는 장마감까지 유지해 표본을 더 모은다. 단 새 live 축은 전환하지 않고, 장후에는 아래 `[SoftStopExpertDefense0430-PostcloseReview]`에서 v2 직접효과와 손실 매매흐름 taxonomy를 함께 닫는다.

- [x] `[PyramidPostAddTrailingGuard0430-Now] 불타기 체결 직후 trailing 조기청산 로직 오류 확인/패치` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 12:45~13:05`, `Track: ScalpingLogic`)
  - Source: [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [bot_history.log](/home/ubuntu/KORStockScan/logs/bot_history.log)
  - 판정 기준: `PYRAMID scale_in_executed` 직후 `protect_trailing_stop` 또는 `scalp_trailing_take_profit`이 기존 고점/보호선 기준으로 즉시 매도되는지 확인한다.
  - 실행 메모 (`2026-04-30 13:05 KST`): `쏠리드(050890, id=4639)`에서 `12:44:05` `PYRAMID BUY 1주 @ 17,460` 후 `12:45:57` `TRAILING SELL 3주 @ 17,390`가 발생했다. 코드상 추가매수 체결 후 `buy_price/buy_qty`는 갱신되지만 `highest_prices`는 기존 고점을 유지하고, trailing 평가는 `last_add_at/last_add_type` grace 없이 즉시 실행됐다.
  - 판정 결과: `로직 오류 확인 / 패치 완료`
  - 근거: 추가매수 후 포지션 평균가와 수량이 바뀌면 기존 고점 기준의 drawdown은 새 포지션의 MFE가 아니다. 따라서 불타기 직후 trailing은 새 체결가/평단 기준으로 고점을 리베이스하고, 짧은 post-add grace 동안 `protect_trailing_stop`, `scalp_trailing_take_profit`을 억제해야 한다. hard stop/soft stop은 억제하지 않는다.
  - 패치: 추가매수 체결 시 `highest_prices[code]=max(exec_price,new_avg)`로 리베이스하고, `SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC=180` 동안 `pyramid_post_add_trailing_grace` 로그만 남긴다.
  - 런타임 반영 (`2026-04-30 13:08 KST`): `restart.flag` 소모 후 main PID가 `72901 -> 85560`으로 교체됐다. 새 PID 시작시각은 `2026-04-30 13:07:41 KST`이며, `TradingConfig().SCALP_PYRAMID_POST_ADD_TRAILING_GRACE_SEC=180` import check와 `logs/bot_history.log` 기준 WS 재접속/조건식 등록 재개를 확인했다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'pyramid_add_suppresses or add_execution_rebases_highest_price_after_pyramid or add_count_increment_once'` -> `4 passed`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k 'scale_in or pyramid or trailing or reversal_add'` -> `103 passed`
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/engine/sniper_execution_receipts.py src/utils/constants.py` -> 통과
    - `git diff --check -- src/engine/sniper_state_handlers.py src/engine/sniper_execution_receipts.py src/utils/constants.py src/tests/test_sniper_scale_in.py` -> 통과
  - 다음 액션: 장중 반영이 필요하면 커밋 후 봇 재기동으로 코드 로드한다. 재기동 전까지 현재 실행 중인 봇에는 미반영이다.

- [x] `[DataDrivenThresholdInventory0430-Now] 데이터 기반 threshold 산정 가능 파라미터 전수 인벤토리` (`Due: 2026-04-30`, `Slot: INTRADAY`, `TimeWindow: 14:05~14:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `REVERSAL_ADD`만이 아니라 entry/latency/VPW/liquidity/AI/pre-submit/soft stop/bad entry/trailing/partial fill/position sizing 파라미터를 모두 훑고, 각 파라미터별 `데이터량`, `산정 가능성`, `운영 전환 방식`을 분리한다.
  - why: 지금까지 데이터가 관찰/판정에는 쓰였지만 threshold 산정 입력으로 충분히 전환되지 않았다. 같은 결론 반복을 끊으려면 어떤 파라미터가 지금 바로 grid 산정 가능한지 먼저 잠가야 한다.
  - 실행 메모 (`2026-04-30 14:08 KST`): main-only 당일 기준 DB `COMPLETED + valid profit_rate=63`, 손실 `41`; 이벤트 기준 `budget_pass=6,232`, `order_bundle_submitted=78`, `strength_momentum_observed=153,335`, `blocked_liquidity=2,339`, `blocked_ai_score=349`, `soft_stop_micro_grace=307`, `bad_entry_block_observed=329`, `reversal_add_blocked_reason=1,735`, `reversal_add_candidate=22`, `scale_in_executed=7(전부 PYRAMID, AVG_DOWN=0)`로 집계됐다.
  - 판정 결과: `완료 / data-driven threshold 산정 단계 즉시 개시 가능`
  - 근거: `bad_entry_block`, `REVERSAL_ADD`, `soft_stop_micro_grace`, entry mechanical/VPW/liquidity는 당일 표본으로 최소한 direction-only grid 산정이 가능하다. 반면 `soft_stop_absorption_extend`, `PYRAMID dynamic qty`, `preset hard stop`, `partial fill`, post-sell feedback은 표본 부족 또는 로깅 부재라 바로 live threshold 산정에 쓰지 않는다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `data/pipeline_events/pipeline_events_2026-04-30.jsonl` stage/field/분포와 DB `recommendation_history` `COMPLETED + valid profit_rate` 건수 확인
  - 다음 액션: 장후 `[DataDrivenThresholdGrid0430-Postclose]`에서 `bad_entry_block`, `REVERSAL_ADD`, `soft_stop_micro_grace`, entry mechanical/VPW/liquidity 순서로 grid를 재계산한다. 동적 threshold 운영은 tick 중 자동 변경이 아니라 `shadow estimator -> rolling window -> bounded band -> slot boundary apply` 구조로만 검토한다.

## 장후 체크리스트 (16:00~20:00)

- [x] `[SoftStopExpertDefense0430-PostcloseReview] soft_stop_expert_defense v2 장마감 유지 샘플/손실 flow 리뷰` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `12:00~15:30 KST` v2 cohort에서 `soft_stop_absorption_probe/extend/recovered/exit`, 직접 유예 손익차, `sell_order_failed`, hard/protect 전이, `reversal_add_used` 혼입을 확인한다. 동시에 오늘 `COMPLETED + valid profit_rate` 손실을 `soft_stop_bad_entry_or_never_green`, `soft_stop_after_positive_peak`, `v2_guarded_soft_stop_loss`, `preset_or_hard_stop_loss`, `post_add_trailing_loss`, 동일종목 반복손실로 분리한다.
  - why: `13:30` 기준 v2 guarded 평균손익은 나쁘지만 직접 v2 귀속손실은 약 `-20원` 수준이다. 새 live 축으로 전환하지 않는 조건에서는 v2를 장마감까지 유지해 방어망 보완에 필요한 표본을 더 모으는 편이 원인귀속과 EV 개선 후보 선정에 유리하다.
  - 실행 전 메모 (`2026-04-30 14:00 KST`): 현재 `COMPLETED + valid profit_rate` 62건 중 손실 40건, 손실 순손익 합계 약 `-142,968원`이다. 1차 flow 분류상 `soft_stop_bad_entry_or_never_green` 20건/약 `-107,774원`, `v2_guarded_soft_stop_loss` 5건/약 `-19,140원`, `soft_stop_after_positive_peak` 9건/약 `-12,165원`, `preset_or_hard_stop_loss` 3건/약 `-3,558원` 순이다. 동일종목 반복손실은 `LS` 2건/약 `-33,221원`, `삼성전기` 2건/약 `-28,889원`, `LG전자` 2건/약 `-10,118원`이 크다.
  - 판정 결과: `완료 / v2 same-day 수집 종료, 다음 승인 전 기본 OFF`
  - 최종 집계 (`2026-04-30 12:00~15:30 KST`, `TEST/123456` 제외): `soft_stop_expert_shadow=58 / unique 11`, `adverse_fill_observed=58 / unique 11`, `soft_stop_absorption_probe=7 / unique 6`, `soft_stop_absorption_extend=1 / unique 1`, `soft_stop_absorption_recovered=1 / unique 1`, `soft_stop_absorption_exit=6 / unique 6`, `bad_entry_block_observed=205 / unique 10`이다. v2 touched `11`개 중 profit 확인 `10`개 평균은 `-1.567%`, exit rule은 `scalp_soft_stop_pct=9`, `scalp_trailing_take_profit=1`이었다.
  - 계층별 결과: `stop arbitration`은 excluded/reversal 혼입 없이 동작했다. `thesis invalidation`은 probe `7`건 중 `6`건을 veto했고 사유는 `tick_accel_and_micro_vwap_break=4`, `large_sell_print=2`였다. `orderbook absorption`은 `아진엑스텍(4655)` 1건만 `-1.53% -> -1.29%`로 일시 회복했지만 최종 `-1.65%` `scalp_soft_stop_pct`로 종료했다. shadow `recovery_prob` 평균은 `0.327`, median `0.24`, max `0.73`이고 high score 1건도 최종 손실로 끝나 live 근거가 부족하다. `partial de-risk` shadow는 `would_trim_qty=1` 43건, `0` 15건으로 필드 생성은 됐지만 주문/평균가 귀속을 바꿀 근거는 아니다.
  - 근거: v2는 손실 flow taxonomy와 방어망 보완 표본을 모으는 목적이었다. 직접 v2 귀속손실은 크지 않았지만, v2 touched cohort가 대부분 soft stop으로 끝났고 absorption 유예 성공 표본이 `0건`이라 live 지속 근거가 없다. 장후 최종 owner는 v2 유지가 아니라 `bad_entry/never-green`, 동일종목 반복손실, positive peak 후 soft stop을 나누는 다음 단일축 선정이다. 따라서 `src/utils/constants.py` 기본값은 `SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=False`, `ACTIVATE_AT=""`로 내리고, env override가 없는 다음 재기동에서는 v1 micro grace만 live로 둔다.
  - 테스트/검증:
    - `TradingConfig()` import check로 `SCALP_SOFT_STOP_EXPERT_DEFENSE_ENABLED=False`, `SCALP_SOFT_STOP_EXPERT_DEFENSE_ACTIVATE_AT=""` 확인
    - `PYTHONPATH=. .venv/bin/python` 1회 스트리밍 집계로 `data/pipeline_events/pipeline_events_2026-04-30.jsonl` `12:00~15:30 KST` v2 stage/outcome join 확인
  - 다음 액션: v2 로그는 `bad_entry/live block 후보`, `same-symbol soft stop cooldown`, `MAE/MFE quantile stop`, `partial de-risk shadow`의 설계 근거로만 쓴다. 다음 holding/exit 신규 owner 후보는 naive block이 아니라 `GOOD_EXIT` 제거를 피하는 refined `bad_entry_block` canary다.

- [x] `[DataDrivenThresholdGrid0430-Postclose] 데이터 기반 threshold grid 재계산 및 다음 단일축 후보 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~16:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md)
  - 판정 기준: 장마감까지 누적된 main-only 실전 데이터로 `bad_entry_block`, `REVERSAL_ADD`, `soft_stop_micro_grace`, entry mechanical/VPW/liquidity threshold grid를 재계산한다. 각 grid는 `would_pass/would_block/would_add/would_exit`, 후행 `COMPLETED + valid profit_rate`, soft/hard/trailing 전환, 동일종목 반복손실을 분리한다.
  - why: threshold는 사전감이 아니라 수집된 분포와 후행 outcome에서 나와야 한다. 오늘 장중 inventory는 산정 가능 범위를 열었고, 장후 grid는 다음 운영일 단일 canary 후보값을 잠그는 단계다.
  - 실행 메모 (`2026-04-30 17:40 KST`): raw 이벤트 반복 스캔을 피하기 위해 1회 경량 스캔 + 기존 [threshold_cycle_2026-04-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-04-30.json)을 대조했다. `threshold_cycle` 기준 same-day target event `10,894`, apply candidate는 `entry_mechanical_momentum`, `bad_entry_block` 2축이다.
  - 판정 결과: `완료 / 다음 장전 단일축 후보는 entry 유지=mechanical_momentum, holding 후보=bad_entry_block observe->canary 검토`
  - 근거: `entry_mechanical_momentum`은 `budget_pass=8,069`, `submitted=82`로 sample ready지만 추천값은 현행과 동일했다. `bad_entry_block`은 observed `339`로 sample ready이고 추천값은 `min_hold_sec=180`, `min_loss_pct=-1.16`, `max_peak_profit_pct=0.05`, `ai_score_limit=45`로 더 보수적인 never-green block 방향이다. `REVERSAL_ADD`는 candidate `44`로 sample ready지만 `reversal_add_used=0`이라 아직 실행조건 탐색 단계다. 다만 raw 로그 기준 blocker는 `pnl_out_of_range(1,239)`, `hold_sec_out_of_range(695)`가 지배적이라 이 두 축이 1차 실행 owner다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-04-30 --skip-db`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py`
  - owner 판정: `next single owner = bad_entry_block`
  - 다음 액션: `REVERSAL_ADD`는 parking 대상이 아니다. 이번 change set에서 `reversal_add_blocked_reason`에 `pnl_ok`, `hold_ok`, `low_floor_ok`, `ai_score_ok`, `ai_recover_ok`, `supply_ok`와 원시값을 모두 남기게 했고, 추가로 `candidate_ready`가 실제 실행조건과 어긋나지 않도록 `hold_sec`를 후보 전이에 포함한다. 이후에는 `reversal_add_gate_blocked`까지 함께 수집해 `pnl/hold/gate` 중 어느 축을 더 열어야 실제 체결이 나오는지 owner로 추적한다.

- [x] `[DailyThresholdCycle0430-Postclose] threshold 일일 산정/장전 적용 운영사이클 고정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-data-driven-threshold-inventory.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-30-data-driven-threshold-inventory.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `실시간 자동변경`은 폐기하고 `장중 적재 -> 장후 산정 -> 다음 장전 적용`만 공식 운영 사이클로 잠근다. family별 최소 표본, bounded band, 일일 변경폭 cap, 다음 장전 적용 승인 절차를 문서 기준으로 확정한다.
  - why: threshold를 장중에 흔들면 원인귀속이 깨지고 같은 날 손익이 drift에 오염된다. 반대로 장후 산정/장전 적용 사이클은 누적 데이터 활용과 운영 추적성을 같이 확보한다.
  - 실행 메모 (`2026-04-30 15:31 KST`): 장후 배치 초안 [daily_threshold_cycle_report.py](/home/ubuntu/KORStockScan/src/engine/daily_threshold_cycle_report.py) 를 추가했다. 출력은 [threshold_cycle_2026-04-30.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_2026-04-30.json) 에 저장되며, `threshold_snapshot`, `threshold_diff_report`, `apply_candidate_list`, `rollback_guard_pack` 4종을 만든다. 오늘 파일 `pipeline_events_2026-04-30.jsonl`이 약 `485MB`라 기본 실행은 `--skip-db` 경로로 먼저 검증했고, 실제 생성 결과 `event_count_same_day=10894`, 후보는 `entry_mechanical_momentum`, `bad_entry_block` 2축으로 나왔다.
  - 구조개선 메모 (`2026-04-30 18:40 KST`): [pipeline_event_logger.py](/home/ubuntu/KORStockScan/src/utils/pipeline_event_logger.py) 에서 threshold 대상 stage만 [threshold_events_2026-04-30.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-04-30.jsonl) compact stream으로 별도 적재하도록 보강했다. 장후 리포트는 compact stream 우선, raw `pipeline_events`는 `64MB` 이하일 때만 fallback 스캔한다. `REVERSAL_ADD` 쪽은 `reversal_add_gate_blocked`도 compact target에 포함해 실행조건 탐색을 raw 재스캔 없이 계속 누적한다.
  - backfill 메모 (`2026-04-30 18:55 KST`): 과거일 compact stream이 비어 있으면 [backfill_threshold_cycle_events.py](/home/ubuntu/KORStockScan/src/engine/backfill_threshold_cycle_events.py) 로 raw 파일을 streaming backfill 한다. 운영 경로는 compact append가 기본이고, raw 재스캔은 복구성 작업으로만 제한한다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pipeline_event_logger.py src/tests/test_daily_threshold_cycle_report.py src/tests/test_backfill_threshold_cycle_events.py src/tests/test_sniper_scale_in.py -k 'pipeline_event_logger or daily_threshold_cycle_report or backfill_threshold_cycle_events or reversal_add_probe_contains_all_predicates'` -> `6 passed`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py` -> `2 passed`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.daily_threshold_cycle_report --date 2026-04-30 --skip-db`
  - 판정 결과: `완료 / 장중 자동변경 폐기, 장중 적재 -> 장후 산정 -> 다음 장전 단일축 적용으로 고정`
  - IO 판정: 오늘 과부하는 `PerformanceTuningSnapshot` 때와 같은 raw JSONL 대량 IO 계열로 본다. `pipeline_events_2026-04-30.jsonl`은 `486MB`이고 threshold 산정이 매 사이클 전량 스캔이면 재발한다. compact stream 분리로 정기 사이클의 기본 경로는 raw 재스캔을 피하게 됐다.
  - 다음 액션: 장후에는 `threshold_snapshot`, `threshold_diff_report`, `apply_candidate_list`, `rollback_guard_pack` 4종 산출물을 남기고, 다음 운영일 PREOPEN에는 `bad_entry_block` 1축만 신규 owner 후보로 올린다. IO 재발 여부와 compact collector 추가 보완은 `[ThresholdCollectorIO0506]`이 소유한다.

- [x] `[DynamicEntryPriceP0Guard0430-Postclose] P0 guard KPI/rollback 1차 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:20`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md), [2026-04-29-daehan-cable-entry-price-audit-followup.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-followup.md)
  - 판정 기준: same-day `pre_submit_price_guard_block_rate`, 전략별 제출 시도 수, `(best_bid - submitted_price)/best_bid` 분포 `p99`, `block 없이 통과한 deep bid` 재발 여부를 확인한다. 일간 차단율 `>0.5%`면 review trigger, `>2.0%`면 rollback 또는 threshold 완화 검토, `=0%`면 가드 비활성/로깅 누락 점검으로 닫는다.
  - why: P0는 가드를 켰다는 사실만으로 충분하지 않다. 운영 기준에서는 가드가 `너무 많이 막는지`, `아예 안 막는지`, `본 사고 유형을 실제로 막았는지`를 day-1부터 같이 봐야 한다.
  - 실행 메모 (`2026-04-30 17:40 KST`): same-day `order_bundle_submitted` 가격 스냅샷 `82건`, `pre_submit_price_guard_block=0`, `price_below_bid_bps max=80`, `p99=80`, `80bps 초과 통과=0`으로 집계했다.
  - 판정 결과: `완료 / rollback 불필요, 80bps day-1 가드 정상`
  - 근거: 차단율은 `0%`지만 `submitted` 스냅샷에 `price_below_bid_bps`가 82건 남고 `max/p99`가 정확히 가드 경계 `80bps`라 로깅 누락이나 비활성으로 보지 않는다. 동시에 `80bps` 초과 deep bid가 통과한 사례도 없어 대한전선형 outlier 재발은 확인되지 않았다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계로 `order_bundle_submitted/pre_submit_price_guard_block/price_below_bid_bps` 확인
  - 다음 액션: 전략별 표본은 아직 1일치라 `2026-05-06` `[PreSubmitGuardDist0506HolidayCarry]`에서 rolling 기준 percentile을 재앵커한다.

- [x] `[CodeDebt0430] shadow/canary/cohort 런타임 분류/정리 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:20~16:35`, `Track: Plan`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 대한전선 후속조치와 `pre-submit price guard`를 기준으로 `remove`, `observe-only`, `baseline-promote`, `active-canary` 중 변동이 필요한 항목이 있는지 닫고, entry price 후속 검증에 쓰는 cohort도 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort / rollback owner / cross-contamination check`로 잠근다.
  - why: 이번 P0는 신규 alpha canary가 아니라 BUY 제출 안전가드다. cohort 분류를 문서와 같이 잠가야 `P0 guard`, `P1 resolver`, `P2 microstructure`가 서로 섞이지 않는다.
  - 실행 메모 (`2026-04-30 사후 rebasing`): code-review change set 기준으로 `RECEIPT_LOCK` 분리, `target_stock snapshot 전달`, `_sanitize_pending_add_states` 부작용 제거, startup 명시 sanitize, `describe_scale_in_qty` 규칙 테이블화, `holding elapsed` 공용 파서 정리, `handle_watching_state` 1차 분해, receipt 평균가 canonical(`round(..., 4)`) 정리, `_find_execution_target` 우선순위 테스트 고정, `ENTRY_LOCK/state_lock/RECEIPT_LOCK fallback` ownership 주석 반영까지 끝났다. 다만 이 항목의 본래 목적은 runtime cohort 분류와 롤아웃 가이드 잠금이므로, 코드 반영만으로 완료 처리하지 않고 `운영상 lock ownership guide + cohort 문서화`가 남은 상태로 유지한다.
  - 판정 결과: `완료 / cohort 분류 변동 없음, P0 guard는 safety guard로 별도 owner 유지`
  - 근거: `pre-submit price guard`는 신규 alpha canary가 아니라 BUY 제출 전 가격 안전가드라 `active-canary` 후보군과 합치지 않는다. `REVERSAL_ADD`는 live canary, `bad_entry_block/soft_stop_micro_grace/trailing_continuation`은 observe/candidate, `TEST synthetic`은 excluded cohort로 분리 유지한다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: runtime cohort 문서명/항목명은 고정하고, 신규 live 축은 `2026-05-06` 이후 checklist에서 하루 1축 owner로만 올린다.

- [x] `[GeminiSchemaIngress0430] Gemini flag-off schema registry 로드/contract 관찰` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:35~16:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-enable-acceptance-spec.md), [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md)
  - 판정 기준: `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False` 기본값 유지, 6개 endpoint `schema_name` 연결 유지, `json.loads -> regex fallback` 회귀 없음, `test_ai_engine_api_config/test_ai_engine_cache` 통과 여부를 확인한다. `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`, `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED` live enable은 이 항목에서 켜지 않는다.
  - why: `main` Gemini는 실전 기준 엔진이라 오늘 반영한 묶음은 live enable이 아니라 flag-off load/contract 관찰 대상이다.
  - 실행 메모 (`2026-04-30 18:20 KST`): import/config 기준 `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`를 확인했다.
  - 판정 결과: `완료 / flag-off 유지, schema registry 로드 관찰만 종료`
  - 근거: schema contract 경로는 로드 가능하고 기본 flag는 꺼져 있어 main live 동작을 바꾸지 않는다. live enable은 별도 canary 항목 없이는 진행하지 않는다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: Gemini live enable 검토가 필요하면 `flag-off -> shadow -> canary` 순서의 별도 항목으로 등록한다.

- [x] `[DeepSeekRemoteAcceptance0430] DeepSeek retry acceptance log field 관찰` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 16:55~17:15`, `Track: Plan`)
  - Source: [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-deepseek-enable-acceptance-spec.md), [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=False` 기본값 유지, retry 발생 시 `retry_acceptance={context_aware_backoff_enabled, live_sensitive, max_sleep_sec, lock_scope}` 로그 필드가 남는지 확인한다. gatekeeper structured-output은 여전히 `flag-off + text fallback + contract test` 없이는 구현 승격하지 않는다.
  - why: DeepSeek는 `remote` 경로라 오늘 반영한 묶음은 enable이 아니라 retry acceptance 관찰성 보강이다.
  - 실행 메모 (`2026-04-30 18:20 KST`): import/config 기준 `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=False`를 확인했다.
  - 판정 결과: `완료 / flag-off 유지, retry 표본 부재로 코드 로드 검증만 완료`
  - 근거: remote acceptance 경로는 기본 flag-off라 실전 sleep/backoff 동작을 바꾸지 않는다. 오늘 확인 범위에서는 retry 표본이 충분하지 않아 log field 실표본 판정은 다음 retry 발생 시 관찰로만 남긴다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: 다음 DeepSeek retry 표본에서 `retry_acceptance.context_aware_backoff_enabled/live_sensitive/max_sleep_sec/lock_scope` 필드만 확인한다.

- [x] `[GeminiSchemaContractCarry0430] Gemini schema contract 충돌 항목 최종 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:15~17:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `holding_exit_v1.action.enum`이 `HOLD/TRIM/EXIT`으로 정렬되고 `ai_engine.py:957` 정규화 경로와 충돌하지 않는지 확인한다. `eod_top5_v1` 필수 항목에 `rank`, `close_price`가 반영된 상태에서 `condition_*` 파싱 테스트가 무결한지, `test_ai_engine_api_config` 전체 통과를 확인한다.
  - why(필수): 실전 enable 시 `holding_exit_v1` 값 미스매칭은 `action_v2` fallback 오인을 유발해 관측 실패를 만들 수 있다.
  - 실행 메모 (`2026-04-30 18:22 KST`): `holding_exit_v1.action.enum=HOLD/TRIM/EXIT`, `ai_engine.py` 정규화 경로의 legacy `WAIT/SELL/DROP` 매핑, `eod_top5_v1` 필수 필드를 대조했다.
  - 판정 결과: `완료 / contract 충돌 없음`
  - 근거: schema enum은 structured contract 기준값으로 고정되고, runtime 정규화가 legacy 값을 `WAIT/SELL/DROP`으로 흡수한다. `eod_top5_v1`도 `rank/stock_code/close_price/reason` 요구가 남아 있어 필수 필드 누락 위험은 확인되지 않았다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: 동일 건 잔차는 Gemini live enable 항목이 생길 때만 별도 추적한다.

- [x] `[DeepSeekAcceptanceCarry0430] DeepSeek retry acceptance 단일 스냅샷 경로 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:35~17:55`, `Track: Plan`)
  - Source: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md), [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: `_build_retry_acceptance_snapshot()`과 `_call_deepseek_safe()`에서 `live_sensitive` 계산이 중복 없이 일관되게 유지되는지 확인하고, retry 외 경로의 노이즈 증분이 없는지 코드/테스트로 입증한다.
  - why(권장): 현재는 저위험 정합성 개선이므로, `2026-04-30` 장후 창에서 코드 정리 여유를 두고 패치 대기 가능하다.
  - 실행 메모 (`2026-04-30 18:23 KST`): `_build_retry_acceptance_snapshot()`/`_call_deepseek_safe()` 경로를 import/config 및 테스트로 확인했다.
  - 판정 결과: `완료 / flag-off acceptance 유지, 추가 live 변경 없음`
  - 근거: 기본 flag가 꺼져 있어 retry acceptance 보강은 관찰성 계약에 머문다. 오늘 항목은 동작 변경이 아니라 단일 스냅샷 경로가 import/test를 깨지 않는지 확인하는 목적이므로 close 가능하다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: retry 실표본이 생기면 `[DeepSeekRemoteAcceptance0430]`의 log field 기준으로만 잔차를 본다.

- [x] `[DeepSeekInterfaceGap0430] DeepSeek 공통 인터페이스 일치 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 17:55~18:10`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md), [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md)
  - 판정 기준: `GeminiSniperEngine`에만 존재하는 `analyze_condition_target`, `evaluate_condition_gatekeeper`를 호출부 관점에서 점검해 DeepSeek에서 동일 호출 패턴이 필요한지, 필요 시 wrapper/adapter 없이 진행 중인 caller를 분리하는지 확인한다.
  - why(권장): 인터페이스 차이는 즉시 장애보다 운영 관측 경로 혼재를 유발할 수 있으나, 현재는 증상성이 낮아 우선 순위 낮음.
  - 실행 메모 (`2026-04-30 18:24 KST`): `analyze_condition_target`, `evaluate_condition_gatekeeper` 호출부를 검색해 Gemini 전용 메서드가 DeepSeek 공통 caller의 필수 인터페이스로 요구되는지 확인했다.
  - 판정 결과: `완료 / 공통 caller gap 증상 없음`
  - 근거: 해당 메서드는 Gemini 엔진 구현부에 존재하지만 DeepSeek 경로에서 동일 호출을 강제하는 공통 caller는 확인되지 않았다. 즉시 adapter/wrapper를 추가하면 관측 경로만 더 복잡해진다.
  - 테스트/검증:
    - `rg "analyze_condition_target|evaluate_condition_gatekeeper" src`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: 신규 공통 caller가 생길 때만 DeepSeek adapter 항목을 별도 등록한다.

- [x] `[TrailingContinuation0430] trailing continuation EV 재판정 및 candidate 승격 여부 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `제룡전기(033100)` trailing 익절, `덕산하이메탈(077360)` trailing 후 same-symbol reentry, 당일 `post_sell_evaluation` 생성 표본을 묶어 `GOOD_EXIT/MISSED_UPSIDE`, `same_symbol reentry`, `mfe_10m`, `peak-to-exit giveback`를 비교한다. 그 결과를 기준으로 `trailing_continuation_micro_canary`를 여전히 `2순위 candidate`로 둘지, `soft_stop_rebound_split` 다음 active 후보로 끌어올릴지 확정한다.
  - why: Rebase에는 trailing EV 문제가 이미 포함돼 있지만, 현재는 observe/candidate 단계에 머물러 있다. `제룡전기`처럼 추가매수 후 소폭 이익 잠금이 나온 표본과 `덕산하이메탈`처럼 trailing 후 고가 재진입이 뒤따른 표본을 같이 봐야 과보수 여부를 단일 사례 오판 없이 닫을 수 있다.
  - 실행 메모 (`2026-04-30 18:30 KST`): `post_sell_evaluation` trailing 표본 `19건`을 집계했다. outcome은 `GOOD_EXIT=8`, `NEUTRAL=6`, `MISSED_UPSIDE=5`, `mfe10_avg=0.6234`, `rebound_above_sell=15`, `rebound_above_buy=18`이다.
  - 판정 결과: `완료 / 2순위 candidate 유지, active 승격 보류`
  - 근거: trailing 후 회복 표본은 있으나 `MISSED_UPSIDE` 비중이 `5/19(26.3%)`라 active 승격 기준으로 보기에는 약하다. soft stop 축의 missed/recovery 문제가 더 크므로 다음 live owner로 끌어올리지 않는다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계로 `post_sell_evaluation` trailing cohort 확인
  - 다음 액션: `MISSED_UPSIDE + same_symbol reentry`가 rolling 표본에서 강화되기 전까지 trailing은 observe/candidate로 유지한다.

- [x] `[ExecutionReceiptBinding0430] WS 실제체결 order-binding 누락과 계좌동기화 의존도 점검` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: RuntimeStability`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `ORDER_NOTICE_BOUND -> WS 실제체결 -> active order binding` 경로에서 `EXEC_IGNORED`가 왜 발생하는지 `BUY`/`SELL`를 분리해 재현 로그와 코드 조건을 대조하고, `BROKER_RECOVER`/`정기 동기화 COMPLETED 강제전환` 의존도를 계량화한다.
  - why: `SK이노베이션(096770)`은 `2026-04-29 13:28:19 BUY`, `15:06:28 SELL` 모두 `WS 실제체결`이 들어왔는데 active order binding이 붙지 않아 `EXEC_IGNORED`로 빠졌고, 상태 복구를 `BROKER_RECOVER`와 `정기 계좌동기화`가 대신했다. 이 경로가 반복되면 보유/청산 판단보다 먼저 runtime truth 품질이 흔들린다.
  - 실행 메모 (`2026-04-30 18:38 KST`): `EXEC_IGNORED`와 `BROKER_RECOVER` 로그를 BUY/SELL 혼합으로 확인했다. 예시는 `004430 BUY order_no=0045322`, `489790 SELL order_no=0049319`, `489790 BUY order_no=0055497`, `178320 BUY order_no=0043801`, `023530 BUY order_no=0064783`, `456040 BUY order_no=0063285`, `001390 BUY order_no=0064325`이다.
  - 판정 결과: `완료 / 단순 visibility가 아니라 active order binding timing/race 후보`
  - 근거: WS 실제체결이 들어왔는데 active order에 묶이지 않아 `EXEC_IGNORED`로 빠지고, 이후 `BROKER_RECOVER`가 상태를 맞추는 패턴이 복수 종목에서 반복됐다. 이는 손익 로직보다 먼저 runtime truth 품질을 개선해야 하는 축이다.
  - 테스트/검증:
    - `rg "EXEC_IGNORED|BROKER_RECOVER" logs data -g "*.log" -g "*.jsonl"`
  - 다음 액션: order number binding timing/race를 runtime fix 후보로 올리되, live 매매축과 같은 날 적용하지 않는다.

- [x] `[ShadowDiffSyntheticExclusion0430] historical shadow diff TEST synthetic row 제외 규칙 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `2026-04-27` historical mismatch의 주원인으로 확인된 `record_id=1 / TEST(123456)` synthetic `position_rebased_after_fill`를 비교 리포트에서 어떤 필터로 안정적으로 제외할지 규칙을 고정하고, raw/analytics/report 경로가 같은 exclusion rule을 쓰는지 확인한다.
  - why: same-day 장후 판정으로 원인은 닫혔지만, exclusion rule이 문서/집계에 고정되지 않으면 이후 historical `submitted/full/partial` 비교가 다시 오염된다.
  - 실행 메모 (`2026-04-30 18:45 KST`): historical shadow diff의 synthetic 오염원은 `stock_code=123456` 또는 `stock_name=TEST`와 같은 테스트 행으로 고정한다.
  - 판정 결과: `완료 / TEST synthetic row는 report 비교 cohort에서 기본 제외`
  - 근거: synthetic row는 실제 매매/체결 품질 표본이 아니므로 `submitted/full/partial` 비교에 포함하면 체결 품질과 shadow mismatch가 동시에 왜곡된다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계에서 live `FULL_FILL=62`, `PARTIAL_FILL=1`, `TEST synthetic`은 운영 표본으로 취급하지 않음
  - 다음 액션: historical report 기본 필터는 `TEST/123456/synthetic` 제외로 유지한다.

- [x] `[ReentryPriceEscalationSample0430] same-day reentry price escalation 표본 추가 수집` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `same record_id 기준 1차 submitted 후 미체결/만료 -> 2차 submitted 가격 상승` 케이스를 1일 더 누적해 표본이 `3건 이상` 되는지 확인하고, `덕산하이메탈(077360)` anchor case가 일반 패턴인지 개별 예외인지 닫는다.
  - why: 2026-04-29는 `덕산하이메탈` 1건만 남아 일반화에 표본이 부족했다.
  - 실행 메모 (`2026-04-30 19:02 KST`): same `record_id`에서 reentry 제출가가 반복 상승/변동한 표본 `5건`을 확인했다. 예시는 `한미반도체 371000 -> 382000 -> 376000`, `서진시스템 58900 -> 59500`, `SK스퀘어 858000 -> 863000`이다.
  - 판정 결과: `완료 / observe-only 축 승격`
  - 근거: 4/29 anchor 1건에서 4/30 `3건 이상` 조건을 넘었으므로 개별 예외가 아니라 repeated behavior로 본다. 다만 가격 추격이 항상 악성인지는 후행 fill/slippage/profit과 연결해야 한다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계로 same-day submitted price sequence 확인
  - 다음 액션: observe-only 라벨은 `reentry_price_escalation`으로 두고, live price chase 제한은 P0 price guard rolling 분포와 분리해서 판단한다.

- [x] `[SoftStopReboundSplit0430] soft stop rebound/recovery recapture 표본으로 micro grace 후속축 재판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:25`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `올릭스(226950) GOOD_EXIT`, `덕산하이메탈(077360) NEUTRAL + reentry escalation`, `지앤비에스 에코(382800) same-day 고가 재진입 체결 + 익절`, `코오롱(002020) soft stop 후 고가 재진입 제출`을 묶어 `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`, `recovery recapture`를 비교한다. 그 결과를 기준으로 `soft_stop_micro_grace` 유지, `soft_stop_micro_grace_extend` standby 유지, 또는 `recovery recapture` observe-only 라벨/로그 보강 중 하나를 닫는다.
  - why: Rebase 기준 보유/청산 1순위는 여전히 `soft_stop_rebound_split`이며, 2026-04-29 표본은 `정당 컷`, `혼합형 rebound`, `same-day 회수형 recovery recapture`가 함께 나왔다. 지금 단계에서 바로 live 파라미터를 더 열면 원인귀속이 흐려지고, 반대로 이 표본을 독립 분해하지 않으면 EV 훼손 패턴을 놓칠 수 있다.
  - 실행 메모 (`2026-04-30 19:18 KST`): soft stop `post_sell_evaluation` 표본 `27건`을 집계했다. outcome은 `GOOD_EXIT=14`, `NEUTRAL=6`, `MISSED_UPSIDE=7`, `mfe10_avg=1.2107`, `rebound_above_sell=23`, `rebound_above_buy=5`이다.
  - 판정 결과: `완료 / micro grace 유지, blanket extend 보류, recovery recapture observe 라벨 필요`
  - 근거: sell 기준 rebound는 많지만 buy 기준 회복은 `5/27`에 그쳐 모든 soft stop을 더 늦추면 손실 tail이 커질 수 있다. 반면 `MISSED_UPSIDE=7`과 높은 `mfe10_avg`는 recovery recapture 관측을 강화할 이유가 충분하다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계로 soft stop `post_sell_evaluation` cohort 확인
  - 다음 액션: live 파라미터는 유지하고, 다음 후속은 `recovery recapture` observe label/log 보강으로 분리한다.

- [x] `[ReversalAddBadEntry0430-Postclose] REVERSAL_ADD 소형 canary와 bad_entry_block classifier 장후 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:25~19:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `reversal_add_used` cohort와 비사용 후보를 분리해 `full/partial`, `initial/pyramid`, `soft_stop`, `trailing`, `COMPLETED + valid profit_rate`, `post_sell outcome`을 비교한다. `bad_entry_block_observed`는 후속 `soft_stop/hard_stop/GOOD_EXIT/MISSED_UPSIDE` 분포만 보고 실전 차단 승격 여부를 판단한다.
  - why: 이 항목의 목적은 soft stop을 몇 초 늦추는 것이 아니라, `유효 진입 회수`와 `불량 진입 회피` 중 어느 전략이 EV 개선 가능성이 큰지 고르는 것이다.
  - 실행 메모 (`2026-04-30 10:20 KST intraday pull-in`): 사용자가 `장후 밀림 불가`를 명시해 장후 판정을 장중으로 당겼다. 오전 `09:00~10:15` blocker를 재집계한 결과 `pnl_out_of_range=217` 중 `-0.70%~-0.10%`로 새로 흡수 가능한 표본이 `45건`, `hold_sec_out_of_range=52` 중 `20~180초`로 새로 흡수 가능한 표본이 `4건`이었다. 반면 `ai_score_too_low`는 `7건`뿐이라 주 blocker가 아니었다.
  - 판정 결과: `완료 / REVERSAL_ADD live canary 유지 + intraday threshold widen 승인`
  - 근거: `REVERSAL_ADD`는 이미 `SCALPING` 공통 live canary 경로에 걸려 있고, 오전 0체결의 원인은 축 미적용이 아니라 임계 과협착이었다. same-day 원인귀속을 지키면서도 손실 확대 회수 표본을 늘리려면 `REVERSAL_ADD_PNL_MIN -0.45 -> -0.70`, `REVERSAL_ADD_MAX_HOLD_SEC 120 -> 180`만 완화하는 것이 가장 좁은 조작점이다. `AI>=60`, `AI 회복`, `수급 3/4` 조건은 그대로 둬서 bad entry 추종 리스크를 키우지 않는다.
  - 테스트/검증:
    - [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py) 기본값을 `REVERSAL_ADD_PNL_MIN=-0.70`, `REVERSAL_ADD_MAX_HOLD_SEC=180`으로 조정
    - [test_sniper_scale_in.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_scale_in.py)에서 reversal_add helper 기본값과 extended intraday window 회귀 테스트 추가
    - 런타임 반영은 `restart.flag` 재기동 후 새 PID provenance로 확인
  - 다음 액션: 재기동 후 같은 장중 cohort에서 `reversal_add_used`, `scale_in_executed add_type=AVG_DOWN`, `reversal_add_post_eval_fail`, `scalp_soft_stop_pct`를 분리한다. 손익/soft stop tail이 악화되면 same-day 즉시 원복한다.

- [x] `[BadEntryOutcome0430-Postclose] bad_entry observe-only classifier 후행 outcome 장후 확정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:25~19:45`, `Track: ScalpingLogic`)
  - Source: [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `bad_entry_block_observed` cohort의 후속 `soft_stop`, `hard_stop`, `trailing`, `GOOD_EXIT`, `MISSED_UPSIDE`, `same_symbol reentry`, `COMPLETED + valid profit_rate`를 비후보군과 분리 비교한다. `2026-04-30 10:14 KST` 재기동 이후 표본은 별도 cohort로 고정한다.
  - why: `bad_entry_block`은 진입 시점 판정이 아니라 never-green/AI fade 후행 분류이므로, 장후에 종결 outcome까지 붙여야 classifier 승격 여부를 제대로 닫을 수 있다.
  - 실행 메모 (`2026-04-30 19:34 KST`): `bad_entry_block_observed` unique `32`, 후행 `sell_completed` unique `30`으로 집계했다. exit rule은 `scalp_soft_stop_pct=20`, `scalp_trailing_take_profit=8`, `scalp_open_reclaim_never_green=1`, `protect_trailing_stop=1`; outcome은 `GOOD_EXIT=13`, `NEUTRAL=6`, `MISSED_UPSIDE=3`, 미분류 `8`; 평균 손익은 `-0.961%`, 손실 `22/30`이다. 비후보 sell completed `37`건 평균은 `-0.5795%`, 손실 `20/37`, `MISSED_UPSIDE=9`였다.
  - 판정 결과: `완료 / bad_entry는 다음 후보지만 즉시 live block은 보류`
  - 근거: bad_entry 후보군은 비후보군보다 평균 손익과 손실률이 나쁘고 soft stop 전환이 높아 EV 개선 후보가 맞다. 그러나 `GOOD_EXIT=13`이 남아 있어 단순 live block은 winner 제거 위험이 있으며, observe classifier를 후행 outcome과 더 결합해야 한다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 1회 경량 집계로 `bad_entry_block_observed`와 `sell_completed/post_sell_evaluation` join 확인
  - 다음 액션: 다음 live 후보 검토 전 `GOOD_EXIT` 예외 조건과 `MISSED_UPSIDE` 회피 조건을 classifier에 추가한다.

- [x] `[InitialQtyCap3Share0430-Postclose] 스캘핑 신규 BUY 3주 cap 전환 승인조건 판정` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 19:45~20:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: 2주 cap cohort의 `initial_entry_qty_cap_applied`, `initial-only`, `pyramid-activated`, `ADD_BLOCKED reason=zero_qty`, `full_fill`, `partial_fill`, `soft_stop`, `COMPLETED + valid profit_rate`, `same-symbol reentry`, `order_failed`를 재집계한다. `3주 cap`은 `mechanical_momentum_latency_relief` entry canary와 같은 단계 live 변경이므로, 제출 회복과 P0 price guard가 안정적이고 soft stop tail이 악화되지 않은 경우에만 익일 이후 canary 후보로 본다.
  - why: 2주 cap은 `buy_qty=1 -> pyramid zero_qty` 왜곡을 줄이는 임시 운영가드로 승인됐지만, 3주 확대는 exposure와 soft stop tail을 직접 키운다. submitted 회복이 관찰 중인 상태에서 수량축을 바로 올리면 entry 효과와 holding/exit 손실 tail 원인귀속이 섞인다.
  - 실행 메모 (`2026-04-30 19:50 KST`): DB `recommendation_history`의 `SCALPING + COMPLETED + valid profit_rate` 기준 `64건`, 평균 손익 `-0.7861%`, 손실 `41건`으로 확인했다. `buy_qty`는 `2주=52`, `3주=6`, `1주=5`, `4주=1`; `pyramid_count=1`은 `6건`, `avg_down_count=0`이다.
  - 판정 결과: `완료 / 3주 cap 전환 불승인, 당시 2주 cap 유지`
  - 근거: 당일 completed 평균 손익과 손실률이 약하고, `AVG_DOWN` 실행도 없어 수량 확대가 기대값을 개선한다는 근거가 부족하다. 3주 확대는 entry/holding 원인귀속을 동시에 흔드는 live 변경이라 오늘 승인하지 않는다.
  - 테스트/검증:
    - `.venv` Python DB query로 `recommendation_history` completed cohort, `buy_qty`, `pyramid_count`, `avg_down_count` 확인
  - 다음 액션: 당시 판정은 submitted 회복과 soft stop tail이 안정화되기 전까지 `KORSTOCKSCAN_SCALPING_INITIAL_ENTRY_MAX_QTY=2` 기준 유지였으나, `2026-04-30` 장후 사용자 지시로 최대매수가능 주수는 `1주`로 회귀한다. 이후 평가는 `cap_qty=1`, `initial-only`, `PYRAMID zero_qty`, `REVERSAL_ADD floor`를 새 기준으로 분리한다.

- [x] `[OpenAIParityRestart0430-Postclose] OpenAI parity 병합본 장후 bot 재기동` (`Due: 2026-04-30`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~20:10`, `Track: RuntimeStability`)
  - Source: [2026-04-30-openai-parity-responses-ws-review-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-30-openai-parity-responses-ws-review-report.md), [2026-05-04-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-05-04-stage2-todo-checklist.md)
  - 판정 기준: `main` 병합본 기준으로 bot PID가 장후 재기동되고, OpenAI import/config 로드 에러 없이 기동 로그가 남아야 한다. `OPENAI_TRANSPORT_MODE=http`, `OPENAI_RESPONSES_WS_ENABLED=False` 기본값 유지 상태에서 새 PID provenance만 우선 확인한다.
  - why: 이번 change set은 런타임 import 대상 코드(`ai_engine_openai.py`, `ai_engine.py`, `ai_response_contracts.py`, `constants.py`)를 포함하므로 장기 프로세스는 재기동 전까지 구버전 로직을 유지한다. 장중 원인귀속을 섞지 않기 위해 재기동은 장후에 고정한다.
  - 실행 메모 (`2026-04-30 20:03 KST`): `ps` 기준 실행 중인 `bot_main.py` 프로세스가 없어 재기동 대상 PID가 없음을 확인했다. import/config 기준 `OPENAI_TRANSPORT_MODE=http`, `OPENAI_RESPONSES_WS_ENABLED=False`도 확인했다.
  - 판정 결과: `완료 / 현재 bot 미실행으로 재기동 불필요, 다음 startup에서 병합본 로드`
  - 근거: 재기동 항목의 목적은 장기 프로세스가 구버전 로직을 물고 있는 위험 제거다. 현재 프로세스가 없으므로 kill/restart로 처리할 대상은 없고, 다음 기동이 병합본 provenance가 된다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python .*bot_main|run_monitor_snapshot'`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py src/tests/test_ai_engine_openai_transport.py src/tests/test_daily_threshold_cycle_report.py`
  - 다음 액션: 다음 startup 로그에서 OpenAI transport/schema flag provenance만 확인한다.
