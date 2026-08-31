# 데이터 품질 보고서

생성일: 2026-08-31 21:32:21
분석 기간: 2026-06-05 ~ 2026-08-31

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 333 |
| COMPLETED | 293 |
| valid_profit_rate | 293 |
| 제외 건수 | 40 |

**서버별:**

- `local`: 333건

**코호트별:**

- `full_fill`: 298건
- `split-entry`: 35건


---

## 2. funnel_fact

- 날짜 수: 45
- 서버: ['local']
- 기간 합계 latency_block_events: 9983
- 기간 합계 submitted_events: 455

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 3676 |
| multi_rebase (split-entry) | 64 |
| partial_then_expand | 59 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 24 |
| same_symbol_repeat_soft_stop | 1304 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 24건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.