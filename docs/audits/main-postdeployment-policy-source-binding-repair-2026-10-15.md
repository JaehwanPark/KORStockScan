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
- handler 및 stop reader 변경에 대한 정확한 source-pair와 rising/holding capability successor hash를 갱신한다. native 보고서와 과거 unverified 상태는 보존하고 현재 fixture 검증을 별도로 발급한다. active policy33 module bytes가 기존 선택과 동일함을 확인한 경우에만 기존 native parity를 재사용한다.

## 검증 및 실행 상태

경보 수정 2,122개 및 배포 경계121개 회귀 PASS. 통합본 전체 관련 회귀3,148개 PASS(기존 pandas 경고1), 변경 Python compile·diff·print-only parser PASS. native capability fixture 및 배포 전 검증 결과와 실제 배포/PID 영수증은 완료 후 아래에 기록한다. 테스트 PASS를 자연 제출·체결·비용 후 성과로 해석하지 않는다. 외부 Project/Calendar sync와 수동 주문/provider 호출은 실행하지 않는다.

실행 owner는 기존 `DirectFamilyPreopenPolicyHandoff`, `AuxiliaryCircuitRecoveryRepair1012`, `MainStopLossRetirementRuntimeTuning1010`, `NonfixedDispatchReadinessReview1012`를 유지한다. 현재 실제 PID와 다음 정규 observer/detector generation의 일치가 운영 수용이며, 제출·경제성은 별도 자연 수용이다.
