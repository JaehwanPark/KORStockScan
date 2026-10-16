# 2026-10-16 EOD·장후 의미 검증과 복구

대상 원천일은10/16, 다음 영업일은10/19다. 자정 이후에도 이 두 날짜를 유지한다. 현재17일 체크리스트는 없으며, 주말 임의 소유자를 만들지 않고16일 원천과19일 실행 소유자를 사용한다. 사용자의 실패 보완·재실행·의미 결함 점검 지시에 따른 source-only 복구다. 원 정규 run은082096071의 `3e85e2b94d2343d39348739296a8acc6`이며 새 코드로 재라벨링하지 않는다. 매매 프로세스 재기동·주문·수동 provider/threshold/env 변경은 수행하지 않는다.

## EOD와 원 실행

20:05:05 시작한 EOD는20:56:06 `completed_with_warnings`다. 직접 DB 조회는 최신일10/16·2,622행을 확인했다. 대상2,626개 중4개(179880·266690·468670·486510)는 최소20개 이력 부족으로 제외됐고, 알파벳 namespace86개는 별도 eligibility 제외다. 이 둘을 동일 실패 분모로 합산하지 않는다. 설치된 장후 owner가 EOD gate 뒤 자연 정지를 수행했으며 실제Main389707은 종료됐다.

원천 감사는344,478행 중 결함6행을 원본·manifest 보존 후 격리했다. 최종 유효 원천은344,472행이다. unknown-token 경고와 허용된 부분 원천을 전체 실패로 바꾸지 않는다. archive는20:58:40에 완료됐으며 이 시점과 현재 재검증을 구분한다.

## 확정 결함과 수리

| 결함 | 직접 근거 | 수리와 검증 |
| --- | --- | --- |
| 관리 release의 종목원장 경로 | 신뢰된 data mount에서 strict reader의 ancestor no-follow가 `NotADirectoryError` | 공용 canonical DATA_DIR 사용. 하위 링크·손상 최신·plain/gzip 충돌 거부 유지. 원본에서2개 재현, 영향367개 통과 |
| rising feedback의 감사 전 입력 결속 | 보고서344,478행과 격리 후344,472행 불일치 | wrapper의 기존 feedback을 preflight 다음으로 이동. 원천을 감춘 count 보정 없이 실제 재생성. shell harness가 이전 순서 실패·수리 후 성공 |
| 보유 연구 feature cache의 물리 row 초과 | native replay의87,655바이트=[호가9,665+feature77,987+구조], 정상 관측32개 | 관측 목록을 기존 immutable tree로 분할·검증 복원. row64KiB·leaf256KiB·cache64MiB 유지. 단일 과대 관측은 기존 streaming. 영향102개, 실제 관측 전수 일치·변조 거부 검증 |
| 압축 후 native 정책 ancestry 단절 | 정상 발행 뒤 native 검증이 과거 원문 경로 부재로 incumbent_unverified | 초기에는 정확한 정책 해시가 증명하는 압축 원본5개를 복원하고 임시 보존. 후속 사용자 지시에 따라 원문·압축 해시/세대와 원 inode를 영수증으로 연결해 압축 가능한 소비 계약으로 대체. file publication과 consumer 성공을 분리 |

최종 runtime 코드 커밋은0e19ffcbeee4daa2090a7ba4aa284a063064ca6e이며 앞선34113fb0a·38be5e0bd·16a5d06a6·b9bf4ea4f·044a0dded·ed3e93a03·e09c1c28f를 포함한다. e6aac24bf의 비압축 보존은 미선택 보호안 이력이며 최종 압축 소비 계약이 대체한다. 매매 kernel·정책 payload·비용 배분 계약은 변경하지 않는다. Native128scope·76,800행·594hit parity는 mismatch0이며 네 family fixture도 현재 코드로 검증했다. 새 저장 계약은 engine root 대신 lifecycle/snapshot_archive.py에 둔다. 새 collector·cron·stage는 추가하지 않았다. `.venv` compile, shell syntax, diff, print-only parser를 확인했다.

