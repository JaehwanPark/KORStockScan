# 데이터 품질 보고서

생성일: 2026-04-17 14:06:24
분석 기간: 2026-04-01 ~ 2026-04-17

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 151 |
| COMPLETED | 148 |
| valid_profit_rate | 148 |
| 제외 건수 | 3 |

**서버별:**

- `local`: 151건

**코호트별:**

- `full_fill`: 100건
- `partial_fill`: 5건
- `split-entry`: 46건


---

## 2. funnel_fact

- 날짜 수: 12
- 서버: ['local']
- 기간 합계 latency_block_events: 12298
- 기간 합계 submitted_events: 111

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 156 |
| multi_rebase (split-entry) | 57 |
| partial_then_expand | 57 |
| rebase_integrity 이상 | 19 |
| same_ts_multi_rebase | 21 |
| same_symbol_repeat_soft_stop | 59 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 19건
- `same_ts_multi_rebase_flag`: 21건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.