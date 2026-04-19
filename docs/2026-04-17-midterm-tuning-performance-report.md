# 2026-04-17 튜닝 계획 대비 실적 및 성과 중간보고서

> 이 문서는 `2026-04-17` 고밀도 표본일 기준 **시점 진단본**이다.
> 현재 실행 기준은 [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md), 기본계획 대비 실행 변경은 [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md), 반복 baseline은 [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md)에서 관리한다.

작성일: `2026-04-17`  
기준 데이터: `data/report/monitor_snapshots/*_2026-04-17.json`, `analysis/gemini_scalping_pattern_lab/outputs/*`, `analysis/claude_scalping_pattern_lab/outputs/*`

## 1. 판정

1. `2026-04-17`은 운영기간 중 `거래수 최대`, `손실건수 최대`, `실현손익 최저`의 날이 맞다. 다만 동시에 `split-entry`, `holding/exit`, `entry blocker` 전 구간에서 가장 고밀도 표본을 확보한 날이기도 하다.
2. 현재 튜닝 계획은 `리포트 정합성 -> split-entry 누수 차단 -> HOLDING/청산 수익전환 -> 그 다음 진입확장` 순서로 재정렬하는 것이 맞다. `latency/tag/threshold`를 먼저 넓히는 것은 다음주 가시적 성과 확률을 낮춘다.
3. 다음주 손익을 익절 전환할 현실적인 경로는 `split-entry soft-stop 누수 억제`와 `HOLDING/청산 판단 분리` 2축을 먼저 닫는 것이다. 진입 완화는 그 뒤 `1축 canary`로만 다뤄야 한다.

## 2. 근거

### 2-1. 계획 대비 오늘까지 상태

| 축 | 계획상 목적 | 오늘까지 상태 | 판정 |
| --- | --- | --- | --- |
| `리포트/집계 정합성` | false loss, stale label, event/latest 혼선 제거 | `entry_pipeline latest/event`, `protect_trailing_stop` 라벨, `ghost shadow` 기준까지 문서/코드 반영 | `완료 유지` |
| `split-entry 누수 차단` | rebase/즉시재평가/재진입반복/partial 표류 분리 | shadow 기준 확정, 일부는 코드 shadow 반영 완료 | `다음주 최우선` |
| `HOLDING/청산 수익전환` | action schema/prompt split로 보유 판단 전용화 | 설계는 있으나 shadow 실전 착수는 미완 | `다음주 2순위` |
| `진입확장` | latency canary, tag/threshold 완화 | bugfix-only는 유효, broad relax는 아직 근거 부족 | `후순위 유지` |

### 2-2. 오늘 실적과 표본 밀도

- `trade_review_2026-04-17`
  - `total_trades=68`
  - `completed_trades=65`
  - `loss_trades=36`
  - `avg_profit_rate=-0.25%`
  - `realized_pnl_krw=-223,423`
- `performance_tuning_2026-04-17`
  - `order_bundle_submitted_events=67`
  - `position_rebased_after_fill_events=117`
  - `partial_fill_events=82`
  - `exit_signals=70`
- `post_sell_feedback_2026-04-17`
  - `evaluated_candidates=68`
  - `MISSED_UPSIDE=19`
  - `GOOD_EXIT=32`
  - `estimated_extra_upside_10m_krw_sum=1,612,548`
- `missed_entry_counterfactual_2026-04-17`
  - `evaluated_candidates=194`
  - `MISSED_WINNER=157`
  - `AVOIDED_LOSER=29`
  - `estimated_counterfactual_pnl_10m_krw_sum=1,896,874`

### 2-3. 오늘 손실과 맞바꾼 데이터의 객관적 가치

1. 직접 손실은 `-223,423원`이다.
2. 그러나 오늘은 단순 손실일이 아니라, 운영기간 전체에서 가장 많은 진단 입력을 확보한 날이다.
   - `거래수`: `68`건으로 직전 최대치 `31`건의 `2.19배`
   - `submitted`: `67`건으로 직전 최대치 `33`건의 `2.03배`
   - `rebase`: `117`건으로 직전 최대치 `64`건의 `1.83배`
   - `partial_fill`: `82`건으로 직전 최대치 `44`건의 `1.86배`
   - `post_sell 평가`: `68`건으로 직전 최대치 `30`건의 `2.27배`
   - `missed_entry 평가`: `194`건으로 직전 최대치 `124`건의 `1.56배`
