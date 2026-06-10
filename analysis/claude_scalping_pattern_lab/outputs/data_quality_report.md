# 데이터 품질 보고서

생성일: 2026-06-10 16:18:52
분석 기간: 2026-06-04 ~ 2026-06-10

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 42 |
| COMPLETED | 41 |
| valid_profit_rate | 41 |
| 제외 건수 | 1 |

**서버별:**

- `local`: 42건

**코호트별:**

- `full_fill`: 42건


---

## 2. funnel_fact

- 날짜 수: 5
- 서버: ['local']
- 기간 합계 latency_block_events: 55581
- 기간 합계 submitted_events: 57

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 883 |
| multi_rebase (split-entry) | 0 |
| partial_then_expand | 0 |
| rebase_integrity 이상 | 0 |
| same_ts_multi_rebase | 0 |
| same_symbol_repeat_soft_stop | 407 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 0건
- `same_ts_multi_rebase_flag`: 0건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.