최초 snapshot 실패 로그와 완료된 거래·매도 후속·누락 진입 보고서는 별도 보존했다. 같은 원천을 반복 계산하던 분석 재시도의 정확한 PGID466810만 identity 확인 후 종료했고, 부모 native terminal은exit143 실패를 남겼다. 세 산출물만으로 완료 manifest를 만들지 않으며 수리된 정상 snapshot producer로 재생성했다. 직접 복구의 첫 실행은 공통 custody 식별자 누락을 발견해 발행 전 중단했고, native parser의 두 식별자를 전달한 새 PID/start/cwd로 다시 실행했다. 이 운영 실수와 교정도 별도 기록한다. 별도 성공한 다섯 stage는 native `--check` 결과에 따라서만 재사용한다.

## 결과별 의미 판정

| 결과 | 실행과 분석의 의미 | 결손·권한·다음 closure |
| --- | --- | --- |
| Main 누적 기계 연구 | 62개 source partition·pre-refresh 제외26, 유효4,530,988행; 누적 비교22scope·machine cell48개·venue 포함 native scope128개·유효 관측36scope는 별도 분모 | 연구 선택·기존 정책 승계와 실제 적용을 분리. 날짜별 staging→PREOPEN→새 PID 소비 필요 |
| 보조 paired 평가 | comparison/request accounting 완료, 등록 정책 carry | 기존 요청/응답을 재사용. 코드 수리는 신규 provider 비교 호출이나 정책 전면 교체가 아님 |
| outcome labels | 34개 중29 mature·5 partial. compact supplement20 exact·14 trace hash mismatch | 원 canonical context/input bundle 결손을 supplement로 승격하지 않음. 경과한 고정 window 부재는 과거 source gap; source-valid 미래 maturity와 구분 |
| 완료 거래·경제성 | 당일 entry fact의COMPLETED5·HOLDING3, 전일 진입을 포함한 completed census9·valid profit_rate9; strict 비용 유효 완료0/제외9 | 0은 무거래·무수익이 아니라 비용 적격0. 공식 원천의 종목일/주문 비용 합계 차이(삼성10원·HPSP20원)와 복수 cycle 배분 불명. null 유지, 임의 안분 금지 |
| 초기 수량 | carry_parent, runtime apply false, 경제성 적격 completed0 | 당일 실제 완료5와 구분. no_winners를 시장 기회 없음이나 모든 거래 손실로 해석하지 않음 |
| 분할 진입 | 계획27·실제 attempt28·intent26·투영 주문19·부모join15·미등록2 | source_gap, 비교 가능한 실제 비용 완료0. `DirectFamilySourceRepairEntrySplit`: original leg/owner/terminal/cost의 정확 join과 native reader 검증 |
| cancel-wait | source_quality pass와 economic_tuning_input_allowed false가 공존 | known open0은 역사 custody 완료가 아님. 누락9/29·9/30·10/1과 알려진 unresolved10을 보존. `DirectFamilySourceRepairEntryCancelWait`: 원 제출·terminal·비용 대사 |
| 보유·손절·익절 | 실제 완료·모델 대체 청산·무진입 CF를 분리. 연구504개 population·32partition, 20,832scope는9/16 원장2,604종목×8 market/route 조합이며 당일 EOD 종목수나 live128scope와 다름 | 과거 TP 최초 전이5건과 실제 비용 결손은 과거 기록을 만들어 닫지 않음. 무진입 forward path482개·최종 snapshot source_gap4/unverified9도 원 census에 남김. legacy gzip 발견 전 missing7/unverified1과 분모가 달라 같은 결손 수의 증감으로 비교하지 않음. 현재 저장 결함과 별도 `HoldingProfitExitSourceContractRepair` owner |
| 상승누락 | 격리 후 원천과 검증된 master를 소비해야 유효 | `PostcloseStructuralPolicyCompletion1011`: 새 source count/hash→classifier→reader→최종 handoff |
| 시장약세 장후 연구 |21:40 예약은 regular_postclose_or_eod_active로 deferred, worker 미시작 | report-only 정상 자원 대기. 이후 허용 야간 슬롯의 report-only 진전과 다음 PID/실제 수익을 구분 |
| 보관·Parquet | archive 완료는 원 as-of 검증; tuning은 Main predecessor 뒤 실행 | 논리 source hash/coverage 검증. 압축·파일 존재·exit0을 전략 결과나 경제성으로 세지 않음 |

