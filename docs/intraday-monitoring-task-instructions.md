# KRX/NXT/PREMARKET 장중 모니터링 작업지시문

이 문서는 KRX 정규장, NXT 거래 구간, `PREMARKET_KRX_LIKE` 관측 구간의 복사 가능한 canonical 작업지시문이다. 실제 종료 시각만 작업 시작 전에 채운다.

## 2026-07-23 역사적 배포 확인 기준점

- 아래 값은 11:11 KST 당시의 역사적 배포 확인 기록이며 현재 런타임을 뜻하지 않는다. 당시 commit은 `f5fb3c78`, graceful restart 뒤 PID는 `147049`, start 시각은 `2026-07-23 11:11:16 KST`였고 runtime env 검증은 `pass`, 필수 키 missing/mismatch는 0건이었다.
- `rising_missed_ai_action_guard`와 `scalp_fast_exit_guard`는 entry와 holding/exit가 분리된 당일 긴급 축이다. `KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ENABLED=true`, `KORSTOCKSCAN_RISING_MISSED_AI_ACTION_GUARD_ACTIVE_DATE=2026-07-23`, `KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ENABLED=true`, `KORSTOCKSCAN_SCALP_FAST_EXIT_GUARD_ACTIVE_DATE=2026-07-23`이며 fast-exit poll은 250ms다.
- 해당 checkpoint PID에는 KRX `KORSTOCKSCAN_EARLY_VOLATILITY_TP_ENABLED=true`, NXT `KORSTOCKSCAN_EARLY_VOLATILITY_TP_NXT_ENABLED=true`와 각각의 `2026-07-23` active date·policy file이 로드됐다. 조기 지정가 부분익절의 비율 0.35, 순이익 목표 +0.55%, TTL 210초는 변경하지 않는다.
- PREMARKET `KORSTOCKSCAN_EARLY_VOLATILITY_TP_PREMARKET_ENABLED=true`와 policy file도 로드됐지만 active date는 `2026-07-24`다. 2026-07-23에는 `runtime_not_active`이며 KRX/NXT 정책을 소급 적용하지 않는다.
- 재기동 후 첫 monitor 이벤트는 수동관리 제외 종목 `950160`의 `manual_control_fast_exit_monitor_blocked`였고 주문은 없었다. 자연 발생 DROP/WAIT/probe/trailing 표본은 아직 정책 효과로 확정하지 않고 postclose 귀속에서 확인한다.
- 위 PID와 commit은 배포 확인 기준점이다. 작업 시작 때 실제 PID/start/commit/env를 다시 조회하고 달라졌으면 이 기준점을 현재 런타임으로 오인하지 말고 `implemented_not_runtime_reflected` 또는 새 배포 provenance로 기록한다.

## 공통 긴급 안전 계약

### AI action과 probe 확대

- 최신 pre-submit AI가 fresh·valid·consistent `DROP`이면 점수, 시장, venue, TP1 freshness와 관계없이 모든 실주문 SCALPING 신규 BUY를 veto한다.
- fresh·valid `WAIT`은 최대 1주 probe만 허용한다. 중앙 allocator의 계획 수량은 residual 상한 metadata로만 보존하고 probe 체결만으로 잔량을 제출하지 않는다.
- fresh·valid `BUY`만 기존 `position_sizing_dynamic_formula`의 10~30% 동적 수량과 기존 post-probe 확대 경로를 사용한다. `NEUTRAL` micro 판정 자체를 공통 차단으로 바꾸지 않으며, BUY 권한 아래의 기존 정상 기회는 유지한다.
- AI 결과가 누락·만료·충돌이면 source-quality guard에 따라 fail-closed 처리한다. venue별 fast tape나 강한 호가가 fresh DROP 또는 AI source-quality 결손을 대체하지 못한다.
- WAIT residual은 기존 3초 probe TTL 안에서 250ms 이상 떨어진 두 번의 연속 평가가 모두 다음을 만족할 때 첫 residual leg를 정확히 한 번만 제출한다.
  - BBO가 fresh·consistent이고 executable mark가 probe 체결가 이상이다.
  - `가격/틱`, `호가`, `signed tape` 중 최소 2개 독립 그룹이 양수이고 음수 그룹은 없다.
  - 최신 AI가 DROP이 아니며 stop, exit, cooldown, 계좌·주문·수량 guard를 모두 통과한다.
- `DROP`, 약세, stale/conflict, stop 접촉, TTL 만료가 발생하면 residual을 폐기하고 해당 position cycle의 추가 확대를 금지한다. WAIT 첫 residual leg 이후 나머지 계획 수량은 별도 재확인 없는 자동 제출을 금지한다.
- residual 체결로 평단·수량이 바뀌면 full-bundle peak를 `max(새 평단, 체결 직후 fresh mark)`로 재기준화한다. 1주 probe 시점의 peak를 확대된 전체 수량의 trailing peak로 재사용하지 않는다.

## Multi-leg Post-Probe 실적 기반 보완 모니터링 작업지시문

`[종료시각]`까지 현재 가동 런타임을 기준으로 `Multi-leg Post-Probe`의 주문 무결성, 정상 승자 확대, 잔량 폐기의 기회비용과 증분 EV를 함께 모니터링한다. 목표는 손실 억제 자체가 아니라 source-quality가 유효한 정상 승자를 안전하게 확대하여 기대값과 순이익을 최대화하는 것이다.

### 시작 기준점과 권한

- 작업 시작 시 PID/start 시각, loaded commit, `source_dirty`, runtime-env handoff와 다음 값을 실제 PID 환경에서 다시 확인한다.
  - `KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED=true`
  - `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED=true`
  - `KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE=[작업일]`
  - `KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED=true`
  - probe 수량 1주, TTL 3초, 최대 bundle 수, slippage·anchor 설정
