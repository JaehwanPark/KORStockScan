# 판정항목별 개선 흐름 정리

주의: 이 문서는 개인 정리용이며 다른 문서에서 참조하지 않는다. 개인문서는 다른 문서를 참조할 수 있다.

## 현재 기준 스냅샷

| 항목 | 현재 기준 |
| --- | --- |
| 기준일 | `2026-05-07 KST` 장후 정렬 기준 |
| entry live owner | `mechanical_momentum_latency_relief` 운영 override와 `dynamic_entry_price_resolver_p1`/`dynamic_entry_ai_price_canary_p2` 가격축이다. `latency_quote_fresh_composite`, `latency_signal_quality_quote_composite`, fallback/split-entry 계열은 종료/폐기 축이다. |
| AI score 50 | `AI_SCORE_50_BUY_HOLD_OVERRIDE_ENABLED=True`로 score 50 또는 `ai_fallback_score_50=True`는 신규 BUY가 아니라 `blocked_ai_score` 보류로 본다. 유안타증권형 반복 손실은 단순 쿨다운 문제가 아니라 손절 thesis invalidation과 WATCHING 재진입 판단이 분리된 구조 문제로 본다. |
| submitted 이후 해석 | submitted 이후는 진입병목이 아니라 체결 품질과 BUY 신호 적정성 관찰 구간이다. `full/partial`은 합치지 않고, 이후 `HOLDING -> exit_rule -> COMPLETED + valid profit_rate`로 BUY 품질을 본다. |
| entry 수량축 | 스캘핑 신규 BUY는 `1주 cap` 유지다. `PYRAMID zero_qty`는 신규 BUY cap 확대가 아니라 `buy_qty=1`에서도 불타기 신호가 실행 가능하도록 1주 floor bugfix로 처리했다. |
| 보유/청산 live owner | `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`다. `bad_entry_refined_canary`는 5/4 장후 flow defer와 장마감 주문실패 혼입으로 OFF했고, refined 후보는 `SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED=True` report-only counterfactual로만 유지한다. |
| holding_flow_override | 보유/청산 및 오버나이트 `SELL_TODAY` 후보를 단일 점수 컷이 아니라 긴 입력 윈도와 AI flow summary로 재검문한다. hard/protect/order safety는 우회하지 않는다. 오버나이트 flow `TRIM`은 부분청산 구현 전까지 `HOLD_OVERNIGHT`가 아니라 원래 `SELL_TODAY` 유지다. |
| 장마감 매도 safety | 15:30 KST 이후 SCALPING 매도 신호는 주문을 보내지 않고 `sell_order_blocked_market_closed` 1회와 `market_closed_sell_pending=True`로 분리한다. 이는 주문 실패를 숨기는 것이 아니라 after-close impossible truth를 보존하는 safety gap 보정이다. |
| 추가매수 횟수 제한 | 물타기/불타기 `MAX_*_COUNT`는 runtime blocker가 아니라 attribution counter다. 반복 추가매수 리스크는 enable flag, cooldown, pending order, position cap, protection 재설정 fail-closed, near-close gate로 제한한다. 단독 hard cooldown은 임시 안전장치 외에는 복합 threshold 전환 후보로 본다. |
| REVERSAL_ADD/PYRAMID | `REVERSAL_ADD`와 `PYRAMID`는 기대값을 키우는 상위 행동 후보지만, 수량 산식은 아직 고정 템플릿 성격이다. 5/6에는 `ReversalAddDynamicQty0506`, `PyramidDynamicQty0506`에서 observe-only `would_qty`부터 설계한다. |
| trailing/protect 위치 | trailing/protect 민감도는 5/4 장후 기준 active live 변경 없이 5/6 `TrailingProtectSensitivity0506` 단일 owner로 재판정한다. `scalp_trailing_take_profit`은 평균 완료수익이 양호하지만 weak borderline과 PYRAMID 교차가 크고, protect trailing은 손실 확대 차단과 missed upside가 섞여 있다. |
| OFI/QI 위치 | OFI/QI는 P2 entry price 내부 입력 품질개선축이다. standalone hard gate가 아니며, `watching/holding/exit` 확장은 별도 workorder 없이는 금지한다. 5/4 장후 P2 stage 111건 중 `USE_DEFENSIVE=96`, `SKIP=8`, `skip_without_bearish_ofi=4`라 neutral/insufficient SKIP demotion 후보는 5/8 `OFIQExpansionLadder0508`에서 본다. |
| OpenAI 위치 | OpenAI Responses WS/schema/deterministic config는 live routing 승격이 아니라 flag-off backlog다. 5/4 장후 실측 WS/shadow stage는 0건이므로 `runtime 미사용 backlog 유지`로 보고, 5/6 `AIEngineFlagOffBacklog0506`에서 route/diagnostic 존재 여부만 재분류한다. |
| threshold/report 진행현황 | 실시간 자동변경은 금지다. 현재는 장전 manifest와 장후 report 생성까지만 허용하며, live runtime threshold mutation은 `ThresholdOpsTransition0506` acceptance 전까지 열지 않는다. `statistical_action_weight`, `holding_exit_decision_matrix`, 누적/rolling threshold report는 report-only/decision-support다. `preclose_sell_target`은 5/7 기준 AI fallback/Telegram 전송/15:00 cron까지 반영됐지만 consumer 범위는 여전히 `operator_preclose_review`까지만 승인이다. |
| ADM 상태 | `holding_exit_decision_matrix`는 report-only 산출물에서 출발한다. 5/7 장후 `holding_exit_matrix_runtime.py`와 provider 3종 parity patch로 loader/flag/cache/provenance plumbing은 구현됐지만 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=False` 기본 OFF를 유지한다. `ADM-2 shadow prompt` naming은 stale에 가깝고, 5/7 matrix entry는 `no_clear_edge` 비중이 높아 same-day live AI 응답 변경 근거는 약하다. |
| 진입 후속 owner | 추상적으로 `submitted/full/partial funnel 회복`이라고 적는 대신, 다음 owner는 `EntryFunnelRecoveryDecision0508`로 고정한다. `BUY Funnel Sentinel + missed_entry_counterfactual + submitted/full/partial/COMPLETED valid PnL`을 한 owner에서 묶어 `score65_74 recovery probe` 다음 장전 enable/hold/drop을 닫는다. broad threshold 완화나 fallback 재개는 이 owner 범위가 아니다. |
| 보유/청산 후속 owner | `ExitDecisionSourceProvenance0508`은 2026-05-07 KST에 선실행 완료했다. `exit_decision_source` taxonomy를 runtime/report/test/post-sell payload에 고정했고, 이후 matrix advisory, bad-entry refined, winner wide-window 해석은 이 field를 공통 provenance로 사용한다. `3-mode counterfactual`은 여전히 설계 only다. |
| 휴장/이월 보정 | `2026-05-05`는 어린이날 휴장이다. 5/6 PREOPEN은 이미 코드/가드가 준비된 carry-over 로드 확인만 받고, 설계 가능한 항목은 5/4 장후에 즉시 닫거나 5/6 POSTCLOSE 단일 owner로 분리한다. |

## 추가매수 제한 해석 메모

### `MAX_*_COUNT` 제거와 one-shot semantic guard의 차이

| 항목 | 제거된 제한 | 현재 남아 있는 가드 | 해석 포인트 |
| --- | --- | --- | --- |
| `AVG_DOWN` | `SCALPING_MAX_AVG_DOWN_COUNT`, `SWING_MAX_AVG_DOWN_COUNT`는 runtime blocker가 아니라 attribution counter다. generic `AVG_DOWN` 평가 경로는 제거했고, scalping `AVG_DOWN` add_type은 `REVERSAL_ADD` 체결 귀속명으로만 남긴다. | `REVERSAL_ADD`의 `pnl/hold/floor/AI recovery/supply`, `scale_in_cooldown`, `pending_add_order`, `position_at_cap`, `near_market_close`, `scale_in_locked` | 물타기는 `몇 번 했는가`보다 `지금 추가해도 되는 포지션인가`를 본다. 단순 낙폭형 일반 물타기는 future swing tuning에서도 재사용하지 않는다. |
| `REVERSAL_ADD` | 별도 `MAX_REVERSAL_ADD_COUNT` gate는 없다. 일자/전략 단위 count cap으로 막지 않고, 동일 포지션 one-shot semantic도 제거했다. | `pnl/hold/floor/AI recovery/supply` 조건, `POST_ADD_EVAL`, `scale_in_cooldown`, `pending_add_order`, `position_at_cap`, `near_market_close`, protection fail-closed | 동일 거래 동일 종목에서도 반복 추가매수를 count/used 플래그로 막지 않는다. 반복 사용 제한은 count가 아니라 상태/쿨다운/주문중복/리스크 가드가 맡는다. |
| `PYRAMID` | `SCALPING_MAX_PYRAMID_COUNT`, `SWING_MAX_PYRAMID_COUNT`는 runtime blocker가 아니라 attribution counter다. | `SCALPING_ENABLE_PYRAMID`/`SWING_ENABLE_PYRAMID`, 최소 수익/추세 유지 조건, `scale_in_cooldown`, `pending_add_order`, `position_at_cap`, `near_market_close`, protection fail-closed | 불타기도 count cap이 아니라 추세 지속성과 리스크 가드로 제한한다. 다만 현재 수량 자체는 고정 템플릿 성격이 강해서 동적 수량화는 observe-only 후속 owner다. |

### 코드 기준 해설

| 축 | 현재 코드 기준 |
| --- | --- |
| deprecated count gate | [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py:59) 기준 `SCALPING_MAX_AVG_DOWN_COUNT`, `SCALPING_MAX_PYRAMID_COUNT`, `SWING_MAX_AVG_DOWN_COUNT`, `SWING_MAX_PYRAMID_COUNT`는 모두 `DEPRECATED: runtime count gate removed; counter remains for attribution`로 남아 있다. |
| 공통 runtime 가드 | [sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py:6728) 기준 추가매수 공통 가드는 `scale_in_locked`, `invalid_position`, `sell_ordered`, `add_judgment_locked`, `scale_in_cooldown`, `pending_add_order`, `position_at_cap`, enable flag, `near_market_close`, `scalping_cutoff`다. |
| `AVG_DOWN` 판정 | generic `AVG_DOWN` 평가는 제거됐고, [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:307) 기준 scalping `AVG_DOWN` add_type은 `evaluate_scalping_reversal_add()`가 만드는 `reversal_add_ok` 체결 경로로만 남는다. |
| `REVERSAL_ADD` 판정 | [sniper_scale_in.py](/home/ubuntu/KORStockScan/src/engine/sniper_scale_in.py:367) 기준 `reversal_add_used`는 더 이상 반복 차단에 쓰지 않는다. 대신 `pnl`, `hold_sec`, `low_floor`, `ai_recovery`, `supply`를 모두 통과해야 하고, 체결 후에는 `POST_ADD_EVAL`과 공통 `scale_in_cooldown/pending_add_order/position_at_cap/protection` 가드가 반복 사용을 제한한다. |
| count의 현재 의미 | [sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py:994) 기준 `avg_down_count`, `pyramid_count`, `add_count`는 체결 후 집계/귀속용으로만 증가한다. 즉 실행 전 blocker가 아니라 체결 후 attribution counter다. |

### 개인 메모 결론

1. `횟수 제한 제거`는 `count-based mechanical block 제거`를 뜻한다.
2. `reversal_add_used` 같은 one-shot semantic도 제거 대상이다. 동일 거래 동일 종목 반복 추가매수 제한은 count/used가 아니라 상태/쿨다운/리스크 가드로만 남긴다.
3. 내일 장중 해석은 `count miss`가 아니라 `pnl/hold/AI/supply/cooldown/pending/position_cap/protection` blocker 분포를 봐야 한다.

## 현재 기준 최종 의사결정 흐름

### Entry

1. `mechanical_momentum_latency_relief` 운영 override와 `dynamic_entry_price_resolver_p1`/`dynamic_entry_ai_price_canary_p2`가 현재 entry owner다.
2. `latency_quote_fresh_composite`, `latency_signal_quality_quote_composite`, `spread relief`, fallback/split-entry 계열은 active owner가 아니라 historical/reference 또는 guarded-off다.
3. 현재 판정 순서는 `budget_pass -> submitted 회복 확인 -> 체결 품질과 BUY 신호 적정성 확인`이다. 단, `AI score 50 fallback`은 더 이상 신규 BUY로 내려보내지 않고 `blocked_ai_score` 보류로 본다.
4. 따라서 entry의 현재 최종 의사결정 흐름은:
   - upstream `buy_recovery_canary`는 고정 배경축
   - live owner는 `DF-ENTRY-007 mechanical_momentum_latency_relief`와 P1/P2 entry price canary
   - 제출 전까지는 병목 판정, `submitted` 이후는 `full/partial` 체결 품질과 `HOLDING/exit_rule/COMPLETED + valid profit_rate`로 BUY 신호 적정성 관찰
   - 이 downstream 품질이 닫혀야 entry baseline 승격 또는 다음 replacement 축 논의가 가능하다

### Holding/Exit

1. 보유/청산 live owner는 `soft_stop_micro_grace`, `REVERSAL_ADD`, `holding_flow_override`다.
2. `DF-HOLDING-004 soft_stop_expert_defense`는 `2026-04-30` same-day v2 수집 축으로 종료했고, 다음 승인 전 기본 OFF다.
3. `REVERSAL_ADD`는 parking 대상이 아니라 `valid_entry_reversal_add` active canary다. 현재 후속은 live 수량 변경이 아니라 5/6 observe-only 동적 수량 산식이다.
4. `bad_entry_refined_canary`는 5/4 장후 OFF다. 이는 bad-entry 조기정리 필요가 사라졌다는 뜻이 아니라, flow defer와 장마감 주문실패가 canary cohort에 섞여 원인귀속이 깨졌다는 뜻이다.
5. 다음 bad-entry 축은 live canary가 아니라 `SCALP_BAD_ENTRY_REFINED_OBSERVE_ENABLED=True` report-only counterfactual enrichment다. `would_exit`와 `should_exit`를 분리해 다음 단일축 설계 입력으로 남긴다.
6. trailing/protect 민감도는 5/4 당일 live 변경 없이 5/6 `TrailingProtectSensitivity0506`에서 `initial-only`, `pyramid_signaled_not_executed`, `pyramid_executed`로 나눠 재판정한다.

### Threshold

1. threshold 운영은 `실시간 drift`가 아니라 `장중 적재 -> 장후 산정 -> 다음 장전 적용`이다.
2. compact stream이 기본 적재 경로이고 raw `pipeline_events` full scan은 복구성 작업으로만 제한한다.
3. 최종 안정화 후 운영전환 조건은 아래 4개다.
   - 매일 자동 실행
   - 매일 장전 승인 threshold 자동 적용 후 봇 기동
   - 매일 장후 threshold version별 매매실적 결과 제출
   - 해당 실적 결과를 다음 threshold weight 산정에 반영
4. 현재 sample ready 축:
   - `entry_mechanical_momentum`
   - `bad_entry_block`
   - `REVERSAL_ADD blocked funnel`
   - `soft_stop_micro_grace`
5. 현재 부족 축:
   - `partial fill`
   - `preset hard stop`
   - `post-sell feedback pipeline`
   - `PYRAMID realized EV`

## 감시종목 -> 보유/청산 완료 흐름

### 단계 요약표

| 단계 | 관문 | 통과 의미 | 대표 차단/결과 |
| --- | --- | --- | --- |
| 1 | 감시종목 유입 | 조건검색/스캐너로 WATCHING 대상에 들어옴 | 감시망 미유입 |
| 2 | 선행 차단 통과 | 과열, 유동성, AI 점수, 스윙 갭 차단을 넘김 | `blocked_overbought`, `blocked_liquidity`, `blocked_ai_score`, `blocked_swing_gap` |
| 3 | 진입 후보 자격 충족 | `(score >= buy_threshold or is_shooting) and vpw_condition` 충족 | score/vpw 미달 |
| 4 | gatekeeper 진입 | WATCHING 최종 진입 검증 구간에 도달. 먼저 `fast_reuse` 재사용 가능성(`window`, `signature`)을 확인 | `gatekeeper_fast_reuse_bypass` 후 실평가 또는 `gatekeeper_fast_reuse` |
| 5 | gatekeeper 통과 | AI가 `allow_entry=true`, `action_label=즉시 매수`로 판단 | `blocked_gatekeeper_reject`, `blocked_gatekeeper_error`, `blocked_gatekeeper_missing` |
| 6 | BUY 신호 | 텔레그램/런타임 기준 BUY 신호로 해석 가능한 상태. 주문 직전 후보 | 이후 `entry_armed`, 예산/수량, `submitted_orders`는 다음 단계 |
| 7 | 주문 자격 확보 | `entry_armed`, `budget_pass`까지 도달해 실제 주문 제출을 재시도할 수 있는 상태 | `latency_block`, `entry_armed_expired`, `entry_armed_expired_after_wait` |
| 8 | 주문 제출/체결 | `submitted` 이후 `full/partial` 체결로 넘어가는 상태 | `submitted` 미도달, `partial fill`, `full fill` |
| 9 | HOLDING 시작 | 체결 수량 기준 보유 상태로 진입, 보호주문/상태동기화 시작 | `holding_started`, `preset_exit_setup`, `preset_exit_sync_*` |
| 10 | HOLDING AI 리뷰 루프 | 가격/시간 변화에 따라 보유 AI 재평가 또는 스킵 수행 | `ai_holding_review`, `ai_holding_skip_unchanged`, `ai_holding_reuse_bypass` |
| 11 | 보유 중 분기 판단 | 추가매수 후보 또는 청산 신호로 분기 | `reversal_add_candidate`, `scale_in_executed`, `exit_signal` |
| 12 | 매도 주문/복구 | 청산 주문 전송 성공 또는 실패 후 HOLDING 복구 재시도 | `sell_order_sent`, `sell_order_failed` |
| 13 | 청산 완료 | 매도 체결 완료 후 포지션 종료 | `sell_completed`, `completed` |

### 플로우차트

```text
[감시종목 유입]
    |
    v
