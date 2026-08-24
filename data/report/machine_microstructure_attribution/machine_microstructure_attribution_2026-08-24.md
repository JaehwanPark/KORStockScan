# Machine Microstructure Attribution

- Target date: `2026-08-24`
- Status: `warning`
- Decision: `partial_owner_or_micro_source_gap_base_tuning_unchanged`
- Authority: diagnostic only; existing widget/episode policy is unchanged.
- Collection feedback: next-session source-only targets `4`; repair gaps and bounded policy-sample rotation are included; manual-control exclusions are not applied.

## Coverage

| Dynamic symbols | Widget symbols | Episode profiles | Anchors | Matched | Gaps |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 11 | 116 | 41 | 5 | 96 |

## Fast Lifecycle Objective

- Decision: `source_only_rolling_paired_research_evidence_accumulating`
- Matched unique decision lifecycles: `1`; entry-submit anchors: `0`; entry-fill anchors: `2`; exit-submit anchors: `0`; exit anchors: `2`.
- Timed outcomes: `2`; completed within 180s: `0.0`.
- Gross/no-slippage average (diagnostic only): `0.379868`; cost-aware owner average (daily diagnostic only): `0.149867`.
- Completion follow-up: `EVIDENCE_ACCUMULATING`; next=`continue_exact_date_collection_and_rolling_readiness_review`; tracked by the 21:15 approval/reminder ledger.
- Speed, target, cooldown, cap, quantity, re-entry, and forced-exit policy remain unchanged.

## Rolling Paired Turnover Policy Research

- Status: `evidence_accumulating`; decision: `continue_source_only_rolling_paired_evidence`.
- Cohorts: `4`; ready candidates: `0`.
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
| widget | 042660:KRX_REGULAR | 042660 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:006800:KRX_REGULAR | 006800 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:010140:KRX_REGULAR | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:080220:KRX_REGULAR | 080220 | micro_scope_source_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | research:475150:KRX_REGULAR | 475150 | micro_scope_source_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| widget | expansion:138080:SOR_REGULAR | 138080 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_heavy_midday | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_heavy_afternoon | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_midday | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | mirae_asset_morning | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | doosan_enerbility_morning | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kakao_morning | 035720 | owner_anchor_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kepco_afternoon | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kakao_late_morning | 035720 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | mirae_asset_midday | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_afternoon | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_heavy_morning | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | doosan_enerbility_late_morning | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kakao_midday | 035720 | owner_anchor_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_telecom_afternoon | 017670 | owner_anchor_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_ea_late_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_ea_afternoon | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | samsung_ea_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | hanse_afternoon | 105630 | owner_anchor_contract_invalid | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | hanse_morning | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | tym_midday | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | tym_afternoon | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kepco_late_morning | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | hanse_midday | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | youngone_morning | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | hanse_late_morning | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kepco_midday | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | youngone_afternoon | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | nhn_afternoon | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | sk_eternix_late_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | mirae_asset_late_morning | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | kepco_morning | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | nhn_morning | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | nhn_late_morning | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_005950_afternoon | 005950 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_005950_late_morning | 005950 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_005950_midday | 005950 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_005950_morning | 005950 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_023530_afternoon | 023530 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_023530_late_morning | 023530 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_023530_midday | 023530 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | candidate_023530_morning | 023530 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_002900_late_morning | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_002900_morning | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_006800_afternoon | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_006800_late_morning | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_010140_late_morning | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_015760_morning | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_028050_midday | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_034020_afternoon | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_034020_midday | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_035720_afternoon | 035720 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_111770_late_morning | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_111770_midday | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_181710_late_morning | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_181710_midday | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_181710_morning | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | existing_475150_late_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_doosan_enerbility_late_morning | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_doosan_enerbility_morning | 034020 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_hanse_afternoon | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_hanse_late_morning | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_hanse_midday | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_hanse_morning | 105630 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kakao_late_morning | 035720 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kakao_midday | 035720 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kakao_morning | 035720 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kepco_afternoon | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kepco_late_morning | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_kepco_midday | 015760 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_mirae_asset_midday | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_mirae_asset_morning | 006800 | micro_expected_session_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_nhn_afternoon | 181710 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_ea_afternoon | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_ea_late_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_ea_morning | 028050 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_heavy_afternoon | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_heavy_midday | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_samsung_heavy_morning | 010140 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_afternoon | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_midday | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_sk_eternix_morning | 475150 | micro_expected_venue_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_tym_afternoon | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_tym_midday | 002900 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_youngone_afternoon | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |
| episode | logic_youngone_morning | 111770 | micro_symbol_not_observed | micro_context_unavailable_base_owner_tuning_unchanged |

Missing micro data is not imputed as zero return and does not stop the existing owner tuning path.

## Policy Change Boundary

This daily report cannot change policy. Policy review opens only after 5 observed trading days, 20 matched unique owner/symbol/session decision lifecycles, BBO coverage >=95%, depth coverage >=90%, and a cost-adjusted paired 5/10/20-day EV improvement with no downside deterioration.
The first runtime linkage still requires a new bounded family mapping and explicit operator approval; any approved candidate applies PREOPEN only.
