# 2026-09-11 장중 모니터링 — 15:20

- 대상 거래일: `2026-09-11`
- 관찰 구간: `2026-09-11 14:47~15:20 KST`
- 판정: `RED — main sell-timeout state race active; broker exposure reconciled`
- 실행 범위: 장중 지시문의 현재 시각까지 due 점검, runtime/source/broker 읽기 전용 대사, 허용된 결함의 격리 수리와 review gate

## 판정

메인 봇은 계속 가동됐고 실제 매수·매도와 broker reconciliation도 성공했지만, 매도 완료 뒤 새 `WATCHING` 행을 과거 `SELL_ORDERED` timeout 작업이 다시 취소 경로로 보내는 상태 경쟁이 15:20 이후까지 반복됐다. 취소 의도 영속성 guard가 broker 호출 전에 이를 차단해 중복 취소·중복 매도는 없었다. 그러나 현재 PID에는 수리 코드가 반영되지 않았으므로 운영 결함은 해결되지 않았다.

## 메인 거래와 오류 인과

- 자이에스앤디 `317400`은 14:43:44 KRX 1주 probe 주문 `0052952`가 제출됐다. holding 중 관찰 수익률은 `-1.02%~+1.00%`였고, trailing 경로가 14:59:32 이익을 확정해 매도 주문 `0054514`를 제출했다.
- 14:59:41 매도 1주가 11,470원에 terminal 처리됐다. exact reconciliation은 순손익 `+44원`, 수수료·세금 `26원`, slippage `0`, `broker_reconciled=true`다.
- terminal receipt가 기존 행 `42977`을 완료하고 새 감시 행 `43185/WATCHING`을 만들었지만, 그 전에 dispatch된 40초 sell timeout handler가 동일 mutable object를 계속 사용했다. 이 handler가 완료된 주문의 cancel intent를 행 `43185`에 쓰려 했고 `pending_submit_flag_missing`으로 차단된 뒤, 실패 복구 코드가 새 행을 `SELL_ORDERED`로 되돌렸다.
- 15:20 error detector는 직전 scan 대비 두 로그 각 1건인 `UNKNOWN(2)` warning으로 표시했지만 이는 오류 소멸이 아니라 scan 간격별 증분이다. 같은 `SELL_CANCEL_INTENT_PERSIST_BLOCKED id=43185 code=317400`은 15:21에도 반복됐고 해당 로그의 누적 일치 행은 373건이었다. detector의 operational mutation은 0건이다.
- 15:20:52 broker 전시장 조회는 보유 `005930×25`, `456010×1`, 미체결 0건이다. `317400` 잔고·미체결이 없어 실제 매도 terminal과 일치한다. `456010×1`은 owner registry 밖 수동 remainder로 `balanced=true`이며 이번 main 오류와 무관하다.

## 수리와 코드 리뷰

다른 작업 창이 selector·재기동을 진행 중이므로 현재 release나 PID를 직접 변경하지 않았다. 기존 격리 작업본 `/home/ubuntu/KORStockScan-worktrees/scalping-unification-20260911`에서 다음을 보완했다.

- `handle_sell_ordered_state`가 dispatch 당시 행 ID와 `SELL_ORDERED` 상태를 고정하고 outbox 확인·시간 초기화·timeout 직전에 소유권을 재검증한다.
- `process_sell_cancellation`이 intent/ack 영속화, broker cancel 응답, terminal absence, 전시장 inventory, receipt ledger, DB interlock 전후에 동일 행 ID와 허용 상태를 확인한다.
- 상태 변경은 `ENTRY_LOCK` 안에서 소유권 확인과 함께 원자적으로 수행한다. 완료·revive로 행 ID가 바뀐 이전 작업은 새 행을 `SELL_ORDERED`로 되살리지 않는다.
- DB 보존도 `id + stock_code + SELL_ORDERED` predicate로 좁혔다.
- `WATCHING|COMPLETED` stale dispatch와 intent persist 중 completion/revive 경합 회귀 테스트를 추가했다.

