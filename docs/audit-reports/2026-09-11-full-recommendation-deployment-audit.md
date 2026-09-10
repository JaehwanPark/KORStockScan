# 위젯·에피소드 추천/배포 전수 점검과 미커밋 통합

관찰일: 2026-09-11 KST. 원 장후 source date는 2026-09-10이다. 사용자 요청은 전체 추천 구현 여부·최신 배포 반영 여부 점검과 모든 Git 미커밋 사항의 commit/push/main 병합이다. 이번 점검은 새 실주문·정책 강제 선택·서비스 재기동을 실행하지 않는다.

## 판정

- 추천 전수 구현 완료: **아니오**. 최신 원장67행 중 위젯/에피소드18행은 보류12, 근거 차단2, 거절3, 관찰1이다. 현재 이18행의 구현 요청0이며 조건 미충족 연구/후보를 코드 누락으로 바꾸지 않는다. 별도 승인된 보조청산·진입 직전 악화 보류·WS 목표 상향의 구현/배포는 아래 별도 근거로 확인했다.
- 배포본 전체 최신 소스와 동일: **아니오**. machine 소유148개 코드/설정 파일은 작업폴더와 byte hash 불일치0. 메인 정체청산 adapter의 공통 함수 추출1개는 현재 두 배포본에 미반영이다. 이 변경은 기존 연산과 동등하며 현재 기동의 필수 blocker가 아니다. 추가 recheck 회귀 테스트1개도 배포본에 없으며 실행 코드 변경은 아니다.
- 공통 `939d90f6`은 장후 수리 범위를 선택한 배포본이고 machine `f9d53a9a`의 전체 기능을 포함하지 않는다. 공통과 machine의 별도 배포 범위를 유지한다. Git main 병합만으로 배포 선택이나 PID가 교체되지 않는다.

## 현재 generation의 추천 전수

원장 rows SHA256: `fa7556b4b9ff01c8e2fb3d7a6dbbb24dd2986884611c4c7fd395c67d47b79aa9`. producer13개 source hash/target date 검증, issues0, 보존식 PASS, native ID 미분류0. 기존 frozen Pass2와 같은 generation이다. 전체 요청15는 main의 증거 차단15이며 machine18행과 혼합하지 않는다.

