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

08:00:30까지 반복 점검으로 이번 기동 acceptance를 확인했다.

- Main: 기존 cron/tmux07:55:01 자동 기동, PID325910. `--verify --target-date 2026-09-10 --pid 325910 --write-verify-artifact` exit0/PASS, PID env available, missing/mismatch0 및 policy failure0. 실제 recheck env false/allowed scopes 빈값. WS07:55:14 LOGIN ACK,08:00 첫 실시간 수신 확인.
- Samsung 오전: 기존 timer로07:57:22 PID327358 running, 당일 authority ready.
- Widget: 기존 timer로07:58:00 PID327676 running. 상태 원장 active_date9/10·last_cycle08:00:06, policy execution eligible005930/080220과 observation-only034020/042660 분리.
- Collector08:00:24: `healthy_observer_canary`, stop_required=false, enqueued/processed2069, depth1053, writer/depth writer 각1·error0. 이 순간 가동/수집 검증이지 through-close source-quality나 경제성 완료가 아니다.
- 최초 수리 코드 SHA256 `32f61a379920a601a5e6559ae4cb8bb310ac53b1c84eea630fdca91faf44026a`는07:53 확인까지 동일했다. 최종 대사에서 다른 작업이07:54:53 추가한 OFF 선택 표시 보완을 발견했다. 현재 hash `656a182b767593a55ba892cab05d5dfffc625fd422fac5e45117418787d829bf`로 전체 관련7개 파일 **488 tests PASS**/compile/diff-check 및08:02 PID verify PASS를 다시 확인했다. 반복484회와 합산하지 않는다. 추가 변경은 OFF 정책의 `newly_enabled` 오표시를 `explicit_off_policy|newly_disabled`로 분류하며 env/선정 권한은 바꾸지 않는다. 이미 기동된 live env는 재생성하지 않았다.07:46 apply의 기존 `newly_enabled` 표시는 잔존하지만 `runtime_disable_family=true`와 실제 PID false가 권위를 가지며, 표시 보완의 다음 자연 producer 소비는 기존 PREOPEN owner에서 확인한다.
- launcher hash `32efc0cc145b78db658357812113e51cb88a643374cd070d9a48b5a2cb481c85`와 PID 값 일치. runtime commit `c9b7363a5e6f9d30e60fc9dfbb60d0b18063fd69`, source_dirty=true는 현재 실행 세대의 사실로 보존한다. 전체 dirty 코드를 clean 검증 세대라고 표시하지 않는다.
- 기동 후 verify/collector snapshot은 이전 증거 디렉터리의 `postboot-runtime-verify.json`, `postboot-collector.json`에 보존했다. 이 세션은 실주문·취소나 수동 기동·재기동을 실행하지 않았다. 독립 런타임의 자연 주문 효과는 이번 수리의 효과로 귀속하지 않는다.

남은 장중/through-close·경제성 및 아직 도래하지 않은 저가주 프로필 기동은 [오늘 체크리스트](../checklists/2026-09-10-stage2-todo-checklist.md)의 기존 owner에서 계속 추적한다. `ThresholdEnvAutoApplyPreopen0910` 및 `RuntimeEnvIntradayObserve0910`의 원래 acceptance를 보존한다. 미래 자연 표본이나 경제성 때문에 이번 코드 수리 완료를 취소하지 않는다. 문서 print-only parser30 tasks/해당 PREOPEN owner1개, 외부 sync 미실행.

## 후속 재리뷰: OFF 표시 수리와 이력 부족 해소

이번 사용자 요청은 결함 보완·반복 리뷰와 정상 OFF 해소방법 확인이다. 위 07:46 재생성/기동 확인 기록과 별도이며 이번에는 운영 apply/env/report 재생성, PID 변경, 강제 ON을 실행하지 않았다.

- 추가 결함: 선택된 OFF envelope가 이전 활성 목록에 없으면 `selection_change_class=newly_enabled`, 이전에 있으면 `policy_refreshed`로 표시됐다. 회귀 테스트 두 경우 모두 실패를 확인한 뒤 PREOPEN 분류만 `explicit_off_policy` / `newly_disabled`로 수정했다. 거절 판정이 우선하며 ON의 `newly_enabled`, env 값, 활성 family 산출과 stage owner 계약은 유지한다. 현재 이 flag의 발급 owner는 recheck 하나다.
- 직접 consumer인 runtime manifest, approval summary, daily report, control tower 및 same-stage change 비교를 점검했다. recheck OFF는 stage owner가 아니며 manifest 활성 목록에서도 제외된다. 이번 수리는 신규 활성화 오표시를 없애는 것이지 주문 증가나 비용 후 수익 개선 자체가 아니다.
- source9/9의 `history_complete=true`와 `history_source_quality_pass=false`를 구분한다. 9/7·9/8·9/9 파일은 있지만 9/7 schema5는 현행 exact 계약을 충족하지 못한다. 파일 부족이나 단순 경제성 표본 부족이 아니다.
- 권장 경로: 9/10 정상 수집 → 설치된 20:10 장후 wrapper의 기존 controller → 9/8·9/9·9/10 유효 rolling 창 → 조건 충족 시 9/11 07:35 기존 자동 PREOPEN → 다음 PID 소비 확인. 최신일을 포함한 동일 scope의 addressable critical이 3일 중 2일 이상이고 source/exact 품질·기존 stop/guard도 통과해야 한다. 이력 결손 해소와 ON 선정은 별도이며 날짜 도래만으로 ON을 보장하지 않는다.
- 회귀 테스트에서 경제성/실체결 표본0, EV·순손익 null 상태로 위 창 이동 후 초기 ON이 가능하고 장중 확대는 계속 OFF임을 확인했다. 반대로 9/10도 품질 불량이면 OFF를 유지한다. 이력 품질 gap 자체는 경제성 실패의 sticky stop으로 남지 않는다. 초기 ON에 양수 EV나 사전 실체결을 추가로 요구하지 않는다.
- 9/7 복원은 원본 exact attempt/parent와 당시 provenance를 실제로 재구성할 수 있을 때만 대안이다. schema 번호 변경·현재 자료로 과거 증거 대체·3일 floor 축소는 하지 않는다. 현재 확인된 두 유효일 뒤 새 하루를 받는 유한 경로이므로 이번에는 조건 제거보다 정상 수집과 자동 handoff 확인을 유지한다.
- 코드 이후 자연 artifact의 표시 갱신은 다음 정상 PREOPEN 실행에서 확인한다. 기존 07:46 artifact를 이번 수정의 새 소비 증거로 삼지 않는다. 당일 장후 원천 확인은 기존 `PostcloseSourceQualityGateReview0910`, 다음 PREOPEN/PID acceptance는 다음 체크리스트로 이관해 추적한다.
- 검증 완료: PREOPEN/submit-drought/recheck policy·controller·review/runtime summary/control tower/drought handoff 8개 모듈 473 tests PASS. Python compile, 문서 print-only parser와 `git diff --check` PASS. OFF/ON·거절 분기와 직접 consumer 재리뷰에서 이번 수정 범위 미해결 finding 0. 운영 산출물 재생성·현재 PID 재검증·경제성 검증은 이번 실행 범위가 아니다.
