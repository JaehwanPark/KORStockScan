# KORStockScan Plan Rebase 중심 문서

기준일: `2026-04-22 KST`  
역할: 현재 튜닝 원칙, 판정축, 실행과제, 일정, 효과를 한곳에 고정하는 중심축 문서다.  
주의: 이 문서는 자동 파싱용 체크리스트를 소유하지 않는다. Project/Calendar 동기화 대상 작업항목은 날짜별 `stage2 todo checklist`가 소유한다.

---

## 1. 현재 판정

1. 현재 단계는 손실 억제형 미세조정이 아니라 `기대값/순이익 극대화`를 위한 `Plan Rebase`다.
2. 현재 기준선은 `main-only`, `normal_only`, `post_fallback_deprecation`이다.
3. 현재 폐기 확정 축은 `fallback_scout/main`, `fallback_single`, `latency fallback split-entry`다.
4. 현재 live 운용 상태는 `하루 1축 canary`이며, 실전 유지축은 `main-only buy_recovery_canary`다.
5. 현재 다음 정식 후보는 `entry_filter_quality`다.
6. 현재 대기 중 다음 판정은 `2026-04-23 INTRADAY BUY sufficiency checkpoint`와 `2026-04-23 POSTCLOSE entry_filter_quality 착수 가능성 재판정`이다.

## 2. 용어 범례

| 표현 | 한글 설명 | 현재 판정 |
| --- | --- | --- |
| `fallback` | 정상 진입이 막힌 상황에서 보조 주문 경로로 진입을 시도하던 예외 경로 | 신규 사용 금지, 폐기 유지 |
| `fallback_scout/main` | `fallback_scout` 탐색 주문과 `fallback_main` 본 주문이 같은 축에서 함께 나가던 2-leg fallback 분할진입 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `fallback_single` | scout/main으로 나뉘지 않은 단일 fallback 진입 경로 | 영구 폐기. 재개/승격/canary 대상 아님 |
| `latency fallback split-entry` | latency 상태가 `CAUTION/DANGER`일 때 fallback 허용으로 분할진입을 시도하던 경로 | 영구 폐기. latency bugfix 대상과 분리 |
| `main-only` | `songstock`/remote 비교를 제외하고 메인서버 실전 로그만 기준으로 보는 방식 | Plan Rebase 기간의 기준선 |
| `normal_only` | fallback 태그와 예외 진입이 섞이지 않은 정상 진입 표본 | 손익/성과 비교의 우선 기준 |
| `post_fallback_deprecation` | `2026-04-21 09:45 KST` fallback 폐기 이후 새로 쌓인 표본 | 폐기 이후 효과 확인 기준 |
| `canary` | 작은 범위로 실전에 적용해 성과와 리스크를 검증하는 1축 변경 | 하루 1축만 허용 |
| `shadow` | 실전 주문에는 반영하지 않고 병렬 계산만 하던 검증 방식 | 신규/보완축에서는 금지 |
| `buy_recovery_canary` | Gemini `WAIT 65~79` 과밀 구간을 2차 재평가해 BUY 회복 여부를 보는 실전 1축 | 현재 유지축 |
| `entry_filter_quality` | 불량 진입을 줄이고 제출/체결 품질을 높이는 다음 정식 튜닝 후보 | `buy_recovery_canary` 1차 판정 후 재판정 |

## 3. 튜닝 원칙

1. 최종 목표는 손실 억제가 아니라 기대값/순이익 극대화다.
2. 손익 판단은 `COMPLETED + valid profit_rate`만 사용한다.
3. `NULL`, 미완료, fallback 정규화 값은 손익 기준으로 사용하지 않는다.
4. 비교 우선순위는 `거래수 -> 퍼널 -> blocker -> 체결품질 -> missed_upside -> 손익`이다.
5. BUY 후 미진입은 `latency guard miss`, `liquidity gate miss`, `AI threshold miss`, `overbought gate miss`로 분리한다.
6. `full fill`과 `partial fill`은 합산하지 않는다.
7. 원인 귀속이 불명확하면 먼저 리포트 정합성, 이벤트 복원, 집계 품질을 점검한다.
8. `counterfactual` 수치는 직접 실현손익과 합산하지 않고 우선순위 판단 자료로만 쓴다.
9. 향후 A/B 테스트의 목적은 단일 모델 우열 확인이 아니라 진입/보유/청산 각 단계에서 `EV`를 높여 기준 조합 대비 `최소 +10%` 개선되는 엔진 조합을 찾는 것이다.

