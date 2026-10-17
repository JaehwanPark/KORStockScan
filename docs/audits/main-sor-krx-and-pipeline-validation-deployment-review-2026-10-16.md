# SOR KRX 지정과 pipeline 검증 경계 수리 — 2026-10-16

## 승인과 변경 범위

사용자는 통합 SOR 체결의 소비 시장을 KRX로 고정하고, 정책 발행·기동·감시가 과거 pipeline 원장을 반복해서 읽는 경로를 제거하도록 지시했다. 모든 보완 후 `35beec0fd584d0b01cbd7b965f1c271161fd46bf`를 통합해 배포·재기동하는 권한도 명시했다. 지정 커밋은 충돌 없이 cherry-pick `be1108609`로 통합했다. 이는 배포/PID 소비 영수증이 아니다.

## 구현과 재리뷰

- 시장 귀속은 `src/trading/market/execution_venue.py`의 순수 계약으로 소유한다. 10/16 이후 aware 체결 시각, broker venue UNKNOWN 및 원본 `0/SOR 또는 통합/Y`에서만 KRX를 지정하고 `user_2026_10_16_sor_execution_venue_krx`를 기록한다. 명시적 KRX/NXT·충돌·원본 누락·이전 날짜에는 적용하지 않는다. 주문·시세 route를 변경하지 않는다.
- 원 FID·broker UNKNOWN·provenance false·비용 결손과 기존 9/27 참고시장 승인을 보존한다. 체결 축→snapshot/ACK→매도 후 관측→완료 투영→장후 결합에 지정 근거와 verified=false를 전달한다. native venue-specific promotion을 합성하지 않는다.
- revive 후보는 같은 완료 leg의 frozen snapshot을 우선해 주문·체결번호를 전달한다. `unknown` 예정 시세 경로는 세션 계약에서 선택하고 실제 BBO는 원 exact item/session/freshness 검증을 유지한다. 과거 놓친 관측창을 소급 복구하지 않는다.
- 공식 체결 시각은 수량 보존·정확한 주문/체결번호·체결 authority로 독립 결속한다. 비용 미상 때문에 시각을 지우지 않으며 strict 경제성과 손익 결손은 유지한다.
- 정책 v2–v6와 active-code handoff는 canonical 일별 pipeline의 봉인된 참조 형식/날짜/해시를 검증하고 raw bytes를 재해시하지 않는다. 원천의 현재 내용/존재를 검증했다는 주장이 아니다. 발행 보고서·정책·코드·다른 원천과 연구 producer의 검증은 유지한다.
- full/artifact detector는 기존 observer digest session을 연결한다. 파일 identity 변경 시 다시 읽고 모든 semantic check는 매번 실행한다. `validation_io`에 실제 전체/재사용 바이트를 기록하며 verdict는 캐시하지 않는다.
- PREOPEN 원 commit→검토 코드의 정확한 source hash pair를 결속한다. 정책·임계치·수량·provider·custody·수동 제외와 기존 timeout은 유지한다.

## 검증과 운영 수용

관련 619개, 영향 경로 1,989개, 집중 계약 27개와 최종 receipt/report/detector/handoff 회귀 2,473개가 통과했다. native 동일 workload는 현재 선택본과 수정본 모두 128 scope·76,800행·594 hit·동일 signal SHA이며 provider/주문 호출 0이다. [native 비교](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/native-policy-parity.json).

pipeline archived 참조의 raw open 0, 잘못된 해시/clean-baseline 이전 거부, 다른 보고서 변경 탐지, detector의 실행 간 재사용·의미 재평가·변경 재읽기, SOR 원본 불변·NXT 보존·잘못된 authority 거부·비용 null을 검증했다.

기존 `DirectFamilyPreopenPolicyHandoff`/`HoldingProfitExitSourceContractRepair`가 실제 배포·PID·정규 후속 수용을 소유한다. 리뷰 후 immutable release/code handoff와 ordered 정지→선택→준비→시작→독립 PID 검증을 진행한다. 원 실패·source/economic OPEN을 보존하며 역사적 journal/DB를 일괄 수정하거나 관측을 합성하지 않는다.

