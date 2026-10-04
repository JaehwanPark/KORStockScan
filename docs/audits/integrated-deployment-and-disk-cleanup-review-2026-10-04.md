# 전체 작업본 통합 배포·다음 세션 준비·디스크 정리

## 범위와 수용

사용자의 전체 작업본 통합 배포·정상기동 가능여부 재점검·불필요 작업본/릴리스/임시파일 정리 지시를 실행했다. [직전 반복 리뷰](source-repair-repeat-review-and-next-session-readiness-2026-10-04.md)는 수리본 미배포 당시의 기록이며, 아래 통합 배포가 후속 운영 코드 기준이다.

최초 intake는 변경63파일·HEAD5fcbea3222c206e809191100da1b33de49ffee10·선택a17bd6d2587e1204eacd0cd283bcbd854eb71bfc다. 선택commit은HEAD의선행이며기존운영수정을보존한다. 새 연구 모듈은scalping 오프라인 역할이고runtime 등록/정책선택/주문/수집을추가하지 않는다. 운영변경은entry setup family/state 수리와명시적uncached 역사복구 소비뿐이다. public loader는복구receipt를등록하지 않는다.

첫 통합 회귀는1failed/1001passed였다. 역사 fixture의source census가수정전kernel SHA를현재작업본에서검증하던문제를발견했다. production seal/검증을완화하지 않고test fixture 안에원SHA와일치하는a17 Git bytes를보관하고사본변조거부test를추가했다. CLI의과거날짜 override 거부는유지한다. 재검증결과는아래에기재한다.

최종22suite **1,006 PASS**(108.49초), 변경Python34파일compile·wrapper4개bash -n·모듈위치gate·diff/parser를확인했다. 새fixture는shared data를mount한불변release에서도원canonical kernel경로를인식한다. 미해결검토finding0이며전체저장소무결함/미래실제가동선언은아니다.

배포와다음영업일 실제소비·자연경제성을분리한다. 현재Widget/Episode live entrypoint의소스변경여부를확인하고독립policy/service pin·custody·timer를보존한다. Main은일요일/휴일에강제기동하지않으며10/6정확한isolated준비를새selector에결속한다. 격리3profile을새코드기동으로해제하지 않는다.

정리는현재/직전selector·systemd/cron·실제proc cwd/cmdline/fd·운영manifest/현재handoff·미통합Git와고유파일을보호한다. 삭제worktree HEAD는archive ref로보존하고dirty 후보는별도patch/사본으로byte 복구가능함을검증한때만정리한다. 유일한연구원천·정책·주문/보유·실행receipt는삭제하지 않는다.

## 실행 증거

- [intake](../../tmp/integrated-deployment-disk-cleanup-20261004/intake.json)
- [통합 test 목록](../../tmp/integrated-deployment-disk-cleanup-20261004/test-paths.json)
- [cleanup census](../../tmp/integrated-deployment-disk-cleanup-20261004/cleanup-census.json)
- [통합 회귀](../../tmp/integrated-deployment-disk-cleanup-20261004/final-integrated-tests.log), [물리 release 회귀](../../tmp/integrated-deployment-disk-cleanup-20261004/physical-release-tests.log)

## 배포·준비 재점검 결과

**64파일 통합 commit은 9c0c0632faaf61c7c4434c2fa77b8673125e050d**다. 새 불변 release는 `/home/ubuntu/KORStockScan-runtime-releases/integrated-source-review-20261004-9c0c0632`이며, 모든 commit 입력 SHA·clean runtime source·shared 경로를 검증했다. 해당 release의 물리 경로/공유 원천 영향 검사는 **209 PASS**다. 1,006개와 중복이므로 합산하지 않는다.

release-set/selection lock 아래 selector를 원자 전환하고 이전 a17 선택과 backup을 보존했다. 새 release에서 source10/2 → target10/6의 isolated 준비 세대 `2026-10-02_fa7c47758a5dbafd_9c0c0632faaf61c7`를 생성했다. [최종 full 검증](../../tmp/integrated-deployment-disk-cleanup-20261004/prepared-final-verify.json)은 **PASS / findings0 / current_full_contract**다. 이전 준비와 정책/handoff98개 SHA는 불변이다. 당일 live bootstrap이나 applied 정책을 미리 합성하지 않았다.

장후 평가/최종 refresh 두 inactive service의 installer는 더 높은 기존 `tower1003` drop-in 때문에 실제 경로를 바꾸지 못해 readback에 실패했다. 최고 우선순위 기존 pin을 backup하고 root/commit만 변경해 재검증했다. 최종 WorkingDirectory/ExecStart/commit은 새 release와 일치하고 MainPID=0, timer는 active다. 정책·인자·스케줄·service restart 변경은 없다.

