# position_tag 영향도 점검 및 전략별 기본 태그 정규화

## 목적

`position_tag`가 스캘핑과 스윙에서 모두 `MIDDLE`을 기본값으로 사용하던 구조를 점검하고, 실제 매수/매도 로직에 미치는 영향과 이번 1차 개선 범위를 정리한다.

이 문서는 현재 코드 기준으로 작성한다.

## 요약

기존 구조에서 가장 큰 문제는 두 가지였다.

1. `MIDDLE`이 `SCALPING`, `KOSPI_ML`, `KOSDAQ_ML` 모두의 공용 기본값이라 의미가 모호했다.
2. active target 관리가 사실상 종목코드 중심이라 같은 종목의 스캘핑/스윙 전략이 서로 덮일 수 있었다.

이번 1차 개선에서는 `position_tag`를 전략별 기본 태그로 정규화하고, active target 중복 기준을 `code + strategy`로 상향했다.

핵심 결과는 아래와 같다.

- legacy `MIDDLE`은 내부에서 전략별 기본 태그로 정규화된다.
- `SCALPING` 기본 태그는 `SCALP_BASE`
- `KOSPI_ML` 기본 태그는 `KOSPI_BASE`
- `KOSDAQ_ML` 기본 태그는 `KOSDAQ_BASE`
- 같은 종목이라도 전략이 다르면 active target 공존이 가능해졌다.
- 스캘핑 매도 후 revive 시 태그가 무조건 `MIDDLE`로 초기화되던 문제가 제거됐다.

## 이번에 반영한 변경

### 1. 전략별 기본 태그 정규화 레이어 추가

공통 정규화 함수는 아래 파일에 추가했다.

- [src/engine/sniper_position_tags.py](/home/ubuntu/KORStockScan/src/engine/sniper_position_tags.py)

이 파일은 아래 책임을 가진다.

- 전략 정규화: `SCALP` -> `SCALPING`
- 전략별 기본 태그 계산
- legacy `MIDDLE`을 전략별 기본 태그로 정규화
- `code + strategy` 기준 identity 생성

### 2. DB 저장/조회 시 기본 태그 정규화

관련 파일:

- [src/database/db_manager.py](/home/ubuntu/KORStockScan/src/database/db_manager.py)

반영 내용:

- `save_recommendation()`에서 `strategy`와 `position_tag`를 함께 정규화
- `register_manual_stock()`의 기본 태그를 `SCALP_BASE` 계열로 전환
- `get_active_targets()`에서 `position_tag`를 전략 기준으로 정규화
- `get_active_targets()`의 중복 제거 기준을 `code`에서 `code + strategy`로 변경

핵심 위치:

- [src/database/db_manager.py](/home/ubuntu/KORStockScan/src/database/db_manager.py#L156)
- [src/database/db_manager.py](/home/ubuntu/KORStockScan/src/database/db_manager.py#L209)
- [src/database/db_manager.py](/home/ubuntu/KORStockScan/src/database/db_manager.py#L297)

### 3. 조건검색식 편입 로직 정규화

관련 파일:

- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py)

반영 내용:

- 조건검색 profile의 기본 스캘핑 태그를 `SCALP_BASE` 계열로 전환
- `scalp_open_reclaim_01`은 전용 태그 `OPEN_RECLAIM` 사용
- `kospi_*_swing_01`은 기본 스윙 태그 `KOSPI_BASE` 계열로 정규화
- active target 중복 체크를 `code + strategy` 기준으로 변경
- DB 레코드 조회도 `rec_date + stock_code + strategy` 기준으로 분리
- 기본 태그 여부 판단을 문자열 `MIDDLE` 비교 대신 정규화 함수로 대체

핵심 위치:

- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L110)
- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L243)
- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L372)
- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L537)
- [src/engine/sniper_condition_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_condition_handlers.py#L734)

### 4. 상태머신의 매수/매도 분기에서 태그 정규화

관련 파일:

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py)

반영 내용:

- 매수 감시 진입 시 `position_tag`를 전략별 기본 태그로 정규화
- 스윙 청산의 `BREAKOUT`, `BOTTOM` 분기 전에 태그 정규화 적용
- 엔진 부팅/DB polling 시점에 active target의 태그를 정규화
- 메모리 신규 편입 시 중복 기준을 `code + strategy`로 변경

