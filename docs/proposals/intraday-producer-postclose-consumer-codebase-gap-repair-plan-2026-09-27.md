# 장중 생산자–장후 소비자 전 코드베이스 결손 점검·보완 계획

작성일: 2026-09-27 KST

상태: **계획 수립**. 아래 단계의 점검·수리·배포를 수행했다는 뜻이 아니다.

## 1. 목적과 범위

장중 실행 경로가 생성해야 할 원천과 장후 분석·정책·감시 경로가 실제 읽는 입력을 **전체 코드베이스에서 역방향과 순방향으로 대사**한다. 발견한 결손은 소유 경로별로 작은 수리 단위로 나누어 재검토한다. 한 번의 요청은 아래 **한 단계만** 실행하며, 단계 결과·잔여 결손·다음 단계 착수 조건을 기록한다.

범위는 활성 main/scalping, scanner, 진입 기계·보조 AI, 주문·체결·취소, 보유·청산·원가/손익, widget/episode의 별도 owner, 관측·source-quality, 장후 wrapper·family producer·summary·strict verifier·finalizer·PREOPEN loader와 선택 릴리스까지다. Swing OFF, sim/source-only, retired 경로도 **실제 생산·소비 누출 여부만** 조사한다. OFF 표본 부재를 복구 결함이나 live 승격 근거로 취급하지 않는다. 열거된 이름은 시작점일 뿐이다. `src`, `deploy`, 설정·스케줄·등록 테이블의 전체 후보를 수집하고, 코드 import/call, wrapper·cron/systemd 진입점, 산출물 writer/reader와 런타임 선택 경로를 교차 대사해야 범위가 닫힌다.

기준 문서는 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [현행 산출물 추적 계약](../report-based-automation-traceability.md), [2026-09-28 실행 checklist](../checklists/2026-09-28-stage2-todo-checklist.md)다. 일별 실행 소유권과 family별 기존 OPEN 항목을 새 공통 계획으로 덮어쓰지 않는다. Clean tuning 기준은 `2026-06-05T00:00:00+09:00`; 그 이전 자료는 구조 감사만 가능하다.

## 2. 조사 원칙과 공통 산출물

각 연결을 `producer 함수/실제 호출자 → 원천 파일·DB·event 및 schema → 투영/정규화 → 장후 reader·stage → 평가/정책 → summary·strict → PREOPEN·실제 PID`로 표기한다. 각 화살표에 활성 상태, owner, 시장·세션, source/effective date, run/generation·hash, 레코드 ID, 단위/시각, 원본 대비 입력·제외·출력 수, 실패 처리, 마지막 확인 근거를 붙인다. 파일 존재·wrapper exit 0·정적 import만으로 연결 완료를 선언하지 않는다. **양방향 전수**를 맞춰 생산자만 있고 소비자가 없는 경로와 소비자가 기대하지만 생산자가 없는 경로를 모두 찾는다. 의도된 source-only·valid-empty·OFF·retired를 각각 명시한다.

각 단계의 보고서는 `docs/audit-reports/<실행일>-intraday-postclose-handoff-S<N>.md`로 작성하고 아래 표를 유지한다. 날짜는 실행일이며 source date와 다르게 기록한다. 결손은 고유 ID로 다음 단계에 승계하고, 기존 checklist owner가 있으면 그 ID를 함께 기록한다.

| 필수 필드 | 내용 |
| --- | --- |
| 식별·상태 | ID, 활성/관측/OFF/퇴역, 실제 dispatch·호출 근거, 선택 릴리스/PID 여부 |
| 연결·모수 | producer, 원천 경로/schema, consumer, 날짜·세대·hash, 입력/유효/제외/미관측 수와 사유 |
| 결손 분류 | 생산 누락, 고아 원천, 미등록 소비, schema·시간·identity 불일치, silent failure, 누락된 terminal, 중복·퇴역 소비, 자원 병목 |
| 영향·수리 | 영향 받는 family/정책/권한, 재현 fixture, 수리 owner·파일, 우선순위, 차단 여부, 회귀·성능 수용 조건 |
| 증거 단계 | 코드 검증, 선택 릴리스, PREOPEN 검증, 실제 PID 소비, 자연 원천·terminal, 비용 후 경제성 각각 독립 상태 |

`COMPLETED + valid profit_rate`만 실현 PnL로 사용한다. 미체결·부분체결·censored·미확인 원가는 0이나 무손익으로 채우지 않는다. 실주문, sim, probe, CF 및 main/widget/episode/manual owner를 합치지 않는다. 결손 row/window를 식별할 수 있으면 `raw_row_exclusion`으로 격리하고 원본·분모를 보존한다. 전체 차단은 preflight 결손/무효, 격리 실패 또는 범위를 특정할 수 없는 큰 계약 손실에만 쓴다. 불명확한 원천을 정책 개선이나 경제적 실패로 단정하지 않는다.

