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

## 최신 수량 선택본 통합과 다음 정규 기동용 배포

동시 승인 작업의 선택본 `c4467c424`를 재인수해 두 부모를 보존한 통합 커밋 `3abcc524c65edaf979cd7e7fd1499123b6531d2f`를 만들었다. 수량 관련8개 파일은 c446과, 지연 구현/인계13개 파일은 검토된769와 byte-identical이다. 통합 영향8개 파일 회귀1,337개(48.94초)·변경30개 Python compile·diff 검증을 통과했다. [통합 검증](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-research-20261017/merged-validation.json)에 결과를 보존했다.

배포 전 원 실패를 그대로 남겼다. 최초 pre-seal과 V2의 host selector 원자 교체 경합, V3의 보유판정 원장, V4의 주문 소유권 원장의 CoW 장치ID 변경을 각각 별도로 진단했다. 실제 host 원천은 봉인 stat/SHA와 같았다. 최종 V5는 private selector upper와, 원래 물리 원장·기존 lock inode의 읽기 전용 연결을 사용한다. 동일 바이트 교체도 SHA+5개 stat CAS로 감지하고, 원천 ledger를 복제하거나 잠금을 만들지 않는다. 원천 보존 커널 회귀·어댑터9개 반례·최종 CAS/영수증 실패 rollback 회귀와 독립 재리뷰를 통과했다. 근거는 [V5 원천 검증](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/file-and-directory-physical-source-regression.json)과 [44개 변경 계획 독립 리뷰](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/independent-publication-plan-review.json)다.

실제 clean release의 세 가족 원7f→현재 코드 인계·128범위/76,800행/598신호 parity mismatch0·네 가족 네트워크 차단 fixture419개(133/86/84/116)를 통과했다. source10/16 summary/strict/controller와 target10/19 `current_full_contract`를 확인한 뒤 기존 native lock·17개 원천 CAS·8개 기존 alias 백업·selector-last 순서로44개 준비 파일을 게시했다. 원 정책·env 전체 bytes, 현재 Main/보조/수량 pointer, 128개 연결·rollback 및 승인된 두 PRE 변경·기존10/19 OPEN6개를 보존했다.

22:56:35 KST에 실제 선택을 게시했고 22:58:18에 host native 전체 재검증 PASS/findings0을 받았다. 다음 기동 bundle은 `e94fddffc8620bc0f788794add090919732983be4a2966cd84f05c89cbce0b23`, 보조 overlay는 `e3e7926d8f30c8e164fdd2a420e4412b22370a03e8a753155220aa8f9ba3e4b5`다. [배포 결과](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/deployment.json), [게시 후 전체 검증](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/published-native-verification.json)에 정확한 source10/16→target10/19·선택 commit·실제 시각을 남겼다. 실제 PID 소비는 false이며 다음10/19 07:35 PREOPEN→07:55 Main의 원 `DirectFamilyPreopenPolicyHandoff`에서 확인한다. 자연1/3/5초 관측·재점검·주문·비용후 성과는 대기 상태다.

## 게시 후 전체 감시 결과와 잔여 범위

[원문 전체 감시](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/postpublication-health-original.json)는 PASS4/WARN2/FAIL1이며 전체 GREEN으로 처리하지 않았다. 7개 초기화/결과·보고서 계약 오류0·선택 코드 provenance·release-set·cron8개 연결은 정상이고, 네트워크·변경 차단 시도·운영 변경은0, canonical 상태/영구 cache는 불변이다. 기존 memory-only session에서 full1.900GB/reuse8.549GB·11.08초였다. native prepared 전체 재검증은 이 단계에서 반복하지 않았다.

