# 스캘핑 익절 장후튜닝의 실체결·완료 포지션 모집단 구현계획

작성: 2026-09-24 KST. 상태: **구현 전 계획**. 적용 범위는 깨끗한 기준일 `2026-06-05T00:00:00+09:00` 이후 메인 실거래 `SCALPING/SCALP` 포지션의 장후 관측·튜닝 입력이다. [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8의 경제성·소유권·안전 기준과 [기존 익절 원천 연결 계획](./scalp-trailing-postclose-threshold-lineage-and-pruning-plan-2026-09-24.md)을 따른다. 다음 자연 표본의 실행 수용 owner는 [9/28 체크리스트 `HoldingExitPositionOutcomeLineageClosure`](../checklists/2026-09-28-stage2-todo-checklist.md)이다. 이 문서는 코드·런타임·임계치·주문 변경이나 장후 작업 실행을 승인하지 않는다.

## 1. 확인된 결손과 결정

- `sniper_trade_review_report.py`의 `completed_trade_projection`은 DB `COMPLETED`를 출발점으로 삼고 매도 terminal 수량·정확 비용을 별도 필드로 남긴다. 그러나 매수 브로커 체결 수량 전체와의 대사를 공통 적격 조건으로 만들지 않는다. DB `buy_qty`와 `buy_time`만으로 실매수 체결을 증명할 수 없다.
- `holding_exit_observation_report.py`의 `_is_valid_completed_trade`는 `COMPLETED`·메인 전략·유효 `profit_rate`만 확인한다. 그 결과 `completed_valid_ids`, `position_outcomes`, 일부 임계치 입력 ID에는 양측 체결·잔량 0·정확 비용이 증명되지 않은 건이 들어갈 수 있다. `economic_input_complete=false`가 후속 권한은 차단하지만 위 ID의 의미를 수정하지는 않는다.
- 현재 네 직접 익절축은 먼저 `exit_rule=scalp_trailing_take_profit`만 선택한다. 후보 정책을 전체 실거래 완료 포지션에 비교하려면 기초 분모는 **청산 규칙과 무관한 동일 완료 포지션 집합**이어야 한다. 다른 청산은 익절 실적이 아니라 경쟁 청산 또는 관측 중단으로 분류한다.
- 열린 포지션은 이미 별도 `open_position_censoring`으로 분리된다. 이 경계를 유지한다. 장후 보고서의 `candidate_value=None`, `paired_replay_eligible_ids=[]`와 실거래 적용 차단도 유지한다.

## 2. 봉인할 공통 기초 모집단

한 행의 단위는 **position/recommendation ID에 결합된 단일 실거래 position cycle**이다. 같은 종목·시각만으로 서로 다른 포지션을 합치지 않는다. 진입 attempt/cycle, account/custody, position tag, venue/session, BUY·SELL order/execution 번호, 원천일·영수증 hash를 연결한다. AVG_DOWN/PYRAMID 등 실제 추가매수가 있으면 동일 cycle의 BUY leg로 보존하고 별도 owner의 효과와 섞지 않는다.

`strict_completed_position_ids`에 들어가려면 아래 조건을 **모두** 충족해야 한다.

1. `main-only`, `normal_only`, `post_fallback_deprecation`의 메인 실거래 owner에 속한 cycle이고 clean-baseline 이후 진입·완료 귀속이 확인된다. sim/probe/CF, widget/episode/manual·별도 machine custody, legacy 표시행은 제외 사유와 함께 별도 둔다. 기간 경계는 진입일과 최종 매도일을 모두 기록해 검증하며, 과거 원천을 현재 상태로 역투영하지 않는다.
2. 브로커 BUY 체결 영수증의 유효 execution identity와 양수 **실제 체결 수량**을 확인한다. `position_rebased_after_fill`/`holding_started`의 중복·누적 갱신을 한 체결로 합치지 않고, 각 order의 누적 수량 증가분만 합산한다. DB `buy_qty`·매수가·매수시각과 대사하되 DB 필드만으로 통과시키지 않는다. 추가매수와 부분 매수는 실제 체결 leg로 합산하고, 미체결 잔여 BUY 주문은 취소·종결 여부를 별도 확인한다.
3. 직접 브로커 SELL 체결·최종 `sell_completed` 영수증을 동일 cycle에 묶고 각 SELL 증가분을 한 번만 센다. 전 과정에서 `누적 BUY 체결 - 누적 SELL 체결 >= 0`, 최종값 `0`, 미해결 SELL 잔량·대기 주문 `0`을 확인한다. 기존 `cumulative_sell_qty == DB buy_qty`는 이전 부분매도나 추가매수가 없는 단순 cycle에서만 충분하다. 중복/역행 누적 영수증과 DB terminal·broker balance 충돌은 적격 제외·원천 결손으로 남긴다.
4. DB 상태가 `COMPLETED`, canonical `profit_rate`가 유한하며, 같은 최종 SELL의 profit rate·수량과 허용 오차 내 대사된다. 화면 표시용 0 대체·추정 청산 규칙은 이 검증을 대신하지 않는다.
5. 매수 원가와 모든 매도 체결가·수량·세금/수수료를 포함한 **체결 기반 비용 후 순손익 증거**가 같은 cycle에 결합된다. 현재의 `broker_fill_prices_fee_aware` 직접 영수증과 수량·profit 대사를 시작점으로 하되 매수 체결 원가, 모든 leg 및 비용 계산의 실제 영수증/수수료율 출처를 검증한다. 브로커가 직접 부과한 비용과 수수료율로 계산한 비용은 출처를 구분한다. 가격만 이용한 모델 손익, 잔고대사 단독, 비용 null, gross 대체는 불합격이다. 슬리피지 기준값이 없으면 해당 비교값만 null로 남기고 체결 비용 자체와 혼동하지 않는다.

정확한 최종 SELL **체결시각**은 기초 모집단 필수 조건이 아니다. 실제 최종 체결과 비용이 증명되지만 `official_fid_908` 시각이 없는 건은 기초 모집단에 남고, 아래 후행 관측 층에서 `not_observable_no_exact_fill_time`으로 분리한다. 반대로 broker balance만으로 종료를 추정한 건은 직접 최종 SELL 체결이 확인될 때까지 기초 모집단에 넣지 않는다. 부분 진입 체결도 실제 보유한 수량이 최종 전량 청산되고 미해결 주문이 없어야 적격이다. `full/partial entry fill` 표시는 별도로 보존한다.

## 3. 독립적인 분류 층과 집계 규칙

| 층 | 동일 기초 ID에 붙일 상태 | 사용 경계 |
| --- | --- | --- |
| 전체 완료 census | `db_completed_main_ids`, `db_completed_valid_profit_ids`, `strict_completed_position_ids`, `excluded_ids_by_reason`, `source_gap_ids` | `DB 완료 ID = 유효 수익률 ID + 무효 수익률 ID`, `유효 수익률 ID = 엄격 적격 + 사유별 제외`를 ID로 대사한다. 한 ID에 여러 결손이 있으면 대표 제외 사유 하나와 모든 결손 목록을 함께 보존한다. 식별 가능한 결손 ID는 격리하고, census/identity/hash가 봉인되지 않으면 전체 입력 차단. |
| 실제 청산 귀속 | `trailing_observed`, `other_exit_observed`, `exit_rule_inferred`, `exit_rule_missing` | 직접 `exit_signal`과 terminal을 연결한다. 추정 규칙은 전체 완료 경제성에는 남을 수 있지만 규칙별 인과·임계치 후보에는 넣지 않는다. 다른 청산은 익절 수익 분자가 아니라 경쟁 청산/검열 사유다. |
| 트레일링 입력 | arm·강약·유효 호가/점수·선택 임계치·policy hash·첫 crossing의 원천 및 `source_gap` | 네 직접 축의 연구 적격은 기초 모집단의 부분집합이다. 실제 trailing으로 종료된 건만으로 전체 후보 비교 분모를 만들지 않는다. 다른 청산 전 관측 경로가 없는 건은 `replay_unavailable`로 분리한다. |
| 청산 후 가격 | `pass`, `partial_window`, `unmatured`, `not_observable_no_exact_fill_time`, `source_gap_*` | 동일 position/fill과 `post_sell_id`를 묶고 정확한 최종 fill time·동일 venue/route·1/3/5/10분 성숙과 품질을 확인한다. 후행 상승은 진단값이며 실현손익이나 반사실 순익으로 합산하지 않는다. |

층별 결손은 `0`, 무발동, 무수익으로 보간하지 않는다. `source_gap_ids`는 `excluded_ids_by_reason`의 부분집합이며 이중 계상하지 않는다. 적격 기본 경제성은 엄격 기초 ID에서만 계산하며, 규칙별·후행 관측별 분모는 각 층의 적격 ID와 제외 ID를 별도로 공개한다. `whole_cohort_pnl_krw`는 요구 비용 증거가 없는 완료 ID가 같은 목표 모집단에 존재하면 null과 사유를 유지하고, 엄격 부분집합 합계는 `exact_cost_subset_pnl_krw`처럼 명시한다. `census_complete`, `whole_census_economics_complete`, `strict_cohort_research_ready`는 각각 판정한다. 결손 ID를 식별해 격리할 수 있으면 적격 부분집합 연구 자체를 일괄 차단하지 않되 제외율·선택 편향을 보고한다. 전체 census/identity/hash가 결손이거나 격리할 수 없는 경우에는 입력 전체를 차단한다. 후보 replay의 paired/holdout 적격은 추가 원천 조건을 모두 만족할 때만 열며 이 계획만으로 후보를 생산하지 않는다.

## 4. 구현 순서와 파일 소유권

| 단계 | 수정 위치와 작업 | 완료 판정 |
| --- | --- | --- |
| C0. 원천·키 검증 | 기존 `sniper_execution_receipts.py`의 BUY `position_rebased_after_fill`·`holding_started`와 SELL partial/final outbox, `sniper_trade_review_report.py`의 event matcher·DB PK를 실표본/fixture로 대사한다. 체결 ID·수량·position cycle을 이미 기록하는지 먼저 확인하고 누락된 최소 필드만 기존 producer에 추가한다. | BUY/SELL 각 leg의 원천·ID·증분/누적 수량을 재구성할 수 있다. 누락은 `source_gap_buy_fill_*`/`source_gap_sell_fill_*`이고 DB 또는 종목/시각으로 추정 통과시키지 않는다. Kiwoom 요청·응답 파서에 손댈 필요가 생기면 공식 API reference gate를 먼저 수행한다. |
| C1. 전체 projection | `sniper_trade_review_report.py`의 화면 `top_n`과 분리된 `completed_trade_projection`에 매수·매도 수량 ledger, 잔량, 주문 종결, 실비용 출처, 정확 시각 출처와 `strict_completion_status/reasons`를 붙인다. 직접 final·sync-only를 구분한다. | 날짜별 DB 완료 ID = projection ID; `sell_completed` terminal ID와 차이는 명시적 gap. late/carry 완료·중복/역행 receipt·partial entry/exit·scale-in을 처리하고 동일 ID 중복 집계가 없다. |
| C2. 공통 모집단 소비 | `holding_exit_observation_report.py`에 한 번만 쓰는 엄격 적격 판정을 두고 `position_outcomes`, 경제성, `trailing_threshold_readiness`가 같은 ID 집합을 공유하게 한다. 기존 느슨한 `completed_valid_ids`는 의미를 분명히 한 census 필드로 유지하거나 schema version을 올려 이름을 바꾸고, 적격 ID와 혼용하지 않는다. | 전체 = strict + 제외의 상호 배타·합집합을 대사하고 원천결손 ID가 제외 ID의 부분집합인지 확인한다. 결손이 있는 ID의 원 단위 경제성·후보 적격은 null/false. 열린 포지션은 별도 censoring. |
| C3. 청산·후행 층 | 같은 보고서의 `exit_rule` 분류와 `sniper_post_sell_feedback.py`의 `post_sell_id`·정확 fill anchor를 strict ID에 결합한다. `holding_exit_sentinel.py`와 장후 summary가 새 ID 집합/상태를 원본 hash로 소비하도록 갱신한다. | trailing/other/inferred/missing의 합계 = strict ID. 후행 pass/partial/unmatured/unobservable/gap의 합계 = strict ID; 원천 없는 값을 후보값으로 승격하지 않는다. |
| C4. 권한·회귀 | 기존 `test_trade_review_report.py`, `test_holding_exit_observation_report.py`, `test_post_sell_feedback.py`와 SELL/BUY receipt 관련 테스트에 실패 사례를 먼저 고정하고 수리·재리뷰한다. | 아래 §5를 통과하고 기존 장후 source/hash → 마지막 consumer 계약이 일치한다. report-only 상태·incumbent 임계치·주문/안전/다른 owner는 그대로다. |

새 Python 모듈·독립 cron·장후 stage는 만들지 않는다. 기존 producer/consumer에 추가할 필드와 schema 전환을 함께 설계한다. 실제 구현에서 자동화 wrapper를 변경해야 하면 그때 운영 문서와 체크리스트를 동일 변경집합에 갱신한다. 선택된 immutable release는 제자리 수정하지 않는다.

## 5. 검증·수용 시나리오

1. 정상 1회 BUY·1회 SELL, 부분 BUY 후 남은 주문 취소·전량 SELL, 여러 BUY leg/scale-in·여러 SELL leg의 최종 잔량 0이 각각 정확히 한 position ID로 계산된다. 부분체결 자체를 무조건 제외하지 않고, 미해결 BUY/SELL 주문·포지션 잔량이 있으면 엄격 완료에서 제외한다.
2. DB `COMPLETED`이나 BUY receipt 없음, BUY 수량 불일치, 중복 execution, SELL terminal 없음, 누적 수량 역행, balance sync만 있음, 수수료/원가 결손, 수익률 불일치, 잘못된 custody/route는 **사유별 제외 ID**로 남고 후보·비용 후 합계에 조용히 들어가지 않는다.
3. strict 완료라도 `exit_signal` 없는 추정 trailing, 실제 다른 규칙 청산, 정확 fill 시각 없는 건, 사후창 `partial_window` 건을 각 층에서 분리한다. 다른 청산의 실제 손익은 전체 완료 경제성에 한 번만 들어가고 trailing 성과에 중복 계상되지 않는다.
4. `>top_n`, 전일 진입·당일 매도, 같은 종목의 두 포지션, 날짜 경계, source hash 변경, 누락/중복 snapshot에서 전체 ID 대사와 stale 차단을 확인한다. clean-baseline 이전·sim/probe/CF·다른 custody는 현재 튜닝 분모에서 제외된다.
5. 최초 회귀를 보존한 뒤 구현→자체 리뷰→보완→재리뷰→관련 pytest/compile→`git diff --check`를 수행한다. 코드 검증, 새 장후 산출·strict terminal, 선택 release, 실제 PID 소비, 자연 체결, 비용 후 paired/holdout 성과는 각각 따로 보고한다. 현재 `candidate_value=None`과 live 적용 차단은 별도 후보 생산·선택 계약이 닫히기 전까지 유지한다.