비용 세부 의미는 공식 upstream953e5dbff123f437ab4d11a78a95191a685eb51f의SDK/spec/Postman 및 로컬 데이터 계약과 대조했다. 해당 revision의ka10076 continuation cursor는 개별 order exact filter나 per-fill 비용 배분 계약을 증명하지 않는다. 추가 broker 조회는 수행하지 않았다. 과거 결손에는 ETA를 만들지 않으며, 원 source/adapter가 없으면 같은 replay를 반복하지 않는다.

## 압축·반복 읽기 후속 리뷰

원문 보존은 비압축 보관과 다르다. 원문 해시/크기/inode/mtime/ctime, gzip 전체 왕복·CRC 일치, 압축 해시/정확한 세대를 작은 monitor_snapshot_archive_identity_v1 영수증으로 연결한다. 큰 trade_review와 completed_projection도 압축 가능하며 작은 dependency receipt는 보존한다. 기동·정책 인계·window·손절 inventory는 압축 바이트와 bounded metadata를 검증하고, 실제 내용을 쓰는 연구만 gzip을 streaming decode한다. 큰 거래 JSON 전체를 정책 선택 함수에서 decode하던 읽기도 제거했다. 원 날짜 보호와 다음 정책일·controller 보호는 유지하며 현재일 보호를 임의 우회하지 않는다.

손절 native CLI에는 기존 invocation-local digest session을 적용했다. 첫 전체 해시 검증은 수행하고 같은 file identity/ctime의 반복 해시만 메모리에서 재사용한다. 종료 후 캐시는 폐기되고 source/cost/정책 의미 검증은 계속 수행한다. 압축 자체로 기동 시간을 보장하지 않으며 실제 바이트/시간 결과를 별도로 기록한다.

코드 리뷰에서 옛 gzip+sidecar가 새 원 inode 경로에 잘못 들어가는 호환성 문제를 실자료 source-window gate로 발견해 보고서 갱신 전에 중단했다. 옛 gzip에는 기존 bounded physical gzip-generation 계약을 유지하고, 새 archive receipt에만 원 inode 이전을 허용했다. 모든 기존 날짜의 frozen window가 동일함을 직접 검증했다. 손상 archive는 해당 날짜의 source_gap으로 격리하며 다른 날짜를 지우지 않는다.

기본 영향460건, 교차 읽기·세대 보완31건, 손절 세션252건, 옛 gzip 호환58건, snapshot CLI87건, 최종 holding fixture99건, 마감 관측 분류290건이 통과했다. 이어 최종 코드에서 cancel-wait96건·상승누락86건·보조84건의 network-denied fixture를 새로 발행했다. 중복 실행 시험 숫자를 고유 합계로 더하지 않는다. 코드 변경 중 실행돼 code-generation guard로 거부된 시험과 selector 변경을 감지한 fixture 시도는 원 실패로 보존하고, 최종 고정 코드/원천의 검증과 구분한다.


실제 과거 holding5개는 기존 gzip bytes를 바꾸지 않고 원문과 일치하는 압축 인계 영수증을 발행한 뒤 plaintext13,005,961bytes를 제거했다. 원 native 부모 정책·전체 frozen input window·현재4개 manifest가 모두 유효하며 원 정책/summary/strict bytes는 바꾸지 않았다. 정규 cleanup은 별도로1,783,336,714bytes를 절감했다. 현재 날짜/다음 정책일 보호는 그대로여서 현재일 큰 원천을 임의 압축·삭제하지 않았다.

보유 보고서만 최종 저장 계약으로 갱신하는 데254.445초가 걸렸고 거래·매도 후속·무진입 prefix3개의 SHA는 그대로다. 정규 손절 stage는375.48초(생산자374.731초), 첫 전체 digest21회/17,060,657,488bytes·동일 세대 재사용70회/50,736,665,771bytes였다. 생산자 thread 실제 논리 읽기30,434,762,867bytes·물리 읽기28,895,936,512bytes, peak RSS144,360KiB다. 재사용 bytes를 실제 총 디스크 절감이나 기동 시간 감소로 과장하지 않는다. 원 stage 약635.5초에는 자원 대기118.45초가 포함돼 단순 시간차를 전부 캐시 효과로 돌리지 않는다.

