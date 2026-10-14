# 최신 Main 재기동 이후 제출병목 점검·구현계획 — 2026-10-14

## 1. 최신 기준과 승인 범위

사용자의 후속 지시는 최신 배포본 기준 계획 보완, 글로벌 위기 감지 기능·문서 제거, 제시한 timeout 6건의 원인·AI 시간 예산 검토, 구현→반복 리뷰·수정·검증 후 배포·Main 재기동이다. 이 문서는 이전 읽기 전용 계획을 대체한다. 구현·코드 검증·실제 PID 소비·자연 제출·경제 성과는 각각 판정한다.

착수 기준은 **18:18:06 실제 소비 receipt의 f71c7d5f9 / PID1025115 / start_ticks3338102**이며 selected root는 `/home/ubuntu/KORStockScan-runtime-releases/observer-population-partition-20261014-f71c7d5f9`다. [선택 동결](../../tmp/submit-crisis-timeout-20261014/selection-before.json)의 전체 commit·이전 release·실제 cwd를 원본으로 사용한다. 구현은 이 commit에서 분리한 worktree에서 수행한다. 기존 workspace의 미커밋 변경을 묶어 배포하지 않는다. 배포 직전 selector/PID/start·정책·문서 hash를 다시 비교한다.

[Plan Rebase §1–§8](../plan-korStockScanPerformanceOptimization.rebase.md), [당일 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md), [ordered release 계약](../runtime-release-routing.md)을 따른다. native bundle `99c894cb018ee594c9767bb6b9d9de544e1019587fb5379605136e0adbb48215`, 원 PREOPEN/source/publication10/13→effective10/14, Main/manual custody·퇴역 owner·operator veto·가격/수량/계좌/주문/quote·cooldown·hard safety를 유지한다. 기존 auxiliary overlay `e79262dfbb296dd8bd643c2c6f20621ee97d5a5ebc3eae7ad24a2105c02592ee`는 이 요청으로 승인한 응답 계약 successor만 CAS 발행한다.

## 2. 이미 배포된 보완과 남은 범위

첫 구현은 `7c517c9206437cfb1c84a8206f6a2a6de12839a9`로 배포했고, 19:21:44 receipt의 PID1157212/start3720079가 소비했다. 아래 f71 분모는 착수 시점의 고정 증거다. 새 PID의 종목 원천은 3906건/시장별 물리 HTTP 1회로 완료했으며, 고정5 중 주성·HPSP의 원천 NXT 자격은 false다. 두 종목은 새 원천으로도 해당 경로에서 차단되어야 한다. 새 자연 AI 표본이 없는 상태를 timeout 개선이나 제출 성공으로 기록하지 않는다. 첫 정규 observer의 19:25·19:30·19:35·19:40 실행은 각각 175초 제한으로 실패했으므로 배포 수용을 완료하지 않고 아래 후속 수리를 수행한다.

| 항목 | 최신 f71 기준 판단 | 이번 범위 |
| --- | --- | --- |
| Main ready hint/방문 | 실제 방문 ACK·token 보존·WATCHING bounded 재방문·phase clocks 반영 | 중복 queue/wake를 추가하지 않고 남은 요청 내 중복 검증 제거 |
| raw/valid/executable PASS | B0 provenance와 semantic terminal 구분 반영 | prompt 안내만으로 해결되지 않은 공통 fact를 기존 compact wire 구조로 요구 |
| entry-split 대용량 projection | full 검증·작은 receipt 소비·routed root 수리 배포 | 기존 완료 구현을 다시 열지 않음 |
| observer PID/분모 | 현재600초/PID, 역할별 provider population·완료 후 health·예약 대기 수리 반영 | 정상 경보 숨김이나 generic grace 추가 없음 |
| 비고정 원천 | 당시 결손과 no-match 구분 필요 | 원45 terminal을 원천 seq/epoch와 재대사; 재현된 전달 결함 없는 곳은 변경하지 않음 |
| 위기 감지 스캐너 | 독립 RSS daemon·DB 저장·알림·필수 heartbeat가 남음 | 기능 및 설명·설정·호출·의존성 선언 제거 |

선행 구현은 [B0–B4 리뷰](../audits/main-nonfixed-submit-bottleneck-implementation-review-2026-10-14.md), [entry-split/Main 전달과 후속 observer 리뷰](../audits/entry-split-projection-and-main-delivery-implementation-review-2026-10-14.md)에 남긴다. 현재 selector의 준비/소비를 과거 PID의 timeout·성과로 대체하지 않는다.

