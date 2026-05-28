# 2026-04-15 메인서버 스캘핑 매매실적 Pros & Cons 감사 리포트 (재집계본)

> 작성시각: 2026-04-15 22:07 KST  
> 대상: `main(local)` 스캘핑 실적  
> 기준 데이터: 로그패치 반영 후 재집계 (`build_trade_review_report`, `build_entry_pipeline_flow_report`)

## 1) 범위 및 데이터 소스

| 구분 | 소스 | 기준 시각/범위 | 비고 |
|---|---|---|---|
| 당일 종합 스냅샷 | `docs/2026-04-15-tuning-result-report-for-auditor.md` | 당일 장후 집계 + 22:07 재집계 | `build_trade_review_report`, `build_entry_pipeline_flow_report` 결과 인용 |
| 품질게이트/운영판정 | `docs/checklists/2026-04-15-stage2-todo-checklist.md` | 15:55~15:57 KST 검증 | integrity/restoration/aggregation 판정 근거 |
| 장중 비교 관측치 | `data/report/server_comparison/server_comparison_2026-04-15.md` | since `09:00:00` | 안전지표 중심(손익 파생 제외) |

---

## 2) 메인서버 당일 실적 스냅샷 (수집치 기준)

| 항목 | 값 | 해석 |
|---|---:|---|
| 총 거래수 | 31 | 체결 표본은 충분한 편 |
| 종료 거래수 / 미종료 거래수 | 31 / 0 | 당일 포지션 잔여 리스크는 없음 |
| 승/패 | 12 / 19 | 승률 열위 (`38.7%`) |
| 평균 손익률 | -0.16% | 건별 기대값은 음수 |
| 실현손익 | +77,774원 | 합산 손익은 플러스 마감 |
| holding 이벤트 수 | 5,403 | 보유/청산 이벤트 복기 가능 상태로 복원 |
| full fill / partial fill | 27 / 53 | 체결품질을 분리 해석할 수 있는 표본 확보 |
| preset sync OK / mismatch | 40 / 13 | partial fill 연계 동기화 결함 축이 확인됨 |
| hard time stop shadow 이벤트 | 45 | 출구 보정 shadow 분포 관찰 가능 |
| tracked_stocks / submitted_stocks | 168 / 2 | 탐지 대비 주문 제출 전환이 매우 낮음 |
| budget_pass -> submitted 전환율 | 0.0% | 퍼널 절단 병목이 핵심 |
| expired_armed_total | 374 | 미진입/만료 누적이 큼 |

---

## 3) Pros (강점)

| 강점 | 근거 데이터 | 감사 관점 판정 |
|---|---|---|
| 당일 손익 플러스 마감 | 실현손익 `+77,774원` | 손실 확대 없이 세션 종료 |
| EOD 잔여 포지션 없음 | `open_trades=0` | 야간 리스크 이월 최소화 |
| HOLDING 복기 이벤트 복원 | `holding_events=5,403` | 감사 추적성(체결-청산 근거선) 회복 |
| 체결품질 분리 가능 | `full=27`, `partial=53` | full/partial 혼합 왜곡 없이 해석 가능 |
| 무결성/복원 게이트 통과 | `COMPLETED_INVALID=0`, 계좌/DB/메모리 일치 확인 | 실거래 정합성 신뢰 가능 구간 확보 |
| 운영 통제 준수 | `No-Decision Day` 유지, 파라미터/승격 동결 | 장애일 과적용 리스크 억제 |
| 상대 비교 우위(당일) | 같은 날 원격은 실현손익 `-14,618원` | 메인은 보수적 운영으로 손익 방어 |

---

## 4) Cons (약점)

| 약점 | 근거 데이터 | 영향 |
|---|---|---|
| 건별 기대값 음수 | 평균 손익률 `-0.16%`, 승/패 `12/19` | 손익 분포가 취약, 우연한 플러스 가능성 |
| 진입 퍼널 절단 | `budget_pass -> submitted = 0.0%` | 기회비용 확대, 체결수익 실현 기회 상실 |
| expired_armed 누적 과다 | `expired_armed_total=374` | 의사결정-주문 실행 사이 간극 큼 |
| partial fill 연계 sync 결함 잔존 | `preset_exit_sync_mismatch=13` | 주문/상태 정합성 재검증 필요 |
| 집계 품질 게이트 이슈 잔존 | `report_2026-04-15.json` `trades` 섹션 부재(기존) | 자동 감사 파이프라인 재현성 저하 |
| 장애/재기동 영향 | 당일 서비스 오류/다중 재기동 기록 | 당일 관찰데이터 해석 신뢰도 하락 |

---

## 5) 미진입 기회비용 관점 (관찰축 기준)

| 분류축 | 현재 수집 근거 | 판정 |
|---|---|---|
| latency guard miss | 장중 비교 리포트에서 gatekeeper/latency 지표 관측됨 | 정량 분해는 추가 필요 |
| liquidity gate miss | 제출 직전 단계 절단(`budget_pass_no_submit`)이 주요 병목으로 관찰 | 영향 큼 |
| AI threshold miss | `blocked_gatekeeper_reject` 상위 단계(09:00~ 비교 리포트) | 영향 중간 이상 |
| overbought gate miss | `blocked_overbought` 상위 단계(09:00~ 비교 리포트) | 영향 중간 |

메모:
- 당일 메인 서버의 정밀 분해는 `aggregation quality fail` 영향으로 완전 자동산출이 불안정하다.  
- 따라서 본 항목은 “현재 수집 가능한 로그 기반 1차 판정”으로 한정한다.

---

## 6) 감사용 종합 판정

| 항목 | 판정 |
|---|---|
| 손익 결과 | **조건부 양호** (합산 플러스, 건별 기대값은 약함) |
| 데이터 신뢰성 | **부분 양호** (integrity/restoration PASS, aggregation FAIL) |
| 운영 의사결정 적정성 | **양호** (`No-Decision Day` 유지가 타당) |
| 즉시 승격/완화 가능성 | **부적정** (집계 품질 및 퍼널 병목 미해소) |

---

## 7) 다음 액션 (감사인 확인 포인트)

1. `aggregation quality gate` 복구 전까지 손익 결론을 자동 리포트 단독 근거로 사용하지 않는다.  
2. `budget_pass -> submitted` 절단 지점 계측을 우선 복구한다.  
3. `expired_armed` 상위 코호트 감소 여부를 익일 동일 시각대 기준으로 재감사한다.  
4. 미진입 기회비용은 `latency / liquidity / AI threshold / overbought` 4축 분리표로 익일 재보고한다.
