# Scalp-sim 안전 제거 상세 작업계획서

작성: `2026-09-15 KST`

상태: **구현 전 계획**
목표: 현재 `scalp-sim` 코드 중 효용이 끝났거나 중복된 부분을 제거하되, 메인봇·위젯·에피소드의 주문·보유·청산·custody와 현재 장후/PREOPEN 계약을 손상시키지 않는다.

이 문서는 제거 구현, 배포, 서비스 재기동 또는 자연 운영 검증 receipt가 아니다. 이 문서의 작성·열람·리뷰만으로 코드 삭제, runtime env 변경, 매매 프로세스 재기동 또는 과거 산출물 삭제를 실행하지 않는다.

## 1. 결론과 권고 범위

현재 `scalp-sim`은 하나의 독립 프로그램이 아니라 다음 세 층으로 구성돼 있다.

| 층 | 현재 역할 | 제거 판단 |
| --- | --- | --- |
| 퇴역 호환층 | overnight wrapper/report, scale-in window approval의 retired marker와 구 schema 호환 | **1차 제거 대상**. 소비자를 `lifecycle.retirement`의 단일 tombstone 계약으로 옮긴 뒤 삭제 |
| 장후 sim policy control-tower | rising-missed 등 source-only 관찰 결과를 sim policy catalog로 투영하고 postclose/PREOPEN/verifier에 전달 | **2차 제거 대상**. 현재 live 주문 권한은 없지만 장후·PREOPEN consumer가 많아 일괄 계약 이관 필요 |
| main 내부 base live simulator | BUY 신호 가상 체결, virtual holding/exit, AI budget, entry-price·post-sell·scale-in 관찰과 real/sim 격리 | **이번 안전 제거 범위에서 유지**. 메인 프로세스 내부 경로라 제거하면 main telemetry·분모·source-quality 계약이 변함 |

권고 구현 범위는 **퇴역 호환층과 장후 sim policy control-tower 제거까지**다. 이 범위는 실제 주문 판단값, 주문 제출, 위젯·에피소드 신호·수량·target·보조청산을 변경하지 않는다. base live simulator 제거는 별도 성능·표본 대체 설계와 사용자 지시가 필요한 후속 과제로 둔다.

## 2. 현재 효용과 제거 이유

### 2.1 유지할 효용

base live simulator는 다음 source-only 기능을 제공한다.

1. 실제 budget·latency·broker submit 이전의 BUY 신호를 `signal_inclusive_best_ask_v1` 가상 체결로 보존한다.
2. entry price candidate의 quote touch/timeout, holding/exit의 MFE·MAE와 opportunity cost, AVG_DOWN/PYRAMID 후보를 real과 분리해 관찰한다.
3. `simulation_book=scalp_ai_buy_all`, `actual_order_submitted=false`, `broker_order_forbidden=true` provenance를 통해 가상행이 실제 주문·실현손익 분모에 섞이지 않게 한다.
4. sim holding의 OpenAI 호출 폭증을 제한하는 `scalp_sim_ai_budget_manager`를 제공한다. 이 budget은 sim 대상만 제어하며 real holding 판단·provider route·BUY threshold·broker guard를 변경할 권한이 없다.

이 기능은 경제적 승인 근거가 아니라 연구 표본과 오염 방지 장치다. 제거하려면 해당 분모를 없애는 것이 허용되는지와 대체 source가 있는지를 먼저 결정해야 한다.

### 2.2 제거할 이유

퇴역 호환층은 이미 실제 producer 기능이 없다.

- `deploy/run_scalp_sim_overnight_preclose.sh`는 retired marker만 출력한다.
- `src/engine/scalp_sim_scale_in_window_approval.py`는 `retired_status(...)`만 반환한다.
- overnight·scale-in family는 `src.engine.lifecycle.retirement`에서 퇴역 상태를 소유한다.