3. 더 중요한 것은 "양"이 아니라 "핵심 패턴 점유율"이다.
   - `same_symbol_repeat_flag`: 전체의 `55.1%`
   - `partial_then_expand_flag`: 전체의 `52.2%`
   - `multi_rebase_flag`: 전체의 `52.2%`
   - `rebase_integrity_flag`: 전체의 `56.2%`
   - `split-entry + scalp_soft_stop_pct`: 전체의 `92.9%`
   - `full_fill + scalp_trailing_take_profit`: 전체의 `84.6%`
   - `split-entry + scalp_trailing_take_profit`: 전체의 `90.0%`
4. 결론적으로 오늘 데이터는 평시 하루치가 아니라 `2~3영업일 이상`의 진단 압축 효과가 있었다고 보는 것이 타당하다. 특히 `split-entry soft-stop` 손실축과 `trailing_take_profit` 수익축이 거의 같은 날에 대량 확보됐다는 점이 중요하다.
5. 다만 `missed_entry +1,896,874원`, `post_sell +1,612,548원`은 `10분 counterfactual / extra upside` 기반 추정치이므로 직접 실현가능 이익으로 합산하면 안 된다. 이 수치는 `오늘 손실을 보전할 여지`가 아니라 `어느 축을 먼저 손대야 하는지 보여주는 진단 가치`로 해석해야 한다.

### 2-4. 진입부터 청산까지 개선 가능성 예측

| 단계 | 현재 관측 | 개선 여지 | 신뢰도 | 해석 |
| --- | --- | --- | --- | --- |
| `WATCHING/진입 차단` | `MISSED_WINNER=157`, blocker는 `latency`, `AI threshold`, `overbought` 혼재 | `매우 큼` | `중간` | 기회비용은 크지만 broad relax는 오판 리스크가 커서 다음주 1순위는 아님 |
| `체결/분할진입` | `split-entry + soft_stop`가 핵심 손실축, rebase/repeat 이상치가 오늘 집중 | `매우 큼` | `높음` | 다음주 실손익 개선 레버리지가 가장 큼 |
| `보유/청산` | `MISSED_UPSIDE=19`, `capture_efficiency_avg_pct=39.8` | `큼` | `중상` | 손절을 줄이는 것만으로는 부족하고, 승자 보유 품질 개선이 필요 |
| `리포트/운영 정합성` | stale label, COMPLETED 오판정, event/latest 혼선이 정리 단계 | `중간` | `높음` | 직접 수익축은 아니지만 잘못된 튜닝을 막는 필수 축 |

추정:

1. 다음주 `가시적 성과`가 나올 확률은 `split-entry 누수 차단 + HOLDING 분리`를 순서대로 실행할 때가 가장 높다.
2. 반대로 `latency/tag/threshold`를 먼저 넓히면 거래수는 늘어도 손실축이 같이 확대될 가능성이 커서 `익절 전환 확률`은 낮아진다.
3. 운영 목표는 `거래 수 확대`가 아니라 `split-entry soft-stop 비중 축소`와 `post-sell missed_upside_rate 축소`다.

### 2-5. Gemini / Claude 인사이트 비교와 미진한 부분

| 구분 | 강점 | 한계 | 본 보고서 반영 방식 |
| --- | --- | --- | --- |
| `Gemini` | fallback 모멘텀 필터, partial fill 직후 시간제한 탈출, dynamic threshold 완화처럼 `기회 확대` 아이디어가 강함 | 표본 스펙과 안전장치보다 가설 제안 쪽 비중이 큼 | `후순위 기회확대 가설 저장소`로 사용 |
| `Claude` | full/partial/split 분리, 표본충분성, data-quality 우선, shadow-only 우선순위가 명확함 | upside 확대 아이디어는 Gemini보다 덜 공격적 | `다음주 운영 우선순위의 1차 기준`으로 사용 |

