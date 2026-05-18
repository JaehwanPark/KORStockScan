# 데이터 품질 보고서

생성일: 2026-05-18 07:58:23
분석 기간: 2026-05-15 ~ 2026-05-15

---

## 1. trade_fact

- **데이터 없음**

---

## 2. funnel_fact

- 날짜 수: 1
- 서버: ['local']
- 기간 합계 latency_block_events: 82
- 기간 합계 submitted_events: 0

---

## 3. sequence_fact

| 플래그 | 건수 |
|---|---|
| 총 record 수 | 24 |
| multi_rebase (split-entry) | 1 |
| partial_then_expand | 1 |
| rebase_integrity 이상 | 2 |
| same_ts_multi_rebase | 1 |
| same_symbol_repeat_soft_stop | 0 |

**정합성 플래그 분포:**

- `rebase_integrity_flag`: 2건
- `same_ts_multi_rebase_flag`: 1건

---

## 4. 서버별 파싱 메모

- 원격 서버 스냅샷은 본 분석에서 local(main) 기준으로 집계됨.
- 원격 비교는 server_comparison_*.md 참조.