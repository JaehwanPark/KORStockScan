# 위젯·episode 장후 정책 연구 로직 점검 — 2026-09-17

## 1. 결론과 점검 범위

위젯과 episode 연구 전체가 체결 종목만 분석하는 것은 아니다. **분봉에서 체결 없이 신호를 재생하는 연구는 이미 있지만, 실제 제출·실현 사례를 요구하는 timing adapter가 남아 있으며, 후보 탐색의 EV 목표와 총 순이익 목표도 완전히 같지 않다.** 미진입 전수 튜닝만으로 전체 정책 연구의 수익 극대화가 증명되는 구조는 아니다.

사용자 요청에 따라 원천→연구→선정→정책 전달을 코드로 점검하고 계산 최적화 계획을 작성했다. 기준 작업본 HEAD는 `052c7be30eb8aa971fbc6847f71ac56692d36435`. 다른 작업의 수정본은 보존했다. 코드 수정, production 연구 재실행, provider 호출, 정책 발행, 배포·재기동은 이 점검에서 실행하지 않았다. 아래는 작업본의 로직 판정이며 현재 selected release/PID의 동일 코드 소비를 증명하지 않는다.

기준: Plan Rebase §1–§8, 오늘 체크리스트의 목적·강제 규칙, [전수 튜닝 계획](../proposals/entry-opportunity-cost-full-population-tuning-implementation-plan-2026-09-17.md) §7.3/U10A/U10B, [위젯 source closure 기록](2026-09-17-widget-postclose-source-closure-implementation.md). 기존 완료된 계산 최적화와 자연 생성 OPEN을 다시 구현 미완료로 돌리지 않는다.

## 2. 실제 연구 흐름

| 경로 | 입력과 연구 | 선정·전달 경계 |
| --- | --- | --- |
| Widget symbol signal | 고정·watch·추천 등록 universe의 clean-baseline 이후 분봉. 신호 조건 1,536개와 일일 entry cap 1–5를 재생. next-bar entry, target/support-break/force-flat, 비용을 모델링 | Calibration/두 half에서 후보를 정한 뒤 최근 16 거래일 holdout 검사. 기존 baseline이 있으면 signal-only/exit-only component 비교를 추가한다. source·incident·policy 계약을 거쳐 KRX regular 정책 후보로 전달 |
| Widget auto/advisory calibration | session별 PASS 자연 관측, signal seed, add/target/cutoff/cooldown/cap 조합 재생 | 날짜를 calibration/holdout으로 분리. 최근 paired replay 선정 경로는 base/stress, 순익·tail·점유·빠른 수익 비교를 사용. 동적 universe도 관측하지만 AM의 regular 경제성 전용과 자동 승격은 금지 |
| Episode attribution/timing | 실제 machine decision anchor와 lifecycle, raw BBO/depth/epoch, owner outcome. fixed delay와 per-signal dynamic confirmation 재생 | 실제 제출/실현을 요구하는 경제성 adapter가 존재. source-only replay 출력도 있으나 같은 actual cohort에 묶인 부분이 남음. timing approval/다음 PREOPEN 소비는 별도 |
| Samsung entry / low-price 2leg | 삼성 보고서는 기존 admission 축·실제 leg 결과를 설명. 저가주 expanded research는 분봉 기반 entry/leg CF와 calibration/holdout 연구도 수행 | 삼성 subset 관찰은 relaxation backtest가 아니며 새 tightening 권한도 아님. 저가주 existing-axis replay는 해당 family의 자동 후보 계약으로 전달; minute-bar proxy는 실체결 증거가 아님 |
| Lifecycle turnover | 동일 lifecycle의 target-timeout 60/120/180초를 source-only 비교. rolling 5/10/20 거래일·비용·coverage·capital efficiency | 후보 연구 전용. 새 runtime exit family나 apply 권한을 등록하지 않는다. 미실현 holding은 경제성 0으로 계산하지 않는다 |

주요 코드 근거:

