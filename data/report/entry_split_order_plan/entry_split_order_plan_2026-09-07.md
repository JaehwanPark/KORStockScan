# Entry Split Order Plan - 2026-09-07

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `0`
- runtime_apply_allowed: `False`
- exploration_seed_allowed: `False` / count: `0`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `[]`
- policy_version: `entry_split_order_plan:2026-09-07:97d170e155`
- artifact_generation_id: `97f4b05d2866022613f50c1a95b380d5b2acb461b18e7d0bbfa7ffe320014c6a`
- baseline_runtime_defaults_enabled: `False`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-09-07.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`39/0` ev=`None` bucket_ev=`-0.6835` observed_split_outcomes=`26` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`97/0` ev=`None` bucket_ev=`-0.4097` observed_split_outcomes=`71` apply_scope=`none` apply_authority=`none` p75_down_ticks=`15.75` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`-` real/sim=`179/414503` ev=`None` bucket_ev=`-0.006` observed_split_outcomes=`50` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/29` ev=`None` bucket_ev=`0.62` observed_split_outcomes=`1` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
