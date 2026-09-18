# 디스크 정리와 microstructure 현행 평가 통합 — 2026-09-18

작업본의 기존 machine-primary·auxiliary AI 평가에 원천 결속·수집 분모·비용/결과 연결을 통합했다. 별도 tuner·정책 grid·런타임 진입 기준은 추가하지 않았다. 비용 producer의 AI 연구 선행 조건 의존, 통합/프리마켓 비용 venue 조회 및 Main/shared-rebound의 scope→market-data item 호출 결함도 수리했다. **9/16에는 비용 차감 CF 진단값을 산출할 수 있지만, 9/17은 당일 비용 원천이 없어 경제성 null이다. 실제 이익이나 특징 추가의 인과 ΔEV가 검증된 상태는 아니다.**

증거 디렉터리는 `tmp/microstructure-integration-20260918/`다. canonical 과거 연구 보고서·동결 policy·selected release·service/PID·cron·env·provider budget·주문을 변경하지 않았다. 다른 세션의 선택 root `low-price-postclose-source-resume-20260918`, source `2a1388c69`를 보존했다. 새 구현은 작업본 source-only다.

## 1. 삭제와 디스크 증거

| 대상 | 실행 결과 | 보존 근거 |
| --- | --- | --- |
| Codex archived sessions | 189개, 3,555,353,537 bytes 삭제 | `/proc` 열린 파일 확인; active sessions·app DB/auth/config·memory 보존 |
| private validation mounts | canonical 원본과 SHA256가 같은 파일80,275개, 2,680,921,567 bytes 삭제 | 원본·source/order/custody/PnL은 삭제하지 않음; 독립·고유 파일 유지 |
| 사용하지 않는 managed releases | 8개 제거 | 소스 무변경, branch에서 commit 도달 가능, original copies의 Git blob/canonical hash 확인, 실행·설정·selector/rollback 참조 제외 |
| 완료 working copies | 6개 제거 | 소스 무변경; 기존 폐기된 생성물 삭제와 `.venv` alias만 허용; 고유 config-error log는 작은 진단 사본으로 보존; 마지막 active cwd/FD/args 확인 |

단계별 filesystem 확보 합계는 **8,559,030,272 bytes = 7.971GiB**다. 시작 filesystem 사용률93%/가용 약11.9GB에서 종료87%/가용 약20.5GB로 개선됐다. 실행 중 writes와 새 검증 증거 때문에 전체 free delta는 단계별 합계와 약간 다를 수 있다.

삭제·Git reachability·원본 hash·retention 이유는 `cleanup-manifest.json`, `cleanup-releases-manifest.json`, `cleanup-worktrees-pass2-manifest.json`, `cleanup-worktrees-manifest.json`, `cleanup-new-archives-manifest.json`에 기록했다. 14개 root의 branch/commit은 Git에 유지한다. 다른 변경이 있는 작업본, 고유 policy/consumer/추천·WS 원천, 선택·이전 release 및 systemd/cron 참조 release는 유지했다. 완료 tar archive도 고유 데이터 여부가 입증되지 않은 것은 유지했다. age만으로 실제 runtime lock을 풀지 않았다.

## 2. 원천 → 평가 → 소비 계약