- [signal universe/grid/replay](../../src/engine/monitoring/widget_symbol_signal_policy_research.py): `load_symbol_universe`, `policy_grid`, `evaluate_policy`, `discover_symbol_policy`, `build_report`.
- [component selection](../../src/engine/monitoring/widget_signal_quality.py): `select_policy_component`.
- [auto calibration](../../src/engine/monitoring/widget_auto_trade_policy_calibration.py): `_specs_for_target_date`, `_research_accumulation`, `_calibrate_session`, `build_policy`.
- [paired replay](../../src/engine/monitoring/widget_paired_policy_replay.py): `select_candidate`.
- [timing](../../src/engine/automation/machine_entry_timing_tuning.py): `_candidate_observation`, `_decision_economic_baseline`, `_evaluate_dynamic_cohort`, `_evaluate_cohort`.
- [attribution](../../src/engine/monitoring/machine_microstructure_attribution.py), [turnover](../../src/engine/monitoring/machine_lifecycle_turnover_policy_research.py), [저가주 연구](../../src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py).

## 3. 확인된 한계와 보완 순서

### R1 — 미진입 timing 연구의 actual-only cohort: P1, 기존 U10A 잔여

**근거:** timing `_candidate_observation` 약 494행 이후는 `actual_order_submitted=true`와 `owner_outcome.realized=true`를 요구한다. `_decision_economic_baseline`의 최종 계약 검사도 같은 요구가 있다. `_evaluate_dynamic_cohort` 약 1330행의 `source_owner_rows` 역시 실제 제출된 owner row만 받는다. 따라서 dynamic replay가 source-only라는 사실만으로 미제출 signal의 전수 경제성 평가가 연결되었다고 볼 수 없다.

실체결 arm을 검증할 때 이 요구는 적정하다. **그 adapter를 미진입 연구 전체의 공통 admission으로 사용하면 후보가 먼저 실제로 거래되어야 연구에 들어가는 순환조건이 된다.** raw에 미진입 진단이 존재하는 것과 최종 selector가 비교하는 것은 다르다.

- Owner: 전수 계획 U10A, 현재 체크리스트 `KiwoomCommonHealthOpportunityCostAcceptance0917`.
- 다음 작업: before-gate 실제 decision anchor의 공통 opportunity union을 만들고 actual adapter와 executable source-only adapter를 분리. incumbent reject의 modeled payoff와 대안을 같은 비용·수량·기간으로 비교한다.
- Closure: 유효한 no-submit 신호가 paired denominator/선정/approval 소비까지 보존되고, signal 없는 prospective diagnostic는 학습 표본이 되지 않는다. stale/depth 부족/cross-epoch/censored는 보존된 disposition으로 남는다. actual 검증 조건을 삭제해서 해결하지 않는다.

### R2 — 최초 후보 탐색 목표와 총 순이익 목표의 차이: P2, 확정된 목적함수 한계

**근거:** signal `_summarize_episodes` 약 1148행은 entry price 한 주 기준 notional-weighted EV를 계산한다. `discover_symbol_policy` 약 1395행의 rank는 두 calibration half 중 낮은 EV에 표본수 감쇠를 곱하고 episode count를 tie-break로 쓴다. 실제 수량·공유 자본으로 계산한 순익/source day를 주목적으로 탐색하지 않는다. Auto `_calibrate_session`의 기본 rank도 EV와 단순 수익률 합 중심이다.

예를 들어 같은 관측기간에 A가 유효 기회 10건에서 각 1%를 벌고 B가 100건에서 각 0.4%를 벌면 높은 EV와 큰 총 순익이 다른 후보를 가리킬 수 있다. 이 예는 로직 설명이며 실제 정책 수익 추정이 아니다. 이후 guard가 있어도 최초 탐색에서 버린 후보를 반드시 복원하지는 않는다.

**이미 보완된 부분:** signal component 비교는 qualified-day 순익·점유·180초 내 양수 청산을 검사하며 calibration 순익으로 single-component winner를 고른다. Paired selector도 일별 순익 비훼손을 요구한다. 그러므로 전체 selector가 EV만 본다는 결론은 틀리다.