결손 우선순위는 **P0**: 실주문·안전·잘못된 정책 적용 또는 원천 훼손 가능성, **P1**: 활성 family의 필수 원천/마지막 소비 누락·잘못된 경제성, **P2**: 관측·효율·퇴역 잔재로 정한다. P0도 증거 없는 즉시 재기동·수동 정책 변경을 뜻하지 않는다. 각 결손에는 영향 범위와 안전한 임시 처리, 수리 뒤 닫아야 할 producer와 consumer의 검사 지점을 함께 지정한다.

## 3. 단계별 작업과 완료 기준

| 단계 | 이번 단계에서만 수행할 일 | 단계 산출물·통과 기준 |
| --- | --- | --- |
| **S0 경로·소유권 전수조사** | 전체 후보 모듈·shell·cron/systemd·등록 stage·loader에서 실제 진입점과 writer/reader를 추출한다. 선택 릴리스와 작업공간의 차이, 활성·관측·OFF·퇴역, 별도 owner를 표시한다. 양방향 연결표를 만들고 각 미분류 경로에 조사 ID를 부여한다. | 누락 없는 후보 목록과 discovery 방법, `producer→artifact→consumer` 그래프, 역방향 orphan 목록, 명시적 제외 목록. 이름 검색만으로 PASS 금지. 코드·설정·스케줄 중 최소 두 관점으로 연결 근거를 대사한다. |
| **S1 공통 원천·투영 계약** | S0의 활성 공통 입력 중 시장/세션·quote/orderbook·WS/REST·scanner·pipeline event·broker/order/fill·DB projection·source-quality 경로를 확인한다. 시간·epoch·route·ID·원본/투영 수 보존, 지연·중복·누락·예외 삼킴을 재현한다. | source별 원천→투영→최초 소비자 표와 valid-empty/missing 구분. 발견 결손마다 재현 가능한 최소 fixture 또는 원천 증거, 수리 owner·영향 범위. Kiwoom 요청/파서/실시간 FID를 수정할 일이 생기면 해당 **공식 reference gate**를 그 수리 단계에서 먼저 수행한다. |
| **S2 진입·BUY 경로** | S0/S1 목록의 활성 기계 BLOCK/RECHECK/ENTER_NOW, 보조 AI, 가격, 수량·분할·probe, `entry_cancel_wait`와 주문 시작 후 timeout, 주문 제출·취소·broker 최종 확인, 저가·후행 원천의 장후 reader를 가족별로 대사한다. AVG_DOWN/PYRAMID 별도 owner를 섞지 않는다. | 판정→첫 주문 intent→각 leg→terminal→장후 수량·가격·시간 평가의 identity·분모 보존 표. 누락된 생산/소비, 부분·잔량·재시작·불확실 주문을 결손 ID와 회귀로 제시한다. 기존 안전·주문 권한 보존. |
| **S3 보유·SELL·손익 경로** | 보유 판단·trailing/익절·추가매수와 청산·취소/terminal·계좌 position·비용/실현손익의 실제 producer와 장후 평가 reader를 대사한다. main, widget, episode, manual 보유 주체를 분리한다. | fill→position→exit→`COMPLETED` 경제성의 세대/owner/원가 검증표. 열린 포지션·부분 청산·censored는 별도 분모. 미확인 손익을 0으로 바꾸는 경로와 장후 누락을 결손 ID로 남긴다. |
| **S4 잔여 활성 family·관측 경로** | S2/S3 외 S0에 남은 active family와 scanner 관심도, market weakness/rising missed, pre-submit delay, low-price, 모니터·detector·code improvement workorder, widget/episode·source-only 분석을 **잔여 목록 0**까지 분류한다. OFF/퇴역 코드의 실제 호출 누출을 조사한다. | 모든 S0 후보에 owner·consumer 또는 의도된 종료 사유가 있다. 이름 미상/미분류 경로가 남으면 단계 실패와 후속 조사 ID를 남긴다. 비권한 관측이 정책·주문 권한으로 승격되지 않았음을 확인한다. |
| **S5 장후 전 체인·다음 장전 소비** | `deploy/run_threshold_cycle_postclose.sh`와 실제 호출 family stage, `postclose_stage_terminal`, `runtime_approval_summary`, `postclose_summary_handoff`, `verify_threshold_cycle_postclose_chain`, controller/finalizer/detector, checklist, PREOPEN loader를 같은 source date/run으로 대사한다. 필요한 stage의 실행 순서·중복 소비·재시도·복구·stale terminal을 확인한다. | 필수 stage마다 실제 producer terminal→동일 세대 summary/strict→최종 소비자 관계와 실패·OFF·valid-empty 규칙. 단순 wrapper DONE이나 summary 존재로 전 체인 PASS를 선언하지 않는다. 자가 hash 순환·오래된 PASS 재사용이 없어야 한다. |
| **S6 결손 수리 묶음** | S1–S5 결손을 위험도/owner별 작은 묶음으로 정렬한다. **한 지시에서 하나의 owner 또는 밀접한 producer–consumer 묶음만** 수정한다. 원천 producer와 마지막 consumer를 함께 고치고 재현 회귀→자가 리뷰→수정보완→재리뷰를 반복한다. | 묶음별 결손 ID, 수정 파일·근거, 이전 실패 재현과 새 통과, 영향 경로 pytest/compile/`bash -n`/wrapper 계약, `git diff --check`; 리뷰 미해결 0. 새로운 실주문·provider·threshold·안전 권한이 필요하면 그 묶음의 권한 블록을 표시하고 독립 수리는 계속한다. |
| **S7 데이터·성능 통합 검증** | 코드 리뷰가 닫힌 묶음만 같은 clean 원천/고정 날짜로 replay한다. 정규 장후의 cold/warm wall·CPU·peak RSS·I/O·provider budget, stage terminal·strict까지 측정한다. 변경 전후 원모수·후보 grid·holdout·비용·source exclusion을 대조한다. 무거운 전체 실행은 실행 범위가 별도로 지시되고 준비됐을 때만 수행한다. | 결과 값 결함 0 또는 명시적 blocker, 성능 회귀 원인·S6 재수리·S7 재측정, 전수 입력/제외/출력 보존, 같은 세대 최종 소비 확인. 빠른 실행을 위해 모수·grid·holdout을 줄인 결과는 PASS 불가. |
| **S8 릴리스·자연 소비 수용** | 변경 범위가 검증된 뒤 승인된 릴리스 작업에서 작업공간/정본/불변 릴리스·선택기·설치 경로를 대사하고 다음 PREOPEN·PID·자연 terminal·비용 후 결과를 순차 수용한다. 이 단계도 먼저 코드·정책 사전 gate와 후속 자연수용을 분리한다. | 코드 검증, 릴리스 선택, PREOPEN, 실제 PID, 자연 원천, 경제성을 개별 상태로 보고한다. 자연 표본이 아직 없으면 `not_observed`로 남긴다. S0–S7의 완료가 자동 배포 또는 경제성 승인이라는 뜻은 아니다. |

