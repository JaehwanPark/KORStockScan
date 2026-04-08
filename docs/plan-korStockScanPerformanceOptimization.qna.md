# KORStockScan 성능 최적화 Q&A 분리본

아래 내용은 아카이브 문서의 `확인 질문과 답변` 섹션만 분리한 참고본이다.

## 확인 질문과 답변

### Q1. Reason code 집계 자동화는 이미 대시보드에 있나요? 아니면 새로 만들어야 하나요?

답변:

- 부분적으로는 이미 있다.
- [sniper_performance_tuning_report.py](../src/engine/sniper_performance_tuning_report.py)에서 `holding_reuse_blockers`, `gatekeeper_reuse_blockers`를 이미 집계하고 있다.
- [app.py](../src/web/app.py) `성능 튜닝 모니터`에서도 전략별 `최신 차단 분포`와 일부 blocker 집계를 노출하고 있다.

정확한 판단:

1. "현재 시점의 blocker 분포를 보는 자동화"는 이미 있다.
2. "일자별 추세 비교", "reason code 상위 변화 알림", "sig_delta 상위 필드 자동 랭킹"은 아직 없다.
3. 따라서 새로 만들 대상은 완전 신규 대시보드라기보다, 기존 `성능 튜닝 모니터`의 blocker 집계를 일자/기간 기준으로 확장하는 것이다.

운영 권장:

1. 1차는 현재 `performance-tuning`에 일자별 blocker trend를 추가한다.
2. 2차는 `sig_delta` 상위 필드까지 별도 섹션이나 CSV export로 확장한다.

### Q1-추가. Gatekeeper 캐시 TTL은 12초에서 20초로 먼저 올리는 게 맞나요? 아니면 동적 TTL로 바로 가야 하나요?

답변:

- 현재 전제부터 수정이 필요하다.
- Gatekeeper 결과 캐시 TTL은 이미 [constants.py](../src/utils/constants.py) `#L228` 기준 `30초`다.
- fast reuse도 [constants.py](../src/utils/constants.py) `#L232` 기준 `30초`다.

정확한 판단:

1. 지금 병목은 TTL 부족보다 `저장 lifecycle`과 `sig_changed` 우회가 더 크다.
2. 따라서 `20초로 증대`는 현재 코드 기준 의미가 없다.
3. 동적 TTL도 지금 당장 1단계에서 할 일은 아니다.

채택안:

1. `현행 30초 유지`
2. 먼저 `missing_action`, `missing_allow_flag`, `sig_changed`의 실제 발생 원인을 추적
3. 그 다음에 전략/장세 기준 동적 TTL을 검토

### Q1-추가. missing_action, missing_allow_flag는 로그만 더 모을까요, 아니면 저장 경로 자체를 바로 수정할까요?

답변:

- 1단계에선 `로그/추적 강화`를 먼저 하는 것이 맞다.

근거:

1. [sniper_state_handlers.py](../src/engine/sniper_state_handlers.py) `#L1331`~`#L1339`에서 `has_last_action`, `has_last_allow_flag`를 판단한다.
2. 같은 파일 `#L1416`~`#L1422`에서 Gatekeeper 평가 후 `last_gatekeeper_action`, `last_gatekeeper_allow_entry`, `last_gatekeeper_fast_signature`를 저장한다.
3. 즉 현재 구조상 "저장 로직이 아예 없다"기보다 "언제 비어 있는지, 언제 초기화되는지"가 핵심이다.

채택안:

1. 먼저 `gatekeeper_fast_reuse_bypass`에 lifecycle 추적 필드를 추가한다.
2. 예: `has_last_action`, `has_last_allow_flag`, `last_action_age`, `last_fast_sig_age`
3. 원인이 확인되면 그 다음 단계에서 저장 경로 수정으로 간다.

### Q1-추가. sig_changed 필드 분해는 reason_codes에 붙일까요, 새 stage로 분리할까요?

답변:

- 둘 중 하나를 고르라면 새 stage 분리보다 `기존 bypass stage에 별도 상세 필드`를 붙이는 쪽이 더 낫다.

이유:

1. `reason_codes`는 집계용 분류 체계라 짧고 안정적으로 유지하는 게 좋다.
2. 필드 변화 상세는 집계보다 원인 추적에 가깝다.
3. 보유 AI에서도 [sniper_state_handlers.py](../src/engine/sniper_state_handlers.py) `#L1954`~`#L1995`처럼 `sig_delta`를 별도 필드로 남기는 방식이 이미 일관된 패턴이다.

채택안:

1. 새 stage `gatekeeper_sig_delta`는 만들지 않는다.
2. 대신 `gatekeeper_fast_reuse_bypass` 로그에 `sig_delta=...`를 추가한다.
3. `reason_codes`는 기존처럼 `sig_changed`, `age_expired`, `missing_action` 같은 상위 카테고리로 유지한다.

