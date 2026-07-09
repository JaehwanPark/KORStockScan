# Scalp Sim AI Deferred Review 2026-07-09

- generated_at: `2026-07-09T20:16:04`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-07-09.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `12`

## Defer Reasons

- `sim_ai_budget_exhausted`: `12`

## Critical Classes

- `soft_critical`: `12`

## Critical Reasons

- `feature_signature_changed`: `12`
- `legacy_critical_zone`: `12`
- `near_safe_profit_band`: `2`
- `soft_loss`: `6`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-07-09T08:11:40.255989 | 가온칩스(399720) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.13 | +0.17 | 0.3 | 361 |
| 2026-07-09T08:14:20.717901 | 가온칩스(399720) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.98 | +0.98 | 0.0 | 521 |
| 2026-07-09T08:14:58.752185 | 한미반도체(042700) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.23 | 0.25 | 536 |
| 2026-07-09T08:15:41.676876 | 한미반도체(042700) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.48 | -0.23 | 0.25 | 579 |
| 2026-07-09T08:42:40.761618 | 삼성전기(009150) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.16 | -0.16 | 0.0 | 193 |
| 2026-07-09T08:46:10.607637 | 피에스케이(319660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.21 | +2.28 | 0.07 | 1983 |
| 2026-07-09T08:46:32.197984 | 한화시스템(272210) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.38 | -0.08 | 0.3 | 453 |
| 2026-07-09T08:47:37.660947 | 한화시스템(272210) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.08 | -0.08 | 0.0 | 519 |
| 2026-07-09T08:48:13.015186 | 피에스케이(319660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.61 | +2.61 | 0.0 | 2105 |
| 2026-07-09T08:48:48.334678 | 한미반도체(042700) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +1.01 | +1.01 | 0.0 | 2565 |
| 2026-07-09T08:48:48.348602 | 피에스케이(319660) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +2.74 | +2.74 | 0.0 | 2141 |
| 2026-07-09T10:07:06.506718 | HLB(028300) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.48 | +1.48 | 0.0 | 403 |
