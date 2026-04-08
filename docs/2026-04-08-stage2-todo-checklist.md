# 2026-04-08 Stage 2 To-Do Checklist

## 목적

- 2단계 잔여 plan을 무리하게 당겨 바꾸지 않고, 오늘 해야 할 관측/설계 작업을 순서대로 정리한다.
- 특히 `공통 hard time stop`처럼 크리티컬한 변경은 충분한 기준을 만든 뒤 결정한다.

## 순서 재정의

- `ai_holding_shadow_band`는 **오늘 데이터를 받기 위한 어제의 선행 작업**이다.
- 따라서 체크리스트는 `어제 선반영` → `오늘 장중 관찰` → `오늘 장후 분석` 순으로 본다.

## 어제(2026-04-07) 선반영 필수

- [x] `ai_holding_shadow_band` 로그 추가
  - `near_ai_exit`, `near_safe_profit` 때문에 실제 fresh review가 몇 건 발생하는지 내일부터 바로 수집 시작
- [x] 봇 수동 재실행 완료
  - `2026-04-07 16:38 KST` 기준 `python bot_main.py` 신규 프로세스 재기동 확인


## 오늘(2026-04-08) 장중 바로 확인할 일

- [x] 운영 로그 확인
  - `2026-04-08 10:33 KST` 기준 `ai_holding_shadow_band` 70건 확인
  - 최근 로그도 `action=review|skip`, `distance_to_ai_exit`, `distance_to_safe_profit` 형식이 정상
- [x] `age_sec` 수정 후 운영 모니터링
  - `2026-04-08 10:33 KST` 기준 `ai_holding_reuse_bypass`, `gatekeeper_fast_reuse_bypass`에 epoch 수준 `age_sec` 재발 0건
- [x] `ai_holding_shadow_band` 표본 정상 수집 확인
  - 전제: 어제 반영 코드 기준으로 봇 수동 재실행은 완료됨
  - `review 65건`, `skip 5건`으로 표본 유입 확인
  - `near_ai_exit=True 22건`, `near_safe_profit=True 0건`으로 현재는 AI 손절 경계 쪽 표본이 먼저 쌓이는 중
- [x] 보유 AI 재사용 경로 모니터링
  - `performance-tuning` 기준 `holding_skip_ratio=7.9%`, `holding_ai_cache_hit_ratio=0.0%`
  - `holding_reuse_blockers` 상위는 `시그니처 변경 103`, `재사용 창 만료 65`, `저점수 경계 58`, `AI 손절 경계 37`
- [x] 스윙 market regime 상태 기록
  - `data/cache/market_regime_snapshot.json` 기준 `risk_state=RISK_OFF`, `allow_swing_entry=false`, `swing_score=25`
  - 사유는 `원유 반전 시그널`, `공포탐욕지수 극단적 공포 유지`
- [x] 스윙 blocker 실시간 분류
  - `2026-04-08 10:33 KST` 기준 `blocked_swing_gap 664`, `blocked_gatekeeper_reject 1`, `blocked_zero_qty 1`
  - 현재 장중 차단은 사실상 `blocked_swing_gap` 편중이며, snapshot의 `allow_swing_entry=false`와 함께 장후에 해석 우선순위를 다시 맞춘다
- [x] Gatekeeper 듀얼 페르소나 장중 긴급 완화 적용
  - `2026-04-08 12:14 KST` 단기 관측값: `dual_persona_conflict_ratio=100.0%(since=11:00)`, `dual_persona_fused_override_ratio=0.0%`, `dual_persona_extra_ms_p95=7666ms`
  - `2026-04-08 12:22 KST` 기준 `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER=False` 적용 후 `bot_main.py` 재기동
  - 재기동 직후 `run_sniper started 12:22:34`, `[BOOT_RESTORE] HOLDING runtime rehydrated count=3` 확인
  - 재기동 이후 구간(12:22~) `dual_persona_shadow` 신규 로그 미발생 확인

## 오늘(2026-04-08) 장후 분석할 일

- [ ] `curr`, `spread` 완화 후보 분석용 기준 정리
  - `holding_sig_deltas` 상위 필드가 시간대/종목별로 어떻게 달라지는지 집계 축 정의
