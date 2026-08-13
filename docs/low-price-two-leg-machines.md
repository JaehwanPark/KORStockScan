# Lower-price two-leg live machines

## Scope

Thirteen independent regular-session profiles implement the user-selected active
scope. Every profile owns its process, lock, durable state,
authority artifact, and exact broker-order ledger.

| Profile | Symbol | Session | Scan bars |
|---|---|---|---|
| `samsung_heavy_midday` | 삼성중공업 `010140` | SOR regular | 13:20 through 13:29 |
| `samsung_heavy_afternoon` | 삼성중공업 `010140` | SOR regular | 14:00 through 14:40 |
| `sk_eternix_midday` | SK이터닉스 `475150` | SOR regular | 13:30 through 13:54 |
| `mirae_asset_morning` | 미래에셋증권 `006800` | SOR regular | 09:35 through 09:44 |
| `jeju_semiconductor_morning` | 제주반도체 `080220` | SOR regular | 09:10 through 09:49 |
| `doosan_enerbility_morning` | 두산에너빌리티 `034020` | SOR regular | 09:20 through 09:49 |
| `hanwha_ocean_late_morning` | 한화오션 `042660` | SOR regular | 10:05 through 10:24 |
| `kakao_morning` | 카카오 `035720` | SOR regular | 09:20 through 09:39 |
| `kakao_late_morning` | 카카오 `035720` | SOR regular | 10:05 through 10:34 |
| `sk_eternix_morning` | SK이터닉스 `475150` | SOR regular | 09:50 through 09:59 |
| `mirae_asset_midday` | 미래에셋증권 `006800` | SOR regular | 13:15 through 13:24 |
| `kepco_afternoon` | 한국전력 `015760` | SOR regular | 14:00 through 14:29 |
| `sk_eternix_afternoon` | SK이터닉스 `475150` | SOR regular | 14:00 through 14:40 |

The 30-day calibration and 16-day untouched holdout selected independent entry
contracts: Samsung Heavy midday uses 30 bars, drawdown at least 0.75%, and
near-low at most 0.35%; Samsung Heavy afternoon keeps 30 bars, 1.25%, and
0.20%; SK Eternix midday uses 20 bars, 2.00%, and 0.75%. From the explicit
2026-08-13 operator quantity change, one signal creates exactly two independent
10-share limit buys: one at the signal close and one at one tick below (maximum
20 shares). Entry orders remain valid for five subsequently completed one-minute
bars. A partial buy fill cancels only the remaining quantity of that exact owned
order; after cancellation reconciliation, the confirmed filled quantity owns one
same-quantity +2-tick limit target. There is no
stop loss, target timeout, forced sale, or target cancellation; an unclosed
position remains held.

The four 2026-08-12 additions use the full clean-baseline 47-date window with
31 calibration dates and the latest 16 dates as holdout. Their conservative
execution proxy requires one-tick penetration beyond both entry and target:

| Profile | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---:|---:|---:|---|---:|---:|
| `mirae_asset_morning` | 15 | 1.75% | 0.50% | -1/-2 ticks | 5 | +4 ticks |
| `jeju_semiconductor_morning` | 20 | 2.50% | 0.10% | close/-1 tick | 3 | +4 ticks |
| `doosan_enerbility_morning` | 15 | 2.00% | 0.50% | close/-1 tick | 5 | +4 ticks |
| `hanwha_ocean_late_morning` | 20 | 1.25% | 0.10% | close/-1 tick | 5 | +4 ticks |

The six 2026-08-12 postclose selections use all 48 clean-baseline trading
dates, split into 32 calibration dates and the latest 16 untouched holdout
dates. They are exactly the three new-symbol and three existing-symbol
time-extension rows shown in the admin Telegram notice, rather than every
hidden report recommendation:

Their deployable preflight input is the tracked
`data/config/low_price_two_leg_expanded_profile_evidence_2026-08-12.json`
projection. It binds the original v5 report canonical SHA, the exact six
recommendation rows, both calibration halves, holdout/full metrics, and the
user-approved scope. The ignored 3.7MB runtime report is audit/source evidence,
not a deployment dependency.

