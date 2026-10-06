# 위젯 종목 신호연구의 수익성 선별·자료 기간 재설계 계획

## 1. 목적과 범위

사용자 요청은 종목 수 확대보다 **현재 보유한 원천으로 더 수익성 있는 종목과 신호를 제대로 구별하는 연구**다. 기존의 종목 확대 방향은 이번 연구의 목표로 이어받지 않는다. 운영 종목 수의 유지·축소 및 이미 등록된 종목 사이의 교체 가능성을 비교하고, 자료 기간도 함께 정한다.

이번 변경은 계획 작성이다. 계산·정책 발행·collector 변경·API 호출·서비스 제어·자료 삭제를 실행한 결과가 아니다. 실행 소유자는 [현재 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)의 `WidgetSymbolProfitabilityResearchRedesign1006`이다. 이 문서의 새 기간·선별 방식은 제안 계약이며 현행 운영 계약으로 표시하지 않는다.

사전 점검의 코드·보고서·terminal SHA와 날짜별 census는 [점검 증빙](../../tmp/widget-research-and-advisory-planning-20261005/inspection.json)에 고정했다. 점검 당시 selected release는 `next-session-ready-20261005-e16ac48b`, 작업공간 HEAD는 `3056b088`이다. 확인한 연구·자문·paired replay·wrapper·handoff 파일은 두 경로의 bytes가 같았다. source 날짜 `2026-10-02`, publication `2026-10-05`, effective `2026-10-06`을 구분한다.

## 2. 현재 구조에서 확인한 한계

| 확인한 사실 | 연구 설계에 주는 의미 |
|---|---|
| [최근 신호연구](../../data/report/widget_symbol_signal_policy_research/widget_symbol_signal_policy_research_2026-10-02.json)는 catalog636 중100종목 평가,536종목 자원 보류 | 현재 population 순서는 protected/추천/보관 coverage/catalog 순이다. 유망 종목의 경제성 순위가 아니며 보류를 수익성 탈락으로 해석할 수 없다. |
| 100종목 중97은 prospective 검증 대기,2는 source 격리,1은 robust calibration 미확보, passed0 | 100종목의 실제 거래 수익성을 모두 확인한 뒤 개선이 없었다는 결과가 아니다. 종목별 계산 도달 단계와 원천 지원을 먼저 확인해야 한다. |
| [연구 코드](../../src/engine/monitoring/widget_symbol_signal_policy_research.py)의 primary는 비용 차감 notional EV, ranking은 학습 두 구간의 보수적인 일별 모형 순이익 | EV와 순이익 지표는 이미 존재한다. 새 지표를 붙이는 것보다 현재 지표의 계산·실행 가능성·같은 자본에서의 종목 선별을 고쳐야 한다. |
| joint capital 입력의 invalid/duplicate episode272, capital limit null, joint peer 결손 | 종목별 모형 수익 합을 실행 가능한 포트폴리오 순이익으로 주장할 수 없다. 원 episode/자본·동시 기회 결속이 먼저다. |
| runtime policy에는 기존 관측 seed4, 별도 observation catalog에는98, 명시 등록 watch는13 | 연구100·관측catalog98·seed4·실주문 적격을 같은 집합으로 취급하지 않는다. 관측 등록은 거래 권한이 아니다. |
| 6/5~10/2 82거래일을66학습+16검증으로 분리 | 누적 전체 기간은 현재 설계다. 전체 기간이 최근 기간보다 실제로 우수하다는 증거는 이번 점검에서 확인하지 않았다. |

삼성·두산·한화오션의 자문평가3종목은 이 종목 신호연구의 seed4와 별도 집합이다. 삼성 Main 연구 결과를 이 종목의 비용·체결·정책으로 그대로 이식하지 않는다.

## 3. 연구 대상과 수익성 선별 방식

### R0. 입력과 대상 고정

1. 당시 selected code, dated policy, seed/관측catalog/등록watch, 원 보고서와 비용 계약을 manifest로 고정한다. 자료 날짜와 파일 생성·재생 날짜를 분리한다.
2. 첫 연구 대상은 seed4(`006800`, `010140`, `080220`, `475150`)와 이미 명시 등록된 watch13의 합집합 **최대17종목**으로 제안한다. 기존 등록 목록의 출처·원천 가용성을 재확인하고 격리·custody를 보존한다. 자동 추천·scanner admission을 통해 신규 종목을 덧붙이지 않는다.
3. 이17은 오프라인 후보 집합이다. 현재98종목의 관측 receipt를 삭제하거나 collector 구독을 바꾸는 계약이 아니다. 현재 관측/실행 범위와 proposed subset을 별도 필드로 둔다. 운영 교체·축소는 기존 dated publisher/consumer 수용을 거치는 별도 결과다.
4. 이미 계산한 나머지 종목 결과는 참고·archive로 보존한다. 같은100종목을 다시 계산하거나 catalog636을 확대 탐색하는 것을 기본 작업으로 삼지 않는다.

