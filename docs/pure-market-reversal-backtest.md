# Pure-market reversal backtest

## Purpose

This backtest does not invert, replay, or grade historic widget signals. Its
purpose is to use only the market information that was causally available at
each completed one-minute bar to find:

1. a long entry as close as practicable to the end of a decline; and
2. an exit that preserves as much as practicable of the subsequent rebound;
3. while maximizing round-trip-cost-adjusted expected value, rather than merely
   maximizing signal count or avoiding every loss.

Historic `ENTRY_*`/`EXIT_*` states, AI output, widget policies and calibration,
orders, positions, and future bars are forbidden decision inputs. Future bars
are used only after simulation to label actual trough/rebound opportunities and
measure capture error.

## Formal evaluation contract

- Input: unique, valid, completed Samsung Electronics one-minute OHLCV with
  source timestamp, venue, and session.
- Cohorts: KRX and NXT are trained, selected, and reported separately.
- Source coverage: materially incomplete venue-days are excluded; missing bars,
  historical BBO, and signed tape are not imputed.
- Execution: a signal can fill only at the next bar open. Resting target and
  stop may fill inside later bars; if both touch in the same bar, the adverse
  stop is applied first. Timeout exits at the next bar open, and every open
  position is included through a session-close mark-to-market. A data gap can
  be exited only at the next observed bar open, never retroactively at the
  prior close.
- Selection: each evaluation date chooses a policy only from prior qualified
  trading dates. The evaluation date cannot influence its own policy.
- Primary result: cost-adjusted out-of-sample EV. Win rate, entry distance/time
  from the ex-post trough, MFE/MAE, exit distance from rebound peak, and
  opportunity capture are diagnostics.
- Judgment floor: each venue needs at least 46 coverage-qualified trading days.
  This is the operator-selected research sufficiency floor. Passing it permits
  research judgment only and does not authorize runtime, policy, or order use.
  Reports separately disclose the smaller walk-forward evaluation-date count
  left after prior-date training; the 46-day coverage count must not be
  presented as 46 out-of-sample dates.
  Before that, the artifact is a valid backtest run but cannot approve a
  strategy or runtime change.
- Authority: `runtime_effect=false`, no orders, accounts, token mutation,
  provider changes, bot control, or automatic parameter promotion.

The clean decision baseline is `2026-06-05`; older rows remain archive/audit
evidence and are rejected from this backtest.

## Commands

Backfill complete historical market bars using only the existing cached Kiwoom
token:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.monitoring.pure_market_kiwoom_backfill \
  --start-date 2026-06-05 --end-date YYYY-MM-DD
```

Generate the walk-forward report:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.monitoring.pure_market_reversal_replay \
  --start-date 2026-06-05 --end-date YYYY-MM-DD \
  --no-widget-observations --write
```

Use the most recent fully completed trading date for `YYYY-MM-DD`. A partial
backfill returns a non-zero status and must not be presented as complete.

## Regime-conditioned extension

A single normal or inverted signal interpretation is not used. The extension
routes each completed minute into one of `WEAK_DOWNTREND`,
`BEARISH_TRANSITION`, `NEUTRAL_TRANSITION`, `BULLISH_TRANSITION`, or
`STRONG_UPTREND` using only timestamp-exact 3/5/15-minute Samsung returns,
session VWAP, and timestamp-aligned KOSPI returns available at that instant.

- `weak_capitulation` admits a near-trough stabilization probe only during a
  weak or bearish-transition regime. It exits after two consecutive bullish
  transition observations, or by its selected stop/target/trailing/timeout.
- `bullish_recovery` admits the normal recovery setup during a bullish
  transition or strong uptrend. It exits after two consecutive bearish
  transition observations, or by its selected stop/target/trailing/timeout.
- Entry transitions are immediate because they already compare short and long
  completed windows. Regime exits require two confirmations and execute at the
  next bar open; this prevents one-bar regime flicker from becoming a simulated
  fill.
