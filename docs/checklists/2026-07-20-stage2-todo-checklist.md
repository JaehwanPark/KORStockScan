# 2026-07-20 Stage2 To-Do Checklist

## 오늘 목적

- 전일 postclose 자동화가 만든 장전 apply 후보와 사용자 개입 요구사항을 산출물 기준으로 확인한다.
- 실주문, threshold, provider, sim/probe 관련 변경은 approval artifact와 checklist 기준 없이 열지 않는다.
- code-improvement workorder는 자동 repo 수정이 아니라 사용자가 Codex에 구현을 지시한 경우에만 실행한다.

## 오늘 강제 규칙

- 장중 runtime threshold mutation은 금지한다. 적용은 PREOPEN `threshold_cycle_preopen_apply`가 생성한 runtime env만 source로 본다.
- 튜닝 데이터 기준은 `clean_tuning_baseline_date=2026-06-04`, `clean_tuning_baseline_ts_kst=2026-06-04T14:29:09+09:00`이다. 기준 이전 raw/report/analytics artifact는 archive/audit evidence로만 보고 EV/rolling/MTD/cumulative tuning, live-auto promotion, runtime approval, pattern lab promotion, real execution quality approval 입력으로 쓰지 않는다.
- Baseline 이후 raw source-quality contract 결손은 날짜 전체 차단이 아니라 결손 row/window를 `raw_row_exclusion`으로 제외하는 것이 기본이다. 전체 block은 preflight missing/invalid, row/window exclusion 실패, 또는 결손을 안정적으로 특정할 수 없는 high-volume no-contract 상황에만 사용한다.
- 장중과 장후에는 `observation_source_quality_audit --write` 또는 최신 artifact로 raw source-quality를 반복 확인한다. Hard contract gap은 결손 row/window 제외 또는 `source_quality_blocked` 없이는 튜닝 입력에 들어갈 수 없고, unknown-token warning은 hard block이 아니더라도 code-improvement workorder handoff 확인 대상이다.
- provider transport/provenance 확인은 threshold 값, 주문가/수량 guard, 스윙 dry-run guard 변경과 분리한다.
- `actual_order_submitted=false`인 sim/probe 표본은 EV/source-quality 입력이며 실주문 전환 근거가 아니다.
- Project/Calendar 동기화는 사용자가 표준 동기화 명령으로 수행한다.

## 코드베이스 유지보수

- [x] `[BlackCodebaseBaseline0720] 전체 Python 코드베이스 Black 26.5.1 기준선 및 CI gate 고정` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 15:50~17:30`, `Track: RuntimeStability`)
  - Source: [pyproject.toml](/home/ubuntu/KORStockScan/pyproject.toml), [black.yml](/home/ubuntu/KORStockScan/.github/workflows/black.yml), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: Python 3.11, Black `26.5.1`, line length `88`로 전체 `black --check .`, AST 동등성, compile, 전체 pytest, checklist parser, `git diff --check`를 통과하고 포맷 배치를 부분 롤백 가능한 독립 커밋으로 남긴다.
  - 금지: 포맷 작업에 runtime report/cache, 주문·provider·threshold·bot 재기동 또는 기능 변경을 포함하지 않는다.
  - 실행 결과 (`2026-07-20 KST`): `black_codebase_baseline_complete`. 전체 `547`개가 `black --check .`을 통과했고 변경 Python `252`개 중 `251`개는 위치 및 docstring 줄끝 공백을 제외한 AST가 `main`과 동일하다. 나머지 1개는 Black이 바꾼 Kiwoom source layout 뒤에도 동일 실행 순서를 검증하도록 source-order 테스트 검색 문자열만 보완한 변경이다. 전체 compile과 pytest는 포맷 전 기준선과 동일한 `4607 passed, 18 skipped, 5 warnings`, checklist parser와 `git diff --check`는 pass이며 review gate 미해결 finding은 `0`이다. runtime report/cache와 수동제어 파일은 커밋에서 제외했고 주문·provider·threshold·bot 재기동은 수행하지 않았다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_START -->
## 자동 생성 체크리스트 (`2026-07-16` postclose -> `2026-07-20`)

- 이 블록은 postclose 자동화 산출물에서 생성된다.
- `codex_daily_workorder_*.md`는 downstream 전달물이라 입력 source로 사용하지 않는다.
- RunbookOps 반복 확인은 `build_codex_daily_workorder`와 Project/Calendar 동기화 경로가 별도로 소유한다.

## 장전 체크리스트 (07:55~09:00)

- [ ] `[RuntimeRolloverPreopen0721] 2026-07-20 operator runtime bundle의 익일 overlay 및 PID handoff 확인` (`Due: 2026-07-21`, `Slot: PREOPEN`, `TimeWindow: 07:55~08:10`, `Track: RuntimeStability`)
  - Source: [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [operator_runtime_overrides_2026-07-21.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides_2026-07-21.env)
  - 판정 기준: 2026-07-21 PREOPEN threshold env를 먼저 source한 뒤 persistent operator override와 target-date overlay가 순서대로 적용되고, 금일 활성화된 date-scoped 20개 family의 `ACTIVE_DATE=2026-07-21`, entry/scale-in split policy usability, runtime verifier `status=pass`, PID mismatch/missing `0`을 확인한다.
  - 금지: 2026-07-20 프로세스에서 ACTIVE_DATE를 선행 변경해 당일 runtime을 끄거나, stale quote, broker/account/order/quantity/cooldown, hard/protect/emergency stop, provider, sizing/cap 권한을 변경하지 않는다.
  - 다음 액션: `rollover_reflected_and_verified`, `overlay_missing`, `preopen_env_missing`, `policy_stale`, `pid_handoff_failed`, `rollback_required` 중 하나로 닫는다.
  - 준비 결과 (`2026-07-20 15:35 KST`): target-date overlay loader와 verifier 합성을 구현하고 금일 `ACTIVE_DATE=2026-07-20`인 20개 family를 누락 없이 `2026-07-21` overlay로 이관했다. runtime wrapper/verifier 전체 `181 passed`, compile, shell syntax, checklist parser, `git diff --check`를 통과했고 review gate 미해결 finding은 `0`이다. PID `231073 -> 270827` 우아한 재기동 후 금일 verifier는 `passed/pid_passed=true`, dated fail/mismatch/missing=`0/0/0`; 계좌 동기화와 WS 연결도 정상이다. 내일 실제 PREOPEN env 생성 후 target-date overlay와 PID handoff를 최종 판정한다.

- [x] `[ScaleInPerTypeExecutionCapPreopen0720] scale-in 유형별 최대 1회 실행 제한 프로세스 반영 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 07:55~08:10`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 신규 프로세스가 변경 코드를 적재했는지 확인하고 동일 포지션 lifecycle에서 `AVG_DOWN` 최대 1회, `PYRAMID` 최대 1회가 각각 독립 적용되는지 확인한다. multi-leg 주문은 하나의 scale-in bundle로 계산하고 미체결/거절/취소 주문은 실행횟수로 계산하지 않는다.
  - 금지: 유형별 카운터를 포지션 종료 전에 초기화하거나 다른 scale-in reason으로 동일 유형 제한을 우회하지 않는다. broker/order/quantity/stale quote guard는 변경하지 않는다.
  - 다음 액션: `process_reflected_and_cap_active`, `process_not_restarted`, `counter_provenance_missing`, `same_type_second_execution_detected` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-20 07:58 KST`): `process_reflected_and_cap_active`. `bot_main.py` PID `14924`가 `07:55:01 KST`에 신규 기동되어 변경 파일을 적재했고 계좌 동기화/WS 연결이 완료됐다. 유형별 1회, 미체결 복원, partial-fill 유지 관련 집중 테스트 `15 passed`를 확인했다. 기존 `038500` lifecycle은 DB상 `AVG_DOWN` bundle 2회가 이미 존재해 새 guard가 추가 동일 유형 실행을 차단하며, `052710`은 유형별 실행 이력이 없다.

