# 장후 승패 보완·배포·기동 준비 실행 리뷰 — 2026-10-03

Owner: [실행계획](../proposals/postclose-outcome-readiness-closure-plan-2026-10-03.md), checklist `PostcloseOutcomeReadinessClosure1003`.

## 코드 보완·재리뷰

- 완료 분봉 CF의 평가 상한은 기존10분이다. 180초는 속도 진단이다. 늦은 손절을 `LOSS_AFTER_PRIMARY_WINDOW`로 분리해 비용 결합 손실로 평가한다. 목표/손절이10분 밖에만 있으면 가져오지 않는다.
- 보유 v1 원천의 명시적 `exact_stop_first_outside_primary_window`는 원본을 변경하지 않고 동일10분 비용 비교에 반영한다. 비용 미결합, 동일 봉 동시 도달, 미도달은 null/exclusion을 유지한다. 비용 결손과 검열의 오류 사유를 분리했다.
- 미평가 기존 ENTER 변경은 제외·변경 수 진단이다. 비교 가능한 지원수와 변경 수 대사를 확인하고 하나의 미평가 변경 때문에 후보 전체를 거부하지 않는다. 기존 성공100%·80% 보존을 새 탈락 조건으로 사용하지 않는다.
- 새 손실 label을 분류·위험 집계와 publisher 검증에도 연결했다. stale checkpoint는 기존 경제 kernel/source hash로 무효화된다.

검증: 영향 모듈592 PASS. 확장 검사에서1,001개 통과 후 연구 원인 기대값4건의 불일치를 발견했고, 해당 원인 기대값을 보완한 나머지·관련 모듈680 PASS(겹치는 검사를 합산하지 않음). 34개 Python compile, diff, 로컬 문서 링크 및 print-only parser 통과. broker 요청/주문·provider·hard safety는 이 코드 수정 대상이 아니다.

## 동일 보유 원천의 격리 재계산

KRX 정규7,069행과 기존 정확 보조 응답을 재사용했다. canonical 정책 발행 없이338.28초에 계산했다. native 시간순 분모와 원본 SHA를 보존했다.

| 기계 refinement | 기존 | 후보 |
|---|---:|---:|
| 학습 선택 기회 |24|11|
| 학습 승률 |58.33%|72.73%|
| 학습 보정 승률 |41.77%|47.95%|
| 학습 비용 결합 경로 평균 |−0.359533%|−0.190359%|
| 후단 선택 기회 |3|1|
| 후단 승률 |33.33%|0%|
| 후단 비용 결합 경로 평균 |−0.624683%|−0.956500%|

91개 후보를 평가해 학습 후보를 선택했고 후단에서 승률 비개선·순위 하락으로 승격하지 않았다. 학습 성공 보존57.14%와 미평가 변경9건은 탈락 사유가 아니다. 늦은 손실을 반영하면서 기존 분모·승률도 바뀌었다. 실제 체결 수익 또는 새로운 독립 검증의 증거는 아니다.

등록 VWAP 생성기와 보조 all/삼성/그 외 연구 비교는 기존 정책 승계다. 삼성 전용 연구 partition을 운영 전용 selector가 적용된 것으로 표시하지 않는다.

## 승인된 운영 후속

통합 커밋 `e6d4d3b9` 배포와 독립13개 경로 설정, 활성5개 서비스 재기동을 실행했다. 재기동 직전 기존 읽기 client로 KRX/NXT 잔고0·미체결0과 위젯 custody 결손0을 확인했다. 새 위젯 PID3137231은 실제 release cwd·10개 선언된 env·startup 영수증 대사를 통과했다. 아직10/6 PID 소비를 의미하지 않는다.

운영 점검에서 overview가 유효 OFF 에피소드 연구를 결손으로 처리하고 격리 준비물을 인식하지 않는 결함을 추가 보완했다. 현재 원천일·strict/controller·선택 release를 모두 재검증한 준비물만 수용하며 미래 live bootstrap을 만들지 않는다. 이 보완을 별도 리뷰·검사 후 Main/분석 경로에 배포했고, 코드가 동일한 위젯/수집 경로의 실제 PID 결속을 유지했다.

후속 검증에서 controller output 변경이 먼저 보고되어 summary input 변경이 가려지고, 실패한 최종 재결속이 stage receipt를 먼저 변경하는 결함을 확인했다. 입력·선행 세대를 쓰기 전에 별도로 검증하고 실패 이유를 controller에 보존했다. 변경된 입력으로 재결속할 때 원 영수증을 그대로 보존하는 회귀를 추가했다. 관련115 PASS. producer 복구 뒤 native summary stage를 먼저 갱신한 후 전체 최종화를 실행한다.

