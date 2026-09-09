# 적응형 청산 전체 scope 보완·재리뷰

기준: `2026-09-09 KST`. 판정: **전체 scope 공통 연구/driver 확장, 전체 계획 구현과 실거래 자동 적용은 아직 미완료**.

최신 재개 결과는 **§7**을 우선한다. §6에서 자연 source/grid를 연결했고, §7에서 실제5개 gateway의 registry-bound SELL transport를 확장했다. owner loop/driver port의 실제 조합·복구/생존성·승인 envelope/PREOPEN는 여전히 미완료다. 아래 §1~§5의 자연 producer 미완료·14:42 실패 판정은 이전 시점 이력이며 현재 blocker로 재사용하지 않는다.

사용자 지시는 전체 종목·프로필 구현과 반복 리뷰이며, 추가 답변은 “후보 자동 산출, 승인된 범위에서만 자동 적용”이다. 종목 하나를 먼저 고르라는 구현 제한을 두지 않는다. 실거래 위험 수치·기존 보유 이관·프로세스 재기동은 이 답변에서 승인되지 않았다. [상세계획](../proposals/widget-episode-adaptive-exit-implementation-plan-2026-09-09.md)과 [이전 부분 구현](2026-09-09-widget-episode-adaptive-exit-implementation-review.md)을 잇는다.

## 1. 실제 변경 (최초 전체-scope 확장 시점)

| 영역 | 변경 | 현재 한계 |
| --- | --- | --- |
| 전체 scope | `adaptive_exit/source.py`가 owner/profile/symbol/route/session 전체 catalog를 구성, 표본 없는 scope도 보존 | source9/8 catalog는 연구/확대 후보도 포함; 실가동 집합 아님 |
| 최초 체결 시계 | widget engine, 공통 two-leg 및 override가 있는 Samsung 오전에 `adaptive_exit_first_fill_observation` 추가 | reconciliation 관측시각이지 거래소 체결시각 아님; 기존 보유 시각 합성 금지 |
| 세 모드 | 시간/진행률, 명시 lot trailing, 결합. 비선택 lot·unsupported target geometry 분리 | 실제 owner별 runner/부분취소 adapter 미구현 |
| execution replay | cancel/submit latency, queue confirmation, depth participation, TTL, 부분체결·잔량·retry, base/stress | modeled CF; 실제 broker 체결 품질 승인 아님 |
| 경제성 | whole-lot census, episode 집계, chronological purge/holdout, 비용 후 절대 EV·동일 집합 순익·p10, 수익 빈도·완료시간·자본점유 | 자연 lot/path 생산 미완료; day-cluster 진단이지 통계적 신뢰구간 검증 완료 아님 |
| 후보/달성성 | 고정 parameter grid 전수 평가, native recommendation ID와 policy/evidence hash, 0유입일·rolling expiry·명시 capacity 기준 조건부 ETA | 연구 `research_ready/hold_evidence`만; 현재 PREOPEN eligible false |
| 공통 주문 driver | durable-before-effect, ACK/terminal 구별, cancel race, per-order 누적 fill, 잔량 epoch 재결속, bounded sell TTL/retry, ambiguous reservation 보존 | `OwnerExitPort` Protocol과 fake port 회귀이며 실제 gateway adapter가 아님 |
| 장후 연결 | 기존 attribution의 `rolling_policy_research_v2.all_scope_study` 및 Markdown | optional typed census/config reader만 연결; 해당 자연 input producer·승인 dispatch/PREOPEN는 미완료 |

신규 파일은 `src/trading/order/adaptive_exit`, `src/trading/config`, `src/engine/monitoring` 및 `src/tests` 역할 package에 두었다. 새 engine-root module, cron/daemon, API 호출 증가, package 설치는 없다. 기존 entry/수량/목표주문/legacy custody 계약은 보존한다.

실제 owner 코드 변경은 **추가 관측 필드**뿐이다. 매도 전환 driver를 실거래 loop에 붙이지 않았으며 runtime env·policy·PID/서비스·주문은 변경하지 않았다. Kiwoom request/parser/FID/취소 프로토콜 수정은 없다. 공식 reference 탐색 시 upstream SHA `234560d213acd8871ae344b5481aecd2f30287fa`(조회 `2026-09-09T04:47:10Z`)의 specs/core/spec JSON/Postman을 확인했지만, 현재 tree의 `kiwoom_docs` 부재와 실제 SELL adapter semantics 검증을 포함한 전체 protocol gate 완료를 주장하지 않는다.

## 2. 자연 근거와 기대효과

기존 `data/report/machine_microstructure_attribution/machine_microstructure_attribution_2026-09-08.json`을 읽기 전용·메모리 내에서 대사했다. byte SHA256은 `0b15809fc5665c2bcbd22f6eefa74a90041fc8915d0b6d90b8e71c46ef5a2012`이며 원본은 재생성하지 않았다.

- catalog 155 scope = widget 19 + episode 136, catalog exclusion 0. 반복 route/session 연구 축을 포함하며 현재 등록 low-price 56개나 실제 PID 수와 다른 분모다.
- 기존 anchor 고유 lifecycle 30은 유지한다. 신규 whole-owner lot census와 ordered post-target path가 없어 자연 경제성 candidate 0, 모든 scope는 `blocked_missing_evidence`다.
- 이는 시간이 지나면 저절로 해소되는 shortage가 아니다. **자연 input producer 미완료**를 표본 부족과 별도로 기록한다. 새 계측 코드가 실제 PID에서 호출됐다는 receipt도 아직 확인하지 않았다.
- 예상 기전은 느린·약한 보유의 자본점유/손실 확대 감소와 빠른 접근 runner의 상승 참여다. 반등 직전 조기매도, 취소 경합, 추가 비용·미체결의 역효과도 있으므로 현재 순익 개선을 입증했다고 보고하지 않는다.
- 동일 episode 집합의 비용 후 순익/EV를 주 지표로, 순익 양수 episode/전체 관측 거래일·terminal 시간·자본 KRW-minute를 보조 지표로 계산한다. unresolved를 0수익으로 넣지 않고 미완료 분모를 표시한다. 회전 지표를 새 고정 live floor로 추가하지 않았다.

기존 target을 일찍 맞춘 baseline에만 짧은 원천을 허용하면 느린 보유가 비교에서 사라진다. 두 arm 모두 같은 전구간을 요구하고, 명시한 공통 horizon의 cancellation/submit latency를 거친 평가용 종료를 사용한다. 이 종료는 실전 baseline에 시간청산을 추가한 것이 아니며, horizon 잔량은 censored/null이다.

## 3. 리뷰 중 수정한 결함

1. active scope 목록을 anchor가 있는 종목만으로 축소하지 않도록 전체 catalog와 유효 표본을 분리했다. 잘못된 catalog row는 격리한다.
2. 두 leg를 독립 표본으로 세거나 미완료/누락 leg를 0원으로 합산하지 않는다. 같은 episode의 cost/entry policy, source/order identity를 검증한다.
3. 최초 체결 관측시각의 부분체결/재시작 갱신, 기존 보유에 새 first clock 부여, 시각/수량 회귀를 막았다. Samsung 오전의 override 경로도 별도로 연결했다.
4. 지정하지 않은 lot까지 trailing하는 경로를 막고 runner lot을 명시하도록 했다. 전량 runner·runner 없음·여러 lot의 합산 target은 미지원 geometry로 제외하고 원래 분모에 남긴다.
5. 취소 도중 target fill, durable intent 후 crash 시 이미 terminal인 target, SELL ACK/실제 fill 구별과 주문별 cumulative fill reset을 보완했다. 세 번째 SELL이 첫 번째 주문번호를 재사용하는 경우도 history로 차단한다. exact proof 없는 잔량 해제·blind 재제출은 없다.
6. max-unprotected 알림이 정상 계산 단계에서 지워지던 경로를 보완했다. manager 유지와 무권한 강제매도는 별개다.
7. 공통 horizon 취소가 target ACK 전에 시작하지 않도록 했다. 종가/고가 touch나 VWAP를 체결 가능한 전량 limit으로 대체하지 않는다.
8. source calendar의 중간 무유입 거래일 생략을 차단했다. ETA window를 관측된 짧은 기간으로 추정하지 않고 외부에 선언된 rolling horizon이 없으면 근거 대기로 둔다. 후보가 floor/window를 낮추지 않는다.
9. source census의 `complete=true`만 믿지 않고 episode/lot 형태·중복·path 포함관계를 검증한다. lot path가 없는 최초 결손을 평가 계약 결손으로 덮지 않는다.
10. Samsung 정오/오후 회귀가 운영 정책·registry를 읽어 충돌하던 fixture를 임시 policy/registry/account 및 source-only writer로 격리했다. 확인한 14:00 이후 운영 registry에는 과거일·테스트형 B/C/T 주문의 신규 행0이며 운영 registry를 수정/정리하지 않았다.

## 4. 승인 조건·자동화 최종 판정

신규 연구는 relative 1% uplift, 5/10/20일 동시 양수, 모든 조기매도 양수, 첫 활성화 전 새 exit 실체결을 요구하지 않는다. primary 비용 후 **절대 증분과 같은 집합 순익**, holdout 비훼손, tail/coverage와 명시한 floor를 사용한다. 기존 v1 gate는 이 변경으로 우회하지 않는다.

전체 source/grid에 대한 후보 산출 함수와 기존 장후 child 연결은 구현됐으나 **자연 입력 생성부터 자동 적용까지의 완성 체인은 아니다**. 다음은 서로 다른 상태다.

| 단계 | 판정 |
| --- | --- |
| typed source + frozen grid → replay/evidence/native candidate | fixture E2E 검증 |
| 자연 first-fill 관측 → 전체 lot/path census | 계측 코드 추가, 전체 producer/consumer 미완료 |
| 경제성 후보 → 승인 envelope 검사/dispatch | 미구현; numerical envelope 미승인과 구분 |
| PREOPEN atomic publish → frozen episode policy → 실제 owner port | 미구현/미연결 |
| 현재 PID의 target 취소·조기매도·trailing | 미적용, 기존 target 유지 |
| 비용 후 작은 수익 빈도/누적 순익 개선 | 자연 경제성 미검증 |

따라서 주 blocker는 단순히 과도한 floor가 아니라 미완성 source/owner/apply 경로와 미승인 위험값이다. 원천·취소/잔량 안전 조건을 없애거나 미구현 gate를 false→true로 바꾸어 해결하지 않는다. 이후 승인 envelope가 유효한 범위에서는 매일 사용자 재승인을 추가로 요구하지 않는 계약을 유지한다.

## 5. 검증과 남은 구현

이 절은 `14:42 KST`의 보존 기록이다. 최신 검증과 다음 구현 순서는 §6을 따른다.

검증 결과(`14:42 KST` 관찰): 직전 확장 회귀 **948 PASS**였으나, 이후 공유 worktree에 별도 `confirmation_window.py`·`micro_confirmation.py`·attribution checkpoint 계산 변경이 유입됐다. 최신 전체 영향 회귀는 **947 PASS / 2 FAIL**이며 통합 review gate를 닫지 않는다. 실패는 `test_machine_microstructure_attribution.py::test_dynamic_confirmation_uses_causal_anchor_bid_not_eventual_fill_price`, `::test_checkpoint_ask_depletion_never_reads_after_checkpoint`다. 기존900ms/기존 feature builder fixture와 새1초 공통 feature 계약의 충돌이다. 해당 병행 변경/테스트를 이번 청산 작업에서 되돌리거나 임의로 고치지 않았다. 중간 결과를 최신 통합 PASS로 재사용하지 않는다.

