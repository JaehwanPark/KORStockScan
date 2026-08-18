# Machine Microstructure Attribution

- Target date: `2026-08-18`
- Status: `warning`
- Decision: `partial_owner_or_micro_source_gap_base_tuning_unchanged`
- Authority: diagnostic only; existing widget/episode policy is unchanged.
- Collection feedback: next-session source-only targets `4`; repair gaps and bounded policy-sample rotation are included; manual-control exclusions are not applied.

## Coverage

| Dynamic symbols | Widget symbols | Episode profiles | Anchors | Matched | Gaps |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 18 | 12 | 61 | 38 | 8 | 43 |

## Fast Lifecycle Objective

- Decision: `source_only_rolling_paired_research_evidence_accumulating`
- Matched unique decision lifecycles: `2`; entry-fill anchors: `3`; exit anchors: `0`.
- Timed outcomes: `1`; completed within 180s: `0.0`.
- Gross/no-slippage average (diagnostic only): `0.308166`; cost-aware owner average (daily diagnostic only): `0.108166`.
- Completion follow-up: `EVIDENCE_ACCUMULATING`; next=`continue_exact_date_collection_and_rolling_readiness_review`; tracked by the 21:15 approval/reminder ledger.
- Speed, target, cooldown, cap, quantity, re-entry, and forced-exit policy remain unchanged.

## Rolling Paired Turnover Policy Research

- Status: `evidence_accumulating`; decision: `continue_source_only_rolling_paired_evidence`.
- Cohorts: `3`; ready candidates: `0`.
- Axis: source-only target timeout `60/120/180s`; ranking requires positive cost-aware rolling EV/net profit, p10 and HELD guards, then capital-efficiency improvement.
- Remaining evidence gaps: `10d_candidate_ev_not_positive,10d_paired_ev_uplift_not_positive,10d_paired_lifecycle_count_below_20,20d_candidate_ev_not_positive,20d_paired_ev_uplift_not_positive,20d_paired_lifecycle_count_below_20,5d_candidate_ev_not_positive,5d_paired_ev_uplift_not_positive,5d_paired_lifecycle_count_below_20,bbo_complete_rate_below_95pct,depth_window_coverage_below_90pct,observed_trading_days_below_5,paired_p10_worse_or_missing,policy_eligible_unique_lifecycles_below_20,primary_20d_net_profit_not_positive,relative_primary_ev_uplift_below_1pct`.
- Runtime family registration, PREOPEN apply, orders, and current owner policy remain unchanged.

## Producer/Consumer Gaps

| Owner | Scope | Symbol | Gap | Effect |
| --- | --- | --- | --- | --- |
| widget | 005930:KRX_REGULAR | 005930 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | 005930:NXT_AFTERMARKET | 005930 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | 005930:NXT_PREMARKET | 005930 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | 034020:KRX_REGULAR | 034020 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | 042660:KRX_REGULAR | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:006800:KRX_REGULAR | 006800 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:010140:KRX_REGULAR | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:080220:KRX_REGULAR | 080220 | micro_scope_source_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:475150:KRX_REGULAR | 475150 | micro_scope_source_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | expansion:100790:SOR_REGULAR | 100790 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | expansion:101730:SOR_REGULAR | 101730 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | expansion:047810:SOR_REGULAR | 047810 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | expansion:469610:SOR_REGULAR | 469610 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_heavy_midday | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_heavy_afternoon | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_midday | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | jeju_semiconductor_morning | 080220 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | hanwha_ocean_late_morning | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kakao_morning | 035720 | micro_anchor_window_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kepco_afternoon | 015760 | micro_anchor_window_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_afternoon | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_028050_afternoon | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_028050_late_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_028050_midday | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_028050_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_010140_late_morning | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_010140_morning | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_042660_afternoon | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_042660_midday | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_042660_morning | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_080220_afternoon | 080220 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_080220_late_morning | 080220 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_080220_midday | 080220 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_475150_late_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_hanwha_ocean_late_morning | 042660 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_jeju_semiconductor_morning | 080220 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kakao_morning | 035720 | micro_anchor_window_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_heavy_afternoon | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_heavy_midday | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_afternoon | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_midday | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |

Missing micro data is not imputed as zero return and does not stop the existing owner tuning path.

## Policy Change Boundary

This daily report cannot change policy. Policy review opens only after 5 observed trading days, 20 matched unique owner/symbol/session decision lifecycles, BBO coverage >=95%, depth coverage >=90%, and a cost-adjusted paired 5/10/20-day EV improvement with no downside deterioration.
The first runtime linkage still requires a new bounded family mapping and explicit operator approval; any approved candidate applies PREOPEN only.