- KRX regular requires Samsung plus KOSPI context. NXT regular can use aligned
  KOSPI context, but NXT premarket and aftermarket remain explicitly
  instrument-only, so NXT cannot inherit KRX strategy authority.

Generate this separate report with:

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.monitoring.pure_market_regime_replay \
  --start-date 2026-06-05 --end-date YYYY-MM-DD --write
```

This extension remains `runtime_effect=false`; it does not change the current
widget, collector service, one-share automation, or main trading bot.

## Adaptive opportunity-surface extension

The adaptive extension removes the fixed drawdown/rebound opportunity label.
For every completed venue session it uses dynamic programming to find the
compounded-wealth-maximizing long-only next-open path after the configured
round-trip cost. This oracle path is an unattainable ex-post ceiling and may be
used only as a label and opportunity-density diagnostic.

The executable diagnostic is separate. For each evaluation date it trains only
on the previous 20 coverage-qualified dates, using completed volatility-scaled
1/3/5/15-minute returns, 20-minute price location, session VWAP, volume,
timestamp-aligned KOSPI relative movement, and known session progress. It then
predicts oracle buy/sell transitions and executes only at the next minute open.
The evaluation date and later prices never enter its features or training set.

```bash
PYTHONPATH=. .venv/bin/python \
  -m src.engine.monitoring.pure_market_adaptive_opportunity_replay \
  --start-date 2026-06-05 --end-date YYYY-MM-DD --write
