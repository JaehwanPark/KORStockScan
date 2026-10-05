# 다음 영업일 기동 잔여 작업·의미감시·Widget/Episode 개선 계획

작성일: 2026-10-05 KST. 대상 영업일: **2026-10-06**. §1–§5는 최초 읽기 전용 점검과 계획의 근거다. 이후 사용자 `계획을 실행하고 코드리뷰후 수정보완 반복` 지시로 구현·기존 원천 연구·표적 검증을 실행했다. 현재 결과와 잔여 작업은 **§6**을 따른다. 코드 검증과 실제 release/정책/PID 소비는 각각 수용한다.

실행 소유자는 [현재 체크리스트](../checklists/2026-10-05-stage2-todo-checklist.md)와 [10/6 기동 체크리스트](../checklists/2026-10-06-stage2-todo-checklist.md)다. 앞선 [기동 최종계획](next-session-machine-policy-application-and-startup-final-plan-2026-10-05.md), [비삼성 지정·적용 후 비교](non-samsung-designated-policy-and-postapply-comparison-implementation-plan-2026-10-05.md), [삼성 소비자 리뷰](../audits/samsung-tick-transition-forward-consumer-review-2026-10-05.md)를 보완한다. 이전 완료 기록을 다시 OPEN으로 만들지 않는다.

## 1. 계획 수립 시점의 상태와 기동 판단

[점검 원본](../../tmp/next-session-semantic-widget-episode-planning-20261005/inspection.json), [준비 전체 검증](../../tmp/next-session-semantic-widget-episode-planning-20261005/prepared_full_verify.json), [release-set](../../tmp/next-session-semantic-widget-episode-planning-20261005/release_set.json), [의미감시 재현](../../tmp/next-session-semantic-widget-episode-planning-20261005/machine-semantic-reproduction.json)에 실제 조회 결과와 source/code SHA를 보존한다. 관측 시각은 원본의 `as_of_kst`를 따른다.

| 대상 | 현재 직접 증거 | 아직 필요한 증거 |
|---|---|---|
| Main | 선택 release `designated-machine-policy-20261005-3d0e5106`, commit `3d0e5106f6a9ce708d1701835198da46d3a831c5`. 10/6 준비본 `current_full_contract` PASS, findings 0; 10/2 controller `done` | 10/6 당일 activation, bootstrap, 실제 Main PID와 자연 관측 |
| 비삼성 기계 | dated bundle `8fb91f19…`, machine `6b6fb204…`, `pullback_p60_v0`, `KRX|KRX_REGULAR`, `symbol_predicate=exclude_005930`. 원 정식 지정 binding PASS | 당일 current 전환·실제 action/activation receipt·고정 B0/C0 적용 후 비교 |
| 삼성 Main | 위 지정의 `exclude_005930` 경계로 기존 삼성 동작 보존. 신규 `absorption_p60_tick_shift1_v1`은 별도 동결 연구 후보 | 신규 소비자의 실제 이후 날짜 검증. 10/6 원 판정·완료 가격·체결 manifest 3경로 부재는 미래 원천 대기 |
| Widget 자동매매 | actual PID 3614517, `/proc` cwd와 unit 모두 별도 `e6d4d3b9` release. 10/6 dated auto-trade 정책 verified. loader는 3종목을 읽지만 실제 enabled는 삼성 KRX_REGULAR/NXT_PREMARKET 2세션 | 07:32 정책 반영·예정된 서비스 복귀, 10/6 startup/policy receipt, 당일 source·행동 확인 |
| Widget 확장 | `widget_symbol_runtime_policy_2026-10-06.json`은 observation_only. 034020/042660의 자동매매 세션은 `research_accumulation_incomplete` | 수집 정상과 주문 자격을 분리. 관측 전용 종목 전체를 매매 성공 대상으로 세지 않음 |
| Episode | 122개 service/preflight owner·366개 policy pin 정합 PASS, 모두 별도 `e6d4d3b9` 코드. unit 상태는 failed 61/inactive 61. 기존 applied/58개 ready authority는 **10/2 증거** | 10/6 applied 파일은 아직 없음. 당일 policy apply 후 profile별 preflight·authority·PID·자연 receipt. 61개 과거 실패의 사유·마지막 실행일을 먼저 분류 |

Episode의 기존 격리 3개는 `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday`다. 현재 비용 0.23% 재검증의 비양수 구간과 승인된 해제 조건이 기존 applied payload에 기록되어 있다. 현재 58/3을 다음날 가동 성공 수로 사용하지 않는다. 10/6 당일 loader로 전체 목록을 재분류한다.

**수립 당시 판단:** Main의 준비 계약은 통과했다. Widget의 dated 정책·별도 release pin도 확인했다. Episode의 당일 applied/기동과 모든 consumer의 미래 PID는 아직 수용 전이다. **20:10 이후 기존 자동 작업이 세대를 변경하여 이 준비 PASS의 현재 재사용 검증은 실패했다.** 최신 사유·인계는 §6.3을 따른다. 운영/stop/plan 결손과 신규 연구 원천 대기는 기동 증빙과 별도로 보고한다.

## 2. 정상 기동을 위한 잔여 실행계획

### 2.1 실행 순서와 종료 조건