최종 코드 binding에 맞춰 손절과 pre-submit delay만 원 native stage로 갱신했다. 손절9cell의 수치, delay231cell의 선택값과 기본0초·기존 nonzero2cell은 모두 그대로다. delay compact 원천 SHA도14dbaa8efb6533739a402b2179e2ecee27be954933c98676ba2ec43363cfac8a로 같다. 원 old ledger/code 실패와 기존 immutable generation은 보존했다.

## 의도적으로 삭제한 삼성 선택 연구 원천

사용자가 삼성 선택 연구 원천을 삭제했음을 확인했다. optional forward sidecar는 새 분석에 그 observations 내용을 재사용하는 대신 등록 단계에서 과거 후보 source seal을 매번 검사해 실패했다. 새 날짜 평가는 별도의 당일 관측·가격·체결과 봉인된 규칙/부모를 사용한다. 이 optional 연구는 Main 정책 발행·기동의 필수 stage가 아니다. 이번 세션이 추가한 원천 복구 OPEN은16일·19일 양쪽에서 취소했고, 삭제 원천을 복원하지 않았다. 실패 bytes를 연구 성공으로 바꾸지 않았으며 기존 optional 예약 호출의 종료/제거까지 완료했다고 주장하지 않는다.

## 마지막 observer 판정 결함

23:49 최종 점검은 EOD로 Main이 자연 종료하고 다음 기동용 selector만 바뀐 상황에서도 old observer에 현재 코드 세대를 요구해 실패했다. 같은 날 closed observation의 허용 경로를 추가하되 exact EOD/DB·원 native Main succeeded terminal·다음 날짜 전용 미소비 selector·Main 부재·원 selector/observer 봉인을 모두 요구한다. process scan 불명확·날짜/서명/세대 변경은 거부한다. historical_generation_verified는 원 source gap과 current_generation_verified/current_observation_verified/full_coverage_proven=false를 보존하며 새 PID 건강 상태를 만들지 않는다. 다음 날의 기존 과거 원천 판정 경로도 유지한다.

이번 세션의 첫 최종 청소 재시도는 storage-only 모드 적용 조건을 잘못 판단해 native preflight에서 거부됐다. 해당 모드는 직전의 특정 저장소 실패 복구 전용이며 이미 DONE인 청소의 일반 재사용 모드가 아니다. 원 성공과 실패를 남기고 guard를 우회하지 않은 정규 청소 경로로 교정했다.

## 최종 인계 검증

복구 Main 원 실행c824687f9fa849038d5688e6ee95b5a0은16a5 코드로22:27:56~22:56:10에7개 stage를 성공했고 tuning도22:58:17에 완료했다. 이를 최종0e19 코드의 실행으로 재라벨링하지 않는다. 이후 영향을 받은 holding/stop/delay와 최종 summary/checklist/strict/controller만 native owner로 갱신했다. 원082 실패·중단 재시도·직접 실행 누락·legacy gzip 불일치·old delay ledger·관측 세대/청소 모드 실패는 각 로그/immutable generation에 남겼다.

최종화는2026-10-17 00:12:51에 source16일·effective19일로DONE이다. Controller DONE과 strict PASS를 native 영수증/해시로 확인했다. 이후 최종 fixture3개(96/86/84건) 발행 후 full detector만 기존 producer/lock으로 재검증했다. 최종화 당시 봉인된 detector bytes와00:15:49의 최신 full detector는 서로 다른 실제 실행으로 보존한다. 최신7개 detector가 모두 초기화/실행됐고 critical/error0·warning3·pass4, operational mutation0이다. 원 finalization footer를 나중 보고서의 해시로 고치지 않았다.

