# 장후 종료 후 계산 수정본 통합 및 다음날 준비

현재 상태는 **최종 통합본 `e74ec5c56` 배포, source14/target15 기동 준비 및 독립 검증 완료**다. 다른 세션의 장후 작업 완전 종료 후 2026-10-15 01:31:55 KST에 `4691d2a70`에서 `e74ec5c56c220b84520578f47c60a61d3e2ac930`으로 선택했다. [실제 선택 영수증](../../tmp/sentinel-integrated-postclose-20261014/selector-publication-actual-e74.json)의 선택 SHA는 `0ea6160e39a27f7967157e8ef2c258b585d3c70baddff219e999cdad195f1e2c`다. 후보 재결속·직접 downstream·전체 controller/strict·`prepared_verified`와 별도 `current_full_contract` 검증이 PASS했다. 원천 summary/cache 세대도 native API로 복구했다. Main은 정지 상태이며 `startup_performed=false`, `actual_pid_consumed=false`다. 선택 영수증의 과거 `preparation_performed=false`는 보존하고 이후 준비 완료를 별도 영수증으로 판정한다. source/publication은2026-10-14, 다음 영업일은2026-10-15다. 아래 검토·실행 계약과 최종 실제 결과를 구분한다.

## 통합 범위와 코드 검증

첫 통합본 `4c4996d2aa44686f18aab19b0ecc7601be1cd15f`는 장후 복구본 `8a252a6e9`와 계산 수정본의 문서 종결 commit `96076385b`를 병합했다. `a179bb42d`의 Sentinel 계산/정확한 parser-owner migration 및 시험 4파일을 byte 동일하게 보존하고, 다른 세션의 native ancestry·보조 membership·최종 handoff 복구 6파일도 보존했다. 문서 충돌은 원 계산 수정 인계와 장후 복구 인계를 모두 유지해 해소했다. 이후 `bdf6ffe6a`와 준비 API를 통합한 `e7eec7a83`도 빌드했지만 선택하지 않았다. 다른 세션이 00:39 선택한 `4691d2a70`의 역사 observer 판정·당일 후보 인계·날짜 전환 code handoff와 새 체크리스트를 다시 통합했다. 원 두 OPEN owner는 이 세션에서 중복 생성하지 않고 최신 이관본에 추가 Acceptance만 연결한다. 최종 build와 실제 선택은 각각 새 영수증으로 구분한다.

12개 관련 suite의 최초 실행은 1,102 PASS와 격리 worktree의 불변 fixture 부재 3건이었다. 필요한 5개 fixture의 원 bytes를 검증·복사한 뒤 해당 3건이 PASS했다. 따라서 서로 다른 1,105개 시험이 모두 통과했다. 원 실패 로그를 보존하며 최초 명령이 성공했다고 기록하지 않는다. 별도 독립 리뷰 4개 suite의 297 PASS는 중복 수이므로 합산하지 않는다. Python compile, wrapper `bash -n`, diff 검사와 코드 리뷰의 미해결 결함은 없다. 실제 provider·주문·Telegram을 호출하지 않았다.

증거는 [통합 build](../../tmp/sentinel-integrated-postclose-20261014/integration-build.json), [통합 검증](../../tmp/sentinel-integrated-postclose-20261014/integration-static-validation.json), [독립 코드 리뷰](../../tmp/sentinel-integrated-postclose-20261014/source-integration-independent-review.json)에 보존한다. Main/manual custody, 매매 가드, 기계/보조 판단값, native 5초 계약은 변경하지 않는다.

## 배포와 정책 준비의 경계

다른 세션이 소유한 정확일자 Main 성공·전체 strict PASS·독립 producer를 요구하는 controller DONE·tuning 성공·다음날 준비와 실제 actor/lock 종료를 확인하기 전에는 selector를 전환하지 않는다. 이후에도 현재 selector가 후보의 Git 조상인지 재검증한다. 장후 owner가 추가 수리를 배포했다면 그 코드를 먼저 통합·리뷰한다.

전환은 검토된 정지 배포 도구로 기존 selector의 원 bytes와 정책·종료 영수증을 보존한 뒤 수행한다. 새 selector의 과거 PID/transition 필드를 현재 소비 증거로 재사용하지 않는다. Main은 정지 상태를 유지하며 새 릴리스의 `actual_pid_consumed=false`를 기록한다. 관련 도구의 [입력 계약](../../tmp/sentinel-integrated-postclose-20261014/stopped-selector-input-contract.md)과 [root 검증](../../tmp/sentinel-integrated-postclose-20261014/selector-publisher-root-review.json)을 따르며 실제 발행 결과는 별도 영수증으로 확인한다.

