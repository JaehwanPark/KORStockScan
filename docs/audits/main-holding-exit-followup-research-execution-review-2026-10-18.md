# Main 보유·익절 후속연구 실행·검토 — 2026-10-18

현재 상태: **실제 가격 경로·진입 전 이력·등록 연관 분석과 비용 소비 시각 수리·별도 실제 재실행 완료**. 원 판정·초기정책·운영 수탁을 보존한 오프라인 연구다. 실행 owner는 당일 checklist의 `MainAllScopeTrailingReplay`이며 별도 보유·재생 수리 세션을 전제하지 않는다.

## 1. 실행 신원과 사전 등록

- [선행 연구](main-holding-exit-research-execution-review-2026-10-18.md)의 원천9/29~10/16·대상10/19·cutoff `1792284633.131831`을 유지했다. [intake](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/intake.json)는 원 manifest/종결과 보호9파일을 고정한다. 원 실패·중단·v3 결과는 수정하지 않았다.
- 격리 branch는 `codex/holding-exit-followup-20261018`, worktree는 `/home/ubuntu/KORStockScan-worktrees/holding-exit-followup-20261018`다. 최초 실행 commit은 `a4a51fd8b9c9e44ee06f02b28e8530eee3c5935d`, base는 `1bf35e6c258cdcda373c813432b52725898f22ab`이다. [실행 전 소스 동결](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/execution-source-freeze.json)에 production Python678개와 실제 import·시험·private 실행기를 결속했다. 기존 재생/런타임 코드 계약 `2df6ba7d0a9ddc2a7f2dcec6f780c49473c0050b7be641d64b0b4062fedd3d12`는 유지한다.
- 비용 시각 소비 수리 commit은 `57a4659f471044f8c8a59db53fc01b12d194333a`다. [보완 등록](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/allocated-cost-repair-registration.json)은 첫 결과 관측 후의 계약 정정이라고 명시하고 실험 정의·원천·선정은 그대로 둔다. 새 비용 출력과 정정 메타데이터만 바꾸었으며 [별도 소스 동결](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/cost-repair-source-freeze.json)·검토 후 비용 모듈만 실행했다. 최초 경로/이력/연관 결과를 새 코드로 재생한 것으로 소급하지 않는다.
- [원 실험 등록](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/experiment-registration.json)은 landmark30/60/120/180초, 후행3/5/10/20/30/60분, 모형 비용률0.23%, 목표+0.4%·비교선-3%를 새 실제 출력 전에 고정했다. -3%는 이번 비교선이며 실제 하드스톱 설정을 의미하지 않는다.
- [연관 분석 등록](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/association-registration.json)은 진입 전120봉 특징과 진입120초 뒤까지의 완료봉, 그 이후 원 진입+10/60분까지의 창을 결합한다. 결과를 보고 임계값을 맞추지 않았다. 같은 기간은 선행 연구에서도 보았으므로 `fresh_confirmatory_holdout=false`다. 10/15~16 시간순 분할은 탐색적 확인이며 새로운 미사용 검증 표본으로 부르지 않는다.

## 2. 생산자·소비자와 원천 계약

새 source는 기존 `src/engine/automation`의 오프라인 보고서 역할에 둔다. Main hot path·키움 요청/응답 parser·실시간 구독은 변경하지 않는다.

