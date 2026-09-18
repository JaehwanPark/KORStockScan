# Claude Scalping Pattern Lab·automation 완전 폐기 계획

작성일: 2026-09-18 KST

상태: PLR0–PLR6 구현·반복 리뷰/수정·검증·커밋/push·선택 배포·불필요 산출물 삭제 완료. [최종 검증](../audit-reports/2026-09-18-claude-scalping-pattern-lab-retirement-review.md)을 따른다. 장후 전체 chain FAIL·자연 PID/정책 적용·경제성 확인은 별도 기존 OPEN이며 폐기 완료로 대체하지 않는다.

## 1. 목적과 제거 후 상태

`analysis/claude_scalping_pattern_lab`과 `src.engine.scalping_pattern_lab_automation`의 독립 분석·후보·작업지시 계통을 폐기한다. 실행을 OFF로만 전환하거나 빈 보고서를 계속 생성하는 방식으로 남기지 않는다. 전용 producer, 실행 진입점, 소비·복구·감사 계약과 불필요한 누적 산출물을 함께 제거한다.

제거 후 Main 장후작업은 기존 기계·compact evaluator와 개별 전략/주문 튜너를 사용한다. 과거 Lab의 존재나 파일 부재가 missing/stale/source-gap, 후보, 구현 지시, 새 일정 또는 복구 명령을 생성하지 않아야 한다. 현재 매매정책·적용 버전·경제성 원천과 guard는 보존한다. Lab의 삭제를 EV 개선이나 구조적 원천 결손 전체 해결로 보고하지 않는다.

계획 원칙은 [Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), 현재 실행 owner는 [9/18 checklist](../checklists/2026-09-18-stage2-todo-checklist.md)를 따른다. 장후 절차 문서를 인용하는 것은 그 절차의 실행이 아니다.

## 2. 확인된 근거와 경계

- 현재 Main wrapper는 cancel-wait 이후 조건부 Claude Lab과 기본 ON automation을 실행한다. Swing 분기는 operator OFF다. 별도 `run_tuning_monitoring_postclose.sh`에는 override로 Lab을 다시 실행하는 경로가 남아 있다.
- Lab의 `run_all.sh`는 prepare → 패턴 집계 → payload 빌드다. `scalping_pattern_lab_automation`은 결과를 기존 family 입력·설계 후보·개선 지시로 변환한다. 두 작업의 직접 매매정책 적용 권한은 없다.
- 9/17 원 실행 세대에서 검증된 완료 거래는 3건·순익 70원이며 적용 profile은 없다. 증분 EV는 null이다. 설계 후보 2개와 작업지시 8개는 경제성 승격 결과가 아니다.
- 기본 작업본 outputs는 9/9 세대이고 9/17 실행 보고서는 stepwise worktree outputs를 참조한다. 날짜·realpath·hash를 확인하지 않은 삭제나 최신성 판단을 금지한다.
- currentness/AI review/propagation 모듈에는 Swing 계약도 있다. `analysis/tuning_observability_summary.py`는 퇴역 Gemini 코드에도 사용된다. 이름이 비슷하다는 이유로 이들 공유 기능이나 다른 Lab 전체를 삭제하지 않는다.

근거: [Main wrapper](../../deploy/run_threshold_cycle_postclose.sh), [보조 monitoring wrapper](../../deploy/run_tuning_monitoring_postclose.sh), [삭제·검증 receipt](../audit-reports/2026-09-18-claude-scalping-pattern-lab-retirement-review.md), [active inventory](../audit-reports/2026-09-05-postclose-work-inventory.md).

## 3. 보존 대상

다음은 Lab 제거 범위가 아니다.

