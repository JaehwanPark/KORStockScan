# 2026-04-18 다음주(2026-04-20~2026-04-24) 일자별 검증축 표

| 일자 | 검증축 | 기대성과 | 우려되는 지점 | 예상 후속과제 |
|---|---|---|---|---|
| 2026-04-20 (월) | split-entry rebase 수량 정합성 shadow 1일차 판정 | leakage 원인 중 수량/재기반 축을 분리해 진입 퍼널 회복 가능성 확인 | shadow 표본 부족 시 결론 유예 | 승격/보류 이진 판정 + 보류 시 재실행 시각 고정 |
| 2026-04-20 (월) | split-entry 즉시 재평가 shadow 1일차 판정 | 미진입 기회비용(지연성 miss) 감소 여지 확인 | 즉시 재평가가 오탐 진입 증가로 연결될 가능성 | blocker 분포(latency/liquidity/AI threshold/overbought) 재집계 |
| 2026-04-20 (월) | same-symbol split-entry cooldown shadow 1일차 판정 | 과잉 재진입 억제와 체결 품질 안정화 동시 달성 가능성 | cooldown 과도 적용 시 고기대값 재진입 차단 | full fill/partial fill 분리 성과표 기반 threshold 미세조정 |
| 2026-04-20 (월) | latency canary bugfix-only 재판정 | bugfix-only 조건에서 순수 latency 개선효과 확인 | quote_stale 외 원인(ws_age/ws_jitter/spread) 미분리 시 오판 | reason allowlist canary 유지/축소 판정 |
| 2026-04-20 (월) | HOLDING action schema shadow-only 착수 | HOLDING 의사결정 해상도 개선, post-sell 품질지표 연동 기반 확보 | schema 변경 시 로그/집계 정합성 손상 가능성 | shadow 로그 스키마 고정 + rollback guard 점검 |
| 2026-04-20 (월) | partial-only timeout shadow 1일차 판정 | partial 체결 정체 해소, 체결 효율 개선 기대 | 조기 timeout이 기대수익을 훼손할 위험 | partial 전용 종료규칙 단일축 재파라미터링 |
| 2026-04-20 (월) | main runtime OpenAI 라우팅/감사필드 실표본 검증 | 작업9 이식 실효성(실경로 반영) 확정 | API key/모델식별자 이슈로 Gemini fallback 가능성 | 라우터 조건/모델명 교정 및 누락 필드 재주입 |
| 2026-04-21 (화) | split-entry leakage canary 승격/보류 판정 | 다음 승격축 1개 확정으로 실행속도 확보 | 결론 지연 시 일정 재밀림 | 승격 시 확대, 보류 시 원인+재시각 고정 |
| 2026-04-21 (화) | HOLDING shadow 성과 판정(missed_upside_rate/capture_efficiency/GOOD_EXIT) | HOLDING 축 기대값 개선 여부를 왜곡 없는 지표로 판정 | 표본 부족/편향으로 과잉해석 위험 | 1~2세션 추가관측 여부 및 판정기준 확정 |
| 2026-04-21 (화) | 작업12 Raw 입력 축소 A/B 범위 확정 | 추론 지연/노이즈 감축 착수 기반 확보 | 과도 축소 시 신호 손실로 진입 품질 저하 | 최소범위 A/B 설계(입력군/기간/rollback) 문서화 |
| 2026-04-22 (수) | 작업11 HOLDING critical 경량 프롬프트 분리 보강 | HOLDING 응답 지연 단축, 급변 구간 대응력 향상 | 경량화로 문맥 손실 시 exit 품질 저하 가능성 | critical 경로 shadow 비교표(기존 vs 경량) 생성 |
| 2026-04-23 (목) | 작업12 Raw 입력 축소 A/B 범위 확정 마감 | 다음 영업일 실행 가능한 실험단위 확정 | 범위 미확정 시 튜닝축 정체 | 실패 시 사유+다음 실행시각 고정 및 재동기화 |
| 2026-04-24 (금) | 주간 판정 통합: 승격 1축 실행 or 보류+재시각 확정 | 주간 결론을 실운영 축으로 전환해 기대값 개선 속도 유지 | 다축 동시 변경 시 원인귀속 불명확 | 한 축 canary 원칙으로 다음주 PREOPEN 실행지시서 확정 |

## 참고 문서

- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
