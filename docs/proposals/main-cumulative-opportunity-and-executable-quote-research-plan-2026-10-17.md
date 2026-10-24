# Main 누적 상승 추가 포착·ENTER_NOW 실패 감소·비상시감시 호가 정합성 연구 계획 — 2026-10-17

## 현재 연구 방향 갱신 — 2026-10-23

최신 정정: 보존 분봉 편입으로 A42/A43의 STOP·TIMEOUT이 늘어 source22 우위 해석을 철회했다. [미확정 복원 뒤 정정](#미확정-추적보존-분봉-복원-뒤-정정)의 날짜별·누적 결과와 잔여 U를 현재 판단으로 사용한다.

현재 방향은 **약세 중 관측 가능한 상승, 현재 정책의 반사실 포착, 실제 PID의 기계→AI→제출을 별도 분모로 검증**하는 것이다. [AGENTS 시장 identity 원칙](../../AGENTS.md#market-identity-and-natural-acceptance)에 따라 정규장 정책 cohort KRX·통합 `_AL` 원천·SOR 주문 경로와 실제 체결 거래소를 구분한다. 종료된 source22의 SOR REGULAR/AFTER 전체를 기존 연구 owner에서 재생했으며 원64개/source21 결과를 새 날짜 결과로 바꾸지 않았다.

새 임계치 탐색 대신 이미 동결한 A17~28·A33~38을 그대로 사용했다. 현재 bundle `1d9e5b09`의 native membership·실제 ask·정규화 적격 행·동일 item/epoch/sequence·비용0.0023·목표+0.4%·stop−3%·30분과 동일 완료 분봉 계약을 유지한다. 현재 parent가 source22를 사용했으므로 이 비교는 독립 holdout이 아니다. 진행 중 source23은 종료·봉인된 날짜로 편입하지 않고 실제 PID 자연 관측만 별도 보고한다.

관측 상승은 거래 가격 라벨만으로 실행 가능하다고 부르지 않는다. 별도 대조에서 원 ask 이후 같은 연속 source의 신선한 실제 bid가 비용 포함 목표에 도달하는지와 그 전 adverse trade를 확인한다. 수량/depth·실제 체결·broker 비용이 없으면 그 항목은 미증명/null이다. 이전 시장 상태만 결속하고 나이를 공개하며, 특히 AFTER에 오래된 정규장 지수 상태를 실시간 약세로 전용하지 않는다. 감시 자료 밖의 시장 전체 recall은 별도 독립 benchmark/BBO 계약이 없으면 미증명이다.

이번 결과는 정규장269/AFTER86 관측 상승 창이며 현재 정책 포착5/23, 기존 A와 새6개까지 합친 포착48/28이다. 현재 미포착 중 ask→후속 bid까지 목표가 관측된 창은135/35개다. 전역 새6개 추가는 정규장 확정 비율80.38%→48.11%·STOP1→47, AFTER70.69%→57.43%로 악화돼 채택하지 않는다. A33의 비상시감시 AFTER 저가 scope와 A35의 주성 AFTER 고가 scope는 작은 범위의 탐색 후보로만 남기며, 다른 scope의 악화와 UNKNOWN도 함께 보존한다. 새 승격 기준·guard 완화·provider 호출은 추가하지 않는다.

다음 검증은 같은 정의를 유지한 신규 종료 원천과 현행 membership의 누적·날짜 분리 비교다. 짧은 연속 관측·연구 특징 미준비와 실제 선택 branch의 준비성, root/hold/조건 실패, 기계 이후 freshness/AI/종료를 구분한다. 신규 등록 자체를 수집 결함으로 단정하지 않는다. 일정과 남은 수용은 [당일 checklist의 MachinePatternOpportunityResearch1023](../checklists/2026-10-23-stage2-todo-checklist.md#기계판정-자연-수용), 계산·반례·현재 PID 현황은 [연구 검토](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#정규장-점검과-source22-반등-후속-연구--2026-10-23)가 소유한다. 운영 등록·정책 발행·배포/재기동·주문 권한으로 전환하지 않는다.

### 정규장135개 실제 경로 추적 후 방향

135개는 현재 정책의 source22 반사실 미포착이며 실제 과거 기계판정 부재135건이 아니다. 실제 e815 정책·lease/native identity·PID/capture/lifecycle까지 연결한 결과는 운영 시간 전4·초기 probe 해제 뒤 목표21·알려진 root/패턴 조건 실패100·root 없음4·실제 기계판정 존재3·claim 전 무효화/목표 뒤 소비2·기존 initial fill 상태 결함1이다. native UNKNOWN80·root missing9는 중복 보조 진단이며 이 수를 수집 결함으로 전용하지 않는다.257개 State→보존 source 대조와 actual receipt parity는 불일치0이며 상류 broker/시장 전체 완전성은 미증명이다. [원인별 전체135개·수리/회귀·원문](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#정규장-미포착135개-실제-경로-추적--2026-10-23).

새 동결 A39~43은15초 회복/돌파/VWAP 회복·3초 유지·10틱 trade/bid 전진을 검증한다. 알려진 실제 lease 경계에서 관측 이력을 끊으며 UNKNOWN을 채우지 않는다. source21/22 전체 적격 정규장에 같은 비용·호가·목표/stop/30분을 적용했다.135개 중14개(첫 lease/고정 안13개), 기존 A17~38보다 새3개를 포착했지만 source22 현행80.38%→합집합51.64%·STOP1→30/TIMEOUT30→367로 악화돼 전역 채택하지 않는다. 새3개의 같은 lease ask→bid 목표도 확인했으나 독립 주문·체결·실현 수익으로 바꾸지 않는다. 사후 scope/임계치 재탐색은 하지 않았다.

기존 receipt/spread 결함은 이미 수리된 원 owner를 재검증했고 새 production 수정은 없었다. 연구의 State reset/UNKNOWN quote-clock 결함만 보완·회귀했다. 다음 종료 source23은 기존 MachinePatternOpportunityResearch1023에서 A17~43의 원 정의·날짜/누적·scope별 W/STOP/TIMEOUT/U·추가 창·실행 여유를 비교한다. 이번135개 추적 완료와 그 미래 수용 OPEN을 구분하며 운영 정책·안전기준·배포/주문 권한은 그대로다.

### 조건 불충족100개 추적 뒤 좁은 연구 방향

후속100개를 실제 e815의 선택15개 branch와 부모5개까지 추적한 결과 native 평가 시 호가 보호49·필수 특징 미준비19·안전한 입력에서 전략 조건 차단32개였다.32개를 모두 실행 가능한 누락 매수로 보지 않는다. 실제100개 coverage parity를 확인했고 새 production 판정 결함은 없었다. 정규장 policy KRX·통합 `_AL` source·SOR route와 실제 거래소 미상을 유지한다. [전체 scope·원 조건·반례](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#조건-불충족100개-scope별-후속-연구--2026-10-23).

현재 방향은 **비상시감시·2만원 미만·정규장의 A42/A43/A44만 좁게 후속 비교**하는 것이다. 원 A39~43×7개 scope35안과 G4 단일 전략 gate5안을 모두 공개했다. A42의3초 유지+매수비중70 조건은 source22 추가W10/STOP0/TIMEOUT0/U51·100개 중5개, A43의10틱 trade/bid 전진은W17/STOP1/TIMEOUT0/U52·7개, A44의G4 구조MIXED/RISING 추가는W63/STOP2/TIMEOUT0/U44·4개를 포착했다. source21은 각각U12, W1/U13, 추가0으로 독립 재현성은 미증명이다. 전역/다른 scope의 STOP·TIMEOUT 악화는 그대로 남기며 기존 전역 미채택을 뒤집지 않는다.

수익 경로의 반복 확인을 독립 거래로 세지 않는다. 원 목표 시각 전에 같은 lease의 실제 bid까지 확인된 창은 각각2/3/2개이고 저가 A39~44 합집합5개다. A44의STOP2는 같은 하락 구간이며 FIRST109개 중99개의 유효시간 상한이1초 미만이다. 저가 U191개 중190개는 같은 item 완료 분봉이 없어 TIMEOUT0을 무위험으로 해석할 수 없다. 원 spread/known quote/UNKNOWN·physical lease·실행5초·hard guard는 유지한다.3초는 기존 동결 패턴 확인 길이로 새 실행 상한이 아니다. 새 임계치로 반례를 제거하거나 U를0수익으로 바꾸지 않는다.

source23 종료·봉인 뒤 기존 MachinePatternOpportunityResearch1023에서 A44를 추가한 동결 정의, 추가/제거 창·원 목표 전 bid·STOP/TIMEOUT/U·원 기한 내 신호 소비 여유를 날짜별/누적으로 재검증한다. 이번 임시 연구 reader의 parent/UNKNOWN/빈 포착 집계만 수리했고35개 회귀·100개 parity를 통과했다. 운영 등록·정책 발행·배포/재기동·주문 및 경제 수용과는 분리한다.

### 미확정 추적·보존 분봉 복원 뒤 정정

앞 절의 U를 추적한 결과 고유159개는 명시 lease 해제156·재기동 중 REMOVE 미확인/collector closed3으로 관측이 끝났다. 원장 보존 SHA·타깃37,555행 원장→정규화·native 라벨 재생이 일치했고 새 운영 수집/보존/라벨 결함은 확인되지 않았다. 연구가 빠뜨린 보존 main_minute_history의 exact `_AL`4개 revision을 native reader로 편입해17개를 복원했다(W6/STOP2/TIMEOUT9). 남은142개는 충분한 후속 원천 부재130·기존 분봉 시각/경계 규정상 U12로 보존한다. [원인·수리·17개 복원·62회귀](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#a42a43a44-미확정-원인과-보존-원천-복원--2026-10-23).

source22 저가 추가 결과는 A42 **W11/STOP1/TIMEOUT4/U45**, A43 **W22/STOP2/TIMEOUT6/U40**, A44 **W63/STOP2/TIMEOUT0/U44**로 정정한다. 고정 현행80.38%에 대한 전체 확정 비율은79.31%/79.26%/85.20%다. A42/A43의10/22 우위 해석을 철회하며 실패 복원을 대조에 남긴다. 두 날짜 누적은 현행46.69%→47.92%/49.50%/56.38%로 별도 공개하고 새 일별/경제/표본 문턱을 추가하지 않는다. A44는 새 날짜 재현성과 짧은 신호 수명·U44가 여전히 미증명이다.

후속 비교는 source23의 원 native 입력과 함께 같은 날짜/item의 보존 REST immutable revision을 먼저 동결하고, 해당 원천을 원 해제 lease의 특징 이력과 섞지 않은 채 outcome 보완에만 사용한다. 원 provider 응답·bar hash/available clock·request code/base date·보수적 clock/boundary 라벨을 유지한다. bid/수량/체결/PnL은 분봉으로 채우지 않는다. 기존 연구 owner와10/26 수용 창을 유지하며 운영 구독/감시 길이/정책/guard/실행5초/배포·재기동·주문 변경은 없다.

보존 REST 편입은 임시 `unresolved/trace.py`의 복원 기능에서 기존 `completed_history` 생산자와 `continuous_reversal_postclose.completed_bars` 및 branch/registered/path/operating/cumulative 소비자로 통합한다. 새 source generation은 사용한 WS·broker·REST revision의 실제 bytes와 종류·원 경로·SHA를 함께 봉인하고, 소비자는 그 세대의 고정 자료만 재사용한다. REST와 WS의 수정주가 동등성을 가정하거나 봉을 이어 붙이지 않으며 출처 충돌·분봉 시각/경계 모호성은 U로 남긴다. 임시 복원 코드와 과거 원 결과는 hash가 결속된 역사 증거로 보존하고 후속 생산 경로로 사용하지 않는다. [구현·리뷰·배포 후보 검증](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#보존-rest-분봉의-기존-생산자소비자-통합--2026-10-23)이 소유하며 기존10/26 자연 수용과 매매 안전기준은 유지한다.

### 제출직전 가드 연구 방향·단회 실행 — 2026-10-23

기계 패턴의 미포착과 실제 AI PASS 뒤 차단은 별도 분모다. 같은 사용자 지시의 제출직전 연구는 [기존 가드 감사 §10](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md)이 소유한다. 10:39 고정 source23 정규장에는 유효 PASS0이며, source22 정규장 유효 PASS7→자금6→broker 제출 관측1이다. 남은6건의 exact capture/transport epoch/sequence/관측 ask를 연결한 결과 W1/TIMEOUT5다. 과거 snapshot의 최다 가드 횟수를 현재 가드 실적이나 일괄 해제 근거로 다시 쓰지 않는다.

우선순위는 **P0 정확 PASS의 남은 critical path 단축과 원 clock/정책 비교 확인 → P1 기존 bounded fresh 재평가의 실제 연결 → P2 약세 context별 기회 복원과 실패 통과의 같은 분모 비교**다. 두산 실제 PASS의 관측 ask62,800→후속 bid63,200(+0.4055%,350.383초)는 놓친 가격 기회의 명확한 사례지만 자금 때 원5초까지69ms만 남았고 다른 hard guard·수량 체결은 미증명이다. 원 callback의 `auxiliary_decision_generation_changed`는 registry/부모 변화뿐 아니라5초 초과도 포함하므로 실제 검사 시각과 비교값을 기존 원천에서 확인한다. 기한 연장·stale PASS 재사용·안전 가드 삭제를 연구 성공으로 대체하지 않는다.

기존 source22 진단 상승 창135개 중 연속 이력120초 이상41개, 그중 사전120초 이내 source-ready BROAD_WEAKNESS와 결속되는 미포착 창29개는 모두 비삼성이다. 시작 시점부터 상승 중이라는 뜻은 아니다. 동결 A33/A36의 후속 prefix 반전 확인과 bid 목표, 확인 시점의 같은 약세 slice까지 이어지는4개 사례를 별도 공개했다. 실제 PASS의 차단 건과 합산하지 않는다. 삼성에는 같은 약세 slice 표본이 없으며 사전 지수 결손을 개별 주가 하락으로 대체하지 않는다.

전면 약세 veto CF는 기계 확인160개에서 W1/TIMEOUT4를 제거해 확정 비율80.38%→82.35%이나 서로 다른 목표 시각은11→10이다. 이 결과도 숨기지 않되 AI PASS 이후 정책 효과로 전용하지 않는다. 현행 family의 누적·날짜별 비교를 유지하며 별도 EV/최소표본/승리 전부 보존이라는 새 채택 문턱은 추가하지 않는다. 기존 전역 패턴 추가안의 악화 결과도 유지한다.

연구는 기존 compact index·exact capture·봉인된 normalized/source22 가격·시장 관측을 재사용해 완료했고 새 AI/Provider 호출0, 원장/DB 복제0, 정책·배포·재기동·주문 변경0이다. 현재 입력·프롬프트·원응답·원 실패 시도는 보존했다. 기존 `MainEntrySourceTerminalRepair1022`의 자연 소비와 `MachinePatternOpportunityResearch1023`의 신규 종료 source 검증을 대신하지 않으며, 이번 단회 연구 완료는 당일 `PostAuxiliaryGuardResearch1023`에 기록한다.

### P0/P1 구현 연결 — 2026-10-23

후속 구현은 실제 선택926ebca82를 기반으로 물리 전송 직전 보조·generation 검사를 한 fresh 불변 뷰에서 수행하고, 실제 검사 clock을 원 terminal에 남긴다. 비상시감시 Main도 기존 bounded native successor 재방문을 공유한다. 원 PASS 재사용·deadline 초기화·guard/TTL/정책 변경은 없다. [동일 리뷰의 구현 절](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md#p0p1-구현통합본-준비--2026-10-23)과 실행 결과가 코드/후보 준비 근거이며, 배포·PID 소비·자연 효과는 기존 `MainEntrySourceTerminalRepair1022`에 OPEN으로 남긴다.

## 현재 연구 방향 갱신 — 2026-10-22

이번 사용자 지시는 방향성 갱신과 실제 오프라인 연구 실행이다. 현재 실행 맥락은10/22 체크리스트이며 아래1~7절의10/17 선택 릴리스·당일 checklist 부재·표본 수는 당시 기록이다. 현재 정책 membership과 종료된 source21을 다시 고정하며 과거 parent 대비 개선을 현재 개선에 합산하지 않는다. 기존 연구의 코드·확인점 캐시는 원천/특징 코드/정확 identity가 같은 범위만 재사용한다.

핵심 질문은 **약세장에서도 비용 후 상승 기회가 있었는지, 현재 기계판정이 이를 어디서 놓치는지**다. A(추가 상승 포착), F(ENTER_NOW 실패 감소), F(current) OR A를 함께 비교한다. 비율 우선안과 기존 비율 이상에서 W를 최대화한 대안을 나란히 공개하고, 추가/제거 W·STOP·TIMEOUT·U 및 새로운/잃은 목표 도달 시각을 명시한다. 관측 확인점 증가를 독립 거래 증가로 바꾸지 않는다. Main family의 기존 비용 포함 목표 선도달 비율 계약을 유지하며 다른 family의 EV 원칙이나 live 적용 gate를 바꾸지 않는다.

시장 약세는 해당 시각 이전의 시장 상태 기록과 원천·시각으로 확인한다. 개별 종목 session return을 시장 지수 약세라고 부르지 않는다. 장후 생성된 시장 요약은 사후 맥락이며 진입 특징에 넣지 않는다. 근래 미증명10/19·20 원천은 결손으로 유지하고0건 기회로 계상하지 않는다. 진행 중인10/22 자료는 완전한 종료 증빙·범위 봉인 없이 완료 일자나 독립 검증일로 사용하지 않는다.

기존 ENTER_NOW/A 표본 밖의 상승도 조사한다. 새 적격 날짜의 동일 item/epoch에서 매5초 구간 첫 적격 실제 ask를 outcome과 무관하게 추출하고 기존30분·비용0.0023·목표+0.4%·stop−3%로 라벨링한다. WIN 구간은 entry→target 시각이 서로 겹치지 않게 시간순으로 정리한다. 이는 사후 관측 가능한 상승 창의 진단 분모이며 실제 체결/시장 전체 기회 수가 아니다. 현재 native WIN의 target이 그 창 안에 있으면 선행 확인을 포함한 포착으로, 현재 확인만 있고 목표가 창 밖이면 시점 차이로, 확인이 없고 A만 있으면 등록 정의의 탐색 공백으로 구분한다. 이 귀속은 새 live gate가 아니다. source break·warmup·UNKNOWN과 quote age·고정/비상시감시·venue/session을 함께 공개한다.

새 원천 outcome을 보기 전에 A17~28을 고정 재사용하고 F35~38을 추가 동결한다. F35는 종목 중립에서 완만한 상승·VWAP·매수·비하락 구조를, F36은 종목 약세에서 상승 구조·작은 반등·매수를, F37은 종목 강세에서 비하락 구조·과열 상한·매수를 요구한다. F38은 VWAP/매수/스프레드 또는 상승 구조/완만한 상승/거래량의 OR다. 정확한 수치는 [이번 실행 manifest](../../tmp/main-machine-cumulative-dual-track-research-20261022/manifest.json)에 고정한다. UNKNOWN은 기존 신호를 보존하며 새 A나 F가 실제 제출·호가 안전을 승인하지 않는다.

source20까지의 선택을 먼저 동결한 후 source21에 그대로 적용한 날짜 분리 비교와, source21까지 합친 누적 탐색을 분리한다. 현재 parent 자체가 source21을 사용해 선택됐다면 source21 비교는 독립 holdout이라고 부르지 않는다. 후행1일 결과나 같은 누적 자료의 재탐색으로 기존 family의 운영 승인 조건을 대체하지 않는다. 기존2GiB/CPU480초/wall600초의 단일 낮은 우선순위 partition 실행을 사용하고, 정상 역사 원천 전체를 다시 재생하지 않는다. 재사용 증명에 실패한 범위만 명시적으로 재계산한다.

운영 후보 등록·정책 발행·배포·재기동·provider·주문은 실행하지 않는다. 보조판정 입력/응답/membership은 유지한다. 결과와 인계는 [기존 연구 검토](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md)에 같은 세션의10/22 후속 결과로 남긴다. 아래 과거 계획의 과거 비교 수치는 현재 결과로 대체해 읽지 않는다.

실행 결과를 반영한 방향: 현재 판정 밖의 가격 상승 창을 분모로 유지하고, 특히 비상시감시와 창 시작 시점의60/180초 특징 미확정 여부를 구분한다. 새 비교 identity는 day/item/epoch/sequence에 session을 포함한다. 정규장과 시간외장의 sequence 재사용을 같은 사건으로 합치지 않는다. 10/21의 적격 구간에서 현재 정책/기존 A 전체가 모두 포착하지 못한64개 상승 창을 연구 반례로 보존한다. 원천이 없는 장 초반·다른 날짜·수집하지 않은 종목의 기회 수는 주장하지 않는다.

관측 반례를 본 뒤 A18/A19/A22/A27에서 연구용 spread 조건만 제거한 A29~32를 별도 [후발 대조 정의](../../tmp/main-machine-cumulative-dual-track-research-20261022/spread-ablation-freeze.json)로 고정·실행했다. 이 대조는 source21 후향 탐색이며 독립 검증이 아니다. 동일 네 parent의 합집합과 비교하면 추가 상승 창0, W+1/TIMEOUT+52/U+34였다. 단순 spread 조건 삭제는 이번 개선안으로 선택하지 않는다. 관측 초기의 특징 미확정과 약세 중 반등 구조를 분리하고, 기존 패턴의 root·hold·필터가 실제로 충족되는지를 확인하는 것이 현재 연구 방향이다. 운영 guard 완화나 미래 가격의 진입 특징 사용으로 해결하지 않는다.

### 미포착64개 후속 연구의 고정 정의

64개 원래 identity를 유지하고 창 시작부터 목표까지 기존 A17~28의 입력 준비성을 전수 추적한다. 처음에는 계산 불가능했지만 도중 준비된 경우와 끝까지 불가능한 경우, 처음부터 계산 가능한 경우를 분리한다. 시작의 ret180 미확정만으로 생산자 결함이나 창 전체 warmup을 단정하지 않는다. 실제 root·hold·확인 필터 실패와 기존 A의 늦은 목표 도달도 함께 센다. 기존 “미포착”은 성공한 동일 창 포착 부재이며 신호 자체 부재와 다르다.

새 정의 A33~38은 [계산 전 동결](../../tmp/main-machine-cumulative-dual-track-research-20261022/rebound-gap-study/freeze.json)에 고정했다. 30초 반전·얕은 눌림 회복·직전30초 고점 돌파·30초 VWAP 회복·60초 회복·상대 강세 돌파의 여섯 가설이다. 필요한30/60초 관측·매수 비중·VWAP/거래량·1/3초 가격 유지는 실제 prefix로 확인하며 UNKNOWN에서 새 신호를 만들지 않는다. root와 확인의 동일 item·알려진 quote age 및 기존5,000ms 연구 상한·spread≤0.10%를 요구한다. 이 연구 상한은 실제 AI/제출의 더 엄격한 freshness 계약을 대체하지 않는다. actual ask·비용0.0023·목표+0.4%·stop−3%·30분 라벨과 운영 안전기준은 유지한다.

전체10/21 SOR REGULAR/AFTER와, 결과가 아닌 날짜·적격성으로 미리 선택한 이전 최신 SOR REGULAR(10/08)·AFTER(10/15)만 계산한다. 새 여섯 가설·OR 전체·이전 표본으로 선택한 조합을 현재 정책 및 현재+기존 A 전체와 비교해64개에서의 순추가 포착과 W/STOP/TIMEOUT/U를 공개한다. 이전 두 파티션은 제한된 대조군이며 전체 누적 검증을 대신하지 않는다. 현재 parent와 가설 방향이10/21을 참고했으므로 독립 holdout은 아니다. 결과가 나쁜 조합을 숨기거나 그 뒤 수치를 바꾸어 재탐색하지 않는다.

실행 결과64개는 목표까지 기존 A 입력 미준비41개·도중 준비4개·시작부터 일부 A 입력 준비19개로 구분됐다. 미준비41개 중39개는 목표 때 연속 이력이120초 미만, 나머지는7틱·3틱에 불과했다. 입력이 준비된 창에서도 root/hold/확인 필터와 늦은 목표가 별도 원인이었다. 이 진단은 생산자 결함을 새로 확정하거나 과거 source loss를 복구한 결과가 아니다.

후속 [실제 등록·수집·소비 추적](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#41개-입력-미준비의-실제-등록수집소비-추적--2026-10-22)에서41개는 신규 등록 관측39개·local release 이후 목표1개·과거 epoch 경계1개로 구분됐다. 이41개는 연구 A17~28의 입력 기준이며 당시 선택된 Main 패턴의 입력 실패41건이 아니다. 실제 선택 정의의 요구0~63초·기계판정 발생 사례·native FALSE를 입력 결손으로 표시하던 prefix spread 진단 결함을 구분했고, 진단 owner를 수리·회귀검증했다. 연구 outcome과 실제 등록의 소비 기회를 섞지 않으며 원천·미확정·실제 안전기준은 유지한다.

A33이 원64개 중4개(삼성3·비상시감시127120의1개)를 추가 포착했고 다른 새 패턴의 포착을 모두 포함했다. 그중127120은 신호·목표가 같은 밀리초의 서로 다른 sequence여서 실제 실행 여유를 입증하지 않으며 이를 제외하면3개다. 현재+기존 A의14/78창은 새6개 합집합에서18/78창이지만 W+12/TIMEOUT+85/U+201이었다. 이전 두 대조군에서도 새6개 전역 합집합의 확정 비율은87.05%→61.85%로 악화됐다. 전역 추가안은 선택하지 않고 A33을 확인 시점·짧은 반등의 탐색 후보로 보존한다. 삼성 AFTER 등 일부 scope의 작은 개선과 현재 분모가 없는 REGULAR scope는 [후속 연구 검토](../audits/main-machine-pattern-dual-track-research-review-2026-10-21.md#미포착64개-인과-분리와-반등-가설--2026-10-22)에서 별도 공개했다. 운영 승격이나 독립 미래 성과를 주장하지 않는다.

## 1. 목적과 범위

사용자 지시에 따라 누적 원천에서 놓친 상승 추가 포착(A)과 기존 ENTER_NOW 실패 감소(F)를 함께 연구한다. 후속 지시의 비상시감시 종목도 별도 분모로 분석한다. 가격 패턴의 사후 성공, 판정 당시 실행 가능한 호가, AI 이후 실제 제출 가능 여부를 구분한다.

오프라인 수동 연구다. 새 가설은 여기에서 고정하며 장후 자동 생성기의 탐색 범위를 늘리지 않는다. 원천 수집 확대, canonical 장후 재생성, 운영 후보 등록·정책 선택·배포·재기동·provider·주문·호가 안전기준 변경은 실행하지 않는다. 보조판정의 기존 입력·응답·membership·성과를 변형하지 않는다. 생산 코드와 다른 세션 작업본은 보존한다.

오늘 10/17 일일 체크리스트가 존재하지 않는다. 10/19 문서는 미래 일정이며 오늘의 실행 권한으로 대체하지 않는다. 이번 명시적 연구 지시로 오프라인 계산과 연구 문서 검증을 수행하고, 운영 후속 작업은 현재 날짜의 owner와 별도 연결해야 한다.

## 2. 비교 기준과 원천 봉인

- 현재 선택 release snapshot은 `postclose-complete-20261017-7f2552aed`, 기계 bundle은 `8809c82e36bacc6a6e07b44c8bba6ccf15e477b67e11bdfcf4addf15112a4139`다. selector의 `actual_pid_consumed=false`를 정책 미적용이나 실제 판정 성과로 전용하지 않는다.
- 이 bundle의 누적 후보 대상 22개 scope membership은 [10/15 정정 연구](../audits/main-machine-cumulative-dual-track-research-review-2026-10-15.md)의 최종 recommendation과 일치한다. 과거 parent `1f069…` 기준의 개선을 현재 개선에 다시 더하지 않는다. 이전 봉인 sparse 확인점과 정의로 현재 membership을 정확 복구하고, 신규 날짜는 현재 native State로 재생한다.
- 기존 27개 partition에 10/15·16의 운용 route 6개를 추가한다. PRE는 NXT `_NX`, REGULAR·AFTER는 SOR `_AL`이다. 해당 원천의 row별 적격 여부와 exact item을 유지하며 invalid epoch를 가격 실패로 바꾸지 않는다.
- 새 원천은 1,269,187행이지만 적격 행은 10/15 SOR AFTER의 39,220행이다. 10/16 운용 세 route는 전부 적격 epoch 증빙이 없다. 현재 값으로 과거 종료 증빙을 생성하지 않는다. 10/15 AFTER의 epoch 검증 제외 후 39,255행에서 체결 수신 지연이 5초를 넘은 35개를 추가 제외해 39,220행이 된다. 확인점 호가 적격 검사는 별도다.
- normalized·sparse·현재 정책·완료 분봉·선택 코드와 후보를 [연구 manifest](../../tmp/main-machine-cumulative-dual-track-research-20261017/missed-rise-manifest.json)에 봉인한다. 지연 import 모듈도 [전체 scalping 코드 봉인](../../tmp/main-machine-cumulative-dual-track-research-20261017/reference-code-seal.json)으로 포함한다. 봉인 불일치·미완료 partition은 완료로 표시하지 않는다.

## 3. 추가 포착 가설

아래 8개를 결과 계산 전에 고정한다. 기존 A01~16을 다시 새 가설로 세지 않는다. 모든 특징은 확인점까지의 수신 prefix로 계산한다. `UNKNOWN→TRUE`는 새 전환으로 인정하지 않는다. hold 중 가격이 root 가격 미만이면 취소하고 확인점에서 필터를 다시 검사한다.

| ID | root와 확인 | 추가 조건 요약 |
|---|---|---|
| A17 | 완만한 상승 조건 전환 후 3초 유지 | 180초 +0.08% 이상, 60초 0~0.15%, 5분 낙폭 ≤0.15%, VWAP 이상, spread ≤0.1% |
| A18 | 얕은 눌림 회복 조건 전환 후 3초 | 180초 고점 대비 낙폭 0.1~0.4%, 60초 저점 대비 +0.05% 이상, 60초 수익률·VWAP ≥0, 매수 비중 ≥50%, spread ≤0.1% |
| A19 | 직전 120초 고점 돌파 후 3초 | 60초 0~0.2% 미만, 거래량 비율 ≥1, 매수 ≥50%, spread ≤0.1% |
| A20 | 거래량 비율 1.5 상향 전환 후 1초 | 60초 +0.03~0.3%, VWAP 이상, 매수 ≥60%, 동반 하락 구조 아님, spread ≤0.1% |
| A21 | VWAP 회복 후 5초 | 180초·60초 수익률 ≥0, 60초 <0.2%, 낙폭 ≤0.4%, 거래량 ≥1, spread ≤0.1% |
| A22 | 고점·저점 동반 상승 전환 후 3초 | 180초 +0.05% 이상, 60초 0~0.15% 미만, VWAP 이상, 매수 ≥50%, spread ≤0.1% |
| A23 | 첫 반전 후 1초 | 180초 +0.1% 이상, 5분 낙폭 0.1~0.6%, 60초 −0.1~+0.1%, VWAP 이상, 매수 ≥50%, 거래량 ≥1 |
| A24 | 60초 +0.02% 상향 전환 후 3초 | 180초 ≥0, 60초 <0.15%, VWAP 이상, 낙폭 <0.2%, 거래량 ≥1, spread ≤0.1% |

8개 각각과 256개 OR 조합을 scope별로 실제 합집합 계산한다. 각 고정 F(current)에 이 OR 조합을 붙이는 결합 비교도 수행한다. 같은 확인점만 dedup하고, 다른 시각의 신호는 독립 거래 횟수로 부르지 않는다. 추가 W/STOP/TIMEOUT/U, distinct target clock, 날짜 편중을 함께 보고한다.

## 4. 기존 ENTER_NOW 실패 감소

실제 `main_live` 캡처와 현재 정책의 native 재생 CF를 분리한다. 실제로 관측된 기계판정의 exact native epoch/sequence/item/관측 ask와 미래 가격을 연결한 사후 CF 라벨이며 실제 체결가·손익이 아니다. 결손은 SOURCE_GAP으로 남긴다. 주문 거절·수량 0·submit false를 가격 패턴 실패로 세지 않는다.

F23~28은 [별도 봉인 정의](../../tmp/main-machine-cumulative-dual-track-research-20261017/refinements/hypotheses-frozen.json)로 과열 추격, 동반 하락·약매수, 약세 회복, 중립 VWAP·구조, 거래량 증가 함정, 거래량 축소 구간을 시험한다. F UNKNOWN은 기존 신호를 보존하고 branch 정제는 다른 정상 OR 경로를 제거하지 않는다.

실제 캡처 연구에서 발견한 후발 F29는 별도 시간·정의를 봉인한다. 종목 세션 변화 −0.4~+0.4%에서만 `60초 수익률 − spread ≥0.05%`를 요구하고 그 밖/UNKNOWN은 유지한다. 실제 표본의 개선을 전체 CF에 일반화하지 않고 별도 검증한다. 후발 F30은 중립 F26과 약세 F25를 결합하여 같은 하락 경로를 다른 국면에서 재허용하는지 확인한다. 결과를 본 뒤 추가한 가설이라는 탐색 편향을 명시한다. 위 약세/중립/강세는 종목 자체 세션 변화이며 시장 지수 regime가 아니다.

## 5. 비상시감시 종목의 호가 정합성

기존 연구의 `good_quote`는 age 미기록 또는 최대 5,000ms를 허용한다. 실제 AI 입력 전의 canonical quote 기준과 Main 제출 시의 더 엄격한 quote·출처·동일 route·현재 시각 재검증을 코드로 대조한다. 연구의 허용 범위가 넓다는 사실과 실제 선택 표본에 stale가 섞였다는 판단을 구분한다.

1. 고정 5종목과 비상시감시를 분리하여 raw·현재 CF·신규 A·실제 ENTER 표본의 quote age/UNKNOWN, W/STOP/TIMEOUT/U를 집계한다. 실제 `main_live` ENTER 중 비상시감시는 1건뿐이며 연결한 실제 판정 표본의 적격 손절 선도달은 0건이라는 관측 범위도 명시한다.
2. 제출 latency 분류 기본 SAFE 250ms·CAUTION 상한 700ms, AI 입력 전 3,000ms, 연구 5,000ms를 별도 표기한다. 환경별 override와 실제 PID의 유효 값은 별도 증빙이며 확인 당시 700ms 이내여도 AI·Main 전달 후 제출 적격을 입증한 것은 아니다.
3. 연구상 상승과 확인점 호가 필수조건을 충족한 CF의 교집합을 보고한다. 실제 제출 가능 여부는 이후 동일 intent의 재검증 증빙이 있을 때만 판정한다. 가격 틱 수만으로 0D 수신 연속성, 미래 재호가 가능성, 실제 주문 가격·수량·체결을 입증하지 않는다.
4. 실시간 거절 사례는 동일 evaluation/intent의 quote 수신→기계 확인→AI→Main 소비 시각과 사유를 연결한다. 해당 자료가 없으면 지연/수신 희소/감시 편입 문제를 임의로 확정하지 않는다.
5. 개선안은 기존 감시 편입 준비, 동일 route 호가의 재사용, 신선한 호가 도착 시 신호 재평가·현재 ask 재계산·중복 intent 방지, 시간 예산 안의 제한된 재검증을 우선 검토한다. quote TTL 완화·UNKNOWN 허용·현재 호가로 과거 ask 대체는 하지 않는다.

## 6. 비교 지표와 검증

라벨은 actual ask·30분·비용률 0.0023·비용 후 목표 +0.4%와 soft −3% 선도달이다. W/STOP/TIMEOUT/U를 분리하며 TIMEOUT은 실제 금전 손실이 아니다. 동일 item의 봉인된 완료 분봉은 원 계약의 검열·경계·동시 접촉 조건을 유지하며 장기 가격을 보조한다. 미래 가격은 라벨에만 사용한다.

scope 자체 분모 `W/(W+STOP+TIMEOUT)`을 우선하고 동률은 W 수와 current·고정 ID 순서를 사용한다. 성공 보존 100%/80%, 최소 일수·표본·별도 EV를 새 탈락 조건으로 넣지 않는다. 분모 없음은 100%가 아니다. 더 높은 비율에서 성공 기회가 줄어든 정도와 승률을 유지하며 W를 최대화한 대안도 공개한다.

검증은 prefix 불변·source break·hold 취소·UNKNOWN·OR, exact key/ask, 독립 선형 가격 라벨, 원 코드/원천 SHA, 기존 current 합계 복원을 포함한다. 낮은 우선순위 최대 2 worker, 각 2GiB/CPU 480초/wall 600초, 불변 partition receipt로 진행한다. 동일 누적 원천에서 가설을 탐색·비교하므로 독립 미래 성과를 입증하지 않는다.

## 7. 완료와 후속 인계

두 연구와 호가 정합성의 수치·반례·관측 한계를 [최종 연구 검토](../audits/main-cumulative-opportunity-failure-and-nonfixed-quote-review-2026-10-17.md)에 기록한다. 운영 적용 가능한 최종 정책이나 배포 완료를 뜻하지 않는다. 연구 후보와 비상시감시 source/consume 계약 개선을 분리하여 기존 [정책 반영 계획](main-cumulative-research-policy-adoption-plan-2026-10-14.md)의 다음 구현에 인계한다. 문서·링크·print-only parser를 검증하고 외부 동기화는 실행하지 않는다.


P0/P1 준비 중 실제 부모가 a2ca8e7d8로 전환되어 이를 통합했다. 이전 운영 profile을 유지한 exact successor 인계와42개 회귀를 추가했다. 후보766a1c3b3는 superseded이며, 최종 native parity/P5·기존 봉인 trailing 보고서의 코드 재검증·준비 root는 [같은 구현 리뷰](../audits/main-post-auxiliary-guards-cumulative-defect-review-2026-10-17.md#실제-부모-변경-후-통합-재리뷰--2026-10-23) 및 result.json에서 확인한다. 이 세션은 통합본 준비 범위를 유지한다.
