# Main 약세 장후 원천 연결·누적·후보 수리 구현 리뷰 — 2026-10-14

## 결정과 실행 경계

사용자의 “구현하고 코드리뷰 후 수정보완 반복하여 결함이 없을때까지 실행하라” 지시에 따라 [WR0–WR5 계획](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md)의 작업본 구현·자체 리뷰·보완·재리뷰·표적 검증을 수행했다. 검토한 지원 경로의 미해결 코드 결함은 0이다. 현재 원천의 미지원 축과 자연 수용은 아래에 별도로 남긴다.

원천/일별/누적 producer와 outbox consumer만 변경했다. Main/WS/scanner/AI/order/observer writer의 추가 hook·로깅·metadata·조회·계산·queue/thread/API/provider 호출은 없다. 기존 기계/보조 입력·응답·membership/원 store, 정책·수량·주문·Main/manual custody·퇴역 owner 권한을 변경하지 않았다. 새 Python module은 만들지 않았으며 기존 `automation`/`scalping` owner와 `src/tests` 위치를 사용했다. `$korstockscan-review-gate`와 현행 Plan Rebase/10/14 체크리스트를 적용했다.

착수 selected release는 `/home/ubuntu/KORStockScan-runtime-releases/main-io-postclose-20261013-373d5f10f`였다. 이는 부모 확인이며 수리 파일의 배포/소비 증거가 아니다. 실제 배포·Main 재기동·cron 변경·원 운영 연구 산출물 재생성·provider/Telegram 실발송·정책 발행은 수행하지 않았다. fixture transport/runner와 임시 data root에서만 쓰기/발송 결과를 검증했다.

## 구현과 반복 리뷰에서 닫은 결함

| 경로/발견 | 수리와 검증 근거 |
|---|---|
| gzip-only master/trace가 날짜 발견·선택에서 누락 | 공통 날짜 파싱·plain 우선 logical alias·gzip-only discovery/source_plan/reader/currentness. 실제 canonical master validator의 effective window/owner/hash를 재사용하며 미래 master와 충돌 alias를 배제 |
| 압축본의 prefix 재해제·CRC 미완료 결과 사용 가능성 | 한 연속 stream의 physical/decoded SHA와 EOF/CRC 선행 검증. staging partition→검증 후 shared object 게시. 예산 중단/CRC/깨진 source는 partial staging/index/census를 폐기하고 그 세대는 `compressed_resume_unavailable` 또는 contract gap으로 건너뜀 |
| trace에 없는 assessment.event를 기대해 자연 판정 전체 U | 기존 native payload의 원 body/payload/assessment SHA·date/attempt/PID/start/event/clock/ask를 검증해 trace에 연결. 원 final `source_invalid` action은 유지. typed event/ask/session/route/item/epoch/sequence가 같은 원 label만 연결 |
| 같은 body를 다른 파일 위치에서 만나 false conflict | native body SHA로 중복 판단하고 첫 물리 receipt 보존. 다른 body의 같은 key는 격리. compact SQLite row seal·key 검사로 캐시 변조가 원 native 증거를 대체하지 못함 |
| capture-wide redaction이 정상 event까지 제외 | 실제 Main/probe 원 표본에서 `signal_token`만 redacted이며 원 해시/event/ask가 일치함을 읽기 전용 확인. 필요한 필드를 개별 검증하고 compact projection에서 비필수 token/body를 복제하지 않음. critical redaction은 U/제외 |
| global bundle/날짜가 같은 정책 cohort를 단절 | immutable bundle/family/execution/payload hash와 관련 kernel/label/보조 binding에 결속한 scope key. replay는 별도 replay-kernel SHA도 결속. full bundle은 provenance에 보존하고 실제 정의 변경은 다른 cohort |
| 자연 보조 component와 scope binding SHA의 해석 차이 | 원 요청 input/prompt/schema SHA·원 component·prompt version을 확인한 경우만 binding SHA로 정규화. 원 hash 별도 보존. 증빙 불일치는 후보 selection UNKNOWN이며 실제 보조 결과를 새 입력으로 차용하지 않음 |
| raw 약세를 연속 확인 약세와 혼동 | 2회 활성/3회 recovery·spacing/TTL/policy/day/UNKNOWN 경계의 확인 latch primary. raw 진단·실제 availability/latch receipt·재구성 basis 분리. 중복 관찰로 횟수를 늘리지 않고 같은 활성 episode 유지 |
| daily 완료 뒤 timeout이 후속 작업을 잃음 | phase 부재/이전 generation도 pending으로 발견. daily→cumulative→notification 단계와 완료 후보 통계 checkpoint를 재사용하며 완료 일별 projection을 재생성하지 않음 |
| 복구된 과거를 새로운 전향 증거로 사용 | 후보 고정 당시 이미 보관된 모든 decision 원천 날짜를 cutoff에 포함. 기존 candidate generation/history 보존. cutoff 이후 새 날짜만 안내 안정성 비교에 사용 |
| PASS-only evaluator/문구가 기계 단독에 전파 | kind별 selection/parent/preview/winner_group, 원 역할 증빙이 있는 확인점 tightening 필터, 기계 단독의 보조 미호출 허용. scope당 합계≤6, 기계/보조 별도 winner. K/R/A/N과 공유 U의 불리한 양 끝값을 계산 |
| 추가 영역이 leave-date/episode 차감에서 사라짐 | subtract/merge가 A/N까지 보존하도록 보완. N은 coverage에 남고 선택 승률 분모에는 들어가지 않음. 별도 회귀로 추가만 있는 pair와 leave-cluster Δ 일치 확인 |
| 코드/압축/키 이행이 잘못된 정정·중복 안내를 만듦 | 관련 scope 기반 recommendation 의미 ID와 winner_group, 기존 sent receipt alias 보존. migration/미완료 비교는 outbox를 수정하지 않고 defer. 실제 source 무효화와 미적격 철회 구분; current pointer 변경은 발송 전 보류 |
| 일반 installer 재호출이 notify/설치 이력을 재설정 | notify 미지정은 기존 값 유지, enable/설치일/초기 selected release/source floor 유지, 새 rebind 별도 기록. cron/config 설치 readback 실패 시 원 bytes/소유권 복구와 cron 재조회. fake runner 회귀로 보존/rollback 검증 |
| 최신 defer가 완료 계산 receipt를 가림 | 야간 `latest_attempt`와 `last_completed_computation.json` 분리. 완료 계산을 새 성공으로 전용하지 않음. 기존 야간 9회/60초/총600초/worker1/512MiB·EOD 우선·자식 회수 유지 |

