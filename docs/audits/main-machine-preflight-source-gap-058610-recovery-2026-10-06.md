# 058610 판정 원천결손: 보호용 preflight 계약 복구

## 1. 범위와 판정

- 사용자 요청의 exact-route 원천 점검 및 기존 제한된 source-only 보완이다. 기계·보조 정책, freshness/route conflict, broker·주문·수량·cap·cooldown·hard safety를 변경하지 않았다.
- 실제 Main PID `4071430`, root `/home/ubuntu/KORStockScan-runtime-releases/machine-source-recovery-20261006-1667abb9/src`를 직접 확인했다. selector나 unit 설정만으로 PID 소비를 추정하지 않았다.
- 최초 원인은 체결 희소/API 실패가 아니라 **현재 PID가 pin한 보호용 baseline 계약 파일의 삭제**다. archive의 동일 원본을 복원했고 같은 PID의 자연 기계 계산 재개를 확인했다.
- 원인·판정 ID 유실에 대한 계측 코드도 보완·리뷰·검증했다. 이 추가 코드의 배포/PID 소비는 대기 상태다. 이번 원천 복원에는 재기동·env/policy 수정·REST/WS/provider 호출·주문 실행이 없었다.

## 2. 058610 exact 판정 증거

| 항목 | 직접 증거 |
|---|---|
| 종목 / 발생 | 에스피지 `058610`, `2026-10-06T12:00:19.368785+09:00` |
| 판정 trace | `aidt-fa9d0f05c1c6498dba82f02e07e3d4e1` |
| evaluation attempt | `machine-source-invalid-385ff98f37fe4f2da646b57081f3f11f` |
| snapshot / observation | `aims-fcedcf50511486f10b0c` / `f7992cce2f7877af73a9571ac631c25a3c5bd14a61af0b8fa559e88177c126f6` |
| scope | market-data `krx_nxt_integrated`, item `058610_AL`, transport epoch `1`; broker route `SOR`, 판정 scope `KRX / krx_regular` |
| bundle | `bd76748c22aaf913af104996be3073664ef355f24c3e6291c47f28e107aedabe` |
| 0B 수신 | `12:00:18.897422`, age `426.963 ms`, route sequence `16` |
| 0D 수신 | `12:00:18.899000`, age `425.385 ms`, route sequence `31` |
| probe warmup | 최초 준비 때 exact 0B 10개·0D 24개, 계산 직전 0B 16개·0D 31개, signed 0B 16개, WS tick source `ws_exact_route` / `trusted_pressure` |
| candle / account | candle age `19,324 ms`로 기존 90초 계약 내, 공유 account/order snapshot age `36,622 ms`로 기존 60초 계약 내 |
| 실제 최초 차단 | `input_blockers=[runtime_preflight_artifact_not_ready]`, `machine_evaluation_status=source_quality_blocked_before_assessment` |
| 실행 여부 | `provider_called=false`, `actual_order_submitted=false`, `broker_order_forbidden=true` |

기계 계산 전 차단 trace의 `DROP`을 계산된 기계 BLOCK이나 보조 AI VETO로 세지 않는다. program/investor missing도 기록돼 있지만 이 판정의 실제 blocker는 baseline artifact다. `_AL` 수신은 underlying event가 KRX에서 발생했다는 증명이 아니며, 해당 venue를 새로 추정하거나 SOR route를 변경하지 않았다.

원천: [당일 판정 trace](../../data/ai_decision_trace/ai_decision_trace_2026-10-06.jsonl), [당일 pipeline](../../data/pipeline_events/pipeline_events_2026-10-06.jsonl). pipeline은 16MiB 단위로 최대 두 블록을 읽어 claim/result를 찾았고 활성 파일 전체를 재스캔하지 않았다. 알림의 “1건”은 degraded route issue 수이며 주문 수·원천 실패 평가 수가 아니다.

## 3. 삭제 원인과 원본 복구

현재 PID의 보호 계약 pin:

- mode=`baseline_v1`
- date=`2026-07-23`
- SHA-256=`27e607109fc1dbf4120b9d86c161b2e0773cc38ca58b6a712662bf06d91b8343`
- owner artifact: [ai_input_quality_baseline_2026-07-23.json](../../data/report/ai_input_quality_baseline/ai_input_quality_baseline_2026-07-23.json)

11:59:20 종료된 pre-August 정리의 [삭제 journal](../../tmp/pre-august-data-cleanup-20261006/deleted.jsonl)에 같은 path/SHA/size가 있다. 첫 동일 blocker trace는 `042700`의 `11:59:30.034430`이다. 삭제 조사에는 literal 파일 경로 참조가 반영됐지만, **환경의 date/hash에서 로더가 계산하는 파일 의존성**이 보호 집합에서 누락됐다. 완료 당시 Main 정책/bootstrap 검사 PASS는 이 보호용 preflight 입력의 존재를 증명하지 않았다.

