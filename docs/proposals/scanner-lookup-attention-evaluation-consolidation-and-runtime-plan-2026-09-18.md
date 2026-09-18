# 조회 관심도 스캐너 평가 통합·장중 정렬 연결·조건부 정리 계획 — 2026-09-18

## 1. 결정·작업 범위

조회 관심도 원천·관측 필드는 보존한다. 독립 `scanner_lookup_attention_tuning` 장후 반복 평가와 자체 승격 판단을 기존 스캐너 평가에 통합한다. **동일 예산에서 실제 선택이 달라지는 기회**의 비용 차감 경제성이 양수이고 독립 검증을 통과할 때만 기존 날짜별 PREOPEN→장중 정렬 가중치 적용을 허용한다. 관심도 높은 체결 종목의 평균이 높다는 사실만으로 승격하지 않는다.

초기 요청은 개선계획 수립이었다. 후속 사용자가 구현·반복 리뷰/수정/검증·commit/push·배포와 제한 장후 결과 갱신을 승인했다. 과거 standalone 산출물 삭제는 아래 통합·소비·보존 검증 완료 이후에 실행한다. 오늘 사용자 제공 휴장/미적재 조건은 expected non-collection이며 broker/API/order·수동 env·calendar·guard·현재 worker 변경 권한은 확대하지 않는다.

장후 전체 개별단위 개선→통합 결과 검증→사용자가 예정한9/21 정책/PREOPEN 준비→정상 거래세션의 자연 소비·성과 순서를 따른다. 이 단위를 먼저 PREOPEN 적용하거나 전체 장후 완료로 보고하지 않는다. 다른 세션의 `scale_in_split_order_plan` source/test/정책/수량 소유권을 보존한다. [전체 정책 인계 후속계획](market-weakness-entry-policy-handoff-next-open-repair-plan-2026-09-18.md)의 날짜/PREOPEN 수리는 전체 개선 후 적용 준비에서 실행한다.

## 2. 확인한 현재 경로·결과

| 경로 | 확인 내용 / 한계 |
|---|---|
| `src/scanners/scalping_scanner.py:_lookup_attention_prior_observation` | 조회 순위 수준0.50·양의 변화0.35·신규top20 0.15의 source-only 점수. AI 매수 점수가 아님 |
| scanner `_scanner_priority_profile`→candidate pool 정렬→promotion/prune/attach | 점수·원천시각·tier·partition·owner·generation·실제/가정 priority·terminal 관측 전달 |
| `src/engine/monitoring/intraday_ws_freshness_monitor.py` | 기존 `scanner_unique_funnel.economic_cohorts` 및 BBO 분석·prune/lineage·작업지시 소비. 설치된 정규장/aftermarket monitor 호출 존재; 신규 trigger 불필요 |
| `scalping/scanner_lookup_attention_resource.py:allocation_book` | complete partition/실제 선택 재현·교체 pair. 현재180–360초 snapshot 수익은 기회 proxy이며 실제 주문 경제성이 아님 |
| 독립 `monitoring/scanner_lookup_attention_tuning.py` | rolling90 calendar days, rollout9/2부터 exact observation→FULL_FILL→완료 Main SCANNER 거래 비교·holdout·policy 생성 |
| `scalping/scanner_lookup_attention_policy.py` | 날짜별 PREOPEN 동결·runtime loader·bounded bonus. 현재 KRX/krx_regular만 eligible |
| `deploy/run_threshold_cycle_preopen.sh`→scanner loader | 유효 정책/날짜별 receipt가 없거나 비승격이면 bonus0. 독립 producer 폐기와 함께 consumer 계약도 이전해야 함 |

9/17 체결 fact sync40.44초/exit0/valid_empty/source0/warning0. 독립 관심도 평가382.81초/exit0, 당시 verify0.21초/exit0. Report는9/18 00:12:34 생성: 유효6,277/제외209·12관측일, candidate298/control5,979, full6/partial9/receipt미연결6,262, completed5(candidate1/control4). 평균 순수익률+0.28479794%/+0.2550475%, 차이+0.02975044%p. 비용은 실제 체결가격과 고정 비교수수료·세금이며 broker 정산이 아니다. 표본의 가중치 미적용으로 정책 인과 uplift/신규 이익을 입증하지 않는다.

