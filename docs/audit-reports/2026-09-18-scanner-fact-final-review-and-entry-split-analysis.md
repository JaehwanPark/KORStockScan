# 조회 관심도·fact 재리뷰와 다음 장후 단위 분석 — 2026-09-18

## 판단과 범위

사용자1번 요청은 기존 scanner integration/fact 계약의 재리뷰·필요 보완·commit/push/deploy 및 불필요한 과거 산출물 정리다.2번의 다음 단위는 read-only 분석이며 해당 Python·wrapper·정책·원천은 수정/재실행하지 않는다. 신규 module·collector·simulator·서비스·주문·provider·env·guard 변경은 없다. 기존 positive same-budget activation 구조결손은 이번 코드검증 성공과 분리한다.

실제 선택본이 처음075abe9d였으나 병행 세션이649f1b9d로 승계했다.649f1b9d는075abe9d와 직전e8e9a04b를 병합해 bounded proof export·primary missing metrics null 검증과 독립 scale-in holdout chronology를 함께 보존한다. 이 병합 source를 기준으로 affected producer/decoder/policy/PREOPEN/Daily/EV/strict/cache/date와 fact-sync/완료 경제성/미래 scanner provenance exclusion/원천 실패 시 prior fact 보존을 재리뷰했다. 추가 in-scope source 결함은 발견하지 않아 같은 기능을 다시 작성하지 않는다. 보완 및 재리뷰는 이전 수정과 현행 병합에서 유지되는지 확인했다. 관련261 pytest PASS(기존 dependency warning1); source compile·bash·diff·문서 parser·router·소비 SHA는 `tmp/scanner-attention-followup-review-20260918/`의 최종 receipts를 따른다.

## 산출물 정리

독립 `data/report/scanner_lookup_attention_tuning`은 직전 삭제28개/26,377,207bytes 이후 잔여 파일0이다. 실제 삭제는 기존 `tmp/scanner-attention-consolidation-20260918/deleted-products.json`이며 이번 추가 삭제0이다. `strategy_position_performance_report`의 현행 CLI는 JSON/MD report history 대신 DB TradePerformanceFact/StrategyPositionPerformanceDaily와 `strategy_position_fact_sync` status receipt를 만든다. 동명 report directory/과거 파일은 없다.9/14~9/18 receipt5개는현행 consumer provenance이므로 보존한다. 실제 모듈명과 산출물 directory를 혼동해 DB fact/receipt를 삭제하지 않는다. `.env`·baseline·동기화 receipt·현행 execution policies·entry split 분석 원본의 byte SHA를 보존한다. 원천·관측 필드·fills/terminal/custody·current/rollback/generation/PREOPEN·compact migration 증거도 삭제하지 않는다.

9/17 sync receipt는23:56:05 generated/valid_empty/fact0/consumer_ready=true이며 기간 내 실제 거래가 없다는 뜻이 아니라 그 source-date 동기화 대상이0이라는 뜻이다. fee/tax comparison rate0.0023·broker_cost_reconciled=false다. 다른날짜 rolling scanner 완료5건과 충돌하지 않는다.

## 다음 실행 단위 식별

과거9/5 inventory #49 다음 항목은 #50/#51/#54 `daily_threshold_cycle_report`/AI correction/cumulative였다. 현행 selected wrapper에서는 standalone #49가 폐기됐고 fact-sync→scale_in_split_order_plan→`entry_split_order_plan`→AI quality materialization/R0–R3 원천 준비→Daily/AI correction/cumulative다. `opening_rotation_profile_tuning`은 retired이며 다음 실행 작업이 아니다. 다른 세션 검증 중 scale-in은 수정하지 않는다. 따라서 다음 개별 경제성 단위는 기존 #75 **entry_split_order_plan**, 이후 대표 집계가 #50 Daily다. Monitor finalize의 lookup subsection은 더 후행인 기존 scanner boundary에서 갱신된다.

## entry_split_order_plan 9/17 결과