장후 sim policy control-tower는 runtime effect와 broker authority가 없고, 최근 자연 산출물도 승인 정책 0건·`sim_policy_candidate_missing`이었다. 그런데 main postclose wrapper는 기본 ON으로 두 번 실행하고 PREOPEN·verifier·control-tower·workorder가 산출물 존재와 schema를 계속 다룬다. 현재 증분 효용에 비해 실행시간·artifact·검증·유지보수 표면이 크므로, 관련 계약을 원자적으로 제거하는 편이 낫다.

## 3. 절대 보존 경계

다음은 이름에 `sim`이 들어가더라도 이번 제거 범위가 아니다.

### 3.1 메인봇 runtime

- `src/engine/sniper_state_handlers.py`의 `SCALP_SIMULATION_BOOK`, enable/fill policy, virtual position 생성·복원·persist, holding/exit 및 sim AI budget 분기
- `src/engine/kiwoom_sniper_v2.py`의 runtime simulation target 식별과 broker submit 격리
- `src/engine/ai_engine_openai.py`의 simulation/observation-only authority 처리
- `src/engine/sniper_scale_in.py`의 sim/probe provenance와 real order 분리
- `src/engine/sniper_post_sell_feedback.py`의 sim candidate/evaluation 분리
- `src/engine/scalp_sim_ev_midcheck.py`의 현재 base simulator EV·분모 분석
- `src/engine/scalping/sim_source_quality.py`의 synthetic/invalid sim 판별
- `src/engine/lifecycle_decision_matrix.py` 중 현행 base sim/real 분리와 generic historical reader
- `src/utils/constants.py`와 `src/utils/threshold_cycle_registry.py` 중 base simulator·candidate-window·AI-budget·entry-price·post-sell에 사용되는 현행 상수와 stage mapping

이 경로는 실주문을 만들지 않지만 메인 process 안에서 실행된다. 단순 삭제는 main event 처리, state 복원, source-quality, threshold report 분모를 바꾸므로 “메인봇 영향 없음” 조건을 충족하지 않는다.

### 3.2 위젯·에피소드 runtime

다음 소유권은 변경하지 않는다.

- `src/trading/widget_auto_trade/**`
- `src/trading/samsung_*_one_share/**`
- `src/trading/low_price_two_leg/**`
- `src/trading/order/**`
- machine entry adverse, target ratchet, profit stagnation, rebound re-entry, market weakness 정책과 loader
- order owner registry, custody ledger, broker/account/order guard, manual exclusion

현재 위젯·에피소드 실제 서비스의 실행 모듈에는 `scalp_sim` 직접 참조가 없다. 공통 필드인 `actual_order_submitted`, `broker_order_forbidden`, `runtime_effect`, `simulation_book`은 다른 source-only 정책에서도 사용하므로 삭제하거나 의미를 바꾸지 않는다.

### 3.3 운영 데이터와 이력

기존 `data/runtime/scalp_live_simulator_state.json`, 과거 pipeline event, report, policy catalog, approval artifact는 구현 과정에서 삭제하지 않는다. 새 producer 중단과 과거 증거 보존은 별개다. 보존기간·압축·archive 삭제는 별도 데이터 retention 작업으로 다룬다.

## 4. 목표 상태

제거 완료 후 다음 조건을 만족해야 한다.

1. main runtime의 base scalp simulator와 real/sim 격리 동작은 변경 전과 같다.
2. 위젯·에피소드 서비스의 source file, systemd unit, drop-in, env, policy hash, 주문/custody 경로는 변경되지 않는다.
3. postclose wrapper는 retired overnight와 `scalp_sim_auto_approval_control_tower`를 실행하지 않는다.
4. PREOPEN은 제거된 family의 artifact를 읽거나 `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_*`, `KORSTOCKSCAN_SCALP_SIM_SCALE_IN_*` env를 생성하지 않는다.
5. verifier와 tuning tower는 제거된 artifact 부재를 실패·source gap·구현 추천으로 보고하지 않는다.
6. daily report·workorder·lineage는 과거 row를 읽을 수 있지만 새 scalp-sim control-tower 산출물을 요구하지 않는다.
7. 퇴역 상태의 canonical owner는 `src.engine.lifecycle.retirement` 한 곳이다.
8. source/test/docs 전체 검색에서 제거된 module 실행·import·필수 artifact 참조가 0건이다. 과거 audit·workorder 본문의 역사적 문자열은 변경하지 않는다.
9. postclose/PREOPEN targeted test와 main real/sim isolation test가 통과한다.
10. 코드 검토 완료, 배포, 자연 postclose, 다음 PREOPEN/PID는 각각 별도 상태로 보고한다.

