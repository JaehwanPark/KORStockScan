# Kiwoom API Data Contract

This document fixes the market-data interpretation rules used by runtime and
reporting code. It is a data quality contract only. It must not change real
order authority, threshold/env values, provider routes, bot state, caps, or
quantity guards.

## 0B Trade Aggressor

- Prefer the 0B event's trade price `10`, best ask `27`, and best bid `28`.
- BUY aggressor is inferred only when trade price touches or crosses best ask.
- SELL aggressor is inferred only when trade price touches or crosses best bid.
- Inside-spread trades, missing trade price, missing best quote, stale cached
  quotes, or unsynced ticks are `UNKNOWN`.
- If `27` or `28` is empty or zero, runtime may use a per-code Top-of-Book cache
  only when the cache is fresh and the tick time is synchronized with receive
  time. Cache usage must be logged.
- Do not fall back from missing orderbook-touch evidence to price-change
  direction. Price-change direction is compatibility metadata, not aggressor
  source evidence.

## ka10003

- `ka10003` trade rows expose trade price/change fields, not a reliable
  buy/sell aggressor source.
- `aggressor_source=price_change_heuristic` must be excluded from buy/sell
  pressure and AI compact directional evidence.
- Briefings may display the heuristic source/quality, but must not present it
  as confirmed BUY/SELL trade direction.

## ka10004

- `sel_fpr_bid` is `best_ask`.
- `buy_fpr_bid` is `best_bid`.
- `marketable_buy_touch_price` and `executable_buy_price` mean immediate buy
  touch price and therefore use `best_ask`.
- `marketable_sell_touch_price` and `executable_sell_price` use `best_bid`.
- `passive_buy_price` uses `best_bid`; scale-in passive order price selection
  should prefer this field.
- `passive_sell_price` uses `best_ask`.
- `bid_req_base_tm` is raw provenance only. Freshness must use REST receive
  timestamp or explicitly measured refresh age.

## ka10080 and ka10081

- Continuation is controlled by response `cont-yn` and `next-key`.
- Client code must sort final merged rows oldest to latest:
  - `ka10080`: by `cntr_tm`.
  - `ka10081`: by `dt`.
- Existing return shapes are preserved:
  - `get_minute_candles_ka10080` returns candle rows.
  - `get_minute_candles_ka10080_with_meta` returns `(candles, meta)`.
  - `get_daily_ohlcv_ka10081_df` returns a DataFrame with
    `df.attrs["kiwoom_source_meta"]`.

## String And Sign Parsing

- Price and quantity fields are normalized as unsigned magnitude unless a
  specific API contract says signed quantity is meaningful.
- Rate, change-rate, and net-flow fields preserve sign.
- `pred_pre_sig` direction mapping is:
  - `1`, `2`: positive.
  - `3`: neutral.
  - `4`, `5`: negative.
- `rank_chg_sign` has no confirmed official meaning in the current contract.
  Preserve it as raw provenance only and do not use it for scoring, entry,
  priority, or live authority decisions.
- A 2026-07-03 read-only `ka00198` live sample returned empty, `+`, and `-`
  values for `rank_chg_sign`, and the non-empty signs matched the observed
  `rank_chg` sign in that sample. Treat this as empirical provenance, not an
  official semantic contract. Promotion to decision input requires repeated
  sample logging plus an explicit parser/scoring contract update.
