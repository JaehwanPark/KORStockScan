# 최초 매수 수량 연구 실행·리뷰 — 2026-10-17

## 결정과 코드 범위

사용자 확정은 **익절 실현 순이익 원화 가중치로 후보 생성, 전체 거래의 비용 후 EV·순이익으로 최종 선정**이다. 현재 유효한 최초 정책은 갱신용 우월성·자연소비 조건으로 재승인하지 않는다. [후속 연구 계약](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#7-2026-10-17-후속-연구-실행-계약)의 실행 owner는 `InitialQuantityResearchRepair1017`다.

- 기준 선택: `post-aux-priority-20261017-c5aeda844`, commit `c5aeda844dfab36146d04e6305cb29508cd47d4f`.
- 구현 commit: `c4467c424b77b0a91370a95a3f4c7111e4db4efc`, branch `codex/initial-quantity-research-repair-20261017`.
- 작업본: `/home/ubuntu/KORStockScan-worktrees/initial-quantity-research-repair-20261017`.
- 불변 후보: `/home/ubuntu/KORStockScan-runtime-releases/initial-quantity-research-20261017-c4467c424`.
- 변경 Python은 기존 scalping reader·평가기·semantic 및 기존 회귀 파일이다. 새로운 engine-root 모듈, 주문 wire/parser 변경은 없다. 다른 작업본의 미커밋 코드는 통합하지 않았다.

## 1 현재 입력 검증과 수리

앞선 [원천 감사](initial-quantity-runtime-postclose-result-review-2026-10-17.md)의 수치는 당시 세대다. 선택 c5aeda에는 IQ171의 native metadata reader와 IQ173의 결손 의미 수리가 이미 포함되어 있다. 이번에는 기존 수리를 다시 구현하지 않고 다음을 확인·보완했다.

| 대상 | 결과 |
| --- | --- |
| fact seal | 9/30·10/15·10/16 모두 native generation 검증 성공. 큰 completion projection을 전체 decode하지 않는다. 기존 크기·변조·stale·비용 정정·gzip·동시 변경 회귀도 검증했다. |
| 실제 실행 이벤트 | 10/16 compact partition 9,923,956바이트에서112개를 읽어112개 소비·제외0. 계획9·leg10·bundle8과 별도 경제/진단 이벤트를 구분했다. |
| 날짜 | emitted 시각의 KST 날짜를 해석하고, 날짜 없는 입력에 실행일을 임의 부여하던 경로를 제거했다. |
| census | 전체 보고서와 bounded model refresh가 같은 보존식을 사용한다. 검증된 stage 제외만 모수 감소를 설명할 수 있고, 미설명 결손/초과·잘못된 count·전역 품질 차단은 source gap이다. 제외 record/attempt·원 이벤트 SHA·품질 계약을 보존한다. |
| 추가 리뷰 결함 | 전체 보고서 입력 allowlist가 probe 잔량 연결 필드7개를 제거했다. 실제 입력 읽기→품질 필터→lineage→`build_report(write=False)` 회귀로 수정했다. 직접 helper만 호출하던 테스트의 연결 범위를 보완했다. |

추가 실제 원천 검증에서 native lineage는 `ready`다. 계획9건은 발행8건과 의도된 유예1건이며, 발행8건의 identity 연결·유효성, 고유 leg10건을 확인했다. 미연결·격리는0이며 raw fallback 호출도0이다. 원 registry1,649이벤트의 파일 SHA·tail hash를 검증했다.

49350의 잔량 주문2건은 봉인된 probe context와 서로 다른 registry intent로 복원되어 계획 leg1·2·3의 제출수량1+1+2=4주와 일치한다. 상태는 `valid_cancel_pending`으로, 확인 체결2주·미체결 제출2주이며 취소 확정·남은 주문수량·비용은 `null`이다. 계획 연결이 정상이라는 판정으로 주문의 최종 취소나 비용 확정을 대신하지 않는다. 원본 로그·registry·운영 보고서는 수정하지 않았다.

## 2 비용·후행 자료 대사

현재 읽기 전용 DB fact와 native 완료 overlay를 결합하면 **입력16, 완료13, 보유3, 비용 적격 완료0**이다. 원 entry-day DB의 완료9/보유7 중4건은 이후 날짜의 봉인 완료 원천으로 연결됐다. DB 원행·과거 영수증을 수정하지 않았다.

| 완료 거래 결손 | 건수 | 다음 근거·종료 조건 |
| --- | ---: | --- |
| 동일 종목·날짜에 여러 포지션 | 10 | 공식 비용 집계 단위 또는 정확한 정산 근거를 확인한 뒤 거래별 비용·수량을 대사한다. |
| Main custody 미확인 | 1 | 49293의 원 buy-parent/order-intent·계좌/owner 귀속이 필요하다. BUY 체결만으로 Main custody를 만들지 않는다. |
| 완료 projection identity 결손 | 1 | 49266의 동일 날짜·record·주문/체결번호에 연결된 원 SELL terminal을 확인한다. 현재 bounded 자료만으로 생산 누락/소비 누락/복구 불가를 단정하지 않는다. |
| 과거 비용 원천 부재 | 1 | 49013은 확인되지 않은 과거0손익을 실적으로 사용하지 않는다. 원 비용·완료 근거 없이는 제외한다. |

`ka10076`에는 `tdy_trde_cmsn`, `tdy_trde_tax`가 있으나 현재 공식 설명은 주문별/체결별/누적 집계 의미를 정의하지 않는다. 종목 합계도 삼성1,995/2,005원, HPSP691/711원으로 각각10/20원 차이가 있다. 나머지3종목의 합계 일치도 개별 배분 의미를 증명하지 않는다. 기존 배분 guard를 제거하거나 추정 비용을 actual로 저장하지 않았다.

Kiwoom 공식 참조 게이트: 조회 `2026-10-17T12:48:23Z`, upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`. 검사 경로는 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/client.py`, `postman/kiwoom-openapi.postman_collection.json`이며 현재 tree에 `kiwoom_docs`가 없다. REST path/api-id/JSON·headers·연속조회·실전/모의 구분도 교차 확인했다. 새 계좌·주문·provider 호출은0이다. 상세 provenance는 아래 JSON에 보존했다.

후행453틱과 기존 종료1건을 원 증거대로 유지했다. 49343은 첫 실제 주문 시작+1200초 종료다. 나머지5개는 과거 종료 증거가 확인되지 않았다. 조기 청산과 일치하는 사례도 있지만 원인을 확정하지 않았다. 현재 선택 코드의 lifecycle 시작·중단·재시작·queue/durable 계약은78개 회귀로 확인했으며, 과거 terminal을 생성하지 않았다.

이 비용·원천 후속은 기존 `InitialQuantityProducerConsumerRepair1010`의 경제/원천 Acceptance로 연결한다. 신규 코드 수리 완료와 비용 정산 근거 확보는 각각 보고한다.

## 3 신규 평가 버전과 마지막 소비자

신규 선정은 `initial_quantity_all_trade_ev_selection_v3`다. v2 실행/비용 replay는 유지하며, 과거 봉인 평가를 검증할 때는 저장된 v2 알고리즘을 명시해 재현한다.

- 익절 가중 수익 증가 필수조건을 제거하고 전체 거래의 원거래 기준금액 대비 평균 paired EV 개선→원화 순이익 개선 순으로 학습 후보 하나를 선정한다.
- 동일 비교 비용의 부모를 사용하고, 분모 결손을 actual 손익으로 대체하지 않는다. 신규 replay의 원금은 원 fact의 매수가×수량과 결속한다.
- 부분체결·모델상 미체결을 비교에 남기며, 원천 결손을 부모 성과로 채우지 않는다.
- 학습의 후행 자료 coverage를 계산할 때 holdout의 익절 거래를 사용하던 누출도 수정했다. holdout 결과로 차순위를 다시 고르지 않는다.
- 기존 표본·coverage·독립 날짜·형상/시간 guard와 최초 생성의 낮은 허들은 유지한다.
- stage validator는 v2/v3 평가를 재현하고 미지원 버전은 거부한다. bounded 의미 감시기도 execution/selection 버전 쌍을 확인해 알려지지 않은 report 버전이나 새 평가의 잘못된 원천 조합을 정상으로 표시하지 않는다.

## 4 실제 원천 재생과 성능

현재 원천으로 v3의 불변 stage를 격리 tmp에 발행하고 native validator를 통과했다. 원 입력16/완료13 중 비용 적격0이므로 `economic_sample_status=cost_missing`, `carry_parent`다. 실제 성과0원·무효과를 측정한 결과가 아니다. 기존 production v2 stage도 같은 새 코드에서 유효했다.

검증 stage SHA: `2245ad31098d3d981720d5b145326fcec9e8b2204ac56e8803ae0ed64f00da7b`. 실행1.331초는 비용 결손0적격 경로 확인이며 전수 성능 측정이 아니다. 격리 재생 전후에는 원 current·selector·production committed-stage bytes가 유지됨을 확인했다. 이 재생의 쓰기는 기존 내용 주소 기반 empty joint evidence와 격리 tmp의 stage뿐이다.

성능은 선택/후보를 교대해3회 비교했다. 합성60거래·3일·240조합의14,400결과는 양쪽·반복 모두 같았고, 원천 추가80거래에서는19,200결과가 같았다.

| 모드 | 선택 중앙값(초) | 후보 중앙값(초) | 확인 |
| --- | ---: | ---: | --- |
| cold | 3.485 | 3.326 | 60거래·14,400조합 계산 |
| warm | 0.949 | 0.943 | 원천 decode·새 조합 계산0 |
| 비용 정정 | 0.949 | 0.944 | 원천 decode·새 조합 계산0, 실제 집계 정정 반영 |
| 새 날짜 | 2.018 | 1.944 | 새 날짜20거래만 읽고4,800조합 추가 |

관리 resident-data peak8,713,984바이트는64MiB 예산 안이다. 프로세스 전체 RSS 약146MiB는 별도 지표다. 기존 stage14,400초 예산 내이며 네트워크를 차단했다. 차이는 작거나 반복 편차와 겹쳐 **비악화·예산 준수·캐시 재사용**으로 판정한다. 추가 최적화나 실제 운영 전체 데이터 처리량·실거래 EV 개선은 입증하지 않는다. 합성 원천은231,000바이트이며 source-gap 조합도 그대로 비교했다.

## 5 검증·준비 상태

- 영향7개 suite900 PASS /42.92초. 이후 의미 감시 버전 조합 보완의71개 표적 회귀 PASS /2.83초. 중복 검증 수를 합산하지 않는다.
- 비용44개, capture78개 별도 표적 검증 PASS. compile·diff 검사 PASS.
- 실제 stage v3 및 과거 stage v2 native validation PASS, 10/19 수량 loader PASS.
- private mount/network namespace에서 코드 인계·schema·bootstrap·native parity를 검증했다. parity는128범위·76,800행·598신호의 불일치0이며, 호스트 보호 원천20개 SHA는 유지됐다. 환경 설정 전체와 기존 OPEN6개를 보존했다.
- 다음 세션 준비본과34개 파일을 운영 위치에 발행하고 selector를 `c4467c424`로 전환했다. 발행 후 native `current_full_contract`는 PASS/findings0이다. 발행 시각은 `2026-10-17T22:18:26.612209+09:00`, 검증 시각은 `22:20:10.481905+09:00`다.
- 추가 읽기 전용 사후 대사는 `22:22:10.214962+09:00` PASS다. current full contract·strict/controller issues0, release set·cron8개 target·10/19 PREOPEN/start의 선택 코드 경로를 확인했다. 보호 source hash와 승인된 미래 보조정책 연결도 일치했다. 이 검증은 실제 PREOPEN 실행이나 PID 소비를 생성하지 않는다.
- 승인된 PRE 보조정책2개를 새 미래 bundle에 인계했으며128개 binding·rollback·registry를 보존했다. 실행 중 Main이 없는 다음 정규 기동용 배포이며 재시작·provider 호출·주문은0회다. 실제 PID 소비는 `false`다.
- 현재 수량 정책은 기존 부모5단계·분할·프로필 시간이다. 새 수치 정책의 경제성은 비용 적격0으로 미평가다.

운영 selector 선택·준비본 검증과 실제 PID 소비는 별도 상태다. 다음 영업일은 `2026-10-19`이며 PREOPEN07:35·정규 Main07:55의 기존 경로를 사용한다. 실제 소비 확인은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유하고, 비용·역사 원천은 `InitialQuantityProducerConsumerRepair1010`가 소유한다. 최초 정책에 추가 우월성이나 배포 전 자연소비 조건을 만들지 않았다.

## 근거

재현 자료의 원본 디렉터리는 `/home/ubuntu/KORStockScan-worktrees/initial-quantity-research-repair-20261017/tmp/quantity-research-20261017`이며, 최종 사본은 `tmp/initial-quantity-research-20261017/validation`에 보존한다. `baseline.json`, `current-census.json`, `cost-capture-reconciliation.json`, `real-source-validation.json`, `final-regression.txt`, `final-semantic-version-regression.txt`, `performance-3rep-final/summary.json`과 실행 도구·원값이 포함된다. 비용 감사 JSON SHA는 `42946452a542999c5e6fee5b36783c2a7cf0e0972d81a1c803462401d963b365`다.

실제 lineage 검증은 `validation/real-lineage-acceptance-20261016-c4467c424.json` 49,092바이트, SHA `46a3b59fe29d06224848dedfa1e066c6e9e8560814be1d9dcf3d5c81cd631b42`다.

배포 증거는 `tmp/initial-quantity-research-20261017/preflight-c4467c424`의 `private-preflight-summary.json`, `publication-plan.json`, `deployment.json`, `published-native-verification.json`이다. 발행 계획34개·39,142,316바이트의 원천 SHA/운영 변경 전 SHA를 독립 리뷰했고 불일치0이었다. native 잠금·CAS·selector 마지막 발행·실패 복구를 확인했으며 원 시도·준비·정책 증거는 보존했다. 격리·불변 snapshot 경로는 준비본이 참조하므로 이동하지 않는다. 기존 tmp 보존 계약상 명시 만료 manifest가 없는 증거는 자동 만료되지 않으며 관련 native 회귀6개가 통과했다.

최종 읽기 전용 영수증은 같은 디렉터리의 `postpublication-verification.json`, SHA `e355960e2572314c07a5c11b35e7fd3f9b7ad2132f37b39219857e914212b80c`다. 이번 입력·선정기 수리·리뷰·다음 정규 기동용 코드 배포는 완료하며, 새 수치 정책의 경제성·역사 비용 원천·실제 PID/자연 행동은 기존 OPEN owner의 종료 조건을 유지한다.