## 5. 작업 단위와 의존 순서

| WP | 목적 | 선행 | 완료 산출물 |
| --- | --- | --- | --- |
| WP0 | 현재 generation·의존성·권한 고정 | 없음 | source/import/artifact/consumer census |
| WP1 | 퇴역 overnight·scale-in 호환층 정리 | WP0 | 단일 retirement tombstone, dead code 삭제 |
| WP2 | 장후 sim control-tower consumer 계약 제거 | WP0 | PREOPEN/verifier/report/tower의 무의존 상태 |
| WP3 | producer·wrapper·registry 제거 | WP2 | control-tower module과 postclose 실행 제거 |
| WP4 | 테스트·문서·검색 잔존 정리 | WP1~WP3 | targeted tests와 참조 census PASS |
| WP5 | 통합 리뷰·배포 후보·자연 acceptance handoff | WP4 | review finding 0, 검증 receipt, 안전한 배포 계획 |

WP2를 먼저 끝내고 WP3 producer를 제거한다. producer부터 삭제하면 PREOPEN/verifier가 필수 artifact missing으로 실패할 수 있다. WP1은 독립 구현할 수 있지만 `threshold_cycle_preopen_apply.py`, verifier, retirement helper와 겹치는 변경은 WP2와 한 사람이 통합한다.

WP 번호는 구현 분할 단위이며 native recommendation ID나 새 checklist stable ID가 아니다. 실제 실행일에는 현재 체크리스트의 기존 code-improvement owner에 결속하고, 기존 owner가 없을 때만 checklist 규칙에 맞는 단일 handoff를 만든다.

## 6. WP0 — 현재 계약과 증거 고정

### 6.1 사전 확인

1. Plan Rebase §1~§8, 실행일 체크리스트 목적·강제 규칙, review gate를 다시 읽는다.
2. `git status --short`로 사용자/자동화 변경을 보존하고 scalp-sim 변경 파일과 겹치는 수정이 있는지 확인한다.
3. `data/runtime/runtime_release_selection.json`, 실제 main PID의 cwd/commit, postclose router `--print-plan`, PREOPEN `--print-plan`을 읽기 전용으로 고정한다.
4. widget/episode unit의 최종 `ExecStart`, `WorkingDirectory`, 현재 PID, policy drop-in을 기록한다. 이 정보는 변경 대상이 아니라 비영향 비교 기준이다.
5. main/postclose/PREOPEN worker가 실행 중이면 source나 canonical artifact를 변경하지 않는다.

### 6.2 의존성 census

다음 범주를 별도로 기록한다.

- Python import: module import, function/path helper import, package exposure
- wrapper/cron/systemd: 직접 실행, flag, marker, artifact wait
- PREOPEN: loader, selector, family/env prefix, manifest, provenance hash
- postclose verifier: required path, schema check, selected-family check, summary projection
- report/workorder/tower: source status, headline, recommendation trigger
- tests: 현행 동작 검증, retirement 호환 검증, 역사적 fixture
- docs: 현재 운영 계약과 과거 감사 기록

표준 검색은 `src`, `deploy`, `docs`, `src/tests`로 제한하고 `data`, `logs`, archive의 대형 원천을 전체 검색하지 않는다. 과거 audit/workorder 본문은 source code 의존성이 아니므로 별도 historical bucket으로 둔다.

### 6.3 기준 artifact

제거 전 마지막 자연 generation의 다음 path/hash/status를 보존한다.

