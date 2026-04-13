# 2026-04-09 Stage 2 To-Do Checklist

## 목적

- 최종 목적은 보수적 `손실 억제`가 아니라 `기대값/순이익 극대화`다.
- 현재 단계는 그 목표를 위한 `1단계: 음수 leakage 제거`에 해당한다.
- `2026-04-08` 미수행 항목을 누락 없이 이월해 장전/장중/장후 순서로 실행한다.
- `종목 선정`과 `진입/탈출 실패`를 분리 추적해, 튜닝 우선순위를 명확히 유지한다.

## 접근 원칙

- 접근 방향은 `보수화`가 아니라 `공격적 기대값 개선`이다.
- 다만 현재는 `fallback 전패`, `scalp_ai_early_exit` 손실 편중처럼 음수 기여가 큰 경로를 먼저 제거한다.
- `한 번에 한 축 canary`, `shadow-only`, `즉시 롤백 가드`는 보수적 철학이 아니라 `원인 귀속 정확도`와 `실전 리스크 통제`를 위한 운영 규율이다.
- 따라서 오늘의 튜닝은 `거래를 줄이는 것` 자체가 목적이 아니라 `저품질 음수 경로를 줄이고, 이후 양수 경로 확대 단계로 넘어가기 위한 정리 작업`이다.

## 전일(2026-04-08) 장마감 요약 전제

- 스캘핑 완료 `12건`, 승률 `25.0%(3/12)`, 실현손익 `-66,367원`
- `fallback` 진입 `5건` 전패, 실현손익 `-27,742원`
- `scalp_ai_early_exit` 종료 `4건` 전부 손실
- 해석: 종목 선정보다 `진입 타이밍/출구 규칙`에서 발생하는 `음수 leakage` 제거가 우선

## 트리거 규칙

- `[자동 실행]`: 예약된 cron 또는 코드가 지정 시각에 자동 수행
- `[내 지시 필요]`: 해당 시점에 나에게 요청해야 판단/기록/결론 작성 수행
- `[내 승인 필요]`: 텔레그램 명령 또는 명시적 요청으로 승인/거절해야 실제 상태가 바뀜
- `[조건 발생 시 즉시]`: 롤백/긴급 대응처럼 조건 충족 즉시 판단이 필요한 항목
- 현재 기준 `2026-04-09 10:00 KST` 스냅샷 생성은 `[자동 실행]`이고, 그 결과 해석/문서화는 `[내 지시 필요]`다.
- `buy pause guard`는 `[자동 실행]` 후보 감지 후 `[내 승인 필요]` `/buy_pause_confirm <guard_id>` 또는 `/buy_pause_reject <guard_id>`로 처리한다.

## 2026-04-09 장전 체크리스트 (08:30~09:00)

- [x] `fallback` 전용 진입 억제 canary 1개만 적용
  - 비중 축소 또는 진입 강도 강화 중 한 가지 축만 적용
  - 적용 시각/파라미터/기대효과를 문서에 기록
  - `2026-04-09 07:51 KST` 적용
  - 코드 파라미터: `SCALP_FALLBACK_ENTRY_QTY_MULTIPLIER=0.70` (비중 축소 축만 적용)
  - 적용 위치: `sniper_state_handlers.py` fallback 주문 전송 직전 수량 canary
  - 기대효과: 동일 실패 패턴 재발 시 fallback 절대 손실총액 약 `30%` 축소
- [x] `OPEN_RECLAIM` / `SCANNER` 출구 규칙 분리 보강
  - `scalp_ai_early_exit`에서 `never_green`과 `양전환 이력 있음`을 분리
  - 포지션 태그별 적용 범위를 명시
  - `2026-04-09 07:51 KST` 적용
  - `OPEN_RECLAIM`: `scalp_open_reclaim_never_green` + `scalp_open_reclaim_retrace_exit` 분리
  - `SCANNER/fallback`: `scalp_scanner_fallback_never_green` + `scalp_scanner_fallback_retrace_exit` 분리
  - 태그별 조건: `OPEN_RECLAIM`/`SCANNER(fallback)` 각각 `never_green(peak<=0.20)` vs `양전환 이력(peak>0.20)` 분기
- [x] `exit_rule='-'` 복원 정확도 보정
  - 전일 누락 거래 우선 복원 후 `trade-review` 반영 확인
  - `2026-04-09 07:51 KST` 적용
  - `trade-review` 복원 보강: `sell_order_sent`/사유문(reason) 기반 `exit_rule` 역복원 경로 추가
  - 우선 복원 대상: `sell_completed(exit_rule='-')` 누락 케이스
- [x] Dual Persona 재활성화 조건 고정
  - `dual_persona_extra_ms_p95 <= 2500`
  - `effective_override_ratio >= 3%`
  - `samples >= 30`
  - `gatekeeper_eval_ms_p95 <= 5000`
  - `2026-04-09 07:51 KST` 적용
  - 고정 파라미터: `OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_SAMPLES=30`, `OPENAI_DUAL_PERSONA_GATEKEEPER_MIN_OVERRIDE_RATIO=3.0`, `OPENAI_DUAL_PERSONA_GATEKEEPER_MAX_EVAL_MS_P95=5000`, `OPENAI_DUAL_PERSONA_MAX_EXTRA_MS=2500`
  - `performance-tuning` watch item에 `Gatekeeper 듀얼 재활성화 조건` 카드 추가(충족/미충족 자동 표시)
- [x] 공통 hard time stop은 shadow 평가만 수행하도록 고정
  - 실전 반영 없이 후보안 영향 추정 결과를 먼저 축적
  - `2026-04-09 07:51 KST` 적용
  - 고정 파라미터: `SCALP_COMMON_HARD_TIME_STOP_SHADOW_ONLY=True`, `SCALP_COMMON_HARD_TIME_STOP_SHADOW_MINUTES=(3,5,7)`
  - 실행 동작: 청산 트리거 대신 `hard_time_stop_shadow` 이벤트만 기록(실전 주문 영향 0)

## 2026-04-09 장중 체크리스트 (09:00~15:30)

- [ ] `curr`, `spread` 완화 후보 분석용 기준 정리
  - `holding_sig_deltas`를 `시간대/position_tag/entry_mode/종목군`으로 분해하는 집계 축 확정
  - `1틱 변화 허용` 후보와 `현행 유지` 후보를 같은 포맷으로 비교표 작성
- [ ] canary 실시간 모니터링(적용 후 `30~60분`)
  - `fallback` 승률/평균손실/손실총액 변화 기록
  - `entry_mode / position_tag / exit_rule / holding_seconds bucket` 분리 집계 유지
  - `AI BUY -> entry_armed -> budget_pass -> order_bundle_submitted` 퍼널을 함께 기록해, `손익 표본 0`이 `기회 부재`인지 `진입 실패 누적`인지 먼저 분리한다
  - `missed_entry_counterfactual` 스냅샷으로 `AI BUY 후 미진입` 후보의 `5분/10분` 가상 손익(`missed winner / avoided loser / neutral`)도 함께 본다
  - 트리거: `[자동 실행]` `09:30~11:00 KST` 5분 간격 `buy pause guard` 평가
  - 트리거: `[자동 실행]` `2026-04-09 10:00 KST` 스냅샷 생성
  - 트리거: `[자동 실행]` `2026-04-09 12:00 KST` 스냅샷 생성
  - 트리거: `[내 지시 필요]` `09:30~10:00 KST` 판단기준표 기록, 또는 `10:00` 이후 스냅샷 기준 1차 결론 기록
  - 트리거: `[내 지시 필요]` `12:00` 이후 스냅샷 기준 1차 실질 해석 기록
  - 트리거: `[내 승인 필요]` guard 경보 수신 시 `/buy_pause_confirm <guard_id>` 또는 `/buy_pause_reject <guard_id>`
  - 트리거: `[프롬프트 백업]` `buy pause 실행해줘` / `buy resume 실행해줘` / `buy pause 상태 보여줘`