10/19 prepared는 최종 선택0e19ffcbeee4daa2090a7ba4aa284a063064ca6e·source10/16·candidate b0214465eecc265388fda660445a43b3280dc303b1175617ce08681bbe5814d4와 결속돼 있다. prepared manifest file SHA는0280f41eece44fc071b1fa9ed95c72c7510deba6f768cb6b5425459ce67bbd08, 의미 SHA는a1916111750df27e76813dc1935a0ff0a297d641181130704dec1ee85cce33e0다. 마지막 별도 verify는 generation-only가 아닌 current_full_contract PASS/findings[]다. 현재 live policy pointer8809c82e…는 그대로고, 다음 후보는 이전2a6afd…와 native behavioral family가 동일하다. Main과 supervisor 부재·startup hold/restart flag 부재·선택 release의 clean source를 확인했다. 설치된 월요일07:35 PREOPEN·07:55 start route도 확인했다.

남은 warning은 EOD의 이미 식별한4개 짧은 이력·holding의 실제 source gap·과거3개 report의 code-generation 미검증, 변동 없는 역사 error 로그, 보존된 tmp 예산 초과다. finalization의 pending-self-audit warning은 마지막 독립 sweep에서 사라졌다. 현재 code fixture4개 PASS는 과거 다른 code generation 보고서를 재계산/재작성한 증거가 아니다. 과거3개 report는 native_validated=false와 원 hash를 유지하고,19일의 기존 DirectFamilySourceRepairEntryCancelWait/PostcloseStructuralPolicyCompletion1011/DirectFamilySourceRepairCompactAuxiliary owner가 다음 정상 producer→선택/발행→native reader를 수용한다. 이 비차단 연구 경고를 현재 기동 소비나 경제성 PASS로 사용하지 않는다. tmp 경고를 끄려고 pin된 원 실패·회복 근거를 삭제하지 않았다.

준비 완료는10/19의 실제07:35 PREOPEN·07:55 기동·새 PID 소비나 비용 후 성과를 증명하지 않는다. actual_pid_consumed=false·runtime_effect=false이며 이번 source-only 복구에서 봇을 재기동하지 않았다. native 검증 범위의 기동 차단은 없으나 아직 도래하지 않은 실제 기동을 보장 완료로 기재하지 않는다.

최종 직접 근거는 [최종 수용 영수증](../../tmp/postclose-monitoring-20261016/final-closure-verification.json), [전체 장전 계약 검증](../../tmp/postclose-monitoring-20261016/final-next-preopen-full-verification.json), [압축 인계 실증](../../tmp/postclose-monitoring-20261016/native-compressed-holding-handoff-verification.json), [반복 읽기 실측](../../tmp/postclose-monitoring-20261016/main-stop-final-validation-io.json), [현재 code3개 fixture](../../tmp/postclose-monitoring-20261016/final-three-family-fixture-validation.json), [정규 최종화](../../tmp/postclose-monitoring-20261016/finalization-closed-observer-regular-cleanup.log), [마지막 독립 detector](../../tmp/postclose-monitoring-20261016/final-fixture-detector-refresh.log)다.

직접 검증 기록은 [task evidence](../../tmp/postclose-monitoring-20261016/initial-state.json), [최초 실패](../../tmp/postclose-monitoring-20261016/originals/snapshot-failed-attempt-1.log), [정상 관측 분할](../../tmp/postclose-monitoring-20261016/real-feature-partition-validation.json), [native parity](../../tmp/postclose-monitoring-20261016/handoff-38be5e0bd/native-parity.json), [fixture 검증](../../tmp/postclose-monitoring-20261016/family-fixture-verification-38be.json)에 보존한다. 외부 문서/Calendar 동기화는 실행하지 않는다.

## 기존 보고서의 다음 정상 생성 수용

