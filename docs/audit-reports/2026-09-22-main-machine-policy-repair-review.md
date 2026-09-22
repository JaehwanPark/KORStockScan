# 9/22 메인 기계판정 학습·장중 적용 보완 리뷰

범위: [기계정책 보완 계획](../proposals/main-nonentry-threshold-postclose-runtime-implementation-plan-2026-09-21.md)의 M1–M6. 사용자 승인: 구현·반복 리뷰·커밋/푸시·배포·장중 정책 적용·장후 재계산. AI VETO/PASS 최적화, widget/episode 정책 및 주문/수량/보유 가드는 이번 변경에 포함하지 않는다.

## 코드 리뷰와 검증

- M1: 82좌표 registry 계약, control4/single20/local_joint24/selector_leaf32/broad_joint16, predecision blocker·미탐색 좌표·지원 source 우선. 승률 → 평균 비용 후 경로 EV → 회복값 → 기회 수 → 단순 정책. 음수 EV 허용.
- M2: train best/visited/cursor/군별 진척/domain/selector/budget version checkpoint, 후보가 있어도96회 전에 holdout에 접근하지 않음. 부모 tree/unknown/source fallback 승계와 유효 후보 중복 제거.
- M3: AI join 없이 기계 capture+기존 비용/가격경로만 읽는 loader. 원천 누락은 행별 부모 fallback, 손상된 봉·metadata는 개별 제외. 완성봉 producer→AI 축약 우회→기계 raw→재생 연결. 시가총액은 기존 수집기의 별도 시점 snapshot, historical legacy Marcap 소급 사용 없음.
- M4: 부적격 고득점 scope가 적격 scope를 막지 않음. scope별 parent CAS 검증 후 다중 scope atomic generation, AI component 보존.
- M5: attempt bundle pin, 제출 전 세대 검증/recheck, PID/start ticks/leaf/임계치 capture, 날짜 변경 carry, machine-only rollback.
- M6: 정규 장후·수동 wrapper의 독립 machine stage와 terminal receipt 연결. 전체 legacy 보고서의 중복 immediate activation 제거.

대상 pytest648건 PASS(로그: `tmp/main-machine-repair-20260922/targeted-tests.log`), Python compile·두 wrapper bash 문법·diff 검증 통과. 기존 `test_openai_scalping_analyze_target_returns_feature_audit_fields` 1건은 이번 diff를 제거한 HEAD 코드에서도 `computed_not_sent`/`not_attempted` 관측 문구 불일치로 실패함을 별도로 확인했다(`baseline-audit-field-test.log`). 이 기존 보조 관측 테스트를 제외한 변경 범위 검증이다. 실제 provider/주문 테스트는 실행하지 않았다.

리뷰 중 보완: 부분 결손 때문에 전체 좌표를 동결하는 로직 제거, AI mismatch 행 제외 연결 제거, 기존 tree의 unknown/결손 fallback 보존, AI formatter의 완성봉 제거 경로 보완, primitive 손상 row 사전 격리, 동일 input 중단 재개 시 탐색 순서 고정. 예비 계산은 train checkpoint에서 중지해 검증되지 않은 후보를 적용하지 않았다.

입력 재검토에서 promotion ID가 없는 기회를 기존 admission 검사가 먼저 제외하는 결함을 추가 발견했다. 독립 machine 경로만 date/attempt/symbol/venue/session/bundle 식별자를 허용하고, 같은 exact attempt의 상충 증거는 양쪽 모두 격리한다. AI/기존 통합 경로의 계약은 유지했다. 부동소수점의 극미세한 EV 차이로 동일 성과의 다수 기회 후보가 밀리지 않도록 순위 비교를 소수10자리로 정규화했다. 수정 후 핵심302건 PASS를 고정 배포본에서도 확인했다. 누락 수정 이전 계산은 `before-admission-fix-machine_policy_2026-09-21.json`으로 보존하고 발행하지 않았다.

## 공식 원천 확인

