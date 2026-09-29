# 2026-09-29 scalp simulator retirement and Samsung morning health review

## Decision and evidence

- The base scalp simulator still created virtual holdings on 2026-09-29. The `000990` receipt had `actual_order_submitted=false` and `broker_order_forbidden=true`, while its runtime target requested a separate WS registration. This consumed observation work without real-order authority.
- The postclose wrapper still invoked `sniper_post_sell_feedback --backfill-sim-candidates --evaluate-sim` by default. Its 2026-09-28 execution observed zero sim events, zero candidates and zero evaluations, while the process ran for about 25.8 seconds. The latest retained sim evaluation file was dated 2026-09-23. These facts do not make older sim outcomes equal to real execution quality.
- New runtime simulator creation and state-file restoration are now hard OFF. The scheduled postclose wrapper no longer invokes the sim evaluator. Historical files, their explicit CLI replay, and real post-sell/holding/order custody remain available. The legacy `SCALP_LIVE_SIMULATOR_ENABLED` configuration field is retained for historical receipt compatibility, but it cannot reactivate the runtime gate.

## Review and validation

- Reviewed the two runtime creation/restoration gates, main target synchronization, sim-only WS registration, postclose wrapper, and downstream report compatibility. No Kiwoom request/response/REG packet contract was modified.
- Targeted test: `test_retired_runtime_does_not_arm_or_restore_simulator` proves that an old in-memory sim target is removed and a new trigger creates neither a sim target nor a WS registration.
- The two historical simulator test modules have 8 failures in both the prior selected release and this change. They concern legacy sim scale-in/PYRAMID paths and are not caused by the retirement patch. The remaining affected tests pass: 76 passed, 18 skipped, 8 known-baseline deselected. Python compile, `bash -n`, `git diff --check`, and the print-only checklist parser pass.
- The historical simulator tests explicitly enable their old helper through a fixture, so they continue testing archival behavior without reopening the production runtime gate.

## Samsung morning alert

- The detector's `systemd_expected_set_unreadable` means at least one `systemctl show` or same-date journal query was unreadable. That reason alone does not establish a failed morning order/service.
- This host's 2026-09-29 preflight and live service both exited successfully at 07:57:21 and 08:00:07 KST. The timer remains loaded/enabled/active. The 10:27 detector reported `process_health=pass`, `one_shot_completed`, `exact_date_authority_and_terminal_service_success`.
- The supplied alert text is absent from the retained local detector log and surviving dated report, so its specific query error and timestamp cannot be reconstructed. No service replay, authority rewrite or detector threshold change is justified by this evidence.

## Acceptance boundary

Code/test closure, release selection, actual PID consumption, a subsequent `scalp_sim=0` runtime count, and the next scheduled postclose skip are separate checks. Historical sim PnL remains sim-only; this retirement is not a real-order or net-profit improvement claim.
