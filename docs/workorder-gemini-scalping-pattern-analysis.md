# 작업지시서: Gemini 스캘핑 손실/수익 패턴 분석 전용 코드베이스 구축

작성일: 2026-04-17  
대상: Gemini (외부 분석 에이전트)  
목표: 지금까지 누적된 스캘핑 실적/이벤트 데이터를 AI 분석 가능한 형태로 정규화하고, 손실패턴/수익패턴을 기대값 관점에서 분해 분석한다.  
중요: 본 작업은 **분석 전용 코드베이스**로만 수행하며, 기존 운영 코드 변경은 금지한다.

---

## 1. 절대 제약 (필수)

1. 기존 운영 코드 수정 금지
- `src/`, `bot_main.py`, 운영 스크립트, 기존 테스트 파일 수정 금지.
- 기존 문서 갱신도 금지한다. 결과는 본 지시서에서 지정한 산출물 경로에만 생성한다.

2. 분석 전용 독립 디렉토리에서만 작업
- 아래 경로를 새로 만들고 그 안에서만 구현:
  - `analysis/gemini_scalping_pattern_lab/`
- 분석 코드/설정/출력은 모두 이 하위에만 저장한다.

3. 환경 변경 금지
- 패키지 설치/업그레이드/삭제 금지.
- 프로젝트 `.venv`의 기존 모듈만 사용한다.

4. 실전 동작 영향 금지
- 봇 재기동, 크론 수정, 운영 프로세스 제어 금지.
- 분석은 파일 읽기 기반 오프라인 수행만 허용한다.

---

## 2. 분석 범위

1. 기간
- 기본: 최근 20거래일.
- 최소: `2026-04-01` ~ `2026-04-17`.

2. 서버
- 로컬(main), 원격(remote) 분리 집계 후 비교.

3. 데이터 소스
- 거래/이벤트 로그 및 리포트 산출물(로컬 파일 기준).
- 손익 계산은 `COMPLETED + valid profit_rate`만 사용.
- `NULL`, 미완료, fallback 정규화 값은 손익 통계에서 제외.

4. 코호트 분리 (혼합 금지)
- `full_fill`
- `partial_fill`
- `split-entry`

5. 미진입 기회비용 분석 포함
- BUY 후 미진입을 아래 blocker로 분리:
  - `latency guard miss`
  - `liquidity gate miss`
  - `AI threshold miss`
  - `overbought gate miss`

---

## 3. 구현 요구사항 (분석 전용 코드베이스)

아래 구조를 `analysis/gemini_scalping_pattern_lab/`에 생성:

1. `README.md`
- 목적, 입력 데이터, 실행 방법, 출력물 설명.

2. `config.py`
- 분석 기간, 경로, 샘플링 옵션, 서버 구분 옵션 정의.

3. `build_dataset.py`
- 원천 로그/리포트에서 분석용 테이블 생성.
- 출력:
  - `outputs/trade_fact.csv`
  - `outputs/funnel_fact.csv`
  - `outputs/sequence_fact.csv`

4. `analyze_patterns.py`
- 손실/수익 패턴 Top N 도출.
- 패턴별:
  - 빈도
  - 평균/중앙 profit_rate
  - 총 기여손익
  - 공통 선행조건
  - 재현 조건

5. `build_llm_payload.py`
- AI 모델 입력용 JSON 생성:
  - `outputs/llm_payload_summary.json`
  - `outputs/llm_payload_cases.json`
- summary + 대표 케이스 원문 이벤트를 함께 구성.

6. `prompt_templates/`
- `loss_pattern_prompt.md`
- `profit_pattern_prompt.md`
- `ev_priority_prompt.md`

7. `run.sh`
- 전체 파이프라인 재현 실행 스크립트:
  - dataset 생성
  - 패턴 분석
  - LLM payload 생성

---

## 4. 데이터 스키마 요구사항

1. `trade_fact.csv` 최소 컬럼
- `server`
- `trade_id`
- `symbol`
- `entry_time`
- `exit_time`
- `held_sec`
- `entry_mode` (`full|partial|split-entry`)
- `exit_rule`
- `status`
- `profit_rate`
- `profit_valid_flag`

2. `funnel_fact.csv` 최소 컬럼
- `server`
- `date`
- `latency_block_events`
- `liquidity_block_events`
- `ai_threshold_block_events`
- `overbought_block_events`
- `submitted_events`

3. `sequence_fact.csv` 최소 컬럼
- `server`
- `trade_id`
- `event_seq` (요약 문자열)
- `partial_then_expand_flag`
- `multi_rebase_flag`
- `rebase_integrity_flag`
- `same_symbol_repeat_flag`

---

## 5. 품질 게이트

1. 분석 산출 전에 품질 리포트 필수 생성:
- `outputs/data_quality_report.md`

2. 품질 리포트 필수 포함 항목
- 총 거래수, `COMPLETED` 수, `valid_profit_rate` 수
- 제외 건수와 제외 사유
- 서버별 결측/파싱 실패 건수
- rebase 정합성 이상 건수

3. 실패 조건
- `profit_valid_flag=true` 표본이 서버별 30건 미만이면 결론을 확정하지 않고 `표본 부족`으로 표기.

---

## 6. AI 분석 실행 지침

1. 모델 입력은 2단 분리
- 요약 통계 입력 (숫자 중심)
- 대표 케이스 입력 (이벤트 시퀀스 중심)

2. 모델 요청사항
- 손실패턴 Top 5
- 수익패턴 Top 5
- 기대값 개선 우선순위 Top 5 (shadow-only/canary 순)

3. 금지사항
- 단순 승률 최적화 중심 결론 금지
- full/partial/split-entry 혼합 해석 금지
- 운영 코드 즉시 변경 제안 금지

---

## 7. 최종 산출물

아래 파일을 생성:

1. `analysis/gemini_scalping_pattern_lab/outputs/pattern_analysis_report.md`
- 형식: `판정 -> 근거 -> 다음 액션`
- 손실패턴/수익패턴/기회비용을 분리 보고.

2. `analysis/gemini_scalping_pattern_lab/outputs/ev_improvement_backlog.md`
- 실행 후보를 `shadow-only` 우선으로 정리.
- 각 항목에 `예상 기대값 개선 축`, `리스크`, `검증 지표` 포함.

3. `analysis/gemini_scalping_pattern_lab/outputs/run_manifest.json`
- 실행 시각, 입력 파일 목록, row count, 해시(가능하면) 기록.

---

## 8. 완료 기준 (Definition of Done)

1. 기존 코드베이스 무수정
- `src/` 이하 변경 0건.

2. 독립 분석 코드베이스 완성
- `analysis/gemini_scalping_pattern_lab/`만 신규/수정.

3. 재현성 확보
- `run.sh` 1회 실행으로 동일 산출물 재생성 가능.

4. 보고 품질 충족
- 손실/수익/기회비용이 분리 보고되고, 기대값 개선 우선순위가 제시됨.

---

## 9. 제출 형식

최종 제출 메시지는 아래 3개 섹션만 포함:

1. `판정`
2. `근거`
3. `다음 액션`

부록으로 생성 파일 목록만 덧붙인다.