```

Average precision is reported relative to oracle-action prevalence to answer
whether a reusable common state exists. The next-open cost-adjusted EV answers
whether the current probability-to-trade pairing is executable. A predictive
lift does not authorize runtime use when execution EV is non-positive, source
context is partial, or the 46-day research floor has not been reached.

### Nested pairability extension

The adaptive report adds a second chronological walk-forward layer after the
base buy-candidate replay. For each evaluation date, its pairability model may
learn only from candidate episodes generated out of sample on earlier dates.
The current date's exit reason and cost-adjusted profit are outcomes only.

The positive training outcome is a base candidate that reaches an adaptive
sell transition with positive cost-adjusted profit. Expired, session-end, and
loss-making sell-transition episodes remain negative evidence. Candidate-arm
and recovery-confirmation features, probabilities, elapsed time, and a
`weak_reversal` versus `bullish_transition` attribution are all known before
entry. Post-exit confidence and current-date outcomes are forbidden inputs.

Within prior history, the selection fraction is chosen on a chronological
validation suffix by EV first and cumulative percentage sum second. The final
model is then refit on all earlier episodes and applied to the untouched next
date. KRX and NXT remain separate, and NXT partial context cannot support KRX
or runtime authority. The extension remains `runtime_effect=false`.

### Lane competing-risk and direct-EV extension

The next layer does not reuse the common five-to-six-minute duration cap. It
extracts every causally confirmed base candidate and observes the first later
base-model event: `sell_transition`, `adverse_buy_transition`, or
`session_end_censored`. These events use prior-trained buy/sell models at each
completed decision bar and execute at the next open; oracle actions and future
prices are forbidden triggers.

`weak_reversal` and `bullish_transition` have physically separate event
classifiers and cost-adjusted-return regressors. Each evaluation date may use
only earlier base-OOS candidate episodes. Event probabilities remain risk
diagnostics; entry selection uses the lane model's directly predicted
cost-adjusted EV above the economic zero boundary, without a same-report tuned
probability threshold. Rejected candidates do not occupy a position slot, so
the replay can consider the next candidate. Accepted candidates exit on their
first causal transition or the actual final session execution timestamp.

Primary judgment compares selected and accept-all control EV on exactly the
same nested-OOS dates. Source-quality failure, especially NXT partial context,
is reported separately from negative strategy EV. This layer remains
`runtime_effect=false` and has no widget, order, account, provider, or bot
authority.

### Economic first-passage utility extension

The economic extension stops treating every base buy/sell probability crossing
as a realizable reversal boundary. A causally confirmed candidate instead
receives two price-path boundaries. Its favorable boundary is round-trip cost
plus a multiple of the candidate's completed trailing 20-minute volatility;
its adverse boundary is another multiple of the same causal volatility scale.
The first completed close to reach either boundary is observed and the outcome
executes at the next minute open. If neither boundary is reached, the episode
is censored at the actual session close.

An adverse price touch alone is not enough to terminate a weak-reversal
episode. That lane requires two consecutive adverse-boundary closes. The
bullish-transition lane requires either two closes or an adverse close with
simultaneously negative completed 3-minute, 5-minute, and acceleration context.
This keeps a one-bar dip from becoming the same premature exit defect as the
old probability crossing while retaining a causal structural-damage exit.

The target and adverse multipliers are not common fixed ENTRY/EXIT labels.
`weak_reversal` and `bullish_transition` choose them separately using only a
chronological validation suffix from earlier base-OOS candidates. A lane event
classifier and direct cost-adjusted EV regressor are then fitted only on prior
episodes. The untouched current date is selected only when its predicted EV is
above zero. Current-date paths, MFE/MAE, event duration, and realized return are
evaluation outcomes and are forbidden as entry features or boundary-selection
inputs.

The report retains accept-all and selected EV on the same OOS dates, compounded
net return, average pre-exit MFE/MAE, full-session counterfactual MFE/MAE,
the count of post-entry session MFE at or above 0.5% as an opportunity-density
diagnostic only, adverse-first episodes that later reached their favorable
boundary, median event duration, event counts, and
lane-separated summaries. Positive perfect-foresight opportunity density does
not grant runtime authority; this layer remains `runtime_effect=false`.

### Recovery-aware adverse exit and favorable trailing extension

This extension preserves the exact entries selected by the economic
first-passage layer. It changes only the counterfactual exit path, so a result
cannot be attributed to a different entry ranking or to a different
non-overlap schedule. Comparisons are restricted to economic-selected entries
whose lane has sufficient prior recovery evidence.

At the first causally confirmed adverse checkpoint, the feature vector uses
only the entry context and the completed checkpoint bar: return versus the
entry and volatility scale, pre-checkpoint MFE, elapsed time, breach streak,
3-minute and 5-minute returns, acceleration, VWAP distance, 20-minute range
position, relative volume, session progress, and distance to the favorable
boundary. Full-session MFE/MAE and every later price are forbidden inputs.
Separate lane models estimate whether bounded recovery improves net return,
the incremental net return, and diagnostic time to favorable recovery. The
adverse exit is deferred only when predicted incremental EV is above zero.

The deferred path remains bounded by a lane-specific prior-selected maximum
wait and a deeper adverse boundary. It therefore does not disable the adverse
guard. When the favorable boundary is reached, a prior-selected causal peak
drawdown multiple either exits immediately or trails until drawdown/session
end. Recovery wait, deeper-adverse, and trailing multiples are selected from a
chronological validation suffix containing only dates earlier than the
evaluation date; the estimators are also fitted only on prior candidates.

The primary comparison is cost-adjusted EV of the same-entry economic exit
and recovery-aware exit. Compounded net return, deferred/recovered counts,
pre-exit MFE/MAE, full-session opportunity density, and positive-MFE capture
ratio are diagnostics. KRX and NXT remain separate, NXT partial context cannot
grant KRX authority, and the entire extension remains `runtime_effect=false`
with no widget, order, account, provider, or bot authority.

### Recovery and favorable-trailing axis separation

The axis-separation layer evaluates four exits on the exact same
economic-selected entry timestamps: `baseline`, `recovery_only`,
`trailing_only`, and `recovery_plus_trailing`. An entry is included only when
the lane has sufficient prior evidence for both exit models. Arm-specific exit
duration never changes that fixed comparison cohort; this is an exit-policy
attribution experiment rather than a single-position capacity simulation.

Recovery-only policy selection, labels, and estimators force favorable exits
to execute immediately. They therefore contain no favorable-trailing outcome.
Bounded recovery still requires positive predicted incremental EV and retains
the prior-selected maximum wait and deeper-adverse boundary.

Trailing has a separate favorable-checkpoint classifier and incremental-return
regressor. Its features contain only the entry context and the completed
favorable checkpoint, including whether an adverse checkpoint had already
occurred. Training includes both direct favorable passages and favorable
passages reached after adverse confirmation, so the combined arm does not
apply an initial-favorable model to an unseen recovery context. A zero trailing
multiple is part of the prior validation policy grid. A nonzero prior-selected
multiple is applied on the evaluation date only when the separate predicted
incremental EV is above zero.

The primary result is the cost-adjusted EV of every arm and its paired delta
from baseline. Compounded net return, additional MAE, application counts, and
MFE capture remain diagnostics. Current-date outcomes cannot switch a lane or
select a multiplier in the same report. This layer remains
`runtime_effect=false`, keeps KRX and NXT separate, and has no widget, order,
account, provider, or bot authority.

### Recovery-only outcome direct entry utility

The recovery-entry layer asks a different question from the four-arm exit
comparison: which confirmed candidates should be entered when the owned exit
policy is bounded recovery-only? It does not reuse the baseline first-passage
outcome regressor as its entry utility. Separate `weak_reversal` and
`bullish_transition` regressors learn the cost-adjusted recovery-only return
directly from causal entry features.

Training labels are nested out of sample. On each earlier evaluation date, the
recovery policy and recovery checkpoint model must already have been fitted
only from dates before that evaluation date. Those completed recovery-only
episodes are moved to entry-utility history only after the earlier date has
been scored. The current evaluation date therefore cannot enter its own model,
policy, or threshold. A fixed economic zero boundary selects only positive
predicted recovery-only EV; there is no same-report lane switch.

The existing economic entry selector is the control. Control and candidate
selectors are both replayed on the same model-ready dates with the same
recovery-only exit policy, and rejected candidates do not consume a position
slot. This isolates entry selection from exit-policy differences. Primary
evidence is cost-adjusted EV; compounded return, pre-exit MAE, lane summaries,
selection count, and eligible opportunity count are diagnostics. Trailing
outcomes and full-session MFE/MAE are forbidden labels or entry features. The
layer is `runtime_effect=false` and has no widget, order, account, provider, or
bot authority.

### Prior-only recovery-entry calibration and capacity

The calibration layer evaluates whether the direct recovery-entry regressor's
predicted EV is reliable across later dates. Each lane calibrator can consume
only predictions that were already produced out of sample on earlier dates,
whose recovery-entry model and recovery-only exit model were themselves fitted
before the label date. The current date is appended to calibration history only
after its evaluation is complete.

Within a lane, a linear predicted-versus-realized utility relationship is
shrunk toward no slope according to prior sample count. Its intercept also
receives a bounded adjustment from residuals on the most recent three prior
dates. Selection uses positive calibrated mean EV. Prediction uncertainty is
reported only as a diagnostic; a positive lower-confidence-bound hard gate is
not used because it could collapse opportunity discovery in a thin sample. If
positive calibrated mean EV would retain fewer than 75% of that date's raw
recovery-selector non-overlap opportunities, the calibrated arm falls back to
the complete raw recovery arm for that date. This capacity fallback uses no
current-date outcome and prevents a negative historical mean from manufacturing
a zero-sample result.

Three arms share the same calibration-ready dates and the same recovery-only
exit policy: the economic selector control, the uncalibrated recovery-entry
selector, and the calibrated selector. Rejected candidates do not consume a
position slot, and each arm independently applies causal non-overlap based on
its selected recovery exit duration. The report separates raw selection count,
non-overlap count, retained opportunity ratio, EV, compounded return, and
pre-exit MAE.

Pareto improvement requires calibrated EV, compounded return, and MAE to be no
worse than both controls while retaining at least 75% of the uncalibrated
non-overlap opportunities. Post-OOS prediction-rank bins, lane residuals, and
date drift are diagnostics only and cannot become same-report lane switches or
thresholds. This layer remains `runtime_effect=false` with no widget, runtime,
order, account, provider, or bot authority.

### Recovery-entry causal timing nested OOS

The timing layer keeps the raw recovery-entry selector and recovery-only exit
owner fixed, and changes only the causal entry timestamp. Three bounded arms
are evaluated: completed-bar continuation confirmation, the first non-chasing
pullback turn, and two-bar VWAP reclaim hold. Every trigger uses a completed
minute and enters at the following open. The trigger bar's exact feature
vector, prior-model buy/sell probabilities, and volatility scale replace the
original confirmation context; later bars and full-session extrema cannot
enter the timing decision.

Each earlier evaluation date first produces all arm outcomes using the recovery
models that were already fitted before that date. A later date may select an
arm and a 3/5/10/20-minute maximum wait only from those earlier OOS outcomes.
The current-date result is appended after evaluation. Policy fitting begins at
four prior dates and 12 raw control episodes; the project-wide 46 qualified-day
research floor still owns the final decision.

Capacity is evaluated independently for each date. If a timed arm retains less
than 75% of the raw selector's non-overlap opportunities, that date falls back
to the complete raw next-open control before prior policy comparison. The same
fallback is enforced on the untouched evaluation date. Thus a sparse trigger
cannot manufacture an attractive zero-sample arm, while a fallback-identical
arm cannot be called positive or Pareto-improved without a strict improvement
in EV, compounded return, or MAE.

The report compares cost-adjusted EV, compounded net return, pre-exit MAE,
opportunity retention, fallback dates, and post-control MFE for candidates with
no timing trigger. KRX and NXT are kept separate; NXT partial context remains
`source_quality_blocked`. This is a manually invoked offline research replay,
not a scheduled intraday job, and remains `runtime_effect=false` with no widget,
runtime, order, account, provider, or bot authority.

### Candidate-level timing incremental utility nested OOS

The candidate utility layer removes the prior timing report's analytical
capacity fallback from the executable comparison. A baseline model sees only
the original recovery-entry candidate and the earlier-OOS selected timing arm,
then chooses `enter_now` or `wait`. After a wait, a separate model may see the
first completed-bar trigger context and choose `timed_entry` or `skip`. A
missing trigger is no trade; the replay never returns to the already-past raw
next-open price.

The exploration budget is causal and lane-specific. Three `enter_now`
decisions earn one `wait`, and that budget carries across evaluation dates so a
three-candidate day cannot reset away all exploration. Final positive or Pareto
judgment still requires at least 75% aggregate recovery-entry opportunity
retention. Realized control/timing outcomes are attached only after the OOS
decision as diagnostic attribution and are prohibited from the same-date
model, threshold, or action.

On the 46 qualified KRX dates, earlier-OOS pair history reached 30 candidates,
including 21 with a timing trigger. The utility models became ready for two
dates and evaluated six non-overlapping controls. The causal budget produced
five `enter_now` decisions and one `wait`; the waited candidate had a trigger,
but the trigger model predicted `-0.692171%` net EV and skipped it. Post-OOS
attribution showed that both immediate and four-minute-delayed recovery-only
paths realized `+0.446652%`, so the skip removed a winner. Selected opportunity
retention was 5/6 (`83.3333%`), but EV worsened from `-0.307658%` to
`-0.458520%`, compounded return from `-1.838699%` to `-2.275189%`, and MAE from
`-0.360498%` to `-0.389401%`. The result is therefore
`no_incremental_predictive_value`, not a runtime promotion. NXT remains
`source_quality_blocked`, and the layer has `runtime_effect=false` with no
widget, order, account, provider, or bot authority.

### Trigger-utility prior-only calibration and bounded exploration

The trigger calibration layer keeps the candidate-level baseline
`enter_now/wait` decision and the recovery-only exit owner unchanged. It stores
the raw trigger prediction, realized recovery-only net return, and residual only
after the evaluation date is complete. Every trigger-model, timing-policy, and
recovery-model fit date must predate that residual's trade date. A later lane
calibrator uses a rank slope shrunk toward one, a residual intercept shrunk
toward zero, and a bounded drift from the latest three prior dates. Current-date
residuals cannot affect the same date.

A causal exploration budget prevents negative trigger predictions from erasing
the evidence needed to evaluate them: three observed trigger entries earn at
most one model skip. This budget carries across dates. Missing triggers remain
no-trade and never fall back to the already-past raw next-open. Final comparison
also requires at least 75% of both whole-cohort and trigger-available
opportunities to remain observed.

On the 46 qualified KRX dates, the calibrator became ready for one untouched
date using seven prior OOS trigger predictions from two dates. On 2026-08-10,
the enter-now control, uncalibrated trigger gate, and calibrated bounded arm
contained 3, 2, and 3 non-overlapping episodes. Their cost-adjusted EVs were
`-0.128383%`, `-0.415901%`, and `-0.128383%`; compounded returns were
`-0.387128%`, `-0.830072%`, and `-0.387128%`; average pre-exit MAE was
`-0.216334%`, `-0.216509%`, and `-0.144339%`. The calibrated arm retained 100%
of control and trigger opportunities.

The 10:33 wait candidate is the key attribution. Raw trigger utility predicted
`-0.692171%`; prior-only calibration reduced it to `-0.122153%`, but did not
make it positive. The initial bounded-exploration rule nevertheless retained
the 10:37 timed entry, which realized `+0.446652%`. The result is
`calibrated_trigger_utility_pareto_improved` relative to the raw gate and no
worse than control, but the improvement is the combined calibration plus
exploration effect. Absolute EV remains negative and only one calibration-ready
date exists, so this is not runtime-promotion evidence. NXT remains
`source_quality_blocked`; `runtime_effect=false` and all order, widget,
provider, account, and bot authority remain forbidden.

### Candidate timing wait-budget arms and prior-only selection

The wait-budget layer changes only how frequently a positive baseline timing
utility may choose `wait`: three enter-now decisions per wait, two per wait, or
one per wait. All arms share the same prior-only trigger calibration, bounded
trigger exploration, and recovery-only exit owner. The original 3:1 decisions
are asserted identical to the preceding calibrated-trigger layer.

Each arm is an OOS observation on its evaluation date. Its realized outcome is
added to arm history only after every arm decision for that date is complete.
An executable selected arm can therefore be chosen only on a later untouched
date. The selector ranks capacity-safe arms by prior OOS cost-adjusted EV, then
compounded return, pre-exit MAE, and the more conservative enter-per-wait ratio.
It adds no minimum date floor beyond the 46 qualified trading days. A failed
arm is excluded without blocking the remaining capacity-safe arms.

The first arm-comparison date was 2026-08-10. The 3:1, 2:1, and 1:1 arms each
retained three non-overlapping episodes and 100% of observed triggers. Their
cost-adjusted EVs were `-0.128383%`, `-0.092497%`, and `-0.092497%`; compounded
returns were `-0.387128%`, `-0.279438%`, and `-0.279438%`; average pre-exit MAE
was `-0.144339%`, `-0.180414%`, and `-0.180414%`. The 12:53 candidate's 12:54
timed entry reduced its loss from `-0.415551%` to `-0.307892%`, but worsened
the arm's average MAE. Waiting from 11:21 to 11:23 produced the same entry price
and net outcome, so 1:1 added no EV over 2:1. The 2:1 arm also retained higher
average MFE (`0.288133%` versus `0.252019%`).

No earlier complete arm-comparison date existed, so the report deliberately
records zero prior-selected policy evaluations and closes as
`insufficient_wait_budget_history`. The next complete date may select 2:1 from
this prior history, but the 2026-08-10 result cannot be used to reselect its own
arm. NXT remains `source_quality_blocked`; `runtime_effect=false` and order,
widget, account, provider, and bot authority remain forbidden.
