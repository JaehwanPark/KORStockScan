# 수량 연구 비용 생산자·소비자 보완 검토 — 2026-10-17

## 1 결정과 범위

사용자 확정은 **키움 확정 총비용을 매수·매도 거래대금에 따라 배분해 수량 연구에 사용하며 거래별 API 확정 비용과 구분**하는 것이다. 구현은 선택 `c4467c424`에서 격리했고, 배포 직전 새 선택 `3abcc524c`의 지연 연구 수리를 함께 보존한다. 실행 owner는 당일 체크리스트의 `InitialQuantityBrokerCostClosure1017`, 계약은 [비용 보완계획 §8](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#8-2026-10-17-비용-생산자소비자-보완-계약)이다.

이 기록의 연구 비용은 `broker_confirmed_total_allocated`, `actual_execution_cost=false`, `economics_scope=initial_quantity_research_only`다. canonical 실제 수수료·손익·profit_rate·strict 상태를 배분값으로 바꾸지 않는다. 기존 최초 정책에 새 경제성/자연소비 선행 허들을 추가하지 않는다.

## 2 구현과 리뷰에서 수정한 결함

| 경로 | 수정·확인 |
| --- | --- |
| 키움 원천 | 기존 계좌·날짜·연속조회 계약을 보존한다. 주문행 수수료 합계를 최종 비용으로 단정하지 않는다. 과거 날짜에 날짜 없는 주문 endpoint를 재호출하지 않으며 정정 전 bytes는 불변 세대에 남긴다. |
| 배분 생산자 | 날짜·종목별 BUY+SELL 거래대금 분모, 정수 원화 최대 나머지 배분, 미청산 거래 및 Main 미확인 거래 몫 보존을 구현했다. 계좌·소유권·수량/금액·체결 순서·완료시각을 검증한다. |
| 체결/소유권 | 원 identity·원 시각·payload가 같은 SELL 재관측만 통합한다. reserve→bound 정상 registry 진행을 허용하고 검증된 이전 BUY ledger와 bounded registry를 연구 전용으로 연결한다. 충돌·수동 소유권·stale 정리만 있는 체결은 제외한다. |
| 원천 전달 | postclose snapshot writer만 영수증/index를 기록한다. 불변 비용 영수증·의존 날짜 SHA·원 fact 참조가·체결 장부 평균가를 구분해 bounded fact→완료 overlay→수량/분할/timeout 연구까지 전달한다. |
| 세대/정정 | source lock 아래 원천 SHA를 재확인하고 불변 영수증을 가리키는 index를 원자적으로 발행한다. 해당 거래/날짜만 compact 증명으로 연결한다. 비용 변경은 경제성만 다시 계산하고 실행 후행자료 cache를 재사용한다. |
| 평가 | 승인된 연구 비용으로 익절 가중 후보를 만들고 손실을 포함한 전체 거래의 비용 후 EV·순이익으로 최종 선정한다. 비용을 holdout 이후 얻은 거래는 학습에서 제거한다. 새 배분 자료를 구 v2 평가로 우회하지 않는다. |
| 정산 대기 | 기존 장후 비용 단계의 `--drain-pending`으로 TARGET 우선+과거 최대1일을 처리한다. 수집 성공과 소비 확인을 구분하고 소비자가 검증·저장한 뒤 ack한다. 150초 요청 사이 예산·180초 기존 process timeout·매일 durable claim·기간 밖 explicit expired를 보존한다. |
| 성능 | 전체 비용 세대를 매 거래에 복제하던 제곱 증가를 제거했다. 공통 전체 증명은 한 번 저장하고 각 거래는 자기 증명만 가진다. 후행 raw decode를 비용 정정 때문에 반복하지 않는다. |

기본 보고서는 읽기 전용이며 운영 비용/index를 배포 준비 목적으로 만들지 않는다. canonical 자동 custody·실주문·provider·cap·hard safety 권한은 바꾸지 않는다. 모듈은 기존 lifecycle/scalping 역할 패키지에 배치했다.

공식 참조: `Kiwoom-Securities/Kiwoom-REST-API` commit `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회 `2026-10-17T13:31:06.770579Z`. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/core/errors.py`, `_data/kiwoom_api_spec.json`, Postman의 ka00001/ka10170/ka10076/kt00015를 확인했다. 해당 revision에는 `kiwoom_docs`가 없었다. 요청/응답 field를 새로 추정하지 않았으며 실제 계좌/API 호출은 하지 않았다.

## 3 봉인 실제 자료의 원가 admission

실제 10/16 완료 9건+미청산 3건 범위다. 앞선 fact16/완료13/보유3 전체 역사 모수와 혼동하지 않는다.

| 항목 | 결과 |
| --- | ---: |
| 완료 거래 | 9 |
| 배분 생산→durable 영수증→수량 소비자 비용 admission | 8 |
| strict exact 비용 적격 | 0 |
| 제외 | 49294: 같은 SELL의 원형 재관측 증명 불충분 |
| 미청산 | 49344·49346·49350: 확인 BUY 비용 몫만 유지, terminal 미생성 |
| 관측 8개 날짜·종목 묶음 총비용 | 6,256원 |
| 확인 거래 배분+별도 잔여 | 4,843원+1,413원=6,256원 |
| 완료 8건 배분비용 | 4,065원 |
| 미청산 3건 비용 몫 | 778원 |
| 완료 8건 연구 손익 | 19,535원, 익절7·손실1 |

이 수치는 배분 연구값이며 거래별 정확 정산 손익이나 이번 수리로 새로 발생한 수익이 아니다. 손실1건도 최종 전체 거래 평가 모수에 남는다. 실제 native current-day handoff+전일/residual custody 경로도 같은 8/1/3 결과였다. 정확 비용 부재를 NULL로 보존하며 미확인 몫을 적격 거래에 전가하지 않았다. 독립 Decimal 정수 배분 재계산과 합계가 일치했다.

기존 봉인 sidecar `261,811,118B`를 SHA 확인하며 한 번 bounded stream 읽는 데 32.287초가 걸렸다. 추출 후 생산자+소비자 검증 0.599초는 이 intake 시간을 제외한다. 원 2GB snapshot·pipeline raw 재생·운영 보고서 재생성은 없었다. 여기서 실제 자료 full candidate grid나 정책 발행을 실행한 것은 아니다.

증거 디렉터리: `/home/ubuntu/KORStockScan-worktrees/quantity-broker-cost-closure-20261017/tmp/quantity-broker-cost-actual-20261017/`. 최종 `real-cost-acceptance-final.json` SHA `b95461642d6f85e715a83f4c881009ff63bcec49c55206bfe2542b340ab79f86`, native handoff 별도 `actual-native-handoff-cost-admission.json`. 앞선 실패 증거도 보존한다.

## 4 성능과 결과 검증

비어 있지 않은 동일 fixture의 비용 생산→수량→분할/timeout 결합 재생을 네트워크 차단 독립 process 3회씩 측정했다. 새로운 경로 자체의 cold/warm·증분 비교이며 과거 0건 처리 시간 대비 개선 주장으로 사용하지 않는다.

| 경로 | 중앙 wall | 적격 거래 | 결합 outcome | raw decode | 실행 case 재계산 |
| --- | ---: | ---: | ---: | ---: | ---: |
| cold 3일 | 5.326초 | 60 | 14,400 | 231,000B | 28,800 |
| warm | 2.134초 | 60 | 14,400 | 0B | 0 |
| 과거 비용만 정정 | 2.044초 | 60 | 14,400 | 0B | 0 |
| 하루 추가 | 3.567초 | 80 | 19,200 | 새 날짜 77,000B | 9,600 |

비용 정정은 영향 20건 영수증만 바꾸며 이전 증명은 거부한다. 실행 outcome hash는 보존된다. source gap 2,880/14,400은 그대로 남기며 전부 지원 체결이라고 부르지 않는다. 최대 managed budget `17,822,208/67,108,864B`; 최대 process RSS `153,852KiB`는 별도 지표다. 모두 v3 `carry_parent`, 강제 경제 승격은 없다. 재현 도구·source/test/tool SHA·3회 결과는 격리 작업본 `tmp/quantity-cost-benchmark-20261017/final-self-contained-chain/`에 보존한다.

별도 1,000포지션 3회 규모 검증에서 모두 1,000건 admission·총비용1,000원 보존·fixture 연구손익39,000원으로 일치했다. 전체 세대 반복 복제로 276,225,854B까지 커져 64MiB admission에 실패하던 입력이 공통 증명+거래별 참조로 4,899,640B가 됐다. managed budget `37,517,120/67,108,864B`, process RSS 최대53,816KiB다. 중앙값은 배분0.106초·내구 저장6.700초·source generation0.123초·census0.298초이며 저장은 fsync를 포함한다. 증거는 같은 디렉터리 `final-scale/summary.json`이다. 이 자료는 작은 synthetic raw와 별도 규모 fixture이므로 전체 운영 raw throughput을 보증하지 않는다.

## 5 리뷰 게이트와 배포 인계

분담 구현 후 생산자/소비자·권한·비용/시간·크기·경합 교차 리뷰와 수정·재리뷰를 반복했다. 통합 표적 회귀 729 PASS/72.09초, 기존 code handoff 표적 422 PASS를 확인했다. 마지막 다일 receipt의 producer/reader 필드 크기 불일치도 수정했다. 14일·8포지션 fixture를 같은 배분 생산자로 계산한 17,532바이트 영수증은 두 원문 reader에서 보존하고 256KiB 초과는 명시 거부하는 161개 영향 회귀가 통과했다. 전체 보고서·일반 scalar 한도는 그대로다. 성능 증거의 고정 hash는 이 마지막 원문 fallback 필드 한도 수정 전이며 측정 경로는 native fact projection을 사용한다. 원래 측정 hash를 사후 변경하지 않는다. 이후 누적 후보 최종 검증·배포 영수증을 아래에 기록한다. Python compile·shell `bash -n`·diff·로컬 링크·print-only parser를 완료 조건으로 유지한다.

배포는 새 선택 `3abcc524c`를 누적 보존한 clean 후보의 정확 source쌍·fresh holding capability fixture·원 정책/128범위 native parity·기존 두 PRE overlay·숫자 불변·next-session `current_full_contract`를 확인한 뒤 selector를 마지막에 CAS 발행한다. 원 7f2552 정책 origin과 원 영수증은 보존하며 포괄적 호환 예외를 만들지 않는다.

기동·실제 PID·자연 생산/ack·새 경제성은 선택 배포와 다른 증거다. 이번 수리는 49294의 원형 증거 및 더 오래된 날짜의 미해결 정산을 복구 완료로 꾸미지 않는다. 해당 원천/경제성은 기존 `InitialQuantityProducerConsumerRepair1010`, 실제 10/19 PREOPEN/PID는 `DirectFamilyPreopenPolicyHandoff`가 계속 소유한다.

누적 후보 검증: `3abcc524c`와 수량 비용 수리를 통합한 뒤 비용/보고서/수량/timeout/지연 계약 회귀 **781 PASS/69.80초**, 영향 Python35개 compile·장후 wrapper `bash -n`·diff 검사를 통과했다. 최종 전략 원문 reader SHA는 `00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4`, 비용 세대 reader는 `db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5`다. 두 source의 원 7f2552 origin 직접 인계를 결속하고 holding capability는 `6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137`로 재검증한다. 기존 지연 연구의 인계쌍과 변경하지 않은 가족은 보존한다.

## 6 다음 정규 기동용 배포

- 선택 커밋: `e12256decc5bb61e560462520ec7cd9965b0f7b2`, release `/home/ubuntu/KORStockScan-runtime-releases/quantity-broker-cost-20261017-e12256dec`. 부모는 이번 수리 `86543ad2b`와 직전 선택 `3abcc524c`다. canonical의 무관한 dirty 소스는 통합하지 않았다.
- 발행: **2026-10-17 23:21:25 KST**, 실제 selector·39파일 발행 뒤 **23:23:09 KST `deployed_and_policy_verified`**. native release/detector/selector/stage/publisher lock·source CAS·selector 마지막 발행·실패 rollback 경계를 사용했다. 원 준비/실패/이전 영수증을 보존했다.
- 추가 검증: 정확 코드 인계 547 PASS와 지연 계약 66 PASS, 네트워크 차단 새 holding fixture116 PASS. 나머지 세 가족은 기존의 정확 세대 fixture를 검증했다. native 128범위·76,800행·598신호는 원 코드와 신호 hash가 같았다.
- 정식 격리 summary는 새로 계산해 성공했고 controller는 `done`, blocked reason0이다. 최종 준비본과 **실제 발행 직후 `current_full_contract` PASS/findings0**를 확인했다.
- 미래 bundle `da16f85fc5da9e602035029ba0255be057ea6094c684dda78e7655f1b8d02155`, overlay `a2b35e7d79e2db8b06daa98a92eb5a2b94066618155eb1be3e3096b275031125`. 원 env/수치 정책 영수증4개·128개 binding·승인된 두 PRE 변경·rollback·기존 10/19 OPEN6개가 같다. 현재 Main/보조/수량 포인터는 보존했다.
- 발행 목록39개·39,168,295B의 source SHA/대상 이전 SHA를 독립 대조했다. 계획 SHA `fadfd911c8b115674152dc702731330802d15afc579bdeabeb29a99db1d70a88`. 비용 원천·pending·연구 index·actual 비용·fact 발행 대상은 0개다. 보호 비용/fact inventory의 작은 bytes만 검증하고 대형 원문4개는 stat 및 기존 native 증명을 유지했다.
- Main 강제 기동·재시작·실제 provider/API·주문은 수행하지 않았다. `actual_pid_consumed=false`; **10/19 07:35 PREOPEN→07:55 Main**의 실제 소비와 이후 정규 장후 비용 생산/소비 ack는 기존 자연 수용 owner에서 확인한다. 경제성 갱신 적격이 생기기 전에는 현재 수량/분할/timeout 정책값을 유지한다.

배포/검증 증거: `/home/ubuntu/KORStockScan/data/report/initial_quantity_broker_cost_deployment/2026-10-17/attempts/reviewed-v1/`. `deployment.json`, `published-native-verification.json`, `host-after-private.json`, `publication-plan.json`과 보존된 원본/rollback bytes가 소유한다. `validation/manifest.json`에는 실제8/9 admission·마지막781회귀·성능3회·공식 참조의 compact 원 증거23개와 SHA를 복사해 보존했다. 실제 거래의 full grid 정책 재선정이나 정확 정산 완료를 배포 근거로 꾸미지 않았다.

## 7 마지막 감시 소비자 후속 결함과 보완

e122의 사후 읽기 전용 `postpublication-verification.json`도 PASS(strict/controller issues0, current full·release/cron/PREOPEN/start 경로 보존)였다. 그 뒤 새 배분 자료를 감시 소비자에 대입하는 추가 리뷰에서 다음 두 결함을 확인해 같은 `InitialQuantityBrokerCostClosure1017`을 재개했다. 원 e122 배포/검증 bytes는 그대로 보존하며, 운영에 아직 없는 새 배분 자료를 소비하지 않은 과거 PASS를 그 경로의 검증으로 간주하지 않는다.

1. 감시기가 compact `completion_generation`/`fact_generation`을 전체 native 증명과 직접 비교해 정상 overlay를 `quantity_completion_overlay_row_binding_invalid`로 거부했다. 원 terminal과 연구 영수증의 직접 일치도 검사해야 한다.
2. stage 생산자는 전체 보고서를 stream으로 쓰지만 감시 child reader는 4MiB다. 새 1,000건 적격 fact만 4,899,640B이므로 합법적인 비어 있지 않은 결과가 크기 때문에 거부된다. 원 보고서의 한도 확대 대신 생산자 소유의 bounded native 검증 요약/영수증을 마지막 감시까지 연결해야 한다.

고치는 범위는 compact 참조/영수증 검증, 감시용 요약 생산·소비·원본/source/code 결속, 구 stage 호환 및 표적 회귀/성능이다. canonical 실제 비용이나 정책값 변경은 포함하지 않는다. 후속 불변 후보의 리뷰·검증·재배포 및 마지막 소비자 결과를 이 절에 이어 기록한다.

3. 실제 native 생산 경로의 1,000건 재생에서 상태 metadata의 소비 한도128KiB가 native512KiB와 달라 정상140KiB 영수증을 거부했다. native 소유 상수로 일치시켰다. 이어 census 재검증에서 여러 날짜의 decoded metadata를 누적해 기존64MiB 공통 예산을 초과하는 결함을 확인했다. 1,000개 비용 영수증을 그대로 유지하고 일자별 검증 메모리를 해제하는 보완·재검증을 진행한다. 앞선 실패 로그를 보존하며 아직 성능 PASS로 표시하지 않는다.


### 7.1 후속 검증 범위와 원 실패 보존

- 수량·분할·timeout·projection 표적8개 모듈 **613 PASS/40.42초**, 별도 영향 수량/감시289 PASS/32.59초 및 projection19 PASS를 확인했다. 테스트 수는 겹칠 수 있어 합산하지 않는다. 마지막 ancestry 역할 보완 후 그 경로를 다시 검증한다.
- 더 넓은 탐색 검증은 **853 PASS/3 FAIL**에서 중단하고 실패 원인을 분리했다. 정확 e122 부모를 새 격리 worktree에 고정한 동일3개 검증에서도 **3 FAIL/21.92초**로 재현됐다. `test_snapshot_archive`의 해당 fixture는 native archive receipt 없이 임의 gzip 후 원본을 지워 `valid_empty`를 기대하고, entry sizing의 두 fixture는 기록되지 않은 `reversal_cumulative_data.json` 읽기를 요구한다. 이번 diff가 만든 회귀로 표시하지 않으며 source-gap/미기록 입력 guard를 완화해 PASS를 만들지 않는다. 원 실패와 부모 재현 로그를 보존하고 전체 코드베이스 테스트 PASS로 보고하지 않는다.
- 실제 native 생산 경로의 큰 fixture는 1,000개 배분 영수증/총비용1,000원을 보존하고 **1,000=초기 적격1+추가매수999 제외**를 대사했다. report/timeout은 각각 약10MiB이고 bounded projection은 약172KiB다. full native validator·공통 원천 의미 관측·마지막 감시 결과가 같고, warm에서는 큰 두 child를 열지 않는다. 이 시험은 1,000건 모수/제외/감시 처리 시험이며 1,000건 전부의 경제성 grid throughput은 아니다. 별도60건×240 grid 측정과 구분한다.
- 초기 fixture가 생산자 단계의 마지막 `frozen` decoded 문서를 소비자 단계까지 보관해 예산을 중복 점유한 실패도 구분했다. 원천/영수증 필드는 삭제하지 않고 실제 별도 worker의 수명을 반영해 생산자 임시 객체만 해제했다. 생산 코드의 날짜별 해제·동일 행/claim 재사용 보완은 유지한다. 정량 최종 성능/소스 SHA는 다음 절의 새 독립 결과에 고정한다.
- 이미 승인된 과거 정책의 ancestry와 현재 일일 stage 감시에 같은 live-source 검사를 적용하면 비용 정정 뒤 기존 정책이 무효로 보이는 후속 결함도 보완한다. 과거 발행 증명/선언 child/정책 연결은 유지하고 현재 원천·비용·코드의 최신 검사는 당일 stage가 맡는다. 최초 정책에 자연소비·우월성 요건을 추가하지 않는다.
- KST 자정 이후 같은 작업 ID를10/18 실행 문서로 이관했다. source10/16·publication10/18·target10/19와 원10/19 OPEN6개는 유지한다.

후행 가격의 마지막 소비도 보완했다. `initial_quantity_following_bars`가 canonical `realized_pnl_krw=None`을 연구 거래의 배분 net과 비교해 `fact_identity_missing`으로 누락시키던 경로를 수정했다. 연구 비용 세대/영수증·basis/금액/시각을 검증하고 검증 원장의 거래대금/수량으로 진입 가격 기준을 계산한다. 결과의 가중치에도 `actual_execution_cost=false`와 연구 영수증 SHA를 전달한다. 기존 API 확정 비용 경로·ka10080 요청/파서·route/요청 예산은 변경하지 않았고 실제 provider 호출은0이다. 새 승인/위조 반례7개와 genuine public 초기 seed/기본정책 선택을 포함한 표적10개가 통과했다.


### 7.2 최종 후속 코드 검증

- 마지막 역할/후행 가격 보완을 포함한 표적8모듈 **622 PASS/41.31초**, 별도 의미 감시 **100 PASS/5.54초(303 deselected)**. 영향 Python8개 compile·장후 wrapper bash 문법·diff·print-only parser·로컬 링크 검사를 통과했다. 원천/비용/행 참조·권한·claim 수명·현재/과거 역할·후행 연구 비용을 독립 리뷰 후 수정·재리뷰하여 이 범위의 미해결 결함0이다. 앞선 탐색3FAIL은 부모 재현 근거와 함께 보존한다.
- 마지막 변경이 모두 고정된 뒤 CPU 경합 없이 실제 native1000 경로를 다시 측정했다. source/tool SHA와 전후 동일성은 `large-semantic-native-uncontended-result.json`이 소유한다(SHA `d630b6c164e015ec077a2f2ba844515abaa9a922dd866283a0d61f031a033a3c`). provider/운영 발행0, 원형 실패와 이전 성공 결과는 별도 보존한다.

| 지표 | 최종 결과 |
| --- | ---: |
| 원형 비용 영수증 / 비용 보존 | 1,000건 / 1,000원 |
| 모수 / 초기 적격 / 추가매수 제외 | 1,000 / 1 / 999 |
| 전체 report / timeout | 10,046,468 / 10,431,556B |
| native 검증 후 감시 projection | 174,633B |
| cold 생산·전체 검증 | 16.3709초 |
| warm 전체 감시 3회 | 45.107 / 44.355 / 44.455ms |
| warm 대형 두 child read | 0 |
| warm metadata read 3회 합계 | 547,980B |
| managed peak / 기존 한도 | 64,482,680 / 67,108,864B |
| 종료 후 managed 잔여 | 0B |
| process peak RSS | 237,856KiB |

canonical 실제 손익은 NULL을 유지하며 적격1건의 연구 손익은 fixture39원이다. 이 값을 실제 추가 수익으로 사용하지 않는다. 64MiB는 관리 대상 resident admission이며 process RSS 전체의 상한으로 부르지 않는다. native 상태171KiB/일과 scalar 약1.14MiB/일의 합법적 입력을 날짜별로 검증한다. 네 capability의 code generation은 e122와 같으므로 기존 정확 세대 fixture를 native 명령으로 재검증한다. 후속 릴리스 준비/발행 결과는 아래에 별도 기록한다.


## 8 후속 릴리스 실제 배포 완료 (2026-10-18)

- 선택 source commit **`900234d791b0bf31797cd4e823d0ae40296f790b`**, release `/home/ubuntu/KORStockScan-runtime-releases/quantity-broker-cost-monitor-20261018-900234d79`. 부모 e122와 그 이전3abcc 지연 수리를 누적 보존했다. 원 작업공간의 동시 source 변경은 덮어쓰지 않았다.
- 독립 재리뷰 후 helper12개/후보를 봉인하고 원본17 source 및 비용/fact inventory를 새로 고정했다. 네트워크/host write를 차단한14 CoW 격리에서 정확 코드 인계·native128범위/76,800행/598신호 mismatch0·네 기존 정확 세대 fixture가 통과했다. 새 summary는 `succeeded`, controller는 `done`/blocked0, 최종 준비본은 `current_full_contract PASS/findings0`이다.
- **00:17:34 KST selector 발행 → 00:19:16 KST `deployed_and_policy_verified`**. 실제 발행 후 native `current_full_contract PASS/findings0`를 확인했다. native lock/CAS·selector 마지막 발행·전체 실패 rollback 경계를 유지했다.
- 독립 대조한 발행34파일/39,147,740B, 계획 SHA `d3e62554fae7e9c32bd0ef4b637f0b72f3fb001209969c4212ea5d6505ea443d`. 모든 source/대상 이전 SHA를 재검사했다. 운영 비용 원천·pending·연구 index/history·actual 비용·fact 발행 대상0개이며 기존 현재 Main/보조/수량 포인터를 보존했다.
- 미래 bundle `ac6545f5ba6b8c18676600bdb6eda1578be5f8f92a4671156579e4b202248054`, overlay `fb961076e4b151cb48e7c4a23b5453c6d6d827caa95efd1eafd2505af4a7ba20`, transition `786e3b5a0eaadfee1771d7f7ff79028fbb6247bfb7b3f110e75ef677ad176afd`. 수치 env·정책 영수증4개·128 bindings·승인된 두 PRE 변경·rollback·10/19 기존 OPEN6개가 같다.
- 완료 범위는 수리 코드·생산자/마지막 소비자·자료/성능·선택 배포 및 다음 정규 기동용 정책 검증이다. 최초 정책에 우월성/자연소비 허들을 추가하지 않았다. 기존 정책 수치 변경·실제 provider/API 호출·주문·Main 강제 기동/재시작0이며 `actual_pid_consumed=false`다. **10/19 07:35 PREOPEN→07:55 Main**의 실제 소비는 `DirectFamilyPreopenPolicyHandoff`, 정규 장후의 새 비용 생산/ack·원형49294 결손·실제 경제성은 `InitialQuantityProducerConsumerRepair1010`가 계속 소유한다.

증거 owner는 `/home/ubuntu/KORStockScan/data/report/initial_quantity_broker_cost_deployment/2026-10-17/attempts/reviewed-v2/`다. `deployment.json`, `published-native-verification.json`, `publication-plan.json`, `host-after-private.json`과 `validation/manifest.json`이 실제 발행과 최종 검증을 구분한다. 마지막 읽기 전용 release/cron/PREOPEN/start·strict/controller·현재 full 검증 결과는 같은 곳의 `postpublication-verification.json`에 기록한다. 원 v1·실패·이전 성공 증거는 수정하지 않았다.

최종 읽기 전용 사후 검증도 **00:21:59 KST PASS**다. 실제900 선택을 기준으로 release-set/cron 및 PREOPEN/start print-plan, native current_full_contract(findings0), strict issues0, controller issues0, 기존128/두PRE/rollback·보호 원천/비용/fact와 Main 부재를 재확인했다. provider_calls/orders/runtime_restarted=0이며 실제 PID 소비는false다. 이번 코드/자료/선택 배포 owner는 종료하고 자연 수용 owner만 기존10/19 일정에 유지한다.