- Owner: U10A의 widget 선정 계약. 기존 family primary metric을 임의로 교체하지 않고 변경 계약을 먼저 명시한다.
- 다음 작업: 탐색 단계부터 공통 source days·등록 수량·capital occupancy·총 modeled net profit·참여율을 산출. 기존 EV/tail 안전조건 아래 순익 목표의 후보를 보존한다. 단일 EV winner만 축약해 보존할지 재검토한다.
- Closure: 높은 EV/낮은 총순익, 낮은 EV/높은 총순익, 음수 incremental entry, 자본 초과 사례를 독립 fixture로 비교하고 calibration winner를 holdout 전에 동결한다.

### R3 — 관측 universe 내부 전수와 시장 기회탐색은 다름: P2, 범위 한계

**근거:** signal `load_symbol_universe` 약 146행은 고정 종목·등록 watch·유효 추천 종목에서 universe를 만든다. Auto `_specs_for_target_date` 약 305행도 이 universe의 비정적 종목을 AM 관측 lane으로 추가한다. 동적 확장은 이미 있어 고정 몇 종목만 연구한다는 주장은 맞지 않는다. 그러나 등록되지 않은 종목은 이 symbol 연구로 새로 발견되지 않는다.

- Owner: U10A와 기존 scanner/census→추천→watch 등록 경계. 별도 새 전시장 collector를 바로 만들 필요는 없다.
- 다음 작업: 기존 scanner 후보/차단/추천 census에서 universe 입출구를 대사한다. 탐지했으나 등록되지 않은 후보, 등록 후 원천 부족, 유효했으나 정책 탈락을 구분한다. 실제 주문 없는 후보도 기존 원천으로 연구 admission을 검증한다.
- Closure: 시장 census→등록→raw source→qualified 연구→selected/carry/blocked의 native ID·count 보존식과 누락 사유를 확인한다. 19종목 관측이나 원천 PASS만으로 전시장 recall을 주장하지 않는다.

### R4 — 분봉 모델의 수익과 실행가능 수익 차이: P1 경제성 증거 경계, 자동 bypass 결함은 미확정

**근거:** signal `_find_entry`/`_exit_episode` 약 905–1020행은 next-bar open과 minute high/close로 진입·target·support exit를 모델링한다. 비용과 같은 bar의 adverse 우선 처리는 있지만 주문 대기열·원래 수량의 depth·TTL·부분체결의 증명이 아니다. 저가주 expanded research 역시 minute-bar touch를 proxy라고 명시한다.

이는 빠른 신호 연구로 유효하다. 다만 signal holdout PASS·execution incident 없음이 모든 CF 주문의 실행가능성을 대신하지는 않는다. 이번 점검에서 실제 trader의 hard guard bypass나 그로 인한 손실은 확인하지 않았다.

- Owner: U10A의 capacity/exit 계약과 기존 approval. 실제 주문·수량·custody guard 보존.
- 다음 작업: 실제 decision에 붙은 raw BBO/depth/지연·원래 주문/exit 계약으로 실행가능 arm을 재검증. 원천 없는 과거 minute-bar 후보는 proxy 단계로 남기고 수익·missed profit을 실행 보장으로 표현하지 않는다.
- Closure: high touch지만 수량 부족, target 변경 후 원래 target fill 재사용, 같은 bar 양방향 touch, 부분체결/TTL/censored 사례가 경제성 승인 근거에 섞이지 않는지 검사한다.

### R5 — source-day와 공동 자본 평가의 불완전성: P2, 추가 계약 검증 필요

**근거:** fixed timing `_evaluate_cohort`는 성공적으로 구성된 observation의 날짜에 rolling window를 만든다. Widget paired `select_candidate` 약 642행도 pair가 있는 source dates를 calibration/holdout 및 일별 순익 분모로 사용한다. 이는 최근 20 거래일 calendar floor와 다르다. Dynamic timing은 별도 `source_report_dates`를 사용하므로 모든 timing 경로가 같은 결함이라는 주장은 피한다.

source가 유효하되 signal이 0인 날, source 누락인 날, pair가 censored인 날을 구분하지 않으면 일별 수익/참여빈도 비교의 의미가 달라진다. 또한 개별 symbol/session 보고서의 좋은 후보를 함께 적용했을 때 공유 자본·동시 진입·custody/cooldown이 허용하는 결합 순익은 이번에 읽은 개별 연구만으로 증명되지 않는다.

