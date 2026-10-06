# 018880 사전 경제성 관측 시간 오류와 제출 경로 점검

## 범위와 운영 상태

- 제출병목 알림의 원천·제출 경로 점검 및 관측 생산자의 제한된 결함 수정이다. 계좌·주문 API 호출, 환경 변경, 배포·재기동은 실행하지 않았다.
- 작업본 HEAD: `167e0e84216c0cbb17ee4264b99b530c0983c0b5`. 직전 원천 갱신·진입 증거 해시 보완 작업본을 보존한다.
- 점검 시 Main PID `3956345`의 cwd는 `/home/ubuntu/KORStockScan-runtime-releases/next-session-ready-20261005-e16ac48b/src`이다. 선택된 `widget-retired-20261006-b53a3835` 및 현재 작업본의 수정 코드 소비를 의미하지 않는다.
- 증거는 기존 trace와 sentinel 캐시의 최대 16 MiB tail로 조회했다. 활성 대용량 payload/pipeline 원천 전체를 다시 읽거나 과거 기록을 수정하지 않았다.

## 1. 해당 시도의 직접 증거

| 항목 | 증거 |
|---|---|
| 종목 / attempt | `018880` / `aims-51219f75460d41308211` |
| promotion | `ZBPROM-018880-1791251221493-5` |
| scope / machine bundle | `KRX / KRX_REGULAR` / `bd76748c22aaf913af104996be3073664ef355f24c3e6291c47f28e107aedabe` |
| machine observation | `7a5b8ab0ee3381e846dfb0520f56b388a73e6debcc2401b6102b61bdfb631f09` |
| 기계 action | `ENTER_NOW` |
| 자금 증빙 | `2026-10-06T10:47:27.727+09:00`, `kt00011_return_code=0`, `kt00011_error=""`, cash contract `valid`, 현금 주문가능 수량 `1858`, 요청 종목 `018880`, 요청 단가 `3985` |
| 자금 원천 hash / 재사용 | `53d967d6d10fb444c550ce6e322c7a3a1693f955f497be05f40444200fd18bd7`, `exact_receipt_reused`, 기존 유효기간 `2.0 sec` |
| 사전 관측 guard | `ALLOW_NORMAL`, `SAFE`, quote age 약 `235.912 ms`, quote stale=false |
| 경제성 생산자 | `10:47:29.711910`, `entry_ai_economic_source_gap`, `'NoneType' object has no attribute 'isoformat'`, capacity blocker 없음 |
| 최종 판정 trace | `10:47:33.737277+09:00`, `analyze_target:018880:1791251249734:7029c668`, provider_called=true, action `WAIT`, `entry_setup_evidence_sha256_invalid`, `entry_setup_machine_auxiliary_compact_semantic_rejected` |
| 종료 event | `10:47:36.311626`, `ai_confirmed_terminal_no_budget`, terminal reason `first_ai_wait_big_bite_not_confirmed`, source stage `first_ai_wait`, action `WAIT`, actual_order_submitted=false, broker_order_forbidden=true |

원천: [해당 날짜 판정 trace](../../data/ai_decision_trace/ai_decision_trace_2026-10-06.jsonl), [sentinel 이벤트 캐시](../../data/runtime/sentinel_event_cache/buy_funnel_sentinel_events_2026-10-06.jsonl), [제출병목 보고서](../../data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json).

`ai_confirmed_terminal_no_budget`는 이 사건에서 현금 부족이나 broker 주문 거절을 뜻하지 않는다. 위 terminal reason과 자금 증빙을 함께 해석해야 한다. 기계 ENTER_NOW 이후 해시 계약 오류로 WAIT가 되어 주문 제출 없이 종료된 시도다.

## 2. 서로 다른 두 결함

### 관측 생산자의 optional clock 직렬화

`sniper_state_handlers._observe_entry_economics_before_ai`는 `apply_entry_split_order_policy(..., observation_only=True)`에 `now`를 생략한다. 후자의 probe 관측 분기는 `now.isoformat()`을 실행하여 `now=None`이면 예외가 발생했다.