### R1. 종목별 원천과 독립 기회 대사

분봉 source → 당시 setup/원 신호 → 확인·진입 가능 시점 → 후보/기존 정책 진입 → submit/fill/terminal을 가능한 범위까지 연결한다. symbol/venue/session/policy revision/transport epoch/시각·sequence/source SHA를 유지한다. 반복 확인·동일 기회의 재시도를 독립 거래로 세지 않는다.

| 평가 층 | 계산할 값과 제외 기준 |
|---|---|
| 완료 분봉 패턴 | 당시 봉까지만 사용하는 setup, 다음 완료봉 진입 모형, 비용·틱 단위, 독립 사건/일별 모형 수익. 봉내 고저 순서·BBO·체결을 추정하지 않는다. |
| 실행 가능 가격 비교 | 기존 exact quote/depth/quantity·원 guard가 있을 때만 동일 기회 비교. spread·호가량·주문 가능 수량 결손은 unknown이다. |
| 실제 거래 결과 | owner의 full/partial fill·COMPLETED·유효 profit_rate 및 원 비용/terminal만 사용. 가격 모형을 실제 손익으로 변환하지 않는다. |

모든 종목의 정상 관측일·valid zero-signal day·source gap·검열을 별도로 센다. 정상적인 무신호일은 일별 분모에 들어가고, 결손일은 0수익으로 채우지 않는다. 실제 체결 부족 때문에 완료 분봉의 report-only 패턴 진단까지 중지하지 않는다.

### R2. 적은 종목으로 더 나은 결과를 내는지 비교

- 기존 종목 구성·당시 정책을 대조군으로 고정한다. source coverage와 당시에 알 수 있었던 거래 가능성으로 계산 대상부터 정하고, 학습 결과에서만 순위를 정한다. 검증 기간의 수익으로 종목·기간·threshold를 다시 고르지 않는다.
- 새 비교 축은 **종목 subset/순위 방식**이다. 기존 종료된 `WidgetEpisodeMachineResearchContract1006`의6가설을 반복하거나 신호/청산 grid를 더하지 않는다. 등록된 정책의 kernel·add/exit·cap·cooldown을 고정하고, 최대2개의 사전 정의된 종목 선별 방식만 비교한다.
- 선별1은 현재 seed 구성의 유지/부분집합, 선별2는 지원되는 등록17 안에서 학습 구간의 동일 자본 기준 일별 비용 차감 순이익으로 정한 부분집합이다. 선정 종목 수 상한은 기존 seed 수4로 고정한 연구 제안이다. 거래 가능성 또는 비용 후 개선이 없으면 축소/무선정 결과도 허용한다.
- 현행 notional EV와 학습 구간별 안정성을 함께 보고한다. 주가가 높거나 모형 진입 횟수가 많다는 이유만으로 순위가 높아지지 않게 같은 자본·동시 노출·기회 배분 규칙을 비교 전에 고정한다. 원 자본 receipt가 없으면 equal-notional 가격 시나리오로 표시하고 실행 가능한 KRW 순이익은 null로 둔다.
- 종목을 제외할 때 기회 손실과 자본의 다른 사용을 함께 계산한다. 동시 사건을 결과를 보고 잘라내지 않는다. 적격일당 순이익, paired EV, 자본 점유, 손실·검열·일별 편중과 비용 stress를 병기한다. 승률·기존 성공 건수·180초 수익 종료 건수는 diagnostic이며 성공100%/80% 보존 veto를 추가하지 않는다.
- 비교에는 같은 날짜·세션의 공통 원천 지원 분모와 전체 원천 결손/검열 비율을 함께 낸다. 지원되는 구간만의 결과를 전체 운영 성과로 확대하거나, 결손이 많은 종목을 수익성이 낮다고 순위 매기지 않는다.

이미 존재하는 `policy_research_economics`, `widget_signal_quality`, 실행 feasibility와 joint gate를 재사용한다. gate의 결손을 새로운 계산 바닥으로 무조건 확대하지 않고 해당 결과의 권한·해석만 제한한다.

## 4. 자료 기간을 정하는 절차

현재 코드는 마지막16거래일 holdout과 최소25거래일을 요구한다. 10/2 기준 최근 한 달9/2~10/2는21거래일이고, 최근20거래일은9/3~10/2다. 고정16일을 유지하면 학습은5일/4일뿐이므로 현 계약으로 실행할 수 없다. 한 달을 기본값으로 넣는 단순 변경은 개선안이 아니다.

