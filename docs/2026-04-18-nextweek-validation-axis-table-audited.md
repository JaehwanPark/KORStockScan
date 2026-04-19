# 2026-04-18 다음주(2026-04-20~2026-04-24) 일자별 검증축 표

> **[감사인 수정보완 이력]**
> 검토일: 2026-04-18 | 검토자 역할: 시스템트레이더(감사인)
> 원본 대비 하단 **§ 감사인 검토 의견** 섹션 추가. 원본 표는 변경 없이 보존.

---

## 원본 계획표

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

---

## § 감사인 검토 의견

> 검토일: 2026-04-18
> 검토 역할: 시스템트레이더(감사인)
> 검토 범위: 2026-04-20~04-24 주간 검증축 전체 구조 및 행별 실행계획
> 결론: **조건부 실행 가능 — 아래 지적사항 중 [필수] 항목 4건은 실행 전 확정 필요**

---

### 1. 구조적 지적사항 (계획 전체에 해당)

#### [지적 S-1] 월요일 동시 shadow 과적재 — **필수 시정**

- **지적 내용**: 2026-04-20(월) 하루에 shadow 착수축이 6개, 실표본 검증 1개로 총 7개가 병렬 가동된다. 동일 세션에서 7개 축이 로그·집계 파이프라인을 공유할 경우, 지표 변동의 원인귀속이 불가능해진다. 특히 split-entry 3개 서브축(rebase/즉시재평가/cooldown)은 상호작용이 직접적이어서 개별 효과 분리가 사실상 불가하다.
- **위험 등급**: 상(High) — 이후 모든 판정의 근거 데이터 신뢰성에 영향
- **권고조치**: split-entry 3개 서브축은 순차 도입(예: rebase D+0, 즉시재평가 D+1, cooldown D+2)하거나 완전히 독립된 shadow slot으로 분리. 월요일 동시 착수축은 최대 3개로 제한.

#### [지적 S-2] 승격 판정 기준의 수치 미정의 — **필수 시정**

- **지적 내용**: 표 전반에 걸쳐 "표본 부족 시 결론 유예"라는 조건이 반복되나, 판정 실행을 위한 최소 표본 수(N_min), 최소 효과크기(Δ_min), 유의수준(α)이 어느 행에도 명시되어 있지 않다. 수치 없는 판정 조건은 실행 시점에 담당자의 주관적 해석에 의존하게 되어 일관성을 보장할 수 없다.
- **위험 등급**: 상(High)
- **권고조치**: 각 판정 행에 최소 `N_min`, `Δ_min`, `판정 기준 지표명` 3개 필드를 추가 정의. 예시: `N_min=50건 진입이벤트, Δ_min=+3% fill_rate, α=0.05`.

#### [지적 S-3] 정량 Rollback 트리거 미정의 — **필수 시정**

- **지적 내용**: 2026-04-20(월) HOLDING schema 행에 "rollback guard 점검"이 언급되나 발동 조건이 수치화되어 있지 않다. 이는 다른 shadow 행에도 공통적으로 해당된다. 수치 없는 rollback guard는 위기 시 즉각 발동이 불가하며 사후 판단에 의존하게 된다.
- **위험 등급**: 상(High)
- **권고조치**: 공통 rollback 발동 기준 정의서를 별도 작성하고 본 표에서 참조. 최소 포함 항목: reject rate 허용 변동폭, partial fill 비율 하한, latency p95 상한, 동일 종목 재진입 빈도 상한.

#### [지적 S-4] HOLDING schema 변경과 성과 판정의 측정 오염 — **필수 시정**

- **지적 내용**: 2026-04-20(월) HOLDING action schema를 shadow로 변경한 직후, 2026-04-21(화) HOLDING shadow 성과를 판정한다. 측정 도구(schema)를 변경한 뒤 곧바로 그 도구로 측정한 값을 판정 근거로 사용하는 것은 자기참조 오류다. schema 변경 전 baseline 지표와의 비교 가능성이 훼손된다.
- **위험 등급**: 상(High)
- **권고조치**: HOLDING schema 변경(월) 이후 최소 1세션(1영업일) 관측 버퍼를 두고, 변경 전 baseline을 동일 스키마로 재계산한 뒤 비교. 화요일 판정 일정은 수요일로 이전 검토.

#### [지적 S-5] Market Regime 통제 변수 부재 — 권고