FAIL은 `update_kospi`의 기존 요일 오탐이다. 실제 설치 `5 20 * * 1-5`와 달리 cron completion/산출물 등록부가 토요일에도21:05 이후 당일 표식을 요구한다. c5의16:11 점검은 같은 항목이 not_yet_due여서 결함이 드러나지 않았고, 해당 감시 코드는 c5/c446/3abcc에서 같았다. 원 FAIL을 보존한다. 수정 소유 파일은 `error_detectors/cron_completion.py`, `artifact_freshness.py`, `schedule_contract.py`이며, 다음 조치는 월~금 설치 일정의 expectedness 결속이다. 단순 trading_day_only 변경으로 평일 휴장일 skipped receipt 확인까지 생략하지 않는다. 종료 기준은 토요일 마감 후 미예정·월요일 미완료 FAIL·평일 휴장 skipped receipt 유효·cron 조회불가 unknown 보존이다. [분류 기록](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_deployment/2026-10-17/attempts/reviewed-v5/postpublication-health-classification.json)에 원문 hash와 별도 잔여를 남겼으며 이번 연구 코드의 정상 결과로 덮지 않았다.

WARN의 `main_trailing_research_handoff_invalid`는 c5 원문부터 존재한다. 기존10/19 OPEN `HoldingProfitExitSourceContractRepair`의 정확한 원세대→현 코드 인계/재검증 담당을 유지한다. 최초 수량의 비용/귀속 결손과 기존 설정 오류 로그2건도 보존했다. 이번 작업이 전체 장후 경제성이나 모든 감시기 결함을 해소했다고 주장하지 않는다.

## 체결 기준 재검토와 단기 선정 보완 — 2026-10-20

### 범위와 판단

- 사용자 `다음액션 실행`의 구현·반복 자체 리뷰·장후 영향 범위 재계산이다. 기준은 실제 선택 `21d822a64a9f4b9047d06babab26febf59f6ae61`, Main PID1175053/start11403252이며 격리 branch `work/pre-submit-delay-consumer-20261020`, 작업본 `/home/ubuntu/KORStockScan-worktrees/pre-submit-delay-evidence-20261020`에서 구현했다. canonical fcd31ae7c의 병행 수정·선택 릴리스·기동 상태를 덮지 않는다.
- **현재 0초는 최적 시간 증명이 아니다.** 10/20 관측된 price_ready5건은 모두 `unsupported_existing_behavior`의 0초다. 10/19 원 정책124개 price_ready cell 중110개는 근거 불충분,12개는 관측 pair에서 즉시 유리,2개는180초를 지지한다. 두 양수 cell은 중복 부모/자식 유형이므로 독립 사례2건이 아니다.
- 운영 default0, 비교 근거, 실제 체결/비용후 성과를 구분한다. 학습/검증 혼합 방향, 미지원 부모·상황, holdout 부족을 즉시 우월로 표시하지 않는다. 초기 정책에 별도의 경제성 승인 gate를 추가하지 않았다.

### 최초 결함과 수리

