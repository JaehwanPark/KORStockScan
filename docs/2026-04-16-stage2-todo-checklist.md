# 2026-04-16 Stage 2 To-Do Checklist

## 목적

- 오늘 배치는 `canary/shadow/test`가 아니라 **운영반영 배치**로 수행한다.
- `scalping_ai_routing_instruction_integrated.md` 작업지시를 장시작 전에 실전 로직에 직접 반영한다.
- 원격 적용 범위는 스캘핑 매매 전 구간 + 조건검색 포함으로 고정한다.
- 모델별 A/B 테스트는 오늘 운영반영과 분리해 별도 시나리오로 후속 검토한다.

## 장전 체크리스트 (08:00~08:50)

- [x] `[Checklist0416] 메인 스캘핑 라우팅 운영반영 (canary 미사용)` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`)
  - 판정 기준: 장시작 전 메인 경로가 작업지시서 기준 로직으로 반영 완료
  - 근거: 금일 배치는 테스트축이 아닌 운영반영
  - 다음 액션: 반영 커밋/설정/기동 로그를 운영기록에 남김
- [x] `[Checklist0416] 메인 스캘핑 모델/입력스키마 운영반영` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:35`)
  - 판정 기준: 스캘핑 경로 입력 스키마 개선이 실전 호출 경로에 반영
  - 근거: 판단 일관성/지연 개선 목적의 즉시 반영
  - 다음 액션: 장중 지표로 적용 효과 확인
- [x] `[Checklist0416] 원격 스캘핑+조건검색 tier1 flash-lite 적용` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:35~08:45`)
  - 판정 기준: 원격에서 스캘핑 및 조건검색이 지정 모델 티어로 동작
  - 근거: 사용자 범위 확정(조건검색 포함)
  - 다음 액션: 호출 모델 로그/리포트에서 적용 확인
- [x] `[Checklist0416] scalping_exit 액션스키마 분리의 기존 튜닝 포함 여부 판정` (`Due: 2026-04-16`, `Slot: PREOPEN`, `TimeWindow: 08:45~08:50`)
  - 판정 기준: 포함이면 후속 분리, 미포함이면 plan 검토항목 유지
  - 근거: 기존 튜닝 문서 명시성 점검 필요
  - 다음 액션: 장후 계획 항목에 확정 반영

### PREOPEN 판정/근거/다음 액션 (2026-04-16 반영)

1. 판정: 메인 스캘핑 라우팅 운영반영 완료 (canary 미사용)
- 근거: `logs/bot_history.log:1048`에 `role=main (main_scalping_openai=ON)` 확인.
- 다음 액션: 장중 퍼널/체결품질 중심 관찰 유지.

2. 판정: 메인 스캘핑 모델/입력스키마 운영반영 완료
- 근거: `logs/bot_history.log:1042~1043`에서 스캘핑 OpenAI `gpt-5.4-nano` 고정 확인, `src/engine/ai_engine_openai_v2.py:753~763` task_type 주입 확인.
- 다음 액션: 장중 `ai_prompt_type`, parse/fallback 지표 수집.

3. 판정: 원격 스캘핑+조건검색 tier1 flash-lite 적용 완료
- 근거: 라우터 구조상 remote는 Gemini 경로 유지(`src/engine/runtime_ai_router.py:72~81`), 원격 운영반영 결과 문서 반영 완료.
- 다음 액션: POSTCLOSE에 원격 비교지표(퍼널/blocker/체결품질) 재판정.

4. 판정: `scalping_exit` 액션스키마 완전 분리는 기존 튜닝 범위 미포함으로 판정
- 근거: 작업지시서에 `현재 청산 action schema가 완전히 분리되지 않음` 명시(`docs/scalping_ai_routing_instruction_integrated.md`), 금일 배치는 분리 규칙 고정/후속 판정으로 운영.
- 다음 액션: 금일 POSTCLOSE 1차 판정, 익일 PREOPEN 최종확정(분리 이행 또는 plan 유지).

5. 판정: 원격 반영 상태는 로컬과 동일 커밋으로 정렬됨
- 근거: `git rev-parse HEAD == git rev-parse @{u} == a93b690a7a1756c7e4e6ea22eec0fadbd43f42de` 확인.
- 다음 액션: 재시작 후 `loss_fallback_probe` 이벤트 발생 여부를 장중 지속 모니터링.

6. 판정: 실거래 bot(`tmux: bot`) 재시작 완료, `loss_fallback_probe`는 즉시 미검출
- 근거: `tmux` 세션 재기동 후 엔진 부팅 로그 확인, 최근 로그 grep에서 `loss_fallback_probe` 매치 없음.
- 다음 액션: 익일 PREOPEN(`08:00~09:00`)에 전일 `loss_fallback_probe` 후보율/성과 판정 후 승인 시에만 `SCALP_LOSS_FALLBACK_OBSERVE_ONLY=False` 전환.

## 장중 체크리스트 (09:00~15:30)

- [x] `운영반영 로직 정상동작 확인 (진입/보유/청산 라우팅)`
- [x] `퍼널 병목(`budget_pass -> submitted`) 재확인 및 blocker 분포 확인`
- [x] `체결품질(full/partial 분리) 및 sync mismatch 추적`
- [x] `관찰축 5: add_judgment_locked blocker 분포 추적 (종목/시간대/정체코호트)`
- [x] `Gatekeeper/holding 지연 지표 확인 (실운영 기준)`
- [x] `원격 스캘핑+조건검색 모델 적용 상태 점검`
- [x] `이상징후 발생 시 즉시 수정 또는 롤백 가드 실행`

## 장후 체크리스트 (15:30~)

- [x] `운영반영 결과 요약 작성 (거래수/퍼널/blocker/체결품질 우선)`
- [x] `COMPLETED + valid profit_rate 기준으로 손익 집계`
- [x] `full fill / partial fill 분리 성과표 기록`
- [x] `관찰축 5 결과 기록: add_blocked_lock_count_by_stock / timebucket / held_sec 코호트`
- [x] `scalping_exit 액션스키마 분리 포함여부 최종 확정 기록`
- [x] `미포함 시 차기 plan에 검토항목 고정`
- [x] `[Checklist0416] 모델별 A/B 테스트 별도 시나리오 초안 backlog 등록` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:30`)
  - 판정: 운영반영과 분리된 실험 시나리오 문서/백로그 생성 여부
  - 근거: 사용자 지시로 A/B는 별도 검토 예정
  - 다음 액션: 실험목적/샘플/중단조건/평가기준 문서화