- [x] `[ScaleInInitialQtyCapPreopen0720] 최초매수 기준 scale-in 누적 체결수량 1.5배 상한 반영 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 07:55~08:10`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py), [sniper_sync.py](/home/ubuntu/KORStockScan/src/engine/sniper_sync.py), [models.py](/home/ubuntu/KORStockScan/src/database/models.py)
  - 판정 기준: 최초매수수량 `initial_buy_qty`와 실제 scale-in 체결 누적 `scale_in_filled_qty`를 확인하고 `floor(initial_buy_qty*1.5)`를 초과하는 신규 scale-in 계획/분할 leg/브로커 호출이 없는지 확인한다. 부분체결은 실제 체결분만 누적하고, 미체결/취소/거절은 누적하지 않는다.
  - 금지: 유형별 실행횟수 제한을 우회하거나 최초수량/누적수량을 포지션 종료 전에 초기화하지 않는다. 상한 완화, broker/order/stale quote guard 우회, sim/probe의 실주문 권한 전환을 하지 않는다.
  - 다음 액션: `process_reflected_and_qty_cap_active`, `legacy_initial_qty_hydrated_from_history`, `initial_qty_missing_fail_closed`, `scale_in_qty_cap_breach_detected` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-20 07:58 KST`): `legacy_initial_qty_hydrated_from_history`. 기존 `038500` DB row의 신규 필드는 아직 `0`이지만 `HoldingAddHistory EXECUTED` 이력으로 runtime 복원값 `initial_buy_qty=1`, `scale_in_filled_qty=485`가 산출되어 `floor(1*1.5)=1` 상한의 남은 수량이 `0`으로 fail-closed 된다. 신규 보유 `052710`은 scale-in 이력이 없어 현재 `buy_qty=20`을 최초수량 baseline으로 사용한다. DB backfill, 상한 완화, broker/order guard 변경은 수행하지 않았다.

- [ ] `[ThresholdEnvAutoApplyPreopen0720] threshold env 자동 apply 산출물 및 사용자 개입 여부 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 08:50~08:55`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-16.json), [threshold_cycle_preopen_apply.py](/home/ubuntu/KORStockScan/src/engine/threshold_cycle_preopen_apply.py), [run_bot.sh](/home/ubuntu/KORStockScan/src/run_bot.sh)
  - 판정 기준: 전일 postclose EV와 당일 apply plan/runtime env를 확인하고 `auto_bounded_live` guard 통과분만 runtime env로 인정한다.
  - 금지: blocked family, approval artifact missing, same-stage owner conflict를 수동 env override로 우회하지 않는다.
  - 다음 액션: `applied_guard_passed_env`, `blocked_no_env`, `partial_apply_with_blocked_families`, `failed_preopen_wrapper`, `not_yet_due` 중 하나로 닫는다.
  - 사전 확인 (`2026-07-20 07:58 KST`): `not_yet_due`. PREOPEN status는 `succeeded`, apply plan은 `auto_bounded_live_ready`, env/manifest는 `07:35 KST` 생성됐고 PID `14924`가 해당 env를 source했다. 다만 `threshold_runtime_env_verify_2026-07-20.json`은 `status=fail`, `fail_reason=runtime_env_handoff_missing`이며 `entry_split_order_plan=policy_inactive_date`, `scale_in_split_order_plan=stale_policy`, `persistent_operator_overrides_2026_06_26=unverified_selected_family`를 기록한다. `08:50~08:55` window에서 이 상태를 재확인해 `partial_apply_with_blocked_families` 여부를 최종 확정한다. 수동 env 보정이나 봇 재기동은 수행하지 않았다.
  - 분할매수 복구 (`2026-07-20 08:13 KST`): `scale_in_split_runtime_recovered`. `2026-07-17` 제헌절 휴장과 주말을 calendar-day age로 합산해 `scale_in_split_order_plan=stale_policy`로 오판하던 freshness 계약을 KRX trading-day age로 통일했다. runtime allocator와 PREOPEN verifier 모두 최대 `3` KRX 거래일을 사용하며, `2026-07-16T20:28:37+09:00` 정책은 오늘 age=`1`로 `policy_usable`이다. review gate에서 split/preopen `154 passed`, sniper scale-in `765 passed`, compile 및 `git diff --check`를 통과했고, 10주 진단은 총수량을 보존한 `5+5`, 가격 `10000/9970` 두 leg로 적용됐다. 봇은 PID `14924 -> 23919`로 재기동되어 기존 selected policy env를 다시 source했으며 계좌 동기화·스캐너·관제 루프가 정상이다. 재생성 verifier에서 scale-in audit는 `pass`로 복구됐고, 전체 verifier fail은 별도 inactive entry-split override 두 건만 남는다. 신규진입 split은 현재 정책 권한이 없어 활성화하지 않았다.
  - 신규진입 split 복구 (`2026-07-20 08:16 KST`): `entry_split_runtime_recovered`. 사용자가 신규진입 split 적용을 명시해 최신 clean-baseline 산출물 `entry_split_order_policy_2026-07-16.json`과 version `entry_split_order_plan:2026-07-16:97d170e155`를 오늘 한정 operator fallback/market-first로 열었다. `runtime_apply_allowed=false` 정책은 사용자 지시와 `ACTIVE_DATE=2026-07-20` 없이는 계속 fail-closed하며, 이번 override도 오늘 이후 자동 OFF 된다. 10주 진단은 총수량 보존 `5주 market-first + 2주/3주 resolver-limit`, 가격 `market/9970/9920`의 3-leg로 적용됐고 stale quote, unapproved DANGER latency, broker/account/order/quantity/cooldown, sizing/cap/provider/TP/exit guard는 유지된다. 관련 entry/split/sniper 테스트 `794 passed`, env shell syntax, `git diff --check` 및 review gate를 통과한 뒤 PID `23919 -> 25809`로 재기동했다. 최종 runtime verifier는 status=`pass`, pid_passed=`true`, pid mismatch/missing=`0`, entry/scale-in audit=`pass/pass`이며 계좌 동기화·WS 로그인·스캐너·관제 루프가 정상이다.
  - 퇴역 runtime 정리 (`2026-07-20 10:33 KST`): `retired_runtime_authority_closed`. `soft_stop_dynamic_grace_runtime`과 `late_entry_price_drift_guard_runtime`의 operator lock을 `retired_archive_only`, `enabled=false`, `runtime_effect=false`로 닫고 잔존 override를 제거했다. PREOPEN writer는 두 family의 13개 env 키를 모두 제거하며 verifier는 manifest/operator override/selected family 중 하나라도 퇴역 흔적이 남으면 `retired_runtime_selection_or_override_present`로 FAIL한다. 1차 review의 `퇴역 override 무시 시 실제 source와 verifier 불일치` 결함과 2차 review의 `stale selected family 미차단·실패 사유 불명확` 결함을 보완했고 PREOPEN apply `141 passed`, compile, checklist parser, 실제 PID `94253` handoff `pass`, `git diff --check`를 통과했다. 대체 owner인 `soft_stop_whipsaw_confirmation`, `weak_context_late_entry_guard_runtime`, `quote_consistency_normalization`과 hard safety는 변경하지 않았고 봇 재기동도 수행하지 않았다.

- [ ] `[RisingMissedScoutRuntimePreopen0720] rising_missed_scout_workorder 구현분 다음 장전 runtime 반영 여부 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [rising_missed_scout_workorder_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/rising_missed_scout_workorder/rising_missed_scout_workorder_2026-07-16.json), [rising_missed_normal_buy_bridge_candidate_discovery_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/rising_missed_normal_buy_bridge_candidate_discovery/rising_missed_normal_buy_bridge_candidate_discovery_2026-07-16.json), [code_improvement_workorder_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-16.json), [threshold_apply_2026-07-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-20.json), [threshold_runtime_env_2026-07-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_2026-07-20.json), [threshold_runtime_env_verify_2026-07-20.json](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/threshold_runtime_env_verify_2026-07-20.json)
  - 판정 기준: 전일 `rising_missed_scout_workorder` 요약(code_improvement_order_count=`2`, forced_scout_with_post_sell_count=`1`, profitable_forced_scout_count=`0`, loss_or_flat_forced_scout_count=`1`, current_missed_count=`0`)과 `rising_missed_normal_buy_bridge_candidate_discovery` 요약(status=`source_missing`, bridge_candidate_count=`0`, code_improvement_order_count=`0`, runtime_env_key=`KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED`)을 함께 보고 구현 완료된 mapped family가 당일 PREOPEN apply plan/runtime env/verify에 반영됐는지 확인한다. source-only order는 별도 runtime family/env mapping과 guard 통과가 있을 때만 반영으로 인정한다.
  - 금지: `rising_missed_scout_workorder`/bridge discovery 생성 또는 forced 1-share scout 손익만으로 runtime threshold mutation, stale submit bypass, broker/order guard 완화, provider/bot/cap 변경, real execution quality approval을 열지 않는다.
  - 다음 액션: `runtime_env_reflected_and_verified`, `implemented_but_runtime_not_selected`, `source_only_no_runtime_authority`, `blocked_by_apply_guard`, `report_missing_or_stale`, `verify_missing_or_failed` 중 하나로 닫는다.
  - 사전 확인 (`2026-07-20 07:58 KST`): `not_yet_due`. 기존 operator lock 소유 family `rising_missed_normal_buy_bridge`는 apply plan selected 및 runtime env/process의 `KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED=true`로 반영됐다. 반면 workorder 2건은 모두 `runtime_effect=false`, `allowed_runtime_apply=false`이고 bridge discovery는 `source_missing`, candidate `0`이다. `08:55~09:00` window에서 프로세스/env 상태를 다시 확인해 runtime 반영과 source-only 비권한을 최종 확정한다.