| 최초 위반 계약 | 원인·수리·회귀 |
| --- | --- |
| 동일 정책의 요청별 해시 분열 | 실제 HPSP의 compact wire `fact.enum`이 f6→f7로 바뀌어 부모 identity가 분리됐다. 원 proof를 검증한 뒤 인용 별칭만 정규화한다. payload/schema provenance와 원 hash를 보존하고 prompt/model/options/risk/verdict/validator 차이는 합치지 않는다. 미래 provider identity와 과거 projection에 같은 owner를 사용한다. |
| 단기 관측과 실행 선정 불일치 | v4는 엄격한 P0/단기 clock을 만족한1/3/5초를 후보에 포함한다. v2/v3 재현은 원 grid 그대로 유지한다. fixture에서1초 선정→native 검증→PreparedPolicy lookup까지 연결하며 미유효 P0를 거절한다. |
| 단기 due 의미감시 오판 | 선택값 검사가 legacy grid에 한정돼 있었다. 단기 선택도 정확한 successor/deadline/terminal 검사를 받도록 수정했다. 정책 미지원/0초 근거는 원천결손으로 세지 않고 별도 집계한다. commit→제출 함수 반환은 체결시간·의도된 대기시간과 구분한다. |
| native 주문계획 연결 누락 | embedded receipt self-hash는 유효한데 중복 outer hash의 부재를 실패로 처리했다. outer hash가 존재하면 일치를 요구하고, 부재이면 native receipt·symbol·record·원 machine/attempt를 검증한다. 가까운 시각/종목만으로 연결하지 않는다. |
| 체결시각·원천 세대 오판 | DB position buy_time과 broker fill 시각은 실제로1초 다를 수 있다. position generation은 원 scalar/field와 비교하고 가격경로는 broker 시각으로 계산한다. original sealed cache는 기존 logical-source/epoch 검증을 따른다. dependency로 봉인된 plain fact JSON에 embedded artifact hash를 요구하던 추가 오탐도 수정했다. |
| 장중 정상 append의 전체 제외 | native SQLite reader의 명시적 snapshot receipt 모드에서 읽은 prefix를 고정하고 native append 후속 세대만 허용한다. 원 strict reader는 그대로 유지한다. 추가 행을 이전 snapshot에 섞지 않으며 미영수 append·재작성·generation conflict는 계속 실패한다. |
| 부분 결과의 성공 오인 | records/bytes 상한 초과는 완료 보고서 발행 전에 실패한다. native metadata/fill fields만 읽고 큰 미색인 snapshot은 정확한 날짜·사유로 남긴다. 미확인 값·비용은 null이다. |

### 실제 재계산과 소비

- [최종 체결/기회 보고서](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-19/attempts/20261020-execution-v4/execution_report.json): clean baseline06/05 이후 매수수량이 기록된 포지션585건을 보존했다. 정확한 first/last recorded fill·Main 주문 연결13건, fill clock 미확인569건, Main owner 미확인1건, position generation/추가매수 충돌2건이다.13건 모두에서 연속 호가가 확보됐다는 뜻은 아니다. ENTER_NOW+PASS 기준점357건(price_ready143, signal_ready214), native 주문계획 연결51건이다. 후행 관측이 없는 행과 미체결 기회도 남겼다.
- 첫 체결 기준1/3/5/30초의 정확한 호가가 있는 포지션은 각각4/4/2/4건이다.60/120/180초는각각0/1/1건이다. 일부 sparse 경로로 전체585건의 하락률이나 최적 지연을 확정하지 않는다. HPSP49389는 첫 체결51300원 이후 관측 최저ask가 약19.49bp 낮지만, 마지막 기록 체결의 가중 평균51188.89원 기준 관측 최저ask는 약2.17bp 높다. HPSP49391은50000원 체결 이후 지연 관측에서49750원(-50bp) ask가 확인됐다. 청산 뒤 중단된 trailing 관측만 사용한 v3에서는 빠졌던 하락이다. v4는 동일 native 계획에 연결된 유효한 지연 후행 호가를 함께 사용한다. 부분 체결·최종 수량 갱신·체결 이후 호가를 같은 기준으로 취급할 수 없다.
- 원 분석[v1](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-19/attempts/20261020-execution-v1/execution_report.json)과 추가 오탐이 드러난[v2](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-19/attempts/20261020-execution-v2/execution_report.json)는 보존했다. v3의 reader 수리와 v4의 청산 후 지연 관측 누락 수리를 각각 재검증했다. legacy snapshot31,761,648B와 native index16일의 선택 projection45,448,247B를 읽었고 pipeline raw 전체 scan은0이다. 최종 v4 소요6.53초, 최대RSS199,636KiB다. 서로 다른 coverage와 cache 상태를 속도 개선 배수로 비교하지 않는다.
- [격리 후보 policy](/home/ubuntu/KORStockScan/data/report/pre_submit_delay_research_review/2026-10-19/attempts/20261020-candidate-v4/threshold_cycle/pre_submit_delay_policy/generations/81fe37304478f68d490a2b0e644c923698479a09d546e031a25406ed2d31cc17/policy.json)는 source10/19·publication10/20·effective10/21이며 실제 게시본이 아니다. policy SHA `678240cfd2cb93f5f82cc529126211b11bfc47f66b21ea9beab05bf3d6d43e74`, algorithm v4다. 정책 학습은09/29 이후 family ledger로 확인한345기준점/P0293만 사용한다.
- 정확한 부모 조합은78→57개, price_ready cell124→105개로 줄었고 가격 pair373→402쌍(단기29쌍 포함)이다. 새105개 cell의 근거는 **불충분92 / 관측 pair 즉시 우위11 / 양수 지연2**다. 양수2개는 같은 부모 집단의180초 부모/자식이며 부모 train6·holdout3, 평균 가격 개선8.74bp/8.23bp다. 실제 데이터에서1/3/5초의 최종 채택은 없었다. 이를 채택 성공이나 비용후 이익으로 표시하지 않는다.
- [native 선택 검증](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-evidence-20261020/native-selection-validation.json)은 원v3·새v4의 전량 재현 및 각각124/105개 cell의 PreparedPolicy 조회를 확인한다. 새 code contract도 일치한다. 후보 생산은 compact5,580,745B/2,273행을1회 decode했으며150.14초·최대RSS82,460KiB다. 현재 정책과 원 PREOPEN bytes를 수정하지 않았다.