1. `load_machine_observation_rows`는 기존 exact machine capture hash와 setup-evidence 검증을 유지한다. payload의 snapshot·venue/session·bundle, flow/recovery, reaction context, micro-window를 lossless diagnostic binding으로 투영한다. 과거 raw stage/AI score를 현행 기계 판단으로 재구성하지 않는다.
2. 비용/후행 경로의 early continue **전에** 검증된 전체 capture population을 날짜·applied bundle·venue/session·machine action별로 남긴다. identical capture hash 중복은 collapse한다. 기존 경제성 사례의 exact attempt 중복/충돌·terminal lineage 제외도 유지한다. 전체 capture 본문을 기간 전체에 추가 보관하지 않고 file별 compact census만 유지한다.
3. `build_machine_decision_case_table`은 상세 export200개 제한 전에 모든 deduplicated cases의 `microstructure_evaluation`을 만든다. 비용 결손·identity gap·관측 cadence 결손·conflict는 제외 사유에 남기며 수익0으로 보충하지 않는다. 적용 bundle·venue/session·행동·AI prompt/verdict를 섞어 평균내지 않는다.
4. AI의 평가 분모는 machine ENTER_NOW다. exact snapshot/action join·실제 provider 호출·등록 prompt/verdict·semantic/source partition·기존 terminal gate를 적용한다. 미진입 AI 미호출은 N/A, CAUTION/INSUFFICIENT/SEMANTIC_INVALID는 VETO와 구분한다. 기존 source/terminal/holdout/promotion gate만 사용한다.
5. calibration `--write`는 같은 날짜의 microstructure JSON/Markdown에 작은 modern section을 갱신한다. 이미 끝난 5GB raw 진단 재스캔 없이 후행 producer의 전체 통계를 전달한다. 부모 schema/date/filename·source hash/generation을 확인한다. source를 읽은 atime 변화는 generation 변화로 취급하지 않는다. report field 추가 후 artifact seal을 다시 계산하여 기존 정책 publisher hash 계약을 보존한다.
6. `microstructure_summary_contract`를 사용하는 EV/daily/runtime summary가 modern section을 소비한다. 부모 없거나 hash가 바뀌면 source gap과 tuning-input false를 표시한다. 이전 날짜 report로 fallback하지 않는다. runtime/allowed apply는 false이고 실제 EV·순익·인과 model ΔEV는 null이다.

기존 holding source-quality fail-closed 소비와 기계/보조 AI의 live 행동·주문·수량·provider·cap·stop·custody guard는 보존했다. 집계 binding 추가는 사후 평가다. 별도로 Main/shared-rebound의 관측 window 호출을 수리했으므로 배포 후 기존 기계판정 입력에 실제 window가 복원될 수 있다. 판단 임계값·특징 산식·guard는 변경하지 않았다. 현재 selected runtime에는 적용되지 않았다. 기존 workspace의 별도 health/feature-packet 수정은 이번 수정 전 snapshot을 남겨 보존했다.

## 3. 구조 수리

**비용 원천 producer 독립화.** 기존 full-cost source가 별도 R0/provider 연구의 선행 조건에 묶여 있었다. main wrapper의 snapshot/raw/research 작업 전에 기존 calibration producer의 `--write --ensure-economic-reference-only` 모드로 같은 날짜의 비용 source를 확보한다. 긴 작업의 자정 통과 전에 수집할 수 있도록 배치했다. 이후 calibration도 검증된 기존 원천을 재사용한다. 독립 수집은 기존 reviewed policy와 official master parser/producer를 재사용하고, source 입력은 `report/micro_reversion_economic_reference/machine_source_inputs/<date>` 아래에 작성한다. live provider budget/lock/env를 발행하지 않고 report/grid/policy publisher도 실행하지 않는다. 실패는 source gap으로 기록하고 실제 evaluator의 비용 제외/null을 유지한다. 과거 당일 official source 없이 현재 자료·조회시각을 소급 발행하지 않는다.

**경제 reference venue 결속.** integrated/premarket 시장데이터 scope를 catalog의 venue로 조회해 KRX/NXT/SOR 비용을 찾지 못하던 결함을 수리했다. 원 capture와 snapshot이 같은 명시적 broker route 및 integrated market-data route를 증명한 경우에만 그 broker-route profile을 조회한다. 원 effective venue/session은 바꾸지 않는다. route 누락/충돌은 추측하지 않는다. 9/16 비용 제외가1,258→15, 결과 사례가768→1,332로 증가했다. 이 변화는 source 복구이며 threshold 개선이나 신규 이익이 아니다.

**Main/shared-rebound 원천 route 호출.** `ai_engine_openai`의 두 관측 producer가 `evaluate_snapshot(route=effective_venue)`를 호출했다. `KRX_NXT_INTEGRATED`/`PREMARKET_KRX_LIKE`는 기존 item mapper가 받는 KRX/NXT/SOR route가 아니므로 빈 item과 `exact_route_missing_or_duplicate`가 발생한다. 같은 exact AI snapshot의 명시적 market-data route와 symbol/venue/session identity를 검증한 뒤 기존 SOR/KRX/NXT source window를 조회하도록 두 호출을 보완했다. broker route의 비용 조회와 시장데이터 route의 item 조회를 혼동하지 않는다. 새 request·FID/parser·REG/REMOVE·auth/order flow를 변경하지 않고 이미 수집한 snapshot consumer를 수리했다. 누락·충돌·malformed source는 SOURCE_UNAVAILABLE이며 stale/epoch/cutoff/continuity 검증은 그대로다. 긍정 synthetic integrated/premarket와 차단 회귀71PASS이며 미래 live 입력 복원은 기존 기계 조건에 따라 판단에 영향을 줄 수 있어 자연 소비는 별도 확인한다. historical 누락 window를 새 값으로 소급 재작성하지 않았다.

