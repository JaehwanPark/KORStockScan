# 2026-04-15 구현 결과서: SCALP AI EXIT AVGDOWN

> 기준 문서: `docs/workorder-scalp-ai-exit-avgdown.md`  
> 작성일: `2026-04-15`  
> 범위: 스캘핑 AI 하방카운트 도달 시 1회 AVG_DOWN 후 보유 재진입

## 1. 판정

- 판정: **요구사항 R1~R7 구현 완료 (코드 + 테스트 검증 완료)**  
- 배포 판정: **기본 OFF 상태 유지, canary 전용 활성화 권고**

## 2. 근거

### 2.1 코드 반영

| 요구사항 | 반영 내용 | 파일 |
| --- | --- | --- |
| R1 | `SCALP_AI_EXIT_AVGDOWN_ENABLED` 상수 추가 (기본 `False`) | `src/utils/constants.py` |
| R2/R3/R4 | `scalp_ai_early_exit` 분기에서 토글 ON + 미소진 시 1회 AVG_DOWN 우선, 성공 시 `ai_low_score_loss_hits=0` 초기화 및 보유 유지 | `src/engine/sniper_state_handlers.py` |
| R5 | AVG_DOWN 주문 실패 시 기존 `scalp_ai_early_exit`로 fallback | `src/engine/sniper_state_handlers.py` |
| R6 | 기존 `SCALPING_ENABLE_AVG_DOWN` 게이트와 무관하게 AI카운트 경로에서 직접 `_process_scale_in_action()` 호출 | `src/engine/sniper_state_handlers.py` |
| R7 | `HOLDING_PIPELINE stage=scalp_ai_exit_avgdown` 로그 및 fallback/소진 사유 로그 반영 | `src/engine/sniper_state_handlers.py` |

### 2.2 테스트/검증

- 실행 명령:
  - `./.venv/bin/python -m pytest -q src/tests/test_sniper_scale_in.py -k "ai_exit_avgdown or ai_early_exit_requires_consecutive_low_score_hits"`
  - `./.venv/bin/python -m py_compile src/engine/sniper_state_handlers.py src/utils/constants.py src/tests/test_sniper_scale_in.py`
- 결과:
  - `5 passed, 52 deselected`
  - `py_compile` 오류 없음

### 2.3 신규 테스트 케이스

- `test_scalping_ai_exit_avgdown_toggle_off_keeps_original_exit`
- `test_scalping_ai_exit_avgdown_first_hit_success_resets_hits`
- `test_scalping_ai_exit_avgdown_first_hit_failure_falls_back_to_sell`
- `test_scalping_ai_exit_avgdown_done_stock_sells_without_retry`

## 3. 리스크/운영 메모

- `calc_scale_in_qty()` 결과가 0이면 신규 경로도 fallback으로 즉시 손절한다.  
- `SCALPING_MAX_AVG_DOWN_COUNT=0` 환경에서는 AI카운트 기반 AVG_DOWN 성공률이 낮을 수 있다.
- 따라서 canary 시점에는 `SCALPING_MAX_AVG_DOWN_COUNT >= 1` 확인이 필요하다.

## 4. 다음 액션

- [ ] `SCALP_AI_EXIT_AVGDOWN_ENABLED` canary 실행 계획 확정 | Status=Todo | Due=2026-04-16 | Slot=PREOPEN | Track=SCALP_EXIT
- [ ] canary 1일차 결과(트리거 수, 성공/실패, fallback 비중, 체결 후 재손절률) 장후 정리 | Status=Todo | Due=2026-04-16 | Slot=POSTCLOSE | Track=SCALP_EXIT