새 후보 입력의 정책 시대는 [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md)의 **9/29 forward boundary**와 실제 parent의 효력·원천 계약을 함께 따른다. 그 이전 자료를 새 후보의 학습·순위·승인에 섞지 않는다. 과거 clean baseline6/5는 archive/audit 경계로 유지하고 이 계획으로 baseline 문서를 바꾸지 않는다.

| 기간안 | 제안 용도 | 확인할 영향 |
|---|---|---|
| 기존6/5 확장+16일 검증 | 이미 봉인된 결과의 역사 대조·계산 구조 확인 | 실제 선택에 쓰인 날짜, 과거 정책 혼합, 계산량·cache 의존성. 이전 결과를 새로운 독립 holdout으로 표시하지 않는다. |
| 최근20 적격 거래일 상한 | 새 선별 연구의 기본 기간 제안 | 최근 반응성, 독립 기회·날짜 지원, 편중·분산, 비용 후 순이익과 결손율. 하한은9/29 및 cohort 효력 경계 이후다. |
| 최근40 적격 거래일 상한 | 기간 효과를 확인하는 한 개 대조안 | 같은 정책 시대·같은 검증 사건에서 추가 학습일이 실제 결과 안정성을 높이는지 확인. 부족한 표본을 옛 정책 자료로 보충하지 않는다. |

기간 비교에서는 학습 종료일·공통 검증 사건/날짜를 먼저 고정한다. 새20/40일 안에 서로 다른 holdout을 만들어 좋은 결과를 고르지 않는다. 현재16일 계약을 유지하면20일 전체 창은 지원 부족으로 종료한다. 한 달에 맞는 사건/날짜 분할 계약을 제안하려면 기존 독립 episode floor·기간 편중·비용 계약과 비교해 근거를 작성하고 producer/validator/consumer version을 함께 설계한다. 계획만으로16일 기준을 제거하지 않는다.

10/2까지 forward era의 완료 거래일은 실행 대사에서10/1 완성 분봉도 확인해9/29·9/30·10/1·10/2 **4일**로 정정했다.20/40일 안은 현재 같은 입력으로 축약되므로 기간 효과를 식별할 수 없다. 이4일은 원천 진단과 제한된 가격 비교에 쓰고, 이미 사용한10/2를 새 검증일로 재명명하지 않는다. 새 후보를 동결한 뒤의 자연 원천만 새로운 검증 증거로 인정한다. 부족하면 `insufficient_sample`/`waiting_new_source`로 마치며 자동으로6~8월까지 기간을 확장하지 않는다. 고정된3학습/2검증일 대기 조건을 새로 만들지도 않는다.

기간의 최종 처분은 `20일 상한 유지`, `40일 상한 필요`, `기간 효과 미식별/지원 부족` 중 하나다. 근거는 공통 사건의 비용 후 결과·독립 지원·날짜별 민감도·실행 가능한 분모다. 기간×종목×신호 조합의 추가 탐색은 이번 유한 연구에 포함하지 않는다.

## 5. 구현·비용·보관 개선 설계

R0~R2와 기간 계약을 확정한 뒤, 구현이 지시된 경우에만 다음을 수행한다.

1. `src/engine/monitoring`의 기존 연구/경제성/정책 loader를 수정한다. 추가 오프라인 분석이 필요하면 같은 역할 패키지에 두고 engine root에 새 모듈을 만들지 않는다. 테스트는 기존 `src/tests/test_widget_symbol_signal_policy_research.py`, `test_widget_symbol_runtime_policy.py`, `test_widget_signal_quality_remediation.py`의 영향 계약부터 확장한다.
2. 신규 자동 발견과 nightly 전체 grid 대신 동결 universe·원천/parent/cost/window/code SHA가 같은 결과의 정확 재사용 및 새 날짜 incremental 계산을 설계한다. 동일 날짜 재생성을 신규 검증으로 세지 않는다. 실패한 input을 carry 성공으로 숨기지 않는다.
3. 기존 `widget_policy` stage는 신호연구→runtime refresh→summary 소비를 요구한다. 연구 축소·주기 변경·producer 중단을 한다면 wrapper, terminal, summary, validator, collector, 정책 publisher의 기대 상태를 같은 변경으로 갱신한다. 현재 mandatory artifact를 단순히 생략하지 않는다. 운영 문서·체크리스트 갱신은 그 자동화 변경의 범위에 포함한다.
4. 계산 절감은 같은 입력에서 cold/reuse wall time·CPU·peak RSS·파일 읽기량으로 측정한다. 현재 로그는 여러 실행을 합친 파일이므로 누적 경과시간을 한 번의 실행 비용으로 발표하지 않는다.
5. 6~8월 종목 스냅샷5,869개는 약146MiB다. 기간 변경만으로 큰 pipeline parquet/report까지 삭제 가능해지는 것은 아니다. frozen/rollback/audit 및 다른 consumer 참조를 조사한 뒤 [저장소 정리 owner](runtime-and-research-storage-cleanup-plan-2026-10-05.md)에 dry-run manifest를 인계한다. 이 계획은 삭제를 실행하지 않는다.