## 4. 작업 규칙

| 규칙 | 기준 | 위반 시 처리 |
| --- | --- | --- |
| 단일 live canary | 하루에 동시 live 변경축은 1개만 허용한다. 단, 같은 거래일 안에서 live 축 교체가 필요하면 `기존 축 OFF -> restart.flag -> 새 축 ON`의 replacement 전환만 허용한다. | 동시 2축 live 금지. 교체 전환 시 기존 축 OFF -> `restart.flag` -> 새 축 ON 순서를 강제한다. |
| shadow 금지 | 신규/보완축은 shadow 없이 canary-only | shadow 항목은 폐기 또는 코드정리로 격하 |
| 문서 참조 방향 | `docs/personal-decision-flow-notes.md`는 개인판단 정합성 기록용 노트다. 다른 문서에서 `Source` 또는 판정 근거 링크로 사용하지 않는다. 개인문서는 checklist/report/plan 문서나 코드 레퍼런스를 참조해도 된다. | 개인문서가 판정 근거 링크로 쓰이면 링크를 checklist에서 제거하고 기준문서/감사문서 근거로 대체한다. |
| 원격 비교 제외 | Plan Rebase 기간은 main-only 기준 | songstock/remote 비교는 의사결정 입력에서 제외 |
| 라우팅 고정 | live 스캘핑 AI는 Gemini 고정 | A/B는 `entry_filter_quality` 1차 판정 후 별도 판단. 병목 완화 중에는 원격 전체 엔진 라우팅만 GPT로 바꾸는 단순 교체를 금지하고, 진입/보유/청산 단계별 코호트 비교와 품질 가드(`submitted/full/partial/soft_stop/COMPLETED + valid profit_rate`)를 함께 고정한다. |
| 문서 기준 | 중심 문서는 기준, checklist는 실행, report는 근거 | 중복 작업항목 생성 금지 |
| 일정 날짜 고정 | 모든 작업일정은 `YYYY-MM-DD KST`와 `Slot/TimeWindow`로 고정 | `후보비교 완료시`, `관찰 후`, `다음주` 같은 상대 일정은 무효. 당일 안에 절대 날짜/시각으로 재작성 |
| 관찰 반나절 제한 | live 영향 여부 관찰은 오전/오후 반나절을 넘기지 않음 | 반나절에 미관측이면 관찰축 오류, live 영향 없음, 또는 그대로 진행 가능 중 하나로 판정 |
| 판정 근거 서술 | `유지/보류/미완/폐기/완료` 모두 수치 + why(기대값 영향/원인귀속/표본충분성)를 함께 남긴다. 수치만 나열하고 해석이 없으면 근거 미충족으로 본다. | checklist/report에 why를 추가 기재하고, why가 없으면 완료/보류 판정을 다시 연다 |
| 봇 재실행 | 검증/반영에 봇 재실행이 필요하고 권한/안전 조건이 맞으면 AI가 표준 wrapper로 직접 실행 | 토큰/계정/운영 승인 등 보안 경계가 있으면 실행하지 않고 필요한 1개 명령을 사용자에게 요청 |
| 장중 스냅샷 운용 | 장중 판단용 스냅샷은 `12:00~12:20 full` 1회를 기준으로 하고, 그 외 장중은 `intraday_light` 증분(지연/jitter 포함)으로만 갱신한다. `server_comparison`은 Plan Rebase 기본 입력에서 제외하며, 명시 플래그(`KORSTOCKSCAN_ENABLE_SERVER_COMPARISON`)가 있을 때만 생성한다. `performance_tuning` 거래일 이력은 고정 3일이 아니라 상황별 가변 window(`trend_max_dates` 또는 env)로 운용한다. 체크리스트에 스냅샷 생성 작업을 둘 때는 `max_date_basis`, `trend_max_dates`, `evidence_cutoff`를 함께 기재한다. 12시 full 스냅샷 완료 후에는 admin Telegram 완료 알림을 발송해 일일 작업지시서 전달 기준으로 삼는다. | full 다중 실행, 고정 기간 강제, max date/cutoff 미기재, 원격 비교값을 기준 판단에 혼입하면 규칙 위반으로 간주하고 main-only 기준으로 재집계한다. |
| PREOPEN 판정 범위 | 장전에는 `restart.flag` 반영, 신규 계측 필드 기록 여부, 전일 carry-over snapshot/로그 존재 여부만 확인한다. 같은 거래일의 `submitted/fill/completed` 발생을 장전 통과조건으로 쓰지 않는다. | 장전 항목에 same-day `submitted/fill/completed`를 완료기준으로 넣으면 무효로 보고, `INTRADAY/POSTCLOSE` 판정으로 재배치한다. |
| canary ON/OFF 반영 | canary flag는 `TRADING_RULES` 생성 시 env/code에서 읽히므로 hot-reload 기준이 아니다. OFF/ON 변경은 env/code 반영 후 `restart.flag` 기반 우아한 봇 재시작이 표준이다 | rollback guard 발동 시 canary OFF 값을 먼저 고정하고 `restart.flag`로 재시작한다. 목표 소요시간은 5분 이내, 토큰/운영 승인 경계가 있으면 사용자 실행 명령을 남김 |
| Kiwoom REST 인증 장애 | `8005 Token이 유효하지 않습니다`처럼 런타임 토큰 무효화가 발생하면 실전 중 토큰 rebind/hot-refresh를 시도하지 않고, `restart.flag` 기반 우아한 봇 재시작만 표준 복구 경로로 쓴다. | 주문가능금액 0원 fail-closed 상태가 반복되면 인증 장애로 분리하고 즉시 우아한 재시작을 수행한다. 장중 hot-patch/re-auth 실험은 canary 판정과 원인귀속을 깨므로 금지한다. |
| runtime env 증적 | canary 판정/재교정/롤백 전후에는 main bot PID의 `/proc/<pid>/environ`에서 핵심 `KORSTOCKSCAN_*` 값을 확인하고 checklist 또는 report에 남긴다. 최소 대상은 해당 축 enable flag, threshold/prompt split, runtime route다. | `/proc/<pid>/environ` 증적 없이 "env 혼선 없음"을 가정해 판정한 항목은 조건부로 취급하고, 다음 판정 전에 provenance 점검을 보강한다. |
| 운영 자동화 증적 분리 | cron/runbook/parquet/manifest/동기화 정상화는 운영 증적이다. 이는 튜닝 효과나 전략 승인 근거와 분리한다. | 운영 정상화 항목을 `§8 과제 레지스터`와 `§10 실제 효과 기록`의 EV/전략 판정으로 승격하지 않는다. 필요 시 audit/report 또는 별도 운영문서에만 남긴다. |
| 문서/동기화 | 문서 변경 후 parser 검증은 AI가 실행하고, Project/Calendar 동기화는 토큰 존재 여부를 AI가 확인하지 말고 사용자에게 실행 요청을 남긴다 | 사용자 요청 명령 1개를 남기고, AI는 토큰/캘린더 자격증명 확인을 시도하지 않는다 |
| 환경 변경 | 패키지 설치/업그레이드/제거 전 사용자 승인 | 승인 전 대안 경로 사용 |

