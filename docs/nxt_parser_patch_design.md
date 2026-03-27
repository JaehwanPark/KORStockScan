# NXT 대상종목 파싱 로직 개선안

## 문제 요약

현재 `fetch_nxt_target_codes()`는 NXT 공식 페이지 HTML 전체에서 `A123456` 또는 `123456` 패턴을 정규식으로 긁어 성공 여부를 판단한다.
이 방식은 다음 문제가 있다.

1. 잘못된 페이지에서도 우연히 1~3개의 6자리 숫자를 잡으면 성공처럼 보일 수 있다.
2. 공식 페이지가 서버 렌더링 테이블 대신 JS/비동기 방식으로 채워지면 단순 regex는 거의 실패한다.
3. `len(codes) > 0` 수준의 느슨한 성공 판정은 오탐을 만들기 쉽다.

## 목표

- source of truth는 계속 `https://www.nextrade.co.kr/menu/marketData/menuList.do`
- 파싱은 **HTML 테이블 우선 -> inline script/JSON fallback -> 전체 regex 최후 fallback** 순으로 강화
- 성공 조건은 최소 임계치(`MIN_EXPECTED_NXT_CODES`) 이상일 때만 인정
- 결과가 1개/3개처럼 비정상적으로 적으면 **성공 처리하지 않고 DB fallback** 으로 넘김

## 권장 변경

### 1. 다단계 파싱 전략

#### 1단계: HTML 테이블 행 기반 파싱
- `BeautifulSoup`로 `<table>`, `<tr>`, `<td>`를 순회
- 각 row text에서 `A123456` 또는 `123456`을 찾고, 종목명 열이 함께 있는 row만 우선 채택
- 페이지 구조가 살아있다면 가장 신뢰도 높음

#### 2단계: inline script / JSON-like 패턴 파싱
- HTML `<script>` 또는 본문 문자열에서 다음 패턴 탐색
  - `A123456`
  - `"isuSrdCd":"A123456"`
  - `"stockCode":"123456"`
- JS 렌더링용 데이터가 HTML에 심겨 있으면 여기서 회수 가능

#### 3단계: 전체 regex fallback
- HTML 전체에서 6자리 숫자 추출
- 단, 최소 개수 임계치 이상일 때만 채택

### 2. 성공 조건 강화

성공 기준을 예를 들어 아래처럼 둔다.

- `MIN_EXPECTED_NXT_CODES = 100`

이 기준보다 적으면:
- 성공 처리하지 않음
- 경고 로그 출력
- DB 최신 거래일 `is_nxt` fallback 사용

### 3. 로그 개선

기존:
- `✅ NXT 대상 종목 목록 수집 성공: 1개`

개선:
- `⚠️ NXT 코드 수집 결과가 비정상적으로 적음: 3개 (page parse)`
- `✅ NXT 대상 종목 목록 수집 성공: 647개 (strategy=table)`

즉, **몇 개를 수집했는지**뿐 아니라 **어떤 파싱 전략이 성공했는지**도 로그에 남긴다.

## 구현 포인트

### 추가 함수
- `_normalize_stock_code(raw)`
- `_extract_codes_from_table(html)`
- `_extract_codes_from_scripts(html)`
- `_extract_codes_by_regex(html)`

### 메인 함수
- `fetch_nxt_target_codes()`는 위 세 전략을 순서대로 실행
- 가장 먼저 임계치를 넘는 전략을 성공으로 채택
- 끝까지 실패하면 예외를 발생시켜 상위 fallback 로직이 동작하게 함

## 기대 효과

- 1개/3개 오탐 성공 문제 제거
- 정적 HTML 구조 변경에도 좀 더 강해짐
- 완전한 JS 렌더링 페이지라면 여전히 실패할 수 있지만, 이 경우도 **조용한 오탐 성공 대신 명시적 실패**가 되어 운영 안전성이 높아진다.

## 한계

페이지가 진짜로 브라우저에서만 XHR/JSON으로 데이터를 받아 테이블을 채우고, HTML 소스에 그 데이터가 전혀 없으면 이 파서도 실패할 수 있다.
그 경우에는 실제 XHR 엔드포인트를 찾아 직접 호출하거나 브라우저 렌더링 기반 수집으로 전환해야 한다.
