# 데이터 품질 보고서

생성일: 2026-06-04 18:03:52
분석 기간: 2026-04-21 ~ 2026-06-04

---

## 1. trade_fact

| 항목 | 값 |
|---|---|
| 총 거래수 | 8 |
| COMPLETED | 8 |
| valid_profit_rate | 8 |
| 제외 건수 | 0 |

**서버별:**

- `local`: 8건

**코호트별:**

- `full_fill`: 8건

> ⚠️ **표본 부족**: `local` 서버 valid_profit_rate=8건 < 30. 이 서버 기준 결론 확정 금지.

---

## 2. funnel_fact

- 날짜 수: 1
- 서버: ['local']
- 기간 합계 latency_block_events: 4418
- 기간 합계 submitted_events: 1

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 54 |
| multi_rebase (split-entry) | 1 |
| partial_then_expand | 1 |
| rebase_integrity 이상 | 2 |
| same_ts_multi_rebase | 1 |
| same_symbol_repeat_soft_stop | 13 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 2건
- `same_ts_multi_rebase_flag`: 1건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.