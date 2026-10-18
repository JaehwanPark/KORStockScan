# Main 보유·익절 연구 실행·코드 검토 기록 — 2026-10-18

현재 상태: **실제 v3 신규 산출물 cold1회+완료 보고서 재개3회·분봉 분석·독립 결과 대사와 코드524 PASS, 추가 actual/CF 통합 검증 완료**. 전체 범위 처리와 경제 개선 증명을 구별한다. 별도 보유·재생 수리 세션을 전제하지 않으며 이번 `MainAllScopeTrailingReplay`가 필요한 연구 계약 수리를 소유한다.

## 1. 실행 범위와 고정한 근거

- 연구 원천일 구간은2026-09-29~10-16, 원천일10/16, 대상일10/19, 동일 cutoff `1792284633.131831`이다. 기간 내 완료 census에는9/28 진입의 carry48376 1건이 포함돼 감사 원문으로 보존됐다. 현재 이 행은 source_gap이며 학습·승격에 사용된 표본은 없다. 원천일 구간과 모든 진입시각의 범위를 동일시하지 않는다. clean baseline 이전 자료를 튜닝에 사용하지 않았다.
- 원천일 master **2,605종목 × 8개 route/session = 20,840범위**를 처리했다. 이는 전 종목의 연속 관측 확보나 동시 구독을 뜻하지 않는다. scope 상태는 `operating_unobserved=5`, `registered_nonoperating=20835`이며 원 보고서의 `raw_census_complete=false`를 보존한다. 과거 모든 날짜의 당시 master까지 증명한 것은 아니다.
- 격리 worktree는 `/home/ubuntu/KORStockScan-worktrees/holding-exit-research-20261018`, base는 `7c241ea21619ce3153f1a338f1b846b0313a894f`다. 1차 수리는 `0ab270be080c1154e5a2a6b0f5a51cad65aa796b`, 분봉 상한 후속 수리는 `d07c3ee3f406d9f324331369698558e430f23a71`에 보존했다. CF AI·연구 진입 경계 후속은 `7dc2a934e3a0a45ff6eca7600c35a41ceda83cb2`이며 최종 코드 계약 SHA는 `2df6ba7d0a9ddc2a7f2dcec6f780c49473c0050b7be641d64b0b4062fedd3d12`다.
- [원 실행 manifest](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v1/campaign.json), [동결 입력](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v1/frozen-input.json), [실험 등록](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/experiment-registration.json)을 보존했다. 기존 numeric 이웃18개와 상황분류 가설2개를 결과 확인 전에 등록했다. 원 M1·AI·진입·수량·경로·비용 가정을 고정하고 기존 actual selector의 `candidate - max(parent modeled, actual realized)`를 유지했다.

## 2. 실제 수리와 생산·소비 경계

