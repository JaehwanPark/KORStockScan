# 데이터 품질 보고서

생성일: 2026-08-21 21:17:22
분석 기간: 2026-06-05 ~ 2026-08-21

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 308 |
| COMPLETED | 272 |
| valid_profit_rate | 272 |
| 제외 건수 | 36 |

**서버별:**

- `local`: 308건

**코호트별:**

- `full_fill`: 273건
- `split-entry`: 35건


---

## 2. funnel_fact

- 날짜 수: 39
- 서버: ['local']
- 기간 합계 latency_block_events: 7475
- 기간 합계 submitted_events: 415

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 3570 |
| multi_rebase (split-entry) | 64 |
| partial_then_expand | 59 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 24 |
| same_symbol_repeat_soft_stop | 1297 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 24건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.