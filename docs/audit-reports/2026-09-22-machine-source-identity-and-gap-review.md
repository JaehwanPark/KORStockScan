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