| 생산자 / 소비자 | 실제 입력·필드 | 출력과 제한 |
| --- | --- | --- |
| `main_trailing_followup_research.run` | 봉인된508개 모델 ID·원 position의 item/route, native chart의 exact item/auth/adjustment·`available_at`, OHLC | 대체청산 중복13 제외495행의 landmark별 가격 경로. 사후 최신 revision geometry는 진입 특징·원 AI·실제 armed state가 아님 |
| `main_trailing_entry_history_diagnostics.run` | 원 `entry_at` 이하 가용 named revision, clean baseline 이후 완료봉 | 마지막120봉의 `range_pct/return_pct/trend_efficiency/rebound_pct` 네 특징. `spread_pct/session_vwap/vwap_distance_pct=null`, 원 context/pin 불변 |
| `main_holding_allocated_cost_diagnostics.run` | 원 승인 비용 receipt/index·원 BUY/SELL/custody·projection 세대·비용 가용시각 | `initial_quantity_research_only`의 관측 완료 거래 배분비용 참고. canonical 실제 비용·손익·공통 전략 적격으로 승격하지 않음 |
| `analyze_associations.summarize` | 같은495 ID의 위 두 가격 보고서, 고정120초 prefix·10/60분 창 | 결측 사유와 원 ID를 보존한176행/304개 row-window, 27개 설명 집계. 실제 체결·EV·승률·최적값을 생산하지 않음 |
| `execution_lineage` | frozen holding signal, exact record/BUY generation·원 정책 hash·시각 | snapshot→기록상 완료 간격만 산출. 주문 intent/제출/브로커 종결 bridge와 slippage는 선택 입력에 없어 null |

JSON 본문과 physical 세대는 같은 바이트에 결속하고, 원천/코드·partition 참조·하위 bounded tree를 마지막 발행까지 재검증했다. UTF-8 원본 bar JSON의 실제 바이트를 decode 전에 관리 예산에 반영하고, 초과는 source gap으로 감추지 않고 실패시킨다. 일자별 private DB/WAL 사본과 named revision cache를 사용한다.

