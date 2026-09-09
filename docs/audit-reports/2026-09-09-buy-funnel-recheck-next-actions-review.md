# #119 BUY Funnel → #23 recheck: 현재 개선작업 도출

점검일: 2026-09-09 KST. §1~§5는 최초 읽기 전용 점검 기록이며 당시 구현은 하지 않았다. 이후 사용자의 개선작업 실행 지시에 따른 구현·수정보완 및 현재 완료 경계는 §6에 기록한다. 과거 as-of와 새 자연 산출물을 혼합하지 않는다.

## 1. 판정

**우선 작업은 장후 전체 재실행이나 recheck 강제 ON이 아니라, 기존 exact ledger 위의 원인 세분화와 대응 owner 정합성 보완이다.** exact attempt 보존식과 전일 controller→strict→PREOPEN 전달은 확인된다. 다만 현금 주문가능 0과 결측의 혼합, refresh 결과의 오해 가능한 계측, AI 원모델/후처리/입력 실패 혼합, 실제 recheck 대응 범위의 과대 해석 위험이 남는다.

이 문서의 P1/P2는 수리 우선순위이며 자동 매매 권한이 아니다. 작은 비용 후 이익의 반복 확보가 목표이지만 제출 건수 증가만으로 효과를 판정하지 않는다. 정상 DROP/관찰 WAIT, 실제 주문가능 0, stale/spread/가격 충돌 guard는 우회하지 않는다.

## 2. 고정 관측과 재현

9/9 `11:25:04` BUY Funnel JSON SHA256: `28e62858ef6ac1217fa2ac67ebfd1dafcd0286f24c9404688ef93b504c6143d9`. 이후 동일 경로는 정기 producer가 갱신하므로 아래 수치는 이 as-of에 한정한다. source: `data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-09-09.json` 및 같은 날짜의 기존 `data/runtime/sentinel_event_cache/` 원천. KRX scope를 분리하고 같은 cutoff의 순수 exact builder로 재현했다. global/CONFLICT/독립 machine 분모는 합산하지 않았다.

| KRX exact terminal 원인 | 시도 수 | 해석 |
| --- | ---: | --- |
| UPSTREAM_GATE | 317 | zero-qty 69 포함; 세부 정상 차단/입력 결손은 별도 |
| LATENCY_PRE_SUBMIT | 148 | 최종 terminal 기준. raw 반복 이벤트 수와 구분 |
| ENTRY_AI_AUTHORITY_REVALIDATION | 40 | fresh WAIT 21, fresh DROP 17, stale-or-untrusted 2 |
| PRICE_REVALIDATION | 8 | 가격/입력 품질 차단. broker 미도달과 구분 |
| BROKER_RECEIPT | 0 | 제출 전 차단 때문에 미도달; broker 체결 품질 정상 증거가 아님 |
| 합계 | 513 | terminal 513 + pending 0 + submitted 0; 미분류 0 |

- Refresh가 적용된 뒤 latency pass는 **31개 exact 시도**이며 다음 차단은 WAIT 18 + DROP 12 + 입력/계약 1 = AI authority 31이다. record/native ID만으로 다시 집계하지 않고 Sentinel의 ordered event-binding을 사용했다. 앞선 11:20의 29건과 혼합하지 않는다.
- Refresh 적용 뒤에도 latency block인 시도는 **126개**다. 기록된 사유는 `spread_above_caution_below_guard_cap` 99, `spread_too_wide` 21, `ws_age_too_high` 5, age+spread 1이다. 같은 시도의 이후 진행에 따라 최종 terminal 축이 바뀔 수 있어 126을 위 terminal 148에 더하지 않는다. 이 이름만으로 spread guard가 잘못됐다고 단정하지 않는다.
- Zero-qty **69개 모두** `pre_cap_qty>0`, `binding_caps=cash_orderable_qty_cap`, cap=0, `kt00011_error=""`, minimum-one-share enabled였다. 예: 069540 09:03:28, 계산 수량166 → cap0 → 최종0. 단순 한 주 floor/전략 배분 부족이 아니다. 실제 브로커가 명시적 0을 반환했는지는 보존된 pipeline 필드만으로 확정할 수 없다.
- 전체 fresh WAIT 21건 중 원모델 DROP 14건이 retry telemetry에 기록돼 있다. 따라서 최종 WAIT 수를 원모델의 관찰 WAIT 수로 해석할 수 없다. Refresh 후 WAIT 18건 중에서도 원모델 DROP은11건이다. 후처리 자체의 정당성은 동일 trace의 계약/근거로 별도 판단해야 한다.
- `entry_ai_result_stale_or_untrusted` 2건은 단순 TTL 초과 두 건이 아니다. 043260 11:07:06은 원모델 WAIT→`semantic_rejected`, 010580 10:48:27은 `input_preflight_blocked`/`not_evaluated_provider_or_preflight`다. 두 시도 모두 retry의 quote refresh는 fresh로 기록됐고 최종 selected authority trace는 `not_available`였다. 기존 retry trace/snapshot을 진단 결속에 보존해야 한다.

