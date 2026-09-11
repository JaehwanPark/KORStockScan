# BBO/master 연결·전 SCALPING V2.14·공통 배포 통합

## 승인 범위와 현재 단계

9/11 사용자 지시 `BBO·master 연결 결함보완 / 배포본·작업본 형상 통일 / 모든 SCALPING에 V2.14 / 코드리뷰 반복`과 후속 `독립 매매기계까지 모두`를 실행한다. 대상은 메인·공통 장후와 현재 위젯·삼성·저가주 코드 세대 통합이다. V2.14는 SCALPING Entry 판단에 적용하고 Holding/Exit·entry-price의 별도 역할/schema는 유지한다. 별도 AI가 없는 위젯·에피소드에 Entry AI를 신설하지 않는다.

검토 코드는 별도 `fix/scalping-unification-20260911` worktree에 통합했다. 아래는 코드 검증이며 마지막 배포 receipt 전에는 현재 PID 반영으로 보지 않는다. 기존 RuntimeEnvIntradayObserve0911이 선택본·PID·자연 호출 확인을 소유한다.

## 확인한 결함과 보완

- 선택본 c15a02cb에 있는 탐색 1주의 residual/scale-in/복원 제한이 작업본에 빠져 있었다. e2388dbb 수리를 보존해 통합했다. 기존 hard-stop 수동관리 정상 분류와 현금/신규 allocation 부족의 정확한 drought 분모 제외도 함께 보존했다.
- 삼성 오전 acf139cd의 prearm 시각 수리를 포함했다. 위젯 a2e14f5d의 미제출 보조청산 복구, owner-scope 수리, 현재 저가주 승인 profile, b49e7ecb fill-notification 순서·재기동 상태 검증은 작업본의 기존 검토 코드와 대사했다. 9/11 한정 신규 1주 계약과 기존 보유의 주문·수량은 그대로 유지한다.
- V2.14가 SCANNER/KRX에만 선택돼 SCALP_BASE가 V2.13으로 남았다. 기존 Entry owner 앞에 검토 commit·해시로 pin하는 명시적 operator rollout을 추가했다. 활성 SCALPING Entry의 tag 전체와 KRX/NXT/전장 세션을 지원한다. 같은 글로벌 accepted-order 원장의 일일100회와 1주·residual 금지·scale-in 금지·입력/계좌/주문/가격/수량/cooldown/latency guard를 유지하며 세션별100회로 곱하지 않는다. 기존 과거 후보·정책 hash는 바꾸지 않는다.
- `shared` Entry 호출도 승인 rollout에서 WATCHING의 V2.14 schema/composer로 전달한다. Holding과 sim 표식 호출은 이 신규 확대에서 제외한다. 실행 경로의 SCANNER 제한과 lifecycle의 KRX/aftermarket 한정 귀속도 승인 scope에 한해 연결했다. 캐시는 정책 hash 외 날짜·venue·session·tag를 분리한다. 잘못된 pin·실행 계약은 직접 fallback 사유를 보존한다.
- rollout은 철회 전까지 지속하고 매 기동에서 기존 operator env로 다시 읽는다. 장기 supervisor의 잔존 pin은 시작 전에 지워 명시적 철회가 무시되지 않도록 했다. 다음 거래일에도 기존 exact-date 런타임 검증은 필요하지만 이 동일 rollout의 매일 새 승인·경제성 floor를 요구하지 않는다.
- 외부 census의 첫 BBO 요청이 공통 read-budget 대기1.25초에 밀린 뒤 다음5분 capture가300초 validity를 넘었다. 기존 요청 한 번의 admission 대기를5초로 하고 batch240초 이후 새 요청을 차단한다. max_retries1/일일4800/실행40/시작간격0.25초/source-only4/5 예약은 유지한다. source-only의 quota·호출량을 늘리는 수리가 아니다. invalid/crossed 응답이나 만료 뒤 관측을 정상 join으로 바꾸지 않는다.
- master의 미확인9종목은 EN/EF/FS 등 보통주 대상 밖이었다. 최초 검사에서 ETN7개를 원본 부재로 본 것은 Q 접두사를 놓친 결과였다. 공식 원본 archive/member/raw source hash·유효일을 검증하고 EN에 한해서 Q+6자리 식별자를 연결한다. 원본 식별자·group·우선주 필드를 남기며 `verified_non_common_stock`으로 분리한다. 보통주 경제성으로 승격하거나 이름으로 추정하지 않는다. 실제 미확인/손상 원천은 계속 gap이다.

