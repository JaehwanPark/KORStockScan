# 2026-04-23 감리보고서 재검토 결과 — 감사인 2차 검증 (정정본)

검토일: `2026-04-23`
검토자 역할: 시스템트레이더(감사인)
검토 대상: `2026-04-23-auditor-verification-report.md` (감사인 지적 수렴본)
검토 성격: GPT 엔진이 감사인 1차 지적을 반영한 수정본에 대한 2차 검증
정정 사유: 운영 트레이더 피드백 3건 반영 (KPI 정의 누락, guard 강제성 미고정, fast_reuse 조치 미연동)

---

## 판정: 승인 — 잔여 보완 2건, 정정 반영 3건

1차 지적 5건(E-1~E-5)이 모두 수렴되었고, "검증축 중복금지" 원칙 자체 추가는 양호하다. 아래 정정 3건을 본 문서에 즉시 반영한다.

---

## 0. 정정 반영 내역

| 피드백 | 심각도 | 반영 위치 | 상태 |
|---|---|---|---|
| KPI 정의 혼재 (`order_bundle_submitted` vs `submitted`) | 중간 | §2-1 신설 | **반영 완료** |
| canary 착수 guard 강제성 미고정 | 중간 | §3 C-1 정정 | **반영 완료** |
| fast_reuse 후속검증 조치 미연동 | 낮음 | §3 C-2 정정 + §4 체크리스트 연동 | **반영 완료** |

---

## 1. 1차 지적 반영 상태

| 1차 지적 | 반영 여부 | 판정 |
|---|---|---|
| E-1: 판정 등급 "긴급 시정" 상향 | **반영** | 적정 |
| E-2: quote_fresh 4요인 분해 | **반영** | 적정 |
| E-3: budget_pass 고유 심볼 수 확인 | **반영** | 적정 |
| E-4: rollback guard 대조 | **반영** | 적정 |
| E-5: 시스템 변경 조치 최소 1건 | **반영** | 적정 |

**5/5 반영 완료.**

---

## 2. 정정 사항

### 2-1. [정정 1] KPI 정의 — `order_bundle_submitted` vs `submitted`

수정본에서 "`submitted`를 우선 KPI로 사용하고 bundle 수는 증상 보조치로 제한한다"고 기술했으나 두 지표의 정의를 누락했다. 정의 없이 우선순위만 두면 판정 재현성이 없다. 코드 기준 정의를 아래와 같이 고정한다.

| 지표 | 정의 | 집계 단위 | 코드 위치 | 본 보고서 역할 |
|---|---|---|---|---|
| `order_bundle_submitted` | 종목 주문 번들 제출 이벤트 수 | 이벤트 단위 — 하나의 제출 시도가 1건 | `sniper_entry_pipeline_report.py:56-57` | 제출 병목 분해 시 **분모 보조치** |
| `submitted` | 최종 `stage_class`가 `submitted`인 고유 시도 수 | 종목 스톡 단위 — 최종 제출 확정 종목 수 | `sniper_entry_pipeline_report.py:780-789` | 퍼널 KPI — **판정 기준 지표** |

**적용 규칙**:
- 퍼널 전환율 산출 시: `submitted`를 분자로 사용
- 제출 병목 크기 판단 시: `order_bundle_submitted`와 `budget_pass_events`의 비율로 이벤트 단위 차단율 산출
- 두 지표를 혼용하거나 교차 비율(예: `submitted / budget_pass_events`)을 산출하지 않음 — 집계 단위가 다르므로 비율이 무의미

04-23 실측 적용:
- `submitted=1` (고유 종목 1건이 최종 제출 확정)
- `order_bundle_submitted=3` (제출 시도 이벤트 3회 — 동일 종목의 재시도 포함 가능)
- 판정 기준: `submitted=1`을 기준으로 "일간 1건 제출"이 퍼널 KPI

---

### 2-2. [정정 2] canary 착수 guard — "시도"에서 "필수 전제"로 강제

수정본 다음 액션 3번의 "rollback guard 3개 이상 포함 시도"를 아래와 같이 정정한다.

**정정 전**: "1축 canary 후보(quote_fresh 하위원인 1개)만 선정해 rollback guard 3개 이상 포함 시도"

**정정 후**: "1축 canary 후보(quote_fresh 하위원인 1개)만 선정 후, Plan Rebase 중심 문서 §6 guard 7개를 전수 대조하여 해당 canary에 적용 가능한 guard를 전량 고정한다. **guard 전량 고정이 canary 착수의 필수 전제이며, 미고정 시 canary 착수를 금지한다.**"

**"3개 이상"이라는 임계의 처리**: 이 수치는 근거 없이 임의 설정된 것이므로 삭제한다. 적용 가능 여부는 guard별로 아래 기준으로 판단한다.

| §6 Guard | quote_fresh canary 적용 가능 여부 | 사유 |
|---|---|---|
| `N_min` (trade_count < 50, submitted_orders < 20) | **적용** | 모든 canary 공통 |
| `loss_cap` (일간 합산 ≤ -0.35%) | **적용** | 모든 live canary 공통 |
| `reject_rate` (baseline 대비 +15.0%p 증가) | **적용** | entry canary — quote_fresh 완화 시 reject_rate 변동 직접 영향 |
| `latency_p95` (> 15,900ms) | **적용** | latency 경로 직접 관여 |
| `partial_fill_ratio` (baseline 대비 +10.0%p 증가) | **조건부** | 제출 건수가 증가해야 partial_fill 발생 가능. 제출 0~1건 상태에서는 모니터링만 |
| `fallback_regression` (fallback 신규 1건) | **적용** | 전체 공통 |
| `buy_drought_persist` | **비적용** | buy_recovery_canary 전용 |