| 경로 | 확인·수리한 내용 | 남겨 둔 결손·한계 |
| --- | --- | --- |
| 실행계획 → pipeline → CF | 실제 sizing producer receipt를 기존 문자열 JSON 저장·decode·원 native SHA/attempt/bundle/route에 연결했다. 가격/depth 가용시각·epoch 타입·leg/수량·초기 BUY generation을 검증했다. | 과거 미기록 계획·후행 depth를 소급 생성하지 않는다. 조건부 leg와 부분 잔량 재생 미지원은 검열한다. |
| entry/ADD 비용시각 | timezone 포함 ISO와 epoch를 같은 adapter로 정규화하고 원 시각을 보존했다. | naive/future/missing/nonfinite를 정상 비용으로 간주하지 않는다. 누적 체결수량을 최초 BUY 수량으로 대체하지 않는다. |
| 실제 비용 provenance | exact-execution과 whole-position scope의 원 provenance를 구분하고 실제 가용시각을 as-of와 train/holdout에 반영했다. 비용만 바꾼 resume과 처음 계산의 의미를 맞췄다. | 수량 연구 전용 배분 비용을 holding actual로 전용하지 않는다. 비용 확인 전 train 표본은 purge 감사에 원 ID를 남긴다. |
| 연구 진입 경계 | 완료일 파일에 연구 시작 전 진입 carry가 포함될 수 있어 `consumed_dates` 최솟값의 KST00:00과 clean baseline을 공통 경계로 사용한다. assembler·일반/분할 replay·checkpoint에 결속한다. | 원 ID·entry·census·기존 source_gap은 보존한다. 경계 전 actual1+alternative1은 감사/검열이며 원천 복구 뒤에도 튜닝에 자동 편입하지 않는다. 경계 정각은 허용한다. |
| 순수 청산 차이 | 별도 `candidate modeled - parent modeled` 진단을 구현했다. | 기존 실제 실현 하한·선정 기준을 이 진단으로 덮어쓰지 않는다. |
| CF 원 보유 AI | 원 actual과 CF의 진입·수량·원가·BUY 세대·계정 namespace·route·비용·원 요청 문맥이 같은 경우만 연결하도록 수리했다. 원 실제 첫 SELL 뒤의 AI/경로는 재사용하지 않는다. | 실제 보유가 없었던 기회의 과거 보유 AI는 관측 불가능하다. 임의 응답·legacy `holding_ai` 주입·required=false 우회로 양성 표본을 만들지 않는다. 합성 fixture에서 실제 producer→저장→public assembler→public replay를 거쳐 VALID 원 AI PASS2/VETO2 소비와 서로 다른 modeled 결과를 확인했다. 자연 경제 성과로 전용하지 않는다. |
| runtime 원천 부하 | 원 계정 범위는 기존 local journal namespace의 digest다. broker 계좌번호·토큰·분봉 auth scope와 구별한다. 설정은 기존 성공 읽기의 비밀 없는 메모리 provenance를 재사용한다. | 새 설정 읽기·계좌 조회를 hot path에 넣지 않는다. source-only 진단 실패가 매수/보유 결정을 바꾸지 않아야 한다. |
| 분봉 reader | native completed-history public reader를 사용하고 DB+WAL을 하루 한 번 사본으로 읽었다. 과거 prefix·acquisition session·동시각 revision 충돌·cutoff를 검증했다. | 수정주가와 진입 기준가격의 동등성은 미입증이다. 봉 내부 순서·depth·체결·실현손익을 만들지 않는다. |
| 분봉 저장 상한 | writer의128MiB 사전 admission softcap을 reader의 source-invalid 상한으로 오용하던 결함을 고쳤다. DB+WAL 합산512MiB는 별도의 사본 자원 예산으로 사용한다. | 예산 초과와 source 의미 오류를 구분한다. 처음의132건 오제외 결과도 원문으로 보존한다. |

[원 필드 계약18개](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/source-contract-audit.json)는 v1 코드의 역사적 근거로 보존했다. 최종 [원천 계약 사전 v2](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/source-contract-audit-v2.json)는 **22개 계약·102개 코드 참조·23개 코드 파일**의 producer/callsite→문자열 JSON→decode→consumer, 타입·단위·시각·identity·fixture를 검증했다. 원 catalog·원14파일 manifest를 덮어쓰지 않고 최종 코드/리뷰 영수증을 결속했다.

## 3. 원천을 대사한 결과

