# 데이터 품질 보고서

생성일: 2026-07-01 20:29:21
분석 기간: 2026-06-04 ~ 2026-07-01

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 142 |
| COMPLETED | 124 |
| valid_profit_rate | 124 |
| 제외 건수 | 18 |

**서버별:**

- `local`: 142건

**코호트별:**

- `full_fill`: 134건
- `split-entry`: 8건


---

## 2. funnel_fact

- 날짜 수: 20
- 서버: ['local']
- 기간 합계 latency_block_events: 139596
- 기간 합계 submitted_events: 290

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 2982 |
| multi_rebase (split-entry) | 20 |
| partial_then_expand | 15 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 10 |
| same_symbol_repeat_soft_stop | 1189 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 10건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.