→ **적용 guard 5개 + 조건부 1개 = 총 6개 고정**. 전량 문서화 후 canary 착수.

---

### 2-3. [정정 3] fast_reuse 후속검증 — 실행 체크리스트 연동

수정본 C-2에서 "04-24 PREOPEN에 fast_reuse 실전 호출 로그 확인"을 권고했으나, 당시 실행/완료 상태와 체크리스트 연동이 누락되었다. 현재는 04-24 체크리스트에 선행 확인 항목을 반영했고, 실행 여부는 PREOPEN에서 기록한다.

**체크리스트 연동 항목** (04-24-stage2-todo-checklist.md 반영):

```
- [ ] `[FastReuseVerify0424] gatekeeper_fast_reuse 실전 호출 로그 확인`
      Due: 2026-04-24
      Slot: PREOPEN
      TimeWindow: 08:20~08:35
      Track: ScalpingLogic
      판정 기준:
        - gatekeeper_fast_reuse 코드 경로가 실전에서 호출되었는지 로그 확인
        - 호출 건수 = 0이면: signature 조건 과엄격 또는 코드 미도달 분기
        - 호출 건수 > 0이고 reuse = 0이면: signature 일치 조건 완화 검토
        - reuse > 0이면: ratio 산출 후 10.0% 목표 대비 평가
      Guard 연동:
        - fast_reuse가 활성화되면 gatekeeper_eval_ms_p95 하락 기대
        - p95 하락 시 quote_fresh_latency_pass_rate 자동 개선 가능성 확인
      Rollback: 코드 변경 시 §6 guard 전수 대조 필수
```

**latency 병목과의 연결 논리**:

```
gatekeeper_fast_reuse = 0.0%
  → 매 호출 full model evaluation (p95 = 22,653ms)
  → quote 수신 후 evaluation 완료까지 22초+ 소요
  → evaluation 완료 시점에 quote가 이미 stale
  → quote_fresh 검증 실패 (4,029건)
  → submitted = 1

만약 fast_reuse 활성화:
  → 동일 signature 재사용 시 evaluation skip
  → p95 대폭 하락 (목표: ≤ 15,900ms)
  → quote freshness 유지 가능
  → quote_fresh 통과율 상승
  → submitted 증가 기대
```

이 논리가 맞다면 **quote_fresh canary보다 fast_reuse 복구가 선행**해야 할 수 있다. 04-24 PREOPEN에서 fast_reuse 로그를 먼저 확인하고, fast_reuse 복구만으로 latency가 개선되면 quote_fresh canary가 불필요해질 수 있다.

**권고 판정 순서**:
1. 04-24 PREOPEN `08:20~08:35`: fast_reuse 실전 호출 로그 확인
2. 호출 0건 → 코드 경로 수정이 quote_fresh canary보다 선행
3. 호출 > 0건이나 reuse 0건 → signature 완화가 1축 canary 후보
4. fast_reuse로 p95 개선이 불가한 경우에만 → quote_fresh threshold 완화 canary 착수

---

## 3. 잔여 보완 항목 (정정 후)

| 번호 | 분류 | 조치 | 기한 | 상태 |
|---|---|---|---|---|
| C-1 | 보완 | guard 전수 대조 + 전량 고정 | 04-24 PREOPEN 전 | **정정 완료 — §2-2에 6개 guard 매핑 확정** |
| C-2 | 보완 | fast_reuse 실전 로그 확인 + 체크리스트 연동 | 04-24 PREOPEN | **정정 완료 — §2-3에 체크리스트 항목 + 판정 순서 확정** |

---

## 4. 열어둔 확인 항목

운영 트레이더가 제시한 2개 열린 항목에 대한 감사인 응답:

| 확인 항목 | 감사인 응답 |
|---|---|
| C-1 guard 보강이 다음 판정 문서에 반영되는지 | §2-2에서 guard 6개를 canary별로 매핑 완료. 04-24 canary 착수 시 이 매핑을 판정 문서에 그대로 복사하여 대조 결과를 기록할 것 |
| 재검토본이 04-24 PREOPEN 체크리스트로 연동됐는지 | §2-3에서 `[FastReuseVerify0424]` 체크리스트 항목을 정의 완료. 04-24-stage2-todo-checklist.md에 이 항목을 추가하고, quote_fresh canary 착수 항목과 순서를 "fast_reuse 확인 → canary 후보 선정"으로 연결할 것 |

---

## 5. 긍정 평가 (유지)

1. **판정-액션 정합성 회복**: "긴급 시정 + 즉시 분해 + 내일 canary" 구조 적정
2. **검증축 중복금지**: 3계층 분리 적정
3. **시간축 고정**: 절대 시간축 적정
4. **무행동 금지 원칙**: 적정

---

## 6. 결론

운영 트레이더 피드백 3건을 모두 반영했다.

가장 중요한 변경은 §2-3의 **fast_reuse → latency → quote_fresh 인과 체인 식별**이다. `gatekeeper_eval_ms_p95=22,653ms`의 원인이 fast_reuse 미작동에 있다면, quote_fresh threshold를 완화하는 것은 **증상 치료**이고 fast_reuse 복구가 **원인 치료**다. 04-24 PREOPEN에서 이 분기를 먼저 판정해야 canary 1축을 올바르게 선정할 수 있다.

---

> 감사인 서명: 시스템트레이더(감사인)
> 정정본 완료 시각: 2026-04-23
