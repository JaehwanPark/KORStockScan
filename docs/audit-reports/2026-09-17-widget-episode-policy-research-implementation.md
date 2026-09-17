# Widget·episode 정책 연구 보완 구현 — 2026-09-17

## 1. 사용자 지시와 상태

사용자가 [연구 로직 리뷰](2026-09-17-widget-episode-policy-research-logic-review.md)를 참조하여 보완·반복 코드리뷰·수정·검증 후 commit/push·배포·기동을 승인했다. 이번 범위는 R1–R5 연구 correctness와 실행 후보의 증거 경계다. [세 계산 최적화 계획](../proposals/postclose-computation-optimization-implementation-plan-2026-09-17.md) O1–O3의 전체 구현을 완료로 표시하지 않는다.

다른 작업의 수정본을 보존하기 위해 `fix/widget-episode-research-20260917` 분리 worktree에서 구현했다. 기본 source는 `052c7be3`; 실제 배포는 검증된 변경과 최신 운영/원격 commit을 통합한 immutable release로 수행하며 최종 receipt를 아래에 추가한다. Source 검증과 자연 정책/실체결/net profit은 별도다.

## 2. R1 — Actual adapter와 전수 source-only 경제성 분리

- 기존 `_candidate_observation` 및 actual economic baseline의 제출·실현·원래 target/수량/비용 검증을 유지한다.
- 원천 producer에서 유효한 원래 decision timestamp/native event/등록 profile·가격·수량·target이 있는 미체결 episode leg도 decision anchor로 보존한다. fill price를 만들거나 미실현 notional/PnL을 채우지 않는다. 확인되지 않은 order submission은 null이며 projection도 null을 false로 바꾸지 않는다.
- `policy_research_economics.source_only_timing_observation`은 before-gate owner decision의 causal replay와 raw BBO/depth/epoch/비용에 결속된 CF만 받는다. no-submit/unknown-submit을 실체결 adapter의 필수 조건 때문에 버리지 않는다. prospective/bar-only/다른 hard guard anchor는 해당 timing 표본으로 승격하지 않는다.
- 모든 confirmation arm은 anchor+300초의 **동일 평가 전용 deadline**을 사용한다. target의 full-quantity executable bid가 확인되면 그 target을 사용하고, 그렇지 않으면 동일 deadline의 fresh full-quantity bid로 source-only payoff를 계산한다. 손실·미해결 target도 원천이 완성되면 평가에 남는다. adverse touch는 stop이 아니며 평가 deadline은 새 live 강제청산이 아니다.
- 이 원천 계약이 있는 cohort는 전체를 common-horizon CF로 평가한다. 옛 실제 terminal과 새 CF terminal을 하나의 EV에 섞지 않는다. historical common label 부재는 economic/control gap으로 보존하고 원래 coverage/sample/positive EV/tail/capital efficiency/same-stage/next-date 계약을 유지한다. 최신 source-day 검증도 추가한다.
- Cohort population disposition은 economic pair/원천 차단/economic-control gap을 대사한다. 관측·경제성·선정·approval 소비와 broker execution은 다른 상태다.

주요 코드: [source-only economics](../../src/engine/monitoring/policy_research_economics.py), [attribution producer](../../src/engine/monitoring/machine_microstructure_attribution.py), [timing consumer](../../src/engine/automation/machine_entry_timing_tuning.py).

## 3. R2 — 최초 탐색부터 source-day 순익을 보존

- Signal discovery의 1,536 grid/cap1–5/기존 두 half positive EV·tail·incremental cap guard/최근16거래일 holdout을 유지한다.
- Calibration 후보는 기존 EV guard를 통과한 뒤 두 half의 낮은 modeled net profit/qualified source day를 기준으로 비교한다. 순익은 기존 등록 기본수량10주 기준의 source-only 지표다. 공유 자본·실제 주문 수량 변경 권한이 아니다.
- 높은 EV/적은 기회와 낮은 EV/많은 기회를 비교하여 더 큰 총 modeled 순익 후보가 최초 탐색에서 탈락하지 않게 한다. 후보/cap은 holdout 전에 고정하며 holdout 실패 후 다른 winner를 찾지 않는다.
- summary에는 qualified day count, modeled currency profit, capital occupancy, participation을 추가했다. valid-zero source day는 분모에 남고 missing/nonfinite outcome은 null이다. Legacy EV/robust score와 새 profit rank를 구분한다.
- Auto calibration의 초기 grid도 완성된 전체 position·leg의 modeled currency profit을 rank에 반영한다. multi-leg을 한 주 수익률 단순 합으로 비교하지 않는다. 해당 경로가 legacy diagnostic인 경우 runtime selected paired economics를 대체했다고 표시하지 않는다.
- 기존 발행 정책의 `METRIC_CONTRACT`를 바꾸지 않았다. 신규 report의 selection metric contract와 producer fingerprint에서 새 의미를 결속하여 기존 exact-date policy reader가 코드 변경만으로 incumbent을 잃지 않게 한다.