보완이 필요한 미진한 부분:

1. `Gemini 165건` vs `Claude cohort 합 148건`처럼 표본 스펙이 다르다. 절대치 우열 비교보다 `패턴 방향성`만 공통분모로 사용해야 한다.
2. 두 보고서 모두 최신 `2026-04-17 close` 스냅샷 기준으로 다시 묶인 `68/194` 레벨의 최종 수치를 운영계획에 직접 연결하지는 못했다.
3. 두 보고서 모두 `main/remote 다음 영업일 실행시각`까지는 고정하지 않았다. 이 부분은 본 보고서와 체크리스트에서 보완한다.

## 3. 다음 액션

### 3-1. 다음주 최우선 실행 순서

1. `2026-04-20 PREOPEN 08:00~08:30 KST`
   - `split-entry rebase 정합성`
   - `split-entry immediate recheck`
   - `same-symbol cooldown`
   - 위 3개 shadow 1일차 판정을 한 번에 닫고, live 승격 후보는 `1축만` 고른다.
2. `2026-04-20 PREOPEN 08:40~09:00 KST`
   - `HOLDING action schema shadow-only` 착수
   - `HOLDING_GENERAL / HOLDING_CRITICAL / PRESET_TP` 분리 착수 범위를 고정한다.
3. `2026-04-20 POSTCLOSE 15:30~16:40 KST`
   - `partial-only timeout shadow 1일차 판정`
   - `AIPrompt 작업 9/10/11` 진행
   - `HOLDING shadow`의 `missed_upside_rate`, `capture_efficiency` 판정 기준 고정
   - 선행 상태(`2026-04-18 10:27 KST`): `작업 9`은 공통 helper + Gemini/OpenAI 공용 패킷 + 메인 OpenAI `analyze_target` 감사 필드 주입까지 반영 완료. `2026-04-20` 장후에는 확대 여부와 실표본 검증만 판정하면 된다.
4. `2026-04-21 POSTCLOSE 15:30~16:10 KST`
   - `split-entry leakage canary 승격/보류`
   - `HOLDING shadow 1일차 판정`
   - 다음 영업일 승격축 `1개`를 확정한다.
5. `latency/tag/threshold` broad relax는 위 1~4가 닫히기 전까지 승격하지 않는다.

### 3-2. 다음주 가시적 성과 기준

1. `split-entry + scalp_soft_stop_pct` 빈도가 `2026-04-17` 기준선보다 유의하게 낮아질 것
2. `same_symbol_repeat_flag`가 감소할 것
3. `post_sell_feedback missed_upside_rate`가 현재 `27.9%`보다 내려갈 것
4. `capture_efficiency_avg_pct`가 현재 `39.8%`보다 올라갈 것
5. 위 1~4가 개선되지 않으면 entry 확장은 중단하고 원인 재판정으로 되돌린다.

## 4. 요청사항

### 4-1. 사용자

1. 문서 수정 후 `GitHub Project -> Calendar` 수동 동기화를 진행해 달라.
2. 다음주 live 축 변경 시 `재기동 시각`, `main/remote 적용 시각`, `관측 시작 시각`을 한 줄로 남겨 달라.
3. 같은 날 새로운 live 축을 여러 개 겹치지 말아 달라. 이번 주는 `1일 1축` 원칙이 반드시 필요하다.

### 4-2. Gemini

1. `fallback 진입 모멘텀 필터`를 현행 정합성 게이트를 통과한 표본만으로 다시 추정해 달라.
2. `dynamic threshold 완화`는 `quote_stale` 우세 구간을 제외한 후 재산정해 달라.

### 4-3. Claude

1. `165건 vs 148건` 표본 차이의 제외 규칙을 문서화해 달라.
2. `split-entry`, `full_fill`, `partial_only`별 일자 단위 EV 대시보드를 추가해 달라.

### 4-4. Codex