native request1020은9/18 00:13:36.979~00:14:34.763(요청~완료 약57.8초)이며 exit0다. 보고서 generated00:14:34, generation8607db22…·policy/report content binding이 존재한다.9/5 inventory가 아닌 이 exact-date native request/result/review와 현재 원본을 기준으로 한다. 원본의 source warning은 tuning_input_allowed=true/hard gap0이며 blanket source blocking이 아니다.

| context | real sample / split 완료 관측 | bucket 평균(%) | 판단 |
| --- | --- | --- | --- |
| balanced_normal | 40 / 26 | −0.6835 | mature parent edge contradicted, 보류 |
| guarded_or_stale | 110 / 81 | −0.4103 | mature parent edge contradicted, 보류 |
| passive_wide_or_weak | 185 / 50 | −0.0001 | 정확 child3건 평균+0.7853%만 bounded seed 통과; 최종 발행 차단 |
| urgent_tight_spread | 2 / 1 | +0.6200 | sample 부족 |

이 bucket 평균은 incumbent 대비 비용 차감 ΔEV가 아니다. Passive exact child는 `qty_clipped_legs2/runtime_first_weight20/probe1_fill_clamped_bbo` 형태3건이고 parent/default의 다른 형태와 섞을 수 없다. 전체 passive sim429,200건은 real split 품질 증거가 아니며 오래된 탐색 cohort를 새 독립 검증으로 세면 안 된다. Positive child3건을 전체 정규주문 EV 개선으로 일반화할 수 없다.

원천 atomic sizing plan 당일3/invalid3/valid0, real submit with/missing plan0, selection_blocked=true. 최종 candidate0/explicit bucket0/exploration_seed=false/EV validated=false/runtime_apply=false이며 missing bucket은 keep_original_order다. Source-level child seed PASS는 최종 policy PASS가 아니다.

four-arm(기존/후보 quantity×기존/후보 leg) receipt0·eligible0·complete0·join coverage null·calibration/holdout0이다. 양측 요청량·entry price receipt·exit policy·비용·terminal conservation·venue/session·policy/attempt/hash가 같은 union을 비교하고 시간 순서 holdout까지 확인해야 승격한다. 현행 gate는complete30/coverage80%/candidate cost-adjusted EV0.1%/participation 감소≤5%이며 positive frequency·capital efficiency·tail도 비열화를 검사한다.30건만 채우는 것이 source 계약 수리의 대안은 아니다. 이 gate가 초기 baseline 사용을 금지하는 것은 아니며 challenger promotion과 분리한다.

기존 producer는 `strategy_owner_replay.build_entry_opportunity_replays`이며 raw frozen price-ready plan/seed→native executable source→four-arm signed receipt를 만들고 entry split/Daily가 소비한다. Producer 없는 기능이라고 단정하지 않는다.9/17 평가의 native replay raw_plan_rows0/unique0/completed0/maturity_waiting0이며 원자 plan 진단3과 같은 분모가 아니다.3개 invalid의 상세 원본 사유/plan vs block 구분을 이 bounded artifact만으로 확정하지 못했다. 큰 raw를 재스캔하지 않고 source/compact projection·stage·fields·eligible filter를 먼저 대조해야 한다. 현행 source package가 이미 이 계약을 보완했더라도 다음 자연 유효 plan→receipt가 확인되기 전에는 과거0을 새 수리 성과로 바꾸지 않는다.

## 대기로 해소 가능한 것과 구조결손

