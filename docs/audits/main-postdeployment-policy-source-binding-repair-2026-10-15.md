# 12:06 정책 원천 경보·장기 슬롯·약세 veto 통합 검토 — 2026-10-15

## 결정과 근거

사용자는 오류 수정·배포·재기동을 승인했고, 다른 세션의 완료 커밋 `40b93125431d2c6fb423cd397958de9a8725ee61`도 같은 배포에 통합하도록 지시했다. 기존 선택 `3b390be1e`·PID1927180의 12:03 검증 이후 발생한 새 결함을 대상으로 한다. 당시 PASS를 현재 상태로 재사용하지 않는다.

1. 편집 가능한 당일 체크리스트에 장기 슬롯·약세 veto의 승인 범위가 추가되자, 이미 소비된 정책의 code reader가 변경된 문서 hash를 다시 요구했다. 실제 PID·정책·원천과 문서 편집을 구분해야 한다. 다른 세션의 수정은 보존한다.
2. 10/14 stop 정책은 vote 원천을 소비하지 않았고 selected cell도 없지만, 전체 holding observation discovery inventory가 10/15의 새 append를 과거 정책 변경으로 판단했다. 확인된 ledger는 같은 inode의 native 10/15 행 추가였다. 원 정책/보고서/실제 사용 원천을 재작성하지 않는다. legacy watch inventory에는 미사용 prefix hash가 없으므로 현재 계산한 hash를 과거 무변경 증거로 주장하지 않는다.
3. 최종화 경보는 새 finalizer 실패가 아니라 위 native stop/bootstrap 검증 실패의 후속 관측이었다. 실패 기록을 삭제하거나 경보를 숨기지 않고 원 producer/consumer 계약을 수정한다.

증거: [원 경보와 비교 자료](../../tmp/postdeploy-binding-error-20261015-1206/), 원 `health-before.json`, `observer-before.json`, `vote-watch-binding.json`, `vote-watch-diff.json`. 정책 bootstrap 원 manifest는 `73a9a4f20bc146ea40c2f74966e107a3cb7773ef623dd1b9df0750a838adebad`, active policy bundle은 `1f069c6894b5b9a7fa3f9450a9a306ff41469346e1318b20b18fcaee7e490637`이다.

## 구현과 리뷰 경계

- stop carried reader만 no-selected/no-consumed 조건에서 이후 날짜 native 미사용 관측의 완전한 append를 허용한다. 실제 사용 원천·과거 날짜·파일 교체·불완전 JSONL·다른 position hash·비유한 시각은 거절한다. full research/publication은 기존 전체 검증을 유지한다. 새 discovery 봉인은 decoded prefix hash도 기록한다.
- 이미 소비된 legacy 문서는 exact live PID와 원 immutable historical snapshot을 함께 검증한다. 새 ordered 배포는 공유 체크리스트를 쓰지 않고 안정된 operating snapshot을 create-only로 봉인한다. public startup/consume/activation은 그 immutable bytes를 요구한다.
- 후보 reader의 predecessor 재검증은 immutable candidate·정확한 source pair·기존 실제 PID·전체 native bootstrap/auxiliary proof를 요구한다. 이전 실패 로그를 보존하며 성공을 후보 PID 소비로 표시하지 않는다. 검증 실패 시 drain/selector/hold 변경에 진입하지 않는다.
- `40b931254`의 전체 physical probe5 내 long3, 두 약세 alpha veto의 exact Main ENTER_NOW/AI PASS 범위와 이력 분리를 통합했다. native deadline, stale/conflict, DANGER, source-quality, 가격·계좌·주문·수량·custody와 기존 operator lock을 유지한다. [별도 구현 리뷰](main-long-probe-and-weak-veto-scope-review-2026-10-15.md)의 사용자 승인 범위를 따른다.
- handler 및 stop reader 변경에 대한 정확한 source-pair와 rising/holding capability successor hash를 갱신한다. native 보고서와 과거 unverified 상태는 보존하고 현재 fixture 검증을 별도로 발급한다. 초기 후보는 active policy33 module bytes가 같았으나, 배포 전 전체 검증에서 active-policy reader도 후보 경로를 거절하는 추가 경계를 발견했다. 정확한 기존 selector/PID와 이미 발급된 candidate receipt의 origin/code/source/pointer를 모두 요구하는 읽기 전용 predecessor scope를 보완했다. 실제 native confirmation128 scopes·76,800rows의 기존/후보 비교를 새로 실행하며 원 데이터·정책·선택은 변경하지 않는다.

## 검증 및 실행 상태

경보 수정 2,122개 및 배포 경계121개 회귀 PASS. 통합본 전체 관련 회귀3,148개 PASS(기존 pandas 경고1), 변경 Python compile·diff·print-only parser PASS. native capability fixture 및 배포 전 검증 결과와 실제 배포/PID 영수증은 완료 후 아래에 기록한다. 테스트 PASS를 자연 제출·체결·비용 후 성과로 해석하지 않는다. 외부 Project/Calendar sync와 수동 주문/provider 호출은 실행하지 않는다.

실행 owner는 기존 `DirectFamilyPreopenPolicyHandoff`, `AuxiliaryCircuitRecoveryRepair1012`, `MainStopLossRetirementRuntimeTuning1010`, `NonfixedDispatchReadinessReview1012`를 유지한다. 현재 실제 PID와 다음 정규 observer/detector generation의 일치가 운영 수용이며, 제출·경제성은 별도 자연 수용이다.

