# S6 `S2-ENT-02` — 원자 sizing 행 계보

실행일: **2026-09-28 KST**. 범위: [S2의 `S2-ENT-02`](2026-09-27-intraday-postclose-handoff-S2.md), [BUY parent→보유 인계](2026-09-28-intraday-postclose-handoff-S6-S2-ENT-03-S3-EXIT-02.md), [현재 체크리스트 `DirectFamilySourceRepairEntrySplit`](../checklists/2026-09-28-stage2-todo-checklist.md). **판정: 작업본의 생산자→첫 reader 행별 계보 수리와 fixture 검증. 9/23 과거 원천의 owner·account·route 및 새 producer ledger는 미확인; 그 날짜의 선택·terminal·비용·자연 소비를 승인하지 않는다.**

## 결손 재현과 분모

- 기존 [9/23 `entry_split_order_plan` 보고서](/home/ubuntu/KORStockScan/data/report/entry_split_order_plan/entry_split_order_plan_2026-09-23.json)는 `atomic_execution_sizing`을 19 관측·17 valid·2 invalid, `real_submit_with_plan=20`, `status=fail/selection_blocked`로 집계했다. 보고서 집계에서 각 plan ID/SHA·attempt·leg·broker order·owner 및 terminal의 연결을 복원할 수 없었다. `20-19`를 결손 1건으로 계산하지 않는다.
- 압축된 9/23 `pipeline_events`의 **기존 bounded execution projection** 1,205 event를 읽기 전용으로 재대사했다. sizing stage 19 event = 실제 plan 발행 14 + 의도된 probe deferred/no-plan 3 + `planned_orders_missing` 차단/no-plan 2. 제출 20 event = `order_leg_sent` 10 + 동일 주문을 다시 알리는 `order_bundle_submitted` 10; 고유 broker order는 10이다. 발행 plan 14개 중 동일 날짜·record·attempt·plan ID/SHA로 주문 leg에 연결된 것은 10, 제출 stage가 미관측인 것은 4다. 10건 모두 과거 event의 owner·account·route 필드가 비어 있어 **ID 연결 10 / source-quality 격리 10 / terminal 미관측 10**으로 남긴다. 4건을 미체결 또는 제출 0으로 단정하지 않는다.
- 당시 producer summary manifest에는 후속 S6에서 추가한 `raw_source_ledger`가 없다. `historical_unsealed/producer_raw_ledger_missing`을 유지하고, 9/23 영수증에 새 세대·건수를 소급 작성하지 않는다. 이 bounded projection은 9/23 전체 raw 모집단이나 운영 경제성 승인 분모가 아니다.
- 실패 fixture는 최초 `build_atomic_execution_sizing_lineage` 부재로 3건 `AttributeError`를 냈다. 이후 다른 attempt의 제출, 바뀐 plan core SHA, summary 원천 세대 재생성, compact reader 파일 변조, 무계획 상태 모순, 중복 leg, 응답 불확실, source-only, full/partial/cancel pending registry를 추가해 재현했다.

## 수리한 생산자→첫 소비자 계약

| 경계 | 작업본 수리와 격리 기준 |
| --- | --- |
| `entry_execution_sizing_plan`·장중 emitter | 기존 계획 core·ID·논리 SHA·수량/leg를 보존하고 `issued`, `blocked_plan`, `deferred_no_plan`, `blocked_no_plan`, `blocked_no_action_receipt` 처분을 기록한다. 주문·수량 계산은 변경하지 않았다. |
| `pipeline_events` → producer summary → bounded projection | 기존 sealed raw ledger의 source date·partition/offset·논리 SHA·원본/유효/제외/격리/미관측 stage census를 사용한다. reader는 compact 입력의 파일별 SHA·inventory·stamp와 producer census를 따로 묶는다. 정상 원천/압축본·중복·late·손상·누락·valid-empty의 판정은 기존 summary/projection 계약에 맡기고, 그 계약이 실패하면 이번 lineage도 `source_gap`이다. |
| `entry_split_order_plan` 첫 reader | plan core SHA, plan ID, action receipt, 전체/즉시/이연 수량과 leg 합을 검사한다. 날짜·record·attempt·plan ID/SHA로 실제 `order_leg_sent`를 결합하고 bundle 반복 event를 주문으로 중복 세지 않는다. 각 행에 계획 시각, 제출 leg·가격·시각, owner/account/route/session, 계획·제출·미제출 수량, 주문·intent·execution ID와 원천품질 사유를 남긴다. ID가 없는 제출은 별도 `unjoined_submits`로 보존한다. owner/account/route 결손·충돌, 다른 leg에 같은 broker order, 잘못된 수량/ID는 격리한다. |
| registry terminal | 검증된 journal의 동일 intent·account·owner·주문·수량·route 상태를 재구성하고 누적 fill과 terminal reconciliation 영수증을 확인한 경우에만 full/partial/open/cancel pending을 구분한다. 브로커 응답 불확실은 주문 확정으로 세지 않는다. registry 증거가 없으면 체결·취소·비용은 `null`/미관측으로 남긴다. |

