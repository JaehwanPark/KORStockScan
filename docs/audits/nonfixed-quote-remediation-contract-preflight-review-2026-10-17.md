# 비상시 호가 보완 전 식별자·필드 계약 사전점검 — 2026-10-17

## 1. 결정과 범위

사용자의 요청에 따라 [호가 시간정책·기회 전달 보완계획](../proposals/nonfixed-quote-freshness-and-opportunity-delivery-remediation-plan-2026-10-17.md)을 구현하기 전에 변수·필드·정책 식별자·대소문자·타입·단위와 생산자→소비자 연결을 점검했다. 이 문서는 사전점검과 구현 시 주의할 계약을 소유한다. 생산 코드·환경값·정책·구독·주문·provider·배포·재기동은 변경하지 않았다.

기준은 선택 릴리스 `postclose-complete-20261017-7f2552aed`, commit `7f2552aedde8fec6ef904a43105827907e50dfc8`, bundle `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`다. selector의 `actual_pid_consumed=false`를 유지했고 다음 운영일은 10/19다. 실제 PID 적용 검증이 아니다. 10/17 체크리스트는 없어 과거·미래 OPEN 항목을 오늘의 실행 권한으로 대체하지 않았다.

## 2. 먼저 보완할 설정 키 불일치

선택 코드에서 다음 차이를 확인했다.

| 생산/소비 위치 | 실제 조회 이름 | 의미 |
|---|---|---|
| `src/utils/constants.py:2157` | `KORSTOCKSCAN_SCALP_PRE_AI_MAX_WS_AGE_SEC` | 기본 pre-AI 원천 시간 설정 |
| `sniper_state_handlers.py:15852` | `SCALP_PRE_AI_MAX_WS_AGE_SEC` | stale backoff 회복 검사에 전달하는 이름 |
| 같은 파일 `_env_float:13058` | 전달한 이름 그대로 `os.getenv(name)` | 접두사를 자동 추가하지 않음 |

기본값이 모두 3초인 경우에는 차이가 드러나지 않는다. 정식 prefixed 설정을 변경하면 기본 판단과 backoff 해제 판단이 다른 값을 사용할 수 있다. 현재 환경값을 조회하거나 변경하지 않았으므로 실제 운영 발생 빈도·제출 영향은 미확정이다. 이 차이를 최종 주문 stale guard의 실제 우회 증거로 해석하지 않는다.

후속 수정은 기존 정식 설정 owner의 이름·기본값·단위·clamp를 회복 판단에서도 일관되게 읽는 것이다. 짧은 이름을 새로운 설정 alias로 확대하지 않는다. 기본값·정식 override·잘못된 값·두 이름이 동시에 있는 경우를 순수 회귀로 확인하고 조건별 시간정책 비교 전에 이 차이를 제거한다.

## 3. 구현 시 잘못 연결하기 쉬운 이름과 의미