- [x] fallback 진입 거래 표본 분리
  - `2026-04-08 12:03 KST` 기준 `trade-review` 완료 스캘핑(`7건`)에서 `entry_mode=fallback 3건`, `normal 0건`, `unknown 4건`
  - `fallback` 성과: 승률 `0% (0/3)`, 평균 보유시간 `502초`, 평균 손익률 `-0.857%`, 평균 실현손익 `-9,227원`(합계 `-27,682원`)
  - `normal` 성과: 표본 `0건`으로 당일 비교 보류
  - 참고: `holding_started` 이벤트가 누락된 레거시 표본은 `unknown`으로 분리

| entry_mode | 표본 | 승률 | 평균 보유시간 | 평균 손익률 | 평균 실현손익 | 실현손익 합계 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fallback | 3 | 0.0% | 502초 | -0.857% | -9,227원 | -27,682원 |
| normal | 0 | - | - | - | - | - |
| unknown | 4 | 50.0% | 575초 | -0.078% | -10,031원 | -40,125원 |
- [x] 스캘핑 손절 패턴 일일 분해
  - `2026-04-08 11:18 KST` 기준 완료된 스캘핑은 `5건`, 이 중 `손절 4건 / 익절 1건`
  - 손절 표본은 `OPEN_RECLAIM 2건`, `SCALP_BASE 1건`, `SCANNER 1건`
  - `OPEN_RECLAIM` 손절 2건 평균 손익률 `-0.99%`, 평균 보유시간 `492.5초`
  - `SCALP_BASE`는 `35초` 초단기 손절, `SCANNER`는 `733초` 지연 손절 1건

| ID | 종목 | position_tag | entry_mode | exit_rule | 보유시간 | 손익률 | 실현손익 | 1차 해석 |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |
| 1403 | 씨아이에스 | OPEN_RECLAIM | 미확인 | `scalp_ai_early_exit` | 527초 | -1.03% | -53,298원 | 지연 손절 표본 |
| 1407 | 산일전기 | SCALP_BASE | `fallback` | `preset hard stop(-0.7)` | 35초 | -0.71% | -27,053원 | 과민 손절 표본 |
| 1368 | 휴림로봇 | OPEN_RECLAIM | 미확인 | `scalp_ai_early_exit` | 458초 | -0.95% | -105원 | `low_score_hits 3/3` 누적 후 청산 |
| 1413 | 현대건설 | SCANNER | `fallback` | `scalp_ai_early_exit` | 733초 | -0.75% | -13,209원 | `never green` 지연 손절 표본 |

참고: `산일전기`는 체결 로그 원본에 `exit_rule=-`로 남았지만, 현재 복기 로직 기준으로는 `preset hard stop(-0.7)` 성격으로 해석한다.
참고: `현대건설`은 `fallback_scout + fallback_main` 번들 진입 후 `peak_profit=-0.13%`로 한 번도 양전환하지 못했고, `near_ai_exit` 구간이 길게 이어진 뒤 `low_score_hits 3/3`에서 청산됐다.
- [x] `SCALP_BASE` / fallback 전용 손절 후보안 비교표 작성

| 후보 | 변경안 | 기대효과 | 현재 표본 적합도 | 주요 리스크 | 오늘 기준 우선순위 |
| --- | --- | --- | --- | --- | --- |
| A | `fallback` 전용 투자비중 축소 | 같은 과민 손절이 나와도 절대 손실을 즉시 줄인다 | 높음 | false stop 자체는 남는다 | 1 |
| B | `preset hard stop(-0.7)` 완화 또는 `30~45초 grace` | `35초 / -0.71%` 손절을 직접 완화한다 | 매우 높음 | 눌림 구간 손실 확대로 이어질 수 있다 | 3 |
| C | `fallback` 전용 `60~120초` 미전환 hard time stop | 완만한 실패 진입을 별도 규칙으로 정리한다 | 중간 | 현재 `35초` 손절 표본에는 단독 효과가 약하다 | 2 |

비교 축:
- `손절 건수`
- `평균 손실폭`
- `1분 내 양전환 실패율`
- `실현손익`

- [x] `OPEN_RECLAIM` 조기손절 후보안 비교표 작성

