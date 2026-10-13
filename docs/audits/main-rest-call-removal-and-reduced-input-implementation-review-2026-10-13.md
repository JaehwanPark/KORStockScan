# REST 호출 제거·판정 입력 간소화 구현 리뷰 — 2026-10-13

## 1. 결과·권한

사용자가 [계획](../proposals/main-rest-excessive-call-removal-and-input-quality-relaxation-plan-2026-10-13.md)의 리뷰·보완, 구현, 반복 코드리뷰·수정을 요청했다. **CR0~CR8의 작업본 코드 구현과 영향 범위 검증을 완료했다.** 원천 설명력·발굴/관측 coverage·긴 이력/현재봉 보충을 낮추면서 불필요한 요청을 제거했다. 실제 주문의 fresh quote·계좌/수량·order/cooldown·Main/manual custody·hard/protect/emergency guard와 원5초를 유지한다.

작업 시작 git status는 clean이었다. 신규 Python 파일은 역할에 맞는 `src/tests/test_rest_call_reduction.py` 하나이며 `src/engine` root에 새 module/호환 wrapper를 만들지 않았다. 기존 utils/market/scalping/scanner/Main owner를 수정했다. 새로운 worker·REST/WS 연결·REG·provider/broker 호출·package 설치·정책 발행·배포/재기동·외부 sync는 실행하지 않았다. `deploy`의 scheduled wrapper 변경은 다음 실제 release 적용 시 효력이 생기는 코드이며, 현재 설치 cron이나 선택 release를 변경하지 않았다.

## 2. 구현과 소비부

| ID | 코드 변경 | 검증/실제 유지 경계 |
| --- | --- | --- |
| CR0 | [Radar tick](../../src/engine/signal_radar.py)의 실제 `TRADE_SIGNAL_DETECTED` receiver0이면 계산/지수 준비를 즉시 종료 | subscriber 검사 이전 source 작업0. scanner의 다른 Radar 메서드/quote 계산은 보존 |
| CR1 | [broker recovery](../../src/engine/sniper_sync.py)의 tracked/수량/manual·퇴역 제외 검사 뒤 첫 적격 후보에서만 kt00008 + second-pass kt00007/ka10076 조회 | 후보0/추적됨/수량0/manual은 추가조회0. 실제 복구 후보2개도 source 묶음은 한 번, 원 attribution/수량 대사 보존 |
| CR2 | [Main async prepare](../../src/engine/sniper_state_handlers.py)의 무조건 capacity prefetch 제거. 판정 뒤 economics observer를 원 `EntryDeadline`의 source-budget context 안에서 실행 | 기존 BLOCK/RECHECK의 reuse-only/U와 ENTER_NOW exact-price 필요조회 유지. original epoch/perf deadline·account generation·2초/5초 age·source-only150ms/attempt1 그대로 |
| CR3 | async/sync Main initial prepare의 투자자 enrich OFF | 기존 snapshot/cache의 선택 수급은 남고 추가 ka10059 조회0. investor는 price/BBO/tape/candle 필수 원천과 구별 |
| CR4 | [zero-base probe](../../src/engine/scalping/zero_base_probe.py)의 native residence 동안 candle/tape/context 선준비 제거. 실제 native 신호 뒤 한 번 준비 | 무신호는 추가 source0, 신호 후 candle1 + 필요 tape. 원5초·lease/readiness 및 source-refresh 후 exact route/clock 재검증. 즉시 평가 호환 경로는 기존 필요조회 유지 |
| CR5 | [discovery panels](../../src/scanners/zero_base_discovery_source.py) gainers `max_pages_limit=1`. [scanner](../../src/scanners/scalping_scanner.py)의 `min(60, interval)` clamp 제거 | API/page bound는 늘리지 않음. KOSPI/KOSDAQ 각1page, 기존60/90초 적용. 순위21~200·발굴 속도 감소를 허용; 별도180초 scheduler는 신설하지 않음 |
| CR6 | [scheduled census wrapper](../../deploy/run_market_opportunity_census_intraday.sh)의 capture argv에 `--skip-executable-bbo` | 기존 rank 관측은 남고 optional04 요청/예약0. 기존 source-gap/U·CF 경제성 결손/95% 근거 부족은 정상값으로 변환하지 않음. 전체 발견/CF 개선으로 주장하지 않음 |
| CR7 | [entry source](../../src/engine/scalping/entry_candle_context.py)에 Main initial/probe 전용 `reduced_completed_v1` opt-in. 최대61 completed·raw same-day partial WS 또는 homogeneous REST completed revision | [WS reader](../../src/trading/market/shared_ws_snapshot.py)는 live identity/hash/route/epoch·원 watermark/clock 보존. 20초 live snapshot 검사 유지. REST 필요 시 forming 제외·같은 분 revision 재사용. raw/adjusted 혼합/미래봉 합성 없음 |
| CR7 소비 | [MTF](../../src/engine/scalping/multi_timeframe_context.py) 선택 외부 index/전일 수준 조회OFF, full-session VWAP/opening range unknown. 잘린 window의 session extrema도 null | neutral/holding source는 별도 opt-in 없으면 기존 계약. reduced 입력은 WS forming overlay를 만들지 않고 부족한 긴 MTF/세션 필드는 missing 상태로 보존 |
| CR8 | [Main account schedule](../../src/engine/kiwoom_sniper_v2.py)의45초 context refresh를 실제 보유/주문·fixed-watch broker admission 대기 때만 실행 |90초 reconciliation·execution callback·계좌 worker single-flight 유지. verified-flat≤60초를 늘리지 않음. 미확인 상태/비정상 qty는 polling 필요로 남김 |

