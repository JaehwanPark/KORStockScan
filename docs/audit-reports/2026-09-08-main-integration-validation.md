# 2026-09-08 main 통합 검증

검증 기준: `2026-09-08 09:16 KST`. 요청 범위는 전체 변경의 커밋·푸시·main 반영이다. 운영 프로세스 재기동, policy/env 적용, 주문, Provider 호출 또는 장후 산출물 재생성은 수행하지 않는다.

## 판정

검토 대상 변경의 unresolved review finding은 0이며 아래 targeted validation을 통과했다. 이는 코드·문서 통합 판정이고 자연 산출물, PREOPEN 선택, PID 소비 또는 경제성 acceptance 완료를 뜻하지 않는다. 현재 작업 브랜치는 이미 `main`이며 원격 main과 분기 없이 시작했다.

## 변경과 재검토

- 장후 summary-generation/strict verifier/controller handoff, lifecycle/EV 귀속, 추천 native ID, 저가주 profile·preflight, Scanner/Daily 실현 순이익 승인과 PREMARKET census의 직접 producer/consumer 및 회귀 테스트를 검토했다.
- 기존 lifecycle/widget 테스트 12건은 호스트의 실제 owner policy/registry를 읽어 fake 주문이 차단되는 환경 의존성이 있었다. 두 테스트 모듈에서 임시 policy/registry 경로와 test account를 주입했으며 실제 resolver와 운영 guard는 대체하거나 완화하지 않았다. 이후 owner coexistence를 포함한 통합 회귀 검증을 통과했다.
- 순수 Black 포맷 변경 6개 파일은 HEAD와 Python AST 동등성을 확인했다. 포맷 전용 커밋에는 runtime report/cache를 넣지 않는다. 기능 변경 파일에 필요한 포맷도 적용하고 최종 전체 Black 검사를 통과했다.
- 검증 종료 후 source/deploy/document 76개 경로의 SHA256을 대조해 검증 도중의 별도 변경이 없음을 확인했다.
- 공개 저장소 반영 후보 147개 파일에 대해 private-key, GitHub/AWS credential, bearer token 및 긴 secret assignment 패턴을 검사했으며 검출 0건이었다. 패턴 검사는 비밀정보 부재에 대한 완전한 보증은 아니다.

## 검증 결과

| 검사 | 결과 |
| --- | --- |
| 수정 테스트와 직접 consumer 총 31개 모듈 | `2388 passed`, 211.49초 |
| 변경/new Python 46개 compile | PASS |
| 변경 shell 5개 `bash -n` | PASS |
| Ruff `E9,F63,F7,F82` | PASS |
| 전체 Black | 888 files unchanged, PASS |
| 문서 backlog print-only parser | 35개 task; 주요 자연 acceptance 7개 ID 각 1건 |
| frozen evidence JSON 4개 parse / v7 preflight evidence canonical hash | PASS |
| `git diff --check` | PASS |

pytest warning 1건은 `pandas_ta`의 pandas Copy-on-Write 옵션 deprecation이다. 전체 저장소 pytest 실행 결과가 아니라 변경 경로와 직접 consumer의 targeted suite 결과다.

## 커밋 경계

- 사용자 요청에 따라 기존 tracked 변경과 non-ignored 신규 코드·테스트·문서·report snapshot을 포함한다. 기존 수동 제외 목록의 comment 변경도 보존하되 이를 새 policy 적용으로 보고하지 않는다.
- 재현에 필요한 frozen review JSON 4개는 명시적으로 포함한다: `2026-09-07-low-price-recommendation-apply-evidence.json`, `2026-09-07-widget-episode-recommendation-ledger.json`, `2026-09-08-postclose-priority-repair-ledger.json`, `2026-09-08-widget-episode-application-receipt.json` (모두 이 문서와 같은 디렉터리).
- `data/runtime/symbol_owner_policy/owner_custody.env`와 그 밖의 ignored runtime 파일은 추가하지 않는다. 저장소 밖 `/home/ubuntu/.codex/skills/korstockscan-review-gate/`는 이 Git 커밋에 포함되지 않는다.
- 체크리스트의 기존 OPEN acceptance는 유지한다. GitHub Project/Google Calendar sync는 실행하지 않는다. 푸시 및 원격 CI 결과는 실제 완료 후 사용자에게 별도로 보고한다.

## 상세 근거

- [장후 우선 수리 리뷰](./2026-09-08-postclose-priority-repair-review.md)
- [위젯·에피소드 추천 구현 리뷰](./2026-09-07-widget-episode-recommendation-implementation-review.md)
- [소액 순이익 승인 리뷰](./2026-09-08-small-net-profit-approval-review.md)
- [Scanner·Daily 승인 후속 리뷰](./2026-09-08-scanner-daily-net-approval-followup-review.md)
- [PREOPEN·장중 08:50 점검](./2026-09-08-preopen-intraday-monitoring-0850.md)
