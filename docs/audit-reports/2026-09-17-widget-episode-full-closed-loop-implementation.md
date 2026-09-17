# Widget/episode 전체 폐루프 구현·검증 — 2026-09-17

## 1. 지시·경계와 현재 판정

사용자 승인: 구현 → 코드리뷰·수정보완 반복 → commit/push → 배포·기동. [계획](../proposals/widget-episode-full-closed-loop-and-scale-performance-implementation-plan-2026-09-17.md)을 참고자료로 사용했다. Source 구현과 실제 release/PID 적용, 자연 신규 정책 소비, 실제 비용차감 수익 개선을 분리한다. 분리 worktree `fix/widget-episode-closed-loop-20260917`에서 최신 profile-checkpoint 및 market-read/fork safety를 통합했다. 운영 원천·env·주문·소유권 자료는 테스트로 변경하지 않았다.

현재 source gate를 통과했고 1차 commit/push·배포·관련 4개 서비스 기동을 완료했다. 추가 리뷰의 episode summary 소비 경계·계산 병목 및 최신 feature-index 보완도 최종 release로 배포·기동했다. 오늘 20:10 evaluation/21:15 final-refresh 자연 실행은 아직 예정 전이다. 신규 seed는 등록 이후 widget10+16/episode30+16 고정 qualified 거래일이 필요하며, 기존 시계열이나 실체결을 전향적 검증으로 대체하지 않는다. 신규 선택/다음 날짜 실제 소비/경제성은 이 코드 배포만으로 완료가 아니다.

## 2. 코드 연결과 source 검증

| 범위 | 구현과 소비 경계 |
| --- | --- |
| C0/C1 | Census의 causal native source만 admission. 전체 종목·lane disposition/census 대사, compact daily bitmask catalog. Forward outcome으로 admission 금지; synthetic benchmark source는 publisher가 거절 |
| C2/P1/P2 | 기존 WS dashboard의 KRX0B/0D native clock/epoch/sequence를 공통 fact writer가 수집. 여러 seed가 한 fact를 참조하며 추가 REG/TR 없음. Native identity 충돌은 해당 symbol/day source-gap으로 봉인. 수집 용량·raw-only·active seed·defer를 별도 receipt로 기록 |
| C3 | Immutable candidate parameter/source/cost/parent/calendar. Widget10 calibration+16 holdout, episode30+16을 등록 뒤 고정. 수정은 명시적 source/cost 또는 parent supersession. Full-depth CF 및 same-day epoch/TTL/partial/censored 구분; 실제 broker fill과 분리 |
| C4 | 별도 postclose source acquisition이 기존 cached-token adapter로 cash/양시장 inventory/unfilled를 취득. 주문/auth refresh 없음. Native fee·quantity·stage·owner·cash/reservation 불확정은 joint promotion 차단. 고정 cohort는 holdout 전에 동결하고, 뒤늦은 신규 admission은 새 cohort로 기존 관측창을 이동하지 않음. 수동/미등록 보유 custody 제외 |
| C5 | Widget/episode 기존 publisher가 fixed-window/native CF/joint 근거를 독립 검증. 여러 file의 immutable generation을 fsync한 뒤 pointer-last CAS publication. Exact-date verified incumbent carry; source-gap으로 신규 승격 불가. Owner apply wrapper의 physical managed code root 바인딩 |
| C6 | 실제 widget/episode reader의 PID/cwd/import root와 accepted SHA receipt. 장중 late publication은 기존 custody를 유지하고 published-not-consumed로 구분. Retired episode의 새 BUY만 막고 기존 broker target/cancel/SELL 유지 |
| C7 | Native 주문/decision과 원 entry policy/candidate SHA를 저장. Exact ka10073 unique symbol/date/quantity/average/gross−fee−tax reconciliation만 실제 net economics로 집계. Missing cost/partial/unresolved는 null. 동일 원 체결의 exact 비용은 재시도에서 보존하고 수정 체결에 재사용 금지. Mature 원 candidate cumulative/holdout 악화 때 auto profile entry retirement |
| C8/P5 | 기존 final-refresh에 source acquisition→completed-study refresh 추가. Grid 재생 없이 source→joint→두 publisher fixed point. Dependency/code/native fact generation 변경과 중단은 이전 PASS 무효화. Tower→checklist→strict require-summary-handoff에서 dated closure receipt 필수. 같은 검증된 완료 generation의 재시도는 grid0/provider0 |
| P3/P4/P6 | Widget 전체1,536 grid/caps1–5를 유지한 day/feature/setup/exit 재사용, 새 day만 replay. Episode는 동일 custody prefix에서 각 window 끝에 snapshot 봉인. 공통 economics 정규화/집계. Source symbol 순차 처리, 32MiB fact/index cache, optional cache 합계2GiB·free reserve10GiB. 필수 raw는 SHA 검증된 lossless block archive로 봉인 후 원 JSONL과 byte-equivalent 유지 |

