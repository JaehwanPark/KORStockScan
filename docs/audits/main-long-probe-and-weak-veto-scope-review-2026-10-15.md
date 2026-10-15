# 장기 관측 슬롯·대기 계측·Main 약세 veto 범위 변경 리뷰 — 2026-10-15

## 결정과 적용 범위

사용자는 장기 슬롯 증설을 확정하고 별도의 적용 전 확인을 생략하도록 지시했으며, 보완 우선순위와 두 약세 veto의 범위 정정을 구현 후 반복 리뷰·보완하도록 요청했다. 전체 physical probe/worker 5개 내 장기 슬롯은 2→3개로 변경했다. 60/150초 원 deadline, lease/result/ACK 귀속 및 짧은 분기 순환은 유지한다. 새 선택본 계측 누락을 별도로 재점검하지 않고 기존에 확인된 대기 계측 연결을 보완했다.

- [비고정 계획 §13](../proposals/main-nonfixed-observation-and-submit-bottleneck-remediation-plan-2026-10-14.md#13-2026-10-15-사용자-확정--장기-슬롯3-및-대기-계측-연결): `NonfixedDispatchReadinessReview1012`가 슬롯과 대기 계측을 소유한다.
- [제출 병목 계획 §14](../proposals/main-postrestart-submission-bottleneck-review-and-remediation-plan-2026-10-14.md#14-2026-10-15-사용자-지시--main-승인-타점의-약세-veto-범위-정정): `AuxiliaryCircuitRecoveryRepair1012`가 약세 검사 범위 및 자연 제출 증거를 소유한다.
- 새 OPEN ID는 만들지 않았다. 별도 용량 비교·부하실험·경제성 확인을 적용 조건으로 실행하지 않았다. 코드 회귀 검증은 사용자 요청대로 수행했다.

## 구현

1. `zero_base_discovery_queue.MAX_LONG_PROBES=3`. 기존 selected B4의 active-target defer·적격 대기 producer와 Main readiness snapshot을 작업공간에 맞춰 연결했다. workspace의 기존 변경은 원본을 보관하고 필요한 함수·consumer만 반영했다.
2. discovery/dispatch 두 cycle에 `probe_claim_eligibility`, `probe_residence_deferred`, active-target snapshot 상태/세대, 복원 후보 수를 전달한다. 원 PID/route/시각을 유지하며 적격 대기를 과거 first_seen으로 합성하지 않는다.
3. 새 참고 문맥은 `trade_quality_risk_context_history`, 실제 차단은 기존 `trade_quality_block_history`에 각각 bounded 저장한다. 실제 return 분기와 일치하는 gate action을 생산한다. 과거 row는 삭제하거나 원인을 소급 합성하지 않는다. 후단 약세 검사는 확인된 source/baseline 차단만 세고 명시적 risk context와 분류 불명 이력을 별도로 보고한다. 다른 기존 history 소비자의 legacy 처리 범위는 유지하되 명시적 참고 문맥은 실제 차단으로 세지 않는다.
4. 현재 Main 호출의 captured machine hash/evaluation/revision, `ENTER_NOW`, 유효 screen/effective `PASS`, 신뢰된 현재 BUY trace/snapshot이 결속된 경우 두 약세 alpha veto는 참고 문맥 로그로 남긴다. 고정 watch와 scanner promotion 모두 기존 binder를 사용한다. 판정 함수의 원 조건과 operator enable flag는 유지하며 승인 범위 밖에는 계속 적용한다.
5. micro source 결손·DANGER·normal-submit 불허·다른 시도·다른 owner·invalid response·CAUTION/VETO·sim/probe에는 이 범위 조정이 적용되지 않는다. 원 native 유효성/deadline, stale/conflict, 가격 drift, 계좌/주문/수량/cooldown 및 보호 exit 경로는 유지한다. 보조 AI 입력·응답·membership·metrics, provider, 주문가/수량 및 operator lock 원본은 변경하지 않았다.

## 리뷰와 보완

- 최초 구현 리뷰에서 참고 문맥이 같은32개 history를 점유해 실제 차단 이력을 밀어낼 수 있음을 발견했다. 저장을 분리하고40개 context 이후에도 실제 source block이 유지되는 회귀를 추가했다.
- 분류 불명·future/비유한 timestamp가 실제 차단으로 승격되지 않도록 확인했다. 기존 row의 원 bytes/원 attribution은 보존한다.
- 두 실제 live call site의 scope 적용, 같은 call-local machine binder, 고정/비고정 parent, 현재 revision과 AI trace/snapshot 조건을 재검토했다. 추가 로그는 실제 주문 허용 영수증이 아니다.
- 선택본과 작업공간의 차이로 발견된 readiness snapshot 의존성 및 두 기존 안전 테스트의 불완전 machine provenance fixture를 보완했다. 생산 guard를 약화시키지 않고 실제 binder를 통과하는 명시적 테스트 fixture를 사용한다.
- 요청 범위의 최종 재리뷰에서 미해결 코드 결함0. 과거 source loss의 원인, 자연 제출·체결·경제성은 코드 결함0과 별도다.

## 검증과 증거

- 기준 선택 commit: `038fe6ea8f7d1fa2d90c02c013d135f59e2743df`; 격리 worktree: `/home/ubuntu/KORStockScan-worktrees/entry-slots-weak-veto-20261015`.
- 선택본 기준 확장 회귀373개 PASS. 작업공간 통합 후 관련 회귀368개 PASS. 두 수는 중복되는 서로 다른 source tree의 검증이며 합산하지 않는다.
- 범위: queue/runtime/probe/Main attach, 약세 history/scope, 고정·비고정 Main, 가격 drift, AI authority, DANGER/stale/broker/quantity 및 async entry bridge. 기존 pandas 경고1건 외 검증 실패 없음.
- 변경 Python compile 및 `git diff --check` PASS. 문서·체크리스트의 print-only parser와 링크 검증 PASS. 두 기존 stable ID는 현재 체크리스트에서 각각 하나의 OPEN owner로 파싱됐다. 외부 sync는 실행하지 않았다.
- [입력·원본 보관 manifest](/home/ubuntu/KORStockScan/tmp/entry-slots-weak-veto-20261015/input-manifest.json), [최종 소스 manifest](/home/ubuntu/KORStockScan/tmp/entry-slots-weak-veto-20261015/output-manifest.json), [요청 변경분](/home/ubuntu/KORStockScan/tmp/entry-slots-weak-veto-20261015/workspace-requested-delta.patch), [작업공간 회귀](/home/ubuntu/KORStockScan/tmp/entry-slots-weak-veto-20261015/workspace-tests-final.log), [선택본 회귀](/home/ubuntu/KORStockScan/tmp/entry-slots-weak-veto-20261015/targeted-tests-final.log).

## 미실행과 후속 상태

별도 적용 전 슬롯 용량 비교/부하실험은 사용자 지시로 생략했다. 이 작업은 계획·코드·회귀의 적용이며 배포/선택 변경/Main 재기동·실제 주문·provider 호출은 실행하지 않았다. 기존 operator lock/env 원본과 운영 selector/PID를 변경하는 명령도 실행하지 않았다. 새 코드의 실제 PID 소비와 자연 관측·Main 편입·제출·비용 후 성과는 기존 실행 owner에서 별도로 확인하며 코드 PASS로 대체하지 않는다.
