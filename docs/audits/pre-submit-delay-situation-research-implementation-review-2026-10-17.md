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
- 직접 소비: sharded validator는 원본 native proof를 확인한 뒤 전량 재계산한다. 생산자의 게시 직전 원천 확인과 연구 검토 reader도 같은 결속을 소비한다. runtime의 exact-parent lookup은 그대로 사용하며 임의 hash alias나 warm-path 파일 읽기를 추가하지 않는다. 기존 정책을 소비하는 코드 인계는 세 변경 source의 전체 exact dependency group으로 결속한다. 실제 정책 내용 변경은 기존 same-policy code handoff가 승인하지 않는다.
- [격리 재계산](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/recalculation-result.json): 원source10/20→target10/21의 과거 발행 날짜를 보존한 재현이며 새 운영 발행이 아니다. 기준점382개 중37개를 연결했고 원 projection logical SHA·census·가격쌍477개를 보존했다.121개 price_ready cell은 불충분102·즉시우위17·양수180초2로 동일하다. 오늘 부모 cell16개는 불충분10·즉시우위6이며 양수는0이다.121개 native PreparedPolicy 조회를 대조했다. native sealed raw references와 현재 compact/ledger/situation generation을 검증했으며 과거 raw 전체를 재자격 심사했다는 뜻은 아니다.14.353초·최대RSS136836KiB, 원자료 추가/수정0이다.
- [오늘12건의 격리 조회](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/today-attempt-replay.json): 원12개 ID를488576B compact에서 대조했다.1건은 근거 있는 즉시제출,11건은 비교 근거 부족이며12건 모두0초다. 이는 실제 정책 적중률 변경이나 주문 재실행이 아니다. 기존 양수180초 집단은 오늘 부모로 이전하지 않는다. 과거 무효 호가8건도 복구되지 않았다.
- 리뷰 보완: 선정 집단을 옮길 때 연구 검토 reader가 원 부모로 membership을 찾던 불일치를 함께 수리했다. 원천 body를 바꾸는 대신 group lookup만 같은 native proof로 결속했다. runtime/세션/새 코드/규칙/route/AI/membership/definition/unknown field 변경, 잘못된 날짜·hash·ancestry·누락/변조 파일은 연결 거부 회귀로 확인한다. native 로더를 축약한 단위 fixture와 실제 원본 native validation 결과를 구분한다.
- 검증: 영향 회귀198개 PASS, reader 보완 이후 표적12개 PASS. 코드 인계 회귀의 최초 실패는 확장된 source group을 누락한 축약 fixture였고 누락 파일 검사를 유지한 채 fixture 입력을 보완했다. 최종 인계/compile/diff/parser 및 후보 결과는 [검증 기록](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/final-candidate/validation.json), [후보 준비](/home/ubuntu/KORStockScan/tmp/pre-submit-delay-semantic-20261021/final-candidate/candidate.json)에 기록한다.

| 기존 경로 | 처리 및 현재 소비자 |
| --- | --- |
| native situation projection / ancestry source reader | retained/extended. 기존 partitioned producer와 native 검증이 소비하며 별도 모듈·worker·보고서 producer를 만들지 않는다. |
| partitioned `_populate`의 exact-parent grouping | consolidated. 같은 함수가 native proof가 있는 집단만 연결하고 나머지는 원 exact-parent를 유지한다. |
| 연구 검토 `_populate`의 원 부모 전용 membership 조회 | replaced in place. 원 신원은 보존하고 검증된 선정 집단을 조회한다. |
| runtime PreparedPolicy exact-parent lookup, v2/v3/v4 역사 reader | retained. 기존 운영 정책과 봉인 과거 generation의 현재 소비자다. |
| 기존 코드 인계 profile | retained. 원 PREOPEN/현재 PID/이전 불변 릴리스가 소비한다. 새 세 파일 group도 같은 검증 함수에 연결한다. |

크기/소유 변화: 기준d2e9bedf3 대비 비테스트 source4개 +193/-13, tests2개 +138/-0, docs3개 +35/-1이다. 이동·새 모듈·실행 entrypoint·worker·schedule 추가0, 폐기 경로0이다. native 보조 함수4개는 기존 원천 owner 안에 두었다. 순증은 기존 owner의 native 동일성/ancestry 검증과 producer-consumer 연결 및 실패 회귀 때문이다. canonical의 병행 수량/종료 문서 변경은 이 commit 집계에 넣지 않는다.

후보 점검 보완: 첫 후보4e107cca1의 공용 `pre_submit_delay_initial_policy.verify_source`에 추가한 검증3줄이 익절 연구 코드 계약까지 바꾸어 currentness 검사를 실패시켰다. 원 실패를 보존하고 공용 모듈은 원상 유지했다. 같은 검증을 기존 partitioned producer의 게시 callback과 native selection validator에 통합했다. currentness 한도를 완화하거나 익절 연구를 재계산하지 않는다. 이로써 shared source·runtime lookup은 기준본과 byte-identical이며 배포 후보는 후속 commit으로 준비한다.

기능/코드 수리와 배포/정책 게시/자연 판정은 별도다. `DirectFamilyPreopenPolicyHandoff`가 다음 정식 source-date 정책 재계산·현재 machine target binding·PREOPEN·정확한 PID 소비를 소유한다. 현재 세션은 재기동과 자동 전환 예약을 수행하지 않는다. 장 종료 대기 세션을 유지할 필요가 없다.

## 2026-10-23 frozen 77-case input lineage and collector accounting repair

Authority: trace the original 77 input-short/stale cases by item, lease and epoch; repair proved defects, review/fix/re-review and validate; deployment waits. Code baseline is `926ebca82aa48119ea1ff1483ef33cd78be508ee`, isolated branch `work/probe-source-contract-20261023`. Canonical concurrent changes are preserved. Existing owner remains `PreSubmitDelayFollowupSubscription1023` under `DirectFamilyPreopenPolicyHandoff`; no new OPEN owner or monitoring framework is created.

### Frozen cases and limits