### 대체·제거와 검증

| 기존 구현 | 대체·판정·현재 소비자 |
| --- | --- |
| provider_identity 내부 schema_shape | `response_contract_shape`로 consolidated. provider와 검증된 과거 timing identity가 한 구현을 사용한다. |
| 신규 정책의 legacy 전용 후보 선택 | v4 버전별 horizon/selection_pairs로 consolidated. 동결 v2/v3는 기존 정책 재현·native validator 때문에 retained이며 퇴역 실행 권한이 아니다. |
| 보고서/lookup에서 혼동하던0초 의미 | `selection_evidence`로 consolidated. report·PreparedPolicy·기존 의미감시가 같은 판정 owner를 소비한다. |
| raw report 별도 우회 reader | none. 기존 `pre_submit_delay_research_review`, native source/completed-store, family producer를 확장했다. 새 module·wrapper·worker·schedule·report framework 없음. |
| 전체 파일 세대가 같아야 하는 native read | 기존 strict 모드 retained. 정확한 immutable 입력 소비자가 사용한다. 장중 분석만 명시적 pinned snapshot receipt를 사용하고 같은 writer proof/reader 안에서 검증한다. |

비테스트 source8파일 `+621/-42`, test4파일 `+371/-4`다. 새 모듈/entrypoint는 없으며 기존 CLI의 선택적 체결 census, 기존 snapshot reader 인자, 기존 lookup 진단 필드가 늘었다. 순증은 전수 모집단 보존·정확 체결/기회 연결·가격경로와 단기 선택 및 부정 입력 회귀에 따른다. 이동·미니파이·퇴역 코드의 다른 경로 이동은 없다. 관련 정적/동적 호출, CLI 및 family dispatch는 기존 owner를 유지한다.

중간 영향1,404개·추가 native reader/보고서135개를 거쳐 구현본1,494개(140.33초), 현재 선택본 통합 후1,511개(190.22초), 마지막 청산 후 관측 보완49개(3.64초) 회귀가 통과했다. 중복 테스트를 합산하지 않는다. compile·diff 검사와 canonical/격리 print-only parser도 통과했고, 현재 체크리스트의 재개 owner는 각각1개다. live provider/order 호출, bot 재기동, 운영 정책 게시, 원 장후 전체 체인 재생성은 수행하지 않았다.

잔여 소유자는 현재 checklist의 `PreSubmitDelaySituationResearch1017`이다. source-index/정확 fill clock가 없는 과거 행은 복구 완료나 영구 소실로 단정하지 않는다. 자연 관측은 정확 horizon coverage와 원 체결 leg, code/policy 인계는 `DirectFamilyPreopenPolicyHandoff`, 비용후 경제성은 실제 비용·terminal 결속으로 각각 종료한다. 현재 machine 부모가 다른 행은 새 후보의 양수 cell을 승계하지 않는다.