- `2026-07-27 14:54:22 KST`의 확인 기준점은 PID `306350`, commit `4ca6910c`, `source_dirty=false`, runtime-env verify `pass`, broker balance/DB reconciliation 일치, WS 로그인 정상이다. 이는 역사적 기준점일 뿐이므로 작업 시작 시 PID가 다르면 새 provenance로 교체한다.
- fresh AI 권한 관측값은 `DROP=fresh_drop_hard_veto`, `WAIT=fresh_wait_bounded_confirmation`이어야 한다. `fresh_negative_veto`는 폐기된 모호한 라벨이며 신규 이벤트에 다시 나타나면 관측 계약 회귀로 판정한다.
- 이 작업은 read-only runtime observation과 source-only attribution이다. 별도 사용자 지시 없이 env, threshold, provider, 주문가격·수량, broker guard, bot 상태를 변경하거나 재기동·주문·취소를 실행하지 않는다.

### 표본 범위와 event 재구성

- clean baseline `2026-06-04T14:29:09+09:00` 이후 실제 SCALPING 신규진입만 사용하고 KRX, NXT, `PREMARKET_KRX_LIKE`를 effective venue/session/broker route별로 분리한다. sim/probe observation-only, counterfactual, real broker 주문·체결을 합치지 않는다.
- 각 `probe_bundle_id`를 기준으로 다음 순서를 timestamp, record ID, broker order number와 함께 재구성한다.

  `entry_split_order_plan_applied -> order_leg_request -> probe_submitted -> order_leg_sent -> probe_filled -> probe_continuation_deferred|residual_planned -> residual_submitted|residual_blocked -> residual fill/receipt -> position_rebased_after_fill -> order_bundle_submitted -> holding/exit`

- 계획수량, probe 수량, residual planned/submitted/filled/unfilled 수량과 실제 broker BUY 주문번호를 대조한다. `order_bundle_submitted.requested_qty` 같은 계획 metadata를 실제 제출수량으로 오인하지 않고 broker order·receipt·fill을 실주문 source of truth로 사용한다.
- 각 평가의 BBO/mark, fill price, positive·negative group, AI action/source/age, `post_probe_direction_ai_authority`, direction state/action/reason, confirmation count, source-version signature와 관측시각을 보존한다.

### 실시간 정상작동 판정

- fresh `DROP` 뒤에는 신규·residual BUY broker API 호출이 0회이고 `post_probe_hard_veto=true`, `probe_expand_forbidden=true`여야 한다.
- fresh `WAIT`은 최초 1주 probe만 허용하며 `post_probe_hard_veto=false`여야 한다. 다음 조건을 모두 만족한 서로 다른 두 시장 관측만 강한 확인으로 센다.
  - 평가 간격이 250ms 이상이다.
  - source-version signature가 실제로 변경됐다. 동일·미버전·미래 timestamp 관측을 재사용하지 않는다.
  - fresh·consistent executable BBO와 `mark >= probe_fill_price`다.
  - 가격/틱, 호가, trusted signed tape 중 최소 두 독립 그룹이 양수이고 음수 그룹·large-sell 경고가 없다.
  - 최신 AI가 DROP이 아니고 stop, exit token, cooldown, account/order/quantity/stale guard가 모두 통과한다.
- WAIT은 첫 강한 확인에서 `confirmation_count=1 + DEFER`, 두 번째 강한 확인에서만 `confirmation_count=2 + ALLOW_NARROW`가 되어야 한다. residual은 계획된 첫 leg 한 건만 정확히 한 번 제출하고 나머지 leg는 별도 재확인 없이는 제출하지 않는다.
- AI BUY 권한 아래의 micro `NEUTRAL`은 기존 정상 확대 기회를 일률적으로 차단하지 않는다. AI `WAIT`과 micro direction `NEUTRAL`을 같은 blocker로 합산하지 않는다.
- fresh AI BUY는 기존 `STRONG=ALLOW_NARROW`, 안전한 `NEUTRAL=ALLOW_NORMAL`, `WEAK|UNKNOWN=DEFER`, 회복 뒤 `ALLOW_RECOVERED_WIDE`, `HARD_NEGATIVE=abort` 경로를 유지한다. 정상 BUY residual leg는 계획 범위 안에서 평가하되 WAIT 전용 첫-leg cap을 BUY에 잘못 적용해 정상 승자 확대를 막지 않는다.
- 가격 owner는 `dynamic_entry_price_resolver_p1`의 `initial -> post_probe -> leg_reprice`로 유지한다. 각 residual leg마다 fresh BBO/source-quality와 P1 가격을 다시 확인하고 `DEFER` 결과에는 executable price나 broker submit이 없어야 하며, 재가격·최종 sizing은 기존 계획수량을 늘리지 않아야 한다.
- 약세, 음수 그룹, stale/conflict, stop 접촉 또는 3초 TTL 만료 시 residual을 제출하지 않고 `residual_blocked`와 `probe_expand_forbidden=true`를 남긴다. 이후 동일 position cycle에서 자동 확대가 재개되지 않아야 한다.
- residual 체결 뒤 `peak_basis_qty`, `peak_basis_avg_price`와 full-bundle peak가 새 수량·평단 및 fresh mark 기준으로 갱신됐는지 확인한다.
- 동일 bundle의 중복 BUY, 계획수량 초과, probe 없는 residual, WAIT residual 2개 이상, DROP 통과, 다른 venue route 주문, exit token 이후 BUY, 부분익절/full-exit과 경합한 초과 BUY·SELL은 즉시 결함이다.

### 정상 승자 확대와 기회비용 판정

