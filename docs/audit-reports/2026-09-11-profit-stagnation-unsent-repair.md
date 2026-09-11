# 삼성 위젯 보조 익절 미전송 기록 결함 보완

- 검토 시각: 2026-09-11 10:02 KST.
- 사용자 지시: 보조 익절 결함 점검·보완, 코드 리뷰와 수정보완 반복.
- 10:02 판정: 코드 수리 및 검토 완료, 당시 미배포. 이후 사용자 승인 배포·재기동은 아래 10:09 receipt를 따른다. 자연 보조청산 성과는 별도다.
- 수리 branch: `fix/profit-stagnation-unsent-20260911`, base `18231b18d949cd458de719fb063da5fc038bb79d`. 별도 worktree에서 수정·테스트했고 선택 release source, policy pin, 주문 원장은 수정하지 않았다.

## 실제 근거와 원인

9/11 삼성 위젯의 동일 진입 신호 `005930:2026-09-11:ENTRY:KRX_REGULAR:2026-09-11T09:07:43.978108+09:00`에는 09:07:44의 확정 `NOT_SENT` 0주와 후속 주문 `0014018`의 `FILLED` 1주가 함께 있다. 전자는 악화보류의 `SOURCE_UNAVAILABLE`로 전송 전 차단되고 예약이 해제된 기록이다. 후자는 259,000원 매수이며 원 목표 주문 `0014048`로 260,500원에 매도됐다. 목표 주문의 terminal과 매도 금액 후행 결속은 `order_owner_registry.jsonl` 740~741행이다.

`profit_stagnation_owners.widget_symbol`은 같은 신호의 모든 BUY 이력을 `safe_buys`로 검사했다. 확정 미전송 기록도 검사 대상이므로 정상 체결분이 있어도 후보 평가 전에 차단됐다. `target_ratchet.widget`의 매수 분모와 최종 pending-BUY 검사에도 같은 결함이 있었다.

원본 상태를 읽기 전용으로 대사한 SHA256: `0c47c7fa4abc252e794194ac3144abae32cd22d114dc036f203e0dfc0ae25676`. 대사 결과는 이전 분모 `[NOT_SENT 0, FILLED 1] / safe=false` → 수정 분모 `[FILLED 1] / safe=true`다. 이는 보유 입력 분류 재현이며 과거 시장 흐름·180초 정체·수익 조건을 재평가하거나 과거 보조청산 성공을 생성한 것이 아니다.

당시 선택 machine root `machine-owner-scope-20260911`과 workspace의 두 수리 대상 source hash는 수정 전 일치했다. 승인 보조청산 policy pin `aa2d47945590d48dde89875d8873d01387e24f66c48f65b99b8d98ec740e3ceb`도 실제 진입 시각·09:10 시각을 넣은 읽기 전용 loader 검증에서 유효했다. 전체 widget state의 마지막 `profit_exit_policy_status`는 여러 symbol 호출이 덮어쓰므로 삼성의 당시 정책 실패 증거로 사용하지 않았다.

## 수정 및 리뷰 반복

1. **재현:** 기존 owner-loop fixture에 동일 신호의 확정 미전송 기록을 추가하면 정상 보유분의 보조청산이 시작되지 않는 회귀 테스트 실패를 확인했다.
2. **Pass 1:** 기존 `profit_stagnation_owners.py`에 공통 보유 입력 필터를 추가했다. `NOT_SENT`, `ENTRY_ADVERSE_NOT_SENT`, 명시적 미전송·미접수, 빈 주문번호, 정수 체결0, null 체결가가 일치하는 기록만 제외한다. `_submit`은 예약 해제 실패 시 `AMBIGUOUS`를 남기므로 제외되지 않는다. 같은 신호의 접수 대기·부분체결·미확정 기록은 원래 검사에 남는다. 실제 체결분만 기준가격·수량·진입시각을 결정한다.
3. **Pass 2:** 목표 상향의 초기 보유 분모와 최종 주문 전 pending-BUY 검사도 공통 필터를 사용하도록 보완했다. 접수/체결금액/원장 bind/미해결 원장 오류의 모순 및 필수 필드 누락은 제외를 금지한다. 신호 ID 결손은 다른 이력과 결합하지 않는다.
4. **재리뷰:** 원장 reservation release → owner journal → 정체 관찰 → 원 목표 취소확정 → 보조 SELL → 복구/terminal의 직접 consumer를 점검했다. 목표 상향의 1회 정정·재실행 중복 방지·pending claim 복구도 확인했다. 이 수정 범위의 unresolved P0~P2 finding은 0이다.

보조 익절의 180초·변동/고점·양수 순이익·fresh 전량 bid·TTL/관측공백, 실제 order/custody owner, 진입 수량과 원 목표, 정책 유효기간·pin은 변경하지 않았다. main 및 episode 진입/청산 계산을 새로 변경하지 않는다. 원래 실패/미전송 row도 삭제하거나 정상 체결로 바꾸지 않는다.

## 검증과 후속

