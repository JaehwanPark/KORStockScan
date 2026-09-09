# 외부 census + #8/#9 + #49 scanner 보완·최종 리뷰

작성 기준: 2026-09-09 KST. 범위는 사용자가 요청한 source-only 보완과 코드 리뷰다. 장중 전체 모니터링·전체 장후 재실행·봇 재기동·실주문·수동 PREOPEN 적용을 실행한 기록이 아니다.

## 1. 판정과 목적

목표는 **비용을 차감한 작은 수익을 반복적으로 얻을 기회의 누락 원인을 정확히 찾아 기존 담당 경로로 전달**하는 것이다. 무조건 매수, gross 상승률, snapshot 개수 또는 보고서 성공을 수익 개선으로 취급하지 않는다.

이번 보완은 정상 hard-cutoff를 scanner 실패로 세는 오탐, 논리 세션/물리 route 혼동, fetch/pool 계측 부재, source 결손을 막연한 표본 대기로 표현하는 문제를 다룬다. #49의 비용 차감 작은 양수 edge와 기존 자동 PREOPEN 계약은 유지한다. 검증 범위의 코드 수리, 다음 자연 산출물, fresh PID 소비와 경제성은 독립 상태다.

## 2. 확인한 근거와 구현

| 범위 | 발견·근거 | 보완·완료 경계 |
| --- | --- | --- |
| 실행 가능 시간창 | 9/8 v4의 KRX raw299 / 구간 eligible21 중 미발견3은 224060 11:00:02, 017900·317330 15:20:01이다. 후자 둘은 기존 15:10 신규매수 hard-cutoff 이후다. | v5 `scope_exclusion`이 immutable cutoff를 제외 사유로 보존한다. 원래 raw 분모는 유지하고 다른 시점/PID의 동적 매수창을 추정하지 않는다. 11:00 건까지 정상 차단으로 바꾸지 않는다. |
| premarket route | `PREMARKET_KRX_LIKE`는 논리 cohort이며 NXT 0D 원천과 단순 문자열로 합칠 수 없다. | decoder가 검증한 exact item/route/epoch BBO와 같은 code+promotion일 때만 물리 NXT로 결속한다. AI trace는 같은 record 증거도 필요하다. route 미확인/다른 promotion은 그대로 미대사다. |
| 최초 소비 결손 | promotion은 있으나 attach가 없으면 fast-precheck 결손으로 오인할 수 있었다. | attach 미도달을 먼저 표시한다. 후속 fast/heavy/AI 증거가 있으면 실제 미소비가 아닌 attach receipt 결손으로 분리한다. 실패 attach 시도·사유도 동일 promotion 범위에서 보존한다. |
| 원천 우선순위·예산 | 9/9 11:20까지 primary KRX 29 capture 중20이 shared-read defer로 빈 원천이었다. 기존 순서에서는 secondary가 앞서고 continuation도 사용했다. | 모든 venue의 primary panel을 secondary보다 먼저 요청하고 census의 ka10027만 최대1 page로 줄였다. 기존 limit/filter·공유 admission/cooldown·retry·ka10004 bound는 유지한다. 실제 첫 page가200행일 수도 있으며 전체 시장 전수라고 주장하지 않는다. |
| fetch/pool 관측 | 기존 `source_seen/candidate_evaluated`는 promotion/prune proxy여서 scanner 외부 또는 adapter 내부 제외를 구분하지 못했다. | scanner package의 `scanner_source_census`가 기존 호출 반환과 rank 후 pool을 cycle/hash/count/물리 route로 기록한다. 최대1024 row/receipt, omitted/rejected 보존, UNKNOWN route·unbound cycle·잘못된 hash/권한/계수는 정확한 포착 근거가 아니다. 신규 API 호출·선정 변경은 없다. |
| #8 → #9 → workorder | hook 반영과 exact BBO/pre-anchor 원천 충족을 같은 `waiting_sample`로 읽기 쉬웠다. | `source_readiness`로 runtime receipt 미확인, route/time/원천 조사, maturity 대기, 비교 표본 floor를 분리한다. native order ID를 유지한 채 scout→중앙 workorder로 전달한다. `acceptance_tests`는 진단 수리, 기존95%/20 resolved 등의 기준은 `economic_acceptance_criteria`로 분리한다. |
| #49 0전환 | 9/8 candidate71 / control2135 관측, 실제 full completed0 / 1, 유효 source5일이다. 단순 `keep_collecting`만으로 유한 ETA를 주장할 수 없다. | natural acceptance v3는 candidate 완료0이면 기존 #119 BUY Funnel/#23 owner의 exact 전환 조사로 안내한다. 동일 record/promotion/symbol/date/venue/session·attach 이후 후속 receipt를 보고한다. receipt 부재는 실제 veto가 아니다. 20유효일/10월2일 유지 재검토는 새 안내보다 우선한다. |
| 최종 소비 | census의 native followup은 중앙 workorder 소비 계약이 있고 #49 경제 승인과는 별개다. | census v4/v5 exact-date/self-hash/native ID·files/tests/downstream를 workorder가 보존한다. #49 새 전환 진단의 직접 consumer는 해당 Markdown 보고서와 기존 체크리스트 검토다. #119/#23의 자동 정책 입력을 새로 연결했다고 주장하지 않는다. |