교체 비교3개/3날짜의 snapshot 평균 차이−2.38954987%p, incoming−1.155944%로 resource gate hold_no_edge. 전체 hold_sample/forward holdout미시작/applyfalse.9/17·9/18 PREOPEN은 inactive/prior_policy_not_live_auto_apply_ready다. 전체 표본 부족과 작은 비교에서 관측된 no-edge를 분리한다.

현재 report/policy를 selected source로 read-only 검증하면 `economic_acceptance_not_reproducible`1건: 저장 `conversion_diagnostic_owner=buy_funnel_sentinel -> entry_recheck_drought_controller`, 기대 `buy_funnel_sentinel -> machine_entry_timing_tuning`. Source는 현행 담당자로 바뀌었으나 frozen 산출물 인계가 남았다. 퇴역 actor 복원 대신 successor/native metadata 인계로 정리한다. 현재 economic 수치를 새 적용 성과로 바꾸지 않는다.

근거: [9/17 요약](../../data/report/scanner_lookup_attention_tuning/scanner_lookup_attention_tuning_2026-09-17.md), [9/17 policy](../../data/threshold_cycle/scanner_lookup_attention_policy/scanner_lookup_attention_policy_2026-09-17.json), [fact sync receipt](../../data/report/strategy_position_fact_sync/strategy_position_fact_sync_2026-09-17.status.json), wrapper PERF/ready 및 위 producer/consumer source. 삭제 완료 뒤 과거 원파일 링크는 §10의 보존 manifest/요약으로 대체한다.

## 3. 소유권·최소 변경 배치

평가 출력의 owner는 기존 `intraday_ws_freshness_monitor`의 스캐너 경제성 section이다. 독립 보고서를 이 section에 단순 복사해 자체 승격을 유지하지 않는다. 기존 native source와 helper를 결합해 하나의 동일 예산 비교/검증 결과를 제공한다. 기존 Daily `daily_threshold_cycle_report.py:build_daily_threshold_cycle_report`의 source bundle/report에 이 section의 날짜·generation·hash·상태·경제성 요약을 연결한다. 현재 Daily가 이 결과를 직접 소비한다고 주장하지 않는다; 연결이 구현·검증해야 할 계약이다.

| 기존 파일 | 변경 책임 |
|---|---|
| `scanners/scalping_scanner.py` | 기존 원천·native rank/promotion/prune source와 실제 정렬 소비. 원 recipe/요청량·budget receipt가 있으면 그대로 연결 |
| `monitoring/intraday_ws_freshness_monitor.py` | 기존 scanner section에 same-budget 비교·분모·validation·산출물 상태 통합. 전체 WS health metric을 승격권한으로 변경하지 않음 |
| `scalping/scanner_lookup_attention_resource.py` | complete partition·same-tier baseline/candidate 선택 재현·changed union·기존 sampling/helper 재사용 |
| `strategy_position_performance_report.py` | 실제 완료 fact/cost source 유지. 이전 추천일의 늦은 완료 revision 갱신 경로만 필요한 경우 최소 보완 |
| `monitoring/scanner_lookup_attention_tuning.py` | 필요한 bounded 계산/검증은 위 기존 owner/helper에 이전. 독립 CLI 반복 평가·승격 구현과 중복 로직 제거; 실제 기존 caller가 없으면 compatibility wrapper도 남기지 않음 |
| `scalping/scanner_lookup_attention_policy.py` | 기존 publisher/loader의 integrated source receipt 검증. 단일 적용 파일은 실행 계약이며 독립 튜닝 보고서가 아님 |
| 기존 postclose/preopen wrapper·Daily·strict verifier | 독립 호출/flag/대기/DONE/필수 파일 계약 제거·통합 source 인계로 전환. 유효 원천 부재를 무조건 optional PASS로 만들지 않음 |

새 production module/DB/table/collector/service/timer/cron/정책 family/범용 학습 framework는 만들지 않는다. `src/engine` root에 새 Python 파일을 만들지 않는다. 함수 이전은 역할 package의 기존 파일 안에서 수행하고 old 구현·wrapper 잔재를 남기지 않는다. wrapper/automation을 실제 수정할 때 현행 운영 문서·체크리스트를 함께 갱신한다. Plan Rebase/README/runbook/AGENTS의 baseline 수정은 이번 계획 수립 범위가 아니다.