label은 실제 ask·비용률 .0023·1800초·비용 후 +.4%/soft −3% 선도달 W/F/U다. `W/(W+F)`와 미해결 U를 따로 보고 U 민감도를 계산하며 이를 실제 fills/PnL/EV로 표시하지 않는다. 고정 1,000회는 경험적 진단이며 통계적 95% 보장이 아니다.

## 원천 확인과 남은 지원 범위

10/13 기존 payload의 bounded prefix에서 현재 저장 형태의 native Main/probe 표본을 확인했다. outer/payload/assessment SHA, event/clock/ask, immutable scope/family/component 증빙이 일치하고 canonical/typed alias가 존재했다. 숫자 역할 계약은 없는 표본이었다. 같은 날 원 machine-comparison은 부모 bundle이 존재하지만 replay execution SHA가 live family SHA와 달랐으므로 둘을 같다고 가정하지 않고 replay kernel을 별도 결속했다. 이 확인은 전체 날짜의 연결률/성과나 새 자연 예약 성공을 측정한 것이 아니다.

기계 수치 필터는 원 `numeric_axis_contracts`에 `baseline_prior/bounded_tunable`, 원 branch 정의, unit/operator/before가 검증된 축만 지원한다. 현재 확인한 원 정책에는 이 계약이 없어 `role_unverified`다. root/FSM/재무장/새 확인 ask의 완전 재생 producer는 현재 없고 `confirmation_replay_unavailable`다. generic 추가/제외 통계와 typed consumer 지원을 이 producer의 구현 완료 또는 실제 숫자 후보로 주장하지 않는다. 이 결손을 임의 역할/정책 rewrite·새 live writer로 보충하지 않으며 보조 이후 연구는 독립적으로 진행 가능하다.

60초 내 재개 불가 gzip을 끝내지 못하면 해당 세대의 coverage를 포기한다. 미래 관찰/누락 ask/정답/미검증 branch를 합성하지 않는다. 새 자연 자료에서 적격 numeric 후보가 나와야 configured-admin Telegram 안내가 가능하며 정책 자동 적용은 없다.

## 검증과 문서 인계