## 5. 완료 기준

| 항목 | 완료 기준 |
| --- | --- |
| 튜닝축 선정 | pain point, 실행과제, 정량 목표, rollback guard, 판정시각, 상태가 한 줄로 연결됨 |
| live canary | `N_min`, 주요 metric, rollback guard, OFF 조건, 판정시각이 문서와 로그에 고정됨 |
| 성과판정 | `COMPLETED + valid profit_rate`, full/partial 분리, blocker 분포, 체결품질이 함께 제시됨 |
| 보류/미착수 | 보류 사유, 기대값 영향, 표본충분성 또는 관측 누락 이유, 다음 판정시각 또는 폐기/코드정리 판정이 명시됨 |
| 판정 근거 | 수치, 기준선 비교, why(왜 그 수치가 유지/보류/미완/폐기로 이어지는지)가 한 묶음으로 남음 |
| 폐기 | 재개 조건이 없으면 폐기 문서/부속문서로 내리고 중심 문서에는 요약만 유지 |
| 하위 참조 | 일일 체크리스트, 감사보고서, Q&A, 폐기과제가 역할별로 분리됨 |
| 실제 효과 갱신 | 일일 체크리스트 완료 시 §10 실제 효과 기록을 같은 턴에 갱신함 |

## 6. 정량 목표와 가드

