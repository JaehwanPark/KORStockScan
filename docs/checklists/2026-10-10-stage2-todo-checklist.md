# 2026-10-10 Stage2 To-Do Checklist

## 오늘 목적

- Main PASS 인수·제출·재점검 연결과 진단 지연을 반복 검증하고 승인된 배포 및 다음 영업일 기동 준비를 완료한다.
- Pre-submit delay 상황별 초기정책과 장후 재생성 상세 계획을 수립·검증한다.
- 후속 승인된 두 계획의 전체 범위 trailing/replay와 제출 지연 v2를 구현·리뷰·검증한다.

## 오늘 강제 규칙

- Main PASS 보완은 후속 사용자 지시로 리뷰 후 배포와 다음 영업일 기동 점검이 승인됐다. 동일 정책의 코드 결속·격리 PREOPEN 준비를 정식 경로로 갱신하며, 그 범위에서 정책 재선정·AI 연구·장후 원장 재생성은 실행하지 않는다. Pre-submit delay 후속 요청은 초기정책·장후 재생성의 계획 수립이며 이번 문서 작업에서 이를 실행하지 않는다. 실제 Main 기동은 다음 영업일 예약이 소유한다.
- 원 요청·native claim·deadline·정책 identity 및 주문·수량·자금·freshness·Main/manual 소유권 guard를 보존한다. 퇴역 episode/widget 실행을 복원하지 않는다.
- 진단 저장 결손은 미확정으로 보고하며 주문 재전송이나 broker 거절로 합성하지 않는다. 기존 10/9 기록과 봉인된 10/12 checklist를 보존한다.
- Project/Calendar 동기화는 사용자가 표준 명령으로 수행한다.
- 최신 사용자 지시로 두 상세계획 작업본의 반복 코드 리뷰 후 배포와 다음 영업일 기동 점검이 승인됐다. 검증한 공통 runtime·부모 동등 초기 구성의 코드 배포와 S6 신규 v2 정책 발행·장후 재생성 수용을 구분한다. 잔여 전수 연구·상한 초과 분할·전체 workload 검증은 아래 두 owner에 유지하며 기존 봉인된 준비 bytes를 덮어쓰지 않고 새 릴리스 준비를 별도 생성한다.

## 실행 항목

- [ ] `[MainAllScopeTrailingReplay] Main 전체 종목·시장 trailing 및 replay 구현·반복 리뷰` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [전체 범위 구현계획 AT0–AT7](../proposals/main-all-symbol-all-market-trailing-and-replay-improvement-plan-2026-10-10.md).
  - 수용: 누적 입력창 비용/projection 세대, 공통 scope와 실제/CF 분리, runtime/replay 공통 판단, causal situation pin·부모 계승, 격리 초기 생성·consumer migration·합산 예산을 구현하고 영향 회귀·성능 비교·재리뷰로 닫는다. 원천 미관측·경제 적격·자연 소비를 코드 완료와 분리한다.
  - 구현 근거: [공통 구현·반복 리뷰](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md). 누적 과거 비용 무효화, 전체 scope/공통 재생·ADD/익일 pin 승계, 12-cell 승인 부모 계승, bounded checkpoint/공통 cohort 집계를 구현했다. 변경 없는 원천의 cost-only 정정은 원천 JSON decode 없이 실제 손익을 미확정으로 전환하며 clean recompute와 같다. 계산 부분의 절감은 전체 장중·장후 성능 수용과 구별한다.
  - 후속 보완: 등록된 유한 classifier grid의 train 선택·holdout 고정, 원 AI crossing 입력의 후보별 결속, selector 실제 byte SHA 참조·원 classifier/시장/부모와 one-market canary 결속을 검증했다. source/cost/code를 최종 집계 뒤 다시 검증하며 변경 시 report/policy를 발행하지 않는다.
  - 자원 보완: numeric 후보/부모와 독립인 source-feature spool을 구현했다. 기존 경로를 source hash로 결속한 여러 input segment에서 이어 재생하고, M1 상태·원 quote/AI 입력·ADD를 보존한다. 4MiB 초과 경로의 결과/상태·cached 결과 사용 시 원 leaf byte 검증·손상 feature 재구축을 검사했다. source-feature spool은 64MiB의 별도 저장 상한을 명시하며 이를 무제한 temp 허용으로 사용하지 않는다.
  - 공통 코드 배포: 후속 리뷰 1,079 passed, 불변 릴리스 262 passed. `main-trailing-delay-20261010-v1` / `d61b36b00696865ca9dd13a466d8544a886e2e28` 선택과 웹 PID 48969 전환 완료. 부모 동등 12 cell, 기존 기계·보조 원본 보존, 10/12 PREOPEN 전체 계약·finalization·cron 8경로 PASS. [기동 준비](../../data/report/main_trailing_delay_deployment/2026-10-10/final-readiness.json); 자연 Main 기동은 07:55 future_due이며 전체 연구 수용은 OPEN이다.
  - OPEN 잔여: 전수 native/forward/실제 비용 연결 producer와 대사, 적격 실제 유형 후보 선정, source/feature spool 상한을 넘는 job의 전수 분할·재개와 cache eviction/전체 candidate block, 전체 workload 성능 gate. 원천 결손·미구현을 초기 부모 계승의 추가 경제 승인 요건으로 바꾸지 않는다. 신규 경제 정책 발행·전수 연구 수용과 검증된 공통 코드의 승인 배포·PREOPEN/PID 수용을 분리한다.