## 3. 지금 시작할 개선작업

### P1-A. Zero-qty의 실제 0 / 원천 결손 구분

- 확인된 코드 결함: `src/utils/kiwoom_utils.py:get_orderable_by_margin_kt00011`의 `to_i`가 `None`, 빈값, 파싱 실패를 모두0으로 만들고 정상 return_code이면 `error=""`로 반환한다. `src/engine/sniper_state_handlers.py:_resolve_scalp_cash_budget_context`에서도 해당 값이0 cap으로 소비된다.
- 격리 mock으로 `명시적0 / 필드 누락 / malformed` 세 입력이 모두 같은 `error="", cash_amount=0, cash_qty=0`이 되는 것을 재현했다. **실제69건이 모두 API 결함이라는 의미는 아니다.** 실조회·주문은 실행하지 않았다.
- 보완: 현금 amount/qty의 field presence, parse status, 명시적0 여부, 요청 종목·단가·시각·응답 provenance를 구분해 기존 budget event→Sentinel 하위 원인으로 연결한다. 결측/잘못된 입력은 명시적 source gap으로 fail closed하고 실제0도 차단 유지한다. 예수금이 양수라는 이유로 cap0을 제거하지 않는다.
- 구현 전 필수: 현행 공식 Kiwoom revision과 관련 문서로 필드 의미를 검증하는 Official Reference Gate. 이번 점검은 로컬 파서 손실의 재현이며 upstream 의미 검증 또는 프로토콜 수정 완료가 아니다.
- 완료: missing/malformed/zero/positive/quantity-price 불일치 회귀와 exact attempt 대사, 기존 안전 cap 불변. owner는 기존 cash-budget/position-sizing·source-quality이며 #23 recheck로 해결할 사유가 아니다.

### P1-B. Refresh 전후의 다음 차단 계측 수정

- 확인된 결함: `buy_funnel_sentinel.py`의 `quote_freshness_still_latency_blocked_after_refresh_count`는 `latency_block AND refresh_attempted AND NOT refresh_applied`만 센다. 이름과 달리 실제 refresh 적용 후의 차단126은 빠지고 실패31만 표시된다. 현재 테스트도 주로 refresh 미적용 실패를 검증한다.
- 보완: 기존 event-binding에서 `refresh_not_applied_blocked`, `refresh_applied_still_blocked`, `refresh_applied_latency_pass`, `next_blocker/pending/submitted`를 분리한다. 다음 blocker에는 exact AI 하위 사유와 가격 사유를 보존한다. 기존 필드는 호환 alias 또는 명시적 deprecated 의미로 유지하고 단순 표시 보완 때문에 최근3일 schema 이력을 다시 초기화하지 않는다.
- 완료: 동일 cutoff에서 적용 후 block126/pass31과 그 이후 AI31을 재현하고, 실패·성공·동일시각·재시도·pending·later-progress 반례를 검증한다. spread99를 quote 갱신 실패로 진단하거나 refresh 성공을 submit 성공으로 표시하지 않는다. 독립 latency 추천 family를 복구하지 않는다.

### P1-C. AI 정상 거부와 입력/계약 결손을 기존 owner에 분기

