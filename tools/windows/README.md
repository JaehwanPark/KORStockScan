# Samsung Price Widget for Windows

`samsung_price_widget.py` is a small always-on-top Windows widget (190 x 220
pixels) that shows Samsung Electronics (`005930`) collector/REST current price,
the shared Kiwoom WebSocket 0B current price and their difference, the difference
from the previous successful query, the broker account's current
Samsung quantity and average purchase price, today's low-price distance, and the
completed-close direction over 1-, 3-, and 5-minute horizons. The former
20-minute graph has been removed. A compact advisory line remains, followed by
an operator-entered quantity and explicit `매수`/`매도` real-order buttons.

The implementation contract, state-machine order, formulas, known limits, and
external-auditor checklist are documented in
[`docs/audit-reports/2026-08-02-samsung-widget-advisory-external-audit-brief.md`](../../docs/audit-reports/2026-08-02-samsung-widget-advisory-external-audit-brief.md).

The Windows client refreshes every 2 seconds. The primary collector/REST price
continues on its existing 10-second source cadence, while a display-only shared
WebSocket snapshot is bridged at up to one-second cadence. `WS/KRX`, `WS/NXT`,
or `WS/SOR` shows the 0B price, its difference from the primary display price,
and observation age. A missing or older-than-five-second tick shows `WS: 수신
대기`; it never replaces the primary price and is never used for manual-order
price validation, quantity, or submission. The trends remain based on completed
one-minute candles. If the collector snapshot is stale, the direct REST
quote-only fallback is cached for eight seconds so the 2-second client does not
multiply broker requests. During the
NXT premarket (`08:00~08:50 KST`), the endpoint requests `005930_NX` for both
the quote and minute chart, attributes it to `PREMARKET_KRX_LIKE`, and the
widget status line shows `PRE`. During the NXT aftermarket
(`15:40~20:00 KST`), it uses the same NXT request code and shows `NXT`.

It calls the KORStockScan AWS endpoints, not Kiwoom directly. The AWS server
uses only the existing `data/runtime/kiwoom_token_cache.json` shared cache and
never issues, refreshes, revokes, exports, or logs a Kiwoom bearer token. The
quote route overlays only Samsung quantity and average purchase price from
read-only `kt00018`, using a 30-second process-local cache. It does not query
orderable cash or use this display data to size or authorize an operator order,
and it does not restart/control the bot. Invalid, partial, or conflicting
KRX/NXT position responses show `보유: 확인불가` without hiding price/advisory
data. Quote and order authority use separate keys. Without the order key,
quote/advisory/position display continues while both order buttons remain
disabled.

Manual order contract:

- Buy quantity is split with the current-price leg first: `ceil(qty/2)` at the
  fresh server price and `floor(qty/2)` at 0.5% below, both tick-normalized
  limits. Quantity 1 therefore creates only the current-price leg.
- A KRX-regular sell is a market order routed through broker `SOR`. NXT
  premarket/aftermarket sells are NXT limit orders at the fresh current price.
- Server quantity is bounded to 1-100 by default
  (`KORSTOCKSCAN_SAMSUNG_WIDGET_MANUAL_MAX_QTY`). A fresh coherent collector
  snapshot no older than 15 seconds and an active session are mandatory.
- Each click uses a UUID idempotency key. Buttons are disabled during the
  request and the server persists `SUBMITTING` before broker transport. A
  partial or ambiguous two-leg result is reported with accepted order numbers;
  the operator must check broker orders before retrying.
- Manual sell quantity is not reconciled with holdings and can affect stock
  bought manually or by another owner. The confirmation dialog states this;
  verify the account and avoid overlapping ownership before using it.

When the token/cache is unavailable or the quote is stale, the widget keeps
the last display but disables ordering. The advisory contract remains pinned
to read-only `widget_advisory_only`; manual button orders use the separate
`operator_widget_manual_order_v1` authority.
The advisory contract is pinned to `authority=widget_advisory_only`,
`runtime_effect=false`, `actual_order_submitted=false`, and
`broker_order_forbidden=true`; the Windows client rejects an advisory that
violates any of those fields.

## AWS setup

