# REST 절감 구현·성능·잔여 과도 호출 점검 — 2026-10-13

## 1. 결론

**절감 코드는 구현·배포되어 실제 WS 체결 재사용과 낮아진 loop/잠금 지연을 관측했다. 그러나 불필요한 호출 제거와 분봉 WS 전환은 미완료다.** 최신 고정 관측 Main에서 체결 준비452건은 WS/HTTP0을 소비했지만 분봉 논리 요구527건은 모두 REST 유지였다. 판정 전 capacity·선택 투자자 조회, 소비 없는 Radar 지수 준비, 대상 여부를 검사하기 전 계좌 복구 조회, 다중 page 발굴과 외부 관측 BBO가 계속된다.

확인한 오늘 Main 물리 전송 하한12,005회와 외부 census BBO3,609회는 서로 다른 프로세스다. 합계 **15,614회는 확인된 부분군의 하한**이며 전체 계정/token 전송량이나 모두 제거 가능한 호출량이 아니다. 누락된 PID 마지막 tail·census의 discovery/기타 프로세스 전송을0으로 처리하지 않는다. 과거 전체 baseline 분모가 없어 10/8 대비 전체 REST 절감률은 null이다.

사용자는 판정 품질요건의 완화를 허용했다. 완전한 비진입 경제성·전시장 관측 호가·20개 장기 MTF/현재봉·수정주가 이력 동등성 때문에 조회를 계속 유지하는 조건을 축소하는 [호출 제거·입력 간소화 계획](../proposals/main-rest-excessive-call-removal-and-input-quality-relaxation-plan-2026-10-13.md)을 작성했다. 이번 요청은 점검으로 수행했으며 코드/운영 호출 제거를 실행한 결과와 구별한다.

## 2. 실행본·원천·전체 호출 범위

- 고정 HTTP·성능 표본은 Main PID3208863, `main-joint-source-20261013-v2`, commit `afd16c5502da1d012d62c1bbe8b07797f1c53efa`, 17:07:37~18:11:32 KST다. 실제 `/proc/.../cwd`와 selector/PID receipt를 대조했고 REST/WS 관련12파일의 작업본/릴리스 hash가 일치했다. [소스 대조](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/current-release-source-comparison.json).
- 조사 도중 별도 작업이 18:16~18:17에 위 PID를 종료·재기동했다. **18:18:35 새 PID3357134/start13243787, 동일 commit**, 18:19:50 WS producer 및 cwd가 일치했다. 새 PID의 장기 성능으로 이전 PID 값을 승계하지 않는다. 종료로 실패한30초 WS 부하 sample은 완료 증거에서 제외한다. 이 점검은 재기동/selector 변경을 실행하지 않았다.
- 말단18:28 대조에서는 별도 작업의 새 `main-timeout-structure-20261013-v3` / commit `0a26f1b9a8158d858f147c2d7e4c99a37d21b2ae`, PID3367538의 실제 cwd를 확인했다. **이번 호출 발견사항을 소유한14개 파일은 관측 v2와 전부 hash 동일**하여 잔여 호출 코드가 새 실행본에도 남는다. v3의 자연 빈도/장기 성능은 위 v2의1,719회나 percentile로 대체하지 않는다. [말단 실행본 대조](../../data/report/main_rest_ws_followup/2026-10-13/terminal-release-comparison-1828.json), [별도 hash manifest](../../data/report/main_rest_ws_followup/2026-10-13/terminal-manifest-1828.json).
- [현재 정적 목록 TSV](main-rest-ws-callsite-inventory-2026-10-13.tsv): non-test Python650개, AST 오류0, recognizer54 + 계측 wrapper 내 OAuth 수동 보완1 = endpoint55지점/API44종, wrapper 호출159/참조18. 과거 퇴역 전86지점/46종/물리11곳과 혼동하지 않는다. recognizer·literal/callback 대조 목록이며 동적 모든 runtime reachability/프로토콜 적합성 증명은 아니다.
- 생존 키움 물리 전송 계측 경계는6곳: `kiwoom_utils` 인증/공통 transport, `kiwoom_orders` 최초/인증 재시도, offline history backfill2곳. `requests.get`의 Naver marketcap, FDR, AI provider는 키움 HTTP 분모에서 제외한다. 외부 census는 공통 transport를 사용하는 별도 프로세스라 Main 메모리 계수에 포함되지 않는다.
- [정적 JSON](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/current-static-inventory.json), [현재 소스 발견사항](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/current-source-findings.json), [runtime 요약](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/runtime-summary.json), [manifest](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/manifest.json)을 보존했다. 상세 `data/report`는 로컬 evidence이며 배포/Git에 자동 포함되지 않으므로 인계 때 hash와 별도 custody를 확인한다.