- 실시간 주문 무결성 PASS와 전략 효과 PASS를 분리한다. 자연 residual 제출이 0건이면 방어 경로만 확인된 것이며 `normal_winner_expansion_runtime_verified`로 닫지 않는다.
- probe 체결 후 1·3·5·10분 exact venue/session 가격으로 MFE, MAE, target/adverse first-hit와 최종 수익률을 성숙시킨다. post-probe primary horizon은 10분이며 미성숙 표본은 `open_unresolved`로 유지한다.
- residual 제출 표본은 실제 residual fill notional과 추가 MFE·MAE, 거래비용·slippage를 사용해 probe-only 대비 증분 손익을 계산한다. partial fill과 full fill을 분리하고 residual 미체결분을 체결된 것으로 보간하지 않는다.
- residual 폐기 표본은 이후 MFE가 충분했는지와 adverse-first 여부를 함께 계산하여 `correctly_not_expanded_or_reversal`, `probe_residual_missed_upside_candidate`, `pyramid_open_unresolved`를 분리한다. 단기 손실 회피만으로 정상 승자 확대 정책의 성공을 확정하지 않는다.
- AI BUY, AI WAIT, direction confirmation signature, effective venue/session, blocker reason, entry score, pressure, tick acceleration, micro-VWAP side별로 결과를 분리한다. KRX 결과로 NXT/PREMARKET을 보강하거나 반대로 합치지 않는다.
- 실현손익은 `COMPLETED + valid profit_rate`만 사용한다. counterfactual·open PnL·simple sum을 real EV와 합산하지 않으며 EV는 `equal_weight_avg_profit_pct`, `notional_weighted_ev_pct`, `source_quality_adjusted_ev_pct` 중 계약된 이름만 사용한다.
- 당일 한두 건은 runtime integrity와 source-quality 경보에만 사용한다. 정상 승자 확대의 EV 판단은 rolling closed source-quality-valid bundle 20건 이상에서 한다.

### source-quality와 산출물

- 기본 source는 당일 `pipeline_events`, broker receipt/order log, `scalping_pyramid_intraday_feedback`, `observation_source_quality_audit`, `ai_decision_outcomes`와 runtime-env verify다. 산출물의 `generated_at`이 마지막 probe event보다 이르면 stale report로 명시하고 raw event와 혼동하지 않는다.
- effective venue/session, broker route, BBO·tick·orderbook provenance, source-version signature, probe/residual receipt join이 결손·충돌한 row/window는 `raw_row_exclusion` 또는 `source_quality_blocked`로 제외한다.
- `micro_vwap_provenance_missing`, residual fill attribution invalid, route conflict 또는 unknown-token warning을 0으로 보간하지 않는다. 결손이 전략 실패인지 자료 결함인지 분리한다.
- 기존 report contract의 `actual_order_submitted=false`, `broker_order_forbidden=true`, `runtime_effect=false`, `allowed_runtime_apply=false`를 유지한다. source-only 보고서가 실주문 품질 승인이나 장중 threshold mutation 권한을 갖지 않는다.

### 즉시 결함·rollback 판정과 보고

- 다음 중 하나라도 발생하면 `rollback_required` 또는 `code_improvement_required`로 보고하고 해당 bundle의 추가 전략 귀속을 중지한다. 별도 사용자 지시 없이 직접 rollback·재기동하지 않는다.
  - fresh DROP 뒤 broker BUY, fresh WAIT의 hard-veto 오기록 또는 2회 확인 전 residual
  - 동일 source version 중복 확인, 250ms 미만 확인, stale/conflict·음수 그룹 통과
  - residual 중복·계획수량 초과·WAIT 두 번째 residual 자동 제출
  - probe/residual receipt join 불일치, route 혼합, peak basis 미재기준화
  - exit token 이후 BUY, partial/full-exit 경합의 중복·초과 주문
- 최종 보고는 반드시 `판정 -> 근거 -> 다음 액션` 순서로 작성한다.
  - 판정: `post_probe_runtime_healthy_no_change | normal_winner_expansion_observed | correctly_not_expanded_observed | insufficient_natural_sample_keep_observing | source_quality_gap | code_improvement_required | rollback_required`
  - 근거: PID/commit/env, venue/session, bundle 수, probe·residual planned/submitted/filled/blocked 수, WAIT/DROP/BUY 권한, 확인 signature, 중복·초과 주문, 10분 MFE/MAE와 성숙 상태, source-quality 제외 수를 함께 제시한다.
  - 다음 액션: 자연 표본 계속 관찰, 결손 producer 보완안, 코드결함 재현·테스트 범위 또는 명시적 operator 결정 필요사항 중 하나로 한정한다.

### 조기 지정가 부분익절 runtime 계약

- `scalp_early_volatility_partial_tp`는 `scalp_trailing_take_profit` holding/exit owner 아래에서 최초 부분익절 지정가와 runner 분리를 조정하는 bounded coordinator다. trailing, hard/protect/emergency 수치나 full-exit 권한을 소유하거나 완화하지 않는다.
- 실제 `SCALPING + HOLDING`이며 sim 포지션이 아닌 새 position cycle만 대상이다. policy의 `active_from_epoch`와 현재 code load 시각 중 늦은 시각 이후 시작한 포지션에만 적용하고 기존 보유분에 소급하지 않는다.
- cohort와 broker route는 반드시 함께 일치해야 한다. KRX 정규장은 `KRX + SOR`, NXT는 `NXT + NXT`, PREMARKET은 `PREMARKET_KRX_LIKE + NXT`다. policy version, `qualified_for_runtime`, effective venue, route 또는 active date가 불일치하면 fail-closed한다.
- 다음 제출 자격을 모두 만족해야 하며, 한 position cycle에는 동시 미체결 지정가 SELL 한 건만 허용하고 실제 부분익절 체결은 한 번만 적용한다. scale-in 재확인을 위한 취소 뒤에는 cooldown·잔고·수량·자격을 처음부터 다시 통과해야 재제출할 수 있다.
  - 보유수량이 2주 이상이고 entry bundle이 terminal이며 pending entry·추가매수·기존 SELL이 없다.
  - 진입 후 policy observation window 120초 안이며 fresh·conflict-free quote를 사용한다.
  - 방향이 `HARD_NEGATIVE`·`UNKNOWN`이 아니고 최소 3개 tick, 2초 observation span, 0.6% observed range를 충족한다.
  - 동일 cycle의 부분익절 체결·재무장 금지 상태가 없고 broker 잔고 재조회 수량이 runtime 보유수량과 정확히 일치한다.
