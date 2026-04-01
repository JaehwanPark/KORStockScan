# kiwoom_sniper_v2 Dependency Audit

This document lists external dependencies on `src/engine/kiwoom_sniper_v2.py` that must remain stable during refactoring.

## Direct Runtime Imports

### `src/bot_main.py`
- Import: `import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2`
- Usage:
  - `run_sniper()`

### `src/notify/telegram_manager.py`
- Import (dynamic): `import src.engine.kiwoom_sniper_v2 as kiwoom_sniper_v2`
- Usage:
  - `analyze_stock_now(code)`
  - `get_realtime_ai_scores(codes)`
  - `get_detailed_reason(code)`

## Tests (Direct Imports / Global Mutation)

### `src/tests/test_watching_scalping.py`
- Import: `from src.engine import kiwoom_sniper_v2`
- Import: `from src.engine.kiwoom_sniper_v2 import handle_watching_state`
- Global variables mutated in tests:
  - `KIWOOM_TOKEN`
  - `WS_MANAGER`
  - `AI_ENGINE`
  - `highest_prices`
  - `alerted_stocks`
  - `cooldowns`
  - `LAST_AI_CALL_TIMES`
  - `TIME_09_00`
  - `TIME_09_03`
  - `TIME_16_00`

### `src/tests/test_watching_with_radar.py`
- Import: `from src.engine import kiwoom_sniper_v2`
- Import: `from src.engine.kiwoom_sniper_v2 import handle_watching_state`
- Global variables mutated in tests:
  - `KIWOOM_TOKEN`
  - `WS_MANAGER`
  - `AI_ENGINE`
  - `highest_prices`
  - `alerted_stocks`
  - `cooldowns`
  - `LAST_AI_CALL_TIMES`
  - `TIME_09_00`
  - `TIME_09_03`
  - `TIME_16_00`

### `src/tests/test_handle_holding.py`
- Import: `from src.engine import kiwoom_sniper_v2`
- Import: `from src.engine.kiwoom_sniper_v2 import handle_holding_state`
- Global variables mutated in tests:
  - `KIWOOM_TOKEN`
  - `WS_MANAGER`
  - `AI_ENGINE`
  - `highest_prices`
  - `alerted_stocks`
  - `cooldowns`
  - `LAST_AI_CALL_TIMES`

### `src/tests/test_holding_logic.py`
- Import: `from src.engine import kiwoom_sniper_v2`
- Import: `from src.engine.kiwoom_sniper_v2 import handle_holding_state`
- Global variables mutated in tests:
  - `KIWOOM_TOKEN`
  - `WS_MANAGER`
  - `AI_ENGINE`
  - `highest_prices`
  - `alerted_stocks`
  - `cooldowns`
  - `LAST_AI_CALL_TIMES`

## Direct Execution Entrypoint

### `restart.sh`
- Runs: `python src/engine/kiwoom_sniper_v2.py`

## Notes

- Documentation references (README, docs) mention `kiwoom_sniper_v2.py` but do not affect runtime.
- Refactoring should preserve the public API and globals listed above (or provide compatible proxies) to avoid breaking runtime or tests.
