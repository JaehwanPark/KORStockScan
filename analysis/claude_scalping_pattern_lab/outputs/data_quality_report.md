# 데이터 품질 보고서

생성일: 2026-06-24 20:27:17
분석 기간: 2026-06-04 ~ 2026-06-24

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 57 |
| COMPLETED | 55 |
| valid_profit_rate | 55 |
| 제외 건수 | 2 |

**서버별:**

- `local`: 57건

**코호트별:**

- `full_fill`: 52건
- `split-entry`: 5건


---

## 2. funnel_fact

- 날짜 수: 15
- 서버: ['local']
- 기간 합계 latency_block_events: 138035
- 기간 합계 submitted_events: 133

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 2643 |
| multi_rebase (split-entry) | 17 |
| partial_then_expand | 12 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 9 |
| same_symbol_repeat_soft_stop | 1068 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 9건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.