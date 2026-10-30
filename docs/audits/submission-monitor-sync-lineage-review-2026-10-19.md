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

확장된 실제 준비 회귀는 predecessor manifest의 reader 비교가 후보 위치를 암묵 사용하던 phase 결함도 드러냈다. `reviewed_preparation_pair`의 기본은 실행 root를 유지하고, 원 manifest를 대사하는 parent/독립 reader 두 호출만 인증된 selected root를 명시한다. 실제 Git 두 세대를 사용한 original/reviewed/unreviewed/workflow/issuer-workflow5경우가 통과했으며 alias·잘못된 root·새 세대 거절을 추가했다. 과거 generic docstring fixture는 실제003 원 monitor·reader를 함께 보존하고, 최신 native shard/child 검증은 별도 완전 현 세대 fixture를 사용한다. private source-review 시험도 원본/후보 profile 사실을 각각 보존하며 native predicate의 verdict를 대체하지 않는다.

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

사용자 추가 승인00386500788c5ee8ff36cd8b6493dd8bf992d250을 같은 통합에 포함한다. 원 후보 `startup-io-retention-20261030-003865007`의P5 `9cdb852cea2344279797005ca9cb1fbb` passed와 담당 세션287검사는 원 후보 증거로 보존한다. 최종 공통 profile은003의 native source-digest recheck를 부모로 하고 monitor/독립 reader endpoint만 추가한다. 원 source proof는 동일 호출의 인증된 byte identity 재사용에만 전달되며 child의 native 의미 검증·변경/누락 거절·원 실행기한은 유지한다. 593ecfae9의 문서 정리 이력도 Git ancestor로 보존하고 여기서 추가 운영 삭제를 수행하지 않는다. 최종 통합본에는 새 candidate/selected P5와 실제PID 소비가 필요하며, 원 후보PASS를 재사용하지 않는다.

현재 세대 시험은 최종70/164 source profile과 physical/logical 비교를 함께 사용하고, 역사 시험은 원 Git archive에서 실제 코드 세대를 대사한다. 과거 overlay를 현재 코드의 근거로 삼던 중복 assertion을 하나의 시험 helper로 통합했다. native predicate와 unknown/dirty/mixed 거절은 그대로 실행한다. 공유 체크리스트 원본SHA `0ebc83a47345a6d59e4c29ed4c7fb75cb2b361cb4ce8a26a746d0e19e931a611`은 새 owner 블록을 제외하면 후보와 동일함을 확인했다. native 달력의 다음 거래일은11/2이며, 최초 journal 생성 전 자연 분기의11/2 08:00~09:15 수용은 같은 owner를OPEN으로 유지한다.

최종 source gate: 감시기·감지기2193, native 인계213, 독립 준비/ordered transition/기동2073의 고유4479경우가 통과했다. 전환2073은 동일 최종 source에서 prefix905와 후속 범위·수정된 역사 시험을 대사한 집합이며 단일 무중단 전체 실행으로 표시하지 않는다. 원 실패 XML/log도 [회귀 manifest](../../data/audit/submission_monitor/2026-10-30-incident/integrated-validation/manifest.json)에 보존했다. 구 storage 원본은81b의 원 reader로 검증하며 현재 reader의 세대 trigger로 재해석하지 않는다. Python compile, diff whitespace, 문서 parser print-only 및 각 최종 profile 대사는 통과했다. 코드리뷰의 미결 in-scope finding은0이고 운영 배포/PID/현재 observer 수용은 아직 별도다.

변경량 기준은 사용자 인계003865007이다. 비시험 source3파일354추가/115삭제, 시험3파일688추가/99삭제다. 이 기록 추가 전 문서는3파일60추가/6삭제이며 incoming593/003의 기존 문서 정리는 별도 ancestor로 유지한다. source 순증은 원천·동기/비진입 분류, 하나의 공유 endpoint 선언 및 phase-root 명시이며 새 module/worker/Provider/정책 owner는 없다. 시험 순증은 두 실제 Git root, 전체 소비자 census와 누락/혼합/unknown 반례다. 역사 assertion 중복은 helper로 통합하고 원 profile/reader와 실패 증거는 유지했다.

## 2026-10-30 successor integration and startup report reuse

