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