[선행 차단 통과]
    |- 실패 -> blocked_overbought
    |- 실패 -> blocked_liquidity
    |- 실패 -> blocked_ai_score
    |- 실패 -> blocked_swing_gap
    v
[(score >= buy_threshold or is_shooting) and vpw_condition]
    |- 실패 -> BUY 후보 미형성
    v
[gatekeeper 진입]
    |- 직전 판단이 재사용 window 안이고 signature도 동일 -> gatekeeper_fast_reuse
    |- 재사용 window 만료(age_expired) -> gatekeeper_fast_reuse_bypass -> 실 gatekeeper 평가
    |- 재사용 window 안이지만 signature 변경(sig_changed) -> gatekeeper_fast_reuse_bypass -> 실 gatekeeper 평가
    v
[gatekeeper 통과 여부]
    |- 실패 -> blocked_gatekeeper_reject / blocked_gatekeeper_error / blocked_gatekeeper_missing
    v
[BUY 신호]
    |- AI WAIT/보류 + Score 50 fallback -> blocked_ai_score 보류
    |
    v
[entry_armed]
    |- 예산 통과 -> budget_pass
    |- TTL 만료 -> entry_armed_expired / entry_armed_expired_after_wait
    v
[제출 전 검증]
    |- 실패 -> latency_block
    |- 재시도 성공 -> submitted
    v
[주문 제출]
    |- 일부 체결 -> partial fill
    |- 전량 체결 -> full fill
    v
[HOLDING 시작]
    |- holding_started / preset_exit_setup
    v
[HOLDING AI 리뷰 루프]
    |- 변화 미미 -> ai_holding_skip_unchanged
    |- 변화 감지 -> ai_holding_review
    v
[보유 중 의사결정]
    |- 추가매수 후보 -> reversal_add_candidate -> scale_in_executed -> HOLDING AI 리뷰 루프
    |- 청산 신호 -> exit_signal
    |               (scalp_soft_stop_pct / scalp_hard_stop_pct / scalp_trailing_take_profit / scalp_ai_momentum_decay)
    v
[매도 주문]
    |- 성공 -> sell_order_sent -> sell_completed -> completed
    |- 실패 -> sell_order_failed -> HOLDING 복구 후 재시도
```

### 해석 메모

- 텔레그램 BUY 신호는 대체로 `gatekeeper 통과`까지는 온 상태로 본다.
- 다만 `BUY 신호 = 주문접수 완료`는 아니다. `entry_armed`, 예산/수량, 주문 제출, 체결은 다음 단계다.
- `AI 판단 보류(Score 50)`는 현재 기준으로 신규 BUY가 아니다. 2026-05-04 이후 score 50 또는 `ai_fallback_score_50=True`는 `blocked_ai_score`로 보류한다.
- `entry_armed`에 들어간 뒤에는 `latency_block`, `quote_stale`, `ws_age/ws_jitter` 같은 제출 전 병목 때문에 곧바로 `submitted`로 가지 못할 수 있다.
- 과거 `2026-04-23 KST` 덕산하이메탈(`077360`)은 `Score 50 fallback -> entry_armed -> budget_pass -> latency_block 반복 -> 주문접수/체결` 사례였지만, 현재는 score 50 fallback 신규 BUY를 보류로 바꿨으므로 historical reference로만 본다.
- `gatekeeper_fast_reuse`는 같은 종목의 직전 gatekeeper 판단을 매우 짧은 시간창에서 재사용한 경우다. fast signature, 재사용 가능 시간, websocket freshness, score 경계값, 직전 action/allow_entry 기록이 모두 맞아야 성립한다.
- `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`는 현재 기준으로 재개 후보가 아니다. live 주문 경로와 runtime guard는 제거됐고, 남아 있는 fallback 표기는 과거 로그/리포트 해석용 historical trace로만 읽는다.
- 여기서 `window`는 “직전 판단이 아직 재사용해도 될 만큼 최근인가”를 보는 시간 조건이고, `signature`는 “지금 장면이 직전 판단과 사실상 같은가”를 보는 상태 조건이다.
- 즉 `window`가 만료되면 `age_expired` 쪽으로 재사용이 깨지고, `window` 안이어도 가격/스프레드/점수/수급 같은 핵심 입력이 달라지면 `sig_changed`로 재사용이 깨진다.
- 의미는 `새 AI gatekeeper 호출을 생략하고 직전 판단을 그대로 재사용했다`는 것이다. 따라서 `gatekeeper_fast_reuse`가 찍히면 gatekeeper 구간에는 도달한 것이 맞지만, 새로운 모델 평가가 매번 다시 돈 것은 아니다.
- 왜 중요하나: BUY 회복이 안 보일 때 `gatekeeper_fast_reuse` 비중이 높으면 실제 병목이 모델 호출 지연이 아니라 `같은 장면 재사용`, `score boundary`, `ws freshness`, `signature 변화` 쪽일 수 있다.
- HOLDING 단계에서는 `is_sell_signal`이 생기기 전까지 `ai_holding_review`와 `scale_in` 후보평가가 반복된다. 즉 제출축이 살아나면 다음 병목은 보유 중 `soft stop/trailing/ai exit` 품질로 넘어간다.
- 이후 보완도 `append`가 아니라 기존 판정 섹션을 최신 스냅샷 기준으로 갱신하는 방식으로 유지한다.

### 보유/청산 보조 관찰 메모

| 항목 | 내용 |
| --- | --- |
| soft_stop 휩쏘 가설 | 소프트손절 후 `1m/3m/5m/10m/20m` 반등을 `rebound_above_sell`, `rebound_above_buy`, `mfe_ge_0_5`, `mfe_ge_1_0`로 분리한다. 매도가만 재상회하면 micro grace/확인유예 후보이고, 매수가까지 회복하면 cooldown live가 아니라 threshold/AI 재판정 후보로 본다. |
| 하드스탑 위치 | `scalp_preset_hard_stop_pct`, `scalp_hard_stop_pct`, `protect_hard_stop`은 soft_stop보다 완화 우선순위를 낮춘다. 하드스탑은 극단 손실 방어선이므로 반등 사례가 있어도 `hard_stop_whipsaw_aux` 보조 관찰로만 두고, 바로 완화 canary로 올리지 않는다. |
| 하방카운트 위치 | `ai_low_score_hits`/`scalp_ai_early_exit`는 2026-04-27 기준 live 경로에서 제거했다. 기존 하방카운트는 가격 휩쏘 필터가 아니라 후행 AI 조기손절이라 soft_stop 보호장치로서 실효성이 낮았다. |
| 4월 로그 해석 | 4월 하방카운트 `0/3` 또는 `0/4` 편중과 `3/3` 희소성은 제거 판단 근거로만 보존한다. 현재 soft_stop 해석은 `rebound_above_sell/buy`, `mfe_ge_*`, `same_symbol_reentry`, `hard_stop_auxiliary` 중심으로 고정한다. |

### 소프트손절 튜닝 전략 메모

| 항목 | 내용 |
| --- | --- |
| 왜 물타기를 선택했나 | 목적은 손실 방어가 아니라 `기대값/순이익 극대화`다. 4월 soft stop 표본은 직접 손실 기여가 컸지만, post-sell 기준 10분 내 매도가 재상회와 +0.5% 이상 반등이 많아 `진입 자체는 유효했지만 초반 눌림 뒤 회복한 표본`이 섞여 있다고 본다. 그래서 전역 손절 완화가 아니라 `valid_entry_reversal_add`로 유효 진입 회수 가능성을 좁게 검증한다. |
| 단순 유예 연장을 우선하지 않는 이유 | `soft_stop_micro_grace_extend`를 바로 켜면 정당 컷이어야 할 never-green/AI fade 표본까지 더 오래 들고 갈 수 있다. EV 관점에서는 손실을 늦추는 것보다 `회복 전조가 확인된 표본만 평단을 낮춰 회수`하는 쪽이 원인귀속과 롤백이 선명하다. |
| REVERSAL_ADD 해석 | 일반 물타기가 아니라 `profit_rate -0.70%~-0.10%`, `held_sec 20~180`, `AI>=60`, 저점 미갱신, AI bottom 대비 `+15pt` 또는 연속회복, 수급 3/4 충족일 때만 1회 허용하는 소형 canary다. 수량은 `REVERSAL_ADD_SIZE_RATIO=0.33`, 1주 cap 환경에서도 `REVERSAL_ADD_MIN_QTY_FLOOR_ENABLED=True`로 1주 floor를 허용한다. `2026-04-30 10:15 KST` intraday override는 `pnl_out_of_range`, `hold_sec_out_of_range` blocker만 완화했고 AI/supply 조건은 유지했다. |
| 수량 산식의 현재 한계 | 현재 수량은 `buy_qty * REVERSAL_ADD_SIZE_RATIO`를 기본 템플릿으로 두고 `MAX_POSITION_PCT` 기반 남은 예산 cap과 1주 floor만 반영한다. 즉 현재가/예수금/보유수량/포지션 cap은 반영하지만, AI 회복 강도, 손실폭 위치, soft/hard stop까지의 거리, 수급 회복 강도, realized volatility를 직접 반영하는 완전 동적 산식은 아니다. |
| 수량 동적화 방향 | EV 관점에서는 `회복 확률`과 `추가 노출 리스크`를 같이 반영하는 동적 수량이 더 자연스럽다. 후보 공식은 `base_floor 1주 + confidence_multiplier(AI 회복, 수급 3/4~4/4, 저점 미갱신) - risk_discount(soft/hard stop 거리, peak_profit never-green, 포지션 cap 근접)` 형태로 두되, live 적용 전에는 counterfactual/observe-only로 `would_qty`, `actual_qty`, `post_add_mfe`, `post_add_stop_rate`를 먼저 남긴다. |
| 불타기 수량 현재값 | `PYRAMID`도 `describe_scale_in_qty()` 공통 경로를 탄다. 스캘핑 `PYRAMID`는 `buy_qty * 0.50` 템플릿, `MAX_POSITION_PCT` 기반 cap, `SCALPING_PYRAMID_ZERO_QTY_STAGE1_ENABLED` floor 옵션을 쓴다. 현재 기본값은 floor off라 `buy_qty=1`이면 `int(1*0.5)=0`으로 막히고, `buy_qty=2`부터 1주 불타기가 가능하다. |
| 불타기 동적화 방향 | 불타기는 손실 회수형 `REVERSAL_ADD`보다 동적 수량화 필요성이 더 크다. `is_new_high`, `peak_profit - profit_rate <= 0.3`, 수익률 레벨, AI/수급 지속성, trailing giveback 여유, 당일 종목 재진입 여부를 반영해 `winner size-up`을 해야 한다. 다만 현재는 `initial-only`와 `pyramid-activated` 표본 분리가 우선이고, 수량 동적화는 `REVERSAL_ADD`와 별도 축으로 설계해야 한다. |
| 물타기 후 손절 기준 | 추가매수 체결 시 receipt 경로에서 `buy_price`를 새 가중평균가로 갱신한다. HOLDING 루프는 매번 `profit_rate = calculate_net_profit_rate(buy_price, curr_price)`로 다시 계산하고, `scalp_soft_stop_pct`, `scalp_hard_stop_pct`, `reversal_add_post_eval_fail`도 이 갱신된 평단 기준 수익률을 사용한다. 즉 최초 진입가 기준으로 계속 판별하는 구조가 아니라 `현재 보유 평단` 기준이다. |
| 물타기 후 즉시 실패 가드 | `reversal_add_state == POST_ADD_EVAL` 동안 `REVERSAL_ADD_POST_EVAL_SEC=25` 창에서 AI가 55 미만, 수익률이 기존 `reversal_add_profit_floor - 0.05%p` 아래, 대량 매도 체결, tick acceleration 약화가 나오면 `reversal_add_post_eval_fail`로 즉시 손절 신호를 만든다. |
| EV 관점 추가전략 1 | `bad_entry_block`: `held_sec>=60`, `profit_rate<=-0.70%`, `peak_profit<=+0.20%`, `AI<=45`인 never-green/AI fade를 observe-only로 로깅한다. 표본이 쌓이고 soft/hard stop 전환율이 비후보보다 높으면 다음 운영일 live entry block 후보로만 검토한다. |
| EV 관점 추가전략 2 | `recovery recapture`: soft stop 후 동일종목 고가 재진입 또는 매수가 회복을 별도 라벨로 분리한다. 목적은 손절 유예가 아니라 `청산 후 회수 경로`가 독립 alpha인지 확인하는 것이다. |
| EV 관점 추가전략 3 | `same-symbol soft stop cooldown`: soft stop 직후 같은 종목을 더 높은 가격에 재진입해 손실과 재진입 슬리피지를 동시에 만드는 패턴을 차단 후보로 둔다. 다만 현재는 shadow/observe 성격으로만 해석하고 live 차단은 별도 단일축이 필요하다. |
| EV 관점 추가전략 4 | `trailing_continuation_micro_canary`: trailing 익절 후 `MISSED_UPSIDE + same_symbol_reentry`가 반복되면 이익을 너무 빨리 끊는 문제다. 현재는 soft stop 다음 2순위 후보로 유지한다. |
| soft_stop_expert_defense | `soft_stop_micro_grace`를 단순 시간유예로 더 늘리지 않고, 전문가 전략 후보를 계층화해 v2 방어망으로 묶었던 당일 수집 축이다. `2026-04-30` live에서는 `stop arbitration layer + thesis invalidation veto + orderbook absorption stop`만 열었고, `MAE/MFE quantile`, `recovery probability`, `partial de-risk`, `adverse fill`은 주문 변경 없이 shadow/observe로만 남겼다. 다음 재승인 전 기본 OFF다. |
| 데이터 기반 threshold 산정 | `REVERSAL_ADD`만의 문제가 아니다. entry mechanical/VPW/liquidity/AI/pre-submit, holding soft stop/bad entry/reversal add/trailing/position sizing을 모두 threshold family로 보고, `데이터량 -> 산정 가능성 -> 단일 canary 후보값` 순서로 잠근다. 실시간 자동변경은 폐기하고 `장중 적재 -> 장후 산정 -> 다음 장전 적용`만 공식 운영 사이클로 쓴다. |
| 통계 행동가중치 | 전문가 규칙 계층과 별도로 `statistical_action_weight`를 둔다. completed trade와 compact action stage를 이용해 가격대/거래량/시간대별로 `exit_only`, `avg_down_wait`, `pyramid_wait`의 평균손익/승률을 비교한다. 단순 평균이 아니라 action별 전체 prior로 shrinkage하고 불확실성 penalty를 뺀 `confidence_adjusted_score`를 쓴다. score 차이가 작으면 `no_clear_edge`, 손실비율이 높으면 `defensive_only_high_loss_rate`로 두고, live 행동 변경이 아니라 다음 threshold weight와 동적 수량화 설계의 근거로만 쓴다. |
| decision snapshot | 행동가중치의 다음 수집축은 `stat_action_decision_snapshot`이다. HOLDING 판단 순간의 `chosen_action`, `eligible_actions`, `rejected_actions`, `scale_in_gate_reason`, `scale_in_action_reason`, `exit_rule_candidate`, 수익률/고점/AI/수급/호가 상태를 같이 남긴다. 목적은 실제 선택 행동만 보는 selection bias를 줄이고 `eligible_but_not_chosen` 후보의 후행 MFE/MAE를 나중에 복원하는 것이다. |
| AI 보유/청산 decision matrix | 사용자가 요구한 최종형은 threshold 적용만이 아니라 AI가 보유/청산 판단 시 통계 matrix를 참조하는 것이다. 별도 산출물 `holding_exit_decision_matrix`를 두고, 전일 장후 산정값을 다음 장전 로드해 장중에는 immutable context로 쓴다. 5/7 장후에는 holding prompt/exit alias 전용 runtime loader, feature flag, cache key suffix, provenance logging, baseline/candidate/excluded cohort를 구현했다. 다만 `ADM-2 shadow prompt injection`은 naming이 stale에 가깝고 실제 runtime flag는 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED` 기본 OFF다. 현재 5/7 matrix는 `no_clear_edge` 비중이 높아 same-day live 전환 근거는 약하다. |
| 롤백 기준 | `REVERSAL_ADD` 체결 cohort의 `COMPLETED + valid profit_rate` 평균이 `<= -0.30%`이거나 `reversal_add_used` 후 soft stop 전환율이 baseline 대비 `+5.0%p` 이상이면 OFF하고, `bad_entry_block` 관찰만 유지한다. `soft_stop_expert_defense`는 guarded cohort 평균손익 `<= -0.30%`, guarded 후 hard/protect stop 전이, `sell_order_failed`, `REVERSAL_ADD` 체결 포지션 적용 1건 이상이면 v2를 OFF하고 v1 micro grace만 유지한다. |