| Profile | Lookback | Drawdown | Near low | Entry offsets | Valid bars | Target |
|---|---:|---:|---:|---|---:|---:|
| `kakao_morning` | 15 | 0.75% | 0.35% | close/-1 tick | 5 | +3 ticks from 2026-08-14 |
| `kepco_afternoon` | 60 | 0.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `kakao_late_morning` | 15 | 0.50% | 0.35% | close/-1 tick | 5 | +2 ticks |
| `sk_eternix_morning` | 15 | 1.50% | 0.75% | close/-1 tick | 5 | +2 ticks |
| `mirae_asset_midday` | 45 | 1.00% | 0.50% | close/-1 tick | 5 | +2 ticks |
| `sk_eternix_afternoon` | 45 | 2.50% | 0.50% | close/-1 tick | 5 | +2 ticks |

Kakao morning keeps its frozen-research +2-tick baseline for the 2026-08-13
execution record, then applies an explicit user-directed +3-tick target transition
from the 2026-08-14 exact-date PREOPEN policy. The service consumes that applied
target instead of the compiled baseline, and the authority artifact records the
before/after value and effective date. At the observed 39,250/39,200 fills this
means independent targets of 39,400/39,350. It does not change Kakao late morning,
any other profile, entry criteria, two-share allocation, no-stop holding, or broker
guards. Postclose research includes +3 ticks as a source-only execution-plan option;
ordinary bounded entry tuning cannot change this operator-owned target axis.
After postclose evidence review, rollback restores +2 ticks in a later exact-date
PREOPEN policy only when explicitly directed by the user. It never cancels or
replaces an already-owned target order.

KEPCO afternoon had 16 completed holdout legs and two held legs (11.11% of
filled legs), with completed-only notional EV `+0.064355%` and held mark
`-1.297293%`. This is accepted only within the reviewed source-only carry
budget of at most 25% held/fill and at least `-3%` held mark. It does not add a
stop, timeout, forced sale, or unrealized PnL to completed EV.

The Doosan Enerbility and Hanwha Ocean episode profiles are parallel to their
widget auto-trading owners. Neither owner reads the other's state, position
quantity, or order numbers, and neither may cancel or sell the other's orders
or quantity. Both may independently submit orders for the same symbol.

## Runtime authority and isolation

The live service is fail-closed unless all of the following are true for the
exact profile and date:

- the immutable profile and exact live-confirmation string match;
- the profile-specific enable environment variable is true;
- the shared cached Kiwoom token is available;
- the main bot process is active;
- the symbol has an explicit `manual_operator` exclusion from the primary bot;
- the profile-bound frozen clean-baseline source replay and result pass;
- the exact-date PREOPEN policy artifact and same-day authority artifact pass;
- the endpoint is `https://api.kiwoom.com`, the route is SOR, and each new entry
  leg is exactly 10 shares. Legacy owned one-share orders remain valid custody
  state and are never resized retroactively.

Activation uses protected `manual_operator` markers for all eight symbols in
`data/config/manual_control_excluded_codes.txt`. The reviewed installer adds
the new Kakao and KEPCO markers immediately before enabling the new timers, so
source implementation alone does not partially transfer their runtime owner.
This excludes the symbols from
the primary bot while leaving the Doosan/Hanwha widget owners and episode
owners mutually independent. Timer installation remains a separate reviewed
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
and never pools different symbols or sessions.  Its sole decision window is
`clean_baseline_cumulative`: every available actual-state daily observation
from `2026-06-05` through the target date, including explicit reconciliation
of a carried episode to its original trade date, with notional-weighted EV as
the primary metric.  Trading dates before machine observation began, or dates
without an observation, are disclosed as coverage gaps but are not imputed as
outcomes and are not backfilled from historical market replay.

After at least 20 completed legs in that clean-baseline actual-observation window,
positive current and candidate EV, and no held/unresolved inventory, one
profile may propose one tightening axis for the next PREOPEN:

- drawdown from the profile baseline to at most `baseline + 0.25%p`, or
- near-low proximity from the profile baseline to at most `baseline - 0.10%p`.

Across all thirteen profiles and the existing Samsung regular machines, at most one
profile/machine and one entry axis may change per day.  The Samsung candidate is
produced first; if it owns a valid mutation, or its same-date candidate is
invalid, the lower-price family carries all policies forward. Quantity is fixed
at 10 shares per leg (20 total) by explicit operator authority; each
profile's frozen 50:50 entry offsets, target ticks, entry validity, route, stop/hold
behavior, provider, bot, cap, and broker guards are immutable.  Each preflight
first materializes or reuses the exact-date applied policy and binds its hash to
the profile authority artifact.

