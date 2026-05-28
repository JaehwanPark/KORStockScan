# 2026-04-28 Stage 2 To-Do Checklist

## 오늘 목적

- `soft_stop_micro_grace`를 `09:00~15:00` 시간단위로 관찰하고, hard stop 전환/미체결/동일종목 재진입 손실 악화가 있으면 즉시 OFF 판정한다.
- `latency_quote_fresh_composite`를 `09:00~15:00` 시간단위로 관찰하고, `same bundle + canary_applied=False` baseline 기준 제출 회복 여부를 닫는다.
- 진입병목 예비 검증축은 `latency_signal_quality_quote_composite` 하나만 준비하고, 현 entry canary가 실패하기 전에는 live ON 하지 않는다.
- 보유/청산 추가 조정 파라미터는 `soft_stop_micro_grace_extend` 하나만 준비하고, 20초 기본축의 비악화가 확인되기 전에는 live ON 하지 않는다.
- `latency_quote_fresh_composite`와 `soft_stop_micro_grace` 장중 판정에 fresh 로그가 없으면 `offline_live_canary_bundle` 서버 export와 사용자 로컬 analyzer 산출물로 같은 시간대 판정을 닫는다.
- `latency_quote_fresh_composite`와 `soft_stop_micro_grace`는 `09:00~15:00` 시간단위로 판정하고, 표본 부족 외의 보류 결론은 금지한다.
- `orderbook_stability_observation`은 `FR_10s`, `quote_age_p50/p90`, `print_quote_alignment` 관찰지표만 기록한다. 현재 진입병목 해소 전에는 live gate/canary로 쓰지 않는다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 단계 분리: 진입병목 canary와 보유/청산 canary는 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되고 단계별 판정을 유지할 때만 `stage-disjoint concurrent canary`로 운영할 수 있다.
- 관찰창이 끝나면 `즉시 판정 -> 다음 축 즉시 착수`를 기본으로 한다. 이미 수집된 데이터로 닫을 수 있는 판정은 장후/익일로 미루지 않는다.
- `장후/익일/다음 장전` 이관은 예외사유 4종(`단일 조작점 미정`, `rollback guard 미문서화`, `restart/code-load 불가`, `운영 경계상 same-day 반영 불가`) 중 하나로만 허용한다. 막힌 조건과 다음 절대시각이 없으면 이관 판정은 무효다.
- PREOPEN은 전일에 이미 `단일 조작점 + rollback guard + 코드/테스트 + restart 절차`가 준비된 carry-over 축만 받는다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- live 승인, replacement, stage-disjoint 예외, 관찰 개시 판정에는 `cohort`를 같이 잠근다. 최소 `baseline cohort`, `candidate live cohort`, `observe-only cohort`, `excluded cohort`를 구분하고 `partial/full`, `initial/pyramid`, `fallback` 혼합 결론을 금지한다.
- `ApplyTarget`은 문서에 명시된 값만 사용하고, parser/workorder가 `remote`를 추정하지 않도록 유지한다.
- 다축 동시 변경 금지, 승인 전 `main` 실주문 변경 금지 규칙을 유지한다.
- `orderbook_stability_observed`는 observe-only 이벤트다. `unstable_quote_observed=True`여도 주문 차단, scout-only 전환, position cap 변경을 하지 않는다.

## 장중 live canary offline bundle 판정 템플릿

- fresh 로그가 Codex 작업환경에 없으면 서버에서 아래 명령으로 lightweight bundle만 생성한다.
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1000 --evidence-cutoff 10:00:00`
- 사용자는 로컬 PC에서 아래 형식으로 analyzer를 실행해 결과 JSON/MD를 전달한다.
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --output-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000\results" --since 09:00:00 --until 10:00:00 --label h1000`
- 시간대 label/window는 `h0900 09:00~10:00`, `h1000 09:00~10:00`, `h1100 10:00~11:00`, `h1200 11:00~12:00`, `h1300 12:00~13:00`, `h1400 13:00~14:00`, `h1500 14:00~15:00`로 맞춘다.
- 산출물은 `entry_quote_fresh_composite_summary_<label>.json/.md`, `soft_stop_micro_grace_summary_<label>.json/.md`, `live_canary_combined_summary_<label>.json/.md`를 기준으로 판정한다.
- 운영 원칙:
  - `09:10 KST` 전후 1차 점검은 가능하면 직접 로그/집계로 먼저 닫고, fresh 로그 접근이 막힐 때만 `h0900` bundle을 만든다.
  - `10:00 KST` 이후 시간단위 점검은 offline bundle 기본으로 보고, heavy snapshot/report builder 호출 없이 cutoff export만 사용한다.
  - `slot_label`은 `판정 시각 기준`이다. 따라서 `h1000`은 `10:00 KST`에 닫는 `09:00~10:00` 구간 bundle이다.

### 시간대별 서버 export 명령

- `09:10 KST` 필요시 1차 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h0900 --evidence-cutoff 10:00:00`
- `10:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1000 --evidence-cutoff 10:00:00`
- `11:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1100 --evidence-cutoff 11:00:00`
- `12:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1200 --evidence-cutoff 12:00:00`
- `13:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1300 --evidence-cutoff 13:00:00`
- `14:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1400 --evidence-cutoff 14:00:00`
- `15:00 KST` 점검:
  - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-28 --slot-label h1500 --evidence-cutoff 15:00:00`

### 시간대별 로컬 analyzer 명령

- `09:10 KST` 필요시 1차 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900" --output-dir "C:\KORStockScanV2\downloads\h0900\offline_live_canary_exports\2026-04-28\h0900\results" --since 09:00:00 --until 10:00:00 --label h0900`
- `10:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000" --output-dir "C:\KORStockScanV2\downloads\h1000\offline_live_canary_exports\2026-04-28\h1000\results" --since 09:00:00 --until 10:00:00 --label h1000`
- `11:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100" --output-dir "C:\KORStockScanV2\downloads\h1100\offline_live_canary_exports\2026-04-28\h1100\results" --since 10:00:00 --until 11:00:00 --label h1100`
- `12:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200" --output-dir "C:\KORStockScanV2\downloads\h1200\offline_live_canary_exports\2026-04-28\h1200\results" --since 11:00:00 --until 12:00:00 --label h1200`
- `13:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300" --output-dir "C:\KORStockScanV2\downloads\h1300\offline_live_canary_exports\2026-04-28\h1300\results" --since 12:00:00 --until 13:00:00 --label h1300`
- `14:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400" --output-dir "C:\KORStockScanV2\downloads\h1400\offline_live_canary_exports\2026-04-28\h1400\results" --since 13:00:00 --until 14:00:00 --label h1400`
- `15:00 KST` 점검:
  - `analysis\offline_live_canary_bundle\run_local_canary_bundle_analysis.bat --bundle-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500" --output-dir "C:\KORStockScanV2\downloads\h1500\offline_live_canary_exports\2026-04-28\h1500\results" --since 14:00:00 --until 15:00:00 --label h1500`

## 장전 체크리스트 (08:50~09:00)

- [x] `[SoftStopGrace0428-Preopen] soft_stop_micro_grace runtime/env/log 준비 확인` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED`, `restart.flag` 반영 여부, `soft_stop_micro_grace` 로그 필드 기록 가능 여부를 확인한다.
  - 완료근거: live flag/env, `restart.flag` 반영 여부, `soft_stop_micro_grace` 로그 필드 기록 가능 여부.
  - 다음 액션: 실패 시 09:00 관찰 시작 전 `OFF 유지` 또는 `재기동 필요` 중 하나로 닫는다.
  - 실행 메모 (`2026-04-28 07:54 KST`): 후행 확인 기준 현재 main `bot_main.py` PID는 `136356`이며 시작시각은 `2026-04-28 07:40:01 KST`다. `restart.flag` 실파일은 비어 있어 미반영 재기동 요청이 남아 있지 않다.
  - 근거: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py) 에서 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=True`, `SEC=20`, `EMERGENCY_PCT=-2.0` 기본값이 고정돼 있고, [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:3878) 는 `soft_stop_micro_grace` stage에 `profit_rate`, `soft_stop_pct`, `emergency_pct`, `elapsed_sec`, `grace_sec`, `extension_used`, `exit_rule_candidate`를 기록한다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_scale_in.py -k "soft_stop_micro_grace"` -> `3 passed`
  - 다음 액션: 재기동 없이 장중 판정은 `[SoftStopGrace0428-0900]` 이후 시간대 점검으로 이어가고, rollback guard 발동 시에만 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=False -> restart.flag` 순서로 OFF 한다.

- [x] `[QuoteFreshComposite0428-Preopen] latency_quote_fresh_composite runtime/env/log 준비 확인` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 5-parameter bundle rule, active flag, `canary_applied` cohort tag, `fallback_regression=0` 확인.
  - 완료근거: bundle rule/env, cohort tag 기록 가능 여부, fallback 회귀 없음.
  - 다음 액션: 실패 시 09:00 관찰 시작 전 `OFF 유지` 또는 `재기동 필요` 중 하나로 닫는다.
  - 실행 메모 (`2026-04-28 07:54 KST`): 후행 확인 기준 현재 main `bot_main.py` PID는 `136356`이며 시작시각은 `2026-04-28 07:40:01 KST`다. `restart.flag` 실파일은 없고 `/proc/136356/environ`에도 관련 override가 없어 코드 기본값 경로로 동작한다.
  - 근거: [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174) 에서 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True` 기본값이 고정돼 있다. [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:205) 는 `signal>=88`, `quote_stale=False`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `danger_reasons subset=quote freshness family`를 묶음으로 검사하고, 통과 시 `quote_fresh_composite_canary_applied`와 `latency_quote_fresh_composite_normal_override`를 남긴다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "quote_fresh_composite_canary"` -> `2 passed`
  - 다음 액션: 재기동 없이 장중 판정은 `[QuoteFreshComposite0428-0900]` 이후 시간대 점검으로 이어가고, `fallback_regression` 또는 `composite_no_recovery`가 확인되면 `OFF -> restart.flag -> replacement 승인` 순서로만 교체한다.

