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

## 실원장 복구·배포 영수증

- 배포 코드: `d05ebbf8770cb63b51a4ae57e9d2924de3fdf975`. 통합cfa070c1e/7b2e421e3/af2b8f994의 기존 변경을 유지한다.
- 실원장1,529행·원본 바이트 전체를 유지하고1530행에 복구 기록 `554b84028fee892111a5a1da3d59291943780289cb7c2953738f28a20513933d`를 추가했다. [실행 영수증](../../tmp/postrestart-alert-20261015-1611/live-recovery-receipt.json). 원장 inode와 과거 ancestor hash를 유지한다. 복구 인식 코드 이전으로의 rollback이나 원장 절삭은 금지하며, 후속 배포도 이 reader 계약을 보존해야 한다.
- 16:53:48 ordered transition complete/pass. 전임 PID2407222 정상 종료, 새 PID2470537/start11470048, cwd `/home/ubuntu/KORStockScan-runtime-releases/owner-journal-cache-recovery-20261015-d05ebbf87/src`. 정책·PREOPEN/env/current pointer·수동 제외 파일은 기존 bytes를 유지한다. 거래 규칙과 탐지 임계값은 변경하지 않았다.
- 실제 새 reader의 cancel_wait 검증은 `incumbent_carry / findings=[]`, 원 보고서 SHA `21c328a5c06e9da1c9fe8d75279bb7de02ba48ab10943073feae4eecf9b26d01` 불변이다. 과거 비용/source gap과 자연 경제성 수용은 OPEN으로 유지한다. [직접 소비 검증](../../tmp/postrestart-alert-20261015-1611/live-source-consumer-verification.json).
- 16:55:10 삼성전자49266·두산49267의 `main_stop_source`와 `scalp_trailing_mechanical_input` 자연 생성 재개를 확인했다. 주성49294의 기존 수동 이관 차단은 유지한다. [자연 사건 원본](../../tmp/postrestart-alert-20261015-1611/holding-natural-event-evidence.json).
- 16:55:33 새 코드의 정규 detector에서 process_health/log_scanner/resource_usage PASS, cancel_wait 원장 경고 없음. artifact_freshness는 첫 현재 세대 관측 대기 및 기존 holding_exit_sentinel_aftermarket_report stale의 warning이다. [최초 탐지](../../tmp/postrestart-alert-20261015-1611/detector-first-new-pid.json). 현재 세대 observer의 완료/동일 run 소비는 아래 최종 확인 영수증에 남긴다.

## 현재 세대 최종 수용

16:55:33.743684 observer는 새 PID2470537/start11470048·d05ebbf87을 관측했고, 정규 detector가 같은 run과 health projection을 소비했다. [배포15조건](../../tmp/postrestart-alert-20261015-1611/postdeploy-verification.json) 모두 PASS. 16:58:02 정규 탐지의 failure0, process_health/log_scanner/resource_usage PASS, 자동 보유 관리 차단0 및 기존 주성 수동 이관1 유지, cancel_wait 원장 경고 해소를 확인했다. 10/16 누적 등록 대기 원본도 불변이다. [최종 수용](../../tmp/postrestart-alert-20261015-1611/final-alert-acceptance-1658.json).

16:56:46에는 I/O wait38.66%≥35%의 일시적 resource_usage fail이 있었고16:58:02에 회복했다. 최초 경보는 삭제하지 않는다. artifact_freshness는 observer 원천 관측 부족과 기존 holding_exit_sentinel_aftermarket_report stale로 warning이 남는다. source coverage 전체 완료·과거 비용 복원·신규 자연 주문 또는 경제성 개선으로 확대 해석하지 않는다. 확인된 원장 캐시/체결 보존/실제 보유 관리 결함 수리는 종료하며, 기존 원천 부족과 holding 보고서 생성 실패의 수용은 기존 OPEN owner가 유지한다.