| 우선순위·시점 | 작업·소유자 | 수용·실패 처리 |
|---|---|---|
| P0, 기동 전 | `SemanticPolicyCoverageRemediation1006`: §3의 지정 정책 오탐을 기존 감시 owner에서 수정·리뷰·표적 회귀 | 정상 designation은 mismatch 경보 0. 변조된 지정/비교/parent는 차단. 기존 실제 운영 경제성 결손은 그대로 표시 |
| P0, 10/6 07:20까지 최종 결정(관리 시각) | `DirectFamilyPreopenPolicyHandoff` 및 `WidgetEpisodeNextSessionStartup1006`: 최종 selector/독립 pin/dated 정책/hash·custody·미결 주문과 일정을 대조 | 기동 준비·명시 격리·복구 필요로 각각 분류. 07:20은 새 거래 guard나 승인 조건이 아니다 |
| 07:32 예정 owner apply | `korstockscan-symbol-owner-policy-auto-apply.timer` → 기존 standing-authority owner. Widget/Episode 예정 정책 반영 결과 확인 | 10/6 Episode applied 파일·정확 profile hash·격리 목록, Widget dated 정책과 stop/apply/restore terminal 확인. wrapper를 수동 실행해 점검하지 않음 |
| 07:35 Main PREOPEN | `DirectFamilyPreopenPolicyHandoff`: source10/2→target10/6, parent CAS·scope·operator designation·bootstrap accepted/rejected 대조 | 성공 시 dated activation 및 bootstrap/env readback. failed/pending은 정상 소비로 표기하지 않음 |
| 07:55 Main start, 08:05 수용 점검 | 같은 owner: 실제 PID/cwd·시작일·bundle/machine hash·heartbeat·자연 삼성/비삼성 관측 대조 | bundle `8fb91f19…`/machine `6b6fb204…`, 비삼성 recipe와 삼성 제외 경계 일치. 실제 정책 변경이 없다면 준비 재검증만으로 current를 강제로 쓰지 않음 |
| Widget 07:32 복귀 및 07:58 timer 이후, 08:05 점검 | `WidgetEpisodeNextSessionStartup1006`: 실제 PID의 당일 startup 및 loaded-policy digest를 예상 digest와 비교 | active·unit 설정·10/5 receipt만으로 성공 처리하지 않음. 삼성 2세션의 실제 권한과 034020/042660 관측 상태 구분 |
| Episode 각 profile의 예약 preflight·진입 창 | 같은 owner와 `EpisodeCaptureSequence1006`: 당일 applied→authority→unit/PID→원천 sequence·행동 receipt | 허용 profile 각각 확인. 격리·valid no-signal·source fail-closed·기동 실패·과거 실패를 다른 결과로 집계 |
| 10/6 원천 완료 후 장후 | `NonSamsungMachineForwardComparison1006`, `SamsungFrozenCandidateValidation1006`: 고정 후보 검증 및 아래 §3 연결 상태 점검 | 새 날짜 관측이 없는 경우 waiting/not_observed. 사용한 날짜로 재튜닝한 후보를 독립 검증 PASS로 표시하지 않음 |

07:32 owner wrapper는 active 주문 service를 일시 정지하고 적용 후 `start --no-block`으로 복귀시킨다. 따라서 07:58 timer가 이미 active인 service를 새로 띄운다고 가정하지 않는다. 예정 복귀의 terminal·PID·receipt를 확인하고, 복귀 실패 시 기존 custody/미결 주문·startup 복구 owner에서 처리한다.

기동 전 변경이 생기면 영향을 받은 코드/문서 review gate를 먼저 닫는다. selector, 정책, summary 또는 **준비 계약에 결속된 10/6 checklist**가 바뀐 경우 새 불변 세대에서 strict→controller→prepared를 다시 수용한다. 문서만 바뀌고 이 원천들이 그대로인 경우 기존 준비본의 원 날짜·hash를 검증하여 재사용한다. 단순 planning 수정으로 expensive 장후 재생을 실행하지 않는다.

### 2.2 기동 수용표

consumer별 `target_date`, expected/observed release·policy SHA, apply/preflight terminal, 실제 PID·시작 시각, source freshness, 자연 관측, 실제 제출/체결/terminal은 각각 기록한다. 정상 기동은 허용 consumer의 정확한 코드·정책 소비와 자연 기능으로 판단한다. 신호가 없거나 주문을 내지 않은 것만으로 기동 실패를 만들지 않는다. 실제 순수익은 완결 체결/청산과 비용 자료로 별도 계산한다.

원천/정책 불일치의 담당 경로와 실패 행/profile을 공개하고 해당 guard를 유지한다. 3개 경제성 격리, OFF 연구, retired 삼성 standalone gateway를 기동 복구 명목으로 활성화하지 않는다.

## 3. 의미감시 범위 점검 및 보완계획

### 3.1 기존 coverage와 발견한 차이

감시 범위는 `artifact_freshness`, `process_health`, Main `submission_bottleneck_monitor`, 장후 stage/strict/controller와 기존 notification 소비 경로다. 모든 감시기가 모든 역할을 수행해야 한다는 뜻은 아니다. 아래 표는 해당 owner 간 연결 여부를 점검한다.