| 지표 | 목표/발동 조건 | 적용축 | 조치 |
| --- | --- | --- | --- |
| `N_min` | 판정 시점 `trade_count < 50`이고 `submitted_orders < 20` | 모든 canary | hard pass/fail 금지, 방향성 판정 |
| `loss_cap` | canary cohort 일간 합산 실현손익이 당일 스캘핑 배정 NAV 대비 `<= -0.35%` | live canary | canary OFF, 전일 설정 복귀 |
| `reject_rate` | `normal_only` baseline 대비 `+15.0%p` 이상 증가 | entry canary | canary OFF |
| `latency_p95` | `gatekeeper_eval_ms_p95 > 15,900ms`, 샘플 `>=50` | entry/latency | canary OFF, latency 경로 재점검 |
| `partial_fill_ratio` | baseline 대비 `+10.0%p` 이상 증가 | entry canary | 경고. `loss_cap` 또는 soft-stop 악화 동반 시 OFF |
| `fallback_regression` | `fallback_scout/main`(탐색/본 주문 동시 fallback) 또는 `fallback_single`(단일 fallback) 신규 1건 이상 | 전체 | 즉시 OFF, 회귀 조사 |
| `buy_drought_persist` | canary 후에도 BUY count가 baseline 하위 3분위수 미만이고 `blocked_ai_score_share` 개선 없음 | `buy_recovery_canary` | canary 유지 금지, score/prompt 재교정 |
| `recovery_false_positive_rate` | canary로 회복된 BUY 중 soft_stop 비율이 `normal_only` baseline 대비 `+5.0%p` 이상 증가 | `buy_recovery_canary` | canary OFF, score/prompt 재교정 |

## 7. 매매단계별 Pain Point

| 단계 | Pain point | 현재 증거 | 기대값 영향 | 우선 판정 |
| --- | --- | --- | --- | --- |
| 진입 | Gemini 전환 후 BUY drought, WAIT65~79 과밀 | 04-22 12시 기준 `WAIT65~79 total_candidates=121`, `recovery_check=21`, `promoted=0`, `submitted=0`, `blocked_ai_score=97건(80.2%)` | 미진입 기회비용 증가, 표본 고갈 | 현재 확정: `buy_recovery_canary` 유지, `prompt` 재교정 1축 적용 |
| 진입 | BUY 신호 자체 부재 시 전체 일정 지연 | `04-22` 종합 기준 `recovery_check=40`, `promoted=6`, `submitted=0`, `completed_trades=0`; BUY 후보가 없거나 너무 적으면 `entry_filter_quality`, `threshold`, HOLDING/EOD까지 모두 표본 부족으로 밀린다 | 후속 축 판정과 보유/청산 개선 일정이 기약 없이 밀림 | 대기 판정: `2026-04-23 INTRADAY BUY sufficiency checkpoint`, 부족 지속 시 same-day next-axis live 교체 |
| 진입 | BUY 후 제출 전 latency/budget 병목 | 04-21 preflight `latency_block=40`, `submitted=0` | threshold 완화만으로 거래 회복 불가 | 현재 확정: `recheck -> submitted` 연결성 우선 |
| 진입 | `shared` 호출 혼입 가능성 | 04-22 오전 실전 로그 `PROMPT_COUNTS={"scalping_shared":39,"scalping_buy_recovery_canary":19,"scalping_entry":357,"-":47}`, `SHARED_STAGE_COUNTS={"ai_cooldown_blocked":39}` | shared를 신규 행동 canary로 볼 근거는 없고, 원인귀속 보존을 위해 코드정리 대상으로만 유지 | 현재 확정: 종료, live canary 아님 |
| 보유 | 포지션 맥락 부족 | 보유 AI가 수익률/고점/보유시간을 직접 입력으로 받는지 미완. `2026-04-23` 덕산하이메탈(`077360`)은 `ID 3331`이 `10:11:09 KST` `scalp_trailing_take_profit`으로 `+0.67%` 완료된 뒤, `ID 3404`가 `10:39:13 KST` 더 높은 가격대에서 `entry_armed -> budget_pass`, `10:39:15 KST` `+매수` 접수로 다시 열렸다. 이어 `ID 3419`는 `12:00:24 KST` `17,520원` 3차 진입 후 `12:02:42 KST` `LOSS soft stop`으로 `-1.6%` 종료됐고, 사용자 관찰 기준으론 그 직후 가격이 다시 `17,520원` 위로 반등했다. | 트레일링 익절 직후 동일종목 고가 재진입과 soft stop 직후 V-shape 반등을 분리하지 못하면, upside를 너무 일찍 끊고 더 나쁜 가격으로 재진입한 뒤 저점 청산하는 이중 기대값 훼손이 반복될 수 있다. | 현재 확정: `position_context` 스키마 설계 유지 + trailing 익절 후 동일종목 재진입 사례와 `soft stop 직후 rebound` 사례를 HOLDING 재판정 입력에 포함 |
| 청산 | EOD/NXT 및 exit_rule 혼선 | NXT 가능/불가능 종목의 EOD 판단 분리 필요 | 청산 원인별 기대값 개선 지점 불명확 | 현재 확정: 후순위 설계 |
| 포지션 증감 | 물타기/불타기/분할진입 축 혼재 | 불타기 수익 확대 관찰, fallback 오염 존재 | 추가진입 기대값 판단 오염 | 현재 확정: `position_addition_policy` 후순위 |
| 운영/데이터 | 리포트 basis 혼선 | 문서 파생값과 DB 실필드 혼용 위험 | 잘못된 승격/롤백 위험 | 현재 확정: DB 우선, 체크리스트 동기화 |