- [원천 감사](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/findings.md)와 [원14파일 봉인](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/audit_manifest.json)을 보존했다. [공식 원천 능력15종](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/source-capability-matrix.json)은 로컬 보관·공식 복구 후보·실시간 수집 필요·미정의·반사실 관측불가를 구분한다. 공식 upstream remote HEAD는10/18 09:48:44 KST `953e5dbff123f437ab4d11a78a95191a685eb51f`와 일치했다. 새 REST/WS 요청·응답 parser·API 호출은 작성·실행하지 않았다.
- [원 BUY custody 대사](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/historical_buy_custody_reuse.json)는 registry1,649 event에서 기존 exact BUY 증명 **12/12건(완료9·보유3)**을 재현했다. 이는 수동 이관 없는 전체 보유 구간·원 청산 owner·정책 증명이 아니므로 자동관리 boolean을 true로 바꾸지 않았다.
- [보유 AI 기록](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/source-audit/holding_votes_window_summary.json)은 **5,465행 모두 INSUFFICIENT, provider_called=true 0건**이다. AI HOLD·유예 성공이나 경제 비교 표본이 아니다.
- [미청산3건 census](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/open-holding-census.json)는 원천일 당시196170/1주,034020/1주,005930/2주를 우측 검열로 보존한다. 마지막 것은 BUY2leg다. 원 open fact의 profit_rate=0/sell_price=0은 placeholder이며 수익0이 아니다. 현재 계좌 조회 결과로 표현하지 않는다.
- 비용 원천의 기존8건 연구 배분은 `initial_quantity_research_only`다. 별도 holding consumer 계약 없이 실제 보유 손익으로 바꾸지 않는다. 원천이 있다는 사실과 현재 연구 소비 허용 범위를 나눈다.
- ka10084 당시 BBO·kt00009 날짜별 체결은 공식 복구 후보지만 이번 계좌 요청은 실행하지 않았다. bounded local inspection에서 못 찾은 것을 API 불가·전체 로컬 부재로 확대하지 않는다. ka10084의 당일/전일 후보가 전체9/29~10/16 자료를 보장하지도 않는다. compact top-book만으로10단계 depth를 복원하지 않으며 과거 미저장 내부 AI/시각/계획과 가상 주문의 실제 fill은 broker에서 복구할 수 없다.

## 4. 전체 재생과 초기정책

최종 v3 [재생 보고서](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/replay/research_2026-10-16.json)와 [4회 완료 영수증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/terminal.json)을 확인했다. v1 보고서·독립 cold 종결은 원 시도 이력으로 보존했다. 아래 범위·모집단·경제 적격·초기정책은 같은 입력의 v1/v3에서 유지됐다.

| 분모 | 결과 | 해석 |
| --- | --- | --- |
| 범위 census | 20,840 | 2,605종목·8route/session 등록/처리 범위 |
| 실제 완료 | 13 | 원 projection의 automatic_management_allowed=false를 유지. 모두 현재 수동 보유라고 단정하지 않음 |
| 같은 실제 진입의 다른 청산 | 13 | 실제13건과 별도 거래13건으로 합산하지 않음 |
| ENTER_NOW+PASS 기회 CF | 482 | 실제 체결·독립 거래 수가 아님 |
| 경제 공통 적격 | 모든 cohort 0 | 원 custody/AI/계획/연속 경로·비용의 필요한 증명이 부족. 손익0·실패한 전략이라는 뜻이 아님 |
| 초기정책 | 3시장 × 4기존 상황 = 12 parent_carry cell | 전20,840범위에 공통 적용 가능한 연구 산출물. 20,840개 개별 종목 정책이 아님 |

[10/19 초기정책](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/replay/initial_policy_2026-10-19.json)은 연구 부모의 시작0.4%·weak0.4%·strong0.8%, classifier=null을 계승했다. policy SHA는 `421f7bb9e59080452d7221c8032f95d101cccb0a6ef3e8b2e40806fb526210d7`이다. **장후 원천 재생성 경로로 부모 동등 초기정책을 생성할 수 있음을 확인했다. 신규 개선값의 경제 우위를 입증한 것은 아니다.** 초기정책 생성에 별도 경제 승인 허들을 붙이지 않았고 운영 발행·소비로 확대하지 않았다.

기존4상황은 HIGH_VARIABILITY/TREND_CONTINUATION/REBOUND_RANGE/BASE다. E1/E2 numeric 후보와 기존 상황 가설을 등록했으나 자연 경제 적격 표본은0이다. E4 강약 전이·새 E5 조기청산·E7 조합을 이번에 새로 구현·선정한 것으로 표현하지 않는다. E5는 아래 가격 경로 진단, E6는 원 AI 입력의 재사용 가능성 확인 수준이다.

