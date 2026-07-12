# Kiwoom API Data Contract

Final audit summary: [`market-data-ai-score-contract-audit-2026-07-06.md`](./market-data-ai-score-contract-audit-2026-07-06.md).

This document fixes the market-data interpretation rules used by runtime and
reporting code. It is a data quality contract only. It must not change real
order authority, threshold/env values, provider routes, bot state, caps, or
quantity guards.

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

## ka10080 and ka10081

- `ka10080` is implemented through `/api/dostk/chart` with `api-id=ka10080`.
  The current minute-candle request payload is `stk_cd`, `tic_scope=1`,
  `upd_stkpc_tp=1`, and same-day `base_dt`.
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
