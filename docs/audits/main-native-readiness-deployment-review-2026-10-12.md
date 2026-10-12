# Native claim·상시/비상시 준비 통합 배포 리뷰 — 2026-10-12

사용자가 두 계획의 재리뷰·결함 보완·배포·재기동을 승인했다. [native 구현](main-native-signal-claim-implementation-review-2026-10-12.md), [상시·비상시 구현](main-fixed-nonfixed-readiness-implementation-review-2026-10-12.md), [인증 감시기 원자 저장](auth-8005-detector-state-persistence-review-2026-10-12.md)을 같은 릴리스에 연결한다. 선행 코드 검증은 1,462건 통합 회귀이며 이번 추가 변경은 아래 별도 회귀로 검증한다.

## 추가 시간초과 원천 대사

조사 당시 실제 PID는 `1020707`/start `3378564`, selected release는 `auxiliary-consumption-attestation-20261012-v1`이다. 16:08 세 건은 모두 원 AI trace와 같은 분의 execution partition에서 exact attempt로 대조했다.

| 종목·원 로그 시각 | attempt | HTTP budget / provider | freeze 후 잔여 | worker 반환 시 잔여 | Main 최종 종료 |
|---|---|---|---|---|---|
| 알테오젠 16:08:15 | `aims-7b60dca5d744307d0ca8` | 2755 / 2738ms | 3870.300ms | 248.852ms | `reversal_signal_path_changed` |
| 주성 16:08:24 | `aims-dae1d2fbec30c907c6e3` | 2972 / 2918ms | 3992.934ms | 171.246ms | `result_deadline_expired` |
| 알테오젠 16:08:28 | `aims-b2fcbfb7f0f5bbbce3ae` | 3073 / 3066ms | 4036.102ms | 227.939ms | worker `evaluation_deadline_expired`, Main `result_not_commit_eligible` |

HTTP lock 대기는 0ms였다. trace capture는 11.29~25.89ms, policy resolve는 15.21~37.77ms, local refresh는 24.91~28.22ms였다. 이 작은 단계만으로 freeze 이후의 전체 예산 감소를 설명하지 못한다. HTTP timeout이 실제 발생했으며 AI PASS/VETO나 broker 주문 실패로 집계하지 않는다. 과거 실패를 새 PID에서 재실행하지 않는다.

## 재리뷰에서 보완한 결함

1. 선행 `entry_local_stage_clocks`는 성공 응답에서만 완성됐다. timeout/로컬 실패에도 provider 구간·실패 처리·annotation 반환 시계를 보존하고 기존 async disposition으로 전달한다. 원 native deadline·timeout·model/provider·회로 조건은 그대로다.
2. 실제 decision trace writer가 이 필드를 읽지 않아 성공 계측도 영구 trace에서는 누락됐다. 제한된 숫자 키만 투영하고 NaN/bool/임의 문자열을 배제한다. annotation 완료 시각은 반환 결과/disposition에서 확인하며 trace 생성 전 아직 없는 값을 합성하지 않는다.
3. cache delivery가 원 호출의 monotonic 시계를 다시 내보낼 수 있었다. cache 결과에서 해당 시계를 제거하고 원 parent trace에 남긴다. cache delivery 지연과 원 provider 지연을 혼합하지 않는다.
4. 현재 delay/holding code custody는 이전 리뷰의 exact file pair만 허용한다. 이번 리뷰의 Main/handler/coordinator/logger/monitor/AI 파일을 원 PREOPEN origin commit에서의 SHA256와 새 SHA256 쌍으로 등록한다. 임의 함수 전체를 예외로 허용하지 않고 다음 byte 변경은 차단한다. [exact pair 근거](../../tmp/native-readiness-deploy-20261012/reviewed-source-pairs.json).

## 검증과 배포 절차

- 추가 AI/trace, native/async, writer/monitor, auth, bootstrap/handoff/ordered deploy 회귀: **1,027 passed**. [로그](../../tmp/fixed-nonfixed-readiness-20261012/pytest-deploy-review-final.txt). exact pair 변경은 [인계 회귀](../../tmp/native-readiness-deploy-20261012/pytest-handoff.txt)로 다시 확인한다.
- 새 기계/보조 정책을 발행하지 않는다. 기존 128경로의 same-policy reader/compatibility, 원 PREOPEN와 정책 파일 해시를 준비·최종 소비에서 확인한다. 상시 5종목과 비상시 5슬롯/긴2·60/150초, native 5초, 원 source/quote 및 Main/manual custody를 유지한다.
- immutable candidate를 현재 selected release에서 만들고 리뷰한 전체 작업본을 정확 파일 해시로 반영한다. candidate checklist는 선행 native/auth 보완과 기존 장후 OPEN owner를 보존하며 Main 종료 후에만 게시한다.
- 기존 `ordered_intraday_deploy`의 detector lock → incumbent 검증 → graceful Main/supervisor drain → selector/checklist → native handoff/bootstrap/auxiliary → launcher → exact PID/start/cwd 소비 순서를 사용한다. candidate delay code를 drain 전에 검증한다.
- 원 finalization의 historical checklist를 보존하고 `strict_checklist_generation_stale`·chain 변경 여부를 최종 릴리스에서 확인한다. 운영 장후/EOD를 다시 생성하지 않는다.

최종 릴리스·실제 PID·자연 heartbeat/진단·정책 소비·기존 파일 보존 결과는 [배포 완료 증빙](../../tmp/native-readiness-deploy-20261012/completion.json)에 기록한다. 입력 전달 개선이 model의 모든 시간초과를 해소했다고 주장하지 않는다. 새로운 시계의 실제 표본이 있으면 구간별로 확인하고 표본 0은 미관측으로 표시한다.

## 배포 후 현재 검증

16:46:58 ordered transition 완료, 최종 릴리스 `native-readiness-20261012-v1`/`fda9f640aadc14c3987075c9e9dc25358c03a28c`. ubuntu PID `1171338`/start `4055127`의 정확 cwd·bootstrap·인계·기계/보조 소비와 128경로 호환성 PASS. 원 PREOPEN·policy·controller 등 보호 파일 해시는 동일하다. 자연 감시의 selected root/commit 소비 provenance를 확인했으며 `strict_checklist_generation_stale`·chain 세대 오류와 신규 log error는 없다. `postclose_finalization`은 원 08:42:39 완료의 `recovered_late` warning을 유지한다. 새 PID의 실제 AI 표본은 확인 시점 0건으로, HTTP 시간초과 개선을 확정하지 않는다.