- 주문수량은 `floor(확인 보유수량 × 0.35)`를 기본으로 최소 1주, 최대 `보유수량-1주`로 제한하여 runner를 최소 1주 남긴다. 지정가는 새 평단에서 거래비용을 반영한 순이익 +0.55% 목표가를 호가단위로 올림한 값이다.
- broker submit은 `order_type=00`, 계산된 `limit_price`, 해당 cohort의 명시적 `dmst_stex_tp`를 사용한다. 이름이 market-order wrapper인 호출 경로라도 `price=0` 시장가로 바꾸거나 route를 암묵 추정하지 않는다.
- submit 전 `SUBMITTING` 상태를 durable ledger에 먼저 기록하고 주문번호 수신 뒤 `OPEN`으로 확정한다. partial/full receipt는 reserved·filled 수량과 금액을 ledger/runtime/DB에 조정하고 최종 runner 청산 손익과 합산하되 partial fill과 full fill 표본은 분리 귀속한다.
- TTL 210초가 지나면 session 경계 이후라도 해당 원 route로 주문을 취소하고 broker 미체결·잔고를 재조회한다. ledger 저장 실패, 주문번호 결손, 취소·체결 reconciliation 실패 시 중복 제출하지 않고 `FAILED_RECONCILIATION` 또는 재확인 상태로 닫는다.
- 미체결 조기 부분익절이 있는 상태에서 scale-in을 검토하면 먼저 취소·재확인한다. 부분익절 체결 뒤 avg-down은 차단하고 pyramid는 명시적 strong-continuation 조건을 통과한 경우만 기존 scale-in guard 아래에서 검토한다.
- hard/emergency/trailing full exit가 발생하면 조기 부분익절보다 우선한다. 기존 지정가를 취소하고 broker 잔고·추가 체결을 재조회한 뒤 확인 수량만 청산하며, 취소 확인 전 겹치는 full SELL을 제출하지 않는다.
- 수량 불변식 위반, 중복 부분익절, hard/full-exit 지연, 취소·체결 reconciliation 실패, route mismatch 또는 cross-cohort attribution이 한 번이라도 발생하면 해당 KRX/NXT/PREMARKET `*_ENABLED` 축만 false로 전환하고 graceful restart한다. 다른 cohort와 entry/fast-exit 축은 함께 끄지 않으며, rollback 대상 policy version의 ledger 미체결 주문만 취소·재조회·조정한다.
- `early_volatility_tp_decision_observed`, `early_volatility_tp_order_sent`, receipt·cancel·reconciliation event를 cohort/policy version/route별로 집계한다. 현재 KRX/NXT의 eligible·submitted·filled 표본은 0건이므로 `policy loaded/runtime active`까지만 확인하고 최종 판정은 `insufficient_sample_keep_observing`으로 닫으며 효과 확정으로 표현하지 않는다.

### 250ms fast exit와 청산 우선순위

- monitor는 실제 `SCALPING + HOLDING` 포지션만 250ms 주기로 확인한다. 신규 AI 분석, holding-flow AI, scale-in feature refresh, 평균단가 보완 판단을 수행하지 않는다.
- 기존 `SCALP_TRAILING_START_PCT`, weak/strong trailing limit, hard/protect/emergency 값을 그대로 사용한다. AI score가 fresh하지 않으면 기존처럼 보수적인 weak 기준을 적용한다.
- fresh WS executable 가격이 기존 trailing worsen floor를 넘으면 atomic 단일 exit token을 선점한다. token 선점 즉시 신규·추가 BUY와 probe residual 제출을 차단하고 다음 순서를 지킨다.
  1. 미체결 BUY residual과 기존 부분익절 SELL을 취소한다.
  2. 브로커 잔고와 체결 수량을 다시 조회한다.
  3. 확인된 보유수량만 매도한다.
  4. 취소 중 추가 체결이 확인되면 동일 token으로 증가분만 후속 매도한다.
- exit 결정 뒤 holding-flow AI, scale-in refresh, 평균단가 보완, trailing continuation 재검토를 실행하지 않는다. 다만 주문수량, 계좌, 중복주문, 가격 freshness, broker guard는 우회하지 않는다.
- WS가 stale이면 token을 먼저 만들지 않고 기존 bounded REST 재검증을 거쳐 재시도한다. 최초 유효 가격의 기준 이탈부터 broker SELL API 호출까지 `decision_to_order_sent_ms <= 500`을 목표·rollback 기준으로 관측한다.
- 상태에는 `probe_confirmation_count`, `probe_expand_forbidden`, `peak_basis_qty`, `peak_basis_avg_price`, `exit_token`, `exit_decided_at`, `exit_order_sent_at`을 남긴다. 이벤트에는 AI veto, probe 평가별 독립 신호, 기준 이탈 가격·시각, cancel/reload/sell 수량과 청산 지연을 남긴다.
- 새 관측값은 생성 시 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 모두 선언한다. 계약이 없으면 runtime 판단에 사용하지 않고 `instrumentation_gap` 또는 `source_quality_blocker`로만 보낸다.

## 감시~청산 AI 입력 공통 사전점검