전체 strict/controller와 cleanup·최종 detector를 통과한 뒤 PREOPEN 준비에서 Main 영수증 불일치가 드러났다. native Main stage는 새 승계 재평가와 기존 immutable 발행을 각각 검증했지만 summary 소비자가 두 report hash의 일치만 요구했다. 동일 정책·부모·정확 날짜·원 발행 원천 및 최신 native stage 결속이 모두 확인되는 기존 승계만 수용하고 원 발행/최신 평가 hash를 구분했다. 변경 후보·stale stage·다른 target은 거부한다. summary/controller/준비 관련159 PASS이며 정책 개선·PID 소비 권한을 추가하지 않는다.

정리에서 발견한10/1 provider 예산 요약 결손은 기존 native budget owner로 복구했다. 원장40 records의20예약/20정산을 검증했고 원장·manifest SHA는 그대로 유지했다. 새 호출·예약·예산 변경0이다. 기존 정리의 미완료 판정을 보존하고 정리를 다시 실행해 storage PASS를 확인했다. 압축으로 변한 collector 이력 결속도 native collector→summary로 갱신했다.

최종 warning 대사에서 비승격 다른 시장 진단의 기본 지원 버전을 정책 오류로 표시하고, 삼성 fixed-watch7항목 identity를5항목으로만 검사하는 오탐을 보완했다. 후보 없는 source-gap 및 runtime/apply 모두 false인 보류 진단만 구분하며 승격 version 검사는 유지한다. 실제 원천 대사에서 premarket의 명시적 보류 후보도 이 경계에 포함해 재검증했다. native identity owner로 scanner5/fixed-watch7을 검증하고 잘못된 origin·generation, 중복·시간 겹침을 계속 거부한다. 실제 운영/stop 원천 결손 경고는 그대로 남긴다.

전체 재점검에서 기존 Cancel wait v2 보고서에 새 대사 계약이 없는 것을 확인해 native CLI로 재생성했다. 83 PASS,1.71초·최대 RSS143,204KiB, 실제 API/provider 호출0·raw 재읽기0이다.10/2 당일 제출0은 검증됐고,9/29·9/30·10/1은 원 execution producer census가 없어 과거 확정 미해결 수를 null로 유지한다. 대기시간90/120/600/1200초·scope override 없음은 그대로다.

새 실제 원천을 끝까지 대사하면서 consumer가 요구하는 tower를 native controller가 생성하지 않는 결함을 추가 발견했다. controller의 summary→관측 tower→checklist 생산 순서와 direct strict의 tower 요건을 새 계약에 연결했다. 기존 legacy 계약은 소급하지 않는다. 실제 tower 생산자를 controller로 실행한 뒤 의미감시가 소비를 수용하는 회귀와 tower 부재를 strict가 거부하는 회귀를 추가했다. 관련322 PASS. 코드/운영 문서·현재 checklist를 함께 검증한 뒤 선택 실행본에 배포하고 정확 세대를 다시 봉인했다.

결과 receipt는 `tmp/postclose-outcome-readiness-closure-20261003/`와 `data/runtime/startup_readiness/2026-10-03/postclose_outcome_readiness/`에 보존한다. 최종 배포·실행·정책 결과는 아래 최종 수용에 기록하며 미래 PREOPEN/PID와 구분한다.

## 최종 수용 — 21:03 이후 재검증