## 3. 현재 제출 분모와 과거 비고정 원천의 재대사

**현재 f71/PID1025115의18:23:27–18:35:07 고정 trace 분모**는26요청/20응답/6timeout, raw PASS10/semantic-valid PASS7/executable PASS1이다. 이 값은 [현재 PID auxiliary census](../../tmp/submit-crisis-timeout-20261014/current-pid-auxiliary-trace-census.json)의 완전한 newline prefix37,564,240B 기준이며 전체 Main 기회/계좌 주문 census를 대신하지 않는다. 응답-invalid8은 공통 support3·중복 citation3·unbound nonpass2다. native path changed13은 이 분류와 중첩하므로 더하지 않는다.

executable PASS1은 [동일 attempt의20행 대사](../../tmp/submit-crisis-timeout-20261014/current-pass-main-lineage.json)로 확인했다.18:33:39의 budget pass 후 CAUTION weak_momentum 보류, 같은 attempt의 다음 호출에서 SAFE/budget pass→2주 sizing(즉시1/보류1)→18:33:40 `ORDER_TYPE_PREFLIGHT_BLOCKED`로 끝났다. 원 request type3/price0이 NXT type6/price0으로 remap된 로컬 preflight 실패이며 broker reject나 체결 실패가 아니다. 이 새 결함을 기존 source·order-type 계약 owner에서 수리한다. Kiwoom 공식 revision·NXT 주문 필드/가격 의미와 local consumer를 먼저 확인하며 임의 type 허용·가격/수량·route guard 우회는 하지 않는다. 뒤에 같은 async ID만 남은 다른 evaluation4행은 제외한다.

과거 창의0분모를 현재에 적용하지 않는다. 현재는 유효 PASS+budget 이후 **로컬 venue eligibility preflight 차단1건**이 확인됐으며, 일반 과차단 해소·제출/체결·경제성 수용은 별도다.


기존 **13:06:32–13:48:00, PID378870/f8dc4431d** 창은 역사 증거다. 고정5 중 삼성 ENTER_NOW3→보조 AI3(유효 CAUTION1/timeout1/raw PASS semantic-invalid1), executable PASS0, 관측 budget/intent/submit각0이었다. 유효 PASS+budget 통과 후 과도한 submit 차단 가설은 분모가 없어 미판정이었다. 13:36의 native→Main claim3.105363초와 freeze1525ms/HTTP777ms는 이후 배포와 섞지 않는다.

비고정47 claim 중45 terminal+cutoff pending2, terminal은 source_unavailable32/no-match10/incomplete3이었다. [원 funnel](../../tmp/latest-restart-submit-review-20261014/funnel-window-130632-134800-v1.json)과 [원 terminal census](../../tmp/latest-restart-submit-review-20261014/nonfixed-terminal-census-130632-134800-v1.json)는 불변이다. [이번45건 재대사](../../tmp/submit-crisis-timeout-20261014/nonfixed-original45-source-reconciliation.json)는 원 행 hash와 epoch/sequence를 연결한다. native stale10건은 terminal/native 신원이 일치하고 실제 age4.220–73.572초다. route snapshot 부재16건은 당시0B/0D 도착0/0으로, 수신 후 downstream 전달 유실을 입증하지 않는다. 나머지 quote age/부재·censored·confirmation pending·window incomplete도 각각 보존한다.

새 Kiwoom 요청·REG/REMOVE·FID·fallback·stale 완화는 이 증거로 정당화되지 않는다. 과거 source_gap은 현재 원천으로 소급 보충하지 않는다. 정규 슬롯·실제 새로운 비고정 신호에서 source→Main attach를 기존 owner로 수용한다. 원45+pending2와 다른 PID의 새 분모를 합치지 않는다.

## 4. 제시한 OpenAI timeout 6건의 원인

[요청·trace 요약](../../tmp/submit-crisis-timeout-20261014/timeout-six-summary.json) 및 같은 디렉터리의 원 request/SDK terminal/native timeline을 사용한다. 모두 `analyze_target`, 물리 시도1회이며 wall-clock budget 소진이다. 이 표본에429·호출량 포화 근거는 없다. API키 index만으로 특정 키 장애를 단정하지 않는다.

