# Kiwoom API Data Contract

Final audit summary: [`market-data-ai-score-contract-audit-2026-07-06.md`](./market-data-ai-score-contract-audit-2026-07-06.md).

This document fixes the market-data interpretation rules used by runtime and
reporting code. It is a data quality contract only. It must not change real
order authority, threshold/env values, provider routes, bot state, caps, or
quantity guards.

## Official Kiwoom Reference Gate

The official upstream implementation reference is
[`Kiwoom-Securities/Kiwoom-REST-API`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API).
Initial registration was verified at `2026-07-26T19:28:13+09:00` against
upstream `main` commit `1504d45fa145eb11fdd662a08aa9d873eee55849`; this
commit is audit provenance, not a permanent pin. Every change that creates or
modifies a Kiwoom REST or WebSocket request, response parser, realtime FID
mapping, subscription/recovery flow, authentication flow, account/order call,
or continuation handler must inspect the current upstream revision before code
is written.

Required upstream references:

- [`kiwoom_docs`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/kiwoom_docs)
  owns the endpoint, request/response field, and realtime message
  documentation. For WebSocket work, always inspect
  [`실시간시세.md`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/kiwoom_docs/%EC%8B%A4%EC%8B%9C%EA%B0%84%EC%8B%9C%EC%84%B8.md)
  and the relevant REST category document together.
- [`kiwoom/specs.py`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/main/kiwoom/specs.py),
  [`kiwoom/core`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/kiwoom/core),
  and
  [`kiwoom/realtime`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/kiwoom/realtime)
  are implementation and machine-readable contract cross-checks.
- [`postman`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/postman)
  is a request-envelope cross-check.
- [`examples`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/main/examples)
  is sample code only. It must not override the documented contract, local
  safety rules, or observed source-quality requirements, and order examples
  must never be executed merely to validate a code change.