- **지적 내용**: 주간 계획 전반에 검증 기간의 시장 환경(변동성 수준, 거래대금, 섹터 로테이션 등)에 대한 조건부 판정 기준이 없다. 저변동 주간에 통과한 축이 고변동 환경에서 무너지는 경우, 다음 주 canary 확대 결정의 일반화 근거가 약해진다.
- **위험 등급**: 중(Medium)
- **권고조치**: 금요일 주간 판정 시 해당 주 regime 태그(저변동/평상/고변동) 및 일평균 거래대금 수준을 판정 기록에 병기. canary 승격 권고안에 "regime 조건부 유효" 여부를 명시.

#### [지적 S-6] 주간 판정 규칙의 과도한 이진화 — 권고

- **지적 내용**: 2026-04-24(금) 주간 통합 판정이 "승격 1축 or 보류" 이진 구조로 고정되어 있다. "한 축 canary 원칙"은 상관관계 있는 축들 간에는 타당하나, 로그·집계·실행 경로가 독립적인 축이 동시에 기준을 충족하는 경우를 원천 배제하는 것은 과도한 제약이다.
- **위험 등급**: 중(Medium)
- **권고조치**: 규칙을 "**canary는 1개 축 유지 / 독립축은 shadow 최대 2개 병렬 허용**"으로 개정. 독립성 판단 기준(공유 코드패스 없음, 집계 지표 비중복)을 사전 정의.

---

### 2. 행별 지적사항

| 일자 | 검증축 | 감사 지적사항 | 권고조치 |
|---|---|---|---|
| 04-20 (월) | split-entry rebase shadow 1일차 | 동시 가동 3개 서브축 중 첫 번째. S-1 적용. "결론 유예" 조건 수치 미정의. S-2 적용. | 단독 슬롯 배정 또는 순차 도입. N_min·Δ_min 수치 추가. |
| 04-20 (월) | split-entry 즉시 재평가 shadow 1일차 | 동시 가동 3개 서브축 중 두 번째. S-1 적용. 오탐 진입 증가 위험 인식 있으나 임계값 미정. | D+1 이후로 이전. 오탐 허용 상한(예: false_entry_rate ≤ 기준값) 정의 후 착수. |
| 04-20 (월) | same-symbol split-entry cooldown shadow 1일차 | 동시 가동 3개 서브축 중 세 번째. S-1 적용. cooldown 과도 적용 위험 인식 있으나 min/max cooldown 범위 미정. | D+2 이후로 이전. cooldown 파라미터 범위 사전 고정 후 shadow 진입. |
| 04-20 (월) | latency canary bugfix-only 재판정 | 비교 baseline의 관측창이 명시되지 않음(전주 동일 시간대인지, 직전 N세션인지 불명). baseline 미고정 시 개선효과 과대/과소 평가 가능. | baseline 관측창 명시(예: "직전 5영업일 동일 시간대 p50/p95"). |
| 04-20 (월) | HOLDING action schema shadow-only 착수 | S-3(rollback 트리거 미정), S-4(성과 판정과 측정 오염) 동시 적용. rollback guard가 "점검" 수준으로만 기술됨. | rollback 발동 수치 정의 후 착수. 성과 판정은 최소 D+2(수) 이후로 이전. |
| 04-20 (월) | partial-only timeout shadow 1일차 | 조기 timeout의 기회비용을 측정할 counterfactual 지표 없음. timeout으로 취소된 주문이 이후 Δt 내 동일 호가에서 체결됐을 경우의 성과 손실을 정량화하는 방법이 부재. | timeout 후 Δt(예: 5분) 내 동일 종목·호가 체결 여부 추적 지표 추가. |
| 04-20 (월) | OpenAI 라우팅/감사필드 실표본 검증 | Gemini fallback 가능성 인식 있으나 fallback 발생 시 감사필드 동등성 검증 절차가 없음. fallback 경로의 지표 포함 여부가 불명확하면 감사 실효성 저하. | fallback 경로별 감사필드 포함 여부 매트릭스를 사전 정의. |
| 04-21 (화) | split-entry leakage canary 승격/보류 판정 | 1일차 shadow 데이터만으로 canary 승격 결정. S-2 적용. 단일 세션은 하나의 market regime에 해당하며 일반화 근거 불충분. | 판정 기준 수치(N_min, Δ_min) 충족 여부를 선행 확인. 미충족 시 관측 연장 rule 명시. |
| 04-21 (화) | HOLDING shadow 성과 판정 | S-4 적용. schema 변경 직후 판정으로 측정 오염 위험. 3개 지표(missed_upside_rate/capture_efficiency/GOOD_EXIT) 중 판정 우선순위 미정의. | 판정을 D+2(수) 이후로 이전. 지표 간 우선순위(primary/secondary) 사전 정의. |
| 04-21 (화) | 작업12 Raw 입력 축소 A/B 범위 확정 | 축소 범위의 신호 손실 위험 인식 있으나 정보 보존 평가 지표가 없음. 입력 축소량과 진입 품질 간 관계를 정량화하는 틀 부재. | A/B 설계 시 information retention metric(예: 핵심 피처 coverage rate) 포함. |
| 04-22 (수) | HOLDING critical 경량 프롬프트 분리 | HOLDING schema 변경(04-20)과 경량 프롬프트 변경(04-22)이 동일 주에 중첩. 성과 변동 시 schema 변경 vs 프롬프트 변경 중 원인귀속 불명. | shadow 비교표에 "schema 변경 효과"와 "프롬프트 변경 효과"를 별도 컬럼으로 분리 기록. |
| 04-23 (목) | 작업12 A/B 범위 확정 마감 | 화요일 확정 시도 후 목요일 마감으로 이중 기재. 두 행의 조건 분기(화요일 실패 시 목요일 재시도)가 명시적으로 기술되지 않아 책임 시점이 불명확. | "04-21 미확정 시 04-23 마감"임을 조건으로 명시. 담당자 및 escalation 경로 기재. |
| 04-24 (금) | 주간 판정 통합 | S-5(regime 태그 부재), S-6(이진 판정 과도) 적용. "한 축 canary 원칙"의 적용 범위가 정의되지 않아 독립축 병렬 승격 가능성을 불필요하게 차단. | regime 태그 병기. 독립축 병렬 canary 허용 규칙 추가 후 주간 판정 수행. |

