# 메인 기계 전수 경제성 연결 보완 리뷰 — 2026-09-20

최신 판정은 아래 **9/20 17시 후속 종결**을 따른다. 이전 절의 미종결·커밋·수치는 당시 증거로 보존한다.

범위: [복구계획 §14](../proposals/main-mechanistic-entry-postclose-full-tuning-loop-restoration-plan-2026-09-20.md#14-공통-데이터미진입-기회비용-경제성-연결-상세-보완계획), 공통 데이터·기회비용 U6/U7/U11의 메인 최초진입 연결. 기존 health·원시각·306파일 migration과 독립 owner 전체를 다시 구현하지 않았다.

**판정: 비교·선정·발행의 확인된 결함을 보완했지만 전체 실행 경제성 완료는 아니다.** 운영 정책 발행과 원화 EV 완성은 별도 수용조건이다. 후보 없음/유효 incumbent carry를 양수 경제성 또는 ME8–ME14 전부 완료로 보고하지 않는다.

## 구현·검증한 변경

- 현행 incumbent부터 기존 bounded grid를 탐색한다. 학습 행동이 모두 같으면 가장 엄격한 첫 좌표를 자동 선택하던 동률을 제거했다. 같은 행동의 후보 수를 독립 개선 비교 수로 보고하지 않는다.
- 등록된 main scope마다 고유 incumbent·비용·기계 원천을 평가한다. 공통/계층 후보가 각 scope의 source/parent를 결속해 기존 발행기로 전달되도록 연결했다. 다른 scope의 KRX 후보 성공을 요구하지 않는다.
- 기존 날짜별 sealed compact 원천을 optional owner 실행 근거로 소비한다. 최신 하루의 projection이나 다른 날짜의 model proof를 과거 전체에 빌려주지 않는다. 기계 모집단 자체는 compact 표본으로 줄이지 않는다.
- 현재 기계가 막지만 당시 고정 보조판정과 실행 모델이 있는 사례는 후보 ENTER를 기존 owner arm과 비교할 수 있다. 이를 자연 Provider 호출이나 broker fill로 다시 기록하지 않는다.
- 전체 모집단의 실행·비용 근거가 일부만 있으면 원화/day를 null로 유지한다. 동일 promotion 반복과 미종결 RECHECK의 순차 재생이 없으면 포트폴리오 합산을 금지한다. 동일 정책의 대리 Δ=0은 원화 순익 0의 근거가 아니다.
- 실행 지원 후보의 일별 순익·보수적 paired EV를 먼저 비교한다. 기존 0.10%·표본·tail 계약은 유지한다. calibration에서 후보를 동결하고 동결 이후 source-day만 독립 승격 holdout으로 수용한다. hierarchy의 holdout 통과 규칙만 사후 골라 묶는 경로를 제거했다.
- 새 기계 정책 변경과 새 AI prompt의 미검증 동시 변경을 막는다. 여러 scope의 독립 이익만으로 공통 계좌 자본의 동시 승격을 증명하지 않으며, joint replay 없는 다중 scope 후보는 명시적 incumbent carry다. source hash/현재 parent/날짜별 loader 검증을 유지한다.
- summary에서 report 실행 플래그를 미래 writer 검증으로 오인하던 판단을 제거했다. owner replay 없음 자체를 역사적 복원 불가로 선언하지 않는다. 미확정은 `source_gap`이며 기존 checklist의 producer 수리 역할로 전달한다.

리뷰→수정→재리뷰→관련 pytest **459 passed** 및 추가 공통 자본·발행 회귀 **124 passed**(중복 포함; 합산하지 않음). 기존 테스트 파일에 signed owner proof, 신규 진입/비진입, 부분 coverage, 반복 promotion, RECHECK, incumbent 동률, 동결 전 holdout 금지, scope별 발행·부모 정책 결속을 검증했다. Python compile 및 diff check 통과. Provider/브로커 호출·주문·봇 재기동은 이 검증에 사용하지 않았다.

## 아직 닫히지 않은 경제성 경계

1. **원래 BLOCK/RECHECK의 frozen 실행 입력.** 기존 `_observe_entry_economics_before_ai`는 ENTER_NOW에만 실행 계획을 기록한다. 당시 가격/수량/가용자본·고정 compact 결과 없는 BLOCK은 현재 값으로 복원할 수 없다. 이 범위의 새로운 prospective producer가 검증됐다고 주장하지 않는다.
2. **독립 실행 모델 지원.** exact scope의 실제 실행/청산과 모델을 검증한 proof가 있어야 한다. 이번 signed fixture 성공을 실제 운영 데이터의 model validation으로 대체하지 않는다.
3. **반복 재평가와 공통 자본.** 단일 독립 episode 지원은 반복 RECHECK·겹치는 자본의 순차 행동 재생을 의미하지 않는다. 미지원 모집단은 제외/원인 보존이며 정상0이 아니다.
4. **과거 회복 가능성.** source date 9/14–9/16의 sealed compact owner projection이 없고 9/17도 operating model proof가 부족하다. 원본이 영구 소실됐다는 증명과는 다르므로 `historical_unrecoverable`로 종결하지 않는다. 당시 source를 exact 재구성할 수 있는지와 미래 writer 보완을 같은 기존 owner에서 이어야 한다.

이 결손은 단순한 표본/시간 대기가 아니다. ME9/ME10의 전체 실행·순차 재생과 ME14의 실제 비용 후 경제성 수용은 OPEN이다. 다음 거래일의 자동 carry는 운영 연속성일 뿐 결손 완료증명이 아니다.

## 실행 receipt

대상 원천일 2026-09-17, 발행일 2026-09-20, 예정 effective date 2026-09-21. 결과와 정책·후행 검증 hash는 아래에 실제 실행 후 기록한다. 작업본 base는 `a198c3b9bb3e0d78bff3feebe05b3d394a467973`이며 다른 세션의 compact 증거 분리 보완을 포함한다. 현재 날짜 9/20 checklist는 없고 9/21은 미래 owner다.


재생성 중 기존 relabel 함수가 이미 full-cost 계약을 가진 행도 먼저 pipeline을 읽는 문제와 scope별 반복 읽기를 확인했다. 최초 실행은 보고서 교체 전에 중단했으며 원 보고서 byte hash가 backup과 같은 것을 확인했다. 기존 날짜별 캐시를 scope 사이에 공유하고 이미 검증된 비용/결과 행은 재조회하지 않도록 수정했다. 원천일·표본·cost/holdout/gate 축소는 없다.


추가 bounded 대사: 과거 기준 정책과 엄격 후보의 자연 원천 6건은 9/14의 187660·256840, 9/15의 417200·056190, 9/16의 452280·195870이다. AI WAIT/전송·의미 오류, latency 종결, 실제 최초진입 및 후속 ADD가 서로 다른 경로다. 실제 제출/체결 flag만으로 같은 최초진입 모델 손익을 입증하지 않는다. 이전 8건 중 paired 별칭 2건의 exact 원행 복구는 추가 역사적 relabel 없이는 확정하지 않았으며 ME8 전체를 완료로 표시하지 않는다. 기록: `tmp/main-machine-economic-closure-20260920/prior-eight-disposition.json`.


## 최종 실행·정량 결과

- 코드 commit `d9e2cdae3c9af2a9ac4b0ab472c8e1c89981f937`, feature 및 `origin/main` push 완료. 선택 release는 `/home/ubuntu/KORStockScan-runtime-releases/main-machine-economic-reviewed-20260920-d9e2cdae3`이다. 실제 배포본 **471 passed**, compile 및 source clean/import root 확인. `future_invocations_only_no_restart`; 실제 PID 소비는 다음 정상 기동의 잔여다.
- 완료된 재생성은 release-local main machine-only 1회이며 약 13분 소요됐다. 그 앞의 반복 읽기 발견 실행은 보고서 교체 전에 중단했다. 이어 compact finalize(Provider 호출 없음), summary/tower/checklist를 갱신했다. 같은 원천에 대한 현재 evaluation fingerprint가 일치하므로 추가 전수 재실행을 하지 않았다.
- 9개 등록 scope 모두 처분. 수용은 KRX 정규 1,715건, PREMARKET_KRX_LIKE 230건, NXT aftermarket 2건, integrated aftermarket 334건이며 나머지 scope는 수용0/원천 미확정이다. 합계2,281은 scope 분리된 attempt 진단 수이며 하나의 공통 계좌 포트폴리오 수익 분모가 아니다.
- KRX는 paired7 + natural1,708, calibration4 / holdout1,711이다. holdout 대리값 비교 가능1,710건이며 원화 operating enrichment는0이다. 학습 행동 signature1, 독립 개선 후보0; 선택 좌표는 incumbent `spread100 / fillability15 / ratio5`다.
- 기존/후보 holdout **terminal-path 대리 EV 모두 −0.0054462573%**, 차이 **0%p**. 이전 엄격한 비진입 후보의 +0.005446%p를 경제적 개선으로 유지하지 않는다. 이 값은 actual EV나 유효 executable operating EV가 아니다. 비용 후 원화/day는 **null**이며 blocker는 `machine_operating_population_unbound`다.
- 실제 원천에서 비용 후 executable 개선을 확인한 후보0. 독립 실행모델·BLOCK/RECHECK 원천·episode/공통 자본의 잔여를 테스트 fixture 또는 정책 파일 생성으로 대체하지 않았다.
- 평가 hash `021f32f212d8442518e5b4800768f898afa1140f4b56a16c447a3270ef0e5647`. 최종 9/21 정책 bundle `a805f9e0a3d84d4e92649c3c40a9b5fb5c045c8cc99a4e17ccf2a35412247416`. Main source→단일 machine/compact bundle→dated loader 결속을 확인했고, 이전 9/21 정책과 main 및 모든 scope의 machine policy 본문이 동일하다.
- main scoped verifier `pass`, compact scoped verifier `PASS`. 전체 `--require-summary-handoff`는 **FAIL: `postclose_terminal_status_missing`**이다. 제한적 summary-handoff controller의 앞선 `done`은 전체 native terminal을 뜻하지 않으며 최신 full controller는 `blocked_predecessor_not_succeeded`다. tower도 최신 전체 FAIL을 소비하도록 갱신했다. 과거 terminal을 합성하거나 전체 wrapper를 재실행하지 않았다.
- 다음날 체크리스트 `[DirectFamilySourceRepairMainMechanisticEntry]`는 `producer_contract_repair / source_gap / producer_repair`로 OPEN이다. 이전 `natural_evidence_wait / historical_unrecoverable` 오귀속을 제거했다. 기존 루프 복구 완료 ID를 전체 경제성 완료로 바꾸지 않았다.
- 변경 문서 print-only parser 및 diff check 통과. 브로커/Provider 호출, 주문, 봇/독립 서비스 재기동, 수동 env/threshold 변경, 조기 PREOPEN 실행은 하지 않았다.

**최종 전체 요청 상태: 미종결.** 비교·발행 결함 수리, 검증·push·미래 호출 release 선택·dated carry 발행은 끝났으나 ME8의 paired 별칭 대사 잔여, ME9/ME10의 전체 실행 경제성과 전체 native terminal 증거가 남았다. 유효한 비용 후 EV·일별 순익을 산출했다고 보고하지 않는다.

후속은 기존 producer 수리 ID에서 당시 cutoff·실행 계획/정책·AI/비용·모델/episode 증거를 연결하는 것이다. 단순 sample floor 완화·대리 EV 승격·과거 누락값0 대입·반복 전체 재실행으로 닫지 않는다. 상세 로그와 machine-readable 결과는 `tmp/main-machine-economic-closure-20260920/result.json` 및 같은 폴더의 검증 receipt에 보존했다.

## 9/20 후속 구현·재리뷰 진행 기록

앞의 `d9e2cdae3` 판정은 이전 실행 증거로 보존한다. 이번 작업본은 `fix/main-machine-operating-completion-20260920`, base `ea92be4bf`이며 실행 release와 원 작업본을 직접 수정하지 않았다.

확인하여 수리한 경계:

1. main observer의 ENTER-only 조건을 관측용 BLOCK/RECHECK까지 확장했다. 사용자 승인된 기존 bounded 계좌 읽기만 사용한다. 실제 주문용 plan은 계속 ENTER 및 보조 PASS를 요구한다.
2. pre-AI replay가 AI 응답이 없는 모든 계획을 버리던 조건을 수리했다. 비진입 계획·모집단은 보존하되 호출하지 않은 AI를 만들어내지 않는다. producer summary와 compact projection의 terminal stage 등록·parser 필드까지 연결했다.
3. 동일 promotion 반복을 독립 수익으로 합산하지 않는다. 순차 RECHECK 및 실제 TTL 종결, 동시 reserve/held symbol, 같은 현금 한도에서의 순익·EV·tail·노출·참여율과 stress/모델 오차를 계산한다.
4. 복수 scope의 무조건 차단을 calibration-frozen 전체 조합의 독립 검증 및 publisher 재계산으로 대체했다. 미검증 scope 조합, 불완전 sequence, 변경된 budget, 미호출 보조 AI는 여전히 구체 사유로 차단한다.
5. model calibration/holdout의 시간 순서를 검사한다. 운영 경제성 완료 후 summary가 proxy EV를 읽던 오류를 수리하고, 실제 적용 machine+compact 버전별 중복 제거·rolling/cumulative 완료 손익은 기존 owner를 재사용한다.

프로토콜 확인: 공식 Kiwoom repository HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f` 재확인. `kiwoom/_data/kiwoom_api_spec.json`의 kt00011 및 `kiwoom/specs.py`, 기존 request/parser를 대사했다. kt00011은 POST `/api/dostk/acnt`, raw6자리 `stk_cd`, 선택 `uv`, 기존 인증/API-ID/실전·모의 분리를 유지한다. API parser·인증·주문 protocol을 바꾸지 않았고 검증 중 실제 계좌 요청도 하지 않았다. 공식 원천 snapshot과 조회 시각은 `tmp/main-machine-operating-completion-20260920/official-reference-review.json`에 남긴다.

이번 지원 범위는 고정 자본 조건부 경제성이다. 변경되는 계좌 한도, FIFO 의존 CF, 미호출 AI 재판정, terminal 없는 부분 체결/미청산은 자동으로 유효 무거래가 되지 않는다. 이러한 범위 제한과 과거 필드 누락, 새 모델의 독립 자연 표본 대기는 서로 다르다. 양수 합성 fixture는 자연 이익 증거가 아니다.

검증·실행의 최종 receipt는 후속 재생성 완료 후 아래에 기록한다. 현재 이 문단만으로 전체 완료를 주장하지 않는다.

재리뷰에서 full-population 후보와 소비자가 운영 replay가 아닌 terminal proxy EV를 1차 경제성으로 검사하던 경계를 수리했다. 기존 10bp·sample·tail·독립 holdout 기준은 유지하며 실제 operating EV와 paired Δ를 사용한다. 미검증 모델을 flag만으로 우회하는 후보는 소비자가 거절한다.

검증: 영향 범위 843개 및 WATCHING owner 2개 통과 후, 실제 지표 선택과 RECHECK→BLOCK 변경 판정 수정을 추가하여 관련 calibration/publisher/loader 306개를 재검증했다. 로그는 `tmp/main-machine-operating-completion-20260920/{final-affected-tests,watch-owner-tests,metric-basis-tests-v2}.log`이다. producer→저장/projection→계산과 실제 TTL 종결 회귀, 동일 자본 충돌·중복, joint holdout/hash/subset 차단을 포함한다. 통제 입력의 일별 +600원 결과는 회귀 증거이며 자연 성과가 아니다.

실행 점검 추가 수리: 최초 main 재생성은 provenance 부적격 과거 paired rows까지 가격 재라벨링에 보내 8월 raw를 읽는 것을 발견하여 중단했다. 새 성공으로 기록하지 않았으며 중단 로그를 보존한다. 기존 source-contract 검사와 동일한 사전 필터를 추가하고 부적격 행은 분모/제외 사유를 보존한다. 관련 307개 회귀 통과. 자연 관측 loader 두 함수는 원 캐시 생성 커밋 `d9e2cdae3`와 AST가 동일하고 9/14–17 원천 stat은 캐시 생성 이후 변경되지 않았다. 기존 2,330건 materialization hash와 입력 stat을 `materialization-reuse.json`에 기록하여 재사용한다.

ME8의 과거 미대사 2건을 찾았다. 9/14 `187660`의 paired trace `analyze_target:187660:1789345103399:1c371c0a`는 자연 attempt `aims-09537e63c28235bd65f7`의 명시적 AI trace alias다. 9/15 `417200`의 paired trace `analyze_target:417200:1789447024094:fbbbc9c0` 역시 자연 attempt `aims-fa0353c534f508292be3`와 같은 명시적 AI trace다(전체 ID는 exact-disposition receipt). 시간 근접 대사가 아니다. paired가 자연 기계 관측과 이중 집계되던 결함을 수리했다. 자연 관측을 보존하고 paired alias 제외 수를 모집단 대사에 남기며, 서로 다른 보유 경로의 SELL/AI 결과는 옮기지 않는다. 관련 308개 회귀 통과. 이미 계산된 9개 full-cost paired 행은 원 source identity/hash를 대사해 후속 재계산에 재사용하며 가격 raw를 다시 읽지 않는다.

## 9/20 17시 후속 종결

**지원 범위의 원천 생성·저장·경제성 계산·선정·소비 구현과 회귀는 완료했다. 자연 경제성 입증 및 아래 미지원 운영 범위의 확대는 완료가 아니다.** 기존 summary는 과거 원천이 현재 producer를 입증하지 못하는 상황을 계속 source gap으로 표시한다. 이를 PASS나 자연 성과로 바꾸지 않았다.

| 항목 | 코드·회귀 결과 | 남은 증거/범위 |
|---|---|---|
| ME8 원천/분모 | BLOCK/RECHECK 관측, 기존 bounded 계좌 읽기, plan/stop/cost/reserve 저장과 parser 연결, 명시적 AI trace alias 제거 완료 | 과거 8행은 고유 6판단. 당시 frozen operating plan의 복구는 검토 원천에서 입증되지 않음. 현재 계좌나 실제 SELL로 보충하지 않음 |
| ME9 독립 실행 경제성 | 기존 owner의 독립 CF arm, 비노출, 반복 RECHECK/실제 TTL 종료, 동일 frozen 승인 수량·예산 계산 완료 | 최초 BLOCK에서 호출되지 않은 AI의 판정, 미확정 cancel/late-fill·부분 체결·미청산은 미지원/결손이며 0원 완료로 만들지 않음 |
| ME10 자본·scope | 동일 promotion 중복, 동시 reserve/보유 종목, 손실 후 현금, base/stress 자본 충돌, frozen 전체 scope 조합 검증 완료 | 계좌 한도 변경·외부 현금흐름, 재평가 중 수량 변경, FIFO 의존 CF는 고정 자본 v1 범위 밖. 시간 경과만으로 해소되지 않음 |
| ME11 선정 | 비용 차감 operating EV·일별 순익·tail·노출·참여율·실측 오차 하한, calibration freeze와 독립 model/candidate holdout, publisher 지표 일치 완료 | 신규 자연 모델 검증 표본 및 동결 이후 후보 holdout 필요. 10bp·sample·tail 기준 유지 |
| ME12 소비 | dated bundle→summary/checklist→main/compact verifier→strict seal/controller 및 reader/fallback 검증 완료 | 9/21 정상 PREOPEN·메인/위젯/에피소드 실제 PID 소비는 아직 실행하지 않음 |
| ME13 리뷰/검증 | producer→저장/projection→계산, 지원/차단 입력, hash/date/scope/holdout 실패, alias/census 회귀 완료 | 합성 회귀는 자연 성과가 아님 |
| 적용 후 성과 | 기존 machine+compact 적용 버전/episode 중복 제거·20 source-day rolling/cumulative 완료 손익 경로 연결 | `waiting_natural_applied_completed_cost_evidence`, groups0. 모델 ΔEV·실제 순익·인과적 개선은 별개 |

자연 재평가 결과:

- KRX 모집단 1,715→1,712(자연1,708+paired4). 명시적 alias3개를 제거했으며 나머지 source/cohort/cost 제외 수는 이전 계산과 동일함을 assertion으로 확인했다. 변경8건 중 alias는2건이므로 고유 변경은6건이다.
- 등록9 scope를 모두 처분했다. main 신규 승격 후보0, 상태 `source_gap`, blocker `machine_operating_population_unbound`, 운영 ΔEV·일별 순익 null. 이는 valid no-edge 측정이 아니다.
- 자연 compact21건은 손절 결손10, 전송 계약 실패8, 원천/세션 결속 실패2, 응답 의미 실패1. 운영 모델 실제 비교0. 추가 AI 호출 없이 재평가했고 `blocked_source/source_gap`으로 incumbent를 유지했다.
- 9/17 원천을 실제 9/20에 발행하여 9/21용 policy를 준비했다. main/전체 scope 및 compact 정책 본문은 이전 승인 incumbent와 동일하다. 신규 양수 정책·실제 증분 이익은 입증되지 않았다.

검증 및 실행 증거:

- 코드 커밋·push: `beb0c1578`(주 구현), `f339f47bb`(부적격 원천 사전 필터), `e89e9da12`(명시적 alias 중복 수리). 최종 source release는 `main-machine-operating-completion-20260920-e89e9da12`.
- 영향 범위843개, WATCHING owner2개 통과 이후 추가 수리의 관련308개 회귀 통과. 중복되는 suite이므로 합산하지 않는다. Python compile, print-only 문서 parser, diff check 통과. 마지막 로그 `alias-review-tests.log`.
- 자연 관측2,330건은 기존 loader AST와 원천 stat을 대사한 materialization을 사용했다. 최초 bounded 재라벨링은 지원212행/7 source-day에 한정했다. alias 후행은 계산된 full-cost9행의 source identity/원천을 대사해 재사용했으며 raw 재스캔0이었다.
- main→compact 평가/발행→summary→checklist→main/compact scoped→preterminal strict→seal→controller를 실행했다. 후행10개 명령 exit0, 독립 widget/machine producer receipt 유효, 재사용한12개 독립 owner 산출물 hash 불변. 전체 A–H·cleanup·detector는 반복하지 않았다. 기존 cleanup/final detector는 15:26:54의 별도 원 실행 증거다.
- 서비스9개 정의/129개 인스턴스의 source binding을 successor로 교체했고 최종에도 모두 inactive/PID0. 기존 시각·주문 인자·수량·guard 불변. 봇 시작/재시작, 주문, 조기 PREOPEN, 외부 sync/알림을 실행하지 않았다.

최종 run `402279f6cf954c7ab00676635c93f6bc`: main terminal `succeeded`, controller `done`, strict `pass`.

- main 평가 hash: `193b8979aa4450c3e5ccbce9f0a5240d61c8ea2224431f2918cece1f88ded1e4`.
- 9/21 bundle hash: `5913223d115fd25b0ac5fd14a6b538ffc5d840e67865eb7b9d64fa035ad53020`.
- seal: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-09-17/09fa70013bce40de9077c3958a0cf8f9.json`.
- 최종 strict: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-09-17/b709bdb53f364e52a32479e8e9cffef5.json`.
- 실행·재사용·서비스·정책·자연 결과의 machine-readable 대사: `tmp/main-machine-operating-completion-20260920/final-reconciliation.json`.
- 원 실패/중단/이전 성공 receipt는 보존했다. 이번 native 성공은 원천 복구나 경제적 성공의 대체 증거가 아니다.

남은 자연 OPEN은 새 지원 입력 유입→독립 실제 모델 표본→동결 이후 후보 holdout→정상 PREOPEN/PID 소비→완료 비용 손익이다. 위 표의 미지원 운영 범위는 자연 대기에 섞지 않으며, 확대하려면 별도 검증 가능한 운영 계약이 필요하다. 현재 준비 상태는 **guarded incumbent 기동 준비 완료**, **경제적 개선 실증 미완료**다.


## 10. 조건부 자본·부분 체결 후속 보완 (2026-09-20)

기준: main 계획 §15. 사용자 구현·검증·커밋·push·배포·제한 재생성 승인. 다른 세션의 canonical 작업본과 선택 중 release를 보존하고 `fix/main-machine-capital-partial-20260920`에서 구현했다. 별도 장중 의미적 감시 프로그램은 구현 범위가 아니다.

| 단계 | 이번 보완 | 범위와 남은 사실 |
| --- | --- | --- |
| E0 | e89e9da12 코드/7ffa045ac 문서 및 기존 자연 복구 receipt를 대사 | 기존 수량·guard·candidate grid·holdout·carry 정책 재사용 |
| E1 | 기존 bounded 계좌 관측의 normalized source hash/clock, 계좌 namespace hash, 종목별 수량/cap을 frozen context와 기존 projection에 전달 | 조건부 초기 자본과 후속 승인 cap 분리. 외부 입출금·계좌 결제대금 의미가 확인되지 않은 basis 변화는 미지원 계약 |
| E2 | reserve→보유 전환·확정 취소분 반환·자기 청산 원금/순익, 현금 보존, 취소 전 holding frame 유지 | touch/queue·서로 다른 child ACK·체결 사이 보유 전이·조기 EXIT 취소 모델은 검증된 지원 밖. 실제 SELL 복사0 |
| E3 | 각 RECHECK attempt의 자기 frozen 수량/cap 허용, 후속 실제 AI만 소비 | 미호출 AI를 PASS로 만들지 않으며 추가 AI 호출0 |
| E4 | 동일 초기 자본의 원화 순익/EV, reserve·보유 적분·peak committed capital·체결 참여율, empirical clock/net error의 자본 경계 차단 | 모델/후보 holdout 및 10bp gate 유지. 모델 EV와 실제/인과적 이익 분리 |
| E5 | 부분/no-fill receipt의 seed/hash/quantity와 상태별 실제 model holdout 확인; 기존 publisher/reader/loader 유지 | full-fill 모델만으로 partial을 승격하지 않음. 현재 정책은 자연 증거 평가 후 incumbent/fallback 가능 |
| E6 | 실제 producer의 저장/projection, native→cancel model→holding frame, 부분 수량의 실제 격리 청산 계산, 선정/소비/실패 회귀 | 전체 raw/A–H 반복 대신 main과 필요한 compact·policy·summary·checklist·strict만 재생성 |

구조적으로 달라진 점은 승인 cap 변화를 입금으로 처리하거나 모든 수량 변화를 차단하지 않는 것, 시간 초과만으로 미체결 reserve를 반환하지 않는 것, 부분 체결 상태를 full-fill-only consumer가 항상 제외하지 않는 것이다. 최초 승인 자본에 이미 반영된 외부 기존 보유/예약을 또 차감하지 않는다. 자기 후보의 자본만 이후 시간순으로 계산하며 수익 재투자는 하지 않는다.

검증 제한: 합성 입력의 partial 계산/모델 선정 성공은 자연 표본이나 실제 이익이 아니다. 실제 계좌 전체의 변동 자본 backtest는 **운영 계약 미종결**이고, 미호출 AI와 지원 모델 없는 queue/cancel 상호작용은 **명시적 미지원**이다. 이를 자연 표본 대기나 전체 범위 구현 완료로 표현하지 않는다. 자연 OPEN은 지원 계약을 갖춘 정상 유입·독립 실제 model/candidate holdout·PREOPEN/PID 소비·완료 비용 손익이다.

리뷰 중 공유 interpreter의 테스트가 퇴역 AVG_DOWN report/capture를 다시 요구하는 두 기존 불일치를 확인했다. 퇴역 report integration 테스트를 제거하고 capture가 재활성화되지 않는 회귀로 정리했다. 공용 AI fixture/holding interpreter/격리 효과 guard 검증은 보존했다.

실행 증거 디렉터리: `tmp/main-machine-capital-partial-20260920/`. 최종 테스트·배포·run·policy hash는 후속 검증 후 아래에 기록한다.

검증: 영향 회귀708개 통과 후 누적 금액 정정·terminal 이후 fill 수리의 관련87개 통과(중복 합산하지 않음). Python compile·diff·print-only parser 통과. `implementation-review.json`에 source hash와 검증 로그를 결속했다. 합성 통과와 자연 경제성은 별개다.

### 10.1 배포·제한 재생성 최종 대사

- 코드 commit/push: `5d60b4afee77243da3ad89bc4de9a12da40955a6`. 선택 immutable release: `/home/ubuntu/KORStockScan-runtime-releases/main-machine-capital-partial-20260920-5d60b4afe`. 서비스9개 정의/129개 인스턴스의 source binding을 갱신했으며 최종에도 PID0/inactive다. 기존 시각·수량·guard·주문 인자를 변경하지 않았다.
- source_date=`2026-09-17`, 실제 publication_date=`2026-09-20`, effective_date=`2026-09-21`.
- 복구 run `f7e6be607be944b8a45fa8f5775494a8`: main `succeeded`, controller `done`, strict `pass`. 후행10개 명령 exit0, 독립 widget/machine receipt 유효, 독립 owner12개 artifact hash 불변. 원 실패와 이전 복구 성공 receipt를 보존했다.
- main source hash `80b34ff0c4357742d7e16654e9cff22cb13f35ec12ed2a95577b39612ce97357`. 최종9/21 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7`. main 전체 scope 및 compact AI 정책 본문은 기존 승인 incumbent와 동일하며 provenance만 갱신했다.
- 메인 KRX 유효 모집단1,712(자연1,708+paired4), 등록9 scope를 대사. 신규 승격0, `machine_operating_population_unbound`, 운영 경제성 null. 자연 compact21건도 `blocked_source/source_gap`, valid no-edge 아님. 적용 버전별 완료 손익은 `waiting_natural_applied_completed_cost_evidence`, groups0.
- 자연 관측2,330건과 앞서 검증된 비용9행은 함수 AST·identity·원천 stat/hash를 확인하고 재사용했다. 평가·후행은 successor에서 실행했고 전체 raw 재스캔/전체 장후 재실행/추가 AI 호출/주문/봇 기동/조기 PREOPEN/외부 sync·알림은 0이다.
- strict receipt `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-09-17/f6c8c6e1268942d78d6ef7b6763ac696.json`. seal receipt `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-09-17/1f755f07e67d47d5aa6ddf3e22b6def5.json`.
- 기계적 완료 및 guarded incumbent 준비와 경제성 실증을 분리한다. 이번 코드의 조건부 지원 경로는 실행·검증됐지만 전체 계좌 현금흐름·모든 부분체결 경로의 보편적 지원 완료는 아니다. §15.9의 미확정 운영 계약은 자연 OPEN으로 바꾸지 않았다.

증거: `implementation-review.json`, `deployment-5d60b4afe.json`, `service-binding-5d60b4afe.json`, `source-reuse-code-review.json`, `limited-recovery-f7e6be607be944b8a45fa8f5775494a8.json`, `final-reconciliation.json` (모두 `tmp/main-machine-capital-partial-20260920/`). 최종 증거 문서 commit은 코드 배포 commit과 분리한다.

## 11. 제출병목 한정 감시와 후속 재리뷰 (9/20)

사용자가 의미 감시를 제출병목으로 한정하고 통보를 승인했다. [감시 계획](../proposals/intraday-semantic-entry-monitoring-and-telegram-alert-feasibility-plan-2026-09-20.md)을 현행 범위로 재정의했다. 기존 Sentinel 정규화·machine ledger·Telegram transport를 재사용하고, 최근 원천의 작은 투영/지속 상태/전이 알림만 추가한다. engine root 모듈·새 collector/서비스·AI/브로커 호출은 없다.

리뷰에서 보완한 사항: 대형 진단 JSON을 알림 consumer가 다시 읽는 비용, 프리마켓 수집 제외, 기존 workspace cron의 배포 source 불일치, snapshot 중복·역행, 늦은 terminal과 단순 window 이탈 혼동, 전송 실패 후 성공 상태 기록 위험. cache 정규화의 lossless terminal 보존과 wrapper dry-run의 무통보를 회귀로 확인한다. 정상 guard·RECHECK와 source 결손을 혼합하지 않는다.

메인 §15의 conditional capital envelope, prior cancel model scope/hash/date, native 잔여 미접촉/sequence, cash reserve→holding→확정 cancel/exit 보존, sequence 공통 자본/holdout 경계를 재리뷰했다. 이번 감시는 모델/evaluator/publisher를 변경하지 않는다. 직전 708개 및 최종87개(중복) 검증과 자연 f7e6be607be944b8a45fa8f5775494a8의 경제성 결과는 그대로 재사용할 대상이며 새로운 자연 검증으로 합산하지 않는다. 기존 별도 운영 계약 및 EV null을 이 감시 구현으로 해소했다고 주장하지 않는다.

후속 재리뷰에서 canonical 작업본의 정상 `ai_confirmed_terminal_no_budget` 보완을 확인했다. 실제 producer의 알려진 terminal_reason/source_stage 두 조합과 주문 금지 세 필드가 맞을 때만 final guard로 처리하는 변경을 통합했다. 나머지 canonical 차이는 덮어쓰지 않았다. 영향 회귀 **283개 PASS**, compile·bash -n·문서 parser·diff 검증 PASS. 증거: `tmp/submission-bottleneck-review-20260920/implementation-review.json`, `tests.log`. 합성 회귀이며 실제 Telegram 발송/자연 수익 증거는 아니다.

배포 뒤 최종 인계 리뷰에서 기술 감시의 도입일 계약을 추가 보완했다. 새 submission monitor 산출물은 9/21부터 필수이며 9/17 복구에서 존재를 요구하지 않는다. 설치 전 missing을 새 구조 결함으로 오인하지 않되, 9/21 운영 중 missing/stale/통보 실패는 기존 error detector가 실패로 표시한다. 날짜 경계 회귀를 추가하고 후속 불변 배포본으로 반영한다.


최종 배포/인계: 코드 `8ddbee7e0` → 날짜 도입 경계 보완 `3f67a4ef7` push 완료. 선택 release `submission-bottleneck-reviewed-20260920-3f67a4ef7`; 9개 서비스 정의/129개 인스턴스는 PID0/inactive 유지. Sentinel cron5개를08–19시5분1개로 대체하고 선택 release router 연결을 확인했으며 다른 cron은 byte 비교로 보존했다. Telegram token/destination 존재, 실제 시험 발송0.

source9/17→publication9/20→effective9/21 후속 run `5953a93cf56c4fd39be8280faa8d530c`: summary/checklist/scoped/strict/seal/controller 8개 후행 명령 exit0, main succeeded/controller done/strict pass. 경제성 코드와34개 입력 stat이 동일하여 main 자연 결과는 원 run `f7e6be607be944b8a45fa8f5775494a8`의 code/as-of/hash를 가진 재사용 receipt로 보존했다. 앞선 `a27ccd1fabd94f04bef82bc8bdae02be`에서 compact 정책 finalize도 완료했다. 전체 raw·AI 호출·전체 장후 반복 없음.

9/21 bundle `15c063637359bd4cbd5a567760abecdf6229aee1f44d1e9d6a7cbc2dc7e97eb7`은 incumbent_carried이며 모든 main scope/compact policy body를 보존한다. 자연 main 모집단1,712·compact21, 승격0, 운영 EV/추가 실제 순익 null, main first blocker `machine_operating_population_unbound`. 기존 과거 결손/별도 미지원 운영 계약을 제거하거나 자연 대기로 이름만 바꾸지 않았다. 정상 PREOPEN/PID·장중 실제 incident 통보·독립 표본/COMPLETED 비용 손익은 OPEN이다.

증거: `tmp/submission-bottleneck-review-20260920/`의 최초283개 회귀·정책 finalize·cron 설치 receipt, `tmp/submission-bottleneck-final-review-20260920/`의 날짜 경계71개 회귀(중복), `final-review.json`, `final-reconciliation.json`, `source-reuse-code-review.json`, `service-binding-3f67a4ef7.json`, `limited-recovery-5953a93cf56c4fd39be8280faa8d530c.json`. 배포와 상태 인계는 경제적 개선 증거가 아니다.