- [ ] 스윙 Gatekeeper missed case 표본 채집
  - `blocked_gatekeeper_reject` 후 추세가 좋았던 표본 후보를 장중 마킹
  - 동시 구간 `dual_persona_shadow` 결론(`ALLOW`/기타) 교차 메모
- [ ] `AI WAIT/latency` missed case 표본 채집
  - `327260 RF머티리얼즈`, `037440 희림`처럼 `종목선정 적중` 후 `gatekeeper reject`가 아니라 `AI WAIT`, `blocked_ai_score`, `AI BUY 후 latency_block`으로 놓친 사례를 별도 마킹
  - `스윙 gatekeeper miss`와 섞지 않고 `AI score / threshold / cooldown / latency_state`를 따로 기록
- [ ] `AI BUY 후 미진입` 퍼널 차단 사례 채집
  - `삼성E&A(028050)`, `대모(317850)`, `비츠로셀(082920)`, `APS(054620)`처럼 `AI BUY` 이후에도 `order_bundle_submitted=0`으로 끝난 사례를 별도 마킹
  - `latency_block`, `blocked_liquidity`, `first_ai_wait`, `blocked_ai_score`를 구분해 `canary 표본 부족의 원인`으로 함께 기록
  - `BUY 판정 전체 universe` 기준 `confidence tier(A/B/C)`도 함께 기록해 explicit `target_buy_price` 표본과 proxy 표본을 분리한다

### 09:30~10:00 판단기준표 기록 (`2026-04-09 09:55 KST` 중간 기록)

| 판단 항목 | 기준 | 09:55 KST 관측치 | 중간 판단 | 10:00 이후 액션 |
| --- | --- | --- | --- | --- |
| `fallback` canary 즉시 악화 여부 | `fallback` 완료 거래 기준 `승률/평균손실/손실총액` 급악화 시 롤백 검토 | `09:30~09:55` 구간 `fallback order_bundle_submitted=0`, `fallback sell_completed=0` 확인. 종료 표본이 아직 없어 손익 판정 불가 | `표본 부족`, 즉시 롤백 근거 없음 | `10:00` 스냅샷과 장후 종료 거래 누적 후 재판단 |
| `BUY 후 미진입` 퍼널 차단 여부 | `ai_confirmed(BUY)`가 있는데 `order_bundle_submitted=0`이면 canary 해석 전 원인 분리 필요 | `09:30~09:55` 기준 강표본은 아직 미확정 | `동반 체크 필요`, 손익 표본 0의 해석 보류 | `10:00` 이후 `AI BUY -> 주문전 차단` 종목을 별도 표본으로 분리 |
| `buy pause guard` 경보 여부 | guard 후보 생성 또는 pending state 발생 시 즉시 승인/거절 판단 | `data/runtime/buy_pause_guard_state.json` 미생성, pending guard 없음 | `경보 없음`, buy pause 불필요 | `10:00` 전후 자동 평가 지속, 경보 수신 시 텔레그램 승인/거절 |
| `AI threshold miss` 표본 | `AI WAIT` / `blocked_ai_score` 반복 종목 별도 분리 | `327260 RF머티리얼즈`: `09:32:57`, `09:38:11`, `09:46:14` `ai_confirmed=WAIT`, `blocked_ai_score=2회` | `AI threshold miss` 표본으로 유지 | 장후 요약표에 `AI threshold/cooldown` 축으로 별도 정리 |
| `latency guard miss` 표본 | `AI BUY -> entry_armed -> budget_pass -> latency_block(REJECT_DANGER)` 반복 시 별도 분리 | `037440 희림`: `09:30~09:55` 구간 `entry_armed=6`, `budget_pass=70`, `latency_block=70`, `spread_ratio≈0.0081~0.0098`, `ws_age_ms≈152~336` | `latency guard miss` 강표본, 우선 분석 대상 | 장후 요약표에 `spread_ratio / ws_age_ms / ws_jitter_ms` 분포 포함 |
| 실행/체결 이상 징후 | 주문 후 체결 무시, buy pause 오판, hard stop 실전 오작동 여부 | `09:30~09:55` 구간 신규 `EXEC_IGNORED`, `hard_time_stop_shadow`, `fallback sell_completed` 미관측 | 즉시 운영 위험 신호 없음 | `10:00` 스냅샷 시 이상 이벤트 재확인 |

- 중간 결론:
  - `fallback` canary는 아직 `손익 표본 부족`이라 `유지/롤백` 판단을 내리기 이르다.
  - 대신 `037440 희림`은 `latency guard miss`, `327260 RF머티리얼즈`는 `AI threshold miss`가 더 선명해져 `AI WAIT/latency` 축 분리의 필요성이 강화됐다.
  - 따라서 `10:00` 전 최우선 운영 판단은 `fallback 롤백`이 아니라 `표본 확보 지속 + missed case 분리 기록 유지`다.

### 10:00 스냅샷 기준 1차 결론 (`2026-04-09 10:02 KST` 수동 실행본)

| 판단 항목 | 10:00 스냅샷 관측치 | 1차 결론 | 후속 액션 |
| --- | --- | --- | --- |
| `fallback` canary 손익 표본 | `completed_fallback_trades=0`, `fallback_realized_pnl_krw=0`, `sample_ready=false` | `표본 부족`, `유지/강화/롤백` 판단 보류 | 장후 종료 거래 누적 후 당일 결론 작성 |
| `BUY 후 미진입` 퍼널 상태 | `삼성E&A(028050)=AI BUY -> entry_armed -> budget_pass -> latency_block`, `대모(317850)=AI BUY/strength pass 후 blocked_liquidity`, 둘 다 `order_bundle_submitted=0` | `손익 표본 0`은 단순 기회 부족이 아니라 `주문전 차단 누적` 영향도 함께 본다 | 장후 결론에서 `손익 canary`와 별도 축으로 `퍼널 차단률` 기록 |
| `buy pause guard` 경보 | `should_alert=false`, `triggered_flag_names=[]`, `pending guard 없음` | `buy pause 불필요` | `09:30~11:00` 자동 guard 평가 지속 |
| trade review / performance snapshot | 두 스냅샷 모두 요약 집계 비어 있음 | `10:00` 시점 완료 거래 자체가 거의 없음 | 장후 스냅샷/리포트에서 재확인 |
| post-sell feedback | `evaluated_candidates=0` | 매도 후속평가 대상 없음 | 장후 매도 누적 시 재생성 |
| missed case 분리 축 | `037440 희림=latency guard miss`, `327260 RF머티리얼즈=AI threshold miss(+일부 latency miss)`, `028050 삼성E&A=AI BUY 후 latency miss`, `317850 대모=AI BUY 후 liquidity miss`, `082920 비츠로셀=AI BUY 후 latency miss`, `054620 APS=AI BUY 후 latency miss`, `004020 현대제철=AI BUY 후 latency miss`, `098070 한텍=AI BUY 후 latency miss`, `259630 엠플러스=AI BUY 후 overbought miss` | 오늘 장중 핵심 분석축은 `fallback 롤백`보다 `AI WAIT/latency/liquidity/overbought miss` 분리 정밀화 | 장후 요약표에 아홉 종목 우선 반영 |