## 검토·검증

- Entry·AI schema/trace·정책·재검사·lifecycle·split/scale-in: 1483 PASS.
- 신규 pin/전체 scope/실제 recheck guard/global counter 유지와 master/BBO/report 분모: 별도 회귀 검증. source 묶음121 PASS, 통합 AI/관측195 PASS(중복 포함; 총계 합산하지 않음).
- 독립 기계/보조청산/owner/profile/알림/관측/문서 자동화: 913 PASS 후 격리 worktree에 없는 과거 고정 입력2개를 읽기 전용으로 복사해 해당2개 재검증 PASS. 시험용 입력은 실전 재발행이 아니다.
- release router·machine pin 계약60 PASS. 관련 Python compile, shell `bash -n`, `git diff --check` 검증. 문서 parser는 최종 기록 후 실행한다.
- Kiwoom 공식 upstream HEAD는12시대 재조회한 `234560d213acd8871ae344b5481aecd2f30287fa`. `kiwoom/_data/kiwoom_api_spec.json`, `kiwoom/core/client.py`, `kiwoom/specs.py`, Postman의 ka10004 POST `/api/dostk/mrkcond`, stk_cd의 KRX/NXT suffix와 real/mock 분리를 확인했다. 해당 tree에 kiwoom_docs는 없었다. 관측 해석이 불명확한 필드/FID는 변경하지 않았다. 증거는 workspace `tmp/scalping-unification-20260911/official/`.

## 기대효과와 남은 검증

SCALP_BASE 등 유효한 SCALPING 입력도 같은 V2.14 판단을 받고 기존 bounded probe 경로에 도달하게 한다. 이는 무조건 매수나 수익 보장이 아니다. 데이터 수리는 실제 비보통주와 결손을 구분하고 기회 유효기간 내 BBO 확보 가능성을 높인다. 과거 누락 호가·순이익을 복원했다고 주장하지 않는다.

배포 후 실제 PID/code/env, 전 SCALPING resolver와 자연 Provider trace·submit/체결·비용 후 수익은 따로 확인한다. 미래 세션 자연 호출은 현재 KRX 호출 성공으로 대신하지 않는다. 공통 코드가 같아도 main/widget/episode의 정책·custody·broker 주문 owner는 독립이다.

## 최종 코드 재검토 (12:52 KST)

새 tag 재검사는 당일 실제 V2.14 결정의 승인 SHA·scope·runtime-effect가 현재 pin과 일치할 때만 허용한다. 발견/재검사와 수동 분석의 Entry/Holding 역할도 대사했다. 승인 publisher는 기존 파일 덮어쓰기를 원자적으로 거절한다. 검증된 비보통주는 census에 보존하되 BBO quota를 예약하지 않는다. 최종 권한 회귀1126 PASS, pin/publisher48 PASS, 마지막 BBO/master75 PASS. 검토 범위 미해결 finding0이며 실배포·자연 경제성은 아래 실행 receipt로 별도 판정한다.

## 실제 consumer 추가 발견과 최종 배포 (13:09 KST)

첫 배포 뒤 새로 나타난 액스비스0011A0는 공식 KOSDAQ ST/보통주0 원본이 있었지만 숫자6자리 parser와 숫자만 남기는 normalizer 때문에 누락됐다. ASCII 영숫자6자리 identity를 source→resolver→BBO route에 보존했다. 새 원천은 `symbol_code_contract=krx_ascii_alphanumeric6_v1`을 명시하고, 과거 계약은 원래 숫자 전용 파생 검증을 유지해 기존 source hash/고정 보고서를 무효화하지 않는다. 관련 consumer 전체945 tests PASS, 신규 exact owner/resolver·malformed code·legacy 대비 회귀103 PASS. 보완 범위 finding0.

