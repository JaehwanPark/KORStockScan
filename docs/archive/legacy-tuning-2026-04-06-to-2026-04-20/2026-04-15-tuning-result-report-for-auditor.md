# 2026-04-15 튜닝 작업 결과보고서 (감사용)

> 작성시각: 2026-04-15 22:10 KST (메인 로그 재집계 반영)
> 기준 Source/Section: `docs/checklists/2026-04-15-stage2-todo-checklist.md` (`장중 체크리스트`, `장후 체크리스트`, `익일 이월 작업`)
> 운영모드: `No-Decision Day` 유지 (당일 실전 파라미터/승격 변경 보류)

---

## 1) 서버별 당일 결과 스냅샷

| 구분 | 메인(local) | 원격(remote) | 해석 |
|---|---:|---:|---|
| 총 거래수 (`total_trades`) | 31 | 44 | 원격이 더 공격적으로 체결됨 |
| 종료 거래수 (`completed_trades`) | 31 | 42 | 원격이 표본 우위 |
| 미종료 거래수 (`open_trades`) | 0 | 2 | 원격 잔여 포지션 존재 |
| 승/패 (`win/loss`) | 12 / 19 | 16 / 26 | 양 서버 모두 패수 우위 |
| 평균 손익률 (`avg_profit_rate`) | -0.16% | -0.34% | 원격이 손익률 열위 |
| 실현손익 (`realized_pnl_krw`) | 77,774원 | -14,618원 | 메인 플러스, 원격 마이너스 |
| 추적 종목수 (`tracked_stocks`) | 168 | 178 | 원격 관측 종목 많음 |
| 제출 종목수 (`submitted_stocks`) | 2 | 7 | 원격 제출 시도 많음 |
| `budget_pass -> submitted` 전환율 | 0.0% | 0.0% | 공통 병목 존재 |
| `expired_armed_total` | 374 | 394 | 원격 만료 이벤트 더 많음 |

검증: `build_trade_review_report('2026-04-15')`, `build_entry_pipeline_flow_report('2026-04-15')`
재집계 메인 핵심값: `holding_events=5,403`, `full_fill=27`, `partial_fill=53`, `preset_exit_sync_ok/mismatch=40/13`

---

## 2) 단위작업별 결과 (POSTCLOSE 대상)

| 단위작업 | 작업 결과 | 메인 영향도 | 원격 영향도 | 검증 근거 |
|---|---|---|---|---|
| RELAX-DYNSTR 퍼널 기록 (`AI BUY->entry_armed->budget_pass->submitted`) | 완료. `submitted` 전환 미확인 | 중간(음): `budget_pass` 대비 전환 0 | 중간(음): 동일 | pipeline 이벤트 집계: `entry_armed/resume` 증가, `submitted=0` |
| RELAX-DYNSTR 1일차 canary 1차 정리 | 완료. 유지+계측보강 판정 | 중간(관찰): 신규 완화 없음 | 중간(관찰): 신규 완화 없음 | checklist 반영 + 퍼널 지표 |
| partial fill min_fill_ratio 효과 기록 | 재집계 반영. 메인 표본 확인, 원격은 보수 해석 유지 | 중간(관찰): `partial/full=53/27`, `sync mismatch=13` | 낮음(유보) | trade review(main): `partial_fill_events=53`, `full_fill_events=27` |
| partial fill canary 1차 정리 | 완료. canary on 유지, 효과판정은 원격 표본 추가 필요 | 중간 | 낮음 | main은 체결품질 코호트 확보, 원격은 기존 운영 로그 기준 추가 관찰 |
| RELAX-LATENCY 유지 점검 | 완료. 전일 결론 유지 | 낮음(변경 없음) | 낮음(변경 없음) | 체크리스트/로그 상 신규 완화 미적용 |
| 기존 관찰축 최소 유지 | 완료 | 낮음(집중도 개선) | 낮음(집중도 개선) | 4축( dynstr/partial/shadow/expired )로 수렴 |
| 관찰축 5 승격 준비 (`add_judgment_locked`) | 완료(축 정의/집계기준 확정) | 중간(보유 정체 코호트 원인 귀속 강화) | 중간(동일) | `ADD_BLOCKED reason=add_judgment_locked` 종목/시간대/정체코호트 집계 기준 확정 |
| expired_armed 전수 분포 재확인 | 완료 | 중간(병목 가시화) | 중간(병목 가시화) | main 374, remote 394 / after_wait 편중 |
| expired_armed 설계 문서 작성 | 완료 | 중간(익일 의사결정 품질 향상) | 중간(동일) | [2026-04-15-expired-armed-design.md](./2026-04-15-expired-armed-design.md) |
| AIPrompt 작업5 분리 검증축 확인 | 완료(진행 중) | 낮음(표본 1건) | 중간(표본 22건) | shadow 로그(`watching_shared_prompt_shadow`) |
| AIPrompt 작업8 감사 3값 구현/검증 | 부분완료 | 낮음 | 낮음 | 코드 주입 확인, `*_sent` 로그 키 미노출 |
| AIPrompt 작업8 결과 정리 | 완료(부분완료로 기록) | 낮음 | 낮음 | checklist 기록 + 보완 일정 |
| AIPrompt 작업9 helper scope 초안 | 완료 | 낮음(설계단) | 낮음(설계단) | 대상 피처 6개 scope 고정 |
| AIPrompt 작업10 FORCE_EXIT MVP 진행 | 완료(착수 유지) | 낮음(실집행 미개시) | 낮음(실집행 미개시) | 설계/코드 경로 확인, 운영 표본 부족 |
| AIPrompt 작업10 2026-04-16 입력 정리 | 완료 | 중간(익일 canary go/no-go 입력) | 중간 | precision/FP/충돌률 입력 고정 |
| AI overlap audit -> selective override 입력 고정 | 완료 | 중간(다음날 설계 착수 가능) | 중간 | `expired_armed`, `budget_pass_no_submit`, `shadow diverged` 3축 |
| AIPrompt 즉시 코드축 결과 정리 | 완료 | 중간(의사결정 근거 정리) | 중간 | 작업 5/8/10 평가포인트 고정 |
| SCALPING shadow 실표본 수집 시작 | 완료 | 낮음(1건) | 중간(22건) | shadow count/diverged 수치 |
| SCALPING shadow 첫 장후 비교표 생성 | 완료(1차) | 낮음 | 중간 | main `1/1 diverged`, remote `22/6 diverged` |
| 오늘 보류항목 사유+재시각 명시 | 완료 | 중간(통제 강화) | 중간 | checklist 이월 블록 반영 |

