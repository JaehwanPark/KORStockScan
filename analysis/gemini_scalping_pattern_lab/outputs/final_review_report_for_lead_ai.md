# 📈 Gemini Scalping Pattern Lab - 최종 검토 보고서 (Final Review Report)

**수신:** KORStockScan 프로젝트 총괄 AI (Lead AI / System Architect)
**발신:** Gemini Data & Quant Analysis Agent
**작성일:** 2026-04-17
**목적:** 스캘핑 손실/수익 패턴 분석 완료 보고 및 향후 시스템 개선(EV Improvement) 액션 아이템 이관

---

## 1. 분석 개요 및 데이터 품질 확인
- **분석 기간:** 2026-04-01 ~ 2026-04-17 (약 3주간)
- **대상 서버:** Local (main) 및 Remote 병합
- **데이터 스펙:** 총 165건의 유효 `COMPLETED` 스캘핑 거래 추출 완료. (로컬 111건, 원격 54건으로 통계적 유의성 달성)
- **제약 준수:** 기존 `src/` 이하 운영 코드는 단 한 줄도 수정하지 않았으며, 전용 오프라인 환경인 `analysis/gemini_scalping_pattern_lab/` 내에서 파이프라인을 완전히 독립적으로 구동했습니다.

## 2. 핵심 인사이트 (Pattern Analysis Summary)

### 🚨 치명적 손실 패턴 (Fix Priority: P0)
현재 시스템의 가장 큰 손실 축(-41.18% 기여손익)은 **"지연 진입(Fallback) 후 돌파 실패"**와 **"유동성 부족으로 인한 부분 체결(Partial Fill) 후 하락 반전"** 상황에서 발생하고 있습니다. 진입 후 즉각적인 상승(Momemtum)이 붙지 않음에도 기계적인 `soft_stop`(-1.6%대)까지 손실을 방치하는 것이 문제입니다.

### 💸 핵심 수익 패턴 (Enhance Priority: P1)
놀랍게도 지연 진입(Fallback)이나 부분 체결(Partial Fill) 자체가 나쁜 것은 아닙니다. 이 상황에서도 매수세가 살아있다면 `trailing_take_profit`을 통해 최고 기여 수익(+23.09%, +21.44%)을 내고 있습니다. 즉, 진입 직후의 "모멘텀 지속 여부"가 승패를 가르는 핵심 트리거입니다.

### 🔍 거대한 기회비용 (Opportunity Cost)
강력한 필터링으로 인해 일평균 20만 건 이상의 진입 기회가 차단(Blocked)되고 있으며 실제 진입은 극소수(일 수십 건)에 불과합니다. 안전하긴 하나, 강력한 모멘텀 장세에서는 득보다 실(기회 상실)이 클 수 있습니다.

---

## 3. 총괄 AI를 위한 코드 수정 제안 (EV Improvement Backlog)

아래 5가지 개선안을 제안합니다. 리스크를 최소화하기 위해 **1~3번 항목을 다음 스프린트에서 `Shadow-Only` 모드로 우선 개발 및 검증할 것**을 권고합니다.

### [제안 1] Shadow-Only: Fallback 진입 모멘텀 필터 도입 (손실 패턴 1번 방어)
- **개발 목표:** Fallback 진입 로직 수행 전(또는 직후) 체결강도/모멘텀 지표를 재확인하여, 이미 꺾인 상태라면 진입을 취소하거나 즉시 본절 탈출.
- **제약 반영 (Midterm Tuning):** 현행 정합성 게이트(Rebase Integrity)를 정상적으로 통과한 표본만으로 모멘텀 필터 임계값을 다시 추정하여 적용. (오류로 인한 손실 케이스 혼입 방지)
- **기대 효과:** -41.18%에 달하는 누적 손실의 상당 부분 방어.

### [제안 2] Shadow-Only: Partial Fill 직후 시간제한 탈출 로직 (손실 패턴 2번 방어)
- **개발 목표:** 체결 품질이 `PARTIAL_FILL`인 경우, 진입 후 n초(예: 3초) 이내에 추가 체결이나 가격 상승이 없다면 Trailing Stop을 본절 위주로 타이트하게 바짝 올려버리는 로직 추가.
- **기대 효과:** 가짜 돌파(Fake Breakout)에 당하는 -1.6% 대 손실을 -0.3% 이하의 약손절/본절 수준으로 절감.

### [제안 3] Shadow-Only: 강한 돌파 시 Partial Fill 후 Split-Entry(불타기) 추가 (수익 극대화)
- **개발 목표:** `PARTIAL_FILL` 직후 호가창 모멘텀이 폭발적으로 상승하는 것이 확인되면, 나머지 미체결 물량을 쫓아가서 시장가/유리한 지정가로 추가 진입(`Split-Entry`).
- **기대 효과:** 현재 놓치고 있는 추세 지속 수익을 최대 30% 이상 증대.

### [제안 4] Canary: AI Momentum Decay 민감도 상향
- **개발 목표:** Exit 전략 중 AI가 추세 반전을 미리 감지하는 로직의 민감도를 상향 조정하여 기계적 Soft Stop이 터지기 전에 선제 청산.

### [제안 5] Shadow-Only: AI Threshold Dynamic 완화 (기회비용 회수)
- **개발 목표:** 특정 조건(10틱 체결강도 극단적 상위 등) 만족 시 기존 AI Score Cut-off와 Overbought Gate를 한시적으로 낮춰주는 Dynamic Threshold 구현.
- **제약 반영 (Midterm Tuning):** Quote Stale(호가 지연)이 우세한 위험 구간을 필터링하여 제외한 후, 정상적인 유동성 구간에서만 Dynamic Threshold 완화 기준을 재산정.

---

## 4. 인수인계 (Hand-over)
본 문서를 끝으로 데이터 추출 및 패턴 진단 Task를 완료합니다. 총괄 AI께서는 본 보고서와 `outputs/` 내의 산출물들을 참고하여, 운영 코드(`src/`) 내 로직 개편 및 Shadow 모드 시뮬레이션 계획을 수립하시기 바랍니다.