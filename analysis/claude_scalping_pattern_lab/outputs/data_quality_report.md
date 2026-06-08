# 데이터 품질 보고서

생성일: 2026-06-08 17:09:21
분석 기간: 2026-06-04 ~ 2026-06-08

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 34 |
| COMPLETED | 34 |
| valid_profit_rate | 34 |
| 제외 건수 | 0 |

**서버별:**

- `local`: 34건

**코호트별:**

- `full_fill`: 34건


---

## 2. funnel_fact

- 날짜 수: 3
- 서버: ['local']
- 기간 합계 latency_block_events: 44199
- 기간 합계 submitted_events: 34

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 212 |
| multi_rebase (split-entry) | 0 |
| partial_then_expand | 0 |
| rebase_integrity 이상 | 0 |
| same_ts_multi_rebase | 0 |
| same_symbol_repeat_soft_stop | 85 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 0건
- `same_ts_multi_rebase_flag`: 0건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.