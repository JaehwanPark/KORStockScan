# 2026-09-18 scale_in_split_order_plan 개별 실행·EV 분석

사용자 지시에 따른 **코드 변경 없는 분석**이다. Source date9/17, 확인일9/18 KST. 실행·source/경제성·시간 성숙·구조 결손을 분리한다. 기존 실행·보고서·policy는 보존하며 raw replay/보고서 재생성·신규 주문·threshold/quantity/env 변경은 없다. 현재 owner는 [당일 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)의 `KiwoomCommonHealthOpportunityCostAcceptance0917`다. PYRAMID 폐기와 AVG_DOWN 공통 Main 반등 소비를 우선하는 현행 지시를 과거 독립 AVG_DOWN 튜닝 계획으로 덮어쓰지 않는다.

## 실행 결과

현행 장후 순서는 독립 market_panic_breadth_collector 다음 조건부 scale_in_split_order_plan이다. 장후 panic 재집계는 제거됐다. wrapper의 scale-in 호출과 JSON/MD 대기는 유지한다.

9/17 원 실행은 `postclose-stepwise-20260917` source로 exit0, wall22.392004초, peak child RSS37,192KiB였다. JSON/MD ready이며 generated_at23:54:54.900144+09:00이다. 후행 원 chain은 resource guard 중단이므로 개별 성공이 전체DONE은 아니다. PERF block operation 수를 읽은 bytes나 실제 경제성 표본으로 해석하지 않는다.

| 지표 | 결과 | 의미 |
| --- | ---: | --- |
| 당일 AVG_DOWN 관측 / unique attempt | 0 / 0 | presence precheck가 유효 제출 anchor를 찾지 못해 JSON 전체 decoding을 생략 |
| 최근20 report date 범위 accepted historical dates | 8 | 구 schema/date mismatch11개 제외;20거래일 보장 아님 |
| historical unique attempt | 4 | 9/7·9/11·9/14·9/15, 다른 report 복사행 재집계 제외 |
| market-like / 요청수량1 | 4 / 3 | 가격 분할 적용 불가; 나머지 수량4도market-like |
| 기준가격 재구성 결손 | 2 | 9/14·9/15; 후행 시간만으로 복구되지 않음 |
| eligible runtime / 완료손익 / 추가 MFE·MAE / paired 경제성 | 0 / 0 / 0 / 0 | real_sample_count4를 경제성4건으로 사용할 수 없음 |
| 경제성 source dates / 가격 join coverage | 0 / 0% | join gap count0은 eligible 분모0의 결과이며 연결 성공 아님 |
| runtime candidate / apply 허용 | 0 / false | market_qty_split_only 후보1은 진단상 잔존이며 활성 successor가 아님 |
| 비용 차감 modeled incremental EV / 실제EV / 일별순익 | null / null / null | 비교 불능; 개선0 또는 무거래 순익0으로 대체 금지 |
| atomic sizing / 실제 post-apply attribution | natural_first_use_pending / not_observed | native 사용과 손익 연결이 입증되지 않음 |

원 source-quality는warning/tuning_input_allowed=true/hard gap0이다. 이는 경제성 source/표본 결손을 해소한 PASS가 아니다. 추천과9/17 `scale_in_split_order_policy_v3` 모두runtime_apply_allowed=false, buckets={}이며 policy version은 `scale_in_split_order_plan:2026-09-17:b84cc1c7e534`다. 기본50:50·0/−0.3% 표기는 선택 성공이 아니며 unseen bucket은 unsplit base order로 fail closed한다.

## 무엇을 튜닝하는가

생산자는 **기존 Main 보유의 AVG_DOWN 추가 매수 주문을 어떻게 나눌지** 평가한다. 반등/진입 여부 자체를 학습하지 않는다. 초기 진입·widget/episode 저가주2차 진입·PYRAMID는 이 표본/정책 owner에 포함되지 않는다. 공통 Main 반등 판정과 기존 AI/손절/주문 guard가 상위 의사결정을 담당한다.

같은 submitted attempt ID의 실제/sim/probe·수량·price/terminal을 분리한다. 당일 normalized anchor와 과거 v3 `daily_attempt_outcomes`를 attempt별 합친다. 제출 후 최대180초의 가격 관측과 기존 leg TTL을 사용한다. 기준 control은 같은 anchor·총수량·TTL·terminal의 비분할 주문이다. 기존70:30/50:50의0/−0.3%,60:40의0/−0.8% 및 heuristic variant를 비교하며3leg는진단전용이다. tick/pct metadata가 함께 있어도 실제 계획은 pct offset이 있으면pct를 우선한다.

후보/control 각각 `calculate_net_realized_pnl`로 왕복 비용을 반영하고 ΔPnL 합계를 control 기준총notional 합계로 나눈 incremental EV를 사용한다. 이 수치는 절대 실현EV가 아니다. 충분히 관측된 TTL 내 가격 touch를 modeled fill로 계산하며 짧은 경로는 censor/null로 제외한다. 같은 종목·유사시각만으로 attempt/receipt를 결합하거나 missing cost/terminal을0으로 만들지 않는다.