- [ ] `[PreSubmitDelaySituationImplementation1010] Pre-submit delay v2 초기정책·관측·due 재점검 구현` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [제출 지연 상세계획 S0–S5](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md).
  - 수용: 원 PASS 관측·두 anchor·shared split/purge·cell/fallback·committed generation·준비된 lookup·현재 scheduler successor·단일 decode/증분 감시를 연결한다. v1 의미·원 deadline·주문 guard와 Main/manual 경계를 보존하고 격리 재생·반복 리뷰·단독/결합 성능을 검증한다. S6 운영 발행과 실제 PID 수용은 후속 실행으로 분리한다.
  - 구현 근거: [격리 계산·반복 리뷰](../audits/main-all-scope-trailing-and-pre-submit-delay-implementation-review-2026-10-10.md). 실제 제출 함수의 scanner/fixed-watch × auxiliary v1/v2 경계, 원 발생 시각·queue 접수/append 구별, v2 durable generation/CAS·warm lookup을 검증했다. 실자료 commit 31/PASS 진단 29/P0 6/가격쌍 21, 정책 부모 해시 결손 29건이므로 격리 초기값 0초·양수 cell 0; 동일 세대 재계산 source JSON decode 0. 계산 부분 절감은 운영 성능 증거가 아니다.
  - 자원 보완: v2 원천은 원 record identity를 검증한 뒤 필요한 필드와 full-field conflict SHA만 보관한다. 최대 2GiB의 명시적 scan-job 상한과 64KiB record buffer, 같은 공유 resident-data budget의 동적 admission을 적용한다. legacy의 전체 decode를 조용히 무제한으로 바꾸지 않는다. 최소 projection과 원 projection의 qualification/census 동등성을 검증했다.
  - 후속 리뷰·공통 코드 배포: 활성일/enable cache·만료 manifest 제거·관측 snapshot 공유·공통 writer 중복 mkdir를 보완했다. 정상/burst/slow writer의 동일 입력 3회 비교에서 의미 동일·누락 0·비악화 PASS. 위 최종 릴리스에 포함됐으며 신규 v2 운영 정책은 선택하지 않았다. 원 PASS의 부모 결손을 실제 가격쌍이나 실현손익으로 대체하지 않는다.
  - OPEN 잔여: retained index/기회·최종 artifact 상한을 넘는 전수 입력의 분할·재개·global census/split 발행과 전체 due/burst/청산·장후 결합 성능 gate. S6 운영 장후 재생성과 신규 v2 정책 선택은 미실행이다. 후속 승인된 공통 코드 배포는 기존 지연 기본값과 부모 경제값을 유지하며 10/12 준비를 신규 세대로 검증한다.

