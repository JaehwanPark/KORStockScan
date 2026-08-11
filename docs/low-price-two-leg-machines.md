# Lower-price two-leg live machines

## Scope

Three independent regular-session profiles implement the user-selected active
scope. Every profile owns its process, lock, durable state,
authority artifact, and exact broker-order ledger.

| Profile | Symbol | Session | Scan bars |
|---|---|---|---|
| `samsung_heavy_midday` | 삼성중공업 `010140` | SOR regular | 13:20 through 13:29 |
| `samsung_heavy_afternoon` | 삼성중공업 `010140` | SOR regular | 14:00 through 14:40 |
| `sk_eternix_midday` | SK이터닉스 `475150` | SOR regular | 13:30 through 13:54 |

The 30-day calibration and 16-day untouched holdout selected independent entry
contracts: Samsung Heavy midday uses 30 bars, drawdown at least 0.75%, and
near-low at most 0.35%; Samsung Heavy afternoon keeps 30 bars, 1.25%, and
0.20%; SK Eternix midday uses 20 bars, 2.00%, and 0.75%. One signal may create
exactly two independent one-share limit buys: one at the signal close and one at
one tick below.  Entry orders remain valid for five subsequently completed
one-minute bars.  Each confirmed fill owns one +2-tick limit target.  There is no
stop loss, target timeout, forced sale, or target cancellation; an unclosed
position remains held.

## Runtime authority and isolation

The live service is fail-closed unless all of the following are true for the
exact profile and date:

- the immutable profile and exact live-confirmation string match;
- the profile-specific enable environment variable is true;
- the shared cached Kiwoom token is available;
- the main bot process is active;
- the symbol has an explicit `manual_operator` exclusion from the primary bot;
- the 2026-06-05 through 2026-08-10 source replay and profile result pass;
- the exact-date PREOPEN policy artifact and same-day authority artifact pass;
- the endpoint is `https://api.kiwoom.com`, the route is SOR, and each order is
  exactly one share.

Activation adds only `010140` and `475150` to
`data/config/manual_control_excluded_codes.txt` with the protected
`manual_operator` marker, after the account inventory and unfinished-order
checks are clear. This transfers those symbols from the primary bot to these
independent profile ledgers. Timer installation remains a separate reviewed
operator action:

```bash
sudo deploy/install_low_price_two_leg_systemd.sh
```

Rollback removes only these units and preserves state, authority, orders, and
held-position evidence:

```bash
sudo deploy/uninstall_low_price_two_leg_systemd.sh
```

## Profile-specific tuning

Postclose `low_price_two_leg_tuning` reads only each profile's durable actual
broker state and its own prior reports.  It never re-queries historical prices
and never pools different symbols or sessions.  Daily, rolling-10,
rolling-20, and clean-baseline cumulative outcomes use notional-weighted EV.

After at least 20 completed legs cumulatively, at least three completed legs in
each recent window, positive current and candidate EV, and no held/unresolved
inventory, one profile may propose one tightening axis for the next PREOPEN:

- drawdown from the profile baseline to at most `baseline + 0.25%p`, or
- near-low proximity from the profile baseline to at most `baseline - 0.10%p`.

Across all three profiles and the existing Samsung regular machines, at most one
profile/machine and one entry axis may change per day.  The Samsung candidate is
produced first; if it owns a valid mutation, or its same-date candidate is
invalid, the lower-price family carries all policies forward.  Quantity, 50:50
legs, target ticks, entry validity, route, stop/hold
behavior, provider, bot, cap, and broker guards are immutable.  Each preflight
first materializes or reuses the exact-date applied policy and binds its hash to
the profile authority artifact.

The retired Daewoo E&C profiles are absent from the runtime allowlist, wrappers,
and install timers. The installer also removes any legacy Daewoo timer files and
stops their exact service instances without deleting state or held-position
evidence.

## Daily implementation-candidate recommendation

The 20:10 postclose chain runs `low_price_two_leg_expanded_candidate_research`
after the actual-profile tuning step. It uses the most recent 46 KRX trading
dates, never earlier than the clean baseline: the first 30 dates select a spot
and the final 16 dates remain untouched holdout evidence. The reviewed research
universe contains nine symbols, with midday and afternoon evaluated separately.

Only profiles with matching source-qualified trading dates, positive
notional-weighted holdout EV, the required calibration/holdout sample floors,
zero held legs, and a latest close at or below KRW 100,000 enter the ranked
recommendation list. The JSON and Markdown report are atomically written before
an `ADMIN_ONLY` Telegram message is attempted. Delivery retries up to three
times, and a target-date state file prevents duplicate notices during postclose
recovery. Missing Telegram configuration, exhausted delivery retries, or a
report authority mismatch closes the postclose wrapper as failed rather than
silently claiming daily delivery.

If the cached Kiwoom token is unavailable or one of the nine sources fails the
common-date/source-quality contract, the producer writes a
`source_quality_blocked` report and sends an admin notice stating that no daily
recommendation was produced. This isolated research-source block does not stop
unrelated postclose producers. Telegram configuration or delivery failure still
fails the wrapper because daily delivery itself was not completed.

This is recommendation-only automation. It cannot add a profile, install or
start a service, create a PREOPEN policy, submit an order, or change quantity,
targets, stops, providers, the main bot, caps, or broker guards. A recommended
profile still requires a separate user instruction, implementation, and review
gate.

## Official Kiwoom reference evidence

- Repository: `Kiwoom-Securities/Kiwoom-REST-API`
- Commit: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Retrieved: `2026-08-11T18:13:09+09:00`
- Inspected: `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`,
  `kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core`, and the Postman collection
- Requests: `ka10080`, `kt10000`, `kt10001`, `kt10003`, and `kt00007`
