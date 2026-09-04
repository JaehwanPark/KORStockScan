# Entry Split Order Plan - 2026-09-03

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `2`
- runtime_apply_allowed: `True`
- exploration_seed_allowed: `True` / count: `2`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `['bounded_exploration_seed']`
- policy_version: `entry_split_order_plan:2026-09-03:fa8fd1c75a`
- artifact_generation_id: `a8c0b254201e146ed23afa31bae8a6a6744c4267ecd7e2429b30ae71aac6f452`
- baseline_runtime_defaults_enabled: `True`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-09-03.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`39/298` ev=`None` bucket_ev=`-0.6835` observed_split_outcomes=`26` apply_scope=`baseline_split_structure` apply_authority=`bounded_exploration_seed` p75_down_ticks=`None` cancel=`0.0` pass=`True`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`93/388` ev=`None` bucket_ev=`-0.4598` observed_split_outcomes=`68` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`bounded_equal_split_baseline` real/sim=`179/409890` ev=`None` bucket_ev=`-0.0061` observed_split_outcomes=`50` apply_scope=`baseline_split_structure` apply_authority=`bounded_exploration_seed` p75_down_ticks=`None` cancel=`0.0` pass=`True`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/681` ev=`None` bucket_ev=`0.62` observed_split_outcomes=`1` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