- [ ] `[OpeningRotationFreshnessEnvelopePreopen0720] OPENING_ROTATION_1PCT freshness envelope 프로세스 반영 및 provenance 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 08:55~09:00`, `Track: ScalpingLogic`)
  - Source: [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [opening_rotation.py](/home/ubuntu/KORStockScan/src/engine/scalping/opening_rotation.py), [market_data_enrichment.py](/home/ubuntu/KORStockScan/src/engine/scalping/market_data_enrichment.py), [test_opening_rotation.py](/home/ubuntu/KORStockScan/src/tests/test_opening_rotation.py)
  - 판정 기준: 신규 프로세스가 변경 코드를 적재했는지 확인하고 `opening_rotation_freshness_envelope_ready`, `market_data_freshness_state`, `market_data_effective_price_source`, effective/WS/REST quote age와 tick context provenance가 `opening_rotation_1pct_observed|qualified` 이벤트에 기록되는지 확인한다. 유효한 `fresh_ws` 또는 1.5초 이내 `rest_enriched`는 진입 평가를 계속하고 `conflicted`, 시간 기준 불명, 양쪽 stale, stale tick context는 패턴 상태를 갱신하지 않고 차단해야 한다.
  - 금지: AI 점수를 하드게이트로 사용하거나 REST signed tape/호가를 단독 BUY 근거로 사용하지 않는다. stale quote, broker/account/order/quantity/cooldown guard를 우회하거나 threshold/provider/cap/bot 상태를 장중 변경하지 않는다.
  - 다음 액션: `process_reflected_and_envelope_active`, `process_not_restarted`, `freshness_provenance_missing`, `valid_envelope_overblocked`, `stale_or_conflicted_envelope_bypassed` 중 하나로 닫는다.
  - 사전 확인 (`2026-07-20 07:58 KST`): `not_yet_due`. PID `14924`가 신규 기동되어 opening rotation 모듈을 포함한 변경 코드를 적재했고 계좌 동기화/WS 연결이 정상이다. fresh WS, bounded REST envelope, expired/conflicted/unknown-time-basis 차단, provenance 보존, AI score 비권한, broker-accept 이후 tag 활성화 집중 테스트 `8 passed`를 확인했다. `08:55~09:00` window에서 프로세스 생존과 provenance contract를 다시 확인해 최종 판정한다.

- [x] `[RisingMissedLowReboundLatencyRecovery0720] 한미반도체 missed-upside 기반 low-rebound latency band 보완 및 런타임 확인` (`Due: 2026-07-20`, `Slot: PREOPEN`, `TimeWindow: 08:29~08:50`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)
  - 판정 기준: `042700`은 08:16 관측가 225,000원에서 08:24 TP1 selector 통과 후 spread 108.46bp latency DANGER로 차단됐으나 08:28 237,000원 이상으로 상승했다. selector low-rebound 및 watch-anchor provenance를 submit context에 보존하고, 90~120bp 구간에서 fresh trusted WS, true OFI sample>=60, true OFI>=0, confidence>=0.8, pressure>=49, depth ratio>=1.05, support>=2, low rebound>=2.5%, latest signed WS tick BUY를 만족할 때만 bounded latency relief가 적용되는지 확인한다.
  - 금지: stale quote, non-spread latency reason, >120bp spread, unknown/REST positive tape, bearish micro, large sell, explicit AI veto, broker/account/order/quantity/cooldown, sizing/cap/provider/TP/exit, hard/protect/emergency guard를 우회하지 않는다.
  - 다음 액션: `runtime_reflected_and_observed`, `runtime_reflected_no_natural_match`, `review_or_test_failed`, `rollback_required` 중 하나로 닫는다. rollback은 `KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_LOW_REBOUND_RECOVERY_ENABLED=false`이다.
  - 실행 결과 (`2026-07-20 08:50 KST`): `runtime_reflected_no_natural_match`. PID `25809` 구간에서 `042700`은 08:24 current=230,000원, spread=108.46bp, WS age=13.3ms, true OFI sample=74/75, low rebound=2.68%였지만 promotion anchor reset으로 delta=0이 되어 latency 차단됐고 08:28~08:50에는 237,000~238,000원을 관측했다. selector의 low-rebound/watch-anchor를 submit context에 보존하고 90~120bp 전용 bounded recovery를 구현했다. review gate에서 stale context, unknown/REST tape, bearish micro, base-band sample floor 누수를 차단했으며 latency 테스트 `137 passed`, submit-context 테스트 `2 passed`, compile/env syntax/parser/`git diff --check`를 통과했다. PID `39824`로 우아한 재기동했고 runtime verifier와 env handoff가 pass했다. 재기동 직후 08:40 BUY window가 종료되어 08:50까지 신규 TP1 natural match는 `0`이었으며 프로세스 오류나 broker 제출은 없었다.

## 장중 체크리스트 (09:05~15:20)

- [x] `[RisingMissedRuntimeMonitor1200] 재기동 이후 TP1·submit·scale-in·exit counterfactual 종합 점검` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 10:27~12:00`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [rising_missed_intraday_feedback_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-20.json), [post_sell_candidates_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-07-20.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
  - 판정 기준: PID `94253` 재기동 이후 12:00까지 TP1 pass/block/defer, WS micro 결측, REST budget/cache defer, counterfactual MFE/MAE, submit-safety/broker, entry multi-leg/reprice, shallow avg down, dynamic latency, reversal guards, high-peak trailing continuation을 동일 시간축으로 집계한다. 명백한 지속상승 winner를 정상 threshold가 반복 차단하면 날짜 제한 bounded 완화를 검토한다.
  - 금지: stale/conflicted quote, broker/account/order/quantity/cooldown, hard/protect/emergency stop을 우회하거나 사후 최고가 하나만으로 전역 threshold를 일괄 완화하지 않는다. 장중 변경은 사용자 지시에 따라 허용하되 review gate와 rollback guard를 반드시 닫는다.
  - 다음 액션: `runtime_healthy_no_change`, `bounded_intraday_relief_applied`, `rollback_required`, `source_quality_blocked` 중 하나로 닫는다.
  - 중간 보완 (`2026-07-20 11:10~12:10 KST`): 삼성공조 `006660`은 strong TP1 micro 이후 상대 tick acceleration 차단이 반복됐고 10:55 차단 후 MAE=0.00%, MFE=+5.51%였다. 당시 최근 5틱은 2초, 전체 10틱 window는 3초로 절대 처리량은 충분했고 fresh WS age=278ms, bullish orderbook, QI=0.92, OFI norm=+5.15였다. 오늘 한정으로 상대 acceleration만 약하고 absolute throughput, fresh quote, positive current micro, fresh TP1 support, large-sell 없음이 모두 충족될 때 다음 submit-safety로 넘기는 bounded relief를 구현했다. 11:53에는 동일 초 10틱, quote age=87ms, OFI norm=+2.03, TP1 support=4였으나 QI=0.012의 neutral depth가 차단했고 이후 MAE=0.00%, MFE=+4.26%였으므로, same-second burst + OFI norm>=1.2 + support>=3도 positive current micro로 인정하되 이후 reversal/latency/broker guard는 유지한다. rollback은 `KORSTOCKSCAN_RISING_MISSED_TICK_ABSOLUTE_THROUGHPUT_RELIEF_ENABLED=false`이다.
  - 실행 결과 (`2026-07-20 12:10 KST`): `bounded_intraday_relief_applied`. 10:27:50~12:00 TP1 terminal evaluation은 pass=70, block=78, defer=4이며 block은 lane-not-eligible=36, insufficient-positive-support=21, AI-state-blocked=21, defer는 WS/REST conflict=2와 WS micro unavailable=2였다. effective source는 WS=145, REST quote=5, conflict=2이고 WS micro provenance 미준비는 1/152(0.66%), REST budget/cache exhaustion defer는 0건이었다. downstream은 source-gap relief=13, weak-AI micro block=18, tick-speed block=13, latency pass/block=7/32, pre-submit AI authority block=5, broker bundle=2였다. first-hit label은 gross-target-first=11, adverse-stop-first=20, no-hit=36, pending=15로 전역 완화 근거는 없었지만, 삼성공조의 fresh absolute-throughput false-negative 두 건은 별도 bounded relief 근거가 됐다. SK이터닉스는 2-leg, 피코그램은 3-leg request/sent가 모두 실행됐고 피코그램 first market leg 139주가 1,443원에 체결된 뒤 residual 69/70주는 1,425/1,418원 passive로 유지됐다. window 내 reprice는 0건이고 shallow avg-down은 피코그램 -0.16%, hold 22초로 pnl/hold 범위 밖이라 미실행이 적정했다. reversal pre-submit block은 0건이며 post-window 피코그램 high-peak trailing은 quote age=3.155초와 AI/feature 결측으로 recheck를 열지 않고 +1.22%에 청산돼 stale bypass는 발생하지 않았다. review gate는 sniper `771 passed`, compile/Black/env syntax/parser/`git diff --check`를 통과했고 PID `117782 -> 150330` 재기동 및 runtime handoff가 pass했다.

- [x] `[RisingMissedStrongMicroSourceGapRelief0720] 원익IPS missed-upside 기반 weak-AI legacy source-gap 보완 및 런타임 확인` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 09:38~10:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [rising_missed_intraday_feedback_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/rising_missed_intraday_feedback/rising_missed_intraday_feedback_2026-07-20.json), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)
  - 판정 기준: `240810`은 09:38:37 TP1 pass 당시 fresh trusted WS micro, support=2, confidence=0.85, true OFI=+0.0067, pressure=88.24, top-depth ratio=7.91이었으나 제출 단계의 legacy `buy_pressure_10t` 결측으로 `source_quality_unknown` 차단됐고 이후 block mark 대비 MFE=+9.52%, MAE=0.00%였다. 오늘 한정 strong-micro source-gap relief가 같은 강한 TP1 context를 보존하고 legacy 필드 결측만 대체하는지 확인한다.
  - 금지: measured bearish/strong-bearish submit micro, stale/REST positive micro, latency, price-gap, tick-speed, reversal, liquidity, broker/account/order/quantity/cooldown, sizing/cap/provider/TP/exit, hard/protect/emergency guard를 우회하지 않는다. 09:39:22 `240810`처럼 current=140,400원, resolver order=129,400원인 chase context는 복구 대상이 아니다.
  - 다음 액션: `runtime_reflected_and_observed`, `runtime_reflected_no_natural_match`, `review_or_test_failed`, `rollback_required` 중 하나로 닫는다. rollback은 `KORSTOCKSCAN_RISING_MISSED_TP1_STRONG_MICRO_SOURCE_GAP_RELIEF_ENABLED=false`이다.
  - 실행 결과 (`2026-07-20 10:20 KST`): `runtime_reflected_no_natural_match`. TP1 pass context의 trusted WS micro confidence/true OFI/pressure/top-depth provenance를 submit context에 보존하고, support>=2, confidence>=0.8, true OFI>0, pressure>=60, depth ratio>=1.5를 모두 만족할 때 legacy `buy_pressure_10t` 결측만 대체하도록 구현했다. measured bearish/strong-bearish submit orderbook과 active-date 불일치는 fail-closed한다. review gate에서 sniper scale-in `768 passed`, latency `137 passed`, compile/env syntax/parser/`git diff --check`를 통과했고 PID `39824 -> 85259` 재기동 및 runtime env handoff가 pass했다. 10:20까지 신규 strong-micro source-gap natural match는 `0`이며 프로세스·WS·스캐너·entry multi-leg/broker 경로는 정상이다.

- [x] `[ScalpHighPeakTrailingContinuationReview0720] 기가레인 조기청산 기반 high-peak trailing continuation 공백 보완` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 10:21~10:45`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [post_sell_candidates_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/post_sell/post_sell_candidates_2026-07-20.jsonl), [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py), [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)
  - 판정 기준: `049080`은 09:54 peak=+2.12%, signal=+0.78%, AI HOLD=78에서 trailing 전량청산 후 09:55 재포착가 12,270원으로 sell 12,050원 대비 +1.83% 반등했다. 기존 continuation recheck가 peak<=1.50%, worsen<=0.90%에만 적용되어 high-peak 후보를 무로그 제외하는지 확인하고, high-peak 전용 bounded confirmation 또는 partial runner가 기회비용을 줄이는지 counterfactual로 비교한다.
  - 금지: hard/protect/emergency stop, stale/conflicted quote safety, broker/account/order/quantity guard를 우회하거나 단일 종목의 사후 고가만으로 전역 trailing threshold를 일괄 확대하지 않는다. current trusted micro의 명시적 large sell 또는 지속 bearish 확인은 보존한다.
  - 다음 액션: `high_peak_recheck_implemented`, `partial_runner_candidate`, `insufficient_counterfactual_evidence`, `rollback_required` 중 하나로 닫는다.
  - 실행 결과 (`2026-07-20 10:28 KST`): `high_peak_recheck_implemented`. 기존 shallow lane은 유지하고 peak 1.50~3.50%, profit>=+0.40%, worsen<=1.50%p, AI>=75, quote age<=1.5초, trusted signed tick>=3, large-sell 없음인 trailing take-profit 후보에만 10초 1회 bounded confirmation을 추가했다. smoothed bearish estimator는 단독 전량청산 권한으로 사용하지 않지만 stale quote 또는 large-sell은 즉시 fail-closed한다. high-peak ineligible 원인도 pipeline에 기록한다. review gate에서 holding/exit 및 source-quality `33 passed`, sniper scale-in `768 passed`, compile/env syntax/Black/parser/`git diff --check`를 통과했고 PID `85259 -> 94253` 재기동, runtime env handoff 및 프로세스 env 9개 키 적재가 pass했다. 초기 WS/계좌/스캐너가 정상이며 신규 natural exit match는 아직 없다.

- [ ] `[RisingMissedLowReboundLatencyRecoveryObserve0720] low-rebound latency recovery 자연 표본 및 guard provenance 확인` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: ScalpingLogic`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py), [operator_runtime_overrides.env](/home/ubuntu/KORStockScan/data/threshold_cycle/runtime_env/operator_runtime_overrides.env)
  - 판정 기준: 신규 BUY window에서 `latency_true_ofi_direct_canary_low_rebound_recovery_active=true`가 기록되고 natural match가 있으면 applied/pass 이후 기존 submit-safety와 broker 결과를 확인한다. natural match가 없으면 분모와 함께 `no_natural_match`로 닫는다.
  - 금지: stale/unknown provenance, REST positive tape, bearish micro, large sell, >120bp spread, broker/account/order/quantity/cooldown guard를 우회하거나 natural match가 없다는 이유로 threshold를 추가 완화하지 않는다.
  - 다음 액션: `natural_match_applied_submit_safe`, `natural_match_blocked_by_downstream_guard`, `no_natural_match`, `provenance_missing`, `rollback_required` 중 하나로 닫는다.

- [ ] `[RuntimeEnvIntradayObserve0720] 전일 selected runtime family 장중 provenance 및 rollback guard 확인` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 09:05~09:20`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-16.json)
  - 판정 기준: selected_families=soft_stop_whipsaw_confirmation, scale_in_split_order_plan, score65_74_recovery_probe, scalping_scanner_real_source_guard_runtime, score65_74_recovery_probe_strong_micro_override_runtime, entry_price_gap_profile_runtime, profit_stagnation_exit_runtime, latency_spread_relief_real_operator_override, quote_consistency_normalization, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, ai_watching_score_smoothing_report_only, lifecycle_decision_matrix_runtime, weak_pullback_entry_block_runtime, early_accel_recheck_runtime, real_pyramid_scale_in_quality_guard_runtime, sell_side_open_time_block_runtime, pre_submit_liquidity_relief_runtime, entry_opportunity_recheck_runtime, weak_context_late_entry_guard_runtime, rising_missed_normal_buy_bridge, persistent_operator_overrides_2026_06_26가 runtime event provenance에 찍히는지 확인한다.
  - 금지: 장중 관찰 결과로 runtime threshold mutation을 수행하지 않는다.
  - 다음 액션: provenance present/missing, rollback guard breach 여부를 분리 기록한다.