- 공유 raw pipeline, monitor snapshot/DB, Parquet/DuckDB, 원 request/response, AI 판단 원천·라벨, order owner/receipt, broker order/fill/terminal, custody/보유·reserve 원장.
- `main_lifecycle_journal`, `main_lifecycle_paired`, 비용·symbol master·운영 청산/실행 모델·모델 holdout과 실제 완료 손익.
- 현행 기계·compact evaluator, Daily/calibration/독립 후보 holdout, entry-price·entry-split·scale-in-split·cancel-wait·scanner·position sizing 등 기존 owner의 기능과 정책.
- `score65_74_recovery_probe` 등 Lab이 매핑한 기존 family 자체, 공용 `score_recovery_economics`/observation. Lab의 매핑·provenance만 제거하며 family 일괄 퇴역이나 threshold 변경을 하지 않는다.
- `observation_source_quality_audit`, 공용 AI provider/config/retry/response 처리와 다른 endpoint의 schema. Lab reviewer가 이 원천을 읽었다는 이유로 원천 또는 공용 안전 검사를 제거하지 않는다.
- separately approved operator override/expiry, 수량·budget·custody·broker·stale/conflict·hard/protect/emergency guard.
- 실행 중 worktree/release와 현재 selected release, rollback 근거 및 적용 중 policy/PREOPEN의 필수 hash 참조. 기존 immutable release의 파일을 직접 삭제하지 않는다.

Swing/DeepSeek와 퇴역 Gemini의 독립 코드 폐기는 이번 목적에 포함하지 않는다. Swing OFF와 Gemini 자동 실행 퇴역 상태를 유지하고 Claude 제거를 이유로 새 실행이나 source 요구를 만들지 않는다.

## 4. 제거·수정 대상 지도

### 4.1 직접 producer와 실행 진입점

| 대상 | 처리 | 완료 조건 |
| --- | --- | --- |
| `analysis/claude_scalping_pattern_lab/` | 코드·config·prompts·README·전용 outputs 제거 | import/CLI/직접 shell 실행 경로 없음 |
| `src/engine/scalping_pattern_lab_automation.py` | 모듈 제거 | 공용 consumer가 삭제 모듈을 import하지 않음 |
| `deploy/run_claude_scalping_pattern_lab_cron.sh` | 전용 wrapper 제거 | cron/문서/installer에 실행 참조 없음 |
| `deploy/run_threshold_cycle_postclose.sh` | Lab·automation 호출/대기/resource hook, 전용 flag/provider/시작일/marker와 후행 Lab 리뷰 refresh 제거 | Main 실행계획에 퇴역 단계 없음; 나머지 단계 순서·guard 유지 |
| `deploy/run_tuning_monitoring_postclose.sh` | override 실행과 전용 변수/`flock` 전달·상태 기록 제거 | 옛 `TUNING_MONITORING_RUN_PATTERN_LABS=true`도 Lab을 실행하지 못함 |
| `deploy/install_pattern_lab_cron.sh` | cleanup shim의 Claude 참조와 현재 crontab 상태 점검 | 옛 marker/경로가 남지 않음; installer가 새 Lab job을 설치하지 않음 |

`install_pattern_lab_cron.sh`는 현재 설치기가 아니라 옛 Claude/Gemini weekly cron을 지우는 shim이다. 잔존 cron을 정리할 필요가 있으면 먼저 정확한 marker/명령만 제거하고 unrelated cron byte를 보존한다. Gemini cleanup 역할이 실제로 남으면 공유 shim을 보존하고 Claude 실행 경로는 제거한다. shim 자체가 더 이상 호출되지 않고 필요도 없을 때만 삭제한다. cron 변경은 구현 실행 시 승인 범위에 포함되는지 확인하며 계획 작성 단계에서는 수행하지 않는다.

### 4.2 전용 후행 감사·AI 리뷰와 공유 코드

