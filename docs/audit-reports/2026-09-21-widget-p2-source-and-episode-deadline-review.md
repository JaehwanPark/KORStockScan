# Widget P2 source selection and episode deadline review — 2026-09-21

Owner: [WS plan](../proposals/widget-episode-shared-ws-market-data-improvement-plan-2026-09-21.md), checklist `KiwoomCommonHealthOpportunityCostAcceptance0917`. User requested the next priorities after the [15:02 read-only bottleneck audit](../../tmp/widget-episode-submit-recheck-20260921-1502.json); deployment/restart authority persists. Main submit logic and previously deployed P2E changes must be preserved.

## Scope and implementation

- Existing three primary collectors gain explicit `KORSTOCKSCAN_WIDGET_MARKET_DATA_SOURCE=ws` selection. Default/rest retains the previous path. Selected valid WS replaces that symbol's ka10001/ka10004 and Samsung's optional ka10003 negative-veto input. Initial/updated completed bars, daily history, peer/index/flow inputs remain existing REST; no new token, connection, subscription, account request or broker order.
- Existing WS receiver retains raw FID18/12 in the same exact-item 0B record and the existing atomic publisher carries them. The existing shared reader validates producer process/epoch, source route, original receive clocks and 0B/0D fields. Day-low is positive absolute KRW; signed percent is preserved. Samsung's descending-three-print negative veto retains exact original sequence/receive order and fails closed on missing/invalid history. No extra engine-root module or duplicate collector.
- WS input does not renew timestamps or create REST receive metadata. BBO carries explicit WS provenance and revalidates source age/PID after auxiliary work. The existing 20-second collector freshness, price/BBO coherence, completed-bar quality and strategy thresholds remain unchanged. Missing selected WS input raises an explicit source gap; it cannot start unbounded REST recovery. Source selection failure has a separate census counter.
- P2's initial applied cohort is the existing Samsung/Doosan/Hanwha Ocean three collectors, not58/198-symbol expansion. `_AL` is an explicit integrated observation source; the consumer's trading session and original REST completed-bar scope remain distinct. This is the user-authorized bounded input rollout, not a claim that the previous P1 three-window census passed. Future complete windows are the natural acceptance boundary.
- Existing regular episode owner deadline is shared between preparation and final validation. A last completed bar whose owner deadline already passed is rejected before market-data guard requests or registry reservation. PLANNED legs that expire remain NO_FILL; submitted/ambiguous orders and earlier fills are untouched. Final owner expiry is `SKIP_OWNER_DEADLINE`, distinct from policy/owner identity changes. No deadline extension, threshold/quantity change or historical signal replay.

## Official API gate

[Upstream receipt](../../tmp/widget-p2-20260921/official-reference.json): current HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, revalidated during this task. Packaged ka10001 and0B/0D/ka10003 specifications, previously inspected identical-revision specs/core/realtime/Postman confirm FID12 is signed percent, FID18 signed KRW, FID10 current price, FID20 provider clock and0D best quotes/quantities. `kiwoom_docs` is absent. [ka10001 extraction](../../tmp/widget-p2-20260921/ka10001-spec.json). Existing real/demo endpoint and REG/REMOVE/auth semantics are unchanged; no upstream order example was executed.

## Review and validation

- First affected regression377 PASS. Added actual collector call-path tests in both REST and WS modes, primary-symbol REST0 assertions, original clocks/negative-veto preservation, missing fields/invalid source rejection and writer/receiver field lineage.
- [Integrated regression](../../tmp/widget-p2-20260921/review-tests.log):577 PASS. [Follow-up regression](../../tmp/widget-p2-20260921/final-followup-tests.log):419 PASS (overlapping counts), including expanded regular owners, source endpoints and unchanged transport guards. Test failures from expected REST request sets were corrected to verify the WS path's removed primary reads rather than weakening runtime behavior.
- Last-bar test uses the real regular machine loop with a closed owner window, asserting no liquidity lookup, reservation or submit, including state reload. Final-check test distinguishes expiry from a policy change. No real-order test or report replay.
- Review retained exact source metadata after slow auxiliary work, original market scope, failed-cycle denominator, inactive/retired service boundaries and atomic immutable deployment. Wider source coverage, three-window statistics, natural submissions/fills and post-cost economics remain separate.

## Deployment and natural evidence

Pending final immutable source validation and guarded producer/consumer handoff. Ended episodes will not be manually started. Rollback restores only the new unit source bindings and the immediately preceding integrated main release, preserving policy, custody and historical identities. New producer/consumer generations invalidate mixed pre-restart windows; no old P1/P2E window is silently reused as P2 acceptance.