The retired Daewoo E&C profiles are absent from the runtime allowlist, wrappers,
and install timers. The installer also removes any legacy Daewoo timer files and
stops their exact service instances without deleting state or held-position
evidence.

The 2026-08-12 postclose tuning candidate predates the six-profile expansion.
For the 2026-08-13 PREOPEN transition only, its exact seven-profile v2 policy is
validated first and the six newly approved profiles are added at their frozen
baselines. From the next postclose cycle onward the candidate and applied-policy
inventory must contain all thirteen profiles; a partial or stale inventory fails
closed.

## Daily implementation-candidate recommendation

The 20:10 postclose chain runs `low_price_two_leg_expanded_candidate_research`
after the actual-profile tuning step. It uses every KRX trading date from the
clean baseline (`2026-06-05`) through the target date. The latest 16 dates remain
untouched holdout evidence; every earlier clean-baseline date forms an expanding
calibration window. The reviewed new-symbol universe combines the fixed seed
set with up to five source-qualified dynamic seeds from the latest completed
daily recommendation snapshot, with all four supported regular-session lanes
evaluated separately.

A separate existing-symbol time-extension lane evaluates only supported
midday/afternoon sessions that have no active profile for that symbol. Active
symbol/session pairs are excluded rather than retuned through this discovery
producer. Active symbol/session pairs are excluded, while unimplemented
midday/afternoon windows for the newly added symbols remain eligible for the
separate time-extension lane.

Only profiles with matching source-qualified trading dates, positive
notional-weighted holdout EV, the required calibration/holdout sample floors,
the bounded no-stop carry budget, and a latest close at or below KRW 100,000
enter the ranked recommendation list. The JSON and Markdown report are atomically written before
an `ADMIN_ONLY` Telegram message is attempted. Delivery retries up to three
times, and a target-date state file prevents duplicate notices during postclose
recovery. Missing Telegram configuration, exhausted delivery retries, or a
report authority mismatch closes the postclose wrapper as failed rather than
silently claiming daily delivery.

If the cached Kiwoom token is unavailable or one of the new/existing-symbol
sources fails the full clean-baseline common-date/source-quality contract, the
producer writes a
`source_quality_blocked` report and sends an admin notice stating that no daily
recommendation was produced. This isolated research-source block does not stop
unrelated postclose producers. Telegram configuration or delivery failure still
fails the wrapper because daily delivery itself was not completed.

This is recommendation-only automation. It cannot add a profile, install or
start a service, create a PREOPEN policy, submit an order, or change quantity,
targets, stops, providers, the main bot, caps, or broker guards. A recommended
profile still requires a separate user instruction, implementation, and review
gate.

## Episode market-data request control

All live lower-price profiles share the episode-only `ka10080` read controller.
A process reuses one successful completed-bar snapshot within the same KST
minute, and independent episode processes serialize a remaining `ka10080`
request at a conservative local interval of 0.4 seconds. An explicit Kiwoom
`1700` or HTTP 429 read failure is retried at most twice with bounded backoff.
The official reference identifies error 1700 but does not publish the local
0.4-second value; that interval is an operational burst guard based on observed
traffic. Failed/invalid snapshots are not cached. Order and cancel API IDs never
enter this retry path, so an ambiguous broker write cannot be replayed.
A successful response is cached for the rest of the KST minute only when it
already contains the immediately preceding completed candle. A boundary response
that still ends two or more minutes behind is returned once but not cached, so the
next bounded poll can observe the newly published candle.

## Official Kiwoom reference evidence

- Repository: `Kiwoom-Securities/Kiwoom-REST-API`
- Commit: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Retrieved: `2026-08-13T10:07:49+09:00`
- Inspected: `kiwoom_docs/차트.md`, `kiwoom_docs/주문.md`,
  `kiwoom_docs/계좌.md`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core`, the Postman collection, and
  `examples/국내주식/차트/get_domestic_stock_minute_chart.py`
- Requests: `ka10080`, `kt10000`, `kt10001`, `kt10003`, and `kt00007`
