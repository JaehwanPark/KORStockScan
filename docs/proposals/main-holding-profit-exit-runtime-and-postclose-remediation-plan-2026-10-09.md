# Main 보유청산·익절 런타임 및 장후작업 결함 보완계획

작성·원천 확인 및 보완 리뷰: 2026-10-09 KST. 상태: **계획 보완 및 읽기 전용 재현 완료, 구현 미실행**.

## 1. 목표·범위·권한

Main의 `scalp_trailing_take_profit`과 기존 보유청산 경로를 `런타임 판단 → 신호/주문/체결 → 실제 비용 → 장후 재생 → 정책/장전 → PID → 자연 결과`로 연결한다. 입력 결손을 정상 무신호·수익 0·경제성 실패로 바꾸지 않고, 기존 정상 청산을 장후가 재현하지 못하거나 감시기가 완료로 오인하는 계약 결함을 먼저 고친다. 새로운 익절 전략이나 더 느슨한 손절을 만드는 계획이 아니다.

이번 요청의 실행 범위는 이 계획 문서의 작성·리뷰·보완·문서 파서 검증이다. 코드 변경, 원천 재수집, 모델/브로커 호출, 정책 발행, 장후 재실행, release 선택, PREOPEN 재생성, 프로세스 재기동 및 주문은 실행하지 않는다. 이후 구현과 운영 단계의 권한은 해당 요청과 당시 checklist로 확인한다.

- 일반 익절의 기계식 강약 분류, 최초 crossing 고정, 실행 가능한 bid 사용과 기존 3시장 구분을 유지한다. 승인된 초기 `+0.4% / WEAK 0.4% / STRONG 0.8%` 및 별도 운영자 override를 기본값으로 덮지 않는다.
- 하드스탑·보호·비상·상한가·종료구간·계좌·브로커·주문·수량·cooldown·시세 freshness와 Main/manual custody·operator veto를 유지한다. preset 손절과 일반 SCALPING 손절을 하나의 임계값으로 합치지 않는다.
- 보유 AI의 EXIT PASS/VETO는 기존 청산 신호의 제한된 유예 권한만 갖는다. 추가매수 `ADD_REBOUND`의 PASS가 SELL 권한으로, EXIT PASS가 ADD 권한으로 넘어가지 않는다. soft-stop의 기존 holding-score 소비도 익절 분류기 변경에 포함하지 않는다.
- Episode/widget, NXT TP1 신규 부분 익절, 별도 MFE 익절, preset TP, 과거 AI-score 4축 익절 선택을 복구하지 않는다. 과거 체결·소유권 영수증은 보존한다.
- source-only 수리에 양의 EV·최소 실제 체결·새 holdout을 완료 조건으로 추가하지 않는다. 기존 **후속 정책 승격**의 경제성·독립 검증·단일 단계/시장·rollback 조건은 유지한다. 초기 승인 정책에 추가 경제성 허들을 만들지 않는다.

## 2. 기준 문서·실행 owner

