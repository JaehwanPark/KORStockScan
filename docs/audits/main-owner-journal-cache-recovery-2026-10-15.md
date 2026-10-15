# Main 주문 소유권 원장 캐시 경합 수리 — 2026-10-15

16:11:14 경보의 원본을 보존하고 확인된 공통 원장 장애를 수리한다. 기존 통합 배포·재기동 승인의 결함 보완 범위이며, 주문·수량·수동 이관·hard safety 정책은 변경하지 않는다. 소유자는 `DirectFamilyPreopenPolicyHandoff`, `DirectFamilySourceRepairEntryCancelWait`, `AuxiliaryCircuitRecoveryRepair1012`를 재사용한다.

## 원인과 분리된 관측

16:05:49 두산034020 주문0057428 / intent a7d44d131778484daa9777e22c9aef26 / Main49267의 원장1528행은 실행142564, 체결1주·62,600원이다. 1529행 ORDER_TERMINAL은 직전 체결을 건너뛰어1527행을 참조하고 체결0을 복사했다. 각 원본 행 자체의 해시는 유효하지만 물리적 체인은 깨졌다. 캐시 식별자와 내용을 별도로 게시하는 중 동시 reader/writer가 새 식별자와 이전 내용을 결합하는 경합을 결정적 스레드 시험으로 재현했다.

이 장애로10/14 cancel_wait 보고서의 ancestor 검증과 삼성전자49266·두산49267의 Main 보유 관리가 fail-closed됐다. 주성036930의 기존 auto_hard_stop_handoff 수동 이관은 별도이며 유지한다. 16:11 observer의 scanner 식별0/fixed53 및 원천·trace/pending 진단은 원장 손상과 구분한다. 16:43 정규 artifact_freshness는 warning으로 바뀌었지만 process_health는 실제 원장 장애로 fail이었다. 과거 경보와 원천 부족을 지우거나 임계값을 완화하지 않는다.

## 구현·검증

캐시는 식별자·불변 내용을 한 tuple로 게시한다. 기존 원장은 변경하지 않고, 동일 intent의 기존 ORDER_BOUND→FILL_RECORDED(full)→stale ORDER_TERMINAL만 검증하는 명시적 복구 기록을 append한다. 전체 원본 byte SHA, 선행/체결/종료 event hash, 계좌·owner·종목·주문·수량·시각을 결속한다. partial/SELL/retired/다른 주문/unknown history/변조된 receipt는 거부한다. 자동 receipt 경로는 복구를 실행하지 않는다.

코드 위치는 공통 주문 저장 계약의 `src/trading/order/owner_journal_recovery.py`, 회귀 시험은 `src/tests/test_owner_journal_recovery.py`다. Kiwoom wire 요청·응답·FID·재접속 의미는 수정하지 않는다.

캐시 경합·원장·Main/manual 퇴역 경계·체결/보유 복원·cancel_wait·주문 receipt 회귀411개 PASS. Python compile 및 diff 검사 PASS. 실제 원장 사본은 원본1,529행을 모두 유지한1,530행으로 검증했고, 기존 체결1주·금액·execution_no·원 체결 시각을 복원했다. 선택본의 native custody 환경에서 동일10/14 보고서는 `source_invalid / cancel_wait_reconciliation_ledger_invalid`에서 `incumbent_carry / findings=[]`로 복구됨을 격리 검증했다. 원 보고서·checkpoint·과거 손익을 재생성하지 않았다.

[원본 경보·원장·시험·사본 검증](../../tmp/postrestart-alert-20261015-1611/)을 보존한다. 배포 전 코드 리뷰는 해당 범위의 미해결 결함0이다. 실원장 append 및 ordered 배포·새 PID 소비·현재 보유 관리·정규 detector 수용은 실제 실행 영수증으로 후속 기록한다. 자연 신규 주문 성공·경제성 개선은 이 수리의 검증 결과가 아니다.
