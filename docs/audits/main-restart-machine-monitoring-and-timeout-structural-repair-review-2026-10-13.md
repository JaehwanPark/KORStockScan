# 10/13 최신 Main 재기동 점검 및 시간초과 구조 수리

## 후속 승인에 따른 배포 전 재리뷰

사용자는 “코드리뷰후 수정보완 반복하고 배포 및 재기동 승인”으로 이번 수리의 배포·재기동을 명시 승인했다. 기존 운영 commit `afd16c5502da1d012d62c1bbe8b07797f1c53efa` 대비 앞선 수리 10파일을 확인했고, 별도 작업본을 일괄 배포하지 않는다. 당일 정책·threshold·모델·원 native 기한은 유지한다.

재리뷰에서 정상 응답 뒤 로컬 검증으로 기한이 소진되면 CLOSED 회로 실패 연쇄가 끊기지 않는 잔여 결함을 보완했다. CLOSED는 실제 Provider 반환 시각으로 정시 응답을 판단한다. HALF_OPEN은 최종 실행 검증과 현재 남은 원 기한을 계속 요구한다. 정상 원응답→native 무효화→로컬 기한 소진이 반복되는 실제 `analyze_target` 경로를 추가 검증했다. 기동 검증에는 원 코드/수리 코드의 정확한 SHA 쌍만 추가하며 이전 영수증을 유지한다.

[배포 전 회귀 로그](../../tmp/timeout-structural-deployment-20261013/review-tests.log): 관련 11개 suite **1,165 PASS**. Python compile 및 diff 검증 PASS. 리뷰 범위 미해결 code finding은 0이다. 배포 후보는 별도 index와 현재 선택 commit을 부모로 생성하며, 공유 원장 복사·외부 sync·Provider replay는 없다. 체크리스트 편집본은 후보 Git에만 준비하고, 기존 Main 종료 후 ordered driver가 발행한다. 배포·실제 PID·자연 관측 결과는 아래 후속 증빙에서 따로 기록한다.

## 판정과 범위

후속 배포 중 `18:15:18`에 기존 Main을 정상 종료한 뒤 선택 전환은 완료됐으나, `18:15:40` 새 인계 검증이 `active_policy_code_handoff_source_changed:.../runtime_release_selection.json`으로 차단됐다. code handoff를 이미 사용한 릴리스의 후속 발행에서 predecessor selector까지 immutable source로 다시 묶는 연속 배포 결함이었다. 실패를 보존하고 startup hold 아래 이전 선택·체크리스트·정책을 복원했다. [복구 영수증](../../tmp/timeout-structural-deployment-20261013/rollback-completion.json)의 PID `3357134`/ticks `13243787`가 `18:18:35`에 같은 incumbent commit을 소비했으며 강제 종료나 정책 변경은 없었다.

`reversal_code_handoff.issue`에서 predecessor selector는 발행 중 CAS와 원 SHA 이력으로 보존하고, 변경 불가 정책 원천 집합에서는 제외하도록 수리했다. 실제 소비자는 계속 현재 selector의 정확한 candidate root/commit을 확인한다. 다른 원천·이전 receipt·code pin은 그대로 검증한다. [연속 인계·변조 반례 13건](../../tmp/timeout-structural-deployment-20261013/handoff-fix-tests.log)이 통과했으며 최종 후보에서 전체 관련 검증 후 재전환한다. 처음 실패한 `00dff1bf` 릴리스를 성공으로 덮어쓰지 않는다.

전수 snapshot은 `2026-10-13T17:23:28+09:00`, 마지막 liveness 재확인은 `17:52:07 KST`다. Main/WS/감시 루프는 가동 중이나 전체 진입 경로를 정상으로 확정하지 않는다. 재기동 후 보조 전송 시간초과, 신호 종료와 전송 실패의 혼합 집계, 비상시 원천 미충족, 저장 준비 잠금 경합의 오류 분류와 장후 경고 원인 투영 결함을 확인했다. 사용자의 후속 “식별된 결손을 우선 보완” 지시에 따라 아래 코드 수리와 검증을 수행했다. 배포·재기동·Provider replay·주문·정책/threshold/수량 변경은 수행하지 않았다.