- 실주문 SCALPING의 `감시 -> 진입 재확인 -> Gatekeeper -> entry-price -> post-probe/leg-reprice -> holding/scale-in -> exit -> overnight`는 `ai_market_snapshot_v1`과 `ai_input_preflight_v1`을 공통 source-quality 계약으로 사용한다.
- 각 호출은 snapshot ID, decision stage, effective venue cohort, broker order route, market-data route, underlying event venue, session bucket과 current price/BBO/tape/candle/program/investor/broker position/open orders의 source·observed time·age·suffix·route·quality·missing reason을 남긴다. 결손값은 `null + missing_reason`이며 실제 0으로 보간하지 않는다.
- WS route 판정은 aggregate suffix보다 0B·0D별 `last_realtime_type_item/suffix/route/effective_venue/ts`를 우선한다. cohort는 `PREMARKET_KRX_LIKE/KRX/NXT_REGULAR_OVERLAP/NXT_AFTERMARKET/OVERNIGHT`, broker route는 `KRX/NXT/SOR`, market-data route는 `krx_only/nxt_only/krx_nxt_integrated`의 직교 차원이다. 실주문 SCALPING route는 `KRX 정규장=SOR`, `PREMARKET_KRX_LIKE=NXT`, `NXT=NXT`로 검증하며 KRX 정규장 `broker_route=SOR`를 별도 venue나 오염으로 판정하지 않는다. 통합 시세의 underlying event venue가 증명되지 않으면 `UNKNOWN + missing reason`으로 보존하며 NXT 전용 판단 근거로 쓰지 않는다.
- preflight blocked이면 entry/watch/Gatekeeper/holding score/holding-flow provider 호출은 0회여야 한다. entry는 DROP/WAIT, holding score는 unusable 50, holding-flow는 deterministic exit 후보 유지, overnight는 `SELL_TODAY`로 닫는다. post-probe/leg-reprice에는 새 AI 호출을 만들지 않고 사용한 AI snapshot과 fresh market snapshot을 함께 기록한다.
- scale-in support와 AI exit defer는 fresh broker holding qty, open BUY/SELL order, snapshot age와 venue-matching broker route가 정합할 때만 허용한다. hard/protect/emergency/trailing, P1 가격 owner, 중앙 수량 owner와 provider route는 변경하지 않는다.
- 첫 적용은 clean baseline 이후 real 이벤트 replay로 생성한 `ai_input_quality_baseline_YYYY-MM-DD.json`의 `baseline_v1` 보호 정책을 사용한다. 이 artifact는 legacy quality proxy와 downstream 실주문 route lineage로 결손·stale·conflict 패턴을 재현하지만 이를 exact provider-input provenance로 승격하지 않는다. provider/scale-in/exit-defer/overnight HOLD 권한을 줄이는 데만 사용하며 real overnight broker reconciliation처럼 검증 표본이 없는 경로는 제한형으로 유지한다.
- `entry_context_intraday_probe_YYYY-MM-DD.json`의 venue/session/decision-point exact matrix는 `exact_v2` 승격 기준이다. clean baseline 이후 exact provenance row만 사용하며 valid row가 0인 cohort는 `not_ready`다. venue cohort를 합산하거나 SOR 주문 route를 venue로 세거나 `baseline_v1` proxy 표본으로 exact matrix를 통과시키지 않는다. 각 provider payload에는 schema, SHA-256, byte size, snapshot ID, venue/broker/market-data route와 canonical candle owner를 남기며 동일 분봉을 summary/raw/context로 중복 전송하지 않는다.
- `KORSTOCKSCAN_AI_INPUT_PREFLIGHT_MODE=baseline_v1|exact_v2`를 명시한다. 선택 mode의 artifact가 없거나 계약이 손상되면 enhanced AI 입력은 fail-closed한다. 현재 PID 기동 후 생성된 PASS artifact는 `ready_pending_restart`이며 artifact보다 나중에 시작된 graceful restart PID에서만 활성화한다.
- AI 판단 품질은 input preflight와 별도로 `ai_decision_trace_v1`로 관측한다. 감시/진입, Gatekeeper, entry-price, holding score/flow, overnight는 immutable `decision_trace_id`, prompt·payload SHA-256, sanitized exact input, provider/model/action/score, snapshot·venue·route와 lifecycle correlation을 남긴다. post-probe는 원래 entry trace ID를 `probe_bundle_id`에 전파하며 신규 AI 호출을 만들지 않는다.
- exact user input과 prompt는 각각 hash별 1회 registry에 저장한다. 민감 필드가 탐지되면 값을 제거하고 `replay_exact=false`로 표시하며, redacted payload를 exact replay 입력으로 사용하지 않는다. trace 저장 실패가 provider·주문·기존 deterministic 판단을 바꾸어서는 안 된다.
- 각 trace는 `ai_decision_outcome_label_v1` pending 행을 만들고 1/3/5/10/20/30/60분 horizon이 성숙한 뒤 별도 producer가 MFE/MAE, target/adverse first-hit, submit/fill/PnL을 연결한다. trace와 counterfactual은 `runtime_effect=false`, `allowed_runtime_apply=false`이며 실현손익과 합산하거나 단독 prompt/runtime 승격 근거로 사용하지 않는다.

## KRX 작업지시문

`[종료시각]`까지 EV 및 순이익 극대화를 위한 KRX 장중 모니터링·보완 작업을 수행한다.

### 런타임·cohort 기준

- 작업 시작 시 현재 가동 PID, start 시각, 로드된 commit/source, runtime env, selected family, 요청·실제 provider route, WS 연결·로그인·0B/0D 최초 수신과 runtime provenance를 확인한다.
- 저장소 최신 코드와 실행 PID 반영 상태를 분리한다. 구현됐더라도 현재 PID에 반영되지 않았으면 `implemented_not_runtime_reflected`로 기록한다.
- 분석 표본은 `effective_venue=KRX`가 명시된 KRX 정규장으로 제한한다. NXT, `PREMARKET_KRX_LIKE`, `OFF_SESSION`, venue unknown 표본을 KRX EV·threshold 판단에 섞지 않는다.
- venue provenance가 충돌·결손·복원 불가한 표본은 성과 및 threshold 판단에서 제외한다. clean baseline 이후 source-quality gate를 통과한 real submit/receipt/fill/PnL, sim/probe, counterfactual을 분리한다.

### 진입 funnel·가격·수량

- Rising Missed는 진입종목 선정 전략이고, probe-first는 Rising Missed를 포함한 모든 실주문 SCALPING 신규진입의 1주 시장가 우선 체결 경로다.
- TP1/Freshness Envelope의 `pass/block/defer`, WS 0B/0D 결측·노후화·conflict, effective source, REST 선택·budget defer와 다음 scanner loop 회복을 분리 집계한다.
- 실제 timestamp와 correlation id로 다음 흐름을 재구성한다.

  `scanner_watch_budget -> candidate_gate -> TP1/Freshness Envelope -> provisional allocator -> P1 initial -> final price/sizing revalidation -> submit_safety -> broker/account/order/quantity/cooldown -> 1주 probe -> receipt/fill -> P1 post_probe -> residual leg_reprice`

