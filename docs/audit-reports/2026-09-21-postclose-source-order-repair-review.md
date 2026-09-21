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