The original 120-probe population through 11:09:25 remains fixed: 38 no-match, 5 pending confirmation, 77 input-short/stale. The 77 unique item/lease/epoch tuples belong to PID1982231/start36273583 and transport1792718217941572. [All 77 identities](../../tmp/probe-source-contract-20261023/case-census.tsv), [case verification and physical references](../../tmp/probe-source-contract-20261023/case-verification.json), and [original full fields](../../tmp/probe-source-contract-20261023/frozen-cases.json) retain the original reasons and source hashes.

| Classification | Cases | Decision and remaining uncertainty |
| --- | ---: | --- |
| Received trades, then current-source age exceeded | 47 | 37 native-history-stale plus 10 source-wait-age cases. Current freshness block is valid. A quiet last interval is not independently certified market no-trade. |
| Depth received, no trade received | 2 | 042500_AL and140430_AL have 0D evidence but no0B. No synthetic trade, source age reset or success claim. |
| Event quote unusable | 3 | 006280_AL,207940_AL and013810_AL lack an executable event BBO. The first two report missing executable_quote; the third is also stale. Later depth cannot rewrite the original trade quote. |
| One late trade, insufficient history | 1 | 478560_AL received its only trade near residence end; native observed_seconds=0 cannot satisfy the60s branch window. |
| Neither0B nor0D wire observed | 24 | Exact local REG was sent and the lease remained bound. Connection-level return_code=0 is not item ACK. Normal inactivity versus upstream subscription/delivery remains unproved. |

All77 wire-to-normalized counter comparisons agree. The frozen intervals contain1950 durable0B records; all match the exact-item received counts and consecutive native sequences. All1899 adjacent cumulative-volume differences equal the incoming trade quantities. All41 available native terminal receipts have the same last0B clock as the wire receipt; their selected lifecycle TRUE count is0. These observations establish local input accounting and valid guards, not complete market coverage or a proof that every future entry is impossible. Source/quote absence is not zero economics, and no trade/PASS/order was manufactured.

Market identity is REGULAR / policy cohort KRX / market-data item `_AL` / route `krx_nxt_integrated` / default broker route SOR. No order receipt verifies a physical execution venue. The24 route_snapshot_missing cases mean no exact source snapshot, not a missing venue label. [Independent volume availability](../../tmp/probe-source-contract-20261023/independent-volume-availability.json) found no paired original-window market-volume receipts in the latest-only queue; a newer source hash or a single unchanged snapshot cannot certify these24 as quiet.

### Proved defects and existing-owner repairs

1. `KiwoomWSManager._observe_micro_reversion_forward` discarded the collector's actual return enum. Per-item normalized receipt counts therefore survived while admitted/rejected/disabled/queue-full/isolated-error attribution survived only as process-wide totals. The original code fails14 outcome-attribution regressions, while5 identity controls pass. Extend the existing exact lease with cumulative outcome counters per0B/0D, first non-enqueued metadata and last outcome metadata. Counters use a finite native enum plus unavailable/error/unobservable buckets; there is no rejection-tail count truncation, raw payload copy, disk work or new source store. `enqueued` is admission only, never writer durability or broker ACK.
2. `ZeroBaseDiscoveryRuntime.dispatch_due_probes` emitted the source hash/clock but omitted the frozen discovery volume and physical lease ID from its existing claim event; the mutable latest queue overwrites older source observations. An existing durable-claim test fails on that omission. Preserve discovery volume, source kind and physical lease ID in the existing event. Future no-trade comparisons require matching source kind, volume semantics, route, date and bracketing clocks; the additional fields alone do not certify silence. Old missing receipts are not backfilled.

Identity is captured before the collector callback and credited only if the original object, lease ID and transport remain current. Cross-item/route/epoch, pre-registration, invalid-clock and replacement/reconnect cases earn no attribution. The terminal native trace already deep-copies lease state before release; `run_zero_base_probe` and the scanner's existing `zero_base_ws_source_trace` field carry the same counters into raw/compact evidence. There is no new result producer, wrapper, CLI, schedule, REG, REMOVE, retry or order path.

Official Kiwoom reference gate preceded coding: upstream HEAD was refreshed11:41:19 KST at `953e5dbff123f437ab4d11a78a95191a685eb51f`; specs/core client/realtime packets+stream/packaged0B+0D/Postman were inspected by11:53:56. `kiwoom_docs` is absent. [Paths, hashes and retrieval](../../tmp/probe-source-contract-20261023/official-reference.json). Preserve0B/0D, plain/NX/AL item semantics, REG refresh=1 and exact REMOVE. No protocol, FID, authentication, account/order, source timeout, policy or safety change.

### Review, validation and dispositions

The first expanded validation exposed a lock-contract mistake introduced by the repair: native ingress already owns a non-reentrant snapshot lock. That isolated test run was interrupted; no runtime process was stopped. Supplemental fix passes explicit lock ownership through the existing queue/observer caller; direct callers acquire the lock. A bounded native-message regression rejects re-entry without hanging. The broad run then found one stale observer-mock signature, fixed in its existing fixture. Real collector rejection+admission, frozen trace, scanner forwarding,200 repeated exclusions, missing identity and generation transitions are covered.

Final affected validation passed849 tests in64.16s, with11 explicitly deselected unrelated handoff fixtures and one existing pandas deprecation warning: [final closure](../../tmp/probe-source-contract-20261023/final-closure.xml). The earlier803-case affected run and146-case supplemental run also passed; duplicate runs are not added to the distinct total. Python compile, diff checks and the canonical print-only backlog parser pass (26 tasks; exactly one current parent, follow-up subscription and premarket NXT owner each). No Project/Calendar sync was executed. An exploratory813-case run had6 failures: the repaired mock plus5 existing policy-handoff fixture failures. Replacing only WS with the pinned original reproduces the same5 policy failures (target_date missing or active_policy_code_reader_root_changed), with6 fixture controls passing. [Original extended result](../../tmp/probe-source-contract-20261023/targeted-initial.xml), [unmodified-code reproduction](../../tmp/probe-source-contract-20261023/baseline-policy-fixtures.xml). Those unrelated handoff tests are explicitly excluded from the final affected suite; this is not an all-suite/P5 PASS. Existing deployment/handoff ownership remains `DirectFamilyPreopenPolicyHandoff`; no policy guard or fixture authority is weakened.

