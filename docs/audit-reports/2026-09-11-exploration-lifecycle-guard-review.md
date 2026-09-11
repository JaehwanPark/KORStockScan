# 9/11 탐색 진입 제한 보완 및 hard-stop 이관 리뷰

사용자 요청: 11시 모니터링에서 확인한 결함 보완과 반복 코드리뷰. 선택 release와 운영 state를 보존하고 별도 branch `fix/exploration-lifecycle-20260911`, worktree `/home/ubuntu/KORStockScan-worktrees/exploration-lifecycle-20260911`에서 수정했다. base `badfb232`; main 선택 release486b9cc2/PID165934에 대한 배포·재기동·env/주문/제외 파일 변경은 이번 수리에 포함하지 않았다.

## 수정과 재리뷰

1. `src/engine/sniper_state_handlers.py`의 `_clear_superseded_entry_setup_exploration_arm`: HOLDING/SELLING, 보유수량, 제출 주문번호/bundle 또는 잔여 주문 제출 중인 lifecycle은 새로운 비탐색 AI 판단으로 기존 탐색 제한을 삭제하지 않는다. 아직 제출 증거 없는 arm의 정상 교체는 유지한다.
2. 같은 파일 `can_consider_scale_in`: 탐색 원본 두 marker·정책 mode·terminal abort 사유를 직접 확인한다. 일반 금지 플래그가 소실되거나 recheck/시간창/cooldown 예외가 있어도 탐색 lifecycle의 추가매수를 허용하지 않는다. 기존 공통 게이트의 owner/사유와 일반 scale-in 경로를 유지한다.
3. `src/engine/scalping/entry_split_order_plan.py`: 이미 bundle ID가 있다는 이유로 누락된 terminal 금지 플래그 복원을 건너뛰던 경로를 수정했다. 원장의 탐색 terminal 또는 명시적 금지 상태를 복원하며, 종목뿐 아니라 양쪽 target ID가 명시된 경우 같은 holding인지 대사한다. 다른 target이면 state를 수정하지 않는다.

초기 신규 테스트의 pytest import 누락을 수정했다. 이후 직접 producer/consumer, 일반 probe 복원·원장 귀속·scale-in gate·잔여 제출 단계를 재리뷰했고, 마지막 보완으로 residual submitting 등 in-flight 단계의 arm 삭제도 막았다. 변경한 코드 범위의 미해결 finding 0. 저스템 실제 과거 호출에서 어느 시점에 플래그가 소실됐는지는 코드 반례와 별개이며 확정 인과로 보고하지 않는다.

## 아이씨티케이 판정 보완

[7/14 체크리스트](../checklists/2026-07-14-stage2-todo-checklist.md)의 15:19~15:21 기록에서 hard-stop 수동관리 이관의 명시적 사용자 승인, enabled=true/retry5초 및 rollback=false를 확인했다. 9/11 현재 PID의 같은 env와 10:56:37 자연 이관은 이 코드 계약과 일치한다. 브로커가 매도를 거절한 사건이나 무승인 코드 실행으로 단정할 수 없다.

기존 `test_hard_stop_manual_handoff_runs_before_avg_down_and_broker_sell`도 통과했다. 따라서 정상 정책을 결함으로 오인해 자동 매도를 켜거나 제외 파일을 지우지 않았다. detector FAIL은 현재 개별 보유의 명시적 operator source가 없다는 별도 소유권 확인 문제다. 과거 정책 승인과 지금 사람이 실제 관리를 인수했다는 증거는 동일하지 않으므로 감시 경보를 숨기거나 PASS로 낮추지 않았다. 정책 의도를 바꾸는 수리와 구분해 기존 Runtime owner에 잔여 인수 확인을 남긴다.

## 검증과 잔여

- 추가매수 전체 테스트: 1,054 passed.
- probe 복원 및 process-health 전체 테스트: 127 passed.
- 마지막 in-flight 보완 후 관련 테스트: 25 passed / 1,105 deselected.
- 변경 Python compile 및 git diff --check 통과. 문서/체크리스트 print-only parser 통과.
- 로그: `tmp/exploration-lifecycle-review-20260911/`. API 호출·운영 산출물 재생성·실주문 없이 격리 worktree 테스트했다.

기대효과는 탐색 1주의 의도하지 않은 잔여 확대·추가매수 차단과 재기동 후 동일 제한 보존이다. 제출한도100, AI BUY 판단, 정상 신규 진입·일반 추가매수의 경제성 정책은 변경하지 않았다. 수익 증가 자체를 입증한 것은 아니다.

상태: code_review_closed / deployment_pending / natural_acceptance_pending. 선택 release 반영과 새 PID 소비는 별도이며 현재 이미 늘어난 저스템 보유를 자동 축소하지 않는다. 기존 RuntimeEnvIntradayObserve0911/CodeImprovementWorkorderReview0911에서 검토 코드 배포, 동일 lifecycle 제한 소비, 과거 원인 및 ICTK 수동관리 인수 확인을 이어간다. 새 경제성 표본을 코드 수리 완료의 조건으로 붙이지 않는다.

## 사용자 승인 배포·재기동 완료

후속 사용자 “배포 재기동” 승인에 따라 선택486b9cc2를 base로 검토된4파일만 합친 새 고정 release `/home/ubuntu/KORStockScan-runtime-releases/exploration-guard-20260911`, commit `e2388dbbda6fc3ac50e7a830f0b3ba7ee77b4b51`을 생성했다. 최종 release에서1182 tests PASS, 변경 diff 검사 후 commit하고 공유 경로를 구성했다. 원 worktree의 미커밋 수정은 검토 원본으로 남아 있고 운영 선택은 이 새 commit이다.

예약 장후 chain 실행 없음 확인 후 selector 원본/공유 제외 파일을 백업하고 원자 교체했다. cron9 routing 및 restart print-plan PASS. canonical `bash restart.sh`를 통해165934 정상 종료→drained supervisor 교체→PID222866 기동. 새 PID cwd/root/dirty=false, 당일 runtime verify PASS/missing family0/PID mismatch0/missing0. V2.14 두 budget env100, quota5 유지. 기존 hard-stop manual handoff=true 정책과 별도 widget/episode 배포는 변경하지 않았다.

11:12:07 broker 전: 삼성25/뉴로메카1/저스템2/ICTK1, 미체결0.11:13:50 후: 삼성25/뉴로메카1/ICTK1, 미체결0. 저스템 차이는11:13:45 기존 scalp_trailing_take_profit의 SELL0036607/2주 전량 체결 및11:13:46 sell_completed로 대사했다. 재기동을 잔고 불변으로 보고하지 않으며 이 매도를 추가매수 제한 수리의 수익 개선으로 귀속하지 않는다. gross+0.82%는 exact 비용 차감 순이익과 별개다. 자동 수량 축소 명령·수동 주문은 실행하지 않았다.

새 collector0B3898/0D4307 callback, worker/writer error0, healthy_observer_canary 확인. code_review_closed/selected_release_updated/actual_pid_consumed 완료. 개별 탐색 lifecycle의 다음 자연 제한 효과와 경제성은 별도 acceptance다. ICTK 수동관리 인수 확인은 남아 있으며 이 배포로 detector의 소유권 경보 해소를 주장하지 않는다.

배포 receipt `data/runtime/exploration_guard_deployment_20260911.json`, 검증/원장/WS/rollback 근거 `tmp/exploration-deployment-20260911/`. 이전 release486b9cc2를 보존했다.
