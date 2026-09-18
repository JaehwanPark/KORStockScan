# 다음 장후 단위: microstructure_reaction_context — 2026-09-18

`entry_recheck_drought_controller` 다음 실행 단위는 `src.engine.scalping.microstructure_reaction_context`다. 현재 wrapper는 전용 controller를 폐기했으므로 저가주 확장 후보/auto-expansion 이후 이 작업으로 넘어간다. 중간 AI gate backtest는 기존 on-demand 진단으로 자동 실행하지 않는다. `RUN_MICROSTRUCTURE_REACTION_CONTEXT` 기본 true, resource guard 후 실행, 실패는 optional WARN, CLI는 경고가 있어도 0을 반환한다. 산출물 존재/exit 0은 분석 완전성·경제성·전체 chain DONE을 의미하지 않는다.

이 문서는 9/17 기존 산출물·현재 producer/consumer source·기존 PERF receipt의 읽기 전용 분석이다. 전체 장후 재실행, 원 pipeline 5.71GB 재스캔, 정책/env 발행, provider/주문 호출을 하지 않았다. 원천 signature와 JSON SHA를 `tmp/entry-recheck-retirement-20260918/next-unit-analysis.json`에 남겼다. workspace의 다른 세션 microstructure/feature-packet health 수정은 이번 폐기 release에 포함하지 않았다.

## 소비 데이터와 계산

실시간 특징 producer는 `scalping_feature_packet.extract_scalping_feature_packet` → `build_microstructure_reaction_context`다. 기존 WS orderbook 상위 3호가의 가격/잔량, 최근 10틱의 가격·거래량·공격 방향·수신/호가 freshness, 최근 봉의 고저/범위 등을 사용한다. 신규 Kiwoom 호출을 만드는 작업이 아니다. 호가가 없거나 틱 5개 미만, timestamp 누락/미래·invalid, tick age >5초, quote age >설정 기본3초, 신뢰 가능한 aggressor/volume 원천 부재이면 neutral/missing/stale로 처리한다.

유효 입력에서 고정 산식으로 ask sweep, post-sweep hold, bid replenishment, wall replenishment risk, VI proximity risk를 0–100으로 계산한다. favorable은 ask>=65, hold>=60, bid>=55이며 위험 점수>=70은 risk-context, ask/hold<=40은 weak로 분류한다. **장후에 이 가중치·기준을 탐색/최적화하는 튜너는 아니다.** 호가 replenishment는 단일 깊이 비율과 단기 가격 반응의 대리 특징이고 VI proximity는 등락/고저 범위 대리 지표다. 실제 호가 취소·재충전 시계열이나 거래소 VI event를 검증한 직접 계측으로 해석하면 안 된다.

장후 producer는 당일 pipeline JSONL을 streaming으로 읽고 context/provenance 필드가 있는 행을 투영한다. delivery v3는 evaluation ID별 중복 로그를 합쳐 compute/payload inclusion/provider response/internal consumption을 구분한다. favorable 진입 관측은 stock/record/venue/context ID로 묶고 같은 ID 내 120초 cluster, 첫 blocker는 cluster 주변15초, outcome은 기준시각 오차5초 이하로 연결한다. v2 context ID를 가진 outcome은 ID/feature version/venue가 같고 시각 오차0이어야 한다. actual 제출과 미제출 진단을 분리한다. 이는 **feature 평가 기회 중복 제거**이며 정책 버전별 실제 completed episode 손익 원장은 아니다.

outcome 원천은 `missed_entry_counterfactual`의 microstructure attempt outcome + watch-cycle ledger다. micro attempt는 원 평가 시점부터 같은 venue의 이후20분 관측 가격으로 close/MFE/MAE를 계산하고 고정 추정 왕복비용0.23%를 차감한다. 현재20분 quality pass는 관측>=3개 및 마지막 offset>=16분이므로 정확한20분 종가나 실제 체결가/손절·익절 전략의 성과와 동일하지 않다. 결손/불완전 outcome의 수익은 null로 제외한다. 비용은 실제 주문별 수수료·세금·slippage 정산이 아니다.

누적 계산은 clean baseline 6/5부터 유효한 작은 일별 rollup만 소비한다. rollup feature/quality/metric/schema 계약과 pipeline/outcome/source-quality-audit의 path/size/mtime signature를 검사한다. 자동 wrapper에는 `--backfill-clean-baseline-rollups`가 없다. 기존 누락·stale 과거 rollup은 자연스럽게 재구축되지 않는다.

## 만들어지는 산출물과 사용처

정책 후보·PREOPEN env·BUY 권한은 생성하지 않는다. JSON/MD, 일별 opportunity rollup, clean-baseline 누적 JSON/MD와 source-quality code-improvement order를 만든다. `runtime_effect=false`, `allowed_runtime_apply=false`, `candidate_review_required=false`, `runtime_application=not_applicable_diagnostic`가 계약이다. 표본20은 진단 해석을 위한 floor이며 runtime 승격 허들이 아니다. 후보0을 유효 no-edge로 판정할 수 없다.