| 대상 | Main 제거 범위 | 공유 기능 보존 규칙 |
| --- | --- | --- |
| `pattern_lab_currentness_audit.py` | Claude path/schema/hash/freshness/feedback 검사·workorder와 Main 단계 | 기존 Swing caller가 있으면 같은 모듈의 Swing 부분만 유지; Claude를 필수 입력으로 읽지 않음 |
| `pattern_lab_ai_review.py` | scalping Lab source, Main initial/reentry/provenance refresh, 전용 queue·provider 요구 | 기존 Swing 기능에 필요한 부분만 유지; Main 공용 source-quality 검사 자체는 보존 |
| `pattern_lab_propagation_audit.py` | scalping automation import·전파 검사와 Main bootstrap/final refresh | Swing 소비 계약을 보존할 경우 삭제 모듈 import 제거 후 정상 import·실행 검증 |
| `automation/pattern_lab_source_contract.py` | Claude 피드백 전용 경로·요구 | 비퇴역 caller의 실제 필요가 있으면 유지; caller 없는 코드만 삭제 |
| `analysis/tuning_observability_summary.py` | Claude output/consumer·Lab 전용 작업지시 요구 | Gemini/다른 caller의 공유 계산은 유지; 퇴역 Claude 경로를 요구하지 않음 |
| `ai_response_contracts.py` 및 endpoint config | 폐기 reviewer의 독점 schema/config만 제거 | Swing reviewer가 유지되면 사용하는 schema도 유지. 공용 AI 계약은 보존 |

공유 모듈은 구현 시 import·CLI caller 지도로 최종 판정한다. 다른 기존 caller가 없으면 모듈과 전용 테스트를 삭제한다. caller가 있으면 그 scope만 보존하고 Main에서 스케줄·복구·freshness 요구가 없게 한다. 이 판정은 제거 누락을 허용하는 유예가 아니다. 모든 잔존 모듈에는 비-Claude caller와 보존 이유를 남긴다. 새 서비스·producer·wrapper·이름만 바꾼 Lab을 만들지 않는다.

### 4.3 소비자 전체 제거 체크포인트

| 소비자/계통 | 제거할 계약 |
| --- | --- |
| `threshold_cycle_ev_report.py` | 삭제 automation import, report loader·Lab summary·source path·warnings·Markdown, Main 감사/review/propagation 입력 |
| `runtime_approval_summary.py` | fallback report 검색, Lab 상태/source/경고·승인 triage·출력. 다른 정책 승인 기능은 보존 |
| `build_code_improvement_workorder.py` | Lab source bundle·후보/매핑·instrumentation 판정·implemented provenance·maintenance review·fingerprint·re-intake |
| `build_codex_daily_workorder.py` | Lab 보고서 링크·이전 작업지시를 계속 구현하라는 안내 |
| `build_next_stage2_checklist.py` | 이전 workorder/summary에서 퇴역 Lab owner·조사 일정을 전이하는 경로. literal 참조가 없어도 실제 입력 테스트로 검증 |
| `automation/tuning_performance_control_tower.py` | Lab source 수·상태·blocker·목적 미완료·Markdown |
| `automation/automation_chain_trigger_decision.py` | Main의 감사/review/propagation input/output·stage flags·source missing/mtime trigger |
| `automation/automation_chain_slimming_audit.py` | 폐기 Main 단계의 inventory·실행 기대·중복/미실행 경고 |
| `verify_threshold_cycle_postclose_chain.py` | 폐기 artifact path/load/source-link/stale-generation/material hash/리뷰 요구/disabled flag 계약. 비퇴역 verifier 검사에는 영향 없음 |
| `automation/postclose_done_controller.py` | Lab stale 경고를 이유로 currentness/propagation/reviewer 재실행하는 recovery command와 retry branch |
| `error_detectors/artifact_freshness.py`, `monitoring/error_detector_coverage.py` | scalping automation 및 Main 전용 감사 freshness registry·expected coverage·false missing 경고 |
| 공용 postclose summary/finalization/recommendation intake·PREOPEN reader | report/source/目的 queue를 간접 소비하는 계약. 직접 literal이 없어도 실제 정책/요약 입력 경로 검증 |
| engine location gate·관련 테스트 | 제거 모듈 allowlist와 전용 테스트를 정리. 공용 테스트 전체를 삭제하지 않음 |