9/8 census 원본 artifact SHA256: `a9c4b1215bf096b0fcb9519fc89f5ce92ab97d182cf03ea97efae1846dc69345`. 과거 원본을 덮어쓰거나 과거 결손을 합성하지 않았다. 신규 파일 위치는 live scanner 계측 `src/scanners/scanner_source_census.py`, 테스트 `src/tests/test_scanner_source_census.py`다. engine root 신규 모듈은 없다.

## 3. 조건의 과도성·달성 가능성

- 진단 수리는 exact 원천/시간/route/권한·count/hash와 직접 consumer 테스트로 닫는다. 양수 EV, 실제 주문, 모든 horizon 또는 live 승격 표본을 새 완료조건으로 붙이지 않는다.
- census 구간 판정의3 capture/20 unique episode와 master·연속성은 유지한다. 20개 미달이어도 개별 행의 결손 원인을 볼 수 있으며, 경제성95%/20 resolved/censor20%를 진단 gate로 요구하지 않는다. cutoff 제외로 분모가 줄었다고 floor를 낮춰 정상 판정을 만들지 않는다.
- #49의 고정 +0.10%p uplift는 이미 제거된 상태다. `small_net_v1`은 작은 candidate 순EV·증분도2-SE 여유, full completed base/독립 holdout 각각20건·5일 및 군별10건·3일, tail guard와 자원배분 증거를 통과하면 승인할 수 있다. 이번에는 이 승인 guard를 바꾸지 않았다. 양수 평균만으로 손실 꼬리나 표본 불확실성을 무시하지 않는다.
- candidate completed0은 승인 floor가 수학적으로 불가능하다는 증거도, 시간이 해결한다는 증거도 아니다. 첫 전환 결손을 확인하고 `finite_eta=null`을 유지한다. 현 유지 재검토 deadline에서 통합·폐기를 판단하며 임의 자동 OFF하지 않는다.
- 기존 `small_net_review`의 net +0.03/+0.07/+0.10% × 1/3/5/20분을 재사용한다. mark-price·희소 BBO 경로는 실제 체결/연속 first-hit/다주문 slippage 검증이 아니다. 실현 비용·실체결·자본점유 개선은 별도 확인한다.

## 4. 자동화와 실제 반영

| 경로 | 코드 연결 | 현재 확인·남은 경계 |
| --- | --- | --- |
| census collector/report | 기존 정기 wrapper가 새 Python producer를 실행한다. cron·wrapper·API 상한은 변경하지 않았다. | 12:00 자연 capture에 primary 우선/max_pages1 receipt가 있다. KRX primary200행, NXT primary는 shared-read defer0행이다. 순서 보완이 공유 예산 고갈까지 해소했다고 보지 않는다. |
| census v5 | 같은 정기 report가 v5/scoped v2·source census를 생성한다. | 12:00:39 자연 report는 `partial_diagnostics_ready`, NXT premarket eligible34 진단 가능이나 KRX eligible0이다. 시장 전체 포착 정상은 아니다. 이 산출물은 작업 중간 source를 소비한 증거이지 최종 수정 전체의 자연 acceptance가 아니다. |
| scanner fetch/pool | 기존 scanner iteration의 source-only hook이다. 예외가 선정/가드를 veto하지 않고 canonical JSON에 batch를 한 번 보존한다. | 12:00 report의 새 receipt0. 기존 메인 PID 반영 완료로 세지 않는다. 별도 허용된 정상 fresh PID 이후 자연 cycle→pool→report 소비가 필요하다. 이번 작업은 재기동하지 않았다. |
| #8/#9 및 중앙 workorder | 다음 정기 producer가 source readiness와 분리된 수리/경제성 조건을 전달한다. | fixture에서 native ID·권한·필드의 끝단 전달을 검증한다. 최종 장후 자연 generation/hash·strict summary 소비는 기존 OPEN owner에 남는다. |
| #49 정책 적용 | 검증된 후보→다음 PREOPEN immutable exact-date receipt→runtime bounded 동일-tier bonus, 별도 재승인 없음. | 9/9 실제 receipt는 `active=false`, `prior_policy_not_live_auto_apply_ready`, `operator_approval_required=false`. 승인 대기가 아니라 경제 근거 미달이다. 보너스 OFF는 scanner 전체 OFF가 아니다. |

