# 삼성전자 기회 계약 복구 및 고정 패턴 재검증 실행계획

Owner: `SamsungOpportunityContract1004`, [현재 checklist](../checklists/2026-10-04-stage2-todo-checklist.md).
선행: [직접 비교 연구의 후속 계약](../audits/samsung-policy-episode-replay-research-review-2026-10-04.md#8-종료-이유와-후속-계약-보완).

## 1. 실행과 권한

사용자의 `계획을 실행하라`에 따라 원천 연결 복구→재진입 계약 대사→고정 회복/흡수 재검증→정책 생성 적격성 검증을 순서대로 실행한다. 보유9/29·9/30·10/2 원천을 사용하고9/28은 기존 prior-day 진단 역할만 유지한다. API/provider 호출·원천 수집 확대·실주문·배포·재기동·운영 policy publication은 실행 범위에 없다. 성공100%/80% 보존 veto를 두지 않는다.

## 2. 원천과 위치

- 선행 `frozen-strict/result.json`·`validation/closure.json`, verified source와 parent policy hash를 그대로 봉인한다. 기존 projection/정책/인계/연구 source를 덮어쓰지 않는다.
- exact-date machine projection, machine capture, pipeline/AI trace, scanner/fixed-watch 원receipt, order-owner registry·buy-fill·terminal/flat/custody 기록 및 필요시 read-only DB snapshot을 조사한다.
- 새 오프라인 생산자는 기존 `src/engine/scalping` 연구 package에 둔다. 계약은 별도 연구 source capsule/consumer로 구현하고 기존 live identity·publisher gate를 대체하지 않는다. 회귀는 `src/tests`, 결과는 격리 `tmp/samsung-opportunity-contract-20261004/` 및 별도 audit에 기록한다.
- 프로토콜 request/parser/realtime mapping을 변경하지 않고 기존 normalized domain만 읽는다.

## 3. 단계 및 수용

### C1. 과거 기회 신원 복구

519개 captured 판정의 trace/attempt/snapshot·setup hash·bundle·날짜/종목/venue/session을 당시 기록과 대사한다.9/29 원native metadata 결손298건이 대상이다. 모든 복구에 path·physical hash·행 위치·원identity·일치 필드를 남긴다. 같은 날/종목/근접 시각만으로 fixed-watch admission을 대입하지 않는다. 중복 불일치는 conflict, 증거 없음은unrecoverable이다. 원projection은 보존하고 별도 복구 ledger를 생산한다.

### C2. 재진입/구간 계약

watch admission/generation은 유지한다. 원owner가 발행한 entry/terminal/cancel/flat/custody 및 새 적격화 증거가 한 포지션/기회에 정확히 연결되는 경우에만 별도 episode 경계를 인정한다. Main·Widget·manual·sim·CF·미체결·부분체결을 나누고 unresolved order/position 뒤의 재진입을 금지한다. 같은 상관 native cluster는 같은 fold에 둔다. 지원수는 episode 개수가 아닌 원native cluster로도 함께 공개한다. 단순 시각bucket·사후 저점/목표 도달로 live/native 기회를 신조하지 않는다.

실제 주문 없는 가격 연구는 그대로 허용한다. 이 경우 modeled terminal을 실제flat/custody로 치환하지 않고 source/cost/execution support 제약을 분리해 보고한다.

### C3. 고정 후보 재검증과 정책 생성 적격성

선행 학습에서 고른 `base_recovery:300:5:barrier:0.23:60`, `absorption_release:300:5:barrier:0.23:60` 및 Main native/trace adapter 조건을 변경하지 않고 복구된 분모에 적용한다. 신호/원binary/비용/종료를 바꾸지 않는다. 새로운 원native 정보가 실제 결과 분모를 바꾸는지, 비교 가능한 기존Main 후단 결과와 양성 증가가 있는지 계산한다.

삼성 child selector의 symbol/origin/venue/session·parent hash·대상 밖parent 상속·expiry·publication 권한 계약을 오프라인 소비자에서 검증한다. runtime 등록/발행은 유효 후보 및 해당 승인 계약을 충족할 때의 별도 단계다. 현 발행 검증의30/10 native 지원·승률 개선·지원조정 개선·coverage 등은 유지한다. 원source 복구가 실패하거나 분모가 여전히 미달이면 그 사실을 명시하고 candidate=null로 종료한다. 같은 원천의 조건 숫자만 반복 변경하지 않는다.

## 4. 코드리뷰와 재생

구현→self review→보완→재리뷰→표적 pytest/compile/diff 후 격리 cold/warm 실행한다. 회귀는 nested metadata의 정확한 위치, exact trace/attempt/snapshot/time/scope/hash, 상충된identity, 미래receipt, native/episode 상관성, 부분/미해결/타owner custody, target 밖parent 상속, 원source 불변성, 성공 보존veto 부재를 확인한다. 읽기만 하는DB snapshot에는 트랜잭션 read-only와 조회 범위·capture hash를 기록하며 계좌 식별자는 출력하지 않는다.

결과·producer/consumer 연결·새로운 복구 수·재검증 성능·publisher 적격성을 [실행 리뷰](../audits/samsung-opportunity-contract-reconciliation-review-2026-10-04.md)에 남긴다. 마지막에 link/owner·print-only parser를 검증하고10/6 기존owner를 보존한다.