선택 릴리스는 `/home/ubuntu/KORStockScan-runtime-releases/main-joint-source-20261013-v2`, commit `afd16c5502da1d012d62c1bbe8b07797f1c53efa`, Main PID `3208863`, start ticks `12814322`, 시작 `17:06:36 KST`, cwd는 해당 릴리스의 `src`다. bootstrap 검사와 정책 소비 영수증은 같은 PID/start/cwd로 PASS다. bundle `d906615b11d8d9175930a0c7e1bed3f7d7f1c7dd237a129814c7629de49f0a5b`의 128개 scope를 소비했다. 이는 당일 부모 정책의 소비 증거이며 내일 후보 활성화나 실제 주문 성공 증거가 아니다.

원본 파일의 경로·크기·byte hash와 읽은 시각은 [snapshot manifest](../../tmp/restart-health-check-20261013/summary.json), 전체 추출은 [재기동 후 사건](../../tmp/restart-health-check-20261013/postrestart-events.json), 마지막 PID 상태는 [17:52 재확인](../../tmp/restart-health-check-20261013/latest-live-check.json)에 고정했다. 대용량 원장을 전체 scan하지 않았다. 기존 요약과 최대 16MiB tail, 관측된 offset 사이의 5MiB 중첩 slice로 `17:06:36~17:23:28`의 대상 terminal을 대사했다.

## 상시·비상시 전수 결과

상시 5종목 모두 exact `_AL`, transport epoch 1의 `0B/0D`가 실제 수신됐다. 아래 age는 17:23 snapshot의 호가 수신 경과시간이며 체결 빈도나 성과가 아니다. 반복 `blocked_strength_momentum`/VPW `risk_context_only` 행을 기계 BLOCK 또는 unique 타점으로 세지 않았다.

| 종목 | 0B/0D 수신 수 | 호가 age | 실제 판정·소비 |
| --- | --- | --- | --- |
| 삼성전자 005930 | 7,747 / 4,853 | 6 ms | 자연 ENTER_NOW와 Provider 응답·시간초과·Main disposition 존재. 응답 후 `reversal_signal_path_changed`와 실제 시간초과를 분리해야 함 |
| 두산에너빌리티 034020 | 570 / 1,891 | 6 ms | 반복 방문·원천 수신 확인. snapshot 내 자연 async machine attempt 없음; 정상 기계 BLOCK으로 대체하지 않음 |
| HPSP 403870 | 207 / 770 | 2,193 ms | 반복 방문·원천 수신 확인. 자연 async machine attempt 없음. 비상시 중복 선정 4회는 기존 Main 대상 충돌로 차단 |
| 알테오젠 196170 | 118 / 547 | 807 ms | `aims-9d57f2897764634ac44d`: ENTER_NOW → PASS → Main accepted → `weak_momentum_caution_without_micro_confirmation`; 실제 제출로 세지 않음 |
| 주성엔지니어링 036930 | 384 / 1,510 | 207 ms | 반복 방문·원천 수신 확인. snapshot 내 자연 async machine attempt 없음 |

비상시 후보 큐 1,351행을 [종목별 census](../../tmp/restart-health-check-20261013/nonfixed-census.csv)에 전부 분류했다. 이 중 상시와 겹치는 주성·HPSP 2행을 따로 해석한다. 재기동 이후 terminal 기록이 있는 87행, 진행 중 5행, 재기동 이후 claim되지 않은 1,259행으로 합계가 일치한다. 큐는 누적 발견 후보이며 1,351종목이 동시에 실수신·기계평가 중이라는 뜻이 아니다. 현재 PID 이후 claim 시각을 가진 행은 90개이며 이전 PID의 `last_result`/`machine_action`을 현재 성공으로 전용하지 않았다.

[105개 terminal 전수표](../../tmp/restart-health-check-20261013/probe-terminal-census.csv)의 보존식은 다음과 같다.

| terminal | 횟수 | 해석 |
| --- | --- | --- |
| source_unavailable | 97 | route snapshot 없음 63, 0B age 초과 13, 0B 없음 9, native stale/absent 12 |
| pattern_not_matched | 2 | 실제 native FALSE 근거. 전체 후보의 정상 평가나 경제적 no-edge가 아님 |
| observation_incomplete | 2 | 원 residence 종료 시 confirmation pending |
| active_conflict | 4 | 이미 존재하는 HPSP Main 대상과 중복; 추가 등록/실행하지 않음 |

