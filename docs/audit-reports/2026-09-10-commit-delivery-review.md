# 2026-09-10 전체 변경 Git 전달 검증

## 범위와 권한

- 사용자 요청: 전체 변경 커밋·푸시·main 병합. 시작 시 main과 origin/main은 `e718a1b3`으로 같았다.
- 기존 장후 복구, 별도 승인된 9/10 위젯·에피소드 변경, 보고서·체크리스트·추천 원장을 함께 전달한다. 이 Git 작업은 매매 재기동, 주문, 정책 재적용, 운영 보고서 재생성 또는 Project/Calendar sync를 실행하지 않는다.
- 이전 [복구 검증](2026-09-10-postclose-0909-recovery-review.md)의 운영 receipt와 코드 hash는 당시 증거로 보존한다. 이번 전달은 운영 YELLOW·자연 원천/정책/PID·경제성 잔여를 GREEN 완료로 바꾸지 않는다.

## Review gate 보완

1. 신규 checklist 테스트가 실제 현재 checklist까지 읽어 native ID를 중복 계수했다. 생성 fixture만 discovery하도록 격리하되 실제 parser와 ID 유일성 assertion은 유지했다.
2. finalization recovery 테스트가 실제 systemd 상태에 따라 missing predecessor를 failure 또는 waiting으로 달리 판단했다. 임시 controller와 systemctl fixture로 격리하고 failed/waiting 두 경로에서 cleanup 금지, detector source date, 사전 FAIL 필수 조건을 검증한다.
3. 9/10 profile 테스트 두 개가 Git에서 제외된 운영 candidate JSON에 의존했다. 임시 applied policy→report→candidate의 실제 producer/hash validator를 사용하도록 바꾸고, 미승인 비-baseline 정책 보존과 2회 revision 경유 검증을 유지한다. 운영 candidate를 고치거나 테스트용 source로 커밋하지 않는다.
4. traceability의 closed-window schema 표기를 실제 producer/consumer/runbook과 같은 `closed_exact_market_window_exclusion_v2`로 정정했다.
5. Black 26.5.1로 변경 Python 28개, 기존 main의 형식 불일치 21개, 검증 중 추가된 테스트 1개를 정리했다. 포맷 검사 대상 총57개 Python 파일의 AST 동등성을 검증했다(7개는 변경 불필요). 거래 판단·수량·guard·프로토콜 의미 변경이 아니다. 기존 검증 hash를 새 bytes로 소급 덮어쓰지 않는다.
6. 임시 lock 2개와 로컬 custody/state 백업 3개는 삭제하지 않고 Git 제외 규칙을 추가했다. 문서에서 참조하는 최종 72행 [intake 원장](2026-09-10-postclose-0909-recovery-intake.json)은 명시 allowlist로 포함했다. 커밋 후보의 비밀키 패턴 검사에서 발견 사항은 없었다.
7. 검증 중 작업트리에 추가된 PREOPEN source-evidence 보존 수정과 테스트도 포함했다. `_scrub_removed_contracts`는 hash-bound `sentinel_evidence`의 null/진단 필드를 deep copy하되 retired family의 상위 제거와 exact evidence validator는 유지한다. 원본 불변, 복사 분리, tampering 거절, retired authority 미복구를 검증했다. 실제 PREOPEN 적용은 이번 Git 작업의 실행 범위가 아니다.

## 검증 결과

- 최초 통합 실행: 1,284 PASS / 2 FAIL. 위 환경 의존성을 보완했으며 실패를 숨기거나 assertion을 제거하지 않았다.
- 보완 후 targeted regression: **1,386 PASS (165.94s)**. 부분 실행 81/104건 등은 중복 합산하지 않는다.
- 추가 PREOPEN/submit-drought consumer regression: **348 PASS (2.86s)**. 포맷 검사는 그 이후에도 별도로 수행한다.
- 최종 포맷 후 수정 테스트·PREOPEN 결합 회귀: **429 PASS (6.15s)**. 위 검증과 겹치므로 고유 테스트 수로 합산하지 않는다.
- Python compile, shell `bash -n`, 새 systemd timer 6개의 `systemd-analyze verify` 통과. 형식만 바뀐 기존 main 파일에는 AST 동등성·compile·Black 검사를 적용하며 별도 전체 trading 테스트 실행으로 표현하지 않는다.
- print-only parser: 전체30 / 현재9/10 checklist14. 외부 sync 및 sync token 검사는 하지 않았다.
- 최종 staged whitespace PASS, 전체 Black **961 files unchanged**, Python58/shell9/JSON6 compile·syntax·parse PASS. 이 문서는 커밋 전 검증 기록이며 실제 원격 반영은 Git commit/ref 대사로 별도 확인한다.
- 이번 Git 전달 보완 범위의 미해결 review finding 0. 과거 source loss·근거 차단 추천·실제 수익 acceptance는 기존 owner에 남긴다.
