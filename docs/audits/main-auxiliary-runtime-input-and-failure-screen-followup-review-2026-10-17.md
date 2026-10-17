# 보조판정 운영 입력 구현·실패 차단 후속 비교 — 2026-10-17

사용자의 다음 액션 실행 지시에 따라 운영 입력 구현, 잔여 연구 예산의 실제 비교, 코드리뷰·수정과 정책 인계 준비를 완료했다. 실행 owner는 [오늘 체크리스트](../checklists/2026-10-17-stage2-todo-checklist.md)의 `AuxiliaryRuntimeInputFailureScreen1017`이다. 프리 승리 PASS4점 회복을 확인했으나 실패 차단은 개선되지 않았고 애프터는 악화했다. 정책 발행·선택 변경·배포·재기동은 수행하지 않았다.

## 1. 연구 질문과 변경 경계

[직전 수리 연구](main-auxiliary-risk-role-contract-research-review-2026-10-17.md)는 raw 현행 입력61/97승(62.9%)→ROLE_VOCAB_PATH73/107승(68.2%)이었다. 새 연구는 이 두 수치를 다시 검증하는 비교가 아니다. 양쪽 모두 같은 동결 RVP 입력을 사용하고, 실제 기존 prompt와 단일 경로·수급 해석 문구를 비교하여 문구의 추가 효과만 측정한다. RVP 대조군은 연구 대조군이며 현재 운영 정책이 이미 RVP를 사용한다는 뜻이 아니다.

직전 후보가 통과시킨 STOP6점·TIMEOUT28점, 차단한 WIN34점은 개발 진단으로만 사용했다. STOP6점은 모두 비삼성 PRE 기존 패턴으로 짧은 범위의 가격 반복·작은 마지막 BUY가 관측됐다. 그러나 TIMEOUT28점 중17점과 WIN 오차단34점 중18점 모두 최근 관측 수익률0이어서 평탄한 가격이나 작은 BUY 하나로 실패를 단정할 수 없다.

단일 후보는 마지막 uptick·누적 수익률만 보지 않고 관측 가격 수준의 진전과 반복을 구별하도록 했다. 수량과 가격 위치의 관계는 실제 제공된 경우만 사용하며 짧거나 평탄한 관측 자체로 실패를 간주하지 않는다. 과거 매도·VWAP 미회복·스프레드 단독 veto, 새 수치 문턱·추가 확인, 진입 전 상승으로 진입 후 목표 달성을 대신하는 해석은 금지했다. 내부 문구는 English ASCII이며 호출 전에 동결했다.

## 2. 원천·표본·실제 호출 계약

모집단의 현재 기계 확인점14,005개와 확정2,342개의 원천 계약은 직전 연구에서 이어받았다. 직전 corrected index1,492개에서 현재까지 모든 보존 세대·두 응답 위치·불명확 시도를 대사해 이미 호출한175개 key를 제외했다. 정확 미사용 확인점은1,317개(기존1,183·확장134),12scope다. 삼성은 AFTER만 남고, 확장 패턴은 두산 PRE/NXT·알테오젠 PRE/NXT·주성 AFTER/SOR에만 남았다. 따라서 이번 표본을 삼성·정규장의 새 효과로 확장하지 않는다.

정답을 읽지 않고 PRE 기존20/확장20, AFTER 기존5/확장5로50점을 고정했다. 각 층에서 scope 순환·고정 hash·미사용 원천 구간 우선 순서로 뽑았으며8scope·26개5분 원천 구간이다. 모든 원천 구간은 과거 연구에 관찰됐으므로 새 독립 구간/미래 holdout이라고 부르지 않는다. 같은 최종 정답에 맞춰 문구·범위를 재선정하지 않는다.