현재 AGENTS/Rebase는 episode/widget의 자동 BUY/SELL/CANCEL/retry·수집/연구 모두 영구 퇴역, 역사 잔고 operator-managed, Main 채택/flat 대사 불필요를 명시한다. 원 10/8 계획의 자동 episode 잔여 callback 유지 조건은 현재 제거 기준이 아니다. 원 journal attribution은 보존한다.

## 3. RW0~RW6 구현·실제 소비

| 단계 | 확인한 구현 | 현재 수용 상태 |
| --- | --- | --- |
| RW0 전송 계측 | 물리6경계의 시작/terminal·timeout·API/owner/PID·분당/누적 bounded 계수 구현 | 자연 started=terminal+inflight 대사 확인. 전 프로세스/계정 전체 누계는 미완성 |
| RW1 Radar | 동기 FDR/잘못된 직접 ka20006 fallback을 단일 준비 worker·정상20일 parser로 변경 | tick callback 대기 제거는 구현. consumer 없는 이벤트 때문에 worker 조회 자체가 여전히 반복됨 |
| RW2 체결 준비 | exact item/route/epoch·원 clock·10체결 WS source adapter | PID3208863 prepare logical452 / WS선택452 / 해당 caller HTTP0. WS tick 대체 실제 소비 확인 |
| RW3 분봉 | Main 공통 raw journal/projection·reader, homogeneous REST completed-history revision 연결 | 논리527 / REST유지527. 현재 `adjusted_1` 요구를 WS selector가 원천 읽기 전에 거절; 430봉/forming 추가 부담도 존재. 분봉 WS 절감 미완료 |
| RW4 cache/capacity | 동일 key single-flight, original clock·0w 원 시각/item/epoch 구분, shared REST history 재사용 | 유효 재사용은 존재하지만 판정 전 capacity/investor 준비가 남음. 필요 소비 기준 lazy 조회 미완료. 0w 단위/집계 의미 미확정은 유지하며 변환 완료를 주장하지 않음 |
| RW5 WS/원천 비용 | snapshot 후처리 lock 밖, 공통 raw writer, 퇴역 detector/중복 encoding 제거 | 최신 retained WS hold p99 2.729ms. ACK/type별 전체 wire·부하 상한은 미확정 |
| RW6 배포·자연 검증 | 10/8 v3 및 10/9 공통시장원천 후속 승인·배포 기록, 관측 v2 및 말단 v3 코드/실PID 대조 | 구현/PID 확인과 자연 일부 지연 개선 성립. 동일 부하 전체 호출 절감률·새 PID 장기 성능·주문/수익 개선은 미검증 |

원 구현 근거: [10/8 리뷰](main-rest-ws-latency-implementation-review-2026-10-08.md), [10/9 후속 승인 배포](main-market-source-authorized-deployment-and-next-preopen-readiness-2026-10-09.md). 당시 부분 benchmark나 미수용 조건을 현재 전체 성능 PASS로 전용하지 않는다.

## 4. 실제 지속 호출

아래는 PID3208863의 17:07:37~18:11:32 누적 계수다. **시작1,719 = terminal1,719 + inflight0**, 응답1,718/timeout1. cache/follower/논리 요청을 물리 전송으로 세지 않았다.