`kt00011` 자체·필수 계좌/미체결/잔량/scale-in/최종 independent REST BBO를 WS로 대체하지 않았다. episode/widget 자동 custody worker를 복원하지 않으며 historical holdings의 operator-managed disposition을 유지한다.

## 3. 반복 리뷰·보완

1. **계획 리뷰:** CR1을 첫 적격 후보의 lazy source 묶음으로 정했다. CR2는 eager 준비를 지운 뒤 ENTER_NOW 필요조회까지 없어지지 않도록 원 source budget을 observer에 전달했다. CR4는 native 대기 중 tape/context fanout까지 함께 제거한다. CR5는 별도 스케줄을 추가하지 않고 기존 page/주기 owner를 재사용한다.
2. **소비부 리뷰:** raw WS metadata는 REST receive clock을 갖지 않는다. probe의 candle 검사에 별도 WS source hash·raw basis·원 generated/available clock·현재 transport epoch 검증을 연결했다. 신규 REST receive timestamp를 만들어 WS를 REST처럼 포장하지 않는다. candle 조회 뒤 WS를 다시 확인해 느린 준비/재접속 뒤 이전 frame을 쓰지 않는다.
3. **추가 수정:** writer가 complete prefix여도 반환한 recent61window가 잘렸으면 full-session claim을 제거한다. full-session derived VWAP/opening range와 extrema를 null/명시 unavailable로 둔다. source selection 중 원 WS transport가 바뀌거나 결손이면 실패한다. partial history가 live snapshot freshness까지 풀지 않게 별도20초 검사를 유지한다.
4. **재리뷰:** reduced metadata만으로 neutral/holding consumer가 자동 opt-in되지 않도록 명시 flag를 entry wrapper에서 전달한다. 완료봉만의 판단에 현재 tick으로 forming 봉을 다시 만드는 경로도 끊었다. WS의 missing minute을 공식 REST no-trade 보장처럼 표시하지 않고 별도 observed/unknown policy로 남긴다. 잘못된/NaN/분수 qty·미확인 상태는 optional polling을 생략하지 않는다.

각 보완 뒤 관련 회귀를 재실행했다. 검토한 코드·소비 계약 범위의 미해결 finding은0이다. 이는 모든 repository 테스트·미래 자연 실패0이나 경제성 완료를 뜻하지 않는다.

## 4. 검증·절감의 증명 범위

- 최초 영향 범위250건, 추가254건, 최종 source/소비/계좌·retirement·read-control 통합 **751 passed /1 deselected /2 warnings**. 중복 실행 수를 고유 합계로 더하지 않는다. Python13파일 compile, `bash -n`과 wrapper argv/실제 census capture 회귀를 통과했다.
- 한 테스트는 퇴역 generic `build_code_improvement_workorder`의 제거된 `MARKET_OPPORTUNITY_CENSUS_DIR` 속성을 요구해 실패했다. 해당 producer와 테스트는 이번 작업에서 변경하지 않았으며 current module은 `Retired compatibility CLI`다. 최초 실패 로그를 보존하고 최종 active 범위에서1개 deselect했다. 이를 위해 퇴역 producer를 복원하지 않았다.
- 같은 completed cutoff의4번 분봉 요청을 memory cache miss/6초 간격으로 재현했다. forming baseline은 원천 fetch4회, completed-only는 shared revision으로 **1회**였다. 다음 분 cutoff에서는 두 경로 모두 새 fetch를 수행했다. 실제 서버 전송·전체75% 절감률이 아닌 **동일 fixture의 source 요청 감소** 증거다.
- 보존된 partial raw WS→entry/probe consumer는 REST0, 원 source hash/epoch/clock 유지, full-session claim false를 확인했다. stale snapshot/transport 변경 거절, 무native 신호 source0/신호 뒤 candle1, 적격 recovery0 source0/후보2개 묶음1, investor/index 선택 fetch0, 원 native deadline/context, quote/account/order guards를 회귀했다.
- CR5/CR6은 발굴/관측 coverage 감소에 따른 절감이다. 과거 판정 완전 일치·95% coverage·실체결/EV 증명을 코드 제거의 추가 gate로 요구하지 않았다. CF 경제성 결손을0이나 신규 주문 근거로 바꾸지도 않았다.