## 4. LA0 — 원천·실제 선택·budget 계약 고정

1. 현재 selected release와 workspace diff, 진행 중 worker·input lock·정책 pin을 확인한다. 병행 변경을 포함한 clean successor에서만 검증·배포하며 실행 중 source를 편집하지 않는다.
2. 조회 원천 순위/변화/top20 성분·source date/time·관측 점수·freshness·venue/session을 보존한다. 관심도 점수와 AI 판정/version을 별도 보존한다. API/FID/REG/request 수리는 현행 공식 Kiwoom reference gate 이후에만 한다; 이번 계획은 API 호출량을 늘리지 않는다.
3. 동일 generation·eligible universe·tier/rank partition·watch-budget owner·reserved/market-gainer partition·실제 가용 slot/정렬 순서/terminal을 freeze한다. 후보 eligible universe·owner quota·선예약·cooldown·기존 보유·거절 guard는 양측 동일하다. 현재 simple_capacity 밖 stateful replacement는 입증된 재현 경로가 없으면 별도 source-gap 제외한다.
4. 가중치0 baseline과 기존 단일 bounded formula candidate를 같은 source로 재현한다. 현재0.60/200 및 score 계수는 승인 증거 없이 확대/탐색하지 않는다. unchanged selection은 no-effect; eligible0/예산여유로 비교 없음은 no-competition이며 missing partition과 구분한다.
5. raw→invalid/excluded→eligible→unchanged/changed→mature/pending/source-gap을 보존한다. Symbol은 공식 master identity를 사용하며 신규 instrument/mixed venue를 문자열 형태만으로 승인하지 않는다.

Closure: actual selection 재현·모든 budget/partition 불변·교체 incoming/outgoing 및 episode 중복제거 key 보존. 더 많은 관측·선택 증가를 이익으로 취급하지 않는다.

## 5. LA1 — 선택이 달라지는 기회의 경제성 정의

Primary는 동일 frozen generation/budget의 **baseline 전체 선택 vs candidate 전체 선택**의 비용 차감 portfolio EV·순익이다. Changed union의 incoming gain/outgoing missed upside·avoided loss를 양방향 평가하고 unchanged와 함께 전체 같은 budget의 기준값을 보존한다. 종목 high-score/low-score 평균 차이는 진단으로 내린다.

- source에 존재하는 original initial-entry recipe/version·기계판정/실제 AI 결과·요청량·cash/reservation·가격·route·후행 exit/cost를 사용한다. 다른 세션 scale-in quantity/leg를 사용하지 않는다. 선택만 바뀌고 이후 guard로 진입하지 않는 경우 그 terminal을 양측 보존한다. 미호출 AI PASS·기계 BLOCK의 ENTER_NOW를 합성하지 않는다.
- Unselected 종목의 가정 진입/청산은 source-only CF로 표시한다. 신호 전에 계약된 requested quantity/budget와 guard/exit 평가에 필요한 원천이 없으면 structural source gap이다. 미래 체결수량·임의1주·현재 계좌를 대체값으로 쓰지 않는다.
- 기존 ordered BBO/depth·epoch·freshness·requested quantity로 spread/slippage·full/partial/no-fill을 분리한다. 현재 sampled BBO first-hit와180–360초 snapshot은 supporting proxy로 유지하며 실행가능 fill/exit 검증 없이 primary로 승격하지 않는다. 기존 source에서 실행 모델이 재현되지 않으면 지원 가능한 pair만 평가하고 source gap을 보고한다; 새 체결 시뮬레이터를 만들지 않는다.
- 동일 사전 고정 exit/horizon/stop·시간순서·capital reservation·동시 보유·회전율을 사용한다. snapshot 기간의 수익을 실제 holding exit 성과로 바꾸지 않는다. 기존 cost version 및 tax/fee/route를 결속하고 비용 부재는 null이다. broker 비용 미정산은 고정 비교 모델이라고 선언한다.
- 평가값은 pair 평균 ΔEV, 전체 budget EV/원화 순익, p10/worst·노출/점유시간·fill quality·coverage다. 정상 source-valid no-entry/no-fill의 모델 cashflow0과 source/cost 미확보 null을 구분한다. Actual COMPLETED는 유효 profit/cost/quantity 및 lifecycle conservation을 요구한다.

