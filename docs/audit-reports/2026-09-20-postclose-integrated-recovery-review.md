# 통합 장후 복구 리뷰·실행 증거

원천일 2026-09-17, 실제 준비 발행일 2026-09-20, 적용 예정일 2026-09-21. 9/18은 봇 중지에 따른 관측 미적재다. 운영 봇/주문/조기 PREOPEN을 실행하지 않는다.

## 코드 검증

선택된 메인 개선 code d9e2cdae3 및 리뷰 a189e7d57을 baseline으로 분리 작업본에서 구현했다. 날짜/범위·run/commit/clock/exit/proof를 결속하고 실제 불변 verification attempt와 원 실패를 보존한다. main strict 이전 DONE과 final detector 이전 DONE 경합을 제거했다. summary-only는 전체 완료가 아니다.

widget/machine 독립 wrapper의 exact-date terminal/source hash를 최종 summary/checklist에 포함한다. 역사 복구는 현재 계좌/cost 수집을 하지 않으며 알림을 끌 수 있다. 복구 정책은 원천/발행/적용일을 구분하고 기존 loader가 같은 날짜 계약으로 검증한다. main/compact 정책이 여러 적용일에 공존해도 명시 날짜로 검증한다. checklist 본문·ID·장전 시간창을 대사한다.

영향 회귀 **498 passed (17.70s)**. 범위: wrapper/finalization/cron completion, verifier/controller/direct handoff, checklist/summary, widget/episode dated policy, compact paired publisher/consumer, entry split 및 cancel wait emitter/evaluation/runtime/attribution. 합성 회귀이며 자연 표본·경제성 결과가 아니다. 로그 `/tmp/postclose-integrated-targeted-tests-20260920.log`. Python compile, 변경 shell bash -n, git diff --check 통과. print-only parser27건 중9/21 owner11건이며 외부 sync는 실행하지 않았다.

기존 배포본에서도 확장 정책 테스트2건이 실패함을 재현했다. fixture가 현재 paired 경제성 계약의 원천/terminal/policy identity를 포함하지 않았고 고정 종목과도 겹쳤다. 실제 paired 함수를 사용하는 독립 종목 fixture로 수정했으며 promotion gate는 완화하지 않았다.

## 인계 경계

기존 메인 리뷰의 ME8 alias 일부, ME9/10 전체 운영 경제성 OPEN을 보존한다. 메인 모집단2,281/대리값 비교/정책 carry를 실제 비용 후 실행 EV 완료라고 해석하지 않는다. 정책 준비·전체 실행 terminal·자연 PREOPEN/PID·실제 완료손익은 각각 별도다.

## 실행 상태

코드 검증 이후 커밋/푸시·immutable successor·A–H 실행/재사용·서비스 source binding·9/21 consumer 검증 증거를 추가한다. 이 초안의 실행 준비 상태는 전체 재생성이나 정상기동 readiness 완료가 아니다.


## 최초 복구 실행에서 발견한 추가 결함

- `70f957b7b`는 origin/main 및 feature push 후 immutable 배포됐다. 배포본55개 회귀와 consumer/preflight117개 회귀도 통과했다. main run `b63ad15ea7ac49b8b4a90e67be990d0e`의 원 실패·선행 성공을 보존한다.
- widget은 저장 snapshot 부재 종목에서 캐시 토큰 부재로 실패했다. historical retained-source-only 모드를 추가해 보존된 지원 입력을 계속 계산하고 부족 종목은 기존 quarantine 분모에 남긴다. completed prefix(advisory/auto)는 원 run/code/소스 hash 및 미변경 의존을 검증해 재사용한다. 새 source-context의 기존 partial receipt는 별도 attempt로 보존한다.
- low-price expansion은 캐시 검사 이전 토큰 요구로 저장 원천도 전부 false exclusion했다. 캐시를 먼저 검증하고 missing cache에만 기존 token/조회 경로를 호출하도록 수정한다. historical recovery는 remote 조회 없이 null·구체 missing 원인을 보존한다. 정상시장 API parser/요청/토큰발급/주문 계약은 변경하지 않는다.
- 공식 upstream current SHA `953e5dbff123f437ab4d11a78a95191a685eb51f`의 `kiwoom/core/auth.py`, `kiwoom/specs.py`, `kiwoom/_data/kiwoom_api_spec.json`을 확인했다. ka10080 POST `/api/dostk/chart`, 운영/모의 분리와 auth token 발급 endpoint를 확인했으며 실제 token issue/refresh는 하지 않는다. 조회 시각과 원문은 `tmp/postclose-integrated-recovery-20260920/official-reference/index.json` 및 같은 폴더에 보존했다.
- 재시도는 원 sim/rising feedback 성공 metric과 산출물 hash, 미변경 코드/원천 세대를 결속한 adoption receipt를 사용한다. 이 성공을 현재 코드로 다시 실행한 것으로 위조하지 않고 기존 플래그로 해당 두 실행만 생략한다. 다른 필수 producer/strict gate는 그대로 실행한다.

