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

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.scalping.entry_odds.observer \
  --target-date YYYY-MM-DD \
  --predictions PATH_TO_RAW_ODDS.jsonl \
  --calibration PATH_TO_PRIOR_CALIBRATION.jsonl
```

The default trace and outcome paths use the target date. All four inputs are
required and malformed rows fail the command instead of being silently
discarded.

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