The one-time bounded raw inspection reads64,792,560 trade bytes and90,655,391 depth bytes. A manual depth projection initially used the0B `source_item` field; the0D schema owns `item`. Its failed attempt is retained, and the corrected90,589,846-byte read verifies the same frozen content digest. Depth journals contain only admitted valid snapshots, so their counts are not asserted equal to wire counts; historical per-lease rejection attribution is precisely the missing evidence. No growing whole-file scan/hash or unchanged report regeneration is introduced. The isolated20,000-call benchmark is0.271us baseline,0.807us current unleased and3.739us current leased per callback; it is not a live latency guarantee.

| Old owner/path | Disposition and consumer |
| --- | --- |
| Ignored collector callback return | replaced in place by bounded exact-lease attribution; existing terminal trace/scanner field consumes it. |
| Existing queue/observer dispatch | retained with explicit snapshot-lock custody; one production call site, no alternative implementation. |
| Mutable queue and claim event | retained; the existing event now preserves already-owned volume/source-kind/lease fields. |
| Collector input validation, queues, writers, native FSM, guards | retained; valid rejection/admission still comes from the same owner, not a new classifier. |
| Prior retention/NXT repair and natural180s/NXT acceptance | retained; absent eligible samples do not reopen that code repair or close its natural acceptance. |

No modules, entrypoints, scheduling registrations or wrappers were added/removed; no deferred compatibility path was created. Source/test/doc growth is recorded separately in the final change manifest. The canonical original strict checklist SHA91d9874a2fe47a5bcebe281c052ca65d0c978fe3477562557a7e735ae8b23011 is preserved through the selected release's native helper; an initial canonical-import invocation failed and did not change the checklist.

### Runtime boundary and next action

An independent deployment during this audit changed the selector from926ebca82/PID1982231 to `a2ca8e7d8d6b77456b509f6f7133a6ba2911e562` / PID2333464/start36885727. The affected selected WS/claim producers are unchanged between those commits. [Current pin](../../tmp/probe-source-contract-20261023/final-runtime-pin.json). This task performs no deployment/restart, selector/PREOPEN/policy publication, live REG/REMOVE, provider or order call. The new counters/claim fields are not current-PID consumption evidence.

Keep the same checklist owner OPEN for the24 unproved origins, deployment wait, next natural exact-lease collector-result consumption and original180s/REMOVE acceptance. After an authorized integration, a naturally received packet must preserve its actual collector enum through the original lease and scanner event; rejection/queue/error cases must remain distinguishable. For no-wire cases, use only existing comparable bracketing market evidence if available; otherwise retain unobservable upstream origin. Next10/26 premarket explicit NXT validation remains separately owned. Old missing native data and rejection reasons remain null, never repaired by relabeling the past.

Scope versus926ebca82: non-test source2 existing files +60/-9; tests3 existing files +149/-2; docs1 existing review +55/-0. No moves. The canonical generated checklist receives4 scoped progress bullets outside the code commit; concurrent checklist deltas are preserved separately. Net source growth retains callback outcomes and original claim fields in existing owners; it does not add a worker, source store, entrypoint or trading branch. Scoped re-review has no unresolved code finding; the24 historical origin uncertainties,5 pre-existing unrelated handoff fixture failures and deployment/natural-consumption acceptance remain explicit.

## 2026-10-23 policy handoff fixture closure and no-wire follow-up

Authority: diagnose and fix the five previously reproduced handoff test failures, review/fix/re-review and validate; additionally trace the same24 no-wire cases; deployment continues to wait. The selected baseline is `a2ca8e7d8d6b77456b509f6f7133a6ba2911e562`, PID2333464/start36885727. Isolated `work/handoff-no-wire-20261023` carries the prior46d41739a repair as equivalent commit3efb7cb48 on that selected ancestry. Canonical dirty/concurrent work and the original77-case population are preserved.

### Five failing checks: causal repair

[Baseline reproduction](../../tmp/handoff-no-wire-20261023/baseline.xml) confirms5 failures and6 controls passing. The first2 fail at `_ORIGIN_SCRIPT` with missing `target_date`; the other3 reach the legitimate `active_policy_code_reader_root_changed` guard while expecting an unrelated code-hash error.

| Failures | First broken test contract | Existing-owner repair |
| --- | --- | --- |
| rollover `none` and `source_error` | The mocked native parent returns a bundle hash alone. The real producer returns an authenticated dated parent and sealed source/code closure. The old source_error stub targets a loader the prepared-parent branch intentionally does not call. | In `test_main_market_source_consolidation.py`, supply the dated parent, exact current pointer and real sealed origin receipt, retaining the actual native receipt reader. Exercise source_error by changing the original referenced source. Assert exported source/code/generation hashes, exact rejection reasons and whether the ordinary loader was invoked. |
| code refresh False/True/closed_postclose | The fixture selects `root/new-release` while executing a different reader and supplies no predecessor review authority. Runtime correctly rejects the root mismatch before examining a missing compatibility receipt. | Select the actual test reader for the intended native code-mismatch check. Separately select the foreign root and require its exact custody rejection in each scenario, then restore the exact selector before the remaining activation/source/CAS checks. |

The repair changes the existing test fixture, not the production policy loader. No production source change was needed for these5 failures. New rollover negatives cover missing origin receipt, changed pointer/date/root and changed origin code in addition to original source/generation/authority/parent checks. The source-error case now reaches the real sealed-source validator. The foreign reader remains rejected; no extra accepted error string or weakened guard was introduced.