## 재개 및 소비자 추가 검증

- `ef0f7f995`에서 main 재개 run `df4fdcca755849f884716d8f929be677`은 원 sim/rising 성공 명령의 rc/run/code·산출물 hash·입력 generation을 검증한 `reuse-prefix-b63ad15.json`으로 두 단계를 재사용한다. 원 실패 status는 attempts에 보존한다.
- widget run `27a0ca2cbfd345348aaca262c4e8c62b`은 197개 모집단에서 retained source 연구를 완료하고 9/21 `observation_only` 정책과 관측 catalog58개를 발행·loader 검증했다. 신규 주문 정책0은 경제적 no-edge 확정이 아니다. 원천별 제외·실제 비교·holdout 상태는 보고서를 따른다. 연구552초·publisher35초, 외부 source 조회0이다. advisory/auto prefix는 원 run/code/hash를 보존해 재사용했다. machine 후행이 연구 enrichment를 변경하면 독립 receipt를 다시 결속해야 한다.
- 서비스7개 source binding을 정렬했고 `MainPID=0 / inactive`, 기존 비source env·주문 args·guard 보존을 확인했다. source pin만 바꿨으며 daemon-reload 뒤 서비스 시작은 없었다. 평일21:55 finalizer만 설치하고 기존 cron 전체를 보존했다. 근거는 `tmp/postclose-integrated-recovery-20260920/service-binding-installed.json` 및 `schedule-install.json`이다.
- bootstrap 실제 `build_manifest(9/21)` 오프라인 검증은 승인 incumbent9/18과 operator lock을 읽었다. PREOPEN canonical env/manifest/verify의 생성·변경은0이다. 회귀10개 통과. 기존 직접 인계 테스트가 rc/run/proof 없는 succeeded를 기대하던 fixture를 현 계약으로 고쳤으며 실패 차단도 검증한다.
- machine completed-study 재사용에 source/publication/effective 계약을 추가했다. 다른 publication/effective를 과거 완료 receipt로 반환하지 않으며 명시 적용일 불일치를 거부한다. 기존 합성 native CF 미래 clock을 모든 해당 publisher에 일관되게 주입하도록 테스트를 보완했다. 연구·발행/reader 영향 회귀89개 통과(18.74초). 미래 clock은 테스트에만 사용되며 운영 시각·과거 원천은 변경하지 않는다.

현재 main/machine/최종 인계와 준비 종결은 진행 중이다. 위 완료된 부분을 전체 terminal 또는 EV 개선으로 해석하지 않는다.

후행 machine writer가 widget 연구/적용 보고서를 정상 보강하는 경우, machine 시작 시 원 widget terminal hash를 고정하고 완료 시 native closed-loop 재구성·출력 hash를 확인한다. widget 원 run/receipt는 덮지 않으며 최종 인계는 명시된 두 산출물의 검증된 변경만 수용한다. 임의 후속 drift·advisory/auto 원천 변경·불완전 machine 결과는 계속 차단한다. 관련 handoff/episode/bootstrap38개 회귀를 추가 확인했다.

## 기동 경로 추가 결함과 부분 원천 인계

삭제된 과거 release를 참조하는 고정 청산 정책 경로를 확인했다. 승인된 SHA `aa2d4794… / 1536dfab… / d455951e…`와 동일한 tracked JSON을 검증하고 경로만 수정했다. 관련 서비스 정의9개·인스턴스129개가 비활성 상태이며 나머지 env/수량/guard는 변하지 않았다. 저가주 live/preflight 템플릿2개도 삭제된 source root를 참조했다. 이전 검토 commit5dcf237ad와 해당 runtime/apply/wrapper 코드가 동일함을 검증해 경로를 복구했고122개 인스턴스의 주문 인자 보존을 대사했다. 최종134개 기동 source/policy 경로 검사에서 missing0이다. 증거 `fixed-policy-path-repair-installed.json`, `low-price-template-source-restored.json`, `all-startup-source-path-audit-after.json`은 기존 실행 증거 폴더에 있다. 서비스 시작/주문은0이다.

