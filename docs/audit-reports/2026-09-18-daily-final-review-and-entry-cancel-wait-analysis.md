# Daily 최종 재리뷰·과거 출력 정리 및 다음 cancel-wait 작업 분석

2026-09-18 KST. 사용자1번 승인으로 Daily 관련 code review/fix/re-review·검증·commit/push·immutable 배포 및 불필요 과거 산출물을 정리한다. 2번 다음 작업은 읽기 전용 분석이며 producer/runtime/selector 코드를 변경하거나 재실행하지 않는다. 최종 source/release/갱신/삭제 receipt는 `tmp/daily-final-review-20260918/closure.json`이며 자연 PID/거래 경제성은 별도다.

## 1. Daily 리뷰·보완·정리

리뷰에서 두 결함을 재현했다. 첫째, versioned evidence가 self-hash를 재계산해 양수 cash 값으로 변조됐을 때 원 family proof와 재검증하지 않는 경로였다. 둘째, 명시적 source-quality 차단이 있어도 유효 가격/scale-in proof adapter가 validated 상태로 덮어쓸 수 있었다. 기존 family evaluator로 증거 status/metrics/proof SHA를 다시 확인하고 명시적 원천 차단을 우선하도록 보완했다. 기존 valid price fixture에 변조/차단 회귀를 추가했다. 새 replay engine·threshold·주문·provider·root module·cron은 추가하지 않는다.

Daily/source/PREOPEN505PASS와 EV/runtime/strict264PASS, compile/diff/print-only parser 및 final release contract/기존 compact strict를 확인한다. 정책·family currentness는 코드 revision이 변경됐으므로 기존 bounded refresh/후행 소비만 재생성한다. 원천 gap을0/no-edge로 대체하거나 별도 경제성 floor를 완화하지 않는다.

현재·최근20 report date·참조/재사용 계약·열린 파일을 확인한 뒤 과거 cumulative/AI-review Markdown 104개/995,488bytes를 삭제했다. 삭제 전 SHA/크기/날짜 manifest와 현재 참조 검색을 보존했다. JSON 원본/동결 proof·모델/holdout·정책/rollback·raw/실제 주문·비용은 삭제하지 않았고 관련 JSON 300개의 SHA가 삭제 전후 동일함을 확인했다. Markdown은 보존 JSON에서 재생성 가능한 출력이다. 참조 가능한 과거 Daily/calibration/cumulative JSON을 공간 확보만을 위해 제거하지 않는다.

## 2. 실제 다음 장후작업과 9/17 실행 결과

현재 선택 release의 native wrapper에서 Daily/AI correction while-loop 종료 직후 **`src.engine.automation.entry_cancel_wait_tuning --date SOURCE_DATE`**를 실행한다. 그 뒤 cumulative JSON/Markdown을 기다리며, 조건부 Swing/Pattern 단계로 이어진다. Inventory의 기존 #55다. Daily 내부의 calibration·AI review·cumulative는 별도 새 작업으로 중복 집계하지 않는다.

[request1024](../../tmp/postclose_stepwise_2026-09-17/request_1024.json) 9/18 00:24:31.276929→[result1024](../../tmp/postclose_stepwise_2026-09-17/result_1024.json) 00:27:06.523476, 약155.25초/exit0. [결과](../../data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-09-17.json)는 source-quality pass/invalid0/proxy0, registered0/completed candidate0/메뉴0, `no_observation_hold`·각 profile `hold_source_contract`, 변경 지원false·carrytrue다. 네 timeout은 standard90/breakout120/pullback600/reserve1200초로 유지했다. economic input false이며 gap은 `touch_mark_proxy_missing_executable_fill_exit_cost`다. pass는 파일/행 파싱 상태이고 경제성 계약 통과가 아니다.

실행 결과의 종료/보고서 생성은 정상이다. 독립 후보/기존 EV·ΔEV·원화 일별 순익·tail·capital 비교값은 산출되지 않았다. 빈 candidate 메뉴는 null/미평가이지 검증된 EV0 또는 no-edge가 아니다. 155초의 exact 구간은 request/result이며 CPU-only 수행시간으로 해석하지 않는다. 원 pipeline JSONL은5,713,580,290bytes(약5.32GiB)다. `_iter_events`가 전체 날짜 파일을 읽는 구조와 작업시간을 확인했으며 이번 분석에서 거대 raw를 다시 조회하지 않았다.

## 3. 튜닝 의도·현재 후보와 경제성 한계

의도는 미체결 BUY 주문을 얼마 동안 유지한 뒤 취소할지 profile별 timeout을 조절하는 것이다. split/ADD/AI prompt 선택이나 일반 threshold EV와 다른 운영 family다. Runtime 후보 메뉴는 standard/breakout에서 현재±30초, pullback/reserve에서±max(30초,10%),5~1200초로 제한한다. 과거 tuner는 각 timeout의 equal-weight gross proxy 평균·floor5를 사용해 상위를 선택하고 가까운 incumbent로 tie-break, standard/breakout daily±30초·나머지±10%로 step을 제한한다.

그러나9/17부터 등록/completed proxy 행을 진단으로 분리하고 추천용 completed에 넣지 않는다. 현행 `economic_tuning_input_allowed`도 source date<9/17이고 valid completed가 있을 때만 true다. 현재 정책 learning→독립 holdout→동일 opportunity·비용·자본의 causal paired EV·일별 cash delta를 새로 만들거나 소비하는 경로가 없다. 신규 관측 누적만으로 기존 메뉴 튜닝이 다시 시작되지 않는 명시적 contract hold다. 차단을 제거하거나 과거 gross proxy를 복원하는 것은 EV 수리가 아니다.

