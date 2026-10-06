# 위젯 자문 누적평가 실행 점검·개선 진단 계획

## 1. 목적과 확인 범위

삼성전자(`005930`)·두산에너빌리티(`034020`)·한화오션(`042660`) 자문의 **실제 실행, 원천 평가, 누적 집계, confirmation 선택, dated 정책 소비**가 각 계약대로 연결되는지 확인한다. 별도의 [종목 신호연구](widget-symbol-profitability-research-redesign-plan-2026-10-05.md)의 seed/확대 catalog와 혼합하지 않는다.

사용자 요청은 점검 및 개선방안의 진단 **계획 수립**이다. 이번에는 코드/기존 산출물과 설치 경로를 읽고 계획·[증빙](../../tmp/widget-research-and-advisory-planning-20261005/inspection.json)을 작성했다. monitoring 절차·누적 보고서 재생성·정책 발행·프로세스 제어를 실행한 결과가 아니다. 실행 owner는 [현재 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)의 `WidgetAdvisoryCumulativeDiagnostic1006`다.

## 2. 사전 점검 결과와 아직 확인하지 않은 것

| 관측 | 현재 말할 수 있는 결론 | 진단이 필요한 부분 |
|---|---|---|
| 설치 unit은 `korstockscan-samsung-widget-evaluation.service`/timer,20:10 KST 예약.10/5 시작20:10:01·종료20:43:06·exit0 | 장후 service 호출·종료 기록은 있다. 현재 설치 cwd는selected `e16ac48b`다. | 종료 후 바뀐 현재 ExecStart를 과거20:10 실행 코드로 단정하지 않는다. 당시 attempt의 run/code SHA와 worker 로그를 대조한다. |
| [최신 terminal](../../data/report/postclose_stage_terminal/2026-10-02/widget_policy.json)은21:22 source10/2 recovery succeeded·computation_executed true | 원 예약 종료와 후속 recovery는 별도 실행이다. terminal이 참조한5개 출력 SHA는 현재 파일과 일치한다. | 재사용·재계산·회복을 새 날짜의 natural sample로 세지 않고 attempt별로 분리한다. |
| [최근 자문 report](../../data/report/widget_advisory_calibration/widget_advisory_calibration_2026-10-02.json)는done·daily verified3/3, 누적 적격80/8/24 | 집계와 유효 정책 발행 경로가 존재한다.112건은 실제 broker 수익 거래112건이 아니다. | 전체 원 raw·중복/적격/성숙 조건의 독립 재계산 및 실제 loader/PID 소비는 아직 점검하지 않았다. |
| 누적 loader 하한6/5, 보관 일별평가 삼성8/3·나머지8/6부터.8월 적격59/5/15=79 | 6~7월 일별평가가 없어 현재 누적표에 기여하지 않는다.8월은 누적 proxy/표시에 실제 포함된다. | 8월 파일의 원천/provenance·당시 정책/세션·현재 후보 입력 역할을 각각 확인한다. |
| 9/9 이후 paired confirmation 선택은 최근20거래일에 제한 | 최종 선택은 과거10분 proxy만으로 정해지지 않는다.8월 누적 적격을 현재 후보 성공 표본으로 해석할 수 없다. | 10/2의 paired에는9/15·9/18·9/23·10/2 경로가 있다. 최근20일 창 자체는9/29 forward 경계를 구현하지 않는다. |
| 삼성 정규장 `scale_in_runtime_trigger_source_missing`,장전 `paired_outcome_incomplete`,두산/한화 `baseline_contract_missing` | 모든 세션 confirmation3을 승계했으며 새 candidate_ready는 false다. 정상 실행과 신규 후보 확보가 다른 상태임을 보여준다. | 원천 결손·의도된 관측 전용·미구현 경로·계약 오류를 구분하고, baseline을 억지로 복원하지 않는다. |

현재 [calibration 코드](../../src/engine/monitoring/widget_advisory_calibration.py)는 누적 proxy EV를 계산한 뒤,9/9 이후에는 [paired selector](../../src/engine/monitoring/widget_paired_policy_replay.py)의 값·결정·EV로 최종 session 결과를 덮어쓴다. 따라서 “8월이 집계된다”와 “8월로 현재 confirmation을 바꾼다”는 서로 다른 검증 질문이다. 정책갱신 원칙은 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md)의9/29 이후 입력이며, loader·집계·selector 각각의 적용 범위를 대조한다.

## 3. 진단 실행 순서

### D0. 같은 실행과 자료 세대 고정

