# 데이터 품질 보고서

생성일: 2026-05-22 17:06:05
분석 기간: 2026-04-21 ~ 2026-05-22

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 165 |
| COMPLETED | 152 |
| valid_profit_rate | 152 |
| 제외 건수 | 13 |

**서버별:**

- `local`: 165건

**코호트별:**

- `full_fill`: 160건
- `partial_fill`: 2건
- `split-entry`: 3건


---

## 2. funnel_fact

- 날짜 수: 29
- 서버: ['local']
- 기간 합계 latency_block_events: 53369
- 기간 합계 submitted_events: 283

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 752 |
| multi_rebase (split-entry) | 38 |
| partial_then_expand | 25 |
| rebase_integrity 이상 | 39 |
| same_ts_multi_rebase | 23 |
| same_symbol_repeat_soft_stop | 149 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 39건
- `same_ts_multi_rebase_flag`: 23건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.