신규 파일은 monitoring/automation/tests의 기존 역할 경계에 배치했다. Engine-root Python allowlist에 예외를 추가하지 않았다. Main cash/inventory hot-path export는 제거하여 장중 main engine을 변경할 필요가 없도록 별도 source owner를 사용한다.

## 3. 반복 리뷰·회귀

- 무실체결 신규 stock000009: causal freeze → 실제 prospective calendar만큼 fixture clock 진행 → native CF books/실행·수익 summary 독립 검증 → joint cash/owner/source 확인 → 다음 거래일 widget1종목 publication → native reader resolve 성공. 실제 주문0, CF/합성 fixture이며 운영 수익 증거가 아니다. Forged positive summary는 native episodes 재집계와 다르면 거절한다.
- Episode original two legs의 completed CF, 공유 stress depth 부족, HELD/partial/censored 차단을 검증한다. Existing prior HELD target policy 보존 회귀를 retired profile에도 적용한다. Native event prefix 재시도/중복은 한 decision으로 대사하며 변화 없는 prefix의 as-of를 덮지 않는다.
- Missing fee zero 대체, raw book identity 충돌, symlink/partial multi-file publication, cohort pruning without supersession, source/parent correction, late consume, stale source/code receipt 재사용을 검토·수정했다.
- Exact 비용 회수 회귀에서 broker matched-exact가 widget net 필드에 반영되지 않던 결함을 발견해 수정했다. Original fill 변화 시 이전 비용 매칭을 폐기한다. Retired entry marker가 HELD custody의 blocked reason을 덮지 않도록 supplemental fix했다.
- 최종 통합 pytest/compile/Ruff/bash-n/diff/print-only parser 결과는 아래 확정 receipt로 추가한다. 반복 실행 pass 수를 합산해 서로 다른 테스트 수로 주장하지 않는다.

## 4. 성능과 남은 자연 acceptance

CPUQuota20%(one-core fraction), MemoryMax512MiB의 isolated engineering systemd unit에서 전체 grid/caps·remote0·cold/warm digest parity를 측정한다. N100D120 무신호 fixture: cold3,190.293초/CPU437.331초/RSS141,620KiB, warm736.396초/CPU147.148초. N19D72 신호 발생 fixture: cold955.556초, warm514.818초, append534.552초, RSS161,988KiB. Append cache miss29,184=19×1,536으로 신규 day만 replay했다. Wall은 quota throttling을 포함한다. 변경된 economics 집계 아래 N100D120 신호 발생 fixture와 full matrix는 진행 중이며 실측/미달/defer를 숨기지 않는다. Warm day-cache 집계와 completed-study phase reuse는 다른 경로다.

필수 evidence는 삭제하지 않는다. Lossless sealed fact 압축을 full reconstructed byte SHA로 확인한 후에만 동일 원천 JSONL을 archive로 치환한다. Optional cache가 reserve/cap을 넘으면 신규 write를 생략하고 재계산하며 원천/정책/receipt는 남긴다. Deadline 초과는 DEFERRED 및 전체 requested scope backlog이며 grid/표본 축소나 완료 PASS가 아니다.

Natural owner는 오늘 checklist `KiwoomCommonHealthOpportunityCostAcceptance0917`(U10A/B·U11), `WidgetPostcloseEvaluationPinAcceptance0916`이다. 둘 다 OPEN을 유지한다. Exact-date final sources/두 publication→tower/checklist/strict/controller, 실제 next-date owner/consumer ack와 original-version mature economics가 closure test다. 종목 수·승률 자체를 수익 개선으로 주장하지 않는다.

