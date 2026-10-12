# 10/12 EOD·장후작업 복구와 10/13 기동 준비

상태: **완료 — 10/13 07:00:37 복구 최종화 DONE·10/13 기동 준비 전체 계약 PASS**. 원천일은 `2026-10-12`, 다음 기동일은 `2026-10-13`으로 고정한다. 사용자가 EOD 종료 대기, 장후 운영 모니터링, 필요한 보완·재실행과 정상 종료·다음 기동 준비를 지시했다. 23:27의 PASS는 당시 코드·원천의 역사 영수증이며 후속 배포를 증명하지 않는다. 이번 점검에는 기존 bounded source-only 복구와 영향 회귀 검증을 적용하며 Main/manual 수탁·정책·주문·provider·안전 조건을 유지한다.

## 10/13 07:00 오류 알림 재점검

**07:12:37 현재 준비 전체 계약 PASS, 최종 종료 세대 결속 PASS**. [재점검 영수증](../../tmp/postclose-monitor-20261012/main-repair/alert-0700-recheck-20261013.json)에 원 알림과 현재 검증을 구분해 기록했다.

- 07:00:11 알림(`cron-20261013T070001-2139339`) 당시 새 controller는 완료됐지만 이전 준비 영수증은 현재 원천 세대와 달라 `prepared_source_or_release_changed`였다. 현재 controller hash는 원 알림의 `6c19d131…`와 같다. 07:00:30 준비 재생성 뒤 source10/12·target10/13·selected `2223ac9e…` 전체 계약을 직접 재검증했고 findings는 없다.
- 정리는07:00:13, 최종화는07:00:37에 종료됐다. 알림은 두 종료 전의06:50 마감 초과를 검출했다. 07:10 자동 full 재점검은 artifact freshness PASS, cron `recovered_late` warning, 나머지5 detector PASS다. 마감 지연은 실제 운영 경고이며 삭제하거나 정시 성공으로 바꾸지 않는다.
- 최종 DONE의 controller/snapshot generation 및 child detector run/hash를 현재 원천과 대조해 불일치0을 확인했다. 현재 결함이 재현되지 않아 코드 수정·재배포·장후 전체 재실행은 하지 않았다. workspace의 별도 변경과 기존 원천 결손 판정은 유지한다.
- 설치된07:35 PREOPEN·07:55 Main 경로는 현재 v6 릴리스로 대사했다. 이번 검증은 기동 준비 증거다. 실제13일 정책 활성화·PID 소비·인증/WS 기동은 예정 시각 이후 기존 `DirectFamilyPreopenPolicyHandoff`에서 확인한다.

## 착수 기준

- 최초 확인: 10/12 17:10 KST. EOD20:05, postclose/controller/tuning20:10, archive20:50 예약은 아직 미도래다. 장후 compute는 정확 원천일 EOD 종료와 DB 날짜·행 수를 검증한 뒤 시작한다.
- 최초 selector는 `native-readiness-20261012-v2` / `cf650549e7a07ed470cd95a500af43336d31232c`, Main PID는 `1215171`이다. 진행 중 실제 worker의 코드 세대를 다시 확인하며 후속 selector로 과거 run을 재라벨링하지 않는다.
- 설치 필수8경로·postclose/finalize print-plan을 대사했다. 최종화의 현행 예약은 **10/13 05:35**, 선행 대기 마감06:00·전체 종료06:50이다. PREOPEN07:35·Main07:55를 별도로 확인한다. [현재 예약 변경 근거](cron-finalization-0535-and-night-research-repair-2026-10-12.md).
- [초기 문맥](../../tmp/postclose-monitor-20261012/initial-context.json), [최신 대기 관측](../../tmp/postclose-monitor-20261012/waiting-state.json), [관측 원장](../../tmp/postclose-monitor-20261012/observations.jsonl). 일회성 상태 관찰은 기존 JSON 영수증만 읽으며 원 시장자료·provider를 조회하지 않는다.

## 사전 발견과 후속 검증