- `data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_<SOURCE_DATE>.json`
- `data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_<SOURCE_DATE>.json`
- `data/threshold_cycle/approvals/scalp_sim_scale_in_window_expansion_<SOURCE_DATE>.json`이 존재하는 경우
- postclose verification, tuning performance control tower, PREOPEN apply plan/runtime manifest
- `data/runtime/scalp_live_simulator_state.json`의 schema/owner/hash/mtime. active positions 내용은 변경하지 않는다.

완료조건: 삭제 대상과 유지 대상이 파일·symbol·consumer별로 분리되고, 제거 후 비교할 main/widget/episode runtime 기준점이 확보된다.

## 7. WP1 — 퇴역 overnight·scale-in 호환층 제거

### 7.1 제거 후보

- `deploy/run_scalp_sim_overnight_preclose.sh`
- `src/engine/scalp_sim_overnight.py`
- `src/engine/scalp_sim_scale_in_window_approval.py`
- 전용 테스트 중 삭제된 구현을 직접 import/실행하는 부분
  - `src/tests/test_scalp_sim_overnight_gatekeeper.py`
  - `src/tests/test_scalp_sim_overnight_report.py`
  - `src/tests/test_threshold_cycle_wrappers.py`의 no-op wrapper 확인
  - `src/tests/test_threshold_cycle_preopen_apply.py`의 scale-in approval producer fixture

파일은 consumer가 정리된 같은 commit에서만 삭제한다. 과거 report schema를 읽는 generic parser와 historic fixture는 현재 reader 호환에 필요하면 유지한다.

### 7.2 consumer 보완

1. `src/engine/verify_threshold_cycle_postclose_chain.py`는 overnight source-quality를 로컬 helper로 중복 구성하지 않고 `lifecycle.retirement`의 canonical retired view를 사용한다. 최종 목표가 historical field 자체 제거라면 verifier output schema migration을 명시한다.
2. `src/engine/threshold_cycle_preopen_apply.py`의 scale-in approval loader/selector/env prefix/manifest projection을 제거한다. 단순 missing artifact block으로 바꾸지 않는다.
3. `src/engine/scalping/scalp_sim_auto_approval_control_tower.py`가 scale-in approval path를 import하는 결합을 먼저 제거한다. WP2에서 control-tower 전체를 삭제하더라도 WP1 단독 commit이 유효해야 한다.
4. `src/utils/threshold_cycle_registry.py`의 `scalp_sim_scale_in_window_expansion` mapping을 제거하고 retired-prefix scrub이 과거 env를 제거하는지 유지한다.
5. `src/engine/daily_threshold_cycle_report.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/sniper_state_handlers.py`에 남은 overnight label은 다음처럼 판정한다.
   - 현재 자연 event 생성 코드이면 제거
   - 과거 artifact read/migration 전용이면 `historical_read_only` 경계로 이동하거나 유지
   - live action/threshold로 연결될 가능성이 있으면 fail-closed test 후 제거
6. `src/engine/build_code_improvement_workorder.py`가 삭제된 module을 수정 후보로 추천하지 않게 한다.

### 7.3 회귀검증

- PREOPEN 입력에 과거 scale-in artifact가 있어도 family/env가 선택되지 않는다.
- artifact가 없어도 PREOPEN과 postclose verifier가 정상 동작한다.
- retired env prefix는 기존 scrub 단계에서 제거된다.
- historical overnight row는 real PnL이나 live family로 승격되지 않는다.
- main base simulator test는 변경 전과 동일하게 통과한다.

완료조건: 삭제 module의 non-historical import/실행 0건, 제거된 family/env 생성 0건, retirement canonical owner 1개다.

## 8. WP2 — 장후 sim control-tower consumer 계약 제거

### 8.1 PREOPEN

주 대상은 `src/engine/threshold_cycle_preopen_apply.py`다.

1. 다음 import와 generator provenance 결속을 제거한다.
   - `scalp_sim_auto_approval_path`
   - `scalp_sim_policy_catalog_path`
   - `scalp_sim_auto_approval_control_tower.__file__`