이 7월 파일은 현재 사용 중인 버전 고정 보호 계약이다. 7월 가격자료로 기계 정책을 재학습하거나 과거 source date를 오늘로 바꾸는 작업이 아니다. `_baseline_artifact_contract_ready`가 보호 계약의 role/authority 필드를 검증하며 `can_open_order_authority=false`, `can_relax_threshold=false`, `can_change_provider=false`를 요구한다.

복구:

1. `/home/ubuntu/KORStockScan-storage-archives/pre-august-data-20261006/data-through-2026-07-31.tar.zst`의 해당 member 하나를 별도 경로로 추출했다. 전체 파일을 운영 경로로 복원하지 않았다.
2. 검증된 archive manifest의 크기 `45,269 bytes`, member SHA, PID pin SHA/날짜, payload 보호 계약을 모두 확인했다. archive 전체 무결성 검증은 정리 당시의 immutable verification을 참조하며 이번에는 추출 member를 직접 다시 검증했다.
3. baseline contract 회귀 4 PASS 후 원본 bytes와 manifest의 원래 mtime `1784811634519081329 ns`를 복원했다. 새 정책을 발행한 뒤 시각을 과거로 위장한 것이 아니라 동일한 역사 원본 metadata를 복구한 것이다.
4. `2026-10-06T12:22:57.771062+09:00` 복원, native 로더 `ready_baseline_v1`, 동일 SHA/날짜와 protective-only role을 확인했다. target 기존 파일 부재·symlink 부재와 PID/root/pin 재확인 후 원자적으로 게시했다.
5. [날짜별 복구 receipt](../../data/runtime/source_contract_recovery/ai_input_baseline_restoration_2026-10-06.json)와 [현재 의존성 receipt](../../data/runtime/source_contract_recovery/ai_input_baseline/current.json)를 남겼다. 기존 정리 도구의 `references()`가 해당 baseline을 보호 대상으로 찾는 것을 직접 검증했다. current receipt는 다음 날짜에도 조회되는 참조이며 successor pin/consumer 확인 전 보존한다.

과거 삭제 journal·archive manifest를 덮어쓰지 않았다. 관련 없는 Git 삭제 10개 및 직전 probe 재생 계획 작업본도 유지했다. 과거 원천결손 판정 058610을 성공으로 재라벨링하지 않는다.

## 4. 계측 생산자→소비자 결함 보완

| 경로 | 확인한 결함 | 작업본 보완 |
|---|---|---|
| `zero_base_probe.run_zero_base_probe` | 계산 전 실패에서는 실제 attempt/capture/bundle과 preflight primary blocker가 probe result로 전달되지 않았다. | 모든 machine receipt의 identity/capture/bundle을 보존. source-invalid primary 또는 required-feature blocker를 진단 사유로 전달. 기존 result/reason/action·retry·등록/해지 동작은 유지 |
| `scalping_scanner` result writer | 원천결손 probe에 exact evaluation ID와 artifact status가 없었다. | 동일 producer attempt·계산 상태·preflight artifact 상태를 원본 receipt에 연결 |
| `ai_decision_trace` | 엔진이 생성한 artifact 상태가 trace allowlist에서 빠졌다. | 기존 `ai_input_runtime_preflight_artifact_status` 보존 |
| `submission_bottleneck_monitor` | nested probe attempt를 읽지 않아 대표 알림에 판정 ID가 없었다. | native probe의 exact attempt를 원인 예시에 전달. malformed ID를 새 유효 ID로 만들지 않음 |

계측 변경은 Kiwoom 요청·응답 parser/FID/REG/REMOVE/reconnect를 변경하지 않는다. 원천 갱신·수신 프로토콜, 재시도 예산, 완료 판정 cooldown 또는 필수값 계약을 수정하지 않았다.

## 5. 자연 소비와 남은 상태