다음날 후보의 코드 결속만 새 릴리스로 갱신하고 기계 membership·threshold·보조 입력/응답·선택값과 현재 정책 pointer를 보존한다. 원 current 정책 `99c894cb...`의 33개 native 파일과 정확히 일치하는 불변 `bd40c7f12`를 full parent validator로 검증했다. 이 검증은 code-handoff 파일 읽기를 차단한 상태에서도 통과했다. 새 후보의 명시적 activation-parent proof가 정상 PREOPEN에서 동일 원 정책 조상을 검증한다.

필요한 직접 downstream은 source14 prompt consumer → summary handoff → 전체 controller/strict → target15 prepare/verify다. 완료된 기계·보조 정책 계산을 다시 실행하지 않는다. 원 source·정책·실패 이력과 원 producer 영수증을 보존한다. [재결속 절차 리뷰](../../tmp/sentinel-integrated-postclose-20261014/rebind-helper-independent-review.json)는 20개 격리 mock을 통과했으며 실제 실행 증거를 대신하지 않는다.

당초 `stage_code_refresh`의 미래 target 계약을 보존한 별도 준비 API를 구현했다. 이후 다른 세션이 승인한 `4691d2a70`의 명시적 source/publication 당일 재결속 확장도 원본 그대로 통합했다. 장후 종료가 자정을 넘겨 기존 [준비 자동화](../../src/engine/automation/next_preopen_readiness.py)에 `stopped_postclose_candidate_rebind`를 추가했다. 실제 대상 거래일의 07:35 전, source/publication 전일, 정확한 다음 거래일, Main/supervisor 정지·정상 장후 격리·미시도 PREOPEN·현재 정책 미활성·전체 controller/strict/stage 종료를 모두 요구한다. release/PREOPEN/producer/publisher 잠금의 inode와 선택/원 후보/현재 pointer/원천의 해시를 재검증하고 기존 native 불변 builder·원 정책 조상 full validation·판단값 equality만 사용한다. 원 후보의 기존 code-refresh 조상도 보존한다. 발행 후 검사 실패는 이미 발행된 successor를 명시하며 원 파일을 덮어써 되돌리지 않는다.

우리 준비 API는 최신 `4691d2a70`의 native 정책 33파일을 그대로 유지한다. BDF 이후 다른 세션의 native2파일 변경은 그 세션의 검증·source lineage로 구분하며 이전 native map을 최신 검증으로 재사용하지 않는다. 기존 준비 자동화 15개 top-level 정의의 AST도 보존했다. 새 API는 현재 pointer·활성화·기동·provider·주문을 수행하지 않는다. 기계/보조 producer의 dependency에 준비 자동화 파일이 포함되지 않으므로 정책 계산을 재실행할 source 변경을 도입하지 않는다. retained immutable release의 원 단계 코드를 검증하는 기존 계약은 계속 적용한다. 표적 67개 및 독립 3-suite **130개** 시험이 통과했으며 67은 130에 포함되므로 합산하지 않는다. [자체 리뷰](../../tmp/sentinel-integrated-postclose-20261014/stopped-postclose-same-day-rebind-self-review.json), [root 리뷰](../../tmp/sentinel-integrated-postclose-20261014/same-day-rebind-root-source-review.json), [독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/stopped-readiness-independent-review.json)에 source/시험 해시를 보존한다. 날짜 경계는 [원 진단](../../tmp/sentinel-integrated-postclose-20261014/same-day-rebind-boundary-readonly-review.json)과 구분하며, 이 코드 검증은 실제 후보 발행이나 준비 성공을 뜻하지 않는다.

## 원천 세대와 성능 수용

20:59의 승인된 raw-row 제외는 식별된 결함 15행을 제거하면서 10/14 raw 파일을 교체했다. 기존 summary/cache는 그 이전 inode/offset을 가리키므로 source-prefix 검증 실패가 정당하다. 이를 빈 입력이나 성공으로 바꾸지 않는다. 원 derived artifacts를 보존하고 기존 native API로 정확일자 summary/cache를 명시적으로 재구축하는 절차를 검토했다. 이 작업은 다른 세션 종료 후 수행하며 실제 보고서 계산과 별도다. 검토 중이던 source14 과거 canonical CLI 발행 검증은 [원천 결속 인과 확인](../../tmp/sentinel-integrated-postclose-20261014/cold-cli-policy-readiness-input-causal-review-v2.json)에 따라 실행 전에 취소했다. 최종 source-quality audit의 `machine_terminal_tuning_gate`와 final-contract가 canonical Sentinel JSON의 SHA와 inode·mtime·ctime을 포함한 원 세대를 참조한다. CLI는 해당 JSON을 반드시 발행하며 `--dry-run`도 쓰기를 생략하지 않으므로, 동일 bytes의 atomic replace도 원 세대 결속을 유지하지 못한다. 원 canonical JSON·감사·final-contract·기존 owner 영수증을 보존한다. 현재 날짜만 허용하는 observer를 과거14일로 재실행하지 않으며15일 자연3슬롯 owner를 유지한다.