- 확인된 진단 결손: core AI axis는 최종 reason/top 집계만 전달하고, 원모델→후처리→최종 authority 및 semantic rejection/preflight/실제 stale을 별도 원인으로 제공하지 않는다. 원천에는 retry original action, contract status, evaluation status, trace/snapshot이 이미 있다.
- 보완: raw action, postprocessed action, selected authority, source/contract/age, parent/attempt/trace를 기존 exact 시도에 결속한다. 정상 거부는 #76/#82의 비용 후 executable opportunity 평가로, semantic/input 결손은 기존 AI contract/source owner로 보낸다. 원모델 DROP→WAIT50은 별도 후처리 범주로 보존한다.
- 완료: 40 = fresh로 분류된 정책 veto38 + 명시적 입력/계약2의 분리, refresh 후31의 세부 대사, missing trace를 다른 시도로 채우지 않는 회귀. 정책상 거부가 경제적으로 옳은지는 별도 비용 후 outcome 검증이며 이번 수리의 선행 EV floor가 아니다. TTL 연장·Provider retry 증가·권한 우회는 하지 않는다.

### P2-D. #23의 잠재 대응 축과 실제 probe 대상 분리

- `entry_recheck_policy.scope_summary`는 terminal stage가 `pre_submit_entry_ai_authority_guard_block`이면 해당 축을 addressable로 남긴다. 그러나 runtime `evaluate_blocked_ai_score_recheck`는 canonical WAIT/EDGE/eligible_wait_probe/recovery_required와 fresh micro·기존 probe-first·cap 계약을 확인한다. 정상 DROP과 observation-only WAIT가 모두 실제 회복 대상인 것은 아니다.
- 관측한 최종 AI40건의 retry probe status는 `not_eligible`36, `not_reported`3, `semantic_rejected`1이었다. 이40건에 대해서 단순 recheck ON이 곧 제출 회복을 뜻하지 않는다. 다른 upstream 시도까지 대상0으로 일반화하지 않는다.
- 보완: 기존 owner의 진단을 `axis_addressable`, `canonical_probe_candidate`, `normal_veto`, `input_gap`, `policy_off/not_evaluated`로 분리하고 실제 runtime predicate와 불일치하는 사례를 테스트한다. 잠재 대응 축을 실제 eligible 건수로 표시하지 않는다. 같은 원천에서 diagnostic eligibility를 평가하되 OFF 상태에서 가상의 실제 arm·주문을 만들지 않는다.
- **69~74.999는 현재 코드에서 score prior band 계측이지 hard range veto가 아니다.** 우선 최소점수를 낮추는 작업은 근거가 없다. 새로운 live 허들을 추가하지 않고, canonical probe가 없으면 기존 AI 입력/판단 개선 owner로 전달한다. #23 최초 ON에 실체결/양수 EV를 새로 요구해 순환 대기를 만들지 않는다.

## 4. 최근3거래일과 실제 자동화 경계

| source 날짜 | report schema | 현재 계약 대사 | 조치 |
| --- | ---: | --- | --- |
| 9/4 | 3 | current_schema_required | 과거 evidence 유지; 숫자만6으로 변경 금지 |
| 9/7 | 5 | current_schema_required | 같은 전환 결손; 자동 복원/재라벨링 금지 |
| 9/8 | 6/exact3 | 유효 scope 존재; controller source hash·semantic 대사 PASS | 최신 유효 첫 source일 |
| 9/9 장중 | 6/exact3 | exact ledger PASS; scheduled postclose preflight는 아직 missing | 당일 장후 산출 전 `not_yet_due`; 현재 실매매 전체 실패로 해석 금지 |