### POSTCLOSE 판정/근거/다음 액션 (2026-04-16 15:25 KST)

1. 판정: 운영반영 로직(진입/보유/청산) 정상동작 확인.
- 근거: `trade_review_2026-04-16` 기준 `entered_rows=25`, `completed_trades=20`, `holding_events=10,731`로 진입/보유/청산 라우팅 이벤트 연속성 확인.
- 다음 액션: `open_trades=5` 잔존 포지션은 동기화 누락/지연 여부를 POSTCLOSE 재점검.

2. 판정: 퍼널 병목은 `budget_pass -> submitted` 구간에 집중.
- 근거: `entry_pipeline_flow_2026-04-16` 기준 `budget_pass_stocks=2`, `budget_pass_to_submitted_stocks=0`, `budget_pass_to_submitted_rate=0.0%`.
- 다음 액션: blocker 상위(`과열=15`, `게이트키퍼: 눌림 대기=4`, `스윙 갭상승=3`)를 2026-04-17 PREOPEN 튜닝 입력으로 고정.

3. 판정: 체결품질은 partial 편중, sync mismatch는 제한적.
- 근거: fill quality 기준 `full_fill_events=5`, `partial_fill_events=27`, `preset_exit_sync_mismatch_events=2`, `mismatch_rate=14.3%`.
- 다음 액션: full/partial 분리 표본 유지, mismatch 2건은 `preset_exit_sync_mismatch` 원인 라벨로 익일 재분석.

4. 판정: COMPLETED + valid profit_rate 기준 손익 집계 완료.
- 근거: `completed_trades=20`, `valid_profit_rate_count=20`, `valid_profit_rate_avg=-0.355%`, `valid_profit_rate_sum=-7.10`.
- 다음 액션: NULL/미완료 제외 규칙 유지, 익일 비교도 동일 필터로만 수행.

5. 판정: 관찰축 5(add_judgment_locked) 결과 기록 완료.
- 근거: `add_blocked_lock_2026-04-16` 기준 `total_blocked_events=1,392`, `stagnation_held_threshold_sec=600`, `stagnation_blocked_events=941`; 상위 종목 `올릭스(416)`, `롯데쇼핑(397)`, `파라다이스(194)`.
- 다음 액션: timebucket/종목/held_sec 코호트 기준으로 2026-04-17 POSTCLOSE 추적 연장.

