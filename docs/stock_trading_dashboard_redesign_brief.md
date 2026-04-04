# CODEX 리디자인 작업 지시서: 주식 트레이딩 시스템 모니터링 대시보드

출처 화면: `web application/stitch/projects/17546666996975243328/screens/f39125ee651745ccafafb4a0e0cc9825`

## 1. 프로젝트 목표
- 기존 CODEX 생성 대시보드를 전문적이고 세련된 UI/UX로 전면 개편.
- 화이트(Light) 및 순수 블랙(Dark) 테마를 토글 버튼으로 전환 가능하도록 구현.
- 장시간 모니터링 시 눈의 피로도를 낮추는 전문 금융 터미널 스타일 지향.

## 2. 디자인 시스템 가이드

### A. 화이트 테마 (Equity Minimalist)
- 배경: `#F8FAFC` (Slate 50)
- 카드: `#FFFFFF` (White) / 부드러운 그림자 (`shadow-sm`)
- 강조색: Primary Blue (`#0053DB`), Success Green (`#10B981`), Danger Red (`#EF4444`)
- 폰트: Manrope (Headlines), Inter (Data/UI)

### B. 순수 블랙 테마 (Obsidian Terminal)
- 배경: `#000000` (Pure Black)
- 카드: `#111111` (Dark Charcoal) / 1px Ghost Border (`#333333`)
- 강조색: Emerald Green (`#10B981`), Crimson Red (`#E11D48`), Slate Blue (`#3B82F6`)
- 특징: 블루/퍼플 톤을 완전히 배제하고 고대비 텍스트 배치

## 3. 화면별 구성 및 API 매칭 가이드

### 1) 일일 전략 리포트 (Main)
- Endpoint: `/api/daily-report?date=YYYY-MM-DD`
- 주요 위젯:
- 핵심 KPI 카드 (순이익, 승률, 효율성 점수)
- 실시간 Market Flow (SPY) 라인 차트
- 우측 Alert Center (시스템 알림)
- 하단 Performance Matrix (전략별 실시간 상태 테이블)

### 2) 진입 게이트 플로우
- Endpoint: `/api/entry-pipeline-flow?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- 주요 위젯:
- 단계별 프로그레스 바 (Handshake, Encryption, Validation)
- 실시간 Condition Logs (터미널 스타일 로그 뷰)
- 시스템 부하 및 처리량 메트릭

### 3) 실제 매매 복기
- Endpoint: `/api/trade-review?date=YYYY-MM-DD&code=000000`
- 주요 위젯:
- 캔들스틱 차트 (진입/청산 지점 표시)
- 매매 요약 정보 (실현 손익, ROI, 수수료 등)
- Execution Lifecycle (주문 체결 타임라인)

### 4) 동적 체결강도
- Endpoint: `/api/strength-momentum?date=YYYY-MM-DD&since=HH:MM:SS&top=10`
- 주요 위젯:
- 상위 10개 종목 체결강도 인덱스 바
- Order Flow Pressure 게이지
- 종목별 모멘텀 핫스팟 차트

### 5) 성능 튜닝 모니터
- Endpoint: `/api/performance-tuning?date=YYYY-MM-DD&since=HH:MM:SS`
- 주요 위젯:
- 네트워크 지연시간 히스토그램 (Latency)
- CPU/Memory 리소스 사용량 게이지
- 노드별 상태 토폴로지 맵

## 4. 추가 구현 사항
- 테마 토글: 상단 네비게이션 우측에 해/달 아이콘 버튼 배치. 클릭 시 `html` 태그에 `dark` 클래스 토글.
- 광고 슬롯: `ad-slot-sidebar` (우측 하단), `ad-slot-inline` (콘텐츠 카드 사이) 클래스를 가진 빈 `div`를 미리 확보.
- 실시간 데이터: Flask 백엔드의 JSON 데이터를 주기적으로 fetch하여 UI를 업데이트하는 로직 필요.

## 5. 전달 파일 활용 방법
- 각 화면의 `</> View Code` 버튼을 통해 추출된 HTML/CSS를 CODEX에 제공하여 UI를 완성.
- 위 API 엔드포인트 명세를 참고하여 데이터 바인딩을 요청.
