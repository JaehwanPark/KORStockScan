# Main 장후 source gap 수리·리뷰·배포 인계 — 2026-10-16

판정: 재현된 해시 덮어쓰기, gzip census 오판독, 잔여 주문 제출 원천 누락, 분할 position 수량 대사, 보유 coverage 시계 및 수동 해제 원천 연결을 수리했다. 원문이 없는 과거 입력과 실제 비용·모델 수용은 별도 결손으로 보존한다. 이 커밋은 코드와 회귀 검증의 인계이며 배포·PID 소비·원천 재발행·경제성 PASS 영수증이 아니다.

## 1. 범위와 코드 기준

- 사용자 지시: 별도 작업트리에서 수리하고 코드리뷰·보완을 반복한 뒤 메인 배포 세션에 커밋을 전달한다.
- 작업트리: `/home/ubuntu/KORStockScan-worktrees/postclose-source-gap-repair-20261016`.
- 브랜치: `codex/postclose-source-gap-repair-20261016`.
- 최초 기준: `a94b54afa7c0ef84049238a2d54e3a0d5441f079`, 당시 선택된 read-reduction/recovery 코드. 원장 복구와 기존 반복 읽기 감소 변경을 보존했다.
- 통합 기준: `3c814c05ca979530e38f19bdc68f328c11116f4d`. 다른 배포 세션이 08:54:13 KST 선택한 코드까지 격리 브랜치에 반영했다. 이번 수정 파일과 해당 후속 코드 변경 파일은 겹치지 않았고, 통합 전후 패치 SHA는 모두 `09c4a013d8c49ee287c742f99ae63039ac098236db611dbc0e90c54ababf4e6f`였다. 배포 시점에 선택본이 다시 바뀌면 메인 배포 세션이 그 차이를 확인한다.
- source date `2026-10-15`의 결손 진단을 수리한다. 다음 적용 날짜와 실제 policy/PREOPEN/PID는 운영 인계 owner가 별도로 검증한다.
- 정규 작업공간의 기존 변경, DB, 정책, 원장, 선택본, cron, 실행 프로세스를 수정하지 않았다. 테스트 데이터·로그·임시 evidence는 작업트리 내부에 격리했다. 새 Python 모듈이나 engine-root 소유권을 추가하지 않았다.
- [Plan Rebase](../plan-korStockScanPerformanceOptimization.rebase.md) §1–§8, [10/16 checklist](../checklists/2026-10-16-stage2-todo-checklist.md), `korstockscan-review-gate`에 따라 검토했다. 이번 작업이 기존 체크리스트의 자연 수용 OPEN을 닫지는 않는다.

선행 정밀 보완안은 정규 작업공간의 `docs/proposals/main-postclose-source-gap-precision-remediation-plan-2026-10-16.md`다. 그 문서와 원 점검 evidence는 이번 코드 커밋에 복사하거나 덮어쓰지 않았다. 아래 기록은 배포자가 해당 문서 없이도 수정과 한계를 평가할 수 있도록 작성했다.

## 2. 생산자와 소비자 수정

