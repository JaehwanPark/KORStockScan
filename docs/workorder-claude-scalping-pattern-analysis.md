# 작업지시서: Claude 스캘핑 패턴 분석 전용 코드베이스 구축

작성일: 2026-04-17  
대상: Claude (외부 분석 에이전트)  
목적: 누적된 스캘핑 거래/이벤트 데이터를 기반으로 손실 패턴, 수익 패턴, 미진입 기회비용을 분해 분석하고 EV 개선 후보를 도출한다.  
원칙: 운영 코드와 분리된 독립 분석 코드베이스에서만 작업한다.

---

## 1. 필수 제약

1. 운영 코드 수정 금지
- `src/`, `bot_main.py`, 기존 운영 스크립트, 기존 테스트 파일 수정 금지.
- 기존 문서 직접 수정 금지. 분석 산출물은 지정된 신규 경로에만 생성.

2. 분석 전용 디렉토리 고정
- 아래 경로를 신규 생성 후 해당 경로에서만 작업:
  - `analysis/claude_scalping_pattern_lab/`

3. 환경 변경 금지
- 패키지 설치/업그레이드/삭제 금지.
- 프로젝트 `.venv`에 이미 존재하는 라이브러리만 사용.

4. 운영 영향 금지
- 봇 재기동, cron/workflow 수정, 운영 프로세스 제어 금지.
- 오프라인 파일 분석만 수행.

---

## 2. 분석 범위

1. 기간
- 기본: 최근 20거래일
- 최소 보장 구간: `2026-04-01 ~ 2026-04-17`

2. 서버 범위
- `local(main)`과 `remote`를 분리 집계 후 비교

3. 코호트 분리 (혼합 금지)
- `full_fill`
- `partial_fill`
- `split-entry`

4. 손익 집계 규칙
- 손익 계산은 `COMPLETED + valid profit_rate`만 사용
- `NULL`, 미완료, fallback 정규화 값은 손익 통계에서 제외

5. 기회비용 분해
- BUY 후 미진입은 다음 blocker로 분리:
  - `latency guard miss`
  - `liquidity gate miss`
  - `AI threshold miss`
  - `overbought gate miss`

---

## 3. 구현 산출물 (코드베이스 구조)

`analysis/claude_scalping_pattern_lab/`에 아래 파일/디렉토리를 생성:

1. `README.md`
- 실행 방법, 입력 경로, 출력물 설명

2. `config.py`
- 분석 기간, 입력 경로, 서버 옵션, 샘플링 옵션

3. `prepare_dataset.py`
- 로그/리포트에서 표준 분석 테이블 생성
- 출력:
  - `outputs/trade_fact.csv`
  - `outputs/funnel_fact.csv`
  - `outputs/sequence_fact.csv`

4. `analyze_ev_patterns.py`
- 손실/수익 패턴 Top N 추출
- 패턴별 빈도, 중앙값, 기여손익, 공통 선행조건 산출

5. `build_claude_payload.py`
- Claude 투입용 JSON 패키지 생성
- 출력:
  - `outputs/claude_payload_summary.json`
  - `outputs/claude_payload_cases.json`

6. `prompts/`
- `prompt_loss_patterns.md`
- `prompt_profit_patterns.md`
- `prompt_ev_prioritization.md`

7. `run_all.sh`
- 데이터 준비 -> 분석 -> payload 생성 일괄 실행

---

## 4. 스키마 요구사항

1. `trade_fact.csv` 필수 컬럼
- `server`
- `trade_id`
- `symbol`
- `entry_time`
- `exit_time`
- `held_sec`
- `entry_mode`
- `exit_rule`
- `status`
- `profit_rate`
- `profit_valid_flag`

2. `funnel_fact.csv` 필수 컬럼
- `server`
- `date`
- `latency_block_events`
- `liquidity_block_events`
- `ai_threshold_block_events`
- `overbought_block_events`
- `submitted_events`

3. `sequence_fact.csv` 필수 컬럼
- `server`
- `trade_id`
- `event_seq`
- `partial_then_expand_flag`
- `multi_rebase_flag`
- `rebase_integrity_flag`
- `same_symbol_repeat_flag`

---

## 5. 품질 게이트

1. 필수 품질 리포트 생성
- `outputs/data_quality_report.md`

2. 품질 리포트 포함 항목
- 총 거래수, `COMPLETED` 수, `valid_profit_rate` 수
- 제외 건수/사유
- 서버별 파싱 실패/결측
- 정합성 플래그 분포 (`cum_gt_requested`, `same_ts_multi_rebase`, `requested0_unknown`)

3. 표본 부족 기준
- 서버별 `profit_valid_flag=true`가 30건 미만이면 결론 확정 금지
- 보고서에 `표본 부족`을 명시하고 후속 수집 제안만 작성

---

## 6. Claude 분석 요청 규칙

1. 입력 방식
- 요약 통계 입력과 대표 케이스 입력을 분리해서 전달

2. Claude 출력 요구
- 손실 패턴 Top 5
- 수익 패턴 Top 5
- 기회비용 회수 후보 Top 5
- EV 개선 우선순위 (shadow-only -> canary -> 승격 순)

3. 금지사항
- full/partial/split-entry 혼합 해석 금지
- 운영 코드 즉시 변경 지시 금지
- 전역 손절 강화 같은 단일축 일반화 결론 금지

---

## 7. 최종 산출 문서

아래 파일을 생성:

1. `analysis/claude_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md`
- 형식: `판정 -> 근거 -> 다음 액션`
- 손실/수익/기회비용/리스크를 분리 서술

2. `analysis/claude_scalping_pattern_lab/outputs/ev_improvement_backlog_for_ops.md`
- 개선 후보별:
  - 기대효과
  - 리스크
  - 필요 표본
  - 검증 지표
  - 적용 단계(`shadow-only`, `canary`, `hold`)

3. `analysis/claude_scalping_pattern_lab/outputs/run_manifest.json`
- 실행 시각, 입력 파일 목록, 행 수, 버전 메모

---

## 8. 완료 기준 (DoD)

1. `src/` 이하 운영 코드 변경 0건
2. 분석 자산은 `analysis/claude_scalping_pattern_lab/`에만 존재
3. `run_all.sh` 단일 명령으로 전체 산출물 재생성 가능
4. 최종 보고서가 `판정/근거/다음 액션` 구조를 충족
5. EV 개선안이 반드시 `shadow-only` 우선순위를 포함

---

## 9. 제출 포맷

최종 제출 메시지는 아래 순서로 제한:

1. `판정`
2. `근거`
3. `다음 액션`

부록으로 생성된 파일 목록만 첨부한다.