| 후보 | 변경안 | 기대효과 | 현재 표본 적합도 | 주요 리스크 | 오늘 기준 우선순위 |
| --- | --- | --- | --- | --- | --- |
| A | `AI early exit min hold 180초 -> 120초` 즉시 적용 | 장초 실패 reclaim을 더 빨리 정리할 여지를 본다 | 낮음 | 장초 흔들림에 과하게 잘릴 수 있다 | 3 |
| B | `low_score_hits 3회 -> 2회` 즉시 적용 | AI 연속 저점수 확인을 조금 더 빠르게 반영한다 | 중간 | 점수 노이즈에 민감해질 수 있다 | 2 |
| C | `never green`, `peak_profit 낮음` 결합 보조 gate | 회복 못 하는 reclaim을 별도 규칙으로 더 빨리 정리한다 | 높음 | 상승 재시도 직전 표본도 같이 잘릴 수 있다 | 1 |

비교 축:
- `손실 확대 방지`
- `조기 잘림 증가`
- `평균 보유시간`
- `실현손익`

메모:
- 현재 `OPEN_RECLAIM` 손절 2건은 모두 `180초`를 한참 지난 뒤 발생해 `min_hold` 직접 완화의 적합도는 상대적으로 낮다.
- `휴림로봇` 표본에서는 `2/3 -> 3/3` 차이가 약 `9초`라서, `low_score_hits 3 -> 2`만으로는 개선폭이 제한적일 수 있다.
- [x] `SCANNER` / fallback 지연 손절 후보안 비교표 작성

| 후보 | 변경안 | 기대효과 | 현재 표본 적합도 | 주요 리스크 | 오늘 기준 우선순위 |
| --- | --- | --- | --- | --- | --- |
| A | `never_green + near_ai_exit 지속` 보조 gate | 양전환 못 한 fallback 번들을 더 빨리 정리한다 | 매우 높음 | 재상승 직전 표본을 일찍 잘릴 수 있다 | 1 |
| B | `fallback` 번들 전용 `5~7분` time stop | `733초` 장기 손실 보유를 직접 줄인다 | 높음 | 느린 우상향 회복 기회를 놓칠 수 있다 | 2 |
| C | `fallback_scout/main` 비중 축소 | 같은 지연 손절이 나와도 절대 손실을 줄인다 | 중간 | 손절 타이밍 문제는 그대로 남는다 | 3 |

메모:
- `현대건설`은 `min_hold=180초` 부족 문제가 아니라, `near_ai_exit` 상태가 오래 지속돼도 `low_score_hits 3/3` 누적 전까지 청산되지 않은 케이스다.
- 따라서 `SCANNER/fallback`은 `OPEN_RECLAIM`과 별도로 보고, `never_green` 또는 `near_ai_exit 지속시간` 기반 보조 gate를 우선 검토한다.
- [x] 오늘 즉시 진행할 스캘핑 로직 보완 범위 확정
  - `OPEN_RECLAIM`: `never_green + peak_profit 낮음` 보조 gate 우선
  - `SCANNER/fallback`: `never_green + near_ai_exit 지속` 또는 `fallback 번들 time stop` 우선
  - `SCALP_BASE/fallback`: 공통 완화보다 `position_tag` 한정 출구 정책 분리를 우선
- `2026-04-08 12:03 KST` 코드/운영 반영 상태 확인
  - `OPEN_RECLAIM`: `scalp_open_reclaim_never_green` 출구 룰 반영
  - `SCANNER/fallback`: `scalp_scanner_fallback_never_green` 출구 룰 반영
  - `SCALP_BASE/fallback`: `preset_hard_stop_grace`(35초 유예 + 비상손절) 반영
  - 스캘핑 절대 투자금 상한: `SCALPING_MAX_BUY_BUDGET_KRW=2,000,000` 적용 유지
- [x] shadow band 1일차 결과 요약
  - `near_ai_exit`, `near_safe_profit` 때문에 review로 간 건수를 초안 수준으로라도 집계
  - `2026-04-08 12:03 KST` 기준 `trade-review event_breakdown`에서 `ai_holding_shadow_band=605건`
  - 동일 시점 raw stage 로그(회전본 포함) 집계: `621건 (review 593 / skip 28)`
  - 근접 플래그 분포(raw): `near_ai_exit=True 74건`, `near_safe_profit=True 12건`, 동시 충족 `0건`
  - 1차 해석: review 비중은 높지만(`95.5%`), near-band 직접 기여 표본은 제한적(`13.8%`)이라 `sig_changed/age_expired` 축과 함께 병행 분석 필요