| 결함 | 수정 및 검증 경계 |
| --- | --- |
| 최종 wire hash를 이전 input hash로 덮음 | `ai_engine_openai`는 최종 compact 입력 구성 후 schema/hash를 갱신하며, 캡처된 `ai_input_payload_*`, `ai_request_*`, `ai_prompt_*` provenance를 일반 annotation merge가 덮지 못한다. cache/parent capture도 보존한다. 프롬프트·모델·threshold는 바꾸지 않았다. |
| compact archive와 legacy `exact_v2` 계약 혼동 | `ai_decision_quality`에 별도 `compact_request_binding_supplement_v1`을 추가했다. 원 trace/request ID, payload wire 재직렬화, prompt·envelope·model, 캡처 시계, machine/native binding, typed venue/session 및 replay context를 대조한다. 원 trace/hash와 strict primary eligibility는 보존한다. 보충 원천 연결이 primary 적격성이나 프롬프트 성능 PASS가 되지는 않는다. |
| gzip census를 missing으로 오판독 | split/cancel-wait가 동일한 strict plain/gzip 논리 source reader와 decoded-size 계약을 사용한다. CRC/EOF, alias 충돌, 날짜·stage·개수·identity hash 합과 원천 세대 변경을 검사한다. 압축 파일 크기를 decoded size로 취급하지 않는다. |
| census 반복 full decode | 원 생산자가 의미 검증한 작은 `execution_census_logical_source_v1`을 cancel-wait source binding에 포함한다. 후속 bounded consumer는 원 retained event의 count/hash 합, manifest, plain/gzip alias 목록과 dev/inode/size/mtime/ctime를 대조한다. 변경 시 이전 검증을 재사용하지 않는다. projection이 없는 과거 보고서는 bounded full validation을 유지한다. present-but-invalid projection은 full read로 덮어 정상 처리하지 않는다. |
| 잔여 BUY가 공통 제출 census에서 빠짐 | 최초 probe 부모/cycle/account/owner/bundle/planned quantity를 고정하고, 기존 residual ACK에도 정규 `order_leg_sent`를 발급한다. 실제 호출에 사용한 owner context를 그대로 재사용하며, 동기 체결 콜백이 먼저 완료되어도 조기 return 전에 기록한다. recovery 필드도 원 source를 보존한다. |
| 잔여 주문을 timeout 실험에 잘못 편입할 위험 | cancel-wait는 residual owner를 `entry_split_probe_residual_runtime`으로 구분한다. `actual_timeout_sec=null`, 후보 timeout 없음, `economic_eligible=false`다. 이미 존재한 residual 실행 시계를 변경하지 않는다. |
| BUY 1/8/12 각각에 SELL 21을 중복 대사 | trade review는 child별 registry·실제 체결을 먼저 검증하고 같은 부모/cycle/account/owner의 전체 BUY 21과 SELL 21을 한 번 대사한다. 누락 child, 교차 cycle, 잘못된 판매 시계/수량은 거부한다. position 잔량은 별도 필드이며 leg별 매도·비용 배분은 만들지 않는다. |
| native 전량체결과 cancel terminal 혼동 | exact execution census와 누적 수량이 주문 수량 전체를 채운 native `FILL_RECORDED/ORDER_TERMINAL`만 보고용 전량체결 증거로 인정한다. 부분체결·cancel은 기존 terminal reconciliation 요건을 유지한다. 원장 terminal receipt를 새로 쓰거나 실제 주문 guard를 완화하지 않는다. |
| quote coverage 시작 지연·frozen worker의 시계 역행 | quote transition 전에 같은 native buy generation으로 coverage를 시작한다. 기존 native birth/restart/ADD 경계는 유지한다. worker 결과가 live coverage의 더 진전된 checked clock을 덮지 못한다. |
| 보유 input gap의 상위 원인이 기록되지 않음 | 작은 sealed `holding_path_input_gap_source_v1`에 원 decision input hash, 활성/forensic 상태, preflight/context blocker, source clock/route와 path별 누락을 기록한다. due path vote의 context kind는 기존 holding-flow 단계 계약을 사용한다. 비활성 forensic view를 실제 input으로 승격하거나 provider를 재호출하지 않는다. 기존 context adapter의 frozen BBO/원가/설정 비용 기반 추정 executable PnL 계약을 유지한다. |
| 합법적인 auto exclusion 해제 후 자동 원천을 무조건 regression으로 판정 | 기존 평균가 도달 해제가 실제 성공했고 잔여 exclusion이 없을 때만 typed `main_stop_release_source_v1`을 관측한다. stop index와 operating comparison이 동일 position/pin의 이 receipt를 소비한다. manual veto, 임의 자동 전환, pin 불일치는 여전히 거부한다. alternative lifecycle은 여전히 censored이며 실현 PnL로 바뀌지 않는다. |

공통 receipt는 관측 목적과 금지 용도를 명시한다. 실주문·sim/CF, 관리권, 전체/부분체결, 실제 비용·설정 비용, 단순 원천 결속·canonical primary를 분리한다. 비용·수익률 결손은 `null`이며 0원이나 gross EV로 채우지 않았다.