**보고 의미.** nullable `v_pw_runtime_support_usable`을 false로 세던 코드를 고쳐 explicit false와 unknown을 구분하고, Markdown의 v2-only delivery 표기를 v3 applicability로 정정했다. 기존 canonical legacy 집계/73일 rollup을 모두 재작성한 것은 아니다. 검증 successor는 원 legacy as-of를 보존하고 modern 평가를 별도로 추가한다.

## 4. 실제 source-only 결과

9/16 검증은 **해당 날짜 전체 capture만** 기존 loader/가격 labeler/case builder로 평가했다. cumulative 기간 또는 실제 episode 손익의 대표값으로 확대하지 않는다. 원 JSONL/gzip은 stat 후 streaming으로 처리했고 원 generation 전후 일치였다. parent canonical calibration을 부분 보고서로 덮어쓰지 않고 `evaluation-result-2026-09-16.json`과 successor JSON/Markdown을 tmp에 생성했다. 비싼 paired/grid/refinement/full postclose chain·benchmark는 실행하지 않았다. 수리 후 필요한 재검증만 했고, 최종 통계 재빌드는35.5MB normalized rows cache를 사용했다.

| 9/16 분모 | 결과 |
| --- | --- |
| 전체 machine capture | 6,901 |
| invalid capture 제외 | 2,207 |
| verified unique capture | 4,694 |
| exact machine/AI action conflict 제외 | 2 |
| full-cost 미확보 제외 | 15 |
| 기존 후행 path/cost label 미충족 제외 | 3,345 |
| 결과 case | 1,332 |
| 추가 cadence/3m endpoint 제외 | 119 |
| full-cost 차감 CF 결과 | 1,213 |
| source/partition/경제성 연결 가능 auxiliary 사례 | 1; 후보 선정·실제 효과 판정에는 부족 |

단일 applied bundle은 `dac82f7fd8b26f85baba0fc44862a50dc4cab4b85eb4ae30bc7aa8822a1e9ce9`다. 다음 수치는 기존 price labeler의3분 window 마지막 관측에서 검증된 실행 비용 estimate를 차감한 동일 가중 CF다. labeler의 endpoint lag 허용은90초이고 정확한3분 close/fill은 아니다. 10분 metric 내 기존 primary path label과3분 cadence를 유지했다. 실제 보유수량·자본·정책 exit·체결가격의 strategy EV/순익으로 해석하지 않는다.

| scope / machine action | CF 결과 수 | 평균 비용 차감% | 하위5% 관측% |
| --- | ---: | ---: | ---: |
| KRX 정규 BLOCK | 448 | -1.077557 | -3.053901 |
| KRX 정규 RECHECK | 211 | -0.832728 | -2.720696 |
| 통합 애프터마켓 BLOCK | 226 | -1.412673 | -2.684799 |
| 통합 애프터마켓 RECHECK | 97 | -1.333515 | -2.393176 |
| 프리마켓 BLOCK | 142 | -1.758389 | -2.918680 |
| 프리마켓 RECHECK | 84 | -1.605730 | -2.219954 |

ENTER_NOW는5건의 descriptive CF만 있고 source/partition까지 허용된 auxiliary 비용 결과는1건이다. source-bound cases 중 flow/recovery usable814, reaction context usable1,324, exact item/cutoff를 포함한 micro-window usable507이다. 서로 다른 분모다. 일부 피한 가격 경로가 평균적으로 불리했다는 진단은 가능하지만, 일부 missed clean opportunities도 있어 평균 음수만으로 모든 차단이 옳다고 단정하지 않는다. matched opportunity/holdout ablation과 actual ledger 없이 특징의 개선 ΔEV는 null이다.