Set a long random value only in the AWS web-service environment as
`KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY`, or preferably set
`KORSTOCKSCAN_SAMSUNG_WIDGET_ACCESS_KEY_FILE` to a root-owned file containing
that value. The file must be readable by the Gunicorn service group only
(`root:www-data`, mode `640`) and its containing directory must be
`root:www-data`, mode `750`. Then restart only the Gunicorn web service after
the code is deployed. Do not run `restart.sh`, restart the trading bot, or put
a Kiwoom app key, secret key, or bearer token in the Windows configuration.

Create a second independent random value for real-order authority as
`KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY`, preferably through
`KORSTOCKSCAN_SAMSUNG_WIDGET_ORDER_KEY_FILE` with the same root-owned file
permissions. Never reuse the read-only key. `POST /api/widget/samsung-order`
accepts only the dedicated order header and does not accept a query-string or
read-only key.

For the standard deployment, place the value in an AWS-only environment file,
attach that file to `korstockscan-gunicorn.service` through a systemd drop-in,
then run `sudo systemctl restart korstockscan-gunicorn`. This restarts the web
API process only; it is separate from the trading-bot service.

Install the independent read-only collector without restarting the trading
bot:

```bash
sudo cp deploy/systemd/korstockscan-samsung-widget-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-samsung-widget-collector
```

It writes an atomic snapshot to
`data/runtime/samsung_widget_advisory_snapshot.json`. Gunicorn serves a fresh
snapshot without calling Kiwoom. If the snapshot is missing or older than 25
seconds, the route calls only `ka10001` to keep the price visible and returns
`DATA_WAIT`; it does not synthesize an entry advisory from partial data. Only
state changes and one observation per completed minute are recorded. JSONL
older than 30 days is deleted.

The daily multi-symbol evaluator runs at 20:10 after the NXT close and
materializes mature 1/3/5/10/20/30/60-minute MFE/MAE plus target/adverse
first-hit observations for Samsung Electronics, Doosan Enerbility, and Hanwha
Ocean.
Daily compact reports remain available after minute JSONL retention cleanup,
and the rolling artifact declares whether the 60-trading-day floor has been
met. The first locally source-qualified decisive 10-minute outcome also enters
a clean-baseline cumulative widget-only calibration. The bounded policy can
select two or three consecutive 10-second actionable confirmations per symbol
and session. A verified 20:10 run writes a date-effective policy for the next
KRX trading day; running collectors load it without a restart. Missing or
invalid daily evidence carries the last valid value forward, and a day without
a decisive sample is a no-change policy rather than a failure. This changes
only widget signal timing (`widget_runtime_effect=true`); it keeps
`runtime_effect=false`, `trading_runtime_effect=false`, and never changes the
trading bot, orders, accounts, providers, tokens, or broker guards.

The evaluator never aggregates counterfactual observations with realized PnL.
Historical pipeline events that lack the
same-session completed OHLCV, BBO, venue, and exact advisory payload are
source-quality-ineligible for state-machine replay rather than being silently
normalized into the 60-day sample.
Actionable rows with invalid widget authority, runtime flags, timestamps,
source quality, venue/session, or entry ranges are counted by exclusion reason
and do not enter MFE/MAE. A normal timer run after 20:00 evaluates that day; a
`Persistent` catch-up before 20:00 evaluates the previous Korean trading day.
The compatibility unit name remains `samsung-widget-evaluation`, but its
service command owns all three widget evaluations and next-day calibration.
After the outcome-label pipeline has had time to finish, a separate 21:15
timer rebuilds the exact portable mechanical replay and ranks up to five
additional KRX collector candidates from as many as 20 clean-baseline dates.
The ranking uses only source-qualified rows where the portable widget core
actually produced a signal or a pre-spread candidate; favorable Entry-AI
outcomes without a portable widget setup are excluded. It then requires
positive target/adverse and equal-weight end-return evidence, an entry liquidity
score of at least 60, at least 1% median intraday range, and at least 80%
fresh-quote coverage. Existing widget codes and manual-control exclusions are
omitted. The JSON report is written under
`data/report/widget_collector_expansion_recommendation/` and sent only to
`ADMIN_ID`; it remains `recommendation_only`, `runtime_effect=false`,
`collector_created=false`, and `service_started=false`. It never creates or
starts a collector without a later explicit operator instruction.
If the exact payload or outcome-label artifact is missing or violates its
report-only authority contract, the job fails without sending a misleading
"no candidate" message. The systemd service retries that source-not-ready
failure every five minutes, bounded to six attempts in 30 minutes.