## 첫 배포 후 발견한 잔여 읽기와 추가 보완

`8d1fb29fda99c3ac867f84f5f876ea034695a0db`는 원 `35beec0f`를 ancestor로 포함하고 11:33:03 native ordered 배포를 완료했다. Main PID3314987/start18181121의 정책 소비를 확인했다. 이 배포 완료가 읽기 개선의 최종 수용은 아니다.

11:35의 /proc 관측에서 Main은 7,394,107,688-byte 10/13 pipeline을 열고 있었다. 별도 holding-exit sentinel은 당일 pipeline/166MB 이벤트 cache, buy-funnel sentinel은 89MB SQLite를 읽고 있었고 monitor snapshot도 독립 실행 중이었다. 이 관측은 파일 metadata와 프로세스 I/O 카운터만 사용했다.

raw open 직전 중단하는 read-only audit로 `artifact_freshness → historical_checklist_for_observer → verify_bootstrap → _observer_delay_generation → verify_source → family_source_ledger_issues → byte_generation(pipeline)` 경로를 확인했다. 지연 정책의 기동 준비도 같은 검증 함수를 사용한다. 기존 반복 읽기 제거에서 이 ledger 내부 경로가 누락되었으므로 재개한 결함이다. 10/12 원장 open 직전 스택은 [원 증거](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/raw-open-first-stack.json)를 보존한다.

추가 구현은 지연 정책 bootstrap/prepare 및 수량 terminal 소비에서 pipeline 참조만 검증한다. 봉인 ledger, compact source bytes, 정확한 overlap, 보고서/정책/코드 결속은 유지하고 연구 producer의 기본 full 원천 검증은 보존한다. canonical plain/gzip/late 참조를 같은 계약으로 처리한다. 실제 10/15 발행 지연 보고서의 수정 consumer 검증은 원장 open 0, 0.207초에 통과했다. 이는 해당 consumer 한 회 측정이며 전체 기동 시간은 후속 배포에서 별도로 측정한다.

observer digest의 role 공통 잠금이 전체 검증 동안 유지되어 다른 observer가 2초 후 `ValidationDeferred`로 중단되는 문제도 확인했다. generation 잠금으로 검증을 분리하고 role 잠금은 발행/retention에만 사용한다. 같은 generation 경합 시 artifact 관측을 명시적으로 deferred/불완전으로 남기고 독립 health 검사는 계속한다. cache 발행 실패로 semantic 결과를 PASS로 바꾸거나 원장 전체 읽기로 재시도하지 않는다.

`5f3bbfc01` 추가 배포는 11:56:37 selected 단계에서 `pre_submit_delay_generation_changed`로 차단됐다. 추가한 `pipeline_source_validation` 표시 필드가 frozen PREOPEN의 전체 영수증 비교를 바꾼 결함이며 정책/임계치 변경은 없다. 해당 필드를 제거하고 영수증 ABI 회귀검사를 추가한다. 원 failed status·hold·native predecessor를 보존하고 기존 `StoppedDeploymentRecovery`로 선택 단계부터 복구한다. 실패를 PASS로 덮거나 hold를 임의 해제하지 않는다.

첫 중단 복구는 `intraday_native_predecessor_hash_invalid`로 mutation 전에 차단됐다. 원 8d1fb29fd PID는 PREOPEN 직접 predecessor가 아니라 `intraday_policy_preserving_handoff` 소비를 완료했으므로 native 영수증이 없는 것이 정상이다. 복구 분기를 보완해 원 live preflight PASS·동일 PID/start/cwd·기존 prepared handoff/consumption·manifest/PREOPEN와 모든 frozen bytes를 검증한다. 실제 intraday 소비를 native 소비로 재분류하지 않는다. recovery/인계 회귀 2,111개를 통과했다. 기존 4개 family의 component hash와 검증 plan은 이 deployment-only 보완으로 변하지 않으며 정확히 같은 generation fixture를 검증해 재사용한다.