첫 통합 af07f6f6a는 09:49:14 native ordered transition complete/pass, Main4144156/start96582464의 실제 정책 소비를 완료했다. 09:50 첫 health는 실패였으며, 이후 오래된 표본이 창 밖으로 나가 artifact PASS가 된 사실을 근본 수리로 판정하지 않는다. [첫 건강 원본](../../data/audit/submission_monitor/2026-10-30-incident/successor-first-health/manifest.json)과 실제 request/trace/payload 원본을 보존했다.

- V6 audit는 실제 family-bound lifetime 대신 고정5초를 적용했다. 실제 203650/018880 관측의8.249/7.055초는 승인된9.6초 범위였다. native event policy와 선택 cell의 lifetime을 결속하고 기존 `signal_is_current`를 사용한다. 실행 임계치·기한은 변경하지 않는다. 원 두 관측은 바이트를 바꾸지 않은 격리 auditor에서 통과했다.
- 전송 캡처는 compact envelope가 없는 경우 native receipt를 누락했고, 초기/carry 네이티브 프롬프트에 generic transport header를 덧붙였다. 기존 전송 소유자가 발행된 프롬프트와 receipt를 보존한다. writer의 native canonical-JSON hash와 transport UTF-8 byte hash도 구분한다. 양쪽 해시를 유지하며 한글 입력·미전송 deadline·오염 반례를 검증한다. 과거 결속이 누락된 request를 새 PASS로 다시 쓰지 않는다.
- 관측기의 현재 health 투영은 알려진 이전PID/시간창의 실패를 현재PID 실패와 섞었다. 원 집계·오류·사례는 유지하고 인증된 actor만 분리한다. unknown/충돌/잘못된 관측 hash·공통 파싱 실패는 여전히 현재 미결이다. 주문·응답·비용은 별도 사실이다.
- 사용자 인계1ab94472fbde3818a2d76599024efd72a897b074의6개 커밋을 Git merge로 통합했다. 같은 BUY/submit generation의 호출별 손절 영수증, 검증된 probe 잔여 미제출·claim 완료 증명과 판단 호가·freshness 진단을 기존 소유자에 연결한다. 인계서/원 패치는 [보존 manifest](../../data/audit/submission_monitor/2026-10-30-incident/successor-integration/incoming-and-report-manifest.json)에 연결했다. 49578 신호/제출 수익률 상충·주문 census 결손,49677 claim 완료시각 결손은 역사 OPEN이다. 브로커 실행 거래소와 비용을 추정하지 않는다.
- 일일 보고서는 매 Main 재기동의 동기 전체 계산에서 기존 `scheduler:daily_report` 작업으로 이관했다. 당일 schema/body date가 맞는 저장본은 원 as-of 그대로 읽고 재계산/재저장하지 않는다. cache 읽기도 Main heartbeat 밖에서 실행한다. 없거나 손상된 경우 기존 builder를 사용하고,08:45 및 명시적 refresh는 기존 계산을 유지한다. `avg_bull`의 MarketRegime 소비, 모델과 전략은 유지한다. 이는 mutable 입력 재검증 완료나 실시간 시세가 아니며 snapshot의 원 생성시각을 보존한다. 원 파일 실패 보존과 동시 reader의 부분 JSON 방지를 위해 원 게시 소유자는 같은 디렉터리 임시파일→atomic replace를 사용한다.

소비자 대사: native V6 runtime/auditor와 family policy; AIO transport→trace writer→monitor 및 quality archive reader; Main scheduler→daily_report_service→MarketRegime/web/API; stop signal→SELL submit→terminal→quantity source→postclose assembler; stop/vote/delay의 native code handoff와 독립 준비 reader; ordered candidate/selected P5→실제PID→native Sentinel/observer→health다. 원래 report-only workload와 optional 일일 보고서를 새 기동 안전 요건으로 승격하지 않는다. Handoff/preparation의 완전한 새 세대와 이미 발행된 af07 predecessor를 각각 인증하며 새 trace 소비자·stop extension을 누락/혼합/unknown으로 허용하지 않는다. 역사 hash 계승은 기존 reviewed registry에서 도출하며 임의 hash를 추가하지 않는다.