## 5. 공식 protocol reference와 배포 receipt

Official Kiwoom repository commit `953e5dbff123f437ab4d11a78a95191a685eb51f`를 2026-09-17 KST에 취득·검토했다. Relevant `kiwoom_api_spec.json`의 kt00001/kt00005/kt00011/ka10075/ka10073, `kiwoom/specs.py`, `kiwoom/core/client.py`, PRD/MOCK Postman을 cross-check했다. Upstream `kiwoom_docs`는 해당 revision에 없음을 기록한다. 100% cash native field는 min_ord_alow_amt/min_ord_alowq이며 기존 adapter의 cash_only_orderable_amount/qty를 소비한다. Read source만 추가했고 order/auth/REG/continuation protocol을 재구현하지 않았다. 실행 중 user floor/virtual override를 원 cash로 사용하지 않는다.

배포는 closed review gate 뒤 physical immutable release와 기존 shared data/docs/logs/tmp/venv를 사용한다. 모든 관련 scheduled producer/publisher/owner-apply와 실제 watch/widget/episode reader의 code generation을 맞추고 이전 drop-in/selector를 rollback 자료로 보존한다. Main PID retained 여부와 실제 관련 consumer PID는 최종 receipt에서 구분한다. 아직 manual production 연구 재생성, 주문 또는 새 provider/REG 호출을 수행하지 않았다.

## 6. Source 최종 gate

최종 stable-source 통합15 suite **990 PASS / 66.49초**. 이후 최신 upstream의 bounded calibration-retention 및 collector-read receipt를 통합하고 episode prospective/helper·expanded·closure·wrapper·tower/strict/handoff **530 PASS / 60.73초**로 재검증했다. Python 변경30파일 compile 및 Ruff F/E9 PASS, 두 owning wrapper bash-n PASS, git diff-check PASS. Print-only backlog parser32항목, 두 기존 acceptance stable ID 각각 current owner1개. External Project/Calendar sync와 production expensive report regeneration은 실행하지 않았다. 검토된 source 범위 finding0.

추가 리뷰에서 완료 receipt의 strict/tower 소비가 단순 self-hash만 확인하던 연결을 current dependency/code/source-generation 검증으로 보완했다. 현재 실제 PID, dated policy 또는 신규 economics가 source gate에 의해 자동 PASS로 승격되지 않는다. Shared indexed fact의 필요한 row도 immutable bounded decode cache를 공유해 K4 reader 반복 decode0을 검증했다. 완료 fixed-point retry가 native outcome/cost producer를 다시 호출하지 않는 회귀도 통과했다.

[격리한 scale 실측 snapshot](2026-09-17-widget-episode-scale-validation.json)은 engineering source이며 publisher 입력이 아니다. 신호 발생 N19D120 cold1,565.342초/CPU302.455초/RSS195,232KiB; N100 요청의 나머지는 측정 중이다. N100 cold와 전체 N19/50/100×D72/120 성능을 달성했다고 주장하지 않는다. 5,400초 phase deadline 초과 시 DEFERRED/backlog 계약을 유지한다. Completed-study 재시도0 replay와 원 데이터 의미 parity는 검증했으며 운영 whole-stage 성능/자연 handoff·next-date 신종목/경제성은 OPEN이다.


## 7. 이어서 실행한 보완 리뷰·성능 검증

Episode 발행/reader가 보고서의 요약값을 신뢰하던 경계를 보완했다. Selected/baseline의 calibration·반기2·holdout·full을 각 구간 끝에 봉인한 원 episode로 독립 재집계한다. 원 가격/tick/target/round-trip 비용·원 두 leg·date/identity·COMPLETE/NO_FILL과 HELD custody 경계를 확인하고 기존 표본/EV/carry/paired 개선 조건을 동일 helper로 재검증한다. HELD의 후일 mark를 앞선 구간에 소급하지 않는다. Forged EV·반기 표본·paired uplift·baseline·중복·가격·비용을 거절한다. Native episode fixture 46일/원 두 leg CF92건→신규 종목 next-date 발행→reader resolve를 검증했고, self-consistent source/publication도 잘못된 summary는 reader에서 거절한다. 이 episode 테스트의 joint gate는 별도 경계로 격리했으며 실제 cash/joint positive E2E는 위 widget 회귀가 담당한다. 주문0·운영 수익 증거 아님.

