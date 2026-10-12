# Main 신호 수명·입력·비상시감시 준비 점검 — 2026-10-12

## 1. 결정과 조사 범위

**기계판정과 보조 PASS는 실제 발생한다. 추가 보완은 신호 종료 원인의 보존, 짧은 유효 신호의 전달, 비상시감시의 준비·관측구간 배정에 필요하다.** 정책 조건을 완화해야 한다는 결론은 이번 원천으로 입증되지 않았다.

조사 시작 시 선택 릴리스는 `deployment-detector-20261012-v1`, commit `e13ffcfb49fe8c1b9f003b77c85b31b771ee3b5c`, Main PID `981118` / start ticks `3253591`, 실제 cwd는 해당 release의 `src`다. 14:33:15 기동 영수증과 14:33:48의 기계정책 128경로 소비를 확인했다. 검토한 runtime performance·native v6·registered state·source diagnostics·Main handler/loop·WS·AI engine 8개 파일의 workspace/release 바이트가 일치한다.

점검 중 별도 승인 배포가 진행됐다. **14:59:23 재확인 시 최신은 `auxiliary-consumption-attestation-20261012-v1` / `800c1d091f149809ddd6e6da2a7bf6da0f651848` / PID `1020707`**이며 14:54:08 기동, 기계·보조 소비와 128경로를 확인했다. 위 주요 소비/탐지 코드 7개는 조사 PID 릴리스와 동일 바이트다. 새 PID의 14:59:45 성능 표본은 선택 native 신호 0·준비 실패 0이다. 아래 34개/4 attempt/121 probe 수는 이전 조사 PID의 증거이며 새 PID 누적이라고 표시하지 않는다.

Main 정확 판정 모집단은 14:38:05~14:38:29의 네 attempt다. 비상시감시 모집단은 **14:33:30~14:52:48의 같은 PID 탐색 claim/result**이며, 다른 PID·하루 누적 queue 상태와 합치지 않는다. 원 raw JSONL의 해당 시간 구간만 약 64MiB streaming으로 읽고 `producer_pid`와 physical lease/code/claim count로 중복을 제거했다. 전체 일일 원문·장후 보고서 재생성이나 provider/broker 호출은 수행하지 않았다.

이번 요청은 점검과 보완 필요사항 도출이다. 코드·정책·guard·프로세스·WS/API 요청을 변경하지 않았다. 후속 수정에는 기존 관련 owner의 리뷰·검증·실행 권한이 필요하며 완료된 과거 작업을 원인 없이 재실행하지 않는다.

## 2. Main 판정과 신호 수명

| attempt | 기계/보조 결과 | Main 처리 | 직접 입증된 원인 |
|---|---|---|---|
| `aims-9695ea7e635b1469a30b` | ENTER_NOW / 실제 AI PASS | `reversal_signal_path_changed` 거절 | worker 완료는 원 신호 후 4.559초, Main 거절은 약 4.648초. 원 5초는 남아 있음. 최종 native 상세 predicate는 보존되지 않음 |
| `aims-df10ce27c226e8de47c0` | 계산 전 계약 무효 / provider 미호출 | 같은 native 사유 거절 | 신호 나이 .847초. source/epoch/scope 정상, FIRST turn·ready membership만 소멸. 가격 253,500→253,000으로 원 저점 재방문 |
| `aims-3b636444741b146dbd02` | ENTER_NOW / provider 전 신호 무효 | 같은 native 사유 거절 | 기계 캡처는 원 신호 후 .657초. 이후 provider 직전과 Main에서 신호 수명이 끝남 |
| `aims-a5b52eb286163533d7f0` | RECHECK / provider 미호출 | 결과 소비 후 `first_ai_wait` | 가격·체결/tape 3,253.47ms로 3,000ms 한도 초과, BBO는 335.13ms로 fresh |

ENTER 두 건은 주성 `036930|REGULAR|GE_100000|SOR`, 같은 `legacy_dd5_0_8_vol_up_v1`의 FIRST_UPTICK 패턴이다. 다른 상시감시 종목에서 이 조사 시점의 정상 캡처는 확인되지 않았다. RECHECK를 AI PASS나 실행 승인으로 세지 않는다. 실제 주문 API 전송은 0이다.