| 로그 시각·종목 | 실제 PID / release | native→claim ms | analyze→provider ms | HTTP 예산 / 로그 provider ms |
| --- | --- | ---: | ---: | ---: |
|14:52:51 주성|574420 /08dbea37c|59.7|951.5|3475 /3461|
|14:57:55 HPSP|574420 /08dbea37c|138.0*|1679.9|2673 /2661|
|14:58:10 HPSP|574420 /08dbea37c|1836.4*|747.4|1936 /2032|
|16:21:28 삼성|679747 /945c30637|1276.3|417.7|2880 /2867|
|16:21:32 삼성|679747 /945c30637|1675.8|385.9|2479 /2591|
|17:40:23 주성|937055 /7ee50c621|1833.1|663.7|2101 /2086|

`*`는 같은 PID monotonic/epoch clock pair로 재구성한 값이며 직접 lifecycle wall-clock와 구분한다. claim→analyze는155.9–242.0ms, SDK queue는0.052–4.252ms, HTTP 직전 local12–16ms, lock wait0이다. nested 구간을 중복 합산하지 않는다. 신호 발생→Main 방문·준비가 먼저 원5초를 소비한 뒤 provider가 남은1936–3475ms 안에 끝나지 못했다. 각 timeout의 provider 시간이 매번5초인 것은 아니다.

14:58:10·17:40:23은 SDK가 응답을 실제 받았으나 예약된 transport cutoff 이후였다. 원 native deadline까지 남은 monotonic 시간은 각각79.7/74.7ms에 불과했다. 나머지4건의 원 physical receipt에는 response_received=false이며 세부 terminal exception type은 기록되지 않았다. 응답 미관측을 서버 미전송이나 특정 네트워크 장애로 확대하지 않는다. 과거 늦은 응답을 주문에 재사용하지 않는다.

### AI 시간 예산 결정

1. HTTP timeout 설정만5000→8000ms로 바꾸어도 실제 예산은 원 native 만료시간으로 제한되어 효과가 없다. native5초→8초는 신호·overlay 선택·응답/submit 검증과 replay 계약 전체의 의미 변경이다. 이번 자료만으로 원 신호를 더 오래 거래해도 안전하고 유리하다는 근거가 없으므로 채택하지 않는다.
2. response reserve250ms(마지막154ms)를100ms로 고정 축소하면 최대150ms를 더 기다리지만, 위 늦은2건은 최종 검증에75–80ms만 남았다. 최신 응답 처리의 꼬리 지연도 있어 실제 salvage가 입증되지 않는다. 임의 reserve 축소·timeout retry·늦은 응답 salvage는 적용하지 않는다.
3. **같은 요청의 중복 registry 검증과 응답 표현 비용을 줄이고 실제 provider 여유는 배포 후 측정한다.** `validate_decision`이 원 generation/native age/revocation 검증을 전부 마친 registry를 반환하고 `validate_before_provider`가 그 결과로 model 일치를 확인한다. 요청 간 cache·검증 생략·만료시각 갱신은 도입하지 않는다. 실제7 registry×13 fixture91쌍의 [결정적 비교](../../tmp/submit-crisis-timeout-20261014/auxiliary-wire-deterministic-comparison.json)에서 논리 입력/원 prompt/schema는 동일하고 canonical PASS bytes는364→106, input+schema+prompt 합계는8237→7404로 감소했다. provider latency·토큰 청구·경제 성과 측정은 아니다. 중복 registry load만의84쌍 교대 측정 중앙값은0.253→0.157ms로 이득0.096ms에 불과하므로 이것만으로 timeout 해소를 주장하지 않는다. 기존 모델·reasoning none·출력 상한1024토큰·호출/재시도 수는 유지하며, 시간 예산 소진을 출력 토큰 부족으로 해석하지 않는다.
4. 적용 후 같은 PID/attempt의 native→claim→준비→SDK→validation→Main 소비와 timeout/censored 분모를 확인한다. 여전히 provider 잔여 예산 부족이 지배적이면 원5초/8초 각각의 동일 source fixture·quote freshness·늦은 응답 최종 guard·비용/기회 결과를 별도로 비교한 후 정책 owner에서 재검토한다. 이번 구현 closure에 새 경제성 gate를 추가하지 않는다.

## 5. 공통 PASS 응답 계약 수리

owner는 기존 `AuxiliaryCircuitRecoveryRepair1012`와 `DirectFamilySourceRepairCompactAuxiliary`다. 13:47의 branch namespaced fact만 인용한 raw PASS는 계속 invalid로 보존한다. 이미 발행한 prompt 안내를 반복 추가하는 대신 **기존 v2 compact citation codec**을 정확한 incumbent v1 registry의 구조 successor로 발행한다.

