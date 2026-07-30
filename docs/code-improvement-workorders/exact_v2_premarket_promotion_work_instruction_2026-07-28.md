# Exact V2 PREMARKET Promotion 재검증 및 자연표본 Baseline 전환

## 작업 정보

- 실행일: `2026-07-28 KST`
- PREMARKET 검증 창: `08:20~08:40 KST`
- 실행 순서: `PREMARKET 재검증 -> binary promotion 판정 -> PASS 시 자연 exact_v2 수집 -> outcome 성숙 -> Control baseline 판정`
- runtime 승격 권한: 이 문서에 정의된 다중분봉 문맥의 binary full-market promotion만 허용
- 판단품질 실험 권한: promotion 이후 자연 exact_v2 표본을 사용하는 offline 관찰만 허용

## 목적

- 현재 정상 작동 중인 exact context capture 계측을 유지한다.
- `canonical_context_missing`, `canonical_completed_bars_missing`, compact forensic payload, `baseline_v1` 호출은 삭제하거나 사후 보정하지 않고 제외 증거로 보존한다.
- `2026-07-28 PREMARKET`에서 multi-timeframe context의 binary full-market promotion을 재검증한다.
- PASS이면 같은 promotion transaction에서 전 스캘핑 종목, 전 활성 세션, 모든 적용 endpoint에 문맥을 전면 적용하고, 이후 자연 exact_v2 표본 수집과 Control baseline 성숙을 시작한다.
- source-quality 검증은 정기 감시로 유지하되, promotion 이후 eligible cohort가 생긴 뒤 판단품질 baseline 작업을 불필요하게 지연시키지 않는다.

## 현재 상태와 출발점

- historical evidence: `2026-07-27 15:46:22 KST` PID `342799`, commit `0dea2b31`, `source_dirty=false` runtime에 exact capture 보완 `c016ab2b`가 반영됐다. 이 기록은 현재 runtime authority가 아니다.
- current startup evidence: `2026-07-28 07:55:02 KST` PID `712183`은 commit `436b98e5e721b7ddeae18e42d4f8a98a15522194`를 로드했고 scanner scheduler `async_v1` 초기화까지 통과했다. 그러나 `KORSTOCKSCAN_RUNTIME_SOURCE_DIRTY=true`이므로 clean runtime acceptance 또는 PREMARKET promotion evidence로 사용할 수 없다.
- current effective env는 holding decision/score/flow/overnight cohort keys를 모두 `true`로 로드했지만, `input_preflight_mode=baseline_v1`이다. `2026-07-28` exact validation, promotion, first-observation, decision request/trace artifact는 아직 없다.
- 실제 현재 코드·PID env 재현에서 promotion activation은 `promotion_artifact_required_missing_or_invalid`이며 `promotion_artifact_required=true`다. 따라서 `holding_score`와 `holding_flow`의 effective context는 `NXT=true`, `KRX=false`, `PREMARKET_KRX_LIKE=false`다. 이는 full-market PASS가 아니라 failed/missing promotion artifact에서 기존 NXT holding context만 보존하는 bounded fallback이다.
- 최신 promotion artifact는 `2026-07-27`의 `decision=blocked_provider_or_schema`, `runtime_activation=false`다. 필수 endpoint exact request와 필수 symbol/route source·payload match가 충족되지 않았으므로 전면 승격되지 않았다.
- current decision: `blocked_review_or_env`. 이 문서는 현 PID에 대해 promotion validation-only 호출, runtime activation, first-observation hook, exact_v2 Control/Baseline 수집을 승인하지 않는다.
- clean review·commit·graceful restart로 `source_dirty=false` PID와 runtime-env handoff가 확인된 경우에만, 같은 날 PREMARKET 창에서 이 문서의 재검증을 재개한다. 이 문서 자체는 restart를 실행하거나 승인하지 않는다.
- promotion 이전 자연 호출, compact forensic payload, `baseline_v1` 호출은 exact_v2 Control/Baseline primary cohort로 사용하지 않는다.

## 1. PREMARKET promotion 재검증

### 1.1 시작 gate