| 항목 | 확인한 실제 계약 | 구현에 반영할 내용 |
|---|---|---|
| helper 인자와 env 이름 | `_env_or_rule_int("SCALPING_ENTRY_SUBMIT_REVALIDATION_MAX_QUOTE_AGE_MS", …)`는 `KORSTOCKSCAN_`를 추가함 | 짧은 helper 인자를 실제 env 이름으로 복사하지 않음 |
| 주문 소유권 객체 | `OwnerOrderContext` 필드는 `owner_type`, `owner_id`, `position_id`, `client_intent_id` 네 개 | 없는 `action` 필드를 읽지 않음 |
| 최초 진입의 논리 역할 | 일반 helper 인자는 `ENTRY_BUY`; 초기 분할 leg0의 intent는 `initial_quantity:…:leg0` 형식 | intent 문자열에 `ENTRY_BUY`가 있는지로 최초 진입을 판별하지 않음 |
| 공통 주문 표면 | Main owner는 `main_scalping`, side는 `BUY`, registry action은 `NEW`, API는 `kt10000` | 이 값들만으로 최초 진입·후속 leg·재가격·잔여·AVG_DOWN을 구분하지 않음 |
| 분할주문 기한 | 첫 leg와 leg1 이후는 다른 생명주기; 후속은 원 bundle slot·주문 시작 시각·최대 1,200초 | 최초 신호의 5초 기한을 후속 분할주문에 자동 상속하지 않음 |
| quote라는 이름의 telemetry | `quote_age_at_submit_ms`는 `_get_ws_snapshot_age_sec`의 `last_ws_update_ts` 기반 | canonical 호가 나이로 재사용하지 않고 기존 `ws_quote_source_receipt`·`ws_quote_receive_age_ms`를 사용 |
| canonical quote receipt | 타입 key는 `source_type`; `observed_epoch`는 초 | `realtime_type` key가 있다고 추측하거나 ms로 해석하지 않음 |
| 보조판정 필드 | status는 소문자 `pass`, effective verdict는 대문자 `PASS`, screen pass는 실제 bool | 표시 문자열·raw alias·persisted effective verdict를 혼용하지 않음 |
| 최소 제출 lineage | `submit_attempt_machine_lineage()`는 제한된 telemetry allowlist | 전체 assessment·AI trace·quote가 있다고 가정하지 않고 Main 실행 owner의 원 provenance에서 명시 조립 |
| depth 수량 | 보존 depth tick의 `ask_levels[].quantity`와 snapshot의 `orderbook.asks[].volume`은 다른 schema | 같은 이름으로 일괄 변경하지 않고 현재 소비자 변환을 유지 |
| source 시각 | `received_at_ms`는 ms, `observed_epoch`는 초, `observed_at`은 ISO 문자열 | 알려진 owner 변환만 사용; 결손을 현재 시각·0으로 대체하지 않음 |
| 0D clock owner | live depth `received_at_ms`는 builder의 로컬 생성 시각, snapshot `observed_epoch`는 그 값/1,000; `packet_received_epoch`는 별도 | 실제 최초 실패 이후 packet 수신은 생성 시각만으로 입증하지 않고 item/epoch/type sequence가 같은 packet 시각과 결속 |
| 진단 시간 | `latest_0b_ms` 등은 등록 시각부터의 offset; `source_clocks.0B.age_ms`는 원천 나이 | offset을 epoch나 age로 사용하지 않음 |
| 연결 세대 | `transport_epoch`는 양의 정수 식별자 | timestamp처럼 나누거나 반올림하지 않음 |
| 순번 | `route_sequence`는 exact item 및 0B/0D별 독립 counter | 0B 순번과 0D 순번의 크기를 한 stream처럼 비교하지 않음 |

순수 fixture에서는 **transport 나이 100ms와 canonical 호가 나이 5,000ms가 동시에 존재**하는 상황을 재현했다. 이는 두 필드가 동의어가 아님을 보여준다. 기존 경로에는 별도의 canonical/latency 검사가 있으므로 실제 stale 주문 발생을 입증한 결과가 아니다.

새 전송 guard의 operation context는 **새 계약**이다. 기존 소유권 객체에 이미 존재한다고 가정하지 않는다. 일반 최초 진입·새 bundle leg0의 첫 전송과 같은 intent의 허용된 auth retry에서 명시 생성·전달한다. `ENTRY_REPRICE_BUY`, `ENTRY_RESIDUAL_BUY`, `SCALE_IN_BUY`, 후속 leg·재개는 각 기존 owner의 기한을 유지한다. SELL·CANCEL·조회·대사에도 자동 전파하지 않는다.

## 4. 정책·시장·대소문자 계약

- 데이터/정책 `assessment.route`·native event의 `venue`, WS `market_route`, broker `dmst_stex_tp`는 역할이 다르다. 예를 들어 데이터는 `SOR`/`009150_AL`이고 broker 선택은 `NXT`인 저장 사례가 있다. 기존 route resolver와 원천 증빙을 따라 검증하며 문자열 직접 동등 비교를 추가하지 않는다.
- WS `0B`·`0D`와 `_AL`·`_NX`는 해당 원천 형식을 사용한다. raw item은 수신 문자열을 보존하고 normalized tick item은 canonical 대문자다. 정상 지원 item에서 실제 case 결함은 확인되지 않았다.
- 정책 schema·backend discriminator와 branch의 실제 ID는 해당 loader가 소유한다. opaque ID·hash·owner 문자열을 일괄 대문자화하지 않는다. 지원되는 session alias는 기존 정규화 함수로 검증하고 데이터 route를 session alias로 사용하지 않는다.
- schema가 v6여도 지원되는 호환 경로의 discriminator가 `operating_v5`일 수 있다. 이름을 v6로 일괄 교체하지 않는다. `UNION`의 `primary_branch=None`도 정상인 경우가 있다. 현재 backend/version의 validator가 보장하는 필드만 요구한다.
- 같은 짧은 해시 필드명도 전체 경로로 구분한다. v6 assessment의 `machine_component_sha256`와 capture의 `runtime_consumption.continuous_reversal.machine_component_sha256`는 계산 owner가 다르다. 신규 context는 bundle·scope execution·aux identity를 각 소유 경로에 결속하고 이름이 같다는 이유로 해시 동등 검사를 추가하지 않는다.