[원천 세대 분석](../../tmp/sentinel-integrated-postclose-20261014/postclose-source-generation-review.json), [제한된 재구축 계획](../../tmp/sentinel-integrated-postclose-20261014/source-rebuild-plan.json), [독립 절차 리뷰](../../tmp/sentinel-integrated-postclose-20261014/scoped-source-rebuild-independent-review.json)를 보존한다. 원 source bytes·삭제행 제외 manifest·코드·선택 해시를 고정하고 native lock과 총 600초 한도를 사용한다. 실제 CLI 130초, observer 40초, 전체 180초의 수용 한도와 자연 3슬롯 검증은 늘리지 않는다.

[감사 digest와 실제 인계 호출 경로](../../tmp/sentinel-integrated-postclose-20261014/audit-digest-deployment-callgraph-review.json)는 계산 코드 변경만으로도 기존 final audit의 현재 코드 재사용 digest가 달라짐을 구분한다. 이는 기존 audit bytes나 C15/current 정책의 자동 무효화를 뜻하지 않는다. 검토한 정지 선택·후보 재결속·consumer/summary/controller·prepare/정상 PREOPEN/기동 경로는 원 감사·정책·단계 영수증을 검증하며 현재 코드의 final-audit 재사용 검사를 호출하지 않는다. 이 정적 확인으로 실제 새 선택본의 native closure와 prepared verify를 대체하지 않으며, 과거 감사나 완료 producer의 재생성을 추가하지 않는다.

별도 source-only 복구는 검토한 native summary/cache 재준비만 수행하고 raw·AI5종 원천·canonical source14 보고서를 보존한다. 재준비 대상6개 derived 파일과 memo는 확인된 final-contract dependency와 겹치지 않았으며 이 작업을 새 final-audit PASS나 보고서 발행 성공으로 기록하지 않는다. 필요하면 원 source13/14와19:55:39.513196 cutoff를 사용하는 `build_buy_funnel_sentinel_report`의130초 build-only 계산 진단을 별도 실행 절차로 검토할 수 있다. 그 경우 반환 JSON과 실행·보존 증거만 E의 새 경로에 저장하고 native `main`/`save_report_artifacts` 또는 경로 override로 canonical 발행을 우회하지 않는다. 이 진단은 실제 CLI 발행 검증·10/15 자연3슬롯·장중 SLA 수용에 포함하지 않는다. 실제10/15 source의 정규 실행은 기존130/40/180초 및 기존 owner에서 별도로 수용한다.

## 최종 수용과 남은 자연 실행

설치된 예약은 10/15 **05:35 finalization, 07:35 PREOPEN, 07:55 Main 정상 기동**이다. 현재의 배포 준비와 `prepared_verified`는 향후 PREOPEN 적용, 새 PID 소비, 자연 주문/체결/terminal 또는 비용 후 손익을 대신하지 않는다. 미래 예약 실행은 due 전까지 `not_yet_due`다.

최종 결과에는 선택 commit/root, 원 정책 보존, 정확 source14/target15 준비 및 독립 verify, 설치 cron/router, Main 정지·startup custody를 함께 기록한다. 기존 `DirectFamilyPreopenPolicyHandoff`, `NonfixedDispatchReadinessReview1012`, `AuxiliaryCircuitRecoveryRepair1012`의 소유권과 Acceptance/History를 보존한다. 문서는 print-only parser만 검증하고 외부 Project/Calendar 동기화는 실행하지 않는다.

최종 리뷰에서 canonical target bootstrap env/manifest/verify의 잔존과 발행 중 출현을 모두 거부하도록 보완했다. 원후보/current와 발행 후 실패 증거를 보존하며 준비 경로·전일 파일과 구분한다. [보완 리뷰](../../tmp/sentinel-integrated-postclose-20261014/stopped-readiness-bootstrap-absence-self-review.json)의86개 시험은 기존67개를 포함한다. 최신 통합 source에서 독립 검증을 다시 결속한다.