- `11:47:53` 재기동부터 원본 복원 전까지 판정 trace **83건 모두** `runtime_preflight_artifact_not_ready`였다. 판정/trace 수이며 실주문 실패 83건이 아니다.
- 복원 후 bounded pipeline 확인에서 probe result **69건 = assessed 13 + source_unavailable 55 + required_feature_insufficient 1**을 확인했다. 이 값은 해당 snapshot 범위이며 전체 당일 통계가 아니다.
- 정상 재개 예: `056190` 12:27:21 BLOCK, observation `b5a22992fb9739945728b8af6cf7feda8cd359c81e72da3ce970bcd49e47611d`; `145170` 12:27:28 RECHECK, observation `8b6b8cff36c35929429f76a46969a3722c3f481a1ba1afdacbd9f82d270f977b`; `455900` 12:28:09 RECHECK, observation `64d00e40069bfa6c12ae0185e2c90a8315d1c708b27eca74403a52000d6a9883`. 각 행의 bundle은 위와 동일하며 `actual_order_submitted=false`다.
- 복원 후 trace의 별도 결손 `323280` 12:25:09, attempt `machine-source-invalid-003968f3e89f4accb2ae4b2e57554e6d`는 `required_feature_provider_trade_late`다. artifact 결손과 분리하며 수신/체결시각 guard를 완화하지 않는다.
- 12:25 보고서에는 여전히 `coverage_degraded`가 있다. 미수신·age 초과·필수값 결손 및 최근 창의 복원 전 실패가 남아 있어 전체 경보 해제나 전 종목 원천 정상화를 주장하지 않는다.
- 058610의 새 자연 attempt는 이번 확인 범위에서 미관측이다. 기존 queue rotation의 다음 exact-route 관측으로 평가하며 과거 판정 재사용·수동 등록/강제 AI 호출을 하지 않는다.
- 조사 당시 추가 계측 코드는 작업본에서 닫혔으며 운영 release/PID 반영은 대기였다. 아래 7~9절에 후속 승인·배포 수용을 기록한다. probe 조건부 경제성 재생의 미지원 상태는 별도 계획으로 남는다.

원천/복구/자연 snapshot: [조사 증거 디렉터리](../../tmp/intraday-source-gap-058610-20261006), [복원 전후 trace 집계](../../tmp/intraday-source-gap-058610-20261006/pre-post-trace-summary.json), [자연 probe 소비](../../tmp/intraday-source-gap-058610-20261006/natural-probe-after-restoration.json), [정리 보호 참조 검증](../../tmp/intraday-source-gap-058610-20261006/restored-contract-retention-proof.json).

## 6. 리뷰·검증과 인계

- self-review→보완→재리뷰: required-feature 차단에서도 native blocker가 유실될 가능성을 추가 확인해 보완했다. 실제 판정/result/reason/action, guard, WS/REST 호출량 및 재시도·lease 수명 불변을 확인했다.
- probe/scanner runtime/trace/bottleneck 4 module 회귀 **286 PASS**. 추가 보완 후 probe **49 PASS**(앞선 probe 검사와 중복 포함), baseline protective contract **4 PASS**. 기존 pandas 옵션 deprecation warning 1개만 관측됐다.
- 실제 scanner result emitter의 exact ID/artifact 상태 전달, native blocker 보존·기존 source kind 우선·무근거 원인 미생성, trace/outcome 권한 불변, monitor example의 exact attempt를 회귀로 검증했다.
- 수정 Python compile, Ruff `E9,F63,F7,F82`, `git diff --check` PASS. 로컬 링크 27개 존재, print-only parser 23항목 및 현재 OPEN/parsed owner 1개, 복구 artifact/current dependency SHA와 같은 Main PID/root를 확인했다. 실제 policy/PID/주문/economic acceptance는 이 코드 검증의 완료 조건으로 추가하지 않는다.
- owner는 기존 `DirectFamilySourceRepairMainMechanisticEntry`에 원천 복구·계측 인계를 연결한다. 배포 완료 기록은 보존하며 이번 추가 계측의 미배포를 과거 배포 실패로 바꾸지 않는다.
- 본 조사 단계에서는 전수 계좌/주문 조회, 새 AI/provider 평가, 정책 재생성, bot/episode 재기동, broad automation 및 외부 동기화를 실행하지 않았다. 후속 사용자 승인에 따른 Main 배포·재기동은 아래에 기록한다.

## 7. 사용자 승인 후 계측 배포 gate

사용자가 `배포하고 재기동 승인`을 명시했다. 위 1~6절의 조사 시점과 구분하여 추가 계측을 Main과 선택 릴리스의 정기 monitor에 배포한다. 다른 서비스를 함께 재기동하지 않는다. 별도 Episode 설치 경로와 격리·퇴역 상태를 보존하고 release-set의 독립 pin을 검증한다.