1. 현재 배포본의 `entry_cancel_wait`, `rising_missed`, `auxiliary`, `holding_vote` 코드 해시에 해당하는 fixture 영수증이 없다. [코드 세대 대사](../../tmp/postclose-monitor-20261012/preflight-capability-generation.json). 기능 미구현이나 정상 계산 결과를 추정하지 않고 **코드 검증 결속 미확인**으로 기록한다. EOD 이후 같은 불변 배포본에서 [기존 양성·음성 회귀 계획](../../tmp/postclose-monitor-20261012/fixture-validation-plan.json)을 검증하고, 실제 PASS 로그와 현재 코드 해시에 결속한다. 역사10/11 PASS 영수증을 현재 검증으로 복사하지 않는다.
2. [활성 목록](../audit-reports/2026-09-05-postclose-work-inventory.md)의05:00 표기·10/11 체크리스트 링크는 현행05:35 설치 및10/12 실행 문맥과 다르다. 현행 설치·현재 체크리스트·승인된 예약 변경 근거를 사용하고 문서 불일치를 보존한다. 예약을 다시 설치하거나 앞당기지 않는다.

## 종료 조건

정확 원천일 EOD terminal·DB 결과, 활성7 stage와 wrapper/controller/tuning/archive의 실제 최신 종료, 내부 family의 입력·분모·비용·선정/승계와 source gap, 권고의 직접 consumer를 점검한다. 필요한 복구는 최초 영향 생산자와 stale 하류에 한정하고 review→보완→영향 검증 후 실행한다. 미관측·복구 불가 원천·미승인 숫자 실험은 그대로 보존한다.

최종 summary/tower→10/13 checklist→strict summary handoff→controller/finalization→cleanup→최종 detector의 동일 세대 종료와 10/13 PREOPEN 전체 계약·예약 경로를 확인한다. 자연 07:35 activation·07:55 새 PID 정책 소비·인증/WS·경제성은 별도 미래 수용이며, 준비 성공으로 완료 표시하지 않는다. 현재 기록은 복구 진행 상태이며 전체 장후 완료를 주장하지 않는다.


## 실제 EOD 및 복구 결과

EOD는 20:05:05 시작해 **20:55:35 `completed_with_warnings`**로 종료했다. 실패 단계는 없고 DB의 마지막 가격일은 10/12, 당일 2,623행이다. `266690`, `468670`, `486510`은 가격 미수신 상태를 유지한다. 과거에도 빠진 종목이라는 사실로 정상 무자료·퇴역을 추정하지 않는다. 원천 결손을 보존하고 유효 행만 사용하는 기존 freshness 계약을 유지한다. Archive는 EOD를 기다린 뒤 **20:56:02 DONE**이다. Main 정지는 원래 장후 wrapper의 EOD 완료 후 `BOT_ACTION=stop` 단계가 수행했다.

| 실제 실패 | 원인·수정 | 검증·결과 |
| --- | --- | --- |
| 21:01:44 entry split `atomic_sizing_source_generation_stale` | QA가 불량 라벨 2행을 격리하면서 바꾼 파일 mtime을 실제 writer로 오인했다. 격리 직후 stat 세대를 기록하고, 동일 파일 세대에 한해 native producer summary를 봉인한다. 변경된 원천·실제 writer·foreign manifest는 계속 거부한다. | 원 producer 회귀에서 재현. QA/summary/wrapper 293건, entry-split 소비자 8건 PASS. v1에서도 동일 검증 PASS. 원천 ledger `274c9ab52f540ea11bb079caef289ef9bb70bbd8689f26c57276d81cd5d5baa8`; 21:48:15 entry split 정책 정상 생성. |
| 21:49:36 cancel wait `cancel_wait_source_or_metric_revalidation_failed` | nested policy-generation의 산출 시각이 재검산마다 달라져 동일 원천·지표의 proof가 달라졌다. 출력 시각만 원 산출물에 고정하고 원천·수탁·기준값은 현재 자료로 검증한다. | 관련 69건 및 v2 69건 PASS. 22:13 정책 생성 성공, 실제 제출 0건은 대사 확인 상태. 과거 결손은 `source_gap`, 비용 EV는 null, 공통 timeout 유지. |
| 22:13:52 초기수량 `quantity_output_path_invalid` | 불변 릴리스의 정상적인 공용 data 연결을 전부 금지했다. 알려진 최상위 data 연결만 canonical 경로로 변환하고 하위 링크·파일 링크·다른 연결·상위 이탈·덮어쓰기는 거부한다. | 전체 refresh 산출→committed pointer→consumer를 포함한 96건 및 v3 96건 PASS. 기존 부모 유지·주문 없음·runtime 적용 없음 검증. |
| 22:34:31 필수 Main stop `stop_source_record_unbounded` | 과거 JSONL의 2MB 초과 행 하나가 전체 정책 산출을 중단했다. bounded chunk로 해당 물리 행 전체를 격리하고 파일·offset·행 SHA·바이트 수·결손 분모를 보존한다. 이후 정상 행을 분석하되 미식별 행 때문에 숫자 후보 선택은 거부하고 검증된 부모값을 `source_gap`으로 발행한다. source index 캐시는 decoder owner 코드에도 결속한다. | 손절 56건·stage/bootstrap 소비자 89건 PASS, v4 결합 재검증 145건 PASS. gzip·마지막 미종결 행·뒤 정상 행·원천 hash·실제 parent carry 및 decoder 변경 cache 무효화를 검증했다. |
| 22:56:13 summary handoff `holding_vote_policy_missing_or_invalid` | 숫자 실험의 부모 loader가 과거 10/12 정책에 현재 source-only 릴리스의 장중 handoff를 요구했다. 부모는 원 bytes/정책/원천/strict 종료·동일 값으로 검증하고 현재 runtime은 기존 코드 gate를 유지한다. 과거 숫자 successor는 코드 불일치 상태에서 migration하지 않는다. 재사용 snapshot도 현행 numeric 코드 및 verified incumbent 상태를 확인한다. | 177건 및 v5 불변본 177건 PASS. 실제 10/12 historical parent 검증 PASS. 이전 snapshot의 `incumbent_unverified`는 폐기하지 않고 유효 재사용에서 제외해 native producer를 재실행한다. |

