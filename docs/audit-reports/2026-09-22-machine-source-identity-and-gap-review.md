# Machine source identity and update-gap repair — 2026-09-22

## Scope and authority

The user authorized repair, review/fix iteration, deployment and guarded restart. This change owns current-decision logging and frozen source diagnostics. It does not change policy selection, AI providers, freshness limits, subscriptions, order routes or hard safety.

## Findings and repair

- At 17:26:35, 003670's exact machine attempt had KRX_NXT_INTEGRATED in its terminal event but UNKNOWN in ai_confirmed. The generic AI ops projection omitted the canonical venue/session that the terminal projection already retained. The ops projection now reuses the existing machine provenance helper on the call-local decision. It does not read the mutable watched-stock cache or infer an underlying execution venue. Explicit UNKNOWN and missing evidence remain unresolved.
- At 17:30:41, 290690's final trade/book receive ages were 3624.739/3603.258 ms; at 17:30:16, 493280's were 3173.900/978.488 ms. The existing 3000 ms source guard blocked these attempts. Context capture cost was 0.075/0.086 ms. These observations do not prove a recurrence of the old synchronous logging delay.
- Final snapshots previously retained only the derived OBSERVATION_UNPROVEN state. They now also freeze the selected route's existing 0B/0D item, route, epoch, timestamp and sequence, plus quiet-observation last_quote/last_trade/closed_episodes. Existing snapshot -> trace -> pipeline trade_activity projection carries these facts. No new reader, network call, filesystem lookup, subscription action or decision condition is introduced. Unknown remains null; local sequence is not an exchange sequence or proof of complete transport.
- Receipt evidence inherits the snapshot's source-quality observation contract and exact snapshot clock. Historical no-print versus receive-loss attribution remains unproven; old events are not rewritten or marked recovered.

## Review and validation

Reviewed current-decision producer, ops/terminal projections, pipeline merge precedence, Sentinel exact six-field identity, frozen route receipt source and trace consumer. Explicit order-stage venue precedence and existing duplicate-key exclusions remain intact. Regression coverage includes BLOCK/RECHECK/SOURCE_INVALID on both event stages, later-stock identity isolation, explicit UNKNOWN, absent continuity, cross-epoch receipts and immutable captured facts.

Validation and deployment receipts: `tmp/machine-lineage-gap-20260922/`. Deployment and natural evidence will be appended after validation.

## Rollback and acceptance

Prior selected release: machine-success-20260922-35eb8e489. Rollback is its saved release selection followed by the standard guarded restart; no policy rollback is required for this diagnostic repair. Completion requires clean release validation, selected-release/PID receipt and inspection of newly generated pipeline/snapshot records. Natural market silence and improved EV are separate, unproven outcomes.

## Deployment validation

- Source commit `4b1631d3b7424c01b5e0b94536bcd29482b375f0` pushed to main; managed release `machine-lineage-20260922-4b1631d3b` selected.
- Workspace: 712 core tests and 384 transport/latency tests passed. Two unrelated fast-signature baseline failures (floating-point exact equality and old feature parity expectation) reproduced on the clean previous release. New release: **1096 passed, 2 deselected**, with the same two baseline tests excluded; compile, diff and print-only checklist parser passed. No package, broker API or WebSocket protocol change.
- Standard guarded restart completed at18:05:16: PID269562 ->286554. PID/cwd attestation and dated bootstrap/env verification PASS. Main singleton confirmed; morning custody handoff not required because its owner is inactive.
- Policy current receipt remains byte-identical: bundle `0c329961a6d8c8301cd91a5c3ad126f2f281ccdf612c27eb0901a2e758063b66`. Inactive machine postclose service repinned to the reviewed release, and cron routing verified. No policy regeneration or notification was invoked.
- Exact receipts: `release-validation.json`, `release-tests.log`, `baseline-clean-tests.log`, `deployment.json`, `selection-before.json`, `machine-service-before.conf`, `restart.log`, `pid-receipt.json`, `policy-before.json` under the evidence directory above.

## Natural acceptance after restart

At18:07:09–18:07:33, nine machine snapshots attested PID286554 and contained the new selected-route continuity evidence. Fourteen ai_confirmed/blocked_ai_score events from nine exact attempts passed the existing Sentinel six-field identity join, with zero missing identities. For003670, both stages at18:07:14 shared the same attempt, integrated venue/session and unchanged bundle. Existing UNKNOWN actual execution-venue facts remained UNKNOWN.

The new evidence distinguished fresh coherent receipt clocks from unproven continuity:067310 and046890 had quiet-observation last_trade=0 despite a recent 0B receipt. This identifies the missing continuity input; it does not establish exchange silence, network loss or which earlier state reset occurred. Existing source/feature guards remain in force. The three engine/handler/WebSocket error logs had no writes after restart at this check. Natural evidence is bounded to this sample, not a claim of all-day recovery or EV improvement.

Receipts: `natural-evidence.json`, `natural-identity-validation.json`. Scoped implementation/review/deployment/natural-record acceptance is complete; historical source loss remains explicitly unresolved.
