# 제출병목 수리 배포와 다음 영업일 준비 검증 — 2026-10-17

사용자의 "배포 및 재기동 승인. 다음 영업일 에러없이 정상가동 가능한지 점검" 지시에 따른다. 대상은 [우선 수리 검토](main-post-auxiliary-priority-repair-review-2026-10-17.md)의 `d942ba69b`와 정확한 코드 인계 후속 `a008631c5`, capability 세대 연결 보완 `c5aeda844`다. 앞선 위험 입력50점 연구 후보는 운영에 적용하지 않는다. 기존 승인된 두 PRE 보조정책과128개 연결, Main/manual custody, 수량·가격·시간·hard safety는 원래 계약대로 인계한다.

## 원점과 검증 범위

원 선택 릴리스는 `auxiliary-next-session-20261017-57d4d4664`다. 10/17은 토요일이며 Main/supervisor PID가 없다. 원 source10/16·target10/19의 정책/준비/체크리스트·selector bytes를 `data/report/post_aux_priority_deployment/2026-10-17/`에 보존했다. 최종 후보는 `post-aux-priority-20261017-c5aeda844`, 커밋 `c5aeda844dfab36146d04e6305cb29508cd47d4f`다. 앞선 `a008631c5`의 미발행 시도와 원 검증 bytes를 보존하고, 후속 시도는 `attempts/c5aeda844/`에 분리했다. 원 작업본의 다른 미커밋 변경은 통합하지 않았다.

토요일 재기동을 성공으로 기록하지 않는다. 정규 `restart.sh`는 기존 Main PID가 없으면 restart.flag를 만들지 않고 종료한다. 직접 start는 오늘자 PREOPEN을 시도하고 env를 기다리는 경로를 열 수 있어 검증용으로 실행하지 않는다. 다음 영업일의 정규 경로는10/19 05:35 finalization →07:35 PREOPEN →07:55 Main이다. 실제 기동·정확 PID/start ticks/준비 정책 소비는 기존 `DirectFamilyPreopenPolicyHandoff`의 당일 검증 대상이다.

## 코드와 배포 전 검증

- 실제 원래 숫자 정책 코드 원점은 `7f2552…`다. delay/holding/stop의 원래 정책 hash와 영수증을 보존하고 새 handler에 대한 정확한 source pair만 등록했다. 관련2,363회귀와 원 수리의528/1,051표적 검증이 통과했다. 중복 검증 수를 합산하지 않는다.
- native 기계 계약 모듈과 auxiliary/entry_cancel_wait 세대는 그대로이며, handler 변경을 포함하는 rising_missed·holding_vote는 새 세대의 fixture로 검증한다. 새 terminal 상태를 소비하는 코드와 동일 PASS 재전송 차단을 함께 인계한다.
- private mount/network namespace와 host root read-only,14개 CoW mount에서 검증한다. 원장·정책 디렉터리 전체 복제는0건이다. 역사 alias가 필요한 원래 코드 검증은 private overlay 안에서만 투영한 후 복구한다.
- 배포 runner 리뷰에서 원 predecessor 고정값, 증빙 경로 승계, native writer 잠금/파일별 CAS/rollback CAS, health FAIL 누락을 보완했다. 원6개 OPEN과 실패 이력은 보존한다.

첫 private whole-chain 준비는 PASS였지만 출판 전 원6OPEN 보존 검사에서8OPEN을 발견해 실제 출판을 차단했다. 새 rising_missed/holding_vote fixture는86/116PASS였으나 역사 보고서의 capability 세대를 현재 코드에 연결하는 직접 쌍이 빠져 있었다. `c5aeda844`에서 원 rising `e9f1620…→b47474ed…`, 원 holding `057c127…→02b637bf…` 두 쌍만 별도 등록했다. 원 보고서·기존 fixture를 수정하거나 과거 보고서를 연쇄 승격하지 않는다. 원 `source/comparison/handoff` 상태와 `native_validated=false`, 모든 runtime/정책 권한 false를 유지하고 독립된 현재 fixture만 검증한다. 관련378PASS·읽기 전용 canonical 경로 검증·compile/diff를 통과했다. [첫 실패 증빙](../../data/report/post_aux_priority_deployment/2026-10-17/preflight-failure.json)을 보존했다.

## 실제 배포와 다음 영업일 준비 결과