- Source9/8 controller의 history는9/4·7·8, OFF 이유는 `drought_history_source_quality_gap`이다. 직접 `controller_error` 재검증은 빈 오류로 PASS했다. `runtime_candidate_ready=true`는 OFF 후보를 적용 가능한 상태이지 recheck ON이 아니다.
- 9/9 00:27:14 strict의 `drought_canonical_handoff=pass`, summary handoff PASS, missing required/downstream/stale 모두0이다. 전일 native `order_entry_recheck_history_transition_review`와 `order_entry_recheck_bounded_maintenance_review`는 canonical workorder에서 `defer_evidence/natural_acceptance_pending`으로 전달됐다. 연결 누락 때문에 장후 전체를 재실행할 근거는 없다.
- Target9/9 07:35:06 PREOPEN manifest는 recheck OFF/allowed_scopes 빈값이다. 점검 시 main PID190811(10:44:51 시작)의 whitelist env에서도 같은 OFF/빈 scope를 확인했다. 과거08시 PID24260을 현재 PID로 사용하지 않았다. 재기동 사유·전체 source 버전의 수용은 이번 점검 범위가 아니다.
- 9/9 장후에도 최근3일은9/7·8·9라 구 schema9/7이 남는다. 9/8·9·10의 세 source가 모두 유효하고 기존 같은-scope drought/안전 조건까지 충족하면 **9/11 PREOPEN이 조건부 최초 가능일**이다. 미래 ON 보장이 아니다. 3일 history는 유한한 전환 대기이며 20일 maintenance는 promotion gate가 아니다.

## 5. 실행 경계와 완료 기준

기존 `EntryRecheckNaturalAttribution0907`에서 P1-A/B/C → P2-D → targeted review/test → 필요한 기존 producer/consumer의 최소 검증으로 추적한다. 새 독립 튜닝축이나 중복 OPEN task는 만들지 않는다. 다른 세션의9/9 AI micro/cost companion·중복 arm floor 보완은 별도 작업으로 보존하며 재구현하지 않는다.

이번 점검의 완료는 최초 병목/정상 차단/원천 결손과 대응 owner·구현 acceptance를 도출하는 것이다. **구현 미실행, 발견 결함 OPEN, 실제 submit drought 미해소**다. 코드 변경·실 Provider 호출·broker 조회/주문·정책/env/lock 변경·재기동·운영 보고서 재생성·Project/Calendar sync는 수행하지 않았다. 기존 cache의 순수 cutoff 재집계, canonical controller 계약 검사와 API mock3종을 수행했다.

문서 review gate: 관련 기존 회귀 `refresh/exact/history/scope/source/maintenance` 선택40 PASS(177 deselected,1.36초), 링크·공백 검사와 `git diff --check` PASS, print-only parser36 tasks/기존 owner1개 확인. 이 기존 회귀의 PASS는 위 새 반례의 코드 수리 완료를 뜻하지 않는다. 다른 세션의 변경은 보존했고 이번 작성 범위는 이 리뷰와 기존 checklist owner의 권고 한 줄뿐이다.

## 6. 사용자 후속 지시에 따른 구현·최종 리뷰

### 6.1 현금 예산과 미수 구현의 실제 범위

현재 코드는 조회 금액을 무시하는 무제한 미수 주문 구조가 아니다.

1. `kiwoom_orders._apply_kt00001_orderable_amount_floor`는 유효 kt00001 금액에 기본 300만원의 `operator_approved_2026_07_22` 예산 하한을 적용한다. 이는 계산 예산 보정이지 브로커 주문가능수량 승인이나 주문 보장이 아니다.
2. `_resolve_scalp_cash_budget_context`는 정상 kt00011 응답의 예수금/미수불가 금액 중 양수 후보의 최소값을 예산으로 사용한다. operator floor가 적용됐으면 그 예산을 보존하되 양수 현금 주문가능 금액으로 제한한다. 실제 배분은 기존 10/15/20/25/25% tier·95% 안전예산·기존 cap이며 현금 주문가능수량 cap이 별도로 적용된다.
3. 기존 일반 SCALPING 미수 예외는 현금 부족 시 해당 종목·정확한 양수 가격의 적용 증거금률20/30/40/50/60%, 허용 수량≥1 및 금액≥1주 가격일 때만 작동한다. `kt10000` 일반 매수로 최대1주, 추가매수/잔여 leg 확대 금지다. 100%·미확인 tier/price/수량/금액은 미수 예외가 아니다. `kt10006` 신용 주문 경로는 사용하지 않는다.
4. 고정11:25 KRX exact zero-qty69개는 전부 `general_entry_margin_authority_reason=applied_margin_rate_not_margin_eligible`, rate100이다. 예산 floor 미구현이나 broker submit 실패69건이 아니다. 과거 현금 필드의 실제0/결손은 보존된 source로 판별 불가하므로 `cash_capacity_provenance_unavailable`로 남긴다.