현재 reader의 날짜 인계도 완성한다. `4691d2a70`이 발행한15일 code handoff는 원 날짜·root·commit에만 유효하므로 그대로 보존한다. 새 통합본의 정상 issuer로 별도 commit 경로의15일 code handoff를 선택 전에 발행하고 current pointer/정책값·원 후보·원 인계를 대사한다. 이후 그 영수증을 포함한 fresh manifest로 selector를 전환한다. 기존 attested BD40 activation-parent 경로는 유지하며 새 인계를 정책 재선정이나 Main 기동으로 사용하지 않는다.

첫 읽기 전용 배포 수집은 전체 native 원천 검증의120초 한도에서 중단됐고 selector/정책은 그대로다. 원 실패를 보존한 [600초 유지보수 검증 보완](../../tmp/sentinel-integrated-postclose-20261014/native-closure-budget-repair-review.json)은 semantic 검사를 생략하지 않는다. 이 시간은 보고서130초·observer40초·총180초 수용 예산과 별개다.

최신 `4691d2a70` 병합과 canonical bootstrap 부재 보완을 포함한 최종 source에서 readiness·Main source·controller·artifact freshness 4개 suite를 독립 실행해 **391 PASS (52.42초)**를 확인했다. 이는 과거1,105/130개와 중복이 있어 합산하지 않는다. `a179bb42d`4파일·최신 장후5파일·native33파일의 bytes 일치와 compile/diff도 확인했다. [최신 통합 독립 리뷰](../../tmp/sentinel-integrated-postclose-20261014/integration-4691-readiness-independent-review.json)에 새 source15개와 검증 로그를 결속한다. 검토 범위의 미해결 결함은 없다.

01:39:04 KST [실제 후보 재결속](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-stage-20261015T013205-f4b219d5/receipt.json)이 PASS했다. 새 후보 bundle은 `9f4aeb484ef20db8f2533decbf2f2ee40f8f5573501e6c870ead2643cbc37d14`, 파일 SHA는 `75a5d4c5cde4ed7da98b221263e806b934f95af6099d159e74bd063de9a0a1a7`이다. 원 current·기계/보조 판단값·원 producer 영수증은 그대로이며 producer를 재계산하지 않았다. consumer·요약·controller·target15 prepare/verify는 이 결과 뒤 별도로 통과했으며 아래 실제 영수증으로 구분한다. 선택 발행은 [root 실제 관찰](../../tmp/sentinel-integrated-postclose-20261014/selector-publication-actual-e74.json)에 보존한다.

Build-only 진단의 결과 경로는 E로 제한하더라도 native summary/cache/compact/slim 및 memo 생성·정리는 일어날 수 있다. 따라서 실행한다면 원 소형 metadata/memo와 보호 보고서·정책·준비 자료를 보존·대사한다.

## 최종 실제 실행 결과 — 2026-10-15 02:10 KST

다른 세션의 장후 controller DONE00:57:34, 전체 검증01:05 및 최종 종료 기록01:11:37을 확인하고 원 증거를 [별도 보존](../../tmp/sentinel-integrated-postclose-20261014/other-session-final-closure/)했다. 그 뒤 선택과 아래 직접 downstream을 수행했다. 완료 기계·보조 producer의 원 판단값/영수증, 현재 활성 정책 bundle `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215` 및 current pointer SHA `51715af029bb299e5a8f9ae68577588dadc4b99224d95d10d500b7f2d5b62902`는 유지했다.

| 단계 | 실제 종료 KST | 결과·증거 |
| --- | --- | --- |
| 통합 commit의15일 code handoff | 01:16:13 | [PASS, 원 인계와 current 보존](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-code_handoff-20261015T011350-36fd08b6/receipt.json) |
| 정지 배포 선택 | 01:31:55 | [e74ec5c56 선택, Main 기동 없음](../../tmp/sentinel-integrated-postclose-20261014/selector-publication-actual-e74.json) |
| 후보 재결속 | 01:39:04 | [PASS, bundle9f4aeb48·판단값 동일](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-stage-20261015T013205-f4b219d5/receipt.json) |
| consumer | 01:39:57 | [PASS](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-consumer-20261015T013949-5ff299f0/receipt.json) |
| summary | 01:43:38 | [PASS](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-summary-20261015T014021-acde8bfb/receipt.json) |
| 전체 controller/strict | 01:50:28 | [DONE 및 전체 검증 PASS](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-controller-20261015T014355-32a4b8cd/receipt.json) |
| target15 prepare | 01:53:53 | [prepared_verified](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-prepare-20261015T015055-dff2e330/receipt.json) |
| 별도 verify | 01:56:18 | [current_full_contract, findings 없음](../../tmp/sentinel-integrated-postclose-20261014/rebind-c15-final-verify-20261015T015412-4601781a/receipt.json) |