`pattern_lab*` 문자열 전부 삭제를 목표로 하지 않는다. Swing, 퇴역 판정, 역사 증거는 허용된다. 활성 Claude/scalping Lab의 import·실행·입력 요구·선정·복구가 0인지가 완료 조건이다. `scalp_entry_action_decision_matrix.py`처럼 이미 퇴역한 모듈의 설명 문자열은 활성 소비자로 세지 않으며 이 기회에 퇴역 코드를 복원/재작성하지 않는다.

## 5. 기존 작업지시의 처리

Lab이 남긴 8개를 새 OPEN으로 모두 이관하지 않는다. 6개의 `implemented`는 주로 report/provenance 구현이며 경제성 완료가 아니다. budget/overbought 설계 후보도 자동 이관하지 않는다.

- 재현된 미해결 수량·identity 결함이 있고 기존 owner의 근거가 있으면 해당 owner의 기존 stable ID에 근거·closure test만 합친다. 이미 완료됐거나 기존 주문 튜너가 소유하면 중복 지시는 종료한다.
- 차단 건수, outcome별 집계, 연결되지 않은 budget/submission 통계만으로 만들어진 지시는 `superseded_by_lab_retirement`로 정리하며 새 family나 튜너를 만들지 않는다.
- 현재 shared workorder의 `orders`, `non_selected_orders`, 목적/다음행동·lineage·전이 대상 모두에서 퇴역 source의 지시가 재등장하지 않게 한다.
- 같은 order ID를 다른 활성 producer가 사용하면 `source_report_type`/source identity/lineage로 판단한다. `order_*latency*` 같은 광범위 prefix나 기존 family 이름으로 일괄 삭제하지 않는다.
- 과거 workorder/checklist를 새 generation으로 읽었을 때에도 Lab 지시가 다시 살아나지 않는 회귀를 둔다. 기존 retirement 도구가 역할에 맞으면 재사용하고 새 퇴역 DB/ledger/상시 producer는 만들지 않는다.

## 6. 누적 과거 산출물 삭제

### 6.1 현재 경로별 규모

9/18 계획 수립 시 파일 메타데이터 기준이다. raw 내용이나 DB를 전수 재스캔하지 않았다. 실행 시 변동·링크·추가 사본을 다시 확인한다.

| 경로 | 파일 수 | bytes | 기본 처리 |
| --- | ---: | ---: | --- |
| `analysis/claude_scalping_pattern_lab/outputs/` | 13 | 590,161 | 보호 참조가 없는 전용 파생물 삭제 |
| `data/report/scalping_pattern_lab_automation/` | 149 | 2,887,928 | 전용 과거 JSON/MD·미사용 locks 삭제 |
| `data/report/pattern_lab_currentness_audit/` | 149 | 964,283 | 혼합 scope/보호 참조 판정 후 Main 불필요 산출물 삭제 |
| `data/report/pattern_lab_ai_review/` | 173 | 2,023,824 | Main 전용 report/response/history/budget·미사용 locks 삭제; 공유/보호 근거는 별도 판정 |
| `data/report/pattern_lab_propagation_audit/` | 146 | 902,988 | Main 불필요 산출물 삭제; 공유/보호 근거는 별도 판정 |

전용 두 경로는 162개·3,478,089bytes, 공유 감사/리뷰 계통은 568개·3,891,095bytes다. 합계 730개·7,369,184bytes(약 7.03MiB)는 **조사 범위 규모**이며 확정 삭제량이 아니다. `data/pattern_lab/`는 현재 없다. 전용 이름의 logs도 이번 제한 조회에서는 발견되지 않았다.

추가 조사 경로는 기존 stepwise worktree의 Lab outputs, 관련 tmp/cache/quarantine/archive 내 전용 사본, 전용 cron logs다. `tmp`·archive·runtime release 전체를 지우지 않고 알려진 전용 경로/manifest에서만 좁혀 확인한다. 과거 worktree 폐기는 해당 세션·프로세스가 사용하지 않는 경우에만 별도 단위로 수행한다.