- 최종 workspace/main과 공통·독립 배포 코드: **57a90bd9a19aa6baac5e78624eb9f0a27168b57a**, root `/home/ubuntu/KORStockScan-runtime-releases/unified-scalping-r2-20260911`. source clean. 이전 fe6415dc/첫 통합 PID348715는 중간 receipt로 보존한다.
- main graceful restart: **363990**, 당일 verify PASS, pid_mismatches/pid_missing 각0. 현재 PID의 rollout SHA `14d30e97aa9b320d216419390d812ff174107e3f9e64a68a69639a0ec3301a2f`, 글로벌 MAX_DAILY_RECHECK/MAX_DAILY_BUY_RECOVERY 각100. 이 source-only 추가 수리에서 V2.14 승인·quota 원장은 변경하지 않았다.
- 서비스17개 `zz-unified-runtime.conf`로 같은 root/정책 파일을 연결했다. 현재 가동7개는 widget364143, notifier364154, 삼성collector364162, 두산364171, 한화364179, symbol364251, research364414로 확인했다. 위젯 startup 기대 env10개 일치/PASS, 기존 보조청산·entry-adverse·target-ratchet policy 바이트 hash 유지. 과거 manifest는 `unified_runtime_successor_manifest`와 현재 unit override로 연결하고 이전 receipt 시각/PID는 보존했다.
- 기존 예약9개 공통 cron routing PASS. 삼성/저가주 미래 service와 preflight,20:10/21:15 분석은 설치 경로 검증이며 조기 실행하지 않았다. 다음 자연 기동은 기존 checklist owner에서 확인한다.
- 재기동 전후 broker12:52/12:57 및13:06/13:08 KRX·NXT 보유 삼성25·흥구석유1·우리기술1·ICTK1, 미체결0으로 동일. 다른 owner 수량을 흡수하거나 수동관리 ICTK를 자동 매도로 복귀시키지 않았다. notifier cursor773 보존.
- 첫 통합 후12:57~12:59 실제 OpenAI Entry trace의 V2.14·새 승인 SHA·parse PASS를 확인했다. Holding은 holding_score_v2, entry-price는 기존 별도 Bedrock 역할이다. 두 번째 배포는 master source-only 수리이며 다음 자연 Entry 및 NXT/전장 호출·경제성까지 완료로 확대하지 않는다.
- 12:55 자연 census는 BBO captured28/invalid8, 검증된 비보통주4는 미요청으로 보존했다. 조회 cap·retry 증가 없이 새 코드가 소비됐으며 2개 panel의 ka10027 shared-budget defer는 그대로 결손이다.
- 오늘13:06 새 공식 master를 기존 producer로 수집, 검토 resolver로 보통주2604/0011A0 VERIFIED를 확인했다. 원본은 `data/policy/micro_reversion/repair-20260911/`, 오늘 canonical master에 최초 발행했다. 기존9/10 원본과 비용·Provider 계약은 보존했다.13:08:40 영향 census report 재검증·native write_report publish 결과 primary master verified315 episode/비보통주18 episode/**missing0**. unique 비보통주9종목이며 episode 수와 혼합하지 않는다.
- 잔여: 과거 BBO 미획득·capture cadence·미성숙/right-censored로 경제성 floor는 미충족이다. 코드·master 연결 완료를 scanner recall 정상 또는 순이익 개선으로 보고하지 않는다. 기존 RuntimeEnvIntradayObserve0911과 machine startup/economic owner를 OPEN 유지한다.

선택 원장·현재 기계 경로 owner는 `data/runtime/unified_runtime_deployment.json`; 검증/이전 selector·unit 원문·정책 env·원장 snapshot·tests는 `tmp/scalping-unification-20260911/`에 보존한다. rollback은 이전 검토 root와 기존 주문 terminal 대사를 따르며 quota/custody 초기화나 과거 원천 재라벨링을 하지 않는다.

## 종료 대사 (13:12 KST)

현재 PID363990 환경에서24개 scope/tag 모두 V2.14·100회 선택을 재검증했다.13:11 자연 Entry1건은 V2.14 prompt가 지정됐지만 input preflight 차단으로 Provider 미호출이며 정상 판단 완료로 세지 않는다. 이전 첫 통합의 실제 Provider 성공과 구분한다.13:11:34 micro observer는 healthy_observer_canary/0B14425·0D18527 callback으로 새 PID 원천 유입을 확인했다.13:10 TYM·롯데케미칼 정오 preflight는 R2 root에서 Result=success/exit0이며 향후 실제 매매 기동·체결 성공은 별개다.

최종 영향 census의 primary master missing0, 남은3개 blocker는 capture cadence/BBO coverage/right-censored다. 문서 print-only parser와 git diff --check PASS. 최종 소스 commit과 작업본/선택본 src·deploy·restart.sh 차이는0이며 종료 기록의 문서 변경은 실행 코드 변경과 분리한다.

후속 상태: `15:32` sell-timeout race/custody projection 수리 release가 이 배포를 승계했다. 현재 root·commit·PID는 [후속 배포 영수증](2026-09-11-sell-timeout-race-custody-projection-review.md)과 runtime selector를 사용하며, 위 `57a90bd9`/PID `363990`은 당시 완료 기록이다.