확장 연구의 `partial_source_quality`는 producer에서 격리된 분모를 보존하는 정상 완료 형식이지만 publisher가 전부 거부했다. 원천 모집단·격리·비용 계약 검증을 통과하고 신규 추천0인 경우에만 기존 정책/disabled 인계를 허용하며 source gap 표기를 보존한다. 부분 원천으로 새 후보를 승격하지 않는다. 재시도는 원 성공 native metric·산출물/코드 hash·입력 generation을 보존한 prefix 인계로 완료된 확장 연구를 다시 계산하지 않을 수 있다. 이전 재사용 원장은 hash로 연결하며 새 run/commit으로 원 metric을 위조하지 않는다. 관련 회귀21개 통과.

## 후행 성과 연결 실패 및 체크포인트 보존

- 13:16 main 재시도는 expanded selection 789개를 계산한 뒤 실제 성과 보고서(약 83 MiB)를 읽는 32 MiB 한도에서 실패했다. 후보 계산 실패나 no-edge로 분류하지 않는다. native command rc=1, 1911.33초이며 명시적 exit가 ERR trap을 우회하여 running이 남는 결함도 확인했다.
- bounded regular/generation 검증을 유지하면서 해당 reader 한도를 기존 연구 보고서 계약과 같은 128 MiB로 맞췄다. EXIT에서도 실패를 단 한 번 기록한다.
- selection checkpoint는 후행 feedback 의존을 제거하되 입력 bar/비용/승인 정책/계산 코드/grid/holdout 결속을 유지한다. 기존 checkpoint는 원 release의 fingerprint 재현, 계산 AST 및 helper 동일성, result hash 확인을 통과한 것만 원본 보존 후 이관한다. 원 실패는 성공으로 바꾸지 않는다.
- 영향 회귀 155 passed (25.23초). 경제적 수익이나 자연 승격의 증거가 아니다. 전체 재생성과 최종 인계는 계속 OPEN.

## Machine 날짜별 producer/consumer 보완

- historical refresh의 entry timing 및 weakness hysteresis가 source 다음 영업일(9/18)에만 발행하던 날짜 결손을 보완했다. 원 source는 유지하고 명시된 publication의 다음 영업일로 effective를 정한다. 정상 실행의 기본 날짜 규칙은 유지한다.
- timing의 동일 단계 widget owner 조회도 실제 effective를 사용한다. timing report/evidence와 weakness immutable source snapshot에 publication을 결속하여 reader가 날짜만 바꾼 과거 증거를 거부한다.
- 회귀 70 passed(2.06초): 정상 기존 계산·후보·차단 회귀, recovery baseline/carry producer→publication→runtime reader, 날짜 불일치 차단. 제어 fixture이며 자연 신규 정책·경제성 성과가 아니다. main 원천 계산은 ad6fadeea 불변 release에서 계속 진행 중이다.

## Admission 원천과 Daily CSV의 분리

- main 939848688f104d61803f244e156ab5d5는 expanded 계산·보고서 생성을 완료했다. 기존 789 checkpoint를 소비하여 selection 재계산을 피했다. 이후 정책 변환은 admission 원장으로 확보한 종목에 Daily CSV 날짜까지 강제하는 reader 결함으로 실패했다.
- `admission_symbols(source_date, owner=episode)`의 기존 hash/date/owner 검증을 재사용하여 종목과 이름이 정확히 일치할 때만 CSV 부재를 허용한다. 미등록·이름 불일치·잘못된 날짜·손상 원장은 거부한다. 보고서 자체의 모집단·비용·holdout·recommendation 검증은 유지한다.
- 확장 보고서 원본 및 원 command rc=0를 재사용 증거로 보존한다. 정책 publisher 실패는 별개 실패 이력으로 남기며 전체 완료로 바꾸지 않는다.

## 기존 정책의 원천 세대 보존