해당 terminal 집합에서 완전한 비상시 machine `assessed`는 0이다. 따라서 원천부터 기계·보조까지 전 종목 정상이라는 결론은 금지한다. 거래가 적거나 해당 route의 수신 기대가 미확정인 종목의 무수신을 broker 거부·회선 장애로 단정하지 않는다. source gap은 그대로 보존한다. 남선알미늄 008350의 terminal은 원 residence deadline보다 약 24.48초 늦게 기록됐고 WS wait는 173,631ms였다. 기록·실제 worker 종료·cleanup을 합쳐 한 원인으로 확정하지 않았으며 원 60/150초와 슬롯 5/long 2를 확대하지 않았다.

## 원인과 수리

1. **비연속 시간초과가 연속 실패로 누적되는 회로 결함.** 삼성전자에서 정상 HTTP 응답 사이에도 최종 native 경로 무효화가 발생했다. 원 응답의 frozen input/schema/citation 검증과 live execution 검증을 합친 `semantic_validation_status`만으로 회로 성공을 인정해, 정상 응답이 앞선 시간초과를 끊지 못했다. 이제 원 응답을 issued input에 독립적으로 검증한다. CLOSED 회로는 원 기한 안의 유효 응답으로 전송 실패 연쇄를 종료하고, 최종 진입 WAIT 및 source/quote/order guard는 유지한다. OPEN/HALF_OPEN 회복은 기존 유효 native 신호·원 기한·단일 ticket·세대·미종결 Future 조건과 최종 execution 검증까지 요구한다. 별도 `entry_auxiliary_response_contract_valid/errors`, `entry_post_response_execution_valid`를 trace와 pending outcome에 함께 보존한다.
2. **응답 뒤 중복 정적 검증.** fresh post-provider `verified_evaluation` 경계를 새로 열고 기존 loader가 발행한 immutable view 및 동일 PID 소비가 확인된 경우에만 기존 prepared v6 claim validator를 사용한다. pointer/source/registry/overlay/revocation/backend generation/scope/ref/native freshness를 재검증하며, 조건이 없으면 원 validator로 돌아간다. 준비 상태나 원 신호를 Provider I/O 너머로 캐시하지 않는다. 경계 중 원천 교체는 WAIT이며 실패 뒤 BUY 재시도하지 않는다. 원 5초와 Provider/model/prompt/schema bytes는 유지한다.
3. **저장 준비의 잠금 경합 오분류.** JSONL generation lock은 nonblocking flock의 `BlockingIOError`를 `OSError(jsonl_generation_lock_busy:...)`로 감싼다. 준비 소비자가 바깥 유형만 다르게 보아 정상 대기를 `trace_dedup_prepare` 실패로 집계했다. 이제 exact marker와 typed cause가 모두 맞는 경합만 pending으로 처리하고 해당 cache를 무효화하며 다음 index 준비를 계속한다. 다른 디스크·권한·parent/descriptor 오류는 계속 실패한다. 17:23 snapshot의 준비 실패 5회와 달리 append 실패 카운터는 0이며, 원장 손실을 입증한 사건으로 과장하지 않는다.
4. **보고서 경고의 원인·날짜 투영.** 10/13 machine/auxiliary의 자체 hash는 유효했고 실제 결손은 `continuous_reversal_execution_not_completed:main_machine_policy`였다. notifier의 generic fallback이 이를 해시/계약 오류처럼 표시했다. 실제 원인과 읽은 파일의 byte generation을 보존하도록 수정했다. 날짜별 machine/auxiliary 의미 판정을 추가해 당일 경고와 전일 incumbent 검증 성공을 동시에 읽을 수 있게 했다. 당일 stage terminal을 생성하거나 경고를 억제하지 않았다. 16:45/16:55의 holding 경고와 17:23의 `valid_empty`는 별도 시점으로 보존한다. holding 신호 0을 자연 청산·손익 성공으로 보지 않는다.

