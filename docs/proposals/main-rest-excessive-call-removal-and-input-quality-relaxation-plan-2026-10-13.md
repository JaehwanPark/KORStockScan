# Main 과도한 REST 호출 제거·판정 입력 간소화 계획 — 2026-10-13

**후속 승인:** 사용자가 이 계획의 리뷰·보완→구현→반복 코드리뷰·수정보완을 요청했다. 아래의 읽기 전용 문구는 최초 점검 이력이며 이번 작업은 CR0~CR8 코드 구현·오프라인 검증까지 수행한다. 배포/재기동과 자연 성능 수용은 별도다.

**구현 전 리뷰 보완:** CR1은 기존 적격 후보 검사 뒤 첫 실제 후보에만 복구3조회 묶음을 lazy 실행한다. CR2는 판정 뒤 observer에 원 entry deadline/context를 전달해 ENTER_NOW 필요조회가 사라지지 않게 한다. CR4는 native residence가 있는 경로의 모든 사전 candle/tape/context 준비를 신호 뒤로 옮기며 즉시 평가 호환 경로는 보존한다. CR5는 1page와 기존60/90초 주기를 이번 기본안으로 확정하고 별도180초 split scheduler는 추가하지 않는다. CR6은 scheduled wrapper의 BBO OFF와 보고의 명시 결손을 함께 검증한다. CR7은 초기 Main/zero-base 입력만 `reduced_completed_v1`으로 opt-in한다: 최대61개 completed window·raw_same_day/partial reader·선택 MTF 외부조회OFF·full-session feature unknown; holding/재가격/strict 소비자는 기본 계약을 유지한다. CR8은 Main 보유/주문 또는 실제 fixed-watch broker admission 대기 수요가 있을 때45초 refresh를 수행하며90초 reconciliation과 execution receipt callback은 유지한다.

**구현 결과:** CR0~CR8을 작업본에 구현하고 반복 리뷰·수정을 수행했다. [구현 리뷰·검증](../audits/main-rest-call-removal-and-reduced-input-implementation-review-2026-10-13.md)이 최종 코드/시험/남은 실제 수용 상태를 소유한다. 751개 영향 범위 회귀, Python13파일 compile, wrapper syntax 및 문서 parser를 검증한다. 배포/PID와 자연 전체 호출 절감률은 이번 코드 완료에 포함하지 않는다. 아래 원 계획의 읽기 전용/미구현 문구는 최초 이력이다.

