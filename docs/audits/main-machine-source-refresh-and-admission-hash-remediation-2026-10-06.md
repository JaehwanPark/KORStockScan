# Main 기계판정 원천 갱신·진입 증거 해시 결함 보완

## 범위와 상태

- 사용자 지시: 확인된 결함 보완, 삼성전자 및 비삼성 기계판정 원천 결손 보완.
- 작업본 기준 HEAD: `167e0e84216c0cbb17ee4264b99b530c0983c0b5`.
- 코드 구현·리뷰·회귀검증 완료. 운영 배포·재기동·실주문·정책 재생성은 이번 작업에서 실행하지 않았다.
- 2026-10-06 11:06 KST 재확인: Main PID `3956345`의 cwd는 `/home/ubuntu/KORStockScan-runtime-releases/next-session-ready-20261005-e16ac48b/src`.
- 선택 릴리스는 `widget-retired-20261006-b53a3835`, selector의 `actual_pid_consumed=false`. 이번 작업본을 해당 PID가 소비했다는 증거는 없다.
- 삼성전자/비삼성 정책 분리, 기존 source freshness·conflict·전송 세대·기한·주문·수량·broker·기존 완료 판정 cooldown 계약을 유지한다.

## 1. 직접 확인한 결함과 변경

| 결함 | 직접 근거 | 변경과 검증 |
|---|---|---|
| 경로별 가격을 읽기 전에 aggregate 가격 부재로 갱신 종료 | 삼성전자 10:21~10:40의 `entry_machine_input_ws_snapshot_refresh_reason=latest_price_missing`. 기존 helper는 `latest.curr` 검증 뒤에만 prepared route를 선택했다. | 준비된 candle route의 `0B/0D`를 먼저 선택한다. 등록 item의 로컬 저장소도 읽는다. aggregate `curr=0`이지만 exact route 가격·호가·체결이 있는 상황을 재현하여 갱신 성공을 확인했다. |
| 계산 전 원천 무효도 정상 평가 대기시간으로 기록 | WATCHING 완료 분기가 모든 결과에 `LAST_AI_CALL_TIMES`를 갱신했다. | 캡처·정책·attempt 증빙이 있는 계산 전 원천/필수값 결손에만 별도 대기를 둔다. 새 exact `0B`와 신선한 같은 경로 `0D`가 확인되면 새 기계판정을 계산한다. 정상 RECHECK/BLOCK, provider 실행 결과는 기존 완료 시계와 cooldown을 사용한다. |
| 비삼성 후보의 해시 확정 후 선택 기록 변형 | 현대차 `005380`, attempt `aims-4155722bfad4374e5ca9`, observation `3fb4a42c7cca5b28ed7ee25efed41dec2640fe878f0e993147f5754e8667cac2`: 기계 ENTER_NOW 후 `entry_setup_evidence_sha256_invalid`로 screen adapter 거부. | `entry_strategy_policy.rebuild`의 `rebuilt.strategy_selection`과 변경 가능한 assessment receipt의 객체 공유를 제거했다. admission recipe가 선택 policy SHA를 갱신하거나 micro receipt를 추가해도 원천 증거 해시가 바뀌지 않는다. |
| adapter 거부 결과에서 기계판정 경로 누락 | 위 현대차 trace의 machine ENTER_NOW 캡처와 최종 `entry_screen` trace 사이에 `entry_mechanistic_action`/screen 상태가 누락됐다. | 유효한 setup의 adapter 거부에도 기계 action·정책 해시를 보존한다. 거부 응답은 `response_invalid`, PASS=false, 기존 fail-closed action을 유지한다. setup 자체가 손상된 경우 새 유효 판정을 만들지 않는다. |
| 원천 시계·재평가 부모 증빙이 trace에서 누락 | 엔진 결과에는 preflight 시계가 있지만 final trace 허용 필드에 없었다. | exact `0B/0D` provenance·source timing을 trace와 ENTRY_PIPELINE에 보존하고, 재평가 부모 observation SHA/attempt를 새 캡처와 결과에 연결한다. |

### 해시 결함의 재현 결과

동일한 비삼성 `pullback_p60_v0` 후보와 입력으로 실제 생성기/consumer 함수들을 사용한 격리 회귀검증이다. 실제 주문이나 broker 수익 검증은 아니다.