연구 protocol SHA256은 `67952298afb4125f3a6e2474b250712fd89ea0ec87e4324b441cea3c9d92e475`다. 확인 ask·비용0.0023 한 번·1,800초·net+0.4%·net soft−3% 선도달 없음의 WIN/FAIL_STOP/FAIL_TIMEOUT만 비교하고 미확정은 실패로 바꾸지 않는다. 동일 공통 유효 집합의 PASS 승률 우선, 동률이면 TP이며 EV·최소 표본·승리 보존율 문턱은 추가하지 않는다.

누적 차감1,897/2,000회를 유지하고 이번 최대100회(50쌍), 잔여3회는 자동 재시도에 사용하지 않는 범위를 고정했다. 무조작·동일 요청은 기존 원장을 재사용하고 새 불명확 전송은 자동 재시도하지 않는다. 원장 DB 복제나 기존 응답·실패·차감 초기화는 하지 않는다.

근거: [호출 전 동결 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/protocol.json), [전체 과거 시도 목록](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/attempt-inventory.json), [동일 입력 검증·캠페인](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/campaigns.json).

## 3. 운영 입력 구현과 코드리뷰

새 입력 owner는 기존 scalping 패키지의 `reversal_auxiliary_production_input.py`다. 동결 연구 변환 SHA `822be246c6aa0f165e78d8fa5f4ad9b8af423f357901752036656bd2395fea5f`를 검증하여 같은 실제 관측을 변환한다. 외부 정보·미래 가격·가공 정답은 추가하지 않는다. 기존 union input/validator와 compact wire 파일은 수정하지 않았고 `signals` 및 기계 판정 hash를 유지한다.

기존 registry에는 새 입력이 적용되지 않는다. 별도 registry의 `production_input_contract`가 정확 scope 목록·구현 hash·원 변환 hash를 명시하며 부모 compact registry와 원 연구 registry를 모두 검증한다. raw→projection→wire→SDK→decode 및 provider identity에 해당 계약을 전달한다. 누락·변조·범위 불일치는 fail closed다. 연구 승인 flags는 운영 활성화 권한으로 전달하지 않으며 활성화 owner는 기존 native policy/overlay publisher다.

양쪽 동일 입력의 연구를 위해 `risk_role_roles=['current','candidate']`를 명시적으로 지원했다. 기존 configuration은 candidate-only로 유지한다. 역할 목록은 configuration/membership에 들어가고 같은 유효 요청의 cache identity를 불필요하게 바꾸지 않는다. null·빈값·중복·역순·계약 없는 역할 목록을 거절하며, 평가 결과에도 양쪽 적용을 기록한다. offline input 비교의 native 발행 차단은 유지한다.

준비 검토에서 compact wire suffix 뒤에 연구 문구를 붙여 비교하던 driver 결함을 수정했다. 실제 요청의 wire suffix를 분리해 원 prompt+단일 suffix 관계를 검증하며,50쌍 모두 입력·schema·모델·옵션 일치를 확인했다. 코드 self review와 독립 리뷰를 닫고, 격리 소스 커밋 `ee0af6b48`에7개 파일을 기록했다. 주 작업본의 동시 변경은 통합하거나 덮지 않았다.

검증: 양쪽 RVP 연구40PASS, 운영 입력33PASS, 기존 wire/transition/tuning82PASS로 서로 다른155개를 통과했다. 실제 provider 호출과 SDK mock 테스트 수를 합산하지 않는다. compile·diff 검사도 통과했다. Kiwoom 요청·인증·주문·수량·hard safety·기계 BLOCK/RECHECK 판정은 변경하지 않았다.

## 4. 실제 결과와 정책 인계 상태

50쌍 모두 공통 유효이며 실제 새 provider 응답100개·미확정0개·기존 cache 응답0개다. 이번 지표의 대조군은 **RVP 입력+기존 prompt**다. raw 현행 입력의 이전 연구와 분모·효과를 합치지 않았다.