기존 bounded sampling은 future return을 보기 전에 시간순서로 정한 한정 cohort다. 기존 first32/nonoverlap sampling metadata를 그대로 보존하고 평가 scope를 한정 표본이라고 명시한다. Full census와 bounded evaluated cohort의 분모를 따로 기록한다. 모든 선택과 자본 경로가 재현되지 않으면 전체 budget EV/원화 순익은 null이며 교체 pair의 진단 ΔEV만 보고한다. 동일 episode가 세대마다 반복돼 표본 floor를 채우지 않게 한다.

Closure: 동일 기회·예산·실행/청산/비용 계약의 paired 비교가 재현된다. 실행 불가능/미확보 source를 유효 no-edge 또는 경제성0으로 바꾸지 않는다.

## 6. LA2 — 통합 출력·변경분 평가·자동화 이전

1. Existing monitor scanner section 아래 관심도 selection 비교의 metric contract를 선언한다: `metric_role=primary_ev`(유효 실행 모델 CF), `decision_authority=source_only_selection_economics`(검증 전), window/cost/source gate·forbidden uses. WS freshness 진단·BBO proxy·actual 성과는 각기 별도 role이다. Metric 이름이 실제 broker execution 또는 causal uplift를 과장하지 않게 한다.
2. 입력 fingerprint는 source content SHA·generation/partition/terminal·recipe/정책/quantity/budget·cost/exit/model version·완료 revision·holdout boundary를 포함한다. 신규 유효 changed pair 또는 늦은 outcome revision이 있을 때만 bounded 평가를 갱신한다. 같은 지문 재시도·휴장·eligible0·no-effect는 기존 결과를 참조하고 상태만 명시한다. 기존 incremental state/ledger를 사용한다.
3. 장중5분 monitor에 rolling90일 raw 전체 재스캔/holdout 재선정·정책 publisher를 넣지 않는다. Native incremental capture/cheap disposition만 수행한다. 최종 evaluation은 기존 scanner report 완결 경계에서 변경 입력에 한 번 수행하고 Daily가 같은 generation을 소비한다. 새 정기 단계/monitor 전체 추가 rerun으로 독립 heavy 작업을 치환하지 않는다.
4. 독립 장후 `RUN_SCANNER_LOOKUP_ATTENTION_TUNING` 호출·resource wait·JSON/MD/policy 대기·verify-only·DONE 필드와 strict 필수 old-artifact 요구를 함께 제거한다. 통합 source의 exact-date/source hash/review readiness 검증으로 인계한다. Deprecated flag가 env에 남아도 독립 producer를 복원하지 않는다.
5. 현재 retired conversion owner metadata는 native successor/as-of 요약으로 현행 owner에 연결한다. frozen 원본 hash를 조용히 고쳐 검증 PASS를 만들지 않는다. 실제 consumer가 successor mapping을 읽는지 검증한다.

Closure: independent heavy owner0·평가/promotion 중복0·Daily/summary/verifier가 동일 integrated source/date/hash 소비. 의도된 무수집·no-effect는 valid skip, 활성 source missing/stale·미완결 generation은 명시적 readiness 결손이다.

## 7. LA3 — 독립 검증·가중치 적용 조건

1. Current 가중치0 기준과 기존 단일 formula만 비교한다. Calibration 기회/날짜를 freeze한 후 후보·recipe·cost·exit·sampling/window를 고정하고 **그 뒤 미사용 날짜**를 holdout으로 사용한다. 이미 조회·선정에 쓴9/2–9/17 결과를 fresh holdout으로 재사용하지 않는다.
2. Existing real-completed gate(total20/dates5·cohort10/dates3 및 base/forward 분리)는 초기 이전에서 유지한다. High/low-score completed 비교가 단독 승인 근거가 되지 않도록 paired gate를 추가 결속한다. Same-budget CF의 유효 paired/window sample floor는 경제성 정의·기존 evaluator floor를 대사해 명시하며 arbitrary 새 공통20일·full-fill 조건을 source repair에 강제하지 않는다. Floor 미정이면 readiness blocked다.
3. Calibration와 독립 holdout에서 candidate 순비용 EV·순익이 양수이고 baseline 대비 paired ΔEV·budget 순익 개선이 양수여야 한다. 기존 small-net 불확실성·tail/worst/stress·coverage/owner guard도 통과해야 한다. Old +0.10% uplift 허들을 무심코 복원하지 않는다. 소표본 평균 양수만으로 승인하지 않는다.
4. 현재 KRX/krx_regular 범위만 이전한다. 기존 aftermarket monitor 관측은 보존하지만 KRX 결과로 NXT/integrated scope를 승인하지 않는다. 지원 확대는 별도 동일 market/session 원천·경제성 검증 없이는 하지 않는다.
5. Status는 source_gap/hold_sample/hold_no_effect/no_capacity_competition/hold_no_edge/independent_holdout_pending/ready를 분리한다. Current3개 음의 proxy와 sample 부족은 유지하며 수리 후 양의 EV를 강제하지 않는다. ready가 아니면 zero bonus baseline이다.