| ID·우선순위 | 현재 coverage·실제 finding | 보완 대상·closure test |
|---|---|---|
| S1 P0 — 지정 정책 오탐 | `artifact_freshness._machine_result_semantics`는 일반 stage/pending/incumbent 승계와 비교한다. 실제 10/2 terminal의 `operator_designation_preserved`/proof `operator_designated`를 report의 `incumbent_carried`와 같은 값으로 요구해 `winrate_candidate_bundle_or_scope_mismatch` 발생. 정식 `entry_designated_policy.binding_valid`는 같은 root/bundle에서 True | proof schema별 정식 read-only validator로 분기. 지정 원 report·request·fixed pair·target·scope·parent CAS를 유지. 새 분기를 추가하고 일반 hash 검사를 생략하는 방식 금지. 정상 designation 및 지정 보존 PASS, 원 request/source/action 변조 FAIL |
| S2 P0 — 적용 후 비교 의미 | `postclose_summary_handoff`/지정 publisher는 새 계약을 알지만 감시기에는 fixed-pair 전용 비교 검증이 없다. 미래 `successor_selected`/carry의 실제 incumbent·challenger·post_apply/activation 의미가 일반 binding 검사만으로 충분한지 미입증 | `entry_designated_policy.validate_comparison_source` 등 정식 검증 재사용. B0/C0와 실제 P_t, latest/cumulative 승률·표본·미확정·처분을 표시. 후보가 이미 incumbent일 때 자기비교 금지, activation 없는 관측을 post_apply로 받지 않는 회귀 |
| S3 P0 — 휴장일/장전의 준비 감시 | 10/5는 로컬 거래일 calendar에서 휴장. `artifact_freshness.check`의 machine/aux/handoff 의미 검사는 `trading_day` 안에 있고, 휴장일에는 cancel-wait 예외만 검사한다. 10/2 봉인 장후 세대·10/6 prepared의 의미가 정규 휴장일 감시에서 빠짐 | as_of_date/source_date/target_date를 나눠 마지막 **완료·봉인 세대**와 다음 due target을 정식 index/receipt에서 선택. generic 날짜 추측 금지. 휴일/주말/자정/07:35 경계, future_due·대기·stale·contract invalid·과거 실패 분리 |
| S4 P1 — 삼성 고정 후보 실행 누락 | 신규 1틱 CLI/v2 계약은 구현·103 tests/519 대사 완료. 자동 stage/result registry·감시 연결은 없음. 10/6 source 3종 부재 | `SamsungFrozenCandidateValidation1006`에서 source-only 장후 연결. 원 source 준비 후 새 generation을 한 번 계산하고 terminal/status/index를 봉인. absent→waiting, excluded/valid-empty/evaluated/failed를 구분. 불변 frozen/code/candidate/date 분모 검사; 연구 waiting을 기동 정책 실패로 경보하지 않음 |
| S5 P1 — Widget 결과 의미 | handoff는 Widget stage의 terminal·artifact SHA를 검사한다. 실제 loader도 정책 자격을 검사한다. 감시 보고서에는 ready/carry/observe/source-gap·paired 미선정 원인·분모의 명시적 대사 연결이 부족 | auto-trade와 symbol expansion을 구분해 생성기/loader의 같은 version validator와 count census를 재사용. 신규 선정0·승계2·관측 전용을 구별. source 수와 replay 수, confirmed/미확정·candidate gate 사유·loaded hash를 소비. 정상 observation_only는 경보 제외 |
| S6 P1 — Episode 결과·기동 행렬 | handoff는 Episode stage/hash, release-set은 122 owner/366 pin을 검증한다. `process_health`의 삼성 morning/Widget 검사로 일반 61 profile의 당일 applied/preflight/PID/자연 receipt까지 대체할 수 없음 | 기존 일반 Episode owner에 profile별 expected due·apply/preflight·격리·source·PID·sequence→terminal 상태표 연결. 58 역사 ready나 failed61을 전부 현재 성공/장애로 계산하지 않음. 정책·authority·source의 다른 날짜/instance 재사용 차단 |
| S7 P1 — 신호부터 원천/청산까지 | Main 제출 병목 감시와 holding/quantity 의미 검사는 기존 별도 owner다. Widget/Episode의 비진입 유형·연속 원천·미결 custody/partial leg 대사를 Main counts로 대체할 수 없음 | 기존 family 사건과 execution-quality/owner registry/leg source에서 원 판정→미진입 이유→submit→fill→terminal/cost count를 각각 결속. guard 거부와 브로커 거절·미체결을 구분. 다른 owner/venue/date 혼합 금지 |
| S8 P1 — 알림 마지막 소비 | notifier `_semantic_source_matches`/`_alert_results`는 당일 source와 cancel-wait 이전일 예외, 4개 stage만 허용한다. 새 source-date 선택/연구/Widget/Episode 결과를 만들기만 하면 알림에 도달하지 않음 | 기존 필터에 등록된 의미 계약만 추가. stable fingerprint=(owner,source_date,target_date,scope,reason,generation). mock에서 경보/중복 억제/정상 회복/세대 전환·관측 불가를 확인. Telegram 실제 송신은 별도 자연 예약 증거로 판단 |

S1은 실제 선택 코드에서 재현한 결함이다. S2·S4·S5·S6·S7·S8은 새 계약/소비의 coverage 보완 사항이다. S3은 코드 조건과 calendar로 확인한 감시 사각이다. source gap 자체와 coverage 누락을 같은 장애 수로 합산하지 않는다.

재현의 다른 세 finding은 `compact_operating_rows_all_excluded`, `machine_operating_economics_incomplete`, `machine_operating_paired_unbound`다. S1을 고쳐도 이 실제 경제성·운영 원천 결손을 PASS로 바꾸지 않는다. 10/2 stage succeeded와 이 finding들은 동시에 성립한다.

### 3.2 구현 순서·위치·비용

1. S1/S2: 기존 `src/engine/error_detectors/artifact_freshness.py`에서 owner validator를 재사용한다. `src/tests/test_error_detector_artifact_freshness.py`에 정상 지정/적용 후 비교와 변조 반례를 추가한다.
2. S3/S8: 같은 감시 owner·`next_preopen_readiness`의 generation-only 읽기 및 기존 notifier를 사용한다. 완료 source 선택과 날짜 결속을 함께 보완하며 `src/tests/test_notify_error_detection_admin.py`의 mock으로 마지막 소비까지 검증한다.
3. S5/S6/S7: 기존 Widget/Episode report/loader/health owner에서 작은 bounded semantic projection을 만든다. 큰 report/grid를 정규 5분 감시마다 재생하지 않는다. projection은 source·producer version·report/code SHA·날짜·owner·분모·처분과 nullable 경제성만 결속한다. stable bounded read, 읽는 중 변경→unobservable, invalid→정확 owner finding을 유지한다.
4. S4: 기존 postclose stage owner 또는 같은 `src/engine/automation` 역할에서 source-only fixed candidate 소비를 연결한다. 체결·완료 가격 생산의 정확한 predecessor 뒤에서 실행한다. 원천 대기 deadline/한 날짜 한 generation/idempotency·동시 실행 lock을 명시하고 immutable candidate/v2 계약을 보존한다. 검증 결과를 운영 publisher나 Main bootstrap의 필수 신규 거래 허가로 연결하지 않는다.
5. 구현→review→보완→표적 regression→재리뷰, 물리 release·cron/unit 경로→자연 감시 receipt→notification mock/자연 소비 순으로 닫는다. 자동화 변경 때는 이 운영계획과 checklist를 같은 변경에 갱신한다. engine root에 새 Python 모듈을 만들지 않는다.