- root object·필수 assessed signal map·nested screen anyOf를 사용한다. PASS는 NO_BLOCKING_RISK와 실제 공급된 공통 observed_machine_signal alias를 요구한다. CAUTION/VETO는 실제 공급 risk와 그 risk에 결속된 fact를 요구한다. unknown/missing/branch-only/partial refs·잘못된 risk·원천 변조를 거부한다.
- lossless alias를 기존 logical response로 decode한 뒤 기존 semantic validator·Main guard를 그대로 통과시킨다. raw provider 응답은 불변이며 누락 common fact를 자동 보충하거나 판정을 PASS로 바꾸지 않는다.
- 모델gpt-5.4-nano, reasoning none, 원 prompt/논리 입력/판정 arm·128scope·기계 정의·신호5초·가격/수량은 유지한다. 기존 wire suffix/codec만 적용한다. registry의 historical research 필드명은 원 definition을 가리키는 호환 표면이며 `research_executed=false`, `provider_called=false`, `policy_reselected=false`를 새 sealed manifest에 명시한다. 연구 실행·경제성 선정으로 보고하지 않는다.
- exact 원 report·overlay·registry·source/code hash, full128 old/new binding, parent CAS, same-day 권한, idempotence·immutable ancestry·rollback을 검증한다. 새 schema manifest는 기존 prompt-repair reader와 공존한다. 과거 확인시각의 요청은 과거 overlay를 선택한다.

2026-10-14 확인한 [OpenAI Structured Outputs 공식 문서](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)의 object/required/additionalProperties/중첩 anyOf 지원 범위와 기존 codec을 사용한다. 문서 지원 확인·로컬 반례시험과 실제 provider 수용은 별도이며 검증용 외부 AI 호출은 실행하지 않는다.

## 6. 정상 PASS 이후 NXT eligibility 생산·전달 계약 수리

18:33:40 로컬 preflight의 정확한 원인은 type6 자체가 아니라 `eligibility_unknown`이다. Main 초기 주문 caller가 canonical eligibility를 전달하지 않았고, market wrapper는 explicit NXT 입력에도 SOR 전용 승인 함수를 적용해 전달받은 evidence를 지웠다. 또한 당일 canonical ledger 생산이 EOD20:05에만 있어 장중 exact-date 조회는 비어 있었다. 단순 caller 인자 추가만으로 closure를 주장하지 않는다.

[공식 Kiwoom 확인](../../tmp/submit-crisis-timeout-20261014/official-kiwoom-order-reference.json): upstream commit `953e5dbff123f437ab4d11a78a95191a685eb51f`, 조회18:41:01.541922KST. 해당 revision에 kiwoom_docs가 없어 specs·packaged spec·core client/auth/errors·PRD/MOCK Postman을 대조했다. kt10000의 venue/type/price·응답·오류·real/demo 경계를 확인하고, ka10099 종목정보의 명시적 nxtEnable을 canonical source로 사용한다. upstream 열거값이 특정 종목의 현재 적격성을 대신하지 않는다.

1. 기존 공식 bulk collector와 canonical DB 저장 계약을 재사용해 Main 시작·거래일 변경 시 진입기회 바깥에서 당일 snapshot을 생산한다. 성공 snapshot은 같은 Main 프로세스·KST 날짜 안에서 재사용하며 재기동은 새 관측을 수행한다. 실패는5분 간격·날짜당 최대3회로 제한한다. 시장별 최대8페이지, 일반 전송 `max_retries=1`, connect/read timeout1/2초와 rate admission 최대1초를 사용하며 기존 인증복구1회는 별도다. 신규 cron/daemon이나 매 주문 동기 API 조회를 만들지 않는다. EOD writer와 공동 owner를 사용하되 EOD 전체 보고·시세 적재는 재실행하지 않는다.
2. Main 초기 주문→market wrapper→preflight에 exact stock/date/provenance eligibility를 전달한다. explicit NXT에서는 SOR 전용 승인 helper를 호출하지 않으며 SOR 경계는 유지한다.
3. ka10099는 NXT 플래그를 제공하지만 KRX aftermarket 필드는 제공하지 않는다. 따라서 원 record의 PARTIAL/unknown KRX를 보존하면서, **explicit NXT에만** exact-date·종목·API/revision/time/payload hash·nxt=True와 알려진 KRX-only 결손을 확인한다. 모순·불명 source·다른 blocker·False/None·stale/date mismatch는 계속 거부한다. SOR/KRX의 unknown을 NXT evidence로 통과시키지 않는다. 주문 price/quantity·최종 quote·계좌/custody/cooldown 검증은 유지한다.
4. 실제 과거036930 당일 row 부재는 불변이다. 새 natural snapshot·새 PID의 exact-date row와 실제 다음 주문 preflight를 확인하며 옛 attempt 재주문·provider test 주문을 만들지 않는다. 가격0/type6은 기존 공식 remap 의미를 유지한다.
5. 완전한 전체 목록을 다시 받았는데 빠진 당일 기존 ka10099 종목은 같은 DB transaction에서 UNKNOWN/`official_source_row_missing`으로 갱신한다. 이전 NXT=True가 당일 row라는 이유만으로 남지 않게 하며, 새 원천 row·payload hash·누락 처리 전 원 row를 immutable attempt receipt에 보존한다. 이 누락 처리는 다른 API 원천·과거 날짜·EOD의 명시적 일부 종목 저장에는 적용하지 않는다. 수집/저장 PASS는 각 종목의 적격성이나 실제 주문 성공을 뜻하지 않는다.

