# 비상시 호가 수리 배포 및 격리 정책 검증 — 2026-10-17

사용자가 배포와 격리 정책 읽기·스키마·코드 호환성 검증을 명시했다. 원 구현 `683c67d27`의 호가 전달·원 5초·물리 전송 계약을 유지하며, 운영 Main은 종료 상태로 둔다. 선택 릴리스와 실제 PID 소비를 구분한다.

최초 네트워크 차단·원 파일시스템 읽기 전용 namespace에서 128범위 next-session Main 정책의 schema/source와 수치·멤버십 불변이 통과했다. auxiliary reader compatibility receipt와 delay/holding/stop의 이전 코드 인계가 누락돼 첫 검증은 FAIL로 보존했다.

`automation.prepared_policy_code_handoff`는 기존 완전 검증된 prepared 원본의 내용 해시·동일 target·원 정책·정확한 코드 inventory 및 검토된 원/후속 소스만 결속한다. 원 controller/summary/Main candidate의 과거 바이트를 보존하여 다음 현재 세대의 발행과 혼동하지 않는다. 현재 delay/holding/stop 정책은 별도로 실제 파일을 검증한다. 숫자 successor, 정책 변경, 날짜 연장, 새 PID 소비를 승인하지 않는다. 신규 모듈 소유 위치는 자동화 인계 계약인 `src/engine/automation`이며 engine root에 추가하지 않았다.

실행 결과와 원 실패는 [배포 증거](../../tmp/nonfixed-quote-deployment-20261017/)에 보존한다. 실제 선택·새 prepared full verification과 최종 수용은 후속 결과에 기재한다. 새 TTL 선정은 요구하지 않는다. 이 기록은 휴장일 실제 호가/주문/체결 및 실현 성과 검증이 아니다.


반복 검증에서 native 요약 발행기가 원 frozen holding replay의 코드 세대를 새 코드로 재구성하려는 누락을 확인했다. 검증된 기존 incumbent carry는 정상 reader의 exact source/code handoff를 통과한 후 원 파일을 보존한다. 새로운 실제 source를 가진 current-code 발행은 기존 경로를 유지한다. source 변경·영수증 결손·numeric successor·다른 날짜는 허용하지 않는다. 관련 2,662개 회귀검사 및 static/diff 검증을 통과했다. 실제 활성화/주문 성과를 추가 수용으로 주장하지 않는다.


whole-native-chain 단계에서 과거 delay report의 code hash를 현재 코드와 직접 비교하는 마지막 소비자 누락도 확인했다. 전체 원천·ledger·날짜 검증을 유지하고, 동일 정책/원 코드 inventory를 가진 effective target의 검증된 prepared code handoff만 수용한다. source 변경·날짜 변경·영수증 결손·ledger 불일치는 계속 실패한다. 최종 관련 회귀검사 2,758 PASS이며 원 보고서와 정책 파일은 재선정/재작성하지 않는다.


체크리스트 소비자의 마지막 검토에서, 네 계열의 current fixture projection은 이미 verified인데 과거 raw contract의 unverified만 읽어 완료된 코드 작업 세 개를 재개하는 누락을 확인했다. 기존 검증된 report-only projection을 소비하도록 연결하고 경제성/원천 결손의 독립 owner는 유지한다. raw report와 summary의 과거 계약은 변경하지 않는다. 최종 관련 2,844 PASS 및 compile/name/diff 검증을 마쳤다.


## 최종 배포 및 수용

- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/nonfixed-quote-20261017-a41ebc84f`, commit `a41ebc84fab4021380166c474142aa7d0ae00da1`. 원 선택 `7f2552aed`와 원 정책/장후/시도 바이트는 [배포 증거](../../tmp/nonfixed-quote-deployment-20261017/)에 보존했다.
- 실제 selector 발행: `2026-10-17T10:14:26.065105+09:00`. 공유 파일의 사후 native 전체 검증은 `2026-10-17T10:16:11.953740+09:00`에 `current_full_contract` PASS/findings0으로 마감했다. 준비된 selector의 시간과 실제 발행 시간을 별도 영수증으로 구분했다.
- 격리 namespace에서 네트워크 차단·원 파일시스템 읽기 전용 및 검증 소유 출력/임시 디렉터리 복제본을 사용했다. Main/auxiliary/delay/holding/stop policy read·schema·code contract PASS. typed bootstrap은 provider_called=false, broker_called=false, order_submitted=false를 유지했다.
- 원 next-session Main 정책의 수치·멤버십 불변, native confirmation 128범위/76,800행/598hit, baseline/candidate signal SHA 일치·불일치0. 원 21개 구현 파일의 SHA도 유지했다.
- 관련 회귀 2,845 PASS. 네 current-generation fixture는 entry-cancel-wait133/rising86/auxiliary84/holding116 PASS이며 원 historical fixture를 현재 성과로 바꾸지 않았다. Python compile/name·문서 링크·print-only parser·diff 검증을 수행했다.
- 준비본의 env_overrides 전체와 delay/holding/stop/initial-quantity 영수증은 원 준비본과 같다. Root 활성 Main policy pointer와 live PREOPEN/env는 변경하지 않았다. 새 TTL, provider/수량/threshold/cap/주문 권한을 추가하지 않았다.
- native source16 summary→strict/controller DONE→target19 prepared 및 독립 전체 검증 PASS. 원 natural/economic/source gaps와 기존 6개 OPEN ID를 유지했다. code capability의 source report는 과거 unverified로 보존하고, 별도 현재 fixture 검증만 소비한다.
- actual_pid_consumed=false, 운영 Main/감독 프로세스 기동 없음. 다음 정규 10/19 PREOPEN07:35→Main07:55의 실제 활성화/PID 및 자연 quote/submit/fill/비용 성과는 기존 owner `DirectFamilyPreopenPolicyHandoff` 등의 미래 수용이다. 휴장일 검증으로 quote stale 미판정의 실제 감소를 주장하지 않는다.

[최종 배포 영수증](../../tmp/nonfixed-quote-deployment-20261017/deployment.json), [공유 파일 전체 검증](../../tmp/nonfixed-quote-deployment-20261017/published-native-verification.json), [격리 검증](../../tmp/nonfixed-quote-deployment-20261017/isolated-validation.json), [발행 원본/계획](../../tmp/nonfixed-quote-deployment-20261017/publication-plan.json)을 보존한다. 최초 누락·읽기 전용 scratch/lock 경계 실패·후속 코드 보완과 private native 시도도 각각 보존했다. 실제 정책/주문/자연 성과로 혼동하지 않는다.