등록할 semantic projection의 지표 계약은 `metric_role=source_quality_gate` 또는 기존 family의 명시된 진단 역할, `decision_authority=report_only`, 정확 `window_policy`, 계약별 `sample_floor`, 원 owner의 `primary_decision_metric`, `source_quality_gate`, `forbidden_uses`를 포함한다. 숫자 부족은 hold_sample/미확정이며 원천 결손의 지표를 0으로 보정하지 않는다. 감시 지표로 주문·provider·threshold·custody·격리를 변경하지 않는다.

성능 수용은 같은 봉인 입력에서 변경 전후 정규 감시 wall/CPU/RSS와 결과 parity로 판단한다. 먼저 기준선을 측정하고 미해결 성능 증가가 있으면 중복 validator/파일 읽기를 줄인다. 의미 검증을 생략하거나 분석 모집단을 줄여 속도를 맞추지 않는다. 미래 삼성 replay는 실제 원천 생성 후 장후 1회에만 수행한다.

## 4. Main 개선 결과에서 도출한 Widget/Episode 개선 필요사항

### 4.1 공통으로 옮길 방법과 family 고유 계약

Main에서 유효했던 개선은 **모든 원 판정의 같은 모집단, 당시 feature, 반복 관측→독립 기회 정리, 비용 결속 결과, 확정/미도달/검열 분리, 고정 후보와 원 부모 비교, source→publisher→실제 소비 대사**다. 같은 방법을 각 family의 원 사건 이름과 기회 identity로 적용한다. Main `ENTER/BLOCK/RECHECK` enum·raw pressure 규칙을 다른 매매기의 입력에 만들어 넣지 않는다.

Main 신규 1틱 후보는 전체 origin 연구 권고이며 상시감시 전용 개선은 미입증이다. Widget의 삼성 실현 수익이나 Main의 전체 origin 승률을 다른 family의 정책 우월성 증거로 사용하지 않는다. 공통 feature가 실제 기록된 경우에만 읽고 absent/unknown을 별도 표시한다.

Main의 비용 결속 target-first 승률, Widget의 비용 후 완결 episode, Episode의 2-leg terminal은 다른 분모다. 각 family의 진단 승률과 기존 paired EV/net/custody 선정·publisher 계약을 병기한다. 승률 우선 목적을 다른 family의 실제 selector로 확대하는 변경은 별도 version 계약과 producer/loader migration으로 설계하며 이 문서로 자동 활성화하지 않는다.

### 4.2 Widget: 현재 막힌 원인과 수정 순서

10/2 자연 보고서는 statistically-ready 신규 세션 **0**, verified 기존 정책 승계 **2**다. 삼성 KRX_REGULAR paired study는 **`scale_in_runtime_trigger_source_missing`**이고 NXT_PREMARKET은 **`paired_outcome_incomplete`**다. source-quality PASS나 valid dated 정책만으로 새로운 후보를 평가했다고 볼 수 없다.

| 작업 | 기존 owner·필요한 보완 | 완료 기준 |
|---|---|---|
| W1 원천 census | `widget_paired_policy_replay.load_inputs`, `widget_signal_quality`: raw/승격 확인/ENTRY_READY·CAUTION/비진입/submit·fill을 같은 source 묶음으로 유지. 종목·venue/session·advisory generation·현재 input SHA·원 quote·중복/재시도 분리 | 실제 기록 수→정확 replay 수→행별 제외→독립 episode count 대사. 반복 confirmation을 독립 승리 표본으로 세지 않음 |
| W2 분할매수 재현 | `widget_paired_policy_replay.build_study`는 현재 add trigger가 있으면 후보 replay를 닫는다. 삼성 실제 정책은 초기 체결 대비 -80/-160bp add가 있음 | 보유 last-trade/BBO/leg fill·틱 절삭/실제 add guard·평균 체결가·target/terminal을 census. 정확히 재현 가능하면 기존 수량/add/exit를 고정한 replay 보완. 부족한 원천을 BBO만으로 대신하여 통과시키지 않음 |
| W3 간접 성공 보존 veto | `select_candidate`는 후보의 `profitable_close_within_180s_count >= baseline`을 필수 요구한다. 동일 성공 사건 100% 보존 규칙은 아니지만 **짧은 수익 종료 건수의 비감소 veto**임 | 개선 후보가 이 count 때문에 탈락하는 반례를 같은 입력에서 비교. count·lost winners는 diagnostic으로 옮기는 selector/consumer version 설계. source·비용·tail·custody guard의 별도 역할을 명시 |
| W4 미확정/평가 종료 | 기존 paired replay는 공통1200초 평가와 base/stress 비용을 사용하며 모든 pair 결과가 완결돼야 window_ready | 검열/결손/진짜 no_entry/완결 손실을 분리해 matched-comparable 및 전체 분모 민감도 병기. 전체 미확정을 해소하지 못했다고 연구까지 중지하지 않음. 1200초 평가 종료를 실제 강제 청산으로 바꾸지 않음 |
| W5 신호 유형 연구 | 기존 confirmation2/3 비교·entry timing·near-low/drawdown/VWAP/pressure 중 **실제 존재하는 source만** 사용 | 삼성/그 외 및 세션을 처음부터 분리. 원 raw 신호·승격 후 미진입·실제 진입의 확정 성공/실패 유형을 비교하고 하나의 변경 축만 동결 |

