# KRX 애프터마켓·SOR 전환 상세 구현 설계서

작성일: 2026-09-11 KST

적용 예정일: 2026-09-14 KST

상태: **설계 완료·Spark 실행단위 반영 / 코드 미구현 / 배포·재기동·실주문 미실행**

이 문서는 2026-09-14부터 16:00~20:00에 KRX 애프터마켓이 개설되고 NXT와 함께 거래되며 SOR 주문을 지원한다는 사용자 제공 운영 전제를 기준으로, KORStockScan의 장중 주문·시세·보유/청산·위젯·스캐너와 장후 수집·튜닝·승인·최종화 전 체인을 전수 점검한 구현 설계다.

원칙 owner는 [Plan Rebase §1~§8](../plan-korStockScanPerformanceOptimization.rebase.md), 현재 실행 owner는 [2026-09-11 Stage2 체크리스트](../checklists/2026-09-11-stage2-todo-checklist.md)다. 이 문서는 독립 제안서이며 기존 OPEN 항목, live 승인, 선택 릴리스, cron/PID 또는 정책 pin을 변경하지 않는다. [장중 지시문](../intraday-monitoring-task-instructions.md)과 [장후 지시문](../postclose-tuning-result-review-task-instructions.md)은 분석 대상으로만 읽었으며 해당 절차를 실행하지 않았다.

## 1. 결론

현재 코드는 2026-09-14 운영에 대해 **NO-GO**다.

16:00~20:00을 NXT 단일시장으로 가정하는 로직이 세션 판정, 주문 라우팅, scanner 조회, 위젯, 체결 귀속, AI 품질, 장후 cohort, 승인 artifact와 DONE controller까지 이어져 있다. 단순히 주문 route의 기본값을 `NXT`에서 `SOR`로 바꾸면 다음 문제가 생긴다.

1. SOR 주문·통합시세 코드 `_AL`을 실제 체결시장으로 오인한다.
2. KRX 애프터마켓에서 허용되지 않는 주문유형을 제출하거나 broker reject 뒤에야 보정한다.
3. 15:30 KRX 정규장 미체결, 15:40 NXT 단독장, 16:00 양시장 개장 사이의 주문 lifecycle이 섞인다.
4. 장후 보고서가 KRX/NXT 애프터마켓 손익을 기존 `NXT/NXT_AFTERMARKET`으로 합쳐 잘못된 EV와 승인 후보를 만든다.
5. 기존 V2.14 NXT 승인 범위가 새 KRX+NXT 통합 세션까지 자동 확장될 수 있다.
6. postclose DONE controller의 고정 cohort 집합 때문에 올바른 신규 cohort를 거부하거나, 반대로 이전 artifact 재사용으로 변경을 놓칠 수 있다.

권고 구현은 다음 네 축을 분리하는 중앙 시장 계약을 먼저 만든 뒤, producer에서 postclose 최종 consumer까지 단계적으로 전환하는 것이다.

| 축 | 의미 | 허용 예시 |
| --- | --- | --- |
| `market_session_regime` | 시간과 시행일에 따른 시장 상태 | `KRX_REGULAR`, `NXT_AFTERMARKET_SOLO`, `KRX_NXT_AFTERMARKET`, `CLOSED` |
| `market_data_route` | 구독·조회한 시세 범위 | `krx_only`, `nxt_only`, `krx_nxt_integrated` |
| `broker_route_requested` | 주문 시 broker에 지정한 route | `KRX`, `NXT`, `SOR` |
| `actual_execution_venue` | 체결 receipt가 증명한 물리 시장 | `KRX`, `NXT`, `UNKNOWN` |

`SOR`는 실제 시장이 아니며 `_AL`도 실제 체결시장 증거가 아니다. 이 불변식을 코드·DB·보고서·승인 contract 전체에 적용해야 한다.

## 2. 확인한 외부·공식 계약과 남은 gap

### 2.1 시장 운영 전제

증권사 공지들은 2026-09-14부터 KRX 애프터마켓 16:00~20:00, NXT 애프터마켓 15:40~20:00, 16:00 이후 양시장 최선집행/SOR 제공을 안내한다.

