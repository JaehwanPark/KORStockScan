# Server Comparison (2026-04-10)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-10`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `6` | `1` | `-5.0` |
| `completed_trades` | `6` | `1` | `-5.0` |
| `open_trades` | `0` | `0` | `0.0` |
| `holding_events` | `0` | `0` | `0.0` |
| `all_rows` | `178` | `175` | `-3.0` |
| `entered_rows` | `6` | `1` | `-5.0` |
| `expired_rows` | `162` | `145` | `-17.0` |

## Performance Tuning
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-10&since=09:00:00`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `holding_reviews` | `29` | `5` | `-24.0` |
| `holding_skips` | `3` | `0` | `-3.0` |
| `holding_skip_ratio` | `9.4` | `0.0` | `-9.4` |
| `holding_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `holding_review_ms_avg` | `3373.28` | `2164.4` | `-1208.88` |
| `holding_review_ms_p95` | `11622.0` | `2471.0` | `-9151.0` |
| `holding_skip_ws_age_p95` | `0.13` | `0.0` | `-0.13` |
| `gatekeeper_decisions` | `58` | `90` | `32.0` |
| `gatekeeper_fast_reuse_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_eval_ms_avg` | `12419.29` | `11177.19` | `-1242.1` |
| `gatekeeper_eval_ms_p95` | `22469.0` | `14247.0` | `-8222.0` |
| `gatekeeper_fast_reuse_ws_age_p95` | `0.08` | `1.63` | `1.55` |
| `gatekeeper_action_age_p95` | `1609.78` | `1408.18` | `-201.6` |
| `gatekeeper_allow_entry_age_p95` | `1609.78` | `1408.18` | `-201.6` |
| `gatekeeper_bypass_evaluation_samples` | `61` | `107` | `46.0` |
| `exit_signals` | `6` | `1` | `-5.0` |
| `dual_persona_shadow_samples` | `0` | `0` | `0.0` |
| `dual_persona_gatekeeper_samples` | `0` | `0` | `0.0` |
| `dual_persona_overnight_samples` | `0` | `0` | `0.0` |
| `dual_persona_conflict_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_conservative_veto_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_extra_ms_p95` | `0.0` | `0.0` | `0.0` |
| `dual_persona_fused_override_ratio` | `0.0` | `0.0` | `0.0` |

- local_watch_items:
  - `label=보유 AI skip 비율, value=9.4%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.13s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=22469ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.08s, target=<= 2.00s`

- remote_watch_items:
  - `label=보유 AI skip 비율, value=0.0%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=0.00s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=14247ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=1.63s, target=<= 2.00s`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-10`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `6` | `1` | `-5.0` |
| `evaluated_candidates` | `6` | `1` | `-5.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-10&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `304135` | `363046` | `58911.0` |
| `tracked_stocks` | `168` | `163` | `-5.0` |
| `submitted_stocks` | `4` | `0` | `-4.0` |
| `blocked_stocks` | `48` | `47` | `-1.0` |
| `waiting_stocks` | `1` | `0` | `-1.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=109`
  - `name=blocked_ai_score, count=19`
  - `name=blocked_overbought, count=16`
  - `name=blocked_gatekeeper_reject, count=7`
  - `name=strength_momentum_pass, count=6`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=110`
  - `name=blocked_overbought, count=20`
  - `name=blocked_ai_score, count=18`
  - `name=blocked_gatekeeper_reject, count=5`
  - `name=strength_momentum_pass, count=5`
