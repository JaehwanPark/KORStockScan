# Main 손절 실제 판단·수량·선정 후속 검토 — 2026-10-18

사용자의 다음 액션 실행 지시에 따라 [계획 §14](../proposals/main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md#14-후속-실행--실제-판단수량-원천과-선정-계약)를 같은 격리 작업본에서 수행한다. 불변 후보 검증(P5)은 모든 연구작업 종료 후로 보류하며 이번에 실행하지 않는다. 기존 [R1 실행 기록](main-stop-research-execution-and-source-contract-repair-review-2026-10-18.md)과 원 실패/성공 bytes를 보존한다.

- 실행 owner: [MainStopResearchExecution1018](../checklists/2026-10-18-stage2-todo-checklist.md).
- 작업본: `/home/ubuntu/KORStockScan-worktrees/main-stop-research-20261018`, 출발 `ad7cb200e0915f917326a644fe112d4ca5fe2120`.
- 후속 증거: [contract-followup](../../tmp/main-stop-research-20261018/contract-followup). 시작 영수증이 원 선택 selector·10/16 보고서·10/19 준비 stop 정책3개 SHA를 고정한다.
- source-only 코드·격리 연구 수리다. 공유 workspace 실행 소스 overlay/merge, 정책/selector 변경, 외부 API/provider/구독/주문, 배포·Main 재기동·P5를 실행하지 않는다.

## 변경과 수용 경계

1. 기존 공유 quote와 실제 evaluator/stage 판단을 분리한다. normal preset의 조기 종료·fast 안전·normal common-soft 호출점에 각각 작은 원천 영수증을 결속한다. fast_prearm은 quote-only이며 normal soft 시계를 전진시키지 않는다.
2. native BUY receipt maps의 실제 이름·정수1 경제 완결성·주문별 누적량/금액/잔량과 terminal bundle을 순수 bounded quantity proof로 묶는다. full/settled partial/unknown과 가용시각을 보존하며 metadata clear 전 증명을 보존한다. legacy probe abort/rebase의 `FULL_FILL`은 원 목표·미체결 terminal 증명이 아니다.
3. source index와 replay가 동일 시각의 서로 다른 실제 평가세대를 보존하고 원 quote를 변경하지 않는다. 지원 구간·원천 미지원·preset 선행 비도달을 전수 census와 경제 분모에서 구분한다.
4. 선정의 단일 비용 grade를 사전 등록하고 원본 비용 등급·배분의 연구 범위를 보존한다. 실제 종료비용과 후보 종료의 causal 비용 모델을 구분한다.
5. 실제 capture/sink/reader 성능 producer가 측정 범위·코드/원천·tail·누락·제외 단계를 봉인한다. 전체 Main 지연이 측정되지 않았으면 정규 성능 PASS가 아니다.

## 검토 중 발견한 보완

- actual evaluation의 수량·유예 상태·비용/AI 참조는 공유 quote가 만들어진 과거 시점의 상태를 그대로 소비하지 않고 실제 판단 시점에 결속한다.
- queue 손실은 다음 판단의 세대/거절 계수에 남긴다. 동일 시각·동일 evaluator/stage의 다른 실제 generation과 동일 generation의 conflicting body를 구분한다.
- normal preset의 mark 기준 판단과 별도 executable bid를 혼동하지 않는다. legacy preset skip을 common-soft 선행 차단이라고 판정하지 않는다.
- 새로운 원천 계약은 과거 미기록 판단과 체결을 생성하지 않는다. 역사 재점검은 봉인 index와 선택행 bytes의 현재 검증 범위 및 원12GB 검증 당시 영수증을 구분한다.

## 생산·소비 연결 보완

| 구간 | 구현·검토 결과 |
| --- | --- |
| 수량 원천 | 새 `scalping/main_stop_quantity_source.py`가 기존 BUY 생산자 출력과 exact 주문 census/금액·잔량·terminal을 검증한다. 최대32주문/256체결·64KiB·노드/깊이 예산을 먼저 검사한다. `FULL_FILL`, notice, map 만료로 terminal을 추정하지 않는다 |
| 재기동 복원 | 기존 BUY identity 복원 성공 뒤 기존 terminal index/journal을 bounded reader로 대조한다. native reader의 두 번째 읽기도 같은 bounded callback을 사용한다. active bundle·수량/목표/시각/경로 불일치는 복원하지 않는다 |
| 실제 판단 | 새 `scalping/main_stop_runtime_source.py`와 실제 normal preset/common-soft·fast 안전 호출점을 연결한다. 현재 수량·유예/touch·handoff·비용·원 AI source를 봉인한다. 독립 mark clock이 없으면 native gate argument라는 사실을 보존한다 |
| 동일 시각·손실 | quote/evaluation별 세대와 공통 observation 세대로 같은 시각의 실제 순서를 보존한다. 동일 세대의 body 충돌은 오류다. 같은 포지션의 기록 실패는 다음 receipt에 남기고, 실제 native 신규 포지션 reset에서만 새 임시 counter/cache를 초기화한다 |
| bounded 재생 | 공유 quote identity와 실제 평가 시점의 수량 증명·작은 평가 reference를 결속한다. 실제 normal common-soft만 soft 시계를 전진시킨다. 지원 구간 앞의 전체 후보/부모 무청산 동등성과 마지막 normal→실제 종료 bridge를 확인한다. 미지원 초기 구간·LRU 예산·전체 coverage census를 보존한다 |
| 원 AI source | first shared quote의 과거 ref 대신 실제 평가 시점의 ref를 조립·소비한다. stop `target:{id}:{code}`와 AI `record:{id}`를 native record 규칙으로 연결하고 현재 수량 증명과 BUY identity를 대조한다. 기존 원 입력/응답과 store를 사용하며 원 AI를 재생성하지 않는다 |
| 비용·선정 | 단일 사전 등록 비용 grade와 full/settled-partial cohort를 구분한다. native 완료 census·비용 세대를 정규 publisher에 연결한다. unknown을 전체 검열 분모에서 지우지 않고, 후보 가상 청산에 실제 종료비용을 넣지 않는다 |
| 장후 준비·최종 소비 | 성능 전 source seal과 비공개 준비 계산을 허용한다. 준비물에는 정책 권한·운영 pointer가 없다. 최종 소비는 같은 등록/source/code/cost/통계/census·operator를 검증하고 replay 재실행 없이 결과를 승계한다 |
| 신규 선정의 성능 권한 | 비용 grade를 생략해 legacy 수기 성능 PASS로 신규 수치 정책을 발행하는 우회를 차단한다. 신규 실험/선정 발행과 기존 승인 artifact의 의미 검증·읽기를 구분하며 초기 부모 승계에는 새 조건을 붙이지 않는다 |
| 로더 성능 | 발행 시 검증한 dependency stat·archive custody를 routine 의미 검증에 재사용한다. 변조·부재·원천 추가와 잘못된 archive는 거부하고 full preflight의 byte 검증은 유지한다. approved incumbent code handoff도 이 검증 안에서 수행한다 |

독립 리뷰에서 재기동의 두 번째 무제한 읽기, 동일 시각 quote 충돌, stale 실제 입력/투표 ref, 초기 지원 quote의 메모리 예산 소유, 다음 포지션으로 남는 실패 counter, archive 이후 loader 재독해 및 성능 전 source seal의 순환을 확인해 보완했다. 통합 회귀 뒤 추가 검토에서는 수량/원 AI BUY 세대 대조 누락과 다른 형식의 stop/AI key 연결을 보완했다. 마지막 권한 검토에서 optional grade 생략에 따른 신규 성능 검증 우회도 확인해 보완했다. Kiwoom 요청·응답 parser/FID·인증/REG/REMOVE·주문 protocol은 변경하지 않았으며 기존 확보 원천을 소비한다.

## 실행·검증 확정

격리 소스 commit은 `9e78afd1194233d87c4d340ba2f1981d340d88d4`다. 소스25파일 변경을 commit했고 작업본은 clean이다. 이는 소스 검증 결과이며 P5 후보 준비·실행 또는 운영 적용 영수증이 아니다. [최종 code closure](../../tmp/main-stop-research-20261018/contract-followup/code-review-closure.json)는 코드·입력·실측·시험·보호 해시를 결속한다.

| 검증 | 최종 결과·원본 |
| --- | --- |
| 통합 회귀 | [attempt-03](../../tmp/main-stop-research-20261018/contract-followup/final-validation-attempt-03/validation.json) **809 PASS**, 경과89.116초. 19개 표적 모듈과 실제 holding 복원3개 test node를 같은 명령으로 검증. 개별/과거 시험 수를 합산하지 않음 |
| Compile·diff | [25파일 compile와 diff-check](../../tmp/main-stop-research-20261018/contract-followup/compile-and-diff.json) PASS. native protocol/셸 변경이 없고 P5·배포 검증은 수행하지 않음 |
| 실제 역사 원천 | [census attempt-03](../../tmp/main-stop-research-20261018/contract-followup/historical-support-census-attempt-03/report.json): 선택 index56,980관측/15포지션, `source_gap=15`, 지원 판단/구간0. REGULAR9·AFTERMARKET6. 실제 evaluator·수량 receipt를 과거 quote로 생성하지 않음 |
| 검증 범위 | 기존14 index seal과 선택 raw 행 bytes를 현재 검증. 과거 index byte SHA 외부 고정 및 이번12GB 전체 재해시는 모두 false. [전체 CLI](../../tmp/main-stop-research-20261018/contract-followup/historical-support-census-attempt-03-cli.json)41.718초, 내부 CPU25.039초/RSS40,684KiB. 동시 회귀·cache 조건이 있어 이전 실행과 속도 개선을 비교하지 않음 |
| 실제 성능 producer | [측정](../../tmp/main-stop-research-20261018/contract-followup/performance-measured.json): 고정3시나리오·3교대쌍,66행 append/readback·누락0. capture arm별9표본의 p95/p99는 부모4.040ms/후보2.276ms. 작은 fixture의 부분 측정이며 성능 우위·전체 Main PASS를 판정하지 않음 |
| 중복 증명 축소 | [256체결 microbenchmark](../../tmp/main-stop-research-20261018/contract-followup/quantity-reference-attempt-02/quantity-reference-256fill-result.json): 두 알고리즘 각50회, 중앙값10.045→4.591ms. preset38,695→2,694B/common38,909→2,908B, 공유 quote38,553B 유지. 이전 중복 알고리즘을 재구성한 비교이며 과거 릴리스/전체 Main 비교가 아님 |
| 운영 보존 | selector·원10/16 연구 보고서·10/19 준비 stop 정책3개 SHA가 시작과 동일. 공유 실행 소스 overlay·정책 발행·provider/주문·재시작·P5·외부 sync0 |

최종 연구 코드 SHA는 `47bb07a6aa094bcbb8bdcfaa6ebbfca7b677e2a42450f9b7e4cf446f16373e5f`, runtime family SHA는 `186be016c9f5f38f080d998871567df175e634188cf8e2a2352584e620f835bc`다. 최종 census·실측·회귀가 같은 세대를 사용했고 실행 전후 변경이 없다. microbenchmark의 실행5구현·입력·script SHA도 최종 파일과 일치한다.

조건부 preset 참고 metadata는13포지션에 있으나 normal owner/동일 가격·시각 등 가정이 미확정이다. 실제 `unreachable_observed`나 손절 성과13건으로 해석하지 않는다. 이번 census는 경제성을 다시 계산하지 않았고 정책을 선정하지 않았다. 과거 결손의 결론은 손절 실적 축적 대기가 아니라 당시 실제 판단/수량 원천의 복구 불가 및 coverage 결손이다.

중간 [회귀 attempt-01](../../tmp/main-stop-research-20261018/contract-followup/final-validation-attempt-01/validation.json)의790 PASS/2 FAIL은 원본으로 보존했다. 실제 gate가 없는 ADD 모델 완료 기대를 미지원·순수 hard 우선순위 검증으로 나누고, 원 AI 시험은 native BUY/평가/record-key를 연결했다. 생성 뒤 request/payload/prompt/store bytes와 membership 불변을 검증했다. 이후799 PASS 세대에서 발견한 신규 성능 권한 우회까지 보완하여 최종809 PASS로 종결했다. 앞선 census/benchmark·원 실패도 덮어쓰지 않았다.

성능 CLI의 격리 작업본 `config_dev.json` 부재 import 로그도 보존했다. 측정 child는 native 함수 import 전에 외부 연결/프로세스 실행을 거부하고 private fixture·sink를 사용했다. 해당 로그를 실제 운영 설정 로딩·provider 호출·전체 Main 실행으로 간주하지 않는다. 문서 종결은 print-only parser·단일 현행 owner·로컬 링크/권한 경계 검사로 확인한다.

## 남은 연구와 P5 경계

현재 capture 성능 producer는 native context/pin·영수증·bounded queue·직렬화·reader를 실제 실행한다. 입력은 봉인 offline fixture다. 전체 Main wake/lock/holding/fast/claim/final guard·동시 장후 selector와 발행의 실측 PASS는 아직 없다. `run_sniper`의 실제 한 회차와 private external-adapter/ledger 실행 경계를 분리하고 동일 고정 입력3회 교대·누락/중복/새 만료0·tail/자원 한도를 측정하는 잔여 구현을 같은 `MainStopResearchExecution1018`이 소유한다. 이 결손을 자연 손절 표본 부족으로 바꾸거나 수기 PASS로 넘기지 않는다.

기존 한 cell 실험/canary 승인 경계는 유지한다. 비어 있지 않은 선정→publisher→loader 양성 fixture가 성능 gate를 격리한 경우 그것은 해당 연결 검증이며 실제 full Main 성능·운영 발행 증거가 아니다. 기존 초기 승계에 새 경제성·자연 표본 gate를 추가하지 않는다.

과거 미지원 cell은 미지원 결론으로 현재 연구를 끝낼 수 있다. 새 원천의 운영 수집·자연 청산/경제성은 기존 수용 owner에서 이어가며 P5 전에 새 producer 배포를 요구하는 순환을 만들지 않는다. **P5는 모든 연구작업 종료 후 코드·원천 세대를 다시 고정해 실행한다.** 이번에 P5·운영 배포·재시작·정책/selector 변경은 실행하지 않는다.
