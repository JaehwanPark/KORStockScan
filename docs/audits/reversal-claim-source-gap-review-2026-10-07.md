# 10/7 반전 신호 검증 결손의 정확 attempt 점검·최소 수리

## 판정과 권한

사용자 알림의 18건을 exact decision trace/evaluation attempt로 고정했다. 12:35:02~12:38:20 KST의 `reversal_first_signal_invalidated` 5건과 `reversal_signal_expired_or_changed` 13건이며 모두 provider_called=false, actual_order_submitted=false이다. 주문 실패나 증권사 API 결함의 근거가 아니다.

현재 OPEN owner는 `SemanticMonitorProducerConsumerRefresh1007`과 `DirectFamilySourceRepairMainMechanisticEntry`이다. 기존 사용자의 반복 리뷰·통합 배포·재기동 승인에 따라 source-only 계측/보고 수리를 배포한다. 기계 조건, 보조 input/prompt/schema, 5초 신호 유효시간, provider·주문·수량·custody·freshness guard는 보존한다. 새 IDE 퇴역 계획은 이 점검 범위에 포함하지 않는다.

## 정확 원천과 한계

0B 수신 나이 0.125~2.404초, 0D 수신 나이 0.126~1.431초이고 모든 trace의 입력 결손 목록은 비어 있다. 정확 `_AL`/krx_nxt_integrated 수신 envelope는 trace에 남아 있다. 최대 16MiB 정규화 stream tail로 18건 모두 동일 종목/item/수신 millisecond 후보를 찾았으나 15건만 단일 row이며 3건은 같은 millisecond 안에 복수 row이다. collector sequence_epoch/series_sequence는 live envelope transport_epoch/route_sequence와 서로 다른 identity이다. 이들을 같은 ID라고 재귀속하지 않는다.

legacy 가격 state를 tail에서 재현하면 가격 하락/새 반전 및 5초가 지난 반전이 관찰된다. 그러나 과거 18건에는 wake에서 선택한 claim snapshot·token이 trace에 없으므로 13건의 만료와 snapshot 변경을 개별 확정할 수 없다. 과거 snapshot을 합성하거나 단일 원천으로 단정하지 않는다. 반전 선택 후 tick REST·candle·investor context 준비를 거쳐 실제 분석 직전 다시 검증하는 경로이므로 준비 지연은 확인해야 할 경로이며 정확 구간 시간 계측 없이 REST/API 자체에 지연을 귀속하지 않는다.

## 최소 보완과 리뷰

- 별도 source diagnostics owner가 native validate_claim을 같은 ingestion RLock에서 그대로 실행한다. 거절 시 frozen 원본 snapshot·제공 snapshot SHA·signal age·exact family/token·현재 native row/segment·current turn ID·attempt/bundle를 붙여 기록한다. telemetry 실패는 기존 예외를 보존한다. 정상 반환·판정/TTL/가격/feature를 바꾸지 않는다.
- AI rejection producer와 ai_decision_trace projection을 연결하여 실제 consumer가 정확 거절 근거를 저장한다.
- 감시기는 정확 attempt/bundle/token/snapshot SHA, 수신 route·item·epoch와 연결된 valid price segment가 확인된 integrated FIRST 신호 만료/무효화만 diagnostics로 분리한다. snapshot 변경, 미래 시계, epoch/invalid source, 다른 attempt/bundle/route, 증빙 없는 기존 row는 issues에 유지한다. 정상 lifecycle 진단으로 source recovery나 매매 권한을 만들지 않는다.
- 단순 예외 문자열 allowlist 또는 alert 억제로 과거 18건을 정상화하지 않는다. API 요청/FID/parser/REG·REMOVE 변경과 외부 재호출은 없다.
- self review → telemetry가 native 예외를 덮는 결함 수정 → exact binding/segment 검증 보완 → re-review를 수행했다. 수정 범위 미해결 finding 0.

검증: 관련 8개 suite 559 PASS, compile 및 git diff --check PASS. 자연 source receipt 및 새 PID 소비는 별도 검증한다. 문서 변경은 print-only parser만 실행하고 외부 sync는 실행하지 않는다.

## 정확 ID 목록