- 재생성된 9/17 report가 9/18 기존 정책의 source SHA와 달라 incumbent 검증이 실패했다. 기존 정책/manifest를 수정하거나 hash를 바꾸지 않는다. 사전 백업의 exact SHA가 일치하는 원 보고서를 `source_snapshots/<sha>.json`으로 보존하고 reader가 그 불변 세대만 허용한다.
- CLI와 machine closed-loop 두 실제 publisher 모두 정책 발행 전 원천 스냅샷을 저장한다. 동시 변경·잘못된 snapshot hash·symlink는 거부하며 기존 candidate/holdout/parent reconstruction 검증을 유지한다.
- 53회 관련 회귀 통과. 후속 native publication 회귀와 실제 carry 변환을 추가 확인한다. 과거 정책은 기존 버전이며 신규 성과로 집계하지 않는다.

## 압축 라벨 predecessor 복구

- ADQ는 기존 라벨을 `.json.gz`에서 정상 읽은 뒤, 저장 CAS가 `.json` 존재만 검사하여 `source_label_predecessor_changed`로 실패했다. 실제 동시 writer나 라벨 변조의 증거는 없고, gzip 단독 세대를 잘못 제외한 결함이다.
- logical JSON의 기존 plain/gzip 동등성·충돌 검사를 유지하며 CAS와 원 revision 저장을 실제 보관 경로에 맞췄다. 원 gzip 바이트를 보존하고 기존 generation-safe writer로 새 세대를 발행한다.
- source-label/migration/CAS 회귀6개, native postclose CLI와 gzip 입력 회귀2개를 확인한다. 기존 label as-of와 새 재평가를 분리하며 원천 또는 완료 손익을 추정하지 않는다.

## 장전 source 선택 및 pipeline wrapper 추가 수리

- PREOPEN rebound reader는 직전 영업일만 추측하지 않고 이미 발행된 exact-date timing policy의 검증된 source 날짜를 사용한다. recovery source9/17→effective9/21 baseline을 제어 입력으로 확인했고 실제 조기 PREOPEN은 실행하지 않았다. timing/rebound 회귀93개 통과.
- main의 pipeline verbosity 입력 배열에 정의되지 않은 RAW_SOURCE 참조가 남아 있었다. exact-date pipeline plain/gzip 경로를 지역 변수로 결정한다. wrapper 회귀13개와 bash syntax 통과.
- ADQ source-label 및 cancel-wait producer는 12c20644f 실행에서 rc0로 통과했다. 이후 wrapper 실패는 별도 원 run에 보존하며 실행 terminal 완료로 표시하지 않는다.

## Machine shared-data 경로 결속

collector expansion/mechanical replay의 상대 data 경로가 immutable release의 공유 mount를 개별 원천 symlink로 잘못 판단했다. 기존 DATA_DIR의 신뢰된 mount 해석을 재사용하고 개별 artifact symlink/세대 충돌 검증은 보존했다. source gate·replay 회귀29개 통과. 대기 중인 이번 machine 프로세스만 종료하여 원 실패 attempt를 보존하고 검증된 successor에서 재개한다. trading 서비스에는 신호를 보내지 않았다.

## Late machine 결과와 최종 summary 재결속

machine은 모든 전행을 통과한 뒤 low-price actual 83 MiB dependency를 32 MiB로 제한한 마지막 receipt 생성에서 실패했다. 기존 보고서 128 MiB 계약을 해당 owner에만 적용하고 미관련 파일 한도는 유지했다. 대용량/native completion42개 회귀 통과. 중간 발행 뒤 실패한 machine 재개는 원 widget receipt/실패 run을 보존하며 현재 native closed-loop 재검증을 선행해야 한다. main의 최종 scoped verifier도 오래된 low-price reuse SHA를 성공으로 재사용하지 않고 실패했다. summary는 변경된 study를 검증된 late native dependency proof에 결속하도록 보완한다. 실패 wrapper를 PASS로 바꾸거나 전체 main evaluator를 다시 돌리지 않는다.

## 최종 의미 검증 및 historical detector

main proxy 모집단1715/대리 비교1710을 비용 차감 운영 paired 표본/EV로 투영하지 않도록 분리한다. 실제 비용 운영 비교가 입증되지 않은 EV/ΔEV/paired 수는 null이며 기존 대리값은 diagnostic_terminal_proxy에 보존한다. active 확장 연구의 partial source/allocator 차단을 퇴역 또는 not_applicable로 표시하지 않는다. 미래 계약 증거 없이 표본 부족을 자동 natural maturity로 판정하지 않고 contract review로 표시하며 과거 결손으로 구현 미완료를 추론하지 않는다. cancel/split의 지원 입력 producer/consumer·양수/holdout/fallback 회귀는 앞선498개 영향 회귀에 포함됐으며 역사 원천 census 결손과 별개다. 미래 운영 모델 자연 실증은 아직 입증되지 않았다.

