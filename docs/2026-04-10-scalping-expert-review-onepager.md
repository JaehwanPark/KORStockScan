# 2026-04-10 스캘핑 튜닝 현황 1페이지 점검 리포트

## 목적

- 스캘핑만 대상으로, `손실 억제`보다 `기대값/순이익 극대화` 관점에서 현재 튜닝 상태를 외부 트레이딩 전문가가 빠르게 점검할 수 있게 정리한다.
- 기준 데이터는 `2026-04-09~2026-04-10` 실매매 스냅샷, `pipeline_events`, `trade_review`, `missed_entry_counterfactual`, `post_sell_feedback`, Stage 2 체크리스트다.

## 1) 감시 제외, 진입부터 청산까지의 상세 단계

1. `AI BUY 확정 (ai_confirmed)`
   - 매수 후보가 AI 확답을 받은 뒤 실제 진입 퍼널로 들어간다.
2. `초기 미진입 분기`
   - `first_ai_wait`, `blocked_strength_momentum`, `blocked_ai_score`, `blocked_overbought`, `blocked_liquidity`에서 1차 차단된다.
3. `진입 자격 확보 (entry_armed)`
   - 조건을 통과한 표본만 짧은 유효시간 안에서 진입 자격을 가진다.
4. `수량 계산 통과 (budget_pass)`
   - 예산/수량/주문가능금액을 통과한 뒤 실제 주문 직전 단계로 이동한다.
5. `Latency Gate`
   - `SAFE/CAUTION/DANGER`로 판정한다.
   - `quote_stale`, `ws_age_ms`, `ws_jitter_ms`, `spread_ratio`, slippage를 함께 본다.
   - `SAFE`는 normal, `CAUTION`은 fallback, `DANGER`는 진입 차단이다.
6. `주문 제출/체결`
   - `order_bundle_submitted` 후 `ENTRY_FILL`, `ENTRY_BUNDLE_FILLED`로 체결을 추적한다.
   - `full fill`과 `partial fill`은 반드시 분리 해석한다.
7. `보유/청산`
   - `holding_started` 후 `preset_exit_setup`, `ai_holding_review`, `hard_time_stop_shadow`를 거쳐 `exit_signal -> sell_order_sent -> sell_completed`로 종료된다.
8. `사후평가`
   - `post_sell_feedback`으로 `GOOD_EXIT`, `MISSED_UPSIDE`, `NEUTRAL`을 평가한다.
   - 실현손익과 별도로 `BUY 후 미진입` 기회비용을 `missed_entry_counterfactual`로 본다.

## 2) 현재까지 단계별 진단 내역

- 판정: 현재 주병목은 `청산 규칙`보다 `진입 전 차단`, 그중에서도 `budget_pass 이후 latency_block`이다.
- 근거:
  - `2026-04-10` 장후 유니크 퍼널은 `ai_confirmed 75 -> entry_armed 44 -> budget_pass 40 -> submitted 6`이다.
  - `budget_pass 후 미제출`은 장후 기준 `34/34 latency_block`이다.
  - 장중 누적 기준으로도 `budget_pass 후 미제출 31건`의 첫 blocker가 모두 `latency`였고, `quote_stale=False/True = 14/17`로 `stale quote`만의 문제도 아니다.
  - `AI BUY 후 미진입` 누적 `69건`은 모두 `first_ai_wait`에서 시작해 terminal이 `blocked_strength_momentum 40`, `blocked_ai_score 23`, `blocked_overbought 5`, `first_ai_wait 1`로 이어졌다.
  - 청산 쪽은 `post_sell_feedback` 기준 `missed_upside_rate 16.7%`, `good_exit_rate 16.7%`로 아직 미세조정보다 표본 축적 단계다.
- 다음 액션:
  - `latency`는 `quote_stale=False` 축 중심으로 제출 전환율을 먼저 올리는 방향이 맞다.
  - `dynamic strength`는 전역 완화가 아니라 `momentum_tag/threshold_profile`별 국소 재설계가 맞다.
  - `overbought`는 표본 부족으로 유지가 맞다.

## 3) 실제 매매 분석 현황

- 판정: 실현손익은 아직 음수지만, 더 큰 EV 훼손은 `미진입 missed winner`에서 발생하고 있다.
- 근거:
  - `2026-04-10` 실매매: `COMPLETED 6건`, `승/패 2/4`, `avg_profit_rate -0.41%`, `realized_pnl -10,885원`.
  - `2026-04-09 -> 2026-04-10` 비교:
    - 실현손익 `-18,590원 -> -10,885원`
    - 평균수익률 `-0.90% -> -0.41%`
    - 완료거래 `4 -> 6`
  - 그러나 `BUY 후 미진입` 반사실 분석은 더 공격적인 신호를 준다.
    - `2026-04-10`: `evaluated 21`, `MISSED_WINNER 17`, `missed_winner_rate 81.0%`, `estimated_counterfactual_pnl_10m +24,960원`
    - `latency_block` 표본만 봐도 `20건`, `missed_winner_rate 80.0%`
  - 청산 사후평가:
    - `estimated_extra_upside_10m_krw_sum +24,730원`
    - 평균 capture efficiency `22.65%`
    - 즉 청산 개선 여지도 있지만, 현재는 진입 전 EV 누수가 더 크다.
  - 체결 품질은 `full fill`과 `partial fill`을 분리 추적 중이며, 현재 메모상 `fallback partial` 코호트는 손익 기여가 음수라 별도 점검축으로 유지 중이다.

## 4) 수익극대화를 위해 현재까지 한 노력

- 판정: 현재 튜닝은 `한 번에 한 축 canary`, `shadow/rollback 가드`, `실현손익 + 기회비용 동시 해석` 원칙으로 운영 중이다.
- 근거:
  - `RELAX-LATENCY`: `강화`
    - 로컬 결론은 강화, 원격 `songstockscan`에는 `quote_stale=False` 유지 상태에서 `ws_jitter`만 완화한 `remote_v2`를 `2026-04-10 14:35 KST`에 선행 적용했다.
  - `RELAX-DYNSTR`: `유지`
    - 조건부 canary는 반영했지만 downstream 전환 근거가 약해 추가 완화보다 재설계 우선이다.
  - `RELAX-OVERBOUGHT`: `유지`
    - missed winner 사례는 있지만 표본이 적어 실전 완화는 보류했다.
  - 리포트/집계 정합성도 함께 보강했다.
    - `entry-pipeline-flow`, `performance-tuning`은 텍스트 로그 의존을 줄이고 `pipeline_events JSONL` 우선 집계로 수정했다.
    - `trade_review`는 `entry_mode` 복원 로직을 보강했지만, `fill quality` 복원 품질은 계속 점검 중이다.

## 전문가 점검 시 추가로 제공하면 좋은 자료

- `latency missed winner` 대표 3건
  - `quote_stale=False`와 `quote_stale=True`를 나눠서 제공
- `체결 품질` 대표 3건
  - `normal full fill 1건`, `fallback full fill 1건`, `fallback partial fill 1건`
- `청산 복기` 대표 2건
  - `GOOD_EXIT 1건`, `MISSED_UPSIDE 1건`
- `현재 canary 파라미터/롤백 조건`
  - latency, dynamic strength, fallback qty multiplier, overbought 유지 조건
- `원격 선행 실험 결과`
  - 로컬 vs `songstockscan` 퍼널/체결 품질/리포트 차이

## 최종 한줄 결론

- 지금 스캘핑 튜닝의 핵심 질문은 `손절을 완화할지`가 아니라, `budget_pass 이후 latency 차단으로 놓치는 고기대값 진입을 어떻게 회수할지`다.