핵심 위치:

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L661)
- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L1993)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L421)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L890)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L935)

### 5. 체결 후 revive / preset TP 흐름 정리

관련 파일:

- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py)

반영 내용:

- 스캘핑 preset TP 자동 세팅 조건을 `SCALPING + 기본 태그` 기준으로 전환
- 스캘핑 매도 후 revive 시 기존 태그를 보존
- revive 신규 DB 레코드도 기존 태그를 유지

핵심 위치:

- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L504)
- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L619)
- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L708)

## position_tag별 매수/매도 영향 매트릭스

아래 표는 현재 코드 기준이다.

| position_tag | 주 전략 | 매수 영향 | 매도 영향 | 후처리 영향 | 비고 |
|---|---|---|---|---|---|
| `SCALP_BASE` | `SCALPING` | 일반 스캘핑 기본 진입 경로 | 일반 스캘핑 청산 경로 | preset TP 자동 세팅 대상 | legacy `MIDDLE`은 내부적으로 여기에 매핑 |
| `OPEN_RECLAIM` | `SCALPING` | `09:03~09:20` 조건검색 전용 태그 | 현재 전용 청산 분기 없음 | 기본 스캘핑과 동일하게 보유 관리 | `scalp_open_reclaim_01` 전용 |
| `VCP_CANDID` | `SCALPING` | 당일 매수 차단 | 직접 영향 작음 | 이후 `VCP_SHOOTING` 승격 대기 | 감시 전용 태그 |
| `VCP_SHOOTING` | `SCALPING` | VCP 승격 후 감시 시작 | 직접 영향 작음 | VCP 흐름 유지 | `VCP_CANDID -> VCP_SHOOTING` |
| `VCP_NEXT` | `SCALPING` | `09:00`부터 시작, 일반 스캘핑보다 빠름 | 직접 영향 작음 | 익일 예약 진입 의미 | 일반 스캘핑과 시작 시각 다름 |
| `KOSPI_BASE` | `KOSPI_ML` | 일반 코스피 스윙 기본 진입 경로 | 장세 기준 손절/청산 경로 | 리포트/보유 관리 기본 태그 | legacy `MIDDLE`은 내부적으로 여기에 매핑 |
| `KOSDAQ_BASE` | `KOSDAQ_ML` | 일반 코스닥 스윙 기본 진입 경로 | 코스닥 스윙 청산 경로 | 리포트/보유 관리 기본 태그 | legacy `MIDDLE`은 내부적으로 여기에 매핑 |
| `BREAKOUT` | `KOSPI_ML` | 현재 진입 영향은 제한적 | 전용 손절선 사용 | 스윙 보유 의미 강화 | 청산 영향 큼 |
| `BOTTOM` | `KOSPI_ML` | 현재 진입 영향은 제한적 | 전용 손절선 사용 | 스윙 보유 의미 강화 | 청산 영향 큼 |
| `S15_CANDID` | fast-track 계열 | 일반 WATCHING 진입과 별도 | 일반 청산과 분리 | armed 후보 관리 | 메인 스캘핑과 분리 |
| `S15_SHOOTING` | fast-track 계열 | fast-track 즉시 실행 | 별도 흐름 | shadow/armed 상태 사용 | 특수 실행 경로 |
| `S15_FAST*` | fast-track 계열 | 일반 진입 분기 밖 | 별도 흐름 | 상태 추적용 | 특수 시스템 태그 |

## 실제 영향도가 큰 분기

### 1. 매수 시작 시각

스캘핑 기본 태그는 `09:03`, `VCP_NEXT`는 `09:00`부터 시작한다.

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L666)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L427)

### 2. 스캘핑 진입 차단

`VCP_CANDID`는 WATCHING 상태여도 당일 진입을 막는다.

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L709)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L456)

### 3. 스윙 청산 손절선

`KOSPI_ML`은 `BREAKOUT`, `BOTTOM`일 때만 전용 손절선을 쓴다.