| 범위 | 확인점 | RVP+기존 prompt | RVP+새 suffix | TP/FP 변화 |
|---|---:|---:|---:|---|
| 전체 | 50 | 29/40승 = 72.50% | 32/44승 = 72.73% | TP+3·FP+1 |
| 비삼성 PRE | 40 | 25/31승 = 80.65% | 29/35승 = 82.86% | TP+4·FP불변 |
| 비삼성 AFTER | 10 | 4/9승 = 44.44% | 3/9승 = 33.33% | TP−1·FP+1 |

전체 confusion은 대조TP29/FP11/FN9/TN1, 후보TP32/FP12/FN6/TN0이다. PRE는 승리7점 회복·3점 상실이고, 실패6점(STOP3·TIMEOUT3)은 양쪽 모두 PASS였다. PRE 기존 패턴20점은14/20승으로 판정 전부 동일했고 확장 패턴20점의 승리 PASS가11→15점 늘었다. 따라서 새 문구는 승리 오차단을 일부 줄였지만 실패 차단 효과는 확인되지 않았다. 전체 실패12점 중 후보는12점 모두 PASS했다. 기계만의 진단은38/50승(76%), PRE34/40승(85%)이며 별도 채택 문턱·자동 AI 우회 권한으로 사용하지 않는다.

| 정확 PRE 경로 | 확인점 | 기존 prompt | 새 suffix | 준비 상태 |
|---|---:|---:|---:|---|
| 두산034020·2만~10만원·NXT | 10 | 5/5승 | 8/8승 | 승률 동률·TP+3 후보 정의 준비 |
| 알테오젠196170·10만원 이상·NXT | 10 | 6/6승 | 7/7승 | 승률 동률·TP+1 후보 정의 준비 |

위 두 경로의 평가10점씩은 **모두 WIN**이며 합계20점이2개5분 원천 구간·6개 승리 목표 시각에 집중됐다. 실패 분리나 넓은 시장 검증으로 표현하지 않는다.50점 전체는26개 구간·23개 승리 목표 시각·3개 STOP 시각이다. 정확 native/input/요청 identity가 고유하다는 사실이 독립 사건50개를 입증하지 않는다. 이는 새로운 최소 표본 채택 문턱을 추가한다는 뜻은 아니다.

AFTER의 주성036930/SOR는2/5승→1/4승, 알테오젠196170/SOR는0/2승→0/3승으로 악화했고 두산034020/SOR는2/2승으로 같았다. 새 suffix를 AFTER로 승계하지 않는다. PRE의 나머지3경로도 전부 같은 판정이므로 새 suffix의 범위 확대 근거로 사용하지 않는다. 삼성·REGULAR는 이번 효과 표본이 없다.

누적 차감은1,997/2,000회·잔여3회다. 과거 실패18개와 승인 체인을 보존했고 새 예산 초기화·자동 증액은 없다. 신규100응답의 토큰 합계256,092개, 지연 중앙1,022ms·p95 1,400ms·최대1,703ms다. 고유 원장 참조355개 object의 압축 구간875,191B·논리2,272,361B를 대사했다. 접촉 공유 pack109개 전체18,411,436B는 배타적 신규 증가량이 아니다.

독립 결과: [동일 입력 프롬프트 비교](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/independent-analysis.json), SHA `1b716f050ee4a8d84b24bc7e39de763db7dae65f0ecace600a95e60d709fd5e5`. 실제 원 응답·요청·source/outcome·모든 과거 시도 제외·표집 재현·예산·저장량을 독립 재리뷰했고 검토 범위의 미해결 결함은 없다.

## 5. 호환성·정책 인계 준비와 남은 운영 경계

직전 screen25/final150의175점에서 원 raw 현행 요청 bytes와 저장 RVP 연구 요청 bytes를 재생산했다. 운영 opt-in은 같은 논리 입력·provider wire·schema·prompt·모델 옵션과 저장된 실제 응답 decode를 재현했다. signals·snapshot·원 registry 파일은 불변이고 실제128bindings·기존9개 registry가 유효하다. 삼성·AFTER를 포함한175점의 대사는 호환성 증빙이며 적용 범위 확장이 아니다. [실증 결과](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/production-parity.json), SHA `e62b515b5cf955edf8a2c94aa24026a66fcdfae3dc388c54ff85c2e2ff7d6a8c`.