| API/owner | 물리 시작 | 현재 원인·제거 방향 |
| --- | ---: | --- |
| ka10027 / zero_base_discovery_panel | 480 | gainers 최대10page/시장·매cycle. 1page/느린 별도 주기로 축소 |
| kt00011 / entry_capacity_prefetch | 294 | 기계판정 전 initial-real 준비. 실제 sizing 수요로 이동 |
| ka10080 / 공통 Main helper | 224 | adjusted_1·430 요청·forming freshness 때문에 REST 유지 |
| kt00005 / balance | 170 | KRX/NXT2원천·45/90초 계좌 snapshot/reconciliation. 필요 consumer별로 재사용/분리 |
| ka10023 / activity panel | 120 | 두 시장 반복 발굴. 선택 주기/동일 cycle 재사용 검토 |
| ka20006 / Radar fallback | 94 | consumer 없는 realtime 이벤트의 지수 준비 후보 |
| ka10075 / 미체결 snapshot | 86 | 계좌 정기 대사. 주문/잔고 safety와 optional context 구분 |
| ka10080 / zero_base_machine_probe | 75 | native 신호 전/후 분봉 준비. 미발생 probe 선조회 제거 |
| kt00007 / 복구 주문이력 | 44 | 복구 후보 검사 전 조회 |
| kt00008 / 복구 결제 설명 | 44 | 복구 후보 검사 전 조회; settlement는 exact fill proof가 아님 |
| ka10076 / 복구 체결이력 | 44 | second-pass 주문 reference 묶음 |
| ka10059 / investor | 32 | initial prepare의 선택 수급 enrich |
| ka10005 / 일주월 조회 | 4 | 선택 MTF/전일 수준 consumer; 낮은 빈도와 실제 사용 확인 후 축소 |
| kt00001 / 예수금 | 3 | 계좌/실제 sizing 필요 소비; 공용 시장 cache로 대체 금지 |
| kt00011 / entry_live_sizing | 3 | 실제 예산 소비. 선조회294와 구별하며 정확 가격/수량 검사 유지 |
| kt00018 / inventory | 2 | 기동/계좌 snapshot 필요 소비 |
| **합계** | **1,719** | 전체가 불필요한 조회는 아님 |

전 정규장/장후 PID2535402의 11:48:45~17:05:24는5,742회였다. discovery1,439, prefetch612, Main분봉525+probe226, Radar348, investor125, 복구3종 각211이 지속됐다. 최신 약1시간 표본에만 생긴 현상이 아니다. 두 PID 총량을 동일 길이/부하의 비교로 사용하지 않는다.

### 4.1 Main 밖 관측 수집

[census 근거](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/census-runtime-summary.json)는 08:00:02~18:15:13,448capture·기존 request meta의 **ka10004 physical3,609**다. captured3,454/invalid·crossed155이며 별도715 non-common exclusion은 전송하지 않은 관측 행이다. 예약/bbo row4,324를 HTTP로 합산하지 않았다. census panel refresh·기타 API 전송은 이3,609에 포함되지 않는다.

장후 KRX448/NXT560 =1,008회다. [기존 wrapper](../../deploy/run_market_opportunity_census_intraday.sh)는 매5분 `all,liquid_common`,16~20시 KRX/NXT를 지정하고 executable BBO가 기본ON이다. 이는 주문용 조회가 아니라 기존 report-only source다. 사용자 요청에 따라 executable/95% 관측 품질을 포기하고 기존 `--skip-executable-bbo` 또는 작은 표본으로 줄일 수 있다. 독립 발굴 분모와 누락 이유는 남긴다.

| 같은 고정 창 | Main actual attempts | 외부 census04 | 알려진 합계 |
| --- | ---: | ---: | ---: |
| PID2535402 /15:00:15~15:15:21 | 242 | 108 | 350 |
| PID2535402 /16:51:15~17:05:24 | 263 | 108 | 371 |
| PID3208863 /17:57:26~18:11:32 | 491 | 108 | 599 |