- 1차 결론:
  - `10:00` 기준으로는 `fallback` canary를 롤백하거나 강화할 근거가 아직 없다.
  - 다만 `손익 표본 0`을 그대로 `잠잠함`으로 읽으면 안 되고, `AI BUY 후 미진입` 퍼널 차단이 동반됐는지 먼저 봐야 한다.
  - 즉시 운영 판단은 `canary 유지 + buy pause 미발동 + 장후 종료 표본 대기`이되, 해석 단위는 `손익 표본`과 별도로 `BUY 후 미진입 차단률`을 함께 본다가 맞다.
  - 오늘 가장 선명한 튜닝 후보는 `스윙 gatekeeper`가 아니라 `AI WAIT/latency/liquidity/overbought miss` 축이며, `희림`, `RF머티리얼즈`, `삼성E&A`, `대모`, `비츠로셀`, `APS`, `현대제철`, `한텍`, `엠플러스`를 첫 표본으로 유지한다.
- 운영 메모:
  - 원래 `10:00` 자동 크론은 `python -c` 안의 `strftime('%Y-%m-%d')`가 cron의 `%` 해석에 걸려 실패했다.
  - 동일 문제 재발 방지를 위해 이후 `10:00` 스냅샷 예약은 `python -m src.engine.run_monitor_snapshot` 래퍼 기준으로만 등록한다.

### 장중 현황 업데이트 (`2026-04-09 10:46 KST`)

| 판단 항목 | 최신 관측치 | 현재 해석 | 후속 액션 |
| --- | --- | --- | --- |
| `fallback` canary 실체결 표본 | `393890 더블유씨피`: `AI BUY 85 -> entry_armed -> budget_pass(qty=55) -> fallback_qty_canary_applied(55->39) -> latency_pass(mode=fallback) -> order_bundle_submitted(requested_qty=39) -> holding_started(entry_mode=fallback, buy_qty=39) -> sell_completed(-1.22%, scalp_ai_early_exit)` | `fallback canary 정상 수행 + 실체결 표본 1건 확보`. 이번 canary의 핵심 축인 `수량 0.70 배율`이 실제 주문/체결까지 반영됨 | `12:00` 해석에 `fallback 손익 표본 1건`과 `실현손익 음수`를 반영 |
| `fallback` canary 현재 손익 현황 | 실체결 종료 표본 기준 `completed_fallback_trades=2`, `win_rate=0%`, `fallback_realized_pnl_krw<0`, `exit_rule=scalp_ai_early_exit` | 더 이상 `손익 표본 0` 상태는 아니고, 현재까지는 `음수 2건`이다. 다만 `정상 full fill`과 `부분체결`이 섞여 있어 즉시 `롤백/강화` 결론을 내리기엔 이르다 | `12:00` 스냅샷과 장후 누적 표본 기준으로 `평균손실/손실총액`과 `체결 품질`을 함께 재평가 |
| `canary 적용 정합성` | `393890 더블유씨피`: `budget_pass qty=55 -> scaled_qty=39 -> WS 체결 1주+38주 -> holding_started buy_qty=39` | canary 배율 적용 실패나 체결 불일치 징후 없음. `정상 full fill` 표본 | `trade_review`/`post_sell_feedback`에 동일 수량 기준으로 반영됐는지 장후 재확인 |
| `fallback 부분체결 표본` | `101490 에스앤에스텍`: `WAIT/threshold miss -> blocked_liquidity -> BUY 85 -> budget_pass qty=9 -> scaled_qty=7 -> BUY 1주 체결 -> 잔량 6주 취소 -> sell_completed(-0.91%, scalp_ai_early_exit)` | `fallback canary` 자체는 정상 적용됐지만, `부분체결/잔량취소`가 발생해 `체결 품질` 해석을 분리해야 한다. `미진입` 표본이 아니라 `부분체결 손절` 표본 | `12:00` 해석에서 `fallback 손익`과 별도로 `full fill vs partial fill`을 분리 기록 |
| `BUY 후 미진입` 퍼널 차단률 해석 | `더블유씨피`는 미진입이 아니라 `진입 성공` 표본으로 이동 | `손익 표본 0 = 기회 부재` 가설은 폐기. 현재는 `실체결 fallback 표본`과 `미진입 퍼널 차단 표본`을 병행 해석해야 함 | `12:00` 해석에서 entered/missed를 분리해 기록 |

- 현황 메모:
  - `더블유씨피`는 오늘 `fallback` canary의 `정상 full fill` 표본이다.
  - `에스앤에스텍`은 `fallback`이 실제 진입까지 갔지만 `1주 부분체결 + 6주 취소`로 끝난 `partial fill` 표본이다.
  - `hard_time_stop_shadow`는 `10:43:56`에 기록만 남았고 실청산에는 개입하지 않았다.
  - 현재 읽기는 `canary 정상 동작 확인`, `손익은 음수`, `표본은 2건`이지만 `체결 품질`을 분리해 봐야 한다.
  - 체결 품질 비교 메모: `더블유씨피`는 `scaled_qty=39`가 전량 체결됐고, `에스앤에스텍`은 `scaled_qty=7` 중 `1주`만 체결돼 같은 fallback 손실 표본이어도 해석 강도가 다르다.

### `AI BUY 후 미진입` 표본 비교표 (`2026-04-09 11:02 KST` 기준)

| 종목 | 분류 | 퍼널 종료 지점 | 핵심 근거 | 해석 메모 |
| --- | --- | --- | --- | --- |
| `037440 희림` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `AI BUY(92/85)` 후 `latency_block` 반복, `spread_ratio≈0.0081~0.0098`, `ws_age_ms≈152~336` | 오늘 latency miss 강표본 |
| `028050 삼성E&A` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `AI BUY 85`, `ws_age_ms=291/192/232/186`, `spread_ratio≈0.009398~0.009407` | 주문 직전 차단 반복 |
| `082920 비츠로셀` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `AI BUY 85`, `qty=23`, `ws_age_ms=430/1884/218/836/133/282/639/299`, `spread_ratio≈0.006165~0.006173` | latency 계열 추가 강표본 |
| `054620 APS` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `10:36:23` `AI BUY 85`, `target_buy_price=9290`, `qty=102`, `ws_age_ms=3693`, `spread_ratio=0.005371` | explicit `A tier` 표본, 초반 상승 확인 후 10분 종가 급반락 |
| `004020 현대제철` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `10:50:04` `AI BUY 85`, `qty=23~24`, `ws_age_ms≈222~568`, `spread_ratio≈0.006305~0.006321`, `order_bundle_submitted=0` | `VWAP_RECLAIM` 계열 latency miss 표본 |
| `098070 한텍` | `latency guard miss` | `entry_armed -> budget_pass -> latency_block` | `10:55:40` `AI BUY 92`, `qty=20`, `ws_age_ms=155~3304`, `spread_ratio≈0.009815`, `order_bundle_submitted=0` | 초반엔 liquidity miss가 있었지만 핵심 missed case는 latency |
| `259630 엠플러스` | `overbought gate miss` | `AI BUY -> blocked_overbought` | `10:58:46` `AI BUY 92` 후 `entry_armed/order_bundle_submitted` 없이 `blocked_overbought` 반복, `intraday_surge≈15.54~20.64`, `max_intraday_surge=15.50` | 주문 직전 차단이 아니라 과열 가드 선차단 |
| `317850 대모` | `liquidity gate miss` | `strength_momentum_pass -> blocked_liquidity` | `AI BUY 92`, `strength_momentum_pass` 후에도 `liquidity_value=70,560,750~247,217,700 < 350,000,000` | 유동성 가드 차단 |
| `327260 RF머티리얼즈` | `AI threshold miss` | `ai_confirmed(WAIT)` 또는 `blocked_ai_score` | `AI WAIT`, `blocked_ai_score` 반복, 일부 구간은 `AI BUY 후 latency_block` 동반 | threshold/cooldown 우선 분석 |