Closure: 동일 budget의 paired 개선과 독립 검증 및 기존 safety/sample/promotion predicate가 evaluator→publisher→PREOPEN validator까지 일치한다. 서로 다른 역할 gate의 PASS를 대체하지 않는다. 추가 operator 재승인을 gate에 끼워 넣지 않되 구현계획 자체를 실제 적용 승인으로 해석하지 않는다.

## 8. LA4 — PREOPEN→장중 정렬→Main 소비

통합 readiness 결과는 기존 **단일** `scanner_lookup_attention_policy` execution contract로 발행하고 integrated source/date/content SHA·검증/campaign·formula·scope·rollback0을 결속한다. Policy/report loader는 독립 old report가 아니라 integrated owner의 canonical source section을 검증한다. 이전 정책은 new promotion gate를 우회할 수 없으며 unsupported/legacy mismatch에서0으로 차단한다.

전체 장후 개선 완료 후 정상 정책 준비 경계에서 next valid target/source_date와 publisher window를 확인한다. 기존 PREOPEN은 exact-date immutable receipt를 만든다. 새 policy가 없거나 미검증이면 zero bonus inactive receipt를 정상적으로 만들고, 다른 entry/sizing 축의 strict failure는 보존한다. Runtime env/hash 수동 핀·날짜 복사·late first publication 우회는 하지 않는다.

장중 scanner loader→`_scanner_priority_profile`→candidate sort key→실제 slot/guard selection→promotion/prune/attach→Main initial-entry 기계판정→실제 compact AI→price/sizing→최종 guard→submit/fill/terminal을 연결한다. Source bonus0/active별 native score와 selection을 비교해 **가중치가 감시 대상을 바꾸는 것이 BUY 승인과 다름**을 입증한다. Same tier/partition/owner/cap 불변, 원천stale/conflict·타session·변조/누락 receipt는0이다. Loader/hash/fingerprint 검증의 장중 hot-path 비용은 기존 cache를 사용하고 이벤트마다 큰 integrated report를 다시 읽지 않는다.

선택 release·실제 source PID·loaded policy/date/hash·자연 rank difference·자연 entry/fill/완료는 분리한다. 기동/재시작은 기존 전체 적용 권한과 strict 운영 gate가 있을 때 정상 경로로 수행한다. 표본용 주문·봇/worker 수동 재시작·새 canary/shadow 서비스는 이 계획의 검증 방법이 아니다.

Closure: 변조·stale·잘못된 날짜/scope·미검증 후보 모두 bonus0; ready exact receipt만 기존 tier 내 bounded score 소비. 자연 selection 차이와 original opportunity/decision lineage가 연결되고 Main hard safety가 그대로 적용된다.

## 9. LA5 — 적용 성과와 지속 평가

Version은 policy/formula/source/holdout/composite entry version·target·owner·venue/session으로 구분한다. Original generation/opportunity→promotion/decision→recommendation/episode/order/fill/exit native key로 중복 제거한다. 실제 성과는 COMPLETED+valid profit/cost로 기존 rolling/cumulative/post-apply window에서 EV/순익/tail/노출·capital time·fill·기회당 완료율을 평가한다. Partial/HELD/no-fill/CF·과거 복구 수익은 별도다.