| Owner | Native ID | Scope | 원 decision | 점검 결과 |
| --- | --- | --- | --- | --- |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:0b57ab867a9e8c770d3c1483720e25c7da5266661339a50e41fe185547abaacc` | 011170/midday/existing_011170_midday | source_only_requires_review_and_user_approval | deferred |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:0bdfc39c76573e968028e3e36bea0f840b8249c225566ea71ae456c3c248b563` | 034020/midday/existing_034020_midday | source_only_requires_review_and_user_approval | deferred |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:2c12077e277ea743fbc2add1007b002a6d0fd3412fc31fa51a91d064914412d8` | 111770/late_morning/existing_111770_late_morning | source_only_requires_review_and_user_approval | deferred |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:3287c340cabe4b868a3283e957a49c5ae5bf8494fb936d371c8bd5f20b934400` | candidate_475560_morning | None | blocked_missing_evidence |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:79378c4760f654a1de2c3ccc44d9be88e31304a1bf2f9f4ca58829fc3b2e6e93` | 108320/morning/candidate_108320_morning | source_only_requires_review_and_user_approval | deferred |
| low_price_two_leg_expanded_candidate_research | `low_price_two_leg_expanded_candidate_research:7b7011b346c958821a742e8461b3cc589c4f575a216c4af83b22dc8a2f518d9d` | 011170/afternoon/logic_lotte_chemical_afternoon | source_only_requires_review_and_user_approval | deferred |
| machine_microstructure_attribution | `machine_lifecycle_turnover_policy_research_v1` | machine lifecycle | EVIDENCE_ACCUMULATING | observed_no_patch |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:1876a96dff2b6afebb1f445538c9a487def36028174fe64880e497c68d19745a` | 361610/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:1ed187a6c7bf27db9dd41bb361c3005e4bc961b64036fa65e2159e926ed22322` | 484870/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:2eaf06787075f5631a2790102165df3f4813b7c8778c2d1e0bd34d9d264c9334` | 142760/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:519bad7f319ed282a6130f6ef2c55cc353c5cbf7f1de96bea8e07b8448bef3e3` | 033640/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:7ff28758a02a80ced86c9d279c6b46cb0b02a95a5eb6186245551a68d8ee66d2` | 138080/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:bf75a6fe44b5b537d1fd09e26ee5a0131e3cb4ea87cf37e6b5b05e18d06a501d` | 240810/KRX_REGULAR | research_watch | deferred |
| widget_collector_expansion_recommendation | `widget_collector_expansion_recommendation:d3845195b73790a6428270bb61f84eaaa065879844b08240e9995643f52e2b88` | 007810/KRX_REGULAR | research_watch | deferred |
| widget_symbol_signal_policy_research | `widget_symbol_signal_policy_research:1a6aebfa63c42f751b0242e3e18a558d326ca01f58eb3055c6b699316120f216` | 475150/KRX_REGULAR | holdout_failed_no_widget_runtime_promotion | rejected |
| widget_symbol_signal_policy_research | `widget_symbol_signal_policy_research:2991bcc69c56990b25c4b08aaf4fdd60e5d3173a67c6592ec632d5328db3c16d` | 006800/KRX_REGULAR | holdout_failed_no_widget_runtime_promotion | rejected |
| widget_symbol_signal_policy_research | `widget_symbol_signal_policy_research:814eab726593d89d0288fe3ad6a3d6fcb3d3dbc4fe5a1d6dff5ca6d17b32d0a0` | 010140/KRX_REGULAR | holdout_failed_no_widget_runtime_promotion | rejected |
| widget_symbol_signal_policy_research | `widget_symbol_signal_policy_research:f4ef9259aaa1ee8420d52ce4303595054ec87d2981b617f425739820921042b3` | 080220/KRX_REGULAR | component_economics_or_holdout_not_ready | blocked_missing_evidence |

보류: 저가주 기존/신규 profile5개는 exact-date 정책과 profile 검증 전이며 widget research-watch7개는 수집 후보로 실제 편입이 아니다. 근거 차단은 `candidate_475560_morning`의 실행 증거와 위젯080220의 component 경제성/holdout이다. 거절3개는475150/006800/010140의 holdout 실패다. 관찰1개는 기존 lifecycle 증거 누적이다. 이전 전체-scope 승인 추가기능을 이 신규 종목/프로필 확대 승인으로 전용하지 않았다.

## 실제 배포와 승인 기능

| 대상 | 코드/정책/실제 소비 | 남은 상태 |
| --- | --- | --- |
| 공통 main/장후 | `postclose-repaired-20260911` / `939d90f629051d2b832d10bf419acf17507a7572`; 선택 HEAD·source clean·cron9 경로 PASS | 9/11 PREOPEN·실제 main PID 예정 전 |
| Widget/episode | `reviewed-additions-20260911` / `f9d53a9ad202c18fdb7f4f50a54475e0560856aa`; 소유148개파일 일치, widget2651657/active/NRestarts0, 9개80-drop-in | episode 기존 자연 timer/preflight와 신규 entry/정산 확인 |
| 최소 보조청산 | `machine_profit_stagnation_v1`, 기존 지속 pin 유지 | 신규 entry/원 목표 복구/비용 대사 |
| 진입 직전 악화 보류 | `machine_entry_adverse_flow_v1`, `all_existing_widget_episode`; 단일 scope 제한 없음 | 기존 timing-conflict·expiry·freshness/원 owner guard 유지, 실제 판단/전송 확인 |
| WS 목표 상향 | `machine_ws_target_ratchet_v1`, widget/episode 모두; 원 owner 한 tick AMEND·수량/receipt 검증 | 신규 entry만, 실제 전환/체결 및 비용 후 효과 미관측 |

[직전 배포·세 정책 pin 검증](2026-09-10-approved-additions-deployment.md)을 재대사했다. V2.14 승인 코드10개 hash는 선택 공통 배포와 일치한다. 미커밋 main adapter는 그10개 pin 파일에 포함되지 않지만 향후 배포에는 `src/trading/order/profit_stagnation.py` 의존성을 함께 포함해야 한다. 이번 요청의 배포 점검 결과를 강제 선택/재기동으로 바꾸지 않았다.

## 미커밋 전수 리뷰와 검증

- 최초 snapshot62개: Python2(실행 코드1·회귀 테스트1), 문서9, 생성자료51(기존 cache/CSV2·보고서49). 모든 파일을 별도 worktree에서 복사·hash 고정했다. ignored runtime/원장/자격증명·로그는 Git 미커밋 분모에 추가하지 않았다.
- main adapter의 eligibility/기존 수익 floor·score prior·상태 저장·reset/wait/exit 결과를 직접 비교했다. 공통 계산의 독립 이전 구현 parity와 실제 adapter tests로 연산 동등성을 검증했다. 주문/수량/threshold/provider 변경은 없다.
- recheck 회귀는 잘못된 과거 날짜를 그대로 보존하면서 rolling3일 창 이동 후 품질 통과/실패를 나누고, 선행 실체결/양수EV 없는 초기 선정과 장중 확대 OFF를 검증한다. 기존 producer 정책 코드는 변경하지 않았다.
- 관련 tests214 PASS; main adapter16 PASS(비관련1029 deselected). Python compile, 문서 print-only parser, diff/비밀정보 패턴/JSON·CSV 형식 및 native source hash 검증 결과를 최종 확인한다. 생성 report의 모든 경제 계산을 재현한 검증은 아니다.
- 기존 문서의9/10 오전/장후 완료 시각은 역사적 receipt로 보존했다. 최신 배포/현재 OPEN 안내와 충돌하는 읽기 경로에는 이번 점검 링크를 보완한다. 전체 adaptive 연구의 과거 미완료를 현재 추가 필수 개발로 복원하지 않는다.

## 다음 확인과 Git 결과

기존 `KRXDaily100NextDayStartupAcceptance0911`에 미배포 main adapter/의존성 차이와 V2.14 예정 상태를 남겼다. 기존 `MachineProfitStagnationStartupAcceptance0911`과 당일 lifecycle/workorder owner가 자연 소비·경제성 및 보류/차단 추천을 유지한다. 완료된 배포를 미래 기동·전수 추천 구현 성공으로 표시하지 않는다. Git remote main과 최종 미커밋 상태는 병합 후 receipt로 확인한다.

최종 검증: 9/11 날짜 기준 parser30행/현재 checklist14개·ID 중복0, compile/diff PASS, 알려진 비밀정보 패턴 검출0, JSON/CSV 유효. 날짜 변경으로9/10의 과거6개 OPEN이 현재-day parser에서 제외된 것이며 작업 완료로 재분류한 것이 아니다. 진행표에서 참조하던9/8 frozen ledger2개가 Git에서 누락돼 원본 hash 그대로 함께 보존했다. 현재 원장67행과 합산하지 않았다. 검토한 미커밋 코드·문서 정합성 범위의 미해결 finding0; 생성 보고서 전 계산 재현이나 다음날 실주문 검증을 뜻하지 않는다.
