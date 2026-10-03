# 장후 정책 성공 보존 제약 정리·실제 생성기 검증 계획 — 2026-10-03

## 목적과 권한

사용자 후속 지시에 따라 기계·보조의 후보 선정은 기존 정책 대비 승률 개선을 우선한다. 성공 100%·80% 보존은 탈락 조건으로 사용하지 않는다. 성공 제외·실패 회피·지원수·비용 차감 성과를 함께 공개한다. 원천·비용·시간순 검증·미평가 변경·hard safety는 유지한다. 기존 운영 문서의 이전 보존 기준보다 이번 사용자 지시가 우선한다.

이번 실행: 실제 생성기/검증기 수정, 보유 원천 격리 재생성, 모든 장후 정책의 보존 제약 조사와 후속 구현계획, 삼성/그 외 후보 실행성 확인, 기존 작업본 통합 검토·커밋 준비. 새 수집·provider 호출·운영 정책 발행·배포·재기동은 범위 밖이다. 배포 대기는 유지한다.

**실행 완료:** [반복 리뷰·격리 결과](../audits/postclose-policy-winrate-objective-migration-review-2026-10-03.md). 80% 제거 직후 선택된28.73bp 후보에서 trace fallback 분모 결함을 발견해 native identity 계약도 보완했다. 최종 등록9개·별도 refinement88개·보조 KRX12개 평가 결과 정식 신규 선정0. 개선 패턴과 source/지원수 부족을 구분했고, publisher는 중간 분모의 보고서를 거부한다. 통합1,460 tests 및 최종411 tests PASS. W0~W4의 이번 실행 범위는 완료, 아래 다른 정책군의 후속 구현은 계획으로 남긴다.

## 실행 순서와 종료 조건

1. **W0 기준선**: 기존 dirty 파일·패치·운영 정책 hash 보존. 동일 원천과 실제 생성기 함수로 변경 전 결과를 고정한다.
2. **W1 실제 기계/보조 경로**: 등록 VWAP 생성기·publisher의 80%, 별도 기계 refinement·validator의 100%, 보조 stage의 성공 제외0·EV 우선 순위를 정리한다. 학습 승률/표본 보정 순위, 동결 후보의 후단 승률 개선, nullable 분모를 일치시킨다. cache·frozen 선택·검증기 version을 함께 갱신한다. 기존 발행 정책은 역사적 계약으로 읽되 새 후보에 이전 계약을 적용하지 않는다.
3. **W2 격리 재생성**: review→보완→표적회귀 후 동일 입력으로 재생성한다. 후보 수·순위·선정·탈락 원인·승률·순손익·시간/메모리 및 입력/운영 불변성을 비교한다. 연구용 미등록 규칙과 실제 생성기의 등록 탐색 범위를 구분한다.
4. **W3 전체 정책 조사와 실행성**: 장후 stage registry/생성기/검증기에서 성공 보존 조건을 전수 검색한다. safety·coverage·비용 조건과 구분하고 제거 대상의 owner·지표·회귀·후속 작업을 명시한다. 삼성 조기 확인2건의 실제 custody/order/terminal 계보, 그 외 필터의 native identity와 후단 미평가 변경17건을 보유 자료에서 확인한다. 없는 증거는 미입증으로 닫는다.
5. **W4 통합 준비**: 기존 source/연구 수정과 이번 objective 수정의 영향을 재검토하고 코드/문서 검사, 커밋 대상 manifest를 남긴다. 새 운영 성과나 배포/PID 수용으로 보고하지 않는다.

소스 위치: 기존 `src/engine/scalping`의 정책 생성·검증 owner, `src/engine/error_detectors`의 의미 검증기, 기존 `src/tests`에 회귀를 둔다. 새 engine root 모듈은 만들지 않는다. 임시 재생 harness와 결과는 `tmp/postclose-winrate-selection-migration-20261003/`에 격리한다.

## 검증

- 성공 일부를 제외해도 학습·후단 승률이 개선되면 보존율 때문에 탈락하지 않는다.
- 성공 전부를 유지해도 승률이 개선되지 않거나 분모가 없으면 선택하지 않는다.
- 후단 결과로 학습 후보를 재선정하지 않는다. 캐시·동결 선택의 목적 version 불일치는 명시 거부한다.
- 비용/원천/미평가 변경/표본 및 catastrophic guard는 기존 책임대로 검증한다.
- Python 표적 pytest/compile, diff, 문서 링크/owner/print-only parser를 통과한다. 외부 sync는 실행하지 않는다.

## 관련 owner

- [범위 재정리](main-machine-auxiliary-samsung-scope-reorganization-plan-2026-10-03.md)
- [보조 생산자·소비자 A6](auxiliary-source-producer-postclose-consumer-improvement-plan-2026-10-03.md)
- [직전 연구 결과](../audits/main-machine-decision-cohort-target-first-research-review-2026-10-03.md)
- [오늘 실행 owner](../checklists/2026-10-03-stage2-todo-checklist.md): `PostcloseWinrateObjectiveMigration1003`