S1–S5의 목적은 **발견과 결손 명세**다. 안전한 국소 수리가 발견 시 필요하더라도 해당 단계의 검토 범위를 넘는 변경은 S6 묶음으로 이관한다. 심각한 live 안전 결함은 결손 ID와 영향·즉시 운용 차단 필요성을 별도로 보고한다. 단계 사이에 미분류 경로·원천 불확실성·신규 발견 경로가 있으면 다음 단계가 이를 명시적으로 받아야 하며 조용히 범위에서 제거하지 않는다.

## 4. 단계별 복사 가능한 지시문

아래에서 `<실행일>`, `<source date>`, `<결손 ID/owner>`만 해당 실행에 맞게 바꾼다. **단계 하나의 결과가 나온 뒤 다음 지시문을 보낸다.**

### S0 — 전수 목록

> 이 계획의 S0만 실행하라. 전체 `src`·`deploy`·설정/등록/스케줄에서 장중 생산자와 장후 소비자 후보를 양방향으로 찾고, 실제 dispatch·선택 릴리스/활성 상태·owner를 대사하라. `<실행일>` S0 보고서에 연결표, 고아/미분류 목록, discovery 방법과 S1 인계를 기록하라. 코드·운영 상태는 변경하지 말고 리뷰 후 목록 누락을 보완하라.

### S1 — 공통 원천

> S0 보고서의 인계 ID를 기준으로 S1만 실행하라. 장중 공통 원천→투영→최초 장후 소비자의 schema·시간·identity·건수와 source-quality 격리를 검사하라. 결손마다 재현 증거와 수리 owner를 붙여 `<실행일>` S1 보고서로 넘겨라. 이 단계에서 실주문·정책·서비스를 변경하지 마라.

### S2 — 진입·BUY

> S0/S1의 인계표로 S2만 실행하라. 활성 진입 판정부터 수량·분할·probe·주문 시작·취소·terminal 및 장후 저가/후행 평가까지 실제 producer–consumer를 연결하라. 부분체결·잔량·불확실 주문·재기동과 family별 분모를 포함해 `<실행일>` S2 보고서에 결손 ID·재현·수리 묶음을 적어라. 다른 owner의 수량/안전 정책을 건드리지 마라.

