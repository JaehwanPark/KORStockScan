# 9/8 오후 수리 통합 배포·재기동 검증

사용자 지시: `커밋&푸시&main병합 후 우아한 재기동`. 기준 2026-09-08 KST.

## 배포 전 검토

이번 통합 범위는 Entry call-local parent/AI final-response provenance, 비용 결손 격리와 작은 수익 진단, census/scanner 진단, workorder→summary→strict verifier, Pattern Lab generation/bounded review, 기존 owner 정책 승계, 수동·기존 target 체결의 custody reconciliation 수리와 연결 문서다. 기존 수정자의 근거와 자연 acceptance는 관련 개별 리뷰에 보존했다. 실효 정책의 새 선택과 경제성 입증은 코드 배포와 별개다.

`korstockscan-review-gate`에 따라 직접 producer/consumer, source/date/hash, 실패·재시도, 명시적 OFF/manual veto, 독립 main/widget/episode owner, launcher/verifier/restart handoff를 통합 검토했다. 추가 P2는 새 전략 component가 NXT 세션을 `nxt`만 인정하여 실제 `nxt_entry_window|nxt_premarket|nxt_regular_overlap|nxt_aftermarket` 원천을 배제하는 문제였다. 원래 세션을 유지하는 공통 scope 검증으로 source/PREOPEN/runtime을 연결했고, 다른 세션·거래소·unknown의 적용은 계속 거절한다. 새 runtime authority나 현재 env 변경은 없다.

- 최종 48개 모듈 **4,084 tests PASS (105.22초)**. 앞선 3,714/319/31회 실행은 중복이므로 합산하지 않는다. NXT exact-session source→경제성→runtime 및 cross-scope 거절 회귀 포함.
- 전체 Black **905 files unchanged**, 영향 Python compile, launcher/postclose/restart `bash -n`, `git diff --check`, 문서 print-only parser 통과. 최종 시험 시작/종료의 source SHA256 대사에서 변경 0건.
- pandas Copy-on-Write deprecation 1건과 기존 멀티스레드 fork 테스트 경고 2건은 실패가 아니며 패키지를 변경하지 않았다. 계좌/주문/Provider를 실행하는 시험은 하지 않았다.
- 기존 main 0c294cba의 Black CI 실패는 pipeline summary 두 모듈 포맷으로 복구한다. 이 두 파일은 AST 동등·직접 테스트 확인 후 별도 포맷 커밋으로 분리했다. 나머지 포맷은 각 기능 수정과 함께 검증했다.
- 진행 중 다른 세션의 변경을 덮어쓰거나 되돌리지 않았다. 최종 소스가 고정되기 전의 테스트 결과로 새 세대를 승인하지 않았다. 로컬 운영 `data/runtime/symbol_owner_policy/owner_custody.env`, ignored raw/env/token은 커밋에서 제외한다.

통합 시험 이후 추가된 lifecycle 변경은 component 관측을 기존 행 검증 뒤로 옮겨 거절 행의 profile/context가 정상 원장을 오염시키지 않도록 한다. 해당 변경과 추가 안전 회귀를 검토하고 8개 영향 모듈 **829 tests PASS (22.46초)**로 재검증했다. 이 수는 위 통합 시험과 중복이므로 합산하지 않는다.

마지막 명시적 stock scope/순수 검증 보완까지 포함한 10개 영향 모듈 **2,082 tests PASS (80.70초)**, 전체 Black 905개 PASS, 최종 compile/diff/parser PASS이며 이 검증 중 소스 변경은 0건이다. 이전 회귀 실행과 중복 합산하지 않는다.

검토한 배포 범위의 미해결 코드 finding은 0이다. 전일 원천 결손, 오늘 자연 submit/fill/terminal/net, 다음 장후 strict generation과 9/9 PREOPEN 승계, 미관측 조건의 최초 후보 계약은 기존 OPEN owner에서 별도로 확인한다. 정책 승계의 최초 effective-date는 9/9이며 9/8 launcher 검증의 추가 export는 0건이다.

## 실행 상태