- [src/engine/sniper_state_handlers.py](/home/ubuntu/KORStockScan/src/engine/sniper_state_handlers.py#L1993)
- [src/engine/kiwoom_sniper_v2.py](/home/ubuntu/KORStockScan/src/engine/kiwoom_sniper_v2.py#L680)

### 4. 스캘핑 체결 후 preset TP

기존에는 `SCALPING + MIDDLE`일 때만 붙었지만, 이제는 `SCALPING + 기본 태그` 기준으로 붙는다.

- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L504)
- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L619)

### 5. 스캘핑 revive 태그 보존

기존에는 revive 시 `MIDDLE`로 강제 초기화했지만, 이제는 기존 태그를 유지한다.

- [src/engine/sniper_execution_receipts.py](/home/ubuntu/KORStockScan/src/engine/sniper_execution_receipts.py#L708)

## 개선 전후 비교

### 개선 전

- `MIDDLE`이 스캘핑/스윙 공용 기본값
- active target 로드 시 `code` 기준 dedupe
- 조건검색 편입도 사실상 종목코드 기준으로 겹치면 스킵
- 스캘핑 revive 시 태그가 `MIDDLE`로 유실

### 개선 후

- legacy `MIDDLE`은 내부에서 전략별 기본 태그로 정규화
- active target dedupe는 `code + strategy`
- 조건검색 편입도 `code + strategy` 기준 중복 체크
- revive 시 기존 태그 유지

## 남아 있는 리스크와 후속 후보

### 1. DB 컬럼 기본값은 여전히 `MIDDLE`

모델 정의상 `position_tag`의 DB server default는 아직 `MIDDLE`이다.

- [src/database/models.py](/home/ubuntu/KORStockScan/src/database/models.py#L86)

다만 현재 주요 생성 경로는 모두 애플리케이션 레벨 정규화를 거치므로, 운영상 직접 영향은 제한적이다.  
후속으로는 아래 둘 중 하나를 택할 수 있다.

- DB default는 legacy 호환용으로 유지
- 신규 스키마 개편 시 `position_tag` nullable + 앱 레벨 강제 지정 구조로 전환

### 2. 스캐너 원천 태그는 아직 일부 `MIDDLE` 생성

일부 스캐너는 여전히 `MIDDLE` 문자열을 생성할 수 있다.

- [src/scanners/final_ensemble_scanner.py](/home/ubuntu/KORStockScan/src/scanners/final_ensemble_scanner.py#L270)
- [src/scanners/kosdaq_scanner.py](/home/ubuntu/KORStockScan/src/scanners/kosdaq_scanner.py#L188)

현재는 DB 저장 시 정규화되므로 즉시 문제는 아니지만, 후속으로 스캐너 원천 출력도 전략별 기본 태그로 맞추는 편이 더 명확하다.

### 3. 태그별 전용 진입/청산 정책은 아직 제한적

이번 1차는 공용 `MIDDLE` 제거와 전략 충돌 완화가 목적이었다.  
향후 필요하면 아래처럼 태그별 정책을 더 세분화할 수 있다.

- `OPEN_RECLAIM` 전용 청산 규칙
- `SCALP_STRONG`, `SCALP_AFTERNOON` 등 세부 스캘핑 태그
- `KOSPI_BASE`, `KOSDAQ_BASE` 별 리포트/통계 분리

## 테스트 및 검증

추가한 테스트:

- [src/tests/test_position_tag_normalization.py](/home/ubuntu/KORStockScan/src/tests/test_position_tag_normalization.py)
- [src/tests/test_condition_open_reclaim.py](/home/ubuntu/KORStockScan/src/tests/test_condition_open_reclaim.py)

검증 결과:

- `python3 -m compileall` 통과
- `pytest`는 현재 환경에 설치되어 있지 않아 실행 불가

## 권장 다음 작업

1. 스캐너 원천 출력의 `MIDDLE`도 전략별 기본 태그로 변경
2. `position_tag`별 진입/청산 정책을 문서 기준으로 데이터화
3. 리포트 계층에서 `SCALP_BASE`, `OPEN_RECLAIM`, `BREAKOUT`, `BOTTOM` 등을 별도 집계 가능하게 확장
