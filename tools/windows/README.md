# Samsung Price Widget for Windows

`samsung_price_widget.py` is a small always-on-top Windows widget (190 x 170
pixels) that shows Samsung Electronics (`005930`) current price, the difference
from the previous successful 10-second query, today's low-price distance, and
the completed-close direction over 1-, 3-, and 5-minute horizons on one compact
line. It also draws a compact 20-minute line chart from completed one-minute
closes; no additional graph is created for the three trend horizons.

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
does not access an account, place/cancel orders, or restart/control the bot.

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

The route is `GET /api/widget/samsung-price` and requires the matching
`X-KORStockScan-Widget-Key` request header. It uses only `POST
/api/dostk/stkinfo`, `api-id: ka10001`, `stk_cd: 005930`, and the `cur_prc`
response field.

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

- Retrieved: `2026-07-31T11:45:32+09:00`
- Upstream: `Kiwoom-Securities/Kiwoom-REST-API`
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`
- Inspected: `kiwoom_docs/종목정보.md`, `kiwoom_docs/차트.md`,
  `examples/국내주식/차트/get_domestic_stock_minute_chart.py`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/client.py`,
  `postman/kiwoom-openapi.postman_collection.json`, and the local
  `docs/kiwoom-api-data-contract.md`.
- Contract used: real `https://api.kiwoom.com`, `POST /api/dostk/stkinfo`,
  `authorization: Bearer ...`, `api-id: ka10001`, body `{"stk_cd":"005930"}`;
  quote value `cur_prc`.

The endpoint uses `ka10001.low_pric` for today's low and `ka10080` with
`tic_scope: "1"` for completed one-minute closes. It derives 1-, 3-, and
5-minute trends locally from contiguous completed closes, requires the
net-change and linear slope direction to agree, and treats movement within
5 basis points as flat. A missing minute makes that horizon unavailable, and
the trend window cannot cross PRE (`08:00`), KRX (`09:00`), or NXT aftermarket
(`15:40`) session starts. Both official request contracts accept `005930_NX`
for NXT, while KRX uses `005930`.
`08:00~08:50 KST` responses retain `market_venue=NXT` for backward
compatibility and expose the project cohort as
`market_cohort=PREMARKET_KRX_LIKE`. The response also exposes
`market_session` and `quote_request_code` for display provenance. The widget
endpoint deliberately does not implement REST/WebSocket auth, REG/REMOVE,
recovery, continuation, order, account, or bot lifecycle flows.