2. `_load_scalp_sim_auto_approval`, `_select_scalp_sim_auto_approval` 및 전용 validation을 제거한다.
3. family/env prefix, selected-family merge, apply manifest, runtime evidence projection에서 `scalp_sim_auto_approval`을 제거한다.
4. 과거 runtime env에 남은 `KORSTOCKSCAN_SCALP_SIM_AUTO_POLICY_*`는 새 정책으로 carry하지 않고 existing retirement scrub에서 제거한다.
5. 같은 stage의 현행 `scalp_sim_candidate_window_expansion`과 `scalp_sim_ai_budget_manager`는 유지한다. 이름 prefix가 비슷하다는 이유로 함께 제거하지 않는다.

### 8.2 postclose verifier

주 대상은 `src/engine/verify_threshold_cycle_postclose_chain.py`다.

1. `scalp_sim_policy_catalog` required path와 schema 검증을 제거한다.
2. due active seed가 `scalp_sim_auto_approval` selection을 요구하는 규칙을 제거하거나 rising-missed의 현행 source-only owner로 되돌린다.
3. 제거 artifact 부재를 failure/warning/source-generation mismatch로 만들지 않는다.
4. 과거 verifier JSON을 읽는 code가 있으면 schema-versioned compatibility read만 유지한다.
5. latest strict verifier는 제거 이후 생성된 source set/hash만 검증하며 과거 catalog hash를 요구하지 않는다.

### 8.3 요약·workorder·lineage

다음은 직접 catalog/control-tower 참조가 확인된 consumer다. WP0 census에서 해당 symbol이 current path인지 historical compatibility인지 다시 판정한 뒤 active source/status/recommendation만 제거한다.

- `src/engine/automation/tuning_performance_control_tower.py`
- `src/engine/automation/key_lineage_ledger.py`
- `src/engine/automation/ldm_hypothesis_discovery.py`
- `src/engine/scalping/rising_missed_selection_prior.py`
- `src/engine/monitoring/limit_down_watch_report.py`
- `src/engine/lifecycle_bucket_discovery.py`의 control-tower 전용 path/helper가 다른 현행 consumer를 잃는 경우

`src/engine/daily_threshold_cycle_report.py`와 `src/engine/build_code_improvement_workorder.py`는 현재 확인된 overnight historical label/module 추천을 WP1에서 정리한다. WP0에서 control-tower 직접 참조가 추가로 확인되지 않으면 WP2에서 수정하지 않는다.

각 consumer는 다음 세 경우로 분류한다.

| 참조 목적 | 변경 |
| --- | --- |
| 제거 artifact 존재/신선도/성공을 요구 | 참조 제거 |
| 제거 artifact로 live family/env를 선택 | selection 제거 및 retired scrub 확인 |
| 과거 보고서의 출처를 표시 | historical compatibility로 유지 가능 |
| rising-missed source 자체를 소비 | control-tower를 경유하지 않는 현재 source-only owner로 유지 |
| base simulator event를 분석 | 유지 |

완료조건: producer를 아직 삭제하지 않은 상태에서도 PREOPEN/postclose 결과가 control-tower artifact 유무에 의존하지 않는다.

## 9. WP3 — producer·wrapper 제거

### 9.1 postclose wrapper

`deploy/run_threshold_cycle_postclose.sh`에서 다음을 제거한다.

- `THRESHOLD_CYCLE_RUN_SCALP_SIM_AUTO_APPROVAL_CONTROL_TOWER` 기본 flag
- 첫 번째 `scalp_sim_auto_approval_control_tower` 실행과 artifact wait
- rising-missed 이후 `scalp_sim_auto_approval_control_tower_prior_refresh` 재실행과 wait
- 최종 DONE marker의 해당 flag projection

wrapper가 기존 선택 release를 통해 실행되므로, 실행 중인 postclose chain을 변경하지 않는다. wrapper 수정은 새 release에만 포함하고 chain terminal 이후 안전한 구간에서 선택한다.

