# Entry Split Order Plan - 2026-09-03

## Summary
- schema_version: `entry_split_order_plan_v1`
- runtime_effect: `False`
- recommended_policy_candidates: `0`
- runtime_apply_allowed: `False`
- exploration_seed_allowed: `False` / count: `0`
- ev_validated_runtime_apply_allowed: `False` / count: `0`
- runtime_apply_authority_classes: `[]`
- policy_version: `entry_split_order_plan:2026-09-03:97d170e155`
- artifact_generation_id: `fa787db6ab66888d6efcda6c0e138e4df37073cafd0bec6a952e3ec432b49990`
- baseline_runtime_defaults_enabled: `False`
- explicit_bucket_count: `0`
- policy_file: `/home/ubuntu/KORStockScan/data/threshold_cycle/entry_split_order_policy/entry_split_order_policy_2026-09-03.json`

## Candidate Grid
- `balanced_normal` legs=`2` mode=`-` real/sim=`39/0` ev=`None` bucket_ev=`-0.6835` observed_split_outcomes=`26` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `guarded_or_stale` legs=`1` mode=`-` real/sim=`93/0` ev=`None` bucket_ev=`-0.4598` observed_split_outcomes=`68` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `passive_wide_or_weak` legs=`2` mode=`-` real/sim=`179/409306` ev=`None` bucket_ev=`-0.006` observed_split_outcomes=`50` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
- `urgent_tight_spread` legs=`2` mode=`-` real/sim=`1/29` ev=`None` bucket_ev=`0.62` observed_split_outcomes=`1` apply_scope=`none` apply_authority=`none` p75_down_ticks=`None` cancel=`0.0` pass=`False`
