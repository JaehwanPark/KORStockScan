# 데이터 품질 보고서

생성일: 2026-06-12 16:10:07
분석 기간: 2026-06-04 ~ 2026-06-12

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 45 |
| COMPLETED | 44 |
| valid_profit_rate | 44 |
| 제외 건수 | 1 |

**서버별:**

- `local`: 45건

**코호트별:**

- `full_fill`: 44건
- `split-entry`: 1건


---

## 2. funnel_fact

- 날짜 수: 7
- 서버: ['local']
- 기간 합계 latency_block_events: 68486
- 기간 합계 submitted_events: 92

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 1631 |
| multi_rebase (split-entry) | 6 |
| partial_then_expand | 4 |
| rebase_integrity 이상 | 7 |
| same_ts_multi_rebase | 4 |
| same_symbol_repeat_soft_stop | 864 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 7건
- `same_ts_multi_rebase_flag`: 4건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.