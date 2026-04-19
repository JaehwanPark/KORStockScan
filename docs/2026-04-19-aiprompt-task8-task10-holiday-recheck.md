# 2026-04-19 AIPrompt 작업 8/10 휴일 재점검

> 작성시각: `2026-04-19 09:26 KST`
> 기준 Source/Section: `docs/2026-04-19-stage2-todo-checklist.md` / `체크박스 미완료`
> 대상 Project 항목:
> - `[Checklist0413] AIPrompt 작업 10 HOLDING hybrid 적용` 1차 결과 평가 / 확대 여부 판정
> - `[Checklist0413] AIPrompt 작업 8 감사용 핵심값 3종 투입` 미완료 시 사유 + 다음 실행시각 기록

## 1. 작업 10 `HOLDING hybrid 적용`

### 판정

- `보류 유지`

### 근거

- `src/engine/sniper_state_handlers.py`의 현재 HOLDING 경로는 여전히 `BUY/WAIT/DROP` 기반 score 평활화 중심이며, `FORCE_EXIT` 제한형 hybrid 관찰에 필요한 `holding_action_applied`, `holding_force_exit_triggered`, `holding_override_rule_version` 로그 축이 확인되지 않는다.
- `src/engine/sniper_state_handlers.py`에는 `DROP`을 사실상 exit placeholder로 다루는 주석과 로직이 남아 있어, 문서상 `FORCE_EXIT` 제한형 MVP와 코드 관찰축이 아직 일치하지 않는다.
- `docs/2026-04-18-nextweek-validation-axis-table-audited.md`는 HOLDING schema 변경 직후 성과 판정을 금지하고 `D+2` 버퍼를 권고한다. 휴일인 `2026-04-19`에는 추가 실표본이 없어 확대 여부를 닫을 수 없다.

### 다음 액션

- `2026-04-20 POSTCLOSE`에는 `shadow-only 유지 / 확대 보류` 1차 판정만 수행한다.
- `2026-04-22 POSTCLOSE`에 `missed_upside_rate`, `capture_efficiency`, `GOOD_EXIT`와 override 로그 축을 함께 보고 최종 확대 여부를 닫는다.

## 2. 작업 8 `감사용 핵심값 3종 투입`

### 판정

- `미완료 유지`

### 근거

- `src/engine/scalping_feature_packet.py`, `src/engine/ai_engine.py`, `src/engine/ai_engine_openai_v2.py` 기준 `buy_pressure_10t`, `distance_from_day_high_pct`, `intraday_range_pct` 값 자체는 프롬프트 입력에 포함된다.
- 반면 문서 원안이 요구한 `buy_pressure_10t_sent`, `distance_from_day_high_pct_sent`, `intraday_range_pct_sent` 감사 로그는 코드상 확인되지 않는다.
- 현재 감사 필드는 `scalp_feature_packet_version`, `tick_acceleration_ratio_sent`, `same_price_buy_absorption_sent`, `large_sell_print_detected_sent`, `ask_depth_ratio_sent`까지만 노출되어 있어 작업 8 완료 기준을 충족했다고 보기 어렵다.

### 다음 액션

- `2026-04-20 POSTCLOSE 15:45~16:00`에 main runtime 실표본에서 3개 sent 로그가 실제로 남는지 우선 확인한다.
- sent 로그가 계속 없으면 같은 슬롯에서 `사유 + 다음 실행시각`을 재기록하고, 완료 판정은 보류한다.

## 3. 검증

### 코드 대조

- `src/engine/scalping_feature_packet.py`: 감사 필드 helper는 존재하나 작업 8 전용 sent 로그 3종은 없음
- `src/engine/ai_engine.py`: 정량형 수급 피처 문자열에 작업 8 핵심값 3종 포함
- `src/engine/ai_engine_openai_v2.py`: OpenAI 경로에도 작업 8 핵심값 3종 포함
- `src/engine/sniper_state_handlers.py`: HOLDING 경로에서 hybrid override 전용 로그 필드 미확인

### 실행 검증

```bash
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scalping_feature_packet.py src/tests/test_ai_engine_openai_v2_audit_fields.py
```

결과:

- `4 passed, 1 warning in 4.94s`
- 경고: `pandas_ta`의 `mode.copy_on_write` deprecation warning 1건

```bash
PYTHONPATH=. .venv/bin/python -m py_compile src/engine/scalping_feature_packet.py src/engine/ai_engine.py src/engine/ai_engine_openai_v2.py src/engine/sniper_state_handlers.py
```

결과:

- `exit code 0`

## 참고 문서

- [2026-04-19-stage2-todo-checklist.md](./2026-04-19-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-18-nextweek-validation-axis-table-audited.md](./2026-04-18-nextweek-validation-axis-table-audited.md)