- selected release·설치 unit/drop-in·실제 attempt code SHA·PID start ticks·source/publication/effective date와 child phase 로그를 모은다. 현재 shared terminal만 보지 않고 immutable attempt receipt를 검증한다.
- 원 observation/evaluation/calibration report·dated policy·runtime loader 결과의 경로/SHA/schema를 manifest에 연결한다. 이번 기준 자료는 source10/2→publication10/5→effective10/6다. 실행 시 최신 완료 날짜가 달라지면 새 generation으로 기록하고 기존 증빙은 보존한다.
- 진행 중인 generation이나 현재 정책 파일을 덮어쓰지 않는다. producer 검증에 재생이 필요하면 격리 경로에서 exact input을 사용한다. 실제 기동/PID 검증은 `WidgetEpisodeNextSessionStartup1006`의 결과를 받아 중복 실행하지 않는다.

### D1. producer→마지막 consumer 연결표

| 단계 | 기존 owner/코드 | 확인할 영수증 |
|---|---|---|
| 원 자문 기록 | 각 종목 `*_widget_advisory` 및 recorder | 실제 관측 시각·symbol/route/session·원 정책/confirmation generation·source epoch/SHA |
| 일별 평가 | `samsung_widget_advisory_evaluation`와 종목별 평가 wrapper | 원 파일→eligible/제외/mature/검열/valid-empty 행수와 daily status |
| 누적/paired 선택 | `widget_advisory_calibration`, `widget_paired_policy_replay` | 과거 집계/실제 후보 창·기회·cost·incumbent SHA·최종 selected value와 이유 |
| 발행/로더 | `widget_advisory_calibration_policy`, `widget_auto_trade_policy_calibration` | source/effective 날짜·schema·원 report hash·carry/default/new 구분·당일 resolve 결과 |
| 자연 소비 | 각 자문 generator, Widget loader/state 및07:32/07:58 기존 owner | required confirmations의 실제 로드 hash/정책 ID·신호 eligibility·당일 reload. 단순 PID 생존과 구분 |
| 장후 인계/감시 | `run_widget_evaluation.sh`, `postclose_summary_handoff`, family 의미감시 | stage terminal·source SHA·summary/validator의 같은 세대 판정·필요 finding의 알림 소비 |

모든 단계에 `expected / observed / disposition / owner / artifact / next action / closure test`를 기록한다. 의도된 default/carry/observe와 retired/OFF를 오류로 바꾸지 않는다.

### D2. 일별 평가가 실제로 무엇을 세는지 독립 대사

1. 삼성의 KRX_REGULAR/NXT_PREMARKET 및 통합 aftermarket 관측, 두산/한화 KRX_REGULAR을 분리한다. session 계약이 바뀐 과거 NXT 단독 값을 새 통합 session에 상속하지 않는다.
2. 원 신호→승격/confirmation→원 ask·entry touched→10분 성숙→target/adverse 첫 도달을 추적한다. timestamp timezone·순서·관측 공백·같은 시각 중복·quote freshness 및 symbol/route 결속을 확인한다. 확인 횟수가 많은 한 사건을 여러 독립 기회로 부풀리지 않는다.
3. raw records →parse valid→unique input→원 신호 사건→eligible→mature→decisive→누적 반영의 행수를 독립 코드/소규모 고정 fixture로 대사한다. distinct 입력과 반복 확인 기록을 유지하며 단순 timestamp 중복 제거로 다른 사건을 잃지 않는다.
4. valid-empty/no-entry·미성숙·right-censored·input 결손·확정 손실을 구분한다. 결손 economics는 null이다. 정상적인 no-entry의0 exposure와 결손 결과의0 치환을 혼동하지 않는다. source 충분한 가격 진단에 실체결 바닥을 요구하지 않는다.
5. adverse-first 이후 target MFE 도달을 복구 성공으로 취급하는 `_opportunity_net_return_proxy`를 검토한다. 이는10분 가격기회 proxy다. 실제 stop·fill·청산 손익으로 표시하면 결함이며, 원 경로/정책이 없으면 실제 이익을 확정하지 않는다. 날짜별 비용·기준 가격·fallback adverse의 legacy 사용도 출처와 함께 대사한다.

### D3. 누적 범위·중복·정책 시대 확인

