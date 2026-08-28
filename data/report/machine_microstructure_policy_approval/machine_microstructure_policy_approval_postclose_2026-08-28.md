# Machine Microstructure Policy Approval

- Target date: `2026-08-28`
- Phase: `postclose`
- Decision: `objective_followup_required`
- Source status: `loaded`
- Objective follow-up source status: `loaded`
- Actionable: `0`
- Objective follow-ups: `1`
- Objective follow-up rejections: `0`
- Reminder: `not_requested`
- Runtime apply performed: `false`

## Fast Lifecycle Objective Follow-up

| Follow-up | State | Current capability | Gaps | Next action |
| --- | --- | --- | --- | --- |
| machine_lifecycle_turnover_policy_research_v1 | EVIDENCE_ACCUMULATING | rolling_paired_research_report_contract_blocked | 10d_candidate_ev_not_positive,10d_paired_ev_uplift_not_positive,10d_paired_lifecycle_count_below_10,10d_source_report_contract_gap,20d_candidate_ev_not_positive,20d_paired_ev_uplift_not_positive,20d_paired_lifecycle_count_below_20,20d_source_report_contract_gap,5d_candidate_ev_not_positive,5d_paired_ev_uplift_not_positive,5d_paired_lifecycle_count_below_5,5d_source_report_contract_gap,bbo_complete_rate_below_95pct,depth_window_coverage_below_90pct,observed_trading_days_below_5,paired_p10_worse_or_missing,policy_eligible_unique_lifecycles_below_20,primary_20d_net_profit_not_positive,relative_primary_ev_uplift_below_1pct | repair_excluded_source_report_contracts_and_rerun |

Objective follow-ups are research/workorder reminders only. They cannot be approved, scheduled, enrolled, or applied as runtime policy.

## Pending

- None

The queue and reminders do not mutate runtime policy. A registered family, explicit operator decision, exact-date PREOPEN handoff, family apply receipt, and post-apply attribution remain separate gates.
