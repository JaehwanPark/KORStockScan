# 2026-09-07 위젯·에피소드 추천 구현과 9/8 적용 검토

사용자 지시: “결함보완하고 코드리뷰, 결함없을때까지 반복, 위젯 에피소드 추천 구현 및 내일 적용”. Source date는 2026-09-07, 적용일은 자정 이후에도 2026-09-08로 고정한다. 본 기록은 이전 장후 복구 완료 기록과 별도의 사용자 승인 구현 pass다.

## 판정

코드 검토·검증 및 9/8 policy publish와 timer 설치를 완료했다. 현재 검토 범위 unresolved P0~P2 finding 0, targeted pytest 399 passed, Python compile/shell syntax/git diff --check 통과. 실제 장중 체결·순이익은 아직 검증하지 않았다.

- 위젯 제주반도체(080220): 기존 holdout 통과 추천의 9/8 exact-date policy와 loader 검증 완료. 자정 이후 기존 PID 9704의 `widget_signal_auto_trade_state.json`에서 해당 9/8 policy ID를 확인했다. 날짜 경계의 기존 dynamic catalog 갱신 경로가 소비하므로 재기동은 필요 없다. Collector는 08:57 예약이다.
- 에피소드: 추천 13건 중 기존 preflight를 통과한 11건(기존 profile 수정 8, 신규 시간대 3)을 구현했다. 총 inventory 53→56, 기존 제외 3 유지, runtime eligible 50→53. 주문은 계속 10주씩 두 leg/최대20주이며 기존 custody는 진입 당시 정책과 target을 유지한다.
- 신규 시간대: TYM 오전(09:10~09:59), NHN 정오(13:30~13:49), 에스디바이오센서 오후(14:15~14:40). 각각 preflight/기동 타이머 09:05/09:09, 13:25/13:29, 14:10/14:14. 기존 template service 및 exact-date preflight를 사용한다.
- 기존 수정 8: NHN 오전, 영원무역 오후, 두산에너빌리티 오전후반, CJ CGV 오전후반·정오, 팬오션 오전후반, SK텔레콤 오전후반, 한세실업 오전. 팬오션 신규 episode target은 추천의 2→4 tick 변경을 포함한다. 기존 보유분 target은 바꾸지 않는다.
- 보류: 영원무역 오전후반은 calibration 후반 EV 음수, 두산에너빌리티 정오는 전반 EV 음수. 기존 경제성 guard를 통과하지 못해 profile을 추가하지 않았다. 기존 CJ CGV 오전·영원무역 정오·SK텔레콤 정오 격리도 유지한다.
- 위젯 확대 7건은 모두 `research_watch`, `implementation_review_ready=false`이므로 실전 등록하지 않았다. 위젯 signal 후보 4건 중 080220만 통과하고 006800/010140/475150은 보류한다.
- Samsung 독립 시간대 기계의 당일 산출물은 observation-only다. Machine timing은 기존 source-date quarantine과 immediate-entry baseline 유지이며 신규 micro confirmation 후보가 없다. 이 관측을 profile/target 변경 지시로 전환하지 않았다.

## 결함 보완과 검증

추천 producer에 stable `recommendation_id`, scope/axis, 별도 proposal hash, intended consumer와 acceptance를 추가했다. ID는 실행 권한을 부여하지 않는다. Episode의 authoritative 추천과 lane/당일 attribution/고정관측 mirror에도 동일 ID를 결속하여 JSON 재독해 뒤 notifier 계약이 끊기지 않게 했다. 기존 recommendation decision, 표본, EV와 source date/hash는 그대로 보존했다.

날짜별 profile/baseline/bounds/transition 및 preflight의 v7 승인 근거를 연결했다. 9/7까지의 53개 inventory는 snapshot으로 보존하고 9/8부터 56개를 사용한다. 기존 데이터 경계 테스트도 대상일 inventory를 읽도록 수정했다. Source report hash, 65거래일 clean-baseline 근거, 두 calibration half, holdout/full EV와 0.23% 현재 비교비용 재검증을 통과해야 한다. 잘못된 날짜/근거 hash/음수 calibration half를 승인으로 바꾸지 않는 회귀 검증을 포함한다.