- 검증 실행은 `2026-07-28 08:20~08:40 KST`에만 한다. 창 밖에서는 artifact와 기존 계측을 읽기만 하고 promotion transaction을 실행하지 않는다.
- 코드 변경이 남아 있으면 `$korstockscan-review-gate`의 `review -> 결함 보완 -> 재리뷰 -> targeted validation`을 finding 0건까지 닫는다.
- 관련 targeted tests, compile, `git diff --check`, runtime env/rollback mapping, first-observation hook가 모두 PASS여야 한다.
- 현재 프로세스가 검증 대상 코드를 실제로 로드하지 않았거나 source가 dirty면 `blocked_review_or_env`로 닫는다. `2026-07-28 07:55` PID `712183`은 이 조건으로 이미 차단됐다. 이 작업지시만으로 bot restart를 수행하지 않는다.

### 1.2 검증 표본과 호출 경계

- 필수 endpoint는 다음 네 개다.
  - `analyze_target`
  - `entry_price`
  - `holding_score`
  - `holding_flow`
- 각 endpoint의 PREMARKET 검증 호출은 기존 validation-only probe 경로에서, 해당 symbol/venue/session에 자연 캡처된 fresh exact source/model/call-input 후보만 사용한다.
- 이 문서가 승인한 PREMARKET validation-only 실제 호출은 허용한다. 그 밖의 인위적인 baseline 표본 호출, 합성 holding 문맥, 다른 venue/session 값 보간, promotion 이전 compact payload 재구성은 금지한다.
- 검증 호출은 promotion 증거일 뿐 Control/Baseline 자연호출 cohort에는 넣지 않는다.
- natural candidate가 없거나 freshness window를 넘었으면 사후 복원하지 않고 해당 endpoint 검증을 실패 처리한다.

### 1.3 endpoint별 필수 계약

각 endpoint와 symbol/venue/session 표본에서 아래를 모두 확인한다.

- `request_id`와 request/prompt/payload/response hash
- `provider != none`
- provider, model/model-id, transport, response-id, latency, token usage, failback chain
- effective venue/session과 broker/market-data route 정합성
- entry/entry-price의 `context_schema=entry_candle_context_v1`
- holding/holding-flow의 `context_schema=holding_decision_context_v1`
- `input_bundle_version=scalping_multi_timeframe_context_v1`
- raw 1분봉 배열과 completed bar 1개 이상
- 세션 시작에 정렬된 completed 3/5/15분 OHLCV
- completed 1분봉 기반 session VWAP
- 5/15분 opening range, 전일 고가·저가·종가, 시장·업종 상대 문맥
- forming bar 별도 표시와 모든 completed-bar 파생 계산에서의 배제
- source-quality fresh/same-basis/conflict-free
- payload/API 내부 변환 일치와 비교 가능한 외부 필드 `MISMATCH=0`
- 민감정보 제거 exact payload 저장과 response provenance 연결

외부 source에서 제공하지 않거나 기준이 다른 필드는 억지 비교하지 않고 `NOT_COMPARABLE` 또는 `SOURCE_UNAVAILABLE`과 사유를 기록한다. 종가경매, KRX+NXT 통합값, 지연 시세는 일반 KRX 완성분봉과 섞지 않는다.

### 1.4 산출물 생성·검증 순서

아래 순서를 바꾸지 않는다. 앞 단계가 FAIL이면 뒤의 runtime 적용 또는 판단품질 산출물을 억지로 생성하지 않는다.

1. `ai_input_external_validation_2026-07-28` source/payload/external match
2. `ai_multi_timeframe_context_review_2026-07-28` review finding와 validation summary
3. `ai_multi_timeframe_context_promotion_2026-07-28` binary promotion decision
4. PASS인 경우에만 target-date runtime env apply/read-back과 `ai_multi_timeframe_context_first_observation_2026-07-28`
5. promotion 이후 자연 `ai_decision_requests_2026-07-28`과 `ai_decision_trace_2026-07-28`
6. horizon이 성숙한 뒤 `ai_decision_outcome_labels_2026-07-28`
7. stage·venue sample floor와 60분 primary maturity를 통과한 뒤 `ai_decision_quality_baseline_2026-07-28`

각 단계는 source hash/generation timestamp와 직전 owner artifact를 기록한다. 최종 review finding 0건 전에는 비싼 report 재생성, runtime env apply, first-observation promotion hook 실행을 하지 않는다.

## 2. Promotion 판정과 적용

### 2.1 PASS

모든 필수 조건을 충족할 때만 `promoted_all_market_sessions_full`을 기록한다.

- PASS artifact를 기록한 같은 promotion transaction에서 다음 범위를 원자적으로 적용한다.
  - 전체 스캘핑 종목
  - `PREMARKET_KRX_LIKE`
  - `KRX_REGULAR`
  - `NXT_REGULAR_OVERLAP`
  - `NXT_AFTERMARKET`
  - 네 필수 endpoint와 기존 계약상 multi-timeframe context가 적용되는 `realtime_report`, `overnight`
