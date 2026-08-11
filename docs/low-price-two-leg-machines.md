# Lower-price two-leg live machines

## Scope

Five independent regular-session profiles implement the user-selected first
three research priorities.  Every profile owns its process, lock, durable state,
authority artifact, and exact broker-order ledger.

| Profile | Symbol | Session | Scan bars |
|---|---|---|---|
| `samsung_heavy_midday` | 삼성중공업 `010140` | SOR regular | 13:15 through 13:54 |
| `samsung_heavy_afternoon` | 삼성중공업 `010140` | SOR regular | 14:00 through 14:40 |
| `daewoo_ec_midday` | 대우건설 `047040` | SOR regular | 13:15 through 13:54 |
| `daewoo_ec_afternoon` | 대우건설 `047040` | SOR regular | 14:00 through 14:40 |
| `sk_eternix_midday` | SK이터닉스 `475150` | SOR regular | 13:15 through 13:54 |

The baseline contract is a 30-completed-bar high-to-close drawdown of at least
1.25% and close-to-window-low proximity of at most 0.20%.  One signal may create
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

The implementation does not add the three symbols to
`data/config/manual_control_excluded_codes.txt`, install timers, or start a
service by itself.  This prevents an unstarted profile from silently removing a
symbol from primary-bot ownership.  Activation is a separate operator action
after review and explicit exclusion confirmation:

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

- drawdown `1.25 -> 1.50`, or
- near-low proximity `0.20 -> 0.10`.

Across all five profiles and the existing Samsung regular machines, at most one
profile/machine and one entry axis may change per day.  The Samsung candidate is
produced first; if it owns a valid mutation, or its same-date candidate is
invalid, the lower-price family carries all policies forward.  Quantity, 50:50
legs, target ticks, entry validity, route, stop/hold
behavior, provider, bot, cap, and broker guards are immutable.  Each preflight
first materializes or reuses the exact-date applied policy and binds its hash to
the profile authority artifact.

## Official Kiwoom reference evidence

- Repository: `Kiwoom-Securities/Kiwoom-REST-API`
- Commit: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Retrieved: `2026-08-11T18:13:09+09:00`
- Inspected: `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`,
  `kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core`, and the Postman collection
- Requests: `ka10080`, `kt10000`, `kt10001`, `kt10003`, and `kt00007`
