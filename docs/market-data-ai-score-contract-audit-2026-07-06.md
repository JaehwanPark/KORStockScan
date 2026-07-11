# Market Data / AI Score Contract Audit - 2026-07-06

Purpose: close the end-to-end audit for Kiwoom market-data, AI score, and microstructure feature meaning from producer through runtime and postclose consumers. This is a source-quality and traceability artifact only. It does not change runtime thresholds, provider routes, bot state, broker guards, order guards, caps, or quantity guards.

Source of truth references:
- `docs/kiwoom-api-data-contract.md`
- `docs/report-based-automation-traceability.md`
- `data/source_quality/clean_baseline_policy.json`
- `data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-03.json`

## Decision

The audit is closed for the originally requested source-meaning surfaces. The remaining open items are not code defects that justify runtime changes. They are either official Kiwoom semantic confirmations or source-only calibration surfaces that must stay non-applying until a dedicated producer/env mapping exists.

No intraday threshold/env mutation, provider route change, bot restart, broker/order guard relaxation, cap change, or quantity guard change is authorized by this audit.

## Field Meaning Contract Table

| Scope | Source meaning | Parser/normalizer contract | Runtime consumption | Postclose consumption | Status |
| --- | --- | --- | --- | --- | --- |
| Kiwoom 0B trade/orderbook | Trade price `10`, best ask `27`, best bid `28`, trade time `20`, signed volume `15`, cumulative volume `13`, execution quantities `1030`/`1031`, buy ratio `1032`, momentary value `1313`, and strength `228` are available. | Use explicit signed `15` as primary taker-side source when present; preserve `10` vs `27`/`28` as `aggressor_touch_*` validation/fallback. Use `1030+1031` before `abs(15)` for volume/value fallback and preserve mismatch provenance. | Trusted aggressor may feed pressure through `kiwoom_0b_signed_trade_volume`, fresh inline quote, or short-TTL TOB cache with sync metadata. `1313` is primary tick value; calculated values carry source provenance. | Source-quality audit can use trusted count/source counts, trade-value source, split-vs-15 mismatch fields, and websocket cumulative `kiwoom_0b_*` parser counters; auxiliary score is diagnostics only. | Closed |
| `ka10003` trade history | Price/change fields do not prove buyer/seller aggressor. Raw `cntr_infr` may sometimes carry split/signed/quote-touch evidence. | Mark normalized ticks as `aggressor_source=price_change_heuristic`; never promote enriched heuristic ticks to orderbook touch after the fact. `ka10003_buy_dominance_observation` may use `1031/1030`, signed `15`/`cntr_trde_qty`, then original-row quote-touch as source-quality-only statistics, and flattens `source_counts`, `trade_value_source_counts`, `inside_spread_count`, and split-vs-15 counters for automatic postclose aggregation. | Price-change heuristic may be diagnostic only; pressure math must stay neutral. The observation must not fill trusted pressure fields or submit support. | Briefing/provenance/source-quality only; no EV/apply pressure support. | Closed |
| `ka10004` orderbook | `sel_fpr_bid` is best ask; `buy_fpr_bid` is best bid; observed `bid_req_base_tm` format is seconds-level `HHmmss`. | Expose `best_ask`, `best_bid`, marketable/passive aliases; REST freshness comes from receive timestamp/age, not `bid_req_base_tm` alone. | Passive scale-in price uses bid/passive fields; executable buy means best ask. | Quote consistency/source-quality can audit receive-age based freshness and optional seconds-level `bid_req_base_tm` lag. | Closed |
| REST/WS market suffix | REST and WebSocket both use explicit route suffixes such as `_NX` and `_AL`. | Preserve caller-supplied `000000_NX`/`000000_AL`; WS snapshot exposes route suffixes, route counts, quota units, and multi-route state. | Route suffixes may select the intended market-data subscription/request only. They do not relax stale quote, broker, order, threshold, provider, or cap guards. | Intraday freshness monitor aggregates route/quota state as source-quality diagnostics. | Closed |
| `ka10046` strength trend | REST `/api/dostk/mrkcond` aggregate strength trend rows are delayed/supporting context, not 0B replacement. | Mark rows as `ka10046_rest_strength_trend`, attach `rest_received_ts_ms`, `decision_authority=strength_trend_rest_fallback_source_only`, and keep `runtime_effect=false`. `acc_trde_prica` is turnover only, never current price. Preserve separate `v_pw_ws_value` and `v_pw_rest_value`. | WS 0B strength has priority; REST strength may fill `v_pw_source=ka10046_rest_fallback` only when WS strength is missing, with `v_pw_runtime_support_usable=false` so it cannot create positive timing score by itself. No standalone BUY, pressure, submit, or apply authority. | `microstructure_reaction_context` aggregates fallback rate, fallback quote freshness, receive timestamp gaps, runtime-effect violations, and 0B-vs-REST divergence as source-quality review only. | Closed |
| `ka10084` signed tape envelope | `rest_signed_trade_ticks`, `market_data_signed_tape_state`, `market_data_rest_signed_tape_pressure_usable`, and `latency_true_ofi_direct_canary_signed_tape_*` are bounded signed-tape provenance. | Preserve the REST signed rows and latency canary counters in pipeline events and submit compact streams. `market_data_rest_signed_tape_pressure_usable` must remain false. | Scanner budget reallocation and latency direct-canary negative veto/annotation only. No BUY support, pressure math, submit-time REST retry, threshold mutation, provider route change, or broker guard bypass. | `microstructure_reaction_context` automatically aggregates signed-tape state counts, REST signed tick source counts, pressure-usable true violations, latency signed-tape totals, sell-dominated counts, latest-side counts, and tape block reasons as source-quality review only. | Closed |
| `ka10080`/`ka10081` chart | `ka10080` uses `/api/dostk/chart`, `api-id=ka10080`, and `stk_min_pole_chart_qry`; candle timestamps are bar timestamps, not live quote freshness. Continuation is `cont-yn`/`next-key`. | Preserve explicit `_NX`/`_AL` request suffixes, fetch continuation, sort old-to-new, attach source metadata. | Micro VWAP/MA features require `micro_vwap_available=true` and `minute_candle_window_fresh=true`. Minute bars must not replace sub-second 0B/0D stale recovery or 5s/10s WS windows. | Backtests must not treat stale chart values as support/risk evidence. | Closed |
| Signed fields | Rate fields preserve sign; `pred_pre_sig` is a state code; `rank_chg_sign` docs are absent but observed/expected values are `+`, `-`, and empty. | Use signed parsers for `flu_rt`, `sdnin_rt`, `open_pric_pre`; signed rank delta for `rank_chg`; raw-only `rank_chg_sign`. | Signed rates/rank can be used only under known field contract; raw rank sign is display/provenance. | Empirical validation only for `rank_chg_sign`; no scoring authority. | Closed |