- [x] `[MainPassSubmitRecheckLatency1010] Main PASS 인수·제출 연결 및 진단 지연 보완·승인 배포` (`Due: 2026-10-10`, `Slot: IMPLEMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [구현계획 S1–S4](../proposals/main-pass-submit-recheck-and-latency-remediation-plan-2026-10-10.md).
  - 수용: take/discard 이후 원 객체 종료·후속 claim 보존, 직접 종료 사유와 전이 identity·PASS 분모 연결, 기존 단일 관측 executor의 유한 접수·원 발생 시각, bounded trace 준비 진척, 실제 제출 함수 내부부터 격리 adapter까지 검증한다. 반복 리뷰·회귀·compile·diff·print-only parser 및 동일 입력 성능 비교를 기록한다.
  - 배포 수용: 재리뷰·회귀 후 불변 릴리스와 web pin을 통합 선택하고 원 10/8 장후 세대·10/12 checklist를 보존한다. 새 릴리스의 동일 정책 code refresh, 10/12 PREOPEN 전체 계약, strict/finalization 세대 및 설치 예약 경로를 확인한다.
  - 자연 수용: 10/12 기존 DirectFamilyPreopenPolicyHandoff에서 실제 PID의 정책 소비와 관측된 PASS→제출 또는 기존 guard 종료를 확인한다. 준비 검증과 자연 기동·체결·경제성을 구분한다.
  - 완료 근거: [반복 리뷰·구현 결과](../audits/main-pass-submit-recheck-latency-implementation-review-2026-10-10.md). 최종 고정 코드 19개 suite 2,424 passed / 139.65초, 기존 Pandas 경고 1건. 동일 부하 3회 비교에서 정상 전달 261.943→185.142ms·동시 전달 60.596→49.021ms; 진단 지연과 필수 저장 지연의 만료 의미를 분리 검증했다. compile·diff·문서 검증 결과는 audit에 기록한다. 구현 수용 완료이며 배포·자연 기동 수용을 뜻하지 않는다.
  - 후속 배포 완료: 재리뷰 2,424 passed / 139.44초, 불변 릴리스 326 passed / 9.25초. `main-pass-submit-20261010-v1` / `b26aae701314d91a75056fac576b5f460beb3c06` 선택, runtime 1,072파일 대사 결손 0, web PID 22143·ubuntu·새 cwd/commit·HTTP 200. 기존 정책 code hash가 일치해 정책 재발행 없이 새 격리 PREOPEN을 생성했다. [최종 기동 준비](../../data/report/main_pass_submit_deployment/2026-10-10/final-readiness.json)는 10/12 `current_full_contract=pass`, finalization issues=[], cron 8개 PASS, 07:35/07:55 예약 정상이며 Main PID 자연 소비는 future_due다.

- [x] `[PreSubmitDelayInitialPolicyPlan1010] Pre-submit delay 상황별 초기정책·장후 재생성 상세 계획` (`Due: 2026-10-10`, `Slot: DOCUMENTATION`, `TimeWindow: 00:00~23:59`, `Track: RuntimeStability`)
  - Source: [상세 개선계획](../proposals/pre-submit-delay-situation-initial-policy-and-postclose-regeneration-plan-2026-10-10.md).
  - 수용: 전체 PASS·두 anchor·원천 복원·시간순 분할·상황별 cell과 0초 fallback, v2 생성/소비·due 재평가, 장후 재생성부터 PREOPEN까지의 owner·순서·유한 종결을 구체화한다. 계획 리뷰·보완·링크·공백·print-only parser를 검증한다.
  - 후속 성능 리뷰: 상세 계획 D10–D16·§4.4/4.5·§6.3·§9·§11에 정책 사전 로딩, snapshot/hash 공유, due/queue 예산·공정성, 장후 단일 decode와 cache 무효화, 증분 감시·재점검 owner 인계 및 성능 실패 시 발행 중단을 명시한다. 문서 수용이며 실측 성능 개선·코드 구현 완료를 뜻하지 않는다.
  - 범위: 문서 계획 완료만 기록한다. 신규 코드 구현·실제 정책 선정/발행·장후 재생성·release 선택·기동·실주문은 미실행이며 기존 10/12 준비 세대는 보존한다. 후속 구현 시 실제 날짜의 실행 owner에 S0–S6와 검증 기준을 연결한다.