```bash
sudo cp deploy/systemd/korstockscan-widget-expansion-recommendation.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-widget-expansion-recommendation.timer
```

```bash
sudo cp deploy/systemd/korstockscan-samsung-widget-evaluation.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-samsung-widget-evaluation.timer
```

The route is `GET /api/widget/samsung-price` and requires the matching
`X-KORStockScan-Widget-Key` request header. The quote-only fallback uses `POST
/api/dostk/stkinfo`, `api-id: ka10001`. The route adds a display-only account
overlay with `/api/dostk/acnt`, `api-id: kt00018`, and returns only the Samsung
row's `rmnd_qty` and `pur_pric`; the full account response is neither returned
nor persisted. The collector itself uses read-only market-data TRs `ka10001`,
`ka10003`, `ka10004`, `ka10064`, `ka10080`, `ka10081`, `ka20001`, `ka20005`, and
`ka90008`; it never calls auth, account, order, cancel, or bot-control endpoints.
The separate `POST /api/widget/samsung-order` endpoint requires
`X-KORStockScan-Widget-Order-Key` and is the only widget HTTP path allowed to
call `kt10000`/`kt10001` through the shared-token order gateway.

The advisory is deterministic, not an AI score or trading hard gate. Dynamic
levels come from prior-day OHLC, session VWAP/opening range, confirmed recent
support/resistance, completed-bar price/volume structure, fresh BBO, and
Samsung relative performance versus SK Hynix and KOSPI. Yahoo `NQ=F`, `MU`,
and `KRW=X` data is explicitly labeled `yahoo_best_effort` and
`BEST_EFFORT_DELAYED`; it is not represented as licensed real-time data.
Favorable external data cannot create an entry signal. Adverse external data
can downgrade or hold an otherwise domestic-qualified advisory.
The separate exit observation uses a rolling 20-bar high, a dynamic drawdown
band equal to the larger of two ticks or twice the recent median one-minute
change, the preceding five-bar low, session VWAP, and completed 3/5-minute
downside direction. `EXIT_CAUTION` records the initial break. `EXIT_READY`
requires a subsequent completed bar within the three-bar confirmation window
to remain below broken support with both 3- and 5-minute downside confirmation.
It becomes `EXIT_CANCELLED` after two
completed closes reclaim support or five completed bars fail to make a new
low. These states are `holding_independent=true`, `future_prediction=false`,
and remain widget observation only. Its source-quality gate requires a fresh
quote, fresh coherent BBO, and contiguous completed one-minute bars; entry-only
inputs such as prior-day OHLC, relative strength, flow, and external markets do
not block this exit observation.
Session-wide relative weakness may be cleared only when both 15-minute and
5-minute aligned returns versus every required comparison are no worse than
-0.5 percentage points; this clears a stale negative veto and cannot promote a
setup by itself. A high-volume retest may qualify as absorption only after the
held structure, latest completed close, VWAP, recent resistance, and non-down
3/5-minute trends agree. A forming-price upside impulse cannot qualify it.
The normal reclaim check accepts either session VWAP or a confirmed recent
resistance reclaim. A resistance-only breakout more than one tick above the
level waits for a pullback instead of issuing an immediate chase signal. The
collector keeps the confirmed structure and rebound-volume evidence for at
most three completed bars; after a completed resistance reclaim, a later
pullback that holds the level and remains within two ticks may become
`ENTRY_CAUTION`. A support break, downtrend, stale source, wide spread, or live
negative reversal cancels that recovery episode. Structural support owns
invalidation, while chase distance is measured from the most recent tactical
VWAP/reclaimed-resistance/support anchor. The chase ceiling is the larger of
30bp or the exact two-tick distance, so it does not contradict the displayed
two-tick range. A forming-
price break without confirmation is treated as a pending soft break and
withdraws the entry
range. `AVOID` requires either a completed one-minute close below support or a
two-tick live break accompanied by negative impulse and ask-side pressure.
After a break, two distinct completed bars must reclaim the broken support
before an actionable state can be promoted again.
NXT premarket context is auxiliary-only through 09:30 KST and is then removed;
it cannot create `ENTRY_READY`. In the NXT aftermarket, the latest regular-KRX
foreign/program flow is labeled `FROZEN_REGULAR_SESSION` and is never presented
as live aftermarket flow. Each advisory expires after 60 seconds or at the
current session close, whichever arrives first, and never later than 20:00 KST.
`ENTRY_READY` and `ENTRY_CAUTION` remain observation labels and never press an
order button. Real orders are created only by the separate operator button,
quantity input, confirmation dialog, and dedicated order-key path.