W3은 [10/3 전체 정책 조사](postclose-policy-winrate-objective-migration-plan-2026-10-03.md)의 ‘Widget 직접 성공 보존 게이트 없음’보다 구체적인 새 finding이다. 기존 조사 결과를 전체 무결함 증거로 반복하지 않는다. 최악 손실·capital_seconds 비악화 조건도 별도로 role을 확인하지만, 이 조건을 모두 성공 보존 veto로 분류하거나 계획만으로 제거하지 않는다.

### 4.3 Episode: 연구 진입과 실제 승격을 분리

10/2 실제 conditioned paired search의 61 profile 중 **45 valid_empty_no_fill /16 source_gap**, 연구 admitted **0**, calibration tested **0**, policy mutation **0**이었다. 이는 ‘모든 패턴을 계산했으나 개선0’이라는 결과가 아니다. 실제 체결 바닥/원천 gate 전에 연구 경로가 열리지 않은 집단이 있다. 반면 별도 expanded/prospective 연구 체인은 기존 `OFF/observe` 처분을 유지한다.

| 작업 | 기존 owner·필요한 보완 | 완료 기준 |
|---|---|---|
| E1 원천 sequence와 profile clock | `low_price_two_leg_tuning`/`EpisodeCaptureSequence1006`: 동일 timestamp의 sequence·prev hash·instance/PID·원 policy·watch/window를 결속 | 10/6 자연 source의 predecessor 확인. 같은 시각 전이를 중복 삭제하지 않으며 과거106 conflict를 정상으로 재라벨링하지 않음 |
| E2 미진입 기회 분석 | 기존 bar/quote·signal capture·durable raw에서 setup 관측/필터 거부/quote 결손/entry wait·cancel을 census | filled leg가 없어도 원천 충분한 **report-only 가격 패턴**은 비교 가능. 실제 8 completed-leg/5 source-day 승격 증거와 분리. OFF prospective chain을 복원하지 않음 |
| E3 profile 유형별 비교 | 동일 종목·profile 시간 창·원 가격 수준/틱당 비용·low proximity·drawdown 및 이미 있는 환경 receipt로 구분 | 삼성/그 외, venue/session별 fixed cohort. profile61 전체를 단일 평균으로 평가하지 않음. 작은 셀/환경 결손은 unknown이며 결과를 본 뒤 유리한 그룹만 holdout으로 선정하지 않음 |
| E4 정확한 두 leg 결과 | 기존 `low_price_two_leg_entry_spot_research`/policy runtime의 fills·target·carry와 completed-entry-cohort 계약 재사용 | 목표 선도달 진단과 완결 leg/episode 비용 후 승률·일별 net·paired EV를 각각 보고. partial/carry/manual terminal/quantity·capital gap을 0으로 넣지 않음 |
| E5 고정 후보·소비 일치 | 기존 등록 revision/holdout/실행 feasibility·capital·authority 계약 재사용 | 당시 incumbent와 다른 candidate identity, frozen source/kernel/cost, 소비한 날짜 ledger 일치. 적격이면 stage/apply/PID를 단계별 확인; 비교 불가/지원 부족은 사유와 실제 계산 범위 보고 |

Episode paired selector에서 명시적인 성공100%/80% 보존 veto는 이번 관련 경로 조사에서 찾지 못했다. 대신 terminal/custody·execution·capital·source/holdout 조건이 있다. 이것을 성공 보존율과 혼동해 해제하지 않는다. 기동 격리3개는 이번 연구 분류로 해제하지 않는다.

### 4.4 유한 연구 순서

`WidgetEpisodeMachineResearchContract1006`는 먼저 W1/W2/E1/E2의 기존 원천 가용성과 계산 경로를 확인한다. 필요한 feature가 기록되어 있지 않으면 해당 가설만 `not_identifiable`로 종료한다. 원천 확대를 이 단계의 해결책으로 전제하지 않는다.

가용성이 확인되면 기존 고정 정책/수량/add/exit를 대조군으로 두고 최대 **Widget 3개·Episode 3개**의 사전 정의만 검증한다: Widget 확인 횟수2↔3·원 신호 유형 필터·같은 setup의 당시 진입시각, Episode low-proximity/drawdown 유형·profile 시간대 유형·같은 setup의 진입시각이다. 기존 feature/정확 시각으로 표현할 수 있는 정의만 등록하며 서로 결합한 grid를 추가하지 않는다. 환경별 집계는 해석용으로 먼저 고정하고 별도 후보 개수로 위장하지 않는다.

학습 날짜에서 후보1개를 동결한 뒤 새 날짜에 검증한다. 지원수·승률·완결 결과·미확정·기회 손실·paired net/EV를 병기하고 성공100%/80% 또는 W3의 수익 건수 보존만으로 탈락시키는 새 규칙을 넣지 않는다. source/지원 부족, 측정된 개선 없음, 후보 동결 권고 중 하나로 종료한다. 운영 publisher 자격과 실제 경제성은 기존 family owner에서 별도 수용한다.

## 5. 소유·리뷰·최종 수용

