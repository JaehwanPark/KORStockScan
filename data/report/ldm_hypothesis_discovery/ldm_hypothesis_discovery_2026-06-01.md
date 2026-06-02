# LDM Hypothesis Discovery - 2026-06-01

## Contract

- decision_authority: `sim_observation_planning`
- runtime_effect: `false`
- allowed_runtime_apply: `false`
- broker_order_forbidden: `true`
- core statement: LDM does not create buy/sell/hold live rules; it allocates sim observation budget and contrastive sample collection.

## Summary

- source_start: `2026-05-18`
- source_end: `2026-06-01`
- input_row_count: `14849`
- hypothesis_count: `12`
- candidate_count: `33`

## Top Hypotheses

- `ldm_hypothesis_711caa66c89b3f51` sample=`228` ev=`2.1509` contrast_delta=`2.1509`
- `ldm_hypothesis_e04e4d815fd8d0f9` sample=`247` ev=`2.0897` contrast_delta=`2.0897`
- `ldm_hypothesis_92dfecb5a05caa64` sample=`258` ev=`1.8561` contrast_delta=`1.8561`
- `ldm_hypothesis_0f038214d5ac5a30` sample=`19` ev=`1.3548` contrast_delta=`1.3548`
- `ldm_hypothesis_e9af2ba90970f01d` sample=`10` ev=`-1.6535` contrast_delta=`-1.6535`
- `ldm_hypothesis_00d0b765311ad7aa` sample=`141` ev=`-0.7987` contrast_delta=`-0.7987`
- `ldm_hypothesis_85018f5d185ec23b` sample=`92` ev=`-0.7679` contrast_delta=`-0.7679`
- `ldm_hypothesis_dead5c62e79220e3` sample=`119` ev=`-0.6395` contrast_delta=`-0.6395`
- `ldm_hypothesis_4782cc3ea9609ffc` sample=`36` ev=`-0.3538` contrast_delta=`-0.3538`
- `ldm_hypothesis_6039289bbc789fbf` sample=`15` ev=`-0.403` contrast_delta=`-0.403`

## Forbidden Uses

- `buy_sell_hold_live_rule`
- `threshold_apply`
- `provider_route_change`
- `bot_restart`
- `position_cap_release`
- `broker_order`
- `hard_safety_bypass`