시험 로그/official reference/compile hashes는 `data/report/main_rest_call_removal_implementation/2026-10-13/`의 manifest로 보존한다. 자연 전체 절감률·live Main의 동일 부하 성능·현재 release/PID 적용은 **미수행/미검증**이다. 실행 중 release는 작업본 수정으로 바뀌지 않았다.

## 5. 공식 reference·다음 실제 수용

프로토콜에 영향을 주는 작업 전 공식 HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`를 재확인하고 current checkout의 specs/_data, REST continuation client 및 realtime packet 계약을 읽었다. `kiwoom_docs` 부재·POST JSON/headers/auth·real/demo·단위 미확정 경계를 보존했다. source 목적/page bound/완성봉 소비를 변경했으며 vendor wire/FID·인증/주문/REG 흐름은 바꾸지 않았다. [공식 reference 영수증](../../data/report/main_rest_call_removal_implementation/2026-10-13/official-reference.json)에 SHA/검사 경로/hash·작성 시각을 기록했다.

후속 실제 적용은 정책/source code pin·원 claim/pointer/custody·strict/PREOPEN 원 바이트·현재 consumer를 검증하는 당시 handoff로 처리한다. operator-approved 구현을 deployment/PID receipt로 오인하지 않는다. 기존 `DirectFamilySourceRepairMainMechanisticEntry`가 source 변경을, `DirectFamilyPreopenPolicyHandoff`가 승인된 범위의 실제 적용을 인계한다. 자연 snapshot delta에는 제거된 목적/coverage와 유지한 consumer의 valid/unknown·loop/queue·physical attempts를 함께 보고하고 전송량 하한/계측 결손을 성공으로 계산하지 않는다.

최종 문서 검증은 owning 계획/리뷰의 로컬 링크18개·공백/fence, evidence manifest9파일 hash, print-only parser exit0/24개 작업과 위 current owner 각각1개다. `git diff --check`를 통과했다. 문서 수정에 따른 strict/PREOPEN 영향은 실제 handoff 때 새 최종 바이트로 확인하며 원 sealed/AUTO 이력을 다시 발행하지 않았다. 외부 sync·실제 주문/provider·live report 재생성·자연 성능 측정은 이번 구현 범위에서 실행하지 않았다.

## 6. 후속 배포·재기동 승인과 준비

사용자가 후속으로 **배포 및 재기동을 승인**했다. 실제 incumbent은 `main-timeout-structure-20261013-v4` / commit `a72d0c47753305d23da6a3f4e38f4d14a585f387` / PID `3387032`다. 이 commit에 검토한 CR0~CR8과 native 기동 인계의 정확 source pair만 추가하며, workspace HEAD 전체를 동기화하지 않는다. 이전 구현의 미배포 문구는 그 시점 이력이다.

기동 전 읽기 전용 검증에서 frozen source 중 현 체크리스트 한 파일만 원 봉인과 달랐다. 정책·env·PREOPEN·prepared/controller/summary 원본은 일치한다. 기존 Git 체크리스트가 봉인 SHA와 일치함을 확인하고 최신 편집본과 함께 보존한다. 배포는 release-set/detector lock 안에서 정확한 원본으로 predecessor를 검증하고 정상 종료 뒤 최종 candidate 문서를 발행한다. source mismatch를 무시하거나 임의 receipt를 만들지 않는다.

`REVIEWED_REST_REDUCTION_SOURCES`는 원 PREOPEN commit의 Main/initial-entry 두 파일 SHA에서 이번 검토한 SHA로의 정확한 쌍만 허용한다. 다른 bytes·변조 baseline·dirty source·원 code digest 불일치는 여전히 거절한다. stop/delay 정책 값·active pointer·auxiliary scope 정의/threshold/Provider·원5초·최종 quote/account/order/quantity/custody는 유지한다. active code handoff와 이미 있는 다음날 후보의 동일정책 code refresh, 실제 PID 검증·자연 관측 결과는 `tmp/rest-removal-deployment-20261013/`와 ordered transition에서 따로 기록한다. 약세 WR0~WR5 구현/재연구나 주문은 이번 승인 범위에 포함하지 않는다.