### 병행 릴리스 재인수와 최종 인계 경계

구현 commit `6fd14475b` 이후 병행 작업이14:47:51에 운영을 `0ce816f7c1e2c495c24fc11fd4ab0a7d837c56ca`로 전환했다. 실제 PID2108660/start11987479의 cwd/선택 receipt를 확인했고, 이번 작업이 수행한 배포나 재기동으로 기록하지 않는다. 격리 merge `fd7071c0f`는 새 SQLite lifecycle·cleanup과 기존 지연 수리를 모두 보존한다. checklist 충돌은 양쪽 담당 항목을 유지해 해결했다. source/test 비교는 현재 선택0ce 기준의 이번 변경만 집계한다.

통합 후에도 후보의 선택 code contract `90593534bb4d658f653da6e2576eb8b833747a963f220743c1850f1ded27c81a`는 같으며 원v3·새v4 PreparedPolicy 및 후보 원천 재검증이 통과했다. 값/분할이 달라지지 않은 후보를 다시 발행하지 않았다. 원 정책/보고서/committed pointer/PREOPEN4개 파일 SHA는 보존됐다. selector 변경은 병행 배포로 구분한다. 이번 branch의 정식 release 준비·native 전체 code handoff·정책 게시·PID 소비는 아직 수행하지 않았다.


## Identical machine-parent timing cohorts — 2026-10-21

- 요청 범위는 구현·반복 코드리뷰·격리 재계산·배포 후보 준비다. 재기동·selector/PREOPEN/운영 정책 교체는 하지 않는다. 기준 코드 `d2e9bedf3ac638788c6850e183f0a2f35e00943c`는 이전에 검증한 자연 종료 전환/수집기 종료 수리를 포함한다. 별도 수량 연구 후보의 미종결 변경은 포함하지 않는다. 실제 유지 대상은 `ea68c5a85`, Main1724066/start19233026, epoch1792547808026387070이다.
- 원인: 오늘 기계 부모 `2581b1bf…`와 원 학습 부모 `29c211d3…`는 전체128개 scope의 기계·보조 payload, membership, definition, backend가 같다. 전체 실행 해시는 정책 인계와 장후 materialization 코드 변경도 포함하여 달라졌다. 부모 문자열만으로 집단을 나누던 생산자는 같은 규칙의 과거 근거를 오늘 정책에 연결하지 못했다. 이전 `c0036d89…`는 session contract 코드가 달라 연결하지 않는다.
- 수리: 기존 `pre_submit_delay_situation_projection`에서 발행된 target bundle→native parent ancestry를 제한된 깊이/파일 크기로 읽고 원 파일 SHA·native seal·날짜·전역 규칙을 검증한다. 두 비평가 코드 파일만 equality에서 분리하며 나머지 실행 코드·unknown field·기계/보조 payload·membership·definition은 정확히 같아야 한다. auxiliary timing identity는 기존 계약 그대로다. 불명/상이 부모에는 alias를 발급하지 않는다. 조건이 성립한 부모만 기존 partitioned producer의 **선정 집단**에 연결한다. qualified projection/판정·호가/기회 ID와 원 부모는 그대로 보존한다. 기존 v4 split/purge·가격쌍 비교·지원 없는0초는 유지한다.
- 직접 소비: sharded validator는 원본 native proof를 확인한 뒤 전량 재계산한다. source verifier와 연구 검토 reader도 같은 결속을 소비한다. runtime의 exact-parent lookup은 그대로 사용하며 임의 hash alias나 warm-path 파일 읽기를 추가하지 않는다. 기존 정책을 소비하는 코드 인계는 네 변경 source의 전체 exact dependency group으로 결속한다. 실제 정책 내용 변경은 기존 same-policy code handoff가 승인하지 않는다.
- [격리 재계산](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/recalculation-result.json): 원source10/20→target10/21의 과거 발행 날짜를 보존한 재현이며 새 운영 발행이 아니다. 기준점382개 중37개를 연결했고 원 projection logical SHA·census·가격쌍477개를 보존했다.121개 price_ready cell은 불충분102·즉시우위17·양수180초2로 동일하다. 오늘 부모 cell16개는 불충분10·즉시우위6이며 양수는0이다.121개 native PreparedPolicy 조회를 대조했다. native sealed raw references와 현재 compact/ledger/situation generation을 검증했으며 과거 raw 전체를 재자격 심사했다는 뜻은 아니다.14.353초·최대RSS136836KiB, 원자료 추가/수정0이다.
- [오늘12건의 격리 조회](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/today-attempt-replay.json): 원12개 ID를488576B compact에서 대조했다.1건은 근거 있는 즉시제출,11건은 비교 근거 부족이며12건 모두0초다. 이는 실제 정책 적중률 변경이나 주문 재실행이 아니다. 기존 양수180초 집단은 오늘 부모로 이전하지 않는다. 과거 무효 호가8건도 복구되지 않았다.
- 리뷰 보완: 선정 집단을 옮길 때 연구 검토 reader가 원 부모로 membership을 찾던 불일치를 함께 수리했다. 원천 body를 바꾸는 대신 group lookup만 같은 native proof로 결속했다. runtime/세션/새 코드/규칙/route/AI/membership/definition/unknown field 변경, 잘못된 날짜·hash·ancestry·누락/변조 파일은 연결 거부 회귀로 확인한다. native 로더를 축약한 단위 fixture와 실제 원본 native validation 결과를 구분한다.
- 검증: 영향 회귀198개 PASS, reader 보완 이후 표적12개 PASS. 코드 인계 회귀의 최초 실패는 확장된 source group을 누락한 축약 fixture였고 누락 파일 검사를 유지한 채 fixture 입력을 보완했다. 최종 인계/compile/diff/parser 및 후보 결과는 [검증 기록](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/validation.json), [후보 준비](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/candidate.json)에 기록한다.