### 6.2 삭제 순서와 보호 계약

1. 실행 시 선택된 release/활성 프로세스 cwd·명령, source generation, 현재 정책/PREOPEN/rollback receipt를 고정한다. 다른 세션의 dirty 변경과 실행 중 source를 보존한다.
2. 후보 파일의 path/realpath/size/SHA/종류·삭제 근거를 작은 cleanup manifest로 기록한다. 현재 소비·hash 참조를 확인하고 `delete / preserve / deferred_active_use`로 나눈다. symlink는 target을 임의 따라가며 삭제하지 않는다.
3. 소비자 수리와 회귀 통과를 먼저 완료한다. 운영 경로의 산출물 삭제 전에 검증된 successor가 미래 장후 invocation을 소유하고, 옛 wrapper/consumer가 해당 파일을 사용하지 않음을 확인한다. 승인된 source-only 실행만으로는 현재 배포 consumer의 의존성이 해제되지 않는다. 배포 승인이 없거나 기존 실행이 계속 사용하면 운영 파일 삭제는 유예하고 정확한 참조·해제 조건을 보고한다. 현재 공용 summary/workorder에 제거 계통이 남아 있으면 승인된 제한 재생성으로 미래 consumer 요구를 끊는다.
4. 참조가 없는 Lab 전용 CSV/JSON/payload/MD, 누적 전용 보고서·캐시·중단 잔여를 삭제한다. Git tracked 파일은 관련 diff로 관리하고 ignored/untracked 파일도 manifest에 포함한다. 생략된 과거 산출물을 무조건 대량 아카이브로 복제하지 않는다.
5. 비용·주문·보유·실적·적용 정책이나 retained release의 재현/hash 증거에 필요한 파일은 보존한다. 사유·참조 owner·해제 closure를 기록한다. 과거 signed policy/source bundle을 고쳐 참조를 지우거나 무효 hash를 PASS로 처리하지 않는다.
6. 사용 중 lock은 삭제하지 않는다. zero-byte lock도 활성 holder 확인 후 처리한다. 선택된/실행 중 immutable release는 직접 수정하지 않으며 불필요한 release 사본 정리는 전체 release 단위의 기존 관리 규칙으로 처리한다.
7. receipt에 실제 삭제 수·bytes, 보호 목록, 실패/유예와 보호 원천 SHA 불변을 남긴다. 전용 경로 삭제 후 기존 consumer가 빈 파일 생성·archive fallback·glob/latest 검색으로 계통을 복원하지 않는지 검증한다.

공유 Daily/EV/runtime summary/workorder·과거 체크리스트 전체를 Lab 이름이 들어 있다는 이유로 삭제하지 않는다. 새 공용 generation에서는 Lab 부분을 제거하고, 필요한 과거 근거는 당시 generation 그대로 남긴다. 남은 역사 파일은 활성 입력 요구가 되어서는 안 된다.

## 7. 실행 단계와 검증

| 단계 | 수행 내용 | 종료 기준 |
| --- | --- | --- |
| PLR0 | 활성 호출·import·소비·복구·공유 caller 지도, cleanup manifest와 정책/원천 freeze | 모든 발견 경로에 delete/patch/preserve 판정과 owner 있음 |
| PLR1 | Main/보조 wrapper와 전용 cron 진입점 제거 | 기존 true env, 누락 파일, 과거 outputs가 있어도 재실행 0 |
| PLR2 | EV/summary/workorder/checklist/trigger/controller/detector 소비 계약 제거; 공유 Swing 분리 | 삭제 모듈 없이 import·Main 계획·후행 생성 정상, Lab missing/stale/복구 0 |
| PLR3 | 두 직접 producer와 전용 코드/테스트 삭제; 고아 shared 코드 판정 | 실제 삭제 + 잔존 공유 caller 근거. 이름만 바꾼 replacement 없음 |
| PLR4 | 실제 파이프라인 회귀와 self-review → 보완 → 재리뷰 | 활성 정책/안전 guard 불변, 과거 입력 재섭취 차단, 영향 범위 검증 통과 |
| PLR5 | 필요한 운영 문서/현재 owner 정리 및 승인된 successor·제한 공용 결과 갱신 | source/push/selected release/dated result 증거를 분리; 옛 운영 consumer의 의존성이 해제됨 |
| PLR6 | cleanup manifest대로 불필요 누적 파일 삭제와 삭제 후 consumer 검증 | 실제 receipt·보호 SHA 불변·재생성 없음; 자연 PID/손익은 별도 |