추가 reducer history 회귀까지 포함한 적응형 청산 전용8개 module은 **156 PASS**다. Python compile·Ruff·`git diff --check`와 print-only 문서 parser는 통과했으며 parser36개 중 기존 acceptance owner1개다. Python 테스트 실행 시점이 서로 다르므로 중간703/948/947 및 전용 검증 수를 합산하지 않는다. 테스트 작성 중 assertion 시각/위치 오류는 보완 후 전용 재검증했다. gateway는 mock으로 검사했으며 실제 broker 호출·Provider 호출·비싼 장후 재생성·배포는 하지 않았다.

관찰 시점 attribution SHA256은 `3ae6d58b553190b9050e0f09041b52c474357b3f7c59b4be872424407f8e19ae`, micro-confirmation SHA256은 `c4ff0cf2cd5607e535de33a3903dcfda2ab2fbc39972e2048027cefd600a3691`이다. 이는 작업 중 코드 snapshot이며 실제 PID receipt가 아니다. 병행 변경의 완료 여부/수정 소유자를 조율한 뒤 같은 고정 worktree로 전체 재검증해야 한다. `$korstockscan-review-gate`에 따라 현재 상태에서 재기동·운영 재생성·자동 적용을 진행하지 않는다.

미완료 기능을 review finding0으로 닫지 않는다. 다음 순서는 기존 [오늘 checklist](../checklists/2026-09-09-stage2-todo-checklist.md)의 `MachineLifecycleTurnoverObjectiveFollowup0909` 하나에서 추적한다.

1. 전체 actual owner episode/lot census와 first fill·target ACK·정해진 post-target horizon의 ordered source 생산/계측 소비를 완성한다. 현재 optional 입력 파일 두 개를 생성하는 owner가 없다는 결손을 닫는다.
2. 실제 widget/Samsung/low-price SELL adapter, 합산 target 부분취소/runner allocation, pending BUY/source EXIT 중재, frozen state/loader와 active manager 생존성을 구현·프로토콜 검증한다. 공통 driver mock 통과를 대체 증거로 사용하지 않는다.
3. 별도 family evidence validator, 승인된 envelope 검증, trusted 등록·PREOPEN publisher·실제 신규 episode binding 및 자연 receipt를 연결한다. 위험 수치는 연구 후보→승인 범위로만 이행하고 기존 보유는 자동 이관하지 않는다.
4. 승인된 배포/적용 뒤 natural R6에서 순익·빈도·tail·자본점유를 평가한다. 구현과 경제성 acceptance는 독립이다.

## 6. 병행 수정 완료 후 자연 source 연결·재리뷰

사용자의 “수정이 완료됨. 다음액션 이어서 진행”에 따라 같은 worktree의 통합 회귀949 PASS를 먼저 확인한 뒤 이전 다음 액션1의 **자연 입력 생산 코드**를 보완했다. 기존 micro-confirmation 보완을 되돌리지 않았다. 최신 확대 회귀는 아래 검증 receipt를 따른다.

### 구현과 자동화 연결

- 위젯·공통 two-leg·Samsung 오전의 기존 target 접수 성공 branch에서 `adaptive_exit_target_observations`를 영속한다. exact order date/no/route·실제 lot/수량/가격·당시 entry policy/hash·최초 fill/응답 관측시각은 후속 scale-in/restart로 덮지 않는다. 계측 실패는 명시 source gap이고 기존 목표주문 관리를 중단하지 않는다.
- `src/engine/monitoring/machine_adaptive_exit_source.py`는 등록된 전체 profile과 실제 위젯 BUY state를 읽는다. target 완료 승자뿐 아니라 HELD/부분매수·미체결·legacy source gap을 분리하고, source date 밖 기존 custody는 별도로 보존한다. 이전 optional census/config 파일 의존은 제거했다.
- 기존21:15 attribution 안에서 **동일한 canonical market/depth 읽기**를 재사용한다. 추가 cron·daemon·시세/Provider/broker 호출은 없다. `natural_owner_census → 최대20 연속 관측 거래일 → outcome-independent 연구 grid → all_scope_study/native candidate → 기존 JSON/Markdown`이 코드상 자동 연결된다. 과거 날짜의 daily child/hash와 owner state source hash를 보존하며 결측일을0표본으로 메우지 않는다.
- target 체결로 중단하지 않는20분 연구 horizon,1초 as-of 관측, 최대64 anchor·stream별 anchor당30,000행·전체 stream 합산120,000 anchor-row bound를 명시한다. bound 초과·freshness/연속성/epoch 결손은 표본 제외 사유이지 자동 cap 상향·정상 EV가 아니다. 이 horizon은 실거래 시간청산 값이 아니다.
- 연구 후보60/120/180초, 손실1%, TTL5초·최대2회 등의 값은 **승인된 위험 envelope가 아니라 코드 버전으로 고정한 모델 가정**이다. 최소2 관측일/2 episode/holdout1의 초기 연구 판정도 live 승인 기준이 아니다. 양수일만 고른 ETA·상대1% 개선·5/10/20일 동시 통과·모든 조기매도 양수는 요구하지 않는다. 실제 승인 기준/dispatch를 false→true로 전환하지 않았다.

### 추가 결함 보완

1. 첫 체결 직전 수신된 신선한 호가를 무조건 버리던 조건을 수정했다. 관측 checkpoint는 체결 이후여야 하고 기존 quote age/future guard는 유지한다.
2. 동일 raw 호가를 여러 checkpoint에서 재사용한 것을 queue confirmation·추가 체결 깊이로 중복 계산하지 않는다. raw quote sequence 회귀·같은 sequence의 상충 book은 차단한다.
3. 초당120행 이상의 정상 원천을 임의 tail로 잘라1초 left watermark를 잃지 않도록 전체 bounded1초 과거 창을 사용한다. 다른 route/epoch나 미래 원천을 빌리지 않는다.
4. target metadata 오류가 known BUY lot을 분모에서 지우지 않게 했다. 위젯 envelope 결손·malformed symbol state를 whole-owner 정상 무표본으로 숨기지 않는다.
5. self-hash가 있어도 과거 daily scope의 날짜·lot 구조·보존식·중복을 검증한다. NaN/잘못된 history는 누적을 중단·격리하고 무관한 attribution 전체를 crash시키지 않는다. scope 단위 정상 원천은 보존한다.

### 읽기 전용 자연 원천 확인

source9/9 owner state만 메모리 내에서 읽었다. 등록 low-price56와 Samsung route/profile5의61 scope 중56은 exact-date census complete, filled lot19는 모두 기존 first-fill/target 신규 결속이 없어 anchor0이다. 위젯 state는 당일 accepted BUY group이 없어 신규 actual scope0이다. missing/invalid exact-date state5는 `cj_cgv_morning`, `samsung:morning_sor_reentry`, `samsung_heavy_morning`, `sk_telecom_midday`, `youngone_midday`이며, OFF/격리/전일 state 가능성과 실제 운영 실패를 동일시하지 않는다. 이 수치는 실행 PID 감사나20분 시장 replay 결과가 아니다.

과거19 lot에 현재 시각을 부여하거나 같은 과거 replay를 반복해 복원하지 않는다. **source 생성 코드 수리 완료**, **배포/신규 receipt 미확인**, **실제 자연 경제성 미확인**은 별도 상태다. strict source 요건과 bounded collection으로 유효 표본이 계속0이면 최초 결손·budget/route/collector 생존성을 이 owner에서 확인하며 무기한 표본 대기로 정상화하지 않는다.

### 검증·남은 순서

- 검증 receipt(`15:57 KST`): 최종 영향 회귀975 PASS/23.12초(중간949/968 및 부분집합은 합산하지 않음). 실제 owner의 접수 성공 branch·mock gateway와 자연 state→ordered path→2일 누적→기존 child/native 연구 후보 E2E를 검사했다. Python compile·Ruff·`git diff --check`와 print-only 문서 parser 통과, parser36개 중 기존 acceptance owner1개다.
- `korstockscan-review-gate`의 producer/consumer·authority·결측/중복·원천 시각·history 격리 재리뷰를 거쳤고 이번 source/연구 연결 범위의 미해결 finding0이다. 미완료 actual adapter와 자동 적용을 finding0으로 닫지 않는다. 실제 broker/Provider 호출·운영 장후 재생성·배포·재기동·정책 발행·commit/push는 수행하지 않았다.
- 다음 구현은 **실제 widget/Samsung/low-price owned SELL adapter·합산 target 부분취소/runner·pending BUY/source EXIT 중재 → frozen loader/manager 생존성 → 승인 envelope validator/독립 family dispatch/PREOPEN atomic publisher·신규 episode binding** 순서다. 최초 활성화 수치는 사용자가 승인한 범위에서만 소비하며 기존 보유는 자동 이관하지 않는다. 기존 `MachineLifecycleTurnoverObjectiveFollowup0909` OPEN에서 추적한다.
- 기대효과는 느린 보유의 자본점유/손실 확대 감소와 빠른 runner 참여지만 아직 관측된 수익 증가가 아니다. 같은 집합의 비용 차감 EV/순익·수익 빈도·tail·자본점유로 자연 R6를 평가한다. 현재 runtime은 기존 목표주문 유지이며 적응형 청산 자동 적용은 미완료다.

## 7. 실제 gateway SELL transport 보완·재리뷰

사용자의 “다음액션 이어서 진행”에 따라 WP4의 **실제 gateway 하위 어댑터**를 구현했다. 공통 `RegisteredSellAdapter`는 widget·Samsung 오전(기존 SOR 재진입 포함)·정오·오후·전체 등록 low-price gateway가 생성한다. 위치는 `src/trading/order/adaptive_exit/broker.py`, 회귀는 `src/tests/test_machine_adaptive_exit_broker.py`다. 새 engine-root module·중앙 custody 원장·주문 daemon은 없다.

### 구현·리뷰 보완

