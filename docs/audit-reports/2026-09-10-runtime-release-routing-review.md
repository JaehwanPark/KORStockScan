# 9/10 공통 배포 경로 코드리뷰·수정보완

범위: 사용자 요청 `경로통일 수정사항 코드리뷰 후 수정보완, 반복 검증 후 커밋·푸시`. 기존 선택 배포 b665e0a3에서 분리한 `fix/runtime-release-routing-review-20260910` branch를 사용한다. 다른 세션의 adaptive-exit/profit-stagnation/custody 미검토 변경은 포함하지 않는다. main 병합, 선택 release 교체, 실제 봇 재기동 또는 장후 재실행은 이번 요청에 포함하지 않는다.

## 발견·수리

| finding | 재현 근거 | 보완 |
| --- | --- | --- |
| P1: 기동 cron 재조정 시 operator env·로그 소실 | 설치된 start 행에 leading env와 redirect를 추가한 반례에서 renderer가 둘을 제거 | schedule/leading assignment/실행 owner/인수·redirect/marker를 나누고 owner 부분만 교체. legacy tmux와 이미 통일된 start 모두 보존 |
| P1: 실행되지 않는 문자열을 설치된 owner로 오인 | `echo`, `false &&`, `printf` 앞에 놓인 route도 이전 검사 통과 | 실제 leading assignment 뒤 명령을 정확히 비교. 예정 worker의 `--print-plan`, 잘못된 날짜 인수 형식·추가 명령도 거절 |
| P2: 읽기 전용 cron 검사에 설치 lock 부작용·대기 | `--check-cron` 경로가 lock 파일을 생성하는 반례 재현 | 검사는 snapshot 조회만 수행. 설치 전용 lock은 nonblocking이며 기존 백업/CAS/readback 유지 |

수정 전 새 회귀5건이 실패했고, 수정 뒤 같은 반례와 legacy 실제 기동 문법·quoted assignment·dry-run 오설치·잠금 비대기 회귀를 통과했다. 현재 설치된 crontab은 수정 renderer의 no-op이며, 설치 전 백업을 새 renderer로 변환한 결과도 현재 crontab과 byte 일치한다. 이번 수리를 위해 cron을 다시 설치하거나 env 값을 바꿀 필요가 없다.

## 리뷰·검증

- `korstockscan-review-gate`로 selector schema/root/HEAD/clean/shared-path → 실행 계획 → child env/cwd → 기존 restart/PREOPEN/postclose wrapper → cron 수정/복구를 재리뷰했다. source-only/주문/수량/provider 권한, 다른 machine service와 기존 lock 경계를 유지했다.
- 최종 별도 worktree 11개 모듈 **1961 PASS / 28.65초**, 기존 pandas 경고1개. 라우터·재기동64개는 이 집합에 포함되며 합산하지 않는다. Ruff/Black·compile·bash syntax·diff 검증과 문서 링크/print-only parser를 확인한다.
- 지난 지시문 현행화, workspace restart shim, 경로 운영 문서와 관련 checklist 두 owner만 함께 보존한다. checklist의 다른 장중/적응형 청산 변경은 커밋에 섞지 않는다.
- 검토 범위의 미해결 finding0은 라우팅 코드/계약 수리에 대한 판정이다. 실제 다음날 기동·정책 선정·거래빈도·NXT drought·비용 차감 순이익의 완료 판정이 아니다.

## 적용 경계

검토된 라우터와 테스트/운영 문서를 canonical workspace에 동기화하되 선택 원장·cron은 그대로 유지한다. 이 workspace 라우터는 설치된 cron이 다음 호출부터 읽는 진입점이다. 선택 release 내부의 사본을 바꾸지 않았으므로 그 HEAD/clean 상태는 유지된다. workspace bootstrap의 수리 코드 세대와 선택 trading code의 세대를 구분한다.

18:59 확인에서 선택값은 `unified-runtime-20260910`/b665e0a3, 실제 main은 PID1048327/a722b27f(17:54:12), widget PID327676(07:57:59)이다. 실제 프로세스·정책·cap을 변경하지 않는다. 이전 설치 receipt와 다음 자연 기동은 [고정 배포 리뷰](2026-09-10-fixed-release-postclose-startup-review.md), 다음 확인은 기존 `KRXDaily100NextDayStartupAcceptance0911`이 소유한다.

이 branch에는 검증된 배포 기반의 기존 entry/holding 수리 commit들이 조상으로 포함된다. 현재 dirty workspace 전체를 커밋한 것이 아니며 원격 main의 자동 병합이나 선택 commit 자동 교체는 없다. 향후 release를 재발행할 경우 본 branch의 변경을 검토된 세대에 포함하고 기존 code/source pin·PREOPEN gate를 다시 확인한다.

workspace 반영 후 라우터/재기동64 tests를 다시 통과했다(전체1961과 중복). 실제 `--check-cron` 및 workspace `restart.sh --print-plan`은 PASS이고, 선택 원장과 crontab의 반영 전후 SHA256은 각각 동일하다. 기존 선택 release의 source clean도 유지된다. 실제 start/restart/postclose/Provider 호출·cron 재설치는 수행하지 않았다. 문서 링크·shell 예제 구문·print-only parser에서 다음날 기동 owner의 유일성을 검증했다.
