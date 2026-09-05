# Low-price two-leg tuning / expanded recommendation final review — 2026-09-05

## 보완 구현 판정 — 2026-09-05 (아래 재점검 finding의 후속)

사용자의 후속 구현 요청으로 LP-F1~F5를 보완했다. 기존 두 필터축을 유지하고
새 실주문 권한은 추가하지 않았다. 아래 미해결 finding 목록은 발견 당시 기록이며
현재 코드 상태는 이 절이 우선한다.

- LP-F1: report v7 / candidate v3는 source-date 실제 applied policy와 전체 artifact
  hash, report/SQ snapshot을 결속한다. 0표본·허위 mutation·mutation 목록에서 숨긴
  정책 변경·legacy schema downgrade를 거절한다. 과거 후보가 미소비/잘못된 경우에도
  그것을 현재값으로 삼지 않는다. CLI report→candidate→PREOPEN 임시 통합 경로를 검증했다.
- LP-F2: 과거 실제 거래 부분집합의 단독 신규 tightening 권한을 제거했다.
  표본/EV 조건은 `diagnostic_economic_conditions_passed`이며 `ready=false`다.
  `hold_source_quality`, `hold_inventory_custody`, `hold_sample`,
  `hold_no_edge_in_observed_subset`, `hold_source_gap_causal_path_required`를 구분한다.
  기존 expanded producer의 `existing_axis_economic_replay`가 현재 적용 필터와 두
  bounded 대안의 독립 최초 신호/진입 경로·동일기간 순이익을 source-only로 계산한다.
- LP-F3: calibration 선택을 순이익/관측일 우선으로 바꾸고 holdout 순이익 증가와
  양수 EV를 함께 확인한다. current/selected 원시 full episodes를 보존하며
  날짜·관측일 수·비용 계약이 다른 비교는 거절한다. 추천 consumer는 paired
  comparison을 재계산한다. 거래당 EV만 오른 거래 감소/순이익 감소 반례는 탈락한다.
- LP-F4: 연구가 clean prefix의 HELD를 다음 날짜 및 half/holdout까지 보존한다.
  외부 custody 해소 근거 없이 재진입/미래 bar touch 청산을 만들지 않는다.
  `custody_blocked_dates`, `carry_in_held_legs`, `custody_resolution_required`를
  기록하며 미실현 mark와 실현손익을 합치지 않는다. 캐시 episode도 변조하지 않는다.
  마지막 재리뷰에서 같은 분봉 캐시를 다른 lookback에서 재사용할 때 관측
  drawdown/near-low가 이전 후보의 값으로 남는 provenance 결함도 수정했다.
- LP-F5: 새 연구의 모든-half-양수/half별 3-leg 조건을 진단으로 내렸다.
  calibration 전체 6 episodes/8 legs, holdout 3 episodes/4 legs 및 양수 경제성은
  유지한다. 기존 격리 중 CJ CGV/영원무역은 전체 경제성 실패가 아닌 half 재검토·
  새 승인 필요로 분리한다. SK텔레콤의 전체/holdout 음수는 여전히 경제성 실패다.

권한 판정: 실제 적용 정책의 자동 carry/PREOPEN 경로는 유지한다. **새 필터 변경의
자동 live 승격은 복구했다고 주장하지 않는다.** 부분집합 증거는 그 권한을 가질 수
없고 minute-bar paired 연구도 source-only다. 새로운 실권한은 검증된 실체결/승인
계약이 필요하다. 기존 50 loader-ready/3 격리 artifact·timer·봇·주문은 이 구현에서
변경하지 않았다. 외부 custody 해소/미기록 실체결을 가상으로 채우지 않은 source gap은
코드 성공 또는 수익개선 증거로 바꾸지 않는다.

최종 검증: 저가주/entry research/expanded/wrapper/verifier/microstructure/
entry-timing/checklist parser **692 passed in 15.60s**. 관련 Ruff, Python compile,
shell syntax, `git diff --check`를 통과했다. CLI→candidate→PREOPEN 임시 경로 및
최초 발견 반례를 회귀테스트로 포함했다. 최종 코드 리뷰의 구현 범위 내 미해결
finding은 0건이며 자연 실체결/외부 custody/새 live 승인 증거는 이 판정 밖이다.