- **대기 조건**: 다음 영업일의 유효 plan/BBO/depth/cost가 이미 생성·결속되는 경로를 확인한 뒤 horizon maturity, post-sell pending223건, urgent real2건 등의 표본 부족은 자연 성숙/누적으로 개선될 수 있다. 오늘 휴장·미적재는 collection 비대상이며 ETA는 실제 유입 없으면null이다.223건 모두 시간이 지나면 완료한다고 보장하지 않는다; irrecoverable missing source와 censored/unclosed를 먼저 나눈다.
- **현재 원천/계약 blocker**:9/17 atomic invalid3/valid0와 price-ready replay census0/four-arm0. 시간만으로 과거 frozen plan/누락된 요청량·BBO·terminal·비용을 복원하지 못한다. Owner는 existing entry_execution_sizing_plan emitter→native decoder→strategy_owner_replay→entry_split evaluator다. Closure는 자연 price-ready eligible plan1건의 원본 recipe/quantity/hash/venue/session→동일 signed source date receipt→consumer complete count 증가 및 누락 분모 보존이다. 상세 invalid reason은 추가 source 대조 전 미확정이다.
- **기존 데이터의 경제성 한계**: parent negative mean은 비교 집단/시장/형태 효과를 분리한 causal 손실 판정이 아니고, child3건+0.7853%는 작은 observational seed다. Win rate나 sim건수로 source gap과 독립 holdout을 대체하지 않는다. 동일 old source를 반복 평가해도 새 independent EV가 생기지 않는다.
- **selection/PREOPEN/PID·실제 성과**: 기존 immutable generation policy→Daily envelope→PREOPEN guard→runtime allocator와 qty-preserving broker guards가 소비 경로다.9/17 Daily의 handoff는 not_selected/policy_disabled이고 actual runtime process consumption=false다. 실제 적용 version/episode 중복 제거·COMPLETED/실제 비용/rolling-cumulative 비교 손익·tail/exposure/model error는 이번 artifact에서 입증되지 않아 null/미평가이며 새 이익0이라고 표현하지 않는다. 다음9/21 PREOPEN은 전체 단위 보완 후 정상 준비 경계에서 별도로 확인한다.

## Daily/AI correction/cumulative 후속 결과

native review1023(exit0/00:24:31 완료)에서real completed rolling7d18/loss4, sim22, same-day projection3518건이다. AI correction은19 candidate families 중review required0으로 `skipped_no_review_candidates`이며 추가 provider 호출/비용0은 호출하지 않았다는 증거다. Profit0이나 튜닝 성공이 아니다. 하나의 submit-stage entry_split OFF envelope가 next PREOPEN 후보로 들어갔다. `runtime_apply_eligible_now=true`는 **OFF 후보 전달 가능**이며 positive split 활성화가 아니다. 보고서 현재/권고 enabledfalse/runtime_change=false, runtime constant state는PID 증거가 아니다. 앞선 atomic invalid와 negative parent 결과를 보존하고 passive 작은 positive child를 publish하지 않는다.

Daily는 source별/window별 rolling·cumulative, source quality와 attribution, deterministic 후보/AI review/단일 stage owner·rollback을 전달하는 통합 owner다. 집계 완료/후보OFF만으로 EV 개선 기여량은 계산되지 않는다. 실제 blocker/손익을 잇는 데 유지 가치가 있으나 데이터나 source가 동일한 독립 추가 반복 평가의 경제성은 없다. 이 분석에서 entry split/Daily/report/policy/provider를 수정하거나 재생성하지 않았다. 전일 native 전체chain의 blocked_native_resource_guard는 단위exit0와 별개이며 전체 DONE을 주장하지 않는다.

## 다음 closure 순서

1. 기존 source/projection에서 invalid3의 구체 사유와 native replay eligible0의 첫 탈락 지점을 확인한다. 이 분석은 code mutation을 승인하지 않는다.
2. 이미 배포된 계약의 다음 영업일 자연 유효 price-ready plan→source-bound native receipt→entry split/Daily 동일 hash·분모를 확인한다. 유효 표본0은 valid no-edge가 아니다.
3. 이후 현행 chronological four-arm/수량 보존/비용·tail·자본·체결 참여 기준으로 기존 후보를 검증한다. 과거 child3건을 새 holdout으로 재사용하지 않는다.
4. 실제 선정이 생기면 PREOPEN receipt→actual PID/version→자연 주문·full/partial→episode별 실제 완료 비용의 rolling/cumulative EV·순익·tail·노출·모델 오차를 평가한다. Model ΔEV와 실제 이익은 분리한다. 같은 stage의 다른세션 quantity/scale-in 정책과 안전 guard를 보존한다.
