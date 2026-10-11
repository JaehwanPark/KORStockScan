# 의미적 감시기·Main 손절 구현 및 반복 리뷰 — 2026-10-11

§1–§6은 최초 구현 시점의 기록이다. 후속 배포 승인에 따른 재리뷰·운영 결과는 §7 이후에 구분한다. 최초 범위는 두 계획의 코드 구현·격리 검증이다. 운영 정책 발행·장후 재생성·배포·재기동·주문·AI 호출·Telegram 발송은 실행하지 않았다. 전체 계획의 운영·경제·전체 Main 성능 수용을 완료로 표시하지 않는다.

- 실행 owner: [10/11 체크리스트](../checklists/2026-10-11-stage2-todo-checklist.md)의 `SemanticMonitorLatestReleaseRepair1010`, `MainStopLossRetirementRuntimeTuning1010`.
- 기준 계획: [의미적 감시기 M0–M8](../proposals/semantic-monitor-latest-release-followup-repair-plan-2026-10-10.md), [손절 SL0–SL8](../proposals/main-stop-loss-retirement-runtime-policy-and-postclose-tuning-plan-2026-10-10.md).
- 작업 전 기준: 10/11 09:00 KST `initial-quantity-repair-20261011-v2`, commit `818e2f85c216336c9b927d9ae49aad35f0649af7`; Main은 Sunday 정지, target10/12의 실제 PID 소비는 미래 수용이다.
- [작업 전 해시와 변경 목록](../../tmp/semantic-stop-implementation-20261011/baseline.json), [기존 미커밋 diff](../../tmp/semantic-stop-implementation-20261011/workspace-before.patch)를 고정했다. 이 기록은 기존 수량·trailing/delay 변경을 이번 손절 구현 성과에 합산하지 않는다.
- 위치 결정: 순수 정책/재생은 `src/engine/scalping`, 장후 발행/원천 참조 분할은 `src/engine/automation`, report-only incident 계약은 `src/engine/monitoring`, 회귀는 `src/tests`가 소유한다. 새 engine-root 모듈은 없다.

## 1. 수리한 경로