- [x] 진입 민감도 완화안 1차 즉시 적용
  - 적용 목표: `blocked_strength_momentum` 비중 완화(스캘핑 한정)
  - 적용 원칙: `과열 차단(blocked_overbought)`은 유지하고, `strength_momentum` 계열만 국소 완화
  - 적용 범위: `VWAP_RECLAIM`, `OPEN_RECLAIM` 우선, `SCANNER`는 후순위
  - `2026-04-08 12:48 KST` 적용값: `SCALP_VPW_RELAX_TAGS=(VWAP_RECLAIM, OPEN_RECLAIM)`, `min_base 95→93`, `min_buy_value 20,000→16,000`, `min_buy_ratio 0.75→0.72`, `min_exec_buy_ratio 0.56→0.53`
- [x] 청산 민감도 완화안 1차 즉시 적용
  - 적용 목표: `조기 청산 과민` 완화(`scalp_ai_momentum_decay`, `scalp_ai_early_exit`의 과잉 반응 완화)
  - 적용 원칙: `하드 손절선`은 유지하고, `신호 확인 횟수/유예시간` 중심으로 조정
  - 적용 범위: `OPEN_RECLAIM`, `SCANNER/fallback`, `SCALP_BASE/fallback` 순서로 분리 적용
  - `2026-04-08 12:48 KST` 적용값: `OPEN_RECLAIM ai_low_score_hits 필요치 3→4`, `scalp_ai_momentum_decay`는 `score<45` + `보유 90초 이상`일 때만 발동
- [x] 즉시 적용용 롤백 가드 문서화
  - 공통: `한 번에 1개 파라미터만` 적용
  - 롤백 조건: 적용 후 `30~60분` 내 손절 건수/평균 손실폭이 기준 대비 급증하면 즉시 원복
  - 기록 규칙: 변경시각, 파라미터, 기대효과, 실제결과를 체크리스트에 누적
- [x] 추가매수 성과/시점 점검 기준 설계
  - `performance-tuning`에 `AVG_DOWN`, `PYRAMID`, `no-add`를 나란히 비교하는 축을 정의
  - `holding_add_history`, `scale_in_executed`, `ADD_SIGNAL`, `trade-review add_count`를 어떤 순서로 연결할지 정리
  - `효과성`과 `시점 적절성` 지표를 분리해서 설계
- [x] 추가매수 초기 관찰 지표 정의
  - `AVG_DOWN 회복률`, `PYRAMID 수익 확장률`, `add lock/cancel 비율`을 1차 후보로 둔다
  - `signal_profit_rate`, `pullback_from_peak`, `time bucket` 기준 timing 라벨(`too_early`, `in_band`, `too_late`) 초안 작성
- [x] 공통 hard time stop 설계용 기초 표본 정리
  - 긴 보유 손실 거래를 `entry_mode`, `position_tag`, `peak_profit`, `시간대` 기준으로 분해
  - `fallback 전용 cut`과 `OPEN_RECLAIM 지연 손절 보정`이 공통 hard time stop보다 먼저 설명되는지 함께 확인
- [x] 스윙 0진입 원인 일일 분류
  - `RISK_OFF / allow_swing_entry=false` day인지 먼저 판정
  - 그 다음 `Gatekeeper reject day`인지, `swing gap day`인지, 기타 실행 차단인지 분리
- [ ] 스윙 Gatekeeper missed case 정리
  - `blocked_gatekeeper_reject` 종목 중 이후 추세가 실제로 좋았던 표본이 있었는지 확인
  - `dual_persona_shadow`가 `ALLOW` 또는 더 공격적인 결론이었던 케이스를 같이 기록
- [x] 스윙 gap 완화 검토 전제 확인
  - 실제 `blocked_swing_gap` 샘플이 있었는지 먼저 확인
  - 샘플이 없으면 gap 완화 논의는 다음날로 미룬다
- [x] 듀얼 페르소나 충돌률 분해 지표 고정
  - `raw_conflict_ratio(agreement_bucket!=all_agree)`와 `effective_override_ratio(fused_action!=gemini_action)`를 분리해 같은 카드에서 함께 본다
  - 당일 기준값(`conflict 높고 override 낮음`)을 baseline으로 기록한다
