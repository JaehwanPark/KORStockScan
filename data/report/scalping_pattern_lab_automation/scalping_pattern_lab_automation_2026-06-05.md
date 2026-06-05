# Scalping Pattern Lab Automation - 2026-06-05

## Summary
- gemini_fresh: `True`
- claude_fresh: `True`
- consensus_count: `5`
- auto_family_candidate_count: `2`
- code_improvement_order_count: `8`
- scalp_entry_adm_status/joined: `warning` / `105`
- runtime_effect: `False`
- decision_authority: `pattern_lab_analysis_workorder_source_only`
- runtime_mutation_allowed: `False`

## Consensus Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`
- `liquidity gate miss EV recovery` route=`auto_family_candidate` family=`-`
- `overbought gate miss EV recovery` route=`auto_family_candidate` family=`-`

## Code Improvement Orders
- `order_ai_threshold_dominance` AI threshold dominance subsystem=`entry_funnel` runtime_effect=`False`
- `order_ai_threshold_miss_ev_recovery` AI threshold miss EV recovery subsystem=`entry_funnel` runtime_effect=`False`
- `order_latency_guard_miss_ev_recovery` latency guard miss EV recovery subsystem=`runtime_instrumentation` runtime_effect=`False`
- `order_liquidity_gate_miss_ev_recovery` liquidity gate miss EV recovery subsystem=`entry_filter_quality` runtime_effect=`False`
- `order_overbought_gate_miss_ev_recovery` overbought gate miss EV recovery subsystem=`entry_filter_quality` runtime_effect=`False`
- `order_latency_canary_tag_완화_1축_canary_승인` latency canary tag 완화 1축 canary 승인 subsystem=`runtime_instrumentation` runtime_effect=`False`
- `order_latency_guard_miss_ev_회수_조건_점검` latency guard miss EV 회수 조건 점검 subsystem=`runtime_instrumentation` runtime_effect=`False`
- `order_ai_threshold_miss_ev_회수_조건_점검` AI threshold miss EV 회수 조건 점검 subsystem=`entry_funnel` runtime_effect=`False`
