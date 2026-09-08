# 외부 census·#49 scanner submit drought 보완 리뷰

기준: 2026-09-08 KST. 범위는 저장된 원천의 진단·경제성 보고·기존 workorder 전달이다. 운영 env/lock, 주문·수량·안전조건, scanner 선택 surface, API 호출량, 봇 PID는 변경하지 않았다. 다른 작업의 AI·매매 코드 변경은 이번 검토 범위가 아니다.

## 판정

시장 포착률 진단을 경제성 승격과 분리하고 실제 거절을 승인 후 미제출로 오분류하던 결함을 보완했다. 정상 구간을 과거 결손과 함께 무기한 보류하지 않으며, 작은 비용 차감 수익의 대안을 비교할 수 있다. 다만 이는 **submit drought 원인 식별 개선**이지 매수 증가나 순이익 개선의 입증이 아니다. census는 source-only이고 #49의 승인된 기존 장전 자동 적용 경로는 유지한다.

## 구현·리뷰에서 닫은 항목

| 항목 | 보완 | 권한·해석 경계 |
| --- | --- | --- |
| Entry 결정 오분류 | `allowed=false`, REJECT, NO_BUY_AI, 관찰·advisory·unknown을 명시적 허용과 분리 | 거절 snapshot 존재만으로 submit safety 결손을 주장하지 않음 |
| 전역 보류 | v4 report의 venue/session별 정상 연속 capture 구간, master 불량 행·공백/미성숙 구간 제외, raw=eligible+excluded 보존식 | 3 capture/20 episode 기준은 유지. 경제성 floor·다른 scope 결손·미포착 자체는 정상 구간 진단의 차단조건이 아님 |
| 작은 순수익 비교 | 기존 검증 BBO에서 net +0.03/+0.07/+0.10% × 1/3/5/20분 대안, 완료·양수 건수·평균 시간·EV·결측을 분리 | 실제 호가 ask→bid와 기존 effective-dated 비교비용 사용. 추가 API 요청 0. 연속 first-hit·실체결·전시장 EV·실제 회전율을 주장하지 않음 |
| 자동 handoff | native recommendation ID + report v4 self-hash + exact date/엄격한 boolean authority → workorder producer v6 → 최종 JSON | `objective_followup_required` 원값을 보존하되 아직 결함이 입증되지 않은 진단은 `defer_evidence`; 반복 횟수만으로 implement-now 승격 금지 |
| 전달 회귀 | 통합시험에서 드러난 최종 serializer의 native ID/hash 누락과 격리 source fixture 경계를 보완 | 원본/후속 ID·hash·scope·acceptance를 최종 소비 단계까지 유지. 외부 implementation-status metadata를 완료 근거로 복사하지 않음 |
| 원본 검증·호환성 | self-hash 검증 전에 generic retirement projection이 audit 값을 고치지 않도록 원본 JSON을 보존. 기존 malformed JSON은 명시적 integrity 진단 | invalid 원본에 native recommendation ID를 발명하지 않으며 workorder 자체의 오류 ID와 구분. #49 진단 v2를 명시하고 정상 frozen v1은 원래 값으로 재현 검증 |
| #49 달성 가능성 | base/holdout별 표본 deficit와 불확실성의 조건부 필요 표본 민감도, 양수 edge 없음/증거 부족을 구분 | 미래 유입률·day cluster가 입증되지 않으면 finite ETA=null. 조건부 계산은 승인 floor 또는 성공 예측이 아님 |
| #49 빈도·유지 판단 | candidate/control에 공통 유효 source-day 분모와 0완료일 포함; 20유효일 또는 rollout+30일(10/2) 재검토 | 원천 부족 때문에 유효일이 늘지 않아도 유지 판단을 무한 연기하지 않음. 자동 OFF/lock 해제/표본 하향 아님 |

새 순수 helper는 live scanner가 아닌 `src/engine/monitoring/market_opportunity_review.py`에 둔다. root engine module, 병렬 매매 owner 또는 새 cron을 만들지 않았다. `korstockscan-review-gate`에 따라 producer→consumer→최종 serializer·반복 승격·runtime 경계와 관련 시험을 반복 점검했다.

## 저장된 당일 원천 재계산

13:11:51 KST, `build_report('2026-09-08')`를 메모리에서 실행했다. 운영 산출물은 덮어쓰지 않았다. self-hash 검증과 Markdown 렌더링, native workorder intake가 통과했다.

- schema: `market_opportunity_census_v4`
- 진단 generation hash: `57c34f03b1167751bb7f8f663aff9c7feac41a577b3da84b193ee4a29d26c6ee`
- status: `partial_diagnostics_ready`. 이 hash는 수동 진단 기록이며 자연 실행·현재 정책 receipt가 아니다.
- 032820 09:10, 289080 11:25, 052690 10:05 benchmark episode의 종전 승인 후 미제출 오분류는 모두 `entry_decision_rejected`로 정정됐다. 정확한 원천 결정과 일치한다.