- 코드·리뷰 커밋 `c75eb507`, 후속 리뷰 `151b0e64`, 병렬 문서 커밋 `7681a8a6`을 일반 merge로 함께 보존했다. 원격 main 배포 커밋은 `6b4ac5e6c89597f250532a1f75610dcb1acb8bce`다. 병합 결과의 소스 hash 변경 0건·diff/parser PASS. [main Black CI](https://github.com/JaehwanPark/KORStockScan/actions/runs/34200280279) success, 두 릴리스 브랜치 CI도 success다.
- 16:40 `./restart.sh` 1회 정상 종료. 이전 main PID682672 종료 후 drained bot tmux supervisor만 새 launcher로 교체했다. 새 main PID **992430**, 시작 **16:40:06 KST**, source commit **6b4ac5e6**, `SOURCE_DIRTY=false`, launcher SHA256 `32efc0cc145b78db658357812113e51cb88a643374cd070d9a48b5a2cb481c85`다. Samsung morning handoff는 `morning_owner_not_active/not_required`로 정상 종결했다.
- 새 PID의 당일 runtime verify **PASS**, selected20, missing/mismatch/finding/정책·날짜 실패0. PREOPEN env SHA256 `f529bb62dd1c75579d2506017d479629aa41595b648805f3b4954795800ee6bc`와 custody env·주문 registry hash는 재기동 전후 동일하다. 정책 승계 9/9 effective date를 9/8로 당기지 않았다.
- 16:37:58 직전 vs 16:40:33 직후 KRX/NXT strict snapshot: 삼성전자30주·삼성중공업10주와 미체결 SELL0018672 10주, owner별 registry30/10, 충돌0이 동일하다. 16:15에 있었던 수동0062568은 **재기동 요청 전부터** 미체결 목록에 없었고 exact-date kt00007 이력은 체결0·잔량0이었다. 취소/만료의 구체 원인은 이 receipt만으로 확정하지 않는다. 자동 복원·취소·owner 흡수·수량 변경을 하지 않았다.
- 위젯 trader PID21846, Samsung heavy episode PID453121, collector PID665/663/660과 시작시각은 유지됐다. 메인 단일 PID, WS LOGIN ACK·신규0B/0D 수신, 16:40:27 이후 heartbeat와 모든 기록된 worker alive=true를 확인했다. 16:40 이후 main/WS/scanner/sync/execution 관련 error log 신규 오류0.
- 16:41:08 micro snapshot은 새 프로세스에서 0B339/0D524 callback, trade/depth writer 각1 alive, queue/worker/writer 오류0, stop 없음이다. 최소 callback floor 전 `warming_up`은 경제성 또는 전체 원천 수용 완료가 아니다. 16:41:17 등록26 item 중 exact0B+0D8/incomplete18은 venue별 자연 receipt로 보존하며 전 item 수집 완료를 주장하지 않는다.

- 16:42:18 재확인에서 micro는 `healthy_observer_canary`, 0B1395/0D2546, configured/alive writer 각각1/1, worker/writer 오류0·자동중지 없음으로 전진했다. 16:42:28 heartbeat와 단일 PID992430, 검증 소스 hash 변경0도 재확인했다.

배포·기동 검증은 완료했다. 자연 parent/cache/controller, 장후 strict generation, callback·exact-route 원천 수용, 9/9 PREOPEN 정책 승계와 비용 차감 경제성은 [당일 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 OPEN ID에서 계속 확인한다. 이 기록을 추가한 문서 커밋은 실행 소스와 별도이며 문서 반영만으로 두 번째 재기동을 하지 않는다.

로컬 증거: `/tmp/release-1610-final-tests.log`, `/tmp/release-1610-incremental-tests.log`, `/tmp/release-1610-code-freeze.json`, `/tmp/release-1610-parser-merge.log`, `/tmp/release-1610-restart.log`, `/tmp/release-1610-broker-prerestart.json`, `/tmp/release-1610-broker-postrestart.json`, `/tmp/release-1610-manual-order-prerestart.json`, `/tmp/release-1610-postrestart-ws.json`, `/tmp/release-1610-postrestart-micro.json`. 외부 Project/Calendar sync는 수행하지 않았다.
