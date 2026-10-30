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

## 2026-10-30 source coverage and shared registration

현재 사건은 기존 `SubmissionMonitorSyncLineage1019`에서 추적한다. 기준 선택본은52425f68f, Main3948505/start95906268이다. 원본은 [원본 manifest](../../data/audit/submission_monitor/2026-10-30-incident/manifest.json)와 [사건 검토](../../data/audit/submission_monitor/2026-10-30-incident/incident-review.md)에 보존한다. 08:05/08:10 보고서 본문은 native 갱신으로 덮어써졌으므로 원본 detector 투영과 보존된 입력 prefix를 사용하며, 완전한 당시 보고서를 복원했다고 주장하지 않는다.

08:05에는 첫 trace 생성 전 native 관측 미완성과 exact no-match 탐침이 있었다. 08:10의 현재 Main 평가 `BLOCK`은 auxiliary 요청을 만들지 않으므로 요청/결과 journal 부재와 실제 읽기 실패를 구분해야 한다. 08:11 Main 동기 호출은 정상 request/trace/기계 관측을 결속하지만 async coordinator 신원은 null이며, 관측기가 이를 미연결 async PASS로 세었다. 별도 완료 predicate는 async 범위 partial을 검증 완료로 표시할 수 있었다. 격리 수리1b34e8cbf는 이 분류들을 수정하되 missing/unknown/현재 결함을 성공이나0으로 바꾸지 않는다. 원코드 실패 재현 및 감시기·감지기2193검사가 통과했다.

후속 전환 검토에서 동일 report-only 코드의 변경 endpoint를 배포 인계와 독립 준비 context에 각각 등록해야 했던 중복 소유를 확인했다. `REVIEWED_SUBMISSION_MONITOR_TRANSITION`을 독립 준비 context의 단일 등록으로 두고, 배포 인계도 그 등록에서 새 profile을 도출한다. 기존70개 물리 준비 profile과164개 reviewed-formatting 배포 profile은 각 계약대로 완전 검증한다. 원본 profile은 변경하지 않는다. 특히 원 계약에 과거 trigger가 없는 부분 소비자 목록에서도 새 profile 전체를 검사하며, 새/누락/dirty/alias/혼합 입력과 미등록 endpoint는 거절한다. 이는 report-only 의미 결손을 새 기동 필수조건으로 추가하지 않는다.

확장된 실제 준비 회귀는 predecessor manifest의 reader 비교가 후보 위치를 암묵 사용하던 phase 결함도 드러냈다. `reviewed_preparation_pair`의 기본은 실행 root를 유지하고, 원 manifest를 대사하는 parent/독립 reader 두 호출만 인증된 selected root를 명시한다. 실제 Git 두 세대를 사용한 original/reviewed/unreviewed/workflow/issuer-workflow5경우가 통과했으며 alias·잘못된 root·새 세대 거절을 추가했다. 과거 generic docstring fixture는 실제524 원 monitor·reader를 함께 보존하고, 최신 native shard/child 검증은 별도 완전 현 세대 fixture를 사용한다. private source-review 시험도 원본/후보 profile 사실을 각각 보존하며 native predicate의 verdict를 대체하지 않는다.

| 소비자와 호출 | 역할/단계 | 처리 |
| --- | --- | --- |
| `submission_bottleneck_monitor.source_gap_semantics`, health projection, tick/CLI | 보고 전용; 원천→판정→발행 | 새 감시기만 native writer/lock으로 발행; 원 결손 유지 |
| `artifact_freshness` 제출 관측 검사 | 보고 전용; 최종 health | 실제 새 observer 날짜·actor·세대·coverage 대사 |
| `verify_candidate_delay_code` | 진입 지연 정책의 배포 전/선택 후 코드 검증 | 원 정책 digest·전체 코드 profile 재검증 |
| `verify_candidate_stop_code` | 손절 정책의 배포 전/선택 후 코드 검증 | 원 정책·원천 결속 재검증 |
| `verify_candidate_holding_vote_code` | 보유 투표 정책의 배포 전/선택 후 코드 검증 | incumbent carry·원 binding 재검증 |
| `startup_validation_code_context._pairs`와 독립 policy-load child | 기동 필수; 후보/최종 준비 후P5 | 동일 등록·실제 child·거절 반례 검증 |
| ordered deployment native transition | 운영 전환 | 기존 admission/hold/CAS/lock/실패 unwind 검증 뒤 실행 |
| exact PID consumption→native Sentinel/observer→full health | 배포 최종 소비 | 원150초 예산·현재 actor·정책 불변 검증 |

Dependency disposition: 원 collection/trace/payload와 source29 계산·정리 prefix는 `reuse`이고, 원본 SHA·null·역사/현재 결손과 실패 attempt를 유지한다. 정책·strict/controller/최종화·PREOPEN·원 handoff·현재 선택본/PID는 `read-only revalidate`다. 신규 commit에 필요한 native code-handoff/preparation과 새 PID observer만 각 기존 owner로 `regenerate`하며, 검증된 원 계산을 다시 실행하지 않는다. 이후 실제 소비로 무효화된 binding만 native 순서로 재발행한다. 후보 체크리스트는 최신 운영 문서를 복사해 이미 발행된 source29 summary·현 정책 binding과08:05 완료 메모를 보존한다. 원본 선택본/strict 체크리스트는 덮어쓰지 않는다.

Replacement/removal: 기존 두 검증기와 발행 entrypoint는 현재 소비자를 유지하므로 `retained`다. 이번 monitor endpoint 중복 등록은 공유 선언으로 `consolidated`; legacy exact profile/원 reader는 기존 receipt 소비를 위해 `retained`다. 신규 module/worker/주문·provider·threshold·수량 변경은 없다. 자연 분기 및 전체 시장 원천/비용 수용은 실제 표본으로만 닫는다. 배포 전·후/PID 상태와 최종 검증 수는 완료 후 아래에 기록한다.

후보 전 capacity census: 등록 worktree311개, 그중 managed release215개, managed 디렉터리 전체220개다. `MAX_RELEASE_SET_UNITS=256`은 systemd unit 검사 한도이며 release/worktree 개수 제한으로 사용하지 않는다. 현재 native release-set 검사passed, 추정 checkout156,485,945B/2,770파일, 후보·복구 여유2개에312,971,890B를 예약하고 가용35,192,725,504B를 확인했다. 이 배포를 위한 삭제나 한도 변경은 필요하지 않았다. 후보 생성 직전에 actor/selector·가용량을 다시 확인한다.
