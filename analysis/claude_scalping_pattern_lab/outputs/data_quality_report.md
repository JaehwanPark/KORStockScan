# 데이터 품질 보고서

생성일: 2026-06-11 16:10:10
분석 기간: 2026-06-04 ~ 2026-06-11

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 43 |
| COMPLETED | 42 |
| valid_profit_rate | 42 |
| 제외 건수 | 1 |

**서버별:**

- `local`: 43건

**코호트별:**

- `full_fill`: 42건
- `split-entry`: 1건


---

## 2. funnel_fact

- 날짜 수: 6
- 서버: ['local']
- 기간 합계 latency_block_events: 60894
- 기간 합계 submitted_events: 68

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 1310 |
| multi_rebase (split-entry) | 2 |
| partial_then_expand | 2 |
| rebase_integrity 이상 | 3 |
| same_ts_multi_rebase | 2 |
| same_symbol_repeat_soft_stop | 729 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 3건
- `same_ts_multi_rebase_flag`: 2건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.