현재 gate는 exact real outcome≥3, 추가MFE/MAE≥3, paired≥3, 경제성날짜≥2, 가격coverage≥80%, 비용차감incrementalEV≥+0.10%, modeled fill참여≥70%, Δ분포p10≥−0.30%p다. 통과후보 중 EV→fill참여→p10 순으로 선택하고 실제적용버전의 negative 경제성 근거도 확인한다. 이번4건은 모두market_like여서 이 비교 grid 자체가 실행 가능한 경제성 대조군을 갖지 못한다.

Live 연결은 `sniper_state_handlers`의 AVG_DOWN 주문 구성→`apply_scale_in_split_order_policy`다. 유효policy·날짜/최대3KRX거래일 age·bucket·quantity 보존·price/TTL guard를 확인하고, market order는 분할하지 않는다. 이후 cap 재검증과 주문 안전이 남는다. PREOPEN도hash/명시runtime_apply_allowed를 확인한다. 파일 생성·selected source·정책 적용·Main PID 소비·자연 추가매수·COMPLETED 비용손익은 별개다. 확인 시 Main PID 없음이며 실제분할/버전손익0건이라는보고서를 브로커전체거래0건으로 확장하지 않는다.

## 대기로 해소될 조건과 구조 결손

| 구분 | 근거 | Closure / 다음 조치 |
| --- | --- | --- |
| 조건부 horizon/terminal 성숙 | 새 eligible AVG_DOWN 제출·연속경로가 실제 존재할 때180초/TTL·정산 완료 대기 가능 | 같은attempt·route/session·수량·유효cost/terminal의 natural join |
| 조건부 표본 축적 | 유효limit수량≥2·완료/가격paired가 새로 들어와야3표본/2날짜 가능 | 상위Main 정상원천과 기존 owner의 자연 유입부터 확인; 날짜 수만 증가시켜 수락하지 않음 |
| 과거market/nonapplicable | 4/4 market-like,3건qty1 | 표본용 quantity 증대/시장주문변경 금지. 과거4건은 excluded 상태 유지 |
| 과거cached outcome 결손 | loader는 과거daily_attempt_outcomes를 그대로 읽고 current anchor만 새로 계산 | 나중 terminal이 생겨도 과거 report에 자동rejoin되는 구조가 아님. 원천 유무·재결합 계약의 별도검토 필요; 이번재생성 없음 |
| 독립 검증 결손 | 같은rolling 표본으로grid 선택·EV gate, 별도chronological holdout 코드/출력 없음 | 최소3표본/2날짜를 독립OOS 검증으로 설명하지 않음. 경제성promotion 검증 계약은별도검토 |
| 체결 모델 한계 | TTL 내관측가격touch→leg전체qty 체결가정, depth/queue 검증 없음 | sampled CF와 실제 fill/quantity/cost의 model error 대사 필요; touch를 real fill로 전환 금지 |
| atomic source 검사 사각 | post-contract submit census는 first observed atomic plan이 있을 때만 생성 | 계획 자체가 전무한실제제출에서 missing-plan 대신pending이될수있는 코드 경계. 당일submit0이므로 현재발생결함이라고 단정하지 않음. 별도기존owner검토; 코드변경금지준수 |
| 실제 성과·일별순익 부재 | post_apply policy/variant grouping은not_observed; 현재paired0 | exact applied version→native COMPLETED+수량/비용→rolling/cumulative net/EV/노출을 연결. modelΔPnL0 합계는 paired분모0이므로 경제성0아님 |

경제성 ETA는null이다. 20개 report가 쌓이거나 기다려 기존cached4건이 window 밖으로 빠지는 것은 EV 개선이 아니다. 이번 작업에서 source grid/floor/holdout/비용/주문·quantity/PREOPEN/bot 코드를 변경하거나 비싼 raw/producer를 재실행하지 않았다. 구조 결손을 기록하며 runtime safeguard와 검증 임계값을 완화하지 않는다.

근거: [원9/17 JSON](../../data/report/scale_in_split_order_plan/scale_in_split_order_plan_2026-09-17.json), [policy](../../data/threshold_cycle/scale_in_split_order_policy/scale_in_split_order_policy_2026-09-17.json), `logs/threshold_cycle_postclose_cron.log`의 target_date/PERF/ready, `src/engine/scalping/scale_in_split_order_plan.py`의 presence precheck/rolling loader/replay/경제성gate/runtime allocator, `tmp/panic-history-scale-analysis-20260918/scale-analysis.json` 및 before/closure source SHA. 과거 독립PYRAMID/AVG_DOWN튜닝폐기와 공유AVG_DOWN운영은 [현행 review](2026-09-18-pyramid-retirement-avg-down-shared-rebound-review.md)를 따른다.

분석 closure: 위commit의문서배포와별개로scale src/deploy/PREOPEN/live consumer코드및원9/17JSON/MD/policy SHA보존PASS. 구조결손은관측된경계로기록하고수정하지않았다. raw replay/producer/API/주문/봇실행/외부sync없음.
