# 완료 포지션별 보유·청산 손익 경로와 런타임 임계치 연결 구현계획

작성: 2026-09-23 KST. 상태: **원천 연결 코드 구현·자연 검증 미종결**. 범위는 메인 실거래 `SCALPING/SCALP` 완료 포지션의 관측·대사와, 청산 판단에 연결될 수 있는 런타임 임계치의 소비 경로 조사다. 본 구현은 관측 필드와 장후 보고서만 보완하며 런타임·정책·임계치·주문 변경이나 장후 모니터링 실행을 승인하지 않는다. 실행 일정과 stable ID는 [당일 체크리스트](../checklists/2026-09-23-stage2-todo-checklist.md)의 별도 OPEN owner로 확정해야 한다. [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8의 active/OFF·안전·경제성 경계가 우선한다. [상류 진입 실행 계획](./main-entry-downstream-postclose-profitability-closure-plan-2026-09-23.md)의 H1을 이어받되, 진입 정책의 효과를 청산 효과로 중복 계상하지 않는다.

## 1. 결정과 확인된 결손

**첫 우선순위는 holding AI 임계치 변경이 아니라 완료 포지션의 전체 모집단·실제 청산 인과·체결비용·청산 후 관측의 연결이다.** 결과에서 손실 기여가 큰 규칙/조건이 밝혀지면 그 규칙의 `bounded_tunable` 임계치만 별도 경제성 평가로 넘긴다. `holding_flow`가 실제 판정을 바꾼 표본이 없으면 AI 품질 개선이나 점수 문턱 변경의 EV를 주장하지 않는다.

| 확인된 9/23 원천 | 현재 의미 | 첫 수리/검사 |
| --- | --- | --- |
| [`trade_review_2026-09-23.json`](../../data/report/monitor_snapshots/trade_review_2026-09-23.json) 15:55 스냅샷: 진입 10건, 완료 8건, 실현손익 +1,279원, 유효 평균 수익률 -0.28%; 완료 청산 규칙은 trailing 7건·soft stop 1건. | 해당 시점의 실현 결과이지 일일 최종치나 규칙별 인과 효과가 아니다. 1건의 큰 손실을 7건의 수익과 같은 규칙으로 묶지 않는다. | 포지션별 원천·비용 및 최종 시각을 확인하고 봉인된 기준 시각을 명시한다. |
| [`sniper_trade_review_report.py`](../../src/engine/sniper_trade_review_report.py)의 `metrics.completed_trades`는 전체 건수지만 `sections.recent_trades`/`completed_trades`는 `top_n` 기본 10건으로 잘린다. [`holding_exit_observation_report.py`](../../src/engine/holding_exit_observation_report.py)는 `recent_trades`만 읽는다. | 화면 표시용 상위 N건이 보유·청산 경제성의 전체 분모로 오인될 수 있는 **구조적 결손**이다. | 기존 owner에서 전체 완료 거래용 compact projection/원천 조회를 분리하고 DB·terminal 건수와 ID 집합을 대사한다. 단순히 `top_n`을 키우지 않는다. |
| [`post_sell_feedback_2026-09-23.json`](../../data/report/monitor_snapshots/post_sell_feedback_2026-09-23.json) 15:56 스냅샷: 후보·평가 6건, 보고서 내부에는 `partial_window` 품질 표기가 있다. 완료 8건 중 2건은 balance reconciliation 경로이고 정확한 체결시각이 없다. | 완료 손익 분모와 청산 후 경로 분모가 다르다. 2건의 청산 후 결과를 실패/0으로 채우지 않는다. `MISSED_UPSIDE`는 매도가 위 반등의 진단이며 순익 개선 증거가 아니다. | 직접 체결 receipt의 시각을 확인할 수 있는 건만 horizon 적격; sync-only는 정확한 체결시각이 회복되지 않으면 별도 `not_observable` 유지. |
| [`sniper_trade_review_report.py`](../../src/engine/sniper_trade_review_report.py)의 청산 규칙은 `exit_signal` 부재 시 `sell_order_sent`/`sell_completed` 사유에서 추정될 수 있다. | `inferred_exit_rule`은 귀속 보조 자료이지 실제 AI/flow 개입 증거가 아니다. | 명시적 판정 이벤트와 추론 라벨을 분리하고, 추정 사례는 해당 임계치 인과 분석에서 제외한다. |
| [`holding_exit_observation_report.py`](../../src/engine/holding_exit_observation_report.py)의 완료 요약은 `realized_pnl_krw` 결손을 `0`으로 합산할 수 있고, 당일 구분에는 추천일/매수일을 사용한다. | 유효 `profit_rate`와 원 단위 순손익·비용의 완전성이 다르며, 전일 보유분의 당일 매도 귀속도 별도 확인이 필요하다. | 원 단위 PnL/비용 결손을 null·분모 제외로 유지하고 매도 terminal 날짜 기준과 원 진입 날짜 기준을 따로 검증한다. |

9/22 등 과거 스냅샷을 오늘 전체 장후의 정답으로 대체하지 않는다. 깨끗한 튜닝 기준은 2026-06-05 00:00 KST 이후이며, 결손 행/창은 식별해 제외하고 임의의 0·gross EV로 복구하지 않는다.

## 2. 완료 포지션 단위 연결 계약

기본 키는 `position/recommendation record_id`와 원 진입의 `attempt/cycle`이다. 여기에 `account/custody`, `symbol`, `venue/session`, 원 진입 정책 세대, `source_date`, 부분체결/scale-in 하위 leg, 매도 order·fill ID를 붙인다. 코드·시각만으로 다른 포지션을 합치지 않는다. 한 포지션의 여러 SELL 시도/부분체결을 한 terminal로 합산하되 원 체결별 수량·가격·비용은 보존한다. `main-only`·`normal_only`·`post_fallback_deprecation` 및 real/sim/probe/CF를 별도 차원으로 고정한다.

| 단계 | 기존 소유자/연결 필드 | 새 구현의 필수 판정 |
| --- | --- | --- |
| 원 진입·보유 상태 | DB 완료 row, [`sniper_trade_review_report.py`](../../src/engine/sniper_trade_review_report.py), 원 진입/scale-in receipt | 시작 수량·원가·부분체결·추가매수 전이를 먼저 고정. 청산 문제를 진입 AI false PASS나 AVG_DOWN/PYRAMID 효과로 자동 귀속하지 않음. |
| 청산 후보·우선순위 | [`sniper_state_handlers.py`](../../src/engine/sniper_state_handlers.py)의 실제 `exit_signal`, hard/protect/emergency·trailing·soft stop 판정 | `observed_exit_rule`, 후보별 통과/차단, 최종 우선 규칙, 비교 lhs 값, effective threshold와 적용 시각을 보존. 추정 규칙은 `inferred`로 표시. |
| 유효 AI 점수·flow 개입 | holding score 수용 gate, `holding_flow` review/override, [`holding_exit_sentinel.py`](../../src/engine/holding_exit_sentinel.py) | 호출 없음/원점수/유효점수/무효·fallback/TTL·품질/선택 prompt·provider/flow action을 구분. `HOLDING_FLOW_OVERRIDE` 출처 라벨만으로 매도 변경을 주장하지 않고 **원래 후보 행동 대비 실제 defer/force/confirm**을 기록. |
| 매도·비용 | [`sniper_execution_receipts.py`](../../src/engine/sniper_execution_receipts.py), [`sniper_sync.py`](../../src/engine/sniper_sync.py), broker terminal | 주문·ACK·부분/전체 fill·잔량·정산, 정확/추정 시각, 매도세·수수료·슬리피지·원가, 실현손익과 `profit_rate`의 일치성. balance reconciliation은 `broker_balance_reconciliation_only`로 별도 표기. |
| 청산 후 경로 | [`sniper_post_sell_feedback.py`](../../src/engine/sniper_post_sell_feedback.py)의 `post_sell_id` 후보/평가와 [`holding_exit_observation_report.py`](../../src/engine/holding_exit_observation_report.py) | 정확한 매도 fill time·동일 venue/source/성숙한 관측창이 있을 때만 horizon 평가. `partial_window`, 미도래, source 결손, sync-only 미정시각은 각기 다른 결손 사유. |

포지션 결과 행은 `lineage_status=complete|partial|source_gap|not_observable|inferred_only`와 단계별 첫 blocker를 가진다. 보고서는 `완료 전체 건수 → 원천 연결 → 명시적 청산 판정 → AI/flow 개입 판정 → terminal/비용 → 후속 관측 가능/평가 완료`의 각 분모·ID 집합·제외 건수를 별도로 표시한다. 장후 모니터 snapshot과 원천의 해시/생성시각을 기록해 미완성 스냅샷을 최종 일일 보고서로 승격하지 않는다.

## 3. 청산 런타임 임계치 조사와 연결 범위

아래는 **확인된 소비 경로의 분류 시작점**이다. [`constants.py`](../../src/utils/constants.py)의 기본값이나 환경변수 이름을 실제 적용값으로 간주하지 않는다. 구현 시작 시 메인 SELL 후보 생성·재검토·전송·동기화의 `_rule*`, 직접 `os.getenv`, position-pinned 값, 날짜별 policy loader, operator override, venue/session branch를 모두 역추적해 `threshold_inventory`를 봉인한다. 각 키는 `reader/consumer`, effective 값·단위·비교 연산자, 기본/환경/정책/포지션 우선순위, 활성 조건, 적용 cohort/시각, safety 역할, source hash, 실제 PID/release 소비, exit rule·event field를 가져야 한다. 이름만 있고 읽지 않는 키, 분기만 있고 임계치가 없는 조건, 미계측 판정은 각각 `unused|non_numeric_guard|source_gap`으로 기록한다.

| 임계치·분기 계열(확인 지점) | 연결해야 할 판정/값 | 권한·분리 경계 |
| --- | --- | --- |
| `SCALP_STOP`, `SCALP_HARD_STOP`, `SCALP_PRESET_HARD_STOP_*`; 포지션 고정 hard stop | 최초 손실 터치, grace/긴급 우선순위, 실제 hard stop 실행 | hard/protect/emergency는 안전축. 수익 개선을 이유로 완화 금지; preset TP는 청산 수익 실현 owner가 아님. |
| `SCALP_SOFT_STOP_MICRO_GRACE_*`, `ABSORPTION_*`, `THESIS_*`, `DYNAMIC_GRACE_*`, `WHIPSAW_CONFIRMATION_*`, expert defense | soft stop 후보·유예/연장·휩쏘 확인·타임아웃·최종 매도; AI 점수가 조건에 쓰였는지 | 실제 ON·OFF와 position-pinned override를 구분. whipsaw는 Plan Rebase상 OFF/source-only; OFF 조건의 결과를 실제 개입으로 세지 않음. |
| `SCALP_TRAILING_START_PCT`, `SCALP_TRAILING_STRONG_AI_SCORE`, `SCALP_TRAILING_LIMIT_STRONG/WEAK`, `SCALP_PROTECT_TRAILING_*` | peak, giveback, strong/weak 점수 갈림, 보호선 평활/긴급 종료 | trailing은 활성 owner. legacy `SCALP_TRAILING_LIMIT`은 실제 소비 확인 없이 현행 선택 임계치로 취급 금지. protect/emergency 우선순위 유지. |
| holding score의 TTL/critical-zone TTL, live/parse/fallback/data-quality gate, prompt 활성 날짜·venue/session | raw 점수가 실제 trailing/soft-stop 조건에 쓸 수 있는 유효 점수였는지와 선택 세대 | 점수 50·cache MISS·fallback만으로 AI 효과 추정 금지. prompt 후보·활성 receipt와 실제 PID 소비는 별도. |
| `KORSTOCKSCAN_SCALP_TRAILING_CONTINUATION_RECHECK_*`, `...LOSS_CONVERSION_RECHECK_*` | 날짜/enable/TTL, 가격·고점·AI·quote freshness·REST recovery·재검토 후 결정 | 직접 환경 경로가 있으므로 `constants.py`만의 조사로 누락되기 쉬움. 활성 날짜·PID·포지션 적용 여부를 먼저 검증. |
| `SCALP_AI_MOMENTUM_DECAY_*`, `SCALP_MFE_PROTECT_*`, `SCALP_SAFE_PROFIT` 및 stagnation/bad-entry/time-stop 계열 | 점수·보유시간·고점/되돌림·수익구간별 별도 exit 후보/observe 판정 | 각 계열의 실제 enable 및 observe/shadow 상태 확인. OFF/관찰은 손익 원인이나 라이브 후보가 아님. |
| `HOLDING_FLOW_OVERRIDE_*`, `HOLDING_FLOW_OFI_*`, `HOLDING_FLOW_MAX_DEFER_EXTENSION_*`, never-green defer clamp 및 micro-estimator env | 후보 청산에 대한 flow 검토, OFI·신선도·worsen·최대 defer/연장, force/confirm | bounded defer만 기존 exit 후보에 개입. OFI smoothing은 가드 내 ON. 원래 exit 규칙과 실제 변경 행동을 별도 저장. |
| `SELL_SIDE_OPEN_TIME_BLOCK_*`, `SELL_TIMEOUT_SEC`, `SELL_ORDER_FAILURE_RETRY_BACKOFF_*`, route/session·broker/account/order/quantity/cooldown·시세 신선도 | 판단 뒤 전송 지연·차단·재시도·시장 경로, 실제 fill 품질 | 실행·안전/custody 축. 청산 규칙 임계치의 EV로 귀속하지 않고 별도 blocker·비용을 기록; 안전 완화 금지. |
| AVG_DOWN/PYRAMID의 별도 trailing/scale-in/exit 값, manual/widget/episode·machine supplemental exit | 포지션별 실제 owner·진입 이후 action 전이 및 독립 runtime 적용 | 메인 청산과 손익/threshold 후보를 합치지 않음. 다른 owner가 사용한 값을 메인 공통 임계치로 소급 적용하지 않음. retired Holding/Exit ADM·matrix와 sim panic exit는 실거래 조정 대상 아님. |
| `post_sell_feedback`의 missed-upside/good-exit 라벨 기준 | 후행 경로의 진단 라벨과 관측 품질 | 장후 **분류 임계치**로 별도 inventory에 기록하되 런타임 SELL 결정 임계치와 섞지 않음. |

완전성 판정은 `실제 메인 SELL 평가에서 읽힌 모든 키/분기 ⊆ inventory`, `inventory 활성 키 ↔ 판정 event/포지션 snapshot` 대사다. 문자열 검색만으로 끝내지 않고 직접 환경 접근·내부 helper·position state·외부 정책 파일·release env를 함께 검사한다. 유효값을 복원할 수 없는 과거 건은 현재 기본값을 대입하지 않고 `threshold_provenance_missing`으로 분리한다. 청산 시점의 유효값을 새로 기록하는 장중 계측은 최소 필드만 기존 event에 추가하고 원 판정·provider 호출·주문 횟수는 바꾸지 않는다.

메인 밖의 **실제 청산 런타임도 누락 없이 조사하되 소유자는 합치지 않는다.** 별도 포지션/custody 키로만 상호 연결 가능한지 확인한다.

| 별도 runtime owner | 조사할 임계치·연결점 | 메인 계획에 들어오는 범위 |
| --- | --- | --- |
| [`widget_symbol_runtime_policy.py`](../../src/engine/monitoring/widget_symbol_runtime_policy.py)와 실제 widget 실행 소비자 | `target_bps` → `take_profit_bps_from_equal_share_average`, `force_exit_time`, dated policy/loader·PID·실제 SELL receipt | widget 자체의 lot/terminal/비용 대사만. 메인 trailing의 수익 표본이나 공통 exit 임계치로 합치지 않음. |
| `machine_adaptive_exit` 및 별도 기계 target exit | [`machine_adaptive_exit_policy.py`](../../src/trading/config/machine_adaptive_exit_policy.py)의 승인된 세대·범위, [`machine_adaptive_exit_approval.py`](../../src/engine/automation/machine_adaptive_exit_approval.py)의 apply 경계, 기계 target·manual exit 판별 | 원 machine lot/exit_execution_class와 broker terminal까지 추적. 승인된 보조 출구가 실제 어느 보유분에 적용됐는지 확인하고 메인 전체 보유분에 자동 소급하지 않음. |
| low-price two-leg·episode·manual, AVG_DOWN/PYRAMID | 각 런타임 policy/position-pinned stop·target·시간/수량, 실제 owner와 체결/수동 custody | 같은 종목·계좌라도 별도 lot/owner로 유지. OFF/source-only/probe는 실거래 청산 모집단 밖에 둠. |

각 별도 owner에서도 `정의 → 현재 선택 정책/override → 실제 consumer → position/lot → SELL terminal → 비용 → 후속 관측`의 연결 가능 여부를 기록한다. 소비자가 확인되지 않은 정책값은 `selected_only`, 실행이 없는 source-only 값은 `no_live_effect`로 남긴다. 다른 owner의 임계치 조사 결과가 메인 `threshold_inventory`의 미매핑을 정당화하지는 않는다.

## 4. 단계별 구현 경계

1. **E0 모집단 봉인:** 기존 `trade_review`의 화면용 `top_n`과 별개로 `holding_exit_observation`이 전체 완료 거래의 작은 정규화 projection을 읽도록 한다. source date, `COMPLETED + valid profit_rate`, real/full·partial, original entry/scale-in·custody 구분을 보존하고 원 DB/terminal/화면 수치를 ID 단위로 대사한다. 매도일 기준 완료와 추천/매수일 기준 cohort를 별개로 저장하고, 비용 또는 원 단위 순손익 결손은 0으로 더하지 않는다. 현재 스냅샷 결손을 새 JSONL 전량 반복 스캔으로 우회하지 않는다.
2. **E1 임계치·판정 lineage:** §3의 키/분기 inventory를 테스트로 고정하고, 후보 평가 시 해당 포지션이 실제 소비한 유효값·출처·버전·비교값·우선순위만 기존 pipeline/exit event에 연결한다. OFF/비적격 branch는 `not_evaluated`로 기록한다. AI 점수 유효성 gate(원점수≠유효점수, fallback, stale, parse/source 품질)와 flow의 `reviewed_only|deferred|forced|confirmed|not_eligible`를 비교한다.
3. **E2 매도 terminal·비용:** 직접 SELL receipt와 sync reconciliation을 같은 포지션에 합치되 중복 매도·분할 fill은 수량 보존으로 검증한다. 9/23 sync-only 두 건의 원 broker receipt에 실제 fill timestamp가 남았는지 읽기 전용으로 확인하고, 없으면 그 과거 시각을 생성하지 않는다. `sell_time_precision=order_second_not_fill_second`는 분 단위 청산 후 관측의 적격시각이 아니다. terminal/비용 오류는 owner receipt에서 수리하고 경제성 집계가 임의 보정하지 않는다.
4. **E3 청산 후 관측:** `post_sell_id`와 원 position/fill ID를 명시 연결하고 1/3/5/10분 등 기존 horizon의 성숙·동일 source/venue/품질을 검사한다. 관측 불가/부분 창을 유효 후행 경로로 합치지 않는다. 청산 후 MFE·MAE는 진단이며 보유 지속 시 실제 체결·비용 후 순익과 동일하지 않다.
5. **E4 경제성·후속 튜닝:** 실제 완료 전량의 `realized_pnl_krw`, `simple_sum_profit_pct`, equal/notional-weighted 비용 후 EV를 분리한다. 동일 포지션의 규칙·AI 개입·flow 개입은 설명 차원이고 각 축에서 손익을 재합산하지 않는다. 손실 기여가 큰 **실제 개입 규칙**만 fixed incumbent·동일 모집단·full-cost exit/자본/부분체결·tail·시간순 holdout과 비교한다. 반사실 경로가 없으면 `source_gap`/관찰만 남기며 정책 추천·새 값 적용은 별도 승인/owner다.

기존 [`holding_exit_observation_report.py`](../../src/engine/holding_exit_observation_report.py)가 장후 소비와 집계를, [`sniper_trade_review_report.py`](../../src/engine/sniper_trade_review_report.py)가 포지션 진단을 소유한다. [`sniper_post_sell_feedback.py`](../../src/engine/sniper_post_sell_feedback.py)는 horizon 원천, `sniper_state_handlers.py`는 실제 판정/임계치 소비, `sniper_execution_receipts.py`·`sniper_sync.py`는 매도 terminal을 소유한다. 새 공통 엔진·독립 cron·AI 호출/주문 경로를 만들지 않는다. 장후 source/hash 검증 후 영향받은 consumer만 재생성하며, 추가 wrapper/stage/자동화 규칙을 수정해야 한다면 그때 운영 문서·체크리스트를 같은 변경집합에 갱신한다.

## 5. 수용·리뷰·권한

| 게이트 | 완료 기준 |
| --- | --- |
| 전체성 | 봉인 source의 DB 완료 ID 집합 = observation 입력 완료 ID 집합 + 사유별 제외 집합. `>top_n`, 동일 종목 다중 포지션, 부분체결, source correction/late terminal 회귀를 통과. 보고서 화면 10건 제한은 유지 가능하나 경제성 분모에 전파되지 않음. |
| 인과·임계치 | 직접 `exit_signal`과 추정 규칙 구분, 후보→유효 임계치/AI score/flow→최종 action→SELL 순서·시각·PID/release/hash 검증. 강제/보류/확인 0건도 0으로 명시하되 AI 무효·미호출·검토만 한 건과 섞지 않음. 모든 실제 소비 키/분기가 inventory에 매핑되거나 명시적 source gap. |
| 실행·비용 | 수량·원가·매도 fill/세금/수수료/정확도 대사; 실현손익/수익률 결손은 null. sync-only 완료 손익은 유지하되 fill 시각이 없으면 후행 horizon 불가. 주문 미전송과 미체결, real과 sim/probe/CF를 분리. |
| 관측·경제성 | 청산 후 적격/partial/미도래/불가의 분모와 품질 공개. 비용 후 PnL·EV·후속 경로 진단을 구별; 동일 frozen cohort, 독립 holdout/rolling 또는 post-apply version, tail·안전 veto 없이는 threshold 후보 승격 금지. |
| 운영 | 기존 report/strict handoff의 날짜·해시·consumer를 확인. 코드 PASS, 장후 산출, dated 정책 선택, PREOPEN 검증, 실제 PID 소비, 자연 매도·비용 후 개선을 별도 receipt로 보고. fail-closed 또는 incumbent carry; 안전·operator lock·custody는 불변. |

구현 시 기존 `test_trade_review_report.py`, `test_holding_exit_observation_report.py`, `test_post_sell_feedback.py`, `test_holding_flow_override.py`와 관련 SELL receipt/sync 회귀를 확장한다. 먼저 실패 테스트로 `>10`건 분모 누락, AI raw50/무효 점수의 false intervention, 실제 force/defer 없는 source label, sync-only 잘못된 10분 horizon, OFF 임계치가 live로 집계되는 사례를 재현한다. 그 뒤 최소 수정→재검토→영향 범위 테스트/compile→`git diff --check` 순서로 닫는다. provider 호출·주문·임계치 변경은 이 관측 구현 범위 밖이다.

## 6. 구현 진행과 현재 수용 경계

당일 checklist OPEN owner는 `HoldingExitPositionOutcomeLineageClosure`다. 재리뷰 중 DB `sell_time`이 빈 잔고대사 완료 2건이 완료일 필터에서 탈락하는 회귀를 발견해, terminal `sell_completed` 관측일을 정확한 fill time과 별도 필드로 봉인했다. 과거 진입분의 현재 DB `COMPLETED` 상태가 과거 날짜로 역투영되는 문제도 함께 막았다. 현 코드의 9/23 읽기 전용 재산출은 전체 8건, 직접 비용 확정 6건/-4,621원, 비용 미확정 2건을 유지한다. 명시적 `exit_signal`이 같은 규칙의 후속 terminal보다 우선하도록 수리했으며, 후행창 `pass`도 1/3/5/10분 지표·10분 성숙을 별도 확인한다.

위 저장 원천의 확인 시점 SHA-256은 `trade_review_2026-09-23.json=eb362d7468d70b5562b157f261df837af3409bd4e723a4170eb11509ed9461d8`, `post_sell_candidates_2026-09-23.jsonl=0d01f03f8edfef608f67bd660e96c4f1ad1c87fd8f972acd8367f4f6015a1363`, `post_sell_evaluations_2026-09-23.jsonl=307a32cbb04ce09a318d4e64ee92e803824e2717cd493c0588a14d43bdbb83f7`이다. 이는 과거 스냅샷 출처 영수증이며 새 코드의 장후 재산출·strict terminal 영수증은 아니다.

기존 `trade_review`에 화면 10건과 분리된 **전체 canonical COMPLETED projection**을 추가하고, 당일 `sell_completed` ID로 전일 진입 carry 포지션만 PK 조회한다. `holding_exit_observation`은 날짜별 선언 건수/ID를 대사하고, legacy 상위 N건·DB 경고·필터된 snapshot·비용 결손은 경제성 증거에서 제외한다. 포지션 행에는 실제 SELL receipt의 비용·수량·official fill time, AI 유효성, flow 실제 defer 여부, 관측창 품질을 연결한다. 표준/fast SCALP 청산은 이미 계산된 선택 분기의 유효 임계치·비교값을 관측 필드로만 남긴다. 환경/정책 출처·PID/release 직접 소비가 증명되지 않은 값은 `effective_branch_only`이며 모든 임계치의 출처가 닫혔다고 표시하지 않는다.

9/23 15:55의 기존 화면 snapshot 8건을 **읽기 전용 재대사**한 결과, 직접 체결 영수증 6건의 비용 후 부분집합 합계는 **-4,621원**이고, 그중 soft stop 1건은 **-5,054원**이다. 잔고 대사 2건의 모델 손익 **+5,900원**을 합쳐 화면 전체는 +1,279원이지만, 이 2건은 정확한 fill second/후행 horizon과 같은 수준의 비용 출처가 없으므로 전체 exact-cost EV는 **null**이다. 8건의 청산 규칙은 모두 추정 경로이며, 관측된 명시적 `exit_signal`·유효 임계치 receipt·flow defer는 각각 0건이다. 직접 체결 6건의 post-sell 평가도 모두 `ka10080_continuation_page_limit_reached`로 `partial_window`; 2건은 정확한 fill time이 없어 관측 불가다. 이는 **손실 원인 조사 순서**만 정하고, threshold 조정 또는 수익성 개선을 승인하지 않는다.

코드 리뷰와 테스트가 통과해도 다음은 별도로 남는다: 영향받은 보고서의 새 세대 산출·원천 해시/strict handoff, 선택 release/실제 PID 소비, 신규 자연 완료 포지션의 명시적 판정·임계치 출처, 후행 관측창 완전성, 동일 모집단 비용 후 paired/holdout EV. 과거 `kt00007`의 `order_time`은 fill time이 아니며 소급 생성하지 않는다. full-population과 비용·관측 분모가 봉인되기 전에는 보고서의 `eligible_for_live_review`와 `cooldown_live_allowed`를 false로 유지한다.