- 실제 PID 환경에 probe enabled=true / active date `DAILY`가 있다.
- 수정 전 작업본과 실제 PID 릴리스의 해당 allocator 함수 SHA-256은 모두 `57d94ba85cc62458bc3fbd13e69a099bd236c5dc7f5774d4fa44e662875fd723`이었다.
- 격리된 정상 정책 fixture로 시간 생략 시 같은 AttributeError를 재현했다. 명시 시간을 전달한 경우는 통과했다. fixture의 과거 날짜는 직렬화 회귀검증용이며 정책 튜닝·승격의 입력이 아니다.
- 수정: 관측 호출에서 시간이 생략되면 KST 시간을 한 번 확정해 정책 날짜 검사와 관측 receipt에 사용한다. live reservation 호출의 시간 처리는 변경하지 않는다.

### ENTER_NOW 소비자의 증거 해시 오류

해당 trace의 `entry_setup_evidence_sha256_invalid`는 직전 작업에서 확인한 mutable selection receipt 공유 결함과 같은 오류다. [직전 보완 기록](main-machine-source-refresh-and-admission-hash-remediation-2026-10-06.md)의 deepcopy 수정 및 거부 trace 보완은 작업본에 있으며 현재 PID에는 아직 반영되지 않았다. 이번 알림을 새 기계 패턴 실패나 자금 API 실패로 분류하지 않는다.

## 3. 수정 후에도 남는 재생 경계

시간 오류 수정 후 probe 관측은 조건부 계약을 남기고 `unsupported_pre_ai_probe_reservation_scope`를 반환한다. 사전 관측에는 실제 probe 체결가격과 그 가격에 종속된 잔여 주문가격이 아직 없다. 따라서 `owner_replay_status=unsupported_unknown_fill_anchored_prices`를 보존한다.

- 주문 목록은 비어 있고 live bundle을 예약하지 않는다.
- `reservation_performed=false`, `runtime_effect=false`, `order_authority_forbidden=true`를 유지한다.
- 진입 수량·probe 1주·조건부 잔여 수량·continuation·정상 관측 시각 및 계약 hash를 보존한다.
- 경제성 자료를 성공·수익 0·유효 replay로 바꾸지 않는다. 시간 예외의 제거는 전체 probe 경제성 재생 지원의 완료가 아니다.

## 4. 리뷰와 검증

- 수정 전 회귀: 시간 생략 1건 실패, 명시 시간 1건 통과. 실패 지점은 allocator의 `now.isoformat()`이다.
- 수정 후 회귀: 두 시간 경로와 기존 실제 예약·체결 기준 잔여계약 테스트, 3건 통과.
- 재리뷰: 관측 분기만 시간 확정, 명시 시계 보존, 날짜 경계의 동일 시계 사용, live 예약 미호출, stock 불변, 미확정 체결가격 미생성, 계약 hash 일치를 확인했다.
- 관련 allocator / atomic sizing / bottleneck consumer 3개 module 회귀: **406 passed**, `pandas_ta`의 기존 pandas 옵션 deprecation warning 1건.
- 수정 Python compile, Ruff `E9,F63,F7,F82`, `git diff --check`, 로컬 문서 링크 4개 및 print-only backlog parser: 통과.
- 확인된 변경 범위의 미해결 코드 결함 없음. 앞선 원천 갱신·해시 보완은 별도 검증 기록을 유지하며 이번 검사 건수와 합산하지 않는다.
- 전체 활성 원천 재스캔, 정책 재생성, 실제 API 테스트, 배포·재기동, external Project/Calendar sync는 실행하지 않았다. 자연 원천·운영 소비·경제성 수용은 코드 검증과 별도다.

## 5. 후속 종료 조건

운영 반영 후 새 attempt에서 시간 예외가 사라지고, 해시 계약을 통과한 기계 action과 screen 결과가 같은 identity로 기록되어야 한다. probe의 미지원 경제성 재생은 별도 상태로 남아야 한다. 실제 주문 제출·체결·종료·비용 수익은 각각 직접 receipt가 있어야 판단할 수 있다.