실제 운영 파일의 읽기 전용 대사는 `validate_applied=(True, valid)`, loader
50 ready/3 quarantine, 기존과 같은 policy hash 및 mutation 0이다. 기존 9/4
source chain도 `pass_with_runtime_quarantine`이며 새 운영 report를 생성하지 않았다.
다음 자연 증거 owner는 `LowPriceEconomicReplayNaturalEvidence0907`이다.

## 최종 재점검 판정 — 발견 당시 기록 (2026-09-05)

**보완 필요. 자동화 연결 확인과 경제성/승인 결함 종결은 다르다.** 아래 1차
구현 기록의 테스트 통과는 유지하지만, 기대효과 및 runtime 승인까지 결함이
없다는 해석은 철회한다. 이번 재점검은 읽기 전용 코드·산출물 검사와 임시
fixture 재현이며 운영 policy, 봇, 주문, timer 또는 보고서를 변경하지 않았다.
이 문서와 다음 체크리스트의 리뷰/보완 owner만 갱신한다.

### 목적과 실제 적용 상태

- 목적: 비용 차감 작은 이익을 반복 확보하여 EV와 동일 관측기간 순이익을
  함께 개선한다. 거래당 EV가 높다는 이유만으로 거래 감소·순이익 감소를
  개선으로 인정하지 않는다. 실현손익과 HELD 미실현손익은 분리한다.
- 기존 두 필터축: postclose `build_candidate` → PREOPEN `build_applied_policy`
  → profile preflight → `service._profile_with_applied_policy` → signal provenance가
  연결되어 있다. systemd의 다음 2026-09-07 preflight/live 예약도 확인했다.
- 확장 추천: `_recommendation_rows`는
  `source_only_requires_review_and_user_approval`, `runtime_effect=false`다.
  신규 profile/시간대/실행계획의 자동 연구·추천과 실제 신규 기계 생성/승인은
  다르다. 현재 13개 revision은 명시적 기존 사용자 승인이지 일반 추천의
  무인 live 승격 증거가 아니다.
- 2026-09-07 파일은 inventory 53, loader ready 50, 격리 3,
  `policy_mutations=[]`이며 `candidate_validated_profile_revision_applied`다.
  **50개 실제 실행 또는 튜닝 수익개선의 증거가 아니다.** 자연 authority,
  runtime policy receipt, 실제 완료손익 확인은 기존 OPEN owner가 소유한다.

### 미해결 finding과 acceptance

1. **LP-F1 / P1 — 경제성 근거가 없는 후보를 PREOPEN이 수용한다.**
   `policy_runtime.validate_candidate`는 policy/report/source-quality hash와 범위를
   검사하지만 report에서 선택·경제성·sample 조건을 재계산하지 않는다.
   빈 state로 생성한 정상 2026-09-07 report를 유지한 채
   `samsung_heavy_midday.rolling_high_drawdown_pct`를 `0.75 → 1.00`으로 바꾸고
   policy hash/mutation lineage만 맞춘 임시 후보가
   `validate_candidate(require_source_files=True)=(True, valid)` 및
   2026-09-08 `build_applied_policy=candidate_applied`를 통과했다. 모든 자료는
   임시 디렉터리에 두었고 gateway/주문은 호출하지 않았다.
   - 보완: 원천 report와 실제 적용 기준정책에서 deterministic 선택 결과를
     재계산하고 profile/axis/before/after/표본/경제성/owner를 후보와 대사한다.
     단순히 candidate의 `ready`나 추가 self-hash를 신뢰해서는 안 된다.
   - Acceptance: 0표본, ready=false, 타 profile/axis, 허위 uplift, 미적용 prior
     정책 후보는 apply에서 거절하고 정상 bounded 후보만 통과한다.
   - Owner: `src/trading/low_price_two_leg/policy_runtime.py:724`,
     `src/engine/automation/low_price_two_leg_policy_apply.py:82`.