최종 detector가 오늘/어제만 허용하여 명시적9/17 복구를 거부했다. full mode·clean baseline 이후·현재 as-of 이하 source date를 producer/receipt validator 양쪽에 적용한다. 회귀에서3일 전 source에 실제 현재 as-of 유지·모든 운영 mutation 비활성화를 확인했고 미래/기준선 이전/non-full은 거부한다. detector/summary/builder101개 회귀 통과.

## Final detector 관측 범위 및 로그 owner 마감

복구 final detector가 과거9/17에 존재하지 않은 새 bootstrap 파일을 요구했다. 명시 prepared9/21의 정상 PREOPEN 시간창으로 검사하며 미래는 future_due, 이미 지난 준비일의 필수 파일 누락은 계속 실패한다. 조기 PREOPEN 파일을 만들지 않는다. 마지막 변경이9/16~17인 기존 error 로그를 현재 폭증4214건으로 재집계하던 recovery 관측을 분리했다. 오래된 로그는 원본/크기/mtime를 보존한 historical evidence warning이고, 현재 변경 로그의 오류 burst와 모든 일반 모드 검사는 그대로 유지한다. 읽기 전용 recovery는 scan state도 갱신하지 않는다. 관련118개 회귀 통과.

cleanup의 실제 차단은 PREOPEN log22,531,453 bytes의 writer-owned rollover 누적 대기였다. active fd 부재·원본 SHA를 검증하는 기존 run_owned_log_rotation owner로 압축 보존했다. 원 SHA d1e40efcb49eaca02752f244df979c306fbabc0ad2c2c6d7ab3ed4cde4197780, 보관 SHA7e476722f1614cfb124e70819255d50ac864568da27673bcfb4be7f5d1b4d524. PREOPEN 실행이나 process restart 없이 해결했으며 실패 cleanup 이력은 유지한다.

최종 dispatcher 회귀에서 log scanner에 recovery source date가 전달되지 않는 누락을 추가 수리했다. 실제 ErrorDetectionEngine→LogScanner로 옛 파일 제외와 현재 변경 오류 fail, scan state 무변경을 함께 검증했다. 관련49개 회귀 통과. 앞선 detector 실패 receipt는 보존하며 현재 오류를 일괄 무시하지 않는다.

## 최종 복구 결과 — 2026-09-20 15:26:54 KST

**통합 실행·정책 인계·기동 전 준비는 완료했다. 신규 경제성 승격 및 메인 운영 경제성 계약 전체 완료를 뜻하지 않는다.** 원천일9/17, 실제 발행일9/20, 준비 적용일9/21이다. 9/18은 봇 중지에 따른 관측 미적재이며 정상0/휴장 표본으로 추가하지 않았다. 9/20 daily checklist 파일은 없어 미래 실행 owner인9/21 checklist를 사용했다.

최종 코드 `5bd73a8d2`는 feature와 origin/main에 push하고 immutable release `postclose-integrated-recovery-20260920-5bd73a8d2`로 선택했다. 최종 source pin9개 정의/129개 인스턴스를 비활성·PID0 상태로 재검증했다. 기존 거래 시각·주문 인자·수량·guard는 보존했다. 고정 청산 정책3개의 동일 SHA 파일과 기존 전문 서비스의 호환 source root를 유지했다. daemon-reload만 했으며 봇 시작/재시작·주문·조기 PREOPEN·외부 sync는 실행하지 않았다.

### R0–R6 구현·검증 대사