## ID 명명 규칙

| 항목 | 규칙 |
| --- | --- |
| 기본 형식 | `DF-영역-번호` |
| 접두어 `DF` | `Decision Flow`의 약자다. 이 문서의 모든 판정 흐름 항목에 공통으로 붙인다. |
| `영역` | 판정이 속한 개선 영역을 적는다. 예: `ENTRY`, `HOLDING`, `EXIT`, `DATA`, `OPS` |
| `번호` | 같은 영역 안에서 `001`부터 순차 증가시킨다. 번호는 의미를 담기보다 순서를 고정하는 용도다. |
| 작성 원칙 1 | 한 ID는 하나의 판정항목만 가진다. 여러 액션을 묶어 하나의 ID로 합치지 않는다. |
| 작성 원칙 2 | 이미 결정이 끝난 항목도 ID를 유지하고, `결정 결과`와 `후속 액션`으로 다음 항목과 연결한다. |
| 작성 원칙 3 | 후속 액션이 새 판정항목으로 분리되면 새 ID를 발급하고, 선행 항목 표 안에 후속 ID를 명시한다. |
| 예시 | `DF-ENTRY-001`, `DF-ENTRY-002`, `DF-HOLDING-001`, `DF-DATA-001` |

## 진입 병목 판정 흐름