Telegram ownership is split by evidence type. The collector observes actionable
`ENTRY_CAUTION`/`ENTRY_READY` states only to open the collector-linked episode;
it does not send an entry message. A Samsung entry message is sent by the
separate widget auto-trader only after Kiwoom accepts an `ENTRY_BUY` or
`SCALE_IN_BUY` and returns an order number. The message says `매수 주문 접수`
and does not claim a fill. Venue/policy blocks, broker rejection, and ambiguous
responses do not create an entry message. Accepted actions older than five
minutes are not backfilled as new notices after a service restart, and delivery
is deduplicated by trade date, symbol, order role, and broker order number. Set
`KORSTOCKSCAN_WIDGET_AUTO_TRADER_ENTRY_TELEGRAM_ENABLED=true` only on the
auto-trader service that owns this delivery.

The collector continues to send one admin-only `EXIT_READY` notice per
confirmed collector entry/exit episode. It remains observation-only and does
not imply a sell order or a holding check. Telegram failures are isolated from
both quote collection and order execution. Thus an NXT advisory blocked by the
KRX-only execution policy can arm later collector exit observation, but cannot
produce an entry-order Telegram notice.

Only those two actionable states can display a recommended price range. `WATCH`
and `DATA_WAIT` show `가격대기`, `NO_CHASE` shows `범위이탈`, and `AVOID` shows
`범위없음`; the widget never fabricates a price while a setup condition is
missing. A single pivot remains candidate provenance and is not treated as
confirmed support until a held retest or a higher-high-and-higher-low structure
is complete. A held retest requires a separating bar and at least a one-tick
intermediate rebound, so adjacent equal-low plateau pivots do not qualify.
The 1/3/5-minute labels describe completed-bar direction; they do not predict
the next price. Their neutral bands are exchange-tick, session, and recent-
volatility adjusted. The compact detail line separately identifies confirmed-
bar `UP`, `STABLE`, `MIXED`, or `DOWN`, so a stable setup is not mislabeled as
an upward forecast. A forming-price downside reversal plus ask-side pressure can
only veto an advisory; a positive impulse cannot promote one.

## Offline Entry-AI comparison

The symbol-portable part of the widget entry logic can be replayed against
existing exact Entry-AI payloads and mature 10-minute outcome labels:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.monitoring.widget_mechanical_entry_replay \
  --target-date YYYY-MM-DD --write
