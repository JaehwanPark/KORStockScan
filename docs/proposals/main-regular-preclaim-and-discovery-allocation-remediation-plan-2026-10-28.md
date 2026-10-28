# 정규장 비상시 최초·재관찰 배분·적시 claim·유형별 보조판정 보완계획

> **10/28 후속 공통 설계:** [기한·신호 유효성·처리 경로 재설계](main-regular-submit-deadline-fresh-recheck-and-discovery-latency-remediation-plan-2026-10-27.md#entry-validity-redesign-20261028)가 신규 기한 대안과 상시/비상시 구현 우선순위를 소유한다. 이 문서의 원5초·기존 기한 보존은 당시 구현과 현재 승인된 운영값의 기록이며, 후속 연구의 기한을 고정하지 않는다. 기존 배분·패턴·원천 안전 및 PRE/REGULAR의 분리 수용은 유지한다.

## 1. 결정과 범위

**정규장 비상시 종목의 최초·재관찰 배분과 늦은 claim·AI 호출 전 기한 소진을 우선 보완한다.** 보조판정은 상시·비상시·종목유형별로 승리 복원을 유지하면서 실패 PASS를 줄이는지 검증한다. 매도 우세/원천 역할 분리와 저가 패턴 재검증의 기존 결과는 재사용하며, 의미 표시만 고치거나 AI 호출 수만 늘린 것을 전달·선별 개선으로 보고하지 않는다.

최초 지시는 **기존 상세계획 갱신**이었고, 후속 지시로 구현·리뷰·필요한 추가 오프라인 보조 연구 호출·배포 전 검증을 승인받았다. 아래§10의 별도 후보 이력과§11의 이번 구현/연구 결과를 구분한다. 실제 배포·재기동·운영 배분/보조 정책 교체는 이번 실행 범위에서 하지 않는다. 실행 owner는 기존 `MainEntrySourceTerminalRepair1022`와 `MachinePatternOpportunityResearch1023`를 유지한다. RFHIC 복구는 `HoldingProfitExitSourceContractRepair`가 소유한다.

이 문서는10/28 REGULAR 후속 보완을 소유한다. [10/27 공통 수리](main-regular-submit-deadline-fresh-recheck-and-discovery-latency-remediation-plan-2026-10-27.md)의 완료된 P0/P1·G1/G2와 [10/28 PRE 계획](main-premarket-opportunity-delivery-submit-latency-and-auxiliary-input-remediation-plan-2026-10-28.md)의 Q1/Q2 실험·668d76c0c 준비본을 재사용한다. PRE 연구 결과나 미배포 준비본을 REGULAR 운영 효과로 취급하지 않는다.

### 이번 갱신의 우선순위

| 순서 | 작업 | 구현·판단의 완료 기준 |
| --- | --- | --- |
| 1 / P1 | 비상시 최초·재관찰 적격 대기와 배분 전이 | 기존 반환 wake를 재구현하지 않고, 최초/재관찰을 각각 Q0/Q1/Q2와 같은 원천·자원에서 비교. source 없는 창은 U, 관찰 도달·재관찰 지연을 실제 lease로 확인 |
| 1 / P0-C | 늦은 claim과 호출 전 준비비용 | 원 event의 빠른 큐 방문 뒤 어디서5초가 소진됐는지 재현하고 중복 준비·불필요 대기 축소. 실제 새 유효 ENTER가 원 기한 내 AI까지 도달하는지 검증 |
| 2 / P3 | 유형별 보조입력·프롬프트 연구 | 같은 확인점의 승리 복원을 보존하면서 STOP/30분 미달 PASS를 줄이는지 누적·미사용 평가에서 비교. PASS 강제/전 유형 일괄 교체 없음 |
| 후순위 / P2 | 등록 저가 상승지속 후보의 재선택 | §10에서 재검증한 기존 실패 성적을 보존. 새 적격 날짜/입력·선택 계약이 바뀔 때만 영향 범위를 재비교 |

P1과 P0-C는 서로 독립적인 원인 재현·수리를 병행할 수 있다. P3의 기존 응답 재집계·표본 동결도 병행하되, 아직 AI에 도달하지 못한 사례를 실제 AI 오판정으로 취급하지 않는다. P0-A의 역할 분리 후보는 현재 veto를 유지하므로 그 코드 완료만으로 P0-C/P1이 해결됐다고 하지 않는다.

### 최신 동결과 재사용할 결과

- [12:02 점검](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-delivery-auxiliary-inspection-20261028-1202)은770b26078/PID3510901/start80028883의 역사 snapshot이다. 비상시 적격 대기338개·관측 최대770.764초, 종료25lease 모두 최초 관찰, 삼성 중첩 claim17개는 큐 방문 중앙29.981ms/claim4.784초/원5초 잔여216.347ms였다. local trace8개는 실제 provider0이다. [12:00 독립 대사](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-coverage-20261028-1200)의 KRX all 패널 상승16개는 구간 내 SOR eligible_due3~6회에도 새 PID claim0이었다. 다른 패널·동결의 가격 상승률을 같은 값으로 합치지 않는다.
- 슬롯 반환 후 정상 dispatch는770에서 이미 배포·자연 수용됐다. 현재 남은 것은 배분/재관찰·원 체류 용량과 큐 방문 이후 유효 claim/준비 경로다. 매도 우세/원천 역할 분리의 별도 구현은§10의 후보 상태이며 R1·Q1/Q2/Q3·보조 후보 운영 적용과 다르다.
- 계획 갱신 중12:27:21에는 선택본이 `buy-lineage-integrated-20261028-d0790117a`/`d0790117a3b224edde4c1b8e3809417299726d7d`, PID3661403/start80241527로 바뀌었다. 실제cwd와 native 정책 소비 ready를 재대사했다. 이 사실은 전 actor의 판정 수치나 역할 분리 후보의 배포 증명이 아니다. [원 actor·문서 baseline·strict 원본](../../tmp/regular-opportunity-aux-review-20261028/plan-refresh/baseline.json)을 보존하고 구현/자연 검증 착수 시 다시 핀한다.
- 정규장 미선택24점의 현행 재평가는 승리/실패 PASS8/6, A/G/H는12/12였다. 승리4개 복원과 실패6개 추가 PASS가 동시에 발생했다. 이 후보를 운영 답으로 재등록하지 않고§6의 P3 비교 기준·실패 대조군으로 재사용한다.

### 기준과 새로 확인한 사실

- 원 사고 동결은10:55의 `a55e37759/PID3200222/start79559884`다. 고정 감시 preclaim 실제 반환972회 중 매도 우세753회였고, Main ENTER2는 모두 AI CAUTION으로 끝났다. [원 분모·가드·상승 구간](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-submit-guard-inspection-20261028).
- RFHIC 세션이11:02:47에 `270511ce54b02b6a5da6a48d17148e45c9b15432`를 선택했다.11:11:39에는 후속 PID3327515 영수증이 발행됐다. 이것을 원a55 표본의 PID나 최종 RFHIC 수용으로 바꾸지 않는다. 계획의 [baseline·원본 보존·실제 import/code SHA](../../tmp/regular-preclaim-allocation-plan-20261028/baseline.json)를 남겼다. 구현 착수 시 그때 확정된 최신 선택본·실제 actor·진행 중 작업을 다시 대사한다.
- 11:17:39 선택 릴리스의 native reader로 PID3327515의 정책 소비 `ready/current_pid_consumption_complete`를 확인했다. 이는 RFHIC 잔여 수량·SELL 복구·health의 완료 증거가 아니며 그 owner의 최종 결과를 따른다. [읽기 대사](../../tmp/regular-preclaim-allocation-plan-20261028/current-consumption-read.json).
- 현 정책 bundle `4abcce1001c0cc689d7b749376ba91be6455f479e4332dc97a1d2fc2d39ca46f`의 `other_non_fixed|REGULAR|LT_20000|SOR`는 G4 단독이다. 누적 선택 영수증은 `CURRENT_NATIVE/carried, WIN4/resolved4`이며 시장 전체·독립 검증 성능4/4라는 뜻이 아니다.
- 같은 scope의 `cumulative_variant_groups`에는 **A01 HIGH_BREAKOUT, A02 MOMENTUM_HOLD, A14 RISING_STRUCTURE_HOLD 등을 포함한 A01~A16 추가 후보가 이미 등록**돼 있다. 기본 `manifest.scopes`의 G4 한 줄만 읽고 상승지속 후보가 미등록이라고 결론내리지 않는다. 후보 정의·비교 조합·실제 선택·PID 소비를 각각 검증한다.
- 별도10:51:57 동결은 일반종목 배정41/종료36/재관찰0, 적격 대기 관측330개, 체류 중앙150.022초·처리량 약1.94종목/분이다. 당시5슬롯×60/150초≈2종목/분 수준이므로 lost wake 수리만으로 대기를 없앨 수 없다. 이는 당시 관측의 용량 설명이며 모든 lease의 불변 처리량 상한은 아니다. [실제 범위·원천 거부·미배포 경계](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-coverage-20261028-1051).
- 당시 a55/270에는 반환 직후 재배정 수리가 미포함이었고 종료→다음 claim10.138초가 관측됐다. [당시 bytes 대사](../../tmp/regular-preclaim-allocation-plan-20261028/slot-release-source-validation.json)는 역사 원인 증거다. 이후770의 같은-loop wake 자연 수용으로 이 통합 결손은 회복됐으므로 현재 미구현 작업으로 반복하지 않는다.

## 2. 유지할 계약과 평가 원칙

| 항목 | 유지할 내용 |
| --- | --- |
| 기계·AI 권한 | 유효 기계 ENTER만 AI 호출, PASS만 기존 제출 경로, CAUTION/VETO/미평가는 기존 WAIT/차단. 시장 상태 분리는 강제 ENTER/PASS 권한이 아님 |
| 원천·주문 안전 | 필수 입력·exact route/item/epoch·시간/가격 현재성·충돌·executable BBO·spread/유동성·계좌/자금·수량·미체결/중복·cooldown·manual/custody·hard/protect/emergency 보존 |
| 기한 | 원 native signal5초와 별도 latency reference1,200ms를 각각 보존. 만료 신호 복원·now+5·옛 PASS 재사용·미확정 주문 재송신 금지 |
| 관찰 자원 | 기존5슬롯·동시성·short-slot 예약/borrow·필수 입력 창·retry due·fresh source120초·기존 최대 체류150초 보존. API/패널/구독·worker 추가 없음 |
| 시장 정체성 | REGULAR policy scope, `_AL/krx_nxt_integrated`, 요청/유효 broker route를 각각 고정. KRX 독립 가격 패널은 발견/coverage 진단일 뿐 SOR 실행 호가·실제 체결 venue 대체 불가 |
| 연구 입력 | 전역 clean 경계와 더 좁은 Main family refresh2026-09-29 이후의 native 적격 누적만 선택에 사용. 원 epoch/lease/원가·연속성·봉인·source hash를 확인하고 결손 row/window만 U/제외 |
| 승패·선택 | 같은 원 ask와 owning cost contract로 net+0.4%를30분 내 net soft stop−3%보다 먼저 관측하면 WIN. STOP/TIMEOUT/U 분리,30분 이후 도달은 후순위 진단. Main 기계 선택은 누적 승률이며 PnL/손익비·기존 제출 통과 여부를 새 채택 조건으로 추가하지 않음 |

기계 라벨, 실제 감시·AI·제출, 체결 venue, 완료 손익은 다른 증거다. trade 경로 라벨과 실행 가능한 bid 경로를 합산하지 않는다. 호가 수량/원 비용·연속 경로가 없으면 체결·순익을 추정하지 않는다. 오늘 미봉인 자료는 원인 재현에 쓰되 확정 성적의 분모에 넣지 않는다.

## 3. P0 — 매도 우세와 원천 결손의 분리

### P0-A: 기존 동작을 보존한 의미 수리

기존 [strength source helper·WATCHING caller](../../src/engine/sniper_state_handlers.py)의 `_strength_momentum_source_quality_block_reason`, `_handle_watching_strategy_branch`, `_strength_momentum_zero_context_fields`와 [native 진단](../../src/engine/monitoring/runtime_performance.py)의 `record_native_preclaim_gate`를 함께 검토한다.

1. stale snapshot·필수 체결/이력 부재·현재성/route/epoch 실패는 실제 source 차단으로 유지한다. `extreme_sell_dominant`는 관측된 시장 상태이며 데이터 부재로 표시하지 않는다. 단순 저매수비중과 필수 known-side 입력 결손도 구별한다.
2. 기존 source helper는 실제 원천 사유만 반환하도록 정리하고, 매도 우세 판정은 기존 momentum 결과/가드 owner에서 독립적으로 전달한다. 이 단계는 매도 우세의 **기존 반환 동작을 유지**하되 existing `baseline_block` 등 원 registry가 허용하는 역할로 기록한다. 단순 이름 변경을 병목 개선 완료로 보고하지 않는다.
3. pipeline의 실제 첫 blocker·역할, trade-quality history, native preclaim receipt, [제출 감시 소비자](../../src/engine/monitoring/submission_bottleneck_monitor.py)를 같은 의미로 갱신한다. market-state block을 API/원천 결손 경보로 오인하지 않되 진짜 결손·미진입은 계속 드러나야 한다. 과거 receipt·reason 문자열은 원 계약의 reader로 해석하고 원 bytes를 재작성하지 않는다.
4. 삼성 원 신호 `...:005930:1793151092725689:21499`와 실제10:50:36.670 가드 방문을 재현한다. native ready·queue visit·preclaim veto·실제 claim·AI를 분리하며, observed visits만으로 original deadline 전체의 연속성을 추정하지 않는다. 과거 unobservable43개를 차단 확정/승리43개로 바꾸지 않는다.

완료는 원 입력에서 동작 보존과 의미·직접 소비자 일치, 새 source loss의 계속된 검출이다. 진단 수리에 양의 수익이나 실제 주문을 요구하지 않는다.

### P0-B: 불필요한 앞단 veto를 없애는 후보 비교

**제안 후보 R1은 ‘필수 원천·안전 확인 → 기계 확인 → AI 위험 판정’이다.** 과거8초 매도 우세만으로 기계판정 자체를 봉쇄하지 않고 기존 risk-context에 전달한다. 새 수치 필터나 추가 반전 확인을 만들지 않는다.

- 현행 R0와 R1을 같은 적격 원 signal/입력에서 비교한다. R1도 현재 소스/호가·native 세대·원 기한을 확인하며 유효 claim/ENTER가 없으면 AI0·주문0이다. 신호가 없는 일반 tick을 전부 AI 호출로 바꾸지 않는다.
- 반전 이전 매도와 확인 이후 실제 새 매도/가격 훼손을 원 시간창으로 나눈다. 현재 위험은 기존 기계·AI·최종 안전 가드가 판단하며, 새 하락·빈/역전 호가·stale·가격 변경을 무시하지 않는다. 매도 우세를 PASS 근거로 뒤집거나 CAUTION을 승격하지 않는다.
- 동일 opportunity의 복수 branch/방문은 기존 중복 제거·원 claim 수명으로 한 번만 처리한다. REF/watch/evaluation/trace 소유권과 이전 미전송 종료·미확정 주문 경계를 유지한다.
- 원 guard에 막힌 WIN 복원뿐 아니라 **새 STOP/TIMEOUT의 진입 허용 증가**를 함께 보고한다. 실패를 제외하거나 승리 종목만 뽑아 R1 우월성을 계산하지 않는다. AI 요청이 달라지면 원 응답을 새 요청의 결과로 재사용하지 않는다.
- R1은 정책 효과가 있는 후보이므로 의미 수리와 별도 diff/선택 결과로 인계한다. 연구·후속 적용 권한과 원 발행 계약이 충족되기 전에는 R0 동작을 유지한다. 코드리뷰·fixture PASS를 자동 적용 근거로 삼지 않는다.

### P0-C: 빠른 방문 뒤 늦은 claim·AI 호출 전 기한 소진

우선 재현은 원 native `005930:1793155776330505:5492`다. 확인12:00:30.411839→큐 방문30.441820, 매도 우세11회 관측 뒤 gate 해제32.649→claim34.701055, 원 deadline35.411839로 이어졌다. **gate가 열린 뒤에도 약2.05초가 지나 claim했고 이후 입력·기계/보조 준비가 잔여711ms를 소진했다.** 같은 구간17개 event/async의 claim 잔여19.202~908.943ms와 local trace8개를 재현군으로 사용한다. 해당 삼성1점의5분 후행에 목표폭 상승이 없었다는 원 결과도 보존하며, 지연 수리를 확정 수익 손실 복원으로 주장하지 않는다.

1. 기존 [WATCHING caller](../../src/engine/sniper_state_handlers.py), [관찰·원 event 비교/claim](../../src/engine/scalping/reversal_source_diagnostics.py), [정책/평가 준비](../../src/engine/scalping/reversal_evaluation_context.py), [async 준비·완료](../../src/engine/scalping/scanner_async_eval.py)의 실제 호출 순서를 고정한다. native 확인→큐 첫 방문→source/시장 gate 각 반환·해제→관찰 snapshot→claim→입력 동결/기계→provider 시작→Main terminal을 같은 PID/event/attempt와 monotonic 원 기한으로 연결한다. 이미 있는 local-stage·native lifecycle 필드를 재사용하고 포함 구간을 합산하지 않는다.
2. gate 해제 뒤2.05초의 실제 원인을 호출 구간별로 분해한다. source snapshot/정책 로딩·전체 복사/재직렬화·검증/진단 쓰기의 반복, 다른 target/REST/공유 lock 대기는 해당 원 caller에서 확인된 부분만 축소한다. 원 source/currentness를 매번 검증할 부분과 hash로 고정한 불변 준비를 분리한다. 준비 가능한 정책·codec·immutable leaf는 기존 준비 owner를 통해 앞서 확보하고 현재 source 재검증을 남긴다. 비용을 다른 준비 큐로 옮긴 것만으로 개선이라 하지 않는다.
3. 앞단 veto가 열리기 전에 비소비 관찰/불변 준비를 할 수 있는지 검토하되 **claim 소비·AI·주문 권한을 앞당기지 않는다.** 살아 있는 다른 새 native 신호가 있더라도 원 selector/중복제거 규칙으로만 새 평가를 발행한다. 오래된 순서를 바꾸거나 시장 veto를 넘어 claim/AI를 허용하는 변경은 성능 수리와 분리해 P0-B/R1의 정책 비교·선택으로 취급한다.
4. 기존 `source_invalid/input_preflight_blocked/entry_deadline_expired`의 underlying error·failure phase·budget를 원 capsule/trace/완료 소비자까지 전달한다. 갱신 실패 안의 실제 deadline 소진을 원천 무수신으로 표시하지 않는다. worker error5/preparation_error1은 기존 error_type/error_message·event/attempt를 대조해 보존 가능한 원인만 확정한다. local `expired_after_response`는 provider_called=false이면 AI 응답/timeout 집계에서 제외한다. 새 병목 분류표·별도 validator/상시 로그 원장을 추가하지 않는다.
5. 원5초와 별도1,200ms reference/소유권을 유지한다. 현재 기한이 끝난 작업은 기존 owner에서 한 번 종료하고 provider0·submit0을 보장한다. now+5·옛 PASS·다른 신호 시계·완료시각으로 기한을 재시작하지 않는다. 새 신호·같은 평가 재시도·진행 중/미확정 주문을 구분하며 동시 중복 호출을 막는다.

완료 기준은 원 입력/원 guard에서 불필요 대기·반복 비용 감소, 기한 내 유효 claim→기계→provider 도달과 동일 평가의 terminal 연결이다. 단순히 만료 요청을 덜 만들거나 reason만 바꾼 것으로 닫지 않는다. 진짜 시장 veto·만료·새 신호 부재도 유효 terminal이며 실제 AI/PASS 표본이 없으면 해당 자연 수용만 기존 owner에 OPEN으로 남긴다. 새로운 최소 잔여ms/추가 대기/timeout 상향을 도입하지 않는다.

## 4. P1 — 일반종목 최초·재관찰 배정

### P1-A: 배정 전이·연속 입력의 최초 결함 수리

기존 [issuing scanner](../../src/scanners/scalping_scanner.py)의 `next_probe_epoch`·결과 drain/dispatch loop, [queue](../../src/scanners/zero_base_discovery_queue.py)의 `observe/claim/resolve/close_handoff`, [runtime](../../src/scanners/zero_base_discovery_runtime.py)의 `drain_results/dispatch_due_probes/_persist`와 [probe](../../src/engine/scalping/zero_base_probe.py)를 함께 사용한다. 배포된 physical-return wake는 재사용하고, 아직 남은 최초/재관찰 배분·due·연속 입력의 전이를 재현한다.

1. 미코·빛샘·엠케이의 최초 미배정, 멜콘·빛과전자의 종료 후 재관찰0을 exact admission/source SHA·due·active target·slot·physical release와 연결한다. 발견 후 경과시간을 연속 적격 대기로 대체하지 않는다. 큐733개와 적격 관측330개는 다른 동결이며 합치지 않는다.
2. fresh source 갱신 중 in-flight 원 claim을 보존하는지, resolve 후 due/lease가 정확히 닫히는지, 종료/재시도 결과가 새 발견에 영구 묶이는지 재현한다. bd6439c77 계열 wake는770에 포함·자연 수용됐으므로 새 parent에서도 보존됐는지 검증하고 **다시 이식하지 않는다.** persist/physical ACK 뒤 기존 정상 dispatch를 유지하며, 재발이 입증되지 않은 polling·패널 주기 변경이나 별도 worker 추가는 없다.
3. stale/active/product/route/retry-not-due·handoff/cleanup-pending은 실제 배정 차단으로 유지한다. 오래된 claim completion·쓰기에 실패한 claim은 새 lease가 아니며, persist 성공 전 worker를 시작하지 않는다. lease 반환 증거 없이 capacity를 해제하지 않는다.
4. 빛과전자의60초 창이28.049초로 끊긴 지점을 원 trade/depth/정규화/native reset에 연결한다. 실제 stale/epoch 변경으로 끊긴 창은 유지한다. 같은 item·lease·epoch의 연속 prefix를 producer가 잘못 버린 경우만 기존 window owner에서 보존하도록 수리한다. 서로 다른 lease/미수신 구간을 연결하거나60초 요구를 낮추지 않는다.
5. 10:32의 stale 시세1303건은 시세→packet ingress 지연과 packet→정규화 지연을 분리한다. 로컬 receive loop와 외부 전달 원인을 구별하기 전 API 장애/정상 무거래로 단정하지 않는다. 요청·subscription/parser 변경이 필요해지면 공식 Kiwoom Reference Gate와 해당 작업 권한을 별도 적용한다.
6. 최신 재현군은 이글루·파이오링크의 최초0, 샌즈랩·멜콘·안랩의 종료 후 재관찰0과 구간 내 exact eligible_due를 사용한다. 동일 code만으로 과거/현재 source generation을 합치지 않고 source SHA·item/route·lease·due·최초/직전 종료·새 갱신을 연결한다. 같은 상승 패널의 미상승·실패/정체 종목도 포함해 사후 상승 종목만 우선하는 배분 후보를 만들지 않는다.
7. 최초와 재관찰 각각의 현재 적격 시작·dispatch 관측·선택/미선택·active/stale/retry 제외를 기존 admission/queue receipt에서 검산한다. first_seen을 대기 시작으로 대신하지 않는다. restart·실제 부적격·활성 lease 전이는 기존 eligible_since/restore owner에서 처리하고 관측 전 시간을 추정해 누적하지 않는다. due가 된 종료 종목이 계속 첫 관찰 종목 뒤로 밀리는지 현재 sort/age-turn을 직접 확인해 Q2가 실제 재관찰까지 서비스하는지 검증한다.

### P1-B: 기존 배분 후보의 REGULAR 비교

PRE 준비본의 `allocation_policy=current|eligible_wait|service_wait`와 age-turn 후보를 재사용한다. **Q1/Q2 opt-in 구현 존재와 현재 운영 선택은 다르다.** 최신 live caller의 기본값·실제 인자·등록 상태를 확인하고 완성본 전체를 복사하지 않는다.

| 후보 | 동결할 차이 | 유지할 조건 |
| --- | --- | --- |
| Q0 | 최신 배포의 현행 순서 | 동일 source/도착·cohort·slot·체류·due |
| Q1 eligible_wait | 기존 age turn에서 현재 인증된 최초 관찰 적격 대기를 반영 | 나머지 activity turn·3:1 source 순환·long-deferred/short 예약 보존 |
| Q2 service_wait | 같은 age turn에서 due가 된 재관찰과 최초 후보의 service/적격 대기를 함께 비교 | 재시도 앞당김·새 예약 slot·동일 종목 독점 금지 |

후보 sort key·동점·eligible_since 수명/restore·source 갱신 시 전이를 준비본과 대사해 사전 고정한다. restart 또는 실제 부적격 전이로 대기가 끊기면 first_seen으로 이어 붙이지 않는다. 후보별 최초/재관찰 대기 분포·최댓값·성숙 이탈·기계/Main 도달·종목 독점·쓰기/dispatch 비용을 같은 입력에서 비교한다. 미관찰 구간의 synthetic tick/기계 결과·다른 종목 lease 길이·미래 상승률을 배정 순위에 넣지 않는다.

비교 산출물은 `최초/재관찰 × 원 가격유형 × source/cohort`별 적격 수·실제 배정·대기 중앙/p95/최대·재관찰 간격·유효 입력 성숙·기계/AI 도달과 추가 WIN/STOP/TIMEOUT/U다. 다른 유형의 대기 악화·종목 독점도 함께 보고한다. 실제 관찰 구간은 원 lease 길이를 쓰고, 후보가 새로 관찰했을 구간에 원천이 없으면 도달/승패를 만들어내지 않는다. 전이 수리는 원 입력 정상화로, 배분 후보 효과는 별도 비교로 판단한다. Q1/Q2의 기존 opt-in 의미가 이 요구를 담지 못하면 그 기존 owner를 보완하되 운영 `current`를 조용히 바꾸지 않는다.

관측한 자원 한계 때문에 Q1/Q2로 모두 즉시 관찰할 수 있다고 약속하지 않는다. Q1/Q2 뒤에도 장기 대기가 남으면 **Q3 ‘필수 창 성숙 뒤 관찰 회전’은 오프라인 정책 연구로만** 비교한다. 후보 반환점은 exact lease의 native `full_input_requirement_seconds`가 충족된 후, 현재 선택 branch가 모두 평가 가능한 FALSE이고 UNKNOWN/진행 중 확인이 없는 첫 기존 평가 경계다. 신호가 있으면 기존 확인/편입/원 기한 경로를 따르고 반환하지 않는다. 원 최대150초·원 예약/신호 deadline·모든 입력 최소 창과 physical release ACK를 유지하며 예약을 short slot으로 바꾸지 않는다. 필수 창 성숙 전 FALSE 한 번이나 사후 하락 예상은 반환 근거가 아니다. 미래 반전 포착 손실·재구독/성숙 비용·추가 W/STOP/TIMEOUT/U를 같은 적격 연속 원천에서 비교한다. 미관찰 창은 U로 남기며 증거/권한 전에는 기존 체류를 유지한다. 기존 승인 조합으로 표현되지 않으면 별도 검토 대상으로 남기며 이번 성능 수리에 숨기지 않는다.

## 5. P2 — 저가 상승지속 후보의 실제 선택 검토

대상은 **일반 비상시 `other_non_fixed|REGULAR|LT_20000|SOR`**다. 삼성 ALL·다른 고정종목·2만원 이상·PRE/AFTER로 자동 확대하지 않는다. 원 확인가격으로 band를 정하고2만원 경계 이동을 native resolver와 대사한다.

아래는 등록/재검증 절차이며 §10에서 완료한 동일 source27 비교를 다시 실행하라는 TODO가 아니다. 새 적격 날짜·입력/정의·선택 계약이 변한 범위만 후속 비교하고 P1/P0-C를 막지 않는다.

### 기존 등록을 먼저 검증한다

기존 [누적 catalog](../../src/engine/scalping/reversal_cumulative_catalog.py), [등록/조합 owner](../../src/engine/scalping/reversal_cumulative_registration.py), [누적 장후 평가](../../src/engine/scalping/reversal_cumulative_postclose.py), [운용 기여 평가](../../src/engine/scalping/reversal_operating_evaluation.py)를 따른다.

1. 실제 manifest의 base scopes·`cumulative_variant_groups`·정의/registry SHA·조합 권한·machine report·선택 receipt·publisher·runtime membership을 끝까지 연결한다. 왜 G4가4/4로 carried됐는지, 후보의 W/STOP/TIMEOUT/U·평가 범위·미평가/제외·비교 조합이 무엇이었는지 확인한다. base scope 목록만으로 등록 누락, 적은4/4만으로 일반 저가 전체의 우월성을 단정하지 않는다.
2. 기존 **A01 HIGH_BREAKOUT, A02 MOMENTUM_HOLD, A14 RISING_STRUCTURE_HOLD**를 우선 재생한다. 비교는 현행 G4, 후보 단독의 기여 진단, 승인된 `G4+각 후보` 조합이다. 단독 진단을 자동 단독 운용 권한으로 바꾸지 않는다. 조건·root·hold·정의 SHA는 임의 수정하지 않는다.
3. 이 등록 batch의 `valid_membership`은 추가 후보1개를 허용한다. 이는 전체 Main의 ‘정책2개 상한’이 아니다. 여러 상승지속 후보를 동시에 추가할 필요가 확인되면 기존 등록 owner에 연구로 고정한 조합만 등록한다. 기존 batch 검증을 포괄 허용으로 바꾸거나 A01~A16 전부를 자동 활성화하지 않는다.
4. 선택된 반전·상승지속 branch는 각 root와 입력으로 독립 탐지하고 기존 `ANY_MATCH_ONE_INTENT`를 유지한다. 같은 기회에서 여러 branch가 충족돼도 모든 signal ref를 포함한 공통 AI 판정과 주문 의도는 한 번이다. 새 membership/입력·bundle/정의 SHA에 옛 PASS/cache를 연결하지 않는다. 보조 계약의 호환성과 보조 우월성은 구별하고, 기존 등록 계약이 요구하지 않는 미완료 AI 비교를 새 초기 등록 gate로 추가하지 않는다. 실제 진입은 여전히 현재 입력의 AI PASS와 최종 안전 가드가 필요하다.

### 원천 전체에서 확인점을 찾는다

기존 ENTER/AI 호출점만 시작점으로 삼지 않는다. native 적격·봉인된 **일반 저가 정규장 연속 원천**에서 현재 반전과 등록 상승지속 패턴의 확인점을 인과적으로 열거한다. 멜콘·빛과전자·빛샘·엠케이는 재현 진단군이며, 상승하지 않은 종목·실패/정체 구간도 같은 모집단에 포함한다. 이후 가격은 라벨에만 사용한다.

각 확인점의 TRUE/FALSE/UNKNOWN, 실제 watch/probe/미관찰, branch·원 기한·원 ask·원 비용·데이터 route를 보존한다. 같은 종목/일자/route의 중첩30분 창·여러 branch는 고유 기회 cluster와 원 신호 수를 함께 제시한다. 원 publisher의 기회 key와 집계법은 조용히 바꾸지 않으며 개발/독립 평가 간 같은 cluster가 새 표본으로 새지 않게 한다. 미구독 상승 창은 가격 진단으로 남기고 기계 재생 WIN을 만들지 않는다.

## 6. 비교·채택·저장 요건

### P3-A: REGULAR 누적 모집단·유형·기준선

보조 연구의 목적은 **유효 기계 기회 중 승리는 보존하고 실패 PASS를 줄이는 것**이다. 기계 통과 전 미관찰/패턴 불일치와 provider 전 기한 소진은 P1/P0-C가 소유한다. 실제 AI 응답 없는 점은 오판정 분모에 넣지 않고, 필요한 경우에만 같은 확인점의 별도 반사실 입력 연구로 명시한다.

- 당일만이 아니라 실행 시 native owner가 허용하는 clean/가족 refresh 이후의 **가용 누적 REGULAR 적격 원천 전체**를 census한다. 최신 활성 machine membership을 native 재생/검증된 확인점에 적용해 현재 선택 기계 확인점과 등록 미선택 패턴의 반사실 확인점을 별도 보존한다. 기존 source26 연구의14선택/24미선택/16회귀·중복 제거51확인점과 정확한 응답은 회귀군으로 우선 재사용한다. 이14점을 최신 정책의 전체 모집단으로 대신하지 않으며, source27 이후 정책·원천 세대가 바뀐 확인점/의존 범위만 재검증한다. 이미 검증한 원 계산을 변경 없이 전부 재생하거나 오래 노출된 회귀 표본을 새 검증으로 부르지 않는다.
- 축은 `실제 FIXED_WATCH/NONFIXED_PROBE/UNVERIFIED × REGULAR × native 종목/가격유형 × data item/route·요청 route`다. 설정상 감시 분류도 보존하되 실제 이력 미확인을 비상시로 채우지 않는다. 삼성 ALL·두산/주성/알테오젠/HPSP 개별 scope와 비상시 LT_20000/20000_TO_100000/GE_100000을 원 resolver로 구분한다. 한 종목이 가격 band를 넘은 경우 원 확인시각의 유형을 쓴다.
- 라벨은 같은 원 entry ask·owning cost contract·30분 net+0.4%·net soft stop−3%보다 목표 선도달이다. WIN/STOP/TIMEOUT/U를 분리하고 trade/bid 라벨을 합산하지 않는다. 동일 종목/날짜/route의 중첩30분 창·동일 기회의 복수 branch/재호출은 point/cluster/attempt별로 각각 센다. 미래 결과는 라벨에만 쓴다.
- source28 장중 prefix는 원인/입력 진단에 우선 사용한다. REGULAR 종료분을 기존 native owner가 독립 봉인·검증할 수 있으면 그 source generation부터 추가하고, 임의로 AFTER 종료나 전체 장후완료를 선행 조건으로 추가하지 않는다. 독립 봉인이 지원되지 않으면 기존 적격 누적 연구를 계속하며 그 창만 U로 남긴다.
- N은 각 유형의 실제 현행 registry/input/prompt/model/schema 바인딩이다. A는 **승리 복원 연구 기준선**이며 현재 운영과 동일하거나 우월하다고 전제하지 않는다. 실패도 모두 PASS했던 A/G/H와 PRE/AFTER 결과는 보존하되 REGULAR 후보의 성공 근거로 재사용하지 않는다. PRE/AFTER는 별도 회귀/후순위이며 이번 REGULAR 연구 예산·효과에 합산하지 않는다.
- 과거 A 응답은 원 복원 집합·회귀 근거로 보존한다. 모델/옵션/schema/입력 세대가 다른 응답은 현재 N과의 causal paired 결과로 합치지 않는다. exact 요청이 다르면 기존 응답을 새 요청의 cache hit로 쓰지 않으며, 현재 계약의 A 재호출이 필요하면 같은 누적 예산에서 별도 계산한다.

### P3-B: 사실 역할과 유형별 prompt의 분리 비교

기존 [research population](../../src/engine/scalping/reversal_auxiliary_research_population.py)·[research executor](../../src/engine/scalping/reversal_auxiliary_research.py)·[입력 실험 owner](../../src/engine/scalping/reversal_auxiliary_risk_context_experiment.py)·[wire](../../src/engine/scalping/reversal_auxiliary_research_wire.py)를 사용한다. 이미 존재하는 PRE 시간구간 분리와 REGULAR G/H 실험을 검토하고 차이가 없는 후보를 이름만 바꿔 호출하지 않는다. production의 SHA 고정 입력은 연구 편의로 바꾸지 않는다.

| 비교 | 바꿀 내용 | 고정할 내용 |
| --- | --- | --- |
| N 대 I | 기존 입력의 사실·해석 역할/동일 구간 결속 | 유형별 현행 prompt·원 point/branch·model/옵션·응답 검증 |
| N 대 P | 감시/종목유형별 위험 해석 prompt | N의 입력 bytes/schema·동일 source/point/옵션 |
| I 대 IP | 입력 효과 위에 유형별 prompt 효과가 필요한 경우만 비교 | I의 입력 bytes/schema·동일 point/옵션 |
| A 복원 회귀 | 기존 복원 WIN의 PASS 보존·실패 PASS 변화 | A의 exact 응답과 원 라벨/point identity |

기존 schema로 표현되지 않는 사실/인용 vocabulary를 추가하면 그 arm은 **입력+schema 변경**으로 표시하고 원 codec/validator를 함께 검증한다. 서로 다른 실제 요청에 기존 응답을 붙이거나 prompt만의 효과라고 하지 않는다.

입력 후보는 원 확인시각 이전의 같은 시간 구간에서 다음 사실만 간결하게 투영한다. 수치·단위·구간 시작/끝·coverage·item/epoch/sequence를 보존하고 해석 문장/최종 verdict와 분리한다.

1. **중립 호가와 새 악화:** 양수 spread/절대 호가폭은 거래 비용 사실이다. 실제 같은 구간 bid 후퇴·가격 되밀림·호가폭/관측 수량 악화는 원천으로 확인된 경우에만 별도 반증 사실로 전달한다. trade 반등을 bid 개선으로, 잔량 미관측을 실제 고갈로 바꾸지 않는다. HPSP의 observed_spread 단독 CAUTION은 재현군이며 자동 PASS 대상이 아니다.
2. **회복 전 하락과 회복 후 재손상:** 원 phase/anchor 전후의 trade·known-side 수량·bid/ask를 같은 구간으로 묶는다. 삼성의60초 음수와 확인 직전 반등처럼 서로 다른 구간이 공존하면 각각 명시한다. 현재 매도 우세/새 하락도 보존하고 반전 신호 자체를 무조건 낙관 근거로 만들지 않는다.
3. **회복 유지와30분 미달 위험:** 현재 회복/되밀림 사실과 원 ask·비용 후 필요한 목표거리를 별도로 보여준다. 과거13초/10체결 상승을 미래30분 진척에서 차감하거나 속도로 외삽하지 않는다. 새 악화가 없다는 사실만으로 목표 도달을 보장하지 않는다. 실제 관측 가능한 가격 정체·흐름을 함께 평가하되 새로운 확률/숫자 veto·추가 확인 대기를 만들지 않는다.

P/IP는 `REGULAR × 상시 개별 scope/비상시 가격유형`별 후보 text·SHA·출처를 사전 동결한다. 상시 관측이 길거나 비상시가 짧다고 임의 가정하지 않는다. 전 유형 공통 prompt 하나를 새 기본값으로 두지 않고, 동일 문구 공유는 해당 유형별 비교가 지지하는 경우에만 검토한다. 자동으로 긴 prompt를 계속 생성하는 탐색 루프는 없으며 원 연구 owner에서 후보를 명시 등록한다.

### P3-C: 실행·평가·채택 검토

1. **무호출 재집계:** exact 기존 응답과 원 input/prompt/model/schema/옵션/validator hash를 대사해 누적 confusion table을 재집계한다. 승리 오차단·STOP PASS·TIMEOUT PASS를 유형별로 대조하고, 기존 A/G/H가 같은 실패를 통과시킨 원 사실/해석/최종 판단을 구분한다. source·clock·timeout/미호출은 별도 분모다.
2. **가설 동결 후 paired 호출:** 차이가 설명되는 I/P만 같은 원 point에서 비교한다. 모든 실패 원천을 census에 포함하고, 비용 때문에 표본을 뽑으면 날짜·유형·WIN/STOP/TIMEOUT별 선정 규칙을 응답 전에 고정한다. 균형 진단 표본 성적은 모집단 승률이 아니다. 이미 본 실패/승리에만 맞춘 후보를 최종 검증으로 채택하지 않는다.
3. **미사용 날짜·비중첩 평가:** 개발과 겹치지 않는 날짜/cluster에 같은 후보 bytes를 적용한다. 현재 적격 신규 표본이 없으면 검증 부족으로 남기고 미래 창은 기존 checklist에서 이어간다. 응답 변동 반복은 같은 요청의 안정성 진단이며 새 독립 표본이 아니다.
4. **간단한 판단:** 같은 유효 paired 집합에서 `A로 복원된 WIN의 새 오차단 없이 승리 PASS 유지/증가`와 `실패 PASS 감소`를 함께 확인하고, PASS 누적 승률 `WIN_PASS/(WIN_PASS+STOP_PASS+TIMEOUT_PASS)`를 보고한다. 복원 집합은 exact point key로 확인해 다른 승리 증가로 기존 복원 손실을 감추지 않는다. N 대비 변화도 함께 제시한다. A 대비 실패가 줄어도 현행 N보다 누적 PASS 승률이 나빠지면 현행 개선으로 채택하지 않는다. 실패 PASS를 줄이는 대신 승리를 잃은 후보는 목적 미충족으로 보존한다. 임의 손익비·수익금·새 표본 하한을 추가하지 않는다.
5. **유형별 인계:** 결과표는 scope별 평가 WIN/STOP/TIMEOUT/U, N/A/I/P/IP의 승리 PASS·STOP PASS·TIMEOUT PASS·승리 오차단, 복원 유지/신규 손실, 제거/추가 실패 PASS, 누적/날짜별/미사용 평가·point/cluster 수다. 상시 한 종목의 개선을 비상시 전체로 확대하지 않는다. 승리 또는 실패가 없는 셀·실제 watch 미확인은 해당 성능 미검증으로 남기고 원 바인딩/상속 계약을 유지한다.

응답은 공통 store의 content identity로 재사용하며 원 source/point pack·AI 원장을 유형/후보마다 복제하지 않는다. 새 호출은 실행 시 native 누적 grant·기사용량·예약/잔여를 검증한 차집합만 실행한다. 실패 attempt·캐시 hit·실제 호출·미호출을 각각 기록하고 한도 초기화·자동 증액·무한 재시도를 하지 않는다. **이번 계획 갱신의 추가 호출/예산 발행은0**이다.

효과가 확인된 셀만 기존 [intraday publisher/reader](../../src/engine/scalping/reversal_auxiliary_intraday.py)의 후속 구현·등록/게시 검토로 인계한다. 정책/입력/schema·cache 세대 일치와 진행 중 옛 평가의 원 terminal을 검증한 뒤 승인된 범위에서 장중 소비한다. 타 유형의 검증을 기동 gate로 추가하거나, 연구 PASS만으로 전 유형 적용/재기동을 실행하지 않는다.

### 공통 비교·자원 요건

- P0-C/P1의 원 전이·준비 수리는 같은 입력/안전에서 불필요한 시간·비용과 정상 전달을 검증하며 후행 WIN 확정을 수리의 선행 gate로 추가하지 않는다. P3의 입력/prompt 효과, Q/R의 정책 효과와 P2의 membership 선택은 각각 원 기준으로 별도 평가한다.
- P0 R0/R1은 동일 machine membership, P1 Q0/Q1/Q2는 동일 signal/policy, P2 G4/추가 후보는 동일 적격 원천을 각각 먼저 고정해 효과를 분리한다. 마지막에 선택된 조합의 상호작용을 검증한다. 여러 변경의 합산 성과를 어느 하나의 수리 효과로 돌리지 않는다.
- Main 패턴 선택은 기존 metric의 `WIN/(WIN+STOP+TIMEOUT)`를 정확한 분수로 비교한다. 같은 승률이면 추가 확정 성공을 주는 조합을 기존 tie rule로 검토한다. 실제 누적·날짜별·독립 cluster와 추가 WIN/실패·기존 WIN 손실·U를 모두 공개한다. 임의 EV/손익비·최소 거래 수·기존 제출 fixture 통과율을 새 alpha 채택선으로 만들지 않는다.
- G4의 작은4/4와 광범위 후보를 비교할 때 각 분모·coverage·날짜·독립성 한계를 공개한다. 낮은 빈도를 숨기지 않고, 같은 eligible 입력에서 후보의 실제 실패까지 포함한다. 우월성 미입증은 현행 유지이며 등록/연구 결함의 부재 또는 충분한 기회 포착을 뜻하지 않는다.
- 배분/진단 코드 수리는 동일 입력의 정상 전이·안전 회귀0·불필요 대기/비용 감소로 검증한다. Q1/Q2/Q3/R1 같은 정책 효과는 별도 비교·선택 상태로 남긴다. 기계 자체의 선택 증명과 AI 이후 전략의 W/실패 허용·실제 제출·완료 경제성을 합치지 않는다.
- native index/manifest/checkpoint를 우선 사용하고 live raw는16MiB 이하 bounded window로 읽는다. source28은 해당 REGULAR 창의 native 종료/봉인·직접 소비 인증 뒤 적격 누적에 추가하며, P3-A의 독립 정규장 봉인을 전체 AFTER 종료 대기로 바꾸지 않는다. 원 hash/offset·제외 사유·stage reuse/read-only revalidate/regenerate를 기존 인계에 남기며 이미 검증한 장후 계산/EOD를 전부 재생하지 않는다.
- [공통 원장](main-ai-comparison-ledger-dedup-and-incremental-storage-plan-2026-10-07.md)의 source/point/outcome/요청 content 참조와 증분 resume를 재사용한다. 조합마다 원천·AI 원장을 복제하지 않는다. Q·기계 재생은 AI0이 기본이다. R1의 실제 AI 비교가 필요하면 exact 요청 응답부터 재사용하고 native 누적 grant·동시 예약·미호출 차집합 안에서만 실행한다. 계획 작성만으로 호출 한도를 증액하지 않는다. 후속 실행 승인으로 발행한 native grant와 실제 사용량은§11에 따로 기록한다.

## 7. 구현·리뷰·검증 순서

| 순서 | 산출물 | 완료 기준 |
| --- | --- | --- |
| S0 | RFHIC 최종 배포본/실제 actor·정책·준비본·원 실패의 code/source inventory | 최신 parent와 다른 dirty 작업을 분리, 기존 source/실패 보존, 반복 구현 없음 |
| S1 / P1-A·P0-C | 최초/재관찰·gate 해제→claim/입력 준비 원인 재현과 수리 | 기존 wake·P0-A 후보 재사용, 현재 원천/시장 veto 보존, 불필요 대기 축소·기한 내 정상 AI 도달과 실패 종료 검증 |
| S2 / P1-B·P0-B | Q0/Q1/Q2와 필요한 R0/R1을 분리 비교 | 같은 적격/자원에서 최초·재관찰 지연·추가 W/STOP/TIMEOUT/U 공개. Q3는 별도 연구 |
| S3 / P3 | 누적 응답 재사용→I/P/IP 비교→미사용 평가 | 상시·비상시·종목유형별 복원 WIN 보존/실패 PASS 감소·정확 요청/분모. source 결손/만료를 AI 오판정으로 세지 않음 |
| S3 후속 / P2 | 새 입력/선택 계약에 영향이 있을 때만 저가 조합 재검증 | §10의 기존 부정 결과 보존, 동일 원천의 변경 없는 전수 재실행 없음 |
| S4 | 자체 리뷰→수정→재리뷰·영향 검증·후보 인계 | 실제 변경 caller와 직접/전이 소비자 일치, 안전 회귀0, 코드/정책/배포 상태 구분 |
| S5 | 후속 권한에 따른 통합·실제 PID·자연 수용 | RFHIC 최종 parent 보존·native 전환·동일 scope/route·새 PID 소비/신호·terminal 검증 |

검증은 기존 `test_strength_momentum_gate`, `test_strength_momentum_observation`, `test_native_signal_claim_diagnostics`, `test_scalping_scanner_candidate_pool`, `test_zero_base_discovery_queue/runtime`, `test_zero_base_probe/main_attach`, `test_reversal_cumulative_policy`, `test_reversal_operating_policy`와 실제 WATCHING/submit 통합 fixture를 확장한다. helper 단독 성공으로 caller의 실제 `return False` 수리나 physical submit·issuing loop의 반환 후 재배정을 증명하지 않는다.

필수 음성은 필수 source/known-side 결손, stale/빈·역전 호가, 다른 item/route/epoch·policy generation, 원5초/별도1200ms 만료, 반복 native 신호·동시 새 평가·옛 completion, handoff/cleanup/restore·source 갱신·writer failure, 가격/계좌/주문/수량/custody다. 공식 master로 검증된 숫자/영문 코드와 unknown 상품·가격 band 경계를 대사해 최신 RFHIC 통합본의 code 지원을 후퇴시키지 않는다. 공유 handler 변경은 RFHIC를 포함한 HOLDING/SELL·manual/퇴역 경계 회귀도 확인한다. 오프라인 no-network provider/broker와 격리 writer를 쓰며 live 주문을 시험하지 않는다.

성능은 동일 원 형태의 cold/warm·경합 입력에서 native 확인→첫 방문→claim→AI→Main→submit, dispatch/persist·queue wait를 분리한다. 반복 전수 JSON/hash/복사·진단 I/O가 원인일 때만 기존 owner에서 제거한다. 시간이 다른 큐로 이동한 것을 개선으로 세지 않고 새 기한·p99 강제 gate를 추가하지 않는다. compile·대상 pytest·diff와 문서 owner/link/print-only parser를 검증한다.

이번 추가 회귀는 실제17개 late claim/8개 local trace의 source shape와 최초/재관찰 admission 전이를 사용한다. 같은 event의 첫/반복 방문·gate 해제·동시 새 event·기한 경계·선택/미선택·옛 completion·writer 실패와 source/clock/세대 음성을 actual WATCHING→async caller에서 검증한다. P3는 fact 역변환·동일 구간/미래 유입·타 item/epoch·schema/인용·exact cache/예산 음성과 유형별 현행/A 복원 회귀를 검사한다. 운영 안전 회귀와 오프라인 분류 효과는 별도 결과다.

## 8. RFHIC 충돌 방지·인계와 교체

**RFHIC 전환 owner가 selector/hold·drain/start·보유/주문 원장과 최종 준비/observer/health를 계속 소유한다.** 이번 계획 때문에 복구를 중지·되돌리거나 별도 Main을 시작하지 않는다. 실제 기동이 바뀌면 관측 epoch/PID를 새로 결속한다.

구현은 그때 확정된 최신 RFHIC 배포 commit 기반의 격리 작업본에서 시작한다. 공유 `sniper_state_handlers.py`·`runtime_performance.py`는 필요한 BUY 함수/진단 hunk만 합치고 SELL·수량/custody 변경을 보존한다.770 이후 포함된 Q opt-in/반환 wake와§10의 역할 분리 후보는 각각 현 parent의 포함 여부·원 차이/검증을 확인해 재사용한다. 같은 수리의 재이식·소스 파일 전체 교체·작업본 전체 통합은 하지 않는다.

배포가 후속 승인되면 native routing owner로 단일 후보를 준비한다. 사전 release/worktree 용량·원본/rollback 참조를 확인하고, 하나의 변경 소비자 inventory로 guard/trace/history/monitor·discovery·정책 catalog/publisher/runtime·영향 장후/준비 reader·공유 holding/exit를 대사한다. code/profile·독립 준비·원 active parent·최종 세대 검증을 거쳐야 하며 report-only 진단을 새 기동 gate로 만들지 않는다. 선택 후 준비와 실제 PID 소비·observer/첫 health는 후보 검증과 별개다. 오래된 모든 인계 조합을 전수 검사하지 않는다.

| 기존 경로 | 처분 |
| --- | --- |
| 매도 우세를 source 결손으로 돌려주는 중복 역할 | P0-A에서 `consolidated`; 과거 reader/원 receipt는 `retained` |
| 실제 freshness/BBO/source·물리 전송·clock·계좌/주문/수량/custody | `retained`; 다른 entry/holding/exit 경로의 보호도 보존 |
| 중복 wake·재관찰 분기·반복 동일 snapshot 쓰기 | 실제 caller 이전 후 겹치는 부분만 `removed`; 이미 수리됐으면 추가 변경 없음 |
| Q1/Q2·누적 catalog/registration/공통 store | 기존 owner로 `consolidated`; 새 queue/worker/validator/원장 없음 |
| claim/평가 준비·같은 정책의 중복 복사/검증 | P0-C에서 원인이 확인된 중복만 `consolidated/removed`; 현재 source·원 기한 검증은 `retained` |
| 보조 연구 I/P/IP·A 기준선 | 기존 research population/executor/실험/store로 `consolidated`; 원 응답·실패는 `retained`, 미검증 셀의 운영 적용은 `deferred` |
| R1/Q1/Q2/Q3·추가 저가 조합의 운영 적용 | 비교/권한/원 발행 계약 충족 전 `deferred`, 기존 두 OPEN ID가 소유 |
| RFHIC 복구·원장·주문/취소·startup hold | 별도 owner에 `retained`; 이 작업의 삭제/조작 대상 아님 |

후속 인계는 base/candidate commit·릴리스 경로·필요 source/code generation·원 실패/정상/음성·소요시간/자원·등록/선택/미적용 목록·교체/잔여를 포함한다. 구현·정책 채택·배포·실제 PID·자연 전달/제출·실현 경제성을 각각 보고한다.

자연 재점검은 기존 checklist의10/28 REGULAR13:30~14:00에 **그때 실제 배포된 actor**를 관측하고, 미구현/미배포이면 현행 관측으로만 남긴다. 변경 branch가 미관측이면10/29 REGULAR09:05~09:25로 같은 owner를 잇는다. 기존10/29 PRE08:05~08:20 수용은 별도 유지하며 REGULAR로 닫지 않는다. 미래 창은 자동 실행/정책 적용·재기동 예약이 아니다.

## 9. 이번 계획의 리뷰·검증 경계

현재 native 구현·기존 준비본·원 현상·등록/선택 receipt를 대조했다. 기본 scopes만 읽어 상승지속 후보를 미등록으로 해석하는 초안 가설은 폐기했고, 실제 cumulative A01~A16과 G4 선택4/4를 분리했다. mutable workspace가 selected source와 다른 것을 확인하고 native import 경로를 선택 릴리스에 명시적으로 고정해 검토했다.

원 strict checklist748fc505는 native 보존 경로로 유지한다. 이번 변경은 이 계획과 기존 공통 계획의 포인터, 오늘 두 OPEN의 인계뿐이다. source/test·정책/원장·runtime 변경0이며 신규 모듈/실행경로0이다. 문서 link/authority·원본 보존·안정 ID의 단일 parsed owner·print-only backlog·diff 검증 후 보고한다. 코드 시험·AI 호출·장후 재생성·후속 전환/자연 수용은 계획 검증 결과로 주장하지 않는다.

10/28 우선순위 갱신은 P1/P0-C를 선행 작업,P3를 유형별 분류 연구로 명시했다. 아래§10의 별도 구현 후보·검증/부정 결과를 보존하고 완료된 wake 이식과 P2 동일 원천 전수 재실행을 현재 TODO에서 제거했다. 공통 보조 계획은 이 REGULAR owner를 가리키며 기존 두 OPEN의 Due/원 Acceptance를 유지한다. 계획 갱신 검증은 문서 링크/단일 parsed owner·authority·before/after diff이며 운영 pytest/실제 연구/후속 배포 검증을 대신하지 않는다.


## 10. 구현·연구 인계 — 2026-10-28

후속 사용자 지시로 구현을 수행한다. 최신 선택 `770b2607888f09ebd62816dc109c9955bcbc497a`/Main `3510901/start80028883`에서 격리 분기했다. 앞 절의 a55/270·계획 전용 권한 기록은 당시 이력으로 유지한다. 이번 범위는 **통합 후보 준비**이며 selector publication·hold/drain·Main 재기동·정책 활성화는 실행하지 않는다.

- **P0-A 구현:** source helper는 실제 stale/quiet/history 결손만 반환하고 매도 우세는 같은 기존 threshold의 시장 상태 helper로 분리한다. 기존 veto/override/pending/원 기한은 유지한다. 실제 WATCHING의 gate context·pipeline·trade-quality history·native preclaim capsule은 동일 `baseline_block/market_state` 의미로 결속한다. 진짜 결손은 `source_quality_block/source_quality`를 유지한다. soft gate OFF로 실제 반환하는 기존 baseline도 context-only로 잘못 표시하지 않는다.
- **P0-B 연구:** R1을 운영에 활성화하지 않는다. 누적 machine point는 원 8초 strength guard receipt를 포함하지 않아 같은 입력의 R0/R1 승패 비교를 확정할 수 없다. 기존 10:50 삼성 exact guard metrics와 최초/최종 방문은 원 bytes로 재현하되 unobservable43개를 성공/손실로 바꾸지 않는다. source28 봉인 후 원 guard·signal·quote/cost를 연결할 수 있는 행만 같은 owner에서 비교하고 추가 STOP/TIMEOUT/U를 포함한다.
- **P1 재사용:** 최신770에 physical-return same-loop wake와 Q1/Q2 opt-in 구현이 이미 포함됐다. 동일 구현을 이식하거나 새 worker를 만들지 않는다. queue/resolve/restore·쓰기 실패·native 60/120초 창과150초·5슬롯·due·물리 ACK 음성을 재검증한다. 현재 배분 `current`를 보존하며 Q1/Q2의 적격 대기는 실제 dispatch 관측만 사용한다. snapshot의 first_seen을 과거 적격 대기로 복원하지 않는다. Q3는 계속 연구 전용이다.
- **P2 재검증:** 기존 10/27 sealed report·압축 비교표·공통 store를 읽기 전용으로 재사용했다. 일반 저가 REGULAR/SOR의 unique native points29,403개와 선택/추가 후보의 metric을 원 표와 대조했다. G4 4/4, G4+A01 94/429(U427), G4+A02 930/3,994(U1,604), G4+A14 36/125(U128)로 현 승률을 개선하지 않아 membership은 그대로다. 동일 종목/일자/SOR의30분 중첩 제거 진단도 각각2/2·33/132·140/407·17/49이며 raw 선택 metric을 바꾸지 않는다. source28 미봉인·미구독 상승을 WIN으로 보간하지 않는다.
- **저장·비용:** 비교표 약0.95MiB·공통 point pack약26.65MiB·필요 snapshot약8.19MiB만 읽었다. 원장 복제0·AI/증권사 호출0·정책 재발행0이다. 새 상시 module/queue/worker/validator0, 기존 native 인계 profile과 독립 준비 reader만 현재 전체 dependency generation으로 확장한다.
- **RFHIC:** 공유 handler의 BUY 진단 함수5개 이외 함수/클래스·module statement가 최신 parent와 동일하다. SELL/보유·원장·수량·manual/퇴역 경계, native custody·원5초/별도1,200ms·quote/BBO·계좌/주문 안전은 변경하지 않는다.

[구현 리뷰·검증과 잔여 수용](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-preclaim-implementation-20261028), [봉인 비교 재검증](../../tmp/regular-preclaim-implementation-20261028/cumulative-comparison-revalidation-v2.json), [원 입력/48경계·함수 범위·국소 시간](../../tmp/regular-preclaim-implementation-20261028/source-scope-and-gate-equivalence.json).

준비된 후보의 commit·path·native parity/후보 P5·소비자 inventory는 같은 리뷰에 이어 기록한다. 정책 선택과 실제 PID·자연 진입/제출·경제성은 별도 상태다. 기존 두 OPEN과13:30~14:00 REGULAR, source28 장후,10/29 PRE/REGULAR 창은 유지하며 미래 자동 실행/배포 예약으로 바꾸지 않는다.


12:25 이후 통합 기준 갱신: RFHIC 별도 owner가12:21:24에 `d0790117a3b224edde4c1b8e3809417299726d7d`를 선택했고 Main `3661403/start80241527`의 정책 소비 영수증을12:25에 발행했다. 준비 직전 재검증에서 이를 발견해770 기준 후보 생성은 실행 전 중단했다. 기존 검증 commit `feaee0623`를 보존하고 d079 위에 BUY 역할 변경만 재적용했다. 최신 partial SELL의 원 BUY lineage 보존 코드와 전체 기존 profile은 유지하고, 새 profile은 `REVIEWED_BUY_LINEAGE_PROFILE`을 상속한다. 충돌한 native 인계·독립 준비 reader와 최신 RFHIC 회귀를 다시 검증하며, 원 정책/원장/actor 전환은 이 작업에서 실행하지 않는다.


최종 후보 준비 완료: `9be6a91a7a35d84198671414ad1f3c6f261f75ad`, `/home/ubuntu/KORStockScan-runtime-releases/regular-preclaim-20261028-9be6a91a7`. 원 source27 trailing 보고서는 공유 handler 전체 code contract 변경으로 후보에서만 currentness가 무효였으므로 기존 native source-reuse/admission/disk/checkpoint owner로 파생 결과를 재검증했다. 512MiB 첫 배치2289파일/536,832,462bytes 봉인 뒤147,579,922bytes를 재개해 총2901파일/684,412,384bytes를 검증했고20,824scope의 새 native currentness를 발행했다. 원 EOD·holding 보고서·초기 정책/경제성 null·선택 actor는 보존했다. capability4개 registry 외 별도 `main_trailing_all_scope_research.CODE_PATHS`와 실제 report-currentness의 trailing/수량 dispatch를 소비자 inventory에 추가해 같은43개를 후보/후속 검사에 사용한다. 새 wrapper/validator/상시 원장·limit 완화는 없다.

delay/stop/holding/active-policy/report 계약 PASS, native 확인128scope/76,800행/569신호 mismatch0, 정확 generation rising118·holding145 network-denied fixture PASS, 최신 RFHIC24회귀·통합 profile115 PASS다. 초기 source/가드/큐/정책1030 PASS+작업본 .venv 경로를 보완한 해당1시험 PASS, holding/custody1224 PASS+baseline 실제 반환 의미를 바로잡은1시험 PASS, 독립 준비1041 PASS·native startup flow255 PASS를 보존했다. 격리 P5는12:54:33 PASS/finding0,12consumer(holding_prompt parent_only 포함), 보호 원천 불변·provider/주문/실제 후보PID0이다. 검증은 코드/후보 readiness이며 R1·Q1/Q2/Q3/추가 패턴의 운영 효과·자연 수용은 미확정이다. [최종 인계·필요 증빙·재검증 조건](../../tmp/regular-preclaim-implementation-20261028/HANDOFF.md). 실제 selected는d0790117a/3661403/start80241527 그대로이고 이번 배포/재기동은 실행하지 않았다.


<a id="regular-delivery-aux-implementation-20261028"></a>
## 11. 후속 구현·리뷰·누적 보조 연구 — 2026-10-28

최신d079 기준 격리 commit `7022d9972`에 기존 P0-A/만료 수리를 통합하고 final-freeze의 중복 canonical 검증과 runtime Q1/Q2 dispatch 연결을 보완했다. 필수 source·기존 시장 veto·원 기한·5슬롯/체류/due와 RFHIC SELL·custody는 유지한다. native 비교128scope/76,800행/569신호 일치·대상 회귀4,846건 통과다. 국소 검증 비용 감소는 실제 late claim 해소/운영 AI 도달로 간주하지 않는다. Q1/Q2/R1 선택과 실제 successor 수용은 기존 OPEN이다.

누적 REGULAR5,118점에서 미확정2,968점을 분리하고 실제 감시·원 가격유형을 대사했다. 추가192회·exact105재사용으로 개발·미사용 날짜9cluster·A/미선택51점 회귀를 수행했다. 중복 제거 selected native53점의 N25승리/14실패 PASS→P26/14였지만 A 복원4점 중 P가3점을 잃었다. 비상시 미선택은 저가2/2→3/3, 중가3/1→3/0, 고가3/3→3/4다. 입력 I/IP는 실패 PASS가 늘었고 P도 복원·유형별 실패 보존을 충족하지 않아 **운영 채택0**이다. 새 날짜 평가는 상시 scope만 있으며 이를 비상시의 검증으로 확대하지 않는다.

[구현·검증·유형별 연구 및 교체/제거](../../tmp/regular-delivery-aux-implementation-20261028/RESULT.md), [같은 owner의 리뷰](../audits/main-regular-nonfixed-opportunity-and-auxiliary-adequacy-review-2026-10-27.md#regular-delivery-aux-implementation-20261028). 최종 native 인계·파생 report/currentness·격리 P5(12consumer/finding0)까지 PASS를 같은 결과 artifact에서 확인했다. 선택본d079/PID3661403은 유지하며 배포·재기동 승인을 기다린다.
