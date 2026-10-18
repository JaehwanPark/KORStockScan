# 2026-10-18 Stage2 To-Do Checklist

## 오늘 목적

- 완료된 수량 연구의 불필요한 임시 데이터·중복 사본을 검증해 정리한다.
- 수량 연구 비용·의미 감시 후속 결함을 검증하고 다음 정규 기동용 배포를 마친다.

## 오늘 강제 규칙

- 선택 릴리스와 기존 정책·보조 binding·원천 및 실패 영수증을 보존하고 격리 후보에서 검증한다.
- 연구 원천일10/16과 적용 대상10/19를 유지한다. 코드·선택 배포·실제 PREOPEN/PID·자연 생산·비용 후 성과를 구분한다.
- 사용자 승인된 확정 총비용 배분은 연구에만 사용한다. canonical 실제 비용·손익·정책값·Main/manual custody·주문/provider·hard safety 권한을 임의 변경하지 않는다.
- 비영업일에 Main을 강제로 기동하지 않는다. 최초 정책에 추가 경제성·자연소비 허들을 부과하지 않는다.
- 문서 검증은 print-only parser만 사용한다. 외부 Project/Calendar 동기화는 사용자가 수행한다.

## 실행 항목

- [ ] `[MainPolicyLoadAndExitValidation1018] 다음 거래일 정책의 Main 공통 로딩·확인 후 종료 경로 구현` (`Due: 2026-10-19`, `Slot: IMPLEMENTATION`, `TimeWindow: P0~P4 코드 종결 후 P5 불변 후보 검증`, `Track: RuntimeStability`)
  - Source: 사용자 계획 리뷰·보완 및 구현·코드리뷰·수정 반복 지시, [보완안](../proposals/main-policy-load-and-exit-validation-plan-2026-10-18.md), [구현 검토](../audits/main-policy-load-and-exit-implementation-review-2026-10-18.md).
  - 범위: 실제 producer→env precedence→Main native consumer/cache/기록 부작용을 확정하고, 같은 공통 로더를 쓰는 별도 검증 child를 감시·외부 통신·주문 초기화 전에 종료한다. 현재10/18·원천10/16·대상10/19와 선택본/검증 후보 신원을 분리하고 당일 활성화 계약은 유지한다.
  - Acceptance: 휴장일·평일의 비어 있지 않은 실제 로더 경로, 미래/current 차이·operator/retirement·필수12consumer의 object/scope/hash 대조, invalid 반환·변조·cache·동시 변경·크래시/timeout·격리/부작용 시도 실패를 검증한다. exact child PID/start ticks·종료·원자적 terminal·운영 보호 hash 불변, source/code handoff·운영 동등성 회귀·리뷰→수정→재리뷰를 확인한다. 검증 receipt는 actual_pid_consumed/runtime_effect=false다.
  - 경계/인계: 후속 지시로 코드·격리 시험은 승인됐다. 운영 배포·Main 재기동·정책/selector·provider/주문·패키지는 변경하지 않는다. P5의 실제 준비 세대 후보 실행은 아직 미실행이며 이 owner에 남긴다. 실제10/19 PREOPEN 활성화·운영 PID는 [DirectFamilyPreopenPolicyHandoff](2026-10-19-stage2-todo-checklist.md)가 유지하고 자연 주문·추가 경제성 승인을 기술 로딩 조건으로 붙이지 않는다.
  - 진행: P0~P4 구현·독립 리뷰·수정·재리뷰를 마쳤다. 실제 Main 조기 분기·공통 env·12consumer·Landlock/seccomp·parent terminal을 연결했고 delay 실패 cache·미래 split 권한·부작용 import·literal env·코드 계보/확장 결속을 수리했다. 실제 native producer128route와 Main child 양성/변조 실패를 검증했다. selected900의10/19 준비본 읽기 전용 current_full_contract 검증은 PASS이며 실제 candidate 세대 실행·운영 적용의 PASS로 간주하지 않는다.

