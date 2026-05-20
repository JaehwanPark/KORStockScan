# Scalping Pattern Lab Automation - 2026-05-20

## Summary
- gemini_fresh: `True`
- claude_fresh: `True`
- consensus_count: `6`
- auto_family_candidate_count: `3`
- code_improvement_order_count: `13`
- scalp_entry_adm_status/joined: `pass` / `154`
- runtime_effect: `False`

## Consensus Findings
- `AI threshold dominance` route=`existing_family` family=`score65_74_recovery_probe`
- `AI threshold miss EV recovery` route=`existing_family` family=`score65_74_recovery_probe`
- `Budget pass without submit` route=`auto_family_candidate` family=`-`
- `latency guard miss EV recovery` route=`instrumentation_order` family=`-`
- `liquidity gate miss EV recovery` route=`auto_family_candidate` family=`-`
- `overbought gate miss EV recovery` route=`auto_family_candidate` family=`-`

## Code Improvement Orders
- `order_ai_threshold_dominance` AI threshold dominance subsystem=`entry_funnel` runtime_effect=`False`
- `order_ai_threshold_miss_ev_recovery` AI threshold miss EV recovery subsystem=`entry_funnel` runtime_effect=`False`
- `order_budget_pass_without_submit` Budget pass without submit subsystem=`scalping_logic` runtime_effect=`False`
- `order_latency_guard_miss_ev_recovery` latency guard miss EV recovery subsystem=`runtime_instrumentation` runtime_effect=`False`
- `order_liquidity_gate_miss_ev_recovery` liquidity gate miss EV recovery subsystem=`entry_filter_quality` runtime_effect=`False`
- `order_overbought_gate_miss_ev_recovery` overbought gate miss EV recovery subsystem=`entry_filter_quality` runtime_effect=`False`
- `order_latency_canary_tag_완화_1축_canary_승인` latency canary tag 완화 1축 canary 승인 subsystem=`runtime_instrumentation` runtime_effect=`False`
- `order_ai_threshold_miss_ev_회수_조건_점검` AI threshold miss EV 회수 조건 점검 subsystem=`entry_funnel` runtime_effect=`False`
- `order_overbought_gate_miss_ev_회수_조건_점검` overbought gate miss EV 회수 조건 점검 subsystem=`entry_filter_quality` runtime_effect=`False`
- `order_partial_fallback_확대_직후_즉시_재평가_report_only` partial → fallback 확대 직후 즉시 재평가 report-only subsystem=`holding_exit` runtime_effect=`False`