| 기존 owner | 보존한 원 보고서 | 현재 코드 capability / 다음 closure |
| --- | --- | --- |
| DirectFamilySourceRepairEntryCancelWait | [10/16 cancel-wait](../../data/report/entry_cancel_wait_tuning/entry_cancel_wait_tuning_2026-10-16.json) | code95d385be… fixture96 PASS. 다음 정상 producer가 원 source·policy carry를 보존하고 새 code/source generation과 native reader verified를 발행 |
| PostcloseStructuralPolicyCompletion1011 | [10/16 상승누락](../../data/report/rising_missed_classifier_prior/rising_missed_classifier_prior_2026-10-16.json) | code3ea3b162… fixture86 PASS. 새 source count/hash·classifier→policy→reader가 같은 세대를 소비하고 valid_empty와 원천 결손을 구분 |
| DirectFamilySourceRepairCompactAuxiliary | [10/16 보조 평가](../../data/report/reversal_auxiliary_tuning/2026-10-16/evaluation.json) | code472deb89… fixture84 PASS. 원 요청/응답·membership·누적 예산을 보존한 정상 producer→선택/발행→reader의 새 세대 검증. 새 provider 호출이나 과거 보고서 restamp로 대체하지 않음 |

위 source body·해시·과거 contract는 그대로다. 새 fixture만으로 서로 다른 과거 code hash를 현재 generation으로 승격하지 않는다. 이19일 기존 owner의 Acceptance는 첫 Main 기동 완료나 실제 경제성을 증명하는 gate와 구분한다.


## 10/17 후속 전수 검토와 재생성

앞 절의 00:17 판정과 영수증은 당시 이력이다. 후속 사용자 지시는 발견한 기계적·의미적 결함의 수리·리뷰·재생성·재검증 반복이며, 최신 선택은 `c63d44bcb048e4ffd66d811c98a8913d7e0fdefe`다. `68be02a77`의 원천 연결·custody, `bd550f123`의 기계 완료 기록, `272083f42`/`c63d44bcb`의 발행 모집단 보완을 포함한다. Main은 EOD 뒤 정지 상태이고 실제 다음 PID는 아직 없다. 원 live 정책 8809c82e…는 유지하며, 10/19 후보 `8071b2f4386dfec0e1e9379d1ada3a0b94aea4ff5d4f02ebbc5c35db7ca5bb0d`를 native CAS로 준비했다. machine family 수치·보조 membership·provider/주문/수량/timeout 권한은 바꾸지 않았다.

| 확정 결함 | 수리·리뷰·실제 소비 근거 |
| --- | --- |
| 분할진입 bounded refresh가 과거 atomic 판정을 계속 복사 | 같은 원천 세대의 현재 reader로 원 계획·action·계좌·owner·bundle·probe residual·registry intent를 검증. 원 leg 0과 계획 leg 1의 의미를 대사하고, 정상 복수 leg의 서로 다른 intent를 허용한다. 잔여 주문 0043364/0043365도 봉인된 context와 정확한 journal만으로 연결 |
| 새 refresh의 compact 날짜 처리 누락 | 실발행 비교에서 emitted_date를 읽지 못해 9개 원 계획이 빈 목록으로 사라지는 회귀를 발견. 원 실패 세대 보존 후 날짜 처리와 producer→reader stage별 보존 검사를 추가. 원 stage가 없음을 나타내는 빈 census와 잘못된 null도 구분. 최종 실제 발행은 계획 8·deferred 1·주문 10, 격리/미연결 0·보존 verified |
| 과거 연구 결손이 현재 custody까지 unknown 처리 | 같은 날짜의 원 ORDER_BOUND·ORDER_TERMINAL identity와 checkpoint 이전 시각, 검증 journal prefix·계좌 조회 세대를 모두 요구. 역사적 잔여 6건 때문에 가려졌던 현재 Main 보유 3건을 known_open으로 확인. 과거 비용·terminal proof 결손을 해소했다고 추정하지 않음 |
| 기계평가 뒤 보조평가 조기 종료 시 완료 정보 유실 | circuit/lock/common-provider 반환에도 원 machine capture를 보존. 현재 WAIT/DROP와 보조 미호출을 유지. 과거 aidt-7dbc…의 해시·snapshot·record·route·PID/start·시각이 일치하는 원 관측 1개만 보고서에 연결. duplicate·conflict·잘못된 날짜·미래 capture·이미 소비한 capture 거부. 원 trace/payload bytes 불변 |
| 현재 fixture와 이전 보고서 생성 세대 분리 | cancel/rising/auxiliary/holding을 실제 native producer로 재생성. 4 family 모두 native_validated=true/verified이며 현재 fixture만 과거 report에 덧붙인 판정이 아님. 원 보고서·immutable generation·실패 이력 보존 |

