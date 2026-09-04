# Entry Split Order Plan - 2026-09-04

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `0`
- runtime_apply_allowed: `False`
- exploration_seed_allowed: `False` / count: `0`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `[]`
- policy_version: `entry_split_order_plan:2026-09-04:97d170e155`
- artifact_generation_id: `943939cc273644ea65b93a4d366c5454b8f945ee0999d7cbb125ff905303c728`
- baseline_runtime_defaults_enabled: `False`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-09-04.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`39/0` ev=`None` bucket_ev=`-0.6835` observed_split_outcomes=`26` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`95/0` ev=`None` bucket_ev=`-0.4422` observed_split_outcomes=`69` apply_scope=`none` apply_authority=`none` p75_down_ticks=`5.0` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`-` real/sim=`179/410133` ev=`None` bucket_ev=`-0.006` observed_split_outcomes=`50` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/29` ev=`None` bucket_ev=`0.62` observed_split_outcomes=`1` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