10/17 16:05:13 KST에 `c5aeda844dfab36146d04e6305cb29508cd47d4f`를 운영 선택했고,16:06:56 실제 출판 후 native 전체 검증을 통과했다. [배포 영수증](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/deployment.json)의41개 변경은 정책·코드 인계·준비본·summary/strict/controller·미래 체크리스트의 metadata/영수증38,092,903바이트다. 대용량 원장·DB·AI pack 복제는 없다. 원 current 기계·보조 포인터는 유지했다.

기계 정책은128범위/76,800행/598신호의 기존·새 코드 결과 해시가 동일하고 mismatch0이다. 새10/19 bundle은 `b521dfd93016626073ca45ef7b3f24bbb2e2b9a28a80ae9983ab01f4c4c02c94`다. 기존 두산 `034020|PRE|20000_TO_100000|NXT`와 알테오젠 `196170|PRE|GE_100000|NXT`의 승인된 보조정책만 새 bundle의 overlay `7a5d69b3059f32d8c8afd326a31e9d359a189c9497b1babcd5f99b8120a50cf9`로 인계했다. 나머지126범위·rollback·registry 정의와 원 overlay는 보존했다. 독립 검토에서 원천1,262개 해시·128연결과 준비 manifest/env/verification3종의 보존을 확인했고, 발행 후 native reader도 PASS다. 새로운 연구 입력 후보를 활성화하지 않았다.

16:10:53 [최종 준비 완료 영수증](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/next-session-completion.json)은 source10/16→target10/19, `current_full_contract=pass`, findings0이다. 새 overlay 발행 뒤 준비본을 다시 생성했으며, 검증 중 source stage·PREOPEN·보조/기계 publisher·체크리스트 잠금과 해시/CAS를 유지했다. 재시도는 UUID별 결과를 보존하고 하나의 completion만 발행한다. 원 체크리스트6OPEN은 그대로이며 다음 실제 PREOPEN/PID는 `DirectFamilyPreopenPolicyHandoff`가 소유한다.

[release/cron 경로 검사](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/routing-verification.json)는 PASS, cron8개와10/19 PREOPEN·Main 계획은 모두 c5a 선택본을 가리킨다. [원천 세대 검사](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/final-source-generation.json)의 strict/controller issue는 각각0이며 `strict_checklist_generation_stale`는 없다. 실제10/16 finalization DONE marker는 아직 없고, 기존 정규10/19 05:35 작업으로 남긴다. 미래 완료 marker나 PID 영수증을 만들지 않았다.

16:11:32 [전체 health](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/final-health-contract.json)는7개 detector 초기화·계약 오류0·FAIL0·운영 변경0이다. cron은 영업일 대기/비영업일 정지를 정상으로 판정했다. 경고2개 detector는 [원래 선택본과 동일](../../data/report/post_aux_priority_deployment/2026-10-17/attempts/c5aeda844/warnings-review.json)하다. 수량 비용/terminal 결손13행은 `InitialQuantityProducerConsumerRepair1010`, trailing 연구/코드 인계 원천은 `HoldingProfitExitSourceContractRepair`가 기존 Acceptance로 소유한다. 원천 결손을0 또는 성공으로 대체하지 않았다. log_scanner의2건은10:48:14/10:48:40 연구 작업본의 `config_dev.json` 부재 원문420바이트/동일 해시이며 새 선택 릴리스의 기동 오류 증거가 아니다. 원 로그·cursor를 수정하거나 경고를 숨기지 않았다.

판정은 **배포와 다음 영업일 준비 검증 완료**다. 토요일 Main/supervisor가 없어 재기동은 실행하지 않았다(`runtime_restarted=false`, `actual_pid_consumed=false`). 월요일07:35 PREOPEN→07:55 Main의 실제 PID/start ticks·정책 소비와 자연 주문/체결·비용 성과는 당일 증빙으로 확인한다. 새 provider/주문 호출은0회다. 현재 검증에서 기동 차단 결함은 발견되지 않았으나 미래 외부 연결·자연 실행의 무오류를 보증하는 결과는 아니다.

`TERMINAL_NOT_SENT`가 실제 원장에 생성된 뒤에는 이를 해석하는 bundle/timeout/handler reader를 유지해야 한다. 이전 구 reader로의 단순 롤백은 fail closed한다. 원장을 삭제하거나 취소·체결 영수증을 만들어 복구하지 않는다.
