# KRX 애프터마켓·SOR 워이어 계약 정합성 게이트 (AM-S00)

작성일: 2026-09-11T16:06:36+09:00
최신 재검증: 2026-09-12T09:54:32+09:00

목표: [AM-S00](../proposals/krx-aftermarket-sor-detailed-implementation-design-2026-09-11.md#13.5-%EC%9E%91%EC%97%85-%ED%8C%A8%ED%82%B7) "9/14 공식 wire 계약 동결" 수행 근거를 단일 증거 문서로 고정.

구현 실행범위: `docs/audit-reports/2026-09-11-krx-aftermarket-kiwoom-contract-gate.md` 신규 생성 1건.

## 1. 구현 위치/루트 확인

요청 조건에 따라 실행 루트는 `git rev-parse --show-toplevel`로 확인했다.

- repository root: `/home/ubuntu/KORStockScan` (일치)
- 선택 배포본/고정 release/실행 PID source tree는 본 수정에서 직접 편집하지 않음.

## 2. 공식 Kiwoom 최신 revision 점검

`git ls-remote https://github.com/Kiwoom-Securities/Kiwoom-REST-API.git refs/heads/main`로 최신 `main` SHA를 재확인했다.

- upstream SHA: `234560d213acd8871ae344b5481aecd2f30287fa`
- inspection timestamp: 2026-09-12T09:54:32+09:00 (KST)
- upstream commit date: 2026-09-01T15:08:20+09:00
- `docs/kiwoom-api-data-contract.md`의 Official Kiwoom Reference Gate 항목과 상충되지 않음.

참조한 공식 경로:

- `https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/_data/kiwoom_api_spec.json`
- `https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/specs.py`
- `https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/core/ws_client.py`
- `https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa/kiwoom/realtime/stream.py`
- `https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/234560d213acd8871ae344b5481aecd2f30287fa/postman/kiwoom-openapi.postman_collection.json`

## 3. 확인된 공식 wire 사실

### 3.1 주문/제어 REST 계약

- 주문 공통 endpoint: `POST /api/dostk/ordr` (domestic, production domain)
  - `kt10000`(buy), `kt10001`(sell), `kt10003`(cancel)
- order request 공통 필드(샘플)
  - `dmst_stex_tp`
  - `stk_cd`
  - `ord_qty`(단위: 1주)
  - `ord_uv`(단위: 원)
  - `trde_tp`
- order response 공통 필드(샘플)
  - `ord_no`, `dmst_stex_tp`
- cancel request 필드
  - `orig_ord_no`, `cncl_qty`
- cancel response 핵심 필드
  - `ord_no`, `base_orig_ord_no`, `cncl_qty`

### 3.2 주문 route 필드 및 허용 값

- `dmst_stex_tp`
  - `KRX`, `NXT`, `SOR` (요청)
- `trde_tp`(주문유형) 공식 열거
  - `0:보통`, `3:시장가`, `5:조건부지정가`, `81:장마감후시간외`, `61:장시작전시간외`, `62:시간외단일가`, `6:최유리지정가`, `7:최우선지정가`, `10:보통(IOC)`, `13:시장가(IOC)`, `16:최유리(IOC)`, `20:보통(FOK)`, `23:시장가(FOK)`, `26:최유리(FOK)`, `28:스톱지정가`, `29:중간가`, `30:중간가(IOC)`, `31:중간가(FOK)`
- `trde_tp`의 세션별 허용 matrix는 동일 spec에서 명시하지 않는다. 로컬 안전 계약은 사용자 승인에 따라 정규장 종료 후 15:30~16:00 전환 구간을 차단하고, 16:00~20:00 통합 애프터마켓에서 `0`/`00`/`6`만 허용하며 `3`은 broker 호출 전에 `6`으로 변환하고 나머지는 차단한다.

### 3.3 연속조회/헤더

- request header: `cont-yn`
- request header: `next-key`
- 공식 문서에서 설명: `cont-yn=Y` 시 후속 조회 키 사용

### 3.4 보유조회/미체결 조회

- `ka10075` (미체결요청) request
  - `all_stk_tp`, `trde_tp`, `stk_cd`, `stex_tp`
- `ka10075` response
  - `stex_tp`(`0:통합`, `1:KRX`, `2:NXT`)
  - `stex_tp_txt`
  - `sor_yn` (`Y`, `N`)
- `ka10075`는 주문 route 구간(통합/KRX/NXT) 식별은 제공하나, SOR 주문의 실제 체결시장에서 `parent/child`를 완전 결속하는 항목은 별도 명시 없음.

### 3.5 종목 자격 원천

- `ka10099` 응답은 예시로 `auditInfo`, `state`, `orderWarning`, `marketCode`, `nxtEnable`을 제공
- `nxtEnable`은 NXT 가용성 신호로 활용 가능성이 있으나 `KRX 애프터마켓` 자격 정식 필드로의 공식 매핑은 추출되지 않음

### 3.6 실시간 0s enum

`0s` 항목의 response field에서 값 의미는 `215(장운영구분)`와 `214(장시작예상잔여시간)`에 대해 다음이 공식 문서화됨:

- `215`
  - `0`: 장시작전 알림
  - `3`: 장시작
  - `2`: 장마감 알림
  - `4`: 장마감
  - `8`: 정규장마감(거래소 수신 15:30 이후)
  - `9`: 전체장마감(거래소 수신 18:00 이후)
  - `a`: 시간외 종가매매 시작(15:40)
  - `b`: 시간외 종가매매 종료(16:00)
  - `c`: 시간외 단일가 시작(16:00)
  - `d`: 시간외 단일가 종료(18:00)
  - `T`: NXT 에프터마켓 단일가 시작 알림
  - `U`: NXT 에프터마켓 시작 알림
  - `V`: NXT 에프터마켓 종료 알림
  - 기타 (선옵 계열 `e,f,o,s` 등) 포함
- `214`
  - `HHmmss` 형식 문자열

## 4. 공식 미확정 항목 자체검사

AM-S00 문서 요건의 `미확정 항목 별 BLOCKED_OFFICIAL_CONTRACT` 조건에 따라 아래는 아직 공식적으로 확정되지 않아 `BLOCKER`로 분리한다.

1. **세션별 주문유형 로컬 안전표(해소)**
   - 공식 enum과 사용자 승인 계약을 결속했다. 정규장은 15:30까지 현행 유지, 15:30~16:00 주문 차단, 16:00~20:00 KRX/NXT 통합 애프터마켓이며 NXT 단독 구간은 없다. route는 `KRX|NXT|SOR`, 주문유형은 `0|00|6`, `3->6` 사전 변환, 그 밖의 유형은 차단한다. 19:40 이후 신규 BUY는 차단하고 기존 보유 SELL만 허용한다.

2. **KRX 애프터마켓 종목 자격 정식 필드**
   - `ka10099`는 NXT 지표(`nxtEnable`) 등은 확인되나, KRX 애프터마켓 개별 자격용 키/검증 규칙은 미확정

3. **SOR parent/child 실제시장 귀속 결속 규칙의 완결성**
   - `ka10075`는 `stex_tp` 및 `sor_yn`을 제공하나, 신규 SOR 주문/자식 주문의 실제 venue 결속을 endpoint 단에서 완결로 선언하는 규격은 미확정

4. **`0s` 상태 전이(transition) 정합성**
   - 값 목록은 확인되었으나, 상호 전이 규칙과 VI/호가시간 구간별 정량 규정은 공식 문서에서 완전 보장되지 않음

## 5. AM-S00 판정

- 공식 wire 계약의 현재 상태는 문서화되었으며, 주문유형 로컬 matrix는 사용자 승인으로 해소했다. `KRX aftermarket eligibility`, SOR parent/child 실제시장 결속, `0s` 전이의 공식 미확정은 별도 blocker로 유지한다.
- 본 태스크는 `code` 또는 `runtime` 변경 없이 증빙 생성만 수행.

## 6. 후속 지침

- 다음 태스크(`AM-S01`) 진입 전, 위 블로커는 각각 `BLOCKED_OFFICIAL_CONTRACT` 상태로 유지되어야 하며, 외부 공식 소스의 갱신/명시된 증빙 보강 시에만 해제 검토 가능.