2026-09-22 KST 확인 upstream HEAD `953e5dbff123f437ab4d11a78a95191a685eb51f`. `kiwoom_docs`는 현재 upstream tree에 없음. `kiwoom/specs.py`, `kiwoom/core/client.py`, `kiwoom/_data/kiwoom_api_spec.json`, `postman/kiwoom-openapi.postman_collection.json`의 ka10001 요청/응답을 대조했다. POST `/api/dostk/stkinfo`, api-id ka10001, 종목별 stk_cd 및 기존 continuation/오류 처리 유지. `mac` 공식 단위는 억원이며 새로운 snapshot만 ×100,000,000 KRW로 변환한다. 같은 응답의 보고 시총을 사용하고 가격/상장주식수를 사후 혼합하지 않는다. 실제 API 호출 추가, 주문·인증·WS 변경 없음. 시각과 확인 항목은 `tmp/main-machine-repair-20260922/official-reference.json`에 보존.

## 최종 계산·배포·소비

- 코드 `7741517b4`, 입력 admission 추가 수정 `17653b451` 모두 main push 완료. 최종 immutable release: `/home/ubuntu/KORStockScan-runtime-releases/main-machine-20260922-17653b451`. 최종 guarded restart09:13:32, PID47171, PID/env bootstrap PASS. 검증 전용 provider/주문 호출 없음.
- 원천 cutoff와 명시 train cutoff2026-09-21, 학습 날짜9/14·15·16·21. 이후 미관측 holdout은 없음이며 독립 검증 성공으로 표현하지 않는다. 독립 계산 terminal09:32:54 `completed`; 각 scope96회 탐색을 마쳤다. artifact: `data/report/ai_decision_action_outcome_calibration/machine_policy_2026-09-21.json` 및 `machine_policy_terminal_2026-09-21.json`.
- KRX admission:1214→1868판정, promotion ID 부재654건을 attempt identity로 복원. 미진입 비교872기회/1846판정. 기존 source contract 부적합154건 제외; 봉/metadata primitive 검사 이후 추가 제외0. 82좌표 중 역사적 완성봉 원천이 없는13개는 부모값 유지. 현재 장중 자연 capture의 완성봉10개/hash/time 검증 PASS. 시총 snapshot writer/reader는 구현·대상 검증했으며 아직 자연 수집 snapshot은0개이므로 현재 자료에서는 unknown이다.

아래 값은 **새로 ENTER_NOW로 전환된 미진입 기회**의 비용 반영 가격경로 값이다. 전체 정책 또는 실제 체결의 손익/승률이 아니다.

| 구간 | 입력 판정 | 미진입 비교 기회 | 새 전환 기회 | 승률 | 평균 경로 EV | 기존 ENTER_NOW 영향 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| KRX 정규 | 1868 | 872 | 1 | 100% | +0.1000% | 22건 모두 유지 |
| KRX/NXT 장후 통합 | 349 | 35 | 1 | 0% | −1.1884% | 2건 중1건 유지·1건 RECHECK |
| 장전 KRX-like | 230 | 15 | 1 | 0% | −1.2831% | 1건 유지 |

음수 EV 자체를 갱신 차단 조건으로 쓰지 않는 사용자 기준을 적용했다. 표본이 각1기회인 결과이며 일반화·실현 수익 개선 증거가 아니다. KRX 변경은 `tape_supportive_score=60`, `tail_fillability=2.5`; 장후 통합은 `early_volume_ratio=1.4`, `momentum_accelerating_score=54`, `top1_supportive_ratio=2.5`; 장전은 `tape_supportive_score=60`. 나머지 값은 각 부모에서 승계한다. selector+leaf32회도 평가했으나 이번 승자는 각 root1개 정책이다. 유형 선택 기능의 미구현을 의미하지 않는다.