기대효과는 오탐성 scanner 수리·무의미한 동일일 replay를 줄이고, 유효한 상승/반등 기회가 어느 단계에서 사라지는지 더 정확히 좁히는 것이다. submit drought 해소나 순이익 증가를 이미 달성했다고 주장하지 않는다. shared-read defer·과거 ingress 결손·fresh PID 미반영은 남은 자연/운영 경계다.

## 5. 공식 API 검증

2026-09-09 11:37 KST, 공식 [Kiwoom REST API 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa) revision `234560d213acd8871ae344b5481aecd2f30287fa`를 확인했다. `_data/kiwoom_api_spec.json`의 ka10027, `kiwoom/specs.py`, `kiwoom/core/client.py`의 fetch_page/iter_pages, `postman/kiwoom-openapi.postman_collection.json`의 real/mock ka10027 요청을 대조했다. 해당 revision에는 `kiwoom_docs` 디렉터리가 없어 현재 published spec/client/Postman을 검증 근거로 기록한다.

POST `/api/dostk/rkinfo`, `api-id=ka10027`, stex1/2/3, 기존 필터와 `cont-yn/next-key` continuation을 확인했다. 이번 변경은 source-only caller의 page 상한 축소뿐이다. 문서의 모호한 source 의미를 새 매매 권한으로 해석하지 않았고 실제 Kiwoom 호출로 검증하지 않았다.

## 6. 리뷰·검증과 후속 owner

`korstockscan-review-gate`에 따라 producer→decoder→report→workorder/Markdown·기존 PREOPEN consumer를 검토했다. attach receipt 오분류, naive KST timestamp 처리, maintenance 알림 우선순위, route 충돌·unbound cycle, 계수 strictness와 canonical/text payload 중복을 보완했다. 서로 다른 source cycle의 단계별 관측은 전환 pair로 세지 않고 `source_pool_cycle_join`을 별도로 검증한다. 잘못된 pool 행은 rejected 계수로 분리한다.

최종 검증(12:10 KST): 검토 범위 미해결 P0~P2 finding 0. 관련13개 pytest 모듈 **781 passed / warning1**, 마지막 malformed-row 격리 보완 후 직접 테스트 **13 passed / warning1**. 두 수치를 고유 테스트 수로 합산하지 않는다. 변경 Python11개 compileall, Black 확인과 `git diff --check` 통과. 문서 print-only parser는36항목, 현행 `ScannerLookupAttentionNaturalEvidence0908` 정확히1건을9/9 체크리스트에서 확인했다. 경고1건은 표시된 테스트 결과로 보존하며 테스트 실패로 세지 않는다.

검증 모듈(`src/tests/`): `test_market_opportunity_census.py`, `test_market_opportunity_review.py`, `test_scanner_source_census.py`, `test_entry_turn_point_replay.py`, `test_scanner_lookup_attention_tuning.py`, `test_scanner_lookup_attention_net_approval.py`, `test_scalping_scanner_candidate_pool.py`, `test_rising_missed_scout_workorder.py`, `test_rising_missed_intraday_feedback.py`, `test_build_code_improvement_workorder.py`, `test_observation_source_quality_audit.py`, `test_pipeline_event_logger.py`, `test_kiwoom_market_data_contract.py`.

설치 상태도 읽기 전용 재확인했다. census5분 capture와20:10 main postclose가 등록되어 있고 main wrapper는 #8→#9, #49 producer와 policy 검증을 호출한다.07:35 PREOPEN cron의 `auto_bounded_live`/auto apply와 wrapper의 lookup immutable receipt 발행이 연결되어 있다. 예약과 코드 경로를 자연 완료·실매매 효과로 대체하지 않는다.

실행하지 않은 범위: 비용 큰 과거 report 재생성, Provider/API 평가, bot/service restart, live env/lock/threshold/수량/주문 변경, commit/push, Project/Calendar sync. 다른 작업의 AI·BUY Funnel·기계·브로커 변경은 이 리뷰 완료 범위로 합산하지 않는다.

현재 후속은 [9/9 체크리스트](../checklists/2026-09-09-stage2-todo-checklist.md)의 기존 `ScannerLookupAttentionNaturalEvidence0908`이다. 새 중복 task를 만들지 않는다. 정기 final source/hash·#8/#9 전달·#49 v3 안내·다음 적법한 fresh PID 소비와 실제 full-fill 경제성을 각각 확인한다. 권한 밖 fresh PID 반영 또는 새 선택 surface가 필요하면 별도 실행 권한 없이 수행하지 않는다.