관련 수리는 562건, 기계 완료 기록은 824건, 발행 보존은 323건 및 마지막 빈 census 보완 262건을 통과했다. 겹치는 검증 실행을 고유 합계로 더하지 않는다. compile/diff와 실자료 검증을 별도로 수행했다. 보유 보고서 재생성은156.049초, 거래·매도 후속·누락진입 prefix 3개의 SHA는 그대로이며 4-artifact native manifest도 검증했다. 같은 immutable 원천을 전체 체인으로 반복 재실행하지 않고 영향을 받은 source/audit·holding·stop·delay·summary consumer만 갱신한다.

### 활성 장후 결과의 의미 대사

| 논리 작업 / owner | 검토한 결과·판정 | 결손 영향·직접 소비·다음 경계 |
| --- | --- | --- |
| EOD·archive / 설치 owner | EOD source 10/16·DB2,622행, 4개 짧은 이력 제외·namespace86 별도. archive 원 terminal 보존 | 짧은 이력은 기동 결함이나 0건 연구가 아님. 원천은 논리 hash가 검증된 압축 인계 유지 |
| Main 기계 / main_machine_policy | 62partition, 유효4,530,988행·pre-refresh26 제외. 비교22scope·machine48cell·native128scope는 다른 분모 | 유효 carry, 새 후보의 비용 후 우월성을 주장하지 않음. 10/19 PREOPEN·PID 소비는 기존 DirectFamilyPreopenPolicyHandoff |
| 품질·legacy / legacy_machine_report | 유효344,472행·원 결함6행 제외 보존. 기계58=평가35(원 연결 복구1 포함)+source-invalid16+contract-invalid7, 미계상0 | 계약-invalid7과 source-invalid16은 격리. 기록 복구는 보조응답·실제 주문·경제성 생성이 아님 |
| 보조 / main_auxiliary_policy | 원 요청 census100=completed47+planned53, missing0. 10scope의 common22pairs/expected50 | comparison_complete는 정산·격리 완료. 전100호출 실행이나 모든 비교쌍 성공을 의미하지 않음. 이번 재생성은 stored 결과만 사용, 추가 provider0 |
| outcome_labels | 34=29mature+5partial, supplement20exact/14trace mismatch | 경과한 window의 원 가격·문맥 부재는 미래 maturity 대기로 숨기지 않음. original source가 없으면 ETA null·경제성 제외 |
| 완료 거래·초기 수량 | completed census9·valid profit_rate9, strict 비용 적격0. 당일 entry의 completed5/holding3 별도 | 비용 종목일/주문 차이 및 cycle 배분 불명은 null·기존 carry. 0을 무거래·무수익으로 해석하지 않음 |
| 분할진입 / DirectFamilySourceRepairEntrySplit | 현재 atomic 계획8·주문10 연결, resolved residual2·미연결0. 전체 model attempt28/intent26/투영주문19/부모join15는 별도 분모 | strict 실제 비용 완료0·paired 운영 model source_gap 유지. 원 terminal/cost와 같은 frozen 주문 범위의 holdout을 요구하며 임의 추정하지 않음 |
| cancel / DirectFamilySourceRepairEntryCancelWait | 현재 custody known_open3. 당일 연구 parent9와 옛 잔여 제출6건 결손을 분리 | 역사 미수집9/30·10/1, known-unresolved10·기존 원 terminal/cost 미확인 보존. 이전 표의9/29 결손은 최신 census에서 해소됨. 현재 계좌 보유가 역사 비용 완결을 뜻하지 않음 |
| 보유·익절·손절 / HoldingProfitExitSourceContractRepair | holding504population/32partition, 20,832scope는 원 종목×route/session. native code 검증 완료, 숫자 EXIT 연구 experiment_not_armed | TP 최초 전이5·완료 snapshot gap4/unverified9·forward unobserved482 등 실제 결손 보존. 손절9cell 기존 수치 유지, 비용·실제/CF 분모 혼합 금지 |
| 제출지연 / pre_submit_delay | default0초·기존 nonzero2cell, 231cell의 기존 선택값 | quote/hash185·epoch70·부모호환29 등 각 분모 분리. 새 runtime 임계값 적용 없이 최종 코드에 맞는 native ledger·generation 재검증 |
| 상승누락 / PostcloseStructuralPolicyCompletion1011 | 정상 native regeneration·valid_empty·incumbent_preserved | 원천 coverage를 검증한 유효 빈 집합이며 source_missing을 0으로 덮은 것이 아님 |
| WS/lookup attention / 기존 freshness owner | source missing[]·diagnostic 생성, integrated selection source_gap·valid paired0 | fill receipt missing2,190·invalid20, 실제 full/partial0. 진단 생성과 attention 선택/비용 후 효과를 구분. 퇴역 ADM/LDM을 복원하지 않음 |
| 시장약세 advisory | 00:40 실행으로 source10/16 completed_with_source_gaps. native47·natural trace58·native binding34, outcome U58 | replay의 source_epoch_unverified488,114로 label index0. 원시 시각/epoch 없이 결과를 만들어 연결하지 않음. 자연/CF source gap, 과거 등록 정책 재선정·Main 승격 금지. 이전 deferred 판정은 당시 이력 |
| 선택적 삼성 frozen sidecar | 사용자가 삭제한 과거 observations를 복원하지 않음. 과거 source seal 검증 실패 보존 | Main 정책/기동 필수 stage가 아니며 연구 성공으로 대체하지 않음. 이번 작업에서 해당 연구의 별도 종료 또는 예약 호출 제거를 주장하지 않음 |
| 최종 인계 / summary_handoff·controller·finalization | 위 최신 source들을 다시 소비하여 tower·19일 checklist·strict·controller·prepared를 갱신 | 최종 영수증을 아래에 기록. 다음 영업일 07:35 PREOPEN·07:55 기동·새 PID·자연 실현손익은 아직 not_yet_due |