- 최초 blocker, 중복 blocker, silent return, broker 호출 누락, 다음 loop 재평가와 최종 submit/fill을 구분한다. post-block 직접 submit retry는 복원하지 않는다.
- stale/missing/conflict source는 완화 근거가 아니다. block/defer 후보는 동일 KRX cohort의 MFE/MAE, target/adverse first-hit, 관찰 horizon과 회복 시각을 확인하되 counterfactual을 실현손익과 합산하지 않는다.
- stale/conflict, tick-speed, weak same-symbol micro reentry, latency, observed-mark gap, broker/account/order/quantity/cooldown을 별도 blocker로 집계한다.
- 진입가격은 `dynamic_entry_price_resolver_p1`의 `initial -> post_probe -> leg_reprice`, 수량은 `position_sizing_dynamic_formula`의 `entry_type_5stage_cap25_v1`을 단일 owner로 유지한다. 별도 owner, legacy fixed-offset fallback, 무조건 추격매수를 만들지 않는다.
- 최종 가격 변경 뒤 `scalping_sizing_final_price_revalidated`를 확인한다. 재판정은 기존 계획보다 수량을 늘리지 않으며 planned/requested/submitted/filled 수량 불변식을 지킨다.
- probe 체결 뒤 공통 AI action·2회 확인 계약과 fresh BBO·micro·방향을 함께 재검증한다. BUY 권한의 기존 `STRONG=narrow`, `NEUTRAL=normal`, `WEAK|UNKNOWN=recheck`, 회복 후 `RECOVERED_WIDE`, `HARD_NEGATIVE=abort` 기회 경로는 유지하되, WAIT은 두 번의 강한 확인을 통과한 첫 residual leg만 허용하고 DROP은 항상 abort한다.

### holding·scale-in·exit

- shallow avg-down은 holding/exit matrix bias, scale-in resolver, 최초 tier 재사용, 중앙 allocator, 보유수량, pending order, probe residual 상태를 함께 확인한다.
- 추가매수 counterfactual은 추가 MFE와 추가 MAE·하방 노출을 함께 평가한다.
- latency 의미는 `SAFE/CAUTION -> slippage·freshness 재확인 후 submit`, `stale -> block`, `DANGER -> 기본 block`으로 유지한다. DANGER 예외는 이미 선택된 bounded capability의 venue·source·probe·가격 계약을 모두 만족한 경우에만 해당 owner 안에서 허용하며 일반 완화로 확장하지 않는다.
- 익절 umbrella owner는 `scalp_trailing_take_profit`으로 유지하고, 조기 지정가 부분익절은 공통 runtime 계약의 bounded coordinator로만 동작한다. TP1/partial/runner/trailing 순서, peak giveback, 청산 후 MFE와 runner 유지시간을 함께 확인한다.
- `rising_missed_reversal_pre_submit_guard`, `reversal_up_watch`, `reversal_up_volatile_watch`는 watch/recheck와 실제 broker submit을 분리한다.
- fast-exit event에서는 token 선점 전 fresh executable price와 KRX 정규장 `dmst_stex_tp=SOR` route를 확인하고, 선점 뒤 공통 cancel→reload→sell 순서와 동일 token 증가분 후속 매도를 확인한다. token 이후 AI·scale-in·평단보완 호출이 0회인지 검증한다.

### 코드개선·기존 real 누적실적 검증 계약

- 당일 손실, 진입 병목, 익절 또는 기타 코드결함은 `당일 사례 분류 -> 원인·단일 owner 확인 -> 구현 -> 코드리뷰 -> clean-baseline 기존 real replay/reconstruct -> 결함 보완 -> 재리뷰·재검증 -> runtime 적용/rollback 판정` 순서로 처리한다.
- 기존 real 데이터는 명확한 코드결함 구현의 선행조건이 아니다. 구현 후 일반화·부작용 검증 입력으로 사용하며, 표본 부족만으로 결함 수정을 보류하지 않는다.
- `2026-06-04T14:29:09+09:00` 이후 explicit KRX 정규장 real 행만 사용한다. 동일 predicate, stage owner, AI action, latency state, entry lineage, probe/residual, policy version을 가능한 범위에서 재구성한다.
- 실현손익은 `COMPLETED + valid profit_rate`만 사용하고 full/partial fill을 분리한다. sim/probe/counterfactual, incomplete/NULL PnL, pre-baseline 자료는 real EV와 합산하지 않는다.
- 새 필드가 과거 row에 없으면 임의 보간하지 않고 `implemented_insufficient_history_keep_guarded`로 닫는다. source-quality가 유효한 부분집합만 검증하며 결손 row/window는 제외한다.
- 손실 개선은 회피손실과 차단될 수익기회를, 진입 병목 개선은 추가 submit/fill과 adverse entry를, trailing 개선은 이익보호와 post-sell MFE/MAE·giveback을 함께 비교한다.
- replay에서 권한 누출, 과차단, 과제출, 수량·가격 불변식 위반 또는 EV 악화가 발견되면 즉시 보완하고 review gate를 다시 통과하기 전 runtime에 반영하지 않는다.

### 장중 적용·보고

- explicit KRX cohort의 operator-directed 지시가 있으면 기존 stage owner의 `bounded_tunable` 단일 축만 최소 범위로 변경할 수 있다. 변경 전 fresh/conflict-free source, 유효 effective price, 충분한 opportunity evidence, 단일 blocker 인과와 same-stage canary 무충돌을 확인한다.
- 변경 전후 값, stage/cohort, 근거 event, 적용 시각, env/PID provenance, rollback 값·발동 조건과 post-apply attribution을 기록한다.
- hard/protect/emergency safety, stale/conflict, 가격 freshness, broker/account/order/quantity/cooldown, provider, PID, cap, 요청수량 확대는 완화하거나 우회하지 않는다.
- entry AI-action guard와 holding/exit fast-exit guard는 stage-disjoint 축으로 각각 기록하고 독립 rollback한다. 중복 BUY/SELL, 초과매도, monitor 예외 또는 유효 표본의 `decision_to_order_sent_ms > 500`이 한 번이라도 발생하면 해당 stage 축을 OFF하고 graceful restart 뒤 직전 배포 상태와 런타임 provenance를 재확인한다.
- 모든 보고는 `판정 -> 근거 -> 다음 액션` 순서로 작성하고 최종 판정은 `runtime_healthy_no_change | bounded_change_applied_attributed | source_quality_gap | code_improvement_required | implemented_not_runtime_reflected | implemented_historical_real_validation_pass | implemented_needs_supplement | implemented_insufficient_history_keep_guarded | rollback_required | insufficient_sample_keep_observing` 중 하나 이상으로 닫는다.

