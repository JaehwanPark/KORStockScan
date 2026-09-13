# Entry Split Order Plan - 2026-09-11

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `1`
- runtime_apply_allowed: `True`
- exploration_seed_allowed: `True` / count: `1`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `['bounded_exploration_seed']`
- policy_version: `entry_split_order_plan:2026-09-11:a59cc28d35`
- artifact_generation_id: `a067dcac6a74440c9317768249cdebfa89a28ec33bf279b24ae1b47fd9c22bf7`
- baseline_runtime_defaults_enabled: `False`
- missing_bucket_action: `keep_original_order`
- explicit_bucket_count: `1`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-09-11.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`39/0` ev=`None` bucket_ev=`-0.6835` observed_split_outcomes=`26` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`109/0` ev=`None` bucket_ev=`-0.4103` observed_split_outcomes=`81` apply_scope=`none` apply_authority=`none` p75_down_ticks=`12.75` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`3` mode=`child_shape_positive_ev_seed` real/sim=`180/426458` ev=`0.7853` bucket_ev=`-0.0001` observed_split_outcomes=`50` apply_scope=`child_shape_bounded_seed` apply_authority=`bounded_exploration_seed` p75_down_ticks=`0.0` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/32` ev=`None` bucket_ev=`0.62` observed_split_outcomes=`1` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