보고서는 `threshold_cycle_ev_report` → `runtime_approval_summary`의 진단 요약과 `build_code_improvement_workorder`의 source-only 수리 업무로 소비된다. 런타임은 이 보고서를 로드하지 않고 매 평가에서 직접 생성한 feature packet을 사용한다. `ai_engine_openai`의 holding score와 upstream holding preflight는 source quality를 소비/제약하며 일반 provider payload에는 전달된 특징이 있을 수 있다. provider response는 전달 증거이고 모델이 실제로 그 특징을 사용했다는 증거가 아니다.

현행 machine-first/compact 보조 AI는 `entry_setup_evidence_v1`·mechanistic assessment/bundle을 주 입력으로 받는다. 기존 raw microstructure packet을 모든 compact 요청에 보내야 하는 계약은 아니다. raw payload 부재를 무조건 source gap이나 feature 복원 의무로 바꾸지 않는다. 필요한 것은 **현행 machine이 쓰는 feature/같은 cutoff/venue/AI 역할의 실제 소비 결속**이다. holding 안전 특징 제거 여부는 장후 진단 폐기와 별도 판단해야 한다.

## 9/17 실행 결과

원 JSON: `data/report/microstructure_reaction_context/microstructure_reaction_context_2026-09-17.json`, generated `2026-09-17T23:44:06+09:00`, SHA256 `44400c719aa1596615789b0a46592960ffb2633a98c1984926bf9d6a6b284eb3`.

| 항목 | 확인 결과 | 해석 |
|---|---:|---|
| command wall / peak waited child RSS | 68.84초 / 약215.7MiB | 기존 PERF, supervisor/group 합계 아님 |
| 투영된 raw 행 / status ok | 20,911 / 208 | 전체 거래 기회나 required 평가 분모가 아님 |
| v3 독립 평가 computed / usable | 63 / 56 | 100% compute, 88.889% usable은 이 분모 |
| provider required / response 확인 | 42 / 32 | 76.19%, unconfirmed10; 재전송/구 소비 강제 근거 아님 |
| internal consumption required / consumed | 0 / 0 | coverage=null; 필수 holding 소비 실패0건을 0% 소비 결함으로 오판하지 않음 |
| applicability unknown legacy 행 | 20,669 | 결손·미평가·scanner traffic·과거 계약을 섞은 raw 합계 |
| favorable 관측 / 독립 미제출 기회 | 43 / 19 | 11종목, 실제 제출 선언0은 이 투영 범위 |
| 당일 exact 결과 / 역사적 gap | 3 / 16 | 현재 로직이 historical gap으로 표기; 기다린다고 이미 지나간 tape가 생기지 않음 |
| 누적 가용 원천 날짜 / 포함 날짜 | 76 / 3 | 포함9/8·9/9·9/17; 전체 누적 population 대표 아님 |
| 누적 독립 기회 / quality-pass 결과 | 38 / 13 | outcome coverage34.211%; diagnostic floor20 미달 |
| 누적 비용 추정 차감 CF EV | -0.803769% | 13건 부분 표본의20분 가격 반사실 평균, 실현 순익 아님 |
| 누적 평균 MFE / MAE | +1.943% / -2.368462% | 도중 최고수익·최대불리 가격; 포착가능성·실제 tail 손실 증명 아님 |

source contract 수리 order는 두 개다: `order_microstructure_v3_evaluation_venue_missing_or_conflicting` 36평가, `order_microstructure_v3_evaluation_anchor_contract_missing` 1평가. 원 receipt에는 상위 effective venue가 있어도 microstructure venue가 null인 경우가 있으며 생산자가 명시 venue들을 단일값으로 해소하지 못한 것이다. 기준점 누락 예는 retired ADM snapshot의 record 없음이다. 현재 retired owner에 과거 문제를 복원 업무로 다시 할당하지 않는다.

9/17 원천 attempt outcome 전체20건은 complete9/gap10/conflict1이다. 이 중 favorable subset의 exact3을 소비한다. 전체 complete9와 favorable exact3의 분모를 혼합하지 않는다. 같은 날짜 현재 `code_improvement_workorder`, `threshold_cycle_ev`, `runtime_approval_summary` 산출물은 workspace와 해당 frozen stepwise worktree에서 확인되지 않는다. 기존 wrapper는 이후 `pipeline_event_verbosity` resource guard에서 `3923.6<4096.0`, 9/18 00:44:49 FAIL로 끝났다. 따라서 두 수리 order가 최종 workorder/summary에 인계됐다고 주장할 수 없다. 그전 날짜 summary나 PERFDONE으로 대체하지 않는다.

## 시간으로 해결되는 것과 구조 결함