## 7. 글로벌 위기 감지 기능·문서 제거

대상은 16:31:09의 `글로벌 위기 감지 스캐너 가동...`을 생산한 독립 기능 전체다. `src/scanners/crisis_monitor.py`와 전용 테스트, bot_main의60분 daemon/startup·heartbeat, 필수 heartbeat registry, RSS5개 feed·keyword·번역·중복/throttle·Telegram 알림·alert state writer, DBManager 저장/조회 API와 MacroAlert ORM을 제거한다. 기능 전용 feedparser/deep-translator 의존성 선언도 제거한다. 설치 환경의 패키지 uninstall은 필요하지 않다.

운영 runbook·semantic monitoring 계획 및 해당 기능을 설명하는 과거 checklist/review/archive 문서9개의 기능 참조를 정리한다. 활성 cron·UI·기타 caller 검색과 startup/process-health 반례시험으로 누락을 확인한다. 기존 실제 DB table/행·alert state·로그·봉인 release와10/7 원천 census의2892행 측정 증거는 파괴하지 않는다. 이는 퇴역 기능을 유지하는 설정이나 consumer가 아니다. 새 Main은 daemon·등록·heartbeat를 만들지 않으며 모니터는 삭제된 daemon을 missing으로 요구하지 않는다.

## 8. 18:36:07 artifact_freshness 경보 추가 수리

사용자가 제공한18:36:07 경보 텍스트와 회수 가능한 후속 `submission_bottleneck_monitor` 보고서·publication generation·PID/start·window를 구분하여 보존한다. [회수 manifest](../../tmp/submit-crisis-timeout-20261014/alert-183607/manifest.json)에 기록했듯 원 경보에 연결된 exact artifact는 회수하지 못했고 alias는 이미 갱신되어 있었다. 보존한 후속 보고서의 `as_of`는18:36:19.746942, `source_as_of`는18:35:13.923993이며 별도 detector는18:38:45다. 이를 원18:35 보고서나18:36:07 detector라고 인용하지 않는다.

후속 보고서의 `no_identified_scanner_machine_evaluation`은 scanner promotion cohort 부재이며 전체 Main 평가0을 뜻하지 않는다. fixed-watch 평가68건은 해당 보고서가 읽은45분 모집단이고 현재 PID의600초 health 분모나 앞의26요청 분모와 다르다. 현재 PID health에서 async PASS 미연결과 원천 window 불완전을 확인했으며 재현된 두 계약 결함을 수리한다. 원 artifact 부재 때문에 후속 fixture의 모든 수치를 원 경보 시각의 확정 사실로 소급하지 않는다. 단순 alert_count 감소를 종료 조건으로 사용하지 않는다.

`source_gap_semantics.diagnostics`의0B_age_exceeded/0B_missing/native_no_matching_pattern/native_observation_incomplete는 실제 source gap·정상 no-match·window 미성숙을 분리한다. 잘못된 producer/consumer population이나 원천 미연결은 수리하되 source_gap/partial을 정상·valid_empty로 덮거나600초 freshness를 늘리지 않는다. 실제 현재 계약 오류·미확인 PASS·실패/모순 제출은 계속 FAIL이어야 한다. 원18:36 경보는 실패 이력으로 보존하고 새 코드의 동일 frozen fixture와 후속 정규 publication/health를 따로 확인한다. 구체적 producer 결함은 `record_async_disposition`이 Main guard의 completion clock을 중복 keyword로 받아 TypeError를 발생시키고 accepted/rejected 기록을 누락한 것이다. 같은 원 사실의 동일 중복만 수용하고 identity/clock 불일치는 거부하도록 수리한다. 과거 누락 terminal을 합성하지 않는다.