### 2.1 “claim 전 만료”는 실제 native 종료 원인을 뜻하지 않는다

performance의 선택 backend 관측 34개는 claimed 4 / `expired_before_claim` 30으로 표시됐다. 그러나 [현재 집계](../../src/engine/monitoring/runtime_performance.py)는 **claim 표시가 없고 현재 시각이 event epoch+5초를 넘으면** 이 상태로 계산한다. 원래 ready가 언제·왜 제거됐는지를 검사하지 않는다. 따라서 30개 모두가 Main 지연 때문에 놓친 기회라고 해석할 수 없다.

[native state](../../src/engine/scalping/reversal_registered_runtime.py)는 FIRST-only turn이 끝나거나 바뀌면 ready에서 제거한다. [원 가격 상태](../../src/engine/scalping/continuous_reversal.py)는 하락 tick에서 `turn=None`으로 전환한다. 실제 계산 전 무효 사례는 .85초 안에 저점을 다시 방문했으며, 5초가 지나서 생긴 종료가 아니다.

필요한 보완은 source-only 사건 보존이다. 선택 ready의 최초 생성→Main 점검→claim 또는 native 제거→최종 상태를 원 event/branch/scope/PID로 연결한다. 실제 timeout, turn 종료/교체, source/epoch 불량, 이미 claim됨, consumer 미도달, 용량/우선순위 대기를 구분한다. 현재의 시간 경과 집계는 관측값으로 유지하고 종료 원인이 없으면 unknown으로 남긴다. 새 레이블이 주문 권한이나 정책 gate가 되지 않게 한다.

### 2.2 Main 최종 native 영수증 유실

[검증 adapter](../../src/engine/scalping/reversal_source_diagnostics.py)의 `validate_claim_with_receipt`는 예외에 `reversal_source_receipt`를 붙인다. 하지만 [Main 완료 처리](../../src/engine/sniper_state_handlers.py)는 예외를 잡고 `str(exc)`만 저장한다. 따라서 PASS 뒤 거절은 source invalid, BBO 불량, epoch 교체, ready 소멸 등을 같은 `reversal_signal_path_changed`로 볼 수밖에 없다.

기계/보조 전 단계에 이미 존재하는 상세 영수증을 Main 최종 검증에도 같은 attempt로 보존하는 보완이 필요하다. 원 native lock 안에서 얻은 predicate·시각·source/epoch/scope와 receipt hash/참조를 기존 작은 disposition writer에 연결한다. 현재 stock의 새 claim을 덧붙이지 않으며 진단 저장 실패가 주문 재실행·새 veto로 바뀌지 않아야 한다. 원 native guard와 등록 해시 검증은 유지한다.

### 2.3 실제 지연과 원천 노후화

4개 claim 중 한 건의 native→claim은 최대 2.596초였다. 이 RECHECK의 원 0B는 14:38:25.857660, dispatch는 14:38:28.475013, 최종 input freeze는 14:38:29.111130이다. 새 BBO는 들어왔으나 같은 route의 체결 자료는 더 오래된 상태다. 이 한 사례로 WS 수신 장애나 API 실패를 단정할 수 없다.

Main에는 async completion wakeup과 비상시 ENTER inbox wakeup이 있다. 반면 fixed-watch native-ready의 `_CHANGE` 알림은 probe의 `wait_observation`에서 사용하며 Main의 completion wait에 직접 연결되어 있지 않다. native-ready에 대해 기존 Main wakeup을 연결할 여지가 있다. 등록된 유효 branch hit만 coalesce하고 WS callback에서는 알림만 수행해야 한다. holding/exit·COMMIT·계좌/주문 우선순위, 기존 worker/cap·원 5초, exact item/epoch를 유지한다. 실제 claim 지연의 sleep·동기 작업·policy 준비·source gate 기여를 구분한 뒤 적용 효과를 판단한다.

