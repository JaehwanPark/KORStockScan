# Finalization historical checklist observer repair — 2026-10-07

## Decision and authority

Repair the two report consumers that reject an approved historical finalization solely because the current checklist changed. Existing owner: `SemanticMonitorProducerConsumerRefresh1007`; existing user approval covers implementation, review, integrated deployment and restart. The frozen daily checklist and its existing acceptance remain unchanged. No new postclose completion, policy selection or economic acceptance is claimed.

## Evidence

- The original 2026-10-06 finalization DONE was recorded at 2026-10-07 08:56:16 KST, after the 06:50 cutoff.
- Original chain: `fb84848e3085e3b6f4938e23a8f708b954dc61968320eeb5115dfc4150e63693`; snapshot: `cd83b048db1745630e0fcea8e0ddf3f8fcde8f45d6af04f8bb4826f853d36158`.
- Strict checklist SHA: `0f470d5ec16f3888cd3d1d489813cb67647ee2768d5f46167a5bc1b790da6f61`. The approved immutable historical snapshot has these exact bytes.
- Current checklist SHA: `1b7156388db7b592a45cbfc81dad0b1adb8e620c96b17d9c7b7c2c468a17893c`. Native intraday handoff and current PID consumption preserve both generations, but finalization/semantic observers omitted that custody.
- Before repair, cron reported `strict_checklist_generation_stale`; semantic handoff additionally reported `strict_generation_changed_during_recheck`.

## Implementation and review

1. Startup automation provides a read-only historical checklist reference only after exact source/current trading date, selected release, frozen handoff, consumed receipt schema/status, actual live PID/start ticks/cwd, bootstrap manifest and race checks pass.
2. The finalization marker observer retries only the checklist-stale failure with that reference. It still validates all strict/stage/summary/Main terminal and snapshot sources against original DONE hashes. Public fresh finalization capture keeps the current checklist requirement.
3. The semantic postclose observer consumes the same reference and reruns the native generation validator. Other source errors remain failures.
4. Cron health exposes the validation basis. Genuine late completion remains `recovered_late`; original DONE and postclose artifacts are not rewritten.

Review covered malformed/missing handoff, schema/status/manifest mismatch, reused PID, handoff mutation during verification, snapshot changes, summary/stage changes and both DONE generation hashes. No unresolved in-scope findings remain after the race-check supplement.

## Validation and deployment closure

Evidence directory: `tmp/finalization-checklist-alert-20261007/`.

- Targeted suite: 305 tests covering intraday handoff, finalization, both detectors, PREOPEN, controller and Main v2 publication.
- Local real-source replay: finalization issues `[]`; semantic handoff `done` with findings `[]`; cron retains historical late-completion warnings only.
- Compile and `git diff --check`, document owner/link check and print-only backlog parser are required before release selection.
- Deployment pending at this implementation checkpoint. The immutable release must pass the same suite, preserve original PREOPEN/checklist/source hashes and 186 episode pins, reissue only identical Main v2 cells/research contracts for the new execution commit, then verify native restart/PID, five-symbol source capture and naturally published health.
- Heavy postclose regeneration, EOD, provider/order requests, external document sync and unrelated widget retirement are excluded from this consumer repair.
