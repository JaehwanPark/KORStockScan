# 2026-09-18 저가주 전체 연구 재실행 — 9/17 결과 successor

- Owner: `LowPriceExpandedResearchRepair0918`. 사용자 추가 승인: 전체 연구 재실행, 유효한 비교·공동 EV 도출 및 전일 장후 결과 갱신. 기존 동결 정책/원본 보고서/실행 중 서비스/정지cron/quantity·비용·grid·sample·provider·custody·안전 guard를 보존한다.
- 거래 서비스 source release: `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`, `/home/ubuntu/KORStockScan-runtime-releases/low-price-research-repaired-20260918`. 거래일9/17, clean prefix6/05 이후73거래일/latest16 holdout. source successor root: `data/report/postclose_research_successor_20260917_20260918/`.
- 전체 저가주 경제 checkpoint는새 scope에서0개로 시작한다. native source 계약 검증 후197개 원천 cache를 사용하며 과거 경제 결과 전체를 재사용하지 않는다. 기존789개 cache-disabled hint만 native 검증 하에 재사용하여 이미 비효율로 판정된 optional cache probe의 불필요한 반복을 피한다. 정책·분석 깊이 변경이 아니다.
- 선행 widget 전체199종목 producer는5종목 계산 뒤 외부응답 `ka10080_response_not_json`으로1차 중단했다. 원천/경제 체크포인트 보존 후1회 복구 실행 중이다. 완료 종목의 source/code/cost/applied incumbent fingerprint가 검증된 경우에만 native 경제 checkpoint를 재사용한다.
- 공동 평가 직접 소비자의 초기 study intake/dependency hash/current receipt 검증에32MiB 제한이 남은 결함을 생산자의 기존128MiB stable no-follow reader로 통일했다. 다른 JSON dependency는기존32MiB를 유지한다. large full-study 소비와order-authority rejection회귀38PASS; nativeclosedloop 추가검증의 고정9/17 fixture가실제9/18 clock을사용하던 불일치를 fixture clock 고정으로 수리했고44PASS이다. production 날짜/자본 source guard는완화하지 않는다.
- 현재9/17 allocator/native_capacity/capacity_source 원천은부재이다. `capacity_2026-09-17.json`은WS 구독 범위 receipt이며현금/보유/예약자본이 아니다. native source acquisition CLI는현재완료일20:05 이후만 허용하므로9/18 잔고를9/17로 재라벨링하지 않는다. 보존된 동등 과거증거가없으면 feasibility/공동 EV의미확정은수치로 대체하지 않는다.
- 실행/회귀/원천scope receipt: `tmp/low-price-full-research-20260918/`. 이 문서는source-only 결과 갱신 및 미종결 기록이며전일 전체postclose DONE 또는경제성 PASS가아니다. 최종full study/source generation/비교/공동 EV 결과는후속 섹션에기록한다.

## 최신 정정 — 서로 다른 정책 비교 수리

[2026-09-18 distinct 경제성 review](2026-09-18-low-price-distinct-economic-review.md)가 아래 최초 집계의 성숙3건 판정을 정정한다. 해당3건은 baseline과 candidate 매개변수가 같은 자기 비교였으며 독립 개선 검증이 아니다. 기존 캐시/동일비용/native grid로 기존로직64개만156.6초 재평가한 최신 결과는 distinct 성숙2건·EV/일별 순익 동시개선0·미청산/terminal미확정55건이다. 팬오션 미청산 baseline의 부분 실현0 대비 상승은 경제적 우위로 확정하지 않는다. 원 보고서·동결policy·ledger는 보존했고 신규API/전체chain 재실행은 없었다. 아래 수치는 원 실행 이력이며 최신 비교 판단은 새 review를 따른다. 공동경제 source 결손·joint EV/net null과 전체chain 미완료 경계는 유지한다.

## 최신 판정 — 9/17 결과 갱신

저가주 전체 1,020프로필의 native 경제 재계산과 기존 로직 64개 비교는 완료했다. 유효 원천197/원천격리7, 경제 checkpoint hit0/miss789이다. 같은 관측창·비용의 수치 비교13개 중 양측 완료 결과·holdout 3signal/4leg·미해결 custody 부재를 충족한 성숙 모델 비교는3개이고, EV 및 일별 순익 개선은0개다. 이는 유효 비교의 incumbent 유지 결과이며 실제 체결 수익이 아니다.

