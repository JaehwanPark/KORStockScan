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

16:26 검증 완료 시점: 커밋·원격 CI·main 병합·재기동 결과는 아래 실행 receipt로 후속 기록한다. 이 문서의 사전 검증만으로 기동 완료를 주장하지 않는다.

재기동 전 기준(16:15:32): KRX/NXT strict 잔고 삼성전자30주·삼성중공업10주, 미체결 SELL0062568(수동 정정 주문)30주와 SELL0018672(삼성중공업 episode)10주. registry는 widget30주/episode10주이며 주문 owner 충돌0. 수동0062568은 자동 registry target으로 추정 등록하지 않는다. 독립 매매 PID21846/453121, collector PID665/663/660을 유지해야 한다. 실행 직전에 다시 조회하여 최종 전후 대사한다.

로컬 검증 근거: `/tmp/release-1610-final-tests.log`, `/tmp/release-1610-black-final.log`, `/tmp/release-1610-code-freeze.json`, `/tmp/release-1610-baseline.json`, `/tmp/release-1610-units-before.txt`. 향후 자연 확인은 [당일 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 기존 OPEN ID를 재사용한다. 외부 Project/Calendar sync는 수행하지 않는다.