Model ΔEV와 실제 순익, causal uplift를 분리한다. 모델 오차는 동일 opportunity/quantity/cost/exit 정의가 연결된 경우만 계산한다. Policy 적용 완료0은 null/not-yet-mature이며 모델 수익을 대신 넣지 않는다. 적용 후 source/provenance/owner/safety 결함과 명시된 economic revert 조건만 기존 rollback0 경로로 처리한다. 표본 부족 또는 하루 이익 악화만으로 새 safety/rollback 규칙을 만들지 않는다.

Closure: integrated assessment→actual PID/source→natural selection/decision→cost-adjusted completed conservation. 기존 bounded maintenance review가 도래하면 source blocked/no-effect/no-edge를 구분해 통합 유지/추가 최소 수리/가중치 사용 중단을 판단하며 무기한 반복 수집으로 남기지 않는다.

## 10. LA6 — 개선 완료 후 과거 산출물 삭제

삭제는 사용자 조건부 요청에 따른 후속 단계다. **통합 code/review·targeted tests·새 report/policy roundtrip·Daily/strict 소비·old producer 제거·future runtime inactive/active contract·적용 버전 증거 보존**이 먼저 완료돼야 한다. 실제 positive candidate/수익 발생을 기다려야 cleanup 가능한 것은 아니다; 가중치0 유지/no-edge 결과에서도 올바른 소비/보존 계약이면 정리할 수 있다. 자연 새 적용 economics가 없는 경우 OPEN과 protected receipt를 보존한다.

1. 삭제 후보는 폐기된 standalone report JSON/MD, 재생성 가능한 완료 임시 projection/replay/cache/archive 사본이다. `data/report/scanner_lookup_attention_tuning/`, `tmp`의 정확 해당 task 산출물·사본을 파일 단위로 확인한다. `lookup` 문자열 전역 삭제·공유 디렉터리 삭제는 하지 않는다.
2. **보존**: 조회 원천/pipeline events·scanner/promotion/prune/BBO/depth·생존 observer state/lock/checkpoint·broker/account/order/holding/custody/완료ledger·공통 fact mart·clean baseline·미사용 holdout·current/rollback/applied policy 및 PREOPEN/hash/version acceptance receipt·active process input·통합 source·삭제manifest. 다른 session/release/worktree/Codex session은 범위가 아니다.
3. 과거 policy/PREOPEN도 applied/rollback/보존검증의 reference면 삭제하지 않는다. 미사용·retired·후행 reference0인 경우만 별도 exact inventory로 정리한다. Standalone 큰 report가 정책의 검증 원천으로 참조되면 해당 receipt/source snapshot을 보존 또는 authoritative successor로 인계한 후 삭제한다; 링크만 고쳐 provenance를 대체하지 않는다.
4. 작은 preservation receipt에 과거 원path/target/as-of/schema/hash·원분모·핵심 gate/EV·cost scope·현재 successor/reference mapping을 남긴다. 삭제 후보별 size/SHA·active process/lock/current source/reference 여부와 keep/delete 사유를 확정한다. Long-growing JSONL은 summary/streaming만 사용한다.
5. 실제 삭제 직전 selector·PID/source/input refs·SHA를 재검사한다. 변경/사용 중인 파일은 제외한다. unlink 완료·확보bytes·보존hash·old producer 재생성 부재·updated docs link를 검증한다. Dry-run count를 실제 삭제로 보고하지 않는다.

Closure: 필요 증거 reference 손실0·보존 파일 해시 불변·삭제 파일 부재·old standalone 재생성0·삭제manifest와 자연/경제성 OPEN owner 보존.

## 11. 리뷰·검증·완결 기준

| 경계 | 기존 테스트에 추가할 필요한 회귀 |
|---|---|
| Source/선택 | scanner candidate pool/source census/runtime scheduler·lookup resource: fixed budget/owner/tier, no-effect, complete partition, changed union, duplicate/stale/unsupported isolation |
| 경제성 | lookup net approval/resource·WS freshness: same-budget paired ±EV, quantity/cost/exit/source missing→null, partial/no-fill, future fill 금지·fresh holdout/time leakage |
| Fact 갱신 | strategy position performance: 늦은 완료 revision, exact rec-date 원row 보존/갱신·identity/비용 결손 |
| 통합/자동화 | existing lookup/WS freshness·Daily/strict/wrapper: duplicate publisher0, unchanged fingerprint heavy0, source hash/date/owner 불일치 실패·old flag 복원 차단 |
| Runtime | candidate sorting·policy loader/PREOPEN: same-tier/cap/guard 불변, invalid receipt0, integrated ready만 적용·existing cache·zero bonus baseline |
| Cleanup | exact inventory/reference/active input 보존·삭제 race/SHA·link/manifest 검증; 실제 입력 삭제를 테스트 fixture로 대신 인정하지 않음 |

