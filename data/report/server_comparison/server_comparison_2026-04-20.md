# Server Comparison (2026-04-20)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-04-20`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_trades` | `38` | `6` | `-32.0` |
| `completed_trades` | `36` | `6` | `-30.0` |
| `open_trades` | `2` | `0` | `-2.0` |
| `holding_events` | `11788` | `0` | `-11788.0` |
| `all_rows` | `183` | `148` | `-35.0` |
| `entered_rows` | `38` | `6` | `-32.0` |
| `expired_rows` | `95` | `124` | `29.0` |

## Performance Tuning
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-04-20&since=09:00:00`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `holding_reviews` | `3601` | `486` | `-3115.0` |
| `holding_skips` | `296` | `45` | `-251.0` |
| `holding_skip_ratio` | `7.6` | `8.5` | `0.9` |
| `holding_ai_cache_hit_ratio` | `0.0` | `1.4` | `1.4` |
| `holding_review_ms_avg` | `1787.78` | `2556.89` | `769.11` |
| `holding_review_ms_p95` | `2500.0` | `3095.0` | `595.0` |
| `holding_skip_ws_age_p95` | `1.23` | `1.19` | `-0.04` |
| `gatekeeper_decisions` | `61` | `81` | `20.0` |
| `gatekeeper_fast_reuse_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_ai_cache_hit_ratio` | `0.0` | `0.0` | `0.0` |
| `gatekeeper_eval_ms_avg` | `12295.82` | `11130.01` | `-1165.81` |
| `gatekeeper_eval_ms_p95` | `19917.0` | `15370.0` | `-4547.0` |
| `gatekeeper_fast_reuse_ws_age_p95` | `0.07` | `0.0` | `-0.07` |
| `gatekeeper_action_age_p95` | `1616.38` | `1224.62` | `-391.76` |
| `gatekeeper_allow_entry_age_p95` | `1616.38` | `1224.62` | `-391.76` |
| `gatekeeper_bypass_evaluation_samples` | `63` | `83` | `20.0` |
| `exit_signals` | `39` | `10` | `-29.0` |
| `dual_persona_shadow_samples` | `2` | `0` | `-2.0` |
| `dual_persona_gatekeeper_samples` | `0` | `0` | `0.0` |
| `dual_persona_overnight_samples` | `2` | `0` | `-2.0` |
| `dual_persona_conflict_ratio` | `50.0` | `0.0` | `-50.0` |
| `dual_persona_conservative_veto_ratio` | `0.0` | `0.0` | `0.0` |
| `dual_persona_extra_ms_p95` | `4324.0` | `0.0` | `-4324.0` |
| `dual_persona_fused_override_ratio` | `0.0` | `0.0` | `0.0` |

- local_watch_items:
  - `label=보유 AI skip 비율, value=7.6%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=1.23s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=19917ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.07s, target=<= 2.00s`

- remote_watch_items:
  - `label=보유 AI skip 비율, value=8.5%, target=20% ~ 60%`
  - `label=보유 AI skip WS age p95, value=1.19s, target=<= 1.50s`
  - `label=Gatekeeper 평가 p95, value=15370ms, target=re-enable <= 5000ms / preferred < 1200ms`
  - `label=Gatekeeper fast reuse 비율, value=0.0%, target=15% ~ 55%`
  - `label=Gatekeeper fast reuse WS age p95, value=0.00s, target=<= 2.00s`

## Post Sell Feedback
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-04-20`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_candidates` | `38` | `9` | `-29.0` |
| `evaluated_candidates` | `38` | `9` | `-29.0` |

## Entry Pipeline Flow
- status: `ok`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-04-20&since=09:00:00&top=10`

| metric | local | remote | delta(remote-local) |
| --- | ---: | ---: | ---: |
| `total_events` | `156047` | `176274` | `20227.0` |
| `tracked_stocks` | `132` | `131` | `-1.0` |
| `submitted_stocks` | `0` | `1` | `1.0` |
| `blocked_stocks` | `29` | `33` | `4.0` |
| `waiting_stocks` | `0` | `0` | `0.0` |

- local_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=89`
  - `name=blocked_overbought, count=16`
  - `name=blocked_gatekeeper_reject, count=9`
  - `name=watching_shared_prompt_shadow, count=6`
  - `name=partial_fill_reconciled, count=5`

- remote_latest_stage_breakdown:
  - `name=strength_momentum_observed, count=77`
  - `name=blocked_overbought, count=19`
  - `name=watching_shared_prompt_shadow, count=18`
  - `name=blocked_gatekeeper_reject, count=10`
  - `name=blocked_strength_momentum, count=3`
