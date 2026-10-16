# 누적 보조 프롬프트 연구 1~6단계 실행·구현 검토 — 2026-10-16

Owner: 현재 체크리스트의 `DirectFamilySourceRepairCompactAuxiliary`. 연구 ID: `aux_prompt_research_20261008_01`. 상태: **실제 비교 완료, 전체 교체 비권고, 두 scope 개선 후보 인계, 배포 지시 대기**.

## 판단과 범위

사용자가 확인한 범위는 누적 보조 프롬프트 연구 1~6단계다. 의미적 감시기 재구현이나 장후 전체 재생성은 이번 실행에 포함하지 않았다. 마지막 지시의 “배포 지시를 대기”가 과거 배포·재기동 승인보다 우선한다. 운영 overlay 발행, current 정책 변경, 배포, 재기동은 수행하지 않았다.

67개의 동일 확인점에서 현행과 H6 후보의 실제 응답을 비교했다. 단순 합계 PASS 승률은 현행 **30/47(63.8%)**, 후보 **25/40(62.5%)**다. 후보의 전체 교체는 권하지 않는다. scope별 기존 기준인 승률 개선 또는 동률·TP 증가를 충족한 곳은 주성 AFTER/SOR와 기타 비삼성 PRE/2만~10만원/NXT 두 곳이다. 각각 2쌍·3쌍의 탐색적 결과이며 일반화나 통계적 확증을 주장하지 않는다. 고정 최소표본이나 EV 문턱을 추가하지 않았다.

## 1. 기준 고정과 원 증빙 대사

- 연구 기준 부모 bundle: `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`, effective date `2026-10-16`. 원 파일 SHA: `b1d9518d416ff623687daad4ceafed3534970e7a805c3644d591c5a38192bf46`.
- 기준 detector manifest: `2ce1ba47781ad9d58d0f0693c2bb58b68f33d21f411dbfd62e7a7dd42f789dca`. 현재 128 scope의 실제 보조 binding을 불변 reader capture로 고정했다. 현재 기계 membership과 누적 machine 보고서의 scope 목록이 일치했다.
- 격리 작업본은 `codex/auxiliary-cumulative-research-20261016`이다. 다른 세션의 배포 변경을 확인하여 기준을 `601717805c1da3697c5730ecb2ab55b9ca9878e7`까지 fast-forward했다. 기본 작업본의 미커밋 변경은 건드리지 않았다. 이 기준은 본 연구 코드의 배포 영수증이 아니다.
- 원천·요청·응답은 공유 store를 사용한다. 연구 설정·명시 campaign/evaluation은 연구 namespace 안에 두고 정기 장후 latest/config와 분리했다.

10/15 요청 284건, payload 896행, trace 790행을 파일별 한 번씩 읽고 SHA/크기/변경 여부를 대조했다. 283건은 원 request/envelope/compact wire/native scope 연결이 확인됐지만 trace의 과거 payload hash와 차이가 있었다. 별도 append-only 보강 증빙으로 남겼으며 원 trace·label·primary eligibility는 고치지 않았다. 1건은 원 request/trace 결손이고 orphan 요청도 별도 보존했다. timeout을 유효 판정으로 바꾸지 않았다.

최종 capture hash를 입력 재구성 hash로 덮지 않는 producer 수리는 기준 코드에 이미 있었다. 해당 코드의 실제 annotation/cache 경로 2개 회귀검증을 실행했다. 과거 잘못된 hash를 새 hash로 덮어 쓴 것은 아니다. 10/15의 기존 10분 라벨을 이번 30분 정답으로 재명명하지 않았다.

근거: [원 증빙 대사](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/binding-supplements-20261015.json).

## 2. 누적 전체 원천과 현재 기계 확인점

기존 AI 호출·PASS·제출점이 아닌 현재 기계 membership에 맞는 누적 확인점을 모집단으로 삼았다. 개정 producer 경계인 9/29 이전 자료는 과거 연구 보존용으로만 남겼다. 실제 보유 raw 날짜와 기존 normalized manifest를 다시 대조하는 기능을 추가했다.

그 결과 **10/13은 원천과 유효 closed epoch receipt가 있는데도 기존 누적 manifest에서 누락**된 것을 발견했다. 연구 전용 경로에서 해당 날짜의 raw 906,760행을 4개 partition으로 정규화하고 현재 FSM을 다시 실행했다. 확인점 1,401건 가운데 WIN 1건, `path_end_before_horizon` 1,400건이었다. 유일한 확정 확인점을 별도 실제 비교로 보충하고 기존 66쌍은 그대로 보존했다. canonical machine/source 보고서를 덮지 않았다.