| 범위 | 생산자 → 소비자와 수리 | 결과 경계 |
| --- | --- | --- |
| M1/F1 | [artifact detector](../../src/engine/error_detectors/artifact_freshness.py)의 holding/initial quantity/stop native findings → 구조화 stage → [notifier](../../src/engine/notify_error_detection_admin.py) | 단독 warning도 알림 대상. 실제 Telegram 전송은 격리 adapter로만 시험 |
| M2/F2 | [공통 incident 계약](../../src/engine/monitoring/semantic_incident_contract.py)에서 source/target/stage/scope/reason/generation/path 결속, 등록/승계/published 복구 | owner 이전은 새 사건이 아님. 비교 source-gap과 실제 실행 실패는 등록 성공으로 해소하지 않음 |
| M2/R1–R5 | notifier state 2MiB·report32MiB, 동일 fd/경로 세대, 손상·과거 report 거부, 수신/실제 전달 분리, 성공 batch마다 전달 상태 저장 | 일부 전송 실패는 미전달 batch만 재시도. 복구 없는 overflow는 128건+누락 수/8개 예시로 표시 |
| M3/F3 | 프로젝트 루트에서 실제 관측일의 파싱된 OPEN owner 조회; 중복/결손/파서 실패 명시 | 과거 완료 owner를 current owner로 되살리지 않음. 행동 가능한 incident에만 owner 필요 |
| M7/F4 | [coverage](../../src/engine/monitoring/error_detector_coverage.py)의 producer/native hook/notifier/recovery state/owner 연결 | 정적 coverage는 실제 메시지 전달 성공이 아님 |
| M4 | [제출 감시기](../../src/engine/monitoring/submission_bottleneck_monitor.py) 원 PASS disposition·attempt·선택 delay due·terminal 연결 | 미선택 horizon 부재는 진단. 선택한 due 완료 결손만 정해진 관측 예산 뒤 결손 처리 |
| M5/M6 | native trailing/delay/quantity ancestor 및 [stop committed validator](../../src/engine/automation/main_stop_postclose.py) → report/strict/handoff/PID loader receipt·durable pin | 정책 준비·current PID lookup·실제 exit를 구분. 후속 비용/원천/하위 census shard 정정은 무효화 |
| SL1/SL2 | [handler](../../src/engine/sniper_state_handlers.py)·[설정](../../src/utils/constants.py)에서 score 손절, expert/dynamic/whipsaw 추가 유예, bad-entry OFF actuator, stop-line/late-loss AVG_DOWN no-op, 소비 없는 shadow/timer 제거 | 생존 ADD_REBOUND·review cadence·관측 stagnation·hard/protect/emergency 보존. 퇴역 env는 [scrub](../../src/engine/lifecycle/retirement.py)으로 재유입 차단 |
| SL-F6 | [vote producer](../../src/engine/ai/holding_exit_vote.py)·[프롬프트](../../src/engine/ai_prompt_contracts.py)·[provider schema](../../src/engine/ai_response_contracts.py)에서 bad-entry 제거, v11 4 path×3 market | v10 원장/정책의 생존 항목은 역사적 독자로 검증. 새 요청에서 퇴역 path를 생성하지 않음 |
| SL-F1–F4/F10/F12 | fast/normal의 role 안전 판단·preset grace·REST 응답 후 시계 대사, 수동 인계 claim/등록/최종 submit fencing | 등록/fsync는 ENTRY_LOCK 밖. 동시 등록 중복·등록 실패 후 hard-stop SELL 전환 금지. 비상/보호값과 수동 수탁 권한은 유지 |
| SL3/SL4 | [공통 typed 정책](../../src/engine/scalping/main_stop_policy.py)·[peak ledger](../../src/engine/scalping/position_peak_ledger.py)·[BUY receipt](../../src/engine/sniper_execution_receipts.py) → startup lookup/position pin·원 touch | 새 initial BUY만 새 정책 pin. ADD·재기동·날짜 변경으로 유예 연장 금지; 복구 시 원 시계가 없으면 새 grace 부여 금지 |
| SL5 | 기존 검증 quote → shared bounded observation queue → `main_stop_source` → [분할 참조 index](../../src/engine/automation/main_stop_source_index.py) → [인과 재생](../../src/engine/scalping/main_stop_replay.py) → 발행/strict/bootstrap/pin | 별도 broker/AI/실시간 연구 worker 없음. 요청한 후행 AI를 합성하지 않음. 실제 비용 없는 평가를 0원으로 채우지 않음 |

## 2. 손절 정책·경제·구조 경계

`soft_stop_pct/grace_sec/window_sec/min_span_sec/min_samples/below_ratio/buffer_pct`의 7개 축과 별도 hard/soft-emergency/protect-emergency/exit-floor 4개 참조를 typed 계약으로 분리했다. role3×시장3의 9개 cell을 발행하며 확인된 부모값을 계승한다. 한 번에 한 cell·한 축만 명시한 경제/운영 계약으로 변경 가능하다. 현재 운영 임계값을 이번 시험에서 변경하지 않았다.

`main_stop_source`는 진입 시 동결된 비용 모형과 판단 당시 `decision_profit_pct`를 별도로 보존한다. crossing은 실제 운영 판단 수익률을 사용하고 대안 청산의 경제성은 비용 모형으로 계산한다. 실제 `COMPLETED`·Main 자동 수탁·실제 비용 대사 원천을 경제 선정의 별도 적격 조건으로 검증한다. 모델 대안 PnL을 실제 체결 손익으로 보고하지 않는다.

재생은 원 quote/route/item/epoch·position/pin·quantity/basis·수신시각·원 AI 요청 결속을 검사한다. 부분 체결·ADD·manual·이미 시작한 exit·첫 관측 이전 crossing·수집 결손은 검열/결손이다. 원장 생성은 1초 cadence이며 1.5초 초과 빈 구간과 queue 거절 세대가 변한 구간을 성공 표본으로 합치지 않는다. 운영 보호 sample은 최대30초/512개이고 runtime 판단 window와 구분한다.