- KRX 군별 attempted4/20/24/32/16, 유효 평가2/19/23/32/7. 순서·범위 제약에 어긋난13조합은 validation/replay에서 제외했고 다른 후보 탐색을 지속했다. 원천 입력 손실과 부적격 임계치 조합 거절을 구분한다. 자세한 scope별 지표·전이는 `tmp/main-machine-repair-20260922/final-scope-results.json`에 보존.
- 09:33:22.880640 세 구간 atomic activation 완료. bundle `a552d63ac3c3c33b310ee7ea6cdb6b7528b5ce3905dae601a7008f498c14137d`, 이전 `cdeff4e82473b3c850fb184861c35d10f96bee5f6407834e14e41840b06a27b6`. 전 scope AI component 동일, 9/23 로더의 동일 bundle 승계 검증 PASS. 계산 terminal은 발행 이전 영수증이므로 activation=null/PID=false를 보존하고, 후속 발행은 `activation.json`·`activation-validation.json`에서 별도 증명한다.
- 최종 selected release의 정규 postclose route, inactive machine-final-refresh 서비스 binding, 필수 cron4개 routing PASS. 다음 정규 회차는 독립 machine stage의 `--write --activate-now`를 거치며, 후속 AI 작업 실패가 이미 발행된 machine generation을 기본값으로 되돌리지 않는다. 기존 전체 runner 분리와 AI 양방향 학습은 연결된 별도 계획 소유다.
- 자연 PID 소비 완료:09:39:50.951600~09:40:20.806801 KRX4건, PID60693/start ticks1079749/cwd최종3a79e240f/src. machine hash `0ccd3dddcd918d88b8a4ab30351e4ac9930d1b62e91a5653a517af6b525bb85f`, bundle위a552d63, AI hash `c7b686514d2061cdfb9871b36c05222e20f94a79e2669a03ff5dd7dcc1cea7d5`. 네 건 모두 실제 적용값tape60/tail2.5를 기록했다. `natural-policy-consumption.json` 및 생성·배포·발행·PID·cron을 묶은 `final-acceptance.json` 보존. 다른 시간 구간의 자연 선택은 해당 세션에서 별도로 관측하며, 현재는 전 scope 발행/로더와 KRX 자연 bundle 소비를 확인한 범위다.

## 장중 소비 검증 중 추가 수리와 종결

09:31경 기존 제출 후 기록 경로에서 split policy 영수증 키가 stock 및 leg metadata 양쪽 `**kwargs`로 전달돼 TypeError가 발생하고 sniper loop가 중단된 것을 발견했다. 정책 발행09:33 이전부터 발생한 별도 기존 결함이며 새 정책 소비를 막았으므로 같은 완료 범위에서 수리했다. 두 필드 집합을 기존 병합 helper에 넣어 실제 leg 영수증 우선순위를 유지했다. broker/account/order request·수량·보유/청산 판단 변경 없음. 실제 주문 없이 제출 후 기록 표현식을 실행하는 회귀 및 관련172건 PASS, 고정 배포본 재검증172건 PASS. 검증 결과와 stack은 `post-ack-tests.log`, `release-post-ack-tests.log`, `post-ack-runtime-incident.log`.

추가 코드 `3a79e240f` main push, 최종 release `/home/ubuntu/KORStockScan-runtime-releases/main-machine-20260922-3a79e240f`. guarded restart09:39:08/PID60693, env bootstrap와 custody handoff PASS. 재계산 없이 기존 a552d63 정책을 승계했다. 최종 source/서비스/cron route도3a79e240f로 재확인했다. 기존 접수 종목222800은 재기동 후 정상 보유 관리의 TRAILING 매도 체결을 관측했으나 이를 이번 튜닝의 수익 검증으로 사용하지 않는다. 별도 청산 영수증에서 `EXIT_RECEIPT_SUBMISSION_CUSTODY_CONTRACT_BLOCKED / exit_session_matches`가 관측됐으며, 기계정책 수리 완료와 청산 custody/실현손익 검증은 구분한다.

**M1–M6 구현·검증·계산·장중 정책 적용·자연 PID 소비·정규 장후 연결 완료.** 한정96회 탐색은 전역 최적성 증명이 아니며, 신규 전환 각1기회·역사적 원천 결손·독립 미래 holdout 부재를 그대로 공개한다. 보조 AI 튜닝/전체 runner 분리/청산 영수증 검증을 기계정책 완료로 합산하지 않는다.


## 소표본 승률 과대평가 추가 보완 — 2026-09-22

