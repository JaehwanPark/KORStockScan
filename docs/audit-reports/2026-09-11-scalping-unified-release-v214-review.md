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