## 전체 장후 정책 조사·보완 설계

조사 경계는 `postclose_summary_handoff.STAGE_REGISTRY`의16개 stage와 `deploy/run_threshold_cycle_postclose.sh`의 직접 실행 module, 연결된 정책 생성·승격·runtime 검증기다. 단순 `100`/`80` 숫자 검색 외에 winner/success/lost/preserve/retention, 전체 행·최악값·일별 delta 조건도 조사했다. 상세 검색 결과와 wrapper module 목록은 W0 임시 증거 경로에 남긴다. OFF/관측 전용 정책을 자동 활성화하지 않는다.

| 정책군 / 코드 owner | 현재 조건의 의미 | 보완·수용 시험 |
|---|---|---|
| Main 등록 기계 / `ai_action_outcome_calibration.build_winrate_policy_report`, `mechanistic_entry_runtime_policy._winrate_successor_hurdles_valid` | 학습·후단·publisher에 성공80% 보존 | 이번 제거. 지원수30/10·노출50%·비용 결합 raw 승률 개선·보정 승률5pp·시간순 분리를 유지. 성공75%만 보존해도 개선 후보를 선택하는 생성기→검증기 회귀 |
| Main 기계 refinement / `entry_strategy_policy`, `build_main_strategy_refinement` | 성공100% 보존 및 회수 성공 우선 순위 | 새 v8 후보는 전체 집단 승률 개선으로 학습·후단을 검증. 순수 실패 회피 후보도 회수 성공0이라는 이유로 탈락시키지 않는다. 이미 발행된 v7 영수증 읽기는 역사적 계약으로 구분하며 새 v7 발행은 거부 |
| Main 보조 / `compact_auxiliary_paired_replay.evaluate_auxiliary_stage` | 성공 PASS 제외0 및 paired EV 우선 | 이번 v5로 변경. 학습 동결·후단 승률 개선, 비용·정확 응답·VETO source 지원 유지. 성공 일부 제외·EV 감소 후보라도 승률 개선이면 보존율 때문에 탈락하지 않음. 서로 다른 목적의 frozen/cache 혼합 거부 |
| 제출 지연 / `pre_submit_delay_tuning` | `winner_retention`은 null 진단 필드; 실행모형·비교호가·비용 차감 개선이 선정 조건 | 성공 보존 게이트 추가 금지. 학습에서 동결한 후보와 incumbent의 동일 비교집단 승률/성공 제외/실패 회피를 후속 보고서에 병기. 호가 결손을 실패0·성공 보존 실패로 취급하지 않는 회귀 |
| Cancel wait / `automation.entry_cancel_wait_tuning` | 실제 실행모형 표본20·시간순 검증·EV 및 일별 순손익 하한 개선 | 직접 성공 보존 게이트 없음. 재생 가능한 동일 주문의 총성과 개선으로 비교하고 개별 기존 성공 손실은 진단. 미해결/late fill/owner reconciliation은 safety로 유지 |
| Entry timing / `automation.machine_entry_timing_tuning` | rolling EV·명목 EV·일별 순손익 개선, 독립 source/표본 | 성공 보존 게이트 없음. rolling 기준과 winner 제외를 분리하고 후보별 비교분모·승률을 추가하는 후속계획. 보호 exit 조건은 유지 |
| Weakness / `automation.market_weakness_hysteresis_tuning` 및 machine attribution | source-bound candidate·out-of-sample review·허용 상태 전이 | 성공 보존 게이트 없음. 같은 scope의 incumbent/candidate 성과와 상태 전이 검증을 묶고 기존 성공 제외율은 진단 전용 |
| Initial quantity / `initial_quantity_policy` | `winner_following_lower_coverage_below_80pct`는 승리 거래의 후속 분봉 관측률. 일별 delta 비음수도 별도 조건 | 80%를 성공 보존율로 오인해 제거하지 않는다. 후속 계획에서 `winner_following_source_coverage` 의미를 명시하고 관측 결손/성과 악화를 분리한다. 모든 날짜 비음수 조건은 전체 성과 개선을 막는지 별도 paired 연구; 자동 완화하지 않음 |
| Entry split / `entry_split_order_plan` | 적격 source80%·지원수·P10/ES10/worst·참여율·자본효율 및 `min(deltas+stress)-error > 0` | 직접 성공 보존율은 없음. **암묵적으로 모든 paired 거래의 개선을 요구하는 최악 delta 하한**은 후속 최우선 재설계 대상. 평균 paired 개선의 오차/불확실성 하한과 tail safety를 분리하여 성공 일부 손실에도 전체 개선을 선택할 수 있도록 연구·계획. 기존 실행/수량 safety는 그대로 |
| Scale-in split / `scale_in_split_order_plan` | 실제 base order/수량·owner 보존과 paired 경제성 | 주문·custody 보존은 성공 보존과 다르다. AVG_DOWN의 같은 owner 비교만 허용하고 PYRAMID 복원 금지. 지원수·경제성·주문권한 회귀 |
| Trailing / `trailing_*_replay`, `trailing_*_policy` | exact cost·terminal·슬리피지 민감도·안전 exit·성과 비교 | 성공100% 보존 조건 미발견. 개별 성공 제외·전체 비용 차감 성과·tail 변화의 표를 추가할 후속계획; protect/emergency 권한 조건 유지 |
| Holding vote / `holding_path_vote_policy` |15셀 provisional 고정 baseline; `operator_directed_initial_baseline_2026_09_26` | 경험적 정책 최적화와 구별. 기존 결과를 새 승률 후보 선정이라고 보고하지 않는다. 후속 successor는 동일 holding/exit 기회의 검증된 순성과 비교를 도입하는 별도 설계 필요 |
| Widget advisory/auto trade / `widget_advisory_calibration`, `widget_auto_trade_policy_calibration`, paired replay | 관측 반복 확인·paired EV/net·tail·source gates; win rate 일부 진단 | 직접 성공 보존 게이트 없음. 동일 scope·custody·train-only 비교표를 확장하고 성공 제외는 보고만 한다. observe/live 권한을 전환하지 않음 |
| Samsung 별도/Low-price episode / `samsung_machine_entry_tuning`, `low_price_two_leg_tuning` | paired 동일 profile EV/일별 net 및 관측 빈도 비율 | 빈도 보존과 승리 사례 보존 구분. 빈도/지원수는 과소노출 검증으로 보고, winner 보존 게이트는 추가하지 않는다. Episode OFF 유지 |
| Source labels/attribution/collector/research capacity·allocation/summary | 원천·용량·운영 진단 또는 보고서 연결 stage | 성공 보존율로 후보를 탈락시키는 정책 생성기가 아님. valid-empty/source-gap 및 선정/PID 상태 분리 |