따라서 사용자가 기억하는 미수 의도와 현행 승인 범위에 차이가 있다. 이번 수정은 기존1주 예외와 수량 owner를 보존한다. 현금 cap·100% tier 제한을 무시하거나 미수 수량을 확대하는 정책은 구현하지 않았다.

### 6.2 공식 API 확인 및 변경 범위

2026-09-09T11:43:42+09:00에 공식 upstream HEAD `234560d213acd8871ae344b5481aecd2f30287fa`를 재확인했다. [공식 API spec](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/blob/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json), `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/core/errors.py`, `postman/kiwoom-openapi.postman_collection.json`의 kt00011/kt10000/kt10006를 점검했다. 현재 revision에는 `kiwoom_docs/`가 없어 그 문서를 읽었다고 주장하지 않으며, packaged 공식 spec의 필드 정의를 사용했다.

- kt00011은 POST `/api/dostk/acnt`, `api-id=kt00011`, `stk_cd` 및 선택적 KRW `uv`다. `min_ord_alow_amt/q`는 미수불가 금액/수량, 적용 tier의 amount/q는 해당 증거금률 주문가능 금액/수량이다. 부호 포함 정수와 0-padding을 보존하며 음수를 절댓값으로 승격하지 않는다.
- return code, 연속조회 header, real/mock 분리를 교차 확인했다. 요청 endpoint/payload/continuation, 토큰·rate limit·retry·주문 API는 변경하지 않았고 실제 API 호출/주문 예제 실행은 하지 않았다.
- 새 테스트 파일은 기존 `src/tests/`의 main-entry cash/margin contract 테스트로 배치했다. 새 engine-root producer 또는 별도 튜닝축은 추가하지 않았다. 다른 세션의 `kiwoom_utils.get_top_fluctuation_ka10027` 및 AI/scanner/machine 수정은 보존했다.

| 보완 | 구현·직접 소비 | 리뷰 기준 |
| --- | --- | --- |
| P1-A cash source | kt00011 parser → cash budget → 기존 margin/log helper → Sentinel zero-qty | valid positive/zero/negative, missing, malformed를 구분. 요청 code/price·응답시각·capacity-only SHA256·field status 기록. 결손/invalid 성공 응답은 cap0 및 명시적 source error로 종결하며 uncapped fallback/미수 권한으로 전환하지 않음. 일반 transport 오류의 기존 fallback 정책은 변경하지 않음 |
| P1-B refresh | 기존 ordered exact bindings → transition 진단 → latency observation/workorder | 미적용 차단/적용 후 차단/적용 후 pass/다음 차단 사유 분리. 기존 `still_latency_blocked_after_refresh_count`는 미적용 차단 의미의 legacy 필드로 명시. 단순 표시 보완으로 schema6/exact3 이력 초기화하지 않음 |
| P1-C AI authority | terminal exact row → raw/postprocessed/selected action·각 trace/source/age → AI observation/workorder | fresh WAIT/DROP와 semantic/preflight/stale/untrusted 분리. retry trace로 selected trace를 채우지 않음. 정책상 정상 veto가 경제적으로 최선이라는 의미는 아님 |
| P2-D recheck | 공유 canonical WAIT predicate → runtime 진단·Sentinel → controller의 hash-bound sentinel evidence | 잠재 대응 시도/확인된 canonical 입력/unknown/normal veto/source gap 구분. 미관측 candidate는 null/unknown이며 기회0이 아님. canonical 입력 통과와 policy OFF·micro/freshness/cap·실제 arm은 별도 |

기존 `order_entry_submit_drought_auto_resolution`의 implementation provenance는 observation breakdown을 그대로 소비한다. #23은 `sentinel_evidence.contract`로 같은 진단을 전달받는다. 진단 owner 이름은 새로운 native workorder ID나 #76/#82에 대한 자동 전략 수정 권한이 아니다.

### 6.3 최종 검증과 자동화·목적 부합성