주요 코드: [symbol discovery](../../src/engine/monitoring/widget_symbol_signal_policy_research.py), [auto calibration](../../src/engine/monitoring/widget_auto_trade_policy_calibration.py).

## 4. R3 — Census→연구 universe 누락을 원천으로 대사

- 기존 exact-date `market_opportunity_census`의 canonical `liquid_common/top_20/forward_exact` panel을 연구 report에 연결했다. 겹치는 다른 panel과 retrospective oracle를 중복 opportunity로 넣지 않는다.
- Native opportunity ID/source index/symbol을 보존하여 미등록 연구 종목, 등록 후 정책 미선정/원천 부족, 정책 선정으로 분류하고 input=count dispositions를 검사한다.
- 현재 universe 외 종목을 자동 실전 편입하거나 다른 owner의 main 신호를 widget/episode 신호로 쓰지 않는다. 미등록 disposition은 기존 scanner/census→추천/watch 원천 owner가 연구 수집·등록을 판단할 증거다. 시장 기회탐색이 이미 완전하다고 주장하지 않는다.
- Missing/oversized/corrupt optional census는 진단 source gap으로 남고 다른 정상 종목의 분봉 연구를 전역 중단시키지 않는다.

## 5. R4 — Proxy PASS와 신규 실행 후보의 분리

- 09-17 source-date부터 신규 symbol execution 후보는 정확히 같은 prospective signal seed와 원래 model entry/exit 시각의 KRX BBO·freshness·full quantity를 재검증한다. 10주 기본수량의 base/stress 참여 모델을 만족하려면 각각의 entry/exit book에 최소40주가 필요하다. 이는 기존 고정 수량에 대한 연구 capacity 검사이며 live 주문수량/broker guard 변경이 아니다.
- Seedless/raw-only 관측, 다른 parameter seed, malformed/stale/missing/symlink raw, same-quote conflict, duplicate episode, calibration/holdout lineage count 불일치는 신규 실행 후보의 증거가 아니다. 원천 파일은 stat/size/no-follow/generation-before-after/hash로 확인한다.
- Report는 proxy 연구 PASS를 별도로 남기고 실행 증거가 없는 신규 후보의 decision을 no-promotion으로 전달한다. Canonical policy와 구버전 reader의 재구성 결과가 같은 차단 decision을 소비할 수 있도록 기존 core policy shape를 유지한다.
- Publisher도 원천을 독립 재검증한다. Exact-date loader가 검증한 **완전히 같은 signal/execution incumbent**의 carry는 신규 proxy 승격으로 취급하지 않는다. 기존 execution incident/holdout/owner/next-date guard도 유지한다.
- Observation seed는 계속 발행 가능하다. 원천 부재를 메우기 위해 실제 fill·과거 BBO·새 API 결과를 합성하거나 오늘 날짜 정책을 수동 발행하지 않는다.

주요 코드: [publisher/reader](../../src/engine/monitoring/widget_symbol_runtime_policy.py), [raw projection contract](../../src/engine/monitoring/widget_symbol_runtime_contract.py).

## 6. R5 — Valid-zero day와 공동 자본 수익 경계

