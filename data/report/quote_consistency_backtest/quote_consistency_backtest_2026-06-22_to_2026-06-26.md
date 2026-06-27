# Quote Consistency Backtest 2026-06-22 to 2026-06-26

- runtime_family: `quote_consistency_normalization`
- observed_quote_rows: `327802`
- ws_input_rows: `327802`
- rest_input_rows: `2335`
- would_block_entry_reprice_scale_in: `295912`
- safety_exit_unblocked: `1729`
- ev_input_excluded_rows: `321061`

## State Counts
- `diverged`: 7
- `ok`: 14
- `single_source`: 6724
- `stale`: 321054
- `warning`: 3

## Stage State Counts
- `entry_submit`: diverged=7, ok=14, single_source=1618, stale=41875, warning=3
- `holding_exit`: stale=695
- `other`: single_source=1338, stale=24245
- `scale_in`: single_source=23, stale=819
- `scanner`: single_source=3745, stale=253420

## Verifier Findings
- `ok` `none`