압축 입력에는 기존 decoded-byte 한도와 2MiB line 한도를 적용한다. bounded consumer 전체 metadata 예산도 유지한다. 같은 소유자의 local projection은 원천 세대와 producer 봉인에 근거한 재사용 계약이며, report와 원천을 모두 바꿀 수 있는 악의적 writer에 대한 인증 장치라고 주장하지 않는다.

## 3. 자체 리뷰와 보완 반복

| 단계 | 발견과 조치 | 결과 |
| --- | --- | --- |
| 초기 구현 리뷰 | stale manifest가 구체적 generation finding 대신 일반 size 오류로 처리됨. 원 manifest 결속 검사를 먼저 하도록 수정. | 초기 500 PASS/1 FAIL 이후 수정, 관련 300 PASS. |
| 생산자/소비자 재리뷰 | residual owner context가 정확한 send에 귀속되는지 확인하고 잘못 들어간 별도 successor 위치를 제거. regular stage emission의 중복 kwargs도 제거. 전체 position 매도 대사 추가. | 관련 fixture 및 실제 소비 함수 검증. |
| bounded projection 리뷰 | projection 구문의 collection 오류를 수정하고 strict logical read, manifest 봉인, alias/cache 무효화 및 세대 검사 검토. | 854 PASS. |
| 원 request 재리뷰 | 실제 archive schema `ai_decision_request_provenance_v1` 및 compact native venue를 확인. legacy effective-venue 미기록을 원문대로 보존하고 typed native scope를 별도로 결속. malformed replay context를 격리. | 확대 검증 2,456 PASS. |
| ACK/비동기 경계 재리뷰 | ACK 뒤 진단 포맷터의 예상 밖 오류가 submit 경로로 전파될 수 있는 경계를 보완. 영수증 생성·저장 실패, 콜백 선행에서도 주문은 정확히 한 번만 호출되고 원 결과를 유지하는 회귀 추가. 테스트 clock을 fixture 날짜로 고정해 실제 시계와 혼합되지 않게 수정. | 관련 1,207 PASS. |
| 최종 통합 | 선택본 후속 변경을 격리 브랜치에 충돌 없이 반영. 패치 동일성 확인 후 실행 receipt, cost, holding 및 report 소비자를 포함해 다시 검증. | 최종 결과는 §4. |

완료 범위에서 미해결 코드 리뷰 finding은 없다. 다음 절과 §5의 원천 부재·경제성·모델·자연 수용은 이 판정에 포함하지 않는다. 계좌 조회·주문·provider 호출로 회귀 시험을 하지 않았다.

## 4. 검증과 증빙

최종 통합 pytest: **2,480 PASS**, 87.29초. 선택본 후속 receipt 변경과 이번 6개 ACK/관측 실패 조합도 포함한다.

검증 명령:

```bash
PYTHONPATH=. nice -n 10 .venv/bin/python -m pytest -q \
  src/tests/test_ai_decision_trace.py src/tests/test_ai_engine_openai_transport.py \
  src/tests/test_entry_cancel_wait_runtime.py src/tests/test_entry_cancel_wait_tuning.py \
  src/tests/test_entry_split_order_plan.py src/tests/test_trade_review_report.py \
  src/tests/test_trade_review_report_revival.py src/tests/test_sniper_scale_in.py \
  src/tests/test_scalp_exit_safety_monitor.py src/tests/test_holding_decision_context.py \
  src/tests/test_broker_cost_source.py src/tests/test_live_trade_profit_rate.py \
  src/tests/test_entry_machine_source_recovery.py src/tests/test_holding_exit_vote.py \
  src/tests/test_holding_path_vote_replay.py src/tests/test_main_stop_policy.py \
  src/tests/test_main_trailing_source_assembler.py src/tests/test_jsonl_io.py \
  src/tests/test_ai_decision_quality.py
```

