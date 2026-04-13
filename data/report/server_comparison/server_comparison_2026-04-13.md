# Server Comparison (2026-04-13)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-13`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `1` | `0` | `-1.0` |
| `completed_trades` | `1` | `0` | `-1.0` |
| `open_trades` | `0` | `0` | `0.0` |
| `holding_events` | `0` | `0` | `0.0` |
| `all_rows` | `44` | `47` | `3.0` |
| `entered_rows` | `1` | `0` | `-1.0` |
| `expired_rows` | `0` | `3` | `3.0` |

## Performance Tuning
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-13&since=09:00:00`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `holding_reviews` | `18` | `0` | `-18.0` |
| `holding_skips` | `0` | `0` | `0.0` |
| `holding_skip_ratio` | `0.0` | `0.0` | `0.0` |
| `holding_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `holding_review_ms_avg` | `2315.06` | `0.0` | `-2315.06` |
| `holding_review_ms_p95` | `2690.0` | `0.0` | `-2690.0` |
| `holding_skip_ws_age_p95` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_decisions` | `17` | `14` | `-3.0` |
| `gatekeeper_fast_reuse_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_eval_ms_avg` | `15242.41` | `16258.36` | `1015.95` |
| `gatekeeper_eval_ms_p95` | `40197.0` | `35544.0` | `-4653.0` |
| `gatekeeper_fast_reuse_ws_age_p95` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_action_age_p95` | `1263.68` | `1309.83` | `46.15` |
| `gatekeeper_allow_entry_age_p95` | `1263.68` | `1309.83` | `46.15` |
| `gatekeeper_bypass_evaluation_samples` | `18` | `14` | `-4.0` |
| `exit_signals` | `1` | `0` | `-1.0` |
| `dual_persona_shadow_samples` | `0` | `0` | `0.0` |
| `dual_persona_gatekeeper_samples` | `0` | `0` | `0.0` |
| `dual_persona_overnight_samples` | `0` | `0` | `0.0` |
| `dual_persona_conflict_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_conservative_veto_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_extra_ms_p95` | `0.0` | `0.0` | `0.0` |
| `dual_persona_fused_override_ratio` | `0.0` | `0.0` | `0.0` |

- local_watch_items:
  - `label=보유 AI skip 비율, value=0.0%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.00s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=40197ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

- remote_watch_items:
  - `label=보유 AI skip 비율, value=0.0%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.00s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=35544ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-13`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `1` | `0` | `-1.0` |
| `evaluated_candidates` | `1` | `0` | `-1.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-13&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `48516` | `46688` | `-1828.0` |
| `tracked_stocks` | `42` | `41` | `-1.0` |
| `submitted_stocks` | `0` | `0` | `0.0` |
| `blocked_stocks` | `29` | `30` | `1.0` |
| `waiting_stocks` | `0` | `0` | `0.0` |

- local_latest_stage_breakdown:
  - `name=blocked_overbought, count=18`
  - `name=strength_momentum_observed, count=11`
  - `name=blocked_gatekeeper_reject, count=6`
  - `name=blocked_ai_score, count=4`
  - `name=strength_momentum_pass, count=2`

- remote_latest_stage_breakdown:
  - `name=blocked_overbought, count=18`
  - `name=strength_momentum_observed, count=9`
  - `name=blocked_gatekeeper_reject, count=6`
  - `name=blocked_ai_score, count=3`
  - `name=strength_momentum_pass, count=2`
