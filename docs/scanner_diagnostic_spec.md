# Scanner Diagnostic Report Spec (Draft)

## 1) Current Implementation Summary
- **Goal**: Provide a single-page diagnostic report that combines market health and AI sentiment, then evaluates each stock on a pass/fail basis.
- **Data sources**:
  - DB `daily_stock_quotes` (latest date, top 200 by market cap → first 150 used)
  - Kiwoom API: KOSPI 5‑day return (optional, if token available)
  - Models: Normal XGB/LGBM, Bull XGB/LGBM, and a stacking meta model
- **Decision logic**:
  - Exclude if < 30 days of data
  - Exclude low‑quality stocks via `is_valid_stock`
  - Check 20‑day MA breakout
  - Compute features → model probabilities → meta probability
  - Fail if below `PROB_RUNNER_PICK`
  - Fail if neither foreign nor institutional flow is positive
  - Otherwise pass
- **Output**:
  - Static HTML file: `scanner_report.html`
  - Dashboard + stock table
  - Pass/fail badges, bull model emphasis

## 2) Operating Criteria To Confirm
- **Market regime thresholds**:
  - MA20 breakout ratio thresholds (50% / 30%) align with current operations?
- **Pass criteria**:
  - `PROB_RUNNER_PICK` value confirmed?
  - Definition of “flow positive” for foreign/institution (roll and accel)
- **Universe size**:
  - Keep top 150 or expand to 200/300?

## 3) Candidate Enhancements
- **Indicators**:
  - Volume spike ratio
  - Volatility (ATR)
  - Flow strength normalized by volatility
- **Sector/industry summaries**:
  - Sector-level average probability
  - Sector-level MA20 breakout ratio
  - Sector-level flow trend
- **Diagnostics / metadata**:
  - Model version tags
  - Generation timestamp and data freshness
  - Failure counts (data 부족 / 계산 에러)
- **Table UX**:
  - Search, filter, sort
  - Mobile readability improvements

## 4) UI/UX Direction
- **Dashboard first**: market regime + key ratios
- **Table second**: per‑stock diagnostic with clear badges
- **Color language**:
  - Green = stable/bull
  - Orange = caution
  - Red = risk
- **Badges**:
  - Pass / Fail / Data 부족

## 5) Proposed Next Steps (Decision Points)
1. Confirm operating thresholds and universe size
2. Decide which additional metrics are mandatory
3. Decide table UX requirements (search/sort/filter)
4. Decide whether report remains static or becomes live/refreshing

---

## Appendix: Current Fields Rendered (Reference)
- 종목코드
- 종목명
- 현재가
- 20일선돌파
- 최종AI확신도
- 개별AI모델분석(일반/상승장)
- 수급(외인/기관)
- 최종결과