Profile에서 반복 cap 경제성 집계를 확인해 한 episode의 시각/가격/손익을 한 번 해석하고 cap별 원 순서로 합산한다. Missing/invalid는 해당 episode를 포함하는 cap에만 null/censored를 유지한다. Cap 추가 episode가 없으면 동일 native sum을 독립 dict로 복제한다. Symbol-local 시간대/minimum-history index를 재사용하고 등록 policy page의 불필요한 hash 계산을 제거했다. Setup/exit/cooldown·전체1,536 grid/caps1–5·원 floating sum/tie·cost는 그대로다. CLI가 `--modes`/`--compute-budget-sec`를 runner에 전달하지 않던 측정 도구 결함도 수정했다.

동일 quota20%/512MiB의 신호 발생 N1D120 cold 비교: 보완 전 wall86.468초/CPU15.977초/RSS191,924KiB; cap 집계 통합만 적용 wall77.513초/CPU14.204초; 시간대/index·동일 cap 재사용까지 적용 wall70.831초/CPU12.883초/RSS191,916KiB. CPU19.37%·wall18.08% 감소, 세 결과 canonical digest `f89d72cdf48d95f9cbdcb2af9ede7b40b63d6e0aa23d10edaebe958f38b8ed5e` 동일, remote0. 이는 N1 실측이며 N100 목표5,400초나 whole-stage SLA를 달성했다는 증거가 아니다. 기존 N100 populated 작업과 full matrix는 OPEN; deadline 초과는 DEFERRED/전체 backlog이고 기존 verified 정책을 유지한다.

Stable-source 최종16 suite **1,089 PASS / 89.40초**, 보완 구간3 suite135 PASS. Python compile/Ruff F,E9·두 wrapper bash-n·diff-check PASS. Source review 범위 finding0. Natural seed/next-date 신규 정책 소비·실제 exact-cost economics 및 full-scale SLA는 기존 OPEN owner에 남긴다.

1차 배포: `06321fdb` source→latest main 통합 `cf42b542` push. 14:29 관련4서비스 기동, widget553146/episode553117의 native C6 receipt에서 당일 기존 widget3종목/episode3정책 소비 확인. Watch553239/runtime553143 및 예정 producer/owner-apply7개 code root를 초기 release로 맞췄고 기존 resource/env/소유권/정책/threshold·operator hash6개를 보존했다. 첫 deployment receipt는 `data/runtime/widget_episode_full_closed_loop_deployment_2026-09-17.json`. 이후 독립 upstream 배포가 일부 source pins/main PID를 갱신했으므로 이 초기 receipt를 현재 PID로 재사용하지 않고 후속 배포 직전 최신 상태를 다시 봉인한다. 초기 main501022 유지 사실과 후속 main575313은 서로 다른 as-of다.


## 8. 최종 commit/push·실제 배포·기동