| 항목 | 수량·처리 |
| --- | --- |
| 포함 원천일 | 9/29·9/30, 10/2·10/6·10/7·10/8·10/12·10/13·10/14·10/15 |
| 원천 partition/행 | 60개 / 7,402,594행; invalid row는 기존 source contract대로 경로 단절·제외 |
| 전체 등록 후보 확인점 | 242,865건 |
| 현재 선택 기계정책 확인점 | 14,005건 |
| 연구 정답 | WIN 1,523 / FAIL_STOP 276 / FAIL_TIMEOUT 543 / UNRESOLVED 11,663 |
| 확정 정답 2,342건 중 개발·기존 연구 제외 | 92건; 새 평가 적격 2,250건 |
| 이번 비교 | 전체 census에서 고정 scope/hash 표집 66쌍 + 누락 날짜의 전체 확정 1쌍 |
| 10/14 | manifest에 포함하되 유효 확인점 0을 날짜 목록에서 숨기지 않음 |
| 10/16 | inventory 고정 시 유효 closed epoch 계약이 없어 미확정 원천으로 제외. 당일 수집 종료 후의 미래 계약을 가정하지 않음 |

삼성의 현재 기계 확인점은 PRE 878건(W13/U865), REGULAR 93건(W88/U5), AFTER 4,330건(W0/FAIL_TIMEOUT238/U4,092)이다. 비삼성은 종목 유형·시장·가격대·route별로 따로 집계했다. 모든 상세 분모와 제외 내역은 [완성 누적 frame](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/complete-source-frame.json)에 있다. UNRESOLVED는 실패나 정상 BLOCK이 아니다.

새 census는 누락된 유효 날짜가 있으면 `retained_source_coverage_complete=false`와 해당 날짜를 기록한다. 기존 manifest를 읽었다는 이유만으로 전체 누적 완료를 주장하는 문제를 막았다. 이 flag는 오프라인 연구 원천 상태이며 운영 기계/주문 관문을 추가하지 않는다.

## 3. 연구 승패와 실제 자동관리 경로 분리

연구 라벨은 확인 ask, 비용률 `0.0023`, 1,800초, 비용 후 목표 `+0.4%`, 비용 후 soft stop `−3%` 선도달 여부다. 손익 크기·손익비로 선발하지 않는다. 30분 밖의 목표 도달을 WIN으로 올리지 않는다.

실제 preset 하드스톱·수동관리 이관은 별도 축이다. 동일 position/pin/시각의 native 이관 증빙이 있으면 목표와 이관의 선후를 기록하는 helper를 추가했다. 빈 이관 목록만으로 자동관리 지속을 증명하지 않으며, 이관과 목표의 동시 시각도 순서를 확정하지 않는다. 수동관리 이관 −1.47%는 매도·실현손실·연구 FAIL을 뜻하지 않는다.

10/15의 기존 Main stop 연구 7개 사례에는 원 호가/position 경로 결손 3건과 다른 lifecycle 식별 불가 4건이 남아 있다. 운영 quote source가 검증되지 않아 실제 자동관리 성과를 확정할 수 없다. 원 보고와 오류는 보존하고 PnL은 null로 둔다. 연구 확인점은 실제 보유분과 동일하지 않으므로 가상의 실제 이관/자동수익을 붙이지 않았다. **시장 경로가 유효하면 연구 평가는 가능하지만, 그것만으로 실제 자동운용 성과를 주장할 수는 없다.**

근거: [연구/운영 경로 대조](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/operating-path-comparison.json).

## 4. 실제 프롬프트 비교와 호출 회계

H6는 확인 ask·spread·제공 가격 경로를 평가하면서, 반전 직전 rolling 매도 우세/VWAP 미회복과 현재 신호의 실패를 구별하도록 했다. signal 인용만으로 성공확률을 증명하지 않고, risk binding은 인용 가능 목록이라는 점을 명시했다. 입력 사실·스키마·모델·token/reasoning 설정은 현행과 같게 유지했다. 내부 문구는 English ASCII다.