## 6. 산출물·수용·종료

| 순서 | 산출물 | 종료 기준 |
|---|---|---|
| R0 | universe/정책/원천/비용 manifest와 현재 계산 funnel | seed·watch·catalog·실행 집합 및 행별 지원/제외 대사, 원 SHA 유지 |
| R1 | 종목별 원천/독립 기회/가격·실제 결과 표 | 반복·결손·valid-empty·검열·실제 체결 분리. 모형 손익과 실제 손익의 오표시0 |
| R2 | 최대2선별 방식의 공통 분모 비교 | 기존4 유지/부분집합/등록종목 교체 연구 권고 또는 개선 없음/식별 불가 확정 |
| R3 | 20/40일 지원·공통 검증·기간 처분 | 시대 경계/학습·검증 누출0, 이미 사용한 날짜의 재라벨링0, 기간 효과 미식별도 유효 결과 |
| R4 | 수정 대상·consumer migration·비용/보관 인계 | 정확 재사용/실패/legacy 검증·권한 회귀 계획과 유한 종료. 운영 승격은 별도 gate |

계획 실행이 승인되면 `tmp/widget-symbol-profitability-redesign-20261006/<generation>/`에 새로운 manifest·원천 대사·종목/기간 비교·처분을 저장한다. 현재 계획 증빙을 덮어쓰지 않는다. code review→보완→표적 회귀→재리뷰를 닫고, 실제 trading source/PID/경제성은 기존 owner에 인계한다.

`WidgetEpisodeMachineResearchContract1006`는 종료된6가설 및 기존 leg/sequence 결손을 계속 소유한다. 본 owner는 **종목 선별·기간·계산 구조**만 맡는다. 자문3종목의 누적 집계/confirmation 진단은 [별도 계획](widget-advisory-cumulative-evaluation-diagnostic-plan-2026-10-05.md), 실제 기동은 `WidgetEpisodeNextSessionStartup1006`다. 원천 부족·개선 없음·새 날짜 대기를 완료 가능한 처분으로 기록하고 같은 입력의 무한 재탐색을 종료한다.

문서 변경은 링크·owner·권한·`git diff --check` 및 print-only backlog parser로 검증한다. Python/거래 테스트·API·경제성 재계산은 이번 문서 수립에 실행하지 않는다.


## 7. 10/5 승인 후 실행 결과

사용자의 `계획을 실행하라` 지시에 따라 R0~R4 격리 구현·연구를 완료했다. [실행 리뷰](../audits/widget-bounded-research-and-advisory-execution-review-2026-10-05.md), [계산/manifest](../../tmp/widget-symbol-profitability-redesign-20261006/final/report.json), [정확 재사용](../../tmp/widget-symbol-profitability-redesign-20261006/final/reuse.json), [보관 dry-run](../../tmp/widget-symbol-profitability-redesign-20261006/final/storage-dry-run.json).

- 17종목 중 공통4일·사전 고정 kernel 지원7, 가격 불완전8, kernel 결손2. 10/1 완성 분봉/동결 receipt 보유를 확인해3일 가정을4일로 정정했다. 기존 Main 연구 범위는 변경하지 않았다.
- 신호/청산 grid 없이2개 subset만 비교했다. 삼성중공업 단독 및 삼성중공업·한국항공우주 구성은 학습 기본 비용에서는 양수지만1틱 stress에서는 음수이며10/2 비교일도 음수다. 실제 자본·체결 손익은 null이다.
- 운영 교체 권고 없음.25일/16일 계약 미충족,20/40 기간 효과 미식별로 유한 종료했다.10/2를 새 독립 holdout으로 취급하지 않는다.
- `src.engine.monitoring.widget_research_plan_execution`은 workspace `tmp` 전용 보고서 생산자다. 같은 입력 지문의 전체 재사용 및 kernel/day incremental 계산을 구현했다. nightly100종목 stage·mandatory 산출물·collector·운영 policy는 변경하지 않는다.
- 과거 스냅샷5869개의 현재 실측은133.03MiB다. frozen source/audit 참조 미해소로 삭제 적격0, 실제 삭제0. 저장소 owner에 manifest를 인계했다.
