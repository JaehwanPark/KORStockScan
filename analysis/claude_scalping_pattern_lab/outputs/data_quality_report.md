# 데이터 품질 보고서

생성일: 2026-05-26 16:29:29
분석 기간: 2026-04-21 ~ 2026-05-26

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 172 |
| COMPLETED | 159 |
| valid_profit_rate | 159 |
| 제외 건수 | 13 |

**서버별:**

- `local`: 172건

**코호트별:**

- `full_fill`: 167건
- `partial_fill`: 2건
- `split-entry`: 3건


---

## 2. funnel_fact

- 날짜 수: 33
- 서버: ['local']
- 기간 합계 latency_block_events: 55760
- 기간 합계 submitted_events: 306

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 871 |
| multi_rebase (split-entry) | 44 |
| partial_then_expand | 28 |
| rebase_integrity 이상 | 45 |
| same_ts_multi_rebase | 26 |
| same_symbol_repeat_soft_stop | 149 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 45건
- `same_ts_multi_rebase_flag`: 26건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.