마지막 창 Main은 prefetch125·Main분봉92·discovery104를 소비했다. 각 창의 census108은 KRX48/NXT60이며 별도 process/capture 근거다. 상기599는 확인된 두 부분군 합이며 전체 토큰 단위 총량은 아니다. 비교 가능한 treatment baseline이 없으므로599→개선율을 계산하지 않는다.

## 5. 성능·WS 부하 판단

| 증거 시점 | loop work p95/p99 | WS lock hold p99 | 의미 |
| --- | --- | --- | --- |
| 10/8 14:28:47 PID206123 | 4.878s/10.853s, warm79 | 24.291ms | 당시 목표 미달의 역사적 영수증 |
| 10/13 15:15 PID2535402 | 1.187s/2.025s | 4.903ms | 정규장 자연 관측, 해당 retained/cumulative 표본 |
| 10/13 18:11 PID3208863 | 0.751s/1.319s, 최근4,096개 | 2.729ms | 장후 자연 관측, total warm4,223·누적5초 초과3 |

**자연 loop/WS 잠금 지연은 과거보다 낮아졌으나 원 계획 단독의 개선율로 귀속할 수 없다.** release·정책·시장/session·native 기회율·host/report 부하와 표본이 다르다. `warm`은 첫 loop 제외이며 완전한 steady-state 보증이 아니다. 표의 percentile은 해당 로그의 retained/cumulative 통계이며 위14분 HTTP 창에 한정해 재계산한 지연값이 아니다.

18:11 preparation service p95/p99는0.822s/1.264s, capacity preparation0.312s/0.615s다. confirmed→claim p95/p99는1.354s/2.347s, claim→machine1.435s/1.978s다. 각 단계는 서로 다른 표본이라 percentile을 더해 전체5초 성공률을 계산하지 않는다. provider response23표본 p95=3.626s, machine→response3.788s이고 submit guard는 미관측이다. 빠른 loop만으로 신호→AI→주문 성능 완료를 주장할 수 없다.

[18:19:50 WS 상태](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/ws-status-summary.json)는 새 PID3357134, local sent9items/cap56, connection available, capture lock1.663ms, 해당 snapshot writer loss/projection errors0다. local sent는 ACK가 아니며 단일 snapshot의 loss0는 전체 무손실 증명이 아니다. 새 PID의 전체 frame/타입별 peak·TCP bytes/s·last-consumer lag/CPU 상한은 미관측이다. 추가 WS 구독이 필요 없는 기존 원천 재사용/불필요 callback 제거를 우선한다.

## 6. 제거 근거·변경 경계

| 핵심 발견 | 직접 producer→consumer 근거 | 다음 조치/종료 시험 |
| --- | --- | --- |
| 소비자 없는 Radar | [producer](../../src/engine/signal_radar.py:95), [Main 생성](../../src/engine/kiwoom_sniper_v2.py:12510), repo src/deploy에 해당 event subscriber 없음; [actual subscriber 검사](../../src/core/event_bus.py:46) 존재 | 실제 receiver0일 때 준비0, receiver있는/다른 scanner method는 보존 |
| 후보 확인 전 계좌3조회 | [복구 함수](../../src/engine/sniper_sync.py:731)는 추가조회→tracked/exclusion/수량 검사 순서, [90/45초 스케줄](../../src/engine/kiwoom_sniper_v2.py:13157) | 적격 복구 후보0이면 추가3HTTP0. owner/census unknown은0으로 위조하지 않음 |
| 판정 전 capacity | [refresh](../../src/engine/sniper_state_handlers.py:61387) 선조회, [비진입 observer](../../src/engine/sniper_state_handlers.py:12433)는 이미 reuse-only | 무조건 prefetch 제거; BLOCK/RECHECK 관측 U 허용, 실제 ENTER_NOW exact-price 필요조회와 guard 유지 |
| 선택 투자자 조회 | [prepare](../../src/engine/sniper_state_handlers.py:61331), [required sources](../../src/engine/scalping/ai_market_snapshot.py:1778)에 investor 없음 | prepare HTTP0·선택 field unknown, optional 결손이 필수 candle/BBO 검사로 확대되지 않음 |
| probe 이중 candle 준비 | [신호 전](../../src/engine/scalping/zero_base_probe.py:681)/[신호 후](../../src/engine/scalping/zero_base_probe.py:818) | 무native신호 candle0·신호후1read, 원 deadline/route/preflight 유지 |
| 발굴의 다중page/주기 | [gainers200](../../src/scanners/zero_base_discovery_source.py:82), [max10page](../../src/utils/kiwoom_utils.py:3090), [90초를60초로 clamp](../../src/scanners/scalping_scanner.py:6949) | 실제1page/수정 주기·축소 rank coverage 기록, 입력률 감소를 semantic 품질 동일로 주장하지 않음 |
| 분봉 WS 의미 gate | [adjusted 요구](../../src/engine/scalping/entry_candle_context.py:385), [WS 거절](../../src/trading/market/shared_ws_snapshot.py:327), [forming 기본](../../src/utils/kiwoom_utils.py:5060) | 판정 raw_same_day/closed-only 계약으로 변경, optional 긴window·forming 누락 허용. raw/adjusted 혼합/미래봉 금지 |