- [x] `[SnapshotCronReleaseBindingRepair1018] snapshot 감시 cron과 비동기 소비의 선택 릴리스 결속 수리` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: 승인 후 제한된 검증·적용`, `Track: RuntimeStability`)
  - Source: 사용자 다음 액션 실행 지시, [실행 경로 누락 점검](/home/ubuntu/KORStockScan/tmp/source-control-runtime-coverage-20261018/report.md), [운영 계약](../runtime-release-routing.md#snapshot-cron-release-binding).
  - 범위: 기존 snapshot3개 schedule의 공용 bootstrap을 선택900234d79에 연결하고 safe/Python/async 자식의 같은 code root를 검증한다. 기존 Main 선택·정책/PREOPEN·수량/custody·주문/provider 권한은 보존한다.
  - Acceptance: exact3행만 변경·기존8route/일시/로그owner 보존, invalid/부분/중복·동시변경 차단, 선택root/오염env 거부, 원자적 완료 읽기·쓰기/실패worker·cooldown 회귀, 독립 리뷰·수정·재리뷰·parser, 적용 후 새 terminal과 selected 코드 확인. 자연10/19 Main 소비는 기존 DirectFamilyPreopenPolicyHandoff가 유지한다.
  - 완료: bootstrap 수리 `9afd16cdc`·독립 리뷰 후 회귀276개/compile/shell/parser PASS. 정확3cron행만 적용하고8필수+3snapshot readback 및 재변환 동일을 확인했다. 기존900234d79의 async 경로에서10/18 새 terminal success·보고서3개/3.916초, 보호11파일 불변을 확인했다. 첫 dispatch-only 수동 시도는 종결을 확인하지 못한 원본으로 보존하며 완료대기 호출과 구별한다. Main 재기동/provider/주문0이며 자연10/19 소비는 별도다. [적용 결과](../audits/snapshot-cron-release-binding-and-source-control-integration-review-2026-10-18.md).

- [x] `[SourceControlReconciliation1018] 검증된 누적 배포 코드와 원문을 보존한 Source Control 통합` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: snapshot 경로 수리 후`, `Track: RuntimeStability`)
  - Source: 사용자 100개 Source Control 변경 지적 및 다음 액션 실행 지시, [파일별 분류](/home/ubuntu/KORStockScan/tmp/source-control-inventory-20261018/inventory.json).
  - 범위/Acceptance: 원102개 bytes·Git index/ref·선택본·cron을 백업하고 검증된900의 누적200개 commit/소스와 이번 bootstrap 수리를 main에 통합한다. 현행 문서·삭제됐던 역사 문서·수동관리 설정·원 실패 및 봉인 증거는 원 bytes를 보존하며 동시 변경은 CAS로 재검토한다. 독립 리뷰·필요 회귀·compile/shell/parser·clean 상태와 기존 선택/PREOPEN 불변을 확인한다. .venv 패키지 변경·Main 강제 기동·외부 sync는 실행하지 않는다.
  - 완료: 08:18 `63cc30e2b`로 main 전진 후 clean을 확인했다. 검증된 bootstrap `9afd16cdc`의 전체 실행 소스와 같고, 원102개 백업·현재 문서/수동설정1,304파일 bytes/mode·보호11해시를 보존했다. 계획304경로만 반영하고 독립 재리뷰 finding0·통합 후보 회귀276/격리 Git 실패9/location3·Python292/shell5/parser를 통과했다. 기존 선택본의 EOF 공백1건은 원문으로 보존하고 이번 overlay diff check는 통과했다. 기존900234d79 및10/19 정책/PREOPEN은 동일하며 cron8+3 readback PASS, Main 재기동/패키지/provider/주문/외부 sync0다. [최종 통합 근거](../audits/snapshot-cron-release-binding-and-source-control-integration-review-2026-10-18.md#source-control-통합-완료).

- [x] `[CompletedResearchDuplicateCleanup1018] 완료 연구 복제본·테스트 임시자료 정리` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 불필요한 완료 연구 데이터 삭제 지시, [정리 검토](../audits/completed-research-duplicate-data-cleanup-review-2026-10-18.md).
  - 범위/Acceptance: 현재900234d79·이전 릴리스·원장/AI 원응답·고유 결과·원 실패·10/19 준비본 및 기존 작업본을 보존하고, 참조/FD·동일 원본 SHA·inode/mtime/ctime 검증 뒤 중복 정책 사본과 종료된 합성 테스트 파일만 journal로 삭제한다. 동시 변경은 중단/재검토하고 확인된 삭제·외부 결손·제어파일 비용·파일시스템 변화를 분리한다.
  - 완료: 확인된6,506개/논리5,000,360,304바이트(정책 중복1,740·pytest4,766) 삭제, 원본 정책 전체 재해시·보호 파일 검증 및9개 guard 회귀/compile 완료. 별도 임시 정리로 사라진10,546개는 삭제 실적에서 제외하고 첫 중단과 잔여1,130개 재시도 증빙을 보존했다. 이후 native current_full_contract PASS/findings0·release-set/cron8개 PASS. 사용률87→80% 변화 전체를 이번 작업에 귀속하지 않는다. 재시작/provider/주문0이며 실제10/19 PREOPEN/PID는 기존 DirectFamilyPreopenPolicyHandoff가 소유한다.

- [x] `[InitialQuantityBrokerCostClosure1017] 키움 확정 총비용 배분 생산자와 수량 연구 소비 폐루프 보완` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 비용 미확인 반복 지적 및 보완 지시, 확정 총비용의 매수·매도 거래대금 배분을 연구에 사용한다는 사용자 확정, [비용 생산자·소비자 계약](../proposals/initial-quantity-runtime-postclose-producer-consumer-repair-plan-2026-10-10.md#8-2026-10-17-비용-생산자소비자-보완-계약).
  - 범위: 선택 c4467c424 기준 격리 구현 후 새 선택3abcc524c의 지연 연구 수리를 누적 보존한다. 연구 전용 배분 비용 생산·bounded fact/완료 overlay/수량/timeout 소비, 검증된 custody 문맥, 정산 대기 날짜 수집·소비 ack·정정 원본/세대 보존을 연결한다. canonical actual 손익·정책값·실주문 권한을 배분 자료로 변경하지 않는다.
  - Acceptance: 다회 거래/익일 청산/미청산/수동 잔여/반올림 보존식·원천/영수증 변조·과거 비용 정정·시간 역전/holdout·v2 호환·정산 대기/실패/경합/예산, 실제 봉인 자료와 비어 있지 않은 fixture 성능, 독립 리뷰·수정·재리뷰·문서 parser. 배포·정규 자연 생산·실제 PID/경제성은 별도 근거로 확인한다.
  - 완료: `e12256dec`에 최신3abcc 지연 수리를 누적 통합하고 독립 코드리뷰·수정·회귀781/인계547/지연66 PASS, 새 holding116 및 native128범위 신호 동일을 확인했다. 실제10/16 완료9건 중 연구 비용8건 admission·제외1건/미청산3건·총비용6,256원 보존과3회 성능/1,000건 예산 검증을 기록했다. 23:21 다음 정규 기동용 선택 발행 후 current_full_contract PASS/findings0, 정책값/128연결/두PRE/원6OPEN·운영 비용/fact 보존, provider/주문/재시작0·actual_pid_consumed=false다. [최종 검토](../audits/initial-quantity-broker-cost-closed-loop-repair-review-2026-10-17.md). 자연 생산·정산/경제성은 기존 InitialQuantityProducerConsumerRepair1010, 실제10/19 PREOPEN/PID는 DirectFamilyPreopenPolicyHandoff가 유지한다.
  - 재개: e122 발행 뒤 마지막 소비자 점검에서 의미 감시기의 compact completion/fact 참조 직접 비교 결함을 확인했다. 공통 증명 검증과 연구 영수증 일치 검사를 보완·회귀한 후 후속 불변 릴리스로 재배포한다. 원 e122 배포·발행 직후 PASS 영수증은 보존하며 자연 수용 owner는 유지한다.
  - 이관: 10/17의 e122 발행·후속 결함·실패 이력을 보존하고 동일 ID로 10/18에 이어간다. 연구 source10/16·다음 정규 적용10/19를 유지한다. 당일 감시는 current source/code/cost를 재검증하고 이미 승인된 과거 정책 ancestry에는 새 경제성·원천 최신성 허들을 추가하지 않는다.

  - 후속 완료: `900234d79`의 compact 참조/영수증·큰 보고서 의미 projection·512KiB native status·일자별 claim 수명·과거 ancestry/당일 검증·후행 연구비용 소비를 수정하고 독립 재리뷰 finding0, 최종622+100 PASS·genuine1,000건 native 끝단/비용 보존·원본 재독해0·64MiB budget 준수로 검증했다. 00:17 선택 발행 후00:19 current_full_contract PASS/findings0, 원 정책값/128/두PRE/rollback/10/19 OPEN6·비용/fact 보존을 확인했다. 기존3 fixture 실패는 정확e122 재현 근거와 분리 보존한다. 실제provider/주문/재시작0·actual_pid_consumed=false이며 다음 정규 소비/경제성 owner는 기존 항목을 유지한다. [후속 배포 증거](../audits/initial-quantity-broker-cost-closed-loop-repair-review-2026-10-17.md#8-후속-릴리스-실제-배포-완료-2026-10-18).
  - 사후 확인: 00:21:59 실제900 release/cron/PREOPEN/start·현재 full·strict/controller 읽기 전용 검증 PASS/issues0. 보호 원천 및 원10/19 자연 수용 owner를 유지한다.


- [x] `[InitialQuantityResearchCleanup1018] 완료된 수량 연구 임시자료 정리` (`Due: 2026-10-18`, `Slot: ADHOC`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: 사용자 "연구가 종료되어 불필요한 데이터는 삭제해줘" 지시.
  - 범위: 이번 수량 연구의 종료된 synthetic fixture·회귀 확인용 작업본·재생성 가능한 cache·Git/보존본과 같은 중복 사본만 정리한다. 현재900/이전e122·실제 PID/서비스 사용본·원7f ancestry·운영 원천/미해결49294·주문/custody·최종/실패 증거·직접 소비되는 보조정책 증명을 보존한다.
  - Acceptance: 정확 source/HEAD/selector와 참조·프로세스/FD/maps/mount census·후보별 SHA/stat 및 독립 리뷰, 삭제 journal·필요한 archive/restore 검증, 최종 정책/준비본 참조 및 사용자 동시 변경 보존·print-only parser. 연구 종료를 정책/원천 삭제 권한으로 확대하지 않는다.
  - 완료: 원 후보8분류/55경로 중 동시 작업에서 먼저 없어진 baseline·중복 checkout·pytest 자료를 별도 부재 기록으로 보존하고 중복 집계하지 않았다. 잔여 cache49곳/711파일·할당55,128,064B(약52.6MiB)를 직접 삭제했다. guard9 PASS·독립 재리뷰 finding0·파일별 journal·원 후보 전체 부재 및 보호122/기존 수정33파일 hash 동일,900/e122·원7f/보조증명/10/19 준비본·원천/custody 보존을 확인했다. 재시작/provider/주문0. [정리 결과](../audits/initial-quantity-research-storage-cleanup-2026-10-18.md).