### 후속 구현 묶음과 완료 기준

1. **공통 비교 증거**: 각 정책 producer의 기존 evidence schema에 `objective_version`, incumbent/candidate의 기회 분모·승/패·미평가, 학습/후단, 제외 성공·회피 실패, paired net·tail을 넣고 publisher가 재검증한다. 보존율은 `diagnostic_only`이며 eligibility 식에서 참조하지 않는다. 정책별 기회 단위·목표를 공통 숫자로 덮어쓰지 않는다.
2. **암묵 제약 해소 연구**: Entry split의 최악 개별 delta와 Initial quantity의 모든 날짜 비음수 조건을 보유 paired 자료로 A/B 비교한다. 더 높은 승률/전체 순성과 후보가 개별 성공 때문에 탈락하는 건수, tail 악화와 자료 결손을 각각 집계한다. 새로운 하한 계산법은 학습에서 고정하고 후단 재선정 없이 검증한다. 이번에는 해당 매매·경제성 safety 조건을 변경하지 않았다.
3. **다른 정책 승률 목적 이행**: 정책별 정의가 필요하다. 진입은 비용 결합 성공/선택기회, 취소·분할은 동일 주문기회의 terminal 순성과, holding/exit는 동일 포지션의 비용 차감 완료 결과다. 같은 정책/동일 분모의 승률 개선을 우선 비교하고 전체 net·위험·노출 변화를 병기하는 설계로 확장한다. 승률 계산이 없는 provisional/observe 정책에 임의 성공 label을 만들지 않는다.
4. **전체 consumer 동기화**: schema/cache/동결 파일/health/publisher를 한 변경으로 수정하고, 과거 immutable 정책 읽기와 새 후보 생성 계약을 분리한다. 재생성은 tmp 격리부터 수행한다. 기존 정책이 더 나으면 승계하고, 유효한 개선 후보가 있으면 성공 보존 비율과 무관하게 선택한다.
5. **수용 회귀**: 성공100% 보존+승률 비개선은 미선정, 성공80% 미만+승률 개선은 적격, 미평가/표본0은 null/부적격, 후단 역전 시 승계, 미래 값/다른 scope 혼합 거부. 실행 권한 검증은 별도 유지한다.

6. **실행 중 발견한 native 분모 결함**: 등록 생성기에서도 현행 date gate 이후 trace fallback을 독립 기회로 세지 않도록 구현했다. 같은 고정 감시 admission의 반복은1기회이며 ID가 없는 시도는 제외 사유로 남긴다. 기존 자료2,876행의 계보 복원이 후속 연구 우선순위다. 동일 평가 시도/원본 source hash/venue·session·watch generation이 정확히 연결될 때만 복원하고, 과거누락 때문에 새 source collection을 요구하지 않는다. 복원 불가능한 행은 관측 후보 증거로만 유지한다.

이 표의 Main 기계·보조는 이번 구현 대상이다. 나머지 정책군은 사용자가 요청한 전수 점검·보완 **계획**이며 구현 완료로 표시하지 않는다. baseline 문서 §7의 이전80%·보조 EV 우선 설명은 새 목적 계약을 문서 전체에 반영하는 후속 baseline 갱신 대상이다.