forward train/holdout은 전체 position을 분리하고 최대60초 유예의 embargo를 둔다. train winner 하나를 먼저 고른 뒤 그 후보만 holdout으로 확인한다. train/holdout 표본·paired EV·표준오차·검열률·일일 변경폭·operator exact-key·현재 코드에 결속된 전체 성능 증빙을 계약에 요구한다. 이 숫자를 운영 파일에 임의로 발행하지 않았다. 검증 fixture에서 2 train+2 holdout의 grace60→0 후보가 정식 publisher→handoff→loader→SCANNER/REGULAR pin에 도달하고 다른8개 cell은 부모를 유지했다. 이는 합성 검증이며 운영 정책 선정이 아니다.

두 경로는 계속 명시적으로 제한된다.

1. **SL-F8 보호선 생성:** 현재 남은 신규 생성 예시는 퇴역 PYRAMID이며, Main 신규 생성자는 검증되지 않았다. DB의 `trailing_stop_price` 숫자만으로 arm·단조성·수탁을 증명하지 않는다. 해당 재생은 `protect_line_producer_unidentified`이며 보호 확인 후보의 성과로 선정하지 않는다. 기존 runtime 보호선을 무효화하거나 PYRAMID를 복구하지 않았다.
2. **SL-F11 AI vote 경제 선정:** 기존 holding vote family의 기본값 발행을 `baseline_only_unidentified_counterfactual_votes`로 명시했다. 새 stop family는 이 family의 값 변경을 중복 발행하지 않는다. 원 crossing 이전 투표가 없는 대안 시점의 AI 답변을 만들지 않았다. 기본 soft−3%에 대해 기존 protect-emergency−2%가 VETO를 해제하는 우선권을 보존하므로, 그 경로에서 VETO 조정의 우월성을 합성하지 않는다. vote 값 변경 selector/실제 우월성 수용은 완료 주장 범위 밖이다.

SL-F8의 별도 Main 생성자 설계 경계는 다음과 같다. native initial BUY/ADD receipt와 수탁을 출발점으로 arm event·기준 가격·비용/quote 원천을 먼저 영속 결속하고, 별도로 승인한 arm/선 산식만 사용한다. `new_line=max(previous_line, authorized_formula(verified_peak, cost_basis))`의 단조성을 같은 buy generation 안에서 검증한다. ADD의 평단/잔량 변경·재기동은 원 receipt로 승계하거나 결손 처리하며, 과거 최고가/보호선을 새로 합성하지 않는다. hard/emergency/manual 우선권과 시장/route/freshness를 보존한다. 실제 적용 전에는 arm 전 선 부재, 중복 tick/재연결, 비용 정정, ADD/부분 SELL, manual 전환, normal/fast 동등성 시험과 해당 가격선 변경 권한을 별도로 확정해야 한다. 이 확인 정책 구현에 신규 보호선 활성화 권한을 섞지 않는다.

## 3. 장후 운영 연결과 저장·재개

[기존 wrapper](../../deploy/run_threshold_cycle_postclose.sh)의 verified postclose-exit snapshot 뒤에 native `main_stop_confirmation` stage를 연결했다. source10/12부터 설치되며 과거10/8 stage 부재를 장애로 만들지 않는다. 새 cron은 없다. 직접 CLI와 wrapper는 기존 공통 heavy-job admission을 사용한다.

호출: `PYTHONPATH=. .venv/bin/python -m src.engine.automation.main_stop_postclose --date SOURCE_DATE --target NEXT_TRADING_DATE`. 이것은 운영 안내이며 이번 작업에서 운영 data root에 실행한 명령이 아니다. target은 native 거래일 함수로 검증하며 현재 실험 계약이 없으면 9개 부모를 계승한다. parent operator 지시가 변경되면 exact source reconciliation 없이 이전 challenger를 이어받지 않는다.

