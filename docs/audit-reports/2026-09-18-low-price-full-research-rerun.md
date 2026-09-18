# 2026-09-18 저가주 전체 연구 재실행 — 9/17 결과 successor

- Owner: `LowPriceExpandedResearchRepair0918`. 사용자 추가 승인: 전체 연구 재실행, 유효한 비교·공동 EV 도출 및 전일 장후 결과 갱신. 기존 동결 정책/원본 보고서/실행 중 서비스/정지cron/quantity·비용·grid·sample·provider·custody·안전 guard를 보존한다.
- 거래 서비스 source release: `cf8d573a6b4577b059b2ce1c27b55ad507e19a91`, `/home/ubuntu/KORStockScan-runtime-releases/low-price-research-repaired-20260918`. 거래일9/17, clean prefix6/05 이후73거래일/latest16 holdout. source successor root: `data/report/postclose_research_successor_20260917_20260918/`.
- 전체 저가주 경제 checkpoint는새 scope에서0개로 시작한다. native source 계약 검증 후197개 원천 cache를 사용하며 과거 경제 결과 전체를 재사용하지 않는다. 기존789개 cache-disabled hint만 native 검증 하에 재사용하여 이미 비효율로 판정된 optional cache probe의 불필요한 반복을 피한다. 정책·분석 깊이 변경이 아니다.
- 선행 widget 전체199종목 producer는5종목 계산 뒤 외부응답 `ka10080_response_not_json`으로1차 중단했다. 원천/경제 체크포인트 보존 후1회 복구 실행 중이다. 완료 종목의 source/code/cost/applied incumbent fingerprint가 검증된 경우에만 native 경제 checkpoint를 재사용한다.
- 공동 평가 직접 소비자의 초기 study intake/dependency hash/current receipt 검증에32MiB 제한이 남은 결함을 생산자의 기존128MiB stable no-follow reader로 통일했다. 다른 JSON dependency는기존32MiB를 유지한다. large full-study 소비와order-authority rejection회귀38PASS; nativeclosedloop 추가검증의 고정9/17 fixture가실제9/18 clock을사용하던 불일치를 fixture clock 고정으로 수리했고44PASS이다. production 날짜/자본 source guard는완화하지 않는다.
- 현재9/17 allocator/native_capacity/capacity_source 원천은부재이다. `capacity_2026-09-17.json`은WS 구독 범위 receipt이며현금/보유/예약자본이 아니다. native source acquisition CLI는현재완료일20:05 이후만 허용하므로9/18 잔고를9/17로 재라벨링하지 않는다. 보존된 동등 과거증거가없으면 feasibility/공동 EV의미확정은수치로 대체하지 않는다.
- 실행/회귀/원천scope receipt: `tmp/low-price-full-research-20260918/`. 이 문서는실행중기록이며전일 전체postclose DONE 또는경제성 PASS가아니다. 최종full study/source generation/비교/공동 EV 결과는후속 섹션에기록한다.

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
