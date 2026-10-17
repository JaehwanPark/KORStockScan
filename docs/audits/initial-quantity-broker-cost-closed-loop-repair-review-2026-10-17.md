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

분담 구현 후 생산자/소비자·권한·비용/시간·크기·경합 교차 리뷰와 수정·재리뷰를 반복했다. 통합 표적 회귀 729 PASS/72.09초, 기존 code handoff 표적 422 PASS를 확인했다. 마지막 다일 receipt의 producer/reader 필드 크기 불일치도 수정했다. 실제 14일·8포지션 배분으로 만든 16KiB 초과 영수증은 두 원문 reader에서 보존하고 256KiB 초과는 명시 거부하는 161개 영향 회귀가 통과했다. 전체 보고서·일반 scalar 한도는 그대로다. 성능 증거의 고정 hash는 이 마지막 원문 fallback 필드 한도 수정 전이며 측정 경로는 native fact projection을 사용한다. 원래 측정 hash를 사후 변경하지 않는다. 이후 누적 후보 최종 검증·배포 영수증을 아래에 기록한다. Python compile·shell `bash -n`·diff·로컬 링크·print-only parser를 완료 조건으로 유지한다.

배포는 새 선택 `3abcc524c`를 누적 보존한 clean 후보의 정확 source쌍·fresh holding capability fixture·원 정책/128범위 native parity·기존 두 PRE overlay·숫자 불변·next-session `current_full_contract`를 확인한 뒤 selector를 마지막에 CAS 발행한다. 원 7f2552 정책 origin과 원 영수증은 보존하며 포괄적 호환 예외를 만들지 않는다.

기동·실제 PID·자연 생산/ack·새 경제성은 선택 배포와 다른 증거다. 이번 수리는 49294의 원형 증거 및 더 오래된 날짜의 미해결 정산을 복구 완료로 꾸미지 않는다. 해당 원천/경제성은 기존 `InitialQuantityProducerConsumerRepair1010`, 실제 10/19 PREOPEN/PID는 `DirectFamilyPreopenPolicyHandoff`가 계속 소유한다.

누적 후보 검증: `3abcc524c`와 수량 비용 수리를 통합한 뒤 비용/보고서/수량/timeout/지연 계약 회귀 **781 PASS/69.80초**, 영향 Python35개 compile·장후 wrapper `bash -n`·diff 검사를 통과했다. 최종 전략 원문 reader SHA는 `00dc2d63df6ef91ff258507696efd3b348650f7b36db1ad6f789e9e3294d6bd4`, 비용 세대 reader는 `db9f1d2db58d6e766b9a18db22e643c4bdc748c8580d8b364cc36d6066b129d5`다. 두 source의 원 7f2552 origin 직접 인계를 결속하고 holding capability는 `6c4734c5e4204b36faf3d72ee873a429147d7a6e5a3a019d55fee29f4e145137`로 재검증한다. 기존 지연 연구의 인계쌍과 변경하지 않은 가족은 보존한다.