1. next live change는 `split-entry leakage` 1축 canary부터 처리한다.
2. `HOLDING action schema/prompt split`은 shadow-only로 먼저 넣고, post-sell 기준으로 평가한다.
3. 장후 리포트는 `손익`보다 `거래수`, `퍼널`, `blocker`, `체결품질`, `missed_upside`를 먼저 본다.

## 5. Claude 응답사항

## 6. 참고(추가 감리 문서)

- `작업 9 메인 OpenAI 이식 감리`: `docs/2026-04-18-aiprompt-task9-main-openai-audit-report.md`

### 5-1. `165건 vs 148건` 표본 차이 제외 규칙

#### 집계 기준 비교

| 항목 | Gemini | Claude |
| --- | --- | --- |
| 서버 범위 | local(111건) + remote(54건) = **165건** | local 전용 = **151건** → 유효 **148건** |
| 유효성 조건 | `valid_profit_rate` 보유 여부 (165건 전부 유효 처리) | `status == "COMPLETED"` AND `profit_valid_flag == True` |
| 제외 건수 | 명시 없음 | 3건 제외 (HOLDING 상태: trade_id 2087, 2664, 2699) |
| 분석 기간 | 2026-04-01 ~ 2026-04-17 (동일) | 2026-04-01 ~ 2026-04-17 (동일) |

#### 제외 규칙 상세

**Claude 3건 제외 근거:**

| trade_id | 종목 | 제외 이유 |
| --- | --- | --- |
| 2087 | 삼성증권 (2026-04-14) | status=HOLDING, exit_time 없음, profit_valid_flag=False |
| 2664 | 이수스페셜티케미컬 (2026-04-17) | status=HOLDING, exit_time 없음, profit_valid_flag=False |
| 2699 | RF머트리얼즈 (2026-04-17) | status=HOLDING, exit_time 없음, profit_valid_flag=False (entry_mode=fallback) |

**로컬 내 차이 (Gemini local 111건 vs Claude local 148건 = 37건 차이):**

- Gemini 보고서의 `COMPLETED=64건`은 Claude의 `COMPLETED=148건`과 상이 → Gemini의 COMPLETED 집계 기준이 다름 (추정: `exit_rule` 필드가 존재하는 거래만 집계했을 가능성)
- Claude는 `trade_review_*.json → sections.recent_trades` 전수 파싱, Gemini는 별도 파싱 로직 사용
- 분석 시점 스냅샷 상태 차이 가능 (Gemini 분석이 2026-04-17 장중 스냅샷 기준이었을 경우 당일 후반 거래 미반영)

**결론:** 165건(Gemini)과 148건(Claude)은 집계 기준 자체가 달라 절대치 우열 비교가 불가능하다. 두 분석을 합산하거나 비율로 비교하면 안 되고, 패턴 방향성(손실축 식별, 수익축 확인)만 공통분모로 사용해야 한다.

---

### 5-2. 코호트별 일자 단위 EV 대시보드

> 기준: `trade_fact.csv` (local 전용, COMPLETED + profit_valid_flag=True, 총 148건)  
> `기여손익 합`은 개별 profit_rate(%) 합산이며 원화 환산 전 수치임.

#### full_fill 코호트 일자별 EV