## 8. Pain Point별 과제 레지스터

| ID | Pain point | 실행과제 | 일정 | 상태 | 판정 basis | 기대효과 | 실제효과 | 참조 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BR-0422` | WAIT65~79 BUY drought | `main-only buy_recovery_canary` 1일차 판정 | `2026-04-22 12:00~12:20` | 완료 | 퍼널 지표 + 실현손익, paper-fill은 counterfactual 참고 | WAIT 과밀 완화, BUY 표본 복구 | `candidates=93`, `ai_confirmed=48`, `entry_armed=12`, `submitted=1`, `WAIT65~79 total_candidates=121`, `recovery_check=21`, `promoted=0`, `submitted=0`, `blocked_ai_score=97건(80.2%)`, `gatekeeper_eval_ms_p95=16481ms`, `completed_trades=0`, `open_trades=1` | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `BR-SR-0422` | score/prompt 재교정 즉시적용 준비 | 12시 판정 후 `score/promote` 또는 `buy_recovery_canary prompt` 1축만 선택 | `2026-04-22 12:20~12:30` | 완료 | `blocked_ai_score_share`, `recovery_check/promoted`, `submitted`, latency/budget blocker | BUY drought가 지속될 때 즉시 재교정하되 원인귀속 보존 | `score/promote` 미선택, `buy_recovery_canary prompt` 재교정 1축 적용. `AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE`는 유지 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `BR2-0422` | `buy_recovery_canary` 1일차 종합 | 오전/장중 결과 종합판정 + 다음 액션 고정 | `2026-04-22 16:30~17:00` | 완료 | 퍼널 지표 + guard 대조 | 다음 live 축 유지/롤백/재교정 명확화 | `WAIT65~79 total_candidates=246`, `recovery_check=40`, `promoted=6`, `submitted=0`, `blocked_ai_score=208건(84.6%)`, `gatekeeper_eval_ms_p95=16637`, `full_fill=0`, `partial_fill=0`, `completed_trades=0` 기준 `유지 + 재교정 유지(신규축 전환 보류)` 확정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `LP-0422` | recheck -> submitted 병목 | WAIT65~79 preflight 및 latency blocker 분리 | `2026-04-22 PREOPEN 08:30~08:40` | 완료 | 퍼널 지표 | threshold 오판 방지 | `latency_state_danger=33`, `latency_fallback_disabled=7` 분리 | [auditor report](./2026-04-21-auditor-performance-result-report.md) |
| `PP-0422` | 프로파일 특화 go/no-go | `watching/holding/exit/shared 제거` 중 1축 강제판정 | `2026-04-22 12:20~12:30` | 완료 | 퍼널 지표 + 실전 로그 | 프롬프트 귀속 명확화, 행동 canary 남발 방지 | 행동 canary는 미착수. 진입 병목 해소 전 `watching/holding/exit` 신규 canary 보류 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `SH-0422` | shared 호출 혼입 가능성 | 오전 `scalping_shared` live 영향 관찰 종료판정 | `2026-04-22 12:20~12:30` | 완료 | 실전 로그 + 퍼널 지표 | shared 호출 건수와 진입 결과를 분리해 불량 진입 원인분석 가능 | `scalping_shared`는 `ai_cooldown_blocked` 관찰성 로그로만 확인되어 live canary 대상에서 제외, 코드정리 후보로 격하 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `HC-0422` | 보유 포지션 맥락 부족 | `position_context` 입력 스키마 설계 | `2026-04-22 15:40~15:50` | 완료 | 스키마/로그 필드 | GOOD_EXIT/capture_efficiency 개선 기반 | `position_context` 7개 입력(`profit_rate/peak_profit/drawdown_from_peak/held_sec/buy_price/position_size_ratio/position_tag`)과 canary 분리 원칙, rollback guard 고정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `HE-0422` | HOLDING 성과 불명확 | D+2 최종판정 | `2026-04-22 15:50~16:00` | 완료 | 실현손익 + missed_upside/capture_efficiency | 보유/청산 개선축 우선순위 확정 | `evaluated_candidates=0`, `completed_trades=0`, `holding_action_applied=0`로 표본 미달. hard pass/fail 금지, `방향성 보류`로 잠금 | [performance report](./plan-korStockScanPerformanceOptimization.performance-report.md) |
| `EFQ-0423` | 정상 진입 품질 저하 | `entry_filter_quality` 착수 가능성 재판정 | `2026-04-23 POSTCLOSE 15:20~15:35` | 예정 | 퍼널 지표 + 실현손익 | 불량 진입 감소, 제출/체결 품질 개선 | TBD | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `BS-0423` | BUY 신호 부재 시 일정 지연 | 오전 `BUY sufficiency checkpoint` | `2026-04-23 INTRADAY 10:40~10:50` | 완료 | same-day `ai_confirmed_buy_count/entry_armed/submitted`, `WAIT65~79 recovery_check/promoted`, blocker 분포 | BUY 신호 부재를 오전에 조기 잠그고 장중 전환 필요 여부를 즉시 확정 | `saved_snapshot_at=11:02:55` 기준 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`; `wait6579 saved_snapshot_at=11:03:12` 기준 `recovery_check=20`, `promoted=13`, `budget_pass=15`, `latency_block=15`, `submitted=0`으로 `BUY는 충분하나 entry_armed 이후 병목` 방향성 판정 | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `NXP-0423` | 오전 BUY 부족 시 다음 축 준비 공백 | 준비된 다음 축 1개로 same-day live 교체 전환 | `2026-04-23 INTRADAY 10:50~11:20` | 완료 | `entry_filter_quality` vs `score/promote` 전환 우선순위, rollback guard, `restart.flag`, 첫 live 로그 확인 | BUY 부재가 지속돼도 장중 실전에서 다음 축 타당성을 즉시 확인 가능 | `BUY 부족` 조건은 충족되지 않았고, 즉시 사용 가능한 downstream 후보 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 `ALLOW_FALLBACK` 결합 경로라 `post_fallback_deprecation` 기준 위반 위험이 있어 same-day live 교체는 미실행. `buy_recovery_canary` 유지/고정 후 장후 `LatencyOps0423`에서 fallback 비결합 downstream 축 설계로 넘김 | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `PA-0423` | 포지션 증감 축 혼재 | `position_addition_policy` 상태머신 초안 | `2026-04-23 POSTCLOSE 16:40~16:50` | 예정 | 설계/로그 필드 | 물타기/불타기/분할진입 통합 설계 | TBD | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `EOD-0424` | EOD/NXT 및 exit_rule 혼선 | EOD/NXT 착수 여부 재판정 | `2026-04-24 POSTCLOSE 15:40~15:50` | 후순위 | 실현손익 + exit funnel | 청산 경로별 기대값 개선 지점 확정 | TBD | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |
| `AB-0424` | AI 엔진 A/B 재개 판단 | 기준 조합 대비 `EV +10%` 이상 개선 가능한 진입/보유/청산 엔진 조합 탐색 계획 확정 | `2026-04-24 POSTCLOSE 15:50~16:00` | 예정 | 퍼널 지표 + 모델 비교 준비상태 + 단계별 품질 가드 | 원격 전체 라우팅 단순 교체가 아니라 단계별 엔진 조합 비교 계획 확정 | TBD | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |

## 9. 일정

| 일자 | 판정시각 | 핵심 판정 | 소유 문서 |
| --- | --- | --- | --- |
| `2026-04-22` | `12:00~12:20` | `buy_recovery_canary` 1일차 계량 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-22` | `12:20~12:30` | 프로파일별 특화 1축 go/no-go, shared 제거 종료판정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-22` | `15:40~17:00` | `position_context`, HOLDING D+2, `buy_recovery_canary` 종합판정 | [2026-04-22 checklist](./2026-04-22-stage2-todo-checklist.md) |
| `2026-04-23` | `10:40~11:20` | `BUY sufficiency checkpoint`, same-day next-axis live 교체 여부 판정/반영 | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `2026-04-23` | `15:20~15:50` | `entry_filter_quality`, A/B preflight | [2026-04-23 checklist](./2026-04-23-stage2-todo-checklist.md) |
| `2026-04-24` | `15:20~16:00` | 주간 통합판정, EOD/NXT, AI 엔진 A/B 재개 여부 | [2026-04-24 checklist](./2026-04-24-stage2-todo-checklist.md) |

## 10. 실제 효과 기록

| 날짜 | 과제 | 실제 효과 | 판정 |
| --- | --- | --- | --- |
| `2026-04-21` | fallback(보조 예외 진입 경로) 폐기 후 main-only(메인서버 단독 기준) 정렬 | `fallback_bundle_ready=0`, `ALLOW_FALLBACK=0` 확인 | 폐기 유지 |
| `2026-04-21` | WAIT65~79 preflight | `total_candidates=54`, `budget_pass=40`, `latency_block=40`, `submitted=0` | 제출 병목 우선 |
| `2026-04-22` | `buy_recovery_canary` 1일차 장중판정 | `candidates=93`, `ai_confirmed=48`, `entry_armed=12`, `submitted=1`, `WAIT65~79 total_candidates=121`, `recovery_check=21`, `promoted=0`, `submitted=0`, `blocked_ai_score=97건(80.2%)`, `gatekeeper_eval_ms_p95=16481ms`, `full_fill=0`, `partial_fill=0`, `completed_trades=0`, `open_trades=1` | BUY drought 지속, prompt 재교정 필요 |
| `2026-04-22` | 프로파일 특화/shared 제거 장중판정 | `PROMPT_COUNTS={"scalping_shared":39,"scalping_buy_recovery_canary":19,"scalping_entry":357,"-":47}`, `SHARED_STAGE_COUNTS={"ai_cooldown_blocked":39}` | `shared`는 코드정리 대상, `watching/holding/exit` 신규 canary는 진입 병목 해소 전 보류 |
| `2026-04-22` | `buy_recovery_canary prompt` 재교정 즉시적용 | `recovery_check=21`, `promoted=0`, `submitted=0` 근거로 `score/promote` 대신 전용 recovery prompt 1축 선택, `AI_MAIN_BUY_RECOVERY_CANARY_PROMOTE_SCORE` 유지 | main-only 단일 canary 유지 |
| `2026-04-22` | HOLDING D+2 최종판정 + hybrid 확대 여부 | `post_sell evaluated_candidates=0`, `trade_review completed_trades=0`, `holding_action_applied=0`, `holding_force_exit_triggered=0` | 표본 미달로 `방향성 보류`, 확대 보류 유지 |
| `2026-04-22` | `buy_recovery_canary` 1일차 종합판정 | `WAIT65~79 total_candidates=246`, `recovery_check=40`, `promoted=6`, `submitted=0`, `blocked_ai_score=208건(84.6%)`, `gatekeeper_eval_ms_p95=16637`, `completed_trades=0` | `유지 + 재교정 유지`, `entry_filter_quality` 전환은 04-23 POSTCLOSE 재판정 |
| `2026-04-23` | HOLDING 축 참고 사례 추가 | 덕산하이메탈(`077360`) `ID 3331`이 `10:11:09 KST` `scalp_trailing_take_profit`으로 `+0.67%` 완료된 뒤, `ID 3404`가 `10:39:13 KST` 더 높은 가격대에서 `entry_armed -> budget_pass`, `10:39:15 KST` `+매수` 접수로 재진입 경로를 다시 열었다. 이어 `ID 3419`는 `12:00:24 KST` `17,520원` 3차 진입 후 `12:02:42 KST` `LOSS soft stop`으로 `-1.6%` 종료됐고, 사용자 관찰 기준으론 직후 `17,520원` 재상회 반등이 나왔다 | HOLDING 축에서 trailing 익절 품질, 동일종목 재진입 guard/cooldown, `soft stop 직후 rebound` 오판을 함께 분리 검토해야 함 |
| `2026-04-23` | 오전 BUY sufficiency checkpoint | `saved_snapshot_at=11:02:55` 기준 `candidates=124`, `ai_confirmed=66`, `entry_armed=36`, `submitted=1`, `budget_pass_events=1893`, `order_bundle_submitted_events=2`, `latency_block_events=1891`, `quote_fresh_latency_blocks=1693`, `gatekeeper_eval_ms_p95=16869ms`; `wait6579 saved_snapshot_at=11:03:12` 기준 `recovery_check=20`, `promoted=13`, `budget_pass=15`, `latency_block=15`, `submitted=0` | `BUY 부족`이 아니라 `BUY는 충분하나 entry_armed 이후 병목`으로 잠금 |
| `2026-04-23` | same-day next-axis live 전환 검토 | 현재 코드상 즉시 사용 가능한 downstream 후보 `SCALP_LATENCY_GUARD_CANARY_ENABLED`는 `sniper_entry_latency`에서 `SCALP_LATENCY_FALLBACK_ENABLED` 및 `ALLOW_FALLBACK`과 결합되어 `post_fallback_deprecation` 기준에 맞는 독립 downstream 축이 아님 | 장중 live 교체 미실행, `buy_recovery_canary` 유지/고정 후 장후 latency 분해/독립축 설계로 이관 |
| `2026-04-23` | `spread relief canary` 14시 중간점검 | 12시 same-day 교체 이후 `12:00~14:00 KST` raw 기준 `ai_confirmed unique=29`, `entry_armed unique=5`, `budget_pass=1882`, `latency_block=1882`, `order_bundle_submitted=0`, `blocked_ai_score unique share=96.6%`, `quote_stale=False 1817`, `quote_stale=True 65`, `spread_too_wide=1380`, `ws_jitter_too_high=566`, `ws_age_too_high=217`; `latency_canary_reason`은 `spread_only_required=964`, `low_signal=842`, `quote_stale=65`, `missing=11`, `fresh spread-only ai_score>=85=0`; snapshot `saved_snapshot_at=14:03:44` 기준 `budget_pass_to_submitted_rate=0.1%`, `quote_fresh_latency_pass_rate=0.1%`, `full_fill_events=2`, `partial_fill_events=0`, `fallback_regression=0` | 제출 회복 효과 미확인. 14:15 재점검에서도 `14:04:30~14:15:17` 신규 `ai_confirmed=0`, `entry_armed unique=2`라 즉시 완화 표본이 부족하다. 실전 `[LATENCY_SPREAD_RELIEF_CANARY]` 통과는 0건이므로 전역 spread 완화/threshold 즉시완화 금지, 장후에는 `min_signal/tag/allowlist`와 `spread_only_required` 조건을 재설계 후보로만 재판정 |
| `2026-04-22` | Plan Rebase 중심 문서 감리 반영 | S-1~S-3, B-1~B-4 반영 | 조건부 승인 시정 완료 |