### 7.1 의미 있는 회귀

기존 테스트 파일에서 영향 계약만 보완하고, 제거한 알고리즘 자체를 새 테스트로 재현하지 않는다.

- **파일 없음:** Lab 코드/outputs/reports가 없는 상태에서 Main EV→workorder→runtime summary→tower→checklist→verifier/controller 경로가 Lab 입력을 요구하지 않는다.
- **오래된 파일 있음:** 9/17 과거 automation/workorder와 임의 양수 Lab 결과를 넣어도 후보·source intake·새 OPEN·Codex 지시·정책 승격으로 소비하지 않는다. 보호된 이전 체크리스트의 독립 owner는 보존한다.
- **복구 경로:** 과거 Lab stale/material-generation 경고가 입력에 남아도 controller가 삭제 CLI를 호출하지 않는다. 동시에 실제 활성 source/summary hash 실패는 기존대로 차단한다. verifier를 일괄 느슨하게 만들어 통과시키지 않는다.
- **옛 실행 설정:** `THRESHOLD_CYCLE_RUN_PATTERN_LABS=true`, `TUNING_MONITORING_RUN_PATTERN_LABS=true` 및 기존 Lab 감사/reviewer true flag가 삭제 producer·provider 호출을 되살리지 않는다. 다른 reviewer/provider 설정은 유지한다.
- **공유 기능:** 보존된 Swing 모듈이 scalping 삭제 모듈 없이 import되고, OFF 상태에서 Main 필수 artifact가 되지 않는다. 공유 observability/Gemini caller의 기존 계약도 삭제된 Claude 입력을 요구하지 않는다.
- **매매정책 보존:** 기존 기계/compact 및 주문 튜너의 지원 입력 계산·dated policy·Daily/PREOPEN/장중 loader 회귀를 영향 범위에 맞게 재사용한다. Lab 삭제 때문에 후보, 수량, budget, custody, override/guard가 바뀌지 않는다.
- **삭제 이후:** 공용 산출물 generation의 source list/lineage에는 활성 Lab 경로가 없고, cleanup 대상 경로는 재생성되지 않는다. 과거 보호 증거의 hash는 유지한다.

기존 관련 테스트는 `test_threshold_cycle_wrappers`, `test_threshold_cycle_ev_report`, `test_runtime_approval_summary`, `test_build_code_improvement_workorder`, `test_build_next_stage2_checklist`, `test_automation_chain_trigger_decision`, `test_automation_chain_slimming_audit`, `test_postclose_done_controller`, `test_verify_threshold_cycle_postclose_chain`, `test_tuning_performance_control_tower`, `test_error_detector_coverage`, `test_engine_location_gate`를 중심으로 선택한다. 공유 리뷰 모듈을 보존하면 해당 currentness/AI-review/integrity/propagation 테스트도 남은 scope로 검증한다. 직접 Lab prepare/net/automation 전용 테스트는 producer 삭제와 함께 정리한다.

Python은 관련 pytest·수정 모듈 compile/import, wrapper는 `bash -n`과 기존 계약 테스트, 변경 전체는 `git diff --check`를 사용한다. 문서는 링크·owner·권한과 print-only parser만 검사한다. 패키지 설치, broker/provider 실호출, 전수 raw scan, 전체 grid/전체 장후 재실행, 대규모 성능검사는 필요 없다. 실제 pytest 범위와 결과는 구현 receipt에 기록하며 계획의 목록을 이미 통과한 것으로 보고하지 않는다.