새 날짜의 report/policy reader는 producer ledger 세대 또는 compact 입력 세대가 바뀐 과거 report를 stale로 거절한다. `refresh_execution_model_only`도 전세대 report를 재사용하지 않는다. 9/23 보고서는 기존 상태를 그대로 보존한다. 원본·유효·제외·격리·미관측 수는 서로 다른 stage/event/order 단위로 유지한다.

## 닫힘 검사와 남은 인계

- 수리 owner: `src/engine/scalping/entry_execution_sizing_plan.py`·`src/engine/sniper_state_handlers.py` 생산자, `src/engine/scalping/entry_split_order_plan.py` 첫 reader. 닫힘 검사: **동일 source date·producer ledger SHA·compact SHA와 plan→attempt→leg→order→검증된 registry terminal의 행별 보존식**, 다른 세대 거절, 중복 제외, source-quality 이유/분모 보존. Fixture는 이 계약을 검증한다. 9/23 owner 미관측 10건과 발행 후 제출 미관측 4건은 실제 원천이 연결되기 전까지 닫히지 않는다.
- `DirectFamilySourceRepairEntrySplit`의 동일 frozen submitted-order scope, **운영 paired source·완결 비용·독립 calibration/holdout**은 계속 OPEN이다. 비용은 0으로 채우지 않는다. `S2-ENT-05` 순차 첫 leg, `S3-EXIT-01` SELL 비용, `S5-FIN-05` 새 자연일 결손은 별도 수리다. 전체 데이터/성능·자연 terminal은 S7, 선택 릴리스·PREOPEN·실제 PID 소비는 S8에 인계한다.
- 코드 자가 리뷰에서 작은 raw reader의 `order_leg_no_response` 누락, 문자열화된 과거 `[]` blocker의 오분류, registry journal을 전체 상태로 읽던 오류, owner 없는 ID 연결의 과대승격을 발견해 수정한 뒤 회귀를 다시 실행했다. 테스트·compile·diff 및 문서 parser 결과는 아래에 기록한다. wrapper는 변경하지 않았다. 정규 장후작업, PREOPEN, 실주문·취소, 정책·수량·timeout·서비스·provider·threshold, 배포는 실행·변경하지 않았다.

## 검증 결과

- 영향 pytest: `src/tests/test_entry_split_order_plan.py`와 `src/tests/test_entry_execution_sizing_plan.py` **253 passed, 1 기존 pandas_ta warning** (전체 영향 회귀). 최종 보완 후 atomic lineage/policy 회귀 **6 passed**; archive·late·중복·손상·valid-empty producer ledger 회귀 **9 passed**. 마지막 보완은 취소 journal의 누적 상태 판정과 source-only 손상 격리이며 그 fixture를 다시 통과했다.
- Python compile: 위 두 생산/소비 모듈, `sniper_state_handlers.py`, 두 영향 테스트 통과. Wrapper 변경 없음(`bash -n` 대상 없음). `git diff --check` 통과. 전체 Ruff 기존 지적 168건 가운데 변경 줄 0건. 문서 링크·owner 확인 및 print-only parser 통과(OPEN 31건, checklist owner 유지).
- 잔여 위험: 9/23 raw는 과거 unsealed이며 owner/route·main BUY registry terminal이 미분류다. fixture와 작업본 검증은 선택 릴리스/PID 자연 소비나 경제성 효과를 증명하지 않는다.