- 비교 메모:
  - `희림`, `삼성E&A`, `비츠로셀`, `APS`, `현대제철`, `한텍`은 공통적으로 `BUY -> entry_armed -> budget_pass`까지 갔지만 `latency_block`에서 주문 전 차단됐다.
  - `대모`는 `AI BUY`와 `strength_momentum_pass`가 있었어도 `blocked_liquidity`로 멈춰 latency 계열과 다르다.
  - `엠플러스`는 `AI BUY`가 있었지만 `entry_armed`로도 가지 못하고 `blocked_overbought`에 선차단돼, 주문직전 차단 계열과 다르다.
  - `RF머티리얼즈`는 `AI WAIT/blocked_ai_score`가 주축이라 threshold 계열 표본으로 분리한다.
  - `APS`는 explicit `target_buy_price`가 남아 있는 `A tier` 표본이라 proxy 표본보다 해석 우선순위가 높다.
  - `현대제철`, `한텍`은 `VWAP_RECLAIM` 계열에서도 `AI BUY` 후 반복적인 `latency_block(REJECT_DANGER)`가 누적될 수 있음을 보여주는 추가 표본이다.

### 12:00 스냅샷 기준 1차 실질 해석 (`2026-04-09 12:00 KST` 예정)

| 판단 항목 | 12:00 스냅샷 관측치 | 실질 해석 | 후속 액션 |
| --- | --- | --- | --- |
| `fallback` canary 손익 표본 | `trade_review` 종료 거래 `4건`: `후성 +0.58%(60주)`, `에스앤에스텍 -0.91%(1주)`, `페니트리움바이오 -2.04%(44주)`, `더블유씨피 -1.22%(39주)` / 총 실현손익 `-18,590원`, 평균 `-0.90%` | 실체결 표본은 더 이상 부족하지 않다. 다만 `entry_mode=''`, `exit_rule=None`으로 저장되어 `fallback cohort`가 리포트에서 분리되지 못했다. 즉 오늘 손익은 읽을 수 있지만 `fallback canary 전용 결론`으로 바로 쓰기엔 정합성 보정이 필요하다 | 장후에 `trade_review`의 `entry_mode`/`exit_rule` 복원 정합성을 우선 점검하고, `fallback 표본`만 재분리해 canary 결론을 확정 |
| `BUY 후 미진입` 퍼널 차단률 | `missed_entry_counterfactual` 기준 `total_candidates=19`, `evaluated_candidates=19`, `MISSED_WINNER=12`, `AVOIDED_LOSER=7` | 오늘은 `실체결 4건`이 있었어도 `미진입 차단 표본 19건`이 더 큰 해석 축이다. 따라서 canary 해석은 손익 표본만으로 내리면 왜곡된다 | `entered vs missed`를 분리해 장후 결론에 병기하고, 미진입 차단률을 canary 보조지표로 고정 |
| `missed_entry_counterfactual` | `MISSED_WINNER 63.2%`, `AVOIDED_LOSER 36.8%` / 상위 사유: `latency_block 13건`, `blocked_strength_momentum 5건`, `blocked_overbought 1건` | `AI BUY 후 미진입`의 다수가 `놓친 수익` 쪽으로 기운다. 특히 `latency_block`은 `missed_winner_rate 61.5%`, `blocked_strength_momentum`은 `60.0%`, `blocked_overbought`는 `100%`라 완화 후보 우선순위가 높다 | 장후 `latency -> dynamic strength -> overbought` 순으로 운영 완화 후보를 재정렬 |
| `빠른 손절/빠른 청산` 적정성 | 비교서버 `songstockscan`의 `에스앤에스텍(101490)`은 `2026-04-09 14:38:52` 진입, `14:39:35` 청산, `-0.23%`, 보유 `43초`였고 `post_sell_feedback`에서 `GOOD_EXIT`로 평가됨 | 손실 거래라고 해서 모두 `음수 leakage`로 분류하면 왜곡된다. 일부는 `매도 후 추가 하락 회피`에 성공한 적정 종료일 수 있다 | 장후 결론에서 `loss trade`를 `bad exit`와 `good defensive exit`로 다시 분리 |
| 미진입 사유 분포 | `latency_block`: `13건`, `blocked_strength_momentum`: `5건`, `blocked_overbought`: `1건` | 오늘 장중 핵심 병목은 `latency guard`다. `liquidity`나 `threshold`도 있었지만 빈도와 missed-winner 비중 모두 `latency`가 가장 크다 | `희림`, `APS`, `현대제철`, `한텍`, `비츠로셀`, `삼성E&A`를 묶어 `latency guard miss` 완화 검토표 작성 |
| buy pause guard 상태 | `evaluated_at=12:00:26`, `should_alert=false`, `sample_ready=false`, `completed_fallback_trades=0` | buy pause는 미발동이 맞다. 다만 이 값은 `더블유씨피/에스앤에스텍/페니트리움바이오`가 `fallback` 실체결로 리포트에 복원되지 않아 `fallback cohort=0`으로 보인 정합성 문제를 포함한다 | `buy_pause_guard`의 fallback trade 집계가 `trade_review` 복원 결과와 같은지 장후 재검증 |
| `본서버 vs songstockscan` raw snapshot 비교 | 원격 `15:45` 생성 스냅샷 기준 `trade_review`: 로컬 `completed_trades=4`, 원격 `2`, 로컬 `realized_pnl_krw=-18,590`, 원격 `215` / `post_sell_feedback`: 로컬 `evaluated_candidates=4`, 원격 `2`, 로컬 `good_exit_rate=25%`, 원격 `100%`, 로컬 `missed_upside_rate=50%`, 원격 `0%` / `performance_tuning`: metrics diff `0건` | 두 서버는 `체결/종료 거래 수`, `청산 적정성`에서 차이가 크다. 반면 `performance_tuning`은 raw snapshot 기준으로도 동일한 0값이라 오늘 실행 병목 비교 근거로는 약하다 | 비교 결과는 `trade_review/post-sell` 중심으로 해석하고, `performance_tuning` 0값은 오늘 결론에서 비중 축소 |
| 1차 운영 결론 | `canary 유지`, `강화 보류`, `즉시 롤백 보류`, `리포트 정합성 보정 우선` | 현재 손익은 음수지만, `실체결 4건`과 `미진입 19건`이 동시에 존재해 원인은 `canary 수량축` 단독보다 `주문전 차단 구조` 영향이 더 크다. 따라서 지금은 `fallback canary를 바로 더 줄이거나 롤백`하기보다 `latency miss`와 `fallback 분리 집계`를 먼저 고치는 게 맞다 | 장후 결론에서 `fallback 수량 canary 유지 + latency 완화 후보 검토 + report 정합성 보정` 3축으로 의사결정안 확정 |