- [x] Gatekeeper 듀얼 페르소나 재활성화 기준 문서화
  - `gatekeeper_eval_ms_p95`, `dual_persona_extra_ms_p95`, `effective_override_ratio`, `sample 수` 기준을 수치로 고정
  - `전면 on` 전에 `canary(스윙/KOSPI_ML 한정)` 단계와 즉시 rollback 기준을 명시
- [x] 듀얼 페르소나 재활성화 전 점검표 작성
  - `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER` 상태를 일일 점검 항목에 추가
  - 재기동 시점과 재활성화/비활성화 변경 이력을 체크리스트에 누적 기록

## 공통 Hard Time Stop 기준 설계 체크

- [x] 단순 `N분 청산`으로 갈지, 조건부 hard stop으로 갈지 먼저 결정
- [x] 최소 분류 축 확정
  - `entry_mode`
  - `position_tag`
  - `peak_profit`
  - `current profit_rate`
  - `AI score 추이`
  - `time-of-day`
- [x] 비교 후보안 작성
  - `3분`, `5분`, `7분` 단일 cut
  - `5분 + 저점수`
  - `fallback 전용 3~5분 cut`
  - `수익 미전환 + 장시간 보유` 조건부 cut
- [ ] 오늘 포함 최근 거래일에서 각 후보안이 승률/손익에 주는 영향 추정

## 2026-04-08 장마감 후속작업 완료결과 (15:01 KST 기준)

데이터 기준:
- `trade-review`: `/api/trade-review?date=2026-04-08&top=200`
- `performance-tuning`: `/api/performance-tuning?date=2026-04-08&since=09:00:00&top=200`
- raw 로그: `logs/sniper_state_handlers_info.log*`

핵심 결과:
- 스캘핑 `12건` 완료, 승률 `25.0%(3/12)`, 평균 손익률 `-0.275%`, 실현손익 `-66,367원`
- `fallback` 진입 `5건` 전패(승률 `0%`), 평균 손익률 `-0.726%`, 실현손익 `-27,742원`
- 동일 종목 내 `수익/손실`이 혼재한 케이스 확인(`현대건설`, `휴림로봇`)
  - 종목 선정보다 `진입 타이밍/출구 선택` 문제가 손익 악화를 키운 day로 분류
- `scalp_ai_early_exit` 종료 `4건` 전부 손실(승률 `0%`, 실현손익 `-9,440원`)
- `exit_rule='-'` 미복원 거래 `4건`이 `-59,882원`을 차지해 복기 블라인드 스팟이 큼

진입/탈출 보완안 1차 적용 후(12:48 KST) 관찰:

| 구간 | 종료건수 | 승률 | 평균 손익률 | 실현손익 | 메모 |
| --- | ---: | ---: | ---: | ---: | --- |
| `12:48` 이전 | 9 | 33.3% | -0.290% | -66,367원 | 대손실 2건 포함(`씨아이에스`, `산일전기`) |
| `12:48` 이후 | 3 | 0.0% | -0.230% | 0원 | 표본은 적지만 대손실 재발은 없었음 |

보유 AI 재사용/성능 관찰:
- `ai_holding_shadow_band` raw 집계: `616건 (review 574 / skip 42)`
- 근접 플래그: `near_ai_exit=True 66건`, `near_safe_profit=True 12건`, 동시 충족 `0건`
- `holding_skip_ratio=6.8%`, `holding_ai_cache_hit_ratio=0.2%`
- `gatekeeper_fast_reuse_ratio=0.0%`, `gatekeeper_eval_ms_p95=13,524ms`

스윙/듀얼 페르소나 분류:
- market regime snapshot: `risk_state=RISK_OFF`, `allow_swing_entry=false`, `swing_score=-10`
- `blocked_swing_gap=38,499`, `blocked_gatekeeper_reject=33`, `blocked_zero_qty=2`
- `dual_persona_shadow=13`, `raw_conflict_ratio=84.6%`, `effective_override_ratio=0.0%`, `dual_persona_extra_ms_p95=7,666ms`
- 결론: 스윙은 `market-regime 제한 + gap 차단 편중` day로 분류

## 2026-04-09 장전 작업계획

상세 체크리스트는 [2026-04-09-stage2-todo-checklist.md](./2026-04-09-stage2-todo-checklist.md)로 분리해 운영한다.