실패한 wrapper와 해당 대기 follower만 종료하고, 성공한 native stage는 현재 코드/원천 계약을 검증한 뒤 재사용 대상으로 보존했다. 새로운 wrapper는 새 release identity로 기록하므로 이전 run을 새 코드 실행으로 재라벨링하지 않는다. 수 GB 원천의 수동 반복 스캔 없이 native producer 및 bounded manifest/receipt를 사용했다. 원 격리 backup과 실패 영수증은 보존했다.

선택 릴리스는 **`postclose-source-seal-20261012-v5` / `e98d39b3e6fa37cc4d77a887e1642df3e47cc27c`**다. workspace HEAD/index 및 별도 사용자 문서는 보존했고, source-only private release에 검토된 16개 source/test 파일만 담았다. native CAS transaction이 `verified`로 종료했고 Main 재기동은 하지 않았다. 첫 selector 보조 스크립트의 callback 형식 오류는 pointer 변경 전에 차단됐으며 같은 native transaction에서 수정·검증을 완료했다. 당시 publishing 상태를 정상 selector로 오인하거나 자동 rollback 성공으로 기록하지 않는다.

코드 세대 fixture는 최초 배포본에서 114건, cancel 시각 수정본에서 115건의 실제 양성·음성 회귀와 로그 SHA로 결속했다. 이전 날짜 PASS를 복사하지 않았다. fixture 검증은 구현 가능성 증거이며 당일 유효 경제 표본·정책 선정·실제 PID 소비를 대신하지 않는다. 위 테스트 수와 불변본 재검증은 서로 중복되므로 합산한 unique 검증 수로 표시하지 않는다.

- [원천 수정 검증](../../tmp/postclose-monitor-20261012/source-seal-regression.log), [소비자 검증](../../tmp/postclose-monitor-20261012/source-seal-consumer-tests.log), [cancel 시각 검증](../../tmp/postclose-monitor-20261012/cancel-clock-regression.log).
- [초기수량 검증](../../tmp/postclose-monitor-20261012/quantity-link-regression.log), [불변 릴리스 검증](../../tmp/postclose-monitor-20261012/quantity-link-release-tests.log), [현재 release/CAS receipt](../../tmp/postclose-monitor-20261012/source-repair-v5-selection.json).
- [현재 fixture 결속](../../tmp/postclose-monitor-20261012/current-fixtures-v2/generation-fixture-validation.json), [초기수량 실제 실패](../../tmp/postclose-monitor-20261012/quantity-publication-failed-status.json).

## 남은 종결 검증