- Fixed timing의 rolling 5/10/20 window는 실제 calendar window와 validated source reports를 사용한다. 성공적인 observation이 있는 날짜만 모아 missing calendar를 건너뛰지 않는다.
- Paired widget에는 기존 family accumulation이 증명한 zero-signal source dates를 전달한다. 기존 유효 pair 날짜에 검증된 zero 날짜를 더하고, 누락/부분 source의 signal0을 꾸며내지 않는다. 유효한 partial-day completed pair를 full-session zero-day 조건 때문에 통째로 버리지도 않는다.
- `joint_capital_demand`는 selected episode interval·등록 기본수량을 시간순으로 재생하여 peak concurrent notional과 독립 순익 합을 계산한다. 같은 시각의 청산은 새 진입 전에 자본을 반환한다.
- Caller가 명시한 연구 capital contract 아래 전 episode가 feasible할 때만 combined modeled 순익을 제시한다. 부족하면 null이며 hindsight로 좋은 거래만 골라 feasible profit을 만들지 않는다. 자본 계약이 없으면 `allocation_contract_missing`, malformed/duplicate interval은 source gap이다.
- 현재 운영의 공통 연구 capital limit을 새로 정하지 않았다. Broker 잔고를 부르는 대신 기존 allocation owner가 exact-date 자본 계약을 전달해야 한다. 따라서 이 구현은 개별 수익 합을 feasible 공동 수익이라고 표시하던 위험을 닫으며 실제 공동 자본/경제성 증거가 생겼다고 주장하지 않는다.

## 7. 반복 리뷰·검증

1. Actual/CF outcome adapter 분리 및 원천/consumer 검사.
2. Source day/수량/시간이 없는 fixture는 새 profit rank의 증거로 쓸 수 없음을 확인하고 원래 시각을 가진 fixture로 보완.
3. Winning target만 CF에 남는 편향을 제거하고 losing unresolved target을 동일 deadline payoff로 평가. 실제 terminal/CF horizon pooling 금지.
4. Legacy METRIC_CONTRACT 호환성, unchanged incumbent carry, 구 reader의 no-promotion decision 재구성, unknown order-status 보존 검사.
5. Optional corrupt census와 partial-day pair가 다른 정상 연구를 전역 중단시키지 않도록 보완.
6. 실행 증거로 차단된 후보를 top-level passed_symbols/decision에서도 제거하고, per-symbol checkpoint를 합친 뒤 전체 census·joint capital demand를 다시 대사했다. calibration selected lineage를 누락하지 않으며 external census/raw 파일 세대 변경은 content full scan 없이 cache fingerprint를 무효화한다. 당일 BBO full scan은 20:05 전 차단한다.

검증 receipt는 `/tmp/widget-episode-research-gate-tests.txt`의 11개 suite **473 passed**. 마지막 producer/approval/runtime trader/collector까지 확대한 15개 suite는 **660 passed**; 분리 worktree에 없는 기존 설정 lineage 보고서 때문에 실패한 default-config 1건은 4개 bounded JSON의 원래 SHA를 검증·복사한 뒤 collector suite **18 passed**로 재검증했다. 운영 설정/원천을 변경하지 않았다. 이후 valid-zero ledger와 partial-day pair 분리 보완은 해당 paired/auto suite **75 passed**로 재검증했다. Ruff/import·compile, 기존 두 wrapper `bash -n`, diff check를 수행했다. 신규 module/test는 monitoring 경제성 owner와 tests에 배치했으며 engine-root allowlist에 새 예외를 추가하지 않았다.

의미 있는 회귀: 미제출/unknown 제출/실제 제출의 같은 CF basis, actual adapter fail-closed, losing payoff 유지, quantity/depth/epoch/terminal drift, 원천 signal 없는 diagnostic 제외, zero-day 분모, 동시 자본 초과, 순익과 EV가 다른 후보, 다른 seed/심볼/심링크 원천·duplicate episode 거부, exact incumbent carry, census panel 중복과 corrupt summary 격리.

운영 API/provider call, production 장후 보고서 재생성, 날짜 정책 수동 재발행은 source 검증에 사용하지 않았다. 자연 원천·policy selection·PID consumption·실체결 net profit은 source-only pytest로 닫지 않는다.

## 8. 배포·기동 인계

배포 대상은 widget evaluation, machine final refresh, 공통 raw projection을 쓰는 widget read-only collectors다. Immutable release/import root를 확인하고 이전 unit drop-in과 실제 PID/cwd를 보존한다. 기존 main selected release와 trading PID·현재 주문/holding/custody/env/dated policy를 이 연구 배포 때문에 교체하지 않는다.