First repair:16/16 targeted cases pass. Re-review strengthens exact reasons and loader-branch assertions;13 rollover cases pass. The full affected9-file run passes865 cases with no deselection of the old11 handoff nodes, and a final85-case consolidation rerun covers the strengthened test source. [Affected suite](../../tmp/handoff-no-wire-20261023/all-affected.xml), [final test owner](../../tmp/handoff-no-wire-20261023/consolidation-final.xml), [strict negatives](../../tmp/handoff-no-wire-20261023/rollover-rereview.xml). Prepared/ordered contracts pass512 cases and exact predecessor-custody checks pass20:1397 distinct passing cases across the865+512+20 suites. The final85-case rerun and earlier targeted runs are repeats, not added to that total. [Prepared/ordered](../../tmp/handoff-no-wire-20261023/prepared-ordered-contracts.xml), [predecessor custody](../../tmp/handoff-no-wire-20261023/predecessor-custody-contracts.xml). Python compile and diff checks pass; current-checklist parser/owner/link validation is recorded in the final result manifest.

An exploratory full handoff/source-inventory matrix was deliberately interrupted after2800 completed cases without failures because it included unrelated source-registration matrices. It is not a full-suite PASS; interruption also triggered pytest tmp_path teardown KeyError. [Original interruption status](../../tmp/handoff-no-wire-20261023/broad-interruption.json). Final validation uses the complete affected tests and bounded native custody/prepared consumers. No package/runtime change or retry of that unrelated matrix was made.

### Additional trace of the original24 no-wire cases

[Exact case verification](../../tmp/handoff-no-wire-20261023/no-wire-followup-verification.json) and [24-row census](../../tmp/handoff-no-wire-20261023/no-wire-census.tsv) preserve item/lease/transport1792718217941572, original source hashes, REG IDs and roughly10s windows under the original PID1982231/start36273583. All24 remain locally bound with sent REG; all exact0B/0D wire and normalized counts remain0. None has an item-attributed broker ACK. Connection return0 and post-REMOVE silence do not establish a successful item subscription or market no-trade.

New evidence:

- The original collector now has a native closed receipt, generated11:55:34, process1982231/start36273583, collector epoch1792718217853785204. [Preserved receipt](../../tmp/handoff-no-wire-20261023/old-pid-closed-collector.json). Observation/depth queue drops, adapter invalid envelopes, worker/writer errors and drops, venue blocks and timestamp rejections are0. Global invalid-depth exclusions525 remain recorded; they cannot explain these24 cases' missing wire receipts. Downstream accounting covers observed callbacks, not unseen broker traffic.
- The original10:16:42 ka10099 snapshot identifies23 no-wire symbols as NXT-disabled and1 as enabled. However37 received-input controls are also NXT-disabled on the same `_AL` route. [Dated comparison](../../tmp/handoff-no-wire-20261023/dated-symbol-master-comparison.json). Thus NXT membership alone does not explain missing integrated source. Regular KRX eligibility is present; the snapshot is not an intraday no-trade/halt receipt. The226330 audit-info exclusion is preserved separately and does not prove a market halt.
- A new, one-time fixed-generation same-day source census reads270,154,988 trade bytes plus332,495,930 depth bytes (602,650,918 total,15.863s). It projects only these24 symbols with original physical offsets/hashes; source growth beyond each pinned size is excluded. [Pinned generations and108 matching records](../../tmp/handoff-no-wire-20261023/same-day-market-brackets.json). All24 have0 records in the original transport epoch.22 have no matching records in that bounded observed day;023150_AL has31 trades/60 depths only09:05~09:08 in an earlier epoch, and007120_AL has5 trades/12 depths only12:15~12:17 in a later epoch. Unsubscribed intervals are not market observation coverage. No production reader or recurring full-source scan was added.
- The later007120 records bind through their collector epoch to current PID2333464/start36885727 and transport1792724342077867. [Exact PID binding](../../tmp/handoff-no-wire-20261023/later-item-pid-binding.json). That proves this exact integrated item can receive under the current process; it cannot close its original10:27 no-wire window. No case has comparable market-volume points bracketing the original interval. Latest-only queue values or the earlier/later observations cannot fill the absent original evidence.

Classification remains24 unresolved before the exact wire receipt, normal market silence confirmed0, subscription/collection failure confirmed0. The additional evidence narrows the uncertainty before native collector admission; it does not classify missing evidence as normal. Historical broker/item delivery and paired volume were not persisted, so the original market-versus-subscription cause remains unproved. No forced REG/REMOVE, source-only API call, timeout/TTL/guard change, source relabeling or manufactured receipt was used.

### Review scope, dispositions and next consumer

| Previous implementation/fixture | Disposition and current consumer |
| --- | --- |
| Hash-only parent stub and ineffective source_error injection | replaced in place with dated sealed parent closure and actual source tamper; the existing rollover script and native receipt reader consume it. |
| Foreign-selector fixture used to expect code mismatch | consolidated into exact-reader code checking plus explicit foreign-reader rejection; the existing validator remains the sole implementation. |
| Native handoff loader, origin receipt validation and predecessor review predicate | retained with current runtime consumers; no authority/expiry/source/custody relaxation. |
| Prior exact-probe outcome/claim repair | retained on selected ancestry through3efb7cb48; original46d41739a evidence remains intact. |
| Original24 no-wire cases and180s/REMOVE/NXT acceptance | retained under existing checklist owners; no absent sample or historical uncertainty is forced complete. |

This phase adds no module, worker, validator, report producer, entrypoint, schedule or compatibility wrapper, and has no deferred removal. Source delta0; tests1 existing file +55/-12; docs1 existing review +46/-0. The canonical generated checklist receives2 scoped progress bullets outside the code commit; concurrent checklist changes are preserved. Scoped review finds no remaining fixture defect; unknown historical origins and deployment/natural acceptance remain OPEN. The original strict checklist SHA91d9874a2fe47a5bcebe281c052ca65d0c978fe3477562557a7e735ae8b23011 is preserved with the selected native helper before checklist edits.

