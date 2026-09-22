# Samsung morning preflight release binding recovery

Owner: `DirectFamilyPreopenPolicyHandoff`, target date2026-09-22. The user reported the `exact_date_authority_missing_or_stale` alert; existing session authorization covers reviewed repair, deployment and restart. This is a scoped deployment binding repair, with no strategy or safety relaxation.

## Cause

The07:57 scheduled Samsung preflight remained in its verification loop after the08:05 acceptance deadline. Its wrapper was bound to `entry-machine-handoff-complete-20260921-4cb5b62ff`, while the actual main PID13962 ran `postclose-handoff-20260922-98c70f566`. The old verifier returned exactly `pid_env_mismatch:KORSTOCKSCAN_AI_INPUT_PREFLIGHT_ARTIFACT_DATE`; the current main release returned PASS for the same PID and target date. The PID value2026-07-29 is the preserved protective baseline provenance, not a claim of today's market-data freshness. The current version validates the retired promotion's preserved rollback/baseline contract; the old version reconstructed its date differently. No date was rewritten to manufacture agreement.

The Samsung authority remained2026-09-21 and the live unit had no PID. The detector correctly reported the missed exact-date readiness deadline. Its observed health artifact had operational_mutation_count0; automatic recovery had not fixed the binding. The preflight's repeated verification alone could not converge while it used the old code.

## Repair and validation

The current immutable release passed103 existing runtime-bootstrap, AI-context-promotion and Samsung-preflight tests. The unchanged wrapper passed `bash -n`; effective systemd verification passed. Two existing preflight overrides were backed up and repinned to the current selected main release, including WorkingDirectory, PYTHONPATH, project/python paths and ExecStart. Only the waiting preflight was restarted at08:08:25. The wrapper reused the already published same-date Samsung policy (written=false); quantities, policy hash, timing and broker guards were not changed.

At08:08:36 the normal preflight issued target_date2026-09-22/statusready authority. At08:08:38 it completed successfully and the already pending morning service started naturally as PID19091. Its own existing widget episode release remains unchanged. Main selection/PID13962 were identical before and after; no main restart or manual broker order was issued. Startup is not evidence of an order, fill or profit.

Evidence: [recovery/PID and authority receipt](../../tmp/samsung-preflight-binding-20260922/recovery.json), [override backups and rollback plan](../../tmp/samsung-preflight-binding-20260922/plan.json), [103 tests](../../tmp/samsung-preflight-binding-20260922-tests.log), [old-verifier failure](../../tmp/samsung-preflight-verify-20260922.json.log). Rollback restores the two saved preflight overrides followed by daemon-reload and a scoped preflight restart; it does not rewrite the main runtime or authority dates. The current error-detection artifact owns the subsequent automatic health verdict.

## Final automatic verdict and separate no-trade outcome

The08:09:18 automatic error report is overallpass, with Samsung `one_shot_completed / exact_date_authority_and_terminal_service_success`. The machine PID19091 exited0 at08:08:56 after a terminal `NO_TRADE`, not an active-running state at the final check. Both legs show `NO_FILL` with adverse-flow `SOURCE_UNAVAILABLE`; the checkpoints report `exact_route_missing_or_duplicate`, and the episode records actual_order_submittedfalse. This is a pre-submit source block, not a broker-submitted unfilled order. No forced retry, terminal reset or guard bypass was performed.

The scoped authority/startup alert is closed. The distinct remaining owner is the entry adverse-flow exact-route source consumer; next action is to compare the requested route/item with its raw shared-WS checkpoints before deciding whether this is missing source or a route adapter defect. Its closure test is a valid exact-route checkpoint through the existing guard, preserving the consumed attempt and no duplicate order submission. This repair does not claim to have resolved that source block. See [automatic health receipt](../../tmp/samsung-preflight-binding-20260922/health-after.json) and [terminal state summary](../../tmp/samsung-preflight-binding-20260922/terminal-state-summary.json).
