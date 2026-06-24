# Scalp Sim AI Deferred Review 2026-06-24

- generated_at: `2026-06-24T20:16:35`
- source: `/home/ubuntu/KORStockScan/data/pipeline_events/pipeline_events_2026-06-24.jsonl`
- artifact_role: `postclose_source_packet_for_sim_ai_quality_review`
- runtime_effect: `false`
- decision_authority: `sim_observation_only`
- deferred_count: `9`

## Defer Reasons

- `sim_ai_budget_exhausted`: `9`

## Critical Classes

- `non_critical`: `1`
- `soft_critical`: `8`

## Critical Reasons

- `feature_signature_changed`: `8`
- `legacy_critical_zone`: `8`
- `near_safe_profit_band`: `2`
- `normal_review`: `1`
- `soft_loss`: `2`

## Deferred Rows

| time | stock | reason | critical_class | critical_reason | profit | peak | drawdown | held_sec |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 2026-06-24T09:31:07.683454 | 계양전기(012200) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +4.81 | +4.81 | 0.0 | 394 |
| 2026-06-24T09:42:18.173607 | 두산로보틱스(454910) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.29 | +1.29 | 0.0 | 1200 |
| 2026-06-24T09:42:18.182931 | SK네트웍스(001740) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.70 | +1.70 | 0.0 | 571 |
| 2026-06-24T09:47:11.936822 | 두산로보틱스(454910) | `sim_ai_budget_exhausted` | `soft_critical` | `feature_signature_changed,legacy_critical_zone` | +1.61 | +1.61 | 0.0 | 1493 |
| 2026-06-24T09:47:11.954515 | SK네트웍스(001740) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.33 | -0.13 | 0.2 | 865 |
| 2026-06-24T12:35:02.190257 | 셀트리온(068270) | `sim_ai_budget_exhausted` | `soft_critical` | `soft_loss,feature_signature_changed,legacy_critical_zone` | -0.17 | -0.17 | 0.0 | 241 |
| 2026-06-24T12:43:22.784587 | 엘앤씨바이오(290650) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.85 | +0.85 | 0.0 | 1090 |
| 2026-06-24T16:54:38.029385 | 에이프릴바이오(397030) | `sim_ai_budget_exhausted` | `non_critical` | `normal_review` | +0.01 | +0.01 | 0.0 | 1105 |
| 2026-06-24T19:46:50.041848 | 광주신세계(037710) | `sim_ai_budget_exhausted` | `soft_critical` | `near_safe_profit_band,feature_signature_changed,legacy_critical_zone` | +0.80 | +1.03 | 0.23 | 628 |
