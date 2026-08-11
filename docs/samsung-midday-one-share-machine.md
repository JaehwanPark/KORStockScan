# Samsung Midday One-Share Machine

## Decision

This is a separate one-share trading machine for Samsung Electronics (`005930`). It shares only the cached Kiwoom token and common infrastructure. Its process, state, lock, same-day authority artifact, and exact broker-order ledger are independent from the morning machine, afternoon machine, and widget strategy. It never uses aggregate account holdings to choose a sell quantity.

The implementation is deployable but default-OFF. Creating these files does not install, enable, or start its systemd timers.

## Fixed policy

- Market: integrated SOR regular session. NXT is not modeled as a separate regular-session market.
- Source: official Kiwoom `ka10080`, one-minute `005930_AL`; only completed bars from the current trade date are accepted.
- Scan: latest completed bar from 13:15 through 13:54 KST, equivalent to the analyzed half-open window `[13:15, 13:55)`. The latest 30 bars must be consecutive. A late process start never backfills and chases an older signal.
- Signal: over the latest 30 completed bars, close is at least 1.25% below the rolling high and no more than 0.20% above the rolling low.
- Entry: one-share SOR limit buy one tick below the signal close, once per day. The order remains valid for the next five completed one-minute bars; after broker reconciliation, the machine may cancel only its exact owned buy order.
- Exit: after an exact one-share fill is confirmed, submit an SOR limit sell two ticks above the actual fill price.
- No stop loss, target timeout, forced sell, or best-price liquidation. If the target closes unfilled, the state becomes `HELD`; if it remains open, the original order is reconciled across dates.

## Evidence and limitations

Clean-baseline replay from 2026-06-05 through 2026-08-10 covered 46 trading days. The selected `[13:15, 13:55)` window produced 25 attempts, 21 fills, 21 target completions, four unfilled entries, and zero held outcomes. Completed positions reached the two-tick target in a median one minute and a maximum four minutes; worst observed post-fill adverse excursion was -0.316%. The final 16-day holdout produced seven attempts, five fills/completions, zero held outcomes, median one minute, and maximum two minutes. At the 0.20% cost/slippage assumption, completed-trade equal-weight average profit was approximately +0.139%.

The sample is below the 60-day promotion floor and was selected from multiple intraday windows, so it is user-directed bounded one-share authority rather than autonomous full-live promotion evidence. Minute OHLC replay cannot establish within-bar event order; target completion was conservatively counted only from the bar after the fill bar.

Official Kiwoom contract gate: upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieved 2026-08-11 12:44:57 KST; inspected `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`, `kiwoom/specs.py`, `kiwoom/core`, and Postman for `ka10080`, `kt10000`, `kt10001`, `kt10003`, `kt00007`, SOR symbol suffix, request fields, continuation, and execution fields. No order example was executed.

## Runtime surfaces

- State: `data/runtime/samsung_midday_one_share_state.json`
- Lock: `data/runtime/samsung_midday_one_share_state.lock`
- Daily authority: `data/runtime/samsung_midday_one_share_authority.json`
- Live enable env: `KORSTOCKSCAN_SAMSUNG_MIDDAY_ONE_SHARE_ENABLED=true`
- Explicit confirmation: `005930_MIDDAY_ONE_SHARE_LIVE`
- Preflight timer: 13:12 KST weekdays. The wrapper checks the existing main `bot` tmux session and retries for up to 90 seconds. The preflight unit intentionally does not use systemd `PrivateTmp`; the live service retains it.
- Service timer: 13:14 KST weekdays

Live mode forbids `--once` and custom state or lock paths. Interrupted or ambiguous broker writes fail closed for manual reconciliation. The global buy pause remains a hard veto. This machine never cancels or sells orders or quantities owned by the morning, afternoon, widget, or primary bot.

## Installation and rollback

After a separate explicit live-start decision, install with `sudo deploy/install_samsung_midday_one_share_systemd.sh`. Roll back only this machine with `sudo deploy/uninstall_samsung_midday_one_share_systemd.sh`; neither command changes or restarts the morning, afternoon, widget, or primary bot service.