v5에서 wrapper·7개 필수 stage·controller·tuning의 최신 종료와 내부 family의 의미 판정, 10/13 checklist 직접 owner, strict summary handoff, 전체 sealed PREOPEN 계약을 확인한다. 10/13 05:35 최종화·07:35 activation·07:55 Main 실제 소비는 미래 예약으로 구분한다. 현재 기계판정 `no_valid_candidate`, 제출지연 `incumbent_carry`는 stage 오류가 없는 결과다. 비교 부족/과거 원천 결손/미승인 연구 실험은 각각 별도 상태로 남기며 새 정책 개선·실현 수익을 주장하지 않는다.


### 계산 정상성과 분석 부족의 분리

- 제출지연은 같은 원천의 원 commit69건·유효 PASS67건·가격 pair57건을 분석한 `initial_baseline_immediate`, 기본 delay0초다. 체결/청산/PnL을 진단 조건으로 요구하지 않았다. ΔEV 및 realized PnL은 null이다. 정확 제외 사유와 부모 결속 미확인 표본은 보존한다.
- 보조판정은 expected request106·completed40·planned66·missing0이다. 요청 대사 완료를 전체 경제 비교 완료로 표현하지 않는다. 비교15scope의 pair19/expected53, unresolved label30, 개선 scope0이며 다음날 bundle은 기존 값 승계다. 고정 과거 window의 미관측 자료를 단순 미래 maturity로 재라벨링하지 않는다.
- 초기수량은 입력 fact1건을 당시 native projection/actual cost 미확인으로 제외해 유효 completed0건이고 부모를 유지한다. 빈 합계0을 실제 비용 후 성과0원으로 보고하지 않는다. historical PID receipt는 부모 정책의 과거 소비 증거이며 새 릴리스/내일 소비 증거가 아니다.
- 손절 정책의 oversized 원천은 명시적 source gap·숫자 선택 거부·부모 유지다. native stage/policy 생성 완료로 과거 결손 복구나 숫자 실험 수락을 주장하지 않는다.

현재 코드 세대에서 추가 손절 회귀를 포함한 **120건**의 fixture 검증 및 4family native inspection이 PASS다. [현재 fixture receipt](../../tmp/postclose-monitor-20261012/current-fixtures-v4/generation-fixture-validation.json), [손절 회귀](../../tmp/postclose-monitor-20261012/main-stop-oversize-regression.log), [소비자 회귀](../../tmp/postclose-monitor-20261012/main-stop-consumer-regression.log), [불변 릴리스 145건](../../tmp/postclose-monitor-20261012/main-stop-release-tests.log), [실제 실패](../../tmp/postclose-monitor-20261012/main-stop-failed-terminal.json).


### 마지막 source-only 복구와 현행 운영 결속

v4의 필수 손절 단계는 실제 정상 종료했고, 전체 source census에서 대형 과거 행 **1,403건·4,374,846,782 bytes**를 확인했다. 최초 초과 행에서 멈춘 이전 실행을 전체 census로 오인하지 않는다. source gap과 부모 수치를 보존했다. v4가 기존 postclose_exit snapshot을 재사용한 사실은 원 영수증으로 남긴다. 다음 검증이 부모 미확인을 실제 차단했으므로 전체 완료를 표시하지 않았으며, v5에서는 실패한 최초 보유판정 원천 producer를 재실행한다.

[부모/소비자 검증](../../tmp/postclose-monitor-20261012/holding-parent-regression.log), [불변 v5 검증](../../tmp/postclose-monitor-20261012/holding-parent-release-tests.log), [실제 handoff 실패](../../tmp/postclose-monitor-20261012/holding-parent-failed-status.json). snapshot 재사용의 변경된 검증 조건과 다음 실제 기동 수용은 기존 OPEN `DirectFamilyPreopenPolicyHandoff`에 [10/13 checklist](../checklists/2026-10-13-stage2-todo-checklist.md)로 결속했다. 10/12 체크리스트와 과거 seal은 변경하지 않았다. 오래된 미전달 owner ID는 현행 실행 소유자로 추정하지 않는다.


## 23:27 핵심 장후 종결과 예약 최종화 대기

v5 wrapper는 **23:24:27 `succeeded`**, 필수7 stage는 모두 `succeeded`·issues0, 전체 controller는 **23:26:35 `done` / whole-native-chain strict PASS**, tuning은 **23:25:43 success**다. 실패한 최신 run 대신 이전 PASS를 사용하지 않았다. 10/13 준비물은 **23:26:54 `prepared_verified`**이며 현재 릴리스에서 `current_full_contract=pass`, findings0이다. actual PID consumed는 false다. [실제 핵심 종료 영수증](../../tmp/postclose-monitor-20261012/night-core-completion.json), [준비물 전체 계약 검증](../../tmp/postclose-monitor-20261012/night-prepared-readiness.json).

