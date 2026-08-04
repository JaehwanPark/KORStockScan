# Samsung Price Widget for Windows

`samsung_price_widget.py` is a small always-on-top Windows widget (190 x 182
pixels) that shows Samsung Electronics (`005930`) current price, the difference
from the previous successful 10-second query, today's low-price distance, and
the completed-close direction over 1-, 3-, and 5-minute horizons on one compact
line. It also draws a compact 20-minute line chart from completed one-minute
closes; no additional graph is created for the three trend horizons. A compact
advisory line shows the entry state, tick-normalized price range, primary
reason, and external-risk quality.

The implementation contract, state-machine order, formulas, known limits, and
external-auditor checklist are documented in
[`docs/audit-reports/2026-08-02-samsung-widget-advisory-external-audit-brief.md`](../../docs/audit-reports/2026-08-02-samsung-widget-advisory-external-audit-brief.md).

The current-price query and previous-price delta refresh every 10 seconds;
the trend and chart remain based on completed one-minute candles. During the
NXT premarket (`08:00~08:50 KST`), the endpoint requests `005930_NX` for both
the quote and minute chart, attributes it to `PREMARKET_KRX_LIKE`, and the
widget status line shows `PRE`. During the NXT aftermarket
(`15:40~20:00 KST`), it uses the same NXT request code and shows `NXT`.

It calls the KORStockScan AWS endpoint, not Kiwoom directly. The AWS endpoint
uses only the existing `data/runtime/kiwoom_token_cache.json` shared cache and
never issues, refreshes, revokes, exports, or logs a Kiwoom bearer token. When
the cache is missing, near expiry, expired, or rejected, it fails closed and
the widget keeps the last successful price with an `AWS 토큰 대기` status. It
immediately removes any prior entry state and price range; a 25-second local
watchdog also expires advisory colors and shows the last-success age. It does
not access an account, place/cancel orders, or restart/control the bot.
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

The optional daily evaluator runs after the NXT close and materializes mature
1/3/5/10/20/30/60-minute MFE/MAE plus target/adverse first-hit observations.
Daily compact reports remain available after minute JSONL retention cleanup,
and the rolling artifact declares whether the 60-trading-day floor has been
met. It is counterfactual observation only and never aggregates with realized
PnL or changes a runtime threshold. Historical pipeline events that lack the
same-session completed OHLCV, BBO, venue, and exact advisory payload are
source-quality-ineligible for state-machine replay rather than being silently
normalized into the 60-day sample.
Actionable rows with invalid widget authority, runtime flags, timestamps,
source quality, venue/session, or entry ranges are counted by exclusion reason
and do not enter MFE/MAE. A normal timer run after 20:00 evaluates that day; a
`Persistent` catch-up before 20:00 evaluates the previous Korean trading day.

```bash
sudo cp deploy/systemd/korstockscan-samsung-widget-evaluation.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now korstockscan-samsung-widget-evaluation.timer
```

The route is `GET /api/widget/samsung-price` and requires the matching
`X-KORStockScan-Widget-Key` request header. The quote-only fallback uses `POST
/api/dostk/stkinfo`, `api-id: ka10001`. The collector uses read-only
market-data TRs `ka10001`, `ka10003`, `ka10004`, `ka10064`, `ka10080`,
`ka10081`, `ka20001`, `ka20005`, and `ka90008`; it never calls auth, account, order,
cancel, or bot-control endpoints.

The advisory is deterministic, not an AI score or trading hard gate. Dynamic
levels come from prior-day OHLC, session VWAP/opening range, confirmed recent
support/resistance, completed-bar price/volume structure, fresh BBO, and
Samsung relative performance versus SK Hynix and KOSPI. Yahoo `NQ=F`, `MU`,
and `KRW=X` data is explicitly labeled `yahoo_best_effort` and
`BEST_EFFORT_DELAYED`; it is not represented as licensed real-time data.
Favorable external data cannot create an entry signal. Adverse external data
can downgrade or hold an otherwise domestic-qualified advisory.
Session-wide relative weakness may be cleared only when both 15-minute and
5-minute aligned returns versus every required comparison are no worse than
-0.5 percentage points; this clears a stale negative veto and cannot promote a
setup by itself. A high-volume retest may qualify as absorption only after the
held structure, latest completed close, VWAP, recent resistance, and non-down
3/5-minute trends agree. A forming-price upside impulse cannot qualify it.
Structural support owns invalidation, while chase distance is measured from
the tactical VWAP/support used to form the displayed price range.
NXT premarket context is auxiliary-only through 09:30 KST and is then removed;
it cannot create `ENTRY_READY`. In the NXT aftermarket, the latest regular-KRX
foreign/program flow is labeled `FROZEN_REGULAR_SESSION` and is never presented
as live aftermarket flow. Each advisory expires after 60 seconds or at the
current session close, whichever arrives first, and never later than 20:00 KST.
The window always says `관측용/자동주문 아님`; `ENTRY_READY` and
`ENTRY_CAUTION` are rendered as softer observation labels, not order commands.

The AWS collector also sends a plain-text Telegram notice only to the configured
`ADMIN_ID` when a displayed advisory first becomes `ENTRY_CAUTION` or
`ENTRY_READY`.  A direct `ENTRY_CAUTION -> ENTRY_READY` upgrade produces one
additional notice.  Repeated 10-second observations are deduplicated, and a
non-actionable interval of at least 60 seconds is required before a new episode
can notify again.  Telegram failures are isolated from quote collection and do
not change advisory state, trading runtime, accounts, or orders.  Set
`KORSTOCKSCAN_SAMSUNG_WIDGET_ENTRY_TELEGRAM_ENABLED=false` on the collector
service to disable this admin-only notification path.

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

## Windows installation

Copy this `tools/windows` directory to the Windows PC. Run PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Install-SamsungPriceWidget.ps1 -ApiUrl 'https://YOUR-AWS-HOST/api/widget/samsung-price' -AccessKey 'YOUR-WIDGET-ACCESS-KEY'
```

This writes the endpoint key only to the current user's `%APPDATA%` config and
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