범용 `build_realtime_analysis_context`의6원천 fanout은 현재 handler의 KOSPI_ML/KOSDAQ_ML 분기다. 이를 현재 Main SCALPING의 활성 불필요 호출로 합산하지 않는다. pruned BBO의 최대1,200/day는 예약 bound이지 실제 전송 근거가 아니다. post-sell BBO는 WS/REG 경로이며 REST polling으로 오인하지 않는다.

## 7. 공식 확인·검증·잔여 범위

18:11 current upstream HEAD와18:12:50 checkout은 공식 SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`다. `kiwoom_docs`는 없다. spec의 ka10080/ka10059/kt00011/ka20006 요청·응답 metadata, specs/core/client/ws_client 및 realtime packets/schemas/decoders 경로/hash를 [공식 영수증](../../data/report/main_rest_ws_followup/2026-10-13/read-only-1808-1819/official-reference.json)에 기록했다. [공식 repository](https://github.com/Kiwoom-Securities/Kiwoom-REST-API/tree/953e5dbff123f437ab4d11a78a95191a685eb51f)는 parser/wire 근거이며 입력 설명력·조회 필요성·주문 authority의 근거를 대신하지 않는다. 프로토콜 구현 착수 시 local gate를 다시 적용한다.

점검은 기존 코드/선택 release/실PID·기존 log/receipt/capture의 읽기와 작은 파생 evidence 작성으로 수행했다. trading/provider 호출·새 REST/WS 연결/REG·운영 설정·스케줄·policy·배포/재기동·원 journal 변경은0이다. 다른 세션의 dirty 소스·배포 상태를 보존했다. 전체 프로세스 계측 tail, 동일 부하 전체 개선율, 새 PID 장기 성능, 실제 submit/fill/경제성은 미완료다.

호출 제거 후속은 CR0~CR8의 구체적인 transport0/상한과 optional missing 처리로 검증한다. 문서 완료를 코드 제거 완료로 표시하지 않는다. 문서 링크/TSV/hash/단일 current owner/print-only parser와 `git diff --check` 검증을 수행하며 문서-only이므로 runtime pytest·큰 보고서 재생성은 실행하지 않는다.

최종 재리뷰에서 0w **시각 검증과 미확정 단위**를 구분하고, CR7의 partial/full-session-prefix admission 변경을 reader→selector→feature/preflight까지 명시했다. 말단 v3의14개 관련 파일 hash 동일성도 확인했다. 변경 문서3개의 로컬 링크57개·새 문서 공백/fence, TSV232행(55endpoint/159call/18reference)/API44종과 실제 파일/행 범위·Git 제외 없음, base evidence7파일 및 별도 terminal manifest의 hash를 통과했다. print-only parser는 exit0/24개 항목이며 관련 기존 current owner4개는 각각1개다. `git diff --check`를 통과했고 unrelated dirty source와 AUTO 블록을 보존했다. 문서 리뷰 범위의 미해결 결함은0이며 CR0~CR8 구현·자연 수용은 후속으로 남는다.