현재 observer는 candidate timeout 도달 이후 첫 update에서 `current_price <= submitted_price`이면 would-fill로 가정하고, 그 update60초 뒤 가격으로 gross return을 계산한다. 전체 timeout 구간의 연속 hit/호가 queue·부분체결·취소 접수/확정 race를 재현하지 않는다. 후보가 당시 시점에 실제 채웠을 수량·actual 운영 exit/stop·수수료/세금/슬리피지/동시 reserve·재진입 기회비용이 결속되지 않는다. gross 60초 mark를 executable 비용 후 PnL로 승격할 수 없는 구조 결손이다. 등록 때 실제 timeout 이하 후보에0을 넣는 과거 방식도 실제 정책 자기 비교·검열/no-fill·누락을 혼동할 위험이 있으나 현행9/17 guard로 적용 차단돼 있다.

## 4. 자연 source·시간 경과와 구조 결손

등록은 SCALPING 실제 BUY 취소 성공 또는 특정 already-resolved 결과 뒤이며, 부분체결 residual 취소와 이미 체결된 resolved 응답은 제외한다. 이후 해당 stock의 WATCHING/보유 update에서 observer를 전진시킨다. 전체 미진입 기회/실제 전체 BUY union이 아니라 취소된 부분 모집단이다. Source0의 정확 원인이 실제 취소0·관측 유입/유지 결손인지 기존 summary만으로 확정되지 않아 ETA=null이다.

| 구분 | 자연 누적으로 가능한 것 | 현재 closure/owner |
| --- | --- | --- |
| 등록0/관측 얇음 | 앞으로 대상 미체결 BUY 취소·후속 유효 update가 있으면 proxy source 수는 늘 수 있음 | 기존 Main cancel/order lineage→등록→관측 유지/최종 disposition 확인. 일반 fill 실적만으로 분모를 대체하지 않음 |
| 등록된 관측 미성숙 | 해당 stock이 유지되고 유효 update가 계속 오면 candidate timeout+60초 진단을 완료할 수 있음 | 기존 runtime observer, 실제 clock/완료 여부. 과거 결과0행에 임의 waiting을 붙이지 않음 |
| 과거 원천·stock state 소실 | 시간이 지나도 원 cancel/quote/clock이 복원되지 않음 | immutable 원천 제외·향후 정확 source 수리. 현재 등록0의 실제 소실을 증명한 것은 아님 |
| executable fill/exit/cost·capital | 관측 수 증가나60초 mark 성숙만으로 계약이 생기지 않음 | 기존 order/execution owner의 frozen same-opportunity incumbent/challenger·실행/청산·full-cost/reserve 모델 및 실측 검증 필요 |
| 정책 검증/선정 | 현행 date guard로 tuning false. floor5를 채워도 다음 단계가 없음 | 기존 tuner의 chronological 후보 동결/독립 미사용 holdout·일별 net/tail/capital 소비까지 별도 개선 범위에서 연결 |

## 5. PREOPEN→장중 실제 소비

출력은 standalone `entry_cancel_wait_runtime`의 PREOPEN selector에서 직접 읽는다. 경제성 false면 보고서 추천값 대신 이전 manifest/env 또는 profile default를 carry한다. 기존 ON 지속·명시 operator OFF·stale/conflict·최종 broker/order/quantity/cooldown은 유지한다. ADM/LDM/lifecycle/일반 threshold EV·runtime bridge에 경제성 입력을 공급하지 않는다.

9/18 dated env에는 attribution true·real min60/stale max30, 네 timeout90/120/600/1200이 결속돼 있다. 이 값은 기존 정책 보존이며9/17의 신규 EV 최적화 결과가 아니다. Default standard60과 보고서90의 차이는 기존 선택 값/manifest 보존이며 값만으로 선정 오류라 할 수 없다. Dated env와 process-loaded 값/PID·실제 취소 행동은 분리한다. 이번 분석은 새 PREOPEN/env/PID/주문 receipt를 만들지 않았다.

## 6. 판단과 다음 조치

**BUY 미체결 대기시간 제어 런타임은 유지할 이유가 있지만, 현재 장후 출력은 경제성 탐색보다 contract gap 진단·기존 정책 보존 역할이다. EV 개선 탐색에 최적화돼 있지 않다.** 미래 관측의 진단 가치와 실제 정책 EV 비교의 결손을 분리해야 한다. 다음 별도 개선에서는 원 submitted/cancel parent union·same qty/budget·candidate fill/cancel race·운영 exit/stop/full-cost·reserve/holding·re-entry 및 독립 holdout 계약을 기존 실행 owner와 결속하는 것이 우선이다. 새 평가기/대량 grid·원천 전체 재스캔·floor 완화보다 비교 가능성/소비 계약이 먼저다. 지금은 미검증 추천을 적용하는 경로를 열지 않는다.

본 분석에서 next producer/runtime/PREOPEN 관련 파일 SHA와 보고서·request/result의 as-of를 보존했다. 재생성·추가 raw 조회·provider·주문·해당 작업 코드 변경은 하지 않았다. 단일 루프 scan/동일 artifact 재사용 비용·silent JSON parse skip·prebaseline previous-report admission은 후속 운영/원천 검증 항목이며 현재 economic guard 차단을 성과로 바꾸지 않는다.
