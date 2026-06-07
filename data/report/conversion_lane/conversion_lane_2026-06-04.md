# Conversion Lane - 2026-06-04

## Decision
- conversion candidates: `396`
- real conversion queue: `3`
- positive EV runtime observed: `3`
- positive EV not due until next PREOPEN: `4`
- positive EV previous-policy natural match 0: `4`
- positive EV real conversion queue: `3`
- positive EV sample-floor blocked: `5`
- conversion candidate strategy scope: scalp=`107` swing=`288` unscoped=`1`
- bounded real canary requestable: `0`
- top blocker ranked: `key_lineage`; top blocker by count: `sample_floor`
- top LDM bucket blocker: `key_lineage`
- submit funnel blocker count: `6` (submit_drought_is_ldm_bucket_blocker=`False`)

## Top Conversion Blockers
- #1 `ldm_hypothesis_00d0b765311ad7aa`: key_lineage -> hypothesis_catalog_missing
- #2 `ldm_hypothesis_0f038214d5ac5a30`: key_lineage -> hypothesis_catalog_missing
- #3 `ldm_hypothesis_4782cc3ea9609ffc`: key_lineage -> hypothesis_catalog_missing
- #4 `ldm_hypothesis_6039289bbc789fbf`: key_lineage -> hypothesis_catalog_missing
- #5 `ldm_hypothesis_711caa66c89b3f51`: key_lineage -> hypothesis_catalog_missing
- #6 `ldm_hypothesis_76e02836d5c6bea3`: key_lineage -> hypothesis_catalog_missing
- #7 `ldm_hypothesis_85018f5d185ec23b`: key_lineage -> hypothesis_catalog_missing
- #8 `ldm_hypothesis_92dfecb5a05caa64`: key_lineage -> hypothesis_catalog_missing
- #9 `ldm_hypothesis_bd95657855656936`: key_lineage -> hypothesis_catalog_missing
- #10 `ldm_hypothesis_dead5c62e79220e3`: key_lineage -> hypothesis_catalog_missing
- #11 `ldm_hypothesis_e04e4d815fd8d0f9`: key_lineage -> hypothesis_catalog_missing
- #12 `ldm_hypothesis_e9af2ba90970f01d`: key_lineage -> hypothesis_catalog_missing
- #13 `submit_drought:BROKER_RECEIPT`: submit_drought -> close_submit_drought_broker_receipt
- #14 `submit_drought:BUDGET_PASS_COLLAPSE`: submit_drought -> close_submit_drought_budget_pass_collapse
- #15 `submit_drought:LATENCY_PRE_SUBMIT`: submit_drought -> close_submit_drought_latency_pre_submit
- #16 `submit_drought:SIM_REAL_AUTHORITY`: submit_drought -> close_submit_drought_sim_real_authority
- #17 `submit_drought:SOURCE_TAXONOMY_LEAKAGE`: submit_drought -> close_submit_drought_source_taxonomy_leakage
- #18 `submit_drought:UPSTREAM_GATE`: submit_drought -> close_submit_drought_upstream_gate
- #19 `scale_in:blocker_reason:trend_not_strong`: env_mapping -> complete_parent_flow
- #20 `scale_in:arm:pyramid`: env_mapping -> complete_parent_flow

## Real Conversion Queue
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:6a0bc81a2f`: state=runtime_observed ev=0.5554 sample=2
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocke:6852993e40`: state=runtime_observed ev=0.7087 sample=1
- `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked:ad38ef346b`: state=runtime_observed ev=0.2535 sample=1