- `test_profit_stagnation_exit.py` + `test_holding_target_ratchet.py`: **188 passed**. 확정 미전송 후 취소확정/보조주문, 목표 상향, 기존 진입시각 제외, 이력 보존, 모호함·접수·체결·금액 모순 및 원장 결손의 차단을 검증했다.
- `test_entry_adverse_owners.py`, `test_machine_adaptive_exit_owner_loop.py`, `test_machine_adaptive_exit_broker.py`, `test_machine_adaptive_exit_reducer.py`, `test_profit_stagnation.py`, `test_machine_profit_stagnation_deployment.py`: **431 passed, 2 skipped**. skip은 widget 전용/episode 전용 계약의 반대 owner fixture이며 실패·미실행 수리를 숨긴 것이 아니다.
- 합계 **619 passed, 2 skipped**. 테스트는 임시 원장과 fake transport를 사용했으며 실 broker/Provider 호출은 없다.
- Python compile 및 `git diff --check` 통과. 문서 print-only parser exit 0, 기존 `MachineProfitStagnationStartupAcceptance0911`의 파싱을 확인했다. 수리 코드 commit `830783b9`를 workspace에 통합했고 검증 worktree와 코드/테스트 4개 파일의 SHA256 일치를 확인했다.
- 기존 실행 owner: [당일 체크리스트의 MachineProfitStagnationStartupAcceptance0911](../checklists/2026-09-11-stage2-todo-checklist.md). 배포 승인·실제 consumer 적용 뒤 신규 자연 진입의 보조 익절 관찰/직접 차단 사유 및 target 전환·복구·수량 terminal을 대사한다. 이전 삼성 목표 익절 성공을 수리 효과로 귀속하지 않는다. 현재 보유나 주문을 임의 이관하지 않는다.

## 사용자 승인 후 10:09 운영 배포·재기동

- 승인: 사용자의 `운영 배포·재기동 하기 바람`. 변경 함수가 widget 전용이므로 `korstockscan-widget-signal-auto-trader.service`만 새 root에 연결했다. main·Samsung episode·저가주 episode의 코드 선택/기동은 이번 수정 대상이 아니다.
- 신규 root: `/home/ubuntu/KORStockScan-runtime-releases/widget-profit-stagnation-20260911`, commit `a2e14f5d300972a5ada86d6025a2951a4916dd58`. 직전 운영 `e0116f6d`에서 검토된 source 2개와 테스트 2개만 반영했다. source/deploy clean, 검토본과 4개 파일 hash 일치, 신규 root의 직접 테스트 **188 passed**를 확인한 뒤 공유 data/logs/tmp/.venv/docs/restart.flag를 연결했다.
- systemd: 기존 96 drop-in 뒤 `97-widget-profit-stagnation-repair.conf` 설치. 10:08:16 PID34176의 SIGTERM 종료 및 process 소멸, lock 비점유 확인. 10:08:44 서비스 start → 새 **PID144180**. `Result=success`, `ActiveState=active`, `SubState=running`, `NRestarts=0`. 실제 cwd/PYTHONPATH가 신규 root와 일치한다.
- 전환 전·종료 후 widget 3개 symbol의 해당 매매분 보유0/미체결0, 보조 exit/정정 claim0을 확인했다. 재기동 후 삼성 기존 주문 이력6개 및 다른 두 symbol의 주문 이력은 동일하다. 원장 초기화·주문 취소·수동 매매는 실행하지 않았다.
- 시작 receipt verifier: `passed=true`, findings0, 새 PID144180, exact date9/11 및 owner-policy 파일/보조 익절 pin을 대사했다. effective-config SHA256 `6e75c75fce0302c038b635583398879f5784f795afc762830c3310f70fd9eff3`과 loaded-execution-policy hash는 재기동 전후 동일하다. 시작 receipt는 이후 자연 청산 성공의 증거가 아니다.
- 실제 PID의 보조 익절 `aa2d4794…`, 악화보류 `1536dfab…`, 목표 상향 `d455951e…` PATH/SHA256을 원 파일과 검증했다. 오늘 신규1주 코드 및 원래 정책·guard를 유지했다. 공통 selector와 cron은 전환 전 hash/본문 그대로다.
- 원장: `data/runtime/widget_profit_stagnation_repair_deployment.json`. 기존 machine profit/additions/one-day-quantity/owner-scope manifest에 widget unit override와 successor pointer를 남겼다. 과거 설치 receipt는 보존했다.
- 백업: `tmp/widget-profit-stagnation-deployment-20260911/`에 직전 unit/manifest/selector/cron, 정지 시 state/registry/startup receipt, 새 root source hash 및 검증 결과를 보존했다. rollback은 새97 drop-in을 제거하고 직전96 root로 연결하는 범위이며, 새 pending 청산/정정이 있다면 해당 successor terminal 또는 원 목표 복원 대사 전에 이전 코드로 되돌리지 않는다. 이후 발생한 state·주문을 과거 백업으로 덮지 않는다.
- 잔여: 실제 새 신호에서 보조 익절 관찰→조건 충족 또는 직접 차단→전환/복구→수량 terminal·비용 순이익은 기존 owner OPEN이다. 기존 삼성 09:25 목표 익절을 배포 후 수익으로 재귀속하지 않는다.