**9/17.** capture4,508 중 invalid1,166을 제외한3,342건은 exact source binding을 보존한다. KRX 정규1,852, 통합 애프터마켓989, 프리마켓501건이다. 당일 economic reference가 없어3,342건 모두 full-cost 제외로 case/경제 결과0이며 EV·순익은 null이다. `evaluation-result-2026-09-17.json`에 수집 분모와 source gap을 남겼다. 유효 no-edge/무기회/정책 실패 판정이 아니다.

## 5. 남은 결손과 closure

| 결손 / owner | 시간 대기로 해결되는가 | 다음 행동·closure test |
| --- | --- | --- |
| 새 비용 수집·late link의 자연 적용 / wrapper + calibration | 배포 후 다음 같은 날짜 실행으로 확인 | early source-only 모드→검증된 당일 reference→calibration 전체 cases→modern micro section→EV/daily/runtime summary의 같은 parent SHA 확인. 기존 strict dated publisher/PREOPEN gate를 유지 |
| 9/17 당일 비용 source 없음 / economic reference owner | 이미 지난 official master source는 단순 대기로 생기지 않음 | 실제 retained 당일 provenance가 발견되면 기존 validator로 bounded 복원; 없으면 irrecoverable source gap/null 보존. 현재 master를9/17로 소급 금지 |
| 통합/프리마켓 micro-window 결손 / Main/shared-rebound→machine_confirmation_routes→entry_adverse_flow | 호출 결함 source 수리 완료; 자연 수집은 별도이며 과거 tape는 대기로 회복 안 됨 | 9/17 통합989/프리501 모두 window source gap. 보완된 두 producer에서 명시 market-data route의 exact item·epoch·causal cutoff·0B/0D 원천→snapshot→machine capture 연결 확인. source window를 label만으로 PASS하지 않음. protocol 수리가 필요하면 official Kiwoom reference gate부터 적용 |
| 경로/관측 coverage / ai_decision_quality labeler + retained route prices | 현재 당일 pending은 성숙 가능;9/16·9/17 historical gap은 아님 | 원 같은 route/session과 정확한 anchor/retained prices가 있는 경우만 bounded 복구. 10분 metric의 기존 primary path predicate를 유지했으므로 그 경로 결손을3분 결과만으로 승격하지 않음 |
| auxiliary 표본 부족 / 기존 machine/AI case table·router | 정상 ENTER_NOW·actual compact 호출·valid cost 결과 유입 시 증가 | 버전별 exact join, partition/terminal/semantic 보존과 기존 floor/holdout gate로 판단. 미호출 AI 결과 가정·threshold 완화·별도 tuner 추가 금지 |
| actual economics / 기존 applied-version completed ledger | 실제 정상 소비·완료 체결·비용 정산 이후 | existing publisher/PREOPEN/PID→자연 판단/submit→actual COMPLETED+valid costs를 기존 owner로 추적. diagnostic CF·기존 회복 손익과 신규 순익을 합산하지 않음 |

## 6. 반복 review·검증

수리 중 export200행의 잘못된 분모 위험, 비용 early-continue의 invisible population, catalog venue mismatch, 부모 seal 갱신 누락, 구 report publisher 호환성, atime 오판, source-window item과 주문 route 혼동, 기존 auxiliary gate 승계 및 Main/shared-rebound scope alias 호출 문제를 검토·보완했다. reviewed source/diagnostic 계약의 미수리 finding은0이다. 위 원천·표본·자연 적용·실제 성과 acceptance는 별도 OPEN이다.

- producer/기계·보조 AI/holding feature/정책 publisher 회귀: **280 PASS**, `targeted-pytest.log`.
- 기존 EV/daily/runtime microstructure 소비 회귀: **4 PASS**, `consumer-pytest.log`.
- calibration strict-verifier 계약 회귀: **13 PASS**, `verifier-contract-pytest.log`.
- actual Main/shared-rebound 관측 adapter 및 adverse-flow/auxiliary 회귀: **71 PASS**, `live-binding-pytest.log`; 관련 합계 **368 PASS**.
- affected Python compile, wrapper `bash -n`, `git diff --check`: PASS.
- 문서/체크리스트: link/단일 owner 및 print-only parser의 증거는 `backlog-final.json`·`closure.json`.
- 배포·재시작·현재 자료로9/17 비용 소급·전체 장후/grid/benchmark·실주문/provider AI 호출·외부 Project/Calendar sync는 실행하지 않았다. source code SHA와 parent artifact SHA는 normalized-case rebuild 결과에 남겼다.