- 최종 4 module 전체 회귀 **287 PASS**, Python compile·Ruff `E9,F63,F7,F82`·diff 검증 PASS. 리뷰 범위의 미해결 코드 결함은 없다.
- 기존 Main PID `4071430`, clean root `machine-source-recovery-20261006-1667abb9`. 당일 정책/PREOPEN 5개 SHA와 보호 baseline SHA `27e607109fc1dbf4120b9d86c161b2e0773cc38ca58b6a712662bf06d91b8343`를 동결했다.
- fresh native read-only KRX/NXT 잔고·미체결은 모두 0, 조회·정규화 계약 정상. DB의 HOLDING/BUY_ORDERED/SELL_ORDERED 0, native registry 검증 1,409개 event, 미결속 intent 0이다. 감사 helper의 최초 호출에서 per-symbol 함수의 필수 인수를 누락해 receipt 작성이 실패했고, native verified snapshot/state로 수정 후 fresh 조회·receipt를 다시 완료했다. 제품 API와 매매 코드는 변경하지 않았다.
- scoped code/test와 자체 점검·계획 문서만 commit한다. 별도 과거 데이터 삭제 10개와 두산 신규 계획 작업본은 보존한다. probe 조건부 경제성 계획의 구현은 이번 배포 범위가 아니다.
- immutable commit/root와 이전 selector rollback을 보존하고, native same-day intraday handoff 준비 뒤 표준 graceful restart를 실행한다. 원 PREOPEN·정책·보호 baseline bytes는 변경하지 않는다.
- 실제 새 singleton PID/root/commit·source cleanliness·bootstrap consumption, heartbeat·WS first-data, fresh broker/custody 및 오류를 확인한 후 아래에 완료 receipt를 기록한다. 자연 원천 품질·제출/체결·경제성은 별도다.

증거: [배포 gate 디렉터리](../../tmp/source-gap-instrumentation-deployment-20261006).

## 8. 재기동 gate에서 발견한 보호 context marker 결손

12:42의 native 기존 PID 검증은 보유 context 7개 key의 `pid_env_mismatch`로 차단됐다. 기존 bootstrap/PREOPEN bytes는 불변이었다. 같은 정리 작업이 `data/runtime/ai_multi_timeframe_context_promotion_2026-07-29.json`도 삭제해, 현재 PID가 소비한 durable context OFF overlay의 owner가 로더에서 사라진 것이 원인이다. 이 단계에서는 재기동 요청을 발행하지 않았다.

- archive 원본은 **7,170 bytes**, SHA `f5e8df9127ce9ddd3a7c61a4f10e6fd3227080cd67bef95a328c87d69685abd8`이며 immutable 정리 manifest와 일치한다.
- 별도 추출 원본을 native `authoritative_runtime_env`에 넣어 **19개 overlay key 모두 기존 PID와 동일**함을 먼저 확인했다. legacy companion manifest/env의 기존 부재 상태에서 native loader가 context OFF와 보호 baseline을 유지한다. companion 파일을 복원하거나 context를 새로 활성화하지 않았다.
- **12:45:22.961767 KST** 원본 SHA·원래 mtime `1785282982045212330ns`를 그대로 no-clobber 원자 복원했다. 기존 PID/bootstrap 재검증 **PASS / finding 0**. 현재 계약 복원이므로 과거 가격·원천 재학습을 수행하지 않는다.
- [복구 receipt](../../data/runtime/source_contract_recovery/ai_context_marker_restoration_2026-10-06.json)와 [current dependency](../../data/runtime/source_contract_recovery/ai_context_marker/current.json)를 발행했다. 기존 baseline과 marker 두 파일이 native 정리 참조 보호에 포함됨을 read-only 확인했다. 자동 삭제·정리 재실행은 하지 않았다.

직접 증거: [원래 실패](../../tmp/source-gap-instrumentation-deployment-20261006/bootstrap-before.json), [복원 전 native/PID 일치](../../tmp/source-gap-instrumentation-deployment-20261006/context-marker-restoration-review.json), [복원 후 통과](../../tmp/source-gap-instrumentation-deployment-20261006/bootstrap-before-restored.json), [정리 참조 보호 검증](../../tmp/source-gap-instrumentation-final-20261006/protected-contract-reference-proof.json).

## 9. 실제 배포·재기동과 자연 계측 최종 수용