- 6/5 clean boundary, 최초 실제 평가8/3·8/6, paired 적용 시작9/9, policy-refresh9/29, 해당 incumbent의 실제 효력일을 별도 필드로 기록한다. source 날짜·report 생성일·publication을 서로 대신 쓰지 않는다.
- 삼성 historical76(8월59/9월17)+target4=80,두산8(5/3),한화24(15/9)를 현재 기준 대조값으로 사용한다. unreadable/contract mismatch/rolling60d 제외와 target 중복 방지 규칙을 검증한다. 원천이 새로 생겼을 때만 새 값으로 갱신한다.
- rolling60일 평가,6/5 이후 누적 통계,최근20거래일 paired 선택의 분모와 역할을 각각 대사한다. rolling sample floor의 적격 일별 보고서 수를 mature outcome 행수 또는 독립 기회 수로 바꾸어 해석하지 않는다.
- 서로 다른 보고서에 같은 source/outcome이 중복된 경우 native identity·source hash로 판정한다. 과거 보고서의 missing identity는 동일 또는 독립이라고 추측하지 않고 영향 범위를 표시한다.
- **역사 자문 통계**와 **현재 successor 선택 population**을 분리하는 계약을 진단한다. 후보 population은9/29 및 exact parent/source contract 경계 이후다. 구시대 proxy·최근20일 안의9/29 이전 pair를 새 후보 train/rank/approve 입력으로 섞지 않는다. 기존 verified 정책 carry/과거 receipt는 보존한다.
- 누적8월 보고서에 대응하는 raw가 현재 없으면 저장된 평가의 출처/정합성·재현 가능성을 별도로 보고한다. 원천 부재가 전체112건의0 EV 또는 전체 평가 실패를 뜻하지 않는다.6~7월 미사용 결론도 이 evaluator의 현재 입력 범위에 한정한다.

### D4. confirmation 비교와 carry 원인 진단

현행 비교 축은2↔3이다. 같은 사건·동일 초기 ask/수량·원 add/exit/cap/cooldown·base/stress 비용에서 candidate와 incumbent를 비교했는지 확인한다. 최근20일 source에서 학습/후단 holdout을 분리하며, 과거 결과를 본 뒤 새로운 독립 검증이라고 이름 붙이지 않는다.

삼성 정규장은 실제 last-trade·tick-clamped add trigger·leg fill/평균가·원 add guard가 필요하다. BBO-only로 추가매수를 합성해 ready를 만들지 않는다. 현재 저장된 원천으로 재현 가능한 부분과 영구 결손을 구분해 `WidgetEpisodeMachineResearchContract1006`의 기존 W2 인계를 재사용한다. 장전은4기회의 원 경로별 early resolution/1200초 공통창·검열을 대사한다.1200초는 평가 종료이며 실제 강제 청산 규칙이 아니다.

두산/한화의 baseline 부재는 운영상 관측 전용이면 정상 처분이다. 이 경우 진단에 필요한 원 자문 신호·10분 가격 결과는 계속 평가하되, trading recipe를 만들거나 candidate-ready를 강제하지 않는다. 실제로 있어야 하는 dated baseline 또는 replay input이 누락된 경우에만 producer/loader 결함으로 분류한다.

누적 proxy가 양수/음수여도 paired 지원 부족이면 최종값이 incumbent로 돌아가는지를 반례로 검증한다. 자문 표시 confirmation의 변화가 downstream entry eligibility에 미치는 실제 경로를 확인한다. `direct_order_authority=false`만으로 간접 신호 효과까지 없다고 주장하지 않는다. 주문/수량/custody/hard safety는 이 진단으로 변경하지 않는다.

### D5. 개선안의 우선순위와 적용 범위

| 우선순위 | 진단 결과에 따른 보완안 | 수용 조건 |
|---|---|---|
| P0 | 행수/원천·source date·identity·policy/cost hash 오결속, 중복/미성숙/평가 오표시 수정 | 같은 원 입력의 독립 대사·반례 회귀. 영향을 특정한 행/window를 제외하고 원 bytes 보존 |
| P0 | 과거 누적 proxy와 현재 paired 선택 역할·시대 경계 명시 | historical/candidate 분모·최종값 출처 구분,9/29 이전 입력으로 신규 후보 선정0 |
| P1 | 필요한 existing leg/guard·원 replay 입력 결속 또는 의도된 unsupported 상태 명시 | 기존 저장 source만 사용. exact 재현 불가면 not_identifiable/carry 사유 확정 |
| P1 | 3종목/각 session의 processed/eligible/independent/comparable/selected/carry 이유를 기존 report·감시에 투영 | `done`만으로 평가 성공 표시0, nullable 경제성·owner/closure 포함. 기존 의미감시 owner 사용 |
| P2 | 날짜 범위 loader·정확 재사용·incremental 집계 및 atomic generation 개선 | 한 번의 합계와 incremental 합계 동일, target 중복0, input 변경 시 cache 거부, active/dated 원본 덮어쓰기0 |