```

The replay deliberately omits Samsung-specific peer strength, investor flow,
and external-market inputs, so a portable-core pass is capped at
`ENTRY_CAUTION`. Its report is diagnostic counterfactual evidence with
`runtime_effect=false`, `actual_order_submitted=false`, and no authority to
replace Entry AI or approve a live runtime change.

## Doosan Enerbility KRX advisory service

The independent Doosan Enerbility (`034020`) collector exposes
`GET /api/widget/doosan-price` with the same
`X-KORStockScan-Widget-Key` header. A Doosan-specific access key can be set with
`KORSTOCKSCAN_DOOSAN_WIDGET_ACCESS_KEY` (or its `_FILE` form); otherwise the
existing Samsung widget key is reused. This is an AWS advisory/API surface and
does not change the Samsung Windows executable.

`DOOSAN_FIRST_PULLBACK_V1` is KRX-regular-only. It starts from the portable
completed-bar support/VWAP/rebound detector, then requires all of the following:

- current-session return at or below `-0.50%`;
- `volume_confirmation_mode=standard_rebound` (absorption-only recovery remains
  `WATCH` in V1);
- fresh coherent quote and BBO with a spread no wider than two ticks;
- two consecutive 10-second actionable observations.

A qualifying return at or below `-1.00%` is labeled `HIGH` and normally becomes
`ENTRY_READY`; a resistance-only reclaim or a carried recovery episode keeps
the portable base engine's `ENTRY_CAUTION`. The broader `-0.50%` cohort is also
`ENTRY_CAUTION`. Multiple non-overlapping entry episodes may be emitted in one
KRX trade date. A completed episode is rearmed only after its linked exit event
expires, a later completed one-minute bar is available, and a non-actionable
observation resets the prior setup; the next setup still requires two fresh
10-second confirmations. The entry reference is the top of the recommended
range. Its linked exit event is emitted at the
tick-rounded `+1%` target or when a later completed one-minute candle closes
below the captured structural support. An intrabar low touch alone does not
create the support-break exit.

Entry and linked-exit events are sent only to the configured Telegram
`ADMIN_ID`. Stable event IDs, a local state file, 30-second failure backoff, and
once-only de-duplication prevent repeated notices; a closed entry event is not
sent late after its exit. Set
`KORSTOCKSCAN_DOOSAN_WIDGET_TELEGRAM_ENABLED=false` to disable both Doosan
notices. Every payload remains `authority=widget_advisory_only`,
`runtime_effect=false`, `actual_order_submitted=false`, and
`broker_order_forbidden=true`.

The collector uses the existing cached Kiwoom token and only `ka10001`,
`ka10004`, `ka10080`, and `ka10081`. It writes atomic state to
`data/runtime/doosan_widget_advisory_snapshot.json` and retains only state
transitions and minute summaries for 30 days. Install it independently; this
does not restart the trading bot:

```bash
sudo cp deploy/systemd/korstockscan-doosan-widget-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-doosan-widget-collector
```

Gunicorn must be gracefully reloaded separately before the new API route is
served. No service reload is performed merely by adding these files.

Official Kiwoom reference gate evidence for this addition was recorded at
`2026-08-05T16:55:23+09:00` against upstream commit
`69642586f7d84ba9fd8a6faf1f1537c7fda6568b`. The inspected contract paths were
`kiwoom_docs/종목정보.md`, `kiwoom_docs/차트.md`, `kiwoom/specs.py`,
`kiwoom/core`, and the Postman collection. KRX uses the unsuffixed `034020`
code; no NXT, auth, account, order, cancel, or continuation flow is added.

## Hanwha Ocean KRX advisory service

The independent Hanwha Ocean (`042660`) collector exposes
`GET /api/widget/hanwha-ocean-price` with the same
`X-KORStockScan-Widget-Key` header. A dedicated key can be set with
`KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_ACCESS_KEY` (or its `_FILE` form), otherwise
the Samsung widget key is reused.

`HANWHA_OCEAN_VWAP_FIRST_PULLBACK_V1` is KRX-regular-only and has no fixed
price or fixed session-return gate. It requires a confirmed retest or
higher-high/higher-low support structure, a VWAP or recent-resistance reclaim,
`volume_confirmation_mode=standard_rebound`, fresh coherent quote/BBO, a
spread no wider than two ticks, and two consecutive 10-second observations.
A completed retest that rebounds above VWAP is labeled `HIGH` and may become
`ENTRY_READY`; the broader valid first-pullback structure remains
`ENTRY_CAUTION`. Resistance-only and recovery-episode signals retain the
portable engine's caution state.

Multiple non-overlapping entry episodes may be emitted in one KRX trade date.
After a linked exit, the prior setup must expire, a later completed one-minute
bar and a non-actionable reset must be observed, and the next setup must pass
two fresh 10-second confirmations. Each linked exit event is emitted at the
tick-rounded `+1%` target or when a later completed one-minute candle closes
below the captured structural support.
Entry and linked-exit events are sent only to Telegram `ADMIN_ID`. Set
`KORSTOCKSCAN_HANWHA_OCEAN_WIDGET_TELEGRAM_ENABLED=false` to disable them.
Every payload remains `authority=widget_advisory_only`,
`runtime_effect=false`, `actual_order_submitted=false`, and
`broker_order_forbidden=true`.

The collector reuses only the cached Kiwoom token and calls `ka10001`,
`ka10004`, `ka10080`, and `ka10081`. It writes atomic state to
`data/runtime/hanwha_ocean_widget_advisory_snapshot.json` and persists only
state transitions and minute summaries:

```bash
sudo cp deploy/systemd/korstockscan-hanwha-ocean-widget-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-hanwha-ocean-widget-collector
```

Gunicorn must be gracefully reloaded separately before the route is served;
neither action restarts the trading bot. Official Kiwoom reference evidence
was rechecked at `2026-08-06T09:31:34+09:00` against upstream commit
`69642586f7d84ba9fd8a6faf1f1537c7fda6568b`. The inspected paths were
`kiwoom_docs/종목정보.md`, `kiwoom_docs/차트.md`, `kiwoom/specs.py`,
`kiwoom/core`, and the Postman collection. KRX uses unsuffixed `042660`; no
NXT, auth, account, order, cancel, or continuation flow is added.

## Windows installation

Copy this `tools/windows` directory to the Windows PC. Run PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Install-SamsungPriceWidget.ps1 -ApiUrl 'https://YOUR-AWS-HOST/api/widget/samsung-price' -AccessKey 'YOUR-WIDGET-ACCESS-KEY' -OrderAccessKey 'YOUR-SEPARATE-ORDER-KEY'
```

