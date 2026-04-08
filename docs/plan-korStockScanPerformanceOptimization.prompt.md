## 계획: KORStockScan 성능 최적화 실행안 (Session Prompt)

이 문서는 **다음 세션 실행 지시용 경량 플랜**이다.
상세 이력/질답/장문 분석은 분리 문서를 사용한다.

## 문서 분할 안내

1. 현재 문서(실행 프롬프트): [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
   - 역할: 지금 바로 수행할 작업지시/우선순위/가드레일
2. 상세 이력(원본 보관): [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)
   - 역할: 단계별 구현 내역, 과거 장중/장후 보고, 세부 로그 해석
3. 확인 질문/답변 분리본: [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
   - 역할: Q&A 성격의 의사결정 근거만 조회

운영 원칙:
- 이 문서는 실행 지시 관점에서만 유지한다.
- 신규 장문 리포트는 archive 또는 일자별 체크리스트에 기록한다.
- 혼선을 막기 위해 이 문서에 과거 상세 로그를 재적재하지 않는다.

---

## 현재 상태 요약 (2026-04-08 장마감 기준)

1. 스캘핑 성과:
   - 완료 `12건`, 승률 `25.0%(3/12)`, 실현손익 `-66,367원`
   - `fallback` 진입 `5건` 전패, 실현손익 `-27,742원`
2. 핵심 해석:
   - 종목 선정 자체보다 `진입 타이밍/출구 규칙` 품질 이슈가 큼
3. 보유 AI 재사용:
   - `holding_skip_ratio=6.8%`, `holding_ai_cache_hit_ratio=0.2%`
   - `ai_holding_shadow_band` raw: `616건(review 574 / skip 42)`
4. 스윙/시장 국면:
   - `risk_state=RISK_OFF`, `allow_swing_entry=false`, `swing_score=-10`
   - 스윙 0진입 day는 `market-regime 제한 + gap 차단 편중`으로 분류
5. 듀얼 페르소나:
   - Gatekeeper 적용은 `OFF` 유지 상태
   - `raw conflict` 높고 `effective override` 낮음, `extra_ms` 높음

---

## `AI캐시 MISS` 이슈 상태

분석 완료(1차):
1. `AI캐시 MISS`는 오작동보다는 재평가 강제 구조 영향이 큼
2. 주 원인 축: `sig_changed`, `near_ai_exit`, `near_safe_profit`, `age_expired`
3. `sig_changed` 상세 원인(1차): `curr`, `spread` 변화 비중이 큼

미완료(2차):
1. `curr/spread` 완화 후보의 정량 영향 추정
2. `near_ai_exit/near_safe_profit` band 직접 조정 여부 결정
3. 최근 거래일 기준 후보안 승률/손익 비교 후 정책 확정

---

## 2026-04-09 실행 기준 문서

- 주 실행 체크리스트: [2026-04-09-stage2-todo-checklist.md](./2026-04-09-stage2-todo-checklist.md)
- 전일 완료/잔여 맥락: [2026-04-08-stage2-todo-checklist.md](./2026-04-08-stage2-todo-checklist.md)

### 장전 (08:30~09:00)

1. `fallback` 전용 진입 억제 canary 1개만 적용
2. `OPEN_RECLAIM` / `SCANNER` 출구 규칙 분리
3. `exit_rule='-'` 복원 정확도 보정
4. Dual Persona 재활성화 조건 고정
5. 공통 hard time stop은 shadow-only 유지

### 장중 (09:00~15:30)

1. `curr/spread` 완화 분석 집계축 확정
2. canary 적용 후 `30~60분` 지표 모니터링 + 롤백 가드
3. 스윙 Gatekeeper missed case 표본 채집

### 장후 (15:30~)

1. hard time stop 후보안 영향 추정
2. 스윙 missed case 정리 + 완화 검토 결론 작성
3. 익일(2026-04-10) 장전 의사결정안 확정

---

## 실행 워크스트림 (정리본)

### WS1. Gatekeeper 재사용 복구

목표:
- `gatekeeper_fast_reuse_ratio > 10%`
- `gatekeeper_ai_cache_hit_ratio > 5%`
- `gatekeeper_eval_ms_p95 < 5000`

핵심:
- `missing_action`, `missing_allow_flag`, `sig_changed` 우회 원인 추적
- lifecycle 저장 시점/재사용 조건 정합성 확인

### WS2. 보유 AI 재평가 낭비 감소

목표:
- `holding_skip_ratio > 5%` 유지/개선
- `holding_ai_cache_hit_ratio > 10%`로 회복
- `holding_review_ms_p95 < 1500`

핵심:
- `sig_delta` 분해 + shadow band 데이터 기반으로만 정책 변경
- 단일일자 손익으로 band 직접 조정 금지

### WS3. 성과 집계/복기 기준 통일

목표:
- `trade-review`, `performance-tuning`, `strategy-performance` 일관성 유지

핵심:
- 정규화 거래 lifecycle 기준으로만 성과판단

### WS3-Add. 추가매수 품질 관측

목표:
- `AVG_DOWN`, `PYRAMID`, `no-add` 분리 관측

핵심:
- 효과성(결과)과 시점 적절성(타이밍) 분리

### WS4. 로그 보관/스냅샷 체계

목표:
- 장중 판단의 익일 재현성 확보

핵심:
- snapshot + gzip 아카이브 일관성 확인

### WS5. 전략 자체 튜닝 (후순위)

대상:
- 스윙 진입 조건, 스캘핑 강도 게이트, fallback/reclaim 보조 로직

원칙:
- 활동량보다 품질(승률/손익/일관성)

### WS5-Add. 스캘핑 진입종목의 스윙 자동전환 검토 (신규)

목표:
- 스캘핑 진입 후 스윙 시나리오로 전환이 합리적인 케이스를 검토

검토 프레임:
1. 전환 트리거 정의
2. 전환 금지 조건 정의
3. 전환 후 리스크 관리 정의
4. 전환/비전환 비교 리플레이 정의

가드레일:
- 최소 5거래일 shadow 검증 전 실전 자동전환 금지
- 손실 은폐 목적 전환 금지

### WS6. post-sell 피드백 파이프라인 (신규)

목표:
- 매도 이후 `1/3/5/10/20분` 구간 성과를 자동 수집/평가
- 장후 보고에 `missed upside / good exit` 분포를 고정 포함

핵심:
- `sell_completed` 시점에 후보 기록(JSONL)
- 장후 배치에서 분봉 기반 자동 평가 + 요약 전송
- 모니터 스냅샷(`post_sell_feedback`) 일자 저장

잔여 과제:
1. `POST_SELL_WS_RETAIN_MINUTES` 운영값 확정 (기본값 `0`, API 분봉 MVP)
2. post-sell 지표를 `performance-tuning` 메인 리포트 카드에 병합
3. 종목/포지션 태그별 `과매도/조기매도` 회귀 피처 확장

### WS7. 이벤트 스키마 + 공통 로거 정리 (신규)

목표:
- `ENTRY_PIPELINE/HOLDING_PIPELINE` 이벤트를 단일 스키마로 기록
- 텍스트 로그 + 구조화 JSONL 동시 유지로 분석/운영 양립

핵심:
- 공통 emit 함수로 로깅 포맷 일원화
- 스키마 버전 기반 하위호환 운영

잔여 과제:
1. `performance_tuning/trade_review`가 JSONL 스키마를 직접 소비하도록 파서 고도화
2. Gatekeeper/Overnight/Scale-in 특수 이벤트까지 공통 스키마 확장
3. 이벤트 필드 품질 검증(누락/타입 오류) 배치 추가

---

## 즉시 착수 체크리스트 (경량)

1. `curr/spread` 완화 후보 분석 기준 정리
2. hard time stop 후보안 영향 추정
3. 스윙 Gatekeeper missed case 표본 정리
4. 듀얼 페르소나 `raw conflict/effective override` 분리 관측 유지
5. `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER` 상태 일일 기록
6. `fallback`/`OPEN_RECLAIM` 분리 튜닝 결과 축적
7. 스캘핑→스윙 자동전환 검토 프레임 문서화
8. post-sell 분류 임계값(`missed/good`) 주간 리밸런싱
9. pipeline_event JSONL 기반 대시보드 초안 작성

## 보류 원칙 (경량)

1. `near_safe_profit`/`near_ai_exit` 즉시 완화 금지
2. 공통 hard time stop 실전 적용 보류
3. `RISK_OFF` day에서 스윙 완화 금지
4. 듀얼 페르소나 즉시 실전 승급 금지
5. 단일일자 결과 기반의 공통 파라미터 일괄 조정 금지

## 관련 문서

- [2026-04-08-stage2-todo-checklist.md](./2026-04-08-stage2-todo-checklist.md)
- [2026-04-09-stage2-todo-checklist.md](./2026-04-09-stage2-todo-checklist.md)
- [plan-korStockScanPerformanceOptimization.archive-2026-04-08.md](./plan-korStockScanPerformanceOptimization.archive-2026-04-08.md)
- [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md)
