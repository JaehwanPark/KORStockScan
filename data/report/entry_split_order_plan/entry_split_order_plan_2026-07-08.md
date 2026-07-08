# Entry Split Order Plan - 2026-07-08

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `1`
- runtime_apply_allowed: `False`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-07-08.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`9/7` ev=`None` bucket_ev=`None` p75_down_ticks=`6.75` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`0/10` ev=`None` bucket_ev=`None` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`3` mode=`post_submit_tick_band_seed` real/sim=`100/5732` ev=`1.1` bucket_ev=`-1.7135` p75_down_ticks=`28.0` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`0/51` ev=`None` bucket_ev=`None` p75_down_ticks=`None` cancel=`0.0` pass=`False`