### DF-ENTRY-001 `blocked_ai_score_share` 개선 검토

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-001` |
| 판정항목 | `blocked_ai_score_share` 개선 검토 |
| 문제 인식 | Gemini가 BUY 대신 WAIT/DROP으로 과도하게 막는 비중이 높으면, 실제로는 진입 가치가 있는 후보도 초기에 탈락해 `미진입 기회비용`이 커진다. |
| 해석 방향 | 단순 손실 억제보다 `기대값/순이익 극대화` 기준으로 본다. 즉, 잘못된 진입을 조금 더 줄이는 것보다 “들어가야 할 종목을 너무 많이 놓치고 있지 않은가”를 먼저 본다. |
| 확인하려는 지표 의미 | `blocked_ai_score_share`는 AI가 BUY로 보내지 않고 점수 단계에서 막아버린 비중이다. 이 값이 높고 BUY/제출 표본이 같이 마르면 AI 해석이 과보수적일 가능성이 높다. |
| 기대효과 | `blocked_ai_score_share`가 내려가면 `WAIT/DROP 과밀`이 완화되고, `ai_confirmed -> submitted`로 이어질 수 있는 후보 풀이 늘어난다. 결국 목표는 BUY 남발이 아니라 “막히지 말아야 할 후보의 복구”다. |
| 주의점 | 이 지표만 보고 threshold를 바로 풀면 원인귀속이 흐려질 수 있다. 제출 병목, latency, budget blocker와 분리해서 봐야 한다. |
| 결정 결과 | 독립 개선축으로는 채택하지 않았다. `blocked_ai_score_share` 자체는 핵심 관찰지표로 유지하되, 이 지표만을 직접 완화 목표로 삼는 별도 액션은 폐기했다. |
| 현재 상태 | `2026-04-30` 기준 폐기 상태 유지다. 이 값은 계속 보조 관찰지표로만 쓴다. 현재 live/active owner는 entry 쪽 `DF-ENTRY-007`, holding/exit 쪽은 `soft_stop_micro_grace`와 `DF-HOLDING-003`의 `REVERSAL_ADD`/refined bad-entry 후보 관리다. |
| 폐기 사유 | 장중 판정 시점에 필요한 것은 지표 자체의 개선 선언이 아니라 `WAIT65~79 -> BUY 회복`을 실제로 만드는 구체 액션이었다. 독립 `blocked_ai_score_share` 개선축은 실행 단위가 모호하고, `score`, `prompt`, `latency`, `budget` 중 무엇을 건드리는지 흐릴 수 있다. |
| 후속 액션 | `DF-ENTRY-002 buy_recovery_canary prompt 재교정`으로 연결한다. 즉, 관찰지표는 유지하되 실행은 recovery prompt 1축으로 옮긴다. |

### DF-ENTRY-002 `buy_recovery_canary prompt` 재교정

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-002` |
| 판정항목 | `buy_recovery_canary prompt` 재교정 |
| 적용 배경 | 12시 기준 `recovery_check=21`인데 `promoted=0`, `submitted=0`이었다. 회복 재평가를 걸었는데도 BUY 복구가 전혀 안 나와, 점수 숫자보다 `recovery prompt` 해석 문맥이 더 보수적일 가능성이 높다고 봤다. |
| 작업 방향성 | `WAIT 65~79` 구간을 단순 보류대가 아니라 “조건이 살아나면 BUY로 복구될 수 있는 회복 구간”으로 읽게 만든다. 재돌파, 매도벽 흡수, 거래 재가속, 고점 재안착 같은 회복 신호를 더 적극적으로 해석하게 하는 쪽이다. |
| 무엇을 안 건드렸는가 | 전역적인 `score/promote` 완화는 하지 않았다. `AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE` 값은 유지했고, `scalping_buy_recovery_canary` 전용 프롬프트만 바꿨다. |
| 기대효과 1 | `promoted=0` 상태를 깨서 `WAIT65~79 -> BUY 회복` 표본을 만든다. |
| 기대효과 2 | 회복된 BUY가 실제 `submitted`까지 이어지는지 확인해, 병목이 프롬프트인지 아니면 latency/budget인지 더 분명히 분리한다. |
| 기대효과 3 | 단순 BUY 수 증가가 아니라 `미진입 기회비용`을 줄이면서도 `main-only`, `1축 canary`, 원인귀속 보존 원칙을 유지한다. |
| 결정 결과 | 채택. `score/promote`가 아니라 `buy_recovery_canary prompt` 재교정 1축을 적용했다. |
| 선정 이유 | `recovery_check=21`, `promoted=0`, `submitted=0` 조합은 score 임계치 전역 완화보다 recovery 전용 해석 문맥 보정이 더 직접적인 수단이라고 판단했다. |
| 장후 재판정 요약 | 오후 스냅샷 기준 `total_candidates=246`, `recovery_check=40`, `promoted=6`, `submitted=0`, `blocked_ai_score=208건(84.6%)`, `gatekeeper_eval_ms_p95=16637ms`, `gatekeeper_decisions=37`, `full_fill=0`, `partial_fill=0`, `completed_trades=0`이다. |
| 현재 해석 1 | `promoted=0 -> 6`으로 바뀐 것은 분명히 좋은 신호다. 즉, 프롬프트 재교정이 `WAIT65~79` 구간을 전부 묶어두던 상태는 일부 풀었다. |
| 현재 해석 2 | 하지만 `submitted=0`, `completed_trades=0`이라 아직 `BUY 회복 성공`으로 부를 수는 없다. 회복 BUY 후보가 생긴 것과 실제 주문/체결 회복은 아직 분리되어 있다. |
| 현재 해석 3 | `blocked_ai_score=208건(84.6%)`가 여전히 절대다수라서, BUY 신호 자체가 충분히 살아났다고 보기도 어렵다. 현재는 `0 -> 소폭 회복`에 가깝고, 여전히 AI threshold 병목이 크다. |
| 현재 해석 4 | 동시에 제출 병목도 남아 있다. `budget_pass_candidates=10`, `latency_block_candidates=10`, `submitted_candidates=0`이라 `BUY 후보 생성` 다음 단계에서 또 막힌다. 즉 병목은 `BUY 부족`과 `BUY -> submitted 단절`이 함께 존재한다. |
| 장중 후속 판정 업데이트 | `2026-04-23 11:03 KST` snapshot 기준 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`다. `wait6579`도 `recovery_check=20`, `promoted=13`, `budget_pass=15`, `latency_block=15`, `submitted=0`이라 오전 방향성은 `BUY 부족`이 아니라 `BUY는 충분하나 entry_armed 이후 병목`으로 바뀌었다. |
| 현재 해석 5 | 따라서 `DF-ENTRY-002`는 이제 “BUY 후보를 못 만든다” 문제를 보는 축이 아니라, upstream 표본 생성은 유효했고 다음 live 주연은 downstream 제출축으로 넘어갔다는 기준점 역할을 한다. `buy_recovery_canary`는 종료가 아니라 유지/고정이다. |
| 현재 해석 6 | `blocked_ai_score_share`와 `score/promote` 해석은 보조가설로 남지만, 당장 다음 canary 우선순위는 아니다. 다시 말해 `DF-ENTRY-002`의 성공 기준은 `BUY 부족 해소 여부`까지이고, `submitted/full/partial` 회복은 후속 제출축에서 본다. |
| 현재 상태 | upstream 고정 상태다. `BUY 후보 자체 부족`보다는 downstream 제출/체결 품질이 주병목이라는 결론이 유지된다. |
| 가드 해석 | `latency_p95=16637ms`는 임계치(`15900ms`)를 넘지만 `gatekeeper_decisions=37`이라 가드 발동 조건인 `sample >= 50`을 아직 못 채웠다. 따라서 hard OFF 근거는 아니고 방향성 경고로만 본다. |
| 오늘 결론 | `현 축 유지 + upstream 고정`이 맞다. 지금 OFF하면 BUY drought 완화 입력이 사라지고, 지금 다른 upstream 축으로 넘어가면 `prompt 개선`, `AI threshold`, `제출 병목`의 원인귀속이 다시 흐려진다. |
| 실패 시 해석 | 이후 관측에서 `ai_confirmed/entry_armed`가 다시 줄거나 `blocked_ai_score_share`가 재악화되면 upstream 문제 재개로 본다. 반대로 `promoted/entry_armed`가 유지되는데 `submitted`만 낮으면 핵심 병목은 계속 제출 경로(latency/quote)다. |
| 다음 확인 포인트 | `ai_confirmed`, `entry_armed`, `promoted`, `submitted`, `submission_blocker_breakdown`, `quote_fresh_latency_blocks`, `full/partial`, `COMPLETED + valid profit_rate`, `latency_p95`를 같은 기준으로 다시 본다. |

### DF-ENTRY-003 `entry_armed -> submitted` latency/quote 제출축 분해

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-003` |
| 판정항목 | `entry_armed -> submitted` 구간의 `latency/quote freshness` 병목을 다음 공식 live/판정축으로 올릴지 여부 |
| 문제 인식 | 현재는 BUY 후보가 부족해서가 아니라, `entry_armed`와 `budget_pass`를 거친 뒤에도 대부분이 `submitted`로 가지 못한다. 같은 날 `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`이면 병목의 중심은 제출 직전이다. |
| 왜 다음 축인가 | upstream인 `DF-ENTRY-002`가 `recovery_check/promoted/entry_armed` 표본을 이미 만들고 있기 때문이다. 이제 기대값을 더 올리려면 `BUY를 더 만들까`보다 `만들어진 후보가 왜 주문 직전에서 잘리는가`를 먼저 분해해야 한다. |
| 분해 대상 1 | `quote_fresh latency block` 자체의 비중이 높은지 확인한다. 즉 stale quote가 아닌데도 내부 지연/guard 조건 때문에 잘리는 표본을 따로 본다. |
| 분해 대상 2 | `gatekeeper_eval_ms_p95`, `gatekeeper_lock_wait_ms`, `gatekeeper_model_call_ms`, `gatekeeper_total_internal_ms`, `gatekeeper_fast_reuse_ratio`, `gatekeeper_ai_cache_hit_ratio`를 함께 봐서 병목이 모델응답인지, lock 직렬화인지, cache miss인지 분리한다. |
| 분해 대상 3 | `ws_age`, `ws_jitter`, `spread_ratio`, `quote_stale`가 어떤 조합에서 `latency_block`을 만드는지 구간화한다. 핵심은 `fresh quote인데도 막힌 표본`과 `실제 stale quote 차단`을 섞지 않는 것이다. |
| 현재 제약 | 기존 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 더 이상 fallback 주문으로 이어지지 않고 `latency_fallback_deprecated` reject trace만 남긴다. 따라서 남은 제약은 fallback 재개가 아니라 `1축 canary` 교체 순서, 복합축 묶음 판정, same-day live 검증이다. |
| 정의 가능 시점 | 장후가 되어서가 아니라, 아래 사전조건 3개가 채워지는 시점부터 정의 가능하다. 현재는 1, 2번은 충족됐고, 3번도 `spread relief canary` 구현으로 코드 레벨에선 충족됐다. 남은 것은 live ON/OFF와 장중 검증 기록이다. |
| 사전조건 1 | 문제 구간이 `BUY 부족`이 아니라 `entry_armed/budget_pass 이후 submitted 단절`로 잠겨 있어야 한다. 오늘은 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `latency_block_events=1891`이라 이 조건은 충족으로 본다. |
| 사전조건 2 | 분해용 관측값이 live 로그/스냅샷에 존재해야 한다. 즉 `quote_fresh_latency_blocks`, `gatekeeper lock_wait/model_call/total_internal`, `ws_age/ws_jitter/spread/quote_stale` 중 최소 핵심 필드가 이미 기록돼 있어야 한다. 오늘은 PREOPEN/INTRADAY에서 이 계측 경로가 확인돼 있어 충족으로 본다. |
| 사전조건 3 | 실전에서 ON/OFF 가능한 조작점이 `fallback`과 분리된 단일 행동으로 정의돼야 한다. 예를 들면 `reason allowlist만 조정`, `quote_stale=False cohort만 별도 처리`, `ws_jitter 한도만 조정`처럼 효과와 리스크를 한 문장으로 설명할 수 있어야 한다. 현재는 이 조작점이 아직 문서/코드로 고정되지 않아 미충족이다. |
| 정의 기준 1 | 축 설명이 `무엇을 완화/조정하는가` 한 문장으로 닫혀야 한다. `latency를 개선한다`처럼 넓은 표현은 불가하고, `fresh quote + ws_jitter 상한 재조정`처럼 단일 행동이어야 한다. |
| 정의 기준 2 | 기대효과가 `budget_pass_to_submitted_rate` 또는 `quote_fresh_latency_pass_rate` 개선처럼 제출축 지표로 직접 연결돼야 한다. `BUY 수 증가` 같은 upstream 효과를 주 KPI로 삼으면 안 된다. |
| 정의 기준 3 | rollback guard가 최소 3개는 같이 붙어야 한다. 기본형은 `loss_cap`, `submitted/full/partial 품질 악화`, `fallback_regression=0 유지`다. 필요하면 `latency_p95` 또는 `reject_rate`를 추가한다. |
| 정의 기준 4 | 금지 조건이 명시돼야 한다. `fallback_scout/main`, `fallback_single`, `ALLOW_FALLBACK` 재유입, 전역 threshold 하향, 다축 동시 변경은 정의 단계에서 제외한다. |
| 지금 바로 할 수 있는 일 | blocker 분해뿐 아니라 `spread-only + quote fresh` 케이스 전용 `fallback 비결합 canary`를 코드에 넣고, 테스트까지 통과시킨 뒤 남은 장에서 live 검증할 수 있다. |
| 지금 바로 못 하는 일 | 다축 동시 ON 상태에서 downstream 효과를 검증할 수는 없다. same-day live는 `기존 축 OFF -> restart.flag -> 새 축 ON` 교체 규칙을 지켜야 하고, fallback 관련 플래그는 재사용하면 안 된다. |
| 결정 결과 | 다음 공식 판정축으로 등록했고, 장중에 `fallback 비결합 spread relief canary` 구현까지 완료했다. 남은 단계도 `장중 정량 checkpoint -> same-day 유지/확대/롤백` 판정이어야 하며, `POSTCLOSE에서 첫 제출/체결 품질만 보고 닫는 방식`은 허용하지 않는다. |
| 현재 상태 | 제출축 분해 작업은 완료됐고, active owner는 더 이상 이 섹션이 아니다. 결과적으로 `DF-ENTRY-007 mechanical_momentum_latency_relief`와 그 이후 HOLDING 품질 판정으로 넘어갔다. |
| 장중 1차 분해 결과 | `2026-04-23 11:21:13 KST` snapshot 기준 `budget_pass_events=2091`, `order_bundle_submitted_events=2`, `latency_block_events=2089`, `quote_fresh_latency_blocks=1882`, `quote_fresh_latency_pass_rate=0.1%`다. raw log 228건 집계에서는 `quote_stale=False 203건`, `quote_stale=True 25건`으로 fresh quote 차단이 우세했고, danger reason overlap은 `spread_too_wide 177`, `ws_age_too_high 42`, `ws_jitter_too_high 36`, `quote_stale 25`, `other_danger 22`였다. |
| gatekeeper 해석 보정 | gatekeeper reject 실표본은 오늘 `2건`뿐이며 `gatekeeper_lock_wait_ms=0`, `gatekeeper_model_call_ms≈total_internal_ms`, `gatekeeper_cache=miss`였다. 즉 느린 것은 맞지만, 현재 `entry_armed -> submitted` 대량 단절의 1차 설명력은 `fresh quote spread 지배`보다 약하다. |
| 단일 조작점 후보 1 | 첫 `fallback 비결합 downstream 1축` 후보는 `quote_stale=False + spread_too_wide 지배 구간 분리`다. 핵심은 전역 latency 완화가 아니라 fresh quote spread 구간을 별도 cohort로 떼어 `budget_pass_to_submitted_rate` 개선 가능성을 보는 것이다. |
| 장중 구현 반영 | [sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/engine/sniper_entry_latency.py)에 `_should_apply_latency_spread_relief_canary()`를 추가해 `REJECT_DANGER -> ALLOW_NORMAL` 직접 override 경로를 넣었다. 설정축은 [constants.py](/home/ubuntu/KORStockScan/src/utils/constants.py)의 `SCALP_LATENCY_SPREAD_RELIEF_CANARY_ENABLED`, `..._TAGS`, `..._MIN_SIGNAL_SCORE`, `..._MAX_SPREAD_RATIO`다. 혼합 danger(`ws_age/ws_jitter/quote_stale` 동반)는 계속 차단한다. |
| 테스트 상태 | [test_sniper_entry_latency.py](/home/ubuntu/KORStockScan/src/tests/test_sniper_entry_latency.py) 기준 `spread-only danger -> ALLOW_NORMAL`, `mixed danger -> 차단 유지`를 포함해 `10 passed`다. |
| 후속 액션 | 남은 장에서는 기존 live 축을 끈 뒤 `spread relief canary`만 켜서 `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `submitted/full/partial fill quality`, `fallback_regression=0`를 본다. 장후 checklist의 `LatencyOps0423 gatekeeper latency 경로 분해(lock/cache/quote_fresh)`는 새 구현의 live 결과까지 포함해 `유지/확대/롤백`을 닫는 단계로 쓴다. |

### DF-ENTRY-004 `spread relief canary` 오전 판정 결과

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-004` |
| 판정항목 | `2026-04-24 09:00~10:30 KST` `spread relief canary` 실효성 판정 |
| 검증축 이름 | `spread relief canary` 오전 판정 |
| 왜 이 축인가 | `DF-ENTRY-002`가 upstream 표본 생성은 이미 확보했기 때문에, 오늘 오전의 핵심은 `BUY를 더 만들까`가 아니라 `entry_armed -> submitted` 제출축에서 `spread relief canary`가 실제 blocker를 줄였는지 확인하는 것이었다. |
| 검증 목적 | `spread-only + quote fresh` 완화가 `budget_pass_to_submitted_rate`, `quote_fresh_latency_pass_rate`, `submitted/full/partial fill quality`를 개선하는지 same-day로 닫는다. |
| 검증 대상 지표 | `ai_confirmed`, `entry_armed`, `budget_pass`, `submitted`, `latency_block`, `latency_state_danger`, `latency_danger_reasons`, `latency_canary_reason`, `quote_fresh_latency_blocks`, `quote_fresh_latency_pass_rate`, `full_fill`, `partial_fill` |
| 보조 진단 지표 | `gatekeeper_fast_reuse`, `gatekeeper_eval_ms_p95`는 AI 평가 지연/재사용 경로 진단용으로만 본다. `budget_pass -> latency_block -> submitted` 직접 blocker보다 우선하는 live 축으로 올리지 않는다. |
| 10:00 KST 판정 | `09:00~10:00` 누적 `ai_confirmed=77`, `entry_armed=31`, `submitted=4`, `budget_pass_events=863`, `latency_block_events=859`, `quote_fresh_latency_blocks=777`, `quote_fresh_latency_pass_rate=0.5%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12543.0ms`였다. 따라서 원인 축은 `upstream BUY 부족`이 아니라 `budget_pass -> latency_block/submitted` downstream 단절로 고정했다. |
| 10:30 KST 재판정 | `09:00~10:30` 누적 `ai_confirmed=91`, `entry_armed=39`, `submitted=8`, `budget_pass_events=1220`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`, `quote_fresh_latency_pass_rate=0.7%`, `full_fill=0`, `partial_fill=0`, `gatekeeper_eval_ms_p95=12485.0ms`였다. `10:20~10:30` 증분에서도 `spread_only_required=82`가 차단사유 대부분이었다. |
| 오늘 판정 | `spread relief canary`는 원인 위치를 downstream으로 잠그는 데는 성공했지만, 실효성 승인에는 실패했다. 즉 `제출축 병목 위치 확인`은 됐고, `실제 제출 회복 효과`는 오전 표본에서 입증하지 못했다. |
| 현재 상태 | 종료 상태다. 병목 위치 확인용 historical 판정으로 남기고, 현재 live entry 판단에는 쓰지 않는다. |
| why 1 | `submitted_orders=8`로 Plan Rebase §6 `N_min` 최소치 `20`에 `+12`가 부족하다. 따라서 hard pass/fail을 줄 표본은 없다. |
| why 2 | 표본 미달과 별개로 `budget_pass_events=1220` 대비 `submitted=8`, `latency_block_events=1212`, `quote_fresh_latency_blocks=1092`라서 downstream 차단이 지배적이라는 방향성은 충분히 강하다. |
| why 3 | `gatekeeper_eval_ms_p95`는 `12.5s` 수준으로 높지만 rollback guard(`>15,900ms`, sample>=50)까지는 아니다. 따라서 immediate rollback 사유도 아니다. |
| 금지 유지 | 이 결과만으로 `entry_filter_quality`, `score/promote`, `HOLDING`, `EOD/NXT`를 같은 오전 창의 주병목 축으로 올리면 안 된다. 원인귀속이 다시 upstream으로 흔들리기 때문이다. |
| 후속 연결 | same-day 보조축은 `quote_fresh` downstream 1축으로 고정했고, `entry_filter_quality`는 parking 유지로 남겼다. 이후 `spread/ws_jitter/other_danger residual`을 차례로 봤지만, direct 제출 회복은 만들지 못했다. 따라서 다음 연결은 `gatekeeper_fast_reuse`가 아니라 `latency_state_danger` 하위원인 재분해로 넘어간다. |

### DF-ENTRY-005 `latency_state_danger` 직접 병목 pivot

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-005` |
| 판정항목 | `budget_pass -> latency_block -> submitted` 단절의 직접 blocker를 `latency_state_danger` 하위 이유로 재고정하고, live 축을 `other_danger relief`로 넘길지 결정 |
| 매몰 지점 | `quote_fresh family`가 효과 미약으로 잠긴 뒤 `gatekeeper_fast_reuse`를 다음 독립축 후보로 올린 것이 흐름을 옆길로 틀었다. `gatekeeper_eval_ms_p95`와 `fast_reuse_ratio=0.0%`는 지연 진단에는 유효하지만, `latency_block` 직접 원인보다 우선하는 제출 회복축은 아니었다. |
| 피벗 잠금 | `SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=True` 상태에서 `13:00` 즉시 재점검이 최우선이다. 이 창에서는 `submitted/full/partial`, `latency_block`, `latency_state_danger`를 먼저 보고 `gatekeeper_fast_reuse_ratio`는 보지 않는다. `SCALP_LATENCY_OTHER_DANGER_RELIEF_CANARY_ENABLED=False` 또는 미동작이면 판정은 미루고 `LatencyCarry0427`의 offload 대상로 넘긴다. |
| 폐기된 보조가설 | `2026-04-24`에는 `window`보다 `signature_changed`가 더 많다는 이유로 `signature-only` deadband를 시도했다. 하지만 `2026-04-27 10:00~11:00`에도 `gatekeeper_fast_reuse_ratio=0.0%`, `budget_pass_to_submitted_rate=0.2%`가 유지돼 live 제출 회복축으로는 닫았다. |
| 11:31 same-day 종료 판정 | raw 재집계 기준 `latency_block=3196`, `latency_state_danger=3000`이었고 내부 분해는 `other_danger=1218`, `ws_jitter-only=869`, `spread-only=257` 순이었다. `other_danger` 단일 케이스 1427건 중 `latency_canary_reason=low_signal`가 `1079건`이라, 남은 기대값 개선 여지는 `latency_state_danger -> other_danger relief` 쪽이 가장 직접적이었다. |
| 현재 해석 | `entry_armed -> budget_pass`는 계속 병목이 아니고, `budget_pass -> latency_block -> submitted`가 주병목이다. 이 구간의 우선 KPI는 `submitted/full/partial`, `latency_state_danger`, `latency_danger_reasons`, `latency_canary_reason`, `other_danger relief applied`다. |
| 현재 상태 | pivot 설명 역할은 완료됐다. `other_danger/ws_jitter/spread` 단일축은 모두 종료됐고, 현재 live owner는 `mechanical_momentum_latency_relief`로 잠겼다. |
| 코드 반영 상태 | `SCALP_LATENCY_OTHER_DANGER_RELIEF_MIN_SIGNAL_SCORE`를 `90.0 -> 85.0`으로 낮춰 `other_danger relief`의 `low_signal` 병목을 바로 완화했다. `85.0 통과 / 84.9 차단` 회귀 테스트도 추가했다. |
| 13:00 장중 판정 | offline bundle `latency_1300` 기준 `budget_pass=5628`, `submitted=9`, `budget_pass_to_submitted_rate=0.2%`, `latency_block=5619`, `latency_state_danger=5290`, `full_fill=4`, `partial_fill=0`이었다. `11:00` 대비 absolute `submitted/full_fill`는 늘었지만 비율 개선이 없고 `latency_state_danger` 비중도 유지 또는 악화돼, `other_danger-only normal override` 효과를 유의미한 제출 회복으로 보지는 않는다. |
| 15:00 장중 판정 | offline bundle `ws_jitter_1500` 기준 `budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_block=7557`, `latency_state_danger=7178`, `full_fill=7`, `partial_fill=0`이었다. `13:00` 대비 absolute `submitted/full_fill`는 늘었지만 효율 비율은 악화됐고 danger 분해도 `other_danger=3256`, `ws_age_too_high=2224`, `ws_jitter_too_high=2203` 순으로 유지돼 `ws_jitter-only relief`도 제출 회복축으로는 닫았다. |
| 금지 조건 | `gatekeeper_fast_reuse_ratio` 개선, `gatekeeper_eval_ms_p95` 하락, signature/window blocker 감소만으로 live 승격/유지 판정을 하지 않는다. 이 값들은 `submitted/full/partial` 또는 `latency_state_danger` 감소와 함께 움직일 때만 보조 근거로 쓴다. `other_danger-only normal override` 적용 후에도 `submitted` 개선이 없다면 `gatekeeper_fast_reuse`로 판정을 되돌리지 않는다. |
| 복합축 적용 | 단일 `gatekeeper_fast_reuse`, `other_danger-only normal override`, `ws_jitter-only relief replacement`는 모두 same-day latency residual 평가축으로 종료됐다. 이후 `latency_quote_fresh_composite`를 live로 열었지만 `2026-04-29 08:29 KST` OFF + restart로 닫혔고, `latency_signal_quality_quote_composite`도 `2026-04-29 12:21~12:50 KST` replacement 후 후보 0건으로 종료됐다. 현재 entry live 축은 `mechanical_momentum_latency_relief`다. 조건은 `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, fallback/split-entry 금지, normal override만 허용이다. |
| fallback/split-entry 정합화 | `CAUTION -> ALLOW_FALLBACK`은 더 이상 실전 주문 경로를 만들지 않도록 `latency_fallback_deprecated` reject로만 남긴다. split-entry follow-up shadow도 기본 OFF로 두고, runtime에서 재개 후보처럼 읽히는 문구를 제거한다. 남는 것은 과거 로그/감리용 helper와 폐기 경로 감지뿐이다. |
| 다음 액션 | 이후 판정은 `quote_fresh_composite_canary_applied`, `submitted/full/partial`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `normal_slippage_exceeded`, `COMPLETED + valid profit_rate`로 닫는다. `gatekeeper_fast_reuse_ratio`는 계속 보조 진단값이고, `other_danger/ws_jitter/spread` 단일축으로 되돌아가지 않는다. |

### DF-ENTRY-006 `latency_quote_fresh_composite` 복합축 live canary

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-006` |
| 판정항목 | `latency_quote_fresh_composite`를 entry live canary로 독립 관리하고, 개별 파라미터가 아니라 묶음 ON/OFF 효과로만 판정할지 결정 |
| 문제 인식 | `other_danger-only`, `ws_jitter-only`, `spread-only`, `gatekeeper_fast_reuse` 단일/보조축은 모두 same-day 제출 회복 실패로 종료됐다. 남은 blocker는 `ws_age/ws_jitter/spread/quote_stale/low_signal`이 quote freshness family로 겹치는 복합 구간일 가능성이 가장 높다. |
| 왜 별도 ID인가 | 이 축은 단일 threshold 완화가 아니라 `signal`, `ws_age`, `ws_jitter`, `spread`, `quote_stale`를 한 묶음 가설로 잠그는 active entry canary다. 따라서 `DF-ENTRY-005`의 pivot 설명 안에 문장으로만 두면, `pivot`과 `실제 live canary`가 같은 항목으로 섞여 판정 추적이 끊긴다. |
| live 정의 | `signal>=88`, `ws_age<=950ms`, `ws_jitter<=450ms`, `spread<=0.0075`, `quote_stale=False`, `fallback/split-entry 금지`, `normal override만 허용`을 1개 묶음으로 적용한다. |
| 판정 원칙 | `signal/ws_age/ws_jitter/spread/quote_stale`를 개별 독립축으로 재해석하지 않는다. 오직 `latency_quote_fresh_composite` 전체 ON/OFF 효과만 본다. |
| 기준선 | primary baseline은 같은 bundle 내 `quote_fresh_composite_canary_applied=False`, `normal_only`, `post_fallback_deprecation` 표본이다. `ShadowDiff0428`이 닫히기 전까지는 이 기준선을 hard baseline으로 승격하지 않고, `2026-04-27 15:00 offline bundle`(`budget_pass=7568`, `submitted=11`, `budget_pass_to_submitted_rate=0.1%`, `latency_state_danger=7178`, `full_fill=7`, `partial_fill=0`)은 방향성 참고선으로만 쓴다. baseline 표본이 `N_min` 미달이면 hard pass/fail이 아니라 방향성 판정으로만 둔다. |
| 핵심 KPI | `submitted/full/partial`, `budget_pass_to_submitted_rate`, `latency_state_danger`, `normal_slippage_exceeded`, `COMPLETED + valid profit_rate` |
| 도달목표 | primary: `budget_pass_to_submitted_rate >= baseline +1.0%p` and `submitted_orders >= 20`. secondary: `latency_state_danger / budget_pass` 비율 `-5.0%p` 이상 개선 and `full_fill + partial_fill`의 `submitted` 대비 전환율 비악화. |
| 보조 진단 | `quote_fresh_composite_canary_applied`, `latency_canary_reason`, `other_danger/ws_age/ws_jitter/spread` 분해는 보조 설명용이다. 이 값들만으로 유지/종료를 판정하지 않는다. |
| rollback guard | `budget_pass_to_submitted_rate`가 baseline 대비 `+1.0%p` 이상 개선하지 못하면 `composite_no_recovery`로 OFF한다. `full/partial` 품질 악화, `normal_slippage_exceeded` 증가, `fallback_regression` 재유입도 즉시 OFF 사유다. |
| 감리 검토 포인트 | baseline이 `same bundle + canary_applied=False`로 잠겼는지, `04-27 15:00 offline bundle`이 참고선으로만 분리됐는지, 성공 기준과 rollback guard가 뒤섞이지 않았는지, baseline 부족 또는 shadow diff 미해소 시 `direction-only`로 격하한다는 규칙이 문서에 남아 있는지를 같이 본다. |
| 금지 조건 | 같은 entry 단계에서 다른 canary를 동시에 두지 않는다. `other_danger/ws_jitter/spread` 단일축으로 되돌아가 개별 attribution을 시도하지 않는다. `gatekeeper_fast_reuse_ratio` 개선만으로 유지 판정을 하지 않는다. |
| 현재 상태 | historical/reference 축으로 전환됐다. `2026-04-29 08:29 KST` 기준 OFF + restart가 반영됐고, 현재는 active entry live canary가 아니다. |
| 후속 연결 | 제출 회복이 확인되지 않아 `latency_signal_quality_quote_composite` same-day replacement를 거쳤고, 다시 효과 미약으로 닫힌 뒤 `DF-ENTRY-007 mechanical_momentum_latency_relief`로 넘어갔다. |