- `input_preflight_mode=exact_v2`, required preflight, active date, entry/holding master와 venue/session/stage context env를 한 transaction에서 활성화한다.
- canary, 일부 session, 일부 symbol/cohort, 일부 endpoint, 호출비율 제한을 두지 않는다.
- activation 직후 first-observation hook와 runtime env read-back으로 full-market mapping을 확인한다.

### 2.2 FAIL

하나라도 실패하면 다음 중 하나의 단일 primary decision과 세부 finding을 artifact에 기록한다.

- `blocked_source_quality`
- `blocked_provider_or_schema`
- `blocked_route_isolation`
- `blocked_runtime_hook_missing`
- `blocked_review_or_env`

FAIL이면 `runtime_activation=false`를 유지한다. partial rollout, canary, session/endpoint 제한 승격, payload 사후 복원은 금지한다. 검증 창이 오기 전 상태는 실패로 쓰지 않고 `not_yet_due`로 유지한다.

### 2.3 불변 경계와 rollback

- provider/model/route, prompt, threshold, 주문가·수량·cap, broker/account/order/cooldown guard, hard/protect/emergency safety를 변경하지 않는다.
- 이 작업지시만으로 bot restart를 실행하지 않는다.
- PASS 뒤 cross-venue 오염, forming bar 혼입, source-quality conflict, provider none, semantic/schema reject, exact hash 누락, runtime hook 예외 또는 기존 safety 우선순위 변화가 확인되면 신규 context surfaces만 기존 rollback mapping으로 원자적으로 비활성화한다.

### 2.4 Operator-directed full promotion override (`2026-07-29`)

- 사용자가 명시적으로 validation gate 우회를 지시한 경우에만 `operator-directed-apply`를 사용할 수 있다. 이 경로는 `operator_directed_full_promotion` mode, dated authorization ID, operator reason, 그리고 원래 validation/review finding 전체를 promotion artifact에 보존한다. 이를 일반 validation PASS로 표시하지 않는다.
- override는 runtime manifest/verify와 PREMARKET transaction window를 계속 요구하며, 전체 symbol·session·endpoint에만 적용된다. partial rollout은 허용하지 않는다.
- runtime preflight artifact readiness만 override marker로 대체한다. 각 호출의 fresh source, venue/session consistency, completed-bar, source-quality, broker/hard-safety guard는 그대로 fail-closed다.
- committed full-market promotion marker는 명시적 committed rollback 전까지 다음 거래일에도 승격 authority를 유지한다. 원 marker·runtime manifest·env의 authority/path/target-date/hash는 승격일 원본 기준으로 매번 검증하고, launcher는 검증 성공 시에만 당일 날짜값으로 전체 Exact V2 runtime env overlay를 재생성한다. marker만으로 baseline PID를 활성화하지 않으며 적용 PID가 당일 전체 Exact V2 runtime env를 read-back한 경우에만 활성화한다. malformed/tampered/future/rollback marker는 fail-closed이고, 적용 PID 반영은 별도 승인된 graceful restart와 runtime env read-back이 필요하다.

## 3. Promotion 후 natural Exact V2 표본 수집

- PASS timestamp 이후 자연 발생한 `analyze_target`, `entry_price`, `holding_score`, `holding_flow` 호출만 primary 수집 대상으로 삼는다.
- 다음 조건을 모두 충족한 row만 eligible이다.
  - `canonical_context_capture_status=exact_completed_bars_captured`
  - `input_preflight_mode=exact_v2`
  - `input_preflight_allowed=true`
  - `provider != none`
  - promotion timestamp 이후 호출
  - exact snapshot ID와 request/prompt/payload/response hash 보유
  - canonical context schema와 `scalping_multi_timeframe_context_v1` 보유
  - raw 1분봉과 completed bar 1개 이상
  - forming bar 분리
  - venue/session consistent
  - source-quality blocker 없음
- 다음 row는 삭제하지 않고 exclusion reason과 함께 별도 보존한다.
  - `canonical_context_missing`
  - `canonical_completed_bars_missing`
  - compact forensic payload
  - `baseline_v1` 또는 preflight off
  - provider none
  - source-quality blocker
  - venue/session conflict
  - promotion 이전 호출
  - PREMARKET validation-only 호출
