# KRX/NXT 장중 모니터링 작업지시문

이 문서는 KRX 정규장과 NXT 거래 구간의 복사 가능한 canonical 작업지시문이다. 실제 종료 시각만 작업 시작 전에 채운다.

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
- probe 체결 뒤 fresh BBO·micro·방향을 재검증한다. `STRONG=narrow`, `NEUTRAL=normal`, `WEAK|UNKNOWN=recheck`, 회복 후 `RECOVERED_WIDE`, `HARD_NEGATIVE=abort`와 residual leg별 P1 reprice를 확인한다.

### holding·scale-in·exit

- shallow avg-down은 holding/exit matrix bias, scale-in resolver, 최초 tier 재사용, 중앙 allocator, 보유수량, pending order, probe residual 상태를 함께 확인한다.
- 추가매수 counterfactual은 추가 MFE와 추가 MAE·하방 노출을 함께 평가한다.
- latency 의미는 `SAFE/CAUTION -> slippage·freshness 재확인 후 submit`, `stale -> block`, `DANGER -> 기본 block`으로 유지한다. DANGER 예외는 이미 선택된 bounded capability의 venue·source·probe·가격 계약을 모두 만족한 경우에만 해당 owner 안에서 허용하며 일반 완화로 확장하지 않는다.
- 익절은 `scalp_trailing_take_profit` owner 아래 TP1/partial/runner/trailing 순서, peak giveback, 청산 후 MFE와 runner 유지시간을 확인한다.
- `rising_missed_reversal_pre_submit_guard`, `reversal_up_watch`, `reversal_up_volatile_watch`는 watch/recheck와 실제 broker submit을 분리한다.

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
- 모든 보고는 `판정 -> 근거 -> 다음 액션` 순서로 작성하고 최종 판정은 `runtime_healthy_no_change | bounded_change_applied_attributed | source_quality_gap | code_improvement_required | implemented_not_runtime_reflected | implemented_historical_real_validation_pass | implemented_needs_supplement | implemented_insufficient_history_keep_guarded | rollback_required | insufficient_sample_keep_observing` 중 하나 이상으로 닫는다.

## NXT 작업지시문

`[종료시각]`까지 현행 NXT 거래 런타임을 기준으로 EV 및 순이익 극대화를 위한 장중 모니터링·보완 작업을 수행한다.

### 적용 범위와 격리

- 분석 표본은 `nxt_entry_window=true`이면서 `effective_venue=NXT`가 명시된 표본으로 제한한다. KRX, `PREMARKET_KRX_LIKE`, `OFF_SESSION`, venue unknown과 혼합하지 않는다.
- 작업 시작 시 PID/start, commit/source, runtime env, selected family, provider route, WS 0B/0D와 NXT provenance를 확인하고 저장소 구현과 현재 PID 반영을 분리한다.
- NXT 결과로 공통/KRX 로직·threshold·runtime env를 오염시키지 않는다. NXT 고유 특성은 기존 NXT family 또는 capability/profile 내부에서만 다룬다.
- 진입가격은 P1, 수량은 중앙 allocator, scale-in은 기존 scale-in owner, 익절은 `scalp_trailing_take_profit`이 계속 단일 권한을 가진다.
- clean baseline 이후 유효 source-quality NXT 표본만 사용하고 real, sim/probe, counterfactual을 분리한다.

### 진입·submit·holding 점검

- Rising Missed와 probe-first의 의미, 전체 funnel 재구성, blocker 분리, 직접 submit retry 금지, P1/allocator 수량 불변식은 KRX 지시문과 동일하게 적용한다.
- NXT TP1/Freshness Envelope의 pass/block/defer, WS 0B/0D micro, REST orderbook/signed-tape, REST budget defer와 다음 scanner loop 회복을 집계한다.
- stale/missing/conflict 및 signed-tape 결손은 `nxt_specific_observation_gap`이다. 실제 sell-dominated tape는 방어 근거이고 BUY 지지로 전환하지 않는다.
- `rising_missed_tick_speed_entry_guard`, stale latency, 가격 freshness, broker/account/order/quantity/cooldown, 중복주문, `MAX_POSITION_PCT`, 95% safe budget은 우회하지 않는다. DANGER는 기본 block이며 기존 NXT bounded capability의 완전한 계약을 만족할 때만 해당 owner 내부 예외로 평가한다.
- NXT fast-tape capability는 exact NXT cohort, marginal depth 단일 실패, fresh trusted WS tape, positive OFI, event-time speed, probe-first/P1 post-probe 조건을 모두 만족할 때만 평가한다. AI WAIT은 최소 1회 재확인하고 유지된 fast tape에서 첫 residual leg 1개만 허용한다. KRX 적용, stale/conflict, fresh AI DROP 통과 또는 residual 2개 이상 제출은 결함이다.
- probe/residual, shallow avg-down, trailing/runner, reversal guard는 NXT source와 체결 특성 기준으로 판단하되 기존 owner를 바꾸지 않는다.

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
- 모든 보고는 `판정 -> 근거 -> 다음 액션` 순서로 작성하고 최종 판정은 `nxt_runtime_healthy_no_change | nxt_specific_bounded_change_applied_attributed | nxt_specific_observation_gap | nxt_runtime_capability_required | common_runtime_contamination_detected | implemented_not_runtime_reflected | implemented_historical_real_validation_pass | implemented_needs_supplement | implemented_insufficient_history_keep_guarded | rollback_required | insufficient_nxt_sample_keep_observing` 중 하나 이상으로 닫는다.
