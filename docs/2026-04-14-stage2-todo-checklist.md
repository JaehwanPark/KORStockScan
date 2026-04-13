# 2026-04-14 Stage 2 To-Do Checklist

## 목적

- `2026-04-13` 장후 판정을 `2026-04-14` 운영 체크리스트로 승격한다.
- 최우선은 `RELAX-LATENCY` 원격 강화 관찰의 반복 재현성 확인이다.
- `RELAX-DYNSTR`는 `2026-04-14 장후`에 `momentum_tag` 1축과 롤백 가드를 확정하고, `2026-04-15 08:30`까지 원격 canary를 시작한다.
- `RELAX-OVERBOUGHT`는 실전 재오픈이 아니라 `표본 누적`만 진행한다.
- `관찰 축 추가`는 여기서 끝낸다. `2026-04-14 장후`에는 `반영 / 보류+단일축 전환 / 관찰 종료` 중 하나로 결론내고, `2026-04-15 장전`에는 바로 착수한다.
- `기존 관찰축`은 더 많은 분석을 위한 입력이 아니라, `2026-04-14 장후 개선 결론`과 `2026-04-15 장중 지속 점검`을 위한 검증축으로만 사용한다.
- `계측 완료 + 실전반영 확신도 50% 이상`인 축은 같은 주 canary 착수를 기본값으로 한다. 착수하지 않으면 장후 문서에 보류 사유를 명시한다.
- 장후 결론은 `상태 요약`이 아니라 `날짜 + 액션 + 실행시각` 형식으로 남긴다.

## 2026-04-13 장후 승격 요약

- `RELAX-LATENCY`: `강화 유지`
  - `submitted_stocks=0` 유지라 즉시 확대 근거는 없지만, `quote_stale=False` 축을 포함한 `latency_danger_reasons` 분해와 `remote_v2` 관찰은 계속 유효하다.
- `RELAX-DYNSTR`: `유지 + 재설계`
  - `below_window_buy_value / below_buy_ratio / below_strength_base` 분해가 가능한 로그는 확보됐고, `2026-04-15 08:30` 원격 canary용 `momentum_tag` 1축을 고를 준비가 됐다.
- `RELAX-OVERBOUGHT`: `유지`
  - `blocked_overbought=20` 수준으로 표본이 누적돼 실전 완화 재오픈 근거는 없다.
- 체결 품질:
  - `entered_rows=1`, `completed_trades=1`, `holding_events=0`
  - 신규 `submitted/holding_started` 전환이 없어 `full fill / partial fill` 해석은 추가 표본이 필요하다.
- live hard stop taxonomy:
  - `hard_time_stop_shadow`는 여전히 shadow-only로 유지한다.
  - live exit는 `scalp_preset_hard_stop_pct`, `protect_hard_stop`, `scalp_hard_stop_pct`를 분리해서 본다.
- 원격 비교검증:
  - `2026-04-13 15:46:39` 자동 비교에서 `Performance Tuning`, `Entry Pipeline Flow`가 `remote_error`였다.
  - 따라서 `2026-04-14`에는 API 비교만으로 닫지 말고 snapshot 기준 재점검이 필요하다.

## 장전 체크리스트 (08:00~09:00)

- [ ] `2026-04-13` 장후 판정이 원격/본서버 설정에 의도치 않게 번진 축이 없는지 확인
- [ ] `RELAX-LATENCY` 관찰 기준을 `quote_stale=False`, `latency_danger_reasons`, `expired_armed` 중심으로 재고정
- [ ] `GitHub Project -> Google Calendar` / `Sync Docs Backlog To GitHub Project` 마지막 실행 상태 확인
- [ ] 전일 `remote_error` 난 `Performance Tuning` / `Entry Pipeline Flow`를 snapshot 기준 재점검할 경로 확인
- [ ] `신규 관찰축 추가 금지`, `개선 먼저`, `기존 축은 개선 후 점검용` 원칙을 오늘 작업지시로 재고정
- [ ] `계측 완료 + 확신도 50% 이상 = 같은 주 canary 착수` 원칙을 오늘 작업지시로 재고정
- [ ] `RELAX-DYNSTR` `2026-04-15 08:30` 원격 canary에 쓸 `momentum_tag` 선정 경로와 환경 설정 경로 확인
- [ ] `partial fill min_fill_ratio` 원격 canary 설정 경로와 rollback 가드 확인

## 장중 체크리스트 (09:00~15:30)

- [ ] `RELAX-LATENCY` 반복 재현성 관찰
  - `AI BUY -> entry_armed -> budget_pass -> submitted` 퍼널 재확인
  - `quote_stale=False latency_block`와 `expired_armed`를 분리 기록
  - `latency_danger_reasons` 상위 사유 1~3개가 유지되는지 본다