| 소유자 | 범위 |
|---|---|
| `NextSessionSemanticWidgetEpisodePlanning1005` | 이번 점검·계획·링크/권한/owner/print-only parser 수용 |
| `SemanticPolicyCoverageRemediation1006` | S1–S3/S5–S8 구현과 기존 감시·알림 마지막 소비 검증. S4 실행 원천은 아래 삼성 owner에 인계 |
| `DirectFamilyPreopenPolicyHandoff` | Main10/6 실제 activation/bootstrap/PID |
| `WidgetEpisodeNextSessionStartup1006` | Widget/Episode07:32 반영 및 당일 profile별 기동 |
| `SamsungFrozenCandidateValidation1006` | S4 소비자 장후 연결·새 날짜 검증, 원 frozen/v2 계약 보존 |
| `NonSamsungMachineForwardComparison1006` | 비삼성 지정된 고정 pair의 적용 후 비교 |
| `WidgetEpisodeMachineResearchContract1006` | W/E 원천 census·간접 성공 veto 정리 설계·최대6가설·family별 지표/consumer 계약 보완. 실거래 승격 실행 권한은 별도 기존 owner |
| `EpisodeCaptureSequence1006` / `DirectFamilySourceRepairLowPriceTwoLeg` | Episode 자연 source sequence 및 운영/체결 원천 결손 |

계획 수립 review에서는 직접 증거/추론/제안, 당일/역사/future_due, source-quality/정책 선정/기동/순수익, OFF와 active profile, 독립 코드 pin과 Main selector를 대조했다. 당시 문서 검증은 link/단일 parsed owner/authority/보호 SHA/diff와 print-only parser로 종료했다. 이후 승인된 코드·기존 원천 연구 실행의 별도 결과는 아래에 기록한다.

문서 불일치도 남긴다. Plan Rebase §7의 entry decision 행에는 여전히 `80% winner retention` 설명이 있고, [10/3 목적 이관 계획](postclose-policy-winrate-objective-migration-plan-2026-10-03.md)은 이후 사용자 지시·새 기계/보조 계약에서 이 veto를 제거했다고 명시한다. 이번 신규 계획/현재 checklist는 사용자 지시와 새 계약을 따른다. 이전 설명을 신규 후보 탈락 조건으로 복원하지 않는다. Plan Rebase/README/runbook 등 baseline 문서의 갱신은 AGENTS의 명시 요청 조건에 따라 별도 문서 유지 작업으로 남기며 이번 계획 작성으로 baseline을 덮지 않는다.

후속 코드 실행은 `korstockscan-review-gate`의 구현→review→보완→재리뷰→영향 회귀를 따른다. 변경한 Python은 pytest/compile, wrapper는 bash -n/관련 계약을 검증한다. Kiwoom request/parser/WS 변경이 필요해지면 AGENTS의 공식 reference gate를 별도로 먼저 닫는다. 같은 원천 대기 상태를 반복 재생하거나 미래 기동/PnL을 완료로 표시하지 않는다.

## 6. 승인 후 실행 결과와 다음 액션

### 6.1 구현·리뷰 결과

[실행 리뷰](../audits/next-session-semantic-coverage-widget-episode-review-2026-10-05.md)와 [검증 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/validation.json)를 따른다. 새 모듈은 기존 `automation`, `error_detectors`, `monitoring` 역할에 배치했다. engine root에 새 Python 파일을 추가하지 않았다.

| 범위 | 구현·검증된 결과 | 자연 소비 잔여 |
|---|---|---|
| S1/S2 | 지정 proof와 fixed-pair의 native binding을 사용. 정상 지정 오탐 제거, parent/request/source/activation 변조 차단. B0/C0와 실제 P_t 구분 | 실제 이후 날짜 fixed-pair 보고서와 activation receipt |
| S3/S8 | calendar의 다음 due target과 실제 완료 controller/prepared source를 분리. 휴장일·자정·07:35 경계, source/target/generation별 알림과 중복·회복·관측 불가 mock 검증 | 설치된 감시 release의 자연 주기 및 알림 소비 |
| S4 | 원 v2 소비자 계약의 동일 bytes를 `data/runtime/research/samsung_tick_transition/consumer-contract-v2.json`에 보존. 기존 final-refresh의 machine_group 성공 뒤 optional source-only sidecar 연결. lock·입력 세대·immutable result/latest·실패 terminal·재사용 구현 | 현재 unit은 기존3d0e5106 release. 새 wrapper 설치와 실제10/6 이후 원천 생성. 현재 결과 `waiting_new_source_date` |
| S5/S7 | Widget/Episode producer에 report/policy/kernel SHA·분모·처분·leg/실행품질의 작은 봉인 projection 연결. 경제성 결손은 null. 기존10/2 보고서의 projection만 별도 생성 | 새 producer가 발행한 projection과 native report의 동일 세대 자연 소비 |
| S6/E1 | 61 profile의 당일 applied→예약 preflight→authority→실제 PID/cwd→persisted capture/sequence→terminal 행렬. source PID/date/policy·120초 관측 신선도 확인. 기존 raw에 있는 meta를 state에 복사 | 10/6 당일 applied와 자연 capture.120초는 감시 판정 예산이며 매매 guard/청산 조건을 변경하지 않음 |
| W1/W3/W4 | raw/중복/독립기회 census, 검열·comparable 분리. 새 Widget selector에서180초 수익 종료 건수 비감소 veto 제거. 이전 봉인 정책은 legacy validation으로만 검증 | 새 generation의 selector/loader 소비. 현재 dated 정책은 수정하지 않음 |
| W2/W5/E2–E5 | 정확 scale-in 입력 가용성 census와 사전 고정6가설의 report-only 연구. Episode 전체 진입 창의 유효 분봉 coverage 및 단일 날짜에 가짜 holdout을 만들지 않는 처리 | 아래 기존 원천 재결속·새 날짜 검증. source 없는 scale-in 경로를 합성하지 않음 |