### 9.2 source module

consumer 제거가 검증된 후 다음을 삭제한다.

- `src/engine/scalping/scalp_sim_auto_approval_control_tower.py`
- `src/tests/test_scalp_sim_auto_approval_control_tower.py`
- control-tower producer 전용 fixture/helper

`rising_missed_classifier_prior`, lifecycle source-only observation, base simulator는 삭제하지 않는다. control-tower가 source를 읽었다는 이유만으로 upstream producer를 함께 퇴역시키지 않는다.

### 9.3 cron/systemd

설치 cron이 `run_threshold_cycle_postclose.sh`만 호출한다면 별도 cron 삭제는 없다. 독립 scalp-sim cron이 발견되면 다음 순서로 처리한다.

1. 설치값과 source installer를 함께 확인한다.
2. 현재 실행 중 PID/lock 0을 확인한다.
3. source installer에서 제거하고 generated crontab diff를 검토한다.
4. 별도 설치 권한이 있는 실행에서만 crontab을 갱신한다.

위젯·에피소드 systemd unit과 collector/trader는 변경·재기동하지 않는다.

완료조건: 새 postclose run에서 제거 producer가 시작되지 않고, artifact 부재 상태로 wrapper·verifier·controller가 정상 terminal이 된다.

## 10. WP4 — 테스트·문서·잔존 참조 정리

### 10.1 유지할 핵심 테스트

- `src/tests/test_scalp_live_simulator.py`
- `src/tests/test_openai_live_sim_ai_budget.py`
- `src/tests/test_post_sell_feedback.py`의 base sim/real 분리
- real/sim/probe classification 및 `actual_order_submitted=false` 보존 테스트
- main order submit path가 sim target을 broker에 보내지 않는 테스트
- widget/episode service import와 정책 테스트

### 10.2 제거·전환할 테스트

- 삭제 producer의 정상 artifact 생성 테스트는 제거한다.
- no-op wrapper가 존재한다는 테스트는 “wrapper/reference가 없음” 검사로 전환하거나 source-wide 잔존 검색으로 대체한다.
- PREOPEN control-tower selection 성공 fixture는 제거한다.
- missing control-tower artifact가 실패라는 fixture는 제거하고, artifact 무관성을 검증한다.
- historical artifact parser fixture는 실제 호환 consumer가 남을 때만 유지한다.

### 10.3 문서

현재 owner 문서만 갱신한다.

- `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- `docs/time-based-operations-runbook.md`
- `docs/report-based-automation-traceability.md`
- `docs/postclose-tuning-result-review-task-instructions.md`
- 필요 시 `docs/intraday-monitoring-task-instructions.md`

과거 checklist, audit report, code-improvement workorder는 당시 증거이므로 대량 수정하지 않는다. 현행 문서에서 “surviving scalp-sim”이라는 표현은 base simulator/candidate-window/AI-budget/post-sell만 가리키도록 좁힌다. 제거된 control-tower/overnight/scale-in family를 현재 필수 owner로 남기지 않는다.

### 10.4 잔존 검색 acceptance

다음 결과를 분류해 active 참조 0을 확인한다.

```bash
rg -n 'scalp_sim_overnight|scalp_sim_scale_in_window_approval|scalp_sim_auto_approval_control_tower|scalp_sim_policy_catalog' src deploy docs --glob '!docs/audit-reports/**' --glob '!docs/code-improvement-workorders/**'
```

허용 잔존은 명시적 retirement migration과 이 계획서의 역사 설명뿐이다. source import, wrapper 실행, required artifact, PREOPEN family/env mapping, current runbook owner가 남아 있으면 완료가 아니다.

## 11. Targeted validation

구현 파일에 따라 정확한 subset을 확정하되 최소 범위는 다음과 같다.

```bash
PYTHONPATH=. .venv/bin/python -m pytest \
  src/tests/test_adm_ldm_retirement.py \
  src/tests/test_threshold_cycle_preopen_apply.py \
  src/tests/test_verify_threshold_cycle_postclose_chain.py \
  src/tests/test_tuning_performance_control_tower.py \
  src/tests/test_daily_threshold_cycle_report.py \
  src/tests/test_scalp_live_simulator.py \
  src/tests/test_openai_live_sim_ai_budget.py \
  src/tests/test_post_sell_feedback.py \
  src/tests/test_threshold_cycle_wrappers.py