The existing `DirectFamilyPreopenPolicyHandoff` owns the closed test failures and any later authorized integration; `PreSubmitDelayFollowupSubscription1023` retains the24 origin uncertainties and exact natural collector-result/180s/REMOVE checks, while `PreSubmitDelayPremarketNxt1026` retains10/26 explicit NXT acceptance. [Current pin](../../tmp/handoff-no-wire-20261023/runtime-pin.json). Deployment/restart and live policy/PREOPEN/selector/provider/order actions performed by this task are0. A future natural lease must expose the original frozen volume/source kind/lease and actual collector outcome through the existing event chain after authorized integration. For no-wire cases, require an item-bound broker response or comparable existing bracketing market evidence; without it retain unknown origin. Test PASS is not a new candidate P5, actual PID consumption or economic acceptance.

## 2026-10-27 quote cadence evidence and monitoring plan

### 범위와 도입 근거

사용자 요청은 **0.7초 근거 확인·실제 갱신 간격 점검·보완방안 구체화, 매수 안전가드 유지**다. 이번 변경은 분석 artifact와 기존 계획/감사 문서뿐이다. 구현·테스트·장후 재계산·정책 발행·구독 조작·배포·재기동을 수행하지 않는다. 구현 설계의 소유자는 [기존 계획 §4.6](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md#46-호가-갱신-대기수집-결함-분리-보완안--2026-10-27)이다.

- `0291c575cd752c23290de173020647826d3bd235` (`2026-09-23T14:14:45+09:00`)의 최초 지연 관측 구현부터 `0 <= depth_age <= 0.7`을 직접 사용했다. 확인한 도입 commit/연결 계획에는 종목별 갱신 분포·오탐·가격 위험을 비교해 0.7을 선택한 실측 근거가 없다. 최적 제출 지연시간을 뜻하는 값도 아니다.
- 9/28 `d8aa4a646f81917ef4a39b72c3eebbc4d7ee686b`은 exact route/epoch/depth와 장후 검증을 강화했고, 9/30 `3d893a1c23a28fe1c00ac1eb9faaa98ea886c515`은 연구용 0D 신선도를 trade mark가 필요한 runtime normalizer와 분리했다. 0.7초는 유지했다. [10/2 계획](../proposals/pre-submit-delay-price-pattern-calculation-remediation-plan-2026-10-02.md#32-짝짓기와-결손-처리)의 0.7초도 기존 기준 보존을 명시한다.
- 10/24 `2f1182f33c8844b802561c7cb601c5c65be4d9c1`의 blame은 formatting 결과이며 값의 최초 도입이 아니다. 현재 `QuoteConsistencyConfig`와 pre-submit refresh에도 700ms 기본값이 있지만, 같은 숫자라는 사실만으로 연구 기준의 실측 근거/동일 authority를 증명하지 않는다. 실제 매수 guard 설정이나 effective value를 이번 분석으로 변경하지 않는다.

### 고정 생산자 모집단과 실측

원 경보는 10/27 08:17:02 KST, release `59a922b1952085dbe268b331a808a5f4062047d8`, PID `3905944`의 자료다. [native 종료 영수증](../../data/runtime/scalp_micro_reversion_forward_collector/closed/2026-10-27-1793055359210484568.json)의 `sequence_epoch=1793055359210484568`, `transport_epoch=1793055359295799`를 고정했다. 분석 시 선택본 `ab663e13b69b1d1edae1e645d8c5c7ad3e8afc16`/PID `3940489`의 새 입력과 합치지 않았다. 원 bootstrap의 release SHA와 PID verify도 앞선 알림 분석에서 확인했다. source 시각은 offset을 가진 `local_receive_timestamp`의 계약대로 해석했다.

[분석 JSON](../../tmp/pre-submit-delay-quote-cadence-20261027/analysis.json)에 exact 경로·prefix bytes/SHA·source stat·collector counter·종목별 분포·원 quote offset/행 SHA를 기록했다. 종료된 생산자의 NXT prefix `40,456,396` bytes/`32,053`행과 SOR prefix `146,423` bytes/`114`행의 합이 종료 영수증의 depth persisted `40,602,819` bytes/`32,167`건과 일치한다. 후속 append는 읽지 않았다. 관측창은 `08:00:01.484~08:20:43.280 KST`, exact item/cohort/session 조합은 37개다.

같은 symbol/item/session/transport epoch의 연속 로컬 수신 시각 차이로 계산했다. 분위수는 양수 간격의 선형 보간이다. 동일 ms의 정상 복수 수신 51개는 별도 보존했고, native sequence의 역행/건너뜀은 0이다. 이 sequence는 로컬 생성값이며 증권사 송신 sequence가 아니다. per-item 연속 구독 세대가 모두 복원된 것은 아니므로 아래는 기술 통계이며 그 자체로 정상 무거래·연속 구독·대기 상한을 인증하지 않는다.

| NXT item | 0D 수신 수 | P50 간격 | P95 간격 | P99 간격 | 최대 간격 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `005930_NX` | 6,251 | 0.200초 | 0.234초 | 0.379초 | 0.663초 |
| `034020_NX` | 4,980 | 0.201초 | 0.568초 | 0.800초 | 1.401초 |
| `196170_NX` | 1,682 | 0.486초 | 2.201초 | 3.453초 | 6.600초 |
| `437730_NX` | 3,178 | 0.201초 | 0.604초 | 1.000초 | 1.800초 |

196170의 양수 간격 1,681개 중 600개(35.69%)가 0.7초보다 길었다. 연속 수신 사이에서 `sum(max(gap-0.7,0))/sum(gap)`로 계산한 경과시간 비율은 35.74%다. 이는 **실제 intent 무효율이나 경제성 수치가 아니다**. 전체 혼합 분포의 최대 281초는 다른 item의 등록/lease 창 미확정 구간을 포함하므로 정상 대기 범위의 근거로 사용할 수 없다. 정규장·애프터·다른 날짜로 일반화하지 않는다.

### 원 intent 대조와 확인 한계

원 intent는 `6aa333b9cc81be3b0fec38bfe2edec97b3dc7f6b7a8af21366766de5dde0c1bf`, 기계 `ENTER_NOW`/보조 `PASS`, session `krx_like_premarket`, data item `196170_NX`, 관측 route `NXT_ONLY`다. 이 intent는 연구 `signal_ready` anchor이며 실제 broker 제출 route나 체결 venue 증명으로 사용하지 않는다. 동일 평가 `aims-d3d9d39ddcf6cf8f7cda`의 제출 경로는 `08:14:55.818` `latency_state_danger`/`quote_stale` 차단, `08:14:55.821` `entry_submit_attempt_finished=returned_false`다. 실제 체결 venue는 이 근거에서 미확정이다.

| Horizon | 호가 age | 원 판정 | 직전→다음 실제 0D 간격 |
| --- | ---: | --- | ---: |
| 0초 | 2.321초 | invalid | 3.399초 |
| 1초 | 3.331초 | invalid | 3.399초 |
| 3초 | 0.722초 | invalid | 1.200초 |
| 5초 | 1.523초 | invalid | 4.001초 |
| 30초 | 2.358초 | invalid | 3.596초 |
| 60초 | 0.521초 | valid | 1.401초 |
| 120초 | 0.021초 | valid | 1.812초 |
| 180초 | 0.801초 | invalid | 2.071초 |

전 8개 관측의 `ws_last_0d_epoch`는 그 관측 시점까지 저장된 해당 item/transport epoch의 마지막 0D와 일치했다. 원장 source row SHA도 기록했다. 0·1초는 `08:14:52.785` 뒤 다음 수신 `08:14:56.184` 전에 발생했다. 정상 수신된 최신 호가를 조회에서 놓친 증거는 없다. age는 모두 양수이며 due offset도 허용창 안이다. 고정 생산자의 depth queue/worker/writer drop·error와 invalid depth clock/snapshot은 0이다. 나중의 같은 가격/정상 수신으로 과거 무효를 유효로 복원하지 않는다.

같은 원 prefix를 재검증하여 미래 자료 없이 각 horizon 직전 10분의 최근 양수 간격 512개를 계산했다. P99는 0/1/3/5/30초 시점에 각각 `3.201/3.201/3.225/3.225/3.380초`였다. 1초 관측 age `3.331초`는 이 과거 P99도 약 `0.130초` 넘었다. 이것 역시 고장 증명이 아니다. 이 자료에는 해당 Main의 완전한 구독 세대와 wire→normalizer 전달 P99 결속이 없으므로 `expected_wait` 확정으로 사용하지 않는다. 사후 정상 quote나 전체 관측창 분위수로 당시 원인을 닫지 않는 반례로 보존한다.

따라서 **0.7초 초과는 확인됐고, 로컬 quote 조회→저장 결손은 확인되지 않았다**. 당시 item별 pre-normalization wire/연속 구독 증거와 증권사 송신 이력이 충분하지 않아 정상 미송신과 upstream 전달 결함까지 구분한 것은 아니다. 기존 `quote_valid=false`를 곧바로 원장 결손으로 설명하는 감시 방식이 이 구분을 가렸다. 보완안은 원 자격을 보존하면서 ledger integrity/quote eligibility/collection health를 독립 표기하고 미확정 경계를 공개한다.

### 검토·대체·완료 경계

- 기준 workspace commit은 분석 JSON의 `1756de1d9d7943739d539d5207cc55484185bff5`다. 이 작업은 기존 proposal/audit만 보완하고 비테스트 source/test 변경은 각각 0이다. 관련 없는 기존 dirty 문서·config·Python과 현재 생성 checklist는 건드리지 않는다.
- self review에서 전체 혼합 최대 간격의 정상화 금지, 현재/과거 생산자 분리, probe-only lease의 Main 오용 금지, future quote/사후 분포 누출 방지, same-ms 수신과 시계 역행 구분, 입력 부족 시 정상 판정 금지를 보완했다. 문서상 초안의 통계 창/표본수는 운영 설정이 아니며 실측 검증 전 임의 runtime 값으로 쓰지 않는다.
- 대체 예정은 monitor의 단일 generic-loss 설명이다. 원 0.7초 연구 reader·호가 원문·매수 guard·역사 자료는 현재 consumer가 있어 유지한다. 신규 module/validator/wrapper/worker/cron이나 별도 실행 owner를 만들지 않는다. 제거·수리 구현은 이번 문서의 완료 주장이 아니다.
- 문서 검증: `git diff --check` PASS, 새 링크/anchor 6개 PASS, print-only backlog parser 22개 항목 파싱 PASS. 원 source prefix 재검증도 일치했다. 보완 리뷰에서 정상 종료의 censor와 예기치 않은 REMOVE, 등록 요청의 실제 type 누락과 단순 무수신, 정상 매수 guard 차단과 수집 결함을 추가로 구분했다. [검증 영수증](../../tmp/pre-submit-delay-quote-cadence-20261027/document-validation.json). trading test/provider/정식 장후 재계산은 실행하지 않았다. 구현·원천 새 세대·배포·실제 PID 소비·자연 갱신 수용·경제성은 모두 미수행이다. 구현 후에도 현재 확인하지 못한 원 wire/구독 이력을 합성하거나 정상 무거래로 닫지 않는다.

## 2026-10-27 quote cadence implementation review

### 구현 범위와 상태

후속 사용자 지시로 [기존 계획 §4.6](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md#46-호가-갱신-대기수집-결함-분리-보완안--2026-10-27)의 갱신 대기/수집 결함 분리를 구현했다. **코드·오프라인 재생 검증 완료, 배포·재기동 대기**다. baseline `1756de1d9d7943739d539d5207cc55484185bff5`, branch `codex/pre-submit-cadence-20261027`, code root `/home/ubuntu/KORStockScan-worktrees/pre-submit-cadence-20261027`다. canonical의 다른 dirty source/config/docs는 구현에 섞지 않았다. 앞선 계획 수립 단계의 미수행 상태는 당시 이력이며 이 절이 후속 구현 결과다.

공식 Kiwoom reference gate는 [고정 증거](../../tmp/pre-submit-delay-quote-cadence-20261027/official-reference.json)에 current remote HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, 실제 조회 시각, inspected file SHA를 기록했다. packaged 0B/0D meta/request/response·REAL decoder·REG/REMOVE envelope·core/spec/Postman을 확인했다. 해당 revision에 `kiwoom_docs`가 없는 한계는 유지한다. 새 wire/FID/ACK 의미나 broker venue를 추정하지 않았으며 protocol/request/parser mapping·auth·주문 호출은 바꾸지 않았다.

### 생산자에서 감시기까지

1. **Main/probe 수신 계수:** 기존 REAL ingress에서 정확 item별 native 등록 세대와 wire ID를 기록한다. 등록 세대는 PID/epoch/등록 serial로 구분하므로 같은 시각 재등록도 별개다. 프레임의 객체 결속 token으로 새 등록/세션/epoch에 이전 wire 영수증이 들어가지 않게 한다. 기존 probe receipt도 같은 단일 owner에서 유지한다.
2. **정규화와 호가 신원:** 같은 wire가 도달한 정규화 수·시각·native route sequence를 연결한다. source cache와 계수의 native sequence가 다르면 같은 ms라도 정상으로 합치지 않는다. 원 native ms 단위 clock 정밀도를 보존하고 wire→normalization 지연은 그 정밀도를 포함한 상한으로 계산한다. 단순 처리 중 pending은 고장으로 확정하지 않으며 이후 정상화된 wire ID가 앞선 누락을 증명한 경우 구분한다.
3. **두 조회 경로:** Main의 `get_latest_data`와 기존 sampler의 `get_pre_submit_delay_depth`가 같은 진단 helper를 사용한다. WS lock 안에서는 bounded scalar/interval view만 복사하고 lock 밖에서 분위수를 계산한다. 진단 값은 원 quote 발생시각과 source hash를 바꾸지 않으며 저장된 quote의 route sequence/depth digest에 결속한다.
4. **전달/소비:** 기존 raw→index/summary/compact는 full fields와 exact event hash를 이미 보존하므로 새로운 생산자나 중복 원장을 만들지 않았다. 감시 cursor v5가 새 scalar 증거를 보존하고 v4는 native bounded migration으로 인계한다. `quote_eligibility_counts`와 `collection_health_counts`를 분리한다. 정상 종료·censor는 기존 horizon/terminal owner에 남기며 가짜 quote를 만들지 않는다.
5. **분류와 알림:** 오래된 quote 자체는 수집 고장 확정이 아니다. 충분한 같은 세대의 구독/수신/정규화·저장 증거와 과거 분포가 있으면 `expected_wait`, 범위만 초과하면 `cadence_exceeded_unproven`, 부족하면 `unobservable`이다. 정확 등록 type 누락·wire→normalization 손실·clock/identity 손상 및 기존 raw/summary/compact 결손은 계속 탐지한다. 독립 depth writer의 drop/reject 검출 owner도 유지하며 그 전역 zero counter를 item 건강성으로 대입하지 않는다.
6. **의미 있는 재발:** 원인 코드만 같아도 새로운 exact 실패 event ID·scope·증가한 영향은 다시 알린다. 변하지 않은 동일 증거는 중복 통지하지 않는다. 과거 raw의 무효를 지우거나 경보 억제로 회복 처리하지 않는다. 원인 미확정 전용 알림은 수집 결함 확정 수와 연구 무효 수를 함께 표시한다.

### 반복 리뷰에서 보완한 지점

- 같은 시각 재등록의 문자열 identity 충돌, wire 수신과 정규화 사이의 등록 교체, 같은 ms의 다른 route sequence를 별도로 보완했다. 명시적 등록 누락과 단순 무수신, 미래/역행 clock과 정상 ms 정밀도, stale 진단 snapshot과 새 증거를 혼동하지 않는다.
- 현재 구독/관측 owner의 `MAX_ACTIVE=128` 안에서 item 상태를 추적하고 각 deque는 512개다. 상한에 닿아도 native 구독/등록을 막거나 cap을 늘리지 않는다. 진단 범위 부족만 미확정으로 드러낸다. REMOVE/재등록/epoch/세션/날짜가 바뀌면 이전 기준을 재사용하지 않는다.
- 최초 성능 리뷰의 매 조회 분위수 재계산을 제거했다. 동일 wire/normalization 세대의 scalar 요약 한 개를 공유하고 rolling window의 첫 만료·세대 변경·이른 과거 재생에는 재사용하지 않는다. cache는 공개 quote/WS payload에 들어가지 않는다.
- 0.7초는 연구 owner의 `MAX_RESEARCH_DEPTH_AGE_SEC` 한 곳으로 모아 기존 관측/장후 검증/분류가 같은 값을 읽는다. 값은 그대로다. runtime guard ENV/config의 700ms 또는 다른 effective 값은 이 상수로 대체하지 않는다.
- 마지막 재리뷰에서 회복 scope를 route·종목·commit 세션에 결속했다. 다른 종목/세션의 정상 수신으로 원 결손을 회복 처리하지 않는다. 같은 scope의 새 정확한 healthy receipt만 현재 구간의 회복 근거로 쓰며 과거 원천 복원은 여전히 false다.
- 추가 재리뷰에서 누적 정규화 누락 하나가 이후 정상 호가까지 계속 고장으로 표시하는 결함을 발견해 수정했다. 누적 누락은 보존하고 현재 normalized wire 대응과 실제 native route sequence를 독립 검증한다. 정규화되지 않은 wire와 손실을 가로지르는 간격은 baseline에 넣지 않는다.
- 손실 시각·등록/세션/날짜/epoch/item·native loss marker로 고유 ID를 만든다. 여러 horizon이 같은 손실을 보아도 고장 event는 한 건이며 관측 수는 별도다. 조회 사이에 손실 후 회복해도 기존 10분 감시 창 안이면 탐지하고, 창 밖 과거 누계만으로 현재 장애를 만들지 않는다. 새 손실 ID는 다시 알린다. 현재 호가 건강성과 최근 손실 event는 동시에 표시할 수 있다.
- 첫 원 intent fixture의 as-of가 기존 20초 저장 유예 안에 있었던 검증 실패는 fixture 시각을 원 계약 이후로 고쳐 재검증했다. 원 production 유예·horizon·freshness를 늘려서 통과시키지 않았다.

### 원 intent 재생과 신규 결손 회귀

[원 intent 재생 영수증](../../tmp/pre-submit-delay-quote-cadence-20261027/original-intent-replay.json)은 실제 native quote 8행의 원문 SHA를 검증하고 임시 data root에서 세 저장 경로를 재생했다. 원 `08:17:02` alert 창의 **연구 무효 5건/수집 고장 확정 0건**, 180초 수신과 원 20초 유예 이후 `08:18:30` 창의 **무효 6건·유효 2건/고장 확정 0건**을 확인했다. 앞선 창의 유효 건수에는 같은 원천 유예가 적용되므로 전체 visible horizon 건수와 단순 비교하지 않는다. 원 구독/wire 이력을 합성하지 않아 원인 미확정은 남는다.

원문 fixture와 별도 synthetic variant를 명확히 분리했다. 현재 정상 캐시를 읽는 실제 WS handler→quote producer에서는 **0.8초 age를 연구 무효로 유지하면서 갱신 대기**로 진단한다. 같은 handler에서 values 없는 wire 뒤 정상 wire를 넣으면 누락된 정규화 ID가 검출되며, 새 quote 자체가 fresh여도 수집 손실을 탐지한다. 후속 정상 wire의 현재 건강성 회복·누계 보존, 여러 관측의 단일 손실 집계, 관측 사이 손실/회복 탐지, 감시 창 밖 과거 손실의 비활성, 새 독립 손실 통지와 등록 type 누락·epoch/item/depth hash 불일치·native sequence 불일치·future/stale clock·표본 부족·오래된 진단·compact 행 삭제·동일 원인의 새 실패 ID도 회귀에 포함했다.

격리 worktree의 config 기본 파일 부재로 standalone test-helper import 경고가 있었으나 실제 account/provider/API 호출 없이 명시적 임시 data root만 사용했다. 운영 데이터 손상으로 해석하거나 설정/원 데이터를 수정하지 않았다.

### 검증과 성능 한계

- 최종 [7개 영향 suite](../../tmp/pre-submit-delay-quote-cadence-20261027/final-regression.json) **2,005 PASS**, 실행 중 source/test SHA 변경 0. 이전 반복의 129/1,994/1,996/1,997 PASS와 cache 이전 세대 영수증도 보존했다. 기존 `pandas_ta`의 pandas deprecation warning 1건이 있으며 dependency를 바꾸지 않았다.
- [안전가드 동등성](../../tmp/pre-submit-delay-quote-cadence-20261027/guard-parity.json): 다른 sniper 함수 **1,279개 AST 불변**. 해당 관측 함수도 진단 첨부와 같은 값의 상수 참조만 정규화하면 원 AST와 같다. 원 quote 8개의 source SHA도 모두 같다. source/test 8파일 compile과 diff check를 수행했다.
- [성능 측정](../../tmp/pre-submit-delay-quote-cadence-20261027/performance.json): wire hook P99 **0.001576ms**, 5단 book source 조회 warm P99 **0.036694ms**, 새 표본마다 재계산한 cold P99 **0.241711ms**다. 기존 8-symbol sampler budget에 곱한 cold 값 **1.934ms**는 기존 50ms turn 안이다. 추가 worker/구독/원천 전수 스캔은 없다.
- 128상태·각 512개 interval/delivery·채워진 summary cache를 둔 합성 allocation peak는 **13,507,560 bytes(12.88MiB)**다. 이는 full process RSS나 실제 장중 callback/PID 성능 수용이 아니다. 운영 배포를 하지 않았으므로 자연 부하 수용은 아직 없다.

### 대체·제거와 인계

| Old path / branch | Disposition and consumer |
| --- | --- |
| `_record_exact_probe_wire_receipt` | removed/consolidated into `_record_source_wire_receipt`; existing REAL dispatcher and probe tests migrated; no compatibility wrapper |
| Invalid quote always explained as generic source loss | replaced by independent eligibility/collection diagnostics in existing monitor; original invalid rows remain excluded |
| Repeated quantile calculation for unchanged source | replaced by one generation/window-bound scalar cache; current Main/sampler readers share it |
| Cumulative normalization loss poisoning all later quotes | replaced by current native sequence accounting plus a time-bound, deduplicated loss event; original loss total retained |
| Duplicated research 0.7 literals | consolidated under existing research owner; runtime safety config/guards retained |
| Native writer/index/summary/compact and independent depth collector | retained with current direct consumers; no new producer, validator module, entrypoint, worker or cron |
| Historical unknown wire source and original raw/failed attempts | retained as evidence; no healthy/no-trade/economic claim |

비테스트 source **5파일 +679/-23**, tests **3파일 +705/-4**와 원문 fixture **1파일 +79행/23,343 bytes**다. 이 외 문서는 기존 2개 owner의 계획·증거를 보완한다. source 증가는 등록 세대·bounded cadence·정확 원천 결속과 분류/알림에 해당하며 module 이동이나 복제 구현은 없다. 제거 완료를 미룬 실행 wrapper는 없다.

현재 checklist의 `PreSubmitDelaySituationResearch1017`로 새 source-classification 결함의 코드 종결과 배포 대기를 인계한다. 다음 단계는 사용자 배포 지시 후의 통합/불변 후보/native active-policy handoff/P5·정식 전환과 실제 새 PID의 동일 source branch 관측이다. 기존 `DirectFamilyPreopenPolicyHandoff`의 운영 전환 소유권은 유지한다. selector/PREOPEN/policy/env·provider·수량·안전가드·실주문·배포/재기동 변경은 **0**이며, 현재 운영 알림에 이미 적용됐다고 주장하지 않는다.
