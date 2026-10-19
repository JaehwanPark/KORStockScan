# 제출병목 관측기의 동기 요청 결속 수리 — 2026-10-19

08:30까지 제출병목 모니터링 지시에 포함된 source-only 관측 결함을 격리 수리했다. 실제 Main `274478/start867428`, 선택8940ea4ad의 운영 코드·Provider·deadline·주문·취소·수량·수동 수탁은 변경하지 않았다. 두산·알테오젠 수동관리 결속은 사용자 지정 다른 세션의 담당이며 수리 대상에서 제외한다.

## 원인과 변경

08:03:39~40 큐리옥스 `aims-a134bfa1399887525008`의 실제 request·trace·machine observation 원문은 존재하고 nested native actor·정책·관측·logical/wire hash가 맞았다. 동기 호출이므로 최상위 `async_request_id/async_producer_pid/async_producer_start_ticks`는 null이다. 관측기는 async ID만 인정해 `reversal_provider_request_hash_or_identity_mismatch`와 `transmission_request_unresolved`를 추가했다. 실제 중단은 별도로 기록된 원래 HTTP 시간 예산 소진이다.

수리는 report-only `_reversal_provider_lineage`에 한정한다. 기존 async branch를 유지하고, 모든 async 필드가 null인 경우에만 기계 관측에서 검증된 Main native receipt와 request nested receipt의14개 필드를 정확히 대조한다. request ID·machine observation·provider preparation 사실·관측 input/prompt와 compact logical/wire hash를 재검증한다. 부분 async·다른 actor·정책·event·hash·시각 불일치는 거부하며 symbol/time 추정은 하지 않는다. `request_binding_basis`는 additive 진단값이다.

## 리뷰·검증

자체 리뷰→보완→재리뷰에서 부분 trace actor 오류가 앞선 trace guard에서 차단되는 경계를 확인했고 음성 시험을 그 실제 단계에 맞췄다. 동기 preparation이 전송/timeout/PASS/Main 수용·주문으로 변환되지 않는 반례를 추가했다. 미해결 in-scope finding0이다.

- `src/tests/test_submission_bottleneck_monitor.py`: **884 PASS**. 기존 async·legacy·history/current PID·source/health 회귀와 동기 compact/noncompact·14개 native 필드·6개 binding 필드·4개 wire hash·부분 async·preparation-only/실제 응답을 검증했다.
- 변경 Python2개 compile·`git diff --check` 통과. 문서 링크·단일 OPEN owner와 print-only parser도 통과했다.
- 실제 원문3행을 offset/SHA와 함께 보존한 단일 과거 timeout 사례에서 원894 코드는 prepared0/issues1/gap1, 수리 코드는 prepared1/issues0/gap0이다. **HTTP 전송1·timeout1·raw PASS0·최초 중단 `original_budget_transport_timeout`은 그대로다.** Provider 재생·주문 경로 재실행은 하지 않았다.

근거는 `/home/ubuntu/KORStockScan/tmp/submission-monitor-20261019-0805-0830/lineage-real-source-case/{manifest,before,after}.json`과 상위 디렉터리의 `lineage-fix-tests-final.txt`다. 단일 사례를 전체 시장 원천 완전성이나 경제성 증거로 쓰지 않는다.

## 운영 인계

`SubmissionMonitorSyncLineage1019`의 코드 리뷰는 닫혔으며 배포는 pending이다. 수정 작업본은 `/home/ubuntu/KORStockScan-worktrees/submission-sync-lineage-20261019`다. 후속 통합 배포 시 기존 frozen native source/code handoff와 최종 선택본/PID를 다시 검증해야 한다. 이 코드만으로 현재894의 경고가 해소됐다고 보고하지 않는다. 새 자연 관측의 exact request prepared 결속과 실제 timeout/미제출 사유 보존이 최종 소비 종결 조건이다.

08:11 이후 큐리옥스의 SELL cancel-intent `pending_submit_flag_missing` 반복은 별도 주문 lifecycle 결함이며 이번 source-only 수리로 수정하거나 guard를 완화하지 않는다. 실제 제출·부분 체결·종결·비용 성과는 모니터링 보고서에서 별도 구분한다.