[실제 readiness](../../data/runtime/policy_bootstrap/prepared/2026-10-15/2026-10-14_33620d4fe1a2db56_e74ec5c56c220b84/readiness.json)의 SHA는 `2f78588be2051bb6fd54c5c391dc08e7e830cc5634ae1decc5342d3d5a5a9fa6`다. [독립 실제 준비 리뷰](../../tmp/sentinel-integrated-postclose-20261014/actual-e74-prepared-independent-review.json)는 이 receipt와 원 controller/strict/7stage, 후보·current·128scope, source14/target15/e74 및 당일 canonical bootstrap 부재를 대사했다. 테스트 결과나 과거 준비 receipt를 현재 준비 완료로 대체하지 않았다.

원천 재준비 첫 호출은 상대경로 때문에 `worker_parent_identity_invalid`로 native 작업 시작 전에 종료했다. [원 실패](../../tmp/sentinel-integrated-postclose-20261014/native-source-rebuild-20261015T0159-e74/receipt.json)를 보존하고 코드 변경 없이 절대경로로 호출했다. [두 번째 실제 실행](../../tmp/sentinel-integrated-postclose-20261014/native-source-rebuild-20261015T0200-e74/receipt.json)은 **342.171895초, exit0, PASS**였다. native600초 유지보수 한도 안에서 원 derived6개를 보존하고 summary schema2/5,896행과 cache schema20/176,333행을 raw EOF2,281,158,235B까지 복구했다. decode 오류는0이며 raw 전후 SHA는 `ce8828653e998121e029bedf84fac9e67da79f853f89ce05b68065c5bb5f53d3`로 동일하다. 원 raw/AI/canonical 보고서는 변경하지 않았다.

[독립 복구·보호 상태 리뷰](../../tmp/sentinel-integrated-postclose-20261014/independentsource-rebuild-and-protected-state-review.json)는 보호88파일의 bytes·세대, 부재10개, raw13/14와 AI5종 세대7개가 불변임을 확인했다. 실제 SQLite state도 cache generation·offset796,005,257과 일치했다. 큰 raw/AI/archive 본문 해시는 독립 리뷰에서 반복하지 않았고 native 전후 해시·보존 영수증을 대사했다. source-window는 forward-only/row0이며 과거 관측을 소급 채우지 않았다. 실제 canonical CLI·observer와 선택적 build-only 진단은 실행하지 않았으므로 보고서130초·자연3슬롯 수용은 미완료다. 기동 준비 계약과 보호 원천을 유지한 것이 이번 복구의 완료 범위다.

[cron·route 검증](../../tmp/sentinel-integrated-postclose-20261014/final-route-plan-cron-e74.json)은 설치된05:35 finalization·07:35 PREOPEN·07:55 Main·주간5분 Sentinel이 target15와 새 선택본을 해석함을 확인했다. [실제 release-set 검증](../../tmp/sentinel-integrated-postclose-20261014/final-release-set-actual-e74.json)도 PASS다. [02:13:28 최종 정지 상태 확인](../../tmp/sentinel-integrated-postclose-20261014/final-document-closure/final-stopped-readiness-observation.json)에서 Main PID·관련 actor·tmux bot은 없고 `actual_pid_consumed=false`이며 restart flag·startup hold·당일 canonical bootstrap도 없다. 선택·readiness·현재 체크리스트 SHA와 선택 릴리스의 source/deploy 상태를 다시 대사했다. 예약 시각 전 단계는 `not_yet_due`다.

현재15일 체크리스트 SHA `58da7e5d91ca8de637d09212dca477273ccf45a29cc55082c2571bcd421630ba`는 준비 완료 후 그대로 보존한다. `DirectFamilyPreopenPolicyHandoff`에서05:35/07:35/07:55 실제 결과·새 PID 소비를, `NonfixedDispatchReadinessReview1012`에서08:00/08:05/08:10 자연3슬롯 및130/40/180초 한도를, `AuxiliaryCircuitRecoveryRepair1012`에서 자연 AI timeout·제출·비용 후 경제성을 확인한다. 기존 Acceptance/History와 단일 owner를 유지하며 새 일정·외부 동기화는 실행하지 않았다. 현재 검토 범위에 미해결 결함은 없으며 미래 자연 실행의 성공은 아직 주장하지 않는다.