### DF-ENTRY-007 `mechanical_momentum_latency_relief` 운영 override

| 항목 | 내용 |
| --- | --- |
| ID | `DF-ENTRY-007` |
| 판정항목 | `latency_quote_fresh_composite`와 `latency_signal_quality_quote_composite` 종료 후, AI 50/70 mechanical fallback 상태까지 포함해 제출 drought를 직접 완화하는 replacement 축을 same-day 운영 override로 관리 |
| 문제 인식 | `2026-04-29 12:21:28~12:45:59 KST` `latency_signal_quality_quote_composite` post-restart cohort는 `budget_pass=972`, `submitted=0`, 후보 통과 0건이었다. `signal>=90` 전제는 AI 50/70 fallback 상태를 열지 못해, submitted 회복 직접성이 낮았다. |
| live 정의 | `signal_score<=75`, `latest_strength>=110`, `buy_pressure_10t>=50`, `ws_age<=1200ms`, `ws_jitter<=500ms`, `spread<=0.0085`, `quote_stale=False`, fallback/split-entry 금지, normal override만 허용 |
| 왜 이 축인가 | 같은 post-restart 창 counterfactual 기준으로는 약 `91`건 후보가 보여, 기존 복합축이 버리던 `mechanical fallback` 표본을 제한적으로 열 수 있다. 즉 지금 필요한 것은 `high score only`가 아니라 `기계 fallback이라도 microstructure가 충분한 후보`를 살리는 것이다. |
| 판정 원칙 | hard baseline 승격이 아니라 same-day 운영 override다. 따라서 새 restart 이후 cohort만 분리해 보고, 기존 `h1200`이나 `QuoteFresh` historical cohort와 직접 합산하지 않는다. |
| 현재 상태 | 현재 entry live 1축이다. `2026-04-29 12:50 KST` ON 후 재기동 반영됐고, `2026-04-30 09:00~10:00` 기준 제출 회복 방향성은 확인됐지만 `submitted` 이후 체결/청산 품질은 별도 관찰 구간이다. |
| 핵심 KPI | `mechanical_momentum_relief_canary_applied`, `latency_mechanical_momentum_relief_normal_override`, `submitted`, `full fill`, `partial fill`, `COMPLETED + valid profit_rate`, `fallback_regression=0` |
| 14시 관찰 결과 | `12:57 restart -> 14:00` 고유 기준 `budget_pass=38`, `mechanical_unique=22`, `submitted=20`, `guard_block=2`, `order_failed=2`, `filled=7`이었다. `13:15 hotfix -> 14:00` 기준으로도 `budget_pass=32`, `submitted=17`, `filled=7`이라 제출 drought는 완화됐지만, fill quality와 청산 품질까지 baseline-lock 할 단계는 아니다. |
| 2026-04-30 최신 상태 | entry live owner 유지다. 오전 `09:00~10:00` 창에서 `budget_pass=951`, `submitted=27`, `mechanical_momentum_relief_canary_applied=22`, `full_fill=0`, `partial_fill=0`로 제출 회복 방향성은 확인됐다. 제출 이후 품질은 보유/청산 outcome과 분리해 본다. |
| rollback guard | post-restart cohort에서 `budget_pass >= 150`인데 `submitted <= 2`, `pre_submit_price_guard_block_rate > 2.0%`, `normal_slippage_exceeded` 반복, 또는 canary cohort 일간 손익이 NAV 대비 `<= -0.35%`이면 OFF 후보로 본다. |
| 다음 액션 | 5/4에는 제출 회복 자체보다 `full/partial`, `HOLDING -> exit_rule -> COMPLETED + valid profit_rate`로 BUY 신호 적정성을 본다. 신규 BUY 수량은 `1주 cap` 기준으로 고정하고, 수량 확대는 별도 승인 전에는 열지 않는다. |

## 제출축 판정 후 다음 단계