2. **LP-F2 / P1 — 기존 튜닝의 부분집합 계산과 새 일평균 순이익 조건이 충돌한다.**
   `_axis_outcome`은 과거 최초 실제 시도만 필터링한다. 변경된 필터에서 나중에
   발생할 신호/진입가격/체결/보유·청산을 재현하지 않는다. tightening 후보는
   현 정책 표본의 부분집합이고 분모는 같으므로, 모든 기존 거래의 순이익이
   비음수가 되면 후보 순이익의 엄격한 증가가 수학적으로 불가능하다.
   합성 12일 재현에서 EV `0.06% → 0.10%`, 완료 24→12 legs로 좋아 보여도
   순이익/일은 24→20으로 줄었다. 이 감소를 차단하는 조건 자체는 옳다.
   문제는 개선된 다음 진입 경로를 계산할 생산자가 없다는 점이다.
   - 보완/제거 검토: 부분집합 결과의 개선 입증/단독 live 판정 역할을 제거하고
     진단으로 유지한다. 기존 두 필터와 기존 minute-bar 연구를 재사용하여
     같은 날짜·정책·비용의 current/candidate 전체 경로를 비교한다. 새 튜닝축,
     수량, target, stop을 추가하지 않는다. 재현 결과의 source-only 권한과
     실체결 확인은 분리한다. 순이익 증가 조건을 삭제해 EV 착시를 재허용하지 않는다.
   - Acceptance: 양수 거래 일부 삭제는 개선으로 승인하지 않고, 늦은 신호에서
     실제로 더 나은 경로가 생기는 fixture를 독립 계산하며 missing 경로는
     `hold_source_gap`, 구조적 무개선은 `hold_no_edge`로 구분한다.
   - Owner: `src/engine/monitoring/low_price_two_leg_tuning.py:1294`, `:1780`.

3. **LP-F3 / P1 — 확장 추천에는 동일기간 순이익 감소 방지가 적용되지 않았다.**
   연구 선택과 추천 정렬은 robust/per-trade EV 위주이고 기존 튜닝에 추가한
   source-valid 관측일당 순이익 계약과 다르다. 실제 2026-09-04 추천에서:

   | 기존 로직 추천 | holdout 신호 current→candidate | EV current→candidate | 모의 순이익 current→candidate |
   | --- | --- | --- | --- |
   | NHN late-morning | 9→4 | 0.231821%→0.303967% | 2,866.0→1,609.2 |
   | 삼성E&A afternoon | 9→3 | 0.175561%→0.185722% | 1,490.6→529.4 |
   | 한세실업 morning | 9→6 | 0.171547%→0.176767% | 281.8→194.62 |

   위 수치는 구형 0.20% 비용의 동일 holdout 연구 출력이며 leg당 1주 정규화
   모의 KRW이지 실계좌 순이익이 아니다. 현행 코드도 같은 선택 구조를 유지한다.
   0.23%로 selected 원시 leg를 재비용화하면 앞의 두 후보는 각각
   1,490.58/458.81이다. baseline 원시 episodes는 저장되지 않아 동일 정밀도의
   paired 재비용화가 불가능한 점도 근거 결손이다. source-only 추천과 현재
   실적용/실제 손실을 혼동하지 않는다.
   - 보완: 기존 로직 개선 lane은 current/candidate 원시 경로와 같은 관측기간의
     순이익·시도빈도·점유시간을 함께 보존·비교한다. EV만 오른 위 사례는
     `hold_no_edge` 또는 목적 trade-off 검토로 분리한다. 신규 시간대/종목은
     현존 동일 기계의 개선으로 허위 표시하지 않고 no-entry 기준과 구분한다.
   - Acceptance: EV 상승/동일기간 순이익 감소 fixture가 자동 개선 추천에
     들어가지 않으며 비용 버전이 양쪽에 동일하게 적용된다.
   - Owner: `src/engine/monitoring/low_price_two_leg_entry_spot_research.py:746`,
     `src/engine/monitoring/low_price_two_leg_expanded_candidate_research.py:632`.

4. **LP-F4 / P2 — 연구는 HELD를 날짜 간 이어받지 않는다.**
   `evaluate_candidate`는 날짜별로 첫 신호를 새로 평가한다. 실기계 `_roll_date`는
   기존 보유가 있으면 episode를 유지한다. 9/4 추천의 NHN afternoon 등에는
   HELD 발생일 뒤에도 후속 연구 episode가 있으나 그 전에 실제 보유가 해소될지
   재현하지 않는다. 따라서 연구 거래빈도/자금점유/EV를 실운영 가능성으로
   바로 해석할 수 없다. 모든 후속 거래가 불가능하다는 주장은 아니다.
   - 보완: 기존 no-stop/보유 custody 규칙을 날짜 경계까지 재현하고 HELD,
     no-fill, partial, 실제 해소 여부를 분리한다. 미해결 자금점유를 0 또는
     가상 강제청산으로 메우지 않는다.
   - Acceptance: 전일 HELD 미해소시 다음 날 신규 episode가 생기지 않고,
     해소된 시점부터만 현재 runtime 규칙에 따라 다음 기회를 평가한다.
   - Owner: `src/engine/monitoring/low_price_two_leg_entry_spot_research.py:666`,
     `src/trading/order/regular_two_leg_machine.py:1033`.