원32MiB tail은 현재 속도에서10분을 덮지 못하고, 기존 compact index는 probe/fixed-watch wait stage를 저장하지 않았다. 기존 index의 해당 stage 보존과 exact offset/epoch window projection을 forward migration으로 확장한다. 원 cache cursor·이전 stage coverage·raw generation·partial line/parse 오류·한도 초과를 보존하고,새 stage가 생산되기 전 과거에는 complete를 부여하지 않는다. 기존 평가 분모에는 source 전용 stage를 섞지 않는다. API·기계판정·주문에 권한을 부여하지 않는 observer source 수리다. 새 PID 시작 전의 검증된 source activation 또는 다음600초 coverage가 충족된 뒤 자연 보고서의 complete 여부를 수용한다. 이 작업은 기존 `NonfixedDispatchReadinessReview1012`/`DirectFamilyPreopenPolicyHandoff` 수용에 포함한다.

배포 준비는 기존 cursor가 검증된 경우에만 최대4회×32MiB append를 허용한다. cache가 없거나 cursor/raw generation이 맞지 않으면 당일 전체 재색인을 실행하지 않는다. reader는 identity index·선택 row 해제·raw suffix에 각각32MiB 한도를 적용하고 초과·변조·부분 행·coverage 부족을 정상 complete로 바꾸지 않는다. [고정70행 비교](../../tmp/submit-crisis-timeout-20261014/alert-183607/frozen-source-window-parity.json)의45 async/25 probe는 필드·semantic 동등성을 검증한 오프라인 fixture다. 그 통과는 당시 실제10분 원천 완전성이나 새 자연 보고서의 정상화를 증명하지 않는다.

## 9. 검증·배포·종료 조건

구현→self review→독립 review→수정→재리뷰→표적 시험을 반복한다. 최종 기록은 [구현 리뷰](../audits/main-submission-crisis-timeout-implementation-review-2026-10-14.md), `tmp/submit-crisis-timeout-20261014`의 테스트·parity·review·gate를 owner로 삼는다. production/test 위치는 기존 scalping/ai/monitoring/infrastructure/database/scanners·utils와 trading/market 및 src/tests만 사용하며 engine root 신규 모듈은 만들지 않는다.

| 범위 | 검증 |
| --- | --- |
| schema/인계 | registry/wire/contract/transition/compatibility/manifest 반례, full128 scope, 원 raw/history 보존 |
| timeout/중복 | native deadline·generation/revocation/model 거부 동일, 요청내 단일 registry 검증, shared deadline·async bridge·transport circuit |
| 위기 제거 | bot import/startup schedule·scanner import·process health/coverage·DB 관련 표적시험, 남은 caller/문서 검색 |
| native·배포 | baseline/candidate128scope parity·코드 hash·policy unchanged, bootstrap/ordered handoff/readiness/actual PID receipt |
| 문서 | 로컬 링크·현행 owner 각1개·AUTO 불변·print-only parser·diff/compile |

NXT 수리로 native 계약 module33개 중 `session_contract.py`1개가 바뀐다. 정의·정책값이 같아도 NXT 수정 전의128scope parity를 최종 후보 검증으로 재사용하지 않는다. 최종 session source hash에 결속한 baseline/candidate128scope fresh parity와 publication/readiness를 다시 확인한다.

원 PREOPEN→후보 AI·Main 주문 caller·async/observer 등 인계 계약 대상 경로의 정확한 SHA쌍을 `intraday_release_handoff.REVIEWED_SUBMISSION_TIMEOUT_SOURCES`에 추가한다. 각 pin은 검토된 최종 bytes만 허용하며 기존 허용쌍·dirty/origin/candidate 변조 거부를 유지한다. 전체 변경 파일의 검토와 immutable release 검증은 이 제한된 source-pair 목록과 별도로 수행한다.

배포 전 reviewed commit의 immutable root와 shared mounts를 만들고 selector/actual PID·정책·문서 원 bytes가 착수 snapshot과 같은지 확인한다. 원 auxiliary report와 e792 overlay의 후보 reader 호환 증거, native code handoff를 먼저 발급한다. release-set/detector/Sentinel lock 아래 기존 Main graceful drain→선택·문서 publication→별도 auxiliary CAS→native prepare/reader readiness→singleton Main 기동·attest 순서로 진행한다. 보호 정책11개 중 auxiliary current pointer만 승인한 exact successor로 전이하며 나머지는 불변이어야 한다. 실패하면 원 시도/hold·receipt를 보존하고 다른 owner 상태를 강제 해제하지 않는다.