## 11. 하위 참조문서

| 문서 | 역할 |
| --- | --- |
| [2026-04-22-stage2-todo-checklist.md](./2026-04-22-stage2-todo-checklist.md) | 오늘 실행 체크리스트와 자동 파싱 작업항목 |
| [2026-04-23-stage2-todo-checklist.md](./2026-04-23-stage2-todo-checklist.md) | 다음 영업일 실행 체크리스트 |
| [2026-04-24-stage2-todo-checklist.md](./2026-04-24-stage2-todo-checklist.md) | 주간 통합판정 체크리스트 |
| [2026-04-22-auditor-performance-result-report.md](./2026-04-22-auditor-performance-result-report.md) | 오늘 감사 기반 성과/병목 판정 |
| [2026-04-21-auditor-performance-result-report.md](./2026-04-21-auditor-performance-result-report.md) | 직전 영업일 감사 기반 성과/병목 판정 |
| [audit-reports/2026-04-22-plan-rebase-central-audit-review.md](./audit-reports/2026-04-22-plan-rebase-central-audit-review.md) | Plan Rebase 중심 문서 구조/원칙/일정 감리보고서 |
| [workorder-0421-tuning-plan-rebase.md](./workorder-0421-tuning-plan-rebase.md) | Plan Rebase 실행 로그와 상세 근거 |
| [plan-korStockScanPerformanceOptimization.execution-delta.md](./plan-korStockScanPerformanceOptimization.execution-delta.md) | 원안 대비 실행 변경사항 |
| [plan-korStockScanPerformanceOptimization.performance-report.md](./plan-korStockScanPerformanceOptimization.performance-report.md) | 정기 성과 기준선과 반복 성과값 |
| [plan-korStockScanPerformanceOptimization.qna.md](./plan-korStockScanPerformanceOptimization.qna.md) | 반복 판단 기준과 감리 Q&A |
| [archive/](./archive/) | 폐기 과제, 과거 workorder, legacy shadow/fallback 경과 |
