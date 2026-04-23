# Server Comparison (2026-01-06)

- remote: `https://songstockscan.ddns.net`
- since: `09:00:00`
- policy: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`

## Trade Review
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/trade-review?date=2026-01-06`
- remote_error: `URLError: <urlopen error timed out>`
- excluded_from_criteria: `win_trades, loss_trades, avg_profit_rate, realized_pnl_krw, row-level profit_rate`

## Performance Tuning
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/performance-tuning?date=2026-01-06&since=09:00:00`
- remote_error: `URLError: <urlopen error timed out>`

## Post Sell Feedback
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/post-sell-feedback?date=2026-01-06`
- remote_error: `URLError: <urlopen error timed out>`
- excluded_from_criteria: `missed_upside_rate, good_exit_rate, avg_realized_profit_rate, avg_extra_upside_10m_pct, median_extra_upside_10m_pct, avg_close_after_sell_10m_pct, capture_efficiency_avg_pct, estimated_extra_upside_10m_krw_sum, estimated_extra_upside_10m_krw_avg, timing_tuning_pressure_score, case-level profit_rate`

## Entry Pipeline Flow
- status: `remote_error`
- remote_url: `https://songstockscan.ddns.net/api/entry-pipeline-flow?date=2026-01-06&since=09:00:00&top=10`
- remote_error: `URLError: <urlopen error timed out>`