현재 v5 코드 세대 fixture는 **124건 PASS·4family native inspection verified**다. [현재 fixture](../../tmp/postclose-monitor-20261012/current-fixtures-v5/generation-fixture-validation.json). 새 보유 관측은 `experiment_not_armed`, 검증된 부모10/12, selected_cells0이며 10/13 `verified_incumbent_carry` 정책을 실제 발행했다. 모듈32개 호출의 해당 run rc는 모두0이다. [native command metrics](../../tmp/postclose-monitor-20261012/native-night-command-metrics.json)는 장후 단독 실행의 child 측정이고 전체 Main 동시 부하 검증 결과가 아니다.

| 논리 작업 | 실제 실행·산출 판정 | 분석·원천 또는 정책 소비 |
| --- | --- | --- |
| EOD·일봉 | 20:55:35 warnings 포함 종료·실패0·당일DB2623행 | 3종목 결손 보존, 정상 무자료/퇴역으로 추정하지 않음 |
| Archive | 20:56:02 DONE | 원 EOD 종료 후 보존 작업, 원 격리 backup 및 정책/원천 refs 유지 |
| 원천 preflight/final QA·verbosity | 해당 v5 호출 rc0·봉인 정상 | 불량 라벨2행 제외; 나머지 source 경고/unknown을 경제 성과로 변환하지 않음 |
| 기계판정 | native stage succeeded·당일 bundle/terminal 생성 | 기존 등록/적용 상태와 challenger 선정 부족을 구분, 실제 PID 소비 미관측 |
| 라벨·기계 분석 보고서 | 2stage succeeded·같은 원천 해시 | 미관측 label은 원 제외 사유 보존, 결과0/손실로 채우지 않음 |
| 보조판정·prompt 직접 consumer | stage succeeded·strict 및 consumer rc0 | 요청대사 완료와 전체 비교 완료를 분리, 개선0·기존 bundle 승계 |
| 제출지연 | stage succeeded·가격 timing policy 발행 | 같은 의도의 실행가능 quote pair 진단, delay0, PnL/ΔEV null |
| Entry split | 산출물·정책 생성 및 native 소비 검증 통과 | 운영 paired source 부족은 source_gap; 새로운 우월 정책 없음 |
| Cancel wait | report/policy·재검산·summary/PREOPEN 결속 | 당일 실제 제출0 대사, 원 과거 결손·null 보존, timeout 변경 없음 |
| Scale-in split | producer rc0·dated carry | 실제 fill 없음으로 적용 조건 비대상, 모델 EV null |
| 초기수량 refresh | immutable generation·commit pointer·consumer PASS | 검증 비용 completed0·과거 fact1 제외, 부모 유지 |
| WS freshness | finalized report rc0 | 당일 진단이며 내일 연결/신선 quote를 미리 증명하지 않음 |
| Rising missed feedback/prior | native 2producer rc0·현재 capability verified | scout/전용 주문 퇴역 유지; 비대상/empty를 새 수익 증거로 사용하지 않음 |
| Broker cost·보유/청산4종 snapshot | native rc0·정확 postclose_exit4종·parent 검증 | actual cost 미확인은 null; snapshot은 source/custody/정책 결속만 증명 |
| Main stop | 새 source-bound commit·stage succeeded | 대형 미식별 행1403 때문에 숫자 선택 거부·source_gap 부모 유지 |
| Holding vote | 다음날 검증 부모승계 정책 실제 생성 | 숫자 실험 not_armed·선정0·실현 성과 미주장, 현재 runtime code gate 유지 |
| Runtime summary→tower→checklist→strict→controller | 최신 동일 generation·7stage 종료·whole chain PASS | 직접9family 원천9/9·경제 mixed·검증 edge0/후보0; 결손 별도 보존 |
| Tuning monitor | success | 원천·작업 진단; 실제 매매/순익 개선과 별도 |
| 다음날 PREOPEN 준비 | `current_full_contract=pass` | selected e98d39b3e, source12/target13·actual PID false |
| 05:35 최종화→cleanup→최종 detector | 예약 미도래, 아직 실제 성공을 주장하지 않음 | 06:00 선행 마감·06:50 종료 상한. 정상 종결까지 이어서 확인 |
| 07:35 activation·07:55 Main | 예약 미도래 | 기존 OPEN `DirectFamilyPreopenPolicyHandoff`의 정확 PID/정책/인증/WS 수용 |
| Episode/Widget/PYRAMID·별도 AVG_DOWN 연구·Swing OFF | 유효 퇴역/OFF | 신규 worker/정책/주문 복원 없음; 과거 수탁/원장은 보존 |