| 대상 | 직접 결과 | 남은 당일 수용 |
| --- | --- | --- |
| Main | 새 selector·PREOPEN/start 경로·등록cron8개·전체 장후/loader/isolated 준비 PASS | 10/6 07:35 PREOPEN·07:55 실제 PID의 코드/정책 소비 |
| Widget | PID3137231의 e6d4d3b9 cwd와 기대 config/policy/env/startup 대사 PASS | 10/6 reload·행동/정책 hash |
| Episode | baseline61개 valid·격리제외58개,122unit/366policy pin 실패0·격리3개 유지 | 당일 applied/source/token/authority preflight·실제 PID |

Widget/Episode의 `src/trading`과 live/preflight wrapper는 e6d4d3b9와 통합 commit 사이에 byte 변경이 없고 이번 Main setup/역사 연구 모듈을 직접 소비하지 않는다. 별도 승인된 e6 live pin·현재 PID·custody를 유지했다. 독립 owner pin을 허용하는 [최종 release-set](../../tmp/integrated-deployment-disk-cleanup-20261004/release-set.final.json)은124owner PASS다. Main/Widget/Episode loader와 next-session readiness도 PASS다.

125개 관련 timer는 enabled/active다. 다음 평일 trigger10/5는 개천절 대체휴일이고 다음 거래일은10/6이다. timer를 시장일 승인 또는 실제 가동 증거로 쓰지 않는다. `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday`의 기존 비용 후 경제성 격리와 failed preflight3개는 유지한다. 58 baseline이 당일 preflight/PID58개 통과를 뜻하지 않는다.

삼성전자와 삼성전자 외 Main은 기존 공통 machine/auxiliary 정책을 승계한다. 새 삼성전자 live 정책을 선택하지 않았다. 운영 경제성·stop/plan 원천 결손도 기존 상태다. 장전 연구 계약은 새 release의 kernel 물리 경로에 명시적으로 결속했다. 새 SHA `7a8ba1454f3818067ac4813ee9b6423cce0ab4cfee3f49fe59f09e684c72803d`는 기존40f567d0과 kernel basename별 SHA·parent·가설·조건·비용·기간·날짜 한도가 동일하고 경로만 다르다. [경로 대사](../../tmp/integrated-deployment-disk-cleanup-20261004/forward-path-review.json)를 보존했으며 원천4경로는 여전히 waiting이다.

## 정리 결과와 잔여

- **worktree21개 삭제**. 각각의 HEAD를 `refs/archive/disk-cleanup-20261004/...`로 보존하고 현재/직전·systemd/cron·실제proc·handoff 참조를 재확인했다. 고유 원천·정책·주문/보유·실행 receipt와 미통합 commit은 유지했다.
- test checkout4개의 고유 수정 코드/진단 로그는 SHA 일치와 tar.gz 복구를 검증해 별도 보관했다. 닫힌 writer lock/open FD 확인 후 삭제했다. 이전 package/closure는 역사 증거이며 삭제 checkout은 [archive ref/사본 결과](../../tmp/integrated-deployment-disk-cleanup-20261004/deleted-worktrees.json)로 재구성한다.
- 종료된 pytest fixture2개를 삭제했다. 살아 있는 lock/FD가 없으며 최신 fixture는 보존했다. [pytest 정리](../../tmp/integrated-deployment-disk-cleanup-20261004/pytest-cleanup-result.json)를 남겼다.
- 기존56 worktree에 새 release1개를 추가하고21개를 삭제해 등록36개다. 실측 가용 디스크는 **17,624,584,192 → 19,437,608,960 bytes**, 순증 **1,813,024,768 bytes(약1.81GB)**다. [실측 기록](../../tmp/integrated-deployment-disk-cleanup-20261004/disk-after.json)은 apparent 삭제량과 구분한다.

최종 근거는 [통합 closure](../../tmp/integrated-deployment-disk-cleanup-20261004/closure.json)다. 원 intake·test·release·selector·준비/route/PID/timer·source/policy 보존·삭제/archive/free-space를 봉인한다. 최종 문서 기록은 별도 commit으로 닫으며 운영 source를 바꾸지 않는다.

10/6 Main `DirectFamilyPreopenPolicyHandoff`, Widget/Episode `WidgetEpisodeNextSessionStartup1006`과 독립 연구 owner를 유지했다. **통합 배포와 준비는 통과했지만, 실제 다음 영업일 가동·정책 소비·자연 성과는 미도래이며 격리3개 전체의 정상 진입을 확정하지 않는다.** 매매 기동·재기동, API/provider/주문, 수집 확대, 새 alpha 정책 선택 및 격리 해제는0이다. 광범위 장후 재생성·cleanup 자동화와 외부 sync도 실행하지 않았다. Kiwoom protocol 변경이 없어 official API reference gate는 비해당이다.