- [ ] `[SimProbeIntradayCoverage0720] sim/probe 관찰축 actual_order_submitted=false 및 source-quality 확인` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 09:35~09:50`, `Track: ScalpingLogic`)
  - Source: [threshold_cycle_ev_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-16.json)
  - 판정 기준: sim/probe 표본이 real execution과 분리되고 `actual_order_submitted=false` provenance가 유지되는지 확인한다.
  - 금지: sim/probe EV를 broker execution 품질이나 실주문 전환 근거로 단독 사용하지 않는다.
  - 다음 액션: source-quality split, active state 복원, open/closed count를 같이 기록한다.

- [ ] `[IntradaySourceQualityGateCheck0720] 장중 raw source-quality 결손/unknown 조기 경보 및 튜닝 입력 차단 준비 확인` (`Due: 2026-07-20`, `Slot: INTRADAY`, `TimeWindow: 14:20~14:35`, `Track: RuntimeStability`)
  - Source: [pipeline_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-20.jsonl), [threshold_events_2026-07-20.jsonl](/home/ubuntu/KORStockScan/data/threshold_cycle/threshold_events_2026-07-20.jsonl), [observation_source_quality_audit_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-20.json), [observation_source_quality_audit.py](/home/ubuntu/KORStockScan/src/engine/observation_source_quality_audit.py)
  - 판정 기준: 장중 `PYTHONPATH=. .venv/bin/python -m src.engine.observation_source_quality_audit --target-date 2026-07-20 --write` 재감사를 실행하거나 최신 산출물을 확인해 `hard_blocking_contract_gap_count`, `hard_blocking_excluded_row_count`, `tuning_input_allowed`, `raw_row_exclusion_applied`, `unknown_token_stage_count`, `review_warning_count`를 기록한다.
  - 금지: hard contract gap 또는 unknown-token warning을 답변에만 남기지 않는다. 결손 row/window는 튜닝 입력 제외 또는 workorder handoff 대상으로 고정하고, broker/order/provider/cap/bot/threshold 변경 근거로 사용하지 않는다.
  - 다음 액션: `source_quality_clean_intraday`, `defective_rows_excluded`, `hard_block_requires_producer_fix`, `unknown_warning_workorder_required`, `audit_missing_or_stale` 중 하나로 닫는다. hard gap/unknown warning이 있으면 장후 `PostcloseSourceQualityGateReview`와 `CodeImprovementWorkorderReview`에서 누락 없이 재확인한다.

## 장후 체크리스트 (20:05~21:55)

- [ ] `[PostcloseSourceQualityGateReview0720] 장후 source-quality gate 결과 및 튜닝 입력 허용/제외 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:25~16:35`, `Track: RuntimeStability`)
  - Source: [observation_source_quality_audit_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-20.json), [threshold_cycle_ev_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-20.json), [code_improvement_workorder_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-20.json), [threshold_cycle_postclose_verification_2026-07-20.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-20.json)
  - 판정 기준: postclose EV/report 소비 전후 `observation_source_quality_audit`의 hard block, row exclusion, clean baseline, unknown-token review warning을 확인한다. `hard_blocking_contract_gap_count>0`이면 결손 row/window 제외 또는 `source_quality_blocked` 산출 여부를 확인하고, `unknown_token_stage_count>0`이면 source-quality producer-fix workorder가 생성됐는지 확인한다.
  - 금지: source-quality preflight missing/stale, row exclusion 실패, hard block candidate 생성, unknown-token workorder handoff 누락을 정상 postclose 완료로 처리하지 않는다. sim/combined EV, live-auto promotion, runtime approval, LDM, threshold apply candidate에 결손 row/window가 섞이면 fail로 닫는다.
  - 다음 액션: `source_quality_gate_pass`, `defective_rows_excluded_and_ev_allowed`, `source_quality_blocked`, `unknown_warning_workorder_created`, `handoff_missing_fix_automation_first` 중 하나로 닫는다.

- [ ] `[ThresholdDailyEVReport0720] daily EV real/sim/combined split 및 자동 반영 결과 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~16:45`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-16.json)
  - 판정 기준: threshold cycle EV를 보고 `live_auto_apply_ready`, `sim_auto_approved`, post-apply attribution, EV authority를 분리해 확인한다.
  - 금지: sim/combined EV만으로 broker execution 품질이나 live 전환을 확정하지 않는다.
  - 다음 액션: 다음 장전 apply 입력으로 쓸 수 있는 항목과 hold_sample/freeze 항목을 분리한다.

- [ ] `[HumanInterventionSummary0720] 자동화체인 사용자 개입 요구사항 분류 및 누락 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 17:00~17:15`, `Track: RuntimeStability`)
  - Source: [threshold_cycle_ev_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-16.json), [time-based-operations-runbook.md](/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
  - 판정 기준: 개입사항을 `approval_artifact_required|created|missing|blocked_by_policy|observe_only`, `Codex 구현 필요`, `수동 동기화 필요`, `관찰만`으로 분류한다.
  - 금지: approval request만 보고 env 파일을 직접 수정하지 않고, 자동화 산출물에 있는 요청을 답변에만 남기고 checklist/Project 대상에서 누락하지 않는다.
  - 다음 액션: approval request가 있으면 `approval_id`, 후보/대상, artifact path, 승인 여부, 다음 PREOPEN 적용 확인 항목을 남긴다. 누락된 항목이 있으면 다음 영업일 checklist에 parser-friendly checkbox로 추가한다.

- [ ] `[CodeImprovementWorkorderReview0720] code improvement workorder 구현 필요 여부 및 Codex 지시 대상 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:15~21:25`, `Track: ScalpingLogic`)
  - Source: [code_improvement_workorder_2026-07-16.md](/home/ubuntu/KORStockScan/docs/code-improvement-workorders/code_improvement_workorder_2026-07-16.md), [code_improvement_workorder_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-16.json)
  - 판정 기준: selected_order_count=108와 `implement_now`, `attach_existing_family`, `design_family_candidate`, `reject` 분류를 확인하고, 비-implement 반복 항목이 `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design` 중 무엇으로 닫혀야 하는지 분리한다.
  - 금지: code-improvement workorder를 자동 repo 수정으로 취급하지 않는다. 사용자가 Codex 구현을 지시한 경우에만 실행한다.
  - 다음 액션: `implement_now`, `terminal_non_implement_longstanding`, `repeat_unresolved_structural_blocker`, `keep_visible_by_design`, `already_implemented`, `defer_design`, `reject` 중 하나로 닫는다.

- [ ] `[LifecycleQuietGapReview0720] lifecycle quiet gap rollup 자동 표면화 및 처리 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:25~21:40`, `Track: ScalpingLogic`)
  - Source: [runtime_apply_gap_audit_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-16.json), [runtime_apply_gap_audit_2026-07-16.md](/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-16.md)
  - 판정 기준: quiet gap summary의 quiet_gap_count=`242`, rollup_required_count=`242`, sim_live_connected_quiet_gap_count=`0`, observation_source_quality_warning_count=`0`, quiet_gap_type_counts=`{'ai_review_parsed_low_coverage': 1, 'positive_source_only_keep_collecting': 241}`를 확인하고 parent conflict/exclusion, positive source-only, source-quality warning, AI coverage 누락을 닫는다.
  - 금지: quiet gap을 threshold/env/provider/order/bot 변경 근거로 사용하지 않는다.
  - 다음 액션: `rollup_only`, `implement_now`, `already_covered_by_parent_policy`, `defer_until_more_sample`, `reject_not_applicable` 중 하나로 닫는다.

- [ ] `[AutomationTriggerDecisionSummary0720] 자동화체인 trigger decision run/skip 요약 및 wrapper marker 대조 확인` (`Due: 2026-07-20`, `Slot: POSTCLOSE`, `TimeWindow: 21:40~21:55`, `Track: RuntimeStability`)
  - Source: [automation_chain_trigger_decision_2026-07-16.json](/home/ubuntu/KORStockScan/data/report/automation_chain_trigger_decision/automation_chain_trigger_decision_2026-07-16.json), [run_threshold_cycle_postclose.sh](/home/ubuntu/KORStockScan/deploy/run_threshold_cycle_postclose.sh)
  - 판정 기준: trigger decision summary의 total_steps=`16`, run_count=`16`, skip_count=`0`, source_missing_count=`7`, force_override_count=`0`, run_steps_sample=`lifecycle_window_rolling5d, lifecycle_window_rolling10d, lifecycle_window_mtd, scalp_sim_ai_deferred_review, pattern_lab_currentness_audit`, skip_steps_sample=`-`, top_reasons=`output_missing_or_unreadable:15, source_missing_or_unreadable:7, upstream_drift_signal:7, upstream_artifact_newer:1`를 확인하고 wrapper 로그의 `[SKIP] threshold-cycle postclose ... trigger_decision=skip` marker와 대조한다.
  - 금지: trigger decision을 PREOPEN apply, final verifier, broker/order/provider/cap/bot/threshold, hard-safety/source-quality fail-closed 경계 변경 근거로 사용하지 않는다.
  - 다음 액션: `trigger_contract_pass`, `unexpected_all_run`, `skip_marker_missing`, `source_missing_run_required`, `force_override_detected`, `needs_followup_patch` 중 하나로 닫는다.

<!-- AUTO_NEXT_STAGE2_CHECKLIST_END -->

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-07-20 15:46:50`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-07-20.md`
- `Trade Review`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