새50점에서도 production 입력·wire·schema·prompt·옵션과 실제 응답 decode가 연구 후보와 일치했다. 연구·운영 identity의 계약 메타데이터를 같다고 위장하지 않았고 정확한 provider 의미만 대사했다. 두 PRE 경로의 새 운영 registry2개는 report 아래 `prepared-registries`에만 저장했다. 운영 registry 등록·binding/overlay/current/pending 선택은 실행하지 않았다. [준비 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/adoption-preparation.json), SHA `d14581b5d1848782b53634ee340affb8da4bbedda28a57e7bf1136d394780bbd`.

새 G reader 코드 때문에 기존 reader hash 인계도 별도로 검증했다. canonical parent `8809c82e…`와 원 capture의 기준일10/16, 원 overlay `8185f257…`를 유지하고 옛 reader5개를 정확 Git bytes로 복구했다. 활성 data에 쓰지 않는 임시 data_root에서 source·overlay·registry23개를 개별 참조하여 compatibility 영수증2개를 발행·검증했고, old/new reader와 캡처의128bindings가 모두 같았다. native auxiliary reader readiness도 pass였다. [격리 검증](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/reader-handoff-isolation.json), SHA `b2d370c45a899205d38619487130ab6f086168f89ae7eb782a1171eb1733fc24`. 이 검증은 **10/16 역사적 incumbent reader의 호환 준비**이며 다음 영업일의 전체 native bootstrap/PREOPEN·정책 채택·실제 PID 소비를 입증하지 않는다.

격리 영수증의 내부 절대 경로는 원 `tmp/auxiliary-runtime-input-followup-20261017/handoff-staging`을 가리킨다. 원 작은 staging tree를 보존하고 symlink를 역참조하지 않은30,888B archive와 [보존 명세](../../data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/runtime-input-followup-20261017/reader-handoff-custody.json)를 남겼다. report의 사본을 실제 compatibility 디렉터리에 그대로 옮겨 운영 인계로 사용하지 않는다.

준비 helper 리뷰에서 analysis/manifest/protocol의 연결과 정확50개 membership 대사 guard를 보강하고 재실행해 같은 산출물 hash를 확인했다. 소스·연구 driver·호출 정의는 변경하지 않았다. code/실제 연구/호환 준비/문서 리뷰를 분리해 종료했다.

이번 후속50점은 RVP→RVP+suffix 효과이고 이전175점은 raw 현행→RVP 효과다. 두 비교의 개선을 합쳐 새 combined 입력의 raw 현행 대비 동일 확인점 효과로 주장하지 않는다. 배포 단계의 기존 native publisher는 정확 대상일·최신 실제 부모·비교/원천 계약과 candidate code handoff를 검증해야 한다. 준비된2개 정의와 이 연구 결과는 그 발행을 대신하는 권한이 아니다. 별도 최소 표본·EV 문턱을 추가하지 않는다.

선택 릴리스는 확인 시점 `nonfixed-quote-20261017-a41ebc84f`, `actual_pid_consumed=false`였으며 이번 작업은 이를 바꾸지 않았다. 배포·재기동·장후 재생성·자연 주문·보유 성과 검증은 실행하지 않았다. 다음 실패 차단 연구는 짧은 가격 반복이나 마지막 작은 BUY를 단독 문턱으로 삼지 않고, 실제 제공된 원천에서 승리와 실패를 가르는 근거가 있는지를 먼저 확인해야 한다. 이번100회 실험을 완료한 상태이며 잔여 예산 소진을 위해 표본이나 문구를 추가 선택하지 않는다.