- Python compile: 22개 변경 Python 파일의 `py_compile` 완료.
- `git diff --check` 통과. 문서 링크·기존 owner 확인 및 print-only parser 통과: 전체 27항목 중 10/16 체크리스트 OPEN은 고유 11개이며 관련 6개 owner가 각각 한 번만 파싱됐다. shell/wrapper/cron은 변경하지 않아 shell validation은 적용 대상이 아니다.
- private evidence root: 작업트리의 `tmp/source-gap-repair-20261016/`. pytest 각 회차 로그, compile 파일 목록, 통합 전후 patch, frozen compact 사례, 공식 참조 manifest/review를 보존한다. production 2.02GB trade review 또는 97.58MB completion projection을 재생성하지 않았다.
- 실제 보관 원문 한 사례의 readonly preview: `archive_identity_verified_trace_hash_mismatch`, findings `[]`, `canonical_primary_eligibility_changed=false`. 원 fixture SHA `52779defdbad206836780b0605b11c9cc0e3b0c8593ed10a76f52d18e0219253`, 보충 receipt semantic SHA `e4feda5bdbe0b4a2c3a1e4c76b79ece2fcc0d1685ee8813ef610a887cf3d4da2`. 이는 전체 283건 복구 완료의 증거가 아니다.
- 반복 읽기 검증: projection fixture에서 native full census reader를 호출하면 실패하도록 대체해도 bounded semantic consumer가 통과한다. 그 뒤 census bytes를 추가하거나 충돌 alias를 생성하면 같은 cache를 재사용하지 않고 거부한다. full semantics를 최초 producer에서 유지한 채 후속 중복 decode를 줄였음을 검증했다. production end-to-end latency 개선 수치는 측정하지 않았다.