```

실제 test filename이 다르면 WP0에서 현재 owner를 확인해 치환한다. 존재하지 않는 테스트를 새 필수 계약으로 만들지 않는다.

추가 검증:

```bash
PYTHONPATH=. .venv/bin/python -m compileall -q src/engine src/utils
bash -n deploy/run_threshold_cycle_postclose.sh
git diff --check
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
```

필수 반례:

1. control-tower artifact 없음, 과거 artifact만 있음, invalid artifact가 남아 있음
2. 과거 PREOPEN env에 제거 prefix가 있음
3. base simulator enabled/disabled, state 없음/빈 state/active state 복원
4. real SCALPING position과 `scalp_ai_buy_all` sim position이 동시에 존재
5. sim AI budget exhaustion이 real AI holding 판단에 영향을 주지 않음
6. widget/episode BUY·SELL fixture가 scalp-sim artifact 없이 동일 결과를 냄
7. postclose wrapper가 removal 이후 DONE이고 verifier가 removed source를 요구하지 않음
8. historical report row가 live selection이나 real PnL로 승격되지 않음

Provider 호출, 실주문, 실제 취소, threshold 변경, trading service 재기동은 이 검증에 필요하지 않다.

## 12. 리뷰 기준

각 WP는 다음 루프를 따른다.

`구현 → self review → producer/consumer review → finding 보완 → 재리뷰 → targeted validation`

리뷰는 최소 다음을 확인한다.

- 삭제 module의 숨은 import·CLI·wrapper·test·artifact path
- missing artifact가 silent success 또는 반대로 false failure를 만드는지
- 과거 env/family가 PREOPEN manifest에 carry되는지
- real/sim/probe 분모와 PnL가 섞이는지
- main/widget/episode/manual custody와 order owner가 변하는지
- `broker_order_forbidden`, `actual_order_submitted`, hard safety가 약화되는지
- selected release와 workspace 차이를 무시하고 배포 완료로 오인하는지
- code removal과 자연 postclose/PREOPEN acceptance를 합치는지

P0~P2 finding이 남아 있으면 다음 WP나 배포로 진행하지 않는다. P3 문서 표현은 직접 owner·권한 오해를 만들 때만 배포 blocker로 올린다.

## 13. 커밋·배포·재기동 계획

권장 commit 경계는 다음과 같다.

1. `retire: remove obsolete scalp sim overnight compatibility`
2. `refactor: remove scalp sim postclose policy control tower`
3. `docs: align scalp sim retirement contracts`

실제 커밋에서는 다른 세션의 변경을 포함하지 않는다. 단계별 commit이 각각 testable하지 않으면 WP1과 WP2~WP3를 두 개의 원자적 commit으로 합친다.

배포는 다음 조건을 모두 충족한 뒤 별도 상태로 수행한다.

- review finding 0
- targeted validation PASS
- 현재 postclose/PREOPEN/main consumer가 실행 중이지 않은 안전한 전환 구간
- clean release root와 검토 commit 일치
- rollback release와 선택 원장 백업 확인
- 다음 예약이 읽을 wrapper/PREOPEN/verifier가 같은 commit에 존재

이번 제거는 main base simulator와 widget/episode trading code를 바꾸지 않으므로 정상적으로는 매매 서비스 재기동이 필요하지 않다. 공통 selected release 교체가 다음 main PID에 적용되는지는 별도 receipt로 확인한다. 이미 실행 중인 main/widget/episode PID가 코드 교체 없이 계속 동작해도 제거 작업의 코드 검증과 모순되지 않는다.

배포 후 acceptance는 다음 순서다.

1. `postclose --print-plan`, `preopen --print-plan`의 root/commit/command 확인
2. 다음 자연 postclose에서 제거 stage 미실행과 wrapper/verifier/controller terminal 확인
3. 다음 PREOPEN에서 제거 family/env 0건과 retired scrub 확인
4. 다음 main PID의 root/commit과 base simulator provenance 보존 확인
5. widget/episode unit/PID/policy hash가 변경 전 기준과 동일한지 확인

자연 postclose 또는 PREOPEN이 아직 도래하지 않았으면 `code_review_closed / deployment_complete / natural_acceptance_pending`으로 분리한다.

## 14. 롤백

롤백 기준:

- postclose verifier가 제거 artifact missing 때문에 실패
- PREOPEN이 제거 family/env를 계속 요구하거나 manifest 보존식이 깨짐
- base simulator state 복원·real/sim 분리 test 또는 자연 receipt가 회귀
- main real order path의 action/authority가 변경
- widget/episode service root·policy·주문/custody 결과가 의도치 않게 변경

롤백은 검증된 이전 release를 selector로 복원하는 방식으로 수행한다. 과거 artifact를 새로 합성하거나 빈 JSON을 만들어 verifier를 통과시키지 않는다. 진행 중 wrapper/PID를 중간 교체하지 않고, 실행 중 주문·보유·custody를 보존한다. 롤백 뒤에도 실패 source-date와 새/이전 commit, artifact hash, 실제 PID root를 기록한다.

## 15. 완료 판정과 보고 형식

| 구분 | 완료 조건 |
| --- | --- |
| 코드 제거 | WP1~WP4 구현, active 참조 0, finding 0, targeted validation PASS |
| 배포 | 선택 release가 검토 commit을 가리키고 plan 경로가 일치 |
| 자연 장후 | 제거 stage 미실행, postclose/verifier/controller 성공 terminal |
| 자연 PREOPEN | 제거 family/env 0, current family 정상 선택/차단, runtime verify 성공 |
| main 비영향 | real/sim 격리, base simulator state/provenance, actual broker path 회귀 없음 |
| widget/episode 비영향 | unit/PID/policy/custody/order behavior에 변경 없음 |
| 경제성 | 이번 제거의 필수 완료조건이 아님. 운영시간·artifact 감소는 별도 측정 |

최종 보고는 `판정 → 제거 범위 → finding과 보완 → validation → commit/배포 → 자연 acceptance → 잔여` 순서로 작성한다. 다음 값을 포함한다.

- 제거/유지 파일과 이유
- source date/as-of, old/new commit과 release root
- postclose/PREOPEN consumer 변경 목록
- active reference census 결과
- targeted test·compile·shell·parser·diff 결과
- selected release와 실제 PID 소비 상태
- main/widget/episode 비영향 근거
- 과거 artifact 보존 상태
- base simulator 제거를 하지 않은 이유와 별도 후속 조건

코드 삭제 완료를 운영 효율 개선이나 비용 후 수익 증가로 확대하지 않는다.

## 16. 일괄 구현 요청 문구

후속 구현 시 다음 문장으로 본 계획의 안전 제거 범위를 실행할 수 있다.

> `scalp-sim 안전 제거 상세 작업계획서`의 WP0~WP5를 순서대로 실행하라. base live simulator와 main real/sim 격리, 위젯·에피소드 매매·custody·정책은 유지하고, 퇴역 overnight·scale-in 호환층과 장후 sim policy control-tower만 제거하라. consumer를 먼저 이관한 뒤 producer를 삭제하고, 각 WP마다 구현→코드리뷰→finding 보완→재리뷰→targeted validation을 반복하라. 다른 작업 변경을 포함하지 말고, 코드 검증·배포·자연 postclose·PREOPEN/PID 소비를 별도 상태로 보고하라. 사용자 승인 없이 매매 서비스 재기동, 실주문·취소, runtime env 수동 변경, threshold/provider/order guard 변경 또는 과거 artifact 삭제를 하지 마라.