17:23 회로는 OPEN/실패 6회였고, **새 코드가 배포되지 않은 상태**의 17:52 자연 재확인에서는 CLOSED/실패 3회였다. 이 회복은 이번 수리 효과가 아니다. 실제 Provider 지연은 여전히 원 5초 안에 완결을 보장하지 못한다. 이번 수리는 전송 실패의 잘못된 누적과 중복 로컬 작업을 다루며 외부 응답시간·진입·경제성 개선을 완료로 주장하지 않는다. 지연 개선 방향의 참고는 [OpenAI 공식 지연 가이드](https://developers.openai.com/api/docs/guides/latency-optimization)이며 live prompt/모델/출력 한도 변경 근거로 전용하지 않았다.

## 리뷰·검증과 인계

리뷰 범위의 수정 파일은 기존 AI transport circuit/engine, trace writer, v6 claim validator, artifact detector와 해당 tests다. 신규 engine-root Python module은 없다. 기존 작업본 변경은 [수정 전 사본](../../tmp/restart-health-check-20261013/before/src/engine/ai_engine_openai.py)을 기준으로 보존했다. hard safety·Main/manual custody·퇴역 owner·Provider 및 threshold 권한 누출을 확인했으며 해당 수정 범위에 미해결 code finding은 0이다.

- 관련 regression 600개 PASS: `test_runtime_policy_evaluation`, `test_ai_decision_trace`, `test_reversal_extended_policy`, `test_entry_transport_circuit`, `test_ai_engine_openai_transport`, `test_error_detector_artifact_freshness` 530개와 `test_reversal_auxiliary_wire`, `test_joint_reversal_source_repair` 70개. 실제 flock 경합, 원천 교체·native 무효화, recovery의 late/malformed/native-invalid, 실제 `analyze_target`의 정상 응답 뒤 경로 무효화 5회, trace/pending 보존을 포함한다. missing terminal 원인·byte generation 보완 뒤 해당 2개 case도 다시 PASS다.
- Python compile 및 `git diff --check` 검증. 문서 link/owner/authority와 print-only parser를 검증한다. shell/cron 변경은 없어서 `bash -n`은 해당 없음. 실 Provider·broker 호출, 무거운 보고서 재생성, 외부 sync, 배포·재기동 및 경제성 검증은 실행하지 않았다.
- 현재 체크리스트 bytes SHA256 `0082135a43f6cade7c9fdb8695e018ce96f8004d2643286f2d140fa446ae86c8`를 유지했다. 현재 소비된 intraday handoff의 public `verify/consume`이 이 문서를 frozen source로 검사하므로 무단 편집으로 Main을 막지 않는다. 이 보고서는 새로운 OPEN ID·주문 권한을 만들지 않는다.

현재 [10/13 checklist](../checklists/2026-10-13-stage2-todo-checklist.md)의 기존 8개 OPEN 인계는 다음과 같다.

| 기존 owner | 현재 상태·다음 closure |
| --- | --- |
| DirectFamilyPreopenPolicyHandoff | 당일 부모/PID 소비 확인. 이번 코드의 불변 릴리스 및 **변경된 v6 code pin의 code-only handoff**는 후속 배포 권한 아래 따로 검증해야 함 |
| AuxiliaryCircuitRecoveryRepair1012 | 이번 회로·응답/실행 분리 code 수리 검증 완료. 새 PID에서 원 기한 내 자연 request→response→Main terminal 및 실제 timeout 연속성 확인 필요 |
| NonfixedDispatchReadinessReview1012 | 전수 census와 5개 진행 슬롯 확인. fresh exact route→native→machine의 자연 terminal과 늦은 residence/cleanup 확인은 OPEN |
| DirectFamilySourceRepairMainMechanisticEntry | 당일 보고서 hash 유효와 실행 terminal 부재를 분리. 정규 장후 terminal→정책→consumer closure 필요 |
| DirectFamilySourceRepairCompactAuxiliary | 같은 원천·응답·정책 계약의 정규 장후 closure 및 자연 보조 호출 검증 필요 |
| DirectFamilySourceRepairEntryCancelWait | 현재 손실/체결을 합성하지 않음. 기존 native 원천·terminal·cost 대사와 정상 장후 owner 수용 유지 |
| DirectFamilySourceRepairEntrySplit | 실제 제출 원천·paired source gap 수용 유지; 이번 수리로 sizing/economic 완료하지 않음 |
| MainMarketWeaknessPostcloseObservation1008 | WR0–WR5 및 야간 연구는 이번 runtime 결손 수리에서 실행하지 않음. 기존 계획/허용 슬롯과 별도 수용 유지 |

운영 다음 단계는 기존 owner의 reviewed code handoff 후 새 PID에서 자연 증거를 대사하는 것이다. 누락 tick·fill·terminal·비용·PnL을 소급 합성하거나 회로/시간/가드를 수동 완화하지 않는다.