## 장중 체크리스트 (09:00~15:20)

- [x] `[SoftStopGrace0428-0900] soft_stop_micro_grace 09시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:00~09:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정: 전제 충족 + 손실 tail 감소 + hard stop/동일종목 손실 비악화면 `유지`, 전제 충족 + hard stop 전환/동일종목 손실/미체결 악화면 `OFF`, 전제 미충족이면 `보류`.
  - 다음 액션: `유지`는 다음 시간 점검 계속, `OFF`는 `SCALP_SOFT_STOP_MICRO_GRACE_ENABLED=False` 및 재기동 필요 여부 기록, `보류`는 누적 표본 부족 수치와 다음 점검시각 기록.
  - 실행 메모 (`2026-04-28 09:19 KST`): `data/pipeline_events/pipeline_events_2026-04-28.jsonl` 기준 `09:00:00~09:19:59` 구간에 `HOLDING_PIPELINE` 자체가 아직 없다. `soft_stop_micro_grace=0`, `COMPLETED + valid profit_rate=0`, `full_fill=0`, `partial_fill=0`, `same_symbol_reentry_loss_count=0`, `fallback_regression=0`.
  - 판정 결과: `보류`
  - 근거: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md:119) 및 [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md) 기준 `soft_stop_micro_grace_events >= 10` 또는 `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail 금지다. 현재는 보유/청산 표본이 0건이라 유지/OFF를 닫을 근거가 없다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `09:00:00~09:19:59` 구간 `HOLDING_PIPELINE` stage count, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `fallback_regression_count`를 확인했다.
  - 다음 액션: `[SoftStopGrace0428-1000]`에서 `h1000 (09:00:00~10:00:00)` 구간으로 재판정한다. 10시에도 `soft_stop_micro_grace=0`이면 direction-only `보류`를 유지하고 표본 부족을 누적 기록한다.

- [x] `[QuoteFreshComposite0428-0900] latency_quote_fresh_composite 09시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 성공 기준: `budget_pass_to_submitted_rate >= baseline +1.0%p`, `latency_state_danger / budget_pass` baseline 대비 `-5.0%p` 이상 개선, `submitted -> full_fill + partial_fill` 전환율 baseline 대비 `-2.0%p` 이내.
  - 판정: 전제 충족 + 성공 기준 충족은 `유지`, 전제 충족 + `composite_no_recovery`는 `OFF 또는 다음 독립축 교체`, 전제 미충족은 `direction-only 보류`.
  - 다음 액션: `유지`는 다음 시간 점검 계속, `OFF`는 5개 파라미터 묶음 전체 OFF, `교체`는 새 workorder와 rollback guard 필요, `direction-only 보류`는 표본 부족 수치와 다음 점검시각 기록.
  - 실행 메모 (`2026-04-28 09:19 KST`): `data/pipeline_events/pipeline_events_2026-04-28.jsonl` 기준 `09:00:00~09:19:59` 구간에 `ENTRY_PIPELINE`는 다수 발생했지만 `order_bundle_submitted=0`, `latency_state_danger=0`, `quote_fresh_composite_canary_applied=True/False 기록=0`, `fallback_regression=0`이다. 대신 `orderbook_stability_observed=251`이 기록돼 재기동 후 observe-only 로그는 정상 반영됐다.
  - 판정 결과: `direction-only 보류`
  - 근거: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md:113)~[121] 및 [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md) 기준 `submitted_orders >= 20`, baseline `>= N_min`, `ShadowDiff0428` 해소 전에는 hard pass/fail 금지다. 현재 `submitted=0`이라 제출 회복/latency danger share/fill quality를 평가할 수 없어 direction-only로만 닫는다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/python` 집계로 `09:00:00~09:19:59` 구간 `ENTRY_PIPELINE` stage count, `order_bundle_submitted`, `latency_state_danger`, `quote_fresh_composite_canary_applied`, `fallback_regression_count`를 확인했다.
    - 같은 집계에서 `orderbook_stability_observed=251`이 확인돼 재기동 후 신규 observe-only 축이 live 로그에 적재되는 것도 함께 검증됐다.
  - 다음 액션: `[QuoteFreshComposite0428-1000]`에서 `h1000 (09:00:00~10:00:00)` 구간으로 재판정한다. 10시에도 `submitted=0`이면 active canary는 유지하되 direction-only `보류`와 표본 부족 수치를 누적 기록한다.

- [x] `[SoftStopGrace0428-1000] soft_stop_micro_grace 10시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, `보류` 시에도 다음 1시간 점검 또는 OFF/교체 액션을 기록한다.
  - 실행 메모 (`2026-04-28 10:55 KST`): `tmp/2026-04-28/soft_stop_micro_grace_summary_h1000.json`과 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`의 `09:00:00~10:00:00` 구간을 대조했다. same-slot `soft_stop_micro_grace=0`, `scalp_soft_stop_pct=0`, `scalp_hard_stop_pct=0`, `same_symbol_reentry_loss_count=0`, `fallback_regression=0`이다. `HOLDING_PIPELINE`에는 trailing 기반 `exit_signal/sell_completed`만 1건 있었고 soft-stop cohort는 아직 없다.
  - 판정 결과: `보류`
  - 근거: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md:119) 기준 `soft_stop_micro_grace_events >= 10` 또는 `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail 금지다. 10시 창은 보유/청산 이벤트 자체는 일부 있었지만 `soft_stop_micro_grace`와 `scalp_soft_stop_pct` 표본이 0건이어서 유지/OFF를 닫을 근거가 없다.
  - 검증:
    - `tmp/2026-04-28/soft_stop_micro_grace_summary_h1000.json`
    - `PYTHONPATH=. .venv/bin/python` 집계로 `09:00:00~10:00:00` 구간 `HOLDING_PIPELINE` stage count, `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `fallback_regression_count`를 재확인했다.
  - 다음 액션: `[SoftStopGrace0428-1100]`에서 `10:00:00~11:00:00` 구간을 재판정한다. 특히 `10:53:50 KST` 수동 재기동 이후 표본을 포함해 `soft_stop_micro_grace` 발생 여부와 `scalp_soft_stop_pct` 비악화 여부를 다시 본다.

- [x] `[QuoteFreshComposite0428-1000] latency_quote_fresh_composite 10시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:10~10:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `composite_no_recovery`면 `OFF 또는 다음 독립축 교체`, 전제 미충족이면 `direction-only 보류`와 2영업일 유효기간 및 다음 점검시각을 기록한다.
  - 실행 메모 (`2026-04-28 10:55 KST`): `tmp/2026-04-28/entry_quote_fresh_composite_summary_h1000.json`은 `budget_pass/submitted/orderbook_stability=0`으로 비어 있었지만, same-slot 원문 `pipeline_events` 집계는 `budget_pass=1223`, `latency_block=1222`, `latency_pass=1`, `order_bundle_submitted=1`, `orderbook_stability_observed=1223`, `fallback_regression=0`을 보여준다. `latency_block` 사유는 `latency_state_danger=1120`, `latency_fallback_deprecated=102`이며, `quote_fresh_composite_canary_applied=True` 표본은 아직 0건이다.
  - 판정 결과: `direction-only 보류`
  - 근거: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md:113)~[121] 기준 hard pass/fail 전제는 `submitted_orders >= 20`, baseline `>= N_min`, `ShadowDiff0428` 해소다. 실제 same-slot 제출은 1건뿐이고 canary_applied baseline도 아직 0건이라, 현 시점에는 `유지/OFF`가 아니라 제출 회복 미달의 direction-only로만 닫는 것이 맞다.
  - 검증:
    - `tmp/2026-04-28/entry_quote_fresh_composite_summary_h1000.json`
    - `PYTHONPATH=. .venv/bin/python` 집계로 `09:00:00~10:00:00` 구간 `budget_pass`, `latency_block`, `latency_pass`, `order_bundle_submitted`, `quote_fresh_composite_canary_applied`, `fallback_regression_count`를 재확인했다.
    - raw 확인: `ENTRY_PIPELINE`에 `09:54:14 latency_pass`, `09:54:15 order_bundle_submitted` 1건이 있고, `10:53:50 KST` 재기동 이후에도 `budget_pass/orderbook_stability_observed/latency_block`는 다시 적재되기 시작했다.
  - 다음 액션: `[QuoteFreshComposite0428-1100]`에서 `10:00:00~11:00:00` 구간을 재판정한다. 특히 `10:53:50 KST` 재기동 이후 표본에서 `quote_fresh_composite_canary_applied=True`, `latency_state_danger share`, `submitted/full/partial`, `entry_price_guard` 기록 여부를 함께 확인한다.

- [x] `[OrderbookStability0428-1000] orderbook_stability_observation 10시 반영 확인` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:20~10:30`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1000`, `09:00:00~10:00:00`
  - 완료근거: fresh 또는 pipeline 로그에 `stage=orderbook_stability_observed`가 실제 기록되고, `entry_quote_fresh_composite_summary_h1000`에 `orderbook_stability` 섹션이 생성되며, `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted`, `unstable_vs_fill`, `unstable_vs_latency_danger`가 확인된다.
  - 판정: observe-only 로그/summary가 모두 생성되면 `반영 완료`, 로그 또는 summary 둘 중 하나라도 누락이면 `재점검 필요`, 둘 다 누락이면 `재기동 후 미반영 조사`.
  - 다음 액션: `반영 완료`여도 live gate 승격은 금지하고 관찰 표본만 누적한다. `재점검 필요` 또는 `미반영 조사`면 프로세스 재기동 시각, 첫 발생 로그 시각, bundle 경로를 함께 기록한다.
  - 실행 메모 (`2026-04-28 10:55 KST`): same-slot 원문 `pipeline_events` 기준 `orderbook_stability_observed=1223`, `unstable_quote_observed=651 (53.2%)`이며 사유는 `fr_10s=251`, `quote_age_p90=245`, `quote_age_p90+print_quote_alignment=50`, `fr_10s+print_quote_alignment=46`, `fr_10s+quote_age_p90=31`, `print_quote_alignment=23`, `all_three=5`로 분해된다. 반면 `tmp/2026-04-28/entry_quote_fresh_composite_summary_h1000.json`은 `orderbook_stability_observed_count=0`으로 비어 있어 summary가 same-slot 로그를 반영하지 못했다.
  - 판정 결과: `재점검 필요`
  - 근거: 관찰 이벤트는 runtime에 실제 적재됐으므로 `미반영 조사`는 아니다. 다만 checklist 기준 완료조건은 `로그`와 `summary`가 모두 맞아야 하는데, h1000 로컬 bundle summary가 stale/empty 상태라 `반영 완료`로 닫을 수 없다.
  - 검증:
    - `tmp/2026-04-28/entry_quote_fresh_composite_summary_h1000.json`
    - `PYTHONPATH=. .venv/bin/python` 집계로 `09:00:00~10:00:00` 구간 `orderbook_stability_observed`, `unstable_quote_observed`, `unstable_reasons`를 재확인했다.
    - 재기동 후 추가 확인: `10:53:50 KST` 이후 `ENTRY_PIPELINE`에 `orderbook_stability_observed`가 다시 적재되고 있으며 `10:54:30~10:56:07` 구간 샘플에서도 `fr_10s`, `quote_age_p50/p90`, `print_quote_alignment`, `unstable_reasons`가 정상 출력된다.
  - 다음 액션: `tmp/2026-04-28` h1000 bundle은 stale로 보고, `[OrderbookStability0428-1100]` 또는 다음 analyzer 재실행에서 `entry_quote_fresh_composite_summary_h1100`의 `orderbook_stability` 섹션이 runtime 로그와 맞는지 재검증한다. live gate 승격은 계속 금지한다.

- [x] `[LatencyEntryPriceGuard0428] DANGER override 진입가 3틱 방어 v1 구현/검증` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 10:30~10:45`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정: 구현 완료. `latency_state=DANGER`가 기존 `latency_quote_fresh_composite` canary로 `ALLOW_NORMAL` override될 때만 BUY 진입가를 v1 임시값 `3틱 하향`으로 방어한다.
  - 범위: 신규 live canary가 아니라 기존 active entry canary의 체결품질 보호 가드다. fallback/scout/split-entry는 재도입하지 않고 SELL/청산가는 기존 정책을 유지한다.
  - 완료근거: `EntryConfig.latency_override_defensive_ticks=3`, `entry_price_guard=latency_danger_override_defensive`, `entry_price_defensive_ticks`, `normal_defensive_order_price`, `latency_guarded_order_price`, `counterfactual_order_price_1tick`, `order_price`가 runtime 및 offline summary에 남는다.
  - 비교 설계: v1은 실주문 3틱 적용과 `counterfactual_order_price_1tick` 로그 방식으로만 1틱 대비 우열을 비교한다. 종목 절반 live A/B는 동일 단계 단일 canary 원칙과 충돌하므로 별도 승인 전까지 금지한다.
  - 검증: `.venv` 기준 unit/integration test와 analyzer summary test로 SAFE 1틱 유지, DANGER override 3틱 적용, `target_buy_price` 상한, 가격대 tick 경계, pipeline guard 필드, offline `latency_entry_price_guard` 집계를 확인했다.
  - 다음 액션: live 반영에는 bot 재기동이 필요하다. 적용 후 시간대별 bundle에서 `latency_entry_price_guard.submitted_guard_breakdown`과 `three_tick_guard` cohort를 확인한다.