## NXT 작업지시문

`[종료시각]`까지 현행 NXT 거래 런타임을 기준으로 EV 및 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다.

### 적용 범위와 격리

- 분석 표본은 `nxt_entry_window=true`이면서 `effective_venue=NXT`가 명시된 표본으로 제한한다. KRX, `PREMARKET_KRX_LIKE`, `OFF_SESSION`, venue unknown과 혼합하지 않는다.
- 작업 시작 시 PID/start, commit/source, runtime env, selected family, provider route, WS 0B/0D와 NXT provenance를 확인하고 저장소 구현과 현재 PID 반영을 분리한다.
- NXT 결과로 공통/KRX 로직·threshold·runtime env를 오염시키지 않는다. NXT 고유 특성은 기존 NXT family 또는 capability/profile 내부에서만 다룬다.
- 진입가격은 P1, 수량은 중앙 allocator, scale-in은 기존 scale-in owner가 계속 단일 권한을 가진다. 익절 umbrella는 `scalp_trailing_take_profit`, 조기 지정가 부분익절은 그 아래 cohort별 bounded coordinator로 유지한다.
- clean baseline 이후 유효 source-quality NXT 표본만 사용하고 real, sim/probe, counterfactual을 분리한다.

### 진입·submit·holding 점검

- Rising Missed와 probe-first의 의미, 전체 funnel 재구성, blocker 분리, 직접 submit retry 금지, P1/allocator 수량 불변식은 KRX 지시문과 동일하게 적용한다.
- NXT TP1/Freshness Envelope의 pass/block/defer, WS 0B/0D micro, REST orderbook/signed-tape, REST budget defer와 다음 scanner loop 회복을 집계한다.
- stale/missing/conflict 및 signed-tape 결손은 `nxt_specific_observation_gap`이다. 실제 sell-dominated tape는 방어 근거이고 BUY 지지로 전환하지 않는다.
- `rising_missed_tick_speed_entry_guard`, stale latency, 가격 freshness, broker/account/order/quantity/cooldown, 중복주문, `MAX_POSITION_PCT`, 95% safe budget은 우회하지 않는다. DANGER는 기본 block이며 기존 NXT bounded capability의 완전한 계약을 만족할 때만 해당 owner 내부 예외로 평가한다.
- NXT fast-tape capability는 exact NXT cohort, marginal depth 단일 실패, fresh trusted WS tape, positive OFI, event-time speed, probe-first/P1 post-probe 조건을 모두 만족할 때만 평가한다. fast tape는 독립 신호 그룹 1개일 뿐이며 첫 강신호 한 번만으로 확대하지 않는다. AI WAIT은 공통 250ms 간격 2회 강한 확인 뒤 첫 residual leg 1개만 허용한다. KRX 적용, stale/conflict, fresh AI DROP 통과 또는 WAIT residual 2개 이상 제출은 결함이다.
- probe/residual, shallow avg-down, trailing/runner, reversal guard는 NXT source와 체결 특성 기준으로 판단하되 기존 owner를 바꾸지 않는다.
- 신규 BUY, residual, fast exit의 실제 broker order는 `dmst_stex_tp=NXT`를 명시한다. KRX-only source, entry cohort와 route conflict, actual NXT 0D 또는 NXT-suffix REST provenance 결손은 submit/token 이전에 차단한다.
- 동일 position cycle이 `HOLDING + buy_qty>0 + entry_execution_broker_route=NXT`로 확인되면 체결이 확정한 NXT entry route를 stale DB `is_nxt=false`보다 우선한다. 이 복구 규칙은 NXT provenance 결손을 임의 추정하는 일반 fallback이 아니다.
- NXT fast exit도 공통 단일 token과 cancel→reload→sell 순서를 사용한다. route/source guard를 통과하기 전 token을 만들지 않으며 token 이후 AI·scale-in·평단보완 호출이 없어야 한다.

### 코드개선·기존 real 누적실적 검증 계약

- 처리 순서는 `당일 NXT 사례 -> 원인·NXT 단일 owner -> 구현 -> 코드리뷰 -> clean-baseline NXT real replay/reconstruct -> 결함 보완 -> 재리뷰·재검증 -> NXT runtime 적용/rollback`이다.
- 기존 real 표본 부족은 명백한 결함 구현의 선행 blocker가 아니다. 구현 후 같은 `nxt_entry_window + effective_venue=NXT` cohort에서 일반화와 부작용을 검증한다.
- 과거 row에 신규 event-time/source 필드가 없으면 속도나 freshness를 추정해 pass 처리하지 않는다. 관측 가능한 조건만 partial replay하고 `implemented_insufficient_history_keep_guarded`로 닫은 뒤 신규 post-apply attribution을 요구한다.
- 실현손익은 clean baseline 이후 `COMPLETED + valid profit_rate`만 사용하고 full/partial fill을 분리한다. counterfactual target/adverse first-hit와 MFE/MAE는 별도 NXT 관측 EV로 유지한다.
- 손실·진입 병목·trailing·기타 개선별 검증 축은 KRX 계약과 동일하되 KRX/PREMARKET 표본을 보강 표본으로 섞지 않는다.
- replay에서 common/KRX 오염, stale submit, owner 파편화, probe 없는 residual, 첫 leg cap 위반, 수량·가격 불변식 위반, slippage·adverse-first 증가가 발견되면 즉시 보완하고 review gate를 반복한다.

### NXT 장중 적용·보고