1. exact account/date/order와 기존 owner/position·symbol/route를 먼저 대사한다. BUY/타 owner·수량0/소수/음수·누락/비정상 지정가는 거부한다. episode 최대10주/leg를 유지하며 widget 교체 SELL의 KRX→SOR 규칙과 기존 원주문 취소 route를 구별한다.
2. `kt00007` dated 원주문과 `ka10075` 전시장 현재 미체결을 각각 최대3페이지 완결한다. continuation key 누락/반복/상한 초과, 날짜 변경, 잘못된 수량, 서로 다른 fill/remainder, unknown/transitive successor는 terminal 증거가 아니다. 원주문 잔량0과 현재 원주문/후속 active 예약 부재가 함께 확인돼야 해제한다.
3. 취소는 명시적 양수 잔량만 전송하며 `cncl_qty=0` 잔량 전체 취소를 재사용하지 않는다. ACK의 새 취소 주문번호·원주문·수량을 검증하고 ACK만으로 원주문 예약을 해제하지 않는다. 부분체결은 취소수량이 아니라 exact fill로만 custody를 줄인다.
4. owner guard를 조회 전/후 확인하고 공유 registry의 durable reservation을 API보다 먼저 남긴다. 응답 유실·형식 오류·HTTP 오류는 ambiguous 예약을 보존하며 쓰기 재시도하지 않는다. 교체 SELL의 client intent는 dated predecessor에 고정해 다른 action ID를 붙여 같은 잔량을 다시 쓰지 못한다. 실제 다음 시도는 마지막 교체 주문의 terminal 잔량에서 이어야 한다.
5. episode adapter의 critical reconciliation은 기존1초 캐시를 우회하되 공통 조회 pacing/retry 한도를 유지한다. widget `ka10075`도 execution-critical shared-read budget에 포함했다. 기본 factory는 write guard가 없고 episode 기존 order authority·production endpoint 검사를 유지한다.
6. 자체 리뷰에서 transitive successor 누락, 장시간 조회 후 guard/날짜 재검사, 중복 교체 reservation, 지정가 `None` 통과, 외부 ValueError 원문 노출을 추가 수리했다. raw account/응답/토큰은 새 진단에 저장하지 않고 응답 hash와 제한된 상태만 반환한다.
7. 공식 response spec/core/types 재대사에서 다음 페이지가 없는 응답의 continuation header는 optional임을 확인했다. 처음 추가한 literal `N` 강제 조건은 제거하고, 정상 누락/빈 값과 `Y`인데 key가 없거나 cursor/API ID가 충돌한 결함을 구분했다. 실제 계약보다 과도한 완료 허들을 추가하지 않는다.