## 5. 분봉 연구와 주성엔지니어링 해석

[최종 분봉 진단](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/minute-diagnostics.json)과 원 [분석](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/minute-analysis.json)은 중복 alternative13건을 제외한 **495행=실제13+CF482**를 대사한다. 독립 리뷰에서6개 입력 SHA,495개 원 reference,25개 집계군×6horizon의20,250개 수치/quantile를 재계산해 일치시켰다.

- 일자별 분봉 revision 연결 **460건=실제10+CF450** 중 진입 이후 완료봉이 하나라도 있는 것은 **411건=실제10+CF401**이다. CF49건은 연결된 분봉에 모든 요청 horizon의 후행 완료봉이 없다. 이를0수익·실패 거래로 바꾸지 않는다.
- 원천 결손35건은 실제3건과 CF32건(auth scope 모호25·미보관7)이다. 실제48376/49013은 원 자료의 매수 참조가격은 있으나 item/route가 없어 `native_entry_reference_or_exact_item_missing`이고,49328은 원 item이 있으나 정확 item 또는 cutoff 이하 revision 연결이 미확인인 `minute_history_exact_item_or_known_revision_missing`이다.48376은 새 연구기간 검열로 v3 진단 reference_price/role이 null이 됐다(원 v1은19,010원/verified_buy_leg_price_path_only). 원 qty·basis·entry·가격 근거는 보존됐으며 전후 horizons=[]이라 관측봉·상하한 변화는 없다. 이를 원 가격 자체의 부재로 표현하지 않는다. 첫/끝 partial minute을 빼므로 진입부터 요청 끝까지 전체 horizon이 관측됐다고 증명한 행은0이다. 완료봉으로만 이루어진 부분창과 전체 horizon을 구별한다.
- CF는6종목이며 주성036930이 **260/482**다. 주성의 실제3+CF260=263행은 겹친 경로를 포함한다. 독립 거래260건의 승률로 계산하지 않는다. 실제3건의 자동관리 증명은 false이며 수동 이관 시각·현재 수탁·자동청산 성공을 이 분석에서 입증하지 않는다.
- 60분 관측봉 안에서 +0.4 목표와 -3 비교선 양쪽 가격에 닿은 경우가 실제2·CF17건이다. 도달 순서가 미확인이므로 목표 선행·손절 오판으로 결론 내리지 않는다. 가격 상하한은 고정0.23% 비용모델을 둔 가격 참조 진단이며 실현손익·체결률·EV·승률이 아니다.

후속 연구는 **시작 전 즉시 악화/지연 회복/상승 지속**, **시작 후 이익 보존**, **신호 이후 체결 손실**을 분리한다. 시장·venue/session은 별도 조건으로 유지하고 당시 생산된 입력만 사용한다. 먼저 event 순서·원 기준가격·수탁/원가/수량을 닫고 그 후 시작률·weak/strong을 비교한다. 시간순 holdout과 종목·날짜·경로 중첩 cluster를 분리하며 같은 자료에서 반복 선택한 결과를 새 검증으로 부르지 않는다. 이후 후보는 결과를 보기 전에 별도 등록한다. 하드스톱·수동 veto·브로커 안전선을 완화하는 결론은 없다.

## 6. 성능 실측과 시도 보존