- [ ] 체결 품질 관찰
  - `full fill / partial fill`을 분리 기록
  - `preset_exit_sync_mismatch` 여부를 함께 본다
  - `partial fill min_fill_ratio` 원격 canary에 바로 쓸 수 있을 정도로 `min_fill_ratio` 대표 분포를 확인한다
- [ ] `RELAX-DYNSTR` 1축 착수용 `momentum_tag` 확정 관찰
  - `below_window_buy_value / below_buy_ratio / below_strength_base`를 `momentum_tag / threshold_profile`별로 계속 분리 기록
  - `missed_winner` 빈도가 가장 높은 `momentum_tag` 1개를 장후에 확정할 근거만 확보한다
- [ ] `RELAX-OVERBOUGHT` 표본 누적
  - `blocked_overbought`가 missed-winner와 직접 연결되는지 계속 분리 기록
- [ ] `expired_armed` 처리 설계용 대표 표본 고정
  - `latency_block`과 별도 누수 경로로 읽을 대표 케이스와 재진입 허용 후보 조건을 메모한다
- [ ] live hard stop taxonomy 관찰
  - `scalp_preset_hard_stop_pct / protect_hard_stop / scalp_hard_stop_pct / hard_time_stop_shadow` 표본 여부를 계속 기록
- [ ] `AI overlap audit`를 `selective override` 착수 입력으로 정리
  - `blocked_stage / momentum_tag / threshold_profile` 교차표가 `2026-04-16` 설계 착수에 바로 쓰일 수준인지 확인한다
- [ ] 원격서버 비교검증
  - API 비교가 `remote_error`이면 `trade_review / performance_tuning / post_sell_feedback / entry_pipeline_flow`를 snapshot 기준으로 다시 대조한다
  - 비교 결과는 `safe metric`, `fetch 재현성`, `원인 설명 가능 여부` 기준으로 짧게 메모한다
- [ ] 장후 개선 결론 준비
  - 신규 가설 발굴이 아니라 `RELAX-LATENCY 반영/보류`, `RELAX-DYNSTR 1축 착수`, `partial fill min_fill_ratio canary`, `expired_armed 설계`를 결정할 만큼만 기존 관찰축을 점검한다

## 장후 체크리스트 (15:30~)

- [ ] `RELAX-LATENCY` 운영서버 승격 가능/불가 1차 결론
- [ ] `RELAX-LATENCY` 운영서버 승격 가능/불가 최종 결론
- [ ] 체결 품질 표본이 생기면 `full fill / partial fill / preset_exit_sync_mismatch`까지 포함해 재판정
- [ ] `RELAX-DYNSTR` `momentum_tag` 1축 원격 canary 설정값 확정 (`2026-04-15 08:30` 실행용)
- [ ] `partial fill min_fill_ratio` 원격 canary 설정값 확정 (`기본값/예외/롤백가드` 포함)
- [ ] `expired_armed` 처리 로직 설계 범위와 `2026-04-15 장후` 완료 기준 확정
- [ ] `AI overlap audit` 기반 `selective override` 설계 착수일을 `2026-04-16`로 고정
- [ ] `AIPrompt P1` 착수 범위 확정
  - `작업 4 WATCHING 75 정합화 원격 canary`, `작업 5 WATCHING/HOLDING 프롬프트 물리 분리`의 write scope / rollback 가드 / 비교지표를 오늘 확정한다
- [ ] `AIPrompt 작업 8 감사용 핵심값 3종 투입`은 오늘 같은 날 착수
  - 미착수 시 `사유 + 다음 실행시각`을 장후 결론에 남긴다
- [ ] 오늘 가능한 `AIPrompt 작업 4/5`는 같은 날 구현 착수
  - 미착수 시 `사유 + 다음 실행시각`을 장후 결론에 남긴다
- [ ] `post-sell` 지표 기준 `원격 1축 매도시점 canary` 재후보화
- [ ] `2026-04-15` 장전 반영/착수 항목과 `2026-04-16` 후속 설계 착수 항목을 별도 체크리스트로 승격
- [ ] 원격 비교검증을 snapshot 기준으로 닫고 `remote_error` 원인을 설명 가능하게 정리
- [ ] 장후 결론을 `날짜 + 액션 + 실행시각` 형식으로 기록
- [ ] `2026-04-15 장중 지속 점검용 관찰축`만 남기고, `신규 관찰축 추가`는 명시적으로 중단

## 참고 문서

- [2026-04-13-stage2-todo-checklist.md](./2026-04-13-stage2-todo-checklist.md)
- [2026-04-11-scalping-ai-prompt-coding-instructions.md](./2026-04-11-scalping-ai-prompt-coding-instructions.md)
- [2026-04-10-scalping-ai-coding-instructions.md](./2026-04-10-scalping-ai-coding-instructions.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-14-audit-reflection-strong-directive.md](./2026-04-14-audit-reflection-strong-directive.md)