사용자 요청:1개 기회의100% 승률이 정책 선정을 독점하는 문제 개선. 기존 기계 전환 평가 안에서 원 승률 대신 표본 보정 점수를 우선 비교하도록 변경했다. Wilson 형태 z=1.645의 보수적 점수이며, 반복 attempt가 아닌 고유 기회 수를 사용한다. 원 승률·순 EV·paired delta는 보존하고 음수 EV도 계속 허용한다. 새로운 최소 표본/손익 승격 장벽, 보조 AI/청산 의존성은 추가하지 않았다.

- 공유 rank 함수로 후보와 scope 선택을 일치시켰다. 선정 버전을 input hash/frozen 재사용 조건에 넣어 이전 raw-win-rate best/checkpoint를 새 점수의 결과로 재사용하지 않는다. train/holdout 모두 원 승률과 보정 점수·점수 버전을 기록한다.
- 1/1은26.99점,6/10은35.16점,12/20은41.86점으로 단일 성공의 과대평가를 할인한다. 상관·부분 승률을 포함한 순위용 점수이며 실제 승률/유의성 보증이 아니다.
- 저장된9/21 후보를 source 재계산 없이 순위만 다시 확인했다. KRX 기록83개 중 유효7개, 최상위1기회100%/+0.10%→26.99점, 최대5기회40%/−0.73906%→14.27점이다. 새 기준에서도 KRX 최상위는 같다. 통합/장전은 유효 후보의 표본이 모두1개여서 표본 보정으로 더 나은 근거를 새로 만들어낼 수 없다.
- 근거:`tmp/postclose-stage-separation-20260922/support-rank-comparison.json`(원 보고서 artifact SHA 포함), `support-rank-final-tests.log`309tests PASS. 원 정책 bundle `a552d63…` loader PASS. 큰 원천/학습/provider 재실행 없이 기존 후보 점수만 분석했으며 정책 pointer를 변경하지 않았다.
- scope 선택 fixture에는 실제 계약에 필요한 표본 수를 명시했다.1/1 대6/10·12/20·18/30 비교, 반복 attempt 불변성, 음수 EV 동점 비교, invalid 표본, 선정 버전 변경 후 재탐색을 검증했다.
- 직전 정책 전체보다 우수함의 입증이나 소표본 문제의 완전 해소를 주장하지 않는다. 기존 ENTER_NOW 유지/제외의 손익 비교와 새 날짜의 자연 성과는 이 점수 개선과 별개다.


### 장중 재생성 중 추가 범위 결함 수정

장중 교체 승인 후 eb3079c96에서9/21 source를 현재 a552d63 부모로 다시 평가했다. KRX96회 중 유효 신규 전환 후보는3기회33.33%/−0.7421%였으나, 기존 ENTER_NOW23attempt 중15를 RECHECK로 바꿨다. 이15건의 손익은 미진입 전환 점수에 포함되지 않는다. 발행 전 계산 PID93556을 종료하고 기존 정책 pointer를 유지했다.

선정 loop와 공통 promotion validator에서 기존 ENTER_NOW 변경 후보를 제외하도록 보완했다. 변경 횟수는 저장된 action transition에서 계산한다. 원 승률·표본보정·음수 EV 허용 조건은 유지하며 이 조건은 범위 밖 미평가 영향의 방지다. 선정 버전은 `support_adjusted_win_rate_preserve_entries_v3`이다. 현재 유효 정책 및 기동 여부와 새 후보 적용을 구분하며, 유효 후보가 없으면 정책은 carry한다.310개 회귀검증 PASS.


장중9/22 preflight를 새로 생성했고 `machine_threshold_tuning_input_allowed=true`를 확인했다. 최신 자료를 읽은 첫 실행은 기존 통합시장 정책의 과거 ENTER_NOW 변경1건에 새 검증 조건을 소급 적용해 `strategy_current_economic_binding_invalid`로 중단되었다. 정책 pointer 변경은 없었다. 수정: 기존 발행분 읽기에만 이전 계약을 유지하고, 신규 후보는 `preserve_existing_entries=true`와 strict 승격 검증을 요구한다. 기존 정책 검증을 원천 로딩 앞으로 옮겼다.311tests 및 실제 기존a552d63 로더 재검증 PASS.