- 최초 기존56개 작업본·보완 통합 커밋은 `e6d4d3b9`다. 보완을 순차 배포한 최신 Main/장후 선택 실행본은 **`a17bd6d2587e1204eacd0cd283bcbd854eb71bfc`**, 경로 `/home/ubuntu/KORStockScan-runtime-releases/postclose-tower-readiness-20261003-a17bd6d2`다. 활성 위젯/수집5개 및 기존 에피소드122개 경로는 trading 코드가 같은 `e6d4d3b9`에 결속돼 있다. 서로 다른 owner release를 허용하는 기존 계약으로 source/unit/실제 PID를 대조했다.
- route/pin 변경은 release-set lock에서 실행했다. 최초5개 재기동 명령 자체는 그 lock 밖에서 실행됐고 후속 readback에서 실제 PID/cwd와 설정 경로의 일치를 확인했다. 재기동 직전 잔고·미체결·위젯 custody 점검 및 startup receipt를 보존했다.
- 원천10/2·발행10/3·다음 적용10/6을 유지했다. 최종 whole controller **DONE**, strict **PASS / whole_native_chain / issues0**, 필수 direct 원천 **10/10**, blocking reasons0이다. strict는 실제 **tower·checklist** 두 소비자를 검증했다. native stage13개 succeeded, 에피소드 연구·research allocation2개는 명시 OFF receipt로 종료했다.
- native cleanup·최종 detector와 정확10/6 준비물 봉인은 **21:03:12 KST DONE**이다. 완료 후 `current_full_contract` 재검증도 **PASS / findings0**이며 선택 commit은a17bd6d2다. overview는 `next_session_policy_ready=true`, Main/Episode/Widget loader check 모두 true, `startup_basis=isolated_prepared_next_preopen`이다.
- 완료 후 별도 읽기 전용 전체 탐지는7/7 초기화, **fail0 / warning2 / runtime mutation0**이다. 준비물·완료 ancestor·fixed-watch identity·비승격 version·cancel 소비 오탐은 없다. 남은 경고는 운영 경제성/stop·plan 원천 결손, 기존 code workorder·KOSPI warning 및 변하지 않은 과거 로그다. 정식 최종 detector는 준비물 발행 전 검사를 포함한 당시 상태로 보존했고 완료 후 별도 보고서를 만들었다. 첫 별도 호출의 적용일 누락 실패도 보존한 뒤 정식 wrapper의 `POSTCLOSE_PREPARED_EFFECTIVE_DATE=2026-10-06` 계약으로 재검증했다.
- 최신 영향322 PASS, cancel83 PASS, 앞선 승패/지원수 및 readiness 회귀·compile·diff·로컬 링크·print-only parser를 통과했다. 중첩 suite 통과 수는 합산하지 않는다. 운영 원천의 결손을 코드 회귀 PASS로 해소됐다고 표시하지 않는다.

근거: [종결 영수증](../../data/runtime/startup_readiness/2026-10-03/postclose_outcome_readiness/completion.json), [10/6 준비 재검증](../../tmp/postclose-outcome-readiness-closure-20261003/next-preopen-complete-verify.json), [완료 후 전체 탐지](../../tmp/postclose-outcome-readiness-closure-20261003/detector-complete-readonly.json), [최종화 로그](../../tmp/postclose-outcome-readiness-closure-20261003/finalization-complete.log), [release-set 검증](../../tmp/postclose-outcome-readiness-closure-20261003/release-set-complete.json).

## 장후 정책 전체 결과

| 정책/원천 | 실제 결과 | 남은 증거 경계 |
|---|---|---|
| Main 등록 기계 생성기 | native 적격142시도·등록9가설, 새 적격 후보 없음·기존 승계 | 학습24기회58.33%, 후단3기회33.33%; 학습 후보·후단 날짜/지원수 gate 미충족. 성공 보존율에 의한 탈락 없음 |
| Main 전체 refinement |91가설에서 학습 후보를 고정했으나 승격하지 않음 | 위 표의 후보 후단1기회·승률0%로 기존 후단33.33%보다 개선되지 않음. 미평가9변경·성공 보존57.14%는 진단 |
| Main 운영 경제성 | KRX 구조 적격3,653시도, 운영 paired0 | `machine_operating_population_unbound`; actual owner·완료 비용/손익이 결합되지 않았음. 상승 패턴 부재나 주문 실패를 뜻하지 않음 |
| 보조 AI | 기존 정책 승계, 운영 경제성 비교0 |15행 중 정확 stop11·자연응답 의미2·전송2 결손. 정확 plan writer/trace 결합0. prospective는 미지원 pre-AI scope12·broker capacity2·latency danger1. 이력 원천을 합성하지 않음 |
| 보조 stage 연구 | KRX18 full-cost CF·별도시장1 cost-incomplete 진단, 새 승격 없음 | stage CF는 operating portfolio/실현 손익이 아님. 정상 장후 executor18 provider 호출은 보유 exact 입력의 정책 계산이며 새 원천 수집은 없음 |
| Cancel wait | 새 대사·policy/report 발행 및 summary/tower/checklist/strict/의미감시 소비 verified | 당일 제출0 검증; 과거3일 producer census 부재로 확정 미해결 null.90/120/600/1200초·scope 그대로 |
| 제출 지연 | 가격 분석·재생 후 model_not_validated·승계 | 비교 호가/실행 모델 부족, selected_delay=None; 실제 주문 실패 count로 해석하지 않음 |
| 초기 수량·entry split | 기존 정책/refresh 영수증 수용·승계 | entry split operating paired source 부족; 수량·leg 권한 확대 없음 |
| scale-in split | 적격 주문 없음·승계 | 분할 경제성 개선 미입증. AVG_DOWN owner·PYRAMID 퇴역 유지 |
| timing·weakness·attribution | stage 완료·기존 정책 유지 | 원천 결손/적격 체결 부재; 신규 threshold 선정 없음 |
| Widget 연구 | 관측·기존 정책 승계 | 신규 정식 선정0, 위젯 실제 기동 영수증은 별도 검증 |
| Episode 연구·기존 실행 profiles | 연구 명시 OFF·기존 profile/policy pin 수용 | 기존 실행 profile 전부의 경제성/기동 승인이 아님; 격리3개 유지 |
| Holding vote / exit | 기존 provisional15셀·10/6 dated policy 수용; trailing 기준 승계 | 등급 estimated_provisional, 실현 paired EV 미입증. 오래된 four-axis trailing 퇴역 유지 |
| source quality·collector·capacity | 현재 source preflight·물리 압축 후 generation 결속 확인 | 식별된 제외28행·현재 잔여 hard defect0; unknown token만으로 전체 입력을 차단하지 않음 |