Kiwoom 공식 참조 gate: residual send 인자의 owner context를 동일 객체로 재사용하기 전에 [공식 저장소](https://github.com/Kiwoom-Securities/Kiwoom-REST-API)의 commit `953e5dbff123f437ab4d11a78a95191a685eb51f`를 `2026-10-16T08:24:25.727785+09:00`에 조회했다. 관련 파일은 `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`. 현재 tree에는 `kiwoom_docs`가 없어 그 부재를 기록했다. `kt10000` POST `/api/dostk/ordr`, api-id/auth, JSON 필드, KRX/NXT/SOR·주/KRW 및 응답 주문번호의 ACK 의미, real/demo 구분을 대조했다. Postman query와 SDK JSON 표현 차이는 미해결 공식 자료 차이로 보존했으며 이번 커밋에서 protocol 선택·요청 변경을 하지 않았다. 실제 API를 호출하지 않았다.

## 5. 남은 결손의 owner·다음 행위·종료 시험

아래 숫자는 source15 선행 점검 snapshot이며 이 코드로 production을 재생성한 결과가 아니다.

| 남은 항목 | 기존 owner / 다음 행위 | 종료 시험 |
| --- | --- | --- |
| 과거 residual 미분류 3건 | `DirectFamilySourceRepairEntrySplit`, `DirectFamilySourceRepairEntryCancelWait`: 원 최초/잔여 주문·bundle·cycle·journal을 보존한 별도 source-only 보충 세대를 검증한 뒤 해당 family만 재생성. 이번 커밋은 과거 영수증을 자동 합성하지 않는다. | 원 3개 identity 각각의 복구/거부 보존, 수량·census 대사, residual timeout 권한 없음. |
| HPSP actual cost | `HoldingProfitExitSourceContractRepair`: 1+8+12주 custody 연결 후 기존 official cost/venue/매도 provenance를 재검증. | 실제 원문과 cost receipt까지 일치해야 exact PnL. 단순 custody PASS는 비용 PASS가 아님. |
| 알테오젠 49268/49300 | 같은 holding owner: 공식 원천의 position별 비용 분해 가능성을 먼저 판정. 단일 day/symbol guard는 유지. | 정확한 세부 귀속이 없으면 `broker_day_symbol_position_not_unique`와 미배분 비용/null 유지. 비례배분 금지. |
| 삼성 49266의 COMPLETED 작성 원인 | 같은 holding owner: exact cycle의 DB 전이/SELL/custody 원문을 대조. `sniper_sync`의 zero-inventory reconciliation은 sell_time 없이 경제성 제외하는 기존 경로로 확인했으나 이 record의 최초 작성자로 확정하지 못함. | 실제 매도/관리 종료/원인 미확인을 구분. 49328과 cycle 혼합 없음. DB나 sell receipt를 임의 교정하지 않음. |
| gzip 과거 두 날짜와 10/1 | cancel-wait/split owner: 9/29·9/30은 strict gzip 경로로 successor를 검증. 10/1은 원 census/manifest/compact partition 부재를 유지. | CRC/EOF·decoded size·hash/count·세대 일치. 원문 부재를 verified-empty로 변경하지 않음. |
| compact labels 284 | `DirectFamilySourceRepairCompactAuxiliary`: 원문 후보 283건을 전체 보충 세대로 대조하고 원 response/validator ending도 별도 확인. 미발견 request 1건과 다른 orphan request 1건을 교환 연결하지 않음. | 복구/거부/미발견 합계 보존, 원 trace 불변, legacy exact_v2 primary 불변. 보충 binding만으로 응답 유효성을 주장하지 않음. |
| 과거 holding 미호출 105건 | holding/stop owner: 배포 후 기존 due/budget에서 typed input gap과 활성 계약·flow·추정 executable PnL을 확인. | 원 입력이 적격인 자연 요청/응답·path vote와 quote/vote coverage를 분리 검증. 과거 미호출을 사후 provider 호출로 채우지 않음. |
| stop automatic-after-handoff 1건 | `MainStopLossRetirementRuntimeTuning1010`: 원 position/pin에 실제 합법적 release 원문이 있는 경우만 별도 receipt 결속. | release 증빙 없는 과거 건은 source gap. operator veto·retired-owner custody를 자동 해제하지 않음. |
| native forward path 470 및 split 모델/holdout | 기존 holding/split owner: 원 opportunity와 같은 item/venue/session/clock의 보관 경로가 있는지 조사. 없으면 기존 collector/budget 안의 source-only frozen execution ref·forward-path 계약을 별도 구체화. 이번 커밋은 새 collector, WS 등록 또는 REST/provider 수집을 추가하지 않음. | 원 경로 없는 과거 470건은 `native_forward_path_unobserved`. 미래 수집·모델 검증 완료를 별도 인계하고 실제/CF, 비용, 미사용 holdout과 기존 floor 보존. |

원천 미지원 수집·모델 확장, 공식 비용 분해 및 과거 원문 복구는 완료 주장 대상에서 제외했다. 이를 missing-data 0 또는 전체 warning 0으로 바꾸는 것이 이번 코드 수리의 종료 조건은 아니다.

## 6. 메인 배포 세션 인계

1. 이 문서가 포함된 커밋과 parent `3c814c05ca979530e38f19bdc68f328c11116f4d`를 확인하고, 배포 시점의 최신 선택본과 변경 파일을 비교해 정상 통합한다. 정규 작업공간의 동시 변경을 reset/overwrite하지 않는다.
2. 코드 검증과 선택본 갱신을 분리한다. 실제 기동·정책/PREOPEN 준비·PID/env 소비는 기존 `DirectFamilyPreopenPolicyHandoff` 및 승인된 배포 절차가 소유한다. 이 작업트리에서는 그 절차를 실행하지 않았다.
3. 원 production journal/trace/label/report는 보존한다. 과거 복구와 family successor 재발행이 허용된 슬롯에 의존 family만 재생성하고 날짜·원천·policy·consumer hash를 정상 reader/summary/controller까지 대조한다. 과거 PASS를 새 세대에 재사용하지 않는다.
4. 자연 실행에서는 최종 capture hash 일치, residual 정규 영수증과 원 registry identity, typed holding gap, coverage 시계, stop release 소비를 확인한다. source repair 때문에 주문량·timeout·hard safety·provider·threshold를 변경하지 않는다.

이번 커밋 전달로 구현 수리와 검증 인계는 닫는다. 실제 배포·기동, 과거 보충 세대, 모델/경제성 및 자연 수용은 위 기존 owner의 후속 증빙으로만 닫는다.
