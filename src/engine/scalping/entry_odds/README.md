# Offline Entry Odds Observer V1

This package is an offline, counterfactual-only sidecar. It does not import a
broker, submit orders, mutate runtime state, change a provider route, or emit a
live `BUY` action. `WOULD_BET`, `WOULD_NO_BET`, and `ABSTAIN` exist only in the
`offline_entry_odds_observer` namespace.

## Inputs

The CLI joins four files by `decision_trace_id`:

1. Immutable `ai_decision_trace_v1` JSONL.
2. Mature `ai_decision_outcome_labels_v1` JSON.
3. Offline `entry_odds_raw_prediction_v1` JSONL.
4. Strictly earlier `entry_odds_calibration_row_v1` JSONL.

Raw predictions must contain:

- four probabilities that sum to 1: `TARGET_FIRST`, `ADVERSE_FIRST`,
  `NEITHER_POSITIVE`, and `NEITHER_NONPOSITIVE`;
- exact source payload SHA-256 and the full calibration signature;
- explicit outcome payoffs in basis points;
- counterfactual fill probability and `FULL/PARTIAL/NO_FILL/UNKNOWN` state;
- separate tax, buy/sell commission, entry/exit spread, buy/sell slippage, and
  impact costs;
- listing market, broker execution venue, tax class, and cost schedule window;
- a cost-exclusive uncertainty hurdle split into model, tail, and operational
  components.

The calibration signature includes provider, exact model, prompt SHA-256,
input schema, odds policy, outcome label/horizon/target/adverse contract, cost
model, broker execution venue, observed venue/session, risk regime, and
liquidity bucket. There is no fallback across different signatures.

## Run

First inventory an exact-payload batch without an API call:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_odds.producer \
  --target-date YYYY-MM-DD
```

After reviewing the manifest, explicitly enable the resumable offline call:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_odds.producer \
  --target-date YYYY-MM-DD \
  --execute-openai
```

The producer uses the mature outcome file only to select traces that can be
evaluated. Observed outcomes, the original action, the score, and later market
data are not included in the provider request. Existing output can be resumed
only when its model, prompt hash, policy version, and target date match.

Rebuild calibration history from complete strictly-prior producer batches:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_odds.history \
  --target-date YYYY-MM-DD
```

The history builder rejects missing/incomplete producer manifests and never
admits a target-date row into calibration.

Then build the target observer report:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_odds.observer \
  --target-date YYYY-MM-DD \
  --predictions PATH_TO_RAW_ODDS.jsonl \
  --calibration PATH_TO_PRIOR_CALIBRATION.jsonl
```

The default trace and outcome paths use the target date. All four inputs are
required and malformed rows fail the command instead of being silently
discarded.

The current producer cost schedule separates the observed quote spread and
the 2026 20bp taxable-equity assumption, but commission, extra slippage,
listing-market classification, and one-share impact are still assumptions.
Those rows remain useful for calibration observation, while
`cost_model_assumption_only` blocks `sim_candidate_ready` until a verified
execution-cost source replaces them.

When the immutable trace and mature outcome files exist but raw odds have not
yet been produced, an explicit bootstrap report can be written with
`--allow-missing-odds-inputs`. That report is always `hold_sample`, records the
missing inputs in its source-quality manifest, and cannot become a simulation
candidate. Missing trace or outcome files still fail closed.

## Outputs

The command atomically writes private-mode JSON and Markdown reports under
`data/report/entry_odds_observer/`. The JSON contains the row ledger,
temperature calibrators, Brier/log-loss/ECE diagnostics, explicit cost
attribution, predicted-vs-OOS EV buckets, negative-veto attribution, and
reusable `calibration_updates` for a later chronological run.

`sim_candidate_ready` remains simulation-candidate evidence only. It requires
the declared sample floors, at least two populated predicted-EV buckets with
monotonic observed EV, positive negative-veto incremental EV, and non-worsening
worst loss and additive drawdown. It never grants runtime authority.
