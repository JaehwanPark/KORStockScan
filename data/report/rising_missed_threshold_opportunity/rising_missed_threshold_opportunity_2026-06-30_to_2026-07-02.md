# Rising missed one-share threshold opportunity aggregate

- generated_at: 2026-07-02T15:22:44+09:00
- window: 2026-06-30 to 2026-07-02
- decision_authority: source_only_threshold_opportunity_cost_aggregate_no_runtime_mutation
- runtime_effect: false
- allowed_runtime_apply: false
- forbidden_uses: runtime_threshold_mutation, stale_submit_bypass, broker_guard_bypass, order_guard_relaxation, provider_route_change, bot_restart, forced_one_share_success_counting, real_execution_quality_approval

## Decision

- Threshold opportunity-cost signal is present, but only as source-only/postclose evidence.
- The strongest clean score bucket is score 70-74; score 60-64 has many winners but negative equal-weight average after losses.
- Score rows at or above threshold that still carried below-threshold terminal text are separated as contract warnings, not clean opportunity-cost evidence.
- Mixed stale/latency/cooldown/source-quality blockers remain common, so this does not justify direct BUY score relaxation.
- Forced one-share scout outcomes are not normal BUY/submit/fill success and cannot approve real execution quality.

## Summary

- `forced_record_count`: 139
- `forced_stage_record_count`: 137
- `forced_flag_event_line_count`: 5364
- `forced_stage_event_line_count`: 2316
- `post_sell_joined_count`: 72
- `profitable_joined_count`: 47
- `loss_or_flat_joined_count`: 25
- `joined_profit`: {'sample': 72, 'valid_profit_sample': 72, 'equal_weight_avg_profit_pct': 0.2449, 'profitable_count': 47, 'loss_or_flat_count': 25, 'simple_sum_profit_pct': 17.63, 'min_profit_pct': -6.56, 'max_profit_pct': 7.02}
- `threshold_block_joined_count`: 60
- `threshold_profitable_count`: 39
- `threshold_loss_or_flat_count`: 21
- `threshold_profit`: {'sample': 60, 'valid_profit_sample': 60, 'equal_weight_avg_profit_pct': 0.2982, 'profitable_count': 39, 'loss_or_flat_count': 21, 'simple_sum_profit_pct': 17.89, 'min_profit_pct': -6.36, 'max_profit_pct': 7.02}
- `threshold_profitable_profit`: {'sample': 39, 'valid_profit_sample': 39, 'equal_weight_avg_profit_pct': 2.139, 'profitable_count': 39, 'loss_or_flat_count': 0, 'simple_sum_profit_pct': 83.42, 'min_profit_pct': 0.06, 'max_profit_pct': 7.02}
- `pure_threshold_profitable_count`: 2
- `mixed_threshold_profitable_count`: 37
- `threshold_contract_warning_record_count`: 7

## By Date

|target_date|forced_record_count|forced_stage_record_count|post_sell_joined_count|profitable_joined_count|threshold_block_joined_count|threshold_profitable_count|threshold_contract_warning_record_count|
|---|---|---|---|---|---|---|---|
|2026-06-30|58|57|35|19|30|16|6|
|2026-07-01|49|48|23|17|18|14|1|
|2026-07-02|32|32|14|11|12|9|0|

## Score Bucket Summary

|score_bucket|sample|valid_profit_sample|equal_weight_avg_profit_pct|profitable_count|loss_or_flat_count|simple_sum_profit_pct|min_profit_pct|max_profit_pct|
|---|---|---|---|---|---|---|---|---|
|50-54|3|3|-0.0833|1|2|-0.25|-0.78|0.97|
|55-59|1|1|1.14|1|0|1.14|1.14|1.14|
|60-64|14|14|-0.1114|8|6|-1.56|-4.52|4.14|
|65-69|9|9|0.2111|6|3|1.9|-4.32|2.98|
|70-74|32|32|0.4766|22|10|15.25|-6.36|7.02|
|unknown|1|1|1.41|1|0|1.41|1.41|1.41|

## Mixed Blockers On Profitable Threshold Records

|blocker|count|
|---|---|
|latency_danger|29|
|stale_or_quote|27|
|source_quality_gap|26|
|cooldown|25|
|pure_threshold_no_mixed_guard|2|

## Top Profitable Threshold Examples

|record_id|target_date|stock_name|profit_rate|peak_profit|max_score_below_threshold|latest_entry_threshold|score_bucket|threshold_contract_warning_event_count|forced_price_delta_pct|scanner_promotion_reason|mixed_blockers|pure_threshold_candidate|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|14586|2026-06-30|SK이터닉스|7.02|9.17|74.0|75.0|70-74|0|4.06|price_jump_start_acceleration|['latency_danger', 'stale_or_quote']|False|
|14581|2026-06-30|가온전선|6.75|9.45|74.0|75.0|70-74|2|20.44|rank_jump_acceleration|['latency_danger', 'stale_or_quote', 'cooldown', 'source_quality_gap']|False|
|14519|2026-06-30|원익IPS|5.74|6.84|70.0|75.0|70-74|0|0.12|price_jump_multisource_confirmation|['cooldown', 'source_quality_gap']|False|
|15035|2026-07-02|남광토건|4.14|5.39|60.0|75.0|60-64|0|1.77|price_jump_start_acceleration|['latency_danger', 'stale_or_quote']|False|
|14518|2026-06-30|가온전선|3.95|4.6|60.0|75.0|60-64|0|11.19|rank_jump_acceleration|['latency_danger']|False|
|15036|2026-07-02|계룡건설|3.53|4.29|70.0|75.0|70-74|0|7.55|price_jump_start_acceleration|['latency_danger', 'stale_or_quote', 'source_quality_gap']|False|
|15100|2026-07-02|선도전기|2.98|3.78|68.0|75.0|65-69|0|2.37|price_jump_start_acceleration|['latency_danger', 'cooldown', 'source_quality_gap']|False|
|14762|2026-07-01|스피어|2.94|3.69|60.0|75.0|60-64|0|0.92|price_jump_start_acceleration|['latency_danger', 'stale_or_quote']|False|
|14749|2026-07-01|두산퓨얼셀|2.93|3.63|74.0|75.0|70-74|0|3.5|price_jump_start_acceleration|['latency_danger', 'stale_or_quote', 'cooldown', 'source_quality_gap']|False|
|14819|2026-07-01|대원전선|2.47|2.82|72.0|75.0|70-74|0|1.4|price_jump_start_acceleration|['stale_or_quote', 'cooldown', 'source_quality_gap']|False|
|14770|2026-07-01|한양이엔지|2.33|2.19|69.0|75.0|65-69|0|10.26|price_jump_start_acceleration|['latency_danger', 'stale_or_quote', 'cooldown', 'source_quality_gap']|False|
|14568|2026-06-30|원익IPS|2.18|2.55|73.0|75.0|70-74|0|0.55|price_jump_start_acceleration|[]|True|

## Next Action

- Postclose split needed: pure score threshold versus latency/stale/cooldown/source-quality mixed cases.
- Candidate buckets to inspect first: score 70-74 profitable threshold-blocked records with fresh context and no hard stale/pre-submit guard, then score 60-64 winners separately from the losing tail.
- Contract warning rows need producer/attribution review before they are used in threshold EV.
- Do not use this aggregate for intraday runtime threshold mutation or real-order approval.