- Owner: U10A의 공통 source-day/기회 비교 및 U11 자동 handoff. 전체 repository에 joint allocator가 없다고 단정한 finding은 아니다.
- 다음 작업: qualified source-day ledger로 0신호/누락/차단을 분리하고, 실행 등록 후보들의 동시 replay를 기존 자본·owner 계약에 맞춰 대사한다.
- Closure: valid-zero day 추가 시 총순익 불변·day 분모 증가, missing day는 0 PnL이 되지 않음, 겹친 두 후보의 자본 이중 사용 금지. 개별 수익 합과 feasible 결합 수익을 별도 출력한다.

## 4. 결함으로 오인하지 않을 경계

- **이번 코드에서 holdout winner 탐색을 확인하지 않았다.** Signal discovery는 calibration에서 후보/cap을 동결한다. Component selector도 calibration에서 single winner를 정하고 그 winner의 holdout을 검사한다. Paired selector도 calibration winner가 holdout에 실패하면 다른 holdout winner를 찾아 바꾸지 않는다. 매일 겹치는 holdout의 반복 사용에 따른 연구 과적합은 별도 통계 위험이며 이번 코드의 미래정보 누출로 확정하지 않는다.
- AM 동적 관측과 KRX regular 정책은 별개다. DUAL AM automatic promotion 금지와 session-specific 자연 표본 조건을 통과했다고 아직 주장할 수 없다. no-seed raw-only 관측은 정책 신호 표본이 아니다.
- Regular 300/AM 240 PASS 관측 등의 accumulation 조건은 coverage 요구다. raw watcher의 full-history bars가 BBO·signal 관측 수를 대신하지 않는다. 종목별 실제 sampling 간격과 budget으로 조건 달성이 가능한지는 자연 owner가 측정해야 하며 임의로 floor를 낮추지 않는다.
- Turnover는 rolling capital efficiency를 비교하는 **후보 전용** 연구다. independent holdout과 registered exit-family 소비를 이번 경로에서 확인하지 못했다. 따라서 빠른 회전 자동정책 완료로 부를 수 없지만, source-only 설계를 자동 발행 결함으로 바꾸지도 않는다.
- 실제 holding/exit·broker 비용 회계가 실제 체결을 요구하는 것은 맞다. 이를 미진입 표본으로 대체하거나 미실현/누락 outcome을 0으로 넣지 않는다. OFF/retired consumer를 복구하지 않는다.

## 5. 다음 실행과 검증 상태

우선순위는 R1의 공통 admission→R3 universe 입출구→R4 실행가능성→R2 목표함수→R5 source-day/결합 비교다. R1은 새 발견으로 별도 OPEN을 중복 생성하지 않고 기존 U10A에 이 증거를 연결한다. R2–R5는 실제 consumer별 계약을 확인한 뒤 필요한 구현 범위를 확정한다. 계산 최적화는 [세 후보 계획](../proposals/postclose-computation-optimization-implementation-plan-2026-09-17.md)에 분리했다. 현재 편향을 빠르게 재현하는 것만으로 전수 연구 완료를 판정하지 않는다.

문서 검증 완료: 신규 두 문서의 상대 링크 결손 0, trailing whitespace 0, owner·authority 재검토와 `git diff --check` 통과. Print-only checklist parser가 32개 항목을 출력했고 위 통합 owner와 widget 자연 owner는 각각 오늘 체크리스트에서 1개씩 확인됐다. 문서-only 작업이므로 pytest, provider/API 호출, production 보고서 재생성, selected release/PID 검사는 실행하지 않았다. 자연 정책·실체결·cost-adjusted net profit 개선은 이 보고서의 수료 조건이 아니며 기존 OPEN에서 확인한다.

## 6. 후속 구현 인계

위 §1–§5는 최초 read-only 점검 시점의 기록이다. 이후 별도 사용자 지시로 R1–R5의 원천 adapter·목표함수·census handoff·실행가능성·source-day/자본 경계를 보완하고 반복 리뷰·검증을 수행했다. [구현·검증·배포 기록](2026-09-17-widget-episode-policy-research-implementation.md)을 현재 상태 owner로 참조한다. 원래 연구 누락이 재현되는 옛 코드와 실제 selected consumer를 섞지 않는다. 미등록 종목의 새로운 원천, 자연 공통-horizon 표본, 공동 capital contract와 실현 수익은 별도 원천/자연 acceptance이며 코드 테스트만으로 완료되지 않는다.