- The
  [Kiwoom OpenAPI portal](https://openapi.kiwoom.com/m/guide/apiguide)
  remains an official conflict/gap reference. If current official sources
  disagree or leave a field undefined, stop semantic promotion and record an
  upstream contract gap instead of guessing.

Before implementation, record the upstream commit SHA, inspected upstream
paths, and retrieval time in the change/review evidence. Verify at least:

1. REST path, `api-id`, headers, request fields, response fields, sign/unit/time
   semantics, continuation headers (`cont-yn`, `next-key`), return/error
   contract, and real/demo separation.
2. WebSocket URL, login and control messages, REG/REMOVE semantics, realtime
   type, item/suffix/route, FID names, field sign/unit/time semantics,
   reconnect/resubscribe behavior, and subscription limits documented by the
   upstream source.
3. Account/order code against the relevant official account/order document,
   while preserving KORStockScan broker, account, order, quantity, cooldown,
   stale/conflict, and hard-safety guards.
4. Parser/request tests for the documented happy path, missing/unknown fields,
   sign and unit preservation, continuation, venue/session routing, and
   redaction of credentials/account identifiers.

Official documentation establishes the vendor protocol, but does not grant
runtime authority. KORStockScan may remain more conservative. An upstream
example or field description must not relax stale/conflict handling, broker
guards, order/quantity limits, provider routes, thresholds, bot state, or
hard/protect/emergency safety. A newly observed field that is absent from the
official contract remains raw/source-quality provenance until its semantics
are confirmed and the local producer-to-consumer contract is reviewed.

### 2026-09-02 ka00198 Lookup-Attention And ka10032 Value-Rank Namespace Gate

- Re-verified at `2026-09-02T09:29:05+09:00` against current upstream commit
  `234560d213acd8871ae344b5481aecd2f30287fa`; inspected
  `kiwoom/_data/kiwoom_api_spec.json` sections `ka00198` and `ka10032`, plus
  `examples/국내주식/종목정보/get_domestic_realtime_stock_rank.py`.
- Official `ka00198` uses `POST /api/dostk/stkinfo` with `api-id=ka00198` and
  required body field `qry_tp` (`1=1 minute`, `2=10 minutes`, `3=1 hour`,
  `4=daily cumulative`, `5=30 seconds`). Its response is an attention ranking:
  `bigd_rank`, signed numeric `rank_chg`, raw `rank_chg_sign`,
  `past_curr_prc`, `base_comp_chgr`, `prev_base_chgr`, `dt`, and `tm`. It does
  not provide an absolute lookup count, an institutional-flow measure, an
  executable BBO, or a request-level KRX/NXT selector.
- The upstream description and example do not establish one unambiguous
  neutral spelling for `rank_chg_sign`. The raw sign remains
  `raw_unverified_not_decision_input`; only the signed numeric `rank_chg` may
  be interpreted, with raw sign consistency retained as source-quality
  diagnostics. Officially documented empty `rank_chg` and example-form `0/N`
  are both valid neutral states. An absent `rank_chg` key, explicit null, or
  non-numeric non-empty value remains a source-quality gap.
- Official `ka10032` `now_rank` and `pred_rank` are respectively the current
  and previous-day trade-value ranks. They are not the current and previous
  `ka00198` lookup ranks. The normalized contract therefore preserves
  `RealtimeLookupRankNow/RealtimeLookupRankChange` separately from
  `ValueRankNow/ValueRankPrevDay`, while legacy `RankNow/RankPrev/RankChange`
  aliases remain compatibility-only. New attribution or tuning consumers must
  not join the legacy aliases across those sources.
- The first lookup-attention prior is a source-only snapshot counterfactual:
  `50% normalized rank level + 35% positive rank change + 15% new top-20
  entry`. It requires the namespaced rank/change and a calendar-valid
  `dt=YYYYMMDD` plus `tm=HHmmss`, records persistence as not yet evaluated, has
  `runtime_effect=false` and `allowed_runtime_apply=false`, and cannot change
  scanner sorting, slot ownership, BUY/DROP, thresholds, provider, order
  price/quantity, cap, broker guards, bot state, or hard safety. A policy
  candidate requires at least 20 completed outcomes across five trading dates
  and cost-adjusted EV review; missing fields are source-quality blocked rather
  than zero-filled.
- The onboarding contract is `metric_role=source_quality_gate`,
  `decision_authority=counterfactual_only`,
  `window_policy=same_day_intraday_light`, and
  `primary_decision_metric=source_quality_adjusted_ev_pct`. The formula itself
  is explicitly `not_ev`; snapshot score, eligible coverage, target/adverse
  first-hit, fill feasibility, and tail loss are secondary diagnostics until
  the completed-outcome floor is met.

### 2026-08-31 ka20003 Request-Market Provenance Gate

- Re-verified at `2026-08-31T07:50:26+09:00` against current upstream commit
  `9180debf7aea0074715dd8f7a15af432afbfc403`; inspected
  `kiwoom/_data/kiwoom_api_spec.json` section `ka20003` and
  `examples/국내주식/업종/get_domestic_all_sector_indices.py`.
- Official `ka20003` uses `POST /api/dostk/sect`, requires header `api-id:
  ka20003`, and requires body `inds_cd`, where `001` selects KOSPI and `101`
  selects KOSDAQ. The response list `all_inds_idex` contains industry/index
  rows but does not repeat the request's parent market on every row.
- `market_panic_breadth_collector` therefore parses the two responses
  separately and persists `source_market=KOSPI|KOSDAQ` from the exact request
  envelope. It must not concatenate both payloads and later infer an industry
  row's parent market from its row code or name.
- Market-specific weakness/recovery requires the index and corroborating
  industry/stock breadth from the same `source_market`. Unscoped legacy rows
  remain audit evidence but cannot support a new single-market scoped alert or
  widget/episode response counterfactual. This remains source-only and grants
  no order, cancellation, exit, threshold, provider, or bot authority.
- Schema-v2 observation identity binds the exact KST timestamp, source-quality
  state, affected/recovery market lists, evidence, and global/per-market release
  margin. Consumers reject identity drift, non-canonical market lists,
  contradictory release checks, and competing observations at the same event
  timestamp instead of selecting one by filename order.

### 2026-08-24 Integrated-SOR Execution Identity Gate

- Re-verified at `2026-08-24T23:42:45+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`; inspected
  `kiwoom_docs/실시간시세.md`, `kiwoom_docs/계좌.md`,
  `kiwoom_docs/주문.md`, `kiwoom/specs.py`, `kiwoom/realtime`, and Postman.
- Official realtime type `00` defines FID `2134` value `0` and FID `2135`
  value `통합` as the integrated execution scope, with FID `2136` carrying
  SOR usage. Those fields do not identify whether KRX or NXT ultimately
  executed an integrated-route order.
- Production type-`00` receipts also contained the wire token `SOR` in FID
  `2135`. The current upstream docs do not enumerate that spelling, so the
  parser accepts it only when the native receipt still agrees on FID `2134=0`
  and FID `2136=Y`. It is normalized to integrated-route scope, retained as
  observed provenance, and never interpreted as an underlying KRX/NXT venue.
- A complete integrated-SOR receipt may therefore preserve exact order and
  execution identity, quantity, price, time, and custody lineage as
  `identity_complete_venue_unresolved`. Its actual venue remains null and it
  is not `complete` execution provenance for venue-specific EV, promotion, or
  runtime approval.
- Same-date journal rows already emitted under provenance v1 remain readable
  only through the frozen v1 state and field contract. V1 cannot emit the new
  unresolved-SOR state or v2-only fields, preventing compatibility reads from
  becoming a schema-drift bypass.
- The bounded state is a source-quality classification only. It does not
  infer an underlying venue, submit or reroute an order, change quantity,
  thresholds, provider, bot state, or bypass any broker or hard-safety guard.

### 2026-08-21 Post-sell Executable-BBO And Rejected-Order Provenance Gate

- Re-verified at `2026-08-21T11:00:23+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`; inspected
  `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/realtime/decoders.py`, `kiwoom/core/ws_client.py`, and Postman
  WebSocket requests. The official type `00` order/execution notice defines
  FID `919` as the raw broker rejection reason.
- The official contract uses `REG` and `REMOVE`; `refresh=1` retains previous
  registrations, and one group accepts at most 100 items. KRX uses the raw
  symbol, NXT uses `_NX`, and the integrated SOR route uses `_AL`. The local
  observer therefore retains an already registered sold symbol instead of
  creating a second subscription owner, and validates the exact frozen sell
  route before accepting a `0D` BBO.
- A confirmed real sell may retain the existing WS subscription for the
  bounded 1/3/5/10-minute horizons plus a 15-second final receipt grace. At
  most eight sell episodes are active. A receipt is valid only while the exact
  route item remains in the manager registration inventory and a same-symbol,
  same-session, exact-route `0D` BBO is at most one second old. Base-symbol
  membership alone is insufficient because plain, `_NX`, and `_AL` are
  separate registrations. While this bounded retention is active, inactive
  target pruning must not demote the route to the micro-reversion source-only
  item. Missing route, route conflict, unsubscribe, stale quote, or missing BBO
  produces an explicit source-quality result rather than mark-price
  substitution.
- Type `00` status `거부` preserves FID `919` without interpreting an
  undocumented numeric meaning and emits an exact-order execution-quality
  provenance receipt. It does not automatically retry, cancel, reroute, resize,
  or change an order; broker/account reconciliation remains the runtime owner.
- The post-sell retention path is observation-only. The rejected-order path is
  receipt-only for an already submitted real order. Neither path sends
  `REG`/`REMOVE`, submits or cancels an order, changes entry/exit logic,
  thresholds, quantity, provider, bot state, or bypasses
  broker/account/cooldown/stale/hard-safety guards.

### 2026-08-20 Episode Realized-PnL Account Gate

- Re-verified at `2026-08-20T14:59:07+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/계좌.md`,
  `examples/국내주식/계좌/get_domestic_realized_pnl_by_period_and_stock.py`, and
  `kiwoom/specs.py` for `ka10073`. The official request is
  `POST /api/dostk/acnt` with `api-id=ka10073` and required `stk_cd`,
  `strt_dt`, and `end_dt`; continuation uses the standard `cont-yn` and
  `next-key` headers. The `dt_stk_rlzt_pl` response supplies date, symbol,
  filled quantity, buy/sell average price, realized profit, profit rate,
  commission, and tax.
- The endpoint is read-only and is consumed only by the episode POSTCLOSE
  report. Exact account PnL is accepted only after unique symbol-day owner,
  quantity, average-price, and gross-minus-cost reconciliation. Ambiguous or
  failed reconciliation falls back to a fixed cost estimate and cannot change
  orders, target ticks, quantity, custody, provider, bot, cap, or broker guard.

### 2026-08-18 WebSocket Reconnect Resubscription Readiness Gate

- Re-verified at `2026-08-18T09:12:13+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/core/ws_client.py`, and
  `kiwoom/realtime/packets.py` for LOGIN acknowledgement, REG/REMOVE packet
  shape, `grp_no`, `refresh=1`, item/type registration, connection-close
  handling, and the requirement to send subscriptions only on an established
  WebSocket session.
- Local `_session_ready` now becomes true after the LOGIN acknowledgement and
  the account/order (`00`) and market-session (`0s`) bootstrap registrations,
  before the reconnect path restores the existing symbol inventory. This
  closes the prior circular wait in which reconnect restoration called the
  normal REG sender while the same bootstrap still owned the unset readiness
  event and therefore timed out after ten seconds.
- The repair changes connection lifecycle ordering only. It does not change
  realtime types, venue suffixes/routes, item limits, scanner selection,
  provider, threshold, order price/quantity, broker/account/order/cooldown, or
  hard/protect/emergency safety authority.

### 2026-08-13 Samsung Morning Exact-Date Manual Add-on Order Gate

- Re-verified at `2026-08-13T07:20:00+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, and
  `postman/kiwoom-openapi.postman_collection.json` for `kt10000`, `kt10003`,
  `kt00007`, `ord_qty`, `cntr_qty`, `ord_remnq`, `cntr_uv`, `cncl_qty`,
  `orig_ord_no`, and `dmst_stex_tp`. The official contract keeps order/cancel at
  `POST /api/dostk/ordr`, accepts `NXT|SOR`, defines quantity in shares, and
  documents `cncl_qty=0` as cancel-all-remaining for the exact original order.
  `kt00007` returns order, filled, and remaining quantity in one-share units;
  normal-machine reconciliation remains fixed at one share while the add-on
  requires the exact submitted quantity, bounded to `1..50`, on every lookup.
- The user-directed `2026-08-13` add-on has a separate state, lock, order
  ledger, env key, live confirmation, and non-persistent exact-date timer. It
  follows only accepted BUY legs while the normal Samsung morning episode and
  the exact source leg are still active, and submits at most two 50-share BUY
  orders at the same route and price. A terminal source episode or completed
  source leg cannot be mirrored late. If the normal leg migrates from NXT to
  SOR after reconciliation, only the unfilled add-on remainder may follow it.
- The add-on may cancel only its exact owned BUY-order remainder. It has no
  SELL endpoint, target, stop, forced exit, quantity escalation, provider/bot
  control, or authority over the normal episode/widget/main-bot orders. Filled
  quantity is recorded as `manual_sell_required_quantity` and is handed to the
  operator for manual sale. The normal 1-share-by-2-leg episode remains
  unchanged.

### 2026-08-20 Episode Held-Inventory Read And Manual-Exit Gate

- Re-verified at `2026-08-20T15:34:48+09:00` against upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`; inspected `계좌.md`, API spec,
  `kiwoom/specs.py`, `kiwoom/core`, and Postman for `kt00007`, `ord_dt`,
  `ord_no`, `ord_qty`, `cntr_qty`, `ord_remnq`, `cntr_uv`, `cont-yn`, and
  `next-key`.
- Episode `ka10080` and `kt00007` reads share the 0.4-second cross-process
  pacer and bounded `1700`/HTTP 429 backoff. Successful identical `kt00007`
  pages may be reused inside one process for at most one second. `kt10000`,
  `kt10001`, and `kt10003` writes remain outside retry/cache paths.
- Manual-exit state reconciliation requires one unique completed `kt00007`
  SELL receipt matching the explicit episode owner symbol, order date, order
  number, exact whole held quantity, and zero remainder. It refuses an active
  target, partial prior exit, cross-owner aggregate allocation, or account
  balance inference and has no broker-write authority. A global receipt
  registry reserves the exact order identity before the owner state write, so
  one manual sell cannot be allocated to multiple profile ledgers.

### 2026-08-13 General Scalping Margin One-Share Orderability Gate

- Re-verified at `2026-08-13T11:41:09+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/계좌.md`, `kiwoom_docs/주문.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, and
  `postman/kiwoom-openapi.postman_collection.json` for `kt00011`, `kt10000`,
  `kt10006`, raw six-digit `stk_cd`, KRW `uv`, `aplc_rt`,
  `profa_{20|30|40|50|60|100}ord_alow_amt/q`, and
  `min_ord_alow_amt/q`.
- General SCALPING entry may use the applied `20/30/40/50/60%` bucket only as
  a cash-shortfall fallback. The same symbol and exact positive limit price
  must return no error, a recognized discrete tier, orderable quantity at
  least one, and orderable amount at least the checked unit price. Exact-price
  cash capacity remains primary when it can buy one share. Unknown, malformed,
  `100%`, missing, mismatched-price, market-price-zero, zero-quantity, or
  insufficient-amount responses fail closed.
- Authority is rechecked at initial sizing, at the most expensive executable
  pre-submit price, and once more at each resolved broker limit price. A
  margin-authorized path submits only when the resolved leg is exactly one
  share and has a positive limit price. It uses the ordinary domestic stock
  BUY API `kt10000`; credit-order API `kt10006` is forbidden.
- Margin authority changes only the capacity source passed into the existing
  `position_sizing_dynamic_formula` allocator. It does not increase an
  allocator-approved quantity: the stage cap is one share. Probe expansion,
  residual multi-leg expansion, and every real scale-in are forbidden for the
  resulting position lifecycle. Existing stale/conflict, effective-price,
  liquidity/microstructure, account/order/cooldown, position, broker-response,
  and hard/protect/emergency guards remain in force.
- BUY/SELL receipt snapshots preserve exact-price, tier, capacity, ordinary
  order API, cash-bypass, and scale-in-forbidden provenance for the position
  lifecycle. Rollback is
  `KORSTOCKSCAN_GENERAL_ENTRY_MARGIN_ONE_SHARE_ENABLED=false`; rollback restores
  cash-only general entry. The former Opening Rotation margin contract was
  retired on 2026-08-14 and has no active authority.

### Archived 2026-08-10 Opening Rotation Margin Orderability Gate

This section is protocol/audit history only. `opening_rotation_full_retirement_20260814`
removed its new-order and margin authority; none of the fields below can
reactivate it.

- Rechecked at `2026-08-10T18:35:18+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/계좌.md`, `kiwoom_docs/주문.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `postman/kiwoom-openapi.postman_collection.json`, and the official
  `get_domestic_orderable_quantity_by_margin_rate.py` example for `kt00011`
  and `kt10000`.
- `kt00011` remains `POST /api/dostk/acnt` with raw six-digit `stk_cd` and an
  optional KRW `uv`. Its `aplc_rt` selects the applied margin-rate bucket and
  the matching `profa_{20|30|40|50|60|100}ord_alow_amt/q` fields provide KRW
  orderable amount and one-share quantity. `min_ord_alow_amt/q` remains the
  explicitly non-margin orderable capacity.
- While active, Opening Rotation could replace its cash-only sizing input with the applied
  `20/30/40/50/60%` bucket only when the exact symbol/price response has
  `return_code=0`, a recognized bucket, orderable quantity at least one, and
  orderable amount at least the checked unit price. It rechecks the most
  expensive executable pre-submit price. A missing/error response, an unknown
  or `100%` applied rate, zero quantity, inconsistent amount, or a failed
  exact-price recheck cannot grant margin authority.
- `aplc_rt` is matched as an exact discrete integer tier. A fractional or
  malformed percentage is not rounded into an eligible bucket, and the local
  `uv` request provenance must exactly match the price being authorized.
- The resulting capacity enters the existing central sizing allocator as a
  broker quantity cap; Opening then reduces an allocator-approved positive
  quantity to exactly one share. The actual order remains ordinary KRX
  `kt10000` DAY limit BUY. It does not use the credit-order API `kt10006`,
  increase quantity, enable scale-in, or bypass time, stale/conflict,
  specialist-owner, account/order/cooldown, absolute-budget, position,
  broker-response, or hard/protect/emergency safety vetoes.
- BUY/SELL receipts retain `margin_order_api=kt10000` and
  `margin_credit_order_api_used=false`. A missing or conflicting value in any
  event of a margin-authorized episode blocks that episode set from postclose
  tuning authority; later normal defaults cannot erase the earlier evidence.

### 2026-08-08 Widget Signal Auto-Trade Order Gate

- Retrieved at `2026-08-08T13:11:22+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/주문.md`, `kiwoom_docs/계좌.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, and
  `postman/kiwoom-openapi.postman_collection.json` for `kt10000`, `kt10001`,
  `kt10003`, and `kt00007`.
- The widget executor uses the ordinary domestic stock order contract. It
  does not call an orderable-cash/deposit endpoint and does not infer that the
  API request itself grants margin eligibility; account configuration and the
  broker response remain authoritative. It does not substitute the credit
  order API `kt10006`.
- Only fills matched to the executor's exact current-trade-date order numbers
  enter its sellable ledger. Aggregate holdings and prior-day quantities are
  forbidden sell inputs. The gateway reads the existing shared token cache
  only and has no issue/refresh fallback.

### 2026-08-12 Widget Successor-Order Reconciliation Gate

- Re-verified at `2026-08-12T14:42:04+09:00` against upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/계좌.md`, `kiwoom_docs/주문.md`,
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, and
  `postman/kiwoom-openapi.postman_collection.json` for `kt00007` order detail,
  `ord_no`, `orig_ord_no`, `ord_qty`, `cntr_qty`, and `ord_remnq`.
- A broker correction or replacement may have a new order number linked to the
  widget-owned root through `orig_ord_no`. Reconciliation follows only an
  exact same-symbol descendant chain when the root has zero fill and explicit
  zero remainder. It rejects missing quantity/remainder fields and oversized
  successors. A partially filled root is never combined with a descendant,
  preventing ambiguous fill aggregation and accidental excess sell quantity.

### 2026-08-07 Daily Runtime Token Ownership Gate

- Retrieved at `2026-08-07T09:03:03+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/auth.py`,
  `kiwoom/core/token_store.py`, `kiwoom/core/ws_client.py`,
  `kiwoom_docs/실시간시세.md`, and the production/mock OAuth entries in
  `postman/kiwoom-openapi.postman_collection.json`.
- Official `au10001` remains `POST /oauth2/token` with
  `grant_type=client_credentials`, `appkey`, and `secretkey`; the response owns
  `token`, `token_type`, and `expires_dt`. The official SDK permits a valid
  persistent file token cache and refreshes before expiry; it also retries a
  WebSocket LOGIN once after an authentication refresh.
- The local live-engine startup is stricter: it may reuse a shared token only
  when its cache `issued_at` belongs to the current KST date and it passes the
  existing expiry safety margin. A prior-day or missing-issuance cache is
  refreshed once under the shared file lock before long-lived REST/WS owners
  are bound. Same-day restarts reuse the same valid shared token, preventing
  repeated issuance and cross-process invalidation.
- A fresh REST 8005 is not restart authority when the same runtime log window
  proves a successful same-request retry and `api_8005_retry:*:retry_success`
  token handoff with no later 8005 or recovery-failure marker. Untimestamped,
  repeated-after-handoff, refresh-failed, or retry-failed incidents remain
  actionable and keep the existing restart cooldown/daily cap contract.
- This gate changes authentication lifecycle and incident attribution only. It
  grants no threshold, provider, order, quantity, cap, stale/conflict, broker,
  or hard-safety authority.

### 2026-08-04 SOR Post-Probe Execution-View Gate

- Retrieved at `2026-08-04T09:20:35+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/realtime/events.py`, `kiwoom/realtime/decoders.py`, and
  `kiwoom/specs.py`.
- The official realtime contract identifies a SOR subscription item as
  `039490_AL`, KRX as `039490`, and NXT as `039490_NX`. The 0B contract keeps
  signed field `15` as BUY/SELL execution-volume provenance and exposes
  exchange fields such as `9081`; 0D owns the executable orderbook view.
- `_AL` proves a SOR execution view, not the underlying exchange of an
  individual event. Post-probe may therefore consume fresh, route-consistent
  `_AL` 0B/0D only when the filled probe has a frozen `SOR` broker route, an
  active position, a bundle ID, fill price, and fill timestamp. Venue
  attribution to an underlying KRX/NXT execution exchange remains false.
  Missing frozen fill lineage or any route/suffix conflict fails closed.
- A pre-submit pressure snapshot cannot be reused as post-fill signed-pressure
  evidence. Mixed QI/OFI orderbook evidence remains mixed rather than being
  promoted to a positive or negative venue signal. These source corrections
  do not bypass AI DROP, broker/account/order/quantity/cooldown, stale quote,
  price freshness, exit-token, or hard/protect/emergency guards.

### 2026-08-10 Micro-Reversion SOR Forward-Collection Gate

- Retrieved at `2026-08-10T08:14:48+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/realtime/events.py`, `kiwoom/realtime/decoders.py`,
  `kiwoom/specs.py`, and `postman/kiwoom-openapi.postman_collection.json`.
- Micro-reversion forward collection may preserve an explicit `_AL` item as
  `venue=SOR` and partition it into `SOR_PREMARKET`, `SOR_REGULAR`, or
  `SOR_AFTERMARKET`. This is route attribution only: it must not be relabeled
  as KRX or NXT, combined with exchange-specific cohorts, or used as execution
  venue proof. Optional/empty 0B field `9081` does not invalidate the SOR route
  item and grants no KRX/NXT inference authority; a conflicting declared venue
  still fails closed.
- This change adds no REG/REMOVE request, subscription item, order, threshold,
  provider, quantity, cap, broker-guard, or bot-state authority.

### 2026-08-14 Micro-Reversion Gap Collection Feedback Gate

- Re-verified at `2026-08-14T15:32:56+09:00` against current upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/realtime/events.py`, `kiwoom/realtime/decoders.py`,
  `kiwoom/realtime/schemas.py`, `kiwoom/realtime/stream.py`,
  `kiwoom/core/ws_client.py`, `kiwoom/_data/kiwoom_api_spec.json`, and
  `postman/kiwoom-openapi.postman_collection.json` for REG/REMOVE, `refresh`,
  item suffixes, type arrays, 0B, and 0D.
- Official REG keeps prior item/type registrations with `refresh=1`; `data[].type`
  is an array and the official builders accept caller-selected realtime types.
  The collection feedback path therefore registers only `0B` and `0D`. It does
  not add order/position type `00`, program type `0w`, or broker type `0F`.
- The exact-date target preserves plain code as KRX, `_NX` as NXT, and `_AL` as
  integrated SOR. One route is selected per symbol per date; an `_AL` row remains
  SOR and is never relabeled as an underlying KRX/NXT event.
- Registration is bounded by the existing WS item budget and the daily feedback
  budget. Source-only ticks reach only the micro forward collector and are
  suppressed before the common realtime trading event and other strategy
  observers. A normal runtime target for the same code first removes the old
  route, registers the normal route/types, and only after successful transport
  send removes that suppression; REMOVE failure stays fail-closed. No
  order/account/quantity/cooldown/stale/hard-safety guard is changed.
- The next exact-date set replaces the prior source-only set, and reconnect
  restoration keeps source-only codes on 0B/0D only. Manual-control exclusions
  are not collection filters. The target artifact and runtime event require
  `market_data_subscription_effect=true`, `trading_runtime_effect=false`,
  `trading_decision_effect=false`,
  `actual_order_submitted=false`, and `broker_order_forbidden=true`.

### 2026-08-10 Micro-Reversion 0B Timestamp-Regression Gate

- Retrieved at `2026-08-10T12:13:31+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/realtime/events.py`, `kiwoom/realtime/decoders.py`,
  `kiwoom/specs.py`, and the Postman collection. The official 0B contract
  defines FID `20` only as optional String `체결시간`; it does not declare
  monotonic arrival ordering or authorize the client to rewrite the value.
- The observed incident kept source sequence `27580 -> 27581` and local receive
  time `11:33:54.121 -> 11:33:54.125` monotonic while FID `20` moved
  `11:33:54 -> 11:33:53`. Runtime therefore preserves the immutable row in
  canonical stream V3, marks it `path_consumer_eligible=false`, and quarantines
  it from detector, path, and P2 consumers when the exchange-time regression is
  at most `1,000ms`.
- Source-sequence regression, local-receive-time regression, or exchange-time
  regression above `1,000ms` remains an observer canary hard stop. Runtime does
  not reorder, impute, clamp, or relabel the official exchange timestamp. A
  quarantined row cannot fill Gate B path coverage or support economic, sim, or
  live promotion.
- This source-quality handling adds no subscription, REG/REMOVE, order,
  threshold, provider, quantity, cap, broker-guard, or bot-state authority.

### 2026-07-27 ka10017 Previous-Limit-Down Observation Gate

- Retrieved at `2026-07-27T16:01:10+09:00` from upstream commit
  `1504d45fa145eb11fdd662a08aa9d873eee55849`.
- Inspected `kiwoom_docs/종목정보.md`,
  `examples/국내주식/종목정보/get_domestic_upper_lower_limit_stocks.py`, the
  local `ka10081` parser, and the existing REG/REMOVE implementation.
- The source-only observer uses `POST /api/dostk/stkinfo`,
  `api-id=ka10017`, with `mrkt_tp=000`, `updown_tp=7`, `sort_tp=2`,
  `stk_cnd=10`, `trde_qty_tp=00000`, `crd_cnd=0`, `trde_gold_tp=0`, and
  `stex_tp=1`. The documented five-character `00000` is canonical. A
  read-only production smoke confirmed that it and the example's `0000`
  currently return `return_code=0`; runtime does not silently switch away
  from the documented value.
- `updown_pric[*].cnt` is required consecutive-count provenance. Missing,
  non-numeric, or non-positive values are row-level source-quality blocks.
  `cnt=1` maps to `single_limit_down`; `cnt>=2` maps to
  `consecutive_limit_down_2plus`.
- The response current price is not used as the prior limit-down close. Price
  band authority requires the latest completed `ka10081` row strictly before
  the target date to match `daily_stock_quotes` on symbol, date, and close.
  Missing or conflicting rows fail closed.
- `ka10001.lst_pric` is the current KRX lower-limit price used only for
  intraday `LIMIT_LOCKED/UNLOCKED/RELOCKED` observation. It grants no BUY,
  order, threshold, provider, quantity, cap, broker-guard, or bot authority.

## 0B Trade Aggressor

- Prefer the 0B event's explicit signed trade volume `15` when it starts with
  `+` or `-`. `+` is BUY taker-side pressure and `-` is SELL taker-side
  pressure.
- Preserve the 0B event's trade price `10`, best ask `27`, and best bid `28` as
  touch/cross validation fields. BUY touch is inferred when trade price touches
  or crosses best ask. SELL touch is inferred when trade price touches or
  crosses best bid.
- When signed `15` is explicit, runtime stores `aggressor_source` as
  `kiwoom_0b_signed_trade_volume` and preserves the quote comparison in
  `aggressor_touch_*`. If signed `15` conflicts with the touch/cross result,
  the signed side remains primary and `aggressor_touch_confirms_signed=false`
  is logged for source-quality review.
- When signed `15` is missing or neutral, trusted fallback may use 0B inline
  `10`/`27`/`28` touch evidence or a fresh synchronized top-of-book cache.
- In this codebase, `BUY`/`SELL` aggressor means marketable taker-side pressure
  for buy/sell pressure math. `10 == 27` is BUY touch/cross evidence and
  `10 == 28` is SELL touch/cross evidence when the signed `15` field is not
  available.
- Inside-spread trades, missing trade price, missing best quote, stale cached
  quotes, or unsynced ticks are `UNKNOWN` only for the touch/cross fallback.
  They do not erase an explicit signed `15` side.
- If `27` or `28` is empty or zero, runtime may use a per-code Top-of-Book cache
  only when the cache is fresh and the tick time is synchronized with receive
  time. Cache usage must be logged.
- Runtime also stores field `15` in additive `aggressor_aux_*` fields for
  diagnostics. `aggressor_aux_pressure_usable` remains false because pressure
  authority belongs to the primary `aggressor_source` contract, not to the
  auxiliary weighted score.
- A bounded submit-safety consumer may use repeated official signed `15`
  SELL prints only as negative-veto provenance for latency direct-canary
  interpretation. This use must log separate `signed_tape_*` provenance, must
  require a minimum sample count, and must not create BUY support, pressure
  math, scale-in support, exit authority, threshold mutation, provider changes,
  or order-cap changes.
- Runtime may also store a weighted auxiliary observation score from `15`,
  `1030`, `1031`, `13`, `228`, and previous tick price. This score is empirical
  diagnostics only. It does not promote the row to trusted pressure, and it
  cannot support entry/scale-in/exit gates by itself.
- Runtime parses 0B auxiliary volume/value fields with this priority:
  `1031` is BUY execution volume, `1030` is SELL execution volume, and `1032`
  is the raw buy-ratio field. When both `1030` and `1031` are present, their
  sum is the preferred tick volume for packet-level calculations. If the
  `1030+1031` sum differs from `abs(15)`, preserve
  `trade_volume_1030_1031_vs_15_mismatch` and delta provenance instead of
  silently normalizing one side.
- Runtime uses 0B `1313` as the primary momentary trade value. If `1313` is
  missing or invalid, it falls back to `abs(price) * (1030+1031)` when both
  split volumes are available, then `abs(price) * abs(15)` when split volumes
  are unavailable. Fallback values are approximate and must carry
  `tick_trade_value_source` plus `tick_trade_value_fallback_volume_source`.
- Runtime accumulates 0B parser provenance in the websocket snapshot as
  `kiwoom_0b_1313_missing_rate_pct`, `kiwoom_0b_trade_value_source_counts`,
  `kiwoom_0b_trade_volume_source_counts`, and
  `kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct`. Feature packets also carry
  recent-window `tick_trade_value_source_counts`, `trade_volume_source_counts`,
  `trade_volume_1030_1031_vs_15_mismatch_rate_pct`, and
  `tick_aggressor_source_counts`. These fields are source-quality/report-only
  instrumentation and cannot create BUY, submit, threshold, provider, bot, or
  cap authority.
- Do not fall back from missing orderbook-touch evidence to price-change
  direction. Price-change direction is compatibility metadata, not aggressor
  source evidence.

## ka10003

- `ka10003` trade rows expose trade price/change fields, not a reliable
  buy/sell aggressor source.
- `aggressor_source=price_change_heuristic` must be excluded from buy/sell
  pressure and AI compact directional evidence.
- Raw `cntr_infr` rows may be summarized by
  `ka10003_buy_dominance_observation` only as `source_quality_only`: use
  `1031/1030` split quantities first when present, signed `15` or
  `cntr_trde_qty` second, and quote-touch comparison only when the original row
  carries best ask/bid fields. Inside-spread rows are excluded by default.
- The observation may log `source_counts`, `trade_value_source_counts`,
  `inside_spread_count`, and `split_vs_15_mismatch_count`, but it must not fill
  `buy_pressure_10t`, `net_aggressive_delta_10t`, `tick_aggressor_trusted_count`,
  or submit/entry/scale-in pressure fields.
- Runtime context flattens those observation counters as
  `ka10003_buy_dominance_observation_source_counts`,
  `ka10003_buy_dominance_observation_trade_value_source_counts`,
  `ka10003_buy_dominance_observation_inside_spread_count`,
  `ka10003_buy_dominance_observation_split_vs_15_evaluable_count`, and
  `ka10003_buy_dominance_observation_split_vs_15_mismatch_count` so postclose
  source-quality reports can automatically measure source mix, 1313 fallback
  use, inside-spread frequency, and 1030/1031-vs-15 mismatch rate.
- When the split-vs-15 observation is evaluable, postclose
  `microstructure_reaction_context` may create a source-only
  `instrumentation_order` for parser/provenance review. That order remains
  `runtime_effect=false` and cannot promote `ka10003` to pressure authority.
- Briefings may display the heuristic source/quality, but must not present it
  as confirmed BUY/SELL trade direction.
- Adding best bid/ask to a `price_change_heuristic` tick later must not promote
  it to `orderbook_touch`. It remains untrusted unless the original source is a
  trusted 0B orderbook-touch or explicitly trusted provider-declared side.

## ka10084

- `ka10084` today/prior trade rows expose signed `cntr_trde_qty`.
- Runtime may use `ka10084` only through the scanner/pre-AI/submit freshness
  envelope or historical log consumers. It is no longer called as a submit-time
  direct-canary retry/fallback.
- Scanner/pre-AI freshness envelope may attach bounded recent `ka10084` rows as
  signed-tape provenance. This consumer may only classify
  `sell_dominated` as scanner budget reallocation or submit-safety negative
  context.
- `ka10084` signed rows are auxiliary negative-veto provenance. Repeated recent
  SELL rows may block or annotate direct-canary interpretation when already
  present in the freshness envelope, especially when 0B tape is stale or
  missing.
- `ka10084` must not create BUY support, pressure math, scale-in support, exit
  authority, threshold mutation, provider changes, order-cap changes, or broker
  guard bypass.
- Intraday observation is automated through pipeline event fields and the
  postclose `microstructure_reaction_context` source-only report:
  `market_data_signed_tape_state`,
  `market_data_rest_signed_tape_pressure_usable`, `rest_signed_trade_ticks`,
  and `latency_true_ofi_direct_canary_signed_tape_*`. These fields are
  provenance/source-quality diagnostics only; a nonzero
  `market_data_rest_signed_tape_pressure_usable=true` count is a contract
  violation to review, not runtime approval.
- Postclose workorders may use these counts to request source-only monitoring,
  negative-veto design review, or forbidden-use repair. They must not enable
  BUY support, pressure math, submit-time REST retry, or broker guard bypass
  without a separate guarded runtime candidate.

## ka10046

- `ka10046` strength trend uses `/api/dostk/mrkcond` with `api-id=ka10046`
  and returns server-side aggregate strength trend rows such as `cntr_str_tm`.
- Websocket 0B remains the primary input for live short-window strength,
  trade-value, signed tape, and split-volume windows. `ka10046` may only fill
  realtime context as `ka10046_rest_fallback` when fresh 0B-derived strength is
  absent or stale.
- When `v_pw_source=ka10046_rest_fallback`, runtime context must set
  `v_pw_runtime_support_usable=false`; the REST value may be displayed and
  audited but must not create a positive timing score by itself.
- Runtime context preserves `v_pw_ws_value` and `v_pw_rest_value` separately so
  postclose source-quality reports can measure WS 0B vs `ka10046` divergence
  without changing runtime authority.
- `ka10046` rows carry `source=ka10046_rest_strength_trend`,
  `decision_authority=strength_trend_rest_fallback_source_only`, and
  `runtime_effect=false`. Its receive timestamp is client-side
  `rest_received_ts_ms`; REST aggregate row time must not be treated as
  sub-second quote freshness.
- `acc_trde_prica` is cumulative trade amount. It may populate
  `today_turnover`, but it must never backfill `curr_price` or executable quote
  fields.
- `ka10046` must not create standalone BUY support, pressure math, submit
  permission, threshold mutation, provider changes, order-cap changes, bot
  restart authority, broker guard bypass, or real execution-quality approval.
- Postclose `microstructure_reaction_context` automatically emits source-only
  workorders when `ka10046_strength_runtime_effect_true_count` or
  `ka10046_strength_missing_received_ts_count` is nonzero. These workorders
  close instrumentation/provenance gaps only and do not authorize runtime
  application.

## Aggressor Pressure Field Contract

| Field | Meaning | Required provenance | Runtime use | Postclose use |
| --- | --- | --- | --- | --- |
| `aggressor_side` / `dir` | Raw or normalized side label from the producer. | Trusted only with `aggressor_source` in `kiwoom_0b_signed_trade_volume`, `orderbook_touch`, `cached_orderbook_touch`, `provider_declared_side`, `exchange_declared_side`, `trusted_declared_side`, or `declared_aggressor_side`. | Source-less side labels are display/provenance only. | Source-less side labels cannot support tuning candidates. |
| `buy_pressure_10t` | BUY aggressive volume share over trusted pressure rows. Neutral `50.0` when no trusted pressure rows exist. | `tick_aggressor_pressure_usable=true` or `tick_aggressor_trusted_count>0`. | May support entry/scale-in only when provenance is usable and other guards pass. | Rows using this field with unusable provenance are source-quality exclusions. |
| `net_aggressive_delta_10t` | Trusted BUY volume minus trusted SELL volume. Neutral `0` when no trusted pressure rows exist. | Same as `buy_pressure_10t`. | Must not interpret heuristic-only ticks as sell/buy pressure. | Same exclusion rule as `buy_pressure_10t`. |
| `tick_aggressor_source_counts` | Diagnostic source distribution for all inferred tick rows. | Additive provenance field. | Logging and source-quality only. | Used to diagnose contamination paths. |
| `tick_aggressor_trusted_count` | Count of pressure rows allowed into buy/sell volume math. | Derived from trusted source allowlist. | Must be positive for directional pressure support. | Required by pressure-consuming source-quality contracts. |
| `tick_aggressor_pressure_usable` | Boolean pressure usability gate. | Derived from trusted pressure rows. | False means neutral/insufficient, not bearish. | False plus a pressure value is a hard source-quality exclusion for pressure-consuming stages. |
| `aggressor_aux_*` | Auxiliary interpretation of non-primary fields such as execution imbalance `1030`/`1031`, cumulative volume delta `13`, trade strength `228`, and previous price movement. The same raw 0B `15` value is preserved as auxiliary provenance but the explicit `+`/`-` sign is the primary `kiwoom_0b_signed_trade_volume` side when present. | `aggressor_aux_pressure_usable=false`. | Display/provenance only; never separate pressure support. Repeated official signed `15` SELL rows may only add negative direct-canary provenance through separately logged `signed_tape_*` fields. | Source-quality diagnostics only. |
| `tick_trade_value` / `tick_trade_value_source` | Momentary 0B trade value and its derivation. | Prefer `1313`; fallback only as `calc_price_x_1030_1031_sum` then `calc_price_x_15_abs`. | May feed strength momentum only with source provenance. | Fallback source is required for source-quality review and unit/range checks. |
| `trade_volume_1030_1031_vs_15_mismatch` | Whether split volume sum differs from signed `15` absolute volume. | Requires both `1030/1031` and `15` parsed. | Diagnostic/source-quality only; not a trading signal. | Used to measure vendor packet pattern and decide future parser refinements. |
| `kiwoom_0b_*` parser counters | Latest websocket cumulative snapshot for actual received 0B packet provenance. | Updated only by the 0B websocket parser. | Source-quality/report-only observation of `1313` absence, value/volume source mix, and split-vs-15 mismatch. | Must not be interpreted as edge, BUY support, submit permission, threshold mutation, provider route change, bot restart, or cap release. |
| `signed_tape_*` | Bounded negative submit-safety view of official signed tape over a short recent window. | Raw signed `15` values from 0B `recent_trade_ticks` or `last_trade_tick`, or freshness-envelope REST `ka10084.cntr_trde_qty`; minimum sample count required. | May block or annotate latency direct-canary interpretation when the signed tape is sell-dominated; submit-time REST retry is forbidden. | Source-quality diagnostics and false-positive review only; not EV/apply support by itself. |
| `microstructure_reaction_context_status` | Reaction context quality. | Requires fresh orderbook, enough ticks, and usable pressure. | `source_quality_partial` is neutral unusable. | Preserved as report-only feature context. |

### Producer To Consumer Trace

| Producer | Intermediate artifact/log field | Runtime consumers | Postclose consumers | Contract |
| --- | --- | --- | --- | --- |
| 0B websocket trade event | `recent_trade_ticks[].aggressor_source=kiwoom_0b_signed_trade_volume` when FID15 has an explicit sign, plus `signed_trade_volume`, `buyer_vol`, `seller_vol`, `tick_trade_value_source`, `aggressor_touch_*`, `best_ask`, `best_bid`, cache/sync fields | `scalping_feature_packet`, `microstructure_reaction_context`, strength momentum | `pipeline_events` feature/audit fields | Explicit signed FID15 is primary taker-side provenance. `1030/1031` are preferred split volumes for packet volume/value fallback, and `1313` is primary momentary value. When the sign is missing or neutral, trusted fallback remains `orderbook_touch|cached_orderbook_touch` only when quote is complete, fresh, and synchronized. |
| `ka10003` tick history | `aggressor_source=price_change_heuristic`, compatibility `dir`, optional `ka10003_buy_dominance_observation` from raw `cntr_infr`, plus flat `ka10003_buy_dominance_observation_*` counters | Tick acceleration and price-change diagnostics only | Briefing/provenance/source-quality diagnostics and `microstructure_reaction_context` source-count aggregation | Forbidden as buy/sell pressure source. Split/signed/quote-touch observation stays `source_quality_only` and cannot become pressure math or submit support. |
| `ka10084` signed trade envelope input | `rest_signed_trade_ticks[].signed_trade_volume`, `aggressor_source=kiwoom_rest_ka10084_signed_trade_qty`, `market_data_signed_tape_state`, `market_data_rest_signed_tape_pressure_usable`, `latency_true_ofi_direct_canary_signed_tape_*` | Scanner budget reallocation, submit-safety negative provenance, and latency true-OFI direct-canary interpretation only | False-positive/source-quality diagnostics only; `microstructure_reaction_context` aggregates state counts, REST tick source counts, pressure-usable true violations, signed-tape sell-dominated counts, latest-side counts, and tape block reasons. | Forbidden as BUY support, pressure math, or submit-time retry. |
| `ka10046` strength trend | `v_pw_source=ka10046_rest_fallback`, `v_pw_runtime_support_usable=false`, `v_pw_ws_value`, `v_pw_rest_value`, `ka10046_strength_*`, `rest_received_ts_ms`, aggregate `strength/s5/s20/s60/acc_amt/trde_qty` | Realtime context fallback/provenance only when WS 0B strength is absent; `acc_amt` may fill turnover only; REST fallback cannot create positive timing score by itself | `microstructure_reaction_context` source-quality summary aggregates fallback rate, fallback quote freshness, missing receive timestamp, runtime-effect violations, and WS-vs-REST strength divergence | REST aggregate strength is delayed/source-only. Forbidden as standalone BUY support, pressure math, executable price, submit permission, runtime apply, or safety bypass. |
| market-data freshness envelope | `market_data_freshness_state`, `market_data_orderbook_state`, `market_data_signed_tape_state`, `market_data_effective_price_source` | Scanner fast-precheck, rising-missed scout quality, submit-safety provenance | Source-quality diagnostics only | REST orderbook may repair stale quote/depth freshness; REST signed tape may only reallocate scanner budget or add negative-veto provenance. Forbidden as BUY support, pressure math, threshold/provider/order-cap change, broker guard bypass, or real execution-quality approval. |
| `microstructure_reaction_context` | `tick_aggressor_*`, `buy_pressure_pct`, `source_quality_partial` | Entry reaction, scale-in quality snapshots, holding/exit matrix | `microstructure_reaction_context_YYYY-MM-DD`, source-quality audit | Unusable pressure returns neutral scores and source-quality provenance. |
| `scalping_feature_packet` | `buy_pressure_10t`, `net_aggressive_delta_10t`, `tick_aggressor_*`, `microstructure_reaction_*` | AI compact payload, entry gates, AVG_DOWN/PYRAMID/REVERSAL_ADD gates | `pipeline_events`, `observation_source_quality_audit`, backtests/calibration | Additive provenance fields must travel with pressure values. |
| `observation_source_quality_audit` | `tick_aggressor_pressure_usable_contract` row exclusion | None; postclose only | Entry recheck, scale-in feedback/calibration, threshold apply preflight | Pressure-consuming candidate rows with unusable provenance are excluded before EV/apply. |

### Contamination Paths Closed In Code

| Path | Risk | Current handling |
| --- | --- | --- |
| Source-less `dir` / `side` treated as true aggressor | False buy/sell pressure and false scale-in support/block | Infer as `declared_tick_side_untrusted`, pressure neutral. |
| Weighted auxiliary score used as a pressure fallback | Empirical auxiliary weights could become false taker-side pressure | Use only explicit signed 0B `15` primary provenance or trusted orderbook touch. Keep `aggressor_aux_pressure_usable=false`. |
| `price_change_heuristic` with later best bid/ask attached | Heuristic could be promoted to orderbook-touch | Infer as `UNKNOWN` with `quote_with_untrusted_aggressor_source`. |
| Heuristic-only pressure interpreted as bearish | False negative entry/scale-in/exit evidence | `buy_pressure_10t=50.0`, `net_aggressive_delta_10t=0`, `tick_aggressor_pressure_usable=false`. |
| Microstructure reaction computed with no trusted pressure rows | Favorable/risk reaction from untrusted sides | `microstructure_reaction_context_status=source_quality_partial`, neutral scores. |
| Postclose candidate row has pressure value but unusable provenance | EV/apply candidate based on contaminated input | `observation_source_quality_audit` emits `tick_aggressor_pressure_usable_contract` and excludes the row. |

### Runtime Gate Consumer Contract

| Runtime gate | Consumed fields | Required source-quality/provenance | Allowed use | Forbidden use |
| --- | --- | --- | --- | --- |
| first-touch AVG_DOWN decision | `current_ai_score`, prior peak, repeated blockers, VPW, `buy_pressure_10t`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, spread/liquidity | AI support requires `holding_score_runtime_context.usable_for_scale_in_support=true`. Micro support requires `reversal_feature_source_quality=usable`, trusted tick pressure, and micro VWAP availability/fresh minute window. | Hold one share vs AVG_DOWN only when recovery support is confirmed and hard guards pass. Runtime prior may add support/risk logging, but support prior alone cannot replace missing AI/micro provenance. | Do not use raw AI score, stale/insufficient holding score, heuristic-only pressure, unavailable micro VWAP, or support prior alone to submit AVG_DOWN. |
| late-loss AVG_DOWN retry | `current_ai_score`, peak/giveback/loss depth, hold time, `curr_vs_micro_vwap_bp`, `score_gate_converted_to_prior`, `score_prior_band`, `ai_score_prior_weight` | AI provenance requires `holding_score_runtime_context.usable_for_scale_in_support=true`; the numeric score is a prior weight only. If micro VWAP is present, `reversal_feature_source_quality` must be usable; the late-loss retry may bypass an adverse fresh micro VWAP threshold, but not stale or missing micro provenance. | Retry only after loss-path criteria and usable AI provenance pass; low/high score changes support weight but cannot decide by itself. | Do not use a numeric AI score with missing `holding_score_*` provenance, and do not use stale/missing micro VWAP provenance to open retry support. |
| loss fallback AI context | `current_ai_score`, `score_gate_converted_to_prior`, `score_prior_band`, `ai_score_prior_weight` | AI context requires `holding_score_runtime_context.usable_for_scale_in_support=true`; the numeric score is prior metadata only. | May be used only as scale-in/loss fallback support metadata when provenance and probe/fallback reason are usable. | Missing, stale, fallback, disabled, timeout, or lock-contention score is neutral display only. AI score alone must not open loss fallback. |
| soft-stop micro grace modifier | `current_ai_score`, absorption/reaction features, `buy_pressure_10t`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, `soft_stop_final_action`, `soft_stop_extension_source`, `score_gate_converted_to_prior`, `score_prior_band`, `ai_score_prior_weight` | AI grace provenance may improve prior confidence when `holding_score_runtime_context.usable_for_soft_grace=true`; unusable AI score is neutral unless quote/source quality is a hard gap. Micro support requires fresh feature context and trusted pressure. Dynamic grace and expert absorption are scorer/modifier inputs only; `soft_stop_micro_grace` remains the single real deferral authority. | May defer soft-stop for one bounded confirmation window only when active stop-relative band and fresh micro/absorption support pass; AI prior support may strengthen but not create the decision alone. | Do not defer soft stop from AI score alone, heuristic pressure, stale quote, hard source-quality gap, standalone dynamic-grace authority, or expert-defense-only extension. |
| holding-flow never-green / OFI debounce | `holding_flow` action/state, OFI state, `curr_vs_micro_vwap_bp`, minute-candle freshness | Never-green defer clamp and OFI debounce may compare micro VWAP only when `micro_context_usable=true`, `micro_vwap_available=true`, and `minute_candle_window_fresh=true`. | May resume an exit after repeated never-green defer deterioration, or debounce an AI EXIT only when OFI is stable bullish and micro provenance is usable. | Do not use a stale or provenance-less micro VWAP value as negative-exit evidence or as an exit-defer extension reason. |
| entry AI remote guard / early-accel recheck / numeric consistency recheck | AI action/score/reason, `score_gate_converted_to_prior`, `score_prior_band`, `ai_score_prior_weight`, `ai_lock_wait_ms`, `ai_retry_attempted`, `ai_retry_result`, `buy_pressure_10t`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, minute-candle freshness | Pressure support requires trusted aggressor provenance. Micro VWAP support/risk and AI reason contradiction checks require `micro_vwap_available=true`, `minute_candle_window_fresh=true`, and usable `minute_candle_context_quality`. Score min/max env keys are prior calibration inputs only. AI lock contention must attempt a bounded wait before producing a fail-closed `lock_contention` result. | May downgrade suspicious remote BUY or request bounded recheck only when current feature provenance is usable; score changes prior weight but not standalone eligibility. Lock contention after retry is a source-quality/runtime availability result, not a neutral score judgment. | Do not treat missing/stale micro VWAP as bearish risk, support, or reason-contradiction evidence. Do not send recheck context without source-quality fields. AI score alone must not create, block, or force BUY/WAIT/DROP. Do not use retry-exhausted lock contention as a valid score-50 model evaluation. |
| score65_74 recovery probe | `buy_pressure`, `tick_accel`, `micro_vwap_bp`, AI score/action, `score_gate_converted_to_prior`, `score_prior_band`, threshold family fields | Runtime and postclose audit require trusted pressure fields and minute-candle provenance fields. `micro_vwap_bp` is an alias of the same micro VWAP concept and must not bypass `micro_vwap_available`/`minute_candle_window_fresh`/`minute_candle_context_quality`. Score band is a prior label, not an unlock authority by itself. | Bounded entry unlock observation only after hard safety, pressure, tick, and fresh micro context pass; score band may adjust priority/labels. | Do not create postclose EV/apply candidate rows from probe events with missing pressure or minute-candle provenance. Do not use score band alone as real-entry authority. |
| PYRAMID | `current_ai_score`, `score_gate_converted_to_prior`, `score_prior_band`, profit/peak, `buy_pressure_10t`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, large sell print | AI provenance may add prior support when `_ai_score_available_for_scale_in=true`; numeric score is not a required check. Pressure support and large-sell clear require trusted aggressor pressure. Tick/micro support requires non-stale reversal feature context. | Pyramiding only when composite support score and hard safety gates pass. Runtime prior may add support/risk logging; hard safety is not relaxed. | Do not use `buy_pressure_10t` when `tick_aggressor_pressure_usable=false`; do not use stale micro VWAP or stale holding score for support. Do not block or open PYRAMID from AI score alone. |
| REVERSAL_ADD / AVG_DOWN probe | `current_ai_score`, `score_gate_converted_to_prior`, AI history, `buy_pressure_10t`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, large sell print | `reversal_feature_source_quality` must be `usable`; AI recovery/provenance must be explicit when the path depends on AI history. Numeric min score is a prior calibration input only. | May support AVG_DOWN only after PnL/hold/recovery and supply checks pass. | Do not treat pressure/micro metrics with missing provenance as valid supply confirmation. Do not use AI score alone to create or block AVG_DOWN. |
| negative exit / trailing AI branch | `current_ai_score` | `holding_score_runtime_context.usable_for_negative_exit=true`; this is fresh-only. | Fresh usable low score may support momentum-decay/never-green exit; fresh usable high score may enable strong trailing branch. | Partial/stale/insufficient/fallback score cannot create AI-driven negative exit or strong trailing branch. |

### Runtime Producer To Consumer Trace

| Producer | Intermediate artifact/log field | Runtime consumers | Postclose consumers | Contract |
| --- | --- | --- | --- | --- |
| `scalping_feature_packet` | `buy_pressure_10t`, `net_aggressive_delta_10t`, `tick_aggressor_pressure_usable`, `tick_aggressor_trusted_count`, `tick_acceleration_ratio`, `curr_vs_micro_vwap_bp`, `micro_vwap_available`, `minute_candle_window_fresh` | first-touch AVG_DOWN, PYRAMID, REVERSAL_ADD, recovery probe, soft-stop grace, AI entry/holding payloads | `pipeline_events`, `observation_source_quality_audit`, entry/scale-in feedback and calibration | Directional pressure support requires trusted pressure rows; micro VWAP support requires available/fresh minute context. |
| `holding_score_v2` runtime state | `holding_score_source`, `holding_score_data_quality`, `holding_score_effective_usable`, `holding_score_last_effective_at`, `holding_score_effective` | scale-in support, soft grace, negative exit, strong trailing, state history | post-sell feedback, holding/exit backtests, source-quality audit | Role gate determines use: fresh for all soft roles, partial only for support/grace with microstructure confirmation, stale/insufficient as neutral display only. |
| runtime prior feedback reports | `runtime_prior_context.signal/status/sample_count/reason` | first-touch AVG_DOWN and PYRAMID soft context | calibration/backtest reports | Prior is advisory support/risk only. It must not mutate thresholds intraday or override hard safety/source-quality blockers. |

### Runtime Contamination Paths Closed In Code

| Path | Risk | Current handling |
| --- | --- | --- |
| Caller treats missing `holding_score_*` contract as usable legacy AI score | Unproven score can open AVG_DOWN, soft-stop grace, or loss fallback | Runtime gates now trust `_holding_score_runtime_context()` directly; missing provenance becomes `insufficient` and `ai_score_unusable`. |
| Runtime prior support opens first-touch AVG_DOWN without fresh AI/micro recovery support | Feedback report can replace current evidence | Support prior remains logged as support but no longer allows AVG_DOWN by itself. |
| AI compact payload drops pressure/micro availability fields | AI may overinterpret neutral `buy_pressure_10t=50` or `curr_vs_micro_vwap_bp=0` | Entry v2, compact JSON, and legacy text payloads carry pressure usability, trusted/heuristic counts, micro VWAP availability, and minute freshness. |
| Entry AI recheck or numeric consistency logic counts `curr_vs_micro_vwap_bp` without minute-candle provenance | Missing chart context becomes false support/risk or triggers a misleading AI correction loop | Entry remote guard, numeric consistency checker, and early-accel strong-bundle recheck count micro VWAP only when `micro_vwap_available=true` and `minute_candle_window_fresh=true`; recheck logs and prompt context carry the same provenance fields. |
| Holding cache counts `price_change_heuristic` BUY as real buy volume | Cache signature can preserve false BUY pressure | Heuristic BUY/SELL is excluded from holding cache buy/sell volume. |

### Immediate Code Defects Fixed

- `microstructure_reaction_context` now trusts only explicit source allowlist for
  pressure math and returns neutral source-quality partial context when pressure
  provenance is unusable.
- `scalping_feature_packet` carries cached orderbook-touch counts, micro VWAP
  availability flags, and reaction-context pressure provenance into audit fields.
- Scale-in feature refresh payloads preserve `micro_vwap_available` and
  `minute_candle_window_fresh` so refreshed micro VWAP values do not lose
  provenance before PYRAMID/AVG_DOWN/REVERSAL_ADD consumption.
- When existing scale-in reversal features are stale because of
  `quote_stale` or `quote_age_gt_max`, refresh forces a bounded
  `ka10004_rest_orderbook` quote refresh before rebuilding features; failed
  quote refresh keeps the old feature context blocked instead of reusing a
  superficially usable WS snapshot.
- `observation_source_quality_audit` now hard-excludes any stage that requires
  tick pressure provenance and emits a pressure value while provenance is
  unusable or missing.
- `threshold_cycle_preopen_apply` re-checks source-date source-quality preflight
  before consuming direct AI/scale-in calibration reports, so a stale or blocked
  postclose source cannot become a next-PREOPEN env override.
- First-touch AVG_DOWN and PYRAMID runtime prior loaders now require the source
  feedback report `source_quality.status=pass`; otherwise they return neutral
  `source_quality_blocked` prior context with `sample_count=0`.

### Kiwoom Confirmation Result

| Item | Confirmation result | Current safe policy |
| --- | --- | --- |
| 0B aggressor-side field priority | FID15 signed trade volume provides explicit signed taker-side evidence when it starts with `+` or `-`; trade price `10` vs best ask/bid `27`/`28` remains the practical quote-touch fallback and validation path. | Use `15` as primary `kiwoom_0b_signed_trade_volume` when signed. Preserve `10`/`27`/`28` comparison in `aggressor_touch_*`; when `15` is missing or neutral, use orderbook-touch inference only with quote freshness/sync checks. |
| `rank_chg_sign` official codes | Provided docs still do not specify the field. Observed/expected values are `+`, `-`, empty, and candidate `N`; `+/-` should match signed `rank_chg`, while empty has repeatedly matched `rank_chg=0` during operating samples. | Preserve raw sign plus derived source-quality diagnostics only; scoring uses signed numeric `rank_chg`, and raw sign still has no entry/priority/live authority. |
| `bid_req_base_tm` exchange/server timing semantics | Practical examples show `HHmmss` such as `162000`, despite some documentation ambiguity. Exchange-time basis is plausible but not explicitly guaranteed. Precision is seconds, not milliseconds. | Treat as quote reference-time provenance and optional lag diagnostic only. Runtime freshness still requires REST receive timestamp/age; do not use `bid_req_base_tm` alone for millisecond freshness or submit authority. |

## ka10004

- `sel_fpr_bid` is `best_ask`.
- `buy_fpr_bid` is `best_bid`.
- `marketable_buy_touch_price` and `executable_buy_price` mean immediate buy
  touch price and therefore use `best_ask`.
- `marketable_sell_touch_price` and `executable_sell_price` use `best_bid`.
- `passive_buy_price` uses `best_bid`; scale-in passive order price selection
  should prefer this field.
- `passive_sell_price` uses `best_ask`.
- `bid_req_base_tm` is quote reference-time provenance. Practical samples use
  `HHmmss` such as `162000`, while some docs may describe a date-like format;
  prefer observed response format but keep parser defensive.
- `bid_req_base_tm` may be compared to KST receive time as a seconds-level
  diagnostic, but it is not millisecond freshness authority. Freshness must use
  REST receive timestamp or explicitly measured refresh age. Runtime snapshots carry
  `bid_req_base_tm_authority=raw_not_freshness_input`,
  `source_time_basis=response_received_epoch_ms`,
  `rest_freshness_basis=response_received_epoch_ms`, and
  `rest_age_source=response_received_epoch_ms` to make this contract explicit.
- For `source=ka10004_rest_orderbook`, a generic `age_ms=0` value is not enough
  freshness evidence unless it is derived from `rest_received_ts_ms`,
  `rest_received_ts`, or the runtime-specific
  `pre_submit_rest_orderbook_refresh_age_ms`. If the receive timestamp is
  missing, runtime must treat the REST orderbook as time-unknown/stale and keep
  `bid_req_base_tm` only as raw provenance.
- Scanner/pre-AI/submit market-data freshness envelope may use `ka10004` to
  repair stale or missing WS quote/depth input and to classify WS/REST conflict.
  This is freshness/provenance only; it must not relax threshold, provider,
  broker, order cap, stale quote, account/order/quantity/cooldown, or submit
  safety guards.
- REST and WebSocket market suffixes are aligned: explicit `000000_NX` and
  `000000_AL` request codes must be preserved when the caller supplies them.
  DB-derived NXT detection may choose `_AL`, but it must not strip an explicit
  `_NX` route request.

## Realtime Freshness And Snapshot Backfill

- Kiwoom realtime payloads are treated as event-driven market-data updates, not
  a quote freshness heartbeat. A connection keepalive, PING, or successful REG
  state is not quote freshness evidence.
- The current contract has no documented first-event warm-up SLA, millisecond
  server send timestamp, or global sequence number. Runtime freshness therefore
  uses client receive timestamps such as `last_ws_update_ts`,
  `last_realtime_type_ts`, `rest_received_ts_ms`, and measured refresh age.
- Public docs and board examples do not provide one stable numeric concurrent
  subscription limit. Some examples mention different approximate limits, so
  this codebase must not encode a fixed official session limit from those
  examples. Until Kiwoom confirms otherwise, count each REG item as quota usage;
  KRX/NXT alternate-route items such as `_NX` or `_AL` are treated as separate
  items even when they point to the same symbol.
- WebSocket REG item strings are route-specific. Empty suffix, `_NX`, and
  `_AL` are separate subscription items and must be explicitly registered when
  needed. Runtime freshness snapshots expose `registered_market_suffixes`,
  `registered_market_routes`, `registered_route_counts`,
  `registered_item_quota_units`, and `multi_route_registered` so route coverage
  and duplicate quota use can be reviewed without changing trading authority.
- `refresh=1` is treated as append/keep-existing behavior, not full
  replacement. Route transitions such as NXT premarket to KRX regular session
  should REMOVE the old route item and then REG the target route. Reusing
  `refresh=1` alone can leave duplicate or silent subscriptions and is not
  accepted as a reliable recovery path.
- Server-side behavior for idle or low-liquidity no-event subscriptions is not
  specified with an official timeout or cancel-notice payload. Client logic must
  therefore track per-symbol last receive time and treat prolonged no-tick
  periods as a source-quality recovery condition, not as proof that the stream is
  healthy.
- There is no documented official reREG cooldown. Recovery should use bounded
  retry and backoff, with request counting to avoid throttle errors such as
  `105110`. The backoff policy is an operational guard, not a freshness SLA.
- Runtime implementation owns an empirical freshness controller inside
  `KiwoomWSManager`: it exposes per-symbol client receive-age snapshots,
  treats no-tick/stale symbols as source-quality recovery candidates, and can
  send a bounded server `REMOVE` before `REG` for persistent repair paths. This
  recovery path is limited to websocket source freshness; it does not create BUY
  or scale-in authority and cannot bypass stale quote, broker, account, order,
  quantity, cooldown, provider, cap, bot-state, hard/protect, or emergency
  guards.
- 0B/0D websocket rows are the primary quote/tick source. Periodic or bounded
  `ka10003`/`ka10004` snapshots may backfill stale or missing realtime context,
  but the backfill remains source-quality recovery unless it carries a measured
  receive timestamp and passes the same quote, orderbook, and pressure
  provenance gates.
- KRX/NXT operating-window differences, subscription item limits, server-side
  idle behavior, and low-liquidity no-event periods are operational freshness
  risks. Persistent stale rows should be reported as `source_quality_gate`
  diagnostics and must not relax broker submit, stale quote, order price,
  quantity, provider, cap, or bot-state guards.

### 2026-08-10 Micro-Reversion Continuous 0D Depth Capture Gate

- Official upstream revision: `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`,
  retrieved `2026-08-10T16:24:11+09:00`.
- Inspected authority paths:
  `kiwoom_docs/실시간시세.md`, `kiwoom/_data/kiwoom_api_spec.json`,
  `kiwoom/specs.py`, `kiwoom/realtime/{packets,events,decoders,schemas,stream}.py`,
  `kiwoom/core`, and
  `examples/국내주식/실시간시세/subscribe_domestic_stock_order_book_depth_async.py`.
  The example is sample evidence only. The Postman collection excludes
  WebSocket requests and therefore is not 0D authority.
- The existing KORStockScan REG/REMOVE packets already include `0D` for every
  registered item alongside `0B`. This implementation does not add a market
  data type, symbol, route, REG, REMOVE, reconnect, or resubscribe path. It only
  attaches an independently flagged observation consumer to the already
  received 0D callback.
- Official 0D time is FID `21`; ask prices/quantities are `41-50`/`61-70`, bid
  prices/quantities are `51-60`/`71-80`, and combined totals are `121`/`125`.
  KRX totals are `6064`/`6065` and NXT totals are `6086`/`6087`. The compact
  micro-reversion row retains the best five levels plus these totals; this is an
  explicit storage projection, not a claim that the official feed has only five
  levels.
- Item suffix remains authoritative for the subscription route: plain item is
  KRX, `_NX` is NXT, and `_AL` remains the integrated SOR cohort. `_AL` must not
  be guessed as the underlying execution venue even when KRX/NXT component
  totals are present.
- 0D has an independent bounded intake queue, sequence, worker, writer, and
  `market_depth_stream.jsonl` partition. 0B canonical rows keep depth null.
  Offline research may join only the latest past 0D row with the same
  symbol/venue/session and an explicit freshness limit. Future, cross-route,
  missing-value-imputed, or touch-as-fill joins are forbidden.
- Capture is default OFF behind
  `SCALP_MICRO_REVERSION_DEPTH_CAPTURE_ENABLED`. Enabling it changes no trading,
  detector, P2 selection, threshold, provider, quantity, cap, broker, or bot
  authority. Queue/writer/drop/storage degradation is canary fail-closed.

## ka10080 and ka10081

- `ka10080` is implemented through `/api/dostk/chart` with `api-id=ka10080`.
  The official request payload is `stk_cd`, `tic_scope=1`, and
  `upd_stkpc_tp=1`. The existing runtime helper also sends same-day `base_dt`
  as a locally observed extension; consumers must not assume that extension is
  portable or use it as historical-range authority.
- Continuation is controlled by response `cont-yn` and `next-key`.
- Client code must sort final merged rows oldest to latest:
  - `ka10080`: by `cntr_tm`.
  - `ka10081`: by `dt`.
- `ka10080.cntr_tm` and `ka10081.dt` are chart bar timestamps, not current quote
  freshness authority. Runtime quote freshness must still come from websocket or
  REST receive timestamps.
- `ka10080` must not be used as a sub-second 0B/0D stale-recovery substitute.
  Short-window 5s/10s pressure, tick acceleration, quote freshness, and signed
  tape decisions remain websocket-first; bounded `ka10004`/`ka10084` snapshots
  may be used only under their separate REST provenance contracts.
- `ka10080` minute candles carry additive `source_timestamp` and
  `source_time_basis=ka10080_cntr_tm_bar_timestamp`. Feature packet consumers may
  use micro VWAP/MA5 only when the latest minute bar is fresh relative to the
  evaluation reference time; missing or stale candle time must set
  `minute_candle_window_fresh=false` and keep micro VWAP/MA5 unavailable for
  support/block decisions.
- Runtime and postclose consumers must not treat `curr_vs_micro_vwap_bp` alone
  as valid micro VWAP evidence. Scale-in, holding, recovery probe, AI
  source-quality gates, and entry backtest/calibration support paths require
  `micro_vwap_available=true` and `minute_candle_window_fresh=true`; otherwise
  the row is `micro_vwap_unavailable` or `micro_vwap_provenance_missing` for
  support/apply-candidate decisions.
- Existing return shapes are preserved:
  - `get_minute_candles_ka10080` returns candle rows.
  - `get_minute_candles_ka10080_with_meta` returns `(candles, meta)`.
  - `get_daily_ohlcv_ka10081_df` returns a DataFrame with
    `df.attrs["kiwoom_source_meta"]`.

### 2026-08-11 Pure-market reversal backfill gate

- Rechecked at `2026-08-11T10:10:15+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/차트.md`, `kiwoom/_data/kiwoom_api_spec.json`,
  `kiwoom/specs.py`, `kiwoom/core/client.py`, and
  `postman/kiwoom-openapi.postman_collection.json` for `ka10080` path, headers,
  request/response fields, continuation, and venue suffix handling.
- `pure_market_kiwoom_backfill` therefore sends only the three documented
  request fields and uses `005930` for KRX and `005930_NX` for NXT. It follows
  `cont-yn`/`next-key`, keeps `cntr_tm` as the source bar timestamp, and rejects
  malformed OHLCV or out-of-session rows without filling gaps. Expected
  out-of-session exclusions and malformed source rows are counted separately;
  only the latter degrades source quality. Continuation must reach a date older
  than the requested start date before the start boundary is complete; merely
  seeing one row on the start date is not sufficient.
- The producer may read only an already-valid shared cached token. Any missing
  token, HTTP/API error including authentication rejection, or malformed
  continuation fails closed without token issuance, refresh, invalidation, or
  replacement. It has no account, order, quantity, runtime, provider, or bot
  authority.
- The same read-only producer uses official `ka20005` at
  `POST /api/dostk/chart` for KOSPI minute context with `inds_cd=001` and
  `tic_scope=1`, parses `inds_min_pole_qry`, and follows the same
  `cont-yn`/`next-key` continuation contract. Index prices are preserved in
  their raw x100 representation; only dimensionless returns are compared with
  Samsung returns. Context joins require the exact `cntr_tm` timestamp, and a
  missing timestamp is kept missing rather than substituted with a neighboring
  index bar.

### 2026-08-11 Lower-price expanding-window research gate

- Rechecked at `2026-08-11T21:27:49+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/차트.md`, `kiwoom/_data/kiwoom_api_spec.json`,
  `kiwoom/specs.py`, `kiwoom/core`,
  `postman/kiwoom-openapi.postman_collection.json`, and
  `examples/국내주식/차트/get_domestic_stock_minute_chart.py` for `ka10080`
  path, `api-id`, headers, request/response fields, continuation, and `_AL`
  integrated-SOR symbol handling. Examples remain samples, not order authority.
- The lower-price candidate producer keeps the existing documented request
  shape: `POST /api/dostk/chart`, `api-id=ka10080`, `stk_cd={symbol}_AL`,
  `tic_scope=1`, and `upd_stkpc_tp=1`, with `cont-yn`/`next-key` continuation.
  This change only makes the locally expected trading-date count explicit and
  expanding from clean baseline `2026-06-05`; it does not add a Kiwoom request
  field or reinterpret `cntr_tm`.
- Every expected clean-baseline trading date must be present for every research
  symbol. Missing or malformed dates fail source quality closed. The latest 16
  dates remain untouched holdout, and older clean-baseline dates expand only the
  calibration side. This source-only lane has no token mutation, account,
  order, runtime, provider, bot, cap, or broker-guard authority.

### 2026-08-12 Widget auxiliary-flow freshness gate

- Rechecked at `2026-08-12T15:12:22+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/차트.md` for `ka10064` and `ka20005`,
  `kiwoom_docs/시세.md`, `kiwoom/_data/kiwoom_api_spec.json`,
  `kiwoom/specs.py`, `kiwoom/core`, and Postman. Official `ka10064` provides
  each estimate's `tm` but does not guarantee a refresh interval. Official
  `ka20005` identifies `001` as KOSPI composite and `101` as KOSDAQ composite.
- Widget collectors therefore preserve `ka10064.tm` as the foreign-estimate
  source time and never replace it with REST receipt time. More than five and
  at most sixty minutes is labeled `DELAYED_ESTIMATE`; older, conflicting, or
  missing values remain stale/unavailable. A fresh `ka90008` program component
  may produce `OBSERVED_PARTIAL`, but the delayed foreign estimate cannot grant
  positive promotion or be presented as real-time flow.
- Doosan, Hanwha Ocean, Mirae Asset Securities, Samsung Heavy Industries, Jeju
  Semiconductor, and SK Eternix keep quote/BBO/minute-bar hard source quality
  separate from this auxiliary component quality. The four prospective symbol
  collectors store peer, market-index, foreign estimate, program, and USD/KRW
  provenance as observation-only data without account, order, quantity, token
  issue/refresh, provider, bot, threshold, or broker-guard authority.

### 2026-08-12 Widget research-watch collector gate

- Rechecked at `2026-08-12T21:52:00+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/종목정보.md` for `ka10001`,
  `kiwoom_docs/시세.md` for `ka10004`, `kiwoom_docs/차트.md` for `ka10080`,
  `kiwoom/specs.py`, `kiwoom/core`, and
  `postman/kiwoom-openapi.postman_collection.json`. The collector uses only
  KRX six-digit `stk_cd`, `tic_scope=1`, and `upd_stkpc_tp=1` with the existing
  read-only client and response parsers.
- The user-directed research-watch collector records current price, REST BBO
  receipt provenance, and completed KRX one-minute OHLCV once per symbol minute.
  It uses only the shared cached token and never issues or refreshes a token.
  It has no account, order, advisory, entry/exit event, quantity, policy apply,
  provider, bot, cap, broker-guard, or hard-safety authority.

### 2026-08-24 Holding-route recovery revalidation

- Rechecked at `2026-08-24T17:06:38+09:00` from upstream commit
  `69642586f7d84ba9fd8a6faf1f1537c7fda6568b`.
- Inspected `kiwoom_docs/실시간시세.md`, `kiwoom/realtime/packets.py`,
  `kiwoom/specs.py`, and the local WebSocket REG/market-route parser. The
  official item contract remains plain six-digit code for KRX, `_NX` for the
  NXT-only route, and `_AL` for the integrated SOR route; REG uses
  `refresh=1` and each data item's `type` list.
- Holding freshness repair now follows the executable sell-session owner.
  KRX regular-session recovery retains the plain/SOR registration, while a
  confirmed NXT-enabled holding in the NXT execution session requests the
  exact `_NX` item required by the fresh executable-bid consumer. `_AL` is not
  accepted as proof of an NXT-only quote. A KRX-only holding outside the KRX
  regular session, or unconfirmed NXT eligibility, records a suppressed repair
  state instead of repeatedly issuing an unusable registration. Both successful
  registration and suppressed route decisions use the bounded repair cooldown,
  so the holding loop does not repeatedly query route metadata or emit the same
  recovery decision on every tick.
- The change is source recovery and provenance only. It grants no sell, entry,
  scale-in, quantity, provider, threshold, cap, broker-guard, or hard-safety
  authority.

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
- 2026-07-06 operating-window samples covered NXT operating/KRX pre-regular
  session (`400` rows) plus KRX regular session (`200` rows). Combined
  distribution was `+=135`, `-=151`, `N=0`, `empty=314`; `+/-` direction
  mismatches were `0`, and empty/nonzero-rank mismatches were `0`. This supports
  source-quality diagnostics only: `empty` is treated as operating neutral when
  `RankChange==0`, while `N` remains a closed-market candidate value until
  postclose repetition confirms it.

### Signed Field Contract

| Source field | Parser/normalizer contract | Intermediate field | Runtime consumers | Postclose consumers | Contract |
| --- | --- | --- | --- | --- | --- |
| `flu_rt` | Signed percent parser. Preserve `+/-`. | `FluRate`, `DayFluRate`, `flu_rate`, `change_pct` | Scanner filters, panic breadth context, daily limit-up context, AI/source payload features | Source-quality audit, entry/backtest diagnostics | Must not be parsed through unsigned price/quantity helpers. Negative values are bearish/decline context only when the producer contract is known. |
| `sdnin_rt` | Signed percent parser. Preserve `+/-`. | `BidSurgeRate`, `SpikeRate` | Scanner source score and candidate provenance | Scanner/source-quality diagnostics | Direction comes from the signed value plus source family; do not take absolute value for score support. |
| `open_pric_pre` / `open_pric_pre_flu_rt` | Signed percent parser. Preserve raw rate separately from recomputed open-relative rate. | `OpenPreRateRaw`, `OpenFluRateRaw`, `ViOpenFluRate` | Scanner source metric selection | Scanner/backtest diagnostics | This is a rate, not a price difference. Legacy `OpenDiff` is compatibility only. |
| `pred_pre_sig` | Raw code plus normalized direction: `positive`, `neutral`, `negative`, or `unknown`. | `PreSig`, `PreSigDirection` | Positive-only source filters and provenance | Source-quality diagnostics | Direction is a state code, not a numeric sign. Unknown code must not be promoted silently. |
| `rank_chg` | Signed numeric rank delta parser. Preserve negative values. | `RankChange`, `rank_chg`, `rank_change_score_input` | Rising-start score may use only `max(0, RankChange)`. | Scanner event and source-quality diagnostics | Negative rank delta must not reward a rising-start candidate. |
| `rank_chg_sign` | Raw string plus derived diagnostics only. | `RankChangeSign`, `rank_sign`, `rank_change_sign_authority=raw_unverified_not_decision_input`, `RankChangeSignState`, `RankChangeSignConsistency` | Display/provenance/source-quality only. | Empirical validation and source-quality audit only. | No scoring, entry, priority, or live authority until official code semantics are confirmed. `RankChangeSignConsistency=mismatch/unknown` is a source-quality finding, not a trading signal. |

### Signed Field Producer To Consumer Trace

| Producer | Intermediate artifact/log field | Runtime consumers | Postclose consumers | Contract |
| --- | --- | --- | --- | --- |
| `ka10027`, `ka10028`, `ka10021`, `ka10023`, `ka10054`, `ka00198` scanner helpers | Normalized scanner candidate fields such as `FluRate`, `OpenFluRate`, `BidSurgeRate`, `RankChange` | `scalping_scanner` candidate scoring/source guard and emitted runtime target payload | Scanner event source-quality, entry/missed opportunity reports | Signed rates and signed rank delta must be preserved before scoring; raw sign fields remain provenance. |
| `market_panic_breadth_collector` | `change_pct`, `change`, breadth summary rows | Panic/breadth report-only context | Panic lifecycle/source-only reports | Signed market/industry change rates may classify regime context but cannot mutate runtime thresholds or orders. |
| `scalping_scanner` event payload | `rank_change_sign_authority`, `rank_change_sign_state`, `rank_change_sign_consistency`, `rank_change_score_policy` | Runtime scanner source guard and candidate priority | `pipeline_events`, source-quality audit, LDM/scanner attribution | Score uses signed numeric rank delta only; raw sign authority and consistency diagnostics must travel with the row. |

### Signed Field Contamination Paths Closed In Code

| Path | Risk | Current handling |
| --- | --- | --- |
| Legacy `ka00198` hot-stock rates parsed with unsigned helper | Negative `base_comp_chgr` / `prev_base_chgr` becomes positive scanner evidence. | Legacy hot-stock parser uses the signed rate parser for those fields. |
| Negative `rank_chg` parsed as unsigned magnitude | Falling rank could increase rising-start score. | `rank_chg` / `RankChange` use signed parsing; score input is explicitly `max(0, RankChange)`. |
| `rank_chg_sign` treated as official direction code | Unconfirmed raw sign could drive priority or live authority. | Raw sign is logged with `raw_unverified_not_decision_input` authority and excluded from scoring. |