[기계 판정 JSON](../../data/report/postclose_research_successor_20260917_20260918/low_price_full_research_result_review_2026-09-17.json), [기존 로직 비교](../../data/report/postclose_research_successor_20260917_20260918/low_price_existing_logic_full_comparison_2026-09-17.json). 선행 widget은 전체199 중 경제계산104/식별 원천격리52/미처리43으로 보존했다. 이번 추가10종목은3경제완료/2원천격리/5조회대기,140.31초였다. 전체 widget study는 아직 발행하지 않았다. native 공동 refresh의 실제 결과는 `waiting / required_completed_study_missing / widget`이다. 9/17 현금·보유·예약자본 및 same-stage timing 원천도 미확보이며 공동 EV·순익은 null이다. 현재 잔고나 모델 EV 합산으로 과거 공동 수익을 만들지 않는다. 전일 전체 장후 chain DONE이 아니다.

## 이번 구조 보완과 운영 방식

- 기존 생산자 안에서 v2 진행 receipt를 종목 처리마다 저장한다. 같은 완료일·universe/origin·code/parser·비용·적용 incumbent·동결 후보·날짜별 외부 입력·EOD freeze가 동일할 때 완료 checkpoint와 격리를 이어받고, 다음 invocation은 대기 목록의 최대10종목만 처리한다. 재대기 항목은 뒤로 보내 미조회 항목을 먼저 처리한다. 완료 입력 snapshot의 파일 generation 변경·checkpoint 변조·입력 계약 변경은 재사용 실패로 명시하고 전체를 자동 재계산하지 않는다.
- 다음 날 advisory 파일이 전일 fingerprint를 바꾸는 날짜 연결 결손을 보완했다. 실제 전일 입력 변화는 여전히 무효화 사유이다. 조회 간격은 기존 기본0.2초이며 임시1초/5초 추가 재시도는 제거했다. 공유 read 전체5건/초·연구4건/초, native 요청/parser/continuation/retry·quantity·비용·grid·holdout·sample/promotion floor는 보존했다. 추가 scheduler/cron/service·생산 모듈·성능 guard·분석 grid 축소 없음.
- 모든 symbol의 처리가 끝나도 정식 report write 전에는 `building`으로 남긴다. 공동 소비자와 새 widget policy 생성은 최신 receipt의 완료 및 study 입력 지문 일치를 확인한다. 이전 같은 날짜 보고서가 새 실행의 대기/중단을 가리는 결함을 닫았다. 기존 동결 정책 reader/실행 중 거래 서비스의 incumbent 사용은 보존한다.
- 기존 machine final-refresh wrapper에서 native 현금/보유 수집을 긴 연구 앞에 배치했다. 직접 acquisition에서도 현재 완료일20:05 이후인지 계좌/token helper 호출 전에 확인한다. 다음 완료일에 적시 생산을 검증하는 수리이며9/17 결손을 복원한 것이 아니다.

| 상태 | 현재 판단 | 다음 closure |
| --- | --- | --- |
| 성숙 모델 비교3개 | EV/일별 순익 개선0; 유효 유지 결과 | 새 유효 관측창에서 같은 비용·완료 기준 비교 |
| 팬오션 점심·제주반도체 오전 수치 상승 | challenger 표본 부족; 승격 근거 아님 | 자연 유효 signal/완료leg 및 baseline 비교 확보 |
| prospective580·calibration 부족135·holdout/full 부족56 | 미래 유효 유입이 있어야 성숙; ETA null | 선언 cohort/window와 실제 유입·완료 분모 검증 |
| 고정일 source/session 미입증231프로필 | 당시 원천·session 결손; 시간만으로 복원되지 않음 | 동등 보존 원천 입증 또는 명시 격리 유지 |
| widget 미처리43 | 공유 read 대기와 아직 추가 실행하지 않은 대상; EV0 아님 | 다음 턴은 해당 queue만 최대10개, 전체199 terminal 후 공동 재섭취 |
| 9/17 공동 자본·same-stage 원천 부재 | 구조적 생산/수집 결손; 공동 수치 미산출 | 보존 원천 확인 또는 다음 완료일의 native 수집·allocator·공동 gate 검증 |