**후속 배포 결과:** 사용자 배포·재기동 승인 후 `main-rest-reduction-20261013` / commit `932bb3a1294e3e5b318cdb565fefa87f11d6e28b`를 선택하고 Main PID `3517912`의 정책128/128 scope·상시5종목 WS 실수신을 확인했다. 원 정책/PREOPEN/active pointer는 유지했다. release 회귀1,461건, 목적 없는 선조회0과 19:40 scheduled census의 BBO OFF를 검증했다. 짧은 자연 호출 window는116회/180.64초→17회/182.37초이나 시장 입력/기동 상태가 달라 확정 절감률·동일 부하 성능으로 승격하지 않는다. 기존 cold source replay 지연과 자연 주문/경제성은 미완료다. [후속 배포 리뷰 §7](../audits/main-rest-call-removal-and-reduced-input-implementation-review-2026-10-13.md#7-배포pid-검증과-초기-자연-관측)이 실제 영수증을 소유하며 본문의 미배포 문구는 최초 코드 완료 시점의 이력이다.

## 1. 결정·범위·현재 인계

사용자는 절감계획의 구현·성능·잔여 호출 점검을 요청하며, **판정 품질요건을 완화하더라도 불필요하고 과도한 호출을 제거할 수 있게 점검**하도록 지시했다. 따라서 10/8 계획의 완전한 입력/판정 parity, 전시장 관측 coverage, 수정주가 이력·현재봉 보충을 무조건 유지하는 접근을 변경한다. 소비 없는 조회를 먼저 없애고 선택 입력·발굴 범위·관측 정밀도를 줄인다. 호출을 줄이기 위한 새 계측/worker/구독 증설부터 시작하지 않는다.

근거와 구현·PID·성능 상태는 [10/13 점검](../audits/main-rest-call-reduction-implementation-performance-and-excessive-calls-audit-2026-10-13.md)이 소유한다. 원 [10/8 REST/WS 계획](main-rest-api-ws-substitution-and-load-reduction-plan-2026-10-08.md)과 그 후속 구현은 이력으로 보존한다. 최초 점검은 읽기 전용이었다. 후속 승인에 따라 현재 CR0~CR8 작업본과 scheduled wrapper 기본 수집을 구현했고 정책 발행·설치 cron·릴리스 선택은 실행하지 않았다. 코드 수용과 실제 배포/PID 수용은 독립 증거로 남긴다.

실행 인계는 [현재 checklist](../checklists/2026-10-13-stage2-todo-checklist.md)의 기존 `DirectFamilySourceRepairMainMechanisticEntry`에 연결한다. 이미 진행되는 shared-deadline·joint 작업의 구현/배포 승인을 새로운 source 의미 변경 승인으로 전용하지 않는다. 실제 배포 인계는 당시 유효한 `DirectFamilyPreopenPolicyHandoff` 범위로 처리한다. 경제성·최소 자연 신호/체결·전체 관측 coverage 증명을 호출 제거의 새 선행 조건으로 추가하지 않는다.

현재 Main/manual custody와 broker/account/order/가격·수량·cooldown·hard/protect/emergency 가드는 유지한다. episode/widget 자동 BUY/SELL/CANCEL/retry·workers·수집·연구는 영구 퇴역이다. 역사적 잔고는 operator-managed이며 Main이 채택/청산하거나 flat/terminal을 합성하지 않는다. 퇴역 수량/미결 intent는 Main을 막거나 조회/worker를 복원할 근거가 아니다. 이는 원 10/8의 잔여 episode callback 유지 문구를 대체한다.

## 2. 제거 우선순위와 품질 손실

아래는 **최종 구현 경계**다. 현재 호출 발생 증거와 추정 가능한 절감 한계는 audit의 API/owner 표를 따른다. 특정 호출 전부가 제거 가능하다고 일괄 계산하지 않는다.

| ID | 현재 지점·원인 | 변경 | 허용할 품질/coverage 손실 | 유지할 조건 |
| --- | --- | --- | --- | --- |
| CR0 | `signal_radar._on_realtime_tick`이 소비자 없는 `TRADE_SIGNAL_DETECTED`를 위해 FDR/ka20006 준비 | 기존 EventBus `has_subscribers`로 실제 수신자가 없으면 해당 tick 계산/지수 준비를 생략. scanner가 쓰는 다른 Radar 메서드와 독립 처리 | 소비 없는 이벤트 설명값은 생성하지 않음; 현재 Main 판정 입력 손실 없음 | 수신자가 생긴 경로는 명시 consumer 계약으로 처리. whole Radar 삭제로 scanner를 깨지 않음 |
| CR1 | `_recover_missing_broker_holdings`가 복구 대상 검사 전에 kt00008·kt00007·ka10076 조회 | tracked/active·수량·manual/퇴역 관리 disposition을 먼저 확인. 적격 미추적 Main 잔고0이면 추가3조회0 | 대상0일 때 품질 손실 없음. settlement-only 추가 설명은 필요시 선택 입력으로 축소 | 후보 census 실패/owner unknown을 대상0으로 위조하지 않음. 실제 Main 복구·기동/재접속·미확인 주문은 기존 필요 대사 수행 |
| CR2 | async `refresh_sources_before_evaluate`에서 모든 초기 real 평가의 kt00011 선조회 | 기계 판정 이전의 무조건 prefetch를 제거. 실제 ENTER_NOW의 sizing/예산 소비에 필요한 exact-price 조회만 실행·같은 attempt로 재사용 | BLOCK/RECHECK의 가상 자본/주문가능수량·경제 관측은 cache-only 또는 U. 완전한 비진입 경제성 관측을 위해 실계좌를 조회하지 않음 | 최종 주문가능수량·계좌 세대·정확 가격·2초 receipt·잔량/scale-in/submit 검사 보존. 뒤로 미룬 필요조회가 원5초 안에 끝나지 않으면 기존 만료 처리 |
| CR3 | Main prepare의 `include_investor_source=True`가 판정 전 ka10059 enrich | 초기 기계/compact 준비는 투자자 추가 조회OFF. 이미 받은 snapshot/cache만 선택 소비 | 외인·기관 방향 설명력 감소, 누락은 null/`unavailable` | investor를 필수 price/BBO/tape/candle 원천처럼 강제하지 않음. holding/exit의 다른 필요 consumer까지 일괄 변경하지 않음 |
| CR4 | zero-base probe가 native 신호 대기 전과 후에 분봉을 조회 | 신호 전 조회를 제거하고 실제 native snapshot 발생 뒤 원 deadline 안에서 한 번 준비 | 패턴 미발생 probe의 사전 candle readiness/실패 설명 생략 | native 관측에 필요한 기존 WS packet/route·claim·원5초·실제 진입 preflight 유지. 신호 발생 뒤의 자료를 과거 관측에 backfill하지 않음 |
| CR5 | discovery가 매주기 KOSPI/KOSDAQ gainers 각 최대10페이지 + activity 수집 | gainers `max_pages_limit=1`을 기본 제거안으로 선택. 기존 점심/장후90초 간격을 실제 적용하고, gainers180초/activity60초 분리는 필요 consumer별로 적용 | gainers 순위21~200 발견 감소, 선택적으로 최대180초 발견 지연 허용 | rank는 발굴용이며 최종 fresh quote와 독립. 실제 상한·truncate/조회시각·다음 cycle을 기록; 두 시장 identity를 임의 병합하지 않음 |
| CR6 | census가 executable BBO를 기본ON, `all,liquid_common`·장후KRX/NXT 수집 | 기존 `--skip-executable-bbo`를 이용해 report-only BBO 조회OFF를 우선안으로 둠. 꼭 필요한 보고 목적만 작은 top-N/일 budget으로 별도 명시 | CF 실행가능성/호가 coverage·95% 요건 포기. 독립 발굴/관측 모집단의 기존 기록은 남김 | 수집하지 않은 BBO는0/유효호가/실제 체결로 채우지 않음. sparse/unknown과 주문용 호가를 구별. 종료된 KRX 세션에서 executable quote 보충을 하지 않음 |
| CR7 | candle가 `adjusted_1` 요구로 WS를 항상 거절하고 forming3초/메모리5초로 REST 재검증 | 판정용 raw same-day WS **완성봉**을 명시 소비 계약으로 허용. REST 필요 consumer는 `include_forming=False`로 completed revision 재사용. 430 고정 요청·20개 15분봉/선택 MTF 보충을 소비 field별로 축소 | 수정주가·긴 이력·현재봉·시장/업종/전일 수준의 설명력 감소를 허용. 충분하지 않은 optional field는 unknown | raw/adjusted 이력 혼합·동등성 표기·미래봉·wrong route/epoch는 금지. 현재 source hash/clock/schema와 필수 quote safety 유지 |
| CR8 | 45초 broker snapshot과90초 reconciliation이 중복될 수 있음 | optional holding-context polling은 실제 Main 보유/입력 수요에서만 실행. 최근 동일 scope의 strict snapshot을 사용 가능한 consumer에 재사용 | 비활성 보유 context 최신성만 낮춤 | watch admission의≤60초 verified-flat 계약과 실제 submit/미확인 주문/잔고 보호는 유지. 단순히45초를90초로 늘려 safety snapshot을 stale로 만들지 않음 |

CR0/CR1은 consumer가 없거나 대상이 없는 조회 제거다. CR2~CR6은 이번 사용자가 허용한 설명력·관측/발굴 completeness 감소를 적용한다. CR7은 입력 의미를 바꾸므로 raw 봉을 수정주가 봉으로 속이지 않고 schema/policy consumer를 함께 보완한다. 과거 판정과 완전 일치는 해당 완화 변경의 수용 조건이 아니다.

## 3. 판정용 품질의 완화 계약

시장가격/호가·필수 수량/원 수신시각/정확 route·producer/epoch와 broker/order/account guards는 hard safety다. 선택 수급·현재봉·장기 이력·시장 상대수익률·관측용 가상 capacity·발굴 rank 깊이는 낮출 수 있는 판정/설명 입력이다. 누락을 정상값0이나 정상 snapshot으로 변환하지 않는다.

CR7의 첫 적용은 같은 날짜·route·session의 이미 수신/저장된 WS 완성봉과 현재 native 입력이다. session-start coverage가 없으면 full-session VWAP/opening range를 추정하지 않고 해당 feature를 unavailable로 둔다. 3/5/15분 중 부족한 window도 같은 방식으로 표시한다. 필수 전략 조건이 필요한 feature의 의미를 바꿀 때는 그 consumer의 결손 처리까지 한 변경으로 닫는다. REST를 피하기 위해 잘못된 수정주가·세션 자료를 합치지 않는다.

현재 reader의 `partial=False`/`history_scope=session`·full-session-prefix admission도 소비자별로 바꿔야 한다. `adjusted_1` gate만 제거한 뒤 prefix 결손을 다시 전부 REST로 복구하면 이 목표를 달성하지 못한다. 제한된 recent-window 소비 계약을 reader→selector→feature quality/preflight에 함께 전달하고, full-session feature가 없는 경우 그 field만 unknown으로 만든다. epoch/route·원 journal watermark·유효 row 무결성과 실제 주문 safety는 계속 검사한다.

확정봉을 쓰는 consumer는 forming 없이 검증된 revision을 같은 분 cutoff 동안 재사용한다. 분 경계·가격 정정·기동/재접속·일자/route 전환 시 원천 유효성을 다시 검사한다. `include_forming=False`만으로 과거 요청마다 필요한 HTTP가 모두 사라진다고 주장하지 않는다. provider/server 900행 응답 제한은 caller의 `limit=40`만으로 바뀌지 않으므로 lookback 축소 자체를 wire bytes/HTTP 절감으로 계산하지 않는다.

관측·연구 품질을 낮추면 해당 보고의 W/F/U·CF·실행가능성 분모도 낮아질 수 있다. 누락은 source gap/U로 유지하고 이미 완료된 과거 행을 새 입력 계약으로 재작성하지 않는다. 원천 개선·실 주문/체결·실현 손익은 독립 상태다.

## 4. 순서·변경 위치·검증

1. CR0/CR1: actual subscriber와 적격 복구 후보가 없을 때 추가 HTTP0. 필요한 consumer/복구 후보가 있는 경우 종전 기능 유지. CR1은 신규 module 없이 기존 `sniper_sync`의 대상 검사/요청 순서를 바꾼다.
2. CR2/CR3/CR4: 판정 전 account/investor/probe 선조회 제거. ENTER_NOW 필요조회는 정확 가격/계좌 generation과 원 deadline으로 실행하며 BLOCK/RECHECK·무신호 probe에 새 조회를 하지 않는다. stage clock과 observer U 처리까지 함께 검증한다.
3. CR5/CR6: source-only 발굴/관측의 page/주기/BBO 수집을 축소. wrapper/automation 변경은 운영 owner 문서와 당일 checklist를 함께 갱신한다. scheduled wrapper의 기본 BBO OFF를 코드에 반영하며 현재 설치 cron/선택 runtime 명령은 실행하지 않는다.
4. CR7/CR8: source 의미·freshness의 실제 consumer를 좁혀 적용. 기존 `trading/market`·`scalping`·`monitoring` owner를 사용하고 새 engine-root 모듈이나 epoch/receipt 체계를 만들지 않는다.

프로토콜/request/parser/REG/recovery에 영향을 주는 구현은 [Official Kiwoom Reference Gate](../kiwoom-api-data-contract.md#official-kiwoom-reference-gate)를 착수 시 다시 적용한다. 공식 `953e5dbff123f437ab4d11a78a95191a685eb51f`와 관련 spec/core/realtime은 이번 점검에서 확인했지만 향후 영구 pin으로 사용하지 않는다. 신규 패키지·API/provider/실주문 호출 없이 보존 fixture와 injected fake transport로 검증한다.

오프라인 검증은 제거 대상의 **실제 transport attempt0/정확 상한**, 선택 입력의 null/unknown 처리, 현재 원 claim clock·최종 quote/account/order/exit 가드 유지다. Radar actual subscriber 없음/있음, 복구 후보0/실Main/퇴역/manual/unknown, BLOCK/RECHECK/ENTER_NOW·가격 변경·late response, 무신호/신호 probe, 1페이지/분리 주기, census skip·기존 report consumer, raw/adjusted 분리·forming 제외·분 경계·재접속을 회귀한다. 모든 판정 결과/관측 completeness를 종전과 같게 만드는 시험을 새로 요구하지 않는다.

## 5. 호출·성능 수용과 롤백

이미 있는 `kiwoom_client_attempts_v1`을 사용한다. Main은 PID/start/release별 누적 snapshot delta, census는 request meta/capture ID·원 offsets로 물리 시작을 대사한다. 다른 PID·다른 세션·census/Main을 중복 합산하지 않는다. admission/cache/logical demand/HTTP attempt/page/retry와 timeout을 구별한다. minute/최근 attempt retention이 지워져도 cumulative total을 버리지 않는다.

before/after는 동일 목적의 수요당/분당 actual attempts, 유지한 데이터의 valid/unknown, caller·provider 전·loop/WS last-consumer 지연, queue/drop/CPU·I/O를 비교한다. 관측/발굴 수요를 의도적으로 낮춘 CR5/CR6은 **coverage 감소에 의한 절감**으로 따로 기록한다. 원5초를 넘긴 새 필요조회는 기존 fail-closed이며 호출 감소만으로 실행 품질 성공을 주장하지 않는다. PID 교체·정책 변경·시장/host 입력률 차이를 같은 부하의 개선율로 계산하지 않는다.

각 CR의 코드 종료는 해당 소비부/모의 transport 회귀·compile/diff로 닫는다. 실제 배포·PID/정확 날짜 policy 소비와 자연 호출 감소는 당시 handoff owner가 별도 확인한다. quota5회/초보다 평균률이 낮다는 사실은 과도한 조회를 유지할 근거가 아니다. 새 50%/95% 목표·표본/체결 경제성 gate를 추가하지 않으며 전후 실제 분모와 tradeoff를 보고한다.

롤백은 검증된 Main-only 호환 consumer/adapter다. 퇴역 executor를 되살리거나 빠진 입력을 stale/0으로 대체하지 않는다. hard safety·Main 복구/청산 누락·wrong route/schema·중복 주문을 발견하면 해당 변경을 기존 안전 절차로 되돌린다. 설명력/관측 coverage의 예정된 감소를 자동 runtime 재기동이나 퇴역 원천 복원 사유로 삼지 않는다.
