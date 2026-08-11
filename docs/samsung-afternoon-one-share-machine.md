# Samsung Afternoon One-Share Machine

## Decision

This is a separate one-share trading machine for Samsung Electronics (`005930`). It shares only the cached Kiwoom token and common infrastructure. Its state, process lock, authority artifact, and exact broker order ledger are independent from the morning machine and the widget strategy. It never uses aggregate account holdings to decide how much to sell.

The implementation is deployable but default-OFF. Creating these files does not install, enable, or start the systemd timers.

## Fixed policy

- Market: integrated SOR regular session. NXT is not analyzed as a separate regular-session market.
- Source: official Kiwoom `ka10080`, one-minute `005930_AL`; only completed bars from the current trade date are accepted.
- Scan: latest completed bar from 14:00 through 14:40 KST. The latest 30 bars must be consecutive one-minute bars. A late process start never backfills and chases an older signal.
- Signal: over the latest 30 completed bars, close is at least 1.25% below the rolling high and no more than 0.20% above the rolling low.
- Entry: one-share SOR limit buy one tick below the signal close, once per day. The order remains valid for the next five completed one-minute bars; after reconciliation it may cancel only its exact owned buy order.
- Exit: after an exact one-share fill is confirmed, submit an SOR limit sell two ticks above the actual fill price.
- No stop loss, target timeout, forced sell, or best-price liquidation. If the target closes unfilled, the state becomes `HELD`; if it remains open, the original order is reconciled across dates.

## Evidence and limitations

The clean-baseline replay covered 46 days: 22 attempts, 20 fills/completions, net EV +0.1612% at the 0.20% cost assumption, median target time 2 minutes, p90 14.1 minutes, and maximum 21 minutes. The 46-day sample is below the 60-day promotion floor, so this is user-directed bounded one-share authority rather than autonomous full-live promotion evidence.

Official Kiwoom contract gate: upstream commit `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`, retrieved 2026-08-11 12:04:45 KST; inspected `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`, and `kiwoom_docs/계좌.md` for `ka10080`, `kt10000`, `kt10001`, `kt10003`, and `kt00007`.

## Runtime surfaces

- State: `data/runtime/samsung_afternoon_one_share_state.json`
- Lock: `data/runtime/samsung_afternoon_one_share_state.lock`
- Daily authority: `data/runtime/samsung_afternoon_one_share_authority.json`
- Live enable env: `KORSTOCKSCAN_SAMSUNG_AFTERNOON_ONE_SHARE_ENABLED=true`
- Explicit confirmation: `005930_AFTERNOON_ONE_SHARE_LIVE`
- Preflight timer: 13:57 KST weekdays; the wrapper verifies the main `bot` tmux session and retries for up to 90 seconds before failing closed.
- Service timer: 13:59 KST weekdays

Live mode forbids `--once` and custom state or lock paths. Any interrupted or ambiguous broker write fails closed for manual reconciliation. The global buy pause remains a hard veto.

## Installation and rollback

After an explicit live-start decision, install with `sudo deploy/install_samsung_afternoon_one_share_systemd.sh`. Roll back only this machine with `sudo deploy/uninstall_samsung_afternoon_one_share_systemd.sh`; neither command changes or restarts the morning machine or widget service.