05:35 최종화의 실제 종료·cleanup·source-date 최종 detector와 그 뒤의 준비물 전체 계약을 재확인한 다음 최종 보고한다. 스케줄을 앞당기거나 Main을 수동 기동하지 않는다. 이 절의 준비 PASS는 다음날 실제 기동/PID/수익 성공이나 최종화 완료가 아니다.


## 10/13 승인된 추가 구현·등록·배포와 하류 재종결

사용자의 후속 승인으로 [보조 회로/제출](../proposals/main-auxiliary-circuit-recovery-and-submit-receipt-remediation-plan-2026-10-12.md)과 [잔여 병목/패턴](../proposals/main-post-readiness-residual-bottleneck-and-unidentified-pattern-research-plan-2026-10-12.md) 계획을 리뷰·보완하고 구현했다. 변경·회귀·frozen native OR·공식 API 확인·신규6정의/4scope의 등록은 [후속 구현 리뷰](main-post-readiness-residual-and-pattern-research-review-2026-10-12.md)가 소유한다.

- 불변 v4 `ca8f298d7cf6ce0c427169a604b29f7c2fd51d73`가 승인 CAS로 선택됐다. Main은 원 EOD stop 이후 OFF이고 수동 기동은0이다. workspace HEAD/index와 타 사용자 파일은 보존했다.
- M 기계 terminal의 `selection_basis` 결손을 native 실행에서 발견해 수정했고 진단 write 실패가 원 finalize/claim/ACK 결과를 바꾸지 않도록 격리했다. 통합1,194건 이후 영향239건을 불변 release에서 재검증했다. 공통 HTTP 실패가 뒤 retry의 SDK deadline에 가려지지 않는 검증205건도 추가했다. 수는 서로 겹친다.
- source9/9지만 stop 코드 결속 오류가 있는 incomplete summary를 checklist가 무조건 census 불일치로 거절하던 구조적 전달 결함을 수정했다. blocker가 남은 complete는 거절하며 영향110건이 작업본/불변v4 각각 PASS다. 이를 위해 engine-root 새 모듈을 추가하지 않았다.
- 새 코드 이후23:20 postclose_exit 스냅샷의 numeric code hash는 현재와 다르므로 재사용하지 않았다. native4종 스냅샷을04:31:08 재생성했으며 `experiment_not_armed`, selected_cells0·현재 code 일치·정확일자 계약 PASS다. stop stage04:34:10, 보조 stage04:34:32 정상 종료다. 제출 지연은 같은 의도 quote 진단을 유지하며 fill/청산 완료를 필수로 추가하지 않았다.
- 신규 registry `4f6fcab1e40f45f84ad7c2614214366a8ec9c268d8fcfa5bdbd7530164c020c2`, candidate13 bundle `8e0bd9516bffd59212dde4f5cadf904858ea18f81bcedc716e14a27861f571b9`, 기존32+신규6=38정의/128scope다. PRE NXT·AFTER SOR 적용 범위를 REGULAR로 복사하지 않는다. 이전106요청/40완료/66계획은 역사 비교로 보존했고 신규 provider 요청0이다. 초기 지정 등록에 별도 경제성/미래 WIN gate를 만들지 않았다.
- 전체 controller **04:35:57 done·whole chain strict PASS**, 현재 활성7stage issues0. [최신 core 인계](../../tmp/postclose-monitor-20261012/main-repair/native-core-handoff-v4.json). target13 prepared_verified 및 [current_full_contract](../../tmp/postclose-monitor-20261012/main-repair/prepared-current-contract-v4.json) PASS·findings0이다. 실제13 PID 소비·경제성·전체 Main+장후 결합 성능은 미입증이다.

