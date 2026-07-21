# 데이터 품질 보고서

생성일: 2026-07-20 20:56:44
분석 기간: 2026-06-04 ~ 2026-07-20

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 289 |
| COMPLETED | 252 |
| valid_profit_rate | 252 |
| 제외 건수 | 37 |

**서버별:**

- `local`: 289건

**코호트별:**

- `full_fill`: 254건
- `split-entry`: 35건


---

## 2. funnel_fact

- 날짜 수: 32
- 서버: ['local']
- 기간 합계 latency_block_events: 141588
- 기간 합계 submitted_events: 495

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 3321 |
| multi_rebase (split-entry) | 49 |
| partial_then_expand | 44 |
| rebase_integrity 이상 | 16 |
| same_ts_multi_rebase | 18 |
| same_symbol_repeat_soft_stop | 1263 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 16건
- `same_ts_multi_rebase_flag`: 18건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.