배포 후 commit/PID/start/cwd·native bundle·auxiliary registry/manifest 실제 소비, 위기 daemon/heartbeat 부재, startup health와 정규 예약 observer를 확인한다. `DirectFamilyPreopenPolicyHandoff`가 배포 소비, `AuxiliaryCircuitRecoveryRepair1012`가 다음 정상 시도의 응답→Main→budget/intent/submit·broker receipt, `NonfixedDispatchReadinessReview1012`가 전체 fixed/nonfixed·source·정규5분3슬롯을 소유한다. 기존 stable ID·Due/Slot/TimeWindow·Acceptance/History/AUTO를 보존하고 새 OPEN을 중복 생성하지 않는다.

코드·계약 수리 종료는 실제 자연 주문·positive EV를 요구하지 않는다. 자연 유효 PASS가 없으면 과차단 가설은 pending, 미래 scheduled source는 not_yet_due, fill/terminal·비용 후 성과는 null/미입증이다. source_gap·정상 no-match·표본 부재는 자동 rollback 사유가 아니다. 계약 실패 시 검증된 code+sealed registry/overlay 조합으로 기존 rollback owner를 사용하며 퇴역 위기 daemon을 복원하지 않는다. 외부 Project/Calendar sync·검증용 주문/provider replay·광범위 보고 재생성은 이 검증에 포함하지 않는다.

## 10. 첫 배포 후 Sentinel 실행 실패의 추가 보완

[첫 배포 observer 검증](../../tmp/submit-crisis-timeout-20261014/postrestart-observer-verification.json)의19:25/19:30/19:35/19:40 정규 실행은175초 제한을 소진했다. 준비 단계가 source cache만 전진시킨 인덱스 불일치를 수리하며, 그 하나로 첫 두 실행 실패 전체를 설명하지 않는다.19:35 자연 실행의 `/proc` 읽기에서는 전일7,394,107,688B raw pipeline_events 원천을 다시 읽는 것을 확인했다. 원 콜백 두 함수의 AST는 동일하지만 소속 `buy_funnel_sentinel.py` 전체 파일 hash가 바뀌어 summary 계약이 달라졌고, 동일 계약 불일치가 반복 재구축 경로를 열었다.19:35 자연 프로세스의 전일 raw 읽기는 FD로 직접 확인했지만 슬롯별 전체 읽기량은 측정하지 않았다. [계약 진단](../../tmp/submit-crisis-timeout-20261014/sentinel-summary-callback-rebuild-diagnosis.json)을 원 실행 실패 증거로 보존한다.

기존 summary producer 안에서 정확히 검토한 이전 parser/callback 계약을 현재 계약으로 이행한다. 별도 monitoring helper가 exact source hash와 callback의 전이 의존 함수·상수 동등성을 검증하며, 원 manifest/checkpoint·raw identity/offset·summary generation 검사를 그대로 적용한다. 현재일과 전일 모두 동일 producer가 bounded append를 수행하고 이전 manifest를 보존한다. 알 수 없는 계약·변조·한도 초과는 실패이며 원천 재스캔이나 제한시간 증액으로 덮지 않는다. native compact index 구현과 Main/AI/native 정책 계약은 바꾸지 않는다.

후속 변경은 분리된 `tmp/submit-crisis-timeout-20261014/observer-prepare-followup`에서 리뷰·시험·배포 receipt를 남기며 첫 배포 증거를 덮어쓰지 않는다. 새 PID와 정규 보고서/후속 detector까지 검증한 뒤 코드·배포 수용을 구분해 기록한다. 새 자연 AI/주문 표본이 없는 경우 timeout 개선율·실제 제출·체결·경제성은 미판정으로 남긴다.

[19:50 후속 검증](../../tmp/submit-crisis-timeout-20261014/postrestart-observer-successor-1950.json)은 기본 Sentinel이 약174.6초 뒤 성공했지만 observer 최소20초가 남지 않아 wrapper가75로 종료했음을 확인한다. 기존 총180초/최종 cleanup5초 안에서 첫 Sentinel 단계에 최대130초를 부여하고 observer40초와 첫 child 종료여유5초를 먼저 확보한다. 빠른 성공은 full observer로, 첫 단계 실패는 원 실패코드를 보존한 source-only 진단으로 이어진다. source-only의 현재 원천 진단 발행을 full Main semantic PASS로 승격하지 않는다.

