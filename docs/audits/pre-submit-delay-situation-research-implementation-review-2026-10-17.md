# pre_submit_delay 상황 연구·단기 관측 구현 검토 — 2026-10-17

사용자 "다음액션을 진행하라"에 따라 [연구 계획](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md)의 후속 분석·연결 보완·단기 관측·의미감시를 구현했다. 원점은 선택 `c5aeda844dfab36146d04e6305cb29508cd47d4f`, 작업본은 `/home/ubuntu/KORStockScan-worktrees/pre-submit-delay-research-20261017`이다. 현재 KST 체크리스트의 목적·강제 규칙은 canonical 문서를 기준으로 확인했고, 다른 작업의 문서·코드·정책과 원 역사 bytes를 보존했다.

새 보고서 생산자는 기존 자동화/장후 생산자 package `src/engine/automation`에, 회귀는 기존 `src/tests`에 배치했다. `src/engine` root 신규 모듈은 없다. Kiwoom wire·요청/FID/REG/REMOVE·인증·주문 프로토콜 변경은 없다.

## 실제 원천 재분석

[연구 보고서](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-16/attempts/20261017-reviewed/report.json)의 원 generation은 `fb0dbdf369a8100c6b3fbee99e4cd5fe4650a10e986318335da6be1a59d75eb4`다. 원 publication/source date 10/16, effective date 10/19를 유지하고 10/17에 점검 보고서를 생성했다. 원 manifest/report/policy 바이트와 425개 compact의 generation을 전후 대조했다. compact 4,354,018바이트·1,735행을 한 번 decode했고, 287개 기준점을 모두 exact alias·decision hash로 연결했다.

| 기준점 | 기록 수 | P0 유효 | 유효 horizon 비교쌍 |
| --- | ---: | ---: | ---: |
| price_ready | 113 | 89 | 286 |
| signal_ready | 174 | 149 | 491 |
| 합계 | 287 | 238 | 777 |

282개 기준점의 native 신원이 확인됐고 anchor를 제외한 같은 machine/native/부모 신원으로 198개의 알려진 독립 기회에 연결됐다. 나머지 5개의 독립 신원이 미확정이므로 전체 독립 기회 수는 null이다. 777쌍과 parent/child 231개 cell은 독립 기회 수가 아니다.

실행 지원 `price_ready`의 99개 cell은 다음과 같다.

| 선정 이유 | cell 수 |
| --- | ---: |
| 학습에서 고른 후보의 검증 pair 없음 | 70 |
| 학습 pair 없음 | 4 |
| 학습 모집단 없음 | 3 |
| 학습·검증 평균이 모두 비양수 | 12 |
| 학습·검증 방향 불일치 | 8 |
| native/부모 연결 미확정 | 2 |

실행 지원 cell의 양수 지연은 0개다. `signal_ready`의 양수 2개는 같은 8개 기준점의 ALL/세부 유형 중복이며 60초, 학습5개 평균4.618bp·검증3개 평균7.862bp다. 실행 지원 anchor로 전환하거나 2개의 독립 근거로 세지 않았다. 0초 결과는 최적성 입증을 뜻하지 않는다.

P0 spread bp는 238개 기준점에 존재한다. 원 신호 기준가격·정확한 frozen tick·단기 1/3/5초·정확히 연결된 지연 후 재점검·비용 성과는 기존 원천에서 확인되지 않았다. spread bp의 고정 진단 구간만 분석했고, 원 신호 가격과 tick을 현재 값으로 복원하지 않았다. 실제·CF·호가 추정을 섞지 않으며 순EV/실현손익은 null이다.

## 구현과 반복 리뷰 보완