Inactive postclose oneshot은 자연 timer 시각을 유지하여 대기시킨다. 오늘 EOD 전 수동으로 expensive 연구를 돌려 source 날짜를 과거로 바꾸지 않는다. Collector는 검증된 기존 scope에서 기동하며 source/date/owner guard와 resource budget을 유지한다. 최종 effective unit/import/PID receipt 및 rollback 경로는 배포 후 추가한다.

현재 자연 owner: 오늘 체크리스트 `WidgetPostcloseEvaluationPinAcceptance0916`. U10A/B 및 미등록 universe/공통 자본 계약의 외부 원천 잔여는 `KiwoomCommonHealthOpportunityCostAcceptance0917`에 연결한다. Source/code closure와 자연/경제성 closure를 별도로 관리한다.

### 8.1 최종 배포 receipt

- 구현 commit `1cecf1ad`, 최신 원격 변경 보존 통합 `77abb524`를 `origin/main`에 push했다. 운영 source는 `/home/ubuntu/KORStockScan-runtime-releases/widget-episode-research-20260917-77abb524`의 동일 통합 commit이며 source/deploy/restart.sh git clean이다. 아래 receipt 보완의 문서 commit은 이 source 세대와 구분한다.
- 통합 15개 suite **661 passed**, wrapper/cost/collector-expansion **147 passed**, 동일 immutable release의 physical data 검증 **134 passed**. compile/Ruff/bash -n/diff/link·owner/print-only parser 검증을 수행했다. package install·운영 API 수동 호출·production 보고서 재생성은 실행하지 않았다.
- 11:24:34 KST raw collector PID **282239**, 11:24:37 observer PID **282392**가 새 release에서 active/running이다. 실제 `/proc` cwd/argv/PYTHONPATH 및 그 release에서의 핵심 6 module import origin을 확인했다. 재시작 횟수0, 기존60초/1초 interval과 각각 CPU10%/20%, Memory256/384MiB를 보존했다.
- Widget evaluation CPU20%/512MiB·machine final refresh CPU20%/2GiB를 보존한 채 WorkingDirectory/PYTHONPATH/project/Python/ExecStart를 같은 release로 고정했다. 각 oneshot은 inactive/PID0이며 **not_yet_due**; timer는 active이고 오늘 **20:10/21:15**에 자연 실행한다. Daytime 강제 평가를 기동 receipt로 사용하지 않았다.
- 배포 전후 main selector SHA 동일, main actual PID **270515**, trader **28368** 및 cwd/상태, 오늘 widget dated policy SHA 동일을 검증했다. 기존 exact-date loader 결과는 이전 widget release와 동일 SHA `ab6d3f69686e42de3b6f4edde6d5687ead523c33bff0e21fd3748bb6fc83d833`이다. 현재 실행/seed 정책0과 raw 관측19의 의미를 구분한다.
- 11:26:04 KST의 bounded snapshot census19는 PASS10/SOURCE_ERROR5/SOURCE_QUALITY_BLOCKED4다. 기존 snapshot과 새 수집의 혼합 시점이며 전체 cycle·full-session source PASS가 아니다. 실제 source issue·AM/new common-horizon 표본·policy/PID 소비·공동 capital 계약·cost-adjusted net profit은 기존 자연 owner에서 **OPEN**이다. source gap을 threshold/depth/freshness guard 완화로 없애지 않았다.
- 세부 receipt: `data/runtime/widget_episode_research_release_2026-09-17.json`; unit 이전 설정 및 새 drop-in: `tmp/widget_episode_research_deploy_20260917`. 네 unit의 신규 `zzzzzzzzzzzzzzzz-widget-episode-research-20260917.conf`만 제거한 뒤 daemon-reload와 read-only collector2개 재기동으로 원 pin을 복구한다. 이전 drop-in·main selector·dated policy·raw/seed는 보존했다.

문서 최종 검증: 새 링크 결손0, 기존 당일 미래 산출물 링크5회는 변경 전 checklist에도 있는 자연 실행 대기 참조다. Print-only parser32개 task 중 두 existing stable owner가 각각1개로 검증됐다. Project/Calendar 외부 sync와 token 조회는 실행하지 않았다.
