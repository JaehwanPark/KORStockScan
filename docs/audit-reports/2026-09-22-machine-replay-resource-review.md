# Machine policy postclose replay resource review — 2026-09-22

## Scope and observed defect

The authorized main-machine worker was terminated with SIGTERM after preserving its atomic checkpoint in `tmp/machine-replay-optimization-20260922/checkpoint-before.json`. The independent stage recorded exit -15. No trading process was restarted.

KRX training contained 12,127 supported attempts; 2,086 had comparable full-cost paths and 10,041 lacked a compatible cost/path contract. The 96-candidate traversal replayed all attempts, deep-copied training evidence and retained every candidate's detailed evidence. The stopped worker used about 3.6 GiB RSS plus swap after more than 80 minutes. Candidate search was progressing, not waiting for AI.

## Implementation and review

- Keep the same complete source population, chronological boundary, policy search budget and support-adjusted win-rate/EV ranking.
- Prepare cost-bound path eligibility once. Skip candidate replay only for cost/path-excluded incumbent BLOCK/RECHECK attempts. Record the skipped reasons and explicitly limit transition diagnostics to replayed rows. Economic exclusions remain in the metrics; unknown returns never become zero.
- Replay every incumbent ENTER_NOW, including unpriced entries. An unevaluable existing-entry admission change still prevents candidate promotion.
- Reuse read-only nested evidence with isolated top-level working rows/setup; only comparison is replaced. Preserve the deep-copy behavior for the non-machine evaluator.
- Bound detailed evaluation cache to one arm. Best evidence, incumbent evidence and compact candidate economics remain available.
- Runtime decision kernels, AI policies, hard guards, source schemas and cost assumptions are unchanged. Missing historical source contracts remain explicit gaps.

Review found an existing test requiring isolated top-level setup objects; the implementation now retains that boundary. Re-review checked nested kernel copying, candidate/holdout handling, exclusion denominators, unpriced existing-entry safety, checkpoint source hashes and deployment scope.

## Validation

327 targeted tests passed across entry strategy, outcome calibration and runtime policy contracts. Added regressions verify skipped nonentry replay counts, input immutability, unchanged economic denominator and the unpriced existing-entry promotion guard.

A bounded 120-attempt/24-candidate benchmark compared the committed old evaluator with the new evaluator on identical inputs: 2,880 -> 580 replay calls; 4.245 -> 0.870 seconds. All candidate economics and selected rank were identical. This is fixture evidence, not a claimed full-day speedup. Evidence: `tmp/machine-replay-optimization-20260922/benchmark.json`.

Deployment and regenerated next-session policy/economics are tracked below after execution. Actual market consumption and realized PnL remain separate from counterfactual policy evaluation.
