# 원천 수리 반복 리뷰·10/6 Main/Widget/Episode 가동 준비 재점검

## 1. 판정과 실행 범위

사용자의 반복 리뷰·수정보완 및 다음 영업일 정상가동 재점검을 실행했다. [선행 준비계획](../proposals/samsung-premarket-forward-validation-and-source-release-preparation-plan-2026-10-04.md)의 C1 원천 수리/C2 오프라인 계약과 실제 다음 세션 handoff를 검토했다.

**작업본에서4개 회귀 사례를 수정하고 재리뷰·관련493tests를 통과했다. 배포된 운영본의10/6 준비 계약은 PASS다. 실제10/6 가동은 미도래이며, 격리3개 에피소드를 포함한 전부의 정상가동은 확정하지 않는다.** 수리 코드의 운영 반영도 아직 실행하지 않았다.

실제commit·배포·재기동·정책 발행·API/provider·주문·수집 확대·외부sync는0이다. 제한된 원천 재생과 read-only native 검증만 실행했다. 전체 장후 wrapper/학습·cleanup·future live bootstrap/당일 적용파일을 실행하거나 생성하지 않았다.

## 2. 재현→수정→회귀→재리뷰

| 재현한 결함 | 보완 | 최종 확인 |
| --- | --- | --- |
| 전달받은 physical SHA만 비교해 원capture 행이 그대로인 archive append를 감지하지 못함 | 실제파일 SHA를읽기전·후각각대조 | caller가옛SHA를제공해도reject |
| 첫hash 확인과capture 행읽기 사이의archive 변경을허용 | 읽기후physical seal재확인 | concurrent append거부 |
| 장전계약이parent validator module의kernel을봉인하지 않음 | mechanistic_entry_runtime_policy.py 추가 | validator generation변경시replan |
| .gz 이름의directory가유효plain projection을가림 | 존재여부를file여부로대조 | directory fallback·gzip파일우선순위모두확인 |

[수정 전4개 실패](../../tmp/source-review-next-session-readiness-20261004/reproduction-verified-tests.log)를 보존했다. 최초 test의plain/gzip 우선순위 가정은 실제 public reader를 확인해 폐기했다. projection owner는gzip파일을우선하며이번수리도그우선순위를유지한다. 최종재현은directory와정상plain의조합이다.

hash 검사 추가 후 잘못된위치의receipt가binding 거부전에파일을열던회귀도발견했다. 기존receipt 위치/내용/kernel 결속을먼저검사하고그뒤실제archive를읽도록순서를보완했다. 기존경로거부계약과새physical 검사모두통과한다.

family/state·strict validator·hard BLOCK/local RECHECK, public loader 기본/independent 경제성결손규칙도재검토했다. 역사복구receipt를default cache에등록하지 않는다. 새mask는runtime action/주문/PID/cost/null을승격하지 않는다. source/identity/guard/parent·검열/CF·성공100%/80%보존veto 경계를유지했다. **최종검토범위 내 미해결 구현 finding0**이며저장소전체/미배포운영코드의무결함선언은아니다.

## 3. 격리 검증과 변경 세대

- [C1 package](../../tmp/source-review-next-session-readiness-20261004/package.json)와 [6개 파일 patch](../../tmp/source-review-next-session-readiness-20261004/source-repair-C1.patch)는선택운영commit a17bd6d2587e1204eacd0cd283bcbd854eb71bfc 기준이다. detached candidate-final-worktree의적용check·최종6파일SHA일치를검증한뒤관련5suite **457 PASS**·compile/diff를확인했다.
- C2 계약/mask/source inventory **36 PASS**, 고유합계 **493 PASS**다. 별도72개교차실행은중복이므로합산하지 않는다.
- [보관 원천 cold 재생](../../tmp/source-review-next-session-readiness-20261004/repair-replay-cold.json)과warm재생의bytes가일치한다. canonical6/원소비5/복구포함6·원native watch2, 원5행SHA와판정/경제성요약은선행수리와동일하다. 바뀐것은복구receipt/kernel proof다. 복구행은RECHECK·미확정이며새승리/정책후보를만들지 않는다.
- [재검토된 장전계약](../../tmp/source-review-next-session-readiness-20261004/forward-replanned-cold/frozen-contract.json)의SHA는40f567d0768ca72c769dad01b6774d25605871228846992a354c3a37647e8054다. 선행458ce71a 계약/출력은수정전kernel의역사증거로보존한다. 명시적재리뷰세대이며원parent·두가설·조건·날짜·최대3적격날짜·비용/기간은동일하다. 경제조건재선정0이다.
- 계약/inventory의cold/warm bytes도일치한다.10/6 원천4경로는여전히waiting_new_source_date다. 미래evaluator/독립성능/정식policy는미검증이며SamsungPremarketForwardValidation1006을유지한다.

선행 [closure](../../tmp/samsung-premarket-forward-preparation-20261004/closure.json)와이전세대bytes는보존한다. 이번수정5개기존파일(helper/장전계약/각test/10/4checklist)은before snapshot·old/new SHA로추적한다. 나머지186개기존source/kernel/문서seal·98개정책/handoff·selector·선택release와10/6checklist를보존한다. [새closure](../../tmp/source-review-next-session-readiness-20261004/closure.json)가현재작업본의증거다.

## 4. 배포본의10/6 준비 재검증

운영 선택release postclose-tower-readiness-20261003-a17bd6d2의코드로실행했다. 작업본patch를운영release/PID 증거로바꾸지 않았다.