원본 frozen 발행을 유지한 Main 정책은 새 승계 평가와 원 발행 source hash를 각각 봉인했다. dated bundle 파일 SHA는 `05faa575…`, 의미 bundle은 `3c500f6a…`다. publication이 준비된 것과 실제 소비는 구분한다.

## 삼성전자와 그 외의 실제 적용

**Main 전용 정책의 분리 적용은 없다.** 연구는005930 fixed-watch와 삼성전자 제외 집단으로 분리했지만 정식 적격 전용 후보를 확보하지 못했다. 실제 KRX 정규 loader는 두 집단 모두 공통 incumbent를 선택한다. 같은 공통 정책에서도 입력별 hierarchy/leaf 선택은 달라질 수 있으며 그 동작은 삼성 전용 정책 선정과 구분한다.

| 집단 | 기계 policy SHA | 보조 policy SHA |10/6 선택 |
|---|---|---|---|
|005930|`d94fecaf…`|`c23acea3…`|공통 기존 정책 승계|
|005930 제외|`d94fecaf…`|`c23acea3…`|공통 기존 정책 승계|

[실제 의미 hash·분리 여부 대사](../../tmp/postclose-outcome-readiness-closure-20261003/symbol-policy-binding-complete.json)에서 현재 effective bundle은9/28의 `6785d52e…`,10/6 staged bundle은 `3c500f6a…`, 미래 activation은 미실행이다. Widget의 기존 종목별 execution policy는 Main 삼성 전용 연구와 별도 owner이며 loader hash `c70eaa5d…`를 실제 startup receipt와 대조했다.

## 다음 영업일 기동 판정과 인계

| 실행자 | 현재 확인 |10/6 남은 수용 |
|---|---|---|
| Main | 선택 release/예약 route·격리 준비물·loader PASS. 토요일 Main PID 없음은 정상 시간 경계 |07:35 PREOPEN 및07:55 실제 PID/정책 hash. 미래 live bootstrap·PID를 생성하지 않음 |
| Widget | 실제 재기동 PID3137231, release/env/startup policy hash 대사 PASS | 기존07:32 정책 반영·custody 재확인과07:58 기동 경로, 당일 소비·자연 실행 |
| Episode |122인스턴스·366정책 pin PASS, 연구 OFF 유지 | profile별 dated preflight/PID. `cj_cgv_morning`, `youngone_midday`는 새 revision/robustness, `sk_telecom_midday`는 비용 후 경제성 문제로10/2 격리 상태 유지 |

판정은 **준비 계약 PASS / 실제 다음 영업일 기동·자연 경제성 미도래**다. 격리3개를 포함한 모든 에피소드의 정상 기동 또는 앞으로의 실제 주문/수익을 보장하지 않는다. 검증된 기존 정책으로 준비하며, 새 정책·양의 실현 개선을 얻었다고 표시하지 않는다.

`EntryCancelWaitSourceReconciliation1002`의 새 계약 실행 세대/last consumer는 완료했다. 과거 census 결손은 `DirectFamilySourceRepairEntryCancelWait`, Main/보조 운영 원천은 `DirectFamilySourceRepairMainMechanisticEntry`·`DirectFamilySourceRepairCompactAuxiliary`, 당일 PREOPEN/PID는 `DirectFamilyPreopenPolicyHandoff`가 현재 OPEN owner다. 결손은 source_gap/null이며 보유 원천 검증으로 복구되지 않는 동일 입력을 반복 재생하지 않는다.