수리한 코드 범위의 결함과 복구할 수 없는 과거 증거 결손을 분리한다. 원천이 없는 비용·익절 전이·고정 window·source epoch에는 종료시각이나 실현 성과를 만들지 않는다. 기존 source repair/자연 수용 owner의 원 Acceptance는 유지하며 동일 입력 재실행으로 이 결손이 사라진다고 주장하지 않는다.

직접 근거: [실발행 atomic 보존](../../tmp/postclose-monitoring-20261016/final-atomic-publication-c63d44bcb.json), [기계 58건 정산](../../tmp/postclose-monitoring-20261016/review-machine-completion-recovery.json), [4 family native 검증](../../tmp/postclose-monitoring-20261016/final-native-policy-generations-c63d44bcb.json), [현재 custody](../../tmp/postclose-monitoring-20261016/review-native-current-custody.json), [보유 재생성](../../tmp/postclose-monitoring-20261016/holding-current-fixture-refresh-68be02a77-verification.json), [후속 릴리스 선택](../../tmp/postclose-monitoring-20261016/handoff-c63d44bcb/selection-after.json).

### 비영업일 의미 점검 owner 인계 보완

- 토요일의 당일 체크리스트 부재를 장후 결함으로 오인하던 경로를 수정했다. 당일 체크리스트가 있으면 그것을 우선하며, 없는 비영업일에만 같은 sweep에서 native 검증한 DONE controller와 다음 영업일 prepared PASS의 source/target/generation/selected release가 일치할 때 기존 다음 영업일 OPEN stable ID를 연결한다. 원래 관측일과 원천일은 보존하며 다른 원천일 경고에는 인계를 확장하지 않는다.
- 실제 PID 소비나 정책 활성화는 생성하지 않는다. 잘못된 날짜·세대·검증 실패·중복 인계·영업일 체크리스트 부재는 계속 실패로 드러낸다. 동일 원천을 다시 읽지 않고 이미 검증된 sweep 결과를 사용한다.
- self review와 보완 후 artifact freshness/coverage 회귀 315 passed, Python compile 및 diff check 통과. 다음 릴리스 선택 뒤 native finalization과 독립 detector로 실제 주말 인계를 재확인한다.