- 원 v1 fresh replay는 assembly625.763초·preflight113.507초·replay256.184초, 합계 **995.454초**에 완료했다. peak RSS175,884KiB이며64MiB는 managed Claim 예산이다. 전체 RSS가64MiB라고 표현하지 않는다.
- 원 driver는 cold1+warm3 중 cold1 완료 뒤 반복 검증의 중복 해시 비용을 줄이기 위해 **연구 PID만 SIGINT**로 종료했다. [중단 영수증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/interruption-receipt.json)·로그·원 산출물을 보존했다. 원 attempts/reviewed-v1/terminal.json을 만들거나4회 완료로 소급하지 않았다.
- 별도 [기존 완료 보고서 digest 재사용 benchmark](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/performance/digest-reuse-v2/terminal.json)는 digest cold55.892초, warm5.442/5.416/5.462초(중앙5.442초)에 같은 semantic 결과를 검증했다. warm마다 대형 full digest read0,약196.9MB thread read와 약5.25MB private scratch write는 남았다. invocation 메모리 cache이며 영구 digest store가 아니다. 이것을 fresh replay995초 대비 동일 작업의 speedup으로 계산하지 않는다.
- [실제 v2 preflight 실패](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/reviewed-v2-preflight-failure.json): native manifest/report의 ASCII escaping 봉인과 private 실행기 봉인을 혼동해 정상 한국어 자료를 거부했다. 원 native SHA/생산자 봉인은 유효함을 확인했다. OUT 생성·replay 시작 전 종료됐고 원 script/log를 보존했다. production 코드·정책·원천 손상이나 변경으로 처리하지 않는다. 새 v3 실행기에서 두 owner의 encoder를 명시적으로 구분한다.
- 최종 [v3 실행](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/terminal.json)은 같은 source/cutoff/window/inventory/IDs/grid에서 **cold1회+warm3회 완료**다. 아래 cold는 신규 산출물 생성이며 OS page cache cold를 주장하지 않는다. warm은 완료 보고서의 기존 semantic 검증·발견·resume 경로다.

| v3 단계 | assembly | preflight | replay | 세 단계 합계 |
| --- | ---: | ---: | ---: | ---: |
| 신규 산출물 cold | 315.189초 | 0.343초 | 20.922초 | **336.454초** |
| warm1 | 2.656초 | 0.336초 | 2.468초 | 5.460초 |
| warm2 | 2.688초 | 0.372초 | 2.444초 | 5.503초 |
| warm3 | 2.700초 | 0.337초 | 2.494초 | 5.530초 |

전체 invocation은 **362.301초**, warm 중앙값5.503초, 진단6.775초·native verification2.181초는 별도다. 네 번의 semantic 결과 SHA는 `1b8aca93fd75224e7b8c0e78fcacf640696cfefdc0a1a681068cdbd38d139f78`로 같다. cold는32 partition/508 feature와 경계 전2model row를 처리했고 warm은32 checkpoint/완료 보고서를 재사용했다. warm마다 대형 full digest read0이며 thread read199,968,721B·private scratch write5,246,976B는 남는다. digest는 invocation 메모리에서 해제됐고 영구 digest store를 쓰지 않았다. warm도 source inventory/generation과 보고서 semantic 재검증을 유지하며 raw path decode/재생은 완료 checkpoint로 재사용한다.

v1 cold995.454초와 v3 cold336.454초는 같은 source/분모/후보 축의 서로 다른 코드·실행 조합에서 관측한 값이다. 단일 cold 관측으로 운영 Main 지연 비악화나 인과적 speedup을 일반화하지 않는다. 특히 cold와 completed-report warm을 같은 작업의 가속비로 계산하지 않는다. v3 누적 process peak RSS는 **193,100KiB(약188.6MiB)**이고64MiB는 별도 managed Claim 예산이며 종료 used0이다.

## 7. 최종 재검증·권한·잔여 owner

[최종 코드 검토 영수증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/code-review-closure-v3.json)은 implementation→self review→보완→독립 재리뷰→표적 검증을 결속한다. 최종 **13개 시험 파일524 PASS/75.87초**, 정확23개 변경 Python 파일 compile·최신8개 production module Ruff(E9/F821/F822)·세 task commit 전체 diff check를 통과했다. 격리 commit 후 clean과 동결 SHA 불변을 확인했다. 중간 확장 회귀255 PASS/4 FAIL는 두 경로 비교 envelope·두 합성 actual 비용시각 fixture를 보완하고18 PASS 뒤 최종524 PASS로 닫았으며 원 실패 로그도 보존했다. v1의485 PASS/분봉26 PASS와 이 수를 중복 합산하지 않는다. 운영 Main 전체 hot path 지연·자연 source 생성·경제 성과를 이 격리 검증으로 입증하지 않는다. 최종 v3가4회 동일 semantic 결과, source/window/ID/grid 보존, 원 시도/선택본/정책/env hash 불변과 digest cache 해제를 확인했다.