## 리뷰·검증 및 배포 범위

producer→진행 receipt/checkpoint→정식 writer→공동 refresh/새 policy 소비와 native-capacity 수집 순서를 review/fix/re-review했다. 마지막 보완은 report write 전 완료 marker 방지, 새 generation과 기존 보고서의 지문 결속, 원천 snapshot 변경 시 완료 checkpoint 재사용 금지이다. 변경된 경로의 최종 검증은 `tmp/low-price-full-research-20260918/closure-resume-final-validation.txt`, 기존 69PASS와 이번95/103/109PASS는 각 당시 diff의 검증이다.

원격 main 병합 전 영향5suite 실행은288PASS/3FAIL이었다. FAIL3개는 postclose wrapper와 이전 checkpoint/scout 경로를 기대하는 테스트의 불일치였다. 현행 다른 세션의 퇴역 변경·테스트 수정을 병합한 뒤 해당3개를 재검증해3PASS이며, 병합 후 영향wrapper19PASS·최종관련112PASS·최종재개21PASS이다. 당시 실패명/assert와 병합 후3PASS는 `closure-affected-suites-final.txt`, `closure-inherited-failures-after-merge.txt`에 보존한다. 퇴역 경로를 복원하지 않았다. 영향 경로 최신 targeted 검증·compile·bash-n·diff·문서 parser 결과 및 최종 commit/push/배포는 `tmp/low-price-full-research-20260918/closure-validation.json`, `closure-deployment.json`을 따른다. 병합 후 전체5suite를 반복하지 않았으며, 이전288PASS와해소된3개만으로 새전체suite실행PASS를합성하지 않는다.

새 managed release는 현행 원격 main의 PYRAMID/scout/drought 폐기 등을 합쳐 배포한다. 실행 중 다른 final-refresh worker의 immutable root/PID를 교체하거나 재시작하지 않는다. 저가주 동결9/18 policy/manifest 및 원본9/17 보고서 SHA는 보존한다. 최신 selector/다음 예약 실행 source와 실제 진행 중 PID 소비를 별도 기록한다. 연구 코드 보완·배포와 자연 매매 효과·경제성은 별개이고 `LowPriceExpandedResearchRepair0918`의 자연/공동 acceptance는 OPEN이다.

## 실제 커밋·푸시·배포