첫 리뷰에서 network/broker 대기 뒤의 일부 mutation이 검사와 원자적으로 묶이지 않은 P1 결함을 발견해 보완했다. 재리뷰 결과 변경 범위의 미해결 finding은 0이다. `test_scalp_exit_safety_monitor.py`와 `test_profit_stagnation_exit.py`는 `146 passed`, 관련 compile과 `git diff --check`도 통과했다. 같은 작업본에 있던 KEPCO exact target fill price/time projection 수리도 그대로 보존했다.

## Runtime·source 상태

- 종료 시 main PID `363990`은 13:07:36 시작, `/home/ubuntu/KORStockScan-runtime-releases/unified-scalping-r2-20260911/src`, commit `57a90bd9` 세대에서 실행 중이었다. 선택 원장은 `weakness-guard-mount-fix-20260911`/`6936e8fd`까지 전진했으나 현재 main PID는 이를 reload하지 않았다.
- widget trader PID `474978`은 active/running, restart 0이며 선택 release 세대를 소비한다. 독립 episode의 오후 예약 service는 모두 terminal success이고, 저빈도 0B·adverse entry 차단은 사용자가 확인한 자본회전 보호 계약으로 유지했다.
- 15:15 BUY sentinel은 KRX `SUBMIT_DROUGHT_CRITICAL + LATENCY_DROUGHT`다. AI unique 219, budget unique 450, submitted 12이며 submitted/AI 5.30%, submitted/budget 2.60%다. 현금·orderable·position-cap 제외 계약은 유지됐다. refresh 336회 중 297회 적용, 60회 latency pass 회복, 11회 실제 submit 연결이 확인됐다. 잔여 첫 원인은 주로 spread/microstructure guard와 fresh AI DROP/WAIT이며 장중 threshold 완화 근거가 아니다.
- 15:20 WS report는 current snapshot usable, official master `verified/2604`, fresh 8·no_tick 16·stale 5다. subscription-state가 dashboard snapshot에 없어서 `order_ws_subscription_stale_repair_observability` 1건이 source-only `implement_now`로 남았다. 현재 PID process reflection이 없으므로 구현 존재를 runtime acceptance로 닫지 않는다.
- micro registration receipt는 15:20까지 대상의 0B/0D를 계속 갱신했다. observer `stop=false`, queue/drop/worker/writer error 0이고 free disk는 약 32GB다.
- scanner bounded BBO observer는 schedule 176 episode, exact BBO 151, terminal sample 128이나 전체 prune 모집단 coverage는 낮고 right-censor가 높다. 전수 EV로 외삽하거나 실주문 승격 근거로 쓰지 않는다.

## 체크리스트 대사와 다음 조건

- `MachineFillTelegramAcceptance0911`: 자연 machine 체결 delivery는 기존 4건 성공, 사용자 단말 수신과 20:00 종료 acceptance가 남아 `waiting`이다.
- `MachineProfitStagnationStartupAcceptance0911`: 14:35 자연 window는 끝났고 KEPCO fill/terminal은 확인했다. exact fill projection 수리는 `code_review_closed/deployment_pending`, 비용 경제성은 장후 owner에 남는다.
- `RuntimeEnvIntradayObserve0911`: main의 선택 release/PID 불일치와 active state-race 때문에 `overdue_unresolved`; broker exposure는 대사 완료다.
- `IntradaySourceQualityGateCheck0911`: 14:21 append 중 raw hash 변경 FAIL과 unknown warning은 그대로 보존한다. 15:20 WS source-only implement-now는 `CodeImprovementWorkorderReview0911` 및 `PostcloseSourceQualityGateReview0911`에서 직접 consumer를 확인한다.
- 16:30 이후 POSTCLOSE 항목은 종료 시각 현재 `not_yet_due`다. 현재 OPEN의 미분류는 0이다.

다음 안전한 적용 조건은 다른 창의 배포 generation 고정, 해당 consumer 무실행 구간, broker 보유·미체결 재대사, 검토 commit 반영, 우아한 main 재기동, 새 PID root/commit/runtime verify·WS first-data와 `317400` 반복 오류 중단 확인이다. 코드 수리 완료를 현재 runtime 반영이나 자연 경제성 완료로 표시하지 않는다.
