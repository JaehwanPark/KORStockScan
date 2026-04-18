# 2026-04-18 Stage 2 To-Do Checklist

## 목적

- 휴일(`2026-04-18`)로 인한 비거래일 운영 원칙에 따라 실행 항목을 `2026-04-17 POSTCLOSE` 또는 `2026-04-20`으로 재배치한다.

## 휴일 이관 처리

- [x] `[HolidayReassign0418] AIPrompt 작업 9 정량형 수급 피처 이식 1차` 착수 항목 이관 완료 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:45`, `Track: AIPrompt`)
  - 판정: 오늘 장후 우선 수행 대상으로 이관
  - 근거: 구현 착수 여부는 비거래일 대기 없이 판정 가능
  - 다음 액션: 미완료 시 `2026-04-20 PREOPEN 08:00~08:10` 재판정
  - 실행 메모 (`2026-04-18 10:27 KST`): `착수`로 종료. `src/engine/scalping_feature_packet.py` 공통 helper를 추가해 Gemini `_format_market_data()`와 OpenAI v2 `_extract_scalping_features()`가 같은 정량형 수급 피처 패킷을 공유하도록 반영했다. 추가로 OpenAI `analyze_target()` 반환에도 `scalp_feature_packet_version`, `tick_acceleration_ratio_sent`, `same_price_buy_absorption_sent`, `large_sell_print_detected_sent`, `ask_depth_ratio_sent`를 주입해 메인 서버 스캘핑 라우트에서 감리 로그가 직접 남도록 맞췄다.
  - 실행 메모 (`2026-04-18 10:56 KST`): 원격 `windy80xyt@songstockscan.ddns.net`에도 `src/engine/scalping_feature_packet.py`, `src/engine/ai_engine.py`, `src/engine/ai_engine_openai_v2.py`를 동기화했다. 원격 `.venv` `py_compile` 검증 통과, `bot_main.py` 실행 프로세스는 비활성 상태로 재기동 대상 없음.
- [x] `[HolidayReassign0418] 작업 6/7 보류 항목 사유+다음 실행시각` 이관 완료 (`Due: 2026-04-17`, `Slot: POSTCLOSE`, `TimeWindow: 15:45~16:00`, `Track: AIPrompt`)
  - 판정: 오늘 장후 문서 갱신 대상으로 이관
  - 근거: 보류 사유/다음 시각 기록은 당일 문서 작업으로 처리 가능
  - 다음 액션: 미완료 시 `2026-04-20 POSTCLOSE 15:45~16:00` 재기록
  - 실행 메모 (`2026-04-18 10:21 KST`): `보류 유지`로 재기록. 작업 6(`P2 HOLDING 포지션 컨텍스트 주입`)와 작업 7(`WATCHING 선통과 조건 문맥 주입`)은 `HOLDING action schema shadow-only` 착수 범위와 충돌하지 않게 다음 영업일 장후 슬롯에서 함께 재판정한다. 다음 실행시각은 `2026-04-20 POSTCLOSE 15:45~16:00 KST`로 유지.

## 참고 문서

- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
