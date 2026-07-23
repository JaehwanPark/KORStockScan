# Intraday WS Freshness Postclose Workorder - 2026-07-23

Codex execution scope: implement only source-quality, instrumentation, report, provenance, and tests.

## 2-Pass Execution

1. First pass: implement instrumentation/report/provenance fixes, run code review, fix defects, and re-review.
2. Second pass: confirm final review, regenerate the related report, and inspect workorder diff.

## Guardrails

- runtime_effect=false
- allowed_runtime_apply=false
- broker_order_forbidden=true
- forbidden_uses=EV,rolling_tuning,MTD_tuning,cumulative_tuning,live_auto_promotion,runtime_apply_bridge,intraday_threshold_mutation,stale_submit_bypass,broker_guard_bypass,provider_route_change,order_price_change,quantity_cap_change,position_cap_release,bot_restart,real_execution_quality_approval

## Selected Directives

### order_ws_total_stale_escalation

- decision: `implement_now`
- priority: `1`
- title: WS total stale escalation
- intent: Treat rows where both trade and orderbook websocket freshness are stale as subscription/connection quality incidents and verify repair evidence after postclose.
- evidence: `['both_ws_stale_count=1161']`
- files_likely_touched: `['src/engine/kiwoom_websocket.py', 'src/engine/monitoring/quote_stale_frequency_report.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py']`
- acceptance_tests: `['PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py']`

### order_ws_trade_tick_quiet_low_liquidity_classification

- decision: `implement_now`
- priority: `2`
- title: WS trade tick quiet low-liquidity classification
- intent: Keep fresh 0D plus stale/missing 0B as trade_tick_quiet source-quality evidence, and enrich low-liquidity classification with cumulative-volume provenance before requesting subscription repair.
- evidence: `['pipeline_trade_tick_quiet_count=560', 'fresh_0d_stale_0b_count=520', 'snapshot_trade_tick_quiet_count=0']`
- files_likely_touched: `['src/engine/kiwoom_websocket.py', 'src/engine/sniper_state_handlers.py', 'src/engine/monitoring/intraday_ws_freshness_monitor.py', 'src/tests/test_state_handler_fast_signatures.py']`
- acceptance_tests: `['PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py']`

## Required Final Report Split

- Existing implementation
- New implementation
- Deferred or non-implement items