| 항목 | 수정 전 | 수정 후 |
|---|---|---|
| 기계 action | `ENTER_NOW` | `ENTER_NOW` |
| setup validator | `entry_setup_evidence_sha256_invalid` | 오류 없음 |
| assessment와 setup의 선택 기록 객체 공유 | true | false |
| 후보의 effective setup을 compact adapter에 전달 | 해시 결함으로 거부 가능 | 정상 PASS 응답 처리 통과 |

이 결함은 기계 신호를 변경해야 하는 근거가 아니라, 이미 생성된 신호가 다음 소비자에서 잘못 거부되는 코드 결함이다. 과거 파일을 수정하거나 과거 실패를 성공으로 바꾸지 않았다.

## 2. 원천 재평가의 유한 경계

소유 모듈은 `src/engine/scalping/entry_machine_source_recovery.py`이다. Main live entry의 로컬 원천 선택/재계산 일정이므로 scalping package에 배치한다. provider 호출, WS 등록/해지, REST 조회, 주문 제출은 이 모듈의 권한이 아니다. engine root에 새 모듈을 추가하지 않는다.

1. `provider_called=false`, `machine_evaluation_expected=true`, `machine_capture_status=captured`, 계산 전 source/required-feature 상태와 유효 observation/policy SHA, attempt, 같은 종목·경로 증빙이 모두 있어야 대기를 생성한다.
2. 기존 완료 평가 시계를 덮어쓰지 않는다. 기존 완료 판정/provider cooldown이 남아 있으면 새 원천이 있어도 이를 우회하지 않는다.
3. 같은 watch/promotion 세대에서 기존 source age 계약을 만족하는 새 `0B`와 신선한 `0D`만 재계산을 연다. `0D`만 갱신, 과거 provider 체결 시계, 미래 시계, 다른 item/route/epoch, 불완전 증빙은 대기한다.
4. 대기 중 추가 REST/AI 준비와 주문 경로에 진입하지 않는다. 과거 BUY가 캐시에 남아 있어도 entry branch를 종료한다. 준비·캡처·정책 로더·canonical preflight·기계판정·필요시 screen·최종 주문 guard 전체가 새 attempt에서 실행된다. 과거 ENTER_NOW를 재사용하지 않는다.
5. 대기 기한은 기존 `AI_WATCHING_COOLDOWN` 길이에 묶고, 같은 기한 안에서 새 원천에 의한 추가 계산은 1회다. 재실패가 기한을 연장하거나 매 체결마다 계산을 반복하지 않는다. 만료/세대 변경/손상 시 기존 정상 평가 경로로 돌아간다.
6. 비동기 계산은 기존 in-flight key를 유지하고, 다음 작업 key는 source parent SHA를 포함한다. 기존 deadline·generation·main-thread commit guard를 유지한다.

## 3. 실제 원천 결손과 정상 패턴 미충족

- 하이브 `352820`, attempt `aims-185578b961fe6229a500`: 09:57:53.782 입력에서 `0B` 수신 09:57:49.235853, age 약 `4546 ms`; `0D` age 약 `207 ms`; source skew 약 `4339 ms`. 기존 `3000 ms` 계약을 넘은 원천이다. `_AL`은 native exchange 증명이 아니며, fresh integrated execution-view proof가 필요하다. 새 원천 없이 이를 유효하게 만들지 않는다.
- 삼성전자 quote-clock conflict/aggregate price 부재는 로컬 경로 선택 및 동일 cutoff 재검증으로 보완한다. 실제로 오래된 체결·호가는 그대로 원천 무효다.
- 비삼성의 provider 체결 지연/필수값 부족도 새 수신 시계만으로 유효한 체결로 바꾸지 않는다. 현재 provider 체결 시계가 있는 같은 경로 입력으로 재평가한다.
- 정상 source로 계산된 삼성전자 `local_breakout_confirmation_required`/미시 가격 반응 부족 RECHECK는 source failure와 별도다. 이번 수정은 돌파·가격 반응을 만들어내거나 정책 통과 조건을 낮추지 않는다.
- 과거 11건/3건의 결손이 복구됐거나 진입·체결·수익이 개선됐다는 실운영 결론은 아직 없다. 운영 반영 후 새 attempt의 직접 증거가 필요하다.