- 기록 원칙:
  - `12:00` 해석은 오늘의 `1차 실질 해석`으로 본다.
  - `손익 표본`, `BUY 후 미진입 퍼널 차단률`, `missed_entry_counterfactual`을 함께 보고 결론을 낸다.
  - `손익 표본 0`이면 `조용함`으로 결론내리지 않고, `주문전 차단` 누적 여부를 먼저 확인한다.
  - `본서버 vs songstockscan` safe-only 비교 결과는 `12:00` 스냅샷 생성 시 자동 저장되며, 이 섹션 아래 생성 블록으로 자동 append된다.
  - 자동 비교는 `profit_rate NULL -> 0` 같은 fallback 정규화 값이 해석을 왜곡하지 않도록 `profit_rate` 파생 지표를 비교 기준에서 제외한다.

- 12:00 해석 메모:
  - 오늘 `trade_review` 종료 4건 중 `entry_mode`가 모두 빈값으로 남아 있어 `fallback 전용 손익`을 리포트에서 직접 분리하지 못했다.
  - `더블유씨피`, `에스앤에스텍`, `페니트리움바이오`는 장중 로그상 `fallback` 실체결이 확인됐는데, `buy_pause_guard`는 `completed_fallback_trades=0`으로 잡혀 정합성 차이가 있다.
  - 따라서 오늘 12시 결론은 `손익 해석 가능`, `fallback 전용 판정은 보류`, `리포트 복원 보정 필요`로 읽는 것이 안전하다.
  - 원격 raw snapshot 비교 기준 `trade_review`는 로컬 `4건`, 원격 `2건`, `post_sell_feedback`은 로컬 `4건`, 원격 `2건`으로 차이가 유지됐다. 반면 `performance_tuning` metrics는 diff `0건`이라 오늘 병목 비교 근거로는 약하다.
  - 비교서버의 `에스앤에스텍`은 `-0.23%` 손실이어도 `post_sell_feedback`상 `GOOD_EXIT`였다. 따라서 장후 해석에서는 `손실 거래 = 실패`로 단순 환산하지 않고, `매도 후 1/3/5/10분 경로` 기준 적정성 여부를 함께 본다.

### `13:00~14:00` trade_review 정합성 점검 결과 (`2026-04-09 14:10 KST`)

| 점검 항목 | 확인 결과 | 해석 | 후속 액션 |
| --- | --- | --- | --- |
| `trade_review` completed rows | `후성(093370)`, `에스앤에스텍(101490)`, `페니트리움바이오(187660)`, `더블유씨피(393890)` 모두 완료 거래로 집계됨 | 종료 손익 집계 자체는 살아 있다 | 손익 해석은 유지 가능 |
| `entry_mode` 복원 | 위 4개 종목 모두 `entry_mode=''` | `fallback cohort` 분리가 실패했다 | `fallback canary` 전용 결론은 아직 보류 |
| `exit_rule` 복원 | 최종 row에 `exit_rule` 필드 자체가 없음 | 청산 규칙 분리 해석이 현재 스냅샷에서는 불가능하다 | `sell_completed/exit_signal` 복원 경로 재점검 필요 |
| 실제 fallback 체결 근거 | `sniper_execution_receipts_info.log`에는 `ENTRY_BUNDLE_FILLED mode=fallback`가 `더블유씨피`, `페니트리움바이오`, `후성`에 대해 존재함. `에스앤에스텍`은 `ENTRY_FILL tag=fallback_scout`까지는 존재하나 `ENTRY_BUNDLE_FILLED`는 없음 | 장중 실체결 근거와 trade_review 집계 결과는 연결되지만, `fallback mode` 태그는 리포트로 전달되지 않는다 | 부분체결 표본까지 포함해 receipt 로그를 복원 소스로 써야 한다 |
| 로그 소스 정합성 | `trade_review`는 `[HOLDING_PIPELINE]` 마커가 있는 텍스트 로그만 읽는데, 오늘 체결 근거는 주로 `ORDER_NOTICE_BOUND`, `ENTRY_FILL`, `ENTRY_BUNDLE_FILLED` 형태로 `sniper_execution_receipts_info.log`에 남아 있다 | 복원 로직 문제 이전에 `입력 로그 소스가 어긋나 있다`가 더 정확한 진단이다 | `trade_review`가 receipt 이벤트 또는 구조화 JSONL을 함께 소비하도록 수정 후보 정리 |

- 점검 메모:
  - 오늘 `trade_review_2026-04-09.json`의 `completed_trades` 4건은 모두 `position_tag=SCANNER`, `entry_mode=''` 상태다.
  - `더블유씨피`, `페니트리움바이오`, `후성`은 receipt 로그상 `ENTRY_BUNDLE_FILLED mode=fallback`가 명확하다.
  - `에스앤에스텍`은 `fallback_scout` 1주 부분체결 뒤 잔량이 이어지지 않아 `full fill`이 아니라 `partial fill` 표본으로 따로 다뤄야 한다.
  - 현재 구조에서는 `buy_pause_guard`와 `trade_review`가 같은 `fallback cohort` 수치를 공유하기 어렵다.
  - 따라서 `14:00~15:20` 이전 우선 결론은 `latency miss 표본 정리`를 계속 진행하되, 장후에는 `trade_review 입력 소스 확장`을 수정 1순위로 둔다.

### `14:00~15:20` latency guard miss 전수 집계 결과 (`2026-04-09 15:22 KST`)