1. 코드·점검 문서 commit `5ece2998d16ec4c1b030993dc9577b115dfc0c02`의 clean immutable root를 선택하고 native intraday handoff를 준비했다. **12:46:43** 새 Main PID `4098111`의 bootstrap/PID 검증 PASS, WS first-data 35개 및 기계 assessed 자연 계측을 확인했다.
2. 자연 probe에서 판정 전 source-unavailable 건의 빈 ID가 기존 scalar logger를 거쳐 문자열 `None`으로 저장됨을 발견했다. 추가 계측 소비자가 이를 ID로 인식하면 같은 종목·원인의 여러 실패가 부정확하게 합쳐질 수 있어 후속 보완했다. 새 scanner 3개 필드는 결손을 `-`로 표현하고 monitor는 `None/null/-/빈 문자열` 및 비문자 입력을 ID로 채택하지 않는다. exact ID가 없는 두 자연시각 event의 모수 보존도 회귀로 확인했다.
3. 후속 scanner runtime/monitor **162 PASS**, compile·Ruff·diff PASS. 앞선 287건과 겹치는 module이 있으므로 고유 건수로 합산하지 않는다. 판정/action/retry/lease·원천 guard·API/provider/주문·수량·cap·custody·operator lock 권한을 다시 확인했으며 리뷰 범위의 미해결 코드 결함은 없다.
4. 최종 코드 commit **`abb71f8d3a70f518b5ff6ea7fab9577d70d77f1c`**, release **`machine-preflight-lineage-20261006-abb71f8d`**. **12:51:20 KST** graceful restart 뒤 singleton Main PID **`4100807`**이 해당 root/commit을 소비한다. 기존 child 종료 후 tmux 감독자를 교체했으며 강제 kill·주문 테스트를 수행하지 않았다. rollback selector와 이전 두 release를 보존했다.
5. 실제 PID `source_dirty=false`, native bootstrap·intraday consumption **PASS / mismatch 0**, 원 정책/PREOPEN **5개 SHA 불변**. 보호 baseline native loader는 `ready_baseline_v1`이고, 보유 context는 기존 **OFF**, 전체 19-key overlay가 원 소비와 동일하다.
6. 재기동 전후 fresh KRX/NXT 잔고·미체결·DB 활성 custody·registry 미결속 intent **모두 0**. hash-verified registry event **1,409개**, Main child **1개**다. Main/스나이퍼/스캐너/Telegram/오류감시 heartbeat와 `ProcessHealthDetector` **PASS**.
7. **12:53:26 확인 snapshot**에서 WS first-data **44개**, 새 PID 이후 probe **22개** 중 기계 assessed **3개**를 자연 확인했다. `413630` 12:52:25 RECHECK, `247540` 12:52:38 BLOCK, `036810` 12:52:54 RECHECK이며 각 exact attempt·capture hash를 보존했다. 계산 전 건의 ID는 `-`로 기록되고 monitor가 이를 정확 ID로 취급하지 않는 것도 live 로그로 확인했다. 자연 원천 미수신·age 초과는 별도 상태로 유지하며 058610의 새 assessed 및 비용 수익 개선을 주장하지 않는다.
8. release-set **PASS**, Episode 설치 **122개 route / 366개 policy pin** 및 cron **8개** 경로 PASS. Episode의 기존 독립 root/pin, failed 29·inactive 93 및 격리를 유지했다. 웹·체결 통보 등 별도 서비스 재기동은 이번 Main 계측 배포에 포함하지 않았다.
9. 시작 후 ERROR는 기존 05:03 장후 저장소 정리 실패와 그에 따른 `postclose_finalization cleanup_failed`를 다시 알린 `cron_completion`이다. 원 실패 receipt를 유지하며 전체 장후 DONE을 주장하지 않는다. 별도 원천 age/필수값 결손과 조건부 probe 경제성 미지원도 해당 기존 owner에서 계속 관리한다.

최종 직접 증거: [배포](../../tmp/source-gap-instrumentation-final-20261006/deployment.json), [graceful restart](../../tmp/source-gap-instrumentation-final-20261006/restart.log), [실제 기동 수용](../../tmp/source-gap-instrumentation-final-20261006/runtime-acceptance.json), [새 PID 소비](../../data/runtime/policy_bootstrap/intraday_handoff/2026-10-06/abb71f8d3a70f518b5ff6ea7fab9577d70d77f1c.consumed.json), [broker 후 상태](../../tmp/source-gap-instrumentation-final-20261006/broker-after.json), [custody 후 상태](../../tmp/source-gap-instrumentation-final-20261006/local-custody-after.json), [자연 probe](../../tmp/source-gap-instrumentation-final-20261006/natural-probe-after.json), [read-only monitor](../../tmp/source-gap-instrumentation-final-20261006/source-gap-monitor-readonly-after.json).

기계·보조 정책 재생성, 조건부 경제성 재생 구현, 새 API/FID/REG/REMOVE 계약 변경, 광범위 장후 작업 및 외부 문서 동기화는 수행하지 않았다. native read-only broker helper로 재기동 수용만 확인했다. 검증 범위는 코드·배포·기동 및 새 계측 소비다.