### S3 — 보유·SELL

> S0/S1의 인계표로 S3만 실행하라. 보유 판단, 매도 주문/취소/terminal, 비용과 실현손익의 장중 생산 및 장후 소비를 owner별로 대사하라. full/partial/open/censored와 real/sim/probe를 구분하고 `<실행일>` S3 보고서에 결손·재현·수리 owner를 남겨라. 이 단계에서 정책·주문·서비스를 변경하지 마라.

### S4 — 잔여 family

> S0 전체 후보 중 S2/S3에서 다루지 않은 항목에 대해 S4만 실행하라. 활성·관측·OFF·퇴역 경로의 생산/소비 또는 의도된 종료 사유를 전수 분류하라. 미분류 0을 증명하거나 남은 항목을 결손 ID로 공개하고 `<실행일>` S4 보고서에 다음 owner를 적어라. OFF·source-only를 실주문 권한으로 복원하지 마라.

### S5 — 장후 마지막 소비자

> S0–S4 연결표를 바탕으로 S5만 실행하라. 실제 장후 wrapper의 family stage부터 동일 source date/run의 terminal·summary·strict·finalizer/detector·checklist·PREOPEN reader까지 순방향과 역방향으로 대사하라. stale/중복/누락 및 OFF/valid-empty 처리를 `<실행일>` S5 보고서에 재현·결손 ID로 기록하라. 정규 장후작업 실행이나 배포는 하지 마라.

### S6 — 수리 묶음 한 건

> 이 계획의 S6에서 `<결손 ID/owner>` 묶음 **한 건만** 구현하라. 해당 장중 producer에서 마지막 장후 consumer까지 수정하고, 실패 재현 회귀를 보존하라. 코드리뷰→수정보완→재리뷰를 미해결 결함 0까지 반복하고 영향 테스트·wrapper 계약·성능 영향과 남은 권한 블록을 `<실행일>` S6 보고서에 기록하라. 다른 묶음, 실주문, 재기동, 배포는 실행하지 마라.

### S7 — 데이터·성능

> 리뷰가 닫힌 `<결손 ID/owner>` 묶음에 대해 S7만 실행하라. 동일 clean 데이터의 변경 전후 원모수·제외·결과·비용·holdout을 비교하고, 승인된 실행 범위에서 cold/warm 장후 wall·CPU·RSS·I/O 및 마지막 consumer를 측정하라. 결과/성능 결함은 S6 재수리 대상으로 돌리고 `<실행일>` S7 보고서에 PASS 또는 blocker를 근거와 함께 남겨라.

### S8 — 릴리스 및 이후 수용

> S0–S7의 필수 gate가 닫힌 `<결손 ID/owner>` 묶음에 대해 S8만 수행하라. 선택 범위·불변 릴리스·정책/rollback·다음 PREOPEN의 사전 검증을 먼저 보고하고, 허용된 릴리스 인계 후 실제 PID·자연 원천/terminal·비용 후 경제성을 각각 대사하라. 발생하지 않은 자연 소비는 `not_observed`로 기록하고 코드·릴리스·PID·경제성 상태를 혼합하지 마라.

## 5. 단계 진행 규칙

1. S0은 전체 후보를 고정하는 첫 단계다. S1–S5는 각자 한 영역만 읽되 새로운 후보를 발견하면 S0 연결표에 역등록한다. S6은 결손 ID 단위로 여러 번 실행할 수 있다. S7도 수리 묶음별로 반복한다.
2. 각 보고서는 `판정 → 직접 증거 → 다음 조치`를 쓴다. 단계 PASS는 해당 범위의 조사 또는 수리 통과만 뜻하며, 다른 단계의 수용을 대체하지 않는다. 이미 닫힌 family 리뷰는 신규 결함·계약 변경·필수 인계 실패가 없으면 재개하지 않는다.
3. 문서-only 단계는 문서 link/owner/권한 점검, print-only parser와 `git diff --check`로 닫는다. 코드 수리는 현재 사용 가능한 `$korstockscan-review-gate` 절차와 AGENTS 규칙을 적용한다. 정규 장후 실행·서비스 재기동·정책 변경은 계획 작성이나 읽기만으로 시작하지 않는다.
4. 단계별 실행 owner는 현행 일별 checklist의 stable ID를 유지한다. 새 결손을 고치는 시점에만 그 날짜의 checklist로 이관하며, 자동 생성 블록을 수동 수정하거나 중복 OPEN owner를 만들지 않는다.