Dependency disposition: 원 source29/30 수집·계산·정리 prefix·원 정책/nullable 비용·실패 attempts는 `reuse`; 발행된 active-parent·source29 strict/controller/최종화·PREOPEN·원PID 소비 증거는 원 reader로 `read-only revalidate`; 새 코드용 handoff/parity/독립 준비, 후보/선택 P5와 새PID bootstrap/observer만 기존 native owner로 `regenerate`. 현재 진행 중인 호환 worker는 관측하고 중복 복구나 전체 장후 재계산을 시작하지 않는다. 계산 prefix의 무효화가 입증되지 않은 한 재생성하지 않는다.

Replacement/removal: 동기 Main 부팅 보고서 호출은 `removed`, 기존 scheduler와 dated report owner로 `consolidated`; generic prompt 변형은 네이티브 issued branch에서 `removed`; 중복 해시 해석은 기존 writer의 별도 논리/바이트 정체성으로 `consolidated`. 기존 모델·소비자·historical reader는 현재 호출자가 있어 `retained`. 새 module/worker/정책 owner나 threshold/provider/주문·수량·안전 변경은 없다. 실제 전송·자연 손절·현재원천과 비용 수용은 native 증거가 있을 때만 닫는다.11/2 최초 journal 전 자연 분기는 같은 `SubmissionMonitorSyncLineage1019` OPEN에 남긴다.

회귀: causal monitor/transport/report/lifetime2197, 손절·수량·vote/delay612, 독립 준비49, 실제 인계35가 최종 소스에서 통과했다. 회귀 원본 XML/log와 실패 시도는 successor-integration에 보존한다. 더 넓은 독립 준비 실행은246 PASS prefix 후 불필요한 반복 I/O를 피하려 중단했고 전체 PASS로 표시하지 않는다. merge 도중 실행된16 SyntaxError 사례와 원 실패도 보존하며 최종2197 정상 실행으로 별도 대사했다. 최종 ordered/P5 회귀·source compile·diff·문서 parser, 운영 전환과 새PID/현재 건강의 완료는 아래 native 영수증으로 별도 기록한다.

최종 추가 gate: ordered/P5660 통과로 고유 총3553검사·실패0·건너뜀0이다. compile29개와 diff/parser도 통과했다. [최종 검증 manifest](../../data/audit/submission_monitor/2026-10-30-incident/successor-integration/review-validation-manifest.json)에 범위별 원본 XML/log·실패 시도를 보존했다. 기준af07 대비 변경량(source/tests/docs)은 manifest에 별도로 기록했으며, 소스 순증은 native 영수증·논리/바이트 구분·완전한 공유 세대와 비동기 dated snapshot 재사용을 위한 것이다. 기존 owner/entrypoint로 통합했고 신규 실행 owner는 없다.

10:48:54 bbb6b82b9의 첫 ordered attempt는 **drain/hold/선택 이전** `deployment_trailing_report_not_current`로 실패했다. 당시후계PID는 없고 incumbent4144156/start96582464와 selector를 보존했다. 이는 수리된 AIO/trace/stop handler/review가 실제 trailing CODE_PATHS에도 포함되기 때문이다. 후보P5 전에 해당 후행 보고서 reader를 확인하지 못한 절차 누락이며, 기존 지침의 나머지 소비자 preflight를 반복 이행한다. 실패 영수증은 그대로 보존하고 단계 완료나 후보PASS를 전체 배포 성공으로 바꾸지 않는다.

수정된 [dependency disposition](../../data/audit/submission_monitor/2026-10-30-incident/successor-integration/revised-dependency-disposition.json)은 source29→target30의 trailing report/currentness만 `regenerate`로 변경했다. native source_reuse 사전검사4증명·미증명20,136,232B가 원33,554,432B 한도 내에서 통과했다. 원 holding/PREOPEN/정책·추출 provenance·입력·역사결손은 유지하고 semantic verdict를 재사용하지 않는다. 기존 admission/disk/checkpoint owner로만 실행하며, 원 보고서 소비자와 수량 소비자까지 순서대로 확인한 다음 최종 후보/선택P5를 새로 발행한다. 첫 실패 attempt의 immutable commit 경로는 유지한다. 새 attempt의 문서 변경도 이 실패와 수정된 disposition을 기록한 실제 검토 이력이다.