### 7.2 운영 문서와 제한 결과 갱신

- owning traceability/runbook와 active inventory에서 #67/#69와 Main 전용 #71/#72/#93 및 후행 refresh 요구를 퇴역 처리한다. 번호를 다른 작업에 재사용하지 않는다.
- current checklist의 실제 Lab OPEN/목적 전이만 정리하고 재현된 독립 결함은 기존 stable ID로 귀속한다. 과거 완료 체크리스트를 일괄 재작성하지 않는다. 새 복원 OPEN이나 daily empty Lab task를 만들지 않는다.
- baseline README/Rebase/prompt/AGENTS 수정은 명시적으로 승인된 문서 범위에 한정한다. 이번 계획 작성에서는 수정하지 않는다. automation 구현 시 운영 문서/checklist 동시 정합성이 필요하다.
- 이번 계획의 근거 링크를 포함해 현재 문서가 삭제 예정 파생물을 참조하면 최종 cleanup/review receipt로 근거 링크를 교체한다. 파일을 삭제한 뒤 현재 운영 문서에 필수 링크가 깨진 채로 두지 않는다. 역사 signed artifact의 원 hash/내용은 바꾸지 않는다.
- 재생성이 승인되면 고정된 원천 날짜에서 공유 EV/workorder/runtime summary/tower/checklist 및 필요한 마지막 consumer만 갱신한다. 수정된 producer/consumer의 의존 순서를 실제 코드에서 확인하고 기존 handoff/fixed-point 계약을 따른다. 원천 불변의 개별 튜닝·grid·provider 계산을 반복하지 않는다.
- 다음 적용일 정책은 기존 독립 owner가 준비한 값을 보존한다. Lab 삭제를 이유로 9/21 정책 값을 새로 만들거나 과거 모델 ΔEV를 새 이익으로 바꾸지 않는다. 직접 Lab 정책이 없으므로 Lab 명의 next-PREOPEN 정책을 새로 발행하지 않는다.
- commit/push·배포가 승인된 실행에서는 관련 변경만 clean successor에 담고 immutable release를 선택한다. 실행 중 source, 다른 세션 변경을 보존한다. 봇 재시작·주문·조기 PREOPEN 확정은 별도 지시 없이 수행하지 않는다.

## 8. 최종 완료 판정과 보고

전체 완료에는 다음 증거가 모두 필요하다.

1. 두 직접 producer·CLI·wrapper의 실제 삭제와 caller 없는 전용 코드 정리.
2. Main 실행/소비/승격/복구/freshness/일정 전이 0 및 공유 잔존 이유·caller 증거.
3. 양수 과거 파일과 누락 입력 모두에서 퇴역 source 재섭취 차단; 활성 정책 계산·소비와 guard 유지.
4. 불필요 누적 파일 실제 삭제 receipt, 보호/유예의 정확한 이유·owner·closure, 공유 원천·보호 정책 SHA 불변.
5. review → 수정 → 재리뷰 및 영향 검증 결과. 문서·소스·배포·결과 갱신 증거는 각각 분리.
6. 승인된 배포가 포함되면 source commit/push·immutable selected root·검증 receipt·제한 재생성 source/as-of/date를 보고. selected release와 PID 소비를 혼동하지 않음.

최종 보고는 삭제/수정/보존 목록, 소비자 closure, 테스트와 cleanup 수치, 준비 정책의 보존 여부, 남은 자연 OPEN을 제공한다. policy/holdout/실제 손익이 없는 상태를 양수 EV 또는 valid no-edge로 보고하지 않는다. 미래 자연 정책 적용·완료 손익 검증은 기존 owner의 OPEN이며 Lab 복원 사유가 아니다.

이번 계획에는 새 일정·collector·DB·서비스·별도 경제성 탐색기를 추가하지 않는다. 계획 검증 후 실제 제거를 실행할 때도 완료된 기존 계산과 경제성 검증은 새 결함이 없는 한 재작업하지 않는다.