이미 최종 exact WS refresh는 구현돼 있다. 필요한 추가 검증은 0B/0D의 원 provider 시각·수신·callback·native ingest·Main 읽기 sequence 연결과 같은 lease 구간의 quiet-tape 증거다. 새 0B가 없는데 시각만 갱신하거나 fresh 0D를 fresh 체결로 취급하지 않는다. 실제 지연/미수신이 확인된 경로만 기존 bounded recovery로 다룬다.

PASS 한 건의 provider transport는 1.427초, `response_validate`는 .721초다. worker의 `ai_response_sec=3.607초`는 기계/입력 구성·provider·반환 처리를 포함하는 다른 범위다. .721초 전부를 특정 원장 함수 비용으로 단정하지 않는다. 정상 진입 자료의 준비 .809초, 캡처 append 최대 .183초, 응답 검증/기록/lock과 Main 전달을 하위 시계로 측정해 중복 비용을 줄일 필요가 있다. 첫 자연 응답 비용과 steady-state를 분리한다.

## 3. 비상시감시 — 기계 계산 전 고갈

같은 조사 PID `981118`에서 고유 탐색 예약 126건, 고유 종료 결과 121건, 해당 as-of 진행 중 5건이다. completed 기계 `ENTER_NOW/RECHECK/BLOCK`은 모두 0이며, 비상시 Main의 보조 AI/주문까지 전달된 시도도 확인되지 않았다. 다음은 native 탐색 결과이며 정상 기계 BLOCK 건수로 변환하지 않는다.

| 종료 결과 | 건수 | 해석 |
|---|---:|---|
| `runtime_dependency_missing` | 5 | 기동 직후 필수 객체/인증 준비 미완료. 정책 자체가 없는 것으로 확정할 수 없음 |
| `route_snapshot_missing` | 21 | 정확 route의 0B/0D가 모두 미관측 |
| `0B_missing` | 22 | 0D는 관측됐으나 0B는 미관측 |
| `0B_age_exceeded` | 19 | 첫 0B/0D는 수신됐으나 이후 필요한 체결 freshness 미충족 |
| `pre_tick_0B_age_exceeded` | 4 | 다음 준비 경계에서 체결이 노후화 |
| `native_observation_residence_exhausted` — 정상 패턴 부재 | 40 | native receipt의 해당 활성 branch가 모두 FALSE |
| 같은 residence 종료 — window/feature 미완료 | 10 | native receipt에 UNKNOWN이 존재하며 평가 입력 부족 |
| 합계 | **121** | lease 단위 종료; 같은 종목의 별도 재탐색은 서로 다른 시도 |

### 3.1 수신자 준비와 실제 의존성 준비의 차이

14:33:44에 5개 worker가 `runtime_dependency_missing`으로 끝났다. [scanner](../../src/scanners/zero_base_discovery_runtime.py)의 `consumer_ready`는 EventBus subscriber 존재만 확인한다. [실제 probe](../../src/engine/scalping/zero_base_probe.py)는 WS_MANAGER·AI_ENGINE·token을 추가로 요구한다. 어떤 의존성이 빠졌는지는 현재 결과에 남아 있지 않다.

보완은 callback 존재와 실제 준비를 함께 확인하는 동일 owner의 readiness receipt다. 준비 전 예약을 실제 실행으로 소비하지 않게 하되 정책 부재·API 실패로 기록하지 않는다. 비밀값을 남기지 않고 token 존재/환경, WS 객체·연결/epoch, 기계 소비자 준비 여부만 기록한다. 준비 실패·지연과 미전송이 입증된 예약의 기존 해제 계약을 유지하며, 다른 거래 경로나 실제 전송 uncertain 예약을 풀지 않는다.

이 5건은 기동 비용/경합 사례로 분리하고 steady-state 실패율에 섞지 않는다. 현재 마지막 dispatch의 consumer ready는 true, no-consumer와 timeout 계수는 0, 진행 중은 5다. 과거의 수신자 없는 영구 슬롯 고착이 현재 재발했다고 판단할 증거는 없다.

### 3.2 관측기간이 패턴의 필요 구간보다 짧은 배정