원칙은 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 원천 경계는 [clean baseline/refresh owner](../../src/engine/automation/source_quality_clean_baseline.py), 프로토콜 변경 절차는 [Kiwoom Official Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 따른다. 앞선 [기계식 익절 폐루프 계획](scalp-trailing-mechanical-strength-closed-loop-tuning-plan-2026-09-25.md)과 [보유 투표·의미 감시 계획](holding-profit-exit-estimated-policy-and-semantic-closed-loop-plan-2026-09-26.md)은 설계 이력이다. 그 문서의 당시 미구현·PID·표본 숫자를 현재 상태로 사용하지 않는다. 이미 구현된 loader·publisher·비동기 투표 수집은 유지하고 아래 재현 결함만 후속 보완한다.

2026-10-09 일일 checklist는 없다. [2026-10-12 checklist](../checklists/2026-10-12-stage2-todo-checklist.md)의 목적·강제 규칙과 관련 owner를 확인했지만 미래 문서를 오늘의 실행 owner로 대신하지 않는다. 그 문서는 이미 postclose summary 세대에 결속되어 있으므로 이번 계획으로 수정하지 않는다.

현재 확인한 10/12 목록에는 보유청산 원천 수리의 독립 OPEN owner가 없다. 구현 착수 시 **당시 현재 checklist의 기존 보유청산 owner를 먼저 재검색**한다. 없을 때만 제안 stable ID `HoldingProfitExitSourceContractRepair` 하나를 등록한다. 아래 HP0–HP6는 해당 owner의 내부 단계이며 별도 OPEN 항목이 아니다. 등록 시 실제 Due/Slot/TimeWindow/Track와 본 계획의 수용 조건을 기재하고, generator가 다음 checklist로 같은 ID·원천·수용 이력을 이관하는지 확인한다. 장전 적용 확인은 기존 `DirectFamilyPreopenPolicyHandoff`를 재사용한다. 문서가 존재한다는 사실은 자동 구현·매매 권한이 아니다.

## 3. 확인 기준과 결함 목록

### 3.1 현재 코드·산출물

2026-10-09 00:43 KST 확인한 selector는 `main-integrated-bottlenecks-20261009-v1`, commit `f36b306cbd69ba8fbefdc7bc48f09b10144bdf44`다. [selector](../../data/runtime/runtime_release_selection.json)는 `actual_pid_consumed=false`, `awaiting_scheduled_main_start_20261012`를 기록한다. 이는 선택 영수증이며 현재 PID 소비 증거가 아니다. 앞선 대화에서 확인한 postclose 전용 v5 선택은 이 시점의 현재 selector가 아니다.

`sniper_state_handlers.py`, `sniper_execution_receipts.py`, `sniper_trade_review_report.py`, `holding_exit_observation_report.py`, `trailing_mechanical_replay.py`, `holding_profit_exit_semantics.py` 6개 파일은 위 선택 릴리스와 작업본 바이트가 같았다. 다른 dirty 변경은 이번 계획의 산출물이 아니며 보존한다. 구현 착수 시 selector·실제 PID·작업본을 다시 고정한다.

| 원천 | 직접 확인한 내용 | 확인 시 SHA256 |
|---|---|---|
| [10/8 holding exit observation](../../data/report/monitor_snapshots/holding_exit_observation_2026-10-08.json) | 완료/유효 수익률 333행, strict 0; 보고기간 6/5~10/8; mechanical cohort 시작 9/23, 12개 ID·strict 0; 새 후보 없음 | `cfd85d0173a966a9a49cc8095540d849f7646cb0b8dce841685f9f2b70787bee` |
| [10/12 holding vote policy](../../data/threshold_cycle/holding_path_vote_policy/holding_path_vote_policy_2026-10-12.json) | source 10/8, 15셀 초기값, `estimated_provisional`; 실현/추정 paired EV 모두 null. source report hash 일치 | 파일 `889c3a4ba0c9cbf5d42562b91f841a2326ffa34686460cda3d14281fc585c103`; bundle semantic hash `772c6a981c948cd0b97b876236611159b4b66e9ee292b6ebdc2ba5761b29b79f` |
| [10/8 기계식 선택 결과](../../data/report/scalp_trailing_mechanical_policy/scalp_trailing_mechanical_policy_2026-10-08.json) | source 10/7, `hold_source_gap/mechanical_population_incomplete`, apply false | 날짜가 다른 10/8 보고서와 한 세대로 섞지 않음 |
| [10/8 bootstrap](../../data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-08.json) | 3시장 트레일링 0.4/0.4/0.8; 일반 soft/hard -3/-5는 운영자 유지 lock | 기존 운영자 값의 증거이며 이번 계획의 변경값이 아님 |

### 3.2 확정 결함과 미완성 기능의 구분

| ID·우선순위 | 근거·판정 | owner와 필요한 종료 증거 |
|---|---|---|
| F1 / P0 | `holding_exit_observation_report._analysis_window_start`는 6/5 baseline을 쓰고 `_mechanical_completed_cohort`는 최초 v2 관측일을 시작으로 삼음. 기존 `policy_refresh_start_date()`의 9/29 후속 평가 경계를 소비하지 않음 | 보고서→replay→선택기. 9/28 이전 기록은 감사/보유 원가 lineage로 보존하되 후속 학습·순위·승격 분모에서 제외되는 경계 fixture |
| F2 / P0 | `sniper_execution_receipts._main_lifecycle_exit_economics_fields`는 configured cost를 기록하고 actual fee는 null. `sniper_trade_review_report._completed_trade_projection`도 actual fee·exact PnL을 null, `broker_actual_cost_observed=False`, actual-cost 결손을 무조건 기록함 | 체결 receipt→비용 대사→trade review→strict cohort. **현재 소비 경로에는 실제 비용을 인정하는 성공 분기가 없어 표본 축적만으로 strict 0이 해소되지 않음**. 공식 비용 원천 결속 또는 명시적 source unavailable 종료 |
| F3 / P0 | 런타임은 `_holding_path_exit_proceeds`의 VETO 유예 후 `exit_signal`을 냄. mechanical replay는 최초 기계 crossing과 `exit_signal`이 1초 이내여야 incumbent 재현으로 인정함 | 런타임 시간·유예 영수증→replay. 합성 crossing t0/exit t0+10초는 `source_gap_incumbent_trigger_not_reproduced`; 자연 발생 빈도는 미확인 |
| F4 / P1 | `holding_profit_exit_semantics.audit_profit_exit_flow`가 `trailing_start_pct == 0.4`를 고정 검사함. 적법한 후속 기계식 정책은 다른 시작률을 허용함 | 정책/PID receipt→의미 감시. 합성 0.5 입력은 `tp_crossing_arm_or_clock_invalid`; 향후 승인된 0.5와 무단 0.5를 정책 결속으로 구분해야 함 |
| F5 / P1 보고 계약 | 같은 감시기는 `tp_pending_submit`을 세지만 최종 상태 분기에 넣지 않음. pending 판단도 signal별이 아닌 record 전체의 `exits/sent/completed` 존재 여부에 의존 | 감시기→artifact freshness→보고 소비자. 합성 신호 1·submit 0에서 `status=pass, tp_pending_submit=1` 재현. **현재 pass는 의미 검사 결과이지 종단 완료 증거가 아님**. 실제 주문 장애로 단정하지 않고 진행 상태를 별도로 제공하며, 한 generation의 submit/terminal이 다른 신호의 미완료를 가리지 않는 fixture 필요 |
| F6 / P1 기능 경계 | `holding_path_vote_replay`는 판단 수 재생만 계산하고 EV는 null. `holding_path_vote_policy.validate_bundle`는 각 셀이 초기 기준값과 같은 경우만 허용 | 초기값 발행은 정상 승인 동작. **후속 최적화 구현 부재**를 source gap이나 새 정책 최적화 완료로 잘못 표시하지 않음. 자동 후속 선택은 HP6의 별도 설계/권한 범위 |
| F7 / P1 | `build_holding_exit_sentinel_report`의 일반 집계는 `as_of`로 자르지만 `audit_profit_exit_flow`에는 당일 전체 events를 전달함. 의미 감사는 별도 cutoff 인자를 받지 않음 | sentinel→semantics→freshness. 합성 `as_of=10:00`, 신호 `10:01`에서 session 신호 0·semantics 신호 1/`source_gap` 재현. 같은 cutoff·source generation에서 일반 집계와 의미 감사가 동일 사건 범위를 사용해야 함 |

F3–F5는 메모리상의 최소 합성 입력으로 기존 순수 함수를 호출한 결과다. 운영 파일·원장·정책을 쓰지 않았고 provider/broker를 호출하지 않았다. F4 재현은 감시기 인자에 기계식 선택 영수증 자체가 없어 적법한 변경을 판별할 수 없다는 소비자 계약 확인이며, 현재 0.5 정책이 발행·적용됐다는 주장이 아니다. F2의 strict 0은 실제 거래·손익 0 또는 전략 무효를 뜻하지 않는다.

추가 리뷰에서 F7은 모든 파일 loader를 메모리 입력으로 대체한 sentinel 호출로 재현했다. 자연 보고서 오판 빈도는 측정하지 않았다. 별도로 **실제 비용 수리의 누락된 저장 경로**를 확인했다. `log_archive_service`가 completed census와 projection sidecar를 만들고 holding report가 그 sidecar를 먼저 읽으며, postclose wrapper는 `verified_postclose_exit_snapshot_manifest`로 기존 산출물을 재사용한다. 현재 검증은 pipeline mtime·report hash·sidecar identity를 확인하므로 새 비용 원천을 연결할 때 비용 revision도 입력 fingerprint와 재사용 조건에 넣어야 한다. 이는 실제 비용이 이미 생산되는데 무시됐다는 주장이 아니라 HP2 구현 시 반드시 함께 보완할 의존 계약이다.

## 4. producer부터 마지막 consumer까지 수정 위치

| 연결 | 기존 owner | 보완 대상 |
|---|---|---|
| 판단·최초 crossing·유예·SELL | [sniper_state_handlers](../../src/engine/sniper_state_handlers.py), [holding_exit_vote](../../src/engine/ai/holding_exit_vote.py), [trailing_exit_decision](../../src/engine/scalping/trailing_exit_decision.py) | 시각·position/buy-fill generation·정책·유예 해제 사유의 한 경로 연결. 정상 결정값 보존 |
| 체결·잔량 복구·비용 | [sniper_execution_receipts](../../src/engine/sniper_execution_receipts.py), [sniper_sync](../../src/engine/sniper_sync.py), [trade review](../../src/engine/sniper_trade_review_report.py) | 가격/수량 원천과 실제 비용 원천을 분리해 대사. balance 복구·부분체결을 임의 완료로 바꾸지 않음 |
| 저장 projection·census·재사용 | [snapshot 저장/검증](../../src/engine/log_archive_service.py), trade review의 `completed_census_manifest`, holding report의 `_verified_trade_review_projection` | 실제 비용 revision→입력 hash→원본 report/census→sidecar→postclose manifest→재사용 판정까지 연결. 오래된 봉인 위에서 row만 수정하지 않음 |
| 장후 집계·재생 | [holding exit report](../../src/engine/holding_exit_observation_report.py), [mechanical replay](../../src/engine/scalping/trailing_mechanical_replay.py), [vote replay](../../src/engine/scalping/holding_path_vote_replay.py) | forward window, 알려진 결손 격리, 실제 유예 상태 재생, 후보별 검열·비용 비교 |
| 장후 세대·직접 인계 | [postclose wrapper](../../deploy/run_threshold_cycle_postclose.sh), [runtime summary](../../src/engine/runtime_approval_summary.py), [summary handoff](../../src/engine/automation/postclose_summary_handoff.py), [checklist generator](../../src/engine/build_next_stage2_checklist.py) | 같은 snapshot 세대·report/policy hash, bounded defect owner 이관, 초기값/후속 후보/적용/경제성 분리 |
| 정책 선택·준비·소비 | [mechanical publisher](../../src/engine/automation/scalp_trailing_mechanical_policy_apply.py), [bootstrap](../../src/engine/automation/runtime_policy_bootstrap.py), [next PREOPEN readiness](../../src/engine/automation/next_preopen_readiness.py), [vote policy loader](../../src/engine/scalping/holding_path_vote_policy.py) | 기존 부모 CAS·one-market/same-stage·lock·정확 날짜·선택/PID 경계 유지; 잘못된 원천 정책 거부 |
| 의미 감시·최종 상태 | [profit semantics](../../src/engine/scalping/holding_profit_exit_semantics.py), [holding sentinel](../../src/engine/holding_exit_sentinel.py), [artifact freshness](../../src/engine/error_detectors/artifact_freshness.py) | 정확한 정책 영수증 대조; 동일 as-of, signal별 pending submit/terminal와 경제 결손의 직접 전달 |

기존 모듈을 먼저 보완한다. 순수 청산 상태 재생을 분리해야 하면 역할은 `src/engine/scalping`, 공통 비용 원천 대사는 실제 기존 체결/거래 원천 패키지, handoff는 `src/engine/automation`, 테스트는 `src/tests`다. `src/engine` 루트에 새 파일이나 중복 구현 wrapper를 만들지 않는다. 실제 새 파일 필요 여부·주변 consumer·소유 경계는 구현 직전 location gate에서 확정한다.

## 5. 단계별 보완 명세

### HP0 — 변경 기준과 재현 고정

1. workspace·선택 release·실제 PID/start identity·정확 날짜 bootstrap·정책·원천 generation/hash를 다시 비교한다. 동작 중 wrapper가 읽는 파일을 교체하지 않는다. 공존 dirty 변경은 별도 범위로 보존한다.
2. F1–F5·F7의 최소 fixture와 기대 결과를 기존 관련 테스트에 넣는다. 합성 증거와 자연 row를 구분한다. 정상 기준선 golden 결과는 first crossing, 유예 여부, SELL intent/수량, hard-safety 우선권, runtime env 기준으로 고정한다. 실제 비용 정정·sidecar 재사용·동일 record의 복수 signal은 통합 fixture로 보강한다.
3. 현재 strict 0을 비용·수량·시간·원천 세대별로 분해하고 가장 최근 exact-date 포지션부터 producer→consumer를 확인한다. 과거 전체 기간 반복 스캔이나 333건 전부 복구를 착수 조건으로 만들지 않는다.

### HP1 — 정책 갱신 기간과 모수 격리

1. 기존 `policy_refresh_start_date(target_date)`를 사용해 감사 조회창과 후속 정책 평가창을 별도 선언한다. current scheduled 계산은 9/29 이후 forward evidence를 사용하고, 코드에 다른 시작일 상수를 추가하지 않는다. 명시적인 이전 기간 조회는 audit-only이며 선택기에 전달되지 않는다.
2. 기계식 코호트는 forward 경계와 검증된 classifier/policy generation의 적용 범위를 함께 결속한다. 과거 최초 v2 관측 하나로 전체 후속 cohort의 날짜를 결정하지 않는다. 선택기와 bootstrap 검증기도 window metadata/hash를 대조해 보고서의 오래된 시작일을 신뢰하지 않는다.
3. 경계 이전 매수 포지션의 원가·잔량·수탁·보유 승계는 계속 복구할 수 있다. 이를 과거 시장 경로/정책 성과를 후속 학습에 넣는 권한으로 사용하지 않는다. 경계 통과 포지션은 경제 평가 적격성과 custody 유지 상태를 각각 기록한다.
4. 알려진 결손 row/window/date는 식별자와 제외 사유를 남겨 격리한다. 정책 후보 비교에서는 동일한 적격 분모, 후보별 검열, 제외 notional에 대한 기존 보수적 검사를 유지한다. 봉인 census 자체가 없거나 전체 identity를 대사할 수 없으면 해당 범위의 선택만 차단한다. 다른 감사 기간의 결손이 forward 범위를 자동 차단하지 않게 한다.
5. `valid_empty`, `insufficient_sample`, `source_gap`, `censored`, `hold_no_edge`를 구분한다. 정상 0건과 원천 파일 부재를 같은 상태로 만들지 않는다. 비용/투표 표본 수를 만들기 위해 synthetic 또는 이전 정책 row를 섞지 않는다.

### HP2 — 실제 비용의 원천 계약과 자연 생산

1. 우선 로컬 보존 체결/정산 원천에 실제 수수료·세금이 있는지 read-only로 조사한다. 현재 `configured_fee_estimate_krw`나 `gross - configured_net`은 실제 비용이 아니다. 금액 0도 명시적 원천 증거가 있을 때만 실제 0으로 인정한다.
2. 실제 비용을 가져올 기존 API/정산 경로가 필요한 경우 구현 **전에** Official Kiwoom Reference Gate를 수행한다. 당시 upstream commit SHA, 확인한 `kiwoom_docs`·SDK/spec/core/realtime·Postman 경로, 조회 KST, real/demo·단위·부호·continuation·오류 의미를 기록한다. endpoint/FID를 이 계획에서 추정해 확정하지 않는다. 공식 문서가 없거나 주문/종목/일자별 비용 배분 의미가 불명확하면 계약 gap으로 남긴다.
3. 정규화된 비용 영수증은 계좌 scope hash, owner·position/buy generation, 거래일, 주문/체결 또는 공식 정산 key, venue/route, 수수료·세금 구성과 합계, 원천 단위·시각·raw/hash, completeness·revision을 포함한다. 비용의 적용 단위가 체결/주문/포지션/정산 중 무엇인지 명시하고, 모든 매수 leg·추가매수·부분 매도에 대한 비용 coverage를 대사한다. 계좌 총액을 종목/체결별 실제 비용으로 임의 배분하지 않는다. 민감 계좌 값은 일반 report/log에 노출하지 않는다.
4. 실제 총 매도대금−총 매수대금−공식 비용으로 exact PnL을 계산하고 수량·원가·부분체결·최종 잔량과 대사한다. 공식 누적 비용은 각 partial event에 중복 합산하지 않는다. 정산이 늦게 확정되면 원본 receipt를 보존하고 같은 포지션의 별도 correction generation으로 결속한다. 과거 DB 수익률이 configured 값이라면 원래 값을 보존하고 observed-exact 계층을 따로 두며 공식 비용과 일치하도록 DB 값을 꾸미지 않는다. exact 수익률은 검증된 exact PnL/원가에서 별도 계산하고 source를 명시한다. 기존 configured DB 수익률과 다르다는 이유만으로 검증된 exact 층을 다시 탈락시키지 않되, 실제 체결대금·비용·수량 내부 불일치는 거부한다. 런타임 `TRADE_COST_RATE`를 이 대사로 변경하지 않는다.
5. trade review의 현재 actual-cost 무조건 결손 분기를 검증된 영수증의 성공/실패 분기로 바꾼다. `configured_cost_estimated`, `actual_cost_pending`, `actual_cost_reconciled`, `cost_source_unavailable`을 구분하여 holding report와 기존 [전략 성과 consumer](../../src/engine/strategy_position_performance_report.py)까지 같은 의미로 전달한다. 정확한 비용을 얻지 못하면 strict에서 제외하되 가격/수량 복구까지 실패했다고 표시하지 않는다.
6. 체결 콜백·빠른 청산 루프는 비용 조회나 정산 응답을 기다리지 않는다. 이미 승인된 체결 후 reconciliation/장후 경로를 사용하며, 새 계좌 호출·예산·권한이 필요하면 그 운영 범위를 먼저 확정한다. 실제 비용이 없다는 이유로 보호청산·기존 초기정책·Main 기동을 새로 막지 않는다.
7. `completion_observed_date`는 원래 매도 완료일로 유지하고 `cost_available_at/reconciled_at`, revision, 보고서의 `knowledge_cutoff`를 별도로 기록한다. D+1 비용 확정으로 D일 거래를 D+1 신규 완료 건으로 복제하지 않는다. 과거 판단의 as-of 재현에는 그때 미확정 비용을 확정값으로 소급 넣지 않고, 정정 후 감사·향후 정책 평가에서는 원래 완료일의 label과 새 비용 가용 시각을 함께 결속한다. train/holdout 소속·분할 기준은 정정 때문에 이동시키지 않는다.
8. 비용 revision이 바뀌면 동일 원천 범위의 `completed_census_input_sha256`와 row/output hash를 다시 만들고, `save_monitor_snapshot`→completed census→`.completed_projection.json`→postclose manifest까지 새 세대로 봉인한다. wrapper의 기존 manifest 재사용 조건에도 비용 입력 generation을 결속하여 pipeline 로그가 그대로여도 새 비용이 반영되게 한다. report와 sidecar의 쓰기 사이에 중단되면 세대 불일치를 거부하고 기존 크기 제한을 유지한다. 256 MiB 초과 원본을 무제한 재파싱하는 우회로 복구하지 않는다. 이전 봉인·receipt를 보존하고, 재실행 멱등성·변경 없는 원천 재사용·일부 파일만 갱신된 경우의 거부를 검증한다. 운영 재생성은 HP5의 별도 허용 조건을 따른다.

종료 기준은 공식 비용 source가 확인된 경우 부분체결/최종체결→대사→strict 성공 fixture와 불일치 거부 fixture다. 실제 원천이 제공되지 않으면 `cost_source_unavailable`과 owner·부족 필드·다음 자료 조건을 남기며 **HP2의 실제 비용 수집 완료 또는 전체 경제 폐루프 완료라고 보고하지 않는다**. 나머지 독립 수리는 계속 진행한다.

### HP3 — 최초 crossing·AI 유예·실제 청산 시각의 동일 재생

1. 기계 최초 crossing 시각, 런타임 감지/평가 시각, 선행 투표 동결 시각, 유예 시작·해제 시각/사유, 실제 `exit_signal`, submit, 각 fill, final terminal을 분리한다. `signal_id`, position key, buy-fill identity, 정책/vector/bundle hash, market/route/epoch로 연결한다. wall/event time·수신/저장 시각·elapsed의 단위와 KST/UTC 변환을 명시하고, 시간 역전이나 restart 후 clock 결손을 유예 시간 연장으로 메우지 않는다. 새 이벤트 종류를 불필요하게 늘리지 않고 기존 transition/snapshot/defer/exit/terminal에 필요한 연결 필드만 보완한다.
2. PASS/INSUFFICIENT 즉시 진행, VETO 최대시간, 악화 한도, stale quote에서 유예 불허, hard/protect/emergency 우선 해제, pending SELL·추가매수 후 세대 변경을 기존 live 의미 그대로 재생한다. 순수 판단은 live/replay 공용으로 두되 I/O·실제 time/provider 호출은 runtime adapter에 남긴다. 휴리스틱 1초 허용폭을 늘려 F3를 감추지 않는다.
3. incumbent 재현은 기계 crossing과 **유예를 거친 실제 청산 허용**을 각각 검증한다. 기록된 10초 유예가 정확하면 정상 경로이고, 해제 사유·시계·원장 결손은 그 단계의 source gap이다. 전송/평가 지연을 모두 AI 유예로 재분류하지 않는다.
4. 다른 숫자 임계값 후보는 후보 crossing **이전**에 실제 저장된 동일 세대 표만 사용한다. 다른 입력이었다면 AI가 냈을 답변을 추정하거나 후보 신호 이후 표를 소급 사용하지 않는다. 후보 경로의 유예/시세/후속 상태를 식별할 수 없으면 검열 처리한다. 실제 매도 이후 경로, 부족한 bid 잔량, 과거 partial SELL은 기존 전량 CF 가정으로 메우지 않는다.
5. baseline에서 fast/normal 최초 crossing·폭·유예·SELL intent 결과가 기존과 동등해야 한다. 두 호출 경로와 기존 pending/retry 분기를 모두 대조한다. 루프에 동기 모델/비용 조회를 추가하지 않고 late result·중복 tick·restart·session/route 변경에 대해 새 신호·중복 주문 권한이 생기지 않아야 한다. 주문 dispatch 자체는 기존 owner를 유지한다. 관측 receipt 저장 실패는 source gap으로 남기되 기존 안전 처리 외의 새 SELL 차단이나 재주문을 만들지 않는다.

실제 비용이 확인돼도 후보 시점의 수수료·세금·슬리피지가 자동 관측되는 것은 아니다. CF는 선언된 execution/cost model과 그 버전·범위·민감도 결과를 따로 기록한다. 실제 체결 비용을 임의 비례 배분해 다른 가격·시간의 브로커 실제 비용이라고 표시하지 않는다.

### HP4 — 정책과 실제 진행 상태에 맞는 의미 감시

1. sentinel은 이벤트가 실제 소비한 mechanical policy/vector·bootstrap·PID generation을 전달하고 semantics는 그 시장의 start/width와 classifier identity를 검사한다. 기본값 0.4가 맞더라도 hash가 다르면 통과시키지 않는다. 검증된 0.5 후속 정책은 허용하고 무단 0.5·다른 시장/날짜/세대 값은 거부한다. 초기값 fallback도 이유와 정확한 baseline receipt로 식별한다.
2. 출력 계약은 `semantic_status`, identity별 `lifecycle_state`, `economics_status`, `as_of/source_generation`을 분리한다. `signal_observed`, `deferred`, `guard_wait`, `pending_submit`, `pending_terminal`, `completed`와 비용의 `pending/verified/unavailable`을 실제 사건으로 표시한다. `deferred`는 crossing 뒤 실제 exit 허용 전 상태이며, 모든 신호가 이 상태들을 순서대로 거친다고 가정하지 않는다. 기존 `pass`는 의미 검사 통과로만 읽고 completed나 exact-cost 증거로 승격하지 않는다.
3. 진행 집계는 최소 `position_key + buy_fill_identity + signal_id`로 나누고, submit/fill은 order/attempt/exit-token receipt로 대사한다. 한 record의 이전 submit/terminal로 다른 신호의 pending을 지우지 않는다. 취소·거부·기존 retry는 해당 attempt의 종결/후속 관계로 표시하고 포지션 완료로 바꾸지 않는다. 원래 signal_id나 buy generation을 복구하지 못하면 record_id만으로 완결 연결을 추정하지 않는다.
4. pending의 경과시간·기존 차단 사유·재평가 가능 여부를 연결한다. 안전 guard의 정상 대기를 주문 누락 장애로 단정하지 않고, 신규 submit deadline이나 자동 retry/SELL은 만들지 않는다. hard-safety 지연·시간 역전·수량 과다·정책 위조는 즉시 결함이고, 자연 표본 0·정산 대기는 별도 상태다.
5. sentinel의 일반 집계·semantics에 동일한 target date/`as_of`와 봉인 source generation을 전달한다. 당일 사건을 cutoff로 제한하되 전일에서 승계된 보유 원가·정책·custody 증거는 origin date를 유지해 별도 연결한다. 선행 표의 requested/received/persisted 시각 필터는 그대로 유지하고 vote 수 집계에도 cutoff를 적용한다. `as_of` 뒤 terminal·정산·post-sell observation을 당시 진행/경제 상태에 합치지 않는다. 후일 감사가 필요하면 별도 retrospective 모드와 source as-of를 표기하고, 당시 읽을 수 있었던 정책·원장을 복원할 수 없으면 `unassessed/source_gap`으로 남긴다. 현재 파일이나 mtime만으로 과거 가용성을 추정하지 않는다.
6. 위 분리 계약은 `holding_profit_exit_semantics_v2`로 명시하고 `holding_profit_exit_semantics`, sentinel JSON/Markdown, `artifact_freshness`와 실제 연결된 summary 소비자·회귀를 같은 변경에 맞춘다. v1 역사 보고서는 기존 의미로 읽되 lifecycle/cost 검증 부재를 완료로 간주하지 않는다. v2 필수 필드 누락·알 수 없는 enum·generation 불일치는 명시 거부하며, v1/v2 혼재와 미래 as-of 유입 fixture를 둔다. `pending_submit`만 producer에 추가하고 parser가 이를 `source_invalid`로 처리하는 미완성 인계를 남기지 않는다. 기존 보고 전용 notifier 권한을 확장하지 않는다.

### HP5 — 장후·준비·선택·PID 인계와 수용

1. postclose exit profile의 기존 trade review→post-sell→holding report 순서와 snapshot manifest byte hash를 유지한다. HP2의 비용 revision·census·sidecar·재사용 판정을 포함해 영향 있는 exact-date producer부터 차등 재생성하고 같은 세대의 summary·checklist·strict→controller→PREOPEN 준비를 검증한다. 원래 target date와 새 생성일을 혼동하지 않으며, 중간 실패 시 이전 PASS를 현 세대 성공으로 재사용하지 않는다. 이 후속 실행은 구현 검증과 별도 운영 권한이 충족된 때만 수행한다.
2. 현재 runtime summary의 `holding_exit_threshold_lineage`와 `holding_path_vote_lineage/policy`를 유지하며 원천·경제·후보·선택·PID 상태를 명시한다. primary family 9개 완료나 초기 15셀 발행만으로 보유청산 경제성이 완료됐다고 해석하지 않는다. 기존 direct-family 전체 구조를 새 generic 튜닝 체계로 되돌리지 않는다.
3. 식별된 수리 결함은 §2의 단일 stable owner로 generator/checklist에 인계한다. 단순 자연 표본 부족은 새 구현 결함을 계속 재발급하지 않는다. 결함 수리의 code closure와 다음 자연 terminal/cost 수용을 별도 필드로 남긴다. 누락·손상·만료한 mandatory handoff와 정상 carry/valid-empty를 구분한다.
4. 기존 선택기는 보고서→candidate→부모 CAS→한 시장·한 단계→override/retirement guard→정확 날짜 bootstrap을 그대로 통과해야 한다. numeric 후보와 classifier 후보가 경쟁하거나 원천 경계가 어긋나면 선택을 보류한다. 초기 보유 AI 정책에는 기존 승인권한을 보존하고 추가 EV gate를 걸지 않는다.
5. selector, 정책, summary, checklist, controller가 바뀌면 이전 `prepared_verified`는 역사 증거다. 현 세대 준비를 다시 만들고 검증할 때도 날짜 전 실제 활성화/PID 소비로 표시하지 않는다. 재기동·release 전환 권한은 자동으로 생기지 않는다.
6. 결과 상태는 `code_validated`, `selected_release`, `prepared_verified`, `actual_pid_consumed`, `natural_observed`, `terminal_cost_verified`, `economic_accepted`로 각각 기록한다. 경제성은 완료·비용 검증된 실제 표본과 식별 가능한 CF 비교를 구분하고, 과거 손익 복구를 수리의 신규 이익으로 계상하지 않는다.

### HP6 — 보유 AI 후속 최적화의 별도 범위

현재 초기 15셀 publisher/loader를 고장으로 취급하지 않는다. 표 수·최신성·시간창·유예의 후보별 decision count, null EV의 원인과 `baseline_prior_no_verified_paired_economics`를 정직하게 전달하는 것까지 HP5의 완료 범위다.

후속 정책 자동 최적화는 별도 승인된 구현 범위가 있을 때만 진행한다. 그때도 기존 `holding_path_vote_policy` owner에서 schema/selection authority와 기준선·후보·롤백 hash를 버전 관리하고, 임의 숫자를 허용하도록 baseline 동등성 검사를 단순 삭제하지 않는다. HP2·HP3의 식별 가능한 실행·비용 모델, 경로×시장별 동일 분모, 선행 표 원장, 독립 holdout, 유예로 인한 안전 악화, 후보별 검열을 갖춘 경우만 비교한다. 모델/프롬프트·provider·호출 주기·주문/수량은 이 튜닝의 조작점이 아니다. 식별 불가능한 셀은 정확한 기존 정책을 유지하고 추정 EV를 실현 EV로 승격하지 않는다.

## 6. 검증 계획과 수정 순서

최소 실행 순서는 **HP0 → HP1·HP2 원천 계약 → HP3 → HP4·HP5 → 재리뷰**다. HP1·HP4의 독립 수리는 공식 비용 원천 미확정 때문에 정지하지 않는다. HP2 완료를 주장할 수 없는 경우 남은 blocker를 그대로 두고 code/관측 수용을 분리한다. HP6는 이번 결함 수리의 자동 확장 범위가 아니다.

| 검증 묶음 | 필수 사례 | 기존 대상 테스트 |
|---|---|---|
| 기간·모수 | 9/28 감사 유지·9/29 forward 포함, 장기보유 원가 보존, identifiable gap 격리, missing global census 차단, valid-empty와 missing 구분 | `test_holding_exit_observation_report.py`, `test_scalp_trailing_mechanical_strength.py` |
| 체결·비용 | partial/full, 매수·추가매수·매도 비용 coverage, cumulative 중복·재수신, 정산 지연·수정, actual 0과 missing, 계좌/owner/route/order 충돌, balance-only, retired 수탁 보존 | `test_trade_review_report_revival.py`, `test_live_trade_profit_rate.py`, `test_main_lifecycle_receipt_integration.py`, `test_strategy_position_performance_report.py` |
| 저장·정정 세대 | D일 완료/D+1 비용 가용성, 완료일/holdout 유지, 비용만 변경된 경우 cache 무효화, report/sidecar 일부 갱신·봉인 불일치 거부, 큰 원본 우회 금지, 동일 입력 재실행 멱등성 | `test_log_archive_service.py`, `test_trade_review_report_revival.py`, `test_holding_exit_observation_report.py`, `test_threshold_cycle_wrappers.py` |
| live/replay | PASS/INSUFFICIENT, VETO 정상 만료/악화/안전 해제, fast/normal·pending/retry 동등성, crossing→exit 지연, 후보 신호 뒤 표 금지, 늦은 응답, clock 역전·restart·ADD 세대·시장 전환, bid 부족과 actual exit 이후 검열, 관측 기록 실패 시 기존 안전 동작 유지 | `test_holding_exit_vote.py`, `test_holding_path_vote_replay.py`, `test_scalp_trailing_decision.py`, `test_scalp_trailing_mechanical_strength.py`, `test_scalp_exit_safety_monitor.py`, `test_sniper_scale_in.py` |
| 의미 감시 | 승인 0.5/무단 0.5, 값 같고 hash 다름, signal만 있음, guard 대기, 동일 record 복수 signal/세대·취소/거부, submit 후 partial/terminal, 완료 비용 대기, cutoff 이전/일치/이후 사건·늦게 도착한 표·정산, v1/v2와 enum 호환 | `test_holding_exit_sentinel.py`, `test_error_detector_artifact_freshness.py` |
| 직접 인계 | 초기 0표 15셀 유지, exact source/target/hash, broken receipt 거부, 정상 carry, 적용 전/후 날짜, stable owner 중복 없음, 준비 세대 변경 | `test_runtime_approval_summary.py`, `test_postclose_summary_handoff.py`, `test_runtime_policy_bootstrap.py`, `test_next_preopen_readiness.py`, `test_build_next_stage2_checklist.py`, `test_threshold_cycle_wrappers.py` |

테스트 경로·case는 구현 착수 때 존재와 실제 consumer를 다시 확인한다. 코드 수정 시 관련 pytest·compile, wrapper 수정 시 `bash -n`·계약 회귀, 문서/owner 변경 시 print-only parser와 `git diff --check`를 수행한다. 작은 고정 fixture·exact-date differential을 우선하고, 동일 원천의 광범위 재생성은 반복하지 않는다. 각 묶음은 구현→자체 리뷰→수정→재리뷰→표적 검증을 반복한다.

성능 수용은 기존 fast/normal에 동기 provider/정산 I/O 추가 0건, 동일 입력의 주문 판단 동등성, bounded 원장/메모리·락, callback·투표 저장·청산 판정 지연의 변경 전후 비교다. 새 시간 임계값을 운영 정책으로 주입하지 않는다. 실제 자연 표본이 없으면 성능/체결 수용은 미관측으로 남기고 합성 결과와 섞지 않는다.

## 7. 완료·중단·rollback 기준

- **계획 완료:** F1–F7의 근거·권한·owner·종료 검사, 비용 정정/저장 세대·as-of·signal별 상태 계약, 수정 위치와 구현 순서, 공식 비용 원천 미확정 및 AI 후속 선택의 별도 범위가 명시되고 문서 검증을 통과한다.
- **수리 코드 완료:** F1–F5·F7 회귀와 비용 revision→census/sidecar→재사용 판정을 포함한 producer→마지막 consumer 계약 검증이 통과한다. HP2 원천 미확정이면 해당 항목 미완료를 남긴다. 자연 체결이나 양의 EV는 코드 수리 완료를 대신하거나 추가 승인 장벽이 되지 않는다.
- **운영 완료:** 별도 허용된 적용 후 정확 날짜 정책·release/PID receipt, 자연 crossing/유예/SELL/terminal/비용의 한 세대 연결을 확인한다. 표본이 없으면 정책/PID 소비까지의 상태만 닫는다.
- **경제 완료:** 적격 실제 비용·기존 forward window·독립 비교·기존 family guard가 충족된 경우에만 판정한다. `null`, 검열, source unavailable은 경제 실패나 0 EV가 아니다.
- **즉시 중단/복원 조건:** hard/protect/emergency 지연, 중복 주문·수량/owner 침범, stale/conflict 허용, 영수증 위조/세대 불일치, unbounded hot-path 대기. 해당 변경을 검증된 이전 source/consumer 세대로 되돌리되 퇴역 executor를 되살리지 않는다. source-gap나 표본 부족만으로 운영자 lock을 해제하지 않는다.

## 8. 이번 문서의 검토·검증 기록

- 최초 검토에서 실제 비용 미생산(F2), live VETO와 replay 시간축 불일치(F3)를 단순 표본 부족과 분리했다.
- 추가 검토에서 semantic start 하드코딩(F4), pending-submit PASS(F5)를 합성 재현하고 계획에 반영했다. 이는 운영 청산 실패가 자연 발생했다는 증거가 아니다.
- 재검토 보완: 초기 AI baseline 발행은 정상 동작으로 유지, HP6 자동 후속 선택과 비용 원천 미확정의 authority boundary 명시, 실제 비용 0/누적/정산수정·DB configured 값 보존, 미래 봉인 checklist 비수정, status 소비자 동시 보완, current selector와 이전 대화의 selector 구분.
- 이번 보완 리뷰: F7의 cutoff 불일치를 메모리 fixture로 재현하고, HP2의 `log_archive_service`/census/sidecar/manifest 재사용 경로·비용 정정 시점과 완료일 분리·큰 원본 재파싱 금지·중간 실패 검증을 추가했다. F5를 실제 주문 장애가 아닌 상태 전달 계약으로 명확히 하고 signal/attempt별 진행 상태와 v1/v2 호환을 명세했다. HP3에는 fast/normal·pending/retry·관측 실패 회귀를 보강했다.
- 보완판 검증: print-only parser exit 0·기존 backlog 20개, 로컬 링크 33개·기존 테스트 파일 20개 경로 확인, `git diff --check`와 untracked 계획의 별도 whitespace 검사 통과. `DirectFamilyPreopenPolicyHandoff`는 10/12 checklist에 1개, 제안 `HoldingProfitExitSourceContractRepair`는 0개다. 10/9 checklist 부재와 미래 checklist 비수정을 재확인했으며 과거 reference 항목을 현재 실행 owner로 채택하지 않았다. 첫 검증에서 잘못 쓴 freshness 테스트 파일명을 실제 경로로 보완한 이력은 유지한다.
- 10/12 checklist SHA256 `6a5428aaa23200c9a7d71ff6ac47286908237d29dfcab6d55d1dd36cb69751b9` 유지 확인. 이번 변경 파일은 이 계획 하나다. trading/provider pytest·compile, 브로커/API 호출, 보고서 재생성, 외부 Project/Calendar sync는 문서 작업 범위 밖이므로 실행하지 않았다. 합성 함수 재현은 운영/PID·실제 비용 원천 검증을 대신하지 않는다.