### DF-HOLDING-001 `submitted 증가 이후 HOLDING/청산 품질 판정`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-001` |
| 시작 조건 | `mechanical_momentum_latency_relief` 또는 후속 downstream 1축에서 `submitted` 회복이 확인된 뒤 hard pass/fail을 시작한다. |
| 현재 상태 | `latency_quote_fresh_composite`는 OFF, `latency_signal_quality_quote_composite`는 후보 0건으로 종료됐고 현재 entry live는 `mechanical_momentum_latency_relief`다. 따라서 HOLDING/청산 hard pass/fail의 선결조건은 과거 `quote_fresh`가 아니라 현 live replacement 축의 `submitted/full/partial` 회복 여부다. 다만 동일 단계 원칙상 entry live 1축과 보유/청산 `soft_stop_micro_grace`는 여전히 분리 병렬 canary로 운용할 수 있다. |
| 다음 단계 목적 | 제출량 증가가 실제 기대값 개선으로 이어지는지 `HOLDING/청산 품질`로 검증한다. 단, 진입 조건은 `submitted` 회복이 먼저다. |
| 핵심 검증축 | `soft_stop/trailing/good_exit`, `holding_action_applied`, `holding_force_exit_triggered`, `exit_rule` 분포, `full/partial` 분리, `COMPLETED + valid profit_rate` |
| 분리 원칙 | `initial-only`와 `pyramid-activated` 표본을 섞지 않는다. `full fill`과 `partial fill`도 합치지 않는다. |
| 수량정책 메모 | `2026-04-28~29`에는 `1주 cap -> PYRAMID zero_qty` 왜곡을 줄이기 위해 임시 `2주 cap`을 시험했다. 그러나 `2026-04-30` 장후 기준 신규 BUY exposure와 holding/exit 원인귀속 오염을 더 우선해 `SCALPING_INITIAL_ENTRY_MAX_QTY=1`로 되돌린다. |
| 1주 cap 최신 메모 | `2026-04-30` 장후 사용자 지시로 최대매수가능 주수를 `1주`로 고정한다. 2주 cap의 과거 관찰값(`initial_entry_qty_cap_applied=38`, `zero_qty=0`, `pyramid_activated=3`)은 historical reference로만 남기고, 다음 운영일에는 `cap_qty=1`, `initial-only`, `REVERSAL_ADD floor`, `PYRAMID zero_qty`를 새 baseline으로 다시 분리한다. |
| 성공 판정 | 제출 증가와 함께 체결 품질/청산 품질 악화가 없고 `COMPLETED + valid profit_rate`가 유지 또는 개선 |
| 실패 판정 | 제출 증가 대비 `soft_stop` 급증, `full_fill` 악화, `COMPLETED + valid profit_rate` 악화 동반 |
| 다음 액션 | `soft_stop_micro_grace`는 현 baseline live로 유지한다. 다음 신규 보유/청산 조작점은 v2 재가동이 아니라 `bad_entry_refined_canary`이며, 5/4 장전에는 로드/override/cohort 확인만 남긴다. |
| 현재 상태 | 선결조건 충족 후 active 단계다. 현재 holding/exit live owner는 `soft_stop_micro_grace`이며, `soft_stop_expert_defense v2`는 2026-04-30 수집 종료 후 기본 OFF다. 다음 신규 후보는 refined `bad_entry` canary다. |
| Source | [2026-04-24-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-24-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

### DF-HOLDING-002 `soft_stop 1차 live canary` 판정 흐름

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-002` |
| 판정항목 | `2026-04-27` 보유/청산 1차 live canary를 `soft_stop_rebound_split` 중심으로 볼지 여부 |
| 문제 인식 | 4월 누적 기준 손익 훼손은 trailing 조기익절보다 soft stop 손실축이 더 직접적이다. `2026-04-24` 생성 리포트 기준 `scalp_soft_stop_pct completed_valid=53`, 평균 `-1.669%`, 실현손익 `-651,680원`이고, `scalp_trailing_take_profit completed_valid=54`, 평균 `+1.041%`, 실현손익 `+280,742원`이다. |
| 추가 가설 | soft stop이 정상 손절이 아니라 휩쏘에 걸리는 케이스가 많을 수 있다. 즉 soft stop 시점에는 손절가를 찍었지만, 이후 1~10분 안에 매도가를 재상회하거나 +0.5~1.0% 이상 되돌리는 표본이 많으면 soft stop을 단순 유지하기보다 confirmation/micro grace 후보로 봐야 한다. |
| 기존 로그 재집계 | 4월 post-sell 평가의 `scalp_soft_stop_pct` 61건 기준, 10분 내 매도가 재상회는 57건(`93.4%`), 10분 내 +0.5% 이상 반등은 43건(`70.5%`), +1.0% 이상 반등은 23건(`37.7%`), 매수가 회복은 16건(`26.2%`)이다. 이는 `soft_stop whipsaw` 가설을 별도 검증축으로 둘 근거가 된다. |
| 왜 1순위인가 | trailing은 놓친 추가상승을 줄이는 upside capture 축이고, soft stop은 이미 실현된 손실을 줄이는 downside leakage 축이다. 기대값 관점에서는 우선 손실 기대값이 큰 soft stop을 먼저 좁혀야 한다. |
| 동시 canary 해석 | 현재 진입병목 축은 `latency_state_danger -> other_danger relief`이고 soft stop은 보유/청산 축이다. 조작점, 적용 시점, cohort tag, rollback guard가 완전히 분리되면 stage-disjoint concurrent canary로 병렬 검토할 수 있다. 단, 두 축이 같은 주문 흐름을 공유하므로 성과판정은 hard pass/fail이 아니라 provisional로 둔다. |
| 1차 canary에서 얻고 싶은 것 | soft stop 자체를 무조건 늦추는 것이 아니라, “진짜 손절해야 할 하락”과 “짧은 V-shape/휩쏘 반등을 잘라버리는 손절”을 분리할 수 있는지 확인한다. |
| 기대효과 1 | soft stop 손실 평균과 실현손익 하방 tail을 줄인다. 즉 제출이 회복될 때 손실 표본이 같이 늘어나는 것을 조기에 막는다. |
| 기대효과 2 | `rebound_above_buy_10m`가 높은 경우에는 cooldown live를 금지하고 threshold/AI 재판정 후보로 넘겨, 반등을 놓치는 역효과를 피한다. |
| 기대효과 3 | `same_symbol_reentry_loss_count`가 높은 경우에는 같은 종목 저품질 재진입을 줄이는 후보를 만들 수 있다. 이 경우 기대효과는 손실 회피와 재진입 비용 절감이다. |
| 기대효과 4 | 10시 중간점검과 11시 1차 판정으로 오염을 조기에 잡는다. cohort tag 혼선, fallback 회귀, soft stop 전환율 급증, 매도 실패가 보이면 장후까지 끌지 않고 OFF 후보로 올린다. |
| 기대효과 5 | 휩쏘 표본이 live에서도 유지되면 `soft_stop confirmation/micro grace`라는 더 직접적인 조작점으로 좁힐 수 있다. 반대로 반등 없이 계속 하락하는 표본이 우세하면 soft stop 완화가 아니라 진입 품질/손절 threshold 재판정으로 넘긴다. |
| 금지 조건 | `partial fill`, `pyramid-activated`, `EOD/NXT`, `fallback` 경로와 합산하지 않는다. soft stop cooldown을 전역 적용하지 않고 qualifying cohort 1개로만 제한한다. |
| 10시 중간점검 | `2026-04-27 10:00~10:10 KST`에는 pass/fail이 아니라 조기 오염을 본다. `soft_stop qualifying cohort`, `submitted/full/partial/completed_valid`, `fallback_regression=0`, 진입 canary와 cohort tag 분리 여부, `rebound_above_sell_1m/3m`, `mfe_ge_0_5`를 먼저 잠근다. |
| 11시 1차 판정 | `2026-04-27 11:00~11:15 KST`에는 `유지/축소/OFF/판정유예` 중 하나로 잠근다. `COMPLETED + valid profit_rate >= 10` 전에는 hard pass/fail이 아니라 방향성 판정으로만 두며, `rebound_above_sell_10m`, `rebound_above_buy_10m`, `mfe_ge_0_5`, `mfe_ge_1_0`로 휩쏘 여부를 같이 본다. |
| 15시 최종 선택 | `soft_stop qualifying cohort`는 `micro grace`로 승인한다. 기본값은 `enabled=True`, `grace_sec=20`, `emergency_pct=-2.0`이며, hard stop `-2.5%`는 그대로 둔다. soft stop 최초 터치 후 20초 안에 emergency를 넘지 않으면 `soft_stop_micro_grace`로 지연하고, 회복 시 grace state를 제거한다. |
| 2026-04-29 표본 보정 | `올릭스(226950)`은 `GOOD_EXIT`, `덕산하이메탈(077360)`은 `NEUTRAL`, `지앤비에스 에코(382800)`는 `MISSED_UPSIDE`이며 soft stop 후 고가 재진입 체결과 익절이 확인됐다. `코오롱(002020)`은 `GOOD_EXIT`지만 soft stop 후 고가 재진입 제출이 있었다. 따라서 지금 결론은 `micro grace 유지 + recovery recapture 라벨/로그 필요성 관찰`이지, 즉시 `soft_stop_micro_grace_extend` ON이 아니다. |
| 현재 상태 | `soft_stop_micro_grace` 자체는 유지다. `soft_stop_expert_defense v2`는 `2026-04-30 12:00~15:30 KST` 수집 축으로만 운용했고, 다음 재승인 전에는 v1 micro grace 단독 기준으로 돌아간다. |
| trailing과의 관계 | `trailing_continuation_micro_canary`는 2순위다. `MISSED_UPSIDE rate >= 60%`, `GOOD_EXIT rate <= 30%`를 충족하고 soft stop 축이 오염되지 않을 때만 다음 후보로 다시 연다. |
| Source | [2026-04-27-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-27-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

### DF-HOLDING-003 `REVERSAL_ADD + bad_entry_block` 전략 분리

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-003` |
| 문제 인식 | soft stop 감소를 `20초 안에 회복하길 기다린다`로만 접근하면 전략 가설이 약하다. 같은 soft stop 후보라도 `진입은 유효했지만 초반 눌림이 과도한 케이스`와 `처음부터 never-green/AI fade였던 불량 진입`은 다른 처리가 필요하다. |
| active canary | `REVERSAL_ADD`: `-0.70%~-0.10%`, 보유 20~180초, AI 회복, 저점 미갱신, 매수압/틱가속/micro VWAP 조건을 통과한 경우 1주 소형 추가매수로 평단 회수를 실험한다. `2026-04-30` 오전에는 0체결이었고 원인은 축 미적용이 아니라 임계 과협착으로 판정했다. |
| observe-only classifier | `bad_entry_block`: 보유 60초 이상, 손익 `<= -0.70%`, peak `<= +0.20%`, AI score `<=45`인 never-green 후보를 `bad_entry_block_observed`로 남긴다. 현재는 표본 부족이 아니라 단순 차단의 precision 부족이 문제다. |
| rollback guard | `REVERSAL_ADD` 체결 후 soft stop/hard stop으로 이어지거나, 체결 cohort 평균 손익이 `<= -0.30%`이면 OFF 후보로 본다. |
| 승격 조건 | `bad_entry_block_observed`가 최소 10건 이상 누적되고 후속 손실 전환이 높으며 `GOOD_EXIT/MISSED_UPSIDE` 놓침 위험이 낮을 때만 별도 live block canary로 연다. 현재 표본은 이 조건 중 손실 전환은 충족했지만 winner 제거 위험이 남아 refined rule로만 승격한다. |
| 현재 상태 | `REVERSAL_ADD`는 threshold widen 후에도 `reversal_add_used=0` 상태다. 다만 이는 parking 근거가 아니라 `실행조건 탐색이 아직 덜 끝난 상태`로 해석한다. raw 로그 기준 blocker는 `pnl_out_of_range`와 `hold_sec_out_of_range`가 대부분이고, 기존 `candidate_ready`에는 `hold_sec`가 빠져 있어 실행 불가능 후보가 섞여 있었다. `bad_entry_block`은 observed unique `32`, 후행 sell completed `30`, 후보 평균 `-0.961%`, 손실 `22/30`, soft stop `20/30`으로 신호성은 충분하다. 단 `GOOD_EXIT=13`이 있어 naive block은 EV를 훼손할 수 있다. `2026-04-30` 장후에는 `held_sec>=180`, `profit_rate<=-1.16`, `peak_profit<=+0.05`, `AI<=45`, `recovery_prob_shadow<=0.30` 또는 thesis/adverse 확인 조건으로 `scalp_bad_entry_refined_canary` 구현과 테스트를 완료했다. |
| 다음 액션 | 5/4 장전에는 신규 설계가 아니라 `SCALP_BAD_ENTRY_REFINED_CANARY_ENABLED=True`, `soft_stop_expert_defense=False`, `bad_entry_refined_candidate/exit` stage 적재와 env override 오염 여부만 확인한다. `REVERSAL_ADD`는 parking하지 않고 `pnl/hold/gate` 실행 blocker를 계속 좁힌다. 후보 전이에 `hold_sec`를 포함해 false candidate를 제거하고, `reversal_add_gate_blocked`를 같이 적재해 실제 체결이 나오도록 다음 완화 owner를 정한다. |
| Source | [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

### DF-HOLDING-004 `soft_stop_expert_defense` 계층화 적용 결정

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-004` |
| 판정항목 | `2026-04-30 12:00 KST` `soft_stop_micro_grace v2`를 전문가 방어망으로 계층화할지 여부 |
| 문제 인식 | `soft_stop_micro_grace`와 `REVERSAL_ADD`만으로는 `scalp_soft_stop_pct` leakage를 충분히 방어하기 어렵다. 특히 단순 시간유예는 정당 손절과 흡수형 눌림을 분리하지 못하고, 반대로 `REVERSAL_ADD`는 후보가 늘어도 체결이 0이면 soft stop tail을 즉시 줄이지 못한다. |
| 결정 결과 | 채택 후 종료. `soft_stop_expert_defense`를 `soft_stop_micro_grace v2` 하나의 holding/exit live canary로 묶어 `2026-04-30 12:00~15:30 KST` 수집 축으로 적용했고, 장후 기본값은 OFF로 정렬한다. |
| live 적용 범위 | 당일 live에는 `stop arbitration layer`, `thesis invalidation veto`, `orderbook absorption stop`만 포함했다. 즉 우선순위 조정, thesis 붕괴 veto, 흡수 확인 시 20초 1회 유예만 실주문 행동을 바꿨다. 다음 재승인 전에는 이 범위도 live로 유지하지 않는다. |
| shadow/observe 범위 | `MAE/MFE quantile stop`, `recovery probability model`, `partial de-risk stop`은 shadow-only, `adverse fill detector`는 observe-only다. 이 네 축은 오늘 주문 수량, 청산 시점, 평균가를 바꾸지 않는다. |
| 제외 조건 | `reversal_add_used=True`, `POST_ADD_EVAL`, hard/emergency stop, `profit_rate <= -2.0%`, active sell order pending, invalid feature, REVERSAL_ADD 체결 포지션은 v2 적용에서 제외한다. |
| 원인귀속 보존 | live 변경은 여러 전략 이름을 갖지만 `soft_stop_micro_grace v2` 하나의 canary owner로 묶는다. 개별 전략은 로그 필드와 cohort tag로 분리하고, 성과 판정은 v1 baseline과 v2 guarded cohort를 비교한다. |
| rollback guard | guarded cohort 평균손익 `<= -0.30%`, guarded 후 hard/protect stop 전이, `sell_order_failed`, 또는 REVERSAL_ADD 체결 포지션 적용 1건 이상이면 v2를 OFF한다. |
| 현재 상태 | 최종 집계 기준 `2026-04-30 12:00~15:30 KST`에서 `soft_stop_expert_shadow=58 / unique 11`, `adverse_fill_observed=58 / unique 11`, `soft_stop_absorption_probe=7 / unique 6`, `extend=1`, `recovered=1`, `exit=6`이었다. v2 touched `11`개 중 profit 확인 `10`개 평균은 `-1.567%`이고 exit rule은 `scalp_soft_stop_pct=9`, `scalp_trailing_take_profit=1`이다. `sell_order_failed`, `protect_hard_stop`, `protect_trailing_stop`, `reversal_add_used` 혼입은 없었다. |
| 후속 액션 | 다음 운영일에는 새 live 축을 v2로 이어가지 않는다. v2 로그는 손실 flow taxonomy(`bad_entry/never-green`, 동일종목 반복손실, positive peak 후 soft stop, v2 guarded, preset hard`)와 refined `bad_entry` canary 설계 근거로만 사용한다. |
| Source | [2026-04-30-stage2-todo-checklist.md](/home/ubuntu/KORStockScan/docs/checklists/2026-04-30-stage2-todo-checklist.md), [plan-korStockScanPerformanceOptimization.rebase.md](/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md) |

### DF-HOLDING-005 `stop arbitration layer`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-005` |
| 전략 | `stop arbitration layer` |
| 역할 | hard stop, emergency stop, soft stop, REVERSAL_ADD, trailing, partial de-risk 후보가 같은 포지션에서 충돌하지 않게 우선순위를 정하는 최상위 조정 계층이다. |
| 적용 상태 | `2026-04-30 12:00~15:30 KST` v2 live 수집에 포함됐다. 다음 재승인 전에는 live가 아니라 v2 로그 해석용 계층이다. |
| 우선순위 | emergency/hard stop과 active sell pending은 항상 우선한다. 그 다음 thesis invalidation veto를 보고, veto가 없고 absorption score가 충분할 때만 soft stop 20초 1회 유예를 허용한다. |
| 기대효과 | 서로 다른 방어전략이 동시에 발동해 `유예`, `추가매수`, `트레일링`, `감산`이 섞이는 것을 막아 원인귀속을 보존한다. |
| 현재 상태 | 동작 자체는 정상이다. 최종 집계에서도 `reversal_add_used` 혼입 `0건`, `sell_order_failed=0`, `protect_hard_stop=0`, `protect_trailing_stop=0`이라 arbitration 오염은 없었다. 다만 오염이 없었다는 것은 v2를 계속 켤 근거가 아니라, v2가 손실 flow를 잘 분류했다는 근거에 가깝다. |
| 실패 신호 | excluded cohort에 v2가 적용되거나, active sell pending 상태에서 추가 유예가 찍히면 즉시 구현/운영 오류로 본다. |
| 다음 액션 | `soft_stop_absorption_probe/extend/exit` 로그에서 `expert_exclusion_reason`과 `reversal_add_used` 제외가 지켜지는지 확인한다. |

### DF-HOLDING-006 `thesis invalidation stop`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-006` |
| 전략 | `thesis invalidation stop` |
| 역할 | 처음 진입한 이유가 깨졌는지를 판단하는 veto 계층이다. thesis가 깨졌으면 micro grace, absorption, recovery 기대를 모두 금지하고 기존 exit로 보낸다. |
| 적용 상태 | `2026-04-30 12:00~15:30 KST` v2 live veto에 포함됐다. 다음 재승인 전에는 live veto가 아니라 장후 분석 근거다. |
| 오늘 veto 조건 | large sell print가 있거나, tick acceleration이 약하고 curr vs micro VWAP 이탈이 강하면 유예를 금지한다. 현재 구현 기준은 `large_sell_print_detected=True` 또는 `tick_acceleration_ratio < 0.60 and curr_vs_micro_vwap_bp < -20`이다. |
| 기대효과 | `흡수되는 눌림`이 아니라 `진입 thesis 붕괴`인 표본을 오래 들고 가지 않게 해, soft stop 유예가 손실 확대로 바뀌는 것을 막는다. |
| 현재 상태 | veto는 정상 동작했다. 최종 probe `7`건 중 `6`건이 thesis invalidation으로 유예 금지됐고, 사유는 `tick_accel_and_micro_vwap_break=4`, `large_sell_print=2`다. 현재 문제는 veto 충돌보다, 애초에 `bad_entry/never-green` 표본이 soft stop 손실의 대부분을 차지한다는 점이다. |
| 실패 신호 | thesis veto 조건이 참인데 `soft_stop_absorption_extend`가 발생하면 즉시 v2 OFF 후보로 본다. |
| 다음 액션 | `soft_stop_absorption_probe`에서 `veto_reason`과 실제 exit 전환을 확인한다. |

### DF-HOLDING-007 `adverse fill detector`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-007` |
| 전략 | `adverse fill detector` |
| 역할 | 진입 직후 체결 품질이 나쁜지 라벨링한다. partial fill, 불리한 microprice, 체결 직후 매도 우위, spread 악화 같은 조건을 soft stop 후행 결과와 연결한다. |
| 적용 상태 | observe-only. 오늘은 주문, 청산, 수량을 바꾸지 않고 `adverse_fill_observed` 로그만 남긴다. |
| 기대효과 | soft stop의 원인이 청산 로직 과민인지, 애초에 체결 품질이 나쁜 진입이었는지 분리한다. 이는 다음 `bad_entry_block` 또는 entry quality 축의 근거가 된다. |
| 현재 상태 | observe-only 정상 유지다. `12:00~15:30` 기준 `adverse_fill_observed=58 / unique 11`이 남았고, 주문/청산 분기 자체를 바꾼 흔적은 없다. `large_sell_print_detected=True`는 13건, feature는 전부 valid였다. |
| 승격 조건 | adverse fill 후보의 후속 soft/hard stop 전환율이 비후보보다 높고, missed winner 위험이 낮을 때만 다음 운영일 live block 후보로 검토한다. |
| 실패 신호 | observe-only인데 주문 제출, 수량, exit timing을 바꾸면 즉시 중단한다. |
| 다음 액션 | `adverse_fill_observed`와 `COMPLETED + valid profit_rate`를 후행 연결하되, 오늘 v2 성과에는 주문 행동 변경분으로 합산하지 않는다. |

### DF-HOLDING-008 `orderbook absorption stop`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-008` |
| 전략 | `orderbook absorption stop` |
| 역할 | soft stop이 고점 대비 밀림 또는 순간 호가 흔들림에 너무 민감하게 반응하는지 방어하는 핵심 실행축이다. 매도 압력이 실제로 흡수되고 있으면 soft stop을 짧게 1회 유예한다. |
| 적용 상태 | `2026-04-30 12:00~15:30 KST` v2 live 수집의 핵심축이었다. 다음 재승인 전에는 live 유예를 하지 않는다. |
| 유예 조건 | microstructure 흡수 신호가 3개 이상일 때만 `20초`, `1회` 유예한다. 후보 신호는 buy pressure, net aggressive delta, same-price buy absorption, micro VWAP 근접, microprice edge, tick acceleration, top3 depth ratio다. |
| 금지 조건 | thesis veto, emergency `<= -2.0%`, REVERSAL_ADD 체결/POST_ADD_EVAL, active sell pending, invalid feature에서는 유예하지 않는다. |
| 기대효과 | `진짜 하락`은 자르되, 호가 흡수 중인 순간 눌림은 20초 더 보아 불필요한 저점 매도를 줄인다. |
| 현재 상태 | 최종 `probe=7 / unique 6` 중 유예 조건을 통과한 것은 `아진엑스텍(4655)` 1건뿐이다. `12:55:18` `soft_stop_absorption_extend` 후 `12:55:22` `-1.29%`까지 회복했지만, `12:57:26` `tick_accel_and_micro_vwap_break` veto 후 `-1.65%` `scalp_soft_stop_pct`로 종료됐다. 직접 변동은 `-0.12%p`이며, absorption만으로 live를 지속할 근거는 없다. |
| 실패 신호 | 유예 후 hard/protect stop 전이, sell failure, REVERSAL_ADD 체결 포지션 혼입, 또는 직접 유예 손익차가 누적 손실로 커지면 v2를 OFF한다. |
| 다음 액션 | `soft_stop_absorption_extend`, `soft_stop_absorption_recovered`, `soft_stop_absorption_exit`는 장후 flow taxonomy와 함께 다음 단일 canary 후보 선별 근거로만 쓴다. |

### DF-HOLDING-009 `recovery probability model`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-009` |
| 전략 | `recovery probability model` |
| 역할 | soft stop 직후 회복 가능성을 점수화해, 향후 유예/청산/감산의 arbitration 입력으로 쓰기 위한 모델 후보다. |
| 적용 상태 | shadow-only. 오늘 live 판단에는 쓰지 않고 `recovery_prob_shadow`만 기록한다. |
| 기대효과 | 단순 rule 유예가 아니라, 과거 MAE/MFE와 현재 microstructure를 결합해 회복 가능성이 높은 표본만 선별하는 다음 단계 근거를 만든다. |
| 현재 상태 | shadow-only 정상이나 live 승격 근거로는 부족하다. 최종 shadow `58`건의 `recovery_prob_shadow` 평균은 `0.327`, median `0.24`, max `0.73`이고, high score였던 `아진엑스텍(4655)`도 최종 `-1.65%`로 종료했다. score는 로깅 품질은 있으나 live action 근거로는 아직 약하다. |
| 승격 조건 | shadow score 상위군의 `rebound_above_sell/buy`, `mfe_10m`, `COMPLETED + valid profit_rate`가 하위군보다 명확히 우수할 때만 canary 후보로 올린다. |
| 실패 신호 | score와 실제 회복이 무관하거나, high score군에서 hard/protect stop 전이가 많으면 모델 입력으로 쓰지 않는다. |
| 다음 액션 | 오늘은 `soft_stop_expert_shadow` 필드 품질과 후행 recovery label 연결성만 확인한다. |

### DF-HOLDING-010 `MAE/MFE quantile stop`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-010` |
| 전략 | `MAE/MFE quantile stop` |
| 역할 | 전략/상황별 정상 손실폭과 정상 회복폭을 quantile로 보고, 고정 `scalp_soft_stop_pct`가 종목/상황별 변동성을 무시하는지 확인한다. |
| 적용 상태 | shadow-only. 오늘 live stop threshold를 바꾸지 않는다. |
| 기대효과 | 모든 종목과 장면에 같은 soft stop 폭을 적용하는 구조의 한계를 검증한다. 정상 MAE가 큰데 MFE 회복도 큰 유형은 유예 후보, MAE가 작아도 MFE가 빈약한 유형은 빠른 컷 후보로 분리할 수 있다. |
| 현재 상태 | shadow-only 정상이다. 최종 shadow `58`건의 `mae_proxy_pct` 평균은 `-1.600`, median `-1.56`, `mfe_proxy_pct` 평균은 `-0.018`, median `-0.23`이다. 즉 v2 touched 표본의 다수는 정상 변동폭을 크게 벗어난 회복형이 아니라 never-green/약한 MFE 쪽으로 기운다. |
| 승격 조건 | 충분한 표본에서 quantile band가 soft stop 결과를 유의미하게 설명하고, full/partial 및 initial/pyramid 분리 후에도 방향이 유지될 때만 다음 후보로 올린다. |
| 실패 신호 | quantile 기준이 표본 부족이거나 특정 종목 몇 건에 과적합되면 live threshold에는 쓰지 않는다. |
| 다음 액션 | `MAE/MFE quantile`은 장후 리포트 입력으로만 쓰고, 오늘 12:00 live 판정에는 합산하지 않는다. |

### DF-HOLDING-011 `partial de-risk stop`

| 항목 | 내용 |
| --- | --- |
| ID | `DF-HOLDING-011` |
| 전략 | `partial de-risk stop` |
| 역할 | 전량 손절 대신 일부 감산으로 tail risk를 줄이고 회복 여지를 남기는 전략 후보다. |
| 적용 상태 | shadow-only. 오늘은 `would_trim_qty`, `would_trim_price`, `post_trim_mfe/mae`만 남기고 실주문 수량은 바꾸지 않는다. |
| live 제외 사유 | 부분 감산은 주문수량, 체결귀속, 평균가, 후속 손익 계산을 모두 바꾼다. 같은 날 `soft_stop_micro_grace v2`와 동시에 live로 열면 원인귀속이 크게 흐려진다. |
| 기대효과 | 전량 손절의 tail loss를 줄이면서, 반등 시 잔여 수량으로 upside capture를 남길 수 있는지 검증한다. |
| 현재 상태 | shadow-only 정상 유지다. 최종 shadow `58`건 중 `would_trim_qty=1`은 43건, `0`은 15건이었다. 필드 생성은 됐지만 실제 주문수량/평균가/손익 귀속을 바꾸는 live 근거는 아니며, 다음 단일축은 partial de-risk가 아니라 refined bad-entry 쪽이다. |
| 승격 조건 | counterfactual 기준으로 tail loss 감소가 뚜렷하고, post-trim MFE가 유의미하며, 주문 실패/부분체결 복잡도가 감당 가능할 때만 별도 단일축 canary로 연다. |
| 실패 신호 | would-trim이 대부분 full exit보다 나쁘거나, 평균가/실현손익 attribution을 흐리면 보류한다. |
| 다음 액션 | 오늘은 shadow 산출값의 존재와 후행 `post_trim_mfe/mae` 연결 가능성만 본다. |

## 항목 간 연결 관계

| 선행 ID | 결정 결과 | 후속 ID | 연결 의미 |
| --- | --- | --- | --- |
| `DF-ENTRY-001` | 독립 개선축 폐기 | `DF-ENTRY-002` | `blocked_ai_score_share`는 관찰지표로 남기고, 실제 실행은 `buy_recovery_canary prompt` 재교정으로 전환 |
| `DF-ENTRY-002` | upstream 표본 생성 유효, 유지/고정 | `DF-ENTRY-003` | `BUY 부족`보다는 `entry_armed -> submitted` 제출 병목이 다음 공식 판정축으로 넘어갔음을 의미 |
| `DF-ENTRY-003` | 제출축 live 검증 진행 후 원인 위치 고정 | `DF-ENTRY-004` | `spread relief canary`는 downstream 병목 위치 확인까지는 완료했고, 실효성 승인 실패 후 `quote_fresh` replacement 후보로 연결됐다는 의미 |
| `DF-ENTRY-004` | same-day 보조축을 `quote_fresh`로 고정 후 `spread/ws_jitter/other_danger residual`을 순차 검증 | `DF-ENTRY-005` | `quote_fresh family`가 제출 회복을 만들지 못한 뒤, `gatekeeper_fast_reuse` 후보로 새지 않고 `latency_state_danger` 직접 blocker로 복귀해야 한다는 의미 |
| `DF-ENTRY-005` | `gatekeeper_fast_reuse` 매몰을 철회하고 `latency_state_danger -> other_danger relief`로 pivot | `DF-ENTRY-006` | pivot 설명과 `latency_quote_fresh_composite` 복합축을 분리해 historical/reference 근거까지 추적한다는 의미 |
| `DF-ENTRY-006` | `latency_quote_fresh_composite`를 묶음 ON/OFF 기준의 entry 복합축으로 관리했지만 현재는 OFF historical/reference 상태 | `DF-ENTRY-007` | same-day replacement(`latency_signal_quality_quote_composite`) 실패 후 `mechanical_momentum_latency_relief`로 현재 live owner가 이동했다는 의미 |
| `DF-ENTRY-007` | `mechanical_momentum_latency_relief`를 현재 entry live replacement 축으로 관리 | `DF-HOLDING-001` | 제출 회복이 확인되면 HOLDING/청산 품질 판정으로 넘어가고, 회복 실패면 다음 entry replacement 축 또는 entry price/P0 guard 계열로 닫는다는 의미 |
| `DF-HOLDING-001` | 제출 회복 이후 HOLDING/청산 품질 판정 축 유지 | `DF-HOLDING-002` | 4월 손익 훼손 기준으로 soft stop을 1순위 live 후보로 분리하고, 10시 중간점검/11시 1차 판정으로 조기 오염을 잡는다는 의미 |
| `DF-HOLDING-002` | `soft_stop_micro_grace` 20초 유예를 1차 live 조작점으로 승인 | `DF-HOLDING-003` | 단순 유예만으로 부족해 `유효 진입 회수`와 `불량 진입 분류`를 분리했다는 의미 |
| `DF-HOLDING-003` | `REVERSAL_ADD` 후보는 생겼지만 체결 0, soft stop tail은 계속 발생 | `DF-HOLDING-004` | 장후로 미루지 않고 `soft_stop_micro_grace v2` 전문가 방어망을 12:00 same-day canary로 적용했다는 historical 흐름 |
| `DF-HOLDING-004` | soft stop expert defense를 v2 canary로 채택했으나 장후 기본 OFF | `DF-HOLDING-003` | v2 지속이 아니라 bad-entry/never-green refined canary로 다음 live owner를 되돌린다는 현재 흐름 |
| `DF-HOLDING-005` | stop 우선순위 조정 계층은 v2 안에서 정상 동작 확인 | `DF-HOLDING-003` | arbitration 오염이 없었으므로 다음 단일축 refined bad-entry의 제외조건으로 흡수한다는 의미 |
| `DF-HOLDING-006` | thesis invalidation veto는 v2 안에서 정상 동작 확인 | `DF-HOLDING-003` | thesis/adverse 확인을 refined bad-entry의 confirmation 조건으로 재사용한다는 의미 |
| `DF-HOLDING-007` | adverse fill은 observe-only | `DF-HOLDING-003` | 불량 체결 라벨은 refined bad-entry 판단 근거로 되돌린다는 의미 |
| `DF-HOLDING-008` | orderbook absorption stop은 성공 표본 부족으로 live 지속 근거 없음 | `DF-HOLDING-009` | absorption은 다음 live 축이 아니라 recovery probability/MAE-MFE shadow 해석 입력으로만 남긴다는 의미 |
| `DF-HOLDING-009` | recovery probability는 shadow-only | `DF-HOLDING-003` | 회복확률 점수는 refined bad-entry의 confirmation/제외조건에 보조 입력으로만 쓴다는 의미 |
| `DF-HOLDING-010` | MAE/MFE quantile은 shadow-only | `DF-HOLDING-011` | 고정 손절폭 보정 가능성을 확인한 뒤, 별도 수량 변경축인 partial de-risk 후보로 연결한다는 의미 |
| `DF-HOLDING-003` | `bad_entry_block` outcome으로 refined rule을 확정 | `DF-HOLDING-001` | v2 OFF 이후 다음 보유/청산 live owner를 `bad_entry_refined_canary`로 되돌려 5/4 장전 로드 확인만 남긴다는 현재 흐름 |

## 운영자 메모: Sentinel 이상치 수신 시 할 일

이 섹션은 개인 운영 메모다. 실행 판정의 Source는 날짜별 checklist, Plan Rebase, report 산출물에 둔다.

### 1. 먼저 하지 말 것

- Sentinel 이상치 알림만 보고 score threshold, spread cap, fallback, 청산 threshold, AI cache TTL, bot restart를 바로 바꾸지 않는다.
- Telegram 문구의 `이상치`를 곧바로 `전략 실패` 또는 `튜닝 미완료`로 해석하지 않는다.
- `submitted 급감`, `HOLD 유예 악화`, `soft stop rebound`, `AI MISS` 같은 단일 현상을 손익 결론으로 바로 연결하지 않는다.

### 2. 즉시 확인 순서

1. Sentinel Markdown/JSON report를 열어 `primary`, `secondary`, 전환율, baseline 대비 차이를 본다.
2. 같은 시각대 pipeline event가 멈췄는지 확인한다. event stream/WS/token/broker 문제가 의심되면 전략 튜닝이 아니라 `incident/playbook`으로 분리한다.
3. 이상치를 아래 4개 중 하나로 라우팅한다.
   - `incident/playbook`: WS/token/event stream/broker/order path 장애
   - `threshold-family 후보`: 반복성, sample floor, daily/rolling/cumulative 방향성, rollback owner가 있는 전략 병목
   - `instrumentation gap`: 판단에 필요한 필드나 로그가 없음
   - `normal drift`: 장세/표본 변동으로 조치 없음
4. threshold 후보로 보이면 장중 live 변경이 아니라 `R3_manifest_only` 후보로만 연결한다.
5. 판단이 애매하면 신규 로그/리포트 보강 항목으로 넘기고, live mutation은 보류한다.

### 3. 알림별 기본 해석

| Sentinel 판정 | 운영자 1차 행동 | threshold-cycle 연결 |
| --- | --- | --- |
| `UPSTREAM_AI_THRESHOLD` | score 50, 65~74, WAIT 65~79, blocked_ai_score 분포를 본다 | missed/avoided outcome 복원 가능할 때만 후보 |
| `LATENCY_DROUGHT` | `budget_pass -> latency_pass -> submitted` 전환과 quote freshness를 본다 | 반복되면 latency/quote family 후보 |
| `PRICE_GUARD_DROUGHT` | P1/P2/pre-submit/scale-in guard block reason과 bps 분포를 본다 | 분포와 fill/slippage가 충분할 때만 후보 |
| `RUNTIME_OPS` | WS/token/event stream/broker 상태를 먼저 본다 | threshold-cycle이 아니라 incident/playbook |
| `HOLD_DEFER_DANGER` | flow defer 후 추가악화, max defer, hard/protect safety 우선순위를 본다 | 반복되면 holding_flow family 후보 |
| `AI_HOLDING_OPS` | cache MISS, Tier provenance, response latency, parse fail을 본다 | 먼저 logging/cache instrumentation 후보 |
| `SOFT_STOP_WHIPSAW` | 반등률, soft stop 후 MFE, never-green 여부를 분리한다 | soft stop/MAE-MFE 후보 가능 |
| `TRAILING_EARLY_EXIT` | trailing 후 missed upside와 protect/hard stop 제외 여부를 본다 | winner wide-window/trailing family 후보 가능 |
| `SELL_EXECUTION_DROUGHT` | exit_signal 대비 sell_order_sent/sell_completed와 receipt truth를 본다 | 보통 runtime/receipt issue 우선 |

### 4. threshold-cycle로 넘기는 최소 조건

- 동일 classification이 반복된다.
- 표본 수가 sample floor를 넘는다.
- `COMPLETED + valid profit_rate`와 체결품질을 분리해 볼 수 있다.
- full fill과 partial fill을 섞지 않는다.
- daily/rolling/cumulative 방향이 같은 쪽을 가리킨다.
- rollback owner, rollback command, 적용 cohort가 문서에 있다.
- 적용은 장중 runtime mutation이 아니라 다음 장전 `manifest_only` 후보에서 시작한다.

### 5. 운영자 다음 액션 문장 템플릿

- 판정: `이번 이상치는 {classification}이며 {incident/threshold 후보/instrumentation gap/normal drift}로 본다.`
- 근거: `{전환율}, {baseline 대비}, {top blocker}, {관련 report path}` 기준이다.
- 다음 액션: `{R3 manifest 후보 생성/incident playbook 승인 요청/logging workorder 추가/no action}`으로 처리한다.

## 운영자 메모: data/report 산출물 운용 구분

이 섹션은 개인 운영 메모다. 공식 실행 판정의 Source는 날짜별 checklist, Plan Rebase, 산출물 원문에 둔다. 개인문서는 산출물 읽는 순서와 운영자 행동을 빠르게 맞추기 위한 보조 노트로만 쓴다.

### 1. 공통 원칙

- `data/report` 아래 산출물은 기본적으로 `관찰/판정 입력`이다. 파일이 생성됐다는 사실만으로 runtime env, threshold, score, spread cap, 청산 정책, bot restart를 바꾸지 않는다.
- 리포트가 `runtime_change=false`, `report_only`, `observe_only`, `manifest_only`, `shadow_prompt`를 명시하면 그 경계를 그대로 따른다.
- live 적용 검토는 `daily -> rolling -> cumulative` 방향 일치, sample floor, rollback owner, rollback command, cohort 분리, 기존 동일 단계 owner 충돌 확인이 있어야 한다.
- `COMPLETED + valid profit_rate` 외 손익은 참고값이다. full fill과 partial fill, initial과 pyramid, fallback/historical trace는 합치지 않는다.
- 운영 자동화의 성공은 `cron 발화`, `wrapper exit`, `산출물 완성`, `알림 발송`, `전략 효과`를 분리해서 본다.

### 2. 리포트별 사용 방식

| 산출물 | 운영 등급 | 먼저 볼 필드 | 운영자 행동 | 금지선 |
| --- | --- | --- | --- | --- |
| `data/report/buy_funnel_sentinel/` | 장중 이상치 감지 | `primary`, `secondary`, `ai_confirmed`, `budget_pass`, `submitted`, baseline 대비 | incident/threshold 후보/instrumentation gap/normal drift로 라우팅 | score threshold, spread cap, fallback, restart 자동 변경 금지 |
| `data/report/holding_exit_sentinel/` | 장중 이상치 감지 | `primary`, `secondary`, `exit_signal`, `sell_completed`, defer/worsen, AI cache | 청산 drought, flow defer, whipsaw, trailing 조기익절을 분리 | 자동 매도, holding threshold, AI TTL, restart 자동 변경 금지 |
| `data/report/threshold_cycle_YYYY-MM-DD.json` | 당일 threshold 입력 | `threshold_snapshot`, `threshold_diff_report`, `apply_candidate_list`, `rollback_guard_pack` | 당일 수치와 다음 장전 후보를 확인 | `apply_ready=True`여도 동일 단계 owner 충돌 전 live 금지 |
| `data/report/threshold_cycle_cumulative/` | 누적/rolling 방향 확인 | `completed_cohorts`, `Family Readiness`, window별 sample | daily와 방향이 맞는지 확인하고 후보를 격상/격하 | 누적 평균 단독으로 threshold 적용 금지 |
| `data/threshold_cycle/apply_plans/` | 장전 manifest 확인 | `apply_mode`, `owner_rule`, `blocked_reason`, rollback owner | R3 `manifest_only` 후보인지, R5 live apply가 막혔는지 확인 | manifest를 runtime mutation으로 해석 금지 |
| `data/report/holding_exit_decision_matrix/` | AI/ADM context 후보 | `matrix_version`, `application_mode`, `Hard Veto`, `Prompt Hints` | 5/7 장후 기준 runtime loader/provenance 구현 완료, flag OFF baseline으로 유지 | live AI 응답/action 변경 금지 |
| `data/report/preclose_sell_target*` | 장마감 후보 검토 | `policy_status`, `automation_stage`, `live_runtime_effect`, 후보 사유 | operator review 또는 AI/Telegram acceptance 분리 | 자동 주문, threshold/ADM consumer 자동 연결 금지 |
| `data/report/monitor_snapshots/` | 상세 복원 근거 | `holding_exit_observation`, `wait6579_ev_cohort`, post-sell/MFE/MAE | checklist 항목의 증적이나 outcome 복원 입력으로 사용 | 단일 snapshot으로 broad threshold 변경 금지 |
| `data/report/tuning_monitoring/status/` | 자동화 완성도 | step별 `started/success/failed`, attempt, exit_code | cron/wrapper 실패와 전략 효과를 분리 | lab/report 결과를 live mutation으로 직접 연결 금지 |

### 3. 2026-05-06 산출물 기준 빠른 판정

| 후보 | 현재 읽는 방식 | 운영자 메모 |
| --- | --- | --- |
| `protect_trailing_smoothing` | `threshold_cycle_2026-05-06.json` daily에서는 `next_preopen_single_owner` 후보 | 5/7 PREOPEN의 `soft_stop whipsaw confirmation`과 같은 holding/exit 단계라 동시 live enable 금지. 충돌 시 hold 또는 단일 owner 하나만 승인 |
| `scale_in_price_guard` | `manifest_only` 유지 | `spread_bps_p90=83.26`은 완화 근거가 아니라 현행 `80bps / 1주 cap` safety 유지 근거 |
| `statistical_action_weight` | `report_only_weight_source` | `time_1030_1400`, `volume_2m_10m`, `price_gte_70k`의 `pyramid_wait` 우위는 ADM/SAW 입력 후보일 뿐 live 주문/청산 판단이 아님 |
| `holding_exit_decision_matrix` | `shadow_prompt_or_observe_only_until_owner_approval` | 5/7 장후 baseline/candidate/excluded cohort와 cache-key/provenance는 구현됐지만 `HOLDING_EXIT_MATRIX_ADVISORY_ENABLED=False` 유지. Hard Veto는 항상 기존 runtime safety가 우선 |

### 4. 리포트 확인 후 문서화 순서

1. 산출물의 `application_mode` 또는 `apply_mode`를 먼저 읽는다.
2. 수치가 상위라도 `sample_ready`, `weight_source_ready`, `completed_valid`, `loss_rate`, `edge_margin`을 같이 본다.
3. 같은 단계 live owner와 충돌하면 live가 아니라 checklist 후보/manifest 후보로 낮춘다.
4. 운영 판단을 남길 때는 `판정 -> 근거 -> 다음 액션` 순서로 쓰고, 미래 작업은 날짜별 checklist에 `Due/Slot/TimeWindow/Track`이 있는 체크박스로 남긴다.
5. checklist를 바꾼 뒤에는 parser 검증을 돌리고, Project/Calendar 동기화는 표준 수동 명령으로만 처리한다.