공식 API 존재·로컬 보관·당시 가용·실제 소비를 구분한다. [선행 공식 원천 감사](main-holding-exit-research-execution-review-2026-10-18.md#3-원천을-대사한-결과)의 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`와15종 능력 구분은 유지하며 새 Kiwoom 요청을 작성·실행하지 않았다. 이후 확보 가능한 현재/과거 broker 자료와 과거 미저장 내부 AI·계획, 가상 주문의 실제 fill을 혼동하지 않는다. 이번 로컬 결손은 API 제공 불가의 증명이 아니다.

## 3. 전체 범위와 진입 특징 복원

[최초 실행 종결](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/terminal.json), [가격 경로 보고서](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/path-geometry/report.json), [진입 전 이력](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/entry-history/report.json)을 분리한다.

| 분모 | 실제 결과 | 의미 |
| --- | ---: | --- |
| 범위 | 2,605종목 × 8route/session = 20,840 | 등록·처리 분모. 20,835 `registered_nonoperating`·5 `operating_unobserved`; 전 시장 원시 관측의 완전성을 뜻하지 않음 |
| 입력 모델 ID | 508 | 실제13·대체청산13·ENTER_NOW+PASS CF482 |
| 중복 대체청산 제외 | 495 | 실제13+CF482, 빠진 ID를 숨기지 않음 |
| 사후 분봉 revision 연결 | 460 | 실제10+CF450. 나머지35는 정확 item/범위 모호/미보관 등 원 사유 유지 |
| 진입 전에 가용한 OHLC 특징 | 227 | 실제3+CF224, 모두120봉. 부분2~119봉은 실제0 |
| 진입 특징 결손/기간 전 감사 | 267 / 1 | 결손을0특징이나 BASE 판정의 성공으로 바꾸지 않음 |
| 120봉에 전일 봉 포함 / 같은 날 내부 공백 | 34 / 157 | 두 집계는 중복 가능. 120봉 존재가 신선함·연속성을 뜻하지 않음 |
| 마지막 완료봉 경과시간 | 최소4.081초·중앙5,077.169초·최대31,880초 | 중앙 약84.6분. 당시 가용과 현재 상황 반영을 분리 |
| 6개 원 특징 분류기 준비 / upward-efficient 양성 | 0 / 0 | 기존6특징 분류기·새 상승 지속 유형의 효과를 비교할 근거가 아님 |

227행의 revision은 모두 `available_at<=entry_at`이다. 이전 날짜 prefix도 실제 보관되어 있었으므로 버리지 않았으며, 특징 계산에는6/5 clean baseline 이전 봉을 넣지 않았다. 새 네 OHLC 특징은 별도 설명변수다. 원 `BASE` pin·보조판정·보유 AI 입력/응답·수동관리 boolean을 수정하거나 과거 런타임 소비를 입증한 것으로 바꾸지 않았다. prior 시점 full revision64개를 실제 decode했고 cache163회를 재사용했다. [독립 이력 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/actual-entry-history-review.json)는32 compact partition/508 ID와 세 native revision의 봉인·가용 시각을 확인했다. 그중 주성 CF revision 하나의 선택 창 첫/끝 원 bar 두 개를 별도로 대사했다.

## 4. 비용 소비 시각 결함과 별도 수리

[최초 비용 출력](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/allocated-cost/holding-allocated-cost-diagnostics.json)은 원 승인8건 중5건만 연결했다. 이 분모의 배분 비용은3,170원·배분 후 관측 순손익 참고 합계2,830원이다. [독립 최초 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/actual-allocated-cost-review.json)는 이 결과를 수리 필요 상태로 보존한다.

49267/49300/49328의 소비자에서 서로 다른 시각 의미를 exact equality로 비교했다. 기존 재생의 `completion_at`은 원 projection SELL leg의 마지막 시각이고, 수량 비용 생산자의 `completed_at`은 동일 broker receipt의 원 체결 발생시각이다. 세 사례는 native 재관측 감사에서 projection 시각이 `first_observed_at`과 정확히 같고 발생·수신·최초 관측은 각각 별도로 입증된다. 1초 근사 허용으로 해결하지 않았다. 등록된 producer audit의 record·order/execution·native identity/payload digest·생산 코드와 시각 순서를 결속했다. `broker_terminal_occurred_at`은 이 원 비용 생산자의 마지막 SELL 발생시각이며 별도 주문 terminal·브로커 지연 증명이 아니다. raw event를 새로 재검증했다고 주장하지 않고 `raw_source_events_reverified_here=false`를 명시했다.

[비용 수리 종결](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/cost-repair-terminal.json)과 [새 비용 출력](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/allocated-cost-repaired/holding-allocated-cost-diagnostics.json)은 **8건**, 배분 비용 **4,065원**, 배분 후 관측 순손익 참고 합계 **19,535원**이다. 이는 과거 관측 거래의 연구 배분값이며 신규 수익·자동청산 성과·정책 개선액이 아니다. 원8건 중5건의 same-clock 연결은 보존하고3건만 증거에 의한 시각 bridge를 사용했다. 49294의 중복/체결 원천 부적격은 그대로 제외하며 미청산3건·원 비용 없는4건도 보존한다. 참여 종목/일자 cohort 총비용6,256원은 미청산·범위 밖 배분 등이 포함된 별도 분모여서 terminal8건 비용과 같지 않다. 49340/49343은 BUY2leg의 완료 합계이며 첫 진입 수량에 대한 트레일링 성과로 바꾸지 않는다.

원 `initial_quantity_research_only`·비용 가용시각10/16 21:01:37.811328 KST·canonical actual 손익·원 자동관리 false·공통 전략 적격0은 유지한다. 새 실행기는 출력 디렉터리와 terminal/failure 두 파일만 쓸 수 있게 좁혔고 이전 보고서6개와 하위 shard 쓰기를 차단했다. 원5건 결과와 최초 terminal·경로·이력·연관 분석은 그대로 보존한다. [보완 결과 독립 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/actual-allocated-cost-repaired-review.json)는 비용8건·각 시각과 원 receipt/선행 결과 보존을 별도로 수용한다.

## 5. 상황별 후행 경로와 주성엔지니어링

[등록 연관 결과](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/association-analysis.json)에서495행 전부의 row audit를 남겼다. 진입120봉227행 중120초 prefix 관측178행, 최소 한 후행 창 적격176행이다. 최종176행은 **실제3+CF173**, row-window는 **10분176+60분128=304**다. 전체495행은65개 종목·시간 중첩 연결군, 연관 분석176행은23개 군이며 군 수 자체도 통계적 독립성 증명은 아니다. 최대 연결군은89행이다. 시간순 train324/holdout171행에서 경계에 닿는 이전군의 purge 규칙을 적용했지만 이번 실제 purge는0이다.

범위/시장/route·진입 OHLC band·초기 경로 geometry로27개 군을 만들었다. 초기120초가 모형 손익분기 아래였던 CF의 train 구간은10분135행 중 목표접촉31,60분103행 중63이었다. holdout은 각각19행 중1,10행 중1이었다. 분모·종목·경로가 달라지고 중첩·이력 공백이 있으므로 기다림의 성공률 증가나 청산 정책 우위로 해석하지 않는다. `upward_efficient=true`가0이므로 상승 지속형과의 성과 대조도 하지 않는다.

모든 가격 상하한은 고정0.23% 모형 비용을 차감한 관측봉 참조다. 첫/끝 partial minute, bar 내부 순서, 체결 가능 bid/수량, 가격 조정 기준가격의 등가성이 증명되지 않았다. 304창의 내부 완료봉 관측과 **원 진입부터 요청 끝까지 전체 구간 관측0건**을 구분한다. +0.4% 목표 접촉을 트레일링 시작·실제 익절 체결로 부르지 않는다.

주성은 실제3+CF260=263행이다. 진입 OHLC 복원163행과 연관 분석119행은 모두CF이며, 연관119행은10/12~14의5개 중첩군이다. 10/15 실제49294의 진입 특징은 결손이다. 이 실제 건의 진입120초 후부터 원 진입+60분까지 관측 가격 범위는 **-5.4085%~-0.23%**, 비교 -3% 접촉·목표+0.4% 미접촉이다. 10/16의 실제49351은 같은 창에서 목표에 접촉했지만 서로 다른 포지션·날짜이므로10/15 하드스톱의 반증으로 합치지 않는다. 사후 반등·다른 날 CF와 수동 이관 후 자동 성과를 혼동하지 않는다.

[신호 계보](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/execution-lineage.json)는 실제13건 중11건에 snapshot13개를 연결했다. 최신 snapshot→기록상 완료 간격은0.831~2.415초이며 **브로커 주문 지연·첫 발동→체결 지연이 아니다**. 주성49294의 연결 snapshot 두 개는 `EXIT_TRAILING_TP`다. 이 기록만으로 앞선 하드스톱·수동 매도의 실제 종결을 입증하지 않는다. 원5,465개 보유 AI가 모두 INSUFFICIENT였다는 사실도 AI 유예 성과로 바뀌지 않는다. [독립 경로·연관 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/actual-path-association-review.json)는 ID/군/시간순 분할·27집계의 전 수치와 row audit를 재계산했다.

## 6. 성능과 검토 범위

최초 실제 invocation은12.748초, 가격 경로6.960초·진입 이력4.917초·비용0.062초·신호 계보0.045초다. 누적 peak RSS는61,336KiB이며64MiB는 별도의 managed Claim 한도, 종료 used0이다. thread `rchar=5,449,470,210B`는 논리 read이며 disk `read_bytes=132,120,576B`와 다르다. private DB/WAL 사본 쓰기 비용도 남으므로 무I/O라고 부르지 않는다. 기존 전체 assembly/replay336초와 다른 작업이어서 가속비를 계산하지 않으며 운영 Main 지연 비악화를 이 결과로 증명하지 않는다.

최초 코드 검토는8파일 compile/Ruff/diff-check와 통합267 PASS/28.38초, private 실행기18개·연관 소비17개 합성 검증으로 닫았다. 비용 수리 후 최종 통합은 **284 PASS/28.82초**,8파일 compile/Ruff/diff-check PASS다. [독립 코드 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/code-cost-clock-repair-independent-review.json)의 비용42개는284에 포함되며 반복 합산하지 않는다. producer 감사→비용 발행→legacy completed source→새 저장 보고서의1초/7초 시각 차이를 증거로 연결하는 양성과 신원/시각/미래 비용·중복 음성 경로를 검증했다. 비용 재실행 private 실행기는 보존 출력 쓰기 차단 등을20개 합성 검사로 확인했다. [최종 코드 종결](/home/ubuntu/KORStockScan/tmp/holding-exit-followup-20261018/code-review-closure-v2.json)에 결속했다.

별도 비용 재실행은0.142초·peak RSS24,496KiB, module build0.060초, managed Claim 보수 예약12,824,176B·종료 used0이다. 최초 모듈 build0.054초와 입력·검증 작업이 달라 성능 개선율을 계산하지 않는다. 두 실제 실행은 CPython audit 범위에서 outbound/DNS·child process·거부 write 시도0, 보호9파일 불변이다. OS sandbox 보장으로 표현하지 않는다. 원 실패와 최초 비용 undercoverage·합성 검증의 수정 이력은 삭제하지 않았다. 전체 trading/pre-AI suite·Main hot path/P5·정책 발행·자연 경제성 검증은 실행하지 않았으며 선행 감사의 더 넓은 pre-AI12실패도 통과로 바꾸지 않았다.

## 7. 판정과 다음 수용

**ENTER_NOW+PASS 후행 자료와 진입 전 보관 OHLC는 추가 연구에 활용할 수 있다. 현재 시작률·weak/strong의 개선값이나 시장 외 신규 정책 유형을 선정할 근거는 확보되지 않았다.** 연구용 네 OHLC 특징과 실제6특징 분류기, 사후 geometry와 당시 입력, 관측 terminal 배분비용과 대체청산 경제를 각각 분리한다.

| 다음 작업 | owner / 근거 | 종료 검사 |
| --- | --- | --- |
| 관측 완료 배분비용의 별도 holding 소비 | `MainAllScopeTrailingReplay`, §4·보완 실제8건 | 이번 diagnostic 소비는 완료. 대체청산 경제로 확대하려면 해당 경로의 비용 모델·시점·수량을 별도 결속하며 원scope를 실제 비용으로 승격하지 않음 |
| 시작 전 악화·회복·지속 비교 | 같은 owner, 진입 이력227/연관176행 및 원 gap | 당시 가용성·경과시간/공백·exact item/route와 bar 순서/기준가격을 입증한 별도 모델 비교. 오래된 특징을 현 상황으로 간주하지 않음 |
| 시작 후 이익 보존·ADD/부분잔량 | 같은 owner, 원 BUY/SELL leg·현재 미지원 lifecycle | 수량·원가·가용 시각의 이벤트 재생, 실행 가능 가격·수량과 비용별 실제/모형/CF 분리. 다중BUY terminal을 단일진입 실적으로 변환하지 않음 |
| 신호 이후 실행 손실 | 같은 owner, 선택 입력에 없는 제출 bridge | 기존 producer가 보유한 exact signal→intent→order→fill/terminal을 원 ID로 연결한 범위만 계산. snapshot 차이를 latency로 대체하지 않음 |
| 장후 초기정책 / 운영 소비 | 원 연구 부모 계승·`DirectFamilyPreopenPolicyHandoff` | 선행 연구 산출물12cell 시작0.4/weak0.4/strong0.8·classifier=null 변경 없음. 실제 운영 로딩은 별도 receipt로 확인하며 초기값에 새 경제 승인 허들을 붙이지 않음 |

실제 source 없는 과거 AI/계획이나 가상 실제 fill을 자연 생산 대기 조건으로 두지 않는다. 원천이 부족한 가설은 이번 자료에서 비교 불가라고 종결하고, 사후 threshold 탐색으로 보완하지 않는다. `MainAllScopeTrailingReplay`의 잔여 경제 비교는 OPEN이다. 선택900/PREOPEN·custody·canonical actual 손익은 보존하며 배포·Main 기동/재시작·외부 계좌/API·신규 구독·provider·주문·Project/Calendar sync를 실행하지 않았다. `MainPolicyLoadAndExitValidation1018`의 P5 후보 실행도 이번 연구에서 수행하지 않았다.