추가 경계 보완 후 회귀1,529개 PASS. 복사한 immutable native fixture5개를 격리 worktree에서 읽었으며 운영 원천에는 쓰지 않았다. 최신 native128 scopes·76,800rows·607hits 및 signal hash가 기존 선택과 동일했다(mismatch0). 새 rising86·holding91 fixture의 network/provider/order0과 원 protected artifact 불변을 확인했다. 배포 전 후보787a5ee97은 선택하지 않았으며 추가 경계 보완 후속본으로 대체한다.

## 첫 배포와 신규 경보 후속

- `110ac4a90`은12:40:21 ordered complete/pass, PID2020871/start9949242가 원 정책을 실제 소비했다. WebSocket도 같은 PID/commit으로 갱신됐다. 공유 체크리스트 완료 기록을 수정한 뒤에도 새 operating snapshot의 public verify가 PASS여서 편집 결속 문제 해소를 실증했다.
- 12:40 정규 관측에서 stop native 정책·delay/bootstrap 결속은 검증됐지만, 배포 전12:35의 `entry_execution_tuning_receipt_contract`가 `historical_unresolved`로 남아 최근10분 규칙에서 현재 미상 사건으로 다시 집계됐다. 사용자 후속 경보와 동일하다. 원 실패를 삭제하거나 recovered로 바꾸지 않는다.
- 후속 보완은 이 정확한 두 delay/bootstrap mismatch에 한정한다. 사건의 마지막 관측이 검증된 현재 PID 탄생 이전이고, 현재 bootstrap/PID·split native projection·delay/env/hash가 모두 검증된 경우에만 과거 사건으로 분류한다. 현재 PID에서 발생한 실패, 다른 원인, 원천/정책 결손, 불완전 증거는 계속 실패다. 실제 원 보고서의 읽기 전용 재계산은 `warning_pending`이며 원 incident bytes/status를 유지한다.
- 관련978개 회귀 PASS. 완전한 제출/경제성 수용을 주장하지 않으며 현재 관측 없음은 pending으로 남긴다. 첫 기동 점검의 heartbeat16초/I/O wait36.45% 실패도 원본에 보존하고 후속 새 점검에서 재확인한다. 한계치를 완화하지 않는다.

## 후속 통합 배포 영수증

- 최종 실행 코드: `bb4808c77087231b072efbd3ea12271fbb3889c6`, 경로 `/home/ubuntu/KORStockScan-runtime-releases/policy-custody-incident-integrated-20261015-bb4808c77`.
- ordered transition12:51:18 `complete/pass`; 실제 PID2039852/start10014770·cwd·selector·bootstrap 소비 PASS. 공유 문서 갱신 후 public handoff 검증도 PASS, startup hold/restart flag 없음. WebSocket은 같은 PID/commit으로12:52:28 갱신됐다.
- 사용자40b931254의 handler/scanner/queue3개 실행 파일이 원 커밋 bytes와 정확히 일치한다. 후속본 active policy33 module은 직전 선택과 동일해서 방금 측정한128 scopes·76,800rows·607hits/mismatch0 증거를 재사용했다. 정책 원본·PREOPEN·bootstrap은 보존한다.
- 후속 관측/탐지기978개 및 handoff/deployer1,402개 PASS. compile·diff·문서 print-only parser PASS. 기존 통합3,148개 및 추가 active-policy 경계1,529개와 중복되는 검증이므로 합산하지 않는다.
- 12:50 정규 관측은 `observer_waiting_ordered_startup_completion`으로 게시/알림을 보류했다.12:52:31 새 detector는 실패0, 과정 중 heartbeat/I/O 실패가 재발하지 않았다. 현재 남은 경고는 첫 현재 관측 대기와06:50 이후 장전 복구 이력이며, 다음 정규 게시·탐지기 동일 run/hash를 별도로 확인한다.
- 증거: [배포 로그](../../tmp/postdeploy-binding-error-20261015-1206/incident-successor/deployment.log), [사용자 커밋 실제 소비](../../tmp/postdeploy-binding-error-20261015-1206/incident-successor/deployed-user-commit-integration.json), [문서 편집 후 handoff 검증](../../tmp/postdeploy-binding-error-20261015-1206/incident-successor/postdeploy-handoff-verify.json), [과거 사건 원본 재계산](../../tmp/postdeploy-binding-error-20261015-1206/incident-readonly-replay.json).

## 최종 수용

12:56:34 정규 producer가 run `4d4a10a1933143f59b529c6e87fdc2bd`를 게시했고,12:57:12 detector가 동일 run/hash·새bb4808c77/PID2039852를 소비했다.12:58:04 최종 수용15조건 모두 PASS.4개 정책 capability는 모두 verified/findings0이며 stop native 원천·실제 PID 소비도 정상이다. 현재 detector fail/critical/error0, startup hold 없음. [최종 수용 영수증](../../tmp/postdeploy-binding-error-20261015-1206/incident-successor/accepted-final.json).

첫 신규 원천 검증 중12:56:02 I/O wait38.96% 경보가 있었고, 계산 완료 후12:57:12에는 resource/process 점검이 PASS로 돌아왔다. 이 초기 검증 비용과 원 경보는 보존한다. 남은 warning은 `bounded_source_quality_observation`의 불완전 관측과06:50 이후 장전 복구 이력이다. 기존 정책 검증 경고나 현재 최종화 실패로 재분류하지 않는다. 자연 제출·체결·비용 후 성과 및 원천 결손 수용은 기존 OPEN owner를 유지한다.
