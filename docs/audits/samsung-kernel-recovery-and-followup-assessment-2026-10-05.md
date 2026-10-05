# 삼성 후속연구 판단 및 과거 후보 커널 원본 복구

작성일: 2026-10-05 KST. 사용자 후속연구 필요성 질문과 과거 후보 원본 결손의 즉시 처리 지적에 따른 점검·복구 기록.

## 1. 삼성 후속연구의 우선순위

[직전 연구](designated-machine-policy-and-samsung-differential-execution-review-2026-10-05.md)의 원흡수 후보는 기존 정책보다 탐색 지표가 개선됐다. 그러나 H2의 원흡수 대비 추가 개선은9/29 손절1건 제거에 집중되며, 그 날짜를 빼면 개선이 없다. 삼성 상시감시 전용 개선도 입증되지 않았다. 따라서 원흡수와 H2의 고정 후속 비교를 이어가되, 현재 자료에서 가설을 무한 증식할 근거는 없다.

H2는 직전 **기계판정 capture**와 현재 capture의 매수압력 전환을 요구한다. [추가 가용성 집계](../../tmp/samsung-kernel-recovery-20261005/H2-source-availability.json):

| H2 계산 불가 원인 | 전체519건 | 상시감시206건 |
|---|---:|---:|
| 직전 capture 부재 또는 현재 receipt 불충족 |112|12|
| 직전 capture와 간격이 원래5초 TTL 초과 |338|193|
| 직전 capture receipt 불충족 |26|1|

첫 분기는 `preceding_capture_missing`이라는 코드 이름에 현재 receipt 불충족도 포함되므로 순수한 파일 부재 건수로 해석하지 않는다. 상시감시206건에서는 H2 조건을 식별한 건수가0이다. 이는 매매 판단 기록의 간격과 H2의 관측 단위가 맞지 않는 문제를 우선 확인할 근거다. 새로운 시장 데이터 수집 필요성이 입증됐다는 뜻은 아니다.

추가연구를 한다면 다음 한 갈래가 우선이다.

1. 보관된 연속 체결/호가에 동일 route·epoch·판정시각 이전의 직전10tick 구간이 실제 존재하는지 census한다.
2. 충분하면 판정 capture 간 비교와 원 tick 구간 간 비교를 별도 가설로 고정하고, 같은 진입·종료·비용·모집단으로 원흡수 대비 차이를 검증한다. 현재 H2 frozen의 뜻을 사후 변경하지 않는다.
3. 연속성·시점·기존 TTL을 충족하지 못하는 부분은 unknown으로 유지한다. TTL 완화나 미래 가격 사용으로 식별률을 높이지 않는다.
4. 새 가설의 지원이 없으면 현재 원흡수/H2의 이후 날짜 검증으로 종료한다. 탐색 날짜를 새 독립 검증으로 재사용하지 않는다.

위 네 단계는 **후속연구 방향 제안**이다. 이번 작업에서는 가용성 집계와 원본 복구·재현 검증을 수행했으며, 새 tick 기반 후보 계산·선정·삼성 운영 지정은 수행하지 않았다.

## 2. 과거 후보2개의 결손 원인과 복구

대상은 `foreign=up` 및 `past_gap_180/program_change=down`의 두 고정 veto 후보다. 원흡수/H2와 별도다.

누락 항목은 시장 원천이나 후보 수식이 아닌 `src/tests/test_samsung_fixed_watch_evaluation_research.py`의 과거 특정 bytes다. frozen이 요구하는 SHA-256은 `c165a5091f8fffbc754fd71c914cc77e5ff72c027287c8c6c042c65051d7c0ef`다. 이전 탐색은 현재 파일·Git의 참조 가능한 이력·보호 release까지만 확인했으며, 미참조 Git 객체까지 확인하지 못했다. 새 날짜를 기다릴 사유로 남긴 것은 적절하지 않았다.

이번에는 `git fsck --no-reflogs --unreachable`로 대상 크기 범위의 blob671개를 확인했고, Git blob `38c14bd525352cd292d03b1eb3ce1a44fc6850c3`에서 **요구 SHA-256과 정확히 일치하는16,829바이트 원본**을 복구했다. 추정 재작성이나 현재 hash 치환이 아니다.

- 보존 ref: `refs/archive/samsung-kernel-recovery-20261005`.
- 원본 보관: `tmp/designated-machine-execution-20261005/original-kernels/c165a5091f8fffbc754fd71c914cc77e5ff72c027287c8c6c042c65051d7c0ef/test_samsung_fixed_watch_evaluation_research.py`.
- [복구 증거](../../tmp/samsung-kernel-recovery-20261005/unreachable-recovery.json), [이전 결손 상태](../../tmp/samsung-kernel-recovery-20261005/migrations.before.json), [갱신한 migration](../../tmp/designated-machine-execution-20261005/migrations.json).

원 frozen 파일과 후보 조건·학습 결과·날짜 경계는 불변이다. 기존 호환 계약으로 원 커널 보관과 새 코드·허용 component 차이를 연결했고 두 후보의 migration은 `validated`다. 기존 실행 closure의 결손 목록은 그때의 기록으로 보존하며 현재 상태는 이 문서를 따른다.

## 3. 재현 검증과 한계

- 기존519관측의 두 selector mask와 native metric이 과거 보고서와 모두 일치한다. 날짜별 두 prefix씩6개 검사도 통과했다. [후보 대사](../../tmp/samsung-kernel-recovery-20261005/candidate-parity.json).
- 선택된 불변 release `3d0e5106`에서 원 frozen을 그대로 소비해10/6 준비 CLI를 실행했다. 이제 원본 결손 없이 `waiting_new_source_date`까지 도달한다. [준비 결과](../../tmp/samsung-kernel-recovery-20261005/next-date-readiness/preparation-status.json). 필요한4경로의 새 날짜 원천은 아직 없다.
- 복구된 옛 테스트 파일을 별도 위치에서 실행한 결과37 PASS·16 SKIP였다.16개는 테스트의 상대 root에서 역사 자료를 찾지 못한 경우로, 전체 통과로 집계하지 않는다.
- 현재 소비자 회귀는57 PASS·1 FAIL이었다. 실패는 과거 fixture가10/6의 변경 가능한 dated 경로에 이전 물리 SHA를 요구해 발생했다. 신규 지정 정책을 원복하거나 expected hash를 현재 것으로 바꾸지 않았다. 동일 SHA의 publisher archive를 연결한 별도 역사 capsule로 원본/정규화/native/후보 mask **160행 왕복 PASS**를 확인했다. [격리 원본 입력 검증](../../tmp/samsung-kernel-recovery-20261005/historical-intake-validation.json). 이는 과거 입력 재현이며 새로운 holdout이 아니다.

원본 복구·연구 재현·미래 입력 대기·실전 성과는 별개다. 과거 두 veto가 운영에 적격해졌다는 결론을 내리지 않는다. 정책·선택 release·Main/Widget/Episode 재기동·주문·추가 원천 수집은 이 작업에서 변경하지 않았다.