- 같은11:25 cache를 순수 builder로 재계산: exact513=terminal513+pending0+submit0, refresh 미적용 차단31/적용 후 차단126/pass31, pass 뒤 WAIT18/DROP12/semantic1. AI terminal40=WAIT21/DROP17/preflight1/semantic1; zero-qty69는 provenance unavailable, margin rate100 사유 보존. 이유 label은 중복 가능하며 transition set을 terminal 수에 더하지 않는다.
- 전일9/8 controller의 현행 PREOPEN source/decision 검증 재실행은 오류 빈값 PASS다. 이력 판정/활성화 기준·가격/latency/AI TTL·주문 수량 제한을 완화하지 않았다. 69~74.999는 score prior이며 20점/99점 canonical 입력도 기존 나머지 조건을 충족하면 runtime predicate를 통과하는 회귀로 확인한다.
- 설치된 cron은 Sentinel 매5분, main postclose20:10, PREOPEN07:35 `auto_bounded_live`다. 새 보고서 진단은 다음 정기 프로세스가 자동 소비하며 별도 수동 보고서 재생성은 불필요하다. #23 source→controller→다음 PREOPEN 연결은 기존 owner 그대로다. 유효 최근3일 및 같은 scope2일 drought 등 기존 조건을 충족해야 하며, 새 진단 때문에 별도 양수 EV/실체결/추가 표본 floor를 넣지 않았다.
- 자연12:00:05 산출물 SHA256 `b322c191c3422b4d3c205ae1b3476714984953857809b3c4139422c6e023da0a`, wrapper DONE12:00:30, KRX 계약 PASS와 unknown 분리 필드를 읽기 확인했다. 당시613=terminal613+pending0+submit0이므로 실제 drought 해소는 아니다. 이 산출물은 코드 작업 중의 정기 생성이며 이후 추가된 표시 필드의 최종 generation receipt는 별도 확인한다.
- PID190811(10:44:51 시작)은 변경하지 않았다. 새 cash parser/log helper 및 runtime 진단은 해당 장기 실행 PID에 hot reload되지 않는다. 기존 승인된 정상 기동 뒤 receipt/field 소비를 확인해야 하며, 코드 수리 완료를 현재 PID 반영으로 표시하지 않는다.
- 기대효과는 정상 거부를 코드 결함으로 오인하거나 source 결손을 현금 부족·기회 부재로 오인해 잘못 튜닝하는 일을 줄이는 것이다. 이 수정만으로 제출이나 순이익 증가를 보장하지 않는다. 비용 후 executable opportunity·실제 submit/fill/terminal/net 수용은 기존 `EntryRecheckNaturalAttribution0907`에서 계속 추적한다.

`korstockscan-review-gate`에 따라 구현→리뷰→보완→재검증을 반복했다. 리뷰에서 진단 추가에 따른 기존 controller 비교 불일치, missing/invalid 성공 응답의 fallback 우회 가능성, unknown을 candidate0으로 오인하는 표현, 비유한 unselected tier 파싱 예외를 보완했다. 최종 검증 결과는 아래 기록으로 닫는다. 실주문·Provider 호출·수동 env/lock·재기동·장후 전체 재실행·외부 sync는 수행하지 않았다.

최종 검증: 직접 parser/Sentinel/controller/PREOPEN/recheck/allocator 및 기존 margin compatibility 535 PASS, workorder submit-drought 전달14 PASS, 실제 sniper 수량·재검증 선택12 PASS로 **서로 다른561 tests PASS**다. 반복 실행 횟수는 합산하지 않았다. Python compile, `git diff --check`, 문서 print-only parser PASS이며 기존 자연 acceptance owner는 OPEN으로 유지했다. 수정 범위의 미해결 P0~P2 finding0; 전체 저장소 무결함 또는 경제성 PASS를 주장하지 않는다.

최종 자연 진단 receipt: as-of12:05:05, SHA256 `9665d06c113d3bc9dacdaa5befcc41d8da48575d920c7a192910ab99803babc3`, wrapper DONE12:05:24. 다음 blocker의 구체 reason·selected source·candidate unknown 최종 필드 존재 및 KRX 계약 PASS. KRX626=terminal626+pending0+submit0; 현금 provenance unavailable79는 기존 PID 계측 한계를 그대로 드러낸다. 후속 parser/PID 소비·경제성 acceptance는 남지만, 이번 진단 producer의 자연 생성은 확인했다. 운영 산출물은 정기 작업이 생성했으며 이 세션에서 재생성하지 않았다.