생성 중인 family stage는 `unobservable`로 처리하고 기존 incident를 회복시키지 않는다. 완료 후에는 다시 봉인 원천을 검증한다. 감시 분기 추가로 실제 Main 운영 결손3finding은 제거되지 않았다. 원천·경제성·격리·custody·OFF·주문/수량/손절 guard는 별도 owner를 유지한다.

### 6.2 실제 보유 원천 연구 결과

[최종 연구](../../tmp/next-session-semantic-widget-episode-implementation-20261005/existing-source-research-v3/result.json)는 original report/source/kernel SHA와 사용한 보고서의 동일 bytes 사본을 봉인한 별도 산출물이다. 실제 체결 바닥을 report-only 연구 입구로 사용하지 않았으며 정책 publisher를 호출하지 않았다. v1/v2는 당시 세대의 역사 계산이며,20:43 자동 producer 완료 후 v3에서 현재 세대와 원본 보존을 함께 검증했다. 가설이나 모집단을 늘리지 않았다.

| 대상 | 실제 계산 | 결과·다음 판별 근거 |
|---|---|---|
| Widget 삼성 KRX_REGULAR | 현 수량/add/exit recipe를 고정하고 last-trade/initial·leg fill/틱 절삭 add/실제 add guard/평균 체결·terminal 가용성 census | `scale_in_runtime_trigger_source_missing`. 현 normalized replay input에서 exact 분할매수 경로 식별 불가. BBO로 대체하지 않음 |
| Widget 삼성 NXT_PREMARKET | 독립4기회. 학습3 중 comparable2·검열1, 마지막 역사 비교1은 검열. confirmation2↔3·ENTRY_READY 필터·1quote 지연을 base/stress로 계산 | 대조는 comparable 구간에서 완결 손실1·미진입1. base 비용 후 CF -16,003원, 기회 EV -0.30657088%. 확인 횟수/지연은 같은 결과. 필터는 그 손실을 피하지만 완결 진입0·승률 null·역사 비교 미확정. 운영 후보 미확보 |
| Widget 비삼성 | exact incumbent recipe가 존재하는 paired 연구 세션 없음 | 관측 전용 종목을 매매 정책 후보로 위장하지 않음 |
| Episode 비삼성61 profile | 실제3날짜의 native capture 검증.9/29 1,204건 모두 lineage-invalid 제외,9/30 valid-empty,10/2 1,178건 중1,072 valid·106 conflict 제외. 저장 bar가 있는58 profile에서3가설 계산 | **29 profile은 전체 진입 창 coverage 확보, 세 가설 모두 완결/held outcome0. 나머지29는 부분 창으로 `source_window_incomplete`; 3은 저장 bar 없음.**58개의 개선 실패나 승률0으로 합산하지 않음 |

Episode의 세 고정 정의는 low-proximity 절반, profile 창 앞 절반, 시작1분 지연이다. 완결 결과가 없으면 native EV와 확정 승률은 null이다. 부분 가격 창의 native 계산은 관측 prefix 진단으로만 표시하고 유효 정책 개선 비교로 받지 않는다.9/29 invalid와10/2 conflict를 정상 원천으로 재라벨링하지 않았다. 현재 Episode61개는 비삼성이며 retired 삼성 standalone chain을 복원하지 않았다.

### 6.3 기동 준비의 현재 잔여 gate

20:38 KST selected release cwd에서 native generation/full 재검증은 **FAIL**이었다. [준비·보호 증빙](../../tmp/next-session-semantic-widget-episode-implementation-20261005/current-readiness-and-protection.json)에 원 사유와 PID를 보존했다.20:10부터 기존 예약 job이 Widget source10/2와 Main/controller source10/5를 실행 중이다. Widget stage receipt가 `running`으로 바뀌어 `strict_stage_generation_stale:widget_policy` 및 읽기 세대 변경, full 검사에서는 tower/checklist/collector 세대 불일치도 표시한다. 이를 이번 projection 생성의 부작용으로 단정하지 않는다.

선택 release·Main current/dated·10/6 prepared index/receipt/checklist·10/2 controller/summary·원 frozen/v2·Widget dated·Episode candidate의 **12개 보호 SHA는 모두 동일**했다. 파일 동일성만으로 현재 원천 재검증 PASS를 주장하지 않는다. 진행 중 wrapper의 코드/입력·lock·서비스를 교체하지 않았고 새 매매 정책을 발행하지 않았다.

자동 작업 종료 후 `DirectFamilyPreopenPolicyHandoff`/`WidgetEpisodeNextSessionStartup1006`에서 실제 완료 source와 target10/6을 먼저 대사한다. 휴장일10/5 실행을10/2의 새 경제성 표본으로 사용하지 않는다. 최종 세대를 동결하여 summary/intake→strict→controller→prepared를 재수용하고,07:32 apply/restore·07:35 activation·실제 PID 수용을 각각 확인한다. 새 감시/producer/wrapper 코드의 배포·독립 pin 소비는 코드 검증과 별도 gate다. 현재 상태에서 다음 영업일 전체 정상 기동을 확정하지 않는다.

최신 관측: Widget 재생은20:43에 succeeded로 종료했다. 원 policy 파일을 다시 쓰지 않고 completed stage의 report SHA와 native loader PASS를 확인하여 작은 Widget projection만 현재 세대에 재결속했다. [재결속 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/widget-completed-projection-rebinding.json). 결과는 실제 scale-in source 결손 warning이며 세대 mismatch는 제거됐다. [20:53 native 재검증](../../tmp/next-session-semantic-widget-episode-implementation-20261005/post-widget-generation-readiness.json)은 여전히FAIL/12보호 SHA 동일이다. Main/controller source10/5는 계속 진행 중이다. Widget 종료만으로 전체 준비를 완료로 표시하지 않는다.

### 6.4 Widget/Episode 다음 액션

