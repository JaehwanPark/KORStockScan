# Swing Bottom Rebound Policy Auto Loop - 2026-05-28

- generated_at: `2026-05-28T21:27:00+09:00`
- decision_authority: `swing_bottom_rebound_sim_policy_auto_approval`
- runtime_effect: `False`
- broker_order_forbidden: `True`
- allowed_runtime_apply: `False`
- ai_tier2_status: `parsed`
- classification_state: `source_only_keep_collecting`
- promote_policy: `False`
- baseline_research_ev_pct: `1.423559`
- candidate_sim_bucket_ev_pct: `1.423559`
- relative_improvement: `1.0`
- sample_count: `56719`
- warnings: `['explicit_gap:No explicit candidate_source payload was provided while the promotion scope requires candidate_source_only.', 'explicit_gap:source_quality_adjusted_ev_pct is not explicitly provided; only baseline/candidate EV metrics are available.', 'explicit_gap:candidate_source=false and candidate_source_selected_count=0 leave the source-selection contract unproven.']`

## Contract

- A 1 percent improvement can auto-approve only the next sim candidate-source policy.
- This does not approve live orders, real canaries, runtime env, thresholds, providers, or bot actions.
- If Tier-2 AI is unavailable, the report keeps collecting instead of promoting.
