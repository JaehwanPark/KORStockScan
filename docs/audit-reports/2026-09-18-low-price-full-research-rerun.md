# 2026-09-18 저가주 전체 연구 재실행 — 9/17 결과 successor

- Owner: `LowPriceExpandedResearchRepair0918`. 사용자 추가 승인: 전체 연구 재실행, 유효한 비교·공동 EV 도출 및 전일 장후 결과 갱신. 기존 동결 정책/원본 보고서/실행 중 서비스/정지cron/quantity·비용·grid·sample·provider·custody·안전 guard를 보존한다.
- 연구 source release: `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`, `/home/ubuntu/KORStockScan-runtime-releases/low-price-research-repaired-20260918`. 거래일9/17, clean prefix6/05 이후73거래일/latest16 holdout. source successor root: `data/report/postclose_research_successor_20260917_20260918/`.
- 전체 저가주 경제 checkpoint는새 scope에서0개로 시작한다. native source 계약 검증 후197개 원천 cache를 사용하며 과거 경제 결과 전체를 재사용하지 않는다. 기존789개 cache-disabled hint만 native 검증 하에 재사용하여 이미 비효율로 판정된 optional cache probe의 불필요한 반복을 피한다. 정책·분석 깊이 변경이 아니다.
- 선행 widget 전체199종목 producer는5종목 계산 뒤 외부응답 `ka10080_response_not_json`으로1차 중단했다. 원천/경제 체크포인트 보존 후1회 복구 실행 중이다. 완료 종목의 source/code/cost/applied incumbent fingerprint가 검증된 경우에만 native 경제 checkpoint를 재사용한다.
- 공동 평가 직접 소비자의 초기 study intake/dependency hash/current receipt 검증에32MiB 제한이 남은 결함을 생산자의 기존128MiB stable no-follow reader로 통일했다. 다른 JSON dependency는기존32MiB를 유지한다. large full-study 소비와order-authority rejection회귀38PASS; nativeclosedloop 추가검증의 고정9/17 fixture가실제9/18 clock을사용하던 불일치를 fixture clock 고정으로 수리했고44PASS이다. production 날짜/자본 source guard는완화하지 않는다.
- 현재9/17 allocator/native_capacity/capacity_source 원천은부재이다. `capacity_2026-09-17.json`은WS 구독 범위 receipt이며현금/보유/예약자본이 아니다. native source acquisition CLI는현재완료일20:05 이후만 허용하므로9/18 잔고를9/17로 재라벨링하지 않는다. 보존된 동등 과거증거가없으면 feasibility/공동 EV의미확정은수치로 대체하지 않는다.
- 실행/회귀/원천scope receipt: `tmp/low-price-full-research-20260918/`. 이 문서는실행중기록이며전일 전체postclose DONE 또는경제성 PASS가아니다. 최종full study/source generation/비교/공동 EV 결과는후속 섹션에기록한다.

## 선행 producer 결함 보완

- 2차 native widget 실행은14번째001550의 `daily_source_coverage_fail`에서 전체 중단했다. 날짜별 native 격리 후에도 family floor에미달한 식별 가능한 symbol의문제가나머지198종목/공동 입력전체를중단시키는 orchestration 결함이다.
- 기존 main에해당symbol의daily coverage/snapshot coverage/source quality 실패만catch하여quarantine ledger와원source SHA/실제failed date·bar count/비율을보존하고다음symbol로진행하게보완했다. 전체199종목denominator를유지하고failed row는EV/승격/공동 선택에포함하지않는다. 글로벌provider 오류는여전히raise하며all invalid는valid empty로쓰지않는다. 기존 날짜격리/floor·원천read/parser·API retry/budget/quantity/경제kernel·promotion guard 변경0.
- 관련suite43PASS/compile/diff PASS, 코드producer→population handoff→widget policy/closedloop 소비 재리뷰 finding0. 최초 closedloop82PASS와별개 검증이다. 변경된 producer 계약에대한 native cache validation을유지하고출력원본을덮어쓰지않는다. source-only 연구 worktree에서리뷰된새commit으로worker를다시기동한다. 현재selected cf8d573a6의실행중trading source는변경하지않는다.
