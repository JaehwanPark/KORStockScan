# 2026-04-29 Stage2 To-Do Checklist

## 오늘 목적

- `latency_quote_fresh_composite` OFF 반영과 restart provenance를 장전 기준으로 확인한다.
- EC2 인스턴스가 `m7g.xlarge`로 상향 완료됐으므로 `runtime basis shift day`로 분리해 CPU/메모리 영향과 전략 효과를 섞지 않는다.
- `ShadowDiff0428`의 두 갈래 원인(`2026-04-28 parquet 미생성`, `2026-04-27 submitted/full/partial mismatch`)을 재검증한다.
- 스캘핑 신규 BUY `initial_entry_qty_cap`은 임시 `2주 cap`으로 완화하고, `initial-only`와 `pyramid-activated`를 계속 분리해 `zero_qty` 왜곡이 줄었는지 본다.
- `씨아이에스(222080)` micro grace 개입 표본의 전일 post-sell 평가는 장전부터 확인하고, 평가가 있으면 `soft_stop_micro_grace_extend` 후보를 장전 기준으로 다시 본다.
- `follow-through failure`는 observe-only backtrace와 스키마 구현 범위만 유지하고 live 축 승격은 보류한다.

## 오늘 강제 규칙

- 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이며 상세 기준은 `Plan Rebase` §1~§6을 따른다.
- live 변경은 동일 단계 내 `1축 canary`만 허용한다. 진입병목축과 보유/청산축은 별개 단계이므로 병렬 canary가 가능하지만, 같은 단계 안에서는 canary 중복을 금지한다.
- 동일 단계 replacement는 `기존 축 OFF -> restart.flag -> 새 축 ON` 순서만 쓴다.
- 손익은 `COMPLETED + valid profit_rate`만 사용하고 `full fill`과 `partial fill`은 분리한다.
- `latency_signal_quality_quote_composite`는 `ShadowDiff` 재검증 전에는 auto-ON 하지 않는다. 단, `2026-04-29 12:21 KST` 사용자 운영 override로 제출 drought 지속 방치가 불허돼 same-day 1축 replacement로 ON 했다가, `12:50 KST` post-restart 효과 미약으로 OFF 했다. 현재 entry live 축은 `mechanical_momentum_latency_relief` 운영 override 1축이며, 이후 판정은 hard baseline이 아니라 post-restart cohort 기준으로 분리한다.
- EC2 인스턴스 상향 직후 하루는 `QuoteFresh`, `latency_state_danger`, `gatekeeper_eval_ms_p95`를 전략 개선이 아니라 `infra basis shift` 후보로 먼저 본다.
- `soft_stop_micro_grace_extend`는 `씨아이에스(222080)` post-sell 평가 확인 전에는 승인하지 않는다.
- 전일 post-sell evaluation 존재 여부만 확인하면 되는 항목은 장후로 넘기지 않고 PREOPEN에서 먼저 닫는다. evaluation이 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤에만 장중/장후로 이관한다.
- `initial_entry_qty_cap` 완화는 `1주 -> 2주` 단일축 조정으로만 본다. same-day에 `pyramid floor`나 추가 포지션 비율 축을 같이 열지 않는다.

## 장전 체크리스트 (08:30~09:00)

- [x] `[VMPerfRebase0429-Preopen] EC2 m7g.xlarge 변경 provenance 및 CPU/메모리 기준선 재확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: RuntimeStability`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `instance type`, `uname -m`, `nproc`, `MemAvailable`, `SwapUsed`, `load average`, main bot PID `/proc/<pid>/environ` 증적을 남기고, 오늘은 `runtime basis shift day`인지 여부를 확정한다.
  - 실행 메모 (`2026-04-28`, 사용자 확인): EC2 인스턴스 변경은 이미 `m7g.xlarge`로 완료됐다.
  - 실행 메모 (`2026-04-29 08:20 KST`): main `bot_main.py` PID는 `7042`, 시작시각은 `2026-04-29 07:56:00 KST`였다. `restart.flag`는 없었고 `/proc/7042/environ`에는 `KORSTOCKSCAN_*` override가 보이지 않아 코드 기본값 경로로 동작 중이다. 런타임 증적은 `uname -m=aarch64`, `nproc=4`, `MemAvailable=11726 MiB`, `SwapUsed=0 MiB`, `load average=0.86/0.83/0.75`였다.
  - 판정 결과: `완료 / runtime basis shift day 유지`
  - why: `t4g.medium -> m7g.xlarge` 변경 완료 직후 첫 거래일은 `QuoteFresh`와 `latency` 계열 baseline을 기존 거래일과 직접 비교하면 infra 효과와 전략 효과가 섞인다.
  - 근거: `aarch64 + 4 vCPU + 15.6 GiB 메모리 + swap unused` 증적이 모두 장전 시점에서 확인됐고, 봇도 `2026-04-29 07:56:00 KST`에 새 PID로 올라와 PREOPEN 범위의 provenance 요건을 충족했다. 오늘 수치는 전략 개선 근거가 아니라 `infra basis shift` 분리표의 기준값으로만 써야 한다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python .*bot_main'`
    - `tr '\0' '\n' < /proc/7042/environ | rg 'KORSTOCKSCAN_|SCALP_|GEMINI|DEEPSEEK'`
    - `uname -m`
    - `nproc`
    - `free -m`
    - `uptime`
  - 다음 액션: 장전에는 변경 여부 재판정이 아니라 provenance/리소스 증적만 남기고, 장중/장후 `QuoteFresh`는 `infra basis shift` 분리표와 함께 본다.

- [x] `[ShadowDiff0429-Preopen] 2026-04-28 parquet/duckdb rebuild 및 shadow diff 재검증` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:42`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/analytics/parquet/pipeline_events/date=2026-04-28`, `post_sell/date=2026-04-28` partition이 생성되고 `submitted/full/partial` diff가 어디까지 줄었는지 확인한다.
  - 실행 메모 (`2026-04-29 08:20~08:21 KST`): `.venv`에서 `build_tuning_monitoring_parquet --dataset pipeline_events --single-date 2026-04-28`와 `--dataset post_sell --single-date 2026-04-28`를 재실행했다. 결과는 `pipeline_events_20260428.parquet=660,682 rows`, `post_sell_20260428.parquet=6 rows`였고 `data/analytics/parquet/pipeline_events/date=2026-04-28`, `post_sell/date=2026-04-28` partition이 모두 생성됐다.
  - 판정 결과: `부분완료 / 2026-04-28 diff 해소, 2026-04-27 historical mismatch 잔존`
  - why: `QuoteFresh` hard baseline은 `ShadowDiff` 미해소 상태에서 다시 승격할 수 없다.
  - 근거: rebuild 후 `compare_tuning_shadow_diff --start 2026-04-28 --end 2026-04-28`는 `all_match=true`로 `submitted=7`, `full_fill=9`, `partial_fill=3`까지 맞았다. 반면 `2026-04-27` 단독 비교는 여전히 `latency_block -3`, `full_fill -9`, `partial_fill -9`가 남아 `2026-04-27~2026-04-28` 합산 `all_match=false`였다. 즉 PREOPEN carry-over의 핵심인 `2026-04-28 parquet 미생성`은 해소됐지만, hard baseline 승격을 막던 historical 잔차는 아직 닫히지 않았다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m src.engine.build_tuning_monitoring_parquet --dataset pipeline_events --single-date 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.build_tuning_monitoring_parquet --dataset post_sell --single-date 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-28 --end 2026-04-28`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-27 --end 2026-04-27`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.compare_tuning_shadow_diff --start 2026-04-27 --end 2026-04-28`
  - 다음 액션: 미해소면 parquet builder/compare query 수정 항목으로 승격하고, 해소면 `QuoteFresh` 기준선 문구를 다시 잠근다.

- [x] `[ShadowDiff0429-PostcloseRootCause] 2026-04-27 historical submitted/fill mismatch 원인분리` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `2026-04-28` parquet 미생성 이슈와 분리된 `2026-04-27 historical` 잔차만 대상으로 `latency_block -3`, `full_fill -9`, `partial_fill -9`의 원인이 `stale parquet`, `builder dedupe`, `compare metric 정의`, `raw stage 품질` 중 어디인지 닫는다.
  - why: PREOPEN 기준선 차단 요인은 같은 이름의 `ShadowDiff`라도 이미 `2026-04-28 freshness`와 `2026-04-27 historical`로 갈라졌다. 이 둘을 다시 합치면 `QuoteFresh` baseline 재승격 판단이 계속 흐려진다.
  - 판정 결과: `완료 / 장후 보정 체크리스트 상세 결과 참조`
  - 근거: 장후 보정 섹션의 동일 ID 항목에서 `2026-04-27` mismatch를 `TEST(123456)` synthetic contamination 중심으로 원인분리했다.
  - 다음 액션: 장후 보정 섹션의 same-day 결과와 익일 `[ShadowDiffSyntheticExclusion0430]` 후속 항목을 기준으로 추적한다.

- [x] `[SoftStopCIS0429-Preopen] 씨아이에스 micro grace post-sell 평가 및 extend 후보 장전 재판정` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:42~08:52`, `Track: Plan`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [analysis/offline_live_canary_bundle/README.md](/home/ubuntu/KORStockScan/analysis/offline_live_canary_bundle/README.md)
  - 판정 기준: `씨아이에스(222080)`의 `post_sell_evaluation`이 생성됐는지 먼저 확인하고, 있으면 `good_cut / whipsaw / ambiguous` 라벨과 `mfe/rebound`를 확인해 `soft_stop_micro_grace_extend` 후보 유지/폐기/보류를 닫는다.
  - 실행 메모 (`2026-04-29 08:19 KST`): `data/post_sell/post_sell_evaluations_2026-04-28.jsonl`에 `씨아이에스(222080)` 평가가 생성돼 있었다. 해당 표본은 `sell_time=12:35:05`, `profit_rate=-1.83%`, `outcome=MISSED_UPSIDE`, `rebound_above_sell=True`, `rebound_above_buy=False`, `metrics_10m.mfe_pct=0.98`, `hit_up_05=True`, `hit_up_10=False`였다.
  - 판정 결과: `완료 / extend 후보 유지, live 승인 보류`
  - why: 이 항목은 전일 `post_sell_evaluation` 확인 작업이므로 장후까지 기다릴 이유가 없다. 오전 거래가 몰리는 날에는 장전 후보 판정이 되어야 보유/청산축 원인귀속이 덜 흔들린다.
  - 근거: `씨아이에스`는 `micro grace` 개입 후에도 실제 청산은 `-1.83%`였지만, 매도가 위로는 10분 내 재상회했고 `+0.5%` 반등도 찍었다. 다만 `buy_price` 회복과 `+1.0%` 반등은 모두 실패해 `good_cut`로는 닫히지 않는다. 즉 기대값 관점에서는 `whipsaw/ambiguous` 쪽 증거가 생겨 `soft_stop_micro_grace_extend` 후보는 유지되지만, single-sample이라 같은 PREOPEN에 곧바로 live ON 할 수준은 아니다.
  - 테스트/검증:
    - `rg -n "222080|씨아이에스|MISSED_UPSIDE|rebound_above_sell|hit_up_05|hit_up_10" data/post_sell/post_sell_evaluations_2026-04-28.jsonl data/post_sell/post_sell_candidates_2026-04-28.jsonl -S`
  - 다음 액션: evaluation이 있으면 장전 판정을 닫고, 없으면 `candidate 존재`, `evaluation 생성 경로`, `막힌 원인`을 남긴 뒤 `12:00` 재확인 또는 장후 이관 여부를 구체적으로 정한다.