| 묶음 | 판정 | 증거 및 한계 |
|---|---|---|
| R0 | 완료 | 선택 release/병행 main 리뷰 기준 분리 worktree. 원 실패와 입력·원 정책 snapshot 보존. 다른 세션 변경 보존 |
| R1 | 완료 | source/publication/effective·scope·summary/checklist 결속, main/compact scoped rc0. 잘못된 날짜/hash/holdout·미래 freeze 거부 회귀 |
| R2 | 완료 | producers_completed→strict→main succeeded→DONE. 실제 UUID attempt, run/code/clock/exit/proof 검증. final detector 이후에만 전체 DONE |
| R3 | 완료 | 독립 widget/machine terminal과 허용된 late enrichment 검증. 퇴역 장후 작업 의존 제거, 설치된21:55 finalizer 인계 |
| R4 | 완료 | 과거9/17 복구와9/20 발행·9/21 reader 검증. 저장 원천만 사용하며 현 계좌/가격/비용/SELL로 과거를 채우지 않음 |
| R5 | 통합·분류 수리 완료; 기존 main 경제성 OPEN 보존 | 기존 지원 producer/consumer·양수/holdout/fallback 회귀 통합. main terminal proxy를 비용 후 EV/paired로 오표시하지 않음. ME8 일부·ME9/ME10 운영 모델/자본 검증 미완료는 아래 별도 구조적 OPEN |
| R6 | 준비 완료 | main/compact·timing·weakness actual loader, widget 기존 정책, episode61개 개별 reader 검사. PREOPEN/PID 자연 소비는 아직 미실행 |

### A–H 실행 및 재사용

| 단계 | 실행/재사용 결과 |
|---|---|
| A 원천 | 보존9/17 원천·원장·비용·source-quality preflight 검증. 결손 분모 보존,9/18 미적재 제외 |
| B 초기 main | economic reference 진단 rc2는 native wrapper의 허용된 비승격 진단. sim post-sell/rising feedback/expanded 원 성공 metric과 코드·입력·결과 SHA를 검증 재사용. auto-expansion/breadth/position fact는 실제 rc0 |
| C execution | scale-in split, entry split, ADQ, cancel-wait, verbosity, source-quality final, Samsung, low-price actual 실제 rc0. 과거 결손은 결과 상태로 남음 |
| D main/compact | full main803.72초, paired batch2.50/0.90초, WS129.81초, rising prior2.14초. 모두 rc0. 원 producer run `ca51eb738e934f34b51e1e0cae51d356`의 마지막 verifier 실패는 보존하고 후행만 수리 |
| E widget | run `27a0ca2cbfd345348aaca262c4e8c62b` succeeded. advisory/auto prefix 검증 재사용, retained study197개→관측 catalog58개. 연구552초/publisher35초, 외부 원천 조회0. 신규 거래 승격0 |
| F machine | expansion→attribution→weakness→timing 실제 성공. 큰 dependency receipt 결함 수리 후 native closed-loop 재검증, approval/checklist만 재개. 최종 run `ab84a2c94c2b4f13a417cf5e1b5d8ac9` succeeded |
| G 최종 인계 | 원 main producer 재실행 없이 run `b379f2eead8642f4ba87709506b814b4`로 원 run/code/hash를 연결해 최종 summary/checklist/scoped/strict/parser 재검증. main terminal succeeded. 최종 controller whole_native_chain_done_claimed=true |
| H 마감 | cleanup 완료 후 full read-only detector run `cron-20260920T152652-577724`,7개 초기화/검사, fail0·warning3·pass4·운영 mutation0. 15:26:54에 finalization/final_detector DONE 기록 |

최종 detector 경고는 과거 intraday panic 보고서 부재/시장 상태 completed_with_warnings, 자신의 부모 finalizer가 아직 detector를 기다리는 정상 `pending_self_audit`, 변경 없는 과거 오류 로그다. 과거 오류가 해결됐다고 주장하지 않는다. 부모 DONE은 detector 반환 후의 로그로 대사했다. 원 main/machine 실패, cleanup/후행 detector 실패와 각 재시도 receipt는 삭제하거나 성공으로 덮지 않았다.

### 준비 정책과 경제성

| 소비자 |9/21 오프라인 검증 결과 |
|---|---|
| 메인/compact | source9/17/pub9/20/target9/21 bundle valid. `incumbent_carried` / `compact_incumbent_carry`; promoted scopes0; hard guards unchanged. bundle SHA `5dd839d8058e364b92671985d2387b23f2143079a0dde198ef91e00128ef6821` |
| widget | 기존9/18 정책을9/21 관측 시점에서 loader가 소비 가능함을 확인. 삼성 KRX 정규/NXT 프리 및 기존 고정 종목.9/21 새 symbol catalog58개는 observation-only |
| episode 정적 owner | 승인된61개를9/21 임시 정책 payload로 actual reader 검증:58 ready,3개는 비용 재검증 비양수 quarantine. 실제 PREOPEN publish는 하지 않음 |
| episode 확장 |9/21 정책3개는 `retired_entry_exit_custody_only`, 모두 신규 진입 불가. 정적61개/관측58개와 합쳐 새 진입 정책으로 세지 않음 |
| timing/weakness | actual dated loader에서9/21 ready, source9/17. timing baseline immediate carry, weakness activation2/release3 유지 |
| 공통 bootstrap | 승인 incumbent9/18과 operator lock으로 manifest를 메모리에서 검증,477키·rejected0.9/21 canonical PREOPEN env/manifest/verify 및 PID receipt는 생성하지 않음 |