### Q2. 그림자 로그 수집 기간을 1주일로 정해도 되나요?

답변:

- 된다.
- 오히려 `1주일`이 기본 권장값이다.

이유:

1. 단일 날짜는 종목군, 장중 변동성, 장세 편향을 많이 탄다.
2. 최소 `5거래일`, 권장 `1주일`이면 임계값 근처 재평가가 일관된 패턴인지 볼 수 있다.
3. 첫 1주 수집 후 표본이 적으면 1주 더 연장하는 방식이 적절하다.

운영 권장:

1. 기본 수집 기간은 `1주일`
2. 분석 기준 미달 시 `1주 추가`
3. 장중 운영 부담이 크지 않도록 별도 파일보다 기존 [sniper_state_handlers_info.log](../logs/sniper_state_handlers_info.log) stage 추가 방식을 우선 사용

### Q3. 성과 기준 통일 검증을 자동 대시보드에 추가하는 게 2단계 목표에 포함되어야 하나요?

답변:

- 필요하다.
- 다만 `2단계 목표`라기보다 `3단계: 성과 집계와 복기 기준 통일`에 포함하는 것이 더 정확하다.

이유:

1. 2단계는 보유 AI 재평가 낭비 감소가 핵심이다.
2. 성과 기준 통일 검증은 튜닝 효과를 신뢰할 수 있게 만드는 별도 품질 게이트다.
3. 따라서 이 검증은 `trade-review`, `performance-tuning`, `strategy-performance`를 묶는 공통 검증 계층으로 다뤄야 한다.

운영 권장:

1. `3단계 목표`에 자동 검증 칩 또는 경고 박스를 추가한다.
2. 검증 항목은 `completed/open/realized_pnl` 3개를 기본으로 한다.
3. 세 화면 중 하나라도 값이 다르면 대시보드에서 경고를 띄우고, snapshot 저장 시 warning도 함께 남긴다.

### Q4. 추가매수 점검 기준도 현재 퍼포먼스 튜닝 계획안에 포함해야 하나요?

답변:

- 포함하는 것이 맞다.
- 다만 `즉시 임계값 완화`가 아니라, `성능 튜닝 모니터에 추가매수 품질 계층을 넣는 설계`로 포함하는 것이 안전하다.

이유:

1. 현재 `performance-tuning`은 Gatekeeper, 보유 AI, exit rule, 전략 성과 추세는 보지만 `AVG_DOWN`, `PYRAMID`의 효과성과 시점은 직접 보지 못한다.
2. 추가매수는 손익을 크게 바꿀 수 있으므로, 전략 튜닝에서 빠져 있으면 `진입/청산 정책`만 보고 잘못된 결론을 내릴 수 있다.
3. 특히 `물타기 회복률`, `불타기 확장률`, `lock/cancel 오염`은 별도 축으로 봐야 한다.

채택안:

1. `3단계-추가`로 `추가매수 효과성 관측 계층`을 계획안에 포함한다.
2. 1차는 `holding_add_history + ADD_SIGNAL + trade-review` 조합으로 바로 계산 가능한 지표부터 붙인다.
3. 2차는 `signal_profit_rate`, `signal_peak_profit`, `market_regime` 같은 필드를 직접 저장해 시점 판단 정밀도를 높인다.

### Q5. 오늘 확인된 스캘핑 손절 문제도 현재 퍼포먼스 튜닝 계획안에 바로 병합해야 하나요?

답변:

- 포함하는 것이 맞다.
- 다만 `스캘핑 공통 손절 완화`로 넣지 말고, `fallback/SCALP_BASE 과민 손절`과 `OPEN_RECLAIM 지연 손절`을 분리한 튜닝 트랙으로 병합해야 한다.

이유:

1. 오늘까지 확인된 손절은 `너무 빠른 손절`과 `너무 늦은 손절`이 동시에 있어, 공통 손절값 1개로 풀면 한쪽을 고치며 다른 쪽을 악화시킬 가능성이 크다.
2. `SCALP_BASE/fallback`은 `SCALP_PRESET_TP`와 `preset hard stop=-0.7`의 영향을 직접 받는다.
3. `OPEN_RECLAIM`은 `AI early exit min_hold / low_score_hits` 구조의 영향을 더 크게 받는다.
4. 따라서 현재 계획안에는 `전략 자체 튜닝`이 아니라 `전략 내부 세부 트랙 분리`가 먼저 반영되어야 한다.

채택안:

1. `2026-04-08 스캘핑 손절 패턴 반영` 섹션을 계획안에 포함한다.
2. 오늘은 `비교표 작성 + 후보안 문서화`까지를 완료 기준으로 둔다.
3. 이후 shadow 또는 실전 반영은 `fallback 전용` 또는 `OPEN_RECLAIM 전용` 중 하나씩만 순차 적용한다.