## Producer To Consumer Trace

| Producer | Intermediate artifact/log | Runtime consumers | Postclose consumers | Audit result |
| --- | --- | --- | --- | --- |
| `kiwoom_websocket` 0B path | `aggressor_source`, cache/sync fields, quote source fields, `aggressor_aux_*`, `tick_trade_value_source`, split-vs-15 mismatch fields | `scalping_feature_packet`, microstructure context, strength momentum | pipeline/source-quality artifacts | Closed: signed 0B `15` is primary when explicit; orderbook-touch is validation/fallback; weighted auxiliary score is diagnostics only. |
| `kiwoom_utils` / tick history helpers | `price_change_heuristic`, raw `ka10003_buy_dominance_observation`, flat `ka10003_buy_dominance_observation_*` source counters, signed scanner fields, source metadata, `ka10046_strength_*` REST provenance, `rest_signed_trade_ticks` | Tick acceleration diagnostics, scanner source features, REST strength fallback only when WS strength is absent, signed-tape negative provenance | briefing/source-quality/backtest diagnostics and `microstructure_reaction_context` aggregation | Closed: heuristic is excluded from pressure; ka10003 dominance is observation-only; signed fields preserve direction; ka10046 stays source-only fallback; ka10084 signed tape remains negative-veto/source-quality only. |
| `scalping_feature_packet` | `buy_pressure_10t`, `net_aggressive_delta_10t`, `tick_aggressor_pressure_usable`, trusted/heuristic counts, `micro_vwap_available`, `minute_candle_window_fresh` | entry, holding, AVG_DOWN, PYRAMID, REVERSAL_ADD, recovery probe | pipeline events, source-quality audit, feedback/calibration | Closed: pressure and micro VWAP require provenance. |
| `microstructure_reaction_context` | reaction status, trusted pressure rows, neutral partial context | entry/scale-in/holding quality snapshots | source-quality and diagnostics | Closed: untrusted or missing pressure is neutral/partial, not bearish. |
| `holding_score_v2` | role gate, data quality, raw/effective score/source, freshness | scale-in support, soft grace, negative exit, state history | post-sell feedback and holding/exit backtests | Closed: stale/fallback/insufficient score is display-only neutral. |
| `entry_ai_gate_backtest` | policy sweep, realized EV, counterfactual metrics, source-quality gate | none directly | `ai_score_optimization_backtest`, PREOPEN candidate loader | Closed: score-only stays diagnostic; guarded recheck only through known bounded family. |
| `ai_score_optimization_backtest` | integrated surface coverage and calibration candidates | none directly | `threshold_cycle_preopen_apply` candidates | Closed: entry/first-touch/PYRAMID candidate paths are bounded; entry-price, holding/flow, general AVG_DOWN/REVERSAL_ADD are source-only unless dedicated mapping exists. |
| `observation_source_quality_audit` | pressure/micro/source-quality row exclusion | none directly | EV/backtest/apply preflight | Closed: contaminated rows are excluded or block candidates before PREOPEN apply. |
| `threshold_cycle_preopen_apply` | candidate loader, source-quality preflight, guard status | next PREOPEN runtime env only | apply plan/runtime env artifacts | Closed: direct calibration reports are rechecked and source-quality-blocked candidates do not write env. |