- 신규 1/3/5초는 버전·목표시각·실제 관측시각·0.25초 오차를 quote hash에 결속한다. 기존 0/30/60/120/180초 hash와 실행 후보는 유지한다. 3.2초 snapshot은 1초 late, 3초 조건부 유효, 5초 not_due다. 실제 offset 정밀도를 보존한다.
- 회차당 horizon 8개, 기존 active 128/종목16/상태8·공유 큐 예산을 유지한다. 남은 due는 재예약하고 같은 원천 snapshot을 공유한다. 신규 worker·구독·provider 호출을 만들지 않는다.
- 원 signal reference는 immutable native claim과 원 assessment의 scope generation·machine parent·event/signal·symbol/item·clock·confirmation price가 일치할 때만 기록한다. hash와 minimal projection에 보존한다. 보조 입력·응답·membership은 바꾸지 않는다.
- 실제로 인수한 successor 요청/완료를 원 intent에 연결하고 거절된 평가의 successor 필드와 기존 성공 resolved 필드를 구별한다. due를 영수증 없이 제거하던 경로와 pause/veto 등 조기 반환 뒤의 기한 초과 경로를 보완했다. 예외·전송 불확실·미만료 상태는 보존한다.
- 새 recheck stage를 raw/producer summary/compact registry·최소 필드 projection에 모두 연결했다. legacy 보고서가 recheck나 관측 전용 종료를 주문 terminal로 해석하던 가능성을 차단하고, terminal_reason이 있는 broker ack/불확실 응답의 분류 우선순위를 보완했다.
- 감시는 grid/ID/decision hash별로 예정 전·저장 유예·유효/무효/시각 초과·명시 중단·누락을 구분한다. 관측 종료는 실제 intent를 종결하지 않는다. 과거 `broker_accepted`·`submit_call_outcome` 영수증도 읽는다. 늦은 중단이 과거 결손을 지우지 않는다.
- 선정 검증에서 과거 projection의 64hex qualification generation을 유지했다. 현재 source byte/ledger 검증·cache 자격·코드 인계는 그대로 검증한다. 부모 fallback/명시적0·anchor 지원 범위를 보고서와 실제 loader 기준으로 대조했다.
- 독립 리뷰에서 source/shard의 크기를 확인하기 전에 전체 hash를 계산하던 읽기 증폭을 발견했다. 실제 크기 사전 확인·byte 한도·단일 bounded read/hash·전후 generation 대사와 출력512MiB/temp1GiB 한도를 추가했다. 커진 shard는 열기 전에 거부한다.

## 검증과 성능 범위

영향 회귀의 최종 결과와 파일/코드 증빙은 [검증 영수증](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-16/attempts/20261017-reviewed/validation.json)에 기록했다. 핵심193개·의미감시55개 pytest, Python compile, `git diff --check`, 추가/통합 로컬 링크18개·print-only parser23항목을 확인했다. 외부 동기화·provider·주문 호출은 없다.

실제 점검 보고서 생성은 wall1.331초·최대RSS40,160KiB·출력4,195,025바이트였다. [국소 관측 benchmark](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-16/attempts/20261017-reviewed/observer_benchmark.json)는 버전별1,200회 중 앞100회 제외·로그 mock·동일 synthetic snapshot 조건이다. 1개 due p95는 원18.843us/후18.896us, 기존5개 overdue p95는 원94.572us/후94.094us, 신규8개 p95는151.434us다. 실제 Main/provider/디스크 포함 지연과 자연250ms 관측률은 측정하지 않았으므로 운영 성능 수용으로 부르지 않는다.

## 정책·운영 경계와 다음 증거

이번 점검 보고서는 report-only이며 원 초기정책·pointer·선택 release·PREOPEN·PID를 변경하지 않는다. 기존 실행 지원 price_ready의 0초 baseline을 유지했다. 코드 완료와 자연 1/3/5초 수집, 실제 재점검/제출·체결·경제성은 별도 상태다. 다음 단계는 정식 코드 인계 후 같은 기회 ID의 단기 시각 정밀도·관측률·재점검 종결을 확인하고, 새 자연 자료로 후보 비교를 갱신하는 것이다. 기존 `DirectFamilyPreopenPolicyHandoff`가 실제 PREOPEN/PID 소비를 소유한다. 이번 구현이 과거 결손을 복원했다고 보고하지 않는다.

## 배포 전 코드 계약 검증

현재 적용 가능한 price_ready20개 cell은 모두0초다. 원 정책 생성본은 선택c5보다 앞선 `7f2552aedde8fec6ef904a43105827907e50dfc8`이며 원 계약 `bd5767c2…`와 정책 `9ebf3d04…`를 유지한다. 기존 inventory에 없던 parser/registry는 원 digest에 추가하지 않고 정확한 원점별 extension으로 결속했다. 변경7개 파일의 원7f→현재 SHA 쌍은 독립 대조했다.

rising/holding의 원 보고서→현재 코드 generation 쌍과 새로운 독립 fixture를 구분했다. summary parser의 신규 stage와, 선택c5에서 존재하던 funnel owner hash 불일치는 정확한 callback/의존 함수 AST 동등성을 확인한 후 predecessor 쌍을 보완했다. producer summary의 stage profile 확장은 원 거부 조건을 유지한다. 미검증 profile을 호환이라고 표시하지 않는다.

[코드 인계 검토](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-research-20261017/compatibility-fixtures/review-result.json)는 인계/요약/세대 관련2,920개 회귀와 네트워크 차단 fixture419개(133/86/116/84)의 통과를 기록한다. fixture는 아직 canonical 게시용 clean-release 증명이 아니며, 정식 release의 private CoW 준비에서 다시 검증한다. 원 정책·machine/aux 포인터·128개 보조 binding·승인된 두 PRE 변경·원 선택 bytes는 보존했다.