| 구분 | 원인·현재 판단 | 다음 행동과 closure test |
|---|---|---|
| 미래 표본 축적 | pass13/floor20, 새 source-valid 평가·가격이 발생하면 수가 늘어남 | 기존 진단 유지. 모델 ETA 추가2 observed dates는 과거3일 rate4.333에 의존한 참고치이며 기동/새 수집/역할 변경에 보장 없음 |
| 실제 pending horizon | 평가 이후20분이 아직 지나지 않은 당일 기회 | 해당 기회만 성숙 후 다시 연결; 9/17 현재 gap을 pending으로 바꾸지 않음 |
| 과거 rollup 누락/stale | 73일 배제; metadata 검사상73개 모두 기존 rollup이 있으나 schema/signature 계약이 맞지 않음(`rollup-metadata-check.json`). 자동 backfill 없음 | metadata manifest에서 원인을 확인 후 기존 compact rollup의 필요한 날짜만 bounded 재구축. quality/identity가 없는 tape는 회복 불가로 보존하고 무한 replay 금지 |
| venue/anchor producer 결속 | status ok인데 venue 없음36, record anchor 없음1 | 현행 Main producer가 canonical same-cutoff venue/record/time/price/context hash를 전달하는지 정상 소비 경로의 회귀+다음 자연 receipt로 검증. conflicting source는 fail closed, 이름만 채우거나 상위 venue를 추측해 historical PASS 금지 |
| historical outcome coverage | 누적25/38 historical gap, 당일16/19 | original identity+time+venue 및 retained forward tape가 있으면 bounded 복원, 없으면 irrecoverable로 별도 제외. 비용 차감 missing을0/no-edge로 대체 금지 |
| 구 entry stage 중심 | stage set에 retired ADM와 legacy AI/drop/score가 남고 machine ENTER/RECHECK, auxiliary PASS/VETO/CAUTION을 전용 분모로 평가하지 않음 | 현행 machine/보조 AI 기존 평가 owner로 mapping을 정리; repeated evaluation과 checkpoint/episode를 구분하고 구 경로를 되살리지 않는 회귀·자연 join 검증 |
| blocker 해석 | blocker ai_confirmed/old ADM snapshot이 있으나 현행 machine의 causal 차단 근거와 다름 | 첫 실제 normal-submit 차단을 machine/보조 AI·기존 safety receipt에 결속. token을 늘리는 분해보다 정상 제출 가설 하나를 검증 |
| 보고 의미 혼선 | Markdown은 `v2 only` 표기인데 summary는 v3, raw missing 합계와 v3 usability 분모가 다름 | render에 각 분모·버전·N/A를 명시하는 작은 수리. 숫자만으로 모든 pipeline 행이 feature 필수라고 추론하지 않음 |
| 거래량/강도 provenance | 729/729 raw mismatch는 comparison scope unknown729, comparable contract violation0. v_pw unusable20911에는 row projection의 null도 false로 세는 코드가 있음 | 원 계약을 확인한 comparable subset만 위반 판정. nullable unknown/N/A와 명시 false를 분리; 전체원천불량/새 REST support 권한으로 확대하지 않음 |
| economics 적합성 | fixed0.23% 비용·20분 close, 16분 이상3관측에도 pass; session/적용 policy version/actual completed outcome 결속 부족 | 기존 machine/AI 경제성 owner의 실행 가능한 비용/노출/tail/holdout 및 버전별 actual ledger를 사용. 이 CF 평균을 실제 PnL이나 threshold 후보로 직접 승격하지 않음 |
| final handoff 없음 | 개별 producer 완료 이후 전체 chain FAIL로9/17 소비 산출물 없음 | 현행 자동 chain/기존 복구 owner에서 dated workorder/EV/summary가 동일 generation을 소비하거나 retired-source 명시 종료하는지 확인. 보고서 생성만 closure 아님 |

## 기능 역할 판단

이 작업을 계속 기다리면 독립 정책이 나오는 구조가 아니다. **현재 기계판정기·보조 AI 튜닝의 feature/품질/기회 attribution 진단으로 연결해 사용해야 한다.** 새 별도 tuner·policy grid·canary/budget을 추가할 이유는 확인되지 않았다. 필요한 보완은 현행 producer/consumer identity 계약, 평가 분모, 누적 rollup coverage와 기존 정상-submit/경제성 owner 연결의 작은 수리다. 현행 machine/AI 보고서가 이를 이미 완전히 맡는지 확인한 다음 중복 장후 집계를 축소/통합할 수 있다. holding의 실제 fail-closed 안전 소비는 그 판단에 포함해 보존해야 한다.

이번 요청에서는 다음 단위를 분석했으며 이 단위의 소스 수리·재실행·폐기를 수행하지 않았다. 장후 진단의 후보0, 13건 음수 CF EV, 부분 coverage로 현재 전체 전략의 실제 순익이나 최종 no-edge를 선언하지 않는다.