This writes both scoped endpoint keys only to the current user's `%APPDATA%` config and
creates `SamsungPriceWidget.lnk` on the desktop. The installer tries to further
restrict that file's ACL, but a managed Windows profile may reject the extra
ACL operation; it then keeps the normal current-user AppData permissions and
continues without requiring administrator privileges. Python for Windows with
Tkinter is required; the launcher uses `pyw.exe` so no console window is shown.

## Official Kiwoom reference gate

- Retrieved and verified: `2026-08-02T22:53:30+09:00`
- Upstream: `Kiwoom-Securities/Kiwoom-REST-API`
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Inspected: `kiwoom_docs/종목정보.md`, `kiwoom_docs/시세.md`,
  `kiwoom_docs/차트.md`, `kiwoom_docs/업종.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core/client.py`,
  `postman/kiwoom-openapi.postman_collection.json`, and the local
  `docs/kiwoom-api-data-contract.md`.
- Contract used: real `https://api.kiwoom.com`, `POST /api/dostk/stkinfo`,
  `authorization: Bearer ...`, `api-id: ka10001`, body `{"stk_cd":"005930"}`;
  quote value `cur_prc`.
- Trend-review recheck: `2026-08-03T00:04:04+09:00`, same upstream SHA.
  KOSPI same-window reads use `POST /api/dostk/chart`, `api-id: ka20005`,
  body `{"inds_cd":"001","tic_scope":"1"}`, and response list
  `inds_min_pole_qry` with 100x integer index values and `cntr_tm` provenance.
- Manual-order recheck: `2026-08-12T07:19:36+09:00`, same upstream SHA.
  Inspected `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, and the Postman
  collection. The widget uses `kt10000` limit buy and `kt10001` market/limit
  sell through the cached-token gateway; it does not use token issue or cash
  and holdings TRs.

The endpoint uses `ka10001.low_pric` for today's low and `ka10080` with
`tic_scope: "1"` for completed one-minute closes. It derives 1-, 3-, and
5-minute trends locally from contiguous completed closes, requires the
net-change, least-squares slope, R-squared, and directional consistency to
agree. The flat band is the larger of a session/horizon tick allowance and
1.25 times recent median absolute one-minute movement. A missing minute makes
that horizon unavailable, and
the trend window cannot cross PRE (`08:00`), KRX (`09:00`), or NXT aftermarket
(`15:40`) session starts. Both official request contracts accept `005930_NX`
for NXT, while KRX uses `005930`.
`08:00~08:50 KST` responses retain `market_venue=NXT` for backward
compatibility and expose the project cohort as
`market_cohort=PREMARKET_KRX_LIKE`. The response also exposes
`market_session` and `quote_request_code` for display provenance. The widget
endpoint deliberately does not implement REST/WebSocket auth, REG/REMOVE,
recovery, continuation, order, account, or bot lifecycle flows.