선택 bundle의 native bundle/family validator와 실제 bundle digest는 통과했다. 48 cells·128 scopes·57 definitions·172 memberships의 실제 ID 목록은 [정책 검증 영수증](../../tmp/nonfixed-contract-preflight-20261017/policy/policy-validation.json)에 고정했다. 정책 재선정·source handoff의 새 승인·실제 적용은 수행하지 않았다. 실제 `source_anchor`·`source_path`를 release root 및 `release/src` CWD에서 실행하여 같은 current policy 경로를 반환하는 것도 확인했다. 이는 전체 원천 해시 검증과 별개다.

## 5. 구현 기준 코드와 검증

현재 작업본과 선택 릴리스의 모듈 구성이 다르다. 원천 16개 파일 표본은 동일6·차이10이고 차이에는 작업본에 없는 `native_source_continuity.py`가 포함된다. 정책 측 별도 표본 49개 중 차이21개는 내용 차이17개와 부재4개다. 없는 것은 `reversal_cumulative_catalog.py`, `reversal_cumulative_postclose.py`, `reversal_cumulative_registration.py`, `reversal_cumulative_runtime.py`다. 두 표본 수를 전체 유일 파일 수로 합산하지 않는다. 이는 동시 작업의 결함 판정이 아니며, 미커밋 변경을 선택 릴리스로 덮어쓰지 않는다.

후속 수정은 선택 커밋과 필수 모듈을 갖춘 격리 작업본을 기준으로 한다. 의도한 동시 변경을 통합할 때도 각 계약 검증을 다시 수행한다. 현재 작업본의 문법 통과만으로 선택본의 loader·정책 호환을 입증하지 않는다.

- 선택 생산 코드 25개: 문법 compile 및 Ruff `F821/F822` 통과, 미정의 이름 발견0.
- 핵심 기존 symbol 17개: AST로 존재·실제 함수 인자·소유권 객체 네 필드를 확인했다. runtime import 없이 수행했다.
- 원천 생산자→소비자 21개 계약 경계: 타입·nullable·단위·시계·대소문자와 실제 소비 필드 대조.
- 원천 기존 표적 테스트 31개 PASS. 정책/route/case 47개·설정/경로 13개의 순수 fixture 60개 PASS, 주문 전달 순수 fixture 17개 PASS. 서로 다른 검사를 유일 pytest 수로 합산하지 않는다.
- 문서 링크·권한·공백·print-only parser를 최종 검증한다. provider·broker·구독 호출, 원천 재스캔, 전체 연구 재생, runtime 기동 검증은 실행하지 않았다.

## 6. 후속 구현 완료 조건

1. 선택 기준과 일치하는 격리 코드에서 설정 키 불일치를 수정하고 같은 값을 소비하는 회귀가 통과한다.
2. 기존 source-wait 경합과 0D 알림 누락을 수정하되 exact item·개별 원천 시각·순번·원 신호 기한을 유지한다.
3. 새 quote-only 회복과 전송 context의 신규 필드는 명시된 버전 계약·생산자·소비자·nullable·단위를 갖추고 기존 필드를 추측해 사용하지 않는다.
4. 일반 최초 진입·leg0·후속 leg·재가격·잔여·AVG_DOWN·SELL·CANCEL 각각의 기존 생명주기를 구분한다.
5. schema/case/route/clock·결손·경합 회귀를 다시 검토한 뒤 시간정책 후보를 비교한다. 이번 점검을 새 시간상한 선정·주문 성공·경제성 검증으로 사용하지 않는다.

세부 증거: [원천 계약](../../tmp/nonfixed-contract-preflight-20261017/source/review.md), [정책·설정 계약](../../tmp/nonfixed-contract-preflight-20261017/policy/review.md), [주문 전달 계약](../../tmp/nonfixed-contract-preflight-20261017/handoff/contracts.md), [17개 symbol 계약](../../tmp/nonfixed-contract-preflight-20261017/symbol-contracts.json), [정적 검사](../../tmp/nonfixed-contract-preflight-20261017/static-validation.json).