## Contamination Paths

| Path | Risk | Current disposition |
| --- | --- | --- |
| Price-change heuristic treated as true aggressor | False buy/sell pressure | Closed in feature packet and microstructure contracts. |
| Weighted auxiliary score treated as pressure fallback | False taker-side pressure from empirical auxiliary fields | Closed: explicit signed 0B `15` uses its own primary source; weighted auxiliary score remains `aggressor_aux_*` with `aggressor_aux_pressure_usable=false`. |
| Calculated tick value without source provenance | 1313 absence could silently change strength momentum and value thresholds. | Closed: `1313` is primary; fallback is `calc_price_x_1030_1031_sum` then `calc_price_x_15_abs`, with source and split-vs-15 mismatch provenance. Runtime also accumulates `kiwoom_0b_1313_missing_rate_pct` and source-count summaries for postclose review. |
| Heuristic tick later enriched with quote and promoted to orderbook touch | False trusted aggressor | Closed: untrusted source remains untrusted. |
| No trusted tick pressure interpreted as bearish | False negative entry/scale-in/exit | Closed: neutral pressure and source-quality insufficient. |
| Stale or missing minute candle used as micro VWAP support/risk | False support/block/exit | Closed: consumers require availability and freshness flags. |
| Raw AI score 50 or stale score used as scale-in/exit authority | False support or false negative exit | Closed: role gate controls support/negative-exit/state-history use. |
| Runtime prior support overriding hard safety/source-quality | Unbounded auto-tuning | Closed: prior is advisory only. |
| Postclose report with source-quality gap creating PREOPEN env | Runtime apply from contaminated input | Closed: preflight and direct-loader source-quality blocking. |
| Entry-price, holding/flow, or general AVG_DOWN/REVERSAL_ADD source-only evidence becoming env through integrated AI report | Unmapped authority leak | Closed: source-only summaries carry `allowed_runtime_apply=false` and do not create `calibration_candidates`. |

## Immediate Code Fixes Completed