5. **LP-F5 / P2 — 모든 하위 기간 양수 조건과 고정 격리는 과잉 가능성이 있다.**
   `_research_cost_revalidation`은 calibration의 두 half, calibration 전체,
   holdout, full 모두 EV>0이어야 한다. 현행 0.23% 비용으로 재계산한 결과:

   | profile | 비양수 세부기간 EV | calibration 전체 | holdout | full |
   | --- | --- | --- | --- | --- |
   | CJ CGV morning | 전반 -0.004323% | +0.030287% | +0.116837% | +0.054061% |
   | 영원무역 midday | 후반 -0.000262% | +0.009584% | +0.025027% | +0.012238% |
   | SK텔레콤 midday | 전반 -0.003348% | -0.001478% | -0.017346% | -0.005668% |

   앞의 두 사례는 모든 기간 손실이 아니므로 3개를 동일한 경제성 실패로
   해석해서는 안 된다. exclusion은 9/7 이후 고정 목록이고 자연 표본 증가로
   자동 해제되지 않는다. 새 사용자 승인 revision이 release condition이다.
   - 완화 검토: 앞의 두 사례의 half 양수 조건은 robustness 진단/재검토로
     낮추고 동일기간 paired 순기여와 독립 holdout 확인으로 대체할지 검토한다.
     CJ의 HELD 경로 결손도 먼저 닫아야 한다. full/holdout까지 음수인 SK는
     단순 조건 완화 대상이 아니다. 이 리뷰로 격리를 해제하지 않았다.
   - Acceptance: 얇은 특정기간 부호와 전체 경제성 실패를 구분하고 승인된
     정책 범위 내 재검토/재격리/rollback 계약을 명시한다. 새 실권한은 별도 승인한다.
   - Owner: `src/trading/low_price_two_leg/preflight.py:564`,
     `src/trading/low_price_two_leg/policy_runtime.py:317`.

### 조건 달성 가능성 및 검증 한계

- 기존 9/4 report를 현행 `build_candidate`로 메모리 내 재평가한 결과:
  48 profiles, 93 alternatives, 후보 관측일 5일 충족 7개, broker-priced 완료
  8 legs 충족 0개, 양수 EV 42개, 일평균 순이익 증가 2개, 최종 ready 0개다.
  프로필별 current 최대 broker-priced 완료도 6 legs다. readiness 조건별 수치는
  각각 독립 집계이며 서로 합산할 수 없다.
- `5일/8 legs/+0.005%p`를 일괄 과도하다고 단정할 근거는 없다. 5일은 전체
  유효 관측일이 아니라 필터를 통과한 완료 가능 실제 시도일에 대한 floor다.
  표본 부족과 LP-F2의 구조적 불가능을 구분해야 한다. 표본확보 확률/완료일은
  현재 자료로 산출하지 않았으며 임의 floor 인하를 권하지 않는다.
- source-quality, broker/account/order/quantity, stale/price freshness, 현재
  held/unresolved custody, same-stage owner guard는 제거 대상이 아니다.
- 5개 targeted pytest 파일 재실행: **521 passed in 10.02s**. 하지만 LP-F1
  반례를 기존 테스트가 포착하지 못한다. 통과 개수는 이 finding을 무효화하거나
  수익 개선을 입증하지 않는다. 합성 검증은 실제 미래 체결/실적용 증거가 아니다.
- 리뷰 문서/체크리스트 검증: backlog 출력 parser 통과, 신규 OPEN owner 1건
  인식, parser targeted pytest **46 passed**, `git diff --check` 통과다.
- 다음 owner: `LowPriceFinalReviewRepairDecision0907`에서 우선 LP-F1 승인
  재검증, LP-F2/F3 경제성 판정 통합, LP-F4 carry 경로, LP-F5 조건 재설계를
  확정한다. 이번 review 범위의 코드 수정/격리 해제/봇 재기동은 수행하지 않았다.

## 1차 구현 확인 기록 — 아래 내용은 최종 재점검 판정에 의해 한정됨