---

### 3. 수정권고 요약 (Action Items)

아래 4건([필수])은 `2026-04-20 PREOPEN` 전 확정을 권고하며, 이후 2건([권고])은 주중 반영 가능.

| 번호 | 분류 | 조치 내용 | 기한 |
|---|---|---|---|
| A-1 | **필수** | 월요일 동시 shadow 착수축 3개 이하로 축소, split-entry 서브축 순차 이전 | 2026-04-20 PREOPEN 전 |
| A-2 | **필수** | 각 판정 행에 N_min·Δ_min·판정 기준 지표명 추가 정의 | 2026-04-20 PREOPEN 전 |
| A-3 | **필수** | 공통 rollback 발동 수치 정의서 작성 및 본 표에서 참조 | 2026-04-20 PREOPEN 전 |
| A-4 | **필수** | HOLDING 성과 판정을 04-22(수) 이후로 이전, baseline 재계산 방법 명시 | 2026-04-20 PREOPEN 전 |
| A-5 | 권고 | 금요일 주간 판정에 regime 태그 및 독립축 병렬 canary 허용 규칙 추가 | 04-24(금) 전 |
| A-6 | 권고 | latency canary baseline 관측창 명시, partial timeout counterfactual 지표 추가 | 04-20(월) 전 |

---

## 4. 실무 보완 체크리스트 (자동 파싱 대상)

- [ ] `[AuditFix0420] split-entry shadow 동시착수 3축 이하로 축소 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:00~08:10`, `Track: ScalpingLogic`)
  - 판정 기준: `rebase/즉시재평가/cooldown` 중 당일 활성 축을 명시하고 비활성 축은 다음 영업일로 이관
- [ ] `[AuditFix0420] 각 판정행 N_min/Δ_min/PrimaryMetric 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:10~08:20`, `Track: Plan`)
  - 판정 기준: 최소 표본·최소 효과크기·주지표가 문서에 숫자로 기록됨
- [ ] `[AuditFix0420] 공통 rollback trigger 수치표 확정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:20~08:30`, `Track: ScalpingLogic`)
  - 판정 기준: reject_rate/partial_fill_ratio/latency_p95/reentry_freq 상한·하한이 수치화됨
- [ ] `[AuditFix0420] HOLDING 성과 판정 D+2 이동 및 baseline 재계산 경로 고정` (`Due: 2026-04-20`, `Slot: PREOPEN`, `TimeWindow: 08:30~08:40`, `Track: AIPrompt`)
  - 판정 기준: 2026-04-21은 관측/재계산만 수행하고 성과판정은 2026-04-22로 이동
- [ ] `[AuditFix0424] 주간판정에 regime 태그 병기` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:30~15:40`, `Track: Plan`)
- [ ] `[AuditFix0424] canary 1축 원칙 + 독립축 shadow 병렬허용 규칙 재확인` (`Due: 2026-04-24`, `Slot: POSTCLOSE`, `TimeWindow: 15:40~15:50`, `Track: Plan`)

## 참고 문서

- [2026-04-20-stage2-todo-checklist.md](./2026-04-20-stage2-todo-checklist.md)
- [2026-04-21-stage2-todo-checklist.md](./2026-04-21-stage2-todo-checklist.md)
- [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md)
- [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md)
