# 데이터 품질 보고서

생성일: 2026-05-29 14:22:28
분석 기간: 2026-04-21 ~ 2026-05-28

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 183 |
| COMPLETED | 169 |
| valid_profit_rate | 169 |
| 제외 건수 | 14 |

**서버별:**

- `local`: 183건

**코호트별:**

- `full_fill`: 178건
- `partial_fill`: 2건
- `split-entry`: 3건


---

## 2. funnel_fact

- 날짜 수: 35
- 서버: ['local']
- 기간 합계 latency_block_events: 113362
- 기간 합계 submitted_events: 321

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 1434 |
| multi_rebase (split-entry) | 47 |
| partial_then_expand | 30 |
| rebase_integrity 이상 | 49 |
| same_ts_multi_rebase | 28 |
| same_symbol_repeat_soft_stop | 270 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 49건
- `same_ts_multi_rebase_flag`: 28건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.