현행13 자연 수용은 기존 `DirectFamilyPreopenPolicyHandoff`와 새 결함 owner `AuxiliaryCircuitRecoveryRepair1012`, `NonfixedDispatchReadinessReview1012`의 각1개 current parsed item이다. 05:35 실제 최종화/cleanup/최종 detector를 기다려 종료를 검증한다. 3종목 EOD 가격 결손과1,403대형 미식별 원천 행은 그대로 유지하며 null을0/정상 무자료/수익으로 바꾸지 않았다.

최종 선택v4의 후속 변경을 모두 결합한30 test 파일 **1,952건 PASS·실패0**,50 source/test compile PASS·diff 공백 검증 PASS다. [현재 코드 gate](../../tmp/postclose-monitor-20261012/main-repair/current-release-review-gate-v4.json). 기존 pandas 라이브러리 경고1건 외 새 경고/실패는 없다. 디스크29GiB와 available memory 약5.8GiB를 관측했으며 native PREOPEN/Main/finalize의 실제 launcher·bash script·venv 경로도 PASS다. 이는 계정·인증·WS의 미래 접속 성공을 대신하지 않는다.


## 정규05:35 최종화 실패와 v5 복구

정규 최종화05:35:01에서 전체 controller05:36:01 done·cleanup 완료까지 통과했으나 다음 준비 갱신이 `stop_vote_source_set_changed`로 거절됐다. 보존된10/8 AI 원본과 cleanup의 새 gzip 사본을 감시/독자가 같은 논리 원천으로 처리하지 못한 결함이다. [수리 리뷰](main-post-readiness-residual-and-pattern-research-review-2026-10-12.md)의 원본 우선 계약을 source adapter와 감시기에 함께 구현하고 실제 index·watch·원본 변경/삭제·gzip-only·symlink 음성 회귀를 추가했다. 불변v5 영향259건·격리29건 PASS 후 승인 CAS를 선택했다. 원천일12/target13과 원06:50 종료 상한을 유지하고 영향 스냅샷·stop·하류 인계만 복구 중이다. 이전 준비/strict PASS로 이번 실패를 덮지 않는다.


## 최종 복구 종료와13 기동 준비 — 07:00:37

최종 선택은 v6 `2223ac9e948cdbf79bf2ed1e1b6c4c5d7f069df6`이며 신규6정의 등록(총38)과 native13 후보의 코드 결속을 완료했다. [최종 구현 판정](main-post-readiness-residual-and-pattern-research-review-2026-10-12.md)의53 source/test code gate·통합 및 후속 회귀는 모두 PASS, 미해결 검토 code finding0이다.

원천12 전체 controller06:56:33 done·활성7stage issues0·4family verified·cancel-wait3 consumer verified, [cleanup 이후13 준비](../../tmp/postclose-monitor-20261012/main-repair/current-readiness-final-v6.json)는 current_full_contract PASS·findings0이다. [실제 최종화](../../tmp/postclose-monitor-20261012/main-repair/finalization-verified-v6.json)는07:00:37 DONE이며 chain `9d4dcb3757f2b2528da1469a9767a384f0e4883d770f5a2a13a3b17219540cf9`, snapshot `c746fe928297a6b80957ac8ec2bb031d641610a9c537911683c126f83feeb76b`, detector run `cron-20261013T070030-2154183`·report `37a1fe3edb4e328f22a97efeec7c31e969ab7f657285b9f335b1a531c1a73369`의 동일 세대를 확인했다.

원06:50 예정 상한은 초과했다. 이미 승인된 복구 모드를 사용했고 마감 환경값을 바꾸지 않았다.06:09의 승인 수탁 환경 누락과 rising-missed 재발행의 기본 적용일14 선택을 호출 결함으로 남겼다. 정규 수탁 환경 로더 및 명시publication12/effective13으로 수정하고 잘못 만든14 산출물은 원본 해시와 함께 가역 감사 보존했다. 최종 감시의 미해결 정책/원천 결속 경고는0이며, 남은 EOD3종목 결손·늦은 복구·self-audit 대기·과거 로그 경고와 미식별1,403행/null은 보존한다.

PREOPEN07:35/Main07:55의 정규 routing과 release set을 대사했으며 현재 Main/tmux bot은 OFF다. 실제13 PID/cwd/start ticks·bundle/registry·인증/WS·정상 신호 수용은 기존 `DirectFamilyPreopenPolicyHandoff`와 새 결함 수용2 owner의 예정 Acceptance다. 이번 완료는 실제 기동·경제성·전체 결합 성능 완료를 대신하지 않는다.