- explicit NXT operator-directed 지시가 있으면 기존 NXT family/capability의 `bounded_tunable` 단일 축만 최소 변경한다. NXT 전용 분기 없이 공통/KRX 변경이 필요하면 적용하지 않고 `nxt_runtime_capability_required`로 닫는다.
- 변경 전후 값, stage/NXT cohort, 근거 event, env/PID provenance, rollback과 NXT post-apply attribution을 남긴다.
- hard safety, stale/conflict, 가격 freshness, tick-speed guard, broker/account/order/quantity/cooldown, provider, PID, cap, 요청수량 확대는 완화하지 않는다.
- entry와 holding/exit 긴급 축은 NXT에서도 독립 rollback한다. 중복주문·초과매도·monitor 예외·500ms 초과가 한 번이라도 확인되면 해당 축을 OFF하고 graceful restart한다.
- 모든 보고는 `판정 -> 근거 -> 다음 액션` 순서로 작성하고 최종 판정은 `nxt_runtime_healthy_no_change | nxt_specific_bounded_change_applied_attributed | nxt_specific_observation_gap | nxt_runtime_capability_required | common_runtime_contamination_detected | implemented_not_runtime_reflected | implemented_historical_real_validation_pass | implemented_needs_supplement | implemented_insufficient_history_keep_guarded | rollback_required | insufficient_nxt_sample_keep_observing` 중 하나 이상으로 닫는다.

## PREMARKET_KRX_LIKE 작업지시문

`[종료시각]`까지 `08:00~08:50 KST`의 명시적 `PREMARKET_KRX_LIKE` 관측 cohort와 실제 NXT broker route를 기준으로 EV 및 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다.

### 적용 범위와 venue 권한

- `PREMARKET_KRX_LIKE`는 KRX-like 특성을 관측하는 별도 cohort지만 실제 broker order route는 NXT다. KRX 정규장이나 일반 NXT EV·threshold 표본에 합산하지 않는다.
- 시간대만으로 PREMARKET cohort를 추정하지 않는다. 명시적 cohort, `dmst_stex_tp=NXT`, actual NXT 0D 또는 NXT-suffix REST provenance가 일치해야 한다.
- KRX-only source, entry cohort/route conflict, NXT 거래 가능성 또는 provenance 결손은 source-quality gap으로 차단한다. 실제 NXT 체결 route가 확정된 holding cycle의 stale DB 복구는 NXT 지시문과 동일하게 제한 적용한다.
- 작업 시작 시 PID/start, commit/source, runtime env, PREMARKET policy active date, WS/REST source와 actual broker route를 확인한다. 구현·정책 파일 존재와 현재 PID 반영을 분리한다.

### 진입·probe·holding·exit

- fresh DROP veto, WAIT 1주 probe, BUY 기존 동적 수량, AI 결손 fail-closed와 WAIT residual 2회 확인은 공통 긴급 안전 계약을 그대로 적용한다.
- PREMARKET에서 signed tape가 제공되지 않거나 품질 gate를 통과하지 못하면 양수로 보간하지 않는다. 이 경우 `가격/틱`과 `호가` 두 독립 그룹이 모두 양수이고 음수 그룹이 없어야 하며, 단일 fast-tape 신호만으로 residual을 확대하지 않는다.
- BUY 권한의 기존 NEUTRAL 정상 확대 기회는 유지하되 WAIT은 첫 residual leg만 허용한다. DROP, 약세, stale/conflict, stop, TTL 만료 시 residual을 폐기하고 해당 cycle 확대를 금지한다.
- partial TP와 full exit는 실제 NXT route로만 처리한다. 조기 지정가 부분익절은 active date가 일치할 때 공통 runtime 계약을 적용하고, fast exit는 route/source 확인 뒤 공통 단일 token과 cancel→reload→sell 순서를 적용하며 `decision_to_order_sent_ms <= 500`, 중복 SELL 0, 초과매도 0을 검증한다.
- PREMARKET 조기 부분익절은 별도 policy/version과 `2026-07-24` active date로 귀속한다. KRX/NXT 당일 정책의 표본 또는 효과로 소급·혼합하지 않는다.

### PREMARKET 장중 적용·보고

- PREMARKET 근거로 공통/KRX threshold나 runtime env를 변경하지 않는다. operator-directed 변경은 명시적 PREMARKET cohort와 실제 NXT route를 가진 기존 bounded owner 안에서만 검토한다.
- 변경 전후 값, cohort/route, policy active date, PID/env provenance, source-quality, rollback과 post-apply attribution을 기록한다. entry와 holding/exit 긴급 축은 독립 rollback한다.
- 중복 BUY/SELL, 초과매도, route 오염, monitor 예외 또는 500ms 초과가 한 번이라도 발생하면 해당 stage 축을 OFF하고 graceful restart 뒤 직전 배포 상태를 확인한다.
- 모든 보고는 `판정 -> 근거 -> 다음 액션` 순서로 작성하고 최종 판정은 `premarket_runtime_healthy_no_change | premarket_specific_bounded_change_applied_attributed | premarket_specific_observation_gap | premarket_runtime_capability_required | venue_route_contamination_detected | implemented_not_runtime_reflected | rollback_required | insufficient_premarket_sample_keep_observing` 중 하나 이상으로 닫는다.

## 당일 postclose 귀속

- entry는 fresh DROP 차단 수, WAIT 1주 probe 수, WAIT residual 확대·폐기 수, BUY 권한의 기존 확대 수와 차단될 수익기회를 분리한다.
- 조기 지정가 부분익절은 eligible·submitted·partial/full fill·TTL cancel·reconciliation 실패·runner 결과를 policy version/cohort/route별로 분리하고, 표본이 없으면 `policy loaded/runtime active`와 `insufficient_sample_keep_observing`을 구분해 기록한다.
- exit는 기준 이탈 수, token 선점 수, 조기 부분익절 cancel/reload/sell 수량, 후속 증가분 매도, `decision_to_order_sent_ms`, 중복·초과매도와 실제 체결 손익을 venue/cohort별로 분리한다.
- source-quality 경고와 실현손익을 섞지 않는다. 실현손익은 clean baseline 이후 `COMPLETED + valid profit_rate`만 사용하고 partial/full fill을 분리한다.
- 다음 PREOPEN에는 entry guard와 fast-exit guard를 각각 영구 활성화, 당일 연장, 보완 후 재검증, rollback 중 하나로 판정한다. 조기 부분익절 정책은 별도 owner·version·표본으로 귀속한다.