- 개발: 부모 binding 7종별 1개 확인점, 7쌍·실제 신규 14회. 기존 개발/검토 key와 새 개발 key를 효과 확인 집합에서 제외했다.
- 효과 비교: 사전 봉인 66쌍과 10/13 보강 1쌍, **67/67 유효 공통 쌍**. 효과 비교 요청 134개 중 exact 응답 1개 재사용, 신규 실제 호출 133회.
- 이번 신규 attempt **147회**. 기존 653회에서 최종 **800/800회**, 잔여 0회. 과거 failed/uncertain 예약 13개는 원 기록대로 남아 있으며 새 실패나 응답 결손으로 바꾸지 않았다. 이 실행에서 신규 실패/미완료 쌍은 없었다.
- source-scope 보강은 원천 날짜 승인만 확장한다. 기존 단일 예산 key·사용량·정기 장후 100회·운영 한도는 바꾸지 않는다.
- 전체 DB/raw 복제 없이 bounded snapshot과 shared object dedup을 사용했다. 연구 전용 폴더는 정규화한 누락 날짜를 포함하여 약 18MiB였다. 공통 store의 전체 증가량은 다른 writer와 섞여 있으므로 본 연구 기여로 단정하지 않는다.

## 5. 결과와 후보 인계

다음 합계는 scope별 표집의 **비가중 진단값**이다. 전체 2,250개 평가 적격 확인점에 대한 전수 AI 성능 추정치가 아니다. 적용 판정은 route·가격대를 포함한 세부 scope에서만 한다.

| 구분 | 시장 | 비교 쌍 | 현행 PASS W/전체 PASS | H6 PASS W/전체 PASS |
| --- | --- | ---: | --- | --- |
| 삼성 | PRE | 3 | 1/1 | 0/0(null) |
| 삼성 | REGULAR | 2 | 0/0(null) | 1/1 |
| 삼성 | AFTER | 7 | 0/6 | 0/4 |
| 비삼성 | PRE | 22 | 9/14 | 9/14 |
| 비삼성 | REGULAR | 18 | 14/17 | 9/12 |
| 비삼성 | AFTER | 15 | 6/9 | 6/9 |
| 전체 진단 합계 | 전체 | 67 | 30/47(63.8%) | 25/40(62.5%) |

혼동행렬은 현행 TP30/FP17/FN18/TN2, 후보 TP25/FP15/FN23/TN4다. 승리 보존율은 62.5%→52.1%, 실패 차단율은 10.5%→21.1%다. 후보가 손절 선도달 4건을 차단하지 못한 점도 남겼다.

| scope | 현행→후보 | 판단 |
| --- | --- | --- |
| 주성 AFTER / GE_100000 / SOR | TP1/FP0/FN1 → TP2/FP0/FN0, 두 PASS 승률 100% | 동률 TP 증가 후보. 10/7 한 날짜·2쌍·서로 다른 5분 구간 |
| 기타 비삼성 PRE / 20000_TO_100000 / NXT | TP1/FP0/FN2 → TP2/FP0/FN1, 두 PASS 승률 100% | 동률 TP 증가 후보. 9/30·10/2, 2종목·3쌍 |
| 삼성 REGULAR / SOR | 현행 전부 비PASS, 후보 승리 1건 복구 | 복구 신호는 기록하되 현행 0/0을 0%로 만들어 우월성을 선언하지 않음 |
| 삼성 AFTER / NXT | 실패 PASS 3건→1건, 양쪽 승률 0% | 실패 차단 개선은 기록. 승률/TP 기준의 개선 scope로 선발하지 않음 |
| 나머지 | 동률 또는 열위 | 현행 유지 |

실제 응답에서 WIN을 `ENTRY_SPREAD_CONCERN`으로 차단한 수가 12→17로 늘었다. 정규장 비삼성에서 승리 5건을 추가 차단했다. VWAP 미회복을 위험으로 인용하는 동일 형태의 답변이 성공·실패 양쪽에 남아 있다. 따라서 과거 맥락 구분 문구를 더 길게 넣으면 전체가 개선된다는 가설은 지지되지 않았다. 다음 연구는 실제 spread 값/target 관계와 현재 확인 경로의 설명을 구분하는 최소 변경 가설이어야 한다. 이번 확인 결과를 읽고 새 후보를 만들면 67개 key도 그 후보의 개발 집합으로 이관해야 한다.

근거: [최종 비교](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/final-analysis.json), [원 응답별 오류](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/error-patterns.json), [표본 집중도](/home/ubuntu/KORStockScan/data/report/reversal_auxiliary_tuning/research/aux_prompt_research_20261008_01/cumulative-20261016/evaluation-concentration.json).

## 6. 구현·리뷰·검증과 배포 대기

기존 `src/engine/scalping` 연구/장후 owner와 인접 테스트만 수정했다. 새 engine root 모듈, Kiwoom 요청/parser, broker 호출은 추가하지 않았다.