원천은 기존 base/gzip 및 late/gzip pipeline ledger이다. 변경된 파일만 해독해 position 전체를 16개 hash partition으로 나누는 위치/해시 참조를 저장한다. AI payload·quote body 복제본을 만들지 않는다. 각 구간의 전역 중복/충돌을 보존하고 split/분모/후보 집계는 전체 기준으로 합산한다. 변경 position만 후보 block을 재생하고 결과 checkpoint를 검증해 재사용한다. 비용 정정은 비용/선정만 재평가한다. 무변경 실행은 원 raw JSON 해독0·replay0이며 필수 byte 확인을 생략하지 않는다.

프로세스의 연구 출력2GiB·임시 예약2GiB, 단일 정렬 index512MiB 및 기존 resident Claim을 재사용한다. 공유 큐의 전체1024건/4MiB를 늘리지 않고 stop category는128건/전체 byte의1/8로 제한했다. enqueue 불가 시 동기 원장 쓰기나 새 worker로 우회하지 않는다. 원천은 structured field에 한 번만 쓰고 text diagnostics에는 해시 참조만 둔다.

4시간 native stage 상한과 동일한 협조적 deadline을 직접 CLI에도 적용했다. budget/deadline 중단은 `report/main_stop_confirmation/resume_SOURCE_DATE.json`에 `incomplete`와 보존 parent/replay cache 위치를 남기며 예전 pointer를 새 성공으로 덮어쓰지 않는다. 부분 결과를 전수 완료로 표시하지 않는다. 공유 dispatcher의 외부 timeout/실패 영수증도 그대로 남는다.

발행은 immutable generation의 policy/report/census → compatibility alias → native committed 검증 → target pointer 순서다. 소비자는 단일 target pointer와 terminal source를 읽는다. 읽는 도중 바뀐 파일, 하위 census shard 교체, 실제 비용 정정, 새로 생긴 원 투표/요청 파일, code 변경을 검출한다. 원천 파일 목록도 봉인하므로 나중에 생긴 base/late 원장이 있으면 이전 handoff를 무효화하며, 해당 파일을 입력에서 누락한 재발행은 거부한다. 현재 코드와 다른 실행 bundle은 loader가 거부하되, 검증된 incumbent의 과거 값은 새 코드의 migration parent로만 읽을 수 있다. 기존 포지션의 ancestor pin을 무조건 최신 pin으로 바꾸지 않는다.

## 4. 리뷰·검증 근거

작업 중 발견한 주요 추가 결함은 수동 인계의 공유 lock 점유/중복 등록, 빠른 경로의 공통 hard fallback·preset grace/응답 시계, 복구 시 grace 재시작, vote v11 요청과 provider schema v10 불일치, queue 쓰기 지연, 실제 판단/비용 모형 혼합, 원천 전체 재정렬, 신규 vote 파일 발견 누락, late 원장 누락, 하위 census 변조 미관측 및 새 코드에서 과거 parent 값 승계 불가였다. 각각 보완하고 반례 시험을 추가했다.

- 통합 영향 회귀: [integrated19](../../tmp/semantic-stop-implementation-20261011/integrated19.log)는 2,292 passed/1 failed. 실패는 기존 테스트의 퇴역 whipsaw owner 기대값이며 Main stop owner로 수정했다.
- 그 수정과 실제 프롬프트/schema를 포함한 영향 재검증: [final20](../../tmp/semantic-stop-implementation-20261011/final20.log) 1,088 passed.
- native shard·발행/strict/bootstrap 교차 확인: [native21](../../tmp/semantic-stop-implementation-20261011/native21.log) 277 passed.
- deadline/late/cost/세대 추가 확인: [closure22](../../tmp/semantic-stop-implementation-20261011/closure22.log) 190 passed.
- 최종 계약 영향 확인: [closing23](../../tmp/semantic-stop-implementation-20261011/closing23.log) 322 passed.
- 고정값 계산을 pin 준비로 이동한 뒤 잘못된 pin의 hard safety까지 확인: [safety24](../../tmp/semantic-stop-implementation-20261011/safety24.log) 1,000 passed. 묶음은 중복되며 단순 합산하지 않는다.
- 최종 원천 목록 보완 후 새 late 파일의 handoff 무효화→누락 발행 거부→전수 census 추가와 연결 consumer 재검증: [native25](../../tmp/semantic-stop-implementation-20261011/native25.log) 264 passed.

