# Main 반전 원천결손 알림 점검 — 2026-10-08

## 결론과 확인 범위

사용자가 전달한 v3 알림은 5건(`expired_or_changed` 3, `path_changed` 2)이다. 알림 경로의 `data`는 작업본 공유 디렉터리로 연결되므로 현재 `latest.json`은 당시 원본이 아니다. 10:50:13 관측의 최신 사건은 v5 알테오젠 2건이며, 이 2건을 원래 5건의 전수 점검 결과로 표시하지 않는다.

실제 2건은 최신 체결·호가가 존재하고 반전 확인 뒤 가격이 다시 내려온 FIRST 신호 취소다. API 원천 결손이나 증권사 주문 실패로 확인되지 않았다. 감시기의 종목별 실행 세대 및 `path_changed` 분류 누락을 작업본에서 보완했다. 기존 5초 TTL, 신호 무효화, AI·주문·수량·custody 보호는 변경하지 않았다.

## 정확한 현재 증빙

- 관측 Main PID: `76094`, cwd `main-loop-latency-20261008-v5/src`. 정책 bundle `40fb3ec7d5f44e2e34044f2a14e2d0d06dd6ea264f69b5f1481be899f2a4a689`.
- 전체 family: `9ca49866d9042d9954e6bc2f64118eafea9a4b8165458c3d4420069990b1ed8b`.
- `196170|REGULAR|GE_100000` / SOR 실행 hash: `5a300defb9acff9a9cb5e08360d86cd5a46000e203533e34e3e136ce2a200330`. 활성 generation JSON의 `union_v6` 셀과 거절 영수증이 일치한다. 전체 family와 다른 값은 정상적인 범위별 실행 계약이다.
- 원천: `data/report/main_loop_latency/2026-10-08/source-alert-traces.json`. 당일 AI trace의 최대 16MiB tail에서 추출한 정확한 2행이며 전체 일자 원장을 복제하지 않았다.

| 판정 시각 KST | 판정 ID | 신호 나이 | 가격 확인→최신 | 체결/호가 age | provider / 주문 제출 |
| --- | --- | --- | --- | --- | --- |
| 10:47:29.992606 | `aims-f8146d66c67b96cd15a3` | 2.820575초 | 241,000→240,500원 | 878.724 / 275.951ms | false / false |
| 10:47:34.903158 | `aims-ca378d75525a5f568505` | 3.043287초 | 241,000→240,500원 | 349.037 / 195.170ms | false / false |

두 건 모두 `196170_AL`, 통합 경로, 동일 native epoch, 정상 native 유효표시, `current_turn_id=null`, 등록 당시 snapshot hash 일치다. native 상태 코드는 하락 체결에서 turn을 취소하고 all-FIRST ready를 제거한다. 입력을 재조회하거나 과거 신호를 되살릴 근거가 없다.

## 최초 알림 5건의 한계

현재 monitor history에는 10:25:14~10:40:17 사건이 남지만 마지막 관측 2개 예시로 갱신되어 있다: `aims-3840c373d8c057e520a8`(036930, 10:28:20, path_changed), `aims-7d49a784548238d6d652`(403870, 10:29:19, expired_or_changed). 이 예시가 최초 5건 전체인 것은 아니며 원 거절 영수증의 만료 초수는 이번 bounded 읽기에서 확보하지 못했다.

당일 trace는 64MiB 초과이고 계속 기록 중이다. 장중 I/O 규칙에 따라 전체 scan하지 않았다. 따라서 최초 5건 모두가 정상 만료/취소였다고 단정하지 않으며 historical_source_repaired도 선언하지 않는다. 최근 관측창에서 사라진 recovered 표시는 과거 원천 복구가 아니다. 최초 5건 확정은 당시 보존본 또는 장후 원장 조회로 정확 ID·거절 영수증을 확보한 후 수행해야 한다.

## 최소 보완 및 리뷰

- `reversal_source_diagnostics.py`: 같은 validation lock에서 v5/v6의 전체 envelope, 저장된 claim, 현재 셀 실행 hash, 현재 state generation, ready 존재 여부를 v4 영수증에 함께 기록한다. 판정 함수·결과·claim 저장 내용은 바꾸지 않는다.
- `submission_bottleneck_monitor.py`: 새로운 영수증의 등록 증명·snapshot·token·종목/경로·시각·전체/셀 세대 연결을 검사한다. 온전한 원천에서 만료된 신호는 만료 진단으로, 만료 전 all-FIRST 신호가 가격 재하락과 함께 제거된 경우만 취소 진단으로 분류한다.
- 기존 v3 operating 영수증은 셀→전체 연결 증빙이 부족하므로 소급하여 자동 정상화하지 않는다. 호가 이상, stale/epoch 단절, 세대 불일치, 증빙 훼손·누락은 계속 원천결손 검사 대상으로 남긴다.
- 코드 위치는 기존 runtime 진단 producer / monitoring consumer / 인접 tests를 사용했다. 다른 작업의 보조 연구 코드와 checklist 변경은 보존했다.
- 초기 검증에서 만료 fixture 자체가 6초 source gap을 만든 것을 발견했다. 경고가 유지되는 동작은 올바르므로 테스트에 실제 연속 체결을 공급하여 순수 TTL 만료와 원천 단절을 분리했다.
- 회귀검사: fixed-watch source repair, AI trace writer, submission bottleneck monitor, runtime policy evaluation **340 passed**. v5/v6 native 거절과 instrumentation 거절이 동일하고 claim 내용이 변하지 않음을 검증했다. Python compile 및 `git diff --check` 통과.

## 적용 상태

`code_review_closed / deployment_pending / natural_receipt_pending`. 이번 원천 점검에서 release 전환, 봇 재기동, API/AI 호출, 정책 변경은 실행하지 않았다. 현재 PID는 기존 v3 형식 영수증을 기록하므로 운영 알림이 해소됐다고 표시하지 않는다. 후속 승인된 통합 배포에서 producer와 consumer를 함께 반영하고 새로운 자연 v4 영수증으로 같은 판정 ID의 분류를 확인한다. 기존 owner는 오늘 checklist의 `DirectFamilySourceRepairMainMechanisticEntry`이며 중복 OPEN을 만들지 않는다.
