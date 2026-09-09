# 9/10 recheck PREOPEN evidence 보존 수리

## 범위와 원인

사용자 지시: 결함 해소 후 오늘 정상 기동까지 반복 점검. 기존 자동 PREOPEN 계약과 예정 기동을 보존하며 recheck 강제 ON, guard/수량/provider/주문 변경은 하지 않는다.

07:35 apply plan의 `drought_sentinel_exact_contract_invalid`를 재현했다. source9/9 controller 원본의 KRX/NXT evidence는 검증 PASS이나 PREOPEN `_scrub_removed_contracts`가 `canonical_probe_candidate=null` 등 hash-bound 본문의 null을 삭제해 SHA256이 불일치했다. `current_report_view` 단독으로는 재현되지 않았고 `_scrub_removed_contracts` 적용 직후 재현됐다. source9/7 schema5의 `current_schema_required`와는 별도 결함이다.

## 수정과 검증

- `src/engine/threshold_cycle_preopen_apply.py`: `sentinel_evidence`만 독립 deepcopy로 보존. 외부 candidate/실행 env의 퇴역 필터와 downstream exact date/scope/hash/authority 검증은 유지한다. evidence를 재해시하거나 invalid source를 승인하지 않는다.
- 기존 `src/tests/test_submit_drought_contract.py`에 nullable dict/list 증거 보존, 원본 비변경, post-scrub candidate 검증, 변조 거부 및 퇴역 family 비복구 회귀를 추가했다. 새 producer/test 위치는 만들지 않았다.
- 348 tests: submit-drought contract + threshold PREOPEN.
- 136 tests: drought handoff + recheck policy/controller/review + ADM/LDM retirement.
- 합계 서로 다른 484 tests PASS. Python compile, launcher/PREOPEN `bash -n`, `git diff --check` PASS. 해당 수리 범위의 self-review/fix/re-review 미해결 finding 0. 사용자 기존 dirty 변경은 보존했으며 전체 저장소 코드 검증 또는 clean commit이라고 주장하지 않는다.

## 허용된 최소 재생성

- 이전 apply/env/manifest/verify는 `tmp/recheck-preopen-20260910.hBGlZf/`에 원본 보존했다. 이전 apply SHA256 `4512496deb066a6fe00224030359660ee822e90d9b9f92ab5dad511e70f79781`.
- 검증 종료 및 중복 PREOPEN/main PID 부재 확인 후 `PYTHONPATH=. .venv/bin/python -m src.engine.threshold_cycle_preopen_apply --date 2026-09-10 --source-date 2026-09-09 --apply-mode auto_bounded_live --auto-apply`만 실행했다.
- 07:46:53 새 apply `auto_bounded_live_ready`, handoff PASS, exit0. 기존 07:35 wrapper 성공 시각은 보존하며 전체 wrapper를 새로 실행했다고 표시하지 않는다. 다른 policy/report/Provider/broker producer는 재실행하지 않았다.
- recheck decision은 `selected=true / deterministic_drought_conditional_preopen_policy / runtime_disable_family=true`로 정상 OFF 정책이 채택됐다. 실제 활성 family 목록은 이전과 동일한18개다. env delta는 recheck15개 설정의 명시뿐이며 `ENABLED=false`, allowed scopes 빈값, 기존 freshness/DANGER/probe-first 보호를 유지한다.
- source9/7 schema5 때문에 최근3일(9/7·8·9) 이력이 부족한 `drought_history_source_quality_gap`은 그대로다. 코드 결함 해소와 recheck ON/실제 submit 회복/경제성은 별개다.

## 기동 acceptance

07:55 기존 cron의 main 기동과 새 PID env/WS receipt를 확인 중이다. 후속은 [오늘 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md)의 `ThresholdEnvAutoApplyPreopen0910` 및 `RuntimeEnvIntradayObserve0910`에서 계속 추적한다. 미래 자연 표본이나 경제성 때문에 이번 코드 수리 완료를 취소하지 않는다.
