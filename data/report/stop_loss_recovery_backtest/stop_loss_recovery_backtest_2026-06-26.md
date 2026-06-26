# Stop Loss Recovery Backtest 2026-06-26

- runtime_effect: `False`
- source_dates: `2026-06-04, 2026-06-05, 2026-06-08, 2026-06-09, 2026-06-10, 2026-06-11, 2026-06-12, 2026-06-15, 2026-06-16, 2026-06-17, 2026-06-18, 2026-06-19, 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25, 2026-06-26`
- exit_count: `5325`
- post_sell_evaluation_count: `2270`
- missing_post_sell_evaluation_count: `3055`

## By Exit Family
- `mfe_protect`: exits=4, eligible=4, recovery_possible=3, hard_safety=0
- `other_loss_exit`: exits=312, eligible=305, recovery_possible=2, hard_safety=7
- `preset_tp_loss_exit`: exits=186, eligible=0, recovery_possible=0, hard_safety=186
- `protect_hard_trailing`: exits=153, eligible=3, recovery_possible=3, hard_safety=150
- `scalp_hard_soft_stop`: exits=4550, eligible=2561, recovery_possible=642, hard_safety=1989
- `swing_probe_sim_exit`: exits=120, eligible=120, recovery_possible=0, hard_safety=0

## Stop Line Recommendations
- `mfe_protect`: confidence=thin_sample_directional, evaluated=4/4, recoverable_rate_evaluated=0.75, env={'KORSTOCKSCAN_SCALP_MFE_PROTECT_TRIGGER_PROFIT_PCT': '-0.3'}
- `other_loss_exit`: confidence=insufficient_evaluated_sample, evaluated=4/305, recoverable_rate_evaluated=0.5, env=-
- `preset_tp_loss_exit`: confidence=not_evaluated_hard_safety, evaluated=0/0, recoverable_rate_evaluated=0.0, env={'KORSTOCKSCAN_SCALP_PRESET_HARD_STOP_PCT': '-1.4', 'KORSTOCKSCAN_SCALP_PRESET_HARD_STOP_EMERGENCY_PCT': '-2.4'}
- `protect_hard_trailing`: confidence=thin_sample_directional, evaluated=3/3, recoverable_rate_evaluated=1.0, env={'KORSTOCKSCAN_SCALP_PROTECT_TRAILING_MIN_EXIT_PROFIT_PCT': '-0.3'}
- `scalp_hard_soft_stop`: confidence=directional_cumulative, evaluated=1270/2561, recoverable_rate_evaluated=0.5055, env={'KORSTOCKSCAN_SCALP_STOP': '-3.0', 'KORSTOCKSCAN_SCALP_HARD_STOP': '-5.0'}
- `swing_probe_sim_exit`: confidence=insufficient_evaluated_sample, evaluated=0/120, recoverable_rate_evaluated=0.0, env=-
