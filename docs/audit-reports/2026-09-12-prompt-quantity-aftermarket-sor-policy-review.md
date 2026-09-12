# Prompt quantity separation and aftermarket SOR successor-policy review

Reviewed: `2026-09-12T17:54:19+09:00` KST

## Decision

`code_review_closed`: the entry-prompt rollout no longer owns quantity, residual-leg expansion, or scale-in. Those decisions remain with the existing position-sizing, entry-split, and scale-in policy families. The 2026-09-14 SOR one-share canary stays an exact-date boundary; it is not removed by a prompt selection.

## Successor-policy contract

The daily report publishes `krx_aftermarket_sor_runtime_policy_v1` for the next KRX trading date only when the canary has a broker order receipt, requested/effective route `SOR`, allowed effective order type (`0`, `00`, or remapped `6`), no recorded contract failure, source-quality pass, and a valid `position_sizing_dynamic_formula` artifact. PREOPEN binds the policy by file/content SHA and exact active date. The order boundary requires a current venue-eligibility result and preserves cap, cooldown, owner/custody, price-freshness, and hard-safety guards. Missing or invalid policy evidence fails closed.

## Kiwoom reference gate

Official reference retrieved `2026-09-12T17:54:19+09:00`: [Kiwoom-Securities/Kiwoom-REST-API](https://github.com/Kiwoom-Securities/Kiwoom-REST-API), main commit `234560d213acd8871ae344b5481aecd2f30287fa`.

- Inspected `kiwoom/_data/kiwoom_api_spec.json` (`kt10000`: `/api/dostk/ordr`, API-id header, `dmst_stex_tp`, `stk_cd`, `ord_qty`, `ord_uv`, `trde_tp`, `cond_uv`).
- Cross-checked `kiwoom/specs.py` and `kiwoom/core/client.py` for API-id/continuation conventions.
- This change does not alter REST paths, request payload fields, authentication, retry/concurrency, or submit behavior; it only strengthens local policy selection and pre-submit eligibility provenance.

## Validation

- `605 passed`: focused prompt, intraday activation, rollout, Kiwoom order boundary, daily report, and PREOPEN policy suites.
- Python compile for all changed modules; `bash -n src/run_bot.sh`; `git diff --check` passed.

Natural canary execution, a later PREOPEN receipt, PID consumption, and cost-adjusted economics remain separate 2026-09-14+ evidence.