| Area | Fix summary | Evidence |
| --- | --- | --- |
| 0B/ka10003 aggressor | Trusted orderbook-touch only; weighted auxiliary score is diagnostics; price-change heuristic excluded from pressure; ka10003 raw dominance stays source-quality-only. | `test_kiwoom_websocket.py`, `test_kiwoom_tick_history.py`, `test_scalping_feature_packet.py` |
| ka10004 quote meaning/freshness | best ask/bid and executable/passive aliases separated; `bid_req_base_tm` not freshness authority. | `test_kiwoom_quote_consistency.py`, `test_quote_consistency.py`, `test_kiwoom_market_data_contract.py` |
| Chart and micro VWAP provenance | minute candle freshness and availability are carried into feature packet and consumers. | `test_scalping_feature_packet.py`, `test_sniper_scale_in.py`, `test_state_handler_fast_signatures.py` |
| Entry/holding/scale-in AI role gates | Entry and holding score consumers use role/data-quality gates instead of raw numeric score. | `test_ai_engine_cache.py`, `test_holding_exit_matrix_runtime.py`, `test_sniper_scale_in.py` |
| Feedback/calibration source-quality | Rising missed and pyramid calibration reports preserve source quality and PREOPEN blocking. | `test_rising_missed_intraday_feedback.py`, `test_scalping_pyramid_intraday_feedback.py`, `test_threshold_cycle_preopen_apply.py` |
| Integrated AI score backtest coverage | Entry price, holding/flow, and general AVG_DOWN/REVERSAL_ADD source-only evidence is inventoried without opening env authority. | `test_ai_score_optimization_backtest.py` |

## Kiwoom Confirmation Result

| Item | Confirmation result | Current safe policy |
| --- | --- | --- |
| Direct official aggressor-side field, if any | Provided 0B spec has no separate direct aggressor field. The practical method remains `10` vs `27`/`28`; `15` may be auxiliary but not proof. | Keep orderbook-touch inference and source-quality gates. |
| `rank_chg_sign` official codes | Provided docs still do not define the field. Observed/expected values are `+`, `-`, and empty, likely rank direction. | Raw provenance only; numeric signed `rank_chg` remains the scoring input. |
| `bid_req_base_tm` timing semantics | Practical examples show `HHmmss` seconds-level time. Exchange basis is plausible but not guaranteed; sub-second freshness is impossible from this field. | Use receive timestamp/age for runtime freshness; use `bid_req_base_tm` only as optional seconds-level diagnostic. |

## Verification Commands

Latest targeted validation run during this audit:

```bash
.venv/bin/python -m pytest src/tests/test_ai_score_optimization_backtest.py
.venv/bin/python -m pytest src/tests/test_threshold_cycle_preopen_apply.py -k "ai_score_optimization or source_quality"
.venv/bin/python -m py_compile src/engine/scalping/ai_score_optimization_backtest.py src/tests/test_ai_score_optimization_backtest.py
git diff --check
```

Observed result: all commands passed.

Historical targeted validations for the earlier slices are represented by the test files listed above and by the contracts in `docs/kiwoom-api-data-contract.md`. Re-run the broader suite before merge if unrelated dirty worktree changes are included in the commit.

## Final Scope Status

| Objective slice | Status | Notes |
| --- | --- | --- |
| 1st Kiwoom field meaning | Closed | Kiwoom answers are reflected; no direct aggressor field exists, `rank_chg_sign` stays raw, and `bid_req_base_tm` is seconds-level diagnostic only. |
| 2nd runtime feature and gate consumers | Closed | Provenance gates are enforced for pressure, micro VWAP, AI score, prior context. |
| 3rd postclose/backtest/apply consumers | Closed | Source-quality preflight and source-only coverage are wired; unmapped surfaces cannot auto-apply. |
| Runtime authority safety | Closed | No threshold/env mutation, provider change, bot restart, broker/order/quantity/cap relaxation. |
| Remaining work | Non-blocking | Optional: collect repeated `rank_chg_sign` samples before promoting any raw sign semantics. |