UNKNOWN 10건 중 9건은 `G1=FALSE`, `manual_path_dca327a873720e53=UNKNOWN`이다. 해당 [등록 정의](../../src/engine/scalping/reversal_path_catalog.py)는 60초 return 관측과 known FALSE→TRUE 전환, 1초 hold를 요구한다. 종료 시 실제 연속 관측은 **18.56~58.64초**여서 이 요건을 충족하지 못했다. 나머지 1건은 G4 UNKNOWN, 46.20초 관측이다.

[queue 배정](../../src/scanners/zero_base_discovery_queue.py)은 기존 5개 슬롯 중 긴 슬롯을 최대 2개·150초, 나머지를 60초로 배정하며 시간은 예약부터 시작한다. 첫 0B 지연·준비와 source segment reset이 이 시간을 소비한다. 새 수집 구간에서 60초 feature와 1초 hold가 필요한 후보에 60초 전체 residence를 배정하면 판단까지 못 가는 구조가 생긴다.

필요한 보완은 활성 branch별 실제 history/feature readiness와 기존 60/150초 슬롯 배정을 연결하는 것이다. 150초 슬롯을 준비 시간이 필요한 유형에 배정하고 source 지연·segment reset·first data·feature ready·남은 residence를 기록한다. 슬롯 수·연결·호출·전체 예산을 늘리거나 unknown을 FALSE/기계 BLOCK으로 바꾸지 않는다. 재사용할 이력은 같은 원천·route·epoch·검증된 연속 구간만 허용하고 제거된 수집 구간을 이어붙이지 않는다. 최소 feature/hold·원 native 5초 조건은 유지한다.

FALSE 40건은 이 window 결손과 다르다. 실제 선택 branch에서 관측한 정상 불일치다. 기존 감시기의 `_probe_verified_no_match`로 원 50개 residence 종료행을 읽기 전용 재검증한 결과도 **40개 검증 성공**이다. PID/start·route/item·epoch/시각·scope/family hash 형식·exact 0B/0D·FALSE/ready 0 계약을 그대로 적용했다. 여러 branch 중 일부 UNKNOWN인 10건을 정상 패턴 부재로 회복 처리하지 않는다.

### 3.3 0B 결손은 quiet와 수신 장애를 대조해야 한다

0B 미수신 22건 모두 0D는 들어왔다. 0B 노후화 19건 모두 최초 0B/0D는 들어왔다. 같은 시점에 충분한 거래가 있었다는 독립 원천 없이 이를 WS/API 결함으로 단정할 수 없다. route snapshot 자체가 없는 21건은 REG 완료·lease/epoch·first packet·REMOVE·snapshot publish의 첫 단절을 추가로 확인해야 한다.

각 실패 lease의 원 REG/first-data/현재 sequence와 기존 raw journal 및 quiet-tape evidence를 연결하는 진단 보완이 필요하다. 실현 가능한 native 신호가 관측된 뒤에만 기계 입력/본 평가로 진행하는 기존 probe→Main 인계는 보존한다. API·retry·동시성 확대나 체결시각 보충으로 입력 부족을 숨기지 않는다.

정상 FALSE 40건은 원천 커버리지에는 기여할 수 있어도 기계 계산·ENTER/PASS/승률의 분모가 아니다. 종료 이유를 native no-match와 incomplete로 바로 읽을 수 있는 결과 projection은 유용하지만 기존 source/policy/guard를 바꾸는 새 실행 상태를 만들지 않는다.

## 4. 보완 우선순위와 종료 검증

