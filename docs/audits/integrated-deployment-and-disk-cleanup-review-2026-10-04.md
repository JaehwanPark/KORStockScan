# 전체 작업본 통합 배포·다음 세션 준비·디스크 정리

## 범위와 수용

사용자의 전체 작업본 통합 배포·정상기동 가능여부 재점검·불필요 작업본/릴리스/임시파일 정리 지시를 실행한다. [직전 반복 리뷰](source-repair-repeat-review-and-next-session-readiness-2026-10-04.md)의 코드·기동 준비 증거와 현재 실제 운영 참조를 다시 대사한다.

최초 intake는 변경63파일·HEAD5fcbea3222c206e809191100da1b33de49ffee10·선택a17bd6d2587e1204eacd0cd283bcbd854eb71bfc다. 선택commit은HEAD의선행이며기존운영수정을보존한다. 새 연구 모듈은scalping 오프라인 역할이고runtime 등록/정책선택/주문/수집을추가하지 않는다. 운영변경은entry setup family/state 수리와명시적uncached 역사복구 소비뿐이다. public loader는복구receipt를등록하지 않는다.

첫 통합 회귀는1failed/1001passed였다. 역사 fixture의source census가수정전kernel SHA를현재작업본에서검증하던문제를발견했다. production seal/검증을완화하지 않고test fixture 안에원SHA와일치하는a17 Git bytes를보관하고사본변조거부test를추가했다. CLI의과거날짜 override 거부는유지한다. 재검증결과는아래에기재한다.

최종22suite **1,006 PASS**(108.49초), 변경Python34파일compile·wrapper4개bash -n·모듈위치gate·diff/parser를확인했다. 새fixture는shared data를mount한불변release에서도원canonical kernel경로를인식한다. 미해결검토finding0이며전체저장소무결함/미래실제가동선언은아니다.

배포와다음영업일 실제소비·자연경제성을분리한다. 현재Widget/Episode live entrypoint의소스변경여부를확인하고독립policy/service pin·custody·timer를보존한다. Main은일요일/휴일에강제기동하지않으며10/6정확한isolated준비를새selector에결속한다. 격리3profile을새코드기동으로해제하지 않는다.

정리는현재/직전selector·systemd/cron·실제proc cwd/cmdline/fd·운영manifest/현재handoff·미통합Git와고유파일을보호한다. 삭제worktree HEAD는archive ref로보존하고dirty 후보는별도patch/사본으로byte 복구가능함을검증한때만정리한다. 유일한연구원천·정책·주문/보유·실행receipt는삭제하지 않는다.

## 실행 증거

- [intake](../../tmp/integrated-deployment-disk-cleanup-20261004/intake.json)
- [통합 test 목록](../../tmp/integrated-deployment-disk-cleanup-20261004/test-paths.json)
- [cleanup census](../../tmp/integrated-deployment-disk-cleanup-20261004/cleanup-census.json)
- 배포·준비·삭제·사후검증은진행중이며미완료gate를PASS로표시하지 않는다.