- 자연 발생하지 않은 endpoint/session은 부분 적용 실패로 판정하지 않고 `pending_natural_endpoints` 또는 `pending_natural_sessions`로 남긴다. 다만 해당 stage의 Control baseline은 표본이 생기기 전까지 ready로 닫지 않는다.
- exclusion 처리는 실제 AI 호출, 주문 판단, 주문 제출 흐름을 차단하거나 변경하지 않아야 한다.

## 4. Outcome maturity 및 Control baseline

- eligible row별 동일 venue/session 가격 경로로 1/3/5/10/20/30/60분 MFE, MAE, target/adverse first-hit를 연결한다.
- realized PnL과 counterfactual outcome은 별도 필드·별도 집계로 유지하고 합산하지 않는다.
- entry/entry-price/post-probe 10분, scale-in 20분, holding/exit 30분, overnight 60분 stage horizon은 진단 지표로 유지한다.
- 전체 Control baseline readiness의 primary gate는 사용자가 지정한 60분 horizon 성숙이다. 60분 미성숙 row는 partial horizon 분석에는 남길 수 있지만 primary Control baseline에는 넣지 않는다.
- stage·venue별 오류 taxonomy를 생성한다.
  - `false_drop`
  - `false_wait`
  - `false_buy`
  - `bad_scale_support`
  - `bad_exit_defer`
  - `early_exit_support`
  - `unsupported_confidence`
- source-quality-adjusted EV와 순이익을 primary 판단축으로 두며 AI 호출 성공률이나 parse 성공률만으로 판단품질 개선을 선언하지 않는다.
- stage·venue별 producer 계약의 sample floor와 60분 maturity floor를 모두 충족하면 `control_error_baseline_ready`로 닫는다.
- 하나라도 미달하면 `sample_floor_keep_collecting` 또는 `partial_horizons_keep_maturing`으로 명확히 종료하고 자연표본 수집을 계속한다.

## 5. Paired replay 진입 조건

- `control_error_baseline_ready` 전에는 Prompt V2 Candidate 호출, model/provider 변경, runtime 승격을 수행하지 않는다.
- Control과 Candidate는 동일한 eligible exact_v2 payload만 사용한다.
- Candidate는 offline replay 전용으로 다음을 유지한다.
  - `runtime_effect=false`
  - `allowed_runtime_apply=false`
  - `actual_order_submitted=false`
  - `broker_order_forbidden=true`
- provider/model/threshold/order/price/quantity/bot 설정은 변경하지 않는다.
- 유리한 사례만 골라내지 않고 같은 stage·venue의 eligible cohort 전체를 paired 비교한다.

## 완료 기준

- PREMARKET promotion 결과가 `promoted_all_market_sessions_full` 또는 명시적 FAIL decision과 finding으로 artifact에 기록된다.
- PASS이면 full-market env mapping과 first-observation hook가 read-back으로 확인된다.
- PASS 이후 entry, entry-price, holding-score, holding-flow 자연 exact_v2 표본의 확보 상태가 endpoint별로 기록된다.
- canonical context/bundle/completed-bar 결손 row의 primary cohort 유입이 0건이다.
- eligible primary cohort의 `provider=none`이 0건이다.
- outcome maturity와 venue/session 정합성이 통과한다.
- Control baseline이 `control_error_baseline_ready`이거나, `sample_floor_keep_collecting`/`partial_horizons_keep_maturing` 사유가 stage·venue별로 명확히 기록된다.
- 구현 변경이 있으면 `implementation -> review -> 결함 보완 -> 재리뷰 -> targeted tests -> compile -> git diff --check`를 finding 0건으로 닫는다.

## 최종 보고 형식

1. 판정: promotion decision, runtime activation, baseline readiness
2. 근거: endpoint별 exact/provenance/source-quality/external-match 및 자연표본 수
3. 제외 증거: exclusion reason별 수와 primary cohort 유입 0건 확인
4. 다음 액션: first observation, sample maturity, paired replay 진입 또는 계속 수집

## 금지 사항

- PREMARKET PASS 전 runtime activation, context 강제 활성화, partial promotion을 수행하지 않는다.
- exact_v1, compact, legacy, promotion 이전 payload를 exact_v2 primary 표본으로 사후 승격하지 않는다.
- 검증용 호출을 자연 Control/Baseline 표본으로 사용하지 않는다.
- 인위적인 baseline AI 호출, 합성 holding 문맥, 사후 payload 재구성을 수행하지 않는다.
- 주문, 가격, 수량, threshold, provider/model/route, hard safety, broker guard, bot 상태를 변경하지 않는다.