| 점검 항목 | 확인 결과 | 해석 | 후속 액션 |
| --- | --- | --- | --- |
| 전수 집계 범위 | `2026-04-09 09:00~15:20`, `ENTRY_PIPELINE`, `stage=latency_block`, `decision=REJECT_DANGER` 기준 전수 집계 | 대표 표본 6종만으로 보면 편향이 생기므로 오늘 해석은 전수 집계 기준이 맞다 | 장후 결론도 전수 집계 기준으로 작성 |
| 전체 규모 | `latency guard miss 1,253건`, `21종목` | 오늘 스캘핑의 주문전 차단은 예외가 아니라 주요 병목이다 | 완화 후보 검토는 단일 사례가 아닌 분포 기준으로 판단 |
| 편중도 | 상위 5종목이 `테크윙 381`, `희림 164`, `롯데케미칼 120`, `머큐리 81`, `SK텔레콤 77`로 총 `823건` (`65.7%`) | latency miss는 전 종목에 균등하지 않고 일부 종목/상황에 강하게 집중된다 | 완화안은 전역 완화보다 `조건부/국소 canary`가 더 적합 |
| 대표 6종 상세 | `희림 164`, `비츠로셀 64`, `APS 52`, `현대제철 26`, `한텍 25`, `삼성E&A 4` | 기존 우선 표본 6종은 여전히 유효하지만, 전체 분포를 대표하지는 않는다 | 전수 분포 + 대표 6종 상세 비교를 함께 유지 |
| 추가 핵심 종목 | `티엘비 59`, `RF머트리얼즈 56`, `지투지바이오 34`, `에스앤에스텍 2`, `후성 1`, `페니트리움바이오 1` | 오늘 장중에 논의한 종목 일부도 latency miss 집계에 실제로 포함된다. 반면 `테크윙`, `롯데케미칼`, `머큐리`, `SK텔레콤`, `휴스틸`은 새롭게 큰 비중을 차지한다 | 장후 결론에서 `대표 6종` 외에 `상위 빈도 종목군`을 별도 메모 |
| 수치 분포 특징 | `한텍 ws_age_avg=1162.8ms`, `에스앤에스텍=1893.5ms`, `중앙에너비스=1781.6ms`처럼 고지연형이 있고, `휴스틸=184.3ms`, `삼성E&A=225.2ms`처럼 낮은 `ws_age_ms`에서도 miss가 발생한다 | 단순히 `ws_age_ms` 기준만 완화하는 접근은 불충분하다. `spread_ratio`, `quote_stale`, 종목 특성까지 함께 봐야 한다 | 장후 완화안은 `ws_age` 단일 임계값 완화 대신 다변수 조건부 완화로 설계 |
| `quote_stale` 비중 | `비츠로셀 22`, `한텍 12`, `중앙에너비스 11`, `지투지바이오 14`처럼 stale 편중 종목이 존재 | 일부 종목은 `stale quote`가 주된 원인이고, 일부는 그렇지 않다 | `quote_stale=True` 계열과 `False` 계열을 분리한 운영안 검토 |
| 원격 비교 가능성 | 원격 `entry-pipeline-flow` API는 `has_data=false`였지만, 원격 `pipeline_events_2026-04-09.jsonl` 원본을 내려받아 동일 기준 전수 비교가 가능해졌다 | API 비교는 불가능하지만, 원본 JSONL 기준 `latency miss` 전수 비교는 가능하다. 원격 API 공백은 `sniper_state_handlers_info.log`에 `[ENTRY_PIPELINE]` 텍스트 로그가 없어서 생긴다 | 이후 비교는 `API`가 아니라 `원격 JSONL/receipts/post-sell 원본` 기준으로 고정 |

- 전수 집계 상위 종목:
  - `089030 테크윙`: `381건`, `ws_age_avg=346.0ms`, `spread_avg=0.009584`, `quote_stale_true=18`
  - `037440 희림`: `164건`, `ws_age_avg=273.1ms`, `spread_avg=0.008473`, `quote_stale_true=2`
  - `011170 롯데케미칼`: `120건`, `ws_age_avg=329.3ms`, `spread_avg=0.005753`, `quote_stale_true=6`
  - `100590 머큐리`: `81건`, `ws_age_avg=259.5ms`, `spread_avg=0.006253`, `quote_stale_true=0`
  - `017670 SK텔레콤`: `77건`, `ws_age_avg=261.8ms`, `spread_avg=0.005339`, `quote_stale_true=0`
  - `005010 휴스틸`: `76건`, `ws_age_avg=184.3ms`, `spread_avg=0.008343`, `quote_stale_true=0`

- 원격 서버 동일 기준 전수 집계 (`2026-04-09 09:00~15:20`, `ENTRY_PIPELINE`, `stage=latency_block`, `decision=REJECT_DANGER`):
  - 총 `481건`, `12종목`
  - 상위 종목:
    - `037440 희림`: `91건`, `ws_age_avg=525.2ms`, `spread_avg=0.009441`, `quote_stale_true=18`
    - `023160 태광`: `78건`, `ws_age_avg=503.2ms`, `spread_avg=0.006479`, `quote_stale_true=11`
    - `066570 LG전자`: `67건`, `ws_age_avg=527.7ms`, `spread_avg=0.004227`, `quote_stale_true=3`
    - `047040 대우건설`: `61건`, `ws_age_avg=235.3ms`, `spread_avg=0.010467`, `quote_stale_true=0`
    - `082920 비츠로셀`: `36건`, `ws_age_avg=965.7ms`, `spread_avg=0.006671`, `quote_stale_true=18`
  - 겹치는 종목 기준으로는 원격도 `희림`, `비츠로셀`, `티엘비`, `RF머트리얼즈`, `에스앤에스텍` 등에서 같은 유형의 latency miss가 확인된다.
  - 반면 로컬 상위였던 `테크윙`, `롯데케미칼`, `머큐리`, `SK텔레콤`은 원격 상위군과 다르다.

- 대표 6종 및 논의 종목 메모:
  - `희림`, `비츠로셀`, `APS`, `현대제철`, `한텍`, `삼성E&A`는 상세 사례 비교 대상으로 유지한다.
  - `티엘비 59건`, `RF머트리얼즈 56건`은 오늘 논의량 대비 실제 latency miss 비중도 높아 장후 메모에 포함한다.
  - `에스앤에스텍`, `후성`, `페니트리움바이오`는 latency miss 자체는 소수 건이지만 `fallback/빠른 청산` 해석 축 때문에 별도 추적 가치가 있다.
  - 원격 서버는 `entry-pipeline-flow` API는 비어 있지만, 내려받은 `pipeline_events_2026-04-09.jsonl` 기준으로는 `latency guard miss` 전수 비교가 가능하다.
  - 원격 `sniper_state_handlers_info.log`에는 `[ENTRY_PIPELINE]` 텍스트 로그가 없어 API가 빈 값이었고, 따라서 앞으로 이 축 비교는 `API`가 아니라 `JSONL 원본` 기준으로 수행한다.
  - 공유 종목군만 보면 원격이 일관되게 더 낫지는 않다. `희림`은 로컬 `164건 / ws_age_avg=273.1ms / stale=2`, 원격 `91건 / 525.2ms / stale=18`, `RF머트리얼즈`는 로컬 `56건 / 322.0ms / stale=0`, 원격 `21건 / 1730.0ms / stale=15`다. 따라서 양 서버 차이는 `네트워크 품질 단독`보다 `후보 종목군/퍼널 진입 분포` 차이로 보는 편이 맞다.
  - `2026-04-10 16:00 KST` 원격 로그+스냅샷 자동 수집 1회 실행을 예약했다. 실행 명령은 `PYTHONPATH=. python -m src.engine.fetch_remote_scalping_logs --date 2026-04-10 --include-snapshots-if-exist`, 로그는 `logs/remote_scalping_fetch_20260410_1600.log`, 결과물은 `tmp/remote_2026-04-10/`에 저장된다.

<!-- AUTO_SERVER_COMPARISON_START -->
### 본서버 vs songstockscan 자동 비교 (`2026-04-10 11:12:13`)

- 기준: `profit-derived metrics are excluded by default because fallback-normalized values such as NULL -> 0 can distort comparison`
- 상세 리포트: `data/report/server_comparison/server_comparison_2026-04-09.md`
- `Trade Review`: status=`ok`, differing_safe_metrics=`5`
  - all_rows local=103 remote=69 delta=-34.0; expired_rows local=89 remote=61 delta=-28.0; total_trades local=4 remote=2 delta=-2.0
- `Performance Tuning`: status=`ok`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
- `Post Sell Feedback`: status=`ok`, differing_safe_metrics=`2`
  - total_candidates local=4 remote=2 delta=-2.0; evaluated_candidates local=4 remote=2 delta=-2.0
- `Entry Pipeline Flow`: status=`ok`, differing_safe_metrics=`0`
  - safe 기준 차이 없음