- [x] `[QuoteFreshComposite0429-PreopenOff] latency_quote_fresh_composite OFF/restart 반영 확인` (`Due: 2026-04-29`, `Slot: PREOPEN`, `TimeWindow: 08:52~09:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite` OFF 값이 env/runtime provenance(`/proc/<pid>/environ` 또는 동등 증적)와 restart 결과에 실제 반영됐는지 확인한다.
  - 실행 메모 (`2026-04-29 08:20 KST`): 최초 확인 시 main `bot_main.py` PID는 `7042`, 시작시각은 `2026-04-29 07:56:00 KST`였고 `restart.flag`는 존재하지 않았다. `/proc/7042/environ`에는 관련 `KORSTOCKSCAN_*` override가 없었고 코드 기본값 [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174) 도 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=True`라서, `2026-04-28 16:08 KST` OFF 판정이 런타임 설정까지는 내려오지 못한 상태였다.
  - 실행 메모 (`2026-04-29 08:29 KST`): 코드 기본값을 `False`로 내리고 `restart.flag`를 생성한 뒤 우아한 재시작을 수행했다. 이후 `restart.flag`는 소모됐고 새 main PID는 `9267`, 시작시각은 `2026-04-29 08:29:27 KST`였다. `logs/bot_history.log`에는 `08:29:36 KST` 기준 스캐너 재기동과 메인 루프 재진입 로그가 남았다.
  - 판정 결과: `완료 / OFF 반영 및 restart provenance 확보`
  - why: same-day 판정은 `OFF`로 닫혔고, carry-over는 장전 provenance가 있어야만 유효하다.
  - 근거: PREOPEN 범위에서는 same-day `submitted/fill`이 아니라 `OFF 값 + restart 반영`만 보면 된다. 현재는 새 PID `9267`가 `SCALP_LATENCY_QUOTE_FRESH_COMPOSITE_CANARY_ENABLED=False` 기본값을 읽는 코드로 다시 올라왔고, 예비축 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED`도 여전히 `False`라서 동일 단계 replacement 순서를 다시 맞췄다.
  - 테스트/검증:
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python .*bot_main'`
    - `tail -n 80 logs/bot_history.log`
    - `tr '\0' '\n' < /proc/7042/environ | rg 'KORSTOCKSCAN_|SCALP_'`
    - [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:174)
  - 다음 액션: 장중에는 예비축 자동 ON 없이 baseline 관찰만 유지한다. 신규 entry 축 검토는 `[QuoteFreshBackupComposite0429-1220]`에서 `ShadowDiff`와 VM basis shift 판정 이후에만 다시 연다.

## 장중 체크리스트 (09:00~15:20)

- [x] `[EntryBottleneckVmShift0429-1000] VM 변경 후 진입병목 infra basis shift 1차 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 10:00~10:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `gatekeeper_eval_ms_p95`, `latency_state_danger / budget_pass`, `ws_age`, `ws_jitter`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`를 기존 `QuoteFresh` 결과와 분리해 본다.
  - why: 인스턴스 상향 직후 첫 1시간은 전략 canary보다 런타임 처리속도 개선 신호가 먼저 움직일 수 있다.
  - 실행 메모 (`2026-04-29 10:02~10:05 KST`): 표준 경로로 `h1000 (09:00:00~10:00:00)` offline bundle을 다시 생성하고 같은 워크스페이스에서 analyzer를 실행했다. 결과는 `budget_pass=3529`, `submitted=2`, `budget_pass_to_submitted_rate=0.0567%`, `latency_state_danger=2961 (83.9048%)`, `full_fill=1`, `partial_fill=0`, `fallback_regression=0`, `signal_quality_quote_composite_candidate_events=11`이었다. raw 재계산 기준 `gatekeeper_eval_ms_p95=10823.4ms (samples=7)`, `ws_age_ms_p95=655.8`, `ws_jitter_ms_p95=813.4`, `latency_state_danger` subset `ws_age_ms_p95=734.0`, `ws_jitter_ms_p95=823.0`였다.
  - 판정 결과: `완료 / infra-only improvement 후보, baseline reset 불가`
  - 근거: `gatekeeper_eval_ms_p95`는 `15,900ms` guard 아래이고 최근 reference로 써오던 `2026-04-27` `13,238.9ms`보다 낮아져 런타임 처리속도 개선 신호는 보인다. 동시에 `latency_state_danger share`도 `2026-04-28 h1000`의 `1120 / 1223 = 91.6%` 대비 오늘 `83.9%`로 낮아졌다. 그러나 같은 `09:00~10:00` 창의 제출 전환율은 `2026-04-28 h1000` `1 / 1223 = 0.0818%`보다 오늘 `2 / 3529 = 0.0567%`로 더 낮고, `ws_age/ws_jitter p95`도 여전히 `655.8ms / 813.4ms`로 quote freshness residual이 크다. 즉 `p95`와 `danger share` 개선은 보이지만 `submitted/full/partial`이 baseline reset을 말할 만큼 회복했다고 보기는 어렵다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-29 --slot-label h1000 --evidence-cutoff 10:00:00`
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/run_local_canary_bundle_analysis.py --bundle-dir tmp/offline_live_canary_exports/2026-04-29/h1000 --output-dir tmp/offline_live_canary_exports/2026-04-29/h1000/results --since 09:00:00 --until 10:00:00 --label h1000`
    - `tmp/offline_live_canary_exports/2026-04-29/h1000/results/entry_quote_fresh_composite_summary_h1000.json`
    - `tmp/offline_live_canary_exports/2026-04-29/h1000/results/live_canary_combined_summary_h1000.json`
    - `PYTHONPATH=. .venv/bin/python` raw 집계로 `09:00:00~10:00:00` 창 `gatekeeper_eval_ms_p95`, `ws_age_ms_p95`, `ws_jitter_ms_p95`를 재계산했다.
  - 다음 액션: `latency_state_danger`와 `gatekeeper_eval_ms_p95`만 개선되고 `submitted/full/partial`이 안 움직이면 `infra-only improvement`로 분리한다. 오전 거래가 충분히 몰렸으면 `[EntryBottleneckVmShift0429-1200Final]`에서 장후 대기 없이 baseline reset 여부를 닫는다.

- [x] `[EntryBottleneckVmShift0429-1200Final] VM 변경 후 진입병목 infra basis shift 12시 최종확정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:00~12:20`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `09:00~12:00` 또는 12시 full snapshot 기준 `budget_pass`, `submitted`, `budget_pass_to_submitted_rate`, `latency_state_danger share`, `gatekeeper_eval_ms_p95`, `ws_age`, `ws_jitter`, `full_fill`, `partial_fill`, `ShadowDiff`를 보고 `VM 이후 baseline reset`, `infra-only improvement`, `기존 baseline 유지`, `판정유예` 중 하나로 닫는다.
  - why: 오전 거래가 집중되는 구조라면 12시 full snapshot이 `VM basis shift`의 1차 최종판정 창이다. 같은 데이터를 장후까지 기다리면 다음 entry 축 착수가 불필요하게 밀린다.
  - 실행 메모 (`2026-04-29 12:09~12:14 KST`): 표준 경로로 `h1200 (09:00:00~12:00:00)` offline bundle을 생성하고 analyzer를 재실행했다. 결과는 `budget_pass=9040`, `submitted=6`, `budget_pass_to_submitted_rate=0.0664%`, `latency_state_danger=8192 (90.6195%)`, `full_fill_events=21`, `partial_fill_events=18`, `fallback_regression=0`, `signal_quality_quote_composite_candidate_events=11`, `direction_only_reason=submitted_orders<20, baseline<50`였다. raw 재계산 기준 `budget_pass=9041`, `submitted=6`, `latency_state_danger=8193`, `gatekeeper_eval_ms_p95=11096.0ms (samples=17)`, `ws_age_ms_p95=766.0`, `ws_jitter_ms_p95=1009.0`, `danger subset ws_age/ws_jitter p95=811.0/1019.0`였다.
  - 판정 결과: `완료 / infra-only improvement`
  - 근거: `budget_pass_to_submitted_rate=0.0664%`는 `2026-04-28 same-day raw 0.082%`와 `2026-04-27 reference 0.1%` 모두 밑돌아 제출 회복 근거가 없다. 반면 `gatekeeper_eval_ms_p95=11096.0ms`는 `2026-04-27 reference 13238.9ms`보다 낮고, `latency_state_danger share=90.6%`도 `2026-04-28 same-day 96.0%`보다 낮아 런타임 측면 개선 신호는 남는다. 즉 `submitted/full/partial` 동반 회복 없는 `p95/latency_state_danger` 개선이므로 `VM 이후 baseline reset`이 아니라 `infra-only improvement`로 분리하는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/export_server_bundle.py --target-date 2026-04-29 --slot-label h1200 --evidence-cutoff 12:00:00`
    - `PYTHONPATH=. .venv/bin/python analysis/offline_live_canary_bundle/run_local_canary_bundle_analysis.py --bundle-dir tmp/offline_live_canary_exports/2026-04-29/h1200 --output-dir tmp/offline_live_canary_exports/2026-04-29/h1200/results --since 09:00:00 --until 12:00:00 --label h1200`
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/entry_quote_fresh_composite_summary_h1200.json`
    - `PYTHONPATH=. .venv/bin/python` raw 집계로 `09:00:00~12:00:00` 창 `budget_pass/submitted/latency_state_danger/gatekeeper_eval_ms_p95/ws_age/ws_jitter` 재확인
  - 다음 액션: entry 단계는 계속 live 축 공백 상태로 두고, 예비축 검토는 `[QuoteFreshBackupComposite0429-1220]`에서 data-quality gate와 replacement 절차 기준으로만 다시 닫는다.

## 장중 설계/후속 체크리스트 (12:20~14:20)

- [x] `[QuoteFreshBackupComposite0429-1220] latency_signal_quality_quote_composite 활성화 조건 12시 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:20~12:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `latency_quote_fresh_composite OFF/restart` 반영, `ShadowDiff` 재검증, `[EntryBottleneckVmShift0429-1200Final]`의 VM basis shift 판정을 확인한 뒤에만 예비축 ON 가능 여부를 닫는다.
  - why: 예비축 활성화 조건은 12시 VM/baseline 판정 이후 바로 판단 가능하다. 장후까지 기다리면 다음 entry 축 착수가 밀린다.
  - 실행 메모 (`2026-04-29 10:08 KST`): `09:00~10:00` 창 제출전환율이 `0.0567% (2/3529)`로 여전히 낮아 same-slot 조기 replacement 가능성을 다시 검토했다. 그러나 오늘 강제 규칙은 `latency_signal_quality_quote_composite`를 `ShadowDiff` 재검증 전 auto-ON 금지로 잠그고 있고, `h1000` summary도 `submitted_orders<20`, `baseline<50`, `signal_quality_quote_composite_candidate_events=11`만 보여줄 뿐 실제 recovery evidence는 아직 부족하다.
  - 조기판정 메모: `지금 즉시 ON 보류`
  - 근거: 오늘은 `runtime basis shift day`라 `gatekeeper_eval_ms_p95`와 `latency_state_danger share` 개선이 infra 효과인지 전략 효과인지 `12:00` 누적창에서 먼저 분리해야 한다. 또한 `2026-04-27 historical ShadowDiff` 잔차가 남아 있어 hard baseline 승격도 아직 불가하다. 따라서 `10시 전환율 미회복`만으로 예비축을 즉시 여는 것은 same-day replacement 승인 절차와 data-quality gate를 동시에 건너뛰는 셈이다.
  - 실행 메모 (`2026-04-29 12:14 KST`): `QuoteFresh OFF/restart provenance`는 이미 장전에 확보됐고, `h1200` summary에서도 `submitted_orders=6`, `budget_pass_to_submitted_rate=0.0664%`, `signal_quality_quote_composite_candidate_events=11`, `direction_only_reason=submitted_orders<20, baseline<50`였다. same-day `ShadowDiff`는 available 상태지만 historical `2026-04-27` 잔차는 여전히 남아 있다.
  - 판정 결과: `완료 / 운영 override로 ON 승인`
  - 근거: `[EntryBottleneckVmShift0429-1200Final]`이 `infra-only improvement`로 닫혀 전략 recovery 증거가 없고, 예비축 후보 이벤트도 `11건`에 그쳐 문서 기준으로는 미승인이었다. 그러나 사용자 운영판정에서 `BUY 신호 대비 submitted 급감`, `보유청산 튜닝 표본 고갈`, `진입병목 형상 유지 불허`가 명시돼, hard baseline 승격이 아니라 EV/거래수 회복을 우선하는 운영 override로 재판정했다. 동일 entry 단계의 기존 축 `latency_quote_fresh_composite`는 이미 OFF + restart 완료 상태이므로 same-day 1축 replacement 원칙은 유지한다.
  - 실행 메모 (`2026-04-29 12:21 KST`): [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:182)에서 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True`로 전환하고 `restart.flag`를 생성했다. `restart.flag`는 소모됐고 main PID는 `9267 -> 30566`, 새 PID 시작시각은 `2026-04-29 12:21:28 KST`였다. threshold는 기존 예비축 정의 그대로 `signal>=90`, `latest_strength>=110`, `buy_pressure_10t>=65`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`다.
  - 테스트/검증:
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/entry_quote_fresh_composite_summary_h1200.json`
    - `tmp/offline_live_canary_exports/2026-04-29/h1200/results/live_canary_combined_summary_h1200.json`
    - PREOPEN provenance: main PID `9267`, `latency_quote_fresh_composite OFF + restart.flag 소모`
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "signal_quality_quote_composite"`
  - 다음 액션: `restart.flag`로 새 PID를 확인하고, 이후 cohort에서는 `latency_signal_quality_quote_composite_normal_override`, `signal_quality_quote_composite_canary_applied`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 분리한다. post-restart `budget_pass >= 150`인데 `submitted <= 2`면 축 효과 미약으로 장후 rollback 검토를 연다.

- [x] `[InitialQtyCap0429-1235] 스캘핑 신규 BUY 2주 cap 완화 후 initial/pyramid 12시 1차 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:35~12:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `initial_entry_qty_cap_applied cap_qty=2` runtime 증적, `initial-only` vs `pyramid-activated` 표본, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 분리해 본다.
  - why: 오전 거래가 몰리면 12시까지 cap 완화가 `PYRAMID zero_qty` 왜곡을 줄였는지 1차 방향성은 볼 수 있다. full-day 손익 확정은 장후까지 기다릴 수 있지만, 구조적 zero_qty 여부는 장중에도 판단 가능하다.
  - 실행 메모 (`2026-04-29 12:18~12:21 KST`): raw `pipeline_events_2026-04-29.jsonl` 기준 `09:00~12:00` 창 `initial_entry_qty_cap_applied(cap_qty=2, applied=True)=6 events / 5 records`였다. 대상은 `올릭스(226950)`, `덕산하이메탈(077360, 2회)`, `비츠로테크(042370)`, `삼표시멘트(038500)`, `대한전선(001440)`였다. 같은 창에서 `pyramid_activated=0`, `ADD_BLOCKED reason=zero_qty=0`였고, cap cohort completed-valid는 `올릭스 -1.57`, `덕산하이메탈 -1.50`, `삼표시멘트 +0.65` 3건이었다.
  - 판정 결과: `완료 / 방향성 유지, 장후 보정 이관`
  - 근거: `2주 cap` runtime 증적은 충분하고 `zero_qty`가 오전 창에 0건이라 최소한 `1주 cap -> zero_qty 왜곡` 완화 방향은 맞다. 다만 `pyramid_activated`가 아직 0건이라 `initial-only`와 `pyramid-activated` 분리효과를 hard하게 닫을 표본은 없다. `completed_valid_avg_profit_rate`도 cap cohort 3건 평균 `-0.8067%`로 EV 개선을 말할 단계가 아니므로, 12시에는 `유지 방향성만 확인`하고 장후 보정으로 넘기는 것이 맞다.
  - 테스트/검증:
    - `rg -n '\"stage\": \"initial_entry_qty_cap_applied\"|\"stage\": \"pyramid_activated\"|\"stage\": \"add_blocked\"' data/pipeline_events/pipeline_events_2026-04-29.jsonl`
    - `PYTHONPATH=. .venv/bin/python` raw cohort 집계로 `cap_qty=2`, `pyramid_activated`, `zero_qty`, `completed_valid profit_rate` 확인
  - 다음 액션: `[InitialQtyCap0429-PostcloseFallback]`에서 full-day 기준으로 `initial-only` vs `pyramid-activated`, `zero_qty`, `COMPLETED + valid profit_rate`를 다시 닫는다. same-day에 `pyramid floor`나 cap 추가 완화는 열지 않는다.

- [x] `[FollowThroughSchema0429-1250] follow-through observe-only 스키마 구현 범위 재판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:50~13:05`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `체결 후 30초/1분/3분 가격`, `AI velocity`, `MFE/MAE`, `호가/직전 거래량`, `시장/섹터 동조성` 중 어디까지를 `post_sell/snapshot`로 먼저 넣을지 구현 범위를 닫는다.
  - why: 이 항목은 전일 월간 backfill과 기존 후보 3건 기반의 observe-only 설계 범위다. 당일 종가가 필요하지 않으므로 장후까지 미룰 이유가 없다.
  - 실행 메모 (`2026-04-29 12:24 KST`): `2026-04-28` carry-over 문맥과 `tmp/monthly_backfill/april_follow_through_backfill_through_0428.{md,json}`를 다시 확인했다. 월간 lightweight backfill 기준 `valid_completed_trades=237`, `soft_stop_rows=64`, `follow_through_failure candidate_count=3`였고, 전일 checklist는 이미 `체결 후 30초/1분/3분 가격`, `AI score velocity`, `MFE/MAE`, `체결 시점 호가 잔량 비율`, `직전 거래량`, `시장/섹터 동조성`을 observe-only 후보 필드로 고정해 둔 상태였다.
  - 판정 결과: `완료 / observe-only 스키마 범위 고정, live 승격 보류`
  - 근거: 월간 후보가 `3건`뿐이라 `follow-through failure`는 아직 live 축이 아니라 observe-only backtrace가 먼저다. 따라서 구현 범위는 전일 잠근 6개 필드로 유지하고, 저장 우선순위도 `post_sell + snapshot 우선, raw pipeline 보강 후순위`로 고정하는 것이 맞다. 표본 1건 또는 same-day 사례만으로 정책 변경 근거로 쓰지 않는다는 guard도 그대로 유지한다.
  - 테스트/검증:
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.md`
    - `tmp/monthly_backfill/april_follow_through_backfill_through_0428.json`
    - [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md:357)
    - [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md:370)
  - 다음 액션: 다음 구현 change set에서는 `post_sell/snapshot` 스키마 보강만 올리고, `follow-through failure` live 후보 재판정은 표본 `20건` 도달 전까지 열지 않는다.

- [x] `[SignalQualityQuoteComposite0429-PostRestart] latency_signal_quality_quote_composite 운영 override 후 post-restart cohort 1차 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:05~13:25`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `restart.flag` 이후 새 PID 기준 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=True` 로드 여부, `latency_signal_quality_quote_composite_normal_override`, `signal_quality_quote_composite_canary_applied`, `submitted`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 확인한다.
  - why: 이번 ON은 hard baseline 승격이 아니라 사용자 운영 override다. 따라서 기존 `h1200` baseline과 합치지 말고 post-restart cohort만 분리해 기대값/거래수 회복 여부를 봐야 한다.
  - 실행 메모 (`2026-04-29 12:45~12:50 KST`): `12:21:28~12:45:59` post-restart cohort raw 기준 `budget_pass=972`, `latency_block=972`, `submitted=0`이었다. `latency_block` 사유는 `latency_state_danger=846`, `latency_fallback_deprecated=126`이고, canary 사유는 `low_signal=770`, `quote_stale=76`으로 `signal_quality_quote_composite` 통과 후보가 0건이었다.
  - 판정 결과: `완료 / 효과 미약, 운영 override 종료`
  - 근거: 이 축은 `signal>=90` 전제라 AI score 50/70 mechanical fallback 상태의 대량 `budget_pass`를 열 수 없다. 실제 post-restart 후보도 0건이므로 제출 drought를 풀 가능성이 낮다. 사용자 운영판정에 따라 동일 entry 단계 복합축을 모두 닫고 새 1축으로 교체한다.
  - rollback guard: post-restart `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 장후 rollback 검토를 연다. `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` raw 집계로 `12:21:28~12:45:59` `budget_pass/submitted/latency_block/canary_reason` 확인
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "signal_quality_quote_composite"`
  - 다음 액션: `latency_signal_quality_quote_composite`를 OFF하고 `mechanical_momentum_latency_relief`를 ON한 뒤 restart provenance와 새 cohort를 분리한다.

- [x] `[MechanicalMomentumLatencyRelief0429-Now] mechanical_momentum_latency_relief 운영 override 즉시 ON` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 12:50~13:05`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: 동일 entry 단계의 기존 복합축 `latency_quote_fresh_composite=False`, `latency_signal_quality_quote_composite=False`를 확인하고 `SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=True`로 새 1축만 켠다. 조건은 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `quote_stale=False`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`다.
  - why: post-restart `latency_signal_quality_quote_composite`는 `budget_pass=972`에서도 후보 0건이라 운영상 제출 회복 가능성이 낮다. 반면 같은 창 counterfactual로 `mechanical_momentum_latency_relief` 후보는 약 91건이며, AI score 50/70 mechanical fallback 상태라도 수급/강도와 quote freshness가 맞는 후보만 제한적으로 연다.
  - 판정 결과: `완료 / 운영 override로 ON 승인`
  - 실행 메모 (`2026-04-29 12:50 KST`): [src/utils/constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:182) 기준 `SCALP_LATENCY_SIGNAL_QUALITY_QUOTE_COMPOSITE_CANARY_ENABLED=False`, `SCALP_LATENCY_MECHANICAL_MOMENTUM_RELIEF_CANARY_ENABLED=True`로 교체했다. [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:365)에 새 canary 조건과 `latency_mechanical_momentum_relief_normal_override` 경로를 추가했다.
  - 실행 메모 (`2026-04-29 12:57 KST`): `restart.flag`를 생성해 우아한 재시작을 수행했다. `restart.flag`는 소모됐고 main PID는 `30566 -> 35539`, 새 PID 시작시각은 `2026-04-29 12:57:02 KST`였다. `logs/bot_history.log`에는 `12:57:14 KST` 웹소켓 연결/로그인/조건식 초기화 로그가 남았다.
  - rollback guard: 새 restart 이후 `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약으로 장후 rollback 검토를 연다. `pre_submit_price_guard_block_rate > 2.0%`, `fallback_regression > 0`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 합산 손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%`이면 즉시 OFF 후보로 본다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_sniper_entry_latency.py -k "mechanical_momentum or signal_quality_quote_composite"`
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_sniper_entry_latency.py src/tests/test_sniper_scale_in.py` -> `102 passed`
    - `PYTHONPATH=. .venv/bin/python` import check로 `quote_fresh=False`, `signal_quality=False`, `mechanical_momentum=True` 확인
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500` -> parser count `46`, `2026-04-29` checklist task `11`, `2026-04-30` checklist task `5`
  - 다음 액션: 이후 cohort에서는 `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted/full/partial`, `COMPLETED + valid profit_rate`, `fallback_regression=0`를 분리한다.

- [x] `[MechanicalMomentumPriceGuard0429-1315] mechanical_momentum target cap 저가제출 반복실패 hotfix` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:10~13:25`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `mechanical_momentum_latency_relief` 경로에서 `target_buy_price`가 현재 `best_bid` 대비 `pre_submit guard` 임계값보다 과도하게 낮으면 `reference_target_cap`을 실주문가로 쓰지 않고 `latency_guarded_order_price`를 유지한다. 수정 후 동일 클래스 케이스가 `pre_submit_price_guard_block` 반복 대신 `order_leg_request/order_leg_sent` 또는 정상 `latency_block`으로 갈려야 한다.
  - why: `삼화전기(009470)` 같은 same-day 표본에서 `latency_pass`까지 통과한 뒤 `submitted_order_price=48800`, `best_bid_at_submit=49850`, `price_below_bid_bps=211`, `resolution_reason=reference_target_cap`로 제출 직전 차단이 반복됐다. 이 상태를 두면 entry canary 성과평가 전에 주문실패 로그만 누적된다.
  - 실행 메모 (`2026-04-29 13:13 KST`): [src/engine/sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py:50)에 `target_buy_price`가 `SCALPING_PRE_SUBMIT_MAX_BELOW_BID_BPS`를 넘는지 사전 확인하는 helper를 추가했다. `counterfactual_order_price_1tick`에는 기존 `target_cap`을 계속 남기되, 실주문 `order_price`는 guard 범위 안일 때만 cap을 적용하게 바꿨다.
  - 판정 결과: `완료 / 저가제출 반복실패 hotfix 반영`
  - 근거: `나노신소재(121600)`처럼 `price_below_bid_bps=79`인 케이스는 동일 경로에서도 실주문이 나갔고, `삼화전기`는 `211bps`라서 guard와 주문가 로직이 충돌했다. 이번 수정은 guard 자체를 완화한 것이 아니라, 실주문가가 guard에 즉시 막힐 가격으로 내려가는 내부 충돌만 제거한 것이다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_sniper_entry_latency.py src/tests/test_sniper_scale_in.py` -> `102 passed`
    - [src/tests/test_sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_entry_latency.py:732) 대한전선 target-cap 회귀 테스트에서 `counterfactual=48800`, `order_price=50400` 확인
  - 다음 액션: 런타임 반영을 위해 재시작 후 `pre_submit_price_guard_block`, `order_bundle_failed`, `resolution_reason=reference_target_cap` 빈도를 post-restart cohort로 다시 본다.

- [x] `[MechanicalMomentumLatencyRelief0429-1400] mechanical_momentum_latency_relief 14시 submitted 점검` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:15`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `12:57 restart` 이후 `14:00` 기준 post-restart cohort에서 `budget_pass`, `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full_fill`, `partial_fill`, `pre_submit_price_guard_block`, `order_bundle_failed`, `fallback_regression=0`, `COMPLETED + valid profit_rate`를 분리 확인한다.
  - why: 현재 entry live 축은 `mechanical_momentum_latency_relief` 1축뿐이라 `submitted`가 실제로 회복되는지 same-day에 다시 보지 않으면 운영 override 유지/종료 판단이 늦어진다. 특히 `13:15` hotfix 이후에는 `저가제출 guard 충돌`과 `순수 latency drought`를 다시 분리해야 한다.
  - 실행 메모 (`2026-04-29 14:00 KST 기준, 사후집계`): `12:57:02 restart -> 14:00:00` 창 원시 event 기준 `budget_pass=1959`, `mechanical override event=105`, `submitted=21`, `pre_submit_price_guard_block=84`, `order_bundle_failed=84`였고, 고유 `record_id` 기준으로는 `budget_pass_unique=38`, `mechanical_unique=22`, `submitted_unique=20`, `guard_block_unique=2`, `order_failed_unique=2`, `filled_unique=7`이었다. `13:15 hotfix -> 14:00` 창으로 다시 자르면 `budget_pass_unique=32`, `mechanical_unique=18`, `submitted_unique=17`, `guard_block_unique=1`, `order_failed_unique=1`, `filled_unique=7`이었다.
  - 판정 결과: `완료 / submitted 회복 확인, 다만 hotfix 직후 삼화전기 단일 guard 충돌 잔존`
  - 근거: `budget_pass >= 150`인데 `submitted <= 2`면 효과 미약이라는 rollback guard 기준에 비춰 보면, post-restart 고유 기준 `submitted_unique=20`, hotfix 이후에도 `submitted_unique=17`이라 제출 drought 자체는 해소됐다. 체결도 `SK스퀘어`, `삼화콘덴서`, `코오롱`, `지앤비에스 에코`, `큐리옥스바이오시스템즈`, `HD현대`, `제룡전기`까지 `FULL_FILL 7건`이 확인됐다. 남은 실패는 `LS머트리얼즈`(restart 직후)와 `삼화전기`(hotfix 이후)처럼 `resolution_reason=reference_target_cap`가 guard와 충돌한 단일 가격결정 문제였다. `ALLOW_FALLBACK` 또는 `fallback bundle` 제출은 보이지 않았고, 관찰된 fallback 관련 로그는 `latency_fallback_deprecated` 차단뿐이라 `fallback_regression=0`으로 본다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `data/pipeline_events/pipeline_events_2026-04-29.jsonl` 집계 (`12:57 restart -> 14:00`, `13:15 hotfix -> 14:00`)
    - `rg -n "pre_submit_price_guard_block|order_bundle_failed" data/pipeline_events/pipeline_events_2026-04-29.jsonl`
    - `rg -n "ALLOW_FALLBACK|fallback_bundle|entry_mode=fallback|latency_fallback" data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: 이 항목은 `제출 회복 yes / 가격결정 충돌 잔존`으로 닫고, 후속은 `DynamicEntryPriceP0Guard0430-*`에서 `pre_submit_price_guard_block` 단일 잔차를 추적한다. hold/exit 평가는 `제룡전기`, `지앤비에스 에코`, `코오롱` 등 same-day filled cohort를 사용한다.

- [x] `[SKInnovationHoldingSync0429-Now] SK이노베이션(096770) HTS 보유 vs 런타임 보유감시 동기화 상태 확인` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 15:00~15:20`, `Track: RuntimeStability`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `HTS 보유`가 현재 `RecommendationHistory.status`, `DB.get_active_targets`, `BROKER_RECOVER`, `HOLDING_PIPELINE`, `bot_main PID` 증적과 일치하는지 보고 `재시작 필요` 여부를 닫는다.
  - why: HTS에는 보유가 있는데 런타임 모니터링에 안 보이면 보유/청산 EV를 방치하게 된다. 다만 장중 재시작은 단절 리스크가 있으므로, 먼저 `미동기화`인지 `가시성 부족`인지 분리해야 한다.
  - 실행 메모 (`2026-04-29 15:06 KST`): main 봇 PID는 `37672`, 시작시각은 `2026-04-29 13:15:26 KST`였다. `13:28:19`에 `WS 실제체결 096770 BUY 2주 @ 142100원 (주문번호 0065464)`가 들어왔지만 당시에는 `[EXEC_IGNORED] no matching active order`로 영수증 바인딩이 누락됐다. 이후 `13:29:24` 정기 계좌동기화에서 `🔄 [BROKER_RECOVER] SK이노베이션(096770) -> HOLDING (qty=2, buy_price=142100, strategy=SCALPING, legacy=False, exec_verified=False, order_ref_verified=False)`가 찍혔다. DB 조회 결과 `id=4196 status=HOLDING buy_price=142100 buy_qty=2 strategy=SCALPING`가 살아 있었고, `13:55:29`에는 `[HOLDING_PIPELINE] ... stage=scalp_preset_tp_ai_hold_action` 이벤트가 확인돼 보유 파이프라인도 실행됐다. 이후 사용자가 `거래 중 단절 리스크`를 이유로 HTS에서 수동 매도를 집행했다. 최신 로그에서는 `15:06:28` `WS 실제체결 096770 SELL 2주 @ 148400원 (주문번호 0081196)`가 다시 `[EXEC_IGNORED]`로 찍혔고, `15:06:56` 정기 동기화가 `잔고 없음 -> COMPLETED 강제 전환`으로 마무리했다. 실체결 기준 수익률은 gross `+4.43%`, 비용 반영 net `+4.19%`였다.
  - 판정 결과: `완료 / 동기화는 복구됐지만 종료는 사용자 수동 매도, 실현 net +4.19%(≈+4.2%), 즉시 재시작 불필요`
  - 근거: 현재형 문제는 `HTS 보유 미편입`이 아니라 `매수·매도 모두에서 WS 체결 영수증 active-order binding 누락 -> 90초 정기 계좌동기화가 상태를 교정`하는 구조였다. 중간에는 `BROKER_RECOVER -> HOLDING -> HOLDING_PIPELINE`까지 복구가 됐지만, 종료는 봇 자율청산이 아니라 사용자의 수동 매도 이후 `SELL 체결 -> COMPLETED 강제 전환`으로 닫혔다. 실계좌 체결가 `142100 -> 148400 (2주)` 기준으로 DB `sell_price/profit_rate`도 `148400 / +4.19%`로 보정했다. 즉 지금 재시작해도 얻는 복구 이득이 없고, 남은 핵심은 `실시간 체결 영수증 바인딩 경로` 보강이다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python - <<'PY' ... RecommendationHistory / DB.get_active_targets()에서 096770 조회 ... PY`
    - `rg -n "096770|SK이노베이션|BROKER_RECOVER|scalp_preset_tp_ai_hold_action|EXEC_IGNORED" logs/bot_history.log logs/sniper_sync_info.log logs/pipeline_event_logger_info.log* logs/sniper_execution_receipts_info.log`
    - `ps -eo pid,lstart,cmd | rg 'bot_main.py|python.*bot_main'`
  - 다음 액션: 장후에는 `ORDER_NOTICE_BOUND -> WS 실제체결 -> active order binding` 경로를 매수/매도 양쪽으로 분리해 follow-up에 올리고, `bot_history` 보유감시 가시성 부족은 부차 이슈로 둔다. 재현되기 전까지는 `restart.flag` 재시작보다 order-binding 경로 보강을 우선한다.

- [x] `[GeminiEngineCarry0429-1305] Gemini P1/P2 live 승인 전제와 schema 매트릭스 carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:05~13:20`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`의 `flag default OFF` 유지 여부, `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`, parse_fail/consecutive_failures/ai_disabled 관찰 메모, 그리고 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` schema/fallback 테스트 매트릭스 초안이 같은 문서에 잠겼는지 본다.
  - 실전 enable acceptance 정의:
    - `flag default OFF`와 rollback owner가 문서/코드에 함께 잠겨 있다.
    - `baseline cohort / candidate live cohort / observe-only cohort / excluded cohort`가 명시돼 있다.
    - `parse_fail`, `consecutive_failures`, `ai_disabled`, `gatekeeper action_label`, `submitted/full/partial` 관찰 필드가 고정돼 있다.
    - 최소 `entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5` endpoint별 fallback/test matrix 초안이 있다.
    - 위 4개 중 1개라도 비면 `실전 enable 미승인`으로 본다.
  - why: 이 항목은 엔진 설계/acceptance 정리라 종가 데이터가 필요하지 않다. 12시 운영 판정 후 바로 정리해도 된다.
  - 산출물: `Gemini enable acceptance 메모 1건`, `6 endpoint schema/fallback/test matrix 초안 1건`, `다음 change set 범위(main observe-only vs canary-only) 1건`
  - 실행 메모 (`2026-04-29 13:32 KST`): [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-enable-acceptance-spec.md)를 작성해 `main` Gemini live 변경 범위를 다시 잠갔다. [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1193) 기준 `GEMINI_SYSTEM_INSTRUCTION_JSON_ENABLED`, `GEMINI_JSON_DETERMINISTIC_CONFIG_ENABLED`는 이미 `require_json=True` 경로에서만 분기하지만, `response_schema` registry ingress와 endpoint별 fallback/test 묶음은 아직 코드/테스트에 없다.
  - 판정 결과: `완료 / P1은 flag-off observe-only 승인, P2 schema registry는 실전 미승인`
  - 근거: Gemini는 `main` 실전 엔진이라 P1/P2를 같은 날 live change로 열면 BUY/WAIT/DROP, HOLD/TRIM/EXIT, condition/eod 분포와 parse_fail 축이 동시에 흔들린다. 현재는 6 endpoint (`entry/holding_exit/overnight/condition_entry/condition_exit/eod_top5`)별 schema ingress, fallback owner, contract test matrix가 같은 change set으로 잠기지 않아 실전 enable acceptance를 충족하지 못한다.
  - 테스트/검증:
    - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:1186)
    - [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py:114)
    - [test_gemini_live_prompt_smoke.py](/home/ubuntu/KORStockScan/src/tests/test_gemini_live_prompt_smoke.py:271)
  - 다음 액션: `2026-04-30`에는 live enable이 아니라 `flag-off schema ingress + contract matrix` 구현 범위만 고정한다.

- [x] `[GeminiSchemaBuild0429-1320] Gemini 6 endpoint schema registry/fallback/test matrix 초안 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:20~13:45`, `Track: ScalpingLogic`)
  - Source: [workorder_gemini_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_gemini_engine_review.md)
  - Owner: `Codex`
  - 결과서: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md)
  - 판정 기준: `entry_v1`, `holding_exit_v1`, `overnight_v1`, `condition_entry_v1`, `condition_exit_v1`, `eod_top5_v1` 각각에 대해 `schema scope`, `fallback path`, `required tests`, `observe fields`, `rollback point`가 표 형태로 초안화된다.
  - why: “없어서 보류”를 반복하지 않으려면 schema registry의 실제 설계 산출물을 먼저 만들어야 하며, 이 작업은 장후 데이터가 필요하지 않다.
  - 실행 메모 (`2026-04-29 13:36 KST`): [2026-04-29-gemini-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-enable-acceptance-spec.md)에 6 endpoint matrix를 추가했다. `entry/watch`, `holding/exit`, `overnight`, `condition_entry`, `condition_exit`, `eod_top5` 각각에 대해 `next schema name`, `fallback owner`, `required tests`, `status=observe-only`를 표로 고정했다.
  - 실행 메모 (`2026-04-29 14:10 KST`): [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:28)에 `GEMINI_RESPONSE_SCHEMA_REGISTRY`, [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:326)에 `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED=False`, `_call_gemini_safe(schema_name=...)` 인입점을 추가했다. 6 endpoint 호출부에는 `schema_name`을 연결했지만 flag 기본값이 OFF라 live 응답 분포는 바꾸지 않는다.
  - 판정 결과: `완료 / flag-off schema registry 묶음 반영`
  - 근거: 현재 묶음은 실전 enable이 아니라 `main` Gemini의 endpoint별 response schema를 켤 수 있는 인입점과 fallback 유지 테스트를 만든 것이다. `GEMINI_RESPONSE_SCHEMA_REGISTRY_ENABLED`를 켜기 전까지는 기존 `json.loads -> regex fallback` 동작이 유지된다.
  - 테스트/검증:
    - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:430)
    - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2023)
    - [ai_engine.py](/home/ubuntu/KORStockScan/src/engine/ai_engine.py:2165)
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py` -> `23 passed`
  - 다음 액션: `2026-04-30`에는 구현 범위 확정이 아니라 `flag-off schema registry load/contract 관찰`만 확인한다.

- [x] `[DeepSeekEngineCarry0429-1345] DeepSeek P1/P2/P3 acceptance/backlog carry-over 판정` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 13:45~14:00`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - Owner: `Codex`
  - 판정 기준: `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED`의 `remote` live-sensitive acceptance(`api_call_lock`, rate-limit/log acceptance, observe-only/canary-only 경로), gatekeeper structured-output의 `flag-off + text fallback + contract test`, holding cache bucket 축소의 EV 근거, Tool Calling backlog 유지 여부를 한 묶음으로 확인한다.
  - 실전 enable acceptance 정의:
    - backoff 축: `live-sensitive cap <= 0.8s`, `report/eod cap`, `api_call_lock` worst-case, retry 후 rate-limit/log acceptance가 문서에 잠겨 있다.
    - gatekeeper structured-output 축: `flag default OFF`, text fallback, `action_label/allow_entry/report/selected_mode/timing` contract test가 있다.
    - holding cache 축: `completed_valid`, `partial/full`, `initial/pyramid`, `missed_upside`, `exit quality` 기준의 EV 근거가 있다.
    - Tool Calling 축: 퍼블릭 schema/fallback/테스트/rollback 구조가 없으면 구현 승격 금지다.
    - 위 조건이 안 맞으면 `remote 실전 enable 미승인` 또는 `backlog 유지`로 닫는다.
  - why: 04-28 판정 기준 DeepSeek 잔여축은 전부 실전 acceptance 또는 설계/backlog 범위이고, 장후 데이터가 필요한 항목이 아니다.
  - 산출물: `DeepSeek enable acceptance 메모 1건`, `backoff acceptance 표 1건`, `gatekeeper structured-output 설계 전제 1건`, `holding cache/Tool Calling backlog 결론 1건`
  - 실행 메모 (`2026-04-29 13:42 KST`): [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-deepseek-enable-acceptance-spec.md)를 작성해 `context-aware backoff`, `gatekeeper structured-output`, `holding cache`, `Tool Calling`의 carry-over 결론을 고정했다. [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:534) 기준 P1 guard는 준비돼 있지만 `api_call_lock` 관찰과 retry acceptance 메모가 아직 없다.
  - 판정 결과: `완료 / P1은 flag-off 운영 승인 유지, P2/P3는 backlog 유지`
  - 근거: DeepSeek는 `remote` 경로라 same-day live-sensitive sleep 증가가 곧 미진입 기회비용이 된다. gatekeeper structured-output은 shared text report 경로를 같이 건드리므로 `flag-off + text fallback + contract test` 없이는 승격할 수 없고, holding cache/Tool Calling도 EV 근거보다 설계 복잡도가 먼저 크다.
  - 테스트/검증:
    - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:534)
    - [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:1511)
    - [test_ai_engine_cache.py](/home/ubuntu/KORStockScan/src/tests/test_ai_engine_cache.py:206)
  - 다음 액션: `2026-04-30`에는 remote enable이 아니라 `lock_wait/retry acceptance` 관찰필드와 `gatekeeper option path` 설계만 구현 대상으로 둔다.

- [x] `[DeepSeekAcceptanceBuild0429-1400] DeepSeek 실전 enable acceptance/spec 메모 작성` (`Due: 2026-04-29`, `Slot: INTRADAY`, `TimeWindow: 14:00~14:20`, `Track: Plan`)
  - Source: [workorder_deepseek_engine_review.md](/home/ubuntu/KORStockScan/docs/archive/workorders/workorder_deepseek_engine_review.md)
  - Owner: `Codex`
  - 결과서: [2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-gemini-deepseek-acceptance-bundle-result-report.md)
  - 판정 기준: `context-aware backoff`, `gatekeeper structured-output`, `holding cache`, `Tool Calling` 각각에 대해 `enable acceptance`, `not now reason`, `required proof`, `next implementation slot`이 문서화된다.
  - why: DeepSeek 잔여축은 코드보다 운영 acceptance가 먼저라, 설계/승인 메모를 장후까지 미루지 않고 고정해야 더 이상 공회전하지 않는다.
  - 실행 메모 (`2026-04-29 13:47 KST`): acceptance spec 문서에 `axis / enable acceptance / not now reason / required proof / next slot` 표를 작성했다. `context-aware backoff`와 `gatekeeper structured-output`은 `2026-04-30 POSTCLOSE` 설계 슬롯으로, `holding cache bucket reduction`과 `Tool Calling`은 backlog 유지로 분리했다.
  - 실행 메모 (`2026-04-29 14:10 KST`): [ai_engine_deepseek.py](/home/ubuntu/KORStockScan/src/engine/ai_engine_deepseek.py:545)에 `_build_retry_acceptance_snapshot()`을 추가하고, retry 로그에 `context_aware_backoff_enabled`, `live_sensitive`, `max_sleep_sec`, `lock_scope=api_call_lock`가 함께 남도록 묶었다.
  - 판정 결과: `완료 / acceptance spec + retry 관찰 묶음 반영`
  - 근거: 이번 산출물은 same-day 실전 승격이 아니라, enable 전에 확인해야 할 관찰필드를 코드 로그와 테스트로 고정한 것이다. `DEEPSEEK_CONTEXT_AWARE_BACKOFF_ENABLED` 기본값은 여전히 OFF라 remote sleep 정책은 바뀌지 않는다.
  - 테스트/검증:
    - [2026-04-29-deepseek-enable-acceptance-spec.md](/home/ubuntu/KORStockScan/docs/ai-acceptance/2026-04-29-deepseek-enable-acceptance-spec.md)
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_ai_engine_api_config.py src/tests/test_ai_engine_cache.py` -> `23 passed`
  - 다음 액션: `2026-04-30`에는 구현/비구현 배치가 아니라 retry acceptance log field와 gatekeeper option path 관찰만 확인한다.

## 장후 보정 체크리스트 (18:30~19:00)

- [x] `[ProjectCarryover0428-Reconcile0429] 2026-04-28 POSTCLOSE carry-over 6건 source checklist 완료상태 재확인` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:40`, `Track: Plan`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: Project에 `Todo`로 남아 있더라도 source owner인 `2026-04-28 checklist`에서 `[HoldingExitPostclose0428]`, `[QuoteFreshPostclose0428]`, `[QuoteFreshReview0428]`, `[QuoteFreshBackupComposite0428]`, `[ShadowDiff0428]`, `[SoftStopGraceExtend0428]`가 이미 `[x]`인지 먼저 확인하고, source 기준 완료/보류 판정과 Project 상태의 불일치 여부를 분리한다.
  - why: Plan Rebase와 날짜별 checklist 기준에서는 실행 판정의 소유권이 source checklist에 있다. Project만 stale하면 같은 작업을 중복 수행하는 대신 source truth와 drift를 먼저 잠가야 한다.
  - 실행 메모 (`2026-04-29 18:34 KST`): `docs/checklists/2026-04-28-stage2-todo-checklist.md`를 다시 확인한 결과 6개 carry-over 항목이 모두 `[x]`였다. source 판정은 `HoldingExitPostclose0428=directional_only 유지`, `QuoteFreshPostclose0428=OFF`, `QuoteFreshReview0428=규칙 고정 완료`, `QuoteFreshBackupComposite0428=보류`, `ShadowDiff0428=미해소/원인위치 분리 완료`, `SoftStopGraceExtend0428=보류`였다. parser 기준으로도 `DOC_CHECKLIST_PATH=docs/checklists/2026-04-28-stage2-todo-checklist.md DOC_BACKLOG_TODAY=2026-04-28 ... --print-backlog-only` 출력에 이 6개 항목은 포함되지 않았다.
  - 판정 결과: `완료 / source checklist 기준 기처리, Project stale drift`
  - 근거: `workorder Source/Section`이 가리키는 원문 checklist가 이미 완료 상태이고, 관련 산출물(`holding_exit_observation_2026-04-28.json`, `post_sell_*_2026-04-28.jsonl`, `shadow_diff_summary`)도 남아 있다. 오늘 추가로 닫을 분석 실체는 없고, 현재 이슈는 Project 상태가 source와 어긋난 운영 drift다.
  - 테스트/검증:
    - `sed -n '320,490p' docs/checklists/2026-04-28-stage2-todo-checklist.md`
    - `env DOC_CHECKLIST_PATH=docs/checklists/2026-04-28-stage2-todo-checklist.md DOC_BACKLOG_TODAY=2026-04-28 PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only`
  - 다음 액션: source checklist를 기준으로 Project 상태를 재동기화한다. 추가 분석이 아니라 stale Todo 정리가 목적이므로, 같은 6건을 오늘 다시 실행하지 않는다.

- [x] `[EntryBottleneckVmShift0429-PostcloseFallback] VM 변경 후 진입병목 12시 미확정 시 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:45`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md)
  - 판정 기준: `[EntryBottleneckVmShift0429-1200Final]`이 `ShadowDiff`, fresh 로그 미확보, 오전 표본 부족 중 하나로 못 닫혔을 때만 same-day `gatekeeper_eval_ms_p95`, `latency_state_danger share`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`, `ShadowDiff`를 재확인한다.
  - why: VM basis shift는 12시 확정을 기본으로 하고, 장후 항목은 미확정 보정용이다.
  - 실행 메모 (`2026-04-29 12:14 KST`): `[EntryBottleneckVmShift0429-1200Final]`이 same-day `infra-only improvement`로 이미 닫혔다.
  - 판정 결과: `해당 없음`
  - 근거: 장후 fallback은 12시 판정 미확정 보정용인데, 이번에는 fresh bundle과 raw 재집계가 모두 확보돼 12시 창에서 직접 닫혔다.
  - 테스트/검증:
    - `[EntryBottleneckVmShift0429-1200Final]` same-day 근거 재사용
  - 다음 액션: 없음.

- [x] `[InitialQtyCap0429-PostcloseFallback] 스캘핑 신규 BUY 2주 cap 표본부족 시 장후 보정 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:45~19:00`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `[InitialQtyCap0429-1235]`에서 표본 부족 또는 fresh 로그 미확보로 못 닫힌 경우에만 full-day `initial_entry_qty_cap_applied cap_qty=2`, `initial-only` vs `pyramid-activated`, `ADD_BLOCKED reason=zero_qty`, `position_rebased_after_fill`, `full_fill`, `partial_fill`, `COMPLETED + valid profit_rate`를 재확인한다.
  - why: 2주 cap의 구조적 효과는 12시 1차 판정을 기본으로 하고, 장후 항목은 표본부족/미확정 보정용이다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `[InitialQtyCap0429-1235]`는 12시에 이미 닫혔고, full-day raw 재집계에서도 `initial_entry_qty_cap_applied=38건`, `ADD_BLOCKED reason=zero_qty=0건`, `completed_valid_count=17`, `completed_valid_avg_profit_rate=+0.0535%`, `pyramid_activated=3건`이 확인됐다.
  - 판정 결과: `해당 없음 / 12시 판정 유지`
  - 근거: 이 장후 항목은 12시 미확정 보정용인데, 실제로는 12시 창에서 `2주 cap 유지 방향성`이 이미 닫혔다. 장후 재집계도 `zero_qty` 재발이 없고 `pyramid` 표본이 일부 늘어난 정도라 same-day에 cap 추가 완화나 `pyramid floor`를 다시 열 근거는 없다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `pipeline_events_2026-04-29.jsonl`, `post_sell_candidates_2026-04-29.jsonl` full-day 재집계
  - 다음 액션: 신규 후속 없음. `2주 cap`은 익일 PREOPEN/INTRADAY에서 계속 `initial-only`와 `pyramid-activated`를 분리 관찰한다.

- [x] `[SoftStopOliX0429-Postclose] 올릭스(226950) soft stop post-sell 라벨 및 micro grace 품질 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:00~19:15`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `올릭스(226950)` `record_id=4240`의 `post_sell_evaluation` 생성 여부를 확인하고, 생성되면 `good_cut / whipsaw / ambiguous`, `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`를 확인해 `soft_stop_micro_grace` 개입 품질을 닫는다.
  - why: same-day raw 기준으로는 `soft_stop_micro_grace`가 약 `27초` 개입한 뒤 `scalp_soft_stop_pct -1.57%`로 종료됐지만, 아직 `post_sell_evaluation`이 없어 기대값 판단을 hard하게 닫을 수 없다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `post_sell_evaluations_2026-04-29.jsonl`에 `recommendation_id=4240` 평가가 생성돼 있었다. `outcome=GOOD_EXIT`, `profit_rate=-1.57%`, `peak_profit=-0.13%`, `same_symbol_soft_stop_cooldown_would_block=true`, `metrics_10m.mfe_pct=0.313`, `rebound_above_sell=true`, `rebound_above_buy=false`였다.
  - 판정 결과: `완료 / GOOD_EXIT, micro grace 추가 연장 근거 부족`
  - 근거: 10분 창 기준 매도가는 한 번 상회했지만(`rebound_above_sell=true`) 매수가는 끝내 회복하지 못했고(`rebound_above_buy=false`), 10분 최대 반등도 `+0.313%`에 그쳤다. 즉 `soft_stop` 직후 약한 반사반등은 있었지만 손절을 뒤집을 정도의 rebound capture 기회는 아니어서 `whipsaw`보다 `정당 컷` 쪽이 맞다. 이 표본은 `micro grace`를 더 늘려 EV를 개선할 근거가 아니라 `20~30초 유예 후에도 구조적으로 약했던 케이스`로 보는 게 정확하다.
  - 테스트/검증:
    - `data/post_sell/post_sell_evaluations_2026-04-29.jsonl`
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
  - 다음 액션: `올릭스`는 `GOOD_EXIT` anchor case로 유지하고, `micro grace extend` 후보 근거에서는 제외한다.

- [x] `[EntryPriceDaehanCable0429-Postclose] 대한전선(001440) submitted-but-unfilled 진입가 cap/timeout 적정성 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:15~19:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-daehan-cable-entry-price-audit-review.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-review.md), [2026-04-29-daehan-cable-entry-price-audit-rereport.md](/home/ubuntu/KORStockScan/docs/audit-reports/2026-04-29-daehan-cable-entry-price-audit-rereport.md)
  - 판정 기준: `대한전선(001440)` `record_id=4219`의 `entry_armed target_buy_price=48800`, `latency_pass normal_defensive_order_price=50400`, `best_bid/best_ask=50500/50900`, `order_bundle_submitted order_price=48800`, `BUY_ORDERED timeout_sec=1200` 증적을 기준으로, 미체결 원인이 `radar target cap 과도`, `round-figure avoidance`, `BUY_ORDERED timeout 과장`, `유동성/호가 추종 실패` 중 어디인지 닫는다.
  - why: same-day raw 기준 이 케이스는 `latency SAFE + submitted 성공`인데도 실주문가가 최우선 호가에서 3% 이상 아래로 내려가 체결 가능성이 사실상 없었다. 이는 entry drought와 별개로 `진입가 산정/timeout` 기대값 누수를 만들 수 있다.
  - 판정 결과: 완료 / `price cap authority conflict + timeout branch misuse + snapshot ambiguity`
  - 근거: 현재 코드상 `normal_defensive_order_price=50400` 산출 후 `target_buy_price=48800`이 `min(defensive_order_price, target_buy_price)`로 최종 주문가를 낮춘다. `best_bid=50500` 대비 하향 괴리는 약 `337bps`로, 유동성 부족보다 가격결정 권한 충돌이 미체결의 직접 원인이다.
  - 다음 액션: P0는 `pre-submit sanity guard + pipeline_events 가격 스냅샷 분리`로 즉시 보강한다. P1 `strategy-aware resolver/SCALPING timeout table`과 P2 `microstructure-adaptive band/reprice loop`는 별도 승인축으로 이관한다.
  - 테스트/검증: `src/tests/test_sniper_entry_latency.py`, `src/tests/test_sniper_scale_in.py`에 대한전선형 cap/guard 케이스를 추가한다.

- [x] `[SoftStopDuksan0429-Postclose] 덕산하이메탈(077360) soft stop post-sell 라벨 및 micro grace 품질 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:15~19:30`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `덕산하이메탈(077360)` `record_id=4246`의 `post_sell_evaluation` 생성 여부를 확인하고, 생성되면 `good_cut / whipsaw / ambiguous`, `rebound_above_sell`, `rebound_above_buy`, `mfe_10m`, `same_symbol_soft_stop_cooldown_would_block`를 확인해 `soft_stop_micro_grace` 개입 품질을 닫는다.
  - why: same-day raw 기준으로는 `soft_stop_micro_grace`가 약 `20초` 개입했지만 `peak_profit=-0.23`, `profit_rate=-1.50%`, `current_ai_score 85 -> 29` 하락 상태로 종료돼, 반등 누락인지 정당 컷인지 `post_sell_evaluation` 없이는 hard EV 판정을 닫을 수 없다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `post_sell_evaluations_2026-04-29.jsonl`에 `recommendation_id=4246` 평가가 생성돼 있었다. `outcome=NEUTRAL`, `profit_rate=-1.50%`, `peak_profit=-0.23%`, `same_symbol_soft_stop_cooldown_would_block=true`, `metrics_10m.mfe_pct=0.674`, `rebound_above_sell=true`, `rebound_above_buy=false`, `metrics_20m.hit_up_10=true`였다.
  - 판정 결과: `완료 / NEUTRAL, soft stop 후 약한 rebound는 있었으나 매수가 회복 실패`
  - 근거: 10분 내 매도가 재상회했고 `+0.674%` 수준의 반등은 있었지만, 매수가는 회복하지 못해(`rebound_above_buy=false`) `명확한 whipsaw`로 보기 어렵다. 동시에 20분 창에 `hit_up_10=true`가 있어 완전한 `GOOD_EXIT`로 고정하기도 애매하다. 따라서 이 표본은 `soft stop 이후 rebound는 있었지만 same-symbol reentry까지 감안하면 EV 해석이 열려 있는 NEUTRAL anchor case`로 유지하는 것이 맞다.
  - 테스트/검증:
    - `data/post_sell/post_sell_evaluations_2026-04-29.jsonl`
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
  - 다음 액션: `덕산하이메탈`은 `soft stop NEUTRAL + reentry escalation` 중첩 anchor case로 유지하고, `soft_stop` 품질과 `재진입가 상승` 축을 분리해 계속 본다.

- [x] `[WorkorderIntradayRefresh0429] 14시 신규 INTRADAY 항목 일일작업지시서 누락 원인분리 및 스케줄 보강` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:30~19:40`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [2026-04-11-github-project-google-calendar-setup.md](/home/ubuntu/KORStockScan/docs/archive/reference-and-runbooks/2026-04-11-github-project-google-calendar-setup.md)
  - 판정 기준: `MechanicalMomentumLatencyRelief0429-1400`가 `sync_docs_backlog_to_project --print-backlog-only`에는 잡히는데 일일작업지시서에는 누락된 원인이 `Project sync 실패`인지, `workorder 재생성 시각/슬롯 정책`인지 분리한다.
  - 실행 메모 (`2026-04-29`): parser 출력에는 `MechanicalMomentumLatencyRelief0429-1400`가 정상 포함됐다. 추가로 사용자 운영 기준상 Project 동기화 직후마다 `Build Codex Daily Workorder`를 `workflow_dispatch(slot=ALL, target_date=오늘)`로 수동 실행하고 있었는데, 이 경과가 기존 설명에 누락돼 있었다. 따라서 이전 설명의 `자동 13:00 이후 재생성 창 부재`는 부분 설명에 그친다.
  - 판정 결과: `완료 / parser sync 정상, 자동 스케줄 보강 완료, manual ALL 누락 경로 별도 메모`
  - 근거: 최소한 `sync_docs_backlog_to_project` parser와 checklist source는 정상이다. 다만 same-day 누락 해석은 `정기 INTRADAY 스케줄 공백`만으로 닫을 수 없고, `manual ALL rerun`에서도 누락됐다는 운영 사실을 같이 남겨야 `workorder build ref/target_date 생성본` 점검 필요성이 보존된다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
    - [.github/workflows/build_codex_daily_workorder.yml](/home/ubuntu/KORStockScan/.github/workflows/build_codex_daily_workorder.yml)
  - 다음 액션: INTRADAY workorder 자동 생성에 `14:20 KST` 추가 스케줄을 반영했다. same-day late 항목이 다시 누락되면 `workflow_dispatch(slot=ALL, target_date=오늘)` summary와 생성 ref를 같이 확인한다.

- [x] `[TelegramScaleInIcon0429-Postclose] 추가매수 체결 텔레그램 아이콘 분리` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:20~20:25`, `Track: RuntimeStability`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py) 의 추가매수 체결 브로드캐스트 문구를 `📉`에서 `➕`로 교체했다.
  - 판정 결과: `완료 / 추가매수 체결과 손절 완료 텔레그램 아이콘 분리`
  - 근거: 기존 `📉 추가매수 체결`은 손절 완료 알림의 하락 아이콘과 시각적으로 겹쳐 운영 판독을 방해했다. 추가매수는 손익 확정 이벤트가 아니라 포지션 증감 이벤트이므로 중립적인 분리 아이콘이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k update_db_for_add`
  - 다음 액션: 운영 중 추가매수/손절/익절 텔레그램 3종이 시각적으로 즉시 구분되는지 실메시지 표본으로 한 번 더 확인한다.

- [x] `[TelegramEntryMetricsSummaryRemoval0429-Postclose] 진입지표요약 텔레그램 발송기능 삭제` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 21:30~21:40`, `Track: RuntimeStability`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [README.md](/home/ubuntu/KORStockScan/README.md)
  - 실행 메모 (`2026-04-29`): [bot_main.py](/home/ubuntu/KORStockScan/src/bot_main.py) 의 `15:40` 진입 지표 + shadow + post-sell 관리자 브로드캐스트 스케줄과 전송 함수를 삭제했다. [telegram_manager.py](/home/ubuntu/KORStockScan/src/notify/telegram_manager.py) 의 관리자 `/entry_metrics`, `/진입지표`, `📊 진입 지표` 버튼 응답도 삭제했다.
  - 판정 결과: `완료 / 진입지표요약 텔레그램 메시지 발송 경로 제거`
  - 근거: 해당 메시지는 현재 Plan Rebase 판정 입력이 아니라 운영 노이즈가 되고 있으며, 진입/청산 분석은 monitor snapshot, checklist, report 기준으로 충분히 대체된다. 로그 집계 모듈 [sniper_entry_metrics.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_metrics.py) 는 오프라인 분석/테스트 재사용 가능성이 있어 남겼다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_sniper_entry_metrics.py src/tests/test_telegram_buy_pause_guard.py src/tests/test_sniper_scale_in.py -q`
    - `PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500`
  - 다음 액션: 운영 브로드캐스트는 추천종목, 체결/상태 알림, 모니터 스냅샷 저장 완료 등 실제 대응이 필요한 알림만 유지한다.

- [x] `[TrailingJeryong0429-Postclose] 제룡전기(033100) 추가매수 체결 후 트레일링 익절 분석` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:25~20:35`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): `record_id=4266` 기준 `13:58:59` 초기 `FULL_FILL 2주 @ 63,400원`, `14:34:26` `scale_in_executed add_type=PYRAMID fill_price=64,600 fill_qty=1 new_avg_price=63,800 new_buy_qty=3`, `14:35:47` `exit_signal sell_reason_type=TRAILING profit_rate=+0.86 peak_profit=+1.33`, `14:35:48` `sell_completed sell_price=64,500 revive=True new_watch_id=4415`를 확인했다.
  - 판정 결과: `완료 / 추가매수 후 트레일링 익절은 확인됐으나 단일 표본만으로 과보수 판정은 보류`
  - 근거: 추가매수 체결 후 평균단가는 `63,800원`, 청산가는 `64,500원`으로 `+0.86%` 수익 실현이며, peak 대비 되돌림은 약 `-0.46%p`였다. 즉 `고점 일부 반납 후 이익 잠금`은 맞지만, 현재 증적에는 `sell_completed` 직후 same-symbol 재진입이나 `post_sell_evaluation` 기반 `MISSED_UPSIDE`가 아직 없다. 이 표본 하나만으로 `트레일링이 너무 이르다`고 단정하기보다, `pyramid 직후 변동성 구간에서 trailing continuation이 충분히 버텼는지`를 별도 축으로 봐야 한다.
  - 테스트/검증:
    - `logs/pipeline_event_logger_info.log.1`
    - `logs/pipeline_event_logger_info.log`
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
    - `data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: `post_sell_evaluation_2026-04-29` 생성 후 `GOOD_EXIT / MISSED_UPSIDE`, `rebound_above_sell`, `mfe_10m`, `same_symbol_reentry`를 붙여 최종 라벨을 닫는다.

- [x] `[TrailingRebase0429-Postclose] Plan Rebase trailing 익절 보수성/EV 개선축 포함 여부 점검` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:35~20:45`, `Track: Plan`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [plan-korStockScanPerformanceOptimization.execution-delta.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.execution-delta.md)
  - 판정 기준: `trailing_continuation`, `same_symbol_reentry`, `opportunity_cost`가 Rebase 문서에 살아 있는지, 그리고 trailing EV 개선이 `active live 축`, `observe-only`, `후순위 candidate` 중 어디에 놓였는지 확인한다.
  - 실행 메모 (`2026-04-29`): Rebase 문서에는 `holding_exit_observation` 필드로 `trailing_continuation`, `same_symbol_reentry`, `opportunity_cost`가 고정돼 있고, pain point에도 `trailing 익절 직후 동일종목 고가 재진입`이 기대값 훼손 사례로 명시돼 있다. 다만 현재 우선순위는 `soft_stop_rebound_split 1순위`, `trailing_continuation_micro_canary 2순위`다.
  - 판정 결과: `완료 / trailing EV 개선은 문서에 포함돼 있으나 active 작업축은 아님`
  - 근거: Plan Rebase는 trailing 문제를 모르는 상태가 아니라, same-symbol reentry와 missed upside를 EV 이슈로 이미 인지하고 있다. 다만 4월 월간 손실기여와 휩쏘 빈도 기준으로 현재 active 보유/청산 1축은 `soft_stop_micro_grace`이며, trailing은 observe/candidate 단계에 머물러 있다. 따라서 “포함 여부”는 `예`, “지금 실행중인 개선축인가”는 `아니오`가 정확하다.
  - 다음 액션: trailing을 `2순위 candidate`에서 끌어올릴지 여부는 익일 checklist에서 `same_symbol reentry + post_sell evaluation` 표본을 붙여 재판정한다.

- [x] `[SoftStopKolon0429-Postclose] 코오롱(002020) soft stop 후 고가 재진입 분석` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:40~19:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): `post_sell_candidates_2026-04-29.jsonl` 기준 `recommendation_id=4322`, `sell_time=14:00:18`, `buy_price=72900`, `sell_price=71800`, `profit_rate=-1.74%`, `peak_profit=+0.32%`, `same_symbol_soft_stop_cooldown_would_block=true`였다. 이후 `record_id=4397`에서 `14:20:27` `order_bundle_submitted order_price=72100`이 확인됐다.
  - 판정 결과: `완료 / soft stop 후 고가 재진입 시도는 있었지만 상승폭은 제한적`
  - 근거: 재진입 제출가는 `72100`으로 soft stop 매도가 `71800` 대비 `+300원 (+0.42%)` 높았지만, 최초 매수가 `72900`보다는 여전히 낮았다. 즉 `soft stop 직후 더 비싸게 다시 추격한 구조`는 맞지만, 덕산하이메탈형 `매수가 상회 재진입` 급은 아니다. 또한 이후 `buy_ordered/fill` 증적은 없어 `고가 재진입 체결`이 아니라 `고가 재진입 제출 시도`로 보는 게 맞다.
  - 테스트/검증:
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
    - `data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: `same_symbol_soft_stop_cooldown_would_block=true`가 반복되는지와 `soft stop 후 20~30분 재시도` 코호트를 모아 `재진입 허용폭` observe-only 축으로 묶는다.

- [x] `[SoftStopGNBSEco0429-Postclose] 지앤비에스 에코(382800) soft stop 후 고가 재진입 분석` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:50~20:00`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): `recommendation_id=4289`, `sell_time=14:01:53`, `buy_price=9030`, `sell_price=8870`, `profit_rate=-2.0%`, `peak_profit=+0.76%`, `same_symbol_soft_stop_cooldown_would_block=true`였다. soft stop 후 `record_id=4399`에서 `14:32:35` `order_bundle_submitted order_price=8960`, `14:32:36` `position_rebased_after_fill avg_buy_price=8960 buy_qty=2`, `14:44:56` `sell_completed sell_price=9010 profit_rate=+0.33 exit_rule=scalp_ai_momentum_decay`가 확인됐다.
  - 판정 결과: `완료 / soft stop 후 고가 재진입 체결 뒤 소폭 익절 완료`
  - 근거: 재진입 체결가는 `8960`으로 soft stop 매도가 `8870` 대비 `+90원 (+1.01%)` 높은 가격이었고, 이후 익절 체결가는 `9010`으로 재진입 대비 `+50원`, 원매수가 `9030` 대비 `-20원`이었다. 즉 이 케이스는 `soft stop 직후 더 높은 가격에 다시 들어가긴 했지만, same-day에 손실 일부를 회수하며 익절 완료한 rebound recovery case`다. 다만 최초 soft stop 손실 `-2.0%`를 완전히 상쇄하진 못했으므로, soft stop 품질 평가에서는 `고가 재진입이 있었고 rebound capture도 일부 성공한 mixed case`로 봐야 한다.
  - 테스트/검증:
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
    - `data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: 지앤비에스 에코는 `soft stop 후 same-day 고가 재진입 체결 + 익절 완료` anchor case로 유지하고, `코오롱/덕산하이메탈`과 분리해 `soft stop rebound recovery` 표본으로 묶는다. 장후 `post_sell_evaluation` 생성 시 `GOOD_EXIT / MISSED_UPSIDE`보다 `soft stop 후 recovery recapture` 별도 라벨 필요 여부를 같이 본다.

- [x] `[SoftStopCuriox0429-Postclose] 큐리옥스바이오시스템즈(445680) soft stop 분석` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:00~20:10`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): 사용자 질의의 `큐리우스바이오(445680)`는 현재 데이터상 `큐리옥스바이오시스템즈(445680)`였다. `recommendation_id=4287`, `sell_time=14:09:51`, `buy_price=103400`, `sell_price=101800`, `profit_rate=-1.77%`, `peak_profit=-0.13%`, `same_symbol_soft_stop_cooldown_would_block=true`였다. soft stop 후 `record_id=4398`에서 `blocked_strength_momentum`만 반복됐고 `order_bundle_submitted`는 없었다.
  - 판정 결과: `완료 / 현재 증적 기준 정당 컷 후보, 재진입 실패`
  - 근거: 보유 중 `peak_profit`가 한 번도 양전환하지 못했고, soft stop 이후에도 same-day 재진입 제출조차 나오지 않았다. 이는 `손절 후 바로 위로 반등한 whipsaw`보다 `수급/모멘텀 미복구 상태에서의 정당 컷` 쪽에 더 가깝다. 다만 `post_sell_evaluation_2026-04-29`가 아직 없어 최종 라벨은 보류한다.
  - 테스트/검증:
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
    - `data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: `post_sell_evaluation` 생성 후 `GOOD_EXIT / NEUTRAL / MISSED_UPSIDE`로 최종 라벨을 닫고, 같은 패턴의 `peak_profit<0` soft stop 코호트를 별도로 분리한다.

- [x] `[SoftStopSKSquare0429-Postclose] SK스퀘어(402340) soft stop 분석` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:20`, `Track: Plan`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 실행 메모 (`2026-04-29`): `recommendation_id=4224`, `sell_time=14:09:23`, `buy_price=835000`, `sell_price=823000`, `profit_rate=-1.66%`, `peak_profit=+0.25%`, `same_symbol_soft_stop_cooldown_would_block=true`였다. soft stop 후 `record_id=4383`에서 `14:29:30` `order_bundle_submitted order_price=819000`이 확인됐지만 soft stop 매도가보다 오히려 낮았다.
  - 판정 결과: `완료 / soft stop 후 재시도는 있었으나 고가 재진입은 아님`
  - 근거: post-sell 재제출가 `819000`은 soft stop 매도가 `823000`보다 `-4000원 (-0.49%)`, 원매수가 `835000`보다 `-16000원` 낮다. 따라서 이 케이스의 핵심은 `soft stop 후 더 비싸게 다시 들어간 실패`가 아니라 `same-day lower-price retry가 있었는데도 원매수 회복이 없었던 soft stop`이다. 현재로선 `whipsaw`보다 `미약한 반등을 못 살린 NEUTRAL/정당 컷 후보`에 가깝다.
  - 테스트/검증:
    - `data/post_sell/post_sell_candidates_2026-04-29.jsonl`
    - `data/pipeline_events/pipeline_events_2026-04-29.jsonl`
  - 다음 액션: `post_sell_evaluation_2026-04-29` 생성 후 `10m rebound_above_sell / rebound_above_buy / mfe_pct`를 확인해 최종 품질 라벨을 닫는다.

- [x] `[AICacheCohort0429-Postclose] gatekeeper/holding AI cache hit vs miss 영향도 관찰축 판정` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:30~19:50`, `Track: ScalpingLogic`)
  - Source: [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md), [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md)
  - 판정 기준: `gatekeeper_cache=fast_reuse/hit/miss`, `ai_cache=hit/miss`, `ai_holding_skip_unchanged`를 코호트로 분리해 `submitted`, `budget_pass_to_submitted_rate`, `full_fill`, `partial_fill`, `soft_stop`, `COMPLETED + valid profit_rate` 차이를 확인하고, `보조지표 유지`, `고우선 observe-only 축 승격`, `독립 canary 후보 준비` 중 하나로 닫는다.
  - why: 현재 문서상 `gatekeeper_fast_reuse`는 종료된 보조 진단축이지만, 캐시/재사용 로직은 지연과 재평가 빈도에 영향을 주므로 submitted/EV에 대한 간접 영향도가 무시할 수준은 아니다. 다만 아직 `submitted/full/partial` 직접 회복 근거가 없어 same-day live 승격보다 영향도 관찰축으로 먼저 분리하는 것이 맞다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `pipeline_events_2026-04-29.jsonl`에는 `gatekeeper_cache`/`ai_cache`가 `submitted/full/partial`과 직접 조인될 수 있는 structured field로 남아 있지 않았다. 대신 holding 쪽에서는 `ai_holding_skip_unchanged=366건`, `scalp_preset_tp_ai_hold_action ai_result_source='-'=1건`이 있었고, `bot_history.log` 기준 `AI 보유감시`는 `MISS 2260건`, `HIT 67건`이었다.
  - 판정 결과: `완료 / 보조지표 유지, 독립 canary 후보 미승격`
  - 근거: same-day에는 holding cache hit/miss 관측량 자체는 충분하지만, `submitted/full/partial/COMPLETED + valid profit_rate`와 직접 연결되는 엔트리 cache structured field가 비어 있어 인과를 hard하게 닫을 수 없다. 즉 영향도가 0이라는 뜻이 아니라 `현재 로그 스키마만으로는 제출 회복이나 EV 변화의 직접 원인축으로 승격할 증거가 부족`하다는 뜻이다. 따라서 Rebase 문서의 `보조 진단 지표` 위치를 유지하는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `pipeline_events_2026-04-29.jsonl`, `bot_history.log` cache hit/miss 집계
  - 다음 액션: cache를 독립 관찰축으로 올리려면 먼저 `gatekeeper_cache`/`ai_cache`를 `order_bundle_submitted`, `position_rebased_after_fill`, `sell_completed`와 조인 가능한 structured field로 남기는 로깅 보강이 선행돼야 한다.

