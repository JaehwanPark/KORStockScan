# Sim-to-Live Automation Contract Audit - 2026-05-15

## 판정

`simulation/probe 결과 -> live 반영` 계약 전수 점검 결과, 즉시 보정이 필요한 실제 누락은 스윙 `swing_one_share_real_canary_phase0` 연결부였다. 이 축은 기존 문서에 정책은 있었지만 `approval request -> 별도 approval artifact -> preopen env -> runtime initial BUY guard`가 닫히지 않아 1주 canary도 허용할 수 없었다.

현재 보정 후 상태는 `pre_final_auto_approval_default_off`다. 기본값은 OFF이며, swing dry-run env는 hard floor/source-quality와 parsed AI Tier2 review가 닫힌 `dry_run_auto_apply_ready`일 때만 사용자 artifact 없이 다음 PREOPEN env를 생성한다. env가 생성되어도 `SWING_LIVE_ORDER_DRY_RUN_ENABLED=true`는 유지된다. 승인된 phase0 real canary도 parsed AI Tier2 review와 source hard floor/source-quality/cap/allowlist가 닫힌 경우에만 1주 초기 BUY/해당 포지션 청산 SELL 또는 승인된 real holding의 1주 scale-in execution 품질을 real-only로 수집한다. 이는 스윙 전체 실주문 전환, cap 해제, provider/bot 변경 근거가 아니다.

추가 확인 결과, 모든 approval 후보가 “artifact 생성 후 바로 live 가능”한 것은 아니다. `position_sizing_cap_release`는 final user approval 전용이며, `position_sizing_dynamic_formula`, `panic_entry_freeze_guard`, `panic_buy_runner_tp_canary`는 조건이 충족되어도 현재 코드베이스에는 artifact loader, preopen env mapping, runtime guard, rollback test가 준비돼 있지 않다. 이 축들은 `approval_contract_status=final_user_approval_required` 또는 `contract_missing`, `approval_live_ready=false`, `approval_contract_missing_components=[...]`로 리포트에 표면화한다. 즉 조건 충족을 조용히 먹지 않고, 승인 artifact를 만들어도 아직 live 반영할 수 없는 상태를 명시한다.

## 근거

| 축 | sim/probe 결과 권한 | approval request | approval artifact | preopen env/apply | runtime guard | 판정 |
| --- | --- | --- | --- | --- | --- | --- |
| 스캘핑 threshold auto-bounded family | completed real/sim split과 rolling/window policy 기준 후보 입력 | daily threshold 후보 | 해당 없음. deterministic/AI/safety guard가 승인자 | `threshold_cycle_preopen_apply`가 selected family만 runtime env 생성 | 각 family runtime guard | 연결됨 |
| `score65_74_recovery_probe` | BUY 신호 자체 확대가 아니라 selected family 여부와 window policy에 따른 후보 | threshold candidate | 해당 없음 | rolling primary가 `hold/no_runtime_env_override`이면 env 없음 | 기존 score/probe guard | 연결됨. 현재 미오픈은 정책 판정 |
| `scalp_ai_buy_all_live_simulator` | `actual_order_submitted=false` sim EV/source-quality 입력 | 직접 live request 없음 | 없음 | 없음 | broker order forbidden | 의도적 diagnostic/sim-only |
| 스윙 dry-run runtime approval (`swing_model_floor`, `swing_gatekeeper_reject_cooldown` 등) | closed sim lifecycle + real completed trade-off로 pre-final 후보 생성 | `swing_runtime_approval_YYYY-MM-DD.json` | 사용자 artifact 없음. parsed AI Tier2가 승인자 | `dry_run_auto_apply_ready`만 env override. global dry-run 강제 유지 | 스윙 주문은 dry-run/probe로 차단 | 연결됨 |
| `swing_one_share_real_canary_phase0` | 후보 우선순위와 expected EV trade-off에는 combined 사용. execution quality는 real-only 필요 | parsed AI Tier2 `swing_runtime_approval`이 별도 request 생성 | optional `data/threshold_cycle/approvals/swing_one_share_real_canary_YYYY-MM-DD.json` | 승인 종목/cap만 env 생성, global dry-run 유지 | 승인 code allowlist, qty=1, daily/open/notional cap, stale/bearish submit 차단 | 보정 완료 |
| `swing_scale_in_real_canary_phase0` | arm별 closed sim/probe scale-in outcome과 OFI/QI quality 입력 | parsed AI Tier2와 arm hard floor 통과 시 request | optional `data/threshold_cycle/approvals/swing_scale_in_real_canary_YYYY-MM-DD.json` | 승인 arm/cap만 env 생성, global dry-run 유지 | 승인된 real swing holding만 1주 추가매수 | 연결됨. 현재는 source-quality/outcome blocker가 우선 |
| `position_sizing_cap_release` | sim/probe EV와 cap opportunity는 승인 요청 근거 | 조건 충족 시 final request 후보 | `final_user_approval_required`로 표시 | preopen env apply는 사용자 최종 승인 전 금지 | runtime cap 확대 guard 필요 | final user approval 없이는 live 불가 |
| `position_sizing_dynamic_formula` | 산식 후보 source bundle/workorder 근거 | 조건 충족 시 request 후보 | `contract_missing`으로 표시 | preopen env apply 미구현 | runtime formula guard 미구현 | approval artifact를 만들어도 바로 live 불가 |
| `panic_entry_freeze_guard` | panic sell report, sim/probe avoided-loss/missed-upside는 후보 근거 | workorder/approval 후보 | `contract_missing`으로 표시 | env key mapping/loader 미구현 | runtime pre-submit freeze 미구현 | approval artifact를 만들어도 바로 live 불가 |
| `panic_buy_runner_tp_canary` | TP counterfactual과 panic-buy source-quality는 후보 근거 | workorder/approval 후보 | `contract_missing`으로 표시 | env key mapping/loader 미구현 | TP/runner runtime guard 미구현 | approval artifact를 만들어도 바로 live 불가 |
| source-quality blockers | stale/missing/coverage는 blocker 또는 workorder 입력 | runtime request가 아니라 blocker | 없음 | 없음 | 없음 | 의도적 source-quality-only |

현재 policy에서는 phase0 real canary request가 parsed AI Tier2 review와 source report hard floor/source-quality/cap/allowlist를 통과하면 optional narrowing artifact 없이도 auto approval될 수 있다. Optional artifact가 있으면 승인 종목/arm/cap을 더 좁히는 용도로만 쓴다.

## 다음 액션

1. 스윙 dry-run env 후보는 parsed AI Tier2 없이는 fail-closed로 남긴다.
2. 다음 장전 `threshold_cycle_preopen_apply`가 pre-final auto artifact 또는 optional narrowing artifact를 소비해 `KORSTOCKSCAN_SWING_*` env를 만들었는지 확인한다.
3. 첫 실행 후에는 broker receipt, order number binding, fill ratio, slippage, cancel/timeout, sell receipt를 real-only로만 판정한다.
4. `position_sizing_cap_release`는 `approval_contract_status=final_user_approval_required`로 남긴다. `position_sizing_dynamic_formula`, `panic_entry_freeze_guard`, `panic_buy_runner_tp_canary`는 `approval_contract_status=contract_missing`으로 남긴다. 실제 적용하려면 해당 축별 approval artifact loader, env mapping, runtime guard, rollback 테스트를 새 작업으로 연다.