| 점검 | 직접 결과 | 증거 |
| --- | --- | --- |
| 준비물 전체 계약 | current_full_contract PASS·findings0·source10/2→target10/6 | [prepared verify](../../tmp/source-review-next-session-readiness-20261004/prepared-verify.json) |
| 전체 장후/loader | stages완료true·next_session_policy_ready=true·Main/Episode/Widget loader=true | [overview](../../tmp/source-review-next-session-readiness-20261004/stage-overview.json) |
| Main 예약 route | PREOPEN/start 모두a17bd6d2·정확10/6·등록cron8개검증 | [PREOPEN](../../tmp/source-review-next-session-readiness-20261004/preopen-plan.json), [start](../../tmp/source-review-next-session-readiness-20261004/main-start-plan.json) |
| Widget/Episode unit | 독립owner release·source/ExecStart/pin일치 | [release set](../../tmp/source-review-next-session-readiness-20261004/release-set.json) |
| Timer | core2 + Episode122 + auto-expansion1·125개enabled/active·평일반복calendar | [calendar](../../tmp/source-review-next-session-readiness-20261004/timer-calendar-check.json) |

10/5는기존시장calendar의개천절대체휴일이고다음거래일은10/6이다. systemd의다음calendar trigger10/5를거래승인/10/6실제가동증거로쓰지 않는다. 기존시장일/날짜별authority와guard를유지한다.

### Main

10/6 staged bundle 3c500f6ae2222ecb607048213b6ae4fda27f60cbb703af1eb9f76789b0026b99를native validator로검증했다. 현재effective bundle은9/28의6785d52e…이며10/6activation/PID소비는미실행이다. 일요일현재ubuntu tmux bot session과Main PID가없는것을장중기동실패로분류하지 않는다.

[정책 binding](../../tmp/source-review-next-session-readiness-20261004/policy-binding.json)에서005930/그외는공통incumbent다. machine SHA d94fecaf16ac7fa038ee3dafb6f8d6eea7110e49aa5a5f0326fed56f859d713a·보조SHA c23acea371fe2d369e5482fd494ece4b8173cbc0e3f490f24344d0a65e625707가두집단모두같다. 새장전계약을삼성전용live policy로등록하지 않았다.

07:35 PREOPEN/07:55 start·실제PID/당일정책hash는기존DirectFamilyPreopenPolicyHandoff의미래gate다. **현재runtime producer는C1 family/state수리전코드다.** 기동준비PASS가수리본운영반영/모든진입source정상을뜻하지 않는다. 검증patch의운영적용은별도다.

### Widget

현재PID3137231의실제cwd는독립release e6d4d3b9이며unit의검증경로와일치한다. [startup재대사](../../tmp/source-review-next-session-readiness-20261004/widget-current-startup-verify.json)는declared env10개·config/policy 기대hash·process start identity를대조해PASS/findings0이다. [실제cwd](../../tmp/source-review-next-session-readiness-20261004/widget-pid-cwd-readback.json)는unit설정과PID소비를구분한다. 다른프로세스의environ은열지않았다.

receipt의policy date10/3·loaded policy SHA c70eaa5d…는10/6reload/자연사용의증거가아니다. 이미active인service의timer가trigger돼도새PID로바뀐다고가정하지 않는다.07:32 owner정책반영/07:58기동경로와그뒤당일reload·행동receipt를확인해야한다.

overview의Widget observation_only는신규연구selector권한이며기존3종목Widget live service가OFF라는뜻이아니다.

### Episode

61개live+61개preflight의122개unit·366개policy pin과122개instance timer가검증됐다. [10/6 baseline 검사](../../tmp/source-review-next-session-readiness-20261004/episode-nextdate-baseline-check.json)는61개계약valid·격리제외58개다. broker token/Main live/실주문은시험하지 않았다. 당일applied파일은아직없고10/6예정preflight owner가작성/검증할대상이다. 미래파일을지금합성하지 않았다.

| 격리 profile | 현행0.23%비용 재검증의문제 | 다음조건 |
| --- | --- | --- |
| cj_cgv_morning | calibration전반−0.004323%·robustness불충족 | 승인된새profile revision·비용후calibration양쪽/holdout/full검증 |
| youngone_midday | calibration후반−0.000262%·같은robustness문제 | 동일 |
| sk_telecom_midday | calibration−0.001478255%·holdout−0.017345954%·full−0.005667687% | 비용후경제성개선의새profile 증거 |

현재실패표시3개preflight는위격리와일치한다. 상태clear/격리해제0이다.58개는baseline/route준비대상이며당일token/source/preflight/PID가이미통과한58개가아니다. Episode explicit_schedule_disabled는새연구/자동확장정책owner의OFF수용이며기존61개live의전부OFF/전부정상증거가아니다.

## 5. 남은 수용

Main의10/6 PREOPEN/PID는기존10/6 owner다. Widget/Episode 당일정책·preflight·PID/자연source는현재10/4checklist의WidgetEpisodeNextSessionStartup1006에서대조한다. 격리3개·운영경제성/stop/plan 결손은유지한다. 결손을0/실패승률/새policy 성공으로치환하지 않는다.

수리본미배포·미래가동/정책소비·실주문/비용후성과미검증이남은제약이다. 준비PASS를전부정상가동보장으로보고하지 않는다.

Python compile·표적pytest·diff/link/owner·print-only parser를검증했다. Kiwoom request/response/FID/continuation/계정/주문protocol 변경0으로official reference gate는비해당이다. wrapper/cron/unit변경0이며광범위매매suite·API/token조회·정책재생성·future preflight/기동은실행하지 않았다.