<!-- AUTO_SERVER_COMPARISON_END -->

## 2026-04-09 장후 체크리스트 (15:30~)

- [ ] 공통 hard time stop 후보안 영향 추정
  - `3분`, `5분`, `7분`, `5분+저점수`, `fallback 3~5분`, `수익 미전환+장시간` 후보를 최근 거래일로 백테스트
  - 승률/평균손익/손익합/조기잘림 비율을 같은 기준으로 산출
- [x] 스캘핑 canary 당일 결론 작성
  - `유지 / 강화 / 롤백` 중 하나로 임시 결론 작성
  - `당일 장후` 결론 + 필요 시 `1~2세션` 후속 확인 계획을 같이 남긴다
  - 트리거: `[내 지시 필요]` 장후 정리 요청 시 수행
- [x] `latency -> dynamic strength -> overbought` 완화 우선순위 확정
  - `latency` 1순위, `dynamic strength` 2순위, `overbought` 3순위로 고정
  - 익일 장전 전에는 `latency`만 조건부 완화 후보 검토, `dynamic strength`는 국소 완화 검토, `overbought`는 표본 추가 확보 전 완화 보류
- [ ] 스윙 Gatekeeper missed case 정리 완료
  - 장중 수집한 후보를 정식 표본으로 확정
  - `blocked_gatekeeper_reject` vs 이후 추세를 일자별로 정리
- [ ] 스윙 missed case 요약표 + threshold 완화 검토 근거 문서화
  - `완화 보류/부분 canary/완화 검토` 중 하나로 근거 기반 결론 작성
  - `2026-04-10` 장전 의사결정안으로 연결
- [ ] `AI WAIT/latency` missed case 요약표 작성
  - `RF머티리얼즈(327260)`, `희림(037440)`, `삼성E&A(028050)`, `대모(317850)`, `비츠로셀(082920)`를 첫 표본으로 정리하고, `AI WAIT`, `latency_block`, `blocked_liquidity` miss를 각각 분리 집계
  - `AI threshold/cooldown 조정 후보`, `latency guard 운영 후보`, `liquidity gate 운영 후보`를 같은 표에서 비교
- [ ] 스캘핑 진입종목의 스윙 자동전환 검토 프레임 초안 작성
  - 전환 트리거/금지조건/전환 후 리스크관리/사후검증 지표를 1페이지로 정리
  - 최소 5거래일 shadow 검증 전 실전 ON 금지 원칙을 명시

### `2026-04-09` 장후 스캘핑 canary 결론 (`2026-04-09 16:10 KST`)

| 항목 | 결론 | 근거 | 익일 액션 |
| --- | --- | --- | --- |
| `fallback canary` 유지 여부 | `유지` | 로컬 `trade_review` 기준 완료 거래 `4건`, 총 실현손익 `-18,590원`, 평균 `-0.90%`로 음수지만, `fallback 수량축` 단독 실패로 단정할 근거는 부족하다 | `2026-04-10` 장전에도 현재 수량 canary는 유지 |
| 확대 여부 | `강화 보류` | `미진입 기회비용`이 `19건`, `MISSED_WINNER 63.2%`로 커서 오늘 병목은 `수량축`보다 `주문전 차단 구조` 쪽이다 | `latency -> dynamic strength -> overbought` 우선순위 정리 후 결정 |
| 즉시 롤백 여부 | `보류` | 음수는 맞지만 `buy_pause_guard` fallback cohort 집계가 `0건`으로 보일 정도로 `trade_review` 정합성 문제가 남아 있고, `entry_mode/exit_rule` 복원도 미완료다 | 먼저 `trade_review`/`buy_pause_guard` fallback cohort 정합성 보정 |
| 주병목 판정 | `latency` 1순위, `dynamic strength` 2순위, `overbought` 3순위 | `latency_block 13건`, `blocked_strength_momentum 5건`, `blocked_overbought 1건`, 전수 집계로는 `latency guard miss 1,253건 / 21종목` | 익일 장전 전 `latency` 완화 후보안 1~2개 작성 |
| 원격 비교 해석 | `원격이 오늘 trade_review/post-sell은 우세`, `latency는 단순 우위 아님` | 원격 raw snapshot 기준 `trade_review 2건 / 215원`, `good_exit_rate 100%`, `missed_upside_rate 0%`였지만, 공유 종목군 `ws_age_ms/stale`는 원격이 더 나쁜 경우도 있다 | 원격은 `청산 적정성` 참조축으로 활용하고, `latency`는 JSONL 원본 기준으로 계속 비교 |
| 당일 운영 결론 | `유지 / 강화 보류 / 즉시 롤백 보류 / 정합성 보정 우선` | 오늘 음수는 `실현손익 음수 + 미진입 기회비용 음수`가 함께 있었고, 이 중 큰 축은 `latency`를 포함한 주문전 차단 구조다 | 익일 목표를 `fallback 수량`이 아니라 `병목 완화와 cohort 정합성 복구`에 둔다 |

- 장후 요약 메모:
  - `trade_review` raw snapshot: 로컬 `completed_trades=4`, 원격 `2`
  - `post_sell_feedback` raw snapshot: 로컬 `good_exit_rate=25%`, 원격 `100%`
  - `performance_tuning` raw snapshot: metrics diff `0건`
  - 로컬/원격 차이는 `네트워크 품질 단독`보다 `후보 종목군`, `퍼널 진입 분포`, `청산 품질` 차이로 해석하는 편이 맞다

### `2026-04-09` 완화 우선순위 확정 (`2026-04-09 16:20 KST`)

| 우선순위 | 축 | 오늘 판단 | 근거 | 내일 적용 원칙 |
| --- | --- | --- | --- | --- |
| `1` | `latency guard` | 최우선 완화 검토 | `latency_block 13건`, 전수 집계 `1,253건 / 21종목`, `missed_entry_counterfactual` 기준 `MISSED_WINNER` 비중이 높다 | 전역 완화 금지, `quote_stale=False` 또는 특정 조건부 완화안만 검토 |
| `2` | `dynamic strength` | 제한적 완화 검토 | `blocked_strength_momentum 5건`, `missed_winner_rate 60.0%` | `momentum_tag`, `threshold_profile` 기준 국소 완화만 검토 |
| `3` | `overbought` | 완화 보류, 관찰 유지 | `blocked_overbought 1건`, `missed_winner_rate 100%`지만 표본 부족 | 추가 표본 확보 전 실전 완화 금지 |

- 우선순위 보조 메모:
  - `fallback 수량 canary`는 오늘 음수였지만 주병목이 `수량축` 단독으로 확정되지 않아 완화 우선순위에서 제외한다.
  - `trade_review`/`buy_pause_guard`의 `fallback cohort` 정합성 보정은 완화안과 별개인 `운영 필수 보정`이다.

### `2026-04-10` 장전 실행안 (`2026-04-09 16:30 KST`)