- [x] `[SoftStopGrace0428-1100] soft_stop_micro_grace 11시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 11:00~11:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1100`, `10:00:00~11:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 실행 메모 (`2026-04-28 12:08 KST`, 정정): 서버 원시 `pipeline_events_2026-04-28.jsonl`의 `10:00:00~11:00:00` 창 기준 `soft_stop_micro_grace=0`, `scalp_soft_stop_pct=1`, `scalp_hard_stop_pct=0`, `same_symbol_reentry_loss_count=0`, `fallback_regression=0`이었다. `우원개발(046940)`이 `10:13:30 KST`에 `exit_rule=scalp_soft_stop_pct`, `sell_completed profit_rate=-1.86%`로 종료됐고, `HOLDING_PIPELINE` 총계는 `holding_started=2`, `sell_completed=2`, `hard_time_stop_shadow=1`, `loss_fallback_probe=1`이었다.
  - 판정 결과: `보류`
  - 근거: same-slot soft stop은 실제 1건 있었지만, hard pass/fail 전제인 `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort >= 10`에는 여전히 크게 못 미친다. 또한 해당 사례는 `soft_stop_micro_grace` stage가 기록되지 않았으므로, 이번 축이 손절을 줄였다고 결론 내릴 근거도 아직 없다.
  - 검증: stale 가능성이 있는 `tmp/2026-04-28` summary는 근거에서 제외하고, 서버 원시 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`에서 `exit_rule=scalp_soft_stop_pct`, `sell_completed`, `046940` 종목 로그를 재확인했다. 최초 오집계는 `stage 이름`만 세고 `exit_rule`를 놓친 임시 집계 오류였다.
  - 다음 액션: `[SoftStopGrace0428-1200]`에서 계속 같은 원시 기준으로 누적한다. soft-stop 표본이 생길 때까지 `유지/보류`만 허용하고, hard stop 전환이나 동일종목 손실 악화가 발생하면 즉시 OFF 후보로 승격한다.

