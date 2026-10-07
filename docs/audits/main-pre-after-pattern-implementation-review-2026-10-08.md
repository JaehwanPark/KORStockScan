# Main 시간외 등록·상태 보완 구현 검토 — 2026-10-08

## P0 경로 복구

사용자는 구현·반복 리뷰·배포·재기동을 승인했다. 원 계획의 연구 당시 미승인 문구는 당시 이력이다. 실행 owner는 `DirectFamilySourceRepairMainMechanisticEntry`를 유지한다.

- `p0-before.json`: 선택 v3의 기록 PID 1324165는 현재 `/proc`에 없다. 실제 launch cwd에서 활성 bundle의 `data/...` 원천 경로 결손을 재현했다. 과거 PID 영수증을 현재 가동으로 표시하지 않는다.
- 명시 data root의 context-local 경로 resolver를 공통 native reader에 적용했다. hash/cache/read/dependency는 같은 절대 lexical 경로를 사용하고 실제 symlink 목적지·stat 변경을 검출한다. 상대 탈출/미지원 접두/외부 링크·누락은 차단한다. 원 봉인 보고서는 수정하지 않는다.
- 정책 payload·bundle·18개 판정 code pin은 변경하지 않았다. 이 최소 수정에는 v5 same-day successor가 필요하지 않다. dispatcher/activation/PID 소비는 동일 anchor reader를 사용하며 새 source receipt는 절대경로로 기록한다.
- launcher는 실제 `src` cwd에서 native `--validate-current`를 실행한다. bootstrap 성공과 별개인 `launch_loader` 상태를 출력한다. provider/order 호출은 없다.
- 이미 종료된 이전 PID의 경우 명시 `--previous-stopped` 인계를 지원한다. 이전 동일 날짜의 소비 영수증·기동 원천·정책·이전 immutable release를 검증하고 PID 부재를 재검사한다. 이를 현재 PID 소비로 표시하지 않는다. 기존 살아 있는 PID 인계는 원 검사를 유지한다.

실제 동일 bundle `cdacf6eed9d77e95d0bdf1a417ec2549323ea2491b91e41b8f948b900434895f`의 4개 cwd 검증은 모두 통과했다. 첫 load 약 1.98초, 재사용 약 .06초이며 731개 dependency를 추적한다. [P0 원천 영수증](../../data/report/pre-after-remediation/2026-10-08/p0-before.json), [4개 cwd 검증](../../data/report/pre-after-remediation/2026-10-08/p0-four-cwd.json).

기존 native/운용/인계/보조 회귀 172 PASS, 추가 anchor 회귀 5 PASS. 후속 인계/기존 path 회귀 136 PASS, 종료 PID 인계 4 PASS, bootstrap/router 117 PASS. compile·bash -n·diff·문서 parser(현행 owner 1개) 통과. 배포 검증은 진행 중이다. 신규 13개 후보 등록/보조 계약/기여도/상태 보완은 P0와 별도 변경 단위로 계속한다. 이 문서는 실제 주문·수익 또는 전체 구현 완료의 영수증이 아니다.