Kiwoom 공식 기준은 10/11 KST 조회한 upstream `953e5dbff123f437ab4d11a78a95191a685eb51f`이다. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json` 및 Postman ka10004 항목을 확인했다. 해당 revision에 `kiwoom_docs` 디렉터리는 없었다. 이번 관련 변경은 기존 ka10004 재확인 응답 뒤의 판단 시계 보정이며 REST request/response field/FID/route suffix/auth/order payload는 바꾸지 않았다. 실제 provider 호출은 없었다.

## 5. 성능 결과와 수용 한계

[고정 workload/예산](../../tmp/semantic-stop-implementation-20261011/performance-contract.json), [최종 runtime/notifier 교대 측정](../../tmp/semantic-stop-implementation-20261011/performance-reviewed.jsonl), [측정 script](../../tmp/semantic-stop-implementation-20261011/benchmark.py), [장후 측정 script](../../tmp/semantic-stop-implementation-20261011/measure_postclose.py), [최종 자동 집계와 원본 해시](../../tmp/semantic-stop-implementation-20261011/performance-summary.json)를 남겼다. normal/burst/slow-writer 각각 baseline/candidate3회, 주문·provider adapter는 격리했다. 초기 비교에서 구 `_rule_float`의 0→기본값 치환 차이를 발견하여 positive buffer0.1의 같은 실효값으로 다시 동결했고 무효 비교 파일도 삭제하지 않았다.

보호 확인 helper CPU는 약40% 감소했다. fast evaluator의 비진입 fixture는 기존보다 p99가 증가했고, notifier의 durable delivery state 쓰기도 비용이 증가했다. 따라서 일부 helper의 개선을 전체 Main 성능 개선으로 표현하지 않는다. 중간 `performance-sealed.jsonl`에서는 normal fast p99가 16.31% 증가하여 사전 15% 예산에 실패했다. 프로파일링 후 고정 정책값 해시 계산을 최초 pin 준비 시점으로 이동했고, 최종 변경 뒤 같은 조건 전부를 다시 측정했다. 최종 9개 candidate 측정은 동일 handler SHA `58c88e60f7aceaafd3f0f0bd468ee1d99b86d2b5b519040ca0254b27c4bd5e49`에 결속된다.

| workload | 보호 helper p99 기존→후보(ms) | fast p99 기존→후보(ms) | fast p99 변화 | 후보 notifier p99(ms) | 후보 fast max(ms, 3회 전체 최대) |
| --- | --- | --- | --- | --- | --- |
| normal | 0.0604→0.0379 | 0.5444→0.6066 | +11.43% | 0.896 | 6.250 |
| burst | 0.0603→0.0378 | 0.5531→0.6278 | +13.51% | 2.583 | 6.242 |
| slow writer | 0.2152→0.1928 | 0.6958→0.7687 | +10.48% | 1.131 | 6.408 |

p99는 각 실행 p99의 3회 중앙값이다. 결과 해시 동일·주문0·고정된 격리 수치 예산은 통과했다. 이 표의 fast는 비진입 fixture이므로 실제 hard/protect breach·전체 Main p95/p99 비악화를 증명하지 않는다.

장후는128개 전수 position/2,560개 후보 계산을 3회 측정했다. warm은 원천 scan0/replay0, cost-only도 scan0/replay0, position1건 증분은 새 파일 scan1·20개 후보만 replay했다. 전체128/129건 census와 정책 값은 같았고 주문0이다. native full verification/handoff/preload도 측정에 포함했다. 큰 실제 원장·동시 trailing/delay host 합산 peak·자연 WS wake→Main dispatch 보호 tail까지 완료한 성능 gate로 사용하지 않는다. 연구 계약이 요구하는 `runtime_and_postclose` 성능 PASS 영수증은 이번 부분 측정으로 발행하지 않았다.

| 장후 조건 | 연구 시간(초, 3회 중앙값) | 원천 scan | 후보 replay |
| --- | --- | --- | --- |
| cold 128 position | 2.013 | 1 | 2,560 |
| 무변경 warm | 0.0113 | 0 | 0 |
| 비용 정정 | 0.157 | 0 | 0 |
| position 1건 추가 | 0.188 | 1 | 20 |

최종 장후 세 측정의 code SHA는 `24bd3eab862ed7fe863839b6fe4a7af76ce1cdb361cadd89d49648596b17e136`로 동일하다. 최종 원천 목록 결속 보완 후 cold/warm/source/cost-delta를 모두 다시 측정했다. 프로세스 peak RSS는 약47.7MiB이고 실제 임시 디스크 peak와 예약 상한은 구분한다. 집계의 `peak_reserved_disk_bytes` 약1.50GiB는 공통 예산 예약량이며 실사용 peak로 보고하지 않는다.

## 6. 잔여 수용과 보호한 상태

| 잔여 | 실제 owner / 다음 조건 / 종료 시험 |
| --- | --- |
| SL6 전체 성능 | `MainStopLossRetirementRuntimeTuning1010`: 전체 normal/fast 동시 breach와 Main/PASS 만료·host heavy-job 합산, 실제 규모 원천의 cold/warm/source/cost-delta를 동일 입력으로 측정. 단위/격리 결과만으로 이 gate를 PASS 처리하지 않음 |
| SL-F8 새 보호선·SL-F11 vote 값 변경 | 같은 stop owner가 별도 생성/경제 선택 owner와 권한을 확정. 위 source-gap/baseline-only 경계를 해제할 native producer·실제 인과 입력/변경 selector·loader 시험 필요. 시간 경과만으로 구현 공백이 없어지지 않음 |
| 감시 A/B 및 손절 운영 인계 | 검토한 코드의 별도 배포 후 source→summary/strict/controller/finalization→정확 target PREOPEN을 재검증. 이전 release 준비 PASS를 새 release의 근거로 전용하지 않음 |
| 실제 소비·경제 | source10/12 이후의 자연 source/원 투표·비용 및 해당일 PID lookup/pin·exit disposition. 정책 파일 존재를 실제 SELL/경제 개선으로 보고하지 않음 |

선택 릴리스와 10/12 봉인 체크리스트, 현재 수량 pointer, Rebase를 작업 전 SHA와 대조했다. [정적 검증](../../tmp/semantic-stop-implementation-20261011/final-static-checks.json)은 Python77개 compile, `bash -n`, `git diff --check` 통과이며 보호한4개 SHA가 동일하다. [문서 검증](../../tmp/semantic-stop-implementation-20261011/document-link-check.json)은 로컬 링크123개 결손0, [최종 print-only backlog](../../tmp/semantic-stop-implementation-20261011/backlog-final.json)는 총22개 OPEN 중 두 현재 owner 각각1개다. 외부 Project/Calendar 동기화는 실행하지 않았다.

공유 미커밋 작업과 원 EOD/정책 원장을 정리하거나 커밋하지 않았다. 배포·재기동·운영 장후 재생성과 자연 수용은 미실행이다. 검토·회귀에서 확인한 구현 결함은 보완했으나, 위 잔여 수용을 포함한 **전체 계획 완료/전체 성능 PASS는 아니다**.


## 7. 배포 승인 후 재리뷰·지연 보완

10/11 후속 요청에서 코드 재리뷰·수정보완·배포와 10/12 정상기동 준비 점검을 승인받았다. [비교 기준과 작업 목록](../../tmp/semantic-stop-deploy-20261011/review-inventory.json)은 직전 선택 릴리스 `initial-quantity-repair-20261011-v2`와 작업본의 실제 차이를 고정한다. 새 릴리스에는 이 차이와 추가 보완을 합쳐 runtime/test 파일46개를 반영했다. canonical 작업트리의 기존 미커밋 변경은 삭제하거나 임의 커밋하지 않았다.

첫 hard breach 시험에서 이전 비진입 시험이 찾지 못한 성능 결함이 드러났다. 새 손절 원장 writer가 실행 스레드와 CPU/GIL을 경합해 정상 부하 p99 +126.4%, 집중 부하 +107.5%로 15% 한도를 넘었다. [실패 원본](../../tmp/semantic-stop-deploy-20261011/breach-performance.jsonl)을 보존했다. 다음을 보완한 뒤 동일 부하로 baseline/candidate를 각각3회 교대 측정했다.

- fast 판단 시점의 원천은 변경 전 canonical JSON으로 동결하고, shared queue admission은 청산 전달/판단 반환 뒤에 수행한다. 호출별 임시 buffer는 최대2건·행당64KiB이며 기존 shared category128건/byte1⁄8 예산을 늘리지 않는다. 큐 실패는 명시적 결손으로 남고 원 청산 예외/반환을 가리지 않는다.
- writer가 같은 원천을 반복 직렬화하지 않도록 canonical bytes로 해시·봉인을 생성한다. 기존 worker에서 행 사이에 실행권을 양보하며 매매 스레드에 sleep·원장 동기 쓰기를 추가하지 않는다.
- bootstrap hash가 없는 관측 vector는 모든 실효 입력을 key로 하는8개 상한의 순수 projection cache를 사용한다. 환경값/실효값/분류기 digest 변화는 새 계산이며 반환값 변조가 cache를 오염시키지 않는다. 투표 원장 이름도 position별128개 상한으로 계산만 재사용하고 파일/정책을 캐시하지 않는다.
- 퇴역한 점수 helper를 직접 호출하던 구 회귀를, 점수 설정 변경이 현재 기계식 TP vector를 바꾸지 않는 소비자 검증으로 수정했다.

| 부하 | 함수 반환 p99 기존→후보(ms) | 증감 | 청산 전달 p99 기존→후보(ms) |
| --- | --- | --- | --- |
| 정상 | 0.579585→0.647460 | +11.71% | 0.577039→0.628593 |
| 집중 | 0.591342→0.653986 | +10.59% | 0.588938→0.633445 |
| 느린 writer | 0.940510→0.964315 | +2.53% | 0.937623→0.933662 |

[최종18회 원본](../../tmp/semantic-stop-deploy-20261011/breach-final.jsonl), [자동 검증 집계](../../tmp/semantic-stop-deploy-20261011/breach-final-summary.json). 매 회500개 동일 hard-stop 전달을 격리 adapter로 확인했고 실제 주문0·결과 hash 동일이다. 이 값은 고정 fixture의 결과이며 전체 Main/동시 연구 host 성능 gate로 발행하지 않는다. 변경 경제정책에 필요한 전체 성능 증빙의 미완료 경계는 유지한다.

- [감시·장후 교차 회귀](../../tmp/semantic-stop-deploy-20261011/review-tests.log): 648 passed.
- [runtime 영향 회귀](../../tmp/semantic-stop-deploy-20261011/runtime-tests.log): 1,014 passed.
- [최종 보완 후 영향 회귀](../../tmp/semantic-stop-deploy-20261011/review-final-tests.log): 1,057 passed.
- [불변 새 릴리스 회귀](../../tmp/semantic-stop-deploy-20261011/release-tests.log): 187 passed. 각 묶음은 중복되며 합산하지 않는다.
- 검토46개 파일의 Python compile, shell `bash -n`, `git diff --check` PASS. 기존 pandas 경고1건은 위 실패 원인과 별개다.

실제 source10/8의 holding/all-scope 인계 재검증은 약77.75초·peak RSS152.6MiB였다. [실자료 결과](../../tmp/semantic-stop-deploy-20261011/actual-source-research.json)의 전체20,832scope 중 population7·common0이며12cell 모두 부모를 유지했다. 누락/검열 표본을 실제0손익이나 신규 우월 정책으로 바꾸지 않았다.


## 8. 승인된 통합 배포와 10/12 기동 준비 결과

선택 릴리스는 `main-stop-semantic-20261011-v1`, commit `91edc62844180be6a279e761f32996c3c76ce72e`이다. 임시 Git index와 detached release로 검토된46개 runtime/test 파일을 직전 선택본에 통합했다. [새 릴리스 구성/해시](../../tmp/semantic-stop-deploy-20261011/release-build.json)와 [CAS 전환](../../data/runtime/research_release_transition/main_stop_semantic_20261011_v1/transition.json)은 `verified`이며 원 workspace 미커밋은 보존했다.

정식 source10/8→target10/12의 holding/all-scope native 원천·typed trailing12cell 부모 승계→제출지연→summary/checklist→strict/controller→finalization→PREOPEN을 새 코드에 결속했다. 기존 초기수량 stage는 native validator PASS로 재사용했고 source/receipt SHA를 보존했다. EOD·completed projection·기계/보조 정책·현재 수량 pointer·Rebase의 원 SHA도 동일하다.

- [정식 인계](../../tmp/semantic-stop-deploy-20261011/formal-handoff.json): 제출지연·summary `succeeded`, controller `done`, PREOPEN `current_full_contract=pass`.
- [최종 준비 근거](../../data/report/main_stop_semantic_deployment/2026-10-11/final-readiness.json): finalization 세대 issues0, strict/checklist 세대 일치, 예약 cron·release-set 검증 PASS.
- 실제 wrapper의 source10/8 최종 `DONE`은 **2026-10-11 11:33:05 KST**다. cleanup·detector도 완료했고 원 wrapper exit0을 확인했다. 과거 DONE을 이번 완료로 전용하지 않았다.
- 최종 감시 run `cron-20261011T113250-549897`: fail0·warning4, runtime mutation0. [경고 원본 요약](../../tmp/semantic-stop-deploy-20261011/final-detector-summary.json)의 workorder/KOSPI 경고, 실행 중인 부모 finalization의 detector 대기, 10/9 22:36:36 인증8005 기록의 dry-run 진단, 변경 없는 과거 로그를 보존했다. 이후 genuine DONE의 별도 native 검증으로 부모 대기는 종료됐으며 감시 원본을 사후 덮어써 PASS로 만들지 않았다. 실제 인증 재호출/토큰 변경/재기동 flag 생성은 하지 않았다.

[준비된 소비 계약](../../tmp/semantic-stop-deploy-20261011/prepared-policy-consumption.json)은 holding path vote v11·생존4경로×3시장12cell이다. soft−3%, common hard−5%, 최초 micro grace60초의 현행 참조와 별도 수동 인계 설정을 유지한다. role/preset의 별도 실효 우선권은 runtime에 남으며 이 숫자를 모든 경로의 단일 손절로 해석하지 않는다.

새 stop family는 source10/12 장후부터 설치되어 다음 영업일 정책을 발행한다. 따라서 source10/8로 준비한 10/12 bootstrap의 stop receipt는 정상적인 `not_installed`이고, 10/12 장중에는 현행값의 position pin·원천 수집을 소비한다. 역사적 자료 없는 새 후보를 10/12 변경 정책으로 합성하지 않았다.

**10/12 07:35 PREOPEN·07:55 Main 예약기동 준비는 PASS**다. Sunday Main은 정지 상태를 유지했으며 `actual_main_pid_consumed=false`/`future_due`다. 기존10/12 OPEN `DirectFamilyPreopenPolicyHandoff`에 새 release cwd/start ticks·v11/stop pin·queue 원천·수동 수탁의 자연 수용을 연결했다. 당일 실제 인증·WS·PID·자연 제출/청산은 아직 미관측이다.

§6의 전체 Main/동시 heavy-job 성능, 새 Main 보호선 생성, AI vote 경제값 변경 selector 및 실제 자연 경제성은 여전히 별도 잔여다. 이번 배포·기동 준비 PASS를 그 완료나 성과 개선으로 대체하지 않는다. 검토한 구현/인계 범위에서 발견한 결함은 수정·재검증했으며 전체 계획 완료로 표시하지 않는다.

[최종 문서 검증](../../tmp/semantic-stop-deploy-20261011/document-checks.json): 로컬 링크149개 결손0, print-only parser22개 OPEN 중 두 현재 구현 owner와10/12 자연 인계 owner 각각1개, diff 검사PASS. 배포46개 소스의 workspace/release SHA가 검토한 구성과 모두 일치한다. 외부 Project/Calendar 동기화는 실행하지 않았다.