## 4. 공식 Kiwoom 확인

- upstream: [Kiwoom-Securities/Kiwoom-REST-API](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)
- commit: `953e5dbff123f437ab4d11a78a95191a685eb51f`
- retrieval: `2026-10-06T01:40:24.070836+00:00` (`10:40:24 KST`)
- inspected: `kiwoom/specs.py`, `kiwoom/core/ws_client.py`, `kiwoom/realtime/packets.py`, `events.py`, `decoders.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`.
- 현재 tree에 `kiwoom_docs`는 없다. packaged spec의 `0B/0D`, item/type, `10/15/20`, `21/41/51/61/71`, WebSocket `/api/dostk/websocket`, LOGIN/REG/REMOVE packet을 교차 확인했다. `20/21`은 HHmmss; `9081`의 native venue mapping은 정의하지 않는다.
- 실/모의 분리, continuation, API error/limit, reconnect/resubscribe 및 주문 프로토콜은 변경 대상이 아니다. 새 API 요청·FID parser·REG/REMOVE는 추가하지 않는다.
- 공식 확인과 bounded 조사 파일은 ignored `tmp/machine-source-remediation-20261006/`에 있다. 주문/account/provider API를 테스트 목적으로 호출하지 않았다.

## 5. 리뷰와 검증

### 리뷰 반복

- 1차: 경로 선택을 price 검사 앞으로 이동. 기존 epoch 오류 코드 회귀를 발견해 기존 `prepared_entry_route_partition_epoch_invalid`를 복구했다.
- 2차: immutable evidence와 mutable selection receipt의 alias를 실제 후보 생성기로 재현하고 분리했다. 정책·기계 action은 동일하며 setup hash와 compact consumer가 정상화됐다.
- 3차: 완료 판정/provider cooldown, 새로운 체결 필요 조건, retry budget, expiry, 손상된 대기 상태, 비동기 cache pinning, 부모 trace 보존, 첫 평가 대기 중 REST/AI 미호출을 점검했다. 기한 만료 후 manager read 오류로 영구 대기하지 않도록 보완했다.
- 4차: 원천 대기 중 과거 BUY를 재사용할 가능성을 차단하고 실제 WATCHING handler에서 WAIT/BUY 캐시 모두 entry branch 종료를 확인했다. 한편 동일 handler 파일의 미호출 private helper와 항상 None인 fallback branch에 기존 undefined name 2개가 남아 있어 해당 죽은 코드만 제거했다. 퇴역 probe/fallback을 복원하지 않는다.
- 재리뷰 결과: 확인된 범위의 미해결 코드 결함 없음. 운영 반영과 자연 원천/주문 결과 검증은 별도 상태다.

### 최종 검사

- 관련 8개 test module: **574 passed**.
- WATCHING 실제 handler의 완료 판정 reuse/source 대기 및 관련 비동기 회귀: **4 passed**, 해당 대형 module에서 관련 없는 **910 deselected**.
- 수정 Python compile, Ruff `E9,F63,F7,F82`, `git diff --check`, 문서 print-only backlog parser: 통과.
- broad automation, 비싼 장후 재생성, 실 계좌/주문 API, 배포·재기동, external Project/Calendar sync는 실행하지 않았다.

## 6. 후속 운영 종료 조건

| 소유 경로 | 남은 증거 | 종료 조건 |
|---|---|---|
| release/실제 Main consumer | 사용자 승인 범위의 배포 및 PID receipt | 신규 코드 release와 실제 소비 경로 일치 |
| Main machine input refresh | 새 삼성/비삼성 attempt의 시계·item·route·epoch·preflight | 유효한 새 원천의 정상 계산, 실제 stale/미증명 입력의 차단 유지 |
| admission/compact consumer | 같은 attempt의 immutable setup, assessment, screen trace | 해시 오류 없이 기계 action 보존; 거부·VETO는 exposure 불허 |
| source recovery | 부모/자식 SHA, 시간, generation, retry budget | 새 체결에 의한 유한 재평가와 완료 판정 cooldown 보존 |
| submit/fill/economics | 실제 submit, fill, terminal 및 비용 증거 | 각 단계의 직접 증거로 따로 판단. 위 코드 검증만으로 성과를 확정하지 않음 |