| Scope | Raw / eligible / excluded | 진단 상태 | 해석 |
| --- | --- | --- | --- |
| KRX regular | 233 / 19 / 214 | 표본 기준 미달 | master 불량30, capture 공백/미성숙184. 유효19행은 따로 보고하며 보존식 차이0 |
| NXT premarket | 36 / 35 / 1 | 구간 진단 가능 | 유효35행의 promotion 미관측. 의도된 운영 제외와 실제 탐색 결손은 별도 판정 |
| NXT overlap | 233 / 84 / 149 | 구간 진단 가능 | 유효84행의 promotion 미관측. NXT 전체를 정상 또는 매수 누락으로 단정하지 않음 |

KRX 유효19행은 candidate-not-promoted12, late-discovery5, discovery-unobserved1, fast-precheck-gap1이다. timely promotion은1행이며 attach/fast/heavy 연결 결손1행이다. 완전한 fetch/pool census가 아니라 promotion/prune proxy라는 한계를 출력에도 명시한다.

KRX의 net +0.03% 대안을 별도로 보면 다음과 같다. 아래 분모는 **master-qualified 경제성 관측 집합**이며 위의 연속 capture 진단19행과 다르다. 모든 대안은 경제성 source floor 미달이고 실제 수익이 아니다.

| Horizon | Resolved / 양수 | 관측 집합 EV | 판정 |
| --- | --- | --- | --- |
| 1분 | 2 / 0 | -1.0477% | 얇은 표본·short BBO 결손 |
| 3분 | 7 / 1 | -1.2527% | 얇은 표본·short BBO 결손 |
| 5분 | 38 / 9 | -0.6921% | 경제성 품질 기준 미달 |
| 20분 | 74 / 32 | -0.1075% | 경제성 품질 기준 미달 |

희소 호가 사이 움직임은 복원하지 않는다. 추가 slippage를 0으로 둔 1주 표시 BBO 반사실이므로 실제 다주문 체결비용 대사나 미래 수익 보장이 아니다. 작은 목표라고 무조건 참여하는 방식의 이익 근거는 확인되지 않았다. 상승·반등 조건의 기존 owner별 검증과 결손 없는 경로가 먼저 필요하다.

세 scope의 native 진단 workorder가 생성되며 각각 `order_market_census_krx_krx_regular`, `order_market_census_nxt_nxt_premarket`, `order_market_census_nxt_nxt_regular_overlap`이다. 같은 날짜/hash/엄격한 비권한 계약으로만 intake한다.

## 자동화·문턱 최종 판단

1. census의 다음 정기 report가 v4 진단을 만들고 기존 장후 workorder가 소비한다. 새 호출 스케줄이나 장중 정책 변경은 없다. source-only 진단에 PREOPEN·실체결·양수 EV를 추가 gate로 요구하지 않는다.
2. #49의 고정 +0.10%p 제거는 앞선 `small_net_v1` 보완을 유지한다. 이번에는 실제 full-fill·독립 holdout·2SE·tail·원천/receipt 조건을 낮추지 않았다. 조건 통과 시 기존 exact-date PREOPEN에서 별도 사용자 재승인 없이 선택되는 경로의 회귀시험이 통과했다.
3. 조건부 표본 민감도는 시간이 해결할 수 있는지 확인하는 보조값이다. candidate 0건·유입 0·음수 edge를 무한 대기로 정당화하지 않는다. 20유효 source일 또는 10/2 유지·통합·폐기 검토를 체크리스트에 남긴다.
4. 전체 시장 fetch/pool 관측, KRX 수집 연속성, 짧은 horizon 호가, 실제 #49 candidate/control terminal 및 다음 PREOPEN/PID/순이익은 아직 자연 acceptance다. 이번 수리가 이 모두를 해결했다고 보고하지 않는다.

9/7 기존 #49 산출물의 메모리 진단에서도 base candidate0/control1, holdout0/0이었다. 새 진단의 필수 audit 교집합이 없어 공통 유효 source-day와 그 분모의 일별 net은 null이며, 과거 원천 관측일 수를 유효일로 대체하지 않았다. 조건부 필요 표본과 finite ETA도 null이다. 이는 기존 정책 재생성/승인 결과가 아니며 무표본을 기다리면 해결된다는 근거가 없음을 명확히 한 것이다.

## 검증·남은 확인

- census·새 helper·#49 net/resource/정책·workorder·runner 관련 341 tests 통과. small-net +0.04%p 차이의 synthetic 경제성 후보 → frozen PREOPEN → runtime bonus 및 별도 승인 불필요, 기존 frozen v1 호환 계약 포함.
- 기존 의존성 `pandas_ta`의 pandas Copy-on-Write deprecated 옵션 경고 1건은 별도다. 테스트 실패가 아니며 패키지 변경은 수행하지 않았다.
- 코드 syntax/compile, Black, `git diff --check`, 문서 print-only parser 통과. parser 33개 중 기존 자연 owner와 신규 10/2 유지 판단 ID가 각각 1회 포함됐다. 외부 Project/Calendar sync는 실행하지 않았다.
- 반복 리뷰·보완 후 변경 범위의 미해결 finding은 0이다. 전체 저장소 무결함이나 배포·자연/경제성 완료를 뜻하지 않는다.
- 기존 OPEN `ScannerLookupAttentionNaturalEvidence0908`과 장중 `RuntimeEnvIntradayObserve0908`에서 다음 자연 generation을 확인한다. 손익·source missing을 합성하거나 이미 누락된 과거 경로를 반복 실행하지 않는다.