- 구현 `3b4a6d12d`, 현행 main 병합 source `2a1388c6929e3c4cd037d507140939fb4c0bb513`. 원격 main 및 `fix/low-price-postclose-closure-20260918`에 atomic fast-forward push 완료. 동시 작업의 PYRAMID/scout/drought 폐기 source·문서·테스트를 보존한다.
- 11:40:47 KST managed root `/home/ubuntu/KORStockScan-runtime-releases/low-price-postclose-source-resume-20260918`를 선택했다. 기존 삼성/widget evaluation 및 machine final-refresh의 다음 invocation source pin을 같은 root로 배포했고 daemon reload 후 WorkingDirectory/ExecStart를 검증했다. 새 timer/cron/service 생성·설치 스케줄 활성화·Main/거래 서비스 restart는 없다. 배포 시 해당 두 장후 unit MainPID0; 앞서 진행 중이던 외부worker를 중단하지 않았다. next source 배포와 actual worker/PID consumption은 별개이고 자연 수집/EV acceptance는 OPEN이다.
- 원본9/17 보고서와 동결9/18 policy/manifest의3개 SHA 불변을 검증했다. source parser contract는기존 `6deba150c7c0336881a3b168988cfaf9cdb97572b5cc361e4fb9864c15e3e1b2`를보존한다. official upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f` 현재일치·관련5 API metadata 및기존spec/error/Postman 확인 receipt는 `closure-official-reference-review.json`이다. 요청/parser/continuation/auth/account/order helper 변경0.
- 현재 실행/경제 결과는 위 최신판정과기계판정 JSON을따른다. 남은43종목은기존 native code/inputs와terminal receipt를보존한queue-only 추가실행대상이다. 새producer code변경만을이유로이번완료104종목의경제계산을다시돌리지않는다. 향후정기는새v2 receipt의동일입력·snapshot·checksum검증으로재개한다. 추가source/공동원천미확보를완료·EV0으로처리하지않는다.

## 선행 producer 결함 보완

- 2차 native widget 실행은14번째001550의 `daily_source_coverage_fail`에서 전체 중단했다. 날짜별 native 격리 후에도 family floor에미달한 식별 가능한 symbol의문제가나머지198종목/공동 입력전체를중단시키는 orchestration 결함이다.
- 기존 main에해당symbol의daily coverage/snapshot coverage/source quality 실패만catch하여quarantine ledger와원source SHA/실제failed date·bar count/비율을보존하고다음symbol로진행하게보완했다. 전체199종목denominator를유지하고failed row는EV/승격/공동 선택에포함하지않는다. 글로벌provider 오류는여전히raise하며all invalid는valid empty로쓰지않는다. 기존 날짜격리/floor·원천read/parser·API retry/budget/quantity/경제kernel·promotion guard 변경0.
- 관련suite43PASS/compile/diff PASS, 코드producer→population handoff→widget policy/closedloop 소비 재리뷰 finding0. 최초 closedloop82PASS와별개 검증이다. 변경된 producer 계약에대한 native cache validation을유지하고출력원본을덮어쓰지않는다. source-only 연구 worktree에서리뷰된새commit으로worker를다시기동한다. 현재selected cf8d573a6의실행중trading source는변경하지않는다.

## 실행 중 복구 및 유효성 경계

- 저가주 CLI 원천 preflight는 기존 197개 원천을 native schema/hash/scope로 검증하고, 누락 7종목을 실제 재조회했다. 관측 거래일수는 042040=58, 060230=62, 285800=58, 348080=59, 417030=19, 446840=58, 487400=25이며 기대값은73이다. 상장일/거래정지 등 원인은 이 값만으로 확정하지 않는다. 실패 metadata와 원천 SHA/날짜 범위는 `episode-source-preflight-blocked.json` 및 `episode-native-recompute-inputs.json`에 보존한다.
- 첫 저가주 CLI 실행은 준비한 캐시 디렉터리의 심볼릭 링크를 native 동결 가드가 거부해 `source_quality_blocked`를 기록했다. 원천 변경이 확인된 것이 아니라 실행 준비 오류였다. exit0도 유효한 경제 재실행이 아니다. 가드를 보존하고 실제 기존 원천 폴더를 native `_SequentialSources`로 읽어 `build_report`의 전체204종목·1,020프로필 경제 계산을 새 checkpoint scope에서 실행했다. preflight에서 이미 확인한 7건을 재사용해 중복 API 조회는 하지 않는다. 전체 grid/73거래일/16 holdout/비용/표본·승격 조건은 유지한다.
- widget 보완 후 실행은28번째까지 처리한 뒤29번째004710에서 공유 read admission의 `shared_read_rate_wait_budget_exhausted`로 중단했다. 재개 실행도7번째101730에서 같은 admission 대기로 종료했다. 이는 종목 source 실패나 no-edge가 아니며 해당 종목을 quarantine/EV0 처리하지 않는다. API quota·bounded wait·retry 계약을 늘리지 않고, 보존된 원천/경제/날짜별 cache를 native 검증해 후속 재개한다.
- 최종 비교는 `selected`의 baseline carry를 challenger로 오인하지 않고 `calibration_winner.holdout`을 사용한다. 숫자 존재와 유효한 성숙 비교를 분리한다. 같은 원천 유효 날짜·native 비용 계약, 양측 COMPLETED 결과 및 holdout 표본, 미해결 custody 부재를 확인하며 낮은 표본/미청산 결과를 0이나 성숙 EV로 대체하지 않는다. 이 추가 판정은 감사 결과의 분류이며 production 승격 가드를 변경하지 않는다.
- 과거 자본 source의 생산자는 `research_native_capacity_source`이며 소비자는 `research_allocation_snapshot` → `research_closed_loop.combined_joint_gate`이다. 실행 wrapper는 긴 선행 연구 뒤 native capacity를 수집하므로 자정 초과 시 원래 거래일의 현재시점 제한을 만족하지 못한다. 9/17 현금·보유·미체결 원천 부재는 단순 표본 대기와 다르며, 보존 원천 복구 또는 다음 완료일의 적시 생산·보존 검증이 필요하다. 현재 잔고로 과거 source를 만들지 않는다.

## 예상 read admission 대기의 연구 진행 보완

- 연구 소비 단계에서 확인한 추가 구조 결함: 정상적인 공유 읽기 용량 대기를 글로벌 source 오류와 동일하게 처리하여 전체199종목을 종료했다. 반복 실행은 첫 대기 종목 이전까지의 source/economics를 다시 확인하므로 불필요한 재작업이 발생했다.
- 기존 widget main에서 두 정상적인 admission 대기(`shared_read_rate_wait_budget_exhausted`, `shared_read_rate_server_cooldown`)만 별도 `source_waiting`으로 기록하고 다른 종목의 source 검증/경제 계산/체크포인트를 이어간다. 해당 종목은 quarantine/EV0/완료 분모로 처리하지 않는다. 대기가 남으면 별도 ledger와exit3을 기록하며 정식 study 보고서를 생성하지 않아 공동 평가/정책 단계로 넘어가지 않는다. 모두 처리한 성공 실행에서 ledger도complete/대기0으로 갱신한다.
- 새로운 retry loop·성능 guard·모듈·grid 축소 없음. 요청/parser/continuation/auth/API read quota와각 요청의bounded wait/retry 계약 변경0. 알 수 없는admission 계약 손실이나provider 오류는글로벌 실패를유지한다. 저가주 재계산 중인b091ef83f worktree를보존하고별도 worktree `widget-deferred-source-repair-20260918`에서보완/검증한다.
- self review 보완: 성공 후 이전 waiting ledger가남지않도록 완료writer 이후progress receipt를갱신했다. 재리뷰범위producer source intake→symbol checkpoint→full population writer→closedloop intake, finding0. 부분/전체대기·잘못된admission의분리 및완료체크포인트 보존/부분보고서 미발행 포함 관련46PASS/compile/diff PASS이다. nativefullworker는검증commit 후새code root에서재개하며selected trading release/PID는변경하지않는다.

## 저가주 전체 경제 재계산 완료

- native full grid 완료:204종목 inventory/유효원천197/원천quarantine7/전체1,020프로필. 경제 checkpoint hit0/miss789이며나머지231프로필은원천 또는integrated-aftermarket 전체범위증거 결손으로계산에포함하지않는다. wall1,625.95초(27분06초), userCPU1,584.71초, systemCPU9.93초, peakRSS657,508KiB이다. 성능수치의범위는이번원천검증+native full build/write invocation이며전체장후chain 시간이아니다.
- [원천 보고서](../../data/report/postclose_research_successor_20260917_20260918/low_price_two_leg_expanded_candidate_research/low_price_two_leg_expanded_candidate_research_2026-09-17.json), [기존로직 전체 비교](../../data/report/postclose_research_successor_20260917_20260918/low_price_existing_logic_full_comparison_2026-09-17.json). 기존로직64개를실제 calibration winner와비교했다. native같은관측창/비용계약의수치비교13개이며양측완료결과·holdout표본(3signal/4completed)·미청산부재를충족한모델비교는3개다. 유효성숙비교의EV개선0/일별순익개선0이다. 실제주문/실현수익/자본가능공동EV가아니다.

| 프로필 | baseline EV% | challenger EV% | EV 차이pp | 완료leg baseline/challenger |
|---|---:|---:|---:|---:|
| 두산에너빌리티 늦은오전 | 0.168286 | 0.168286 | 0 | 8/8 |
| 팬오션 늦은오전 | 0.382903 | 0.382903 | 0 | 10/10 |
| SK텔레콤 오전 | 0.092564 | 0.092564 | 0 | 8/8 |

- 소표본수치상EV상승2개는승격근거가아니다. 팬오션점심 0.070402→0.222456%, +0.152054pp이나challenger1signal/1completed이며시도빈도0.375→0.0625/유효관측일로감소해일별단위모델순익은-1.3525KRW/일이다. 제주반도체오전은challenger2signal/1completed에불과하며baseline EV0의완료표본이없어성숙완료EV비교로인정하지않는다. 단위모델금액을실제10주매매수익이나공동자본수익으로환산하지않는다.
- 전체native결정: prospective580, source/session quarantine231, robust calibration 부적격147, holdout실패57, positive_not_better3, early source-only holdout pass2. native지원추천1은팬오션오전이며그자체가새live종목승격이아니다. baseline EV/paired uplift가미확정인early후보와미래prospective의자연표본 검증은OPEN이다.

## 실제 원천 실패 연결 및 부분 모집단 소비 보완

- 첫deferred-aware native pass는51종목까지진행(29경제완료/17공유read대기/5daily source격리)한후042040에서종료했다. 생산자의실제오류이름은`042040_source_quality_fail`인데consumer catch는`source_quality_not_pass`만포함해식별 가능한종목실패가다시전체를중단한것이다. 실제fetch함수를사용하는회귀를추가하고기존main의정확한native FAIL이름1개만연결했다. 요청/parser/continuation/원천·경제범위/샘플·quality조건은그대로이며원천snapshot parser hash를보존한다. nativeFAIL상세meta는fetch가반환하지않으므로widget ledger에확인하지못한bar/date/SHA를만들어넣지않는다. 저가주AL실패metadata를KRX원천으로오용하지않는다.
- 직접정책/관측catalog consumer가모든199종목에PASS를요구해producer의식별된부분quarantine을글로벌실패로오인하는연결결손도보완했다. strictledger(count/type/universe/정확한native이유/FAILmeta/비평가행/authority false/승격리스트 제외)를검증한격리행만새승격·관측등록에서제외하고나머지종목의기존KRX출처/비용/표본/실행·joint guard를유지한다. 잘못된ledger/미식별FAIL/all-invalid는실패한다. 기존검증된incumbent carry·퇴역/incident/custodyguard는변경하지않는다.
- 최신producer+policy consumer69PASS(47+22)/compile/diff PASS. 재리뷰범위source品質의symbol scope→전체denominator→원천ledger→policy/catalog/closedloop, finding0. source-only실행만하며현재날짜동결policy를교체하지않는다.

- Official reference 확인: upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`, retrieval `2026-09-18T09:28:35.428171+09:00`; inspected `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/specs.py`, `kiwoom/core/errors.py`, `postman/kiwoom-openapi.postman_collection.json`. 현재tracked tree에는`kiwoom_docs`가없음을기록했고기존ka10080spec/Postman/SDK를교차확인했다. protocol의새의미를추정하거나API/auth/order contract를변경하지않는다. 증거:`tmp/low-price-full-research-20260918/official-kiwoom-source-quality-review.json`.

## 최종 코드의 외부 응답 중단과 재개

- `b0c2a0476` full native widget pass는114번째200350 조회에서 `ka10080_response_not_json`으로exit1이었다. 앞선113종목의결과는경제계산47/공유read대기47/개별원천격리19이며정식전체study는발행하지않았다. wall1,582.92초/userCPU983.48초/systemCPU49.86초/peakRSS235,052KiB. 이응답을source PASS·quarantine·EV0으로바꾸거나parser/provider/retryguard를완화하지않는다.
- 동일검증코드로native CLI를재개했다(`widget-full-source-handoff-resume-1.log`). 계약이일치한종목은 `exact_symbol_checkpoint_reuse`를사용하며현재입력계약검증을통과하지못한checkpoint는재사용하지않고평가를갱신한다. 이경우에도native 날짜별kernel cache hit를확인했다. 006800의원천/API없이직접nativefingerprint와checkpointchecksum을검증했고현재fingerprint일치·reusable=true였다. 이전경제checkpoint의무조건재사용이아니다.
- 대기가남으면별도waiting ledger/exit3이며정식전체보고서와공동후속은보류한다. 최종전체결과/원천격리/비교/공동경제성을확인할때까지이owner는OPEN이다.