| 기존 경로 | 처리 및 현재 소비자 |
| --- | --- |
| native situation projection / ancestry source reader | retained/extended. 기존 partitioned producer와 native 검증이 소비하며 별도 모듈·worker·보고서 producer를 만들지 않는다. |
| partitioned `_populate`의 exact-parent grouping | consolidated. 같은 함수가 native proof가 있는 집단만 연결하고 나머지는 원 exact-parent를 유지한다. |
| 연구 검토 `_populate`의 원 부모 전용 membership 조회 | replaced in place. 원 신원은 보존하고 검증된 선정 집단을 조회한다. |
| runtime PreparedPolicy exact-parent lookup, v2/v3/v4 역사 reader | retained. 기존 운영 정책과 봉인 과거 generation의 현재 소비자다. |
| 기존 코드 인계 profile | retained. 원 PREOPEN/현재 PID/이전 불변 릴리스가 소비한다. 새 네 파일 group도 같은 검증 함수에 연결한다. |

크기/소유 변화: 기준d2e9bedf3 대비 비테스트 source5개 +195/-11, tests2개 +131/-0, docs3개 +33/-1이다. 이동·새 모듈·실행 entrypoint·worker·schedule 추가0, 폐기 경로0이다. native 보조 함수4개는 기존 원천 owner 안에 두었다. 순증은 기존 owner의 native 동일성/ancestry 검증과 producer-consumer 연결 및 실패 회귀 때문이다. canonical의 병행 수량/종료 문서 변경은 이 commit 집계에 넣지 않는다.

기능/코드 수리와 배포/정책 게시/자연 판정은 별도다. `DirectFamilyPreopenPolicyHandoff`가 다음 정식 source-date 정책 재계산·현재 machine target binding·PREOPEN·정확한 PID 소비를 소유한다. 현재 세션은 재기동과 자동 전환 예약을 수행하지 않는다. 장 종료 대기 세션을 유지할 필요가 없다.