| 날짜 | 거래수 | 승수 | 패수 | 승률 | 기여손익 합(%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-04-06 | 13 | 5 | 8 | 38.5% | -6.55 |
| 2026-04-07 | 5 | 3 | 2 | 60.0% | +0.45 |
| 2026-04-08 | 12 | 3 | 9 | 25.0% | -3.30 |
| 2026-04-09 | 4 | 1 | 3 | 25.0% | -3.59 |
| 2026-04-10 | 6 | 2 | 4 | 33.3% | -2.44 |
| 2026-04-13 | 1 | 1 | 0 | 100.0% | +0.50 |
| 2026-04-14 | 5 | 2 | 3 | 40.0% | -1.51 |
| 2026-04-15 | 19 | 7 | 12 | 36.8% | -5.26 |
| 2026-04-16 | 14 | 2 | 12 | 14.3% | -6.29 |
| 2026-04-17 | 19 | 12 | 7 | 63.2% | +8.19 |
| **합계** | **98** | **38** | **60** | **38.8%** | **-20.03** |

#### split-entry 코호트 일자별 EV

| 날짜 | 거래수 | 승수 | 패수 | 승률 | 기여손익 합(%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-04-13 | 1 | 1 | 0 | 100.0% | +0.96 |
| 2026-04-14 | 2 | 1 | 1 | 50.0% | +1.22 |
| 2026-04-15 | 12 | 5 | 7 | 41.7% | +0.22 |
| 2026-04-16 | 7 | 4 | 3 | 57.1% | -0.54 |
| 2026-04-17 | 24 | 9 | 15 | 37.5% | -15.04 |
| **합계** | **46** | **20** | **26** | **43.5%** | **-13.18** |

#### partial_fill 코호트 일자별 EV

| 날짜 | 거래수 | 승수 | 패수 | 승률 | 기여손익 합(%) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-04-16 | 4 | 0 | 4 | 0.0% | -2.59 |
| **합계** | **4** | **0** | **4** | **0.0%** | **-2.59** |

> ⚠️ partial_fill은 2026-04-16 이전 날짜에 발생 없음. 2026-04-17 partial_fill 1건(RF머트리얼즈, trade_id=2699)은 HOLDING으로 마감돼 제외됨.

#### 코호트별 EV 흐름 요약

| 날짜 | full_fill 승률 | split-entry 승률 | 당일 EV 특이사항 |
| --- | ---: | ---: | --- |
| 2026-04-06 | 38.5% | — | split-entry 표본 없음 (초기 운영) |
| 2026-04-07 | 60.0% | — | full_fill 유일한 흑자일 |
| 2026-04-08 | 25.0% | — | full_fill 손실 집중 |
| 2026-04-09 | 25.0% | — | 표본 소량, 패턴 미확정 |
| 2026-04-10 | 33.3% | — | split-entry 표본 없음 |
| 2026-04-13 | 100.0% | 100.0% | 표본 극소 (각 1건), 신뢰 불가 |
| 2026-04-14 | 40.0% | 50.0% | split-entry 첫 흑자일 (+1.22%) |
| 2026-04-15 | 36.8% | 41.7% | split-entry 소폭 흑자, full_fill 적자 |
| 2026-04-16 | 14.3% | 57.1% | full_fill 최저 승률; partial_fill 전량 손실 |
| 2026-04-17 | **63.2%** | 37.5% | full_fill 최고 승률; split-entry soft-stop 집중으로 기여손익 -15.04% |

**패턴 해석:**
1. `full_fill`은 2026-04-17에 승률 63.2% / +8.19%로 반등했으나 누적은 여전히 -20.03%.
2. `split-entry`는 2026-04-16까지 +0.22~+1.22% 소폭 흑자를 유지하다가 2026-04-17 단일일에 -15.04%로 누적 -13.18% 전환. **2026-04-17 split-entry 24건이 전체 누적 손실의 최대 기여 단일 이벤트.**
3. `split-entry 승률`은 2026-04-16(57.1%)이 최고였으나 2026-04-17에 37.5%로 급락 → `같은 날 동일종목 soft-stop 반복(same_symbol_repeat_flag)` 집중이 원인.

---

## 참고 문서

- [plan-korStockScanPerformanceOptimization.prompt.md](./plan-korStockScanPerformanceOptimization.prompt.md)
- [2026-04-16-holding-profit-conversion-plan.md](./2026-04-16-holding-profit-conversion-plan.md)
- [2026-04-16-profit-conversion-gap-analysis.md](./2026-04-16-profit-conversion-gap-analysis.md)
- [2026-04-17-stage2-todo-checklist.md](./2026-04-17-stage2-todo-checklist.md)
- [analysis/gemini_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md](../analysis/gemini_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md)
- [analysis/claude_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md](../analysis/claude_scalping_pattern_lab/outputs/final_review_report_for_lead_ai.md)
