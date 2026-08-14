# Samsung Midday Two-Leg Machine

## Decision

This is a separate two-leg trading machine for Samsung Electronics (`005930`). The legacy package/unit filenames remain compatibility surfaces, but new runtime authority is exactly two independent 10-share orders (20 shares maximum). It shares only the cached Kiwoom token and common infrastructure. Its process, state, lock, same-day authority artifact, and exact broker-order ledger are independent from the morning machine, afternoon machine, and widget strategy. It never uses aggregate account holdings to choose a sell quantity.

The implementation is deployable but default-OFF. Creating these files does not install, enable, or start its systemd timers.

## Fixed policy

- Market: integrated SOR regular session. NXT is not modeled as a separate regular-session market.
- Source: official Kiwoom `ka10080`, one-minute `005930_AL`; only completed bars from the current trade date are accepted.
- Scan: latest completed bar from 13:15 through 13:54 KST, equivalent to the analyzed half-open window `[13:15, 13:55)`. The latest 30 bars must be consecutive. A late process start never backfills and chases an older signal.
- Signal: over the latest 30 completed bars, close is at least 1.25% below the rolling high and no more than 0.20% above the rolling low.
- Entry: once per day, submit one 10-share SOR limit at the executable signal close and one 10-share SOR limit one tick below it. This is a fixed 50:50 allocation and is not a single 20-share broker order. Each leg remains valid for the next five completed one-minute bars; after broker reconciliation, the machine may cancel only that leg's exact owned buy order.
- Exit: a full buy fill submits a same-quantity target immediately. A partial buy fill first cancels the remaining quantity of only that exact owned order; after reconciliation, it submits a target for only the confirmed filled quantity. The baseline was two ticks above that leg's actual average fill price. For episodes newly armed from the explicit 2026-08-14 09:21:07 KST operator override onward, the target is three ticks above the actual average fill; existing target orders are never canceled or replaced by this transition.
- No stop loss, target timeout, forced sell, or best-price liquidation. If the target closes unfilled, the state becomes `HELD`; if it remains open, the original order is reconciled across dates.

The `ka10080` source reuses one successful snapshot within the same KST minute
only after the immediately preceding completed candle is present. A boundary
response that still ends earlier is not cached and is refetched on the next
bounded poll. It shares a cross-process 0.4-second episode read pacer. Explicit error 1700 or
HTTP 429 reads receive at most two bounded-backoff retries. Failed snapshots are
not cached, and order/cancel API IDs are never retried by this controller.

## Evidence and limitations

Clean-baseline replay from 2026-06-05 through 2026-08-10 covered 46 trading days. The selected `[13:15, 13:55)` window's original conservative signal-close-minus-one-tick leg produced 25 attempts, 21 fills, 21 target completions, four unfilled entries, and zero held outcomes. Completed positions reached the two-tick target in a median one minute and a maximum four minutes; worst observed post-fill adverse excursion was -0.316%. The final 16-day holdout produced seven attempts, five fills/completions, zero held outcomes, median one minute, and maximum two minutes. At the 0.20% cost/slippage assumption, completed-trade equal-weight average profit was approximately +0.139%. The added signal-close leg is the execution-probability leg identified by the entry-price re-evaluation; minute OHLC touch is supporting counterfactual evidence, not queue-fill proof. Each leg keeps independent attribution.

The sample is below the 60-day promotion floor and was selected from multiple intraday windows, so it is user-directed bounded two-leg authority rather than autonomous full-live promotion evidence. Minute OHLC replay cannot establish within-bar event order; target completion was conservatively counted only from the bar after the fill bar.

Official Kiwoom contract gate: upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieved 2026-08-13 10:07:49 KST; inspected `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`, `kiwoom/specs.py`, API spec, and Postman for `ka10080`, `kt10000`, `kt10001`, `kt10003`, `kt00007`, SOR symbol suffix, request fields, continuation, and execution fields. The official source defines 1700 as a request-limit error but does not specify the local pacing interval. No order example was executed.

## Runtime surfaces

- State: `data/runtime/samsung_midday_one_share_state.json`
- Lock: `data/runtime/samsung_midday_one_share_state.lock`
- Daily authority: `data/runtime/samsung_midday_one_share_authority.json`
- Live enable env: `KORSTOCKSCAN_SAMSUNG_MIDDAY_ONE_SHARE_ENABLED=true`
- Explicit confirmation: `005930_MIDDAY_TWO_LEG_LIVE`
- Preflight timer: 13:12 KST weekdays. The wrapper checks the existing main `bot` tmux session and retries for up to 90 seconds. The preflight unit intentionally does not use systemd `PrivateTmp`; the live service retains it.
- Service timer: 13:14 KST weekdays

Live mode forbids `--once` and custom state or lock paths. Interrupted or ambiguous broker writes fail closed for manual reconciliation. A legacy active one-share state also fails closed for manual reconciliation; only terminal legacy state can migrate automatically. The global buy pause remains a hard veto. This machine never cancels or sells orders or quantities owned by the morning, afternoon, widget, or primary bot.

## Installation and rollback

After a separate explicit live-start decision, install with `sudo deploy/install_samsung_midday_one_share_systemd.sh`. Roll back only this machine with `sudo deploy/uninstall_samsung_midday_one_share_systemd.sh`; neither command changes or restarts the morning, afternoon, widget, or primary bot service.

## Postclose entry observation

When a live episode is armed, `signal_features` freezes the completed signal bar, rolling high/low, observed drawdown and near-low distance, 30-bar lookback, five-bar entry validity, both leg prices, and the signal-time target ticks/runtime source/policy hash. Signals before 2026-08-14 09:21:07 KST retain the +2-tick exact-date hash; newly armed episodes after the transition use the +3-tick operator-overlay hash. The 20:10 `samsung_machine_entry_tuning` report reads only the target-date state and earlier daily artifacts from the same producer; it does not query historical prices. Actual broker fills remain separate by leg, and order identifiers/audit payloads are not copied. New target reconciliations persist the broker `kt00007.cntr_uv` sell fill price. Older configured-target proxy outcomes remain diagnostic and cannot satisfy the candidate floor.

The report compares the current signal cohort only with stricter observed subsets: drawdown may move from 1.25% to at most 1.50%, or near-low distance from 0.20% to at least 0.10%. It cannot estimate a relaxed threshold or a different cancel window. A postclose candidate requires the source-quality preflight, cumulative episode and completed-leg floors, positive rolling10/20 and cumulative notional EV, and no held/unresolved inventory. Across midday and afternoon, at most one machine and one entry axis may tighten on a given next-session PREOPEN.

The preflight wrapper materializes an exact-date applied policy before the live service starts. Missing or stale candidates use the verified baseline; an invalid latest candidate or exact-date artifact blocks before broker gateway construction. A valid exact-date base artifact is immutable and reused by later preflights that day. The 2026-08-14 operator transition is applied as a time-scoped +2-to-+3 target overlay for new Samsung episodes only; it does not mutate the base artifact or existing orders. No-stop holding, two 10-share legs, five completed entry bars, provider, bot, cap, and broker guards remain outside tuning authority. Target ticks are also outside postclose automatic tuning and require an explicit operator transition with before/after, effective time, and rollback provenance. Existing owned one-share state remains supported and is never resized retroactively.