목적은 새 튜닝축을 추가하는 것이 아니라 기존 profile별
`rolling_high_drawdown_pct`와 `rolling_low_proximity_pct` 축이 거래비용 차감 후
작은 순이익을 반복적으로 확보하도록 평가·자동 적용하는 것이다. 구현 후
postclose 생산자→후보→중앙 verifier→exact-date PREOPEN policy→profile preflight
연결은 자동화 가능 상태다. 단, 2026-09-04 승인 13개 중 현행 공통 비용계약으로
비양수가 되는 3개 profile은 런타임에서 제외한다.

## 근거

- 공통 비용: minute-bar 연구, actual-outcome 튜닝, 연구근거 재검증 및 authority가
  `low_price_two_leg_round_trip_cost_v1`, round-trip `0.23%`를 공유한다.
- 목적함수: 비용차감 순이익/전체 source-valid 관측일을 1차로 두고, notional EV,
  시도빈도, 점유 자본시간 수익을 보조지표로 유지한다. 후보가 발생한 날만 분모로
  세어 일평균 수익을 부풀리지 않는다.
- 표본계약: profile별 후보 관측일 5일, broker-priced completed leg 8개,
  후보의 양수 EV와 현 정책의 유효 EV, EV +0.005%p 이상, 일평균 순이익 증가,
  held/unresolved 0을 요구한다. 다른 symbol/session을 pooling하지 않는다.
- 재비용화: `cj_cgv_morning`, `youngone_midday`, `sk_telecom_midday`는
  calibration half/holdout/full 중 하나 이상이 비양수여서 격리한다. 다른 승인
  10개는 모두 통과한다.
- 적용계약: 53-profile 정책 inventory는 보존하되 3개를
  `runtime_quarantined_unified_cost_nonpositive`로 명시해 loader가 반환하지 않는다.
  나머지 50개만 runtime active이며 격리 preflight는 terminal exit 4로 끝나
  broker gateway를 생성하거나 반복 재시도하지 않는다.
- provenance: 향후 튜닝 report 자체 hash, candidate의 report hash 및
  source-quality 파일 SHA-256을 PREOPEN apply가 다시 검증한다.
- 수집 복구: 공식 Kiwoom `ka10080`의 symbol/date/request 계약과 bar content hash를
  per-symbol checkpoint에 결속한다. shared-read defer는 같은 continuation page에서
  bounded retry한 뒤 exit 75로 넘기며 postclose wrapper가 최대 3회 이어서 실행한다.
  이전 정상 report는 불완전 재시도로 덮어쓰지 않는다.
- 공식 참고 검증: `Kiwoom-Securities/Kiwoom-REST-API` commit
  `234560d213acd8871ae344b5481aecd2f30287fa`, 2026-09-05 21:30:56 KST.
  `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`,
  `kiwoom/core/client.py`, Postman collection 및 국내주식 분봉 예제를 확인했다.
  계약은 `POST /api/dostk/chart`, `api-id=ka10080`, `{symbol}_AL`,
  `tic_scope=1`, `upd_stkpc_tp=1`, `cont-yn`/`next-key`이다.

## 권한·잔여 확인

이 변경은 기존 두 진입 필터축과 source/report 자동화만 보완한다. quantity,
target, entry validity, stop/forced exit, provider, bot, cap, broker/account/order/
cooldown 및 hard-safety를 변경하지 않는다. 2026-09-07에는 50개 active profile의
자연 authority/runtime-policy receipt와 postclose 실제 순이익·EV·빈도 attribution을
관찰해야 하며, 자연 신호 0건 자체는 실패가 아니다.

## 검증 결과

- 저가주·연결 래퍼·중앙 verifier targeted pytest: `521 passed`. 중앙 verifier의
  Samsung v9 fixture도 현행 source-runtime-policy binding 계약으로 정리해 제외한
  테스트가 없다.
- Ruff, Python compile, 두 shell wrapper의 `bash -n`, `git diff --check`, checklist
  parser를 통과했다.
- 실제 2026-09-04 report/candidate/expanded-report 중앙 계약은 `status=pass`,
  `recommendation_implementation_status=pass_with_runtime_quarantine`, 승인 10건 통과,
  격리 3건, 기타 실패 0건이다.
- exact-date `2026-09-07` applied policy는 `validate_applied=(true, valid)`, inventory
  53개, loader ready 50개, terminal quarantine 3개이며 각 active policy hash 길이는
  64자다. 격리 profile read-only preflight는 exit 4를 반환했다.