- 표적 8 suites: 순수 연구, 독립 자동화, notifier, 새 source repair, panic/weakness observer, 퇴역 entry bridge, canonical symbol master, engine location gate. 기존 연구 107개와 새 repair 50개 및 인접 계약 94개를 검증한다. 최종 실행 결과는 **251 passed**.
- 변경 Python 4개 `py_compile`, Ruff, Black 정합, 관련 설치/실행 wrapper 2개 `bash -n`, `git diff --check` 통과. 실제 Kiwoom request/response/FID/auth/account/order/continuation 변경이 없어 protocol 변경 검증과 호출은 수행하지 않았다.
- 새/수정 문서의 로컬 링크·실행 owner·권한 경계를 확인하고 print-only backlog parser를 실행했다. 현행 25개 task 중 `MainMarketWeaknessPostcloseObservation1008` owner는 10/14 체크리스트 1개다. 10/13 원 Acceptance/리뷰 수용/History를 보존해 이전했으며 이전 체크 표시는 자연 완료가 아니다.
- 착수 dirty/untracked 37개의 hash를 기록했다. 이번에 의도적으로 바꾼 두 체크리스트를 제외한 원 dirty 35개는 그대로다. 10/13은 owner 이전 section 밖 bytes가 착수 hash와 같다. 10/14 AUTO는 이번 section 삽입 대상이 아니며 작업 중 별도 생성된 정책/summary 세대 변경을 과거 snapshot으로 되돌리지 않았다. 최종 checklist 바이트의 strict/PREOPEN 영향은 기존 `DirectFamilyPreopenPolicyHandoff`가 소유하고 이번 문서 parser PASS로 완료를 주장하지 않는다.

