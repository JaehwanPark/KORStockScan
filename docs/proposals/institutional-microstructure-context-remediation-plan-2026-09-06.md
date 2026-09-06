# Institutional / Microstructure context 결함 보완 구현계획

- 작성: `2026-09-06 KST`
- 상태: `implemented_runtime_not_observed_yet` (검증·범위 밖 회귀는 아래 §9)
- 근거: [최종 재리뷰 R1~R5](../audit-reports/2026-09-06-institutional-microstructure-context-final-review.md#6-목적자동화조건-달성-가능성-재리뷰)
- 실행 owner: [2026-09-07 체크리스트](../checklists/2026-09-07-stage2-todo-checklist.md)의 `ContextObjectiveRepairReview0907`; 자연 실행 확인은 `ContextDeliveryNaturalEvidence0907`.
- 원칙: Plan Rebase §1~§8의 현재 owner override와 clean baseline `2026-06-05 KST`를 따른다. §1~8은 승인된 설계이고 §9는 구현 기록이다. 코드 검증과 실제 PID 소비·수익 개선은 구분한다.

## 1. 결정과 완료 목표

Institutional 전용 aggregate의 폐기는 유지한다. Microstructure는 기존 AI/holding의 입력 품질과 기회 손실 원인을 정확히 설명하는 진단 기능으로 완성한다. 기대효과는 잘못된 favorable 판정·중복 소비 집계·허위 경제성 표본을 제거하고, 실제 결손을 기존 개선 담당 경로에 자동으로 전달하는 것이다.

다음 네 가지를 구현 완료 기준으로 삼는다.

1. 동일 입력은 공통 freshness 기준으로 같은 판정을 받고, 시간 결손은 favorable 증거가 되지 않는다.
2. 계산·payload 포함·provider 요청/응답·내부 소비·캐시 재사용을 실제 관측한 범위에서 구분한다.
3. 유효 결과가 있는 동일 시점의 기회만 경제성에 포함하며, source-only 진단과 적용효과를 혼합하지 않는다.
4. 진단 결손은 기존 workorder로 자동 전달되고, 의미 없는 PREOPEN 후보 대기와 신규 family 제안은 생성되지 않는다.

신규 튜닝축·별도 cron·독립 승인 체인·새 provider 호출은 추가하지 않는다. Institutional 재활성화, ADM/LDM 복구, 실주문/수량/cap/손절 기준 변경은 계획에 포함하지 않는다. Microstructure의 코드·계측 보완은 통상 코드 배포/정상 기동으로 반영한다. 이 진단에 20건·양의 EV를 충족해야 코드를 사용할 수 있다는 조건을 붙이지 않는다.

현재 구현에서도 20건·양의 EV는 누적 report의 후보 검토 표시 조건이며 코드 기동/feature 계산을 막는 gate는 아니다. 이번 계획에서 제거하는 것은 이 진단을 별도 runtime 승격 대상으로 보이게 하는 상태·후속 요구와 신규 family 제안이다.

## 2. 결함별 처분과 구현 순서

| 단계 | 대상 결함 | 처분 | 완료 산출물 |
| --- | --- | --- | --- |
| A | R1 신선도 | 공통 정규화·결손 판정 보완 | 같은 threshold/age 판정과 version이 기록된 feature packet |
| B | R2 전송·소비·logger | delivery v3와 호출 단위 대사 구현 | cache/실패/내부 소비를 구분하는 보존 가능한 receipt |
| C | R3 EV 표본·결합 | finite-return 집계·attempt 결과 연결·version 분리 | 유효 표본에 근거한 diagnostic EV와 제외 사유 |
| D | R4 후보 경로, R5 coverage/handoff | 불필요 후보 제거·분모 수정·workorder 검증 | 자동 진단→기존 owner 개선 작업→다음 실행 확인 |

각 단계는 구현→코드리뷰→발견 결함 수정→관련 회귀→재리뷰 순서로 닫는다. A~D 구현은 다음 영업일 정상 기동 전 완료를 목표로 하되, 시장 표본의 발생이나 양의 수익률은 구현 완료 조건이 아니다.

## 3. A — 신선도 계산을 하나로 통일

수정 위치: `src/engine/scalping/microstructure_reaction_context.py`의 precompute/build와 `src/engine/scalping_feature_packet.py`의 extract/audit. 공통 정규화 함수는 의존 방향상 하위인 기존 reaction 모듈에 두고 양쪽이 사용한다. `src/engine` root에 새 모듈을 만들지 않는다.

### A1. 설정값 정규화

| 입력 | 적용값/처리 |
| --- | --- |
| 유한한 양수 | 기존 정수 ms 규칙과 최소 1ms 유지 |
| 미설정·None·빈 문자열·0 | 현재 canonical 기본값 3000ms |
| 유한한 음수 | 기존 canonical 방어 동작인 1ms clamp 유지, invalid-setting provenance 표시 |
| 숫자 변환 실패·bool·NaN·Infinity | 3000ms로 안전하게 파싱 종료하고 invalid-setting provenance 표시; 해당 reaction은 유효 freshness 증거로 사용하지 않음 |

packet과 reaction은 정규화 결과를 재사용한다. `quote_stale_threshold_ms`와 `microstructure_reaction_quote_stale_threshold_ms`를 같은 receipt에 보존한다. 1200ms 상수나 별도 reaction 설정을 다시 만들지 않는다.

### A2. 시간 품질 판정

- 실제 quote/tick age를 각각 검증한다. None/빈 값/비유한 값/복구 불가능한 음수·미래시각은 `source_quality_missing` 또는 `source_quality_partial`과 구체적 reason으로 반환한다.
- 미래 timestamp가 계산 초기에 `max(0, age)`로 정규화돼 사라지는 경로까지 확인한다. 보정 가능한 timestamp는 기존 canonical 정규화/허용 오차와 provenance를 재사용하며 임의의 새 오차 허용치를 추가하지 않는다.
- 필요한 age가 모두 유효한 경우에만 기존 quote threshold와 tick 5000ms를 적용한다. 부족한 tick 개수·trusted pressure 조건은 현재 계약을 유지한다.
- 정상 입력의 reaction 수식과 점수 경계는 유지한다. source-quality 수정이 필요한 사례만 neutral/unusable로 바뀌어야 한다. 기존 holding은 품질 결과를 자신의 기존 규칙으로 처리하며, 이 수정이 신규 강제 청산/전역 entry 차단으로 번지지 않게 검사한다.
- freshness 의미가 바뀌므로 `CONTEXT_VERSION`을 v2로 올린다. context hash는 계산 입력·threshold·feature version만 표현하고 전송 여부/cache 상태를 섞지 않는다.

수용시험: 200ms/0설정에서 양쪽 3000ms; 명시 1200ms 일치; 음수 clamp 일치; quote/tick 시간 결손의 favorable 0건; 임계값 직전/동일/직후 판정; 정상 입력 수식 동등성; holding/broker 기존 guard 우회 없음.

## 4. B — 실제 관측에 근거한 delivery v3

수정 위치: `scalping_feature_packet.py`, `ai_engine_openai.py`, `sniper_state_handlers.py`, `src/utils/pipeline_event_logger.py`, 필요 시 기존 `scalping/ai_decision_trace.py`의 필드 projection. retired ADM parser는 현재 실행 owner로 사용하지 않는다.

### B1. 필드 의미

아래 이름은 `microstructure_reaction_` prefix를 사용한다. 기존 필드는 호환성을 검토하되 v2의 의미를 덮어쓰지 않고 telemetry version을 v3로 올린다.

| 필드/상태 | 의미 |
| --- | --- |
| `context_computed` | 이 evaluation에서 feature 계산을 실제 수행함 |
| `context_payload_included` | 최종 provider 입력의 구조화된 feature key/value가 존재함 |
| `provider_delivery_status` | `not_attempted`, `attempted_unconfirmed`, `response_received`; 모르는 전송 결과를 성공으로 추정하지 않음 |
| `context_sent` | payload 포함과 해당 요청의 응답으로 전달이 확인될 때만 true; timeout 등 확인 불가는 null과 위 상태로 표현 |
| `context_consumed` / `context_consumer` | 코드가 실제 읽은 내부 소비만 기록. 예: holding source-quality/preflight. provider의 내부 판단 사용 여부는 추정하지 않음 |
| `context_reused` | 현재 결과가 이전 계산/응답의 cache 또는 feature reuse임 |
| receipt identity | 현재 evaluation과 원본 context/parent request의 연결. 기존 snapshot/trace/request/attempt ID를 우선 재사용 |

`context_sent=false`는 소비가 없다는 뜻이 아니며, 내부 품질 소비가 있으면 `consumed=true`일 수 있다. provider 응답은 payload 전달 증거로만 사용하고 순이익 기여나 모델의 feature 활용 증거로 격상하지 않는다.

### B2. 생성 위치와 전파

1. feature builder는 computed receipt만 생성한다. 최종 입력 구성 후 구조화 JSON의 실제 key 경로로 payload 포함 여부를 결정한다. 설명 문자열의 substring 검색은 제거한다. legacy text는 formatter가 명시한 field manifest가 있을 때만 판정하고, 없으면 unverifiable로 남긴다.
2. `_call_openai_safe`의 기존 HTTP/WS 호출·응답 metadata를 사용해 전송 상태를 확정한다. request ID 생성 또는 로컬 fallback 반환만으로 전송 성공을 인정하지 않는다. 성공/timeout/parse error/WS→HTTP fallback을 해당 논리 요청에 연결한다. provider route·retry 횟수·timeout 값은 변경하지 않는다.
3. holding quality 함수와 upstream preflight가 context를 실제 읽은 지점에서 내부 소비를 기록한다. provider가 생략되는 경로도 해당 내부 receipt를 보존한다.
4. cache hit은 현재 computed/sent를 새 발생으로 기록하지 않는다. 이전 context identity와 parent trace를 남기고 reuse를 집계한다. 캐시에서 얻은 feature를 현재 내부 코드가 다시 읽었다면 그 내부 소비만 현재 receipt로 남긴다.
5. `_build_ai_ops_log_fields`, `_build_tick_source_quality_log_fields`, preflight 결과와 event logger whitelist를 함께 보완한다. nullable 전송 상태를 `bool()`로 강제해 unknown을 false로 잃지 않는다.
6. report는 같은 논리 evaluation을 여러 stage가 복제해도 새 계산/호출로 세지 않는다. 유효 identity가 없으면 행 진단으로 남기고 unique 호출 집계에서 제외한다. 필요할 때 한 번만 만든 source-only evaluation ID를 끝까지 전달하며, 로그마다 새 ID를 만들지 않는다.

수용시험: 이름만 든 설명 문자열, 의도적 omission, preflight-only, 정상 응답, 로컬 fallback, timeout, parse 실패, 캐시, WS fallback을 각각 대사한다. 같은 receipt를 세 stage에 복제해도 computed/provider logical call은 1건이다. logger→report까지 threshold·identity·nullable 상태가 보존돼야 한다.

## 5. C — 유효 경제성 표본과 같은 attempt의 결과 연결

수정 위치: reaction report의 `_unique_entry_opportunities`, `_attach_time_exact_outcomes`, `_daily_opportunity_rollup`, cumulative loader와 기존 `src/engine/sniper_missed_entry_counterfactual.py`의 attempt/결과 투영 부분.

### C1. 모집단과 유효 표본

- `feature_diagnostic`: clean baseline 이후 당시 계산 version·품질·시점이 확인되는 source-only feature의 미래 결과 진단. 의도적 provider omission 때문에 제외하지 않는다.
- `delivery_observation`: v3 identity와 실제 전달/내부 소비를 확인하는 운영 자료. 손익 표본과 별개다.
- `applied_effect`: 기존 전략 owner의 동일 입력 비교/실제 종료 귀속이 있는 경우만 표시한다. 현재 직접 적용 비교가 없으면 `not_evaluated`로 닫는다. 새 독립 replay 엔진이나 새 진입 정책을 이 report에 만들지 않는다.
- 기존 v1/v2 telemetry 자료는 historical diagnostic에 남긴다. version을 추정해서 v3로 변환하지 않는다. 미래 version 변화도 compatible 여부가 명시된 parent만 함께 집계하고 서로 다른 venue·stage의 효과를 다른 runtime owner에 적용하지 않는다.
- EV 분모는 `exact identity/time + source-quality pass + 유한한 비용차감 return`을 모두 통과한 unique opportunity 수다. pass count와 finite-return count를 별도로 보고한다. NULL/NaN/±Infinity/pending/결과 결손은 0으로 채우지 않는다.
- 기존 20건은 `diagnostic_sample_floor_met`로 이름과 역할을 바꾼다. 1~19건도 값·표본수를 보여주되 early evidence다. 20건이 진단 실행·코드 보완·workorder 생성·runtime 로딩을 막지 않는다. pass20/finite1이면 진단 floor는 미달이다.
- 비용은 원천의 기존 계산과 차감 여부/provenance를 보존한다. 이미 차감한 비용을 다시 빼거나 슬리피지를 새 고정 패널티로 추가하지 않는다. 20분 미래 수익률은 기존 정책의 실제 청산 수익률로 부르지 않는다.

### C2. cycle 대표시각과 micro attempt 시각의 불일치 해소

1. 새 event에서는 현재 평가 identity, feature version/hash, reference time/price, venue/session을 보존한다. 종목+record+120초 cluster만을 현재 version의 확정 identity로 사용하지 않는다.
2. 기존 missed-entry producer의 `all_buy_evaluations`/`full_rows`/attempt source contract가 가진 결과 중 동일 anchor가 증명되는 자료를 우선 재사용한다. raw field projection도 함께 확인한다.
3. cycle 대표 결과만으로 연결할 수 없는 경우 기존 missed-entry report 안에 `microstructure_attempt_outcomes` 절을 추가한다. 동일 producer 실행에서 읽은 event/동일 venue 가격 시계열과 기존 horizon 계산을 재사용하여 micro anchor 시각부터의 결과를 만든다. 기존 cycle ledger의 의미는 유지한다. 신규 CLI·cron·broker/provider 호출은 만들지 않는다.
4. 정확한 원천 identity로 먼저 join한다. legacy fallback은 동일 종목/record/venue와 기존 5초 허용차 안에서 유일하게 대응할 때만 허용한다. record 재사용·venue conflict·복수 후보는 ambiguous로 제외한다. 단순히 허용차를 늘리거나 관측 anchor를 미래 결과에 맞춰 옮기지 않는다.
5. 원천에 같은 anchor의 가격 경로가 없으면 `unrecoverable_historical_gap`; 아직 horizon이 끝나지 않았으면 `pending_outcome`이다. 구조적 producer 결손은 구체적 workorder로 전달하고 과거 복원 불가능 자료는 제외 사유와 함께 종결한다.
6. 생산 순서를 기존 운영 경로에서 대조한다. micro가 먼저 실행되는 경우 기존 wrapper 안에서 원천 materialization 뒤로 옮긴다. forward/재귀 의존성과 두 번째 전체 raw scan을 만들지 않는다. 필요 없는 전 history 재생성을 요구하지 않는다.

### C3. 산출물 migration과 재평가

- report schema는 5, daily rollup schema는 2로 변경한다. rollup signature에는 원천 signature와 feature/quality/metric/rollup version을 포함한다. 오래된 aggregate를 현재 규칙으로 재해석하지 않는다.
- 현재 window에서 신선하고 호환되는 날짜만 집계한다. legacy rollup은 별도 historical summary로 표시한다. raw가 보존된 필요한 날짜만 선택적으로 재생성하며 archive 삭제·전체 history 강제 backfill은 하지 않는다.
- 과거 raw를 새 코드로 다시 계산할 수 있어도 `offline_recomputed` 자료다. 당시 실제 version/전송/소비로 소급 표시하지 않는다. 당시 입력을 복원할 수 없는 항목은 historical gap으로 종결한다.
- 재평가는 새로운 mature outcome, 복구된 source, 변경된 계산 version이 있을 때 수행한다. 같은 input signature로 동일 개선 작업을 반복 생성하지 않는다.
- 표본 도달 전망은 동종 version의 최근 운영일별 신규 finite outcome 수·결합률로 참고 계산한다. 0건이면 ETA unknown이지 자동 실패가 아니다. 추가 종목수 floor·연속 양수일·별도 +1% 허들은 도입하지 않는다.

수용시험: pass20/finite1, 중복 event, NaN/Infinity, version 혼합, 같은 record의 다른 attempt/venue, 5초 경계, source 결손/pending을 대사한다. 같은 cycle의 두 micro anchor는 각자 시각의 결과와 연결되며 기존 cycle summary는 유지돼야 한다.

## 6. D — 불필요한 후보 경로 제거와 자동 진단 연결

### D1. 제거를 확정할 경로

- `microstructure_signed_tape_runtime_candidate`와 `order_microstructure_signed_tape_runtime_candidate_review`의 신규 생성 분기를 제거한다. 과거 workorder가 current builder로 재유입될 때는 archive/superseded로 명시 종결한다. 다른 family의 정상 후보는 필터링하지 않는다.
- micro report의 `bounded_candidate_review_only`, `candidate_review_required`, `required_runtime_reflection_actions`의 PREOPEN 요구를 없앤다. 새 schema는 `analysis_status`와 `runtime_application=not_applicable_diagnostic`를 사용한다. 내부 소비 여부는 B의 receipt로 별도 표시한다.
- 기존 reader가 필드를 요구하면 한시적 compatibility alias로만 제공하되 ready/promotion은 false 또는 not-applicable로 고정한다. EV/runtime/daily summary와 테스트를 같은 변경에서 갱신한다.
- Institutional producer OFF, current retired, historical artifact 복구 workorder 없음은 회귀로 고정한다.

### D2. coverage 분모와 경고

| 지표 | 분모/해석 |
| --- | --- |
| 전체 event 수 | 운영량 진단; 품질 성공률 분모로 사용하지 않음 |
| 계산 coverage | 계산이 요구된 유효 evaluation 중 computed 비율 |
| usable coverage | unique computed 중 정상 품질 비율 |
| provider delivery coverage | payload 포함·전송이 요구된 호출 중 확인된 전달 비율; unknown 별도 |
| internal consumption coverage | 내부 소비가 요구된 경로 중 실제 내부 receipt 비율 |
| outcome join coverage | 평가 가능한 feature opportunity 중 exact 결과 결합 비율; pending/결손 별도 |

적용 대상은 stage/endpoint의 실제 기존 호출 계약으로 정하고 신규 튜닝 taxonomy로 만들지 않는다. stage 목록은 생산자/소비자 검사에 필요한 최소 범위로 선언하고 알 수 없는 경로는 applicability unknown으로 집계한다. 분모 0은 N/A이며 성공률 0/100으로 치환하지 않는다.

전체 event 기준 고정 5% 경고는 제거한다. missing timestamp·상충 receipt·필수 전달 누락 같은 계약 위반은 1건부터 드러내되, 같은 원인은 하나의 개선 작업으로 묶는다. 정상적인 일시 stale·짧은 window·자연 표본 0은 운영 진단이며 반복 workorder를 만들지 않는다. 의도적으로 derived entry payload를 생략한 호출은 delivery 실패가 아니다.

### D3. 기존 workorder와 검증기 연결

- `_microstructure_code_improvement_orders`에서 R1/R2/R3의 실제 계약 결손에 한해 `instrumentation_order`를 만든다. 실행 담당은 기존 `runtime_instrumentation`/source-quality이며, main AI 품질 비교가 필요한 자료는 해당 기존 담당 경로에 source bundle로 연결한다.
- 각 작업은 cause, owner, source date/signature, unique affected count, 대표 receipt, touched files, 수용시험, 종료 조건을 가진다. 동일 cause/version/scope의 반복을 deduplicate하고 evidence만 갱신한다.
- `build_code_improvement_workorder`→daily/EV/runtime summary→`verify_threshold_cycle_postclose_chain`에서 같은 order가 전달됐는지 검사한다. 실제 계약 위반을 조용히 PASS하지 않으며 미전달은 이 진단 분기의 `automation_handoff_gap`으로 기록한다.
- micro optional report의 실패는 diagnostic warning/source workorder로 격리한다. 보고서가 없는 날이나 favorable0을 이유로 정상 다른 전략의 PREOPEN/장후 작업을 중단하지 않는다. 전체 체인 hard gate는 기존 안전/원천 계약의 범위를 따른다.
- 원천 수집·report·workorder 발행/갱신·handoff 검증은 기존 scheduled chain에서 자동 실행한다. 자동 code mutation이나 실주문 정책 변경까지 완료됐다고 표시하지 않는다.

새/변경 metric은 `metric_role`, `decision_authority`, `window_policy`, `sample_floor`, `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 선언한다. 경제성의 주 지표는 `source_quality_adjusted_ev_pct`; 운영 coverage는 손익이나 runtime 승인 지표로 사용하지 않는다.

수용시험: REST source1건 신규 family0; 미평가 scanner 행 10배에도 대상 요청 품질 비율 불변; intended omission 작업0; 동일 결손 stage 복제에도 workorder1; workorder 유실 검출; optional report 실패 격리; 정상 다른 owner 후보 보존.

## 7. 리뷰·검증과 적용 순서

| 검증 단위 | 우선 테스트 |
| --- | --- |
| A | `test_microstructure_reaction_context.py`, `test_scalping_feature_packet.py` |
| B | 위 테스트 + `test_ai_engine_openai_v2_audit_fields.py`, `test_ai_engine_cache.py`, `test_pipeline_event_logger.py`, `test_state_handler_fast_signatures.py`; 필요한 trace/transport fixture |
| C | `test_microstructure_reaction_context_report.py`, `test_missed_entry_counterfactual.py`, 원천 projection/source-quality 회귀 |
| D | `test_build_code_improvement_workorder.py`, `test_daily_threshold_cycle_report.py`, `test_threshold_cycle_ev_report.py`, `test_runtime_approval_summary.py`, `test_verify_threshold_cycle_postclose_chain.py`, `test_threshold_cycle_wrappers.py`, `test_adm_ldm_retirement.py` |

- 각 반례를 변경 전에 재현하고 해당 경계가 수정 후 차단되는지 확인한다. 기존 expected 값을 새 결과로 바꾸는 것만으로 끝내지 않는다. 정상 control input과 연결된 producer/consumer를 함께 검사한다.
- `.venv`를 사용해 targeted pytest, compile, Black check, `git diff --check`를 수행한다. wrapper 수정 시 `bash -n`과 순서/실패 격리 회귀를 추가한다. 문서/checklist parser는 기존 `--print-backlog-only --limit 500` 경로로 검증한다.
- 운영문서는 구현으로 실제 바뀌는 automation 계약과 함께 갱신한다. baseline 문서는 별도 사용자 지시 범위를 확인하며 이번 계획 작성에서는 수정하지 않는다.
- A~D 통합 리뷰가 닫힌 뒤 필요한 현재 날짜 report만 선택적으로 재생성한다. source-only report PASS와 실제 PID 소비를 구분한다. 기존 예정 PREOPEN/정상 기동에서 loaded code version→당일 v3 receipt→장후 집계→workorder 대사를 확인한다.
- 시장 운영일에 해당 경로가 실행되지 않으면 `not_observed_yet`로 남긴다. 정상 소비 증거를 만들기 위한 강제 주문이나 추가 AI 호출을 하지 않는다. 다음 자연 발생에서 다시 확인한다.
- rollback은 검증된 변경분 단위로 수행한다. 새 포맷을 읽지 못하면 해당 diagnostic을 명시적 blocked/legacy 상태로 내리고 다른 전략 소스를 보존한다. Institutional/ADM/LDM을 다시 켜거나 unknown timestamp를 favorable로 되돌리는 복귀는 허용하지 않는다.

## 8. 최종 목적 부합성 판정

| 질문 | 계획의 답 |
| --- | --- |
| 작은 순수익을 자주 확보하는 목적에 도움이 되는가? | 잘못된 입력·기회 집계에 따른 판단을 제거하고 기존 전략 개선에 정확한 증거를 제공한다. 실제 수익 증가 판정은 기존 owner의 비용차감 결과가 담당한다. |
| 런타임 적용이 자동인가? | 보완된 계산·내부 소비·계측은 정상 코드 기동 후 자동이다. 진단 report/workorder도 기존 장후 경로에서 자동이다. 독립 micro threshold/PREOPEN 승격은 적용 대상이 아니다. |
| 조건이 너무 높은가? | code/계측 적용의 20건·양의 EV 대기는 제거한다. 20건은 finite diagnostic 표본 해석에만 유지하고, 추가 기간/수익/종목수 floor는 만들지 않는다. |
| 언제 작업이 끝나는가? | R1~R5 반례·회귀와 producer→consumer 계약이 통과하면 구현 종결, 다음 자연 PID receipt가 확인되면 운영 확인 종결. 수익 개선 미확인을 무한 구현/승인 대기로 바꾸지 않는다. |

계획 단계 기록: R1~R5의 처분·구현 위치·수용시험·운영 확인 owner를 정의했다. 이후 구현 결과는 §9 및 연결된 최종 리뷰를 따른다.

## 9. 구현 결과

- A: 공통 quote 설정 정규화, 결손·비유한·미래 age 배제, feature v2 및 순수 feature hash를 구현했다. 정상 입력 수식과 기존 안전 guard는 유지한다.
- B: delivery v3, 구조화된 실제 feature 포함 검사, HTTP/WS 응답 및 실패 구분, 내부 소비, cache identity/reuse, nullable 값의 logger→report/trace 보존을 구현했다. HTTP 최소 입력 재시도는 마지막 실제 입력 기준으로 포함 여부를 확인한다.
- C: 기존 missed-entry producer의 이미 읽은 event/동일 venue 가격 자료로 `microstructure_attempt_outcomes`를 추가했다. 기존 cycle ledger의 의미·REST 호출수는 유지한다. current feature v2와 legacy를 구분하며 report schema5/rollup schema2, finite EV 분모, pending/결손/ambiguous 배제, diagnostic sample forecast를 구현했다. full snapshot(기존 15:45) 이후 발생한 평가의 결과는 그 산출물에 없을 수 있으며 source gap으로 표시한다. 전일 전체 파일 강제 재생성이나 미래 가격 호출로 성공 표본을 만들지 않는다.
- D: 독립 signed-tape family/후보 대기와 전체 event 기준 5% 경고를 제거했다. 단순 ka10003 관측만으로 개선 작업을 반복 생성하는 경로도 제거했다. v3 unique coverage와 계약 결손 workorder, daily/EV/runtime order ID 전달, optional 분기 검증을 연결했다.
- 최종 분모 보완: cache 재사용은 새 계산 요구에서 제외하고, 필수 holding payload가 빠진 실제 시도는 provider delivery 분모에 남긴다. 분모 0은 N/A이며 모순된 receipt는 확인된 전달로 인정하지 않는다.
- Institutional/ADM/LDM 폐기는 유지한다. 전략 threshold, 주문/수량/provider/cap/안전 기준·cron·bot 상태를 변경하지 않았다. 실제 정상 기동/장후 확인은 `ContextDeliveryNaturalEvidence0907`에 남긴다.
- 검증 수치와 중간 wrapper 회귀의 원인·계약 정합화는 [최종 리뷰 §7](../audit-reports/2026-09-06-institutional-microstructure-context-final-review.md#7-ad-구현-후-재리뷰)에 기록한다. source-only code PASS를 실수익 개선으로 표현하지 않는다.
