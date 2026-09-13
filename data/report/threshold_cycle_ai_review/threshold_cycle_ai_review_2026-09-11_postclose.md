# Threshold Cycle AI Correction - 2026-09-11 postclose

- AI status: `parsed`
- Family coverage: `complete` (reviewed `1` / expected `1`)
- Missing families: `-`
- Authority: proposal-only; deterministic calibration guard is the source of truth.
- Runtime change: `false`
- Input context chars: `55865`
- Input context hash: `55a0419ec16ec0483594f36a36603b2d492422d9bfd4122854a5dcdd4d9d8fd3`
- Provider status: `openai / success`
- Usage: input_tokens=`15987`, output_tokens=`900`, total_tokens=`16887`, elapsed_ms=`40603`
- Cost: estimated_cost_usd=`None`, status=`missing_price_contract`

| family | ai_state | route | proposal | guard | reason |
| --- | --- | --- | --- | --- | --- |
| position_sizing_dynamic_formula | agree | threshold_candidate | state=adjust_down, value=flat_10_fallback, window=rolling_10d | accepted=True, effective_state=adjust_down, effective_value=flat_10_fallback, runtime_change=False | Agree with deterministic candidate: current_value is "entry_type_5stage_cap25_v1", recommended_value is "flat_10_fallback", calibration_state is "adjust_down", and sample_count 31 meets sample_floor 30 under primary rolling_10d policy. Evidence also shows rolling_10d candidate_quality favors "flat_10_fallback" source_quality_adjusted_ev_pct 0.1835 over "entry_type_5stage_cap25_v1" 0.141. |
