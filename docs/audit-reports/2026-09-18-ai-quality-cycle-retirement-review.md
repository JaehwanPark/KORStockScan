# R0–R3 AI quality cycle retirement review — 2026-09-18

사용자가 `scalping.micro_reversion.ai_quality_cycle` 관련 장후작업·산출물 전체 제거와 연결 런타임 정비를 지시했다. 다른 세션의 현행 AI 원천/라벨·compact 평가 구현은 보존한다. 선택 배포 source `815414f83`를 기준으로 격리 작업 트리에서 수정하고 unrelated workspace 변경을 덮어쓰지 않는다.

## 제거 경계

- R0–R3 실행기·전용 counterfactual 진단기와 R2/R3 연구 인계·checklist workorder/summary hash 의존성을 제거한다.
- 장후 R0–R3·고아 standalone legacy optimizer/consumer 예약, Provider budget flags, DONE marker, PREOPEN current-axis 예약 및 cleanup 전용 root 인계를 제거한다. 현행 calibration의 compact finalize→optimizer/policy/consumer/summary 경로는 유지한다.
- legacy standing authorization/family/live selector 및 ask-depletion current-axis producer/input/runtime/source-buffer를 제거한다. Main AI의 prompt/request/capture/response/cache hook 및 observer의 전용 ring-buffer hook을 제거한다. 기존 독립 entry/holding/provider/schema/order/quantity/custody/safety owner는 그대로다.
- trusted registry에서 퇴역 family를 제거한다. 이전 family 문자열은 과거 receipt 거절용으로만 남기며 등록/적용 authority를 부여하지 않는다.
- 공용 quality의 폐기 source-bundle/materialize/execute CLI mode와 bridge CLI producer를 제거한다. 공용 순수 source/contract 함수·원본 trace/labels·시장/주문/체결·비용 원장, shared cost/master/lifecycle 입력과 현행 compact 정책/holdout/rollback 증거는 보존한다.
- 전용 report roots(R0–R3, bridge, A/B/C materialized/result/checkpoint, runtime-family) 및 current-axis runtime 산출물을 원본/공유 원천과 구분해 삭제한다. 삭제 시 active process/open FD/lock·symlink·동시 변경을 확인한다. 상세 파일별 manifest와 원본 보존 receipt는 `tmp/ai-quality-cycle-retirement-20260918/cleanup.json`이다.

## 리뷰·검증

Implementation→self review→보완→re-review: 폐기 코드 import, 직접 CLI 재생성, inherited flag 복원, 고아 후행 예약, 조건부 repair task 재생성 및 R2/R3 summary 의존성을 점검·제거했다. 관련 테스트에서 퇴역 API의 성공을 요구하는 사례는 함께 폐기하고 CLI I/O 전 차단·과거 report/OPEN workorder 비재생성·wrapper/registry 비복원 회귀를 추가했다.

핵심 source/wrapper/checklist 430 PASS, 후행 control-plane/reference/adversarial 140 PASS. 추가 runtime/collector/lifecycle/trace 검증은 687 PASS 및 기존 실패2건이다. 실패2건(일반 feature delivery-state 기대값과 holding payload 길이 상한)은 변경 전 selected815에서도 동일 재현했으며, 이 제거 작업에서 성능 상한이나 unrelated runtime을 변경하지 않는다. 추가 bridge/compile/bash/diff/parser와 현행 compact handoff 결과는 `validation.json`이 소유한다. 합성 테스트는 자연 주문/양수 EV 증거가 아니다.

## 결과·권한

Commit/push·선택 배포·실제 PID 및 artifact 삭제의 실제 결과는 owning `deployment.json`/`cleanup.json`을 따른다. 새 bot restart·주문·provider/guard/env/cron 변경·장후 전체 재실행·early PREOPEN·외부 sync는 없다. 기존 immutable release/rollback과 source 원장은 삭제 대상이 아니다. 폐기만으로 전일 전체 장후 chain DONE이나 EV 개선을 주장하지 않는다.

실제 삭제: 전용 파생 파일722개·444,154,086bytes(약423.6MiB), 보호한 원천/compact hash 불변. 삭제 후 기존 compact 인계 PASS. Bridge/cleanup 경계141 PASS, workspace7 PASS, compile/bash/diff/print-only parser PASS. 기존 baseline 실패2건은 별도이며 범위 내 잔여 finding0이다.

## 후속 소비 경로 리뷰

추가 사용자 승인에 따라 selected `1a7b4ea95` 이후 소비 경로를 재리뷰했다. 공용 consumer가 퇴역 prepared/bridge/materialized/execution 파일을 계속 읽고 R0–R3 재생성 acceptance를 발행하는 잔여 결함을 확인했다. 해당 입력·hash 의존성과 factorial router를 제거하고 optional 경로는 `retired_ai_quality_cycle`로 종결한다. 공용 optimizer의 고아 standalone CLI도 제거하여 현행 compact 보고서를 폐기 입력 기반 보고서로 덮어쓰지 않게 했다. 현행 compact finalizer·정책·인계 및 공용 순수 계약 함수는 보존한다.

전용7개 roots 및 지정 step1022 산출물의 재생성 여부를 확인했으며 추가 삭제 대상은0개다. 이전 삭제722개 manifest와 원본/공유 증거·immutable rollback은 보존한다. 후속 targeted pytest·compact 인계·parser/compile/diff, commit/push 및 선택 배포 receipt는 `tmp/ai-quality-cycle-consumer-closure-20260918/`를 따른다. 기존 baseline 실패2건은 변경 없는 별도 범위이며 이번에 광역 성능 테스트를 반복하지 않는다. 배포는 후속 invocation 선택이며 실제 PID/PREOPEN·자연 행동·양수 EV 수락은 별도다.

후속 최종 검증: consumer/optimizer/strict verifier236 PASS, 미사용 helper 정리 후 consumer15 PASS, compile/diff·worktree/workspace print-only parser PASS, 기존9/17 compact 인계 PASS. 범위 내 미해결 finding0. 전용 파생 산출물 추가0개. 신규 Python module 및 광역 재실행·provider 호출은 없다.
