# 2026-09-21 postclose source order repair review

## 범위와 원인

사용자 요청: collector label 순서 경합, widget 352종목 자료 부족, machine refresh 반복 실패를 수리하고 source2026-09-21로 재실행한다. 매매 정책/주문/봇은 이번 수리 대상이 아니다.

- 메인 기계판정 `machine_policy_2026-09-17.json`의 candidate가 오늘 current bundle `1c5c13ed...`로 적용됐다. 별도 widget/episode `machine_microstructure_policy_approval` queue0을 메인 후보0으로 설명한 것은 오류다. 기계정책은 AI replay 없이 승률→평균 순익 순서로 선택한다. holdout5기회, 승률60%, 평균−0.40682%; 현재 report는 같은 holdout에서 frozen candidate를 재평가한 것이므로 evaluated_candidate_count0이 후보 부재를 뜻하지 않는다.
- 21:15 machine 서비스가 main label/episode/summary 완성 전에 시작했다. source wait900초 만료 뒤에도 attribution/timing/approval/builder를 계속 실행하고 builder1이 source42를 가려 전체를 반복했다.
- main은22:36 episode `joint_cohort_member_pruned_without_supersession` 예외로 실패했다. 이후에 있는 label producer는 실행되지 않았다. 공동 후보 명단 검증은 allocation 차단으로 남기되 독립 보고서 생성 자체를 중단시키지 않도록 한다.
- Widget evaluator의 기존 날짜 제외 계약과 loader의 모든75일 필수 계약이 불일치했다. 불완전 fetched day를 메모리에서 PASS 취급하여 실제 저장하지 않은 snapshot을 lstat하는 결함도 있었다.

## 변경과 검증

- 기존 postclose_summary_handoff에 exact-date 입력 barrier 추가. widget 성공 receipt, main 실행 여부, label/episode/summary 날짜를 점검한다. 각 producer의 상세 schema/hash 검증은 유지한다. main 성공만 기다리는 순환 의존은 만들지 않는다.
- Machine 선행 대기12시간, 전체 timeout16시간. systemd Restart=no. collector 실패 시 후단 중단.
- Widget의 실제 검증/저장된 날짜만 평가하고 결손 날짜 명시. 기존300분봉/양수거래량90%/장개폐장 커버, 결손 있는 경우25일 이상 등 기존 품질·holdout 기준 유지. 기본 원격 backfill10종목, 나머지 retained source 평가. 이번 복구는 retained-only로 추가 API 호출 없이 수행한다.
- 공동 명단 검증 실패는 allocation_blocked/EV null로 발행한다. frozen manifest를 바꾸거나 부적격 후보를 승격하지 않는다.
- 신규 운영 모듈/서비스를 만들지 않고 기존 owner를 수정한다. 기존 사용자 dirty 파일은 보존한다.

## Official Kiwoom reference

