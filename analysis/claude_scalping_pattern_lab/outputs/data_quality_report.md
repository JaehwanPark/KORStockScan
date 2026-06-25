# 데이터 품질 보고서

생성일: 2026-06-25 21:43:46
분석 기간: 2026-06-04 ~ 2026-06-25

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 59 |
| COMPLETED | 57 |
| valid_profit_rate | 57 |
| 제외 건수 | 2 |

**서버별:**

- `local`: 59건

**코호트별:**

- `full_fill`: 53건
- `split-entry`: 6건


---

## 2. funnel_fact

- 날짜 수: 16
- 서버: ['local']
- 기간 합계 latency_block_events: 138052
- 기간 합계 submitted_events: 137

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 2714 |
| multi_rebase (split-entry) | 18 |
| partial_then_expand | 13 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 9 |
| same_symbol_repeat_soft_stop | 1102 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 9건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.