최종 검증이 정규 슬롯 종료 뒤에 끝나면, 승인된 배포 검증으로 기존 보고 생산자의 현재 PID·세대 결속과 출력 계약만 동일한 시간 상한에서 확인할 수 있다. 검증용 알림·주문·AI 호출은 수행하지 않고 수동 검증을 자연 정규 슬롯 수용으로 세지 않는다. 기존 자연3슬롯 owner와 원 결손·경제성 미판정은 유지한다.

[19:55 자연 후속](../../tmp/submit-crisis-timeout-20261014/postrestart-observer-successor-1955.json)은 실행과 현재7c/PID의 발행은 완료했지만 의미 검증은 partial이었다. 정규 completed publication1회와 full coverage 수용0회를 구분한다. 정확한 terminal-session 원천 및 고정 watch 경계·기존 incident를 추가 대사하며 이 관찰만으로 경보 해소를 선언하지 않는다.

[정확한290행 대사](../../tmp/submit-crisis-timeout-20261014/natural1955-observer-diagnosis.json)에서 원천은 최근600초를 완전히 덮었으며 모두 Main fixed-watch의 정상 진입 금지 대기였다. 기존15:30–16:00 경계에 더해 native resolver가 확정한19:40–19:45 CLOSE_ONLY와19:45–20:00 TERMINAL_EXIT만 정확한 venue/session 조합으로 인정한다. MAIN_FIXED_WATCH·고정종목·source quality pass·entry_allowed_by_clock=false·actual_order_submitted=false·broker_order_forbidden=true를 모두 요구한다. 잘못된 필드형·세션·시각·venue·owner·주문 증거는 계속 거부하며20:00 이후 CLOSED를 일반 허용하지 않는다.

이는 원천 검증의290개 정상 대기 오분류만 수리한다. 회수한18:36:19 보고서와 동일한 과거 incident 객체 및 source_as_of19:15:13은 그대로 보존한다. 원 fixture의 semantic partial·current_observation_verified=false·full_coverage=false·runtime apply 금지를 유지하고 건강 판정만 bounded source-quality observation의 warning_pending으로 바뀐다. 과거 결손 회복·현재 AI 판단·자연 주문을 합성하지 않는다. 최종 monitor90388bc7와 기존 PREOPEN 원천의 exact pair를 인계 owner에 추가하며 기존 허용쌍을 보존한다. 후속 배포는 보호80개 중 검토한 H/monitor2쌍만 변경하고 나머지78개·native33개·보호 정책12개의 동일 bytes를 확인한다.

## 11. 실제 CLI 실행 경로 추가 수리

후속17aac0dae는20:17:14에 ordered complete/pass, PID1243842/start4052271로 소비됐다. [독립 런타임 검증](../../tmp/submit-crisis-timeout-20261014/observer-prepare-followup/postrestart-runtime-verification.json)은 위기 기능 부재·정책12개 불변·자연 startup3906행과 source 준비1batch를 확인한다. 하지만 [20:22 무알림 검증](../../tmp/submit-crisis-timeout-20261014/observer-prepare-followup/manual-no-notify-20261014T202217-1d20b590/receipt.json)의 Sentinel은0.518초에 `summary_contract_migration_funnel_owner_changed`로 실패했다. source-only 후속 발행은 완료했으나 partial이며 원 exit1을 보존한다. 이를 full validation으로 집계하지 않는다.

원 파일 d487b404의 SHA와 callback 정의는 맞지만 실제 `python -m src.engine.buy_funnel_sentinel`은 callback 모듈 이름을 `__main__`으로 설정한다. 정상 CLI를 canonical import 이름만으로 거부한 검증 결함을 수리한다. `__main__`이라는 문자열만 허용하지 않고 실제 등록 module·callback globals/함수 identity·canonical spec.name·origin/file·승인 파일 SHA·전이 정의/의존성 검증을 모두 결속한다. 실제 CLI 실행을 재현하는 격리 시험에서 수정 전 실패와 수정 후 수용을 확인하고 다른 모듈·변조된 spec/origin/정의를 거부한다. 원 parser/manifest/checkpoint·append 한도·매매 정책은 유지한다.

추가 코드·시험·문서·배포 결과는 `tmp/submit-crisis-timeout-20261014/cli-summary-followup`에 새 시도로 보존한다. 보호80개/native33개 및 정책12개 전체 bytes는 유지하고 동일 승인으로 재리뷰·표적 검증 뒤 ordered 배포한다. 원 두 배포/수동 실패 영수증을 덮어쓰지 않는다. 장후 실행의 producer_parity 요약과 Sentinel default 요약은 별도 owner/lock이며 기존 장후 작업·일정·정상 종료를 변경하지 않는다.