## 7. 전체 폐루프·연구 확대 성능 후속 계획

사용자의 추가 계획 보완 지시에 따라 [전체 폐루프·성능 상세 구현계획](../proposals/widget-episode-full-closed-loop-and-scale-performance-implementation-plan-2026-09-17.md)을 작성했다. §1–§5는 초기 read-only 리뷰, §6은 선행 코드 보완 인계다. 기존 조건부 자동 발행이 없다는 뜻이 아니며, 아래 잔여를 선행 R1–R5 코드 배포 완료와 혼동하지 않는다.

| 잔여 | 상세 단계 | 완료 증거 |
| --- | --- | --- |
| Canonical census 누락→인과적 후보 admission→budgeted research catalog | C0–C2 | Native ID/count·defer/source gap·원래 clock/session을 보존한 전체 admission과 수집 coverage |
| 새 정책의 과거 seed 부재 bootstrap·분봉 proxy와 실행검증 분리 | C3 | Historical full-grid 탐색→candidate freeze→전향적 calibration/holdout; 과거 quote 합성·winner 재탐색 금지 |
| 공동 자본 결과를 최종 선정·발행에 결속 | C4–C5 | Existing allocator/owner snapshot 아래 feasible joint profit·incumbent 비교·독립 publisher 재구성 |
| 신규 종목/registered 정책의 익일 자동 소비와 성과 회수 | C6–C8 | PREOPEN owner activation→actual consumer ack→full/partial terminal·exact-cost version attribution→final handoff |
| 확대 N/D/G/K·I/O·관측·deadline·disk/RSS 오버행 | P1–P6/critical path | Full semantic parity, 19/50/100종목 cold/warm/append/정정/재개 계측과 capacity·deadline·storage receipt |

기존 `load_symbol_universe`의 완료 일일 추천 자동 편입, widget next-date publisher/dated reader, episode 신규 종목·시간대 auto-expansion publisher/service는 재사용한다. 자동 미등록 후보 admission, 실행 source와 joint decision의 최종 gate 결속, 자연 generation/소비/성과까지의 전체 closure는 **후속 계획**이다. 전향적 이중-window 변경은 새 계약 제안이며 현재 gate를 문서로 해제하지 않는다.

현재 raw REST budget에서 nominal cycle은12N초이며 N19=228초/N50=600초다. Historical bar 수집의 universe 확대만으로 subsecond timing/fresh5초 BBO나 full-session coverage가 생기지 않는다. 과거 전체 구간에 새 seed를 요구하는 검증 순환조건과 낮은 sampling capacity를 각각 닫아야 한다. 성능은 기존 최적화된 correctness reference와 비교하고, grid/미진입/zero-day 표본 축소로 deadline을 맞추지 않는다.

[계산 최적화 계획](../proposals/postclose-computation-optimization-implementation-plan-2026-09-17.md) O0–O3에 추가 범위/의존을 연결했다. 현재 owner는 오늘 checklist의 `KiwoomCommonHealthOpportunityCostAcceptance0917` 및 `WidgetPostcloseEvaluationPinAcceptance0916`을 유지한다. 본 추가는 문서-only이며 새로운 자동 실행·운영 권한·구현 완료를 뜻하지 않는다.

이번 전체 폐루프 source 구현과 반복 리뷰·규모 실측/배포 상태는 [09-17 구현 기록](../audit-reports/2026-09-17-widget-episode-full-closed-loop-implementation.md)을 따른다. C0–C8/P1–P6 producer/consumer를 연결하며 자연 신규 정책·actual next-date 소비·경제성은 기존 stable-ID acceptance owner에서 따로 확인한다. Final-refresh의 native account source 취득은 N/K에 비례하지 않고 기존 read adapter/cached token만 사용한다. Timer/grid/caps/sample/hard guard는 유지한다.