## 실제 배포·현재 PID·정규 감시 수용

- 최종 선택 commit은 `4c65523b20469ca6d195f22293b21fb2f253f7ee`, 검토 source는 `7588246dbbf2383fce762b4781aa9dfd3eb044a4`이다. 원 `35beec0fd584d0b01cbd7b965f1c271161fd46bf` ancestor를 확인했다.
- 정식 중단 복구는 12:08:05 PASS로 완료했다. Main PID3377997/start18399636, 정확한 선택 release cwd, singleton, `actual_pid_consumed=true`, hold 없음과 독립 bootstrap/인계 검증을 확인했다. 원 실패 status와 원 소비 영수증은 보존했다. 원 Main은 11:56:32 정상 종료됐고 새 Main 시작은 12:07:34였다. 이 중단 시간을 정상 기동 소요에서 숨기지 않는다.
- 선택 12:07:08→인계 준비 12:07:17→PID 소비 기록 12:07:53→독립 검증 완료 12:08:05였다. 선택 후 인계 준비는 이전 60.6초에서 8.9초, 선택→독립 완료는 이전 192.1초에서 56.9초로 줄었다. 이전 release 검증 코드가 수행한 2회 full 원장 읽기와 실패 수리 시간은 이 비교 밖의 원 증거로 남아 있다.
- 0.5초 간격의 실제 기동 관측 114회에서 새 Main의 pipeline FD는 관측되지 않았다. 현재 선택본의 별도 full audit open stack에서도 과거 pipeline 원장 open은 0이며, 당일 수동관리/보유 이상 확인을 위한 최근 16MiB tail 경로만 관측했다. 샘플링만으로 모든 짧은 open 부재를 증명했다고 주장하지 않는다. 전체 digest 비용과 Python semantic 읽기 비용도 구별한다.
- optional 연구는 정식 configure와 calendar 검증으로 새 선택본에 재결속했다. enabled/notify_enabled와 기존 운영 설정·다른 cron 행을 보존했고 worker/provider/주문/수동 알림은 실행하지 않았다.
- 12:08:32의 `submission_bottleneck_monitor: stale; observer_generation_not_current`는 중단 동안 남은 11:55/이전 PID 보고서였다. 12:10 정규 wrapper가 12:10:41 관측→12:10:52 발행한 새 PID3377997/최종 commit의 현재 보고서로 갱신했다. 후속 full detector에서 두 실패 원인이 사라지고 artifact severity는 warning, 나머지 6개 detector는 PASS였다.
- 남은 의미 경고는 holding `policy_binding_gap`, entry-cancel/rising-missed의 역사적 `policy_generation_unverified`, scanner 식별 평가 증거 부족이다. 이를 freshness 회복이나 현재 fixture PASS로 경제성/원천 의미 복구로 바꾸지 않는다. 기존 `HoldingProfitExitSourceContractRepair`, `DirectFamilySourceRepairEntryCancelWait`, `PostcloseStructuralPolicyCompletion1011`, `NonfixedDispatchReadinessReview1012`가 각 원 계약을 계속 소유한다.
- 별도 `intraday_light` snapshot PID3374819가 2,024,840,392-byte 전일 `trade_review_2026-10-15.json`을 열었고 RSS 약4.8GB인 점도 확인했다. 이는 제거한 정책 소비의 과거 pipeline 재해시와 별도인 보고서 집계 비용이다. 12:11:57 재관측에서는 해당 snapshot 프로세스가 없었다. 전체 성능 문제가 모두 해소됐다고 주장하지 않는다.

수용 증거는 [배포 terminal](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/ordered-deployment-stopped-final-result.json), [기동 프로세스 관측](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/stopped-final-startup-process-samples.json), [현재 보고서·detector](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/postdeploy-current-monitor-and-detector-verification.json), [optional 재결속](/home/ubuntu/KORStockScan/tmp/sor-krx-pipeline-validation-deploy-20261016-1100/optional-stopped-final/optional-root-rebind-receipt.json)이다. source review·배포·자연 감시·원천 의미/경제성 수용을 구별한다.