| 구분 | 항목 | 결정 | 필수 확인 | 추가 검토 필요 |
| --- | --- | --- | --- | --- |
| `유지` | `fallback 수량 canary` | `유지` | `trade_review`/`buy_pause_guard` fallback cohort 정합성 | 정합성 결과에 따라 해석만 조정 |
| `유지` | `overbought` 차단 | `유지` | 완화안에 섞이지 않았는지 확인 | 표본 추가 후 재검토 |
| `유지` | 공통 hard time stop | `shadow-only 유지` | 실청산 ON 여부 재확인 | 장후 백테스트 후 별도 검토 |
| `필수 확인` | `trade_review` 정합성 보정 | `장전 전 확인` | `entry_mode`, `exit_rule`, `fallback cohort` 일치 여부 | 불일치 시 당일 해석 신뢰도 낮춤 |
| `필수 확인` | 원격 수집 자동화 | `유지` | `16:00 KST` cron, `logs/remote_scalping_fetch_20260410_1600.log` 확인 | 실패 시 수동 수집 대기 |
| `조건부 검토` | `latency guard` | `후보안 1~2개만 검토` | 전역 완화 금지, `quote_stale=False` 등 조건부 설계 여부 | 세부 수치 확정 필요 |
| `조건부 검토` | `dynamic strength` | `국소 완화 검토` | `momentum_tag`, `threshold_profile` 분리 여부 | 세부 범위 확정 필요 |
| `보류` | `overbought` 완화 | `보류` | 실행안에 포함 금지 | 표본 추가 확보 후 재검토 |

- 금일 미완료건 처리:
  - `공통 hard time stop 후보안 영향 추정`: 장후 이월
  - `AI WAIT/latency/liquidity missed case 요약표`: 부분 완료, 내일 장중/장후 보강
  - `스윙 Gatekeeper missed case 정리`: 내일 장후 이월
  - `스윙 missed case 요약표 + threshold 완화 검토`: 내일 장후 이월
  - `스캘핑 진입종목의 스윙 자동전환 검토 프레임`: 내일 장후 이월

- 운영 반영 전 필수 확인:
  - `fallback` 실체결 수가 `trade_review`와 `buy_pause_guard`에 동일하게 잡히는지 확인
  - `latency` 완화안이 전역 완화가 아닌지 확인
  - `quote_stale=True` 구간이 완화 대상에 섞이지 않았는지 확인
  - `dynamic strength` 완화가 `momentum_tag`/`threshold_profile` 분리 검토인지 확인
  - `overbought` 완화가 실행안에 들어가 있지 않은지 확인

### 전체 plan 대비 `2026-04-09` 비교검토 (`2026-04-10 09:00 KST`)

| plan 워크스트림 | `2026-04-09` 반영 상태 | 갭/리스크 | 필수 조치 | 추가 검토 |
| --- | --- | --- | --- | --- |
| `WS1 Gatekeeper 재사용 복구` | `부분 반영` (`Dual Persona OFF 유지`, 조건 고정) | `missing_action/missing_allow_flag/sig_changed` 원인 분해가 미완료 | 장중에 `gatekeeper_fast_reuse_ratio`, `gatekeeper_ai_cache_hit_ratio`와 blocker 원인 표를 별도 기록 | 재사용 조건 완화는 원인 분해 후 |
| `WS2 보유 AI 재평가 낭비 감소` | `부분 반영` (`curr/spread` 축 정의 시도) | `curr/spread` 완화안 정량 영향 추정 미완료 | `curr/spread` 분석 집계축 확정 및 전일 대비 비교표 작성 | `near_ai_exit/near_safe_profit` band 조정은 보류 유지 |
| `WS3 성과 집계/복기 기준 통일` | `부분 반영` (raw snapshot 비교, post-sell 병행 해석) | `trade_review entry_mode/exit_rule/fallback cohort` 정합성 미복구 | `trade_review`가 receipt/JSONL을 함께 소비하도록 보강 후보 확정 | canary 결론 해석 오차 최소화 |
| `WS3-Add 추가매수 품질 관측` | `미반영` | `AVG_DOWN/PYRAMID/no-add` 분리 비교가 `4/9` 계획에 없음 | `4/10` 장후 항목으로 이월 명시 | 지표 정의 후 리포트 편입 |
| `WS4 로그/스냅샷 체계` | `반영` (`10:00/12:00` 스냅샷, `16:00` 원격 수집 자동화) | 원격 `entry-pipeline-flow` API 공백(텍스트 로그 의존) | `JSONL 원본` 기준 비교를 기본으로 유지 | API 파서 고도화는 `WS7`로 이월 |
| `WS5 전략 튜닝` | `반영` (`latency > dynamic strength > overbought` 우선순위 확정) | `latency` 전역 완화 오적용 위험 | 조건부 완화안 1~2개만 검토 (`quote_stale=False` 등) | `dynamic strength`는 국소 완화만 |
| `WS5-Add 스캘핑→스윙 전환` | `미완료` | 검토 프레임 초안 부재 | 장후 초안 작성 이월 유지 | 5거래일 shadow 전 실전 금지 |
| `WS6 post-sell 피드백` | `반영` (원격/로컬 post-sell 비교 반영) | 분류 임계값 주간 리밸런싱 미실행 | 장후 `missed/good` 임계값 리밸런싱 항목 추가 | `performance-tuning` 카드 병합 검토 |
| `WS7 이벤트 스키마/공통 로거` | `미착수` | `entry-pipeline-flow` 텍스트 로그 공백 시 API 무력화 | `trade_review/performance_tuning` JSONL 직접 소비 우선순위로 이월 | 필드 품질 검증 배치는 후속 |

- 비교검토 결론:
  - `2026-04-09`는 전략 튜닝 방향(`WS5`)과 운영 관측(`WS4`, `WS6`)은 반영됐지만, 집계 정합성(`WS3`)과 이벤트 스키마(`WS7`)가 다음 병목이다.
  - `2026-04-10` 장전/장중 우선순위는 `WS3 -> WS2 -> WS1` 순으로 두고, 전략 완화안 적용은 이 정합성 확인 후 진행한다.

## 2026-04-09 종일 유지 점검 (미적용 정책 11개)

- [ ] `near_safe_profit` 수치 직접 하향하지 않는다
- [ ] `near_ai_exit` 수치 직접 완화하지 않는다
- [x] 공통 hard time stop 실전 적용하지 않는다
- [ ] fallback 전면 차단하지 않는다
- [ ] 스캘핑 공통 손절값 일괄 완화하지 않는다
- [ ] 추가매수(`AVG_DOWN`/`PYRAMID`) 임계값 직접 완화하지 않는다
- [ ] 스윙 AI threshold 직접 완화하지 않는다
- [ ] `RISK_OFF` 상태의 스윙 허용 기준 완화하지 않는다
- [x] `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER` 당일 재활성화하지 않는다(조건 미달 시)
- [ ] `dual_persona_shadow` 스윙 실전 승급하지 않는다
- [ ] 스윙 gap 기준 직접 완화하지 않는다

## 2026-04-09 완료 기준

- [x] 장전 5개 항목 결과가 시각/수치와 함께 기록된다
- [ ] 장중 4개 항목 결과가 시각/수치와 함께 기록된다
  - `canary 손익 표본`과 `BUY 후 미진입 퍼널 차단 표본`이 함께 남아야 한다
- [ ] 장후 6개 항목(전일 미수행 포함) 결과가 문서화된다
- [ ] 종일 유지 점검 11개 항목의 유지 여부가 체크된다
- [ ] `2026-04-10`에 바로 넘길 수 있는 의사결정 근거(적용/보류/롤백)가 남는다

## 참고 문서

- [2026-04-08-stage2-todo-checklist.md](./2026-04-08-stage2-todo-checklist.md)
- [2026-04-10-stage2-todo-checklist.md](./2026-04-10-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