- [x] `[ReentryPriceEscalation0429-Postclose] 덕산하이메탈(077360) 1차 미체결 후 2차 재진입가 상승 케이스 분석축 승격` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 19:50~20:10`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `덕산하이메탈(077360)` `record_id=4246`에서 `1차 submitted 17330 -> 미체결`, `2차 submitted/fill 18030`, `재진입가 상승폭 +700원 (+4.0%)`, `peak_profit=-0.23`, `soft_stop -1.50%`를 기준 케이스로 고정하고, 이 형상을 `entry price escalation after miss` 분석축으로 유지할지 여부를 닫는다.
  - why: 이 케이스는 단순 슬리피지 문제가 아니라 `1차 미체결 뒤 더 높은 가격을 다시 허용한 재진입 구조`가 EV를 훼손했을 가능성을 보여준다. 현재 entry 관찰축에는 `re-arm/reprice escalation`이 별도 고정돼 있지 않아, 같은 종류의 손실 표본을 다시 놓칠 수 있다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `record_id=4246`에서 `09:17:04 order_bundle_submitted order_price=17330` 후 미체결, `10:08:14 order_bundle_submitted order_price=18030`, `10:11:42 FULL_FILL avg_buy_price=18030`, `10:15:23 sell_completed profit_rate=-1.50`가 확인됐다. 상승폭은 `+700원`, `+4.04%`다.
  - 판정 결과: `완료 / 분석축 승격 유지`
  - 근거: 이 표본은 `1차 미체결 -> 같은 record 재무장 -> 더 높은 가격 허용 -> soft stop 손실`의 순서가 선명하다. 문제를 `유동성 부족` 하나로 축소하면 놓치고, 실제로는 `re-arm 허용 후 target_buy_price 상향 구조`를 별도 축으로 봐야 한다. 따라서 `entry price escalation after miss` anchor case로 유지하는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `pipeline_events_2026-04-29.jsonl`의 `record_id=4246` 단계 재구성
  - 다음 액션: 이 케이스는 `price guard`와 분리해 `re-arm/재진입가 상승` 축으로 계속 본다.

- [x] `[ReentryPriceEscalationSample0429-Postclose] 동일 거래일 1차 미체결 후 2차 재진입가 상승폭 표본 수집` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 20:10~20:30`, `Track: ScalpingLogic`)
  - Source: [2026-04-29-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-29-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `data/pipeline_events/pipeline_events_2026-04-29.jsonl`에서 같은 `record_id` 기준 `1차 order_bundle_submitted` 이후 미체결 또는 `entry_armed_expired_after_wait`가 발생하고, 이후 `2차 order_bundle_submitted` 또는 fill이 이어진 종목을 수집해 `1차 target/order price`, `2차 target/order price`, `상승폭(원/%), full/partial fill`, `COMPLETED + valid profit_rate`, `soft_stop 여부`를 표로 정리한다.
  - why: 덕산하이메탈 단일 사례만으로는 구조 문제를 일반화할 수 없다. 같은 날 표본을 모으면 `고점 추격형 재진입`이 반복되는지, 아니면 개별 종목 예외인지 구분할 수 있다.
  - 실행 메모 (`2026-04-29 장후 재확인`): same-day full log에서 `같은 record_id 기준 1차 submitted 후 미체결/만료 -> 2차 submitted 가격 상승` 케이스를 다시 수집했다. 오늘 기준 명확히 확인된 표본은 `덕산하이메탈(077360) record_id=4246: 17330 -> 18030 (+700원, +4.04%), FULL_FILL 후 soft_stop -1.50%` 1건뿐이었다.
  - 판정 결과: `완료 / 표본 부족, 오늘은 덕산하이메탈 anchor case만 유지`
  - 근거: 수집 기준을 엄격히 걸면 same-day 동일 `record_id` 구조에서는 `덕산하이메탈` 1건만 남는다. 따라서 아직은 일반화보다 anchor case 보존이 우선이다. 표본 3건 이상이 쌓이기 전까지는 이 축을 독립 observe-only로 키우기보다 `대표 케이스 1건`으로 유지하는 편이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `pipeline_events_2026-04-29.jsonl` same-record multi-submission 집계
  - 다음 액션: 표본 수집은 익일 이후로 계속 누적하되, today hard conclusion은 `덕산하이메탈 단일 anchor case`다.

- [x] `[ShadowDiff0429-PostcloseRootCause] 2026-04-27 historical submitted/fill mismatch 원인분리` (`Due: 2026-04-29`, `Slot: POSTCLOSE`, `TimeWindow: 18:30~18:50`, `Track: ScalpingLogic`)
  - Source: [2026-04-28-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-28-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
  - 판정 기준: `2026-04-27` historical 기준 `submitted/full/partial` mismatch가 `event restoration bug`, `중복 집계`, `test contamination`, `legacy fallback 잔차` 중 어디가 주원인인지 분리한다.
  - why: historical mismatch가 닫혀야 `submitted/full/partial`을 hard pass/fail 판정 축에 다시 쓸 수 있다.
  - 실행 메모 (`2026-04-29 장후 재확인`): `pipeline_events_2026-04-27.jsonl` raw 집계 기준 `submitted_unique=11`, `submitted_events=17`, `position_rebased_after_fill rows=84`, `completed_candidates=8`이었다. 이 중 `record_id=1 / TEST(123456)`가 `position_rebased_after_fill` 77건을 차지했고, `fallback_scout`, `scale_in_executed`, `same_ts_multi_rebase`, `UNKNOWN/PARTIAL/FULL_FILL`이 한꺼번에 섞인 synthetic shadow/test 이벤트였다.
  - 판정 결과: `완료 / 주원인은 TEST(123456) synthetic contamination`
  - 근거: `2026-04-27` mismatch는 실전 종목 퍼널 불일치보다 `record_id=1 TEST(123456)`가 historical dataset에 유입된 탓이 훨씬 크다. 실제 non-test fill unique는 7~8건 수준인데 synthetic `position_rebased_after_fill`가 77건 추가돼 `submitted 11 vs fill rows 84`로 왜곡됐다. 따라서 이 이슈는 `실전 fill 누락`보다 `historical pipeline_events 테스트 오염`으로 닫는 것이 맞다.
  - 테스트/검증:
    - `PYTHONPATH=. .venv/bin/python` 으로 `pipeline_events_2026-04-27.jsonl` `stage/record_id` 재집계
    - `rg -n '"record_id": 1|TEST|123456' data/pipeline_events/pipeline_events_2026-04-27.jsonl`
  - 다음 액션: historical 비교 리포트에서는 `TEST(123456)` synthetic row exclusion rule을 먼저 적용해야 한다.

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-29 15:48:02`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-29.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