[HX09 후속 검증](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/hx09-actual-e2e-validation.json)은 기존 공식 비용 생산자→완료 projection→archive→assembler→공개 연구 재생의 actual·대체청산·CF 양성 경로를 추가했다. 가짜 공식 transport만 사용해 비용1원·실현손익1원을 생산하고 actual/CF가 각각 원 AI PASS2건을 실제 소비함을 확인했다. actual 실현손익과 modeled 결과, CF의 actual_pnl=null을 구별한다. 시험 모듈122 PASS/16.59초와 독립 신규시험1 PASS/4.52초·지적0, compile/diff check를 통과했다. 기존524개와121개가 겹치므로 합산하지 않는다. 시험만 바꾼 후속 commit은 `1bf35e6c258cdcda373c813432b52725898f22ab`이며 [후속 코드 종결](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/code-review-closure-v4.json)에 결속했다. production 코드 SHA는 동일해 v3 실행 commit과 원 결과를 유지했다. 합성 양성은 실제 v3의 경제 적격0건을 대체하지 않는다.

[독립 실제 결과 검토](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/v3-output-review.json)는 봉인142개·bounded tree74개·파일 세대450개를 대사했다.20,840범위·508연구 ID·초기정책과 경제 적격/train/holdout0·114개 EV/null 셀을 확인했다. 분봉495개 ID의3,220 horizon record·45,080개 horizon 필드는 동일하며48376의 reference_price/role 검열2필드만 별도 설명했다. holding ref의 격리 경로·그 경로에 따른 hash 변경은 비경로 값 변경과 구별했다. 미해결 경제·권한 지적은0이다.

더 넓은 pre-AI suite의12실패 중 대표1건은 동일 base에서 `operating_full_policy_incomplete: ENTRY unrecorded_file_read reversal_cumulative_data.json`으로 재현했다. 12건 모두를 개별로 기존 결함이라고 입증한 것은 아니다. guard를 완화하지 않았으며 이 결과와 이번 표적 회귀를 구별한다.

운영 선택본은 `quantity-broker-cost-monitor-20261018-900234d79` / `900234d791b0bf31797cd4e823d0ae40296f790b`다. 이번 연구의 source commit과 운영 소비를 혼동하지 않는다. 활성/준비 정책·selector·custody env를 보호하고 운영 정책 발행·Main 기동/재시작·계좌/API 조회·신규 구독·AI provider 호출·주문은 실행하지 않는다. [v3 audit guard](/home/ubuntu/KORStockScan/tmp/holding-exit-research-20261018/attempts/reviewed-v3/guard-evidence.json)는 outbound/DNS·child process·거부된 write 시도0을 기록했다. urllib3의 로컬 ::1:0 IPv6 capability probe1회와 기존 worktree logger4개 쓰기 이벤트, research admission lock은 별도 관측했다. CPython audit 범위이며 OS sandbox라고 부르지 않는다. 격리 config_dev.json 부재의 기본 URL 경고도 원 로그에 보존했고 설정을 위조하거나 provider/API를 호출하지 않았다.

잔여 owner는 현재 checklist의 `MainAllScopeTrailingReplay`다. 원천일/계정/route와 원 계획·AI·연속 경로를 입증한 범위의 경제 비교, 연구 배분 비용의 별도 holding consumer 계약, 미지원 ADD/부분잔량·실제 SELL 뒤 경로 및 후속 실험을 유지한다. 복구 불가능한 과거 내부 원천·가상 실제 fill을 자연 생산 대기 조건으로 삼지 않는다. 실제 PREOPEN/PID 적용은 기존 `DirectFamilyPreopenPolicyHandoff`의 별도 수용이다. 다른 수리 세션의 완료를 기다리는 blocker는 없다.