- [카카오페이증권 거래시간 변경 안내](https://www.kakaopaysec.com/customer/notice/dynamicBoardPageDetail.do?id=7452): KRX 16:00~20:00 연속매매, 기존 정규장 미체결의 비이월, 지원 주문유형 안내.
- [KB증권 KRX 애프터마켓 안내](https://www.kbsec.com/go.able?idt=20260904&linkcd=s060901010000&seq=10010298): 양시장 거래시간, 주문조건과 VI 관련 안내.
- [삼성증권 거래시간 확대 안내](https://www.samsungpop.com/ux/kor/customer/notice/notice/noticeViewContent.do?MenuSeqNo=24420): KRX/NXT 주문 지속시간과 양시장 최선집행 안내.
- [연합뉴스 제도 보도](https://www.yna.co.kr/amp/view/AKR20260910157400008): KRX 16:00 개장, NXT 15:40 개장 및 호가시장 구조 설명.

다만 공개 [KRX 영문 거래시간 페이지](https://global.krx.co.kr/contents/GLB/06/0602/0602020204/GLB0602020204T1.jsp)는 점검 시점에 과거 16:00~18:00 단일가 설명을 유지했다. 따라서 증권사 공지를 일정 근거로 사용할 수는 있어도, 종목별 자격·정확한 주문유형 코드·VI 상태 FID를 추정해 wire contract를 바꿔서는 안 된다.

### 2.2 Kiwoom 공식 reference gate

점검 revision은 공식 [`Kiwoom-Securities/Kiwoom-REST-API`](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa) commit `234560d213acd8871ae344b5481aecd2f30287fa`, retrieval `2026-09-11T14:51:40+09:00`이다.

확인 경로:

- `kiwoom/_data/kiwoom_api_spec.json`
- `kiwoom/specs.py`
- `kiwoom/core/runtime.py`, `kiwoom/core/ws_client.py`
- `kiwoom/realtime/stream.py`
- Postman collection의 주문·계좌 production/demo envelope
- 국내주식 주문 buy/sell/modify/cancel examples — sample로만 확인

확인된 범위:

- 주문 endpoint `/api/dostk/ordr`
- 신규매수/매도/정정/취소 `api-id` `kt10000`/`kt10001`/`kt10002`/`kt10003`
- `dmst_stex_tp=KRX|NXT|SOR`
- `ka10075` 조회의 `stex_tp=0` 통합, `1` KRX, `2` NXT
- 주문 응답·미체결 정보의 `stex_tp`, `stex_tp_txt`, `sor_yn`
- 실시간 타입 `0s`에 장운영 관련 FID 215/214가 존재함

확인되지 않은 범위:

- 2026-09-14 시행 후 세션별 주문유형 code의 최종 허용표
- KRX 애프터마켓 종목 자격의 공식 machine-readable 필드
- FID 215/214의 새 양시장 상태값과 전이 의미
- SOR parent/child 주문의 시장별 상태를 어떤 식별자로 완전 결속하는지
- 정규장/애프터마켓 일봉·종가 필드 의미 변경 여부

구현 직전에 [Kiwoom API Data Contract의 Official Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 다시 수행한다. 새 공지·portal·spec·실패 없는 mock가 없으면 미확인 의미는 `UNKNOWN`으로 두고 해당 신규 주문 권한은 fail-closed한다. 기존 주문·보유 청산과 read-only reconciliation은 영향 범위만 격리한다.

## 3. 현행 동작 재현과 위험

2026-09-14 16:05 KST를 주입한 read-only probe에서 확인한 현행 결과는 다음과 같다.

```text
sniper venue                  = NXT
default_order_route           = NXT
scanner stex_tp               = 2
widget session/venue/code     = NXT_AFTERMARKET / NXT / 005930_NX
explicit SOR market order     = order type 3, pre-remapped=false
```

이는 양시장 개장 뒤에도 KRX를 조회·고려하지 않고, SOR 시장가 주문을 사전 차단/변환하지 않는다는 뜻이다. 현재 증권사 공지상 KRX 애프터마켓은 일반 시장가를 허용하지 않으므로 reject 후 재시도 방식은 주문 중복·지연·route 변경 위험이 있다.

### 3.1 핵심 결함 목록

| ID | 결함 | 영향 | 조치 |
| --- | --- | --- | --- |
| AM-01 | 16:00~20:00 `NXT` hardcode | KRX 기회 누락, 잘못된 venue | 중앙 세션 계약 도입 |
| AM-02 | 기본 주문 route가 NXT | 최선집행/SOR 미사용 | 승인된 scope에서 SOR 선택 |
| AM-03 | SOR 장후 market type 사전 remap 없음 | reject·중복 retry 위험 | submit 전 허용 주문유형 검증 |
| AM-04 | `_AL`을 장후 NXT로 귀속 | 실제시장·손익 오귀속 | `_AL => actual venue UNKNOWN` 불변식 |
| AM-05 | `NXT_AFTERMARKET` 단일 cohort | KRX/NXT 경제성 혼합 | decision scope와 fill venue 분리 |
| AM-06 | `is_nxt`만 저장 | KRX 애프터마켓 자격 부재 | 날짜별 자격 ledger 추가 |
| AM-07 | 15:30 주문 이월 상태 미모델링 | orphan·중복주문 | boundary reconciliation state machine |
| AM-08 | postclose 고정 2-cohort 검증 | 신규 cohort 차단/누락 | contract-version별 cohort validator |
| AM-09 | 기존 NXT live 승인의 자동 상속 가능 | 권한 누수 | 신규 dual cohort 기본 observe-only |
| AM-10 | cron/monitor가 19:20 종료 | 19:45 terminal exit 관찰 누락 | 필요한 owner만 19:50까지 연장 |

## 4. 목표 세션 계약

### 4.1 effective-date 기반 상태표

역사 데이터 재현성을 위해 거래일을 반드시 입력받는다. 현재 wall clock만으로 과거 행을 재분류하지 않는다.

| 거래일/시간 KST | `market_session_regime` | 개장시장 | 기본 통합 시세 route | 신규 entry 의미 |
| --- | --- | --- | --- | --- |
| `< 2026-09-14`, 기존 시간 | 기존 contract | 기존대로 | 기존대로 | 과거 결과 불변 |
| `>= 2026-09-14`, 09:00~15:30 | `KRX_REGULAR` | KRX 및 기존 NXT 정규 세션 계약 | 현행 규칙 | 현행 승인 유지 |
| 15:30~15:40 | `SESSION_TRANSITION` | 주문·종목별 상태 확인 | read/reconcile only | 신규 주문 금지 |
| 15:40~16:00 | `NXT_AFTERMARKET_SOLO` | NXT | `nxt_only` 또는 기존 승인 route | 기존 NXT 계약의 versioned 후속 |
| 16:00~19:40 | `KRX_NXT_AFTERMARKET` | KRX+NXT | `krx_nxt_integrated` | 신규 별도 승인 전 observe-only |
| 19:40~19:45 | `KRX_NXT_AFTERMARKET_CLOSE_ONLY` | KRX+NXT | 통합 + 실제시장 receipt | 신규 BUY 금지, 보유청산만 |
| 19:45~20:00 | `KRX_NXT_AFTERMARKET_TERMINAL_EXIT` | KRX+NXT | 통합 + 실제시장 receipt | 기존 terminal exit safety만 |
| 20:00 이후 | `CLOSED` | 없음 | reconciliation only | 신규 주문 금지 |

19:40/19:45는 거래소 규칙이 아니라 현재 KORStockScan의 보수적 BUY cutoff/terminal exit 정책을 보존한 값이다. 이를 시장 개장 확대를 이유로 늦추거나 완화하지 않는다.

### 4.2 순수 resolver API

새 소유 위치는 `src/trading/market`이다. `src/engine` root에는 새 Python 모듈을 만들지 않는다.

제안 파일:

- `src/trading/market/session_contract.py`
- `src/trading/market/aftermarket_eligibility.py`

핵심 타입 예시:

```python
@dataclass(frozen=True)
class MarketSessionContext:
    contract_version: str
    observed_at_kst: datetime
    trade_date: date
    session_regime: str
    open_venues: tuple[str, ...]
    decision_market_scope: str
    preferred_market_data_route: str
    entry_allowed_by_clock: bool
    exit_allowed_by_clock: bool
    source_quality: str
    blocker: str | None

@dataclass(frozen=True)
class SymbolVenueEligibility:
    trade_date: date
    stock_code: str
    krx_regular_eligible: bool | None
    nxt_eligible: bool | None
    krx_aftermarket_eligible: bool | None
    eligible_venues: tuple[str, ...]
    source_id: str
    source_sha256: str | None
    observed_at_kst: datetime | None
    quality_state: str
    blockers: tuple[str, ...]
```

필수 함수:

```python
resolve_market_session(observed_at_kst, *, contract_version=None)
resolve_symbol_venue_eligibility(stock_code, trade_date, source_snapshot)
resolve_market_data_route(session_context, eligibility, purpose)
resolve_broker_order_route(session_context, eligibility, authority, side)
validate_order_type_for_session(session_context, requested_route, side, order_type)
classify_actual_execution_venue(broker_receipt)
```

모든 함수는 timezone-aware KST 입력을 요구한다. naive datetime, 시행일 누락, malformed source는 신규 entry에서 예외를 삼키지 않고 명시 blocker를 반환한다.

### 4.3 불변식

1. `broker_route_requested=SOR`이면 `actual_execution_venue`를 채우지 않는다.
2. request code `_AL`은 `market_data_route=krx_nxt_integrated`이며 실제시장 증거가 아니다.
3. request code `_NX`만 `market_data_route=nxt_only`를 증명한다.
4. 실제 체결시장 값은 broker fill/current-order receipt의 명시 필드에서만 만든다.
5. receipt가 `sor_yn=Y`라도 실제시장 필드가 0/통합/공백이면 `UNKNOWN`을 보존한다.
6. `UNKNOWN`을 시간대로 KRX/NXT에 배분하거나 비용·손익을 0으로 보간하지 않는다.
7. 과거 `<2026-09-14` 행의 기존 세션은 새 clock으로 재작성하지 않는다.
8. 새 `KRX_NXT_AFTERMARKET` entry는 별도 승인 artifact가 없으면 주문하지 않는다.

## 5. 종목별 거래 가능 시장

### 5.1 새 날짜별 ledger

기존 `DailyStockQuote.is_nxt`는 NXT 가능 여부 한 축만 표현하며 날짜별 provenance와 KRX 애프터마켓 자격을 담지 못한다. 이를 과적재하지 않고 별도 테이블을 추가한다.

제안 테이블 `security_market_eligibility_daily`:

| 필드 | 형식 | 규칙 |
| --- | --- | --- |
| `trade_date`, `stock_code` | PK | exact date + 6자리 base code |
| `krx_regular_eligible` | nullable bool | 미확인은 `NULL` |
| `nxt_eligible` | nullable bool | `ka10099.nxtEnable` 등 검증된 원천 |
| `krx_aftermarket_eligible` | nullable bool | 새 공식 원천 확인 뒤만 기록 |
| `eligible_venues_json` | JSON | 확정된 `KRX`/`NXT`만 포함 |
| `audit_info`, `stock_state`, `order_warning`, `market_code` | raw text | 의미를 손실하지 않고 보존 |
| `source_api_id`, `source_revision` | text | API/공지/spec revision |
| `observed_at_kst` | timestamp | 실제 관측시각 |
| `payload_sha256` | text | 정규화 전 원천 또는 snapshot hash |
| `quality_state` | text | `VALID`, `PARTIAL`, `UNKNOWN`, `CONFLICT` |
| `blocked_reasons_json` | JSON | 명시적인 실패 사유 |

구현 위치:

- model/migration: [models.py](../../src/database/models.py), [db_manager.py](../../src/database/db_manager.py)
- producer 확장: [kiwoom_utils.py](../../src/utils/kiwoom_utils.py)의 `get_stock_eligibility_map_ka10099`
- EOD producer: [update_kospi.py](../../src/utils/update_kospi.py)

`ka10099`의 `nxtEnable`, `auditInfo`, `state`, `orderWarning`, `marketCode` raw 값을 누락 없이 저장한다. `nxtEnable`을 KRX 애프터마켓 자격으로 재사용하지 않는다. 공식 KRX 애프터마켓 자격 필드가 확인되지 않으면 `krx_aftermarket_eligible=NULL`로 두며, pure KRX route 신규진입은 차단한다. SOR의 처리 가능성을 곧 실제시장 자격 증명으로 간주하지 않는다.

### 5.2 source failure 처리

- 개별 종목 누락: 해당 종목·해당 route만 차단.
- page/continuation 불완전: 완전성을 증명하지 못한 snapshot 전체를 신규 entry 입력으로 금지.
- 서로 다른 공식 원천 충돌: raw provenance 보존, `CONFLICT`, 주문 권한 없음.
- 이전 영업일 cache: 분석 참고만 가능, 오늘 신규 entry 권한 없음.
- broker reject: 사후 evidence이며 사전 자격 원천의 대체물이 아님.
- 보유 청산: 자격 결손으로 보유를 방치하지 않고, 기존 hard safety와 broker가 허용하는 검증된 route로 bounded reconciliation/청산을 계속한다.

## 6. 주문·보유 lifecycle 설계

### 6.1 주문 route 선택

`src/engine/kiwoom_orders.py`의 현재 “KRX 정규장이 아니면 NXT” 기본값을 제거한다.

목표 우선순위:

1. 호출 owner가 명시한 검증된 route.
2. exact-date 승인 artifact가 허용한 `SOR`.
3. 보유/원주문 reconciliation에서 증명된 원 route.
4. 그 외 신규 entry는 `order_route_authority_missing`으로 차단.

시장 확대만으로 모든 장후 주문을 SOR로 바꾸지 않는다. NXT-only 종목/owner는 NXT를 유지할 수 있고, 새 dual-market entry는 별도 승인 뒤 SOR를 사용한다. KRX-only route도 검증된 자격과 승인 없이는 선택하지 않는다.

### 6.2 주문유형 preflight

현재 `_nxt_market_order_remap_required`는 NXT만 보정하며, SOR after-market type `3`은 그대로 전송될 수 있다. 이를 세션 기반 validator로 교체한다.

```text
requested side/route/type
  -> session contract
  -> symbol eligibility
  -> official order-type matrix
  -> authority/custody/quantity/cooldown/stale guards
  -> final route/type freeze
  -> broker submit
```

- KRX 애프터마켓에서 market type가 금지되면 broker 호출 전에 차단 또는 공식적으로 확인된 최유리 지정가형으로 변환한다.
- 현재 local fallback의 type `6`을 새 규칙으로 확정하지 않는다. 구현 시 공식 Kiwoom code표를 재확인하고 fixture를 고정한다.
- conditional/midpoint 등 공지상 미지원 유형은 fail-closed한다.
- reject 뒤 route/type를 바꾸는 자동 retry는 새 주문 intent이며 금지한다.
- buy와 sell 모두 같은 validator를 쓰되, existing holding terminal exit는 별도 safety authority를 유지한다.
- submit 직전 세션·route·order type·자격·source freshness를 재검사하고 freeze hash를 receipt에 남긴다.

### 6.3 15:30~16:00 boundary reconciliation

KRX 정규장 미체결은 새 KRX 애프터마켓으로 자동 이월되지 않는 반면, NXT 주문은 해당 시장의 기존 계약에 따라 이어질 수 있다. 따라서 symbol이나 시간 근접성으로 재주문하면 안 된다.

상태 전이:

```text
REGULAR_OPEN
  -> 15:30 SESSION_BOUNDARY_RECONCILING
     -> KRX child terminal/released proof
     -> NXT child still-open 또는 terminal proof
     -> SOR parent와 각 확인 가능한 child 상태 대사
  -> 15:40 NXT_AFTERMARKET_SOLO_READY
  -> 16:00 KRX_NXT_AFTERMARKET_READY
```

필수 규칙:

- `ka10075(stex_tp=0)`와 기존 `kt00007` exact order evidence를 사용한다.
- parent intent, original order number, child/successor, route, quantity를 결속한다.
- KRX child 하나가 terminal이어도 SOR intent 전체가 terminal이라고 추정하지 않는다.
- NXT child가 살아 있으면 같은 잔량을 SOR로 재제출하지 않는다.
- partial fill은 `requested = filled + confirmed_cancel + broker_remaining` 수량 보존이 닫혀야 한다.
- ACK/reject/empty page만으로 terminal을 만들지 않는다.
- cancel/modify는 원 order number와 원 route를 보존하고 기본 SOR/NXT로 재해석하지 않는다.
- restart 뒤에는 durable intent와 exact dated/current receipt가 일치할 때만 복구한다.

제안 artifact:

`data/runtime/aftermarket_close_reconciliation/aftermarket_close_reconciliation_YYYY-MM-DD.json`

schema `aftermarket_close_reconciliation_v1`은 원 주문 identity, parent/child route, requested/filled/canceled/remaining, evidence paths/hashes, reconciliation state, unknown gaps, generated_at을 포함한다. 장후 체인은 이 artifact의 immutable snapshot/hash를 입력으로 사용한다.

### 6.4 보유·청산

[sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py)의 현재 `krx_only_outside_krx_regular_session` 차단과 NXT 19:45 terminal 경로를 dual-market-aware로 바꾼다.

- 신규 BUY 권한과 기존 보유 SELL 안전권한을 분리한다.
- 16:00 이후 보유의 요청 route는 원 체결/현재 주문/승인된 exit route에 따라 정한다.
- entry가 SOR였다는 이유만으로 exit 실제시장을 SOR로 기록하지 않는다.
- 19:40 이후 신규 BUY 금지는 유지한다.
- 19:45 terminal exit의 eligible route는 양시장 상태·종목 자격·원 주문을 확인한다.
- 한 시장 VI/정지 시 다른 시장이 열려 있음을 추정하지 않고 실시간 상태와 공식 계약을 요구한다.
- broker response가 모호하면 blind retry를 금지하고 existing reconciler에 넘긴다.

## 7. 시세·WebSocket·scanner 설계

### 7.1 request code와 실제시장 분리

현재 좋은 기반은 유지한다.

- `_NX`: NXT-only route
- `_AL`: integrated route
- plain base code: KRX route

[kiwoom_websocket.py](../../src/engine/kiwoom_websocket.py)의 `_ws_item_effective_venue`가 `_AL`에서 물리 venue를 비워 두는 동작은 올바르다. 반대로 다음 consumer의 `_AL => NXT` 보정은 제거한다.

- [entry_candle_context.py](../../src/engine/scalping/entry_candle_context.py)
- [ai_market_snapshot.py](../../src/engine/scalping/ai_market_snapshot.py)
- [holding_decision_context.py](../../src/engine/scalping/holding_decision_context.py)

통합 호가/체결 event에는 `market_data_route=krx_nxt_integrated`, `actual_execution_venue=UNKNOWN`을 기록한다. 공식 packet에 실제 발생시장을 증명하는 별도 필드가 확인될 때만 parser gate와 fixture를 거쳐 물리 venue를 채운다.

### 7.2 세션 상태

현재 `0s` FID 215/214는 기록만 한다. 새 구현은 다음 단계로 제한한다.

1. 공식 새 상태값/전이를 확인해 enum table version을 추가한다.
2. raw FID, item/route, exchange timestamp, receive timestamp를 그대로 보존한다.
3. 알려진 상태만 `OPEN`, `CALL_AUCTION`, `VI`, `CLOSED`로 정규화한다.
4. unknown 상태는 live 진입에 사용하지 않는다.
5. reconnect 뒤 exact route별 최신 상태를 다시 확보하기 전 신규 entry를 차단한다.
6. `ws_receive_expectation`의 quiet waiver는 확인된 call auction/VI 구간에만 적용한다.

정적 시간표만 보고 시장 OPEN을 만들지 않는다. 시간표는 “열릴 수 있음”이고, live state receipt가 실제 상태를 증명한다.

### 7.3 scanner

[scalping_scanner.py](../../src/scanners/scalping_scanner.py)의 `stex_tp=1|2` 단일 선택을 중앙 contract로 이동한다.

- 15:40~16:00: NXT 조회 `2`.
- 16:00~20:00: 공식 API가 통합 순위 조회값을 지원하면 검증된 값 사용.
- 통합값이 없으면 KRX `1`과 NXT `2`를 독립 조회하고 base symbol 기준으로 merge한다.
- merge 시 같은 종목의 rank/price/volume을 한 시장 값으로 덮지 않고 source route를 보존한다.
- 중복 종목 선택은 기존 owner의 scoring/dedupe 규칙을 사용하며, “두 시장 노출”을 두 신호로 세지 않는다.
- 요청 일부 실패는 성공 시장만 전체 통합시장이라고 가장하지 않고 `PARTIAL` source quality로 표시한다.

## 8. runtime producer/consumer별 변경

### 8.1 직접 변경 필수

| 영역 | 파일 | 설계 변경 |
| --- | --- | --- |
| 세션 | [sniper_time.py](../../src/engine/sniper_time.py) | 중앙 resolver 호출, 시행일·15:40/16:00/19:40/19:45 경계 |
| scanner | [scalping_scanner.py](../../src/scanners/scalping_scanner.py) | dual 조회/통합 source quality/종목 dedupe |
| 주문 | [kiwoom_orders.py](../../src/engine/kiwoom_orders.py) | default route 제거, SOR after type preflight, buy/sell 동일 clock 전달 |
| sniper 보유 | [sniper_state_handlers.py](../../src/engine/sniper_state_handlers.py) | dual after exit와 boundary reconciliation |
| 체결 receipt | [sniper_execution_receipts.py](../../src/engine/sniper_execution_receipts.py) | `nxt_*` time label 제거, session/route/actual venue 분리 |
| post-sell | [sniper_post_sell_feedback.py](../../src/engine/sniper_post_sell_feedback.py) | SOR+dual after 허용, actual venue 품질과 비용 귀속 |
| AI 입력 | `entry_candle_context.py`, `ai_market_snapshot.py`, `holding_decision_context.py` | `_AL=>NXT` 삭제, integrated scope 유지 |
| AI 품질 | [ai_decision_quality.py](../../src/engine/scalping/ai_decision_quality.py) | versioned session map, 신규 source-only cohort |
| entry 승인 | [entry_setup_live_policy.py](../../src/engine/scalping/entry_setup_live_policy.py) | dual cohort 기본 미승인, 명시 artifact만 허용 |
| rollout | [entry_setup_scalping_rollout.py](../../src/engine/scalping/entry_setup_scalping_rollout.py) | 기존 NXT scope의 자동 확장 차단 |
| 위젯 contract | [samsung_widget_contract.py](../../src/engine/monitoring/samsung_widget_contract.py) | 새 세션·통합 route·request code |
| 위젯 manual | [manual_orders.py](../../src/trading/widget_auto_trade/manual_orders.py) | 세션/route validation 중앙화 |
| 위젯 web | [samsung_price_widget_routes.py](../../src/web/samsung_price_widget_routes.py) | 16:00부터 `_AL`/integrated scope |
| 위젯 gateway | [gateway.py](../../src/trading/widget_auto_trade/gateway.py) | SOR after sell type preflight, reject retry 금지 |
| 위젯 engine | [engine.py](../../src/trading/widget_auto_trade/engine.py) | exact session/route set 제거, receipt field 확장 |
| 자격 | [kiwoom_utils.py](../../src/utils/kiwoom_utils.py) | raw `nxtEnable` 포함, KRX-after source 분리 |
| EOD | [update_kospi.py](../../src/utils/update_kospi.py) | regular close와 aftermarket close 의미 분리, eligibility ledger |
| DB | [models.py](../../src/database/models.py), [db_manager.py](../../src/database/db_manager.py) | eligibility table와 trade venue/session columns |

### 8.2 기존 정규장 machine 회귀 보호

Samsung morning/midday/afternoon, low-price two-leg 등 정규장 전용 machine의 entry 범위는 늘리지 않는다. 이들은 다음만 검증한다.

- 정규장 SOR route와 기존 세션 결과 불변.
- 시행일 로직이 정규장 주문유형을 바꾸지 않음.
- 기존 보유가 애프터마켓 청산 owner로 인계될 때 custody/수량이 보존됨.
- owner scope에 새 dual session이 명시되지 않으면 신규 entry 0.
- adaptive exit나 terminal reconciliation이 새 BUY 권한을 만들지 않음.

## 9. pipeline event·DB 경제성 계약

### 9.1 공통 event 필드

`market_session_contract_v2`부터 다음 필드를 producer 공통 schema에 추가한다.

```text
session_contract_version
market_session_regime
decision_market_scope
market_data_route
market_data_request_code
broker_route_requested
actual_execution_venue
actual_execution_venue_source
eligible_venues
eligibility_source_sha256
session_state
session_state_source
venue_attribution_quality
```

호환 기간에는 기존 `effective_venue`, `market_session_bucket`을 쓰되 다음 규칙을 적용한다.

- `effective_venue`: 실제 물리 시장이 증명된 때만 `KRX|NXT`, 아니면 `UNKNOWN`.
- `market_session_bucket`: 신규 canonical `market_session_regime`의 compatibility projection.
- 신규 consumer는 legacy 필드만 보고 dual cohort를 선택할 수 없다.
- old schema producer는 `schema_version_missing_for_dual_aftermarket`로 source-quality 차단한다.

### 9.2 trade fact 확장

`RecommendationHistory`와 `TradePerformanceFact`에 최소 다음 값을 durable하게 남긴다.

```text
entry_session_regime
entry_broker_route
entry_actual_venue
entry_actual_venue_source
exit_session_regime
exit_broker_route
exit_actual_venue
exit_actual_venue_source
session_contract_version
```

기존 행을 시간대만으로 backfill하지 않는다. broker receipt가 실제 venue를 증명한 행만 backfill하고 나머지는 `UNKNOWN`과 backfill reason을 기록한다. migration은 additive nullable column/table로 수행하며 기존 PnL, cost, owner identity를 다시 계산하거나 덮지 않는다.

### 9.3 경제성 집계

- PnL은 `COMPLETED + valid profit_rate`만 사용한다.
- entry/exit 실제시장별로 분리하되 둘 중 하나가 UNKNOWN이면 별도 unknown cohort다.
- `SOR` cohort는 요청 방식 분석용이며 물리 시장 손익 cohort가 아니다.
- full/partial fill, real/sim/probe/CF, owner를 계속 분리한다.
- 비용/결과 누락은 0이 아니라 null/coverage다.
- `15:40~16:00 NXT solo`와 `16:00~20:00 dual`을 한 NXT after bucket으로 합치지 않는다.
- KRX/NXT 체결 차이를 비교하더라도 비무작위 SOR routing 편향을 명시한다.

## 10. 장후 전 체인 상세 설계

장후 분석은 이번 전수 점검에 포함했다. 아래 순서는 [run_threshold_cycle_postclose.sh](../../deploy/run_threshold_cycle_postclose.sh), 후속 monitoring, DONE controller와 finalization의 실제 dependency를 기준으로 한다.

### 10.1 postclose 진입 gate

20:00이 됐다는 사실만으로 source가 닫혔다고 보지 않는다. main postclose 시작 전에 다음 exact-date artifact를 요구한다.

1. KRX/NXT 애프터마켓 최종 session-state receipt.
2. pipeline event snapshot freeze와 hash.
3. `aftermarket_close_reconciliation_v1` terminal 또는 명시된 unresolved gap.
4. 날짜별 종목 자격 snapshot/hash.
5. actual execution venue attribution coverage.
6. 기존 clean-baseline/source-quality preflight.

미체결 reconciliation gap이 있으면 주문 lifecycle/경제성 관련 행만 제외·차단한다. 식별 가능한 일부 gap을 이유로 무관한 날짜 전체를 차단하지 않는다. 반대로 actual venue가 없는 행을 NXT/KRX에 임의 배분하지 않는다.

### 10.2 직접 변경해야 할 postclose producer

| producer | 현행 문제 | 목표 계약 |
| --- | --- | --- |
| [buy_funnel_sentinel.py](../../src/engine/buy_funnel_sentinel.py) | after=NXT, venue allowlist 제한 | decision scope/route/actual venue 분리, dual source gap 이유 |
| [holding_exit_sentinel.py](../../src/engine/holding_exit_sentinel.py) | 같은 단일 venue/session map | entry·exit 실제시장과 SOR route 별도 |
| [market_opportunity_census.py](../../src/engine/monitoring/market_opportunity_census.py) | 15:30 이후 전부 NXT, integrated UNKNOWN 제거 가능 | 15:40 solo/16:00 dual 분리, route별 census와 merge coverage |
| [rising_missed_intraday_feedback.py](../../src/engine/monitoring/rising_missed_intraday_feedback.py) | KRX/NXT/PREMARKET allowlist | 신규 schema 수용, dual scope와 actual venue 분리 |
| [scalping_pyramid_intraday_feedback.py](../../src/engine/monitoring/scalping_pyramid_intraday_feedback.py) | 기존 cohort 고정 | 동일 변경, scale-in 권한은 늘리지 않음 |
| [observation_source_quality_audit.py](../../src/engine/observation_source_quality_audit.py) | 장후 KRX 차단을 정상 사유로 봄 | 시행일 이후 해당 사유를 결함으로 판정, attribution coverage 검사 |
| [intraday_ws_freshness_monitor.py](../../src/engine/monitoring/intraday_ws_freshness_monitor.py) | KRX/NXT만, route별 expected code 고정 | integrated route·양시장 session state·19:50 관찰 |
| [ws_receive_expectation.py](../../src/engine/monitoring/ws_receive_expectation.py) | 개장 auction 중심 | 검증된 VI/call-auction quiet state만 허용 |
| [ai_quality_cycle.py](../../src/engine/scalping/micro_reversion/ai_quality_cycle.py) | KRX/NXT partition | dual decision scope 수용, live 권한 추가 금지 |
| [main_ai_prompt_optimizer.py](../../src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py) | 정확히 2 cohort 요구 | version별 expected cohort, 신규 cohort는 research-only |
| [entry_setup_paired_replay_batch.py](../../src/engine/scalping/entry_setup_paired_replay_batch.py) | KRX regular/NXT after만 | dual source-only arm 추가, 과거 cohort 불변 |
| [main_ai_prompt_consumer.py](../../src/engine/scalping/main_ai_prompt_consumer.py) | batch cohort/hash 고정 | contract version·새 cohort hash 검증 |
| [ai_action_outcome_calibration.py](../../src/engine/scalping/ai_action_outcome_calibration.py) | route scope 고정 | actual venue/route/session별 calibration, unknown 제외 |
| [machine_microstructure_attribution.py](../../src/engine/monitoring/machine_microstructure_attribution.py) | after session=>NXT | integrated scope 보존; regular-only machine 범위 불변 |
| [widget_advisory_calibration.py](../../src/engine/monitoring/widget_advisory_calibration.py) | NXT after spec 고정 | solo/dual cohort와 source coverage 분리 |
| [widget_auto_trade_policy_calibration.py](../../src/engine/monitoring/widget_auto_trade_policy_calibration.py) | 같은 문제 | 신규 cohort 자동 정책 승격 금지 |
| [samsung_widget_advisory_evaluation.py](../../src/engine/monitoring/samsung_widget_advisory_evaluation.py) | expected 260분 NXT after | solo20분/dual240분을 별도 expected minutes로 관리 |
| [samsung_widget_advisory.py](../../src/engine/monitoring/samsung_widget_advisory.py) | NXT 전용 threshold/peer 가정 | dual context 별도 진단, 기존 NXT 경제정책 상속 금지 |
| [ai_multi_timeframe_context_promotion.py](../../src/engine/automation/ai_multi_timeframe_context_promotion.py) | 세션 집합 고정 | source schema 수용만, 자동 promotion 없음 |
| [daily_threshold_cycle_report.py](../../src/engine/daily_threshold_cycle_report.py) | `infer_scalping_venue`와 upstream legacy field | session version 필수, actual venue별 EV와 unknown coverage |
| [threshold_cycle_preopen_apply.py](../../src/engine/threshold_cycle_preopen_apply.py) | KRX/NXT/PREMARKET venue 허용 | 신규 dual family는 승인 artifact 없으면 apply 불가 |

### 10.3 strict controller·승인 chain

[run_postclose_done_controller.sh](../../deploy/run_postclose_done_controller.sh)은 현재 `bounded_live_candidates_by_cohort`의 key 집합을 정확히 다음 두 개로 강제한다.

```text
KRX/KRX_REGULAR
NXT/NXT_AFTERMARKET
```

이를 단순히 세 번째 live candidate로 늘리면 안 된다. 첫 단계 목표는 다음과 같다.

```text
KRX/KRX_REGULAR                  -> 기존 live 승인 계약
NXT/NXT_AFTERMARKET              -> 2026-09-14 이전 replay 호환 계약
NXT/NXT_AFTERMARKET_SOLO         -> versioned 기존/관찰 계약
INTEGRATED/KRX_NXT_AFTERMARKET   -> source-only, live_candidate=null
```

controller는 `expected_cohorts_by_contract_version`을 사용하고 각 cohort에 `authority_state`를 요구한다. 신규 dual cohort는 `OBSERVE_ONLY` 또는 `BLOCKED_MISSING_APPROVAL`로 terminal 가능하지만 live candidate를 내면 실패해야 한다. 기존 NXT candidate hash를 dual cohort에 재사용하면 실패한다.

다음 artifact들의 hash/lineage에도 새 contract 파일과 close reconciliation hash를 포함한다.

- prompt optimizer/consumer candidate contract
- AI decision/action outcome calibration
- runtime approval summary
- key lineage ledger
- conversion lane
- control tower
- checklist handoff
- postclose summary handoff
- final verifier

[verify_threshold_cycle_postclose_chain.py](../../src/engine/verify_threshold_cycle_postclose_chain.py)는 필드 존재만 확인하지 말고 다음을 검증한다.

- contract version과 target date 일치.
- 시행일 이후 dual window의 legacy-only row 수 0 또는 정확한 raw exclusion.
- integrated request를 NXT actual venue로 투영한 행 0.
- cohort별 input row hash와 제외 row hash.
- actual venue coverage 및 UNKNOWN 수.
- 신규 cohort의 live authority가 없음.
- close reconciliation과 pipeline snapshot source hash 일치.

### 10.4 후단 중 직접 의미 변경은 없고 회귀검증이 필요한 부분

다음 owner는 주로 target date, predecessor status, artifact hash와 terminal state를 확인하므로 시장 규칙을 직접 재구현하지 않는다. 다만 upstream schema가 바뀌어 필드를 버리거나 오래된 artifact를 재사용하지 않는지 회귀검증한다.

| 후단 | 판정 |
| --- | --- |
| [postclose_summary_handoff.py](../../src/engine/automation/postclose_summary_handoff.py) | source 목록/hash에 신규 market contract·reconciliation 포함 필요. 시장 계산 자체는 금지 |
| [runtime_approval_summary.py](../../src/engine/runtime_approval_summary.py) | 신규 blocker/cohort가 aggregate에서 사라지지 않고 live 승인으로 오인되지 않는지 검증 |
| [key_lineage_ledger.py](../../src/engine/automation/key_lineage_ledger.py) | version/hash lineage 연결 확인 |
| [conversion_lane.py](../../src/engine/automation/conversion_lane.py) | observe-only를 live candidate로 변환하지 않는지 확인 |
| [run_tuning_monitoring_postclose.sh](../../deploy/run_tuning_monitoring_postclose.sh) | predecessor gate는 유지, Parquet schema 보존 검증 |
| `build_tuning_monitoring_parquet.py` | 새 nullable/string/list 필드가 JSONL→Parquet에서 손실되지 않는지 fixture 추가 |
| [run_postclose_finalization.sh](../../deploy/run_postclose_finalization.sh) | predecessor final 상태를 기다리는 구조 유지, 신규 required owner 포함 여부 확인 |
| dashboard archive/error detector/log cleanup | 새 artifact archive·missing detector만 추가, 거래 의미 계산 금지 |

### 10.5 장후 시간표

- 20:00 시장 종료 시각은 유지.
- 20:05 EOD update는 유지하되 “NXT close 후” 문구를 “KRX/NXT 애프터마켓 close 후”로 변경.
- 20:10 widget advisory evaluation은 두 시장 final source와 reconciliation gate 뒤 실행.
- 21:05 AI replay, 21:15 machine final refresh는 신규 schema/hash를 소비.
- main postclose, tuning monitoring, DONE controller, finalization의 predecessor 순서는 유지.

시간만 맞는 것은 acceptance가 아니다. exact-date source freeze와 terminal order reconciliation이 늦으면 downstream도 기다리거나 명시 실패해야 한다.

## 11. cron·wrapper 변경

### 11.1 수정 대상

- [install_stage2_ops_cron.sh](../../deploy/install_stage2_ops_cron.sh)
  - `NXT_AFTERMARKET` label을 `AFTERMARKET` 또는 세션별 label로 변경.
  - holding-exit sentinel과 WS freshness 종료를 19:20에서 최소 19:50까지 연장해 19:45 terminal exit를 관찰.
  - buy-funnel은 기존 19:20/19:40 정책 의도에 맞춰 별도 유지 여부를 명시.
- [install_market_opportunity_census_cron.sh](../../deploy/install_market_opportunity_census_cron.sh)
  - 16:00 이후 dual label/route, 15:40~16:00 NXT solo 분리.
- [install_eod_data_chain_cron.sh](../../deploy/install_eod_data_chain_cron.sh)
  - 설명·receipt 명칭 갱신, 시각은 20:05 유지.
- [run_threshold_cycle_postclose.sh](../../deploy/run_threshold_cycle_postclose.sh)
  - preflight에 market contract/reconciliation/eligibility hashes 추가.
  - `check-reusable` 입력 fingerprint에 중앙 계약 코드와 schema version 포함.
- [run_postclose_done_controller.sh](../../deploy/run_postclose_done_controller.sh)
  - version-aware cohort·authority 검증.

cron 설치는 코드 구현과 별도 운영 변경이다. wrapper·installer 수정 후 `bash -n`, 정확한 설치 행/label/중복 owner 테스트를 통과하고, 별도 승인 전 실제 crontab/systemd에는 적용하지 않는다.

## 12. 권한·승인 경계

기존 [entry_setup_scalping_rollout.py](../../src/engine/scalping/entry_setup_scalping_rollout.py)의 승인 범위 `NXT|NXT_AFTERMARKET`은 `KRX_NXT_AFTERMARKET`을 포함하지 않는다.

새 dual cohort의 초기 상태:

```text
data collection       = allowed after source contract validation
source-quality report = allowed
simulation/replay     = allowed with actual_order_submitted=false
live BUY              = forbidden without new immutable approval
holding reconciliation= allowed under existing safety/custody
protective SELL       = allowed only through existing owner authority
threshold promotion   = forbidden until cohort-specific evidence/approval
```

신규 live approval artifact에는 최소 다음을 넣는다.

- target date/effective date/expiry
- code commit/root, market contract version/hash
- owner, symbol/profile, session, allowed route/order type
- eligibility snapshot hash
- cap/quantity/cooldown와 기존 hard guards
- source-quality minimum과 actual venue attribution handling
- canary 범위, rollback owner, terminal order 처리
- 이전 NXT approval과 다른 candidate/contract hash

새 시장 개장 자체는 거래 권한이 아니다. source-only 표본이 없다는 이유로 실제 주문을 만들거나 cap/threshold를 완화하지 않는다.

## 13. Spark용 bounded 구현 작업계획

### 13.1 분할 기준

[OpenAI Codex models 문서](https://developers.openai.com/codex/models)는 `gpt-5.3-codex-spark`를 빠른 실시간 코딩 반복에 최적화된 text-only research preview로 설명한다. 아래 파일 수·반복 제한은 OpenAI가 공표한 모델 한계가 아니라, 이 대형 거래 코드베이스에서 범위 팽창과 토큰 낭비를 막기 위한 **프로젝트 자체의 보수적 실행 계약**이다.

기존 Phase 0~6처럼 한 요청에 여러 owner를 묶지 않는다. 한 Codex 호출은 아래 `AM-Sxx` 하나만 실행하며, 완료 후 자동으로 다음 ID를 시작하지 않는다.

### 13.2 모든 작업에 공통인 중단·토큰 절약 규칙

1. **한 호출=한 ID**다. 사용자가 `AM-Sxx` 하나를 명시하지 않고 “전체 구현”이라고 해도 executor는 첫 미완료 ID 하나만 수행하고 결과를 반환한다. 다음 ID는 새 지시를 기다린다.
2. 작업 시작 시 AGENTS, Plan Rebase §1~§8, 현재 체크리스트 목적·강제규칙을 읽거나 같은 세션에서 이미 읽은 최신 context를 재사용한다. 본 문서는 공통규칙, 해당 ID 행, 해당 세부 section만 읽는다. 역사 audit/archive 전체를 재귀 탐색하지 않는다.
3. `Read`에 적힌 파일과 그 파일이 직접 import하는 필수 contract/nearby test만 연다. repo 전체 검색은 최초 위치 확인용 `rg` 한 번으로 제한하고, 출력이 크면 path/pattern을 좁힌다. `sniper_state_handlers.py`, `daily_threshold_cycle_report.py`, verifier 같은 거대 파일은 관련 함수의 `rg` 결과와 인접 범위만 읽고 파일 전체를 반복 출력하지 않는다.
4. `Write`에 적힌 경로 밖은 수정하지 않는다. 새 필요 경로가 발견되면 구현하지 말고 `OUT_OF_SCOPE_FOLLOWUP`으로 반환한다. “같이 정리”, 일반 refactor, rename, dead-code cleanup, 성능 개선, 로그 미화, 새 CLI/report/daemon은 금지한다.
5. 새 Python 파일은 해당 ID가 명시적으로 허용한 두 파일 외에는 만들지 않는다. `src/engine` root에 새 모듈을 만들지 않는다. compatibility wrapper도 기존 caller가 깨지는 증거가 없으면 만들지 않는다.
6. 구현은 `1회 discovery -> 1회 implementation pass -> 1회 self-review -> 최대 2회 in-scope fix/test -> 최종 re-review`로 끝낸다. 같은 원인의 실패가 두 번 반복되거나 세 번째 수정회차가 필요하면 PASS를 주장하지 않고 `BLOCKED_REPEATED_FAILURE`로 종료한다. 하위 agent를 만들거나 별도 agent에게 같은 전수검사를 중복 위임하지 않는다.
7. 테스트는 해당 ID의 `Validate`, 영향 파일 compile/import, 해당 diff의 `git diff --check`만 실행한다. broad pytest, report 재생성, live API/provider/account/order 호출, cron/systemd 설치, bot 재기동, Project/Calendar sync는 금지한다. unrelated test failure는 고치지 않고 명령·첫 실패·영향을 기록한다.
8. official protocol 의미가 없거나 충돌하면 추정 구현하지 않는다. `BLOCKED_OFFICIAL_CONTRACT`와 필요한 정확한 문서/필드를 남긴다. 독립적인 source-only 또는 순수 코드 작업은 계속할 수 있지만 권한을 열지 않는다.
9. dirty worktree의 기존 변경과 겹치면 diff를 먼저 분리한다. 안전하게 분리할 수 없으면 `BLOCKED_DIRTY_OVERLAP`으로 종료한다. 사용자 변경을 revert/format하지 않는다.
10. 테스트를 통과시키려고 기존 threshold, provider, bot state, cap, quantity, cooldown, owner/custody, live approval을 바꾸지 않는다. 신규 dual entry의 기본은 항상 OFF/observe-only다.
11. 출력은 아래 여섯 줄 형식을 우선한다. 긴 작업일지나 다음 단계 구현은 쓰지 않는다.

```text
DECISION: PASS | BLOCKED | FAIL
TASK_ID: AM-Sxx
CHANGED: <paths or none>
VALIDATION: <commands and result>
BLOCKERS: <exact blockers or none>
NEXT_ID: <one ID or none; do not execute>
```

### 13.3 Spark에 전달할 고정 프롬프트 머리말

아래 머리말에 작업표의 ID 하나만 붙여 사용한다.

```text
Execute exactly one task ID from
docs/proposals/krx-aftermarket-sor-detailed-implementation-design-2026-09-11.md.

Task ID: AM-Sxx

Obey AGENTS.md and the task row's Read/Write/Validate/Stop boundaries.
Do not implement any later task, deploy, restart services, install cron,
call a live broker/provider, regenerate postclose reports, or edit unrelated files.
Use at most two in-scope fix-and-retest cycles. If the task needs an unlisted
file, an undefined official Kiwoom contract, a third fix cycle, or overlaps
unseparable user changes, stop with the specified BLOCKED status.
Finish with DECISION/TASK_ID/CHANGED/VALIDATION/BLOCKERS/NEXT_ID.
```

작업별 세부 지시는 본 문서의 의미를 다시 설계할 권한이 아니다. 모호하면 기능을 추가하지 않고 blocker로 남긴다.

### 13.4 작업 순서 요약

```text
AM-S00
  -> AM-S01 -> AM-S02 -> AM-S02B
  -> AM-S03 -> AM-S04A -> AM-S04B
AM-S01 -> AM-S05A -> AM-S05B -> AM-S05C -> AM-S06
AM-S00 + AM-S01 + AM-S04B -> AM-S07 -> AM-S08 -> AM-S09 -> AM-S10 -> AM-S11
AM-S01 -> AM-S12 -> AM-S13 -> AM-S14
AM-S02 + AM-S05A -> AM-S15A -> AM-S15B -> AM-S15C -> AM-S16
AM-S11 + AM-S15C -> AM-S17 -> AM-S18A -> AM-S18B -> AM-S18C
AM-S14 + AM-S18A -> AM-S19A -> AM-S19B -> AM-S19C
AM-S18C + AM-S19C -> AM-S20A -> AM-S20B
AM-S16 + AM-S20B -> AM-S21A -> AM-S21B -> AM-S22 -> AM-S23
AM-S20B + AM-S23 -> AM-S24A
AM-S20B + AM-S23 -> AM-S24B
AM-S24A + AM-S24B -> AM-S25
AM-S25 + 별도 사용자 승인 -> AM-S26
```

의존 task가 PASS가 아니면 downstream task는 시작하지 않는다. `AM-S00`의 일부 wire gap은 관련 task만 막으며, 순수 session contract `AM-S01`처럼 독립된 작업까지 전역 차단하지 않는다.

### 13.5 작업 패킷

| ID | 단일 목표 | Read | Write | Validate | Stop/인계 |
| --- | --- | --- | --- | --- | --- |
| `AM-S00` | 9/14 공식 wire 계약을 evidence로 동결 | 공식 Kiwoom 최신 revision, `docs/kiwoom-api-data-contract.md`, 본 문서 §2 | 신규 `docs/audit-reports/2026-09-11-krx-aftermarket-kiwoom-contract-gate.md`만 | SHA/path/time, order type matrix, eligibility source, 0s enum, unresolved 목록 자체검사 | 코드 수정0. 미확정 필드별 `BLOCKED_OFFICIAL_CONTRACT`; `NEXT_ID=AM-S01` |
| `AM-S01` | effective-date 순수 세션 resolver 구현 | 본 문서 §4, `src/engine/sniper_time.py`, `src/tests/test_constants.py` | 신규 `src/trading/market/session_contract.py`, 신규 `src/tests/test_market_session_contract.py` | 새 test, import/compile, pre/post-9/14 경계 | 주문·DB·consumer 수정 금지; `NEXT_ID=AM-S02` |
| `AM-S02` | 기존 clock consumer 3곳만 중앙 resolver에 연결 | AM-S01, `src/engine/sniper_time.py`, `src/engine/monitoring/samsung_widget_contract.py`, `src/web/samsung_price_widget_routes.py` | 앞의 production 3개, `src/tests/test_constants.py`, `src/tests/test_samsung_price_widget_routes.py`, `src/tests/test_samsung_widget_advisory.py` | 명시한 test 3개에서 session 관련 test만 `-k` 선택 | widget engine/scanner/order 금지; `NEXT_ID=AM-S02B` |
| `AM-S02B` | sniper entrypoint가 중앙 session context만 전달 | AM-S02, session 선택부만 `src/engine/kiwoom_sniper_v2.py` | production 1개, 기존 관련 `src/tests/test_kiwoom_sniper_market_regime_runtime.py` | injected clock과 pre/post-9/14 context 전달, 기존 startup 회귀 | handler/order 로직 수정 금지; `NEXT_ID=AM-S03` |
| `AM-S03` | 날짜별 종목 자격 순수 contract 구현 | 본 문서 §5, `src/utils/kiwoom_utils.py`의 현행 eligibility 함수 | 신규 `src/trading/market/aftermarket_eligibility.py`, 신규 `src/tests/test_aftermarket_eligibility.py` | both/only/neither/unknown/conflict/stale tests, compile | API 호출·DB 수정 금지; KRX-after field 미확정이어도 nullable contract까지만 PASS |
| `AM-S04A` | eligibility DB schema와 compatibility reader 추가 | AM-S03, `src/database/models.py`, `src/database/db_manager.py` | production 2개, 신규 `src/tests/test_market_eligibility_db.py` | clean DB create, existing DB additive migration, old row read | data backfill·EOD producer 금지; `NEXT_ID=AM-S04B` |
| `AM-S04B` | `ka10099` raw 자격 producer와 20:05 EOD 저장 연결 | AM-S00/S03/S04A, 관련 함수만 `src/utils/kiwoom_utils.py`, `src/utils/update_kospi.py` | production 2개, 신규 `src/tests/test_update_kospi_aftermarket_eligibility.py` | pagination/provenance/null KRX-after, old `is_nxt` compatibility, API fake | 실제 API·일봉 종가 재해석·과거 backfill 금지; 미확정 field는 NULL/blocker |
| `AM-S05A` | `_AL/_NX/plain`을 data route로만 정규화 | AM-S01, `src/engine/kiwoom_websocket.py`, `src/engine/scalping/micro_reversion/contracts.py` | production 2개, `src/tests/test_kiwoom_websocket.py`, `src/tests/test_micro_reversion_contracts.py` | `_AL=>integrated/actual UNKNOWN`, `_NX=>NXT route`, reconnect 관련 test | 새 FID enum/REG 변경 금지; `NEXT_ID=AM-S05B` |
| `AM-S05B` | 공식 0s 상태값만 versioned enum으로 정규화 | AM-S00/S05A, 0s 처리부만 `src/engine/kiwoom_websocket.py` | production 1개, `src/tests/test_kiwoom_websocket.py` | known state transitions/raw 보존/unknown fail-closed | 공식 enum 미확정 시 코드0 `BLOCKED_OFFICIAL_CONTRACT`; REG/REMOVE 변경 금지 |
| `AM-S05C` | WS freshness/quiet expectation이 dual state를 소비 | AM-S05B, `src/engine/monitoring/intraday_ws_freshness_monitor.py`, `src/engine/monitoring/ws_receive_expectation.py` | production 2개, `src/tests/test_intraday_ws_freshness_monitor.py`, `src/tests/test_ws_freshness_acceptance.py` | integrated route, VI/call-auction known-only quiet, 19:45 coverage | subscription·threshold 변경 금지; `NEXT_ID=AM-S06` |
| `AM-S06` | scanner의 15:40 solo/16:00 dual source 수집 | AM-S01/S05A, `src/scanners/scalping_scanner.py`, `src/scanners/scanner_source_census.py` | production 2개, `src/tests/test_scalping_scanner_candidate_pool.py`, `src/tests/test_scanner_source_census.py` | route별 성공/partial/merge/dedupe fixture | official integrated rank 값이 없으면 두 조회 merge만; 주문/score 변경 금지 |
| `AM-S07` | 공식 evidence에 맞춘 순수 order-type preflight | AM-S00/S01/S03/S04B, 본 문서 §6.2, `src/engine/kiwoom_orders.py`의 remap 함수 | `src/trading/market/session_contract.py`, `src/tests/test_market_session_contract.py` | route×side×session×type table tests | type code 미확정 시 `BLOCKED_OFFICIAL_CONTRACT`; broker adapter 수정 금지 |
| `AM-S08` | `kiwoom_orders` buy/sell에 route/type preflight 연결 | AM-S07, `src/engine/kiwoom_orders.py`, `src/tests/test_kiwoom_orders.py` | 읽은 두 파일만 | explicit now, SOR-after type3 pre-submit block/remap, no reject-reroute tests | 실제 API0, retry/cap/quantity 불변; `NEXT_ID=AM-S09` |
| `AM-S09` | 15:30 parent/child reconciliation 순수 ledger 구현 | AM-S00/S01, 본 문서 §6.3, `src/trading/order/owner_custody_registry.py`, `src/engine/kiwoom_orders.py`의 read-only reconciliation helper | 신규 `src/trading/order/aftermarket_reconciliation.py`, 신규 `src/tests/test_aftermarket_reconciliation.py` | KRX release/NXT open/SOR split/partial/cancel/restart quantity conservation | broker call adapter·sniper integration 금지; 모호 receipt는 UNKNOWN terminal 금지 |
| `AM-S10` | sniper holding/terminal-exit session·route 전환 | AM-S01/S08/S09, 관련 함수만 `src/engine/sniper_state_handlers.py`, `src/engine/sniper_trade_utils.py` | production 2개, `src/tests/test_sniper_trade_utils.py`, `src/tests/test_scalp_exit_safety_monitor.py` | 19:40/19:45, KRX/NXT/SOR, custody/duplicate-sell 관련 test만 | 거대 handler의 무관 refactor 금지; 대상 함수 밖 수정 필요 시 BLOCKED |
| `AM-S11` | sniper execution/post-sell receipt에 4축 저장 | AM-S05A/S10, `src/engine/sniper_execution_receipts.py`, `src/engine/sniper_post_sell_feedback.py` | production 2개, `src/tests/test_post_sell_feedback.py`, `src/tests/test_main_lifecycle_receipt_integration.py` | SOR requested vs actual KRX/NXT/UNKNOWN, solo/dual, cost-null 관련 test | AI/report 집계 금지; `NEXT_ID=AM-S12` |
| `AM-S12` | widget session/request-route contract 전환 | AM-S02/S05A, `src/engine/monitoring/samsung_widget_contract.py`, `src/web/samsung_price_widget_routes.py`, `src/trading/widget_auto_trade/policy.py` | production 3개, `src/tests/test_samsung_price_widget_routes.py`, `src/tests/test_widget_auto_trade_policy.py` | 15:40 `_NX`, 16:00 `_AL`, actual venue 미추론 | engine/gateway/manual order 금지 |
| `AM-S13` | widget manual/gateway 주문 preflight 연결 | AM-S08/S12, `src/trading/widget_auto_trade/manual_orders.py`, `src/trading/widget_auto_trade/gateway.py` | production 2개, `src/tests/test_widget_manual_orders.py`, `src/tests/test_widget_signal_auto_trade.py` | SOR-after SELL type, unsupported type pre-submit 0, explicit route 관련 test | engine/advisory 수정 금지; `NEXT_ID=AM-S14` |
| `AM-S14` | widget engine이 새 session/route receipt를 보존 | AM-S12/S13, 관련 함수만 `src/trading/widget_auto_trade/engine.py` | production 1개, `src/tests/test_widget_signal_auto_trade.py` | unapproved dual BUY 0, existing regular/NXT regression, receipt fields | advisory/calibration/refactor 금지 |
| `AM-S15A` | AI 입력 3곳의 `_AL=>NXT` 제거 | AM-S05A, `src/engine/scalping/entry_candle_context.py`, `src/engine/scalping/ai_market_snapshot.py`, `src/engine/scalping/holding_decision_context.py` | production 3개, `src/tests/test_entry_candle_context.py`, `src/tests/test_ai_market_snapshot.py`, `src/tests/test_holding_decision_context.py` | integrated scope/actual UNKNOWN, old `_NX` and KRX behavior | score/prompt/threshold 변경 금지; `NEXT_ID=AM-S15B` |
| `AM-S15B` | probe/baseline/lifecycle의 legacy-after projection 분리 | AM-S15A, `src/engine/scalping/entry_context_intraday_probe.py`, `src/engine/scalping/ai_input_quality_baseline_replay.py`, `src/engine/scalping/entry_candidate_lifecycle_state.py` | production 3개, `src/tests/test_entry_context_intraday_probe.py`, `src/tests/test_ai_input_quality_baseline_replay.py`, `src/tests/test_entry_candidate_lifecycle_state.py` | pre-9/14 replay 불변, post-9/14 dual/UNKNOWN, no time-only venue inference | policy/AI score 변경 금지; `NEXT_ID=AM-S15C` |
| `AM-S15C` | micro-reversion 수집 계약에서 route와 actual venue 분리 | AM-S15B, `src/engine/scalping/micro_reversion/forward_collector.py`, `src/engine/scalping/micro_reversion/ai_quality_bridge.py`, `src/engine/scalping/strategy_owner_components.py` | production 3개, `src/tests/test_micro_reversion_forward_collector.py`, `src/tests/test_micro_reversion_ai_quality_bridge.py`, `src/tests/test_strategy_owner_components.py` | integrated route 보존, actual UNKNOWN coverage, regular/NXT legacy regression | 새 observer/AI 호출/threshold 금지; `NEXT_ID=AM-S16` |
| `AM-S16` | AI quality/live policy에 dual observe-only cohort 추가 | AM-S15C, `src/engine/scalping/ai_decision_quality.py`, `src/engine/scalping/entry_setup_live_policy.py`, `src/engine/scalping/entry_setup_scalping_rollout.py`, `src/engine/scalping/entry_recheck_policy.py` | production 4개, `src/tests/test_ai_decision_quality.py`, `src/tests/test_entry_setup_live_policy.py`, `src/tests/test_entry_recheck_policy.py` | old approvals valid only old scope, dual live candidate blocked 관련 test | optimizer/controller 금지, 새 approval 생성 금지 |
| `AM-S17` | sentinels/census producer의 세션 분류 전환 | AM-S11/S15C, `src/engine/buy_funnel_sentinel.py`, `src/engine/holding_exit_sentinel.py`, `src/engine/monitoring/market_opportunity_census.py` | production 3개, `src/tests/test_buy_funnel_sentinel.py`, `src/tests/test_holding_exit_sentinel.py`, `src/tests/test_market_opportunity_census.py` | solo/dual/UNKNOWN/actual venue, valid-empty/partial source | downstream tuning/report 수정 금지 |
| `AM-S18A` | missed/pyramid/source-quality가 새 필드를 손실 없이 소비 | AM-S17, `src/engine/monitoring/rising_missed_intraday_feedback.py`, `src/engine/monitoring/scalping_pyramid_intraday_feedback.py`, `src/engine/observation_source_quality_audit.py` | production 3개, `src/tests/test_rising_missed_intraday_feedback.py`, `src/tests/test_scalping_pyramid_intraday_feedback.py`, `src/tests/test_observation_source_quality_audit.py` | identifiable row exclusion, legacy-after misclassification 0, no global overblock | threshold/calibration 변경 금지 |
| `AM-S18B` | pure-market backfill/replay를 시행일별 세션으로 분리 | AM-S18A, `src/engine/monitoring/pure_market_kiwoom_backfill.py`, `src/engine/monitoring/pure_market_adaptive_opportunity_replay.py`, `src/engine/monitoring/pure_market_reversal_replay.py` | production 3개, `src/tests/test_pure_market_kiwoom_backfill.py`, `src/tests/test_pure_market_adaptive_opportunity_replay.py`, `src/tests/test_pure_market_reversal_replay.py` | legacy replay 불변, dual route provenance, partial source | remote backfill/API 호출·새 연구축 금지 |
| `AM-S18C` | machine/micro attribution의 dual source-only 축 보존 | AM-S18B, `src/engine/monitoring/machine_microstructure_attribution.py`, `src/engine/scalping/micro_reversion/ai_quality_cycle.py`, `src/engine/automation/ai_multi_timeframe_context_promotion.py` | production 3개, `src/tests/test_machine_microstructure_attribution.py`, `src/tests/test_micro_reversion_ai_quality_cycle.py`, `src/tests/test_ai_multi_timeframe_context_promotion.py` | regular-only machine 불변, dual actual UNKNOWN coverage, auto-promotion 0 | machine scope·threshold·provider 변경 금지 |
| `AM-S19A` | widget advisory가 NXT-only 정책을 dual에 상속하지 않음 | AM-S14/S18A, 관련 함수만 `src/engine/monitoring/samsung_widget_advisory.py`, `src/engine/monitoring/widget_collector_expansion_recommendation.py` | production 2개, `src/tests/test_samsung_widget_advisory.py`, `src/tests/test_widget_collector_expansion_recommendation.py` | solo NXT caution 유지, dual 별도 context/observe-only, 20:00 close | 숫자 threshold·peer 전략·새 advisory 기능 금지 |
| `AM-S19B` | widget 장후 평가·calibration 세션 분리 | AM-S19A, `src/engine/monitoring/samsung_widget_advisory_evaluation.py`, `src/engine/monitoring/widget_advisory_calibration.py`, `src/engine/monitoring/widget_auto_trade_policy_calibration.py` | production 3개, `src/tests/test_samsung_widget_advisory_evaluation.py`, `src/tests/test_widget_advisory_calibration.py`, `src/tests/test_widget_auto_trade_policy_calibration.py` | solo20/dual240 coverage, dual auto-promotion 0, legacy replay | advisory 전략 자체·숫자 threshold 변경 금지 |
| `AM-S19C` | widget execution/replay 경제성 cohort 분리 | AM-S19A/S19B, `src/engine/monitoring/widget_execution_quality.py`, `src/engine/monitoring/widget_mechanical_entry_replay.py`, `src/engine/monitoring/widget_paired_policy_replay.py` | production 3개, `src/tests/test_widget_mechanical_entry_replay.py`, `src/tests/test_widget_paired_policy_replay.py`, 기존 execution-quality test가 없으면 신규 1개 | actual venue/route/session, legacy replay, cost-null | 새 counterfactual·정책 추천 금지 |
| `AM-S20A` | daily EV report의 route/actual venue/cohort 집계 | AM-S11/S18C/S19C, 관련 함수만 `src/engine/daily_threshold_cycle_report.py` | production 1개, `src/tests/test_daily_threshold_cycle_report.py` | COMPLETED+valid PnL, full/partial, KRX/NXT/UNKNOWN, cost-null 관련 test | 거대 파일의 무관 section 수정 금지; report 재생성 금지 |
| `AM-S20B` | action-outcome calibration의 route/session key version화 | AM-S20A, `src/engine/scalping/ai_action_outcome_calibration.py` | production 1개, `src/tests/test_ai_action_outcome_calibration.py` | legacy keys, dual source-only key, UNKNOWN/cost missing exclusion | threshold recommendation/promotion 금지 |
| `AM-S21A` | replay/optimizer/consumer cohort contract version화 | AM-S16/S20B, `src/engine/scalping/entry_setup_paired_replay_batch.py`, `src/engine/scalping/micro_reversion/main_ai_prompt_optimizer.py`, `src/engine/scalping/main_ai_prompt_consumer.py` | production 3개, `src/tests/test_entry_setup_paired_replay_batch.py`, `src/tests/test_main_ai_prompt_optimizer.py`, `src/tests/test_main_ai_prompt_consumer.py` | expected cohort by version, dual source-only, hash mismatch fail | provider 호출·prompt 내용 최적화·live candidate 금지 |
| `AM-S21B` | preopen apply가 dual observe-only를 live로 승격하지 않음 | AM-S16/S21A, 관련 함수만 `src/engine/threshold_cycle_preopen_apply.py` | production 1개, `src/tests/test_threshold_cycle_preopen_apply.py` | old KRX/NXT approvals unchanged, dual missing approval blocked, exact hash/date | policy artifact 생성·threshold/env 적용 금지 |
| `AM-S22` | DONE controller의 고정 2-cohort 검증 교체 | AM-S21B, `deploy/run_postclose_done_controller.sh`, `src/tests/test_postclose_done_controller.py` | 읽은 두 파일만 | old contract, new observe-only, illegal dual-live failure, `bash -n` | verifier/handoff 수정 금지 |
| `AM-S23` | strict verifier에 session contract/reconciliation/coverage 검증 | AM-S21B/S22, 관련 함수만 `src/engine/verify_threshold_cycle_postclose_chain.py` | production 1개, `src/tests/test_verify_threshold_cycle_postclose_chain.py` | hashes/date/UNKNOWN coverage/raw exclusion/authority 관련 test만 | 전체 verifier refactor·artifact 생성 금지 |
| `AM-S24A` | runtime summary·lineage·conversion이 observe-only를 보존 | AM-S20B/S23, `src/engine/runtime_approval_summary.py`, `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py` | production 3개, `src/tests/test_runtime_approval_summary.py`, `src/tests/test_conversion_lane_key_lineage.py` | hash lineage, dual observe-only nonconversion | handoff/Parquet/wrapper 금지 |
| `AM-S24B` | summary handoff와 Parquet schema 왕복 보존 | AM-S20B/S23, `src/engine/automation/postclose_summary_handoff.py`, `src/engine/build_tuning_monitoring_parquet.py` | production 2개, `src/tests/test_postclose_summary_handoff.py`, `src/tests/test_build_tuning_monitoring_parquet.py` | required source hashes, JSONL→Parquet route/session/venue round trip | finalization/report 재생성 금지 |
| `AM-S25` | wrapper/cron label·preflight·재사용 hash 갱신 | AM-S22/S23/S24A/S24B, `deploy/run_threshold_cycle_postclose.sh`, `deploy/install_stage2_ops_cron.sh`, `deploy/install_market_opportunity_census_cron.sh`, `deploy/install_eod_data_chain_cron.sh`, `deploy/run_market_opportunity_census_intraday.sh` | 앞의 shell 5개, `src/tests/test_threshold_cycle_wrappers.py` | 5개 `bash -n`, exact cron rows/labels, new hash invalidation 관련 test | 실제 cron 설치·postclose 실행 금지; finalization은 generic regression만 |
| `AM-S26` | 승인 후 고정 release/canary 운영 | 모든 코드 task PASS와 §15 승인 | 소스 수정 없음; 승인된 release/receipt 경로만 | exact root/commit/PID/pin/source/order reconciliation | **코딩 task 아님. 명시적 배포 승인 없으면 실행 금지** |

`AM-S24A`와 `AM-S24B`는 서로 독립 호출이다. 한 호출에 함께 요청하지 않으며 둘 다 PASS한 뒤에만 `AM-S25`를 시작한다.

### 13.6 각 task의 변경량 상한

- production 파일: 원칙 1~3개, 명시된 예외 `AM-S16` 4개.
- shell 파일: `AM-S25`에 이름을 고정한 5개만 예외다. 여섯 번째 wrapper가 필요하면 새 task로 분리한다.
- test 파일: 원칙 1~3개. 기존 거대 test에 fixture 몇 개를 추가할 수 있으나 unrelated test 정리는 금지.
- 신규 production Python: 전체 계획에서 `session_contract.py`, `aftermarket_eligibility.py`, `aftermarket_reconciliation.py` 세 개뿐이다.
- 신규 정기 producer/service/report: 0개. reconciliation은 기존 owner가 쓰는 단일 runtime artifact이며 별도 daemon이 아니다.
- DB migration: additive only. historical rewrite/backfill job은 만들지 않는다.
- commit: 한 task당 reviewable commit 1개를 권고하되, 사용자가 commit을 지시하지 않으면 commit하지 않는다.
- diff가 task의 Write 상한을 넘으면 변경을 계속하지 않고 더 작은 후속 ID가 필요하다고 보고한다.

### 13.7 의도적으로 제거한 과잉 구현

다음은 원 설계에서 파생될 수 있지만 이번 목표에 필요하지 않아 구현 backlog에서 제외한다.

- 범용 다중거래소 plugin/framework.
- 새 market calendar 서비스 또는 휴장일 원격 provider.
- SOR 최적화 알고리즘·자체 best-execution engine.
- KRX/NXT 호가를 결합한 새 alpha/score/threshold.
- 실시간 venue 예측 또는 UNKNOWN venue 사후 추정 모델.
- 새 dashboard, Telegram 알림, 운영 UI.
- 과거 전기간 venue backfill crawler.
- 자동 canary 승인·자동 cap 확대·자동 rollback 수치.
- 기존 NXT 명칭 전체 rename과 역사 artifact rewrite.
- 범용 DB migration framework 또는 event bus 재설계.
- postclose chain 병렬화·성능 최적화.

필요성이 별도로 입증되면 새 설계/승인으로 다룬다. 현재 task의 “완성도 향상” 사유로 추가하지 않는다.

### 13.8 task 종료 판정

`PASS`는 해당 task의 코드/문서 contract와 targeted validation만 닫혔다는 뜻이다. 다음을 의미하지 않는다.

- downstream task 완료
- 전체 KRX 애프터마켓 구현 완료
- 배포/cron/PID 소비
- 실제 API 호환 확인
- 자연 주문/체결
- 비용 후 경제성

`BLOCKED` task는 같은 호출에서 우회 구현하거나 다음 task로 넘어가지 않는다. blocker가 해소된 뒤 같은 ID를 새 호출로 재개한다. `FAIL`은 작성한 변경 안에서 재현 가능한 결함이 남은 상태이며 PASS로 포장하지 않는다.

## 14. 테스트 매트릭스

### 14.1 시간·시행일

1. 2026-09-11 16:05 replay는 기존 NXT 결과 유지.
2. 2026-09-14 15:29:59, 15:30, 15:39:59 transition.
3. 15:40:00 NXT solo, `_NX`.
4. 15:59:59까지 dual로 조기 전환되지 않음.
5. 16:00:00 dual, integrated route.
6. 19:39:59 entry clock 허용 가능, 기존 추가 guard 유지.
7. 19:40:00 신규 BUY 금지.
8. 19:45:00 terminal exit state.
9. 20:00:00 closed, 신규 주문 0.
10. naive datetime/DST 무관 KST/휴장일/주말 fail-closed.

### 14.2 종목 자격

- NXT only, KRX-after only, both, neither.
- unknown/missing/conflict/stale previous-date.
- 관리·투자주의·거래정지·정리매매 등 raw flag 조합.
- ETF/ETN/기타 시장구분과 base-code/suffix 정규화.
- pagination 완전/중복 cursor/중단/부분 page.
- `is_nxt=false`가 KRX-after=true를 자동 의미하지 않음.

### 14.3 시세·scanner

- `_NX`, `_AL`, plain code의 route 분류.
- `_AL` event actual venue UNKNOWN.
- 동일 종목 KRX/NXT 응답 merge와 중복 신호 0.
- 한 route failure 시 PARTIAL, 전체 성공으로 표시하지 않음.
- 15:40~16:00 bar와 16:00 이후 bar 분리.
- route/epoch/reconnect/out-of-order/stale 상태.
- `0s` known/unknown VI·call auction·close state.

### 14.4 주문

- SOR after + type3가 broker call 전에 변환 또는 차단.
- 검증된 limit/best/priority/IOC/FOK 조합.
- unsupported conditional/midpoint/unknown type 차단.
- buy/sell clock 전달 일치.
- submit 직전 session transition 발생 시 전송 0.
- source/eligibility unknown 시 신규 entry 0.
- broker reject 뒤 route/type 자동 변경 재시도 0.
- cancel/modify가 exact original route/order number 유지.
- SOR response 자체로 actual venue를 채우지 않음.

### 14.5 lifecycle/recovery

- 15:30 KRX 미체결 release, NXT persistent.
- SOR parent와 KRX/NXT child split.
- partial fill + partial cancel + remaining 합계 보존.
- lost ACK, duplicate callback, restart, current ledger empty.
- child 하나 terminal인 동안 sibling open.
- 이전 거래일 order와 오늘 order 혼합 방지.
- 보유 수량/owner/custody 불변, duplicate sell 0.

### 14.6 AI·postclose

- legacy 두 cohort replay 불변.
- 신규 dual source-only cohort가 terminal report를 생성.
- dual cohort live candidate 생성 시 verifier 실패.
- 기존 NXT approval hash 재사용 시 실패.
- KRX fill/NXT fill/UNKNOWN 실제시장별 분리.
- full/partial, real/sim/probe/CF 분리.
- invalid profit/cost missing은 null, 0 대체 없음.
- raw row exclusion과 whole-input block 조건 구분.
- post-sell, missed, pyramid join에서 새 필드 손실 0.
- JSONL→Parquet→diff→archive 왕복 schema/hash 보존.
- DONE controller, handoff, finalization predecessor PASS/FAIL fixture.

### 14.7 wrapper·회귀

- 관련 pytest와 compile.
- shell `bash -n` 및 installer contract test.
- exact cron owner/행 수/시간/label 검증.
- contract code 변경 시 reusable artifact invalidation.
- 정규장 SOR·기존 NXT solo·기존 machine entry 결과 불변.
- `git diff --check`.
- 문서/checklist print-only parser.

## 15. 배포·canary·rollback

### 15.1 배포 순서

1. DB additive migration과 backward-compatible reader.
2. source/event producer dual-write.
3. report consumer가 old/new schema 모두 읽되 dual live는 차단.
4. order/reconciliation 코드 배포, 신규 dual entry OFF.
5. synthetic/exact-date source 관찰.
6. 별도 승인된 작은 canary만 SOR entry 활성화.
7. old compatibility field 제거는 충분한 retention window 뒤 별도 변경.

workspace를 직접 배포하지 않고 [runtime release routing](../runtime-release-routing.md)의 고정 release 절차를 따른다. 현재 사용자 작업트리의 변경을 이 구현에 포함하지 않는다.

### 15.2 canary acceptance

- exact PID root/commit/clean 상태.
- market contract/eligibility/approval hash 실제 소비.
- 15:40 solo와 16:00 dual 전환 receipt.
- SOR 요청 route와 실제 KRX/NXT fill venue 분리.
- 미체결·부분체결·cancel 수량 보존.
- 중복 주문, authority leak, unsupported type submit 0.
- postclose chain에서 새 cohort source-only/blocked 처리.
- 자연 표본의 비용 후 EV/순익은 충분한 완료 표본 뒤 별도 판정.

### 15.3 즉시 rollback 조건

- `_AL` 또는 SOR을 실제 NXT/KRX로 오귀속.
- unsupported order type가 broker에 도달.
- 15:30/16:00 경계 중복주문 또는 orphan order.
- owner/custody/quantity 불일치.
- 새 dual cohort가 승인 없이 live BUY.
- postclose가 UNKNOWN venue 행을 기존 NXT EV에 포함.
- schema mismatch를 silent skip하고 DONE 처리.

rollback은 신규 dual entry만 OFF로 돌리고 기존 주문·보유·미체결 reconciliation과 보호 청산은 계속한다. 상태 schema/ledger를 지우거나 이전 코드로 단순 downgrade하지 않는다. 신규 artifact를 읽지 못하는 이전 consumer로 되돌릴 때는 compatibility 검증이 먼저다.

## 16. 완료 정의와 미해결 blocker

### 16.1 코드 완료

- 중앙 세션/자격 계약과 모든 직접 producer/consumer 전환.
- 주문 boundary·SOR type·actual venue 불변식 구현.
- postclose strict chain과 schema/hash 갱신.
- review finding 0, targeted test/compile/bash/parser/diff check PASS.

### 16.2 배포 완료

- 검토된 고정 release 선택.
- 승인된 cron/systemd 설치.
- exact PID/root/commit/환경/정책 hash receipt.
- 기존 주문·보유·원장 보존.

### 16.3 자연 운영 완료

- 9/14 이후 실제 session-state/source 전환 관찰.
- SOR 요청과 실제 KRX/NXT 체결 귀속 대사.
- KRX 정규장 미체결 비이월과 NXT 잔존 주문의 실제 reconciliation.
- 20:05 이후 postclose 전체 chain exact-date terminal.

### 16.4 경제성 완료

- `COMPLETED + valid profit_rate`의 비용 후 EV/순익.
- KRX/NXT actual venue, solo/dual session, full/partial, owner별 분리.
- UNKNOWN/cost-null coverage 공개.
- 기존 승인 cohort와 새 canary version을 섞지 않은 판정.

### 16.5 구현 전 반드시 닫을 blocker

| blocker | owner evidence | closure test |
| --- | --- | --- |
| Kiwoom 세션별 주문유형 code 미확정 | 최신 공식 spec/portal/broker notice | route×side×type fixture와 preflight PASS |
| KRX-after 종목 자격 필드 미확정 | 공식 종목목록/API raw payload | exact-date ledger completeness PASS |
| `0s` 새 상태 enum 미확정 | 공식 realtime 문서/관측 packet | known transition fixture, unknown fail-closed |
| SOR parent/child 실제시장 귀속 일부 미정 | `ka10075`/계좌 주문 receipt | partial/cancel/restart 수량·identity 보존 |
| 일봉 종가 의미 미확정 | `ka10081` 최신 문서와 9/14 표본 | regular close/after close 필드 분리 검증 |
| 신규 live 권한 없음 | immutable approval artifact | dual cohort exact scope/hash 승인 |

## 17. 전수점검 범위 판정

### 17.1 수정 필수 범주

- 세션/시간 resolver
- scanner와 시세 request route
- WebSocket session-state normalization
- 주문 route/type preflight
- 미체결/부분체결/cancel/restart reconciliation
- sniper holding/terminal exit
- widget/manual/web/gateway/engine
- 종목 자격 producer와 DB
- execution/post-sell receipts
- AI input/cohort/quality/live-policy/rollout
- funnel/missed/pyramid/source-quality/calibration/daily report
- prompt optimizer/consumer/controller/verifier
- cron labels, observation coverage, reusable input hashes

### 17.2 회귀검증 중심 범주

- regular-only Samsung/low-price machine entry
- runtime approval summary/control tower/key lineage/conversion lane
- tuning monitoring Parquet/diff/archive
- postclose summary handoff/finalization/error detector/dashboard archive
- generic log cleanup/locking/predecessor wait

### 17.3 문자열·상수 전수검색 후속 inventory

운영 Python/shell에서 `NXT_AFTERMARKET`, `nxt_aftermarket`, `NXT_1600`, `NXT close`, `krx_only_outside_krx_regular_session`, KRX/NXT 고정 allowlist를 전수검색했다. 아래는 §8·§10의 대표 owner 밖에서 추가로 확인한 경로와 구현 판정이다. 단순 문자열 치환은 금지한다.

**세션 또는 route 의미를 직접 바꾸는 경로**

- `src/engine/kiwoom_sniper_v2.py`: 새 중앙 clock/context를 생성해 handler에 전달.
- `src/engine/sniper_trade_utils.py`: `nxt_aftermarket_early_sell` 분류와 route validation을 dual session 계약으로 전환.
- `src/scanners/scanner_source_census.py`: request venue와 실제 시장을 분리하고 integrated source coverage를 보존.
- `src/engine/scalping/entry_context_intraday_probe.py`: `NXT_AFTERMARKET` preflight cohort를 solo/dual로 분리.
- `src/engine/scalping/ai_input_quality_baseline_replay.py`: 과거 legacy replay와 시행일 이후 dual schema를 version으로 분리.
- `src/engine/scalping/entry_candidate_lifecycle_state.py`: expected session을 venue 하나로 추론하지 않음.
- `src/engine/scalping/entry_recheck_policy.py`: 기존 `NXT|NXT_AFTERMARKET` 승인 범위가 dual로 확장되지 않게 함.
- `src/engine/scalping/strategy_owner_components.py`: legacy `nxt_aftermarket` component mapping의 compatibility projection 추가.
- `src/engine/scalping/micro_reversion/contracts.py`: `_AL`의 반환값을 실제 venue가 아닌 data route로 명명·소비.
- `src/engine/scalping/micro_reversion/forward_collector.py`: time-only NXT-after 분류 제거.
- `src/engine/scalping/micro_reversion/ai_quality_bridge.py`: route venue allowlist와 actual venue allowlist를 분리.
- `src/engine/monitoring/pure_market_kiwoom_backfill.py`: 16:00 이후 NXT 단일 backfill 금지, route별 provenance 보존.
- `src/engine/monitoring/pure_market_adaptive_opportunity_replay.py`, `pure_market_reversal_replay.py`: historical/versioned session windows 적용.
- `src/engine/monitoring/widget_execution_quality.py`: supported session과 실제 체결시장 축 추가.
- `src/engine/monitoring/widget_mechanical_entry_replay.py`, `widget_paired_policy_replay.py`: dual session을 과거 NXT arm으로 합치지 않음.
- `src/engine/monitoring/widget_collector_expansion_recommendation.py`: 20:00 종료 상수는 유지하되 source scope와 coverage를 dual로 전환.
- `src/trading/widget_auto_trade/policy.py`: supported session/venue map에서 session=>venue 단일 매핑 제거.
- `deploy/run_market_opportunity_census_intraday.sh`: wrapper 인자·artifact label·source contract version 전달.

**물리 거래소 집합 `KRX,NXT`를 유지하되 의미 회귀를 확인할 경로**

- `src/utils/kiwoom_utils.py`의 inventory normalization completeness.
- `src/engine/sniper_s15_fast_track.py`, `src/engine/sniper_sync.py`의 양 거래소 inventory/custody 확인.
- `src/trading/config/symbol_owner_policy.py`, `src/trading/order/symbol_owner_policy_apply.py`, `symbol_owner_policy_auto_apply.py`의 verified exchange proof.
- `src/trading/order/owner_custody_registry.py`의 migration receipt. 여기에 `SOR`을 세 번째 물리 거래소로 추가하지 않는다.
- `src/trading/order/adaptive_exit/arbitration.py`, `group_whole_exit.py`의 source-final-exit 실제 route 검증. scope route `SOR`과 체결/시세의 물리 `KRX|NXT`를 계속 구분하되 새 session enum을 수용한다.
- `src/engine/scalping/microstructure_reaction_context.py`, `src/engine/monitoring/scalping_avg_down_recovery_calibration.py`의 actual-venue 필터. UNKNOWN 제외량과 coverage를 추가한다.
- `src/engine/monitoring/samsung_widget_entry_notify.py`의 `nxt_aftermarket_*` 사유 문자열은 역사 receipt 호환을 위해 유지하고 신규 dual 사유를 별도 추가한다.

이 inventory에 대응하는 기존 테스트 파일도 동일 검색 결과를 기준으로 갱신한다. 특히 `test_kiwoom_websocket.py`, `test_scalping_scanner_candidate_pool.py`, `test_widget_*`, `test_ai_*`, `test_buy_funnel_sentinel.py`, `test_holding_exit_sentinel.py`, `test_observation_source_quality_audit.py`, `test_main_ai_prompt_*`, `test_threshold_cycle_preopen_apply.py`, `test_threshold_cycle_wrappers.py`의 과거 기대값을 일괄 치환하지 않고 시행일 전 fixture를 보존한 채 9/14 fixture를 추가한다.

### 17.4 이번 설계에서 실행하지 않은 것

- 거래 코드 수정
- DB migration 실행
- 실제 Kiwoom API/auth/account/order 호출
- 실주문·취소·정정
- bot/service 재기동
- cron/systemd 설치
- threshold/provider/cap/quantity/정책 변경
- postclose report 재생성
- 장중/장후 모니터링 절차 실행
- 외부 Project/Calendar sync

이 경계를 지켜야 “코드 준비”, “배포”, “실제 PID 소비”, “자연 체결”, “장후 체인 성공”, “비용 후 경제성”을 서로 다른 증거로 판정할 수 있다.