2026-09-21 KST 조회 upstream main `953e5dbff123f437ab4d11a78a95191a685eb51f`. `kiwoom_docs`는 tree에 없음. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json` ka10080, Postman PRD/MOCK ka10080 대사. POST /api/dostk/chart, stock suffix/1분/signed KRW/volume shares/continuation을 확인했다. 기존 요청·응답 parser·인증·연속조회는 수정하지 않고 저장 자료의 유효 날짜 소비와 호출 종목 수를 제한한다. 검토 원문은 tmp/postclose-source-repair-reference에 보존.

## 실행 증거

수리 후 관련 pytest173개 통과, Python compile/bash -n/diff --check 및 print-only checklist parser 통과. Prefix 재사용 허용 경로는 advisory/auto-policy가 소비하지 않는 공동 연구 모듈에 한정하여 보완했다. immutable release 재실행 결과는 아래에 기록한다. 기존 main 실패·과거 recovery 이력은 보존한다.

### 재실행과 후행 보완

- `a13afa1f5` immutable release 자체에서 관련164 tests PASS. 공통 cron router와 widget/machine 기존 systemd source pin을 새 release로 연결했다. 실행 중 매매 봇은 이전 release 그대로이며 새로운 PID 소비로 표시하지 않았다.
- 22:58:57 label 원 producer 성공. 22건(partial18/pending4), source input validator issues0. 23:00:57 collector 추천 재생성 성공, qualified/reported7건, 아직 미등록6건, notification 미실행. 추천은 메인 기계정책 승격과 별개이다.
- Widget 기존 완료 prefix를 보존하고 retained-only signal 연구 재실행. 475150 등 하루/일부 날짜 결손 종목이 기존 일별 품질 계약으로 평가됨을 확인했다. 전체355 분모 유지, 실제 완료·제외 수는 terminal 후 확정한다.
- Main의 실패 원인과 같은 공동 명단 예외가 후행 `freeze_joint_bundle`에도 남아 있어 refresh에서 진단으로 기록하고 기존 canonical allocation gate로 재구성하도록 보완한다. publisher가 gate를 재계산했을 때 일치해야 한다는 회귀 검증을 포함한다.
- 복구 worker만 4CPU/가용메모리4GB 확인 후 CPUQuota80%로 제한하였다. 정규 서비스 자원 한도는 변경하지 않았다.

후행 보완 검증: 공동 manifest 실패를 포함한 실제 publish/reuse 회귀4개, 관련 closed-loop/completion/handoff126 tests PASS. 원 gate와 publisher 재구성 gate 불일치가 없음을 확인했다.


### 전수 report 저장 한도 후속

Episode 복구는23:09:19에 공동 명단 검증 단계를 통과했으나 `low_price_research_report_size_exceeds_contract`로 중단됐다. 전수 결과를 삭제/축약하지 않고 생산자와 generation-stable reader가 공유하는 한도를128MiB→256MiB로 확장했다. 초과 오류에 실제 bytes/limit를 출력한다. 자동 정책·closure·runtime summary가 이 native reader를 소비함을 확인하고 writer/reader/크기 초과/계약/completion143 tests PASS. 재실행은 원 source9/21과 publication9/21/effective9/22를 유지한다. 전체 main wrapper는22:36 failed 이력을 유지하며, 독립 source 복구를 main DONE으로 바꾸지 않는다.


### 사용자 지정 연구 범위 축소

후속 사용자 지시에 따라 위젯100종목, 에피소드 신규50종목으로 변경한다. 위의256MiB 한도 증액은 배포하지 않았으며 이번 변경에서128MiB로 복원한다. 에피소드 신규320종목×5시간대와 기존 시간대/로직95프로필이 합쳐져1695프로필로 확대되었고, 각 프로필의 후보·baseline·holdout 상세 결과 중복이 JSON 저장량을 키웠다. 신규50종목이면250+95=345프로필 수준으로 줄어든다. 기존 운영 종목은 유지한다.

공유 선정 함수는 기존 연구 lifecycle owner에 추가한다. 완료 추천 순위와 사전 자료 유무로 선정하고 평가 중인 손익을 사용하지 않는다. 전체 catalog/동결 manifest는 삭제하지 않으며 자원상 이월과 소스 부족/경제성 탈락을 구분한다. source waiting의 context와 episode candidate fingerprint에 선택된 명단이 반영되어 전수355/320 캐시를 축소된 분모로 오인 재사용하지 않는다. 위젯 기존 운영/명시 watch가100을 초과하면 조용히 누락시키지 않고 명시 오류로 중단한다.

검증: 위젯/에피소드/runtime policy/handoff206 tests PASS, compile/diff/parser PASS. 선정 단계에서 기존 운영 종목의 처리 순서까지 바뀌던 결함을 회귀 테스트로 발견하여 보존하도록 수정했다. 완료 advisory/auto-policy prefix는 연구 lifecycle/closure refresh를 소비하지 않아 source hash 검증 후 재사용하며, signal/episode 경제성 평가는 새 선택 명단으로 검증한다.

축소 release 자체206 tests PASS, cron routing4/4 확인 후 episode50 재실행 시작. 위젯 중단 receipt가 started 상태이면 top-level sources 없이 reused_prefix.sources만 보존되는 재개 결함을 확인했다. native 재개에서 해당 증거를 동일 날짜/해시 검증 후 읽도록 보완하고 중단 후 재재개 회귀를 추가했다. 자료 검증을 생략하거나 prefix를 재작성하지 않는다.


### 내일 기동 준비를 위한 지속 복구

사용자 지시에 따라9/21 source→publication9/21→effective9/22를 고정하고 main/독립 연구/후행 monitoring/최종 closure를 끝까지 복구한다. 계산 대상 추가 축소가 필요하면 기존 운영 종목을 보존하고 사전 데이터 커버리지·완료 추천·이미 검증된 학습 성과를 우선한다. 평가할 holdout 결과로 사전 대상을 고르지 않는다.

- 검증된 b195524bc에서 main wrapper 재개, bot action none, notification false. 기존 거래 프로세스는 유지한다. 구 release 대기 보고서 세션을 종료하고 새 release monitoring owner로 연결한다. 최종 controller는 독립 terminal 이후 실행한다.
- 비용 source prerequisite가 상대 data root를 manifest 경로에 두 번 결합하여 종목 master/fee/tax 파일을 결손 처리하던 오류를 확인했다. helper에서 root를 resolve하고 상대/절대 경로 회귀4개 PASS. 기존 immutable CLI에 절대 data root를 전달한 원 producer 재생성으로 master2604·비용 profile6·eligible7812/7812·source blockers0을 확인했다. 가격·비용을 임의 대체하지 않았다.
- 에피소드50 복구 정상 종료. report46,798,188bytes로128MiB 이내이며 신규/시간대/로직 추천0건이다. 신규 추천 없음과 기존 운영 정책 승계·내일 loader 검증은 별개로 진행한다.

- Widget 최종98평가/2source격리(001550,450080),9/22 observation98 로더 PASS. 기존 widget 자동매매3종목과 episode19종목61프로필 및 main승계정책은9/22 실제 loader 읽기 성공. 신규 research승격0은 기존 전략 중지를 뜻하지 않는다.
- 첫 main복구는23:52 final raw projection mismatch로 실패했다. 기존 봇 supervisor가23:51 재기동하면서 장후 preflight 이후 raw에 scanner configuration1행(5796bytes)을 추가했다. 따라서 검증 차단은 정당했다. 다음 복구는 표준 main BOT_ACTION=stop으로 기존 야간 tmux세션을 종료하여 원본과 정규 아침 기동을 안정화했다. 별도 주문·보유 정산 변경은 없다. 이번 복구에서 이미 성공한 sim post-sell/rising-missed 보조 피드백만 invocation flag로 재실행하지 않는다. 기존 보고서는 보존하고 필수 원천 감사·정책 생성은 재수행한다.
- Machine 분석/closure/policy는 모두rc0, 마지막 builder만 stale direct summary로rc1. 정확 원인은 effective_dates=[]인데 fallback 당일 bootstrap PID를 actual_pid_consumed=true로 붙이던 summary 결함이다. PID 생존 여부만의 문제가 아니다. 효과일·manifest·검증 날짜가 일치한 bootstrap에서만 PID 소비를 인정하도록 수정하고, machine wrapper도 summary→checklist 순서로 갱신한다. 관련95 tests PASS.
- 자정 이후 source/publication9/21와effective9/22를 유지한다.9/22 체크리스트는 아직 없으며 native builder에서 최신 owner로 생성할 예정이다.

### 자정 경계 복구 보완 (2026-09-22)

- 00:02 main 재시도에서 `research_same_date_publication_conflict`: effective date가 달력상 당일이 되어 전일 장후 발행 갱신을 거부했다. 명시적 publication date, 다음 거래일, 07:30 이전, bootstrap 부재를 모두 만족할 때만 CAS 재발행을 허용한다.
- 이전 machine은 연구 발행 후 checklist 생성에서 실패했다. 후속 main 연구 재생성/코드 수리로 전체 closure가 오래되어 widget 입력 대기에서 교착됐다. 이전 서명 receipt, 동일 widget terminal, 현재 widget 연구 semantic hash와 immutable 발행 세대를 검증한 경우 재구축만 허용한다. 최종 성공 게이트는 완전한 current receipt를 유지한다.
- 코드 리뷰에서 누락된 date import를 보완했다. 경계시간/장전 준비 존재/잘못된 날짜/보고서 및 발행 변조 회귀 검증 포함.

- 야간 발행/재개 회귀: 작업본91건, 사용자 별도 변경을 제외한 immutable release82건 PASS. release6978f7ca0에서 00:13 에피소드 CAS 발행 성공, 후속 main 평가 진행. 실제 서비스 reader도 widget3종목4세션, episode19종목61프로필과 청산 전용 확장3프로필을 읽었다.
- 정규 machine wrapper가 publication 환경을 기본 설정하지 않던 경로를 보완하여 입력 대기 이전 completed-source/next-trading-date를 고정했다. wrapper17건 및 bash 문법 PASS.