- 보완 source `acac4f27` commit/main push 뒤 병행 O2 feature-index source `e159ff3c`와 최신 remote를 force 없이 병합했다. Latest dependency 3 suite **207 PASS / 42.38초**, 최종 source 동등성을 확인한 main integration **`bf7105f1c70716ca0637e0b0c5864ebead0f9951`** push. 새로운 engine-root 모듈/패키지 설치·변경 없음.
- 최종 physical immutable release: `/home/ubuntu/KORStockScan-runtime-releases/widget-episode-closed-loop-r3-20260917`, HEAD bf7105f1. Physical src/deploy tracked clean, data/docs/logs/tmp/venv만 기존 workspace shared 경로. Physical/shared 7 suite **343 PASS / 40.09초**. 당일 예정 evaluation/final-refresh/owner-apply 및 실제 widget/episode/watch/runtime 7개 WorkingDirectory·ExecStart와 필요한 ExecCondition을 동일 root로 검증했다. 기존 실행 인자·EnvironmentFiles·CPU/Memory/Nice/User/Group/restart/stop 제한은 그대로다. 병행 producer drop-in 우선순위 때문에 첫 root 검증이 멈췄고 실제 effective 우선순위를 수정한 뒤 7개 root·보호 설정을 재검증했다. 실패 검증으로 기동/selector PASS를 대신하지 않았다.
- 2026-09-17 **14:58 최종 기동**: widget **609186**, episode **609158**, watch **609286**, runtime collector **609182**. 전부 active/running·NRestarts0·실제 cwd/import root 일치·startup ExecMainStatus0. 예정3개는 inactive/MainPID0·not_yet_due. Main **575313**의 실제 cwd를 유지했고 이 배포가 main의 새 코드 소비를 증명한다고 표시하지 않는다.
- C6 당일 native receipt: `consumers/widget_2026-09-17_609186.json` / `episode_2026-09-17_609158.json`, status consumed, 기존 widget3종목(005930/034020/042660)/episode3정책(028670_midday/034020_midday/111770_late_morning)와 source policy SHA 확인. **기존 v1 소비이며 신규 v2 폐루프 선정/경제성 proof가 아니다.** 당일 정책·owner registry/custody·threshold env·operator override hash6개 동일, manual 주문 호출0.
- Durable current receipt: `data/runtime/widget_episode_closed_loop_r3_deployment_2026-09-17.json`. Rollback: `tmp/systemd_widget_episode_closed_loop_r3_20260917_145815`의 effective-before/기존 selector 및 1차 immutable release 보존. Runtime router postclose print-plan은 최종 root로 결속한다. Workspace tracked/untracked foreign 변경은 별도 stash 백업 후 병합·복원했고, 문서 충돌은 신규 source 보완과 원 owner의 추가 evidence를 함께 보존했다. 외부 Project/Calendar sync, 비싼 production 보고서 재생성, 수동 정책/threshold/owner 적용은 하지 않았다.

판정: 구현·반복 리뷰 보완·대상 validation·commit/push·관련 서비스 배포/기동 완료. 최종 검토 범위 source finding0. 두 기존 checklist OPEN owner와 일정은 유지한다. 오늘 자연 장후 generation→두 publication→tower/checklist/strict/controller/finalization은 예정 전이다. 등록 이후 widget10+16/episode30+16 qualified 거래일·next-date native owner activation/실제 신규 소비·원 버전 exact-cost net profit는 WAITING이다. N100 populated/full scale SLA는 OPEN이며 N1 개선을 전체 시간 목표 달성으로 확대하지 않는다.


## 9. 15:03 후속 통합 배포 이후 현재 consumer 재검증

병행 owner가 최신 async/sizing·execution-critical tick metadata 보완을 통합 배포했다. 최종 문서 remote 보존 merge `c8ea749d`와 현재 selected/physical **`03ddbd2d6bf0b1c77073bb80c867d5cda695c6d7`** (`opportunity-async-sizing-20260917`)의 src/deploy diff0을 확인했다. 이번 episode summary·cap/시간대 집계와 feature-index 소스가 모두 포함된다. 추가 upstream 영향8 suite **693 PASS / 19.88초**. 이전 bf7105f1 기동/575313 유지 receipt는 14:58 역사 상태로 보존하며 현재 PID로 재사용하지 않는다.

현재7개 code root는 통합 physical release로 일치한다. Main **616502** actual PID receipt/실제 cwd `.../opportunity-async-sizing-20260917/src`를 확인했다. Widget **615120**, episode **615208**, watch **615423**, runtime **615580**, active·NRestarts0. Native C6 status consumed·cwd/import root와 당일 기존 widget3/episode3 acceptance 확인. 기존 원 policy/owner/custody/threshold/operator hash6개가 14:58 원 snapshot과 동일하다. 실제 재검증 receipt: `data/runtime/widget_episode_post_integration_validation_2026-09-17.json`. 이 검증은 후속 owner의 배포를 확인한 것이며 별도 수동 주문/정책 변경을 실행한 것이 아니다.

현재 판정도 code/deploy/PID 소비와 신규 정책 자연 선정·경제성을 분리한다. 신규 v2 정책·mature net profit·N100 full-scale 목표 OPEN, 당일 20:10/21:15 장후 자연 실행은 아직 예정 전이다. 외부 문서 sync는 실행하지 않았다.