6. 판정: Gatekeeper/HOLDING 지연 지표 확인 완료(실운영 기준).
- 근거: `performance_tuning_2026-04-16` 기준 `holding_review_ms_avg=1426.14`, `holding_review_ms_p95=2468`, `gatekeeper_eval_ms_avg=12541.42`, `gatekeeper_eval_ms_p95=27408`.
- 다음 액션: `gatekeeper_eval_ms_p95` 고값 구간은 timeout/재시도 정책 분리 검토 대상 유지.

7. 판정: 원격 스캘핑+조건검색 적용 상태 점검 완료(비교 가능 구간 기준).
- 근거: `server_comparison_2026-04-16` 기준 `trade_review=ok`, `post_sell_feedback=ok`, 다만 `performance_tuning/entry_pipeline_flow`는 `remote_error(timeout)`.
- 다음 액션: remote timeout은 운영 변경 없이 관측 지속, 2026-04-17 PREOPEN에 재비교.

8. 판정: 이상징후 즉시 수정/롤백 가드는 미발동(유지).
- 근거: 금일 운영 로그에서 거래 엔진 즉시 롤백 트리거 조건(주문 불가/상태붕괴) 미검출; remote 비교 timeout은 외부 응답 지연 이슈로 분리.
- 다음 액션: 실거래 경로는 현행 유지, timeout 급증 시에만 canary 축 재격리.

9. 판정: `scalping_exit` 액션스키마 완전 분리는 금일 운영반영 범위 미포함으로 최종 확정.
- 근거: 금일 배치의 실전 반영은 라우팅/입력 정렬 중심이며, HOLDING action schema 완전 분리는 별도 작업축으로 남아 있음.
- 다음 액션: 미포함 검토항목을 2026-04-17 PREOPEN backlog로 고정(아래 익일 체크리스트 + A/B 시나리오 초안 문서 연동).

## 익일 착수 체크리스트 (2026-04-17 PREOPEN)

- [x] `[Checklist0417] recommendation_history.nxt 필드 정리 작업 착수` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:30~09:00`) (`실행: 2026-04-16 12:10 KST`)
  - 판정 기준: `nxt` 필드의 실사용 경로/대체필드/마이그레이션 순서를 확정하고 구현 착수
  - 근거: `nxt`는 NXT거래 여부/수량 의미와 불일치하며, 현재 실데이터 활용도가 낮음
  - 다음 액션: 1) 대체 필드 도입(명시적 네이밍) 2) 호환 read/write 3) 참조 제거 및 drop 순으로 진행
  - 실행 메모: 1단계 착수 완료 (`entry_armed_at_epoch` 추가, `sniper_s15_fast_track` read/write 호환 반영, `nxt` fallback 유지)
- [ ] `[Checklist0417] scalping_exit 액션스키마 분리 여부 재판정 및 실행순서 확정` (`Due: 2026-04-17`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:20`)
  - 판정 기준: `HOLDING` action schema(`HOLD/SELL/FORCE_EXIT`) 분리 적용 여부와 롤백 가드 포함 실행순서를 확정
  - 근거: 2026-04-16 운영반영에는 완전 분리가 미포함이므로 차기 plan 고정 필요
  - 다음 액션: 분리 포함 시 shadow-only 선적용, 미포함 시 계획문서에 보류사유/재판정 시각 고정
  - 실행 게이트 확인(2026-04-16 15:34 KST): `TimeWindow=2026-04-17 08:00~08:20 KST` 미도래로 미실행 유지 (체크박스 보류)

## 참고 문서

- [2026-04-16-scalping-ai-routing-senior-architect-review-result.md](./2026-04-16-scalping-ai-routing-senior-architect-review-result.md)
- [scalping_ai_routing_instruction_integrated.md](./scalping_ai_routing_instruction_integrated.md)
- [2026-04-15-performance-review-followup.md](./2026-04-15-performance-review-followup.md)

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-16 15:49:38`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-16.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`6`
  - holding_events local=10843 remote=0 delta=-10843.0; all_rows local=210 remote=221 delta=11.0; expired_rows local=174 remote=183 delta=9.0
- `Performance Tuning`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=16 remote=28 delta=12.0; evaluated_candidates local=16 remote=28 delta=12.0
- `Entry Pipeline Flow`: status=`remote_error`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->
