# Swing Strategy Discovery Sim - 2026-05-21

- generated_at: `2026-05-21T17:42:41`
- policy_version: `swing_strategy_discovery_sim_v1`
- mode: `sim_only_aggressive_exploration`
- runtime_effect: `False`
- decision_authority: `swing_sim_exploration_only`
- candidate_count: `50`
- arm_count: `400`
- selection_arm_counts: `{'diversity_exploration': 15, 'lifecycle_rank': 35}`
- block_reason_counts: `{'no_block_observed': 37, 'blocked_swing_gap': 4, 'blocked_gatekeeper_reject': 9}`
- quote_feature_coverage: `1.0`
- warnings: `['sector_theme:manual_sector_missing', 'sector_theme:sector_theme_missing']`

## Arm Set

| arm_id | entry | sizing | exit |
| --- | --- | --- | --- |
| `arm01_next_open_equal_fixed5d` | `next_open_entry` | `equal_notional` | `fixed_5d` |
| `arm02_next_open_vol_fixed10d` | `next_open_entry` | `volatility_adjusted` | `fixed_10d` |
| `arm03_pullback_equal_fixed10d` | `pullback_limit_entry` | `equal_notional` | `fixed_10d` |
| `arm04_pullback_risk_mae_time` | `pullback_limit_entry` | `risk_capped` | `mae_stop_time_stop` |
| `arm05_breakout_conf_trailing` | `breakout_confirm_entry` | `confidence_weighted` | `trailing_after_mfe` |
| `arm06_gap_fade_risk_fixed5d` | `gap_fade_entry` | `risk_capped` | `fixed_5d` |
| `arm07_pullback_vol_scale_recovery` | `pullback_limit_entry` | `volatility_adjusted` | `scale_in_recovery` |
| `arm08_breakout_risk_mae_time` | `breakout_confirm_entry` | `risk_capped` | `mae_stop_time_stop` |

## Contract

- DB tables are the source of truth; this Markdown/JSON is an audit artifact.
- `actual_order_submitted=false`, `broker_order_forbidden=true`, and `runtime_effect=false` are mandatory.
- Legacy ML is a low-weight feature/cohort, not the final selector.
- Sector/theme fields are collected in v1 and reserved as required v2 extension inputs.