현재 쓰이지 않는 역사 proxy를 제거하거나 archive 전용으로 바꾸는 것은 실제 소비 역할이 확인된 뒤의 변경안이다. 먼저 삭제하지 않는다. 종목별 positive EV나 실거래 성공은 진단/결함 수리의 완료 조건으로 추가하지 않는다.

## 4. 산출물·검증·완료 기준

실행이 지시되면 `tmp/widget-advisory-cumulative-diagnostic-20261006/<generation>/`에 D0 manifest, D1 연결표, D2~D3 독립 행수·기간 대사, D4 session별 carry 원인, D5 수정 순서/영향/유한 closure를 남긴다. 기존 정책/report를 재생할 필요가 있으면 격리 출력에만 생성한다. 자동화/발행 경로 변경은 producer→validator→loader→summary/운영 문서/체크리스트를 같은 변경에 반영한다.

구현 검증은 기존 `test_widget_advisory_calibration.py`, `test_samsung_widget_advisory_evaluation.py`, `test_widget_paired_policy_replay.py`, 관련 자문 loader 및 `test_postclose_summary_handoff.py`의 영향 계약으로 한정한다. 정상·valid-empty·target 중복·8월 역사/forward 후보 분리·다른 세션·missing baseline·scale-in 원천 부족·미성숙/검열·변조/legacy carry·휴장/자정 target을 검증하고 review→수정→회귀→재리뷰로 닫는다. provider·계좌·주문 호출이 필요 없는 fixture로 검증한다.

최종 결과는 **실행 정상 여부 / 계산 정상 여부 / 현재 후보 지원 / 발행·loader 소비 / 실제 경제성**을 각각 판정한다. 정상 실행+지원 부족, 의도된 관측 전용, 실제 결함, not_observed/미래 due를 허용한다. 각 결함의 owner/artifact/수정/closure test가 있거나 원천 영구 결손의 유한 처분이 기록되면 진단은 완료다. 신규 정책 수익성 증명이나 실제 봇 기동까지 기다려 진단을 무기한 연장하지 않는다.

`SemanticPolicyCoverageRemediation1006`는 기존 감시·알림, `WidgetEpisodeMachineResearchContract1006`는 기존 leg/paired 연구 결손, `WidgetEpisodeNextSessionStartup1006`는 당일 적용/PID를 계속 소유한다. 본 owner는 **3종목 자문 평가의 실행·행수·기간·최종 선택 역할 진단**만 소유한다. 본 계획과 current10/5 체크리스트만 갱신하고 준비에 결속된10/6 체크리스트·정책·receipt는 보존한다.

이번 문서 검증은 링크·단일 owner·권한·diff 및 print-only parser다. 거래 테스트·전체 raw replay·경제성 재계산·Project/Calendar sync는 실행하지 않는다.


## 5. 10/5 승인 후 실행 결과

사용자의 계획 실행 지시에 따라 D0~D5를 격리 계산·코드리뷰·수정보완·회귀로 완료했다. [실행 리뷰](../audits/widget-bounded-research-and-advisory-execution-review-2026-10-05.md), [원천/누적 대사](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/report.json), [실행 세대](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/execution-context.json), [연결 표](../../tmp/widget-advisory-cumulative-diagnostic-20261006/final/connection-table.json).

- 4일×3종목 일별 재생의 저장 결과 차이0. 누적80/8/24,8월79는 일치한다.10/1의1460개DATA_WAIT는 가격 null/WS stale·future이며 유효한 무신호일과 구분했다.
- 새 paired의9/29하한으로 삼성 장전의 역사4경로는 forward1경로로 줄며 양 arm 검열이다. 정규장5219행의 완전한 원leg/add guard0, 두산/한화 baseline부재는 관측 전용 처분이다. 새 후보 선택0·confirmation3 승계 사유를 확정했다.
- filename/target 날짜 결속, 역사 proxy/신규 population 구분, 격리 incumbent snapshot, publication/source 날짜 분리, 간접 자문 producer를 포함하는 stage 코드 지문을 보완했다. 과거 정책 receipt의 read-only 검증은 유지한다.
- 현재10/6 dated loader의 네 session 수용을 읽기 전용으로 확인했다. 기존 발행/준비 bytes 보존, 배포·기동·PID·새수집·원천 합성 없음. 원천/의미감시/실제 다음날 소비는 기존 owner에 인계한다.
