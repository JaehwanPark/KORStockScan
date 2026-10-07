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

검증: 관련 8개 suite 564 PASS, compile 및 git diff --check PASS. 자연 source receipt 및 새 PID 소비는 별도 검증한다. 문서 변경은 print-only parser만 실행하고 외부 sync는 실행하지 않는다.

## 추가 인계 결함과 수리

반복 장중 배포의 prepare는 직전 코드 commit 안의 현재 체크리스트가 원래 장후 세대와 같아야 한다고 가정했다. 앞선 배포가 이미 이전 Git object의 원래 snapshot을 봉인한 경우 이 가정은 깨진다. actual previous PID와 consumed handoff를 검증한 후, 원본 SHA에 묶인 predecessor snapshot/consumed receipt를 승계하고 원래 Git object bytes까지 재확인하도록 보완했다. 새 봉인에서도 predecessor 경로와 handoff/consumed SHA를 직접 검증하며, snapshot·consumption·Git bytes·custody 변조는 모두 fail closed다. PREOPEN·현재 checklist·정책 bytes는 수정하지 않는다. 반복 배포 정상 1건과 변조 4건의 regression을 추가했다.

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

## 최종 배포·자연 증거 (2026-10-07T13:07:15.457550+09:00)

- 실행 commit `9ab26285047091387465000e6d15c4cbfafe1fa7`, 릴리스 `/home/ubuntu/KORStockScan-runtime-releases/reversal-claim-source-20261007-v1`, PID 870498 (13:03:33 KST 기동). old PID 854451은 graceful 종료했다. 추가 재기동·force kill·실주문은 실행하지 않았다.
- native bootstrap/봉인 handoff/원본 prepared 재검증 PASS. 원래 env/PREOPEN/dated policy/checklist 등 frozen 9개 hash 동일. 독립 episode pin 186개 동일.
- 메타데이터만 native publisher→현재 부모 CAS로 재발급했다. 현재 bundle `6bbf13a83d5c7c1873be4781d2d12c2c6817d327c04d6330c78bd3c810fcd2f4`, family `ec2ea546fff5892a74f7b28cef361ed1f6f42037a05e0de6a5b8d5e2a0592ddb`를 실제 PID가 13:04:35에 소비했다. 기계/보조 12셀 payload와 K/B/A/V1 연구 hash는 이전과 같다.
- 새 PID의 WS 연결과 5개 fixed watch 기계 capture 확인. 13:06:10 snapshot에서 BLOCK 3/RECHECK 2이며 ENTER/실제 주문·수익성 성공을 주장하지 않는다.
- 자연 거절 receipt 3개: 두산 만료 age 7.725424초(`aims-87566efb6c9c5c70af38`), 두산 무효화 age 4.281601초(`aims-56cf167975df9e28d61e`), HPSP 무효화 age 3.059662초(`aims-ababaec015c75446356c`). 정확 수신 row/동일 epoch/연결 segment 및 snapshot/token/attempt 검증 후 모두 diagnostics로 소비했다. 모두 provider_called=false/actual_order_submitted=false.
- 운영 감시기 자연 산출 13:05:20에서 신규 만료 1건이 diagnostics로 반영됐다. 13:06:10 read-only projection에서는 신규 무효화 2건도 확인됐다. 이전 PID의 증빙 없는 만료·무효화 4건은 현 10분 창 issues에 남는다. 과거 source가 수리됐다고 주장하거나 경보를 강제 해제하지 않는다. 장래 fresh source를 동일 native monitor 경로로 계속 관찰한다.
- 검증: 작업본 564 PASS, immutable 실행본 564 PASS; Python compile/bash syntax/diff/print-only parser PASS. 미해결 review finding 0은 이 최소 수리와 배포 인계 범위에 한한다. 신호 준비 지연의 전략적 개선/정책 TTL 변경은 이 source-only 수리 범위 밖이다.
- 최종 증거: `tmp/reversal-source-alert-20261007/final-closure.json`, `deployment-verify.json`, `activation.json`, `natural-rejected-traces.json`, `natural-monitor.json`, `source-semantics-live.json`, `targeted-tests.log`, `immutable-tests.log`.