직접 consumer 검토: profile lookup → PREOPEN apply → preflight → 기존 service/ledger custody, widget loader → 날짜 경계 catalog → 기존 owner guards, recommendation mirror → notifier validator. Python 검증 399 passed는 기존 held original-target 보호, 부분체결 terminal, 주문 owner, widget 날짜 경계 수신 회귀를 포함한다. 로그: `tmp/widget_episode_apply_20260908/tests_final.log`.

## Intake와 Pass 2

[원장](./2026-09-07-widget-episode-recommendation-ledger.json)은 widget 11 + episode 15 = 26행이다. 최종 분류는 implemented_pass1 11, already_implemented_verified 2(위젯 080220·동일 두산 axis의 당일 중복 추천), observed_no_patch 8, deferred 5다. ID 유일성과 전수 보존을 확인했고 미분류 0이다. 삼성 observation, low-price 실제성과, machine timing 및 approval followup의 비추천 상태도 scope inventory에 명시했다.

각 producer의 `attach_recommendation_contract`를 같은 frozen source에 적용하고 JSON deepcopy 뒤 Pass 2를 반복했다. ID/proposal/decision 변경 0, 새로운 eligible 구현 0이다. 이 산출물은 native metadata projection이며 market replay나 새로운 경제성 generation이 아니다. 기존 장후 canonical 보고서와 그 hash를 교체하지 않아 terminal controller/finalization 재실행은 필요 없다. `machine_lifecycle_turnover_policy_research_v1`의 복원 불가능한 당일 source 손실은 기존 다음 exact-date 관찰 owner가 유지하며 구현 완료로 세지 않는다.

승인 근거: [11개 profile immutable evidence](./2026-09-07-low-price-recommendation-apply-evidence.json). Canonical SHA256 `557d58771956bca4e0649feda1482e8faf0c6730efdc5e88549e3399bd2e8bc5`. Source report 원본 byte SHA256 `6cb5b2293dbf01bdb9ed4c8c3bc1816ad7d1f5a5834972f92c5c7db27b4c3178`, canonical SHA256 `2ef00c2cec2520458396361b86847321f2bd39172dacd475818e64960e63425b`.

## 적용 receipt와 다음 acceptance

적용 상태: `candidate_validated_profile_revision_applied`, policy hash `a4d3741f97b1c538eba106bb5cbd7cd45c192cc5d89d0a3eec59a9344287fb01`. 기존 mutex 안에서 정식 apply CLI로 생성했고 validator와 11개 profile loader/research gate를 다시 통과했다. 신규 타이머 6개 installed hash 일치·enabled/active·9/8 예약, 승인 profile 전체 타이머 22개의 다음 예정일도 9/8을 확인했다. 매매 service를 시작하거나 재기동하지 않았고 주문·취소를 호출하지 않았다. 상세 [적용 receipt](./2026-09-08-widget-episode-application-receipt.json)에서 위젯 PID/정책과 각 에피소드 service/timer 상태를 확인할 수 있다.

9/8 natural preflight/PID/신호·주문·terminal 귀속은 [당일 체크리스트](../checklists/2026-09-08-stage2-todo-checklist.md)의 `WidgetEpisodeRecommendationApplyAcceptance0908`이 소유한다. 코드 및 applied artifact 완료와 실제 경제적 효과를 분리한다. Rollback은 exact-date preflight/hash/source 실패 시 해당 신규 진입 fail-closed이며, 명시적 재검토 후 다음 PREOPEN에 이전 profile revision을 재선택한다. 이미 보유한 수량·target 주문은 원 owner와 당시 정책을 유지한다. 자동 강제청산/guard 완화는 없다.