공식 reference는 [protocol gate 기록](../kiwoom-api-data-contract.md#2026-09-09-adaptive-exit-owned-sell-adapter-reference)의 `234560d213acd8871ae344b5481aecd2f30287fa`, `16:06 KST` spec/core/Postman 교차검증이다. 해당 revision에 `kiwoom_docs`가 없고 portal 조회도 실패했으므로 미정의 cancel/modify code를 추정하지 않았다. 실제 broker request로 검증하지 않았다.

### 완료와 남은 구현의 구분

- 완료: 실제 gateway factory→공통 transport→기존 소유권 registry의 명시 수량 SELL 취소/교체·엄격한 당일 대사와 모의 회귀. `SellSnapshot/SellAck`는 그 자체로 driver `BrokerProof`나 승인 receipt가 아니다.
- **미완료**: owner loop의 `OwnerExitPort` 구현/driver 조합, frozen policy·lot binding과 실제 guard/전시장 재고 연결, pending BUY/source EXIT/target 자동 재생성 중재, 합산 target 부분취소·runner 배분, 상태 loader/manager 생존성, 승인 envelope validator·dispatch/PREOPEN atomic publish·신규 episode 자동 binding.
- **활성화 전 복구 제약**: 날짜가 바뀐 기존 주문은 undated current ledger의 번호 재사용을 추정하지 않고 owner recovery를 요구한다. 역사적 잔량이 계속 남는 취소·미정의 후속 status·명시 거절 이후 같은 predecessor 재발행도 자동 우회하지 않는다. 이들은 수집일 수나 양수 EV로 해결할 문제가 아니라 WP4/WP5 실제 복구 계약의 미완료 범위다. 원주문 종료 근거를 제거하거나 수동 예약 해제로 해결하지 않는다.
- 이 어댑터는 실제 loop에서 아직 호출되지 않는다. 기존 보유/목표매도·승인 숫자·runtime env/policy/PID/cron/systemd를 변경하지 않았고 실주문·재기동·운영 report 재생성·commit/push를 실행하지 않았다. 새 callable factory가 자동 실거래 활성화라는 뜻은 아니다.

### 목적·자동화·허들 판정

‘비용 후 작은 수익을 빈번하게’에 필요한 **중복 매도/과매도 없이 빠르게 주문을 전환하는 실행 기반**을 추가했다. 취소 경합·캐시 지연·중복 교체를 줄일 수 있는 기전이지 아직 관측된 순익 증가는 아니다. 기존 장후 source→연구 grid→native 후보 연결은 유지되지만, 실제 장전 자동 적용은 위 미완료 구현과 최초 승인 범위가 닫히기 전까지 불가다.

새 N일·N건·승률/양수 EV floor는 추가하지 않았다. exact 소유권·종료·잔량·freshness는 경제성 허들이 아니라 주문 안전 조건이므로 제거하지 않는다. 정상 브로커 응답이 계속 차단될 경우 첫 파서/복구 결손을 수정할 owner를 남기며 무기한 표본 대기로 정상화하지 않는다. 자연 경제성은 같은 episode 집합의 비용 후 EV/순익·수익 빈도·tail·자본점유로 별도 확인한다. 코드 검증을 실거래 효과로 바꾸지 않는다.

검증 receipt(`16:26 KST`): 최종 영향 회귀 **1177 PASS/27.08초**, 그 안의 신규 adapter 전용 **123 PASS**(등록 low-price56 profile factory 포함)다. 앞선1114/1173·전용119 및 부분집합을 합산하지 않는다. Ruff·Python compile·`git diff --check`·print-only parser가 통과했고 parser36개 중 기존 acceptance owner는1개다. `korstockscan-review-gate`의 producer/consumer·원장 reservation·silent-fail·권한/실제 후속 연결 검토에서 발견한 위 결함을 보완 후 재리뷰했으며 **이번 transport 구현 범위 미해결 finding0**이다. 실제 owner loop/복구·자동 적용 미완료는 이 판정으로 닫지 않는다. 기존 checklist `MachineLifecycleTurnoverObjectiveFollowup0909`에 같은 순서의 미완료 구현을 유지하며 중복 OPEN을 만들지 않는다.

## 8. Owner port·동결 session 복구 후속 보완

사용자의 다음액션 실행 요청에 따라 WP4/WP5의 **공통 실행 session과 구체 port**를 추가했다. 구현 위치는 기존 주문 역할 package의 `src/trading/order/adaptive_exit/runtime.py`이며 engine root module·중앙 custody 원장·새 daemon은 없다. 실제 loop 설치와 최초 승인 envelope는 아직 별개 미완료다.

### 구현과 자체 리뷰 보완

1. `RegisteredOwnerExitPort`가 `OwnerSession`의 최초 fill·원 target·entry/cost·exit policy·ExecutionBounds·owner context·target intent·승인 receipt hash를 동결한다. 복원은 전체 schema/hash/수량/journal/날짜/정책 결속을 검증하며 잘못된 상태를 새 빈 episode로 바꾸지 않는다. self hash는 무결성일 뿐 권한이 아니고, 독립 `authorize_binding`이 없으면 broker 호출/주문을 시작하지 않는다.
2. 기존 registry의 exact client intent 읽기와 `recover_replacement`를 연결했다. ACK와 registry 저장은 성공했지만 owner 저장 전에 실패한 경우 동일 bound 주문을 fresh dated/current proof로 회복하며 SELL을 다시 제출하지 않는다. unbound/ambiguous/rejected 예약을 symbol/time 근접 조회로 채우지 않는다. 실제 가격·비용/PnL은 합성하지 않는다.
3. original-owner lock·guard를 조회 전후 재검사한다. 취소 phase는 저장됐지만 broker reservation 전에 실패한 경우에만 exact client intent **부재**, fresh quote와 원 guard를 확인해 같은 취소를 한 번 이어간다. 예약/ACK/ambiguous/rejected 행이 있으면 재시도하지 않는다. disk 실패는 메모리/주문 진행보다 먼저 전파하고, 계약 거절은 마지막 durable phase와 명시 alert를 유지한다.
4. 초기 목표매도의 실제 부분체결을 판단보다 먼저 대사한다. `TARGET_WORKING|INTENT_PERSISTED|CANCEL_PENDING` 수량 rebind 누락을 수리했고, exact 누적 fill에서만 새 수량 epoch를 만든다. 최초 fill 시계·연장 횟수·trailing stop은 재시작/부분체결로 초기화하지 않는다. 후속 매도 TTL·부분체결·두 번째 시도는 원 target이 아니라 마지막 terminal 교체 주문의 잔량에 연결한다.
5. 조회 완료 proof의 시각을 루프 시작 시각과 비교하던 조건은 실제 지연이 있는 응답을 미래 시각으로 차단할 수 있었다. trusted owner의 조회 후 시계로 대사하고, 판단/쓰기 직전 시세 freshness는 별도로 재검사한다. 조회 중 시세가 만료되면 쓰기는 차단하며 quote-age 한도를 높이지 않는다.
6. 트레일링 reducer/decision이 두 번에 걸쳐 저장되던 부분을 원자 전환으로 수정했다. 매 저장 checkpoint를 JSON roundtrip 복원해 high-water/stop·trail flag 일치를 검증했다. 시세 부재 상태에서도 기존 주문 대사는 가능하지만 stale/결측 시세로 교체 매도하지 않는다.
7. source/date gap의 직접 원인을 alert에 보존한다. 날짜 변경 시 전일 주문을 당일 번호로 재결속하지 않으며 `broker_source_gap:cross_date_current_ledger_requires_owner_recovery`와 `manager_required=true`를 유지한다. 이는 공통 session의 보존 계약이며 실제 owner loader/종료 루프가 이를 소비했다는 증거는 아니다.

공식 API `main`은 `2026-09-09T16:36:01+09:00`에 기존 SHA `234560d213acd8871ae344b5481aecd2f30287fa`로 재확인했고, spec의4개 API와 core client/types를 확인했다. [protocol 기록](../kiwoom-api-data-contract.md#2026-09-09-adaptive-exit-owned-sell-adapter-reference)을 따른다. 요청 필드/조회 cap·pacing을 확대하거나 미정의 취소 상태를 추정하지 않았다. 모든 브로커 검증은 tmp registry와 fake wire였다.

### 목적·자동화·남은 단계

- 기대효과는 재시작·부분체결·조회 지연 때문에 매도 전환이 중단되는 경로와 중복/과매도 위험을 줄여, 비용 후 작은 수익의 반복 실현을 지원하는 것이다. 이번 테스트는 실행 정합성 근거이며 실제 순이익·빈도·자본효율 개선의 증거가 아니다.
- 장후 source→grid→native 후보 자동 연구는 기존 구현을 유지한다. **실제 런타임 자동 적용은 아직 미완료**다. 독립 target/lot용 concrete port는 있지만 기존 위젯/전체 episode 루프가 이를 호출하지 않으며 운영 정책/PID·기존 주문/보유를 변경하지 않았다.
- 다음 구현 순서: 기존 owner per-lot custody/target·pending BUY/source EXIT 중재 → 합산 target/runner·owner loader/날짜 rollover·실제 manager 생존성·미정의 취소/명시 거절 복구 → 승인 envelope/validator·독립 dispatch/PREOPEN atomic publisher·신규 episode binding. 이 실행 결손은 표본을 기다리거나 floor를 낮춰 해결할 일이 아니다.
- 승인 조건에 새로운 N일/N건·상대1%·5/10/20일 동시 양수·각 조기청산 양수 조건을 추가하지 않았다. 조회 후 시각의 불가능한 비교는 제거했지만 exact 소유권/잔량/terminal·freshness와 최초 승인 범위는 유지한다. 승인된 범위 안 자동 유지 설계와 아직 없는 최초 승인 숫자를 구별한다.

최종 검증 receipt(`16:54 KST`): session/복구 전용61건을 포함한 영향 회귀 **1238 PASS/29.24초**, Ruff·compile·`git diff --check`·print-only parser 통과. parser36개 중 기존 acceptance owner는1개다. 앞선1238/28.81초와 직접 경로280/6.85초는 중복 검증이며 합산하지 않는다. `korstockscan-review-gate`에서 수량 rebind·트레일링 원자성·조회 후 시계·취소 미전송 복구를 수리하고 producer/consumer·registry·직접 fake wire·권한·silent failure를 재리뷰했다. **이번 공통 port/session 범위 미해결 finding0**이며 실제 owner loop/자동 적용 미완료는 이 판정으로 닫지 않는다. 실제 broker/Provider 호출·정책 발행·프로세스 재기동·운영 report 재생성·commit/push는 이번 작업에서 실행하지 않았다.

## 9. 실제 owner loop 연결과 custody 보존

사용자의 다음 액션 요청에 따라 `owner_loop.py`를 기존 `src/trading/order/adaptive_exit/` 역할 package에 추가하고 위젯·공통 two-leg의 **실제 `run_once`**에 동결 session 소비를 연결했다. 저가주 전체 dated catalog와 Samsung 오전/SOR 재진입·정오·오후는 같은 base loop/선택적 서비스 인자를 사용한다. 신규 engine-root module·중앙 원장·daemon·cron은 없다. 운영 launcher가 서비스를 공급하거나 보유 lot에 새 session을 발급한 것은 아니며 실거래 활성화는 계속 미완료다.

### 구현·리뷰 보완

1. `OwnerLoopServices`는 독립 승인 검증, 원 owner 잠금, 전체 broker/account/manual/safety guard, 정규화 시세와 거래정지 반영 시계의 **명시적 연결점**이다. 기본값은 없음이다. 서비스/승인/잠금/검증 시계가 없으면 adaptive broker 호출을 시작하지 않는다. 기록된 hash·후보만으로 새 session이나 권한을 만들지 않는다. 이 서비스의 실제 launcher 구현은 다음 작업이다.
2. 공통 two-leg는 profile/symbol/session·원 episode/leg·target 주문 날짜/번호/intent·fill 가격/수량을 결속한다. 목표매도 부분체결과 교체 매도 체결을 별도 수량으로 저장하고 동일 lot의 기존 target 재생성·재매수 경로로 되돌아가지 않는다. 선택되지 않은 기존 target은 원래 owner가 관리한다. pending BUY/confirmation·기존 registry 복구 상태는 추정 취소/신규 주문 대신 명시 recovery로 보류한다.
3. 위젯은 원 target·owner context·독립 target intent와 해당 episode의 잔량 보존식을 확인한다. 기존 target/source EXIT/scale-in 경로와 동시에 주문하지 않는다. 이미 접수·대기 중인 별도 주문이나 기존 exit intent가 있으면 보류한다. **새 source EXIT의 정책별 우선순위, pending BUY 취소 후 진입 전환, 합산 target/runner 분할의 적극적 중재는 아직 구현되지 않았다.** 현재 연결을 그 중재의 완료로 보고하지 않는다.
4. 날짜 전환·현재 catalog 삭제 시 동결 widget symbol만 원 날짜/주문과 함께 유지하고, 다른 symbol의 정상 날짜 전환은 막지 않는다. producer snapshot이 없어도 동결 session 소비 분기에 도달한다. Episode는 보유 session을 rollover로 버리지 않고 `run_until_terminal`이 미해결 manager를 HELD/BLOCKED terminal로 종료하지 않게 했다. 전일 주문의 undated current ledger 결속은 계속 금지이며 `cross_date_current_ledger_requires_owner_recovery`를 보존한다. 현재 설치된 process의 생존/익일 자동 복구를 검증한 것은 아니다.
5. 원자 저장 실패 시 메모리를 마지막 상태로 되돌리고 예외를 전파하며 broker 쓰기를 선행하지 않는다. 취소 ACK 뒤 owner 복원은 재취소/기존 target 재등록으로 변환하지 않는다. 리뷰에서 확인한 **잠금 상실 후 outer loop가 상태를 덮어쓰는 문제**를 보완했다. 잠금이 없으면 durable 상태를 변경하지 않는다. 손상된 custody JSON/schema는 새 빈 포트폴리오로 초기화하거나 덮지 않고 로더 오류로 보존한다.
6. 수량이 0이 된 episode는 `ADAPTIVE_EXIT_FLAT`, widget은 `adaptive_exit_remaining_qty`로 분리했다. 이는 비용 대사 완료가 아니다. `adaptive_exit_realized_pnl_status=unreconciled_exact_fill_cost_required`이며 기존 `COMPLETE`/TP 완료·재진입 관찰로 합치거나 체결가/수익을 추정하지 않는다. 교체 주문의 정확한 fill-price/비용을 일반 owner 원장에 반영하고 기존 완료 consumer와 다음 episode에 넘기는 구현이 남았다. 이 후속 처리 전에는 자동 반복 매매 완료라고 할 수 없다.

공식 API는 `2026-09-09T17:01:29+09:00`에 기존 SHA `234560d213acd8871ae344b5481aecd2f30287fa`로 재확인하고 spec4개 API를 읽었다. 요청·응답 필드/취소 상태 해석·retry/read pacing을 변경하지 않았다. 기존5개 adapter를 사용한 호출 계약을 tmp owner registry/fake wire로 검증했으며 실제 broker/Provider는 호출하지 않았다.

### 목적·자동화·조건 달성 가능성

- 기대효과는 조기청산·trailing 판단을 **실행 owner까지 전달**하면서 재시작·부분체결·날짜 전환의 중복/과매도·상태 유실을 방지하는 것이다. 비용 후 작은 수익의 빈번한 실현은 의도이지 이 테스트로 입증된 수익 개선이 아니다. 현재 다음 episode handoff까지 미완성이므로 반복 수익 실현·자동 적용 완료는 주장하지 않는다.
- 기존 자연 연구 경로는 유지한다. 새 경제성/거래일/sample floor·매 청산 양수 요구는 추가하지 않았다. 원 소유권·잔량·exact terminal·freshness·독립 승인 검증은 유지할 안전 조건이다. 구현되지 않은 consumer/중재를 표본 누적이나 floor 인하로 해소할 수 있다고 보고하지 않는다.
- 다음 순서는 **exact fill-price/비용/terminal 원장→다음 episode handoff**, 합산 target/runner·pending BUY/새 source EXIT 중재와 전일/취소/거절 복구, 최초 승인 envelope/validator·PREOPEN publisher·신규 enrollment·launcher 서비스다. 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`에 기록했으며 별도 중복 항목은 만들지 않았다. 승인 숫자는 여전히 미승인이다.

최종 검증 receipt(`17:19 KST`): 실제 owner-loop 전용 **43 PASS/2 owner-비대상 SKIP**, 최종 영향 회귀 **1281 PASS/2 owner-비대상 SKIP/30.56초**. 전용 테스트가 영향 회귀에 포함되므로 합산하지 않는다. 전체 dated low-price profile와 Samsung 세 constructor가 같은 base 연결을 공급하는 것도 확인했다. Ruff·compile·`git diff --check`·print-only parser 통과, parser36개 중 기존 acceptance owner는1개다. `korstockscan-review-gate`에서 원 target/lot→port/driver→gateway/registry→owner 저장/loader/종료와 silent-fail·권한 경계를 재리뷰하고 발견한 상태 필드 결속·수량 종료 분리·잠금 상실·손상 state 초기화 결함을 보완했다. **검토한 소비 분기/보존 범위의 미해결 finding0**이며 새 source EXIT 중재·정확한 비용 원장·승인/실제 launcher 미완료를 전체 완료로 바꾸지 않는다. 실제 정책 발행·보유 이관·주문·runtime env/PID/재기동·운영 report 재생성·commit/push는 실행하지 않았다.

## 10. 수량 종료 원장과 기존 다음 진입 handoff

사용자의 다음 액션 요청에 따라 기존 `src/trading/order/adaptive_exit/` package에 `terminal.py`를 추가했다. 별도 daemon·주문 owner·장후 작업은 만들지 않았다. §9의 다음 episode consumer 전부 미구현이라는 설명은 이전 시점이다. **이번 범위는 정확한 수량 종료와 기존 진입 owner로의 handoff이며, 정확한 체결금액·비용 대사는 미완료**다.

### 구현과 보완

1. 원 target와 모든 교체 SELL의 날짜/주문번호/registry intent/연속 predecessor/정책 hash를 확인하고 기존 dated/current 대사 receipt가 있는 `ORDER_TERMINAL`만 종료 원장으로 만든다. target 체결과 교체 체결의 합이 원 lot 매수 수량과 일치해야 한다. 취소 ACK·자체 session hash·잔량0 하나만으로 완료하지 않는다. 체결되지 않고 끝난 수량은 `unfilled_terminal_qty`로 남기고 미정의 취소/만료 사유를 발명하지 않는다.
2. 위젯은 모든 선택 lot가 종료되고 원 owner registry 잔량이0일 때 기존 orders에 target/교체 SELL 수량을 원자 반영하고 원 session·terminal receipt를 보존한다. episode open을 닫고 기존 완료 횟수와 cooldown 기준을 한 번만 갱신한다. `take_profit_completed_at`이나 수익 성공으로 바꾸지 않는다. 다음 loop의 기존 신호·일일 cap·cooldown·가격/수량·전체 broker/safety 검사를 그대로 거치며 이 코드가 새 BUY를 제출하지 않는다.
3. 공통 two-leg는 당일 `attempt_consumed`와 `ADAPTIVE_EXIT_FLAT`을 유지한다. 전일 모든 leg가 종료되고 원 registry 잔량도0이면 원 상태·주문·session·수량 종료 증거 전체를 archive한 뒤 기존 새 날짜 entry owner에 넘긴다. 즉시 재매수나 당일 횟수 확대가 아니다. Samsung 계열과 전체 low-price profile은 같은 base 경로를 사용한다.
4. 저장 실패는 메모리를 되돌리고 예외를 전파한다. 재시작 뒤 원장 중복 반영·재주문·완료 횟수 중복 증가를 방지한다. 위젯 전일 완료가 늦게 반영되면 전일 archive로 귀속하고 오늘 한도를 소모하지 않는다. 일반 날짜 전환이나 보존기간 경계로 adaptive 종료 증거를 삭제하지 않으며, terminal 원장이 없으면 episode manager를 정상 종료시키지 않는다. 잠금/독립 승인 검증이 없으면 claim을 해제하지 않는다.

### 비용 원천의 확인된 제약

`2026-09-09T17:21:55+09:00`에 공식 upstream SHA `234560d213acd8871ae344b5481aecd2f30287fa`를 재확인하고 `kiwoom/_data/kiwoom_api_spec.json`의 `ka10076`·`kt00015`를 확인했다. 기존 `kt00007` 수량 대사만으로 체결금액·비용을 확정할 수 없다. `ka10076`의 주문번호 request는 exact-order 필터가 아니라 이전 체결 조회 cursor이며 날짜 필드/명시적 체결 sequence와 주문별 비용 합산 의미가 부족하다. `kt00015`는 거래번호/정산내역이며 주문번호와의 exact 연결을 확인하지 못했다. 종목·일자 합계인 기존 `ka10073`의 수량 일치만으로 독립 owner 비용을 배분하지 않는다.

따라서 체결금액·수수료·세금·순이익은 `null`, `realized_pnl_status=unreconciled_exact_fill_cost_required`를 유지한다. 주문 가격이나 `cntr_uv × 누적체결수량`, 고정 비용으로 exact 손익을 채우지 않는다. 이 미완료는 `external_dependency/정확한 주문별 정산 원천 계약`이며 단순 표본 floor 문제가 아니다. 요청/응답 parser·호출량·실제 API는 변경/실행하지 않았다. 실현 손익 및 장후 경제성 consumer는 이 gap을 해소하기 전 완료로 보지 않는다.

### 목적·자동화·다음 수용조건

- 기대효과는 종료 수량이 별도 view에 갇혀 다음 유효 신호를 계속 막는 구조적 결손과 날짜별 횟수 오집계를 줄이는 것이다. 작은 수익의 빈도 증가나 순이익 개선을 아직 입증한 것은 아니다.
- **비용 확인 대기를 기존 다음 진입의 새 승인 허들로 만들지 않는다.** 다만 정확한 소유권·체결/미체결 terminal·잔량·원 잠금/승인 검증은 유지한다. 신규 EV/표본/거래일 floor, 매 청산 양수 요구, 수량/cap/cooldown 완화는 없다.
- 자연 후보 산출 경로는 기존21:15 owner를 유지한다. 이번 종료/handoff는 승인된 session을 소비하는 코드 경로이지 현재 운영 bootstrap 설치·최초 활성화가 아니다. 정확한 정산 원천/비용 consumer, 합산 target/runner·pending BUY/새 source EXIT 중재, 미해결 전일 주문/취소·거절 복구, 승인 envelope/validator·PREOPEN publisher·신규 enrollment·launcher 서비스가 남아 있다. 전일 **이미 종료된** 상태의 archive와 미해결 전일 주문의 broker 복구는 구분한다.
- 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`에서 계속 추적한다. 운영 산출물 재생성·policy/env/PID·보유/주문·재기동·commit/push·외부 sync는 실행하지 않았다.

최종 검증 receipt(`17:43 KST`): 신규 terminal 전용 **30 PASS/2 owner-비대상 SKIP**, 최종 영향 회귀 **1311 PASS/4 owner-비대상 SKIP/35.29초**. 전용 검증은 영향 회귀에 포함되므로 합산하지 않는다. 두 독립 lot의 단일 episode 완료, target 부분체결/교체 SELL, target 단독 완료, 비용 null·권한 비승격, 다음 신호/익일 기존 owner handoff, 재시작·저장 실패·권한/잠금 결손·미대사 registry·재해시 충돌·전일 횟수 귀속을 확인했다. Ruff·compile·`git diff --check`·print-only parser 통과, parser36개 중 기존 acceptance owner는1개다. 직접 pytest executable 실행은 import-path 오류로 수집 실패했고 프로젝트 표준 `.venv/bin/python -m pytest`로 재실행해 위 결과를 얻었다. `korstockscan-review-gate`에 따라 원 registry→terminal producer→실제 owner 저장/재시작/날짜 전환→기존 next-entry gate와 경제성 비권한 경계를 재리뷰했다. **이번 수량 종료·증거 보존·handoff 범위의 미해결 finding0**이며 정확한 비용·전체 live 통합 미완료를 전체 완료로 바꾸지 않는다.

## 11. 공통 체결 통보와 종료 대사 순서 충돌 보완

사용자의 다음 액션 요청에 따라 체결금액·비용 원천부터 추적하던 중, 먼저 재현된 종료/handoff 결함을 보완했다. 이번 수정 위치는 기존 공유 원장 `owner_custody_registry.py`와 `adaptive_exit/{broker,terminal}.py`, 기존 두 테스트 모듈이다. 별도 producer·주문 owner·engine-root 모듈은 만들지 않았다.

### 발견·수정·재리뷰

- **P1 재현**: `sniper_execution_receipts.handle_real_execution`의 공통 WS 수신이 먼저 `ORDER_TERMINAL`을 기록하면, adaptive dated/current 대사가 나중에 성공해도 일반 `transition()`의 정상적인 terminal 멱등성 때문에 전용 reason이 기록되지 않았다. 종료 원장이 그 reason 문자열을 필수 증거로 요구해 위젯·episode 모두 수량0 뒤 handoff에 실패했다. 수정 전 순서별 회귀는 **2 FAIL/2 PASS**였다. 이는 수익 표본 부족이나 안전 차단이 아니라 소비 계약 결함이다.
- **독립 대사 증거**: 원 종료 상태·reason·일반 transition 계약을 바꾸지 않고 append-only `TERMINAL_RECONCILIATION_RECORDED`에 날짜/주문/계좌/owner/position/intent/route/주문수량/체결수량과 dated/current receipt SHA를 결속한다. 원장 잠금 안에서 최신 수량을 다시 확인한다. WS 종료·취소 ACK만으로 이 증거를 만들지 않으며 재대사 성공 후에만 원 terminal consumer가 사용한다.
- **반복·저장·호환**: 같은 수량의 후속 조회는 첫 proof를 보존해 immutable terminal이 매번 달라지지 않는다. 증거 저장 실패는 source failure로 남겨 driver 진척을 막고 다음 정상 대사에서 무재주문 복구한다. 구 adapter의 `adaptive_exact_terminal:<SHA>`는 원본 hash-chain terminal event 당시 수량으로 읽기 전용 투영한다. 과거 파일을 덮지 않으며 뒤늦은 모순 수량으로 옛 proof를 재결속하지 않는다.
- **직접 consumer 검증**: 원 target 단독 완료, target 부분체결 후 교체 SELL, WS 선행/후행·registry 사이 fill 경합, 원장 쓰기 실패, 재시작, owner/계좌/날짜/주문/수량 충돌, 기존 다음 신호/익일 owner 경로를 확인했다. 일반 main/manual registry transition과 실제 API parser/호출 조건은 변경하지 않았다. 종료 금액·비용·실현손익은 여전히 null이며 TP 성공·새 BUY 승인으로 바꾸지 않았다.

### 목적·자동화·조건·다음 순서

- 기대효과는 정상 청산 뒤 수량 종료 증거가 생성되지 않아 후속 유효 진입이 막히는 구조적 병목 제거다. **비용 후 작은 수익의 빈도/순이익 개선은 아직 실증하지 않았다.** 안전상 필요한 exact owner/잔량/terminal을 유지하면서 불필요한 수신 순서 의존만 제거했다. 새 양수 EV·기간·표본 floor 또는 비용 대기형 next-entry gate는 추가하지 않았다.
- 기존21:15 자연 후보 산출과 승인된 session의 종료/handoff 코드는 유지한다. **실제 최초 자동 활성화는 미완료**다. 승인 envelope 숫자·검증기/PREOPEN publisher/enrollment·실제 launcher 서비스 없이 후보나 테스트 성공을 실주문 권한으로 전환하지 않는다. 현재 정책/env/PID·주문·보유·재기동·commit/push·장후 report 재생성은 실행하지 않았다.
- 공식 upstream은 `2026-09-09T18:06:32+09:00`에 SHA `234560d213acd8871ae344b5481aecd2f30287fa`로 재확인했다. spec `00`의903은 누적 체결금액이지만938/939는 당일 수수료/세금이며 exact 주문별 배분을 확인하지 못했다. 기존 공통 WS→registry가 외부 owner의 누적 금액도 기록하지만 원 raw/시간/비용 companion까지 완결된 adaptive 경제성 consumer는 아니다. REST 비용 계약의 §10 gap도 유지한다. 기존 자연 금액을 정확한 비용·순이익으로 승격하거나 마지막 체결가×누적수량으로 대체하지 않는다.
- **다음 실행 가능 구현**은 합산 target/runner·pending BUY/새 source EXIT의 원 owner 중재와 미해결 전일 주문/취소·거절 복구다. 정확한 주문별 정산 원천/경제성 consumer는 외부 계약 gap과 병행해 분리 추적하며 같은 원천 재조회나 sample floor 인하로 해결하려 하지 않는다. 그 뒤 최초 승인 envelope/validator·PREOPEN/enrollment·launcher를 닫는다. 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`를 재사용한다. 코드·배포·자연 소비·경제성은 별도 판정이다.

최종 검증 receipt(`18:09 KST`): broker/terminal/공유 owner 회귀 **253 PASS/2 owner-비대상 SKIP**, 전체 영향 회귀 **1332 PASS/4 owner-비대상 SKIP/36.82초**. 전용 검증은 전체에 포함되므로 합산하지 않는다. Ruff·compile·`git diff --check`·print-only parser 통과, parser36개 중 기존 acceptance owner는1개다. `korstockscan-review-gate`로 공유 체결 수신→registry transition/fill→dated/current proof→terminal→실제 owner 저장/재시작/next-entry를 재리뷰했고, 이 순서 충돌·증거 저장/호환 범위의 미해결 finding0이다. 별도 정산 계약·중재/복구·최초 live 통합 미완료와 자연 경제성은 남아 있으며 전체 구현 완료로 보고하지 않는다.

## 12. 위젯 원래 EXIT와 적응형 청산 단일 owner 중재

사용자의 다음 액션 요청에 따라 §11의 중재 후속 중 **위젯의 기존 source final EXIT 소비**를 구현했다. 위치는 기존 `src/trading/order/adaptive_exit/arbitration.py`와 공통 decision/driver/port/owner-loop, 원 위젯 engine 및 전용 회귀다. 새 engine-root 모듈·주문 daemon·신호 producer는 만들지 않았다. Episode에 위젯 EXIT 신호 계약을 임의 부여하지 않는다.

### 구현·결함 보완

1. 기존 `_exit_signal`의 원 producer 계약·native 신호 ID·종목/route/session·원천 freshness 검증을 통과하고, 진입 당시 동결 정책이 명시적으로 `source_final_exit_action=sell_own_filled_quantity`인 경우만 원 owner의 청산 요청으로 접수한다. `observe_only_no_forced_sell`과 잘못된 정책은 강제매도로 전환하지 않고 기존 adaptive 정책을 유지한다. 원 정책을 독립 검증하는 `authorize_final_exit` 서비스가 없으면 활성화하지 않는다. 이는 매번 새 사용자 승인이나 별도 수익률 gate가 아니라 기존 정책의 권한 확인이며 실제 launcher 공급은 아직 미구현이다.
2. `machine_adaptive_exit_original_final_exit_v1`은 원 entry signal·position·scope·동결 session binding 전체·execution-policy hash·source hash·route/session·원천 관측시각/접수시각을 결속한다. **리뷰 중 처리 시각으로 원천 시각을 대체하는 결함을 보완**해 최초 fill 이전 또는 미래 snapshot은 접수하지 않는다. 원자 저장이 완료된 뒤에만 broker 단계로 진행한다. 접수 뒤 원천 파일이 없어지거나 재시작해도 의도는 보존하지만 각 실제 쓰기의 fresh executable BBO·원 잠금·원 정책/전체 safety는 다시 검증한다. 다른 포지션 receipt·재해시된 충돌·도중 권한 철회·저장 실패를 거절한다.
3. 검증된 final EXIT는 soft deadline/runner 선정/trailing보다 우선하는 intent로 기존 driver 하나에 전달한다. **원 target 취소→exact terminal/잔량 대사→같은 owner의 SELL** 경로를 재사용하고 기존 별도 `_maybe_submit_exit`나 새 BUY로 우회하지 않는다. 이미 trailing인 lot도 같은 writer로 청산한다. 미제출 `pending_entry_confirmation`은 원 청산 접수 시에만 철회하고 원본을 종료 이력에 보존한다. 완료 뒤 §10/11 수량 종료 consumer와 기존 다음 신호/cap/cooldown으로 돌아가며 실현 수익/익절 완료를 합성하지 않는다.
4. **리뷰 중 비표준 pending 주문 상태를 놓치는 결함을 보완**했다. `SUBMITTED`뿐 아니라 `ACCEPTED/UNKNOWN/AMBIGUOUS` 등 종료가 입증되지 않은 non-target 주문이 있으면 원 owner 복구로 남긴다. 실제 pending BUY를 암묵적으로 취소하거나 늦은 매수체결을 무시하지 않는다. 신규 종료 주문과 기존 target가 서로 다른 lot/owner를 매도하지 않도록 기존 수량 보존식·소유권/주문 안전은 유지한다.

### 목적·자동화·조건·남은 범위

- 기대효과는 적응형 분기에 들어간 뒤 원래의 유효한 EXIT가 무시되거나 별도 매도 owner와 충돌하는 문제를 줄이고, 정상 종료 뒤 다음 유효 기회로 복귀할 수 있게 하는 것이다. **비용 후 작은 수익의 빈도/누적 순이익 개선은 아직 측정하지 않았다.** 현행 exit 모드의 연구와 실제 source EXIT 효과도 같은 경제성 분모로 합치지 않는다.
- 신규 양수 EV·표본·거래일 floor나 모든 청산 양수 조건은 추가하지 않았다. 접수된 신호를 매 loop 재발생시켜야 한다는 과도한 조건도 없다. 필수 source-policy/identity·시각·원 잠금/잔량/BBO 검증은 안전 계약이다. 정확한 비용 미대사는 null과 별도 경제성 acceptance로 유지하며 기존 next-entry의 새 허들로 만들지 않는다.
- 기존21:15 자연 연구→후보 산출은 유지하고 이번 변경은 동결 session이 있을 때의 코드 소비 분기다. **최초 실거래 자동 적용은 여전히 미완료**다. 승인 numeric envelope/독립 validator·PREOPEN publisher·신규 enrollment·실제 launcher 서비스가 남아 있으며 후보 자동 산출 승인을 임의 위험값 승인으로 해석하지 않는다. 검증용 fake service를 실제 승인 검증기로 설치하지 않았다.
- 다음 실행 가능한 범위는 **합산 target의 runner 배분/부분취소, 실제 pending BUY의 취소·late fill 중재, legacy/force-flat EXIT 및 미해결 전일/취소·거절 복구**다. 이번 위젯 source EXIT 하나를 전체 owner 중재 완료로 바꾸지 않는다. 정확한 주문별 금액/비용 consumer의 외부 원천 계약 gap은 병행 추적한다. 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`를 재사용하며 중복 작업을 만들지 않았다.
- 공식 upstream은 `2026-09-09T18:19:48+09:00`에 SHA `234560d213acd8871ae344b5481aecd2f30287fa`로 재확인했다. `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10001/kt10003` 요청/응답·제약과 기존 Postman 요청 형식을 대조했다. 이번에는 기존 adapter를 재사용했고 API wire/request/response parser·호출량/retry·ACK/terminal 계약을 변경하지 않았다. 실제 broker/Provider 호출은 없다.

최종 검증 receipt(`18:30 KST`): 신규 중재 전용 **38 PASS/2.40초**, 전체 영향 회귀 **1370 PASS/4 owner-비대상 SKIP/38.79초**. 전용 검증은 전체에 포함되므로 합산하지 않는다. Ruff·compile·`git diff --check`·print-only parser 통과, parser36개 중 기존 acceptance owner는1개다. `korstockscan-review-gate`에 따라 원 snapshot/정책→원자 receipt→decision/driver/port→gateway/registry→종료/다음 신호 consumer를 재리뷰했다. 중간 검증의 테스트용 Clock 필수인자 누락과 유효 tick에 맞지 않는 모의 가격도 수정한 뒤 재실행했으며 실제 clock/가격 안전 조건은 완화하지 않았다. **이번 위젯 source EXIT 중재·증거 보존 범위의 미해결 finding0**이며 실제 pending BUY/합산 target/전체 활성화 미완료를 완료로 바꾸지 않는다. 운영 정책/보유/주문·env/PID/재기동·장후 report 재생성·commit/push는 실행하지 않았다. 병행 작업과 기존 dirty 변경은 보존했다.

## 13. 합산 target 배분·부분취소 계산 계약과 장후 진단 연결

사용자의 다음 액션 요청은 §12 후속 적응형 청산 구현으로 해석했다. 선택된 장후 모니터링 문서를 실제 모니터링·주문/재기동 실행 지시로 확대하지 않았다. **이번 완료 범위는 합산 target의 불변 원천 결속·runner 잔량 범위·부분취소 수량 보존 계산과 기존 장후 consumer 연결이다. 실제 부분취소/트레일링 실행 coordinator는 아직 미구현이다.**

### 먼저 확인한 구조적 제약

- 기존 `OwnerSession`/driver는 하나의 target와 하나의 lot를 전제로 하고, 원 target 전량 terminal 뒤 교체 SELL을 허용한다. 같은 합산 target를 여러 lot session에 넣으면 각각 같은 주문을 취소/매도할 수 있으므로 기존 duplicate-target 거절을 해제하지 않았다.
- 현재 registry의 open SELL commitment는 원 주문수량−체결수량이다. 부분취소 ACK만으로 원 주문 전체를 `ORDER_TERMINAL` 처리하면 아직 살아 있는 비runner 목표수량까지 해제하게 된다. 반대로 기존 전량 terminal 조건을 그대로 요구하면 부분취소 이후 영원히 기다릴 수 있다. **정식 부분취소 proof와 남은 reservation을 보존하는 group coordinator가 필요**하며 표본 floor 문제로 분류하지 않는다.
- 합산 SELL 누적 체결수량은 원 BUY lot별 실제 매도 귀속을 제공하지 않는다. FIFO/비례 배분을 실제 broker fill로 발명하지 않으며, 최종 구현에서 필요한 것은 승인 정책에 결속된 명시적 owner 회계/runner 배분 규칙이다. 존재하지 않는 broker lot label을 기다리는 조건을 새 승인 gate로 만들지 않는다.

### 구현·리뷰·보완

1. 기존 order/runtime 역할 package에 `target_group.py`를 추가했다. 기존 target observation에서 같은 scope/episode/date/route의 BUY lot·주문번호·최초 fill 관측시각·수량/가격과 단일 target를 결속한다. 원천/entry-policy hash·엄격한 source-only 권한·중복 lot/BUY 주문·부분매수/누락 clock·날짜/ACK 시각·수량 합계를 검증한다. 신규 producer·engine-root 모듈·daemon·broker API는 없다.
2. `plan_runner_release`는 명시한 strict runner subset과 target 누적 체결/잔량으로 가능한 runner 잔량의 **하한/상한**을 계산한다. 예를 들어 두10주 lot 중 한 lot가 runner이고 합산 target5주가 체결됐다면 잔량은5~10주로만 확인된다. 하한을 임의 주문수량으로 채택하거나 상한을 실제 귀속으로 단정하지 않는다. 반환 `cancel_quantity=null`, live 지원 false로 실제 회계 배분 미완료를 표시한다.
3. `CancelAccounting`/`reconcile_group_cancel`은 원 group·dated target/cancel·원 수량·확인된 취소수량·전후 누적체결/잔량을 검증하는 **순수 계산 계약**이다. 취소 중 late fill·일부만 취소·전량 체결을 반영해 `owned_open_qty = target_reserved_qty + unreserved_qty`를 지킨다. 원 target 잔량이 양수여도 계산이 가능하며 원 target 전체 terminal을 추가 요구하지 않는다. 이 구조체는 실제 REST proof producer가 아니고 `runtime_reservation_release_allowed=false`다. 일반 ACK나 rehash 하나로 실제 registry 예약을 풀지 않는다.
4. 기존21:15 attribution의 `collect_owner_census → bind_ordered_paths → all_scope_study → Markdown`에 `shared_target_groups`를 전달했다. 하나의 합산 target는 한 번만 기록하고 lot 분모는 그대로 보존한다. 동결 주문/수량/가격과 현재 owner의 각 BUY lot를 다시 대사하며 결손은 `source_invalid`, 결속된 경우도 `source_bound_runtime_unavailable`다. 과거 group를 현재 활성 target로 인증하지 않도록 `current_target_epoch_verified=false`를 남긴다. rolling history의 과거 lot 분모와 달리 이 진단은 현재 source-date만 다룬다. group를 독립 lot 경제성 경로로 승격하지 않고 기존 unsupported exclusion을 유지한다.
5. 리뷰에서 중복 lot 정렬의 타입 오류, target/first-fill의 날짜 혼입, 현재 owner fill-price 변경이 동결 group에 재결속되는 반례를 보완했다. 잘못된 group와 scope 미완료 사유가 consumer에서 누락되지 않게 했고 기존 단일 target 연구·실제 owner 분기는 유지했다.

공식 upstream은 `2026-09-09T18:32:31+09:00`에 SHA `234560d213acd8871ae344b5481aecd2f30287fa`로 재확인했다. `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10003` 전체 요청/응답을 읽고 현행 adapter의 `kt00007/ka10075` 대사·registry 예약 consumer를 확인했다. 양수 부분취소 request의 존재를 실제 부분취소 대사/예약 해제 완료로 해석하지 않는다. API wire/parser/실제 호출·호출량/retry는 변경하지 않았다.

### 목적·자동화·조건·다음 액션

- 기대효과는 일부 trailing을 위해 전체 목표주문을 취소하거나 같은 target를 중복 관리하는 결함을 예방하고, 구조적 미지원과 단순 표본 부족을 분리하는 것이다. **현재 비용 후 작은 수익의 빈도/순이익 개선이나 실제 부분 trailing 효과는 미검증**이다.
- 새 EV/거래일/표본 floor, 매 청산 양수 요구, 전량 target terminal 허들을 추가하지 않았다. 실제 BUY-lot 매도 label 수집을 전제하는 달성 불가능한 조건 대신 명시적 owner 회계 배분과 group-level 수량/비용 귀속을 후속 설계 경계로 둔다. 소유권·pending BUY·freshness·broker guard와 최초 numeric envelope는 유지한다.
- 장후 진단의 기존 producer/consumer 연결은 코드/fixture로 닫았지만 자연 산출물은 재생성하지 않았다. 실제 **group coordinator→partial-cancel proof/registry reservation→runner SELL/terminal 원장**, pending BUY 취소·late fill, legacy/force-flat·전일 복구, 승인 envelope/검증기·PREOPEN/enrollment·실제 launcher는 남아 있다. 정확한 주문별 비용 consumer의 외부 계약 gap은 병행한다. 다음 첫 구현은 frozen group 회계 배분/receipt 계약과 실제 partial-cancel proof·예약 유지의 연결이며 현재 false 플래그를 단순히 true로 바꾸는 작업이 아니다.
- 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`를 재사용한다. source hash/계산 성공은 정책 승인·PID 소비·실체결이 아니며 이전 §12 완료를 재개방하지 않는다. 현재 운영 상태·정책·보유/주문·PID·장후 report·commit/push·재기동은 변경하지 않았다.

최종 검증 receipt(`18:45 KST`): 신규 group 전용 **60 PASS/0.79초**, source/study 직접 consumer 포함 **97 PASS/1.23초**, 전체 영향 회귀 **1430 PASS/4 owner-비대상 SKIP/37.97초**. 중복 포함된 검증 수는 합산하지 않는다. 0~20주 target 체결의 가능한 전체 두-lot 배분, 취소 중 late/full fill·부분취소, ACK/잘못된 terminal·수량/날짜/정책/owner 결손, 같은 target 중복 방지, 현재 lot 누락/가격 변경, study와 Markdown handoff를 확인했다. Ruff·compile·`git diff --check`·print-only parser 통과, parser36개 중 기존 acceptance owner는1개다. `korstockscan-review-gate`에 따라 원 source→group 계산/현재 원장 대사→census/study/Markdown과 실제 단일-lot/registry의 미지원 경계를 재리뷰했다. **이번 계산·source 진단 범위의 미해결 finding0**이며 미구현 partial-cancel proof/registry/coordinator·live 활성화는 OPEN이다. 병행 사용자 변경은 보존했다.

## 14. 부분취소 확인과 원장 예약 보존 연결

§13의 다음 액션 중 **정상 부분취소 요청의 확인 증거→공통 원장 예약 계산**을 구현했다. 단순 계산 객체가 아니라 기존 `RegisteredSellAdapter`의 당일 상세/미체결 조회와 `OrderOwnerRegistry`를 연결한 opt-in 코드다. 실거래 호출·현재 원장 수정·서비스 설치·정책 활성화는 실행하지 않았다. group coordinator/runner 매도 전체 구현 완료가 아니다.

### 구현·재리뷰 범위

1. `reconcile_partial_cancel`은 exact owner/position/account·dated target/cancel·symbol/route·적응형 정책 hash에 결속된 기존 취소만 읽는다. 기존 `kt00007 → ka10075` bounded pagination을 재사용한다. 취소 ACK, source-only `CancelAccounting`, 미체결 목록에서 사라졌다는 사실만으로 예약을 해제하지 않는다.
2. 이번 지원 계약은 **원 목표주문은 일부 잔량이 살아 있고, 요청한 부분취소 수량 전부가 확인된 경우**다. dated cancel의 원주문·수량·`cnfm_qty`/유효 확인시각·체결0/잔량0, current cancel 부재, 당일 두 root의 같은 누적체결/잔량 및 `원수량 = 체결 + 살아 있는 목표잔량 + 누적 확인취소`를 모두 대사한다. API의 접수/거절/정정 상태 문자열을 추정하지 않는다. source 품질·조회창 freshness·당일 account/date 및 lock 내 journal generation을 다시 검증한다.
3. `SELL_PARTIAL_CANCEL_RECONCILED` 한 건의 append/fsync로 **target는 ORDER_BOUND 유지·취소 요청은 확인 종료·canceled_qty 누적**을 투영한다. 두 별도 기록 사이 crash로 target 예약만 풀리거나 같은 cancel이 재시도 가능해지지 않는다. 신규 SELL과 승인된 수동 청산 귀속의 기존 예약 계산은 `원수량−체결−확인취소`를 사용한다. 이 수량은 주문 가능한 여유의 상한이지 runner 선택·주문 승인이나 lot별 실제 매도 귀속이 아니다.
4. 같은 proof 재조회/재시작은 이중 해제를 하지 않는다. 순차 부분취소는 각 cancel ID를 별도로 확인하고, 확인 후 자연 체결 증가는 취소 누계를 유지한다. 이후 fill이 이미 취소된 수량까지 침범하거나 오래된 broker root가 취소 잔량을 되살리는 반례를 거절한다. 조회 중 fill/terminal·owner/account/policy 변경, 누락/모순 page·일부만 확인·저장 실패도 검증했다. 금액/비용은 추정 보간하지 않는다.
5. 재리뷰에서 발견한 취소 후 과체결 허용, 구 root의 예약 부활, 반복 확인 중 late fill 갱신 막힘, 수동 귀속 consumer의 구 예약 계산을 보완했다. 기존 single-lot `submit_owned_sell`의 전량 target terminal guard는 그대로이며 새 group 경로에 이를 잘못 재사용하지 않아야 한다. 실제 owner 루프는 아직 새 opt-in partial primitive를 호출하지 않는다.

공식 참조는 구현 전 upstream `main` 조회로 SHA `234560d213acd8871ae344b5481aecd2f30287fa`를 확인하고, `2026-09-09T19:01:58+09:00` 최종 조회에서도 같은 SHA를 재확인했다. `kiwoom/specs.py`, packaged spec의 `kt10003/kt00007/ka10075` 전체 요청/응답, `kiwoom/core/client.py`의 요청·오류·pagination, Postman의 해당 세 endpoint 운영/모의 request를 읽었다. 이 revision의 `kiwoom_docs` 부재는 유지된다. 확인수량 필드 하나가 terminal을 의미한다고 가정하지 않고 위 수량/identity 교집합만 지원하며, 미정의 상태/일부확인/정정 변형은 승격하지 않는다. 실제 주문 example·계좌 조회는 실행하지 않았고 호출 상한·retry·계좌/가격 safety를 바꾸지 않았다.

### 목적·조건·남은 연결

- 기대효과: 정상 부분취소 뒤 전체 목표주문 종료를 기다리는 구조적 막힘과, 남은 목표수량까지 예약 해제해 중복 매도하는 위험을 함께 줄이는 기반이다. **작은 비용 후 수익의 빈도·순이익·자본회전 개선은 아직 미관측**이다.
- 양수 EV/새 거래일·표본 floor, 모든 조기청산 양수, 실제 BUY-lot 매도 label 같은 추가 허들은 없다. 이번 `요청량 전부 확인`은 지원된 증거 형태의 경계다. 취소 중 체결로 요청 일부만 확인되는 경우·거절/전일 복구는 **미완료 구현/계약**으로 남기며 달성할 수 없는 수량을 계속 기다리는 정상 대기로 포장하지 않는다. 원 target가 전량 terminal이면 기존 whole-target 대사 owner의 범위이지 본 부분예약 primitive의 성공조건을 강제할 대상이 아니다.
- 다음 구현은 **동결 owner 회계/runner 배분→단일 group coordinator가 이번 proof와 예약을 소비→runner SELL/terminal 및 기존 owner handoff**다. pending BUY 취소/late fill·legacy/force-flat·일부취소/거절·미해결 전일 복구, 최초 numeric envelope/독립 validator·PREOPEN publisher/enrollment·실제 launcher는 별도 미완료다. 정확한 주문금액/비용 원천 계약 gap도 유지한다.
- 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`를 유지한다. 장후 census/study의 `shared_target_runtime_supported=false`를 true로 뒤집지 않았다. 현재 group의 연구 제외·자연 표본 상태도 변경하지 않았으며 운영 report 재생성·PID/env/정책/주문·commit/push/재기동은 없다.

최종 검증(`19:04 KST`): 영향 회귀 **1518 PASS/4 owner-비대상 SKIP/43.46초**. 그 뒤 테스트만 추가한 저장 직후 응답 유실 반례를 포함해 broker/공통 registry **306 PASS/9.13초**이며 두 수를 합산하지 않는다. Ruff·compile·`git diff --check` 및 print-only parser 통과(36개, 기존 acceptance owner1개). 마지막 재리뷰에서 멱등 확인도 신규 unbound cancel·journal generation을 검증하도록 보완했다. `korstockscan-review-gate`로 adapter 원천→잠금/CAS·단일 append→SELL/수동 귀속 예약·기존 single-lot 소비 경계를 확인했으며 **이번 부분취소 확인/예약 보존 범위 미해결 finding0**이다. 미구현 group 실행·부분확인 복구·최초 활성화와 자연/경제성은 위 OPEN 범위로 남는다. 병행 사용자 변경은 보존했다.

## 15. 동결 runner 배분과 group 증거 소비 coordinator

§14의 다음 액션 중 **명시적 회계 배분 동결→단일 target 슬롯→기존 부분취소 proof 소비**를 구현했다. 신규 `src/trading/order/adaptive_exit/group_runtime.py`는 공통 주문 owner 패키지에 둔 opt-in coordinator이며 engine-root/새 producer가 아니다. 실제 owner의 launcher/enrollment·주문 발행 호출자는 추가하지 않았다. 아래의 fake transport 검증은 실거래 실행 receipt가 아니다.

### 구현·review/fix 범위

1. `RunnerAllocation`은 group source hash·정책 hash·승인 receipt hash, runner lot 집합과 전체 lot 우선순위를 필수로 받는다. 지원 규칙 `nonrunner_first_then_runner_in_declared_lot_order_v1`은 **원 목표 체결을 nonrunner부터, 각 집합 안에서는 선언한 순서대로 기록하는 내부 수량 회계**다. 기본 FIFO/비례 배분이 아니며 자동 선정·승인값도 아니다. `target_book_filled_qty`와 `book_open_qty`로 표시하고 실제 broker BUY-lot별 매도 귀속·손익은 null로 분리한다. 첫 체결 시각/가격은 group 원천을 바꾸지 않는다.
2. `GroupCoordinator.freeze`는 승인/enrollment 및 custody callback·원 owner 잠금 아래 group의 모든 BUY 주문번호/수량과 target를 원장에 대사한다. 기존 adapter의 당일 fresh 상세/미체결 수량을 확인하고 **취소 전에** 불변 배분과 최초 수량을 원자 저장·read-back한다. 저장 슬롯은 account×dated target이며 정책·lot가 달라졌다고 새 슬롯을 만들지 않는다. callback은 실제 durable/CAS 저장과 single-lot/group 중복 enrollment 배제까지 소유해야 한다. 실제 launcher 공급은 미완료다.
3. 동결 binding에서 결정한 client ID의 이미 접수된 취소만 `bind_cancel`이 결속한다. 그 ID가 없거나 ambiguous/rejected이면 주문번호 추정·재전송·사후 동결을 하지 않는다. coordinator에는 주문 전송 메서드가 없다. 명시적 부분취소 action의 실제 driver/guard 연결은 다음 구현이다.
4. `reconcile`은 §14의 `RegisteredSellAdapter.reconcile_partial_cancel`→registry 단일 append를 소비한다. exact target/cancel intent·정책·source contract·저장 proof·누적 취소·현재 체결을 대사하고 **목표 예약잔량 + runner 해제수량 + 목표 체결 = 최초 수량**을 닫는다. `RELEASE_RECONCILED`는 해당 시각의 수량 receipt일 뿐 현재 주문가능 잔고가 아니며 `sell_authority=false`다. 후속 SELL은 원장 예약·가격/TTL/전체 guard를 다시 검증해야 한다.
5. 취소 확인 원장은 저장됐지만 group 저장이 실패한 경우 재시작은 같은 exact 취소를 소비해 복구하며 이중 해제하지 않는다. nonrunner 목표 추가 체결은 동결 runner를 다시 배분하지 않는다. 재리뷰에서 저장 **전** schema/시각 검증과 날짜 경계, 생성 후 adapter 정책/context·배분·freshness bound 변경에 대한 승인 재사용 방지를 보완했다. hash 재계산된 잘못된 상태·실제 귀속/SELL 권한 혼입도 차단한다.

공식 참조는 구현 전 `2026-09-09T19:10:42+09:00` upstream `main` 조회의 SHA `234560d213acd8871ae344b5481aecd2f30287fa`다. `kiwoom/specs.py`, packaged `kt00007/ka10075/kt10003` 요청/응답, `kiwoom/core/client.py` 요청·pagination·오류 처리와 Postman 운영/모의 envelope를 대사했다. `kiwoom_docs`는 해당 revision에 없다. 기존 wire/parser/상태 의미·호출 상한은 변경하지 않았고 실제 API 조회/취소/주문은 실행하지 않았다.

### 목적·달성 가능성과 남은 실행 연결

- 기대효과는 공유 목표주문을 lot별로 중복 관리하거나 정상 부분취소 이후 남은 목표 예약까지 풀리는 오류를 예방하고, 재시작 후에도 같은 runner 수량을 보존하는 것이다. 비용을 차감한 작은 수익 빈도·EV/순이익·회전 개선은 아직 실측하지 않았다.
- 실제 broker가 제공하지 않는 BUY-lot 매도 label, 별도 양수 EV·추가 거래일/sample floor·모든 조기청산 양수 같은 허들을 추가하지 않았다. 이번 회계 규칙을 사용하려면 **정책에 명시하고 기존 최초 승인 envelope/독립 validator로 승인해야 한다**. 코드 지원 자체가 승인 범위를 넓히지 않는다.
- 이번 경로는 취소 요청 전량이 확인되고 nonrunner 목표잔량이 남는 경우다. 목표잔량이 모두 체결됐거나 남은 목표 전체가 runner인 경우, 일부 취소만 확인·거절/미확인/전일 상태는 `requires_owner_recovery`/직접 결손으로 분리한다. 이를 무기한 정상 대기 또는 자연 표본 부족으로 숨기지 않는다. whole-target/terminal 경로를 아직 group coordinator로 연결하지 않은 구현 경계이며 해당 종목 자체를 영구 제외하자는 조건이 아니다.
- **다음 직접 구현:** 동일 동결 group에서 조기청산/trailing 판단→단일 부분/전량 취소 action→해제된 runner의 bounded SELL/TTL·terminal 및 원 owner handoff. pending BUY 취소/late fill·legacy/force-flat·전일/거절 복구와 정확한 주문별 비용 consumer는 별도다. 최초 numeric envelope/독립 validator·PREOPEN publisher/enrollment·실제 launcher도 미완료다.
- 기존 `MachineLifecycleTurnoverObjectiveFollowup0909`에서 이어간다. source-only census/study의 `shared_target_runtime_supported=false`/경제성 제외는 유지한다. 기존 single-lot driver/owner-loop·정책/PID·운영 원장·주문·cron/systemd·장후 report·commit/push/재기동은 변경하지 않았다. 코드 지원·실제 자동화 연결·자연/경제성 완료를 분리한다.

검증 receipt는 아래 최종 회귀 결과를 따른다. 전용 테스트는 **110 PASS/4.86초**, 앞선 broker/group 회귀는 **390 PASS/11.09초**이며 포함 관계가 있어 합산하지 않는다. 2/3-lot 모든 누적 수량·선언 우선순위·late fill·ACK/일부확인·owner/account/date·정책 변경·저장 전후 실패/응답 유실·중복 슬롯·손상 상태를 확인했다.

최종 영향 회귀: **1629 PASS/4 owner-비대상 SKIP/48.23초**. Ruff/format·compile·`git diff --check`·print-only parser 통과(36개, 기존 acceptance owner1개). `korstockscan-review-gate`로 group 원천→명시적 동결/승인·durable/CAS 저장→기존 adapter/registry proof→비권한 수량 receipt 및 아직 연결되지 않은 single-lot/owner-loop 경계를 재리뷰했다. **이번 배분·group 증거 소비 범위의 미해결 finding0**이며 위의 미완료 실행·최초 활성화·자연/경제성은 완료로 바꾸지 않는다. 실제 환경 호출/원장 변경 없이 fake transport·격리 임시 원장으로 검증했고 병행 사용자 변경은 보존했다.

## 16. Group 부분취소와 첫 runner SELL·TTL 연결

§15의 다음 액션 중 **승인된 action receipt→첫 부분취소→해제량 전부의 첫 지정가 runner SELL→TTL 취소/runner 수량 종료**를 구현했다. 위치는 기존 주문 owner 패키지의 새 `group_execution.py`, 기존 `broker.py`와 새 전용 테스트다. 실제 group 판단 producer·owner loop/launcher/enrollment를 연결한 것은 아니며, 선택된 장후 지시문을 실행하거나 원 보유를 새 청산에 이관하지 않았다.

### 구현·직접 consumer와 리뷰 보완

1. `GroupRunnerExecutor`는 실제 승인 numeric bounds와 승인 receipt hash, 독립 `authorize_action`, 원 owner의 lock/atomic CAS 저장을 필수로 받는다. 임의 TTL/가격/정책 기본값이나 항상 승인하는 실제 validator는 없다. `RELEASE_RUNNER / SELL_RUNNER / CANCEL_RUNNER_TTL`마다 불변 source/decision hash·시각·dated predecessor·수량을 **전송 전에** 저장/read-back한다. hash 하나를 승인으로 인정하지 않고 실제 group/lot 판단·depth/가격·loss/custody/manual/broker safety는 필수 validator가 검증해야 한다. 그 실제 공급자는 아직 없다.
2. 취소는 §15의 동결 deterministic client ID와 승인 수량을 사용한다. 첫 SELL은 새 opt-in `submit_partial_cancel_residual`에서 당일 상세/미체결→기존 partial proof와 원장 수량을 다시 확인한 뒤, **확인된 취소량만** 기존 NEW SELL reserve에 전달한다. 남은 원 target는 ORDER_BOUND/예약 유지다. single-lot `submit_owned_sell`의 전량 predecessor terminal 조건은 완화하지 않았다. 다른 예약을 빼고 남은 원장 수량이 부족하면 차단하며 새 action ID로 같은 predecessor를 다시 쓰지 못한다.
3. action 저장 전후 실패·응답 유실은 전송 전에 멈춘다. 원장에 같은 intent가 없을 때만 같은 fresh action으로 재개할 수 있고, reserved/ambiguous/rejected/ACK가 있으면 무재전송 대사/복구다. 같은 action의 가격·수량 변경, 다른 승인 bounds로 기존 슬롯 재사용, 외부 취소의 사후 채택을 차단한다. 주문 ACK는 terminal이 아니다.
4. 첫 runner의 fresh 잔량만 TTL 취소한다. action 저장 후 추가 fill로 잔량이 줄면 이전 큰 취소수량을 전송하지 않으며 이때의 수량 갱신/후속 재시도는 아직 복구 계약 미완료다. runner의 exact dated/current→registry terminal proof는 account/owner/position/date/order/client/route/수량/계약을 대사한다. 전량 runner 체결과 terminal 부분체결 잔량을 구분하고 **둘 모두 `group_terminal=false`**, 비용/실현손익 null이다. 원 target 및 group 전체 종료·다음 기존 진입 handoff를 대신하지 않는다.
5. 재리뷰에서 부분취소 후 미매도 대기의 deadline이 반복 대사/재시작으로 늘어나지 않도록 했다. durable 취소 요청시각을 보수적 시작점으로 명시하며 실제 broker 취소시각을 발명하지 않는다. 결손/기한 경과는 recovery이지 강제 매도·호가 guard 해제 권한이 아니다. 원장 reserve/fsync 중 승인·날짜/시세가 바뀌는 경우도 **등록 후 전송 직전 guard**로 차단한다. 새 partial source의 age도 저장 대기 후 다시 확인한다. 이미 저장된 reservation은 사후 재전송하지 않고 복구 대상으로 보존한다. validator는 자기 intent의 예약과 다른 주문 commitment를 구분하는 재실행 가능한 검사여야 한다.

### 공식 API·권한·남은 작업

- Official Reference Gate: upstream `main`을 `2026-09-09T19:29:04+09:00` 재확인했고 SHA는 `234560d213acd8871ae344b5481aecd2f30287fa`다. `kiwoom_docs`가 없는 revision임을 확인하고 `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`의 `kt10001/kt10003/kt00007/ka10075`, `kiwoom/core/client.py`, Postman production/demo의 해당 envelope를 읽었다. 새 호출량/retry/시장가·0수량 취소·추정 상태 enum을 도입하지 않았으며 검증은 fake transport/격리 임시 원장뿐이다.
- 목적은 해제량 초과매도·중복 취소/SELL과 runner 종료의 전체 flat 오인을 막는 것이다. 작은 비용 후 수익의 빈도·누적 순익·자본 회전 개선은 실측하지 않았다. 새 양수 EV/실제 청산 표본/거래일 floor나 broker가 제공하지 않는 lot별 매도 label을 승인 허들로 추가하지 않았다.
- **다음 직접 구현:** 실제 group-level 조기청산/trailing 판단 receipt producer와 whole-target 전량/완료 분기, TTL 뒤 residual·일부취소/거절 복구, group 전체 수량 terminal→기존 owner handoff. 현재 한 번의 정상 부분취소/첫 runner 주문 지원을 전체 exit 구현 완료로 바꾸지 않는다. pending BUY 취소·late fill, legacy/force-flat·미해결 전일 복구도 OPEN이다.
- 최초 numeric envelope/독립 validator·PREOPEN publisher/enrollment·실제 launcher는 여전히 미완료다. 실제 source-only census/study 지원 false/exclusion, 기존 single-lot/위젯/episode owner 분리를 유지했다. 정확한 주문별 금액·수수료/세금 consumer는 외부 원천 계약 gap이며 수량 종료와 별개다. 새 live 활성화·실주문/취소·현재 원장/보유 수정·PID/env/정책/cron/systemd 변경·재기동·장후 report 재생성·commit/push는 실행하지 않았다.
- 기존 OPEN `MachineLifecycleTurnoverObjectiveFollowup0909`에 후속 근거를 남겼다. 코드 수리·배포·자연 소비·경제성을 각각 확인하며 병행 사용자 변경은 보존했다. 검증 최종 receipt는 아래에 기록한다.

최종 검증(`19:47 KST`): 신규 전용62개를 포함한 전체 영향 회귀 **1691 PASS/4 owner-비대상 SKIP/52.48초**. SKIP은 widget catalog/episode terminal loop 및 episode manager/widget daily cap의 다른 owner 조합이다. 중간 원장 회귀의 예상 오류 문자열 불일치는 테스트를 실제 `sell_quantity_exceeds_owner_available` 계약에 맞춰 수정했고 수량 guard는 유지했다. Ruff/format·compile·`git diff --check`·print-only parser 통과(36개, 기존 acceptance owner1개). `korstockscan-review-gate`로 action source/필수 승인→동결 저장/재시작→adapter/atomic registry→TTL·exact runner terminal 및 아직 미연결인 group owner 소비 경계를 재검토했다. **이번 첫 부분취소/runner SELL·TTL 수량 실행 범위의 미해결 finding0**이며 group 전체 구현·최초 활성화·경제성 완료는 아니다. 검증 코드 SHA256은 `broker.py=b90d6a639d8491f55aab6b4562e01cd9a4c167af83e035445f810845d76a3cf1`, `group_execution.py=863d15059deea21f013b9f7f608fe4642281d04576bdb79a6ef421b8081218bc`다. 실제 runtime receipt로 재사용하지 않는다.

외부 Project/Calendar sync는 실행하지 않았다. 필요할 때 사용자가 실행할 표준 명령은 다음 하나다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