1. `fallback` 진입 실패 억제
  - `fallback` 전용 진입 강도 하향(비중/트리거 중 1개만) canary 적용
  - 목표: `fallback` 승률 `0% -> 25%+` 또는 손실총액 `-27,742원` 대비 `50%` 이상 축소
2. `OPEN_RECLAIM` / `SCANNER` 출구 분리 튜닝
   - `scalp_ai_early_exit` 전용으로 `never_green` 우선 청산 vs `한 번 양전환` 케이스를 분리
   - 목표: `scalp_ai_early_exit` 손실 편중 완화(4전 전패 재발 방지)
3. `exit_rule='-'` 복원 정확도 우선 보정
   - 누락 4건의 종료 규칙 역추적 로직 점검 및 리포트 반영
   - 목표: `exit_rule` 미복원율 `0%`에 근접
4. Gatekeeper/Dual Persona 재활성화 전제 고정
   - 재활성화 조건: `dual_persona_extra_ms_p95 <= 2500`, `effective_override_ratio >= 3%`, `samples >= 30`, `gatekeeper_eval_ms_p95 <= 5000`
   - 미달 시 `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER=False` 유지
5. 공통 hard time stop은 shadow 평가만 수행
   - 실전 적용 금지 유지, `fallback`/`OPEN_RECLAIM` 트랙 분리 우선
   - 후보안(`3/5/7분`, 조건부 cut)은 장후 재현 평가 후에만 승격

## 오늘은 아직 바꾸지 않을 것

- [ ] `near_safe_profit` 수치 직접 하향
- [ ] `near_ai_exit` 수치 직접 완화
- [ ] 공통 hard time stop 실전 적용
- [ ] fallback 전면 차단
- [ ] 스캘핑 공통 손절값 일괄 완화
- [ ] 추가매수(`AVG_DOWN` / `PYRAMID`) 임계값 직접 완화
- [ ] 스윙 AI threshold 직접 완화
- [ ] `RISK_OFF` 상태의 스윙 허용 기준 완화
- [ ] `OPENAI_DUAL_PERSONA_APPLY_GATEKEEPER` 당일 재활성화
- [ ] `dual_persona_shadow`의 스윙 실전 승급
- [ ] 스윙 gap 기준 직접 완화

## 오늘 작업 완료 기준

- [x] 어제 반영한 `ai_holding_shadow_band` 로그가 실제 장중 로그에 찍힌다
- [x] fallback/normal 비교표가 나온다
- [x] hard time stop 설계 후보안 2~3개와 각각의 장단점이 문서화된다
- [x] `SCALP_BASE/fallback` 과민 손절과 `OPEN_RECLAIM` 지연 손절을 분리한 비교표가 남는다
- [x] `fallback 전용 후보안`과 `OPEN_RECLAIM 전용 후보안`이 각각 2~3개 이상 문서화된다
- [x] 진입 민감도 완화안 1차 실전 적용 + 결과 기록이 남는다
- [x] 청산 민감도 완화안 1차 실전 적용 + 결과 기록이 남는다
- [x] 즉시 적용 롤백 가드(30~60분 기준) 실행 기록이 남는다
- [x] `2026-04-09`에 바로 이어서 판단할 수 있을 수준의 근거가 정리된다
- [x] 스윙 day를 `market-regime 제한` / `gatekeeper 거부 중심` / `gap 차단 중심` 중 하나로 분류할 수 있다
- [ ] 스윙 missed case 요약표가 남고, threshold 완화 검토 여부를 근거 기반으로 말할 수 있다
- [x] 듀얼 페르소나 `raw conflict` / `effective override` 분리 리포트가 남는다
- [x] Gatekeeper 듀얼 페르소나 재활성화 기준 + canary/rollback 절차가 문서화된다
- [x] 추가매수(`AVG_DOWN` / `PYRAMID`) 점검 기준이 `performance-tuning` 계획안에 포함된다
- [x] 추가매수 효과성/시점 적절성을 설명할 1차 지표 세트가 문서화된다

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-09-stage2-todo-checklist.md](./2026-04-09-stage2-todo-checklist.md)
- [2026-04-07-performance-tuning-checklist.md](./2026-04-07-performance-tuning-checklist.md)
- [2026-04-07-stage2-task1-execution-report.md](./2026-04-07-stage2-task1-execution-report.md)
- [2026-04-07-swing-results](./2026-04-07-swing-results)