| KST | 종목 | attempt | trace | 거절 |
| --- | --- | --- | --- | --- |
| 12:35:02.195359 | 403870 | aims-fb5ed1fe63ce35a19334 | aidt-ac06473cf3e74b4399643ed654fd9e3c | reversal_first_signal_invalidated |
| 12:35:13.520605 | 036930 | aims-c7aced0c822582b3163c | aidt-5ad862e8b9e04d0bbec11efb2bd919b5 | reversal_signal_expired_or_changed |
| 12:35:21.797566 | 034020 | aims-a483f3467da3f12be0c6 | aidt-e5bd5ee58b7e4821a0a7dd37242ee09c | reversal_signal_expired_or_changed |
| 12:35:29.758888 | 036930 | aims-b4679f710fe0d3ab2922 | aidt-6b809271ec044e99bd2909403a5b47b8 | reversal_signal_expired_or_changed |
| 12:35:37.255754 | 034020 | aims-3f41c89405dcf3897cfa | aidt-a94ae86ebb414fbb94321a35a86de50d | reversal_signal_expired_or_changed |
| 12:35:44.518359 | 403870 | aims-d72023c8faadfa694449 | aidt-5ac4c7c4e44e4d7ca0857cba47f2b962 | reversal_signal_expired_or_changed |
| 12:35:58.628960 | 036930 | aims-2afa9ebf7a45db034a4e | aidt-a286104ea0dc40e99a088ac46df3ac59 | reversal_first_signal_invalidated |
| 12:36:00.902158 | 403870 | aims-b1284a8e0198a8752057 | aidt-9224a9f077414ceea5700240fda9f291 | reversal_first_signal_invalidated |
| 12:36:05.843751 | 036930 | aims-f1e28e43226ea7098bb3 | aidt-d24525a7580741b185a9b62bf11e4fd2 | reversal_signal_expired_or_changed |
| 12:36:44.897807 | 036930 | aims-ecf4a0f4fbec81333336 | aidt-2564bba9c43543d48a6a6631e88b04c2 | reversal_signal_expired_or_changed |
| 12:36:49.157037 | 036930 | aims-07500f65b0ac6893ce3d | aidt-a96ca6209c1b46e98bef3e62c7578530 | reversal_signal_expired_or_changed |
| 12:36:56.561232 | 036930 | aims-b067823c9b28a3ed07db | aidt-b11fba2880694afdb0cc7be5beb7623e | reversal_signal_expired_or_changed |
| 12:37:05.477196 | 005930 | aims-0c9fd76c0e01ae4fc3d4 | aidt-244e32cb4c8449cf82d2fdb0006ab3b2 | reversal_first_signal_invalidated |
| 12:37:09.996548 | 036930 | aims-1228cde78dce1272f3b8 | aidt-4b9f2268664a4a1f8ceb0f4ca8e75ce6 | reversal_signal_expired_or_changed |
| 12:37:11.788172 | 196170 | aims-fe971561c7c2e0e8c1f0 | aidt-66ffe5b8727f45b084e165051a1f24e5 | reversal_signal_expired_or_changed |
| 12:37:24.692663 | 036930 | aims-d7bfcdc93d9bac7c2b48 | aidt-a781999b27244a4488c7610c3c894c57 | reversal_signal_expired_or_changed |
| 12:37:31.883042 | 034020 | aims-2f06e9a286f51012b542 | aidt-3eabbe04b7954f6e9c8591fd26720cc2 | reversal_signal_expired_or_changed |
| 12:38:20.902370 | 036930 | aims-5bc0f20276da9840c066 | aidt-d5e2910d343945f9b3653537841a9465 | reversal_first_signal_invalidated |

## 증거와 배포 인계

읽기 전용 동결/수신 대조/가격 재현: `tmp/reversal-source-alert-20261007/monitor-frozen.json`, `exact-traces.json`, `exact-receive-joins.json`, `exact-price-replay.json`, `before.json`. 최초 18건과 이후 추가 자연 trace를 구분한다. 현재 체크리스트/PREOPEN/boot env 및 원래 dated policy는 기존 봉인을 유지하며 수정하지 않는다. 배포 후 동일 cell payload/research hashes, native parent CAS, 실제 PID/5종목 WS, 새 rejected receipt 저장과 monitor projection을 확인한다.
