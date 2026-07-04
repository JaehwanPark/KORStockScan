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
| Kiwoom 0B trade/orderbook | Trade price `10`, best ask `27`, best bid `28`, trade time `20`, signed volume `15`, cumulative volume `13`, execution quantities `1030`/`1031`, and strength `228` are available; no direct aggressor-side field is documented. | Infer taker-side pressure from `10` vs `27`/`28`; keep missing/inside-spread/stale/unsynced quote as `UNKNOWN`. Auxiliary weighted observations are stored only as `aggressor_aux_*` provenance with pressure unusable. | Trusted aggressor may feed pressure only with fresh inline quote or short-TTL TOB cache and sync metadata. | Source-quality audit can use trusted count/source counts; auxiliary score is diagnostics only. | Closed |
| `ka10003` trade history | Price/change fields do not prove buyer/seller aggressor. | Mark as `aggressor_source=price_change_heuristic`; never promote to orderbook touch after the fact. | Price-change heuristic may be diagnostic only; pressure math must stay neutral. | Briefing/provenance only; no EV/apply pressure support. | Closed |
| `ka10004` orderbook | `sel_fpr_bid` is best ask; `buy_fpr_bid` is best bid; observed `bid_req_base_tm` format is seconds-level `HHmmss`. | Expose `best_ask`, `best_bid`, marketable/passive aliases; REST freshness comes from receive timestamp/age, not `bid_req_base_tm` alone. | Passive scale-in price uses bid/passive fields; executable buy means best ask. | Quote consistency/source-quality can audit receive-age based freshness and optional seconds-level `bid_req_base_tm` lag. | Closed |
| `ka10080`/`ka10081` chart | Candle timestamps are bar timestamps, not live quote freshness. Continuation is `cont-yn`/`next-key`. | Fetch continuation, sort old-to-new, attach source metadata. | Micro VWAP/MA features require `micro_vwap_available=true` and `minute_candle_window_fresh=true`. | Backtests must not treat stale chart values as support/risk evidence. | Closed |
| Signed fields | Rate fields preserve sign; `pred_pre_sig` is a state code; `rank_chg_sign` docs are absent but observed/expected values are `+`, `-`, and empty. | Use signed parsers for `flu_rt`, `sdnin_rt`, `open_pric_pre`; signed rank delta for `rank_chg`; raw-only `rank_chg_sign`. | Signed rates/rank can be used only under known field contract; raw rank sign is display/provenance. | Empirical validation only for `rank_chg_sign`; no scoring authority. | Closed |

## Producer To Consumer Trace

| Producer | Intermediate artifact/log | Runtime consumers | Postclose consumers | Audit result |
| --- | --- | --- | --- | --- |
| `kiwoom_websocket` 0B path | `aggressor_source`, cache/sync fields, quote source fields, `aggressor_aux_*` | `scalping_feature_packet`, microstructure context | pipeline/source-quality artifacts | Closed: orderbook-touch is the only trusted inferred aggressor path; weighted auxiliary score is diagnostics only. |
| `kiwoom_utils` / tick history helpers | `price_change_heuristic`, signed scanner fields, source metadata | Tick acceleration diagnostics, scanner source features | briefing/source-quality/backtest diagnostics | Closed: heuristic is excluded from pressure and signed fields preserve direction. |
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
| Signed 0B volume `15` or weighted auxiliary score treated as pressure fallback | False taker-side pressure from empirical auxiliary fields | Closed: preserved as `aggressor_aux_*` with `aggressor_aux_pressure_usable=false`. |
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
| 0B/ka10003 aggressor | Trusted orderbook-touch only; weighted auxiliary score is diagnostics; price-change heuristic excluded from pressure. | `test_kiwoom_websocket.py`, `test_kiwoom_tick_history.py`, `test_scalping_feature_packet.py` |
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