| 우선 | 대상·소유 코드 | 보완 | 종료 검증 |
|---|---|---|---|
| P0 | performance + native source diagnostics | 미claim의 실제 제거/대기/시간 종료 원인 보존 | observed ready가 claimed / 원 native 종료 / timeout / pending / unobservable로 보존되고 미래 추정이 원인을 덮지 않음 |
| P0 | Main 최종 native validation·disposition | `reversal_source_receipt`를 exact attempt에 연결 | PASS 뒤 path 변경의 source/quote/epoch/ready predicate와 원 시각/해시 보존, 중복 실행·guard 변경 0 |
| P0 | scanner/probe readiness | subscriber와 WS/기계/인증 준비를 함께 확인 | 객체 미준비 동안 미전송 예약 소모 0, 실제 송신/cleanup·재기동 uncertain 보호 |
| P1 | nonfixed queue residence·native feature readiness | 현재 60/150초 슬롯을 실제 branch 필요 이력과 연결 | 60초+hold 후보의 판단 불가능 배정 재현/해소, 같은 슬롯/예산·feature/5초 guard 보존 |
| P1 | fixed-watch ready→Main | 기존 wakeup에 유효 native ready 전달, 반복 준비 비용 축소 | same event의 전달/claim 지연 감소, busy loop·중복 claim·holding/exit 지연 증가 0 |
| P1 | 0B/0D source lifecycle | quiet·REG/source miss·source 지연의 lease별 증거 연결 | missing/stale 이유를 입증하고 fresh quote를 fresh 체결로 대체하지 않음 |
| P1 | AI/기록 처리 경계 | .721초 응답 후처리·기계 준비·append 하위 시간 분해 | 동일 원 source/body 저장·검증을 유지하며 source→기계→AI→Main 전체 시간이 감소 |
| 연구 | 등록 FIRST/확인형 패턴 | 누적 원천에서 패턴 유효 수명·정당한 되돌림·확인형 후보의 소비 가능 기회 비교 | 기존 outcome/cost/선택 계약으로 평가; live validity guard를 먼저 완화하지 않음 |

실제 구현은 기존 module owner와 관련 체크리스트의 후속 작업으로 진행한다. source-only 계측 수리와 signal scheduling 변경, pattern 정의 변경/수동연구를 각각 검토해야 한다. 완료된 정렬·관측 큐·배포 복구를 통째로 재실행하거나 이번 점검만으로 매매·정책 변경 권한을 만들지 않는다.

회귀는 native 제거 전후/clock boundary·동시 ready/claim·MAIN 처리 중 원 receipt·미준비 의존성·단기/장기 슬롯·partial history·source quiet/packet gap·callback/cleanup의 기존 테스트를 확장한다. fake clock/transport와 같은 입력으로 확인하며 자연 테스트를 위해 provider/broker 호출을 추가하지 않는다. 실제 적용은 리뷰/검증→기존 승인 handoff→PID→자연 결과의 별도 증빙으로 닫는다.

## 5. 증거와 검증 경계

- [기존 정확 Main PID 점검](../../tmp/main-machine-status-20261012-pid981118/summary.json): 4개 판정·원 deadline·Main disposition·실제 물리 전송.
- [이번 exact pipeline 상세](../../tmp/main-machine-followup-review-20261012-pid981118/exact-attempt-pipeline-details.json): 당시 고정 offset의 해당 4개 attempt만 읽음.
- [이번 비상시감시 census](../../tmp/main-machine-followup-review-20261012-pid981118/nonfixed-probe-census.json): producer PID·원 inode/offset·126 claim/121 terminal·50 native receipt와 UNKNOWN 사례.
- [후속 최신 PID 표본](../../tmp/main-machine-followup-review-20261012-pid981118/latest-successor-snapshot.json): 새 PID의 표본은 이전 PID 분석 수와 분리.
- [선행 전달 수리](machine-auxiliary-signal-delivery-review-2026-10-12.md), [선행 정상 FALSE 커버리지 수리](route-coverage-source-review-2026-10-12.md): 완료 근거와 현재 새 발견을 구분함.
- [상시·비상시 상세 보완계획](../proposals/main-fixed-nonfixed-signal-readiness-and-latency-remediation-plan-2026-10-12.md): 기존 Main 신호 계획과 결속한 구현 순서·readiness/관측 배정·원천 진단·표적 회귀·자연 수용 기준. 계획 수립은 코드 구현·배포 완료가 아니다.

로컬 문서 링크·owner/authority·print-only parser 19항목·공백을 검증했다. 기존 정상 FALSE validator의 재검증은 source-only 읽기이며 코드 구현 시험·거래 실행이 아니다. 코드 수정을 수행하지 않아 trading pytest/compile·기계/보조 정책 재생성·배포/재기동·외부 sync는 수행하지 않았다. 조사한 4개 Main attempt·121개 probe terminal은 수익성/승률·전체 시장 기회 분모가 아니다. 과거 미보존 native 종료 시각을 현재 상태로 채우지 않는다.