1. **Widget 정규장:** 이미 저장된 runtime signal·holding/leg/execution ledger에서 당시 initial fill·last-trade·-80/-160bp add의 틱 절삭·guard·owner/date/policy를 exact replay input에 연결 가능한지 먼저 확인한다. 연결되면 수량/add/exit를 유지한 같은3가설로 재계산한다. 결속 불가 필드는 `not_identifiable`로 종료하며 신규 API 수집을 전제하지 않는다.
2. **Episode:** 부분 창29개·bar 없음3개의 목록을 기준으로 보유 완료 분봉/collector cache와 capture의 symbol/date/clock/내용 SHA를 대사하여 기존 원천 소비를 보완한다. 같은 시각의 다른 policy/instance를 합치지 않는다. 전체 창 확보29개는 ‘세 정의에서 신호 미관측’으로 인계하고, 해당 source에서 이미 기록된 signal feature와 당시 policy가 재생 결과와 일치하는지 비교한다.
3. **새 날짜:**10/6 native sequence와 당시 고정 정책을 먼저 봉인한다. Widget2세션, Episodeprofile/창, 삼성 Main frozen, 비삼성 Main B0/C0를 각 owner에서 비교한다. 이번 동일 입력6가설은 종료하며 새 입력·식별 가능 feature가 없으면 grid를 늘리지 않는다. 운영 선정은 기존 family cost/custody/실행 계약에서 별도로 판단한다.


## 7. 10/5 야간 기동 준비 실행

사용자 다음 액션 실행 지시에 따라 검토된 전체 작업본을 통합 커밋·배포하고 마지막 완료 원천 `10/2 → 10/6`의 준비 계약을 다시 닫는다. 사용자는 봇이 내일 기동하므로 **지금 PID 소비 확인을 요구하지 않는다**고 명시했다. 오늘은 코드·설치 경로·dated 정책·예약 apply/preflight·strict/controller/prepared가 준비 수용 대상이다. 실제 apply/activation·PID·자연 행동은 기존 10/6 OPEN owner에서 수행하며 오늘 매매 프로세스를 기동하지 않는다.

### 7.1 발견한 휴장일 대기 결함과 보완

10/5 EOD는 `skipped_non_trading_day`, DB 완료 시세일은10/2였다. 그런데 기존 Main wrapper/controller가 source10/5의 succeeded를 기다렸고 Widget 예약 작업은 마지막 완료일10/2를 다시 발행했다. 공유 calendar 검증을 Main/Widget/final-refresh/controller 진입에 연결하여 휴장일 예약은 `[SKIP]`로 끝내고 정책/준비 발행을 시작하지 않도록 수정했다. canonical 날짜·calendar 오류는 fail closed이며 명시적인 유효 영업일의 원 날짜 복구는 유지한다. Main bot-stop보다 먼저 calendar가 검사된다.

[종료 전 원본](../../tmp/next-session-semantic-widget-episode-implementation-20261005/holiday-analysis-cancellation-preflight.json)에 cmdline/start-ticks·EOD 원본·bot action을 보존하고 확인한 휴장일 분석 worker만 SIGTERM으로 종료했다. 실제 매매 service에는 start/restart를 실행하지 않는다. 불변 실행 snapshot을 수정하지 않으며 휴장일 중단을 경제성 DONE으로 바꾸지 않는다. 세대 정리 중 machine final-refresh **분석 timer**만 일시 정지하고 검토된 설치 경로에서 원 예약을 복귀한다.

### 7.2 기존 원천 재결속의 종료 결과

[bounded census](../../tmp/next-session-semantic-widget-episode-implementation-20261005/existing-source-rebinding-census.json)는9/29·9/30·10/2 Widget 삼성 event journal과10/2 저장 cache9개를 SHA로 봉인했다. 당시 일부 주문·체결·liquidity/velocity guard는 존재하나 정규장 분할매수의 연속 last-trade/initial/add/guard 전체 경로는 식별할 수 없다. Episode와 겹치는 cache는 KRX_REGULAR/기본 symbol 요청 경로이며 live Episode의 SOR `_AL` 완료 분봉과 다르다. 해당 기간의 native Episode ka10080 cache도 없다. 이 자료로 SOR 결손·3격리를 대체하지 않는다. 같은6가설은 기존 계산 결과와 source gap을 유지하고10/6의 실제 새 원천으로 인계한다.

### 7.3 배포·최종 수용 순서

1. 휴장일 wrapper/native controller·선택 release router·family 정책·의미감시·알림의 표적 회귀, compile/bash-n/diff 및 print-only parser를 닫는다.
2. 전체 검토 코드의 불변 release를 선택하고 Widget/Episode live·preflight·auto-expansion·07:32 apply 및 장후 분석의 **설정만** 새 코드에 결속한다. native 정책 pin/custody/미결 주문/격리/guard는 유지한다. 기존 selector와 managed drop-in bytes를 rollback 원본으로 보존한다.
3. current generation에서 결손/stale로 판정된 producer만 재생한다. summary→tower/checklist→strict `require-summary-handoff`→전체 controller→10/6 prepared를 동결된 최종 세대에서 수용한다. 단순 코드 이전으로 원 경제성 표본이나 새 정책 개선을 주장하지 않는다.
4. Main 삼성 제외·비삼성 지정 recipe, Widget 삼성2세션/타 종목 observation, Episode native10/6 apply 계획58 carry/3 quarantine·timer·preflight 소유를 확인한다. native 계획 검증은 아직 apply 실행이 아니다. 미래 PID·실제 원천/경제성은 오늘 준비 gate에서 제외한다.

최종 결과는 [기동 준비 실행 증거](../../tmp/next-session-semantic-widget-episode-implementation-20261005/next-session-final-preparation.json)에 기록한다. 이 문단은 절차이며 실제 PASS는 해당 파일의 native 검증 결과로만 수용한다.