필수 직접 원천11/11, summary `direct_evidence_complete`, **검증된 edge0·새 승격 후보0**이다. economic state는 source_gap5, insufficient_sample1, measured_no_edge1, mixed1, not_applicable3이며 실행 성공과 별개다. rising 연구의 탐색 후보6개/302쌍17일은 승격 후보0과 다른 분모다.

main1715 모집단/1710 비교의 기존 대리값은 양쪽 -0.0054462573%, 대리 Δ0이다. 이를 비용 차감 운영 EV로 쓰지 않고 diagnostic_terminal_proxy에만 보존했다. main의 운영 비용 후 EV·순익/일은 null이다. compact 과거 source 계약 결손과 source/candidate/model holdout 미충족도 승격하지 않는다. 양수 정책·실제 이익·인과적 개선을 새로 확인한 바 없다.

### 잔여 OPEN과 다음 확인

- **구조적/구현 검증 OPEN:** 기존 메인 owner의 ME8 일부 alias·ME9/ME10 operating population/운영 청산·비용·공유 자본 계약. 이번 인계 수리나 모집단 수로 해소를 주장하지 않는다. owner는 [메인 operating evidence 리뷰](2026-09-20-main-machine-operating-evidence-closure-review.md) 및 기존 메인 계획 §14. closure는 지원 producer→동일 자본 CF 운영 계산→독립 검증→정책 소비의 실제 계산·회귀다. 단순 시간 경과로 닫히지 않는다.
- **과거 원천/지원 범위:** cancel-wait execution census와 entry split의 당시 terminal/cost 결손, 확장 allocator snapshot, microstructure 원천 결속 결손은 과거 복구 가능성과 미래 생성 검증을 구분한다. native report별 blocker/owner/closure를 유지한다. 지원 producer 회귀 통과를 과거 원천 복구로 해석하지 않는다.
- **자연 OPEN:**9/21 정상07:35 PREOPEN→07:55 main→07:57 episode→07:58 widget의 실제 날짜/hash/guard 및 PID 소비, 독립 자연 표본·완료 비용 손익. 기존 `DirectFamilyPreopenPolicyHandoff`와 family stable owner를 유지한다. 오늘 새 실행 권한이나 조기 실행은 만들지 않는다.

### 검증·원본 증거

최초 영향498개, 이후 원인별 집중 회귀를 수행했다. 마지막 날짜/관측118개 및 실제 dispatcher49개 통과. 서로 겹치므로 합산하지 않는다. Python compile, 변경 shell bash -n, git diff --check, print-only 문서 parser 통과. 합성 fixture는 자연 표본/EV 증거가 아니다.

- [최종 대사 JSON](/home/ubuntu/KORStockScan/tmp/postclose-integrated-recovery-20260920/final-reconciliation-20260920.json): 원 실행/재사용·terminal·검증 attempt·현 정책 및 증거 SHA.
- [controller](/home/ubuntu/KORStockScan/data/report/postclose_done_controller/postclose_done_controller_2026-09-17.json), [불변 최종 strict](/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/attempts/2026-09-17/73ffc93c1c534af1a5a310249ad71fc6.json), [detector](/home/ubuntu/KORStockScan/data/report/error_detection/error_detection_2026-09-17.json).
- [선택 release actual reader](/home/ubuntu/KORStockScan/tmp/postclose-integrated-recovery-20260920/selected-release-final-dated-readers.json), [widget/episode/bootstrap](/home/ubuntu/KORStockScan/tmp/postclose-integrated-recovery-20260920/startup-offline-readers.json), [서비스129개](/home/ubuntu/KORStockScan/tmp/postclose-integrated-recovery-20260920/service-binding-5bd73a8d2.json).

초기 실행 중 기록은 당시 상태를 보존한 것이며 현재 실행 종결은 이 절과 불변 receipt를 기준으로 판단한다. **기동 전 준비 완료와 전체 경제성 보완 완료를 구분한다.**