- [x] `[QuoteFreshComposite0428-1100] latency_quote_fresh_composite 11시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 11:10~11:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1100`, `10:00:00~11:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 실행 메모 (`2026-04-28 11:18 KST`): 서버 원시 `10:00:00~11:00:00` 창 기준 `budget_pass=1862`, `latency_block=1858`, `latency_pass=4`, `order_bundle_submitted=4`, `order_leg_request=4`, `fallback_regression=0`이었다. blocker 사유는 `latency_state_danger=1823`, `latency_fallback_deprecated=35`였고, `latency_quote_fresh_composite_normal_override=1`, `safe_normal_entry_allowed=3`이었다. `quote_fresh_composite_canary_applied=True`는 1건뿐이며 제출 guard는 `latency_danger_override_defensive=1`, 나머지 3건은 guard 미적용 normal이었다.
  - 판정 결과: `direction-only 보류`
  - 근거: `budget_pass_to_submitted_rate`는 `4 / 1862 = 0.21%`로 10시 창 `1 / 1223 = 0.08%` 대비 개선됐고 canary 실표본 1건에서 실제 제출도 확인됐다. 그러나 hard pass/fail 전제인 `submitted_orders >= 20`, baseline `N_min`, `ShadowDiff0428` 해소를 충족하지 못해 승격/실패 판정을 닫을 표본은 아니다.
  - 검증: stale 가능성이 있는 `tmp/2026-04-28/*h1100*` summary는 근거에서 제외하고, 서버 원시 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`에서 `quote_fresh_composite_canary_applied`, `latency reason`, `entry_price_guard`, `order_bundle_submitted`를 재집계했다.
  - 다음 액션: `[QuoteFreshComposite0428-1200]`에서 `submitted >= 20` 도달 여부와 `canary_applied=True` cohort의 `submitted/full/partial/COMPLETED + valid profit_rate`를 이어서 본다. 현 시점에서는 5개 파라미터 묶음 OFF 또는 신규 축 교체 판단을 열지 않는다.

- [x] `[OrderbookStability0428-1100] orderbook_stability_observation 11시 반영 재확인` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 11:20~11:30`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1100`, `10:00:00~11:00:00`
  - 완료근거: `entry_quote_fresh_composite_summary_h1100`의 `orderbook_stability` 섹션이 runtime `ENTRY_PIPELINE stage=orderbook_stability_observed` 집계와 같은 방향으로 생성되고, `unstable_quote_observed_count/share`, `unstable_reason_breakdown`, `unstable_vs_submitted`, `unstable_vs_fill`, `unstable_vs_latency_danger`가 0이 아닌 표본으로 확인된다.
  - 판정: runtime 로그와 summary가 함께 맞으면 `반영 완료`, summary만 비면 `analyzer 재실행 필요`, 둘 다 비면 `재기동 후 미반영 조사`.
  - 실행 메모 (`2026-04-28 11:18 KST`): 서버 원시 `10:00:00~11:00:00` 창 기준 `orderbook_stability_observed=1862`, `unstable_quote_observed=907 (48.7%)`였다. 사유는 `quote_age_p90=544`, `fr_10s=182`, `quote_age_p90+print_quote_alignment=66`, `fr_10s+print_quote_alignment=46`, `print_quote_alignment=39`, `fr_10s+quote_age_p90=21`, `all_three=9`로 분해됐다. 제출 4건 중 `latency_danger_override_defensive` 1건도 원시 runtime에는 정상 기록됐다.
  - 판정 결과: `반영 완료 (서버 원시 runtime 기준)`
  - 근거: 관찰 이벤트 자체는 11시 창에서 대량 적재됐고 `unstable_quote_observed_count/share`와 사유 breakdown도 충분한 표본으로 확인됐다. 로컬 `tmp/2026-04-28` h1100 summary는 stale/invalid 가능성이 남아 있으므로 이번 슬롯은 `summary 일치`가 아니라 `server raw runtime 반영` 기준으로 닫는다.
  - 검증: `data/pipeline_events/pipeline_events_2026-04-28.jsonl`에서 `stage=orderbook_stability_observed`와 `unstable_reasons`를 재집계했다. local summary metadata의 `pipeline_event_rows_loaded=0` 계열 값은 판정 근거에서 제외했다.
  - 다음 액션: observe-only 유지. `[OrderbookStability0428-1200]`부터는 가능하면 실제 bundle root를 직접 읽은 analyzer summary와 다시 합류시키되, mismatch가 남으면 bundle path/manifest 로드 실패를 우선 조사한다.

- [x] `[SoftStopGrace0428-1200] soft_stop_micro_grace 12시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1200`, `11:00:00~12:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 실행 메모 (`2026-04-28 12:03 KST`): 서버 원시 `pipeline_events_2026-04-28.jsonl`의 `11:00:00~12:00:00` 창 기준 `soft_stop_micro_grace=0`, `scalp_soft_stop_pct=0`, `scalp_hard_stop_pct=0`, `same_symbol_reentry_loss_count=0`, `fallback_regression=0`이었다. `HOLDING_PIPELINE`은 `holding_started=1`, `sell_completed=1`, `hard_time_stop_shadow=2`만 확인됐고 soft-stop qualifying cohort는 계속 0건이다.
  - 판정 결과: `보류`
  - 근거: 11시 창에 이어 12시 창도 hard pass/fail 전제 표본이 전혀 형성되지 않았다. 아직 즉시 OFF 사유는 없지만, same-day hard 판정이 밀릴 가능성이 높아졌다.
  - 검증: stale 가능성이 있는 `tmp/2026-04-28` summary는 사용하지 않고, 서버 원시 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`만 사용해 `11:00:00~12:00:00` 구간 stage 집계를 재확인했다.
  - 다음 액션: `[SoftStopGrace0428-1300]`까지도 soft-stop cohort가 0이면 장중 hard 판정 기대를 낮추고, `[HoldingExitPostclose0428]`에서 same-day 관찰축 유지 여부를 장후 분해 기준으로 닫는다.

- [x] `[QuoteFreshComposite0428-1200] latency_quote_fresh_composite 12시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 12:10~12:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1200`, `11:00:00~12:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 실행 메모 (`2026-04-28 12:03 KST`): 서버 원시 `11:00:00~12:00:00` 창 기준 `strength_momentum_pass=1147`, `budget_pass=1731`, `latency_block=1731`, `latency_pass=0`, `order_bundle_submitted=0`, `fallback_regression=0`이었다. blocker 사유는 `latency_state_danger=1663`, `latency_fallback_deprecated=68`이었고, `quote_fresh_composite_canary_applied=True`는 0건이었다.
  - 판정 결과: `direction-only 보류`
  - 근거: 사용자 우려대로 BUY 후보는 계속 존재하지만 제출 회복은 12시 창에서 오히려 0건으로 후퇴했다. 다만 이번 창은 `submitted_orders >= 20`, baseline `N_min`, `ShadowDiff0428` 해소를 여전히 충족하지 못하고, canary 실표본도 0건이라 same-slot hard fail이나 즉시 축 교체를 닫을 단계는 아니다.
  - 검증: stale 가능성이 있는 `tmp/2026-04-28/*h1200*` summary는 배제하고, 서버 원시 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`에서 `strength_momentum_pass`, `budget_pass`, `latency_block`, `latency reason`, `quote_fresh_composite_canary_applied`, `order_bundle_submitted`를 재집계했다.
  - 다음 액션: `[QuoteFreshComposite0428-1300]`에서도 `submitted=0` 또는 `canary_applied=True=0`가 반복되면 장중 유지 논리를 약화된 것으로 보고, `[QuoteFreshReview0428]`와 `[QuoteFreshBackupComposite0428]`에서 `현 축 유지 vs OFF/교체`를 장후 우선 판정한다.

- [x] `[SoftStopGrace0428-1300] soft_stop_micro_grace 13시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 13:00~13:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1300`, `12:00:00~13:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, `same_symbol_reentry_loss_count` 악화 시 soft_stop 축과 분리한 후속 후보를 기록한다.
  - 판정: `보류`. `h1300` summary는 `/home/ubuntu/KORStockScan/tmp/2026-04-28` 기준으로 `bundle_dir`/`pipeline_event_rows_loaded` 메타데이터가 비어 있어 stale 가능성이 높아서 서버 원시 `12:00:00~13:00:00` 집계로 닫았다.
  - 완료 메모: 서버 원시 기준 `soft_stop_micro_grace=21`, `scalp_soft_stop_pct=1`, `scalp_hard_stop_pct=0`, `same_symbol_reentry_loss_count=0`였다. soft-stop qualifying cohort는 `씨아이에스(222080)` 1건이며 `soft_stop_micro_grace`가 실제로 개입한 뒤 `12:35:05 KST` `profit_rate=-1.78%`, `sell_completed=-1.83%`로 종료됐다. 즉 장중 표본 0은 아니지만 hard pass/fail 전제인 `COMPLETED + valid profit_rate >= 10`은 여전히 미충족이다.
  - 다음 액션: `[HoldingExitPostclose0428]`, `[SoftStopGoodCut0428]`에서 `씨아이에스(222080)`를 `micro grace 개입 실패 표본`으로 분리하고, 우원개발류 `비개입 soft stop`과 혼합 결론을 금지한다.

- [x] `[QuoteFreshComposite0428-1300] latency_quote_fresh_composite 13시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 13:10~13:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1300`, `12:00:00~13:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 성공 기준 충족 시 `유지`, `fallback_regression >= 1`이면 즉시 OFF/회귀조사, 전제 미충족 시 direction-only와 다음 점검시각 기록.
  - 판정: `direction-only 보류`. `/home/ubuntu/KORStockScan/tmp/2026-04-28/entry_quote_fresh_composite_summary_h1300.json`은 메타데이터/summary가 비어 있어 stale 또는 invalid summary로 보고, 서버 원시 `12:00:00~13:00:00` 집계로 닫았다.
  - 완료 메모: 서버 원시 기준 `budget_pass=897`, `latency_block=896`, `latency_pass=1`, `order_bundle_submitted=1`, `quote_fresh_composite_canary_applied=True=0`, `latency_pass reason=safe_normal_entry_allowed 1건`이었다. 즉 제출 1건은 있었지만 active canary가 실제 제출 회복을 만든 표본은 없고, hard pass/fail 전제 `submitted_orders >= 20`도 미충족이다.
  - 다음 액션: `[QuoteFreshComposite0428-1400]`에서도 `quote_fresh_composite_canary_applied=True=0` 또는 `submitted` 정체가 반복되면, 장후 `[QuoteFreshReview0428]`와 `[QuoteFreshBackupComposite0428]`에서 `현 축 유지 vs OFF/교체`를 우선 판정한다. 14시부터는 `tmp/2026-04-28` summary 메타데이터(`bundle_dir`, `manifest_generated_at`, `pipeline_event_rows_loaded`)를 먼저 확인한 뒤 사용한다.

- [x] `[SoftStopGrace0428-1400] soft_stop_micro_grace 14시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1400`, `13:00:00~14:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: 15시 최종판정 전 `유지`, `OFF`, `보류` 임시판정을 기록하고, OFF 필요 시 재기동 필요 여부를 먼저 정리한다.
  - 완료 메모: 사용자 승인으로 `14시 장중 점검 생략 -> 16:00 KST raw 기반 통합점검`으로 대체했다. `offline bundle` 생성 없이 `data/pipeline_events/pipeline_events_2026-04-28.jsonl`와 장후 `post_sell` 산출물 기준으로 닫는다.

- [x] `[QuoteFreshComposite0428-1400] latency_quote_fresh_composite 14시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 14:10~14:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1400`, `13:00:00~14:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: 15시 최종판정 전 `유지`, `OFF`, `교체`, `direction-only 보류` 임시판정을 기록하고, 부분 적용 금지를 재확인한다.
  - 완료 메모: 사용자 승인으로 `14시 장중 점검 생략 -> 16:00 KST raw 기반 통합점검`으로 대체했다. 장 종료 후에는 `pipeline_events` 파일이 정적이므로 `offline bundle` 없이 raw 집계로 same-day 판정을 닫는다.

- [x] `[SoftStopGrace0428-1500] soft_stop_micro_grace 15시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:00~15:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1500`, `14:00:00~15:00:00`
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `full_fill`, `partial_fill`, `same_symbol_reentry_loss_count`, `emergency_pct <= -2.0`, `fallback_regression=0`.
  - hard pass/fail 전제: `soft_stop_micro_grace >= 10` 또는 `soft_stop qualifying cohort`의 `COMPLETED + valid profit_rate >= 10`.
  - 판정/다음 액션: `유지`, `OFF`, `보류` 중 하나로 닫고, 보류 시 누적 표본 부족 수치와 `2026-04-29 10:00` 재판정 조건을 기록한다.
  - 완료 메모: 사용자 승인으로 `15시 장중 점검 생략 -> 16:00 KST raw 최종점검`으로 대체했다. 장 종료 후 same-day raw 누적으로 최종 판정을 닫으므로 15시 중간 판정은 생략한다.

- [x] `[QuoteFreshComposite0428-1500] latency_quote_fresh_composite 15시 점검` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - label/window: `h1500`, `14:00:00~15:00:00`
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `full_fill`, `partial_fill`, `quote_fresh_composite_canary_applied=True/False`, `ShadowDiff0428`, `fallback_regression=0`.
  - hard pass/fail 전제: `submitted_orders >= 20`, baseline 표본 `>= N_min`, `ShadowDiff0428` 해소.
  - 판정/다음 액션: `유지`, `OFF`, `다음 독립축 교체`, `direction-only 보류` 중 하나로 닫고, direction-only는 2영업일 내 재판정 및 미재판정 자동 OFF를 기록한다.
  - 완료 메모: 사용자 승인으로 `15시 장중 점검 생략 -> 16:00 KST raw 최종점검`으로 대체했다. 장 종료 후 same-day raw 누적으로 OFF/유지/교체 판정을 닫으므로 15시 중간 판정은 생략한다.

- [x] `[SoftStopGrace0428-Final1500] soft_stop_micro_grace 15시 종합판정` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:00~15:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 결과는 `유지`, `OFF`, `표본부족으로 2026-04-29 10:00 재판정` 중 하나만 허용한다.
  - 완료근거: 09:00~15:00 누적 표본 수, hard stop 전환/동일종목 손실/미체결 악화 여부, `fallback_regression=0`.
  - 다음 액션: 표본부족 재판정은 누적 표본 수와 `2026-04-29 10:00 KST` 절대시각을 함께 기록한다.
  - 완료 메모: 사용자 승인으로 `16:00 KST raw 최종점검`으로 대체했다. same-day 최종판정은 `[SoftStopGrace0428-1600Raw]`가 소유한다.

- [x] `[QuoteFreshComposite0428-Final1500] latency_quote_fresh_composite 15시 종합판정` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 15:10~15:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 결과는 `유지`, `OFF`, `다음 독립축 교체`, `direction-only로 2026-04-29 10:00 재판정` 중 하나만 허용한다.
  - 완료근거: same bundle baseline, `submitted_orders`, `latency_state_danger`, fill quality, `ShadowDiff0428`, `fallback_regression=0`.
  - 다음 액션: `direction-only`는 `2영업일 내 재판정, 미재판정 시 자동 OFF` 규칙을 명시한다. `OFF/교체` 시 예비축은 `latency_signal_quality_quote_composite`만 검토하고, 기존 5개 파라미터 부분 적용은 금지한다.
  - 완료 메모: 사용자 승인으로 `16:00 KST raw 최종점검`으로 대체했다. same-day 최종판정은 `[QuoteFreshComposite0428-1600Raw]`가 소유한다.

## 장후 체크리스트 (18:05~19:20)

- [x] `[SoftStopGrace0428-1600Raw] soft_stop_micro_grace 16시 raw 통합점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:00~16:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 범위: `09:00:00~15:30:00` same-day raw 누적
  - 완료근거: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `COMPLETED + valid profit_rate`, `same_symbol_reentry_loss_count`, `micro grace 개입 표본 vs 비개입 soft stop 표본` 분리.
  - 판정 기준: 장 종료 후 `pipeline_events`가 정적이면 `offline bundle` 없이 raw 기준으로 `유지`, `OFF`, `보류` 중 하나를 닫는다.
  - 실행 메모 (`2026-04-28 16:05 KST`): `data/pipeline_events/pipeline_events_2026-04-28.jsonl`의 `09:00:00~15:30:00` raw 누적 기준 `soft_stop_micro_grace=21`, `scalp_soft_stop_pct=2`, `scalp_hard_stop_pct=0`, `scalp_trailing_take_profit=4`, `same_symbol_reentry_loss_count=0`이었다. `micro grace` 개입 표본은 `씨아이에스(222080)` 1건뿐이고, `우원개발(046940)`은 `scalp_soft_stop_pct`였지만 `micro grace` 비개입 표본이었다.
  - 판정 결과: `보류`
  - 근거: same-day raw 기준으로 severe-loss guard 악화(`scalp_hard_stop_pct=0`)나 동일종목 재진입 손실 증거는 없었지만, 실제 `micro grace` 개입 cohort는 `씨아이에스` 1건뿐이고 해당 종목의 `post_sell_evaluation`은 아직 생성되지 않았다. 즉 `OFF`까지 갈 악화는 없지만 `유지`를 hard하게 닫을 cohort도 부족하다.
  - 테스트/검증:
    - `tmp/2026-04-28/raw_postclose_0428_summary.json`
    - `data/post_sell/post_sell_candidates_2026-04-28.jsonl`에서 `우원개발(046940)`, `씨아이에스(222080)` candidate 확인
    - `pipeline_events` raw에서 `씨아이에스(222080)`의 `soft_stop_micro_grace -> exit_signal/sell_completed` 구간 재확인
  - 다음 액션: `씨아이에스(222080)`는 `micro grace 개입 실패`, `우원개발(046940)`은 `비개입 soft stop`으로 분리하여 장후 감리에 연결한다. `2026-04-29`에는 `씨아이에스 post_sell 평가 생성 여부`를 확인한 뒤 `soft_stop_micro_grace_extend` 승격 여부를 다시 본다.

- [x] `[QuoteFreshComposite0428-1600Raw] latency_quote_fresh_composite 16시 raw 통합점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 16:10~16:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 범위: `09:00:00~15:30:00` same-day raw 누적
  - 완료근거: `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `quote_fresh_composite_canary_applied=True/False`, `full_fill`, `partial_fill`, `ShadowDiff0428`, `fallback_regression=0`.
  - 판정 기준: 장 종료 후 `pipeline_events`가 정적이면 `offline bundle` 없이 raw 기준으로 `유지`, `OFF`, `다음 독립축 교체`, `direction-only 보류` 중 하나를 닫는다.
  - 실행 메모 (`2026-04-28 16:08 KST`): same-day raw 누적 기준 `budget_pass=8547`, `latency_block=8540`, `latency_pass=7`, `order_bundle_submitted=7`, `full_fill=6`, `partial_fill=0`, `orderbook_stability_observed=8547`, `unstable_quote_observed=8547`이었다. blocker 사유는 `latency_state_danger=8208`, `latency_fallback_deprecated=332`였고, `latency_pass` 사유는 `safe_normal_entry_allowed=6`, `latency_quote_fresh_composite_normal_override=1`이었다. same-day 제출률은 `7 / 8547 = 0.082%`로 `2026-04-27 15:00` reference `0.1%`보다 낮았고, `latency_state_danger / budget_pass = 96.0%`로 reference `94.8%`보다 악화됐다.
  - 판정 결과: `OFF`
  - 근거: hard baseline은 `ShadowDiff0428` 미해소로 여전히 방향성 판정만 가능하지만, same-day 누적에서도 `budget_pass_to_submitted_rate` 회복이 reference를 넘지 못했고 `latency_state_danger` share도 개선되지 않았다. `latency_quote_fresh_composite_normal_override`는 `피에스케이홀딩스(031980)` 1건만 확인되어 묶음 축이 entry drought를 해소했다고 보기 어렵다. `fallback_regression=0`은 지켰지만 기대값 관점에서는 active entry 축 유지 근거가 부족하다.
  - 테스트/검증:
    - `tmp/2026-04-28/raw_postclose_0428_summary.json`
    - `pipeline_events` raw에서 same-day `order_bundle_submitted` 7건과 `entry_price_guard` 분포 확인
    - reference 비교: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) §6
  - 다음 액션: `2026-04-29 PREOPEN`에 `latency_quote_fresh_composite OFF + restart.flag 반영 확인`을 남긴다. `latency_signal_quality_quote_composite`는 예비축으로만 유지하고, `ShadowDiff0428` 재분해 전에는 자동 ON 하지 않는다.

- [x] `[HoldingExitPostclose0428] soft_stop/trailing/same_symbol 장후 분해` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:00`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `soft_stop_micro_grace`, `scalp_soft_stop_pct`, `trailing`, `same_symbol_reentry`, `hard_stop_auxiliary`를 분리하고 full/partial, initial/pyramid 합산 결론을 금지한다.
  - 완료근거: soft_stop/trailing/same_symbol/hard_stop_auxiliary 분리표, `COMPLETED + valid profit_rate`, full/partial 분리, missed_upside/opportunity cost 분리.
  - 실행 메모 (`2026-04-28 16:15 KST`): saved snapshot [holding_exit_observation_2026-04-28.json](/home/ubuntu/KORStockScan/data/report/monitor_snapshots/holding_exit_observation_2026-04-28.json) 기준 `readiness={submitted_orders=5, full_fill_events=4, partial_fill_events=0, completed_valid_trades=4, observation_ready=False, directional_only=True}`였다. same-day raw는 `submitted=7`, `full_fill=6`, `completed_valid=6`으로 더 크므로, saved snapshot은 장후 final refresh 이전 값으로 보고 direction-only로만 해석했다. snapshot 기준 `soft_stop completed_valid_avg_profit_rate=-1.671`, `realized_pnl_krw=-658,942`, `trailing completed_valid_avg_profit_rate=+1.066`, `realized_pnl_krw=+288,293`, `same_symbol after_soft_stop_count=12`, `after_soft_stop_next_loss_count=5`였다.
  - 판정 결과: `directional_only 유지`
  - 근거: 보유/청산 축의 pain point는 여전히 `soft_stop`이고, 월간 `soft_stop_rebound`/`same_symbol_reentry` 시그널도 유지된다. 다만 same-day saved snapshot 자체가 raw보다 under-count라 hard pass/fail을 닫을 상태는 아니다.
  - 테스트/검증:
    - `data/report/monitor_snapshots/holding_exit_observation_2026-04-28.json`
    - `tmp/2026-04-28/raw_postclose_0428_summary.json`
  - 다음 액션: `2026-04-29`에는 saved snapshot refresh와 `ShadowDiff` 재검증을 먼저 맞춘 뒤 보유축 baseline을 다시 잠근다.

- [x] `[SoftStopGoodCut0428] good-cut soft stop vs whipsaw soft stop 분리` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:10`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `scalp_soft_stop_pct` 사례를 `good_cut`과 `whipsaw`로 분리한다. `good_cut`은 단일 시점 가격이 아니라 `T+5/T+15/T+30/종가` 가격분포, `MFE/MAE`, `post_sell rebound`, `AI 급락`, `시장/섹터 동조성`을 같이 본다. 최소 기준은 `peak_profit <= +0.20%`, `매도 후 추가 하락 지속`, `AI 급락`이면 `good_cut` 후보, `post_sell rebound_above_sell=True` 또는 `mfe_ge_0_5 / mfe_ge_1_0`이면 `whipsaw` 우선으로 본다. 두 성격이 공존하면 `ambiguous`로 남긴다.
  - 완료근거: 우원개발(046940) 포함 same-day `scalp_soft_stop_pct` 사례에 대해 `good_cut / whipsaw / ambiguous` 라벨, `exit_rule`, `peak_profit`, `sell_completed profit_rate`, `T+5/T+15/T+30/종가`, `MFE`, `MAE`, `post_sell rebound`, `same_symbol_soft_stop_cooldown_would_block`가 같이 남는다.
  - 실행 메모 (`2026-04-28 16:20 KST`): same-day `scalp_soft_stop_pct`는 `우원개발(046940)`, `씨아이에스(222080)` 2건이었다. `우원개발`은 `rebound_above_sell_10m=True`, `rebound_above_buy_10m=False`, `mfe_10m_pct=1.327`, `close_ret_10m_pct=0.166`이라 `whipsaw/ambiguous`로 분류했고, `씨아이에스`는 `post_sell_candidate`만 있고 `evaluation`이 아직 없어 최종 라벨을 pending으로 남겼다. same-day `good_cut` 확정 표본은 0건이다.
  - 판정 결과: `whipsaw 우세 / good_cut 미확정`
  - 근거: 단일 시점 현재가가 아니라 `post_sell` 시계열 기준으로 보면 `우원개발`은 매도가 위로는 회복했지만 매수가 회복은 못했고, `씨아이에스`는 아직 평가 파일이 비어 있다. 따라서 same-day `soft_stop_micro_grace`를 실패로 단정하기보다 `whipsaw 성향 우세`로 보는 것이 맞다.
  - 테스트/검증:
    - `data/post_sell/post_sell_evaluations_2026-04-28.jsonl`
    - `data/post_sell/post_sell_candidates_2026-04-28.jsonl`
  - 다음 액션: `2026-04-29 POSTCLOSE`에 `씨아이에스` 평가가 생성되면 `good_cut / whipsaw / ambiguous`를 다시 닫는다. 월간 기준 `whipsaw=60`, `good_cut_candidate=4`라 `extend` 검토는 유지하되 same-day 즉시 승인하지 않는다.

- [x] `[EntryFollowThrough0428] 우원개발류 follow-through 실패 분해 및 예비축 정의` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:10~18:25`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: `latency=SAFE/ALLOW_NORMAL` 또는 기존 entry gate 통과 후에도 `peak_profit`이 거의 없이 `AI/strength`가 급락하고 `soft_stop` 또는 미미한 반등 후 청산으로 이어지는 종목을 `follow_through_failure` 후보로 묶는다. `latency miss`와 혼합 결론을 금지하되, 분석 결과가 충분히 쌓이면 진입 게이트 보강 후보로 환류될 여지는 열어둔다.
  - 완료근거: 우원개발(046940) 등 same-day 사례에 대해 `entry_mode`, `latency state`, `peak_profit`, `held_sec`, `profit_rate`, `post_sell path`, `체결 후 30초/1분/3분 가격궤적`, `AI score velocity(진입평가시→체결시→보유 N초)`, `체결 시점 호가/거래량`, `시장/섹터 동조성`을 한 표에 묶고, `entry follow-through quality`가 다음 후보축인지 아닌지 판정을 남긴다.
  - 실행 메모 (`2026-04-28 16:23 KST`): 월간 lightweight backfill 기준 `follow_through_failure candidate_count=3`이며 `덕산하이메탈(3419)`, `LB세미콘(3873)`, `우원개발(4085)`가 top case였다. `우원개발`은 `entry_mode=normal`, `fill_quality=full_fill`, `peak_profit=0.1`, `held_sec=199`, `profit_rate=-1.86`, `rebound_above_sell_10m=True`, `rebound_above_buy_10m=False`, `mfe_10m_pct=1.327`로 분류됐다.
  - 판정 결과: `예비축 미승인 / observe-only 유지`
  - 근거: today same-day와 월간 스크리닝 모두 `follow-through_failure` 표본이 3건뿐이라 신규 live 축을 열기에는 너무 적다. 다만 `우원개발`이 `latency miss`가 아니라 `valid entry 후 follow-through failure`라는 점은 충분히 확인됐다.
  - 테스트/검증:
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.json`
  - 다음 액션: `follow_through_failure` 표본이 `20건`에 도달하기 전까지는 observe-only feature backtrace만 진행하고, `latency_quote_fresh_composite` OFF 판정과 혼합하지 않는다.

- [x] `[FollowThroughSchema0428] 체결 후 N초 가격행동·AI velocity 로그 스키마 보강안 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:35`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: 향후 `follow_through_failure` 감리를 위해 `체결 후 30초/1분/3분 가격`, `AI score velocity`, `MFE/MAE`, `체결 시점 호가 잔량 비율`, `직전 거래량`, `시장/섹터 동조성`을 공통 로그/스냅샷 스키마에 넣을지 범위를 잠근다. 표본 1건만으로 정책 변경 근거로 쓰지 않는다는 문구를 같이 명시한다.
  - 완료근거: 신규 로그 필드 후보, 저장 위치(`pipeline/holding/post_sell/snapshot`), 계산 시점, 필드명 초안, 과부하 우려와 우회 경로가 정리된다.
  - 판정 결과: `잠금 완료`
  - 완료 메모: observe-only 후보 필드는 `체결 후 30초/1분/3분 가격`, `AI score velocity`, `MFE/MAE`, `체결 시점 호가 잔량 비율`, `직전 거래량`, `시장/섹터 동조성`으로 고정한다. 저장 위치는 `pipeline/holding/post_sell/snapshot` 중 `post_sell + snapshot 우선`, raw pipeline 보강은 후순위로 둔다. 표본 1건만으로 정책 변경 근거로 쓰지 않는다는 문구도 유지한다.
  - 다음 액션: `2026-04-29 POSTCLOSE`에 구현 범위 검토 항목을 생성한다.

- [x] `[AprilFollowThroughBackfill0428] 4월 soft_stop/follow-through 후보 월간 선별 백필` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:35~18:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 4월 전체를 heavy rebuild로 다시 돌리지 않고, 이미 저장된 `trade_review`, `post_sell_candidates/evaluations`, `holding_exit_observation` 입력만으로 `scalp_soft_stop_pct`와 `follow_through_failure` 후보를 월간 선별한다. `good_cut / whipsaw / ambiguous`와 `follow_through_failure`는 분리 라벨링하고, full/partial, initial/pyramid 합산 결론을 금지한다.
  - 완료근거: 4월 대상 일자 범위, 사용한 입력 파일 목록, 선별 건수, `good_cut / whipsaw / ambiguous / follow_through_failure` 분포, 장후 심화분석 우선순위가 남는다.
  - 실행 메모 (`2026-04-28 16:18 KST`): lightweight backfill을 `analysis/april_follow_through_backfill.py --month-start 2026-04-01 --target-date 2026-04-28`로 재실행했다. 입력은 `trade_review snapshot 21개`, `post_sell file 27개`, `valid_completed_trades=237`, `post_sell_rows=203`, `soft_stop_rows=64`였다.
  - 판정 결과: `월간 후보 선별 완료`
  - 근거: soft-stop 라벨은 `whipsaw=60`, `good_cut_candidate=4`, `ambiguous=0`였고, `follow_through_failure` 후보는 `3건`이었다. 즉 월간 관찰 기준으로는 `soft_stop whipsaw`가 여전히 주 pain point이고, `follow-through`는 신설 live 축보다 observe-only backtrace가 먼저다.
  - 테스트/검증:
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.json`
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.md`
  - 다음 액션: `2026-04-29`에는 `follow_through schema 구현 범위`와 `soft_stop extend 재판정`만 carry-over 하고, 월간 heavy rebuild는 열지 않는다.

- [x] `[QuoteFreshPostclose0428] quote_fresh composite 장후 baseline/guard 정리` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: same bundle baseline, reference baseline, `ShadowDiff0428`, `composite_no_recovery`, `loss_cap`, `partial_fill_ratio`, `fallback_regression`을 분리 정리한다.
  - 완료근거: `quote_fresh_composite_canary_applied=True/False` baseline 비교, `2026-04-27 15:00` reference와 hard baseline 분리, guard별 발동 여부.
  - 완료 메모 (`2026-04-28 16:12 KST`): same-day raw baseline/guard는 `budget_pass=8547`, `submitted=7`, `budget_pass_to_submitted_rate=0.082%`, `latency_state_danger=8208 (96.0%)`, `full_fill=6`, `partial_fill=0`, `fallback_regression=0`으로 잠갔다. reference는 `2026-04-27 15:00 offline bundle 0.1% / 94.8%`를 유지하고, same-day는 이에 미달했다.
  - guard 발동 정리:
    - `composite_no_recovery`: directionally triggered
    - `fallback_regression`: not triggered
    - `loss_cap`: same-day canary cohort 표본 부족으로 hard 판정 보류
    - `partial_fill_ratio`: `partial_fill=0`, guard 미발동
  - 다음 액션: `2026-04-29 PREOPEN`에 `OFF/restart 반영 확인`을 남긴다.

- [x] `[QuoteFreshBackupComposite0428] latency_signal_quality_quote_composite 예비 검증축 활성화 조건 검토` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:25`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `latency_quote_fresh_composite`가 `composite_no_recovery` 또는 direction-only expiry로 종료될 때만 예비축을 검토한다. 조건은 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, `fallback_regression=0`으로 고정한다.
  - 완료근거: `signal_quality_quote_composite_candidate_events`, `submitted/full/partial`, `latency_state_danger`, `ShadowDiff0428`, `fallback_regression` 분리표.
  - 판정 결과: `보류`
  - 근거: active `latency_quote_fresh_composite`는 same-day 종료(OFF) 쪽으로 닫히지만, `ShadowDiff0428`이 아직 크고 same-day canary effect도 `latency_quote_fresh_composite_normal_override 1건`에 그친다. 따라서 예비축을 `2026-04-29 PREOPEN`에 바로 ON 하기보다, `OFF/restart 반영`과 `ShadowDiff` 재검증 후 별도 승인하는 것이 맞다.
  - 다음 액션: `2026-04-29 POSTCLOSE`에 예비축 activation 재판정 항목을 생성한다.

- [x] `[SoftStopGraceExtend0428] soft_stop_micro_grace_extend 추가 조정 파라미터 활성화 조건 검토` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:35`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: 기본 `soft_stop_micro_grace 20초`가 hard stop/동일종목 손실/미체결을 악화시키지 않았지만 반등 포착이 부족한 경우에만 `extend_sec=10`, `extend_buffer_pct=0.20`, `emergency_pct=-2.0`을 검토한다.
  - 완료근거: `soft_stop_micro_grace_events`, `extension_used`, `scalp_hard_stop_pct`, `emergency_stop_events`, `same_symbol_reentry_loss_count`, `post_sell_soft_stop_rebound_above_sell_10m`, `mfe_ge_0_5`.
  - 판정 결과: `보류`
  - 근거: same-day `micro grace` 개입은 `씨아이에스(222080)` 1건뿐이고, 해당 `post_sell_evaluation`도 아직 생성되지 않았다. 월간 `whipsaw` 비중은 높지만 same-day 직접 개입 품질을 모른 채 `extend`를 추가하면 원인귀속이 흐려진다.
  - 다음 액션: `2026-04-29 POSTCLOSE`에 `씨아이에스 평가 생성 후 extend 재판정` 항목을 생성한다.

- [x] `[FallbackSplit0428] fallback/split-entry 폐기 정합성 정리` (`Due: 2026-04-28`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:50`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 모든 실행축에서 제외 상태(`remove`)로 고정하고, `fallback_qty`는 historical guard 용어로만 남긴다.
  - why: 기준선 문서상 영구 폐기 축인데 runtime 분류표와 작업지시서에 `observe-only` 또는 `baseline-promote` 표현이 남아 있으면 재개 후보처럼 보인다.
  - 다음 액션: `remove / guarded-off / historical-only` 표현으로 같은 change set에서 문서 정합을 잠근다.

- [x] `[FallbackSplit0428] latency fallback split-entry code path hard-off 제거` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:10~09:30`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `CAUTION -> ALLOW_FALLBACK` 또는 scout/main fallback bundle이 실시간 주문 경로를 만들지 않아야 한다. `split_entry` follow-up runtime shadow도 기본 OFF여야 한다.
  - why: same-day 판정으로 entry 제출 회복과 무관한 축으로 닫혔고, partial/rebase 오염만 남긴다.
  - 다음 액션: deprecated reason/log는 historical trace로만 남기고 실전 경로는 reject로 닫는다.

- [x] `[FallbackSplit0428] 테스트·감시 지표 청소` (`Due: 2026-04-28`, `Slot: INTRADAY`, `TimeWindow: 09:40~10:20`, `Track: ScalpingLogic`)
  - Source: [workorder-shadow-canary-runtime-classification.md](/home/ubuntu/KORStockScan/docs/workorder-shadow-canary-runtime-classification.md)
  - 판정 기준: fallback/split-entry 관련 테스트는 `deprecated reject` 또는 `historical helper`만 검증하도록 축소하고, runtime shadow 기본 OFF를 같이 검증한다.
  - why: 재개를 전제한 테스트/분류가 남아 있으면 운영 문서와 상충한다.
  - 검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/trading/tests/test_entry_orchestrator.py src/trading/tests/test_entry_policy.py src/tests/test_sniper_entry_latency.py src/tests/test_sniper_entry_metrics.py src/tests/test_split_entry_followup_audit.py src/tests/test_split_entry_followup_runtime.py`
    - `PYTHONPATH=. .venv/bin/python -m py_compile src/engine/sniper_entry_latency.py src/engine/sniper_execution_receipts.py src/trading/entry/entry_orchestrator.py src/trading/entry/entry_policy.py`

- [x] `[FallbackSplit0428] 감리/보고 반영` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 17:40~18:00`, `Track: Plan`)
  - Source: [audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-single-axis-tuning-audit.md), [personal-decision-flow-notes.md](/home/ubuntu/KORStockScan/docs/personal/personal-decision-flow-notes.md)
  - 판정 기준: `왜 제거되는지`, `무엇이 historical-only로 남는지`, `다음 관측포인트는 무엇인지`를 checklist와 audit 기준으로 고정한다.
  - why: 개인문서 단독 근거 사용 금지 원칙 때문에 최종 근거는 checklist/audit에 남아야 한다.

- [x] `[QuoteFreshReview0428] quote_fresh composite 다음 판정 규칙 고정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:00~18:15`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-27-entry-latency-composite-canary-audit-review.md)
  - 판정 기준: `latency_quote_fresh_composite`는 `signal/ws_age/ws_jitter/spread/quote_stale` 5개를 개별 축으로 해석하지 않고 묶음 ON/OFF로만 판정한다. `ws_age만 유지` 같은 부분 적용은 금지한다. primary baseline은 같은 bundle 내 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본으로 고정하고, baseline이 `N_min` 미달이거나 `submitted_orders < 20`이거나 `ShadowDiff0428` 미해소면 방향성 판정으로 격하한다. `ShadowDiff0428`은 submitted/full/partial 집계의 live runtime 경로와 offline bundle 경로 간 차이가 `1건 이내`로 좁혀진 상태를 뜻한다.
  - why: 복합축 이름으로 동일 단계 다중축 실험을 우회하면 원인귀속과 rollback 판단이 깨진다.
  - hard pass/fail 전제조건:
    - `submitted_orders >= 20`
    - baseline 표본 `>= N_min`
    - `ShadowDiff0428` 해소
  - 도달목표:
    - primary: `budget_pass_to_submitted_rate >= baseline +1.0%p`
    - secondary: `latency_state_danger / budget_pass` 비율 `-5.0%p` 이상 개선 and `full_fill + partial_fill`의 `submitted` 대비 전환율이 baseline 대비 `-2.0%p` 이내
  - 감리 검토 포인트:
    - 비교 baseline이 `same bundle + canary_applied=False`로 잠겼는지
    - `2026-04-27 15:00 offline bundle`은 참고선이고 hard pass/fail 기준선이 아니라는 점이 분리됐는지
    - `composite_no_recovery`, `loss_cap`, `partial_fill_ratio`, `normal_slippage_exceeded`, `fallback_regression` guard가 성공 기준과 섞이지 않고 분리 기재됐는지
    - baseline 부족, `submitted_orders < 20`, 또는 `ShadowDiff0428` 미해소 시 `direction-only` 판정으로 격하하고 `2영업일` 내 재판정, 미재판정 시 자동 OFF 규칙이 남아 있는지
  - 다음 액션: 다음 판정 메모에는 임계값별 `분포 기준`, `예상 기각률`, `효과 부족 시 fallback 임계값`, `composite_no_recovery` guard를 함께 남긴다.
  - 실행 메모 (`2026-04-28 16:14 KST`): same-day raw 최종판정은 `OFF`로 닫고, 다음 판정 규칙은 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 허용하도록 다시 잠갔다. reference baseline은 계속 `2026-04-27 15:00 offline bundle`, hard baseline은 `same bundle + canary_applied=False + normal_only + post_fallback_deprecation` + `ShadowDiff0428` 해소 상태로만 인정한다.
  - 판정 결과: `규칙 고정 완료`
  - 다음 액션: `2026-04-29 PREOPEN`에 `latency_quote_fresh_composite OFF/restart 반영 확인`을 남기고, 예비축은 `ShadowDiff` 재검증 후 별도 승인으로 분리한다.
  - fresh 로그 없음 대응: 같은 시각 `offline_live_canary_bundle`을 생성하고 사용자 로컬 산출물의 `entry_quote_fresh_composite_summary_<label>`로 `submitted/full/partial`, `latency_state_danger`, `fallback_regression_count`, `shadow_diff_status`, `direction_only_reason`을 확인한다.

- [x] `[ShadowDiff0428] postclose submitted/full/partial mismatch 재분해` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:15~18:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md)
  - 판정 기준: `deploy/run_tuning_monitoring_postclose.sh 2026-04-27` 재실행에서 나온 `data/analytics/shadow_diff_summary.json`의 `submitted_events jsonl=19 vs duckdb=17`, `full_fill_count jsonl=37 vs duckdb=31`, `partial_fill_count jsonl=30 vs duckdb=24` 차이를 이벤트 복원/집계 품질 관점에서 재분해하고, 누락 source가 `pipeline_events`, `post_sell`, 집계 SQL 중 어디인지 닫아야 한다.
  - why: pattern lab 재실행은 복구됐지만 funnel/fill count mismatch를 그대로 두면 다음 진입병목 판정의 baseline 품질이 흔들린다.
  - 실행 메모 (`2026-04-28 16:32 KST`): `src/engine/compare_tuning_shadow_diff.py --start 2026-04-27 --end 2026-04-28` 재실행 결과 `all_match=false`였다. `2026-04-27` 기존 mismatch(`submitted 19 vs 17`, `full_fill 37 vs 31`, `partial_fill 30 vs 24`)는 그대로 남아 있고, `2026-04-28`분은 `data/analytics/parquet/pipeline_events/date=2026-04-28` 및 `post_sell/date=2026-04-28` partition 자체가 없어 DuckDB가 당일 raw를 통째로 못 읽는 상태였다.
  - 판정 결과: `미해소 / 원인위치 분리 완료`
  - 근거: same-day diff가 큰 이유는 `2026-04-28 parquet 미생성`이고, historical 소규모 mismatch는 `2026-04-27 submitted/full/partial dedup 또는 parquet builder 집계 경로`에 남아 있다. 즉 원인은 `raw pipeline`이 아니라 `parquet freshness + historical compare mismatch` 두 갈래로 분해된다.
  - 테스트/검증:
    - `tmp/2026-04-28/shadow_diff_summary_2026-04-27_2026-04-28.json`
    - `data/analytics/shadow_diff_summary.json`
    - `find data/analytics/parquet -type f`로 `2026-04-28 partition 부재` 확인
  - 다음 액션: `2026-04-29 PREOPEN`에 `2026-04-28 parquet/duckdb rebuild + shadow diff 재검증`을 남긴다. `QuoteFresh` hard baseline은 이 항목이 닫히기 전까지 재승격하지 않는다.

- [x] `[GeminiP1Rollout0428] main Gemini JSON system_instruction/deterministic flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:20`, `Track: ScalpingLogic`) (`실행: 2026-04-28 20:05 KST`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md)
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `main` 실전 엔진에서 이 flag를 켜려면 `BUY/WAIT/DROP`, `HOLD/TRIM/EXIT`, `condition/eod` JSON contract 유지, rollback owner, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 필드가 같은 메모에 잠겨 있어야 한다.
  - why: Gemini는 현재 `main` 실전 기준 엔진이라 P1은 단순 코드 완료가 아니라 live 판정 분포를 바꾸는 canary 승인 작업이다.
  - 판정 결과: `보류 유지`
  - 근거: `src/utils/constants.py` 기준 `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED=False`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED=False`로 기본값 `OFF`가 유지되고, `src/tests/test_ai_engine_api_config.py`는 토글 ON/OFF 동작만 검증한다. 하지만 workorder가 요구한 `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 메모, rollback owner가 아직 `main` 실전 승인 수준으로 같은 문서에 잠기지 않았다. active entry/holding 축이 진행 중인 날에 Gemini P1까지 같은 날 열면 원인귀속도 흐려진다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - `src/engine/ai_engine.py`, `src/utils/constants.py`에서 flag 기본값/분기 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[GeminiEngineCarry0429-Postclose]`에서 `main` live 승인 전제 문서화 여부와 observe-only/cohort 잠금부터 다시 본다.

- [x] `[DeepSeekP1Rollout0428] remote DeepSeek context-aware backoff flag 실전 승인 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:20~18:30`, `Track: ScalpingLogic`) (`실행: 2026-04-28 20:07 KST`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`는 코드상 guard가 준비됐더라도 기본값 `OFF`를 유지한다. `remote` 운용에서 flag를 켜려면 `live-sensitive cap <= 0.8s`, `report/eod cap`, jitter 상한, `api_call_lock` 장기 점유 여부, retry 이후 rate-limit/log acceptance를 함께 잠가야 한다.
  - why: DeepSeek는 `remote` 운용 엔진이라 P1 잔여작업은 구현이 아니라 실제 enable 판정과 운영 acceptance다.
  - 판정 결과: `보류 유지`
  - 근거: `src/utils/constants.py` 기준 `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED=False`, `DEEPSEEK_RETRY_LIVE_MAX_SLEEP_SEC=0.8`, `DEEPSEEK_RETRY_REPORT_MAX_SLEEP_SEC=4.0` guard는 준비됐고 `src/tests/test_ai_engine_api_config.py`도 상한 계산 자체는 통과한다. 다만 workorder가 요구한 `api_call_lock` 장기 점유 관측, retry 이후 rate-limit/log acceptance, `remote observe-only` vs `remote canary-only` 적용 경로가 실제 운영 메모로 잠기지 않아 same-day enable 승인은 부족하다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - `src/engine/ai_engine_deepseek.py`의 `_compute_retry_sleep()` 및 cap 분기 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[DeepSeekEngineCarry0429-Postclose]`에서 `remote` live-sensitive acceptance와 lock 관찰 필드를 먼저 잠근다.

- [x] `[GeminiSchema0428] Gemini JSON endpoint schema registry 적용 범위 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:05~18:25`, `Track: ScalpingLogic`) (`실행: 2026-04-28 20:10 KST`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md)
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 6개 endpoint를 분리하고, `response_schema` 실패 시 기존 `json.loads/raw regex fallback` 경로로 즉시 복귀할 수 있어야 한다. `system_instruction`/deterministic JSON config flag와 schema registry를 한 change set에서 묶어 global live 전환하지 않는다.
  - why: Gemini는 `main` 실전 기준 엔진이라 범용 `_call_gemini_safe()` 한 줄 변경으로 전 경로를 동시에 바꾸면 BUY/WAIT/DROP 분포와 parse_fail 축이 함께 흔들린다.
  - 판정 결과: `보류`
  - 근거: workorder는 `schema_name` 또는 `response_schema` 인자를 받는 endpoint별 registry를 요구하지만, 현재 `src/engine/ai_engine.py`에는 그런 registry 계층이 없고 `response_schema` 적용 코드도 없다. 따라서 같은날 `main` 엔진에 schema 범위를 잠그거나 실전 승인으로 넘길 준비가 아니다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - `src/engine/ai_engine.py`에서 `response_schema`/`schema_name` 부재 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[GeminiEngineCarry0429-Postclose]`에서 registry 설계 범위와 fallback ownership만 먼저 문서화한다.

- [x] `[GeminiSchema0428] Gemini schema/fallback 테스트 매트릭스 및 관찰 필드 잠금` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:25~18:40`, `Track: ScalpingLogic`) (`실행: 2026-04-28 20:12 KST`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md)
  - 판정 기준: 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` 계약 테스트, `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 영향 관찰 필드를 같이 고정한다. live canary를 검토하려면 `flag default OFF`, `rollback owner`, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 문서에 잠겨 있어야 한다.
  - why: schema는 파싱만 바꾸는 게 아니라 장애 관측 축과 rollback 경계까지 같이 정하지 않으면 `main` live 엔진에서 원인귀속이 흐려진다.
  - 판정 결과: `보류`
  - 근거: 현재 테스트는 `system_instruction/deterministic flag`와 cache 가정까지만 다루고, workorder가 요구한 6개 endpoint 계약 테스트 매트릭스와 `parse_fail / consecutive_failures / ai_disabled / gatekeeper action_label / submitted/full/partial` 관찰 필드 묶음은 같은 문서에 잠겨 있지 않다. 즉 live canary 검토를 열 수준의 테스트 경계가 아직 없다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - workorder의 `endpoint별 response schema registry` 및 `관찰 필드` 요구사항 대조
  - 다음 액션: `2026-04-29 POSTCLOSE` `[GeminiEngineCarry0429-Postclose]`에서 테스트 매트릭스 초안과 관찰 필드 묶음을 문서화할지 먼저 판정한다.

- [x] `[DeepSeekGatekeeper0428] DeepSeek gatekeeper structured-output option 축 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:40~18:55`, `Track: ScalpingLogic`) (`실행: 2026-04-28 20:14 KST`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: `generate_realtime_report()`의 사람용 text report는 유지하고, `evaluate_realtime_gatekeeper()`에만 JSON option 경로를 검토한다. `flag default OFF`, JSON 실패 시 text fallback, `action_label/allow_entry/report/selected_mode/timing` contract 유지 테스트가 없으면 착수하지 않는다.
  - why: DeepSeek는 `remote` 운용 엔진이지만, gatekeeper structured-output은 퍼블릭 contract와 캐시 테스트를 건드려 진입 판단 분포를 바꿀 수 있다.
  - 판정 결과: `미승인`
  - 근거: `src/engine/ai_engine_deepseek.py`는 여전히 `_generate_realtime_report_payload()`를 `generate_realtime_report()`와 `evaluate_realtime_gatekeeper()`가 공유하는 구조이고, structured-output 전용 flag/default-off 경로와 JSON 실패 시 text fallback, `action_label/allow_entry/report/selected_mode/timing` contract 유지 테스트가 별도로 없다. workorder가 요구한 “gatekeeper만 별도 option 경로”가 아직 설계 수준이므로 same-day 실전 축으로 올리면 안 된다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - `src/engine/ai_engine_deepseek.py`의 `generate_realtime_report()` / `evaluate_realtime_gatekeeper()` 공유 경로 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[DeepSeekEngineCarry0429-Postclose]`에서 `flag-off + text fallback + contract test` 설계 메모 준비 여부만 다시 본다.

- [x] `[DeepSeekHolding0428] DeepSeek holding cache bucket 조정 근거 점검` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 18:55~19:10`, `Track: Plan`) (`실행: 2026-04-28 20:16 KST`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: `holding cache miss 증가 -> completed_valid 품질 개선` 근거가 있는지, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 분리 기준에서 gain이 있는지 먼저 확인한다. 근거가 없으면 `_compact_holding_ws_for_cache()` 버킷 축소는 same-day 보류로 닫는다.
  - why: holding cache 세분화는 비용/호출량을 늘릴 수 있지만 기대값 개선이 아직 고정되지 않았다.
  - 판정 결과: `보류 유지`
  - 근거: workorder 기준으로도 `_compact_holding_ws_for_cache()` 세분화는 `holding cohort`의 `completed_valid`, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 개선 근거가 먼저 필요하다. 현재 active 운영축은 entry/soft-stop 쪽이고, holding cache bucket을 줄여도 기대값 개선 근거가 문서/리포트에 없다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py`
    - `src/engine/ai_engine.py`, `src/engine/ai_engine_deepseek.py`의 `_compact_holding_ws_for_cache()` 유지 경로 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[DeepSeekEngineCarry0429-Postclose]`에서 hold/exit cohort 근거가 생기기 전까지 `보류 유지`를 재확인한다.

- [x] `[DeepSeekTooling0428] DeepSeek Tool Calling 필요성/범위 판정` (`Due: 2026-04-28`, `Slot: POSTCLOSE`, `TimeWindow: 19:10~19:20`, `Track: Plan`) (`실행: 2026-04-28 20:18 KST`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - 판정 기준: Tool Calling이 실제로 `JSON parse_fail`, contract drift, 운영 복잡도 감소에 기여하는지 판단하고, 아니면 설계 메모로만 남긴다. SDK/응답 schema/테스트/rollback 구조가 준비되지 않으면 구현 작업으로 승격하지 않는다.
  - why: 현재 Tool Calling은 기능 개선보다 code debt/설계 검토 성격이 강하다.
  - 판정 결과: `backlog 관찰 유지`
  - 근거: workorder 자체가 Tool Calling을 `후순위(code debt)`와 `설계 메모` 범위로만 규정하고 있고, 현재 DeepSeek 경로에는 퍼블릭 응답 schema, fallback, 테스트, rollback 구조가 준비되지 않았다. 기대값 개선 축보다 설계 복잡도가 먼저 커지므로 same-day 구현/승인 작업으로 올릴 이유가 약하다.
  - 테스트/검증:
    - workorder `§1`, `§3-4`, `§5` 재확인
    - 현재 코드베이스에서 Tool Calling 경로 미도입 상태 확인
  - 다음 액션: `2026-04-29 POSTCLOSE` `[DeepSeekEngineCarry0429-Postclose]`에서 backlog 유지 여부만 다시 확인하고, 별도 workorder 초안은 실제 필요성이 생길 때만 연다.