| 리뷰에서 발견한 결함 | 수리·재검증 |
| --- | --- |
| 누적 child materializer가 구형 nested fact ledger를 flat `facts`로 가정 | 실제 원 fact만 승계하고 필수 원 fact가 없으면 fail closed. 원 object 불변, optional 결손은 null 유지 |
| 누적 child의 원 registry가 구형 envelope를 가리킴 | 새 materialized snapshot에 선택 branch의 registry를 연결하고 원 registry provenance 보존 |
| price-progress registry가 구형 request projector로 라우팅 | 명시 PROGRESS registry를 extended projector로 연결. 기존 버전은 기존 경로 유지 |
| materializer 수정 뒤 prepare cache 재사용 가능 | cache key와 campaign에 materializer 코드 hash 추가 |
| 과거 허용 날짜만으로 누적 연구 확장 불가 | source-only 불변 승인 leaf와 campaign 검증 추가. funds/원 예산 reset 금지 |
| 기존 normalized 목록을 전체 raw 보유 목록으로 오인 | retained date inventory, 누락 날짜·미확정 날짜 분리, 미완료 coverage flag |

재물질화 과정에서는 이전 snapshot object와 96건의 메타데이터 차이를 확인했다. 원 확인점·라벨은 같고, 실제 현행 요청 147개를 현행 materializer로 양쪽 다시 구성한 결과 요청 차이 **0건**이었다. 기존 object를 덮지 않았다. 처음에 전체 object 동일성을 요구한 검증은 이 provenance 차이 때문에 실패했고, 원천/라벨·실제 전송 동등성으로 분리하여 재검증했다.

검증 완료: 관련 pytest **346 passed**, final capture hash의 annotation/cache 검증 **2 passed**, 변경 Python 9개 compile 및 `git diff --check` 통과. 문서 링크 109개를 대사해 신규 결손 0개를 확인했다. 격리 작업본에 없는 기존 checklist 참조 3개는 기준 commit에도 같은 링크가 있고 기본 작업본에는 실제 파일이 있음을 확인했으며 원 파일을 복제하지 않았다. print-only parser는 29개 항목, 현재 실행 owner는 1개다. 외부 sync는 실행하지 않았다. pytest는 provider를 호출하지 않았고 실제 provider 호출 147회는 위 연구 캠페인에서만 실행했다.

배포 요청을 받으면 최신 selector/PID/start ticks, 부모와 두 scope의 현행 binding, 원 source/evaluation/hash를 다시 고정한다. 부모나 typed 사실이 바뀌었으면 영향 scope만 재대조하고, 과거 evaluation의 부모를 새 값으로 덮지 않는다. 코드 배포가 필요하면 정식 active-policy handoff/native parity 및 stop/holding 계약을 통과한 candidate로 준비한다. 검증 누락 상태에서 먼저 Main을 중지하지 않는다.

검토 가능한 발행 후보는 두 scope만이며, 다른 시장·가격대·REGULAR 상속 범위로 자동 확장하지 않는다. 기존 `reversal_auxiliary_intraday`의 명시 evaluation·CAS·원 claim TTL·scope rollback을 사용한다. 발행, PID 소비, 첫 자연 요청, 주문/실현 성과는 각각 확인한다. 이번 작업의 `runtime_effect=false`와 배포 대기 상태는 유지한다.

연구는 검토된 후보를 수동 등록하고 장후에는 등록 후보를 평가하는 구조를 유지한다. 매일 자유 문구 생성, 전체 원장 복제, 기존 800회 예산의 자동 재충전은 없다. 추가 가설의 신규 연구 호출은 별도 예산 지시 후 진행한다.

## 단계 종료 상태

| 단계 | 이번 종료 상태 | 남은 경계 |
| --- | --- | --- |
| 1. 증빙 | 원 archive 연결 283건·결손 1건 분리, producer 기존 수리 검증 | 과거 primary gate/PnL을 조작하여 닫지 않음 |
| 2. 누적 모집단 | 유효 보유 원천 10일, 누락 10/13 보강 | 10/16 미확정 epoch와 U11,663은 제외 |
| 3. 연구/운영 계약 | 별도 정답·native custody 선후 helper 구현 | 실제 7개 보유 경로의 역사 결손은 미확인 유지 |
| 4. 실제 비교 | 개발 7쌍·평가 67쌍, 신규 147회 완료 | 예산 800/800, 새 무제한 권한 없음 |
| 5. 평가 | 전면 교체 비권고, 세부 두 scope 후보 | 탐색 표본 한계 공개; 실현 수익 아님 |
| 6. 코드 종료/인계 | 반복 리뷰·수리·영향 검증 통과 | **정책 발행·배포·재기동은 사용자 지시 대기** |
