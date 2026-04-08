# 2026-04-09 Stage 2 To-Do Checklist

## 목적

- `2026-04-08` 미수행 항목을 누락 없이 이월해 장전/장중/장후 순서로 실행한다.
- `종목 선정`과 `진입/탈출 실패`를 분리 추적해, 튜닝 우선순위를 명확히 유지한다.

## 전일(2026-04-08) 장마감 요약 전제

- 스캘핑 완료 `12건`, 승률 `25.0%(3/12)`, 실현손익 `-66,367원`
- `fallback` 진입 `5건` 전패, 실현손익 `-27,742원`
- `scalp_ai_early_exit` 종료 `4건` 전부 손실
- 해석: 종목 선정보다 `진입 타이밍/출구 규칙` 품질 보정이 우선

## 2026-04-09 장전 체크리스트 (08:30~09:00)

- [ ] `fallback` 전용 진입 억제 canary 1개만 적용
  - 비중 축소 또는 진입 강도 강화 중 한 가지 축만 적용
  - 적용 시각/파라미터/기대효과를 문서에 기록
- [ ] `OPEN_RECLAIM` / `SCANNER` 출구 규칙 분리 보강
  - `scalp_ai_early_exit`에서 `never_green`과 `양전환 이력 있음`을 분리
  - 포지션 태그별 적용 범위를 명시
- [ ] `exit_rule='-'` 복원 정확도 보정
  - 전일 누락 거래 우선 복원 후 `trade-review` 반영 확인
- [ ] Dual Persona 재활성화 조건 고정
  - `dual_persona_extra_ms_p95 <= 2500`
  - `effective_override_ratio >= 3%`
  - `samples >= 30`
  - `gatekeeper_eval_ms_p95 <= 5000`
- [ ] 공통 hard time stop은 shadow 평가만 수행하도록 고정
  - 실전 반영 없이 후보안 영향 추정 결과를 먼저 축적

## 2026-04-09 장중 체크리스트 (09:00~15:30)

- [ ] `curr`, `spread` 완화 후보 분석용 기준 정리
  - `holding_sig_deltas`를 `시간대/position_tag/entry_mode/종목군`으로 분해하는 집계 축 확정
  - `1틱 변화 허용` 후보와 `현행 유지` 후보를 같은 포맷으로 비교표 작성
- [ ] canary 실시간 모니터링(적용 후 `30~60분`)
  - `fallback` 승률/평균손실/손실총액 변화 기록
  - 손절 급증/평균손실 확대 시 즉시 롤백
- [ ] 스윙 Gatekeeper missed case 표본 채집
  - `blocked_gatekeeper_reject` 후 추세가 좋았던 표본 후보를 장중 마킹
  - 동시 구간 `dual_persona_shadow` 결론(`ALLOW`/기타) 교차 메모

## 2026-04-09 장후 체크리스트 (15:30~)

- [ ] 공통 hard time stop 후보안 영향 추정
  - `3분`, `5분`, `7분`, `5분+저점수`, `fallback 3~5분`, `수익 미전환+장시간` 후보를 최근 거래일로 백테스트
  - 승률/평균손익/손익합/조기잘림 비율을 같은 기준으로 산출
- [ ] 스윙 Gatekeeper missed case 정리 완료
  - 장중 수집한 후보를 정식 표본으로 확정
  - `blocked_gatekeeper_reject` vs 이후 추세를 일자별로 정리
- [ ] 스윙 missed case 요약표 + threshold 완화 검토 근거 문서화
  - `완화 보류/부분 canary/완화 검토` 중 하나로 근거 기반 결론 작성
  - `2026-04-10` 장전 의사결정안으로 연결
- [ ] 스캘핑 진입종목의 스윙 자동전환 검토 프레임 초안 작성
  - 전환 트리거/금지조건/전환 후 리스크관리/사후검증 지표를 1페이지로 정리
  - 최소 5거래일 shadow 검증 전 실전 ON 금지 원칙을 명시

## 2026-04-09 종일 유지 점검 (미적용 정책 11개)

- [ ] `near_safe_profit` 수치 직접 하향하지 않는다
- [ ] `near_ai_exit` 수치 직접 완화하지 않는다
- [ ] 공통 hard time stop 실전 적용하지 않는다
- [ ] fallback 전면 차단하지 않는다
- [ ] 스캘핑 공통 손절값 일괄 완화하지 않는다
- [ ] 추가매수(`AVG_DOWN`/`PYRAMID`) 임계값 직접 완화하지 않는다
- [ ] 스윙 AI threshold 직접 완화하지 않는다
- [ ] `RISK_OFF` 상태의 스윙 허용 기준 완화하지 않는다
- [ ] `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER` 당일 재활성화하지 않는다(조건 미달 시)
- [ ] `dual_persona_shadow` 스윙 실전 승급하지 않는다
- [ ] 스윙 gap 기준 직접 완화하지 않는다

## 2026-04-09 완료 기준

- [ ] 장전 5개 항목 결과가 시각/수치와 함께 기록된다
- [ ] 장중 3개 항목 결과가 시각/수치와 함께 기록된다
- [ ] 장후 3개 항목(전일 미수행 포함) 결과가 문서화된다
- [ ] 종일 유지 점검 11개 항목의 유지 여부가 체크된다
- [ ] `2026-04-10`에 바로 넘길 수 있는 의사결정 근거(적용/보류/롤백)가 남는다

## 참고 문서

- [2026-04-08-stage2-todo-checklist.md](./2026-04-08-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
