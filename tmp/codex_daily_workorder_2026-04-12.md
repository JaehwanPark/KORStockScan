# Codex 일일 작업지시서

- 생성시각: `2026-04-12T10:10:24+09:00`
- 프로젝트: `JaehwanPark` / `#1` / `@KORStockScan`
- 기준일자: `2026-04-12` / overdue 포함: `False`
- 상태필터: `Todo, In Progress`
- 슬롯필터: `전체`
- 후보건수: `3` / 지시반영건수: `3`
- Track 분포: `-:3`

## 오늘 Codex 실행 큐

1. `[AIPrompt] 작업 1 SCALP_PRESET_TP SELL 의도 확인`
   - 상태: `Todo` / 슬롯: `POSTCLOSE` / 트랙: `-` / Due: `2026-04-12` / TimeWindow: `15:40~16:10`
   - 섹션: `P0. 즉시 착수 가능한 확인/계측`
   - 소스: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md`
   - Project Item ID: `PVTI_lAHOAXZuE84BUTcPzgpsU-E`
2. `[AIPrompt] 작업 2 AI 운영계측 추가`
   - 상태: `Todo` / 슬롯: `INTRADAY` / 트랙: `-` / Due: `2026-04-12` / TimeWindow: `10:00~10:30`
   - 섹션: `작업 상세`
   - 소스: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md`
   - Project Item ID: `PVTI_lAHOAXZuE84BUTcPzgpqZLE`
3. `[AIPrompt] 작업 3 HOLDING hybrid override 조건 명세`
   - 상태: `Todo` / 슬롯: `POSTCLOSE` / 트랙: `-` / Due: `2026-04-12` / TimeWindow: `15:40~16:10`
   - 섹션: `작업 상세`
   - 소스: `docs/2026-04-11-scalping-ai-prompt-coding-instructions.md`
   - Project Item ID: `PVTI_lAHOAXZuE84BUTcPzgpqZLU`

## Codex 전달 템플릿

```text
아래 Project 항목을 오늘 작업 대상으로 처리해줘.
원칙:
- 판정, 근거, 다음 액션 순서로 보고
- 관련 문서/체크리스트 동시 업데이트
- 테스트/검증 결과 포함
- workorder에 적힌 Source/Section을 기준으로 우선 문맥을 맞출 것

[대상 항목]
- [AIPrompt] 작업 1 SCALP_PRESET_TP SELL 의도 확인 | 상태=Todo | 슬롯=POSTCLOSE | Due=2026-04-12 | Source=docs/2026-04-11-scalping-ai-prompt-coding-instructions.md | Section=P0. 즉시 착수 가능한 확인/계측 | ID=PVTI_lAHOAXZuE84BUTcPzgpsU-E
- [AIPrompt] 작업 2 AI 운영계측 추가 | 상태=Todo | 슬롯=INTRADAY | Due=2026-04-12 | Source=docs/2026-04-11-scalping-ai-prompt-coding-instructions.md | Section=작업 상세 | ID=PVTI_lAHOAXZuE84BUTcPzgpqZLE
- [AIPrompt] 작업 3 HOLDING hybrid override 조건 명세 | 상태=Todo | 슬롯=POSTCLOSE | Due=2026-04-12 | Source=docs/2026-04-11-scalping-ai-prompt-coding-instructions.md | Section=작업 상세 | ID=PVTI_lAHOAXZuE84BUTcPzgpqZLU
```