영향도 기준: `높음`(당일 실현손익/체결수 즉시 변화), `중간`(퍼널·품질게이트·익일결정 영향), `낮음`(설계/문서/표본부족)

---

## 3) 서비스 안정화 작업 영향

| 작업 | 결과 | 메인 영향 | 원격 영향 | 검증 |
|---|---|---|---|---|
| `DetachedInstanceError(bhk3)` 대응 (`expire_on_commit=False`) | 적용 완료 | 치명오류 재발 미관측 | 15:30 치명오류 이후 재기동+패치, 재발 미관측 | 최근 로그 구간에서 `bhk3` 신규 0건 |
| 계좌/DB/메모리 동기화 재점검 | 완료 | 일치 | 일치 | `데이터 동기화 완료. 메모리 일치` 로그 확인 |

---

## 4) 감사 포인트 (No-Decision Day 판정 근거)

| 항목 | 판정 | 근거 |
|---|---|---|
| integrity gate | PASS | `COMPLETED_INVALID=0` (main/remote) |
| event restoration gate | PASS | 양 서버 동기화 완료 + 계좌/DB 정합성 일치 |
| aggregation quality gate | FAIL | `report_2026-04-15.json`에 `trades` 섹션 부재(메인/원격 공통) |
| 최종 운영판정 | No-Decision Day 유지 | gate 3개 중 1개 미통과 |

---

## 5) 2026-04-16 진행방향 예측 (간략)

1. **단기(장전)**
   `budget_pass -> submitted` 절단 지점 계측을 보강하면, `expired_armed_after_wait` 비율이 먼저 하락할 가능성이 높다.
   단, aggregation gate 미보정 상태에서는 실전 승격/파라미터 변경은 계속 보류가 타당하다.

2. **중기(장중~장후)**
   원격은 shadow 표본이 충분히 쌓이기 시작했으므로(`22건`), `action_diverged` 패턴 기반 selective override 후보를 좁힐 수 있다.
   메인은 partial/full 표본이 복구되어(`53/27`) 결함축(`sync mismatch=13`)까지 추적 가능해졌다.
   원격 partial fill 효익 추정은 기존처럼 보수적으로 유지한다.

3. **리스크**
   현재 핵심 리스크는 손익 자체보다 `집계 품질(대시보드 노출 불완전)`과 `entry 전환율 0% 병목`이다.
   두 항목이 먼저 해소되지 않으면 튜닝 효과의 원인귀속이 왜곡될 확률이 높다.

---

## 6) 실행/검증 명령 기록

```bash
PYTHONPATH=. pytest -q src/tests/test_entry_pipeline_report.py src/tests/test_live_trade_profit_rate.py
# 결과: 14 passed
```

```python
build_trade_review_report('2026-04-15')
build_entry_pipeline_flow_report('2026-04-15')
```

```bash
grep -n "not bound to a Session|bhk3|데이터 동기화|완벽히 일치" logs/bot_history.log
```