기존 role package/source/test를 우선 재사용한다. implementation→self review→fix→re-review→targeted validation을 반복한다. Python compile·wrapper 변경 bash syntax·diff check·문서 link/owner/print-only parser를 수행한다. 전체 trading suite·raw90일 반복 scan·full postclose rerun·provider/API/order 호출·성능 benchmark 확장은 하지 않는다. 장중 비용 검증은 호출 구조/캐시·변경분 처리 회귀로 한정하고 필요할 때만 기존 bounded measurement를 한 번 사용한다.

단계별 결과는 code closure/배포/자연 원천/후보 readiness/PREOPEN/PID/실제 경제성/삭제로 따로 보고한다. Scope defect0·mechanical PASS가 positive EV가 아니다. 구조적 source gap에는 owner/input/evidence/next action/closure test를 남기고 ETA는 근거 없으면 null이다.

Executable owner는 [당일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `ScannerLookupAttentionConsolidation0918` 하나다. 기존 다른 경제성·Main/PREOPEN·scale-in owner와 중복 승인권을 만들지 않는다.9/21은 사용자 예정 적용 준비 target이며 실제 운영 calendar/전체 선행 closure로 확인한다. 후속 checklist 이전 시 stable ID/Acceptance/History를 보존하고 current parsed owner 하나를 확인한다.


## 12. 구현 판정과 남은 원천 경계

현재 실행 모델 원천은 `sniper_missed_entry_counterfactual` 자체가 exact fill/exit/cost replay missing을 선언한다. 선택되지 않은 종목의 original recipe/요청량/실제 guard와 full capital path가 없으므로 별도 체결 시뮬레이터를 새로 만들지 않고 primary를 null/source_gap으로 인계한다. 이 상태에서 publish 가능한 정책은 가중치0뿐이다. 양의 snapshot 또는 high/low completed 평균으로 active 정책을 만드는 구형 경로를 차단한다. **실행가능 portfolio CF와 독립 forward holdout을 거친 positive 자동 활성화는 아직 달성되지 않았으며 LA1/LA3의 자연·경제성 closure가 아니다.** 현행 source 계약에서 그런 ready 주장은 validator가 거부한다. 나중에 원천이 생긴다는 이유만으로 자동 ready로 바뀌지 않는다; 기존 실행 owner가 양측 재현 계약을 제공한 뒤 그 계약의 evaluator/publisher/PREOPEN 검증을 함께 보완해야 한다.

현재 구현은 기존 monitor의 native 변경분 수집과 최종 경계 평가, standalone CLI/publisher/장후 호출 폐기, 통합 source→Daily/EV/summary/strict→zero policy→dated PREOPEN 준비 경로다. 원래 frozen 산출물은 compact preservation receipt로 보존하고 현재 fact revision을 exact identity로 재결속한다. native 변경분 없는 재시도는 input fingerprint를 재사용하며 rolling raw90일을 읽지 않는다. 과거 giant state/raw 재구축 없이 existing report의 lookup section만 후속 갱신한다; 부모 monitor의 intraday/as-of와 다른 section은 그대로이며 lookup의 postclose phase·generated_at은 별도다. 수리되지 않은 이전 날짜의 full observation census는 historical diagnostics이며 신규 natural 표본으로 복제하지 않는다.

9/17 source를9/18 expected non-collection publication에 결속한9/21 준비 정책을 발행한다. source_evaluation_date/publication_date/prepared_effective_date를 분리하며 PREOPEN receipt는 실제 target일09:00 이전 정상 경계에서만 동결한다. 전체 장후/PREOPEN/Main 기동·PID·실제 EV 완료를 이 단위의 source review PASS로 표시하지 않는다. 자세한 결과·검증·배포·삭제는 [통합 구현 review](../audit-reports/2026-09-18-scanner-lookup-attention-consolidation-review.md)와 `tmp/scanner-attention-consolidation-20260918/` receipts를 따른다.