계획의 [구현 인계 §10](../proposals/main-market-weakness-postclose-source-binding-and-candidate-repair-plan-2026-10-13.md#10-2026-10-14-승인-구현과-수용-인계), [optional 운영 문서](../time-based-operations-runbook.md#main-약세-장후-연구--optional-운영-owner), [현행 체크리스트](../checklists/2026-10-14-stage2-todo-checklist.md)가 후속 owner다. 배포/자기 code rebind 뒤 실제 예약에서 terminal→daily→누적→candidate→notification disposition→attempt/night summary를 확인해야 한다. 현재는 작업본 구현 검증만 닫으며 자연 입력/적격 안내/실제 매매 효과는 미검증이다. Project/Calendar 외부 sync와 broad automation은 수행하지 않았다.

## 후속 코드 재리뷰와 수정보완

사용자의 후속 “코드리뷰후 수정보완” 요청으로 생산자→누적 캐시→알림→재시도 경계를 다시 검토했다. 위 251개 통과는 최초 검증 이력이며 다음 결함을 포괄하지 않았다. 아래 8종을 실패 회귀로 재현하고 수정·재리뷰했다.

| 심각도·결함 | 보완과 재현 검증 |
|---|---|
| P1 미지원 재생 및 필터 모집단의 알림 유입 | 원 FSM/새 ask/정답 producer가 없는 `machine_confirmation_replay_cf`는 selection UNKNOWN·안내 불가. 로컬 `verified=true`만으로 승격하지 않는다. 현재 지원하는 기계/보조 필터는 제외>0·추가=0이어야 하며 추가만 있는 pair의 순수 계산을 후보 지원과 분리한다 |
| P1 재처리 중인 날짜가 비교에서 사라져 오철회 | `pending_source_dates`와 전체 날짜 cursor의 generation/status/code를 누적 비교/manifest에 결속한다. 미완료 날짜가 있으면 outbox를 수정하지 않는다. 새 pending 날짜 생성도 과거 비교의 발송 currentness를 무효화한다 |
| P1 충돌 상태를 누락한 후보 통계 캐시 | 동일 숫자 분모라도 scope conflict가 생기면 새 checkpoint key로 계산한다. 이전 eligible 결과를 재사용하지 않고 `source_gap`, winner=false로 남긴다 |
| P1 보류된 철회가 새 추천·정정과 중복 발송 | 매 reconcile마다 현재 필요한 정정/철회 ID를 결정하고 오래된 prepared/failed 항목을 억제한다. 같은 범위의 새 winner는 대체 안내 하나, source gap은 정정 하나만 fake transport에 전달한다 |
| P1 비교 저장 후 manifest 전 crash가 영구 재개 실패 | 검증된 immutable comparison을 재사용해 manifest→current handoff를 반복 가능하게 한다. manifest 부재는 복구하고 기존 충돌 bytes는 계속 거부한다. 통계 재계산 없이 복구하는 crash 회귀로 검증한다 |
| P1 목적지 저장 실패를 원천 결손으로 오인 | projection/cursor commit 오류를 `projection_commit_failed` defer로 분리한다. plain 원천을 skip하거나 결손 완료로 봉인하지 않고 마지막 durable cursor에서 재시도한다. gzip 중단은 기존 무재개/coverage 포기 계약을 유지한다 |
| P2 event 없는 probe BLOCK을 자연 판정으로 집계 | event 유무와 관계없이 native probe origin을 먼저 보존한다. 정상 event 없는 BLOCK은 count-only/U이며 ask/거래 기회를 만들지 않는다 |
| P2 역할 확인된 축도 일괄 `role_unverified` 표시 | 역할 미확인·완전 재생 미지원·특징 결손·강화 cutpoint 부재를 `role_unverified / confirmation_replay_unavailable / feature_missing / no_tightening_cutpoint`로 구분한다. 후보 manifest와 비교 capability의 사유가 일치한다 |

최종 표적 검증은 동일 8 suites **263 passed**(기존 251개+추가 12개)다. 변경 Python 5개 compile/Ruff, 핵심 구현·repair 회귀 4개 Black 정합, 공백 검사 및 문서 print-only parser가 통과했다. 검토 문서/owner 구간 로컬 링크32개 정상, parser task25개 중 현행 약세 owner1개다. 자동화 회귀의 기존 서식은 최소 수정하고 저장 오류의 새 defer 계약을 확인했으며 최종 변경 부분 6개도 재통과했다. 신규 모듈·장중 호출/기록·기존 보조 연구 입력/응답·매매 정책/권한 변경은 없다.

이번 재리뷰 범위의 미해결 코드 결함은 0이다. 배포·예약 code rebind·원 운영 자료 재계산·실제 Telegram 발송·PID 소비·경제성은 실행하거나 입증하지 않았다. 최신 작업본 hash를 선택 release와 재결속하기 전까지 위 테스트 결과를 실운영 적용으로 해석하지 않는다. 후속 owner는 동일 `MainMarketWeaknessPostcloseObservation1008`이며 AUTO 봉인과 다른 OPEN 작업을 재작성하지 않는다.

## 후속 배포 승인 실행

사용자의 “배포승인” 이후 **2026-10-14 09:26 KST**에 선택 릴리스와 자기 야간 예약 재결속을 완료했다. 앞 절의 미배포 표시는 각 리뷰 시점의 이력이며, 현행 배포 결과는 아래 영수증이 소유한다.

- 선택 릴리스: `/home/ubuntu/KORStockScan-runtime-releases/main-market-weakness-20261014-5fb4c0a33`, commit `5fb4c0a33a9df2b26e5fab4740576ce746a8cc93`. 실제 현행 부모 `01d9fefa4234b421fb0b2c74683562aa8a9c7358` 위에 약세 모듈3개·회귀2개·관련 문서4개만 결합했다. [원천/빌드 SHA](../../data/report/main_market_weakness_deployment/2026-10-14/build.json), [불변 release의 263개 테스트 통과](../../data/report/main_market_weakness_deployment/2026-10-14/release-tests.txt).
- [배포 결과](../../data/report/main_market_weakness_deployment/2026-10-14/deployment-result.json)는 `deployed_optional_verified`다. release-set/selection과 기존 detector 잠금 아래 선택을 전환했다. 착수 당시 Main·supervisor는 이미 없었고 정지 상태를 유지했다. 과거 PID receipt를 새 PID 소비로 전용하지 않았으며 `actual_pid_consumed=false`다.
- 원 정책·당일 PREOPEN/env/manifest와 이전 소비 receipt를 보존한 [인계 검증](../../data/report/main_market_weakness_deployment/2026-10-14/preserved-preopen-handoff.json)이 통과했다. 이것은 원 검증 세대 보존이며 Main 시작·재시작·새 정책 활성화가 아니다. 당일 최초 기동의 기존 15분 창을 연장하지 않으며 차기 PREOPEN 준비는 해당 날짜의 정책/원천 owner가 담당한다.
- [Optional 설정](../../data/report/main_market_weakness_deployment/2026-10-14/installation-after.json)의 `enabled=true`, `notify_enabled=true`, 설치 이력·원 source floor를 보존했다. KST `40 0-5,21-23 * * *` 한 행과 reviewed code hash를 재조회했다. 다른 cron 행과 연구 일별/후보/outbox 이력은 변하지 않았다.
- [필수 cron 8개 경로](../../data/report/main_market_weakness_deployment/2026-10-14/cron-routing-after.json), [선택 release 집합](../../data/report/main_market_weakness_deployment/2026-10-14/release-set-after.json), [실제 wrapper의 장중 차단](../../data/report/main_market_weakness_deployment/2026-10-14/outside-window-verified.json)을 확인했다. `outside_night_window`는 기존 owned log에만 남았고 연구 namespace의 파일/mtime/inode는 그대로였다. 장중 연구와 실제 Telegram 발송은 없었다.

첫 자연 수용은 **10/14 21:40부터의 허용 예약**이다. EOD/일반 장후 작업·시간/자원 gate로 보류될 수 있으며 다음 허용 슬롯에서 기존 예산 내 재개한다. 새 코드의 terminal→누적→후보→알림 disposition은 아직 관측하지 않았고, 실제 유의미한 숫자 발견이나 수익 개선을 주장하지 않는다. 기존 `MainMarketWeaknessPostcloseObservation1008`은 이 자연 수용을 위해 OPEN으로 유지한다.
